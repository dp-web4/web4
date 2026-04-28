"""
Unified attestation verification.

Dispatches to anchor-specific verification modules based on the
envelope's anchor type. Consumers call verify_envelope() without
needing to know which hardware produced the attestation.
"""

from .envelope import AttestationEnvelope, VerificationResult


def verify_envelope(envelope: AttestationEnvelope,
                    expected_challenge: str = '',
                    **kwargs) -> VerificationResult:
    """Verify an attestation envelope.

    Dispatches to the appropriate anchor-specific verifier.
    Consumers call this — never the anchor modules directly.

    Args:
        envelope: The attestation envelope to verify
        expected_challenge: The challenge the verifier issued (for freshness)
        **kwargs: Anchor-specific arguments (e.g., expected_pcrs for TPM2)

    Returns:
        VerificationResult with the verification outcome
    """
    # Challenge verification
    if expected_challenge and envelope.proof.challenge != expected_challenge:
        return VerificationResult(
            valid=False,
            trust_ceiling=envelope.trust_ceiling,
            effective_trust=0,
            fresh=False,
            reason=f'Challenge mismatch: expected {expected_challenge[:8]}..., '
                   f'got {envelope.proof.challenge[:8]}...',
        )

    # Dispatch to anchor-specific verifier
    anchor_type = envelope.anchor.type

    if anchor_type == 'tpm2':
        from .anchors.tpm2 import verify_tpm2
        return verify_tpm2(envelope, **kwargs)
    elif anchor_type == 'fido2':
        from .anchors.fido2 import verify_fido2
        return verify_fido2(envelope, **kwargs)
    elif anchor_type == 'secure_enclave':
        from .anchors.secure_enclave import verify_secure_enclave
        return verify_secure_enclave(envelope, **kwargs)
    elif anchor_type == 'software':
        from .anchors.software import verify_software
        return verify_software(envelope, **kwargs)
    else:
        return VerificationResult(
            valid=False,
            trust_ceiling=0,
            effective_trust=0,
            fresh=False,
            reason=f'Unknown anchor type: {anchor_type}',
        )
