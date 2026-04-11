#!/usr/bin/env python3
"""
Web4 Witnessing Specification — Reference Implementation
Spec: web4-standard/WEB4_WITNESSING_SPECIFICATION.md (110 lines, 7 sections)

Covers:
  §1  Introduction (cross-protocol witnessing)
  §2  Roles (time, audit-minimal, oracle — extensible registry)
  §3  Envelope Format (COSE_Sign1 canonical, JOSE/JWS alternative)
  §4  Error Handling (Problem Details format)
  §5  Interoperability Vectors (test vectors for all 3 roles)
  §6  IANA Considerations (Witness Role Registry)
  §7  Security Considerations (no nonce reuse, expiry rejection, multi-witness)

Run:  python3 witnessing_attestation_spec.py
"""

import time, hashlib, json, struct, os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum

# ─────────────────────────────────────────────
# §2 Witness Roles
# ─────────────────────────────────────────────

class WitnessRole(Enum):
    TIME = "time"                   # Attests to freshness via trusted timestamp
    AUDIT_MINIMAL = "audit-minimal" # Transaction occurred, minimal policy met
    ORACLE = "oracle"               # Contextual external information

WITNESS_ROLE_REGISTRY: Dict[str, Dict[str, str]] = {
    "time": {
        "description": "Attests to freshness by providing a trusted timestamp",
        "required_claims": "ts,nonce"
    },
    "audit-minimal": {
        "description": "Attests that a transaction occurred and met minimal policy requirements",
        "required_claims": "policy,event_hash"
    },
    "oracle": {
        "description": "Provides contextual external information (e.g., price, state)",
        "required_claims": "event_hash"
    },
}

def is_registered_role(role: str) -> bool:
    return role in WITNESS_ROLE_REGISTRY

def register_role(name: str, description: str, required_claims: str):
    """Extensible role registration per spec §2"""
    WITNESS_ROLE_REGISTRY[name] = {
        "description": description,
        "required_claims": required_claims
    }

# ─────────────────────────────────────────────
# §3.3 Required Fields
# ─────────────────────────────────────────────

REQUIRED_FIELDS = {"role", "ts", "subject", "event_hash", "nonce"}
# "policy" is MAY — can be omitted

@dataclass
class AttestationPayload:
    """Canonical attestation payload per spec §3.3"""
    role: str               # MUST be registered role
    ts: str                 # ISO 8601 timestamp
    subject: str            # W4IDp of attested entity
    event_hash: str         # SHA-256 hex of event/transcript
    nonce: str              # Random value for replay protection
    policy: str = ""        # Optional policy identifier

    def validate(self) -> List[str]:
        """Validate required fields"""
        errors = []
        if not self.role:
            errors.append("role: MUST be present")
        if not is_registered_role(self.role):
            errors.append(f"role: '{self.role}' not in registry")
        if not self.ts:
            errors.append("ts: MUST be present")
        if not self.subject:
            errors.append("subject: MUST be present")
        if not self.event_hash:
            errors.append("event_hash: MUST be present")
        if not self.nonce:
            errors.append("nonce: MUST be present")
        return errors

    def to_cbor_map(self) -> Dict:
        """CBOR-like map representation"""
        m = {
            "role": self.role,
            "ts": self.ts,
            "subject": self.subject,
            "event_hash": bytes.fromhex(self.event_hash) if len(self.event_hash) == 64 else self.event_hash,
            "nonce": bytes.fromhex(self.nonce) if all(c in '0123456789abcdef' for c in self.nonce) else self.nonce,
        }
        if self.policy:
            m["policy"] = self.policy
        return m

    def to_json(self) -> Dict:
        """JCS canonical JSON representation (sorted keys)"""
        m = {"event_hash": self.event_hash, "nonce": self.nonce}
        if self.policy:
            m["policy"] = self.policy
        m["role"] = self.role
        m["subject"] = self.subject
        m["ts"] = self.ts
        return m

# ─────────────────────────────────────────────
# §3.1 COSE Attestation Structure
# ─────────────────────────────────────────────

@dataclass
class COSEProtectedHeader:
    """COSE_Sign1 protected headers per spec §3.1"""
    alg: int = -8          # EdDSA
    kid: str = ""          # Key ID
    content_type: str = "application/web4+witness+cbor"

    def to_map(self) -> Dict:
        return {1: self.alg, 4: self.kid.encode() if self.kid else b"", 3: self.content_type}

