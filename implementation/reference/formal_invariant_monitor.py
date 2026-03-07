#!/usr/bin/env python3
"""
Formal Invariant Monitor — Cross-Layer Continuous Verification — Session 28, Track 7
=====================================================================================

A continuous invariant checker that monitors all 5 Web4 layers (Entity, Trust,
ATP, LCT, Federation) for property violations. Currently, invariants are
checked in isolation per-module. This monitor verifies CROSS-LAYER properties
that only hold when layers interact correctly.

Invariants monitored:
  1. ATP Conservation: total ATP is constant across all operations
  2. Trust Bounds: T3 scores always in [0, 1]
  3. LCT Uniqueness: no two entities share an LCT ID
  4. Authority-Trust Coherence: authorities have trust ≥ threshold
  5. Revocation Completeness: revoked LCTs have no active children
  6. Federation Partition Safety: ATP doesn't duplicate across partitions
  7. Delegation Depth: AGY delegation chains ≤ max depth
  8. Role-Permission Consistency: granted roles match available permissions
  9. Temporal Monotonicity: Lamport timestamps never decrease for a process
  10. Attestation Integrity: attestations reference valid entities

~55 checks expected.
"""

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Callable

passed = 0
failed = 0
errors = []


def check(condition, msg):
    global passed, failed, errors
    if condition:
        passed += 1
    else:
        failed += 1
        errors.append(msg)
        print(f"  FAIL: {msg}")


# ============================================================
# §1 — Invariant Framework
# ============================================================

class InvariantSeverity(Enum):
    CRITICAL = "critical"   # System MUST halt if violated
    HIGH = "high"           # Operation must be rolled back
    MEDIUM = "medium"       # Warning, may need investigation
    LOW = "low"             # Informational


@dataclass
class InvariantViolation:
    """A detected invariant violation."""
    invariant_name: str
    severity: InvariantSeverity
    message: str
    layer: str  # Which Web4 layer
    context: Dict = field(default_factory=dict)


@dataclass
class Invariant:
    """A formal invariant to be continuously monitored."""
    name: str
    description: str
    severity: InvariantSeverity
    layer: str
    check_fn: Callable[['SystemState'], List[InvariantViolation]]
    enabled: bool = True


class InvariantMonitor:
    """Continuous invariant monitor for Web4 system state."""

    def __init__(self):
        self.invariants: List[Invariant] = []
        self.violations_history: List[InvariantViolation] = []
        self.check_count = 0

    def register(self, invariant: Invariant):
        self.invariants.append(invariant)

    def check_all(self, state: 'SystemState') -> List[InvariantViolation]:
        """Check all enabled invariants against current state."""
        self.check_count += 1
        violations = []
        for inv in self.invariants:
            if inv.enabled:
                new_violations = inv.check_fn(state)
                violations.extend(new_violations)
        self.violations_history.extend(violations)
        return violations

    def violation_count(self) -> int:
        return len(self.violations_history)

    def critical_violations(self) -> List[InvariantViolation]:
        return [v for v in self.violations_history
                if v.severity == InvariantSeverity.CRITICAL]

    def violations_by_layer(self) -> Dict[str, int]:
        counts = defaultdict(int)
        for v in self.violations_history:
            counts[v.layer] += 1
        return dict(counts)


# ============================================================
# §2 — System State Model
# ============================================================

@dataclass
class EntityRecord:
    entity_id: str
    lct_id: str
    trust_scores: Dict[str, float] = field(default_factory=dict)
    atp_balance: float = 100.0
    roles: Set[str] = field(default_factory=set)
    is_authority: bool = False
    is_revoked: bool = False
    federation_id: str = ""
    delegation_parent: Optional[str] = None
    delegation_depth: int = 0
    lamport_time: int = 0


@dataclass
class AttestationRecord:
    attestor_id: str
    target_id: str
    dimension: str
    value: float
    timestamp: int = 0


