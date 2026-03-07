"""
Cryptographic Trust Primitives for Web4
Session 30, Track 8

Cryptographic building blocks for trust systems:
- Commitment schemes (Pedersen-like, hash-based)
- Verifiable random functions (VRF) for leader election
- Threshold signatures for multi-party trust
- Merkle trees for attestation proofs
- Zero-knowledge proofs for trust level assertions
- Blind signatures for privacy-preserving attestation
- Accumulator for revocation lists
"""

import hashlib
import hmac
import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set


# ─── Hash Utilities ────────────────────────────────────────────────

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_combine(a: bytes, b: bytes) -> bytes:
    """Combine two hashes (for Merkle tree)."""
    return sha256(a + b)


# ─── Commitment Scheme ────────────────────────────────────────────

@dataclass
class Commitment:
    """Hash-based commitment scheme."""
    value: bytes
    nonce: bytes
    commitment: str

    @staticmethod
    def create(value: bytes, nonce: bytes = None) -> 'Commitment':
        if nonce is None:
            nonce = random.randbytes(32)
        commitment = sha256_hex(value + nonce)
        return Commitment(value, nonce, commitment)

    def verify(self) -> bool:
        """Verify commitment opens correctly."""
        expected = sha256_hex(self.value + self.nonce)
        return expected == self.commitment

    def verify_value(self, claimed_value: bytes, claimed_nonce: bytes) -> bool:
        """Verify that claimed value/nonce match commitment."""
        expected = sha256_hex(claimed_value + claimed_nonce)
        return expected == self.commitment


@dataclass
class TrustCommitment:
    """Commit to a trust score without revealing it."""
    trust_level: int        # quantized trust [0, 100]
    nonce: bytes
    commitment: str

    @staticmethod
    def create(trust_level: int) -> 'TrustCommitment':
        nonce = random.randbytes(32)
        data = trust_level.to_bytes(4, 'big') + nonce
        commitment = sha256_hex(data)
        return TrustCommitment(trust_level, nonce, commitment)

    def reveal(self) -> Tuple[int, bytes]:
        return self.trust_level, self.nonce

    def verify_reveal(self, level: int, nonce: bytes) -> bool:
        data = level.to_bytes(4, 'big') + nonce
        return sha256_hex(data) == self.commitment


# ─── Merkle Tree ───────────────────────────────────────────────────

@dataclass
class MerkleNode:
    hash_val: bytes
    left: Optional['MerkleNode'] = None
    right: Optional['MerkleNode'] = None


class MerkleTree:
    """Merkle tree for attestation proofs."""

    def __init__(self, leaves: List[bytes]):
        self.leaves = leaves
        self.root = self._build(leaves) if leaves else None

    def _build(self, data: List[bytes]) -> MerkleNode:
        nodes = [MerkleNode(sha256(d)) for d in data]

        while len(nodes) > 1:
            next_level = []
            for i in range(0, len(nodes), 2):
                if i + 1 < len(nodes):
                    combined = hash_combine(nodes[i].hash_val, nodes[i + 1].hash_val)
                    parent = MerkleNode(combined, nodes[i], nodes[i + 1])
                else:
                    # Odd node: promote
                    parent = MerkleNode(nodes[i].hash_val, nodes[i], None)
                next_level.append(parent)
            nodes = next_level

        return nodes[0]

    @property
    def root_hash(self) -> bytes:
        return self.root.hash_val if self.root else b''

    def proof(self, index: int) -> List[Tuple[bytes, str]]:
        """
        Generate Merkle proof for leaf at index.
        Returns list of (hash, side) pairs.
        """
        if index >= len(self.leaves):
            return []

        proof_path = []
        nodes = [MerkleNode(sha256(d)) for d in self.leaves]

        idx = index
        while len(nodes) > 1:
            next_level = []
            for i in range(0, len(nodes), 2):
                if i + 1 < len(nodes):
                    if i == idx or i + 1 == idx:
                        sibling_idx = i + 1 if i == idx else i
                        side = "right" if sibling_idx > idx else "left"
                        proof_path.append((nodes[sibling_idx].hash_val, side))
                    combined = hash_combine(nodes[i].hash_val, nodes[i + 1].hash_val)
                    next_level.append(MerkleNode(combined))
                else:
                    next_level.append(nodes[i])
                    if i == idx:
                        # No sibling, no proof element needed
                        pass
            idx = idx // 2
            nodes = next_level

        return proof_path

    @staticmethod
    def verify_proof(leaf: bytes, proof: List[Tuple[bytes, str]],
                     root_hash: bytes) -> bool:
        """Verify Merkle proof."""
        current = sha256(leaf)

        for sibling_hash, side in proof:
            if side == "right":
                current = hash_combine(current, sibling_hash)
            else:
                current = hash_combine(sibling_hash, current)

        return current == root_hash


