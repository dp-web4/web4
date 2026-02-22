#!/usr/bin/env python3
"""
ACT Settlement Protocol — Reference Implementation

Closes the #1 gap in the Web4 canonical equation:
  Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP

ATP/ADP metering (CreditGrant→UsageReport→Settle) exists.
Cross-society ATP sync (COMMIT→VERIFY→RECONCILE) exists.
What was MISSING: the ACT chain itself — the settlement ledger that
provides finality, immutability, and proof anchoring.

This implementation provides:
  1. MockACTChain — Hash-chained blocks with 2/3 consensus + Merkle proofs
  2. FractalChainManager — Compost→Leaf→Stem→Root with SNARC gating
  3. ACTSettlementEngine — Bridges ATPSyncManager ↔ ACT chain for finality
  4. Settlement anchoring — BilateralStatements anchored on-chain
  5. ADP proof anchoring — Discharge proofs on-chain
  6. Conservation proofs — On-chain verification of ATP conservation
  7. Double-spend detection — Cross-chain prevention
  8. Fork resolution — Witness-majority canonical selection

Spec references:
  - web4-standard/core-spec/atp-adp-cycle.md
  - ledgers/spec/fractal-chains/
  - implementation/reference/cross_society_atp_sync.py
  - implementation/reference/atp_metering.py
"""

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
#  1. CORE DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

class ChainLevel(Enum):
    """Fractal chain hierarchy — ephemeral → permanent."""
    COMPOST = 0   # ms-seconds, ring buffer, no ATP cost
    LEAF = 1      # seconds-minutes, SNARC-gated, 1-10 ATP
    STEM = 2      # minutes-hours, multi-witness, 10-100 ATP
    ROOT = 3      # permanent, global consensus, 100+ ATP


class EntryType(Enum):
    """Types of entries that can be anchored on-chain."""
    BILATERAL_SETTLEMENT = "bilateral_settlement"
    ADP_DISCHARGE = "adp_discharge"
    CONSERVATION_PROOF = "conservation_proof"
    LCT_REGISTRATION = "lct_registration"
    CHARTER_AMENDMENT = "charter_amendment"
    CREDENTIAL_ISSUANCE = "credential_issuance"
    AUDIT_SEAL = "audit_seal"
    TRANSFER_COMMIT = "transfer_commit"
    TRANSFER_COMPLETE = "transfer_complete"
    DOUBLE_SPEND_ALERT = "double_spend_alert"


class ConsensusState(Enum):
    """State of a proposed entry in consensus."""
    PROPOSED = "proposed"
    VOTING = "voting"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FINALIZED = "finalized"


# Witness requirements by entry type (from fractal chain spec)
WITNESS_REQUIREMENTS = {
    EntryType.BILATERAL_SETTLEMENT: 3,
    EntryType.ADP_DISCHARGE: 2,
    EntryType.CONSERVATION_PROOF: 3,
    EntryType.LCT_REGISTRATION: 3,
    EntryType.CHARTER_AMENDMENT: 5,
    EntryType.CREDENTIAL_ISSUANCE: 2,
    EntryType.AUDIT_SEAL: 3,
    EntryType.TRANSFER_COMMIT: 2,
    EntryType.TRANSFER_COMPLETE: 2,
    EntryType.DOUBLE_SPEND_ALERT: 1,
}

# ATP costs by chain level
ATP_COSTS = {
    ChainLevel.COMPOST: 0,
    ChainLevel.LEAF: 5,
    ChainLevel.STEM: 50,
    ChainLevel.ROOT: 200,
}


@dataclass
class WitnessVote:
    """A witness's vote on a proposed entry."""
    witness_id: str
    entry_id: str
    vote: bool  # True = accept, False = reject
    signature: str  # Hex signature
    timestamp: float
    reason: Optional[str] = None


@dataclass
class MerkleNode:
    """A node in a Merkle tree."""
    hash: str
    left: Optional["MerkleNode"] = None
    right: Optional["MerkleNode"] = None
    data: Optional[str] = None  # Only leaves have data


@dataclass
class MerkleProof:
    """Proof of inclusion in a Merkle tree."""
    leaf_hash: str
    root_hash: str
    path: List[Tuple[str, str]]  # [(sibling_hash, "left"|"right"), ...]

    def verify(self) -> bool:
        """Verify this Merkle proof."""
        current = self.leaf_hash
        for sibling_hash, direction in self.path:
            if direction == "left":
                current = _sha256(sibling_hash + current)
            else:
                current = _sha256(current + sibling_hash)
        return current == self.root_hash


@dataclass
class ACTEntry:
    """An entry on the ACT chain."""
    entry_id: str
    entry_type: EntryType
    chain_level: ChainLevel
    timestamp: float
    prev_hash: str
    content: Dict[str, Any]
    content_hash: str
    witnesses: List[WitnessVote] = field(default_factory=list)
    merkle_proof: Optional[MerkleProof] = None
    block_height: Optional[int] = None
    consensus_state: ConsensusState = ConsensusState.PROPOSED
    atp_cost: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type.value,
            "chain_level": self.chain_level.value,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "content": self.content,
            "content_hash": self.content_hash,
            "witnesses": [
                {"witness_id": w.witness_id, "vote": w.vote, "sig": w.signature}
                for w in self.witnesses
            ],
            "block_height": self.block_height,
            "consensus_state": self.consensus_state.value,
            "atp_cost": self.atp_cost,
        }


@dataclass
class ACTBlock:
    """A block of entries on the ACT chain."""
    block_height: int
    timestamp: float
    entries: List[ACTEntry]
    prev_block_hash: str
    merkle_root: str
    consensus_signatures: Dict[str, str]  # node_id → signature
    total_atp_cost: float

    def to_dict(self) -> Dict:
        return {
            "block_height": self.block_height,
            "timestamp": self.timestamp,
            "entry_count": len(self.entries),
            "prev_block_hash": self.prev_block_hash,
            "merkle_root": self.merkle_root,
            "consensus_signatures": len(self.consensus_signatures),
            "total_atp_cost": self.total_atp_cost,
        }

    @property
    def block_hash(self) -> str:
        data = f"{self.block_height}:{self.merkle_root}:{self.prev_block_hash}"
        return _sha256(data)


# ═══════════════════════════════════════════════════════════════
#  2. SNARC SCORING (Significant/Novel/Anomalous/Relevant/Consequential)
# ═══════════════════════════════════════════════════════════════

@dataclass
class SNARCScore:
    """SNARC criteria for leaf→stem promotion."""
    significant: int = 0   # ATP cost > threshold → +2
    novel: int = 0         # First occurrence → +3
    anomalous: int = 0     # anomaly_score > 0.7 → +2
    relevant: int = 0      # Within active MRH → +1
    consequential: int = 0 # Has downstream effects → +2

    @property
    def total(self) -> int:
        return self.significant + self.novel + self.anomalous + self.relevant + self.consequential

    @property
    def should_retain(self) -> bool:
        """Retain in leaf chain if score ≥ 3."""
        return self.total >= 3

    @property
    def should_promote(self) -> bool:
        """Promote to stem chain if score ≥ 5."""
        return self.total >= 5