@dataclass
class SystemState:
    """Complete system state for invariant checking."""
    entities: Dict[str, EntityRecord] = field(default_factory=dict)
    lct_registry: Dict[str, str] = field(default_factory=dict)  # lct_id -> entity_id
    attestations: List[AttestationRecord] = field(default_factory=list)
    atp_pool: float = 0.0
    total_initial_atp: float = 0.0
    federations: Dict[str, Set[str]] = field(default_factory=dict)  # fed_id -> entity_ids
    authority_threshold: float = 0.7
    max_delegation_depth: int = 5
    available_roles: Set[str] = field(default_factory=lambda: {"member", "authority", "attestor", "admin"})
    revocation_children: Dict[str, Set[str]] = field(default_factory=dict)  # entity -> children


# ============================================================
# §3 — Invariant Definitions
# ============================================================

def check_atp_conservation(state: SystemState) -> List[InvariantViolation]:
    """ATP Conservation: total ATP is constant."""
    total = state.atp_pool + sum(e.atp_balance for e in state.entities.values())
    if abs(total - state.total_initial_atp) > 0.01:
        return [InvariantViolation(
            "atp_conservation", InvariantSeverity.CRITICAL,
            f"ATP total {total:.2f} != initial {state.total_initial_atp:.2f} "
            f"(diff={total - state.total_initial_atp:.4f})",
            "ATP"
        )]
    return []


def check_trust_bounds(state: SystemState) -> List[InvariantViolation]:
    """Trust Bounds: all T3 scores in [0, 1]."""
    violations = []
    for eid, entity in state.entities.items():
        for dim, score in entity.trust_scores.items():
            if score < -0.001 or score > 1.001:
                violations.append(InvariantViolation(
                    "trust_bounds", InvariantSeverity.HIGH,
                    f"Entity {eid} dimension {dim} = {score:.4f} out of [0,1]",
                    "Trust"
                ))
    return violations


def check_lct_uniqueness(state: SystemState) -> List[InvariantViolation]:
    """LCT Uniqueness: no two entities share an LCT ID."""
    lct_to_entities = defaultdict(list)
    for eid, entity in state.entities.items():
        if entity.lct_id:
            lct_to_entities[entity.lct_id].append(eid)

    violations = []
    for lct_id, entities in lct_to_entities.items():
        if len(entities) > 1:
            violations.append(InvariantViolation(
                "lct_uniqueness", InvariantSeverity.CRITICAL,
                f"LCT {lct_id} shared by {entities}",
                "LCT"
            ))
    return violations


def check_authority_trust(state: SystemState) -> List[InvariantViolation]:
    """Authority-Trust Coherence: authorities have trust ≥ threshold."""
    violations = []
    for eid, entity in state.entities.items():
        if entity.is_authority:
            composite = entity.trust_scores.get("composite", 0.0)
            if composite < state.authority_threshold:
                violations.append(InvariantViolation(
                    "authority_trust", InvariantSeverity.HIGH,
                    f"Authority {eid} trust {composite:.2f} < threshold {state.authority_threshold}",
                    "Trust"
                ))
    return violations


def check_revocation_completeness(state: SystemState) -> List[InvariantViolation]:
    """Revoked LCTs should not have active (non-revoked) children."""
    violations = []
    for eid, entity in state.entities.items():
        if entity.is_revoked:
            children = state.revocation_children.get(eid, set())
            for child_id in children:
                child = state.entities.get(child_id)
                if child and not child.is_revoked:
                    violations.append(InvariantViolation(
                        "revocation_completeness", InvariantSeverity.HIGH,
                        f"Revoked {eid} has active child {child_id}",
                        "LCT"
                    ))
    return violations


def check_federation_atp_partition(state: SystemState) -> List[InvariantViolation]:
    """Federation partition safety: no entity in multiple federations."""
    violations = []
    entity_feds = defaultdict(list)
    for fed_id, members in state.federations.items():
        for eid in members:
            entity_feds[eid].append(fed_id)

    for eid, feds in entity_feds.items():
        if len(feds) > 1:
            violations.append(InvariantViolation(
                "federation_partition", InvariantSeverity.CRITICAL,
                f"Entity {eid} in multiple federations: {feds}",
                "Federation"
            ))
    return violations


