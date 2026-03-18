"""
Tests for web4.security — Security Primitives.

Validates crypto suite definitions, W4ID parsing/derivation, key policies,
signature envelopes, and verifiable credentials per security-framework.md
and data-formats.md.
"""

import json
import pathlib
import pytest

from web4.security import (
    CryptoSuiteId,
    CryptoSuite,
    EncodingProfile,
    SUITE_BASE,
    SUITE_FIPS,
    SUITES,
    get_suite,
    negotiate_suite,
    W4ID,
    W4IDError,
    parse_w4id,
    derive_pairwise_w4id,
    KNOWN_METHODS,
    KeyStorageLevel,
    KeyPolicy,
    SignatureEnvelope,
    VerifiableCredential,
)


# ── Test Vector Loading ──────────────────────────────────────────

VECTORS_PATH = (
    pathlib.Path(__file__).resolve().parent.parent.parent.parent
    / "test-vectors" / "security" / "security-primitives.json"
)


@pytest.fixture(scope="module")
def vectors():
    with open(VECTORS_PATH) as f:
        data = json.load(f)
    return {v["id"]: v for v in data["vectors"]}


# ── Crypto Suite Tests ───────────────────────────────────────────

class TestCryptoSuites:
    """Tests for CryptoSuite definitions per spec §1."""

    def test_base_suite_definition(self, vectors):
        """sec-001: W4-BASE-1 suite has correct algorithms."""
        v = vectors["sec-001"]
        suite = get_suite(CryptoSuiteId.W4_BASE_1)
        assert suite.kem == v["expected"]["kem"]
        assert suite.sig == v["expected"]["sig"]
        assert suite.aead == v["expected"]["aead"]
        assert suite.hash_alg == v["expected"]["hash"]
        assert suite.kdf == v["expected"]["kdf"]
        assert suite.encoding.value == v["expected"]["encoding"]

    def test_fips_suite_definition(self, vectors):
        """sec-002: W4-FIPS-1 suite has correct algorithms."""
        v = vectors["sec-002"]
        suite = get_suite(CryptoSuiteId.W4_FIPS_1)
        assert suite.kem == v["expected"]["kem"]
        assert suite.sig == v["expected"]["sig"]
        assert suite.aead == v["expected"]["aead"]
        assert suite.hash_alg == v["expected"]["hash"]
        assert suite.kdf == v["expected"]["kdf"]
        assert suite.encoding.value == v["expected"]["encoding"]

    def test_suite_ids_are_string_values(self):
        """Suite IDs are string-typed for serialization."""
        assert CryptoSuiteId.W4_BASE_1.value == "W4-BASE-1"
        assert CryptoSuiteId.W4_FIPS_1.value == "W4-FIPS-1"

    def test_suites_registry_complete(self):
        """All defined suite IDs have entries in SUITES registry."""
        for sid in CryptoSuiteId:
            assert sid in SUITES

    def test_base_suite_is_cose(self):
        """BASE suite uses COSE encoding (MUST per spec)."""
        assert SUITE_BASE.encoding == EncodingProfile.COSE

    def test_fips_suite_is_jose(self):
        """FIPS suite uses JOSE encoding."""
        assert SUITE_FIPS.encoding == EncodingProfile.JOSE

    def test_suite_to_dict_roundtrip(self):
        """Suite serialization produces complete dict."""
        d = SUITE_BASE.to_dict()
        assert d["suite_id"] == "W4-BASE-1"
        assert d["sig"] == "Ed25519"
        assert d["encoding"] == "COSE"

    def test_invalid_suite_string_raises(self):
        """Constructing CryptoSuiteId from invalid string raises ValueError."""
        with pytest.raises(ValueError):
            CryptoSuiteId("NONEXISTENT")

    def test_suites_are_frozen(self):
        """Suite instances are immutable."""
        with pytest.raises(AttributeError):
            SUITE_BASE.sig = "RSA"  # type: ignore


# ── Suite Negotiation Tests ──────────────────────────────────────

