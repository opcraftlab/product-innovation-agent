"""Task boundaries and consequential failure cases. All records are test fixtures."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout,redirect_stderr

from innovation_agent import core,tasks
from innovation_agent.cli import main
from innovation_agent.provider import generate
from innovation_agent.schemas import ValidationError

def fixture(agent="validation"):
    root=core.DATA/"task_examples"
    return core.read_json(root/(agent+".input.json")),core.read_json(root/(agent+".output.json"))

def evaluate(data,analysis,agent="validation"):
    analysis["input_digest"]=tasks.input_digest(agent,tasks.normalize(agent,data))
    return tasks.evaluate(agent,data,analysis)

def supported_fixture():
    data,out=fixture(); data["synthetic"]=False;data["constraints"]=[];data["evidence"]=[]
    for review in out["reviews"]:
        for c in review["checks"]:
            eid=review["candidate_id"]+"-"+c["dimension"]
            data["evidence"].append({"id":eid,"statement":"Constructed test record, not a real market fact",
                "kind":"interview" if c["dimension"]=="demand" else "technical","source":"unit-test fixture",
                "date":"2026-01-01","sample_size":3,"verified":True,"synthetic":False,
                "dimensions":[c["dimension"]],"candidate_ids":[review["candidate_id"]],"limitations":"Tests rule behavior only"})
            c.update(status="supported",evidence_ids=[eid])
    return data,out

class TaskBoundaries(unittest.TestCase):
    def test_minimal_independent_inputs(self):
        for agent in ("opportunity","concept"):
            data=tasks.normalize(agent,{"goal":"A task","context":"Background"})
            self.assertEqual(data["evidence"],[])
        with self.assertRaisesRegex(ValidationError,"candidate"):
            tasks.normalize("validation",{"goal":"A task","context":"Background"})

    def test_relevant_methods_only(self):
        for agent in tasks.AGENTS:
            data,_=fixture(agent);system,prompt=tasks.build_prompt(agent,data)
            payload=json.loads(prompt.split("\n",1)[1])
            self.assertEqual({m["id"] for m in payload["method_cards"]},set(tasks.AGENTS[agent]["methods"]))
            self.assertLess(len(payload["method_cards"]),18)

    def test_synthetic_demo_never_claims_supported(self):
        for agent in tasks.AGENTS:
            data,out=fixture(agent)
            self.assertEqual({d["verdict"] for d in evaluate(data,out,agent)["decisions"]},{"demo_only"})

    def test_hypotheses_remain_hypotheses(self):
        for agent in ("opportunity","concept"):
            data,out=fixture(agent);data["synthetic"]=False
            self.assertEqual(evaluate(data,out,agent)["decisions"][0]["verdict"],"hypothesis_only")

    def test_unknown_input_field_rejected(self):
        data,out=fixture();data["sucess_probability"]=99
        with self.assertRaises(ValidationError): evaluate(data,out)

    def test_budget_requires_currency(self):
        data,out=fixture();del data["currency"]
        with self.assertRaisesRegex(ValidationError,"currency"): evaluate(data,out)

    def test_duplicate_input_ids_rejected(self):
        data,out=fixture();data["candidates"][1]["id"]="D1"
        with self.assertRaisesRegex(ValidationError,"Duplicate"): evaluate(data,out)

    def test_unknown_scoped_input_evidence_rejected(self):
        data,out=supported_fixture();data["evidence"][0]["candidate_ids"]=["absent"]
        with self.assertRaisesRegex(ValidationError,"unknown input candidate"): evaluate(data,out)

    def test_input_update_invalidates_output(self):
        data,out=fixture();data["goal"]="Changed goal"
        with self.assertRaisesRegex(ValidationError,"digest"): tasks.evaluate("validation",data,out)

class TaskDecisions(unittest.TestCase):
    def test_only_selected_checks_supported_not_business_approval(self):
        data,out=supported_fixture();gate=evaluate(data,out)
        self.assertEqual({d["verdict"] for d in gate["decisions"]},{"selected_checks_supported"})
        self.assertIn("不代表",gate["scope"])

    def test_reject_made_up_evidence(self):
        data,out=fixture();out["reviews"][0]["checks"][0]["evidence_ids"]=["invented"]
        with self.assertRaisesRegex(ValidationError,"unknown evidence"): evaluate(data,out)

    def test_bad_evidence_cannot_support(self):
        for field,value in [("kind","desk"),("kind","simulation"),("verified",False),("synthetic",True),
                             ("dimensions",["communication"]),("candidate_ids",["D2"])]:
            with self.subTest(field=field,value=value):
                data,out=supported_fixture();data["evidence"][0][field]=value
                self.assertEqual(evaluate(data,out)["decisions"][0]["verdict"],"research")

    def test_real_counterevidence_forces_rework(self):
        data,out=supported_fixture();counter=copy.deepcopy(data["evidence"][0]);counter["id"]="counter"
        data["evidence"].append(counter);out["reviews"][0]["checks"][0]["counter_evidence_ids"]=["counter"]
        self.assertEqual(evaluate(data,out)["decisions"][0]["verdict"],"rework")

    def test_cannot_drop_bad_candidate(self):
        data,out=fixture();out["reviews"].pop()
        with self.assertRaisesRegex(ValidationError,"every input candidate"): evaluate(data,out)

    def test_cannot_skip_requested_dimension(self):
        data,out=fixture();out["reviews"][0]["checks"].pop()
        with self.assertRaisesRegex(ValidationError,"requested dimension"): evaluate(data,out)

    def test_cannot_hide_candidate_from_priority(self):
        data,out=fixture();out["priority"]=["D1"]
        with self.assertRaisesRegex(ValidationError,"priority"): evaluate(data,out)

    def test_hard_failure_stops_and_no_experiment_needed(self):
        data,out=supported_fixture()
        data["constraints"]=[{"id":"blocked","description":"Cannot meet delivery requirement","status":"fail","candidate_ids":["D1"]}]
        out["experiments"]=[x for x in out["experiments"] if x["candidate_id"]!="D1"]
        self.assertEqual(evaluate(data,out)["decisions"][0]["verdict"],"stop")

    def test_cannot_spend_on_hard_failed_candidate(self):
        data,out=supported_fixture();data["constraints"]=[{"id":"B","description":"Blocked","status":"fail","candidate_ids":["D1"]}]
        with self.assertRaisesRegex(ValidationError,"blocked"): evaluate(data,out)

    def test_unknown_constraint_blocks_selected_support(self):
        data,out=supported_fixture();data["constraints"]=[{"id":"U","description":"Unknown","status":"unknown","candidate_ids":["*"]}]
        self.assertEqual(evaluate(data,out)["decisions"][0]["verdict"],"research")

    def test_unresolved_candidate_needs_experiment(self):
        data,out=fixture();out["experiments"].pop()
        with self.assertRaisesRegex(ValidationError,"next experiment"): evaluate(data,out)

    def test_portfolio_cost_not_per_candidate_budget(self):
        data,out=fixture();data["budget"]=200
        gate=evaluate(data,out);self.assertEqual(gate["budget_status"],"exceeded");self.assertEqual(gate["planned_cost"],240)

    def test_missing_budget_is_not_zero_authorization(self):
        data,out=fixture();del data["budget"];del data["currency"]
        gate=evaluate(data,out);self.assertEqual(gate["budget_status"],"not_set");self.assertIsNone(gate["budget"])

    def test_invalid_numbers_and_dates(self):
        for value in [True,-1,float('nan')]:
            data,out=fixture();data["budget"]=value
            with self.assertRaises(ValidationError): evaluate(data,out)
        data,out=supported_fixture();data["evidence"][0]["date"]="20260101"
        with self.assertRaisesRegex(ValidationError,"YYYY-MM-DD"): evaluate(data,out)

class TaskIO(unittest.TestCase):
    def test_each_demo_prepare_import_cycle(self):
        with tempfile.TemporaryDirectory() as tmp,redirect_stdout(io.StringIO()):
            for agent in tasks.AGENTS:
                root=Path(tmp)/agent;root.mkdir()
                inp=core.DATA/"task_examples"/(agent+".input.json")
                out=core.DATA/"task_examples"/(agent+".output.json")
                self.assertEqual(main(["task","prepare","--agent",agent,"--input",str(inp),"--output",str(root/"prompt.md")]),0)
                self.assertEqual(main(["task","import","--agent",agent,"--input",str(inp),"--analysis",str(out),"--output-dir",str(root/"run")]),0)
                self.assertEqual(main(["task","demo","--agent",agent,"--output-dir",str(root/"demo")]),0)
                self.assertTrue((root/"run"/"report.md").is_file())

    def test_invalid_output_does_not_create_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            data,out=fixture();out["input_digest"]="stale";path=Path(tmp)/"run"
            with self.assertRaises(ValidationError): tasks.save_result("validation",data,out,path,"test")
            self.assertFalse(path.exists())

    def test_existing_output_blocks_api_before_spending(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict("os.environ",{"OPENAI_API_KEY":"test","INNOVATION_MODEL":"test"}),patch("innovation_agent.cli.generate") as gen,redirect_stderr(io.StringIO()):
            inp=core.DATA/"task_examples"/"validation.input.json"
            self.assertEqual(main(["task","run","--agent","validation","--input",str(inp),"--output-dir",tmp]),2)
            gen.assert_not_called()

    def test_missing_key_no_api_call(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict("os.environ",{},clear=True),patch("innovation_agent.cli.generate") as gen,redirect_stderr(io.StringIO()):
            inp=core.DATA/"task_examples"/"validation.input.json"
            self.assertEqual(main(["task","run","--agent","validation","--input",str(inp),"--output-dir",str(Path(tmp)/"run")]),2)
            gen.assert_not_called()

    def test_model_path_uses_agent_specific_schema_and_saves(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict("os.environ",{"OPENAI_API_KEY":"test","INNOVATION_MODEL":"test"}),redirect_stdout(io.StringIO()):
            for agent in tasks.AGENTS:
                data,out=fixture(agent);inp=core.DATA/"task_examples"/(agent+".input.json")
                with patch("innovation_agent.cli.generate",return_value=(out,{"live_api":False})) as gen:
                    self.assertEqual(main(["task","run","--agent",agent,"--input",str(inp),"--output-dir",str(Path(tmp)/agent)]),0)
                    gen.assert_called_once();self.assertEqual(gen.call_args.kwargs["schema"],tasks.output_schema(agent))

    def test_provider_conservative_schema_keeps_local_checks(self):
        class Fake:
            def open(self,req,timeout):
                self.payload=json.loads(req.data)
                return io.BytesIO(json.dumps({"status":"completed","output":[{"type":"message","content":[{"type":"output_text","text":"{}"}]}]}).encode())
        fake=Fake();schema=tasks.output_schema("opportunity")
        generate("s","u","model","test",opener=fake,schema=schema)
        submitted=json.dumps(fake.payload["text"]["format"]["schema"])
        self.assertNotIn("minLength",submitted);self.assertIn("minLength",json.dumps(schema))
        self.assertIn("opportunities",submitted);self.assertNotIn('"reviews"',submitted)

if __name__=="__main__": unittest.main()
