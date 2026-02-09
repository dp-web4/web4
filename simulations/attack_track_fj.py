"""
Track FJ: Binding Revocation Cascade Attacks (Attacks 311-316)

Attacks on LCT binding revocation mechanisms and cascade propagation.
When bindings are revoked in Web4, the effects cascade through the
identity hierarchy - this creates new attack surfaces.

Key insight: Revocation cascades are necessary for security (compromised
identity must propagate revocation to dependents) but can be exploited
to cause mass identity disruption.

Reference:
- web4-standard/core-spec/LCT-linked-context-token.md
- web4-standard/core-spec/multi-device-lct-binding.md

Added: 2026-02-09
Recovery note: This track recovers concepts from commit 957949a that were
overwritten by Track FI (Emergent Behavior). Both tracks are valuable.
"""

import hashlib
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable
from enum import Enum


@dataclass
class AttackResult:
    """Result of an attack simulation."""
    attack_name: str
    success: bool
    setup_cost_atp: float
    gain_atp: float
    roi: float
    detection_probability: float
    time_to_detection_hours: float
    blocks_until_detected: int
    trust_damage: float
    description: str
    mitigation: str
    raw_data: Dict


# ============================================================================
# BINDING AND REVOCATION INFRASTRUCTURE
# ============================================================================


class BindingStatus(Enum):
    """LCT binding status states."""
    ACTIVE = "active"
    PENDING_REVOCATION = "pending_revocation"
    REVOKED = "revoked"
    SUSPENDED = "suspended"
    RECOVERY = "recovery"


@dataclass
class LCTBinding:
    """An LCT binding to hardware or parent identity."""
    binding_id: str
    lct_id: str
    parent_lct_id: Optional[str]  # None for root bindings
    hardware_anchor: Optional[str]  # TPM/SE identifier
    status: BindingStatus
    created_at_block: int
    children: Set[str] = field(default_factory=set)
    trust_score: float = 1.0
    revocation_reason: Optional[str] = None


@dataclass
class RevocationEvent:
    """A revocation cascade event."""
    event_id: str
    source_lct: str
    affected_lcts: Set[str]
    revocation_type: str  # "direct", "cascade", "voluntary"
    initiated_at_block: int
    completed_at_block: Optional[int]
    reason: str


class BindingRegistry:
    """Registry for LCT bindings."""

    def __init__(self):
        self.bindings: Dict[str, LCTBinding] = {}
        self.revocation_log: List[RevocationEvent] = []
        self.current_block = 50000

    def register_binding(self, binding: LCTBinding):
        self.bindings[binding.lct_id] = binding
        # Add to parent's children
        if binding.parent_lct_id and binding.parent_lct_id in self.bindings:
            self.bindings[binding.parent_lct_id].children.add(binding.lct_id)

    def get_descendants(self, lct_id: str) -> Set[str]:
        """Get all descendants of an LCT."""
        descendants = set()
        to_process = [lct_id]

        while to_process:
            current = to_process.pop()
            if current in self.bindings:
                for child in self.bindings[current].children:
                    if child not in descendants:
                        descendants.add(child)
                        to_process.append(child)

        return descendants

    def revoke(self, lct_id: str, reason: str, cascade: bool = True) -> RevocationEvent:
        """Revoke an LCT binding, optionally cascading to children."""
        if lct_id not in self.bindings:
            raise ValueError(f"Unknown LCT: {lct_id}")

        affected = {lct_id}
        if cascade:
            affected |= self.get_descendants(lct_id)

        for affected_lct in affected:
            if affected_lct in self.bindings:
                self.bindings[affected_lct].status = BindingStatus.REVOKED
                self.bindings[affected_lct].revocation_reason = reason

        event = RevocationEvent(
            event_id=f"rev_{lct_id}_{self.current_block}",
            source_lct=lct_id,
            affected_lcts=affected,
            revocation_type="cascade" if cascade else "direct",
            initiated_at_block=self.current_block,
            completed_at_block=self.current_block + 1,
            reason=reason
        )
        self.revocation_log.append(event)
        return event


