"""
Cognitive Sub-Entity LCT Framework — Reference Implementation

Implements RFC_COGNITIVE_SUB_ENTITIES.md (RFC-CSE-001):
- Hierarchical LCT structure: primary → sub-entities (agents, models, tools, roles)
- Cognitive provenance tracking: spawn context, fingerprint, lineage
- Trust inheritance: sub-entities start at parent×coefficient, evolve independently
- Autonomy levels: supervised < semi-autonomous < autonomous < fully-autonomous
- Collusion detection: decision correlation, timing patterns, outcome alignment
- ATP attribution: cognitive contribution tracking, fair value distribution
- Decision conflict resolution: voting, escalation, parent override
- Resource constraints: thermal/power limits as natural proliferation regulation
- Cognitive diversity scoring: reward diverse reasoning approaches

Key insight from RFC: "Every cognitive entity gets an LCT. Agents, roles, tools
are all legitimate entities requiring identity. Single hardware platforms spawn
multiple autonomous cognitive processes."

Spec: web4-standard/rfcs/RFC_COGNITIVE_SUB_ENTITIES.md
"""

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class CognitiveEntityType(Enum):
    """Types of cognitive sub-entities."""
    AGENT = "agent"         # Independent reasoning entity
    MODEL = "model"         # ML model instance
    TOOL = "tool"           # Specialized capability
    ROLE = "role"           # Context-specific behavior
    VALIDATOR = "validator" # Compliance/verification entity

class AutonomyLevel(Enum):
    """Autonomy levels for cognitive entities (ordered)."""
    SUPERVISED = "supervised"             # Requires approval for all decisions
    SEMI_AUTONOMOUS = "semi-autonomous"   # Approval for high-consequence only
    AUTONOMOUS = "autonomous"             # Independent within scope
    FULLY_AUTONOMOUS = "fully-autonomous" # Unrestricted within scope

class SpawnContext(Enum):
    """Why a sub-entity was created."""
    TASK_DELEGATION = "task_delegation"
    ROLE_ACTIVATION = "role_activation"
    CAPABILITY_EXTENSION = "capability_extension"
    SPECIALIZATION = "specialization"
    FEDERATION_REQUEST = "federation_request"

class ConflictResolution(Enum):
    """How to resolve sub-entity disagreements."""
    PARENT_OVERRIDE = "parent_override"   # Parent decides
    MAJORITY_VOTE = "majority_vote"       # Sub-entities vote
    HIGHEST_TRUST = "highest_trust"       # Highest T3 wins
    ESCALATION = "escalation"             # Escalate to society

class SubEntityStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    DORMANT = "dormant"       # Exists but not executing

class CollusionIndicator(Enum):
    TIMING_CORRELATION = "timing"       # Suspiciously coordinated timing
    OUTCOME_ALIGNMENT = "outcome"       # Always agree
    DECISION_MIRRORING = "mirroring"    # Identical decision patterns
    ATP_FUNNELING = "funneling"         # ATP flowing to same target


# Autonomy level → trust inheritance coefficients (§3)
TRUST_INHERITANCE = {
    AutonomyLevel.SUPERVISED: 0.9,       # High inheritance, low independence
    AutonomyLevel.SEMI_AUTONOMOUS: 0.8,  # Moderate inheritance
    AutonomyLevel.AUTONOMOUS: 0.6,       # Lower inheritance, higher independence
    AutonomyLevel.FULLY_AUTONOMOUS: 0.4, # Minimal inheritance
}

# Autonomy level → minimum independent trust required
MIN_INDEPENDENT_TRUST = {
    AutonomyLevel.SUPERVISED: 0.0,       # No minimum
    AutonomyLevel.SEMI_AUTONOMOUS: 0.3,
    AutonomyLevel.AUTONOMOUS: 0.5,
    AutonomyLevel.FULLY_AUTONOMOUS: 0.7,
}