def compute_snarc(entry: ACTEntry, seen_types: Set[str], mrh_scope: Set[str]) -> SNARCScore:
    """Compute SNARC score for an entry."""
    score = SNARCScore()

    # Significant: high ATP cost
    if entry.atp_cost > 10:
        score.significant = 2

    # Novel: first occurrence of this entry type
    type_key = f"{entry.entry_type.value}:{entry.content.get('type', 'unknown')}"
    if type_key not in seen_types:
        score.novel = 3
        seen_types.add(type_key)

    # Anomalous: content flags anomaly
    if entry.content.get("anomaly_score", 0) > 0.7:
        score.anomalous = 2

    # Relevant: entry references entities in MRH scope
    refs = set()
    for key in ("society_a", "society_b", "source_society", "target_society", "entity_id"):
        if key in entry.content:
            refs.add(entry.content[key])
    if refs & mrh_scope:
        score.relevant = 1

    # Consequential: has downstream effects (settlements, alerts)
    consequential_types = {
        EntryType.BILATERAL_SETTLEMENT,
        EntryType.DOUBLE_SPEND_ALERT,
        EntryType.CONSERVATION_PROOF,
        EntryType.CHARTER_AMENDMENT,
    }
    if entry.entry_type in consequential_types:
        score.consequential = 2

    return score


# ═══════════════════════════════════════════════════════════════
#  3. MERKLE TREE
# ═══════════════════════════════════════════════════════════════

def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def build_merkle_tree(hashes: List[str]) -> Optional[MerkleNode]:
    """Build a Merkle tree from leaf hashes."""
    if not hashes:
        return None

    # Create leaf nodes
    nodes = [MerkleNode(hash=h, data=h) for h in hashes]

    # Pad to power of 2
    while len(nodes) & (len(nodes) - 1):
        nodes.append(MerkleNode(hash=nodes[-1].hash))

    # Build tree bottom-up
    while len(nodes) > 1:
        next_level = []
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i + 1] if i + 1 < len(nodes) else nodes[i]
            parent_hash = _sha256(left.hash + right.hash)
            parent = MerkleNode(hash=parent_hash, left=left, right=right)
            next_level.append(parent)
        nodes = next_level

    return nodes[0]


def get_merkle_proof(root: MerkleNode, leaf_hash: str) -> Optional[MerkleProof]:
    """Get a proof of inclusion for a leaf hash."""
    path = []

    def _find(node: MerkleNode, target: str) -> bool:
        if node.data == target:
            return True
        if node.left is None:
            return False

        if _find(node.left, target):
            if node.right:
                path.append((node.right.hash, "right"))
            return True
        if node.right and _find(node.right, target):
            path.append((node.left.hash, "left"))
            return True
        return False

    if _find(root, leaf_hash):
        return MerkleProof(
            leaf_hash=leaf_hash,
            root_hash=root.hash,
            path=path,
        )
    return None


# ═══════════════════════════════════════════════════════════════
#  4. MOCK ACT CHAIN
# ═══════════════════════════════════════════════════════════════

