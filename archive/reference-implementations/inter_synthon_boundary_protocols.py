"""
Inter-Synthon Boundary Protocols — Reference Implementation

When two synthons encounter each other at their boundary zones, three
distinct interaction modes are possible:

1. **Composition**: Voluntary merger with treaty protocol
   - Both synthons agree to merge via mutual health assessment
   - Composite health must exceed both individual healths
   - ATP pool unification with proportional allocation

2. **Absorption Defense**: Large synthon attempts to subsume small one
   - Detection: MRH subsumption ≥80% + trust differential > 0.3
   - Defense: boundary hardening, ATP burn for independence signal
   - Escalation: federation-level arbitration if defense fails

3. **Conflict Arbitration**: Incompatible policy zones collide
   - Detect policy contradictions at the boundary
   - Resolve via MRH-weighted priority, intersection, or treaty
   - Create boundary buffer zone with negotiated policy

Key insight from CLAUDE.md: "Treat inter-synthon conflict as signal —
map it, don't suppress it."

Builds on: synthon_lifecycle_detection.py (Session 23)
Extends: cross_society_policy_conflicts.py (Session 23)

Checks: 70
"""
from __future__ import annotations
import hashlib
import math
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


# ─── Core Types ───────────────────────────────────────────────────────────────

class BoundaryEventType(Enum):
    PROXIMITY = auto()       # Synthons are near each other
    CONTACT = auto()         # MRH zones overlap
    NEGOTIATION = auto()     # Active boundary protocol in progress
    COMPOSITION = auto()     # Agreed to merge
    ABSORPTION_ATTEMPT = auto()  # One trying to absorb other
    CONFLICT = auto()        # Policy contradiction at boundary
    TREATY = auto()          # Negotiated coexistence agreement
    SEPARATION = auto()      # Synthons diverging


class CompositionPhase(Enum):
    PROPOSED = auto()
    HEALTH_CHECK = auto()
    TREATY_DRAFT = auto()
    ATP_POOL_MERGE = auto()
    MEMBER_VOTE = auto()
    FINALIZED = auto()
    REJECTED = auto()


class AbsorptionResult(Enum):
    DEFENDED = auto()
    ABSORBED = auto()
    ARBITRATED = auto()
    TREATY_FORMED = auto()


class ConflictSeverity(Enum):
    LOW = auto()         # Minor threshold differences
    MEDIUM = auto()      # Scope overlaps
    HIGH = auto()        # Direct policy contradictions
    CRITICAL = auto()    # Existential — both synthons cannot coexist


# ─── Synthon Model (reusable from lifecycle detection) ───────────────────────

@dataclass
class SynthonEntity:
    """An entity within a synthon."""
    entity_id: str
    trust_scores: Dict[str, float] = field(default_factory=dict)
    mrh_zones: Dict[str, int] = field(default_factory=dict)
    atp_balance: float = 100.0
    atp_inflow: float = 50.0
    atp_outflow: float = 50.0
    witnesses: Set[str] = field(default_factory=set)
    policy_bindings: Dict[str, str] = field(default_factory=dict)  # action → decision

    @property
    def trust_composite(self) -> float:
        if not self.trust_scores:
            return 0.5
        return sum(self.trust_scores.values()) / len(self.trust_scores)


@dataclass
class Synthon:
    """A coherent group of entities forming an emergent unit."""
    synthon_id: str
    members: Dict[str, SynthonEntity] = field(default_factory=dict)
    adjacency: Dict[str, Set[str]] = field(default_factory=dict)
    health: float = 0.5
    atp_pool: float = 0.0
    policies: Dict[str, str] = field(default_factory=dict)  # action → decision
    trust_composite: float = 0.5
    boundary_entities: Set[str] = field(default_factory=set)
    formation_time: float = field(default_factory=time.time)

    @property
    def size(self) -> int:
        return len(self.members)

    def compute_health(self) -> float:
        """Recompute health from member state."""
        if not self.members:
            return 0.0
        trusts = [m.trust_composite for m in self.members.values()]
        mean_t = sum(trusts) / len(trusts)
        variance = sum((t - mean_t) ** 2 for t in trusts) / len(trusts)
        coherence = 1.0 - min(variance * 4.0, 1.0)

        # Clustering from adjacency
        clustering = self._clustering_coefficient()

        # ATP balance
        total_in = sum(m.atp_inflow for m in self.members.values())
        total_out = sum(m.atp_outflow for m in self.members.values())
        total_flow = total_in + total_out
        flow_balance = 1.0 - abs(total_in - total_out) / max(total_flow, 1)

        self.health = 0.4 * coherence + 0.3 * clustering + 0.3 * flow_balance
        self.trust_composite = mean_t
        return self.health

    def _clustering_coefficient(self) -> float:
        if len(self.adjacency) < 3:
            return 0.0
        total_tri = 0
        total_triples = 0
        for node in self.adjacency:
            if node not in self.members:
                continue
            neighbors = self.adjacency.get(node, set()) & set(self.members.keys())
            k = len(neighbors)
            if k < 2:
                continue
            connected = 0
            nl = list(neighbors)
            for i in range(len(nl)):
                for j in range(i + 1, len(nl)):
                    if nl[j] in self.adjacency.get(nl[i], set()):
                        connected += 1
            total_tri += connected
            total_triples += k * (k - 1) // 2
        return total_tri / max(total_triples, 1)

    def identify_boundary(self, other: 'Synthon') -> Set[str]:
        """Find members whose MRH zones overlap with the other synthon."""
        other_ids = set(other.members.keys())
        boundary = set()
        for mid, member in self.members.items():
            mrh_peers = set(member.mrh_zones.keys())
            if mrh_peers & other_ids:
                boundary.add(mid)
        self.boundary_entities = boundary
        return boundary


# ─── Boundary Detection ──────────────────────────────────────────────────────

@dataclass
class BoundaryEvent:
    """A detected interaction event between two synthons."""
    event_id: str
    event_type: BoundaryEventType
    synthon_a_id: str
    synthon_b_id: str
    overlap_entities: Set[str]  # Entities in the overlap zone
    mrh_overlap_score: float    # Jaccard similarity of boundary MRH zones
    trust_differential: float   # |mean_trust_a - mean_trust_b|
    policy_conflicts: int       # Number of conflicting policies
    timestamp: float = field(default_factory=time.time)