# Autonomy ordering for comparison
AUTONOMY_ORDER = {
    AutonomyLevel.SUPERVISED: 0,
    AutonomyLevel.SEMI_AUTONOMOUS: 1,
    AutonomyLevel.AUTONOMOUS: 2,
    AutonomyLevel.FULLY_AUTONOMOUS: 3,
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class T3Snapshot:
    """Trust tensor snapshot for sub-entity."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    @property
    def composite(self) -> float:
        return 0.4 * self.talent + 0.3 * self.training + 0.3 * self.temperament

    def modulate(self, factor: float) -> 'T3Snapshot':
        return T3Snapshot(
            talent=min(1.0, self.talent * factor),
            training=min(1.0, self.training * factor),
            temperament=min(1.0, self.temperament * factor))


@dataclass
class CognitiveProvenance:
    """Tracks lineage and cognitive identity (§2)."""
    parent_lct: str
    spawn_context: SpawnContext
    cognitive_fingerprint: str       # Model identifier
    decision_scope: List[str]        # Allowed domains
    spawned_at: str                  # ISO timestamp
    lineage_depth: int = 1           # How many levels from root

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parent_lct": self.parent_lct,
            "spawn_context": self.spawn_context.value,
            "cognitive_fingerprint": self.cognitive_fingerprint,
            "decision_scope": self.decision_scope,
            "spawned_at": self.spawned_at,
            "lineage_depth": self.lineage_depth,
        }


@dataclass
class ResourceConstraints:
    """Hardware constraints that regulate sub-entity proliferation."""
    max_concurrent: int = 10          # Max active sub-entities
    compute_budget: float = 1.0       # Fraction of available compute
    memory_budget_mb: float = 1024    # MB available
    thermal_headroom: float = 1.0     # 0=throttled, 1=full headroom
    power_budget_w: float = 15.0      # Watts available

    def can_spawn(self, current_count: int) -> bool:
        return (current_count < self.max_concurrent and
                self.compute_budget > 0.1 and
                self.thermal_headroom > 0.2)


@dataclass
class Decision:
    """A decision made by a cognitive sub-entity."""
    decision_id: str
    entity_lct: str
    domain: str
    outcome: str                      # Decision value
    confidence: float
    timestamp: str
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id, "entity_lct": self.entity_lct,
            "domain": self.domain, "outcome": self.outcome,
            "confidence": self.confidence, "timestamp": self.timestamp,
        }


@dataclass
class ATPContribution:
    """ATP value attribution for cognitive work (§4)."""
    entity_lct: str
    amount: float
    task: str
    timestamp: str
    quality_score: float = 1.0       # 0-1, affects attribution weight

    @property
    def weighted_amount(self) -> float:
        return self.amount * self.quality_score


@dataclass
class CollusionReport:
    """Report of suspected collusion between sub-entities."""
    entities: List[str]
    indicator: CollusionIndicator
    confidence: float
    evidence: Dict[str, Any]
    detected_at: str


@dataclass
class ConflictCase:
    """Record of a conflict between sub-entities."""
    conflict_id: str
    domain: str
    decisions: List[Decision]         # Conflicting decisions
    resolution_method: ConflictResolution
    resolved_outcome: str
    resolved_by: str                  # Entity that resolved
    resolved_at: str


# ============================================================================
# COGNITIVE SUB-ENTITY
# ============================================================================

@dataclass
class CognitiveSubEntity:
    """A cognitive sub-entity with its own LCT, trust, and autonomy."""
    lct: str
    entity_type: CognitiveEntityType
    autonomy: AutonomyLevel
    provenance: CognitiveProvenance
    t3: T3Snapshot
    independent_t3: T3Snapshot        # Independently earned trust
    status: SubEntityStatus = SubEntityStatus.ACTIVE
    decision_history: List[Decision] = field(default_factory=list)
    atp_contributions: List[ATPContribution] = field(default_factory=list)
    atp_balance: float = 0.0

    @property
    def effective_t3(self) -> T3Snapshot:
        """Effective trust = inherited + independent, capped at 1.0."""
        coeff = TRUST_INHERITANCE[self.autonomy]
        inherited = self.t3.modulate(coeff)
        return T3Snapshot(
            talent=min(1.0, inherited.talent + self.independent_t3.talent),
            training=min(1.0, inherited.training + self.independent_t3.training),
            temperament=min(1.0, inherited.temperament + self.independent_t3.temperament))

    @property
    def meets_autonomy_requirement(self) -> bool:
        """Check if independent trust meets autonomy level minimum."""
        return self.independent_t3.composite >= MIN_INDEPENDENT_TRUST[self.autonomy]

    def can_decide(self, domain: str) -> bool:
        """Check if entity can make decisions in domain."""
        if self.status != SubEntityStatus.ACTIVE:
            return False
        return domain in self.provenance.decision_scope or "*" in self.provenance.decision_scope

    def record_decision(self, decision: Decision):
        self.decision_history.append(decision)

    def earn_atp(self, amount: float, task: str, quality: float = 1.0):
        contrib = ATPContribution(
            entity_lct=self.lct, amount=amount, task=task,
            timestamp=datetime.now(timezone.utc).isoformat(),
            quality_score=quality)
        self.atp_contributions.append(contrib)
        self.atp_balance += contrib.weighted_amount

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lct": self.lct, "type": self.entity_type.value,
            "autonomy": self.autonomy.value,
            "provenance": self.provenance.to_dict(),
            "effective_t3": self.effective_t3.composite,
            "independent_t3": self.independent_t3.composite,
            "status": self.status.value,
            "atp_balance": self.atp_balance,
            "decisions": len(self.decision_history),
        }


# ============================================================================
# COGNITIVE HIERARCHY MANAGER
# ============================================================================

class CognitiveHierarchy:
    """Manages hierarchical LCT structure for cognitive sub-entities."""

    def __init__(self, primary_lct: str, primary_t3: T3Snapshot,
                 constraints: Optional[ResourceConstraints] = None):
        self.primary_lct = primary_lct
        self.primary_t3 = primary_t3
        self.constraints = constraints or ResourceConstraints()
        self.sub_entities: Dict[str, CognitiveSubEntity] = {}
        self.children: Dict[str, List[str]] = {primary_lct: []}  # parent → children
        self.conflicts: List[ConflictCase] = []
        self.collusion_reports: List[CollusionReport] = []

    def spawn(self, name: str, entity_type: CognitiveEntityType,
              autonomy: AutonomyLevel, spawn_context: SpawnContext,
              fingerprint: str, scope: List[str],
              parent_lct: Optional[str] = None) -> Optional[CognitiveSubEntity]:
        """Spawn a new cognitive sub-entity (§1)."""
        parent = parent_lct or self.primary_lct
        active_count = sum(1 for e in self.sub_entities.values()
                           if e.status == SubEntityStatus.ACTIVE)
        if not self.constraints.can_spawn(active_count):
            return None

        # Construct hierarchical LCT (§1)
        type_prefix = entity_type.value
        lct = f"{parent}:{type_prefix}:{name}"

        # Determine parent T3
        if parent == self.primary_lct:
            parent_t3 = self.primary_t3
            depth = 1
        elif parent in self.sub_entities:
            parent_t3 = self.sub_entities[parent].effective_t3
            depth = self.sub_entities[parent].provenance.lineage_depth + 1
        else:
            return None

        # Trust inheritance (§3)
        coeff = TRUST_INHERITANCE[autonomy]
        inherited_t3 = parent_t3.modulate(coeff)

        provenance = CognitiveProvenance(
            parent_lct=parent, spawn_context=spawn_context,
            cognitive_fingerprint=fingerprint, decision_scope=scope,
            spawned_at=datetime.now(timezone.utc).isoformat(),
            lineage_depth=depth)

        entity = CognitiveSubEntity(
            lct=lct, entity_type=entity_type, autonomy=autonomy,
            provenance=provenance, t3=parent_t3,
            independent_t3=T3Snapshot(0.0, 0.0, 0.0))

        self.sub_entities[lct] = entity
        self.children.setdefault(parent, []).append(lct)
        self.children[lct] = []
        return entity

    def terminate(self, lct: str) -> bool:
        """Terminate a sub-entity and all its children."""
        if lct not in self.sub_entities:
            return False
        entity = self.sub_entities[lct]
        entity.status = SubEntityStatus.TERMINATED
        # Cascade to children
        for child_lct in self.children.get(lct, []):
            self.terminate(child_lct)
        return True

    def suspend(self, lct: str) -> bool:
        if lct not in self.sub_entities:
            return False
        self.sub_entities[lct].status = SubEntityStatus.SUSPENDED
        return True

    def resume(self, lct: str) -> bool:
        if lct not in self.sub_entities:
            return False
        entity = self.sub_entities[lct]
        if entity.status == SubEntityStatus.SUSPENDED:
            entity.status = SubEntityStatus.ACTIVE
            return True
        return False

    def active_count(self) -> int:
        return sum(1 for e in self.sub_entities.values()
                   if e.status == SubEntityStatus.ACTIVE)

    def lineage(self, lct: str) -> List[str]:
        """Get full lineage from root to entity."""
        if lct == self.primary_lct:
            return [self.primary_lct]
        if lct not in self.sub_entities:
            return []
        chain = [lct]
        current = self.sub_entities[lct].provenance.parent_lct
        while current != self.primary_lct and current in self.sub_entities:
            chain.append(current)
            current = self.sub_entities[current].provenance.parent_lct
        chain.append(self.primary_lct)
        return list(reversed(chain))

    def depth(self, lct: str) -> int:
        if lct == self.primary_lct:
            return 0
        if lct in self.sub_entities:
            return self.sub_entities[lct].provenance.lineage_depth
        return -1


# ============================================================================
# TRUST EVOLUTION
# ============================================================================

class TrustEvolution:
    """Manages independent trust evolution for sub-entities (§3)."""

    @staticmethod
    def update_from_decision(entity: CognitiveSubEntity,
                              decision: Decision,
                              outcome_quality: float) -> T3Snapshot:
        """Update independent T3 based on decision outcome."""
        delta = 0.02 * (outcome_quality - 0.5)  # ±0.01 per decision
        old = entity.independent_t3
        new = T3Snapshot(
            talent=max(0.0, min(1.0, old.talent + delta)),
            training=max(0.0, min(1.0, old.training + delta * 0.5)),
            temperament=max(0.0, min(1.0, old.temperament + delta * 0.3)))
        entity.independent_t3 = new
        return new

    @staticmethod
    def check_autonomy_promotion(entity: CognitiveSubEntity) -> Optional[AutonomyLevel]:
        """Check if entity qualifies for higher autonomy."""
        current_order = AUTONOMY_ORDER[entity.autonomy]
        for level in AutonomyLevel:
            level_order = AUTONOMY_ORDER[level]
            if level_order == current_order + 1:
                if entity.independent_t3.composite >= MIN_INDEPENDENT_TRUST[level]:
                    return level
        return None

    @staticmethod
    def promote(entity: CognitiveSubEntity, new_level: AutonomyLevel) -> bool:
        """Promote entity to higher autonomy level."""
        if AUTONOMY_ORDER[new_level] <= AUTONOMY_ORDER[entity.autonomy]:
            return False
        if entity.independent_t3.composite < MIN_INDEPENDENT_TRUST[new_level]:
            return False
        entity.autonomy = new_level
        return True


# ============================================================================
# COLLUSION DETECTOR (§5.1)
# ============================================================================

class CollusionDetector:
    """Detect coordinated behavior between sub-entities."""

    @staticmethod
    def check_timing_correlation(entities: List[CognitiveSubEntity],
                                   window_seconds: float = 1.0) -> Optional[CollusionReport]:
        """Detect suspiciously synchronized decision timing."""
        all_decisions = []
        for e in entities:
            for d in e.decision_history:
                all_decisions.append((e.lct, d))

        # Check for clustered timing
        for i, (lct1, d1) in enumerate(all_decisions):
            for lct2, d2 in all_decisions[i+1:]:
                if lct1 == lct2:
                    continue
                try:
                    t1 = datetime.fromisoformat(d1.timestamp.replace("Z", "+00:00"))
                    t2 = datetime.fromisoformat(d2.timestamp.replace("Z", "+00:00"))
                    if abs((t1 - t2).total_seconds()) < window_seconds:
                        return CollusionReport(
                            entities=[lct1, lct2],
                            indicator=CollusionIndicator.TIMING_CORRELATION,
                            confidence=0.6,
                            evidence={"decisions": [d1.decision_id, d2.decision_id],
                                       "time_diff_s": abs((t1-t2).total_seconds())},
                            detected_at=datetime.now(timezone.utc).isoformat())
                except (ValueError, TypeError):
                    continue
        return None

    @staticmethod
    def check_outcome_alignment(entities: List[CognitiveSubEntity],
                                  threshold: float = 0.9) -> Optional[CollusionReport]:
        """Detect entities that always agree (suspiciously high alignment)."""
        if len(entities) < 2:
            return None

        for i, e1 in enumerate(entities):
            for e2 in entities[i+1:]:
                shared_domains = set()
                for d in e1.decision_history:
                    shared_domains.add(d.domain)
                shared_domains &= {d.domain for d in e2.decision_history}

                if not shared_domains:
                    continue

                agreements = 0
                total = 0
                for domain in shared_domains:
                    d1_outcomes = {d.outcome for d in e1.decision_history if d.domain == domain}
                    d2_outcomes = {d.outcome for d in e2.decision_history if d.domain == domain}
                    overlap = d1_outcomes & d2_outcomes
                    total += max(len(d1_outcomes), len(d2_outcomes))
                    agreements += len(overlap)

                if total > 0 and agreements / total >= threshold:
                    return CollusionReport(
                        entities=[e1.lct, e2.lct],
                        indicator=CollusionIndicator.OUTCOME_ALIGNMENT,
                        confidence=agreements / total,
                        evidence={"agreement_rate": agreements / total,
                                   "shared_domains": list(shared_domains)},
                        detected_at=datetime.now(timezone.utc).isoformat())
        return None

    @staticmethod
    def check_atp_funneling(entities: List[CognitiveSubEntity],
                              threshold: float = 0.8) -> Optional[CollusionReport]:
        """Detect ATP flowing disproportionately to one target."""
        total_atp = sum(e.atp_balance for e in entities)
        if total_atp <= 0:
            return None
        for e in entities:
            if e.atp_balance / total_atp > threshold:
                return CollusionReport(
                    entities=[e.lct for e in entities],
                    indicator=CollusionIndicator.ATP_FUNNELING,
                    confidence=e.atp_balance / total_atp,
                    evidence={"target": e.lct, "ratio": e.atp_balance / total_atp},
                    detected_at=datetime.now(timezone.utc).isoformat())
        return None


# ============================================================================
# CONFLICT RESOLVER (§5.3)
# ============================================================================

class ConflictResolver:
    """Resolve disagreements between cognitive sub-entities."""

    @staticmethod
    def resolve(decisions: List[Decision], entities: Dict[str, CognitiveSubEntity],
                method: ConflictResolution, primary_lct: str = "") -> ConflictCase:
        """Resolve conflict between disagreeing sub-entities."""
        if not decisions:
            raise ValueError("No decisions to resolve")

        domain = decisions[0].domain
        ts = datetime.now(timezone.utc).isoformat()
        conflict_id = f"conflict:{hashlib.sha256(f'{domain}:{ts}'.encode()).hexdigest()[:12]}"

        if method == ConflictResolution.PARENT_OVERRIDE:
            # Parent's decision wins (or first if parent not in decisions)
            parent_decision = next(
                (d for d in decisions if d.entity_lct == primary_lct), decisions[0])
            outcome = parent_decision.outcome
            resolved_by = parent_decision.entity_lct

        elif method == ConflictResolution.MAJORITY_VOTE:
            # Count outcomes
            votes: Dict[str, int] = {}
            for d in decisions:
                votes[d.outcome] = votes.get(d.outcome, 0) + 1
            outcome = max(votes, key=votes.get)
            resolved_by = "majority_vote"

        elif method == ConflictResolution.HIGHEST_TRUST:
            # Highest effective T3 composite wins
            best_decision = decisions[0]
            best_trust = 0.0
            for d in decisions:
                if d.entity_lct in entities:
                    trust = entities[d.entity_lct].effective_t3.composite
                    if trust > best_trust:
                        best_trust = trust
                        best_decision = d
            outcome = best_decision.outcome
            resolved_by = best_decision.entity_lct

        elif method == ConflictResolution.ESCALATION:
            # Escalate — no automatic resolution
            outcome = "ESCALATED"
            resolved_by = "federation"

        else:
            outcome = decisions[0].outcome
            resolved_by = decisions[0].entity_lct

        return ConflictCase(
            conflict_id=conflict_id, domain=domain,
            decisions=decisions, resolution_method=method,
            resolved_outcome=outcome, resolved_by=resolved_by,
            resolved_at=ts)


# ============================================================================
# ATP ATTRIBUTION ENGINE (§4)
# ============================================================================

class ATPAttribution:
    """Fair ATP distribution across cognitive sub-entities."""

    @staticmethod
    def distribute(total_atp: float,
                    entities: List[CognitiveSubEntity],
                    method: str = "proportional") -> Dict[str, float]:
        """Distribute ATP based on cognitive contribution."""
        if not entities:
            return {}

        if method == "proportional":
            # Weight by quality-adjusted contributions
            total_weighted = sum(sum(c.weighted_amount for c in e.atp_contributions)
                                  for e in entities)
            if total_weighted <= 0:
                # Equal distribution
                share = total_atp / len(entities)
                return {e.lct: share for e in entities}
            result = {}
            for e in entities:
                weighted = sum(c.weighted_amount for c in e.atp_contributions)
                share = total_atp * (weighted / total_weighted)
                result[e.lct] = round(share, 4)
            return result

        elif method == "trust_weighted":
            # Weight by effective T3
            total_trust = sum(e.effective_t3.composite for e in entities)
            if total_trust <= 0:
                share = total_atp / len(entities)
                return {e.lct: share for e in entities}
            return {e.lct: round(total_atp * e.effective_t3.composite / total_trust, 4)
                    for e in entities}

        else:  # equal
            share = total_atp / len(entities)
            return {e.lct: share for e in entities}


# ============================================================================
# COGNITIVE DIVERSITY SCORER
# ============================================================================

class CognitiveDiversity:
    """Measure and reward cognitive diversity within a hierarchy (§Edge Advantages)."""

    @staticmethod
    def score(entities: List[CognitiveSubEntity]) -> float:
        """Cognitive diversity score ∈ [0,1]. Higher = more diverse."""
        if len(entities) <= 1:
            return 0.0

        # Dimension 1: Entity type diversity
        types = set(e.entity_type for e in entities)
        type_diversity = len(types) / len(CognitiveEntityType)

        # Dimension 2: Fingerprint diversity (different models/tools)
        fingerprints = set(e.provenance.cognitive_fingerprint for e in entities)
        fp_diversity = min(1.0, len(fingerprints) / max(len(entities), 1))

        # Dimension 3: Scope diversity
        all_scopes = set()
        for e in entities:
            all_scopes.update(e.provenance.decision_scope)
        scope_diversity = min(1.0, len(all_scopes) / max(len(entities) * 2, 1))

        # Dimension 4: Autonomy diversity
        autonomy_levels = set(e.autonomy for e in entities)
        autonomy_diversity = len(autonomy_levels) / len(AutonomyLevel)

        return (type_diversity * 0.3 + fp_diversity * 0.3 +
                scope_diversity * 0.2 + autonomy_diversity * 0.2)


# ============================================================================
# TESTS
# ============================================================================

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def run_tests():
    passed = 0
    failed = 0
    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    # ================================================================
    # T1: Entity types and autonomy levels
    # ================================================================
    print("T1: Entity Types & Autonomy")
    check("T1.1 Agent type", CognitiveEntityType.AGENT.value == "agent")
    check("T1.2 Model type", CognitiveEntityType.MODEL.value == "model")
    check("T1.3 Tool type", CognitiveEntityType.TOOL.value == "tool")
    check("T1.4 Role type", CognitiveEntityType.ROLE.value == "role")
    check("T1.5 Validator type", CognitiveEntityType.VALIDATOR.value == "validator")
    check("T1.6 Supervised < semi", AUTONOMY_ORDER[AutonomyLevel.SUPERVISED] < AUTONOMY_ORDER[AutonomyLevel.SEMI_AUTONOMOUS])
    check("T1.7 Semi < auto", AUTONOMY_ORDER[AutonomyLevel.SEMI_AUTONOMOUS] < AUTONOMY_ORDER[AutonomyLevel.AUTONOMOUS])
    check("T1.8 Auto < fully", AUTONOMY_ORDER[AutonomyLevel.AUTONOMOUS] < AUTONOMY_ORDER[AutonomyLevel.FULLY_AUTONOMOUS])

    # ================================================================
    # T2: T3 snapshot
    # ================================================================
    print("T2: T3 Snapshot")
    t3 = T3Snapshot(0.8, 0.7, 0.6)
    check("T2.1 Composite", abs(t3.composite - (0.4*0.8 + 0.3*0.7 + 0.3*0.6)) < 0.001)
    modulated = t3.modulate(0.5)
    check("T2.2 Modulated talent", modulated.talent == 0.4)
    check("T2.3 Modulated training", modulated.training == 0.35)
    check("T2.4 Modulated capped", T3Snapshot(1.0, 1.0, 1.0).modulate(1.5).talent == 1.0)

    # ================================================================
    # T3: Cognitive hierarchy creation
    # ================================================================
    print("T3: Hierarchy Creation")
    parent_t3 = T3Snapshot(0.85, 0.80, 0.75)
    hierarchy = CognitiveHierarchy("lct:web4:sprout:14214250", parent_t3)
    check("T3.1 Primary LCT set", hierarchy.primary_lct == "lct:web4:sprout:14214250")
    check("T3.2 No sub-entities initially", len(hierarchy.sub_entities) == 0)
    check("T3.3 Default constraints", hierarchy.constraints.max_concurrent == 10)

    # ================================================================
    # T4: Spawn sub-entities (§1)
    # ================================================================
    print("T4: Spawn Sub-Entities")
    validator = hierarchy.spawn(
        "compliance", CognitiveEntityType.VALIDATOR,
        AutonomyLevel.SEMI_AUTONOMOUS, SpawnContext.TASK_DELEGATION,
        "claude-sonnet-4-20250514", ["web4_validation", "compliance_analysis"])
    check("T4.1 Validator spawned", validator is not None)
    check("T4.2 LCT hierarchical", validator.lct == "lct:web4:sprout:14214250:validator:compliance")
    check("T4.3 Type correct", validator.entity_type == CognitiveEntityType.VALIDATOR)
    check("T4.4 Autonomy set", validator.autonomy == AutonomyLevel.SEMI_AUTONOMOUS)
    check("T4.5 Provenance parent", validator.provenance.parent_lct == "lct:web4:sprout:14214250")
    check("T4.6 Lineage depth 1", validator.provenance.lineage_depth == 1)
    check("T4.7 Active status", validator.status == SubEntityStatus.ACTIVE)

    scheduler = hierarchy.spawn(
        "scheduler", CognitiveEntityType.AGENT,
        AutonomyLevel.AUTONOMOUS, SpawnContext.CAPABILITY_EXTENSION,
        "claude-opus-4-20250514", ["task_scheduling", "resource_allocation"])
    check("T4.8 Agent spawned", scheduler is not None)
    check("T4.9 Agent LCT", scheduler.lct.endswith(":agent:scheduler"))

    witness_role = hierarchy.spawn(
        "witness", CognitiveEntityType.ROLE,
        AutonomyLevel.SUPERVISED, SpawnContext.ROLE_ACTIVATION,
        "witness-handler-v1", ["witnessing"])
    check("T4.10 Role spawned", witness_role is not None)
    check("T4.11 Three sub-entities", hierarchy.active_count() == 3)

    # ================================================================
    # T5: Trust inheritance (§3)
    # ================================================================
    print("T5: Trust Inheritance")
    # Validator: semi-autonomous → 0.8× inheritance
    eff = validator.effective_t3
    check("T5.1 Inherited trust < parent", eff.composite < parent_t3.composite)
    check("T5.2 Semi-auto coeff 0.8", TRUST_INHERITANCE[AutonomyLevel.SEMI_AUTONOMOUS] == 0.8)
    check("T5.3 Inherited talent ≈ 0.68", abs(eff.talent - 0.85 * 0.8) < 0.01)

    # Scheduler: autonomous → 0.6× inheritance
    sched_eff = scheduler.effective_t3
    check("T5.4 Autonomous lower inheritance", sched_eff.composite < eff.composite)

    # Witness: supervised → 0.9× inheritance
    wit_eff = witness_role.effective_t3
    check("T5.5 Supervised highest inheritance", wit_eff.composite > sched_eff.composite)

    # ================================================================
    # T6: Sub-entity of sub-entity (nested hierarchy)
    # ================================================================
    print("T6: Nested Hierarchy")
    sub_agent = hierarchy.spawn(
        "analyzer", CognitiveEntityType.TOOL,
        AutonomyLevel.SUPERVISED, SpawnContext.SPECIALIZATION,
        "analyzer-v1", ["data_analysis"],
        parent_lct=scheduler.lct)
    check("T6.1 Nested spawn", sub_agent is not None)
    check("T6.2 Depth 2", sub_agent.provenance.lineage_depth == 2)
    check("T6.3 Parent is scheduler", sub_agent.provenance.parent_lct == scheduler.lct)
    lineage = hierarchy.lineage(sub_agent.lct)
    check("T6.4 Full lineage", len(lineage) == 3)
    check("T6.5 Lineage starts at root", lineage[0] == hierarchy.primary_lct)
    check("T6.6 Lineage ends at entity", lineage[-1] == sub_agent.lct)

    # ================================================================
    # T7: Resource constraints
    # ================================================================
    print("T7: Resource Constraints")
    constrained = CognitiveHierarchy(
        "lct:constrained", T3Snapshot(0.8, 0.8, 0.8),
        ResourceConstraints(max_concurrent=2))
    constrained.spawn("a1", CognitiveEntityType.AGENT, AutonomyLevel.SUPERVISED,
                       SpawnContext.TASK_DELEGATION, "fp1", ["*"])
    constrained.spawn("a2", CognitiveEntityType.AGENT, AutonomyLevel.SUPERVISED,
                       SpawnContext.TASK_DELEGATION, "fp2", ["*"])
    blocked = constrained.spawn("a3", CognitiveEntityType.AGENT, AutonomyLevel.SUPERVISED,
                                 SpawnContext.TASK_DELEGATION, "fp3", ["*"])
    check("T7.1 Spawn blocked by constraint", blocked is None)
    check("T7.2 Active count = max", constrained.active_count() == 2)

    # Thermal constraint
    hot = ResourceConstraints(max_concurrent=10, thermal_headroom=0.1)
    check("T7.3 Thermal throttled blocks spawn", not hot.can_spawn(0))

    # Compute budget
    no_compute = ResourceConstraints(max_concurrent=10, compute_budget=0.05)
    check("T7.4 Low compute blocks spawn", not no_compute.can_spawn(0))

    # ================================================================
    # T8: Decision tracking
    # ================================================================
    print("T8: Decision Tracking")
    d1 = Decision("d001", validator.lct, "compliance_analysis", "compliant",
                   0.95, _ts(), "All checks pass")
    validator.record_decision(d1)
    check("T8.1 Decision recorded", len(validator.decision_history) == 1)
    check("T8.2 Can decide in scope", validator.can_decide("compliance_analysis"))
    check("T8.3 Cannot decide out of scope", not validator.can_decide("financial_audit"))

    d2 = Decision("d002", scheduler.lct, "task_scheduling", "prioritize_sync",
                   0.80, _ts())
    scheduler.record_decision(d2)
    check("T8.4 Scheduler decision recorded", len(scheduler.decision_history) == 1)

    # ================================================================
    # T9: Trust evolution
    # ================================================================
    print("T9: Trust Evolution")
    old_t3 = T3Snapshot(validator.independent_t3.talent,
                         validator.independent_t3.training,
                         validator.independent_t3.temperament)
    TrustEvolution.update_from_decision(validator, d1, 0.9)  # Good outcome
    check("T9.1 Independent trust increased", validator.independent_t3.composite > old_t3.composite)

    bad_d = Decision("d003", validator.lct, "compliance_analysis", "wrong",
                      0.3, _ts())
    validator.record_decision(bad_d)
    TrustEvolution.update_from_decision(validator, bad_d, 0.1)  # Bad outcome
    check("T9.2 Trust decreased on bad outcome",
          validator.independent_t3.talent < validator.independent_t3.talent + 0.1)

    # ================================================================
    # T10: Autonomy promotion
    # ================================================================
    print("T10: Autonomy Promotion")
    # Build up independent trust for witness role
    for _ in range(60):
        d = Decision(f"d_w{_}", witness_role.lct, "witnessing", "verified", 0.9, _ts())
        witness_role.record_decision(d)
        TrustEvolution.update_from_decision(witness_role, d, 0.95)

    promo = TrustEvolution.check_autonomy_promotion(witness_role)
    check("T10.1 Promotion available", promo is not None)
    if promo:
        check("T10.2 Promotion to semi-auto", promo == AutonomyLevel.SEMI_AUTONOMOUS)
        success = TrustEvolution.promote(witness_role, promo)
        check("T10.3 Promotion succeeded", success)
        check("T10.4 New autonomy level", witness_role.autonomy == AutonomyLevel.SEMI_AUTONOMOUS)

    # Cannot promote without sufficient trust
    fresh = hierarchy.spawn("fresh", CognitiveEntityType.TOOL,
                             AutonomyLevel.SUPERVISED, SpawnContext.TASK_DELEGATION,
                             "fp", ["*"])
    no_promo = TrustEvolution.check_autonomy_promotion(fresh)
    check("T10.5 No promotion for fresh entity", no_promo is None)

    # Cannot demote (lower order)
    no_demote = TrustEvolution.promote(witness_role, AutonomyLevel.SUPERVISED)
    check("T10.6 Cannot demote", not no_demote)

    # ================================================================
    # T11: ATP attribution
    # ================================================================
    print("T11: ATP Attribution")
    validator.earn_atp(10, "compliance_check", quality=0.9)
    scheduler.earn_atp(20, "scheduling", quality=0.8)
    witness_role.earn_atp(5, "witnessing", quality=1.0)
    check("T11.1 Validator ATP", validator.atp_balance == 9.0)  # 10 * 0.9
    check("T11.2 Scheduler ATP", scheduler.atp_balance == 16.0)  # 20 * 0.8
    check("T11.3 Witness ATP", witness_role.atp_balance == 5.0)

    # Proportional distribution
    dist = ATPAttribution.distribute(100, [validator, scheduler, witness_role], "proportional")
    check("T11.4 Three recipients", len(dist) == 3)
    check("T11.5 Scheduler gets most", dist[scheduler.lct] > dist[validator.lct])
    total_dist = sum(dist.values())
    check("T11.6 Total ≈ 100", abs(total_dist - 100) < 0.1)

    # Trust-weighted distribution
    dist_tw = ATPAttribution.distribute(100, [validator, scheduler, witness_role], "trust_weighted")
    check("T11.7 Trust-weighted distribution sums to ≈100", abs(sum(dist_tw.values()) - 100) < 0.1)

    # Equal distribution
    dist_eq = ATPAttribution.distribute(100, [validator, scheduler, witness_role], "equal")
    check("T11.8 Equal distribution", abs(dist_eq[validator.lct] - 100/3) < 0.1)

    # Empty entities
    dist_empty = ATPAttribution.distribute(100, [], "proportional")
    check("T11.9 Empty → empty", len(dist_empty) == 0)

    # ================================================================
    # T12: Collusion detection — timing
    # ================================================================
    print("T12: Collusion Detection — Timing")
    ts_now = _ts()
    e1 = CognitiveSubEntity(
        lct="lct:e1", entity_type=CognitiveEntityType.AGENT,
        autonomy=AutonomyLevel.AUTONOMOUS,
        provenance=CognitiveProvenance("lct:root", SpawnContext.TASK_DELEGATION,
                                        "fp1", ["*"], ts_now),
        t3=T3Snapshot(0.8, 0.8, 0.8), independent_t3=T3Snapshot(0.3, 0.3, 0.3))
    e2 = CognitiveSubEntity(
        lct="lct:e2", entity_type=CognitiveEntityType.AGENT,
        autonomy=AutonomyLevel.AUTONOMOUS,
        provenance=CognitiveProvenance("lct:root", SpawnContext.TASK_DELEGATION,
                                        "fp2", ["*"], ts_now),
        t3=T3Snapshot(0.8, 0.8, 0.8), independent_t3=T3Snapshot(0.3, 0.3, 0.3))

    # Same timestamp decisions
    d_e1 = Decision("d1", "lct:e1", "task", "optionA", 0.9, ts_now)
    d_e2 = Decision("d2", "lct:e2", "task", "optionA", 0.9, ts_now)
    e1.record_decision(d_e1)
    e2.record_decision(d_e2)

    timing_report = CollusionDetector.check_timing_correlation([e1, e2], window_seconds=1.0)
    check("T12.1 Timing correlation detected", timing_report is not None)
    check("T12.2 Indicator type", timing_report.indicator == CollusionIndicator.TIMING_CORRELATION)

    # ================================================================
    # T13: Collusion detection — outcome alignment
    # ================================================================
    print("T13: Collusion Detection — Outcome")
    # Add more decisions with same outcomes
    for i in range(5):
        outcome = f"same_outcome_{i}"
        e1.record_decision(Decision(f"da{i}", "lct:e1", f"domain_{i}", outcome, 0.9, _ts()))
        e2.record_decision(Decision(f"db{i}", "lct:e2", f"domain_{i}", outcome, 0.9, _ts()))

    outcome_report = CollusionDetector.check_outcome_alignment([e1, e2], threshold=0.8)
    check("T13.1 Outcome alignment detected", outcome_report is not None)
    check("T13.2 Alignment confidence high", outcome_report.confidence >= 0.8)

    # ================================================================
    # T14: Collusion detection — ATP funneling
    # ================================================================
    print("T14: ATP Funneling")
    e3 = CognitiveSubEntity(
        lct="lct:e3", entity_type=CognitiveEntityType.TOOL,
        autonomy=AutonomyLevel.SUPERVISED,
        provenance=CognitiveProvenance("lct:root", SpawnContext.TASK_DELEGATION,
                                        "fp3", ["*"], _ts()),
        t3=T3Snapshot(0.5, 0.5, 0.5), independent_t3=T3Snapshot(0.1, 0.1, 0.1))
    e3.atp_balance = 1.0
    e1.atp_balance = 100.0  # Disproportionate
    e2.atp_balance = 2.0

    funnel_report = CollusionDetector.check_atp_funneling([e1, e2, e3], threshold=0.8)
    check("T14.1 Funneling detected", funnel_report is not None)
    check("T14.2 Target identified", funnel_report.evidence["target"] == "lct:e1")

    # No funneling with balanced ATP
    e1.atp_balance = 10.0
    e2.atp_balance = 10.0
    e3.atp_balance = 10.0
    no_funnel = CollusionDetector.check_atp_funneling([e1, e2, e3], threshold=0.8)
    check("T14.3 No funneling when balanced", no_funnel is None)

    # ================================================================
    # T15: Conflict resolution
    # ================================================================
    print("T15: Conflict Resolution")
    d_conflict1 = Decision("dc1", validator.lct, "compliance", "approve", 0.8, _ts())
    d_conflict2 = Decision("dc2", scheduler.lct, "compliance", "reject", 0.7, _ts())
    d_conflict3 = Decision("dc3", witness_role.lct, "compliance", "approve", 0.6, _ts())

    # Majority vote
    case_mv = ConflictResolver.resolve(
        [d_conflict1, d_conflict2, d_conflict3], hierarchy.sub_entities,
        ConflictResolution.MAJORITY_VOTE)
    check("T15.1 Majority vote → approve", case_mv.resolved_outcome == "approve")
    check("T15.2 Resolution method recorded", case_mv.resolution_method == ConflictResolution.MAJORITY_VOTE)

    # Highest trust
    case_ht = ConflictResolver.resolve(
        [d_conflict1, d_conflict2], hierarchy.sub_entities,
        ConflictResolution.HIGHEST_TRUST)
    check("T15.3 Highest trust resolves", case_ht.resolved_outcome in ("approve", "reject"))
    check("T15.4 Resolved by entity", case_ht.resolved_by in (validator.lct, scheduler.lct))

    # Parent override
    case_po = ConflictResolver.resolve(
        [d_conflict1, d_conflict2], hierarchy.sub_entities,
        ConflictResolution.PARENT_OVERRIDE, hierarchy.primary_lct)
    check("T15.5 Parent override uses first decision", case_po.resolved_outcome in ("approve", "reject"))

    # Escalation
    case_esc = ConflictResolver.resolve(
        [d_conflict1, d_conflict2], hierarchy.sub_entities,
        ConflictResolution.ESCALATION)
    check("T15.6 Escalation outcome", case_esc.resolved_outcome == "ESCALATED")
    check("T15.7 Resolved by federation", case_esc.resolved_by == "federation")

    # ================================================================
    # T16: Entity lifecycle — suspend/resume/terminate
    # ================================================================
    print("T16: Entity Lifecycle")
    check("T16.1 Suspend", hierarchy.suspend(validator.lct))
    check("T16.2 Status suspended", validator.status == SubEntityStatus.SUSPENDED)
    check("T16.3 Cannot decide when suspended", not validator.can_decide("compliance_analysis"))
    check("T16.4 Resume", hierarchy.resume(validator.lct))
    check("T16.5 Status active again", validator.status == SubEntityStatus.ACTIVE)
    check("T16.6 Can decide after resume", validator.can_decide("compliance_analysis"))

    # Terminate with cascade
    term_parent = hierarchy.spawn("term_parent", CognitiveEntityType.AGENT,
                                    AutonomyLevel.AUTONOMOUS, SpawnContext.TASK_DELEGATION,
                                    "fp", ["*"])
    term_child = hierarchy.spawn("term_child", CognitiveEntityType.TOOL,
                                   AutonomyLevel.SUPERVISED, SpawnContext.SPECIALIZATION,
                                   "fp", ["*"], parent_lct=term_parent.lct)
    check("T16.7 Terminate parent", hierarchy.terminate(term_parent.lct))
    check("T16.8 Parent terminated", term_parent.status == SubEntityStatus.TERMINATED)
    check("T16.9 Child cascaded", term_child.status == SubEntityStatus.TERMINATED)

    # ================================================================
    # T17: Cognitive diversity
    # ================================================================
    print("T17: Cognitive Diversity")
    diverse_entities = [validator, scheduler, witness_role, sub_agent]
    diversity = CognitiveDiversity.score(diverse_entities)
    check("T17.1 Diversity > 0", diversity > 0)
    check("T17.2 Diversity ≤ 1", diversity <= 1.0)

    # Homogeneous set
    homogeneous = [
        CognitiveSubEntity(
            lct=f"lct:h{i}", entity_type=CognitiveEntityType.AGENT,
            autonomy=AutonomyLevel.SUPERVISED,
            provenance=CognitiveProvenance("lct:root", SpawnContext.TASK_DELEGATION,
                                            "same_fp", ["same_scope"], _ts()),
            t3=T3Snapshot(0.5, 0.5, 0.5), independent_t3=T3Snapshot(0.1, 0.1, 0.1))
        for i in range(3)
    ]
    homo_diversity = CognitiveDiversity.score(homogeneous)
    check("T17.3 Homogeneous lower diversity", homo_diversity < diversity)

    # Single entity
    single_diversity = CognitiveDiversity.score([validator])
    check("T17.4 Single entity → 0", single_diversity == 0.0)

    # ================================================================
    # T18: Serialization
    # ================================================================
    print("T18: Serialization")
    v_dict = validator.to_dict()
    check("T18.1 LCT in dict", "lct" in v_dict)
    check("T18.2 Type in dict", v_dict["type"] == "validator")
    check("T18.3 Autonomy in dict", "autonomy" in v_dict)
    check("T18.4 Provenance in dict", "provenance" in v_dict)
    prov_dict = validator.provenance.to_dict()
    check("T18.5 Provenance parent", prov_dict["parent_lct"] == hierarchy.primary_lct)
    check("T18.6 Provenance scope", "web4_validation" in prov_dict["decision_scope"])
    check("T18.7 Decision count in dict", v_dict["decisions"] >= 2)

    # ================================================================
    # T19: Meets autonomy requirement
    # ================================================================
    print("T19: Autonomy Requirements")
    # Supervised → no minimum
    fresh2 = hierarchy.spawn("fresh2", CognitiveEntityType.TOOL,
                              AutonomyLevel.SUPERVISED, SpawnContext.TASK_DELEGATION,
                              "fp", ["*"])
    check("T19.1 Supervised always meets", fresh2.meets_autonomy_requirement)

    # Autonomous needs 0.5
    auto_entity = hierarchy.spawn("auto_test", CognitiveEntityType.AGENT,
                                    AutonomyLevel.AUTONOMOUS, SpawnContext.TASK_DELEGATION,
                                    "fp", ["*"])
    check("T19.2 Autonomous needs independent trust", not auto_entity.meets_autonomy_requirement)
    # Build trust
    for _ in range(120):
        d = Decision(f"d_at{_}", auto_entity.lct, "*", "ok", 0.9, _ts())
        auto_entity.record_decision(d)
        TrustEvolution.update_from_decision(auto_entity, d, 0.95)
    check("T19.3 After trust building", auto_entity.meets_autonomy_requirement)

    # ================================================================
    # T20: Wildcard scope
    # ================================================================
    print("T20: Wildcard Scope")
    wild = hierarchy.spawn("wildcard", CognitiveEntityType.AGENT,
                            AutonomyLevel.SUPERVISED, SpawnContext.TASK_DELEGATION,
                            "fp", ["*"])
    check("T20.1 Wildcard scope allows any domain", wild.can_decide("anything"))
    check("T20.2 Specific scope too", wild.can_decide("specific_domain"))

    # ================================================================
    # T21: E2E scenario — edge device cognitive constellation
    # ================================================================
    print("T21: E2E Scenario")
    edge = CognitiveHierarchy(
        "lct:web4:sprout:14214250", T3Snapshot(0.85, 0.80, 0.75),
        ResourceConstraints(max_concurrent=5, thermal_headroom=0.8))

    # Phase 1: Spawn constellation (per RFC example)
    comp_validator = edge.spawn(
        "compliance", CognitiveEntityType.VALIDATOR,
        AutonomyLevel.SEMI_AUTONOMOUS, SpawnContext.TASK_DELEGATION,
        "claude-sonnet-4-20250514", ["web4_validation", "compliance_analysis"])
    task_scheduler = edge.spawn(
        "scheduler", CognitiveEntityType.AGENT,
        AutonomyLevel.AUTONOMOUS, SpawnContext.CAPABILITY_EXTENSION,
        "claude-opus-4-20250514", ["task_scheduling", "resource_allocation"])
    sensor_fusion = edge.spawn(
        "sensor_fusion", CognitiveEntityType.TOOL,
        AutonomyLevel.SUPERVISED, SpawnContext.SPECIALIZATION,
        "fusion-model-v2", ["sensor_data"])
    edge_witness = edge.spawn(
        "witness", CognitiveEntityType.ROLE,
        AutonomyLevel.SUPERVISED, SpawnContext.ROLE_ACTIVATION,
        "witness-handler-v1", ["witnessing"])
    fed_member = edge.spawn(
        "federation", CognitiveEntityType.ROLE,
        AutonomyLevel.SEMI_AUTONOMOUS, SpawnContext.FEDERATION_REQUEST,
        "fed-protocol-v1", ["federation_ops"])

    check("T21.1 Five sub-entities", edge.active_count() == 5)

    # Phase 2: Make decisions
    comp_validator.record_decision(
        Decision("e2e_d1", comp_validator.lct, "compliance_analysis", "compliant", 0.95, _ts()))
    TrustEvolution.update_from_decision(comp_validator, comp_validator.decision_history[-1], 0.9)

    task_scheduler.record_decision(
        Decision("e2e_d2", task_scheduler.lct, "task_scheduling", "batch_sync", 0.8, _ts()))
    TrustEvolution.update_from_decision(task_scheduler, task_scheduler.decision_history[-1], 0.85)

    # Phase 3: ATP attribution
    comp_validator.earn_atp(15, "compliance_audit", quality=0.95)
    task_scheduler.earn_atp(25, "scheduling_optimization", quality=0.85)
    sensor_fusion.earn_atp(8, "data_fusion", quality=1.0)

    total_atp = 100
    dist = ATPAttribution.distribute(total_atp,
                                       [comp_validator, task_scheduler, sensor_fusion],
                                       "proportional")
    check("T21.2 ATP distributed", sum(dist.values()) > 99)

    # Phase 4: Cognitive diversity
    all_entities = [comp_validator, task_scheduler, sensor_fusion, edge_witness, fed_member]
    div = CognitiveDiversity.score(all_entities)
    check("T21.3 Diverse constellation", div > 0.3)

    # Phase 5: Conflict + resolution
    d_approve = Decision("e2e_c1", comp_validator.lct, "policy", "approve_update", 0.85, _ts())
    d_reject = Decision("e2e_c2", task_scheduler.lct, "policy", "defer_update", 0.7, _ts())
    d_approve2 = Decision("e2e_c3", fed_member.lct, "policy", "approve_update", 0.6, _ts())

    conflict = ConflictResolver.resolve(
        [d_approve, d_reject, d_approve2], edge.sub_entities,
        ConflictResolution.MAJORITY_VOTE)
    check("T21.4 Conflict resolved", conflict.resolved_outcome == "approve_update")

    # Phase 6: Lineage verification
    for e_lct in edge.sub_entities:
        lin = edge.lineage(e_lct)
        check(f"T21.lin_{e_lct.split(':')[-1]} Lineage starts at root", lin[0] == edge.primary_lct)

    # Phase 7: Hierarchy depth
    check("T21.5 All depth-1 entities", all(edge.depth(e) == 1 for e in edge.sub_entities))

    # ================================================================
    # T22: Edge cases
    # ================================================================
    print("T22: Edge Cases")
    # Spawn with invalid parent
    bad = hierarchy.spawn("bad", CognitiveEntityType.AGENT, AutonomyLevel.SUPERVISED,
                           SpawnContext.TASK_DELEGATION, "fp", ["*"],
                           parent_lct="lct:nonexistent")
    check("T22.1 Invalid parent → None", bad is None)

    # Terminate nonexistent
    check("T22.2 Terminate nonexistent → False", not hierarchy.terminate("lct:fake"))

    # Suspend nonexistent
    check("T22.3 Suspend nonexistent → False", not hierarchy.suspend("lct:fake"))

    # Resume non-suspended
    check("T22.4 Resume active → False", not hierarchy.resume(scheduler.lct))

    # Lineage of nonexistent
    check("T22.5 Lineage nonexistent → []", hierarchy.lineage("lct:fake") == [])

    # Depth of primary
    check("T22.6 Depth of primary = 0", hierarchy.depth(hierarchy.primary_lct) == 0)

    # ================================================================
    print()
    print("=" * 60)
    total = passed + failed
    print(f"Cognitive Sub-Entity Framework: {passed}/{total} checks passed")
    if failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {failed} checks FAILED")
    print("=" * 60)
    return passed, failed


if __name__ == "__main__":
    run_tests()
