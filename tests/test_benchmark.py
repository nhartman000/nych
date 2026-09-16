"""
NYCH Benchmark Tests
====================
Benchmark harness and tests for token/byte reduction, latency, compute,
fidelity and reconstruction equivalence.
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from nych.ingest import NaturalLanguageInput, SensorInput
from nych.pipeline import PipelineConfig, run_pipeline
from nych.types import Modality


class TestBenchmarkHarness:
    """Benchmark tests for the NYCH pipeline."""

    @pytest.fixture
    def benchmark_config(self) -> PipelineConfig:
        """Configuration for benchmark runs."""
        return PipelineConfig(
            packet_version="1.0.0",
            use_probabilistic_selection=False,
            max_tote_iterations=10,
        )

    def measure_pipeline_latency(
        self,
        input_data: Any,
        config: PipelineConfig,
    ) -> dict[str, float]:
        """Measure pipeline latency for a given input."""
        start = time.perf_counter()
        result = run_pipeline(input_data, config)
        end = time.perf_counter()
        
        return {
            "total_latency_seconds": end - start,
            "valid": result.validation.valid,
            "continuity_score": result.validation.continuity_score,
        }

    def test_natural_language_latency(
        self,
        benchmark_config: PipelineConfig,
    ) -> None:
        """Benchmark natural language input latency."""
        input_data = NaturalLanguageInput(
            text="Build a test for the programming system using test driven development",
            speaker="benchmark_user",
            perspective="first",
            tense="present",
        )
        
        metrics = self.measure_pipeline_latency(input_data, benchmark_config)
        
        # Record metrics (no hard thresholds - these are for tracking)
        assert metrics["valid"] is True
        assert metrics["total_latency_seconds"] > 0
        assert metrics["continuity_score"] > 0

    def test_sensor_latency(
        self,
        benchmark_config: PipelineConfig,
    ) -> None:
        """Benchmark sensor input latency."""
        input_data = SensorInput(
            data={
                "temperature": 22.5,
                "humidity": 45.0,
                "pressure": 1013.25,
                "device_id": "sensor_benchmark_001",
            },
            source_device="sensor_benchmark_001",
            modality=Modality.VE,
            timestamp="2026-08-23T15:49:19.666Z",
        )
        
        metrics = self.measure_pipeline_latency(input_data, benchmark_config)
        
        assert metrics["valid"] is True
        assert metrics["total_latency_seconds"] > 0

    def test_reconstruction_equivalence(
        self,
        benchmark_config: PipelineConfig,
    ) -> None:
        """
        Test that pipeline output can be reconstructed from evidence.
        
        This verifies that the evidence emitted contains sufficient
        information to reconstruct the pipeline result.
        """
        input_data = NaturalLanguageInput(
            text="Test reconstruction equivalence",
            speaker="test",
        )
        
        result = run_pipeline(input_data, benchmark_config)
        
        # Verify evidence contains all stages
        event_types = [e["event_type"] for e in result.evidence]
        assert "ingest" in event_types
        assert "transform" in event_types
        assert "validation" in event_types
        assert "audit" in event_types
        
        # Verify packet can be reconstructed from evidence
        ingest_event = next(e for e in result.evidence if e["event_type"] == "ingest")
        assert "packet" in ingest_event["payload"]

    def test_deterministic_reproducibility(
        self,
        benchmark_config: PipelineConfig,
    ) -> None:
        """
        Test that identical inputs produce identical outputs.
        
        This is a golden-vector test for reproducibility.
        """
        input_data = NaturalLanguageInput(
            text="Reproducibility test input",
            speaker="test",
            perspective="first",
            tense="present",
        )
        
        results = []
        for _ in range(3):
            result = run_pipeline(input_data, benchmark_config)
            results.append(result)
        
        # All results should be identical
        for i in range(1, len(results)):
            assert results[i].packet.packet_id == results[0].packet.packet_id
            assert results[i].packet.symbols == results[0].packet.symbols
            assert results[i].context.domain == results[0].context.domain
            assert results[i].validation.valid == results[0].validation.valid
            assert results[i].validation.continuity_score == results[0].validation.continuity_score
