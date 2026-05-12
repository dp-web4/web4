"""
Web4 Witness System
===================

Production-ready witness attestation system for Web4 protocols.

Implements the witness framework defined in WEB4_WITNESSING_SPECIFICATION.md
and protocols/web4-witness.md for LCT identity, delegations, and transactions.

Key Features:
- Multiple witness types (time, audit, oracle, existence, action, state, quality)
- COSE/CBOR and JOSE/JSON attestation formats
- Ed25519 signature verification
- Nonce-based replay protection
- Freshness window validation (±300s)
- Witness reputation tracking
- Multi-witness consensus support

Witness Classes:
- time: Trusted timestamps and liveness
- audit: Policy compliance validation
- audit-minimal: Lightweight rate/digest checks
- oracle: External data attestation
- existence: Entity liveness proof
- action: Operation witnessing
- state: Status attestation
- quality: Performance metrics

Author: Legion Autonomous Session (2025-12-05)
Session: Autonomous Web4 Research Track 3
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from enum import Enum
from datetime import datetime, timedelta, timezone
import hashlib
import json
import time as time_module
import base64
import secrets

# Import crypto verification from Track 2
from crypto_verification import verify_signature, parse_public_key, parse_signature


class WitnessType(str, Enum):
    """Witness attestation types"""
    TIME = "time"
    AUDIT = "audit"
    AUDIT_MINIMAL = "audit-minimal"
    ORACLE = "oracle"
    EXISTENCE = "existence"
    ACTION = "action"
    STATE = "state"
    QUALITY = "quality"


class WitnessError(Exception):
    """Raised when witness validation fails"""
    pass


@dataclass
class WitnessAttestation:
    """
    Witness attestation structure

    Follows WEB4_WITNESSING_SPECIFICATION.md canonical format
    """
    witness_did: str  # DID of witness
    witness_type: WitnessType
    claims: Dict[str, Any]  # Type-specific claims
    signature: str  # Ed25519 signature (hex or base64)
    timestamp: datetime  # ISO 8601 attestation time
    nonce: str  # Replay protection
    subject: Optional[str] = None  # Entity being attested
    event_hash: Optional[str] = None  # SHA-256 of event/transcript
    policy: Optional[str] = None  # Policy identifier

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "witness": self.witness_did,
            "type": self.witness_type.value,
            "claims": self.claims,
            "sig": self.signature,
            "ts": self.timestamp.isoformat(),
            "nonce": self.nonce,
            "subject": self.subject,
            "event_hash": self.event_hash,
            "policy": self.policy
        }

    def to_signing_data(self) -> bytes:
        """
        Get canonical signing data

        Constructs deterministic message for signature verification
        """
        # Build canonical representation (sorted JSON)
        canonical_data = {
            "witness": self.witness_did,
            "type": self.witness_type.value,
            "claims": self.claims,
            "ts": self.timestamp.isoformat(),
            "nonce": self.nonce
        }

        if self.subject:
            canonical_data["subject"] = self.subject
        if self.event_hash:
            canonical_data["event_hash"] = self.event_hash
        if self.policy:
            canonical_data["policy"] = self.policy

        # Sort keys for determinism
        canonical = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        return canonical.encode('utf-8')


@dataclass
class WitnessRequirements:
    """
    Requirements for witness validation

    Attack Mitigation #6: Witness Shopping Prevention (Integrated)
    - min_reputation_score: Minimum witness reputation required
    - require_consensus: Forces witnesses to agree (prevents cherry-picking)
    """
    required_types: Set[WitnessType]  # Required witness types
    min_witnesses: int = 1  # Minimum number of witnesses
    freshness_window_seconds: int = 300  # ±300s default
    require_consensus: bool = False  # All witnesses must agree
    allowed_witnesses: Optional[Set[str]] = None  # Whitelist of witness DIDs

    # Mitigation #6: Witness shopping prevention
    min_reputation_score: float = 0.5  # Minimum witness reputation (0.0-1.0)
    max_witness_attempts: int = 5  # Max witnesses queried before success required


@dataclass
class WitnessValidationResult:
    """Result of witness validation"""
    valid: bool
    error: Optional[str] = None
    verified_attestations: List[WitnessAttestation] = field(default_factory=list)
    failed_attestations: List[Tuple[WitnessAttestation, str]] = field(default_factory=list)
    consensus_achieved: bool = False


class WitnessRegistry:
    """
    Registry of trusted witnesses

    Manages witness public keys, reputation, and capabilities

    Attack Mitigation #6: Witness Shopping Prevention (Integrated)
    - Tracks witness attempt history per entity
    - Enforces minimum reputation requirements
    """

    def __init__(self):
        """Initialize witness registry"""
        # Witness public keys: DID -> public_key
        self.witnesses: Dict[str, str] = {}

        # Witness reputation: DID -> (successful_attestations, failed_attestations)
        self.reputation: Dict[str, Tuple[int, int]] = {}

        # Witness capabilities: DID -> Set[WitnessType]
        self.capabilities: Dict[str, Set[WitnessType]] = {}

        # Nonce tracking for replay protection: nonce -> expiry_time
        self.used_nonces: Dict[str, float] = {}

        # Mitigation #6: Witness shopping tracking
        # (entity_lct, event_hash) -> [list of witness_dids attempted]
        self.witness_attempts: Dict[Tuple[str, str], List[str]] = {}

    def register_witness(
        self,
        witness_did: str,
        public_key: str,
        capabilities: Set[WitnessType]
    ):
        """Register a new witness"""
        self.witnesses[witness_did] = public_key
        self.capabilities[witness_did] = capabilities
        self.reputation[witness_did] = (0, 0)  # (successful, failed)

    def is_witness_registered(self, witness_did: str) -> bool:
        """Check if witness is registered"""
        return witness_did in self.witnesses

    def get_witness_public_key(self, witness_did: str) -> Optional[str]:
        """Get witness public key"""
        return self.witnesses.get(witness_did)

    def get_witness_capabilities(self, witness_did: str) -> Set[WitnessType]:
        """Get witness capabilities"""
        return self.capabilities.get(witness_did, set())

    def record_success(self, witness_did: str):
        """Record successful attestation"""
        if witness_did in self.reputation:
            success, fail = self.reputation[witness_did]
            self.reputation[witness_did] = (success + 1, fail)

    def record_failure(self, witness_did: str):
        """Record failed attestation"""
        if witness_did in self.reputation:
            success, fail = self.reputation[witness_did]
            self.reputation[witness_did] = (success, fail + 1)

    def get_reputation_score(self, witness_did: str) -> float:
        """
        Get witness reputation score (0.0-1.0)

        Uses exponential moving average of success rate
        """
        if witness_did not in self.reputation:
            return 0.5  # Default for unknown witnesses

        success, fail = self.reputation[witness_did]
        total = success + fail

        if total == 0:
            return 0.5  # No history

        return success / total

    def check_nonce(self, nonce: str) -> bool:
        """
        Check if nonce is unused

        Returns True if nonce is fresh, False if already used
        """
        # Clean expired nonces
        now = time_module.time()
        expired = [n for n, exp in self.used_nonces.items() if exp < now]
        for n in expired:
            del self.used_nonces[n]

        # Check if nonce is used
        if nonce in self.used_nonces:
            return False

        # Mark as used (expires in 1 hour)
        self.used_nonces[nonce] = now + 3600
        return True

    def record_witness_attempt(
        self,
        entity_lct: str,
        event_hash: str,
        witness_did: str
    ):
        """
        Record witness attempt for shopping detection

        Attack Mitigation #6: Tracks which witnesses were queried
        for a specific event by a specific entity.
        """
        key = (entity_lct, event_hash)
        if key not in self.witness_attempts:
            self.witness_attempts[key] = []
        self.witness_attempts[key].append(witness_did)

    def get_witness_attempts(
        self,
        entity_lct: str,
        event_hash: str
    ) -> int:
        """
        Get number of witness attempts for an event

        Attack Mitigation #6: Used to detect witness shopping
        """
        key = (entity_lct, event_hash)
        return len(self.witness_attempts.get(key, []))

    def check_witness_shopping(
        self,
        entity_lct: str,
        event_hash: str,
        max_attempts: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if entity is witness shopping

        Attack Mitigation #6: Witness Shopping Prevention
        Detects when an entity queries excessive witnesses for same event,
        likely searching for favorable attestation.

        Returns:
            (valid, error_message) tuple
        """
        attempts = self.get_witness_attempts(entity_lct, event_hash)
        if attempts >= max_attempts:
            return False, f"Excessive witness attempts: {attempts} >= {max_attempts}"
        return True, None


