#!/usr/bin/env python3
"""
Web4 LCT Capability Levels — Reference Implementation

Implements the 6-level capability framework from:
  web4-standard/core-spec/lct-capability-levels.md

Levels:
  0 STUB      — Placeholder reference, pending entity
  1 MINIMAL   — Self-issued bootstrap, basic plugin identity
  2 BASIC     — Operational plugins with relationships
  3 STANDARD  — Autonomous agents with full tensors
  4 FULL      — Society-issued with birth certificate
  5 HARDWARE  — Hardware-bound identity (TPM/TrustZone)

Features:
  - LCTEntity with full capability-level semantics
  - CapabilityValidator: validates claimed level vs actual components
  - CapabilityQuery/CapabilityResponse: discovery protocol
  - LevelUpgrader: upgrade path with constraint enforcement
  - StubComponent: standardized stub format
  - CrossDomainNegotiator: common ground protocol
  - EntityLevelRegistry: entity-type → level range enforcement
  - SecurityChecker: misrepresentation, stub exploitation, upgrade attack detection
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


# ══════════════════════════════════════════════════════════════
# §2 — Capability Levels
# ══════════════════════════════════════════════════════════════

class CapLevel(IntEnum):
    STUB = 0
    MINIMAL = 1
    BASIC = 2
    STANDARD = 3
    FULL = 4
    HARDWARE = 5


LEVEL_NAMES = {
    CapLevel.STUB: "STUB",
    CapLevel.MINIMAL: "MINIMAL",
    CapLevel.BASIC: "BASIC",
    CapLevel.STANDARD: "STANDARD",
    CapLevel.FULL: "FULL",
    CapLevel.HARDWARE: "HARDWARE",
}

TRUST_TIERS = {
    CapLevel.STUB: (0.0, 0.0),
    CapLevel.MINIMAL: (0.0, 0.2),
    CapLevel.BASIC: (0.2, 0.4),
    CapLevel.STANDARD: (0.4, 0.6),
    CapLevel.FULL: (0.6, 0.8),
    CapLevel.HARDWARE: (0.8, 1.0),
}

TRUST_TIER_NAMES = {
    CapLevel.STUB: "untrusted",
    CapLevel.MINIMAL: "low",
    CapLevel.BASIC: "basic",
    CapLevel.STANDARD: "medium",
    CapLevel.FULL: "high",
    CapLevel.HARDWARE: "maximum",
}


# ══════════════════════════════════════════════════════════════
# §3 — Entity Types & Level Ranges
# ══════════════════════════════════════════════════════════════

ENTITY_LEVEL_RANGES = {
    # Core types
    "human": (4, 5),
    "ai": (2, 4),
    "organization": (4, 4),
    "role": (1, 3),
    "task": (1, 2),
    "resource": (1, 3),
    "device": (3, 5),
    "service": (2, 4),
    "oracle": (3, 4),
    "accumulator": (2, 3),
    "dictionary": (3, 4),
    "hybrid": (2, 5),
    # Extended types
    "plugin": (1, 2),
    "session": (1, 2),
    "relationship": (1, 2),
    "pattern": (1, 3),
    "society": (4, 5),
    "witness": (3, 4),
    "pending": (0, 0),
    "policy": (2, 4),
    "infrastructure": (1, 3),
}


# ══════════════════════════════════════════════════════════════
# §5 — Stub Format
# ══════════════════════════════════════════════════════════════

@dataclass
class StubComponent:
    """§5.2 — All stubs MUST contain stub=True and reason."""
    reason: str
    stub: bool = True

    def to_dict(self) -> dict:
        return {"stub": True, "reason": self.reason}

    @classmethod
    def from_dict(cls, d: dict) -> "StubComponent":
        return cls(reason=d.get("reason", "Unknown"))


# ══════════════════════════════════════════════════════════════
# T3/V3 Tensors (6 dimensions per spec §2.3+)
# ══════════════════════════════════════════════════════════════

T3_DIMENSIONS = [
    "technical_competence",
    "social_reliability",
    "temporal_consistency",
    "witness_count",
    "lineage_depth",
    "context_alignment",
]

V3_DIMENSIONS = [
    "energy_balance",
    "contribution_history",
    "resource_stewardship",
    "network_effects",
    "reputation_capital",
    "temporal_value",
]


@dataclass
class Tensor:
    """6-dimensional trust or value tensor."""
    dimensions: dict
    composite_score: Optional[float] = None
    last_computed: Optional[str] = None
    computation_witnesses: list = field(default_factory=list)
    stub: bool = False
    reason: Optional[str] = None

    def is_stub(self) -> bool:
        return self.stub

    def non_null_count(self) -> int:
        return sum(1 for v in self.dimensions.values() if v is not None)

    def non_zero_count(self) -> int:
        return sum(1 for v in self.dimensions.values() if v is not None and v != 0)

    def compute_composite(self) -> float:
        vals = [v for v in self.dimensions.values() if v is not None and isinstance(v, (int, float))]
        if not vals:
            return 0.0
        self.composite_score = round(sum(vals) / len(vals), 4)
        return self.composite_score

    def to_dict(self) -> dict:
        d = {"dimensions": dict(self.dimensions)}
        if self.composite_score is not None:
            d["composite_score"] = self.composite_score
        if self.last_computed:
            d["last_computed"] = self.last_computed
        if self.computation_witnesses:
            d["computation_witnesses"] = list(self.computation_witnesses)
        if self.stub:
            d["stub"] = True
            d["reason"] = self.reason or "Uninitialized"
        return d

    @classmethod
    def make_stub(cls, dim_names: list, reason: str) -> "Tensor":
        return cls(
            dimensions={d: None for d in dim_names},
            composite_score=None,
            stub=True,
            reason=reason,
        )

    @classmethod
    def make_initial(cls, dim_names: list, initial_value: float = 0.0) -> "Tensor":
        t = cls(
            dimensions={d: initial_value for d in dim_names},
            last_computed=_now(),
        )
        t.compute_composite()
        return t


# ══════════════════════════════════════════════════════════════
# Binding, MRH, BirthCertificate, Attestation, Lineage, Revocation
# ══════════════════════════════════════════════════════════════

@dataclass
class Binding:
    entity_type: str
    public_key: Optional[str] = None
    hardware_anchor: Optional[str] = None
    hardware_type: Optional[str] = None
    attestation_chain: list = field(default_factory=list)
    created_at: Optional[str] = None
    binding_proof: Optional[str] = None

    def is_hardware_bound(self) -> bool:
        return self.hardware_anchor is not None and self.hardware_type is not None

    def to_dict(self) -> dict:
        d = {"entity_type": self.entity_type}
        if self.public_key:
            d["public_key"] = self.public_key
        if self.hardware_anchor:
            d["hardware_anchor"] = self.hardware_anchor
        if self.hardware_type:
            d["hardware_type"] = self.hardware_type
        if self.attestation_chain:
            d["attestation_chain"] = list(self.attestation_chain)
        if self.created_at:
            d["created_at"] = self.created_at
        if self.binding_proof:
            d["binding_proof"] = self.binding_proof
        return d


@dataclass
class MRHRelationship:
    lct_id: str
    rel_type: str = "peer"
    binding_context: Optional[str] = None
    pairing_type: Optional[str] = None
    permanent: bool = False
    role: Optional[str] = None
    last_attestation: Optional[str] = None
    witness_count: int = 0
    ts: Optional[str] = None

    def to_dict(self) -> dict:
        d = {"lct_id": self.lct_id}
        if self.rel_type:
            d["type"] = self.rel_type
        if self.binding_context:
            d["binding_context"] = self.binding_context
        if self.pairing_type:
            d["pairing_type"] = self.pairing_type
        if self.permanent:
            d["permanent"] = True
        if self.role:
            d["role"] = self.role
        if self.last_attestation:
            d["last_attestation"] = self.last_attestation
        if self.witness_count:
            d["witness_count"] = self.witness_count
        if self.ts:
            d["ts"] = self.ts
        return d


@dataclass
class MRH:
    bound: list = field(default_factory=list)
    paired: list = field(default_factory=list)
    witnessing: list = field(default_factory=list)
    horizon_depth: int = 0
    last_updated: Optional[str] = None

    def has_relationships(self) -> bool:
        return bool(self.bound or self.paired)

    def has_witnessing(self) -> bool:
        return bool(self.witnessing)

    def to_dict(self) -> dict:
        return {
            "bound": [r.to_dict() for r in self.bound],
            "paired": [r.to_dict() for r in self.paired],
            "witnessing": [r.to_dict() for r in self.witnessing],
            "horizon_depth": self.horizon_depth,
            "last_updated": self.last_updated or _now(),
        }


@dataclass
class Policy:
    capabilities: list = field(default_factory=list)
    constraints: dict = field(default_factory=dict)

    def has_capabilities(self) -> bool:
        return bool(self.capabilities)

    def to_dict(self) -> dict:
        return {"capabilities": list(self.capabilities), "constraints": dict(self.constraints)}


@dataclass
class Attestation:
    witness: str
    att_type: str
    claims: dict = field(default_factory=dict)
    sig: Optional[str] = None
    ts: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "witness": self.witness,
            "type": self.att_type,
            "claims": dict(self.claims),
            "sig": self.sig or "cose:ES256:...",
            "ts": self.ts or _now(),
        }


@dataclass
class BirthCertificate:
    issuing_society: Optional[str] = None
    citizen_role: Optional[str] = None
    birth_timestamp: Optional[str] = None
    birth_witnesses: list = field(default_factory=list)
    genesis_block_hash: Optional[str] = None
    birth_context: Optional[str] = None
    stub: bool = False
    reason: Optional[str] = None

    def is_stub(self) -> bool:
        return self.stub

    def is_complete(self) -> bool:
        return (
            not self.stub
            and self.issuing_society is not None
            and self.citizen_role is not None
            and len(self.birth_witnesses) >= 3
        )

    def to_dict(self) -> dict:
        if self.stub:
            return {"stub": True, "reason": self.reason or "Self-issued entity"}
        return {
            "issuing_society": self.issuing_society,
            "citizen_role": self.citizen_role,
            "birth_timestamp": self.birth_timestamp or _now(),
            "birth_witnesses": list(self.birth_witnesses),
            "genesis_block_hash": self.genesis_block_hash,
            "birth_context": self.birth_context,
        }


@dataclass
class LineageEntry:
    parent: Optional[str]
    reason: str
    ts: Optional[str] = None

    def to_dict(self) -> dict:
        return {"parent": self.parent, "reason": self.reason, "ts": self.ts or _now()}


@dataclass
class Revocation:
    status: str = "active"
    ts: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {"status": self.status, "ts": self.ts, "reason": self.reason}


@dataclass
class HardwareAttestation:
    platform: Optional[str] = None
    key_storage: str = "software"
    boot_integrity: bool = False
    pcr_values: dict = field(default_factory=dict)
    last_attestation: Optional[str] = None
    stub: bool = False
    reason: Optional[str] = None

    def is_stub(self) -> bool:
        return self.stub

    def to_dict(self) -> dict:
        if self.stub:
            return {
                "platform": None,
                "key_storage": "software",
                "stub": True,
                "reason": self.reason or "Software-only binding",
            }
        return {
            "platform": self.platform,
            "key_storage": self.key_storage,
            "boot_integrity": self.boot_integrity,
            "pcr_values": dict(self.pcr_values),
            "last_attestation": self.last_attestation or _now(),
        }


# ══════════════════════════════════════════════════════════════
# LCTEntity — Core entity with capability level
# ══════════════════════════════════════════════════════════════

class LCTEntity:
    """A Web4 entity at a specific capability level."""

    def __init__(
        self,
        lct_id: str,
        entity_type: str,
        capability_level: int,
        binding: Optional[Binding] = None,
        mrh: Optional[MRH] = None,
        t3: Optional[Tensor] = None,
        v3: Optional[Tensor] = None,
        policy: Optional[Policy] = None,
        birth_certificate: Optional[BirthCertificate] = None,
        attestations: list = None,
        lineage: list = None,
        revocation: Optional[Revocation] = None,
        hardware_attestation: Optional[HardwareAttestation] = None,
    ):
        self.lct_id = lct_id
        self.entity_type = entity_type
        self.capability_level = CapLevel(capability_level)
        self.binding = binding
        self.mrh = mrh or MRH()
        self.t3 = t3 or Tensor.make_stub(T3_DIMENSIONS, f"Level {capability_level} entity")
        self.v3 = v3 or Tensor.make_stub(V3_DIMENSIONS, f"Level {capability_level} entity")
        self.policy = policy or Policy()
        self.birth_certificate = birth_certificate or BirthCertificate(stub=True, reason="Not issued")
        self.attestations = attestations or []
        self.lineage = lineage or []
        self.revocation = revocation
        self.hardware_attestation = hardware_attestation or HardwareAttestation(stub=True)
        self.subject = f"did:web4:key:{lct_id.split(':')[-1]}"

    def trust_tier(self) -> str:
        return TRUST_TIER_NAMES.get(self.capability_level, "unknown")

    def trust_range(self) -> tuple:
        return TRUST_TIERS.get(self.capability_level, (0.0, 0.0))

    def level_name(self) -> str:
        return LEVEL_NAMES.get(self.capability_level, "UNKNOWN")

    def to_dict(self) -> dict:
        d = {
            "lct_id": self.lct_id,
            "entity_type": self.entity_type,
            "capability_level": int(self.capability_level),
            "subject": self.subject,
        }
        if self.binding:
            d["binding"] = self.binding.to_dict()
        d["mrh"] = self.mrh.to_dict()
        d["t3_tensor"] = self.t3.to_dict()
        d["v3_tensor"] = self.v3.to_dict()
        d["policy"] = self.policy.to_dict()
        d["birth_certificate"] = self.birth_certificate.to_dict()
        if self.attestations:
            d["attestations"] = [a.to_dict() for a in self.attestations]
        if self.lineage:
            d["lineage"] = [l.to_dict() for l in self.lineage]
        if self.revocation:
            d["revocation"] = self.revocation.to_dict()
        if self.hardware_attestation and not self.hardware_attestation.is_stub():
            d["hardware_attestation"] = self.hardware_attestation.to_dict()
        return d


# ══════════════════════════════════════════════════════════════
# CapabilityValidator — §8 Validation Rules
# ══════════════════════════════════════════════════════════════

class ValidationResult:
    def __init__(self):
        self.valid = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.actual_level: Optional[int] = None

    def add_error(self, msg: str):
        self.valid = False
        self.errors.append(msg)

    def add_warning(self, msg: str):
        self.warnings.append(msg)


class CapabilityValidator:
    """Validates that an entity's claimed capability level matches its actual components."""

    def validate(self, entity: LCTEntity) -> ValidationResult:
        result = ValidationResult()

        # §8.1 — lct_id format: lct:web4:{entity_type}:{hash}
        self._validate_lct_id(entity, result)

        # Entity type known?
        if entity.entity_type not in ENTITY_LEVEL_RANGES and entity.entity_type != "pending":
            result.add_warning(f"Unknown entity type: {entity.entity_type}")

        # Entity-level compatibility (§3.3)
        if entity.entity_type in ENTITY_LEVEL_RANGES:
            lo, hi = ENTITY_LEVEL_RANGES[entity.entity_type]
            if not (lo <= entity.capability_level <= hi):
                result.add_warning(
                    f"Entity type '{entity.entity_type}' typical range is [{lo},{hi}], "
                    f"claimed level {entity.capability_level}"
                )

        # Per-level validation
        level = entity.capability_level
        if level >= CapLevel.STUB:
            self._validate_level_0(entity, result)
        if level >= CapLevel.MINIMAL:
            self._validate_level_1(entity, result)
        if level >= CapLevel.BASIC:
            self._validate_level_2(entity, result)
        if level >= CapLevel.STANDARD:
            self._validate_level_3(entity, result)
        if level >= CapLevel.FULL:
            self._validate_level_4(entity, result)
        if level >= CapLevel.HARDWARE:
            self._validate_level_5(entity, result)

        # Compute actual achievable level
        result.actual_level = self._compute_actual_level(entity)

        return result

    def _validate_lct_id(self, entity: LCTEntity, result: ValidationResult):
        parts = entity.lct_id.split(":")
        if len(parts) < 4 or parts[0] != "lct" or parts[1] != "web4":
            result.add_error(f"Invalid lct_id format: {entity.lct_id} (expected lct:web4:{{type}}:{{hash}})")

    def _validate_level_0(self, entity: LCTEntity, result: ValidationResult):
        if not entity.entity_type:
            result.add_error("Level 0: entity_type required")

    def _validate_level_1(self, entity: LCTEntity, result: ValidationResult):
        # Binding with public key
        if not entity.binding or not entity.binding.public_key:
            result.add_error("Level 1: binding with public_key required")
        if not entity.binding or not entity.binding.binding_proof:
            result.add_error("Level 1: binding_proof required (self-signed)")
        # MRH present (empty is OK)
        # T3: all 6 dims with initial values
        if entity.t3.is_stub():
            result.add_error("Level 1: T3 tensor must not be stub")
        elif entity.t3.non_null_count() < 6:
            result.add_error(f"Level 1: T3 needs all 6 dimensions, has {entity.t3.non_null_count()}")
        # V3: all 6 dims (zero OK)
        if entity.v3.is_stub():
            result.add_error("Level 1: V3 tensor must not be stub")
        elif entity.v3.non_null_count() < 6:
            result.add_error(f"Level 1: V3 needs all 6 dimensions, has {entity.v3.non_null_count()}")

    def _validate_level_2(self, entity: LCTEntity, result: ValidationResult):
        # At least one MRH relationship (bound OR paired)
        if not entity.mrh.has_relationships():
            result.add_error("Level 2: at least one MRH relationship (bound or paired) required")
        # T3: all 6 with non-zero
        if not entity.t3.is_stub() and entity.t3.non_zero_count() < 6:
            result.add_error(f"Level 2: T3 needs all 6 non-zero, has {entity.t3.non_zero_count()}")
        # Policy: at least one capability
        if not entity.policy.has_capabilities():
            result.add_error("Level 2: at least one policy capability required")

    def _validate_level_3(self, entity: LCTEntity, result: ValidationResult):
        # MRH witnessing
        if not entity.mrh.has_witnessing():
            result.add_error("Level 3: at least one witnessing relationship required")
        # T3 computation witnesses
        if not entity.t3.is_stub() and not entity.t3.computation_witnesses:
            result.add_error("Level 3: T3 computation_witnesses required (oracle)")
        # V3 energy_balance non-zero
        if not entity.v3.is_stub():
            eb = entity.v3.dimensions.get("energy_balance", 0)
            if eb is None or eb == 0:
                result.add_error("Level 3: V3 energy_balance must be non-zero (ATP)")
        # Attestations
        if not entity.attestations:
            result.add_error("Level 3: at least one attestation required")

    def _validate_level_4(self, entity: LCTEntity, result: ValidationResult):
        # Birth certificate complete
        if entity.birth_certificate.is_stub():
            result.add_error("Level 4: complete birth_certificate required (not stub)")
        elif not entity.birth_certificate.is_complete():
            result.add_error("Level 4: birth_certificate incomplete (need society, role, ≥3 witnesses)")
        # Permanent citizen role in paired
        has_citizen = any(
            getattr(r, "pairing_type", None) == "birth_certificate" and getattr(r, "permanent", False)
            for r in entity.mrh.paired
        )
        if not has_citizen:
            result.add_error("Level 4: permanent citizen role pairing required in MRH")
        # Lineage
        if not entity.lineage:
            result.add_error("Level 4: at least one lineage entry required")
        # Revocation tracking
        if not entity.revocation:
            result.add_error("Level 4: revocation status tracking required")

    def _validate_level_5(self, entity: LCTEntity, result: ValidationResult):
        # Hardware binding
        if not entity.binding or not entity.binding.is_hardware_bound():
            result.add_error("Level 5: hardware_anchor and hardware_type required in binding")
        valid_hw = {"tpm2", "trustzone", "secure_element"}
        if entity.binding and entity.binding.hardware_type and entity.binding.hardware_type not in valid_hw:
            result.add_error(f"Level 5: hardware_type must be one of {valid_hw}")
        # Hardware attestation
        if entity.hardware_attestation and entity.hardware_attestation.is_stub():
            result.add_error("Level 5: hardware_attestation must not be stub")

    def _compute_actual_level(self, entity: LCTEntity) -> int:
        """Compute the highest level the entity actually qualifies for."""
        for level in range(5, -1, -1):
            test = ValidationResult()
            # Re-validate at each level
            self._validate_level_0(entity, test)
            if level >= 1:
                self._validate_level_1(entity, test)
            if level >= 2:
                self._validate_level_2(entity, test)
            if level >= 3:
                self._validate_level_3(entity, test)
            if level >= 4:
                self._validate_level_4(entity, test)
            if level >= 5:
                self._validate_level_5(entity, test)
            if test.valid:
                return level
        return 0