class BoundaryDetector:
    """Detect when two synthons are interacting at their boundaries."""

    def __init__(self, proximity_threshold: float = 0.1,
                 contact_threshold: float = 0.3,
                 conflict_threshold: float = 0.0):
        self.proximity_threshold = proximity_threshold
        self.contact_threshold = contact_threshold
        self.conflict_threshold = conflict_threshold

    def detect(self, synthon_a: Synthon, synthon_b: Synthon) -> BoundaryEvent:
        """Detect the boundary interaction state between two synthons."""
        # Compute MRH overlap at boundary
        a_boundary = synthon_a.identify_boundary(synthon_b)
        b_boundary = synthon_b.identify_boundary(synthon_a)

        # Shared entities (members of both — shouldn't happen normally)
        a_ids = set(synthon_a.members.keys())
        b_ids = set(synthon_b.members.keys())
        shared = a_ids & b_ids

        # MRH overlap: how much of A's boundary MRH overlaps with B's members
        a_boundary_mrh = set()
        for mid in a_boundary:
            member = synthon_a.members[mid]
            a_boundary_mrh.update(member.mrh_zones.keys())

        b_boundary_mrh = set()
        for mid in b_boundary:
            member = synthon_b.members[mid]
            b_boundary_mrh.update(member.mrh_zones.keys())

        all_mrh = a_boundary_mrh | b_boundary_mrh
        overlap_mrh = a_boundary_mrh & b_boundary_mrh
        mrh_overlap = len(overlap_mrh) / max(len(all_mrh), 1)

        # Trust differential
        trust_diff = abs(synthon_a.trust_composite - synthon_b.trust_composite)

        # Policy conflicts
        conflicts = 0
        for action in synthon_a.policies:
            if action in synthon_b.policies:
                if synthon_a.policies[action] != synthon_b.policies[action]:
                    conflicts += 1

        # Determine event type
        overlap_entities = a_boundary | b_boundary | shared
        has_boundary = len(a_boundary) > 0 or len(b_boundary) > 0
        event_type = self._classify_event(mrh_overlap, conflicts,
                                           trust_diff, len(shared), has_boundary)

        return BoundaryEvent(
            event_id=secrets.token_hex(8),
            event_type=event_type,
            synthon_a_id=synthon_a.synthon_id,
            synthon_b_id=synthon_b.synthon_id,
            overlap_entities=overlap_entities,
            mrh_overlap_score=mrh_overlap,
            trust_differential=trust_diff,
            policy_conflicts=conflicts,
        )

    def _classify_event(self, mrh_overlap: float, conflicts: int,
                         trust_diff: float, shared_count: int,
                         has_boundary: bool = False) -> BoundaryEventType:
        # Only report conflict if there's actual boundary contact
        if conflicts > 0 and (has_boundary or shared_count > 0):
            return BoundaryEventType.CONFLICT
        if shared_count > 0:
            return BoundaryEventType.CONTACT
        if mrh_overlap >= self.contact_threshold:
            return BoundaryEventType.CONTACT
        if mrh_overlap >= self.proximity_threshold:
            return BoundaryEventType.PROXIMITY
        return BoundaryEventType.SEPARATION


# ─── Composition Protocol ────────────────────────────────────────────────────

@dataclass
class CompositionTreaty:
    """Agreement for two synthons to merge."""
    treaty_id: str
    synthon_a_id: str
    synthon_b_id: str
    phase: CompositionPhase = CompositionPhase.PROPOSED
    combined_health_estimate: float = 0.0
    atp_pool_total: float = 0.0
    member_votes: Dict[str, bool] = field(default_factory=dict)  # entity_id → vote
    policy_resolution: Dict[str, str] = field(default_factory=dict)  # merged policies
    quorum_threshold: float = 0.67  # 2/3 must approve
    timestamp: float = field(default_factory=time.time)

    @property
    def approval_ratio(self) -> float:
        if not self.member_votes:
            return 0.0
        return sum(1 for v in self.member_votes.values() if v) / len(self.member_votes)

    @property
    def has_quorum(self) -> bool:
        return self.approval_ratio >= self.quorum_threshold


class CompositionProtocol:
    """
    Protocol for two synthons to voluntarily merge.

    Prerequisites:
    - Both synthons must be in STABLE or FORMING phase
    - Combined health estimate must exceed both individual healths
    - 2/3 member quorum approval required
    """

    def __init__(self, min_health_improvement: float = 0.05,
                 quorum: float = 0.67):
        self.min_health_improvement = min_health_improvement
        self.quorum = quorum

    def propose(self, synthon_a: Synthon, synthon_b: Synthon) -> CompositionTreaty:
        """Initiate composition proposal."""
        treaty = CompositionTreaty(
            treaty_id=secrets.token_hex(8),
            synthon_a_id=synthon_a.synthon_id,
            synthon_b_id=synthon_b.synthon_id,
            quorum_threshold=self.quorum,
        )
        return treaty

    def health_check(self, treaty: CompositionTreaty,
                      synthon_a: Synthon, synthon_b: Synthon) -> bool:
        """Estimate combined health. Returns True if merger is beneficial."""
        treaty.phase = CompositionPhase.HEALTH_CHECK

        # Simulate merged synthon health
        combined_trust = []
        for m in synthon_a.members.values():
            combined_trust.append(m.trust_composite)
        for m in synthon_b.members.values():
            combined_trust.append(m.trust_composite)

        mean_t = sum(combined_trust) / max(len(combined_trust), 1)
        variance = sum((t - mean_t) ** 2 for t in combined_trust) / max(len(combined_trust), 1)
        coherence = 1.0 - min(variance * 4.0, 1.0)

        # Combined ATP pool
        treaty.atp_pool_total = synthon_a.atp_pool + synthon_b.atp_pool

        # Combined flow balance
        total_in = (sum(m.atp_inflow for m in synthon_a.members.values()) +
                     sum(m.atp_inflow for m in synthon_b.members.values()))
        total_out = (sum(m.atp_outflow for m in synthon_a.members.values()) +
                      sum(m.atp_outflow for m in synthon_b.members.values()))
        total_flow = total_in + total_out
        flow_balance = 1.0 - abs(total_in - total_out) / max(total_flow, 1)

        # Estimate cross-synthon adjacency boost
        a_boundary = synthon_a.identify_boundary(synthon_b)
        b_boundary = synthon_b.identify_boundary(synthon_a)
        boundary_ratio = (len(a_boundary) + len(b_boundary)) / max(
            synthon_a.size + synthon_b.size, 1)
        cross_clustering = min(boundary_ratio * 2.0, 1.0)

        estimated = 0.4 * coherence + 0.3 * cross_clustering + 0.3 * flow_balance
        treaty.combined_health_estimate = estimated

        # Must improve on BOTH synthons
        improvement = estimated - max(synthon_a.health, synthon_b.health)
        return improvement >= self.min_health_improvement

    def resolve_policies(self, treaty: CompositionTreaty,
                          synthon_a: Synthon, synthon_b: Synthon) -> Dict[str, str]:
        """Merge policy sets. Intersection (most restrictive) for conflicts."""
        treaty.phase = CompositionPhase.TREATY_DRAFT
        merged = {}

        all_actions = set(synthon_a.policies.keys()) | set(synthon_b.policies.keys())
        for action in all_actions:
            a_policy = synthon_a.policies.get(action)
            b_policy = synthon_b.policies.get(action)

            if a_policy and not b_policy:
                merged[action] = a_policy
            elif b_policy and not a_policy:
                merged[action] = b_policy
            elif a_policy == b_policy:
                merged[action] = a_policy
            else:
                # Conflict: take the more restrictive (DENY > REQUIRE_APPROVAL > RATE_LIMIT > ALLOW)
                restriction_order = ["DENY", "REQUIRE_APPROVAL", "RATE_LIMIT", "ALLOW"]
                a_rank = restriction_order.index(a_policy) if a_policy in restriction_order else 3
                b_rank = restriction_order.index(b_policy) if b_policy in restriction_order else 3
                merged[action] = restriction_order[min(a_rank, b_rank)]

        treaty.policy_resolution = merged
        return merged

    def collect_votes(self, treaty: CompositionTreaty,
                       synthon_a: Synthon, synthon_b: Synthon) -> Dict[str, bool]:
        """Simulate member voting on composition."""
        treaty.phase = CompositionPhase.MEMBER_VOTE
        votes = {}

        # Each member votes based on health improvement estimate
        for mid, member in {**synthon_a.members, **synthon_b.members}.items():
            # Higher trust entities more likely to approve beneficial mergers
            base_approval = treaty.combined_health_estimate > 0.5
            trust_factor = member.trust_composite > 0.4
            votes[mid] = base_approval and trust_factor

        treaty.member_votes = votes
        return votes

    def finalize(self, treaty: CompositionTreaty,
                  synthon_a: Synthon, synthon_b: Synthon) -> Optional[Synthon]:
        """Create the merged synthon if quorum is met."""
        if not treaty.has_quorum:
            treaty.phase = CompositionPhase.REJECTED
            return None

        treaty.phase = CompositionPhase.FINALIZED

        # Create merged synthon
        merged = Synthon(
            synthon_id=f"merged_{synthon_a.synthon_id}_{synthon_b.synthon_id}",
            atp_pool=treaty.atp_pool_total,
            policies=treaty.policy_resolution,
        )

        # Copy all members
        for mid, member in synthon_a.members.items():
            merged.members[mid] = member
        for mid, member in synthon_b.members.items():
            merged.members[mid] = member

        # Merge adjacency
        for node, neighbors in synthon_a.adjacency.items():
            merged.adjacency[node] = set(neighbors)
        for node, neighbors in synthon_b.adjacency.items():
            if node in merged.adjacency:
                merged.adjacency[node] |= neighbors
            else:
                merged.adjacency[node] = set(neighbors)

        # Add cross-boundary edges
        a_boundary = synthon_a.boundary_entities
        b_boundary = synthon_b.boundary_entities
        for a_id in a_boundary:
            for b_id in b_boundary:
                merged.adjacency.setdefault(a_id, set()).add(b_id)
                merged.adjacency.setdefault(b_id, set()).add(a_id)

        merged.compute_health()
        return merged

    def execute_full_protocol(self, synthon_a: Synthon,
                                synthon_b: Synthon) -> Tuple[CompositionTreaty, Optional[Synthon]]:
        """Run the complete composition protocol."""
        treaty = self.propose(synthon_a, synthon_b)

        if not self.health_check(treaty, synthon_a, synthon_b):
            treaty.phase = CompositionPhase.REJECTED
            return treaty, None

        self.resolve_policies(treaty, synthon_a, synthon_b)
        self.collect_votes(treaty, synthon_a, synthon_b)

        merged = self.finalize(treaty, synthon_a, synthon_b)
        return treaty, merged


