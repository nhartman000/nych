# NYCH

**NYCH** is Nicholas Hartman's symbolic language / locality research substrate. The current public Python package implements a small, inspectable foundation for symbolic glyphs, address-space placement, sequence encoding, lexicon lookup, plugin hooks, and visualization.

> **Implementation status:** this repository is a minimal software substrate, not a complete executable specification of every NYCH concept developed elsewhere. The code currently present should be treated as the authority for what this package actually implements.

## Current implementation

The package currently contains modules for:

- symbolic glyph objects and metadata;
- address construction / extension;
- encoding symbol sequences into address traces;
- decoding address traces back to glyph sequences;
- a temporary boot lexicon;
- mapping / inspection helpers;
- plugin API / plugin loading support;
- storage helpers;
- 3D visualization of NYCH locality.

The package metadata describes the project as a **deterministic symbolic language and visualization substrate**.

## Symbol model

The current `Symbol` type contains:

```python
Symbol(
    glyph: str,
    meaning: str,
    address: tuple,
    metadata: Any = None,
)
```

The current address representation uses four components. Visualization projects the first three components as:

```text
X = time
Y = region
Z = volume
D4 = additional context dimension
```

## Sequence encoding

`nych.encoding.encode_sequence()` takes a list of symbols plus a base address and extends the address with ordinal sequence position. The resulting representation retains both the glyph and its generated address trace.

Conceptually:

```text
symbol sequence
      ↓
base locality/address
      ↓
ordinal position added as an emergent dimension
      ↓
addressed symbolic trace
```

The current implementation is intentionally small and should not be read as a claim that ordinal position is the only possible NYCH dimensional transform.

## Boot lexicon

`nych/lexicon.py` currently contains a **temporary boot lexicon** used to satisfy engine contracts. The source itself explicitly states that it is temporary and intended to be replaced by loaded/authoritative lexicon material.

The repository therefore does not present the four current example glyphs as the complete NYCH language.

## CLI

After installation:

```bash
nych inspect
```

prints the current boot symbols, meanings, and addresses.

```bash
nych visualize
```

opens the locality visualizer.

To save a visualization:

```bash
nych visualize --save nych.png
```

## Installation

```bash
git clone https://github.com/nhartman000/nych.git
cd nych
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

The canonical packaging metadata is `pyproject.toml`.

## Repository boundaries

NYCH is used by other research/runtime work in this GitHub account, including MG8-related experiments. Those integrations should not redefine NYCH's own package semantics. Conversely, this small package should not be presented as implementing every higher-level MG8/TCTA concept.

Related public repositories:

- TCTA: https://github.com/nhartman000/TCTA-
- MG8: https://github.com/nhartman000/mg8
- MG8 reference runtime: https://github.com/nhartman000/mg8-engine

## Repository hygiene

Generated virtual environments, Python bytecode, build metadata, and visualization output are not source artifacts and are excluded by `.gitignore`.

A virtual environment had previously been committed to this repository. The current-tree cleanup removes it from active source control; historical Git objects may still contribute to repository size until a deliberate history-cleaning operation is performed.