@dataclass
class COSEAttestation:
    """COSE_Sign1 attestation per spec"""
    protected: COSEProtectedHeader
    payload: AttestationPayload
    signature: bytes = b""
    external_aad: bytes = b""

    def sig_structure(self) -> List:
        """Build Sig_structure per COSE Sign1: ["Signature1", protected, external_aad, payload]"""
        return ["Signature1", self.protected.to_map(), self.external_aad,
                self.payload.to_cbor_map()]

    def sign(self, private_key_sim: str = "sim"):
        """Simulated signing (Ed25519)"""
        sig_input = json.dumps(self.sig_structure(), default=str).encode()
        self.signature = hashlib.sha256(sig_input + private_key_sim.encode()).digest()

    def verify(self, public_key_sim: str = "sim") -> bool:
        """Simulated verification"""
        sig_input = json.dumps(self.sig_structure(), default=str).encode()
        expected = hashlib.sha256(sig_input + public_key_sim.encode()).digest()
        return self.signature == expected

# ─────────────────────────────────────────────
# §3.2 JOSE Attestation Structure
# ─────────────────────────────────────────────

@dataclass
class JOSEProtectedHeader:
    """JOSE/JWS protected header per spec §3.2"""
    alg: str = "ES256"
    kid: str = ""
    typ: str = "JWT"

    def to_json(self) -> Dict:
        return {"alg": self.alg, "kid": self.kid, "typ": self.typ}

@dataclass
class JOSEAttestation:
    """JOSE/JWS attestation per spec"""
    protected: JOSEProtectedHeader
    payload: AttestationPayload
    signature: str = ""

    def jws_signing_input(self) -> str:
        """JWS signing input: base64url(header) . base64url(payload)"""
        import base64
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(self.protected.to_json(), sort_keys=True).encode()
        ).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(self.payload.to_json(), sort_keys=True).encode()
        ).decode().rstrip("=")
        return f"{header_b64}.{payload_b64}"

    def sign(self, private_key_sim: str = "sim"):
        """Simulated ES256 signing"""
        signing_input = self.jws_signing_input()
        self.signature = hashlib.sha256(
            (signing_input + private_key_sim).encode()
        ).hexdigest()

    def verify(self, public_key_sim: str = "sim") -> bool:
        signing_input = self.jws_signing_input()
        expected = hashlib.sha256(
            (signing_input + public_key_sim).encode()
        ).hexdigest()
        return self.signature == expected

# ─────────────────────────────────────────────
# §3.4 Verification
# ─────────────────────────────────────────────

class AttestationVerifier:
    """Verification per spec §3.4"""

    def __init__(self, freshness_window: int = 300):
        """freshness_window: ±seconds (default ±300s per spec)"""
        self.freshness_window = freshness_window
        self.used_nonces: Set[str] = set()

    def verify_freshness(self, ts: str, now: Optional[float] = None) -> bool:
        """Confirm ts within freshness window"""
        try:
            # Parse ISO 8601
            ts_struct = time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
            ts_epoch = time.mktime(ts_struct) - time.timezone
        except ValueError:
            return False
        if now is None:
            now = time.time()
        return abs(now - ts_epoch) <= self.freshness_window

    def verify_event_hash(self, attestation_hash: str, event_data: bytes) -> bool:
        """Confirm event_hash matches event digest"""
        expected = hashlib.sha256(event_data).hexdigest()
        return attestation_hash == expected

    def verify_role(self, role: str) -> bool:
        """Confirm role is recognized"""
        return is_registered_role(role)

    def check_nonce_reuse(self, nonce: str) -> bool:
        """Witnesses MUST NOT reuse nonces (§7)"""
        if nonce in self.used_nonces:
            return False  # Reuse detected
        self.used_nonces.add(nonce)
        return True

    def verify_complete(self, payload: AttestationPayload,
                        event_data: bytes,
                        now: Optional[float] = None) -> Dict[str, Any]:
        """Full verification per spec §3.4 steps 1-4"""
        results = {
            "valid": True,
            "errors": []
        }
        # Step 1: Signature verified externally (COSE/JOSE verify methods)
        # Step 2: Freshness
        if not self.verify_freshness(payload.ts, now):
            results["valid"] = False
            results["errors"].append("ts: outside freshness window")
        # Step 3: Event hash match
        if not self.verify_event_hash(payload.event_hash, event_data):
            results["valid"] = False
            results["errors"].append("event_hash: does not match event digest")
        # Step 4: Role recognized
        if not self.verify_role(payload.role):
            results["valid"] = False
            results["errors"].append(f"role: '{payload.role}' not recognized")
        # §7: Nonce reuse
        if not self.check_nonce_reuse(payload.nonce):
            results["valid"] = False
            results["errors"].append("nonce: reuse detected")
        # Field validation
        field_errors = payload.validate()
        if field_errors:
            results["valid"] = False
            results["errors"].extend(field_errors)
        return results

