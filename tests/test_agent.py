"""Constructed fixtures test program rules; they are not real market records."""
import copy
from datetime import date
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
import urllib.error

from innovation_agent import core
from innovation_agent.cli import main
from innovation_agent.provider import generate, parse_response, NoRedirect
from innovation_agent.schemas import ValidationError, DIMENSIONS

def fixture(stage="prototype"):
    root=core.DATA/"demo"
    b=core.read_json(root/"brief.json"); a=core.read_json(root/"analysis.json")
    b.update(synthetic=False,target_stage=stage,constraints=[],max_directions=1)
    a["candidates"]=a["candidates"][:1]; a["experiments"]=a["experiments"][:1]
    kinds=dict(zip(DIMENSIONS,("capability","interview","preference","behavior","technical","quote","preference","behavior")))
    e=[]
    for d in DIMENSIONS:
        eid="E-"+d
        e.append({"id":eid,"statement":"Constructed unit-test record, not a market claim", "kind":kinds[d],"source":"unit test only", "date":"2026-01-01","sample_size":5,"verified":True,"synthetic":False,"dimensions":[d],"candidate_ids":["D1"],"limitations":"Mock flags exercise rule behavior only"})
        a["candidates"][0]["assessments"][d]={"status":"supported","reason":"Test branch", "evidence_ids":[eid],"counter_evidence_ids":[]}
    a["input_digest"]=core.digest(b,e)
    return b,e,a

def check(b,e,a):
    a["input_digest"]=core.digest(b,e)
    return core.evaluate(a,b,e)

class GateTests(unittest.TestCase):
    def test_valid_records_only_allow_human_review(self):
        b,e,a=fixture(); self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"ready_for_human_review")

    def test_synthetic_evidence_cannot_pass(self):
        b,e,a=fixture(); e[1]["synthetic"]=True
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"research")

    def test_synthetic_project_never_gets_business_verdict(self):
        b,e,a=fixture(); b["synthetic"]=True
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"demo_only")

    def test_simulation_never_passes(self):
        b,e,a=fixture(); e[1]["kind"]="simulation"
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"research")

    def test_unverified_evidence_cannot_pass(self):
        b,e,a=fixture(); e[1]["verified"]=False
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"research")

    def test_desk_research_does_not_prove_demand(self):
        b,e,a=fixture(); e[1]["kind"]="desk"
        self.assertEqual(check(b,e,a)["directions"][0]["assessments"]["demand"]["effective_status"],"promising")

    def test_other_direction_cannot_supply_support(self):
        b,e,a=fixture(); e[1]["candidate_ids"]=["D2"]
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"research")

    def test_other_dimension_cannot_supply_support(self):
        b,e,a=fixture(); e[1]["dimensions"]=["communication"]
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"research")

    def test_unknown_reference_rejected(self):
        b,e,a=fixture(); a["candidates"][0]["assessments"]["demand"]["evidence_ids"]=["invented"]
        with self.assertRaisesRegex(ValidationError,"unknown evidence"): check(b,e,a)

    def test_supported_without_references_does_not_pass(self):
        b,e,a=fixture(); a["candidates"][0]["assessments"]["demand"]["evidence_ids"]=[]
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"research")

    def test_counterevidence_blocks_unqualified_pass(self):
        b,e,a=fixture(); counter=copy.deepcopy(e[1]); counter["id"]="E-counter"; e.append(counter)
        a["candidates"][0]["assessments"]["demand"]["counter_evidence_ids"]=["E-counter"]
        g=check(b,e,a)["directions"][0]
        self.assertEqual(g["verdict"],"rework"); self.assertEqual(g["assessments"]["demand"]["effective_status"],"mixed")

    def test_same_support_and_counter_rejected(self):
        b,e,a=fixture(); a["candidates"][0]["assessments"]["demand"]["counter_evidence_ids"]=["E-demand"]
        with self.assertRaisesRegex(ValidationError,"distinct"): check(b,e,a)

    def test_hard_failure_dominates_supported_assessments(self):
        b,e,a=fixture(); b["constraints"]=[{"id":"C","description":"Cannot fit required space","status":"fail","candidate_ids":["*"]}]
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"stop")

    def test_unknown_constraint_requires_research(self):
        b,e,a=fixture(); b["constraints"]=[{"id":"C","description":"Size unknown","status":"unknown","candidate_ids":["*"]}]
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"research")

    def test_candidate_cannot_disappear_to_escape_constraint(self):
        b,e,a=fixture(); b["constraints"]=[{"id":"C","description":"Blocked direction","status":"fail","candidate_ids":["D2"]}]
        with self.assertRaisesRegex(ValidationError,"constrained candidate"): check(b,e,a)

    def test_budget_overrun_blocks_candidate(self):
        b,e,a=fixture(); b["budget"]=1
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"research")

    def test_portfolio_budget_checked_across_candidates(self):
        root=core.DATA/"demo"; b=core.read_json(root/"brief.json"); e=core.read_json(root/"evidence.json"); a=core.read_json(root/"analysis.json")
        b["budget"]=200
        self.assertTrue(check(b,e,a)["portfolio_over_budget"])

    def test_scale_needs_transactions_retention_and_delivery(self):
        b,e,a=fixture("scale")
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"research")
        for kind in ("transaction","retention","delivery"):
            r=copy.deepcopy(e[1]); r.update(id="E-"+kind,kind=kind,candidate_ids=["*"]); e.append(r)
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"research")
        for r in e[-3:]: r["candidate_ids"]=["D1"]
        self.assertEqual(check(b,e,a)["directions"][0]["verdict"],"ready_for_human_review")

    def test_stale_input_rejected(self):
        b,e,a=fixture(); b["budget"]+=1
        with self.assertRaisesRegex(ValidationError,"digest"): core.evaluate(a,b,e)

    def test_each_candidate_needs_an_experiment(self):
        b,e,a=fixture(); a["experiments"][0]["candidate_id"]="D2"
        with self.assertRaisesRegex(ValidationError,"unknown candidate"): check(b,e,a)

    def test_nonfinite_budget_and_boolean_number_rejected(self):
        for value in (float("nan"),float("inf"),True):
            b,e,a=fixture(); b["budget"]=value
            with self.assertRaises(ValidationError): core.validate_inputs(b,e)

    def test_future_verified_record_rejected(self):
        b,e,a=fixture(); e[1]["date"]="2099-01-01"
        with self.assertRaisesRegex(ValidationError,"future"): core.validate_inputs(b,e)

    def test_zero_verified_real_sample_rejected(self):
        b,e,a=fixture(); e[1]["sample_size"]=0
        with self.assertRaisesRegex(ValidationError,"sample_size"): core.validate_inputs(b,e)

class ProjectTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.p=Path(self.tmp.name)/"p"
    def tearDown(self): self.tmp.cleanup()
    def test_history_feedback_and_stale_cycle(self):
        b,e,a=fixture(); core.init_project(self.p,b,e)
        first=core.commit_analysis(self.p,a,"test")
        self.assertEqual(core.current_status(self.p)["state"],"current")
        extra=copy.deepcopy(e[1]); extra["id"]="E-new"
        core.add_evidence(self.p,[extra])
        self.assertEqual(core.current_status(self.p)["state"],"stale")
        with self.assertRaises(ValidationError): core.commit_analysis(self.p,a,"test")
        system,prompt=core.build_prompt(self.p)
        self.assertIn("previous_analysis",prompt); self.assertIn("E-new",prompt)
        a["input_digest"]=core.digest(b,e+[extra]); core.commit_analysis(self.p,a,"test")
        self.assertEqual(core.current_status(self.p)["state"],"current")
        self.assertEqual(len(list((self.p/"history").glob("*.json"))),2)
        self.assertTrue((self.p/"history"/(first["run_id"]+".json")).exists())

    def test_duplicate_feedback_does_not_overwrite(self):
        b,e,a=fixture(); core.init_project(self.p,b,e)
        before=(self.p/"evidence.json").read_bytes()
        with self.assertRaises(ValidationError): core.add_evidence(self.p,[e[0]])
        self.assertEqual(before,(self.p/"evidence.json").read_bytes())

    def test_feedback_requires_array_and_preserves_data(self):
        b,e,a=fixture(); core.init_project(self.p,b,e)
        before=(self.p/"evidence.json").read_bytes()
        with self.assertRaises(ValidationError): core.add_evidence(self.p,{"id":"bad"})
        self.assertEqual(before,(self.p/"evidence.json").read_bytes())

    def test_init_never_overwrites_existing_project(self):
        b,e,a=fixture(); core.init_project(self.p,b,e)
        with self.assertRaises(ValidationError): core.init_project(self.p,b,e)

    def test_failed_analysis_preserves_last_good_run(self):
        b,e,a=fixture(); core.init_project(self.p,b,e); core.commit_analysis(self.p,a,"test")
        before=(self.p/"latest.json").read_bytes()
        a["candidates"][0]["assessments"]["fit"]["evidence_ids"]=["bad"]
        with self.assertRaises(ValidationError): core.commit_analysis(self.p,a,"test")
        self.assertEqual(before,(self.p/"latest.json").read_bytes())

    def test_cli_demo_prepare_and_status(self):
        output=io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["demo","--project",str(self.p)]),0)
            self.assertEqual(main(["prepare","--project",str(self.p),"--output",str(self.p/"prompt.md")]),0)
            self.assertEqual(main(["status","--project",str(self.p)]),0)
        self.assertIn("合成",(self.p/"report.md").read_text())
        self.assertIn("input_digest",(self.p/"prompt.md").read_text())

    def test_cli_manual_import(self):
        b,e,a=fixture(); core.init_project(self.p,b,e); core.write_json(self.p/"answer.json",a)
        with redirect_stdout(io.StringIO()): self.assertEqual(main(["import-analysis","--project",str(self.p),"--file",str(self.p/"answer.json")]),0)
        self.assertEqual(core.current_status(self.p)["mode"],"manual_import")

    def test_cli_missing_key_does_not_call_provider(self):
        with patch.dict("os.environ",{},clear=True),patch("innovation_agent.cli.generate") as gen,redirect_stderr(io.StringIO()):
            self.assertEqual(main(["run","--project",str(self.p)]),2)
            gen.assert_not_called()

