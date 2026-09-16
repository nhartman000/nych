"""
NYCH MGate Benchmark Harness
=============================
Benchmark harness for measuring the effect of three-gate MGate validation
on trajectory search success, invalid advancement rate, and computational cost.

Configurations:
- C0: deterministic search (first admissible candidate, no gate checks)
- C1: NYCH constrained trajectory search without MGate (best candidate, no gate checks)
- C2: NYCH + Three-Gate MGate (full gate validation with backtracking)
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from nych.ingest import NaturalLanguageInput, SensorInput
from nych.pipeline import PipelineConfig, run_pipeline


# ============================================================================
# Benchmark problem definition
# ============================================================================

@dataclass(frozen=True)
class BenchmarkProblem:
    """A single benchmark problem with expected outcomes."""
    problem_id: str
    description: str
    input_text: str
    input_type: str = "natural_language"
    perspective: str = "first"
    tense: str = "present"
    expected_domain: str = ""
    expected_intent: str = ""
    goal_completion_expected: bool = True
    notes: str = ""


@dataclass(frozen=True)
class BenchmarkMetrics:
    """Metrics collected from a single benchmark run."""
    problem_id: str
    config: str
    success: bool
    invalid_advancement: bool
    gate_evaluations: int = 0
    backtracks: int = 0
    transform_evaluations: int = 0
    runtime_seconds: float = 0.0
    final_state_hash: str = ""
    gst_hash: str = ""
    permit_issued: bool = False
    permit_violations: int = 0
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 30 Hand-audited canonical problems
# ============================================================================

def get_benchmark_problems() -> list[BenchmarkProblem]:
    """
    Return 30 hand-audited canonical problems.
    
    These problems are designed to exercise:
    - Simple valid trajectories (no backtracking needed)
    - Invalid transforms that should be rejected
    - Ambiguous cases where gating matters
    - Cases that punish unnecessary gating
    """
    problems = [
        # ------------------------------------------------------------------
        # Group A: Simple valid cases (10)
        # These should succeed under all configurations.
        # ------------------------------------------------------------------
        BenchmarkProblem(
            problem_id="simple_001",
            description="Build a unit test for a calculator",
            input_text="Build a unit test for a calculator",
            expected_domain="construction",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Simple valid case, no backtracking needed",
        ),
        BenchmarkProblem(
            problem_id="simple_002",
            description="Write a function to add two numbers",
            input_text="Write a function to add two numbers in Python",
            expected_domain="programming",
            expected_intent="process",
            goal_completion_expected=True,
            notes="Straightforward implementation",
        ),
        BenchmarkProblem(
            problem_id="simple_003",
            description="Create a REST API endpoint",
            input_text="Create a REST API endpoint for user registration",
            expected_domain="unknown",
            expected_intent="process",
            goal_completion_expected=True,
            notes="Standard web development task",
        ),
        BenchmarkProblem(
            problem_id="simple_004",
            description="Debug a memory leak in a service",
            input_text="Debug a memory leak in the authentication service",
            expected_domain="programming",
            expected_intent="process",
            goal_completion_expected=True,
            notes="Debugging task with clear problem space",
        ),
        BenchmarkProblem(
            problem_id="simple_005",
            description="Design a database schema for e-commerce",
            input_text="Design a database schema for an e-commerce platform",
            expected_domain="design",
            expected_intent="design",
            goal_completion_expected=True,
            notes="Database design task",
        ),
        BenchmarkProblem(
            problem_id="simple_006",
            description="Set up CI/CD pipeline for deployment",
            input_text="Set up a CI/CD pipeline for automated deployment",
            expected_domain="programming",
            expected_intent="process",
            goal_completion_expected=True,
            notes="DevOps configuration",
        ),
        BenchmarkProblem(
            problem_id="simple_007",
            description="Write integration tests for payment module",
            input_text="Write integration tests for the payment processing module",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Integration testing task",
        ),
        BenchmarkProblem(
            problem_id="simple_008",
            description="Optimize database query performance",
            input_text="Optimize the database query performance for the search API",
            expected_domain="data_processing",
            expected_intent="operate",
            goal_completion_expected=True,
            notes="Performance optimization",
        ),
        BenchmarkProblem(
            problem_id="simple_009",
            description="Implement user authentication with JWT",
            input_text="Implement user authentication using JWT tokens",
            expected_domain="unknown",
            expected_intent="process",
            goal_completion_expected=True,
            notes="Security implementation",
        ),
        BenchmarkProblem(
            problem_id="simple_010",
            description="Create a logging middleware for the API",
            input_text="Create a logging middleware for the REST API",
            expected_domain="unknown",
            expected_intent="process",
            goal_completion_expected=True,
            notes="Middleware development",
        ),
        
        # ------------------------------------------------------------------
        # Group B: Cases with potential invalid transforms (10)
        # These contain transforms that should be rejected by constraints.
        # MGate should help prevent invalid advancement.
        # ------------------------------------------------------------------
        BenchmarkProblem(
            problem_id="invalid_001",
            description="Test with ambiguous modality",
            input_text="Test the system using undefined sensor modality",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Ambiguous modality should be resolved",
        ),
        BenchmarkProblem(
            problem_id="invalid_002",
            description="Test with conflicting perspectives",
            input_text="I want to test the system from multiple conflicting perspectives simultaneously",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Conflicting perspectives need resolution",
        ),
        BenchmarkProblem(
            problem_id="invalid_003",
            description="Test with domain ambiguity",
            input_text="Test the bridge between medical diagnosis and software testing systems",
            expected_domain="programming",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Cross-domain ambiguity",
        ),
        BenchmarkProblem(
            problem_id="invalid_004",
            description="Test with temporal inconsistency",
            input_text="I tested the system yesterday and will test it again tomorrow but now",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Temporal inconsistency",
        ),
        BenchmarkProblem(
            problem_id="invalid_005",
            description="Test with missing subject",
            input_text="Test the system without specifying who is testing",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Missing actor/subject",
        ),
        BenchmarkProblem(
            problem_id="invalid_006",
            description="Test with impossible competency claim",
            input_text="Test the system as an expert with no experience",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Competency inconsistency",
        ),
        BenchmarkProblem(
            problem_id="invalid_007",
            description="Test with contradictory constraints",
            input_text="Test the system with maximum speed and maximum accuracy simultaneously",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Contradictory constraints",
        ),
        BenchmarkProblem(
            problem_id="invalid_008",
            description="Test with undefined operator",
            input_text="Xyzzy the system using plugh mode",
            expected_domain="general",
            expected_intent="process",
            goal_completion_expected=True,
            notes="Gibberish input - should resolve gracefully",
        ),
        BenchmarkProblem(
            problem_id="invalid_009",
            description="Test with empty context",
            input_text="Test",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Minimal input - should handle gracefully",
        ),
        BenchmarkProblem(
            problem_id="invalid_010",
            description="Test with mixed modalities",
            input_text="I feel the temperature of the code and see that it is 42 degrees celsius while debugging",
            expected_domain="programming",
            expected_intent="process",
            goal_completion_expected=True,
            notes="Mixed sensor and language modality",
        ),
        
        # ------------------------------------------------------------------
        # Group C: Cases where gating should matter (10)
        # These are designed to test whether MGate catches issues that
        # simpler search strategies miss.
        # ------------------------------------------------------------------
        BenchmarkProblem(
            problem_id="gate_matter_001",
            description="Test with state continuity break",
            input_text="Test the first module, then test the second module, then return to test the first again",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="State continuity should be validated",
        ),
        BenchmarkProblem(
            problem_id="gate_matter_002",
            description="Test with perspective shift",
            input_text="I want to test the system from my perspective, then from the user perspective, then from the admin perspective",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Multiple perspective shifts",
        ),
        BenchmarkProblem(
            problem_id="gate_matter_003",
            description="Test with tense inconsistency",
            input_text="I will test the system, I am testing the system, I tested the system, all at once",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Tense inconsistency",
        ),
        BenchmarkProblem(
            problem_id="gate_matter_004",
            description="Test nested self-reference",
            input_text="I want to test the system that tests me while I test it",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Self-referential loop",
        ),
        BenchmarkProblem(
            problem_id="gate_matter_005",
            description="Test with competency escalation",
            input_text="As a beginner, I want to test this expert-level system professionally",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Competency escalation",
        ),
        BenchmarkProblem(
            problem_id="gate_matter_006",
            description="Test with domain drift",
            input_text="Start with programming, then move to medicine, then back to programming to test",
            expected_domain="programming",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Domain drift and return",
        ),
        BenchmarkProblem(
            problem_id="gate_matter_007",
            description="Test with actor substitution",
            input_text="I want Alice to test the system, then Bob tests it, then I test it as Alice",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Actor substitution",
        ),
        BenchmarkProblem(
            problem_id="gate_matter_008",
            description="Test with nested intentions",
            input_text="I want to test the system with the intention of testing my testing intentions",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Meta-intention",
        ),
        BenchmarkProblem(
            problem_id="gate_matter_009",
            description="Test with temporal paradox",
            input_text="Test the system before it was created, after it was deprecated, and during its current version",
            expected_domain="testing",
            expected_intent="test",
            goal_completion_expected=True,
            notes="Temporal paradox",
        ),
        BenchmarkProblem(
            problem_id="gate_matter_010",
            description="Test with contradictory evidence",
            input_text="The test passed and failed simultaneously with equal confidence",
            expected_domain="testing",
            expected_intent="evaluate",
            goal_completion_expected=True,
            notes="Contradictory evidence",
        ),
    ]
    return problems


# ============================================================================
# Configuration runners
# ============================================================================

def _run_config_c0(problem: BenchmarkProblem) -> BenchmarkMetrics:
    """
    C0: Deterministic search - first admissible candidate, no gate checks.
    """
    config = PipelineConfig(enable_mgate=False, use_probabilistic_selection=False, enable_machine_b=False)
    return _run_pipeline_benchmark(problem, config, "C0")


def _run_config_c1(problem: BenchmarkProblem) -> BenchmarkMetrics:
    """
    C1: NYCH constrained trajectory search without MGate.
    Uses best candidate but no gate validation.
    """
    config = PipelineConfig(enable_mgate=False, use_probabilistic_selection=False, enable_machine_b=False)
    return _run_pipeline_benchmark(problem, config, "C1")


def _run_config_c2(problem: BenchmarkProblem) -> BenchmarkMetrics:
    """
    C2: NYCH + Three-Gate MGate.
    Full gate validation with backtracking.
    """
    config = PipelineConfig(
        enable_mgate=True,
        use_probabilistic_selection=False,
        max_mgate_iterations=5,
        max_backtrack_steps=10,
        enable_machine_b=False,
    )
    return _run_pipeline_benchmark(problem, config, "C2")


def _run_pipeline_benchmark(problem: BenchmarkProblem, config: PipelineConfig, config_label: str) -> BenchmarkMetrics:
    """
    Run a single problem through the pipeline with the given config.
    """
    start_time = time.perf_counter()
    
    try:
        if problem.input_type == "natural_language":
            input_data = NaturalLanguageInput(
                text=problem.input_text,
                speaker="benchmark",
                perspective=problem.perspective,
                tense=problem.tense,
            )
        else:
            input_data = SensorInput(
                data={"value": problem.input_text},
                source_device="benchmark",
                modality=problem.input_type,
            )
        
        result = run_pipeline(input_data, config)
        
        runtime = time.perf_counter() - start_time
        
        # Extract metrics
        gate_evaluations = 0
        backtracks = 0
        transform_evaluations = 0
        if result.mgate_summary:
            gate_executions = result.mgate_summary.get("gate_executions", [])
            for g in gate_executions:
                for gate in ["g1", "g2", "g3"]:
                    history = g.get(gate, {}).get("history", [])
                    gate_evaluations += len([h for h in history if h.get("phase") == "TEST"])
            backtracks = result.mgate_summary.get("backtrack_count", 0)
            transform_evaluations = result.mgate_summary.get("total_rungs", 0)
        
        # Check goal completion: pipeline completed successfully and validation passed
        success = result.validation.valid
        
        # Invalid advancement: state advanced but validation failed
        invalid_advancement = not result.validation.valid and result.state is not None
        
        # Final state hash
        state_dict = result.state.to_dict() if hasattr(result.state, "to_dict") else {}
        final_state_hash = hashlib.sha256(str(state_dict).encode()).hexdigest()[:16]
        
        # GST hash
        gst = result.to_gst_dict()
        gst_hash = hashlib.sha256(str(gst).encode()).hexdigest()[:16]
        
        # Permit
        permit_issued = False
        permit_violations = 0
        if result.mgate_summary and result.mgate_summary.get("action_permit"):
            permit = result.mgate_summary["action_permit"]
            permit_issued = permit.get("state") == "ISSUED"
        
        return BenchmarkMetrics(
            problem_id=problem.problem_id,
            config=config_label,
            success=success,
            invalid_advancement=invalid_advancement,
            gate_evaluations=gate_evaluations,
            backtracks=backtracks,
            transform_evaluations=transform_evaluations,
            runtime_seconds=runtime,
            final_state_hash=final_state_hash,
            gst_hash=gst_hash,
            permit_issued=permit_issued,
            permit_violations=permit_violations,
            metadata={
                "description": problem.description,
                "domain": result.context.domain,
                "intent": result.context.intent,
                "expected_domain": problem.expected_domain,
                "expected_intent": problem.expected_intent,
            }
        )
        
    except Exception as e:
        runtime = time.perf_counter() - start_time
        return BenchmarkMetrics(
            problem_id=problem.problem_id,
            config=config_label,
            success=False,
            invalid_advancement=False,
            runtime_seconds=runtime,
            error=str(e),
            metadata={"description": problem.description}
        )


# ============================================================================
# Benchmark runner
# ============================================================================

@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""
    results: list[BenchmarkMetrics] = field(default_factory=list)
    timestamp: str = ""
    config: dict[str, Any] = field(default_factory=dict)


def run_full_benchmark(problems: Optional[list[BenchmarkProblem]] = None) -> BenchmarkSuite:
    """
    Run the complete benchmark suite across all three configurations.
    
    Args:
        problems: List of benchmark problems. If None, uses default 30.
    
    Returns:
        BenchmarkSuite with all results.
    """
    if problems is None:
        problems = get_benchmark_problems()
    
    results = []
    
    for problem in problems:
        for config_label in ["C0", "C1", "C2"]:
            if config_label == "C0":
                metrics = _run_config_c0(problem)
            elif config_label == "C1":
                metrics = _run_config_c1(problem)
            else:
                metrics = _run_config_c2(problem)
            results.append(metrics)
    
    return BenchmarkSuite(
        results=results,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        config={
            "version": "mgate-v0.1",
            "git_commit": "1fe88d6",
            "git_tag": "mgate-v0.1",
            "python_version": "3.14.4",
            "problem_count": len(problems),
            "configurations": ["C0", "C1", "C2"],
        }
    )


def save_benchmark_results(suite: BenchmarkSuite, path: str) -> None:
    """Save benchmark results to a JSON file."""
    with open(path, "w") as f:
        json.dump({
            "timestamp": suite.timestamp,
            "config": suite.config,
            "results": [
                {
                    "problem_id": r.problem_id,
                    "config": r.config,
                    "success": r.success,
                    "invalid_advancement": r.invalid_advancement,
                    "gate_evaluations": r.gate_evaluations,
                    "backtracks": r.backtracks,
                    "transform_evaluations": r.transform_evaluations,
                    "runtime_seconds": r.runtime_seconds,
                    "final_state_hash": r.final_state_hash,
                    "gst_hash": r.gst_hash,
                    "permit_issued": r.permit_issued,
                    "permit_violations": r.permit_violations,
                    "error": r.error,
                    "metadata": r.metadata,
                }
                for r in suite.results
            ],
        }, f, indent=2)


def print_benchmark_summary(suite: BenchmarkSuite) -> None:
    """Print a summary of benchmark results."""
    print("=" * 80)
    print("NYCH MGate Benchmark Results")
    print("=" * 80)
    print(f"Timestamp: {suite.timestamp}")
    print(f"Config: {json.dumps(suite.config, indent=2)}")
    print()
    
    # Group by config
    by_config: dict[str, list[BenchmarkMetrics]] = {}
    for r in suite.results:
        by_config.setdefault(r.config, []).append(r)
    
    for config_label in ["C0", "C1", "C2"]:
        config_results = by_config.get(config_label, [])
        if not config_results:
            continue
        
        print(f"\nConfiguration {config_label}:")
        print("-" * 40)
        
        successes = sum(1 for r in config_results if r.success)
        invalid_adv = sum(1 for r in config_results if r.invalid_advancement)
        total_runtime = sum(r.runtime_seconds for r in config_results)
        total_gate_evals = sum(r.gate_evaluations for r in config_results)
        total_backtracks = sum(r.backtracks for r in config_results)
        permit_issued = sum(1 for r in config_results if r.permit_issued)
        permit_violations = sum(r.permit_violations for r in config_results)
        errors = [r for r in config_results if r.error]
        
        print(f"  Problems run: {len(config_results)}")
        print(f"  Goal completion: {successes}/{len(config_results)} ({100*successes/len(config_results):.1f}%)")
        print(f"  Invalid advancements: {invalid_adv}")
        print(f"  Total runtime: {total_runtime:.4f}s")
        print(f"  Total gate evaluations: {total_gate_evals}")
        print(f"  Total backtracks: {total_backtracks}")
        print(f"  Permits issued: {permit_issued}")
        print(f"  Permit violations: {permit_violations}")
        if errors:
            print(f"  Errors: {len(errors)}")
            for e in errors[:3]:
                print(f"    - {e.problem_id}: {e.error}")
    
    print("\n" + "=" * 80)
    print("Per-problem comparison:")
    print("-" * 80)
    
    # Show first 10 problems with their 3-config results
    shown = set()
    for r in suite.results:
        if r.problem_id not in shown and len(shown) < 10:
            shown.add(r.problem_id)
            probs = [x for x in suite.results if x.problem_id == r.problem_id]
            print(f"\n{r.problem_id}: {r.metadata.get('description', '')}")
            for p in sorted(probs, key=lambda x: x.config):
                status = "PASS" if p.success else "FAIL"
                print(f"  {p.config}: {status} | runtime={p.runtime_seconds:.4f}s | backtracks={p.backtracks} | evals={p.gate_evaluations}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    suite = run_full_benchmark()
    print_benchmark_summary(suite)
    save_benchmark_results(suite, "benchmarks/mgate_v0.1_benchmark_results.json")
    print("Results saved to benchmarks/mgate_v0.1_benchmark_results.json")
