#!/usr/bin/env python3
"""
Web4 Coherence Bridge
======================

Resolves the cross-spec divergences found by cross_spec_coherence_analysis.py:

1. **LCT Format Dispatcher**: Detects and routes between Format A/B/C
2. **Permission Bridge**: Maps between LUPS, R6, SAL, Hardbound, Reputation systems
3. **Tensor Normalizer**: Bridges legacy 6-dim to canonical 3-dim T3/V3
4. **Unified Constants**: Single source of truth for ATP/trust parameters

From coherence analysis:
- 3 incompatible LCT ID formats → unified dispatcher with canonical form
- 5 isolated permission systems → bridging adapters with common interface
- 2 files using legacy 6-dim tensors → normalization with semantic mapping
- Software trust ceiling 0.85 vs 0.7 → context-dependent resolution

This module DOES NOT modify existing implementations. Instead it provides
adapter interfaces that existing code can opt into incrementally.

Session: Legion Autonomous 2026-02-26
"""

import hashlib
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse, parse_qs


# ============================================================================
# SECTION 1: UNIFIED CONSTANTS
# ============================================================================

class Web4Constants:
    """
    Single source of truth for all cross-spec constants.

    Resolves divergence: each constant documents its source and reason.
    """

    # ---- ATP Defaults ----
    DEFAULT_ATP_BUDGET = 100.0       # Consistent across mcp_web4, team.py, member.py
    TRANSFER_FEE_RATE = 0.05         # 5% per transfer (ai_agent_accountability)
    BRIDGE_FEE_FORWARD = 0.01        # 1% forward bridge crossing
    BRIDGE_FEE_RETURN = 0.005        # 0.5% return bridge crossing
    QUERY_FEE_RATE = 0.10            # 10% trust query fee (privacy governance)

    # ---- Trust Ceilings ----
    # Resolution: both 0.85 and 0.7 are valid, context-dependent
    TRUST_CEILING_HARDWARE = 1.0     # TPM2 bound (hardware_entity.py)
    TRUST_CEILING_SOFTWARE = 0.85    # Verified software (avp_transport.py)
    TRUST_CEILING_FALLBACK = 0.7     # Unverified software (Hardbound dev mode)

    # ---- Quality / Convergence ----
    # C = 0.7 is intentional convergence across SAGE, Web4, Synchronism
    QUALITY_THRESHOLD = 0.7          # ATP settlement gate
    TRUST_HIGH_BOUNDARY = 0.7        # Medium→High trust transition
    CONSCIOUSNESS_THRESHOLD = 0.7    # SAGE C threshold (from Thor S44)
    TRUST_LOW_BOUNDARY = 0.3         # Trust degradation alert

    # ---- Decay Rates (context-dependent, not contradictory) ----
    DECAY_FEDERATION_HEARTBEAT = 0.1       # 10% per heartbeat period
    DECAY_TRUST_INACTIVITY = -0.001        # Per month, training dimension
    DECAY_CHAIN_PER_HOP = 0.5              # 50% multiplicative per hop

    # ---- Tensor Weights (spec allows variation; these are defaults) ----
    T3_EQUAL_WEIGHTS = {"talent": 1/3, "training": 1/3, "temperament": 1/3}
    T3_TRACKER_WEIGHTS = {"talent": 0.30, "training": 0.50, "temperament": 0.20}
    T3_REPUTATION_WEIGHTS = {"talent": 0.40, "training": 0.40, "temperament": 0.20}


# ============================================================================
# SECTION 2: LCT FORMAT DISPATCHER
# ============================================================================

class LCTFormat(Enum):
    """The three LCT ID formats found in the codebase."""
    FORMAT_A = "agent_identity"    # lct:web4:agent:{lineage}@{context}#{task}
    FORMAT_B = "uri_scheme"        # lct://{component}:{instance}:{role}@{network}
    FORMAT_C = "ad_hoc"            # lct:web4:{type}:{id}
    UNKNOWN = "unknown"


@dataclass
class ParsedLCT:
    """Unified parsed representation of any LCT format."""
    raw: str
    format: LCTFormat

    # Common fields (populated by whichever format is detected)
    entity_type: str = ""         # human, ai, agent, society, etc.
    identifier: str = ""          # Primary identifier
    platform: str = ""            # Platform/context/network
    task_or_role: str = ""        # Task (Format A) or Role (Format B)

    # Format A specific
    lineage: str = ""             # Creator chain (Format A)

    # Format B specific
    component: str = ""           # Component type (Format B)
    instance: str = ""            # Instance name (Format B)
    network: str = ""             # Network (Format B)
    params: Dict[str, str] = field(default_factory=dict)

    @property
    def canonical_type(self) -> str:
        """Map to canonical 15+1 entity type."""
        type_map = {
            "human": "HUMAN", "user": "HUMAN",
            "ai": "AI", "agent": "AI", "ai_agent": "AI",
            "society": "SOCIETY", "team": "SOCIETY",
            "org": "ORGANIZATION", "organization": "ORGANIZATION",
            "role": "ROLE",
            "task": "TASK",
            "resource": "RESOURCE",
            "device": "DEVICE", "hw": "DEVICE", "hardware": "DEVICE",
            "service": "SERVICE",
            "oracle": "ORACLE",
            "accumulator": "ACCUMULATOR",
            "dictionary": "DICTIONARY", "dict": "DICTIONARY",
            "hybrid": "HYBRID",
            "policy": "POLICY",
            "infrastructure": "INFRASTRUCTURE", "infra": "INFRASTRUCTURE",
            # Format B components
            "sage": "AI",
            "web4-agent": "AI",
            "act-validator": "SERVICE",
            "act-society": "SOCIETY",
            "memory": "RESOURCE",
            "portal": "SERVICE",
            "sync": "SERVICE",
        }
        return type_map.get(self.entity_type.lower(), "UNKNOWN")


