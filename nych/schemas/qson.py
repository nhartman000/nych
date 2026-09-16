"""
QSON Schema Adapter/Validator
==============================
QSON should carry canonical execution/evidence events, actors, sequence
and validation results.
"""

from __future__ import annotations

from typing import Any

from nych.exceptions import SchemaValidationError
from nych.schemas import SchemaValidator


# QSON canonical schema definition
_QSON_SCHEMA = {
    "type": "object",
    "required": ["events"],
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["event_id", "event_type", "actor", "sequence", "timestamp", "payload", "validation"],
                "properties": {
                    "event_id": {"type": "string"},
                    "event_type": {"type": "string", "enum": ["ingest", "transform", "validation", "audit"]},
                    "actor": {"type": "string"},
                    "sequence": {"type": "integer"},
                    "timestamp": {"type": "string"},
                    "payload": {"type": "object"},
                    "validation": {
                        "type": "object",
                        "required": ["valid"],
                        "properties": {
                            "valid": {"type": "boolean"},
                        },
                    },
                },
            },
        },
    },
}


class QSONValidator(SchemaValidator):
    """Validator for QSON (Query/Evidence Stream Object Notation) format."""
    
    def validate(self, data: dict[str, Any]) -> bool:
        """Validate QSON data against canonical schema."""
        if not isinstance(data, dict):
            raise SchemaValidationError("QSON data must be a dictionary")
        
        if "events" not in data:
            raise SchemaValidationError("QSON data missing required 'events' field")
        
        if not isinstance(data["events"], list):
            raise SchemaValidationError("QSON 'events' must be a list")
        
        for i, event in enumerate(data["events"]):
            if not isinstance(event, dict):
                raise SchemaValidationError(f"Event {i} must be a dictionary")
            
            required_fields = ["event_id", "event_type", "actor", "sequence", "timestamp", "payload", "validation"]
            for field in required_fields:
                if field not in event:
                    raise SchemaValidationError(f"Event {i} missing required field: {field}")
            
            if event["event_type"] not in ["ingest", "transform", "validation", "audit"]:
                raise SchemaValidationError(f"Event {i} has invalid event_type: {event['event_type']}")
            
            if not isinstance(event["sequence"], int):
                raise SchemaValidationError(f"Event {i} sequence must be an integer")
        
        return True
    
    def to_canonical(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert to canonical QSON format."""
        if "events" not in data:
            data["events"] = []
        
        # Ensure all events have required fields
        for event in data["events"]:
            event.setdefault("validation", {"valid": True})
        
        return data


def validate_qson(data: dict[str, Any]) -> bool:
    """Validate QSON data. Returns True if valid."""
    validator = QSONValidator()
    return validator.validate(data)


def to_canonical_qson(data: dict[str, Any]) -> dict[str, Any]:
    """Convert data to canonical QSON format."""
    validator = QSONValidator()
    return validator.to_canonical(data)
