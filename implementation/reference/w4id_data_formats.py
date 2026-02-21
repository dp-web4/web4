#!/usr/bin/env python3
"""
Web4 Data Formats — Reference Implementation

Implements the Data Formats specification from:
  web4-standard/core-spec/data-formats.md

Core primitives:
  - W4ID: DID-compliant identifiers (did:web4:key:... and did:web4:web:...)
  - Pairwise W4ID: Privacy-preserving pseudonymous IDs per peer (§4)
  - Verifiable Credentials: W3C VC structure with Web4 extensions
  - JCS Canonicalization: RFC 8785 JSON Canonicalization Scheme (§5.1)
  - CBOR Deterministic Encoding: RFC 7049 deterministic rules (§5.2)
  - Ed25519 Signatures: Sign/verify over canonical payloads

These are foundational primitives used by all Web4 protocols.
"""

import base64
import hashlib
import hmac
import json
import struct
from dataclasses import dataclass, field
from typing import Optional

# Try real crypto if available
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# Try cbor2 if available
try:
    import cbor2
    HAS_CBOR = True
except ImportError:
    HAS_CBOR = False


# ══════════════════════════════════════════════════════════════
# §1 — W4ID (Web4 Identifier)
# ══════════════════════════════════════════════════════════════

class W4IDError(Exception):
    pass


@dataclass
class W4ID:
    """DID-compliant Web4 Identifier (§1).

    Format: did:web4:{method}:{method-specific-id}
    Methods: key (self-certifying), web (domain-based)
    """
    method: str
    method_specific_id: str

    @property
    def did(self) -> str:
        return f"did:web4:{self.method}:{self.method_specific_id}"

    def __str__(self) -> str:
        return self.did

    def __eq__(self, other) -> bool:
        if isinstance(other, W4ID):
            return self.did == other.did
        return False

    def __hash__(self) -> int:
        return hash(self.did)

    def to_dict(self) -> dict:
        return {"id": self.did, "method": self.method, "method_specific_id": self.method_specific_id}

    @classmethod
    def parse(cls, did_str: str) -> "W4ID":
        """Parse a W4ID string into components."""
        parts = did_str.split(":")
        if len(parts) < 4:
            raise W4IDError(f"Invalid W4ID: too few segments in '{did_str}'")
        if parts[0] != "did" or parts[1] != "web4":
            raise W4IDError(f"Invalid W4ID prefix: expected 'did:web4:', got '{parts[0]}:{parts[1]}:'")
        method = parts[2]
        if method not in ("key", "web"):
            raise W4IDError(f"Unknown W4ID method: '{method}' (expected 'key' or 'web')")
        method_specific_id = ":".join(parts[3:])
        if not method_specific_id:
            raise W4IDError(f"Empty method-specific-id in '{did_str}'")
        return cls(method=method, method_specific_id=method_specific_id)

    @classmethod
    def from_public_key(cls, pub_key_bytes: bytes) -> "W4ID":
        """Create a key-method W4ID from a public key (§1.2 key method)."""
        key_id = base64.urlsafe_b64encode(pub_key_bytes).decode().rstrip("=")
        return cls(method="key", method_specific_id=key_id)

    @classmethod
    def from_domain(cls, domain: str) -> "W4ID":
        """Create a web-method W4ID from a domain name (§1.2 web method)."""
        return cls(method="web", method_specific_id=domain)


# ══════════════════════════════════════════════════════════════
# §4 — Pairwise W4ID Derivation
# ══════════════════════════════════════════════════════════════

