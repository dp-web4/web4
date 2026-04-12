#!/usr/bin/env python3
"""
LCT Capability Levels — Reference Implementation
===================================================

Implements the LCT Capability Levels specification (core-spec/lct-capability-levels.md):
- 6 capability levels (STUB → HARDWARE)
- Per-level field requirements and validation
- Capability query protocol (request/response)
- Level upgrade path with constraints
- Cross-domain communication negotiation
- Stub format for unimplemented components
- Entity-type/level compatibility enforcement

Self-testing: python3 lct_capability_levels.py
"""

import json
import hashlib
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


# ═══════════════════════════════════════════════════════════════
#  Section 1: Capability Level Definitions
# ═══════════════════════════════════════════════════════════════

class CapabilityLevel(IntEnum):
    STUB = 0        # Placeholder reference
    MINIMAL = 1     # Self-issued bootstrap
    BASIC = 2       # Operational with relationships
    STANDARD = 3    # Autonomous with full tensors
    FULL = 4        # Society-issued with birth certificate
    HARDWARE = 5    # Hardware-bound (TPM/TrustZone)


TRUST_TIERS = {
    CapabilityLevel.STUB:     ("untrusted", 0.0, 0.0),
    CapabilityLevel.MINIMAL:  ("minimal",   0.0, 0.2),
    CapabilityLevel.BASIC:    ("low",       0.2, 0.4),
    CapabilityLevel.STANDARD: ("medium",    0.4, 0.6),
    CapabilityLevel.FULL:     ("high",      0.6, 0.8),
    CapabilityLevel.HARDWARE: ("critical",  0.8, 1.0),
}


# Entity type to typical capability level range (spec §3.3)
ENTITY_LEVEL_RANGES = {
    "human":        (4, 5),
    "ai":           (2, 4),
    "society":      (4, 5),
    "organization": (4, 5),
    "role":         (1, 3),
    "task":         (1, 2),
    "resource":     (1, 3),
    "device":       (3, 5),
    "service":      (2, 4),
    "oracle":       (3, 4),
    "accumulator":  (2, 3),
    "dictionary":   (3, 4),
    "hybrid":       (2, 5),
    "policy":       (3, 4),
    "infrastructure": (1, 3),
    # Extended types (spec §3.2)
    "plugin":       (1, 2),
    "session":      (1, 2),
    "relationship": (1, 2),
    "pattern":      (1, 3),
    "witness":      (3, 4),
    "pending":      (0, 0),
}


# ═══════════════════════════════════════════════════════════════
#  Section 2: Stub Format (spec §5)
# ═══════════════════════════════════════════════════════════════

def make_stub(reason: str) -> dict:
    """Create a stub for unimplemented components (spec §5.2)."""
    return {"stub": True, "reason": reason}


def is_stub(component: Optional[dict]) -> bool:
    """Check if a component is a stub."""
    return component is not None and component.get("stub") is True


def t3_stub(reason: str = "Level 0 entity") -> dict:
    """T3 tensor stub with null dimensions (spec §5.3)."""
    return {
        "dimensions": {
            "technical_competence": None,
            "social_reliability": None,
            "temporal_consistency": None,
            "witness_count": None,
            "lineage_depth": None,
            "context_alignment": None,
        },
        "composite_score": None,
        "stub": True,
        "reason": reason,
    }


def v3_stub(reason: str = "Level 0 entity") -> dict:
    """V3 tensor stub with null dimensions."""
    return {
        "dimensions": {
            "energy_balance": None,
            "contribution_history": None,
            "resource_stewardship": None,
            "network_effects": None,
            "reputation_capital": None,
            "temporal_value": None,
        },
        "composite_score": None,
        "stub": True,
        "reason": reason,
    }


def birth_cert_stub(reason: str = "Self-issued entity") -> dict:
    """Birth certificate stub (spec §5.3)."""
    return {
        "issuing_society": None,
        "citizen_role": None,
        "birth_witnesses": [],
        "stub": True,
        "reason": reason,
    }


def hw_attestation_stub(reason: str = "Software-only binding") -> dict:
    """Hardware attestation stub (spec §5.3)."""
    return {
        "platform": None,
        "key_storage": "software",
        "stub": True,
        "reason": reason,
    }


# ═══════════════════════════════════════════════════════════════
#  Section 3: T3/V3 Tensor Types
# ═══════════════════════════════════════════════════════════════

T3_DIMENSIONS = [
    "technical_competence", "social_reliability", "temporal_consistency",
    "witness_count", "lineage_depth", "context_alignment",
]

V3_DIMENSIONS = [
    "energy_balance", "contribution_history", "resource_stewardship",
    "network_effects", "reputation_capital", "temporal_value",
]


@dataclass
class T3Tensor:
    dimensions: dict
    composite_score: float
    last_computed: str = ""
    computation_witnesses: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "dimensions": dict(self.dimensions),
            "composite_score": self.composite_score,
        }
        if self.last_computed:
            d["last_computed"] = self.last_computed
        if self.computation_witnesses:
            d["computation_witnesses"] = list(self.computation_witnesses)
        return d

    @staticmethod
    def initial(ts: str = "") -> "T3Tensor":
        dims = {d: 0.1 for d in T3_DIMENSIONS}
        dims["witness_count"] = 0.0
        dims["lineage_depth"] = 0.0
        return T3Tensor(dimensions=dims, composite_score=0.067, last_computed=ts)

    def has_all_nonzero(self) -> bool:
        return all(v is not None and v > 0 for v in self.dimensions.values())


@dataclass
class V3Tensor:
    dimensions: dict
    composite_score: float
    last_computed: str = ""
    computation_witnesses: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "dimensions": dict(self.dimensions),
            "composite_score": self.composite_score,
        }
        if self.last_computed:
            d["last_computed"] = self.last_computed
        if self.computation_witnesses:
            d["computation_witnesses"] = list(self.computation_witnesses)
        return d

    @staticmethod
    def zero(ts: str = "") -> "V3Tensor":
        return V3Tensor(
            dimensions={d: 0.0 for d in V3_DIMENSIONS},
            composite_score=0.0,
            last_computed=ts,
        )


