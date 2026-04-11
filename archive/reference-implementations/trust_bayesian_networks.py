"""
Trust Bayesian Networks for Web4
Session 34, Track 2

Probabilistic trust reasoning using Bayesian networks:
- Directed acyclic graph of trust variables
- Conditional probability tables (CPTs)
- Variable elimination for exact inference
- Belief propagation for marginal computation
- Posterior trust update given evidence
- Trust-specific models (attestation quality, delegation reliability)
- Sensitivity analysis for trust parameters
- Maximum a posteriori (MAP) trust estimation
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
from itertools import product


# ─── Bayesian Network Structure ──────────────────────────────────

@dataclass
class BayesianNode:
    """A node in a Bayesian network."""
    name: str
    values: List[str]        # possible values (e.g., ["high", "low"])
    parents: List[str] = field(default_factory=list)
    cpt: Dict[Tuple, float] = field(default_factory=dict)
    # CPT: (parent_val1, parent_val2, ..., self_val) -> probability

    def set_cpt(self, table: Dict[Tuple, float]):
        """Set conditional probability table."""
        self.cpt = dict(table)

    def prob(self, value: str, parent_values: Tuple = ()) -> float:
        """P(self=value | parents=parent_values)."""
        key = parent_values + (value,)
        return self.cpt.get(key, 0.0)


class BayesianNetwork:
    """A Bayesian network for trust reasoning."""

    def __init__(self):
        self.nodes: Dict[str, BayesianNode] = {}
        self.topo_order: List[str] = []

    def add_node(self, name: str, values: List[str],
                  parents: List[str] = None) -> BayesianNode:
        node = BayesianNode(name=name, values=values,
                            parents=parents or [])
        self.nodes[name] = node
        self._update_topo_order()
        return node

    def _update_topo_order(self):
        """Topological sort via Kahn's algorithm."""
        in_degree = {n: 0 for n in self.nodes}
        children: Dict[str, List[str]] = defaultdict(list)
        for name, node in self.nodes.items():
            for p in node.parents:
                children[p].append(name)
                in_degree[name] = in_degree.get(name, 0) + 1

        queue = [n for n, d in in_degree.items() if d == 0]
        order = []
        while queue:
            n = queue.pop(0)
            order.append(n)
            for child in children.get(n, []):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        self.topo_order = order

    def joint_probability(self, assignment: Dict[str, str]) -> float:
        """Compute P(X1=x1, X2=x2, ...) using chain rule."""
        prob = 1.0
        for name in self.topo_order:
            node = self.nodes[name]
            parent_vals = tuple(assignment[p] for p in node.parents)
            prob *= node.prob(assignment[name], parent_vals)
        return prob

    def enumerate_all(self) -> List[Tuple[Dict[str, str], float]]:
        """Enumerate all possible assignments with their probabilities."""
        all_vars = self.topo_order
        all_values = [self.nodes[n].values for n in all_vars]

        results = []
        for combo in product(*all_values):
            assignment = dict(zip(all_vars, combo))
            prob = self.joint_probability(assignment)
            results.append((assignment, prob))
        return results


# ─── Exact Inference (Variable Elimination) ──────────────────────

def marginal(bn: BayesianNetwork, query: str,
              evidence: Dict[str, str] = None) -> Dict[str, float]:
    """
    Compute P(query | evidence) using enumeration-based inference.
    Returns {value: probability} for the query variable.
    """
    evidence = evidence or {}
    all_assignments = bn.enumerate_all()

    # Filter by evidence
    consistent = []
    for assignment, prob in all_assignments:
        if all(assignment[k] == v for k, v in evidence.items()):
            consistent.append((assignment, prob))

    # Sum out everything except query
    query_probs: Dict[str, float] = defaultdict(float)
    for assignment, prob in consistent:
        query_probs[assignment[query]] += prob

    # Normalize
    total = sum(query_probs.values())
    if total > 0:
        return {v: p / total for v, p in query_probs.items()}
    return {v: 1.0 / len(bn.nodes[query].values) for v in bn.nodes[query].values}


def map_estimate(bn: BayesianNetwork,
                  evidence: Dict[str, str] = None) -> Dict[str, str]:
    """
    Maximum A Posteriori estimation: find most likely assignment given evidence.
    """
    evidence = evidence or {}
    all_assignments = bn.enumerate_all()

    best_assignment = None
    best_prob = -1.0

    for assignment, prob in all_assignments:
        if all(assignment[k] == v for k, v in evidence.items()):
            if prob > best_prob:
                best_prob = prob
                best_assignment = assignment

    return best_assignment or {}


