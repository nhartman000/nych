"""Distribution regressions; run against the installed wheel in clean-install CI."""

import importlib
from importlib import metadata, resources


def test_distribution_python_floor_matches_required_tcta():
    from packaging.specifiers import SpecifierSet

    nych_python = SpecifierSet(metadata.metadata("nych")["Requires-Python"])
    tcta_python = SpecifierSet(metadata.metadata("tcta-engine")["Requires-Python"])
    assert "3.10" not in tcta_python
    assert "3.10" not in nych_python
    assert "3.11" in nych_python
    assert "3.11" in tcta_python


def test_schema_and_container_modules_are_importable():
    for name in ("container", "schemas", "schemas.g8son", "schemas.gst",
                 "schemas.mg8", "schemas.qson", "plugins.vscode.extensions"):
        assert importlib.import_module(f"nych.{name}") is not None


def test_installed_seed_registry_and_dictionary_are_usable():
    from nych.protected_terms import has_dictionary_definition
    from nych.semantic_registry import load_registry

    registry = load_registry()
    assert registry["senses"]
    assert registry["gestalt_spans"]
    assert has_dictionary_definition("test")
    assert resources.files("nych").joinpath("data/DICTIONARY_LICENSE.txt").read_text(
        encoding="utf-8"
    ).strip()
