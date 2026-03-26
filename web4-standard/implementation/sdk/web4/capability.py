"""
Web4 LCT Capability Levels

Canonical implementation per web4-standard/core-spec/lct-capability-levels.md.

Defines a 6-level capability framework (Stub → Hardware) for Linked Context
Tokens. Each level has progressive requirements — binding, MRH relationships,
witnessing, birth certificates, and hardware attestation — that determine an
LCT's trust tier and interaction capabilities.

Key concepts:
- CapabilityLevel: 0 (STUB) through 5 (HARDWARE)
- TrustTier: maps levels to trust score ranges
- Level assessment: determine actual level from LCT components
- Upgrade paths: validate transitions between levels
- Entity-level ranges: typical level ranges per entity type

Validated against: web4-standard/test-vectors/capability/
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple

from .lct import LCT, EntityType

__all__ = [
    # Classes
    "CapabilityLevel", "TrustTier", "LevelRequirement", "CapabilityAssessment",
    # Functions
    "assess_level", "validate_level", "can_upgrade",
    "level_requirements", "trust_tier",
    "entity_level_range", "is_level_typical", "common_ground",
    "capability_assessment_to_jsonld", "capability_assessment_from_jsonld",
    "capability_assessment_from_jsonld_string",
    "capability_framework_to_jsonld", "capability_framework_from_jsonld",
    "capability_framework_from_jsonld_string",
    # Constants
    "CAPABILITY_JSONLD_CONTEXT", "ENTITY_LEVEL_RANGES",
]


# ── JSON-LD Context ──────────────────────────────────────────────

CAPABILITY_JSONLD_CONTEXT = "https://web4.io/contexts/capability.jsonld"


# ── Capability Levels ────────────────────────────────────────────

class CapabilityLevel(IntEnum):
    """LCT capability levels per spec §2.1."""
    STUB = 0       # Placeholder reference, pending entity
    MINIMAL = 1    # Self-issued bootstrap, basic plugin identity
    BASIC = 2      # Operational plugins with relationships
    STANDARD = 3   # Autonomous agents with full tensors
    FULL = 4       # Society-issued with birth certificate
    HARDWARE = 5   # Hardware-bound identity (TPM/TrustZone)


class TrustTier(str):
    """Trust tier labels mapped from capability levels."""
    UNTRUSTED = "untrusted"
    LOW = "low"
    MODERATE = "moderate"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


# ── Trust Tier Mapping ───────────────────────────────────────────

# Spec §2.1: each level maps to a trust score range
_TRUST_TIERS: Dict[CapabilityLevel, Tuple[str, float, float]] = {
    CapabilityLevel.STUB:     (TrustTier.UNTRUSTED, 0.0, 0.0),
    CapabilityLevel.MINIMAL:  (TrustTier.LOW,       0.0, 0.2),
    CapabilityLevel.BASIC:    (TrustTier.MODERATE,   0.2, 0.4),
    CapabilityLevel.STANDARD: (TrustTier.MEDIUM,     0.4, 0.6),
    CapabilityLevel.FULL:     (TrustTier.HIGH,       0.6, 0.8),
    CapabilityLevel.HARDWARE: (TrustTier.MAXIMUM,    0.8, 1.0),
}


# ── Entity-Level Ranges ─────────────────────────────────────────

# Spec §3.3: typical capability level ranges per entity type
ENTITY_LEVEL_RANGES: Dict[EntityType, Tuple[int, int]] = {
    EntityType.HUMAN:          (4, 5),
    EntityType.AI:             (2, 4),
    EntityType.SOCIETY:        (4, 5),
    EntityType.ORGANIZATION:   (4, 4),
    EntityType.ROLE:           (1, 3),
    EntityType.TASK:           (1, 2),
    EntityType.RESOURCE:       (1, 3),
    EntityType.DEVICE:         (3, 5),
    EntityType.SERVICE:        (2, 4),
    EntityType.ORACLE:         (3, 4),
    EntityType.ACCUMULATOR:    (2, 3),
    EntityType.DICTIONARY:     (3, 4),
    EntityType.HYBRID:         (1, 5),
    EntityType.POLICY:         (3, 4),
    EntityType.INFRASTRUCTURE: (3, 5),
}


# ── Level Requirements ───────────────────────────────────────────

@dataclass(frozen=True)
class LevelRequirement:
    """Human-readable requirements for a capability level."""
    level: CapabilityLevel
    name: str
    description: str
    requirements: List[str]
    trust_range: Tuple[float, float]

    def to_jsonld(self) -> Dict[str, Any]:
        """Serialize to JSON-LD per lct-capability-levels spec."""
        return {
            "@context": [CAPABILITY_JSONLD_CONTEXT],
            "@type": "LevelRequirement",
            "level": int(self.level),
            "name": self.name,
            "description": self.description,
            "requirements": list(self.requirements),
            "trust_range": list(self.trust_range),
        }

    def to_jsonld_string(self, indent: int = 2) -> str:
        """Serialize to JSON-LD string."""
        return json.dumps(self.to_jsonld(), indent=indent)

    @classmethod
    def from_jsonld(cls, doc: Dict[str, Any]) -> LevelRequirement:
        """Deserialize from JSON-LD document."""
        tr = doc["trust_range"]
        return cls(
            level=CapabilityLevel(doc["level"]),
            name=doc["name"],
            description=doc["description"],
            requirements=doc["requirements"],
            trust_range=(tr[0], tr[1]),
        )

    @classmethod
    def from_jsonld_string(cls, s: str) -> LevelRequirement:
        """Deserialize from JSON-LD string."""
        return cls.from_jsonld(json.loads(s))


_LEVEL_REQUIREMENTS: Dict[CapabilityLevel, LevelRequirement] = {
    CapabilityLevel.STUB: LevelRequirement(
        level=CapabilityLevel.STUB,
        name="Stub",
        description="Placeholder reference, pending entity",
        requirements=["Valid lct_id", "Entity type (may be pending)"],
        trust_range=(0.0, 0.0),
    ),
    CapabilityLevel.MINIMAL: LevelRequirement(
        level=CapabilityLevel.MINIMAL,
        name="Minimal",
        description="Self-issued bootstrap, basic plugin identity",
        requirements=[
            "Valid lct_id",
            "Binding with public key",
            "MRH present (may be empty)",
            "T3 tensor with initial values",
            "V3 tensor with zero values",
        ],
        trust_range=(0.0, 0.2),
    ),
    CapabilityLevel.BASIC: LevelRequirement(
        level=CapabilityLevel.BASIC,
        name="Basic",
        description="Operational plugins with established relationships",
        requirements=[
            "All Level 1 requirements",
            "At least one MRH bound or paired relationship",
            "All T3 dimensions non-zero",
            "At least one policy capability",
        ],
        trust_range=(0.2, 0.4),
    ),
    CapabilityLevel.STANDARD: LevelRequirement(
        level=CapabilityLevel.STANDARD,
        name="Standard",
        description="Autonomous agents with full tensor support",
        requirements=[
            "All Level 2 requirements",
            "At least one witnessing relationship",
            "Non-zero V3 (ATP energy balance)",
        ],
        trust_range=(0.4, 0.6),
    ),
    CapabilityLevel.FULL: LevelRequirement(
        level=CapabilityLevel.FULL,
        name="Full",
        description="Society-issued identity with birth certificate",
        requirements=[
            "All Level 3 requirements",
            "Complete birth certificate",
            "At least 3 birth witnesses",
            "Permanent citizen role pairing",
        ],
        trust_range=(0.6, 0.8),
    ),
    CapabilityLevel.HARDWARE: LevelRequirement(
        level=CapabilityLevel.HARDWARE,
        name="Hardware",
        description="Hardware-bound identity (TPM/TrustZone)",
        requirements=[
            "All Level 4 requirements",
            "Hardware anchor in binding",
        ],
        trust_range=(0.8, 1.0),
    ),
}


# ── Assessment Helpers ───────────────────────────────────────────

def _has_binding(lct: LCT) -> bool:
    """Check if LCT has a valid binding with public key."""
    return lct.binding is not None and bool(lct.binding.public_key)


def _has_mrh_relationship(lct: LCT) -> bool:
    """Check if LCT has at least one bound or paired MRH relationship."""
    return bool(lct.mrh.bound) or bool(lct.mrh.paired)


def _has_nonzero_t3(lct: LCT) -> bool:
    """Check if all T3 dimensions are non-zero."""
    return (lct.t3.talent != 0.0
            and lct.t3.training != 0.0
            and lct.t3.temperament != 0.0)


def _has_policy_capability(lct: LCT) -> bool:
    """Check if LCT has at least one policy capability."""
    return bool(lct.policy.capabilities)


def _has_witnessing(lct: LCT) -> bool:
    """Check if LCT has at least one witnessing relationship."""
    return bool(lct.mrh.witnessing)


def _has_nonzero_v3(lct: LCT) -> bool:
    """Check if V3 has non-zero energy (any dimension)."""
    return (lct.v3.valuation != 0.0
            or lct.v3.veracity != 0.0
            or lct.v3.validity != 0.0)


def _has_birth_certificate(lct: LCT) -> bool:
    """Check if LCT has a complete birth certificate with ≥3 witnesses."""
    bc = lct.birth_certificate
    if bc is None:
        return False
    return (bool(bc.issuing_society)
            and bool(bc.citizen_role)
            and len(bc.birth_witnesses) >= 3)


def _has_permanent_citizen_pairing(lct: LCT) -> bool:
    """Check if LCT has a permanent citizen role pairing."""
    return any(
        p.permanent and "citizen" in p.lct_id
        for p in lct.mrh.paired
    )


def _has_hardware_anchor(lct: LCT) -> bool:
    """Check if LCT has a hardware anchor in its binding."""
    return lct.binding is not None and bool(lct.binding.hardware_anchor)


# ── Public API ───────────────────────────────────────────────────

def assess_level(lct: LCT) -> CapabilityLevel:
    """
    Determine an LCT's actual capability level from its components.

    Checks requirements top-down (Level 5 → 0) and returns the highest
    level whose requirements are fully met.

    Args:
        lct: The LCT to assess.

    Returns:
        The highest CapabilityLevel the LCT qualifies for.
    """
    # Level 5: Hardware — requires hardware anchor + all Level 4
    if (_has_hardware_anchor(lct)
            and _has_birth_certificate(lct)
            and _has_permanent_citizen_pairing(lct)
            and _has_witnessing(lct)
            and _has_nonzero_v3(lct)
            and _has_mrh_relationship(lct)
            and _has_nonzero_t3(lct)
            and _has_policy_capability(lct)
            and _has_binding(lct)):
        return CapabilityLevel.HARDWARE

    # Level 4: Full — requires birth certificate + permanent citizen pairing
    if (_has_birth_certificate(lct)
            and _has_permanent_citizen_pairing(lct)
            and _has_witnessing(lct)
            and _has_nonzero_v3(lct)
            and _has_mrh_relationship(lct)
            and _has_nonzero_t3(lct)
            and _has_policy_capability(lct)
            and _has_binding(lct)):
        return CapabilityLevel.FULL

    # Level 3: Standard — requires witnessing + non-zero V3
    if (_has_witnessing(lct)
            and _has_nonzero_v3(lct)
            and _has_mrh_relationship(lct)
            and _has_nonzero_t3(lct)
            and _has_policy_capability(lct)
            and _has_binding(lct)):
        return CapabilityLevel.STANDARD

    # Level 2: Basic — requires MRH relationship + non-zero T3 + capability
    if (_has_mrh_relationship(lct)
            and _has_nonzero_t3(lct)
            and _has_policy_capability(lct)
            and _has_binding(lct)):
        return CapabilityLevel.BASIC

    # Level 1: Minimal — requires binding
    if _has_binding(lct):
        return CapabilityLevel.MINIMAL

    # Level 0: Stub
    return CapabilityLevel.STUB


def validate_level(lct: LCT, claimed_level: int) -> Tuple[bool, List[str]]:
    """
    Verify that an LCT meets the requirements for a claimed capability level.

    Args:
        lct: The LCT to validate.
        claimed_level: The capability level being claimed (0-5).

    Returns:
        Tuple of (is_valid, list_of_missing_requirements).
        is_valid is True if the LCT meets all requirements for claimed_level.
    """
    level = CapabilityLevel(claimed_level)
    missing: List[str] = []

    if level >= CapabilityLevel.MINIMAL:
        if not _has_binding(lct):
            missing.append("Binding with public key required")

    if level >= CapabilityLevel.BASIC:
        if not _has_mrh_relationship(lct):
            missing.append("At least one MRH bound or paired relationship required")
        if not _has_nonzero_t3(lct):
            missing.append("All T3 dimensions must be non-zero")
        if not _has_policy_capability(lct):
            missing.append("At least one policy capability required")

    if level >= CapabilityLevel.STANDARD:
        if not _has_witnessing(lct):
            missing.append("At least one witnessing relationship required")
        if not _has_nonzero_v3(lct):
            missing.append("Non-zero V3 (energy balance) required")

    if level >= CapabilityLevel.FULL:
        if not _has_birth_certificate(lct):
            missing.append("Complete birth certificate with ≥3 witnesses required")
        if not _has_permanent_citizen_pairing(lct):
            missing.append("Permanent citizen role pairing required")

    if level >= CapabilityLevel.HARDWARE:
        if not _has_hardware_anchor(lct):
            missing.append("Hardware anchor in binding required")

    return (len(missing) == 0, missing)


def can_upgrade(lct: LCT, target_level: int) -> Tuple[bool, List[str]]:
    """
    Check if an LCT can upgrade to a target capability level.

    Upgrade constraints per spec §6.2:
    - Level 5 (HARDWARE) requires hardware binding from creation
    - Level 4 (FULL) requires society issuance
    - Lower levels can self-upgrade by meeting requirements
    - Downgrades are not permitted

    Args:
        lct: The LCT to check.
        target_level: The target capability level (0-5).

    Returns:
        Tuple of (can_upgrade, list_of_blockers).
    """
    target = CapabilityLevel(target_level)
    current = assess_level(lct)
    blockers: List[str] = []

    if target <= current:
        blockers.append(f"Already at level {current} (≥ target {target}); downgrades not permitted")
        return (False, blockers)

    # Check if target requirements are met
    valid, missing = validate_level(lct, target_level)
    blockers.extend(missing)

    # Special constraint: Level 5 requires hardware from creation
    if target == CapabilityLevel.HARDWARE and not _has_hardware_anchor(lct):
        if "Hardware anchor" not in " ".join(blockers):
            blockers.append("Level 5 requires hardware binding from creation (cannot be added post-hoc)")

    return (len(blockers) == 0, blockers)


def level_requirements(level: int) -> LevelRequirement:
    """
    Get human-readable requirements for a capability level.

    Args:
        level: Capability level (0-5).

    Returns:
        LevelRequirement with description and requirement list.
    """
    return _LEVEL_REQUIREMENTS[CapabilityLevel(level)]


def trust_tier(level: int) -> Tuple[str, float, float]:
    """
    Get the trust tier and score range for a capability level.

    Args:
        level: Capability level (0-5).

    Returns:
        Tuple of (tier_name, min_score, max_score).
    """
    return _TRUST_TIERS[CapabilityLevel(level)]


def entity_level_range(entity_type: EntityType) -> Tuple[int, int]:
    """
    Get the typical capability level range for an entity type.

    Args:
        entity_type: The entity type to look up.

    Returns:
        Tuple of (min_level, max_level).
    """
    return ENTITY_LEVEL_RANGES[entity_type]


def is_level_typical(entity_type: EntityType, level: int) -> bool:
    """
    Check if a capability level is typical for an entity type.

    Args:
        entity_type: The entity type.
        level: The capability level to check.

    Returns:
        True if level falls within the entity type's typical range.
    """
    min_lvl, max_lvl = ENTITY_LEVEL_RANGES[entity_type]
    return min_lvl <= level <= max_lvl


def common_ground(level_a: int, level_b: int) -> CapabilityLevel:
    """
    Compute minimum shared capability level for cross-domain interaction.

    Per spec §7.1, when LCTs from different domains interact, they
    establish common ground at the minimum of their capability levels.

    Args:
        level_a: First entity's capability level.
        level_b: Second entity's capability level.

    Returns:
        The minimum CapabilityLevel.
    """
    return CapabilityLevel(min(level_a, level_b))


@dataclass(frozen=True)
class CapabilityAssessment:
    """Result of assessing an LCT's capability level.

    Attributes:
        lct_id: The LCT that was assessed.
        assessed_level: The computed capability level (0-5).
        level_name: Human-readable level name.
        trust_tier: Trust tier label for this level.
        trust_range: Min/max trust scores for this tier.
        requirements_met: Whether all requirements for this level are met.
        missing_requirements: List of unmet requirement descriptions.
    """
    lct_id: str
    assessed_level: int
    level_name: str
    trust_tier: str
    trust_range: Tuple[float, float]
    requirements_met: bool
    missing_requirements: List[str]


def capability_assessment_to_jsonld(lct: LCT) -> Dict[str, Any]:
    """Serialize an LCT's capability assessment to JSON-LD."""
    level = assess_level(lct)
    tier_name, tier_min, tier_max = trust_tier(level)
    is_valid, missing = validate_level(lct, level)
    return {
        "@context": [CAPABILITY_JSONLD_CONTEXT],
        "@type": "CapabilityAssessment",
        "lct_id": lct.lct_id,
        "assessed_level": int(level),
        "level_name": CapabilityLevel(level).name.lower().capitalize(),
        "trust_tier": tier_name,
        "trust_range": [tier_min, tier_max],
        "requirements_met": is_valid,
        "missing_requirements": missing,
    }


