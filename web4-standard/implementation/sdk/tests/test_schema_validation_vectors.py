"""
M1: Cross-language schema validation vectors exercised via pytest.

Loads all 278 validation vectors from web4-standard/test-vectors/schema-validation/
and validates them against JSON Schemas using the SDK's web4.validation module.

- Valid documents (92) MUST pass schema validation.
- Invalid documents (186) MUST fail schema validation.

These vectors are the PRIMARY cross-language interoperability artifact: Go, TypeScript,
and Rust implementations use the same vectors to validate their serialization output.
Running them in CI catches schema/code drift automatically.

Vector files (9 schemas, 278 total vectors):
  lct (23), attestation-envelope (20), r7-action (20), atp (23), acp (36),
  t3v3 (38), entity (32), capability (36), dictionary (50)
"""

import json
import os
from typing import Any, Dict, List, Tuple

import pytest

from web4.validation import validate

# ── Vector loading ─────────────────────────────────────────────

VECTORS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "test-vectors", "schema-validation"
)

# Map vector filename stem to SDK schema name (as accepted by validate()).
_VECTOR_STEM_TO_SCHEMA: Dict[str, str] = {
    "lct-jsonld-validation": "lct",
    "attestation-envelope-jsonld-validation": "attestation-envelope",
    "t3v3-jsonld-validation": "t3v3",
    "atp-jsonld-validation": "atp",
    "acp-jsonld-validation": "acp",
    "entity-jsonld-validation": "entity",
    "capability-jsonld-validation": "capability",
    "dictionary-jsonld-validation": "dictionary",
    "r7-action-jsonld-validation": "r7-action",
}


def _load_all_vectors() -> (
    Tuple[List[Tuple[str, str, Dict[str, Any]]], List[Tuple[str, str, Dict[str, Any]]]]
):
    """Load all valid and invalid vectors from the schema-validation directory.

    Returns:
        (valid_cases, invalid_cases) where each case is
        (vector_id, schema_name, document).
    """
    valid_cases: List[Tuple[str, str, Dict[str, Any]]] = []
    invalid_cases: List[Tuple[str, str, Dict[str, Any]]] = []

    for filename, schema_name in sorted(_VECTOR_STEM_TO_SCHEMA.items()):
        path = os.path.join(VECTORS_DIR, f"{filename}.json")
        if not os.path.exists(path):
            continue

        with open(path) as f:
            data = json.load(f)

        for vec in data.get("valid", []):
            valid_cases.append((vec["id"], schema_name, vec["document"]))

        for vec in data.get("invalid", []):
            invalid_cases.append((vec["id"], schema_name, vec["document"]))

    return valid_cases, invalid_cases


VALID_CASES, INVALID_CASES = _load_all_vectors()

VALID_IDS = [c[0] for c in VALID_CASES]
INVALID_IDS = [c[0] for c in INVALID_CASES]


# ── Tests ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "vector_id,schema_name,document", VALID_CASES, ids=VALID_IDS
)
def test_valid_vector_passes_schema(
    vector_id: str, schema_name: str, document: Dict[str, Any]
) -> None:
    """Valid cross-language vectors MUST pass schema validation."""
    result = validate(document, schema_name)
    assert result.valid, (
        f"Vector {vector_id} should be valid for schema {schema_name!r} "
        f"but got errors: {result.errors}"
    )


@pytest.mark.parametrize(
    "vector_id,schema_name,document", INVALID_CASES, ids=INVALID_IDS
)
def test_invalid_vector_fails_schema(
    vector_id: str, schema_name: str, document: Dict[str, Any]
) -> None:
    """Invalid cross-language vectors MUST fail schema validation."""
    result = validate(document, schema_name)
    assert not result.valid, (
        f"Vector {vector_id} should be INVALID for schema {schema_name!r} "
        f"but validation passed (expected schema violation)"
    )


# ── Summary test ───────────────────────────────────────────────


class TestVectorCoverage:
    """Verify all expected vectors were loaded."""

    def test_valid_count(self) -> None:
        assert len(VALID_CASES) == 92, (
            f"Expected 92 valid vectors, got {len(VALID_CASES)}"
        )

    def test_invalid_count(self) -> None:
        assert len(INVALID_CASES) == 186, (
            f"Expected 186 invalid vectors, got {len(INVALID_CASES)}"
        )

    def test_total_count(self) -> None:
        total = len(VALID_CASES) + len(INVALID_CASES)
        assert total == 278, f"Expected 278 total vectors, got {total}"

    def test_all_schemas_covered(self) -> None:
        schemas_with_valid = {c[1] for c in VALID_CASES}
        schemas_with_invalid = {c[1] for c in INVALID_CASES}
        expected = set(_VECTOR_STEM_TO_SCHEMA.values())
        assert schemas_with_valid == expected, (
            f"Missing valid vectors for: {expected - schemas_with_valid}"
        )
        assert schemas_with_invalid == expected, (
            f"Missing invalid vectors for: {expected - schemas_with_invalid}"
        )