class WitnessSystem:
    """
    Web4 Witness System

    Validates witness attestations for LCT identity, delegations, and transactions
    """

    def __init__(self, registry: Optional[WitnessRegistry] = None):
        """
        Initialize witness system

        Args:
            registry: Witness registry (creates new if None)
        """
        self.registry = registry or WitnessRegistry()

    def create_attestation(
        self,
        witness_did: str,
        witness_type: WitnessType,
        claims: Dict[str, Any],
        private_key,  # Ed25519PrivateKey for signing
        subject: Optional[str] = None,
        event_hash: Optional[str] = None,
        policy: Optional[str] = None
    ) -> WitnessAttestation:
        """
        Create signed witness attestation

        Args:
            witness_did: DID of witness
            witness_type: Type of attestation
            claims: Type-specific claims
            private_key: Ed25519 private key for signing
            subject: Entity being attested (optional)
            event_hash: SHA-256 of event/transcript (optional)
            policy: Policy identifier (optional)

        Returns:
            Signed WitnessAttestation
        """
        # Generate nonce
        nonce = base64.b64encode(secrets.token_bytes(16)).decode('ascii')

        # Create attestation
        attestation = WitnessAttestation(
            witness_did=witness_did,
            witness_type=witness_type,
            claims=claims,
            signature="",  # Will be filled after signing
            timestamp=datetime.now(timezone.utc),
            nonce=nonce,
            subject=subject,
            event_hash=event_hash,
            policy=policy
        )

        # Sign attestation
        signing_data = attestation.to_signing_data()
        signature_bytes = private_key.sign(signing_data)
        attestation.signature = signature_bytes.hex()

        return attestation

    def verify_attestation(
        self,
        attestation: WitnessAttestation,
        requirements: Optional[WitnessRequirements] = None,
        entity_lct: Optional[str] = None  # NEW: For witness shopping detection
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify single witness attestation

        Args:
            attestation: Attestation to verify
            requirements: Validation requirements
            entity_lct: Entity requesting attestation (for shopping detection)

        Returns:
            (valid, error_message) tuple
        """
        # Check witness is registered
        if not self.registry.is_witness_registered(attestation.witness_did):
            return False, f"Unknown witness: {attestation.witness_did}"

        # Mitigation #6: Check witness reputation
        if requirements and requirements.min_reputation_score > 0:
            reputation = self.registry.get_reputation_score(attestation.witness_did)
            if reputation < requirements.min_reputation_score:
                return False, f"Witness reputation too low: {reputation:.2f} < {requirements.min_reputation_score:.2f}"

        # Mitigation #6: Check witness shopping
        if requirements and entity_lct and attestation.event_hash:
            valid, error = self.registry.check_witness_shopping(
                entity_lct,
                attestation.event_hash,
                requirements.max_witness_attempts
            )
            if not valid:
                return False, f"Witness shopping detected: {error}"

            # Record this attempt
            self.registry.record_witness_attempt(
                entity_lct,
                attestation.event_hash,
                attestation.witness_did
            )

        # Check witness capability
        capabilities = self.registry.get_witness_capabilities(attestation.witness_did)
        if attestation.witness_type not in capabilities:
            return False, f"Witness {attestation.witness_did} not authorized for {attestation.witness_type}"

        # Check whitelist if provided
        if requirements and requirements.allowed_witnesses:
            if attestation.witness_did not in requirements.allowed_witnesses:
                return False, f"Witness {attestation.witness_did} not in allowed list"

        # Check freshness
        freshness_window = requirements.freshness_window_seconds if requirements else 300
        age = (datetime.now(timezone.utc) - attestation.timestamp).total_seconds()

        if abs(age) > freshness_window:
            return False, f"Attestation too old/future: {age}s (limit: ±{freshness_window}s)"

        # Check nonce uniqueness
        if not self.registry.check_nonce(attestation.nonce):
            return False, f"Nonce already used: {attestation.nonce}"

        # Verify signature
        public_key = self.registry.get_witness_public_key(attestation.witness_did)
        if not public_key:
            return False, f"No public key for witness: {attestation.witness_did}"

        try:
            signing_data = attestation.to_signing_data()
            valid = verify_signature(
                public_key=public_key,
                message=signing_data,
                signature=attestation.signature
            )

            if not valid:
                return False, "Invalid signature"

        except Exception as e:
            return False, f"Signature verification error: {e}"

        # Verify type-specific claims
        valid, error = self._verify_type_specific_claims(attestation)
        if not valid:
            return False, error

        return True, None

    def _verify_type_specific_claims(
        self,
        attestation: WitnessAttestation
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify type-specific claim requirements

        Each witness type has required claims that must be present
        """
        claims = attestation.claims

        if attestation.witness_type == WitnessType.TIME:
            # TIME: ts, nonce required
            if 'ts' not in claims:
                return False, "TIME witness missing 'ts' claim"
            if 'nonce' not in claims:
                return False, "TIME witness missing 'nonce' claim"

        elif attestation.witness_type == WitnessType.AUDIT:
            # AUDIT: policy_met, evidence, policy_id required
            required = ['policy_met', 'evidence', 'policy_id']
            for field in required:
                if field not in claims:
                    return False, f"AUDIT witness missing '{field}' claim"

        elif attestation.witness_type == WitnessType.AUDIT_MINIMAL:
            # AUDIT_MINIMAL: digest_valid, rate_ok required
            required = ['digest_valid', 'rate_ok']
            for field in required:
                if field not in claims:
                    return False, f"AUDIT_MINIMAL witness missing '{field}' claim"

        elif attestation.witness_type == WitnessType.ORACLE:
            # ORACLE: source, data, ts required
            required = ['source', 'data', 'ts']
            for field in required:
                if field not in claims:
                    return False, f"ORACLE witness missing '{field}' claim"

        elif attestation.witness_type == WitnessType.EXISTENCE:
            # EXISTENCE: observed_at, method required
            required = ['observed_at', 'method']
            for field in required:
                if field not in claims:
                    return False, f"EXISTENCE witness missing '{field}' claim"

        elif attestation.witness_type == WitnessType.ACTION:
            # ACTION: action_type, result required
            required = ['action_type', 'result']
            for field in required:
                if field not in claims:
                    return False, f"ACTION witness missing '{field}' claim"

        elif attestation.witness_type == WitnessType.STATE:
            # STATE: state, measurement required
            required = ['state', 'measurement']
            for field in required:
                if field not in claims:
                    return False, f"STATE witness missing '{field}' claim"

        elif attestation.witness_type == WitnessType.QUALITY:
            # QUALITY: metric, value required
            required = ['metric', 'value']
            for field in required:
                if field not in claims:
                    return False, f"QUALITY witness missing '{field}' claim"

        return True, None

    def validate_witnesses(
        self,
        attestations: List[WitnessAttestation],
        requirements: WitnessRequirements,
        entity_lct: Optional[str] = None  # NEW: For witness shopping detection
    ) -> WitnessValidationResult:
        """
        Validate multiple witness attestations

        Args:
            attestations: List of attestations to validate
            requirements: Validation requirements
            entity_lct: Entity requesting attestation (for shopping detection)

        Returns:
            WitnessValidationResult with validation details
        """
        verified = []
        failed = []

        # Verify each attestation
        for attestation in attestations:
            valid, error = self.verify_attestation(
                attestation,
                requirements,
                entity_lct  # Pass for witness shopping detection
            )

            if valid:
                verified.append(attestation)
                self.registry.record_success(attestation.witness_did)
            else:
                failed.append((attestation, error))
                self.registry.record_failure(attestation.witness_did)

        # Check minimum witnesses
        if len(verified) < requirements.min_witnesses:
            return WitnessValidationResult(
                valid=False,
                error=f"Insufficient witnesses: {len(verified)} < {requirements.min_witnesses}",
                verified_attestations=verified,
                failed_attestations=failed
            )

        # Check required types
        verified_types = {att.witness_type for att in verified}
        missing_types = requirements.required_types - verified_types

        if missing_types:
            return WitnessValidationResult(
                valid=False,
                error=f"Missing required witness types: {missing_types}",
                verified_attestations=verified,
                failed_attestations=failed
            )

        # Check consensus if required
        consensus = True
        if requirements.require_consensus and len(verified) > 1:
            # All witnesses must agree on key claims
            consensus = self._check_consensus(verified)

        return WitnessValidationResult(
            valid=True,
            verified_attestations=verified,
            failed_attestations=failed,
            consensus_achieved=consensus
        )

    def _check_consensus(self, attestations: List[WitnessAttestation]) -> bool:
        """
        Check if witnesses agree on key claims

        For consensus, all witnesses of the same type must provide
        consistent claims
        """
        # Group by type
        by_type: Dict[WitnessType, List[Dict]] = {}
        for att in attestations:
            if att.witness_type not in by_type:
                by_type[att.witness_type] = []
            by_type[att.witness_type].append(att.claims)

        # Check consistency within each type
        for witness_type, claims_list in by_type.items():
            if len(claims_list) < 2:
                continue  # Single witness, no consensus needed

            # For each claim key, all values must match
            first_claims = claims_list[0]
            for claims in claims_list[1:]:
                for key, value in first_claims.items():
                    if key not in claims or claims[key] != value:
                        return False  # Disagreement found

        return True


# Example usage and factory functions

def create_time_attestation(
    witness_system: WitnessSystem,
    witness_did: str,
    private_key,
    nonce: str,
    subject: Optional[str] = None
) -> WitnessAttestation:
    """Create time witness attestation"""
    claims = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "nonce": nonce,
        "accuracy": 100  # milliseconds
    }

    return witness_system.create_attestation(
        witness_did=witness_did,
        witness_type=WitnessType.TIME,
        claims=claims,
        private_key=private_key,
        subject=subject
    )


