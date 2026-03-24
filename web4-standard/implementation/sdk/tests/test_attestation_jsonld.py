"""
Tests for AttestationEnvelope JSON-LD serialization (I3).

Validates that to_jsonld() produces spec-compliant documents matching
the attestation-envelope spec, and that from_jsonld() round-trips cleanly.
"""

import json
import time
import pytest

from web4.attestation import (
    AttestationEnvelope,
    AnchorInfo,
    Proof,
    PlatformState,
    ATTESTATION_JSONLD_CONTEXT,
    TRUST_CEILINGS,
)


# ── Fixtures ─────────────────────────────────────────────────────

def _software_envelope(**overrides) -> AttestationEnvelope:
    """Minimal software envelope for testing."""
    defaults = dict(
        entity_id="lct://web4:test:agent@active",
        public_key="MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE_test_key",
        anchor=AnchorInfo(type="software"),
        proof=Proof(
            format="ecdsa_software",
            signature="MEUCIQD_test_sig",
            challenge="challenge-abc-123",
        ),
        timestamp=1710864000.0,
        challenge_issued_at=1710863990.0,
        challenge_ttl=300.0,
        envelope_version="0.1",
    )
    defaults.update(overrides)
    return AttestationEnvelope(**defaults)


def _tpm2_envelope(**overrides) -> AttestationEnvelope:
    """TPM2 envelope with PCR values for testing."""
    defaults = dict(
        entity_id="lct://sage:cbp:agent@raising",
        public_key="MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE_tpm_key",
        anchor=AnchorInfo(
            type="tpm2",
            manufacturer="Intel",
            model="INTC TPM2.0",
            firmware_version="1.38",
        ),
        proof=Proof(
            format="tpm2_quote",
            signature="MEUCIQD_tpm_sig",
            challenge="challenge-tpm-456",
            pcr_digest="a1b2c3d4e5f6",
            pcr_selection=[0, 1, 7],
        ),
        timestamp=1710864000.0,
        challenge_issued_at=1710863995.0,
        challenge_ttl=60.0,
        platform_state=PlatformState(
            available=True,
            boot_verified=True,
            pcr_values={0: "aabbccdd", 1: "11223344", 7: "deadbeef"},
            os_version="Linux 6.8.0",
            kernel_version="6.8.0-94-generic",
        ),
        issuer="legion",
        purpose="session_start",
    )
    defaults.update(overrides)
    return AttestationEnvelope(**defaults)


# ── @context and @type ───────────────────────────────────────────

class TestJsonldContext:
    """Verify @context header and @type field."""

    def test_context_present(self):
        doc = _software_envelope().to_jsonld()
        assert "@context" in doc
        assert doc["@context"] == [ATTESTATION_JSONLD_CONTEXT]

    def test_type_present(self):
        doc = _software_envelope().to_jsonld()
        assert doc["@type"] == "AttestationEnvelope"

    def test_context_url_value(self):
        doc = _software_envelope().to_jsonld()
        assert doc["@context"][0] == "https://web4.io/contexts/attestation-envelope.jsonld"


# ── WHO fields ───────────────────────────────────────────────────

class TestJsonldWhoFields:
    """Verify entity_id, public_key, and fingerprint."""

    def test_entity_id(self):
        doc = _software_envelope().to_jsonld()
        assert doc["entity_id"] == "lct://web4:test:agent@active"

    def test_public_key(self):
        doc = _software_envelope().to_jsonld()
        assert doc["public_key"] == "MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE_test_key"

    def test_fingerprint_auto_computed(self):
        env = _software_envelope()
        doc = env.to_jsonld()
        assert doc["public_key_fingerprint"] == env.public_key_fingerprint
        assert len(doc["public_key_fingerprint"]) == 16  # SHA-256 truncated


# ── WHAT (anchor) ────────────────────────────────────────────────

class TestJsonldAnchor:
    """Verify anchor serialization."""

    def test_software_anchor_minimal(self):
        doc = _software_envelope().to_jsonld()
        assert doc["anchor"] == {"type": "software"}

    def test_tpm2_anchor_full(self):
        doc = _tpm2_envelope().to_jsonld()
        anchor = doc["anchor"]
        assert anchor["type"] == "tpm2"
        assert anchor["manufacturer"] == "Intel"
        assert anchor["model"] == "INTC TPM2.0"
        assert anchor["firmware_version"] == "1.38"

    def test_optional_anchor_fields_excluded_when_none(self):
        doc = _software_envelope().to_jsonld()
        assert "manufacturer" not in doc["anchor"]
        assert "model" not in doc["anchor"]
        assert "firmware_version" not in doc["anchor"]

    def test_fido2_anchor(self):
        env = _software_envelope(
            anchor=AnchorInfo(type="fido2", manufacturer="Yubico"),
        )
        doc = env.to_jsonld()
        assert doc["anchor"]["type"] == "fido2"
        assert doc["anchor"]["manufacturer"] == "Yubico"
        assert "model" not in doc["anchor"]


