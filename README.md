# NYCH

**NYCH** is Nicholas Hartman's symbolic language / locality research substrate. The public Python package implements an inspectable foundation for symbolic glyphs, address-space placement, sequence encoding, sense-first semantic encoding, multiword Gestalt compression, lexicon lookup, plugin hooks, and visualization.

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
- a persistent sense/Gestalt registry;
- explicit sense selection with auditable fallback resolution;
- longest-first multiword Gestalt matching with protected invariants.

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

Sense-first semantic encoding is available directly from the CLI:

```bash
nych encode "the unit test repair preserved the test suite"
nych encode "the river bank closed my account" \
  --sense 2=finance.bank.institution --json
```

`--sense POSITION=SENSE_ID` is repeatable and uses zero-based token positions.
An explicit sense always has higher authority than contextual cue matching. Use
`--no-spans` to disable multiword Gestalts or `--registry PATH` to test an
alternate registry.

## Sense registry and Gestalt spans

`nych/data/sense_registry.json` is the installed seed registry. It currently
contains 14 distinct senses and 11 curated multiword Gestalts. Stable semantic
IDs are separate from display glyphs so a glyph can change without changing
the meaning identifier.

`nych.semantic_encoding.encode_text()` resolves in this order:

1. explicit caller-supplied sense;
2. longest registered non-overlapping Gestalt span;
3. unambiguous surface form;
4. contextual cue match;
5. honest unresolved/default fallback.

Every result records its resolution method. Multiword records also retain the
canonical expression and protected invariants. `audit_summary()` reports source
word count, compressed semantic-unit count, method counts, and the fraction of
the source that depended on guessing.

This is deterministic registry matching, not semantic understanding. Registry
coverage is deliberately small, cue matching only considers immediate
neighbors, and unresolved ambiguity is not presented as certainty.

## Vernacular competency and domain classification

`nych.competency` classifies which sensory modality an utterance's language
leans on and which subject-matter domain its vocabulary belongs to, then
scores how fluently it uses that domain's vernacular:

```bash
nych analyze "the recursion feels off, the buffer looks wrong"
```

```json
{
  "text": "the recursion feels off, the buffer looks wrong",
  "modality": "KINESTHETIC_INTERNAL",
  "modality_score": 1,
  "domain": "COMPUTER_SCIENCE",
  "domain_score": 2,
  "competency": 9
}
```

This is intended as a step that can run *before* semantic encoding in a
larger pipeline — e.g. an MG8 gate runtime that routes or scores a gate
based on the speaker's domain and competency before the text is Gestalt-
encoded. Same honesty bar as the rest of this package: it's a small,
hand-built keyword lexicon (modality marker phrases, domain jargon lists,
hedge words), not a trained classifier, and it reports `"UNRESOLVED"` with
a `None` competency rather than forcing a guess when nothing in the text
matches its lexicon — most ordinary sentences will land there for domain.

## Pre-Gestalt state-role tagging

`nych.state_roles` runs *before* semantic encoding and before
domain/competency are used for anything: given a raw sentence, it tags
which word or phrase fills each role in a minimal state-representation
schema — `action`, `enumerator`, `object`, `tense` (a relational-time
marker like "after"/"before", distinct from the verb's own grammatical
tense), and `state` (the value the tense marker relates to):

```bash
nych parse "Re-ran both test suites after changes"
```

```json
{
  "action": {"word": "Re-ran", "position": 0, "lemma": "run"},
  "enumerator": {"word": "both", "position": 1},
  "object": {"word": "test suites", "start": 2, "end": 4},
  "tense": {"word": "after", "position": 4},
  "state": {"word": "changes", "start": 5, "end": 6}
}
```