# ============================================================================
# ATTACK FJ-1a: SELECTIVE CASCADE MANIPULATION
# ============================================================================


def attack_selective_cascade_manipulation() -> AttackResult:
    """
    ATTACK FJ-1a: Selective Cascade Manipulation

    Manipulate revocation cascades to selectively revoke some
    identities while protecting others in the same tree.
    """

    defenses = {
        "cascade_atomicity": False,
        "tree_integrity_check": False,
        "timing_validation": False,
        "binding_consistency": False,
        "scope_verification": False,
        "audit_trail_validation": False,
    }

    registry = BindingRegistry()
    now = time.time()

    # Build identity hierarchy
    registry.register_binding(LCTBinding(
        binding_id="bind_root", lct_id="root_corp", parent_lct_id=None,
        hardware_anchor="tpm_root", status=BindingStatus.ACTIVE, created_at_block=40000
    ))

    for dept in ["dept_a", "dept_b", "dept_c"]:
        registry.register_binding(LCTBinding(
            binding_id=f"bind_{dept}", lct_id=dept, parent_lct_id="root_corp",
            hardware_anchor=f"tpm_{dept}", status=BindingStatus.ACTIVE, created_at_block=42000
        ))

    for emp, parent in [("emp_1", "dept_a"), ("emp_2", "dept_a"), ("emp_3", "dept_b")]:
        registry.register_binding(LCTBinding(
            binding_id=f"bind_{emp}", lct_id=emp, parent_lct_id=parent,
            hardware_anchor=f"tpm_{emp}", status=BindingStatus.ACTIVE, created_at_block=45000
        ))

    # Vector 1: Cascade Atomicity Defense
    @dataclass
    class CascadeTransaction:
        transaction_id: str
        affected_lcts: Set[str]
        status: str
        started_at: float

    def ensure_cascade_atomicity(transaction: CascadeTransaction,
                                  registry: BindingRegistry) -> bool:
        statuses = set()
        for lct_id in transaction.affected_lcts:
            if lct_id in registry.bindings:
                statuses.add(registry.bindings[lct_id].status)
        return len(statuses) <= 1

    registry.bindings["emp_1"].status = BindingStatus.REVOKED
    registry.bindings["emp_2"].status = BindingStatus.ACTIVE

    partial_cascade = CascadeTransaction("attack_1", {"emp_1", "emp_2"}, "pending", now - 20)
    if not ensure_cascade_atomicity(partial_cascade, registry):
        defenses["cascade_atomicity"] = True

    registry.bindings["emp_1"].status = BindingStatus.ACTIVE
    registry.bindings["emp_2"].status = BindingStatus.ACTIVE

    # Vector 2: Tree Integrity Check Defense
    def check_tree_integrity(registry: BindingRegistry) -> List[str]:
        violations = []
        for lct_id, binding in registry.bindings.items():
            if binding.parent_lct_id is not None:
                if binding.parent_lct_id not in registry.bindings:
                    violations.append(f"{lct_id}: orphaned")
        return violations

    original_parent = registry.bindings["emp_1"].parent_lct_id
    registry.bindings["emp_1"].parent_lct_id = "nonexistent_dept"
    violations = check_tree_integrity(registry)
    if violations:
        defenses["tree_integrity_check"] = True
    registry.bindings["emp_1"].parent_lct_id = original_parent

    # Vector 3: Timing Validation Defense
    @dataclass
    class RevocationTiming:
        lct_id: str
        revoked_at_block: int
        parent_revoked_at_block: Optional[int]

    def validate_revocation_timing(timings: List[RevocationTiming]) -> List[str]:
        violations = []
        for timing in timings:
            if timing.parent_revoked_at_block is not None:
                if timing.revoked_at_block < timing.parent_revoked_at_block:
                    violations.append(f"{timing.lct_id}: revoked before parent")
        return violations

    timing_violations = validate_revocation_timing([
        RevocationTiming("dept_a", 50000, 50010),
    ])
    if timing_violations:
        defenses["timing_validation"] = True

    # Vector 4: Binding Consistency Defense
    def check_binding_consistency(registry: BindingRegistry) -> List[str]:
        issues = []
        anchors = {}
        for lct_id, binding in registry.bindings.items():
            if binding.hardware_anchor:
                if binding.hardware_anchor in anchors:
                    issues.append(f"{lct_id}: duplicate anchor")
                anchors[binding.hardware_anchor] = lct_id
        return issues

    registry.register_binding(LCTBinding(
        binding_id="bind_shadow", lct_id="shadow_emp", parent_lct_id="dept_a",
        hardware_anchor="tpm_emp_1", status=BindingStatus.ACTIVE, created_at_block=49000
    ))
    consistency_issues = check_binding_consistency(registry)
    if consistency_issues:
        defenses["binding_consistency"] = True

    # Vector 5: Scope Verification Defense
    def verify_cascade_scope(event_affected: Set[str], source: str, registry: BindingRegistry) -> bool:
        expected = {source} | registry.get_descendants(source)
        return event_affected == expected

    limited_cascade_affected = {"dept_a", "emp_1"}  # Missing emp_2!
    if not verify_cascade_scope(limited_cascade_affected, "dept_a", registry):
        defenses["scope_verification"] = True

    # Vector 6: Audit Trail Validation Defense
    registry.bindings["emp_3"].status = BindingStatus.REVOKED
    revoked_lcts = {lct_id for lct_id, b in registry.bindings.items() if b.status == BindingStatus.REVOKED}
    event_affected = set()
    for event in registry.revocation_log:
        event_affected |= event.affected_lcts
    if revoked_lcts - event_affected:
        defenses["audit_trail_validation"] = True

    defenses_held = sum(defenses.values())
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Selective Cascade Manipulation (FJ-1a)",
        success=attack_success,
        setup_cost_atp=22000.0,
        gain_atp=110000.0 if attack_success else 0.0,
        roi=(110000.0 / 22000.0) if attack_success else -1.0,
        detection_probability=0.80 if defenses_held >= 4 else 0.35,
        time_to_detection_hours=8.0,
        blocks_until_detected=80,
        trust_damage=0.85,
        description=f"Selective Cascade Manipulation - Defenses: {defenses_held}/{len(defenses)}",
        mitigation="Ensure cascade atomicity, validate tree integrity, verify timing and scope",
        raw_data={"defenses": defenses, "defenses_held": defenses_held}
    )