# ═══════════════════════════════════════════════════════════════
#  Section 4: LCT Entity with Capability Level
# ═══════════════════════════════════════════════════════════════

@dataclass
class MRHRelationship:
    lct_id: str
    rel_type: str  # "parent", "child", "peer"
    binding_context: str = ""
    ts: str = ""
    pairing_type: str = ""
    permanent: bool = False
    role: str = ""
    last_attestation: str = ""
    witness_count: int = 0

    def to_dict(self) -> dict:
        d = {"lct_id": self.lct_id, "type": self.rel_type}
        if self.binding_context:
            d["binding_context"] = self.binding_context
        if self.ts:
            d["ts"] = self.ts
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
        return d


@dataclass
class Attestation:
    witness: str
    att_type: str
    claims: dict
    sig: str
    ts: str

    def to_dict(self) -> dict:
        return {
            "witness": self.witness,
            "type": self.att_type,
            "claims": self.claims,
            "sig": self.sig,
            "ts": self.ts,
        }


@dataclass
class CapabilityLCT:
    """An LCT with capability level tracking and validation."""

    lct_id: str
    entity_type: str
    capability_level: CapabilityLevel
    subject: str = ""

    # Binding
    binding: Optional[dict] = None  # public_key, hardware_anchor, etc.

    # MRH
    mrh_bound: list = field(default_factory=list)
    mrh_paired: list = field(default_factory=list)
    mrh_witnessing: list = field(default_factory=list)
    horizon_depth: int = 0
    mrh_last_updated: str = ""

    # Tensors
    t3: Optional[T3Tensor] = None
    v3: Optional[V3Tensor] = None

    # Policy
    policy_capabilities: list = field(default_factory=list)
    policy_constraints: dict = field(default_factory=dict)

    # Birth certificate
    birth_certificate: Optional[dict] = None

    # Hardware attestation
    hardware_attestation: Optional[dict] = None

    # Attestations
    attestations: list = field(default_factory=list)

    # Lineage
    lineage: list = field(default_factory=list)

    # Revocation
    revocation: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {
            "lct_id": self.lct_id,
            "entity_type": self.entity_type,
            "capability_level": self.capability_level.value,
        }
        if self.subject:
            d["subject"] = self.subject

        # Binding
        if self.binding:
            d["binding"] = dict(self.binding)
        else:
            d["binding"] = None

        # MRH
        if self.capability_level >= CapabilityLevel.MINIMAL:
            d["mrh"] = {
                "bound": [r.to_dict() for r in self.mrh_bound],
                "paired": [r.to_dict() for r in self.mrh_paired],
                "witnessing": [r.to_dict() for r in self.mrh_witnessing],
                "horizon_depth": self.horizon_depth,
                "last_updated": self.mrh_last_updated,
            }
        else:
            d["mrh"] = None

        # Tensors
        if self.t3:
            d["t3_tensor"] = self.t3.to_dict()
        else:
            d["t3_tensor"] = t3_stub()

        if self.v3:
            d["v3_tensor"] = self.v3.to_dict()
        else:
            d["v3_tensor"] = v3_stub()

        # Policy
        d["policy"] = {
            "capabilities": list(self.policy_capabilities),
            "constraints": dict(self.policy_constraints),
        }

        # Birth certificate
        if self.birth_certificate:
            d["birth_certificate"] = dict(self.birth_certificate)
        else:
            d["birth_certificate"] = birth_cert_stub()

        # Hardware
        if self.hardware_attestation:
            d["hardware_attestation"] = dict(self.hardware_attestation)
        else:
            d["hardware_attestation"] = hw_attestation_stub()

        # Attestations
        if self.attestations:
            d["attestations"] = [a.to_dict() for a in self.attestations]

        # Lineage
        if self.lineage:
            d["lineage"] = list(self.lineage)

        # Revocation
        if self.revocation:
            d["revocation"] = dict(self.revocation)

        return d

    def validate(self) -> list:
        """Validate LCT against its claimed capability level. Returns list of violations."""
        errors = []

        # All levels: lct_id format
        if not self.lct_id.startswith("lct:web4:"):
            errors.append("lct_id must start with 'lct:web4:'")

        # All levels: entity_type required
        if not self.entity_type:
            errors.append("entity_type is required")

        # Entity-level compatibility (spec §3.3)
        if self.entity_type in ENTITY_LEVEL_RANGES:
            lo, hi = ENTITY_LEVEL_RANGES[self.entity_type]
            if not (lo <= self.capability_level <= hi):
                errors.append(
                    f"entity_type '{self.entity_type}' typical range is {lo}-{hi}, "
                    f"but capability_level is {self.capability_level}"
                )

        # Level 1+: binding with public key
        if self.capability_level >= CapabilityLevel.MINIMAL:
            if not self.binding or not self.binding.get("public_key"):
                errors.append("Level 1+ requires binding.public_key")
            if not self.binding or not self.binding.get("binding_proof"):
                errors.append("Level 1+ requires binding.binding_proof")
            # T3 must have all 6 dimensions
            if not self.t3:
                errors.append("Level 1+ requires T3 tensor (not stub)")
            elif len(self.t3.dimensions) != 6:
                errors.append("T3 must have exactly 6 dimensions")
            # V3 must have all 6 dimensions
            if not self.v3:
                errors.append("Level 1+ requires V3 tensor (not stub)")
            elif len(self.v3.dimensions) != 6:
                errors.append("V3 must have exactly 6 dimensions")

        # Level 2+: at least one MRH relationship + policy capability
        if self.capability_level >= CapabilityLevel.BASIC:
            if not self.mrh_bound and not self.mrh_paired:
                errors.append("Level 2+ requires at least one bound or paired relationship")
            if self.t3 and not self.t3.has_all_nonzero():
                errors.append("Level 2+ requires all T3 dimensions nonzero")
            if not self.policy_capabilities:
                errors.append("Level 2+ requires at least one policy capability")

        # Level 3+: witnessing, oracle T3, ATP, attestation
        if self.capability_level >= CapabilityLevel.STANDARD:
            if not self.mrh_witnessing:
                errors.append("Level 3+ requires at least one witnessing relationship")
            if self.t3 and not self.t3.computation_witnesses:
                errors.append("Level 3+ requires T3 computation_witnesses")
            if self.v3:
                eb = self.v3.dimensions.get("energy_balance", 0)
                if eb is None or eb <= 0:
                    errors.append("Level 3+ requires non-zero ATP (energy_balance)")
            if not self.attestations:
                errors.append("Level 3+ requires at least one attestation")

        # Level 4+: birth certificate, lineage, revocation
        if self.capability_level >= CapabilityLevel.FULL:
            if not self.birth_certificate or is_stub(self.birth_certificate):
                errors.append("Level 4+ requires complete birth certificate")
            else:
                bw = self.birth_certificate.get("birth_witnesses", [])
                if len(bw) < 3:
                    errors.append("Level 4+ birth certificate needs ≥3 witnesses")
            # Permanent citizen role pairing
            has_citizen = any(
                r.pairing_type == "birth_certificate" and r.permanent
                for r in self.mrh_paired
            )
            if not has_citizen:
                errors.append("Level 4+ requires permanent citizen role pairing")
            if not self.lineage:
                errors.append("Level 4+ requires at least genesis lineage entry")
            if not self.revocation:
                errors.append("Level 4+ requires revocation status tracking")

        # Level 5: hardware binding
        if self.capability_level >= CapabilityLevel.HARDWARE:
            if not self.binding or not self.binding.get("hardware_anchor"):
                errors.append("Level 5 requires binding.hardware_anchor")
            if not self.binding or not self.binding.get("hardware_type"):
                errors.append("Level 5 requires binding.hardware_type (tpm2/trustzone/secure_element)")
            if not self.hardware_attestation or is_stub(self.hardware_attestation):
                errors.append("Level 5 requires complete hardware_attestation")

        return errors

    def trust_tier(self) -> str:
        """Return human-readable trust tier for this level."""
        return TRUST_TIERS[self.capability_level][0]

    def trust_range(self) -> tuple:
        """Return (min, max) trust score range for this level."""
        _, lo, hi = TRUST_TIERS[self.capability_level]
        return (lo, hi)