class TestSuiteNegotiation:
    """Tests for negotiate_suite per spec §1.1."""

    def test_both_support_base(self, vectors):
        """sec-007: BASE preferred when both support it."""
        v = vectors["sec-007"]
        offered = [CryptoSuiteId(s) for s in v["input"]["offered"]]
        supported = [CryptoSuiteId(s) for s in v["input"]["supported"]]
        result = negotiate_suite(offered, supported)
        assert result is not None
        assert result.value == v["expected"]["negotiated"]

    def test_fips_only_overlap(self, vectors):
        """sec-008: FIPS selected when it's the only overlap."""
        v = vectors["sec-008"]
        offered = [CryptoSuiteId(s) for s in v["input"]["offered"]]
        supported = [CryptoSuiteId(s) for s in v["input"]["supported"]]
        result = negotiate_suite(offered, supported)
        assert result is not None
        assert result.value == v["expected"]["negotiated"]

    def test_no_overlap(self, vectors):
        """sec-009: None when no mutual suite exists."""
        v = vectors["sec-009"]
        offered = [CryptoSuiteId(s) for s in v["input"]["offered"]]
        supported = [CryptoSuiteId(s) for s in v["input"]["supported"]]
        result = negotiate_suite(offered, supported)
        assert result is None

    def test_default_supported_is_base_only(self):
        """Default supported list is [W4-BASE-1] only."""
        result = negotiate_suite([CryptoSuiteId.W4_BASE_1])
        assert result == CryptoSuiteId.W4_BASE_1

    def test_default_rejects_fips_only(self):
        """Default supported rejects FIPS-only offers."""
        result = negotiate_suite([CryptoSuiteId.W4_FIPS_1])
        assert result is None

    def test_base_preferred_over_fips(self):
        """BASE is preferred even when both are available."""
        result = negotiate_suite(
            [CryptoSuiteId.W4_FIPS_1, CryptoSuiteId.W4_BASE_1],
            [CryptoSuiteId.W4_BASE_1, CryptoSuiteId.W4_FIPS_1],
        )
        assert result == CryptoSuiteId.W4_BASE_1


# ── W4ID Tests ───────────────────────────────────────────────────

class TestW4ID:
    """Tests for W4ID parsing and validation per data-formats.md §1."""

    def test_parse_key_method(self, vectors):
        """sec-003: Parse did:web4:key:... correctly."""
        v = vectors["sec-003"]
        w4id = parse_w4id(v["input"]["did"])
        assert w4id.method == v["expected"]["method"]
        assert w4id.method_specific_id == v["expected"]["method_specific_id"]
        assert w4id.is_known_method == v["expected"]["is_known_method"]
        assert w4id.did == v["expected"]["did"]

    def test_parse_web_method(self, vectors):
        """sec-004: Parse did:web4:web:... correctly."""
        v = vectors["sec-004"]
        w4id = parse_w4id(v["input"]["did"])
        assert w4id.method == v["expected"]["method"]
        assert w4id.method_specific_id == v["expected"]["method_specific_id"]
        assert w4id.is_known_method == v["expected"]["is_known_method"]

    def test_invalid_format_rejected(self, vectors):
        """sec-005: Non-DID strings raise W4IDError."""
        v = vectors["sec-005"]
        with pytest.raises(W4IDError):
            parse_w4id(v["input"]["did"])

    def test_missing_method_specific_id(self, vectors):
        """sec-006: Empty method-specific-id is rejected."""
        v = vectors["sec-006"]
        with pytest.raises(W4IDError):
            parse_w4id(v["input"]["did"])

    def test_did_string_representation(self):
        """str(w4id) returns the full DID string."""
        w4id = W4ID(method="key", method_specific_id="abc123")
        assert str(w4id) == "did:web4:key:abc123"

    def test_w4id_equality(self):
        """Two W4IDs with same DID are equal."""
        a = parse_w4id("did:web4:key:same")
        b = W4ID(method="key", method_specific_id="same")
        assert a == b
        assert hash(a) == hash(b)

    def test_w4id_inequality(self):
        """Different W4IDs are not equal."""
        a = parse_w4id("did:web4:key:one")
        b = parse_w4id("did:web4:key:two")
        assert a != b

    def test_unknown_method_accepted(self):
        """Unknown methods parse but is_known_method is False."""
        w4id = parse_w4id("did:web4:custom:something")
        assert w4id.method == "custom"
        assert not w4id.is_known_method

    def test_known_methods_set(self):
        """KNOWN_METHODS contains key and web."""
        assert "key" in KNOWN_METHODS
        assert "web" in KNOWN_METHODS

    def test_w4id_to_dict(self):
        """W4ID serializes to dict with all fields."""
        w4id = parse_w4id("did:web4:web:example.com")
        d = w4id.to_dict()
        assert d["did"] == "did:web4:web:example.com"
        assert d["method"] == "web"
        assert d["method_specific_id"] == "example.com"

    def test_empty_method_rejected(self):
        """W4ID constructor rejects empty method."""
        with pytest.raises(W4IDError):
            W4ID(method="", method_specific_id="abc")

    def test_empty_specific_id_rejected(self):
        """W4ID constructor rejects empty method_specific_id."""
        with pytest.raises(W4IDError):
            W4ID(method="key", method_specific_id="")

    def test_method_specific_id_with_colons(self):
        """Method-specific-id can contain colons (e.g. paths)."""
        w4id = parse_w4id("did:web4:web:example.com:path:to:doc")
        assert w4id.method == "web"
        assert w4id.method_specific_id == "example.com:path:to:doc"

    def test_various_invalid_formats(self):
        """Various malformed strings are rejected."""
        invalids = [
            "",
            "did:web4",
            "did:web4:",
            "did:web4::",
            "did:other:key:abc",
            "web4:key:abc",
            "did:web4:KEY:abc",  # method must be lowercase
        ]
        for invalid in invalids:
            with pytest.raises(W4IDError):
                parse_w4id(invalid)


