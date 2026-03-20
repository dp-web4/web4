#!/usr/bin/env python3
"""
Validate Web4 SDK JSON-LD output against JSON Schema specifications.

Usage:
    python validate_schemas.py              # Run all validations
    python validate_schemas.py --verbose    # Show full document output
    python validate_schemas.py lct          # Validate LCT only
    python validate_schemas.py attestation  # Validate AttestationEnvelope only

Validates that:
1. SDK to_jsonld() output conforms to the spec-derived JSON Schema
2. Minimal documents (only required fields) pass
3. Fully-populated documents (all optional fields) pass
4. Roundtrip from_jsonld(to_jsonld()) produces valid output
5. Known-invalid documents are rejected

Exit code 0 = all validations pass, 1 = failures found.
"""

import json
import sys
import os
from pathlib import Path

import jsonschema
from jsonschema import Draft202012Validator

# Ensure SDK is importable
SDK_PATH = Path(__file__).parent.parent / "implementation" / "sdk"
if str(SDK_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PATH))

SCHEMA_DIR = Path(__file__).parent
VERBOSE = "--verbose" in sys.argv


def load_schema(name: str) -> dict:
    """Load a JSON Schema file."""
    path = SCHEMA_DIR / name
    with open(path) as f:
        return json.load(f)


def validate_document(doc: dict, schema: dict, label: str) -> bool:
    """Validate a document against a schema. Returns True if valid."""
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    if errors:
        print(f"  FAIL: {label}")
        for err in errors:
            path = ".".join(str(p) for p in err.absolute_path) or "(root)"
            print(f"    - {path}: {err.message}")
        return False
    else:
        print(f"  PASS: {label}")
        return True


def validate_invalid(doc: dict, schema: dict, label: str) -> bool:
    """Validate that a document is REJECTED by the schema. Returns True if correctly rejected."""
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(doc))
    if errors:
        print(f"  PASS: {label} (correctly rejected)")
        return True
    else:
        print(f"  FAIL: {label} (should have been rejected but passed)")
        return False


# ── LCT Validations ──────────────────────────────────────────────

