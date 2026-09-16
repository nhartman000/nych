"""
Test Configuration and Fixtures
================================
Shared fixtures and configuration for NYCH pipeline tests.
"""

from __future__ import annotations

import pytest

from nych.ingest import NaturalLanguageInput, SensorInput
from nych.pipeline import PipelineConfig
from nych.types import Modality, SourceType


@pytest.fixture
def sample_natural_language_input() -> NaturalLanguageInput:
    """Sample natural language input for testing."""
    return NaturalLanguageInput(
        text="I want to build a test for the programming system",
        speaker="test_user",
        perspective="first",
        tense="present",
    )


@pytest.fixture
def sample_sensor_input() -> SensorInput:
    """Sample sensor input for testing."""
    return SensorInput(
        data={"temperature": 22.5, "humidity": 45.0, "device_id": "sensor_001"},
        source_device="sensor_001",
        modality=Modality.VE,
        timestamp="2026-08-23T15:49:19.666Z",
    )


@pytest.fixture
def default_pipeline_config() -> PipelineConfig:
    """Default pipeline configuration for testing."""
    return PipelineConfig(
        packet_version="1.0.0",
        use_probabilistic_selection=False,
        max_tote_iterations=10,
    )


@pytest.fixture
def probabilistic_pipeline_config() -> PipelineConfig:
    """Pipeline configuration with probabilistic selection."""
    return PipelineConfig(
        packet_version="1.0.0",
        use_probabilistic_selection=True,
        selection_seed=42,
        max_tote_iterations=10,
    )