# ══════════════════════════════════════════════════════════════
# §4 — Capability Query Protocol
# ══════════════════════════════════════════════════════════════

RELATIONSHIP_SUPPORT = {
    "human": {
        "can_be_bound_by": ["organization", "society"],
        "can_pair_with": ["ai", "role", "device", "service"],
        "can_witness": ["ai", "human", "task", "device"],
        "can_be_witnessed_by": ["oracle", "human", "ai", "witness"],
    },
    "ai": {
        "can_be_bound_by": ["device", "organization"],
        "can_pair_with": ["plugin", "service", "ai", "human", "role"],
        "can_witness": ["plugin", "task", "session", "ai"],
        "can_be_witnessed_by": ["oracle", "human", "ai", "witness"],
    },
    "device": {
        "can_be_bound_by": ["organization", "infrastructure"],
        "can_pair_with": ["service", "ai", "device"],
        "can_witness": ["device", "resource"],
        "can_be_witnessed_by": ["oracle", "device", "human"],
    },
    "plugin": {
        "can_be_bound_by": ["ai", "service"],
        "can_pair_with": ["plugin", "ai", "service"],
        "can_witness": [],
        "can_be_witnessed_by": ["ai", "oracle"],
    },
    "service": {
        "can_be_bound_by": ["organization", "device"],
        "can_pair_with": ["ai", "plugin", "service", "human"],
        "can_witness": ["task", "session"],
        "can_be_witnessed_by": ["oracle", "ai", "human"],
    },
    "oracle": {
        "can_be_bound_by": ["society", "organization"],
        "can_pair_with": ["service", "ai"],
        "can_witness": ["human", "ai", "device", "service", "task", "plugin"],
        "can_be_witnessed_by": ["oracle", "society"],
    },
    "society": {
        "can_be_bound_by": ["society"],
        "can_pair_with": ["human", "ai", "organization", "oracle", "device"],
        "can_witness": ["human", "ai", "organization", "role", "oracle"],
        "can_be_witnessed_by": ["oracle", "society", "witness"],
    },
    "organization": {
        "can_be_bound_by": ["society"],
        "can_pair_with": ["human", "ai", "role", "service", "device"],
        "can_witness": ["human", "ai", "task", "service"],
        "can_be_witnessed_by": ["oracle", "society", "witness"],
    },
    "role": {
        "can_be_bound_by": ["organization", "society"],
        "can_pair_with": ["human", "ai"],
        "can_witness": [],
        "can_be_witnessed_by": ["oracle", "human", "ai", "witness"],
    },
    "accumulator": {
        "can_be_bound_by": ["organization", "society"],
        "can_pair_with": [],
        "can_witness": [],
        "can_be_witnessed_by": ["oracle", "device"],
    },
    "dictionary": {
        "can_be_bound_by": ["organization", "society"],
        "can_pair_with": ["ai", "service", "dictionary"],
        "can_witness": [],
        "can_be_witnessed_by": ["oracle", "human", "ai"],
    },
}