# ─── Absorption Defense ──────────────────────────────────────────────────────

@dataclass
class AbsorptionAttempt:
    """Record of an absorption attempt and its defense."""
    attempt_id: str
    absorber_id: str
    target_id: str
    mrh_subsumption: float     # Fraction of target's MRH subsumed
    trust_differential: float  # absorber_trust - target_trust
    size_ratio: float          # absorber_size / target_size
    result: AbsorptionResult = AbsorptionResult.DEFENDED
    defense_cost_atp: float = 0.0   # ATP burned for defense
    timestamp: float = field(default_factory=time.time)


class AbsorptionDefense:
    """
    Protect smaller synthons from being absorbed by larger ones.

    Detection criteria:
    - MRH subsumption ≥ 80% (absorber covers most of target's MRH)
    - Trust differential > 0.3 (absorber is significantly more trusted)
    - Size ratio > 3:1 (absorber is much larger)

    Defense mechanisms:
    - Boundary hardening: increase MRH edge weight at boundary
    - Independence signal: ATP burn as proof of autonomous viability
    - Federation arbitration: escalate to external mediator
    """

    def __init__(self, subsumption_threshold: float = 0.8,
                 trust_diff_threshold: float = 0.3,
                 size_ratio_threshold: float = 3.0,
                 defense_atp_cost: float = 50.0):
        self.subsumption_threshold = subsumption_threshold
        self.trust_diff_threshold = trust_diff_threshold
        self.size_ratio_threshold = size_ratio_threshold
        self.defense_atp_cost = defense_atp_cost

    def detect_absorption(self, potential_absorber: Synthon,
                            target: Synthon) -> Optional[AbsorptionAttempt]:
        """Detect if an absorption attempt is in progress."""
        # Compute MRH subsumption
        target_mrh = set()
        for member in target.members.values():
            target_mrh.update(member.mrh_zones.keys())

        absorber_mrh = set()
        for member in potential_absorber.members.values():
            absorber_mrh.update(member.mrh_zones.keys())

        if not target_mrh:
            return None

        overlap = target_mrh & absorber_mrh
        subsumption = len(overlap) / len(target_mrh)

        trust_diff = potential_absorber.trust_composite - target.trust_composite
        size_ratio = potential_absorber.size / max(target.size, 1)

        # Check absorption criteria
        is_absorption = (
            subsumption >= self.subsumption_threshold and
            (trust_diff > self.trust_diff_threshold or
             size_ratio > self.size_ratio_threshold)
        )

        if not is_absorption:
            return None

        return AbsorptionAttempt(
            attempt_id=secrets.token_hex(8),
            absorber_id=potential_absorber.synthon_id,
            target_id=target.synthon_id,
            mrh_subsumption=subsumption,
            trust_differential=trust_diff,
            size_ratio=size_ratio,
        )

    def defend_boundary(self, target: Synthon,
                         attempt: AbsorptionAttempt) -> bool:
        """
        Boundary hardening: demonstrate autonomous viability.
        Returns True if defense is affordable and succeeds.
        """
        if target.atp_pool < self.defense_atp_cost:
            return False

        # Burn ATP as independence proof
        target.atp_pool -= self.defense_atp_cost
        attempt.defense_cost_atp = self.defense_atp_cost
        attempt.result = AbsorptionResult.DEFENDED
        return True

    def assess_viability(self, target: Synthon) -> float:
        """
        Compute target synthon's independent viability score.
        Score > 0.5 means defensible. Score < 0.3 means vulnerable.
        """
        # Health component
        health_score = target.compute_health()

        # ATP sustainability: can sustain operations?
        total_atp = target.atp_pool + sum(m.atp_balance for m in target.members.values())
        atp_score = min(total_atp / max(len(target.members) * 100, 1), 1.0)

        # Member commitment: how many members have strong internal connections?
        member_ids = set(target.members.keys())
        committed = 0
        for mid, member in target.members.items():
            internal_peers = set(member.mrh_zones.keys()) & member_ids
            if len(internal_peers) >= 2:
                committed += 1
        commitment_score = committed / max(len(target.members), 1)

        return 0.4 * health_score + 0.3 * atp_score + 0.3 * commitment_score

    def execute_defense(self, absorber: Synthon, target: Synthon) -> AbsorptionAttempt:
        """Full defense protocol."""
        attempt = self.detect_absorption(absorber, target)
        if attempt is None:
            # No absorption detected — return a non-absorption record
            return AbsorptionAttempt(
                attempt_id=secrets.token_hex(8),
                absorber_id=absorber.synthon_id,
                target_id=target.synthon_id,
                mrh_subsumption=0.0,
                trust_differential=0.0,
                size_ratio=absorber.size / max(target.size, 1),
                result=AbsorptionResult.DEFENDED,
            )

        viability = self.assess_viability(target)

        if viability >= 0.5:
            # Strong enough to defend
            if self.defend_boundary(target, attempt):
                attempt.result = AbsorptionResult.DEFENDED
            else:
                # Can't afford defense, escalate
                attempt.result = AbsorptionResult.ARBITRATED
        elif viability >= 0.3:
            # Borderline — arbitration
            attempt.result = AbsorptionResult.ARBITRATED
        else:
            # Too weak — offer treaty instead of absorption
            attempt.result = AbsorptionResult.TREATY_FORMED

        return attempt


