#!/usr/bin/env python3
"""
Cross-Specification Coherence Analysis
=======================================

Programmatic analysis of contradictions, divergences, and gaps across
Web4's 121 reference implementations.

Findings from systematic search of implementation/reference/ and simulations/:
- 3 incompatible LCT ID formats
- 5 disconnected permission models
- Legacy 6-dim tensors in 2 files + bridge code
- ATP constants inconsistent across modules
- EntityType enums range from 5 to 15+ types

This module:
1. Documents every known divergence with file/line references
2. Validates cross-spec assumptions programmatically
3. Proposes unified interfaces where feasible
4. Serves as executable documentation of the coherence state

Session: Legion Autonomous 2026-02-26
"""

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# SECTION 1: LCT ID FORMAT DIVERGENCE
# ============================================================================

class LCTFormatType(Enum):
    """Three incompatible LCT ID formats found across codebase."""
    FORMAT_A = "agent_identity"    # lct:web4:agent:{lineage}@{context}#{task}
    FORMAT_B = "uri_scheme"        # lct://{component}:{instance}:{role}@{network}
    FORMAT_C = "ad_hoc"            # lct:web4:{type}:{id} (no formal spec)


@dataclass
class LCTFormatDivergence:
    """Documents a specific LCT format used in a file."""
    file_path: str
    format_type: LCTFormatType
    example: str
    parser_method: str  # "regex", "urlparse", "split", "none"
    entity_types_used: List[str] = field(default_factory=list)


# Known divergences from systematic search
LCT_FORMAT_DIVERGENCES = [
    LCTFormatDivergence(
        file_path="lct_identity_system.py",
        format_type=LCTFormatType.FORMAT_A,
        example="lct:web4:agent:alice@Thor#perception",
        parser_method="regex",
        entity_types_used=["agent"],
    ),
    LCTFormatDivergence(
        file_path="lct_unified_presence.py",
        format_type=LCTFormatType.FORMAT_B,
        example="lct://sage:thinker:expert_42@testnet",
        parser_method="urlparse",
        entity_types_used=["sage", "web4-agent", "act-validator", "user", "agent"],
    ),
    LCTFormatDivergence(
        file_path="r7_framework.py (125+ occurrences)",
        format_type=LCTFormatType.FORMAT_C,
        example="lct:web4:ai:claude",
        parser_method="split",
        entity_types_used=["ai", "human", "org", "society", "witness", "role",
                          "admin", "device", "service", "oracle", "test"],
    ),
]


@dataclass
class EntityTypeEnum:
    """Documents an EntityType enum definition."""
    file_path: str
    types: List[str]
    count: int
    notes: str


# Five different EntityType enums found
ENTITY_TYPE_ENUMS = [
    EntityTypeEnum(
        file_path="web4_entity.py",
        types=["HUMAN", "AI", "SOCIETY", "ORGANIZATION", "ROLE", "TASK",
               "RESOURCE", "DEVICE", "SERVICE", "ORACLE", "ACCUMULATOR",
               "DICTIONARY", "HYBRID", "POLICY", "INFRASTRUCTURE"],
        count=15,
        notes="Canonical (str, Enum) - most complete",
    ),
    EntityTypeEnum(
        file_path="web4_entity_type_system.py",
        types=["HUMAN", "AI", "SOCIETY", "ORGANIZATION", "ROLE", "TASK",
               "RESOURCE", "DEVICE", "SERVICE", "ORACLE", "ACCUMULATOR",
               "DICTIONARY", "HYBRID", "POLICY", "INFRASTRUCTURE"],
        count=15,
        notes="Rich metadata (mode, energy, description) - matches web4_entity.py",
    ),
    EntityTypeEnum(
        file_path="lct_core_spec.py",
        types=["HUMAN", "AI", "ORGANIZATION", "ROLE", "TASK", "RESOURCE",
               "DEVICE", "SERVICE", "ORACLE", "ACCUMULATOR", "DICTIONARY", "HYBRID"],
        count=12,
        notes="Missing POLICY, INFRASTRUCTURE, SOCIETY",
    ),
    EntityTypeEnum(
        file_path="lct_identity.py",
        types=["HUMAN", "AI_AGENT", "ORGANIZATION", "TEAM", "SERVICE"],
        count=5,
        notes="Uses AI_AGENT (underscore), has TEAM (unique), missing many types",
    ),
    EntityTypeEnum(
        file_path="lct_federation_registry.py",
        types=["HUMAN", "AI", "ORGANIZATION", "ROLE", "DEVICE", "SERVICE", "SOCIETY"],
        count=7,
        notes="Federation subset - includes SOCIETY unlike lct_core_spec",
    ),
]