class ProviderTests(unittest.TestCase):
    def response(self,text="{}",status="completed"):
        return {"status":status,"output":[{"type":"reasoning"},{"type":"message","content":[{"type":"output_text","text":text}]}]}
    def test_parse_completed(self): self.assertEqual(parse_response(self.response('{"ok":true}')),{"ok":True})
    def test_incomplete_rejected(self):
        with self.assertRaisesRegex(ValidationError,"not completed"): parse_response(self.response(status="incomplete"))
    def test_refusal_rejected(self):
        d=self.response(); d["output"][1]["content"]=[{"type":"refusal","refusal":"No"}]
        with self.assertRaisesRegex(ValidationError,"refused"): parse_response(d)
    def test_invalid_json_rejected(self):
        with self.assertRaisesRegex(ValidationError,"valid JSON"): parse_response(self.response("broken"))
    def test_payload_and_single_call(self):
        raw=json.dumps(self.response()).encode()
        class Fake:
            count=0
            def open(self,req,timeout):
                self.count+=1; self.req=req; self.timeout=timeout
                return io.BytesIO(raw)
        fake=Fake(); result,meta=generate("system","input","test-model","not-a-real-key",opener=fake)
        payload=json.loads(fake.req.data)
        self.assertEqual(fake.count,1); self.assertFalse(payload["store"])
        self.assertEqual(payload["text"]["format"]["type"],"json_schema")
        self.assertTrue(payload["text"]["format"]["strict"])
        self.assertNotIn("not-a-real-key",json.dumps(meta))
    def test_http_error_does_not_expose_body_or_retry(self):
        class Fake:
            count=0
            def open(self,req,timeout):
                self.count+=1
                raise urllib.error.HTTPError(req.full_url,429,"secret-body",{},None)
        fake=Fake()
        with self.assertRaises(ValidationError) as ctx: generate("s","u","m","secret-key",opener=fake)
        self.assertEqual(fake.count,1); self.assertNotIn("secret",str(ctx.exception))
    def test_redirects_disabled(self): self.assertIsNone(NoRedirect().redirect_request(None,None,None,None,None,None))

if __name__=="__main__": unittest.main()
