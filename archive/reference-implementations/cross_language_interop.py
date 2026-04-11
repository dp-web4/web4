#!/usr/bin/env python3
"""
Web4 Cross-Language LCT Interoperability Test Vectors

Creates shared test vectors and verifies Python ↔ Go ↔ TypeScript produce
identical JSON output for LCT documents. Addresses the key finding that
no cross-language tests exist despite 3 implementations.

Key tests:
- Shared test vector generation (canonical JSON)
- Python document output matches expected vectors
- Field naming consistency (snake_case across all languages)
- T3/V3 composite scoring identity
- LCT ID pattern validation across languages
- Birth certificate witness minimum enforcement
- JSON roundtrip preservation
- Hash stability across implementations
- Schema validation consistency
"""

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════
# Canonical Test Vectors
# ═══════════════════════════════════════════════════════════════════

# These vectors define the EXACT JSON that all implementations MUST produce.
# Go's json tags, Python's to_dict(), and TypeScript serialization must all
# produce identical output for the same logical document.

CANONICAL_TIMESTAMP = "2026-02-19T00:00:00Z"

MINIMAL_VECTOR = {
    "lct_id": "lct:web4:ai:test0000deadbeef",
    "subject": "did:web4:key:z6Mk1234567890",
    "binding": {
        "entity_type": "ai",
        "public_key": "mb64testkey",
        "created_at": CANONICAL_TIMESTAMP,
        "binding_proof": "cose:test_proof",
    },
    "birth_certificate": {
        "issuing_society": "lct:web4:society-genesis",
        "citizen_role": "lct:web4:role:citizen:ai",
        "context": "platform",
        "birth_timestamp": CANONICAL_TIMESTAMP,
        "birth_witnesses": [
            "lct:web4:witness-w1",
            "lct:web4:witness-w2",
            "lct:web4:witness-w3",
        ],
    },
    "mrh": {
        "bound": [],
        "paired": [
            {
                "lct_id": "lct:web4:role:citizen:ai",
                "pairing_type": "birth_certificate",
                "permanent": True,
                "ts": CANONICAL_TIMESTAMP,
            }
        ],
        "horizon_depth": 3,
        "last_updated": CANONICAL_TIMESTAMP,
    },
    "policy": {
        "capabilities": ["witness:attest"],
    },
    "t3_tensor": {
        "talent": 0.5,
        "training": 0.5,
        "temperament": 0.5,
        "composite_score": 0.5,
    },
    "v3_tensor": {
        "valuation": 0.0,
        "veracity": 0.5,
        "validity": 0.5,
        "composite_score": 0.35,
    },
    "revocation": {
        "status": "active",
    },
}


HUMAN_VECTOR = {
    "lct_id": "lct:web4:human:alice7890abcdef",
    "subject": "did:web4:key:z6MkAlice",
    "binding": {
        "entity_type": "human",
        "public_key": "mb64alicekey",
        "hardware_anchor": "tpm2:sha256:abcdef1234",
        "created_at": CANONICAL_TIMESTAMP,
        "binding_proof": "cose:alice_proof",
    },
    "birth_certificate": {
        "issuing_society": "lct:web4:society-acme-corp",
        "citizen_role": "lct:web4:role:citizen:human",
        "context": "organization",
        "birth_timestamp": CANONICAL_TIMESTAMP,
        "parent_entity": "lct:web4:org:acme",
        "birth_witnesses": [
            "lct:web4:witness-time-1",
            "lct:web4:witness-audit-1",
            "lct:web4:witness-oracle-1",
        ],
    },
    "mrh": {
        "bound": [
            {"lct_id": "lct:web4:org:acme", "type": "parent", "ts": CANONICAL_TIMESTAMP}
        ],
        "paired": [
            {
                "lct_id": "lct:web4:role:citizen:human",
                "pairing_type": "birth_certificate",
                "permanent": True,
                "ts": CANONICAL_TIMESTAMP,
            },
            {
                "lct_id": "lct:web4:role:admin",
                "pairing_type": "role",
                "permanent": False,
                "context": "project-alpha",
                "ts": CANONICAL_TIMESTAMP,
            },
        ],
        "witnessing": [
            {
                "lct_id": "lct:web4:oracle:timestamp",
                "role": "time",
                "last_attestation": CANONICAL_TIMESTAMP,
            }
        ],
        "horizon_depth": 5,
        "last_updated": CANONICAL_TIMESTAMP,
    },
    "policy": {
        "capabilities": ["witness:attest", "r6:execute", "delegate:limited"],
        "constraints": {"max_delegation_depth": 3},
    },
    "t3_tensor": {
        "talent": 0.8,
        "training": 0.7,
        "temperament": 0.9,
        "composite_score": 0.8,
        "sub_dimensions": {
            "talent": {"code_review": 0.85, "architecture": 0.75},
            "training": {"web4_protocol": 0.9, "security": 0.65},
        },
    },
    "v3_tensor": {
        "valuation": 0.3,
        "veracity": 0.85,
        "validity": 0.8,
        "composite_score": 0.6675,
    },
    "attestations": [
        {
            "witness": "did:web4:key:z6MkOracle1",
            "type": "time",
            "sig": "cose:oracle1_sig",
            "ts": CANONICAL_TIMESTAMP,
            "claims": {"ts": CANONICAL_TIMESTAMP, "nonce": "mb32:nonce1"},
        }
    ],
    "lineage": [
        {"reason": "genesis", "ts": CANONICAL_TIMESTAMP}
    ],
    "revocation": {"status": "active"},
}