This feeds the TOTE-loop database lookup below (domain + subdomain +
object/action → a known function or loop against
[T.O.T.E-loops](https://github.com/nhartman000/T.O.T.E-loops)), which
falls back to the raw schema above when nothing matches. Same honesty bar
as everywhere else
here: this is a small heuristic tagger over word lists (enumerators,
relational-tense markers, a small irregular-verb table plus an -ed suffix
rule), not a real dependency parser. A role that isn't found comes back as
`None`, not a guess — e.g. a sentence with no relational-tense marker gets
`"tense": null, "state": null` rather than an invented split.

## TOTE-loop database lookup

`nych.tote_lookup` connects the state-role tagger to the
[T.O.T.E-loops](https://github.com/nhartman000/T.O.T.E-loops) seed database:
given a `tag_roles()` record plus an optional domain and subdomain, it
queries a caller-supplied TOTE SQLite database (built in that repository
with `python -m src.build_db`, producing `data/tote_loops.sqlite3`) for a
matching known loop:

```bash
nych lookup "Re-ran both test suites after changes" \
  --db ../T.O.T.E-loops/data/tote_loops.sqlite3 --domain COMPUTER_SCIENCE
```

Matching is disclosed, deterministic word matching against three fields, in
order of specificity: the loop's joined gestalt `lexical_form`s, then its
`name`, then its `objective` (`match_method` in the result says which one
won). A small hand-built table bridges nych domain labels (e.g.
`COMPUTER_SCIENCE`) to TOTE domain values (e.g. `software-engineering`);
`--subdomain` constrains on the `loop_id` namespace prefix (`code`, `ai`).
The only normalization is a disclosed naive plural rule ("suites" can match
"suite").

Same honesty bar as the rest of the package: when nothing matches — or the
database path doesn't exist, or the roles contain no usable object/action
words — the result is an explicit fallback carrying the raw state-role
record (`{"matched": false, "fallback": "state_roles", "reason": ...}`),
never a forced best guess. No database is bundled with this package and no
sibling-repository path is probed; the path is always caller-supplied.

## Discretionary Gestalt mapping: the LLM boundary

The pipeline is `USER → natural-language input → NYCH encoder →
Gestalt mapping → MG8 engine`. Everything up to Gestalt mapping is
pre-LLM and deterministic: the state representation (`nych parse`), the
relational tense, the action, the domain/subdomain and vernacular
competency (`nych analyze`), and the TOTE-loop lookup (`nych lookup`) are
all extracted **before any word is Gestalt-mapped to any symbol**.

At Gestalt mapping, discretion is deferred to an LLM — there aren't enough
symbols to handle all of English. nych never makes that call itself; it
builds the handoff package the caller (e.g. mg8-engine's gate loop) gives
to the LLM, with these rules attached:

- map by most obvious visual match;
- embed the word **sans vowels and doubled consonants** into the symbol's
  id string as a disambiguation clue (`nych.skeleton`, `nych skeleton WORD`
  — doubling is judged on the original spelling, so "Re-ran" → `rrn` but
  "pattern" → `ptrn`);
- the four modality operators (👀 👁️🧠 🗯️ 💪) are **permanently
  invariant** in both directions: an operator is never remapped, and no
  other word may be given an operator's glyph (with or without the emoji
  variation selector) — enforced on `pin` and on loading a saved pin file;
- once the LLM maps a word in a session it is pinned `#temp-invariant`
  (`nych.session_invariants.SessionInvariants`) and reused, never
  re-decided — a conflicting repin raises unless explicitly forced, and a
  forced repin keeps the old value in the pin's history;
- compressible deterministic findings are chunked before symbols are
  rendered;
- **scientific names, names of people, and prescription drug names are
  NOT rendered into Gestalt** — they pass through literally, with no
  glyph, no skeleton id, and no session pin (`nych.protected_terms`, a
  disclosed heuristic over honorific/genus/drug lists and surface
  patterns, not NER; over-protection is the safe failure mode since a
  wrongly-literal word loses nothing while a wrongly-symbolized referent
  can be unrecoverable). Name pairs are caught mid-sentence and at
  sentence start ("Nicholas Hartman fixed it"); a lone capitalized word
  mid-sentence ("emailed Maurice") is protected under a separate
  `possible_name` category, because the same rule also catches months,
  places, and product names. The capitalized first word of a sentence is
  treated as a name when it has **no dictionary definition** ("Maurice
  called" → protected; "Fixed the build", "Re-ran …", "Emailed …" → not).
  The dictionary is a bundled 91,034-word list (ESDB/SCOWL size 60,
  lowercase entries only, so names that exist only capitalized never count
  as defined; provenance and license in
  [`nych/data/DICTIONARY_LICENSE.txt`](nych/data/DICTIONARY_LICENSE.txt)).
  Measured on the commit messages and READMEs of the NYCH repositories it
  flagged 1 coined word ("Multiword") out of 225 sentence openers. Known
  gap, inherent to the rule: a name that is also a dictionary word
  ("Mark", "Grace") reads as a word at sentence start.

The pin store's lifetime belongs to the caller (saved/loaded as plain
JSON); nych provides the store and the rules, not the memory policy.

## .gst pretext export for the LLM pruning step

The inverse-transform/dither pruning is also LLM-executed, not
deterministic code: the coarse **domain prune**, the **subdomain prune**,
and the **competency check** within domain — with a controlled
boundary-leakage margin ("dither") so access widens gradually from novice
to expert instead of cliff-edging. All the deterministic findings are
passed to that LLM as the pretext in a `.gst` file:

```bash
nych gst "re-ran both test suites after changes" \
  --db ../T.O.T.E-loops/data/tote_loops.sqlite3 --dither 0.1 --out out.gst
```

The payload shape is grounded against mg8-engine's actual `Gst` model
(plain JSON, extra keys allowed): `gst_version`, `state_id`, `domain`,
`state` (source text + roles), and a `nych_pretext` extra key carrying the
analysis, the TOTE match or its honest fallback, the invariant modality
operators, the words still needing a Gestalt mapping (each with its
consonant-skeleton clue), the protected terms, the session pins, the
discretion rules, and the pruning instructions with the dither value.
mg8-engine's `Gst` parser accepts the file unchanged, and its
`mg8_engine.pipeline` module consumes it for the first LLM call. nych
serializes the pretext; it does not execute the prune or call the LLM.

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

Run the test suite with:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Repository boundaries

NYCH is used by other research/runtime work in this GitHub account, including MG8-related experiments. Those integrations should not redefine NYCH's own package semantics. Conversely, this small package should not be presented as implementing every higher-level MG8/TCTA concept.

Related public repositories:

- TCTA: https://github.com/nhartman000/TCTA
- MG8: https://github.com/nhartman000/mg8
- MG8 reference runtime: https://github.com/nhartman000/mg8-engine

## Repository hygiene

Generated virtual environments, Python bytecode, build metadata, and visualization output are not source artifacts and are excluded by `.gitignore`.

A virtual environment had previously been committed to this repository. The current-tree cleanup removes it from active source control; historical Git objects may still contribute to repository size until a deliberate history-cleaning operation is performed.

## License

MIT — see [LICENSE](LICENSE). No restriction on commercial use; the intent is
wide adoption.