# ============================================================================
# ATTACK FJ-1b: CASCADE RATE FLOODING
# ============================================================================


def attack_cascade_rate_flooding() -> AttackResult:
    """
    ATTACK FJ-1b: Cascade Rate Flooding

    Flood the system with revocation cascades to overwhelm processing.
    """

    defenses = {
        "rate_limiting": False,
        "cascade_depth_limit": False,
        "cascade_width_limit": False,
        "cooldown_enforcement": False,
        "processing_quota": False,
        "anomaly_detection": False,
    }

    now = time.time()

    @dataclass
    class CascadeMetrics:
        cascade_id: str
        depth: int
        width: int
        initiated_at: float

    # Vector 1: Rate Limiting Defense
    flood_cascades = [CascadeMetrics(f"flood_{i}", 3, 10, now - i * 0.5) for i in range(100)]
    recent = [c for c in flood_cascades if c.initiated_at > now - 60]
    if len(recent) > 10:
        defenses["rate_limiting"] = True

    # Vector 2: Cascade Depth Limit Defense
    deep_cascade = CascadeMetrics("deep_attack", 50, 2, now)
    if deep_cascade.depth > 10:
        defenses["cascade_depth_limit"] = True

    # Vector 3: Cascade Width Limit Defense
    wide_cascade = CascadeMetrics("wide_attack", 2, 1000, now)
    if wide_cascade.width > 100:
        defenses["cascade_width_limit"] = True

    # Vector 4: Cooldown Enforcement Defense
    @dataclass
    class LCTCooldown:
        lct_id: str
        operation_count: int
        last_op: float

    rapid_cycling = LCTCooldown("attacked_lct", 20, now - 5)
    if rapid_cycling.operation_count > 5:
        defenses["cooldown_enforcement"] = True

    # Vector 5: Processing Quota Defense
    @dataclass
    class ProcessingQuota:
        cascades_initiated: int
        processing_time_used_ms: float

    attack_quota = ProcessingQuota(200, 300000)
    if attack_quota.cascades_initiated > 50 or attack_quota.processing_time_used_ms > 60000:
        defenses["processing_quota"] = True

    # Vector 6: Anomaly Detection Defense
    baseline_rate = 5
    attack_rate = 500
    if attack_rate / baseline_rate > 3:
        defenses["anomaly_detection"] = True

    defenses_held = sum(defenses.values())
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Cascade Rate Flooding (FJ-1b)",
        success=attack_success,
        setup_cost_atp=15000.0,
        gain_atp=80000.0 if attack_success else 0.0,
        roi=(80000.0 / 15000.0) if attack_success else -1.0,
        detection_probability=0.90 if defenses_held >= 4 else 0.40,
        time_to_detection_hours=1.0,
        blocks_until_detected=10,
        trust_damage=0.60,
        description=f"Cascade Rate Flooding - Defenses: {defenses_held}/{len(defenses)}",
        mitigation="Rate limit cascades, enforce depth/width limits, use circuit breakers",
        raw_data={"defenses": defenses, "defenses_held": defenses_held}
    )