# Regex for Format A: lct:web4:agent:{lineage}@{context}#{task}
_FORMAT_A_RE = re.compile(
    r'^lct:web4:agent:(?P<lineage>[^@]+)@(?P<context>[^#]+)#(?P<task>.+)$'
)


def parse_lct(lct_str: str) -> ParsedLCT:
    """
    Universal LCT parser — detects format and extracts components.

    Handles all three formats found in the codebase:
    - Format A: lct:web4:agent:{lineage}@{context}#{task}
    - Format B: lct://{component}:{instance}:{role}@{network}?{params}
    - Format C: lct:web4:{type}:{id}
    """
    if not lct_str:
        return ParsedLCT(raw=lct_str, format=LCTFormat.UNKNOWN)

    # Format B: URI scheme
    if lct_str.startswith("lct://"):
        return _parse_format_b(lct_str)

    # Format A: Agent identity with @ and #
    match = _FORMAT_A_RE.match(lct_str)
    if match:
        return _parse_format_a(lct_str, match)

    # Format C: Ad-hoc colon-separated
    if lct_str.startswith("lct:") or lct_str.startswith("web4:"):
        return _parse_format_c(lct_str)

    return ParsedLCT(raw=lct_str, format=LCTFormat.UNKNOWN)


def _parse_format_a(raw: str, match: re.Match) -> ParsedLCT:
    """Parse Format A: lct:web4:agent:{lineage}@{context}#{task}"""
    lineage = match.group("lineage")
    context = match.group("context")
    task = match.group("task")

    # Extract root creator from lineage
    root_creator = lineage.split(".")[0]
    # Handle org: prefix
    if root_creator.startswith("org:"):
        root_creator = root_creator[4:]

    return ParsedLCT(
        raw=raw,
        format=LCTFormat.FORMAT_A,
        entity_type="agent",
        identifier=lineage,
        platform=context,
        task_or_role=task,
        lineage=lineage,
    )


def _parse_format_b(raw: str) -> ParsedLCT:
    """Parse Format B: lct://{component}:{instance}:{role}@{network}?{params}"""
    # Replace lct:// with http:// for urlparse compatibility
    http_form = raw.replace("lct://", "http://", 1)
    parsed = urlparse(http_form)

    # Authority: component:instance:role@network
    authority = parsed.netloc  # e.g. "sage:thinker:expert_42@testnet"
    query_params = {}
    if parsed.query:
        query_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    fragment = parsed.fragment

    # Split authority on @
    if "@" in authority:
        user_part, network = authority.rsplit("@", 1)
    else:
        user_part = authority
        network = ""

    # Split user part on :
    parts = user_part.split(":")
    component = parts[0] if len(parts) >= 1 else ""
    instance = parts[1] if len(parts) >= 2 else ""
    role = parts[2] if len(parts) >= 3 else ""

    return ParsedLCT(
        raw=raw,
        format=LCTFormat.FORMAT_B,
        entity_type=component,
        identifier=instance or component,
        platform=network,
        task_or_role=role,
        component=component,
        instance=instance,
        network=network,
        params=query_params,
    )


def _parse_format_c(raw: str) -> ParsedLCT:
    """Parse Format C: lct:web4:{type}:{id} or web4:{type}:{id}"""
    parts = raw.split(":")

    # Normalize: skip lct and web4 prefixes
    # lct:web4:type:id → [lct, web4, type, id]
    # web4:type:id → [web4, type, id]
    if parts[0] == "lct" and len(parts) >= 4 and parts[1] == "web4":
        entity_type = parts[2]
        identifier = ":".join(parts[3:])
    elif parts[0] == "web4" and len(parts) >= 3:
        entity_type = parts[1]
        identifier = ":".join(parts[2:])
    elif parts[0] == "lct" and len(parts) >= 3:
        entity_type = parts[1]
        identifier = ":".join(parts[2:])
    else:
        entity_type = parts[0] if parts else ""
        identifier = ":".join(parts[1:]) if len(parts) > 1 else ""

    return ParsedLCT(
        raw=raw,
        format=LCTFormat.FORMAT_C,
        entity_type=entity_type,
        identifier=identifier,
    )


def to_canonical_lct(parsed: ParsedLCT) -> str:
    """Convert any parsed LCT to canonical Format A (if applicable) or Format C."""
    if parsed.format == LCTFormat.FORMAT_A:
        return parsed.raw  # Already canonical

    # Convert Format B to canonical
    if parsed.format == LCTFormat.FORMAT_B:
        lineage = parsed.instance or parsed.component
        context = parsed.network or "local"
        task = parsed.task_or_role or "perception"
        return f"lct:web4:agent:{lineage}@{context}#{task}"

    # Format C stays as Format C (no task/platform info to canonicalize)
    return parsed.raw


# ============================================================================
# SECTION 3: PERMISSION BRIDGE
# ============================================================================

