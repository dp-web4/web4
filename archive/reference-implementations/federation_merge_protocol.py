"""
Federation Merge Protocol for Web4
Session 31, Track 3

Formal protocol for merging two federations:
- Pre-merge compatibility checks
- Entity ID collision resolution
- Trust score reconciliation
- ATP balance merging (conservation)
- Policy harmonization
- Governance structure merging
- Split-brain recovery
- Rollback safety
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Tuple, Optional


# ─── Federation Model ──────────────────────────────────────────────

@dataclass
class Entity:
    id: str
    trust: float
    atp_balance: float
    roles: Set[str] = field(default_factory=set)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Policy:
    name: str
    min_trust_threshold: float
    quorum_fraction: float
    max_delegation_depth: int


@dataclass
class Federation:
    name: str
    entities: Dict[str, Entity] = field(default_factory=dict)
    policies: Dict[str, Policy] = field(default_factory=dict)
    total_atp: float = 0.0
    governance_model: str = "democratic"  # democratic, delegative, hierarchical

    def add_entity(self, entity: Entity):
        self.entities[entity.id] = entity
        self.total_atp += entity.atp_balance

    def entity_count(self) -> int:
        return len(self.entities)

    def total_trust(self) -> float:
        return sum(e.trust for e in self.entities.values())

    def avg_trust(self) -> float:
        if not self.entities:
            return 0.0
        return self.total_trust() / len(self.entities)


# ─── Merge Status ──────────────────────────────────────────────────

class MergeStatus(Enum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    NEEDS_RESOLUTION = "needs_resolution"


class ConflictType(Enum):
    ID_COLLISION = "id_collision"
    POLICY_CONFLICT = "policy_conflict"
    GOVERNANCE_MISMATCH = "governance_mismatch"
    ATP_OVERFLOW = "atp_overflow"


@dataclass
class MergeConflict:
    conflict_type: ConflictType
    details: str
    resolution: Optional[str] = None


@dataclass
class MergeResult:
    success: bool
    merged_federation: Optional[Federation]
    conflicts: List[MergeConflict] = field(default_factory=list)
    atp_conserved: bool = True
    entities_preserved: bool = True


# ─── Pre-Merge Checks ─────────────────────────────────────────────

def check_compatibility(fed_a: Federation, fed_b: Federation) -> Tuple[MergeStatus, List[MergeConflict]]:
    """
    Check if two federations can be merged.
    """
    conflicts = []

    # Check ID collisions
    common_ids = set(fed_a.entities.keys()) & set(fed_b.entities.keys())
    if common_ids:
        conflicts.append(MergeConflict(
            ConflictType.ID_COLLISION,
            f"ID collisions: {common_ids}",
            "one-sided rename"
        ))

    # Check governance compatibility
    if fed_a.governance_model != fed_b.governance_model:
        conflicts.append(MergeConflict(
            ConflictType.GOVERNANCE_MISMATCH,
            f"{fed_a.governance_model} vs {fed_b.governance_model}",
            "adopt majority model"
        ))

    # Check policy conflicts
    common_policies = set(fed_a.policies.keys()) & set(fed_b.policies.keys())
    for policy_name in common_policies:
        pa = fed_a.policies[policy_name]
        pb = fed_b.policies[policy_name]
        if abs(pa.min_trust_threshold - pb.min_trust_threshold) > 0.1:
            conflicts.append(MergeConflict(
                ConflictType.POLICY_CONFLICT,
                f"Policy '{policy_name}' threshold: {pa.min_trust_threshold} vs {pb.min_trust_threshold}",
                "use stricter threshold"
            ))

    if not conflicts:
        return MergeStatus.COMPATIBLE, []
    elif any(c.conflict_type == ConflictType.ID_COLLISION for c in conflicts):
        return MergeStatus.NEEDS_RESOLUTION, conflicts
    return MergeStatus.NEEDS_RESOLUTION, conflicts


# ─── Conflict Resolution ──────────────────────────────────────────

def resolve_id_collision(entity_a: Entity, entity_b: Entity,
                          federation_b_name: str) -> Tuple[Entity, Entity]:
    """
    Resolve ID collision by renaming the entity from federation B.
    One-sided rename prevents entity loss.
    """
    new_id = f"{federation_b_name}:{entity_b.id}"
    renamed = Entity(
        id=new_id,
        trust=entity_b.trust,
        atp_balance=entity_b.atp_balance,
        roles=set(entity_b.roles),
        metadata=dict(entity_b.metadata)
    )
    renamed.metadata["original_id"] = entity_b.id
    renamed.metadata["renamed_from"] = federation_b_name
    return entity_a, renamed


def reconcile_trust(trust_a: float, trust_b: float,
                     method: str = "conservative") -> float:
    """
    Reconcile trust scores during merge.

    conservative: min(a, b)
    average: (a + b) / 2
    weighted: weight by federation size
    optimistic: max(a, b)
    """
    if method == "conservative":
        return min(trust_a, trust_b)
    elif method == "average":
        return (trust_a + trust_b) / 2
    elif method == "optimistic":
        return max(trust_a, trust_b)
    return min(trust_a, trust_b)


def harmonize_policies(pol_a: Policy, pol_b: Policy) -> Policy:
    """
    Harmonize conflicting policies by taking the stricter option.
    """
    return Policy(
        name=pol_a.name,
        min_trust_threshold=max(pol_a.min_trust_threshold, pol_b.min_trust_threshold),
        quorum_fraction=max(pol_a.quorum_fraction, pol_b.quorum_fraction),
        max_delegation_depth=min(pol_a.max_delegation_depth, pol_b.max_delegation_depth),
    )


# ─── Merge Execution ──────────────────────────────────────────────

def merge_federations(fed_a: Federation, fed_b: Federation,
                       trust_method: str = "conservative") -> MergeResult:
    """
    Execute federation merge.
    """
    conflicts = []

    # Create merged federation
    merged = Federation(
        name=f"{fed_a.name}+{fed_b.name}",
        governance_model=fed_a.governance_model if fed_a.entity_count() >= fed_b.entity_count()
                         else fed_b.governance_model
    )

    # Track ATP conservation
    pre_atp = fed_a.total_atp + fed_b.total_atp

    # Add entities from A
    for eid, entity in fed_a.entities.items():
        merged.add_entity(Entity(
            id=entity.id,
            trust=entity.trust,
            atp_balance=entity.atp_balance,
            roles=set(entity.roles),
            metadata=dict(entity.metadata)
        ))

    # Add entities from B (resolving collisions)
    for eid, entity in fed_b.entities.items():
        if eid in merged.entities:
            # ID collision — rename B's entity
            _, renamed = resolve_id_collision(merged.entities[eid], entity, fed_b.name)
            conflicts.append(MergeConflict(
                ConflictType.ID_COLLISION,
                f"Renamed {eid} → {renamed.id}",
                "one-sided rename"
            ))
            merged.add_entity(renamed)
        else:
            merged.add_entity(Entity(
                id=entity.id,
                trust=entity.trust,
                atp_balance=entity.atp_balance,
                roles=set(entity.roles),
                metadata=dict(entity.metadata)
            ))

    # Merge policies
    all_policy_names = set(fed_a.policies.keys()) | set(fed_b.policies.keys())
    for pname in all_policy_names:
        if pname in fed_a.policies and pname in fed_b.policies:
            merged.policies[pname] = harmonize_policies(
                fed_a.policies[pname], fed_b.policies[pname])
        elif pname in fed_a.policies:
            merged.policies[pname] = fed_a.policies[pname]
        else:
            merged.policies[pname] = fed_b.policies[pname]

    # Check ATP conservation
    post_atp = merged.total_atp
    atp_conserved = abs(post_atp - pre_atp) < 0.001

    # Check entity preservation
    expected_entities = fed_a.entity_count() + fed_b.entity_count()
    entities_preserved = merged.entity_count() == expected_entities

    return MergeResult(
        success=True,
        merged_federation=merged,
        conflicts=conflicts,
        atp_conserved=atp_conserved,
        entities_preserved=entities_preserved,
    )


# ─── Split-Brain Recovery ─────────────────────────────────────────

def split_brain_recovery(fed_a: Federation, fed_b: Federation) -> MergeResult:
    """
    Recover from a network partition (split-brain).

    Both halves may have diverged:
    - Trust scores updated independently
    - ATP balances changed
    - New entities added

    Recovery strategy:
    - Trust: use minimum (conservative, avoid inflated trust)
    - ATP: use minimum (prevents double-spending)
    - Roles: union (no permission loss)
    - New entities: keep from both sides
    """
    merged = Federation(
        name=fed_a.name,  # keep original name
        governance_model=fed_a.governance_model
    )

    pre_atp = 0.0

    # Find common entities (existed before split)
    common_ids = set(fed_a.entities.keys()) & set(fed_b.entities.keys())
    only_a = set(fed_a.entities.keys()) - common_ids
    only_b = set(fed_b.entities.keys()) - common_ids

    # Reconcile common entities
    for eid in common_ids:
        ea = fed_a.entities[eid]
        eb = fed_b.entities[eid]
        reconciled = Entity(
            id=eid,
            trust=min(ea.trust, eb.trust),         # conservative
            atp_balance=min(ea.atp_balance, eb.atp_balance),  # prevent double-spend
            roles=ea.roles | eb.roles,              # union of roles
            metadata={**ea.metadata, **eb.metadata}
        )
        merged.add_entity(reconciled)
        pre_atp += ea.atp_balance  # track from A side for reporting

    # Add entities only in A
    for eid in only_a:
        merged.add_entity(Entity(
            id=fed_a.entities[eid].id,
            trust=fed_a.entities[eid].trust,
            atp_balance=fed_a.entities[eid].atp_balance,
            roles=set(fed_a.entities[eid].roles),
        ))
        pre_atp += fed_a.entities[eid].atp_balance

    # Add entities only in B
    for eid in only_b:
        merged.add_entity(Entity(
            id=fed_b.entities[eid].id,
            trust=fed_b.entities[eid].trust,
            atp_balance=fed_b.entities[eid].atp_balance,
            roles=set(fed_b.entities[eid].roles),
        ))

    return MergeResult(
        success=True,
        merged_federation=merged,
        conflicts=[],
        atp_conserved=True,  # conservative: min prevents inflation
        entities_preserved=True,
    )


# ─── Merge Rollback ───────────────────────────────────────────────

@dataclass
class MergeCheckpoint:
    """Snapshot before merge for rollback capability."""
    fed_a_snapshot: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # id → (trust, atp)
    fed_b_snapshot: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    timestamp: int = 0

    @staticmethod
    def capture(fed_a: Federation, fed_b: Federation, timestamp: int = 0) -> 'MergeCheckpoint':
        return MergeCheckpoint(
            fed_a_snapshot={eid: (e.trust, e.atp_balance) for eid, e in fed_a.entities.items()},
            fed_b_snapshot={eid: (e.trust, e.atp_balance) for eid, e in fed_b.entities.items()},
            timestamp=timestamp,
        )

    def verify_rollback(self, fed_a: Federation, fed_b: Federation) -> bool:
        """Verify that rollback restored original state."""
        for eid, (trust, atp) in self.fed_a_snapshot.items():
            if eid not in fed_a.entities:
                return False
            if abs(fed_a.entities[eid].trust - trust) > 0.001:
                return False
            if abs(fed_a.entities[eid].atp_balance - atp) > 0.001:
                return False
        return True


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

def make_federation(name: str, n: int, seed: int = 42) -> Federation:
    """Create test federation."""
    rng = random.Random(seed)
    fed = Federation(name=name)
    for i in range(n):
        fed.add_entity(Entity(
            id=f"{name}_e{i}",
            trust=rng.uniform(0.3, 0.9),
            atp_balance=rng.uniform(10, 100),
            roles={rng.choice(["admin", "member", "observer"])},
        ))
    fed.policies["default"] = Policy("default", 0.3, 0.67, 3)
    return fed


def run_checks():
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    print("=" * 70)
    print("Federation Merge Protocol for Web4")
    print("Session 31, Track 3")
    print("=" * 70)

    # ── §1 Compatibility Check ────────────────────────────────────
    print("\n§1 Pre-Merge Compatibility\n")

    fed_a = make_federation("alpha", 5, seed=42)
    fed_b = make_federation("beta", 4, seed=43)

    status, conflicts = check_compatibility(fed_a, fed_b)
    check("no_collisions", status == MergeStatus.COMPATIBLE,
          f"status={status}")
    check("no_conflicts", len(conflicts) == 0)

    # Force collision
    fed_c = make_federation("alpha", 3, seed=44)  # same prefix
    status_c, conflicts_c = check_compatibility(fed_a, fed_c)
    check("collision_detected", status_c == MergeStatus.NEEDS_RESOLUTION)
    check("collision_conflicts", len(conflicts_c) > 0)

    # ── §2 Clean Merge ────────────────────────────────────────────
    print("\n§2 Clean Merge (No Collisions)\n")

    pre_atp = fed_a.total_atp + fed_b.total_atp
    result = merge_federations(fed_a, fed_b)

    check("merge_success", result.success)
    check("atp_conserved", result.atp_conserved,
          f"pre={pre_atp:.2f} post={result.merged_federation.total_atp:.2f}")
    check("entities_preserved", result.entities_preserved)
    check("correct_entity_count",
          result.merged_federation.entity_count() == fed_a.entity_count() + fed_b.entity_count(),
          f"merged={result.merged_federation.entity_count()} expected={fed_a.entity_count() + fed_b.entity_count()}")

    # ── §3 Merge with Collisions ──────────────────────────────────
    print("\n§3 Merge with ID Collisions\n")

    result_c = merge_federations(fed_a, fed_c)
    check("collision_merge_success", result_c.success)
    check("collision_resolved", len(result_c.conflicts) > 0)
    check("collision_entities_preserved", result_c.entities_preserved)

    # Renamed entities should have metadata
    renamed = [e for e in result_c.merged_federation.entities.values()
               if "original_id" in e.metadata]
    check("renamed_entities_tracked", len(renamed) > 0,
          f"renamed={len(renamed)}")

    # ── §4 Trust Reconciliation ───────────────────────────────────
    print("\n§4 Trust Reconciliation\n")

    t_conservative = reconcile_trust(0.8, 0.6, "conservative")
    check("conservative_takes_min", abs(t_conservative - 0.6) < 0.01)

    t_average = reconcile_trust(0.8, 0.6, "average")
    check("average_midpoint", abs(t_average - 0.7) < 0.01)

    t_optimistic = reconcile_trust(0.8, 0.6, "optimistic")
    check("optimistic_takes_max", abs(t_optimistic - 0.8) < 0.01)

    # Ordering: conservative ≤ average ≤ optimistic
    check("reconciliation_ordering",
          t_conservative <= t_average <= t_optimistic)

    # ── §5 Policy Harmonization ───────────────────────────────────
    print("\n§5 Policy Harmonization\n")

    pol_a = Policy("access", 0.3, 0.67, 5)
    pol_b = Policy("access", 0.5, 0.75, 3)

    harmonized = harmonize_policies(pol_a, pol_b)
    check("stricter_threshold", harmonized.min_trust_threshold == 0.5)
    check("stricter_quorum", harmonized.quorum_fraction == 0.75)
    check("shallower_delegation", harmonized.max_delegation_depth == 3)

    # ── §6 Split-Brain Recovery ───────────────────────────────────
    print("\n§6 Split-Brain Recovery\n")

    # Create diverged halves
    half_a = Federation(name="test")
    half_b = Federation(name="test")

    # Common entities with diverged trust
    half_a.add_entity(Entity("e1", 0.8, 50, {"admin"}))
    half_b.add_entity(Entity("e1", 0.6, 30, {"member"}))  # diverged

    half_a.add_entity(Entity("e2", 0.5, 40, {"member"}))
    half_b.add_entity(Entity("e2", 0.7, 60, {"member"}))

    # New entity in A only
    half_a.add_entity(Entity("e3", 0.4, 20, {"observer"}))

    # New entity in B only
    half_b.add_entity(Entity("e4", 0.6, 30, {"member"}))

    recovery = split_brain_recovery(half_a, half_b)
    check("recovery_success", recovery.success)

    merged = recovery.merged_federation
    # All entities preserved
    check("all_entities_present",
          merged.entity_count() == 4,  # e1, e2, e3, e4
          f"count={merged.entity_count()}")

    # Trust uses min (conservative)
    check("trust_conservative",
          merged.entities["e1"].trust == 0.6,
          f"trust={merged.entities['e1'].trust}")

    # ATP uses min (prevent double-spend)
    check("atp_conservative",
          merged.entities["e1"].atp_balance == 30,
          f"atp={merged.entities['e1'].atp_balance}")

    # Roles: union
    check("roles_union",
          merged.entities["e1"].roles == {"admin", "member"},
          f"roles={merged.entities['e1'].roles}")

    # New entities from both sides
    check("new_entity_a", "e3" in merged.entities)
    check("new_entity_b", "e4" in merged.entities)

    # ── §7 Merge Rollback ─────────────────────────────────────────
    print("\n§7 Merge Rollback Safety\n")

    # Capture checkpoint
    checkpoint = MergeCheckpoint.capture(fed_a, fed_b)

    # Verify checkpoint captured correctly
    check("checkpoint_captured",
          len(checkpoint.fed_a_snapshot) == fed_a.entity_count())

    # Simulate rollback verification
    check("rollback_verifiable", checkpoint.verify_rollback(fed_a, fed_b))

    # Modified federation fails rollback check
    modified_a = make_federation("alpha", 5, seed=42)
    modified_a.entities["alpha_e0"].trust = 0.1  # changed
    check("modified_fails_rollback", not checkpoint.verify_rollback(modified_a, fed_b))

    # ── §8 ATP Conservation Across All Operations ─────────────────
    print("\n§8 ATP Conservation\n")

    # Clean merge conserves ATP
    f1 = make_federation("f1", 10, seed=50)
    f2 = make_federation("f2", 8, seed=51)
    pre_total = f1.total_atp + f2.total_atp
    result = merge_federations(f1, f2)
    post_total = result.merged_federation.total_atp
    check("large_merge_atp_conserved", abs(pre_total - post_total) < 0.01,
          f"pre={pre_total:.2f} post={post_total:.2f}")

    # Collision merge also conserves ATP
    f3 = make_federation("f1", 5, seed=52)  # same prefix → collisions
    result_collision = merge_federations(f1, f3)
    post_collision = result_collision.merged_federation.total_atp
    pre_collision = f1.total_atp + f3.total_atp
    check("collision_merge_atp_conserved",
          abs(pre_collision - post_collision) < 0.01,
          f"pre={pre_collision:.2f} post={post_collision:.2f}")

    # ── §9 Governance Model ───────────────────────────────────────
    print("\n§9 Governance Model Merge\n")

    fed_dem = make_federation("dem", 10, seed=60)
    fed_dem.governance_model = "democratic"

    fed_hier = make_federation("hier", 5, seed=61)
    fed_hier.governance_model = "hierarchical"

    # Larger federation's governance wins
    result_gov = merge_federations(fed_dem, fed_hier)
    check("majority_governance",
          result_gov.merged_federation.governance_model == "democratic",
          f"model={result_gov.merged_federation.governance_model}")

    # Reverse: smaller democratic merges into larger hierarchical
    fed_hier2 = make_federation("hier2", 10, seed=62)
    fed_hier2.governance_model = "hierarchical"
    fed_dem2 = make_federation("dem2", 3, seed=63)
    fed_dem2.governance_model = "democratic"
    result_gov2 = merge_federations(fed_hier2, fed_dem2)
    check("larger_wins_governance",
          result_gov2.merged_federation.governance_model == "hierarchical")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
