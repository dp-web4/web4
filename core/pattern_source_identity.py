#!/usr/bin/env python3
"""
Web4 Pattern Source Identity (PSI) System

This module provides pattern federation identity and trust using real Web4 LCT
(Linked Context Token) infrastructure.

Key Integration Points:
- T3 Tensor: 6-dimension trust (technical_competence, social_reliability,
  temporal_consistency, witness_count, lineage_depth, context_alignment)
- V3 Tensor: 6-dimension value (energy_balance, contribution_history,
  resource_stewardship, network_effects, reputation_capital, temporal_value)
- MRH: Markov Relevancy Horizon with bound/paired/witnessing relationships
- Pattern signing: Uses LCT binding for cryptographic identity

Reference:
- LCT Spec: web4-standard/core-spec/LCT-linked-context-token.md
- Migration: proposals/PATTERN_SOURCE_IDENTITY.md
- Existing LCT impl: web4-standard/implementation/act_deployment/lct.py

Session History:
- L121: Original implementation (incorrectly used "LCT" term)
- CBP 2026-01-03: Renamed and refactored to use real LCT structures
"""

import json
import hashlib
import base64
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# Cryptographic imports
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey
    )
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("Warning: cryptography library not available, using mock signatures")


# ============================================================================
# T3 Trust Tensor (from LCT spec)
# ============================================================================

