"""
Trust Evidence Chains for Web4
Session 31, Track 8

Formal evidence-based trust reasoning:
- Evidence types (direct observation, attestation, delegation, reputation)
- Evidence chain construction and validation
- Evidence strength and freshness decay
- Chain of custody for trust claims
- Evidence conflict resolution
- Provenance tracking
- Evidence graph analysis (reachability, cycles, roots)
- Aggregate evidence scoring
"""

import math
import hashlib
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Set


# ─── Evidence Types ───────────────────────────────────────────────

class EvidenceType(Enum):
    DIRECT_OBSERVATION = "direct"    # First-hand interaction
    ATTESTATION = "attestation"      # Third-party claim
    DELEGATION = "delegation"        # Trust transferred
    REPUTATION = "reputation"        # Aggregate community signal
    HARDWARE = "hardware"            # Hardware-bound evidence (TPM etc)


# Evidence weight by type (higher = more trustworthy)
EVIDENCE_WEIGHTS = {
    EvidenceType.HARDWARE: 1.0,
    EvidenceType.DIRECT_OBSERVATION: 0.9,
    EvidenceType.ATTESTATION: 0.7,
    EvidenceType.DELEGATION: 0.5,
    EvidenceType.REPUTATION: 0.3,
}


@dataclass
class Evidence:
    evidence_id: str
    evidence_type: EvidenceType
    source: str          # who provides the evidence
    subject: str         # about whom
    trust_claim: float   # claimed trust value [0,1]
    timestamp: int       # when created
    source_trust: float = 1.0  # trust in the source itself

    @property
    def effective_strength(self) -> float:
        """Evidence strength = type weight × source trust."""
        return EVIDENCE_WEIGHTS[self.evidence_type] * self.source_trust

    def freshness(self, current_time: int, half_life: int = 100) -> float:
        """Decay factor based on age of evidence."""
        age = current_time - self.timestamp
        if age <= 0:
            return 1.0
        return math.exp(-math.log(2) * age / half_life)

    def weighted_claim(self, current_time: int, half_life: int = 100) -> float:
        """Trust claim weighted by strength and freshness."""
        return self.trust_claim * self.effective_strength * self.freshness(current_time, half_life)


# ─── Evidence Chain ───────────────────────────────────────────────

@dataclass
class EvidenceChain:
    """Ordered chain of evidence supporting a trust claim."""
    chain: List[Evidence] = field(default_factory=list)

    def add(self, evidence: Evidence):
        self.chain.append(evidence)

    def chain_strength(self, current_time: int) -> float:
        """
        Chain strength is the product of link strengths (weakest link principle).
        Longer chains are inherently weaker.
        """
        if not self.chain:
            return 0.0
        strength = 1.0
        for e in self.chain:
            strength *= e.effective_strength * e.freshness(current_time)
        return strength

    def chain_trust(self, current_time: int) -> float:
        """
        Aggregate trust claim from chain.
        Final claim = last link's claim × chain strength.
        """
        if not self.chain:
            return 0.0
        return self.chain[-1].trust_claim * self.chain_strength(current_time)

    def validate(self) -> Tuple[bool, str]:
        """Validate chain integrity: each link's subject must be next link's source."""
        if len(self.chain) <= 1:
            return True, "ok"

        for i in range(len(self.chain) - 1):
            if self.chain[i].subject != self.chain[i + 1].source:
                return False, f"break at link {i}: {self.chain[i].subject} ≠ {self.chain[i+1].source}"

        return True, "ok"

    @property
    def depth(self) -> int:
        return len(self.chain)


# ─── Evidence Graph ───────────────────────────────────────────────

