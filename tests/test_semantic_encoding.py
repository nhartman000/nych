import json
import subprocess
import sys
import unittest

from nych.semantic_encoding import audit_summary, encode_text
from nych.semantic_registry import load_registry, sense_by_id


class SemanticEncodingTests(unittest.TestCase):
    def test_registry_is_valid_and_persistent(self):
        registry = load_registry()
        self.assertGreaterEqual(len(registry["senses"]), 14)
        self.assertEqual(sense_by_id("finance.bank.institution", registry)["gestalt"], "🏦")

    def test_explicit_sense_overrides_river_context(self):
        encoded, records = encode_text(
            "the river bank closed my account",
            sense_choices={2: "finance.bank.institution"},
        )
        bank = next(record for record in records if record["position"] == 2)
        self.assertEqual(bank["method"], "explicit")
        self.assertEqual(bank["sense_id"], "finance.bank.institution")
        self.assertIn("🏦", encoded)

    def test_longest_spans_preserve_invariants(self):
        _, records = encode_text("the unit test repair preserved the test suite")
        spans = [record for record in records if record["method"] == "gestalt_span"]
        self.assertEqual([record["sense_id"] for record in spans],
                         ["process.unit_test_repair", "artifact.test_suite"])
        self.assertTrue(all(record["protected_invariants"] for record in spans))
        audit = audit_summary(records)
        self.assertEqual(audit["total_words"], 8)
        self.assertEqual(audit["total_units"], 5)

    def test_cli_json_exposes_audit(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nych.cli", "encode",
             "the river bank closed my account", "--sense",
             "2=finance.bank.institution", "--json"],
            check=True, text=True, capture_output=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["audit"]["fraction_guessed"], 0.0)


if __name__ == "__main__":
    unittest.main()
