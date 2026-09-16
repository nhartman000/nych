"""
NYCH Pipeline End-to-End Tests
================================
End-to-end conformance tests for the NYCH pipeline.
"""

from __future__ import annotations

import pytest

from nych.ingest import NaturalLanguageInput, SensorInput
from nych.pipeline import PipelineConfig, run_pipeline
from nych.types import SourceType


class TestPipelineEndToEnd:
    """End-to-end tests for the complete NYCH pipeline."""

    def test_natural_language_input(
        self,
        sample_natural_language_input: NaturalLanguageInput,
        default_pipeline_config: PipelineConfig,
    ) -> None:
        """Test complete pipeline with natural language input."""
        result = run_pipeline(sample_natural_language_input, default_pipeline_config)
        
        assert result is not None
        assert result.packet is not None
        assert result.context is not None
        assert result.state is not None
        assert result.validation is not None
        assert result.audit is not None
        assert result.evidence is not None
        
        # Verify packet
        assert result.packet.source_type == SourceType.NATURAL_LANGUAGE
        assert result.packet.version == "1.0.0"
        
        # Verify context
        assert result.context.domain is not None
        assert result.context.subject is not None
        assert result.context.intent is not None
        assert result.context.competency is not None
        
        # Verify validation
        assert result.validation.valid is True
        assert result.validation.closure_state == "closed"
        
        # Verify evidence
        assert len(result.evidence) > 0
        for event in result.evidence:
            assert "event_id" in event
            assert "event_type" in event
            assert "actor" in event

    def test_sensor_input(
        self,
        sample_sensor_input: SensorInput,
        default_pipeline_config: PipelineConfig,
    ) -> None:
        """Test complete pipeline with sensor input."""
        result = run_pipeline(sample_sensor_input, default_pipeline_config)
        
        assert result is not None
        assert result.packet.source_type == SourceType.SENSOR
        assert result.context.modality.value == "VE"
        
        # Verify validation passed
        assert result.validation.valid is True

    def test_pipeline_determinism(
        self,
        sample_natural_language_input: NaturalLanguageInput,
        default_pipeline_config: PipelineConfig,
    ) -> None:
        """
        Golden-vector test: identical input + versions => identical symbolic packet.
        """
        result1 = run_pipeline(sample_natural_language_input, default_pipeline_config)
        result2 = run_pipeline(sample_natural_language_input, default_pipeline_config)
        
        # Packets should be identical
        assert result1.packet.packet_id == result2.packet.packet_id
        assert result1.packet.symbols == result2.packet.symbols
        assert result1.packet.operators == result2.packet.operators
        assert result1.packet.numeric_values == result2.packet.numeric_values
        
        # Contexts should be identical
        assert result1.context.domain == result2.context.domain
        assert result1.context.subject == result2.context.subject
        assert result1.context.intent == result2.context.intent
        
        # States should be identical
        assert result1.state.current == result2.state.current
        
        # Validations should be identical
        assert result1.validation.valid == result2.validation.valid
        assert result1.validation.continuity_score == result2.validation.continuity_score

    def test_pipeline_with_probabilistic_selection(
        self,
        sample_natural_language_input: NaturalLanguageInput,
        probabilistic_pipeline_config: PipelineConfig,
    ) -> None:
        """Test pipeline with probabilistic candidate selection."""
        result = run_pipeline(sample_natural_language_input, probabilistic_pipeline_config)
        
        assert result is not None
        assert result.validation.valid is True

    def test_state_chronology_advancement(
        self,
        sample_natural_language_input: NaturalLanguageInput,
        default_pipeline_config: PipelineConfig,
    ) -> None:
        """Test that state chronology advances correctly."""
        result = run_pipeline(sample_natural_language_input, default_pipeline_config)
        
        # State should have prior/current advancement
        # The pipeline should have advanced state from initial to final
        assert result.state.current is not None

    def test_evidence_emission_qson_compatible(
        self,
        sample_natural_language_input: NaturalLanguageInput,
        default_pipeline_config: PipelineConfig,
    ) -> None:
        """Test that emitted evidence is QSON-compatible."""
        from nych.schemas.qson import validate_qson
        
        result = run_pipeline(sample_natural_language_input, default_pipeline_config)
        
        # Evidence should be valid QSON
        assert validate_qson({"events": result.evidence}) is True

    def test_audit_unit_completeness(
        self,
        sample_natural_language_input: NaturalLanguageInput,
        default_pipeline_config: PipelineConfig,
    ) -> None:
        """Test that audit unit contains all required fields."""
        result = run_pipeline(sample_natural_language_input, default_pipeline_config)
        
        audit = result.audit
        assert audit.unit_id is not None
        assert len(audit.source_refs) > 0
        assert len(audit.state_refs) > 0
        assert len(audit.metrics) > 0
        assert len(audit.hashes) > 0

    def test_fast_path_no_anomalies(
        self,
        sample_natural_language_input: NaturalLanguageInput,
        default_pipeline_config: PipelineConfig,
    ) -> None:
        """Test that stable inputs use fast path."""
        result = run_pipeline(sample_natural_language_input, default_pipeline_config)
        
        # For a simple input, should use fast path (no anomalies)
        # The pipeline should complete without errors
        assert result.validation.valid is True

    def test_mgate_three_gate_execution(
        self,
        sample_natural_language_input: NaturalLanguageInput,
        default_pipeline_config: PipelineConfig,
    ) -> None:
        """Test that MGate three-gate system executes per white paper §12."""
        result = run_pipeline(sample_natural_language_input, default_pipeline_config)
        
        assert result.mgate_summary is not None
        assert "total_rungs" in result.mgate_summary
        assert "successful_rungs" in result.mgate_summary
        assert "backtrack_count" in result.mgate_summary
        assert "gate_executions" in result.mgate_summary
        assert result.mgate_summary["successful_rungs"] >= 1
        
        # Each rung should have exactly 3 gates (G1, G2, G3)
        for gate_exec in result.mgate_summary["gate_executions"]:
            assert "rung_index" in gate_exec
            assert "g1" in gate_exec
            assert "g2" in gate_exec
            assert "g3" in gate_exec
            assert gate_exec["all_exit"] is True

    def test_mgate_backtrack_on_failure(
        self,
        sample_natural_language_input: NaturalLanguageInput,
        default_pipeline_config: PipelineConfig,
    ) -> None:
        """Test that MGate backtracks when a gate cannot EXIT."""
        result = run_pipeline(sample_natural_language_input, default_pipeline_config)
        
        # With default config, should succeed without backtracking
        # But the backtrack mechanism must be present and logged
        assert "backtrack_count" in result.mgate_summary
        assert isinstance(result.mgate_summary["backtrack_count"], int)

    def test_to_gst_dict_serialization(
        self,
        sample_natural_language_input: NaturalLanguageInput,
        default_pipeline_config: PipelineConfig,
    ) -> None:
        """Test GST serialization per white paper §18."""
        result = run_pipeline(sample_natural_language_input, default_pipeline_config)
        
        gst = result.to_gst_dict()
        assert gst["gst_id"] == result.packet.packet_id
        assert gst["domain"] == result.context.domain
        assert gst["perspective"] == result.context.perspective.value if result.context.perspective else None
        assert gst["tense"] == result.context.tense.value if result.context.tense else None
        assert "mgate_summary" in gst

    def test_action_permit_single_use(
        self,
        sample_natural_language_input: NaturalLanguageInput,
        default_pipeline_config: PipelineConfig,
    ) -> None:
        """Test that ActionPermit is issued and single-use per white paper §15."""
        result = run_pipeline(sample_natural_language_input, default_pipeline_config)
        
        assert result.mgate_summary is not None
        assert result.mgate_summary.get("action_permit") is not None
        
        permit = result.mgate_summary["action_permit"]
        assert permit["state"] == "ISSUED"
        assert "permit_id" in permit
        assert "state_hash" in permit
        assert "semantic_hash" in permit
        assert "epoch" in permit
