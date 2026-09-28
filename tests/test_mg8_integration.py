import json
import tempfile
import unittest
from pathlib import Path

from nych_mg8 import formats, runtime


class CanonicalCompatibilityTests(unittest.TestCase):
    def test_canonical_custom_gate_type_is_interchange_valid(self):
        document = {
            "g8son_version": "1.0", "file_id": "f",
            "gates": [{"gate_id": "g", "type": "HUMAN_REVIEW", "conditions": ["reviewed"]}],
        }
        formats.validate_g8son(document)
        with self.assertRaises(formats.SchemaError):
            formats.validate_reference_g8son(document)

    def test_non_gate_qson_event_does_not_require_result(self):
        event = formats.build_qson_event(
            "T1", "R1", 1, "review", actor_id="reviewer",
            timestamp="2026-09-28T00:00:00Z",
        )
        formats.validate_qson(formats.build_qson("R1", [event]))

    def test_qson_rejects_run_and_sequence_conflicts(self):
        first = formats.build_qson_event("T1", "R1", 1, "review", timestamp="2026-09-28T00:00:00Z")
        second = formats.build_qson_event("T2", "WRONG", 1, "review", timestamp="2026-09-28T00:00:01Z")
        with self.assertRaises(formats.SchemaError):
            formats.validate_reference_qson(formats.build_qson("R1", [first, second]))

    def test_windows_traversal_is_rejected(self):
        with self.assertRaises(formats.SchemaError):
            formats.validate_resource_reference(r"..\outside.gst", ".gst")


class EndToEndExecutionTests(unittest.TestCase):
    def make_unit(self, root: Path):
        (root / "state").mkdir()
        (root / "gates").mkdir()
        state = formats.build_gst("S1", external_current={"confidence": 0.95})
        gate = formats.build_gate("g1", 1, "AND", [formats.build_condition("external.current.confidence", ">=", 0.9)])
        formats.save_json(root / "state/main.gst", state)
        formats.save_json(root / "gates/main.g8son", formats.build_g8son("f1", [gate]))
        formats.save_json(root / "flow.ork", formats.build_flow_ork(["g1"]))
        formats.save_json(root / "unit.mg8", formats.build_mg8_manifest("u1", "flow.ork", ["state/main.gst"], ["gates/main.g8son"], "trace/run.qson"))
        return root / "unit.mg8"

    def test_manifest_is_actually_loaded_and_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = self.make_unit(Path(directory))
            unit, engine, final_state = runtime.execute_unit(manifest, run_id="R1")
            self.assertEqual(engine.events[0]["result"], "PASS")
            self.assertEqual(final_state["state_id"], "S1")
            ledger = formats.load_json(unit.trace_path)
            formats.validate_reference_qson(ledger)

    def test_external_pass_claim_is_ignored(self):
        state = formats.build_gst("S1", external_current={"confidence": 0.1})
        state["gate_result"] = "PASS"
        gate = formats.build_gate("g1", 1, "AND", [formats.build_condition("external.current.confidence", ">=", 0.9)])
        self.assertEqual(runtime.evaluate_gate(state, gate), "FAIL")

    def test_qson_flush_does_not_duplicate_events(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.qson"
            engine = runtime.GateRuntime("R1")
            state = formats.build_gst("S1", external_current={"confidence": 1.0})
            gate = formats.build_gate("g1", 1, "AND", [formats.build_condition("external.current.confidence", ">=", 0.9)])
            engine.attempt_gate("f1", gate, state, "S1")
            engine.append_to_qson_file(path)
            engine.append_to_qson_file(path)
            self.assertEqual(len(formats.load_json(path)["events"]), 1)


if __name__ == "__main__":
    unittest.main()