# ═══════════════════════════════════════════════════════════════
#  Section 5: Capability Query Protocol (spec §4)
# ═══════════════════════════════════════════════════════════════

@dataclass
class CapabilityQuery:
    """Query another LCT's capabilities before trust (spec §4.2)."""
    target_lct: str
    requester_lct: str
    requested_info: list
    timestamp: str
    signature: str = ""

    def to_dict(self) -> dict:
        return {
            "query_type": "capability_discovery",
            "target_lct": self.target_lct,
            "requester_lct": self.requester_lct,
            "requested_info": list(self.requested_info),
            "timestamp": self.timestamp,
            "signature": self.signature,
        }


@dataclass
class CapabilityResponse:
    """Response to capability query (spec §4.3)."""
    source_lct: str
    capability_level: int
    entity_type: str
    supported_components: dict
    relationship_support: dict
    trust_tier: str
    composite_t3: float
    composite_v3: float
    timestamp: str
    signature: str = ""

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
            "timestamp": self.timestamp,
            "signature": self.signature,
        }


def build_capability_response(lct: CapabilityLCT, ts: str) -> CapabilityResponse:
    """Build capability discovery response from an LCT (spec §4.3)."""

    # Determine supported components
    components = {
        "binding": {
            "implemented": lct.binding is not None,
            "hardware_anchored": bool(
                lct.binding and lct.binding.get("hardware_anchor")
            ),
            "key_algorithm": (
                lct.binding.get("public_key", "").split(":")[1]
                if lct.binding and ":" in lct.binding.get("public_key", "")
                else "unknown"
            ),
        },
        "mrh": {
            "implemented": lct.capability_level >= CapabilityLevel.MINIMAL,
            "relationship_types": ["bound", "paired", "witnessing"],
            "horizon_depth": lct.horizon_depth,
        },
        "t3_tensor": {
            "implemented": lct.t3 is not None,
            "dimensions": 6 if lct.t3 else 0,
            "oracle_computed": bool(lct.t3 and lct.t3.computation_witnesses),
        },
        "v3_tensor": {
            "implemented": lct.v3 is not None,
            "dimensions": 6 if lct.v3 else 0,
            "oracle_computed": bool(lct.v3 and lct.v3.computation_witnesses),
        },
        "birth_certificate": {
            "implemented": bool(
                lct.birth_certificate and not is_stub(lct.birth_certificate)
            ),
            "stub": is_stub(lct.birth_certificate) if lct.birth_certificate else True,
        },
        "attestations": {
            "implemented": bool(lct.attestations),
            "count": len(lct.attestations),
        },
        "lineage": {
            "implemented": bool(lct.lineage),
            "stub": not bool(lct.lineage),
        },
    }

    # Relationship support based on entity type
    rel_support = _relationship_support(lct.entity_type)

    t3_score = lct.t3.composite_score if lct.t3 else 0.0
    v3_score = lct.v3.composite_score if lct.v3 else 0.0

    return CapabilityResponse(
        source_lct=lct.lct_id,
        capability_level=lct.capability_level.value,
        entity_type=lct.entity_type,
        supported_components=components,
        relationship_support=rel_support,
        trust_tier=lct.trust_tier(),
        composite_t3=t3_score,
        composite_v3=v3_score,
        timestamp=ts,
    )


