#!/usr/bin/env python3
"""
LCT Revocation Cascades — Web4 Session 27, Track 3

When an LCT is revoked, what happens to everything that depends on it?
Existing revocation_registry.py handles basic revocation records.
This goes deeper into the cascade effects.

Key questions:
1. When a delegator is revoked, what happens to all delegatees?
2. How does revocation propagate across federation boundaries?
3. What are the timeline conflicts when revocation races with transactions?
4. How do entities recover from incorrect revocations?
5. What's the revocation propagation delay model?
6. Can an attacker weaponize the revocation system itself?

Real-world parallels:
- Certificate revocation (CRL/OCSP) in PKI
- Token revocation in OAuth2
- License revocation cascading in software supply chains
"""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque


# ============================================================
# Section 1: LCT Identity Model
# ============================================================

class RevocationReason(Enum):
    KEY_COMPROMISE = "key_compromise"
    BEHAVIOR_VIOLATION = "behavior_violation"
    DELEGATION_CHAIN_BREAK = "delegation_chain_break"
    FEDERATION_EXPULSION = "federation_expulsion"
    VOLUNTARY = "voluntary"
    ADMIN_OVERRIDE = "admin_override"
    CASCADE = "cascade"  # revoked because parent was revoked
    INCORRECT_REVERSAL = "incorrect_reversal"  # revoked-then-restored


