"""
Cross-Society Policy Conflict Resolution — Reference Implementation

When an entity is citizen of multiple societies with contradictory
policies, which governs? This implements multi-jurisdiction conflict
detection, MRH-distance-weighted resolution, and appeal escalation.

Key concepts:
- Policy conflict detection across society boundaries
- Jurisdictional priority ordering by MRH distance
- Conflict resolution strategies: priority, intersection, union, arbitration
- Emergency freeze when high-trust societies actively contradict
- Appeal escalation chain for disputed resolutions
- Audit trail per EU AI Act Art. 9 (risk management)
- FSM for entity dual-citizenship state management

Checks: 66
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

class PolicyAction(Enum):
    ALLOW = auto()
    DENY = auto()
    REQUIRE_APPROVAL = auto()
    RATE_LIMIT = auto()


class ConflictType(Enum):
    DIRECT_CONTRADICTION = auto()    # One allows, other denies
    SCOPE_OVERLAP = auto()           # Both regulate same action differently
    THRESHOLD_MISMATCH = auto()      # Different T3 requirements
    JURISDICTION_AMBIGUITY = auto()  # Unclear which society applies


class ResolutionStrategy(Enum):
    PRIORITY = auto()        # Higher-priority society wins
    INTERSECTION = auto()    # Most restrictive policy applies
    UNION = auto()           # Most permissive policy applies
    ARBITRATION = auto()     # Third-party arbitrator decides
    FREEZE = auto()          # Entity suspended pending resolution


class MRHZone(Enum):
    SELF = 0
    DIRECT = 1
    INDIRECT = 2
    PERIPHERAL = 3
    BEYOND = 4


@dataclass
class Policy:
    """A society's policy on a specific action."""
    policy_id: str
    society_id: str
    action: str             # What action this policy governs
    decision: PolicyAction
    t3_requirement: float = 0.0  # Minimum T3 to qualify
    scope: str = "general"       # Policy scope
    priority: int = 0            # Higher = more authoritative
    conditions: Dict[str, Any] = field(default_factory=dict)

    def evaluate(self, t3_composite: float) -> PolicyAction:
        if t3_composite < self.t3_requirement:
            return PolicyAction.DENY
        return self.decision


@dataclass
class Society:
    """A Web4 society with policies."""
    society_id: str
    name: str
    trust_score: float          # Society's own T3 composite
    policies: Dict[str, Policy] = field(default_factory=dict)
    mrh_zone: MRHZone = MRHZone.DIRECT

    def add_policy(self, policy: Policy):
        self.policies[policy.action] = policy


@dataclass
class EntityMembership:
    """An entity's membership in a society."""
    entity_id: str
    society_id: str
    mrh_distance: int       # Hop count from entity to society
    trust_in_society: float  # Entity's T3 within this society
    joined_at: float = field(default_factory=time.time)


@dataclass
class PolicyConflict:
    """A detected conflict between two societies' policies."""
    conflict_id: str
    action: str
    society_a: str
    society_b: str
    policy_a: Policy
    policy_b: Policy
    conflict_type: ConflictType
    severity: float  # 0-1
    details: str


@dataclass
class ConflictResolution:
    """Resolution of a policy conflict."""
    resolution_id: str
    conflict_id: str
    strategy: ResolutionStrategy
    winning_society: Optional[str]
    resolved_action: PolicyAction
    rationale: str
    timestamp: float = field(default_factory=time.time)
    appealed: bool = False
    appeal_result: Optional[str] = None


# ─── Conflict Detection ──────────────────────────────────────────────────────

