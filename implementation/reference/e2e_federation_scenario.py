#!/usr/bin/env python3
"""
End-to-End Federation Scenario — Session 20, Track 5

Complete lifecycle simulation exercising the full Web4 stack:
- Node bootstrap and discovery (DNS-SD + DHT)
- Schema version negotiation between peers
- Trust establishment via witnessing
- ATP allocation and transfer
- Consensus on federation state
- Key rotation ceremony
- Device compromise detection and revocation
- Partition and recovery
- Cross-federation trust bridge
- Full lifecycle: birth → active → suspend → reactivate → revoke
- Performance of integrated operations

Integrates: entity_discovery_protocol, schema_evolution_negotiation,
            consensus_partial_synchrony, hardware_binding_recovery,
            multi_scale_trust_composition, wire_protocol_serialization
"""

from __future__ import annotations
import hashlib
import math
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple


# ─── Data Structures ─────────────────────────────────────────────────────────

class EntityState(Enum):
    NASCENT = "nascent"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class TrustLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class T3:
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    @property
    def composite(self) -> float:
        return (self.talent + self.training + self.temperament) / 3.0


@dataclass
class ATPWallet:
    """ATP allocation and transfer tracking."""
    balance: float = 0.0
    total_received: float = 0.0
    total_sent: float = 0.0
    total_fees: float = 0.0

    def deposit(self, amount: float):
        self.balance += amount
        self.total_received += amount

    def transfer(self, amount: float, fee_rate: float = 0.05) -> Tuple[float, float]:
        """Transfer with fee. Returns (net_amount, fee)."""
        fee = amount * fee_rate
        total = amount + fee
        if total > self.balance:
            return 0.0, 0.0
        self.balance -= total
        self.total_sent += amount
        self.total_fees += fee
        return amount, fee


@dataclass
class FederationNode:
    """A node participating in a federation."""
    node_id: str
    state: EntityState = EntityState.NASCENT
    t3: T3 = field(default_factory=T3)
    wallet: ATPWallet = field(default_factory=ATPWallet)
    public_key: bytes = b""
    endpoints: List[str] = field(default_factory=list)
    witnesses: Set[str] = field(default_factory=set)
    witnessed_by: Set[str] = field(default_factory=set)
    schema_version: str = "1.0.0"
    hardware_anchor: str = "software"
    trust_score: float = 0.5
    last_active: float = 0.0
    key_version: int = 0
    birth_cert_hash: str = ""


@dataclass
class FederationEvent:
    """Logged federation event."""
    event_type: str
    source: str
    target: Optional[str]
    timestamp: float
    details: Dict = field(default_factory=dict)


# ─── S1: Node Bootstrap ─────────────────────────────────────────────────────