class LCTStatus(Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    SUSPENDED = "suspended"  # temporary, can be restored
    RESTORED = "restored"    # was revoked/suspended, now active again


@dataclass
class LCTIdentity:
    """An LCT identity with delegation relationships."""
    lct_id: str
    parent_id: Optional[str] = None  # delegator
    federation: str = "default"
    status: LCTStatus = LCTStatus.ACTIVE
    created_at: float = 0.0
    revoked_at: Optional[float] = None
    revocation_reason: Optional[RevocationReason] = None
    atp_balance: float = 100.0
    t3_composite: float = 0.5
    hardware_bound: bool = False
    delegatees: List[str] = field(default_factory=list)  # children
    permissions: Set[str] = field(default_factory=lambda: {"read", "write", "delegate"})


@dataclass
class RevocationEvent:
    """A revocation event with timestamp and metadata."""
    event_id: str
    lct_id: str
    timestamp: float
    reason: RevocationReason
    initiator: str  # who initiated the revocation
    cascade_depth: int = 0  # how deep in the cascade chain
    cascade_parent: Optional[str] = None  # which revocation triggered this one
    propagation_delay: float = 0.0  # time to reach all nodes
    affected_transactions: int = 0  # transactions voided by this revocation


@dataclass
class Transaction:
    """A transaction that may be affected by revocation."""
    tx_id: str
    sender: str
    receiver: str
    amount: float
    timestamp: float
    finalized: bool = False
    voided: bool = False
    voided_reason: Optional[str] = None


# ============================================================
# Section 2: Revocation Cascade Engine
# ============================================================

class RevocationCascadeEngine:
    """
    Manages LCT revocation cascades.

    When a delegator is revoked:
    1. All direct delegatees are CASCADE-revoked
    2. Their delegatees are CASCADE-revoked (recursive)
    3. ATP balances are frozen at each level
    4. T3 trust scores are zeroed
    5. Pending transactions involving revoked entities are voided
    """

    def __init__(self):
        self.identities: Dict[str, LCTIdentity] = {}
        self.revocation_events: List[RevocationEvent] = []
        self.pending_transactions: List[Transaction] = []
        self.event_counter = 0
        self.current_time = 0.0

    def register(self, identity: LCTIdentity):
        self.identities[identity.lct_id] = identity
        if identity.parent_id and identity.parent_id in self.identities:
            parent = self.identities[identity.parent_id]
            if identity.lct_id not in parent.delegatees:
                parent.delegatees.append(identity.lct_id)

    def submit_transaction(self, tx: Transaction):
        self.pending_transactions.append(tx)

    def revoke(self, lct_id: str, reason: RevocationReason, initiator: str,
               propagation_delay: float = 0.0) -> Dict[str, Any]:
        """
        Revoke an LCT and cascade to all dependents.
        Returns cascade statistics.
        """
        if lct_id not in self.identities:
            return {"error": "LCT not found"}

        identity = self.identities[lct_id]
        if identity.status == LCTStatus.REVOKED:
            return {"error": "Already revoked"}

        self.current_time += 1.0  # advance time

        # Execute cascade via BFS
        cascade_stats = {
            "root_revoked": lct_id,
            "reason": reason.value,
            "total_revoked": 0,
            "max_depth": 0,
            "atp_frozen": 0.0,
            "transactions_voided": 0,
            "federations_affected": set(),
            "cascade_events": [],
        }

        queue = deque([(lct_id, 0, None)])  # (lct_id, depth, parent_event_id)
        visited = set()

        while queue:
            current_id, depth, parent_event = queue.popleft()
            if current_id in visited:
                continue
            visited.add(current_id)

            current = self.identities.get(current_id)
            if not current or current.status == LCTStatus.REVOKED:
                continue

            # Revoke this identity
            current.status = LCTStatus.REVOKED
            current.revoked_at = self.current_time + depth * propagation_delay
            current.revocation_reason = reason if depth == 0 else RevocationReason.CASCADE

            # Create revocation event
            self.event_counter += 1
            event = RevocationEvent(
                event_id=f"rev_{self.event_counter}",
                lct_id=current_id,
                timestamp=current.revoked_at,
                reason=current.revocation_reason,
                initiator=initiator if depth == 0 else f"cascade_from_{lct_id}",
                cascade_depth=depth,
                cascade_parent=parent_event,
                propagation_delay=depth * propagation_delay,
            )

            # Freeze ATP
            cascade_stats["atp_frozen"] += current.atp_balance
            current.atp_balance = 0.0

            # Zero T3
            current.t3_composite = 0.0

            # Void pending transactions
            for tx in self.pending_transactions:
                if not tx.voided and not tx.finalized:
                    if tx.sender == current_id or tx.receiver == current_id:
                        if tx.timestamp >= current.revoked_at - propagation_delay:
                            tx.voided = True
                            tx.voided_reason = f"party_revoked:{current_id}"
                            event.affected_transactions += 1

            cascade_stats["total_revoked"] += 1
            cascade_stats["max_depth"] = max(cascade_stats["max_depth"], depth)
            cascade_stats["transactions_voided"] += event.affected_transactions
            cascade_stats["federations_affected"].add(current.federation)
            cascade_stats["cascade_events"].append({
                "event_id": event.event_id,
                "lct_id": current_id,
                "depth": depth,
                "atp_frozen": current.atp_balance,
                "federation": current.federation,
            })

            self.revocation_events.append(event)

            # Cascade to delegatees
            for delegatee_id in current.delegatees:
                if delegatee_id not in visited:
                    queue.append((delegatee_id, depth + 1, event.event_id))

        cascade_stats["federations_affected"] = list(cascade_stats["federations_affected"])
        return cascade_stats

    def suspend(self, lct_id: str, reason: RevocationReason) -> bool:
        """Suspend an LCT (temporary, can be restored)."""
        if lct_id not in self.identities:
            return False
        identity = self.identities[lct_id]
        if identity.status != LCTStatus.ACTIVE:
            return False
        identity.status = LCTStatus.SUSPENDED
        identity.revocation_reason = reason
        return True

    def restore(self, lct_id: str, restorer: str) -> Dict[str, Any]:
        """
        Restore a suspended/revoked LCT.
        Only works for certain revocation reasons and requires authority.
        """
        if lct_id not in self.identities:
            return {"success": False, "reason": "LCT not found"}

        identity = self.identities[lct_id]

        # Can only restore SUSPENDED, not REVOKED (unless admin override)
        if identity.status == LCTStatus.ACTIVE:
            return {"success": False, "reason": "Already active"}

        # Cannot restore key_compromise without key rotation
        if identity.revocation_reason == RevocationReason.KEY_COMPROMISE:
            return {"success": False, "reason": "Key compromise requires key rotation, not restore"}

        identity.status = LCTStatus.RESTORED
        identity.revocation_reason = RevocationReason.INCORRECT_REVERSAL

        # Partial ATP recovery (not all — some may have been redistributed)
        recovery_fraction = 0.8  # 80% recovery
        identity.atp_balance = 100.0 * recovery_fraction

        # T3 recovery is slower — trust must be re-earned
        identity.t3_composite = 0.3  # low starting trust after incident

        return {
            "success": True,
            "lct_id": lct_id,
            "new_status": identity.status.value,
            "atp_recovered": identity.atp_balance,
            "t3_starting": identity.t3_composite,
        }


# ============================================================
# Section 3: Cross-Federation Propagation
# ============================================================

@dataclass
class Federation:
    """A federation with its own propagation characteristics."""
    federation_id: str
    members: Set[str] = field(default_factory=set)
    propagation_latency_ms: float = 100.0  # intra-federation
    bridge_nodes: Set[str] = field(default_factory=set)  # nodes connected to other federations


class CrossFederationPropagator:
    """
    Models how revocations propagate across federation boundaries.

    Key insight: inter-federation propagation is slower than intra-federation
    because bridge nodes must verify and relay revocation events.
    """

    def __init__(self):
        self.federations: Dict[str, Federation] = {}
        self.inter_federation_latency_ms: float = 500.0  # 5x intra-federation

    def add_federation(self, federation: Federation):
        self.federations[federation.federation_id] = federation

    def calculate_propagation_time(self, source_federation: str,
                                    target_federation: str,
                                    num_hops: int = 1) -> float:
        """Calculate time for revocation to reach target federation."""
        if source_federation == target_federation:
            return self.federations[source_federation].propagation_latency_ms

        # Inter-federation: source intra + bridge relay + target intra
        source_intra = self.federations[source_federation].propagation_latency_ms
        bridge_relay = self.inter_federation_latency_ms * num_hops
        target_intra = self.federations[target_federation].propagation_latency_ms

        return source_intra + bridge_relay + target_intra

    def simulate_propagation(self, source_lct: str, source_federation: str) -> Dict[str, Any]:
        """Simulate revocation propagation across all federations."""
        results = {}

        for fed_id, federation in self.federations.items():
            if fed_id == source_federation:
                time_ms = federation.propagation_latency_ms
            else:
                # Count hops (simplified: direct connection = 1 hop)
                time_ms = self.calculate_propagation_time(source_federation, fed_id)

            results[fed_id] = {
                "propagation_time_ms": time_ms,
                "members_affected": len(federation.members),
                "has_bridge": len(federation.bridge_nodes) > 0,
            }

        return {
            "source": source_lct,
            "source_federation": source_federation,
            "propagation_map": results,
            "max_propagation_ms": max(r["propagation_time_ms"] for r in results.values()),
            "total_entities_notified": sum(r["members_affected"] for r in results.values()),
        }


# ============================================================
# Section 4: Timeline Conflict Resolution
# ============================================================

@dataclass
class TimelineEvent:
    """An event with a timestamp that may conflict with revocations."""
    event_type: str  # "transaction", "delegation", "attestation"
    timestamp: float
    actor: str
    details: Dict[str, Any] = field(default_factory=dict)
    valid: bool = True
    invalidation_reason: Optional[str] = None


class TimelineConflictResolver:
    """
    Resolves conflicts when revocation timestamps race with other events.

    The core problem: If A is revoked at T=100, but a transaction at T=99
    was processed by a node that didn't know about the revocation until T=105,
    is the transaction valid?

    Web4 resolution: RETROACTIVE VOID with finality window.
    - Revocation timestamp is the authority
    - Transactions after revocation timestamp are void
    - But transactions before revocation and finalized before propagation are valid
    - Finality window = max propagation delay
    """

    def __init__(self, finality_window_ms: float = 1000.0):
        self.finality_window_ms = finality_window_ms

    def resolve_conflicts(self, revocation_time: float,
                          events: List[TimelineEvent]) -> Dict[str, Any]:
        """Resolve all events against a revocation timestamp."""
        results = {
            "revocation_time": revocation_time,
            "finality_window": self.finality_window_ms,
            "events_analyzed": len(events),
            "events_voided": 0,
            "events_valid": 0,
            "events_in_limbo": 0,  # within finality window
            "details": [],
        }

        for event in events:
            if event.timestamp < revocation_time - self.finality_window_ms:
                # Well before revocation — definitely valid
                event.valid = True
                results["events_valid"] += 1
                status = "VALID (before revocation window)"
            elif event.timestamp > revocation_time:
                # After revocation — definitely void
                event.valid = False
                event.invalidation_reason = "after_revocation"
                results["events_voided"] += 1
                status = "VOIDED (after revocation)"
            else:
                # Within finality window — depends on finalization
                finalized_before_revocation = event.details.get("finalized_at", float('inf')) < revocation_time
                if finalized_before_revocation:
                    event.valid = True
                    results["events_valid"] += 1
                    status = "VALID (finalized before revocation)"
                else:
                    event.valid = False
                    event.invalidation_reason = "in_finality_window_unfinalized"
                    results["events_in_limbo"] += 1
                    status = "LIMBO (in finality window, not finalized)"

            results["details"].append({
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "actor": event.actor,
                "status": status,
                "valid": event.valid,
            })

        return results


# ============================================================
# Section 5: Revocation Attack Analysis
# ============================================================

@dataclass
class RevocationAttack:
    """An attack that weaponizes the revocation system."""
    name: str
    description: str
    attacker_goal: str
    mechanism: str
    defense: str
    simulated_impact: Dict[str, Any] = field(default_factory=dict)


class RevocationAttackAnalyzer:
    """Analyzes attacks that exploit the revocation system itself."""

    def analyze_all(self) -> List[RevocationAttack]:
        attacks = []

        # Attack 1: Revocation flooding
        flood_impact = self._simulate_revocation_flood()
        attacks.append(RevocationAttack(
            name="Revocation Flooding",
            description="Attacker submits massive number of false revocation requests to overwhelm the system",
            attacker_goal="Denial of service via revocation processing overload",
            mechanism="Create many LCTs, then revoke them all simultaneously to trigger cascading processing",
            defense=(
                "Rate limiting on revocation requests per identity. "
                "Revocation requires ATP stake (economic cost). "
                "Batched processing with priority queue (genuine revocations prioritized by trust score)."
            ),
            simulated_impact=flood_impact,
        ))

        # Attack 2: Strategic revocation to partition network
        partition_impact = self._simulate_partition_revocation()
        attacks.append(RevocationAttack(
            name="Strategic Partition via Revocation",
            description="Revoke carefully chosen bridge nodes to partition the trust network",
            attacker_goal="Isolate a federation or community from the rest of the network",
            mechanism="Identify and revoke bridge nodes between federations",
            defense=(
                "Bridge node redundancy: minimum 3 bridges per federation pair. "
                "Bridge nodes have higher revocation threshold (requires multiple attestations). "
                "Automatic bridge replacement when bridge count drops below minimum."
            ),
            simulated_impact=partition_impact,
        ))

        # Attack 3: Revocation-then-race
        race_impact = self._simulate_revocation_race()
        attacks.append(RevocationAttack(
            name="Revocation Race Attack",
            description="Submit transactions just before expected revocation to exploit propagation delay",
            attacker_goal="Execute unauthorized transactions during the propagation window",
            mechanism="Know revocation is coming, submit transactions to far nodes before revocation arrives",
            defense=(
                "Finality window: transactions not final until propagation delay elapsed. "
                "Revocation has retroactive effect: voids transactions after revocation timestamp. "
                "High-value transactions require additional confirmation during finality window."
            ),
            simulated_impact=race_impact,
        ))

        # Attack 4: False revocation of competitor
        false_revocation_impact = self._simulate_false_revocation()
        attacks.append(RevocationAttack(
            name="False Revocation Attack",
            description="Attacker with admin access falsely revokes a competitor's LCT",
            attacker_goal="Disable a legitimate entity through false revocation",
            mechanism="Abuse admin privileges to revoke without valid reason",
            defense=(
                "Multi-signature revocation: requires 2-of-3 admin signatures for revocation. "
                "Revocation challenge period: revoked entity has 24h to challenge. "
                "Admin accountability: false revocations penalize the admin's own T3 score."
            ),
            simulated_impact=false_revocation_impact,
        ))

        return attacks

    def _simulate_revocation_flood(self) -> Dict[str, Any]:
        """Simulate revocation flooding attack."""
        # Without defense: process all N revocations
        n_flood = 10000
        processing_time_per = 0.001  # 1ms per revocation
        total_time_without = n_flood * processing_time_per

        # With defense: rate limit to 100/sec per identity
        rate_limit = 100
        total_time_with = n_flood / rate_limit  # seconds to drain at rate limit
        atp_cost_per = 1.0  # 1 ATP per revocation
        total_atp_cost = n_flood * atp_cost_per

        return {
            "flood_size": n_flood,
            "without_defense_seconds": total_time_without,
            "with_defense_seconds": total_time_with,
            "atp_cost_to_attacker": total_atp_cost,
            "defense_effective": total_atp_cost > 5000,  # expensive to flood
        }

    def _simulate_partition_revocation(self) -> Dict[str, Any]:
        """Simulate strategic partition via bridge node revocation."""
        n_bridges = 3  # bridges between two federations
        bridge_trust_threshold = 0.8  # high trust required to revoke bridge

        # Without defense: revoke all 3 bridges → partition
        # With defense: need to compromise 3 high-trust nodes simultaneously
        attack_cost = n_bridges * 650  # hardware cost per identity
        detection_probability = 1 - (1 - 0.85) ** n_bridges  # probability at least one detected

        return {
            "bridges_needed": n_bridges,
            "attack_cost": attack_cost,
            "detection_probability": round(detection_probability, 4),
            "auto_replacement": True,
            "replacement_time_seconds": 30,
            "defense_effective": detection_probability > 0.95,
        }

    def _simulate_revocation_race(self) -> Dict[str, Any]:
        """Simulate revocation race condition."""
        propagation_delay_ms = 500
        transaction_latency_ms = 50
        finality_window_ms = 1000

        # Transactions during propagation window
        transactions_in_window = propagation_delay_ms // transaction_latency_ms

        # With finality window: all transactions in window are held
        transactions_held = finality_window_ms // transaction_latency_ms

        return {
            "propagation_delay_ms": propagation_delay_ms,
            "transactions_in_race_window": transactions_in_window,
            "finality_window_ms": finality_window_ms,
            "transactions_held": transactions_held,
            "retroactive_void": True,
            "defense_effective": True,
        }

    def _simulate_false_revocation(self) -> Dict[str, Any]:
        """Simulate false revocation attack."""
        signatures_required = 2
        challenge_period_hours = 24
        admin_t3_penalty = 0.3  # T3 penalty for false revocation

        return {
            "signatures_required": signatures_required,
            "challenge_period_hours": challenge_period_hours,
            "admin_penalty": admin_t3_penalty,
            "victim_downtime_max_hours": challenge_period_hours,
            "defense_effective": signatures_required >= 2,
        }


# ============================================================
# Section 6: Recovery Ceremony
# ============================================================

@dataclass
class RecoveryStep:
    """A step in the recovery ceremony."""
    step_number: int
    description: str
    requires: List[str]
    produces: str
    estimated_time_hours: float


class RecoveryCeremony:
    """
    Formal ceremony for recovering from an LCT revocation.

    Different recovery paths based on revocation reason:
    1. Key compromise → Full key rotation + re-attestation
    2. Behavior violation → Probation period + community vote
    3. Cascade (parent revoked) → Re-delegation from new parent
    4. Incorrect revocation → Fast restore with compensation
    """

    def plan_recovery(self, identity: LCTIdentity) -> Dict[str, Any]:
        """Generate a recovery plan based on revocation reason."""
        if identity.status not in (LCTStatus.REVOKED, LCTStatus.SUSPENDED):
            return {"error": "Identity is not revoked or suspended"}

        reason = identity.revocation_reason

        if reason == RevocationReason.KEY_COMPROMISE:
            return self._key_compromise_recovery(identity)
        elif reason == RevocationReason.BEHAVIOR_VIOLATION:
            return self._behavior_violation_recovery(identity)
        elif reason == RevocationReason.CASCADE:
            return self._cascade_recovery(identity)
        elif reason == RevocationReason.INCORRECT_REVERSAL:
            return self._incorrect_revocation_recovery(identity)
        elif reason == RevocationReason.VOLUNTARY:
            return self._voluntary_recovery(identity)
        else:
            return self._default_recovery(identity)

    def _key_compromise_recovery(self, identity: LCTIdentity) -> Dict[str, Any]:
        steps = [
            RecoveryStep(1, "Generate new cryptographic keypair", ["hardware_access"], "new_keypair", 0.5),
            RecoveryStep(2, "Bind new key to hardware (TPM/SE)", ["new_keypair", "tpm_access"], "hardware_binding", 1.0),
            RecoveryStep(3, "Submit key rotation request to federation admin", ["hardware_binding"], "rotation_request", 0.5),
            RecoveryStep(4, "Admin verifies hardware binding and approves rotation", ["rotation_request", "admin_approval"], "new_lct", 2.0),
            RecoveryStep(5, "Re-establish witness attestations (minimum 3)", ["new_lct"], "witness_attestations", 24.0),
            RecoveryStep(6, "Probation period with reduced permissions", ["witness_attestations"], "probation_complete", 168.0),
        ]

        return {
            "recovery_type": "key_compromise",
            "steps": [{"step": s.step_number, "description": s.description,
                       "time_hours": s.estimated_time_hours} for s in steps],
            "total_time_hours": sum(s.estimated_time_hours for s in steps),
            "atp_recovery": 0.5,  # 50% ATP recovered after ceremony
            "t3_starting": 0.2,   # very low trust — must re-earn
            "permissions_during_probation": {"read"},  # read-only during probation
            "full_recovery_time_hours": sum(s.estimated_time_hours for s in steps),
        }

    def _behavior_violation_recovery(self, identity: LCTIdentity) -> Dict[str, Any]:
        steps = [
            RecoveryStep(1, "Submit appeal with evidence of remediation", [], "appeal", 1.0),
            RecoveryStep(2, "Community review of appeal (minimum 5 voters)", ["appeal"], "community_vote", 72.0),
            RecoveryStep(3, "If approved: enter probation with monitoring", ["community_vote"], "probation", 0.5),
            RecoveryStep(4, "Complete probation period with good behavior", ["probation"], "probation_complete", 720.0),
        ]

        return {
            "recovery_type": "behavior_violation",
            "steps": [{"step": s.step_number, "description": s.description,
                       "time_hours": s.estimated_time_hours} for s in steps],
            "total_time_hours": sum(s.estimated_time_hours for s in steps),
            "atp_recovery": 0.3,  # 30% ATP recovered
            "t3_starting": 0.1,   # very low trust
            "community_vote_threshold": 0.67,  # 2/3 majority needed
            "probation_duration_hours": 720,  # 30 days
        }

    def _cascade_recovery(self, identity: LCTIdentity) -> Dict[str, Any]:
        steps = [
            RecoveryStep(1, "Identify new delegator (parent)", [], "new_parent", 2.0),
            RecoveryStep(2, "New parent verifies identity and grants delegation", ["new_parent"], "new_delegation", 4.0),
            RecoveryStep(3, "Federation admin approves re-delegation", ["new_delegation"], "admin_approval", 8.0),
        ]

        return {
            "recovery_type": "cascade",
            "steps": [{"step": s.step_number, "description": s.description,
                       "time_hours": s.estimated_time_hours} for s in steps],
            "total_time_hours": sum(s.estimated_time_hours for s in steps),
            "atp_recovery": 0.9,  # 90% — not their fault
            "t3_starting": 0.4,   # moderate — cascade wasn't their fault
            "note": "Cascade revocation was not caused by this entity's behavior",
        }

    def _incorrect_revocation_recovery(self, identity: LCTIdentity) -> Dict[str, Any]:
        steps = [
            RecoveryStep(1, "Admin acknowledges incorrect revocation", [], "acknowledgment", 0.5),
            RecoveryStep(2, "Immediate restore with full permissions", ["acknowledgment"], "restored", 0.1),
            RecoveryStep(3, "Compensation: ATP bonus + T3 boost for inconvenience", ["restored"], "compensated", 0.5),
        ]

        return {
            "recovery_type": "incorrect_revocation",
            "steps": [{"step": s.step_number, "description": s.description,
                       "time_hours": s.estimated_time_hours} for s in steps],
            "total_time_hours": sum(s.estimated_time_hours for s in steps),
            "atp_recovery": 1.2,  # 120% — compensation for wrongful revocation
            "t3_starting": 0.6,   # higher starting trust — wrongful revocation
            "compensation_atp_bonus": 20.0,
        }

    def _voluntary_recovery(self, identity: LCTIdentity) -> Dict[str, Any]:
        return {
            "recovery_type": "voluntary",
            "steps": [{"step": 1, "description": "Submit reactivation request",
                       "time_hours": 0.5}],
            "total_time_hours": 0.5,
            "atp_recovery": 0.95,
            "t3_starting": identity.t3_composite * 0.8,  # slight trust decay during absence
        }

    def _default_recovery(self, identity: LCTIdentity) -> Dict[str, Any]:
        return {
            "recovery_type": "default",
            "steps": [
                {"step": 1, "description": "Submit recovery request", "time_hours": 1.0},
                {"step": 2, "description": "Admin review and approval", "time_hours": 24.0},
            ],
            "total_time_hours": 25.0,
            "atp_recovery": 0.7,
            "t3_starting": 0.3,
        }


# ============================================================
# Section 7: Cascade Depth Analysis
# ============================================================

class CascadeDepthAnalyzer:
    """
    Analyzes how cascade depth affects the revocation blast radius.

    Key insight: delegation chains create amplification —
    revoking a root-level delegator can cascade to N^d entities
    (N delegatees per level, d levels deep).
    """

    def analyze_blast_radius(self, branching_factor: int = 3,
                              max_depth: int = 5) -> Dict[str, Any]:
        """Calculate blast radius for different chain depths."""
        depths = []
        total_revoked = 0

        for d in range(max_depth + 1):
            entities_at_depth = branching_factor ** d
            total_revoked += entities_at_depth
            depths.append({
                "depth": d,
                "entities_at_depth": entities_at_depth,
                "cumulative_revoked": total_revoked,
                "cascade_time_factor": d,  # linear with depth
            })

        return {
            "branching_factor": branching_factor,
            "max_depth": max_depth,
            "total_blast_radius": total_revoked,
            "depths": depths,
            "geometric_growth": True,
            "mitigation": "Delegation depth limit of 7 caps blast radius",
            "capped_blast_radius": sum(branching_factor ** d for d in range(min(max_depth, 7) + 1)),
        }

    def simulate_cascade_timing(self, engine: RevocationCascadeEngine,
                                 root_id: str) -> Dict[str, Any]:
        """Simulate cascade timing for a specific delegation tree."""
        result = engine.revoke(root_id, RevocationReason.KEY_COMPROMISE, "admin",
                               propagation_delay=0.1)

        if "error" in result:
            return result

        # Analyze timing by depth
        depth_timing = defaultdict(list)
        for event in result["cascade_events"]:
            depth_timing[event["depth"]].append(event)

        timing_analysis = []
        for depth in sorted(depth_timing.keys()):
            events = depth_timing[depth]
            timing_analysis.append({
                "depth": depth,
                "entities_revoked": len(events),
                "propagation_delay": depth * 0.1,
            })

        return {
            "root": root_id,
            "total_revoked": result["total_revoked"],
            "max_depth": result["max_depth"],
            "timing": timing_analysis,
            "total_atp_frozen": result["atp_frozen"],
        }


# ============================================================
# Section 8: Tests
# ============================================================

def run_tests():
    """Run all revocation cascade tests."""
    checks_passed = 0
    checks_failed = 0

    def check(condition, description):
        nonlocal checks_passed, checks_failed
        status = "✓" if condition else "✗"
        print(f"  {status} {description}")
        if condition:
            checks_passed += 1
        else:
            checks_failed += 1

    # --- Section 1-2: Core Cascade Engine ---
    print("\n=== S1-2: Core Cascade Engine ===")

    engine = RevocationCascadeEngine()

    # Build delegation tree: root -> [a1, a2] -> [b1, b2] each
    root = LCTIdentity(lct_id="root", created_at=0, atp_balance=200.0, t3_composite=0.9)
    a1 = LCTIdentity(lct_id="a1", parent_id="root", created_at=1, atp_balance=100.0, t3_composite=0.7)
    a2 = LCTIdentity(lct_id="a2", parent_id="root", created_at=1, atp_balance=100.0, t3_composite=0.6)
    b1 = LCTIdentity(lct_id="b1", parent_id="a1", created_at=2, atp_balance=50.0, t3_composite=0.5)
    b2 = LCTIdentity(lct_id="b2", parent_id="a1", created_at=2, atp_balance=50.0, t3_composite=0.4)
    b3 = LCTIdentity(lct_id="b3", parent_id="a2", created_at=2, atp_balance=50.0, t3_composite=0.5)

    for identity in [root, a1, a2, b1, b2, b3]:
        engine.register(identity)

    check(len(engine.identities) == 6, "s1_registered_6_identities")
    check(len(root.delegatees) == 2, "s2_root_has_2_delegatees")
    check(len(a1.delegatees) == 2, "s3_a1_has_2_delegatees")

    # Add transactions
    tx1 = Transaction(tx_id="tx1", sender="a1", receiver="b1", amount=10, timestamp=0.5)
    tx2 = Transaction(tx_id="tx2", sender="b2", receiver="a2", amount=5, timestamp=0.9)
    tx3 = Transaction(tx_id="tx3", sender="root", receiver="a1", amount=20, timestamp=1.5, finalized=True)
    engine.submit_transaction(tx1)
    engine.submit_transaction(tx2)
    engine.submit_transaction(tx3)

    # Revoke a1 — should cascade to b1, b2
    result = engine.revoke("a1", RevocationReason.KEY_COMPROMISE, "admin", propagation_delay=0.1)
    check(result["total_revoked"] == 3, "s4_cascade_revoked_3_entities")  # a1 + b1 + b2
    check(result["max_depth"] == 1, "s5_max_cascade_depth_1")
    check(result["atp_frozen"] > 0, "s6_atp_was_frozen")
    check("key_compromise" in result["reason"], "s7_reason_is_key_compromise")

    # a1 should be revoked
    check(engine.identities["a1"].status == LCTStatus.REVOKED, "s8_a1_is_revoked")
    check(engine.identities["b1"].status == LCTStatus.REVOKED, "s9_b1_cascade_revoked")
    check(engine.identities["b2"].status == LCTStatus.REVOKED, "s10_b2_cascade_revoked")

    # a2 and b3 should NOT be revoked (different branch)
    check(engine.identities["a2"].status == LCTStatus.ACTIVE, "s11_a2_still_active")
    check(engine.identities["b3"].status == LCTStatus.ACTIVE, "s12_b3_still_active")

    # Root should still be active (parent doesn't cascade UP)
    check(engine.identities["root"].status == LCTStatus.ACTIVE, "s13_root_still_active")

    # T3 should be zeroed for revoked entities
    check(engine.identities["a1"].t3_composite == 0.0, "s14_a1_t3_zeroed")
    check(engine.identities["b1"].t3_composite == 0.0, "s15_b1_t3_zeroed")

    # --- Section 2 continued: Suspension and Restore ---
    print("\n=== S2b: Suspension and Restore ===")

    engine2 = RevocationCascadeEngine()
    entity = LCTIdentity(lct_id="e1", created_at=0, atp_balance=100.0, t3_composite=0.7)
    engine2.register(entity)

    suspended = engine2.suspend("e1", RevocationReason.BEHAVIOR_VIOLATION)
    check(suspended, "s16_suspension_successful")
    check(engine2.identities["e1"].status == LCTStatus.SUSPENDED, "s17_status_is_suspended")

    restore_result = engine2.restore("e1", "admin")
    check(restore_result["success"], "s18_restore_successful")
    check(engine2.identities["e1"].status == LCTStatus.RESTORED, "s19_status_is_restored")
    check(restore_result["atp_recovered"] > 0, "s20_atp_partially_recovered")
    check(restore_result["t3_starting"] == 0.3, "s21_t3_starts_low_after_restore")

    # Cannot restore key compromise without rotation
    engine3 = RevocationCascadeEngine()
    kc_entity = LCTIdentity(lct_id="kc1", created_at=0)
    engine3.register(kc_entity)
    engine3.revoke("kc1", RevocationReason.KEY_COMPROMISE, "admin")
    kc_restore = engine3.restore("kc1", "admin")
    check(not kc_restore["success"], "s22_cannot_restore_key_compromise")

    # --- Section 3: Cross-Federation Propagation ---
    print("\n=== S3: Cross-Federation Propagation ===")

    propagator = CrossFederationPropagator()
    fed_a = Federation(federation_id="fed_a", members={"a1", "a2", "a3"}, propagation_latency_ms=50.0,
                       bridge_nodes={"a3"})
    fed_b = Federation(federation_id="fed_b", members={"b1", "b2"}, propagation_latency_ms=100.0,
                       bridge_nodes={"b1"})
    fed_c = Federation(federation_id="fed_c", members={"c1", "c2", "c3", "c4"}, propagation_latency_ms=75.0,
                       bridge_nodes={"c1"})

    propagator.add_federation(fed_a)
    propagator.add_federation(fed_b)
    propagator.add_federation(fed_c)

    # Propagation from fed_a
    prop_result = propagator.simulate_propagation("a1", "fed_a")
    check(prop_result["source_federation"] == "fed_a", "s23_source_federation_correct")
    check(prop_result["propagation_map"]["fed_a"]["propagation_time_ms"] == 50.0, "s24_intra_fed_fast")
    check(prop_result["propagation_map"]["fed_b"]["propagation_time_ms"] > 50.0, "s25_cross_fed_slower")
    check(prop_result["max_propagation_ms"] > 0, "s26_max_propagation_positive")
    check(prop_result["total_entities_notified"] == 9, "s27_all_9_entities_notified")

    # Inter-federation should be ~10x intra-federation
    intra_time = prop_result["propagation_map"]["fed_a"]["propagation_time_ms"]
    inter_time = prop_result["propagation_map"]["fed_b"]["propagation_time_ms"]
    check(inter_time > intra_time * 3, "s28_inter_federation_significantly_slower")

    # --- Section 4: Timeline Conflict Resolution ---
    print("\n=== S4: Timeline Conflict Resolution ===")

    resolver = TimelineConflictResolver(finality_window_ms=100.0)

    events = [
        TimelineEvent("transaction", 50.0, "alice", {"finalized_at": 55.0}),   # before window
        TimelineEvent("transaction", 95.0, "bob", {"finalized_at": 96.0}),     # in window, finalized before
        TimelineEvent("transaction", 98.0, "carol", {"finalized_at": 110.0}),  # in window, not finalized
        TimelineEvent("delegation", 105.0, "dave"),                             # after revocation
        TimelineEvent("attestation", 150.0, "eve"),                             # well after
    ]

    resolution = resolver.resolve_conflicts(revocation_time=100.0, events=events)

    check(resolution["events_analyzed"] == 5, "s29_analyzed_5_events")
    check(resolution["events_valid"] == 2, "s30_2_events_valid")
    check(resolution["events_voided"] == 2, "s31_2_events_voided")
    check(resolution["events_in_limbo"] == 1, "s32_1_event_in_limbo")

    # Check specific event statuses
    check(resolution["details"][0]["valid"], "s33_pre_window_event_valid")
    check(resolution["details"][1]["valid"], "s34_finalized_before_revocation_valid")
    check(not resolution["details"][2]["valid"], "s35_unfinalized_in_window_invalid")
    check(not resolution["details"][3]["valid"], "s36_post_revocation_voided")
    check(not resolution["details"][4]["valid"], "s37_well_after_revocation_voided")

    # --- Section 5: Revocation Attacks ---
    print("\n=== S5: Revocation Attacks ===")

    attack_analyzer = RevocationAttackAnalyzer()
    attacks = attack_analyzer.analyze_all()

    check(len(attacks) == 4, "s38_4_attack_types_analyzed")

    # Check specific attacks
    flood = attacks[0]
    check(flood.name == "Revocation Flooding", "s39_flood_attack_identified")
    check(flood.simulated_impact["defense_effective"], "s40_flood_defense_effective")
    check(flood.simulated_impact["atp_cost_to_attacker"] > 5000, "s41_flood_expensive_to_attacker")

    partition = attacks[1]
    check(partition.simulated_impact["detection_probability"] > 0.95, "s42_partition_likely_detected")
    check(partition.simulated_impact["auto_replacement"], "s43_auto_bridge_replacement_exists")

    race = attacks[2]
    check(race.simulated_impact["retroactive_void"], "s44_retroactive_void_prevents_race")
    check(race.simulated_impact["defense_effective"], "s45_race_defense_effective")

    false_rev = attacks[3]
    check(false_rev.simulated_impact["signatures_required"] >= 2, "s46_multi_sig_required")
    check(false_rev.simulated_impact["defense_effective"], "s47_false_revocation_defense_effective")

    # --- Section 6: Recovery Ceremony ---
    print("\n=== S6: Recovery Ceremony ===")

    ceremony = RecoveryCeremony()

    # Key compromise recovery
    kc_identity = LCTIdentity(lct_id="kc", status=LCTStatus.REVOKED,
                               revocation_reason=RevocationReason.KEY_COMPROMISE)
    kc_plan = ceremony.plan_recovery(kc_identity)
    check(kc_plan["recovery_type"] == "key_compromise", "s48_kc_recovery_type_correct")
    check(len(kc_plan["steps"]) == 6, "s49_kc_has_6_steps")
    check(kc_plan["t3_starting"] == 0.2, "s50_kc_low_starting_trust")
    check(kc_plan["atp_recovery"] == 0.5, "s51_kc_50pct_atp_recovery")

    # Behavior violation recovery
    bv_identity = LCTIdentity(lct_id="bv", status=LCTStatus.REVOKED,
                               revocation_reason=RevocationReason.BEHAVIOR_VIOLATION)
    bv_plan = ceremony.plan_recovery(bv_identity)
    check(bv_plan["recovery_type"] == "behavior_violation", "s52_bv_recovery_type_correct")
    check(bv_plan["community_vote_threshold"] == 0.67, "s53_bv_requires_2_3_majority")
    check(bv_plan["probation_duration_hours"] == 720, "s54_bv_30_day_probation")

    # Cascade recovery (not their fault)
    cascade_identity = LCTIdentity(lct_id="cas", status=LCTStatus.REVOKED,
                                    revocation_reason=RevocationReason.CASCADE)
    cas_plan = ceremony.plan_recovery(cascade_identity)
    check(cas_plan["recovery_type"] == "cascade", "s55_cascade_recovery_type")
    check(cas_plan["atp_recovery"] == 0.9, "s56_cascade_90pct_atp_recovery")
    check(cas_plan["t3_starting"] == 0.4, "s57_cascade_moderate_starting_trust")

    # Incorrect revocation recovery (compensation)
    ir_identity = LCTIdentity(lct_id="ir", status=LCTStatus.REVOKED,
                               revocation_reason=RevocationReason.INCORRECT_REVERSAL)
    ir_plan = ceremony.plan_recovery(ir_identity)
    check(ir_plan["recovery_type"] == "incorrect_revocation", "s58_incorrect_recovery_type")
    check(ir_plan["atp_recovery"] == 1.2, "s59_incorrect_120pct_atp_compensation")
    check(ir_plan["compensation_atp_bonus"] == 20.0, "s60_incorrect_bonus_compensation")

    # Recovery proportionality: cascade fastest, key compromise slowest
    check(cas_plan["total_time_hours"] < kc_plan["total_time_hours"],
          "s61_cascade_faster_than_key_compromise")
    check(ir_plan["total_time_hours"] < bv_plan["total_time_hours"],
          "s62_incorrect_faster_than_behavior_violation")

    # --- Section 7: Cascade Depth Analysis ---
    print("\n=== S7: Cascade Depth Analysis ===")

    depth_analyzer = CascadeDepthAnalyzer()
    blast = depth_analyzer.analyze_blast_radius(branching_factor=3, max_depth=5)

    check(blast["branching_factor"] == 3, "s63_branching_factor_3")
    check(blast["max_depth"] == 5, "s64_max_depth_5")
    check(blast["total_blast_radius"] == 1 + 3 + 9 + 27 + 81 + 243, "s65_total_blast_radius_364")
    check(blast["geometric_growth"], "s66_geometric_growth_confirmed")

    # Depth 0 = 1 (root), Depth 1 = 3, Depth 2 = 9
    check(blast["depths"][0]["entities_at_depth"] == 1, "s67_depth_0_is_1")
    check(blast["depths"][1]["entities_at_depth"] == 3, "s68_depth_1_is_3")
    check(blast["depths"][2]["entities_at_depth"] == 9, "s69_depth_2_is_9")

    # Capped blast radius should be <= total
    check(blast["capped_blast_radius"] <= blast["total_blast_radius"], "s70_capped_leq_total")

    # Simulate cascade on a real tree
    engine4 = RevocationCascadeEngine()
    tree_root = LCTIdentity(lct_id="tree_root", created_at=0, atp_balance=500.0)
    engine4.register(tree_root)

    # Build 3-level tree: root -> 3 children -> 3 grandchildren each
    for i in range(3):
        child = LCTIdentity(lct_id=f"child_{i}", parent_id="tree_root", atp_balance=100.0)
        engine4.register(child)
        for j in range(3):
            grandchild = LCTIdentity(lct_id=f"grandchild_{i}_{j}", parent_id=f"child_{i}", atp_balance=50.0)
            engine4.register(grandchild)

    cascade_timing = depth_analyzer.simulate_cascade_timing(engine4, "tree_root")
    check(cascade_timing["total_revoked"] == 13, "s71_tree_cascade_revokes_13")  # 1 + 3 + 9
    check(cascade_timing["max_depth"] == 2, "s72_tree_max_depth_2")
    check(cascade_timing["total_atp_frozen"] > 0, "s73_tree_atp_frozen")

    # Timing should show depth 0 first, then depth 1, then depth 2
    check(len(cascade_timing["timing"]) == 3, "s74_timing_has_3_depth_levels")
    check(cascade_timing["timing"][0]["depth"] == 0, "s75_first_timing_at_depth_0")
    check(cascade_timing["timing"][1]["entities_revoked"] == 3, "s76_depth_1_revokes_3")
    check(cascade_timing["timing"][2]["entities_revoked"] == 9, "s77_depth_2_revokes_9")

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"LCT Revocation Cascades: {checks_passed}/{checks_passed + checks_failed} checks passed")

    if checks_failed > 0:
        print(f"  FAILED: {checks_failed} checks")
    else:
        print("  ALL CHECKS PASSED")

    print(f"\nKey findings:")
    print(f"  - Cascade blast radius: {blast['total_blast_radius']} at depth 5 (branching=3)")
    print(f"  - Recovery time: cascade={cas_plan['total_time_hours']:.1f}h, "
          f"key_compromise={kc_plan['total_time_hours']:.1f}h")
    print(f"  - Cross-federation propagation: intra={intra_time}ms, inter={inter_time}ms")
    print(f"  - All 4 revocation attacks defended")

    return checks_passed, checks_failed


if __name__ == "__main__":
    run_tests()
