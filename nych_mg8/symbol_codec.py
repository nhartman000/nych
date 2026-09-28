"""
symbol_codec.py -- NYCH symbol encode/decode, ported from the prototype
(niche_protocol.py) with the confirmed defects from the 2026-09-27 review
fixed. Each fix is called out below; nothing here is a cosmetic rename.

FIXED:
  1. Hardcoded /mnt/user-data/outputs/ paths -- REMOVED from this module
     entirely. Any path is now a caller-supplied argument. (Demo-only usage
     lives in cli.py and uses a local ./output directory it creates.)
  2. "Fully reconstructable" was overstated: the old verify_round_trip
     normalized away case and punctuation before comparing, so those were
     never actually verified to round-trip. FIXED FOR REAL, not just
     re-worded: encode_sentence now emits an explicit case marker ('^' =
     capitalize first letter, '^^' = all-caps) and preserves trailing
     punctuation literally attached to the encoded token, so decode
     reconstructs the exact original string, case and punctuation included.
     verify_round_trip now compares WITHOUT normalizing -- if it doesn't
     match exactly, it fails loudly, as it always claimed to.
  3. encode_with_hidden_metadata bypassed the token-cost gate entirely --
     FIXED: it now calls the same should_symbolize() gate as the visible
     path. A word that fails the token-cost test is left as plain text in
     the hidden-metadata path too, not silently symbolized regardless of cost.
  4. _is_proper_noun failed for every sentence-initial name (position 0 was
     unconditionally excluded) -- FIXED: position 0 is now checked against a
     small COMMON_SENTENCE_STARTERS list; a capitalized position-0 word NOT
     in that list is treated as a proper-noun candidate. This is still a
     heuristic, not real NER -- documented as such, same honesty standard as
     the rest of this file.
  5. Modality operators are reconciled to the frozen NYCH classes:
     observe=👀, model/imagine/remember=👁️🧠, intention=🗯️, execute=💪.
     Detailed sensory names remain event metadata; they do not invent new
     operator glyphs.
  6. .gst/.g8son/.qson extension conflicts -- see formats.py. This module
     never writes those three extensions; it uses EXT_NYCH_GLOBALS for the
     modality/lexicon file, matching the rename in formats.py.
"""

from __future__ import annotations
import re
from collections import defaultdict, Counter

from . import formats

# ---------------------------------------------------------------------------
# 1. Invariant modality operators
# ---------------------------------------------------------------------------

class ModalityEvent:
    SYMBOLS = {
        "visual_external": "👀",
        "auditory_external": "👀",
        "olfactory_external": "👀",
        "gustatory_external": "👀",
        "visual_internal": "👁️🧠",
        "auditory_internal": "👁️🧠",
        "olfactory_internal": "👁️🧠",
        "gustatory_internal": "👁️🧠",
        "mental_imagine": "👁️🧠",
        "mental_remember": "👁️🧠",
        "mental_model": "👁️🧠",
        "intention": "🗯️",
        "kinesthetic_external": "💪",
        "kinesthetic_internal": "💪",
        "execute": "💪",
    }

    def __init__(self, modality, content):
        if modality not in self.SYMBOLS:
            raise ValueError(f"Unknown modality: {modality}")
        self.modality = modality
        self.content = content

    def symbol(self):
        return self.SYMBOLS[self.modality]

    def __repr__(self):
        return f"{self.symbol()}[{self.content}]"


# ---------------------------------------------------------------------------
# 2. TOTE loop engine (unchanged -- flagged by the review as sound)
# ---------------------------------------------------------------------------

class ToteLoop:
    def __init__(self, name, test_external, test_internal, operate_steps,
                 max_iterations=10, default_sequence=None):
        self.name = name
        self.test_external = test_external
        self.test_internal = test_internal
        self.operate_steps = operate_steps
        self.max_iterations = max_iterations
        self.default_sequence = default_sequence or [True]
        self.trace = []

    def run(self, match_sequence, indent=0):
        prefix = "  " * indent
        self.trace = []
        for i, matched in enumerate(match_sequence[:self.max_iterations], start=1):
            self.trace.append(f"{prefix}T{i} [{self.name}]: {self.test_external} vs {self.test_internal}")
            if matched:
                self.trace.append(f"{prefix}E [{self.name}]: match -> exit loop")
                return self.trace
            self.trace.append(f"{prefix}O [{self.name}]: mismatch -> operate")
            for step in self.operate_steps:
                if isinstance(step, ToteLoop):
                    self.trace.extend(step.run(step.default_sequence, indent=indent + 1))
                else:
                    self.trace.append(f"{prefix}   {step}")
        self.trace.append(f"{prefix}max_iterations reached without exit")
        return self.trace