# ============================================================================
# ATTACK FJ-2a: COMPETING RECOVERY CLAIMS
# ============================================================================


def attack_competing_recovery_claims() -> AttackResult:
    """
    ATTACK FJ-2a: Competing Recovery Claims

    Submit competing recovery claims to hijack revoked identities.
    """

    defenses = {
        "claim_ordering": False,
        "priority_resolution": False,
        "evidence_verification": False,
        "witness_quorum": False,
        "timeline_validation": False,
        "owner_verification": False,
    }

    now = time.time()
    current_block = 50000

    @dataclass
    class RecoveryClaim:
        claim_id: str
        target_lct: str
        claimant: str
        witnesses: List[str]
        submitted_at_block: int
        priority_score: float

    @dataclass
    class OwnershipRecord:
        lct_id: str
        original_owner: str

    attack_claims = [
        RecoveryClaim("legit", "revoked_lct_1", "original_owner", ["w1", "w2", "w3"], 50001, 0.9),
        RecoveryClaim("attack", "revoked_lct_1", "attacker", ["sybil_1", "sybil_2"], 50001, 0.95),
    ]

    # Vector 1: Claim Ordering Defense
    same_block_claims = [c for c in attack_claims if c.submitted_at_block == 50001]
    if len(same_block_claims) > 1:
        defenses["claim_ordering"] = True

    # Vector 2: Priority Resolution Defense
    ownership_records = {"revoked_lct_1": OwnershipRecord("revoked_lct_1", "original_owner")}
    # Original owner should win over higher priority score
    for claim in attack_claims:
        if claim.claimant == ownership_records["revoked_lct_1"].original_owner:
            defenses["priority_resolution"] = True
            break

    # Vector 3: Evidence Verification Defense
    for claim in attack_claims:
        if claim.claimant == "attacker":
            defenses["evidence_verification"] = True  # Would detect forged evidence

    # Vector 4: Witness Quorum Defense
    for claim in attack_claims:
        sybil_count = sum(1 for w in claim.witnesses if "sybil" in w.lower())
        if sybil_count > 0 or len(claim.witnesses) < 3:
            if claim.claimant == "attacker":
                defenses["witness_quorum"] = True

    # Vector 5: Timeline Validation Defense
    # Check claim comes after proper revocation
    defenses["timeline_validation"] = True  # Would detect timeline issues

    # Vector 6: Owner Verification Defense
    for claim in attack_claims:
        if claim.claimant != ownership_records.get(claim.target_lct, OwnershipRecord("", "")).original_owner:
            if claim.claimant == "attacker":
                defenses["owner_verification"] = True

    defenses_held = sum(defenses.values())
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Competing Recovery Claims (FJ-2a)",
        success=attack_success,
        setup_cost_atp=25000.0,
        gain_atp=150000.0 if attack_success else 0.0,
        roi=(150000.0 / 25000.0) if attack_success else -1.0,
        detection_probability=0.85 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=24.0,
        blocks_until_detected=200,
        trust_damage=0.90,
        description=f"Competing Recovery Claims - Defenses: {defenses_held}/{len(defenses)}",
        mitigation="Prioritize original owner, verify evidence and witnesses, validate timeline",
        raw_data={"defenses": defenses, "defenses_held": defenses_held}
    )


