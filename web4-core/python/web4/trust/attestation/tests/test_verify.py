"""
Tests for verify_envelope() dispatch and anchor verifiers — H2: Sprint 2.

Covers: dispatch routing, challenge verification, software verifier (end-to-end),
TPM2/FIDO2/SE stub verifiers, unknown anchor type, edge cases.
"""

import time
import pytest

from web4.trust.attestation.envelope import (
    AttestationEnvelope,
    AnchorInfo,
    Proof,
    PlatformState,
    VerificationResult,
)
from web4.trust.attestation.verify import verify_envelope
from web4.trust.attestation.anchors.software import verify_software
from web4.trust.attestation.anchors.tpm2 import verify_tpm2, create_tpm2_attestation
from web4.trust.attestation.anchors.fido2 import verify_fido2
from web4.trust.attestation.anchors.secure_enclave import verify_secure_enclave


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _fresh_software_envelope(challenge='nonce-123'):
    return AttestationEnvelope(
        entity_id='lct://test:sw@session',
        public_key='test-key',
        anchor=AnchorInfo(type='software'),
        proof=Proof(format='ecdsa_software', signature='base64sig', challenge=challenge),
        purpose='session_start',
    )


def _fresh_tpm2_envelope(challenge='tpm-nonce', with_pcr=True):
    proof_kwargs = dict(format='tpm2_quote', signature='tpmsig', challenge=challenge)
    if with_pcr:
        proof_kwargs['pcr_digest'] = 'abcdef'
        proof_kwargs['pcr_selection'] = [0, 1, 7]

    return AttestationEnvelope(
        entity_id='lct://test:tpm@session',
        public_key='tpm-key',
        anchor=AnchorInfo(type='tpm2', manufacturer='Infineon'),
        proof=Proof(**proof_kwargs),
        platform_state=PlatformState(
            available=True, boot_verified=True,
            pcr_values={0: 'aa', 1: 'bb', 7: 'cc'},
        ) if with_pcr else PlatformState(),
        purpose='session_start',
    )


def _fresh_fido2_envelope(challenge='fido-nonce'):
    return AttestationEnvelope(
        entity_id='lct://test:fido@session',
        public_key='fido-key',
        anchor=AnchorInfo(type='fido2'),
        proof=Proof(
            format='fido2_assertion', signature='fidosig', challenge=challenge,
            authenticator_data='auth-data', client_data_hash='client-hash',
        ),
        purpose='session_start',
    )


def _fresh_se_envelope(challenge='se-nonce'):
    return AttestationEnvelope(
        entity_id='lct://test:se@session',
        public_key='se-key',
        anchor=AnchorInfo(type='secure_enclave'),
        proof=Proof(format='se_attestation', signature='sesig', challenge=challenge),
        purpose='session_start',
    )


# ---------------------------------------------------------------------------
# Dispatch Routing
# ---------------------------------------------------------------------------

class TestDispatch:
    """verify_envelope() routes to the correct anchor verifier."""

    def test_dispatch_software(self):
        env = _fresh_software_envelope()
        result = verify_envelope(env)
        assert result.valid is True
        assert 'Software-only' in result.reason or 'software' in result.reason.lower()

    def test_dispatch_tpm2(self):
        env = _fresh_tpm2_envelope()
        result = verify_envelope(env)
        assert result.valid is True
        assert 'TPM2' in result.reason or 'tpm' in result.reason.lower()

    def test_dispatch_fido2(self):
        env = _fresh_fido2_envelope()
        result = verify_envelope(env)
        assert result.valid is True
        assert 'FIDO2' in result.reason or 'fido' in result.reason.lower()

    def test_dispatch_secure_enclave(self):
        env = _fresh_se_envelope()
        result = verify_envelope(env)
        assert result.valid is True
        assert 'Secure Enclave' in result.reason or 'SE' in result.reason

    def test_dispatch_unknown_anchor(self):
        env = AttestationEnvelope(
            entity_id='test', public_key='key',
            anchor=AnchorInfo(type='quantum_crystal'),
            proof=Proof(format='quantum', signature='q', challenge='c'),
        )
        result = verify_envelope(env)
        assert result.valid is False
        assert 'Unknown anchor type' in result.reason

    def test_returns_verification_result(self):
        env = _fresh_software_envelope()
        result = verify_envelope(env)
        assert isinstance(result, VerificationResult)