def _relationship_support(entity_type: str) -> dict:
    """Determine relationship support by entity type."""
    # Default: any entity can be witnessed
    support = {
        "can_be_bound_by": [],
        "can_pair_with": [],
        "can_witness": [],
        "can_be_witnessed_by": ["oracle", "human", "ai", "witness"],
    }

    if entity_type in ("human", "ai"):
        support["can_be_bound_by"] = ["organization", "society"]
        support["can_pair_with"] = ["role", "ai", "human", "service", "plugin"]
        support["can_witness"] = ["task", "plugin", "session", "ai", "human"]
    elif entity_type == "device":
        support["can_be_bound_by"] = ["organization", "human"]
        support["can_pair_with"] = ["service", "plugin"]
        support["can_witness"] = ["task", "resource"]
    elif entity_type == "plugin":
        support["can_be_bound_by"] = ["ai", "service"]
        support["can_pair_with"] = ["ai", "plugin", "service"]
        support["can_witness"] = ["task", "session"]
    elif entity_type == "service":
        support["can_be_bound_by"] = ["organization"]
        support["can_pair_with"] = ["ai", "human", "device", "plugin"]
        support["can_witness"] = ["task", "resource"]
    elif entity_type in ("society", "organization"):
        support["can_be_bound_by"] = ["society"]
        support["can_pair_with"] = ["human", "ai", "organization"]
        support["can_witness"] = ["human", "ai", "task", "role"]
    elif entity_type == "role":
        support["can_be_bound_by"] = ["organization", "society"]
        support["can_pair_with"] = ["human", "ai"]
        support["can_witness"] = ["task"]
    elif entity_type == "oracle":
        support["can_be_bound_by"] = ["society", "organization"]
        support["can_pair_with"] = ["service", "ai"]
        support["can_witness"] = ["human", "ai", "device", "plugin"]

    return support


# ═══════════════════════════════════════════════════════════════
#  Section 6: Level Upgrade Path (spec §6)
# ═══════════════════════════════════════════════════════════════

UPGRADE_REQUIREMENTS = {
    (0, 1): "Add binding with public key, initialize T3/V3",
    (1, 2): "Establish MRH relationship, add policy capability",
    (2, 3): "Add witnessing, get oracle tensors, receive attestation",
    (3, 4): "Obtain birth certificate from society",
    (4, 5): "Bind to hardware (cannot be done post-hoc)",
}


def can_upgrade(lct: CapabilityLCT, target_level: CapabilityLevel) -> tuple:
    """
    Check if LCT can upgrade to target level.
    Returns (can_upgrade: bool, reason: str).
    """
    current = lct.capability_level

    if target_level <= current:
        return (False, "Cannot downgrade or stay at same level")

    if target_level.value - current.value > 1:
        return (False, "Can only upgrade one level at a time")

    # Level 5 constraint: must have hardware from creation
    if target_level == CapabilityLevel.HARDWARE:
        if not lct.binding or not lct.binding.get("hardware_anchor"):
            return (False, "Hardware binding cannot be added post-hoc")

    # Validate the LCT would pass at target level
    # Temporarily set level and validate
    original = lct.capability_level
    lct.capability_level = target_level
    errors = lct.validate()
    lct.capability_level = original

    if errors:
        return (False, f"Missing requirements: {'; '.join(errors)}")

    return (True, UPGRADE_REQUIREMENTS.get((current, target_level.value), ""))


def upgrade(lct: CapabilityLCT, target_level: CapabilityLevel) -> tuple:
    """
    Attempt to upgrade LCT. Returns (success, message).
    """
    ok, reason = can_upgrade(lct, target_level)
    if not ok:
        return (False, reason)
    lct.capability_level = target_level
    return (True, f"Upgraded to level {target_level.value} ({target_level.name})")


# ═══════════════════════════════════════════════════════════════
#  Section 7: Cross-Domain Communication (spec §7)
# ═══════════════════════════════════════════════════════════════

def negotiate_common_ground(
    lct_a: CapabilityLCT, lct_b: CapabilityLCT
) -> dict:
    """
    Negotiate common ground between two LCTs (spec §7.1).
    Returns negotiation result dict.
    """
    common_level = min(lct_a.capability_level, lct_b.capability_level)

    # Check relationship compatibility
    rel_a = _relationship_support(lct_a.entity_type)
    rel_b = _relationship_support(lct_b.entity_type)

    can_a_pair_b = lct_b.entity_type in rel_a.get("can_pair_with", [])
    can_b_pair_a = lct_a.entity_type in rel_b.get("can_pair_with", [])
    compatible = can_a_pair_b or can_b_pair_a

    # Trust: use lower entity's computation method
    if lct_a.t3 and lct_b.t3:
        trust = min(lct_a.t3.composite_score, lct_b.t3.composite_score)
    else:
        trust = 0.0

    return {
        "common_level": common_level.value,
        "common_level_name": common_level.name,
        "compatible": compatible,
        "a_can_pair_b": can_a_pair_b,
        "b_can_pair_a": can_b_pair_a,
        "trust_floor": trust,
        "relationship_semantics": f"Level {common_level.value}",
    }


# ═══════════════════════════════════════════════════════════════
#  Section 8: Entity Factory (convenience builders)
# ═══════════════════════════════════════════════════════════════

def _ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def create_stub(entity_type: str = "pending", lct_id: str = "") -> CapabilityLCT:
    """Create Level 0 STUB entity."""
    if not lct_id:
        h = hashlib.sha256(f"{entity_type}-{time.time()}".encode()).hexdigest()[:12]
        lct_id = f"lct:web4:{entity_type}:{h}"
    return CapabilityLCT(
        lct_id=lct_id,
        entity_type=entity_type,
        capability_level=CapabilityLevel.STUB,
    )


def create_minimal(
    entity_type: str, key_algo: str = "ed25519", lct_id: str = ""
) -> CapabilityLCT:
    """Create Level 1 MINIMAL entity (self-issued bootstrap)."""
    ts = _ts()
    if not lct_id:
        h = hashlib.sha256(f"{entity_type}-{time.time()}".encode()).hexdigest()[:12]
        lct_id = f"lct:web4:{entity_type}:{h}"
    subject = f"did:web4:key:{hashlib.sha256(lct_id.encode()).hexdigest()[:16]}"

    return CapabilityLCT(
        lct_id=lct_id,
        entity_type=entity_type,
        capability_level=CapabilityLevel.MINIMAL,
        subject=subject,
        binding={
            "entity_type": entity_type,
            "public_key": f"mb64:{key_algo}:pubkey_{lct_id[-8:]}",
            "hardware_anchor": None,
            "created_at": ts,
            "binding_proof": f"cose:ES256:selfproof_{lct_id[-8:]}",
        },
        t3=T3Tensor.initial(ts),
        v3=V3Tensor.zero(ts),
        horizon_depth=1,
        mrh_last_updated=ts,
        birth_certificate=birth_cert_stub(),
    )