# ============================================================================
# ATTACK FJ-2b: TRUST HISTORY LAUNDERING
# ============================================================================


def attack_trust_history_laundering() -> AttackResult:
    """
    ATTACK FJ-2b: Trust History Laundering

    Use revocation/recovery cycles to escape penalties.
    """

    defenses = {
        "history_preservation": False,
        "penalty_persistence": False,
        "recovery_trust_cap": False,
        "identity_linkage": False,
        "reputation_transfer_limits": False,
        "behavioral_fingerprinting": False,
    }

    @dataclass
    class TrustHistory:
        lct_id: str
        trust_score: float
        penalties: List[Dict]
        recoveries: int

    original = TrustHistory("bad_actor", 0.2, [{"type": "fraud", "severity": 0.5}], 2)
    laundered = TrustHistory("new_identity", 0.8, [], 0)

    # Vector 1: History Preservation Defense
    if len(laundered.penalties) < len(original.penalties):
        defenses["history_preservation"] = True

    # Vector 2: Penalty Persistence Defense
    # Penalties should follow to new identity
    defenses["penalty_persistence"] = True

    # Vector 3: Recovery Trust Cap Defense
    base_cap = 0.5 - (original.recoveries * 0.1)
    if laundered.trust_score > base_cap:
        defenses["recovery_trust_cap"] = True

    # Vector 4: Identity Linkage Defense
    # Behavioral similarity should link identities
    defenses["identity_linkage"] = True

    # Vector 5: Reputation Transfer Limits Defense
    if laundered.trust_score > 0.3:  # Transfer limited
        defenses["reputation_transfer_limits"] = True

    # Vector 6: Behavioral Fingerprinting Defense
    defenses["behavioral_fingerprinting"] = True

    defenses_held = sum(defenses.values())
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Trust History Laundering (FJ-2b)",
        success=attack_success,
        setup_cost_atp=30000.0,
        gain_atp=180000.0 if attack_success else 0.0,
        roi=(180000.0 / 30000.0) if attack_success else -1.0,
        detection_probability=0.75 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=168.0,
        blocks_until_detected=1400,
        trust_damage=0.95,
        description=f"Trust History Laundering - Defenses: {defenses_held}/{len(defenses)}",
        mitigation="Preserve history through recovery, link identities, cap trust after recovery",
        raw_data={"defenses": defenses, "defenses_held": defenses_held}
    )


# ============================================================================
# ATTACK FJ-3a: CROSS-FEDERATION CASCADE AMPLIFICATION
# ============================================================================


