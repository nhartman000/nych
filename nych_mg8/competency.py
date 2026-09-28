"""
competency.py -- Rule 3a: vernacular competency check + modality classifier.
Ported unchanged from niche_protocol.py -- the review flagged the
word-boundary-safe marker matching here as sound and worth retaining as-is.
Still a hand-built keyword lexicon, not a trained model (same honesty
standard as the rest of this package): a real, testable rule-based
classifier, not a claim of general natural-language understanding.
"""

from __future__ import annotations
import re

MODALITY_MARKERS = {
    "VISUAL_EXTERNAL": [
        "looks good", "looks right", "i see", "looks like", "appears", "watch",
        "observe", "picture this", "show me", "clear picture", "visibly", "on screen",
    ],
    "VISUAL_INTERNAL": [
        "i can see it", "envision", "imagine", "visualize", "in my mind's eye",
        "picture in my head", "mental image", "i can picture",
    ],
    "AUDITORY_EXTERNAL": [
        "sounds good", "sounds right", "i hear", "tell me", "that clicks",
        "loud and clear", "resonates aloud", "listen",
    ],
    "AUDITORY_INTERNAL": [
        "rings true", "sounds off in my head", "inner voice", "tells me", "quiet voice",
        "i keep telling myself", "self-talk",
    ],
    "KINESTHETIC_INTERNAL": [
        "feels right", "feels off", "doesn't feel right", "gut feeling", "sense that",
        "feel like", "comfortable with", "uneasy", "intuition",
    ],
    "KINESTHETIC_EXTERNAL": [
        "grasp", "handle", "grab", "solid", "smooth", "rough", "hands-on", "tangible",
        "pressure", "warm", "concrete feel",
    ],
}

HEDGES = ["i guess", "maybe", "sort of", "kind of", "i think", "not sure", "probably",
          "i dunno", "dunno", "whatever"]

DOMAIN_JARGON = {
    "COMPUTER_SCIENCE": ["algorithm", "recursion", "buffer", "latency", "throughput",
                          "manifold", "orthogonal", "invariant", "boundary", "vector",
                          "convergence", "midpoint", "allocation"],
    "MANUAL_TRADES": ["torque", "fastener", "kerf", "tolerance", "countersink",
                       "grain", "joist", "shim"],
    "MEDICAL": ["etiology", "differential", "contraindication", "prognosis",
                "presenting", "titrate", "comorbidity"],
}


def _marker_pattern(marker):
    return r"\b" + re.escape(marker) + r"\b"


def classify_modality(text):
    lower = text.lower()
    scores = {}
    for modality, markers in MODALITY_MARKERS.items():
        hits = sum(1 for m in markers if re.search(_marker_pattern(m), lower))
        if hits:
            scores[modality] = hits
    if not scores:
        return "UNRESOLVED", 0
    best = max(scores, key=scores.get)
    return best, scores[best]


def competency_score(text, domain):
    lower = text.lower()
    words = re.findall(r"[a-z']+", lower)
    if not words:
        return 1
    jargon = DOMAIN_JARGON.get(domain.upper(), [])
    jargon_hits = sum(1 for j in jargon if re.search(_marker_pattern(j), lower))
    hedge_hits = sum(1 for h in HEDGES if re.search(_marker_pattern(h), lower))
    diversity = len(set(words)) / len(words)
    raw = 2.0 + (jargon_hits * 1.8) + (diversity * 4.0) - (hedge_hits * 1.5)
    return max(1, min(10, round(raw)))
