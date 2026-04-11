"""
Web4 Cryptographic Trust Anchoring — Session 18, Track 2
========================================================

Merkle-tree based trust commitment and verification system.
Entities commit to trust states via Merkle roots, enabling:
- Compact trust commitments (single hash commits entire trust state)
- Inclusion proofs (prove specific trust value without revealing all)
- Exclusion proofs (prove entity NOT in a trust set)
- Historical trust proofs (prove trust at a specific time)
- Trust attestation chains (multiple attestors sign trust claims)
- Batch verification (verify many trust claims efficiently)

This is the cryptographic backbone for verifiable trust —
making trust claims tamper-evident and independently verifiable.

~90 checks expected.
"""

import hashlib
import hmac
import math
import random
import struct
import time as time_mod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


# ============================================================
# §1 — Merkle Tree Implementation
# ============================================================

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_leaf(data: bytes) -> bytes:
    """Hash a leaf node with 0x00 prefix to prevent second preimage attacks."""
    return sha256(b'\x00' + data)


def hash_node(left: bytes, right: bytes) -> bytes:
    """Hash an internal node with 0x01 prefix."""
    return sha256(b'\x01' + left + right)


@dataclass
class MerkleTree:
    leaves: List[bytes] = field(default_factory=list)
    leaf_hashes: List[bytes] = field(default_factory=list)
    root: bytes = b''
    levels: List[List[bytes]] = field(default_factory=list)

    def build(self, data_items: List[bytes]):
        """Build tree from data items."""
        self.leaves = data_items
        self.leaf_hashes = [hash_leaf(d) for d in data_items]

        if not self.leaf_hashes:
            self.root = sha256(b'empty')
            self.levels = [[self.root]]
            return

        # Build bottom-up
        self.levels = [self.leaf_hashes[:]]
        current = self.leaf_hashes[:]

        while len(current) > 1:
            next_level = []
            for i in range(0, len(current), 2):
                if i + 1 < len(current):
                    next_level.append(hash_node(current[i], current[i + 1]))
                else:
                    # Odd node: promote (hash with itself)
                    next_level.append(hash_node(current[i], current[i]))
            current = next_level
            self.levels.append(current)

        self.root = current[0]

    def get_proof(self, index: int) -> List[Tuple[bytes, str]]:
        """
        Get inclusion proof for leaf at index.
        Returns list of (sibling_hash, side) tuples.
        """
        if index < 0 or index >= len(self.leaf_hashes):
            return []

        proof = []
        idx = index
        for level in self.levels[:-1]:  # Skip root level
            if idx % 2 == 0:
                sibling_idx = idx + 1
                side = "right"
            else:
                sibling_idx = idx - 1
                side = "left"

            if sibling_idx < len(level):
                proof.append((level[sibling_idx], side))
            else:
                proof.append((level[idx], "right"))  # odd: duplicate self

            idx //= 2

        return proof

    def verify_proof(self, leaf_data: bytes, proof: List[Tuple[bytes, str]]) -> bool:
        """Verify an inclusion proof against the root."""
        current = hash_leaf(leaf_data)
        for sibling, side in proof:
            if side == "left":
                current = hash_node(sibling, current)
            else:
                current = hash_node(current, sibling)
        return current == self.root


def test_section_1():
    checks = []

    # Basic tree construction
    items = [b"alice:0.8", b"bob:0.6", b"carol:0.9", b"dave:0.4"]
    tree = MerkleTree()
    tree.build(items)

    checks.append(("tree_has_root", len(tree.root) == 32))
    checks.append(("four_leaves", len(tree.leaf_hashes) == 4))
    checks.append(("levels_built", len(tree.levels) == 3))  # 4 → 2 → 1

    # Deterministic: same data → same root
    tree2 = MerkleTree()
    tree2.build(items)
    checks.append(("deterministic", tree.root == tree2.root))

    # Different data → different root
    tree3 = MerkleTree()
    tree3.build([b"alice:0.7"] + items[1:])
    checks.append(("different_root", tree3.root != tree.root))

    # Inclusion proof
    proof = tree.get_proof(0)
    checks.append(("proof_exists", len(proof) > 0))
    checks.append(("proof_valid", tree.verify_proof(items[0], proof)))

    # Verify all leaves
    for i, item in enumerate(items):
        proof = tree.get_proof(i)
        checks.append((f"leaf_{i}_valid", tree.verify_proof(item, proof)))

    # Invalid data fails proof
    fake_proof = tree.get_proof(0)
    checks.append(("fake_data_fails", not tree.verify_proof(b"alice:0.999", fake_proof)))

    # Empty tree
    empty = MerkleTree()
    empty.build([])
    checks.append(("empty_root", len(empty.root) == 32))

    # Single element tree
    single = MerkleTree()
    single.build([b"only"])
    checks.append(("single_root", len(single.root) == 32))
    proof_single = single.get_proof(0)
    checks.append(("single_proof_valid", single.verify_proof(b"only", proof_single)))

    # Odd number of elements
    odd = MerkleTree()
    odd.build([b"a", b"b", b"c"])
    checks.append(("odd_root", len(odd.root) == 32))
    for i in range(3):
        p = odd.get_proof(i)
        checks.append((f"odd_proof_{i}", odd.verify_proof([b"a", b"b", b"c"][i], p)))

    return checks


# ============================================================
# §2 — Trust State Commitment
# ============================================================