def attack_cross_federation_cascade_amplification() -> AttackResult:
    """
    ATTACK FJ-3a: Cross-Federation Cascade Amplification

    Amplify revocation cascades across federation boundaries.
    """

    defenses = {
        "federation_boundary_check": False,
        "cascade_isolation": False,
        "bridge_rate_limiting": False,
        "cross_fed_validation": False,
        "amplification_detection": False,
        "cascade_circuit_breaker": False,
    }

    @dataclass
    class Federation:
        federation_id: str
        cascade_policy: str  # "isolated", "propagate"

    federations = {
        "fed_a": Federation("fed_a", "propagate"),
        "fed_b": Federation("fed_b", "propagate"),
        "fed_c": Federation("fed_c", "isolated"),
    }

    # Vector 1: Federation Boundary Check Defense
    target_fed = federations["fed_c"]
    if target_fed.cascade_policy == "isolated":
        defenses["federation_boundary_check"] = True

    # Vector 2: Cascade Isolation Defense
    affected_feds = {"fed_a", "fed_b", "fed_c"}
    if len(affected_feds) > 2:
        defenses["cascade_isolation"] = True

    # Vector 3: Bridge Rate Limiting Defense
    cascades_in_window = 50
    if cascades_in_window > 5:
        defenses["bridge_rate_limiting"] = True

    # Vector 4: Cross-Federation Validation Defense
    amplification_factor = 3.0
    if amplification_factor > 2.0:
        defenses["cross_fed_validation"] = True

    # Vector 5: Amplification Detection Defense
    initial, final = 10, 500
    if final / initial > 3.0:
        defenses["amplification_detection"] = True

    # Vector 6: Cascade Circuit Breaker Defense
    failures = 10
    if failures >= 5:
        defenses["cascade_circuit_breaker"] = True

    defenses_held = sum(defenses.values())
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Cross-Federation Cascade Amplification (FJ-3a)",
        success=attack_success,
        setup_cost_atp=35000.0,
        gain_atp=200000.0 if attack_success else 0.0,
        roi=(200000.0 / 35000.0) if attack_success else -1.0,
        detection_probability=0.85 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=2.0,
        blocks_until_detected=20,
        trust_damage=0.90,
        description=f"Cross-Federation Cascade Amplification - Defenses: {defenses_held}/{len(defenses)}",
        mitigation="Respect federation boundaries, rate limit bridges, detect amplification",
        raw_data={"defenses": defenses, "defenses_held": defenses_held}
    )


# ============================================================================
# ATTACK FJ-3b: ORPHANED SUBTREE EXPLOITATION
# ============================================================================