# ─────────────────────────────────────────────
# §4 Error Handling
# ─────────────────────────────────────────────

@dataclass
class WitnessError:
    """Web4 Problem Details for witness errors per spec §4"""
    type: str = "w4:err:witness"
    title: str = ""
    status: int = 400
    detail: str = ""
    instance: str = ""

    def to_json(self) -> Dict:
        return {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "instance": self.instance
        }

    def content_type(self) -> str:
        return "application/problem+json"

# ─────────────────────────────────────────────
# §5 Interoperability Vectors
# ─────────────────────────────────────────────

def generate_test_vectors() -> Dict[str, AttestationPayload]:
    """Generate unsigned test vectors for all 3 roles per spec §5"""
    event_data = b"test event data"
    event_hash = hashlib.sha256(event_data).hexdigest()
    base_ts = "2025-09-11T15:00:02Z"
    base_subject = "w4idp:abcd1234"

    return {
        "time": AttestationPayload(
            role="time",
            ts=base_ts,
            subject=base_subject,
            event_hash=event_hash,
            nonce="01020304",
            policy="policy://baseline-v1"
        ),
        "audit-minimal": AttestationPayload(
            role="audit-minimal",
            ts=base_ts,
            subject=base_subject,
            event_hash=event_hash,
            nonce="05060708",
            policy="policy://baseline-v1"
        ),
        "oracle": AttestationPayload(
            role="oracle",
            ts=base_ts,
            subject=base_subject,
            event_hash=event_hash,
            nonce="090a0b0c",
            policy=""
        ),
    }

# ─────────────────────────────────────────────
# §6 IANA Considerations
# ─────────────────────────────────────────────

def get_iana_registry() -> Dict[str, Dict]:
    """Return the Web4 Witness Role Registry per spec §6"""
    return dict(WITNESS_ROLE_REGISTRY)

# ─────────────────────────────────────────────
# §7 Security Considerations
# ─────────────────────────────────────────────

class SecurityPolicy:
    """Security constraints per spec §7"""

    @staticmethod
    def validate_nonce_uniqueness(nonces: List[str]) -> bool:
        """Witnesses MUST NOT reuse nonces"""
        return len(nonces) == len(set(nonces))

    @staticmethod
    def validate_no_expired(ts: str, freshness_window: int = 300) -> bool:
        """Expired attestations MUST be rejected"""
        try:
            ts_struct = time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
            ts_epoch = time.mktime(ts_struct) - time.timezone
        except ValueError:
            return False
        return abs(time.time() - ts_epoch) <= freshness_window

    @staticmethod
    def recommend_multi_witness(witness_count: int) -> bool:
        """Implementations SHOULD support multiple witnesses"""
        return witness_count >= 2