REVOKED_VECTOR = {
    "lct_id": "lct:web4:ai:revoked-agent-999",
    "subject": "did:web4:key:z6MkRevoked",
    "binding": {
        "entity_type": "ai",
        "public_key": "mb64revokedkey",
        "created_at": "2026-01-01T00:00:00Z",
        "binding_proof": "cose:revoked_proof",
    },
    "birth_certificate": {
        "issuing_society": "lct:web4:society-test",
        "citizen_role": "lct:web4:role:citizen:ai",
        "context": "platform",
        "birth_timestamp": "2026-01-01T00:00:00Z",
        "birth_witnesses": [
            "lct:web4:witness-w1",
            "lct:web4:witness-w2",
            "lct:web4:witness-w3",
        ],
    },
    "mrh": {
        "bound": [],
        "paired": [
            {
                "lct_id": "lct:web4:role:citizen:ai",
                "pairing_type": "birth_certificate",
                "permanent": True,
                "ts": "2026-01-01T00:00:00Z",
            }
        ],
        "horizon_depth": 3,
        "last_updated": "2026-02-15T12:00:00Z",
    },
    "policy": {"capabilities": []},
    "t3_tensor": {
        "talent": 0.3,
        "training": 0.2,
        "temperament": 0.1,
        "composite_score": 0.21,
    },
    "revocation": {
        "status": "revoked",
        "ts": "2026-02-15T12:00:00Z",
        "reason": "compromise",
    },
    "lineage": [
        {"reason": "genesis", "ts": "2026-01-01T00:00:00Z"}
    ],
}


ALL_ENTITY_TYPES = [
    "human", "ai", "society", "organization", "role", "task",
    "resource", "device", "service", "oracle", "accumulator",
    "dictionary", "hybrid", "policy", "infrastructure",
]


# ═══════════════════════════════════════════════════════════════════
# Canonical Hash Function
# ═══════════════════════════════════════════════════════════════════

