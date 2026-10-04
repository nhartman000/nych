# NYCH Gestalt Algebra v1

**Author:** Nicholas Hartman / American Milestone Inc.
**Framework:** NYCH Gestalt Algebra (symbolic construction and compression)

## 1. Scope

NYCH Gestalt Algebra governs how a resolved sense becomes a symbolic unit, and how symbolic units combine. It does not govern whether a transformation between state representations is *admissible* — that is TCTA's question (`transform_algebra_axioms_v1.md`), over the state representation `SR = (s, D, C)` that TCTA already defines. It does not govern how a resulting structure is *executed or audited* — that is MG8's question (`.g8son`/`.ork`/`.qson`, per `mg8/docs/FILE_FAMILY.md`). This document's scope is narrower than either: given a word in context, how is it deterministically resolved and symbolically encoded, and under what conditions may two or more encoded units be composed into one.

Following TCTA's own formal-status discipline (`transform_algebra_axioms_v1.md` §15), this document marks every object, operator, and law as one of:

- **implemented** — backed by a named module in the `nych` package, cited by path;
- **not yet implemented** — named and typed here because the architecture requires it, but no code exists;
- **hypothesis** — a claim this document does not assert as proven.

Presenting any of the second or third category as the first would violate the separation of claims `NYCH_Current_Architecture_Specification.txt` §9 already requires project-wide. This document does not relax that for its own content.

## 2. Objects

| Object | Status | Definition |
|---|---|---|
| Lexical token | implemented | A surface word-position pair extracted by whitespace tokenization (`nych.semantic_encoding.encode_text`). |
| Resolved sense | implemented | An entry from the sense registry (`nych.semantic_registry`), carrying `sense_id`, `gestalt`, `surface_forms`, and (for multiword entries) `canonical_expression` and `protected_invariants`. |
| Semantic ID | implemented | The tuple `(sense_id, gestalt, resolution_method, confidence)` `encode_text` records per token — not merely the glyph, but the glyph plus its provenance. |
| Gestalt symbol | implemented | The glyph a resolved sense maps to (`entry["gestalt"]`). |
| Consonant skeleton | implemented | The vowel/doubled-consonant-stripped disambiguation clue embedded in a Gestalt-mapping id (`nych.skeleton`), required by `mg8-engine`'s `validate_mapping_plan` to be present in every accepted mapping's `symbol_id`. |
| Multiword Gestalt (span) | implemented | A longest-first, non-overlapping phrase match against `registry["gestalt_spans"]` (`nych.semantic_encoding.match_gestalt_spans`); resolves to one `sense_id`/`gestalt` covering multiple tokens at once. |
| Relational Gestalt | not yet implemented | A higher-order unit representing a *relation* between two or more already-encoded units (e.g. a compressed `drive(hammer, nail, wood)`), rather than one token or phrase. No registry entry, encoder, or decoder for this exists. |
| State representation | implemented (by reference) | TCTA's `SR = (s, D, C)` (`transform_algebra_axioms_v1.md` §2); NYCH does not redefine it, it supplies the symbolic content that can populate `s`. |
| Protected literal | implemented | A word NYCH `protected_terms.py` classifies as a scientific name, a person's name, or a prescription drug name; never Gestalt-mapped, passed through unchanged. |
| Provenance class | implemented | The resolution method a semantic ID records: `explicit` \| `gestalt_span` \| `surface_form_unambiguous` \| `cue_match` \| `default_fallback` \| `unsymbolized` (`encode_text`'s `method` field). `audit_summary` reports the fraction of a text resolved by the two guessing methods (`cue_match`, `default_fallback`) as `fraction_guessed`. |
| Epistemic status | implemented (by reference) | `OBS \| MODEL \| INTENT \| ACT` (`nych/epistemic.py`'s `EpistemicStatus`) — word-only, deliberately disjoint from the perceptual-channel modality operators below. |

## 3. Operators

| Operator | Status | Definition |
|---|---|---|
| Sense resolution, \(\rho(w, c)\) | implemented | `encode_text`'s per-token resolution: explicit caller-supplied sense, else longest registered Gestalt span, else unambiguous surface form, else contextual cue match, else honest unresolved/default fallback (`nych/README.md`'s documented resolution order, §"Sense registry and Gestalt spans"). |
| Symbol assignment, \(E(s)\) | implemented | Encodes a resolved sense as `(sense_id, gestalt, skeleton, provenance)`. For words the deterministic registry does not cover (`needs_mapping`), `E` is deferred to the discretionary LLM step under the rules in §4, not performed by `nych` itself. |
| Sequential composition | implemented | `encode_text`'s left-to-right token substitution into the output string — positional concatenation, not a typed combinator. |
| Relational composition, \(\otimes_R\) | not yet implemented | No code composes two encoded units under a named relation `R` into a new typed unit. §5's relational-compatibility law is written against this operator precisely because it does not exist yet — the law is the specification the operator must satisfy once built, not a description of present behavior. |
| Gestalt compression, \(C_R\) | not yet implemented | No code promotes a recurring relational structure to its own higher-order Gestalt. This is the "relational compression" `nych/README.md` and the project's broader theory both name as a goal; no registry mechanism for it exists. |
| Decompression, \(D\) | partial | `encode_text` only substitutes glyphs into the original token positions; there is no separate reconstruction pass, and nothing decompresses a `C_R` unit (since none exist) back to a relational expression. |
| Invariant projection | implemented (by reference) | The four modality operators (👀/👁️🧠/🗯️/💪) are permanently invariant in both directions (`nych/README.md` §"Discretionary Gestalt mapping"); enforced in code by `mg8_engine.pipeline.validate_mapping_plan` and by `nych.session_invariants`' `#temp-invariant` pin store. |
| Context restriction | implemented | The LLM-executed domain prune, subdomain prune, and competency check with a controlled dither margin, carried as the `pruning` instructions in a `.gst` pretext (`nych/README.md` §".gst pretext export"). |
| Modality application | implemented (by reference) | `nych.types.Modality`'s perceptual-channel operators (VE/VI/AE/AI/KE/KI/SME/TAS/MEN/IMG/REM), mapped to their own emoji set in `nych.invariant` — orthogonal to epistemic status (`nych/epistemic.py` module docstring explains why the two axes don't share symbols). |
| TOTE-loop association | implemented | `nych.tote_lookup` matches a tagged state-role record against the T.O.T.E-loops seed database, falling back honestly to the raw record when nothing matches. |