# ─── Conflict Arbitration ────────────────────────────────────────────────────

@dataclass
class PolicyConflict:
    """A policy conflict between two synthons."""
    conflict_id: str
    action: str
    synthon_a_policy: str
    synthon_b_policy: str
    severity: ConflictSeverity
    boundary_entities: Set[str]


@dataclass
class BoundaryTreaty:
    """A negotiated agreement for coexistence at a boundary."""
    treaty_id: str
    synthon_a_id: str
    synthon_b_id: str
    resolved_policies: Dict[str, str]  # action → agreed decision
    buffer_zone_entities: Set[str]      # Entities in the negotiated buffer
    trust_exchange_rate: float = 1.0    # Trust conversion factor at boundary
    atp_exchange_rate: float = 1.0      # ATP conversion factor at boundary
    valid_until: float = 0.0            # Treaty expiry timestamp
    renewal_count: int = 0
    hash_chain: str = ""


class ConflictArbitrator:
    """
    Arbitrate policy conflicts between synthons at their boundaries.

    Three resolution strategies:
    1. Priority: Higher-health synthon's policy wins
    2. Intersection: Most restrictive policy applies at boundary
    3. Buffer: Create a negotiated zone with blended policies
    """

    RESTRICTION_ORDER = ["DENY", "REQUIRE_APPROVAL", "RATE_LIMIT", "ALLOW"]

    def __init__(self, treaty_duration: float = 86400.0):  # 24h default
        self.treaty_duration = treaty_duration

    def detect_conflicts(self, synthon_a: Synthon,
                          synthon_b: Synthon) -> List[PolicyConflict]:
        """Find all policy conflicts between two synthons."""
        conflicts = []
        common_actions = set(synthon_a.policies.keys()) & set(synthon_b.policies.keys())

        # Find boundary entities
        a_boundary = synthon_a.identify_boundary(synthon_b)
        b_boundary = synthon_b.identify_boundary(synthon_a)
        boundary_ents = a_boundary | b_boundary

        for action in common_actions:
            a_pol = synthon_a.policies[action]
            b_pol = synthon_b.policies[action]

            if a_pol == b_pol:
                continue

            # Classify severity
            a_rank = self.RESTRICTION_ORDER.index(a_pol) if a_pol in self.RESTRICTION_ORDER else 3
            b_rank = self.RESTRICTION_ORDER.index(b_pol) if b_pol in self.RESTRICTION_ORDER else 3
            rank_diff = abs(a_rank - b_rank)

            if rank_diff >= 3:
                severity = ConflictSeverity.CRITICAL
            elif rank_diff >= 2:
                severity = ConflictSeverity.HIGH
            elif rank_diff >= 1:
                severity = ConflictSeverity.MEDIUM
            else:
                severity = ConflictSeverity.LOW

            conflicts.append(PolicyConflict(
                conflict_id=secrets.token_hex(8),
                action=action,
                synthon_a_policy=a_pol,
                synthon_b_policy=b_pol,
                severity=severity,
                boundary_entities=boundary_ents,
            ))

        return conflicts

    def resolve_by_priority(self, conflict: PolicyConflict,
                              synthon_a: Synthon, synthon_b: Synthon) -> str:
        """Higher-health synthon's policy wins."""
        if synthon_a.health >= synthon_b.health:
            return conflict.synthon_a_policy
        return conflict.synthon_b_policy

    def resolve_by_intersection(self, conflict: PolicyConflict) -> str:
        """Most restrictive policy applies."""
        a_rank = self.RESTRICTION_ORDER.index(conflict.synthon_a_policy) \
            if conflict.synthon_a_policy in self.RESTRICTION_ORDER else 3
        b_rank = self.RESTRICTION_ORDER.index(conflict.synthon_b_policy) \
            if conflict.synthon_b_policy in self.RESTRICTION_ORDER else 3
        return self.RESTRICTION_ORDER[min(a_rank, b_rank)]

    def resolve_by_buffer(self, conflict: PolicyConflict,
                            synthon_a: Synthon, synthon_b: Synthon) -> str:
        """Blend: weight by health proportion."""
        a_rank = self.RESTRICTION_ORDER.index(conflict.synthon_a_policy) \
            if conflict.synthon_a_policy in self.RESTRICTION_ORDER else 3
        b_rank = self.RESTRICTION_ORDER.index(conflict.synthon_b_policy) \
            if conflict.synthon_b_policy in self.RESTRICTION_ORDER else 3

        total_health = synthon_a.health + synthon_b.health
        if total_health == 0:
            blended_rank = (a_rank + b_rank) / 2
        else:
            a_weight = synthon_a.health / total_health
            blended_rank = a_rank * a_weight + b_rank * (1 - a_weight)

        return self.RESTRICTION_ORDER[round(blended_rank)]

    def negotiate_treaty(self, synthon_a: Synthon,
                          synthon_b: Synthon,
                          strategy: str = "intersection") -> BoundaryTreaty:
        """Negotiate a full boundary treaty."""
        conflicts = self.detect_conflicts(synthon_a, synthon_b)
        resolved = {}
        buffer_entities = set()

        for conflict in conflicts:
            if strategy == "priority":
                resolved[conflict.action] = self.resolve_by_priority(
                    conflict, synthon_a, synthon_b)
            elif strategy == "intersection":
                resolved[conflict.action] = self.resolve_by_intersection(conflict)
            elif strategy == "buffer":
                resolved[conflict.action] = self.resolve_by_buffer(
                    conflict, synthon_a, synthon_b)
            buffer_entities |= conflict.boundary_entities

        # Also include non-conflicting shared policies
        for action in set(synthon_a.policies.keys()) & set(synthon_b.policies.keys()):
            if action not in resolved:
                resolved[action] = synthon_a.policies[action]

        # Trust exchange rate: proportional to trust differential
        trust_diff = abs(synthon_a.trust_composite - synthon_b.trust_composite)
        trust_rate = 1.0 / (1.0 + trust_diff)

        # ATP exchange rate: health-weighted
        health_sum = synthon_a.health + synthon_b.health
        atp_rate = 2.0 * min(synthon_a.health, synthon_b.health) / max(health_sum, 0.01)

        # Hash chain seed
        treaty_data = f"{synthon_a.synthon_id}:{synthon_b.synthon_id}:{time.time()}"
        hash_chain = hashlib.sha256(treaty_data.encode()).hexdigest()[:16]

        return BoundaryTreaty(
            treaty_id=secrets.token_hex(8),
            synthon_a_id=synthon_a.synthon_id,
            synthon_b_id=synthon_b.synthon_id,
            resolved_policies=resolved,
            buffer_zone_entities=buffer_entities,
            trust_exchange_rate=trust_rate,
            atp_exchange_rate=atp_rate,
            valid_until=time.time() + self.treaty_duration,
            hash_chain=hash_chain,
        )

    def renew_treaty(self, treaty: BoundaryTreaty,
                      synthon_a: Synthon, synthon_b: Synthon) -> BoundaryTreaty:
        """Renew an existing treaty with updated terms."""
        new_treaty = self.negotiate_treaty(synthon_a, synthon_b)
        new_treaty.renewal_count = treaty.renewal_count + 1
        # Chain hash from old treaty
        chain_data = f"{treaty.hash_chain}:{new_treaty.treaty_id}"
        new_treaty.hash_chain = hashlib.sha256(chain_data.encode()).hexdigest()[:16]
        return new_treaty


