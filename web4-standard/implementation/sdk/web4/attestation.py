"""
Web4 AttestationEnvelope — unified hardware trust primitive.

One shape, any anchor type. The verifier sees the same envelope regardless
of whether the proof came from TPM 2.0, FIDO2/YubiKey, Secure Enclave,
or a software fallback.

This module consolidates the attestation types from web4-core into the SDK
for unified access. Decision documented in SPRINT.md (H4).

Key types:
- AttestationEnvelope: the canonical attestation data structure
- AnchorInfo: hardware anchor metadata (type, manufacturer, model)
- Proof: cryptographic proof from the anchor (signature, challenge)
- PlatformState: boot/runtime state (PCR values, OS info)
- VerificationResult: outcome of verifying an envelope
- verify_envelope: unified verification dispatcher

Trust ceilings by anchor type:
  tpm2 (with PCR): 1.0 | tpm2 (no PCR): 0.85 | fido2: 0.9
  secure_enclave: 0.85 | software: 0.4

Note: binding.py uses AnchorType.PHONE_SECURE_ELEMENT while this module
uses 'secure_enclave'. H5 will reconcile this naming for constellation
integration.

Patent alignment: US 11,477,027 / US 12,278,913 / US App 19/178,619
Spec: docs/specs/attestation-envelope.md
Source: web4-core/python/web4/trust/attestation/
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Optional, Dict, List
from hashlib import sha256
import time
import json

__all__ = [
    # Classes
    "AttestationEnvelope", "AnchorInfo", "Proof",
    "PlatformState", "VerificationResult",
    # Functions
    "verify_envelope",
    # Constants
    "ATTESTATION_JSONLD_CONTEXT", "TRUST_CEILINGS", "FRESHNESS_MAX_AGE",
]


# ── JSON-LD Context ──────────────────────────────────────────────

ATTESTATION_JSONLD_CONTEXT = "https://web4.io/contexts/attestation-envelope.jsonld"

# ── Trust Ceilings ────────────────────────────────────────────────

TRUST_CEILINGS: Dict[str, float] = {
    'tpm2': 1.0,          # Hardware-bound, non-exportable, measured boot
    'tpm2_no_pcr': 0.85,  # Hardware-bound but boot state not verified
    'fido2': 0.9,         # Hardware-bound, user-presence, no platform state
    'secure_enclave': 0.85,  # Hardware-backed, attestation format varies
    'software': 0.4,      # Filesystem key — copyable, no hardware binding
}

FRESHNESS_MAX_AGE: Dict[str, Optional[int]] = {
    'session_start': 8 * 3600,     # 8 hours
    're_attestation': 24 * 3600,   # 24 hours
    'witness': 3600,               # 1 hour
    'enrollment': None,            # One-time, verified at creation
    'migration': 3600,             # 1 hour — migrations are time-sensitive
}


# ── Data Types ────────────────────────────────────────────────────

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
    pcr_selection: Optional[List[int]] = None  # Which PCRs included

    # FIDO2-specific
    authenticator_data: Optional[str] = None  # CBOR authenticator data
    client_data_hash: Optional[str] = None


@dataclass
class PlatformState:
    """Platform boot/runtime state (when available)."""
    available: bool = False
    boot_verified: Optional[bool] = None
    pcr_values: Optional[Dict[int, str]] = None  # PCR index -> hex digest
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

    def __post_init__(self) -> None:
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
        """Freshness decay: 1.0 (just created) -> 0.0 (expired)."""
        max_age = FRESHNESS_MAX_AGE.get(self.purpose or 'session_start')
        if max_age is None:
            return 1.0
        age = time.time() - self.timestamp
        return max(0.0, 1.0 - age / max_age)

    @property
    def effective_trust(self) -> float:
        """Trust ceiling x freshness decay."""
        return self.trust_ceiling * self.freshness_factor

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AttestationEnvelope:
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
    def from_json(cls, json_str: str) -> AttestationEnvelope:
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))

    def to_jsonld(self) -> Dict[str, Any]:
        """
        Serialize to spec-compliant JSON-LD per attestation-envelope spec.

        Produces the canonical AttestationEnvelope document structure with:
        - @context header for JSON-LD processors
        - Spec-compliant field naming matching the TypeScript interface
        - Structured anchor, proof, and platform_state objects
        - Optional fields included only when populated
        """
        doc: Dict[str, Any] = {
            "@context": [ATTESTATION_JSONLD_CONTEXT],
            "@type": "AttestationEnvelope",
            "envelope_version": self.envelope_version,
        }

        # === WHO ===
        doc["entity_id"] = self.entity_id
        doc["public_key"] = self.public_key
        doc["public_key_fingerprint"] = self.public_key_fingerprint

        # === WHAT (anchor) ===
        anchor: Dict[str, Any] = {"type": self.anchor.type}
        if self.anchor.manufacturer:
            anchor["manufacturer"] = self.anchor.manufacturer
        if self.anchor.model:
            anchor["model"] = self.anchor.model
        if self.anchor.firmware_version:
            anchor["firmware_version"] = self.anchor.firmware_version
        doc["anchor"] = anchor

        # === PROOF ===
        proof: Dict[str, Any] = {
            "format": self.proof.format,
            "signature": self.proof.signature,
            "challenge": self.proof.challenge,
        }
        if self.proof.attestation_object:
            proof["attestation_object"] = self.proof.attestation_object
        if self.proof.pcr_digest:
            proof["pcr_digest"] = self.proof.pcr_digest
        if self.proof.pcr_selection:
            proof["pcr_selection"] = list(self.proof.pcr_selection)
        if self.proof.authenticator_data:
            proof["authenticator_data"] = self.proof.authenticator_data
        if self.proof.client_data_hash:
            proof["client_data_hash"] = self.proof.client_data_hash
        doc["proof"] = proof

        # === WHEN ===
        doc["timestamp"] = self.timestamp
        doc["challenge_issued_at"] = self.challenge_issued_at
        doc["challenge_ttl"] = self.challenge_ttl

        # === WHERE (platform state) ===
        ps: Dict[str, Any] = {"available": self.platform_state.available}
        if self.platform_state.boot_verified is not None:
            ps["boot_verified"] = self.platform_state.boot_verified
        if self.platform_state.pcr_values:
            # Spec uses Record<number, string> — serialize int keys as strings
            ps["pcr_values"] = {
                str(k): v for k, v in self.platform_state.pcr_values.items()
            }
        if self.platform_state.os_version:
            ps["os_version"] = self.platform_state.os_version
        if self.platform_state.kernel_version:
            ps["kernel_version"] = self.platform_state.kernel_version
        doc["platform_state"] = ps

        # === TRUST ===
        doc["trust_ceiling"] = self.trust_ceiling

        # === METADATA (optional) ===
        if self.issuer:
            doc["issuer"] = self.issuer
        if self.purpose:
            doc["purpose"] = self.purpose

        return doc

    def to_jsonld_string(self, indent: int = 2) -> str:
        """Serialize to spec-compliant JSON-LD string."""
        return json.dumps(self.to_jsonld(), indent=indent)

    @classmethod
    def from_jsonld(cls, doc: Dict[str, Any]) -> AttestationEnvelope:
        """
        Deserialize from spec-compliant JSON-LD document.

        Accepts both the spec JSON-LD format and the SDK dict format
        for backward compatibility. Ignores @context and @type fields.
        """
        data: Dict[str, Any] = {}

        # Strip JSON-LD envelope fields
        for k, v in doc.items():
            if k.startswith("@"):
                continue
            data[k] = v

        # Reconstruct nested types
        if "anchor" in data and isinstance(data["anchor"], dict):
            data["anchor"] = AnchorInfo(**data["anchor"])

        if "proof" in data and isinstance(data["proof"], dict):
            data["proof"] = Proof(**data["proof"])

        if "platform_state" in data and isinstance(data["platform_state"], dict):
            ps_data = dict(data["platform_state"])
            # Spec serializes PCR keys as strings; restore to int keys
            if "pcr_values" in ps_data and ps_data["pcr_values"]:
                ps_data["pcr_values"] = {
                    int(k): v for k, v in ps_data["pcr_values"].items()
                }
            data["platform_state"] = PlatformState(**ps_data)

        return cls(**{k: v for k, v in data.items()
                      if k in cls.__dataclass_fields__})

    @classmethod
    def from_jsonld_string(cls, s: str) -> AttestationEnvelope:
        """Deserialize from JSON-LD string."""
        return cls.from_jsonld(json.loads(s))


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


# ── Anchor Verifiers ──────────────────────────────────────────────

def _verify_software(envelope: AttestationEnvelope) -> VerificationResult:
    """Verify a software-only attestation envelope.

    Trust ceiling capped at 0.4 — filesystem-resident key, copyable.
    """
    if envelope.anchor.type != 'software':
        return VerificationResult(
            valid=False, trust_ceiling=0, effective_trust=0,
            fresh=False, reason='Wrong anchor type for software verifier')

    fresh = envelope.is_fresh
    has_signature = bool(envelope.proof.signature)
    has_challenge = bool(envelope.proof.challenge)

    return VerificationResult(
        valid=fresh and has_signature and has_challenge,
        trust_ceiling=envelope.trust_ceiling,
        effective_trust=envelope.effective_trust,
        fresh=fresh,
        anchor_verified=True,
        reason='Software-only anchor — key is filesystem-resident, ceiling 0.4',
    )


def _verify_tpm2(envelope: AttestationEnvelope,
                 expected_pcrs: Optional[Dict[int, str]] = None) -> VerificationResult:
    """Verify a TPM 2.0 attestation envelope.

    Stub — PCR validation implemented, hardware quote verification pending.
    """
    if envelope.anchor.type != 'tpm2':
        return VerificationResult(
            valid=False, trust_ceiling=0, effective_trust=0,
            fresh=False, reason='Wrong anchor type for TPM2 verifier')

    fresh = envelope.is_fresh

    platform_state_ok = None
    if expected_pcrs and envelope.platform_state.pcr_values:
        platform_state_ok = all(
            envelope.platform_state.pcr_values.get(idx) == expected
            for idx, expected in expected_pcrs.items()
        )

    anchor_verified = False  # True when real TPM verification is wired

    return VerificationResult(
        valid=fresh and (platform_state_ok is not False),
        trust_ceiling=envelope.trust_ceiling,
        effective_trust=envelope.effective_trust,
        fresh=fresh,
        anchor_verified=anchor_verified,
        platform_state_ok=platform_state_ok,
        reason='TPM2 verification stub — hardware verification pending',
    )


def _verify_fido2(envelope: AttestationEnvelope) -> VerificationResult:
    """Verify a FIDO2/WebAuthn attestation envelope.

    Stub — library integration pending.
    """
    if envelope.anchor.type != 'fido2':
        return VerificationResult(
            valid=False, trust_ceiling=0, effective_trust=0,
            fresh=False, reason='Wrong anchor type for FIDO2 verifier')

    fresh = envelope.is_fresh
    anchor_verified = False

    return VerificationResult(
        valid=fresh,
        trust_ceiling=envelope.trust_ceiling,
        effective_trust=envelope.effective_trust,
        fresh=fresh,
        anchor_verified=anchor_verified,
        reason='FIDO2 verification stub — library integration pending',
    )


def _verify_secure_enclave(envelope: AttestationEnvelope) -> VerificationResult:
    """Verify a Secure Enclave attestation envelope.

    Stub — macOS integration pending.
    """
    if envelope.anchor.type != 'secure_enclave':
        return VerificationResult(
            valid=False, trust_ceiling=0, effective_trust=0,
            fresh=False, reason='Wrong anchor type for SE verifier')

    fresh = envelope.is_fresh
    anchor_verified = False

    return VerificationResult(
        valid=fresh,
        trust_ceiling=envelope.trust_ceiling,
        effective_trust=envelope.effective_trust,
        fresh=fresh,
        anchor_verified=anchor_verified,
        reason='Secure Enclave verification stub — macOS integration pending',
    )


# ── Verification Dispatcher ──────────────────────────────────────

def verify_envelope(envelope: AttestationEnvelope,
                    expected_challenge: str = '',
                    **kwargs: Any) -> VerificationResult:
    """Verify an attestation envelope.

    Dispatches to the appropriate anchor-specific verifier.
    Consumers call this — never the anchor verifiers directly.

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
    _verifiers: Dict[str, Callable[..., VerificationResult]] = {
        'tpm2': _verify_tpm2,
        'fido2': _verify_fido2,
        'secure_enclave': _verify_secure_enclave,
        'software': _verify_software,
    }

    verifier = _verifiers.get(anchor_type)
    if verifier is None:
        return VerificationResult(
            valid=False,
            trust_ceiling=0,
            effective_trust=0,
            fresh=False,
            reason=f'Unknown anchor type: {anchor_type}',
        )

    return verifier(envelope, **kwargs)
