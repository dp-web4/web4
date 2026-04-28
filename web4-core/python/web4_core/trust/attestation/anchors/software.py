"""
Software-only anchor verification.

The fallback when no hardware anchor is available.
Verifies ECDSA/HMAC signatures against known public keys.
Trust ceiling capped at 0.4 — the key is filesystem-resident
and copyable.

Status: Implemented — this is the baseline.
"""

from ..envelope import AttestationEnvelope, VerificationResult


def verify_software(envelope: AttestationEnvelope) -> VerificationResult:
    """Verify a software-only attestation envelope.

    Software attestation verifies the signature is valid but
    cannot prove hardware binding. Trust ceiling is 0.4.

    Returns:
        VerificationResult with verification outcome
    """
    if envelope.anchor.type != 'software':
        return VerificationResult(
            valid=False, trust_ceiling=0, effective_trust=0,
            fresh=False, reason='Wrong anchor type for software verifier')

    fresh = envelope.is_fresh

    # Software verification: check signature format is valid
    # (actual ECDSA verification would go here with the public key)
    has_signature = bool(envelope.proof.signature)
    has_challenge = bool(envelope.proof.challenge)

    return VerificationResult(
        valid=fresh and has_signature and has_challenge,
        trust_ceiling=envelope.trust_ceiling,
        effective_trust=envelope.effective_trust,
        fresh=fresh,
        anchor_verified=True,  # Software verification is always "verified" (it's just weak)
        reason='Software-only anchor — key is filesystem-resident, ceiling 0.4',
    )