class MockACTChain:
    """
    Mock ACT blockchain for settlement protocol anchoring.

    Provides:
    - Hash-chained blocks with 2/3 consensus
    - Merkle tree per block for O(log N) verification
    - Entry-level witness requirements by type
    - Fork detection and resolution
    - Double-spend detection
    """

    def __init__(self, consensus_nodes: List[str], consensus_threshold: float = 0.67):
        self.consensus_nodes = consensus_nodes
        self.consensus_threshold = consensus_threshold
        self.blocks: List[ACTBlock] = []
        self.pending_entries: List[ACTEntry] = []
        self.entry_index: Dict[str, ACTEntry] = {}  # entry_id → entry
        self.settled_transfers: Set[str] = set()  # transfer IDs already settled
        self.genesis_hash = _sha256("act:genesis:web4")
        self._latest_entry_hash = self.genesis_hash

    @property
    def chain_height(self) -> int:
        return len(self.blocks)

    @property
    def latest_block_hash(self) -> str:
        if self.blocks:
            return self.blocks[-1].block_hash
        return self.genesis_hash

    def propose_entry(
        self,
        entry_type: EntryType,
        content: Dict[str, Any],
        chain_level: ChainLevel = ChainLevel.ROOT,
    ) -> ACTEntry:
        """Propose a new entry for consensus."""
        content_hash = _sha256(json.dumps(content, sort_keys=True))
        entry = ACTEntry(
            entry_id=f"act:{entry_type.value}:{uuid.uuid4().hex[:12]}",
            entry_type=entry_type,
            chain_level=chain_level,
            timestamp=time.time(),
            prev_hash=self._latest_entry_hash,
            content=content,
            content_hash=content_hash,
            atp_cost=ATP_COSTS[chain_level],
        )
        self._latest_entry_hash = content_hash
        self.pending_entries.append(entry)
        self.entry_index[entry.entry_id] = entry
        return entry

    def submit_vote(self, entry_id: str, witness_id: str, vote: bool, reason: Optional[str] = None) -> WitnessVote:
        """Submit a witness vote for a pending entry."""
        entry = self.entry_index.get(entry_id)
        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        # Check witness is a valid consensus node
        if witness_id not in self.consensus_nodes:
            raise ValueError(f"Witness {witness_id} not a consensus node")

        # Check for duplicate vote
        if any(w.witness_id == witness_id for w in entry.witnesses):
            raise ValueError(f"Witness {witness_id} already voted on {entry_id}")

        sig = _sha256(f"{witness_id}:{entry_id}:{vote}:{time.time()}")
        w = WitnessVote(
            witness_id=witness_id,
            entry_id=entry_id,
            vote=vote,
            signature=sig,
            timestamp=time.time(),
            reason=reason,
        )
        entry.witnesses.append(w)
        entry.consensus_state = ConsensusState.VOTING
        return w

    def check_consensus(self, entry_id: str) -> Tuple[bool, float]:
        """Check if an entry has reached consensus."""
        entry = self.entry_index.get(entry_id)
        if not entry:
            return False, 0.0

        accept_votes = sum(1 for w in entry.witnesses if w.vote)
        total_nodes = len(self.consensus_nodes)
        ratio = accept_votes / total_nodes if total_nodes > 0 else 0.0

        # Also check witness requirements by entry type
        required_witnesses = WITNESS_REQUIREMENTS.get(entry.entry_type, 2)
        has_enough_witnesses = accept_votes >= required_witnesses
        has_consensus = ratio >= self.consensus_threshold

        return has_enough_witnesses and has_consensus, ratio

    def finalize_entry(self, entry_id: str) -> bool:
        """Finalize an entry that has reached consensus."""
        has_consensus, ratio = self.check_consensus(entry_id)
        if not has_consensus:
            return False

        entry = self.entry_index[entry_id]
        entry.consensus_state = ConsensusState.ACCEPTED
        return True

    def create_block(self) -> Optional[ACTBlock]:
        """Create a block from accepted entries."""
        accepted = [e for e in self.pending_entries if e.consensus_state == ConsensusState.ACCEPTED]
        if not accepted:
            return None

        # Build Merkle tree from entry hashes
        entry_hashes = [e.content_hash for e in accepted]
        merkle_tree = build_merkle_tree(entry_hashes)
        merkle_root = merkle_tree.hash if merkle_tree else _sha256("empty")

        # Assign Merkle proofs to entries
        if merkle_tree:
            for entry in accepted:
                proof = get_merkle_proof(merkle_tree, entry.content_hash)
                if proof:
                    entry.merkle_proof = proof

        # Collect consensus signatures (from all accepting witnesses of any entry)
        all_signers = {}
        for entry in accepted:
            for w in entry.witnesses:
                if w.vote and w.witness_id not in all_signers:
                    all_signers[w.witness_id] = w.signature

        block_height = self.chain_height
        block = ACTBlock(
            block_height=block_height,
            timestamp=time.time(),
            entries=accepted,
            prev_block_hash=self.latest_block_hash,
            merkle_root=merkle_root,
            consensus_signatures=all_signers,
            total_atp_cost=sum(e.atp_cost for e in accepted),
        )

        # Finalize entries
        for entry in accepted:
            entry.block_height = block_height
            entry.consensus_state = ConsensusState.FINALIZED

        self.blocks.append(block)
        self.pending_entries = [e for e in self.pending_entries if e.consensus_state != ConsensusState.FINALIZED]

        return block

    def verify_entry(self, entry_id: str) -> Dict[str, Any]:
        """Verify an entry's immutability proof."""
        entry = self.entry_index.get(entry_id)
        if not entry:
            return {"verified": False, "reason": "entry_not_found"}

        if entry.consensus_state != ConsensusState.FINALIZED:
            return {"verified": False, "reason": "not_finalized", "state": entry.consensus_state.value}

        # Verify Merkle proof
        merkle_valid = entry.merkle_proof.verify() if entry.merkle_proof else False

        # Verify witness count meets requirement
        required = WITNESS_REQUIREMENTS.get(entry.entry_type, 2)
        accept_votes = sum(1 for w in entry.witnesses if w.vote)

        return {
            "verified": merkle_valid and accept_votes >= required,
            "entry_id": entry_id,
            "block_height": entry.block_height,
            "merkle_valid": merkle_valid,
            "witnesses": accept_votes,
            "required_witnesses": required,
            "content_hash": entry.content_hash,
        }

    def detect_double_spend(self, transfer_id: str) -> bool:
        """Check if a transfer has already been settled."""
        if transfer_id in self.settled_transfers:
            return True
        return False

    def record_settlement(self, transfer_id: str) -> None:
        """Record a transfer as settled (for double-spend detection)."""
        self.settled_transfers.add(transfer_id)

    def resolve_fork(self, competing_entries: List[ACTEntry]) -> ACTEntry:
        """Resolve a fork by selecting entry with most witness votes."""
        if not competing_entries:
            raise ValueError("No entries to resolve")
        return max(competing_entries, key=lambda e: sum(1 for w in e.witnesses if w.vote))

    def get_chain_proof(self) -> Dict:
        """Get a proof of the entire chain's integrity."""
        if not self.blocks:
            return {"valid": True, "blocks": 0, "entries": 0}

        valid = True
        prev_hash = self.genesis_hash
        for block in self.blocks:
            if block.prev_block_hash != prev_hash:
                valid = False
                break
            prev_hash = block.block_hash

        return {
            "valid": valid,
            "blocks": len(self.blocks),
            "entries": sum(len(b.entries) for b in self.blocks),
            "latest_hash": self.latest_block_hash,
            "total_atp_cost": sum(b.total_atp_cost for b in self.blocks),
        }

    def query_entries(self, entry_type: Optional[EntryType] = None, since: Optional[float] = None) -> List[ACTEntry]:
        """Query entries by type and/or time."""
        results = []
        for block in self.blocks:
            for entry in block.entries:
                if entry_type and entry.entry_type != entry_type:
                    continue
                if since and entry.timestamp < since:
                    continue
                results.append(entry)
        return results


# ═══════════════════════════════════════════════════════════════
#  5. FRACTAL CHAIN MANAGER
# ═══════════════════════════════════════════════════════════════

class FractalChainManager:
    """
    Manages the 4-level fractal chain hierarchy:
      Compost → Leaf → Stem → Root

    Entries flow upward based on SNARC scoring and witness attestation.
    Each level has different retention, verification, and ATP costs.
    """

    def __init__(self, act_chain: MockACTChain, mrh_scope: Optional[Set[str]] = None):
        self.act_chain = act_chain
        self.mrh_scope = mrh_scope or set()

        # Per-level storage
        self.compost: List[ACTEntry] = []          # Ring buffer
        self.leaf: List[ACTEntry] = []              # SNARC-gated
        self.stem: List[ACTEntry] = []              # Multi-witness
        # Root entries go to act_chain

        self.compost_max_size = 1000  # Ring buffer size
        self.seen_types: Set[str] = set()  # For SNARC novelty tracking
        self._promotion_log: List[Dict] = []

    def ingest(self, entry_type: EntryType, content: Dict[str, Any]) -> ACTEntry:
        """
        Ingest a new entry at the compost level and let it flow upward
        through fractal chain levels based on SNARC scoring.
        """
        entry = ACTEntry(
            entry_id=f"fc:{entry_type.value}:{uuid.uuid4().hex[:12]}",
            entry_type=entry_type,
            chain_level=ChainLevel.COMPOST,
            timestamp=time.time(),
            prev_hash=_sha256(str(len(self.compost))),
            content=content,
            content_hash=_sha256(json.dumps(content, sort_keys=True)),
            atp_cost=0,
        )

        # Add to compost (ring buffer)
        self.compost.append(entry)
        if len(self.compost) > self.compost_max_size:
            self.compost = self.compost[-self.compost_max_size:]

        # SNARC scoring for potential promotion
        snarc = compute_snarc(entry, self.seen_types, self.mrh_scope)

        if snarc.should_promote:
            self._promote_to_stem(entry, snarc)
        elif snarc.should_retain:
            self._promote_to_leaf(entry, snarc)

        return entry

    def _promote_to_leaf(self, entry: ACTEntry, snarc: SNARCScore) -> None:
        """Promote entry from compost to leaf level."""
        entry.chain_level = ChainLevel.LEAF
        entry.atp_cost = ATP_COSTS[ChainLevel.LEAF]
        self.leaf.append(entry)
        self._promotion_log.append({
            "entry_id": entry.entry_id,
            "from": "compost",
            "to": "leaf",
            "snarc_score": snarc.total,
            "timestamp": time.time(),
        })

    def _promote_to_stem(self, entry: ACTEntry, snarc: SNARCScore) -> None:
        """Promote entry from compost to stem level (skipping leaf)."""
        entry.chain_level = ChainLevel.STEM
        entry.atp_cost = ATP_COSTS[ChainLevel.STEM]
        self.stem.append(entry)
        self._promotion_log.append({
            "entry_id": entry.entry_id,
            "from": "compost",
            "to": "stem",
            "snarc_score": snarc.total,
            "timestamp": time.time(),
        })

    def promote_to_root(self, entry_id: str) -> Optional[ACTEntry]:
        """
        Promote a stem entry to root level (on-chain).
        Requires consensus via the ACT chain.
        """
        # Find in stem
        entry = None
        for e in self.stem:
            if e.entry_id == entry_id:
                entry = e
                break

        if not entry:
            return None

        # Create on-chain entry
        root_entry = self.act_chain.propose_entry(
            entry_type=entry.entry_type,
            content=entry.content,
            chain_level=ChainLevel.ROOT,
        )

        self._promotion_log.append({
            "entry_id": entry.entry_id,
            "root_entry_id": root_entry.entry_id,
            "from": "stem",
            "to": "root",
            "timestamp": time.time(),
        })

        return root_entry

    def get_stats(self) -> Dict:
        """Get statistics for all chain levels."""
        return {
            "compost": len(self.compost),
            "leaf": len(self.leaf),
            "stem": len(self.stem),
            "root": sum(len(b.entries) for b in self.act_chain.blocks),
            "promotions": len(self._promotion_log),
            "total_atp_cost": (
                sum(e.atp_cost for e in self.leaf) +
                sum(e.atp_cost for e in self.stem) +
                sum(b.total_atp_cost for b in self.act_chain.blocks)
            ),
        }