## 4. Protected-domain and invariant constraints on composition

`E(x) \otimes_R E(y)` (once `\otimes_R` exists) is defined only when, per the rules `nych/README.md` already states for the discretionary mapping step and the anti-promotion invariants `nych/epistemic.py` already states for epistemic status:

- neither `x` nor `y` is a protected literal (§5, Protected-term identity) — a protected term never participates in symbolic composition, it stays literal;
- the four modality operators are not reassigned by the composition — invariant projection is never overridden by a relational step;
- a word already pinned `#temp-invariant` in the active session keeps its existing mapping rather than being re-resolved as part of the composition;
- no epistemic-status promotion occurs across the composition — composing an `ACT`-status unit with a `MODEL`-status unit must not yield a unit presented as `OBS` (§5, Non-promotion, below).

This section states constraints a future `\otimes_R` must satisfy; it is not itself an operator definition, since `\otimes_R` is not yet implemented (§3).

## 5. Laws

### Determinism — implemented

Given the same registry, context, and input, resolution is identical:

\[
\rho_{R,C}(w) = \rho_{R,C}(w)
\]

`encode_text` has no sampling step in the deterministic path; the only non-determinism in the pipeline is the discretionary LLM mapping for words `needs_mapping` lists, which is why `mg8_engine.pipeline.validate_mapping_plan` exists — the engine validates that call's output rather than trusting it.

### Protected-term identity — implemented

For protected literal \(p\):

\[
E(p) = p
\]

Enforced by `nych.protected_terms` at classification time and by `mg8_engine.pipeline.validate_mapping_plan` at acceptance time (`REJECT IF` a protected term was Gestalt-mapped).

### Non-promotion — implemented (by reference)

NYCH's epistemic operators obey exactly the four invariants `nych/epistemic.py`'s `ANTI_PROMOTION_INVARIANTS` already names canonically:

\[
\text{ACT} \not\Rightarrow \text{OBS\_POSTCONDITION}, \quad
\text{ACT} \not\Rightarrow \text{INTENT}, \quad
\text{MODEL} \not\Rightarrow \text{OBS}, \quad
\text{END} \not\Rightarrow \text{EXIT}
\]

This document does not restate these as new laws; it cites them as already-canonical constraints that also bind any future composition operator (§4).

### Invariant preservation — hypothesis

\[
I(D(E(x))) = I(x)
\]

Encoding and decoding should preserve entities, modality, negation, quantities, temporal relationships, and protected meanings. No test suite currently checks this property; `D` itself is only partial (§3), so the law cannot yet be evaluated beyond the single-token case, where it reduces trivially to the resolved sense's `surface_forms` round-tripping.

### Reconstruction — hypothesis, partially vacuous

\[
D(E(x)) \equiv_I x
\]

where \(\equiv_I\) is equivalence under the declared invariants above, not character identity. \(\equiv_I\) itself is not formally defined by this document (§6) — stating the law before its equivalence relation is defined is intentional: it records the requirement a future `\equiv_I` must satisfy, not a result.