def validate_lct() -> int:
    """Validate LCT JSON-LD output against schema. Returns failure count."""
    from web4.lct import (
        LCT, BirthCertificate, Binding, MRH, MRHPairing,
        Policy, Attestation, LineageEntry, EntityType, T3, V3,
    )

    schema = load_schema("lct-jsonld.schema.json")
    failures = 0
    total = 0

    print("\n=== LCT JSON-LD Schema Validation ===\n")

    # 1. Minimal LCT (only required fields populated)
    total += 1
    minimal = LCT(
        lct_id="lct:test:minimal",
        subject="did:web4:test",
        binding=Binding(
            entity_type=EntityType.HUMAN,
            public_key="ed25519:testkey",
            created_at="2026-03-20T00:00:00Z",
        ),
    )
    doc = minimal.to_jsonld()
    if VERBOSE:
        print(json.dumps(doc, indent=2))
    if not validate_document(doc, schema, "Minimal LCT"):
        failures += 1

    # 2. Full LCT (all optional fields populated)
    total += 1
    bc = BirthCertificate(
        issuing_society="lct:web4:society:genesis",
        citizen_role="lct:web4:role:citizen:platform",
        birth_timestamp="2026-03-20T12:00:00Z",
        birth_witnesses=["did:web4:bob", "did:web4:charlie"],
        genesis_block_hash="0xabc123def456",
    )
    full = LCT(
        lct_id="lct:web4:ai:full001",
        subject="did:web4:alice",
        binding=Binding(
            entity_type=EntityType.AI,
            public_key="ed25519:fullkey123",
            created_at="2026-03-20T12:00:00Z",
            binding_proof="cose:ES256:proof_data",
            hardware_anchor="tpm2",
        ),
        birth_certificate=bc,
        mrh=MRH(
            bound=["lct:web4:hw:device1"],
            paired=[
                MRHPairing(
                    lct_id="lct:web4:role:citizen:platform",
                    pairing_type="birth_certificate",
                    permanent=True,
                    ts="2026-03-20T12:00:00Z",
                )
            ],
            witnessing=["did:web4:witness1"],
            horizon_depth=3,
            last_updated="2026-03-20T12:00:00Z",
        ),
        policy=Policy(
            capabilities=["pairing:initiate", "metering:grant", "witness:attest"],
            constraints={"max_rate": 5000, "requires_quorum": True},
        ),
        t3=T3(talent=0.85, training=0.92, temperament=0.78),
        v3=V3(valuation=0.89, veracity=0.91, validity=0.76),
        attestations=[
            Attestation(
                witness="did:web4:bob",
                type="existence",
                claims={"observed_at": "2026-03-20T12:00:00Z", "method": "direct"},
                sig="cose:ES256:attestation_sig",
                ts="2026-03-20T12:00:00Z",
            )
        ],
        lineage=[
            LineageEntry(
                parent="lct:web4:ai:previous",
                reason="rotation",
                ts="2026-03-19T00:00:00Z",
            )
        ],
    )
    doc = full.to_jsonld()
    if VERBOSE:
        print(json.dumps(doc, indent=2))
    if not validate_document(doc, schema, "Full LCT (all optional fields)"):
        failures += 1

    # 3. Revoked LCT
    total += 1
    revoked = LCT(
        lct_id="lct:test:revoked",
        subject="did:web4:revoked",
        binding=Binding(
            entity_type=EntityType.SERVICE,
            public_key="ed25519:revokedkey",
            created_at="2026-03-20T00:00:00Z",
        ),
    )
    revoked.revoke(reason="compromised key")
    doc = revoked.to_jsonld()
    if not validate_document(doc, schema, "Revoked LCT"):
        failures += 1

    # 4. LCT created via factory method
    total += 1
    factory = LCT.create(
        entity_type=EntityType.AI,
        public_key="ed25519:factorykey",
        society="lct:web4:society:genesis",
        context="platform",
        witnesses=["did:web4:w1", "did:web4:w2"],
        timestamp="2026-03-20T12:00:00Z",
    )
    doc = factory.to_jsonld()
    if not validate_document(doc, schema, "LCT from factory create()"):
        failures += 1

    # 5. Roundtrip: to_jsonld -> from_jsonld -> to_jsonld
    total += 1
    doc1 = full.to_jsonld()
    roundtrip = LCT.from_jsonld(doc1)
    doc2 = roundtrip.to_jsonld()
    if not validate_document(doc2, schema, "Roundtrip LCT (from_jsonld -> to_jsonld)"):
        failures += 1

    # 6. Suspended LCT
    total += 1
    suspended = LCT(
        lct_id="lct:test:suspended",
        subject="did:web4:suspended",
        binding=Binding(
            entity_type=EntityType.DEVICE,
            public_key="ed25519:suspkey",
            created_at="2026-03-20T00:00:00Z",
        ),
    )
    suspended.revocation_status = suspended.revocation_status.__class__("suspended")
    doc = suspended.to_jsonld()
    if not validate_document(doc, schema, "Suspended LCT"):
        failures += 1

    # 7. Invalid: missing required lct_id
    total += 1
    invalid_missing = {"@context": ["https://web4.io/contexts/lct.jsonld"], "subject": "x"}
    if not validate_invalid(invalid_missing, schema, "Reject: missing lct_id"):
        failures += 1

    # 8. Invalid: bad entity_type
    total += 1
    invalid_type = {
        "@context": ["https://web4.io/contexts/lct.jsonld"],
        "lct_id": "lct:bad",
        "subject": "did:web4:bad",
        "binding": {"entity_type": "not_a_real_type", "public_key": "k", "created_at": "t"},
        "mrh": {"bound": [], "paired": [], "witnessing": [], "horizon_depth": 1},
        "policy": {"capabilities": []},
        "t3_tensor": {"talent": 0.5, "training": 0.5, "temperament": 0.5, "composite_score": 0.5},
        "v3_tensor": {"valuation": 0.5, "veracity": 0.5, "validity": 0.5, "composite_score": 0.5},
        "revocation": {"status": "active"},
    }
    if not validate_invalid(invalid_type, schema, "Reject: invalid entity_type"):
        failures += 1

    # 9. Invalid: trust value out of range
    total += 1
    invalid_range = {
        "@context": ["https://web4.io/contexts/lct.jsonld"],
        "lct_id": "lct:bad",
        "subject": "did:web4:bad",
        "binding": {"entity_type": "human", "public_key": "k", "created_at": "t"},
        "mrh": {"bound": [], "paired": [], "witnessing": [], "horizon_depth": 1},
        "policy": {"capabilities": []},
        "t3_tensor": {"talent": 1.5, "training": 0.5, "temperament": 0.5, "composite_score": 0.5},
        "v3_tensor": {"valuation": 0.5, "veracity": 0.5, "validity": 0.5, "composite_score": 0.5},
        "revocation": {"status": "active"},
    }
    if not validate_invalid(invalid_range, schema, "Reject: T3 talent > 1.0"):
        failures += 1

    # 10. Invalid: extra field at root
    total += 1
    invalid_extra = {
        "@context": ["https://web4.io/contexts/lct.jsonld"],
        "lct_id": "lct:bad",
        "subject": "did:web4:bad",
        "binding": {"entity_type": "human", "public_key": "k", "created_at": "t"},
        "mrh": {"bound": [], "paired": [], "witnessing": [], "horizon_depth": 1},
        "policy": {"capabilities": []},
        "t3_tensor": {"talent": 0.5, "training": 0.5, "temperament": 0.5, "composite_score": 0.5},
        "v3_tensor": {"valuation": 0.5, "veracity": 0.5, "validity": 0.5, "composite_score": 0.5},
        "revocation": {"status": "active"},
        "unexpected_field": "should fail",
    }
    if not validate_invalid(invalid_extra, schema, "Reject: unexpected root field"):
        failures += 1

    print(f"\n  LCT: {total - failures}/{total} passed")
    return failures