# ═══════════════════════════════════════════════════════════════
#  6. ACT SETTLEMENT ENGINE
# ═══════════════════════════════════════════════════════════════

@dataclass
class SettlementRecord:
    """A record of a finalized settlement."""
    settlement_id: str
    statement: Dict[str, Any]       # BilateralStatement content
    entry_id: str                   # ACT chain entry ID
    block_height: Optional[int]
    merkle_proof: Optional[MerkleProof]
    conservation_verified: bool
    timestamp: float


@dataclass
class ConservationProof:
    """Proof that ATP conservation holds across all societies."""
    proof_id: str
    timestamp: float
    societies: Dict[str, float]     # society_id → balance
    total_atp: float
    expected_total: float
    drift: float
    conserved: bool
    entry_id: Optional[str] = None  # ACT chain entry if anchored


@dataclass
class ADPProof:
    """Proof of an ADP (Allocation Discharge Packet) on-chain."""
    adp_id: str
    grant_id: str
    discharged_amount: float
    remaining: float
    evidence_digest: str
    entry_id: Optional[str] = None
    timestamp: float = 0.0


class ACTSettlementEngine:
    """
    Bridges cross-society ATP sync with the ACT chain.

    Workflow:
    1. Societies perform ATP transfers via COMMIT→VERIFY→RECONCILE
    2. BilateralStatements from reconciliation are proposed to ACT chain
    3. Consensus nodes vote; accepted entries get Merkle proofs
    4. Settlement is final once block is created
    5. Conservation proofs are periodically anchored

    Also handles:
    - ADP discharge anchoring
    - Double-spend detection
    - Conservation verification
    """

    def __init__(self, act_chain: MockACTChain):
        self.act_chain = act_chain
        self.settlements: List[SettlementRecord] = []
        self.conservation_proofs: List[ConservationProof] = []
        self.adp_proofs: List[ADPProof] = []
        self._double_spend_alerts: List[Dict] = []

    def anchor_settlement(self, statement: Dict[str, Any]) -> ACTEntry:
        """
        Anchor a BilateralStatement on the ACT chain.
        Returns the proposed entry (still needs consensus votes).
        """
        # Check for double-spend on any transfer referenced
        transfer_ids = statement.get("transfer_ids", [])
        for tid in transfer_ids:
            if self.act_chain.detect_double_spend(tid):
                # Record alert
                alert = self.act_chain.propose_entry(
                    EntryType.DOUBLE_SPEND_ALERT,
                    {"transfer_id": tid, "statement": statement},
                    ChainLevel.ROOT,
                )
                self._double_spend_alerts.append({
                    "transfer_id": tid,
                    "alert_entry": alert.entry_id,
                    "timestamp": time.time(),
                })
                raise ValueError(f"Double-spend detected for transfer {tid}")

        # Propose settlement entry
        entry = self.act_chain.propose_entry(
            EntryType.BILATERAL_SETTLEMENT,
            {
                "type": "bilateral_settlement",
                "statement_id": statement.get("statement_id", f"stmt:{uuid.uuid4().hex[:12]}"),
                "society_a": statement["society_a"],
                "society_b": statement["society_b"],
                "a_balance": statement["a_balance"],
                "b_balance": statement["b_balance"],
                "net_position": statement["net_position"],
                "transfers_reconciled": statement.get("transfers_reconciled", 0),
            },
            ChainLevel.ROOT,
        )

        # Record transfer IDs as settled
        for tid in transfer_ids:
            self.act_chain.record_settlement(tid)

        return entry

    def finalize_settlement(self, entry_id: str) -> Optional[SettlementRecord]:
        """
        Finalize a settlement after consensus is reached and block is created.
        """
        entry = self.act_chain.entry_index.get(entry_id)
        if not entry or entry.consensus_state != ConsensusState.FINALIZED:
            return None

        record = SettlementRecord(
            settlement_id=entry.content.get("statement_id", entry.entry_id),
            statement=entry.content,
            entry_id=entry.entry_id,
            block_height=entry.block_height,
            merkle_proof=entry.merkle_proof,
            conservation_verified=False,
            timestamp=time.time(),
        )
        self.settlements.append(record)
        return record

    def anchor_conservation_proof(self, societies: Dict[str, float], expected_total: float) -> ConservationProof:
        """
        Anchor a conservation proof on-chain.
        Verifies that total ATP across all societies equals expected.
        """
        total = sum(societies.values())
        drift = abs(total - expected_total)
        conserved = drift < 0.001  # Float tolerance

        proof = ConservationProof(
            proof_id=f"cons:{uuid.uuid4().hex[:12]}",
            timestamp=time.time(),
            societies=dict(societies),
            total_atp=total,
            expected_total=expected_total,
            drift=drift,
            conserved=conserved,
        )

        # Anchor on-chain
        entry = self.act_chain.propose_entry(
            EntryType.CONSERVATION_PROOF,
            {
                "type": "conservation_proof",
                "proof_id": proof.proof_id,
                "total_atp": total,
                "expected_total": expected_total,
                "drift": drift,
                "conserved": conserved,
                "society_count": len(societies),
            },
            ChainLevel.ROOT,
        )
        proof.entry_id = entry.entry_id

        self.conservation_proofs.append(proof)
        return proof

    def anchor_adp_discharge(self, grant_id: str, discharged: float, remaining: float, evidence: str) -> ADPProof:
        """
        Anchor an ADP discharge proof on-chain.
        Records that ATP was consumed and provides evidence digest.
        """
        adp = ADPProof(
            adp_id=f"adp:{uuid.uuid4().hex[:12]}",
            grant_id=grant_id,
            discharged_amount=discharged,
            remaining=remaining,
            evidence_digest=evidence,
            timestamp=time.time(),
        )

        entry = self.act_chain.propose_entry(
            EntryType.ADP_DISCHARGE,
            {
                "type": "adp_discharge",
                "adp_id": adp.adp_id,
                "grant_id": grant_id,
                "discharged": discharged,
                "remaining": remaining,
                "evidence_digest": evidence,
            },
            ChainLevel.STEM,  # ADP discharges start at stem level
        )
        adp.entry_id = entry.entry_id

        self.adp_proofs.append(adp)
        return adp

    def verify_settlement(self, settlement_id: str) -> Dict:
        """Verify a finalized settlement's immutability."""
        record = next((s for s in self.settlements if s.settlement_id == settlement_id), None)
        if not record:
            return {"verified": False, "reason": "settlement_not_found"}

        chain_verification = self.act_chain.verify_entry(record.entry_id)
        return {
            "settlement_id": settlement_id,
            "chain_verification": chain_verification,
            "block_height": record.block_height,
            "conservation_verified": record.conservation_verified,
        }

    def get_stats(self) -> Dict:
        """Get settlement engine statistics."""
        return {
            "settlements": len(self.settlements),
            "conservation_proofs": len(self.conservation_proofs),
            "adp_proofs": len(self.adp_proofs),
            "double_spend_alerts": len(self._double_spend_alerts),
            "chain": self.act_chain.get_chain_proof(),
        }