# ---------------------------------------------------------------------------
# Challenge Verification
# ---------------------------------------------------------------------------

class TestChallengeVerification:
    """Challenge matching in verify_envelope()."""

    def test_matching_challenge_passes(self):
        env = _fresh_software_envelope(challenge='my-nonce')
        result = verify_envelope(env, expected_challenge='my-nonce')
        assert result.valid is True

    def test_mismatched_challenge_fails(self):
        env = _fresh_software_envelope(challenge='nonce-A')
        result = verify_envelope(env, expected_challenge='nonce-B')
        assert result.valid is False
        assert 'Challenge mismatch' in result.reason

    def test_no_expected_challenge_skips_check(self):
        """When expected_challenge is empty, challenge check is skipped."""
        env = _fresh_software_envelope(challenge='anything')
        result = verify_envelope(env, expected_challenge='')
        assert result.valid is True

    def test_no_expected_challenge_default(self):
        """Default is no challenge check."""
        env = _fresh_software_envelope()
        result = verify_envelope(env)
        assert result.valid is True

    def test_challenge_mismatch_returns_zero_trust(self):
        env = _fresh_software_envelope(challenge='a')
        result = verify_envelope(env, expected_challenge='b')
        assert result.effective_trust == 0
        assert result.fresh is False


# ---------------------------------------------------------------------------
# Software Verifier (End-to-End)
# ---------------------------------------------------------------------------

class TestSoftwareVerifier:
    """The only fully implemented verifier — test end-to-end behavior."""

    def test_valid_fresh_software(self):
        env = _fresh_software_envelope()
        result = verify_software(env)
        assert result.valid is True
        assert result.trust_ceiling == 0.4
        assert result.fresh is True
        assert result.anchor_verified is True

    def test_expired_software(self):
        env = _fresh_software_envelope()
        env.timestamp = 0.0  # Very old
        result = verify_software(env)
        assert result.valid is False
        assert result.fresh is False

    def test_missing_signature(self):
        env = _fresh_software_envelope()
        env.proof.signature = ''
        result = verify_software(env)
        assert result.valid is False

    def test_missing_challenge(self):
        env = _fresh_software_envelope()
        env.proof.challenge = ''
        result = verify_software(env)
        assert result.valid is False

    def test_wrong_anchor_type(self):
        env = _fresh_tpm2_envelope()
        result = verify_software(env)
        assert result.valid is False
        assert 'Wrong anchor type' in result.reason

    def test_effective_trust_bounded_by_software_ceiling(self):
        env = _fresh_software_envelope()
        result = verify_software(env)
        assert result.effective_trust <= 0.4


# ---------------------------------------------------------------------------
# TPM2 Verifier (Stub)
# ---------------------------------------------------------------------------

class TestTPM2Verifier:
    """TPM2 verifier stub behavior."""

    def test_valid_fresh_tpm2(self):
        env = _fresh_tpm2_envelope()
        result = verify_tpm2(env)
        assert result.valid is True
        assert result.trust_ceiling == 1.0
        assert result.fresh is True
        assert result.anchor_verified is False  # Stub — hardware verification pending

    def test_tpm2_no_pcr_ceiling(self):
        env = _fresh_tpm2_envelope(with_pcr=False)
        result = verify_tpm2(env)
        assert result.valid is True
        assert result.trust_ceiling == 0.85

    def test_pcr_validation_pass(self):
        env = _fresh_tpm2_envelope()
        expected_pcrs = {0: 'aa', 1: 'bb', 7: 'cc'}
        result = verify_tpm2(env, expected_pcrs=expected_pcrs)
        assert result.valid is True
        assert result.platform_state_ok is True

    def test_pcr_validation_fail(self):
        env = _fresh_tpm2_envelope()
        expected_pcrs = {0: 'aa', 1: 'bb', 7: 'WRONG'}
        result = verify_tpm2(env, expected_pcrs=expected_pcrs)
        assert result.valid is False
        assert result.platform_state_ok is False

    def test_wrong_anchor_type(self):
        env = _fresh_software_envelope()
        result = verify_tpm2(env)
        assert result.valid is False
        assert 'Wrong anchor type' in result.reason

    def test_expired_tpm2(self):
        env = _fresh_tpm2_envelope()
        env.timestamp = 0.0
        result = verify_tpm2(env)
        assert result.valid is False

    def test_create_tpm2_attestation_returns_none(self):
        """Stub creation should return None (not yet implemented)."""
        result = create_tpm2_attestation('lct://test', 'challenge')
        assert result is None