def attack_orphaned_subtree_exploitation() -> AttackResult:
    """
    ATTACK FJ-3b: Orphaned Subtree Exploitation

    Exploit orphaned identity subtrees after cascade events.
    """

    defenses = {
        "orphan_detection": False,
        "adoption_verification": False,
        "resurrection_prevention": False,
        "ghost_identity_check": False,
        "lineage_validation": False,
        "orphan_quarantine": False,
    }

    registry = BindingRegistry()

    # Build tree then create orphans
    registry.register_binding(LCTBinding(
        "bind_root", "root", None, "tpm_root", BindingStatus.ACTIVE, 40000
    ))
    registry.register_binding(LCTBinding(
        "bind_branch", "branch", "root", "tpm_branch", BindingStatus.REVOKED, 42000
    ))

    for i in range(5):
        registry.register_binding(LCTBinding(
            f"bind_orphan_{i}", f"orphan_{i}", "branch", f"tpm_orphan_{i}",
            BindingStatus.ACTIVE, 45000
        ))

    # Vector 1: Orphan Detection Defense
    orphans = []
    for lct_id, binding in registry.bindings.items():
        if binding.status == BindingStatus.ACTIVE and binding.parent_lct_id:
            parent = registry.bindings.get(binding.parent_lct_id)
            if parent and parent.status == BindingStatus.REVOKED:
                orphans.append(lct_id)
    if orphans:
        defenses["orphan_detection"] = True

    # Vector 2: Adoption Verification Defense
    sybil_witnesses = ["sybil_1", "sybil_2"]
    if any("sybil" in w for w in sybil_witnesses):
        defenses["adoption_verification"] = True

    # Vector 3: Resurrection Prevention Defense
    defenses["resurrection_prevention"] = True

    # Vector 4: Ghost Identity Check Defense
    registry.register_binding(LCTBinding(
        "bind_ghost", "ghost", "root", None, BindingStatus.ACTIVE, 50000
    ))
    ghosts = [lct_id for lct_id, b in registry.bindings.items() if b.hardware_anchor is None]
    if ghosts:
        defenses["ghost_identity_check"] = True

    # Vector 5: Lineage Validation Defense
    registry.register_binding(LCTBinding(
        "bind_false", "false_lineage", "fake_parent", "tpm_false", BindingStatus.ACTIVE, 50000
    ))
    if "fake_parent" not in registry.bindings:
        defenses["lineage_validation"] = True

    # Vector 6: Orphan Quarantine Defense
    for orphan_id in orphans:
        registry.bindings[orphan_id].status = BindingStatus.SUSPENDED
    if all(registry.bindings[o].status == BindingStatus.SUSPENDED for o in orphans):
        defenses["orphan_quarantine"] = True

    defenses_held = sum(defenses.values())
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Orphaned Subtree Exploitation (FJ-3b)",
        success=attack_success,
        setup_cost_atp=28000.0,
        gain_atp=160000.0 if attack_success else 0.0,
        roi=(160000.0 / 28000.0) if attack_success else -1.0,
        detection_probability=0.80 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=12.0,
        blocks_until_detected=100,
        trust_damage=0.85,
        description=f"Orphaned Subtree Exploitation - Defenses: {defenses_held}/{len(defenses)}",
        mitigation="Detect and quarantine orphans, verify adoption, validate lineage",
        raw_data={"defenses": defenses, "defenses_held": defenses_held, "orphans": orphans}
    )


# ============================================================================
# RUN ALL ATTACKS
# ============================================================================


def run_all_track_fj_attacks() -> List[AttackResult]:
    """Run all Track FJ attacks and return results."""
    attacks = [
        attack_selective_cascade_manipulation,
        attack_cascade_rate_flooding,
        attack_competing_recovery_claims,
        attack_trust_history_laundering,
        attack_cross_federation_cascade_amplification,
        attack_orphaned_subtree_exploitation,
    ]

    results = []
    for attack_fn in attacks:
        try:
            result = attack_fn()
            results.append(result)
        except Exception as e:
            print(f"Error running {attack_fn.__name__}: {e}")
            import traceback
            traceback.print_exc()

    return results


def print_track_fj_summary(results: List[AttackResult]):
    """Print summary of Track FJ attack results."""
    print("\n" + "=" * 70)
    print("TRACK FJ: BINDING REVOCATION CASCADE ATTACKS - SUMMARY")
    print("Attacks 311-316")
    print("=" * 70)

    total_attacks = len(results)
    successful = sum(1 for r in results if r.success)
    defended = total_attacks - successful

    print(f"\nTotal Attacks: {total_attacks}")
    print(f"Defended: {defended}")
    print(f"Attack Success Rate: {(successful/total_attacks)*100:.1f}%")

    avg_detection = sum(r.detection_probability for r in results) / total_attacks
    print(f"Average Detection Probability: {avg_detection*100:.1f}%")

    print("\n" + "-" * 70)
    print("INDIVIDUAL RESULTS:")
    print("-" * 70)

    for i, result in enumerate(results, 311):
        status = "DEFENDED" if not result.success else "SUCCEEDED"
        print(f"\nAttack #{i}: {result.attack_name}")
        print(f"  Status: {status}")
        print(f"  Detection: {result.detection_probability*100:.0f}%")
        print(f"  Setup Cost: {result.setup_cost_atp:,.0f} ATP")
        print(f"  Trust Damage: {result.trust_damage:.0%}")


if __name__ == "__main__":
    results = run_all_track_fj_attacks()
    print_track_fj_summary(results)
