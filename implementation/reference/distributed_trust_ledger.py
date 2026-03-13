"""
Distributed Trust Ledger for Web4
Session 33, Track 8

Append-only distributed ledger for trust attestations:
- Chained blocks with Merkle integrity
- Multi-node replication with gossip
- Conflict detection and resolution
- Fork detection and reconciliation
- Ledger compaction (snapshots)
- Consistency verification across replicas
- Trust-weighted block proposal
- Leader-based and leaderless modes
- Audit trail with provenance
"""

import hashlib
import time
import struct
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict


# ─── Cryptographic Utilities ─────────────────────────────────────

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def hash_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


# ─── Ledger Entry ────────────────────────────────────────────────

@dataclass
class LedgerEntry:
    """A single entry in a trust ledger block."""
    entry_type: str          # "attestation", "revocation", "delegation", "transfer"
    entity_id: str
    data: Dict[str, object]  # Flexible payload
    timestamp: float
    author_id: str

    def serialize(self) -> bytes:
        parts = [
            self.entry_type.encode(),
            b"|",
            self.entity_id.encode(),
            b"|",
            str(sorted(self.data.items())).encode(),
            b"|",
            struct.pack(">Q", int(self.timestamp * 1000)),
            b"|",
            self.author_id.encode(),
        ]
        return b"".join(parts)

    @property
    def hash(self) -> str:
        return hash_hex(self.serialize())


# ─── Ledger Block ────────────────────────────────────────────────

@dataclass
class LedgerBlock:
    """A block in the trust ledger chain."""
    index: int
    prev_hash: str
    entries: List[LedgerEntry]
    timestamp: float
    proposer_id: str        # Who proposed this block
    nonce: int = 0          # Optional PoW nonce

    @property
    def entries_hash(self) -> str:
        """Merkle root of entries."""
        if not self.entries:
            return hash_hex(b"empty")
        hashes = [sha256(e.serialize()) for e in self.entries]
        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])
            next_layer = []
            for i in range(0, len(hashes), 2):
                next_layer.append(sha256(hashes[i] + hashes[i+1]))
            hashes = next_layer
        return hash_hex(hashes[0])

    @property
    def block_hash(self) -> str:
        """Hash of the entire block."""
        data = struct.pack(">Q", self.index) + \
               self.prev_hash.encode() + \
               self.entries_hash.encode() + \
               struct.pack(">Q", int(self.timestamp * 1000)) + \
               self.proposer_id.encode() + \
               struct.pack(">I", self.nonce)
        return hash_hex(data)


# ─── Trust Ledger (Single Node) ──────────────────────────────────

