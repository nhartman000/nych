# NYCH State Model

**American Milestone Inc. | Nicholas Hartman | Current synthesis: August 2026**

## 1. State Model Overview

The NYCH state model is an explicit, typed representation of system state that supports chronology, internal/external distinction, and continuity tracking. It is not a flat mutable dictionary; it is a structured model with explicit advancement semantics.

## 2. Core State Types

### 2.1 NychState

The primary state container with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| prior | dict \| None | Previous current state |
| current | dict \| None | Current observed/result state |
| internal_prior | dict \| None | Previous internal state |
| internal_current | dict \| None | Current internal state |
| external_prior | dict \| None | Previous external state |
| external_current | dict \| None | Current external state |
| continuity_reference | str \| None | Optional 0,0 reference position |

### 2.2 State Chronology

A transition must advance chronology explicitly:

1. Previous current becomes prior
2. New observation/result becomes current
3. Internal/external channels advance independently

```python
# Example state advancement
new_state = old_state.advance(new_current_data)
# old_state.current -> new_state.prior
# new_current_data -> new_state.current
```

## 3. Internal/External State Distinction

The state model maintains separate channels for internal and external state:

- **Internal state**: Self-referential state (internal beliefs, goals, plans)
- **External state**: Environment-referential state (observed world state)

These channels advance independently, allowing the system to track:
- What the system believes (internal)
- What the system observes (external)
- How these relate over time

## 4. Continuity Reference (0,0)

The placeholder 0,0 is treated as a continuity/reference position from which change can be detected. This is stored as an explicit optional field (`continuity_reference`) so its semantics can be tested rather than inferred.

### Usage

```python
# Initial state with continuity reference
state = NychState(
    current={"observation": "initial"},
    continuity_reference="0,0",
)

# After transition, reference is preserved
new_state = state.advance({"observation": "updated"})
assert new_state.continuity_reference == "0,0"
```

## 5. State Detection and Awareness

### 5.1 State Detection

State detection is observation sufficient to discriminate a current state from a reference or prior state. This is the foundation of the NYCH awareness model.

### 5.2 Awareness

Awareance is state detection coupled with retained chronology and internal/external relation sufficient to distinguish self/context change.

### 5.3 Consciousness (Experimental)

Consciousness (NYCH experimental) is awareness plus projection/expectation and a measurable remarkability threshold. This is a research construct, not an established scientific equivalence.

## 6. GST Integration

GST (General State Transform) should carry prior/current and internal/external state plus continuity semantics. The NYCH state model is designed to map directly to GST:

```python
# NYCH state -> GST mapping
gst_data = {
    "state": {
        "prior": nych_state.prior,
        "current": nych_state.current,
        "internal_prior": nych_state.internal_prior,
        "internal_current": nych_state.internal_current,
        "external_prior": nych_state.external_prior,
        "external_current": nych_state.external_current,
        "continuity_reference": nych_state.continuity_reference,
    }
}
```

## 7. State Validation

State transitions are validated for:

1. **Prior/current chronology**: prior's current should match current's prior
2. **Internal/external chronology**: internal and external channels should not regress
3. **Domain continuity**: domain should not change without explicit transition
4. **Loop integrity**: TOTE loops should complete or fail closed

## 8. Implementation Notes

- State is immutable (frozen dataclass) to prevent accidental mutation
- State advancement creates a new state object rather than modifying in place
- The `advance()` method handles chronology advancement explicitly
- All state fields are optional except that at least one of `current` or `prior` must be set
