"""
GST Schema Adapter/Validator
=============================
GST should carry prior/current and internal/external state plus
continuity semantics.
"""

from __future__ import annotations

from typing import Any

from nych.exceptions import SchemaValidationError
from nych.schemas import SchemaValidator


# GST canonical schema definition
_GST_SCHEMA = {
    "type": "object",
    "required": ["state"],
    "properties": {
        "state": {
            "type": "object",
            "required": ["prior", "current"],
            "properties": {
                "prior": {"type": ["object", "null"]},
                "current": {"type": ["object", "null"]},
                "internal_prior": {"type": ["object", "null"]},
                "internal_current": {"type": ["object", "null"]},
                "external_prior": {"type": ["object", "null"]},
                "external_current": {"type": ["object", "null"]},
                "continuity_reference": {"type": ["string", "null"]},
            },
        },
    },
}


class GSTValidator(SchemaValidator):
    """Validator for GST (General State Transform) format."""
    
    def validate(self, data: dict[str, Any]) -> bool:
        """Validate GST data against canonical schema."""
        if not isinstance(data, dict):
            raise SchemaValidationError("GST data must be a dictionary")
        
        if "state" not in data:
            raise SchemaValidationError("GST data missing required 'state' field")
        
        state = data["state"]
        if not isinstance(state, dict):
            raise SchemaValidationError("GST 'state' must be a dictionary")
        
        if "prior" not in state and "current" not in state:
            raise SchemaValidationError("GST state must have at least 'prior' or 'current'")
        
        return True
    
    def to_canonical(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert to canonical GST format."""
        if "state" not in data:
            data["state"] = {}
        
        state = data["state"]
        state.setdefault("prior", None)
        state.setdefault("current", None)
        state.setdefault("internal_prior", None)
        state.setdefault("internal_current", None)
        state.setdefault("external_prior", None)
        state.setdefault("external_current", None)
        state.setdefault("continuity_reference", None)
        
        return data


def validate_gst(data: dict[str, Any]) -> bool:
    """Validate GST data. Returns True if valid."""
    validator = GSTValidator()
    return validator.validate(data)


def to_canonical_gst(data: dict[str, Any]) -> dict[str, Any]:
    """Convert data to canonical GST format."""
    validator = GSTValidator()
    return validator.to_canonical(data)