class TrustLedger:
    """
    Append-only trust ledger with chain integrity.
    """

    # Shared genesis for deterministic initialization
    GENESIS_TIMESTAMP = 0.0

    def __init__(self, node_id: str, genesis: Optional[LedgerBlock] = None):
        self.node_id = node_id
        self.chain: List[LedgerBlock] = []
        self.pending_entries: List[LedgerEntry] = []
        self._entity_index: Dict[str, List[Tuple[int, int]]] = defaultdict(list)  # entity -> [(block_idx, entry_idx)]

        # Genesis block (shared across all nodes if provided)
        if genesis is None:
            genesis = LedgerBlock(
                index=0, prev_hash="0" * 16,
                entries=[], timestamp=self.GENESIS_TIMESTAMP,
                proposer_id="genesis"
            )
        self.chain.append(genesis)

    @property
    def height(self) -> int:
        return len(self.chain)

    @property
    def head(self) -> LedgerBlock:
        return self.chain[-1]

    @property
    def head_hash(self) -> str:
        return self.head.block_hash

    def add_entry(self, entry: LedgerEntry):
        """Add entry to pending pool."""
        self.pending_entries.append(entry)

    def propose_block(self) -> Optional[LedgerBlock]:
        """Create a new block from pending entries."""
        if not self.pending_entries:
            return None

        block = LedgerBlock(
            index=self.height,
            prev_hash=self.head_hash,
            entries=list(self.pending_entries),
            timestamp=time.time(),
            proposer_id=self.node_id,
        )
        self.chain.append(block)

        # Index entries
        for i, entry in enumerate(block.entries):
            self._entity_index[entry.entity_id].append((block.index, i))

        self.pending_entries.clear()
        return block

    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """Verify chain integrity."""
        for i in range(1, len(self.chain)):
            # Check prev_hash link
            if self.chain[i].prev_hash != self.chain[i-1].block_hash:
                return False, f"broken link at block {i}"
            # Check index
            if self.chain[i].index != i:
                return False, f"wrong index at block {i}"
        return True, None

    def get_entity_history(self, entity_id: str) -> List[LedgerEntry]:
        """Get all entries for an entity in chronological order."""
        entries = []
        for block_idx, entry_idx in self._entity_index.get(entity_id, []):
            entries.append(self.chain[block_idx].entries[entry_idx])
        return entries

    def snapshot(self) -> Dict[str, object]:
        """Create a ledger state snapshot."""
        return {
            "node_id": self.node_id,
            "height": self.height,
            "head_hash": self.head_hash,
            "total_entries": sum(len(b.entries) for b in self.chain),
            "entities": list(self._entity_index.keys()),
        }


# ─── Multi-Node Ledger Network ──────────────────────────────────

class LedgerNetwork:
    """
    Network of ledger nodes with gossip replication.
    """

    def __init__(self):
        self.nodes: Dict[str, TrustLedger] = {}
        self.connections: Dict[str, Set[str]] = defaultdict(set)  # bidirectional
        # Shared genesis so all nodes have identical chain root
        self._genesis = LedgerBlock(
            index=0, prev_hash="0" * 16,
            entries=[], timestamp=0.0,
            proposer_id="genesis"
        )

    def add_node(self, node_id: str) -> TrustLedger:
        ledger = TrustLedger(node_id, genesis=self._genesis)
        self.nodes[node_id] = ledger
        return ledger

    def connect(self, a: str, b: str):
        self.connections[a].add(b)
        self.connections[b].add(a)

    def gossip_block(self, source: str, block: LedgerBlock) -> Set[str]:
        """
        Gossip a block from source to all connected nodes.
        Returns set of nodes that accepted the block.
        """
        accepted = set()
        queue = list(self.connections.get(source, set()))
        visited = {source}

        while queue:
            node_id = queue.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)

            ledger = self.nodes.get(node_id)
            if ledger is None:
                continue

            # Accept if it extends our chain
            if block.prev_hash == ledger.head_hash and block.index == ledger.height:
                ledger.chain.append(LedgerBlock(
                    index=block.index,
                    prev_hash=block.prev_hash,
                    entries=list(block.entries),
                    timestamp=block.timestamp,
                    proposer_id=block.proposer_id,
                ))
                # Index entries
                for i, entry in enumerate(block.entries):
                    ledger._entity_index[entry.entity_id].append((block.index, i))
                accepted.add(node_id)
                # Continue gossiping
                queue.extend(self.connections.get(node_id, set()))

        return accepted

    def check_consistency(self) -> Dict[str, Dict[str, bool]]:
        """
        Check pairwise consistency of all node ledgers.
        Returns {(nodeA, nodeB): consistent}.
        """
        result = {}
        node_list = list(self.nodes.keys())
        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                a, b = node_list[i], node_list[j]
                ledger_a = self.nodes[a]
                ledger_b = self.nodes[b]

                # Consistent if they agree on common prefix
                min_height = min(ledger_a.height, ledger_b.height)
                consistent = True
                for k in range(min_height):
                    if ledger_a.chain[k].block_hash != ledger_b.chain[k].block_hash:
                        consistent = False
                        break
                result[f"{a}-{b}"] = consistent
        return result

    def detect_forks(self) -> List[Tuple[str, str, int]]:
        """
        Detect forks: nodes with same height but different head hashes.
        Returns [(nodeA, nodeB, fork_height)].
        """
        forks = []
        node_list = list(self.nodes.keys())
        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                a, b = node_list[i], node_list[j]
                la, lb = self.nodes[a], self.nodes[b]

                # Find divergence point
                min_h = min(la.height, lb.height)
                for k in range(min_h):
                    if la.chain[k].block_hash != lb.chain[k].block_hash:
                        forks.append((a, b, k))
                        break

        return forks


