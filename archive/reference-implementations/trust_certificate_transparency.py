"""
Trust Certificate Transparency for Web4
Session 33, Track 3

CT-inspired append-only transparency logs for trust attestations:
- Merkle hash tree for verifiable attestation inclusion
- Signed Tree Head (STH) for log integrity
- Inclusion proofs (O(log n) audit path)
- Consistency proofs between two log states
- Log monitors for detecting suspicious patterns
- Gossip protocol for cross-log consistency
- Audit framework for offline verification
- Revocation and misbehavior detection
"""

import hashlib
import time
import struct
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from collections import defaultdict


# ─── Cryptographic Primitives (simplified) ───────────────────────

def h(data: bytes) -> bytes:
    """SHA-256 hash."""
    return hashlib.sha256(data).digest()


def leaf_hash(data: bytes) -> bytes:
    """Hash of a leaf node (domain separation from internal nodes)."""
    return h(b'\x00' + data)


def internal_hash(left: bytes, right: bytes) -> bytes:
    """Hash of an internal node (domain separation)."""
    return h(b'\x01' + left + right)


def entry_hash(entry_bytes: bytes) -> bytes:
    """Hash a log entry."""
    return leaf_hash(entry_bytes)


# ─── Log Entry Types ─────────────────────────────────────────────

@dataclass
class AttestationEntry:
    """A trust attestation record for the CT log."""
    entity_id: str           # LCT ID being attested
    attester_id: str         # Who made the attestation
    trust_score: float       # T3 trust score
    timestamp: float         # Unix timestamp
    evidence_type: str       # "direct", "delegation", "hardware", etc.
    signature: bytes = b""   # Attester signature (simplified)

    def serialize(self) -> bytes:
        """Serialize entry to bytes for hashing."""
        parts = [
            self.entity_id.encode(),
            b"|",
            self.attester_id.encode(),
            b"|",
            struct.pack(">d", self.trust_score),
            struct.pack(">Q", int(self.timestamp * 1000)),
            self.evidence_type.encode(),
        ]
        return b"".join(parts)

    @property
    def entry_hash_bytes(self) -> bytes:
        return entry_hash(self.serialize())


@dataclass
class RevocationEntry:
    """A trust revocation record."""
    entity_id: str
    revoker_id: str
    reason: str
    timestamp: float

    def serialize(self) -> bytes:
        return b"|".join([
            b"REV",
            self.entity_id.encode(),
            self.revoker_id.encode(),
            self.reason.encode(),
            struct.pack(">Q", int(self.timestamp * 1000)),
        ])

    @property
    def entry_hash_bytes(self) -> bytes:
        return entry_hash(self.serialize())


# ─── Merkle Tree ─────────────────────────────────────────────────

def merkle_root(leaves: List[bytes]) -> bytes:
    """Compute Merkle root of a list of leaf hashes."""
    if not leaves:
        return h(b"empty")
    if len(leaves) == 1:
        return leaves[0]

    # Pad to next power of 2 for simplicity (CT uses a different algorithm)
    while len(leaves) & (len(leaves) - 1):
        leaves = leaves + [leaves[-1]]  # duplicate last

    layer = list(leaves)
    while len(layer) > 1:
        next_layer = []
        for i in range(0, len(layer), 2):
            next_layer.append(internal_hash(layer[i], layer[i + 1]))
        layer = next_layer
    return layer[0]


def merkle_inclusion_proof(leaves: List[bytes], index: int) -> List[bytes]:
    """
    Generate an inclusion proof (audit path) for leaf at index.
    Returns list of sibling hashes from bottom to top.
    """
    if not leaves or index >= len(leaves):
        return []

    # Pad to power of 2
    size = len(leaves)
    padded = list(leaves)
    while len(padded) & (len(padded) - 1):
        padded.append(padded[-1])

    proof = []
    idx = index
    layer = list(padded)

    while len(layer) > 1:
        sibling = idx ^ 1  # XOR with 1 flips between left/right
        if sibling < len(layer):
            proof.append(layer[sibling])
        idx //= 2
        next_layer = []
        for i in range(0, len(layer), 2):
            next_layer.append(internal_hash(layer[i], layer[i + 1]))
        layer = next_layer

    return proof