# ── Pairwise Derivation Tests ────────────────────────────────────

class TestPairwiseDerivation:
    """Tests for derive_pairwise_w4id per data-formats.md §4."""

    def test_derivation_is_deterministic(self, vectors):
        """sec-010: Same inputs produce same W4ID."""
        v = vectors["sec-010"]
        secret = bytes.fromhex(v["input"]["master_secret_hex"])
        peer = v["input"]["peer_identifier"]
        w4id_1 = derive_pairwise_w4id(secret, peer)
        w4id_2 = derive_pairwise_w4id(secret, peer)
        assert w4id_1 == w4id_2
        assert w4id_1.method == v["expected"]["method"]

    def test_different_peers_different_ids(self):
        """Different peer identifiers produce different W4IDs."""
        secret = b"same_secret"
        a = derive_pairwise_w4id(secret, "peer_a")
        b = derive_pairwise_w4id(secret, "peer_b")
        assert a != b

    def test_different_secrets_different_ids(self):
        """Different master secrets produce different W4IDs."""
        peer = "same_peer"
        a = derive_pairwise_w4id(b"secret_a", peer)
        b = derive_pairwise_w4id(b"secret_b", peer)
        assert a != b

    def test_derived_is_key_method(self):
        """Pairwise W4IDs always use key method."""
        w4id = derive_pairwise_w4id(b"secret", "peer")
        assert w4id.method == "key"

    def test_derived_is_valid_w4id(self):
        """Derived W4ID has valid DID format."""
        w4id = derive_pairwise_w4id(b"secret", "peer")
        reparsed = parse_w4id(w4id.did)
        assert reparsed == w4id


# ── Key Policy Tests ─────────────────────────────────────────────

class TestKeyPolicy:
    """Tests for KeyPolicy per spec §2."""

    def test_hardware_backed_detection(self, vectors):
        """sec-011: Correct hardware-backed detection for all storage levels."""
        v = vectors["sec-011"]
        for item in v["input"]["policies"]:
            policy = KeyPolicy(storage_level=KeyStorageLevel(item["storage_level"]))
            assert policy.is_hardware_backed == item["is_hardware_backed"], (
                f"{item['storage_level']} should be hardware_backed={item['is_hardware_backed']}"
            )

    def test_default_rotation_365_days(self):
        """Default key rotation is 365 days."""
        policy = KeyPolicy(storage_level=KeyStorageLevel.ENCRYPTED)
        assert policy.rotation_days == 365

    def test_default_suite_is_base(self):
        """Default allowed suite is W4-BASE-1."""
        policy = KeyPolicy(storage_level=KeyStorageLevel.HSM)
        assert CryptoSuiteId.W4_BASE_1 in policy.allowed_suites

    def test_invalid_rotation_rejected(self):
        """Rotation < 1 day is rejected."""
        with pytest.raises(ValueError):
            KeyPolicy(storage_level=KeyStorageLevel.HSM, rotation_days=0)

    def test_policy_to_dict(self):
        """KeyPolicy serialization includes all fields."""
        policy = KeyPolicy(
            storage_level=KeyStorageLevel.SECURE_ENCLAVE,
            rotation_days=90,
            allowed_suites=[CryptoSuiteId.W4_BASE_1, CryptoSuiteId.W4_FIPS_1],
        )
        d = policy.to_dict()
        assert d["storage_level"] == "secure_enclave"
        assert d["rotation_days"] == 90
        assert d["is_hardware_backed"] is True
        assert len(d["allowed_suites"]) == 2

    def test_all_storage_levels(self):
        """All storage levels are valid enum values."""
        levels = [KeyStorageLevel.HSM, KeyStorageLevel.SECURE_ENCLAVE,
                  KeyStorageLevel.ENCRYPTED, KeyStorageLevel.PLAINTEXT]
        assert len(levels) == 4
        for level in levels:
            policy = KeyPolicy(storage_level=level)
            assert policy.storage_level == level