def check_delegation_depth(state: SystemState) -> List[InvariantViolation]:
    """Delegation depth: chains ≤ max depth."""
    violations = []
    for eid, entity in state.entities.items():
        if entity.delegation_depth > state.max_delegation_depth:
            violations.append(InvariantViolation(
                "delegation_depth", InvariantSeverity.MEDIUM,
                f"Entity {eid} delegation depth {entity.delegation_depth} > max {state.max_delegation_depth}",
                "Entity"
            ))
    return violations


def check_role_permission(state: SystemState) -> List[InvariantViolation]:
    """Role-Permission: entities only have defined roles."""
    violations = []
    for eid, entity in state.entities.items():
        invalid = entity.roles - state.available_roles
        if invalid:
            violations.append(InvariantViolation(
                "role_permission", InvariantSeverity.MEDIUM,
                f"Entity {eid} has undefined roles: {invalid}",
                "Entity"
            ))
    return violations


def check_temporal_monotonicity(state: SystemState) -> List[InvariantViolation]:
    """Lamport timestamps never decrease for a process."""
    violations = []
    # Check that attestation timestamps are non-decreasing per attestor
    attestor_times = defaultdict(list)
    for att in state.attestations:
        attestor_times[att.attestor_id].append(att.timestamp)

    for attestor, times in attestor_times.items():
        for i in range(1, len(times)):
            if times[i] < times[i - 1]:
                violations.append(InvariantViolation(
                    "temporal_monotonicity", InvariantSeverity.HIGH,
                    f"Attestor {attestor} timestamp decreased: {times[i-1]} → {times[i]}",
                    "Trust"
                ))
    return violations


def check_attestation_integrity(state: SystemState) -> List[InvariantViolation]:
    """Attestations reference valid entities."""
    violations = []
    for att in state.attestations:
        if att.attestor_id not in state.entities:
            violations.append(InvariantViolation(
                "attestation_integrity", InvariantSeverity.HIGH,
                f"Attestation by unknown entity {att.attestor_id}",
                "Trust"
            ))
        if att.target_id not in state.entities:
            violations.append(InvariantViolation(
                "attestation_integrity", InvariantSeverity.HIGH,
                f"Attestation targets unknown entity {att.target_id}",
                "Trust"
            ))
    return violations


# ============================================================
# §4 — Monitor Builder
# ============================================================

def build_full_monitor() -> InvariantMonitor:
    """Build a monitor with all Web4 invariants."""
    monitor = InvariantMonitor()

    invariants = [
        Invariant("atp_conservation", "Total ATP is constant", InvariantSeverity.CRITICAL, "ATP", check_atp_conservation),
        Invariant("trust_bounds", "T3 scores in [0,1]", InvariantSeverity.HIGH, "Trust", check_trust_bounds),
        Invariant("lct_uniqueness", "No shared LCT IDs", InvariantSeverity.CRITICAL, "LCT", check_lct_uniqueness),
        Invariant("authority_trust", "Authorities meet trust threshold", InvariantSeverity.HIGH, "Trust", check_authority_trust),
        Invariant("revocation_completeness", "Revoked entities cascade to children", InvariantSeverity.HIGH, "LCT", check_revocation_completeness),
        Invariant("federation_partition", "Entities in at most one federation", InvariantSeverity.CRITICAL, "Federation", check_federation_atp_partition),
        Invariant("delegation_depth", "Delegation chains bounded", InvariantSeverity.MEDIUM, "Entity", check_delegation_depth),
        Invariant("role_permission", "Roles are from defined set", InvariantSeverity.MEDIUM, "Entity", check_role_permission),
        Invariant("temporal_monotonicity", "Timestamps non-decreasing", InvariantSeverity.HIGH, "Trust", check_temporal_monotonicity),
        Invariant("attestation_integrity", "Attestations reference valid entities", InvariantSeverity.HIGH, "Trust", check_attestation_integrity),
    ]

    for inv in invariants:
        monitor.register(inv)

    return monitor