class PermissionBridge:
    """
    Bridges between the 5 permission systems.

    Maps any permission check to the appropriate system based on context.

    Mapping logic:
    - LUPS task types ↔ R6 AuthRoles ↔ SAL Roles ↔ Hardbound Roles ↔ Reputation Levels
    """

    # LUPS task types → R6 AuthRole mapping
    LUPS_TO_R6: Dict[str, str] = {
        "perception": "viewer",
        "planning": "viewer",
        "planning.strategic": "reviewer",
        "execution.safe": "developer",
        "execution.code": "developer",
        "delegation.federation": "admin",
        "cognition": "developer",
        "cognition.sage": "admin",
        "admin.readonly": "reviewer",
        "admin.full": "admin",
    }

    # LUPS task types → SAL role mapping
    LUPS_TO_SAL: Dict[str, str] = {
        "perception": "citizen",
        "planning": "citizen",
        "planning.strategic": "authority",
        "execution.safe": "citizen",
        "execution.code": "authority",
        "delegation.federation": "authority",
        "cognition": "witness",
        "cognition.sage": "oracle",
        "admin.readonly": "auditor",
        "admin.full": "authority",
    }

    # LUPS task types → Hardbound role mapping
    LUPS_TO_HARDBOUND: Dict[str, str] = {
        "perception": "observer",
        "planning": "member",
        "planning.strategic": "reviewer",
        "execution.safe": "member",
        "execution.code": "developer",
        "delegation.federation": "admin",
        "cognition": "developer",
        "cognition.sage": "admin",
        "admin.readonly": "reviewer",
        "admin.full": "admin",
    }

    # LUPS task types → Reputation level mapping (minimum T3 composite)
    LUPS_TO_REPUTATION: Dict[str, Tuple[str, float]] = {
        "perception": ("novice", 0.0),
        "planning": ("novice", 0.0),
        "planning.strategic": ("developing", 0.3),
        "execution.safe": ("developing", 0.3),
        "execution.code": ("trusted", 0.5),
        "delegation.federation": ("expert", 0.7),
        "cognition": ("trusted", 0.5),
        "cognition.sage": ("expert", 0.7),
        "admin.readonly": ("developing", 0.3),
        "admin.full": ("master", 0.9),
    }

    # R6 AuthRole → LUPS task types (reverse)
    R6_TO_LUPS: Dict[str, List[str]] = {
        "viewer": ["perception", "planning"],
        "reviewer": ["planning.strategic", "admin.readonly"],
        "developer": ["execution.safe", "execution.code", "cognition"],
        "admin": ["delegation.federation", "cognition.sage", "admin.full"],
    }

    # LUPS permissions → Reputation permissions
    LUPS_TO_REPUTATION_PERMS: Dict[str, str] = {
        "atp:read": "read:atp_balance",
        "atp:write": "write:atp_transfer",
        "exec:safe": "execute:basic_tests",
        "exec:code": "execute:integration_tests",
        "federation:delegate": "grant:delegation:*",
        "admin:read": "read:admin_panel",
        "admin:full": "admin:org:*",
        "network:http": "execute:network_http",
        "storage:read": "read:shared_docs",
        "storage:write": "write:code:own",
    }

    def map_lups_to_r6(self, task_type: str) -> Optional[str]:
        """Get R6 AuthRole for a LUPS task type."""
        return self.LUPS_TO_R6.get(task_type)

    def map_lups_to_sal(self, task_type: str) -> Optional[str]:
        """Get SAL role for a LUPS task type."""
        return self.LUPS_TO_SAL.get(task_type)

    def map_lups_to_hardbound(self, task_type: str) -> Optional[str]:
        """Get Hardbound role for a LUPS task type."""
        return self.LUPS_TO_HARDBOUND.get(task_type)

    def map_lups_to_reputation(self, task_type: str) -> Optional[Tuple[str, float]]:
        """Get minimum reputation level + T3 threshold for a LUPS task type."""
        return self.LUPS_TO_REPUTATION.get(task_type)

    def map_r6_to_lups_tasks(self, r6_role: str) -> List[str]:
        """Get all LUPS task types available to an R6 role."""
        return self.R6_TO_LUPS.get(r6_role, [])

    def translate_permission(self, lups_perm: str) -> Optional[str]:
        """Translate a LUPS permission to reputation-system format."""
        return self.LUPS_TO_REPUTATION_PERMS.get(lups_perm)

    def check_reputation_eligible(self, task_type: str, t3_composite: float) -> Tuple[bool, str]:
        """Check if an entity's T3 composite meets the threshold for a task type."""
        mapping = self.LUPS_TO_REPUTATION.get(task_type)
        if not mapping:
            return False, f"Unknown task type: {task_type}"
        level, threshold = mapping
        if t3_composite >= threshold:
            return True, f"T3 {t3_composite:.2f} >= {threshold} ({level})"
        return False, f"T3 {t3_composite:.2f} < {threshold} ({level} required)"

    def get_all_mappings(self, task_type: str) -> Dict[str, Any]:
        """Get complete cross-system mapping for a task type."""
        rep = self.LUPS_TO_REPUTATION.get(task_type)
        return {
            "lups_task": task_type,
            "r6_role": self.LUPS_TO_R6.get(task_type),
            "sal_role": self.LUPS_TO_SAL.get(task_type),
            "hardbound_role": self.LUPS_TO_HARDBOUND.get(task_type),
            "reputation_level": rep[0] if rep else None,
            "t3_threshold": rep[1] if rep else None,
        }


# ============================================================================
# SECTION 4: TENSOR NORMALIZER
# ============================================================================

