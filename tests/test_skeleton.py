import unittest

from nych.skeleton import consonant_skeleton, describe, skeleton_id


class SkeletonTests(unittest.TestCase):
    def test_vowels_removed(self):
        self.assertEqual(consonant_skeleton("suites"), "sts")

    def test_doubled_consonants_collapsed(self):
        self.assertEqual(consonant_skeleton("pattern"), "ptrn")

    def test_case_and_punctuation_ignored(self):
        self.assertEqual(consonant_skeleton("Re-ran"), "rrn")

    def test_all_vowel_word_gives_empty_skeleton(self):
        self.assertEqual(consonant_skeleton("eau"), "")

    def test_skeleton_id_embeds_namespace(self):
        self.assertEqual(skeleton_id("pattern"), "gestalt.ptrn")
        self.assertEqual(skeleton_id("pattern", "sym"), "sym.ptrn")

    def test_skeleton_id_fallback_for_all_vowel_word(self):
        # Disclosed fallback: plain lowercase letters, not invented consonants.
        self.assertEqual(skeleton_id("eau"), "gestalt.eau")

    def test_describe_discloses_fallback_flag(self):
        self.assertFalse(describe("pattern")["skeleton_fallback"])
        self.assertTrue(describe("eau")["skeleton_fallback"])

    def test_distinct_words_can_share_skeleton_not_hidden(self):
        # "bat" and "bet" both -> "bt": the clue narrows, it does not
        # uniquely identify. This is inherent to the rule, not a bug.
        self.assertEqual(consonant_skeleton("bat"), consonant_skeleton("bet"))


if __name__ == "__main__":
    unittest.main()