def analyze_entity_type_coverage() -> Dict[str, List[str]]:
    """Which entity types appear in which enum definitions?"""
    # Normalize AI_AGENT -> AI for comparison
    all_types: Dict[str, List[str]] = {}
    for enum_def in ENTITY_TYPE_ENUMS:
        for t in enum_def.types:
            normalized = t.replace("AI_AGENT", "AI")
            if normalized not in all_types:
                all_types[normalized] = []
            all_types[normalized].append(enum_def.file_path)
    return all_types


def find_entity_type_gaps() -> List[Tuple[str, List[str]]]:
    """Find entity types that exist in some enums but not others."""
    coverage = analyze_entity_type_coverage()
    all_files = [e.file_path for e in ENTITY_TYPE_ENUMS]
    gaps = []
    for entity_type, present_in in sorted(coverage.items()):
        missing_from = [f for f in all_files if f not in present_in]
        if missing_from:
            gaps.append((entity_type, missing_from))
    return gaps


# ============================================================================
# SECTION 2: PERMISSION MODEL DIVERGENCE
# ============================================================================

class PermissionSystem(Enum):
    LUPS = "lct_unified_permission_standard"
    R6_AUTH = "r6_authorization_roles"
    SAL = "society_authority_law"
    HARDBOUND = "hardbound_team_roles"
    REPUTATION = "reputation_based_auth"


@dataclass
class PermissionModelDivergence:
    """Documents a permission system and its characteristics."""
    system: PermissionSystem
    file_path: str
    roles: List[str]
    permission_format: str  # e.g., "category:perm", "workflow_action"
    has_atp_enforcement: bool
    has_delegation_control: bool
    has_code_execution_control: bool
    cross_references: List[PermissionSystem] = field(default_factory=list)


PERMISSION_MODELS = [
    PermissionModelDivergence(
        system=PermissionSystem.LUPS,
        file_path="lct_unified_permission_standard.py",
        roles=["perception", "planning", "planning.strategic", "execution.safe",
               "execution.code", "delegation.federation", "cognition",
               "cognition.sage", "admin.readonly", "admin.full"],
        permission_format="category:perm (atp:read, exec:safe, network:http)",
        has_atp_enforcement=True,
        has_delegation_control=True,
        has_code_execution_control=True,
        cross_references=[],  # No cross-references found!
    ),
    PermissionModelDivergence(
        system=PermissionSystem.R6_AUTH,
        file_path="r6_implementation_tiers.py",
        roles=["admin", "developer", "reviewer", "viewer"],
        permission_format="workflow_action (create, approve, reject, cancel, view)",
        has_atp_enforcement=False,
        has_delegation_control=False,
        has_code_execution_control=False,
        cross_references=[],
    ),
    PermissionModelDivergence(
        system=PermissionSystem.SAL,
        file_path="sal_society_authority_law.py",
        roles=["citizen", "authority", "oracle", "witness", "auditor"],
        permission_format="implied (governance-specific)",
        has_atp_enforcement=False,
        has_delegation_control=False,
        has_code_execution_control=False,
        cross_references=[],
    ),
    PermissionModelDivergence(
        system=PermissionSystem.HARDBOUND,
        file_path="simulations/test_team.py + policy.py",
        roles=["admin", "developer", "reviewer", "member", "observer"],
        permission_format="rule-based (PolicyRule with action_type, allowed_roles)",
        has_atp_enforcement=True,  # Per-member ATP budget
        has_delegation_control=False,
        has_code_execution_control=False,
        cross_references=[],
    ),
    PermissionModelDivergence(
        system=PermissionSystem.REPUTATION,
        file_path="lct_authorization_system.py",
        roles=["novice", "developing", "trusted", "expert", "master"],
        permission_format="action:target (read:public_docs, execute:basic_tests)",
        has_atp_enforcement=False,
        has_delegation_control=False,
        has_code_execution_control=False,
        cross_references=[],
    ),
]


def find_permission_contradictions() -> List[str]:
    """Identify specific contradictions between permission systems."""
    contradictions = []

    # LUPS says admin.full can delegate; R6 has no delegation concept
    contradictions.append(
        "LUPS defines delegation.federation task type; R6 AuthRole has no delegation permissions"
    )

    # LUPS has code execution levels; other systems don't
    contradictions.append(
        "LUPS defines execution.safe (sandbox) and execution.code (full); "
        "R6, SAL, Hardbound, Reputation systems have no code execution control"
    )

    # Hardbound uses ad-hoc roles not in any spec
    contradictions.append(
        "Hardbound simulation uses 'member' and 'observer' roles not defined in "
        "R6 (viewer) or SAL (citizen) systems"
    )

    # Permission format mismatch
    contradictions.append(
        "Permission formats are incompatible: LUPS uses 'atp:read', "
        "Reputation uses 'read:public_docs', R6 uses bare 'approve'"
    )

    # ATP enforcement inconsistency
    contradictions.append(
        "ATP enforcement: LUPS has per-task budgets (perception=200, cognition=1000), "
        "Hardbound has per-member budgets (default=100), R6/SAL/Reputation have none"
    )

    return contradictions