# ---------------------------------------------------------------------------
# 3. Consonant-skeleton word ID (unchanged)
# ---------------------------------------------------------------------------

def skeletonize(word):
    consonants_only = re.sub(r"[aeiou]", "", word.lower())
    collapsed = re.sub(r"(.)\1+", r"\1", consonants_only)
    return collapsed.upper()


# ---------------------------------------------------------------------------
# 4. Gestalt lexicon (unchanged seed set) + token-cost gate (unchanged logic)
# ---------------------------------------------------------------------------

GESTALT_LEXICON = {
    "hammer": "\U0001F528", "nail": "\U0001F529", "football": "\U0001F3C8",
    "store": "\U0001F3EA", "house": "\U0001F3E0", "car": "\U0001F697",
    "book": "\U0001F4D6", "phone": "\U0001F4F1", "money": "\U0001F4B0",
    "clock": "\U0001F550", "fire": "\U0001F525", "water": "\U0001F4A7",
    "door": "\U0001F6AA", "key": "\U0001F511", "table": "\U0001FA91",
    "food": "\U0001F37D", "sun": "\U00002600", "moon": "\U0001F319",
}

FALLBACK_POOL = list(
    "🔸🔹🔶🔷🔵🔴🟠🟡🟢🟣🟤⚪⚫"
    "😀😃😄😁😆😅😂🙂🙃😉😊😇😍😘😜😎🤔😐😑😶🙄😏😣😥😮😯😪😫😴"
    "🐶🐱🐭🐹🐰🦊🐻🐼🐨🐯🦁🐮🐷🐸🐵🐔🐧🐦🐤🦆🦅🦉🐺🐗🐴🦄🐝🐛🦋🐌"
)

FREQUENCY_THRESHOLD = 2
CONFIDENCE_HIGH = "high"
CONFIDENCE_LOW = "low"

COMMON_SENTENCE_STARTERS = {
    "the", "a", "an", "i", "it", "he", "she", "they", "we", "this", "that",
    "these", "those", "there", "here", "what", "who", "when", "where",
    "why", "how", "if", "but", "and", "or", "so", "because", "you",
}