@dataclass
class EvidenceGraph:
    """Graph of all evidence relationships."""
    evidence: Dict[str, Evidence] = field(default_factory=dict)
    # source → [(evidence_id, subject)]
    edges: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)

    def add_evidence(self, e: Evidence):
        self.evidence[e.evidence_id] = e
        if e.source not in self.edges:
            self.edges[e.source] = []
        self.edges[e.source].append((e.evidence_id, e.subject))

    def find_paths(self, source: str, target: str,
                   max_depth: int = 5) -> List[EvidenceChain]:
        """Find all evidence chains from source to target."""
        chains: List[EvidenceChain] = []
        self._dfs(source, target, [], set(), max_depth, chains)
        return chains

    def _dfs(self, current: str, target: str,
             path: List[Evidence], visited: Set[str],
             max_depth: int, result: List[EvidenceChain]):
        if len(path) >= max_depth:
            return

        if current == target and path:
            chain = EvidenceChain(chain=list(path))
            result.append(chain)
            return

        if current in visited:
            return

        visited.add(current)
        for eid, subject in self.edges.get(current, []):
            e = self.evidence[eid]
            path.append(e)
            self._dfs(subject, target, path, visited, max_depth, result)
            path.pop()
        visited.remove(current)

    def find_roots(self) -> Set[str]:
        """Find evidence roots: sources with no incoming evidence."""
        all_subjects = set()
        all_sources = set()
        for e in self.evidence.values():
            all_subjects.add(e.subject)
            all_sources.add(e.source)
        return all_sources - all_subjects

    def detect_cycles(self) -> bool:
        """Check if evidence graph has cycles (circular trust)."""
        visited: Set[str] = set()
        in_stack: Set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            in_stack.add(node)
            for _, subject in self.edges.get(node, []):
                if subject not in visited:
                    if dfs(subject):
                        return True
                elif subject in in_stack:
                    return True
            in_stack.remove(node)
            return False

        for node in list(self.edges.keys()):
            if node not in visited:
                if dfs(node):
                    return True
        return False


# ─── Evidence Conflict Resolution ─────────────────────────────────

def resolve_conflicts(evidence_list: List[Evidence],
                      current_time: int) -> float:
    """
    Resolve conflicting evidence about same subject.
    Weight-average by effective strength and freshness.
    """
    if not evidence_list:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for e in evidence_list:
        w = e.effective_strength * e.freshness(current_time)
        weighted_sum += e.trust_claim * w
        total_weight += w

    if total_weight <= 0:
        return 0.0

    return weighted_sum / total_weight


def evidence_agreement(evidence_list: List[Evidence]) -> float:
    """
    Measure how much evidence agrees (low variance = high agreement).
    Returns agreement score [0,1] where 1 = perfect agreement.
    """
    if len(evidence_list) <= 1:
        return 1.0

    claims = [e.trust_claim for e in evidence_list]
    mean = sum(claims) / len(claims)
    variance = sum((c - mean) ** 2 for c in claims) / len(claims)
    # Max possible variance for [0,1] is 0.25
    return 1.0 - min(1.0, variance / 0.25)


# ─── Provenance ───────────────────────────────────────────────────