def _hkdf_sha256(master_secret: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    """HKDF-SHA256 key derivation (RFC 5869)."""
    # Extract
    prk = hmac.new(salt, master_secret, hashlib.sha256).digest()
    # Expand
    t = b""
    okm = b""
    for i in range(1, (length + 31) // 32 + 1):
        t = hmac.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
        okm += t
    return okm[:length]


def _base32_encode(data: bytes) -> str:
    """URL-safe base32 encoding, lowercase, no padding."""
    return base64.b32encode(data).decode().lower().rstrip("=")


def derive_pairwise_w4id(master_secret: bytes, peer_identifier: str) -> str:
    """Derive a pairwise pseudonymous W4ID for privacy (§4.1)."""
    salt = hashlib.sha256(peer_identifier.encode()).digest()
    pairwise_key = _hkdf_sha256(
        master_secret,
        salt=salt,
        info=b"web4-pairwise-id",
        length=32,
    )
    return f"w4id:pair:{_base32_encode(pairwise_key[:16])}"


class PairwiseIdentityManager:
    """Manages pairwise W4IDs for a single entity."""

    def __init__(self, master_secret: bytes):
        self.master_secret = master_secret
        self._cache: dict[str, str] = {}

    def get_pairwise_id(self, peer_identifier: str) -> str:
        if peer_identifier not in self._cache:
            self._cache[peer_identifier] = derive_pairwise_w4id(self.master_secret, peer_identifier)
        return self._cache[peer_identifier]

    def verify_deterministic(self, peer_identifier: str) -> bool:
        """Verify that the same input always produces the same output."""
        id1 = derive_pairwise_w4id(self.master_secret, peer_identifier)
        id2 = derive_pairwise_w4id(self.master_secret, peer_identifier)
        return id1 == id2

    @property
    def peer_count(self) -> int:
        return len(self._cache)


# ══════════════════════════════════════════════════════════════
# §5.1 — JSON Canonicalization Scheme (JCS, RFC 8785)
# ══════════════════════════════════════════════════════════════

def canonicalize_json(obj) -> str:
    """RFC 8785 JSON Canonicalization Scheme.

    Rules:
    - Object keys sorted lexicographically (Unicode code point order)
    - No whitespace between tokens
    - Numbers use shortest representation
    - Strings use minimal escaping
    - Recursive for nested objects
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(obj) -> str:
    """SHA-256 hash of the canonical JSON representation."""
    canonical = canonicalize_json(obj)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ══════════════════════════════════════════════════════════════
# §5.2 — CBOR Deterministic Encoding (RFC 7049)
# ══════════════════════════════════════════════════════════════

def canonicalize_cbor(obj) -> bytes:
    """CBOR deterministic encoding per RFC 7049 §3.9.

    Rules:
    1. Integers use smallest possible encoding
    2. Maps sorted by key encoding
    3. Indefinite-length items use definite-length
    4. No duplicate keys in maps

    Falls back to simulated CBOR if cbor2 not installed.
    """
    if HAS_CBOR:
        return cbor2.dumps(obj, canonical=True)
    else:
        # Simulated deterministic encoding for environments without cbor2
        return _simulate_cbor_encode(obj)


def _simulate_cbor_encode(obj) -> bytes:
    """Minimal deterministic CBOR-like encoding for testing without cbor2.
    NOT production — just sufficient for self-tests.
    """
    canonical_json = canonicalize_json(obj)
    return b"\xd9\xd9\xf7" + canonical_json.encode("utf-8")


def cbor_hash(obj) -> str:
    """SHA-256 hash of CBOR deterministic encoding."""
    encoded = canonicalize_cbor(obj)
    return hashlib.sha256(encoded).hexdigest()


# ══════════════════════════════════════════════════════════════
# §2 — Verifiable Credentials (VCs)
# ══════════════════════════════════════════════════════════════

@dataclass
class VerifiableCredential:
    """W3C Verifiable Credential with Web4 extensions (§2)."""
    vc_id: str
    vc_type: list
    issuer: str  # W4ID of issuer
    issuance_date: str
    credential_subject: dict
    context: list = field(default_factory=lambda: [
        "https://www.w3.org/2018/credentials/v1",
        "https://web4.io/contexts/v1",
    ])
    proof: Optional[dict] = None
    expiration_date: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "@context": list(self.context),
            "id": self.vc_id,
            "type": list(self.vc_type),
            "issuer": self.issuer,
            "issuanceDate": self.issuance_date,
            "credentialSubject": dict(self.credential_subject),
        }
        if self.expiration_date:
            d["expirationDate"] = self.expiration_date
        if self.proof:
            d["proof"] = dict(self.proof)
        return d

    def canonical_form(self) -> str:
        """JCS canonical form for signing."""
        d = self.to_dict()
        if "proof" in d:
            del d["proof"]
        return canonicalize_json(d)

    def sign(self, signer_key_bytes: bytes) -> "VerifiableCredential":
        """Sign the VC with Ed25519 (simulated or real)."""
        canonical = self.canonical_form()
        sig_bytes = _sign_bytes(canonical.encode("utf-8"), signer_key_bytes)
        self.proof = {
            "type": "Ed25519Signature2020",
            "created": self.issuance_date,
            "verificationMethod": self.issuer,
            "proofPurpose": "assertionMethod",
            "proofValue": base64.urlsafe_b64encode(sig_bytes).decode(),
        }
        return self

    def verify(self, verifier_key_bytes: bytes) -> bool:
        """Verify the VC signature."""
        if not self.proof:
            return False
        canonical = self.canonical_form()
        sig_bytes = base64.urlsafe_b64decode(self.proof["proofValue"])
        return _verify_bytes(canonical.encode("utf-8"), sig_bytes, verifier_key_bytes)

    @classmethod
    def from_dict(cls, d: dict) -> "VerifiableCredential":
        return cls(
            vc_id=d["id"],
            vc_type=d["type"],
            issuer=d["issuer"],
            issuance_date=d["issuanceDate"],
            credential_subject=d["credentialSubject"],
            context=d.get("@context", []),
            proof=d.get("proof"),
            expiration_date=d.get("expirationDate"),
        )


# ══════════════════════════════════════════════════════════════
# Signing Helpers
# ══════════════════════════════════════════════════════════════

def generate_keypair() -> tuple:
    """Generate Ed25519 keypair. Returns (private_bytes, public_bytes)."""
    if HAS_CRYPTO:
        private = Ed25519PrivateKey.generate()
        priv_bytes = private.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
        pub_bytes = private.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        return priv_bytes, pub_bytes
    else:
        # Simulated for environments without cryptography
        priv = hashlib.sha256(str(id(object())).encode()).digest()
        pub = hashlib.sha256(priv).digest()
        return priv, pub


def _sign_bytes(message: bytes, private_key_bytes: bytes) -> bytes:
    """Sign message with Ed25519."""
    if HAS_CRYPTO:
        private = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        return private.sign(message)
    else:
        return hmac.new(private_key_bytes, message, hashlib.sha256).digest()


def _verify_bytes(message: bytes, signature: bytes, public_key_bytes: bytes) -> bool:
    """Verify Ed25519 signature."""
    if HAS_CRYPTO:
        try:
            public = Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public.verify(signature, message)
            return True
        except Exception:
            return False
    else:
        # Simulated verification: reconstruct from private→public mapping
        # In test mode, we store the private key hash as the "public key"
        # This is NOT secure — just for testing without crypto lib
        expected = hmac.new(public_key_bytes, message, hashlib.sha256).digest()
        return hmac.compare_digest(signature, expected)


# ══════════════════════════════════════════════════════════════
# W4ID Document Resolution
# ══════════════════════════════════════════════════════════════

@dataclass
class W4IDDocument:
    """DID Document for a W4ID (simplified)."""
    w4id: W4ID
    public_key_bytes: bytes
    service_endpoints: list = field(default_factory=list)
    created: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "@context": ["https://www.w3.org/ns/did/v1", "https://web4.io/contexts/v1"],
            "id": self.w4id.did,
            "verificationMethod": [{
                "id": f"{self.w4id.did}#key-1",
                "type": "Ed25519VerificationKey2020",
                "controller": self.w4id.did,
                "publicKeyMultibase": f"z{base64.urlsafe_b64encode(self.public_key_bytes).decode().rstrip('=')}",
            }],
            "authentication": [f"{self.w4id.did}#key-1"],
            "service": self.service_endpoints,
            "created": self.created or "2026-02-21T12:00:00Z",
        }


# ══════════════════════════════════════════════════════════════
# Self-Tests
# ══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}")
            failed += 1

    # ── T1: W4ID Creation & Parsing ─────────────────────────
    print("\n═══ T1: W4ID Creation & Parsing ═══")
    # Key method
    key_id = W4ID(method="key", method_specific_id="abc123xyz")
    check("T1: key W4ID created", key_id is not None)
    check("T1: key DID format", key_id.did == "did:web4:key:abc123xyz")
    check("T1: str() works", str(key_id) == "did:web4:key:abc123xyz")

    # Web method
    web_id = W4ID.from_domain("example.com")
    check("T1: web W4ID created", web_id is not None)
    check("T1: web DID format", web_id.did == "did:web4:web:example.com")

    # Parse
    parsed = W4ID.parse("did:web4:key:abc123xyz")
    check("T1: parse succeeds", parsed is not None)
    check("T1: parse method correct", parsed.method == "key")
    check("T1: parse id correct", parsed.method_specific_id == "abc123xyz")
    check("T1: parse equals original", parsed == key_id)

    # Parse with colons in id
    complex_id = W4ID.parse("did:web4:web:sub.example.com:path")
    check("T1: complex parse preserves colons", complex_id.method_specific_id == "sub.example.com:path")

    # Hash/equality
    id_set = {key_id, parsed}
    check("T1: equal IDs hash same", len(id_set) == 1)

    # Invalid parse
    try:
        W4ID.parse("not-a-did")
        check("T1: invalid parse raises", False)
    except W4IDError:
        check("T1: invalid parse raises", True)

    try:
        W4ID.parse("did:other:key:xyz")
        check("T1: wrong prefix raises", False)
    except W4IDError:
        check("T1: wrong prefix raises", True)

    try:
        W4ID.parse("did:web4:unknown:xyz")
        check("T1: unknown method raises", False)
    except W4IDError:
        check("T1: unknown method raises", True)

    # Serialization
    d = key_id.to_dict()
    check("T1: to_dict has id", d["id"] == key_id.did)
    check("T1: to_dict has method", d["method"] == "key")

    # ── T2: W4ID from Public Key ────────────────────────────
    print("\n═══ T2: W4ID from Public Key ═══")
    priv, pub = generate_keypair()
    pk_id = W4ID.from_public_key(pub)
    check("T2: from_public_key creates key method", pk_id.method == "key")
    check("T2: DID starts correctly", pk_id.did.startswith("did:web4:key:"))
    check("T2: deterministic", W4ID.from_public_key(pub) == pk_id)

    # Different keys produce different IDs
    priv2, pub2 = generate_keypair()
    pk_id2 = W4ID.from_public_key(pub2)
    check("T2: different keys → different IDs", pk_id != pk_id2)

    # ── T3: Pairwise W4ID Derivation (§4) ───────────────────
    print("\n═══ T3: Pairwise W4ID Derivation ═══")
    master_secret = b"test-master-secret-32-bytes-long!"
    peer_a = "did:web4:key:alice-public-key"
    peer_b = "did:web4:key:bob-public-key"

    pw_a = derive_pairwise_w4id(master_secret, peer_a)
    check("T3: pairwise ID format", pw_a.startswith("w4id:pair:"))
    check("T3: pairwise ID non-empty", len(pw_a) > len("w4id:pair:"))

    # Deterministic
    pw_a2 = derive_pairwise_w4id(master_secret, peer_a)
    check("T3: deterministic derivation", pw_a == pw_a2)

    # Different peers → different IDs
    pw_b = derive_pairwise_w4id(master_secret, peer_b)
    check("T3: different peers → different IDs", pw_a != pw_b)

    # Different secrets → different IDs
    other_secret = b"other-master-secret-32-bytes!!!!"
    pw_c = derive_pairwise_w4id(other_secret, peer_a)
    check("T3: different secrets → different IDs", pw_a != pw_c)

    # PairwiseIdentityManager
    mgr = PairwiseIdentityManager(master_secret)
    id_alice = mgr.get_pairwise_id(peer_a)
    check("T3: manager returns same as direct", id_alice == pw_a)
    check("T3: manager caches", mgr.peer_count == 1)
    id_bob = mgr.get_pairwise_id(peer_b)
    check("T3: manager tracks peers", mgr.peer_count == 2)
    check("T3: manager deterministic verify", mgr.verify_deterministic(peer_a))

    # Unlinkability: can't correlate pairwise IDs back to master
    check("T3: alice pairwise ≠ bob pairwise", id_alice != id_bob)

    # ── T4: JCS Canonicalization (§5.1) ──────────────────────
    print("\n═══ T4: JCS Canonicalization (RFC 8785) ═══")
    # Key ordering
    obj1 = {"b": 2, "a": 1, "c": 3}
    can1 = canonicalize_json(obj1)
    check("T4: keys sorted", can1 == '{"a":1,"b":2,"c":3}')

    # No whitespace
    check("T4: no whitespace", " " not in can1)

    # Nested objects sorted
    obj2 = {"z": {"b": 2, "a": 1}, "a": {"d": 4, "c": 3}}
    can2 = canonicalize_json(obj2)
    check("T4: nested sorted", '"a"' in can2 and can2.index('"a"') < can2.index('"z"'))
    check("T4: inner keys sorted", '{"c":3,"d":4}' in can2)

    # Deterministic hash
    h1 = canonical_hash(obj1)
    h2 = canonical_hash({"c": 3, "a": 1, "b": 2})  # Same content, different order
    check("T4: canonical hash deterministic", h1 == h2)

    # Different content → different hash
    h3 = canonical_hash({"a": 1, "b": 2, "c": 4})
    check("T4: different content → different hash", h1 != h3)

    # Arrays preserved
    obj3 = {"items": [3, 1, 2], "name": "test"}
    can3 = canonicalize_json(obj3)
    check("T4: arrays preserved", '"items":[3,1,2]' in can3)

    # Unicode
    obj4 = {"name": "Renée", "emoji": "🌍"}
    can4 = canonicalize_json(obj4)
    check("T4: unicode preserved", "Renée" in can4 and "🌍" in can4)

    # ── T5: CBOR Deterministic Encoding (§5.2) ──────────────
    print("\n═══ T5: CBOR Deterministic Encoding ═══")
    obj_simple = {"a": 1, "b": "hello", "c": True}
    cbor_bytes = canonicalize_cbor(obj_simple)
    check("T5: CBOR encodes to bytes", isinstance(cbor_bytes, bytes))
    check("T5: CBOR non-empty", len(cbor_bytes) > 0)

    # Deterministic
    cbor_bytes2 = canonicalize_cbor(obj_simple)
    check("T5: CBOR deterministic", cbor_bytes == cbor_bytes2)

    # Different input → different output
    cbor_bytes3 = canonicalize_cbor({"a": 2, "b": "world"})
    check("T5: different input → different CBOR", cbor_bytes != cbor_bytes3)

    # CBOR hash
    ch1 = cbor_hash(obj_simple)
    ch2 = cbor_hash(obj_simple)
    check("T5: CBOR hash deterministic", ch1 == ch2)

    ch3 = cbor_hash({"a": 2})
    check("T5: different data → different CBOR hash", ch1 != ch3)

    if HAS_CBOR:
        # Verify roundtrip with real cbor2
        decoded = cbor2.loads(cbor_bytes)
        check("T5: CBOR roundtrip (real)", decoded == obj_simple)
        print(f"  [INFO] Using real cbor2 library")
    else:
        print(f"  [INFO] Using simulated CBOR (cbor2 not installed)")
        check("T5: simulated CBOR has prefix", cbor_bytes[:3] == b"\xd9\xd9\xf7")

    # ── T6: Verifiable Credentials (§2) ─────────────────────
    print("\n═══ T6: Verifiable Credentials ═══")
    priv_issuer, pub_issuer = generate_keypair()
    issuer_id = W4ID.from_public_key(pub_issuer)

    vc = VerifiableCredential(
        vc_id="vc:web4:cred:001",
        vc_type=["VerifiableCredential", "Web4Credential"],
        issuer=issuer_id.did,
        issuance_date="2026-02-21T12:00:00Z",
        credential_subject={
            "id": "did:web4:key:alice",
            "type": "CitizenshipCredential",
            "society": "lct:web4:society:dev-team",
            "rights": ["vote", "propose"],
        },
    )
    check("T6: VC created", vc is not None)
    check("T6: VC has id", vc.vc_id == "vc:web4:cred:001")
    check("T6: VC has issuer", vc.issuer == issuer_id.did)

    # Canonical form (no proof)
    canonical = vc.canonical_form()
    check("T6: canonical has no proof", "proof" not in canonical)
    check("T6: canonical is JSON", canonical.startswith("{"))

    # Serialization
    vcd = vc.to_dict()
    check("T6: to_dict has @context", "@context" in vcd)
    check("T6: to_dict has id", vcd["id"] == "vc:web4:cred:001")
    check("T6: to_dict has type", "Web4Credential" in vcd["type"])
    check("T6: to_dict has issuer", vcd["issuer"] == issuer_id.did)
    check("T6: to_dict has subject", "id" in vcd["credentialSubject"])

    # Sign
    vc.sign(priv_issuer)
    check("T6: VC signed", vc.proof is not None)
    check("T6: proof type", vc.proof["type"] == "Ed25519Signature2020")
    check("T6: proof has value", "proofValue" in vc.proof)

    # Verify
    valid = vc.verify(pub_issuer)
    check("T6: signature valid", valid)

    # Verify with wrong key
    _, wrong_pub = generate_keypair()
    invalid = vc.verify(wrong_pub)
    check("T6: wrong key fails verify", not invalid)

    # Tamper detection
    vc.credential_subject["rights"].append("admin")
    tampered = vc.verify(pub_issuer)
    check("T6: tamper detected", not tampered)

    # Restore
    vc.credential_subject["rights"].pop()

    # Roundtrip
    vcd_signed = vc.to_dict()
    vc2 = VerifiableCredential.from_dict(vcd_signed)
    check("T6: from_dict roundtrip id", vc2.vc_id == vc.vc_id)
    check("T6: from_dict roundtrip proof", vc2.proof is not None)

    # With expiration
    vc_exp = VerifiableCredential(
        vc_id="vc:web4:cred:002",
        vc_type=["VerifiableCredential"],
        issuer=issuer_id.did,
        issuance_date="2026-02-21T12:00:00Z",
        credential_subject={"id": "did:web4:key:bob"},
        expiration_date="2027-02-21T12:00:00Z",
    )
    vc_exp_d = vc_exp.to_dict()
    check("T6: expiration in dict", vc_exp_d.get("expirationDate") == "2027-02-21T12:00:00Z")

    # ── T7: W4ID Document ───────────────────────────────────
    print("\n═══ T7: W4ID Document ═══")
    doc = W4IDDocument(
        w4id=issuer_id,
        public_key_bytes=pub_issuer,
        service_endpoints=[{
            "id": f"{issuer_id.did}#web4-api",
            "type": "Web4Service",
            "serviceEndpoint": "https://api.example.com/web4",
        }],
    )
    dd = doc.to_dict()
    check("T7: document has @context", "@context" in dd)
    check("T7: document has id", dd["id"] == issuer_id.did)
    check("T7: has verification method", len(dd["verificationMethod"]) > 0)
    check("T7: verification method has key", "publicKeyMultibase" in dd["verificationMethod"][0])
    check("T7: has authentication", len(dd["authentication"]) > 0)
    check("T7: has service", len(dd["service"]) > 0)

    # ── T8: Cross-Format Consistency ────────────────────────
    print("\n═══ T8: Cross-Format Consistency ═══")
    test_obj = {"action": "transfer", "amount": 100, "from": "alice", "to": "bob"}

    # JCS and CBOR of same object should have different hashes (different encodings)
    jcs_h = canonical_hash(test_obj)
    cbor_h = cbor_hash(test_obj)
    check("T8: JCS hash ≠ CBOR hash (different formats)", jcs_h != cbor_h)

    # But both are deterministic
    check("T8: JCS idempotent", canonical_hash(test_obj) == jcs_h)
    check("T8: CBOR idempotent", cbor_hash(test_obj) == cbor_h)

    # VC canonical form uses JCS
    vc_canon = vc.canonical_form()
    vc_canon2 = vc.canonical_form()
    check("T8: VC canonical form deterministic", vc_canon == vc_canon2)

    # ── T9: Pairwise Privacy Properties ─────────────────────
    print("\n═══ T9: Pairwise Privacy Properties ═══")
    secret = b"privacy-secret-for-testing-32by!"
    mgr2 = PairwiseIdentityManager(secret)

    peers = [f"did:web4:key:peer-{i}" for i in range(10)]
    pairwise_ids = [mgr2.get_pairwise_id(p) for p in peers]

    # All unique
    check("T9: all pairwise IDs unique", len(set(pairwise_ids)) == 10)

    # Can't derive one peer's ID from another
    check("T9: no correlation between peers",
          all(pairwise_ids[i] != pairwise_ids[j]
              for i in range(10) for j in range(i + 1, 10)))

    # Same peer always gets same ID
    for i, p in enumerate(peers):
        check(f"T9: peer {i} consistent", mgr2.get_pairwise_id(p) == pairwise_ids[i])

    # ── T10: Signing Integration ────────────────────────────
    print("\n═══ T10: Signing Integration ═══")
    # Sign canonical JSON
    priv_s, pub_s = generate_keypair()
    message = canonicalize_json({"action": "approve", "target": "proposal-1"})
    sig = _sign_bytes(message.encode(), priv_s)
    check("T10: signature produced", len(sig) > 0)
    check("T10: signature verifies", _verify_bytes(message.encode(), sig, pub_s))

    # Different message fails
    other_msg = canonicalize_json({"action": "reject", "target": "proposal-1"})
    check("T10: different message fails", not _verify_bytes(other_msg.encode(), sig, pub_s))

    # Full flow: create W4ID → sign VC → verify
    priv_f, pub_f = generate_keypair()
    flow_id = W4ID.from_public_key(pub_f)
    flow_vc = VerifiableCredential(
        vc_id="vc:web4:flow:001",
        vc_type=["VerifiableCredential", "Web4TrustCredential"],
        issuer=flow_id.did,
        issuance_date="2026-02-21T12:00:00Z",
        credential_subject={
            "id": "did:web4:key:subject",
            "t3_score": 0.85,
            "trust_tier": "high",
        },
    )
    flow_vc.sign(priv_f)
    check("T10: flow VC signed", flow_vc.proof is not None)
    check("T10: flow VC verifies", flow_vc.verify(pub_f))

    # ══════════════════════════════════════════════════════════
    print(f"""
{'='*60}
  W4ID Data Formats — Track S Results
  {passed} passed, {failed} failed out of {passed + failed} checks
{'='*60}
""")

    if failed == 0:
        print("  All checks pass — Web4 data format primitives validated")
        print("  W4ID: DID-compliant identifiers (key + web methods)")
        print("  Pairwise: Privacy-preserving pseudonymous IDs (HKDF)")
        print("  VCs: W3C Verifiable Credentials with Ed25519 signatures")
        print("  JCS: RFC 8785 JSON Canonicalization")
        print(f"  CBOR: {'Real cbor2' if HAS_CBOR else 'Simulated'} deterministic encoding")
        print(f"  Crypto: {'Real Ed25519' if HAS_CRYPTO else 'Simulated HMAC'}")
    else:
        print("  Some checks failed — review output above")

    return passed, failed


if __name__ == "__main__":
    run_tests()
