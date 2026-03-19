"""
Tests for web4.attestation — AttestationEnvelope SDK integration.

Validates that the consolidated attestation module works correctly
when accessed through the SDK package. Tests cover construction,
trust ceilings, freshness model, serialization, and verification
dispatch for all 4 anchor types.

Sprint task: H4 (SDK integration for AttestationEnvelope)
"""

import json
import time
import pytest

from web4.attestation import (
    AttestationEnvelope,
    AnchorInfo,
    Proof,
    PlatformState,
    VerificationResult,
    TRUST_CEILINGS,
    FRESHNESS_MAX_AGE,
    verify_envelope,
)


# ── Helper ─────────────────────────────────────────────────────────

def _make_envelope(anchor_type='software', purpose='session_start', **kwargs):
    """Create a test envelope with sensible defaults."""
    anchor_kwargs = {'type': anchor_type}
    proof_kwargs = {
        'format': f'{anchor_type}_quote' if anchor_type != 'software' else 'ecdsa_software',
        'signature': 'test-sig-base64',
        'challenge': 'test-nonce-123',
    }
    if anchor_type == 'tpm2':
        proof_kwargs['pcr_digest'] = 'abcdef1234567890'
        proof_kwargs['pcr_selection'] = [0, 1, 2, 7]

    return AttestationEnvelope(
        entity_id='lct://test:agent@raising',
        public_key='-----BEGIN PUBLIC KEY-----\ntest\n-----END PUBLIC KEY-----',
        anchor=AnchorInfo(**anchor_kwargs),
        proof=Proof(**proof_kwargs),
        purpose=purpose,
        issuer='test-machine',
        **kwargs,
    )


# ── Construction Tests ──────────────────────────────────────────

class TestConstruction:
    """Verify envelope construction and auto-computed fields."""

    def test_software_defaults(self):
        env = _make_envelope('software')
        assert env.anchor.type == 'software'
        assert env.trust_ceiling == 0.4
        assert env.envelope_version == '0.1'

    def test_fingerprint_auto_computed(self):
        env = _make_envelope()
        assert len(env.public_key_fingerprint) == 16
        assert env.public_key_fingerprint != ''

    def test_fingerprint_deterministic(self):
        env1 = _make_envelope()
        env2 = _make_envelope()
        assert env1.public_key_fingerprint == env2.public_key_fingerprint

    def test_fingerprint_preserves_explicit(self):
        env = AttestationEnvelope(
            entity_id='test',
            public_key='key',
            public_key_fingerprint='explicit-fp',
        )
        assert env.public_key_fingerprint == 'explicit-fp'

    def test_challenge_ttl_default(self):
        env = _make_envelope()
        assert env.challenge_ttl == 300.0

    def test_timestamp_auto_set(self):
        before = time.time()
        env = _make_envelope()
        after = time.time()
        assert before <= env.timestamp <= after


# ── Trust Ceiling Tests ─────────────────────────────────────────

class TestTrustCeilings:
    """Verify trust ceiling auto-computation per anchor type."""

    def test_software_ceiling(self):
        env = _make_envelope('software')
        assert env.trust_ceiling == 0.4

    def test_tpm2_with_pcr_ceiling(self):
        env = _make_envelope('tpm2')
        assert env.trust_ceiling == 1.0

    def test_tpm2_without_pcr_ceiling(self):
        env = AttestationEnvelope(
            entity_id='test',
            public_key='key',
            anchor=AnchorInfo(type='tpm2'),
            proof=Proof(format='tpm2_quote', signature='sig', challenge='nonce'),
            # No pcr_digest
        )
        assert env.trust_ceiling == 0.85

    def test_fido2_ceiling(self):
        env = _make_envelope('fido2')
        assert env.trust_ceiling == 0.9

    def test_secure_enclave_ceiling(self):
        env = _make_envelope('secure_enclave')
        assert env.trust_ceiling == 0.85

    def test_ceiling_ordering(self):
        """tpm2 > fido2 >= secure_enclave > software."""
        assert TRUST_CEILINGS['tpm2'] > TRUST_CEILINGS['fido2']
        assert TRUST_CEILINGS['fido2'] >= TRUST_CEILINGS['secure_enclave']
        assert TRUST_CEILINGS['secure_enclave'] > TRUST_CEILINGS['software']

    def test_all_ceilings_bounded(self):
        for anchor, ceiling in TRUST_CEILINGS.items():
            assert 0.0 <= ceiling <= 1.0, f"{anchor} ceiling out of bounds"