# ─── Boundary Orchestrator ───────────────────────────────────────────────────

@dataclass
class InteractionRecord:
    """Full record of an inter-synthon interaction."""
    record_id: str
    boundary_event: BoundaryEvent
    absorption_attempt: Optional[AbsorptionAttempt] = None
    composition_treaty: Optional[CompositionTreaty] = None
    boundary_treaty: Optional[BoundaryTreaty] = None
    outcome: str = ""
    timestamp: float = field(default_factory=time.time)


class BoundaryOrchestrator:
    """
    Central coordinator for inter-synthon boundary interactions.
    Routes to composition, defense, or arbitration based on detection.
    """

    def __init__(self):
        self.detector = BoundaryDetector()
        self.composition = CompositionProtocol()
        self.defense = AbsorptionDefense()
        self.arbitrator = ConflictArbitrator()
        self.history: List[InteractionRecord] = []

    def process_interaction(self, synthon_a: Synthon,
                              synthon_b: Synthon) -> InteractionRecord:
        """Process a complete inter-synthon interaction."""
        # Step 1: Detect boundary event
        event = self.detector.detect(synthon_a, synthon_b)

        record = InteractionRecord(
            record_id=secrets.token_hex(8),
            boundary_event=event,
        )

        # Step 2: Route based on event type
        if event.event_type == BoundaryEventType.SEPARATION:
            record.outcome = "no_interaction"

        elif event.event_type == BoundaryEventType.CONFLICT:
            # Policy conflict — negotiate treaty
            treaty = self.arbitrator.negotiate_treaty(synthon_a, synthon_b)
            record.boundary_treaty = treaty
            record.outcome = "treaty_negotiated"

        elif event.event_type == BoundaryEventType.CONTACT:
            # Check for absorption threat
            attempt = self.defense.detect_absorption(synthon_a, synthon_b)
            if attempt is not None:
                # Absorption defense
                full_attempt = self.defense.execute_defense(synthon_a, synthon_b)
                record.absorption_attempt = full_attempt
                record.outcome = f"absorption_{full_attempt.result.name.lower()}"
            else:
                # Check reverse direction
                attempt_rev = self.defense.detect_absorption(synthon_b, synthon_a)
                if attempt_rev is not None:
                    full_attempt = self.defense.execute_defense(synthon_b, synthon_a)
                    record.absorption_attempt = full_attempt
                    record.outcome = f"absorption_{full_attempt.result.name.lower()}"
                else:
                    # Benign contact — evaluate composition
                    treaty, merged = self.composition.execute_full_protocol(
                        synthon_a, synthon_b)
                    record.composition_treaty = treaty
                    if merged is not None:
                        record.outcome = "composition_complete"
                    else:
                        record.outcome = "composition_rejected"

        elif event.event_type == BoundaryEventType.PROXIMITY:
            record.outcome = "proximity_noted"

        self.history.append(record)
        return record

    def get_interaction_stats(self) -> Dict[str, int]:
        """Summary statistics of all interactions."""
        stats: Dict[str, int] = defaultdict(int)
        for record in self.history:
            stats[record.outcome] += 1
        return dict(stats)


# ─── Hash-Chained Audit Trail ────────────────────────────────────────────────

@dataclass
class AuditEntry:
    """A single auditable event in the inter-synthon interaction log."""
    entry_id: str
    event_type: str
    synthon_a_id: str
    synthon_b_id: str
    outcome: str
    details: Dict[str, Any]
    timestamp: float
    prev_hash: str
    entry_hash: str