# ── PROOF ────────────────────────────────────────────────────────

class TestJsonldProof:
    """Verify proof serialization."""

    def test_required_proof_fields(self):
        doc = _software_envelope().to_jsonld()
        proof = doc["proof"]
        assert proof["format"] == "ecdsa_software"
        assert proof["signature"] == "MEUCIQD_test_sig"
        assert proof["challenge"] == "challenge-abc-123"

    def test_tpm2_proof_with_pcr(self):
        doc = _tpm2_envelope().to_jsonld()
        proof = doc["proof"]
        assert proof["pcr_digest"] == "a1b2c3d4e5f6"
        assert proof["pcr_selection"] == [0, 1, 7]

    def test_optional_proof_fields_excluded(self):
        doc = _software_envelope().to_jsonld()
        proof = doc["proof"]
        assert "attestation_object" not in proof
        assert "pcr_digest" not in proof
        assert "pcr_selection" not in proof
        assert "authenticator_data" not in proof
        assert "client_data_hash" not in proof

    def test_fido2_proof_fields(self):
        env = _software_envelope(
            proof=Proof(
                format="fido2_assertion",
                signature="sig",
                challenge="chal",
                authenticator_data="authdata_b64",
                client_data_hash="cdh_b64",
            ),
        )
        doc = env.to_jsonld()
        proof = doc["proof"]
        assert proof["authenticator_data"] == "authdata_b64"
        assert proof["client_data_hash"] == "cdh_b64"

    def test_attestation_object_included_when_set(self):
        env = _software_envelope(
            proof=Proof(
                format="tpm2_quote",
                signature="sig",
                challenge="chal",
                attestation_object="raw_attestation_b64",
            ),
        )
        doc = env.to_jsonld()
        assert doc["proof"]["attestation_object"] == "raw_attestation_b64"


# ── WHEN (timestamps) ───────────────────────────────────────────

class TestJsonldTimestamps:
    """Verify timestamp fields."""

    def test_timestamp_present(self):
        doc = _software_envelope().to_jsonld()
        assert doc["timestamp"] == 1710864000.0

    def test_challenge_issued_at(self):
        doc = _software_envelope().to_jsonld()
        assert doc["challenge_issued_at"] == 1710863990.0

    def test_challenge_ttl(self):
        doc = _software_envelope().to_jsonld()
        assert doc["challenge_ttl"] == 300.0


# ── WHERE (platform state) ──────────────────────────────────────

class TestJsonldPlatformState:
    """Verify platform_state serialization."""

    def test_unavailable_platform_state(self):
        doc = _software_envelope().to_jsonld()
        ps = doc["platform_state"]
        assert ps["available"] is False
        assert "boot_verified" not in ps
        assert "pcr_values" not in ps
        assert "os_version" not in ps

    def test_full_platform_state(self):
        doc = _tpm2_envelope().to_jsonld()
        ps = doc["platform_state"]
        assert ps["available"] is True
        assert ps["boot_verified"] is True
        assert ps["os_version"] == "Linux 6.8.0"
        assert ps["kernel_version"] == "6.8.0-94-generic"

    def test_pcr_values_string_keys(self):
        """Spec uses Record<number, string> — JSON keys are always strings."""
        doc = _tpm2_envelope().to_jsonld()
        pcr = doc["platform_state"]["pcr_values"]
        assert "0" in pcr  # String keys in JSON
        assert pcr["0"] == "aabbccdd"
        assert pcr["7"] == "deadbeef"


# ── TRUST and METADATA ──────────────────────────────────────────

class TestJsonldTrustAndMetadata:
    """Verify trust_ceiling and optional metadata."""

    def test_software_trust_ceiling(self):
        doc = _software_envelope().to_jsonld()
        assert doc["trust_ceiling"] == 0.4

    def test_tpm2_trust_ceiling(self):
        doc = _tpm2_envelope().to_jsonld()
        assert doc["trust_ceiling"] == 1.0  # TPM2 with PCR

    def test_envelope_version(self):
        doc = _software_envelope().to_jsonld()
        assert doc["envelope_version"] == "0.1"

    def test_issuer_included_when_set(self):
        doc = _tpm2_envelope().to_jsonld()
        assert doc["issuer"] == "legion"

    def test_purpose_included_when_set(self):
        doc = _tpm2_envelope().to_jsonld()
        assert doc["purpose"] == "session_start"

    def test_issuer_excluded_when_none(self):
        doc = _software_envelope().to_jsonld()
        assert "issuer" not in doc

    def test_purpose_excluded_when_none(self):
        doc = _software_envelope().to_jsonld()
        assert "purpose" not in doc


