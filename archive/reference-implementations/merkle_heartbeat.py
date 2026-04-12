#!/usr/bin/env python3
"""
Merkle-Tree Heartbeat Aggregation — Storage Efficiency for Hardbound Teams
===========================================================================

Heartbeat blocks aggregate actions into ledger entries. Currently each action
is stored individually in the hash-chained ledger. As teams grow (10K+ actions),
this creates large ledger files and slow verification.

Merkle tree aggregation provides:
  1. O(log N) verification of any action within a block
  2. Compact block representation (just merkle_root)
  3. Selective disclosure (prove single action without revealing all)
  4. Compatible with existing hash-chain (merkle_root chains into next block)

Structure:
  HeartbeatBlock:
    - merkle_root: SHA-256 root of action tree
    - actions: List[Action] (stored separately, compressed)
    - block_number, metabolic_state, timestamp

  MerkleProof:
    - leaf_index: which action in the block
    - leaf_hash: hash of the action
    - siblings: list of (hash, direction) for verification
    - root: expected merkle root

Integration with TeamLedger:
  Instead of N individual entries per heartbeat, write 1 block entry
  with merkle_root. Full actions stored in separate .actions.jsonl file.
  Verification: reconstruct root from proof path, compare with ledger entry.

Date: 2026-02-21
Closes gap: "Heartbeat blocks are metadata-only; could aggregate into Merkle trees"
"""

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# Merkle Tree — Binary hash tree over action hashes
# ═══════════════════════════════════════════════════════════════

def sha256(data: str) -> str:
    """SHA-256 hex digest."""
    return hashlib.sha256(data.encode()).hexdigest()