### Relational compatibility — not yet defined (the critical gap)

\[
E(x \mathbin{R} y) \equiv E(x) \otimes_R E(y)
\]

This is the law a working `\otimes_R` must satisfy for relational composition to be sound: encoding a relation directly must agree with encoding its operands and then composing them. Since neither `\otimes_R` nor `\equiv` across composed units is implemented, this law is not evaluable today. It is recorded here because it is the specific property future work on `\otimes_R` (§3) must be checked against, not a description of current behavior.

### Stable compression — not yet defined

\[
D(C_R(x \otimes_R y)) \equiv_I D(x \otimes_R y)
\]

A higher-order Gestalt produced by `C_R` (§3, not yet implemented) must decompress to something invariant-equivalent to decompressing its uncompressed form. Not evaluable until `C_R`, `\otimes_R`, and `\equiv_I` all exist.

## 6. Classification

NYCH Gestalt Algebra is not a group, ring, or field. The current implemented subset (§2–3) supports characterizing it as the beginning of:

- a **many-sorted algebra** — tokens, senses, semantic IDs, and Gestalt symbols are distinct sorts, not one undifferentiated type;
- a **partial algebra** — `\otimes_R` (once built) is defined only under the constraints in §4, not for every pair of operands;
- a **deterministic semantic encoding calculus** — the implemented subset (§2–3, resolution through composition and context restriction).

It is not yet, and this document does not claim it to be, a **typed term-rewriting system**, a **semantic composition calculus** in the full relational sense, or a **relational compression algebra** — each of those requires `\otimes_R` and/or `C_R`, which §3 records as not yet implemented.

## 7. Missing to reach a complete algebra

Per §2–6, the specific gaps between the current implementation and a complete NYCH Gestalt Algebra are:

- `\otimes_R` itself: a typed relational composition operator, with a declared table of legal relations (candidates: actor/action/object, before/after/during, internal/external, prior/current, intention/action/observation, cause/effect, part/whole, domain/subdomain, test/operate/test/exit — the last already present as data via `nych.tote_lookup`, not yet as an algebraic relation type);
- `C_R` and its inverse: higher-order Gestalt creation and canonical decompression;
- \(\equiv_I\): the invariant-equivalence relation the Reconstruction and Stable-compression laws are stated against;
- a reduction order and collision-resolution rule for when composition or compression is ambiguous;
- closure conditions: what makes a composed/compressed expression well-formed enough to participate as an operand in a still-larger expression;
- a proof obligation (or, short of proof, a tested hypothesis in the same register as TCTA's H1/H2) that compression preserves the invariants §5 declares, rather than assuming it.

The discretionary LLM Gestalt-mapping step (§3, Symbol assignment) is not itself algebraic — nothing about an LLM's proposed mapping is deterministic or composable. It becomes usable by this algebra only after `mg8_engine.pipeline.validate_mapping_plan` accepts it and `nych.session_invariants` pins it `#temp-invariant`; before that, it is a proposal, not an object this algebra operates on.

## 8. Relationship to TCTA and MG8

Per `mg8/docs/FILE_FAMILY.md`'s package-to-trace relationship and `transform_algebra_axioms_v1.md`'s own scope statement, the three specifications divide the pipeline this way, none redefining the others' normative content:

- **NYCH Gestalt Algebra** (this document) governs how a resolved sense becomes a symbolic unit and how symbolic units may compose — populating the \(s\) component of TCTA's `SR = (s, D, C)`.
- **TCTA** (`transform_algebra_axioms_v1.md`) governs whether a transform between state representations is admissible, independent of how those representations were symbolically constructed.
- **MG8** (`.g8son`/`.ork`/`.qson`, `mg8/docs/FILE_FAMILY.md`) governs how the resulting gated structures are executed and audited, independent of both the symbolic construction and the admissibility question.

## 9. Formal status

Per the discipline stated in §1 and used throughout §2–5:

- **implemented, code-backed**: sense resolution, symbol assignment (deterministic path only), sequential composition, consonant skeletons, multiword Gestalt spans, protected-literal identity, invariant modality operators, context restriction with dither, TOTE-loop association, the four non-promotion invariants (by reference to `nych/epistemic.py`).
- **partial**: decompression (single-token substitution only, no relational case).
- **not yet implemented**: relational composition (\(\otimes_R\)), Gestalt compression (\(C_R\)) and its inverse, relational Gestalts as an object.
- **hypothesis, not evaluable until the above exist**: invariant preservation, reconstruction, relational compatibility, stable compression.

No claim in this document should be read as asserting that NYCH is currently a complete, proven algebra. §6–7 state precisely what would need to be built and shown for that claim to become available.