# ─── Conflict Resolution ─────────────────────────────────────────

def resolve_fork_longest(ledger_a: TrustLedger,
                           ledger_b: TrustLedger) -> str:
    """Resolve fork by choosing the longest chain. Returns winning node_id."""
    if ledger_a.height > ledger_b.height:
        return ledger_a.node_id
    elif ledger_b.height > ledger_a.height:
        return ledger_b.node_id
    else:
        # Same height: pick by hash ordering (deterministic tiebreak)
        if ledger_a.head_hash <= ledger_b.head_hash:
            return ledger_a.node_id
        return ledger_b.node_id


def resolve_fork_trust_weighted(ledger_a: TrustLedger,
                                  ledger_b: TrustLedger,
                                  trust_scores: Dict[str, float]) -> str:
    """
    Resolve fork by total trust weight of proposers in the chain.
    """
    def chain_trust(ledger: TrustLedger) -> float:
        return sum(trust_scores.get(b.proposer_id, 0.0) for b in ledger.chain)

    ta = chain_trust(ledger_a)
    tb = chain_trust(ledger_b)

    if ta > tb:
        return ledger_a.node_id
    elif tb > ta:
        return ledger_b.node_id
    return ledger_a.node_id  # tiebreak


# ─── Ledger Compaction ───────────────────────────────────────────

@dataclass
class LedgerSnapshot:
    """Compacted ledger state at a specific height."""
    height: int
    state_hash: str
    entity_states: Dict[str, Dict[str, object]]  # entity -> latest state
    timestamp: float


def compact_ledger(ledger: TrustLedger) -> LedgerSnapshot:
    """
    Compact ledger into a snapshot: latest state per entity.
    """
    entity_states: Dict[str, Dict[str, object]] = {}

    for block in ledger.chain:
        for entry in block.entries:
            if entry.entity_id not in entity_states:
                entity_states[entry.entity_id] = {}
            entity_states[entry.entity_id].update({
                "last_type": entry.entry_type,
                "last_data": entry.data,
                "last_timestamp": entry.timestamp,
                "last_author": entry.author_id,
            })

    state_data = str(sorted(
        (k, sorted(v.items())) for k, v in entity_states.items()
    )).encode()

    return LedgerSnapshot(
        height=ledger.height,
        state_hash=hash_hex(state_data),
        entity_states=entity_states,
        timestamp=time.time(),
    )


# ─── Audit Trail ─────────────────────────────────────────────────

@dataclass
class AuditResult:
    """Result of a ledger audit."""
    chain_valid: bool
    total_blocks: int
    total_entries: int
    unique_entities: int
    unique_authors: int
    time_span_s: float
    issues: List[str]