def verify_inclusion_proof(leaf_hash_val: bytes, index: int,
                             proof: List[bytes], root: bytes,
                             total_leaves: int) -> bool:
    """Verify an inclusion proof against a root hash."""
    # Pad to power of 2
    size = total_leaves
    padded_size = size
    while padded_size & (padded_size - 1):
        padded_size += 1

    current = leaf_hash_val
    idx = index

    for sibling in proof:
        if idx % 2 == 0:
            current = internal_hash(current, sibling)
        else:
            current = internal_hash(sibling, current)
        idx //= 2

    return current == root


def merkle_consistency_proof(old_size: int, new_size: int,
                               leaves: List[bytes]) -> Tuple[bytes, bytes, bool]:
    """
    Simplified consistency proof: verify that new log extends old log
    without modifying existing entries. Returns (old_root, new_root, consistent).
    """
    if old_size > len(leaves) or new_size > len(leaves):
        return b"", b"", False
    if old_size > new_size:
        return b"", b"", False

    old_root = merkle_root(leaves[:old_size])
    new_root = merkle_root(leaves[:new_size])

    # Verify that old entries are unchanged prefix of new log
    # (In real CT this uses a proof; here we verify directly)
    return old_root, new_root, True  # consistent by construction


# ─── Signed Tree Head ────────────────────────────────────────────

@dataclass
class SignedTreeHead:
    """Log state commitment (analogous to CT STH)."""
    tree_size: int
    timestamp: float
    root_hash: bytes
    log_id: str
    # In production: would include digital signature
    signature: bytes = b""

    def serialize(self) -> bytes:
        return struct.pack(">QQ", self.tree_size, int(self.timestamp * 1000)) + \
               self.root_hash + self.log_id.encode()

    @property
    def sth_hash(self) -> bytes:
        return h(self.serialize())


# ─── Transparency Log ────────────────────────────────────────────

class TrustTransparencyLog:
    """
    Append-only trust attestation log with Merkle tree integrity.
    """

    def __init__(self, log_id: str):
        self.log_id = log_id
        self.entries: List[object] = []          # Raw entry objects
        self.leaf_hashes: List[bytes] = []       # Hash of each entry
        self.sth_history: List[SignedTreeHead] = []
        self._entity_index: Dict[str, List[int]] = defaultdict(list)

    @property
    def size(self) -> int:
        return len(self.entries)

    def append(self, entry) -> Tuple[int, bytes]:
        """
        Append an entry. Returns (index, leaf_hash).
        """
        idx = len(self.entries)
        lh = entry.entry_hash_bytes
        self.entries.append(entry)
        self.leaf_hashes.append(lh)

        # Track entity
        if hasattr(entry, 'entity_id'):
            self._entity_index[entry.entity_id].append(idx)

        return idx, lh

    def get_sth(self) -> SignedTreeHead:
        """Get current Signed Tree Head."""
        root = merkle_root(self.leaf_hashes) if self.leaf_hashes else h(b"empty")
        sth = SignedTreeHead(
            tree_size=self.size,
            timestamp=time.time(),
            root_hash=root,
            log_id=self.log_id,
        )
        self.sth_history.append(sth)
        return sth

    def get_inclusion_proof(self, index: int) -> Tuple[bytes, List[bytes]]:
        """Get inclusion proof for entry at index. Returns (leaf_hash, proof)."""
        if index >= self.size:
            return b"", []
        lh = self.leaf_hashes[index]
        proof = merkle_inclusion_proof(self.leaf_hashes, index)
        return lh, proof

    def verify_inclusion(self, index: int, root: bytes) -> bool:
        """Verify that entry at index is included in log with given root."""
        if index >= self.size:
            return False
        lh, proof = self.get_inclusion_proof(index)
        return verify_inclusion_proof(lh, index, proof, root, self.size)

    def get_entity_entries(self, entity_id: str) -> List[Tuple[int, object]]:
        """Get all log entries for a specific entity."""
        indices = self._entity_index.get(entity_id, [])
        return [(i, self.entries[i]) for i in indices]

    def is_append_only(self, old_sth: SignedTreeHead) -> bool:
        """Verify log is consistent with older STH (append-only check)."""
        if old_sth.tree_size > self.size:
            return False
        old_root, _, consistent = merkle_consistency_proof(
            old_sth.tree_size, self.size, self.leaf_hashes
        )
        return consistent and old_root == old_sth.root_hash


