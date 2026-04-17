"""Tests for the web4.generate module and ``web4 generate`` CLI command."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from web4.generate import (
    UnsupportedTypeError,
    available_types,
    generate,
    generate_string,
)

# ═══════════════════════════════════════════════════════════════════
# 1. Module API tests
# ═══════════════════════════════════════════════════════════════════


def test_available_types_returns_sorted_list() -> None:
    types = available_types()
    assert isinstance(types, list)
    assert types == sorted(types)
    assert len(types) == 23


def test_available_types_contains_expected() -> None:
    types = available_types()
    _expected = {"T3Tensor", "V3Tensor", "R7Action", "LCT" if "LCT" in types else "LinkedContextToken"}
    # Check key types are present
    assert "T3Tensor" in types
    assert "V3Tensor" in types
    assert "R7Action" in types
    assert "LinkedContextToken" in types
    assert "AttestationEnvelope" in types
    assert "TrustQuery" in types


@pytest.mark.parametrize("type_name", available_types(), ids=available_types())
def test_generate_produces_valid_dict(type_name: str) -> None:
    """Every supported type produces a non-empty dict with @type."""
    doc = generate(type_name)
    assert isinstance(doc, dict)
    assert len(doc) > 0
    assert "@type" in doc, f"{type_name}: generated doc missing @type"


@pytest.mark.parametrize("type_name", available_types(), ids=available_types())
def test_generate_produces_json_serializable_output(type_name: str) -> None:
    """Every generated document can be serialized to JSON."""
    doc = generate(type_name)
    s = json.dumps(doc)
    assert isinstance(s, str)
    assert len(s) > 2  # not just "{}"


@pytest.mark.parametrize("type_name", available_types(), ids=available_types())
def test_generate_roundtrips_through_dispatcher(type_name: str) -> None:
    """Every generated document can be deserialized by from_jsonld()."""
    from web4.deserialize import from_jsonld

    doc = generate(type_name)
    obj = from_jsonld(doc)
    assert obj is not None


def test_generate_with_web4_prefix() -> None:
    """The web4: prefix is stripped before lookup."""
    doc = generate("web4:T3Tensor")
    assert doc["@type"] == "T3Tensor"


def test_generate_unsupported_type_raises() -> None:
    with pytest.raises(UnsupportedTypeError) as exc_info:
        generate("NonexistentType")
    assert "NonexistentType" in str(exc_info.value)


def test_generate_unsupported_type_with_prefix_raises() -> None:
    with pytest.raises(UnsupportedTypeError):
        generate("web4:FakeType")


def test_generate_string_returns_json() -> None:
    s = generate_string("T3Tensor")
    doc = json.loads(s)
    assert doc["@type"] == "T3Tensor"


def test_generate_string_indent() -> None:
    s = generate_string("V3Tensor", indent=4)
    assert "\n    " in s  # 4-space indent


def test_generate_string_compact() -> None:
    s = generate_string("V3Tensor", indent=0)
    # indent=0 still produces newlines but no spaces
    assert isinstance(s, str)


# ═══════════════════════════════════════════════════════════════════
# 2. Schema validation (generated docs match their JSON Schemas)
# ═══════════════════════════════════════════════════════════════════

# Map generate type -> schema name (only types with schemas)
# Note: TrustQuery excluded — trust-query.schema.json validates to_dict()
# format (no @context/@type), but generate() produces to_jsonld() for
# dispatcher compatibility. TrustQuery schema validation is covered in
# test_trust.py via to_dict().
_TYPE_TO_SCHEMA = {
    "T3Tensor": "t3v3",
    "V3Tensor": "t3v3",
    "ATPAccount": "atp",
    "TransferResult": "atp",
    "AttestationEnvelope": "attestation-envelope",
    "AgentPlan": "acp",
    "Intent": "acp",
    "Decision": "acp",
    "ExecutionRecord": "acp",
    "EntityTypeInfo": "entity",
    "EntityTypeRegistry": "entity",
    "LevelRequirement": "capability",
    "CapabilityAssessment": "capability",
    "CapabilityFramework": "capability",
    "DictionarySpec": "dictionary",
    "TranslationResult": "dictionary",
    "TranslationChain": "dictionary",
    "DictionaryEntity": "dictionary",
    "R7Action": "r7-action",
}


@pytest.mark.parametrize(
    "type_name,schema_name",
    list(_TYPE_TO_SCHEMA.items()),
    ids=list(_TYPE_TO_SCHEMA.keys()),
)
def test_generated_doc_validates_against_schema(type_name: str, schema_name: str) -> None:
    """Generated documents pass schema validation."""
    try:
        from web4.validation import validate
    except Exception:
        pytest.skip("jsonschema not installed")

    doc = generate(type_name)
    result = validate(doc, schema_name)
    assert result.valid, f"{type_name} generated doc failed {schema_name} schema: {result.errors}"


# ═══════════════════════════════════════════════════════════════════
# 3. CLI integration tests
# ═══════════════════════════════════════════════════════════════════


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "web4", "generate", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_cli_generate_t3() -> None:
    r = _run_cli("T3Tensor")
    assert r.returncode == 0
    doc = json.loads(r.stdout)
    assert doc["@type"] == "T3Tensor"


def test_cli_generate_compact() -> None:
    r = _run_cli("V3Tensor", "--compact")
    assert r.returncode == 0
    assert "\n" not in r.stdout.strip()  # single line


def test_cli_generate_list() -> None:
    r = _run_cli("--list")
    assert r.returncode == 0
    lines = r.stdout.strip().split("\n")
    assert len(lines) == 23
    assert "T3Tensor" in lines


def test_cli_generate_unknown_type() -> None:
    r = _run_cli("BadType")
    assert r.returncode == 1
    assert "unknown type" in r.stderr.lower() or "BadType" in r.stderr


def test_cli_generate_no_args() -> None:
    r = _run_cli()
    assert r.returncode == 1


def test_cli_generate_with_prefix() -> None:
    r = _run_cli("web4:R7Action")
    assert r.returncode == 0
    doc = json.loads(r.stdout)
    assert doc["@type"] == "R7Action"