# ============================================================
# §5 — Test Helpers
# ============================================================

def create_valid_state(n_entities: int = 5) -> SystemState:
    """Create a valid system state for testing."""
    state = SystemState()
    rng = random.Random(42)

    for i in range(n_entities):
        eid = f"entity_{i}"
        entity = EntityRecord(
            entity_id=eid,
            lct_id=f"lct_{i:04x}",
            trust_scores={"composite": 0.5 + rng.random() * 0.3,
                         "talent": 0.6, "training": 0.5, "temperament": 0.7},
            atp_balance=100.0,
            roles={"member"},
            federation_id="fed_a",
            lamport_time=i,
        )
        state.entities[eid] = entity
        state.lct_registry[entity.lct_id] = eid

    state.atp_pool = 50.0
    state.total_initial_atp = state.atp_pool + sum(
        e.atp_balance for e in state.entities.values()
    )
    state.federations["fed_a"] = {f"entity_{i}" for i in range(n_entities)}

    # Add some attestations
    for i in range(n_entities - 1):
        state.attestations.append(AttestationRecord(
            attestor_id=f"entity_{i}",
            target_id=f"entity_{i + 1}",
            dimension="composite",
            value=0.7,
            timestamp=i + 1,
        ))

    return state


# ============================================================
# §6 — Tests
# ============================================================

def test_valid_state():
    """§6.1: Valid state passes all invariants."""
    print("\n§6.1 Valid State Monitoring")

    monitor = build_full_monitor()
    state = create_valid_state(5)

    # s1: All invariants pass on valid state
    violations = monitor.check_all(state)
    check(len(violations) == 0,
          f"s1: valid state has no violations (got {len(violations)})")

    # s2: Monitor registered all 10 invariants
    check(len(monitor.invariants) == 10,
          f"s2: 10 invariants registered (got {len(monitor.invariants)})")

    # s3: Check count incremented
    check(monitor.check_count == 1, "s3: check count = 1")


def test_atp_conservation():
    """§6.2: ATP conservation invariant."""
    print("\n§6.2 ATP Conservation")

    monitor = build_full_monitor()

    # s4: Valid transfers preserve ATP
    state = create_valid_state(3)
    # Transfer 10 from entity_0 to entity_1
    state.entities["entity_0"].atp_balance -= 10
    state.entities["entity_1"].atp_balance += 10
    violations = monitor.check_all(state)
    atp_violations = [v for v in violations if v.invariant_name == "atp_conservation"]
    check(len(atp_violations) == 0, "s4: valid transfer preserves ATP")

    # s5: ATP creation detected
    state2 = create_valid_state(3)
    state2.entities["entity_0"].atp_balance += 50  # Create ATP from nothing
    violations2 = monitor.check_all(state2)
    atp_v = [v for v in violations2 if v.invariant_name == "atp_conservation"]
    check(len(atp_v) > 0, "s5: ATP creation detected as violation")
    check(atp_v[0].severity == InvariantSeverity.CRITICAL, "s5b: ATP violation is CRITICAL")

    # s6: ATP destruction detected
    state3 = create_valid_state(3)
    state3.entities["entity_0"].atp_balance -= 50  # Destroy ATP
    violations3 = monitor.check_all(state3)
    atp_v3 = [v for v in violations3 if v.invariant_name == "atp_conservation"]
    check(len(atp_v3) > 0, "s6: ATP destruction detected")


