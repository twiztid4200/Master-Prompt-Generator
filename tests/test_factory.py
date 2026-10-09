import json
import tempfile
import unittest
from pathlib import Path

from factory.providers.mock import MockProvider
from factory.agents.verifier import review
from factory.runner import run_mission
from factory.tools.github_readonly import DECLARATION, inspect_repository
from factory.validate import load_schema, validate

ROOT = Path(__file__).resolve().parent.parent
GOAL = "Analyze the MASTER AWAKENING repository and determine the best architecture for evolving it into an AI Agent Factory."


def fixture_transport(url: str) -> dict:
    if url.endswith("/git/trees/HEAD?recursive=1"):
        return {"truncated": False, "tree": [{"path": "index.html", "type": "blob"}]}
    return {
        "html_url": "https://github.com/twiztid4200/Master-Prompt-Generator",
        "full_name": "twiztid4200/Master-Prompt-Generator",
        "description": "Master prompt generator",
        "default_branch": "main",
        "pushed_at": "2026-04-06T21:38:41Z",
        "language": "HTML",
        "license": None,
        "has_pages": True,
        "size": 115,
        "private": False,
    }


class FactoryTests(unittest.TestCase):
    def test_prompt_library_preserved(self):
        library = json.loads((ROOT / "data" / "prompts.json").read_text())
        self.assertEqual(library["category_count"], 20)
        self.assertEqual(library["prompt_count"], 500)
        self.assertEqual(len(library["category_order"]), 20)
        prompts = []
        for key in library["category_order"]:
            cat = library["categories"][key]
            self.assertEqual(len(cat["prompts"]), 25)
            prompts.extend(cat["prompts"])
        self.assertEqual(len(prompts), 500)
        self.assertEqual(len(set(prompts)), 500)
        self.assertTrue(prompts[0].startswith("Act as a master performance coach"))

    def test_website_still_has_behavior(self):
        html = (ROOT / "index.html").read_text()
        self.assertIn("MASTER AWAKENING", html)
        self.assertIn("sendToGrok", html)
        self.assertIn("awakeningFavorites", html)
        self.assertIn("randomMasterPrompt", html)
        self.assertIn("toggleDrawer", html)
        self.assertIn("data/prompts.json", html)
        self.assertNotIn("const categories =", html)
        self.assertNotIn("Act as a master performance coach", html)

    def test_contracts_and_tool(self):
        schema = load_schema("agent.schema.json")
        for name in ("architect.json", "scout.json", "verifier.json"):
            contract = json.loads((ROOT / "factory" / "contracts" / name).read_text())
            self.assertEqual(validate(contract, schema), [])
        self.assertEqual(validate(DECLARATION, load_schema("tool.schema.json")), [])
        self.assertFalse(DECLARATION["executes_code"])
        self.assertEqual(DECLARATION["reads_or_modifies"], "read")

    def test_mock_does_not_invent_tokens(self):
        usage = MockProvider().usage()
        self.assertIsNone(usage["input_tokens"])
        self.assertIsNone(usage["output_tokens"])
        self.assertIsNone(usage["estimated_cost_usd"])
        self.assertFalse(usage["available"])

    def test_mission_pass_with_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = run_mission(GOAL, "twiztid4200", "Master-Prompt-Generator", MockProvider(), Path(tmp), transport=fixture_transport)
            self.assertEqual(record["result"], "PASS")
            self.assertEqual(record["iteration"], 1)
            self.assertGreaterEqual(len(record["verdict"]["challenges"]), 2)
            self.assertIsNone(record["usage"]["input_tokens"])
            self.assertTrue((Path(tmp) / "factory" / "memory" / "discoveries" / f"{record['id']}.md").exists())

    def test_pages_claim_omitted_when_flag_false(self):
        def bad_transport(url: str) -> dict:
            payload = fixture_transport(url)
            if "tree" not in payload:
                payload["has_pages"] = False
            return payload
        with tempfile.TemporaryDirectory() as tmp:
            record = run_mission(GOAL, "twiztid4200", "Master-Prompt-Generator", MockProvider(), Path(tmp), transport=bad_transport)
        self.assertEqual(record["result"], "PASS")
        self.assertNotIn("pages", [item["id"] for item in record["report"]["findings"]])

    def test_verifier_fails_unsupported_fact(self):
        evidence = {"ok": True, "source_url": "https://github.com/example/repo", "file_count": 1, "has_pages": False, "license": None}
        report = {
            "goal": GOAL,
            "agent": "scout",
            "provider": "mock",
            "unknowns": [],
            "findings": [{
                "id": "pages",
                "kind": "fact",
                "statement": "Pages is enabled.",
                "evidence": "has_pages=true",
                "source_url": evidence["source_url"],
                "confidence": 1,
                "license": None,
                "maintenance": None,
                "security": None,
                "relevance": GOAL,
            }],
        }
        verdict = review(GOAL, report, evidence, MockProvider())
        self.assertEqual(verdict["verdict"], "FAIL")
        self.assertTrue(verdict["unsupported_claims"])


if __name__ == "__main__":
    unittest.main()