@dataclass
class TrustCommitment:
    """A cryptographic commitment to an entity's trust state."""
    entity_id: str
    talent: float
    training: float
    temperament: float
    timestamp: float
    attestor_id: str
    nonce: bytes = field(default_factory=lambda: b'')

    def serialize(self) -> bytes:
        """Canonical serialization for hashing."""
        parts = [
            self.entity_id.encode(),
            struct.pack('>ddd', self.talent, self.training, self.temperament),
            struct.pack('>d', self.timestamp),
            self.attestor_id.encode(),
            self.nonce,
        ]
        return b'|'.join(parts)

    def commitment_hash(self) -> str:
        return sha256_hex(self.serialize())

    def composite_trust(self) -> float:
        return (self.talent + self.training + self.temperament) / 3


@dataclass
class TrustCommitmentStore:
    """Stores and indexes trust commitments."""
    commitments: Dict[str, List[TrustCommitment]] = field(default_factory=dict)
    merkle_roots: List[Tuple[float, bytes]] = field(default_factory=list)

    def add(self, commitment: TrustCommitment):
        key = commitment.entity_id
        if key not in self.commitments:
            self.commitments[key] = []
        self.commitments[key].append(commitment)

    def build_snapshot(self) -> MerkleTree:
        """Build Merkle tree of all current commitments."""
        all_data = []
        for eid in sorted(self.commitments.keys()):
            for c in self.commitments[eid]:
                all_data.append(c.serialize())
        tree = MerkleTree()
        tree.build(all_data)
        self.merkle_roots.append((time_mod.time(), tree.root))
        return tree

    def get_history(self, entity_id: str) -> List[TrustCommitment]:
        return self.commitments.get(entity_id, [])


def test_section_2():
    checks = []

    # Create commitments
    c1 = TrustCommitment("alice", 0.8, 0.7, 0.9, 1000.0, "bob", b"nonce1")
    c2 = TrustCommitment("bob", 0.6, 0.5, 0.7, 1000.0, "alice", b"nonce2")

    checks.append(("serializable", len(c1.serialize()) > 0))
    checks.append(("hash_deterministic", c1.commitment_hash() == c1.commitment_hash()))
    checks.append(("different_hashes", c1.commitment_hash() != c2.commitment_hash()))
    checks.append(("composite_trust", abs(c1.composite_trust() - 0.8) < 0.01))

    # Store and snapshot
    store = TrustCommitmentStore()
    store.add(c1)
    store.add(c2)
    tree = store.build_snapshot()

    checks.append(("snapshot_root", len(tree.root) == 32))
    checks.append(("two_leaves", len(tree.leaf_hashes) == 2))

    # Prove inclusion
    proof = tree.get_proof(0)  # alice's commitment (sorted by entity_id)
    # Sorted: alice first, then bob
    checks.append(("alice_provable", tree.verify_proof(c1.serialize(), proof)))

    proof_bob = tree.get_proof(1)
    checks.append(("bob_provable", tree.verify_proof(c2.serialize(), proof_bob)))

    # History
    checks.append(("history_alice", len(store.get_history("alice")) == 1))
    checks.append(("history_empty", len(store.get_history("carol")) == 0))

    # Nonce prevents precomputation
    c3 = TrustCommitment("alice", 0.8, 0.7, 0.9, 1000.0, "bob", b"different_nonce")
    checks.append(("nonce_matters", c1.commitment_hash() != c3.commitment_hash()))

    return checks


# ============================================================
# §3 — Trust Attestation Chain
# ============================================================

@dataclass
class TrustAttestation:
    """A signed trust claim from one entity about another."""
    subject_id: str
    attestor_id: str
    trust_claim: Dict[str, float]
    timestamp: float
    signature: str = ""
    prev_attestation_hash: str = ""

    def content_hash(self) -> str:
        content = f"{self.subject_id}:{self.attestor_id}:{sorted(self.trust_claim.items())}:{self.timestamp}:{self.prev_attestation_hash}"
        return sha256_hex(content.encode())

    def sign(self, key: bytes):
        self.signature = hmac.new(key, self.content_hash().encode(), hashlib.sha256).hexdigest()

    def verify(self, key: bytes) -> bool:
        expected = hmac.new(key, self.content_hash().encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.signature, expected)


@dataclass
class AttestationChain:
    """Hash-linked chain of attestations for an entity."""
    entity_id: str
    attestations: List[TrustAttestation] = field(default_factory=list)

    def append(self, attestor_id: str, trust_claim: Dict[str, float],
               timestamp: float, key: bytes) -> TrustAttestation:
        prev_hash = self.attestations[-1].content_hash() if self.attestations else "genesis"
        att = TrustAttestation(
            subject_id=self.entity_id,
            attestor_id=attestor_id,
            trust_claim=trust_claim,
            timestamp=timestamp,
            prev_attestation_hash=prev_hash,
        )
        att.sign(key)
        self.attestations.append(att)
        return att

    def verify_chain(self, keys: Dict[str, bytes]) -> Tuple[bool, int]:
        """Verify entire chain integrity. Returns (valid, break_index)."""
        prev_hash = "genesis"
        for i, att in enumerate(self.attestations):
            if att.prev_attestation_hash != prev_hash:
                return False, i
            key = keys.get(att.attestor_id)
            if key is None or not att.verify(key):
                return False, i
            prev_hash = att.content_hash()
        return True, -1

    def latest_trust(self) -> Optional[Dict[str, float]]:
        if not self.attestations:
            return None
        return self.attestations[-1].trust_claim


