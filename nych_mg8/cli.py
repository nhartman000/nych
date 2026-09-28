#!/usr/bin/env python3
"""
cli.py -- Command-line entry point. No hardcoded absolute paths anywhere
(fixes the confirmed /mnt/user-data/outputs/ FileNotFoundError defect) --
all output goes under a caller-specified or ./output directory that is
created if missing.

Usage:
    python3 -m nych_mg8.cli encode "I went to the store to buy a hammer."
    python3 -m nych_mg8.cli demo-gate
"""
from __future__ import annotations
import argparse
import os
import sys

from . import formats, runtime
from .symbol_codec import verify_round_trip


def cmd_encode(args):
    encoded, decoded, legend = verify_round_trip(args.sentence)
    print(f"Original: {args.sentence}")
    print(f"Encoded:  {encoded}")
    print()
    print(legend)
    print()
    print(f"Round-trip exact match: {decoded == args.sentence}")


def cmd_demo_gate(args):
    """Runs one canonical .mg8 unit end to end: .gst state -> .g8son gate ->
    runtime evaluation -> .qson ledger. Writes files under --output-dir
    (default ./output), never a hardcoded absolute path."""
    out_dir = args.output_dir
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "state"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "gates"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "trace"), exist_ok=True)

    state = formats.build_gst("STATE_001", external_current={
        "object_detected": True, "confidence": 0.95,
    })
    formats.validate_gst(state)
    formats.save_json(os.path.join(out_dir, "state", "main.gst"), state)

    cond1 = formats.build_condition("external.current.object_detected", "==", True)
    cond2 = formats.build_condition("external.current.confidence", ">=", 0.9)
    gate = formats.build_gate("gate_001", 1, "AND", [cond1, cond2])
    g8son = formats.build_g8son("example.gates.001", [gate])
    formats.validate_g8son(g8son)
    formats.save_json(os.path.join(out_dir, "gates", "main.g8son"), g8son)

    flow = formats.build_flow_ork(["gate_001"])
    formats.validate_flow_ork(flow)
    formats.save_json(os.path.join(out_dir, "flow.ork"), flow)

    manifest = formats.build_mg8_manifest(
        unit_id="example.unit.001", entry="flow.ork",
        state=["state/main.gst"], gates=["gates/main.g8son"], trace="trace/run.qson",
    )
    formats.validate_mg8_manifest(manifest)
    formats.save_json(os.path.join(out_dir, "unit.mg8"), manifest)

    _unit, rt, _state = runtime.execute_unit(os.path.join(out_dir, "unit.mg8"), run_id="RUN_001")
    print(f"Gate result: {rt.events[-1]['result']}")
    print(f"Files written under: {out_dir}")


def cmd_run(args):
    _unit, rt, state = runtime.execute_unit(args.manifest, trace_output=args.trace_output)
    print(f"Run ID: {rt.run_id}")
    print(f"Gate attempts: {len(rt.events)}")
    print(f"Final result: {rt.events[-1]['result']}")
    print(f"Final state ID: {state.get('state_id')}")


def main():
    parser = argparse.ArgumentParser(prog="nych_mg8")
    sub = parser.add_subparsers(dest="command", required=True)

    p_encode = sub.add_parser("encode", help="Encode a sentence and verify exact round-trip.")
    p_encode.add_argument("sentence")
    p_encode.set_defaults(func=cmd_encode)

    p_gate = sub.add_parser("demo-gate", help="Run one canonical .mg8 unit end to end.")
    p_gate.add_argument("--output-dir", default="./output")
    p_gate.set_defaults(func=cmd_demo_gate)

    p_run = sub.add_parser("run", help="Load and execute a canonical .mg8 unit.")
    p_run.add_argument("manifest")
    p_run.add_argument("--trace-output", help="Write this run to a separate QSON path.")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