@dataclass
class T3Tensor:
    """
    Trust Tensor (T3) - 6-dimensional trust measurement.

    From LCT specification: "Every LCT MUST contain a t3_tensor with at least
    these dimensions."

    Dimensions:
    - technical_competence: Can entity perform claimed capabilities? [0.0-1.0]
    - social_reliability: Does entity honor commitments? [0.0-1.0]
    - temporal_consistency: Is entity's behavior consistent over time? [0.0-1.0]
    - witness_count: How many entities witness this entity? [0.0-1.0]
    - lineage_depth: How deep is trust lineage? [0.0-1.0]
    - context_alignment: How well aligned with current context? [0.0-1.0]

    Computation: Societies or trust oracles compute T3 tensors based on:
    - Historical behavior
    - Witness attestations
    - MRH relationship quality
    - Time-weighted decay
    """
    # Core dimensions (all 0.0-1.0)
    technical_competence: float = 0.1
    social_reliability: float = 0.1
    temporal_consistency: float = 0.1
    witness_count: float = 0.0
    lineage_depth: float = 0.0
    context_alignment: float = 0.5

    # Metadata
    last_computed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    computation_witnesses: List[str] = field(default_factory=list)

    @property
    def composite_score(self) -> float:
        """
        Compute weighted composite trust score.

        Default weights emphasize social reliability and temporal consistency
        as these are most predictive of future behavior.
        """
        weights = {
            'technical_competence': 0.15,
            'social_reliability': 0.25,
            'temporal_consistency': 0.20,
            'witness_count': 0.15,
            'lineage_depth': 0.10,
            'context_alignment': 0.15
        }

        score = (
            self.technical_competence * weights['technical_competence'] +
            self.social_reliability * weights['social_reliability'] +
            self.temporal_consistency * weights['temporal_consistency'] +
            self.witness_count * weights['witness_count'] +
            self.lineage_depth * weights['lineage_depth'] +
            self.context_alignment * weights['context_alignment']
        )

        return min(1.0, max(0.0, score))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (matches LCT spec format)."""
        return {
            "dimensions": {
                "technical_competence": self.technical_competence,
                "social_reliability": self.social_reliability,
                "temporal_consistency": self.temporal_consistency,
                "witness_count": self.witness_count,
                "lineage_depth": self.lineage_depth,
                "context_alignment": self.context_alignment
            },
            "composite_score": self.composite_score,
            "last_computed": self.last_computed,
            "computation_witnesses": self.computation_witnesses
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'T3Tensor':
        """Create T3Tensor from dictionary."""
        dims = data.get("dimensions", data)  # Support both nested and flat
        return T3Tensor(
            technical_competence=dims.get("technical_competence", 0.1),
            social_reliability=dims.get("social_reliability", 0.1),
            temporal_consistency=dims.get("temporal_consistency", 0.1),
            witness_count=dims.get("witness_count", 0.0),
            lineage_depth=dims.get("lineage_depth", 0.0),
            context_alignment=dims.get("context_alignment", 0.5),
            last_computed=data.get("last_computed", datetime.now(timezone.utc).isoformat()),
            computation_witnesses=data.get("computation_witnesses", [])
        )

    def update_from_interaction(self, success: bool, quality_weight: float = 1.0):
        """
        Update T3 tensor based on interaction outcome.

        Args:
            success: Whether interaction was successful
            quality_weight: Quality factor of the interaction (0.0-1.0)
        """
        # Learning rate for updates
        alpha = 0.01 * quality_weight

        if success:
            # Successful interactions improve dimensions
            self.technical_competence = min(1.0, self.technical_competence + alpha)
            self.social_reliability = min(1.0, self.social_reliability + alpha * 1.5)
            self.temporal_consistency = min(1.0, self.temporal_consistency + alpha * 0.5)
        else:
            # Failed interactions decay trust
            self.social_reliability = max(0.0, self.social_reliability - alpha * 2.0)
            self.temporal_consistency = max(0.0, self.temporal_consistency - alpha)

        self.last_computed = datetime.now(timezone.utc).isoformat()


# ============================================================================
# V3 Value Tensor (from LCT spec)
# ============================================================================

@dataclass
class V3Tensor:
    """
    Value Tensor (V3) - 6-dimensional value measurement.

    From LCT specification: "Every LCT MUST contain a v3_tensor with at least
    these dimensions."

    Dimensions:
    - energy_balance: ATP/ADP balance (integer, can be negative)
    - contribution_history: Historical value contributions [0.0-1.0]
    - resource_stewardship: How well entity manages resources [0.0-1.0]
    - network_effects: Value created for others [0.0-1.0]
    - reputation_capital: Accumulated social capital [0.0-1.0]
    - temporal_value: Value persistence over time [0.0-1.0]

    Computation: Societies or value oracles compute V3 tensors based on:
    - Energy economics (ATP/ADP)
    - Contribution metrics
    - Resource management
    - Network impact
    """
    # Core dimensions
    energy_balance: int = 0
    contribution_history: float = 0.0
    resource_stewardship: float = 0.5
    network_effects: float = 0.0
    reputation_capital: float = 0.0
    temporal_value: float = 0.5

    # Metadata
    last_computed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    computation_witnesses: List[str] = field(default_factory=list)

    @property
    def composite_score(self) -> float:
        """
        Compute weighted composite value score.

        Note: energy_balance is normalized to [0,1] range for composite.
        """
        # Normalize energy_balance to 0-1 (sigmoid-ish)
        normalized_energy = 1.0 / (1.0 + abs(min(0, self.energy_balance) / 100.0))
        if self.energy_balance > 0:
            normalized_energy = min(1.0, 0.5 + self.energy_balance / 200.0)

        weights = {
            'energy_balance': 0.20,
            'contribution_history': 0.20,
            'resource_stewardship': 0.15,
            'network_effects': 0.20,
            'reputation_capital': 0.15,
            'temporal_value': 0.10
        }

        score = (
            normalized_energy * weights['energy_balance'] +
            self.contribution_history * weights['contribution_history'] +
            self.resource_stewardship * weights['resource_stewardship'] +
            self.network_effects * weights['network_effects'] +
            self.reputation_capital * weights['reputation_capital'] +
            self.temporal_value * weights['temporal_value']
        )

        return min(1.0, max(0.0, score))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (matches LCT spec format)."""
        return {
            "dimensions": {
                "energy_balance": self.energy_balance,
                "contribution_history": self.contribution_history,
                "resource_stewardship": self.resource_stewardship,
                "network_effects": self.network_effects,
                "reputation_capital": self.reputation_capital,
                "temporal_value": self.temporal_value
            },
            "composite_score": self.composite_score,
            "last_computed": self.last_computed,
            "computation_witnesses": self.computation_witnesses
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'V3Tensor':
        """Create V3Tensor from dictionary."""
        dims = data.get("dimensions", data)
        return V3Tensor(
            energy_balance=dims.get("energy_balance", 0),
            contribution_history=dims.get("contribution_history", 0.0),
            resource_stewardship=dims.get("resource_stewardship", 0.5),
            network_effects=dims.get("network_effects", 0.0),
            reputation_capital=dims.get("reputation_capital", 0.0),
            temporal_value=dims.get("temporal_value", 0.5),
            last_computed=data.get("last_computed", datetime.now(timezone.utc).isoformat()),
            computation_witnesses=data.get("computation_witnesses", [])
        )


# ============================================================================
# MRH Relationship Types (from LCT spec)
# ============================================================================

class MRHRelationshipType(Enum):
    """Types of MRH relationships."""
    # Binding types
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"

    # Pairing types
    BIRTH_CERTIFICATE = "birth_certificate"
    ROLE = "role"
    OPERATIONAL = "operational"

    # Witnessing roles
    TIME = "time"
    AUDIT = "audit"
    ORACLE = "oracle"
    EXISTENCE = "existence"
    ACTION = "action"
    STATE = "state"
    QUALITY = "quality"


@dataclass
class MRHRelationship:
    """Single relationship in the MRH."""
    lct_id: str
    relationship_type: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    permanent: bool = False
    context: Optional[str] = None
    witness_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lct_id": self.lct_id,
            "type": self.relationship_type,
            "ts": self.timestamp,
            "permanent": self.permanent,
            "context": self.context,
            "witness_count": self.witness_count
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MRHRelationship':
        return MRHRelationship(
            lct_id=data["lct_id"],
            relationship_type=data.get("type", data.get("relationship_type", "unknown")),
            timestamp=data.get("ts", data.get("timestamp", "")),
            permanent=data.get("permanent", False),
            context=data.get("context"),
            witness_count=data.get("witness_count", 0)
        )


@dataclass
class MarkovRelevancyHorizon:
    """
    Markov Relevancy Horizon (MRH) - Context boundary for an entity.

    From LCT specification: "The MRH defines the context boundary for an entity -
    the set of all entities that are relevant to this LCT's operations, trust
    calculations, and interactions."

    Relationship Types:
    - bound: Permanent hierarchical attachments (parent/child/sibling)
    - paired: Authorized operational connections (birth_certificate/role/operational)
    - witnessing: Trust accumulation through observation
    """
    bound: List[MRHRelationship] = field(default_factory=list)
    paired: List[MRHRelationship] = field(default_factory=list)
    witnessing: List[MRHRelationship] = field(default_factory=list)
    horizon_depth: int = 3
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_bound(self, lct_id: str, relationship_type: str, context: str = None):
        """Add binding relationship (permanent hierarchical)."""
        self.bound.append(MRHRelationship(
            lct_id=lct_id,
            relationship_type=relationship_type,
            permanent=True,
            context=context
        ))
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def add_paired(self, lct_id: str, pairing_type: str, permanent: bool = False):
        """Add pairing relationship (operational connection)."""
        self.paired.append(MRHRelationship(
            lct_id=lct_id,
            relationship_type=pairing_type,
            permanent=permanent
        ))
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def add_witness(self, lct_id: str, witness_role: str):
        """Add witnessing relationship."""
        # Check if witness already exists
        for w in self.witnessing:
            if w.lct_id == lct_id:
                w.witness_count += 1
                w.timestamp = datetime.now(timezone.utc).isoformat()
                self.last_updated = datetime.now(timezone.utc).isoformat()
                return

        self.witnessing.append(MRHRelationship(
            lct_id=lct_id,
            relationship_type=witness_role,
            witness_count=1
        ))
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def get_witness_lcts(self, limit: int = 5) -> List[str]:
        """Get top witness LCT IDs by witness count."""
        sorted_witnesses = sorted(
            self.witnessing,
            key=lambda w: w.witness_count,
            reverse=True
        )
        return [w.lct_id for w in sorted_witnesses[:limit]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (matches LCT spec format)."""
        return {
            "bound": [r.to_dict() for r in self.bound],
            "paired": [r.to_dict() for r in self.paired],
            "witnessing": [r.to_dict() for r in self.witnessing],
            "horizon_depth": self.horizon_depth,
            "last_updated": self.last_updated
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MarkovRelevancyHorizon':
        """Create MRH from dictionary."""
        return MarkovRelevancyHorizon(
            bound=[MRHRelationship.from_dict(r) for r in data.get("bound", [])],
            paired=[MRHRelationship.from_dict(r) for r in data.get("paired", [])],
            witnessing=[MRHRelationship.from_dict(r) for r in data.get("witnessing", [])],
            horizon_depth=data.get("horizon_depth", 3),
            last_updated=data.get("last_updated", datetime.now(timezone.utc).isoformat())
        )


# ============================================================================
# Pattern Source Identity (PSI)
# ============================================================================

class PatternSourceIdentity:
    """
    Pattern Source Identity for pattern federation.

    Integrates with Web4 LCT (Linked Context Token) infrastructure for:
    - Cryptographic identity via Ed25519 binding
    - Multi-dimensional trust via T3 tensor
    - Multi-dimensional value via V3 tensor
    - Context relationships via MRH

    Trust tiers (based on T3 composite score):
    - 0.0-0.2: Untrusted - Reject patterns
    - 0.2-0.4: Low Trust - Accept with sandboxing
    - 0.4-0.6: Medium Trust - Accept, weight by trust
    - 0.6-0.8: High Trust - Accept, normal weight
    - 0.8-1.0: Exceptional - Accept, high weight
    """

    def __init__(
        self,
        # Cryptographic binding
        private_key: Optional[bytes] = None,
        public_key: Optional[bytes] = None,
        lct_id: Optional[str] = None,
        entity_type: str = "ai",

        # Trust and value tensors
        t3_tensor: Optional[T3Tensor] = None,
        v3_tensor: Optional[V3Tensor] = None,

        # MRH relationships
        mrh: Optional[MarkovRelevancyHorizon] = None,

        # Metadata
        created_timestamp: Optional[str] = None,
        last_active: Optional[str] = None,
        device_fingerprint: Optional[str] = None,

        # Interaction tracking (for tensor updates)
        interactions: int = 0,
        successful_interactions: int = 0,
        failed_interactions: int = 0
    ):
        """
        Initialize Pattern Source Identity.

        Args:
            private_key: Ed25519 private key bytes (generated if None)
            public_key: Ed25519 public key bytes (derived if None)
            lct_id: LCT identifier (derived from public key if None)
            entity_type: Entity type (human, ai, device, service, etc.)
            t3_tensor: Trust tensor (initialized if None)
            v3_tensor: Value tensor (initialized if None)
            mrh: Markov Relevancy Horizon (initialized if None)
            created_timestamp: Genesis timestamp
            last_active: Last activity timestamp
            device_fingerprint: Hardware/environment fingerprint
            interactions: Total interaction count
            successful_interactions: Successful interaction count
            failed_interactions: Failed interaction count
        """
        # Generate cryptographic binding
        if private_key is None:
            if CRYPTO_AVAILABLE:
                sk = Ed25519PrivateKey.generate()
                self._private_key_obj = sk
                self._public_key_obj = sk.public_key()

                self.private_key = sk.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                )
                self.public_key = self._public_key_obj.public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )
            else:
                # Mock keys for testing without cryptography library
                self.private_key = b"mock_private_key_32_bytes_long!!"
                self.public_key = b"mock_public_key_32_bytes_lng!!"
                self._private_key_obj = None
                self._public_key_obj = None
        else:
            self.private_key = private_key
            self.public_key = public_key

            if CRYPTO_AVAILABLE and private_key:
                self._private_key_obj = Ed25519PrivateKey.from_private_bytes(private_key)
                self._public_key_obj = Ed25519PublicKey.from_public_bytes(public_key)
            else:
                self._private_key_obj = None
                self._public_key_obj = None

        # Derive LCT ID from public key (matches LCT spec format)
        if lct_id is None:
            pk_hash = hashlib.sha256(self.public_key).digest()
            self.lct_id = f"lct:web4:{entity_type}:{pk_hash.hex()[:16]}"
        else:
            self.lct_id = lct_id

        self.entity_type = entity_type

        # Initialize tensors
        self.t3_tensor = t3_tensor or T3Tensor()
        self.v3_tensor = v3_tensor or V3Tensor()

        # Initialize MRH
        self.mrh = mrh or MarkovRelevancyHorizon()

        # Timestamps
        now = datetime.now(timezone.utc).isoformat()
        self.created_timestamp = created_timestamp or now
        self.last_active = last_active or now

        # Device fingerprint
        self.device_fingerprint = device_fingerprint or self._generate_device_fingerprint()

        # Interaction tracking
        self.interactions = interactions
        self.successful_interactions = successful_interactions
        self.failed_interactions = failed_interactions

    @staticmethod
    def _generate_device_fingerprint() -> str:
        """Generate device fingerprint for hardware binding."""
        import platform
        import socket

        fingerprint = {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "processor": platform.processor()
        }

        fp_str = json.dumps(fingerprint, sort_keys=True)
        return hashlib.sha256(fp_str.encode()).hexdigest()[:16]

    # ========================================================================
    # Trust Properties (using T3 tensor)
    # ========================================================================

    @property
    def trust_score(self) -> float:
        """Get composite trust score from T3 tensor."""
        return self.t3_tensor.composite_score

    @property
    def trust_tier(self) -> str:
        """Get trust tier based on composite score."""
        score = self.trust_score
        if score < 0.2:
            return "untrusted"
        elif score < 0.4:
            return "low"
        elif score < 0.6:
            return "medium"
        elif score < 0.8:
            return "high"
        else:
            return "exceptional"

    @property
    def value_score(self) -> float:
        """Get composite value score from V3 tensor."""
        return self.v3_tensor.composite_score

    # ========================================================================
    # Interaction Recording (updates tensors)
    # ========================================================================

    def record_interaction(self, success: bool, quality_weight: float = 1.0):
        """
        Record interaction outcome and update tensors.

        Args:
            success: Whether interaction was successful
            quality_weight: Quality factor of the interaction
        """
        self.interactions += 1

        if success:
            self.successful_interactions += 1
        else:
            self.failed_interactions += 1

        # Update T3 tensor
        self.t3_tensor.update_from_interaction(success, quality_weight)

        # Update V3 tensor contribution metrics
        if success:
            self.v3_tensor.contribution_history = min(
                1.0,
                self.v3_tensor.contribution_history + 0.01 * quality_weight
            )
            self.v3_tensor.network_effects = min(
                1.0,
                self.v3_tensor.network_effects + 0.005 * quality_weight
            )

        self.last_active = datetime.now(timezone.utc).isoformat()

    def add_witness(self, witness_lct_id: str, witness_role: str = "quality"):
        """
        Add witness attestation (updates MRH and T3).

        Args:
            witness_lct_id: LCT ID of the witnessing entity
            witness_role: Role of witness (time, audit, oracle, existence, action, state, quality)
        """
        self.mrh.add_witness(witness_lct_id, witness_role)

        # Update T3 witness_count dimension
        total_witnesses = len(self.mrh.witnessing)
        witness_attestations = sum(w.witness_count for w in self.mrh.witnessing)

        # Normalize: 10+ witnesses = 1.0
        self.t3_tensor.witness_count = min(1.0, total_witnesses / 10.0)

        # Also update social_reliability based on witness attestations
        if witness_attestations > 0:
            self.t3_tensor.social_reliability = min(
                1.0,
                self.t3_tensor.social_reliability + 0.02
            )

        self.t3_tensor.last_computed = datetime.now(timezone.utc).isoformat()

    # ========================================================================
    # Cryptographic Operations
    # ========================================================================

    def sign(self, message: bytes) -> bytes:
        """
        Sign message with private key.

        Args:
            message: Message bytes to sign

        Returns:
            Ed25519 signature bytes
        """
        if CRYPTO_AVAILABLE and self._private_key_obj:
            return self._private_key_obj.sign(message)
        else:
            # Mock signature for testing
            return hashlib.sha256(message + self.private_key).digest()

    def verify(self, message: bytes, signature: bytes) -> bool:
        """
        Verify signature on message.

        Args:
            message: Original message bytes
            signature: Signature to verify

        Returns:
            True if valid, False otherwise
        """
        if CRYPTO_AVAILABLE and self._public_key_obj:
            try:
                self._public_key_obj.verify(signature, message)
                return True
            except InvalidSignature:
                return False
        else:
            # Mock verification
            expected = hashlib.sha256(message + self.private_key).digest()
            return signature == expected

    # ========================================================================
    # Pattern Signing (with LCT provenance)
    # ========================================================================

    def sign_pattern(self, pattern: Dict) -> Dict:
        """
        Sign pattern with LCT provenance.

        Creates provenance block with:
        - source_lct: This identity's LCT ID
        - t3_snapshot: T3 tensor at signing time
        - mrh_witnesses: Top witnesses from MRH
        - binding_signature: Cryptographic signature

        Args:
            pattern: Pattern dictionary to sign

        Returns:
            Pattern with provenance added
        """
        # Create canonical payload for signing
        payload = {
            "pattern_id": pattern.get("pattern_id", "unknown"),
            "context": pattern.get("context", {}),
            "context_tag": pattern.get("context_tag", {}),
            "timestamp": pattern.get("timestamp", datetime.now(timezone.utc).isoformat())
        }

        # Canonical JSON (deterministic)
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))

        # Sign
        signature = self.sign(canonical.encode())

        # Add LCT-style provenance
        signed = pattern.copy()
        signed["provenance"] = {
            # Real LCT reference
            "source_lct": self.lct_id,

            # T3 tensor snapshot
            "t3_snapshot": self.t3_tensor.to_dict(),

            # MRH witnesses (top 5)
            "mrh_witnesses": self.mrh.get_witness_lcts(limit=5),

            # Cryptographic binding
            "binding_signature": base64.b64encode(signature).decode(),
            "public_key": base64.b64encode(self.public_key).decode(),

            # Metadata
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "entity_type": self.entity_type
        }

        return signed

    @staticmethod
    def verify_pattern_provenance(
        pattern: Dict,
        psi_registry: Optional[Dict[str, 'PatternSourceIdentity']] = None
    ) -> Tuple[bool, Optional[str], float]:
        """
        Verify pattern provenance.

        Args:
            pattern: Pattern with provenance to verify
            psi_registry: Optional registry to look up source identity

        Returns:
            (valid, source_lct_id, trust_score) tuple
        """
        prov = pattern.get("provenance")
        if not prov:
            return False, None, 0.0

        source_lct = prov.get("source_lct")

        try:
            # Reconstruct payload
            payload = {
                "pattern_id": pattern.get("pattern_id", "unknown"),
                "context": pattern.get("context", {}),
                "context_tag": pattern.get("context_tag", {}),
                "timestamp": pattern.get("timestamp", "")
            }
            canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))

            # Decode signature
            public_key_bytes = base64.b64decode(prov["public_key"])
            signature_bytes = base64.b64decode(prov["binding_signature"])

            # Verify signature
            if CRYPTO_AVAILABLE:
                public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
                try:
                    public_key.verify(signature_bytes, canonical.encode())
                    valid = True
                except InvalidSignature:
                    return False, source_lct, 0.0
            else:
                # Mock verification (always passes in mock mode)
                valid = True

            # Get trust score from T3 snapshot
            t3_snapshot = prov.get("t3_snapshot", {})
            trust_score = t3_snapshot.get("composite_score", 0.1)

            # If registry provided, get live trust score
            if psi_registry and source_lct in psi_registry:
                trust_score = psi_registry[source_lct].trust_score

            return valid, source_lct, trust_score

        except Exception as e:
            print(f"Provenance verification error: {e}")
            return False, source_lct, 0.0

    # ========================================================================
    # Serialization
    # ========================================================================

    def to_dict(self, include_private: bool = False) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Args:
            include_private: Include private key (for storage only)

        Returns:
            Dictionary representation
        """
        data = {
            "lct_id": self.lct_id,
            "entity_type": self.entity_type,
            "public_key": base64.b64encode(self.public_key).decode(),

            # Tensors
            "t3_tensor": self.t3_tensor.to_dict(),
            "v3_tensor": self.v3_tensor.to_dict(),

            # MRH
            "mrh": self.mrh.to_dict(),

            # Metadata
            "created_timestamp": self.created_timestamp,
            "last_active": self.last_active,
            "device_fingerprint": self.device_fingerprint,

            # Interaction stats
            "interactions": self.interactions,
            "successful_interactions": self.successful_interactions,
            "failed_interactions": self.failed_interactions,

            # Computed properties
            "trust_score": self.trust_score,
            "trust_tier": self.trust_tier,
            "value_score": self.value_score
        }

        if include_private:
            data["private_key"] = base64.b64encode(self.private_key).decode()

        return data

    def save(self, path: Path):
        """
        Save identity to file.

        WARNING: Private key stored unencrypted. In production, encrypt.
        """
        data = self.to_dict(include_private=True)

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(path: Path) -> 'PatternSourceIdentity':
        """Load identity from file."""
        with open(path, 'r') as f:
            data = json.load(f)

        return PatternSourceIdentity(
            private_key=base64.b64decode(data["private_key"]),
            public_key=base64.b64decode(data["public_key"]),
            lct_id=data.get("lct_id"),
            entity_type=data.get("entity_type", "ai"),
            t3_tensor=T3Tensor.from_dict(data.get("t3_tensor", {})),
            v3_tensor=V3Tensor.from_dict(data.get("v3_tensor", {})),
            mrh=MarkovRelevancyHorizon.from_dict(data.get("mrh", {})),
            created_timestamp=data.get("created_timestamp"),
            last_active=data.get("last_active"),
            device_fingerprint=data.get("device_fingerprint"),
            interactions=data.get("interactions", 0),
            successful_interactions=data.get("successful_interactions", 0),
            failed_interactions=data.get("failed_interactions", 0)
        )

    def __repr__(self) -> str:
        return (
            f"PatternSourceIdentity("
            f"lct_id={self.lct_id}, "
            f"trust={self.trust_score:.3f} [{self.trust_tier}], "
            f"value={self.value_score:.3f}, "
            f"interactions={self.interactions}, "
            f"witnesses={len(self.mrh.witnessing)})"
        )


# ============================================================================
# Backward Compatibility Alias
# ============================================================================

# For code that still references the old class name
LCTIdentity = PatternSourceIdentity


# ============================================================================
# Demo
# ============================================================================

def demo():
    """Demonstrate Pattern Source Identity system."""
    print("=" * 80)
    print("Pattern Source Identity (PSI) Demo")
    print("Using Web4 LCT Infrastructure: T3 Tensor, V3 Tensor, MRH")
    print("=" * 80)
    print()

    # Create new identity
    print("1. Creating new identity...")
    psi = PatternSourceIdentity(entity_type="ai")
    print(f"   LCT ID: {psi.lct_id}")
    print(f"   Trust: {psi.trust_score:.3f} [{psi.trust_tier}]")
    print(f"   Value: {psi.value_score:.3f}")
    print()

    # Show T3 tensor dimensions
    print("2. Initial T3 Tensor (6-dimensional trust):")
    t3 = psi.t3_tensor.to_dict()["dimensions"]
    for dim, val in t3.items():
        print(f"   {dim}: {val:.3f}")
    print()

    # Simulate interactions
    print("3. Simulating 100 successful interactions...")
    for _ in range(100):
        psi.record_interaction(success=True, quality_weight=0.8)

    print(f"   Trust: {psi.trust_score:.3f} [{psi.trust_tier}]")
    print(f"   Value: {psi.value_score:.3f}")
    print()

    # Add witnesses
    print("4. Adding witness attestations...")
    witness_lcts = [
        "lct:web4:oracle:trust:abc123",
        "lct:web4:oracle:quality:def456",
        "lct:web4:witness:time:ghi789"
    ]
    for witness in witness_lcts:
        psi.add_witness(witness, "quality")
        psi.add_witness(witness, "existence")

    print(f"   Witnesses in MRH: {len(psi.mrh.witnessing)}")
    print(f"   Trust after witnessing: {psi.trust_score:.3f}")
    print()

    # Show updated T3 tensor
    print("5. Updated T3 Tensor:")
    t3 = psi.t3_tensor.to_dict()["dimensions"]
    for dim, val in t3.items():
        print(f"   {dim}: {val:.3f}")
    print()

    # Sign a pattern
    print("6. Signing pattern with LCT provenance...")
    pattern = {
        "pattern_id": "test_pattern_001",
        "context": {"emotional": {"frustration": 0.5}},
        "context_tag": {"application": "test", "domain": "demo"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    signed = psi.sign_pattern(pattern)
    print(f"   Source LCT: {signed['provenance']['source_lct']}")
    print(f"   T3 Composite: {signed['provenance']['t3_snapshot']['composite_score']:.3f}")
    print(f"   MRH Witnesses: {len(signed['provenance']['mrh_witnesses'])}")
    print()

    # Verify pattern
    print("7. Verifying pattern provenance...")
    valid, source_lct, trust = PatternSourceIdentity.verify_pattern_provenance(signed)
    print(f"   Valid: {valid}")
    print(f"   Source: {source_lct}")
    print(f"   Trust: {trust:.3f}")
    print()

    # Save and load
    print("8. Testing persistence...")
    save_path = Path("/tmp/test_psi_identity.json")
    psi.save(save_path)
    print(f"   Saved to: {save_path}")

    loaded = PatternSourceIdentity.load(save_path)
    print(f"   Loaded: {loaded}")
    print()

    print("=" * 80)
    print("Demo complete!")
    print()
    print("Key changes from original implementation:")
    print("- Uses T3 tensor (6D) instead of simple trust_score")
    print("- Uses V3 tensor (6D) instead of simple reputation")
    print("- Uses MRH for witnessed relationships")
    print("- Pattern provenance includes T3 snapshot and MRH witnesses")
    print("- LCT ID format matches Web4 spec: lct:web4:{type}:{hash}")
    print("=" * 80)


if __name__ == "__main__":
    demo()