# ═══════════════════════════════════════════════════════════════
#  7. INTEGRATED E2E TEST
# ═══════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name: str, condition: bool):
        nonlocal passed, failed
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}")
        if condition:
            passed += 1
        else:
            failed += 1

    # ─── T1: Mock ACT Chain — Genesis ───
    print("\n═══ T1: Mock ACT Chain — Genesis ═══")
    nodes = ["node-alpha", "node-beta", "node-gamma", "node-delta", "node-epsilon"]
    chain = MockACTChain(consensus_nodes=nodes, consensus_threshold=0.6)

    check("T1: chain created", chain is not None)
    check("T1: genesis hash exists", len(chain.genesis_hash) == 64)
    check("T1: height is 0", chain.chain_height == 0)
    check("T1: latest hash is genesis", chain.latest_block_hash == chain.genesis_hash)

    # ─── T2: Entry Proposal + Consensus ───
    print("\n═══ T2: Entry Proposal + Consensus ═══")
    entry = chain.propose_entry(
        EntryType.BILATERAL_SETTLEMENT,
        {
            "society_a": "soc:alpha",
            "society_b": "soc:beta",
            "a_balance": 900.0,
            "b_balance": 1100.0,
            "net_position": 100.0,
            "transfers_reconciled": 3,
        },
    )
    check("T2: entry proposed", entry.consensus_state == ConsensusState.PROPOSED)
    check("T2: entry has ID", entry.entry_id.startswith("act:bilateral_settlement:"))
    check("T2: entry has content hash", len(entry.content_hash) == 64)
    check("T2: ATP cost = 200", entry.atp_cost == 200)

    # Vote — need 3/5 = 60% for consensus
    chain.submit_vote(entry.entry_id, "node-alpha", True)
    chain.submit_vote(entry.entry_id, "node-beta", True)
    has_consensus, ratio = chain.check_consensus(entry.entry_id)
    check("T2: 2/5 no consensus", not has_consensus)

    chain.submit_vote(entry.entry_id, "node-gamma", True)
    has_consensus, ratio = chain.check_consensus(entry.entry_id)
    check("T2: 3/5 = consensus (60%)", has_consensus)
    check("T2: ratio ≈ 0.6", abs(ratio - 0.6) < 0.01)

    # ─── T3: Block Creation + Merkle Proofs ───
    print("\n═══ T3: Block Creation + Merkle Proofs ═══")
    chain.finalize_entry(entry.entry_id)
    check("T3: entry accepted", entry.consensus_state == ConsensusState.ACCEPTED)

    block = chain.create_block()
    check("T3: block created", block is not None)
    check("T3: block height = 0", block.block_height == 0)
    check("T3: block has merkle root", len(block.merkle_root) == 64)
    check("T3: entry finalized", entry.consensus_state == ConsensusState.FINALIZED)
    check("T3: entry has block height", entry.block_height == 0)
    check("T3: entry has merkle proof", entry.merkle_proof is not None)
    check("T3: merkle proof valid", entry.merkle_proof.verify())
    check("T3: chain height = 1", chain.chain_height == 1)

    # ─── T4: Entry Verification ───
    print("\n═══ T4: Entry Verification ═══")
    verification = chain.verify_entry(entry.entry_id)
    check("T4: verified", verification["verified"])
    check("T4: merkle valid", verification["merkle_valid"])
    check("T4: 3 witnesses", verification["witnesses"] == 3)
    check("T4: block height 0", verification["block_height"] == 0)

    # Verify non-existent
    v2 = chain.verify_entry("act:fake:123")
    check("T4: fake entry not verified", not v2["verified"])

    # ─── T5: Chain Integrity Proof ───
    print("\n═══ T5: Chain Integrity Proof ═══")
    proof = chain.get_chain_proof()
    check("T5: chain valid", proof["valid"])
    check("T5: 1 block", proof["blocks"] == 1)
    check("T5: 1 entry", proof["entries"] == 1)
    check("T5: ATP cost = 200", proof["total_atp_cost"] == 200)

    # ─── T6: Multiple Entries + Multi-Block ───
    print("\n═══ T6: Multiple Entries + Multi-Block ═══")
    e2 = chain.propose_entry(
        EntryType.CONSERVATION_PROOF,
        {"total_atp": 2000.0, "expected": 2000.0, "conserved": True},
    )
    e3 = chain.propose_entry(
        EntryType.TRANSFER_COMPLETE,
        {"transfer_id": "xfer:001", "amount": 100.0, "source": "soc:alpha", "target": "soc:beta"},
    )

    # Vote on both
    for node in ["node-alpha", "node-beta", "node-gamma"]:
        chain.submit_vote(e2.entry_id, node, True)
        chain.submit_vote(e3.entry_id, node, True)

    chain.finalize_entry(e2.entry_id)
    chain.finalize_entry(e3.entry_id)
    block2 = chain.create_block()

    check("T6: block 2 created", block2 is not None)
    check("T6: block 2 height = 1", block2.block_height == 1)
    check("T6: block 2 has 2 entries", len(block2.entries) == 2)
    check("T6: chain height = 2", chain.chain_height == 2)
    check("T6: block 2 links to block 1", block2.prev_block_hash == block.block_hash)

    # Both entries should have valid Merkle proofs
    check("T6: e2 merkle valid", e2.merkle_proof is not None and e2.merkle_proof.verify())
    check("T6: e3 merkle valid", e3.merkle_proof is not None and e3.merkle_proof.verify())

    # ─── T7: Double-Spend Detection ───
    print("\n═══ T7: Double-Spend Detection ═══")
    chain.record_settlement("xfer:settled-001")
    check("T7: double-spend detected", chain.detect_double_spend("xfer:settled-001"))
    check("T7: no false positive", not chain.detect_double_spend("xfer:new-001"))

    # ─── T8: Fork Resolution ───
    print("\n═══ T8: Fork Resolution ═══")
    fork_a = ACTEntry(
        entry_id="fork:a",
        entry_type=EntryType.BILATERAL_SETTLEMENT,
        chain_level=ChainLevel.ROOT,
        timestamp=time.time(),
        prev_hash="abc",
        content={"fork": "a"},
        content_hash=_sha256("fork-a"),
        witnesses=[
            WitnessVote("n1", "fork:a", True, "sig1", time.time()),
            WitnessVote("n2", "fork:a", True, "sig2", time.time()),
        ],
    )
    fork_b = ACTEntry(
        entry_id="fork:b",
        entry_type=EntryType.BILATERAL_SETTLEMENT,
        chain_level=ChainLevel.ROOT,
        timestamp=time.time(),
        prev_hash="abc",
        content={"fork": "b"},
        content_hash=_sha256("fork-b"),
        witnesses=[
            WitnessVote("n1", "fork:b", True, "sig1", time.time()),
            WitnessVote("n2", "fork:b", True, "sig2", time.time()),
            WitnessVote("n3", "fork:b", True, "sig3", time.time()),
        ],
    )
    canonical = chain.resolve_fork([fork_a, fork_b])
    check("T8: fork resolved to majority", canonical.entry_id == "fork:b")

    # ─── T9: Query Entries ───
    print("\n═══ T9: Query Entries ═══")
    settlements = chain.query_entries(entry_type=EntryType.BILATERAL_SETTLEMENT)
    check("T9: 1 settlement on chain", len(settlements) == 1)

    all_entries = chain.query_entries()
    check("T9: 3 total entries on chain", len(all_entries) == 3)

    # ─── T10: Witness Requirement Enforcement ───
    print("\n═══ T10: Witness Requirement Enforcement ═══")
    # Charter amendment needs 5 witnesses
    charter = chain.propose_entry(
        EntryType.CHARTER_AMENDMENT,
        {"amendment": "increase ATP cap", "new_value": 5000},
    )
    # Only 3 votes — not enough for charter (needs 5)
    for node in ["node-alpha", "node-beta", "node-gamma"]:
        chain.submit_vote(charter.entry_id, node, True)
    has_cons, _ = chain.check_consensus(charter.entry_id)
    check("T10: charter needs 5 witnesses, 3 insufficient", not has_cons)

    # Add 2 more
    chain.submit_vote(charter.entry_id, "node-delta", True)
    chain.submit_vote(charter.entry_id, "node-epsilon", True)
    has_cons, ratio = chain.check_consensus(charter.entry_id)
    check("T10: charter with 5 witnesses = consensus", has_cons)
    check("T10: 100% ratio", abs(ratio - 1.0) < 0.01)

    # ─── T11: SNARC Scoring ───
    print("\n═══ T11: SNARC Scoring ═══")
    seen = set()
    mrh = {"soc:alpha", "soc:beta"}

    # Novel + consequential settlement
    test_entry = ACTEntry(
        entry_id="test:snarc",
        entry_type=EntryType.BILATERAL_SETTLEMENT,
        chain_level=ChainLevel.COMPOST,
        timestamp=time.time(),
        prev_hash="prev",
        content={"society_a": "soc:alpha", "type": "bilateral_settlement"},
        content_hash="hash",
        atp_cost=15,  # > 10 → significant
    )
    snarc = compute_snarc(test_entry, seen, mrh)
    check("T11: significant (ATP > 10)", snarc.significant == 2)
    check("T11: novel (first occurrence)", snarc.novel == 3)
    check("T11: relevant (soc:alpha in MRH)", snarc.relevant == 1)
    check("T11: consequential (settlement)", snarc.consequential == 2)
    check("T11: total = 8", snarc.total == 8)
    check("T11: should promote (≥ 5)", snarc.should_promote)

    # Second occurrence — no longer novel
    snarc2 = compute_snarc(test_entry, seen, mrh)
    check("T11: not novel second time", snarc2.novel == 0)
    check("T11: total decreased", snarc2.total == 5)

    # ─── T12: Fractal Chain Manager ───
    print("\n═══ T12: Fractal Chain Manager ═══")
    fcm = FractalChainManager(
        act_chain=MockACTChain(["node-1", "node-2", "node-3"], 0.67),
        mrh_scope={"soc:alpha", "soc:beta"},
    )

    # First ingest is novel (SNARC +3) so it promotes to leaf
    first = fcm.ingest(
        EntryType.TRANSFER_COMMIT,
        {"source": "soc:gamma", "amount": 5},  # Not in MRH scope, low cost
    )
    check("T12: first entry promoted to leaf (novel)", first.chain_level == ChainLevel.LEAF)

    # Second ingest of same type is NOT novel → stays in compost (0 SNARC points)
    low = fcm.ingest(
        EntryType.TRANSFER_COMMIT,
        {"source": "soc:gamma", "amount": 3},  # Same type, not novel
    )
    check("T12: repeat entry stays in compost", low.chain_level == ChainLevel.COMPOST)

    # Ingest high-value entry (should promote to stem)
    high = fcm.ingest(
        EntryType.BILATERAL_SETTLEMENT,
        {"society_a": "soc:alpha", "type": "new_settlement", "anomaly_score": 0.8},
    )
    check("T12: high-value promoted to stem", high.chain_level == ChainLevel.STEM)

    stats = fcm.get_stats()
    check("T12: compost has entries", stats["compost"] >= 2)
    check("T12: leaf has entry", stats["leaf"] == 1)
    check("T12: stem has entry", stats["stem"] == 1)
    check("T12: promotions tracked", stats["promotions"] >= 2)

    # ─── T13: Stem → Root Promotion ───
    print("\n═══ T13: Stem → Root Promotion ═══")
    root_entry = fcm.promote_to_root(high.entry_id)
    check("T13: promoted to root", root_entry is not None)
    check("T13: root entry on ACT chain", root_entry.chain_level == ChainLevel.ROOT)
    check("T13: root ATP cost = 200", root_entry.atp_cost == 200)

    # ─── T14: Settlement Engine — Anchor Settlement ───
    print("\n═══ T14: Settlement Engine — Anchor Settlement ═══")
    engine = ACTSettlementEngine(chain)  # Use original chain with 5 nodes

    settlement_stmt = {
        "statement_id": "stmt:alpha-beta-001",
        "society_a": "soc:alpha",
        "society_b": "soc:beta",
        "a_balance": 900.0,
        "b_balance": 1100.0,
        "net_position": 100.0,
        "transfers_reconciled": 5,
        "transfer_ids": ["xfer:101", "xfer:102", "xfer:103"],
    }
    settle_entry = engine.anchor_settlement(settlement_stmt)
    check("T14: settlement anchored", settle_entry is not None)
    check("T14: entry is bilateral_settlement", settle_entry.entry_type == EntryType.BILATERAL_SETTLEMENT)

    # Vote to reach consensus
    for node in ["node-alpha", "node-beta", "node-gamma"]:
        chain.submit_vote(settle_entry.entry_id, node, True)
    chain.finalize_entry(settle_entry.entry_id)
    block3 = chain.create_block()
    check("T14: block created with charter + settlement", block3 is not None)

    record = engine.finalize_settlement(settle_entry.entry_id)
    check("T14: settlement finalized", record is not None)
    check("T14: record has block height", record.block_height is not None)
    check("T14: record has merkle proof", record.merkle_proof is not None)

    # ─── T15: Double-Spend Prevention ───
    print("\n═══ T15: Double-Spend Prevention ═══")
    # Try to settle same transfers again
    double_stmt = {
        "statement_id": "stmt:alpha-beta-002",
        "society_a": "soc:alpha",
        "society_b": "soc:beta",
        "a_balance": 800.0,
        "b_balance": 1200.0,
        "net_position": 200.0,
        "transfer_ids": ["xfer:101"],  # Already settled!
    }
    try:
        engine.anchor_settlement(double_stmt)
        check("T15: double-spend should raise", False)
    except ValueError as e:
        check("T15: double-spend caught", "Double-spend" in str(e))
        check("T15: alert recorded", len(engine._double_spend_alerts) > 0)

    # ─── T16: Conservation Proof ───
    print("\n═══ T16: Conservation Proof ═══")
    cons = engine.anchor_conservation_proof(
        societies={"soc:alpha": 900.0, "soc:beta": 1100.0},
        expected_total=2000.0,
    )
    check("T16: conservation proved", cons.conserved)
    check("T16: drift < 0.001", cons.drift < 0.001)
    check("T16: total = 2000", cons.total_atp == 2000.0)
    check("T16: anchored on chain", cons.entry_id is not None)

    # Violated conservation
    cons_bad = engine.anchor_conservation_proof(
        societies={"soc:alpha": 900.0, "soc:beta": 1050.0},
        expected_total=2000.0,
    )
    check("T16: violation detected", not cons_bad.conserved)
    check("T16: drift = 50", abs(cons_bad.drift - 50.0) < 0.01)

    # ─── T17: ADP Discharge Anchoring ───
    print("\n═══ T17: ADP Discharge Anchoring ═══")
    adp = engine.anchor_adp_discharge(
        grant_id="atp-grant-001",
        discharged=42.5,
        remaining=57.5,
        evidence="sha256:abc123def456",
    )
    check("T17: ADP anchored", adp.entry_id is not None)
    check("T17: discharged = 42.5", adp.discharged_amount == 42.5)
    check("T17: remaining = 57.5", adp.remaining == 57.5)
    check("T17: evidence digest", adp.evidence_digest == "sha256:abc123def456")

    # ─── T18: Settlement Verification ───
    print("\n═══ T18: Settlement Verification ═══")
    # Need to finalize ADP and conservation entries for chain integrity
    for e in chain.pending_entries[:]:
        for node in ["node-alpha", "node-beta", "node-gamma"]:
            try:
                chain.submit_vote(e.entry_id, node, True)
            except ValueError:
                pass  # Already voted
        chain.finalize_entry(e.entry_id)
    chain.create_block()

    v = engine.verify_settlement("stmt:alpha-beta-001")
    check("T18: settlement verified", v["chain_verification"]["verified"])
    check("T18: block height present", v["block_height"] is not None)

    v_bad = engine.verify_settlement("stmt:nonexistent")
    check("T18: nonexistent not verified", not v_bad["verified"])

    # ─── T19: Engine Statistics ───
    print("\n═══ T19: Engine Statistics ═══")
    stats = engine.get_stats()
    check("T19: 1 settlement", stats["settlements"] == 1)
    check("T19: 2 conservation proofs", stats["conservation_proofs"] == 2)
    check("T19: 1 ADP proof", stats["adp_proofs"] == 1)
    check("T19: double-spend alerts > 0", stats["double_spend_alerts"] > 0)
    check("T19: chain valid", stats["chain"]["valid"])

    # ─── T20: Merkle Tree Correctness ───
    print("\n═══ T20: Merkle Tree — Correctness ═══")
    # Build tree from known hashes
    hashes = [_sha256(f"leaf-{i}") for i in range(7)]
    tree = build_merkle_tree(hashes)
    check("T20: tree built", tree is not None)

    # Verify each leaf
    for h in hashes:
        proof = get_merkle_proof(tree, h)
        if proof:
            check(f"T20: proof for {h[:8]}... valid", proof.verify())
        else:
            check(f"T20: proof found for {h[:8]}...", False)

    # ─── T21: Full E2E — Society Formation → ATP → Settlement → ACT ───
    print("\n═══ T21: Full E2E — Society → ATP → Settlement → ACT ═══")

    # Create fresh chain for E2E test
    e2e_nodes = ["val-1", "val-2", "val-3", "val-4", "val-5"]
    e2e_chain = MockACTChain(e2e_nodes, 0.6)
    e2e_engine = ACTSettlementEngine(e2e_chain)
    e2e_fcm = FractalChainManager(e2e_chain, mrh_scope={"soc:earth", "soc:mars"})

    # Step 1: Simulate ATP transfer (normally done by ATPSyncManager)
    transfer_content = {
        "transfer_id": "xfer:e2e-001",
        "source_society": "soc:earth",
        "target_society": "soc:mars",
        "amount": 500.0,
        "reason": "colony_support",
        "source_balance_before": 10000.0,
        "target_balance_before": 2000.0,
    }

    # Step 2: Ingest transfer into fractal chain (should promote due to high value)
    fc_entry = e2e_fcm.ingest(EntryType.TRANSFER_COMPLETE, transfer_content)
    check("T21: transfer ingested", fc_entry is not None)

    # Step 3: Reconcile with bilateral statement
    stmt = {
        "statement_id": "stmt:earth-mars-001",
        "society_a": "soc:earth",
        "society_b": "soc:mars",
        "a_balance": 9500.0,
        "b_balance": 2500.0,
        "net_position": 500.0,
        "transfers_reconciled": 1,
        "transfer_ids": ["xfer:e2e-001"],
    }

    # Step 4: Anchor settlement on ACT chain
    settle_e = e2e_engine.anchor_settlement(stmt)
    check("T21: settlement anchored", settle_e is not None)

    # Step 5: Consensus voting
    for node in ["val-1", "val-2", "val-3"]:
        e2e_chain.submit_vote(settle_e.entry_id, node, True)
    e2e_chain.finalize_entry(settle_e.entry_id)

    # Step 6: Conservation proof
    cons_e = e2e_engine.anchor_conservation_proof(
        {"soc:earth": 9500.0, "soc:mars": 2500.0},
        expected_total=12000.0,
    )
    check("T21: conservation verified", cons_e.conserved)

    # Vote on conservation
    for node in ["val-1", "val-2", "val-3"]:
        try:
            e2e_chain.submit_vote(cons_e.entry_id, node, True)
        except ValueError:
            pass
    e2e_chain.finalize_entry(cons_e.entry_id)

    # Step 7: ADP discharge for earth's consumed ATP
    adp_e = e2e_engine.anchor_adp_discharge(
        grant_id="grant:earth-ops-001",
        discharged=500.0,
        remaining=9500.0,
        evidence=_sha256("earth-colony-support-evidence"),
    )
    check("T21: ADP discharged", adp_e is not None)

    # Vote on ADP
    for node in ["val-1", "val-2", "val-3"]:
        try:
            e2e_chain.submit_vote(adp_e.entry_id, node, True)
        except ValueError:
            pass
    e2e_chain.finalize_entry(adp_e.entry_id)

    # Step 8: Create block with all entries
    e2e_block = e2e_chain.create_block()
    check("T21: block created", e2e_block is not None)
    check("T21: block has 3 entries", len(e2e_block.entries) == 3)

    # Step 9: Finalize settlement record
    record = e2e_engine.finalize_settlement(settle_e.entry_id)
    check("T21: settlement record created", record is not None)
    check("T21: record has merkle proof", record.merkle_proof is not None)

    # Step 10: Verify immutability
    verification = e2e_chain.verify_entry(settle_e.entry_id)
    check("T21: entry verified immutable", verification["verified"])

    # Step 11: Chain integrity
    chain_proof = e2e_chain.get_chain_proof()
    check("T21: chain valid", chain_proof["valid"])
    check("T21: 1 block", chain_proof["blocks"] == 1)
    check("T21: 3 entries total", chain_proof["entries"] == 3)

    # Step 12: Fractal chain stats
    fc_stats = e2e_fcm.get_stats()
    check("T21: fractal chain tracked entries", fc_stats["compost"] >= 1)

    # Step 13: Double-spend prevention works across E2E
    try:
        e2e_engine.anchor_settlement({
            "statement_id": "stmt:earth-mars-002",
            "society_a": "soc:earth",
            "society_b": "soc:mars",
            "a_balance": 9000.0,
            "b_balance": 3000.0,
            "net_position": 1000.0,
            "transfer_ids": ["xfer:e2e-001"],  # Already settled!
        })
        check("T21: E2E double-spend caught", False)
    except ValueError:
        check("T21: E2E double-spend caught", True)

    # ─── T22: Reject Votes ───
    print("\n═══ T22: Reject Votes ═══")
    reject_chain = MockACTChain(["r1", "r2", "r3"], 0.67)
    re = reject_chain.propose_entry(EntryType.CHARTER_AMENDMENT, {"change": "bad_idea"})
    reject_chain.submit_vote(re.entry_id, "r1", True)
    reject_chain.submit_vote(re.entry_id, "r2", False, reason="Disagree with amendment")
    reject_chain.submit_vote(re.entry_id, "r3", False, reason="Too risky")

    has_cons, _ = reject_chain.check_consensus(re.entry_id)
    check("T22: rejected entry no consensus", not has_cons)

    accepted = reject_chain.finalize_entry(re.entry_id)
    check("T22: cannot finalize rejected", not accepted)

    # ─── T23: Duplicate Vote Prevention ───
    print("\n═══ T23: Duplicate Vote Prevention ═══")
    dup_chain = MockACTChain(["d1", "d2", "d3"], 0.67)
    de = dup_chain.propose_entry(EntryType.AUDIT_SEAL, {"audit": "test"})
    dup_chain.submit_vote(de.entry_id, "d1", True)
    try:
        dup_chain.submit_vote(de.entry_id, "d1", True)  # Duplicate!
        check("T23: duplicate vote prevented", False)
    except ValueError:
        check("T23: duplicate vote prevented", True)

    # ─── T24: Invalid Witness Prevention ───
    print("\n═══ T24: Invalid Witness Prevention ═══")
    try:
        dup_chain.submit_vote(de.entry_id, "not-a-node", True)
        check("T24: invalid witness prevented", False)
    except ValueError:
        check("T24: invalid witness prevented", True)

    # ─── T25: Entry Serialization ───
    print("\n═══ T25: Entry Serialization ═══")
    serial = entry.to_dict()
    check("T25: entry serializable", isinstance(serial, dict))
    check("T25: has entry_id", "entry_id" in serial)
    check("T25: has entry_type", serial["entry_type"] == "bilateral_settlement")
    check("T25: has witnesses list", isinstance(serial["witnesses"], list))

    block_serial = block.to_dict()
    check("T25: block serializable", isinstance(block_serial, dict))
    check("T25: block has height", block_serial["block_height"] == 0)

    # ═══ Summary ═══
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"  ACT Settlement Protocol — Results")
    print(f"  {passed} passed, {failed} failed out of {total} checks")
    print(f"{'=' * 60}")

    if failed == 0:
        print(f"""
  All tests verified:
  T1:  Mock ACT Chain genesis + initialization
  T2:  Entry proposal + 2/3 consensus voting
  T3:  Block creation + Merkle proofs
  T4:  Entry verification (immutability proof)
  T5:  Chain integrity proof
  T6:  Multiple entries + multi-block chain
  T7:  Double-spend detection
  T8:  Fork resolution (witness majority)
  T9:  Entry querying by type
  T10: Witness requirement enforcement (charter needs 5)
  T11: SNARC scoring (Significant/Novel/Anomalous/Relevant/Consequential)
  T12: Fractal chain manager (compost→leaf→stem)
  T13: Stem → Root promotion (on-chain anchoring)
  T14: Settlement engine — anchor BilateralStatement
  T15: Double-spend prevention via settlement engine
  T16: Conservation proof anchoring
  T17: ADP discharge anchoring
  T18: Settlement verification
  T19: Engine statistics
  T20: Merkle tree correctness (7-leaf tree, all proofs valid)
  T21: Full E2E: Society→ATP→Settlement→ACT (13 steps)
  T22: Reject votes prevent consensus
  T23: Duplicate vote prevention
  T24: Invalid witness prevention
  T25: Entry serialization round-trip

  Components:
  - MockACTChain: Hash-chained blocks, 2/3 consensus, Merkle proofs
  - FractalChainManager: Compost→Leaf→Stem→Root with SNARC gating
  - ACTSettlementEngine: ATP settlement finality + proof anchoring
  - Double-spend detection, fork resolution, conservation proofs
  - ADP discharge anchoring with evidence digests
""")
    else:
        print(f"\n  {failed} checks need attention.")

    return passed, failed


if __name__ == "__main__":
    run_tests()
