"""
protected_terms.py -- terms that are NEVER rendered into Gestalt symbols.

Rule (canon): scientific names, names of people, and prescription drug
names are not Gestalt-mapped. They pass through the pipeline literally --
no glyph, no consonant-skeleton id, no #temp-invariant pin. The reason is
recoverability: these are precise referents where any symbolic compression
risks a dangerous or unrecoverable ambiguity (one drug name mistaken for
another, one species or person for another).

Detection heuristics, disclosed at the same honesty bar as the rest of
this package -- small hand-built lists and surface patterns, not NER:

    person      -- an honorific (Dr./Mr./Ms. ...) followed by capitalized
                   words; or an adjacent pair of capitalized words that is
                   not sentence-initial.
    scientific  -- a binomial pattern: a known genus (small list) or an
                   abbreviated genus ("E.") followed by a lowercase
                   species word.
    drug        -- a word on a small known-prescription-drug list, or one
                   carrying a characteristic pharmaceutical suffix
                   (-cillin, -statin, -pril, -azepam, ...).

These WILL miss names outside the lists/patterns and may occasionally
over-protect (e.g. a capitalized pair that isn't a person). Over-protection
is the safe failure mode here: a word wrongly left literal loses nothing,
while a protected term wrongly symbolized loses its referent.
"""

from __future__ import annotations

import re

HONORIFICS = {
    "mr", "mrs", "ms", "mx", "dr", "prof", "professor", "sir", "madam",
    "miss", "rev", "capt", "sgt", "lt", "col", "gen",
}

# Small known-genus list for binomial ("Genus species") detection.
GENERA = {
    "homo", "escherichia", "staphylococcus", "streptococcus", "salmonella",
    "drosophila", "arabidopsis", "saccharomyces", "canis", "felis", "mus",
    "rattus", "danio", "caenorhabditis", "bacillus", "mycobacterium",
    "plasmodium", "candida", "aspergillus", "clostridium", "helicobacter",
}

# Small known prescription-drug list.
KNOWN_DRUGS = {
    "metformin", "amoxicillin", "lisinopril", "atorvastatin", "sertraline",
    "fluoxetine", "warfarin", "prednisone", "gabapentin", "omeprazole",
    "levothyroxine", "amlodipine", "alprazolam", "lorazepam", "oxycodone",
    "hydrocodone", "insulin", "albuterol", "losartan", "metoprolol",
    "simvastatin", "azithromycin", "ciprofloxacin", "tramadol", "adderall",
    "ritalin", "xanax", "valium", "prozac", "zoloft", "lipitor", "ozempic",
}

# Characteristic pharmaceutical suffixes (INN naming stems).
DRUG_SUFFIXES = (
    "cillin", "mycin", "floxacin", "statin", "pril", "sartan", "olol",
    "dipine", "azole", "azepam", "oxetine", "prazole", "tinib", "ciclib",
    "mab", "nib", "vir", "gliptin", "glitazone", "setron", "triptan",
)

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'.-]*")


def _core(token: str) -> str:
    """Token stripped of surrounding punctuation, case preserved."""
    m = _WORD_RE.search(token)
    return m.group(0).rstrip(".-") if m else ""


def _is_capitalized(core: str) -> bool:
    return bool(core) and core[0].isupper() and core[1:].islower()


def _is_drug(core: str) -> bool:
    lower = core.lower()
    if lower in KNOWN_DRUGS:
        return True
    return len(lower) > 6 and any(lower.endswith(s) for s in DRUG_SUFFIXES)


def find_protected(sentence: str) -> list[dict]:
    """Find protected terms in `sentence`.

    Returns a list of {"word", "position", "category", "reason"} records,
    one per protected token, in token order. Tokens are whitespace-split to
    stay aligned with state_roles.tag_roles positions."""
    tokens = sentence.split()
    cores = [_core(t) for t in tokens]
    records: dict[int, dict] = {}

    def protect(i: int, category: str, reason: str) -> None:
        if i not in records and cores[i]:
            records[i] = {"word": tokens[i], "position": i,
                          "category": category, "reason": reason}

    for i, core in enumerate(cores):
        lower = core.lower()

        # drugs: position-independent list/suffix check
        if _is_drug(core):
            protect(i, "drug",
                    "known prescription drug" if lower in KNOWN_DRUGS
                    else "pharmaceutical name suffix")
            continue

        # scientific binomial: known or abbreviated genus + lowercase species
        abbrev_genus = bool(re.fullmatch(r"[A-Z]\.?", tokens[i].rstrip(",;:")))
        if (lower in GENERA or abbrev_genus) and i + 1 < len(cores):
            nxt = cores[i + 1]
            if nxt and nxt.islower():
                if lower in GENERA and _is_capitalized(core):
                    protect(i, "scientific", "binomial genus")
                    protect(i + 1, "scientific", "binomial species")
                    continue
                if abbrev_genus:
                    protect(i, "scientific", "abbreviated binomial genus")
                    protect(i + 1, "scientific", "binomial species")
                    continue

        # person: honorific followed by capitalized word(s)
        if lower in HONORIFICS and i + 1 < len(cores) and _is_capitalized(cores[i + 1]):
            protect(i + 1, "person", "follows honorific")
            j = i + 2
            while j < len(cores) and _is_capitalized(cores[j]):
                protect(j, "person", "follows honorific")
                j += 1
            continue

        # person: adjacent capitalized pair, not sentence-initial
        if (i > 0 and _is_capitalized(core) and i + 1 < len(cores)
                and _is_capitalized(cores[i + 1])
                and cores[i - 1] and not tokens[i - 1].endswith((".", "!", "?"))):
            protect(i, "person", "capitalized adjacent pair")
            protect(i + 1, "person", "capitalized adjacent pair")

    return [records[i] for i in sorted(records)]


def protected_positions(sentence: str) -> dict[int, dict]:
    """{token position -> protected record} for `sentence`."""
    return {r["position"]: r for r in find_protected(sentence)}