# ============================================================================
# SECTION 3: TRUST TENSOR DIVERGENCE
# ============================================================================

class TensorModel(Enum):
    CANONICAL_3DIM = "3-dim (talent/training/temperament)"
    LEGACY_6DIM = "6-dim (technical_competence/temporal_consistency/social_reliability/...)"
    MIXED = "mixed (some canonical + some non-standard)"


@dataclass
class TensorUsage:
    """Documents how a file uses trust tensors."""
    file_path: str
    model: TensorModel
    dimensions: List[str]
    composite_formula: str
    schema_compliant: bool


TENSOR_USAGES = [
    # Canonical 3-dim (correct)
    TensorUsage(
        file_path="sal_society_authority_law.py",
        model=TensorModel.CANONICAL_3DIM,
        dimensions=["talent", "training", "temperament"],
        composite_formula="(talent + training + temperament) / 3",
        schema_compliant=True,
    ),
    TensorUsage(
        file_path="t3_tracker.py",
        model=TensorModel.CANONICAL_3DIM,
        dimensions=["talent", "training", "temperament"],
        composite_formula="0.3*talent + 0.5*training + 0.2*temperament",
        schema_compliant=True,
    ),
    TensorUsage(
        file_path="t3v3_reputation_engine.py",
        model=TensorModel.CANONICAL_3DIM,
        dimensions=["talent", "training", "temperament"],
        composite_formula="composite averaging",
        schema_compliant=True,
    ),
    # Legacy 6-dim (deprecated, still active)
    TensorUsage(
        file_path="lct_capability_levels.py",
        model=TensorModel.LEGACY_6DIM,
        dimensions=["technical_competence", "social_reliability",
                     "temporal_consistency", "witness_count",
                     "lineage_depth", "context_alignment"],
        composite_formula="sum(6 dims) / 6",
        schema_compliant=False,
    ),
    TensorUsage(
        file_path="lct_capability_levels_v2.py",
        model=TensorModel.LEGACY_6DIM,
        dimensions=["technical_competence", "social_reliability",
                     "temporal_consistency", "witness_count",
                     "lineage_depth", "context_alignment"],
        composite_formula="sum(6 dims) / 6",
        schema_compliant=False,
    ),
    # Mixed (simulation)
    TensorUsage(
        file_path="attack_track_fo.py",
        model=TensorModel.MIXED,
        dimensions=["talent", "trajectory", "trust", "tenacity", "tact", "temperament"],
        composite_formula="ad-hoc",
        schema_compliant=False,
    ),
]


@dataclass
class CompositeFormulaVariant:
    """Different composite formulas found."""
    file_path: str
    formula: str
    weights: Optional[Dict[str, float]] = None


COMPOSITE_FORMULAS = [
    CompositeFormulaVariant(
        file_path="sal_society_authority_law.py",
        formula="equal_weight_average",
        weights={"talent": 0.333, "training": 0.333, "temperament": 0.333},
    ),
    CompositeFormulaVariant(
        file_path="t3_tracker.py",
        formula="weighted_average",
        weights={"talent": 0.30, "training": 0.50, "temperament": 0.20},
    ),
    CompositeFormulaVariant(
        file_path="reputation_computation.py",
        formula="weighted_average (spec example)",
        weights={"talent": 0.40, "training": 0.40, "temperament": 0.20},
    ),
]


def find_tensor_contradictions() -> List[str]:
    """Identify specific tensor model contradictions."""
    contradictions = []

    contradictions.append(
        "lct_capability_levels.py and v2 use 6-dim tensors "
        "(technical_competence, social_reliability, temporal_consistency, "
        "witness_count, lineage_depth, context_alignment) while spec requires "
        "3-dim (talent, training, temperament)"
    )

    contradictions.append(
        "cross_implementation_integration.py explicitly bridges 6-dim→3-dim "
        "with lossy mapping (technical_competence→talent, social_reliability→"
        "temperament, temporal_consistency→training) — semantically imprecise"
    )

    contradictions.append(
        "Composite formula varies: SAL uses equal weights (1/3 each), "
        "T3 tracker uses 30/50/20, reputation computation uses 40/40/20 — "
        "no canonical weighting defined in spec"
    )

    contradictions.append(
        "attack_track_fo.py uses non-standard dimensions (trajectory, trust, "
        "tenacity, tact) alongside canonical (talent, temperament) — "
        "these are not defined in t3v3.schema.json"
    )

    return contradictions


# ============================================================================
# SECTION 4: ATP CONSTANTS DIVERGENCE
# ============================================================================

