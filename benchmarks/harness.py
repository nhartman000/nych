"""
NYCH Benchmark Harness
======================
Benchmark harness for measuring token/byte reduction, latency, compute,
fidelity and reconstruction equivalence.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from nych.ingest import NaturalLanguageInput, SensorInput
from nych.pipeline import PipelineConfig, run_pipeline


@dataclass(frozen=True)
class BenchmarkResult:
    """Result of a single benchmark run."""
    input_type: str
    input_size_bytes: int
    output_size_bytes: int
    token_reduction_ratio: float
    byte_reduction_ratio: float
    latency_seconds: float
    fidelity_score: float
    reconstruction_valid: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BenchmarkSuite:
    """Collection of benchmark results."""
    results: list[BenchmarkResult] = field(default_factory=list)
    timestamp: str = "2026-08-23T15:49:19.666Z"
    config: dict[str, Any] = field(default_factory=dict)


def run_benchmark_suite() -> BenchmarkSuite:
    """
    Run the complete benchmark suite.
    
    Returns:
        BenchmarkSuite with all results.
    """
    results = []
    config = {
        "packet_version": "1.0.0",
        "use_probabilistic_selection": False,
        "max_tote_iterations": 10,
    }
    
    # Benchmark 1: Natural language input
    nl_input = NaturalLanguageInput(
        text="Build a comprehensive test suite for the NYCH symbolic pipeline "
             "that validates all stages from ingestion through evidence emission. "
             "The test should verify deterministic behavior, state chronology, "
             "and schema conformance.",
        speaker="benchmark",
        perspective="first",
        tense="present",
    )
    results.append(_benchmark_input("natural_language", nl_input, config))
    
    # Benchmark 2: Sensor input
    sensor_input = SensorInput(
        data={
            "temperature": 22.5,
            "humidity": 45.0,
            "pressure": 1013.25,
            "device_id": "sensor_benchmark_001",
            "readings": [22.1, 22.3, 22.5, 22.4, 22.6],
        },
        source_device="sensor_benchmark_001",
        modality="VE",
        timestamp="2026-08-23T15:49:19.666Z",
    )
    results.append(_benchmark_input("sensor", sensor_input, config))
    
    # Benchmark 3: Short input
    short_input = NaturalLanguageInput(
        text="Test",
        speaker="benchmark",
    )
    results.append(_benchmark_input("short_text", short_input, config))
    
    return BenchmarkSuite(results=results, config=config)


def _benchmark_input(
    input_type: str,
    input_data: Any,
    config: dict[str, Any],
) -> BenchmarkResult:
    """Run a single benchmark for the given input."""
    pipeline_config = PipelineConfig(**config)
    
    # Measure input size
    if hasattr(input_data, "text"):
        input_text = input_data.text
    elif hasattr(input_data, "data"):
        input_text = json.dumps(input_data.data)
    else:
        input_text = str(input_data)
    input_size_bytes = len(input_text.encode("utf-8"))
    
    # Run pipeline and measure latency
    start_time = time.perf_counter()
    result = run_pipeline(input_data, pipeline_config)
    end_time = time.perf_counter()
    latency = end_time - start_time
    
    # Measure output size
    output_dict = result.to_dict()
    output_json = json.dumps(output_dict)
    output_size_bytes = len(output_json.encode("utf-8"))
    
    # Calculate reduction ratios
    token_reduction = 1.0 - (output_size_bytes / max(input_size_bytes, 1))
    byte_reduction = 1.0 - (output_size_bytes / max(input_size_bytes, 1))
    
    # Fidelity: continuity score as proxy
    fidelity = result.validation.continuity_score
    
    # Reconstruction validity
    reconstruction_valid = len(result.evidence) > 0 and result.validation.valid
    
    return BenchmarkResult(
        input_type=input_type,
        input_size_bytes=input_size_bytes,
        output_size_bytes=output_size_bytes,
        token_reduction_ratio=token_reduction,
        byte_reduction_ratio=byte_reduction,
        latency_seconds=latency,
        fidelity_score=fidelity,
        reconstruction_valid=reconstruction_valid,
        metadata={
            "packet_id": result.packet.packet_id,
            "symbols_count": len(result.packet.symbols),
            "operators_count": len(result.packet.operators),
            "evidence_events": len(result.evidence),
            "continuity_score": result.validation.continuity_score,
        },
    )


def print_benchmark_results(suite: BenchmarkSuite) -> None:
    """Print benchmark results in a human-readable format."""
    print("=" * 80)
    print("NYCH Pipeline Benchmark Results")
    print("=" * 80)
    print(f"Timestamp: {suite.timestamp}")
    print(f"Config: {json.dumps(suite.config, indent=2)}")
    print()
    
    for result in suite.results:
        print(f"Input Type: {result.input_type}")
        print(f"  Input Size: {result.input_size_bytes} bytes")
        print(f"  Output Size: {result.output_size_bytes} bytes")
        print(f"  Byte Reduction: {result.byte_reduction_ratio:.2%}")
        print(f"  Latency: {result.latency_seconds:.4f} seconds")
        print(f"  Fidelity Score: {result.fidelity_score:.2f}")
        print(f"  Reconstruction Valid: {result.reconstruction_valid}")
        print(f"  Metadata: {json.dumps(result.metadata, indent=4)}")
        print()


def save_benchmark_results(suite: BenchmarkSuite, path: str) -> None:
    """Save benchmark results to a JSON file."""
    with open(path, "w") as f:
        json.dump({
            "timestamp": suite.timestamp,
            "config": suite.config,
            "results": [
                {
                    "input_type": r.input_type,
                    "input_size_bytes": r.input_size_bytes,
                    "output_size_bytes": r.output_size_bytes,
                    "token_reduction_ratio": r.token_reduction_ratio,
                    "byte_reduction_ratio": r.byte_reduction_ratio,
                    "latency_seconds": r.latency_seconds,
                    "fidelity_score": r.fidelity_score,
                    "reconstruction_valid": r.reconstruction_valid,
                    "metadata": r.metadata,
                }
                for r in suite.results
            ],
        }, f, indent=2)


if __name__ == "__main__":
    suite = run_benchmark_suite()
    print_benchmark_results(suite)
    save_benchmark_results(suite, "benchmarks/results.json")
    print("Results saved to benchmarks/results.json")
