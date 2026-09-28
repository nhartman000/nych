"""
tote_registry.py -- Domain/Specialty/Function/Technique registry of TOTE
loops. Serialized to formats.EXT_TOTE_REGISTRY (".totereg"), NOT ".g8son" --
the prototype's use of .g8son for this was a real schema conflict (a TOTE
registry is not "bounded conditional gates" in the canonical sense) and has
been renamed here rather than reconciled by changing the canon.
"""

from __future__ import annotations
import json

from .symbol_codec import ToteLoop, ModalityEvent
from . import formats


class ToteRegistry:
    def __init__(self):
        self.data = {}

    def register(self, domain, specialty, function, technique, tote_loop):
        self.data.setdefault(domain, {}).setdefault(specialty, {}).setdefault(
            function, {})[technique] = tote_loop

    def lookup(self, domain, specialty, function, technique):
        return (self.data.get(domain, {}).get(specialty, {})
                .get(function, {}).get(technique))

    def list_techniques(self, domain, specialty, function):
        return list(self.data.get(domain, {}).get(specialty, {}).get(function, {}).keys())


def _modality_event_to_dict(ev):
    return {"modality": ev.modality, "content": ev.content}


def _modality_event_from_dict(d):
    return ModalityEvent(d["modality"], d["content"])


def _tote_loop_to_dict(loop):
    return {
        "name": loop.name,
        "test_external": _modality_event_to_dict(loop.test_external),
        "test_internal": _modality_event_to_dict(loop.test_internal),
        "operate_steps": [
            {"type": "loop", "loop": _tote_loop_to_dict(s)} if isinstance(s, ToteLoop)
            else {"type": "event", "event": _modality_event_to_dict(s)}
            for s in loop.operate_steps
        ],
        "default_sequence": loop.default_sequence,
        "max_iterations": loop.max_iterations,
    }


def _tote_loop_from_dict(d):
    steps = []
    for s in d["operate_steps"]:
        if s["type"] == "loop":
            steps.append(_tote_loop_from_dict(s["loop"]))
        else:
            steps.append(_modality_event_from_dict(s["event"]))
    return ToteLoop(
        name=d["name"],
        test_external=_modality_event_from_dict(d["test_external"]),
        test_internal=_modality_event_from_dict(d["test_internal"]),
        operate_steps=steps,
        max_iterations=d.get("max_iterations", 10),
        default_sequence=d.get("default_sequence"),
    )


def save_registry(path: str, registry: ToteRegistry) -> None:
    """path should end in formats.EXT_TOTE_REGISTRY (.totereg), not .g8son."""
    serialized = {}
    for domain, specs in registry.data.items():
        serialized[domain] = {}
        for specialty, funcs in specs.items():
            serialized[domain][specialty] = {}
            for function, techs in funcs.items():
                serialized[domain][specialty][function] = {
                    tech: _tote_loop_to_dict(loop) for tech, loop in techs.items()
                }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serialized, f, ensure_ascii=False, indent=2)


def load_registry(path: str) -> ToteRegistry:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    registry = ToteRegistry()
    for domain, specs in raw.items():
        for specialty, funcs in specs.items():
            for function, techs in funcs.items():
                for tech, loop_dict in techs.items():
                    registry.register(domain, specialty, function, tech,
                                       _tote_loop_from_dict(loop_dict))
    return registry


def save_globals(path: str, gestalt_lexicon: dict) -> None:
    """path should end in formats.EXT_NYCH_GLOBALS (.nychg), not .gst.
    .gst is reserved by the MG8 canon for structured state/context."""
    data = {"modality_symbols": ModalityEvent.SYMBOLS, "gestalt_lexicon": gestalt_lexicon}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_globals(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
