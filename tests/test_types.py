"""
NYCH Types Tests
================
Unit tests for NYCH typed interfaces.
"""

from __future__ import annotations

import pytest

from nych.types import (
    AuditUnit,
    CandidateTransform,
    Modality,
    NychContext,
    NychPacket,
    NychState,
    Perspective,
    SourceType,
    Tense,
    ValidationResult,
)


class TestNychPacket:
    """Tests for NychPacket type."""

    def test_create_packet(self) -> None:
        """Test creating a valid NychPacket."""
        packet = NychPacket(
            packet_id="test123",
            version="1.0.0",
            source_type=SourceType.NATURAL_LANGUAGE,
        )
        assert packet.packet_id == "test123"
        assert packet.version == "1.0.0"
        assert packet.source_type == SourceType.NATURAL_LANGUAGE
        assert packet.symbols == []
        assert packet.operators == []
        assert packet.numeric_values == []
        assert packet.metadata_refs == {}

    def test_packet_empty_id_raises(self) -> None:
        """Test that empty packet_id raises ValueError."""
        with pytest.raises(ValueError, match="packet_id must be non-empty"):
            NychPacket(
                packet_id="",
                version="1.0.0",
                source_type=SourceType.NATURAL_LANGUAGE,
            )

    def test_packet_empty_version_raises(self) -> None:
        """Test that empty version raises ValueError."""
        with pytest.raises(ValueError, match="version must be non-empty"):
            NychPacket(
                packet_id="test123",
                version="",
                source_type=SourceType.NATURAL_LANGUAGE,
            )

    def test_packet_to_dict(self) -> None:
        """Test packet serialization to dict."""
        packet = NychPacket(
            packet_id="test123",
            version="1.0.0",
            source_type=SourceType.SENSOR,
            symbols=["💻"],
            operators=["Test"],
            numeric_values=[42.0],
            metadata_refs={"key": "value"},
        )
        data = packet.to_dict()
        assert data["packet_id"] == "test123"
        assert data["source_type"] == "sensor"
        assert data["symbols"] == ["💻"]
        assert data["operators"] == ["Test"]
        assert data["numeric_values"] == [42.0]
        assert data["metadata_refs"] == {"key": "value"}

    def test_packet_from_dict(self) -> None:
        """Test packet deserialization from dict."""
        data = {
            "packet_id": "test123",
            "version": "1.0.0",
            "source_type": "sensor",
            "symbols": ["💻"],
            "operators": ["Test"],
            "numeric_values": [42.0],
            "metadata_refs": {"key": "value"},
        }
        packet = NychPacket.from_dict(data)
        assert packet.packet_id == "test123"
        assert packet.source_type == SourceType.SENSOR
        assert packet.symbols == ["💻"]


class TestNychContext:
    """Tests for NychContext type."""

    def test_create_context(self) -> None:
        """Test creating a valid NychContext."""
        context = NychContext(
            domain="programming",
            subject="test_subject",
            intent="test",
            competency="developer",
        )
        assert context.domain == "programming"
        assert context.subject == "test_subject"
        assert context.intent == "test"
        assert context.competency == "developer"

    def test_context_empty_domain_raises(self) -> None:
        """Test that empty domain raises ValueError."""
        with pytest.raises(ValueError, match="domain must be non-empty"):
            NychContext(
                domain="",
                subject="test",
                intent="test",
                competency="dev",
            )

    def test_context_to_dict(self) -> None:
        """Test context serialization."""
        context = NychContext(
            domain="programming",
            subject="test",
            intent="test",
            competency="dev",
            modality=Modality.VE,
            perspective=Perspective.FIRST,
            tense=Tense.PRESENT,
        )
        data = context.to_dict()
        assert data["domain"] == "programming"
        assert data["modality"] == "VE"
        assert data["perspective"] == "first"
        assert data["tense"] == "present"


class TestNychState:
    """Tests for NychState type."""

    def test_create_state(self) -> None:
        """Test creating a valid NychState."""
        state = NychState(
            current={"key": "value"},
            continuity_reference="0,0",
        )
        assert state.current == {"key": "value"}
        assert state.continuity_reference == "0,0"

    def test_state_advance(self) -> None:
        """Test state chronology advancement."""
        state = NychState(
            prior={"old": "data"},
            current={"current": "data"},
            continuity_reference="0,0",
        )
        new_state = state.advance({"new": "data"})
        
        assert new_state.prior == {"current": "data"}
        assert new_state.current == {"new": "data"}

    def test_state_no_current_or_prior_raises(self) -> None:
        """Test that state with no current or prior raises ValueError."""
        with pytest.raises(ValueError, match="At least one of current or prior must be set"):
            NychState()


class TestValidationResult:
    """Tests for ValidationResult type."""

    def test_valid_result(self) -> None:
        """Test creating a valid validation result."""
        result = ValidationResult(
            valid=True,
            reasons=[],
            anomaly_flags=[],
            continuity_score=1.0,
            closure_state="closed",
        )
        assert result.valid is True
        assert result.continuity_score == 1.0
        assert result.closure_state == "closed"

    def test_invalid_result(self) -> None:
        """Test creating an invalid validation result."""
        result = ValidationResult(
            valid=False,
            reasons=["test_failed"],
            anomaly_flags=["low_continuity"],
            continuity_score=0.5,
            closure_state="open",
        )
        assert result.valid is False
        assert result.reasons == ["test_failed"]
        assert result.anomaly_flags == ["low_continuity"]


class TestAuditUnit:
    """Tests for AuditUnit type."""

    def test_create_audit_unit(self) -> None:
        """Test creating a valid audit unit."""
        audit = AuditUnit(
            unit_id="audit123",
            source_refs=["src1"],
            state_refs=["state1"],
            transform_ref="transform1",
            metrics={"latency": 0.1},
            hashes={"packet": "abc123"},
        )
        assert audit.unit_id == "audit123"
        assert audit.source_refs == ["src1"]
        assert audit.metrics == {"latency": 0.1}

    def test_audit_unit_empty_id_raises(self) -> None:
        """Test that empty unit_id raises ValueError."""
        with pytest.raises(ValueError, match="unit_id must be non-empty"):
            AuditUnit(unit_id="")