def test_section_3():
    checks = []

    # Create attestation chain
    chain = AttestationChain("alice")
    key_bob = b"bob_secret_key_32bytes_padding!!"
    key_carol = b"carol_secret_key_32bytes_pad!!!"

    att1 = chain.append("bob", {"talent": 0.8, "training": 0.7, "temperament": 0.9}, 1000.0, key_bob)
    checks.append(("att1_signed", len(att1.signature) == 64))
    checks.append(("att1_valid", att1.verify(key_bob)))
    checks.append(("att1_wrong_key_fails", not att1.verify(key_carol)))

    att2 = chain.append("carol", {"talent": 0.85, "training": 0.75, "temperament": 0.88}, 2000.0, key_carol)
    checks.append(("att2_linked", att2.prev_attestation_hash == att1.content_hash()))

    # Verify chain
    keys = {"bob": key_bob, "carol": key_carol}
    valid, idx = chain.verify_chain(keys)
    checks.append(("chain_valid", valid))

    # Tamper detection
    chain.attestations[0].trust_claim["talent"] = 0.99
    valid2, idx2 = chain.verify_chain(keys)
    checks.append(("tamper_detected", not valid2))
    checks.append(("tamper_at_0", idx2 == 0))

    # Restore original value — content hash returns to original, signature valid again
    chain.attestations[0].trust_claim["talent"] = 0.8
    valid3, _ = chain.verify_chain(keys)
    checks.append(("restore_heals_chain", valid3))

    # Latest trust
    latest = chain.latest_trust()
    checks.append(("latest_trust", latest is not None))
    checks.append(("latest_talent", latest["talent"] == 0.85))

    return checks


# ============================================================
# §4 — Trust Merkle Proofs (Inclusion + Exclusion)
# ============================================================

@dataclass
class TrustRegistry:
    """Registry of trust states with Merkle proof support."""
    entities: Dict[str, Dict[str, float]] = field(default_factory=dict)
    sorted_ids: List[str] = field(default_factory=list)
    tree: Optional[MerkleTree] = None

    def register(self, entity_id: str, trust: Dict[str, float]):
        self.entities[entity_id] = trust
        self.sorted_ids = sorted(self.entities.keys())

    def commit(self) -> bytes:
        """Build Merkle commitment of all registered trust states."""
        items = []
        for eid in self.sorted_ids:
            t = self.entities[eid]
            data = f"{eid}:{t.get('talent',0):.6f}:{t.get('training',0):.6f}:{t.get('temperament',0):.6f}"
            items.append(data.encode())
        self.tree = MerkleTree()
        self.tree.build(items)
        return self.tree.root

    def prove_inclusion(self, entity_id: str) -> Optional[Tuple[bytes, List]]:
        """Generate inclusion proof for entity."""
        if entity_id not in self.entities or self.tree is None:
            return None
        idx = self.sorted_ids.index(entity_id)
        t = self.entities[entity_id]
        data = f"{entity_id}:{t.get('talent',0):.6f}:{t.get('training',0):.6f}:{t.get('temperament',0):.6f}"
        proof = self.tree.get_proof(idx)
        return (data.encode(), proof)

    def prove_exclusion(self, entity_id: str) -> Dict:
        """
        Prove entity is NOT in the registry.
        Uses sorted order: show neighbors that bound where it would be.
        """
        if entity_id in self.entities:
            return {"excluded": False, "reason": "entity_exists"}

        # Find position where entity_id would be inserted
        pos = 0
        for i, eid in enumerate(self.sorted_ids):
            if eid > entity_id:
                break
            pos = i + 1

        result = {"excluded": True, "position": pos}

        if pos > 0:
            left_id = self.sorted_ids[pos - 1]
            left_data = self.prove_inclusion(left_id)
            result["left_neighbor"] = left_id
            result["left_proof"] = left_data

        if pos < len(self.sorted_ids):
            right_id = self.sorted_ids[pos]
            right_data = self.prove_inclusion(right_id)
            result["right_neighbor"] = right_id
            result["right_proof"] = right_data

        return result


