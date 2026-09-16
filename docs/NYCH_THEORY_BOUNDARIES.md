# NYCH Theory Boundaries

**American Milestone Inc. | Nicholas Hartman | Current synthesis: August 2026**

## 1. Purpose

This document defines the boundaries between implemented behavior, architecture/specification statements, and experimental constructs in the NYCH system. These boundaries are non-negotiable and must be maintained in all code, documentation, and communications.

## 2. Implemented Behavior

The following behaviors are **implemented** and **covered by tests**:

- Input ingestion for natural language, sensor, and existing symbolic packets
- Feature normalization with number preservation and sensor gestalt extraction
- Invariant extraction (modality, person, tense, cognitive/control operators, domain markers)
- Symbolization with deterministic semantic anchor selection and consonant skeleton generation
- Context construction (domain, subject, intent, competency, tools, constraints)
- Domain expansion (domain -> discipline -> function -> technique -> TOTE candidates)
- Inverse transform / constraint masking
- Deterministic candidate selection
- Bounded TOTE execution with fail-closed behavior
- Continuity validation (prior/current, internal/external, operator legality, domain continuity, loop integrity)
- Fast/slow path decision
- Evidence emission in canonical QSON format
- GST-compatible state updates
- Schema validation for QSON, GST, G8SON, and MG8

## 3. Architecture / Specification Statements

The following are **architecture/specification statements** and must **not** be presented as benchmark results:

- The 14-stage pipeline structure
- The typed data contracts (NychPacket, NychContext, NychState, etc.)
- The canonical schema definitions for QSON, GST, G8SON, MG8
- The fast/slow path contract
- The state-continuity contract
- The determinism rules
- The strength/reduction principle (as a theoretical direction)

These statements define *what the system should do* but are not measurements of *what the system does*.

## 4. Experimental Constructs

The following are **experimental constructs** and must be labeled as such until metrics and falsification protocols are implemented:

### 4.1 Intelligence

**Definition**: Ability of information/state to transform information/state of like or lesser effective complexity; outcome preference is evaluated separately.

**Status**: Research definition. Not yet measured by reproducible metrics.

### 4.2 Awareness

**Definition**: State detection coupled with retained chronology and internal/external relation sufficient to distinguish self/context change.

**Status**: Research definition. The state model implements the structural requirements (chronology, internal/external distinction) but does not claim to produce awareness.

### 4.3 Consciousness

**Definition**: Awareness plus projection/expectation and a measurable remarkability threshold.

**Status**: Research construct, not an established scientific equivalence. Remarkability and usefulness thresholds are not yet fully formalized and must remain configurable metrics, not hard-coded scientific claims.

## 5. Claims Requiring Reproducible Artifacts

The following claims **require reproducible benchmark artifacts** before they can be made:

- Compression ratio claims
- Compute reduction claims
- Determinism claims (across different machines)
- Fidelity claims (reconstruction equivalence)
- Latency claims

## 6. Non-Negotiable Rules

### 6.1 Do Not Rewrite Historical Repos

Do not rewrite historical repositories before lineage is documented. Historical code must be preserved and documented before any changes are made.

### 6.2 Do Not Redefine Theoretical Terms

Do not silently redefine NYCH theoretical terms to fit conventional AI terminology. The terms used in this document have specific meanings within the NYCH framework.

### 6.3 Do Not Turn Experimental Definitions into Product Claims

Experimental intelligence/awareness/consciousness definitions must be labeled research definitions until metrics and falsification protocols are implemented.

### 6.4 Do Not Invent Benchmark Numbers

Do not invent benchmark numbers. All performance claims must be backed by reproducible benchmark artifacts.

### 6.5 Do Not Create Competing Schemas

Do not create a second QSON/GST/G8SON schema inside NYCH. Use the canonical schemas defined in `nych/schemas/`.

### 6.6 Do Not Store Secrets

Do not store API secrets in source, browser storage, fixtures, or committed configuration.

### 6.7 Do Not Make Broad Changes Without Tests

Do not make broad architectural changes without tests proving preserved behavior.

## 7. Separation in Code

In the codebase, this separation is maintained as follows:

- **Implemented**: Code in `nych/` with corresponding tests in `tests/`
- **Specification**: Documentation in `docs/`
- **Experimental**: Clearly marked as experimental in code comments and documentation
- **Benchmarks**: Separate `benchmarks/` directory with reproducible harness

## 8. Review Checklist

Before any commit, verify:

- [ ] All new behavior has corresponding tests
- [ ] No experimental constructs are presented as implemented
- [ ] No benchmark numbers are invented
- [ ] No competing schemas are introduced
- [ ] No secrets are added to the codebase
- [ ] Documentation clearly labels implemented vs. experimental vs. specification