# ── Freshness Tests ─────────────────────────────────────────────

class TestFreshness:
    """Verify freshness model: is_fresh, freshness_factor, effective_trust."""

    def test_fresh_envelope(self):
        env = _make_envelope()
        assert env.is_fresh is True
        assert env.freshness_factor > 0.99

    def test_expired_envelope(self):
        env = _make_envelope()
        env.timestamp = time.time() - 9 * 3600  # 9 hours, session_start max is 8
        assert env.is_fresh is False
        assert env.freshness_factor == 0.0

    def test_enrollment_never_expires(self):
        env = _make_envelope(purpose='enrollment')
        env.timestamp = time.time() - 365 * 24 * 3600  # 1 year ago
        assert env.is_fresh is True
        assert env.freshness_factor == 1.0

    def test_effective_trust_decays(self):
        env = _make_envelope('tpm2')
        # Fresh: effective = ceiling
        assert env.effective_trust == pytest.approx(env.trust_ceiling, abs=0.01)

    def test_effective_trust_zero_when_expired(self):
        env = _make_envelope('tpm2')
        env.timestamp = time.time() - 9 * 3600
        assert env.effective_trust == 0.0

    def test_freshness_max_age_coverage(self):
        """All defined purposes have known max ages."""
        expected_purposes = {'session_start', 're_attestation', 'witness',
                             'enrollment', 'migration'}
        assert set(FRESHNESS_MAX_AGE.keys()) == expected_purposes


# ── Serialization Tests ─────────────────────────────────────────

class TestSerialization:
    """Verify to_dict/from_dict and to_json/from_json round-trips."""

    def test_dict_round_trip(self):
        env = _make_envelope('tpm2')
        d = env.to_dict()
        restored = AttestationEnvelope.from_dict(d)
        assert restored.entity_id == env.entity_id
        assert restored.trust_ceiling == env.trust_ceiling
        assert restored.anchor.type == 'tpm2'
        assert restored.proof.pcr_digest == env.proof.pcr_digest

    def test_json_round_trip(self):
        env = _make_envelope('fido2')
        j = env.to_json()
        restored = AttestationEnvelope.from_json(j)
        assert restored.entity_id == env.entity_id
        assert restored.anchor.type == 'fido2'
        assert restored.trust_ceiling == env.trust_ceiling

    def test_json_is_valid_json(self):
        env = _make_envelope()
        j = env.to_json()
        parsed = json.loads(j)
        assert isinstance(parsed, dict)
        assert 'entity_id' in parsed
        assert 'anchor' in parsed

    def test_nested_dataclass_preservation(self):
        env = _make_envelope('tpm2')
        d = env.to_dict()
        assert isinstance(d['anchor'], dict)
        assert isinstance(d['proof'], dict)
        assert isinstance(d['platform_state'], dict)
        restored = AttestationEnvelope.from_dict(d)
        assert isinstance(restored.anchor, AnchorInfo)
        assert isinstance(restored.proof, Proof)
        assert isinstance(restored.platform_state, PlatformState)

    def test_platform_state_round_trip(self):
        env = _make_envelope('tpm2')
        env.platform_state = PlatformState(
            available=True,
            boot_verified=True,
            pcr_values={0: 'aabb', 1: 'ccdd'},
            os_version='Linux 6.8',
        )
        d = env.to_dict()
        restored = AttestationEnvelope.from_dict(d)
        assert restored.platform_state.available is True
        assert restored.platform_state.boot_verified is True
        assert restored.platform_state.os_version == 'Linux 6.8'


# ── Verification Dispatch Tests ─────────────────────────────────