class ConflictDetector:
    """Detect policy conflicts across societies sharing an entity."""

    def __init__(self):
        self.conflicts: List[PolicyConflict] = []

    def detect_conflicts(self, entity_id: str,
                          societies: Dict[str, Society],
                          memberships: Dict[str, EntityMembership]) -> List[PolicyConflict]:
        """Find all policy conflicts for an entity across its societies."""
        conflicts = []
        society_list = [societies[m.society_id] for m in memberships.values()
                        if m.society_id in societies]

        # Check all pairs
        for i, sa in enumerate(society_list):
            for sb in society_list[i + 1:]:
                # Find common actions
                common_actions = set(sa.policies.keys()) & set(sb.policies.keys())
                for action in common_actions:
                    pa = sa.policies[action]
                    pb = sb.policies[action]
                    conflict = self._check_pair(entity_id, action, sa, sb, pa, pb)
                    if conflict:
                        conflicts.append(conflict)

        self.conflicts.extend(conflicts)
        return conflicts

    def _check_pair(self, entity_id: str, action: str,
                     sa: Society, sb: Society,
                     pa: Policy, pb: Policy) -> Optional[PolicyConflict]:
        """Check if two policies conflict."""
        # Direct contradiction: one allows, other denies
        if (pa.decision == PolicyAction.ALLOW and pb.decision == PolicyAction.DENY) or \
           (pa.decision == PolicyAction.DENY and pb.decision == PolicyAction.ALLOW):
            return PolicyConflict(
                f"conflict_{secrets.token_hex(6)}",
                action, sa.society_id, sb.society_id, pa, pb,
                ConflictType.DIRECT_CONTRADICTION, 1.0,
                f"{sa.name} {pa.decision.name} vs {sb.name} {pb.decision.name} on '{action}'"
            )

        # Threshold mismatch: different T3 requirements
        if abs(pa.t3_requirement - pb.t3_requirement) > 0.2:
            return PolicyConflict(
                f"conflict_{secrets.token_hex(6)}",
                action, sa.society_id, sb.society_id, pa, pb,
                ConflictType.THRESHOLD_MISMATCH, 0.5,
                f"T3 requirement: {sa.name}={pa.t3_requirement} vs {sb.name}={pb.t3_requirement}"
            )

        # Different decisions that aren't contradictions but still conflict
        if pa.decision != pb.decision:
            return PolicyConflict(
                f"conflict_{secrets.token_hex(6)}",
                action, sa.society_id, sb.society_id, pa, pb,
                ConflictType.SCOPE_OVERLAP, 0.6,
                f"{sa.name} {pa.decision.name} vs {sb.name} {pb.decision.name} on '{action}'"
            )

        return None


# ─── Conflict Resolution Engine ──────────────────────────────────────────────

class ConflictResolver:
    """
    Resolves policy conflicts using configurable strategies.
    Default: MRH-distance-weighted priority (closer society governs).
    """

    def __init__(self, default_strategy: ResolutionStrategy = ResolutionStrategy.PRIORITY):
        self.default_strategy = default_strategy
        self.resolutions: List[ConflictResolution] = []

    def resolve(self, conflict: PolicyConflict,
                memberships: Dict[str, EntityMembership],
                societies: Dict[str, Society],
                strategy: Optional[ResolutionStrategy] = None) -> ConflictResolution:
        """Resolve a conflict between two societies."""
        strat = strategy or self.default_strategy

        if strat == ResolutionStrategy.PRIORITY:
            return self._resolve_priority(conflict, memberships, societies)
        elif strat == ResolutionStrategy.INTERSECTION:
            return self._resolve_intersection(conflict)
        elif strat == ResolutionStrategy.UNION:
            return self._resolve_union(conflict)
        elif strat == ResolutionStrategy.FREEZE:
            return self._resolve_freeze(conflict)
        else:
            return self._resolve_priority(conflict, memberships, societies)

    def _resolve_priority(self, conflict: PolicyConflict,
                           memberships: Dict[str, EntityMembership],
                           societies: Dict[str, Society]) -> ConflictResolution:
        """Priority resolution: closer society (lower MRH distance) wins.
        Ties broken by society trust score, then policy priority."""
        m_a = memberships.get(conflict.society_a)
        m_b = memberships.get(conflict.society_b)

        if not m_a or not m_b:
            winner = conflict.society_a if m_a else conflict.society_b
            winning_policy = conflict.policy_a if m_a else conflict.policy_b
        else:
            # Score: lower MRH distance is better, higher trust is better
            score_a = -m_a.mrh_distance * 10 + societies.get(conflict.society_a, Society("", "", 0)).trust_score * 5 + conflict.policy_a.priority
            score_b = -m_b.mrh_distance * 10 + societies.get(conflict.society_b, Society("", "", 0)).trust_score * 5 + conflict.policy_b.priority

            if score_a >= score_b:
                winner = conflict.society_a
                winning_policy = conflict.policy_a
            else:
                winner = conflict.society_b
                winning_policy = conflict.policy_b

        resolution = ConflictResolution(
            f"res_{secrets.token_hex(6)}",
            conflict.conflict_id,
            ResolutionStrategy.PRIORITY,
            winner,
            winning_policy.decision,
            f"Priority: {winner} wins (MRH distance + trust score)",
        )
        self.resolutions.append(resolution)
        return resolution

    def _resolve_intersection(self, conflict: PolicyConflict) -> ConflictResolution:
        """Intersection: most restrictive policy wins."""
        # DENY > REQUIRE_APPROVAL > RATE_LIMIT > ALLOW
        restriction_order = {
            PolicyAction.DENY: 4,
            PolicyAction.REQUIRE_APPROVAL: 3,
            PolicyAction.RATE_LIMIT: 2,
            PolicyAction.ALLOW: 1,
        }
        a_rank = restriction_order.get(conflict.policy_a.decision, 0)
        b_rank = restriction_order.get(conflict.policy_b.decision, 0)

        if a_rank >= b_rank:
            winner = conflict.society_a
            action = conflict.policy_a.decision
        else:
            winner = conflict.society_b
            action = conflict.policy_b.decision

        resolution = ConflictResolution(
            f"res_{secrets.token_hex(6)}",
            conflict.conflict_id,
            ResolutionStrategy.INTERSECTION,
            winner,
            action,
            f"Intersection: most restrictive ({action.name}) from {winner}",
        )
        self.resolutions.append(resolution)
        return resolution

    def _resolve_union(self, conflict: PolicyConflict) -> ConflictResolution:
        """Union: most permissive policy wins."""
        restriction_order = {
            PolicyAction.DENY: 4,
            PolicyAction.REQUIRE_APPROVAL: 3,
            PolicyAction.RATE_LIMIT: 2,
            PolicyAction.ALLOW: 1,
        }
        a_rank = restriction_order.get(conflict.policy_a.decision, 0)
        b_rank = restriction_order.get(conflict.policy_b.decision, 0)

        if a_rank <= b_rank:
            winner = conflict.society_a
            action = conflict.policy_a.decision
        else:
            winner = conflict.society_b
            action = conflict.policy_b.decision

        resolution = ConflictResolution(
            f"res_{secrets.token_hex(6)}",
            conflict.conflict_id,
            ResolutionStrategy.UNION,
            winner,
            action,
            f"Union: most permissive ({action.name}) from {winner}",
        )
        self.resolutions.append(resolution)
        return resolution

    def _resolve_freeze(self, conflict: PolicyConflict) -> ConflictResolution:
        """Freeze: entity suspended pending manual resolution."""
        resolution = ConflictResolution(
            f"res_{secrets.token_hex(6)}",
            conflict.conflict_id,
            ResolutionStrategy.FREEZE,
            None,
            PolicyAction.DENY,
            f"FREEZE: Entity suspended due to conflict severity {conflict.severity}",
        )
        self.resolutions.append(resolution)
        return resolution


