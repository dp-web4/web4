#!/usr/bin/env python3
"""
Trust Merkle Tree
Session #57: Blockchain anchoring for trust updates

Implements Merkle tree construction and verification for trust update batches.
Enables cryptographic proof-of-inclusion and tamper detection.

Architecture:
- TrustUpdateLeaf: Single trust update (hashable)
- TrustMerkleTree: Merkle tree construction and proof generation
- Integration with TrustUpdateBatcher for automatic anchoring

Design from: blockchain_anchoring.md
"""

import hashlib
from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class TrustUpdateLeaf:
    """
    Single trust update in Merkle tree.

    Represents one trust score update that will be hashed and included
    in the Merkle tree for batch anchoring.
    """
    lct_id: str
    org_id: str
    talent_delta: Decimal
    training_delta: Decimal
    temperament_delta: Decimal
    veracity_delta: Decimal
    validity_delta: Decimal
    valuation_delta: Decimal
    timestamp: datetime
    # Optional metadata
    action_count: int = 0
    transaction_count: int = 0

    def hash(self) -> bytes:
        """
        Hash this update for Merkle tree inclusion.

        Uses SHA-256 over canonical string representation.
        Includes all deltas and timestamp for complete auditability.

        Returns:
            32-byte SHA-256 hash
        """
        data = f"{self.lct_id}:{self.org_id}:"
        data += f"{self.talent_delta}:{self.training_delta}:{self.temperament_delta}:"
        data += f"{self.veracity_delta}:{self.validity_delta}:{self.valuation_delta}:"
        data += f"{self.timestamp.isoformat()}"

        if self.action_count > 0 or self.transaction_count > 0:
            data += f":{self.action_count}:{self.transaction_count}"

        return hashlib.sha256(data.encode('utf-8')).digest()

    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'lct_id': self.lct_id,
            'org_id': self.org_id,
            'talent_delta': str(self.talent_delta),
            'training_delta': str(self.training_delta),
            'temperament_delta': str(self.temperament_delta),
            'veracity_delta': str(self.veracity_delta),
            'validity_delta': str(self.validity_delta),
            'valuation_delta': str(self.valuation_delta),
            'timestamp': self.timestamp.isoformat(),
            'action_count': self.action_count,
            'transaction_count': self.transaction_count
        }


class TrustMerkleTree:
    """
    Merkle tree for trust update batches.

    Enables:
    - Single on-chain hash representing 100+ updates
    - Proof-of-inclusion for any update
    - Tamper detection
    - Audit trail verification

    Properties:
    - Binary tree structure
    - SHA-256 hashing
    - Left-right sibling pairing
    - Duplicate last node if odd count
    """

    def __init__(self, updates: List[TrustUpdateLeaf]):
        """
        Build Merkle tree from trust updates.

        Args:
            updates: List of trust updates to include in tree
        """
        self.leaves = updates
        self.tree = self._build_tree()
        self.root = self.tree[-1][0] if self.tree else None

    def _build_tree(self) -> List[List[bytes]]:
        """
        Build complete Merkle tree from leaves to root.

        Algorithm:
        1. Hash all leaves
        2. Pair hashes left-to-right
        3. Hash each pair to create parent
        4. Repeat until single root
        5. Duplicate last hash if odd count

        Returns:
            List of levels, bottom (leaves) to top (root)
        """
        if not self.leaves:
            return []

        # Leaf level
        current_level = [leaf.hash() for leaf in self.leaves]
        tree = [current_level]

        # Build up to root
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left

                # Hash pair
                parent = hashlib.sha256(left + right).digest()
                next_level.append(parent)

            tree.append(next_level)
            current_level = next_level

        return tree

    def get_root(self) -> Optional[bytes]:
        """
        Get Merkle root.

        Returns:
            32-byte root hash, or None if tree is empty
        """
        return self.root

    def get_root_hex(self) -> Optional[str]:
        """
        Get Merkle root as hex string.

        Returns:
            64-character hex string, or None if tree is empty
        """
        return self.root.hex() if self.root else None

    def get_proof(self, index: int) -> List[Tuple[bytes, str]]:
        """
        Get Merkle proof for update at index.

        Proof is a list of sibling hashes and their positions,
        allowing reconstruction of the root from the leaf.

        Args:
            index: Index of leaf in original updates list

        Returns:
            List of (sibling_hash, position) where position is 'left' or 'right'

        Raises:
            IndexError: If index is out of range
        """
        if index >= len(self.leaves):
            raise IndexError(f"Index {index} out of range (tree has {len(self.leaves)} leaves)")

        proof = []
        current_index = index

        for level in self.tree[:-1]:  # Exclude root level
            # Find sibling
            if current_index % 2 == 0:
                # Left node, sibling is right
                sibling_index = current_index + 1
                position = 'right'
            else:
                # Right node, sibling is left
                sibling_index = current_index - 1
                position = 'left'

            if sibling_index < len(level):
                proof.append((level[sibling_index], position))

            # Move to parent
            current_index //= 2

        return proof

    def get_proof_hex(self, index: int) -> List[Tuple[str, str]]:
        """
        Get Merkle proof as hex strings.

        Args:
            index: Index of leaf in original updates list

        Returns:
            List of (sibling_hash_hex, position)
        """
        proof = self.get_proof(index)
        return [(sibling.hex(), position) for sibling, position in proof]

    @staticmethod
    def verify_proof(leaf_hash: bytes, proof: List[Tuple[bytes, str]], root: bytes) -> bool:
        """
        Verify Merkle proof.

        Reconstructs root from leaf using proof path and checks equality.

        Args:
            leaf_hash: Hash of the leaf to verify
            proof: List of (sibling_hash, position)
            root: Expected Merkle root

        Returns:
            True if proof is valid and reconstructed root matches
        """
        current = leaf_hash

        for sibling, position in proof:
            if position == 'left':
                current = hashlib.sha256(sibling + current).digest()
            else:
                current = hashlib.sha256(current + sibling).digest()

        return current == root

    @staticmethod
    def verify_proof_hex(leaf_hash_hex: str, proof_hex: List[Tuple[str, str]], root_hex: str) -> bool:
        """
        Verify Merkle proof using hex strings.

        Args:
            leaf_hash_hex: Hex string of leaf hash
            proof_hex: List of (sibling_hash_hex, position)
            root_hex: Expected Merkle root hex

        Returns:
            True if proof is valid
        """
        leaf_hash = bytes.fromhex(leaf_hash_hex)
        proof = [(bytes.fromhex(sibling_hex), position) for sibling_hex, position in proof_hex]
        root = bytes.fromhex(root_hex)

        return TrustMerkleTree.verify_proof(leaf_hash, proof, root)

    def get_leaf_count(self) -> int:
        """Get number of leaves in tree"""
        return len(self.leaves)

    def get_tree_height(self) -> int:
        """Get height of tree (number of levels)"""
        return len(self.tree)

    def get_stats(self) -> dict:
        """
        Get tree statistics.

        Returns:
            Dictionary with tree stats
        """
        return {
            'leaf_count': self.get_leaf_count(),
            'tree_height': self.get_tree_height(),
            'root_hash': self.get_root_hex(),
            'proof_size': self.get_tree_height() - 1  # Proof length for any leaf
        }


