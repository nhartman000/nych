import json
import subprocess
import sys
import unittest

from nych.competency import (
    analyze_utterance,
    classify_domain,
    classify_modality,
    competency_score,
)


class CompetencyTests(unittest.TestCase):
    def test_classify_modality_matches_word_boundary_safe(self):
        modality, hits = classify_modality("I can visualize the whole layout in my head")
        self.assertEqual(modality, "VISUAL_INTERNAL")
        self.assertGreaterEqual(hits, 1)

    def test_classify_modality_does_not_substring_match(self):
        # "throughput" contains "rough" -- must not trip KINESTHETIC_EXTERNAL's
        # "rough" marker. Regression test for the exact bug noted in this
        # module's origin (niche_protocol.py).
        modality, hits = classify_modality("we need to improve system throughput")
        self.assertNotEqual(modality, "KINESTHETIC_EXTERNAL")

    def test_classify_modality_unresolved_when_no_marker_present(self):
        modality, hits = classify_modality("the meeting is at three o'clock")
        self.assertEqual(modality, "UNRESOLVED")
        self.assertEqual(hits, 0)

    def test_classify_domain_detects_computer_science_jargon(self):
        domain, hits = classify_domain("the recursion caused a buffer allocation issue")
        self.assertEqual(domain, "COMPUTER_SCIENCE")
        self.assertGreaterEqual(hits, 2)

    def test_classify_domain_detects_manual_trades_jargon(self):
        domain, hits = classify_domain("check the fastener torque and countersink depth")
        self.assertEqual(domain, "MANUAL_TRADES")

    def test_classify_domain_unresolved_for_ordinary_sentence(self):
        # Honest negative case: most everyday text isn't jargon-heavy in any
        # of the three listed domains, and should say so rather than guess.
        domain, hits = classify_domain("we went to the store and bought some bread")
        self.assertEqual(domain, "UNRESOLVED")
        self.assertEqual(hits, 0)

    def test_competency_score_rewards_jargon_and_diversity(self):
        fluent = competency_score(
            "the recursion caused a manifold boundary invariant violation",
            "COMPUTER_SCIENCE",
        )
        hedged = competency_score(
            "i guess it's sort of maybe a recursion thing, i dunno",
            "COMPUTER_SCIENCE",
        )
        self.assertGreater(fluent, hedged)

    def test_competency_score_bounded_one_to_ten(self):
        self.assertGreaterEqual(competency_score("", "COMPUTER_SCIENCE"), 1)
        self.assertLessEqual(competency_score("", "COMPUTER_SCIENCE"), 10)

    def test_analyze_utterance_combines_all_three(self):
        result = analyze_utterance("the recursion feels off, the buffer looks wrong")
        self.assertEqual(result["domain"], "COMPUTER_SCIENCE")
        self.assertIn(result["modality"], ("KINESTHETIC_INTERNAL", "VISUAL_EXTERNAL"))
        self.assertIsInstance(result["competency"], int)

    def test_analyze_utterance_competency_none_when_domain_unresolved(self):
        # Honest gap: without a resolvable domain there's no vernacular to
        # score fluency against, so competency is None, not a fabricated
        # number.
        result = analyze_utterance("the weather was nice today")
        self.assertEqual(result["domain"], "UNRESOLVED")
        self.assertIsNone(result["competency"])

    def test_cli_analyze_outputs_valid_json(self):
        completed = subprocess.run(
            [sys.executable, "-m", "nych.cli", "analyze",
             "the recursion feels off, the buffer looks wrong"],
            check=True, text=True, capture_output=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["domain"], "COMPUTER_SCIENCE")


if __name__ == "__main__":
    unittest.main()