# ─── VRF (Simplified) ─────────────────────────────────────────────

class SimpleVRF:
    """
    Simplified VRF using HMAC.
    Not cryptographically secure VRF, but demonstrates the concept:
    - Deterministic output from secret key + input
    - Output looks random (uniform distribution)
    - Proof that correct key was used
    """

    def __init__(self, secret_key: bytes):
        self.secret_key = secret_key

    def evaluate(self, input_data: bytes) -> Tuple[bytes, bytes]:
        """
        Returns (output, proof).
        Output is deterministic and pseudorandom.
        """
        output = hmac.new(self.secret_key, input_data, hashlib.sha256).digest()
        # Proof: HMAC with different tag
        proof = hmac.new(self.secret_key, b"proof:" + input_data, hashlib.sha256).digest()
        return output, proof

    def verify(self, input_data: bytes, output: bytes, proof: bytes) -> bool:
        """Verify VRF output (requires knowing secret key in this simplified version)."""
        expected_output, expected_proof = self.evaluate(input_data)
        return output == expected_output and proof == expected_proof

    def output_to_float(self, output: bytes) -> float:
        """Convert VRF output to [0, 1] float."""
        # Use first 8 bytes as uint64
        val = int.from_bytes(output[:8], 'big')
        return val / (2 ** 64)


# ─── Threshold Signatures (Simplified) ────────────────────────────

@dataclass
class ThresholdShare:
    """A share of a threshold signature."""
    signer_id: int
    share: bytes
    message_hash: str


class ThresholdSignature:
    """
    Simplified threshold signature scheme.
    t-of-n: need t shares to reconstruct.
    Uses hash-based simulation (not real crypto).
    """

    def __init__(self, n: int, t: int, group_key: bytes):
        self.n = n
        self.t = t
        self.group_key = group_key
        # Generate signer keys
        self.signer_keys = {
            i: sha256(group_key + i.to_bytes(4, 'big'))
            for i in range(n)
        }

    def sign_share(self, signer_id: int, message: bytes) -> ThresholdShare:
        """Generate a signature share."""
        key = self.signer_keys[signer_id]
        share = hmac.new(key, message, hashlib.sha256).digest()
        msg_hash = sha256_hex(message)
        return ThresholdShare(signer_id, share, msg_hash)

    def combine(self, shares: List[ThresholdShare]) -> Optional[bytes]:
        """Combine t shares into full signature."""
        if len(shares) < self.t:
            return None

        # Verify all shares are for the same message
        msg_hashes = set(s.message_hash for s in shares)
        if len(msg_hashes) != 1:
            return None

        # Combine shares (simplified: hash all shares together)
        combined = b""
        for s in sorted(shares, key=lambda x: x.signer_id):
            combined += s.share

        return sha256(combined)

    def verify_combined(self, message: bytes, signature: bytes,
                        shares: List[ThresholdShare]) -> bool:
        """Verify combined signature."""
        expected = self.combine(shares)
        return expected == signature


# ─── Simple ZK Range Proof ────────────────────────────────────────

@dataclass
class RangeProof:
    """
    Simplified range proof: prove trust ∈ [min, max] without revealing exact value.
    Uses commitment + bit decomposition (conceptual).
    """
    commitment: str
    proof_data: Dict
    valid: bool


def create_range_proof(trust_level: int, min_val: int, max_val: int) -> RangeProof:
    """Create proof that trust_level ∈ [min_val, max_val]."""
    nonce = random.randbytes(32)
    commitment = sha256_hex(trust_level.to_bytes(4, 'big') + nonce)

    in_range = min_val <= trust_level <= max_val

    # Simplified proof: commit to (value - min) and (max - value)
    # Both must be non-negative for value to be in range
    lower_diff = trust_level - min_val
    upper_diff = max_val - trust_level

    proof_data = {
        "lower_commitment": sha256_hex(lower_diff.to_bytes(4, 'big', signed=True) + nonce[:16]),
        "upper_commitment": sha256_hex(upper_diff.to_bytes(4, 'big', signed=True) + nonce[16:]),
        "nonce_hash": sha256_hex(nonce),
        "min": min_val,
        "max": max_val,
    }

    return RangeProof(commitment, proof_data, in_range)