def create_standard(
    entity_type: str,
    society_lct: str = "lct:web4:society:default",
    oracle_lct: str = "lct:web4:oracle:trust:fed",
) -> CapabilityLCT:
    """Create Level 3 STANDARD entity with full tensor support."""
    ts = _ts()
    h = hashlib.sha256(f"{entity_type}-{time.time()}".encode()).hexdigest()[:12]
    lct_id = f"lct:web4:{entity_type}:{h}"
    subject = f"did:web4:key:{hashlib.sha256(lct_id.encode()).hexdigest()[:16]}"

    t3 = T3Tensor(
        dimensions={
            "technical_competence": 0.7,
            "social_reliability": 0.6,
            "temporal_consistency": 0.65,
            "witness_count": 0.5,
            "lineage_depth": 0.4,
            "context_alignment": 0.7,
        },
        composite_score=0.59,
        last_computed=ts,
        computation_witnesses=[oracle_lct],
    )
    v3 = V3Tensor(
        dimensions={
            "energy_balance": 100,
            "contribution_history": 0.5,
            "resource_stewardship": 0.6,
            "network_effects": 0.4,
            "reputation_capital": 0.5,
            "temporal_value": 0.55,
        },
        composite_score=0.51,
        last_computed=ts,
        computation_witnesses=[oracle_lct],
    )

    att = Attestation(
        witness=f"did:web4:key:oracle_{h[:6]}",
        att_type="existence",
        claims={"observed_at": ts},
        sig=f"cose:ES256:att_{h[:8]}",
        ts=ts,
    )

    return CapabilityLCT(
        lct_id=lct_id,
        entity_type=entity_type,
        capability_level=CapabilityLevel.STANDARD,
        subject=subject,
        binding={
            "entity_type": entity_type,
            "public_key": f"mb64:ed25519:pubkey_{lct_id[-8:]}",
            "hardware_anchor": None,
            "created_at": ts,
            "binding_proof": f"cose:ES256:proof_{lct_id[-8:]}",
        },
        mrh_bound=[
            MRHRelationship(
                lct_id=society_lct, rel_type="parent",
                binding_context="society", ts=ts,
            )
        ],
        mrh_paired=[
            MRHRelationship(
                lct_id=f"lct:web4:role:operator:{h[:6]}",
                rel_type="peer", ts=ts,
            )
        ],
        mrh_witnessing=[
            MRHRelationship(
                lct_id=f"lct:web4:oracle:time:global",
                rel_type="witness", role="time",
                last_attestation=ts, witness_count=10, ts=ts,
            )
        ],
        horizon_depth=3,
        mrh_last_updated=ts,
        t3=t3,
        v3=v3,
        policy_capabilities=["execute:r6", "read:data", "write:reports"],
        policy_constraints={"max_rate": 1000},
        attestations=[att],
        birth_certificate=birth_cert_stub(),
    )


def create_full(
    entity_type: str,
    society_lct: str = "lct:web4:society:foundation",
    citizen_role: str = "",
    witnesses: list = None,
) -> CapabilityLCT:
    """Create Level 4 FULL entity with society-issued birth certificate."""
    ts = _ts()
    h = hashlib.sha256(f"{entity_type}-{time.time()}".encode()).hexdigest()[:12]
    lct_id = f"lct:web4:{entity_type}:{h}"

    if not citizen_role:
        citizen_role = f"lct:web4:role:citizen:{entity_type}_{h[:6]}"
    if not witnesses:
        witnesses = [
            f"lct:web4:witness:w1_{h[:4]}",
            f"lct:web4:witness:w2_{h[:4]}",
            f"lct:web4:witness:w3_{h[:4]}",
        ]

    oracle_lct = "lct:web4:oracle:trust:federation"

    # Start from a standard entity and add L4 requirements
    lct = create_standard(entity_type, society_lct, oracle_lct)
    lct.lct_id = lct_id
    lct.capability_level = CapabilityLevel.FULL

    # Birth certificate
    lct.birth_certificate = {
        "issuing_society": society_lct,
        "citizen_role": citizen_role,
        "birth_timestamp": ts,
        "birth_witnesses": witnesses,
        "genesis_block_hash": f"0x{hashlib.sha256(lct_id.encode()).hexdigest()[:16]}",
        "birth_context": "federation",
    }

    # Permanent citizen role pairing
    lct.mrh_paired.append(MRHRelationship(
        lct_id=citizen_role,
        rel_type="peer",
        pairing_type="birth_certificate",
        permanent=True,
        ts=ts,
    ))

    # Lineage
    lct.lineage = [{"parent": None, "reason": "genesis", "ts": ts}]

    # Revocation
    lct.revocation = {"status": "active", "ts": None, "reason": None}

    return lct


def create_hardware(
    entity_type: str = "device",
    hardware_type: str = "tpm2",
    society_lct: str = "lct:web4:society:foundation",
) -> CapabilityLCT:
    """Create Level 5 HARDWARE entity with hardware attestation."""
    lct = create_full(entity_type, society_lct)
    lct.capability_level = CapabilityLevel.HARDWARE

    h = lct.lct_id.split(":")[-1]

    # Add hardware binding
    lct.binding["hardware_anchor"] = f"eat:mb64:hw:{h}"
    lct.binding["hardware_type"] = hardware_type
    lct.binding["attestation_chain"] = [
        f"eat:manufacturer:{h[:4]}",
        f"eat:platform:{h[:4]}",
        f"eat:application:{h[:4]}",
    ]

    # Hardware attestation
    lct.hardware_attestation = {
        "platform": f"linux-{hardware_type}",
        "key_storage": hardware_type,
        "boot_integrity": True,
        "pcr_values": {"0": f"pcr0_{h[:8]}", "7": f"pcr7_{h[:8]}"},
        "last_attestation": _ts(),
    }

    return lct


