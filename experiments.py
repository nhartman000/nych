"""
NYCH MGate Experimental Validation
====================================
Runs the benchmark corpus across three frozen configurations
and analyzes whether MGate provides measurable benefit.

Configurations:
- C0: Deterministic search (first admissible candidate, no gate checks)
- C1: NYCH constrained trajectory search without MGate
- C2: NYCH + Three-Gate MGate (full gate validation with backtracking)
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from benchmarks.mgate_benchmark import (
    BenchmarkMetrics,
    BenchmarkProblem,
    BenchmarkSuite,
    _run_config_c0,
    _run_config_c1,
    _run_config_c2,
    get_benchmark_problems,
)
from nych.ingest import NaturalLanguageInput
from nych.pipeline import PipelineConfig, run_pipeline


# ============================================================================
# Experiment configuration
# ============================================================================

@dataclass
class ExperimentConfig:
    """Configuration for an experiment run."""
    name: str
    description: str
    mgate_enabled: bool
    machine_b_enabled: bool
    max_mgate_iterations: int
    max_backtrack_steps: int
    use_probabilistic_selection: bool = False
    selection_seed: int | None = None


EXPERIMENT_CONFIGS = {
    "C0": ExperimentConfig(
        name="C0_deterministic",
        description="Deterministic search - first admissible candidate, no gate checks",
        mgate_enabled=False,
        machine_b_enabled=False,
        max_mgate_iterations=0,
        max_backtrack_steps=0,
    ),
    "C1": ExperimentConfig(
        name="C1_nych_no_mgate",
        description="NYCH constrained trajectory search without MGate",
        mgate_enabled=False,
        machine_b_enabled=False,
        max_mgate_iterations=0,
        max_backtrack_steps=0,
    ),
    "C2": ExperimentConfig(
        name="C2_nych_with_mgate",
        description="NYCH + Three-Gate MGate with backtracking",
        mgate_enabled=True,
        machine_b_enabled=False,
        max_mgate_iterations=5,
        max_backtrack_steps=10,
    ),
}


# ============================================================================
# Experiment runner
# ============================================================================

def run_experiments(problems: list[BenchmarkProblem]) -> dict[str, Any]:
    """
    Run all problems through all three configurations and collect results.
    
    Returns:
        Dict with experiment results, metrics, and analysis.
    """
    all_results: dict[str, list[BenchmarkMetrics]] = {}
    
    for config_name in ["C0", "C1", "C2"]:
        config = EXPERIMENT_CONFIGS[config_name]
        pipeline_config = PipelineConfig(
            enable_mgate=config.mgate_enabled,
            use_probabilistic_selection=config.use_probabilistic_selection,
            selection_seed=config.selection_seed,
            max_mgate_iterations=config.max_mgate_iterations,
            max_backtrack_steps=config.max_backtrack_steps,
            enable_machine_b=config.machine_b_enabled,
        )
        
        config_results = []
        for problem in problems:
            if config_name == "C0":
                metrics = _run_config_c0(problem)
            elif config_name == "C1":
                metrics = _run_config_c1(problem)
            else:
                metrics = _run_config_c2(problem)
            config_results.append(metrics)
        
        all_results[config_name] = config_results
        print(f"  {config_name}: {sum(1 for r in config_results if r.success)}/{len(config_results)} succeeded")
    
    # Analyze cross-configuration comparison
    analysis = analyze_results(all_results)
    
    return {
        "configs": {name: config.__dict__ for name, config in EXPERIMENT_CONFIGS.items()},
        "results": {name: [r for r in results] for name, results in all_results.items()},
        "analysis": analysis,
    }


def analyze_results(all_results: dict[str, list[BenchmarkMetrics]]) -> dict[str, Any]:
    """
    Analyze cross-configuration results to answer:
    - Does MGate reduce invalid advancement?
    - What computational cost buys that reduction?
    """
    analysis: dict[str, Any] = {}
    
    c0_results = all_results.get("C0", [])
    c1_results = all_results.get("C1", [])
    c2_results = all_results.get("C2", [])
    
    # Success rate comparison
    c0_success = sum(1 for r in c0_results if r.success) / max(len(c0_results), 1)
    c2_success = sum(1 for r in c2_results if r.success) / max(len(c2_results), 1)
    
    # Invalid advancement comparison
    c0_invalid = sum(r.invalid_advancement for r in c0_results)
    c2_invalid = sum(r.invalid_advancement for r in c2_results)
    
    # Gate evaluation overhead
    c2_gate_evals = sum(r.gate_evaluations for r in c2_results)
    c0_gate_evals = sum(r.gate_evaluations for r in c0_results)
    
    # Backtrack count
    c2_backtracks = sum(r.backtracks for r in c2_results)
    
    # Runtime comparison
    c0_runtime = sum(r.runtime_seconds for r in c0_results)
    c2_runtime = sum(r.runtime_seconds for r in c2_results)
    
    # Per-problem comparison
    per_problem = []
    for i, problem in enumerate(get_benchmark_problems()):
        c0 = c0_results[i] if i < len(c0_results) else None
        c2 = c2_results[i] if i < len(c2_results) else None
        
        per_problem.append({
            "problem_id": c0.problem_id if c0 else "",
            "c0_success": c0.success if c0 else False,
            "c2_success": c2.success if c2 else False,
            "c0_gate_evals": c0.gate_evaluations if c0 else 0,
            "c2_gate_evals": c2.gate_evaluations if c2 else 0,
            "c0_runtime": c0.runtime_seconds if c0 else 0.0,
            "c2_runtime": c2.runtime_seconds if c2 else 0.0,
            "c2_backtracks": c2.backtracks if c2 else 0,
        })
    
    analysis = {
        "success_rate": {
            "C0": c0_success,
            "C1": sum(1 for r in c1_results if r.success) / max(len(c1_results), 1),
            "C2": c2_success,
        },
        "invalid_advancements": {
            "C0": c0_invalid,
            "C1": sum(r.invalid_advancement for r in c1_results),
            "C2": c2_invalid,
        },
        "gate_evaluations": {
            "C0": c0_gate_evals,
            "C2": c2_gate_evals,
            "overhead": c2_gate_evals - c0_gate_evals,
        },
        "backtracks": {
            "C2_total": c2_backtracks,
        },
        "runtime": {
            "C0_total": c0_runtime,
            "C1_total": sum(r.runtime_seconds for r in c1_results),
            "C2_total": c2_runtime,
            "overhead": c2_runtime - c0_runtime,
        },
        "per_problem": per_problem,
        "conclusion": _draw_conclusion(
            c0_success, c2_success, c0_invalid, c2_invalid,
            c2_gate_evals, c0_runtime, c2_runtime
        ),
    }
    
    return analysis


def _draw_conclusion(
    c0_success: float,
    c2_success: float,
    c0_invalid: int,
    c2_invalid: int,
    c2_gate_evals: int,
    c0_runtime: float,
    c2_runtime: float,
) -> str:
    """Draw a conclusion about MGate's effect."""
    if c2_success > c0_success:
        success_improvement = (c2_success - c0_success) * 100
        invalid_reduction = c0_invalid - c2_invalid
        return (
            f"MGate improved success rate by {success_improvement:.1f}% "
            f"and reduced invalid advancements by {invalid_reduction} "
            f"at the cost of {c2_gate_evals} gate evaluations and "
            f"{c2_runtime - c0_runtime:.4f}s runtime overhead."
        )
    elif c2_success == c0_success:
        invalid_reduction = c0_invalid - c2_invalid
        return (
            f"MGate shows no change in success rate or invalid advancement "
            f"for these problems. Overhead: {c2_gate_evals} gate evaluations, "
            f"{c2_runtime - c0_runtime:.4f}s runtime. "
            f"This suggests the constraint stage already filters invalid transforms "
            f"effectively, and MGate adds cost without benefit on well-constrained inputs."
        )
    else:
        return (
            f"MGate reduced success rate ({c0_success:.1%} -> {c2_success:.1%}). "
            f"This may indicate over-constraining or gate definitions that are too strict."
        )