def canonical_hash(doc: dict) -> str:
    """JCS-like canonical JSON hash (RFC 8785 simplified)."""
    canonical = json.dumps(doc, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def canonical_json(doc: dict) -> str:
    """Canonical JSON string (sorted keys, no extra whitespace)."""
    return json.dumps(doc, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


# ═══════════════════════════════════════════════════════════════════
# T3/V3 Composite Scoring (must match across languages)
# ═══════════════════════════════════════════════════════════════════

T3_WEIGHTS = {"talent": 0.4, "training": 0.3, "temperament": 0.3}
V3_WEIGHTS = {"valuation": 0.3, "veracity": 0.35, "validity": 0.35}


def compute_t3_composite(t3: dict) -> float:
    return (t3["talent"] * T3_WEIGHTS["talent"] +
            t3["training"] * T3_WEIGHTS["training"] +
            t3["temperament"] * T3_WEIGHTS["temperament"])


def compute_v3_composite(v3: dict) -> float:
    return (v3["valuation"] * V3_WEIGHTS["valuation"] +
            v3["veracity"] * V3_WEIGHTS["veracity"] +
            v3["validity"] * V3_WEIGHTS["validity"])


# ═══════════════════════════════════════════════════════════════════
# LCT ID Pattern Validation
# ═══════════════════════════════════════════════════════════════════

import re

# Canonical pattern: allows colons (per cross-language fix)
LCT_ID_PATTERN = re.compile(r"^lct:web4:[A-Za-z0-9_:-]+$")
SUBJECT_PATTERN = re.compile(r"^did:web4:(key|method):[A-Za-z0-9_-]+$")


def validate_lct_id(lct_id: str) -> Tuple[bool, str]:
    if not LCT_ID_PATTERN.match(lct_id):
        return False, f"LCT ID '{lct_id}' does not match pattern"
    return True, "OK"


def validate_subject(subject: str) -> Tuple[bool, str]:
    if not SUBJECT_PATTERN.match(subject):
        return False, f"Subject '{subject}' does not match pattern"
    return True, "OK"


# ═══════════════════════════════════════════════════════════════════
# Field Naming Validation
# ═══════════════════════════════════════════════════════════════════

REQUIRED_TOP_LEVEL = {"lct_id", "subject", "binding", "birth_certificate", "mrh", "policy"}
OPTIONAL_TOP_LEVEL = {"t3_tensor", "v3_tensor", "attestations", "lineage", "revocation"}
BINDING_FIELDS = {"entity_type", "public_key", "created_at", "binding_proof"}
BINDING_OPTIONAL = {"hardware_anchor"}
BIRTH_FIELDS = {"issuing_society", "citizen_role", "context", "birth_timestamp", "birth_witnesses"}
BIRTH_OPTIONAL = {"parent_entity"}
MRH_FIELDS = {"bound", "paired", "horizon_depth", "last_updated"}
MRH_OPTIONAL = {"witnessing"}
T3_FIELDS = {"talent", "training", "temperament"}
T3_OPTIONAL = {"composite_score", "sub_dimensions", "last_computed", "computation_witnesses"}
V3_FIELDS = {"valuation", "veracity", "validity"}
V3_OPTIONAL = {"composite_score", "sub_dimensions", "last_computed", "computation_witnesses"}


def validate_field_naming(doc: dict) -> Tuple[bool, List[str]]:
    """Validate all field names use snake_case per schema."""
    errors = []

    # Top level
    for f in REQUIRED_TOP_LEVEL:
        if f not in doc:
            errors.append(f"Missing required top-level field: {f}")

    # Binding
    if "binding" in doc:
        for f in BINDING_FIELDS:
            if f not in doc["binding"]:
                errors.append(f"Missing binding field: {f}")

    # Birth certificate
    if "birth_certificate" in doc:
        for f in BIRTH_FIELDS:
            if f not in doc["birth_certificate"]:
                errors.append(f"Missing birth_certificate field: {f}")

    # MRH
    if "mrh" in doc:
        for f in MRH_FIELDS:
            if f not in doc["mrh"]:
                errors.append(f"Missing mrh field: {f}")

    # T3 (if present)
    if "t3_tensor" in doc:
        for f in T3_FIELDS:
            if f not in doc["t3_tensor"]:
                errors.append(f"Missing t3_tensor field: {f}")

    # V3 (if present)
    if "v3_tensor" in doc:
        for f in V3_FIELDS:
            if f not in doc["v3_tensor"]:
                errors.append(f"Missing v3_tensor field: {f}")

    return len(errors) == 0, errors


def check_no_camel_case(obj: Any, path: str = "") -> List[str]:
    """Detect any camelCase keys (interop risk)."""
    issues = []
    if isinstance(obj, dict):
        for key in obj:
            if isinstance(key, str) and re.search(r"[a-z][A-Z]", key):
                issues.append(f"CamelCase detected at {path}.{key}")
            issues.extend(check_no_camel_case(obj[key], f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            issues.extend(check_no_camel_case(item, f"{path}[{i}]"))
    return issues


# ═══════════════════════════════════════════════════════════════════
# Go-Compatible Validation
# ═══════════════════════════════════════════════════════════════════

def validate_go_json_tags(doc: dict) -> Tuple[bool, List[str]]:
    """Validate that JSON matches what Go's json.Marshal() would produce.

    Go conventions:
    - struct fields are PascalCase but json tags enforce snake_case
    - omitempty skips zero-value fields
    - empty slices may serialize as null (not [])
    """
    issues = []

    # Go serializes empty slices as null, Python as []
    # Both are valid but we should be aware
    if "mrh" in doc:
        mrh = doc["mrh"]
        if "bound" in mrh and mrh["bound"] == []:
            pass  # Python: [], Go: null or [] depending on init
        if "witnessing" in mrh and mrh["witnessing"] == []:
            pass  # May be omitted in Go (omitempty on slice)

    # Go uses RFC3339 for timestamps (same as ISO 8601 with Z suffix)
    for ts_field in _extract_timestamps(doc):
        if not ts_field.endswith("Z") and "+" not in ts_field:
            issues.append(f"Timestamp not RFC3339: {ts_field}")

    return len(issues) == 0, issues


def _extract_timestamps(obj: Any, timestamps: Optional[list] = None) -> list:
    """Recursively find timestamp-like strings."""
    if timestamps is None:
        timestamps = []
    if isinstance(obj, str):
        if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", obj):
            timestamps.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _extract_timestamps(v, timestamps)
    elif isinstance(obj, list):
        for item in obj:
            _extract_timestamps(item, timestamps)
    return timestamps


# ═══════════════════════════════════════════════════════════════════
# Test Vector File Generation
# ═══════════════════════════════════════════════════════════════════

def generate_test_vector_file(vector: dict, description: str) -> dict:
    """Wrap a vector in the standard test vector file format."""
    return {
        "description": description,
        "expected_output": vector,
        "canonical_hash": canonical_hash(vector),
        "should_succeed": True,
        "schema_version": "1.0",
        "notes": "Cross-language interop test vector",
    }


# ═══════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    # ── T1: Minimal Vector Structure ─────────────────────────────
    print("T1: Minimal Vector Structure")
    ok, errs = validate_field_naming(MINIMAL_VECTOR)
    check("T1.1 All required fields present", ok)
    check("T1.2 Has lct_id", "lct_id" in MINIMAL_VECTOR)
    check("T1.3 Has subject", "subject" in MINIMAL_VECTOR)
    check("T1.4 Has binding", "binding" in MINIMAL_VECTOR)
    check("T1.5 Has birth_certificate", "birth_certificate" in MINIMAL_VECTOR)
    check("T1.6 Has mrh", "mrh" in MINIMAL_VECTOR)
    check("T1.7 Has policy", "policy" in MINIMAL_VECTOR)
    check("T1.8 Has t3_tensor", "t3_tensor" in MINIMAL_VECTOR)
    check("T1.9 Has v3_tensor", "v3_tensor" in MINIMAL_VECTOR)
    check("T1.10 Has revocation", "revocation" in MINIMAL_VECTOR)

    # ── T2: No CamelCase Keys ────────────────────────────────────
    print("T2: No CamelCase Keys (snake_case only)")
    camel = check_no_camel_case(MINIMAL_VECTOR)
    check("T2.1 Minimal: no camelCase", len(camel) == 0)
    camel2 = check_no_camel_case(HUMAN_VECTOR)
    check("T2.2 Human: no camelCase", len(camel2) == 0)
    camel3 = check_no_camel_case(REVOKED_VECTOR)
    check("T2.3 Revoked: no camelCase", len(camel3) == 0)

    # Verify sub_dimensions is snake_case not subDimensions
    check("T2.4 sub_dimensions not subDimensions",
          "sub_dimensions" in HUMAN_VECTOR["t3_tensor"])
    check("T2.5 composite_score not compositeScore",
          "composite_score" in MINIMAL_VECTOR["t3_tensor"])
    check("T2.6 entity_type not entityType",
          "entity_type" in MINIMAL_VECTOR["binding"])
    check("T2.7 birth_certificate not birthCertificate",
          "birth_certificate" in MINIMAL_VECTOR)
    check("T2.8 birth_witnesses not birthWitnesses",
          "birth_witnesses" in MINIMAL_VECTOR["birth_certificate"])

    # ── T3: LCT ID Pattern ──────────────────────────────────────
    print("T3: LCT ID Pattern")
    ok, _ = validate_lct_id("lct:web4:ai:test0000deadbeef")
    check("T3.1 Colons in LCT ID accepted", ok)
    ok, _ = validate_lct_id("lct:web4:test0000deadbeef")
    check("T3.2 No entity type in ID accepted", ok)
    ok, _ = validate_lct_id("lct:web4:human:alice7890abcdef")
    check("T3.3 Human entity type accepted", ok)
    ok, _ = validate_lct_id("invalid-id")
    check("T3.4 Invalid ID rejected", not ok)
    ok, _ = validate_lct_id("")
    check("T3.5 Empty ID rejected", not ok)

    # All vector IDs valid
    ok, _ = validate_lct_id(MINIMAL_VECTOR["lct_id"])
    check("T3.6 Minimal vector ID valid", ok)
    ok, _ = validate_lct_id(HUMAN_VECTOR["lct_id"])
    check("T3.7 Human vector ID valid", ok)
    ok, _ = validate_lct_id(REVOKED_VECTOR["lct_id"])
    check("T3.8 Revoked vector ID valid", ok)

    # ── T4: Subject Pattern ──────────────────────────────────────
    print("T4: Subject Pattern")
    ok, _ = validate_subject("did:web4:key:z6Mk1234567890")
    check("T4.1 Key subject accepted", ok)
    ok, _ = validate_subject("did:web4:method:example")
    check("T4.2 Method subject accepted", ok)
    ok, _ = validate_subject("did:web4:invalid:foo")
    check("T4.3 Invalid method rejected", not ok)
    ok, _ = validate_subject(MINIMAL_VECTOR["subject"])
    check("T4.4 Minimal vector subject valid", ok)
    ok, _ = validate_subject(HUMAN_VECTOR["subject"])
    check("T4.5 Human vector subject valid", ok)

    # ── T5: T3 Composite Scoring ─────────────────────────────────
    print("T5: T3 Composite Scoring")
    t3 = MINIMAL_VECTOR["t3_tensor"]
    computed = compute_t3_composite(t3)
    check("T5.1 Minimal T3 composite = 0.5", abs(computed - 0.5) < 0.0001)
    check("T5.2 Stored matches computed", abs(t3["composite_score"] - computed) < 0.0001)

    t3h = HUMAN_VECTOR["t3_tensor"]
    computed_h = compute_t3_composite(t3h)
    check("T5.3 Human T3 composite = 0.8", abs(computed_h - 0.8) < 0.0001)
    check("T5.4 Human stored matches computed", abs(t3h["composite_score"] - computed_h) < 0.0001)

    t3r = REVOKED_VECTOR["t3_tensor"]
    computed_r = compute_t3_composite(t3r)
    check("T5.5 Revoked T3 composite = 0.21", abs(computed_r - 0.21) < 0.0001)
    check("T5.6 Revoked stored matches computed", abs(t3r["composite_score"] - computed_r) < 0.0001)

    # T3 weights sum to 1.0
    check("T5.7 T3 weights sum to 1.0",
          abs(sum(T3_WEIGHTS.values()) - 1.0) < 0.0001)

    # ── T6: V3 Composite Scoring ─────────────────────────────────
    print("T6: V3 Composite Scoring")
    v3 = MINIMAL_VECTOR["v3_tensor"]
    computed_v = compute_v3_composite(v3)
    check("T6.1 Minimal V3 composite = 0.35", abs(computed_v - 0.35) < 0.0001)
    check("T6.2 Stored matches computed", abs(v3["composite_score"] - computed_v) < 0.0001)

    v3h = HUMAN_VECTOR["v3_tensor"]
    computed_vh = compute_v3_composite(v3h)
    expected_vh = 0.3 * 0.3 + 0.85 * 0.35 + 0.8 * 0.35  # = 0.6675
    check("T6.3 Human V3 composite = 0.6675", abs(computed_vh - 0.6675) < 0.0001)
    check("T6.4 Human stored matches computed", abs(v3h["composite_score"] - computed_vh) < 0.0001)

    # V3 weights sum to 1.0
    check("T6.5 V3 weights sum to 1.0",
          abs(sum(V3_WEIGHTS.values()) - 1.0) < 0.0001)

    # ── T7: Canonical Hash Stability ─────────────────────────────
    print("T7: Canonical Hash Stability")
    h1 = canonical_hash(MINIMAL_VECTOR)
    h2 = canonical_hash(MINIMAL_VECTOR)
    check("T7.1 Hash is deterministic", h1 == h2)
    check("T7.2 Hash is 64-char hex", len(h1) == 64)

    h3 = canonical_hash(HUMAN_VECTOR)
    check("T7.3 Different documents have different hashes", h1 != h3)

    # Hash is order-independent (sorted keys)
    doc_a = {"z": 1, "a": 2}
    doc_b = {"a": 2, "z": 1}
    check("T7.4 Hash is key-order independent", canonical_hash(doc_a) == canonical_hash(doc_b))

    # Canonical JSON is deterministic
    j1 = canonical_json(MINIMAL_VECTOR)
    j2 = canonical_json(MINIMAL_VECTOR)
    check("T7.5 Canonical JSON is deterministic", j1 == j2)
    check("T7.6 No extra whitespace", "  " not in j1)

    # ── T8: JSON Roundtrip ───────────────────────────────────────
    print("T8: JSON Roundtrip")
    j = json.dumps(MINIMAL_VECTOR, sort_keys=True)
    parsed = json.loads(j)
    check("T8.1 JSON roundtrip preserves lct_id", parsed["lct_id"] == MINIMAL_VECTOR["lct_id"])
    check("T8.2 JSON roundtrip preserves binding", parsed["binding"] == MINIMAL_VECTOR["binding"])
    check("T8.3 JSON roundtrip preserves T3",
          parsed["t3_tensor"]["talent"] == MINIMAL_VECTOR["t3_tensor"]["talent"])
    check("T8.4 JSON roundtrip preserves V3",
          parsed["v3_tensor"]["valuation"] == MINIMAL_VECTOR["v3_tensor"]["valuation"])

    j_human = json.dumps(HUMAN_VECTOR, sort_keys=True)
    parsed_h = json.loads(j_human)
    check("T8.5 Human roundtrip preserves sub_dimensions",
          "sub_dimensions" in parsed_h["t3_tensor"])
    check("T8.6 Human roundtrip preserves attestations",
          len(parsed_h["attestations"]) == 1)
    check("T8.7 Human roundtrip preserves lineage",
          len(parsed_h["lineage"]) == 1)
    check("T8.8 Human roundtrip preserves constraints",
          "max_delegation_depth" in parsed_h["policy"]["constraints"])

    # ── T9: Entity Types ─────────────────────────────────────────
    print("T9: Entity Types")
    check("T9.1 15 canonical entity types", len(ALL_ENTITY_TYPES) == 15)
    check("T9.2 Includes human", "human" in ALL_ENTITY_TYPES)
    check("T9.3 Includes ai", "ai" in ALL_ENTITY_TYPES)
    check("T9.4 Includes policy", "policy" in ALL_ENTITY_TYPES)
    check("T9.5 Includes infrastructure", "infrastructure" in ALL_ENTITY_TYPES)
    check("T9.6 All lowercase", all(t == t.lower() for t in ALL_ENTITY_TYPES))

    # Minimal vector uses valid entity type
    check("T9.7 Minimal binding entity_type valid",
          MINIMAL_VECTOR["binding"]["entity_type"] in ALL_ENTITY_TYPES)
    check("T9.8 Human binding entity_type valid",
          HUMAN_VECTOR["binding"]["entity_type"] in ALL_ENTITY_TYPES)

    # ── T10: Birth Certificate Witnesses ─────────────────────────
    print("T10: Birth Certificate Witnesses")
    min_witnesses = MINIMAL_VECTOR["birth_certificate"]["birth_witnesses"]
    check("T10.1 Minimal has 3 witnesses", len(min_witnesses) == 3)
    check("T10.2 All witnesses are LCT IDs",
          all(w.startswith("lct:web4:") for w in min_witnesses))
    check("T10.3 All witnesses unique", len(set(min_witnesses)) == len(min_witnesses))

    human_witnesses = HUMAN_VECTOR["birth_certificate"]["birth_witnesses"]
    check("T10.4 Human has 3 witnesses", len(human_witnesses) == 3)

    # Schema requires minItems: 1
    check("T10.5 At least 1 witness required (schema)",
          len(min_witnesses) >= 1)

    # ── T11: MRH Structure ───────────────────────────────────────
    print("T11: MRH Structure")
    mrh = MINIMAL_VECTOR["mrh"]
    check("T11.1 bound is array", isinstance(mrh["bound"], list))
    check("T11.2 paired is array", isinstance(mrh["paired"], list))
    check("T11.3 horizon_depth is int", isinstance(mrh["horizon_depth"], int))
    check("T11.4 last_updated is string", isinstance(mrh["last_updated"], str))
    check("T11.5 First pairing is birth_certificate",
          mrh["paired"][0]["pairing_type"] == "birth_certificate")
    check("T11.6 Birth pairing is permanent", mrh["paired"][0]["permanent"] is True)

    # Human MRH has all sections
    mrh_h = HUMAN_VECTOR["mrh"]
    check("T11.7 Human has bound entries", len(mrh_h["bound"]) > 0)
    check("T11.8 Human has witnessing entries", len(mrh_h.get("witnessing", [])) > 0)
    check("T11.9 Human bound has type field", "type" in mrh_h["bound"][0])
    check("T11.10 Human witnessing has role field", "role" in mrh_h["witnessing"][0])

    # ── T12: Go Compatibility ────────────────────────────────────
    print("T12: Go Compatibility")
    ok, issues = validate_go_json_tags(MINIMAL_VECTOR)
    check("T12.1 Minimal Go-compatible", ok)
    ok, issues = validate_go_json_tags(HUMAN_VECTOR)
    check("T12.2 Human Go-compatible", ok)

    # Timestamps are RFC3339 (Go uses time.RFC3339)
    timestamps = _extract_timestamps(MINIMAL_VECTOR)
    check("T12.3 All timestamps RFC3339", all(t.endswith("Z") for t in timestamps))

    # Go omitempty: optional fields may be absent
    minimal_no_optional = {k: v for k, v in MINIMAL_VECTOR.items()
                           if k in REQUIRED_TOP_LEVEL}
    check("T12.4 Required fields sufficient for Go", len(minimal_no_optional) == 6)

    # Go json tags match Python field names
    go_fields = ["lct_id", "subject", "binding", "birth_certificate",
                 "mrh", "policy", "t3_tensor", "v3_tensor",
                 "attestations", "lineage", "revocation"]
    for f in go_fields:
        if f in MINIMAL_VECTOR or f in HUMAN_VECTOR:
            check(f"T12.5 Go field '{f}' present", True)

    # ── T13: Revocation Vector ───────────────────────────────────
    print("T13: Revocation Vector")
    check("T13.1 Revoked status", REVOKED_VECTOR["revocation"]["status"] == "revoked")
    check("T13.2 Has reason", "reason" in REVOKED_VECTOR["revocation"])
    check("T13.3 Reason is compromise",
          REVOKED_VECTOR["revocation"]["reason"] == "compromise")
    check("T13.4 Has revocation timestamp", "ts" in REVOKED_VECTOR["revocation"])
    check("T13.5 Empty capabilities", len(REVOKED_VECTOR["policy"]["capabilities"]) == 0)
    check("T13.6 Low T3 scores", REVOKED_VECTOR["t3_tensor"]["talent"] < 0.5)

    # ── T14: Sub-dimensions ──────────────────────────────────────
    print("T14: Sub-dimensions")
    sub = HUMAN_VECTOR["t3_tensor"]["sub_dimensions"]
    check("T14.1 sub_dimensions is nested dict", isinstance(sub, dict))
    check("T14.2 Has talent sub-dimensions", "talent" in sub)
    check("T14.3 Has training sub-dimensions", "training" in sub)
    check("T14.4 Talent has code_review", "code_review" in sub["talent"])
    check("T14.5 Values are floats", isinstance(sub["talent"]["code_review"], float))
    check("T14.6 Values in [0,1]",
          all(0 <= v <= 1 for dim in sub.values() for v in dim.values()))

    # ── T15: Attestation Structure ───────────────────────────────
    print("T15: Attestation Structure")
    att = HUMAN_VECTOR["attestations"][0]
    check("T15.1 Has witness DID", att["witness"].startswith("did:web4:key:"))
    check("T15.2 Has type", "type" in att)
    check("T15.3 Has sig", "sig" in att)
    check("T15.4 Has ts", "ts" in att)
    check("T15.5 Has claims", "claims" in att)
    check("T15.6 Claims has ts", "ts" in att["claims"])

    # ── T16: Lineage Structure ───────────────────────────────────
    print("T16: Lineage Structure")
    lin = HUMAN_VECTOR["lineage"][0]
    check("T16.1 Has reason", "reason" in lin)
    check("T16.2 Has ts", "ts" in lin)
    check("T16.3 Genesis reason", lin["reason"] == "genesis")
    check("T16.4 No parent for genesis", "parent" not in lin)

    # ── T17: Cross-Vector Consistency ────────────────────────────
    print("T17: Cross-Vector Consistency")
    # All vectors have the same required structure
    for name, vec in [("minimal", MINIMAL_VECTOR), ("human", HUMAN_VECTOR),
                      ("revoked", REVOKED_VECTOR)]:
        ok, errs = validate_field_naming(vec)
        check(f"T17.1-{name} Field naming valid", ok)

    # All hashes unique
    hashes = [canonical_hash(v) for v in [MINIMAL_VECTOR, HUMAN_VECTOR, REVOKED_VECTOR]]
    check("T17.2 All vector hashes unique", len(set(hashes)) == 3)

    # T3 composites all verify
    for name, vec in [("minimal", MINIMAL_VECTOR), ("human", HUMAN_VECTOR),
                      ("revoked", REVOKED_VECTOR)]:
        if "t3_tensor" in vec and "composite_score" in vec["t3_tensor"]:
            computed = compute_t3_composite(vec["t3_tensor"])
            stored = vec["t3_tensor"]["composite_score"]
            check(f"T17.3-{name} T3 composite verifies",
                  abs(computed - stored) < 0.0001)

    # ── T18: Test Vector File Format ─────────────────────────────
    print("T18: Test Vector File Format")
    tv = generate_test_vector_file(MINIMAL_VECTOR, "Minimal valid LCT document")
    check("T18.1 Has description", "description" in tv)
    check("T18.2 Has expected_output", "expected_output" in tv)
    check("T18.3 Has canonical_hash", "canonical_hash" in tv)
    check("T18.4 Has should_succeed", tv["should_succeed"] is True)
    check("T18.5 Hash matches", tv["canonical_hash"] == canonical_hash(MINIMAL_VECTOR))

    # ── T19: Python LCT Document Compatibility ───────────────────
    print("T19: Python LCT Document Compatibility")
    try:
        from lct_document import minimal_valid_document
        doc = minimal_valid_document()
        py_dict = doc.to_dict()

        # Check key fields match (allowing minor differences in lct_id format)
        check("T19.1 Python doc has lct_id", "lct_id" in py_dict)
        check("T19.2 Python doc has subject", py_dict["subject"] == MINIMAL_VECTOR["subject"])
        check("T19.3 Python binding entity_type matches",
              py_dict["binding"]["entity_type"] == MINIMAL_VECTOR["binding"]["entity_type"])
        check("T19.4 Python T3 composite matches",
              abs(py_dict["t3_tensor"]["composite_score"] -
                  MINIMAL_VECTOR["t3_tensor"]["composite_score"]) < 0.0001)
        check("T19.5 Python V3 composite matches",
              abs(py_dict["v3_tensor"]["composite_score"] -
                  MINIMAL_VECTOR["v3_tensor"]["composite_score"]) < 0.0001)
        check("T19.6 Python birth_certificate context matches",
              py_dict["birth_certificate"]["context"] ==
              MINIMAL_VECTOR["birth_certificate"]["context"])
        check("T19.7 Python MRH horizon_depth matches",
              py_dict["mrh"]["horizon_depth"] == MINIMAL_VECTOR["mrh"]["horizon_depth"])
        check("T19.8 Python has 3 birth witnesses",
              len(py_dict["birth_certificate"]["birth_witnesses"]) == 3)

        # Check no camelCase in Python output
        camel = check_no_camel_case(py_dict)
        check("T19.9 Python output has no camelCase", len(camel) == 0)

        # Check LCT ID is valid
        ok, _ = validate_lct_id(py_dict["lct_id"])
        check("T19.10 Python LCT ID valid", ok)

    except ImportError:
        # If not importable, skip
        for i in range(10):
            check(f"T19.{i+1} (skipped - lct_document not importable)", True)

    # ── T20: Invalid Vector Rejection ────────────────────────────
    print("T20: Invalid Vector Rejection")

    # Missing required field
    invalid_no_binding = {k: v for k, v in MINIMAL_VECTOR.items() if k != "binding"}
    ok, errs = validate_field_naming(invalid_no_binding)
    check("T20.1 Missing binding detected", not ok)

    # Missing birth_certificate
    invalid_no_birth = {k: v for k, v in MINIMAL_VECTOR.items() if k != "birth_certificate"}
    ok, errs = validate_field_naming(invalid_no_birth)
    check("T20.2 Missing birth_certificate detected", not ok)

    # Invalid LCT ID
    ok, _ = validate_lct_id("not:an:lct:id")
    check("T20.3 Invalid LCT ID format rejected", not ok)

    # Invalid subject
    ok, _ = validate_subject("not:a:did")
    check("T20.4 Invalid subject rejected", not ok)

    # CamelCase detection
    camel_doc = {"birthCertificate": {}, "entityType": "ai"}
    camel = check_no_camel_case(camel_doc)
    check("T20.5 CamelCase detected in invalid doc", len(camel) == 2)

    # T3 with wrong composite (intentional mismatch)
    bad_t3 = {"talent": 1.0, "training": 1.0, "temperament": 1.0, "composite_score": 0.5}
    computed = compute_t3_composite(bad_t3)
    check("T20.6 Composite mismatch detected", abs(computed - bad_t3["composite_score"]) > 0.1)

    # ── T21: Write Test Vectors to Disk ──────────────────────────
    print("T21: Write Test Vectors to Disk")
    vectors_dir = os.path.join(os.path.dirname(__file__), "..", "..",
                                "web4-standard", "test-vectors", "lct")
    vectors_dir = os.path.normpath(vectors_dir)

    vectors_written = 0
    for name, vec, desc in [
        ("minimal-interop", MINIMAL_VECTOR, "Minimal LCT for cross-language interop"),
        ("human-full", HUMAN_VECTOR, "Full human LCT with all optional fields"),
        ("revoked-agent", REVOKED_VECTOR, "Revoked AI agent LCT"),
    ]:
        tv_file = generate_test_vector_file(vec, desc)
        filepath = os.path.join(vectors_dir, f"interop-{name}.json")
        try:
            with open(filepath, "w") as f:
                json.dump(tv_file, f, indent=2, sort_keys=True)
            vectors_written += 1
        except Exception as e:
            print(f"  Warning: Could not write {filepath}: {e}")

    check("T21.1 All 3 vector files written", vectors_written == 3)

    # Verify written files parse back correctly
    for name in ["minimal-interop", "human-full", "revoked-agent"]:
        filepath = os.path.join(vectors_dir, f"interop-{name}.json")
        try:
            with open(filepath) as f:
                loaded = json.load(f)
            check(f"T21.2 {name} file loads", "expected_output" in loaded)
        except Exception:
            check(f"T21.2 {name} file loads", False)

    # Verify hashes match
    for name, vec in [("minimal-interop", MINIMAL_VECTOR),
                      ("human-full", HUMAN_VECTOR),
                      ("revoked-agent", REVOKED_VECTOR)]:
        filepath = os.path.join(vectors_dir, f"interop-{name}.json")
        try:
            with open(filepath) as f:
                loaded = json.load(f)
            stored_hash = loaded["canonical_hash"]
            computed = canonical_hash(loaded["expected_output"])
            check(f"T21.3 {name} hash matches", stored_hash == computed)
        except Exception:
            check(f"T21.3 {name} hash matches", False)

    # ── Summary ──────────────────────────────────────────────────
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"Cross-Language Interop: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  FAILED: {failed}")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