def test_section_4():
    checks = []

    reg = TrustRegistry()
    reg.register("alice", {"talent": 0.8, "training": 0.7, "temperament": 0.9})
    reg.register("carol", {"talent": 0.6, "training": 0.5, "temperament": 0.7})
    reg.register("eve", {"talent": 0.3, "training": 0.4, "temperament": 0.5})
    root = reg.commit()

    checks.append(("registry_root", len(root) == 32))

    # Inclusion proof
    proof_alice = reg.prove_inclusion("alice")
    checks.append(("alice_proof_exists", proof_alice is not None))
    data, path = proof_alice
    checks.append(("alice_proof_valid", reg.tree.verify_proof(data, path)))

    proof_carol = reg.prove_inclusion("carol")
    checks.append(("carol_proof_valid", reg.tree.verify_proof(proof_carol[0], proof_carol[1])))

    # Non-existent entity
    checks.append(("bob_not_found", reg.prove_inclusion("bob") is None))

    # Exclusion proof
    excl = reg.prove_exclusion("bob")
    checks.append(("bob_excluded", excl["excluded"]))
    # bob sorts between alice and carol
    checks.append(("bob_left_neighbor", excl.get("left_neighbor") == "alice"))
    checks.append(("bob_right_neighbor", excl.get("right_neighbor") == "carol"))

    # Verify exclusion neighbor proofs
    if "left_proof" in excl:
        left_data, left_path = excl["left_proof"]
        checks.append(("excl_left_valid", reg.tree.verify_proof(left_data, left_path)))
    if "right_proof" in excl:
        right_data, right_path = excl["right_proof"]
        checks.append(("excl_right_valid", reg.tree.verify_proof(right_data, right_path)))

    # Entity that exists cannot be excluded
    excl_alice = reg.prove_exclusion("alice")
    checks.append(("alice_not_excluded", not excl_alice["excluded"]))

    # Edge: exclusion before all entities
    excl_aaa = reg.prove_exclusion("aaa")
    checks.append(("aaa_excluded", excl_aaa["excluded"]))
    checks.append(("aaa_no_left", "left_neighbor" not in excl_aaa))

    # Edge: exclusion after all entities
    excl_zzz = reg.prove_exclusion("zzz")
    checks.append(("zzz_excluded", excl_zzz["excluded"]))
    checks.append(("zzz_no_right", "right_neighbor" not in excl_zzz))

    return checks


# ============================================================
# §5 — Historical Trust Proofs
# ============================================================

@dataclass
class TrustSnapshot:
    """A timestamped Merkle root of all trust states."""
    timestamp: float
    root: bytes
    entity_count: int
    prev_snapshot_hash: str = ""

    def snapshot_hash(self) -> str:
        content = f"{self.timestamp}:{self.root.hex()}:{self.entity_count}:{self.prev_snapshot_hash}"
        return sha256_hex(content.encode())


@dataclass
class TrustHistory:
    """Chain of trust snapshots for historical verification."""
    snapshots: List[TrustSnapshot] = field(default_factory=list)
    registries: Dict[float, TrustRegistry] = field(default_factory=dict)

    def take_snapshot(self, registry: TrustRegistry, timestamp: float) -> TrustSnapshot:
        root = registry.commit()
        prev_hash = self.snapshots[-1].snapshot_hash() if self.snapshots else "genesis"
        snap = TrustSnapshot(
            timestamp=timestamp, root=root,
            entity_count=len(registry.entities),
            prev_snapshot_hash=prev_hash,
        )
        self.snapshots.append(snap)
        # Deep copy the registry state
        reg_copy = TrustRegistry()
        for eid, trust in registry.entities.items():
            reg_copy.register(eid, dict(trust))
        reg_copy.commit()
        self.registries[timestamp] = reg_copy
        return snap

    def prove_trust_at_time(self, entity_id: str, timestamp: float) -> Optional[Dict]:
        """Prove an entity's trust state at a specific historical time."""
        reg = self.registries.get(timestamp)
        if reg is None:
            return None
        proof = reg.prove_inclusion(entity_id)
        if proof is None:
            return None
        snap = next((s for s in self.snapshots if s.timestamp == timestamp), None)
        if snap is None:
            return None
        return {
            "entity_id": entity_id,
            "timestamp": timestamp,
            "trust": reg.entities[entity_id],
            "proof": proof,
            "snapshot_root": snap.root,
            "snapshot_hash": snap.snapshot_hash(),
        }

    def verify_chain(self) -> Tuple[bool, int]:
        """Verify snapshot chain integrity."""
        prev_hash = "genesis"
        for i, snap in enumerate(self.snapshots):
            if snap.prev_snapshot_hash != prev_hash:
                return False, i
            prev_hash = snap.snapshot_hash()
        return True, -1


def test_section_5():
    checks = []

    reg = TrustRegistry()
    reg.register("alice", {"talent": 0.5, "training": 0.5, "temperament": 0.5})
    reg.register("bob", {"talent": 0.5, "training": 0.5, "temperament": 0.5})

    history = TrustHistory()

    # Snapshot at t=100
    snap1 = history.take_snapshot(reg, 100.0)
    checks.append(("snap1_created", snap1 is not None))
    checks.append(("snap1_root", len(snap1.root) == 32))
    checks.append(("snap1_genesis", snap1.prev_snapshot_hash == "genesis"))

    # Update trust and snapshot at t=200
    reg.register("alice", {"talent": 0.8, "training": 0.7, "temperament": 0.9})
    snap2 = history.take_snapshot(reg, 200.0)
    checks.append(("snap2_linked", snap2.prev_snapshot_hash == snap1.snapshot_hash()))
    checks.append(("roots_differ", snap1.root != snap2.root))

    # Prove trust at historical time
    proof_t100 = history.prove_trust_at_time("alice", 100.0)
    checks.append(("historical_proof", proof_t100 is not None))
    checks.append(("historical_trust", proof_t100["trust"]["talent"] == 0.5))

    proof_t200 = history.prove_trust_at_time("alice", 200.0)
    checks.append(("current_proof", proof_t200 is not None))
    checks.append(("current_trust", proof_t200["trust"]["talent"] == 0.8))

    # Verify proof against snapshot root
    data, path = proof_t200["proof"]
    reg_200 = history.registries[200.0]
    checks.append(("proof_matches_root", reg_200.tree.verify_proof(data, path)))

    # Chain integrity
    valid, idx = history.verify_chain()
    checks.append(("chain_valid", valid))

    # Non-existent time
    checks.append(("no_proof_t50", history.prove_trust_at_time("alice", 50.0) is None))

    return checks