# ============================================================================
# Deterministic replay verification
# ============================================================================

def verify_determinism(problem: BenchmarkProblem, config_name: str, runs: int = 3) -> dict[str, Any]:
    """
    Verify that the same problem produces byte-identical results across runs.
    
    This implements the determinism check: identical inputs produce
    byte-identical .gst output across repeated runs.
    """
    config = EXPERIMENT_CONFIGS[config_name]
    pipeline_config = PipelineConfig(
        enable_mgate=config.mgate_enabled,
        use_probabilistic_selection=config.use_probabilistic_selection,
        selection_seed=config.selection_seed,
        max_mgate_iterations=config.max_mgate_iterations,
        max_backtrack_steps=config.max_backtrack_steps,
        enable_machine_b=config.machine_b_enabled,
    )
    
    input_data = NaturalLanguageInput(
        text=problem.input_text,
        speaker="benchmark",
        perspective=problem.perspective,
        tense=problem.tense,
    )
    
    hashes = []
    for _ in range(runs):
        result = run_pipeline(input_data, pipeline_config)
        gst = result.to_gst_dict()
        h = hashlib.sha256(str(gst).encode()).hexdigest()
        hashes.append(h)
    
    deterministic = len(set(hashes)) == 1
    
    return {
        "problem_id": problem.problem_id,
        "config": config_name,
        "runs": runs,
        "hashes": hashes,
        "deterministic": deterministic,
    }


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    import os
    os.makedirs("benchmarks", exist_ok=True)
    
    print("=" * 80)
    print("NYCH MGate Experiment Suite")
    print("=" * 80)
    print()
    
    # Run experiments
    print("Running 30 problems x 3 configurations...")
    print()
    
    problems = get_benchmark_problems()
    experiment_data = run_experiments(problems)
    
    print()
    print("Analysis:")
    print("-" * 40)
    analysis = experiment_data["analysis"]
    
    print(f"  Success rates: C0={analysis['success_rate']['C0']:.1%}, "
          f"C1={analysis['success_rate']['C1']:.1%}, "
          f"C2={analysis['success_rate']['C2']:.1%}")
    
    print(f"  Invalid advancements: C0={analysis['invalid_advancements']['C0']}, "
          f"C1={analysis['invalid_advancements']['C1']}, "
          f"C2={analysis['invalid_advancements']['C2']}")
    
    print(f"  Gate evaluations: C0={analysis['gate_evaluations']['C0']}, "
          f"C2={analysis['gate_evaluations']['C2']}")
    
    print(f"  Total backtracks: C2={analysis['backtracks']['C2_total']}")
    
    print(f"  Runtime: C0={analysis['runtime']['C0_total']:.4f}s, "
          f"C1={analysis['runtime']['C1_total']:.4f}s, "
          f"C2={analysis['runtime']['C2_total']:.4f}s")
    
    print(f"  MGate overhead: {analysis['runtime']['overhead']:.4f}s")
    
    print()
    print(f"Conclusion: {analysis['conclusion']}")
    
    print()
    print("Verifying determinism (3 problems x 3 configs x 3 runs)...")
    print("-" * 40)
    
    determinism_results = []
    for problem in problems[:3]:
        for config_name in ["C0", "C1", "C2"]:
            det = verify_determinism(problem, config_name, runs=3)
            determinism_results.append(det)
            status = "PASS" if det["deterministic"] else "FAIL"
            print(f"  {problem.problem_id} / {config_name}: {status}")
    
    experiment_data["determinism"] = determinism_results
    
    # Save results
    output_path = "benchmarks/mgate_experiment_results.json"
    with open(output_path, "w") as f:
        json.dump(experiment_data, f, indent=2, default=str)
    
    print()
    print(f"Results saved to {output_path}")
    print()
    print("=" * 80)
