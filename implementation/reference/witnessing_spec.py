#!/usr/bin/env python3
"""
Web4 Witnessing Specification — Reference Implementation
Spec: web4-standard/protocols/web4-witnessing.md (110 lines, 7 sections)

Covers:
  §1  Introduction (purpose, cross-protocol consistency)
  §2  Roles (time, audit-minimal, oracle + extensible registry)
  §3  Envelope Format (COSE_Sign1, JOSE/JWS, required fields, verification)
  §4  Error Handling (w4:err:witness, problem details)
  §5  Interoperability Vectors (unsigned test vectors per role)
  §6  IANA Considerations (witness role registry)
  §7  Security Considerations (scoping, nonce reuse, expiry)

Complements existing witness_protocol_unified.py (176 checks) and
witness_enforcer.py with COSE/JOSE envelope format specifics.
"""

from __future__ import annotations
import calendar
import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

# ============================================================
# Test harness
# ============================================================
_pass = _fail = 0


def check(label: str, condition: bool):
    global _pass, _fail
    if condition:
        _pass += 1
    else:
        _fail += 1
        print(f"  FAIL: {label}")


# ============================================================
# §2 Witness Roles
# ============================================================

class WitnessRole(Enum):
    """Canonical witness roles per §2."""
    TIME = "time"              # Trusted timestamp
    AUDIT_MINIMAL = "audit-minimal"  # Minimal policy check
    ORACLE = "oracle"          # External contextual info


# Initial IANA registry entries per §6
WITNESS_ROLE_REGISTRY = {
    "time": "Attests to freshness by providing a trusted timestamp",
    "audit-minimal": "Attests that a transaction occurred and met minimal policy requirements",
    "oracle": "Provides contextual external information (e.g., price, state)",
}


def is_registered_role(role: str) -> bool:
    """Check if role is in the registry."""
    return role in WITNESS_ROLE_REGISTRY


def register_role(role: str, description: str):
    """Register a new witness role per §2 extensibility."""
    WITNESS_ROLE_REGISTRY[role] = description


# ============================================================
# §3.3 Required Fields
# ============================================================

REQUIRED_FIELDS = {"role", "ts", "subject", "event_hash", "nonce"}
OPTIONAL_FIELDS = {"policy"}

# Signature algorithms per §3
COSE_ALG_EDDSA = -8  # EdDSA (Ed25519)
JOSE_ALG_ES256 = "ES256"  # ECDSA P-256


# ============================================================
# §3.1 COSE Attestation Structure
# ============================================================

@dataclass
class COSEProtectedHeader:
    """COSE protected headers per §3.1."""
    alg: int = COSE_ALG_EDDSA  # -8 = EdDSA
    kid: bytes = b""           # Key identifier
    content_type: str = "application/web4+witness+cbor"

    def to_map(self) -> dict:
        return {
            1: self.alg,            # alg
            4: self.kid,            # kid
            3: self.content_type,   # content type
        }


@dataclass
class COSEAttestation:
    """COSE_Sign1 attestation per §3.1."""
    protected: COSEProtectedHeader
    payload: dict
    signature: bytes = b""

    def sig_structure(self) -> list:
        """Build Sig_structure per COSE Sign1: ["Signature1", protected, external_aad, payload]."""
        return [
            "Signature1",
            self._encode_protected(),
            b"",  # external_aad = empty
            self._encode_payload(),
        ]

    def _encode_protected(self) -> bytes:
        """Mock CBOR encode of protected headers."""
        # Convert bytes to hex for JSON serialization
        m = self.protected.to_map()
        m = {k: (v.hex() if isinstance(v, bytes) else v) for k, v in m.items()}
        return json.dumps(m, sort_keys=True).encode()

    def _encode_payload(self) -> bytes:
        """Mock CBOR encode of payload."""
        return json.dumps(self.payload, sort_keys=True).encode()

    def sign(self, private_key: str):
        """Mock signing — hash the sig_structure."""
        sig_input = str(self.sig_structure()).encode()
        self.signature = hashlib.sha256(sig_input).digest()

    def verify(self, public_key: str) -> bool:
        """Mock verification — recompute and compare."""
        sig_input = str(self.sig_structure()).encode()
        expected = hashlib.sha256(sig_input).digest()
        return self.signature == expected

    def validate_required_fields(self) -> list[str]:
        """Check all required payload fields per §3.3."""
        errors = []
        for field_name in REQUIRED_FIELDS:
            if field_name not in self.payload:
                errors.append(f"Missing required field: {field_name}")
        if "role" in self.payload and not is_registered_role(self.payload["role"]):
            errors.append(f"Unregistered role: {self.payload['role']}")
        return errors


