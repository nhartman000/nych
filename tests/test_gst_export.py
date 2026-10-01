import json
import tempfile
import unittest
from pathlib import Path

from nych.gst_export import GST_VERSION, build_gst, write_gst
from nych.session_invariants import SessionInvariants

SENTENCE = "the recursion feels off, re-ran both test suites after changes"


class GstExportTests(unittest.TestCase):
    def test_shape_matches_engine_gst_fields(self):
        gst = build_gst(SENTENCE)
        self.assertEqual(gst["gst_version"], GST_VERSION)
        self.assertTrue(gst["state_id"].startswith("nych-"))
        self.assertIsInstance(gst["state"], dict)
        self.assertEqual(gst["state"]["source_text"], SENTENCE)

    def test_domain_lowercased_from_analysis(self):
        gst = build_gst(SENTENCE)
        self.assertEqual(gst["domain"], "computer_science")

    def test_unresolved_domain_maps_to_general(self):
        gst = build_gst("we went to the store")
        self.assertEqual(gst["domain"], "general")
        self.assertEqual(gst["nych_pretext"]["analysis"]["domain"], "UNRESOLVED")
        self.assertIsNone(gst["nych_pretext"]["analysis"]["competency"])

    def test_pruning_instructions_and_dither_present(self):
        gst = build_gst(SENTENCE, dither=0.25)
        pruning = gst["nych_pretext"]["pruning"]
        self.assertEqual(pruning["dither"], 0.25)
        self.assertTrue(any("dither" in i for i in pruning["instructions"]))
        self.assertTrue(any("domain" in i for i in pruning["instructions"]))

    def test_dither_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            build_gst(SENTENCE, dither=1.5)

    def test_no_db_means_no_tote_claims(self):
        gst = build_gst(SENTENCE)
        self.assertIsNone(gst["nych_pretext"]["tote_match"])
        self.assertIsNone(gst["nych_pretext"]["tote_fallback"])

    def test_missing_db_fallback_is_carried_not_hidden(self):
        gst = build_gst(SENTENCE, db_path="/nonexistent/db.sqlite3")
        self.assertIsNone(gst["nych_pretext"]["tote_match"])
        self.assertEqual(gst["nych_pretext"]["tote_fallback"]["fallback"],
                         "state_roles")

    def test_pinned_mappings_included(self):
        session = SessionInvariants()
        session.pin("suites", "gestalt.sts")
        gst = build_gst(SENTENCE, session=session)
        pinned = [p["word"] for p in gst["nych_pretext"]["pinned"]]
        self.assertIn("suites", pinned)
        needs = [d["word"] for d in gst["nych_pretext"]["needs_mapping"]]
        self.assertNotIn("suites", needs)

    def test_write_gst_roundtrips_as_json(self):
        gst = build_gst(SENTENCE)
        with tempfile.TemporaryDirectory() as tmp:
            path = write_gst(gst, Path(tmp) / "out.gst")
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded, gst)

    def test_state_id_deterministic_for_same_text(self):
        self.assertEqual(build_gst(SENTENCE)["state_id"],
                         build_gst(SENTENCE)["state_id"])


if __name__ == "__main__":
    unittest.main()