def capability_assessment_from_jsonld(doc: Dict[str, Any]) -> CapabilityAssessment:
    """Deserialize a CapabilityAssessment from a JSON-LD document.

    Args:
        doc: A JSON-LD document with @type "CapabilityAssessment".

    Returns:
        CapabilityAssessment dataclass with the assessment fields.
    """
    tr = doc["trust_range"]
    return CapabilityAssessment(
        lct_id=doc["lct_id"],
        assessed_level=doc["assessed_level"],
        level_name=doc["level_name"],
        trust_tier=doc["trust_tier"],
        trust_range=(tr[0], tr[1]),
        requirements_met=doc["requirements_met"],
        missing_requirements=list(doc["missing_requirements"]),
    )


def capability_assessment_from_jsonld_string(s: str) -> CapabilityAssessment:
    """Deserialize a CapabilityAssessment from a JSON-LD string."""
    return capability_assessment_from_jsonld(json.loads(s))


def capability_framework_to_jsonld() -> Dict[str, Any]:
    """Serialize the full capability level framework to JSON-LD."""
    return {
        "@context": [CAPABILITY_JSONLD_CONTEXT],
        "@type": "CapabilityFramework",
        "levels": [req.to_jsonld() for req in _LEVEL_REQUIREMENTS.values()],
    }


def capability_framework_from_jsonld(doc: Dict[str, Any]) -> List[LevelRequirement]:
    """Deserialize a CapabilityFramework from a JSON-LD document.

    Args:
        doc: A JSON-LD document with @type "CapabilityFramework".

    Returns:
        List of LevelRequirement objects, one per capability level.
    """
    return [LevelRequirement.from_jsonld(level_doc) for level_doc in doc["levels"]]


def capability_framework_from_jsonld_string(s: str) -> List[LevelRequirement]:
    """Deserialize a CapabilityFramework from a JSON-LD string."""
    return capability_framework_from_jsonld(json.loads(s))