# ============================================================
# §3.2 JOSE Attestation Structure
# ============================================================

@dataclass
class JOSEProtectedHeader:
    """JOSE protected header per §3.2."""
    alg: str = JOSE_ALG_ES256
    kid: str = ""
    typ: str = "JWT"

    def to_dict(self) -> dict:
        return {"alg": self.alg, "kid": self.kid, "typ": self.typ}


@dataclass
class JOSEAttestation:
    """JWS attestation per §3.2 with JCS canonical JSON."""
    protected: JOSEProtectedHeader
    payload: dict
    signature: str = ""

    def signing_input(self) -> str:
        """JCS canonical JSON payload for signing."""
        return json.dumps(self.payload, sort_keys=True, separators=(',', ':'))

    def sign(self, private_key: str):
        """Mock signing."""
        data = json.dumps(self.protected.to_dict(), sort_keys=True) + "." + self.signing_input()
        self.signature = hashlib.sha256(data.encode()).hexdigest()

    def verify(self, public_key: str) -> bool:
        """Mock verification."""
        data = json.dumps(self.protected.to_dict(), sort_keys=True) + "." + self.signing_input()
        expected = hashlib.sha256(data.encode()).hexdigest()
        return self.signature == expected

    def validate_required_fields(self) -> list[str]:
        """Check required fields per §3.3."""
        errors = []
        for field_name in REQUIRED_FIELDS:
            if field_name not in self.payload:
                errors.append(f"Missing required field: {field_name}")
        if "role" in self.payload and not is_registered_role(self.payload["role"]):
            errors.append(f"Unregistered role: {self.payload['role']}")
        return errors


# ============================================================
# §3.4 Verification
# ============================================================

DEFAULT_FRESHNESS_WINDOW = 300  # ±300 seconds per spec


def verify_attestation_freshness(ts: str, now: Optional[float] = None,
                                 window: int = DEFAULT_FRESHNESS_WINDOW) -> bool:
    """Verify ts within freshness window per §3.4 step 2."""
    current = now or time.time()
    try:
        att_time = calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))
    except ValueError:
        return False
    return abs(current - att_time) <= window


def verify_event_hash(claimed_hash: str, event_data: str) -> bool:
    """Verify event_hash matches event digest per §3.4 step 3."""
    computed = hashlib.sha256(event_data.encode()).hexdigest()
    return claimed_hash == computed


def full_verification(attestation, public_key: str,
                      event_data: str, now: Optional[float] = None) -> list[str]:
    """Full 4-step verification per §3.4."""
    errors = []

    # Step 1: Verify signature
    if not attestation.verify(public_key):
        errors.append("Signature verification failed")

    # Step 2: Check freshness
    ts = attestation.payload.get("ts", "")
    if not verify_attestation_freshness(ts, now):
        errors.append("Attestation not within freshness window")

    # Step 3: Verify event_hash
    event_hash = attestation.payload.get("event_hash", "")
    if not verify_event_hash(event_hash, event_data):
        errors.append("Event hash mismatch")

    # Step 4: Confirm role and policy
    field_errors = attestation.validate_required_fields()
    errors.extend(field_errors)

    return errors


# ============================================================
# §4 Error Handling
# ============================================================

@dataclass
class WitnessProblemDetails:
    """Problem details format per §4 (RFC 7807)."""
    type_uri: str = "w4:err:witness"
    title: str = ""
    status: int = 400
    detail: str = ""
    instance: str = ""

    def to_json(self) -> dict:
        return {
            "type": self.type_uri,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "instance": self.instance,
        }

    def to_cbor_content_type(self) -> str:
        return "application/problem+cbor"

    def to_json_content_type(self) -> str:
        return "application/problem+json"


# ============================================================
# §5 Interoperability Vectors
# ============================================================