# ── Roundtrip ────────────────────────────────────────────────────

class TestJsonldRoundtrip:
    """Verify to_jsonld → from_jsonld round-trip fidelity."""

    def test_software_roundtrip(self):
        env = _software_envelope()
        doc = env.to_jsonld()
        restored = AttestationEnvelope.from_jsonld(doc)
        assert restored.entity_id == env.entity_id
        assert restored.public_key == env.public_key
        assert restored.public_key_fingerprint == env.public_key_fingerprint
        assert restored.anchor.type == env.anchor.type
        assert restored.proof.format == env.proof.format
        assert restored.proof.signature == env.proof.signature
        assert restored.proof.challenge == env.proof.challenge
        assert restored.timestamp == env.timestamp
        assert restored.trust_ceiling == env.trust_ceiling
        assert restored.envelope_version == env.envelope_version

    def test_tpm2_roundtrip(self):
        env = _tpm2_envelope()
        doc = env.to_jsonld()
        restored = AttestationEnvelope.from_jsonld(doc)
        assert restored.entity_id == env.entity_id
        assert restored.anchor.type == "tpm2"
        assert restored.anchor.manufacturer == "Intel"
        assert restored.anchor.firmware_version == "1.38"
        assert restored.proof.pcr_digest == "a1b2c3d4e5f6"
        assert restored.proof.pcr_selection == [0, 1, 7]
        assert restored.platform_state.available is True
        assert restored.platform_state.boot_verified is True
        assert restored.platform_state.pcr_values == {0: "aabbccdd", 1: "11223344", 7: "deadbeef"}
        assert restored.issuer == "legion"
        assert restored.purpose == "session_start"

    def test_string_roundtrip(self):
        env = _tpm2_envelope()
        s = env.to_jsonld_string()
        restored = AttestationEnvelope.from_jsonld_string(s)
        assert restored.entity_id == env.entity_id
        assert restored.anchor.manufacturer == "Intel"
        assert restored.platform_state.pcr_values[7] == "deadbeef"

    def test_pcr_key_type_preservation(self):
        """PCR keys serialize as strings but deserialize back to ints."""
        env = _tpm2_envelope()
        doc = env.to_jsonld()
        # JSON serialization converts int keys to strings
        json_str = json.dumps(doc)
        parsed = json.loads(json_str)
        restored = AttestationEnvelope.from_jsonld(parsed)
        # Keys should be ints again
        assert 0 in restored.platform_state.pcr_values
        assert isinstance(list(restored.platform_state.pcr_values.keys())[0], int)


# ── Cross-format compatibility ───────────────────────────────────

class TestCrossFormatCompat:
    """Verify from_jsonld accepts SDK dict format too."""

    def test_from_dict_format(self):
        """from_jsonld should handle a plain dict (no @context)."""
        env = _software_envelope()
        plain_dict = env.to_dict()
        restored = AttestationEnvelope.from_jsonld(plain_dict)
        assert restored.entity_id == env.entity_id
        assert restored.proof.signature == env.proof.signature

    def test_jsonld_ignores_context(self):
        """@context and @type are stripped, not passed to constructor."""
        doc = _software_envelope().to_jsonld()
        assert "@context" in doc
        assert "@type" in doc
        # Should not raise on unknown fields
        restored = AttestationEnvelope.from_jsonld(doc)
        assert restored.entity_id == "lct://web4:test:agent@active"


# ── Spec canonical example ───────────────────────────────────────

class TestSpecCanonical:
    """Validate against the spec's canonical structure."""

    def test_canonical_field_order(self):
        """Spec interface defines fields in a specific order.
        Verify all spec fields are present in JSON-LD output."""
        doc = _tpm2_envelope().to_jsonld()
        spec_fields = [
            "@context", "@type", "envelope_version",
            "entity_id", "public_key", "public_key_fingerprint",
            "anchor", "proof",
            "timestamp", "challenge_issued_at", "challenge_ttl",
            "platform_state",
            "trust_ceiling",
            "issuer", "purpose",
        ]
        for f in spec_fields:
            assert f in doc, f"Spec field '{f}' missing from JSON-LD output"

    def test_anchor_type_values(self):
        """Spec defines 4 anchor types."""
        for atype in ["tpm2", "fido2", "secure_enclave", "software"]:
            env = _software_envelope(anchor=AnchorInfo(type=atype))
            doc = env.to_jsonld()
            assert doc["anchor"]["type"] == atype

    def test_proof_format_values(self):
        """Spec defines 4 proof formats."""
        for fmt in ["tpm2_quote", "fido2_assertion", "se_attestation", "ecdsa_software"]:
            env = _software_envelope(
                proof=Proof(format=fmt, signature="sig", challenge="chal"),
            )
            doc = env.to_jsonld()
            assert doc["proof"]["format"] == fmt

    def test_purpose_values(self):
        """Spec defines 5 purpose values."""
        for purpose in ["enrollment", "session_start", "re_attestation", "witness", "migration"]:
            env = _software_envelope(purpose=purpose)
            doc = env.to_jsonld()
            assert doc["purpose"] == purpose


