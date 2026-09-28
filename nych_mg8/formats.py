"""Canonical MG8 structures and explicitly named reference-profile checks."""
from __future__ import annotations

import json
from pathlib import PurePosixPath
from typing import Any


class SchemaError(ValueError):
    pass


EXT_PACKAGE, EXT_UNIT, EXT_ORCHESTRATION = ".mg8pk", ".mg8", ".ork"
EXT_STATE, EXT_GATES, EXT_LEDGER = ".gst", ".g8son", ".qson"
EXT_NYCH_GLOBALS, EXT_TOTE_REGISTRY = ".nychg", ".totereg"
VALID_RESULTS = {"PASS", "FAIL", "INTERMEDIATE"}
VALID_EVENT_TYPES = {"gate_attempt", "override", "correction", "state_commit", "external_input", "runtime_error", "review"}
REFERENCE_GATE_TYPES = {"AND", "OR"}
REFERENCE_OPERATORS = {"==", "!=", ">", ">=", "<", "<="}


def _require(condition, message):
    if not condition:
        raise SchemaError(message)


def _exact(document, allowed, label):
    extra = set(document) - set(allowed)
    _require(not extra, f"{label} has unsupported top-level keys: {sorted(extra)}")


def validate_resource_reference(reference: str, suffix: str) -> None:
    _require(isinstance(reference, str) and reference, "resource reference must be non-empty")
    _require("\\" not in reference, f"resource path must use '/': {reference!r}")
    path = PurePosixPath(reference)
    _require(not path.is_absolute() and ".." not in path.parts, f"unsafe resource path: {reference!r}")
    _require(reference.endswith(suffix), f"resource path must end in {suffix}: {reference!r}")


def build_mg8_manifest(unit_id, entry, state, gates, trace, metadata=None):
    return {"mg8_version": "1.0", "unit_id": unit_id, "entry": entry, "state": list(state), "gates": list(gates), "trace": trace, "metadata": metadata or {}}


def validate_mg8_manifest(d):
    _require(isinstance(d, dict), ".mg8 must be an object")
    _exact(d, {"mg8_version", "unit_id", "entry", "state", "gates", "trace", "metadata"}, ".mg8")
    for key in ("mg8_version", "unit_id", "entry", "state", "gates", "trace"):
        _require(key in d, f".mg8 missing {key!r}")
    _require(isinstance(d["mg8_version"], str) and d["mg8_version"], "mg8_version must be non-empty")
    _require(isinstance(d["unit_id"], str) and d["unit_id"], "unit_id must be non-empty")
    validate_resource_reference(d["entry"], EXT_ORCHESTRATION)
    validate_resource_reference(d["trace"], EXT_LEDGER)
    for key, suffix in (("state", EXT_STATE), ("gates", EXT_GATES)):
        refs = d[key]
        _require(isinstance(refs, list) and refs, f"{key} must be non-empty")
        _require(len(refs) == len(set(refs)), f"{key} references must be unique")
        for ref in refs:
            validate_resource_reference(ref, suffix)
    _require("metadata" not in d or isinstance(d["metadata"], dict), "metadata must be an object")


def build_gst(state_id, current=None, internal_current=None, external_current=None,
              prior=None, internal_prior=None, external_prior=None, intent=None,
              outcome_expectation=None, constraints=None):
    return {"gst_version": "1.0", "state_id": state_id, "prior": prior or {},
            "current": current or {}, "internal": {"prior": internal_prior or {}, "current": internal_current or {}},
            "external": {"prior": external_prior or {}, "current": external_current or {}},
            "intent": intent, "outcome_expectation": outcome_expectation,
            "constraints": constraints if constraints is not None else {}}


def validate_gst(d):
    """Validate the open GST baseline; GST has no published closed JSON schema."""
    _require(isinstance(d, dict), ".gst must be an object")
    _require(isinstance(d.get("gst_version"), str) and d["gst_version"], ".gst missing gst_version")
    _require(isinstance(d.get("state_id"), str) and d["state_id"], ".gst missing state_id")
    for side in ("internal", "external"):
        if side in d:
            _require(isinstance(d[side], dict), f"{side} must be an object")
            for phase in ("prior", "current"):
                if phase in d[side]:
                    _require(isinstance(d[side][phase], dict), f"{side}.{phase} must be an object")


def build_condition(path, operator, value):
    return {"path": path, "operator": operator, "value": value}


def build_gate(gate_id, order, gate_type, conditions, on_pass="continue", on_fail="stop", on_intermediate="review"):
    return {"gate_id": gate_id, "order": order, "type": gate_type, "conditions": list(conditions),
            "outcomes": {"PASS": on_pass, "FAIL": on_fail, "INTERMEDIATE": on_intermediate}}


def build_g8son(file_id, gates, metadata=None):
    d = {"g8son_version": "1.0", "file_id": file_id, "gates": list(gates)}
    if metadata is not None:
        d["metadata"] = metadata
    validate_g8son(d)
    return d


