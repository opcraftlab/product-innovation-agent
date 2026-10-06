"""Regression checks for the mechanism contract, using synthetic records only."""
import unittest

from innovation_agent import core, guidance, tasks
from innovation_agent.schemas import ValidationError


def fixture(agent):
    data = core.read_json(core.DATA / f"task_examples/{agent}.input.json")
    out = core.read_json(core.DATA / f"task_examples/{agent}.output.json")
    return data, out


class InnovationContract(unittest.TestCase):
    def test_generic_list_without_mechanism_chain_rejected(self):
        for agent in ("opportunity", "concept"):
            with self.subTest(agent=agent):
                data, out = fixture(agent)
                del out[tasks.AGENTS[agent]["collection"]][0]["innovation"]
                with self.assertRaisesRegex(ValidationError, "innovation"):
                    tasks.evaluate(agent, data, out)

    def test_missing_implementation_or_falsifier_rejected(self):
        for field in ("implementation", "user_change", "switching_reason", "capability_status", "falsifier"):
            with self.subTest(field=field):
                data, out = fixture("concept")
                out["concepts"][0]["innovation"][field] = "   "
                with self.assertRaisesRegex(ValidationError, "non-empty"):
                    tasks.evaluate("concept", data, out)

    def test_invented_or_duplicate_mechanism_ids_rejected(self):
        for ids in (["I99"], ["I01", "I01"]):
            with self.subTest(ids=ids):
                data, out = fixture("concept")
                out["concepts"][0]["innovation"]["mechanism_ids"] = ids
                with self.assertRaises(ValidationError):
                    tasks.evaluate("concept", data, out)

    def test_category_name_alone_cannot_satisfy_mechanism_contract(self):
        data, out = fixture("concept")
        out["concepts"][0]["innovation"].update(level="category_hypothesis", mechanism_ids=[])
        with self.assertRaisesRegex(ValidationError, "explicit mechanism"):
            tasks.evaluate("concept", data, out)

    def test_cosmetic_request_does_not_require_inventing_a_mechanism(self):
        data, out = fixture("concept")
        out["concepts"][0]["innovation"].update(level="expression", mechanism_ids=[],
            mechanism="仅改变颜色，未改变任务或结构")
        self.assertEqual(tasks.evaluate("concept", data, out)["decisions"][0]["verdict"], "demo_only")

    def test_no_justified_direction_can_return_no_candidates(self):
        for agent in ("opportunity", "concept"):
            with self.subTest(agent=agent):
                data, out = fixture(agent)
                out[tasks.AGENTS[agent]["collection"]] = []
                out["summary"] = "现有条件下不提出方向，先补充真实任务"
                gate = tasks.evaluate(agent, data, out)
                self.assertEqual(gate["decisions"], [])
                self.assertTrue(any("没有形成" in x for x in gate["warnings"]))

    def test_complete_chain_never_proves_innovation_quality(self):
        data, out = fixture("concept")
        data["synthetic"] = False
        out["input_digest"] = tasks.input_digest("concept", tasks.normalize("concept", data))
        out["concepts"][0]["innovation"]["level"] = "category_hypothesis"
        gate = tasks.evaluate("concept", data, out)
        self.assertEqual({x["verdict"] for x in gate["decisions"]}, {"hypothesis_only"})
        self.assertTrue(any("不证明机制成立" in w for w in gate["warnings"]))

    def test_report_preserves_chain_and_counterargument(self):
        data, out = fixture("concept")
        report = tasks.render_report("concept", tasks.normalize("concept", data), out, tasks.evaluate("concept", data, out))
        for key in ("mechanism", "implementation", "falsifier"):
            self.assertIn(out["concepts"][0]["innovation"][key], report)

    def test_api_payload_has_complete_mechanisms_for_discovery(self):
        data, _ = fixture("opportunity")
        system, _ = tasks.build_prompt("opportunity", data)
        self.assertIn("A1.", system)
        self.assertIn("B4.", system)
        for card in guidance.mechanism_cards():
            self.assertIn(card["action"], system)

    def test_generated_entrypoints_have_not_drifted(self):
        from scripts.build_guidance import check
        self.assertEqual(check(), [])


if __name__ == "__main__":
    unittest.main()