# ── Backward compatibility ───────────────────────────────────────

class TestBackwardCompat:
    """Verify to_dict/from_dict still works unchanged."""

    def test_to_dict_unchanged(self):
        """to_jsonld should NOT affect to_dict output."""
        env = _software_envelope()
        d = env.to_dict()
        assert "@context" not in d
        assert "@type" not in d
        # to_dict uses asdict, includes all fields (even None)
        assert "issuer" in d

    def test_from_dict_still_works(self):
        env = _software_envelope()
        d = env.to_dict()
        restored = AttestationEnvelope.from_dict(d)
        assert restored.entity_id == env.entity_id

    def test_to_json_unchanged(self):
        env = _software_envelope()
        j = env.to_json()
        parsed = json.loads(j)
        assert "@context" not in parsed


# ── Context File Consistency (B2) ─────────────────────────────────


import pathlib

CONTEXT_FILE = (
    pathlib.Path(__file__).resolve().parents[3]
    / "schemas" / "contexts" / "attestation-envelope.jsonld"
)


class TestAttestationContextFileConsistency:
    """Verify attestation-envelope.jsonld covers all to_jsonld() output fields."""

    @pytest.fixture(autouse=True)
    def load_context(self):
        assert CONTEXT_FILE.exists(), f"Missing context file: {CONTEXT_FILE}"
        self.context = json.loads(CONTEXT_FILE.read_text())["@context"]

    def test_context_has_version(self):
        assert self.context.get("@version") == 1.1

    def test_context_has_web4_namespace(self):
        assert "web4" in self.context
        assert self.context["web4"] == "https://web4.io/ns/"

    def test_context_has_type_definition(self):
        assert "AttestationEnvelope" in self.context

    def test_who_fields_covered(self):
        who_keys = ["entity_id", "public_key", "public_key_fingerprint"]
        for key in who_keys:
            assert key in self.context, f"Missing WHO term: {key}"

    def test_anchor_fields_covered(self):
        anchor_keys = ["anchor", "type", "manufacturer", "model", "firmware_version"]
        for key in anchor_keys:
            assert key in self.context, f"Missing anchor term: {key}"

    def test_proof_fields_covered(self):
        proof_keys = [
            "proof", "format", "signature", "challenge",
            "attestation_object", "pcr_digest", "pcr_selection",
            "authenticator_data", "client_data_hash",
        ]
        for key in proof_keys:
            assert key in self.context, f"Missing proof term: {key}"

    def test_when_fields_covered(self):
        when_keys = ["timestamp", "challenge_issued_at", "challenge_ttl"]
        for key in when_keys:
            assert key in self.context, f"Missing WHEN term: {key}"

    def test_platform_state_fields_covered(self):
        ps_keys = [
            "platform_state", "available", "boot_verified",
            "pcr_values", "os_version", "kernel_version",
        ]
        for key in ps_keys:
            assert key in self.context, f"Missing platform_state term: {key}"

    def test_trust_and_metadata_fields_covered(self):
        meta_keys = ["trust_ceiling", "issuer", "purpose", "envelope_version"]
        for key in meta_keys:
            assert key in self.context, f"Missing metadata term: {key}"

    def test_software_envelope_all_keys_in_context(self):
        """All keys from a software envelope's to_jsonld() must be in context."""
        env = _software_envelope()
        doc = env.to_jsonld()
        self._check_keys(doc)

    def test_tpm2_envelope_all_keys_in_context(self):
        """All keys from a TPM2 envelope's to_jsonld() must be in context."""
        env = _tpm2_envelope()
        doc = env.to_jsonld()
        self._check_keys(doc)

    def test_full_envelope_all_keys_in_context(self):
        """Envelope with all optional fields populated."""
        env = _tpm2_envelope(
            issuer="lct://web4:ca",
            purpose="device_binding",
            platform_state=PlatformState(
                available=True,
                boot_verified=True,
                pcr_values={0: "aabb", 7: "ccdd"},
                os_version="Linux 6.8",
                kernel_version="6.8.0-106-generic",
            ),
        )
        doc = env.to_jsonld()
        self._check_keys(doc)

    def _check_keys(self, obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.startswith("@"):
                    continue
                # pcr_values uses numeric string keys — data, not terms
                if path.endswith("pcr_values"):
                    continue
                assert k in self.context, (
                    f"Key '{k}' (at {path}) not in context file"
                )
                self._check_keys(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for item in obj:
                self._check_keys(item, path)