@dataclass
class ATPConstant:
    """An ATP-related constant found in the codebase."""
    name: str
    value: float
    file_path: str
    context: str


# All ATP constants found by systematic search
ATP_CONSTANTS = {
    "default_budget": [
        ATPConstant("atp_budget", 100.0, "mcp_web4_protocol.py:815", "session creation default"),
        ATPConstant("default_member_budget", 100.0, "simulations/team.py:52", "team member default"),
        ATPConstant("atp_budget", 100.0, "simulations/member.py:65", "member dataclass default"),
    ],
    "transfer_fees": [
        ATPConstant("TRANSFER_FEE", 0.05, "ai_agent_accountability.py:377", "5% per transfer"),
        ATPConstant("TRANSFER_FEE_RATE", 0.05, "ai_agent_accountability_stack.py:948", "5% per transfer"),
        ATPConstant("FORWARD_FEE", 0.01, "ai_agent_accountability_stack.py:811", "1% forward bridge"),
        ATPConstant("RETURN_FEE", 0.005, "ai_agent_accountability_stack.py:812", "0.5% return bridge"),
        ATPConstant("QUERY_FEE_RATE", 0.10, "t3v3_privacy_governance.py:505", "10% query fee"),
    ],
    "trust_ceilings": [
        ATPConstant("hardware_ceiling", 1.0, "hardware_entity.py:85", "TPM2 hardware binding"),
        ATPConstant("software_ceiling", 0.85, "avp_transport.py:79", "software-only transport"),
        ATPConstant("software_ceiling", 0.7, "CLAUDE.md", "software binding (Hardbound)"),
    ],
    "quality_threshold": [
        ATPConstant("quality_threshold", 0.7, "multi_machine_sage_federation.py:348", "ATP settlement gate"),
        ATPConstant("trust_boundary", 0.7, "mcp_web4_protocol.py:536", "medium/high trust"),
        ATPConstant("convergence", 0.7, "MEMORY.md", "SAGE, Web4, Synchronism all find this"),
    ],
    "decay_rates": [
        ATPConstant("decay_rate", 0.1, "simulations/federation.py:917", "10% heartbeat decay"),
        ATPConstant("decay_rate", 0.15, "simulations/attack_simulations.py:2146", "15% test config"),
        ATPConstant("training_decay", -0.001, "t3v3_reputation_engine.py:664", "per month inactivity"),
        ATPConstant("decay_per_hop", 0.5, "simulations/attack_simulations.py:75535", "50% chain decay"),
    ],
}


def find_atp_contradictions() -> List[str]:
    """Identify ATP constant contradictions."""
    contradictions = []

    contradictions.append(
        "Software trust ceiling: 0.85 in avp_transport.py vs 0.7 in CLAUDE.md "
        "(Hardbound software binding) — which is canonical?"
    )

    contradictions.append(
        "Decay rates vary by context: 0.1 (federation), 0.15 (test), -0.001/month "
        "(training), 0.5/hop (chain) — no unified decay parameter model"
    )

    contradictions.append(
        "0.7 threshold appears in 6+ different contexts (quality gate, trust boundary, "
        "convergence value) — possibly a fundamental constant, possibly coincidental"
    )

    contradictions.append(
        "Transfer fee types: 5% transfer, 1% forward bridge, 0.5% return bridge, "
        "10% query fee — all named 'fee' but serve different purposes"
    )

    return contradictions


# ============================================================================
# SECTION 5: UNIFIED INTERFACE PROPOSALS
# ============================================================================

@dataclass
class UnifiedLCTID:
    """
    Proposed unified LCT ID that can represent all 3 formats.

    Format: lct:{version}:{entity_type}:{identifier}[?{params}]

    Where:
    - version: "v1" (current)
    - entity_type: from canonical 15-type enum
    - identifier: format-specific part
    - params: optional query parameters

    Examples:
    - lct:v1:agent:alice@Thor#perception         (Format A identity)
    - lct:v1:sage:thinker:expert_42@testnet       (Format B presence)
    - lct:v1:human:alice                          (Format C simple)
    """
    version: str = "v1"
    entity_type: str = ""
    identifier: str = ""
    params: Dict[str, str] = field(default_factory=dict)

    # Canonical entity types (union of all 5 enums)
    CANONICAL_TYPES = {
        "HUMAN", "AI", "SOCIETY", "ORGANIZATION", "ROLE", "TASK",
        "RESOURCE", "DEVICE", "SERVICE", "ORACLE", "ACCUMULATOR",
        "DICTIONARY", "HYBRID", "POLICY", "INFRASTRUCTURE",
        # Additional from other enums
        "TEAM",  # From lct_identity.py
    }

    def to_string(self) -> str:
        base = f"lct:{self.version}:{self.entity_type.lower()}:{self.identifier}"
        if self.params:
            param_str = "&".join(f"{k}={v}" for k, v in sorted(self.params.items()))
            base += f"?{param_str}"
        return base

    @staticmethod
    def detect_format(lct_str: str) -> LCTFormatType:
        """Detect which format an LCT string uses."""
        if lct_str.startswith("lct://"):
            return LCTFormatType.FORMAT_B
        if "@" in lct_str and "#" in lct_str:
            return LCTFormatType.FORMAT_A
        return LCTFormatType.FORMAT_C


