"""Deterministic MG8 reference-profile loader and executor."""
from __future__ import annotations

import copy
import operator
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from . import formats

_OPS = {"==": operator.eq, "!=": operator.ne, ">": operator.gt,
        ">=": operator.ge, "<": operator.lt, "<=": operator.le}


class RuntimeError_(Exception):
    pass


def _resolve_path(state, path):
    node = state
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


def evaluate_condition(state, condition):
    found, value = _resolve_path(state, condition["path"])
    if not found:
        return False, False
    try:
        return True, bool(_OPS[condition["operator"]](value, condition["value"]))
    except (KeyError, TypeError):
        return False, False


def evaluate_gate(state, gate):
    resolved = [evaluate_condition(state, condition) for condition in gate["conditions"]]
    if gate["type"] == "AND":
        if any(not known for known, _ in resolved):
            return "INTERMEDIATE"
        return "PASS" if all(value for _, value in resolved) else "FAIL"
    if gate["type"] == "OR":
        if any(known and value for known, value in resolved):
            return "PASS"
        return "FAIL" if all(known for known, _ in resolved) else "INTERMEDIATE"
    raise RuntimeError_(f"unsupported reference gate type: {gate['type']!r}")


def _safe_resolve(root: Path, reference: str, suffix: str) -> Path:
    formats.validate_resource_reference(reference, suffix)
    resolved = (root / reference).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError_(f"resource escapes MG8 unit: {reference!r}") from exc
    if not resolved.is_file():
        raise RuntimeError_(f"MG8 resource not found: {reference!r}")
    return resolved


def _merge_states(states):
    """Merge resources in manifest order; later mapping fields override earlier ones."""
    merged = copy.deepcopy(states[0])
    source_ids = [merged["state_id"]]
    for state in states[1:]:
        source_ids.append(state["state_id"])
        for key, value in state.items():
            if key in {"gst_version", "state_id"}:
                continue
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key].update(copy.deepcopy(value))
            else:
                merged[key] = copy.deepcopy(value)
    if len(source_ids) > 1:
        merged["source_state_ids"] = source_ids
        merged["state_id"] = "+".join(source_ids)
    return merged


@dataclass
class LoadedUnit:
    source: Path
    root: Path
    manifest: dict
    state: dict
    gates: dict[str, tuple[str, dict]]
    flow: list[str]
    trace_path: Path


def load_unit(manifest_path) -> LoadedUnit:
    source = Path(manifest_path).resolve()
    if source.suffix != formats.EXT_UNIT or not source.is_file():
        raise RuntimeError_("input must be an existing .mg8 manifest")
    root = source.parent
    manifest = formats.load_json(source)
    formats.validate_mg8_manifest(manifest)

    states = []
    for reference in manifest["state"]:
        document = formats.load_json(_safe_resolve(root, reference, formats.EXT_STATE))
        formats.validate_gst(document)
        states.append(document)
    state = _merge_states(states)

    gates = {}
    file_ids = set()
    for reference in manifest["gates"]:
        document = formats.load_json(_safe_resolve(root, reference, formats.EXT_GATES))
        formats.validate_reference_g8son(document)
        if document["file_id"] in file_ids:
            raise RuntimeError_(f"duplicate G8SON file_id: {document['file_id']}")
        file_ids.add(document["file_id"])
        for gate in document["gates"]:
            if gate["gate_id"] in gates:
                raise RuntimeError_(f"duplicate gate_id across unit: {gate['gate_id']}")
            gates[gate["gate_id"]] = (document["file_id"], gate)

    ork = formats.load_json(_safe_resolve(root, manifest["entry"], formats.EXT_ORCHESTRATION))
    formats.validate_flow_ork(ork)
    unknown = [gate_id for gate_id in ork["flow"] if gate_id not in gates]
    if unknown:
        raise RuntimeError_(f"ORK references unknown gates: {unknown}")

    formats.validate_resource_reference(manifest["trace"], formats.EXT_LEDGER)
    trace_path = (root / manifest["trace"]).resolve()
    try:
        trace_path.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError_("trace path escapes MG8 unit") from exc
    return LoadedUnit(source, root, manifest, state, gates, ork["flow"], trace_path)


class GateRuntime:
    def __init__(self, run_id, actor_id="mg8-engine"):
        self.run_id, self.actor_id = run_id, actor_id
        self._sequence = 0
        self._flushed = 0
        self.events = []

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def attempt_gate(self, file_id, gate, state, input_state_id,
                     proposed_next_state=None, proposed_next_state_id=None):
        candidate = copy.deepcopy(proposed_next_state if proposed_next_state is not None else state)
        result = evaluate_gate(candidate, gate)
        action = gate["outcomes"][result]
        self._sequence += 1
        committed = candidate if result == "PASS" else None
        output_state_id = (proposed_next_state_id or candidate.get("state_id") or input_state_id) if committed else None
        event = formats.build_qson_event(
            trace_id=f"TRJ_{uuid.uuid4().hex}", run_id=self.run_id,
            sequence=self._sequence, event_type="gate_attempt", file_id=file_id,
            gate_id=gate["gate_id"], input_state_id=input_state_id,
            result=result, action=action, output_state_id=output_state_id,
            actor_id=self.actor_id, timestamp=self._now(),
            evidence={"conditions_evaluated": len(gate["conditions"])},
        )
        self.events.append(event)
        return result, committed

    def to_qson(self):
        if not self.events:
            raise RuntimeError_("cannot serialize an empty QSON ledger")
        document = formats.build_qson(self.run_id, self.events)
        formats.validate_reference_qson(document)
        return document

    def append_to_qson_file(self, path):
        new_events = self.events[self._flushed:]
        if not new_events:
            return
        target = Path(path)
        if target.exists():
            document = formats.load_json(target)
            formats.validate_reference_qson(document)
            if document["run_id"] != self.run_id:
                raise RuntimeError_("cannot append events to a different run_id")
            document["events"].extend(copy.deepcopy(new_events))
        else:
            document = formats.build_qson(self.run_id, copy.deepcopy(new_events))
        formats.validate_reference_qson(document)
        target.parent.mkdir(parents=True, exist_ok=True)
        formats.save_json(target, document)
        self._flushed = len(self.events)


ProposalProvider = Callable[[dict, dict], tuple[dict | None, str | None] | None]


def execute_unit(manifest_path, proposal_provider: ProposalProvider | None = None,
                 run_id: str | None = None, trace_output=None) -> tuple[LoadedUnit, GateRuntime, dict]:
    """Load resources, execute ORK order, route outcomes, and write QSON."""
    unit = load_unit(manifest_path)
    if trace_output is not None:
        unit.trace_path = Path(trace_output).resolve()
    runtime = GateRuntime(run_id or f"RUN_{uuid.uuid4().hex}")
    state = copy.deepcopy(unit.state)
    for gate_id in unit.flow:
        file_id, gate = unit.gates[gate_id]
        proposal = proposal_provider(gate, copy.deepcopy(state)) if proposal_provider else None
        proposed_state, proposed_id = proposal if proposal is not None else (None, None)
        result, committed = runtime.attempt_gate(
            file_id, gate, state, state["state_id"], proposed_state, proposed_id
        )
        if committed is not None:
            state = committed
        action = gate["outcomes"][result]
        if result != "PASS" or action in {"stop", "review"}:
            break
    runtime.append_to_qson_file(unit.trace_path)
    return unit, runtime, state