# ── AttestationEnvelope Validations ──────────────────────────────

def validate_attestation() -> int:
    """Validate AttestationEnvelope JSON-LD output against schema. Returns failure count."""
    from web4.attestation import (
        AttestationEnvelope, AnchorInfo, Proof, PlatformState,
    )
    import time

    schema = load_schema("attestation-envelope-jsonld.schema.json")
    failures = 0
    total = 0

    print("\n=== AttestationEnvelope JSON-LD Schema Validation ===\n")

    # 1. Minimal software envelope
    total += 1
    minimal = AttestationEnvelope(
        entity_id="lct:test:soft",
        public_key="ed25519:softkey",
        proof=Proof(format="ecdsa_software", signature="sig", challenge="nonce"),
    )
    doc = minimal.to_jsonld()
    if VERBOSE:
        print(json.dumps(doc, indent=2))
    if not validate_document(doc, schema, "Minimal software envelope"):
        failures += 1

    # 2. Full TPM2 envelope (all optional fields)
    total += 1
    full = AttestationEnvelope(
        entity_id="lct:test:tpm",
        public_key="-----BEGIN PUBLIC KEY-----\nMFkw...\n-----END PUBLIC KEY-----",
        anchor=AnchorInfo(
            type="tpm2",
            manufacturer="Intel",
            model="INTC TPM 2.0",
            firmware_version="1.38",
        ),
        proof=Proof(
            format="tpm2_quote",
            signature="base64sig",
            challenge="challenge_nonce",
            pcr_digest="sha256:digest_hash",
            pcr_selection=[0, 7, 14],
        ),
        platform_state=PlatformState(
            available=True,
            boot_verified=True,
            pcr_values={0: "abc123", 7: "def456", 14: "789ghi"},
            os_version="Linux 6.8.0",
            kernel_version="6.8.0-94-generic",
        ),
        timestamp=time.time(),
        purpose="session_start",
        issuer="legion.local",
    )
    doc = full.to_jsonld()
    if VERBOSE:
        print(json.dumps(doc, indent=2))
    if not validate_document(doc, schema, "Full TPM2 envelope"):
        failures += 1

    # 3. FIDO2 envelope
    total += 1
    fido2 = AttestationEnvelope(
        entity_id="lct:test:fido",
        public_key="ed25519:fidokey",
        anchor=AnchorInfo(type="fido2", manufacturer="Yubico", model="YubiKey 5"),
        proof=Proof(
            format="fido2_assertion",
            signature="fido_sig",
            challenge="fido_challenge",
            authenticator_data="cbor_auth_data",
            client_data_hash="client_hash",
        ),
        purpose="enrollment",
    )
    doc = fido2.to_jsonld()
    if not validate_document(doc, schema, "FIDO2 envelope"):
        failures += 1

    # 4. Secure Enclave envelope
    total += 1
    se = AttestationEnvelope(
        entity_id="lct:test:se",
        public_key="ed25519:sekey",
        anchor=AnchorInfo(type="secure_enclave", manufacturer="Apple"),
        proof=Proof(
            format="se_attestation",
            signature="se_sig",
            challenge="se_challenge",
            attestation_object="raw_attestation_b64",
        ),
        purpose="witness",
    )
    doc = se.to_jsonld()
    if not validate_document(doc, schema, "Secure Enclave envelope"):
        failures += 1

    # 5. Roundtrip: to_jsonld -> from_jsonld -> to_jsonld
    total += 1
    doc1 = full.to_jsonld()
    roundtrip = AttestationEnvelope.from_jsonld(doc1)
    doc2 = roundtrip.to_jsonld()
    if not validate_document(doc2, schema, "Roundtrip envelope"):
        failures += 1

    # 6. Invalid: missing entity_id
    total += 1
    invalid_missing = {
        "@context": ["https://web4.io/contexts/attestation-envelope.jsonld"],
        "@type": "AttestationEnvelope",
        "envelope_version": "0.1",
        "public_key": "k",
    }
    if not validate_invalid(invalid_missing, schema, "Reject: missing entity_id"):
        failures += 1

    # 7. Invalid: bad anchor type
    total += 1
    invalid_anchor = {
        "@context": ["https://web4.io/contexts/attestation-envelope.jsonld"],
        "@type": "AttestationEnvelope",
        "envelope_version": "0.1",
        "entity_id": "lct:bad",
        "public_key": "k",
        "public_key_fingerprint": "fp",
        "anchor": {"type": "quantum_computer"},
        "proof": {"format": "ecdsa_software", "signature": "s", "challenge": "c"},
        "timestamp": 0,
        "challenge_issued_at": 0,
        "challenge_ttl": 300,
        "platform_state": {"available": False},
        "trust_ceiling": 0.5,
    }
    if not validate_invalid(invalid_anchor, schema, "Reject: invalid anchor type"):
        failures += 1

    # 8. Invalid: trust_ceiling > 1.0
    total += 1
    invalid_ceiling = {
        "@context": ["https://web4.io/contexts/attestation-envelope.jsonld"],
        "@type": "AttestationEnvelope",
        "envelope_version": "0.1",
        "entity_id": "lct:bad",
        "public_key": "k",
        "public_key_fingerprint": "fp",
        "anchor": {"type": "software"},
        "proof": {"format": "ecdsa_software", "signature": "s", "challenge": "c"},
        "timestamp": 0,
        "challenge_issued_at": 0,
        "challenge_ttl": 300,
        "platform_state": {"available": False},
        "trust_ceiling": 1.5,
    }
    if not validate_invalid(invalid_ceiling, schema, "Reject: trust_ceiling > 1.0"):
        failures += 1

    # 9. Invalid: wrong @type
    total += 1
    invalid_type = {
        "@context": ["https://web4.io/contexts/attestation-envelope.jsonld"],
        "@type": "WrongType",
        "envelope_version": "0.1",
        "entity_id": "lct:bad",
        "public_key": "k",
        "public_key_fingerprint": "fp",
        "anchor": {"type": "software"},
        "proof": {"format": "ecdsa_software", "signature": "s", "challenge": "c"},
        "timestamp": 0,
        "challenge_issued_at": 0,
        "challenge_ttl": 300,
        "platform_state": {"available": False},
        "trust_ceiling": 0.4,
    }
    if not validate_invalid(invalid_type, schema, "Reject: wrong @type"):
        failures += 1

    print(f"\n  AttestationEnvelope: {total - failures}/{total} passed")
    return failures


# ── Main ─────────────────────────────────────────────────────────

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    run_lct = not args or "lct" in args
    run_att = not args or "attestation" in args

    total_failures = 0
    if run_lct:
        total_failures += validate_lct()
    if run_att:
        total_failures += validate_attestation()

    print(f"\n{'='*50}")
    if total_failures == 0:
        print("ALL VALIDATIONS PASSED")
    else:
        print(f"{total_failures} VALIDATION(S) FAILED")
    print(f"{'='*50}\n")

    return 1 if total_failures else 0


if __name__ == "__main__":
    sys.exit(main())