class Federation:
    """A complete federation with lifecycle management."""

    def __init__(self, federation_id: str, initial_atp: float = 1000.0):
        self.federation_id = federation_id
        self.nodes: Dict[str, FederationNode] = {}
        self.events: List[FederationEvent] = []
        self.initial_atp = initial_atp
        self.fee_pool: float = 0.0
        self.consensus_round: int = 0
        self.schema_versions: Dict[str, int] = {}  # version → count
        self.trust_edges: Dict[Tuple[str, str], float] = {}
        self.revoked_keys: Set[str] = set()

    def bootstrap_node(self, node_id: str, now: float, **kwargs) -> FederationNode:
        """Bootstrap a new node into the federation."""
        node = FederationNode(
            node_id=node_id,
            public_key=os.urandom(32),
            endpoints=[f"tcp://{node_id}:7400"],
            last_active=now,
            birth_cert_hash=hashlib.sha256(f"{node_id}:{now}".encode()).hexdigest()[:16],
            **kwargs,
        )
        self.nodes[node_id] = node
        self._log("bootstrap", node_id, None, now)
        return node

    def activate_node(self, node_id: str, now: float) -> bool:
        """Transition NASCENT → ACTIVE with initial ATP allocation."""
        node = self.nodes.get(node_id)
        if not node or node.state != EntityState.NASCENT:
            return False
        node.state = EntityState.ACTIVE
        # Initial ATP allocation scaled by sqrt(N)
        n = len([n for n in self.nodes.values() if n.state == EntityState.ACTIVE])
        allocation = max(50.0, self.initial_atp / math.sqrt(max(1, n)))
        node.wallet.deposit(allocation)
        node.last_active = now
        self._log("activate", node_id, None, now, {"atp": allocation})
        return True

    def suspend_node(self, node_id: str, now: float, reason: str = "") -> bool:
        """Transition ACTIVE → SUSPENDED."""
        node = self.nodes.get(node_id)
        if not node or node.state != EntityState.ACTIVE:
            return False
        node.state = EntityState.SUSPENDED
        self._log("suspend", node_id, None, now, {"reason": reason})
        return True

    def reactivate_node(self, node_id: str, now: float) -> bool:
        """Transition SUSPENDED → ACTIVE."""
        node = self.nodes.get(node_id)
        if not node or node.state != EntityState.SUSPENDED:
            return False
        node.state = EntityState.ACTIVE
        node.last_active = now
        self._log("reactivate", node_id, None, now)
        return True

    def revoke_node(self, node_id: str, now: float, reason: str = "") -> bool:
        """Transition to REVOKED (terminal state)."""
        node = self.nodes.get(node_id)
        if not node or node.state == EntityState.REVOKED:
            return False
        node.state = EntityState.REVOKED
        self.revoked_keys.add(node_id)
        # Remove trust edges
        to_remove = [k for k in self.trust_edges if node_id in k]
        for k in to_remove:
            del self.trust_edges[k]
        self._log("revoke", node_id, None, now, {"reason": reason})
        return True

    def _log(self, event_type: str, source: str, target: Optional[str],
             timestamp: float, details: Dict = None):
        self.events.append(FederationEvent(
            event_type, source, target, timestamp, details or {},
        ))


# ─── S2: Discovery and Handshake ────────────────────────────────────────────

    def discover_peers(self, node_id: str) -> List[str]:
        """Node discovers other active nodes."""
        return [
            nid for nid, node in self.nodes.items()
            if nid != node_id and node.state == EntityState.ACTIVE
        ]

    def negotiate_schema(self, node_a: str, node_b: str) -> Optional[str]:
        """Negotiate common schema version between two nodes."""
        a = self.nodes.get(node_a)
        b = self.nodes.get(node_b)
        if not a or not b:
            return None
        # Simple: take the lower version (backward compatible)
        va = tuple(int(x) for x in a.schema_version.split("."))
        vb = tuple(int(x) for x in b.schema_version.split("."))
        common = min(va, vb)
        return ".".join(str(x) for x in common)


# ─── S3: Trust Establishment via Witnessing ──────────────────────────────────

    def witness(self, witness_id: str, target_id: str, now: float,
                quality: float = 0.5) -> bool:
        """Witness establishes trust edge."""
        w = self.nodes.get(witness_id)
        t = self.nodes.get(target_id)
        if not w or not t:
            return False
        if w.state != EntityState.ACTIVE or t.state != EntityState.ACTIVE:
            return False
        if witness_id == target_id:
            return False

        w.witnesses.add(target_id)
        t.witnessed_by.add(witness_id)

        # Trust edge: witness's composite × quality
        edge_trust = w.t3.composite * quality
        self.trust_edges[(witness_id, target_id)] = edge_trust

        # Update target's trust score (weighted average with witness count)
        all_edges = [v for (_, tgt), v in self.trust_edges.items() if tgt == target_id]
        if all_edges:
            t.trust_score = sum(all_edges) / len(all_edges)

        # Training dimension improves with witness count
        t.t3.training = min(1.0, 0.3 + 0.05 * len(t.witnessed_by))

        self._log("witness", witness_id, target_id, now, {"quality": quality})
        return True


