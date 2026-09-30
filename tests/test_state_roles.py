import json
import subprocess
import sys
import unittest

from nych.state_roles import tag_roles


class StateRoleTests(unittest.TestCase):
    def test_worked_example_reran_test_suites(self):
        result = tag_roles("Re-ran both test suites after changes")
        self.assertEqual(result["action"]["word"], "Re-ran")
        self.assertEqual(result["action"]["lemma"], "run")
        self.assertEqual(result["enumerator"]["word"], "both")
        self.assertEqual(result["object"]["word"], "test suites")
        self.assertEqual(result["tense"]["word"], "after")
        self.assertEqual(result["state"]["word"], "changes")

    def test_regular_ed_verb_detected(self):
        result = tag_roles("closed the account after the deposit")
        self.assertEqual(result["action"]["word"], "closed")
        self.assertEqual(result["action"]["lemma"], "clos")
        self.assertEqual(result["tense"]["word"], "after")
        self.assertEqual(result["state"]["word"], "the deposit")

    def test_no_enumerator_present(self):
        # Honest gap: when no enumerator word appears, the field is None,
        # not a forced guess.
        result = tag_roles("fixed the build before the release")
        self.assertIsNone(result["enumerator"])
        self.assertEqual(result["action"]["word"], "fixed")
        self.assertEqual(result["object"]["word"], "the build")
        self.assertEqual(result["tense"]["word"], "before")

    def test_no_tense_marker_present(self):
        # Honest gap: no relational-tense marker means no state value can
        # be extracted either -- both are None rather than guessed from
        # whatever text happens to be left over.
        result = tag_roles("built the pipeline")
        self.assertIsNone(result["tense"])
        self.assertIsNone(result["state"])
        self.assertEqual(result["object"]["word"], "the pipeline")

    def test_irregular_verb_went(self):
        result = tag_roles("went to the store before the meeting")
        self.assertEqual(result["action"]["lemma"], "go")

    def test_no_verb_at_all_action_is_none(self):
        result = tag_roles("the weather today")
        self.assertIsNone(result["action"])

    def test_object_excludes_action_and_enumerator_positions(self):
        result = tag_roles("tested several modules during the release")
        self.assertEqual(result["action"]["word"], "tested")
        self.assertEqual(result["enumerator"]["word"], "several")
        # object must start after the enumerator, not re-include it
        self.assertEqual(result["object"]["start"], 2)
        self.assertEqual(result["object"]["word"], "modules")

    def test_cli_parse_outputs_valid_json(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nych.cli", "parse",
             "Re-ran both test suites after changes"],
            check=True, text=True, capture_output=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["action"]["word"], "Re-ran")
        self.assertEqual(payload["state"]["word"], "changes")


if __name__ == "__main__":
    unittest.main()