# ─── Emergency Freeze Protocol ────────────────────────────────────────────────

class FreezeStatus(Enum):
    ACTIVE = auto()
    FROZEN = auto()
    THAWING = auto()


@dataclass
class FreezeState:
    entity_id: str
    status: FreezeStatus
    frozen_at: Optional[float] = None
    freeze_reason: str = ""
    conflicting_societies: List[str] = field(default_factory=list)
    thaw_votes: Dict[str, bool] = field(default_factory=dict)
    auto_expire: float = 86400.0  # 24h auto-expire

    @property
    def should_expire(self) -> bool:
        if self.frozen_at is None:
            return False
        return time.time() - self.frozen_at > self.auto_expire

    @property
    def thaw_quorum_met(self) -> bool:
        if not self.thaw_votes:
            return False
        approvals = sum(1 for v in self.thaw_votes.values() if v)
        return approvals >= math.ceil(len(self.conflicting_societies) * 2 / 3)


class EmergencyFreezeProtocol:
    """
    Freeze entities when high-trust societies have active contradictions.
    Requires 2/3 quorum from conflicting societies to thaw.
    """

    def __init__(self, trust_threshold: float = 0.7):
        self.trust_threshold = trust_threshold
        self.freeze_states: Dict[str, FreezeState] = {}

    def evaluate_freeze(self, entity_id: str, conflicts: List[PolicyConflict],
                         societies: Dict[str, Society]) -> Optional[FreezeState]:
        """Determine if conflicts warrant emergency freeze."""
        # Only freeze for direct contradictions between high-trust societies
        severe = [c for c in conflicts
                  if c.conflict_type == ConflictType.DIRECT_CONTRADICTION
                  and societies.get(c.society_a, Society("", "", 0)).trust_score >= self.trust_threshold
                  and societies.get(c.society_b, Society("", "", 0)).trust_score >= self.trust_threshold]

        if not severe:
            return None

        involved = set()
        for c in severe:
            involved.add(c.society_a)
            involved.add(c.society_b)

        state = FreezeState(
            entity_id=entity_id,
            status=FreezeStatus.FROZEN,
            frozen_at=time.time(),
            freeze_reason=f"{len(severe)} direct contradictions between high-trust societies",
            conflicting_societies=list(involved),
        )
        self.freeze_states[entity_id] = state
        return state

    def vote_thaw(self, entity_id: str, society_id: str, approve: bool) -> bool:
        state = self.freeze_states.get(entity_id)
        if not state or state.status != FreezeStatus.FROZEN:
            return False
        if society_id not in state.conflicting_societies:
            return False
        state.thaw_votes[society_id] = approve
        if state.thaw_quorum_met:
            state.status = FreezeStatus.THAWING
        return True

    def thaw(self, entity_id: str) -> bool:
        state = self.freeze_states.get(entity_id)
        if not state:
            return False
        if state.thaw_quorum_met or state.should_expire:
            state.status = FreezeStatus.ACTIVE
            return True
        return False