def test_trust_bounds():
    """§6.3: Trust score bounds invariant."""
    print("\n§6.3 Trust Bounds")

    monitor = build_full_monitor()

    # s7: Valid trust scores pass
    state = create_valid_state(3)
    violations = monitor.check_all(state)
    trust_v = [v for v in violations if v.invariant_name == "trust_bounds"]
    check(len(trust_v) == 0, "s7: valid trust scores pass")

    # s8: Score > 1 detected
    state.entities["entity_0"].trust_scores["composite"] = 1.5
    violations2 = monitor.check_all(state)
    trust_v2 = [v for v in violations2 if v.invariant_name == "trust_bounds"]
    check(len(trust_v2) > 0, "s8: trust > 1 detected")

    # s9: Score < 0 detected
    state.entities["entity_0"].trust_scores["composite"] = -0.1
    violations3 = monitor.check_all(state)
    trust_v3 = [v for v in violations3 if v.invariant_name == "trust_bounds"]
    check(len(trust_v3) > 0, "s9: trust < 0 detected")


def test_lct_uniqueness():
    """§6.4: LCT uniqueness invariant."""
    print("\n§6.4 LCT Uniqueness")

    monitor = build_full_monitor()
    state = create_valid_state(3)

    # s10: Unique LCTs pass
    violations = monitor.check_all(state)
    lct_v = [v for v in violations if v.invariant_name == "lct_uniqueness"]
    check(len(lct_v) == 0, "s10: unique LCTs pass")

    # s11: Duplicate LCT detected
    state.entities["entity_1"].lct_id = state.entities["entity_0"].lct_id
    violations2 = monitor.check_all(state)
    lct_v2 = [v for v in violations2 if v.invariant_name == "lct_uniqueness"]
    check(len(lct_v2) > 0, "s11: duplicate LCT detected")
    check(lct_v2[0].severity == InvariantSeverity.CRITICAL, "s11b: LCT duplication is CRITICAL")


def test_authority_trust():
    """§6.5: Authority-trust coherence."""
    print("\n§6.5 Authority-Trust Coherence")

    monitor = build_full_monitor()
    state = create_valid_state(3)

    # s12: High-trust authority passes
    state.entities["entity_0"].is_authority = True
    state.entities["entity_0"].trust_scores["composite"] = 0.9
    violations = monitor.check_all(state)
    auth_v = [v for v in violations if v.invariant_name == "authority_trust"]
    check(len(auth_v) == 0, "s12: high-trust authority passes")

    # s13: Low-trust authority detected
    state.entities["entity_0"].trust_scores["composite"] = 0.3
    violations2 = monitor.check_all(state)
    auth_v2 = [v for v in violations2 if v.invariant_name == "authority_trust"]
    check(len(auth_v2) > 0, "s13: low-trust authority detected")


def test_revocation_completeness():
    """§6.6: Revocation cascade completeness."""
    print("\n§6.6 Revocation Completeness")

    monitor = build_full_monitor()
    state = create_valid_state(4)

    # Setup parent-child relationship
    state.revocation_children["entity_0"] = {"entity_1", "entity_2"}

    # s14: Complete cascade passes
    state.entities["entity_0"].is_revoked = True
    state.entities["entity_1"].is_revoked = True
    state.entities["entity_2"].is_revoked = True
    violations = monitor.check_all(state)
    rev_v = [v for v in violations if v.invariant_name == "revocation_completeness"]
    check(len(rev_v) == 0, "s14: complete cascade passes")

    # s15: Incomplete cascade detected
    state.entities["entity_2"].is_revoked = False  # Child not revoked
    violations2 = monitor.check_all(state)
    rev_v2 = [v for v in violations2 if v.invariant_name == "revocation_completeness"]
    check(len(rev_v2) > 0, "s15: incomplete revocation cascade detected")