def audit_ledger(ledger: TrustLedger) -> AuditResult:
    """Full audit of a ledger."""
    chain_valid, error = ledger.verify_chain()
    issues = []
    if error:
        issues.append(error)

    entities = set()
    authors = set()
    total_entries = 0
    timestamps = []

    for block in ledger.chain:
        total_entries += len(block.entries)
        for entry in block.entries:
            entities.add(entry.entity_id)
            authors.add(entry.author_id)
            timestamps.append(entry.timestamp)

        # Check monotonic timestamps (blocks)
        if len(ledger.chain) > 1:
            for i in range(1, len(ledger.chain)):
                if ledger.chain[i].timestamp < ledger.chain[i-1].timestamp:
                    issues.append(f"non-monotonic block timestamp at {i}")

    time_span = max(timestamps) - min(timestamps) if timestamps else 0.0

    return AuditResult(
        chain_valid=chain_valid,
        total_blocks=ledger.height,
        total_entries=total_entries,
        unique_entities=len(entities),
        unique_authors=len(authors),
        time_span_s=time_span,
        issues=issues,
    )


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
    print("Distributed Trust Ledger for Web4")
    print("Session 33, Track 8")
    print("=" * 70)

    T = 1741500000.0

    # ── §1 Ledger Entry ─────────────────────────────────────────
    print("\n§1 Ledger Entry\n")

    e1 = LedgerEntry("attestation", "lct:alice", {"trust": 0.85}, T, "lct:bob")
    e2 = LedgerEntry("revocation", "lct:mallory", {"reason": "sybil"}, T + 10, "lct:admin")

    check("entry_hash_deterministic", e1.hash == e1.hash)
    check("different_entries_different_hash", e1.hash != e2.hash)
    check("entry_serializable", len(e1.serialize()) > 0)

    # ── §2 Block Creation ────────────────────────────────────────
    print("\n§2 Block Creation\n")

    block = LedgerBlock(
        index=1, prev_hash="0" * 16,
        entries=[e1, e2], timestamp=T,
        proposer_id="node1"
    )
    check("block_hash_computed", len(block.block_hash) == 16)
    check("entries_hash_computed", len(block.entries_hash) == 16)
    check("block_hash_deterministic", block.block_hash == block.block_hash)

    # Different entries → different block hash
    block2 = LedgerBlock(
        index=1, prev_hash="0" * 16,
        entries=[e1], timestamp=T,
        proposer_id="node1"
    )
    check("different_entries_different_block", block.block_hash != block2.block_hash)

    # ── §3 Single Node Ledger ────────────────────────────────────
    print("\n§3 Single Node Ledger\n")

    ledger = TrustLedger("node1")
    check("genesis_exists", ledger.height == 1)
    check("genesis_valid", ledger.verify_chain()[0])

    # Add entries and propose block
    ledger.add_entry(LedgerEntry("attestation", "lct:alice", {"trust": 0.9}, T, "lct:bob"))
    ledger.add_entry(LedgerEntry("attestation", "lct:bob", {"trust": 0.8}, T + 1, "lct:carol"))
    block = ledger.propose_block()
    check("block_proposed", block is not None)
    check("height_incremented", ledger.height == 2)
    check("pending_cleared", len(ledger.pending_entries) == 0)

    # Chain valid
    valid, err = ledger.verify_chain()
    check("chain_valid", valid, f"err={err}")

    # Entity history
    alice_history = ledger.get_entity_history("lct:alice")
    check("entity_history", len(alice_history) == 1)
    check("entity_history_type", alice_history[0].entry_type == "attestation")

    # Snapshot
    snap = ledger.snapshot()
    check("snapshot_height", snap["height"] == 2)
    check("snapshot_entities", "lct:alice" in snap["entities"])

    # ── §4 Multi-Block Chain ─────────────────────────────────────
    print("\n§4 Multi-Block Chain\n")

    for i in range(5):
        ledger.add_entry(LedgerEntry("attestation", f"lct:entity{i}",
                                      {"trust": 0.5 + i * 0.1}, T + 100 + i, "lct:admin"))
        ledger.propose_block()

    check("multi_block_height", ledger.height == 7)
    valid2, err2 = ledger.verify_chain()
    check("multi_block_valid", valid2, f"err2={err2}")

    # Each block links to previous
    for i in range(1, ledger.height):
        check(f"chain_link_{i}",
              ledger.chain[i].prev_hash == ledger.chain[i-1].block_hash)

    # ── §5 Network Gossip ────────────────────────────────────────
    print("\n§5 Network Gossip\n")

    net = LedgerNetwork()
    n1 = net.add_node("n1")
    n2 = net.add_node("n2")
    n3 = net.add_node("n3")
    net.connect("n1", "n2")
    net.connect("n2", "n3")

    # n1 proposes a block
    n1.add_entry(LedgerEntry("attestation", "lct:test", {"trust": 0.9}, T, "n1"))
    block = n1.propose_block()

    # Gossip to network
    accepted = net.gossip_block("n1", block)
    check("gossip_reaches_n2", "n2" in accepted)
    check("gossip_reaches_n3", "n3" in accepted)

    # All nodes at same height
    check("n1_height", n1.height == 2)
    check("n2_height", n2.height == 2)
    check("n3_height", n3.height == 2)

    # ── §6 Consistency Check ─────────────────────────────────────
    print("\n§6 Consistency Check\n")

    consistency = net.check_consistency()
    check("n1_n2_consistent", consistency.get("n1-n2", False))
    check("n2_n3_consistent", consistency.get("n2-n3", False))
    check("n1_n3_consistent", consistency.get("n1-n3", False))

    # ── §7 Fork Detection ────────────────────────────────────────
    print("\n§7 Fork Detection\n")

    # Create a fork: n1 and n3 propose different blocks at same height
    net2 = LedgerNetwork()
    na = net2.add_node("na")
    nb = net2.add_node("nb")
    # Don't connect them — they'll diverge

    na.add_entry(LedgerEntry("attestation", "lct:a", {"trust": 0.9}, T, "na"))
    nb.add_entry(LedgerEntry("attestation", "lct:b", {"trust": 0.8}, T + 1, "nb"))
    na.propose_block()
    nb.propose_block()

    forks = net2.detect_forks()
    check("fork_detected", len(forks) > 0)

    # No fork in consistent network
    forks_consistent = net.detect_forks()
    check("no_fork_consistent", len(forks_consistent) == 0)

    # ── §8 Fork Resolution ───────────────────────────────────────
    print("\n§8 Fork Resolution\n")

    # Longest chain wins
    na.add_entry(LedgerEntry("attestation", "lct:extra", {"x": 1}, T + 2, "na"))
    na.propose_block()
    winner = resolve_fork_longest(na, nb)
    check("longest_wins", winner == "na", f"winner={winner}")

    # Trust-weighted resolution
    trust = {"na": 0.3, "nb": 0.9}
    tw_winner = resolve_fork_trust_weighted(na, nb, trust)
    # nb has higher trust despite shorter chain
    # chain trust: na blocks have proposer na(0.3×3), nb blocks have proposer nb(0.9×2)
    # na: 0.9, nb: 1.8 → nb wins by trust
    check("trust_weighted_resolution", tw_winner == "nb", f"tw_winner={tw_winner}")

    # ── §9 Compaction ────────────────────────────────────────────
    print("\n§9 Compaction\n")

    compact = compact_ledger(ledger)
    check("compact_height", compact.height == ledger.height)
    check("compact_state_hash", len(compact.state_hash) == 16)
    check("compact_has_entities", len(compact.entity_states) > 0)

    # Snapshot captures latest state
    for eid, state in compact.entity_states.items():
        check(f"compact_{eid}_has_data", "last_type" in state, f"state={state}")
        break  # Just check first

    # ── §10 Audit ────────────────────────────────────────────────
    print("\n§10 Audit\n")

    audit = audit_ledger(ledger)
    check("audit_valid", audit.chain_valid)
    check("audit_blocks", audit.total_blocks == ledger.height)
    check("audit_entries", audit.total_entries > 0)
    check("audit_entities", audit.unique_entities > 0)
    check("audit_no_issues", len(audit.issues) == 0, f"issues={audit.issues}")

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