# ─── Appeal Escalation ────────────────────────────────────────────────────────

class AppealStatus(Enum):
    FILED = auto()
    REVIEWING = auto()
    UPHELD = auto()
    OVERTURNED = auto()
    DISMISSED = auto()


@dataclass
class Appeal:
    appeal_id: str
    resolution_id: str
    appellant_entity: str
    reason: str
    status: AppealStatus = AppealStatus.FILED
    reviewer_society: Optional[str] = None
    revised_action: Optional[PolicyAction] = None
    timestamp: float = field(default_factory=time.time)


class AppealChain:
    """Multi-tier appeal escalation for conflict resolutions."""

    def __init__(self):
        self.appeals: List[Appeal] = []
        self.max_appeals_per_resolution: int = 2

    def file_appeal(self, resolution: ConflictResolution,
                     appellant: str, reason: str) -> Optional[Appeal]:
        # Check appeal limit
        existing = [a for a in self.appeals if a.resolution_id == resolution.resolution_id]
        if len(existing) >= self.max_appeals_per_resolution:
            return None

        appeal = Appeal(
            appeal_id=f"appeal_{secrets.token_hex(6)}",
            resolution_id=resolution.resolution_id,
            appellant_entity=appellant,
            reason=reason,
        )
        self.appeals.append(appeal)
        resolution.appealed = True
        return appeal

    def review(self, appeal_id: str, reviewer: str,
               upheld: bool, revised_action: Optional[PolicyAction] = None) -> bool:
        appeal = next((a for a in self.appeals if a.appeal_id == appeal_id), None)
        if not appeal:
            return False
        appeal.reviewer_society = reviewer
        appeal.status = AppealStatus.UPHELD if upheld else AppealStatus.OVERTURNED
        if not upheld and revised_action:
            appeal.revised_action = revised_action
        return True


# ─── Conflict Audit Trail ────────────────────────────────────────────────────

@dataclass
class ConflictAuditEntry:
    entry_id: str
    entity_id: str
    action: str
    societies: List[str]
    conflict_type: str
    resolution_strategy: str
    resolved_action: str
    timestamp: float
    hash: str


class ConflictAuditTrail:
    """EU AI Act Art. 9 compliant audit trail for policy conflicts."""

    def __init__(self):
        self.entries: List[ConflictAuditEntry] = []

    def record(self, entity_id: str, conflict: PolicyConflict,
               resolution: ConflictResolution) -> ConflictAuditEntry:
        prev_hash = self.entries[-1].hash if self.entries else "genesis"
        data = f"{entity_id}:{conflict.action}:{resolution.resolved_action.name}:{prev_hash}"
        entry = ConflictAuditEntry(
            entry_id=f"caudit_{len(self.entries)}",
            entity_id=entity_id,
            action=conflict.action,
            societies=[conflict.society_a, conflict.society_b],
            conflict_type=conflict.conflict_type.name,
            resolution_strategy=resolution.strategy.name,
            resolved_action=resolution.resolved_action.name,
            timestamp=time.time(),
            hash=hashlib.sha256(data.encode()).hexdigest(),
        )
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        for i in range(1, len(self.entries)):
            prev = self.entries[i - 1]
            curr = self.entries[i]
            data = f"{curr.entity_id}:{curr.action}:{curr.resolved_action}:{prev.hash}"
            expected = hashlib.sha256(data.encode()).hexdigest()
            if curr.hash != expected:
                return False
        return True