# ─── S4: ATP Transfer ───────────────────────────────────────────────────────

    def transfer_atp(self, sender_id: str, receiver_id: str, amount: float,
                     now: float) -> Tuple[bool, float]:
        """Transfer ATP between nodes. Returns (success, fee)."""
        sender = self.nodes.get(sender_id)
        receiver = self.nodes.get(receiver_id)
        if not sender or not receiver:
            return False, 0.0
        if sender.state != EntityState.ACTIVE or receiver.state != EntityState.ACTIVE:
            return False, 0.0

        net, fee = sender.wallet.transfer(amount)
        if net == 0:
            return False, 0.0

        receiver.wallet.deposit(net)
        self.fee_pool += fee

        self._log("transfer", sender_id, receiver_id, now,
                 {"amount": amount, "fee": fee, "net": net})
        return True, fee

    def atp_conservation(self) -> float:
        """Check ATP conservation: total should equal initial supply."""
        total_balances = sum(n.wallet.balance for n in self.nodes.values())
        total_fees = self.fee_pool
        total_sent_fees = sum(n.wallet.total_fees for n in self.nodes.values())
        return total_balances + total_fees


# ─── S5: Consensus Round ────────────────────────────────────────────────────

    def run_consensus(self, value: str, now: float) -> Tuple[bool, str]:
        """
        Simplified BFT consensus round.
        Requires 2f+1 active nodes (f = floor((n-1)/3)).
        """
        active = [n for n in self.nodes.values() if n.state == EntityState.ACTIVE]
        n = len(active)
        if n < 4:
            return False, "insufficient_nodes"

        f = (n - 1) // 3
        quorum = 2 * f + 1

        # Simulate voting — all honest nodes vote for value
        votes = n  # All active nodes agree (no Byzantine in this scenario)
        if votes >= quorum:
            self.consensus_round += 1
            self._log("consensus", "federation", None, now,
                     {"round": self.consensus_round, "value": value, "votes": votes})
            return True, "finalized"

        return False, "no_quorum"


# ─── S6: Key Rotation ───────────────────────────────────────────────────────

    def rotate_key(self, node_id: str, now: float) -> bool:
        """Rotate a node's key pair."""
        node = self.nodes.get(node_id)
        if not node or node.state != EntityState.ACTIVE:
            return False

        old_key_hash = hashlib.sha256(node.public_key).hexdigest()[:16]
        node.public_key = os.urandom(32)
        node.key_version += 1

        self._log("key_rotation", node_id, None, now,
                 {"old_key": old_key_hash, "version": node.key_version})
        return True


# ─── S7: Compromise and Revocation ──────────────────────────────────────────

    def detect_compromise(self, node_id: str) -> bool:
        """Simplified compromise detection: trust below threshold."""
        node = self.nodes.get(node_id)
        if not node:
            return False
        return node.trust_score < 0.2

    def cascade_revocation(self, node_id: str, now: float) -> List[str]:
        """Revoke a node and any node exclusively witnessed by it."""
        revoked = []
        if self.revoke_node(node_id, now, "compromise"):
            revoked.append(node_id)

        # Check for nodes only witnessed by revoked node
        for nid, node in list(self.nodes.items()):
            if node.state == EntityState.REVOKED:
                continue
            if node.witnessed_by and node.witnessed_by.issubset(self.revoked_keys):
                if self.revoke_node(nid, now, f"cascade_from:{node_id}"):
                    revoked.append(nid)

        return revoked