@dataclass
class CapabilityQuery:
    """§4.2 — Capability discovery request."""
    target_lct: str
    requester_lct: str
    requested_info: list = field(default_factory=lambda: [
        "capability_level", "entity_type", "supported_components",
        "relationship_types", "trust_tier",
    ])
    timestamp: Optional[str] = None
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "query_type": "capability_discovery",
            "target_lct": self.target_lct,
            "requester_lct": self.requester_lct,
            "requested_info": list(self.requested_info),
            "timestamp": self.timestamp or _now(),
            "signature": self.signature or "cose:ES256:...",
        }


@dataclass
class CapabilityResponse:
    """§4.3 — Capability discovery response."""
    source_lct: str
    capability_level: int
    entity_type: str
    supported_components: dict
    relationship_support: dict
    trust_tier: str
    composite_t3: float
    composite_v3: float
    timestamp: Optional[str] = None
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "response_type": "capability_discovery",
            "source_lct": self.source_lct,
            "capability_level": self.capability_level,
            "entity_type": self.entity_type,
            "supported_components": self.supported_components,
            "relationship_support": self.relationship_support,
            "trust_tier": self.trust_tier,
            "composite_t3": self.composite_t3,
            "composite_v3": self.composite_v3,
            "timestamp": self.timestamp or _now(),
            "signature": self.signature or "cose:ES256:...",
        }


