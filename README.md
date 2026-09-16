# NYCH Symbolic Pipeline

**American Milestone Inc. | Nicholas Hartman | Current synthesis: August 2026**

A cohesive NYCH pipeline with explicit typed boundaries. This implementation accepts either language or sensor input, normalizes both into a shared NYCH packet/state model, constrains the action/state space, runs admissible reasoning/execution, validates the result, and emits canonical evidence.

## Architecture

The NYCH pipeline consists of 14 stages:

1. **INGEST**: Accept NaturalLanguageInput | SensorInput | ExistingSymbolicPacket
2. **IDENTITY / VERNACULAR**: Determine speaker/narrative perspective and vernacular context
3. **FEATURE NORMALIZATION**: Preserve numbers; convert sensor patterns to typed gestalts
4. **INVARIANT EXTRACTION**: Extract modality, person, tense, cognitive/control operators, domain markers
5. **SYMBOLIZATION**: Select deterministic semantic anchor; produce consonant skeleton
6. **CONTEXT BUILD**: Construct Domain + Subject + Intent + Competency + tools + state
7. **DOMAIN EXPANSION**: Domain -> Discipline -> Function -> Technique -> TOTE candidates
8. **INVERSE TRANSFORM / CONSTRAINT MASK**: Reject inadmissible candidates
9. **CANDIDATE SELECTION**: Deterministic or probabilistic within admissible boundary
10. **TOTE EXECUTION**: Test -> Operate -> Test -> Exit with bounded steps
11. **CONTINUITY VALIDATION**: Compare prior/current, internal/external, operators, domain, loop
12. **FAST/SLOW PATH**: Compressed representation vs expanded metadata
13. **EVIDENCE EMISSION**: Canonical QSON-compatible events
14. **PACKAGE/RETURN**: Expose result through MG8

## Installation

```bash
pip install -e .
```

## Usage

```python
from nych import run_pipeline, PipelineConfig, NaturalLanguageInput

# Configure pipeline
config = PipelineConfig(
    packet_version="1.0.0",
    use_probabilistic_selection=False,
    max_tote_iterations=10,
)

# Create input
input_data = NaturalLanguageInput(
    text="Build a test for the programming system",
    speaker="user",
    perspective="first",
    tense="present",
)

# Run pipeline
result = run_pipeline(input_data, config)

# Access results
print(f"Packet ID: {result.packet.packet_id}")
print(f"Domain: {result.context.domain}")
print(f"Valid: {result.validation.valid}")
print(f"Evidence events: {len(result.evidence)}")
```

## Project Structure

```
nych-symbolic-pipeline/
├── nych/
│   ├── __init__.py          # Package entry point
│   ├── types.py             # Typed interfaces
│   ├── exceptions.py        # Custom exceptions
│   ├── pipeline.py          # Pipeline orchestrator
│   ├── ingest.py            # Input adapters
│   ├── identity.py          # Identity/vernacular analysis
│   ├── normalization.py     # Feature normalization
│   ├── invariant.py         # Invariant extraction
│   ├── symbolization.py     # Symbolization
│   ├── context.py           # Context construction
│   ├── domain.py            # Domain expansion
│   ├── constraint.py        # Inverse transform / constraint masking
│   ├── selection.py         # Candidate selection
│   ├── tote.py              # TOTE execution
│   ├── validation.py        # Continuity validation
│   ├── fast_slow.py         # Fast/slow path decision
│   ├── evidence.py          # Evidence emission
│   └── schemas/
│       ├── __init__.py
│       ├── qson.py          # QSON schema validator
│       ├── gst.py           # GST schema validator
│       ├── g8son.py         # G8SON schema validator
│       └── mg8.py           # MG8 schema validator
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_pipeline.py     # End-to-end tests
│   ├── test_types.py        # Type tests
│   ├── test_schemas.py      # Schema tests
│   └── test_benchmark.py    # Benchmark tests
├── docs/
│   ├── NYCH_ARCHITECTURE.md
│   ├── NYCH_PIPELINE.md
│   ├── NYCH_LINEAGE.md
│   ├── NYCH_STATE_MODEL.md
│   └── NYCH_THEORY_BOUNDARIES.md
├── benchmarks/
│   ├── harness.py           # Benchmark harness
│   └── results_template.md  # Results template
├── migration/
│   └── DEPRECATION_PLAN.md  # Migration/deprecation plan
├── pyproject.toml
└── README.md
```

## Typed Data Contracts

| Type | Required Fields |
|------|----------------|
| NychPacket | packet_id, version, source_type, symbols, operators, numeric_values, metadata_refs |
| NychContext | domain, subject, intent, competency, modality, perspective, tense, tools, constraints |
| NychState | prior, current, internal_prior, internal_current, external_prior, external_current, continuity_reference |
| CandidateTransform | transform_id, input_state, output_state, technique, tote, admissibility_evidence, score |
| ValidationResult | valid, reasons, anomaly_flags, continuity_score, closure_state |
| AuditUnit | unit_id, source_refs, state_refs, transform_ref, metrics, hashes |

## Canonical Schemas

- **QSON**: Execution/evidence events, actors, sequence, validation results
- **GST**: Prior/current and internal/external state plus continuity semantics
- **G8SON**: Gates/constraints applied to candidate transforms
- **MG8**: References to orchestration, state, gates and evidence

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nych

# Run benchmarks
python -m benchmarks.harness
```

## Determinism Rules

- Version every symbol table, embedding/similarity model, operator lexicon and rule set
- Never claim independent-machine convergence unless identical model/version/tie-break rules are fixed
- Every nondeterministic model call must be outside the deterministic validation boundary
- Tie-breaking must be explicit and stable
- No hidden prompt-only state: material state belongs in typed state/context objects
- All loops are bounded; absence of an admissible continuation fails closed

## Theory Boundaries

- **Implemented**: Code covered by tests
- **Specification**: Architecture statements (not benchmark results)
- **Experimental**: Intelligence/awareness/consciousness constructs (labeled as research definitions)

## License

Proprietary - American Milestone Inc.