# ── Signature Envelope Tests ─────────────────────────────────────

class TestSignatureEnvelope:
    """Tests for SignatureEnvelope per spec §1.3."""

    def test_envelope_creation(self):
        """Create signature envelope with all fields."""
        env = SignatureEnvelope(
            payload_hash="sha256:abc123",
            signature="base64sig",
            signer="did:web4:key:alice",
            suite_id=CryptoSuiteId.W4_BASE_1,
            timestamp="2026-03-18T00:00:00Z",
        )
        assert env.payload_hash == "sha256:abc123"
        assert env.signer == "did:web4:key:alice"

    def test_default_suite_is_base(self):
        """Default suite is W4-BASE-1."""
        env = SignatureEnvelope(
            payload_hash="h", signature="s", signer="signer",
        )
        assert env.suite_id == CryptoSuiteId.W4_BASE_1

    def test_envelope_to_dict(self):
        """Envelope serializes to dict."""
        env = SignatureEnvelope(
            payload_hash="hash", signature="sig", signer="signer",
            suite_id=CryptoSuiteId.W4_FIPS_1,
        )
        d = env.to_dict()
        assert d["suite_id"] == "W4-FIPS-1"
        assert d["signer"] == "signer"

    def test_envelope_is_frozen(self):
        """Envelopes are immutable."""
        env = SignatureEnvelope(
            payload_hash="h", signature="s", signer="x",
        )
        with pytest.raises(AttributeError):
            env.signature = "new"  # type: ignore


# ── Verifiable Credential Tests ──────────────────────────────────

class TestVerifiableCredential:
    """Tests for VerifiableCredential per data-formats.md §2."""

    def test_vc_structure(self, vectors):
        """sec-012: VC produces valid JSON-LD structure."""
        v = vectors["sec-012"]
        inp = v["input"]
        vc = VerifiableCredential(
            id=inp["id"],
            issuer=inp["issuer"],
            subject=inp["subject"],
            credential_type=inp["credential_type"],
            claims=inp["claims"],
        )
        d = vc.to_dict()
        assert v["expected"]["context_includes"] in d["@context"]
        for t in v["expected"]["type_includes"]:
            assert t in d["type"]
        assert "id" in d["credentialSubject"]

    def test_vc_includes_claims_in_subject(self):
        """Claims are merged into credentialSubject."""
        vc = VerifiableCredential(
            id="vc:1", issuer="issuer", subject="subject",
            claims={"role": "analyst", "level": 3},
        )
        d = vc.to_dict()
        assert d["credentialSubject"]["role"] == "analyst"
        assert d["credentialSubject"]["level"] == 3
        assert d["credentialSubject"]["id"] == "subject"

    def test_vc_optional_expiration(self):
        """Expiration is omitted when not set."""
        vc = VerifiableCredential(
            id="vc:1", issuer="i", subject="s",
        )
        d = vc.to_dict()
        assert "expirationDate" not in d

    def test_vc_with_expiration(self):
        """Expiration is included when set."""
        vc = VerifiableCredential(
            id="vc:1", issuer="i", subject="s",
            expiration_date="2027-01-01T00:00:00Z",
        )
        d = vc.to_dict()
        assert d["expirationDate"] == "2027-01-01T00:00:00Z"

    def test_vc_with_proof(self):
        """VC includes proof when signature envelope is provided."""
        proof = SignatureEnvelope(
            payload_hash="hash", signature="sig", signer="issuer",
        )
        vc = VerifiableCredential(
            id="vc:1", issuer="issuer", subject="subject",
            proof=proof,
        )
        d = vc.to_dict()
        assert "proof" in d
        assert d["proof"]["signer"] == "issuer"

    def test_vc_without_proof(self):
        """VC omits proof when not provided."""
        vc = VerifiableCredential(
            id="vc:1", issuer="i", subject="s",
        )
        d = vc.to_dict()
        assert "proof" not in d

    def test_vc_default_type(self):
        """Default credential type is Web4Credential."""
        vc = VerifiableCredential(
            id="vc:1", issuer="i", subject="s",
        )
        d = vc.to_dict()
        assert "Web4Credential" in d["type"]
