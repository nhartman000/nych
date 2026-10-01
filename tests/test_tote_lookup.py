import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from nych.state_roles import tag_roles
from nych.tote_lookup import lookup_loop

# Minimal fixture copy of the relevant T.O.T.E-loops schema
# (schema.sql: tote_loops, gestalts, loop_gestalts).
FIXTURE_SCHEMA = """
CREATE TABLE gestalts (
    gestalt_id TEXT PRIMARY KEY,
    glyph TEXT,
    lexical_form TEXT NOT NULL,
    sense TEXT NOT NULL,
    route TEXT NOT NULL,
    recoverability_note TEXT NOT NULL
);
CREATE TABLE tote_loops (
    loop_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    objective TEXT NOT NULL,
    initial_test TEXT NOT NULL,
    exit_predicate TEXT NOT NULL,
    max_iterations INTEGER NOT NULL,
    epistemic_status TEXT NOT NULL
);
CREATE TABLE loop_gestalts (
    loop_id TEXT NOT NULL REFERENCES tote_loops(loop_id),
    gestalt_id TEXT NOT NULL REFERENCES gestalts(gestalt_id),
    role TEXT NOT NULL,
    PRIMARY KEY (loop_id, gestalt_id, role)
);
"""

GESTALTS = [
    ("test", "🧪", "test", "software or model evaluation", "G", "n"),
    ("bug", "🐛", "bug", "software defect", "G", "n"),
    ("repair", "🔧", "repair", "correct a defect", "G", "n"),
    ("provenance", None, "provenance", "evidentiary status", "P", "n"),
]

LOOPS = [
    ("code.unit_test_repair", "Unit-test repair", "software-engineering",
     "Restore a failing unit test suite to passing.",
     "Run the test suite.", "All tests pass.", 10, "CANONICAL",
     ["test", "bug", "repair"]),
    ("ai.retrieval_grounding", "Retrieval grounding", "ai-retrieval",
     "Ensure answers cite retrieved provenance.",
     "Inspect citations.", "Every claim grounded.", 5, "CANONICAL",
     ["provenance"]),
]


class ToteLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls._tmp.name) / "tote_loops.sqlite3"
        conn = sqlite3.connect(cls.db_path)
        conn.executescript(FIXTURE_SCHEMA)
        conn.executemany("INSERT INTO gestalts VALUES (?,?,?,?,?,?)", GESTALTS)
        for loop in LOOPS:
            conn.execute("INSERT INTO tote_loops VALUES (?,?,?,?,?,?,?,?)", loop[:8])
            for gid in loop[8]:
                conn.execute("INSERT INTO loop_gestalts VALUES (?,?,?)",
                             (loop[0], gid, "process-context"))
        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_worked_example_matches_unit_test_repair(self):
        roles = tag_roles("Re-ran both test suites after changes")
        result = lookup_loop(roles, self.db_path, domain="COMPUTER_SCIENCE")
        self.assertTrue(result["matched"])
        self.assertEqual(result["loop"]["loop_id"], "code.unit_test_repair")
        self.assertEqual(result["match_method"], "gestalt-lexical")
        self.assertIn("test", result["matched_words"])
        # raw roles are carried through on a match too
        self.assertEqual(result["roles"]["action"]["lemma"], "run")

    def test_subdomain_constrains_namespace(self):
        roles = tag_roles("checked the provenance after retrieval")
        hit = lookup_loop(roles, self.db_path, subdomain="ai")
        self.assertTrue(hit["matched"])
        self.assertEqual(hit["loop"]["loop_id"], "ai.retrieval_grounding")
        miss = lookup_loop(roles, self.db_path, subdomain="code")
        self.assertFalse(miss["matched"])
        self.assertEqual(miss["fallback"], "state_roles")

    def test_no_match_falls_back_to_raw_roles(self):
        roles = tag_roles("watered the garden before lunch")
        result = lookup_loop(roles, self.db_path)
        self.assertFalse(result["matched"])
        self.assertEqual(result["fallback"], "state_roles")
        self.assertEqual(result["roles"], roles)

    def test_missing_database_is_disclosed_fallback_not_error(self):
        roles = tag_roles("Re-ran both test suites after changes")
        result = lookup_loop(roles, Path(self._tmp.name) / "nope.sqlite3")
        self.assertFalse(result["matched"])
        self.assertIn("database not found", result["reason"])

    def test_no_candidate_words_is_disclosed(self):
        roles = tag_roles("the of and")
        result = lookup_loop(roles, self.db_path)
        self.assertFalse(result["matched"])
        self.assertIn("no object/action words", result["reason"])

    def test_unmapped_domain_does_not_constrain(self):
        roles = tag_roles("Re-ran both test suites after changes")
        result = lookup_loop(roles, self.db_path, domain="BASKETWEAVING")
        self.assertTrue(result["matched"])

    def test_cli_lookup_outputs_valid_json(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nych.cli", "lookup",
             "Re-ran both test suites after changes",
             "--db", str(self.db_path), "--domain", "COMPUTER_SCIENCE"],
            check=True, text=True, capture_output=True,
        )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["matched"])
        self.assertEqual(payload["loop"]["loop_id"], "code.unit_test_repair")


if __name__ == "__main__":
    unittest.main()