def compute_provenance_hash(evidence: Evidence) -> str:
    """Compute content hash for evidence provenance."""
    content = f"{evidence.source}:{evidence.subject}:{evidence.trust_claim}:{evidence.timestamp}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def verify_provenance_chain(chain: EvidenceChain) -> bool:
    """Verify that evidence chain has valid provenance (no gaps)."""
    if not chain.chain:
        return True

    # Timestamps must be non-decreasing
    for i in range(len(chain.chain) - 1):
        if chain.chain[i].timestamp > chain.chain[i + 1].timestamp:
            return False

    return True


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
    print("Trust Evidence Chains for Web4")
    print("Session 31, Track 8")
    print("=" * 70)

    # ── §1 Evidence Types & Strength ────────────────────────────
    print("\n§1 Evidence Types & Strength\n")

    e_hw = Evidence("e1", EvidenceType.HARDWARE, "tpm", "device_a", 0.95, 100)
    e_direct = Evidence("e2", EvidenceType.DIRECT_OBSERVATION, "alice", "bob", 0.8, 100)
    e_attest = Evidence("e3", EvidenceType.ATTESTATION, "carol", "bob", 0.7, 100)
    e_rep = Evidence("e4", EvidenceType.REPUTATION, "network", "bob", 0.6, 100)

    # Hardware > Direct > Attestation > Reputation
    check("hw_strongest", e_hw.effective_strength > e_direct.effective_strength)
    check("direct_gt_attest", e_direct.effective_strength > e_attest.effective_strength)
    check("attest_gt_rep", e_attest.effective_strength > e_rep.effective_strength)

    # Source trust reduces strength
    e_untrusted = Evidence("e5", EvidenceType.DIRECT_OBSERVATION, "eve", "bob",
                           0.9, 100, source_trust=0.3)
    check("untrusted_weaker", e_untrusted.effective_strength < e_direct.effective_strength,
          f"untrusted={e_untrusted.effective_strength:.2f} direct={e_direct.effective_strength:.2f}")

    # ── §2 Evidence Freshness ───────────────────────────────────
    print("\n§2 Evidence Freshness\n")

    e = Evidence("f1", EvidenceType.DIRECT_OBSERVATION, "alice", "bob", 0.8, 0)

    fresh = e.freshness(0)
    check("fresh_at_creation", abs(fresh - 1.0) < 0.01)

    at_half_life = e.freshness(100)
    check("half_fresh_at_halflife", abs(at_half_life - 0.5) < 0.05,
          f"freshness={at_half_life:.4f}")

    old = e.freshness(500)
    check("old_evidence_weak", old < 0.1,
          f"freshness={old:.4f}")

    # Weighted claim decays with time
    wc_fresh = e.weighted_claim(0)
    wc_old = e.weighted_claim(200)
    check("weighted_claim_decays", wc_fresh > wc_old,
          f"fresh={wc_fresh:.4f} old={wc_old:.4f}")

    # ── §3 Evidence Chain ───────────────────────────────────────
    print("\n§3 Evidence Chain Construction\n")

    chain = EvidenceChain()
    chain.add(Evidence("c1", EvidenceType.DIRECT_OBSERVATION,
                       "alice", "bob", 0.9, 50))
    chain.add(Evidence("c2", EvidenceType.ATTESTATION,
                       "bob", "carol", 0.8, 60))
    chain.add(Evidence("c3", EvidenceType.DELEGATION,
                       "carol", "dave", 0.7, 70))

    check("chain_depth_3", chain.depth == 3)

    valid, msg = chain.validate()
    check("chain_valid", valid, msg)

    # Chain strength decreases with length
    short_chain = EvidenceChain()
    short_chain.add(Evidence("s1", EvidenceType.DIRECT_OBSERVATION,
                             "alice", "bob", 0.9, 50))
    check("shorter_stronger",
          short_chain.chain_strength(100) > chain.chain_strength(100),
          f"short={short_chain.chain_strength(100):.4f} long={chain.chain_strength(100):.4f}")

    # Invalid chain (broken link)
    bad_chain = EvidenceChain()
    bad_chain.add(Evidence("b1", EvidenceType.DIRECT_OBSERVATION,
                           "alice", "bob", 0.9, 50))
    bad_chain.add(Evidence("b2", EvidenceType.ATTESTATION,
                           "carol", "dave", 0.8, 60))  # carol ≠ bob
    valid_bad, _ = bad_chain.validate()
    check("broken_chain_invalid", not valid_bad)

    # ── §4 Evidence Graph ───────────────────────────────────────
    print("\n§4 Evidence Graph\n")

    graph = EvidenceGraph()
    graph.add_evidence(Evidence("g1", EvidenceType.DIRECT_OBSERVATION,
                                "alice", "bob", 0.8, 10))
    graph.add_evidence(Evidence("g2", EvidenceType.ATTESTATION,
                                "bob", "carol", 0.7, 20))
    graph.add_evidence(Evidence("g3", EvidenceType.ATTESTATION,
                                "alice", "carol", 0.75, 15))
    graph.add_evidence(Evidence("g4", EvidenceType.DELEGATION,
                                "carol", "dave", 0.6, 30))

    # Find paths from alice to dave
    paths = graph.find_paths("alice", "dave")
    check("paths_found", len(paths) >= 2,
          f"paths={len(paths)}")

    # Roots (alice has no incoming)
    roots = graph.find_roots()
    check("root_is_alice", "alice" in roots,
          f"roots={roots}")

    # No cycles in DAG
    check("no_cycles", not graph.detect_cycles())

    # Add cycle: dave → alice
    graph.add_evidence(Evidence("g5", EvidenceType.REPUTATION,
                                "dave", "alice", 0.5, 40))
    check("cycle_detected", graph.detect_cycles())

    # ── §5 Conflict Resolution ──────────────────────────────────
    print("\n§5 Evidence Conflict Resolution\n")

    # Agreeing evidence
    agreeing = [
        Evidence("a1", EvidenceType.DIRECT_OBSERVATION, "s1", "target", 0.8, 90),
        Evidence("a2", EvidenceType.DIRECT_OBSERVATION, "s2", "target", 0.75, 95),
        Evidence("a3", EvidenceType.ATTESTATION, "s3", "target", 0.82, 92),
    ]
    resolved = resolve_conflicts(agreeing, 100)
    check("agreeing_near_mean", 0.7 < resolved < 0.85,
          f"resolved={resolved:.4f}")

    agreement = evidence_agreement(agreeing)
    check("high_agreement", agreement > 0.9,
          f"agreement={agreement:.4f}")

    # Conflicting evidence
    conflicting = [
        Evidence("c1", EvidenceType.DIRECT_OBSERVATION, "s1", "target", 0.9, 90),
        Evidence("c2", EvidenceType.DIRECT_OBSERVATION, "s2", "target", 0.1, 95),
    ]
    conflict_agreement = evidence_agreement(conflicting)
    check("low_agreement", conflict_agreement < 0.5,
          f"agreement={conflict_agreement:.4f}")

    # Fresher evidence has more weight
    old_new = [
        Evidence("on1", EvidenceType.DIRECT_OBSERVATION, "s1", "target", 0.3, 0),    # old, low trust
        Evidence("on2", EvidenceType.DIRECT_OBSERVATION, "s2", "target", 0.9, 95),   # recent, high trust
    ]
    resolved_time = resolve_conflicts(old_new, 100)
    check("fresher_dominates", resolved_time > 0.6,
          f"resolved={resolved_time:.4f}")

    # ── §6 Provenance ──────────────────────────────────────────
    print("\n§6 Provenance Tracking\n")

    e1 = Evidence("p1", EvidenceType.DIRECT_OBSERVATION, "alice", "bob", 0.8, 100)
    e2 = Evidence("p2", EvidenceType.DIRECT_OBSERVATION, "alice", "bob", 0.8, 100)
    e3 = Evidence("p3", EvidenceType.DIRECT_OBSERVATION, "alice", "bob", 0.7, 100)

    h1 = compute_provenance_hash(e1)
    h2 = compute_provenance_hash(e2)
    h3 = compute_provenance_hash(e3)

    # Same content → same hash
    check("same_content_same_hash", h1 == h2)
    # Different content → different hash
    check("diff_content_diff_hash", h1 != h3)

    # Valid provenance chain (timestamps increasing)
    prov_chain = EvidenceChain()
    prov_chain.add(Evidence("pc1", EvidenceType.DIRECT_OBSERVATION,
                            "alice", "bob", 0.8, 10))
    prov_chain.add(Evidence("pc2", EvidenceType.ATTESTATION,
                            "bob", "carol", 0.7, 20))
    check("provenance_valid", verify_provenance_chain(prov_chain))

    # Invalid provenance (timestamp goes backward)
    bad_prov = EvidenceChain()
    bad_prov.add(Evidence("bp1", EvidenceType.DIRECT_OBSERVATION,
                          "alice", "bob", 0.8, 50))
    bad_prov.add(Evidence("bp2", EvidenceType.ATTESTATION,
                          "bob", "carol", 0.7, 30))  # before previous!
    check("provenance_invalid", not verify_provenance_chain(bad_prov))

    # ── §7 Aggregate Scoring ───────────────────────────────────
    print("\n§7 Aggregate Evidence Scoring\n")

    # Multiple evidence sources about same entity
    all_evidence = [
        Evidence("ae1", EvidenceType.HARDWARE, "tpm1", "server", 0.95, 90),
        Evidence("ae2", EvidenceType.DIRECT_OBSERVATION, "monitor", "server", 0.85, 95),
        Evidence("ae3", EvidenceType.ATTESTATION, "auditor", "server", 0.80, 80),
        Evidence("ae4", EvidenceType.REPUTATION, "network", "server", 0.70, 50),
    ]

    score = resolve_conflicts(all_evidence, 100)
    check("aggregate_reasonable", 0.7 < score < 0.95,
          f"score={score:.4f}")

    # Hardware evidence should pull score up
    no_hw = [e for e in all_evidence if e.evidence_type != EvidenceType.HARDWARE]
    score_no_hw = resolve_conflicts(no_hw, 100)
    check("hw_increases_score", score > score_no_hw,
          f"with_hw={score:.4f} without={score_no_hw:.4f}")

    # Agreement is high when evidence aligns
    check("aligned_agreement", evidence_agreement(all_evidence) > 0.7,
          f"agreement={evidence_agreement(all_evidence):.4f}")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