def handle_capability_query(entity: LCTEntity, query: CapabilityQuery) -> CapabilityResponse:
    """Entity responds to a capability discovery query."""
    # Build supported_components
    components = {
        "binding": {
            "implemented": entity.binding is not None,
            "hardware_anchored": entity.binding.is_hardware_bound() if entity.binding else False,
            "key_algorithm": "Ed25519" if entity.binding and entity.binding.public_key else None,
        },
        "mrh": {
            "implemented": True,
            "relationship_types": ["bound", "paired", "witnessing"],
            "horizon_depth": entity.mrh.horizon_depth,
        },
        "t3_tensor": {
            "implemented": not entity.t3.is_stub(),
            "dimensions": 6 if not entity.t3.is_stub() else 0,
            "oracle_computed": bool(entity.t3.computation_witnesses),
        },
        "v3_tensor": {
            "implemented": not entity.v3.is_stub(),
            "dimensions": 6 if not entity.v3.is_stub() else 0,
            "oracle_computed": bool(entity.v3.computation_witnesses),
        },
        "birth_certificate": {
            "implemented": not entity.birth_certificate.is_stub(),
            "stub": entity.birth_certificate.is_stub(),
        },
        "attestations": {
            "implemented": bool(entity.attestations),
            "count": len(entity.attestations),
        },
        "lineage": {
            "implemented": bool(entity.lineage),
            "stub": not bool(entity.lineage),
        },
    }

    rel_support = RELATIONSHIP_SUPPORT.get(entity.entity_type, {
        "can_be_bound_by": [],
        "can_pair_with": [],
        "can_witness": [],
        "can_be_witnessed_by": [],
    })

    t3_score = entity.t3.composite_score if entity.t3.composite_score is not None else 0.0
    v3_score = entity.v3.composite_score if entity.v3.composite_score is not None else 0.0

    return CapabilityResponse(
        source_lct=entity.lct_id,
        capability_level=int(entity.capability_level),
        entity_type=entity.entity_type,
        supported_components=components,
        relationship_support=rel_support,
        trust_tier=entity.trust_tier(),
        composite_t3=t3_score,
        composite_v3=v3_score,
    )


# ══════════════════════════════════════════════════════════════
# §6 — Level Upgrade Path
# ══════════════════════════════════════════════════════════════

class UpgradeResult:
    def __init__(self, success: bool, new_level: Optional[int] = None, reason: str = ""):
        self.success = success
        self.new_level = new_level
        self.reason = reason


class LevelUpgrader:
    """Manages level upgrades with constraint enforcement (§6.2)."""

    def __init__(self):
        self.validator = CapabilityValidator()

    def can_upgrade(self, entity: LCTEntity, target_level: int) -> UpgradeResult:
        """Check if entity can upgrade to target level."""
        current = entity.capability_level

        # No downgrades (§6.2)
        if target_level <= current:
            return UpgradeResult(False, reason=f"Cannot downgrade from {current} to {target_level}")

        # Must be sequential
        if target_level > current + 1:
            return UpgradeResult(False, reason=f"Must upgrade one level at a time ({current} → {current + 1})")

        # Level 5 requires hardware from creation (§6.2)
        if target_level == CapLevel.HARDWARE:
            if not entity.binding or not entity.binding.is_hardware_bound():
                return UpgradeResult(
                    False,
                    reason="Level 5 (HARDWARE) requires hardware binding from creation — cannot add post-hoc",
                )

        # Level 4 requires society issuance (§6.2)
        if target_level == CapLevel.FULL:
            if entity.birth_certificate.is_stub():
                return UpgradeResult(
                    False,
                    reason="Level 4 (FULL) requires society-issued birth certificate",
                )

        # Validate all requirements for target level
        old_level = entity.capability_level
        entity.capability_level = CapLevel(target_level)
        result = self.validator.validate(entity)
        entity.capability_level = CapLevel(old_level)

        if not result.valid:
            return UpgradeResult(
                False,
                reason=f"Missing requirements for level {target_level}: {'; '.join(result.errors)}",
            )

        return UpgradeResult(True, new_level=target_level)

    def upgrade(self, entity: LCTEntity, target_level: int) -> UpgradeResult:
        """Execute upgrade if allowed."""
        check = self.can_upgrade(entity, target_level)
        if check.success:
            entity.capability_level = CapLevel(target_level)
            check.new_level = target_level
        return check


# ══════════════════════════════════════════════════════════════
# §7 — Cross-Domain Communication
# ══════════════════════════════════════════════════════════════

@dataclass
class NegotiationResult:
    compatible: bool
    common_level: int
    reason: str = ""
    adaptation_needed: bool = False

    def to_dict(self) -> dict:
        return {
            "compatible": self.compatible,
            "common_level": self.common_level,
            "reason": self.reason,
            "adaptation_needed": self.adaptation_needed,
        }


class CrossDomainNegotiator:
    """§7.1 — Common Ground Protocol for cross-domain LCT interaction."""

    def negotiate(self, entity_a: LCTEntity, entity_b: LCTEntity) -> NegotiationResult:
        """Negotiate common ground between two entities."""
        # Step 1: capability discovery (simulated)
        resp_a = handle_capability_query(entity_a, CapabilityQuery(
            target_lct=entity_a.lct_id, requester_lct=entity_b.lct_id))
        resp_b = handle_capability_query(entity_b, CapabilityQuery(
            target_lct=entity_b.lct_id, requester_lct=entity_a.lct_id))

        # Step 2: common level = min
        common = min(resp_a.capability_level, resp_b.capability_level)

        # Step 3: check compatibility
        rel_a = resp_a.relationship_support
        rel_b = resp_b.relationship_support
        can_pair = (
            entity_b.entity_type in rel_a.get("can_pair_with", [])
            or entity_a.entity_type in rel_b.get("can_pair_with", [])
        )

        if not can_pair:
            return NegotiationResult(
                compatible=False,
                common_level=common,
                reason=(
                    f"{entity_a.entity_type} cannot pair with {entity_b.entity_type} "
                    f"(and vice versa)"
                ),
            )

        adaptation = resp_a.capability_level != resp_b.capability_level

        return NegotiationResult(
            compatible=True,
            common_level=common,
            reason=f"Common ground at level {common} ({LEVEL_NAMES[CapLevel(common)]})",
            adaptation_needed=adaptation,
        )


# ══════════════════════════════════════════════════════════════
# §9 — Security Considerations
# ══════════════════════════════════════════════════════════════

class SecurityCheckResult:
    def __init__(self):
        self.issues: list[str] = []
        self.severity: str = "none"

    def add_issue(self, msg: str, severity: str = "warning"):
        self.issues.append(msg)
        if severity == "critical" or self.severity == "critical":
            self.severity = "critical"
        elif severity == "warning" and self.severity != "critical":
            self.severity = "warning"

    @property
    def clean(self) -> bool:
        return len(self.issues) == 0