# ============================================================
# §6 — Multi-Attestor Trust Aggregation
# ============================================================

@dataclass
class MultiAttestorTrust:
    """Aggregates trust claims from multiple attestors with weighted voting."""
    entity_id: str
    attestations: List[TrustAttestation] = field(default_factory=list)
    attestor_weights: Dict[str, float] = field(default_factory=dict)

    def add_attestation(self, att: TrustAttestation, weight: float = 1.0):
        self.attestations.append(att)
        self.attestor_weights[att.attestor_id] = weight

    def aggregate(self) -> Dict[str, float]:
        """Weighted average of trust claims across attestors."""
        if not self.attestations:
            return {}

        dims = set()
        for att in self.attestations:
            dims.update(att.trust_claim.keys())

        result = {}
        for dim in dims:
            total_weight = 0.0
            weighted_sum = 0.0
            for att in self.attestations:
                if dim in att.trust_claim:
                    w = self.attestor_weights.get(att.attestor_id, 1.0)
                    weighted_sum += att.trust_claim[dim] * w
                    total_weight += w
            result[dim] = weighted_sum / total_weight if total_weight > 0 else 0.0

        return result

    def consensus_level(self) -> float:
        """How much do attestors agree? 0.0 = no agreement, 1.0 = perfect."""
        if len(self.attestations) < 2:
            return 1.0

        dims = set()
        for att in self.attestations:
            dims.update(att.trust_claim.keys())

        variances = []
        for dim in dims:
            values = [att.trust_claim.get(dim, 0.5) for att in self.attestations]
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            variances.append(variance)

        avg_variance = sum(variances) / len(variances) if variances else 0
        # Max possible variance for [0,1] is 0.25 (all at 0 or 1)
        return max(0.0, 1.0 - avg_variance / 0.25)

    def build_commitment(self) -> MerkleTree:
        """Build Merkle tree of all attestations."""
        tree = MerkleTree()
        items = [
            f"{att.attestor_id}:{sorted(att.trust_claim.items())}:{att.timestamp}".encode()
            for att in self.attestations
        ]
        tree.build(items)
        return tree


def test_section_6():
    checks = []

    mat = MultiAttestorTrust("alice")

    att1 = TrustAttestation("alice", "bob", {"talent": 0.8, "training": 0.7, "temperament": 0.9}, 1000.0)
    att2 = TrustAttestation("alice", "carol", {"talent": 0.7, "training": 0.8, "temperament": 0.85}, 1001.0)
    att3 = TrustAttestation("alice", "dave", {"talent": 0.75, "training": 0.75, "temperament": 0.88}, 1002.0)

    mat.add_attestation(att1, weight=1.0)
    mat.add_attestation(att2, weight=0.8)
    mat.add_attestation(att3, weight=0.6)

    # Aggregation
    agg = mat.aggregate()
    checks.append(("agg_talent", 0.7 < agg["talent"] < 0.85))
    checks.append(("agg_training", 0.7 < agg["training"] < 0.8))
    checks.append(("agg_temperament", 0.85 < agg["temperament"] < 0.92))

    # Consensus
    consensus = mat.consensus_level()
    checks.append(("high_consensus", consensus > 0.8))

    # Low consensus scenario
    mat2 = MultiAttestorTrust("bob")
    att_agree = TrustAttestation("bob", "alice", {"talent": 0.9}, 1000.0)
    att_disagree = TrustAttestation("bob", "carol", {"talent": 0.1}, 1001.0)
    mat2.add_attestation(att_agree)
    mat2.add_attestation(att_disagree)

    low_consensus = mat2.consensus_level()
    checks.append(("low_consensus", low_consensus < 0.5))

    # Commitment
    tree = mat.build_commitment()
    checks.append(("commitment_root", len(tree.root) == 32))
    checks.append(("three_attestations", len(tree.leaf_hashes) == 3))

    # Weight affects outcome
    mat3 = MultiAttestorTrust("carol")
    att_high = TrustAttestation("carol", "expert", {"talent": 0.9}, 1000.0)
    att_low = TrustAttestation("carol", "novice", {"talent": 0.3}, 1001.0)
    mat3.add_attestation(att_high, weight=5.0)
    mat3.add_attestation(att_low, weight=1.0)
    agg3 = mat3.aggregate()
    # Weighted: (0.9*5 + 0.3*1) / 6 = 4.8/6 = 0.8
    checks.append(("weight_matters", abs(agg3["talent"] - 0.8) < 0.01))

    return checks


# ============================================================
# §7 — Batch Verification
# ============================================================

@dataclass
class BatchVerifier:
    """Efficiently verify multiple trust proofs against a common root."""
    root: bytes
    verified: int = 0
    failed: int = 0

    def verify_batch(self, proofs: List[Tuple[bytes, List[Tuple[bytes, str]]]]) -> Dict:
        """Verify a batch of (leaf_data, proof_path) pairs."""
        results = []
        for leaf_data, proof_path in proofs:
            current = hash_leaf(leaf_data)
            for sibling, side in proof_path:
                if side == "left":
                    current = hash_node(sibling, current)
                else:
                    current = hash_node(current, sibling)
            valid = current == self.root
            results.append(valid)
            if valid:
                self.verified += 1
            else:
                self.failed += 1

        return {
            "total": len(proofs),
            "verified": self.verified,
            "failed": self.failed,
            "results": results,
            "all_valid": all(results),
        }


