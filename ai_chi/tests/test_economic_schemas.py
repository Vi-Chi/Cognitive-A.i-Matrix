import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


SCHEMA_FILES = [
    ROOT / "schemas" / "budget-envelope.schema.json",
    ROOT / "schemas" / "compute-receipt.schema.json",
    ROOT / "schemas" / "economic-audit-signal.schema.json",
    ROOT / "schemas" / "cycle-receipt.schema.json",
]


POLICY_FILES = [
    ROOT / "_PROJECT_KNOWLEDGE_BASE" / "economics" / "budget_policy.json",
    ROOT / "_PROJECT_KNOWLEDGE_BASE" / "economics" / "cache_policy.json",
]


LEDGER_FILES = [
    ROOT / "_PROJECT_KNOWLEDGE_BASE" / "economics" / "compute_decisions.jsonl",
    ROOT / "_PROJECT_KNOWLEDGE_BASE" / "economics" / "compute_receipts.jsonl",
    ROOT / "_PROJECT_KNOWLEDGE_BASE" / "economics" / "economic_audit_signals.jsonl",
]


class EconomicSchemaTests(unittest.TestCase):
    def load_json(self, path: Path):
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_expected_files_exist(self):
        for path in [*SCHEMA_FILES, *POLICY_FILES, *LEDGER_FILES]:
            with self.subTest(path=path):
                self.assertTrue(path.exists(), path)

    def test_schemas_have_minimum_contract_shape(self):
        for path in SCHEMA_FILES:
            with self.subTest(path=path.name):
                schema = self.load_json(path)
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(schema["type"], "object")
                self.assertFalse(schema["additionalProperties"])
                self.assertIsInstance(schema["title"], str)
                self.assertGreater(len(schema["title"]), 0)
                self.assertIsInstance(schema["required"], list)
                self.assertGreater(len(schema["required"]), 4)

    def test_policy_defaults_are_non_tradable_and_stop_gated(self):
        budget_policy = self.load_json(POLICY_FILES[0])
        self.assertFalse(budget_policy["sigma_credit"]["public_tradable"])
        self.assertFalse(budget_policy["sigma_credit"]["redeemable"])
        self.assertIn("public_token_or_sns_launch", budget_policy["hard_blocks"])
        self.assertIn("mainnet_or_on_chain_write", budget_policy["hard_blocks"])
        self.assertTrue(budget_policy["default_route_policy"]["local_first"])
        self.assertFalse(budget_policy["default_route_policy"]["allow_icp_update"])

    def test_cache_policy_blocks_sensitive_seed_material(self):
        cache_policy = self.load_json(POLICY_FILES[1])
        self.assertFalse(cache_policy["secret_material_allowed"])
        self.assertFalse(cache_policy["credential_material_allowed"])
        self.assertFalse(cache_policy["untrusted_content_allowed"])
        self.assertIn("raw_untrusted_imports", cache_policy["blocked_seed_classes"])

    def test_jsonl_ledgers_are_empty_or_valid_json_per_line(self):
        for path in LEDGER_FILES:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                for line in text.splitlines():
                    if line.strip():
                        self.assertIsInstance(json.loads(line), dict)


if __name__ == "__main__":
    unittest.main()