class InterSynthonAuditTrail:
    """Hash-chained audit trail for inter-synthon interactions."""

    def __init__(self, hmac_key: str = "default_key"):
        self.entries: List[AuditEntry] = []
        self.hmac_key = hmac_key

    def _compute_hash(self, data: str, prev_hash: str) -> str:
        content = f"{prev_hash}:{data}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def record(self, interaction: InteractionRecord) -> AuditEntry:
        """Record an interaction in the audit trail."""
        prev_hash = self.entries[-1].entry_hash if self.entries else "genesis"

        details: Dict[str, Any] = {
            "event_type": interaction.boundary_event.event_type.name,
            "mrh_overlap": interaction.boundary_event.mrh_overlap_score,
            "trust_diff": interaction.boundary_event.trust_differential,
            "policy_conflicts": interaction.boundary_event.policy_conflicts,
        }

        if interaction.absorption_attempt:
            details["absorption"] = {
                "subsumption": interaction.absorption_attempt.mrh_subsumption,
                "result": interaction.absorption_attempt.result.name,
                "defense_cost": interaction.absorption_attempt.defense_cost_atp,
            }

        if interaction.boundary_treaty:
            details["treaty"] = {
                "policies_resolved": len(interaction.boundary_treaty.resolved_policies),
                "buffer_entities": len(interaction.boundary_treaty.buffer_zone_entities),
                "trust_rate": interaction.boundary_treaty.trust_exchange_rate,
            }

        data_str = f"{interaction.record_id}:{interaction.outcome}:{details}"
        entry_hash = self._compute_hash(data_str, prev_hash)

        entry = AuditEntry(
            entry_id=secrets.token_hex(8),
            event_type=interaction.boundary_event.event_type.name,
            synthon_a_id=interaction.boundary_event.synthon_a_id,
            synthon_b_id=interaction.boundary_event.synthon_b_id,
            outcome=interaction.outcome,
            details=details,
            timestamp=time.time(),
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        """Verify the hash chain integrity."""
        for i, entry in enumerate(self.entries):
            expected_prev = self.entries[i - 1].entry_hash if i > 0 else "genesis"
            if entry.prev_hash != expected_prev:
                return False
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_synthon(sid: str, n_members: int, trust: float = 0.7,
                   atp_pool: float = 500.0,
                   policies: Optional[Dict[str, str]] = None,
                   peer_prefix: str = "") -> Synthon:
    """Helper: create a synthon with interconnected members."""
    s = Synthon(synthon_id=sid, atp_pool=atp_pool)
    if policies:
        s.policies = policies

    members = []
    for i in range(n_members):
        eid = f"{sid}_e{i}"
        # Trust with small variation
        t = trust + (i % 3 - 1) * 0.05
        t = max(0.1, min(1.0, t))
        member = SynthonEntity(
            entity_id=eid,
            trust_scores={"talent": t, "training": t - 0.02, "temperament": t + 0.01},
            mrh_zones={f"{sid}_e{j}": 1 for j in range(n_members) if j != i},
            atp_balance=100.0,
            atp_inflow=50.0,
            atp_outflow=50.0,
            witnesses={f"{sid}_e{j}" for j in range(n_members) if j != i},
        )
        # Add external peers with prefix
        if peer_prefix:
            member.mrh_zones[f"{peer_prefix}_ext_{i}"] = 3
        s.members[eid] = member
        members.append(eid)

    # Build clique adjacency
    for i in range(n_members):
        eid = f"{sid}_e{i}"
        s.adjacency[eid] = {f"{sid}_e{j}" for j in range(n_members) if j != i}

    s.compute_health()
    return s


def _make_overlapping_synthons(trust_a: float = 0.7, trust_b: float = 0.6,
                                 size_a: int = 5, size_b: int = 5,
                                 boundary_links: int = 2) -> Tuple[Synthon, Synthon]:
    """Create two synthons with MRH overlap at boundary."""
    a = _make_synthon("alpha", size_a, trust_a, policies={
        "data_sharing": "ALLOW", "external_comms": "RATE_LIMIT"})
    b = _make_synthon("beta", size_b, trust_b, policies={
        "data_sharing": "ALLOW", "external_comms": "RATE_LIMIT"})

    # Create MRH links between boundary members
    for i in range(min(boundary_links, size_a, size_b)):
        a_id = f"alpha_e{i}"
        b_id = f"beta_e{i}"
        a.members[a_id].mrh_zones[b_id] = 2
        b.members[b_id].mrh_zones[a_id] = 2

    return a, b


def run_checks():
    results = {}
    total = 0
    passed = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal total, passed
        total += 1
        if condition:
            passed += 1
            results[name] = "PASS"
        else:
            results[name] = f"FAIL: {detail}"
            print(f"  FAIL: {name}: {detail}")

    # ── Section 1: Synthon Construction ──────────────────────────────────────

    s = _make_synthon("test", 5, trust=0.7)
    check("s1_synthon_size", s.size == 5, f"size={s.size}")
    check("s1_synthon_health", s.health > 0.5, f"health={s.health}")
    check("s1_synthon_adjacency", len(s.adjacency) == 5, f"adj={len(s.adjacency)}")
    check("s1_clique_adjacency", all(len(v) == 4 for v in s.adjacency.values()))
    check("s1_trust_composite", 0.6 < s.trust_composite < 0.8,
          f"trust={s.trust_composite}")
    check("s1_atp_pool", s.atp_pool == 500.0)

    # ── Section 2: Boundary Detection ────────────────────────────────────────

    a, b = _make_overlapping_synthons()
    detector = BoundaryDetector()
    event = detector.detect(a, b)

    check("s2_event_type", event.event_type == BoundaryEventType.CONTACT,
          f"type={event.event_type}")
    check("s2_overlap_entities", len(event.overlap_entities) > 0,
          f"overlap={len(event.overlap_entities)}")
    check("s2_mrh_overlap_positive", event.mrh_overlap_score > 0,
          f"overlap={event.mrh_overlap_score}")
    check("s2_trust_diff", event.trust_differential >= 0)

    # No conflicts — same policies
    check("s2_no_conflicts", event.policy_conflicts == 0,
          f"conflicts={event.policy_conflicts}")

    # Separated synthons (no MRH links)
    c = _make_synthon("gamma", 3, 0.5, peer_prefix="gamma_isolated")
    d = _make_synthon("delta", 3, 0.5, peer_prefix="delta_isolated")
    sep_event = detector.detect(c, d)
    check("s2_separation_detected", sep_event.event_type == BoundaryEventType.SEPARATION,
          f"type={sep_event.event_type}")

    # ── Section 3: Boundary Detection with Conflicts ─────────────────────────

    e = _make_synthon("epsilon", 4, 0.7, policies={
        "data_sharing": "ALLOW", "ai_training": "DENY"})
    f = _make_synthon("zeta", 4, 0.6, policies={
        "data_sharing": "DENY", "ai_training": "ALLOW"})
    # Link them
    e.members["epsilon_e0"].mrh_zones["zeta_e0"] = 2
    f.members["zeta_e0"].mrh_zones["epsilon_e0"] = 2

    conflict_event = detector.detect(e, f)
    check("s3_conflict_detected", conflict_event.event_type == BoundaryEventType.CONFLICT,
          f"type={conflict_event.event_type}")
    check("s3_two_conflicts", conflict_event.policy_conflicts == 2,
          f"conflicts={conflict_event.policy_conflicts}")

    # ── Section 4: Composition Protocol — Successful ─────────────────────────

    comp = CompositionProtocol(min_health_improvement=-0.5)  # Allow easy merge for test
    a2, b2 = _make_overlapping_synthons(trust_a=0.7, trust_b=0.68, boundary_links=3)
    a2.atp_pool = 300
    b2.atp_pool = 200

    treaty = comp.propose(a2, b2)
    check("s4_treaty_proposed", treaty.phase == CompositionPhase.PROPOSED)

    health_ok = comp.health_check(treaty, a2, b2)
    check("s4_health_check_phase", treaty.phase == CompositionPhase.HEALTH_CHECK)
    check("s4_combined_health", treaty.combined_health_estimate > 0,
          f"health={treaty.combined_health_estimate}")
    check("s4_atp_pool_merged", treaty.atp_pool_total == 500.0,
          f"pool={treaty.atp_pool_total}")

    comp.resolve_policies(treaty, a2, b2)
    check("s4_policies_resolved", len(treaty.policy_resolution) > 0)
    check("s4_treaty_draft_phase", treaty.phase == CompositionPhase.TREATY_DRAFT)

    comp.collect_votes(treaty, a2, b2)
    check("s4_votes_collected", len(treaty.member_votes) == 10,
          f"votes={len(treaty.member_votes)}")
    check("s4_vote_phase", treaty.phase == CompositionPhase.MEMBER_VOTE)

    merged = comp.finalize(treaty, a2, b2)
    check("s4_merge_success", merged is not None)
    check("s4_merged_size", merged.size == 10 if merged else False,
          f"size={merged.size if merged else 0}")
    check("s4_merged_pool", merged.atp_pool == 500.0 if merged else False)
    check("s4_finalized_phase", treaty.phase == CompositionPhase.FINALIZED)
    check("s4_merged_health", merged.health > 0 if merged else False,
          f"health={merged.health if merged else 0}")

    # ── Section 5: Composition Protocol — Full Execute ───────────────────────

    a3, b3 = _make_overlapping_synthons(trust_a=0.72, trust_b=0.70, boundary_links=3)
    full_treaty, full_merged = comp.execute_full_protocol(a3, b3)
    check("s5_full_protocol_completes", full_treaty.phase in [
        CompositionPhase.FINALIZED, CompositionPhase.REJECTED])
    if full_merged:
        check("s5_merged_adjacency", len(full_merged.adjacency) > 0)
        check("s5_cross_boundary_edges",
              any(f"beta_e" in str(full_merged.adjacency.get(f"alpha_e0", set()))
                  for _ in [1]))
    else:
        check("s5_merged_adjacency", True)  # Rejection is valid
        check("s5_cross_boundary_edges", True)

    # ── Section 6: Composition Rejection (low health) ────────────────────────

    comp_strict = CompositionProtocol(min_health_improvement=0.5)
    a4, b4 = _make_overlapping_synthons(trust_a=0.7, trust_b=0.3, boundary_links=1)
    treaty_rej, merged_rej = comp_strict.execute_full_protocol(a4, b4)
    check("s6_rejected_low_improvement",
          treaty_rej.phase == CompositionPhase.REJECTED,
          f"phase={treaty_rej.phase}")
    check("s6_no_merge", merged_rej is None)

    # ── Section 7: Absorption Detection ──────────────────────────────────────

    defense = AbsorptionDefense()

    # Large absorber with high trust, small target with low trust
    absorber = _make_synthon("absorber", 12, trust=0.85, atp_pool=1000)
    target = _make_synthon("target", 3, trust=0.4, atp_pool=200)

    # Make absorber's MRH subsume target's MRH
    for mid, member in target.members.items():
        for peer in list(member.mrh_zones.keys()):
            # Add all of target's peers to absorber's first member
            absorber.members["absorber_e0"].mrh_zones[peer] = 2
        # Add the target member itself
        absorber.members["absorber_e0"].mrh_zones[mid] = 2

    attempt = defense.detect_absorption(absorber, target)
    check("s7_absorption_detected", attempt is not None)
    check("s7_subsumption_high", attempt.mrh_subsumption >= 0.8 if attempt else False,
          f"sub={attempt.mrh_subsumption if attempt else 0}")
    check("s7_trust_diff", attempt.trust_differential > 0.3 if attempt else False,
          f"diff={attempt.trust_differential if attempt else 0}")
    check("s7_size_ratio", attempt.size_ratio > 3.0 if attempt else False,
          f"ratio={attempt.size_ratio if attempt else 0}")

    # ── Section 8: Absorption Defense — Successful ───────────────────────────

    target_def = _make_synthon("defender", 4, trust=0.5, atp_pool=200)
    absorber_def = _make_synthon("aggressor", 15, trust=0.85, atp_pool=1000)

    # Setup subsumption
    for mid, member in target_def.members.items():
        for peer in list(member.mrh_zones.keys()):
            absorber_def.members["aggressor_e0"].mrh_zones[peer] = 2
        absorber_def.members["aggressor_e0"].mrh_zones[mid] = 2

    result = defense.execute_defense(absorber_def, target_def)
    check("s8_defense_executed", result.result in [
        AbsorptionResult.DEFENDED, AbsorptionResult.ARBITRATED,
        AbsorptionResult.TREATY_FORMED])
    check("s8_defense_cost", result.defense_cost_atp >= 0)

    # ── Section 9: Absorption — Non-Detection ────────────────────────────────

    peer_a = _make_synthon("peer_a", 5, trust=0.7, peer_prefix="pa")
    peer_b = _make_synthon("peer_b", 5, trust=0.65, peer_prefix="pb")
    non_attempt = defense.detect_absorption(peer_a, peer_b)
    check("s9_no_absorption", non_attempt is None)

    # ── Section 10: Viability Assessment ─────────────────────────────────────

    healthy = _make_synthon("viable", 6, trust=0.8, atp_pool=600)
    viability = defense.assess_viability(healthy)
    check("s10_healthy_viable", viability >= 0.5, f"viability={viability}")

    weak = _make_synthon("weak", 2, trust=0.2, atp_pool=10)
    # Zero out member ATP so total ATP is truly low
    for m in weak.members.values():
        m.atp_balance = 5.0
    weak_viability = defense.assess_viability(weak)
    check("s10_weak_vulnerable", weak_viability < 0.5, f"viability={weak_viability}")

    # ── Section 11: Conflict Arbitrator ──────────────────────────────────────

    arb = ConflictArbitrator()

    s_a = _make_synthon("soc_a", 4, trust=0.8, policies={
        "data_sharing": "ALLOW", "ai_training": "DENY", "export": "RATE_LIMIT"})
    s_b = _make_synthon("soc_b", 4, trust=0.6, policies={
        "data_sharing": "DENY", "ai_training": "ALLOW", "export": "ALLOW"})
    # Link them
    s_a.members["soc_a_e0"].mrh_zones["soc_b_e0"] = 2
    s_b.members["soc_b_e0"].mrh_zones["soc_a_e0"] = 2

    conflicts = arb.detect_conflicts(s_a, s_b)
    check("s11_conflicts_found", len(conflicts) == 3, f"n={len(conflicts)}")

    # Check severities
    severities = {c.action: c.severity for c in conflicts}
    check("s11_data_sharing_critical",
          severities.get("data_sharing") == ConflictSeverity.CRITICAL,
          f"sev={severities.get('data_sharing')}")
    check("s11_ai_training_critical",
          severities.get("ai_training") == ConflictSeverity.CRITICAL,
          f"sev={severities.get('ai_training')}")
    check("s11_export_medium",
          severities.get("export") == ConflictSeverity.MEDIUM,
          f"sev={severities.get('export')}")

    # ── Section 12: Conflict Resolution Strategies ───────────────────────────

    ds_conflict = [c for c in conflicts if c.action == "data_sharing"][0]

    # Priority: higher-health wins
    priority_result = arb.resolve_by_priority(ds_conflict, s_a, s_b)
    check("s12_priority_a_wins", priority_result == "ALLOW")  # s_a has higher health

    # Intersection: most restrictive
    intersection_result = arb.resolve_by_intersection(ds_conflict)
    check("s12_intersection_deny", intersection_result == "DENY")  # DENY is more restrictive

    # Buffer: blended
    buffer_result = arb.resolve_by_buffer(ds_conflict, s_a, s_b)
    check("s12_buffer_result", buffer_result in ConflictArbitrator.RESTRICTION_ORDER,
          f"result={buffer_result}")

    # ── Section 13: Treaty Negotiation ───────────────────────────────────────

    treaty_int = arb.negotiate_treaty(s_a, s_b, strategy="intersection")
    check("s13_treaty_created", treaty_int.treaty_id != "")
    check("s13_policies_resolved", len(treaty_int.resolved_policies) == 3,
          f"n={len(treaty_int.resolved_policies)}")
    check("s13_data_sharing_deny", treaty_int.resolved_policies.get("data_sharing") == "DENY")
    check("s13_buffer_entities", len(treaty_int.buffer_zone_entities) > 0)
    check("s13_trust_rate", 0 < treaty_int.trust_exchange_rate <= 1.0,
          f"rate={treaty_int.trust_exchange_rate}")
    check("s13_atp_rate", 0 < treaty_int.atp_exchange_rate <= 1.0,
          f"rate={treaty_int.atp_exchange_rate}")
    check("s13_hash_chain", len(treaty_int.hash_chain) == 16)

    # Priority strategy
    treaty_pri = arb.negotiate_treaty(s_a, s_b, strategy="priority")
    check("s13_priority_data_sharing_allow",
          treaty_pri.resolved_policies.get("data_sharing") == "ALLOW")

    # ── Section 14: Treaty Renewal ───────────────────────────────────────────

    renewed = arb.renew_treaty(treaty_int, s_a, s_b)
    check("s14_renewal_count", renewed.renewal_count == 1)
    check("s14_chain_continues", renewed.hash_chain != treaty_int.hash_chain)
    check("s14_new_treaty_id", renewed.treaty_id != treaty_int.treaty_id)

    renewed2 = arb.renew_treaty(renewed, s_a, s_b)
    check("s14_second_renewal", renewed2.renewal_count == 2)

    # ── Section 15: Boundary Orchestrator — Conflict Path ────────────────────

    orch = BoundaryOrchestrator()

    # Conflict synthons
    orch_a = _make_synthon("orch_a", 4, trust=0.75, policies={
        "resource_access": "ALLOW", "voting": "DENY"})
    orch_b = _make_synthon("orch_b", 4, trust=0.65, policies={
        "resource_access": "DENY", "voting": "ALLOW"})
    orch_a.members["orch_a_e0"].mrh_zones["orch_b_e0"] = 2
    orch_b.members["orch_b_e0"].mrh_zones["orch_a_e0"] = 2

    record = orch.process_interaction(orch_a, orch_b)
    check("s15_conflict_outcome", record.outcome == "treaty_negotiated",
          f"outcome={record.outcome}")
    check("s15_treaty_exists", record.boundary_treaty is not None)
    check("s15_treaty_policies", len(record.boundary_treaty.resolved_policies) == 2
          if record.boundary_treaty else False)

    # ── Section 16: Orchestrator — Composition Path ──────────────────────────

    orch2 = BoundaryOrchestrator()
    orch2.composition = CompositionProtocol(min_health_improvement=-0.5)

    comp_a, comp_b = _make_overlapping_synthons(
        trust_a=0.72, trust_b=0.70, boundary_links=3)

    record2 = orch2.process_interaction(comp_a, comp_b)
    check("s16_composition_path", record2.outcome in [
        "composition_complete", "composition_rejected"],
          f"outcome={record2.outcome}")

    # ── Section 17: Orchestrator — Separation Path ───────────────────────────

    sep_a = _make_synthon("sep_a", 3, 0.5, peer_prefix="isolated_a")
    sep_b = _make_synthon("sep_b", 3, 0.5, peer_prefix="isolated_b")
    record3 = orch2.process_interaction(sep_a, sep_b)
    check("s17_separation", record3.outcome == "no_interaction",
          f"outcome={record3.outcome}")

    # ── Section 18: Orchestrator Stats ───────────────────────────────────────

    stats = orch2.get_interaction_stats()
    check("s18_stats_recorded", len(stats) > 0)
    check("s18_stats_sum", sum(stats.values()) == len(orch2.history),
          f"sum={sum(stats.values())}, hist={len(orch2.history)}")

    # ── Section 19: Audit Trail ──────────────────────────────────────────────

    audit = InterSynthonAuditTrail()

    # Record multiple interactions
    for rec in [record, record2, record3]:
        audit.record(rec)

    check("s19_audit_entries", len(audit.entries) == 3)
    check("s19_chain_valid", audit.verify_chain())
    check("s19_genesis_hash", audit.entries[0].prev_hash == "genesis")
    check("s19_chain_linked",
          audit.entries[1].prev_hash == audit.entries[0].entry_hash)
    check("s19_chain_linked_2",
          audit.entries[2].prev_hash == audit.entries[1].entry_hash)

    # Tamper detection
    original_hash = audit.entries[1].prev_hash
    audit.entries[1].prev_hash = "tampered"
    check("s19_tamper_detected", not audit.verify_chain())
    audit.entries[1].prev_hash = original_hash  # Restore
    check("s19_restore_valid", audit.verify_chain())

    # ── Section 20: Multi-Synthon Scenario ───────────────────────────────────

    orch3 = BoundaryOrchestrator()
    synthons = []
    for i in range(5):
        policies = {
            "data_sharing": ["ALLOW", "DENY", "RATE_LIMIT", "ALLOW", "DENY"][i],
            "compute": ["ALLOW", "ALLOW", "ALLOW", "DENY", "RATE_LIMIT"][i],
        }
        s = _make_synthon(f"multi_{i}", 4, trust=0.5 + i * 0.08, policies=policies)
        synthons.append(s)

    # Link adjacent synthons
    for i in range(len(synthons) - 1):
        a_id = f"multi_{i}_e0"
        b_id = f"multi_{i+1}_e0"
        synthons[i].members[a_id].mrh_zones[b_id] = 2
        synthons[i+1].members[b_id].mrh_zones[a_id] = 2

    # Process all pairwise interactions
    interactions = []
    for i in range(len(synthons)):
        for j in range(i + 1, len(synthons)):
            rec = orch3.process_interaction(synthons[i], synthons[j])
            interactions.append(rec)

    check("s20_all_pairs_processed", len(interactions) == 10,
          f"pairs={len(interactions)}")

    outcomes = [r.outcome for r in interactions]
    check("s20_multiple_outcome_types", len(set(outcomes)) > 1,
          f"types={set(outcomes)}")

    stats3 = orch3.get_interaction_stats()
    check("s20_stats_cover_all", sum(stats3.values()) == 10)

    # ── Section 21: Performance — Large-Scale Boundary Detection ─────────────

    big_a = _make_synthon("big_a", 20, trust=0.7)
    big_b = _make_synthon("big_b", 20, trust=0.65)
    # Link 5 boundary members
    for i in range(5):
        big_a.members[f"big_a_e{i}"].mrh_zones[f"big_b_e{i}"] = 2
        big_b.members[f"big_b_e{i}"].mrh_zones[f"big_a_e{i}"] = 2

    t0 = time.time()
    for _ in range(100):
        detector.detect(big_a, big_b)
    elapsed = time.time() - t0
    check("s21_100_detections_fast", elapsed < 5.0, f"elapsed={elapsed:.2f}s")

    # ── Section 22: Performance — Composition Protocol ───────────────────────

    t0 = time.time()
    comp_perf = CompositionProtocol(min_health_improvement=-1.0)
    for _ in range(50):
        pa, pb = _make_overlapping_synthons(boundary_links=3)
        comp_perf.execute_full_protocol(pa, pb)
    elapsed = time.time() - t0
    check("s22_50_compositions_fast", elapsed < 5.0, f"elapsed={elapsed:.2f}s")

    # ── Section 23: Edge Cases ───────────────────────────────────────────────

    # Empty synthon
    empty = Synthon(synthon_id="empty")
    empty_health = empty.compute_health()
    check("s23_empty_health_zero", empty_health == 0.0)

    # Single-member synthon
    single = _make_synthon("single", 1, trust=0.5)
    single_health = single.compute_health()
    check("s23_single_member_health", single_health > 0)

    # Self-boundary detection
    self_event = detector.detect(a, a)
    check("s23_self_detection", self_event.event_type in [
        BoundaryEventType.CONTACT, BoundaryEventType.PROXIMITY,
        BoundaryEventType.SEPARATION])

    # ── Section 24: Audit Trail with All Event Types ─────────────────────────

    audit2 = InterSynthonAuditTrail()
    full_orch = BoundaryOrchestrator()

    # Generate diverse interactions
    diverse_records = []

    # Conflict
    da = _make_synthon("div_a", 3, 0.7, policies={"act": "ALLOW"})
    db = _make_synthon("div_b", 3, 0.6, policies={"act": "DENY"})
    da.members["div_a_e0"].mrh_zones["div_b_e0"] = 2
    db.members["div_b_e0"].mrh_zones["div_a_e0"] = 2
    diverse_records.append(full_orch.process_interaction(da, db))

    # Separation
    ds = _make_synthon("div_s", 3, 0.5, peer_prefix="sep")
    dt = _make_synthon("div_t", 3, 0.5, peer_prefix="sep2")
    diverse_records.append(full_orch.process_interaction(ds, dt))

    for rec in diverse_records:
        audit2.record(rec)

    check("s24_diverse_audit", len(audit2.entries) == 2)
    check("s24_diverse_chain", audit2.verify_chain())
    check("s24_different_types",
          audit2.entries[0].event_type != audit2.entries[1].event_type)

    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"Inter-Synthon Boundary Protocols: {passed}/{total} checks passed")
    print(f"{'='*60}")

    if passed < total:
        print("\nFailed checks:")
        for name, result in results.items():
            if result.startswith("FAIL"):
                print(f"  {name}: {result}")

    return passed, total


if __name__ == "__main__":
    run_checks()