# ---------------------------------------------------------------------------
# FIDO2 Verifier (Stub)
# ---------------------------------------------------------------------------

class TestFIDO2Verifier:
    """FIDO2 verifier stub behavior."""

    def test_valid_fresh_fido2(self):
        env = _fresh_fido2_envelope()
        result = verify_fido2(env)
        assert result.valid is True
        assert result.trust_ceiling == 0.9
        assert result.anchor_verified is False  # Stub

    def test_wrong_anchor_type(self):
        env = _fresh_software_envelope()
        result = verify_fido2(env)
        assert result.valid is False
        assert 'Wrong anchor type' in result.reason

    def test_expired_fido2(self):
        env = _fresh_fido2_envelope()
        env.timestamp = 0.0
        result = verify_fido2(env)
        assert result.valid is False
        assert result.fresh is False


# ---------------------------------------------------------------------------
# Secure Enclave Verifier (Stub)
# ---------------------------------------------------------------------------

class TestSecureEnclaveVerifier:
    """Secure Enclave verifier stub behavior."""

    def test_valid_fresh_se(self):
        env = _fresh_se_envelope()
        result = verify_secure_enclave(env)
        assert result.valid is True
        assert result.trust_ceiling == 0.85
        assert result.anchor_verified is False  # Stub

    def test_wrong_anchor_type(self):
        env = _fresh_software_envelope()
        result = verify_secure_enclave(env)
        assert result.valid is False
        assert 'Wrong anchor type' in result.reason

    def test_expired_se(self):
        env = _fresh_se_envelope()
        env.timestamp = 0.0
        result = verify_secure_enclave(env)
        assert result.valid is False


# ---------------------------------------------------------------------------
# Cross-Anchor Consistency
# ---------------------------------------------------------------------------

class TestCrossAnchorConsistency:
    """Properties that should hold across all anchor types."""

    @pytest.mark.parametrize("make_env,anchor_type", [
        (_fresh_software_envelope, 'software'),
        (_fresh_tpm2_envelope, 'tpm2'),
        (_fresh_fido2_envelope, 'fido2'),
        (_fresh_se_envelope, 'secure_enclave'),
    ])
    def test_fresh_envelope_is_valid(self, make_env, anchor_type):
        """Every fresh envelope should pass its own verifier."""
        env = make_env()
        result = verify_envelope(env)
        assert result.valid is True, f"{anchor_type} fresh envelope invalid: {result.reason}"

    @pytest.mark.parametrize("make_env,anchor_type", [
        (_fresh_software_envelope, 'software'),
        (_fresh_tpm2_envelope, 'tpm2'),
        (_fresh_fido2_envelope, 'fido2'),
        (_fresh_se_envelope, 'secure_enclave'),
    ])
    def test_expired_envelope_is_invalid(self, make_env, anchor_type):
        """Every expired envelope should fail verification."""
        env = make_env()
        env.timestamp = 0.0  # Very old
        result = verify_envelope(env)
        assert result.valid is False, f"{anchor_type} expired envelope still valid"

    @pytest.mark.parametrize("make_env,anchor_type", [
        (_fresh_software_envelope, 'software'),
        (_fresh_tpm2_envelope, 'tpm2'),
        (_fresh_fido2_envelope, 'fido2'),
        (_fresh_se_envelope, 'secure_enclave'),
    ])
    def test_result_has_trust_fields(self, make_env, anchor_type):
        """Every result should populate trust_ceiling and effective_trust."""
        env = make_env()
        result = verify_envelope(env)
        assert result.trust_ceiling > 0
        assert result.effective_trust > 0
        assert result.effective_trust <= result.trust_ceiling