class SecurityChecker:
    """§9 — Detect misrepresentation, stub exploitation, upgrade attacks."""

    def __init__(self):
        self.validator = CapabilityValidator()

    def check_misrepresentation(self, entity: LCTEntity) -> SecurityCheckResult:
        """§9.1 — Detect if entity claims higher level than components support."""
        result = SecurityCheckResult()
        validation = self.validator.validate(entity)

        if validation.actual_level is not None and validation.actual_level < entity.capability_level:
            result.add_issue(
                f"MISREPRESENTATION: Claims level {entity.capability_level} "
                f"but only qualifies for level {validation.actual_level}",
                "critical",
            )
        return result

    def check_stub_exploitation(self, entity: LCTEntity) -> SecurityCheckResult:
        """§9.2 — Detect attempts to use stubbed components as if real."""
        result = SecurityCheckResult()

        if entity.capability_level >= CapLevel.MINIMAL and entity.t3.is_stub():
            result.add_issue("Stub exploitation: using stub T3 at level ≥1", "critical")
        if entity.capability_level >= CapLevel.MINIMAL and entity.v3.is_stub():
            result.add_issue("Stub exploitation: using stub V3 at level ≥1", "critical")
        if entity.capability_level >= CapLevel.FULL and entity.birth_certificate.is_stub():
            result.add_issue("Stub exploitation: using stub birth_certificate at level ≥4", "critical")
        if entity.capability_level >= CapLevel.HARDWARE and entity.hardware_attestation.is_stub():
            result.add_issue("Stub exploitation: using stub hardware_attestation at level 5", "critical")

        return result

    def check_upgrade_attack(self, entity: LCTEntity, target_level: int) -> SecurityCheckResult:
        """§9.3 — Detect unauthorized upgrade attempts."""
        result = SecurityCheckResult()

        # Level 5 post-hoc binding
        if target_level >= CapLevel.HARDWARE:
            if not entity.binding or not entity.binding.is_hardware_bound():
                result.add_issue(
                    "Upgrade attack: Level 5 requires hardware binding from creation",
                    "critical",
                )

        # Level 4 without society
        if target_level >= CapLevel.FULL:
            if entity.birth_certificate.is_stub():
                result.add_issue(
                    "Upgrade attack: Level 4 requires society-issued birth certificate",
                    "critical",
                )

        # Level 3 without witnesses
        if target_level >= CapLevel.STANDARD:
            if not entity.attestations:
                result.add_issue(
                    "Upgrade attack: Level 3 requires witness attestation",
                    "warning",
                )

        # Level 2 without mutual relationship
        if target_level >= CapLevel.BASIC:
            if not entity.mrh.has_relationships():
                result.add_issue(
                    "Upgrade attack: Level 2 requires mutual MRH relationship",
                    "warning",
                )

        return result


# ══════════════════════════════════════════════════════════════
# Entity Factory — Build entities at specific levels
# ══════════════════════════════════════════════════════════════

class EntityFactory:
    """Convenience factory for building valid entities at each level."""

    @staticmethod
    def make_stub(entity_type: str = "pending", suffix: str = "placeholder") -> LCTEntity:
        return LCTEntity(
            lct_id=f"lct:web4:{entity_type}:{suffix}",
            entity_type=entity_type,
            capability_level=0,
        )

    @staticmethod
    def make_minimal(entity_type: str, suffix: str) -> LCTEntity:
        t3 = Tensor.make_initial(T3_DIMENSIONS, 0.1)
        v3 = Tensor.make_initial(V3_DIMENSIONS, 0.0)
        return LCTEntity(
            lct_id=f"lct:web4:{entity_type}:{suffix}",
            entity_type=entity_type,
            capability_level=1,
            binding=Binding(
                entity_type=entity_type,
                public_key=f"mb64:ed25519:{suffix}",
                binding_proof=f"cose:ES256:{suffix}",
                created_at=_now(),
            ),
            t3=t3,
            v3=v3,
            policy=Policy(),
            birth_certificate=BirthCertificate(stub=True, reason="Self-issued entity"),
        )

    @staticmethod
    def make_basic(entity_type: str, suffix: str, parent_lct: str) -> LCTEntity:
        t3 = Tensor.make_initial(T3_DIMENSIONS, 0.3)
        v3 = Tensor.make_initial(V3_DIMENSIONS, 0.1)
        mrh = MRH(
            bound=[MRHRelationship(lct_id=parent_lct, rel_type="parent", binding_context="deployment", ts=_now())],
            horizon_depth=2,
            last_updated=_now(),
        )
        return LCTEntity(
            lct_id=f"lct:web4:{entity_type}:{suffix}",
            entity_type=entity_type,
            capability_level=2,
            binding=Binding(
                entity_type=entity_type,
                public_key=f"mb64:ed25519:{suffix}",
                binding_proof=f"cose:ES256:{suffix}",
                created_at=_now(),
            ),
            mrh=mrh,
            t3=t3,
            v3=v3,
            policy=Policy(capabilities=["execute:irp", "read:patterns"]),
            birth_certificate=BirthCertificate(stub=True, reason="Self-issued entity"),
        )

    @staticmethod
    def make_standard(entity_type: str, suffix: str, parent_lct: str) -> LCTEntity:
        t3 = Tensor(
            dimensions={
                "technical_competence": 0.7,
                "social_reliability": 0.6,
                "temporal_consistency": 0.65,
                "witness_count": 0.5,
                "lineage_depth": 0.4,
                "context_alignment": 0.7,
            },
            computation_witnesses=["lct:web4:oracle:trust:federation"],
            last_computed=_now(),
        )
        t3.compute_composite()
        v3 = Tensor(
            dimensions={
                "energy_balance": 100,
                "contribution_history": 0.5,
                "resource_stewardship": 0.6,
                "network_effects": 0.4,
                "reputation_capital": 0.5,
                "temporal_value": 0.55,
            },
            computation_witnesses=["lct:web4:oracle:value:federation"],
            last_computed=_now(),
        )
        v3.compute_composite()
        mrh = MRH(
            bound=[MRHRelationship(lct_id=parent_lct, rel_type="parent", ts=_now())],
            paired=[MRHRelationship(lct_id="lct:web4:role:operator:1", pairing_type="assigned", ts=_now())],
            witnessing=[MRHRelationship(
                lct_id="lct:web4:oracle:time:global",
                role="time",
                last_attestation=_now(),
                witness_count=10,
            )],
            horizon_depth=3,
            last_updated=_now(),
        )
        return LCTEntity(
            lct_id=f"lct:web4:{entity_type}:{suffix}",
            entity_type=entity_type,
            capability_level=3,
            binding=Binding(
                entity_type=entity_type,
                public_key=f"mb64:ed25519:{suffix}",
                binding_proof=f"cose:ES256:{suffix}",
                created_at=_now(),
            ),
            mrh=mrh,
            t3=t3,
            v3=v3,
            policy=Policy(capabilities=["execute:irp", "read:patterns", "compute:trust"]),
            attestations=[Attestation(
                witness="did:web4:key:oracle123",
                att_type="existence",
                claims={"observed_at": _now()},
            )],
            birth_certificate=BirthCertificate(stub=True, reason="Self-issued entity"),
        )

    @staticmethod
    def make_full(entity_type: str, suffix: str, society_lct: str) -> LCTEntity:
        t3 = Tensor(
            dimensions={
                "technical_competence": 0.8,
                "social_reliability": 0.75,
                "temporal_consistency": 0.8,
                "witness_count": 0.7,
                "lineage_depth": 0.6,
                "context_alignment": 0.85,
            },
            computation_witnesses=["lct:web4:oracle:trust:federation"],
            last_computed=_now(),
        )
        t3.compute_composite()
        v3 = Tensor(
            dimensions={
                "energy_balance": 500,
                "contribution_history": 0.7,
                "resource_stewardship": 0.8,
                "network_effects": 0.6,
                "reputation_capital": 0.75,
                "temporal_value": 0.7,
            },
            computation_witnesses=["lct:web4:oracle:value:federation"],
            last_computed=_now(),
        )
        v3.compute_composite()
        citizen_role_lct = f"lct:web4:role:citizen:{suffix}"
        mrh = MRH(
            bound=[MRHRelationship(lct_id=society_lct, rel_type="society", ts=_now())],
            paired=[MRHRelationship(
                lct_id=citizen_role_lct,
                pairing_type="birth_certificate",
                permanent=True,
                ts=_now(),
            )],
            witnessing=[MRHRelationship(
                lct_id="lct:web4:oracle:time:global",
                role="time",
                last_attestation=_now(),
                witness_count=50,
            )],
            horizon_depth=4,
            last_updated=_now(),
        )
        bc = BirthCertificate(
            issuing_society=society_lct,
            citizen_role=citizen_role_lct,
            birth_timestamp=_now(),
            birth_witnesses=[
                "lct:web4:witness:w1",
                "lct:web4:witness:w2",
                "lct:web4:witness:w3",
            ],
            genesis_block_hash="0xabc123",
            birth_context="federation",
        )
        return LCTEntity(
            lct_id=f"lct:web4:{entity_type}:{suffix}",
            entity_type=entity_type,
            capability_level=4,
            binding=Binding(
                entity_type=entity_type,
                public_key=f"mb64:ed25519:{suffix}",
                binding_proof=f"cose:ES256:{suffix}",
                created_at=_now(),
            ),
            mrh=mrh,
            t3=t3,
            v3=v3,
            policy=Policy(capabilities=["execute:irp", "read:patterns", "compute:trust", "issue:certs"]),
            birth_certificate=bc,
            attestations=[
                Attestation(witness="did:web4:key:oracle1", att_type="existence", claims={"observed_at": _now()}),
                Attestation(witness="did:web4:key:oracle2", att_type="trust_computation", claims={"t3": 0.75}),
            ],
            lineage=[LineageEntry(parent=None, reason="genesis", ts=_now())],
            revocation=Revocation(status="active"),
        )

    @staticmethod
    def make_hardware(entity_type: str, suffix: str, society_lct: str) -> LCTEntity:
        entity = EntityFactory.make_full(entity_type, suffix, society_lct)
        entity.capability_level = CapLevel.HARDWARE
        entity.binding.hardware_anchor = f"eat:mb64:hw:{suffix}"
        entity.binding.hardware_type = "tpm2"
        entity.binding.attestation_chain = [
            "eat:manufacturer:intel",
            "eat:platform:legion",
            "eat:application:web4",
        ]
        entity.hardware_attestation = HardwareAttestation(
            platform="linux-tpm2",
            key_storage="tpm",
            boot_integrity=True,
            pcr_values={"0": "abcd1234", "7": "ef567890"},
            last_attestation=_now(),
        )
        return entity


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def _now() -> str:
    return "2026-02-21T12:00:00Z"