# ─── Log Monitor ─────────────────────────────────────────────────

@dataclass
class MonitorAlert:
    """Alert generated by log monitor."""
    alert_type: str
    entity_id: str
    detail: str
    severity: str  # "info", "warning", "critical"


class TrustLogMonitor:
    """
    Monitors the transparency log for suspicious patterns:
    - Rapid trust score changes
    - Multiple revocations in short time
    - Conflicting attestations from same attester
    - Trust inflation attacks
    """

    def __init__(self, log: TrustTransparencyLog):
        self.log = log
        self.alerts: List[MonitorAlert] = []

    def check_trust_volatility(self, entity_id: str,
                                window_secs: float = 3600.0,
                                threshold: float = 0.3) -> List[MonitorAlert]:
        """Alert if trust score changes by > threshold within window."""
        entries = self.log.get_entity_entries(entity_id)
        alerts = []

        attestations = [(e for e in entries if isinstance(e[1], AttestationEntry))]
        atts = [(i, e) for i, e in entries if isinstance(e, AttestationEntry)]

        if len(atts) < 2:
            return []

        # Check consecutive pairs within window
        for j in range(1, len(atts)):
            i1, e1 = atts[j-1]
            i2, e2 = atts[j]
            if e2.timestamp - e1.timestamp <= window_secs:
                delta = abs(e2.trust_score - e1.trust_score)
                if delta > threshold:
                    alerts.append(MonitorAlert(
                        "trust_volatility", entity_id,
                        f"score changed by {delta:.3f} in {e2.timestamp - e1.timestamp:.0f}s",
                        "warning"
                    ))

        return alerts

    def check_conflicting_attestations(self, entity_id: str) -> List[MonitorAlert]:
        """Alert if same attester gives conflicting scores within same time window."""
        entries = [(i, e) for i, e in self.log.get_entity_entries(entity_id)
                   if isinstance(e, AttestationEntry)]
        alerts = []

        attester_scores: Dict[str, List[float]] = defaultdict(list)
        for _, e in entries:
            attester_scores[e.attester_id].append(e.trust_score)

        for attester, scores in attester_scores.items():
            if len(scores) >= 2:
                spread = max(scores) - min(scores)
                if spread > 0.5:
                    alerts.append(MonitorAlert(
                        "conflicting_attestation", entity_id,
                        f"attester {attester} gave scores ranging {min(scores):.2f}–{max(scores):.2f}",
                        "critical"
                    ))

        return alerts

    def check_revocation_flood(self, window_secs: float = 300.0,
                                threshold: int = 5) -> List[MonitorAlert]:
        """Alert if too many revocations happen in a short window."""
        revocations = [(e.timestamp, e.entity_id)
                       for e in self.log.entries if isinstance(e, RevocationEntry)]
        if len(revocations) < threshold:
            return []

        # Sort by time
        revocations.sort()
        alerts = []
        for i in range(threshold - 1, len(revocations)):
            window_start = revocations[i - threshold + 1][0]
            window_end = revocations[i][0]
            if window_end - window_start <= window_secs:
                alerts.append(MonitorAlert(
                    "revocation_flood", "GLOBAL",
                    f"{threshold} revocations in {window_end - window_start:.0f}s",
                    "critical"
                ))
                break  # Report once

        return alerts

    def run_all_checks(self, entity_ids: List[str]) -> List[MonitorAlert]:
        """Run all monitoring checks."""
        all_alerts = []
        for eid in entity_ids:
            all_alerts.extend(self.check_trust_volatility(eid))
            all_alerts.extend(self.check_conflicting_attestations(eid))
        all_alerts.extend(self.check_revocation_flood())
        self.alerts.extend(all_alerts)
        return all_alerts


# ─── Cross-Log Gossip ────────────────────────────────────────────