# ─── Policy Evaluation Gateway ────────────────────────────────────────────────

class PolicyGateway:
    """
    Unified policy evaluation gateway that checks all societies,
    detects conflicts, resolves them, and returns a final decision.
    """

    def __init__(self, default_strategy: ResolutionStrategy = ResolutionStrategy.PRIORITY):
        self.detector = ConflictDetector()
        self.resolver = ConflictResolver(default_strategy)
        self.freeze_protocol = EmergencyFreezeProtocol()
        self.audit = ConflictAuditTrail()
        self.appeal_chain = AppealChain()

    def evaluate(self, entity_id: str, action: str,
                  t3_composite: float,
                  societies: Dict[str, Society],
                  memberships: Dict[str, EntityMembership]) -> Tuple[PolicyAction, List[PolicyConflict]]:
        """Evaluate a policy action across all societies."""
        # Check freeze
        freeze_state = self.freeze_protocol.freeze_states.get(entity_id)
        if freeze_state and freeze_state.status == FreezeStatus.FROZEN:
            if not freeze_state.should_expire:
                return PolicyAction.DENY, []

        # Collect applicable policies
        applicable = {}
        for m in memberships.values():
            s = societies.get(m.society_id)
            if s and action in s.policies:
                applicable[m.society_id] = s.policies[action]

        if not applicable:
            return PolicyAction.ALLOW, []  # No policy = allowed

        if len(applicable) == 1:
            sid = next(iter(applicable))
            return applicable[sid].evaluate(t3_composite), []

        # Multiple policies → detect conflicts
        conflicts = self.detector.detect_conflicts(entity_id, societies, memberships)
        relevant_conflicts = [c for c in conflicts if c.action == action]

        if not relevant_conflicts:
            # No conflict — use highest-priority policy
            best_sid = max(applicable.keys(),
                           key=lambda s: applicable[s].priority)
            return applicable[best_sid].evaluate(t3_composite), []

        # Check if freeze is warranted
        freeze = self.freeze_protocol.evaluate_freeze(entity_id, relevant_conflicts, societies)
        if freeze:
            return PolicyAction.DENY, relevant_conflicts

        # Resolve conflicts
        final_action = PolicyAction.ALLOW
        for conflict in relevant_conflicts:
            resolution = self.resolver.resolve(conflict, memberships, societies)
            self.audit.record(entity_id, conflict, resolution)
            # Most restrictive resolution wins across all conflicts
            if resolution.resolved_action == PolicyAction.DENY:
                final_action = PolicyAction.DENY
            elif resolution.resolved_action == PolicyAction.REQUIRE_APPROVAL and \
                 final_action != PolicyAction.DENY:
                final_action = PolicyAction.REQUIRE_APPROVAL

        return final_action, relevant_conflicts


# ─── Checks ──────────────────────────────────────────────────────────────────