def _hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:16]


# ══════════════════════════════════════════════════════════════
# Self-Tests
# ══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}")
            failed += 1

    validator = CapabilityValidator()
    upgrader = LevelUpgrader()
    negotiator = CrossDomainNegotiator()
    security = SecurityChecker()

    # ── T1: Level 0 (STUB) ──────────────────────────────────
    print("\n═══ T1: Level 0 — STUB Entity ═══")
    stub = EntityFactory.make_stub()
    check("T1: stub entity created", stub is not None)
    check("T1: level is 0", stub.capability_level == CapLevel.STUB)
    check("T1: entity type is pending", stub.entity_type == "pending")
    check("T1: trust tier is untrusted", stub.trust_tier() == "untrusted")
    check("T1: level name is STUB", stub.level_name() == "STUB")
    check("T1: T3 is stub", stub.t3.is_stub())
    check("T1: V3 is stub", stub.v3.is_stub())
    check("T1: birth cert is stub", stub.birth_certificate.is_stub())
    r = validator.validate(stub)
    check("T1: validates at level 0", r.valid)

    # ── T2: Level 1 (MINIMAL) ───────────────────────────────
    print("\n═══ T2: Level 1 — MINIMAL Entity ═══")
    minimal = EntityFactory.make_minimal("plugin", "vision-irp-1")
    check("T2: minimal entity created", minimal is not None)
    check("T2: level is 1", minimal.capability_level == CapLevel.MINIMAL)
    check("T2: has binding", minimal.binding is not None)
    check("T2: has public key", minimal.binding.public_key is not None)
    check("T2: has binding proof", minimal.binding.binding_proof is not None)
    check("T2: T3 not stub", not minimal.t3.is_stub())
    check("T2: T3 has 6 dims", minimal.t3.non_null_count() == 6)
    check("T2: V3 not stub", not minimal.v3.is_stub())
    check("T2: V3 has 6 dims", minimal.v3.non_null_count() == 6)
    check("T2: trust tier is low", minimal.trust_tier() == "low")
    r = validator.validate(minimal)
    check("T2: validates at level 1", r.valid)

    # ── T3: Level 2 (BASIC) ─────────────────────────────────
    print("\n═══ T3: Level 2 — BASIC Entity ═══")
    basic = EntityFactory.make_basic("plugin", "audio-irp-1", "lct:web4:ai:orchestrator")
    check("T3: basic entity created", basic is not None)
    check("T3: level is 2", basic.capability_level == CapLevel.BASIC)
    check("T3: has MRH relationship", basic.mrh.has_relationships())
    check("T3: has bound entry", len(basic.mrh.bound) > 0)
    check("T3: T3 non-zero count >= 6", basic.t3.non_zero_count() >= 6)
    check("T3: has policy capabilities", basic.policy.has_capabilities())
    check("T3: trust tier is basic", basic.trust_tier() == "basic")
    r = validator.validate(basic)
    check("T3: validates at level 2", r.valid)

    # ── T4: Level 3 (STANDARD) ──────────────────────────────
    print("\n═══ T4: Level 3 — STANDARD Entity ═══")
    standard = EntityFactory.make_standard("ai", "sage-1", "lct:web4:device:legion")
    check("T4: standard entity created", standard is not None)
    check("T4: level is 3", standard.capability_level == CapLevel.STANDARD)
    check("T4: has witnessing", standard.mrh.has_witnessing())
    check("T4: T3 has computation witnesses", len(standard.t3.computation_witnesses) > 0)
    eb = standard.v3.dimensions.get("energy_balance", 0)
    check("T4: V3 energy_balance non-zero", eb is not None and eb > 0)
    check("T4: has attestations", len(standard.attestations) > 0)
    check("T4: trust tier is medium", standard.trust_tier() == "medium")
    check("T4: composite T3 computed", standard.t3.composite_score is not None)
    r = validator.validate(standard)
    check("T4: validates at level 3", r.valid)

    # ── T5: Level 4 (FULL) ──────────────────────────────────
    print("\n═══ T5: Level 4 — FULL Entity ═══")
    full = EntityFactory.make_full("human", "alice-1", "lct:web4:society:web4-foundation")
    check("T5: full entity created", full is not None)
    check("T5: level is 4", full.capability_level == CapLevel.FULL)
    check("T5: birth cert not stub", not full.birth_certificate.is_stub())
    check("T5: birth cert complete", full.birth_certificate.is_complete())
    check("T5: has 3 birth witnesses", len(full.birth_certificate.birth_witnesses) >= 3)
    has_citizen = any(
        getattr(r, "pairing_type", None) == "birth_certificate" and getattr(r, "permanent", False)
        for r in full.mrh.paired
    )
    check("T5: has permanent citizen pairing", has_citizen)
    check("T5: has lineage", len(full.lineage) > 0)
    check("T5: has revocation tracking", full.revocation is not None)
    check("T5: trust tier is high", full.trust_tier() == "high")
    r = validator.validate(full)
    check("T5: validates at level 4", r.valid)

    # ── T6: Level 5 (HARDWARE) ──────────────────────────────
    print("\n═══ T6: Level 5 — HARDWARE Entity ═══")
    hw = EntityFactory.make_hardware("device", "legion-tpm2", "lct:web4:society:web4-foundation")
    check("T6: hardware entity created", hw is not None)
    check("T6: level is 5", hw.capability_level == CapLevel.HARDWARE)
    check("T6: binding has hardware_anchor", hw.binding.hardware_anchor is not None)
    check("T6: hardware_type is tpm2", hw.binding.hardware_type == "tpm2")
    check("T6: has attestation chain", len(hw.binding.attestation_chain) > 0)
    check("T6: hardware_attestation not stub", not hw.hardware_attestation.is_stub())
    check("T6: hw platform is linux-tpm2", hw.hardware_attestation.platform == "linux-tpm2")
    check("T6: hw key_storage is tpm", hw.hardware_attestation.key_storage == "tpm")
    check("T6: has pcr values", len(hw.hardware_attestation.pcr_values) > 0)
    check("T6: trust tier is maximum", hw.trust_tier() == "maximum")
    r = validator.validate(hw)
    check("T6: validates at level 5", r.valid)

    # ── T7: Validation — Invalid Entities ────────────────────
    print("\n═══ T7: Validation — Invalid Entities ═══")
    # Level 1 without binding
    bad1 = LCTEntity(
        lct_id="lct:web4:plugin:bad1",
        entity_type="plugin",
        capability_level=1,
        # No binding
    )
    r1 = validator.validate(bad1)
    check("T7: level 1 without binding invalid", not r1.valid)
    check("T7: has binding error", any("binding" in e.lower() or "public_key" in e.lower() for e in r1.errors))

    # Level 2 without relationships
    bad2 = EntityFactory.make_minimal("plugin", "bad2")
    bad2.capability_level = CapLevel.BASIC
    r2 = validator.validate(bad2)
    check("T7: level 2 without relationships invalid", not r2.valid)

    # Level 3 without attestations
    bad3 = EntityFactory.make_basic("ai", "bad3", "lct:web4:device:d1")
    bad3.capability_level = CapLevel.STANDARD
    r3 = validator.validate(bad3)
    check("T7: level 3 without attestations invalid", not r3.valid)

    # Level 4 without birth cert
    bad4 = EntityFactory.make_standard("human", "bad4", "lct:web4:device:d1")
    bad4.capability_level = CapLevel.FULL
    r4 = validator.validate(bad4)
    check("T7: level 4 without birth cert invalid", not r4.valid)

    # Level 5 without hardware
    bad5 = EntityFactory.make_full("device", "bad5", "lct:web4:society:s1")
    bad5.capability_level = CapLevel.HARDWARE
    r5 = validator.validate(bad5)
    check("T7: level 5 without hardware invalid", not r5.valid)

    # ── T8: Actual Level Computation ─────────────────────────
    print("\n═══ T8: Actual Level Computation ═══")
    # Standard entity claiming level 3 should compute as 3
    r_std = validator.validate(standard)
    check("T8: standard actual level = 3", r_std.actual_level == 3)

    # Over-claiming: minimal entity claiming level 3
    overclaim = EntityFactory.make_minimal("ai", "overclaim")
    overclaim.capability_level = CapLevel.STANDARD
    r_oc = validator.validate(overclaim)
    check("T8: overclaim detected — invalid", not r_oc.valid)
    check("T8: actual level < claimed", r_oc.actual_level < 3)

    # Full entity should compute as 4
    r_full = validator.validate(full)
    check("T8: full actual level = 4", r_full.actual_level == 4)

    # Hardware entity should compute as 5
    r_hw = validator.validate(hw)
    check("T8: hardware actual level = 5", r_hw.actual_level == 5)

    # ── T9: Entity-Level Range Warnings ──────────────────────
    print("\n═══ T9: Entity-Level Range Warnings ═══")
    # Human at level 1 should warn (typical range 4-5)
    low_human = EntityFactory.make_minimal("human", "low-human")
    r_lh = validator.validate(low_human)
    check("T9: human at level 1 warns", len(r_lh.warnings) > 0)
    check("T9: warning mentions range", any("range" in w.lower() or "typical" in w.lower() for w in r_lh.warnings))

    # Plugin at level 1 should not warn (typical range 1-2)
    plugin_ok = EntityFactory.make_minimal("plugin", "ok-plugin")
    r_po = validator.validate(plugin_ok)
    range_warnings = [w for w in r_po.warnings if "range" in w.lower() or "typical" in w.lower()]
    check("T9: plugin at level 1 no range warning", len(range_warnings) == 0)

    # ── T10: Capability Query Protocol ───────────────────────
    print("\n═══ T10: Capability Query Protocol ═══")
    query = CapabilityQuery(
        target_lct=standard.lct_id,
        requester_lct=minimal.lct_id,
    )
    qd = query.to_dict()
    check("T10: query has type", qd["query_type"] == "capability_discovery")
    check("T10: query has target", qd["target_lct"] == standard.lct_id)
    check("T10: query has requester", qd["requester_lct"] == minimal.lct_id)
    check("T10: query has timestamp", "timestamp" in qd)
    check("T10: query has signature", "signature" in qd)

    resp = handle_capability_query(standard, query)
    rd = resp.to_dict()
    check("T10: response has source_lct", rd["source_lct"] == standard.lct_id)
    check("T10: response level = 3", rd["capability_level"] == 3)
    check("T10: response entity_type = ai", rd["entity_type"] == "ai")
    check("T10: response has components", "supported_components" in rd)
    check("T10: response has relationship_support", "relationship_support" in rd)
    check("T10: response trust_tier = medium", rd["trust_tier"] == "medium")
    check("T10: response has composite_t3", "composite_t3" in rd)
    check("T10: response has composite_v3", "composite_v3" in rd)
    check("T10: T3 implemented", rd["supported_components"]["t3_tensor"]["implemented"])
    check("T10: birth cert stub", rd["supported_components"]["birth_certificate"]["stub"])

    # ── T11: Cross-Domain Negotiation ────────────────────────
    print("\n═══ T11: Cross-Domain Negotiation ═══")
    # AI (level 3) + plugin (level 1) — compatible
    n1 = negotiator.negotiate(standard, minimal)
    check("T11: AI-plugin compatible", n1.compatible)
    check("T11: common level = 1", n1.common_level == 1)
    check("T11: adaptation needed", n1.adaptation_needed)

    # Two AIs — compatible
    ai2 = EntityFactory.make_standard("ai", "sage-2", "lct:web4:device:thor")
    n2 = negotiator.negotiate(standard, ai2)
    check("T11: AI-AI compatible", n2.compatible)
    check("T11: AI-AI common level = 3", n2.common_level == 3)
    check("T11: AI-AI no adaptation", not n2.adaptation_needed)

    # Human (level 4) + device (level 5) — compatible
    n3 = negotiator.negotiate(full, hw)
    check("T11: human-device compatible", n3.compatible)
    check("T11: human-device common = 4", n3.common_level == 4)

    # Oracle + plugin — check incompatibility (plugin not in oracle's can_pair_with)
    oracle = EntityFactory.make_standard("oracle", "price-feed", "lct:web4:society:s1")
    plugin = EntityFactory.make_minimal("plugin", "tiny")
    n4 = negotiator.negotiate(oracle, plugin)
    # Oracle can pair with service, ai — not plugin
    # But plugin can pair with plugin, ai, service — not oracle
    check("T11: oracle-plugin incompatible", not n4.compatible)

    # ── T12: Level Upgrade Path ──────────────────────────────
    print("\n═══ T12: Level Upgrade Path ═══")
    # Upgrade minimal (1) → basic (2): needs relationships
    up1 = upgrader.can_upgrade(minimal, 2)
    check("T12: minimal→basic blocked (no relationships)", not up1.success)

    # Add relationship, then upgrade
    minimal.mrh.bound.append(MRHRelationship(lct_id="lct:web4:ai:parent", rel_type="parent", ts=_now()))
    minimal.policy.capabilities.append("execute:irp")
    # T3 needs all non-zero for level 2
    for d in T3_DIMENSIONS:
        minimal.t3.dimensions[d] = max(minimal.t3.dimensions[d] or 0, 0.1)
    up2 = upgrader.upgrade(minimal, 2)
    check("T12: minimal→basic succeeds after adding req", up2.success)
    check("T12: now at level 2", minimal.capability_level == CapLevel.BASIC)

    # No downgrades
    down = upgrader.can_upgrade(minimal, 1)
    check("T12: downgrade blocked", not down.success)
    check("T12: downgrade reason mentions downgrade", "downgrade" in down.reason.lower())

    # Skip levels blocked
    skip = upgrader.can_upgrade(minimal, 4)
    check("T12: skip levels blocked", not skip.success)

    # Level 5 post-hoc blocked
    full_sw = EntityFactory.make_full("device", "sw-only", "lct:web4:society:s1")
    up5 = upgrader.can_upgrade(full_sw, 5)
    check("T12: level 5 post-hoc blocked", not up5.success)
    check("T12: reason mentions hardware", "hardware" in up5.reason.lower())

    # ── T13: Stub Format ─────────────────────────────────────
    print("\n═══ T13: Stub Format ═══")
    s = StubComponent(reason="Self-issued entity")
    sd = s.to_dict()
    check("T13: stub has stub=true", sd["stub"] is True)
    check("T13: stub has reason", sd["reason"] == "Self-issued entity")

    # T3 stub
    t3_stub = Tensor.make_stub(T3_DIMENSIONS, "Level 0 entity")
    check("T13: T3 stub is_stub", t3_stub.is_stub())
    t3d = t3_stub.to_dict()
    check("T13: T3 stub dict has stub=true", t3d["stub"] is True)
    check("T13: T3 stub all dims null", all(v is None for v in t3d["dimensions"].values()))

    # Birth cert stub
    bc_stub = BirthCertificate(stub=True, reason="Self-issued entity")
    bcd = bc_stub.to_dict()
    check("T13: BC stub has stub=true", bcd["stub"] is True)
    check("T13: BC stub is_stub", bc_stub.is_stub())

    # HW attestation stub
    hw_stub = HardwareAttestation(stub=True, reason="Software-only binding")
    hwd = hw_stub.to_dict()
    check("T13: HW stub has stub=true", hwd["stub"] is True)
    check("T13: HW stub key_storage=software", hwd["key_storage"] == "software")

    # ── T14: Security — Misrepresentation ────────────────────
    print("\n═══ T14: Security — Misrepresentation Detection ═══")
    # Entity claiming level 3 but only level 1 components
    imposter = EntityFactory.make_minimal("ai", "imposter")
    imposter.capability_level = CapLevel.STANDARD  # Claims 3
    mr = security.check_misrepresentation(imposter)
    check("T14: misrepresentation detected", not mr.clean)
    check("T14: severity is critical", mr.severity == "critical")
    check("T14: issue mentions MISREPRESENTATION", any("MISREPRESENTATION" in i for i in mr.issues))

    # Honest entity — no misrepresentation
    honest = EntityFactory.make_standard("ai", "honest", "lct:web4:device:d1")
    mr2 = security.check_misrepresentation(honest)
    check("T14: honest entity clean", mr2.clean)

    # ── T15: Security — Stub Exploitation ────────────────────
    print("\n═══ T15: Security — Stub Exploitation ═══")
    # Level 1 entity with stub T3 — exploitation
    stub_exploit = LCTEntity(
        lct_id="lct:web4:plugin:exploit",
        entity_type="plugin",
        capability_level=1,
        binding=Binding(entity_type="plugin", public_key="mb64:ed25519:x", binding_proof="cose:ES256:x"),
        # T3/V3 remain stubs (default)
    )
    se = security.check_stub_exploitation(stub_exploit)
    check("T15: stub exploitation detected at level 1", not se.clean)
    check("T15: exploitation severity critical", se.severity == "critical")

    # Level 4 with stub birth cert — exploitation
    fake_full = EntityFactory.make_standard("human", "fake", "lct:web4:device:d1")
    fake_full.capability_level = CapLevel.FULL
    se2 = security.check_stub_exploitation(fake_full)
    check("T15: stub birth cert at level 4 detected", not se2.clean)

    # Clean entity — no exploitation
    se3 = security.check_stub_exploitation(standard)
    check("T15: clean entity no exploitation", se3.clean)

    # ── T16: Security — Upgrade Attacks ──────────────────────
    print("\n═══ T16: Security — Upgrade Attack Detection ═══")
    # Post-hoc hardware binding
    sw_device = EntityFactory.make_full("device", "sw-dev", "lct:web4:society:s1")
    ua = security.check_upgrade_attack(sw_device, 5)
    check("T16: post-hoc hw binding attack detected", not ua.clean)
    check("T16: hw attack severity critical", ua.severity == "critical")

    # Level 4 without society
    nosoc = EntityFactory.make_standard("human", "nosoc", "lct:web4:device:d1")
    ua2 = security.check_upgrade_attack(nosoc, 4)
    check("T16: level 4 without society detected", not ua2.clean)

    # Level 3 without attestation
    noatt = EntityFactory.make_basic("ai", "noatt", "lct:web4:device:d1")
    noatt.attestations = []
    ua3 = security.check_upgrade_attack(noatt, 3)
    check("T16: level 3 without attestation detected", not ua3.clean)

    # Clean upgrade — all requirements met
    valid_basic = EntityFactory.make_basic("plugin", "valid", "lct:web4:ai:parent")
    ua4 = security.check_upgrade_attack(valid_basic, 2)
    check("T16: clean upgrade no issues", ua4.clean)

    # ── T17: Serialization Roundtrip ─────────────────────────
    print("\n═══ T17: Serialization Roundtrip ═══")
    for name, entity in [("stub", stub), ("minimal", EntityFactory.make_minimal("plugin", "rt1")),
                          ("standard", EntityFactory.make_standard("ai", "rt2", "lct:web4:device:d1")),
                          ("full", EntityFactory.make_full("human", "rt3", "lct:web4:society:s1")),
                          ("hardware", EntityFactory.make_hardware("device", "rt4", "lct:web4:society:s1"))]:
        d = entity.to_dict()
        j = json.dumps(d)
        parsed = json.loads(j)
        check(f"T17: {name} roundtrip — lct_id preserved", parsed["lct_id"] == entity.lct_id)
        check(f"T17: {name} roundtrip — level preserved", parsed["capability_level"] == int(entity.capability_level))

    # ── T18: Trust Range Boundaries ──────────────────────────
    print("\n═══ T18: Trust Range Boundaries ═══")
    for level in CapLevel:
        lo, hi = TRUST_TIERS[level]
        entity_at_level = LCTEntity(
            lct_id=f"lct:web4:ai:trust-test",
            entity_type="ai",
            capability_level=level,
        )
        check(f"T18: level {level} range [{lo}, {hi}]", lo <= hi)
    check("T18: STUB range starts at 0", TRUST_TIERS[CapLevel.STUB][0] == 0.0)
    check("T18: HARDWARE range ends at 1", TRUST_TIERS[CapLevel.HARDWARE][1] == 1.0)
    check("T18: ranges are monotonic",
          all(TRUST_TIERS[CapLevel(i)][0] <= TRUST_TIERS[CapLevel(i+1)][0] for i in range(5)))

    # ── T19: Entity Type Coverage ────────────────────────────
    print("\n═══ T19: Entity Type Coverage ═══")
    check("T19: 21 entity types defined", len(ENTITY_LEVEL_RANGES) == 21)
    core_types = ["human", "ai", "organization", "role", "task", "resource",
                   "device", "service", "oracle", "accumulator", "dictionary", "hybrid"]
    for ct in core_types:
        check(f"T19: core type '{ct}' in registry", ct in ENTITY_LEVEL_RANGES)
    extended = ["plugin", "session", "relationship", "pattern", "society", "witness", "pending", "policy", "infrastructure"]
    for et in extended:
        check(f"T19: extended type '{et}' in registry", et in ENTITY_LEVEL_RANGES)

    # ── T20: Negotiation Result Serialization ────────────────
    print("\n═══ T20: Negotiation + Full Validation Integration ═══")
    # Build a realistic scenario: society issues birth cert to AI
    society = EntityFactory.make_full("society", "web4-foundation", "lct:web4:society:root")
    agent = EntityFactory.make_standard("ai", "claude-1", "lct:web4:device:legion")

    # Negotiate
    n = negotiator.negotiate(society, agent)
    nd = n.to_dict()
    check("T20: negotiation result serializes", "compatible" in nd)
    check("T20: society-ai compatible", n.compatible)

    # Full validation of society
    r_soc = validator.validate(society)
    check("T20: society validates at level 4", r_soc.valid)

    # Security check on society
    mr_soc = security.check_misrepresentation(society)
    check("T20: society no misrepresentation", mr_soc.clean)

    se_soc = security.check_stub_exploitation(society)
    check("T20: society no stub exploitation", se_soc.clean)

    # Verify the hardware entity passes all security checks
    hw_sec = security.check_misrepresentation(hw)
    check("T20: hardware no misrepresentation", hw_sec.clean)
    hw_stub_check = security.check_stub_exploitation(hw)
    check("T20: hardware no stub exploitation", hw_stub_check.clean)

    # ══════════════════════════════════════════════════════════
    print(f"""
{'='*60}
  LCT Capability Levels — Track Q Results
  {passed} passed, {failed} failed out of {passed + failed} checks
{'='*60}
""")

    if failed == 0:
        print("  All checks pass — 6-level capability framework validated")
        print("  Levels 0-5: STUB → MINIMAL → BASIC → STANDARD → FULL → HARDWARE")
        print("  CapabilityValidator + CapabilityQuery + LevelUpgrader")
        print("  CrossDomainNegotiator + SecurityChecker (3 attack types)")
        print(f"  {len(ENTITY_LEVEL_RANGES)} entity types with level range enforcement")
    else:
        print("  Some checks failed — review output above")

    return passed, failed


if __name__ == "__main__":
    run_tests()
