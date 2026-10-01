"""
NYCH Schema Tests
=================
Tests for canonical schema adapters and validators.
"""

from __future__ import annotations

import pytest

from nych.exceptions import SchemaValidationError
from nych.schemas.g8son import G8SONValidator, validate_g8son
from nych.schemas.gst import GSTValidator, validate_gst
from nych.schemas.mg8 import MG8Validator, validate_mg8
from nych.schemas.qson import QSONValidator, validate_qson


class TestQSONValidator:
    """Tests for QSON schema validation."""

    def test_valid_qson(self) -> None:
        """Test valid QSON data."""
        data = {
            "events": [
                {
                    "event_id": "evt123",
                    "event_type": "ingest",
                    "actor": "pipeline",
                    "sequence": 0,
                    "timestamp": "2026-08-23T15:49:19.666Z",
                    "payload": {},
                    "validation": {"valid": True},
                },
            ],
        }
        assert validate_qson(data) is True

    def test_qson_missing_events_raises(self) -> None:
        """Test that missing events field raises error."""
        with pytest.raises(SchemaValidationError, match="missing required 'events' field"):
            validate_qson({})

    def test_qson_invalid_event_type_raises(self) -> None:
        """Test that invalid event type raises error."""
        data = {
            "events": [
                {
                    "event_id": "evt123",
                    "event_type": "invalid_type",
                    "actor": "pipeline",
                    "sequence": 0,
                    "timestamp": "2026-08-23T15:49:19.666Z",
                    "payload": {},
                    "validation": {"valid": True},
                },
            ],
        }
        with pytest.raises(SchemaValidationError, match="invalid event_type"):
            validate_qson(data)

    def test_qson_to_canonical_adds_missing_fields(self) -> None:
        """Test that to_canonical adds missing fields."""
        data = {"events": []}
        result = QSONValidator().to_canonical(data)
        assert result["events"] == []


class TestGSTValidator:
    """Tests for GST schema validation."""

    def test_valid_gst(self) -> None:
        """Test valid GST data."""
        data = {
            "state": {
                "prior": {"old": "data"},
                "current": {"new": "data"},
                "internal_prior": None,
                "internal_current": None,
                "external_prior": None,
                "external_current": None,
                "continuity_reference": "0,0",
            },
        }
        assert validate_gst(data) is True

    def test_gst_missing_state_raises(self) -> None:
        """Test that missing state field raises error."""
        with pytest.raises(SchemaValidationError, match="missing required 'state' field"):
            validate_gst({})

    def test_gst_missing_prior_and_current_raises(self) -> None:
        """Test that missing both prior and current raises error."""
        with pytest.raises(SchemaValidationError, match="must have at least 'prior' or 'current'"):
            validate_gst({"state": {}})

    def test_gst_to_canonical_adds_defaults(self) -> None:
        """Test that to_canonical adds default fields."""
        data = {"state": {"prior": None, "current": {"key": "value"}}}
        result = GSTValidator().to_canonical(data)
        assert result["state"]["internal_prior"] is None
        assert result["state"]["continuity_reference"] is None


class TestG8SONValidator:
    """Tests for G8SON schema validation."""

    def test_valid_g8son(self) -> None:
        """Test valid G8SON data."""
        data = {
            "gates": [
                {
                    "gate_id": "gate1",
                    "gate_type": "domain",
                    "transform_id": "transform1",
                    "passed": True,
                    "reason": "domain_match",
                    "metadata": {},
                },
            ],
        }
        assert validate_g8son(data) is True

    def test_g8son_missing_gates_raises(self) -> None:
        """Test that missing gates field raises error."""
        with pytest.raises(SchemaValidationError, match="missing required 'gates' field"):
            validate_g8son({})

    def test_g8son_invalid_gate_type_raises(self) -> None:
        """Test that invalid gate type raises error."""
        data = {
            "gates": [
                {
                    "gate_id": "gate1",
                    "gate_type": "invalid_type",
                    "transform_id": "transform1",
                    "passed": True,
                },
            ],
        }
        with pytest.raises(SchemaValidationError, match="invalid gate_type"):
            validate_g8son(data)

    def test_g8son_to_canonical_adds_defaults(self) -> None:
        """Test that to_canonical adds default fields."""
        data = {"gates": [{"gate_id": "g1", "gate_type": "domain", "transform_id": "t1", "passed": True}]}
        result = G8SONValidator().to_canonical(data)
        assert result["gates"][0]["reason"] == ""
        assert result["gates"][0]["metadata"] == {}


class TestMG8Validator:
    """Tests for MG8 schema validation."""

    def test_valid_mg8(self) -> None:
        """Test valid MG8 data."""
        data = {
            "orchestration": {"pipeline_id": "pipeline1", "run_id": "run1"},
            "state": {"gst_ref": "gst1", "nych_ref": "nych1"},
            "gates": [{"g8son_ref": "g8son1", "result": True}],
            "evidence": [{"qson_ref": "qson1", "event_type": "ingest"}],
        }
        assert validate_mg8(data) is True

    def test_mg8_missing_section_raises(self) -> None:
        """Test that missing required section raises error."""
        with pytest.raises(SchemaValidationError, match="missing required section: orchestration"):
            validate_mg8({"state": {}, "gates": [], "evidence": []})

    def test_mg8_to_canonical_adds_defaults(self) -> None:
        """Test that to_canonical adds default sections."""
        data = {}
        result = MG8Validator().to_canonical(data)
        assert "orchestration" in result
        assert "state" in result
        assert result["gates"] == []
        assert result["evidence"] == []
