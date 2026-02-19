"""
LCT Capability Levels - Reference Implementation (LEGACY — 6-dim tensors)
==========================================================================

⚠️  DEPRECATION NOTICE (2026-02-19)
    This file uses the LEGACY 6-dimensional T3/V3 tensor schema:
      T3: technical_competence, social_reliability, temporal_consistency,
          witness_count, lineage_depth, context_alignment
      V3: energy_balance, contribution_history, resource_stewardship,
          network_effects, reputation_capital, temporal_value

    The CANONICAL schema (per CLAUDE.md, ontology, JSON schema, and spec) uses
    3 root dimensions:
      T3: talent, training, temperament
      V3: valuation, veracity, validity

    CANONICAL version: web4-standard/implementation/reference/lct_capability_levels.py
    Migration functions: web4-trust-core/src/tensor/t3.rs::from_legacy_6d()

    This file is retained for backward compatibility with session/test imports
    (which primarily use EntityType and CapabilityLevel, not the tensor classes).
    New code SHOULD use the canonical version.

Implements the LCT Capability Levels specification for Web4.

Provides:
- Capability level definitions (0-5)
- Entity type registry
- Capability query protocol
- Stub generators for reduced implementations
- Level validation and upgrade paths

Usage:
    from core.lct_capability_levels import (
        CapabilityLevel,
        EntityType,
        LCTCapabilities,
        create_minimal_lct,
        query_capabilities,
        validate_lct_level
    )

    # Create a Level 2 plugin LCT
    lct = create_minimal_lct(
        entity_type=EntityType.PLUGIN,
        level=CapabilityLevel.BASIC,
        parent_lct="lct:web4:agent:orchestrator"
    )

    # Query capabilities
    caps = query_capabilities(lct)
    print(f"Level: {caps.capability_level}, T3: {caps.t3_supported}")

Author: CBP Session (Dennis + Claude)
Date: 2026-01-03
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum, IntEnum
from datetime import datetime, timezone
import hashlib
import json


# =============================================================================
# Capability Levels
# =============================================================================

class CapabilityLevel(IntEnum):
    """
    LCT Capability Levels (0-5).

    Each level builds on the previous, adding required components.
    """
    STUB = 0       # Placeholder reference, pending entity
    MINIMAL = 1    # Self-issued bootstrap, basic plugin identity
    BASIC = 2      # Operational plugins, simple agents with relationships
    STANDARD = 3   # Autonomous agents, federated entities with full tensors
    FULL = 4       # Society-issued identities, core infrastructure
    HARDWARE = 5   # Physical devices with hardware attestation


# =============================================================================
# Entity Types
# =============================================================================

class EntityType(str, Enum):
    """
    LCT Entity Types - what kind of entity this LCT represents.

    Core types from Web4 spec plus extended types for fractal use.
    """
    # Core types (from spec)
    HUMAN = "human"
    AI = "ai"
    ORGANIZATION = "organization"
    ROLE = "role"
    TASK = "task"
    RESOURCE = "resource"
    DEVICE = "device"
    SERVICE = "service"
    ORACLE = "oracle"
    ACCUMULATOR = "accumulator"
    DICTIONARY = "dictionary"
    HYBRID = "hybrid"

    # Extended types (for fractal use)
    PLUGIN = "plugin"
    SESSION = "session"
    RELATIONSHIP = "relationship"
    PATTERN = "pattern"
    SOCIETY = "society"
    WITNESS = "witness"
    PENDING = "pending"


# Typical capability level ranges for each entity type
ENTITY_LEVEL_RANGES: Dict[EntityType, Tuple[CapabilityLevel, CapabilityLevel]] = {
    EntityType.HUMAN: (CapabilityLevel.FULL, CapabilityLevel.HARDWARE),
    EntityType.AI: (CapabilityLevel.BASIC, CapabilityLevel.FULL),
    EntityType.ORGANIZATION: (CapabilityLevel.FULL, CapabilityLevel.FULL),
    EntityType.ROLE: (CapabilityLevel.MINIMAL, CapabilityLevel.STANDARD),
    EntityType.TASK: (CapabilityLevel.MINIMAL, CapabilityLevel.BASIC),
    EntityType.RESOURCE: (CapabilityLevel.MINIMAL, CapabilityLevel.STANDARD),
    EntityType.DEVICE: (CapabilityLevel.STANDARD, CapabilityLevel.HARDWARE),
    EntityType.SERVICE: (CapabilityLevel.BASIC, CapabilityLevel.FULL),
    EntityType.ORACLE: (CapabilityLevel.STANDARD, CapabilityLevel.FULL),
    EntityType.ACCUMULATOR: (CapabilityLevel.BASIC, CapabilityLevel.STANDARD),
    EntityType.DICTIONARY: (CapabilityLevel.STANDARD, CapabilityLevel.FULL),
    EntityType.HYBRID: (CapabilityLevel.MINIMAL, CapabilityLevel.HARDWARE),
    EntityType.PLUGIN: (CapabilityLevel.MINIMAL, CapabilityLevel.BASIC),
    EntityType.SESSION: (CapabilityLevel.MINIMAL, CapabilityLevel.BASIC),
    EntityType.RELATIONSHIP: (CapabilityLevel.MINIMAL, CapabilityLevel.BASIC),
    EntityType.PATTERN: (CapabilityLevel.MINIMAL, CapabilityLevel.STANDARD),
    EntityType.SOCIETY: (CapabilityLevel.FULL, CapabilityLevel.HARDWARE),
    EntityType.WITNESS: (CapabilityLevel.STANDARD, CapabilityLevel.FULL),
    EntityType.PENDING: (CapabilityLevel.STUB, CapabilityLevel.STUB),
}


# =============================================================================
# T3 Tensor (6 dimensions)
# =============================================================================

@dataclass
class T3Tensor:
    """
    Trust Tensor with 6 dimensions.

    Dimensions (all 0.0-1.0):
    - technical_competence: Can entity perform claimed capabilities?
    - social_reliability: Does entity honor commitments?
    - temporal_consistency: Is behavior consistent over time?
    - witness_count: How many entities witness this entity? (normalized)
    - lineage_depth: How deep is trust lineage? (normalized)
    - context_alignment: How well aligned with current context?
    """
    technical_competence: Optional[float] = None
    social_reliability: Optional[float] = None
    temporal_consistency: Optional[float] = None
    witness_count: Optional[float] = None
    lineage_depth: Optional[float] = None
    context_alignment: Optional[float] = None

    composite_score: Optional[float] = None
    last_computed: Optional[str] = None
    computation_witnesses: List[str] = field(default_factory=list)
    stub: bool = False
    reason: Optional[str] = None

    # Trust ceiling for software-bound vs hardware-bound entities
    trust_ceiling: Optional[float] = None        # Max trust (1.0 for hardware, 0.85 for software)
    trust_ceiling_reason: Optional[str] = None   # Why ceiling exists (e.g., "software_binding")

    def recompute_composite(self) -> float:
        """Recompute composite score from dimensions."""
        dims = [
            self.technical_competence,
            self.social_reliability,
            self.temporal_consistency,
            self.witness_count,
            self.lineage_depth,
            self.context_alignment
        ]
        valid = [d for d in dims if d is not None]
        if not valid:
            self.composite_score = None
            return 0.0

        self.composite_score = sum(valid) / len(valid)
        self.last_computed = datetime.now(timezone.utc).isoformat()
        return self.composite_score

    def is_stub(self) -> bool:
        """Check if this is a stub tensor."""
        return self.stub or all(d is None for d in [
            self.technical_competence, self.social_reliability,
            self.temporal_consistency, self.witness_count,
            self.lineage_depth, self.context_alignment
        ])

    @classmethod
    def create_stub(cls, reason: str = "Not implemented") -> 'T3Tensor':
        """Create a stub T3 tensor."""
        return cls(stub=True, reason=reason)

    @classmethod
    def create_minimal(
        cls,
        trust_ceiling: Optional[float] = None,
        trust_ceiling_reason: Optional[str] = None
    ) -> 'T3Tensor':
        """Create minimal T3 tensor for Level 1."""
        t3 = cls(
            technical_competence=0.1,
            social_reliability=0.1,
            temporal_consistency=0.1,
            witness_count=0.0,
            lineage_depth=0.0,
            context_alignment=0.1,
            stub=False,
            trust_ceiling=trust_ceiling,
            trust_ceiling_reason=trust_ceiling_reason
        )
        t3.recompute_composite()
        return t3

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
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
            "computation_witnesses": self.computation_witnesses,
            "stub": self.stub if self.stub else None,
            "reason": self.reason
        }


# =============================================================================
# V3 Tensor (6 dimensions)
# =============================================================================

@dataclass
class V3Tensor:
    """
    Value Tensor with 6 dimensions.

    Dimensions:
    - energy_balance: ATP/ADP balance (integer, can be negative)
    - contribution_history: Historical value contributions (0.0-1.0)
    - resource_stewardship: How well entity manages resources (0.0-1.0)
    - network_effects: Value created for others (0.0-1.0)
    - reputation_capital: Accumulated social capital (0.0-1.0)
    - temporal_value: Value persistence over time (0.0-1.0)
    """
    energy_balance: Optional[int] = None
    contribution_history: Optional[float] = None
    resource_stewardship: Optional[float] = None
    network_effects: Optional[float] = None
    reputation_capital: Optional[float] = None
    temporal_value: Optional[float] = None

    composite_score: Optional[float] = None
    last_computed: Optional[str] = None
    computation_witnesses: List[str] = field(default_factory=list)
    stub: bool = False
    reason: Optional[str] = None

    def recompute_composite(self) -> float:
        """Recompute composite score from dimensions (excluding energy_balance)."""
        dims = [
            self.contribution_history,
            self.resource_stewardship,
            self.network_effects,
            self.reputation_capital,
            self.temporal_value
        ]
        valid = [d for d in dims if d is not None]
        if not valid:
            self.composite_score = None
            return 0.0

        self.composite_score = sum(valid) / len(valid)
        self.last_computed = datetime.now(timezone.utc).isoformat()
        return self.composite_score

    def is_stub(self) -> bool:
        """Check if this is a stub tensor."""
        return self.stub

    @classmethod
    def create_stub(cls, reason: str = "Not implemented") -> 'V3Tensor':
        """Create a stub V3 tensor."""
        return cls(stub=True, reason=reason)

    @classmethod
    def create_zero(cls) -> 'V3Tensor':
        """Create zero V3 tensor for Level 1."""
        v3 = cls(
            energy_balance=0,
            contribution_history=0.0,
            resource_stewardship=0.0,
            network_effects=0.0,
            reputation_capital=0.0,
            temporal_value=0.0,
            stub=False
        )
        v3.recompute_composite()
        return v3

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
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
            "computation_witnesses": self.computation_witnesses,
            "stub": self.stub if self.stub else None,
            "reason": self.reason
        }


# =============================================================================
# MRH Relationships
# =============================================================================

@dataclass
class MRHRelationship:
    """A single MRH relationship."""
    lct_id: str
    relationship_type: str  # "bound", "paired", "witnessing"
    subtype: Optional[str] = None  # e.g., "parent", "operational", "time"
    permanent: bool = False
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        d = {
            "lct_id": self.lct_id,
            "type": self.subtype or self.relationship_type,
            "ts": self.timestamp
        }
        if self.relationship_type == "paired":
            d["permanent"] = self.permanent
            d["pairing_type"] = self.subtype or "operational"
        if self.relationship_type == "witnessing":
            d["role"] = self.subtype or "existence"
            d["witness_count"] = self.metadata.get("witness_count", 1)
        if self.relationship_type == "bound":
            d["binding_context"] = self.metadata.get("binding_context", "deployment")
        return d


@dataclass
class MRH:
    """Markov Relevancy Horizon - relationship container."""
    bound: List[MRHRelationship] = field(default_factory=list)
    paired: List[MRHRelationship] = field(default_factory=list)
    witnessing: List[MRHRelationship] = field(default_factory=list)
    horizon_depth: int = 3
    last_updated: Optional[str] = None

    def add_bound(self, lct_id: str, subtype: str = "parent", **kwargs) -> None:
        """Add binding relationship."""
        self.bound.append(MRHRelationship(
            lct_id=lct_id,
            relationship_type="bound",
            subtype=subtype,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=kwargs
        ))
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def add_paired(self, lct_id: str, subtype: str = "operational",
                   permanent: bool = False, **kwargs) -> None:
        """Add pairing relationship."""
        self.paired.append(MRHRelationship(
            lct_id=lct_id,
            relationship_type="paired",
            subtype=subtype,
            permanent=permanent,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=kwargs
        ))
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def add_witnessing(self, lct_id: str, role: str = "existence", **kwargs) -> None:
        """Add witnessing relationship."""
        self.witnessing.append(MRHRelationship(
            lct_id=lct_id,
            relationship_type="witnessing",
            subtype=role,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=kwargs
        ))
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def has_relationships(self) -> bool:
        """Check if MRH has any relationships."""
        return bool(self.bound or self.paired or self.witnessing)

    def relationship_types(self) -> List[str]:
        """Get list of relationship types present."""
        types = []
        if self.bound:
            types.append("bound")
        if self.paired:
            types.append("paired")
        if self.witnessing:
            types.append("witnessing")
        return types

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "bound": [r.to_dict() for r in self.bound],
            "paired": [r.to_dict() for r in self.paired],
            "witnessing": [r.to_dict() for r in self.witnessing],
            "horizon_depth": self.horizon_depth,
            "last_updated": self.last_updated
        }


# =============================================================================
# LCT Structure
# =============================================================================

@dataclass
class LCTBinding:
    """Cryptographic binding section."""
    entity_type: str
    public_key: Optional[str] = None
    hardware_anchor: Optional[str] = None
    hardware_type: Optional[str] = None  # tpm2, trustzone, secure_element
    created_at: Optional[str] = None
    binding_proof: Optional[str] = None

    def is_hardware_bound(self) -> bool:
        """Check if binding is hardware-anchored."""
        return self.hardware_anchor is not None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "entity_type": self.entity_type,
            "public_key": self.public_key,
            "hardware_anchor": self.hardware_anchor,
            "hardware_type": self.hardware_type,
            "created_at": self.created_at,
            "binding_proof": self.binding_proof
        }


@dataclass
class LCTPolicy:
    """Policy section with capabilities and constraints."""
    capabilities: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "capabilities": self.capabilities,
            "constraints": self.constraints
        }


@dataclass
class BirthCertificate:
    """Birth certificate section (Level 4+)."""
    issuing_society: Optional[str] = None
    citizen_role: Optional[str] = None
    birth_timestamp: Optional[str] = None
    birth_witnesses: List[str] = field(default_factory=list)
    genesis_block_hash: Optional[str] = None
    birth_context: Optional[str] = None
    stub: bool = False
    reason: Optional[str] = None

    def is_stub(self) -> bool:
        """Check if this is a stub."""
        return self.stub or self.issuing_society is None

    @classmethod
    def create_stub(cls, reason: str = "Self-issued entity") -> 'BirthCertificate':
        """Create a stub birth certificate."""
        return cls(stub=True, reason=reason)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        if self.stub:
            return {
                "issuing_society": None,
                "citizen_role": None,
                "birth_witnesses": [],
                "stub": True,
                "reason": self.reason
            }
        return {
            "issuing_society": self.issuing_society,
            "citizen_role": self.citizen_role,
            "birth_timestamp": self.birth_timestamp,
            "birth_witnesses": self.birth_witnesses,
            "genesis_block_hash": self.genesis_block_hash,
            "birth_context": self.birth_context
        }


@dataclass
class LCT:
    """
    Complete LCT structure with capability level support.

    Implements the LCT Capability Levels specification.
    """
    lct_id: str
    capability_level: CapabilityLevel
    entity_type: EntityType

    subject: Optional[str] = None
    binding: Optional[LCTBinding] = None
    mrh: Optional[MRH] = None
    policy: Optional[LCTPolicy] = None
    t3_tensor: Optional[T3Tensor] = None
    v3_tensor: Optional[V3Tensor] = None
    birth_certificate: Optional[BirthCertificate] = None
    attestations: List[Dict] = field(default_factory=list)
    lineage: List[Dict] = field(default_factory=list)
    revocation: Optional[Dict] = None

    def __post_init__(self):
        """Initialize stubs based on capability level."""
        if self.mrh is None:
            self.mrh = MRH()
        if self.policy is None:
            self.policy = LCTPolicy()
        if self.t3_tensor is None:
            if self.capability_level >= CapabilityLevel.MINIMAL:
                self.t3_tensor = T3Tensor.create_minimal()
            else:
                self.t3_tensor = T3Tensor.create_stub("Level 0 entity")
        if self.v3_tensor is None:
            if self.capability_level >= CapabilityLevel.MINIMAL:
                self.v3_tensor = V3Tensor.create_zero()
            else:
                self.v3_tensor = V3Tensor.create_stub("Level 0 entity")
        if self.birth_certificate is None:
            self.birth_certificate = BirthCertificate.create_stub()

    def to_dict(self) -> Dict:
        """Convert to canonical dictionary format."""
        d = {
            "lct_id": self.lct_id,
            "capability_level": self.capability_level.value,
            "entity_type": self.entity_type.value,
        }

        if self.subject:
            d["subject"] = self.subject
        if self.binding:
            d["binding"] = self.binding.to_dict()
        if self.mrh:
            d["mrh"] = self.mrh.to_dict()
        if self.policy:
            d["policy"] = self.policy.to_dict()
        if self.t3_tensor:
            d["t3_tensor"] = self.t3_tensor.to_dict()
        if self.v3_tensor:
            d["v3_tensor"] = self.v3_tensor.to_dict()
        if self.birth_certificate:
            d["birth_certificate"] = self.birth_certificate.to_dict()
        if self.attestations:
            d["attestations"] = self.attestations
        if self.lineage:
            d["lineage"] = self.lineage
        if self.revocation:
            d["revocation"] = self.revocation

        return d

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# =============================================================================
# Capability Query Protocol
# =============================================================================

@dataclass
class CapabilityQueryResponse:
    """Response to a capability discovery query."""
    source_lct: str
    capability_level: CapabilityLevel
    entity_type: EntityType

    # Component support
    binding_implemented: bool = False
    binding_hardware_anchored: bool = False
    binding_key_algorithm: Optional[str] = None

    mrh_implemented: bool = False
    mrh_relationship_types: List[str] = field(default_factory=list)
    mrh_horizon_depth: int = 0

    t3_implemented: bool = False
    t3_dimensions: int = 0
    t3_oracle_computed: bool = False

    v3_implemented: bool = False
    v3_dimensions: int = 0
    v3_oracle_computed: bool = False

    birth_certificate_implemented: bool = False
    attestations_count: int = 0
    lineage_implemented: bool = False

    # Relationship support
    can_be_bound_by: List[str] = field(default_factory=list)
    can_pair_with: List[str] = field(default_factory=list)
    can_witness: List[str] = field(default_factory=list)
    can_be_witnessed_by: List[str] = field(default_factory=list)

    # Trust summary
    trust_tier: str = "unknown"
    composite_t3: Optional[float] = None
    composite_v3: Optional[float] = None

    timestamp: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "response_type": "capability_discovery",
            "source_lct": self.source_lct,
            "capability_level": self.capability_level.value,
            "entity_type": self.entity_type.value,

            "supported_components": {
                "binding": {
                    "implemented": self.binding_implemented,
                    "hardware_anchored": self.binding_hardware_anchored,
                    "key_algorithm": self.binding_key_algorithm
                },
                "mrh": {
                    "implemented": self.mrh_implemented,
                    "relationship_types": self.mrh_relationship_types,
                    "horizon_depth": self.mrh_horizon_depth
                },
                "t3_tensor": {
                    "implemented": self.t3_implemented,
                    "dimensions": self.t3_dimensions,
                    "oracle_computed": self.t3_oracle_computed
                },
                "v3_tensor": {
                    "implemented": self.v3_implemented,
                    "dimensions": self.v3_dimensions,
                    "oracle_computed": self.v3_oracle_computed
                },
                "birth_certificate": {
                    "implemented": self.birth_certificate_implemented,
                    "stub": not self.birth_certificate_implemented
                },
                "attestations": {
                    "implemented": self.attestations_count > 0,
                    "count": self.attestations_count
                },
                "lineage": {
                    "implemented": self.lineage_implemented,
                    "stub": not self.lineage_implemented
                }
            },

            "relationship_support": {
                "can_be_bound_by": self.can_be_bound_by,
                "can_pair_with": self.can_pair_with,
                "can_witness": self.can_witness,
                "can_be_witnessed_by": self.can_be_witnessed_by
            },

            "trust_tier": self.trust_tier,
            "composite_t3": self.composite_t3,
            "composite_v3": self.composite_v3,

            "timestamp": self.timestamp
        }


def query_capabilities(lct: LCT) -> CapabilityQueryResponse:
    """
    Query an LCT's capabilities.

    Returns a CapabilityQueryResponse with full capability information.
    """
    response = CapabilityQueryResponse(
        source_lct=lct.lct_id,
        capability_level=lct.capability_level,
        entity_type=lct.entity_type,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

    # Binding
    if lct.binding:
        response.binding_implemented = lct.binding.public_key is not None
        response.binding_hardware_anchored = lct.binding.is_hardware_bound()
        response.binding_key_algorithm = "Ed25519" if lct.binding.public_key else None

    # MRH
    if lct.mrh:
        response.mrh_implemented = lct.mrh.has_relationships()
        response.mrh_relationship_types = lct.mrh.relationship_types()
        response.mrh_horizon_depth = lct.mrh.horizon_depth

    # T3 Tensor
    if lct.t3_tensor and not lct.t3_tensor.is_stub():
        response.t3_implemented = True
        # Count non-None dimensions
        dims = [lct.t3_tensor.technical_competence, lct.t3_tensor.social_reliability,
                lct.t3_tensor.temporal_consistency, lct.t3_tensor.witness_count,
                lct.t3_tensor.lineage_depth, lct.t3_tensor.context_alignment]
        response.t3_dimensions = sum(1 for d in dims if d is not None)
        response.t3_oracle_computed = bool(lct.t3_tensor.computation_witnesses)
        response.composite_t3 = lct.t3_tensor.composite_score

    # V3 Tensor
    if lct.v3_tensor and not lct.v3_tensor.is_stub():
        response.v3_implemented = True
        dims = [lct.v3_tensor.contribution_history, lct.v3_tensor.resource_stewardship,
                lct.v3_tensor.network_effects, lct.v3_tensor.reputation_capital,
                lct.v3_tensor.temporal_value]
        response.v3_dimensions = sum(1 for d in dims if d is not None) + (
            1 if lct.v3_tensor.energy_balance is not None else 0
        )
        response.v3_oracle_computed = bool(lct.v3_tensor.computation_witnesses)
        response.composite_v3 = lct.v3_tensor.composite_score

    # Birth certificate
    if lct.birth_certificate and not lct.birth_certificate.is_stub():
        response.birth_certificate_implemented = True

    # Attestations and lineage
    response.attestations_count = len(lct.attestations)
    response.lineage_implemented = len(lct.lineage) > 0

    # Relationship support (based on entity type and level)
    response.can_be_bound_by = _get_bindable_types(lct.entity_type)
    response.can_pair_with = _get_pairable_types(lct.entity_type, lct.capability_level)
    response.can_witness = _get_witnessable_types(lct.entity_type, lct.capability_level)
    response.can_be_witnessed_by = _get_witness_sources(lct.entity_type)

    # Trust tier
    response.trust_tier = _compute_trust_tier(response.composite_t3)

    return response


def _get_bindable_types(entity_type: EntityType) -> List[str]:
    """Get entity types that can bind to this entity."""
    binding_rules = {
        EntityType.PLUGIN: ["ai", "device", "service"],
        EntityType.SESSION: ["ai", "human"],
        EntityType.AI: ["device", "organization"],
        EntityType.DEVICE: ["organization"],
        EntityType.SERVICE: ["device", "organization"],
    }
    return binding_rules.get(entity_type, [])


def _get_pairable_types(entity_type: EntityType, level: CapabilityLevel) -> List[str]:
    """Get entity types that can pair with this entity."""
    if level < CapabilityLevel.BASIC:
        return []

    pairing_rules = {
        EntityType.PLUGIN: ["ai", "plugin", "service"],
        EntityType.AI: ["plugin", "service", "ai", "human", "device"],
        EntityType.HUMAN: ["ai", "service", "organization"],
        EntityType.SERVICE: ["ai", "plugin", "service", "human"],
        EntityType.DEVICE: ["ai", "service", "device"],
    }
    return pairing_rules.get(entity_type, ["ai", "service"])


def _get_witnessable_types(entity_type: EntityType, level: CapabilityLevel) -> List[str]:
    """Get entity types this entity can witness."""
    if level < CapabilityLevel.STANDARD:
        return []

    witness_rules = {
        EntityType.ORACLE: ["ai", "device", "service", "human"],
        EntityType.AI: ["plugin", "task", "session"],
        EntityType.HUMAN: ["ai", "service", "organization"],
        EntityType.WITNESS: ["ai", "device", "service", "human", "organization"],
    }
    return witness_rules.get(entity_type, [])


def _get_witness_sources(entity_type: EntityType) -> List[str]:
    """Get entity types that can witness this entity."""
    return ["oracle", "human", "ai", "witness", "society"]


def _compute_trust_tier(composite_t3: Optional[float]) -> str:
    """Compute trust tier from T3 composite score."""
    if composite_t3 is None:
        return "unknown"
    elif composite_t3 < 0.2:
        return "untrusted"
    elif composite_t3 < 0.4:
        return "low"
    elif composite_t3 < 0.6:
        return "medium"
    elif composite_t3 < 0.8:
        return "high"
    else:
        return "exceptional"


# =============================================================================
# LCT Creation Helpers
# =============================================================================

def generate_lct_id(entity_type: EntityType, name: str) -> str:
    """Generate a canonical LCT ID."""
    # Create hash from name and timestamp
    content = f"{entity_type.value}:{name}:{datetime.now(timezone.utc).isoformat()}"
    hash_bytes = hashlib.sha256(content.encode()).hexdigest()[:16]
    return f"lct:web4:{entity_type.value}:{hash_bytes}"


def create_minimal_lct(
    entity_type: EntityType,
    level: CapabilityLevel = CapabilityLevel.MINIMAL,
    name: Optional[str] = None,
    parent_lct: Optional[str] = None,
    public_key: Optional[str] = None
) -> LCT:
    """
    Create an LCT at the specified capability level.

    Args:
        entity_type: Type of entity
        level: Capability level (0-5)
        name: Entity name (used in ID generation)
        parent_lct: Parent LCT for binding relationship
        public_key: Public key for binding (generated if None)

    Returns:
        LCT instance
    """
    name = name or f"{entity_type.value}-{datetime.now().strftime('%H%M%S')}"
    lct_id = generate_lct_id(entity_type, name)

    # Create LCT
    lct = LCT(
        lct_id=lct_id,
        capability_level=level,
        entity_type=entity_type,
        subject=f"did:web4:key:{lct_id.split(':')[-1]}"
    )

    # Add binding for Level 1+
    if level >= CapabilityLevel.MINIMAL:
        lct.binding = LCTBinding(
            entity_type=entity_type.value,
            public_key=public_key or f"mb64:ed25519:{lct_id.split(':')[-1]}",
            created_at=datetime.now(timezone.utc).isoformat()
        )

    # Add parent binding for Level 2+
    if level >= CapabilityLevel.BASIC and parent_lct:
        lct.mrh.add_bound(parent_lct, subtype="parent", binding_context="deployment")

    return lct


# =============================================================================
# Level Validation
# =============================================================================

@dataclass
class ValidationResult:
    """Result of LCT level validation."""
    valid: bool
    current_level: CapabilityLevel
    claimed_level: CapabilityLevel
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate_lct_level(lct: LCT) -> ValidationResult:
    """
    Validate that an LCT meets the requirements for its claimed level.

    Returns ValidationResult with any errors/warnings.
    """
    result = ValidationResult(
        valid=True,
        current_level=CapabilityLevel.STUB,
        claimed_level=lct.capability_level
    )

    # Level 0: Just needs lct_id
    if not lct.lct_id or not lct.lct_id.startswith("lct:web4:"):
        result.errors.append("Invalid lct_id format")
        result.valid = False
        return result

    result.current_level = CapabilityLevel.STUB

    # Level 1: Needs binding with public key, T3/V3 tensors
    if lct.capability_level >= CapabilityLevel.MINIMAL:
        if not lct.binding or not lct.binding.public_key:
            result.errors.append("Level 1+ requires binding with public_key")
            result.valid = False
        else:
            result.current_level = CapabilityLevel.MINIMAL

        if lct.t3_tensor is None or lct.t3_tensor.is_stub():
            result.errors.append("Level 1+ requires non-stub T3 tensor")
            result.valid = False

        if lct.v3_tensor is None or lct.v3_tensor.is_stub():
            result.errors.append("Level 1+ requires non-stub V3 tensor")
            result.valid = False

    # Level 2: Needs at least one MRH relationship
    if lct.capability_level >= CapabilityLevel.BASIC:
        if not lct.mrh or not lct.mrh.has_relationships():
            result.errors.append("Level 2+ requires at least one MRH relationship")
            result.valid = False
        else:
            result.current_level = CapabilityLevel.BASIC

        if not lct.policy or not lct.policy.capabilities:
            result.warnings.append("Level 2+ should have at least one policy capability")

    # Level 3: Needs witnessing, oracle-computed tensors, attestations
    if lct.capability_level >= CapabilityLevel.STANDARD:
        if not lct.mrh.witnessing:
            result.warnings.append("Level 3+ should have witnessing relationships")

        if lct.t3_tensor and not lct.t3_tensor.computation_witnesses:
            result.warnings.append("Level 3+ should have oracle-computed T3")

        if lct.v3_tensor and (lct.v3_tensor.energy_balance is None or
                              lct.v3_tensor.energy_balance == 0):
            result.warnings.append("Level 3+ should have non-zero ATP balance")

        if not lct.attestations:
            result.warnings.append("Level 3+ should have at least one attestation")

        if result.valid:
            result.current_level = CapabilityLevel.STANDARD

    # Level 4: Needs birth certificate with witnesses
    if lct.capability_level >= CapabilityLevel.FULL:
        if not lct.birth_certificate or lct.birth_certificate.is_stub():
            result.errors.append("Level 4+ requires birth certificate")
            result.valid = False
        elif len(lct.birth_certificate.birth_witnesses) < 3:
            result.errors.append("Level 4+ requires minimum 3 birth witnesses")
            result.valid = False
        else:
            result.current_level = CapabilityLevel.FULL

        # Check for permanent citizen pairing
        has_citizen_pairing = any(
            p.subtype == "birth_certificate" and p.permanent
            for p in lct.mrh.paired
        )
        if not has_citizen_pairing:
            result.errors.append("Level 4+ requires permanent citizen pairing")
            result.valid = False

    # Level 5: Needs hardware binding
    if lct.capability_level >= CapabilityLevel.HARDWARE:
        if not lct.binding or not lct.binding.is_hardware_bound():
            result.errors.append("Level 5 requires hardware-anchored binding")
            result.valid = False
        else:
            result.current_level = CapabilityLevel.HARDWARE

    return result


# =============================================================================
# Demo
# =============================================================================

def demo():
    """Demonstrate LCT capability levels."""
    print("=" * 70)
    print("LCT CAPABILITY LEVELS DEMONSTRATION")
    print("=" * 70)
    print()

    # Create Level 1 plugin
    print("Creating Level 1 Plugin LCT...")
    plugin_lct = create_minimal_lct(
        entity_type=EntityType.PLUGIN,
        level=CapabilityLevel.MINIMAL,
        name="vision-irp"
    )
    print(f"  LCT ID: {plugin_lct.lct_id}")
    print(f"  Level: {plugin_lct.capability_level.name}")
    print(f"  T3 composite: {plugin_lct.t3_tensor.composite_score:.3f}")
    print()

    # Validate
    result = validate_lct_level(plugin_lct)
    print(f"  Validation: {'PASS' if result.valid else 'FAIL'}")
    if result.errors:
        for e in result.errors:
            print(f"    ERROR: {e}")
    print()

    # Create Level 2 plugin with parent binding
    print("Creating Level 2 Plugin LCT with parent binding...")
    plugin_lct2 = create_minimal_lct(
        entity_type=EntityType.PLUGIN,
        level=CapabilityLevel.BASIC,
        name="audio-irp",
        parent_lct="lct:web4:agent:sage-orchestrator"
    )
    plugin_lct2.policy.capabilities = ["execute:irp", "read:patterns"]
    print(f"  LCT ID: {plugin_lct2.lct_id}")
    print(f"  Level: {plugin_lct2.capability_level.name}")
    print(f"  MRH relationships: {plugin_lct2.mrh.relationship_types()}")
    print()

    # Query capabilities
    print("Querying capabilities...")
    caps = query_capabilities(plugin_lct2)
    print(f"  Capability level: {caps.capability_level.name}")
    print(f"  Entity type: {caps.entity_type.value}")
    print(f"  MRH implemented: {caps.mrh_implemented}")
    print(f"  T3 dimensions: {caps.t3_dimensions}")
    print(f"  Trust tier: {caps.trust_tier}")
    print(f"  Can pair with: {caps.can_pair_with}")
    print()

    # Validate
    result = validate_lct_level(plugin_lct2)
    print(f"  Validation: {'PASS' if result.valid else 'FAIL'}")
    if result.warnings:
        for w in result.warnings:
            print(f"    WARNING: {w}")
    print()

    # Create Level 3 agent
    print("Creating Level 3 AI Agent LCT...")
    agent_lct = create_minimal_lct(
        entity_type=EntityType.AI,
        level=CapabilityLevel.STANDARD,
        name="sage-consciousness"
    )
    agent_lct.mrh.add_paired("lct:web4:plugin:vision-irp", subtype="operational")
    agent_lct.mrh.add_witnessing("lct:web4:oracle:time:global", role="time")
    agent_lct.t3_tensor.computation_witnesses = ["lct:web4:oracle:trust:federation"]
    agent_lct.v3_tensor.energy_balance = 100
    agent_lct.attestations = [{"witness": "did:web4:key:...", "type": "existence"}]

    caps = query_capabilities(agent_lct)
    print(f"  LCT ID: {agent_lct.lct_id}")
    print(f"  Level: {agent_lct.capability_level.name}")
    print(f"  Trust tier: {caps.trust_tier}")
    print(f"  Can witness: {caps.can_witness}")
    print()

    result = validate_lct_level(agent_lct)
    print(f"  Validation: {'PASS' if result.valid else 'FAIL'}")
    print()

    print("=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    demo()