def gossip_check(log_a: TrustTransparencyLog,
                  log_b: TrustTransparencyLog) -> Dict[str, bool]:
    """
    Gossip consistency check between two logs.
    Both should contain the same entries if they share an entity.
    Returns consistency report.
    """
    report = {}

    # Get common entities
    entities_a = set(log_a._entity_index.keys())
    entities_b = set(log_b._entity_index.keys())
    common = entities_a & entities_b

    for eid in common:
        entries_a = {(i, e.entry_hash_bytes) for i, e in log_a.get_entity_entries(eid)}
        entries_b = {(i, e.entry_hash_bytes) for i, e in log_b.get_entity_entries(eid)}
        # Check that at least entry hashes agree (in real CT, logs should match)
        hashes_a = {h for _, h in entries_a}
        hashes_b = {h for _, h in entries_b}
        report[eid] = len(hashes_a & hashes_b) > 0

    return report


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
    print("Trust Certificate Transparency for Web4")
    print("Session 33, Track 3")
    print("=" * 70)

    T = 1741500000.0  # fixed base timestamp

    # ── §1 Log Entry Serialization ───────────────────────────────
    print("\n§1 Log Entry Serialization\n")

    e1 = AttestationEntry("lct:alice", "lct:bob", 0.85, T, "direct")
    e2 = AttestationEntry("lct:alice", "lct:carol", 0.78, T + 100, "delegation")
    e3 = RevocationEntry("lct:mallory", "lct:admin", "compromised", T + 200)

    check("entry_serializable", len(e1.serialize()) > 0)
    check("entry_hash_deterministic", e1.entry_hash_bytes == e1.entry_hash_bytes)
    check("different_entries_different_hashes", e1.entry_hash_bytes != e2.entry_hash_bytes)
    check("revocation_hash_differs", e1.entry_hash_bytes != e3.entry_hash_bytes)

    # ── §2 Merkle Tree ───────────────────────────────────────────
    print("\n§2 Merkle Tree\n")

    leaves = [h(str(i).encode()) for i in range(8)]
    root = merkle_root(leaves)

    check("root_is_bytes", isinstance(root, bytes) and len(root) == 32)

    # Same leaves → same root
    root2 = merkle_root(list(leaves))
    check("root_deterministic", root == root2)

    # Different leaves → different root
    leaves_mod = list(leaves)
    leaves_mod[3] = h(b"modified")
    root_mod = merkle_root(leaves_mod)
    check("modified_changes_root", root != root_mod)

    # Single leaf
    root_single = merkle_root([leaves[0]])
    check("single_leaf_root", root_single == leaves[0])

    # ── §3 Inclusion Proofs ──────────────────────────────────────
    print("\n§3 Inclusion Proofs\n")

    for i in [0, 1, 3, 7]:
        proof = merkle_inclusion_proof(leaves, i)
        verified = verify_inclusion_proof(leaves[i], i, proof, root, len(leaves))
        check(f"inclusion_proof_leaf_{i}", verified)

    # Wrong leaf fails verification
    bad_leaf = h(b"wrong")
    proof_0 = merkle_inclusion_proof(leaves, 0)
    check("wrong_leaf_fails", not verify_inclusion_proof(bad_leaf, 0, proof_0, root, len(leaves)))

    # Wrong root fails
    check("wrong_root_fails", not verify_inclusion_proof(
        leaves[0], 0, proof_0, h(b"wrong_root"), len(leaves)))

    # ── §4 Transparency Log Operations ───────────────────────────
    print("\n§4 Transparency Log Operations\n")

    log = TrustTransparencyLog("web4-trust-log-1")
    entries_list = [
        AttestationEntry("lct:alice", "lct:bob", 0.8, T, "direct"),
        AttestationEntry("lct:bob", "lct:carol", 0.75, T + 50, "delegation"),
        AttestationEntry("lct:alice", "lct:carol", 0.85, T + 100, "direct"),
        RevocationEntry("lct:mallory", "lct:admin", "sybil", T + 150),
        AttestationEntry("lct:carol", "lct:dave", 0.9, T + 200, "hardware"),
    ]

    for entry in entries_list:
        log.append(entry)

    check("log_size", log.size == 5)
    sth1 = log.get_sth()
    check("sth_tree_size", sth1.tree_size == 5)
    check("sth_hash_non_empty", len(sth1.root_hash) == 32)

    # Inclusion verification
    for i in range(5):
        check(f"log_inclusion_{i}", log.verify_inclusion(i, sth1.root_hash))

    # Entity index
    alice_entries = log.get_entity_entries("lct:alice")
    check("alice_has_entries", len(alice_entries) == 2)
    check("alice_entry_types", all(isinstance(e, AttestationEntry) for _, e in alice_entries))

    # ── §5 Consistency Proof ─────────────────────────────────────
    print("\n§5 Consistency Proof (Append-Only)\n")

    # Record old STH at size 3
    old_leaves = list(log.leaf_hashes[:3])
    old_root_check = merkle_root(old_leaves)
    old_sth = SignedTreeHead(3, T, old_root_check, "web4-trust-log-1")

    # Verify log is consistent with old STH
    check("append_only_consistent", log.is_append_only(old_sth))

    # A tampered old STH should fail
    tampered_sth = SignedTreeHead(3, T, h(b"tampered"), "web4-trust-log-1")
    check("tampered_sth_fails", not log.is_append_only(tampered_sth))

    # ── §6 Monitor Checks ────────────────────────────────────────
    print("\n§6 Monitor Checks\n")

    monitor = TrustLogMonitor(log)

    # No volatility for alice (scores: 0.8, 0.85 — small change)
    vol_alerts = monitor.check_trust_volatility("lct:alice", window_secs=3600, threshold=0.3)
    check("no_volatility_alice", len(vol_alerts) == 0)

    # Build a log with volatility
    log2 = TrustTransparencyLog("web4-trust-log-2")
    log2.append(AttestationEntry("lct:volatile", "lct:x", 0.9, T, "direct"))
    log2.append(AttestationEntry("lct:volatile", "lct:y", 0.2, T + 10, "direct"))  # big drop
    mon2 = TrustLogMonitor(log2)
    vol_alerts2 = mon2.check_trust_volatility("lct:volatile", window_secs=3600, threshold=0.3)
    check("volatility_detected", len(vol_alerts2) > 0)

    # Conflicting attestations
    log3 = TrustTransparencyLog("web4-trust-log-3")
    log3.append(AttestationEntry("lct:target", "lct:attester1", 0.9, T, "direct"))
    log3.append(AttestationEntry("lct:target", "lct:attester1", 0.1, T + 60, "direct"))  # conflict
    mon3 = TrustLogMonitor(log3)
    conf_alerts = mon3.check_conflicting_attestations("lct:target")
    check("conflict_detected", len(conf_alerts) > 0)
    check("conflict_is_critical", conf_alerts[0].severity == "critical")

    # Revocation flood
    log4 = TrustTransparencyLog("web4-trust-log-4")
    for i in range(8):
        log4.append(RevocationEntry(f"lct:entity{i}", "lct:admin", "batch_revoke", T + i))
    mon4 = TrustLogMonitor(log4)
    flood_alerts = mon4.check_revocation_flood(window_secs=300, threshold=5)
    check("revocation_flood_detected", len(flood_alerts) > 0)

    # ── §7 Gossip Consistency ────────────────────────────────────
    print("\n§7 Gossip Consistency\n")

    # Two logs share some entries
    log_a = TrustTransparencyLog("log-a")
    log_b = TrustTransparencyLog("log-b")

    shared_entry = AttestationEntry("lct:shared", "lct:src", 0.8, T, "direct")
    log_a.append(shared_entry)
    log_b.append(shared_entry)

    # Both have same hash for shared entity
    report = gossip_check(log_a, log_b)
    check("gossip_consistent", report.get("lct:shared", False))

    # Entity only in one log
    log_a.append(AttestationEntry("lct:only_a", "lct:src", 0.7, T + 10, "direct"))
    report2 = gossip_check(log_a, log_b)
    check("unique_entity_not_in_report", "lct:only_a" not in report2)

    # ── §8 STH Signature (Hash Integrity) ───────────────────────
    print("\n§8 STH Integrity\n")

    sth_a = log.get_sth()
    sth_b = log.get_sth()

    # Same log state → same root hash (even if timestamps differ)
    check("same_root_same_log", sth_a.root_hash == sth_b.root_hash)

    # After appending new entry, root changes
    log.append(AttestationEntry("lct:new", "lct:src", 0.77, T + 300, "direct"))
    sth_c = log.get_sth()
    check("root_changes_after_append", sth_c.root_hash != sth_a.root_hash)
    check("size_increments", sth_c.tree_size == sth_a.tree_size + 1)

    # Old entries still verify with new log
    check("old_entries_still_valid",
          all(log.verify_inclusion(i, sth_c.root_hash) for i in range(5)))

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