@dataclass
class UnifiedPermissionCheck:
    """
    Proposed unified permission interface that bridges all 5 systems.

    Maps: (entity_lct, action, resource) -> (allowed, reason)

    Internally dispatches to the appropriate permission system based on context.
    """
    def check(self, entity_lct: str, action: str, resource: str = "",
              context: str = "default") -> Tuple[bool, str]:
        """
        Unified permission check.

        Routes to:
        - LUPS for task-based permissions (action starts with category:)
        - R6 for workflow actions (create, approve, reject, cancel, view)
        - SAL for governance actions (citizen, authority, oracle actions)
        - Reputation for resource-targeted actions (read:, write:, execute:)
        """
        # Route by action format
        if ":" in action and not action.startswith(("read:", "write:", "execute:")):
            return self._check_lups(entity_lct, action)
        elif action in ("create", "approve", "reject", "cancel", "view", "configure"):
            return self._check_r6(entity_lct, action)
        elif action.startswith(("read:", "write:", "execute:", "witness:", "admin:", "grant:", "mint:")):
            return self._check_reputation(entity_lct, action, resource)
        else:
            return False, f"Unknown action format: {action}"

    def _check_lups(self, lct: str, permission: str) -> Tuple[bool, str]:
        return False, "LUPS check not implemented in coherence analyzer"

    def _check_r6(self, lct: str, action: str) -> Tuple[bool, str]:
        return False, "R6 check not implemented in coherence analyzer"

    def _check_reputation(self, lct: str, action: str, resource: str) -> Tuple[bool, str]:
        return False, "Reputation check not implemented in coherence analyzer"


# ============================================================================
# SECTION 6: COHERENCE METRICS
# ============================================================================

@dataclass
class CoherenceMetric:
    """A quantitative measure of cross-spec coherence."""
    dimension: str
    total_implementations: int
    consistent_implementations: int
    divergent_implementations: int
    contradictions: List[str]

    @property
    def coherence_score(self) -> float:
        """0.0 = fully incoherent, 1.0 = fully coherent."""
        if self.total_implementations == 0:
            return 0.0
        return self.consistent_implementations / self.total_implementations


def compute_coherence_metrics() -> List[CoherenceMetric]:
    """Compute coherence metrics across all dimensions."""
    metrics = []

    # LCT Format coherence
    # 40+ files use Format C, 1 uses Format A, 3 use Format B
    metrics.append(CoherenceMetric(
        dimension="LCT ID Format",
        total_implementations=44,
        consistent_implementations=40,  # Format C majority
        divergent_implementations=4,    # Format A (1) + Format B (3)
        contradictions=[
            "3 incompatible formats with no format detection or dispatch",
            "5 different EntityType enums (5 to 15 types)",
            "No cross-format validation exists",
        ],
    ))

    # Permission model coherence
    metrics.append(CoherenceMetric(
        dimension="Permission Model",
        total_implementations=5,
        consistent_implementations=0,  # All 5 are independent
        divergent_implementations=5,
        contradictions=find_permission_contradictions(),
    ))

    # Trust tensor coherence
    schema_compliant = sum(1 for t in TENSOR_USAGES if t.schema_compliant)
    non_compliant = sum(1 for t in TENSOR_USAGES if not t.schema_compliant)
    metrics.append(CoherenceMetric(
        dimension="Trust Tensor Model",
        total_implementations=len(TENSOR_USAGES),
        consistent_implementations=schema_compliant,
        divergent_implementations=non_compliant,
        contradictions=find_tensor_contradictions(),
    ))

    # ATP constants coherence
    metrics.append(CoherenceMetric(
        dimension="ATP Constants",
        total_implementations=len(sum(ATP_CONSTANTS.values(), [])),
        consistent_implementations=3,  # Default budget consistent at 100
        divergent_implementations=12,
        contradictions=find_atp_contradictions(),
    ))

    return metrics


# ============================================================================
# SECTION 7: CROSS-SPEC DEPENDENCY GRAPH
# ============================================================================

@dataclass
class SpecDependency:
    """A dependency between two specifications/implementations."""
    source: str       # Module that depends on
    target: str       # Module being depended on
    interface: str    # What interface is expected
    satisfied: bool   # Whether the target provides what source expects
    notes: str = ""


