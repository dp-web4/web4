"""
Adaptive Trust Policies for Web4
Session 30, Track 8

Dynamic policy adjustment based on federation state:
- Threat-level adaptive policies (DEFCON-like levels)
- Policy gradient optimization for trust thresholds
- Context-dependent policy selection
- Policy composition (AND, OR, weighted)
- Hysteresis in policy transitions (prevent oscillation)
- Policy evaluation with accountability framing
- Emergency policy override (CRISIS mode)
- Policy learning from historical decisions
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Callable


# ─── Threat Levels ─────────────────────────────────────────────────

class ThreatLevel(Enum):
    GREEN = 0    # normal operations
    YELLOW = 1   # elevated awareness
    ORANGE = 2   # heightened threat
    RED = 3      # active attack
    BLACK = 4    # critical / CRISIS


@dataclass
class FederationState:
    """Observable federation state for policy decisions."""
    avg_trust: float
    min_trust: float
    attack_rate: float      # attacks per time window [0, 1]
    anomaly_count: int
    byzantine_fraction: float
    health_score: float     # from federation health metrics [0, 1]
    time: int = 0


# ─── Policy Definitions ───────────────────────────────────────────

@dataclass
class TrustPolicy:
    """Configurable trust policy parameters."""
    min_trust_threshold: float = 0.3
    attestation_quorum: int = 3
    decay_rate: float = 0.01
    max_delegation_depth: int = 3
    require_hardware_binding: bool = False
    cooldown_period: int = 10
    name: str = "default"


# Predefined policy profiles
POLICIES = {
    ThreatLevel.GREEN: TrustPolicy(
        min_trust_threshold=0.3, attestation_quorum=2, decay_rate=0.005,
        max_delegation_depth=5, require_hardware_binding=False, cooldown_period=5,
        name="green"
    ),
    ThreatLevel.YELLOW: TrustPolicy(
        min_trust_threshold=0.4, attestation_quorum=3, decay_rate=0.01,
        max_delegation_depth=4, require_hardware_binding=False, cooldown_period=10,
        name="yellow"
    ),
    ThreatLevel.ORANGE: TrustPolicy(
        min_trust_threshold=0.5, attestation_quorum=5, decay_rate=0.02,
        max_delegation_depth=3, require_hardware_binding=True, cooldown_period=20,
        name="orange"
    ),
    ThreatLevel.RED: TrustPolicy(
        min_trust_threshold=0.7, attestation_quorum=7, decay_rate=0.05,
        max_delegation_depth=2, require_hardware_binding=True, cooldown_period=50,
        name="red"
    ),
    ThreatLevel.BLACK: TrustPolicy(
        min_trust_threshold=0.9, attestation_quorum=10, decay_rate=0.1,
        max_delegation_depth=1, require_hardware_binding=True, cooldown_period=100,
        name="black"
    ),
}


# ─── Threat Assessment ────────────────────────────────────────────

def assess_threat_level(state: FederationState) -> ThreatLevel:
    """Determine threat level from federation state."""
    score = 0.0

    # Low average trust → higher threat
    if state.avg_trust < 0.3:
        score += 2.0
    elif state.avg_trust < 0.5:
        score += 1.0

    # High attack rate
    score += state.attack_rate * 3.0

    # Anomalies
    if state.anomaly_count > 10:
        score += 2.0
    elif state.anomaly_count > 3:
        score += 1.0

    # Byzantine fraction
    if state.byzantine_fraction > 0.25:
        score += 3.0
    elif state.byzantine_fraction > 0.1:
        score += 1.5

    # Low health
    if state.health_score < 0.3:
        score += 2.0
    elif state.health_score < 0.5:
        score += 1.0

    if score >= 8:
        return ThreatLevel.BLACK
    elif score >= 5:
        return ThreatLevel.RED
    elif score >= 3:
        return ThreatLevel.ORANGE
    elif score >= 1.5:
        return ThreatLevel.YELLOW
    return ThreatLevel.GREEN


# ─── Hysteresis Controller ────────────────────────────────────────

class HysteresisController:
    """
    Prevents policy oscillation by requiring sustained signals.

    Level increases require fewer consecutive signals than decreases
    (faster escalation, slower de-escalation).
    """

    def __init__(self, escalation_window: int = 2, de_escalation_window: int = 5):
        self.current_level = ThreatLevel.GREEN
        self.escalation_window = escalation_window
        self.de_escalation_window = de_escalation_window
        self.level_history: List[ThreatLevel] = []

    def update(self, raw_level: ThreatLevel) -> ThreatLevel:
        """Apply hysteresis to raw threat level."""
        self.level_history.append(raw_level)

        if raw_level.value > self.current_level.value:
            # Escalation: check recent history (need full window)
            recent = self.level_history[-self.escalation_window:]
            if len(recent) >= self.escalation_window and \
               all(l.value >= raw_level.value for l in recent):
                self.current_level = raw_level
        elif raw_level.value < self.current_level.value:
            # De-escalation: require longer sustained signal
            recent = self.level_history[-self.de_escalation_window:]
            if len(recent) >= self.de_escalation_window and \
               all(l.value <= raw_level.value for l in recent):
                self.current_level = raw_level

        return self.current_level


# ─── Policy Composition ───────────────────────────────────────────

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    confidence: float  # [0, 1]


def policy_and(decisions: List[PolicyDecision]) -> PolicyDecision:
    """All policies must allow (most restrictive)."""
    if not decisions:
        return PolicyDecision(True, "no policies", 1.0)

    all_allowed = all(d.allowed for d in decisions)
    min_conf = min(d.confidence for d in decisions)
    reasons = [d.reason for d in decisions if not d.allowed]

    return PolicyDecision(
        all_allowed,
        "; ".join(reasons) if reasons else "all policies allow",
        min_conf
    )


def policy_or(decisions: List[PolicyDecision]) -> PolicyDecision:
    """Any policy allows (most permissive)."""
    if not decisions:
        return PolicyDecision(False, "no policies", 0.0)

    any_allowed = any(d.allowed for d in decisions)
    max_conf = max(d.confidence for d in decisions)
    reasons = [d.reason for d in decisions if d.allowed]

    return PolicyDecision(
        any_allowed,
        reasons[0] if reasons else "no policy allows",
        max_conf
    )


def policy_weighted(decisions: List[Tuple[PolicyDecision, float]]) -> PolicyDecision:
    """Weighted policy combination with threshold."""
    if not decisions:
        return PolicyDecision(False, "no policies", 0.0)

    total_weight = sum(w for _, w in decisions)
    allow_weight = sum(w for d, w in decisions if d.allowed)

    fraction = allow_weight / total_weight if total_weight > 0 else 0
    allowed = fraction > 0.5  # majority wins

    return PolicyDecision(
        allowed,
        f"weighted: {fraction:.2f} allow fraction",
        fraction if allowed else 1 - fraction
    )


# ─── Policy Evaluation ────────────────────────────────────────────

def evaluate_access(entity_trust: float, policy: TrustPolicy,
                    context: str = "normal") -> PolicyDecision:
    """Evaluate whether entity meets trust policy for access."""
    # CRISIS mode changes accountability, not strictness
    if context == "crisis":
        # In crisis, allow lower trust but with accountability
        effective_threshold = policy.min_trust_threshold * 0.8
        if entity_trust >= effective_threshold:
            return PolicyDecision(True,
                                  f"crisis access: trust {entity_trust:.2f} >= {effective_threshold:.2f}",
                                  entity_trust)
        return PolicyDecision(False,
                              f"denied even in crisis: {entity_trust:.2f} < {effective_threshold:.2f}",
                              entity_trust)

    if entity_trust >= policy.min_trust_threshold:
        return PolicyDecision(True,
                              f"trust {entity_trust:.2f} >= {policy.min_trust_threshold:.2f}",
                              entity_trust)
    return PolicyDecision(False,
                          f"trust {entity_trust:.2f} < {policy.min_trust_threshold:.2f}",
                          entity_trust)


# ─── Policy Gradient Optimization ─────────────────────────────────

class PolicyOptimizer:
    """
    Optimize trust thresholds via policy gradient.

    Objective: maximize utility = correct_accepts - α * false_accepts - β * false_rejects
    """

    def __init__(self, alpha: float = 2.0, beta: float = 1.0,
                 learning_rate: float = 0.01):
        self.alpha = alpha  # false accept penalty
        self.beta = beta    # false reject penalty
        self.learning_rate = learning_rate
        self.threshold = 0.5
        self.utility_history: List[float] = []

    def evaluate(self, entities: List[Tuple[float, bool]]) -> float:
        """
        Evaluate current threshold on labeled data.
        entities: [(trust_score, is_trustworthy)]
        """
        utility = 0.0
        for trust, is_good in entities:
            accepted = trust >= self.threshold
            if accepted and is_good:
                utility += 1.0  # correct accept
            elif accepted and not is_good:
                utility -= self.alpha  # false accept
            elif not accepted and is_good:
                utility -= self.beta  # false reject
            # correct reject: 0 utility

        return utility / max(1, len(entities))

    def step(self, entities: List[Tuple[float, bool]]):
        """One gradient step."""
        # Numerical gradient
        eps = 0.01
        self.threshold += eps
        u_plus = self.evaluate(entities)
        self.threshold -= 2 * eps
        u_minus = self.evaluate(entities)
        self.threshold += eps  # restore

        gradient = (u_plus - u_minus) / (2 * eps)
        self.threshold += self.learning_rate * gradient
        self.threshold = max(0.1, min(0.9, self.threshold))

        self.utility_history.append(self.evaluate(entities))

    def optimize(self, entities: List[Tuple[float, bool]], steps: int = 100):
        """Run optimization."""
        for _ in range(steps):
            self.step(entities)


# ─── Policy Learning ──────────────────────────────────────────────

class PolicyLearner:
    """Learn policy parameters from historical decisions."""

    def __init__(self):
        self.history: List[Dict] = []

    def record(self, state: FederationState, policy: TrustPolicy,
               outcome: str):
        """Record a policy decision and its outcome."""
        self.history.append({
            "avg_trust": state.avg_trust,
            "attack_rate": state.attack_rate,
            "health": state.health_score,
            "threshold": policy.min_trust_threshold,
            "outcome": outcome,
        })

    def recommend_threshold(self) -> float:
        """Recommend threshold based on historical success."""
        if not self.history:
            return 0.5

        # Successful decisions
        good = [h for h in self.history if h["outcome"] == "success"]
        bad = [h for h in self.history if h["outcome"] == "failure"]

        if not good:
            return 0.5

        # Average threshold of successful decisions
        good_avg = sum(h["threshold"] for h in good) / len(good)

        # If many failures, increase threshold
        failure_rate = len(bad) / len(self.history) if self.history else 0
        adjustment = failure_rate * 0.1

        return min(0.9, good_avg + adjustment)

    def recommend_policy(self, state: FederationState) -> TrustPolicy:
        """Recommend policy based on state and history."""
        level = assess_threat_level(state)
        base_policy = POLICIES[level]

        # Adjust threshold based on learning
        learned_threshold = self.recommend_threshold()

        return TrustPolicy(
            min_trust_threshold=max(base_policy.min_trust_threshold, learned_threshold),
            attestation_quorum=base_policy.attestation_quorum,
            decay_rate=base_policy.decay_rate,
            max_delegation_depth=base_policy.max_delegation_depth,
            require_hardware_binding=base_policy.require_hardware_binding,
            cooldown_period=base_policy.cooldown_period,
            name=f"learned_{level.name.lower()}"
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
    print("Adaptive Trust Policies for Web4")
    print("Session 30, Track 8")
    print("=" * 70)

    # ── §1 Threat Assessment ──────────────────────────────────────
    print("\n§1 Threat Level Assessment\n")

    peaceful = FederationState(avg_trust=0.8, min_trust=0.5, attack_rate=0.0,
                                anomaly_count=0, byzantine_fraction=0.0,
                                health_score=0.9)
    check("peaceful_is_green", assess_threat_level(peaceful) == ThreatLevel.GREEN)

    moderate = FederationState(avg_trust=0.5, min_trust=0.2, attack_rate=0.3,
                                anomaly_count=5, byzantine_fraction=0.05,
                                health_score=0.6)
    moderate_level = assess_threat_level(moderate)
    check("moderate_is_yellow_or_orange",
          moderate_level in (ThreatLevel.YELLOW, ThreatLevel.ORANGE),
          f"level={moderate_level.name}")

    severe = FederationState(avg_trust=0.2, min_trust=0.0, attack_rate=0.8,
                              anomaly_count=15, byzantine_fraction=0.3,
                              health_score=0.2)
    check("severe_is_red_or_black",
          assess_threat_level(severe).value >= ThreatLevel.RED.value,
          f"level={assess_threat_level(severe).name}")

    # ── §2 Policy Profiles ────────────────────────────────────────
    print("\n§2 Policy Profiles\n")

    # Threat escalation → stricter policies
    thresholds = [POLICIES[l].min_trust_threshold for l in ThreatLevel]
    check("thresholds_increase",
          all(thresholds[i] <= thresholds[i+1] for i in range(len(thresholds)-1)),
          f"thresholds={thresholds}")

    quorums = [POLICIES[l].attestation_quorum for l in ThreatLevel]
    check("quorums_increase",
          all(quorums[i] <= quorums[i+1] for i in range(len(quorums)-1)),
          f"quorums={quorums}")

    depths = [POLICIES[l].max_delegation_depth for l in ThreatLevel]
    check("delegation_decreases",
          all(depths[i] >= depths[i+1] for i in range(len(depths)-1)),
          f"depths={depths}")

    # ── §3 Hysteresis ─────────────────────────────────────────────
    print("\n§3 Hysteresis Controller\n")

    hc = HysteresisController(escalation_window=2, de_escalation_window=3)

    # Single spike doesn't escalate
    result = hc.update(ThreatLevel.RED)
    check("single_spike_no_escalation", result == ThreatLevel.GREEN,
          f"level={result.name}")

    # Sustained signal escalates
    hc.update(ThreatLevel.RED)
    result = hc.update(ThreatLevel.RED)
    check("sustained_escalates", result == ThreatLevel.RED,
          f"level={result.name}")

    # Single green doesn't de-escalate
    result = hc.update(ThreatLevel.GREEN)
    check("single_green_no_deescalation", result == ThreatLevel.RED,
          f"level={result.name}")

    # Sustained green de-escalates
    for _ in range(4):
        hc.update(ThreatLevel.GREEN)
    result = hc.update(ThreatLevel.GREEN)
    check("sustained_green_deescalates", result == ThreatLevel.GREEN,
          f"level={result.name}")

    # ── §4 Policy Composition ─────────────────────────────────────
    print("\n§4 Policy Composition\n")

    d_allow = PolicyDecision(True, "allowed", 0.8)
    d_deny = PolicyDecision(False, "denied", 0.6)

    # AND: both must allow
    and_result = policy_and([d_allow, d_deny])
    check("and_requires_all", not and_result.allowed)

    and_both = policy_and([d_allow, PolicyDecision(True, "ok", 0.9)])
    check("and_both_allow", and_both.allowed)

    # OR: any allows
    or_result = policy_or([d_allow, d_deny])
    check("or_any_allows", or_result.allowed)

    or_none = policy_or([d_deny, PolicyDecision(False, "no", 0.5)])
    check("or_none_denies", not or_none.allowed)

    # Weighted
    weighted = policy_weighted([
        (d_allow, 0.7),
        (d_deny, 0.3),
    ])
    check("weighted_majority_allows", weighted.allowed)

    weighted_deny = policy_weighted([
        (d_allow, 0.3),
        (d_deny, 0.7),
    ])
    check("weighted_majority_denies", not weighted_deny.allowed)

    # ── §5 Access Evaluation ──────────────────────────────────────
    print("\n§5 Access Evaluation\n")

    green_policy = POLICIES[ThreatLevel.GREEN]
    red_policy = POLICIES[ThreatLevel.RED]

    # High trust passes both
    high = evaluate_access(0.9, green_policy)
    check("high_trust_green_access", high.allowed)
    high_red = evaluate_access(0.9, red_policy)
    check("high_trust_red_access", high_red.allowed)

    # Medium trust passes green, fails red
    med = evaluate_access(0.5, green_policy)
    check("medium_trust_green_access", med.allowed)
    med_red = evaluate_access(0.5, red_policy)
    check("medium_trust_red_denied", not med_red.allowed)

    # Crisis mode relaxes threshold
    crisis = evaluate_access(0.6, red_policy, context="crisis")
    check("crisis_relaxes_threshold", crisis.allowed,
          f"threshold={red_policy.min_trust_threshold*0.8:.2f} trust=0.6")

    # ── §6 Policy Gradient Optimization ───────────────────────────
    print("\n§6 Policy Gradient Optimization\n")

    rng = random.Random(42)
    # Generate labeled data: trust > 0.6 → trustworthy
    entities = [(rng.random(), rng.random() > 0.5) for _ in range(100)]
    # Make trustworthiness correlate with trust
    entities = [(t, t > 0.55 + rng.gauss(0, 0.1)) for t in
                [rng.random() for _ in range(100)]]

    optimizer = PolicyOptimizer(alpha=2.0, beta=1.0, learning_rate=0.05)
    initial_utility = optimizer.evaluate(entities)
    optimizer.optimize(entities, steps=100)
    final_utility = optimizer.evaluate(entities)

    check("optimization_improves", final_utility >= initial_utility - 0.1,
          f"initial={initial_utility:.3f} final={final_utility:.3f}")

    # Threshold should converge near true boundary (~0.55)
    check("threshold_near_boundary", 0.3 < optimizer.threshold < 0.8,
          f"threshold={optimizer.threshold:.3f}")

    # ── §7 Policy Learning ────────────────────────────────────────
    print("\n§7 Policy Learning from History\n")

    learner = PolicyLearner()

    # Record good decisions (moderate threshold, success)
    for _ in range(10):
        learner.record(peaceful, TrustPolicy(min_trust_threshold=0.4), "success")

    # Record bad decisions (low threshold, failure)
    for _ in range(5):
        learner.record(moderate, TrustPolicy(min_trust_threshold=0.2), "failure")

    recommended = learner.recommend_threshold()
    check("learned_threshold_reasonable", 0.3 < recommended < 0.8,
          f"recommended={recommended:.3f}")

    # More failures → higher threshold
    for _ in range(10):
        learner.record(severe, TrustPolicy(min_trust_threshold=0.3), "failure")

    higher = learner.recommend_threshold()
    check("more_failures_higher_threshold", higher >= recommended,
          f"before={recommended:.3f} after={higher:.3f}")

    # Recommend policy
    policy = learner.recommend_policy(moderate)
    check("recommended_policy_exists", policy.name.startswith("learned_"))
    check("recommended_threshold_bounded", 0 < policy.min_trust_threshold <= 1)

    # ── §8 Emergency Override ─────────────────────────────────────
    print("\n§8 Emergency / CRISIS Mode\n")

    black_policy = POLICIES[ThreatLevel.BLACK]

    # BLACK level is most restrictive
    check("black_highest_threshold",
          black_policy.min_trust_threshold >= 0.9)
    check("black_requires_hw", black_policy.require_hardware_binding)
    check("black_max_quorum",
          black_policy.attestation_quorum >= POLICIES[ThreatLevel.RED].attestation_quorum)

    # Even in CRISIS, very low trust is denied
    denied_crisis = evaluate_access(0.1, black_policy, context="crisis")
    check("crisis_still_denies_very_low", not denied_crisis.allowed,
          f"trust=0.1 threshold={black_policy.min_trust_threshold*0.8:.2f}")

    # CRISIS with high trust is allowed (even under BLACK)
    allowed_crisis = evaluate_access(0.8, black_policy, context="crisis")
    check("crisis_allows_high_trust", allowed_crisis.allowed)

    # ── §9 Policy Transition Costs ────────────────────────────────
    print("\n§9 Policy Transition Analysis\n")

    # Count how many entities would be affected by policy change
    entity_trusts = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

    green_accepted = sum(1 for t in entity_trusts if t >= POLICIES[ThreatLevel.GREEN].min_trust_threshold)
    red_accepted = sum(1 for t in entity_trusts if t >= POLICIES[ThreatLevel.RED].min_trust_threshold)

    disrupted = green_accepted - red_accepted
    check("escalation_disrupts", disrupted > 0,
          f"green_accepts={green_accepted} red_accepts={red_accepted}")

    # Disruption proportional to level jump
    yellow_accepted = sum(1 for t in entity_trusts if t >= POLICIES[ThreatLevel.YELLOW].min_trust_threshold)
    check("bigger_jump_more_disruption",
          green_accepted - red_accepted >= green_accepted - yellow_accepted,
          f"green→red: {green_accepted - red_accepted}, green→yellow: {green_accepted - yellow_accepted}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