def test_federation_partition():
    """§6.7: Federation partition safety."""
    print("\n§6.7 Federation Partition Safety")

    monitor = build_full_monitor()
    state = create_valid_state(4)
    state.federations = {
        "fed_a": {"entity_0", "entity_1"},
        "fed_b": {"entity_2", "entity_3"},
    }

    # s16: Disjoint partitions pass
    violations = monitor.check_all(state)
    fed_v = [v for v in violations if v.invariant_name == "federation_partition"]
    check(len(fed_v) == 0, "s16: disjoint partitions pass")

    # s17: Overlap detected
    state.federations["fed_b"].add("entity_1")  # entity_1 in both feds
    violations2 = monitor.check_all(state)
    fed_v2 = [v for v in violations2 if v.invariant_name == "federation_partition"]
    check(len(fed_v2) > 0, "s17: entity in multiple federations detected")
    check(fed_v2[0].severity == InvariantSeverity.CRITICAL, "s17b: partition violation is CRITICAL")


def test_delegation_depth():
    """§6.8: Delegation depth bounds."""
    print("\n§6.8 Delegation Depth")

    monitor = build_full_monitor()
    state = create_valid_state(3)

    # s18: Shallow delegation passes
    state.entities["entity_0"].delegation_depth = 2
    violations = monitor.check_all(state)
    del_v = [v for v in violations if v.invariant_name == "delegation_depth"]
    check(len(del_v) == 0, "s18: shallow delegation passes")

    # s19: Deep delegation detected
    state.entities["entity_0"].delegation_depth = 10
    violations2 = monitor.check_all(state)
    del_v2 = [v for v in violations2 if v.invariant_name == "delegation_depth"]
    check(len(del_v2) > 0, "s19: deep delegation detected")


def test_temporal_monotonicity():
    """§6.9: Temporal monotonicity."""
    print("\n§6.9 Temporal Monotonicity")

    monitor = build_full_monitor()
    state = create_valid_state(3)

    # s20: Monotone timestamps pass
    violations = monitor.check_all(state)
    temp_v = [v for v in violations if v.invariant_name == "temporal_monotonicity"]
    check(len(temp_v) == 0, "s20: monotone timestamps pass")

    # s21: Non-monotone timestamps detected
    state.attestations.append(AttestationRecord(
        attestor_id="entity_0", target_id="entity_2",
        dimension="composite", value=0.6, timestamp=0  # Time went backward!
    ))
    violations2 = monitor.check_all(state)
    temp_v2 = [v for v in violations2 if v.invariant_name == "temporal_monotonicity"]
    check(len(temp_v2) > 0, "s21: non-monotone timestamp detected")


def test_attestation_integrity():
    """§6.10: Attestation integrity."""
    print("\n§6.10 Attestation Integrity")

    monitor = build_full_monitor()
    state = create_valid_state(3)

    # s22: Valid attestations pass
    violations = monitor.check_all(state)
    att_v = [v for v in violations if v.invariant_name == "attestation_integrity"]
    check(len(att_v) == 0, "s22: valid attestations pass")

    # s23: Attestation from unknown entity detected
    state.attestations.append(AttestationRecord(
        attestor_id="ghost", target_id="entity_0",
        dimension="composite", value=0.5
    ))
    violations2 = monitor.check_all(state)
    att_v2 = [v for v in violations2 if v.invariant_name == "attestation_integrity"]
    check(len(att_v2) > 0, "s23: attestation from ghost entity detected")


def test_multi_violation():
    """§6.11: Multiple simultaneous violations."""
    print("\n§6.11 Multiple Violations")

    monitor = build_full_monitor()
    state = create_valid_state(5)

    # Inject multiple violations
    state.entities["entity_0"].atp_balance += 500  # ATP violation
    state.entities["entity_1"].trust_scores["composite"] = 2.0  # Trust violation
    state.entities["entity_2"].lct_id = state.entities["entity_3"].lct_id  # LCT violation

    violations = monitor.check_all(state)

    # s24: Multiple violations detected simultaneously
    check(len(violations) >= 3, f"s24: multiple violations detected ({len(violations)})")

    # s25: Different invariant types
    types = set(v.invariant_name for v in violations)
    check(len(types) >= 3, f"s25: {len(types)} different invariant types")

    # s26: Violations by layer
    by_layer = monitor.violations_by_layer()
    check(len(by_layer) >= 2, f"s26: violations span {len(by_layer)} layers")

    # s27: Critical violations tracked separately
    critical = monitor.critical_violations()
    check(len(critical) >= 1, f"s27: {len(critical)} critical violations")