# ─── S8: Partition and Recovery ──────────────────────────────────────────────

    def simulate_partition(self, group_a: Set[str], group_b: Set[str], now: float) -> Dict:
        """Simulate a network partition between two groups."""
        # Remove cross-group trust edges
        removed_edges = []
        for (src, tgt), trust in list(self.trust_edges.items()):
            if (src in group_a and tgt in group_b) or (src in group_b and tgt in group_a):
                removed_edges.append(((src, tgt), trust))
                del self.trust_edges[(src, tgt)]

        self._log("partition", "network", None, now,
                 {"group_a": list(group_a), "group_b": list(group_b)})

        return {"removed_edges": len(removed_edges), "edges": removed_edges}

    def heal_partition(self, partition_data: Dict, now: float):
        """Restore edges after partition heals."""
        for (src, tgt), trust in partition_data.get("edges", []):
            # Restore with decayed trust (partition damages trust)
            self.trust_edges[(src, tgt)] = trust * 0.8
        self._log("partition_heal", "network", None, now)


# ─── S9: Cross-Federation Bridge ────────────────────────────────────────────

    def create_bridge(self, other: "Federation", bridge_nodes: Tuple[str, str],
                      now: float) -> float:
        """Create trust bridge with another federation."""
        local_node = self.nodes.get(bridge_nodes[0])
        remote_node = other.nodes.get(bridge_nodes[1])
        if not local_node or not remote_node:
            return 0.0
        if local_node.state != EntityState.ACTIVE or remote_node.state != EntityState.ACTIVE:
            return 0.0

        bridge_trust = min(local_node.trust_score, remote_node.trust_score) * 0.8
        self._log("bridge", bridge_nodes[0], bridge_nodes[1], now,
                 {"remote_fed": other.federation_id, "trust": bridge_trust})
        return bridge_trust


# ─── S10: Full Lifecycle ────────────────────────────────────────────────────

    def active_count(self) -> int:
        return sum(1 for n in self.nodes.values() if n.state == EntityState.ACTIVE)

    def total_trust(self) -> float:
        return sum(v for v in self.trust_edges.values())

    def event_count(self, event_type: str = None) -> int:
        if event_type:
            return sum(1 for e in self.events if e.event_type == event_type)
        return len(self.events)


