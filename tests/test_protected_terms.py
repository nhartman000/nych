import unittest

from nych.protected_terms import find_protected, protected_positions


def words(sentence):
    return [r["word"] for r in find_protected(sentence)]


class ProtectedTermTests(unittest.TestCase):
    def test_known_drug_protected(self):
        recs = find_protected("prescribed metformin after the diagnosis")
        self.assertEqual(recs[0]["word"], "metformin")
        self.assertEqual(recs[0]["category"], "drug")

    def test_drug_suffix_protected(self):
        recs = find_protected("started cloxacillin yesterday")
        self.assertEqual(recs[0]["category"], "drug")
        self.assertEqual(recs[0]["reason"], "pharmaceutical name suffix")

    def test_binomial_scientific_name_protected(self):
        recs = find_protected("cultured Escherichia coli overnight")
        self.assertEqual([r["word"] for r in recs], ["Escherichia", "coli"])
        self.assertTrue(all(r["category"] == "scientific" for r in recs))

    def test_abbreviated_binomial_protected(self):
        recs = find_protected("the E. coli sample grew")
        self.assertEqual([r["word"] for r in recs], ["E.", "coli"])

    def test_honorific_name_protected(self):
        recs = find_protected("spoke with Dr. Hartman about results")
        self.assertEqual([r["word"] for r in recs], ["Hartman"])
        self.assertEqual(recs[0]["category"], "person")

    def test_capitalized_pair_mid_sentence_protected(self):
        recs = find_protected("emailed Nicholas Hartman the report")
        self.assertEqual([r["word"] for r in recs], ["Nicholas", "Hartman"])

    def test_sentence_initial_capital_not_person(self):
        # "Re-ran both test suites" -- sentence-initial capitalization is
        # not evidence of a person name.
        self.assertEqual(words("Re-ran both test suites after changes"), [])

    def test_ordinary_sentence_has_no_protected_terms(self):
        self.assertEqual(words("fixed the build before the release"), [])

    def test_lowercase_genus_word_alone_not_protected(self):
        # "homo" lowercase mid-sentence without species pattern: binomial
        # rule requires the capitalized genus form.
        self.assertEqual(words("the homo sapiens debate"), [])

    def test_name_pair_at_sentence_start_protected(self):
        recs = find_protected("Nicholas Hartman fixed the build")
        self.assertEqual([r["word"] for r in recs], ["Nicholas", "Hartman"])
        self.assertTrue(all(r["category"] == "person" for r in recs))

    def test_sentence_opener_not_paired_into_a_name(self):
        recs = find_protected("Then Maurice called about the build")
        self.assertEqual([(r["word"], r["category"]) for r in recs],
                         [("Maurice", "possible_name")])

    def test_lone_first_name_mid_sentence_protected(self):
        recs = find_protected("emailed Maurice the report")
        self.assertEqual([(r["word"], r["category"]) for r in recs],
                         [("Maurice", "possible_name")])

    def test_single_capital_letter_without_period_is_not_a_genus(self):
        self.assertEqual(words("A dog chased the cat"), [])

    def test_pronoun_i_not_protected(self):
        self.assertEqual(words("then I re-ran it and I'm done"), [])

    def test_after_period_counts_as_sentence_start(self):
        # "Fixed" begins a new sentence: not a lone mid-sentence name.
        self.assertEqual(words("shipped it. Fixed the build"), [])

    def test_lone_sentence_initial_name_is_known_gap(self):
        # Disclosed limitation: indistinguishable from any capitalized
        # opener without a name list.
        self.assertEqual(words("Maurice called about the build"), [])

    def test_protected_positions_keyed_by_token_index(self):
        pos = protected_positions("gave Mrs. Chen the metformin")
        self.assertIn(2, pos)   # Chen
        self.assertIn(4, pos)   # metformin


if __name__ == "__main__":
    unittest.main()