def create_test_vector(role: str, subject: str = "w4idp:test",
                       event_data: str = "test_event") -> dict:
    """Create unsigned test vector per §5."""
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    event_hash = hashlib.sha256(event_data.encode()).hexdigest()
    nonce = hashlib.sha256(f"{ts}{role}".encode()).hexdigest()[:8]

    return {
        "role": role,
        "ts": ts,
        "subject": subject,
        "event_hash": event_hash,
        "policy": f"policy://baseline-v1" if role != "oracle" else None,
        "nonce": nonce,
    }


# Canonical test vectors for each role per §5
TEST_VECTORS = {
    "time": {
        "role": "time",
        "ts": "2025-09-11T15:00:02Z",
        "subject": "w4idp:abcd1234",
        "event_hash": "deadbeefcafebabe" * 4,
        "policy": "policy://baseline-v1",
        "nonce": "01020304",
    },
    "audit-minimal": {
        "role": "audit-minimal",
        "ts": "2025-09-11T15:00:02Z",
        "subject": "w4idp:abcd1234",
        "event_hash": "deadbeefcafebabe" * 4,
        "policy": "policy://baseline-v1",
        "nonce": "05060708",
    },
    "oracle": {
        "role": "oracle",
        "ts": "2025-09-11T15:00:02Z",
        "subject": "w4idp:abcd1234",
        "event_hash": "deadbeefcafebabe" * 4,
        "policy": None,
        "nonce": "090a0b0c",
    },
}


# ============================================================
# §6 IANA Considerations
# ============================================================

@dataclass
class IANARegistryEntry:
    """IANA registry entry per §6."""
    role: str
    description: str
    specification: str = "Web4 Witnessing Specification"
    initial: bool = True  # True for initial entries


IANA_INITIAL_ENTRIES = [
    IANARegistryEntry("time", "Trusted timestamp attestation"),
    IANARegistryEntry("audit-minimal", "Minimal policy compliance attestation"),
    IANARegistryEntry("oracle", "External contextual information attestation"),
]


# ============================================================
# §7 Security Considerations
# ============================================================

class SecurityProperty(Enum):
    """Security properties per §7."""
    SCOPED_PAIRWISE = "scoped_pairwise"   # Not surveillance
    NO_NONCE_REUSE = "no_nonce_reuse"     # Across attestations
    REJECT_EXPIRED = "reject_expired"      # Expired attestations
    MULTI_WITNESS = "multi_witness"        # Redundancy


@dataclass
class NonceTracker:
    """Track nonces to prevent reuse per §7."""
    seen: set[str] = field(default_factory=set)

    def check_and_record(self, nonce: str) -> bool:
        """Return True if nonce is new, False if reused."""
        if nonce in self.seen:
            return False
        self.seen.add(nonce)
        return True


# ============================================================
# TESTS
# ============================================================

