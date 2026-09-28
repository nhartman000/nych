"""Real tests against the canonical MG8 schemas -- run with:
    python3 tests/test_formats.py
Exits nonzero on any failure, same discipline as this project's other
adversarial test harnesses (no silent pass)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nych_mg8 import formats

FAILURES = []


def check(cond, label):
    print(f"  {'OK ' if cond else 'FAIL'} {label}")
    if not cond:
        FAILURES.append(label)


def test_gst_roundtrip():
    d = formats.build_gst(
        state_id="STATE_001",
        external_current={"object_detected": True, "confidence": 0.95},
    )
    formats.validate_gst(d)  # must not raise
    check(d["gst_version"] == "1.0", "gst_version is 1.0")
    check(d["external"]["current"]["object_detected"] is True, "external.current round-trips")


def test_g8son_gate_count_enforced():
    cond = formats.build_condition("external.current.object_detected", "==", True)
    gate = formats.build_gate("gate_001", 1, "AND", [cond])
    g = formats.build_g8son("example.gates.001", [gate])
    formats.validate_g8son(g)  # must not raise
    check(True, ".g8son with 1 gate validates")

    try:
        formats.build_g8son("bad.gates.001", [gate, gate, gate, gate])
        check(False, ".g8son with 4 gates should be rejected (max is 3)")
    except formats.SchemaError:
        check(True, ".g8son with 4 gates correctly rejected")


def test_g8son_invariant1_file_id_ne_gate_id():
    cond = formats.build_condition("x", "==", 1)
    gate = formats.build_gate("same_id", 1, "AND", [cond])
    try:
        formats.build_g8son("same_id", [gate])
        check(False, "invariant 1 (file_id != gate_id) should have been enforced")
    except formats.SchemaError:
        check(True, "invariant 1 (file_id != gate_id) correctly enforced")


def test_qson_rejects_jsonl_shape():
    bad = {"qson_version": "1.0", "run_id": "R1", "events": "not-a-list"}
    try:
        formats.validate_qson(bad)
        check(False, "invariant 11 (events must be an array) should have been enforced")
    except formats.SchemaError:
        check(True, "invariant 11 (events must be an array, not JSONL) correctly enforced")


def test_qson_trace_id_uniqueness():
    e1 = formats.build_qson_event(
        trace_id="T1", run_id="R1", sequence=1, event_type="gate_attempt",
        file_id="f1", gate_id="g1", input_state_id="S1", result="PASS",
        action="continue", output_state_id="S2", actor_type="runtime",
        actor_id="engine", timestamp="2026-01-01T00:00:00Z",
    )
    e2 = dict(e1)  # duplicate trace_id -- invariant 2 violation
    doc = formats.build_qson("R1", [e1, e2])
    try:
        formats.validate_qson(doc)
        check(False, "invariant 2 (fresh trace_id per attempt) should have been enforced")
    except formats.SchemaError:
        check(True, "invariant 2 (duplicate trace_id) correctly rejected")


def test_mg8_manifest_relative_paths():
    m = formats.build_mg8_manifest(
        unit_id="example.unit.001", entry="flow.ork",
        state=["state/main.gst"], gates=["gates/main.g8son"], trace="trace/run.qson",
    )
    formats.validate_mg8_manifest(m)
    check(True, ".mg8 manifest with relative paths validates")

    bad = formats.build_mg8_manifest(
        unit_id="u", entry="flow.ork", state=["/etc/passwd"], gates=[], trace="t.qson",
    )
    try:
        formats.validate_mg8_manifest(bad)
        check(False, "invariant 9 (relative paths only) should have been enforced")
    except formats.SchemaError:
        check(True, "invariant 9 (absolute path escape) correctly rejected")


def test_flow_ork():
    d = formats.build_flow_ork(["gate_001", "gate_002"])
    formats.validate_flow_ork(d)
    check(d["ork_version"] == "0.1-reference", "flow.ork uses canonical reference version")


if __name__ == "__main__":
    test_gst_roundtrip()
    test_g8son_gate_count_enforced()
    test_g8son_invariant1_file_id_ne_gate_id()
    test_qson_rejects_jsonl_shape()
    test_qson_trace_id_uniqueness()
    test_mg8_manifest_relative_paths()
    test_flow_ork()

    if FAILURES:
        print(f"\n{len(FAILURES)} FAILURE(S):")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("\nAll format tests passed.")