# ═══════════════════════════════════════════════
# TEST SUITE
# ═══════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    # ─── §2: Witness Roles ───
    print("§2: Witness Roles")

    check("T1.1 time role registered", is_registered_role("time"))
    check("T1.2 audit-minimal registered", is_registered_role("audit-minimal"))
    check("T1.3 oracle registered", is_registered_role("oracle"))
    check("T1.4 unknown not registered", not is_registered_role("unknown"))
    check("T1.5 Initial registry has 3 roles", len(WITNESS_ROLE_REGISTRY) == 3)

    # Extensible registration
    register_role("quality", "Attests to output quality", "score,evidence")
    check("T1.6 Custom role registered", is_registered_role("quality"))
    check("T1.7 Registry now has 4 roles", len(WITNESS_ROLE_REGISTRY) == 4)

    # Clean up for other tests
    del WITNESS_ROLE_REGISTRY["quality"]

    # ─── §3.3: Required Fields ───
    print("§3.3: Required Fields / Attestation Payload")

    event_data = b"test transaction data"
    event_hash = hashlib.sha256(event_data).hexdigest()
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    nonce = os.urandom(4).hex()

    payload = AttestationPayload(
        role="time", ts=ts, subject="w4idp:abcd1234",
        event_hash=event_hash, nonce=nonce, policy="policy://baseline-v1"
    )
    errors = payload.validate()
    check("T2.1 Valid payload: no errors", len(errors) == 0)

    # Missing required fields
    bad_payload = AttestationPayload(role="", ts="", subject="", event_hash="", nonce="")
    bad_errors = bad_payload.validate()
    check("T2.2 Missing role detected", any("role" in e for e in bad_errors))
    check("T2.3 Missing ts detected", any("ts" in e for e in bad_errors))
    check("T2.4 Missing subject detected", any("subject" in e for e in bad_errors))
    check("T2.5 Missing event_hash detected", any("event_hash" in e for e in bad_errors))
    check("T2.6 Missing nonce detected", any("nonce" in e for e in bad_errors))

    # Unregistered role
    unreg = AttestationPayload(role="fake", ts=ts, subject="w4idp:x", event_hash=event_hash, nonce=nonce)
    unreg_errors = unreg.validate()
    check("T2.7 Unregistered role detected", any("registry" in e for e in unreg_errors))

    # Policy is optional
    no_policy = AttestationPayload(role="oracle", ts=ts, subject="w4idp:y",
                                   event_hash=event_hash, nonce=nonce)
    check("T2.8 No policy: still valid", len(no_policy.validate()) == 0)

    # JSON serialization (JCS canonical = sorted keys)
    json_out = payload.to_json()
    keys = list(json_out.keys())
    check("T2.9 JSON has all required fields",
          all(k in json_out for k in ["role", "ts", "subject", "event_hash", "nonce"]))
    check("T2.10 JSON keys sorted (JCS)", keys == sorted(keys))

    # CBOR map representation
    cbor_out = payload.to_cbor_map()
    check("T2.11 CBOR map has role", cbor_out["role"] == "time")
    check("T2.12 CBOR event_hash is bytes", isinstance(cbor_out["event_hash"], bytes))

    # ─── §3.1: COSE Attestation ───
    print("§3.1: COSE Attestation")

    cose_header = COSEProtectedHeader(alg=-8, kid="kid-demo-1")
    check("T3.1 COSE alg = EdDSA (-8)", cose_header.alg == -8)
    check("T3.2 COSE content type", cose_header.content_type == "application/web4+witness+cbor")

    header_map = cose_header.to_map()
    check("T3.3 Header map key 1 = alg", header_map[1] == -8)
    check("T3.4 Header map key 3 = content_type", header_map[3] == "application/web4+witness+cbor")

    cose = COSEAttestation(protected=cose_header, payload=payload)
    sig_struct = cose.sig_structure()
    check("T3.5 Sig_structure format", sig_struct[0] == "Signature1")
    check("T3.6 Sig_structure has 4 elements", len(sig_struct) == 4)
    check("T3.7 External AAD is empty bytes", sig_struct[2] == b"")

    cose.sign("test_key")
    check("T3.8 Signature generated", len(cose.signature) == 32)  # SHA-256
    check("T3.9 Verification succeeds", cose.verify("test_key"))
    check("T3.10 Wrong key fails", not cose.verify("wrong_key"))

    # ─── §3.2: JOSE Attestation ───
    print("§3.2: JOSE Attestation")

    jose_header = JOSEProtectedHeader(alg="ES256", kid="kid-demo-1")
    check("T4.1 JOSE alg = ES256", jose_header.alg == "ES256")
    check("T4.2 JOSE typ = JWT", jose_header.typ == "JWT")

    jose = JOSEAttestation(protected=jose_header, payload=payload)
    signing_input = jose.jws_signing_input()
    check("T4.3 JWS signing input format (header.payload)", "." in signing_input)
    parts = signing_input.split(".")
    check("T4.4 Two parts in signing input", len(parts) == 2)
    check("T4.5 Both parts non-empty", all(len(p) > 0 for p in parts))

    jose.sign("test_key")
    check("T4.6 JOSE signature generated", len(jose.signature) > 0)
    check("T4.7 JOSE verification succeeds", jose.verify("test_key"))
    check("T4.8 JOSE wrong key fails", not jose.verify("wrong_key"))

    # ─── §3.4: Verification ───
    print("§3.4: Verification")

    verifier = AttestationVerifier(freshness_window=300)

    # Freshness check
    now_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    check("T5.1 Current timestamp is fresh", verifier.verify_freshness(now_ts))

    old_ts = "2020-01-01T00:00:00Z"
    check("T5.2 Old timestamp is stale", not verifier.verify_freshness(old_ts))

    # Event hash verification
    check("T5.3 Correct hash verifies", verifier.verify_event_hash(event_hash, event_data))
    check("T5.4 Wrong hash fails", not verifier.verify_event_hash("badhash", event_data))

    # Role verification
    check("T5.5 Known role verifies", verifier.verify_role("time"))
    check("T5.6 Unknown role fails", not verifier.verify_role("fake"))

    # Nonce reuse detection
    check("T5.7 First nonce accepted", verifier.check_nonce_reuse("nonce_001"))
    check("T5.8 Reused nonce rejected", not verifier.check_nonce_reuse("nonce_001"))
    check("T5.9 Different nonce accepted", verifier.check_nonce_reuse("nonce_002"))

    # Complete verification
    fresh_payload = AttestationPayload(
        role="time", ts=now_ts, subject="w4idp:test",
        event_hash=event_hash, nonce="complete_test_nonce"
    )
    result = verifier.verify_complete(fresh_payload, event_data)
    check("T5.10 Complete verification passes", result["valid"])
    check("T5.11 No errors in valid attestation", len(result["errors"]) == 0)

    # Bad complete verification (wrong hash)
    bad_hash_payload = AttestationPayload(
        role="time", ts=now_ts, subject="w4idp:test",
        event_hash="0" * 64, nonce="bad_hash_nonce"
    )
    result_bad = verifier.verify_complete(bad_hash_payload, event_data)
    check("T5.12 Bad hash fails verification", not result_bad["valid"])
    check("T5.13 Error mentions event_hash", any("event_hash" in e for e in result_bad["errors"]))

    # ─── §4: Error Handling ───
    print("§4: Error Handling")

    err = WitnessError(
        title="Expired attestation",
        status=400,
        detail="Attestation timestamp outside freshness window",
        instance="/attestations/12345"
    )
    err_json = err.to_json()
    check("T6.1 Error type = w4:err:witness", err_json["type"] == "w4:err:witness")
    check("T6.2 Error status", err_json["status"] == 400)
    check("T6.3 Error detail", len(err_json["detail"]) > 0)
    check("T6.4 Content type", err.content_type() == "application/problem+json")

    # ─── §5: Interoperability Vectors ───
    print("§5: Interoperability Vectors")

    vectors = generate_test_vectors()
    check("T7.1 3 test vectors", len(vectors) == 3)
    check("T7.2 time vector", vectors["time"].role == "time")
    check("T7.3 audit-minimal vector", vectors["audit-minimal"].role == "audit-minimal")
    check("T7.4 oracle vector", vectors["oracle"].role == "oracle")

    # All vectors have matching event_hash
    test_event = b"test event data"
    expected_hash = hashlib.sha256(test_event).hexdigest()
    for role_name, vec in vectors.items():
        check(f"T7.{4 + list(vectors.keys()).index(role_name) + 1} {role_name} hash matches",
              vec.event_hash == expected_hash)

    # All vectors have unique nonces
    nonces = [v.nonce for v in vectors.values()]
    check("T7.8 All nonces unique", len(nonces) == len(set(nonces)))

    # All vectors validate
    for role_name, vec in vectors.items():
        errs = vec.validate()
        check(f"T7.{8 + list(vectors.keys()).index(role_name) + 1} {role_name} validates",
              len(errs) == 0)

    # Cross-format consistency (COSE and JOSE should have same payload)
    time_vec = vectors["time"]
    cose_time = COSEAttestation(
        protected=COSEProtectedHeader(kid="test-key-1"),
        payload=time_vec
    )
    jose_time = JOSEAttestation(
        protected=JOSEProtectedHeader(kid="test-key-1"),
        payload=time_vec
    )
    cose_payload = cose_time.payload.to_cbor_map()
    jose_payload = jose_time.payload.to_json()
    check("T7.12 COSE/JOSE same role", cose_payload["role"] == jose_payload["role"])
    check("T7.13 COSE/JOSE same subject", cose_payload["subject"] == jose_payload["subject"])
    check("T7.14 COSE/JOSE same ts", cose_payload["ts"] == jose_payload["ts"])

    # ─── §6: IANA Considerations ───
    print("§6: IANA Considerations")

    registry = get_iana_registry()
    check("T8.1 Registry has time", "time" in registry)
    check("T8.2 Registry has audit-minimal", "audit-minimal" in registry)
    check("T8.3 Registry has oracle", "oracle" in registry)
    check("T8.4 Registry entries have description",
          all("description" in v for v in registry.values()))

    # ─── §7: Security Considerations ───
    print("§7: Security Considerations")

    sp = SecurityPolicy()

    # Nonce uniqueness
    check("T9.1 Unique nonces pass", sp.validate_nonce_uniqueness(["a", "b", "c"]))
    check("T9.2 Duplicate nonces fail", not sp.validate_nonce_uniqueness(["a", "b", "a"]))

    # Multi-witness recommendation
    check("T9.3 Single witness: not recommended", not sp.recommend_multi_witness(1))
    check("T9.4 Two witnesses: recommended", sp.recommend_multi_witness(2))
    check("T9.5 Three witnesses: recommended", sp.recommend_multi_witness(3))

    # ─── Integration: Full attestation lifecycle ───
    print()
    print("Integration: Full attestation lifecycle")

    # 1. Create payload
    int_event = b"transfer 100 ATP from alice to bob"
    int_hash = hashlib.sha256(int_event).hexdigest()
    int_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    int_nonce = os.urandom(8).hex()

    int_payload = AttestationPayload(
        role="audit-minimal", ts=int_ts, subject="w4idp:alice",
        event_hash=int_hash, nonce=int_nonce,
        policy="policy://atp-transfer-v1"
    )
    check("T10.1 Payload validates", len(int_payload.validate()) == 0)

    # 2. Create COSE attestation
    int_cose = COSEAttestation(
        protected=COSEProtectedHeader(kid="witness-key-1"),
        payload=int_payload
    )
    int_cose.sign("witness_private_key")
    check("T10.2 COSE signed", len(int_cose.signature) > 0)
    check("T10.3 COSE verifies", int_cose.verify("witness_private_key"))

    # 3. Create JOSE alternative
    int_jose = JOSEAttestation(
        protected=JOSEProtectedHeader(kid="witness-key-1"),
        payload=int_payload
    )
    int_jose.sign("witness_private_key")
    check("T10.4 JOSE signed", len(int_jose.signature) > 0)
    check("T10.5 JOSE verifies", int_jose.verify("witness_private_key"))

    # 4. Verify attestation
    int_verifier = AttestationVerifier(freshness_window=300)
    int_result = int_verifier.verify_complete(int_payload, int_event)
    check("T10.6 Full verification passes", int_result["valid"])

    # 5. Second witness with different nonce
    int_nonce2 = os.urandom(8).hex()
    int_payload2 = AttestationPayload(
        role="time", ts=int_ts, subject="w4idp:alice",
        event_hash=int_hash, nonce=int_nonce2
    )
    int_result2 = int_verifier.verify_complete(int_payload2, int_event)
    check("T10.7 Second witness passes", int_result2["valid"])
    check("T10.8 Multi-witness recommended", sp.recommend_multi_witness(2))

    # 6. Replay attack (reuse first nonce)
    replay_payload = AttestationPayload(
        role="time", ts=int_ts, subject="w4idp:alice",
        event_hash=int_hash, nonce=int_nonce  # REUSED nonce
    )
    replay_result = int_verifier.verify_complete(replay_payload, int_event)
    check("T10.9 Replay attack detected (reused nonce)", not replay_result["valid"])

    # ─── Summary ───
    print()
    print("=" * 60)
    if failed == 0:
        print(f"Witnessing Attestation Spec: {passed}/{total} checks passed")
        print("  All checks passed!")
    else:
        print(f"Witnessing Attestation Spec: {passed}/{total} checks passed, {failed} FAILED")
    print("=" * 60)
    return failed == 0

if __name__ == "__main__":
    run_tests()