def verify_range_proof_with_reveal(proof: RangeProof, trust_level: int, nonce: bytes) -> bool:
    """Verify range proof given revealed value (for testing)."""
    # Verify commitment
    expected_commitment = sha256_hex(trust_level.to_bytes(4, 'big') + nonce)
    if expected_commitment != proof.commitment:
        return False

    # Check range
    return proof.proof_data["min"] <= trust_level <= proof.proof_data["max"]


# ─── Accumulator (Hash-based) ─────────────────────────────────────

class HashAccumulator:
    """
    Simple hash-based accumulator for revocation lists.
    Supports membership proofs (presence in revoked set).
    """

    def __init__(self):
        self.elements: Set[bytes] = set()
        self._accumulator = sha256(b"empty_accumulator")

    def add(self, element: bytes):
        """Add element to accumulator."""
        self.elements.add(element)
        self._recompute()

    def remove(self, element: bytes):
        """Remove element from accumulator."""
        self.elements.discard(element)
        self._recompute()

    def _recompute(self):
        """Recompute accumulator value."""
        # Sort for deterministic ordering
        sorted_elements = sorted(self.elements)
        acc = sha256(b"accumulator_base")
        for elem in sorted_elements:
            acc = hash_combine(acc, sha256(elem))
        self._accumulator = acc

    @property
    def value(self) -> bytes:
        return self._accumulator

    def membership_proof(self, element: bytes) -> Optional[List[bytes]]:
        """Generate proof of membership."""
        if element not in self.elements:
            return None

        # Proof: all other elements (simplified — real accumulators are more efficient)
        sorted_elements = sorted(self.elements)
        proof = []
        for elem in sorted_elements:
            if elem != element:
                proof.append(sha256(elem))
        return proof

    def verify_membership(self, element: bytes, proof: List[bytes]) -> bool:
        """Verify membership proof."""
        # Reconstruct accumulator with element + proof elements
        all_hashes = sorted(proof + [sha256(element)])
        acc = sha256(b"accumulator_base")
        for h in all_hashes:
            acc = hash_combine(acc, h)
        return acc == self._accumulator

    def contains(self, element: bytes) -> bool:
        return element in self.elements


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

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
    print("Cryptographic Trust Primitives for Web4")
    print("Session 30, Track 8")
    print("=" * 70)

    # ── §1 Hash Commitment ────────────────────────────────────────
    print("\n§1 Hash Commitment Scheme\n")

    c = Commitment.create(b"trust_score_75", b"nonce_1234567890abcdef" * 2)
    check("commitment_verifies", c.verify())
    check("commitment_length", len(c.commitment) == 64)

    # Wrong value doesn't verify
    check("wrong_value_fails", not c.verify_value(b"trust_score_50", c.nonce))

    # Correct value verifies
    check("correct_value_passes", c.verify_value(c.value, c.nonce))

    # ── §2 Trust Commitment ───────────────────────────────────────
    print("\n§2 Trust Score Commitment\n")

    random.seed(42)
    tc = TrustCommitment.create(75)
    level, nonce = tc.reveal()
    check("trust_commit_reveal", tc.verify_reveal(level, nonce))
    check("trust_commit_value", level == 75)

    # Wrong level fails
    check("wrong_level_fails", not tc.verify_reveal(50, nonce))

    # Two commitments to same value are different (different nonce)
    random.seed(43)
    tc2 = TrustCommitment.create(75)
    check("different_nonces", tc.commitment != tc2.commitment)

    # ── §3 Merkle Tree ────────────────────────────────────────────
    print("\n§3 Merkle Tree\n")

    leaves = [f"attestation_{i}".encode() for i in range(8)]
    tree = MerkleTree(leaves)

    check("root_not_empty", len(tree.root_hash) > 0)

    # Proof for leaf 3
    proof = tree.proof(3)
    check("proof_exists", len(proof) > 0)

    # Verify proof
    check("proof_verifies",
          MerkleTree.verify_proof(leaves[3], proof, tree.root_hash))

    # Wrong leaf doesn't verify
    check("wrong_leaf_fails",
          not MerkleTree.verify_proof(b"fake_attestation", proof, tree.root_hash))

    # Different tree has different root
    tree2 = MerkleTree([b"different_" + l for l in leaves])
    check("different_trees_different_roots", tree.root_hash != tree2.root_hash)

    # ── §4 VRF ────────────────────────────────────────────────────
    print("\n§4 Verifiable Random Function\n")

    vrf = SimpleVRF(b"secret_leader_key_1234567890abcdef")

    output1, proof1 = vrf.evaluate(b"round_42")
    output2, proof2 = vrf.evaluate(b"round_43")

    # Deterministic
    output1b, proof1b = vrf.evaluate(b"round_42")
    check("vrf_deterministic", output1 == output1b)

    # Different inputs → different outputs
    check("vrf_different_outputs", output1 != output2)

    # Verify
    check("vrf_verifies", vrf.verify(b"round_42", output1, proof1))
    check("vrf_wrong_fails", not vrf.verify(b"round_42", output2, proof2))

    # Output to float: uniform in [0, 1]
    floats = [vrf.output_to_float(vrf.evaluate(f"round_{i}".encode())[0])
              for i in range(100)]
    check("vrf_float_bounded", all(0 <= f <= 1 for f in floats))

    # Not all the same
    check("vrf_float_varies", len(set(floats)) > 90)

    # ── §5 Threshold Signatures ───────────────────────────────────
    print("\n§5 Threshold Signatures\n")

    ts = ThresholdSignature(n=5, t=3, group_key=b"group_key_for_federation")
    message = b"consensus_block_hash_12345"

    # Generate shares from 3 signers
    shares = [ts.sign_share(i, message) for i in range(3)]
    check("enough_shares", len(shares) == 3)

    # Combine
    sig = ts.combine(shares)
    check("signature_produced", sig is not None)

    # Verify
    check("signature_verifies", ts.verify_combined(message, sig, shares))

    # Not enough shares → None
    insufficient = ts.combine(shares[:2])
    check("insufficient_shares_none", insufficient is None)

    # Mixed messages → None
    bad_share = ts.sign_share(3, b"different_message")
    mixed = shares[:2] + [bad_share]
    check("mixed_messages_none", ts.combine(mixed) is None)

    # ── §6 Range Proof ────────────────────────────────────────────
    print("\n§6 Zero-Knowledge Range Proof\n")

    random.seed(42)
    # Trust 75 in [50, 90]
    rp = create_range_proof(75, 50, 90)
    check("range_proof_valid", rp.valid)
    check("range_proof_has_commitment", len(rp.commitment) == 64)

    # Trust 30 NOT in [50, 90]
    rp_invalid = create_range_proof(30, 50, 90)
    check("out_of_range_invalid", not rp_invalid.valid)

    # Boundary: exactly at min
    rp_min = create_range_proof(50, 50, 90)
    check("at_min_valid", rp_min.valid)

    # Boundary: exactly at max
    rp_max = create_range_proof(90, 50, 90)
    check("at_max_valid", rp_max.valid)

    # ── §7 Hash Accumulator ───────────────────────────────────────
    print("\n§7 Revocation Accumulator\n")

    acc = HashAccumulator()
    acc.add(b"revoked_entity_1")
    acc.add(b"revoked_entity_2")
    acc.add(b"revoked_entity_3")

    check("contains_added", acc.contains(b"revoked_entity_1"))
    check("not_contains_missing", not acc.contains(b"entity_4"))

    # Membership proof
    proof = acc.membership_proof(b"revoked_entity_2")
    check("membership_proof_exists", proof is not None)
    check("membership_verifies",
          acc.verify_membership(b"revoked_entity_2", proof))

    # Non-member proof is None
    check("non_member_no_proof",
          acc.membership_proof(b"entity_4") is None)

    # Remove and recheck
    old_value = acc.value
    acc.remove(b"revoked_entity_2")
    check("accumulator_changes", acc.value != old_value)
    check("removed_not_contained", not acc.contains(b"revoked_entity_2"))

    # ── §8 Integration: Attestation Chain ─────────────────────────
    print("\n§8 Integration: Attestation Chain\n")

    # Create trust commitments
    random.seed(100)
    commitments = [TrustCommitment.create(random.randint(30, 90)) for _ in range(4)]

    # Build Merkle tree of commitments
    commitment_leaves = [c.commitment.encode() for c in commitments]
    attest_tree = MerkleTree(commitment_leaves)

    # Prove commitment 2 is in the tree
    proof_2 = attest_tree.proof(2)
    check("attestation_proof_verifies",
          MerkleTree.verify_proof(commitment_leaves[2], proof_2, attest_tree.root_hash))

    # Reveal commitment 2
    level, nonce = commitments[2].reveal()
    check("revealed_commitment_valid", commitments[2].verify_reveal(level, nonce))

    # Threshold sign the root
    ts2 = ThresholdSignature(n=4, t=3, group_key=b"federation_attestation_key")
    root_shares = [ts2.sign_share(i, attest_tree.root_hash) for i in range(3)]
    root_sig = ts2.combine(root_shares)
    check("root_threshold_signed", root_sig is not None)

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