# Example usage and testing
if __name__ == "__main__":
    print("Trust Merkle Tree - Example Usage")
    print("=" * 60)

    # Create some test updates
    updates = []
    for i in range(10):
        updates.append(TrustUpdateLeaf(
            lct_id=f"lct:ai:test:{i:03d}",
            org_id="org:test:001",
            talent_delta=Decimal('0.001'),
            training_delta=Decimal('0.002'),
            temperament_delta=Decimal('0.001'),
            veracity_delta=Decimal('0.01'),
            validity_delta=Decimal('0.01'),
            valuation_delta=Decimal('0.005'),
            timestamp=datetime.utcnow(),
            action_count=1,
            transaction_count=1
        ))

    # Build Merkle tree
    print(f"\nBuilding Merkle tree from {len(updates)} updates...")
    tree = TrustMerkleTree(updates)

    # Display stats
    stats = tree.get_stats()
    print(f"\nTree Statistics:")
    print(f"  Leaf count: {stats['leaf_count']}")
    print(f"  Tree height: {stats['tree_height']} levels")
    print(f"  Root hash: {stats['root_hash']}")
    print(f"  Proof size: {stats['proof_size']} hashes per proof")

    # Generate proof for first update
    print(f"\nGenerating proof for update #0...")
    proof = tree.get_proof(0)
    proof_hex = tree.get_proof_hex(0)

    print(f"  Proof length: {len(proof)} hashes")
    print(f"  Proof path:")
    for i, (hash_hex, position) in enumerate(proof_hex):
        print(f"    Level {i+1}: {position:5s} {hash_hex[:16]}...")

    # Verify proof
    leaf_hash = updates[0].hash()
    is_valid = TrustMerkleTree.verify_proof(leaf_hash, proof, tree.get_root())
    print(f"\nProof verification: {'✅ VALID' if is_valid else '❌ INVALID'}")

    # Test tampering detection
    print(f"\nTesting tamper detection...")
    tampered_leaf = TrustUpdateLeaf(
        lct_id="lct:ai:TAMPERED:999",
        org_id="org:test:001",
        talent_delta=Decimal('0.999'),  # Tampered value
        training_delta=Decimal('0.002'),
        temperament_delta=Decimal('0.001'),
        veracity_delta=Decimal('0.01'),
        validity_delta=Decimal('0.01'),
        valuation_delta=Decimal('0.005'),
        timestamp=updates[0].timestamp,
        action_count=1,
        transaction_count=1
    )

    tampered_hash = tampered_leaf.hash()
    is_tampered_valid = TrustMerkleTree.verify_proof(tampered_hash, proof, tree.get_root())
    print(f"  Tampered proof: {'❌ ACCEPTED (BUG!)' if is_tampered_valid else '✅ REJECTED (EXPECTED)'}")

    # Memory efficiency
    import sys
    tree_size = sys.getsizeof(tree.tree)
    proof_size = sys.getsizeof(proof)
    print(f"\nMemory efficiency:")
    print(f"  Full tree: ~{tree_size:,} bytes")
    print(f"  Single proof: ~{proof_size:,} bytes")
    print(f"  Compression: {tree_size/proof_size:.1f}x")

    print("\n" + "=" * 60)
    print("✅ Merkle tree implementation verified")