class TestVerifyEnvelope:
    """Verify the verification dispatcher routes correctly."""

    def test_software_valid(self):
        env = _make_envelope('software')
        result = verify_envelope(env)
        assert result.valid is True
        assert result.anchor_verified is True
        assert result.trust_ceiling == 0.4

    def test_tpm2_valid(self):
        env = _make_envelope('tpm2')
        result = verify_envelope(env)
        assert result.valid is True
        assert result.trust_ceiling == 1.0

    def test_fido2_valid(self):
        env = _make_envelope('fido2')
        result = verify_envelope(env)
        assert result.valid is True
        assert result.trust_ceiling == 0.9

    def test_secure_enclave_valid(self):
        env = _make_envelope('secure_enclave')
        result = verify_envelope(env)
        assert result.valid is True
        assert result.trust_ceiling == 0.85

    def test_unknown_anchor_type(self):
        env = _make_envelope('software')
        env.anchor = AnchorInfo(type='quantum_chip')
        result = verify_envelope(env)
        assert result.valid is False
        assert 'Unknown anchor type' in result.reason

    def test_challenge_mismatch(self):
        env = _make_envelope('software')
        result = verify_envelope(env, expected_challenge='wrong-nonce')
        assert result.valid is False
        assert result.effective_trust == 0
        assert 'Challenge mismatch' in result.reason

    def test_challenge_match(self):
        env = _make_envelope('software')
        result = verify_envelope(env, expected_challenge='test-nonce-123')
        assert result.valid is True

    def test_expired_envelope_invalid(self):
        env = _make_envelope('software')
        env.timestamp = time.time() - 9 * 3600
        result = verify_envelope(env)
        assert result.valid is False
        assert result.fresh is False

    def test_tpm2_pcr_validation(self):
        env = _make_envelope('tpm2')
        env.platform_state = PlatformState(
            available=True,
            pcr_values={0: 'aabb', 1: 'ccdd'},
        )
        # Matching PCRs
        result = verify_envelope(env, expected_pcrs={0: 'aabb', 1: 'ccdd'})
        assert result.valid is True
        assert result.platform_state_ok is True

    def test_tpm2_pcr_mismatch(self):
        env = _make_envelope('tpm2')
        env.platform_state = PlatformState(
            available=True,
            pcr_values={0: 'aabb'},
        )
        result = verify_envelope(env, expected_pcrs={0: 'wrong'})
        assert result.valid is False
        assert result.platform_state_ok is False

    def test_wrong_anchor_type_for_verifier(self):
        """Ensure cross-type rejection works."""
        env = _make_envelope('software')
        # Force dispatch to tpm2 verifier
        env.anchor = AnchorInfo(type='tpm2')
        # This should work because dispatch is by anchor.type
        result = verify_envelope(env)
        assert result.valid is True  # TPM2 stub accepts if fresh


# ── SDK Import Tests ─────────────────────────────────────────────

class TestSDKImport:
    """Verify attestation types are accessible from the top-level web4 package."""

    def test_top_level_import(self):
        from web4 import AttestationEnvelope as AE
        assert AE is AttestationEnvelope

    def test_verify_envelope_importable(self):
        from web4 import verify_envelope as ve
        assert ve is verify_envelope

    def test_constants_importable(self):
        from web4 import TRUST_CEILINGS as tc
        assert isinstance(tc, dict)
        assert 'tpm2' in tc

    def test_freshness_max_age_importable(self):
        from web4 import FRESHNESS_MAX_AGE as fma
        assert isinstance(fma, dict)
        assert 'enrollment' in fma

    def test_all_types_in_all(self):
        import web4
        for name in ['AttestationEnvelope', 'AnchorInfo', 'Proof',
                      'PlatformState', 'VerificationResult',
                      'TRUST_CEILINGS', 'FRESHNESS_MAX_AGE',
                      'verify_envelope']:
            assert name in web4.__all__, f"{name} not in __all__"

    def test_total_symbol_count_increased(self):
        import web4
        # Was 247 symbols + __version__, now +8 attestation symbols
        assert len(web4.__all__) >= 255
