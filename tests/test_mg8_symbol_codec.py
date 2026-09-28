"""Real tests of the symbol codec fixes -- proper-noun position-0 bug,
case/punctuation round-trip, hidden-metadata token-cost gate."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nych_mg8 import symbol_codec as sc

FAILURES = []


def check(cond, label):
    print(f"  {'OK ' if cond else 'FAIL'} {label}")
    if not cond:
        FAILURES.append(label)


def test_sentence_initial_proper_noun_now_detected():
    """FIX 4: the old rule (position != 0) guaranteed every sentence-initial
    name was misclassified. This is the regression test for that fix."""
    builder = sc.LegendBuilder()
    check(builder._is_proper_noun("Maria", 0) is True,
          "sentence-initial capitalized non-common-word IS now flagged proper noun")
    check(builder._is_proper_noun("The", 0) is False,
          "sentence-initial common word ('The') correctly NOT flagged as proper noun")
    check(builder._is_proper_noun("Maria", 3) is True,
          "mid-sentence capitalized word still flagged proper noun (unchanged behavior)")


def test_roundtrip_preserves_case_and_punctuation():
    """FIX 2: verify_round_trip no longer silently normalizes away case and
    punctuation before comparing."""
    sentence = "I went to the store to buy a hammer and a table."
    encoded, decoded, legend = sc.verify_round_trip(sentence)
    check(decoded == sentence, f"exact round-trip including case/punctuation: {decoded!r} == {sentence!r}")


def test_roundtrip_with_capitalized_word_mid_sentence():
    sentence = "The Hammer was heavy and the Table was old."
    encoded, decoded, legend = sc.verify_round_trip(sentence)
    check(decoded == sentence, f"capitalization mid-sentence preserved exactly: {decoded!r}")


def test_hidden_metadata_respects_token_cost_gate():
    """FIX 3: hidden-metadata encoding must call should_symbolize, same as
    the visible path -- not bypass the gate."""
    # Force a token_counter that makes symbolizing ANY word a net increase,
    # so nothing should get embedded.
    def always_expensive(s):
        # penalize non-ASCII (symbols) heavily so plain text always wins the
        # should_symbolize() comparison, regardless of word length
        non_ascii = sum(1 for c in s if ord(c) >= 128)
        ascii_chars = sum(1 for c in s if ord(c) < 128)
        return non_ascii * 1000 + ascii_chars
    tokens, builder = sc.encode_with_hidden_metadata("I bought a hammer today", always_expensive)
    any_hidden = any(any(sc.VS_BASE <= ord(c) < sc.VS_BASE + 26 for c in tok) for tok in tokens)
    check(not any_hidden, "hidden-metadata path respects the token-cost gate (no embedding when uneconomical)")

    # With the normal (cheap) counter, hammer SHOULD get symbolized since a
    # single gestalt emoji is cheaper than the word "hammer".
    tokens2, builder2 = sc.encode_with_hidden_metadata("I bought a hammer today")
    any_hidden2 = any(any(sc.VS_BASE <= ord(c) < sc.VS_BASE + 26 for c in tok) for tok in tokens2)
    check(any_hidden2, "hidden-metadata path DOES embed when it passes the token-cost gate")


def test_fast_slow_track_mechanism_still_works():
    """Sanity check that the tested (90.3% vs 68.9% on real data) mechanism
    is intact after the refactor, on the original toy example."""
    corpus = ["i ate a piece of bread for breakfast", "she baked fresh bread this morning",
              "the bread was warm and soft", "i felt bored during the long meeting",
              "he was bored and started doodling", "waiting in line made her bored"]
    tokens = " ".join(corpus).split()
    word_freq = {}
    for w in tokens:
        word_freq[w] = word_freq.get(w, 0) + 1
    bigrams = sc.build_bigram_counts(tokens)
    candidates = ["bread", "bored"]
    fast = sc.fast_track_guess(candidates, word_freq)
    # real bigram signal: "her bored" appears in the corpus, "her bread" does not
    slow, conf = sc.slow_track_resolve(candidates, "her", None, bigrams)
    check(fast == "bread", "fast track picks the more frequent candidate (unchanged)")
    check(slow == "bored" and conf > 0,
          f"slow track uses real 'her bored' bigram signal to override fast track's 'bread' default (got {slow!r})")


if __name__ == "__main__":
    test_sentence_initial_proper_noun_now_detected()
    test_roundtrip_preserves_case_and_punctuation()
    test_roundtrip_with_capitalized_word_mid_sentence()
    test_hidden_metadata_respects_token_cost_gate()
    test_fast_slow_track_mechanism_still_works()

    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("\nAll symbol_codec tests passed.")