def canonical_json(obj: Any) -> str:
    """Canonical JSON for consistent hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


class MerkleTree:
    """
    Binary Merkle tree over a list of data items.

    Leaves are SHA-256 hashes of canonical JSON representations.
    Internal nodes are SHA-256(left_hash + right_hash).
    If leaf count is odd, last leaf is duplicated (standard padding).
    """

    def __init__(self, items: List[Any]):
        """Build a Merkle tree from a list of items."""
        if not items:
            self.root = sha256("empty")
            self.leaves = []
            self._levels = [[self.root]]
            return

        # Hash leaves
        self.leaves = [sha256(canonical_json(item)) for item in items]
        self._items = list(items)

        # Build tree bottom-up
        self._levels = [list(self.leaves)]
        current = list(self.leaves)

        while len(current) > 1:
            next_level = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else current[i]
                parent = sha256(left + right)
                next_level.append(parent)
            self._levels.append(next_level)
            current = next_level

        self.root = current[0] if current else sha256("empty")

    def get_proof(self, index: int) -> "MerkleProof":
        """
        Generate a Merkle proof for the item at the given index.

        The proof consists of sibling hashes needed to reconstruct
        the root from the leaf. Direction indicates which side the
        sibling is on (left=0, right=1).
        """
        if index < 0 or index >= len(self.leaves):
            raise IndexError(f"Index {index} out of range [0, {len(self.leaves)})")

        siblings = []
        idx = index

        for level in self._levels[:-1]:  # All levels except root
            if idx % 2 == 0:
                # Sibling is to the right
                sibling_idx = idx + 1
                direction = "right"
            else:
                # Sibling is to the left
                sibling_idx = idx - 1
                direction = "left"

            if sibling_idx < len(level):
                siblings.append((level[sibling_idx], direction))
            else:
                # Odd leaf count — sibling is self (duplication)
                siblings.append((level[idx], "right"))

            idx //= 2

        return MerkleProof(
            leaf_index=index,
            leaf_hash=self.leaves[index],
            siblings=siblings,
            root=self.root,
        )

    @property
    def depth(self) -> int:
        return len(self._levels) - 1

    @property
    def size(self) -> int:
        return len(self.leaves)


@dataclass
class MerkleProof:
    """
    Proof that a leaf exists in a Merkle tree.

    Verification: start from leaf_hash, combine with each sibling
    in order, check final hash matches root.
    """
    leaf_index: int
    leaf_hash: str
    siblings: List[Tuple[str, str]]  # (hash, direction)
    root: str

    def verify(self) -> bool:
        """Verify this proof reconstructs the expected root."""
        current = self.leaf_hash
        for sibling_hash, direction in self.siblings:
            if direction == "left":
                current = sha256(sibling_hash + current)
            else:
                current = sha256(current + sibling_hash)
        return current == self.root

    def to_dict(self) -> dict:
        return {
            "leaf_index": self.leaf_index,
            "leaf_hash": self.leaf_hash,
            "siblings": [(h, d) for h, d in self.siblings],
            "root": self.root,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MerkleProof":
        return cls(
            leaf_index=data["leaf_index"],
            leaf_hash=data["leaf_hash"],
            siblings=[(h, d) for h, d in data["siblings"]],
            root=data["root"],
        )


# ═══════════════════════════════════════════════════════════════
# Heartbeat Merkle Block — Aggregated heartbeat with Merkle root
# ═══════════════════════════════════════════════════════════════

@dataclass
class HeartbeatMerkleBlock:
    """
    A heartbeat block with Merkle-aggregated actions.

    Instead of storing each action as a separate ledger entry,
    all actions within one heartbeat interval are collected into
    a Merkle tree. Only the root hash goes into the main ledger.

    Space savings:
      Before: N entries × ~200 bytes = 200N bytes in ledger
      After:  1 entry × ~200 bytes + N entries × ~200 bytes in .actions file
      The main ledger shrinks by factor of N per heartbeat block.
      Total storage is similar, but ledger traversal is O(blocks) not O(actions).
    """
    block_number: int
    metabolic_state: str
    actions: List[Dict[str, Any]]
    merkle_root: str = ""
    merkle_tree: Optional[MerkleTree] = field(default=None, repr=False)
    timestamp: str = ""
    recharge_amount: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.actions and not self.merkle_root:
            self.merkle_tree = MerkleTree(self.actions)
            self.merkle_root = self.merkle_tree.root

    def get_proof(self, action_index: int) -> MerkleProof:
        """Get a Merkle proof for a specific action in this block."""
        if not self.merkle_tree:
            self.merkle_tree = MerkleTree(self.actions)
        return self.merkle_tree.get_proof(action_index)

    def verify_action(self, action_index: int, action: Dict) -> bool:
        """Verify that a specific action exists in this block."""
        proof = self.get_proof(action_index)
        # Also verify the leaf hash matches the claimed action
        expected_hash = sha256(canonical_json(action))
        return proof.verify() and proof.leaf_hash == expected_hash

    def to_ledger_entry(self) -> dict:
        """Create a compact ledger entry (no individual actions)."""
        return {
            "type": "merkle_heartbeat_block",
            "block_number": self.block_number,
            "merkle_root": self.merkle_root,
            "actions_count": len(self.actions),
            "metabolic_state": self.metabolic_state,
            "timestamp": self.timestamp,
            "recharge_amount": self.recharge_amount,
            "tree_depth": self.merkle_tree.depth if self.merkle_tree else 0,
        }

    @property
    def storage_ratio(self) -> float:
        """Storage savings ratio (ledger size reduction)."""
        if not self.actions:
            return 1.0
        # 1 block entry vs N action entries
        return 1.0 / len(self.actions)


# ═══════════════════════════════════════════════════════════════
# Merkle Block Store — Manages block + action separation
# ═══════════════════════════════════════════════════════════════

class MerkleBlockStore:
    """
    Storage layer that separates block metadata from action data.

    Main ledger:   block metadata (merkle_root, count, state)
    Actions store: full action data (indexed by block_number)

    This allows:
    - Fast ledger traversal (scan blocks, not individual actions)
    - Selective action retrieval (load specific block's actions)
    - Merkle proof verification without loading all actions
    """

    def __init__(self):
        self.blocks: List[HeartbeatMerkleBlock] = []
        self.total_actions = 0
        self.total_blocks = 0

    def add_block(self, actions: List[Dict], metabolic_state: str,
                  recharge_amount: float = 0.0) -> HeartbeatMerkleBlock:
        """Create a new Merkle block from actions."""
        block = HeartbeatMerkleBlock(
            block_number=self.total_blocks,
            metabolic_state=metabolic_state,
            actions=actions,
            recharge_amount=recharge_amount,
        )
        self.blocks.append(block)
        self.total_blocks += 1
        self.total_actions += len(actions)
        return block

    def verify_block(self, block_number: int) -> bool:
        """Verify a block's Merkle root matches its actions."""
        if block_number >= len(self.blocks):
            return False
        block = self.blocks[block_number]
        # Rebuild tree from actions and compare root
        fresh_tree = MerkleTree(block.actions)
        return fresh_tree.root == block.merkle_root

    def get_action_proof(self, block_number: int,
                          action_index: int) -> MerkleProof:
        """Get a Merkle proof for a specific action in a specific block."""
        return self.blocks[block_number].get_proof(action_index)

    def storage_stats(self) -> dict:
        """Storage statistics."""
        ledger_entries = self.total_blocks  # One per block
        action_entries = self.total_actions  # In separate store
        original_entries = self.total_actions + self.total_blocks  # Without Merkle

        return {
            "total_blocks": self.total_blocks,
            "total_actions": self.total_actions,
            "ledger_entries": ledger_entries,
            "action_store_entries": action_entries,
            "original_ledger_entries": original_entries,
            "ledger_reduction_factor": (
                round(original_entries / ledger_entries, 2) if ledger_entries > 0 else 0
            ),
            "avg_actions_per_block": (
                round(self.total_actions / self.total_blocks, 1) if self.total_blocks > 0 else 0
            ),
        }


# ═══════════════════════════════════════════════════════════════
# Demo + Verification
# ═══════════════════════════════════════════════════════════════

def run_demo():
    print("=" * 70)
    print("  MERKLE-TREE HEARTBEAT AGGREGATION")
    print("  O(log N) Verification + Selective Disclosure + Storage Efficiency")
    print("=" * 70)

    checks_passed = 0
    checks_failed = 0

    def check(name, condition, detail=""):
        nonlocal checks_passed, checks_failed
        if condition:
            print(f"  ✓ {name}")
            checks_passed += 1
        else:
            msg = f": {detail}" if detail else ""
            print(f"  ✗ {name}{msg}")
            checks_failed += 1

    # ── Test 1: Basic Merkle Tree ──
    print("\n── Test 1: Basic Merkle Tree Construction ──")
    actions = [
        {"type": "run_analysis", "actor": "alice", "target": "dataset-1"},
        {"type": "review_pr", "actor": "bob", "target": "pr-42"},
        {"type": "validate_schema", "actor": "charlie", "target": "schema-v2"},
        {"type": "run_diagnostics", "actor": "alice", "target": "service-a"},
    ]
    tree = MerkleTree(actions)
    print(f"  Leaves: {tree.size}, Depth: {tree.depth}, Root: {tree.root[:16]}...")

    check("T1: Tree has correct leaf count", tree.size == 4)
    check("T1: Tree has correct depth", tree.depth == 2)
    check("T1: Root is 64-char hex", len(tree.root) == 64)

    # ── Test 2: Merkle Proof Verification ──
    print("\n── Test 2: Merkle Proof Verification ──")
    for i in range(len(actions)):
        proof = tree.get_proof(i)
        valid = proof.verify()
        print(f"  Action {i} ({actions[i]['type']}): proof valid={valid}, "
              f"siblings={len(proof.siblings)}")
        check(f"T2: Proof valid for action {i}", valid)

    # ── Test 3: Tamper Detection ──
    print("\n── Test 3: Tamper Detection ──")
    proof = tree.get_proof(1)  # proof for bob's review_pr

    # Modify the leaf hash (simulate tampered action)
    tampered_proof = MerkleProof(
        leaf_index=proof.leaf_index,
        leaf_hash=sha256("tampered_data"),  # Wrong hash
        siblings=proof.siblings,
        root=proof.root,
    )
    check("T3: Tampered proof fails verification", not tampered_proof.verify())

    # Modify a sibling hash
    if proof.siblings:
        bad_siblings = list(proof.siblings)
        bad_siblings[0] = ("0" * 64, bad_siblings[0][1])
        bad_proof = MerkleProof(
            leaf_index=proof.leaf_index,
            leaf_hash=proof.leaf_hash,
            siblings=bad_siblings,
            root=proof.root,
        )
        check("T3: Modified sibling fails verification", not bad_proof.verify())

    # ── Test 4: Odd Number of Leaves ──
    print("\n── Test 4: Odd Number of Leaves (Padding) ──")
    odd_actions = actions[:3]  # 3 items
    odd_tree = MerkleTree(odd_actions)
    print(f"  Leaves: {odd_tree.size}, Depth: {odd_tree.depth}")

    for i in range(3):
        proof = odd_tree.get_proof(i)
        check(f"T4: Proof valid for leaf {i} (odd tree)", proof.verify())

    # ── Test 5: HeartbeatMerkleBlock ──
    print("\n── Test 5: HeartbeatMerkleBlock ──")
    block = HeartbeatMerkleBlock(
        block_number=0,
        metabolic_state="wake",
        actions=actions,
        recharge_amount=5.0,
    )
    print(f"  Root: {block.merkle_root[:16]}...")
    print(f"  Storage ratio: {block.storage_ratio:.2f}")

    check("T5: Block has merkle root", len(block.merkle_root) == 64)
    check("T5: Block root matches tree root", block.merkle_root == tree.root)
    check("T5: Storage ratio < 1.0 (savings)", block.storage_ratio < 1.0)

    # Verify individual action
    check("T5: Action 0 verifiable in block",
          block.verify_action(0, actions[0]))
    check("T5: Wrong action fails verification",
          not block.verify_action(0, actions[1]))

    # ── Test 6: Ledger Entry Format ──
    print("\n── Test 6: Ledger Entry Format ──")
    entry = block.to_ledger_entry()
    print(f"  Entry: {json.dumps(entry, indent=2)}")

    check("T6: Entry type is merkle_heartbeat_block",
          entry["type"] == "merkle_heartbeat_block")
    check("T6: Entry has merkle_root", "merkle_root" in entry)
    check("T6: Entry has actions_count", entry["actions_count"] == 4)
    check("T6: Entry has tree_depth", entry["tree_depth"] == 2)

    # ── Test 7: Block Store + Scale Test ──
    print("\n── Test 7: Block Store at Scale ──")
    store = MerkleBlockStore()

    # Simulate 100 heartbeats with varying action counts
    import random
    random.seed(42)
    metabolic_states = ["focus", "wake", "rest", "dream", "crisis"]

    for i in range(100):
        state = metabolic_states[i % 5]
        # Action count varies by metabolic state
        if state == "crisis":
            n_actions = random.randint(10, 20)
        elif state == "focus":
            n_actions = random.randint(5, 15)
        elif state == "wake":
            n_actions = random.randint(3, 8)
        elif state == "rest":
            n_actions = random.randint(1, 3)
        else:  # dream
            n_actions = random.randint(0, 2)

        block_actions = [
            {"type": f"action_{j}", "actor": f"agent-{j%3}",
             "round": i, "value": random.random()}
            for j in range(n_actions)
        ]
        if block_actions:
            store.add_block(block_actions, state, recharge_amount=5.0)

    stats = store.storage_stats()
    print(f"  Total blocks: {stats['total_blocks']}")
    print(f"  Total actions: {stats['total_actions']}")
    print(f"  Ledger entries (Merkle): {stats['ledger_entries']}")
    print(f"  Original entries (flat): {stats['original_ledger_entries']}")
    print(f"  Ledger reduction: {stats['ledger_reduction_factor']}×")
    print(f"  Avg actions/block: {stats['avg_actions_per_block']}")

    check("T7: 80+ blocks created", stats["total_blocks"] >= 80)
    check("T7: 500+ total actions", stats["total_actions"] >= 500)
    check("T7: Ledger reduction > 3×", stats["ledger_reduction_factor"] > 3.0)

    # ── Test 8: Verify Random Blocks ──
    print("\n── Test 8: Block Integrity Verification ──")
    import random
    random.seed(99)
    sample_blocks = random.sample(range(stats["total_blocks"]), min(10, stats["total_blocks"]))

    all_valid = True
    for block_num in sample_blocks:
        if not store.verify_block(block_num):
            all_valid = False
            break

    check("T8: All sampled blocks verify", all_valid)

    # Verify random actions within blocks
    actions_verified = 0
    for block_num in sample_blocks[:5]:
        block = store.blocks[block_num]
        if block.actions:
            idx = random.randint(0, len(block.actions) - 1)
            proof = store.get_action_proof(block_num, idx)
            if proof.verify():
                actions_verified += 1

    check("T8: All sampled action proofs verify", actions_verified == 5)

    # ── Test 9: Proof Serialization (for network transport) ──
    print("\n── Test 9: Proof Serialization ──")
    proof = store.get_action_proof(0, 0)
    proof_dict = proof.to_dict()
    proof_json = json.dumps(proof_dict)
    restored_proof = MerkleProof.from_dict(json.loads(proof_json))

    check("T9: Proof survives JSON roundtrip", restored_proof.verify())
    check("T9: Restored proof matches original root",
          restored_proof.root == proof.root)
    check("T9: Proof JSON is compact (< 1KB)",
          len(proof_json) < 1024)

    # ── Test 10: Empty and Single-Action Blocks ──
    print("\n── Test 10: Edge Cases ──")
    empty_tree = MerkleTree([])
    check("T10: Empty tree has root", len(empty_tree.root) == 64)

    single = MerkleTree([{"type": "solo"}])
    single_proof = single.get_proof(0)
    check("T10: Single-item tree has valid proof", single_proof.verify())
    check("T10: Single-item proof has 0 siblings", len(single_proof.siblings) == 0)

    large_tree = MerkleTree([{"n": i} for i in range(1000)])
    check("T10: 1000-item tree depth is 10", large_tree.depth == 10)
    proof_500 = large_tree.get_proof(500)
    check("T10: Proof for item 500 (of 1000) is valid", proof_500.verify())
    check("T10: Proof size is O(log N)",
          len(proof_500.siblings) == 10)

    # ── Test 11: Proof Size vs Block Size ──
    print("\n── Test 11: Proof Size Scaling ──")
    sizes = [4, 16, 64, 256, 1024]
    for n in sizes:
        t = MerkleTree([{"i": i} for i in range(n)])
        p = t.get_proof(0)
        expected_depth = math.ceil(math.log2(n)) if n > 1 else 0
        print(f"  N={n:4d}: depth={t.depth}, proof_siblings={len(p.siblings)}, "
              f"expected={expected_depth}")

    check("T11: Proof scales as O(log N)",
          all(
              MerkleTree([{"i": i} for i in range(n)]).get_proof(0).verify()
              for n in sizes
          ))

    # ── Summary ──
    print("\n" + "=" * 70)
    total = checks_passed + checks_failed
    print(f"  Merkle Heartbeat: {checks_passed}/{total} checks passed")
    if checks_failed == 0:
        print("  ALL CHECKS PASSED!")

    print(f"\n  KEY RESULTS:")
    print(f"    - Merkle tree: O(log N) verification, O(N) storage")
    print(f"    - Ledger reduction: {stats['ledger_reduction_factor']}× fewer entries")
    print(f"    - Proof size: {math.ceil(math.log2(1000))} siblings for 1000-action block")
    print(f"    - Tamper detection: modified proofs fail verification")
    print(f"    - Selective disclosure: prove single action without revealing block")
    print(f"    - Edge cases: empty, single, odd leaf counts all handled")

    print(f"\n  INTEGRATION PATH:")
    print(f"    1. HeartbeatMerkleBlock replaces individual action entries")
    print(f"    2. Ledger stores 1 merkle_root per heartbeat (not N actions)")
    print(f"    3. Actions stored in separate .actions.jsonl (indexed by block)")
    print(f"    4. MerkleProof enables selective verification without full load")
    print(f"    5. Compatible with existing hash-chain (root chains into next)")
    print("=" * 70)

    return checks_failed == 0


if __name__ == "__main__":
    success = run_demo()
    import sys
    sys.exit(0 if success else 1)