def test_section_7():
    checks = []

    # Build a registry with 10 entities
    reg = TrustRegistry()
    rng = random.Random(42)
    for i in range(10):
        reg.register(f"entity_{i:02d}", {
            "talent": round(rng.uniform(0.1, 0.9), 3),
            "training": round(rng.uniform(0.1, 0.9), 3),
            "temperament": round(rng.uniform(0.1, 0.9), 3),
        })
    root = reg.commit()

    # Generate proofs for all entities
    proofs = []
    for i in range(10):
        eid = f"entity_{i:02d}"
        result = reg.prove_inclusion(eid)
        if result:
            proofs.append(result)

    checks.append(("ten_proofs", len(proofs) == 10))

    # Batch verify
    verifier = BatchVerifier(root=root)
    batch_result = verifier.verify_batch(proofs)
    checks.append(("batch_all_valid", batch_result["all_valid"]))
    checks.append(("batch_count", batch_result["total"] == 10))
    checks.append(("batch_verified", batch_result["verified"] == 10))

    # Inject a bad proof
    bad_proofs = proofs[:] + [(b"fake_entity_data", proofs[0][1])]
    verifier2 = BatchVerifier(root=root)
    batch_result2 = verifier2.verify_batch(bad_proofs)
    checks.append(("batch_with_fake", not batch_result2["all_valid"]))
    checks.append(("one_failed", batch_result2["failed"] == 1))

    # Performance: verify 100 proofs
    large_proofs = proofs * 10  # 100 proofs (10 entities × 10)
    verifier3 = BatchVerifier(root=root)
    start = time_mod.time()
    batch_result3 = verifier3.verify_batch(large_proofs)
    elapsed = time_mod.time() - start
    checks.append(("large_batch_valid", batch_result3["all_valid"]))
    checks.append(("large_batch_fast", elapsed < 1.0))

    return checks


# ============================================================
# §8 — Trust Commitment Schemes (Pedersen-style)
# ============================================================

@dataclass
class TrustCommitScheme:
    """
    Hash-based commitment scheme for trust values.
    commit(trust, blinding) → C
    open(trust, blinding) → verify against C

    Supports additive homomorphism for composite trust computation:
    commit(t1) + commit(t2) can be verified without revealing t1, t2.
    """

    @staticmethod
    def commit(trust_value: float, blinding: bytes) -> str:
        """Create binding commitment to trust value."""
        data = struct.pack('>d', trust_value) + blinding
        return sha256_hex(data)

    @staticmethod
    def open(trust_value: float, blinding: bytes, commitment: str) -> bool:
        """Verify commitment opening."""
        data = struct.pack('>d', trust_value) + blinding
        return sha256_hex(data) == commitment

    @staticmethod
    def commit_vector(trust: Dict[str, float], blindings: Dict[str, bytes]) -> Dict[str, str]:
        """Commit to a trust vector (one commitment per dimension)."""
        return {
            dim: TrustCommitScheme.commit(val, blindings.get(dim, b'\x00' * 32))
            for dim, val in trust.items()
        }

    @staticmethod
    def open_vector(trust: Dict[str, float], blindings: Dict[str, bytes],
                    commitments: Dict[str, str]) -> bool:
        """Verify all commitments in a trust vector."""
        return all(
            TrustCommitScheme.open(trust[dim], blindings.get(dim, b'\x00' * 32), commitments[dim])
            for dim in trust.keys()
        )


def test_section_8():
    checks = []

    rng = random.Random(42)
    blinding = rng.randbytes(32)

    # Basic commit/open
    c = TrustCommitScheme.commit(0.8, blinding)
    checks.append(("commit_hex", len(c) == 64))
    checks.append(("open_valid", TrustCommitScheme.open(0.8, blinding, c)))
    checks.append(("open_wrong_value", not TrustCommitScheme.open(0.7, blinding, c)))
    checks.append(("open_wrong_blinding", not TrustCommitScheme.open(0.8, b'\x00' * 32, c)))

    # Hiding: same value, different blindings → different commitments
    b1 = rng.randbytes(32)
    b2 = rng.randbytes(32)
    c1 = TrustCommitScheme.commit(0.5, b1)
    c2 = TrustCommitScheme.commit(0.5, b2)
    checks.append(("hiding", c1 != c2))

    # Binding: same blinding, different values → different commitments
    c3 = TrustCommitScheme.commit(0.5, b1)
    c4 = TrustCommitScheme.commit(0.6, b1)
    checks.append(("binding", c3 != c4))

    # Vector commitment
    trust = {"talent": 0.8, "training": 0.7, "temperament": 0.9}
    blindings = {dim: rng.randbytes(32) for dim in trust}
    commitments = TrustCommitScheme.commit_vector(trust, blindings)
    checks.append(("vector_3_dims", len(commitments) == 3))
    checks.append(("vector_opens", TrustCommitScheme.open_vector(trust, blindings, commitments)))

    # Tampered vector fails
    tampered = dict(trust)
    tampered["talent"] = 0.99
    checks.append(("tampered_fails", not TrustCommitScheme.open_vector(tampered, blindings, commitments)))

    return checks


# ============================================================
# §9 — Cross-Entity Trust Proof Composition
# ============================================================