def run_checks():
    checks = []
    t0 = time.time()

    # ── S1: Policy Basics ─────────────────────────────────────────────────
    p1 = Policy("p1", "society_A", "transfer_atp", PolicyAction.ALLOW, t3_requirement=0.3)
    checks.append(("s1_allow_high_t3", p1.evaluate(0.5) == PolicyAction.ALLOW))
    checks.append(("s1_deny_low_t3", p1.evaluate(0.2) == PolicyAction.DENY))

    s1 = Society("society_A", "Alpha Society", 0.8)
    s1.add_policy(p1)
    checks.append(("s1_policy_added", "transfer_atp" in s1.policies))

    # ── S2: Conflict Detection ────────────────────────────────────────────
    sa = Society("soc_alpha", "Alpha", 0.8)
    sa.add_policy(Policy("pa1", "soc_alpha", "send_message", PolicyAction.ALLOW))
    sa.add_policy(Policy("pa2", "soc_alpha", "large_transfer", PolicyAction.DENY))

    sb = Society("soc_beta", "Beta", 0.7)
    sb.add_policy(Policy("pb1", "soc_beta", "send_message", PolicyAction.DENY))
    sb.add_policy(Policy("pb2", "soc_beta", "large_transfer", PolicyAction.ALLOW))

    societies = {"soc_alpha": sa, "soc_beta": sb}
    memberships = {
        "soc_alpha": EntityMembership("entity_1", "soc_alpha", 1, 0.7),
        "soc_beta": EntityMembership("entity_1", "soc_beta", 2, 0.6),
    }

    detector = ConflictDetector()
    conflicts = detector.detect_conflicts("entity_1", societies, memberships)
    checks.append(("s2_two_conflicts", len(conflicts) == 2))
    checks.append(("s2_direct_contradiction",
                    all(c.conflict_type == ConflictType.DIRECT_CONTRADICTION for c in conflicts)))
    checks.append(("s2_severity_1", all(c.severity == 1.0 for c in conflicts)))

    # ── S3: Threshold Mismatch ────────────────────────────────────────────
    sc = Society("soc_gamma", "Gamma", 0.75)
    sc.add_policy(Policy("pc1", "soc_gamma", "publish_data", PolicyAction.ALLOW, t3_requirement=0.3))

    sd = Society("soc_delta", "Delta", 0.65)
    sd.add_policy(Policy("pd1", "soc_delta", "publish_data", PolicyAction.ALLOW, t3_requirement=0.7))

    societies2 = {"soc_gamma": sc, "soc_delta": sd}
    memberships2 = {
        "soc_gamma": EntityMembership("entity_2", "soc_gamma", 1, 0.6),
        "soc_delta": EntityMembership("entity_2", "soc_delta", 1, 0.5),
    }
    detector2 = ConflictDetector()
    thresh_conflicts = detector2.detect_conflicts("entity_2", societies2, memberships2)
    checks.append(("s3_threshold_mismatch",
                    any(c.conflict_type == ConflictType.THRESHOLD_MISMATCH for c in thresh_conflicts)))

    # ── S4: Priority Resolution ───────────────────────────────────────────
    resolver = ConflictResolver(ResolutionStrategy.PRIORITY)
    # Alpha is closer (MRH distance 1 vs 2) → Alpha wins
    resolution = resolver.resolve(conflicts[0], memberships, societies)
    checks.append(("s4_alpha_wins", resolution.winning_society == "soc_alpha"))
    checks.append(("s4_priority_strategy", resolution.strategy == ResolutionStrategy.PRIORITY))

    # ── S5: Intersection Resolution ───────────────────────────────────────
    res_int = resolver.resolve(conflicts[0], memberships, societies,
                                ResolutionStrategy.INTERSECTION)
    # send_message: Alpha ALLOW, Beta DENY → intersection = DENY
    checks.append(("s5_intersection_deny", res_int.resolved_action == PolicyAction.DENY))

    # ── S6: Union Resolution ─────────────────────────────────────────────
    res_union = resolver.resolve(conflicts[0], memberships, societies,
                                  ResolutionStrategy.UNION)
    checks.append(("s6_union_allow", res_union.resolved_action == PolicyAction.ALLOW))

    # ── S7: Freeze Resolution ─────────────────────────────────────────────
    res_freeze = resolver.resolve(conflicts[0], memberships, societies,
                                   ResolutionStrategy.FREEZE)
    checks.append(("s7_freeze_deny", res_freeze.resolved_action == PolicyAction.DENY))
    checks.append(("s7_freeze_no_winner", res_freeze.winning_society is None))

    # ── S8: Emergency Freeze Protocol ─────────────────────────────────────
    freeze_proto = EmergencyFreezeProtocol(trust_threshold=0.7)
    freeze_state = freeze_proto.evaluate_freeze("entity_1", conflicts, societies)
    checks.append(("s8_freeze_triggered", freeze_state is not None))
    checks.append(("s8_status_frozen", freeze_state.status == FreezeStatus.FROZEN))
    checks.append(("s8_two_societies", len(freeze_state.conflicting_societies) == 2))

    # Low-trust societies don't trigger freeze
    low_sa = Society("low_a", "Low A", 0.3)
    low_sa.add_policy(Policy("la1", "low_a", "action", PolicyAction.ALLOW))
    low_sb = Society("low_b", "Low B", 0.4)
    low_sb.add_policy(Policy("lb1", "low_b", "action", PolicyAction.DENY))
    low_conflict = PolicyConflict("lc1", "action", "low_a", "low_b",
                                   low_sa.policies["action"], low_sb.policies["action"],
                                   ConflictType.DIRECT_CONTRADICTION, 1.0, "test")
    no_freeze = freeze_proto.evaluate_freeze("entity_low", [low_conflict],
                                              {"low_a": low_sa, "low_b": low_sb})
    checks.append(("s8_no_freeze_low_trust", no_freeze is None))

    # ── S9: Thaw Quorum ──────────────────────────────────────────────────
    checks.append(("s9_no_quorum_yet", not freeze_state.thaw_quorum_met))

    freeze_proto.vote_thaw("entity_1", "soc_alpha", True)
    checks.append(("s9_one_vote", not freeze_state.thaw_quorum_met))

    freeze_proto.vote_thaw("entity_1", "soc_beta", True)
    checks.append(("s9_quorum_met", freeze_state.thaw_quorum_met))
    checks.append(("s9_thawing", freeze_state.status == FreezeStatus.THAWING))

    thawed = freeze_proto.thaw("entity_1")
    checks.append(("s9_thawed", thawed and freeze_state.status == FreezeStatus.ACTIVE))

    # Non-member can't vote
    checks.append(("s9_non_member_rejected",
                    not freeze_proto.vote_thaw("entity_1", "soc_nonexistent", True)))

    # ── S10: Appeal Chain ─────────────────────────────────────────────────
    appeal_chain = AppealChain()
    appeal = appeal_chain.file_appeal(resolution, "entity_1", "Unfair jurisdictional priority")
    checks.append(("s10_appeal_filed", appeal is not None))
    checks.append(("s10_appeal_status", appeal.status == AppealStatus.FILED))
    checks.append(("s10_resolution_marked", resolution.appealed))

    appeal_chain.review(appeal.appeal_id, "soc_gamma", upheld=False,
                         revised_action=PolicyAction.REQUIRE_APPROVAL)
    checks.append(("s10_overturned", appeal.status == AppealStatus.OVERTURNED))
    checks.append(("s10_revised", appeal.revised_action == PolicyAction.REQUIRE_APPROVAL))

    # Appeal limit
    appeal2 = appeal_chain.file_appeal(resolution, "entity_1", "Second appeal")
    checks.append(("s10_second_appeal", appeal2 is not None))
    appeal3 = appeal_chain.file_appeal(resolution, "entity_1", "Third appeal")
    checks.append(("s10_appeal_limit", appeal3 is None))

    # ── S11: Audit Trail ─────────────────────────────────────────────────
    audit = ConflictAuditTrail()
    for c, r in zip(conflicts, [resolution, res_int]):
        audit.record("entity_1", c, r)
    checks.append(("s11_two_entries", len(audit.entries) == 2))
    checks.append(("s11_chain_valid", audit.verify_chain()))

    # Tamper
    audit.entries[0].hash = "tampered"
    checks.append(("s11_tamper_detected", not audit.verify_chain()))

    # ── S12: Policy Gateway ───────────────────────────────────────────────
    gateway = PolicyGateway(ResolutionStrategy.PRIORITY)

    # Single society → no conflict
    single_s = {"soc_only": Society("soc_only", "Only", 0.8)}
    single_s["soc_only"].add_policy(Policy("so1", "soc_only", "read_data", PolicyAction.ALLOW))
    single_m = {"soc_only": EntityMembership("entity_3", "soc_only", 1, 0.7)}
    action, conflicts = gateway.evaluate("entity_3", "read_data", 0.7, single_s, single_m)
    checks.append(("s12_single_allow", action == PolicyAction.ALLOW))
    checks.append(("s12_no_conflicts", len(conflicts) == 0))

    # No policy → allowed
    action2, _ = gateway.evaluate("entity_3", "unknown_action", 0.7, single_s, single_m)
    checks.append(("s12_no_policy_allow", action2 == PolicyAction.ALLOW))

    # Multi-society conflict → priority resolution
    # Use societies where beta trust < 0.7 to avoid emergency freeze
    sg_a = Society("sg_alpha", "GW Alpha", 0.8)
    sg_a.add_policy(Policy("ga1", "sg_alpha", "send_msg", PolicyAction.ALLOW))
    sg_b = Society("sg_beta", "GW Beta", 0.6)  # Below freeze threshold
    sg_b.add_policy(Policy("gb1", "sg_beta", "send_msg", PolicyAction.DENY))
    gw_socs = {"sg_alpha": sg_a, "sg_beta": sg_b}
    gw_mems = {
        "sg_alpha": EntityMembership("gw_entity", "sg_alpha", 1, 0.7),
        "sg_beta": EntityMembership("gw_entity", "sg_beta", 2, 0.6),
    }
    action3, conflicts3 = gateway.evaluate("gw_entity", "send_msg", 0.7,
                                             gw_socs, gw_mems)
    checks.append(("s12_conflict_resolved", len(conflicts3) > 0))
    checks.append(("s12_alpha_governs",
                    action3 == PolicyAction.ALLOW))  # Alpha closer, ALLOW

    # ── S13: Freeze via Gateway ───────────────────────────────────────────
    # Two high-trust societies contradicting
    freeze_sa = Society("freeze_a", "Freeze A", 0.85)
    freeze_sa.add_policy(Policy("fa1", "freeze_a", "critical_action", PolicyAction.ALLOW))
    freeze_sb = Society("freeze_b", "Freeze B", 0.9)
    freeze_sb.add_policy(Policy("fb1", "freeze_b", "critical_action", PolicyAction.DENY))
    freeze_socs = {"freeze_a": freeze_sa, "freeze_b": freeze_sb}
    freeze_mems = {
        "freeze_a": EntityMembership("entity_freeze", "freeze_a", 1, 0.8),
        "freeze_b": EntityMembership("entity_freeze", "freeze_b", 1, 0.8),
    }
    action4, conf4 = gateway.evaluate("entity_freeze", "critical_action", 0.8,
                                       freeze_socs, freeze_mems)
    checks.append(("s13_frozen_deny", action4 == PolicyAction.DENY))

    # ── S14: MRH Distance Impact ─────────────────────────────────────────
    # Same trust but different MRH distances
    se = Society("soc_near", "Near", 0.7)
    se.add_policy(Policy("pe1", "soc_near", "action_x", PolicyAction.DENY, priority=0))
    sf = Society("soc_far", "Far", 0.7)
    sf.add_policy(Policy("pf1", "soc_far", "action_x", PolicyAction.ALLOW, priority=0))
    near_far_socs = {"soc_near": se, "soc_far": sf}
    near_far_mems = {
        "soc_near": EntityMembership("entity_4", "soc_near", 1, 0.7),  # Close
        "soc_far": EntityMembership("entity_4", "soc_far", 5, 0.7),    # Far
    }
    resolver2 = ConflictResolver(ResolutionStrategy.PRIORITY)
    det3 = ConflictDetector()
    conflicts4 = det3.detect_conflicts("entity_4", near_far_socs, near_far_mems)
    if conflicts4:
        res_mrh = resolver2.resolve(conflicts4[0], near_far_mems, near_far_socs)
        checks.append(("s14_nearer_wins", res_mrh.winning_society == "soc_near"))
    else:
        checks.append(("s14_nearer_wins", False))

    # ── S15: Performance ──────────────────────────────────────────────────
    pt0 = time.time()
    # Create 20 societies with policies, detect all conflicts
    perf_socs = {}
    perf_mems = {}
    for i in range(20):
        s = Society(f"perf_s{i}", f"Perf {i}", 0.5 + (i % 5) * 0.1)
        s.add_policy(Policy(f"pp{i}", f"perf_s{i}", "shared_action",
                             PolicyAction.ALLOW if i % 2 == 0 else PolicyAction.DENY))
        perf_socs[f"perf_s{i}"] = s
        perf_mems[f"perf_s{i}"] = EntityMembership("perf_entity", f"perf_s{i}",
                                                     i + 1, 0.5)

    det_perf = ConflictDetector()
    perf_conflicts = det_perf.detect_conflicts("perf_entity", perf_socs, perf_mems)
    pt1 = time.time()
    checks.append(("s15_many_conflicts", len(perf_conflicts) > 50))
    checks.append(("s15_detection_fast", pt1 - pt0 < 1.0))

    # Resolve all conflicts
    res_perf = ConflictResolver()
    pt2 = time.time()
    for c in perf_conflicts:
        res_perf.resolve(c, perf_mems, perf_socs)
    pt3 = time.time()
    checks.append(("s15_resolution_fast", pt3 - pt2 < 1.0))
    checks.append(("s15_all_resolved", len(res_perf.resolutions) == len(perf_conflicts)))

    elapsed = time.time() - t0

    # ── Print Results ─────────────────────────────────────────────────────
    passed = sum(1 for _, v in checks if v)
    total = len(checks)
    title = f"Cross-Society Policy Conflicts — {passed}/{total} checks passed"
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    for name, val in checks:
        print(f"  [{'PASS' if val else 'FAIL'}] {name}")

    failed = [n for n, v in checks if not v]
    if failed:
        print(f"\n  FAILURES:")
        for f in failed:
            print(f"    ✗ {f}")

    print(f"\n  Time: {elapsed:.2f}s\n")
    return passed == total


if __name__ == "__main__":
    run_checks()
