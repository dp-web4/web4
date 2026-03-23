#!/usr/bin/env python3
"""
Cross-language schema validation test vector runner.

Validates that JSON Schema validation vectors behave correctly:
- All 'valid' documents PASS schema validation
- All 'invalid' documents FAIL schema validation

Usage:
    python validate_schema_vectors.py              # Run all
    python validate_schema_vectors.py lct          # LCT only
    python validate_schema_vectors.py attestation  # AttestationEnvelope only
    python validate_schema_vectors.py r7           # R7 Action only
    python validate_schema_vectors.py atp          # ATP/ADP only
    python validate_schema_vectors.py acp          # ACP only
    python validate_schema_vectors.py t3v3         # T3/V3 only
    python validate_schema_vectors.py --verbose    # Show details

Exit code 0 = all vectors behave correctly, 1 = unexpected results.

This script uses jsonschema (Draft 2020-12) but the vector files are
language-agnostic — any JSON Schema validator can consume them.
"""

import json
import sys
from pathlib import Path

import jsonschema
from jsonschema import Draft202012Validator

VECTORS_DIR = Path(__file__).parent
SCHEMA_DIR = VECTORS_DIR.parent.parent / "schemas"
VERBOSE = "--verbose" in sys.argv

VECTOR_FILES = {
    "lct": {
        "vectors": "lct-jsonld-validation.json",
        "schema": "lct-jsonld.schema.json",
    },
    "attestation": {
        "vectors": "attestation-envelope-jsonld-validation.json",
        "schema": "attestation-envelope-jsonld.schema.json",
    },
    "r7": {
        "vectors": "r7-action-jsonld-validation.json",
        "schema": "r7-action-jsonld.schema.json",
    },
    "atp": {
        "vectors": "atp-jsonld-validation.json",
        "schema": "atp-jsonld.schema.json",
    },
    "acp": {
        "vectors": "acp-jsonld-validation.json",
        "schema": "acp-jsonld.schema.json",
    },
    "t3v3": {
        "vectors": "t3v3-jsonld-validation.json",
        "schema": "t3v3-jsonld.schema.json",
    },
}


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def run_vectors(name: str, config: dict) -> tuple[int, int, int]:
    """Run validation vectors for one schema. Returns (passed, failed, total)."""
    schema = load_json(SCHEMA_DIR / config["schema"])
    vectors = load_json(VECTORS_DIR / config["vectors"])
    validator = Draft202012Validator(schema)

    passed = 0
    failed = 0
    total = 0

    print(f"\n=== {vectors['meta'].get('description', name)} ===\n")

    # Valid documents: MUST pass
    for vec in vectors.get("valid", []):
        total += 1
        doc = vec["document"]
        errors = list(validator.iter_errors(doc))
        if errors:
            failed += 1
            print(f"  FAIL (should pass): {vec['id']} — {vec['description']}")
            for err in errors:
                path = ".".join(str(p) for p in err.absolute_path) or "(root)"
                print(f"    - {path}: {err.message}")
        else:
            passed += 1
            if VERBOSE:
                print(f"  PASS: {vec['id']} — {vec['description']}")

    # Invalid documents: MUST fail
    for vec in vectors.get("invalid", []):
        total += 1
        doc = vec["document"]
        errors = list(validator.iter_errors(doc))
        if errors:
            passed += 1
            if VERBOSE:
                error_kinds = {e.validator for e in errors}
                print(
                    f"  PASS (correctly rejected): {vec['id']} — {vec['description']} "
                    f"[{', '.join(sorted(error_kinds))}]"
                )
        else:
            failed += 1
            print(
                f"  FAIL (should reject): {vec['id']} — {vec['description']}"
            )

    valid_count = len(vectors.get("valid", []))
    invalid_count = len(vectors.get("invalid", []))
    print(f"\n  {name}: {passed}/{total} passed ({valid_count} valid + {invalid_count} invalid vectors)")
    return passed, failed, total


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    # Determine which vector sets to run
    if args:
        targets = {a: VECTOR_FILES[a] for a in args if a in VECTOR_FILES}
        if not targets:
            print(f"Unknown target(s): {args}. Available: {list(VECTOR_FILES.keys())}")
            return 1
    else:
        targets = VECTOR_FILES

    total_passed = 0
    total_failed = 0
    total_count = 0

    for name, config in targets.items():
        p, f, t = run_vectors(name, config)
        total_passed += p
        total_failed += f
        total_count += t

    print(f"\n{'=' * 50}")
    if total_failed == 0:
        print(f"ALL {total_count} VECTORS PASSED")
    else:
        print(f"{total_failed}/{total_count} VECTORS FAILED")
    print(f"{'=' * 50}\n")

    return 1 if total_failed else 0


if __name__ == "__main__":
    sys.exit(main())