# ══════════════════════════════════════════════════════════════════════════════
#  CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def run_checks():
    checks = []
    now = 1000000.0

    # ── S1: Node Bootstrap ───────────────────────────────────────────────

    fed = Federation("test_fed", initial_atp=10000.0)

    # S1.1: Bootstrap creates nascent node
    n1 = fed.bootstrap_node("alice", now)
    checks.append(("s1_bootstrap_nascent", n1.state == EntityState.NASCENT))

    # S1.2: Activate transitions to ACTIVE with ATP
    fed.activate_node("alice", now + 1)
    checks.append(("s1_activate", n1.state == EntityState.ACTIVE and n1.wallet.balance > 0))

    # S1.3: Bootstrap 5 more nodes
    for name in ["bob", "charlie", "dave", "eve", "frank"]:
        fed.bootstrap_node(name, now + 2)
        fed.activate_node(name, now + 3)
    checks.append(("s1_6_nodes", fed.active_count() == 6))

    # S1.4: Birth cert hash generated
    checks.append(("s1_birth_cert", len(n1.birth_cert_hash) == 16))

    # S1.5: Cannot activate already active node
    checks.append(("s1_double_activate", not fed.activate_node("alice", now + 4)))

    # ── S2: Discovery and Handshake ──────────────────────────────────────

    # S2.1: Discover peers
    peers = fed.discover_peers("alice")
    checks.append(("s2_discover_5_peers", len(peers) == 5))

    # S2.2: Don't discover self
    checks.append(("s2_no_self", "alice" not in peers))

    # S2.3: Schema negotiation (same version)
    schema = fed.negotiate_schema("alice", "bob")
    checks.append(("s2_schema_match", schema == "1.0.0"))

    # S2.4: Schema negotiation (different versions)
    fed.nodes["bob"].schema_version = "1.1.0"
    schema = fed.negotiate_schema("alice", "bob")
    checks.append(("s2_schema_lower", schema == "1.0.0"))

    # ── S3: Trust Establishment ──────────────────────────────────────────

    # S3.1: Witness creates trust edge
    fed.witness("alice", "bob", now + 10, quality=0.8)
    checks.append(("s3_witness_edge", ("alice", "bob") in fed.trust_edges))

    # S3.2: Trust score updates
    checks.append(("s3_trust_updated", fed.nodes["bob"].trust_score > 0))

    # S3.3: Multiple witnesses improve trust
    old_trust = fed.nodes["charlie"].trust_score
    fed.witness("alice", "charlie", now + 11, quality=0.9)
    fed.witness("bob", "charlie", now + 12, quality=0.7)
    checks.append(("s3_multi_witness", fed.nodes["charlie"].trust_score > 0))

    # S3.4: Training dimension grows with witnesses
    checks.append(("s3_training_grows", fed.nodes["charlie"].t3.training > 0.3))

    # S3.5: Self-witness rejected
    checks.append(("s3_no_self_witness", not fed.witness("alice", "alice", now + 13)))

    # S3.6: Build full trust mesh
    names = ["alice", "bob", "charlie", "dave", "eve", "frank"]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            fed.witness(a, b, now + 20 + i, quality=0.6)
    checks.append(("s3_trust_mesh", len(fed.trust_edges) > 10))

    # ── S4: ATP Transfer ─────────────────────────────────────────────────

    # S4.1: Successful transfer
    alice_before = fed.nodes["alice"].wallet.balance
    success, fee = fed.transfer_atp("alice", "bob", 100, now + 30)
    checks.append(("s4_transfer_success", success and fee > 0))

    # S4.2: Fee deducted
    checks.append(("s4_fee_pool", fed.fee_pool > 0))

    # S4.3: Balance reduced by amount + fee
    alice_after = fed.nodes["alice"].wallet.balance
    checks.append(("s4_balance_reduced", alice_after < alice_before - 100))

    # S4.4: Receiver gets net amount
    checks.append(("s4_receiver_gets", fed.nodes["bob"].wallet.balance > 100))

    # S4.5: Transfer to suspended fails
    fed.suspend_node("frank", now + 31)
    success, _ = fed.transfer_atp("alice", "frank", 10, now + 32)
    checks.append(("s4_suspended_fails", not success))

    # S4.6: Insufficient balance fails
    success, _ = fed.transfer_atp("alice", "bob", 999999, now + 33)
    checks.append(("s4_insufficient_fails", not success))

    # ── S5: Consensus ────────────────────────────────────────────────────

    # Reactivate frank for consensus
    fed.reactivate_node("frank", now + 34)

    # S5.1: Consensus with 6 active nodes
    success, status = fed.run_consensus("update_trust_params", now + 40)
    checks.append(("s5_consensus_success", success and status == "finalized"))

    # S5.2: Consensus round increments
    checks.append(("s5_round_incremented", fed.consensus_round == 1))

    # S5.3: Multiple rounds
    fed.run_consensus("schema_upgrade", now + 41)
    checks.append(("s5_multi_round", fed.consensus_round == 2))

    # S5.4: Insufficient nodes fails (need >= 4)
    small_fed = Federation("small")
    for name in ["x", "y", "z"]:
        small_fed.bootstrap_node(name, now)
        small_fed.activate_node(name, now + 1)
    success, _ = small_fed.run_consensus("test", now + 2)
    checks.append(("s5_insufficient_nodes", not success))

    # ── S6: Key Rotation ─────────────────────────────────────────────────

    # S6.1: Rotate key
    old_key = fed.nodes["alice"].public_key
    success = fed.rotate_key("alice", now + 50)
    checks.append(("s6_rotate", success and fed.nodes["alice"].public_key != old_key))

    # S6.2: Key version increments
    checks.append(("s6_version", fed.nodes["alice"].key_version == 1))

    # S6.3: Multiple rotations
    fed.rotate_key("alice", now + 51)
    checks.append(("s6_multi_rotate", fed.nodes["alice"].key_version == 2))

    # S6.4: Cannot rotate suspended node's key
    fed.suspend_node("eve", now + 52)
    checks.append(("s6_suspended_no_rotate", not fed.rotate_key("eve", now + 53)))

    # ── S7: Compromise and Revocation ────────────────────────────────────

    fed.reactivate_node("eve", now + 54)

    # S7.1: Low trust triggers compromise detection
    fed.nodes["eve"].trust_score = 0.1
    checks.append(("s7_compromise_detected", fed.detect_compromise("eve")))

    # S7.2: Normal trust doesn't trigger
    checks.append(("s7_normal_no_compromise", not fed.detect_compromise("alice")))

    # S7.3: Revocation changes state
    # Create a node only witnessed by eve
    fed.bootstrap_node("orphan", now + 55)
    fed.activate_node("orphan", now + 56)
    fed.witness("eve", "orphan", now + 57, quality=0.5)
    fed.nodes["orphan"].witnessed_by = {"eve"}  # Only eve witnesses

    revoked = fed.cascade_revocation("eve", now + 60)
    checks.append(("s7_cascade", "eve" in revoked and "orphan" in revoked))

    # S7.4: Revoked node removed from trust edges
    eve_edges = [k for k in fed.trust_edges if "eve" in k]
    checks.append(("s7_edges_removed", len(eve_edges) == 0))

    # S7.5: Cannot revoke already revoked
    checks.append(("s7_double_revoke", not fed.revoke_node("eve", now + 61)))

    # ── S8: Partition and Recovery ───────────────────────────────────────

    group_a = {"alice", "bob"}
    group_b = {"charlie", "dave"}
    edges_before = len(fed.trust_edges)

    # S8.1: Partition removes cross-group edges
    partition_data = fed.simulate_partition(group_a, group_b, now + 70)
    checks.append(("s8_partition", partition_data["removed_edges"] > 0))

    # S8.2: Edges reduced
    checks.append(("s8_edges_reduced", len(fed.trust_edges) < edges_before))

    # S8.3: Heal restores edges with decay
    fed.heal_partition(partition_data, now + 80)
    for (src, tgt), trust in partition_data["edges"]:
        if (src, tgt) in fed.trust_edges:
            # Restored at 80% of original
            checks.append(("s8_heal_decayed", fed.trust_edges[(src, tgt)] < trust))
            break

    # ── S9: Cross-Federation Bridge ──────────────────────────────────────

    fed2 = Federation("partner_fed")
    fed2.bootstrap_node("gateway2", now + 90)
    fed2.activate_node("gateway2", now + 91)

    # S9.1: Create bridge
    bridge_trust = fed.create_bridge(fed2, ("alice", "gateway2"), now + 92)
    checks.append(("s9_bridge", bridge_trust > 0))

    # S9.2: Bridge trust bounded by min of both nodes
    checks.append(("s9_bridge_bounded", bridge_trust <= 1.0))

    # S9.3: Bridge with revoked node fails
    bridge_trust2 = fed.create_bridge(fed2, ("eve", "gateway2"), now + 93)
    checks.append(("s9_revoked_no_bridge", bridge_trust2 == 0.0))

    # ── S10: Full Lifecycle ──────────────────────────────────────────────

    # S10.1: NASCENT → ACTIVE → SUSPENDED → ACTIVE → REVOKED
    fed.bootstrap_node("lifecycle", now + 100)
    checks.append(("s10_nascent", fed.nodes["lifecycle"].state == EntityState.NASCENT))

    fed.activate_node("lifecycle", now + 101)
    checks.append(("s10_active", fed.nodes["lifecycle"].state == EntityState.ACTIVE))

    fed.suspend_node("lifecycle", now + 102)
    checks.append(("s10_suspended", fed.nodes["lifecycle"].state == EntityState.SUSPENDED))

    fed.reactivate_node("lifecycle", now + 103)
    checks.append(("s10_reactivated", fed.nodes["lifecycle"].state == EntityState.ACTIVE))

    fed.revoke_node("lifecycle", now + 104)
    checks.append(("s10_revoked", fed.nodes["lifecycle"].state == EntityState.REVOKED))

    # S10.2: Cannot reactivate from REVOKED
    checks.append(("s10_revoked_terminal", not fed.reactivate_node("lifecycle", now + 105)))

    # S10.3: Event log completeness
    checks.append(("s10_events_logged", fed.event_count() > 20))

    # S10.4: Specific event types logged
    checks.append(("s10_bootstrap_events", fed.event_count("bootstrap") >= 7))
    checks.append(("s10_witness_events", fed.event_count("witness") > 5))
    checks.append(("s10_transfer_events", fed.event_count("transfer") >= 1))

    # S10.5: ATP conservation (ignoring revoked nodes — they keep their ATP)
    # total_received includes both minted deposits AND transfers in; subtract total_sent to get minted
    total_in_system = sum(n.wallet.balance for n in fed.nodes.values()) + fed.fee_pool
    total_minted = sum(n.wallet.total_received - n.wallet.total_sent for n in fed.nodes.values())
    checks.append(("s10_atp_conservation", abs(total_in_system - total_minted) < 0.001))

    # ── S11: Performance ─────────────────────────────────────────────────

    import random
    rng = random.Random(42)

    # S11.1: 100-node federation
    t0 = time.time()
    big_fed = Federation("big", initial_atp=100000.0)
    for i in range(100):
        big_fed.bootstrap_node(f"n{i}", now)
        big_fed.activate_node(f"n{i}", now + 1)
    elapsed = time.time() - t0
    checks.append(("s11_100_bootstrap", big_fed.active_count() == 100 and elapsed < 2.0))

    # S11.2: Build trust mesh (each node witnesses 5 random peers)
    t0 = time.time()
    for i in range(100):
        peers = rng.sample(range(100), min(5, 99))
        for j in peers:
            if i != j:
                big_fed.witness(f"n{i}", f"n{j}", now + 10, quality=rng.uniform(0.5, 0.9))
    elapsed = time.time() - t0
    checks.append(("s11_trust_mesh", len(big_fed.trust_edges) > 400 and elapsed < 2.0))

    # S11.3: 500 ATP transfers
    t0 = time.time()
    transfers_ok = 0
    for i in range(500):
        s = f"n{rng.randint(0, 99)}"
        r = f"n{rng.randint(0, 99)}"
        if s != r:
            ok, _ = big_fed.transfer_atp(s, r, rng.uniform(1, 10), now + 20 + i)
            if ok:
                transfers_ok += 1
    elapsed = time.time() - t0
    checks.append(("s11_500_transfers", transfers_ok > 100 and elapsed < 2.0))

    # S11.4: Consensus at scale
    t0 = time.time()
    for i in range(10):
        big_fed.run_consensus(f"round_{i}", now + 100 + i)
    elapsed = time.time() - t0
    checks.append(("s11_10_consensus", big_fed.consensus_round == 10 and elapsed < 1.0))

    # S11.5: Mass key rotation
    t0 = time.time()
    for i in range(100):
        big_fed.rotate_key(f"n{i}", now + 200)
    elapsed = time.time() - t0
    checks.append(("s11_100_rotations", elapsed < 1.0))

    # S11.6: Event log size
    checks.append(("s11_event_count", big_fed.event_count() > 1000))

    # ── Print Results ────────────────────────────────────────────────────
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print(f"\n{'='*60}")
    print(f"  E2E Federation Scenario — {passed}/{total} checks passed")
    print(f"{'='*60}")

    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    if passed < total:
        print(f"\n  FAILURES:")
        for name, ok in checks:
            if not ok:
                print(f"    ✗ {name}")

    print()
    return passed, total


if __name__ == "__main__":
    run_checks()