# Critical cross-spec dependencies and whether they're satisfied
SPEC_DEPENDENCIES = [
    SpecDependency(
        source="federation_consensus_atp.py",
        target="lct_identity_system.py",
        interface="LCT ID string format for platform identification",
        satisfied=False,
        notes="federation uses ad-hoc 'platform_alpha' strings, identity uses lct:web4:agent: format",
    ),
    SpecDependency(
        source="multi_machine_sage_federation.py",
        target="lct_unified_permission_standard.py",
        interface="Permission checking for delegation tasks",
        satisfied=False,
        notes="federation has own validate() method, doesn't call LUPS check_permission()",
    ),
    SpecDependency(
        source="lct_identity_system.py",
        target="web4_entity.py",
        interface="EntityType enum for identity creation",
        satisfied=False,
        notes="Identity system hardcodes 'agent' type; entity system has 15 types",
    ),
    SpecDependency(
        source="federation_consensus_atp.py",
        target="lct_unified_permission_standard.py",
        interface="ATP budget limits per task type",
        satisfied=False,
        notes="Federation uses arbitrary ATP amounts; LUPS defines per-task budgets",
    ),
    SpecDependency(
        source="society_lifecycle.py",
        target="lct_identity_system.py",
        interface="Citizen LCT creation with identity certificates",
        satisfied=False,
        notes="Society creates ad-hoc LCT strings; identity system has full certificate chain",
    ),
    SpecDependency(
        source="r7_framework.py",
        target="lct_unified_permission_standard.py",
        interface="Reputation-based permission escalation",
        satisfied=False,
        notes="R7 tracks reputation independently; LUPS has no reputation integration",
    ),
    SpecDependency(
        source="lct_authorization_system.py",
        target="lct_unified_permission_standard.py",
        interface="Reputation level → task type mapping",
        satisfied=False,
        notes="Authorization uses own permission format (read:public_docs); LUPS uses (atp:read)",
    ),
    # Satisfied dependencies
    SpecDependency(
        source="sal_society_authority_law.py",
        target="t3v3 schema",
        interface="3-dim trust tensor model",
        satisfied=True,
        notes="SAL correctly uses talent/training/temperament",
    ),
    SpecDependency(
        source="t3v3_reputation_engine.py",
        target="t3v3 schema",
        interface="3-dim trust tensor model",
        satisfied=True,
        notes="Reputation engine correctly uses canonical T3",
    ),
]


def compute_dependency_satisfaction() -> Tuple[int, int, float]:
    """Returns (satisfied, total, ratio)."""
    satisfied = sum(1 for d in SPEC_DEPENDENCIES if d.satisfied)
    total = len(SPEC_DEPENDENCIES)
    return satisfied, total, satisfied / total if total > 0 else 0.0


# ============================================================================
# SECTION 8: TEST SUITE
# ============================================================================