def test_continuous_monitoring():
    """§6.12: Continuous monitoring through state transitions."""
    print("\n§6.12 Continuous Monitoring")

    monitor = build_full_monitor()
    state = create_valid_state(5)

    # s28: Initial state clean
    v1 = monitor.check_all(state)
    check(len(v1) == 0, "s28: initial state clean")

    # s29: Perform valid transfer — still clean
    state.entities["entity_0"].atp_balance -= 10
    state.entities["entity_1"].atp_balance += 10
    v2 = monitor.check_all(state)
    atp_v2 = [v for v in v2 if v.invariant_name == "atp_conservation"]
    check(len(atp_v2) == 0, "s29: valid transfer — still clean")

    # s30: Inject bug — ATP not conserved
    state.entities["entity_2"].atp_balance += 1  # Bug: create 1 ATP
    v3 = monitor.check_all(state)
    atp_v3 = [v for v in v3 if v.invariant_name == "atp_conservation"]
    check(len(atp_v3) > 0, "s30: ATP bug detected on third check")

    # s31: Fix bug and verify clean again
    state.entities["entity_2"].atp_balance -= 1
    v4 = monitor.check_all(state)
    atp_v4 = [v for v in v4 if v.invariant_name == "atp_conservation"]
    check(len(atp_v4) == 0, "s31: bug fixed — state clean again")

    # s32: History preserved
    check(monitor.check_count == 4, f"s32: 4 checks performed ({monitor.check_count})")
    check(monitor.violation_count() > 0, "s32b: violation history preserved")


def test_invariant_interactions():
    """§6.13: Cross-layer invariant interactions."""
    print("\n§6.13 Cross-Layer Interactions")

    monitor = build_full_monitor()
    state = create_valid_state(5)

    # Scenario: authority with low trust who delegates deeply
    state.entities["entity_0"].is_authority = True
    state.entities["entity_0"].trust_scores["composite"] = 0.3  # Below threshold
    state.entities["entity_0"].delegation_depth = 8  # Above max

    # s33: Both violations detected
    violations = monitor.check_all(state)
    auth_v = [v for v in violations if v.invariant_name == "authority_trust"]
    del_v = [v for v in violations if v.invariant_name == "delegation_depth"]
    check(len(auth_v) > 0, "s33a: authority-trust violation detected")
    check(len(del_v) > 0, "s33b: delegation-depth violation detected")

    # s34: Cross-layer: revoked entity still has federation membership
    state2 = create_valid_state(4)
    state2.entities["entity_0"].is_revoked = True
    state2.revocation_children["entity_0"] = {"entity_1"}
    # entity_1 is not revoked but should be
    violations2 = monitor.check_all(state2)
    rev_v = [v for v in violations2 if v.invariant_name == "revocation_completeness"]
    check(len(rev_v) > 0, "s34: cross-layer revocation incomplete")


# ============================================================
# §7 — Run All Tests
# ============================================================

def main():
    print("=" * 70)
    print("Formal Invariant Monitor — Cross-Layer Verification")
    print("Session 28, Track 7")
    print("=" * 70)

    test_valid_state()
    test_atp_conservation()
    test_trust_bounds()
    test_lct_uniqueness()
    test_authority_trust()
    test_revocation_completeness()
    test_federation_partition()
    test_delegation_depth()
    test_temporal_monotonicity()
    test_attestation_integrity()
    test_multi_violation()
    test_continuous_monitoring()
    test_invariant_interactions()

    print(f"\n{'=' * 70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    if errors:
        print(f"\nFailures:")
        for e in errors:
            print(f"  - {e}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
