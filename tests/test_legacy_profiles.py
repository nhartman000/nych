"""Legacy NYCH profiles are explicit and retain their historical shapes."""

import importlib

import pytest


@pytest.mark.parametrize("name,profile_id", [
    ("mg8", "nych.legacy.mg8-container.v1"),
    ("g8son", "nych.legacy.g8son-results.v1"),
    ("qson", "nych.legacy.qson-audit.v1"),
    ("gst", "nych.legacy.gst-state.v1"),
])
def test_legacy_profile_identity_and_historical_normalizer(name, profile_id):
    module = importlib.import_module(f"nych.schemas.{name}")
    assert module.PROFILE_ID == profile_id
    assert "not the dedicated canonical" in (module.__doc__ or "").lower()
    normalizer = getattr(module, f"to_canonical_{name}")
    assert "legacy" in normalizer.__doc__.lower()
    data = {}
    assert normalizer(data) is data  # historical in-place API, not a migration
    expected = {
        "mg8": {"orchestration": {}, "state": {}, "gates": [], "evidence": []},
        "g8son": {"gates": []},
        "qson": {"events": []},
        "gst": {"state": dict.fromkeys([
            "prior", "current", "internal_prior", "internal_current",
            "external_prior", "external_current", "continuity_reference",
        ])},
    }
    assert data == expected[name]
    assert getattr(module, f"validate_{name}")(data)


def test_container_and_evidence_declare_legacy_profiles():
    from nych import container, evidence
    from nych.schemas import mg8, qson

    assert container.PROFILE_ID == mg8.PROFILE_ID
    assert evidence.PROFILE_ID == qson.PROFILE_ID


def test_legacy_gate_results_are_not_dedicated_gate_conditions():
    from nych.schemas.g8son import to_canonical_g8son, validate_g8son

    data = {"gates": [{"gate_id": "g", "gate_type": "admissibility",
                       "transform_id": "t", "passed": True}]}
    assert validate_g8son(data)
    assert to_canonical_g8son(data) is data
    assert "g8son_version" not in data
    assert "file_id" not in data
    assert "conditions" not in data["gates"][0]
    assert data["gates"][0]["passed"] is True