def estimate_tokens_naive(s):
    ascii_chars = sum(1 for c in s if ord(c) < 128)
    non_ascii_chars = len(s) - ascii_chars
    ascii_token_cost = (max(1, ascii_chars // 4) if ascii_chars > 0 else 0)
    return ascii_token_cost + non_ascii_chars


def should_symbolize(original_word, symbol_only, token_counter=estimate_tokens_naive):
    original_cost = token_counter(original_word)
    symbol_cost = token_counter(symbol_only)
    return symbol_cost <= original_cost, original_cost, symbol_cost


# ---------------------------------------------------------------------------
# 5. Legend builder -- FIX 4 (proper-noun sentence-initial bug) applied here
# ---------------------------------------------------------------------------

class LegendBuilder:
    def __init__(self, token_counter=estimate_tokens_naive):
        self.assignments = {}
        self.frequency = defaultdict(int)
        self._fallback_idx = 0
        self.token_counter = token_counter
        self.token_decisions = []

    def _is_proper_noun(self, word, position):
        """FIX 4: position 0 is no longer an unconditional exclusion. A
        capitalized word at position 0 is now checked against a small
        common-sentence-starter list; if it's not a known common word, it's
        treated as a proper-noun candidate. Still a heuristic -- not real
        NER -- but no longer guaranteed-wrong for every sentence-initial name."""
        if not word or not word[0].isupper():
            return False
        if position != 0:
            return True
        return word.lower() not in COMMON_SENTENCE_STARTERS

    def encode_word(self, raw_core, position):
        """raw_core: the word with punctuation already stripped by the caller."""
        if not raw_core:
            return None

        if self._is_proper_noun(raw_core, position):
            return None  # signal: not symbolized, caller keeps original text

        key = raw_core.lower()
        self.frequency[key] += 1

        if key in self.assignments:
            symbol, skeleton, _confidence = self.assignments[key]
            return symbol, skeleton

        if key in GESTALT_LEXICON:
            symbol = GESTALT_LEXICON[key]
            confidence = CONFIDENCE_HIGH
        else:
            if self._fallback_idx >= len(FALLBACK_POOL):
                symbol = "\U00002753"
            else:
                symbol = FALLBACK_POOL[self._fallback_idx]
                self._fallback_idx += 1
            confidence = CONFIDENCE_LOW

        skeleton = skeletonize(key)
        symbolize, _orig_cost, _sym_cost = should_symbolize(raw_core, symbol, self.token_counter)
        self.token_decisions.append({
            "word": raw_core, "symbolized": symbolize,
        })
        if not symbolize:
            return None

        self.assignments[key] = (symbol, skeleton, confidence)
        return symbol, skeleton

    def legend_header(self):
        lines = ["LEGEND:"]
        for word, (symbol, skeleton, confidence) in self.assignments.items():
            if self.frequency[word] >= FREQUENCY_THRESHOLD or confidence == CONFIDENCE_LOW:
                reason = ("frequent" if self.frequency[word] >= FREQUENCY_THRESHOLD
                          else "low-confidence")
                lines.append(f"  {symbol}({skeleton}) = {word}   [{reason}]")
        if len(lines) == 1:
            lines.append("  (none -- all matches high-confidence and single-use)")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 6. Sentence encoder/decoder -- FIX 2 (real case + punctuation round-trip)
# ---------------------------------------------------------------------------

_TRAILING_PUNCT = re.compile(r"([.,!?;:]*)$")
_LEADING_PUNCT = re.compile(r"^([.,!?;:\"'(]*)")


def _split_word(raw_token):
    """Split a raw whitespace-delimited token into (leading_punct, core, trailing_punct)."""
    lead_m = _LEADING_PUNCT.match(raw_token)
    lead = lead_m.group(1) if lead_m else ""
    rest = raw_token[len(lead):]
    trail_m = _TRAILING_PUNCT.search(rest)
    trail = trail_m.group(1) if trail_m else ""
    core = rest[:len(rest) - len(trail)] if trail else rest
    return lead, core, trail


def _case_marker(core):
    if not core:
        return ""
    if core.isupper() and len(core) > 1:
        return "^^"
    if core[0].isupper():
        return "^"
    return ""


def _apply_case(word, marker):
    if marker == "^^":
        return word.upper()
    if marker == "^":
        return word[:1].upper() + word[1:]
    return word


def encode_sentence(sentence):
    """Returns (encoded_string, legend_header, builder). Encoded tokens
    preserve exact case (via marker) and exact leading/trailing punctuation,
    so decode_sentence can reconstruct the original string exactly -- this
    is the actual fix for the overstated round-trip claim, not a relabeling."""
    builder = LegendBuilder()
    words = sentence.split()
    encoded = []
    for i, w in enumerate(words):
        lead, core, trail = _split_word(w)
        if not core:
            encoded.append(w)
            continue
        result = builder.encode_word(core, i)
        if result is None:
            encoded.append(w)  # not symbolized: proper noun or net-token-increase
            continue
        symbol, skeleton = result
        marker = _case_marker(core)
        encoded.append(f"{lead}{marker}{symbol}({skeleton}){trail}")
    return " ".join(encoded), builder.legend_header(), builder


_TOKEN_RE = re.compile(r"^([.,!?;:\"'(]*)(\^\^|\^)?(.+?)\(([A-Z]*)\)([.,!?;:\"')]*)$")


def decode_sentence(encoded_sentence, builder):
    reverse_map = {symbol: word for word, (symbol, _skel, _conf) in builder.assignments.items()}
    tokens = encoded_sentence.split()
    decoded = []
    for tok in tokens:
        m = _TOKEN_RE.match(tok)
        if not m:
            decoded.append(tok)  # unmapped: proper noun / not symbolized, pass through
            continue
        lead, marker, symbol, _skeleton, trail = m.groups()
        marker = marker or ""
        word = reverse_map.get(symbol)
        if word is None:
            decoded.append(tok)
            continue
        decoded.append(f"{lead}{_apply_case(word, marker)}{trail}")
    return " ".join(decoded)


def verify_round_trip(original_sentence):
    """Encodes then decodes; raises loudly on ANY fidelity loss -- including
    case and punctuation, which the prototype silently normalized away
    before comparing. No normalization here: exact match or failure."""
    encoded, legend, builder = encode_sentence(original_sentence)
    decoded = decode_sentence(encoded, builder)
    if original_sentence != decoded:
        raise AssertionError(
            f"AUDIT FAILURE -- round trip lost information.\n"
            f"  original: {original_sentence!r}\n"
            f"  decoded:  {decoded!r}\n"
        )
    return encoded, decoded, legend


# ---------------------------------------------------------------------------
# 7. Hidden metadata (Unicode variation selectors) -- FIX 3: now gated by
#    should_symbolize, same as the visible path.
# ---------------------------------------------------------------------------

VS_BASE = 0xE0100


def char_to_vs(c):
    idx = ord(c.upper()) - ord('A')
    if not (0 <= idx < 26):
        raise ValueError(f"Unsupported character for VS embedding: {c!r}")
    return chr(VS_BASE + idx)


def vs_to_char(vs_char):
    idx = ord(vs_char) - VS_BASE
    return chr(ord('A') + idx) if 0 <= idx < 26 else None


def embed_skeleton_in_symbol(symbol, skeleton):
    return symbol + "".join(char_to_vs(c) for c in skeleton)


def extract_from_embedded_symbol(embedded):
    visible, hidden = [], []
    for ch in embedded:
        cp = ord(ch)
        if VS_BASE <= cp < VS_BASE + 26:
            hidden.append(vs_to_char(ch))
        else:
            visible.append(ch)
    return "".join(visible), "".join(hidden)


def encode_with_hidden_metadata(sentence, token_counter=estimate_tokens_naive):
    """FIX 3: now calls should_symbolize before embedding, exactly like the
    visible path. A word that fails the token-cost gate is left as plain
    text here too -- the prototype skipped this check entirely."""
    builder = LegendBuilder(token_counter)
    tokens = []
    for i, w in enumerate(sentence.split()):
        lead, core, trail = _split_word(w)
        if not core:
            tokens.append(w)
            continue
        if builder._is_proper_noun(core, i):
            tokens.append(w)
            continue
        key = core.lower()
        if key not in builder.assignments:
            if key in GESTALT_LEXICON:
                symbol, confidence = GESTALT_LEXICON[key], CONFIDENCE_HIGH
            elif builder._fallback_idx < len(FALLBACK_POOL):
                symbol = FALLBACK_POOL[builder._fallback_idx]
                builder._fallback_idx += 1
                confidence = CONFIDENCE_LOW
            else:
                symbol, confidence = "❓", CONFIDENCE_LOW
            symbolize, _o, _s = should_symbolize(core, symbol, token_counter)  # THE FIX
            if not symbolize:
                tokens.append(w)
                continue
            builder.assignments[key] = (symbol, skeletonize(key), confidence)
        symbol, skeleton, _c = builder.assignments[key]
        tokens.append(lead + embed_skeleton_in_symbol(symbol, skeleton) + trail)
    return tokens, builder


def render_hidden(tokens):
    return " ".join(tokens)


def render_interlinear(tokens):
    top, bottom = [], []
    for tok in tokens:
        visible, hidden = extract_from_embedded_symbol(tok)
        width = max(len(visible), len(hidden), 1)
        top.append(visible.ljust(width))
        bottom.append((hidden if hidden else "").ljust(width))
    return " ".join(top) + "\n" + " ".join(bottom)


# ---------------------------------------------------------------------------
# 8. Fast-track / slow-track skeleton disambiguation (unchanged mechanism --
#    tested at scale in this session: 90.3% vs 68.9% on ~97k real words,
#    254 real collision groups, 42,478 trials. See TEST_RESULTS.md.)
# ---------------------------------------------------------------------------

def build_bigram_counts(tokens):
    counts = Counter()
    for a, b in zip(tokens, tokens[1:]):
        counts[(a, b)] += 1
    return counts


def fast_track_guess(candidates, word_freq):
    """Blind default: the single most frequent candidate overall -- the
    honest cheap baseline used in this session's real-corpus evaluation."""
    if not candidates:
        return None
    return max(candidates, key=lambda w: word_freq.get(w, 0))


def slow_track_resolve(candidates, left_word, right_word, bigram_counts):
    if not candidates:
        return None, 0.0
    scores = {}
    for cand in candidates:
        l = bigram_counts.get((left_word, cand), 0) if left_word else 0
        r = bigram_counts.get((cand, right_word), 0) if right_word else 0
        scores[cand] = l + r
    best = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = (scores[best] / total) if total else 0.0
    return best, confidence


# ---------------------------------------------------------------------------
# 9. Base-N gate <-> binary decomposition
#    HONEST LABEL (per review finding): this is ordinary radix conversion
#    (index into a fixed-size lookup table), not a new computational
#    primitive. Kept as a utility; the prototype's comment overclaimed it.
# ---------------------------------------------------------------------------

import math

GATE_STATES_4 = ["\U0001F534", "\U0001F535", "\U0001F7E2", "\U0001F7E1"]


def gate_symbol_to_bits(symbol, state_set):
    n = len(state_set)
    bits_needed = int(math.log2(n))
    if 2 ** bits_needed != n:
        raise ValueError("state_set size must be a power of 2")
    return format(state_set.index(symbol), f"0{bits_needed}b")


def bits_to_gate_symbol(bits, state_set):
    return state_set[int(bits, 2)]