# ═══════════════════════════════════════════════════════════════
#  Section 9: Self-Tests
# ═══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(condition, label):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label}")

    # ─── T1: Level 0 STUB ───
    print("\n═══ T1: Level 0 STUB ═══")
    stub = create_stub("pending", "lct:web4:pending:placeholder123")
    check(stub.capability_level == CapabilityLevel.STUB, "T1: Level is STUB (0)")
    check(stub.entity_type == "pending", "T1: Entity type is pending")
    errors = stub.validate()
    check(len(errors) == 0, f"T1: STUB validates cleanly — {len(errors)} errors")
    d = stub.to_dict()
    check(d["binding"] is None, "T1: Binding is None")
    check(d["mrh"] is None, "T1: MRH is None")
    check(d["t3_tensor"]["stub"] is True, "T1: T3 is stub")
    check(d["v3_tensor"]["stub"] is True, "T1: V3 is stub")
    check(stub.trust_tier() == "untrusted", "T1: Trust tier is untrusted")

    # ─── T2: Level 1 MINIMAL ───
    print("\n═══ T2: Level 1 MINIMAL ═══")
    minimal = create_minimal("plugin", lct_id="lct:web4:plugin:vision-irp-abc123")
    check(minimal.capability_level == CapabilityLevel.MINIMAL, "T2: Level is MINIMAL (1)")
    errors = minimal.validate()
    check(len(errors) == 0, f"T2: MINIMAL validates — {len(errors)} errors")
    d = minimal.to_dict()
    check(d["binding"]["public_key"].startswith("mb64:"), "T2: Has public key")
    check(d["binding"]["binding_proof"].startswith("cose:"), "T2: Has binding proof")
    check(d["mrh"] is not None, "T2: MRH present")
    check(len(d["t3_tensor"]["dimensions"]) == 6, "T2: T3 has 6 dimensions")
    check(len(d["v3_tensor"]["dimensions"]) == 6, "T2: V3 has 6 dimensions")
    check(minimal.trust_tier() == "minimal", "T2: Trust tier is minimal")
    lo, hi = minimal.trust_range()
    check(lo == 0.0 and hi == 0.2, f"T2: Trust range [0.0, 0.2] — got [{lo}, {hi}]")

    # ─── T3: Level 2 BASIC ───
    print("\n═══ T3: Level 2 BASIC ═══")
    basic = create_minimal("ai", lct_id="lct:web4:ai:basic-agent-001")
    basic.capability_level = CapabilityLevel.BASIC
    # Should fail — missing relationship and nonzero T3
    errors = basic.validate()
    check(len(errors) > 0, f"T3: Incomplete BASIC fails — {len(errors)} errors")
    # Fix: add relationship, nonzero T3, policy
    basic.mrh_bound.append(MRHRelationship(
        lct_id="lct:web4:ai:orchestrator", rel_type="parent",
        binding_context="deployment", ts=_ts(),
    ))
    basic.t3 = T3Tensor(
        dimensions={
            "technical_competence": 0.5, "social_reliability": 0.4,
            "temporal_consistency": 0.3, "witness_count": 0.2,
            "lineage_depth": 0.3, "context_alignment": 0.5,
        },
        composite_score=0.37,
    )
    basic.policy_capabilities = ["execute:irp", "read:patterns"]
    errors = basic.validate()
    check(len(errors) == 0, f"T3: Complete BASIC validates — {len(errors)} errors")
    check(basic.trust_tier() == "low", "T3: Trust tier is low")

    # ─── T4: Level 3 STANDARD ───
    print("\n═══ T4: Level 3 STANDARD ═══")
    standard = create_standard("ai")
    errors = standard.validate()
    check(len(errors) == 0, f"T4: STANDARD validates — {len(errors)} errors")
    check(standard.trust_tier() == "medium", "T4: Trust tier is medium")
    check(standard.t3.composite_score == 0.59, "T4: T3 composite is 0.59")
    check(standard.v3.dimensions["energy_balance"] == 100, "T4: ATP is 100")
    check(len(standard.attestations) == 1, "T4: Has 1 attestation")
    check(len(standard.mrh_witnessing) == 1, "T4: Has 1 witnessing")
    d = standard.to_dict()
    check(d["capability_level"] == 3, "T4: Serializes level 3")

    # ─── T5: Level 4 FULL ───
    print("\n═══ T5: Level 4 FULL ═══")
    full = create_full("human")
    errors = full.validate()
    check(len(errors) == 0, f"T5: FULL validates — {len(errors)} errors")
    check(full.trust_tier() == "high", "T5: Trust tier is high")
    check(full.birth_certificate is not None, "T5: Has birth certificate")
    check(not is_stub(full.birth_certificate), "T5: Birth cert is not stub")
    bw = full.birth_certificate.get("birth_witnesses", [])
    check(len(bw) >= 3, f"T5: Birth cert has ≥3 witnesses — got {len(bw)}")
    check(full.revocation["status"] == "active", "T5: Revocation status is active")
    check(len(full.lineage) >= 1, "T5: Has lineage")
    # Check permanent citizen pairing
    has_citizen = any(
        r.pairing_type == "birth_certificate" and r.permanent
        for r in full.mrh_paired
    )
    check(has_citizen, "T5: Has permanent citizen role pairing")

    # ─── T6: Level 5 HARDWARE ───
    print("\n═══ T6: Level 5 HARDWARE ═══")
    hw = create_hardware("device", "tpm2")
    errors = hw.validate()
    check(len(errors) == 0, f"T6: HARDWARE validates — {len(errors)} errors")
    check(hw.trust_tier() == "critical", "T6: Trust tier is critical")
    check(hw.binding["hardware_anchor"] is not None, "T6: Has hardware anchor")
    check(hw.binding["hardware_type"] == "tpm2", "T6: Hardware type is tpm2")
    check(hw.hardware_attestation is not None, "T6: Has hardware attestation")
    check(not is_stub(hw.hardware_attestation), "T6: HW attestation not stub")
    check(hw.hardware_attestation["boot_integrity"] is True, "T6: Boot integrity true")
    check("0" in hw.hardware_attestation.get("pcr_values", {}), "T6: PCR values present")

    # ─── T7: Validation catches level mismatches ───
    print("\n═══ T7: Validation Rejects Invalid ═══")
    # MINIMAL without binding → should fail
    broken = CapabilityLCT(
        lct_id="lct:web4:plugin:broken", entity_type="plugin",
        capability_level=CapabilityLevel.MINIMAL,
    )
    errors = broken.validate()
    check(len(errors) > 0, f"T7: MINIMAL without binding fails — {len(errors)} errors")
    check(any("public_key" in e for e in errors), "T7: Missing public_key caught")

    # STANDARD without attestation
    no_att = create_standard("ai")
    no_att.attestations = []
    errors = no_att.validate()
    check(len(errors) > 0, "T7: STANDARD without attestation fails")
    check(any("attestation" in e for e in errors), "T7: Missing attestation caught")

    # FULL without birth cert
    no_bc = create_full("human")
    no_bc.birth_certificate = birth_cert_stub()
    errors = no_bc.validate()
    check(len(errors) > 0, "T7: FULL without birth cert fails")

    # HARDWARE without hardware_anchor
    no_hw = create_hardware("device")
    no_hw.binding["hardware_anchor"] = None
    no_hw.binding["hardware_type"] = None
    errors = no_hw.validate()
    check(len(errors) > 0, "T7: HARDWARE without anchor fails")

    # ─── T8: Entity-Level Compatibility ───
    print("\n═══ T8: Entity-Level Compatibility ═══")
    # Human at Level 1 should warn (typical range 4-5)
    human_l1 = create_minimal("human", lct_id="lct:web4:human:low-lvl")
    errors = human_l1.validate()
    check(any("typical range" in e for e in errors), "T8: Human at L1 warns about range")

    # Plugin at Level 1 should be fine (typical range 1-2)
    plugin_l1 = create_minimal("plugin", lct_id="lct:web4:plugin:normal")
    errors = plugin_l1.validate()
    check(len(errors) == 0, "T8: Plugin at L1 validates")

    # Pending at Level 0 should be fine
    pending = create_stub("pending", "lct:web4:pending:ok")
    errors = pending.validate()
    check(len(errors) == 0, "T8: Pending at L0 validates")

    # Device at Level 1 should warn (typical range 3-5)
    dev_l1 = create_minimal("device", lct_id="lct:web4:device:low")
    errors = dev_l1.validate()
    check(any("typical range" in e for e in errors), "T8: Device at L1 warns")

    # ─── T9: Capability Query Protocol ───
    print("\n═══ T9: Capability Query Protocol ═══")
    agent = create_standard("ai")
    query = CapabilityQuery(
        target_lct=agent.lct_id,
        requester_lct="lct:web4:plugin:requester",
        requested_info=["capability_level", "entity_type", "supported_components",
                        "relationship_types", "trust_tier"],
        timestamp=_ts(),
    )
    qd = query.to_dict()
    check(qd["query_type"] == "capability_discovery", "T9: Query type correct")
    check(len(qd["requested_info"]) == 5, "T9: 5 requested info fields")

    resp = build_capability_response(agent, _ts())
    rd = resp.to_dict()
    check(rd["response_type"] == "capability_discovery", "T9: Response type correct")
    check(rd["capability_level"] == 3, "T9: Response level is 3")
    check(rd["entity_type"] == "ai", "T9: Response entity type is ai")
    check(rd["trust_tier"] == "medium", "T9: Response trust tier")
    check(rd["composite_t3"] == 0.59, "T9: Response T3 score")
    check(rd["supported_components"]["binding"]["implemented"] is True, "T9: Binding implemented")
    check(rd["supported_components"]["t3_tensor"]["oracle_computed"] is True, "T9: T3 oracle-computed")
    check(rd["supported_components"]["birth_certificate"]["stub"] is True, "T9: Birth cert is stub")
    check("can_pair_with" in rd["relationship_support"], "T9: Has relationship support")

    # ─── T10: Level Upgrade Path ───
    print("\n═══ T10: Level Upgrade Path ═══")
    plugin = create_minimal("plugin", lct_id="lct:web4:plugin:upgrading")

    # Can't upgrade from 1 to 3 (skip)
    ok, reason = can_upgrade(plugin, CapabilityLevel.STANDARD)
    check(not ok, f"T10: Can't skip levels — {reason}")

    # Can't upgrade to same level
    ok, reason = can_upgrade(plugin, CapabilityLevel.MINIMAL)
    check(not ok, "T10: Can't stay at same level")

    # Upgrade 1 → 2 (needs relationship + policy)
    ok, reason = can_upgrade(plugin, CapabilityLevel.BASIC)
    check(not ok, f"T10: L1→L2 missing reqs — {reason}")

    # Fix and upgrade
    plugin.mrh_bound.append(MRHRelationship(
        lct_id="lct:web4:ai:parent", rel_type="parent", ts=_ts(),
    ))
    plugin.t3 = T3Tensor(
        dimensions={d: 0.3 for d in T3_DIMENSIONS},
        composite_score=0.3,
    )
    plugin.policy_capabilities = ["execute:irp"]
    ok, msg = upgrade(plugin, CapabilityLevel.BASIC)
    check(ok, f"T10: L1→L2 upgrade succeeds — {msg}")
    check(plugin.capability_level == CapabilityLevel.BASIC, "T10: Level is now BASIC")

    # Can't downgrade
    ok, reason = can_upgrade(plugin, CapabilityLevel.MINIMAL)
    check(not ok, "T10: Can't downgrade")

    # ─── T11: Cross-Domain Negotiation ───
    print("\n═══ T11: Cross-Domain Negotiation ═══")
    device = create_hardware("device")
    plugin2 = create_minimal("plugin", lct_id="lct:web4:plugin:edge001")

    result = negotiate_common_ground(device, plugin2)
    check(result["common_level"] == 1, f"T11: Common level = min(5,1) = 1 — got {result['common_level']}")
    check(result["common_level_name"] == "MINIMAL", "T11: Common level name is MINIMAL")
    # Device not in plugin's can_pair_with but plugin in device's
    check("compatible" in result, "T11: Compatibility assessed")

    # Same-level negotiation
    a1 = create_standard("ai")
    a2 = create_standard("ai")
    result2 = negotiate_common_ground(a1, a2)
    check(result2["common_level"] == 3, "T11: Same-level common = 3")
    check(result2["compatible"] is True, "T11: AI↔AI compatible")
    check(result2["trust_floor"] == 0.59, "T11: Trust floor correct")

    # ─── T12: Stub Format ───
    print("\n═══ T12: Stub Format ═══")
    s = make_stub("Testing")
    check(s["stub"] is True, "T12: Stub has stub=True")
    check(s["reason"] == "Testing", "T12: Stub has reason")
    check(is_stub(s), "T12: is_stub detects stub")
    check(not is_stub({"data": 123}), "T12: is_stub rejects non-stub")
    check(not is_stub(None), "T12: is_stub handles None")

    t3s = t3_stub("Level 0")
    check(t3s["stub"] is True, "T12: T3 stub has stub flag")
    check(all(v is None for v in t3s["dimensions"].values()), "T12: T3 stub dims are None")
    check(t3s["composite_score"] is None, "T12: T3 stub score is None")

    v3s = v3_stub("Level 0")
    check(v3s["stub"] is True, "T12: V3 stub has stub flag")

    bcs = birth_cert_stub()
    check(bcs["stub"] is True, "T12: Birth cert stub")
    check(bcs["issuing_society"] is None, "T12: Birth cert stub society is None")

    hws = hw_attestation_stub()
    check(hws["stub"] is True, "T12: HW attestation stub")
    check(hws["key_storage"] == "software", "T12: HW stub key_storage is software")

    # ─── T13: Serialization Roundtrip ───
    print("\n═══ T13: Serialization Roundtrip ═══")
    for level_name, creator in [
        ("STUB", lambda: create_stub()),
        ("MINIMAL", lambda: create_minimal("plugin")),
        ("STANDARD", lambda: create_standard("ai")),
        ("FULL", lambda: create_full("human")),
        ("HARDWARE", lambda: create_hardware("device")),
    ]:
        lct = creator()
        d = lct.to_dict()
        j = json.dumps(d, indent=2)
        parsed = json.loads(j)
        check(parsed["capability_level"] == lct.capability_level.value,
              f"T13: {level_name} roundtrip preserves level")

    # ─── T14: Entity Type Coverage ───
    print("\n═══ T14: Entity Type Coverage ═══")
    check(len(ENTITY_LEVEL_RANGES) == 21, f"T14: 21 entity types defined — got {len(ENTITY_LEVEL_RANGES)}")
    core_types = ["human", "ai", "society", "organization", "role", "task",
                  "resource", "device", "service", "oracle", "accumulator",
                  "dictionary", "hybrid", "policy", "infrastructure"]
    for et in core_types:
        check(et in ENTITY_LEVEL_RANGES, f"T14: Core type '{et}' has range")

    extended_types = ["plugin", "session", "relationship", "pattern", "witness", "pending"]
    for et in extended_types:
        check(et in ENTITY_LEVEL_RANGES, f"T14: Extended type '{et}' has range")

    # ─── T15: Trust Tier Coverage ───
    print("\n═══ T15: Trust Tier Coverage ═══")
    for level in CapabilityLevel:
        tier = TRUST_TIERS[level]
        check(len(tier) == 3, f"T15: Level {level.name} has tier definition")
    check(TRUST_TIERS[CapabilityLevel.STUB][0] == "untrusted", "T15: STUB is untrusted")
    check(TRUST_TIERS[CapabilityLevel.HARDWARE][0] == "critical", "T15: HARDWARE is critical")

    # Non-overlapping ranges
    for i in range(5):
        _, _, hi = TRUST_TIERS[CapabilityLevel(i)]
        _, lo_next, _ = TRUST_TIERS[CapabilityLevel(i + 1)]
        check(hi <= lo_next + 0.001, f"T15: Level {i}→{i+1} ranges don't overlap")

    # ─── T16: Relationship Support ───
    print("\n═══ T16: Relationship Support ═══")
    for et in ["human", "ai", "device", "plugin", "service", "society", "role", "oracle"]:
        rel = _relationship_support(et)
        check("can_pair_with" in rel, f"T16: {et} has can_pair_with")
        check("can_be_witnessed_by" in rel, f"T16: {et} has can_be_witnessed_by")

    # ─── T17: Hardware-specific constraints ───
    print("\n═══ T17: Hardware-Specific Constraints ═══")
    # Can't upgrade to L5 without hardware from creation
    full_sw = create_full("device")
    ok, reason = can_upgrade(full_sw, CapabilityLevel.HARDWARE)
    check(not ok, f"T17: L4→L5 without HW fails — {reason}")
    check("post-hoc" in reason, "T17: Error mentions post-hoc constraint")

    # TrustZone variant
    tz = create_hardware("device", "trustzone")
    check(tz.binding["hardware_type"] == "trustzone", "T17: TrustZone hardware type")
    errors = tz.validate()
    check(len(errors) == 0, f"T17: TrustZone validates — {len(errors)} errors")

    # Secure element variant
    se = create_hardware("device", "secure_element")
    check(se.binding["hardware_type"] == "secure_element", "T17: Secure element type")
    errors = se.validate()
    check(len(errors) == 0, f"T17: Secure element validates — {len(errors)} errors")

    # ─── T18: Upgrade Requirements Documentation ───
    print("\n═══ T18: Upgrade Requirements ═══")
    check(len(UPGRADE_REQUIREMENTS) == 5, f"T18: 5 upgrade paths — got {len(UPGRADE_REQUIREMENTS)}")
    for (lo, hi), desc in UPGRADE_REQUIREMENTS.items():
        check(hi == lo + 1, f"T18: Upgrade {lo}→{hi} is sequential")
        check(len(desc) > 10, f"T18: Upgrade {lo}→{hi} has description")

    # ─── Summary ───
    print(f"\n{'=' * 60}")
    print(f"  LCT Capability Levels — Track Q Results")
    print(f"  {passed} passed, {failed} failed out of {passed + failed} checks")
    print(f"{'=' * 60}")

    if failed == 0:
        print(f"\n  All {passed} checks pass — LCT Capability Levels validated")
        print(f"  6 levels: STUB → MINIMAL → BASIC → STANDARD → FULL → HARDWARE")
        print(f"  Capability query protocol, upgrade paths, cross-domain negotiation")
        print(f"  21 entity types with compatibility ranges")
        print(f"  Stub format for unimplemented components")
    else:
        print(f"\n  {failed} checks need attention")

    return passed, failed


if __name__ == "__main__":
    run_tests()