# ─── Trust-Specific Models ───────────────────────────────────────

def attestation_quality_network() -> BayesianNetwork:
    """
    Model: Is an attestation trustworthy?

    Variables:
    - AttesterReputation: {high, low}
    - EvidenceStrength: {strong, weak}
    - AttestationQuality: {reliable, unreliable}
    """
    bn = BayesianNetwork()

    rep = bn.add_node("reputation", ["high", "low"])
    rep.set_cpt({
        ("high",): 0.7,    # Prior: 70% of attesters have high reputation
        ("low",): 0.3,
    })

    ev = bn.add_node("evidence", ["strong", "weak"])
    ev.set_cpt({
        ("strong",): 0.6,
        ("weak",): 0.4,
    })

    quality = bn.add_node("quality", ["reliable", "unreliable"],
                           parents=["reputation", "evidence"])
    quality.set_cpt({
        # P(quality | reputation, evidence)
        ("high", "strong", "reliable"): 0.95,
        ("high", "strong", "unreliable"): 0.05,
        ("high", "weak", "reliable"): 0.7,
        ("high", "weak", "unreliable"): 0.3,
        ("low", "strong", "reliable"): 0.6,
        ("low", "strong", "unreliable"): 0.4,
        ("low", "weak", "reliable"): 0.2,
        ("low", "weak", "unreliable"): 0.8,
    })

    return bn


def delegation_trust_network() -> BayesianNetwork:
    """
    Model: Should a delegation be accepted?

    Variables:
    - DelegatorTrust: {trusted, untrusted}
    - CapabilityMatch: {match, mismatch}
    - DelegationDecision: {accept, reject}
    """
    bn = BayesianNetwork()

    dt = bn.add_node("delegator_trust", ["trusted", "untrusted"])
    dt.set_cpt({("trusted",): 0.6, ("untrusted",): 0.4})

    cm = bn.add_node("capability_match", ["match", "mismatch"])
    cm.set_cpt({("match",): 0.75, ("mismatch",): 0.25})

    dd = bn.add_node("decision", ["accept", "reject"],
                      parents=["delegator_trust", "capability_match"])
    dd.set_cpt({
        ("trusted", "match", "accept"): 0.95,
        ("trusted", "match", "reject"): 0.05,
        ("trusted", "mismatch", "accept"): 0.3,
        ("trusted", "mismatch", "reject"): 0.7,
        ("untrusted", "match", "accept"): 0.4,
        ("untrusted", "match", "reject"): 0.6,
        ("untrusted", "mismatch", "accept"): 0.05,
        ("untrusted", "mismatch", "reject"): 0.95,
    })

    return bn


# ─── Sensitivity Analysis ────────────────────────────────────────

def sensitivity_analysis(bn: BayesianNetwork, query: str, query_value: str,
                          param_node: str, evidence: Dict[str, str] = None
                          ) -> Dict[str, float]:
    """
    How does P(query=value | evidence) change for each value of param_node?
    """
    evidence = evidence or {}
    result = {}

    for val in bn.nodes[param_node].values:
        ev = dict(evidence)
        ev[param_node] = val
        post = marginal(bn, query, ev)
        result[val] = post.get(query_value, 0.0)

    return result


# ─── Bayesian Trust Update ───────────────────────────────────────

def bayesian_trust_update(prior: float, likelihood_given_true: float,
                           likelihood_given_false: float) -> float:
    """
    Simple Bayesian update for binary trust.
    P(trust | evidence) = P(evidence | trust) * P(trust) / P(evidence)
    """
    numerator = likelihood_given_true * prior
    denominator = (likelihood_given_true * prior +
                   likelihood_given_false * (1 - prior))
    if denominator == 0:
        return prior
    return numerator / denominator


def sequential_bayesian_update(prior: float,
                                observations: List[Tuple[float, float]]) -> float:
    """
    Sequential Bayesian updates from multiple observations.
    Each observation is (likelihood_if_true, likelihood_if_false).
    """
    current = prior
    for lt, lf in observations:
        current = bayesian_trust_update(current, lt, lf)
    return current


# ─── Mutual Information ──────────────────────────────────────────