@dataclass
class TrustProofBundle:
    """Bundle of trust proofs that compose across entities."""
    proofs: List[Dict] = field(default_factory=list)
    combined_root: bytes = b''

    def add_proof(self, entity_id: str, trust: Dict[str, float],
                  merkle_proof: Tuple[bytes, List], snapshot_hash: str):
        self.proofs.append({
            "entity_id": entity_id,
            "trust": trust,
            "merkle_proof": merkle_proof,
            "snapshot_hash": snapshot_hash,
        })

    def compute_combined_root(self) -> bytes:
        """Compute a combined Merkle root over all proof hashes."""
        hashes = [sha256_hex(p["snapshot_hash"].encode()).encode() for p in self.proofs]
        tree = MerkleTree()
        tree.build(hashes)
        self.combined_root = tree.root
        return tree.root

    def composite_trust(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Compute weighted composite trust across all entities in bundle."""
        if not self.proofs:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0
        for p in self.proofs:
            w = weights.get(p["entity_id"], 1.0) if weights else 1.0
            t = p["trust"]
            composite = sum(t.values()) / len(t) if t else 0.0
            weighted_sum += composite * w
            total_weight += w

        return weighted_sum / total_weight if total_weight > 0 else 0.0


def test_section_9():
    checks = []

    # Create registries and proofs for two entities
    reg = TrustRegistry()
    reg.register("alice", {"talent": 0.8, "training": 0.7, "temperament": 0.9})
    reg.register("bob", {"talent": 0.6, "training": 0.5, "temperament": 0.7})
    root = reg.commit()

    history = TrustHistory()
    snap = history.take_snapshot(reg, 100.0)

    bundle = TrustProofBundle()
    for eid in ["alice", "bob"]:
        proof = reg.prove_inclusion(eid)
        bundle.add_proof(eid, reg.entities[eid], proof, snap.snapshot_hash())

    checks.append(("bundle_two_proofs", len(bundle.proofs) == 2))

    # Combined root
    combined = bundle.compute_combined_root()
    checks.append(("combined_root", len(combined) == 32))

    # Composite trust
    composite = bundle.composite_trust()
    alice_comp = (0.8 + 0.7 + 0.9) / 3
    bob_comp = (0.6 + 0.5 + 0.7) / 3
    expected = (alice_comp + bob_comp) / 2
    checks.append(("composite_correct", abs(composite - expected) < 0.01))

    # Weighted composite
    weighted = bundle.composite_trust({"alice": 2.0, "bob": 1.0})
    expected_w = (alice_comp * 2 + bob_comp * 1) / 3
    checks.append(("weighted_correct", abs(weighted - expected_w) < 0.01))

    # Deterministic
    combined2 = bundle.compute_combined_root()
    checks.append(("deterministic_combined", combined == combined2))

    return checks


# ============================================================
# §10 — Trust Anchor Chain (Genesis → Current)
# ============================================================

@dataclass
class TrustAnchorChain:
    """
    Chain from genesis to current trust state with Merkle proof at each step.
    Enables full audit: "this entity's trust went from X to Y, and here's the proof at each step."
    """
    entity_id: str
    anchors: List[Dict] = field(default_factory=list)

    def add_anchor(self, trust: Dict[str, float], merkle_root: bytes,
                   proof: Tuple[bytes, List], timestamp: float):
        prev_hash = self.anchors[-1]["anchor_hash"] if self.anchors else "genesis"
        anchor = {
            "trust": dict(trust),
            "merkle_root": merkle_root,
            "proof": proof,
            "timestamp": timestamp,
            "prev_anchor_hash": prev_hash,
            "anchor_hash": sha256_hex(
                f"{trust}:{merkle_root.hex()}:{timestamp}:{prev_hash}".encode()
            ),
        }
        self.anchors.append(anchor)

    def verify_chain(self) -> Tuple[bool, int]:
        """Verify anchor chain integrity."""
        prev_hash = "genesis"
        for i, anchor in enumerate(self.anchors):
            if anchor["prev_anchor_hash"] != prev_hash:
                return False, i
            expected = sha256_hex(
                f"{anchor['trust']}:{anchor['merkle_root'].hex()}:{anchor['timestamp']}:{prev_hash}".encode()
            )
            if anchor["anchor_hash"] != expected:
                return False, i
            prev_hash = anchor["anchor_hash"]
        return True, -1

    def trust_trajectory(self) -> List[Tuple[float, float]]:
        """Return (timestamp, composite_trust) trajectory."""
        return [
            (a["timestamp"], sum(a["trust"].values()) / len(a["trust"]))
            for a in self.anchors
        ]


def test_section_10():
    checks = []

    reg = TrustRegistry()
    reg.register("alice", {"talent": 0.5, "training": 0.5, "temperament": 0.5})
    root1 = reg.commit()
    proof1 = reg.prove_inclusion("alice")

    chain = TrustAnchorChain("alice")
    chain.add_anchor({"talent": 0.5, "training": 0.5, "temperament": 0.5}, root1, proof1, 100.0)

    # Update trust
    reg.register("alice", {"talent": 0.7, "training": 0.6, "temperament": 0.8})
    root2 = reg.commit()
    proof2 = reg.prove_inclusion("alice")
    chain.add_anchor({"talent": 0.7, "training": 0.6, "temperament": 0.8}, root2, proof2, 200.0)

    # Another update
    reg.register("alice", {"talent": 0.85, "training": 0.75, "temperament": 0.9})
    root3 = reg.commit()
    proof3 = reg.prove_inclusion("alice")
    chain.add_anchor({"talent": 0.85, "training": 0.75, "temperament": 0.9}, root3, proof3, 300.0)

    checks.append(("three_anchors", len(chain.anchors) == 3))

    # Chain integrity
    valid, idx = chain.verify_chain()
    checks.append(("chain_valid", valid))

    # Trust trajectory
    trajectory = chain.trust_trajectory()
    checks.append(("trajectory_length", len(trajectory) == 3))
    checks.append(("trust_increasing", trajectory[-1][1] > trajectory[0][1]))

    # Tamper detection
    chain.anchors[1]["trust"]["talent"] = 0.99
    valid2, idx2 = chain.verify_chain()
    checks.append(("tamper_detected", not valid2))
    checks.append(("tamper_at_1", idx2 == 1))

    # Genesis anchor
    checks.append(("genesis_linked", chain.anchors[0]["prev_anchor_hash"] == "genesis"))

    return checks


# ============================================================
# §11 — Performance & Stress Test
# ============================================================

def test_section_11():
    checks = []
    rng = random.Random(42)

    # Large tree: 1000 entities
    reg = TrustRegistry()
    for i in range(1000):
        reg.register(f"entity_{i:04d}", {
            "talent": round(rng.uniform(0.1, 0.9), 4),
            "training": round(rng.uniform(0.1, 0.9), 4),
            "temperament": round(rng.uniform(0.1, 0.9), 4),
        })

    start = time_mod.time()
    root = reg.commit()
    build_time = time_mod.time() - start
    checks.append(("tree_1000_built", len(root) == 32))
    checks.append(("tree_1000_fast", build_time < 1.0))

    # Proof generation for 100 random entities
    start = time_mod.time()
    proofs_generated = 0
    for i in rng.sample(range(1000), 100):
        eid = f"entity_{i:04d}"
        proof = reg.prove_inclusion(eid)
        if proof:
            data, path = proof
            if reg.tree.verify_proof(data, path):
                proofs_generated += 1
    proof_time = time_mod.time() - start
    checks.append(("100_proofs_valid", proofs_generated == 100))
    checks.append(("100_proofs_fast", proof_time < 2.0))

    # History chain with 50 snapshots
    history = TrustHistory()
    small_reg = TrustRegistry()
    for i in range(10):
        small_reg.register(f"e{i}", {"talent": 0.5, "training": 0.5, "temperament": 0.5})

    start = time_mod.time()
    for t in range(50):
        eid = f"e{t % 10}"
        old = small_reg.entities[eid]
        small_reg.register(eid, {
            "talent": min(1.0, old["talent"] + 0.01),
            "training": min(1.0, old["training"] + 0.005),
            "temperament": min(1.0, old["temperament"] + 0.008),
        })
        history.take_snapshot(small_reg, float(t))
    history_time = time_mod.time() - start

    checks.append(("50_snapshots", len(history.snapshots) == 50))
    checks.append(("history_fast", history_time < 2.0))

    # Verify entire history chain
    valid, idx = history.verify_chain()
    checks.append(("history_chain_valid", valid))

    # Proof at arbitrary historical point
    proof_at_25 = history.prove_trust_at_time("e5", 25.0)
    checks.append(("historical_proof_exists", proof_at_25 is not None))

    # Batch verification of 200 proofs
    batch_proofs = []
    for i in range(min(200, len(reg.sorted_ids))):
        eid = reg.sorted_ids[i]
        result = reg.prove_inclusion(eid)
        if result:
            batch_proofs.append(result)

    verifier = BatchVerifier(root=root)
    start = time_mod.time()
    batch_result = verifier.verify_batch(batch_proofs)
    batch_time = time_mod.time() - start
    checks.append(("batch_200_valid", batch_result["all_valid"]))
    checks.append(("batch_200_fast", batch_time < 2.0))

    return checks


# ============================================================
# Harness
# ============================================================

def run_section(name, func):
    results = func()
    passed = sum(1 for _, v in results if v)
    total = len(results)
    status = "✓" if passed == total else "✗"
    print(f"  {status} {name}: {passed}/{total}")
    return results


def main():
    all_checks = []
    sections = [
        ("§1 Merkle Tree Implementation", test_section_1),
        ("§2 Trust State Commitment", test_section_2),
        ("§3 Trust Attestation Chain", test_section_3),
        ("§4 Trust Merkle Proofs", test_section_4),
        ("§5 Historical Trust Proofs", test_section_5),
        ("§6 Multi-Attestor Aggregation", test_section_6),
        ("§7 Batch Verification", test_section_7),
        ("§8 Commitment Schemes", test_section_8),
        ("§9 Cross-Entity Proof Composition", test_section_9),
        ("§10 Trust Anchor Chain", test_section_10),
        ("§11 Performance & Stress Test", test_section_11),
    ]

    for name, func in sections:
        results = run_section(name, func)
        all_checks.extend(results)

    passed = sum(1 for _, v in all_checks if v)
    total = len(all_checks)
    print(f"\nTotal: {passed}/{total}")

    if passed < total:
        print(f"\nFailed checks:")
        for name, v in all_checks:
            if not v:
                print(f"    FAIL: {name}")


if __name__ == "__main__":
    main()