@dataclass
class NormalizedT3:
    """Canonical 3-dim T3 tensor."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0

    def weighted_composite(self, weights: Dict[str, float] = None) -> float:
        if not weights:
            weights = Web4Constants.T3_EQUAL_WEIGHTS
        return (
            self.talent * weights.get("talent", 1/3) +
            self.training * weights.get("training", 1/3) +
            self.temperament * weights.get("temperament", 1/3)
        )


class TensorNormalizer:
    """
    Bridges legacy 6-dim tensors to canonical 3-dim T3.

    Mapping rationale (from cross_implementation_integration.py:443-450):
    - technical_competence → talent (both measure capability)
    - temporal_consistency → training (both measure learned patterns)
    - social_reliability → temperament (both measure behavioral stability)

    Additional legacy dims folded in:
    - witness_count → boosts all dims (more witnesses = more data)
    - lineage_depth → boosts training (deeper lineage = more history)
    - context_alignment → boosts temperament (aligned = reliable)
    """

    @staticmethod
    def from_legacy_6dim(
        technical_competence: float = 0.5,
        social_reliability: float = 0.5,
        temporal_consistency: float = 0.5,
        witness_count: float = 0.5,
        lineage_depth: float = 0.5,
        context_alignment: float = 0.5,
    ) -> NormalizedT3:
        """Convert legacy 6-dim tensor to canonical 3-dim."""
        # Primary mapping
        talent = technical_competence
        training = temporal_consistency
        temperament = social_reliability

        # Secondary influence from auxiliary dims
        witness_boost = (witness_count - 0.5) * 0.1  # ±0.05 max
        lineage_boost = (lineage_depth - 0.5) * 0.1
        context_boost = (context_alignment - 0.5) * 0.1

        # Apply boosts (witness affects all, lineage→training, context→temperament)
        talent = max(0.0, min(1.0, talent + witness_boost))
        training = max(0.0, min(1.0, training + witness_boost + lineage_boost))
        temperament = max(0.0, min(1.0, temperament + witness_boost + context_boost))

        return NormalizedT3(
            talent=round(talent, 6),
            training=round(training, 6),
            temperament=round(temperament, 6),
        )

    @staticmethod
    def from_mixed_dims(dims: Dict[str, float]) -> NormalizedT3:
        """
        Normalize arbitrary dimension dict to canonical 3-dim.

        Handles attack_track_fo.py mixed dims:
        talent, trajectory, trust, tenacity, tact, temperament
        """
        # Direct mapping for canonical dims
        talent = dims.get("talent", 0.5)
        training = dims.get("training", 0.5)
        temperament = dims.get("temperament", 0.5)

        # Map non-standard dims
        if "technical_competence" in dims:
            talent = dims["technical_competence"]
        if "temporal_consistency" in dims:
            training = dims["temporal_consistency"]
        if "social_reliability" in dims:
            temperament = dims["social_reliability"]

        # Fold secondary non-standard dims as modest influence
        secondary = {}
        for key in ["trajectory", "trust", "tenacity", "tact",
                     "witness_count", "lineage_depth", "context_alignment"]:
            if key in dims:
                secondary[key] = dims[key]

        if secondary:
            avg_secondary = sum(secondary.values()) / len(secondary)
            boost = (avg_secondary - 0.5) * 0.05  # Modest influence
            talent = max(0.0, min(1.0, talent + boost))
            training = max(0.0, min(1.0, training + boost))
            temperament = max(0.0, min(1.0, temperament + boost))

        return NormalizedT3(
            talent=round(talent, 6),
            training=round(training, 6),
            temperament=round(temperament, 6),
        )


# ============================================================================
# SECTION 5: ENTITY TYPE UNIFIER
# ============================================================================

class CanonicalEntityType(Enum):
    """
    Unified entity type enum — union of all 5 enum definitions.

    16 types total (15 canonical + TEAM from lct_identity.py).
    """
    HUMAN = "human"
    AI = "ai"
    SOCIETY = "society"
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
    POLICY = "policy"
    INFRASTRUCTURE = "infrastructure"
    TEAM = "team"  # From lct_identity.py (maps to SOCIETY in most contexts)


# Aliases for cross-enum compatibility
ENTITY_TYPE_ALIASES: Dict[str, CanonicalEntityType] = {
    # Direct matches
    "human": CanonicalEntityType.HUMAN,
    "ai": CanonicalEntityType.AI,
    "ai_agent": CanonicalEntityType.AI,  # lct_identity.py uses AI_AGENT
    "society": CanonicalEntityType.SOCIETY,
    "organization": CanonicalEntityType.ORGANIZATION,
    "org": CanonicalEntityType.ORGANIZATION,
    "role": CanonicalEntityType.ROLE,
    "task": CanonicalEntityType.TASK,
    "resource": CanonicalEntityType.RESOURCE,
    "device": CanonicalEntityType.DEVICE,
    "hw": CanonicalEntityType.DEVICE,
    "hardware": CanonicalEntityType.DEVICE,
    "service": CanonicalEntityType.SERVICE,
    "oracle": CanonicalEntityType.ORACLE,
    "accumulator": CanonicalEntityType.ACCUMULATOR,
    "dictionary": CanonicalEntityType.DICTIONARY,
    "dict": CanonicalEntityType.DICTIONARY,
    "hybrid": CanonicalEntityType.HYBRID,
    "policy": CanonicalEntityType.POLICY,
    "infrastructure": CanonicalEntityType.INFRASTRUCTURE,
    "infra": CanonicalEntityType.INFRASTRUCTURE,
    "team": CanonicalEntityType.TEAM,
    # Format B components
    "sage": CanonicalEntityType.AI,
    "web4-agent": CanonicalEntityType.AI,
    "act-validator": CanonicalEntityType.SERVICE,
    "act-society": CanonicalEntityType.SOCIETY,
    "memory": CanonicalEntityType.RESOURCE,
    "portal": CanonicalEntityType.SERVICE,
    "sync": CanonicalEntityType.SERVICE,
    # Format C ad-hoc types
    "agent": CanonicalEntityType.AI,
    "user": CanonicalEntityType.HUMAN,
    "admin": CanonicalEntityType.ROLE,
    "witness": CanonicalEntityType.ROLE,
    "citizen": CanonicalEntityType.ROLE,
    "expert": CanonicalEntityType.ROLE,
    "root": CanonicalEntityType.ROLE,
    "test": CanonicalEntityType.AI,  # Test entities default to AI
    "mcp": CanonicalEntityType.SERVICE,
    "plugin": CanonicalEntityType.SERVICE,
    "session": CanonicalEntityType.RESOURCE,
    "federation": CanonicalEntityType.SOCIETY,
    "sprout": CanonicalEntityType.DEVICE,
    "audit": CanonicalEntityType.RESOURCE,
}


def resolve_entity_type(type_str: str) -> CanonicalEntityType:
    """Resolve any entity type string to canonical type."""
    normalized = type_str.lower().strip()
    if normalized in ENTITY_TYPE_ALIASES:
        return ENTITY_TYPE_ALIASES[normalized]
    # Try enum direct match
    try:
        return CanonicalEntityType(normalized)
    except ValueError:
        return CanonicalEntityType.AI  # Default: treat unknown as AI entity


# ============================================================================
# SECTION 6: TRUST CEILING RESOLVER
# ============================================================================

class TrustCeilingContext(Enum):
    """Context determines which trust ceiling applies."""
    TPM2_HARDWARE = "tpm2"           # Hardware-bound identity → 1.0
    VERIFIED_SOFTWARE = "verified"    # Software with attestation chain → 0.85
    UNVERIFIED_SOFTWARE = "fallback"  # Dev mode / no attestation → 0.7
    FAILURE = "failure"               # Verification failed → 0.0


def resolve_trust_ceiling(context: TrustCeilingContext) -> float:
    """
    Resolve the software trust ceiling contradiction.

    The 0.85 vs 0.7 is NOT a contradiction — they're different contexts:
    - 0.85: Software with verified attestation chain (AVP transport)
    - 0.7: Software without attestation (Hardbound dev mode)
    """
    mapping = {
        TrustCeilingContext.TPM2_HARDWARE: Web4Constants.TRUST_CEILING_HARDWARE,
        TrustCeilingContext.VERIFIED_SOFTWARE: Web4Constants.TRUST_CEILING_SOFTWARE,
        TrustCeilingContext.UNVERIFIED_SOFTWARE: Web4Constants.TRUST_CEILING_FALLBACK,
        TrustCeilingContext.FAILURE: 0.0,
    }
    return mapping.get(context, 0.0)


# ============================================================================
# SECTION 7: TEST SUITE
# ============================================================================

def run_tests():
    """Validate all coherence bridge components."""
    checks_passed = 0
    checks_failed = 0
    total_checks = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal checks_passed, checks_failed, total_checks
        total_checks += 1
        if condition:
            checks_passed += 1
        else:
            checks_failed += 1
            print(f"  FAIL: {name}: {detail}")

    # ====================================================================
    # T1: LCT Format Detection
    # ====================================================================
    print("T1: LCT format detection")

    # Format A
    p = parse_lct("lct:web4:agent:alice@Thor#perception")
    check("T1.1 Format A detected", p.format == LCTFormat.FORMAT_A)
    check("T1.2 Format A lineage", p.lineage == "alice")
    check("T1.3 Format A platform", p.platform == "Thor")
    check("T1.4 Format A task", p.task_or_role == "perception")
    check("T1.5 Format A entity type", p.entity_type == "agent")

    # Format A with hierarchical lineage
    p2 = parse_lct("lct:web4:agent:alice.assistant1.researcher@Sprout#planning.strategic")
    check("T1.6 Hierarchical lineage", p2.lineage == "alice.assistant1.researcher")
    check("T1.7 Platform Sprout", p2.platform == "Sprout")
    check("T1.8 Strategic planning task", p2.task_or_role == "planning.strategic")

    # Format A with org prefix
    p3 = parse_lct("lct:web4:agent:org:anthropic.safety@cloud:aws-east-1#admin.readonly")
    check("T1.9 Org lineage", p3.lineage == "org:anthropic.safety")
    check("T1.10 Cloud context", p3.platform == "cloud:aws-east-1")
    check("T1.11 Admin readonly task", p3.task_or_role == "admin.readonly")

    # Format B
    p4 = parse_lct("lct://sage:thinker:expert_42@testnet")
    check("T1.12 Format B detected", p4.format == LCTFormat.FORMAT_B)
    check("T1.13 Format B component", p4.component == "sage")
    check("T1.14 Format B instance", p4.instance == "thinker")
    check("T1.15 Format B role", p4.task_or_role == "expert_42")
    check("T1.16 Format B network", p4.network == "testnet")

    # Format B with params
    p5 = parse_lct("lct://agent:beta@mainnet?capabilities=text-gen&trust_threshold=0.75")
    check("T1.17 Format B with params", p5.format == LCTFormat.FORMAT_B)
    check("T1.18 Params parsed", p5.params.get("capabilities") == "text-gen")
    check("T1.19 Trust threshold param", p5.params.get("trust_threshold") == "0.75")

    # Format C
    p6 = parse_lct("lct:web4:ai:claude")
    check("T1.20 Format C detected", p6.format == LCTFormat.FORMAT_C)
    check("T1.21 Format C type", p6.entity_type == "ai")
    check("T1.22 Format C id", p6.identifier == "claude")

    # Format C with web4: prefix (no lct:)
    p7 = parse_lct("web4:soft:admin:12345")
    check("T1.23 web4: prefix Format C", p7.format == LCTFormat.FORMAT_C)
    check("T1.24 Type = soft", p7.entity_type == "soft")

    # Format C society
    p8 = parse_lct("lct:web4:society:alpha-corp")
    check("T1.25 Society format C", p8.entity_type == "society")
    check("T1.26 Society id", p8.identifier == "alpha-corp")

    # Empty/unknown
    p9 = parse_lct("")
    check("T1.27 Empty string = UNKNOWN", p9.format == LCTFormat.UNKNOWN)

    # ====================================================================
    # T2: Canonical Type Mapping
    # ====================================================================
    print("T2: Canonical entity type mapping")

    p_agent = parse_lct("lct:web4:agent:alice@Thor#perception")
    check("T2.1 agent → AI", p_agent.canonical_type == "AI")

    p_human = parse_lct("lct:web4:human:bob")
    check("T2.2 human → HUMAN", p_human.canonical_type == "HUMAN")

    p_sage = parse_lct("lct://sage:thinker@testnet")
    check("T2.3 sage → AI", p_sage.canonical_type == "AI")

    p_society = parse_lct("lct:web4:society:alpha")
    check("T2.4 society → SOCIETY", p_society.canonical_type == "SOCIETY")

    p_device = parse_lct("lct:web4:device:hw01")
    check("T2.5 device → DEVICE", p_device.canonical_type == "DEVICE")

    p_hw = parse_lct("lct:web4:hw:sensor01")
    check("T2.6 hw → DEVICE", p_hw.canonical_type == "DEVICE")

    p_dict = parse_lct("lct:web4:dictionary:en-fr")
    check("T2.7 dictionary → DICTIONARY", p_dict.canonical_type == "DICTIONARY")

    # ====================================================================
    # T3: Canonical LCT Conversion
    # ====================================================================
    print("T3: Canonical LCT conversion")

    p_a = parse_lct("lct:web4:agent:alice@Thor#perception")
    check("T3.1 Format A stays as-is",
          to_canonical_lct(p_a) == "lct:web4:agent:alice@Thor#perception")

    p_b = parse_lct("lct://sage:thinker:coordinator@mainnet")
    canonical_b = to_canonical_lct(p_b)
    check("T3.2 Format B converts to Format A",
          canonical_b == "lct:web4:agent:thinker@mainnet#coordinator")

    p_c = parse_lct("lct:web4:ai:claude")
    check("T3.3 Format C stays as-is (no task info)",
          to_canonical_lct(p_c) == "lct:web4:ai:claude")

    # ====================================================================
    # T4: Permission Bridge
    # ====================================================================
    print("T4: Permission bridge")
    bridge = PermissionBridge()

    # LUPS → R6
    check("T4.1 perception → viewer",
          bridge.map_lups_to_r6("perception") == "viewer")
    check("T4.2 execution.code → developer",
          bridge.map_lups_to_r6("execution.code") == "developer")
    check("T4.3 delegation.federation → admin",
          bridge.map_lups_to_r6("delegation.federation") == "admin")
    check("T4.4 admin.full → admin",
          bridge.map_lups_to_r6("admin.full") == "admin")

    # LUPS → SAL
    check("T4.5 perception → citizen",
          bridge.map_lups_to_sal("perception") == "citizen")
    check("T4.6 cognition.sage → oracle",
          bridge.map_lups_to_sal("cognition.sage") == "oracle")
    check("T4.7 admin.readonly → auditor",
          bridge.map_lups_to_sal("admin.readonly") == "auditor")

    # LUPS → Hardbound
    check("T4.8 perception → observer",
          bridge.map_lups_to_hardbound("perception") == "observer")
    check("T4.9 execution.code → developer",
          bridge.map_lups_to_hardbound("execution.code") == "developer")

    # LUPS → Reputation
    level, threshold = bridge.map_lups_to_reputation("admin.full")
    check("T4.10 admin.full → master (T3 >= 0.9)",
          level == "master" and threshold == 0.9)
    level2, threshold2 = bridge.map_lups_to_reputation("perception")
    check("T4.11 perception → novice (T3 >= 0.0)",
          level2 == "novice" and threshold2 == 0.0)

    # R6 → LUPS (reverse)
    tasks = bridge.map_r6_to_lups_tasks("admin")
    check("T4.12 R6 admin → 3 LUPS tasks",
          len(tasks) == 3 and "admin.full" in tasks)
    viewer_tasks = bridge.map_r6_to_lups_tasks("viewer")
    check("T4.13 R6 viewer → 2 LUPS tasks",
          len(viewer_tasks) == 2 and "perception" in viewer_tasks)

    # Reputation eligibility check
    ok, msg = bridge.check_reputation_eligible("admin.full", 0.95)
    check("T4.14 T3=0.95 eligible for admin.full", ok)
    ok2, msg2 = bridge.check_reputation_eligible("admin.full", 0.5)
    check("T4.15 T3=0.5 NOT eligible for admin.full", not ok2)
    ok3, msg3 = bridge.check_reputation_eligible("perception", 0.0)
    check("T4.16 T3=0.0 eligible for perception", ok3)

    # Permission translation
    check("T4.17 atp:read → read:atp_balance",
          bridge.translate_permission("atp:read") == "read:atp_balance")
    check("T4.18 admin:full → admin:org:*",
          bridge.translate_permission("admin:full") == "admin:org:*")

    # Full mapping
    mapping = bridge.get_all_mappings("delegation.federation")
    check("T4.19 Full mapping has all fields",
          all(k in mapping for k in ["lups_task", "r6_role", "sal_role",
                                      "hardbound_role", "reputation_level", "t3_threshold"]))
    check("T4.20 Federation mapping correct",
          mapping["r6_role"] == "admin" and mapping["sal_role"] == "authority"
          and mapping["hardbound_role"] == "admin" and mapping["reputation_level"] == "expert")

    # All 10 LUPS tasks have mappings
    all_mapped = all(
        bridge.map_lups_to_r6(t) is not None
        and bridge.map_lups_to_sal(t) is not None
        and bridge.map_lups_to_hardbound(t) is not None
        and bridge.map_lups_to_reputation(t) is not None
        for t in ["perception", "planning", "planning.strategic",
                   "execution.safe", "execution.code", "delegation.federation",
                   "cognition", "cognition.sage", "admin.readonly", "admin.full"]
    )
    check("T4.21 All 10 LUPS tasks mapped to all 4 systems", all_mapped)

    # ====================================================================
    # T5: Tensor Normalizer
    # ====================================================================
    print("T5: Tensor normalizer")

    # Legacy 6-dim → canonical 3-dim
    t3 = TensorNormalizer.from_legacy_6dim(
        technical_competence=0.7,
        social_reliability=0.6,
        temporal_consistency=0.65,
        witness_count=0.5,
        lineage_depth=0.5,
        context_alignment=0.5,
    )
    check("T5.1 Talent from technical_competence",
          t3.talent == 0.7, f"talent={t3.talent}")
    check("T5.2 Training from temporal_consistency",
          t3.training == 0.65, f"training={t3.training}")
    check("T5.3 Temperament from social_reliability",
          t3.temperament == 0.6, f"temperament={t3.temperament}")

    # With boost from high witness count
    t3_boosted = TensorNormalizer.from_legacy_6dim(
        technical_competence=0.7,
        social_reliability=0.6,
        temporal_consistency=0.65,
        witness_count=0.9,  # High → boost
        lineage_depth=0.8,  # High → boost training
        context_alignment=0.8,  # High → boost temperament
    )
    check("T5.4 Witness boost increases talent",
          t3_boosted.talent > 0.7)
    check("T5.5 Lineage + witness boost increases training",
          t3_boosted.training > 0.65)
    check("T5.6 Context + witness boost increases temperament",
          t3_boosted.temperament > 0.6)

    # Neutral witnesses (0.5) → no boost
    t3_neutral = TensorNormalizer.from_legacy_6dim(
        technical_competence=0.5,
        social_reliability=0.5,
        temporal_consistency=0.5,
        witness_count=0.5,
        lineage_depth=0.5,
        context_alignment=0.5,
    )
    check("T5.7 Neutral → all 0.5",
          t3_neutral.talent == 0.5 and t3_neutral.training == 0.5
          and t3_neutral.temperament == 0.5)

    # Mixed dims (attack_track_fo.py style)
    t3_mixed = TensorNormalizer.from_mixed_dims({
        "talent": 0.8, "trajectory": 0.6, "trust": 0.7,
        "tenacity": 0.5, "tact": 0.4, "temperament": 0.9,
    })
    check("T5.8 Mixed dims: talent preserved",
          abs(t3_mixed.talent - 0.8) < 0.05)  # Small boost from secondaries
    check("T5.9 Mixed dims: temperament preserved",
          abs(t3_mixed.temperament - 0.9) < 0.05)
    check("T5.10 Mixed dims: training defaults to 0.5",
          abs(t3_mixed.training - 0.5) < 0.05)

    # Pure canonical (no conversion needed)
    t3_canonical = TensorNormalizer.from_mixed_dims({
        "talent": 0.7, "training": 0.8, "temperament": 0.6,
    })
    check("T5.11 Pure canonical passes through",
          t3_canonical.talent == 0.7 and t3_canonical.training == 0.8
          and t3_canonical.temperament == 0.6)

    # Composite calculations
    check("T5.12 Equal-weight composite",
          abs(t3_canonical.composite - 0.7) < 0.001,
          f"composite={t3_canonical.composite}")
    check("T5.13 Weighted composite (tracker weights)",
          abs(t3_canonical.weighted_composite(Web4Constants.T3_TRACKER_WEIGHTS) -
              (0.7*0.3 + 0.8*0.5 + 0.6*0.2)) < 0.001)

    # Clamping
    t3_extreme = TensorNormalizer.from_legacy_6dim(
        technical_competence=0.99,
        social_reliability=0.01,
        temporal_consistency=0.5,
        witness_count=1.0,  # Max boost
        lineage_depth=1.0,
        context_alignment=0.0,  # Min boost for temperament
    )
    check("T5.14 Clamped to [0, 1]",
          0.0 <= t3_extreme.talent <= 1.0
          and 0.0 <= t3_extreme.training <= 1.0
          and 0.0 <= t3_extreme.temperament <= 1.0)

    # ====================================================================
    # T6: Entity Type Unifier
    # ====================================================================
    print("T6: Entity type unifier")

    check("T6.1 'human' resolves",
          resolve_entity_type("human") == CanonicalEntityType.HUMAN)
    check("T6.2 'AI_AGENT' resolves to AI",
          resolve_entity_type("AI_AGENT") == CanonicalEntityType.AI)
    check("T6.3 'ai' resolves to AI",
          resolve_entity_type("ai") == CanonicalEntityType.AI)
    check("T6.4 'sage' resolves to AI",
          resolve_entity_type("sage") == CanonicalEntityType.AI)
    check("T6.5 'team' resolves to TEAM",
          resolve_entity_type("team") == CanonicalEntityType.TEAM)
    check("T6.6 'org' resolves to ORGANIZATION",
          resolve_entity_type("org") == CanonicalEntityType.ORGANIZATION)
    check("T6.7 'hw' resolves to DEVICE",
          resolve_entity_type("hw") == CanonicalEntityType.DEVICE)
    check("T6.8 'dict' resolves to DICTIONARY",
          resolve_entity_type("dict") == CanonicalEntityType.DICTIONARY)
    check("T6.9 'infra' resolves to INFRASTRUCTURE",
          resolve_entity_type("infra") == CanonicalEntityType.INFRASTRUCTURE)
    check("T6.10 unknown defaults to AI",
          resolve_entity_type("unknown_thing") == CanonicalEntityType.AI)

    # All canonical types have at least one alias
    for ct in CanonicalEntityType:
        has_alias = any(v == ct for v in ENTITY_TYPE_ALIASES.values())
        check(f"T6.11 {ct.name} has alias", has_alias)

    # ====================================================================
    # T7: Trust Ceiling Resolution
    # ====================================================================
    print("T7: Trust ceiling resolution")

    check("T7.1 TPM2 = 1.0",
          resolve_trust_ceiling(TrustCeilingContext.TPM2_HARDWARE) == 1.0)
    check("T7.2 Verified software = 0.85",
          resolve_trust_ceiling(TrustCeilingContext.VERIFIED_SOFTWARE) == 0.85)
    check("T7.3 Unverified software = 0.7",
          resolve_trust_ceiling(TrustCeilingContext.UNVERIFIED_SOFTWARE) == 0.7)
    check("T7.4 Failure = 0.0",
          resolve_trust_ceiling(TrustCeilingContext.FAILURE) == 0.0)

    # ====================================================================
    # T8: Constants verification
    # ====================================================================
    print("T8: Unified constants")

    check("T8.1 Default budget = 100",
          Web4Constants.DEFAULT_ATP_BUDGET == 100.0)
    check("T8.2 Transfer fee = 5%",
          Web4Constants.TRANSFER_FEE_RATE == 0.05)
    check("T8.3 Quality threshold = 0.7",
          Web4Constants.QUALITY_THRESHOLD == 0.7)
    check("T8.4 Consciousness threshold = 0.7",
          Web4Constants.CONSCIOUSNESS_THRESHOLD == 0.7)
    check("T8.5 C=0.7 consistent across all contexts",
          Web4Constants.QUALITY_THRESHOLD ==
          Web4Constants.TRUST_HIGH_BOUNDARY ==
          Web4Constants.CONSCIOUSNESS_THRESHOLD)

    # ====================================================================
    # T9: End-to-end bridge flow
    # ====================================================================
    print("T9: End-to-end bridge flow")

    # Parse an LCT from Format A
    lct = parse_lct("lct:web4:agent:alice@Thor#delegation.federation")
    check("T9.1 Parse delegation LCT", lct.format == LCTFormat.FORMAT_A)

    # Get canonical entity type
    check("T9.2 Canonical type = AI", lct.canonical_type == "AI")

    # Get permission mappings
    task_type = lct.task_or_role
    mapping = bridge.get_all_mappings(task_type)
    check("T9.3 R6 mapping = admin", mapping["r6_role"] == "admin")
    check("T9.4 SAL mapping = authority", mapping["sal_role"] == "authority")

    # Check reputation eligibility
    ok, _ = bridge.check_reputation_eligible(task_type, 0.75)
    check("T9.5 T3=0.75 eligible for delegation (needs 0.7)", ok)
    ok2, _ = bridge.check_reputation_eligible(task_type, 0.5)
    check("T9.6 T3=0.5 NOT eligible for delegation", not ok2)

    # Normalize a legacy tensor for this entity
    t3 = TensorNormalizer.from_legacy_6dim(
        technical_competence=0.8,
        social_reliability=0.7,
        temporal_consistency=0.75,
    )
    check("T9.7 Normalized T3 composite > 0.7",
          t3.composite > 0.7, f"composite={t3.composite}")

    # Resolve trust ceiling based on platform
    # Thor has hardware binding → TPM2
    ceiling = resolve_trust_ceiling(TrustCeilingContext.TPM2_HARDWARE)
    check("T9.8 Thor trust ceiling = 1.0", ceiling == 1.0)

    # Full chain: LCT → task → permissions → reputation → trust ceiling
    check("T9.9 Full chain: parse → canonical → permissions → reputation → ceiling",
          lct.format == LCTFormat.FORMAT_A
          and lct.canonical_type == "AI"
          and mapping["r6_role"] == "admin"
          and t3.composite > Web4Constants.QUALITY_THRESHOLD
          and ceiling == Web4Constants.TRUST_CEILING_HARDWARE)

    # ====================================================================
    # T10: Cross-format identity resolution
    # ====================================================================
    print("T10: Cross-format identity resolution")

    # Same logical entity in all 3 formats
    format_a = "lct:web4:agent:alice@Thor#cognition"
    format_b = "lct://web4-agent:alice:cognition@mainnet"
    format_c = "lct:web4:ai:alice"

    pa = parse_lct(format_a)
    pb = parse_lct(format_b)
    pc = parse_lct(format_c)

    # All should resolve to AI canonical type
    check("T10.1 All formats → AI type",
          pa.canonical_type == "AI" and pb.canonical_type == "AI" and pc.canonical_type == "AI")

    # Format A and B should have platform info
    check("T10.2 Format A has platform", pa.platform == "Thor")
    check("T10.3 Format B has network", pb.network == "mainnet")
    check("T10.4 Format C has no platform", pc.platform == "")

    # Format A and B should have task/role
    check("T10.5 Format A has task", pa.task_or_role == "cognition")
    check("T10.6 Format B has role", pb.task_or_role == "cognition")
    check("T10.7 Format C has no task", pc.task_or_role == "")

    # ====================================================================
    # Print Summary
    # ====================================================================
    print(f"\n{'='*60}")
    print(f"Web4 Coherence Bridge: {checks_passed}/{total_checks} checks passed")
    print(f"{'='*60}")

    if checks_failed == 0:
        print("\nAll bridge components validated!")
        print("\nBridge capabilities:")
        print("  1. LCT Format Dispatcher: A/B/C → parsed + canonical type")
        print("  2. Permission Bridge: LUPS ↔ R6 ↔ SAL ↔ Hardbound ↔ Reputation")
        print("  3. Tensor Normalizer: 6-dim/mixed → canonical 3-dim T3")
        print("  4. Entity Type Unifier: 40+ variants → 16 canonical types")
        print("  5. Trust Ceiling Resolver: context → appropriate ceiling")
        print("  6. Unified Constants: single source of truth")
        print(f"\nDivergences RESOLVED:")
        print(f"  - LCT formats: dispatch + canonical conversion")
        print(f"  - Permission systems: bidirectional mapping tables")
        print(f"  - Tensor models: normalization with semantic mapping")
        print(f"  - Entity types: alias resolution to 16 canonical types")
        print(f"  - Trust ceilings: context-dependent (0.85 vs 0.7 both valid)")
        print(f"  - C=0.7: confirmed as intentional convergence value")
    else:
        print(f"\n{checks_failed} checks failed — see details above")

    return checks_passed, total_checks


if __name__ == "__main__":
    passed, total = run_tests()
    exit(0 if passed == total else 1)
