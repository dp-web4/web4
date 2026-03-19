"""
AttestationEnvelope — the canonical data structure for hardware-backed trust.

One shape, any anchor type. The verifier sees the same envelope regardless
of whether the proof came from TPM 2.0, FIDO2/YubiKey, Secure Enclave,
or a software fallback.

Patent alignment: US 11,477,027 / US 12,278,913 / US App 19/178,619
Spec: web4/docs/specs/attestation-envelope.md
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List
from hashlib import sha256
import time
import json


# Trust ceilings by anchor type — max trust an anchor can provide
TRUST_CEILINGS = {
    'tpm2': 1.0,          # Hardware-bound, non-exportable, measured boot
    'tpm2_no_pcr': 0.85,  # Hardware-bound but boot state not verified
    'fido2': 0.9,         # Hardware-bound, user-presence, no platform state
    'secure_enclave': 0.85,  # Hardware-backed, attestation format varies
    'software': 0.4,      # Filesystem key — copyable, no hardware binding
}

# Freshness max age by purpose (seconds)
FRESHNESS_MAX_AGE = {
    'session_start': 8 * 3600,     # 8 hours
    're_attestation': 24 * 3600,   # 24 hours
    'witness': 3600,               # 1 hour
    'enrollment': None,            # One-time, verified at creation
    'migration': 3600,             # 1 hour — migrations are time-sensitive
}


@dataclass
class AnchorInfo:
    """Hardware anchor metadata."""
    type: str                        # 'tpm2' | 'fido2' | 'secure_enclave' | 'software'
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None


@dataclass
class Proof:
    """Cryptographic proof from the hardware anchor."""
    format: str                      # 'tpm2_quote' | 'fido2_assertion' | 'se_attestation' | 'ecdsa_software'
    signature: str                   # Base64-encoded signature over challenge
    challenge: str                   # The nonce that was signed

    # Optional anchor-specific fields
    attestation_object: Optional[str] = None  # Raw attestation (Base64)

    # TPM-specific
    pcr_digest: Optional[str] = None          # SHA-256 of selected PCRs
    pcr_selection: Optional[List[int]] = None # Which PCRs included

    # FIDO2-specific
    authenticator_data: Optional[str] = None  # CBOR authenticator data
    client_data_hash: Optional[str] = None


@dataclass
class PlatformState:
    """Platform boot/runtime state (when available)."""
    available: bool = False
    boot_verified: Optional[bool] = None
    pcr_values: Optional[Dict[int, str]] = None  # PCR index → hex digest
    os_version: Optional[str] = None
    kernel_version: Optional[str] = None


@dataclass
class AttestationEnvelope:
    """
    Unified attestation envelope — the dictionary entity for hardware trust.

    Producers: SAGE instances, Hardbound actors, Web4 entities
    Consumers: Any verifier (federation peers, governance controllers, trust computation)

    The envelope normalizes across hardware types so consumers never need
    to know which hardware produced it.
    """

    # === WHO ===
    entity_id: str                    # LCT ID
    public_key: str                   # PEM or JWK
    public_key_fingerprint: str = ''  # SHA-256 of public key

    # === WHAT ===
    anchor: AnchorInfo = field(default_factory=lambda: AnchorInfo(type='software'))

    # === PROOF ===
    proof: Proof = field(default_factory=lambda: Proof(
        format='ecdsa_software', signature='', challenge=''))

    # === WHEN ===
    timestamp: float = field(default_factory=time.time)
    challenge_issued_at: float = 0.0
    challenge_ttl: float = 300.0      # 5 minutes default

    # === WHERE ===
    platform_state: PlatformState = field(default_factory=PlatformState)

    # === TRUST ===
    trust_ceiling: float = 0.4        # Default to software ceiling

    # === METADATA ===
    envelope_version: str = '0.1'
    issuer: Optional[str] = None      # Machine name or instance ID
    purpose: Optional[str] = None     # 'enrollment' | 'session_start' | etc.

    def __post_init__(self):
        """Compute derived fields."""
        if not self.public_key_fingerprint and self.public_key:
            self.public_key_fingerprint = sha256(
                self.public_key.encode('utf-8')
            ).hexdigest()[:16]

        if self.trust_ceiling == 0.4 and self.anchor.type != 'software':
            # Auto-set ceiling from anchor type
            anchor_key = self.anchor.type
            if anchor_key == 'tpm2' and self.proof.pcr_digest:
                anchor_key = 'tpm2'
            elif anchor_key == 'tpm2':
                anchor_key = 'tpm2_no_pcr'
            self.trust_ceiling = TRUST_CEILINGS.get(anchor_key, 0.4)

    @property
    def is_fresh(self) -> bool:
        """Check if this attestation is still within its freshness window."""
        max_age = FRESHNESS_MAX_AGE.get(self.purpose or 'session_start')
        if max_age is None:
            return True  # Enrollment — no expiry
        return (time.time() - self.timestamp) < max_age

    @property
    def freshness_factor(self) -> float:
        """Freshness decay: 1.0 (just created) → 0.0 (expired)."""
        max_age = FRESHNESS_MAX_AGE.get(self.purpose or 'session_start')
        if max_age is None:
            return 1.0
        age = time.time() - self.timestamp
        return max(0.0, 1.0 - age / max_age)

    @property
    def effective_trust(self) -> float:
        """Trust ceiling × freshness decay."""
        return self.trust_ceiling * self.freshness_factor

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict) -> 'AttestationEnvelope':
        """Deserialize from dictionary."""
        data = dict(data)
        if 'anchor' in data and isinstance(data['anchor'], dict):
            data['anchor'] = AnchorInfo(**data['anchor'])
        if 'proof' in data and isinstance(data['proof'], dict):
            data['proof'] = Proof(**data['proof'])
        if 'platform_state' in data and isinstance(data['platform_state'], dict):
            data['platform_state'] = PlatformState(**data['platform_state'])
        return cls(**{k: v for k, v in data.items()
                      if k in cls.__dataclass_fields__})

    @classmethod
    def from_json(cls, json_str: str) -> 'AttestationEnvelope':
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class VerificationResult:
    """Result of verifying an attestation envelope."""
    valid: bool
    trust_ceiling: float
    effective_trust: float
    fresh: bool
    reason: str = ''                  # Human-readable explanation
    anchor_verified: bool = False     # Whether hardware-specific verification passed
    platform_state_ok: Optional[bool] = None  # Whether platform state matches policy


# === Self-test ===

if __name__ == '__main__':
    # Create a software-only attestation (simplest case)
    envelope = AttestationEnvelope(
        entity_id='lct://sage:cbp:agent@raising',
        public_key='-----BEGIN PUBLIC KEY-----\nMFkw...\n-----END PUBLIC KEY-----',
        anchor=AnchorInfo(type='software'),
        proof=Proof(
            format='ecdsa_software',
            signature='base64sig...',
            challenge='random-nonce-123',
        ),
        purpose='session_start',
        issuer='cbp',
    )

    print(f'Entity: {envelope.entity_id}')
    print(f'Anchor: {envelope.anchor.type}')
    print(f'Trust ceiling: {envelope.trust_ceiling}')
    print(f'Fresh: {envelope.is_fresh}')
    print(f'Freshness factor: {envelope.freshness_factor:.3f}')
    print(f'Effective trust: {envelope.effective_trust:.3f}')
    print(f'Fingerprint: {envelope.public_key_fingerprint}')
    print()

    # Round-trip serialization
    json_str = envelope.to_json()
    restored = AttestationEnvelope.from_json(json_str)
    assert restored.entity_id == envelope.entity_id
    assert restored.trust_ceiling == envelope.trust_ceiling
    print('Serialization round-trip: OK')
    print()

    # TPM attestation (higher trust)
    tpm_envelope = AttestationEnvelope(
        entity_id='lct://sage:thor:agent@raising',
        public_key='-----BEGIN PUBLIC KEY-----\nMFkw...\n-----END PUBLIC KEY-----',
        anchor=AnchorInfo(type='tpm2', manufacturer='Infineon'),
        proof=Proof(
            format='tpm2_quote',
            signature='base64tpmsig...',
            challenge='tpm-nonce-456',
            pcr_digest='abcdef1234567890',
            pcr_selection=[0, 1, 2, 7],
        ),
        platform_state=PlatformState(
            available=True,
            boot_verified=True,
            pcr_values={0: 'aabb...', 1: 'ccdd...', 2: 'eeff...', 7: '1122...'},
        ),
        purpose='enrollment',
        issuer='thor',
    )

    print(f'TPM Entity: {tpm_envelope.entity_id}')
    print(f'TPM Anchor: {tpm_envelope.anchor.type} ({tpm_envelope.anchor.manufacturer})')
    print(f'TPM Trust ceiling: {tpm_envelope.trust_ceiling}')
    print(f'TPM PCR digest: {tpm_envelope.proof.pcr_digest}')
    print(f'TPM Boot verified: {tpm_envelope.platform_state.boot_verified}')
    print(f'TPM Effective trust: {tpm_envelope.effective_trust:.3f}')
    print()

    print('=== All self-tests passed ===')
