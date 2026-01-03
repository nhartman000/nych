"""
Natural language → NYCH mapping

Rules:
- NOT reversible sentence reconstruction
- Must recover most likely intent + outcome
- Pronouns & identifiers are lossy unless critical
"""

from .lexicon import LEXICON

def map_natural_language(text: str):
    mapped = []

    lower = text.lower()

    for glyph, symbol in LEXICON.items():
        if symbol.name in lower:
            mapped.append(symbol)

    return mapped
