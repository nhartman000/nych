"""
G8SON Schema Adapter/Validator
===============================
G8SON should represent gates/constraints applied to candidate transforms.
"""

from __future__ import annotations

from typing import Any

from nych.exceptions import SchemaValidationError
from nych.schemas import SchemaValidator


# G8SON canonical schema definition
_G8SON_SCHEMA = {
    "type": "object",
    "required": ["gates"],
    "properties": {
        "gates": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["gate_id", "gate_type", "transform_id", "passed"],
                "properties": {
                    "gate_id": {"type": "string"},
                    "gate_type": {"type": "string", "enum": ["domain", "competency", "policy", "state", "admissibility"]},
                    "transform_id": {"type": "string"},
                    "passed": {"type": "boolean"},
                    "reason": {"type": "string"},
                    "metadata": {"type": "object"},
                },
            },
        },
    },
}


class G8SONValidator(SchemaValidator):
    """Validator for G8SON (Gate/Constraint Stream Object Notation) format."""
    
    def validate(self, data: dict[str, Any]) -> bool:
        """Validate G8SON data against canonical schema."""
        if not isinstance(data, dict):
            raise SchemaValidationError("G8SON data must be a dictionary")
        
        if "gates" not in data:
            raise SchemaValidationError("G8SON data missing required 'gates' field")
        
        if not isinstance(data["gates"], list):
            raise SchemaValidationError("G8SON 'gates' must be a list")
        
        valid_gate_types = {"domain", "competency", "policy", "state", "admissibility"}
        
        for i, gate in enumerate(data["gates"]):
            if not isinstance(gate, dict):
                raise SchemaValidationError(f"Gate {i} must be a dictionary")
            
            required_fields = ["gate_id", "gate_type", "transform_id", "passed"]
            for field in required_fields:
                if field not in gate:
                    raise SchemaValidationError(f"Gate {i} missing required field: {field}")
            
            if gate["gate_type"] not in valid_gate_types:
                raise SchemaValidationError(f"Gate {i} has invalid gate_type: {gate['gate_type']}")
            
            if not isinstance(gate["passed"], bool):
                raise SchemaValidationError(f"Gate {i} 'passed' must be a boolean")
        
        return True
    
    def to_canonical(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert to canonical G8SON format."""
        if "gates" not in data:
            data["gates"] = []
        
        for gate in data["gates"]:
            gate.setdefault("reason", "")
            gate.setdefault("metadata", {})
        
        return data


def validate_g8son(data: dict[str, Any]) -> bool:
    """Validate G8SON data. Returns True if valid."""
    validator = G8SONValidator()
    return validator.validate(data)


def to_canonical_g8son(data: dict[str, Any]) -> dict[str, Any]:
    """Convert data to canonical G8SON format."""
    validator = G8SONValidator()
    return validator.to_canonical(data)