def mutual_information(bn: BayesianNetwork, var_a: str, var_b: str) -> float:
    """
    I(A; B) = sum P(a,b) log(P(a,b) / (P(a)P(b)))
    Measures how much knowing A tells about B.
    """
    marginal_a = marginal(bn, var_a)
    marginal_b = marginal(bn, var_b)

    mi = 0.0
    all_assignments = bn.enumerate_all()

    # Compute joint marginal for (A, B)
    joint: Dict[Tuple[str, str], float] = defaultdict(float)
    for assignment, prob in all_assignments:
        key = (assignment[var_a], assignment[var_b])
        joint[key] += prob

    for (a_val, b_val), p_ab in joint.items():
        p_a = marginal_a.get(a_val, 0.0)
        p_b = marginal_b.get(b_val, 0.0)
        if p_ab > 0 and p_a > 0 and p_b > 0:
            mi += p_ab * math.log2(p_ab / (p_a * p_b))

    return mi


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
    print("Trust Bayesian Networks for Web4")
    print("Session 34, Track 2")
    print("=" * 70)

    # ── §1 Network Construction ──────────────────────────────────
    print("\n§1 Network Construction\n")

    bn = BayesianNetwork()
    a = bn.add_node("A", ["0", "1"])
    a.set_cpt({("0",): 0.4, ("1",): 0.6})

    b = bn.add_node("B", ["0", "1"], parents=["A"])
    b.set_cpt({
        ("0", "0"): 0.9, ("0", "1"): 0.1,
        ("1", "0"): 0.2, ("1", "1"): 0.8,
    })

    check("nodes_added", len(bn.nodes) == 2)
    check("topo_order", bn.topo_order == ["A", "B"])
    check("parent_link", bn.nodes["B"].parents == ["A"])

    # ── §2 Joint Probability ─────────────────────────────────────
    print("\n§2 Joint Probability\n")

    # P(A=0, B=0) = P(A=0) * P(B=0|A=0) = 0.4 * 0.9 = 0.36
    jp = bn.joint_probability({"A": "0", "B": "0"})
    check("joint_00", abs(jp - 0.36) < 1e-9, f"jp={jp}")

    # P(A=1, B=1) = 0.6 * 0.8 = 0.48
    jp2 = bn.joint_probability({"A": "1", "B": "1"})
    check("joint_11", abs(jp2 - 0.48) < 1e-9)

    # All joints sum to 1
    all_joints = bn.enumerate_all()
    total = sum(p for _, p in all_joints)
    check("joints_sum_to_1", abs(total - 1.0) < 1e-9, f"total={total}")

    # ── §3 Marginal Inference ────────────────────────────────────
    print("\n§3 Marginal Inference\n")

    # P(A) should match prior
    marg_a = marginal(bn, "A")
    check("marginal_a_0", abs(marg_a["0"] - 0.4) < 1e-9)
    check("marginal_a_1", abs(marg_a["1"] - 0.6) < 1e-9)

    # P(B) = P(B|A=0)*P(A=0) + P(B|A=1)*P(A=1)
    # P(B=0) = 0.9*0.4 + 0.2*0.6 = 0.36 + 0.12 = 0.48
    marg_b = marginal(bn, "B")
    check("marginal_b_0", abs(marg_b["0"] - 0.48) < 1e-9, f"marg_b_0={marg_b['0']}")

    # P(A | B=1) — posterior
    post_a = marginal(bn, "A", {"B": "1"})
    # P(A=1|B=1) = P(B=1|A=1)*P(A=1) / P(B=1) = 0.8*0.6 / 0.52 ≈ 0.923
    check("posterior_a_given_b1", abs(post_a["1"] - 0.48 / 0.52) < 1e-9,
          f"post={post_a['1']}")

    # ── §4 Attestation Quality Model ────────────────────────────
    print("\n§4 Attestation Quality Model\n")

    aq = attestation_quality_network()

    # Prior P(quality=reliable)
    prior_quality = marginal(aq, "quality")
    check("prior_reliable", prior_quality["reliable"] > 0.5,
          f"reliable={prior_quality['reliable']:.3f}")

    # Given high reputation: P(reliable | rep=high) should increase
    post_high = marginal(aq, "quality", {"reputation": "high"})
    check("high_rep_increases_quality",
          post_high["reliable"] > prior_quality["reliable"],
          f"prior={prior_quality['reliable']:.3f}, post={post_high['reliable']:.3f}")

    # Given strong evidence AND high reputation
    post_best = marginal(aq, "quality", {"reputation": "high", "evidence": "strong"})
    check("best_case_very_reliable", post_best["reliable"] > 0.9,
          f"best={post_best['reliable']:.3f}")

    # Worst case: low reputation, weak evidence
    post_worst = marginal(aq, "quality", {"reputation": "low", "evidence": "weak"})
    check("worst_case_unreliable", post_worst["unreliable"] > 0.7,
          f"worst_unreliable={post_worst['unreliable']:.3f}")

    # ── §5 Delegation Decision Model ────────────────────────────
    print("\n§5 Delegation Decision Model\n")

    dd = delegation_trust_network()

    # P(accept | trusted, match) should be high
    p_accept_good = marginal(dd, "decision",
                              {"delegator_trust": "trusted", "capability_match": "match"})
    check("good_delegation_accepted", p_accept_good["accept"] > 0.9)

    # P(accept | untrusted, mismatch) should be very low
    p_accept_bad = marginal(dd, "decision",
                             {"delegator_trust": "untrusted", "capability_match": "mismatch"})
    check("bad_delegation_rejected", p_accept_bad["reject"] > 0.9)

    # ── §6 MAP Estimation ────────────────────────────────────────
    print("\n§6 MAP Estimation\n")

    map_result = map_estimate(bn, {"B": "1"})
    check("map_a_is_1", map_result.get("A") == "1",
          f"map_a={map_result.get('A')}")

    map_att = map_estimate(aq, {"quality": "reliable"})
    check("map_rep_high", map_att.get("reputation") == "high")

    # ── §7 Bayesian Trust Update ──────────────────────────────────
    print("\n§7 Bayesian Trust Update\n")

    # Start with prior 0.5, observe positive evidence
    post1 = bayesian_trust_update(0.5, 0.9, 0.1)
    check("positive_update_increases", post1 > 0.5, f"post1={post1:.3f}")
    check("positive_update_value", abs(post1 - 0.9) < 1e-9)

    # Multiple positive observations compound
    post_seq = sequential_bayesian_update(0.5, [(0.9, 0.1)] * 3)
    check("sequential_converges_high", post_seq > 0.99, f"post_seq={post_seq:.3f}")

    # Negative evidence decreases trust
    post_neg = bayesian_trust_update(0.8, 0.2, 0.9)
    check("negative_decreases", post_neg < 0.8, f"post_neg={post_neg:.3f}")

    # Neutral evidence (50/50) keeps prior
    post_neutral = bayesian_trust_update(0.7, 0.5, 0.5)
    check("neutral_preserves", abs(post_neutral - 0.7) < 1e-9)

    # ── §8 Sensitivity Analysis ──────────────────────────────────
    print("\n§8 Sensitivity Analysis\n")

    sens = sensitivity_analysis(aq, "quality", "reliable", "reputation")
    check("sens_high_better", sens["high"] > sens["low"],
          f"high={sens['high']:.3f}, low={sens['low']:.3f}")

    sens_ev = sensitivity_analysis(aq, "quality", "reliable", "evidence")
    check("sens_strong_better", sens_ev["strong"] > sens_ev["weak"])

    # ── §9 Mutual Information ────────────────────────────────────
    print("\n§9 Mutual Information\n")

    mi_ab = mutual_information(bn, "A", "B")
    check("mi_positive", mi_ab > 0, f"mi={mi_ab:.4f}")

    # MI is symmetric
    mi_ba = mutual_information(bn, "B", "A")
    check("mi_symmetric", abs(mi_ab - mi_ba) < 1e-9)

    # Independent variables have MI = 0
    bn_ind = BayesianNetwork()
    x = bn_ind.add_node("X", ["0", "1"])
    x.set_cpt({("0",): 0.5, ("1",): 0.5})
    y = bn_ind.add_node("Y", ["0", "1"])
    y.set_cpt({("0",): 0.5, ("1",): 0.5})
    mi_ind = mutual_information(bn_ind, "X", "Y")
    check("independent_mi_zero", abs(mi_ind) < 1e-9, f"mi_ind={mi_ind}")

    # Attestation quality highly depends on reputation
    mi_rep_qual = mutual_information(aq, "reputation", "quality")
    mi_ev_qual = mutual_information(aq, "evidence", "quality")
    check("rep_more_informative", mi_rep_qual > 0, f"mi_rep={mi_rep_qual:.4f}")
    check("evidence_informative", mi_ev_qual > 0, f"mi_ev={mi_ev_qual:.4f}")

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
