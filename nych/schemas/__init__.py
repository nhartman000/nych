"""
NYCH Schema Adapters/Validators
================================
Canonical schema adapters and validators for QSON, GST, G8SON, and MG8.
"""

from __future__ import annotations

from typing import Any

from nych.exceptions import SchemaValidationError


class SchemaValidator:
    """Base class for schema validators."""
    
    def validate(self, data: dict[str, Any]) -> bool:
        """Validate data against schema. Returns True if valid."""
        raise NotImplementedError
    
    def to_canonical(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert data to canonical form."""
        raise NotImplementedError
