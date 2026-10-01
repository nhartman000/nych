# NYCH Lineage

**American Milestone Inc. | Nicholas Hartman | Current synthesis: August 2026**

## 1. Inventory of NYCH-Related Repositories/Modules

This document classifies each NYCH-related repository or module according to its role in the overall architecture.

### Classification Categories

- **Canonical specification**: Defines the authoritative schema, protocol, or interface contract.
- **Active implementation**: Production-ready code that implements the specification.
- **Demonstration**: Example code or proof-of-concept that illustrates usage.
- **Compatibility layer**: Adapter code that bridges between NYCH and external systems.
- **Experiment**: Research code exploring new concepts not yet in the specification.
- **Archive**: Historical code preserved for reference but no longer maintained.
- **Placeholder**: Stub or skeleton code awaiting implementation.

### Current Repository Classification

| Repository/Module | Classification | Notes |
|-------------------|----------------|-------|
| `nych-symbolic-pipeline` (this repo) | Active implementation | Canonical implementation of the cohesive NYCH pipeline |
| `nych/types.py` | Canonical specification | Typed data contracts for NychPacket, NychContext, NychState, etc. |
| `nych/pipeline.py` | Active implementation | Pipeline orchestrator implementing all 14 stages |
| `nych/schemas/` | Canonical specification | Schema validators for QSON, GST, G8SON, MG8 |
| `nych/ingest.py` | Active implementation | Input adapters for natural language and sensor data |
| `nych/identity.py` | Active implementation | Identity/vernacular analysis |
| `nych/normalization.py` | Active implementation | Feature normalization |
| `nych/invariant.py` | Active implementation | Invariant extraction |
| `nych/symbolization.py` | Active implementation | Symbolization and consonant skeleton generation |
| `nych/context.py` | Active implementation | Context construction |
| `nych/domain.py` | Active implementation | Domain expansion |
| `nych/constraint.py` | Active implementation | Inverse transform / constraint masking |
| `nych/selection.py` | Active implementation | Candidate selection |
| `nych/tote.py` | Active implementation | TOTE execution |
| `nych/validation.py` | Active implementation | Continuity validation |
| `nych/fast_slow.py` | Active implementation | Fast/slow path decision |
| `nych/evidence.py` | Active implementation | Evidence emission |
| `tests/` | Active implementation | End-to-end conformance tests |
| `docs/` | Canonical specification | Architecture, pipeline, lineage, state model, theory boundaries |
| `benchmarks/` | Active implementation | Benchmark harness and results template |
| `migration/` | Archive | Migration/deprecation plans |

## 2. Duplication Analysis

### Identified Duplications

The following concepts were identified as potentially duplicated across modules and have been consolidated:

| Concept | Previous Duplication | Consolidated Location |
|---------|---------------------|----------------------|
| NychPacket definition | Multiple modules had partial packet definitions | `nych/types.py` |
| State model (prior/current) | Scattered across state handling code | `nych/types.py` (NychState) |
| Symbol table | Multiple symbol tables in different modules | `nych/symbolization.py` |
| Operator definitions | Cognitive and control operators defined separately | `nych/types.py` (enums) |
| Schema validation | Ad-hoc validation in multiple places | `nych/schemas/` |

### Semantic Equivalence Verification

Before consolidation, each duplicated concept was verified for semantic equivalence:

1. **NychPacket**: All previous definitions contained the same core fields (packet_id, version, source_type, symbols, operators, numeric_values, metadata_refs). Consolidated into a single frozen dataclass.
2. **NychState**: All previous state models distinguished prior/current and internal/external channels. Consolidated into a single frozen dataclass with explicit chronology advancement.
3. **Operator enums**: Cognitive and control operators were defined with the same values across modules. Consolidated into typed enums in `nych/types.py`.

## 3. Authority Boundaries

### Active Implementation Authority

The `nych-symbolic-pipeline` repository is the **single active NYCH implementation authority**. All other NYCH-related code should either:

1. Depend on this repository's typed interfaces, or
2. Be clearly marked as historical/experimental.

### Canonical Schema Authority

The canonical schemas for QSON, GST, G8SON, and MG8 are defined in `nych/schemas/`. No other repository should define competing schemas for these formats.

### Typed Interface Authority

All typed interfaces (NychPacket, NychContext, NychState, etc.) are defined in `nych/types.py`. These are the authoritative contracts that all modules must use.

## 4. Migration Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking changes to typed interfaces | Medium | High | Version interfaces; maintain backward compatibility |
| Schema validation failures at boundaries | Low | Medium | Add conformance tests at repository boundaries |
| Performance regression from consolidation | Low | Medium | Benchmark before and after changes |
| Loss of experimental code | Low | Low | Archive experimental code before removal |

## 5. Test Plan

1. **Unit tests**: All pipeline stages have unit tests.
2. **Integration tests**: End-to-end tests verify complete pipeline flow.
3. **Schema conformance tests**: QSON, GST, G8SON, MG8 validators tested against canonical schemas.
4. **Golden-vector tests**: Identical inputs produce identical outputs.
5. **Benchmark tests**: Latency, fidelity, and reconstruction equivalence measured.
6. **Property tests**: Selectors cannot inject non-admissible transforms.

## 6. Implementation Notes

- All probabilistic calls are contained inside deterministic constraints.
- The pipeline fails closed when no admissible continuation exists.
- State chronology advances explicitly; prior/current and internal/external channels advance independently.
- Evidence is emitted in canonical QSON format and validated against the schema.
- MG8 packages references without redefining normative schemas.
