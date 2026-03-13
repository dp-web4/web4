"""
Trust Ontology Reasoning for Web4
Session 33, Track 5

RDFS/OWL-style inference over trust relationships:
- RDF triple store with subject-predicate-object
- RDFS subclass/subproperty inference
- Domain/range constraint checking
- Transitive property inference (trust delegation chains)
- Symmetric property handling (mutual attestation)
- Inverse property reasoning
- Trust-specific OWL restrictions (cardinality, value)
- Entailment checking and reasoning closure
- Consistency detection (contradictory trust assertions)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, FrozenSet
from collections import defaultdict
from enum import Enum, auto


# ─── RDF Triple Store ────────────────────────────────────────────

@dataclass(frozen=True)
class Triple:
    """An RDF triple (subject, predicate, object)."""
    subject: str
    predicate: str
    object: str

    def __repr__(self):
        return f"({self.subject} {self.predicate} {self.object})"


class TripleStore:
    """Simple RDF triple store with pattern matching."""

    def __init__(self):
        self.triples: Set[Triple] = set()
        # Indices
        self._spo: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        self._pos: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        self._osp: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))

    def add(self, s: str, p: str, o: str) -> bool:
        """Add a triple. Returns True if new."""
        t = Triple(s, p, o)
        if t in self.triples:
            return False
        self.triples.add(t)
        self._spo[s][p].add(o)
        self._pos[p][o].add(s)
        self._osp[o][s].add(p)
        return True

    def remove(self, s: str, p: str, o: str) -> bool:
        """Remove a triple. Returns True if existed."""
        t = Triple(s, p, o)
        if t not in self.triples:
            return False
        self.triples.remove(t)
        self._spo[s][p].discard(o)
        self._pos[p][o].discard(s)
        self._osp[o][s].discard(p)
        return True

    def match(self, s: Optional[str] = None, p: Optional[str] = None,
              o: Optional[str] = None) -> Set[Triple]:
        """Pattern match triples. None means wildcard."""
        if s and p and o:
            t = Triple(s, p, o)
            return {t} if t in self.triples else set()
        if s and p:
            return {Triple(s, p, obj) for obj in self._spo.get(s, {}).get(p, set())}
        if p and o:
            return {Triple(subj, p, o) for subj in self._pos.get(p, {}).get(o, set())}
        if s and o:
            return {Triple(s, pred, o) for pred in self._osp.get(o, {}).get(s, set())}
        if s:
            result = set()
            for pred, objs in self._spo.get(s, {}).items():
                for obj in objs:
                    result.add(Triple(s, pred, obj))
            return result
        if p:
            result = set()
            for obj, subjs in self._pos.get(p, {}).items():
                for subj in subjs:
                    result.add(Triple(subj, p, obj))
            return result
        if o:
            result = set()
            for subj, preds in self._osp.get(o, {}).items():
                for pred in preds:
                    result.add(Triple(subj, pred, o))
            return result
        return set(self.triples)

    @property
    def size(self) -> int:
        return len(self.triples)

    def contains(self, s: str, p: str, o: str) -> bool:
        return Triple(s, p, o) in self.triples


# ─── RDFS/OWL Vocabulary Constants ───────────────────────────────

RDFS_SUBCLASS = "rdfs:subClassOf"
RDFS_SUBPROPERTY = "rdfs:subPropertyOf"
RDFS_DOMAIN = "rdfs:domain"
RDFS_RANGE = "rdfs:range"
RDF_TYPE = "rdf:type"
OWL_TRANSITIVE = "owl:TransitiveProperty"
OWL_SYMMETRIC = "owl:SymmetricProperty"
OWL_INVERSE = "owl:inverseOf"
OWL_FUNCTIONAL = "owl:FunctionalProperty"
OWL_DISJOINT = "owl:disjointWith"
OWL_SAME_AS = "owl:sameAs"

# Web4-specific
W4_TRUSTS = "web4:trusts"
W4_ATTESTS = "web4:attests"
W4_DELEGATES = "web4:delegatesTo"
W4_HAS_TRUST = "web4:hasTrustScore"
W4_HAS_LCT = "web4:hasLCT"
W4_ENTITY = "web4:Entity"
W4_AGENT = "web4:Agent"
W4_HUMAN = "web4:Human"
W4_AI_AGENT = "web4:AIAgent"
W4_ATTESTATION = "web4:Attestation"


# ─── RDFS Reasoner ───────────────────────────────────────────────

class RDFSReasoner:
    """
    Forward-chaining RDFS/OWL reasoner for trust ontologies.
    Applies inference rules to derive new triples.
    """

    def __init__(self, store: TripleStore):
        self.store = store
        self.inferred: Set[Triple] = set()

    def _add_inferred(self, s: str, p: str, o: str) -> bool:
        """Add an inferred triple."""
        t = Triple(s, p, o)
        if t in self.inferred or t in self.store.triples:
            return False
        self.inferred.add(t)
        self.store.add(s, p, o)
        return True

    def apply_subclass(self) -> int:
        """
        RDFS rule: if A rdfs:subClassOf B and X rdf:type A → X rdf:type B
        """
        count = 0
        subclass_triples = self.store.match(p=RDFS_SUBCLASS)
        for sc in subclass_triples:
            sub, sup = sc.subject, sc.object
            instances = self.store.match(p=RDF_TYPE, o=sub)
            for inst in instances:
                if self._add_inferred(inst.subject, RDF_TYPE, sup):
                    count += 1
        return count

    def apply_subproperty(self) -> int:
        """
        RDFS rule: if P rdfs:subPropertyOf Q and X P Y → X Q Y
        """
        count = 0
        subprop_triples = self.store.match(p=RDFS_SUBPROPERTY)
        for sp in subprop_triples:
            sub, sup = sp.subject, sp.object
            usages = self.store.match(p=sub)
            for usage in usages:
                if self._add_inferred(usage.subject, sup, usage.object):
                    count += 1
        return count

    def apply_transitive(self) -> int:
        """
        OWL rule: if P rdf:type owl:TransitiveProperty and X P Y and Y P Z → X P Z
        """
        count = 0
        trans_props = {t.subject for t in self.store.match(p=RDF_TYPE, o=OWL_TRANSITIVE)}
        for prop in trans_props:
            triples = self.store.match(p=prop)
            # Build adjacency from these triples
            adj: Dict[str, Set[str]] = defaultdict(set)
            for t in triples:
                adj[t.subject].add(t.object)

            # Compute transitive closure
            for x in list(adj.keys()):
                visited = set()
                stack = list(adj[x])
                while stack:
                    y = stack.pop()
                    if y in visited:
                        continue
                    visited.add(y)
                    if self._add_inferred(x, prop, y):
                        count += 1
                    for z in adj.get(y, set()):
                        if z not in visited:
                            stack.append(z)
        return count

    def apply_symmetric(self) -> int:
        """
        OWL rule: if P rdf:type owl:SymmetricProperty and X P Y → Y P X
        """
        count = 0
        sym_props = {t.subject for t in self.store.match(p=RDF_TYPE, o=OWL_SYMMETRIC)}
        for prop in sym_props:
            triples = list(self.store.match(p=prop))
            for t in triples:
                if self._add_inferred(t.object, prop, t.subject):
                    count += 1
        return count

    def apply_inverse(self) -> int:
        """
        OWL rule: if P owl:inverseOf Q and X P Y → Y Q X
        """
        count = 0
        inverse_triples = self.store.match(p=OWL_INVERSE)
        for inv in inverse_triples:
            prop_a, prop_b = inv.subject, inv.object
            for t in list(self.store.match(p=prop_a)):
                if self._add_inferred(t.object, prop_b, t.subject):
                    count += 1
            for t in list(self.store.match(p=prop_b)):
                if self._add_inferred(t.object, prop_a, t.subject):
                    count += 1
        return count

    def apply_domain_range(self) -> int:
        """
        RDFS rule: if P rdfs:domain C and X P Y → X rdf:type C
                   if P rdfs:range C and X P Y → Y rdf:type C
        """
        count = 0
        for d in self.store.match(p=RDFS_DOMAIN):
            prop, cls = d.subject, d.object
            for t in self.store.match(p=prop):
                if self._add_inferred(t.subject, RDF_TYPE, cls):
                    count += 1
        for r in self.store.match(p=RDFS_RANGE):
            prop, cls = r.subject, r.object
            for t in self.store.match(p=prop):
                if self._add_inferred(t.object, RDF_TYPE, cls):
                    count += 1
        return count

    def compute_closure(self, max_iterations: int = 20) -> int:
        """
        Apply all inference rules until fixed point.
        Returns total number of inferred triples.
        """
        total = 0
        for _ in range(max_iterations):
            n = 0
            n += self.apply_subclass()
            n += self.apply_subproperty()
            n += self.apply_transitive()
            n += self.apply_symmetric()
            n += self.apply_inverse()
            n += self.apply_domain_range()
            if n == 0:
                break
            total += n
        return total


# ─── Consistency Checker ─────────────────────────────────────────

@dataclass
class ConsistencyViolation:
    """A detected inconsistency in the trust ontology."""
    violation_type: str
    detail: str
    triples: List[Triple]


def check_consistency(store: TripleStore) -> List[ConsistencyViolation]:
    """
    Check for logical inconsistencies in trust assertions.
    """
    violations = []

    # 1. Functional property violation: X P Y and X P Z where Y != Z
    func_props = {t.subject for t in store.match(p=RDF_TYPE, o=OWL_FUNCTIONAL)}
    for prop in func_props:
        values: Dict[str, Set[str]] = defaultdict(set)
        for t in store.match(p=prop):
            values[t.subject].add(t.object)
        for subj, objs in values.items():
            if len(objs) > 1:
                violations.append(ConsistencyViolation(
                    "functional_violation",
                    f"{subj} has multiple values for functional property {prop}: {objs}",
                    [Triple(subj, prop, o) for o in objs]
                ))

    # 2. Disjoint class violation: X rdf:type A and X rdf:type B where A disjointWith B
    disjoint_pairs = [(t.subject, t.object) for t in store.match(p=OWL_DISJOINT)]
    for cls_a, cls_b in disjoint_pairs:
        instances_a = {t.subject for t in store.match(p=RDF_TYPE, o=cls_a)}
        instances_b = {t.subject for t in store.match(p=RDF_TYPE, o=cls_b)}
        common = instances_a & instances_b
        for x in common:
            violations.append(ConsistencyViolation(
                "disjoint_violation",
                f"{x} is instance of both disjoint classes {cls_a} and {cls_b}",
                [Triple(x, RDF_TYPE, cls_a), Triple(x, RDF_TYPE, cls_b)]
            ))

    # 3. Trust-specific: self-attestation (entity attests itself)
    for t in store.match(p=W4_ATTESTS):
        if t.subject == t.object:
            violations.append(ConsistencyViolation(
                "self_attestation",
                f"{t.subject} attests itself",
                [t]
            ))

    return violations


# ─── Trust Query Helpers ─────────────────────────────────────────

def who_trusts(store: TripleStore, entity: str) -> Set[str]:
    """Find all entities that trust the given entity."""
    return {t.subject for t in store.match(p=W4_TRUSTS, o=entity)}


def trusted_by(store: TripleStore, entity: str) -> Set[str]:
    """Find all entities trusted by the given entity."""
    return {t.object for t in store.match(s=entity, p=W4_TRUSTS)}


def trust_chain(store: TripleStore, source: str, target: str,
                max_depth: int = 5) -> Optional[List[str]]:
    """Find a trust chain from source to target via transitive trust."""
    visited = set()
    queue = [(source, [source])]

    while queue:
        current, path = queue.pop(0)
        if current == target:
            return path
        if current in visited or len(path) > max_depth:
            continue
        visited.add(current)

        for next_entity in trusted_by(store, current):
            if next_entity not in visited:
                queue.append((next_entity, path + [next_entity]))

    return None


def entities_of_type(store: TripleStore, type_uri: str) -> Set[str]:
    """Find all entities of a given type (including subclass inference)."""
    return {t.subject for t in store.match(p=RDF_TYPE, o=type_uri)}


# ── Web4 Trust Ontology Builder ──────────────────────────────────

def build_web4_trust_ontology() -> TripleStore:
    """Build the core Web4 trust ontology."""
    store = TripleStore()

    # Class hierarchy
    store.add(W4_HUMAN, RDFS_SUBCLASS, W4_AGENT)
    store.add(W4_AI_AGENT, RDFS_SUBCLASS, W4_AGENT)
    store.add(W4_AGENT, RDFS_SUBCLASS, W4_ENTITY)

    # Property characteristics
    store.add(W4_TRUSTS, RDF_TYPE, OWL_TRANSITIVE)
    store.add(W4_ATTESTS, RDFS_DOMAIN, W4_AGENT)
    store.add(W4_ATTESTS, RDFS_RANGE, W4_ENTITY)
    store.add(W4_DELEGATES, RDF_TYPE, OWL_TRANSITIVE)

    # Disjoint: Human and AIAgent
    store.add(W4_HUMAN, OWL_DISJOINT, W4_AI_AGENT)

    # Functional: each entity has exactly one LCT
    store.add(W4_HAS_LCT, RDF_TYPE, OWL_FUNCTIONAL)

    return store


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
    print("Trust Ontology Reasoning for Web4")
    print("Session 33, Track 5")
    print("=" * 70)

    # ── §1 Triple Store Basics ───────────────────────────────────
    print("\n§1 Triple Store Basics\n")

    store = TripleStore()
    added = store.add("alice", "trusts", "bob")
    check("add_triple", added)
    check("store_size_1", store.size == 1)

    added2 = store.add("alice", "trusts", "bob")
    check("no_duplicate", not added2)
    check("store_size_still_1", store.size == 1)

    store.add("bob", "trusts", "carol")
    store.add("alice", "knows", "carol")
    check("store_size_3", store.size == 3)

    # Pattern matching
    check("match_spo", len(store.match("alice", "trusts", "bob")) == 1)
    check("match_sp", len(store.match(s="alice", p="trusts")) == 1)
    check("match_po", len(store.match(p="trusts", o="carol")) == 1)
    check("match_p_only", len(store.match(p="trusts")) == 2)
    check("match_s_only", len(store.match(s="alice")) == 2)
    check("match_all", len(store.match()) == 3)
    check("contains", store.contains("alice", "trusts", "bob"))
    check("not_contains", not store.contains("carol", "trusts", "alice"))

    # Remove
    removed = store.remove("alice", "knows", "carol")
    check("remove_success", removed)
    check("store_size_after_remove", store.size == 2)
    removed2 = store.remove("x", "y", "z")
    check("remove_nonexistent", not removed2)

    # ── §2 Subclass Inference ────────────────────────────────────
    print("\n§2 Subclass Inference\n")

    store2 = TripleStore()
    store2.add(W4_HUMAN, RDFS_SUBCLASS, W4_AGENT)
    store2.add(W4_AGENT, RDFS_SUBCLASS, W4_ENTITY)
    store2.add("alice", RDF_TYPE, W4_HUMAN)

    reasoner = RDFSReasoner(store2)
    n_subclass = reasoner.apply_subclass()
    check("subclass_inferred", n_subclass > 0)
    check("alice_is_agent", store2.contains("alice", RDF_TYPE, W4_AGENT))

    # Second round: transitive subclass (Human → Agent → Entity)
    n2 = reasoner.apply_subclass()
    check("transitive_subclass", store2.contains("alice", RDF_TYPE, W4_ENTITY))

    # ── §3 Transitive Property ───────────────────────────────────
    print("\n§3 Transitive Property Inference\n")

    store3 = TripleStore()
    store3.add(W4_TRUSTS, RDF_TYPE, OWL_TRANSITIVE)
    store3.add("alice", W4_TRUSTS, "bob")
    store3.add("bob", W4_TRUSTS, "carol")
    store3.add("carol", W4_TRUSTS, "dave")

    reasoner3 = RDFSReasoner(store3)
    n_trans = reasoner3.apply_transitive()
    check("transitive_inferred", n_trans > 0)
    check("alice_trusts_carol", store3.contains("alice", W4_TRUSTS, "carol"))
    check("alice_trusts_dave", store3.contains("alice", W4_TRUSTS, "dave"))
    check("bob_trusts_dave", store3.contains("bob", W4_TRUSTS, "dave"))

    # ── §4 Symmetric Property ───────────────────────────────────
    print("\n§4 Symmetric Property Inference\n")

    store4 = TripleStore()
    store4.add("web4:mutualAttestation", RDF_TYPE, OWL_SYMMETRIC)
    store4.add("alice", "web4:mutualAttestation", "bob")

    reasoner4 = RDFSReasoner(store4)
    n_sym = reasoner4.apply_symmetric()
    check("symmetric_inferred", n_sym == 1)
    check("bob_attests_alice", store4.contains("bob", "web4:mutualAttestation", "alice"))

    # ── §5 Inverse Property ──────────────────────────────────────
    print("\n§5 Inverse Property Inference\n")

    store5 = TripleStore()
    store5.add("web4:attestedBy", OWL_INVERSE, W4_ATTESTS)
    store5.add("alice", W4_ATTESTS, "bob")

    reasoner5 = RDFSReasoner(store5)
    n_inv = reasoner5.apply_inverse()
    check("inverse_inferred", n_inv > 0)
    check("bob_attested_by_alice", store5.contains("bob", "web4:attestedBy", "alice"))

    # ── §6 Domain/Range ──────────────────────────────────────────
    print("\n§6 Domain/Range Inference\n")

    store6 = TripleStore()
    store6.add(W4_ATTESTS, RDFS_DOMAIN, W4_AGENT)
    store6.add(W4_ATTESTS, RDFS_RANGE, W4_ENTITY)
    store6.add("alice", W4_ATTESTS, "server42")

    reasoner6 = RDFSReasoner(store6)
    n_dr = reasoner6.apply_domain_range()
    check("domain_inferred", n_dr >= 1)
    check("alice_is_agent", store6.contains("alice", RDF_TYPE, W4_AGENT))
    check("server_is_entity", store6.contains("server42", RDF_TYPE, W4_ENTITY))

    # ── §7 Full Closure ──────────────────────────────────────────
    print("\n§7 Full Reasoning Closure\n")

    store7 = build_web4_trust_ontology()
    # Add instances
    store7.add("alice", RDF_TYPE, W4_HUMAN)
    store7.add("gpt4", RDF_TYPE, W4_AI_AGENT)
    store7.add("alice", W4_TRUSTS, "bob")
    store7.add("bob", W4_TRUSTS, "carol")
    store7.add("alice", W4_ATTESTS, "gpt4")
    store7.add("alice", W4_HAS_LCT, "lct:alice-001")

    reasoner7 = RDFSReasoner(store7)
    total_inferred = reasoner7.compute_closure()
    check("closure_inferred", total_inferred > 0, f"inferred={total_inferred}")

    # Check inferences
    check("alice_is_entity_via_chain",
          store7.contains("alice", RDF_TYPE, W4_ENTITY))
    check("alice_trusts_carol_transitive",
          store7.contains("alice", W4_TRUSTS, "carol"))
    check("alice_is_agent_via_attests",
          store7.contains("alice", RDF_TYPE, W4_AGENT))

    # ── §8 Consistency Checking ──────────────────────────────────
    print("\n§8 Consistency Checking\n")

    # Disjoint violation: entity is both Human and AIAgent
    store8 = build_web4_trust_ontology()
    store8.add("hybrid", RDF_TYPE, W4_HUMAN)
    store8.add("hybrid", RDF_TYPE, W4_AI_AGENT)
    violations = check_consistency(store8)
    disjoint_violations = [v for v in violations if v.violation_type == "disjoint_violation"]
    check("disjoint_detected", len(disjoint_violations) > 0)

    # Functional property violation: two LCTs
    store8.add("alice", W4_HAS_LCT, "lct:alice-001")
    store8.add("alice", W4_HAS_LCT, "lct:alice-002")
    violations2 = check_consistency(store8)
    func_violations = [v for v in violations2 if v.violation_type == "functional_violation"]
    check("functional_violation_detected", len(func_violations) > 0)

    # Self-attestation
    store8.add("bad_entity", W4_ATTESTS, "bad_entity")
    violations3 = check_consistency(store8)
    self_att = [v for v in violations3 if v.violation_type == "self_attestation"]
    check("self_attestation_detected", len(self_att) > 0)

    # Clean store has no violations
    clean = build_web4_trust_ontology()
    clean.add("alice", RDF_TYPE, W4_HUMAN)
    clean.add("alice", W4_HAS_LCT, "lct:alice")
    check("clean_no_violations", len(check_consistency(clean)) == 0)

    # ── §9 Trust Queries ─────────────────────────────────────────
    print("\n§9 Trust Queries\n")

    store9 = TripleStore()
    store9.add("alice", W4_TRUSTS, "bob")
    store9.add("alice", W4_TRUSTS, "carol")
    store9.add("bob", W4_TRUSTS, "carol")
    store9.add("dave", W4_TRUSTS, "carol")

    check("who_trusts_carol", who_trusts(store9, "carol") == {"alice", "bob", "dave"})
    check("alice_trusts", trusted_by(store9, "alice") == {"bob", "carol"})

    # Trust chain
    store9.add("carol", W4_TRUSTS, "eve")
    chain = trust_chain(store9, "alice", "eve")
    check("trust_chain_found", chain is not None and chain[0] == "alice" and chain[-1] == "eve")
    check("trust_chain_length", len(chain) <= 4)  # alice→bob/carol→eve or alice→carol→eve

    # No chain
    no_chain = trust_chain(store9, "eve", "alice")
    check("no_reverse_chain", no_chain is None)

    # Type query
    store9.add("alice", RDF_TYPE, W4_HUMAN)
    store9.add("gpt", RDF_TYPE, W4_AI_AGENT)
    humans = entities_of_type(store9, W4_HUMAN)
    check("humans_query", humans == {"alice"})

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