def run_tests():
    """Validate the coherence analysis itself."""
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

    # --- T1: LCT Format Detection ---
    print("T1: LCT format detection")
    check("T1.1 Format A detection",
          UnifiedLCTID.detect_format("lct:web4:agent:alice@Thor#perception") == LCTFormatType.FORMAT_A)
    check("T1.2 Format B detection",
          UnifiedLCTID.detect_format("lct://sage:thinker:expert_42@testnet") == LCTFormatType.FORMAT_B)
    check("T1.3 Format C detection",
          UnifiedLCTID.detect_format("lct:web4:ai:claude") == LCTFormatType.FORMAT_C)
    check("T1.4 Format A with org",
          UnifiedLCTID.detect_format("lct:web4:agent:org:anthropic@cloud:aws#admin.readonly") == LCTFormatType.FORMAT_A)
    check("T1.5 Format B with params",
          UnifiedLCTID.detect_format("lct://agent:beta@mainnet?capabilities=text-gen") == LCTFormatType.FORMAT_B)

    # --- T2: Entity Type Coverage ---
    print("T2: Entity type coverage analysis")
    coverage = analyze_entity_type_coverage()
    check("T2.1 HUMAN in all enums",
          len(coverage.get("HUMAN", [])) == 5,
          f"HUMAN in {len(coverage.get('HUMAN', []))} enums, expected 5")
    check("T2.2 AI in most enums",
          len(coverage.get("AI", [])) >= 4,
          f"AI in {len(coverage.get('AI', []))} enums")
    check("T2.3 POLICY only in 2 enums",
          len(coverage.get("POLICY", [])) == 2,
          f"POLICY in {len(coverage.get('POLICY', []))} enums")
    check("T2.4 TEAM only in 1 enum",
          len(coverage.get("TEAM", [])) == 1,
          f"TEAM in {len(coverage.get('TEAM', []))} enums")

    gaps = find_entity_type_gaps()
    check("T2.5 Gaps exist",
          len(gaps) > 0,
          "Expected entity type gaps to exist")
    check("T2.6 INFRASTRUCTURE has gaps",
          any(t == "INFRASTRUCTURE" for t, _ in gaps),
          "INFRASTRUCTURE should be missing from some enums")

    # --- T3: Permission Contradictions ---
    print("T3: Permission model contradictions")
    contradictions = find_permission_contradictions()
    check("T3.1 Contradictions found",
          len(contradictions) >= 4,
          f"Found {len(contradictions)} contradictions, expected >= 4")
    check("T3.2 All 5 permission models documented",
          len(PERMISSION_MODELS) == 5)
    check("T3.3 No cross-references between models",
          all(len(m.cross_references) == 0 for m in PERMISSION_MODELS),
          "Expected zero cross-references (isolated systems)")
    check("T3.4 Only LUPS has delegation control",
          sum(1 for m in PERMISSION_MODELS if m.has_delegation_control) == 1)
    check("T3.5 Only LUPS has code execution control",
          sum(1 for m in PERMISSION_MODELS if m.has_code_execution_control) == 1)

    # --- T4: Trust Tensor Analysis ---
    print("T4: Trust tensor model analysis")
    schema_compliant = [t for t in TENSOR_USAGES if t.schema_compliant]
    non_compliant = [t for t in TENSOR_USAGES if not t.schema_compliant]
    check("T4.1 Some schema-compliant tensors",
          len(schema_compliant) >= 3,
          f"Found {len(schema_compliant)} compliant implementations")
    check("T4.2 Some non-compliant tensors",
          len(non_compliant) >= 2,
          f"Found {len(non_compliant)} non-compliant implementations")
    check("T4.3 Legacy 6-dim files identified",
          any(t.model == TensorModel.LEGACY_6DIM for t in TENSOR_USAGES))
    check("T4.4 Mixed dim files identified",
          any(t.model == TensorModel.MIXED for t in TENSOR_USAGES))

    tensor_contradictions = find_tensor_contradictions()
    check("T4.5 Tensor contradictions found",
          len(tensor_contradictions) >= 3,
          f"Found {len(tensor_contradictions)} contradictions")

    # --- T5: Composite Formula Variants ---
    print("T5: Composite formula analysis")
    check("T5.1 Multiple composite formulas found",
          len(COMPOSITE_FORMULAS) >= 3)

    # Check that weights don't match across formulas
    weights_list = [f.weights for f in COMPOSITE_FORMULAS if f.weights]
    unique_weights = set(tuple(sorted(w.items())) for w in weights_list)
    check("T5.2 Weights differ across implementations",
          len(unique_weights) >= 2,
          f"Found {len(unique_weights)} unique weight sets")

    # --- T6: ATP Constants ---
    print("T6: ATP constant analysis")
    atp_contradictions = find_atp_contradictions()
    check("T6.1 ATP contradictions found",
          len(atp_contradictions) >= 3,
          f"Found {len(atp_contradictions)} contradictions")

    # Default budget consistency
    default_budgets = ATP_CONSTANTS.get("default_budget", [])
    check("T6.2 Default budgets consistent at 100",
          all(c.value == 100.0 for c in default_budgets),
          "All default ATP budgets should be 100.0")

    # Transfer fee base rate consistency
    base_fees = [c for c in ATP_CONSTANTS.get("transfer_fees", [])
                 if "TRANSFER_FEE" in c.name and "RATE" not in c.name
                 and "FORWARD" not in c.name and "RETURN" not in c.name
                 and "QUERY" not in c.name]
    check("T6.3 Base transfer fee consistent at 5%",
          all(c.value == 0.05 for c in base_fees),
          f"Found {[c.value for c in base_fees]}")

    # Trust ceiling divergence
    ceilings = ATP_CONSTANTS.get("trust_ceilings", [])
    software_ceilings = [c for c in ceilings if "software" in c.name]
    check("T6.4 Software trust ceiling has divergence",
          len(set(c.value for c in software_ceilings)) > 1,
          f"Software ceilings: {[c.value for c in software_ceilings]}")

    # --- T7: Coherence Metrics ---
    print("T7: Coherence metrics")
    metrics = compute_coherence_metrics()
    check("T7.1 Four dimensions analyzed",
          len(metrics) == 4)

    for m in metrics:
        check(f"T7.2 {m.dimension} has contradictions",
              len(m.contradictions) > 0,
              f"{m.dimension}: {len(m.contradictions)} contradictions")

    # LCT format has highest coherence (Format C dominates)
    lct_metric = next(m for m in metrics if m.dimension == "LCT ID Format")
    check("T7.3 LCT format coherence > 0.8",
          lct_metric.coherence_score > 0.8,
          f"Score: {lct_metric.coherence_score:.2f}")

    # Permission model has lowest coherence (all different)
    perm_metric = next(m for m in metrics if m.dimension == "Permission Model")
    check("T7.4 Permission coherence = 0.0",
          perm_metric.coherence_score == 0.0,
          f"Score: {perm_metric.coherence_score:.2f}")

    # --- T8: Dependency Graph ---
    print("T8: Cross-spec dependency graph")
    satisfied, total, ratio = compute_dependency_satisfaction()
    check("T8.1 Most dependencies unsatisfied",
          ratio < 0.5,
          f"Satisfaction ratio: {ratio:.2f} ({satisfied}/{total})")
    check("T8.2 Some dependencies satisfied",
          satisfied > 0,
          f"Satisfied: {satisfied}")
    check("T8.3 T3V3 schema dependencies satisfied",
          all(d.satisfied for d in SPEC_DEPENDENCIES if "t3v3" in d.target.lower()))

    unsatisfied = [d for d in SPEC_DEPENDENCIES if not d.satisfied]
    check("T8.4 Unsatisfied dependencies have notes",
          all(d.notes for d in unsatisfied))

    # --- T9: UnifiedLCTID ---
    print("T9: Unified LCT ID proposal")
    uid = UnifiedLCTID(entity_type="human", identifier="alice")
    check("T9.1 Unified ID serialization",
          uid.to_string() == "lct:v1:human:alice")

    uid_params = UnifiedLCTID(entity_type="agent", identifier="bob@Thor",
                              params={"task": "perception"})
    check("T9.2 Unified ID with params",
          uid_params.to_string() == "lct:v1:agent:bob@Thor?task=perception")

    check("T9.3 Canonical types include HUMAN",
          "HUMAN" in UnifiedLCTID.CANONICAL_TYPES)
    check("T9.4 Canonical types include TEAM",
          "TEAM" in UnifiedLCTID.CANONICAL_TYPES)
    check("T9.5 Canonical types count >= 15",
          len(UnifiedLCTID.CANONICAL_TYPES) >= 15,
          f"Count: {len(UnifiedLCTID.CANONICAL_TYPES)}")

    # --- T10: Comprehensive Summary Stats ---
    print("T10: Summary statistics")
    total_contradictions = (
        len(contradictions) +
        len(tensor_contradictions) +
        len(atp_contradictions) +
        len(lct_metric.contradictions)
    )
    check("T10.1 Total contradictions >= 15",
          total_contradictions >= 15,
          f"Total: {total_contradictions}")

    total_divergences = len(LCT_FORMAT_DIVERGENCES)
    check("T10.2 Format divergences documented",
          total_divergences >= 3)

    check("T10.3 All 5 entity type enums documented",
          len(ENTITY_TYPE_ENUMS) == 5)

    check("T10.4 Coherence scores computed",
          all(0.0 <= m.coherence_score <= 1.0 for m in metrics))

    # --- Print Summary ---
    print(f"\n{'='*60}")
    print(f"Cross-Spec Coherence Analysis: {checks_passed}/{total_checks} checks passed")
    print(f"{'='*60}")

    print("\nCoherence Scores by Dimension:")
    for m in metrics:
        bar = "█" * int(m.coherence_score * 20) + "░" * (20 - int(m.coherence_score * 20))
        print(f"  {m.dimension:25s} [{bar}] {m.coherence_score:.0%}")

    print(f"\nDependency Satisfaction: {satisfied}/{total} ({ratio:.0%})")

    print(f"\nContradictions Found:")
    print(f"  LCT Format:       {len(lct_metric.contradictions)}")
    print(f"  Permission Model:  {len(contradictions)}")
    print(f"  Trust Tensors:     {len(tensor_contradictions)}")
    print(f"  ATP Constants:     {len(atp_contradictions)}")
    print(f"  TOTAL:             {total_contradictions}")

    print(f"\nKey Findings:")
    print(f"  - 3 incompatible LCT ID formats (no dispatch mechanism)")
    print(f"  - 5 isolated permission systems (zero cross-references)")
    print(f"  - 2 files still using deprecated 6-dim tensors")
    print(f"  - Software trust ceiling: 0.85 vs 0.7 (unresolved)")
    print(f"  - {len(unsatisfied)}/{total} cross-spec dependencies unsatisfied")

    print(f"\nProposed Actions:")
    print(f"  1. Implement format detection + dispatch for LCT IDs")
    print(f"  2. Bridge LUPS <-> R6 <-> SAL <-> Reputation permissions")
    print(f"  3. Migrate lct_capability_levels.py to 3-dim tensors")
    print(f"  4. Canonicalize software trust ceiling (0.85 or 0.7)")
    print(f"  5. Define C=0.7 as named constant if intentional convergence")

    return checks_passed, total_checks


if __name__ == "__main__":
    passed, total = run_tests()
    exit(0 if passed == total else 1)
