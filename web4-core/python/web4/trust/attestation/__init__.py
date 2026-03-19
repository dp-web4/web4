"""
Attestation Envelope — Unified hardware trust primitive.

The dictionary entity for hardware trust. All three repos (Web4, SAGE,
Hardbound) use this same envelope shape regardless of hardware anchor type.

Usage:
    from web4.trust.attestation import AttestationEnvelope, AnchorInfo, Proof

    envelope = AttestationEnvelope(
        entity_id="lct://sage:cbp:agent@raising",
        public_key="...",
        anchor=AnchorInfo(type="tpm2"),
        proof=Proof(format="tpm2_quote", signature="...", challenge="..."),
    )
"""

from web4.trust.attestation.envelope import (
    AttestationEnvelope,
    AnchorInfo,
    Proof,
    PlatformState,
    VerificationResult,
    TRUST_CEILINGS,
)

__all__ = [
    'AttestationEnvelope',
    'AnchorInfo',
    'Proof',
    'PlatformState',
    'VerificationResult',
    'TRUST_CEILINGS',
]