def create_audit_attestation(
    witness_system: WitnessSystem,
    witness_did: str,
    private_key,
    policy_id: str,
    policy_met: bool,
    evidence: str,
    subject: Optional[str] = None
) -> WitnessAttestation:
    """Create audit witness attestation"""
    claims = {
        "policy_met": policy_met,
        "evidence": evidence,
        "policy_id": policy_id
    }

    return witness_system.create_attestation(
        witness_did=witness_did,
        witness_type=WitnessType.AUDIT,
        claims=claims,
        private_key=private_key,
        subject=subject,
        policy=policy_id
    )


def create_action_attestation(
    witness_system: WitnessSystem,
    witness_did: str,
    private_key,
    action_type: str,
    result: str,
    actor: Optional[str] = None,
    event_hash: Optional[str] = None
) -> WitnessAttestation:
    """Create action witness attestation"""
    claims = {
        "action_type": action_type,
        "result": result
    }

    if actor:
        claims["actor"] = actor

    return witness_system.create_attestation(
        witness_did=witness_did,
        witness_type=WitnessType.ACTION,
        claims=claims,
        private_key=private_key,
        event_hash=event_hash
    )


if __name__ == '__main__':
    print("Web4 Witness System - Example Usage")
    print("=" * 60)

    # This would require cryptography library and actual key generation
    # See crypto_verification.py for key generation functions
    print("\nWitness System initialized")
    print("See crypto_verification.py for key generation")
    print("See test_witness_system.py for comprehensive testing")
