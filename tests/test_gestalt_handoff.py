import sqlite3
import tempfile
import unittest
from pathlib import Path

from nych.gestalt_handoff import DISCRETION_RULES, build_handoff
from nych.session_invariants import MODALITY_OPERATORS, SessionInvariants

SENTENCE = "Re-ran both test suites after changes"


class GestaltHandoffTests(unittest.TestCase):
    def test_deterministic_findings_come_first(self):
        h = build_handoff(SENTENCE)
        # state representation extracted before any mapping
        self.assertEqual(h["roles"]["action"]["lemma"], "run")
        self.assertEqual(h["roles"]["tense"]["word"], "after")
        self.assertIn("domain", h["analysis"])
        # no LLM / no db supplied -> tote honestly absent, not faked
        self.assertIsNone(h["tote"])

    def test_needs_mapping_carries_skeleton_clues(self):
        h = build_handoff(SENTENCE)
        by_word = {d["word"]: d for d in h["needs_mapping"]}
        self.assertIn("suites", by_word)
        self.assertEqual(by_word["suites"]["skeleton"], "sts")
        self.assertTrue(by_word["suites"]["id"].endswith(".sts"))

    def test_modality_operators_always_included_and_invariant(self):
        h = build_handoff(SENTENCE)
        self.assertEqual(h["modality_operators"], MODALITY_OPERATORS)
        operator_rule = next(r for r in h["discretion_rules"]
                             if "modality operators are invariant" in r)
        self.assertIn("never remapped", operator_rule)
        self.assertIn("never assigned to any other word", operator_rule)
        self.assertEqual(h["discretion_rules"], list(DISCRETION_RULES))

    def test_pinned_words_not_reopened(self):
        session = SessionInvariants()
        session.pin("suites", "gestalt.sts")
        h = build_handoff(SENTENCE, session=session)
        needs = [d["word"] for d in h["needs_mapping"]]
        self.assertNotIn("suites", needs)
        pinned = [p["word"] for p in h["pinned"]]
        self.assertIn("suites", pinned)

    def test_stopwords_excluded_from_mapping(self):
        h = build_handoff("fixed the build before the release")
        needs = [d["word"].lower() for d in h["needs_mapping"]]
        self.assertNotIn("the", needs)
        self.assertIn("build", needs)

    def test_tote_lookup_runs_when_db_supplied(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "t.sqlite3"
            conn = sqlite3.connect(db)
            conn.executescript("""
                CREATE TABLE gestalts (gestalt_id TEXT PRIMARY KEY, glyph TEXT,
                    lexical_form TEXT NOT NULL, sense TEXT NOT NULL,
                    route TEXT NOT NULL, recoverability_note TEXT NOT NULL);
                CREATE TABLE tote_loops (loop_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE, domain TEXT NOT NULL,
                    objective TEXT NOT NULL, initial_test TEXT NOT NULL,
                    exit_predicate TEXT NOT NULL, max_iterations INTEGER NOT NULL,
                    epistemic_status TEXT NOT NULL);
                CREATE TABLE loop_gestalts (loop_id TEXT NOT NULL,
                    gestalt_id TEXT NOT NULL, role TEXT NOT NULL,
                    PRIMARY KEY (loop_id, gestalt_id, role));
                INSERT INTO gestalts VALUES ('test','🧪','test','eval','G','n');
                INSERT INTO tote_loops VALUES ('code.unit_test_repair',
                    'Unit-test repair','software-engineering',
                    'Make the test suite pass.','Run tests.','All pass.',10,'CANONICAL');
                INSERT INTO loop_gestalts VALUES ('code.unit_test_repair','test','process-context');
            """)
            conn.commit()
            conn.close()
            h = build_handoff(SENTENCE, db_path=db)
            self.assertTrue(h["tote"]["matched"])
            self.assertEqual(h["tote"]["loop"]["loop_id"], "code.unit_test_repair")

    def test_missing_db_is_disclosed_fallback(self):
        h = build_handoff(SENTENCE, db_path="/nonexistent/t.sqlite3")
        self.assertFalse(h["tote"]["matched"])
        self.assertEqual(h["tote"]["fallback"], "state_roles")


if __name__ == "__main__":
    unittest.main()


class ProtectedTermHandoffTests(unittest.TestCase):
    def test_protected_terms_never_in_needs_mapping(self):
        h = build_handoff("prescribed metformin after the consult")
        needs = [d["word"].lower() for d in h["needs_mapping"]]
        self.assertNotIn("metformin", needs)
        protected = {p["word"]: p for p in h["protected"]}
        self.assertIn("metformin", protected)
        self.assertEqual(protected["metformin"]["render"], "literal")
        self.assertEqual(protected["metformin"]["category"], "drug")

    def test_person_name_protected_in_handoff(self):
        h = build_handoff("emailed Nicholas Hartman the report")
        needs = [d["word"] for d in h["needs_mapping"]]
        self.assertNotIn("Nicholas", needs)
        self.assertNotIn("Hartman", needs)
        self.assertIn("report", [w.lower() for w in needs])

    def test_protection_rule_present_in_discretion_rules(self):
        h = build_handoff("fixed the build")
        self.assertTrue(any("NOT rendered into Gestalt" in r
                            for r in h["discretion_rules"]))