if __name__ == "__main__":

    # ── T1: Witness Roles (§2) ───────────────────────────────
    print("T1: Witness Roles (§2)")

    check("T1.1 3 canonical roles", len(WitnessRole) == 3)
    check("T1.2 time role", WitnessRole.TIME.value == "time")
    check("T1.3 audit-minimal role", WitnessRole.AUDIT_MINIMAL.value == "audit-minimal")
    check("T1.4 oracle role", WitnessRole.ORACLE.value == "oracle")
    check("T1.5 3 initial registry entries", len(WITNESS_ROLE_REGISTRY) == 3)
    check("T1.6 time registered", is_registered_role("time"))
    check("T1.7 audit-minimal registered", is_registered_role("audit-minimal"))
    check("T1.8 oracle registered", is_registered_role("oracle"))
    check("T1.9 unknown not registered", not is_registered_role("unknown"))

    # Extensibility
    register_role("quality", "Quality assessment attestation")
    check("T1.10 New role registered", is_registered_role("quality"))
    # Restore for later tests
    del WITNESS_ROLE_REGISTRY["quality"]

    # ── T2: COSE Attestation (§3.1) ──────────────────────────
    print("T2: COSE Attestation (§3.1)")

    now_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    event = "transaction:12345"
    event_hash = hashlib.sha256(event.encode()).hexdigest()

    cose_hdr = COSEProtectedHeader(
        alg=COSE_ALG_EDDSA,
        kid=b"kid-demo-1",
        content_type="application/web4+witness+cbor",
    )

    cose = COSEAttestation(
        protected=cose_hdr,
        payload={
            "role": "time",
            "ts": now_ts,
            "subject": "w4idp:abcd1234",
            "event_hash": event_hash,
            "policy": "policy://baseline-v1",
            "nonce": "01020304",
        },
    )

    check("T2.1 COSE alg is EdDSA (-8)", cose.protected.alg == -8)
    check("T2.2 COSE content type correct",
          cose.protected.content_type == "application/web4+witness+cbor")
    check("T2.3 COSE kid set", cose.protected.kid == b"kid-demo-1")

    # Sig structure
    sig_struct = cose.sig_structure()
    check("T2.4 Sig structure has 4 elements", len(sig_struct) == 4)
    check("T2.5 Sig structure[0] = 'Signature1'", sig_struct[0] == "Signature1")
    check("T2.6 Sig structure[2] = empty aad", sig_struct[2] == b"")

    # Sign and verify
    cose.sign("mock_private_key")
    check("T2.7 Signature produced", len(cose.signature) > 0)
    check("T2.8 Verification succeeds", cose.verify("mock_public_key"))

    # Tamper and verify fails
    cose_tampered = COSEAttestation(
        protected=cose_hdr,
        payload={**cose.payload, "ts": "2020-01-01T00:00:00Z"},
        signature=cose.signature,
    )
    check("T2.9 Tampered verification fails", not cose_tampered.verify("mock_public_key"))

    # Required fields validation
    check("T2.10 All required fields present", len(cose.validate_required_fields()) == 0)

    # ── T3: JOSE Attestation (§3.2) ──────────────────────────
    print("T3: JOSE Attestation (§3.2)")

    jose_hdr = JOSEProtectedHeader(alg="ES256", kid="kid-demo-1", typ="JWT")

    jose = JOSEAttestation(
        protected=jose_hdr,
        payload={
            "role": "audit-minimal",
            "ts": now_ts,
            "subject": "w4idp:abcd1234",
            "event_hash": event_hash,
            "policy": "policy://baseline-v1",
            "nonce": "AQIDBA==",
        },
    )

    check("T3.1 JOSE alg is ES256", jose.protected.alg == "ES256")
    check("T3.2 JOSE typ is JWT", jose.protected.typ == "JWT")

    # JCS canonical JSON
    si = jose.signing_input()
    check("T3.3 Signing input is canonical JSON", "," in si and ":" in si)
    check("T3.4 No extra whitespace", " " not in si)

    # Sign and verify
    jose.sign("mock_private_key")
    check("T3.5 JOSE signature produced", len(jose.signature) > 0)
    check("T3.6 JOSE verification succeeds", jose.verify("mock_public_key"))

    # Tamper
    jose_tampered = JOSEAttestation(
        protected=jose_hdr,
        payload={**jose.payload, "nonce": "tampered"},
        signature=jose.signature,
    )
    check("T3.7 JOSE tamper detected", not jose_tampered.verify("mock_public_key"))

    # ── T4: Required Fields (§3.3) ───────────────────────────
    print("T4: Required Fields (§3.3)")

    check("T4.1 5 required fields", len(REQUIRED_FIELDS) == 5)
    check("T4.2 role is required", "role" in REQUIRED_FIELDS)
    check("T4.3 ts is required", "ts" in REQUIRED_FIELDS)
    check("T4.4 subject is required", "subject" in REQUIRED_FIELDS)
    check("T4.5 event_hash is required", "event_hash" in REQUIRED_FIELDS)
    check("T4.6 nonce is required", "nonce" in REQUIRED_FIELDS)
    check("T4.7 policy is optional", "policy" in OPTIONAL_FIELDS)

    # Missing fields
    bad_cose = COSEAttestation(
        protected=cose_hdr,
        payload={"role": "time"},  # Missing most required
    )
    errors = bad_cose.validate_required_fields()
    check("T4.8 Missing fields detected", len(errors) >= 4)

    # Unregistered role
    bad_role = COSEAttestation(
        protected=cose_hdr,
        payload={
            "role": "nonexistent",
            "ts": now_ts,
            "subject": "w4idp:test",
            "event_hash": "abc",
            "nonce": "def",
        },
    )
    check("T4.9 Unregistered role caught",
          any("Unregistered" in e for e in bad_role.validate_required_fields()))

    # ── T5: Verification (§3.4) ──────────────────────────────
    print("T5: Verification (§3.4)")

    # Freshness check
    fresh_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    check("T5.1 Current ts is fresh",
          verify_attestation_freshness(fresh_ts))

    old_ts = "2020-01-01T00:00:00Z"
    check("T5.2 Old ts is stale",
          not verify_attestation_freshness(old_ts))

    # Event hash
    data = "test_event_data"
    correct_hash = hashlib.sha256(data.encode()).hexdigest()
    check("T5.3 Correct hash verifies",
          verify_event_hash(correct_hash, data))
    check("T5.4 Wrong hash fails",
          not verify_event_hash("wrong_hash", data))

    # Full 4-step verification
    good_att = COSEAttestation(
        protected=cose_hdr,
        payload={
            "role": "time",
            "ts": fresh_ts,
            "subject": "w4idp:test",
            "event_hash": correct_hash,
            "nonce": "unique1",
        },
    )
    good_att.sign("key")
    errs = full_verification(good_att, "key", data)
    check("T5.5 Full verification passes", len(errs) == 0)

    # Fail each step
    bad_sig = COSEAttestation(
        protected=cose_hdr,
        payload=good_att.payload,
        signature=b"wrong",
    )
    check("T5.6 Bad signature caught",
          any("Signature" in e for e in full_verification(bad_sig, "key", data)))

    stale_att = COSEAttestation(
        protected=cose_hdr,
        payload={**good_att.payload, "ts": "2020-01-01T00:00:00Z"},
    )
    stale_att.sign("key")
    check("T5.7 Stale ts caught",
          any("freshness" in e for e in full_verification(stale_att, "key", data)))

    wrong_hash_att = COSEAttestation(
        protected=cose_hdr,
        payload={**good_att.payload, "event_hash": "wrong"},
    )
    wrong_hash_att.sign("key")
    check("T5.8 Wrong hash caught",
          any("hash" in e for e in full_verification(wrong_hash_att, "key", data)))

    # ── T6: Error Handling (§4) ──────────────────────────────
    print("T6: Error Handling (§4)")

    prob = WitnessProblemDetails(
        type_uri="w4:err:witness",
        title="Attestation Expired",
        status=400,
        detail="Timestamp outside freshness window",
    )
    check("T6.1 Problem type is w4:err:witness",
          prob.type_uri == "w4:err:witness")
    check("T6.2 JSON content type",
          prob.to_json_content_type() == "application/problem+json")
    check("T6.3 CBOR content type",
          prob.to_cbor_content_type() == "application/problem+cbor")

    doc = prob.to_json()
    check("T6.4 Problem details has type", doc["type"] == "w4:err:witness")
    check("T6.5 Problem details has title", doc["title"] == "Attestation Expired")
    check("T6.6 Problem details has status", doc["status"] == 400)
    check("T6.7 Problem details has detail", "freshness" in doc["detail"])

    # ── T7: Interoperability Vectors (§5) ────────────────────
    print("T7: Interoperability Vectors (§5)")

    check("T7.1 3 test vectors", len(TEST_VECTORS) == 3)
    check("T7.2 Time vector has all fields",
          REQUIRED_FIELDS <= set(TEST_VECTORS["time"].keys()))
    check("T7.3 Audit vector has all fields",
          REQUIRED_FIELDS <= set(TEST_VECTORS["audit-minimal"].keys()))
    check("T7.4 Oracle vector has all fields",
          REQUIRED_FIELDS <= set(TEST_VECTORS["oracle"].keys()))

    # Generate test vector
    gen = create_test_vector("time", "w4idp:test", "test_event")
    check("T7.5 Generated vector has role", gen["role"] == "time")
    check("T7.6 Generated vector has event_hash", len(gen["event_hash"]) == 64)
    check("T7.7 Generated vector has nonce", len(gen["nonce"]) > 0)

    # Each role has distinct nonce in canonical vectors
    nonces = [TEST_VECTORS[r]["nonce"] for r in TEST_VECTORS]
    check("T7.8 Canonical vectors have distinct nonces",
          len(set(nonces)) == 3)

    # ── T8: IANA Considerations (§6) ─────────────────────────
    print("T8: IANA Considerations (§6)")

    check("T8.1 3 initial IANA entries", len(IANA_INITIAL_ENTRIES) == 3)
    check("T8.2 Time in IANA", IANA_INITIAL_ENTRIES[0].role == "time")
    check("T8.3 Audit-minimal in IANA",
          IANA_INITIAL_ENTRIES[1].role == "audit-minimal")
    check("T8.4 Oracle in IANA", IANA_INITIAL_ENTRIES[2].role == "oracle")
    check("T8.5 All marked as initial",
          all(e.initial for e in IANA_INITIAL_ENTRIES))

    # ── T9: Security Considerations (§7) ─────────────────────
    print("T9: Security Considerations (§7)")

    check("T9.1 4 security properties", len(SecurityProperty) == 4)
    check("T9.2 Scoped pairwise property",
          SecurityProperty.SCOPED_PAIRWISE.value == "scoped_pairwise")

    # Nonce tracker
    tracker = NonceTracker()
    check("T9.3 New nonce accepted", tracker.check_and_record("nonce1"))
    check("T9.4 Same nonce rejected", not tracker.check_and_record("nonce1"))
    check("T9.5 Different nonce accepted", tracker.check_and_record("nonce2"))

    # Freshness window
    check("T9.6 Default freshness window is 300s",
          DEFAULT_FRESHNESS_WINDOW == 300)

    # ── T10: Cross-Format Compatibility ──────────────────────
    print("T10: Cross-Format Compatibility")

    # Same payload, different formats
    payload = {
        "role": "time",
        "ts": now_ts,
        "subject": "w4idp:cross",
        "event_hash": correct_hash,
        "nonce": "crosstest",
    }

    cose_att = COSEAttestation(protected=cose_hdr, payload=payload)
    jose_att = JOSEAttestation(protected=jose_hdr, payload=payload)

    cose_att.sign("key")
    jose_att.sign("key")

    check("T10.1 Both formats verify", cose_att.verify("key") and jose_att.verify("key"))
    check("T10.2 Both validate fields",
          len(cose_att.validate_required_fields()) == 0 and
          len(jose_att.validate_required_fields()) == 0)
    check("T10.3 COSE uses EdDSA (-8)",
          cose_att.protected.alg == -8)
    check("T10.4 JOSE uses ES256",
          jose_att.protected.alg == "ES256")

    # ── T11: End-to-End Witness Flow ─────────────────────────
    print("T11: End-to-End Witness Flow")

    # 1. Create attestation
    e2e_data = "handshake:session:xyz"
    e2e_hash = hashlib.sha256(e2e_data.encode()).hexdigest()
    e2e_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    e2e_att = COSEAttestation(
        protected=COSEProtectedHeader(kid=b"witness-1"),
        payload={
            "role": "audit-minimal",
            "ts": e2e_ts,
            "subject": "w4idp:entity123",
            "event_hash": e2e_hash,
            "policy": "policy://handshake-v2",
            "nonce": hashlib.sha256(b"unique").hexdigest()[:8],
        },
    )

    # 2. Sign
    e2e_att.sign("witness_private_key")
    check("T11.1 E2E attestation signed", len(e2e_att.signature) > 0)

    # 3. Full verification
    e2e_errors = full_verification(e2e_att, "witness_private_key", e2e_data)
    check("T11.2 E2E verification passes", len(e2e_errors) == 0)

    # 4. Nonce uniqueness
    nonce_tracker = NonceTracker()
    nonce = e2e_att.payload["nonce"]
    check("T11.3 First nonce accepted", nonce_tracker.check_and_record(nonce))
    check("T11.4 Replay rejected", not nonce_tracker.check_and_record(nonce))

    # 5. Error for expired
    expired = WitnessProblemDetails(
        title="Nonce Reuse",
        status=409,
        detail=f"Nonce {nonce} already used",
    )
    check("T11.5 Error details generated", expired.status == 409)

    # ════════════════════════════════════════════════════════
    print()
    print("=" * 60)
    total = _pass + _fail
    print(f"Witnessing Spec: {_pass}/{total} checks passed")
    if _fail:
        print(f"  ({_fail} FAILED)")
    else:
        print("  All checks passed!")
    print("=" * 60)