def validate_g8son(d):
    """Canonical interchange validation; operator semantics remain profile-defined."""
    _require(isinstance(d, dict), ".g8son must be an object")
    _exact(d, {"g8son_version", "file_id", "gates", "metadata"}, ".g8son")
    _require(isinstance(d.get("g8son_version"), str) and d["g8son_version"], ".g8son missing version")
    _require(isinstance(d.get("file_id"), str) and d["file_id"], ".g8son missing file_id")
    gates = d.get("gates")
    _require(isinstance(gates, list) and 1 <= len(gates) <= 3, ".g8son must contain 1-3 gates")
    seen = set()
    for gate in gates:
        _require(isinstance(gate, dict), "gate must be an object")
        for key in ("gate_id", "type", "conditions"):
            _require(key in gate, f"gate missing {key!r}")
        gate_id = gate["gate_id"]
        _require(isinstance(gate_id, str) and gate_id and gate_id not in seen, "gate_id must be non-empty and unique")
        _require(gate_id != d["file_id"], "file_id and gate_id must differ")
        seen.add(gate_id)
        _require(isinstance(gate["type"], str) and gate["type"], "gate type must be non-empty")
        _require(isinstance(gate["conditions"], list) and gate["conditions"], "conditions must be non-empty")
        _require(all(isinstance(c, (str, dict)) for c in gate["conditions"]), "conditions must contain strings or objects")
        if "order" in gate:
            _require(isinstance(gate["order"], int) and gate["order"] >= 1, "order must be >= 1")
        if "outcomes" in gate:
            _require(isinstance(gate["outcomes"], dict) and set(gate["outcomes"]) <= VALID_RESULTS, "invalid outcome key")
    _require("metadata" not in d or isinstance(d["metadata"], dict), "metadata must be an object")


def validate_reference_g8son(d):
    validate_g8son(d)
    for gate in d["gates"]:
        _require(gate["type"] in REFERENCE_GATE_TYPES, "reference runtime supports AND/OR only")
        _require("outcomes" in gate and set(gate["outcomes"]) == VALID_RESULTS, "reference gate requires all outcome routes")
        for condition in gate["conditions"]:
            _require(isinstance(condition, dict), "reference runtime requires structured predicates")
            _require(isinstance(condition.get("path"), str) and condition["path"], "predicate path required")
            _require(condition.get("operator") in REFERENCE_OPERATORS and "value" in condition, "invalid predicate")


def build_flow_ork(flow):
    return {"ork_version": "0.1-reference", "flow": list(flow)}


def validate_flow_ork(d):
    _require(isinstance(d, dict) and d.get("ork_version") == "0.1-reference", "unsupported ORK profile")
    _require(isinstance(d.get("flow"), list) and d["flow"], "flow must be non-empty")
    _require(all(isinstance(x, str) and x for x in d["flow"]), "flow entries must be gate IDs")


def build_qson_event(trace_id, run_id, sequence, event_type, file_id=None,
                     gate_id=None, input_state_id=None, result=None, action=None,
                     output_state_id=None, actor_type="runtime", actor_id="mg8-engine",
                     timestamp="", evidence=None):
    event = {"trace_id": trace_id, "run_id": run_id, "sequence": sequence,
             "event_type": event_type, "actor": {"type": actor_type, "id": actor_id},
             "timestamp": timestamp}
    values = {"file_id": file_id, "gate_id": gate_id, "input_state_id": input_state_id,
              "result": result, "action": action, "output_state_id": output_state_id, "evidence": evidence}
    event.update({k: v for k, v in values.items() if v is not None})
    return event


def build_qson(run_id, events, metadata=None):
    d = {"qson_version": "1.0", "run_id": run_id, "events": list(events)}
    if metadata is not None:
        d["metadata"] = metadata
    return d


def validate_qson(d):
    """Canonical validation supports gate and non-gate QSON events."""
    _require(isinstance(d, dict), ".qson must be an object")
    _exact(d, {"qson_version", "run_id", "events", "metadata"}, ".qson")
    _require(isinstance(d.get("qson_version"), str) and d["qson_version"], ".qson missing version")
    run_id = d.get("run_id")
    _require(isinstance(run_id, str) and run_id, ".qson missing run_id")
    events = d.get("events")
    _require(isinstance(events, list) and events, ".qson events must be a non-empty array")
    trace_ids = set()
    for event in events:
        for key in ("trace_id", "run_id", "sequence", "event_type", "actor"):
            _require(key in event, f"event missing {key!r}")
        trace_id, sequence = event["trace_id"], event["sequence"]
        _require(isinstance(trace_id, str) and trace_id and trace_id not in trace_ids, "trace_id must be unique")
        _require(isinstance(sequence, int) and sequence >= 1, "sequence must be positive")
        trace_ids.add(trace_id)
        _require(event["event_type"] in VALID_EVENT_TYPES, "invalid event_type")
        actor = event["actor"]
        _require(isinstance(actor, dict) and all(isinstance(actor.get(k), str) and actor[k] for k in ("type", "id")), "actor requires type/id")
        if "result" in event:
            _require(event["result"] in VALID_RESULTS, "invalid result")
    _require("metadata" not in d or isinstance(d["metadata"], dict), "metadata must be an object")


def validate_reference_qson(d):
    validate_qson(d)
    sequences = set()
    for event in d["events"]:
        _require(event["run_id"] == d["run_id"], "event run_id must match ledger in reference profile")
        _require(event["sequence"] not in sequences, "sequence must be unique within a reference-profile run")
        sequences.add(event["sequence"])
        if event["event_type"] == "gate_attempt":
            for key in ("file_id", "gate_id", "input_state_id", "result", "action"):
                _require(key in event, f"gate_attempt missing {key!r}")
            _require(len({event["file_id"], event["gate_id"], event["trace_id"]}) == 3, "file/gate/trace identities must differ")


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
