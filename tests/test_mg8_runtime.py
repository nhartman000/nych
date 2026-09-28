"""Real tests of the gate-evaluation runtime -- invariants 3, 4, 5, 6, 8."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nych_mg8 import formats, runtime

FAILURES = []


def check(cond, label):
    print(f"  {'OK ' if cond else 'FAIL'} {label}")
    if not cond:
        FAILURES.append(label)


def test_and_gate_pass():
    state = formats.build_gst("S1", external_current={"object_detected": True, "confidence": 0.95})
    cond1 = formats.build_condition("external.current.object_detected", "==", True)
    cond2 = formats.build_condition("external.current.confidence", ">=", 0.9)
    gate = formats.build_gate("gate_001", 1, "AND", [cond1, cond2])
    result = runtime.evaluate_gate(state, gate)
    check(result == "PASS", f"AND gate with both conditions true -> PASS (got {result})")


def test_and_gate_fail():
    state = formats.build_gst("S1", external_current={"object_detected": True, "confidence": 0.5})
    cond1 = formats.build_condition("external.current.object_detected", "==", True)
    cond2 = formats.build_condition("external.current.confidence", ">=", 0.9)
    gate = formats.build_gate("gate_001", 1, "AND", [cond1, cond2])
    result = runtime.evaluate_gate(state, gate)
    check(result == "FAIL", f"AND gate with one condition false -> FAIL (got {result})")


def test_missing_data_is_intermediate_not_pass():
    """Invariant 4: INTERMEDIATE never implicitly means PASS. Missing state
    data must never silently resolve to PASS."""
    state = formats.build_gst("S1", external_current={})  # confidence key absent
    cond = formats.build_condition("external.current.confidence", ">=", 0.9)
    gate = formats.build_gate("gate_001", 1, "AND", [cond])
    result = runtime.evaluate_gate(state, gate)
    check(result == "INTERMEDIATE", f"missing state data -> INTERMEDIATE, never PASS (got {result})")
    check(result != "PASS", "confirmed: missing data did NOT default to PASS")


def test_or_gate():
    state = formats.build_gst("S1", external_current={"a": False, "b": True})
    cond_a = formats.build_condition("external.current.a", "==", True)
    cond_b = formats.build_condition("external.current.b", "==", True)
    gate = formats.build_gate("gate_001", 1, "OR", [cond_a, cond_b])
    result = runtime.evaluate_gate(state, gate)
    check(result == "PASS", f"OR gate with one true condition -> PASS (got {result})")


def test_runtime_authoritative_not_self_claimed():
    """Invariant 5: an externally-claimed result must NOT influence the
    outcome. Simulate an 'LLM' trying to claim PASS by passing a gate object
    with a misleading outcomes dict -- the actual PASS/FAIL decision must
    still come only from evaluate_gate's own condition evaluation."""
    state = formats.build_gst("S1", external_current={"confidence": 0.1})
    cond = formats.build_condition("external.current.confidence", ">=", 0.9)
    # An attacker-controlled gate might set outcomes to say anything, but
    # outcomes only map RESULT -> action string, they cannot set the result
    # itself -- the result always comes from evaluate_gate.
    gate = formats.build_gate("gate_001", 1, "AND", [cond],
                               on_pass="approved_by_claim", on_fail="stop")
    result = runtime.evaluate_gate(state, gate)
    check(result == "FAIL", f"low confidence still FAILs regardless of outcome labels (got {result})")


def test_state_commits_only_on_pass():
    """Invariant 6: proposed state committed only after runtime validation."""
    rt = runtime.GateRuntime(run_id="RUN_TEST")
    state = formats.build_gst("S1", external_current={"confidence": 0.1})
    cond = formats.build_condition("external.current.confidence", ">=", 0.9)
    gate = formats.build_gate("gate_001", 1, "AND", [cond])

    proposed_fail = formats.build_gst("S2_FAIL", external_current={"confidence": 0.1})
    result, committed = rt.attempt_gate(
        file_id="example.gates.001", gate=gate, state=state,
        input_state_id="S1", proposed_next_state=proposed_fail, proposed_next_state_id="S2_FAIL",
    )
    check(result == "FAIL", "gate correctly FAILs on low confidence")
    check(committed is None, "invariant 6: proposed state NOT committed on FAIL")

    state_ok = formats.build_gst("S1", external_current={"confidence": 0.99})
    proposed = formats.build_gst("S2", external_current={"confidence": 0.99})
    result2, committed2 = rt.attempt_gate(
        file_id="example.gates.001", gate=gate, state=state_ok,
        input_state_id="S1", proposed_next_state=proposed, proposed_next_state_id="S2",
    )
    check(result2 == "PASS", "gate correctly PASSes on high confidence")
    check(committed2 is not None and committed2["state_id"] == "S2",
          "invariant 6: proposed state committed only on PASS")


def test_qson_events_have_unique_trace_ids():
    rt = runtime.GateRuntime(run_id="RUN_TEST")
    state = formats.build_gst("S1", external_current={"confidence": 0.99})
    cond = formats.build_condition("external.current.confidence", ">=", 0.9)
    gate = formats.build_gate("gate_001", 1, "AND", [cond])
    for _ in range(3):
        rt.attempt_gate("f1", gate, state, "S1", None, None)
    doc = rt.to_qson()
    formats.validate_qson(doc)  # will raise on duplicate trace_id
    trace_ids = [e["trace_id"] for e in doc["events"]]
    check(len(trace_ids) == len(set(trace_ids)), "invariant 2: every gate attempt got a fresh trace_id")
    check(len(doc["events"]) == 3, "three attempts produced three events")


if __name__ == "__main__":
    test_and_gate_pass()
    test_and_gate_fail()
    test_missing_data_is_intermediate_not_pass()
    test_or_gate()
    test_runtime_authoritative_not_self_claimed()
    test_state_commits_only_on_pass()
    test_qson_events_have_unique_trace_ids()

    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("\nAll runtime tests passed.")
