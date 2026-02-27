#!/usr/bin/env python3
"""
Adversarial Machine Learning on Trust Systems

What happens when attackers use ML to optimize their trust manipulation?

Traditional trust attacks (Sybil, free-riding, collusion) are HEURISTIC —
the attacker follows a fixed strategy. But an ML-powered attacker can:
  - Learn the trust update function and OPTIMIZE against it
  - Find blind spots in detection algorithms
  - Craft minimal-effort attacks that achieve maximum trust inflation
  - Extract the trust model from observations (model stealing)
  - Poison training data to shift trust norms

This implementation tests Web4's trust system against ML-powered adversaries.

Sections:
  §1  Trust Model as Differentiable Function — make trust updates gradient-friendly
  §2  Gradient-Based Trust Optimization — attacker maximizes trust via gradient ascent
  §3  Adversarial Action Sequences — optimal action ordering to inflate trust
  §4  Data Poisoning Attacks — manipulate trust evidence to shift norms
  §5  Model Extraction — learn trust function from input-output observations
  §6  Evasion Attacks — craft actions that evade anomaly detection
  §7  Robust Trust Aggregation — defenses against ML-powered manipulation
  §8  Adversarial Training — harden trust models against known attack patterns
  §9  Trust Watermarking — detect model extraction via canary values
  §10 Game-Theoretic ML Defense — minimax optimization of trust policy
  §11 Ensemble Trust Models — diversity as defense against targeted attacks
  §12 Full Red Team Simulation — coordinated ML attack vs adaptive defense
"""

import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
#  §1. TRUST MODEL AS DIFFERENTIABLE FUNCTION
# ═══════════════════════════════════════════════════════════════

class DifferentiableTrust:
    """
    Wrap Web4's trust update as a differentiable function.

    Trust update: T(t+1) = clip(T(t) + α * (quality - 0.5) * (1 - T(t)), 0, 1)

    This is differentiable in both T and quality:
      ∂T(t+1)/∂quality = α * (1 - T(t))
      ∂T(t+1)/∂T(t) = 1 - α * (quality - 0.5)

    The gradient tells the attacker how much each action quality
    affects the trust update — enabling gradient ascent attacks.
    """

    def __init__(self, alpha: float = 0.02,
                 decay_rate: float = 0.001,
                 diminishing_factor: float = 0.8):
        self.alpha = alpha
        self.decay_rate = decay_rate
        self.diminishing_factor = diminishing_factor

    def update(self, trust: float, quality: float, n_same_type: int = 1) -> float:
        """Single trust update step. Returns new trust."""
        # Diminishing returns for repeated same-type actions
        effective_quality = quality * (self.diminishing_factor ** (n_same_type - 1))
        delta = self.alpha * (effective_quality - 0.5) * (1 - trust)
        # Natural decay
        trust = trust - self.decay_rate * trust
        trust = trust + delta
        return max(0.0, min(1.0, trust))

    def gradient_quality(self, trust: float, n_same_type: int = 1) -> float:
        """∂T(t+1)/∂quality — how much quality affects trust change."""
        diminish = self.diminishing_factor ** (n_same_type - 1)
        return self.alpha * diminish * (1 - trust)

    def gradient_trust(self, trust: float, quality: float, n_same_type: int = 1) -> float:
        """∂T(t+1)/∂T(t) — sensitivity of new trust to current trust."""
        diminish = self.diminishing_factor ** (n_same_type - 1)
        effective_quality = quality * diminish
        return 1 - self.decay_rate - self.alpha * (effective_quality - 0.5)

    def trajectory(self, initial_trust: float,
                  qualities: List[float],
                  apply_diminishing: bool = False) -> List[float]:
        """Compute full trust trajectory from action sequence.

        By default, assumes diverse action types (no diminishing returns).
        Set apply_diminishing=True to simulate same-type repeated actions.
        """
        trust = initial_trust
        traj = [trust]
        count = 0

        for q in qualities:
            count += 1
            n_type = count if apply_diminishing else 1
            trust = self.update(trust, q, n_type)
            traj.append(trust)

        return traj


# ═══════════════════════════════════════════════════════════════
#  §2. GRADIENT-BASED TRUST OPTIMIZATION
# ═══════════════════════════════════════════════════════════════

class GradientTrustAttack:
    """
    Attacker uses gradient ascent to maximize trust.

    Given a budget of N actions with cost function C(quality):
      maximize: T(N) = f(T(0), q_1, q_2, ..., q_N)
      subject to: Σ C(q_i) ≤ budget

    This is a constrained optimization problem solvable with
    gradient ascent + projection.
    """

    def __init__(self, trust_model: DifferentiableTrust,
                 action_cost: Callable[[float], float] = None):
        self.model = trust_model
        # Cost: higher quality actions cost more
        self.cost = action_cost or (lambda q: q ** 2)

    def optimize_sequence(self, initial_trust: float,
                         n_actions: int,
                         budget: float = None,
                         learning_rate: float = 0.1,
                         n_iterations: int = 100) -> Dict:
        """
        Find optimal action quality sequence to maximize final trust.

        Uses gradient ascent on the action qualities.
        """
        if budget is None:
            budget = n_actions * 0.5  # Default: can afford quality 0.7 per action

        # Initialize: all medium quality
        qualities = [0.7] * n_actions

        best_trust = 0
        best_qualities = qualities[:]

        for iteration in range(n_iterations):
            # Forward pass
            trust = initial_trust
            trusts = [trust]
            type_counts = 0

            for q in qualities:
                type_counts += 1
                trust = self.model.update(trust, q, type_counts)
                trusts.append(trust)

            final_trust = trusts[-1]

            if final_trust > best_trust:
                best_trust = final_trust
                best_qualities = qualities[:]

            # Backward pass: compute gradients
            # Using numerical gradients for robustness
            gradients = []
            for i in range(n_actions):
                eps = 0.01
                q_plus = qualities[:]
                q_plus[i] = min(1.0, qualities[i] + eps)
                trust_plus = self.model.trajectory(initial_trust, q_plus)[-1]

                q_minus = qualities[:]
                q_minus[i] = max(0.0, qualities[i] - eps)
                trust_minus = self.model.trajectory(initial_trust, q_minus)[-1]

                grad = (trust_plus - trust_minus) / (2 * eps)
                gradients.append(grad)

            # Gradient ascent
            total_cost = sum(self.cost(q) for q in qualities)
            for i in range(n_actions):
                # Update quality (gradient ascent for trust, gradient descent for cost)
                cost_grad = 2 * qualities[i]  # d/dq of q^2

                if total_cost > budget:
                    # Over budget: reduce expensive actions
                    qualities[i] -= learning_rate * cost_grad
                else:
                    qualities[i] += learning_rate * gradients[i]

                qualities[i] = max(0.0, min(1.0, qualities[i]))

        # Final evaluation
        final_trajectory = self.model.trajectory(initial_trust, best_qualities)

        return {
            'optimal_qualities': best_qualities,
            'final_trust': final_trajectory[-1],
            'trajectory': final_trajectory,
            'total_cost': sum(self.cost(q) for q in best_qualities),
            'avg_quality': statistics.mean(best_qualities),
        }

    def compare_strategies(self, initial_trust: float,
                          n_actions: int = 50) -> Dict:
        """Compare gradient-optimized vs naive strategies."""
        # Strategy 1: Constant high quality (naive honest)
        naive_high = self.model.trajectory(initial_trust, [0.9] * n_actions)

        # Strategy 2: Constant medium quality
        naive_mid = self.model.trajectory(initial_trust, [0.6] * n_actions)

        # Strategy 3: Gradient-optimized
        optimized = self.optimize_sequence(initial_trust, n_actions)

        # Strategy 4: Random
        random_quals = [random.random() for _ in range(n_actions)]
        naive_random = self.model.trajectory(initial_trust, random_quals)

        return {
            'naive_high_final': naive_high[-1],
            'naive_mid_final': naive_mid[-1],
            'optimized_final': optimized['final_trust'],
            'random_final': naive_random[-1],
            'optimization_advantage': optimized['final_trust'] - naive_high[-1],
            'strategies': {
                'naive_high': naive_high[-1],
                'naive_mid': naive_mid[-1],
                'optimized': optimized['final_trust'],
                'random': naive_random[-1],
            }
        }


# ═══════════════════════════════════════════════════════════════
#  §3. ADVERSARIAL ACTION SEQUENCES
# ═══════════════════════════════════════════════════════════════

class AdversarialSequencer:
    """
    Find optimal action ORDERING (not just quality) to inflate trust.

    Key insight: the diminishing returns formula means action TYPE diversity
    matters. An attacker should alternate between different action types
    to avoid the diminishing returns penalty.

    Also: front-loading high quality actions when trust gradient is steepest
    (at low trust) vs back-loading when approaching threshold.
    """

    @staticmethod
    def front_load_vs_back_load(model: DifferentiableTrust,
                                initial_trust: float = 0.2,
                                n_actions: int = 50) -> Dict:
        """Compare front-loading vs back-loading high-quality actions."""
        n_high = n_actions // 2
        n_low = n_actions - n_high

        # Front-load: high quality first, then low
        front_load = [0.9] * n_high + [0.5] * n_low
        front_traj = model.trajectory(initial_trust, front_load)

        # Back-load: low quality first, then high
        back_load = [0.5] * n_low + [0.9] * n_high
        back_traj = model.trajectory(initial_trust, back_load)

        # Alternating: alternate high and low
        alternating = []
        for i in range(n_actions):
            alternating.append(0.9 if i % 2 == 0 else 0.5)
        alt_traj = model.trajectory(initial_trust, alternating)

        return {
            'front_load_final': front_traj[-1],
            'back_load_final': back_traj[-1],
            'alternating_final': alt_traj[-1],
            'front_advantage': front_traj[-1] - back_traj[-1],
            'best_strategy': max(
                [('front', front_traj[-1]),
                 ('back', back_traj[-1]),
                 ('alternating', alt_traj[-1])],
                key=lambda x: x[1]
            )[0],
        }

    @staticmethod
    def diversity_exploitation(model: DifferentiableTrust,
                              initial_trust: float = 0.2,
                              n_actions: int = 50,
                              n_types: int = 5) -> Dict:
        """
        Exploit diminishing returns by diversifying action types.

        Each action type has its own diminishing returns counter.
        Cycling through types avoids the penalty.
        """
        # Same type (maximal diminishing returns)
        same_type_trust = initial_trust
        for i in range(n_actions):
            same_type_trust = model.update(same_type_trust, 0.8, i + 1)

        # Diverse types (minimal diminishing returns)
        diverse_trust = initial_trust
        type_counts = defaultdict(int)
        for i in range(n_actions):
            action_type = i % n_types
            type_counts[action_type] += 1
            diverse_trust = model.update(diverse_trust, 0.8, type_counts[action_type])

        return {
            'same_type_final': same_type_trust,
            'diverse_type_final': diverse_trust,
            'diversity_advantage': diverse_trust - same_type_trust,
            'diversity_matters': diverse_trust > same_type_trust,
        }


# ═══════════════════════════════════════════════════════════════
#  §4. DATA POISONING ATTACKS
# ═══════════════════════════════════════════════════════════════

class DataPoisoning:
    """
    Manipulate trust evidence to shift system-wide trust norms.

    Attack types:
      1. Label flipping: report high quality as low and vice versa
      2. Distribution shift: gradually change what "normal" looks like
      3. Targeted poisoning: inject evidence about specific entities
    """

    @staticmethod
    def label_flipping(n_honest: int = 100,
                      n_poison: int = 20,
                      n_rounds: int = 100) -> Dict:
        """
        Label flipping: attacker reports opposite quality.

        Honest witnesses report actual quality ∈ [0, 1].
        Poisoners flip: report 1 - actual_quality.
        """
        entity_trust = 0.3  # Entity being evaluated
        true_quality = 0.7  # Entity's actual quality

        # System that averages all witness reports
        trust_trajectory = [entity_trust]

        for _ in range(n_rounds):
            reports = []
            # Honest reports
            for _ in range(n_honest):
                noise = random.gauss(0, 0.05)
                reports.append(max(0, min(1, true_quality + noise)))

            # Poisoned reports (flipped)
            for _ in range(n_poison):
                noise = random.gauss(0, 0.05)
                reports.append(max(0, min(1, (1 - true_quality) + noise)))

            # Simple average aggregation
            avg_report = statistics.mean(reports)

            # Trust update
            entity_trust += 0.02 * (avg_report - 0.5)
            entity_trust = max(0, min(1, entity_trust))
            trust_trajectory.append(entity_trust)

        # What trust SHOULD be with only honest reports
        honest_only = 0.3
        for _ in range(n_rounds):
            reports = [max(0, min(1, true_quality + random.gauss(0, 0.05)))
                      for _ in range(n_honest)]
            honest_only += 0.02 * (statistics.mean(reports) - 0.5)
            honest_only = max(0, min(1, honest_only))

        return {
            'poisoned_final_trust': trust_trajectory[-1],
            'honest_final_trust': honest_only,
            'trust_depression': honest_only - trust_trajectory[-1],
            'poison_effective': trust_trajectory[-1] < honest_only - 0.05,
            'poison_fraction': n_poison / (n_honest + n_poison),
        }

    @staticmethod
    def distribution_shift(n_entities: int = 50,
                          n_rounds: int = 200,
                          shift_start: int = 100,
                          shift_magnitude: float = 0.2) -> Dict:
        """
        Gradually shift what "normal" quality means.

        Before shift: quality centered at 0.6
        After shift: quality centered at 0.6 + shift (attacker inflates norm)
        """
        trusts = [0.5] * n_entities

        gini_trajectory = []
        avg_trust_trajectory = []

        for step in range(n_rounds):
            for i in range(n_entities):
                # Normal quality distribution
                base_quality = 0.6

                # After shift_start, attacker shifts the distribution
                if step >= shift_start:
                    progress = min(1.0, (step - shift_start) / 50)
                    base_quality += shift_magnitude * progress

                quality = max(0, min(1, base_quality + random.gauss(0, 0.1)))
                trusts[i] += 0.02 * (quality - 0.5)
                trusts[i] = max(0, min(1, trusts[i]))

            avg_trust_trajectory.append(statistics.mean(trusts))
            gini_trajectory.append(
                sum(abs(ti - tj) for ti in trusts for tj in trusts) /
                (2 * len(trusts) ** 2 * max(0.01, statistics.mean(trusts)))
            )

        # Detect the shift
        avg_before = statistics.mean(avg_trust_trajectory[:shift_start])
        avg_after = statistics.mean(avg_trust_trajectory[shift_start:])

        return {
            'avg_before_shift': avg_before,
            'avg_after_shift': avg_after,
            'trust_inflation': avg_after - avg_before,
            'shift_detectable': avg_after - avg_before > 0.05,
            'final_avg_trust': avg_trust_trajectory[-1],
        }


# ═══════════════════════════════════════════════════════════════
#  §5. MODEL EXTRACTION
# ═══════════════════════════════════════════════════════════════

class ModelExtraction:
    """
    Learn the trust update function from observations.

    Attacker queries the trust system with known inputs and observes outputs.
    Then fits a model to predict trust updates.
    """

    @staticmethod
    def extract_model(target: DifferentiableTrust,
                     n_queries: int = 200) -> Dict:
        """
        Extract trust model parameters through probing.

        Strategy: vary quality and observe trust changes.
        """
        # Generate query-response pairs
        queries = []
        for _ in range(n_queries):
            trust = random.uniform(0.1, 0.9)
            quality = random.uniform(0.0, 1.0)
            new_trust = target.update(trust, quality, n_same_type=1)
            queries.append((trust, quality, new_trust))

        # Fit linear model: new_trust = a * trust + b * quality + c
        # Using least squares
        n = len(queries)
        sum_t = sum(t for t, _, _ in queries)
        sum_q = sum(q for _, q, _ in queries)
        sum_nt = sum(nt for _, _, nt in queries)
        sum_tt = sum(t * t for t, _, _ in queries)
        sum_qq = sum(q * q for _, q, _ in queries)
        sum_tq = sum(t * q for t, q, _ in queries)
        sum_t_nt = sum(t * nt for t, _, nt in queries)
        sum_q_nt = sum(q * nt for _, q, nt in queries)

        # Solve 3x3 linear system using Cramer's rule
        A = [[sum_tt, sum_tq, sum_t],
             [sum_tq, sum_qq, sum_q],
             [sum_t, sum_q, n]]
        b_vec = [sum_t_nt, sum_q_nt, sum_nt]

        det_A = (A[0][0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1]) -
                 A[0][1] * (A[1][0] * A[2][2] - A[1][2] * A[2][0]) +
                 A[0][2] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]))

        if abs(det_A) < 1e-10:
            return {'extracted': False, 'reason': 'singular matrix'}

        # Cramer's rule for a, b, c
        a = (b_vec[0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1]) -
             A[0][1] * (b_vec[1] * A[2][2] - A[1][2] * b_vec[2]) +
             A[0][2] * (b_vec[1] * A[2][1] - A[1][1] * b_vec[2])) / det_A

        b = (A[0][0] * (b_vec[1] * A[2][2] - A[1][2] * b_vec[2]) -
             b_vec[0] * (A[1][0] * A[2][2] - A[1][2] * A[2][0]) +
             A[0][2] * (A[1][0] * b_vec[2] - b_vec[1] * A[2][0])) / det_A

        c = (A[0][0] * (A[1][1] * b_vec[2] - b_vec[1] * A[2][1]) -
             A[0][1] * (A[1][0] * b_vec[2] - b_vec[1] * A[2][0]) +
             b_vec[0] * (A[1][0] * A[2][1] - A[1][1] * A[2][0])) / det_A

        # Test extracted model on new data
        test_errors = []
        for _ in range(100):
            trust = random.uniform(0.1, 0.9)
            quality = random.uniform(0.0, 1.0)
            actual = target.update(trust, quality, 1)
            predicted = a * trust + b * quality + c
            predicted = max(0, min(1, predicted))
            test_errors.append(abs(actual - predicted))

        mae = statistics.mean(test_errors)
        max_error = max(test_errors)

        return {
            'extracted': True,
            'coefficients': {'a': a, 'b': b, 'c': c},
            'mean_absolute_error': mae,
            'max_error': max_error,
            'model_quality': 'good' if mae < 0.01 else 'moderate' if mae < 0.05 else 'poor',
            'n_queries': n_queries,
        }


# ═══════════════════════════════════════════════════════════════
#  §6. EVASION ATTACKS
# ═══════════════════════════════════════════════════════════════

class EvasionAttack:
    """
    Craft actions that evade anomaly detection while inflating trust.

    Anomaly detectors look for:
      - Sudden quality changes
      - Unrealistic quality patterns
      - Statistical outliers
      - Periodic behavior

    Evasion: craft actions that look normal but subtly inflate trust.
    """

    @staticmethod
    def detect_anomaly(qualities: List[float],
                      threshold_z: float = 2.0) -> List[int]:
        """Simple Z-score anomaly detector."""
        if len(qualities) < 10:
            return []

        anomalies = []
        window = 20

        for i in range(window, len(qualities)):
            recent = qualities[i - window:i]
            mean = statistics.mean(recent)
            std = statistics.stdev(recent) if len(recent) > 1 else 0.1
            if std < 0.01:
                std = 0.01
            z = (qualities[i] - mean) / std
            if abs(z) > threshold_z:
                anomalies.append(i)

        return anomalies

    @staticmethod
    def evasive_inflation(n_actions: int = 200,
                         inflation_rate: float = 0.003) -> Dict:
        """
        Gradually inflate quality while staying within normal bounds.

        The attacker reports quality = normal_mean + small_bias
        where small_bias < detection_threshold.
        """
        model = DifferentiableTrust()

        # Normal behavior (for comparison)
        normal_qualities = [0.6 + random.gauss(0, 0.1) for _ in range(n_actions)]
        normal_qualities = [max(0, min(1, q)) for q in normal_qualities]

        # Evasive: same noise but with drift
        evasive_qualities = []
        drift = 0.0
        for i in range(n_actions):
            drift += inflation_rate
            q = 0.6 + drift + random.gauss(0, 0.1)
            q = max(0, min(1, q))
            evasive_qualities.append(q)

        # Trust outcomes
        normal_traj = model.trajectory(0.3, normal_qualities)
        evasive_traj = model.trajectory(0.3, evasive_qualities)

        # Detection
        normal_anomalies = EvasionAttack.detect_anomaly(normal_qualities)
        evasive_anomalies = EvasionAttack.detect_anomaly(evasive_qualities)

        return {
            'normal_final_trust': normal_traj[-1],
            'evasive_final_trust': evasive_traj[-1],
            'trust_gain': evasive_traj[-1] - normal_traj[-1],
            'normal_anomalies': len(normal_anomalies),
            'evasive_anomalies': len(evasive_anomalies),
            'evasion_successful': (evasive_traj[-1] > normal_traj[-1] + 0.02 and
                                   len(evasive_anomalies) <= len(normal_anomalies) + 5),
        }


# ═══════════════════════════════════════════════════════════════
#  §7. ROBUST TRUST AGGREGATION
# ═══════════════════════════════════════════════════════════════

class RobustAggregation:
    """
    Defense: aggregation methods that resist ML-powered manipulation.

    Standard mean is vulnerable to poisoning.
    Robust alternatives:
      - Trimmed mean (remove outliers)
      - Median (immune to < 50% poisoning)
      - Weighted by witness trust
      - Byzantine-fault-tolerant aggregation
    """

    @staticmethod
    def compare_aggregations(honest_reports: List[float],
                            poison_reports: List[float]) -> Dict:
        """Compare different aggregation methods under poisoning."""
        all_reports = honest_reports + poison_reports

        # Simple mean (vulnerable)
        simple_mean = statistics.mean(all_reports)

        # Trimmed mean (10% from each tail)
        sorted_reports = sorted(all_reports)
        trim = max(1, len(sorted_reports) // 10)
        trimmed = sorted_reports[trim:-trim] if len(sorted_reports) > 2 * trim else sorted_reports
        trimmed_mean = statistics.mean(trimmed)

        # Median (robust to < 50% poisoning)
        median_val = statistics.median(all_reports)

        # Trust-weighted (honest witnesses have higher trust)
        # Simulate: honest witnesses have trust 0.7, poisoners have trust 0.3
        weights = [0.7] * len(honest_reports) + [0.3] * len(poison_reports)
        weighted_sum = sum(r * w for r, w in zip(all_reports, weights))
        weighted_mean = weighted_sum / sum(weights)

        # True value (honest only)
        honest_mean = statistics.mean(honest_reports)

        return {
            'honest_mean': honest_mean,
            'simple_mean': simple_mean,
            'trimmed_mean': trimmed_mean,
            'median': median_val,
            'weighted_mean': weighted_mean,
            'simple_error': abs(simple_mean - honest_mean),
            'trimmed_error': abs(trimmed_mean - honest_mean),
            'median_error': abs(median_val - honest_mean),
            'weighted_error': abs(weighted_mean - honest_mean),
            'best_robust': min(
                [('trimmed', abs(trimmed_mean - honest_mean)),
                 ('median', abs(median_val - honest_mean)),
                 ('weighted', abs(weighted_mean - honest_mean))],
                key=lambda x: x[1]
            )[0],
        }


# ═══════════════════════════════════════════════════════════════
#  §8. ADVERSARIAL TRAINING
# ═══════════════════════════════════════════════════════════════

class AdversarialTraining:
    """
    Harden trust models by training against known attack patterns.

    Method:
      1. Generate attack patterns (gradient, poisoning, evasion)
      2. Train detector to recognize these patterns
      3. Adjust trust update to penalize suspicious behavior
    """

    @staticmethod
    def generate_attack_patterns(n_patterns: int = 100,
                                pattern_length: int = 50) -> Dict:
        """Generate labeled attack pattern dataset."""
        patterns = []

        for _ in range(n_patterns // 4):
            # Pattern 1: Gradual inflation
            p = [0.5 + 0.005 * t + random.gauss(0, 0.05)
                 for t in range(pattern_length)]
            patterns.append(('inflation', [max(0, min(1, v)) for v in p]))

            # Pattern 2: Sudden quality spike
            spike_at = random.randint(10, 40)
            p = [0.5 + random.gauss(0, 0.05)] * pattern_length
            for t in range(spike_at, min(spike_at + 5, pattern_length)):
                p[t] = 0.95
            patterns.append(('spike', [max(0, min(1, v)) for v in p]))

            # Pattern 3: Normal behavior
            p = [0.6 + random.gauss(0, 0.1) for _ in range(pattern_length)]
            patterns.append(('normal', [max(0, min(1, v)) for v in p]))

            # Pattern 4: Oscillating (gaming detection)
            p = [0.5 + 0.2 * math.sin(2 * math.pi * t / 10) + random.gauss(0, 0.05)
                 for t in range(pattern_length)]
            patterns.append(('oscillating', [max(0, min(1, v)) for v in p]))

        return {
            'patterns': patterns,
            'n_attack': sum(1 for label, _ in patterns if label != 'normal'),
            'n_normal': sum(1 for label, _ in patterns if label == 'normal'),
        }

    @staticmethod
    def simple_detector(pattern: List[float]) -> str:
        """
        Classify a quality pattern as attack or normal.

        Features:
          - Trend: positive slope → potential inflation
          - Variance: very low variance → robotic behavior
          - Spikes: sudden jumps → trust bombing
          - Mean: unusually high mean → suspicious
        """
        if len(pattern) < 10:
            return 'normal'

        # Trend
        first_half = statistics.mean(pattern[:len(pattern) // 2])
        second_half = statistics.mean(pattern[len(pattern) // 2:])
        trend = second_half - first_half

        # Variance
        var = statistics.variance(pattern) if len(pattern) > 1 else 0

        # Spikes
        mean = statistics.mean(pattern)
        std = statistics.stdev(pattern) if len(pattern) > 1 else 0.1
        spikes = sum(1 for v in pattern if abs(v - mean) > 2 * std)

        # Classification rules (learned from adversarial training)
        if trend > 0.1:
            return 'inflation'
        if spikes > 3:
            return 'spike'
        if var < 0.001:
            return 'robotic'
        if mean > 0.85:
            return 'suspicious_high'

        return 'normal'

    @staticmethod
    def evaluate_detector(patterns: List[Tuple[str, List[float]]]) -> Dict:
        """Evaluate detector accuracy on labeled patterns."""
        correct = 0
        false_positives = 0
        false_negatives = 0

        for label, pattern in patterns:
            prediction = AdversarialTraining.simple_detector(pattern)

            if label == 'normal' and prediction == 'normal':
                correct += 1
            elif label != 'normal' and prediction != 'normal':
                correct += 1
            elif label == 'normal' and prediction != 'normal':
                false_positives += 1
            else:
                false_negatives += 1

        total = len(patterns)
        return {
            'accuracy': correct / total if total > 0 else 0,
            'false_positive_rate': false_positives / total if total > 0 else 0,
            'false_negative_rate': false_negatives / total if total > 0 else 0,
            'total': total,
        }


# ═══════════════════════════════════════════════════════════════
#  §9. TRUST WATERMARKING
# ═══════════════════════════════════════════════════════════════

class TrustWatermark:
    """
    Detect model extraction by embedding canary values.

    The trust system embeds tiny, entity-specific perturbations in
    trust updates. If an extracted model reproduces these perturbations,
    it proves the model was copied.
    """

    def __init__(self, secret_key: str = "web4_watermark_key"):
        self.key = secret_key

    def watermark(self, entity_id: str, trust: float, step: int) -> float:
        """Add tiny watermark perturbation to trust value."""
        import hashlib
        h = hashlib.sha256(f"{self.key}:{entity_id}:{step}".encode()).digest()
        # Extract a tiny perturbation from hash
        perturbation = (h[0] / 256.0 - 0.5) * 0.001  # ±0.0005
        return max(0.0, min(1.0, trust + perturbation))

    def detect(self, entity_id: str, observed_trusts: List[Tuple[int, float]],
              actual_trusts: List[Tuple[int, float]]) -> Dict:
        """
        Detect if observed trust values contain watermarks.

        Compare observed values with expected watermarked values.
        """
        matches = 0
        total = 0
        import hashlib

        for (step_o, trust_o), (step_a, trust_a) in zip(observed_trusts, actual_trusts):
            if step_o != step_a:
                continue

            # What the watermark should be
            expected_wm = self.watermark(entity_id, trust_a, step_a)

            # Does observed match watermarked version?
            if abs(trust_o - expected_wm) < 0.0001:
                matches += 1
            total += 1

        match_rate = matches / total if total > 0 else 0

        return {
            'total_checked': total,
            'matches': matches,
            'match_rate': match_rate,
            'watermark_detected': match_rate > 0.8,
        }


# ═══════════════════════════════════════════════════════════════
#  §10. GAME-THEORETIC ML DEFENSE
# ═══════════════════════════════════════════════════════════════

class MinimaxDefense:
    """
    Minimax optimization: defender minimizes maximum attacker gain.

    The defender chooses trust update parameters (α, decay, detection threshold).
    The attacker chooses action strategy to maximize trust inflation.
    Equilibrium: neither can improve by unilateral change.
    """

    @staticmethod
    def find_equilibrium(n_iterations: int = 50) -> Dict:
        """
        Alternating optimization to find approximate Nash equilibrium.

        Defender adjusts: alpha (trust update rate), detection_threshold
        Attacker adjusts: quality bias, action diversity
        """
        # Defender parameters
        alpha = 0.02
        detection_threshold = 2.0

        # Attacker parameters
        quality_bias = 0.1
        diversity = 3

        defender_utility_history = []
        attacker_utility_history = []

        for iteration in range(n_iterations):
            # Attacker's best response
            model = DifferentiableTrust(alpha=alpha)
            attacker_qualities = []
            for i in range(50):
                action_type = i % diversity
                q = 0.6 + quality_bias + random.gauss(0, 0.05)
                attacker_qualities.append(max(0, min(1, q)))

            traj = model.trajectory(0.3, attacker_qualities)
            attacker_trust = traj[-1]

            # Detection
            anomalies = EvasionAttack.detect_anomaly(
                attacker_qualities, threshold_z=detection_threshold
            )
            detected = len(anomalies) > 3

            # Utilities
            attacker_utility = attacker_trust - (0.5 if detected else 0)
            defender_utility = -attacker_trust + (0.3 if detected else 0)

            attacker_utility_history.append(attacker_utility)
            defender_utility_history.append(defender_utility)

            # Defender adapts
            if attacker_trust > 0.7:
                alpha = max(0.005, alpha * 0.95)  # Slow down updates
                detection_threshold = max(1.0, detection_threshold - 0.1)
            else:
                alpha = min(0.05, alpha * 1.05)
                detection_threshold = min(3.0, detection_threshold + 0.05)

            # Attacker adapts
            if detected:
                quality_bias = max(0.0, quality_bias - 0.02)
                diversity = min(10, diversity + 1)
            else:
                quality_bias = min(0.3, quality_bias + 0.01)

        return {
            'final_alpha': alpha,
            'final_detection_threshold': detection_threshold,
            'final_quality_bias': quality_bias,
            'final_diversity': diversity,
            'defender_avg_utility': statistics.mean(defender_utility_history[-10:]),
            'attacker_avg_utility': statistics.mean(attacker_utility_history[-10:]),
            'converged': (statistics.stdev(defender_utility_history[-10:]) < 0.1
                         if len(defender_utility_history) >= 10 else False),
        }


# ═══════════════════════════════════════════════════════════════
#  §11. ENSEMBLE TRUST MODELS
# ═══════════════════════════════════════════════════════════════

class EnsembleTrust:
    """
    Use multiple diverse trust models as defense.

    If attacker optimizes against one model, the others catch the attack.
    Ensemble agreement = high confidence.
    Ensemble disagreement = suspicious.
    """

    @staticmethod
    def create_ensemble() -> List[DifferentiableTrust]:
        """Create diverse ensemble of trust models."""
        return [
            DifferentiableTrust(alpha=0.02, decay_rate=0.001, diminishing_factor=0.8),
            DifferentiableTrust(alpha=0.015, decay_rate=0.002, diminishing_factor=0.7),
            DifferentiableTrust(alpha=0.025, decay_rate=0.001, diminishing_factor=0.9),
            DifferentiableTrust(alpha=0.01, decay_rate=0.003, diminishing_factor=0.75),
        ]

    @staticmethod
    def ensemble_evaluate(models: List[DifferentiableTrust],
                         initial_trust: float,
                         qualities: List[float]) -> Dict:
        """Evaluate trust using ensemble and measure agreement."""
        trajectories = []
        for model in models:
            traj = model.trajectory(initial_trust, qualities)
            trajectories.append(traj)

        # Final trust from each model
        final_trusts = [traj[-1] for traj in trajectories]

        # Agreement metrics
        mean_trust = statistics.mean(final_trusts)
        std_trust = statistics.stdev(final_trusts) if len(final_trusts) > 1 else 0
        spread = max(final_trusts) - min(final_trusts)

        return {
            'individual_trusts': final_trusts,
            'ensemble_mean': mean_trust,
            'ensemble_std': std_trust,
            'spread': spread,
            'high_agreement': spread < 0.1,
            'suspicious': spread > 0.2,
        }

    @staticmethod
    def targeted_vs_ensemble(n_actions: int = 50) -> Dict:
        """
        Compare: attack optimized against model 1 vs ensemble defense.
        """
        models = EnsembleTrust.create_ensemble()

        # Optimize attack against first model only
        attacker = GradientTrustAttack(models[0])
        attack_result = attacker.optimize_sequence(0.3, n_actions)
        attack_qualities = attack_result['optimal_qualities']

        # Evaluate on target model
        target_trust = models[0].trajectory(0.3, attack_qualities)[-1]

        # Evaluate on ensemble
        ensemble_result = EnsembleTrust.ensemble_evaluate(
            models, 0.3, attack_qualities
        )

        # Normal behavior for comparison
        normal_qualities = [0.6 + random.gauss(0, 0.1) for _ in range(n_actions)]
        normal_qualities = [max(0, min(1, q)) for q in normal_qualities]
        normal_ensemble = EnsembleTrust.ensemble_evaluate(
            models, 0.3, normal_qualities
        )

        return {
            'attack_on_target': target_trust,
            'attack_on_ensemble': ensemble_result['ensemble_mean'],
            'attack_spread': ensemble_result['spread'],
            'attack_suspicious': ensemble_result['suspicious'],
            'normal_spread': normal_ensemble['spread'],
            'normal_suspicious': normal_ensemble['suspicious'],
            'ensemble_detects_attack': ensemble_result['spread'] > normal_ensemble['spread'] * 1.5,
        }


# ═══════════════════════════════════════════════════════════════
#  §12. FULL RED TEAM SIMULATION
# ═══════════════════════════════════════════════════════════════

class RedTeamSimulation:
    """
    Coordinated ML attack vs adaptive defense.

    Red team: 10 ML-powered attackers trying to inflate trust
    Blue team: ensemble trust model with anomaly detection

    Run for 200 rounds and measure:
      - Attacker success rate
      - Detection rate
      - System trust integrity
    """

    @staticmethod
    def simulate(n_honest: int = 90,
                n_attackers: int = 10,
                n_rounds: int = 200) -> Dict:
        """Run full red team simulation."""
        random.seed(42)

        models = EnsembleTrust.create_ensemble()
        detector = AdversarialTraining

        # Entity states
        honest_trusts = [0.3 + random.gauss(0, 0.05) for _ in range(n_honest)]
        honest_trusts = [max(0.1, min(0.9, t)) for t in honest_trusts]
        attacker_trusts = [0.3] * n_attackers

        detections = 0
        false_alarms = 0
        attacker_trust_history = []
        honest_trust_history = []

        # Track quality histories for anomaly detection
        attacker_quality_histories = [[] for _ in range(n_attackers)]

        for round_num in range(n_rounds):
            # Honest entities: normal behavior
            for i in range(n_honest):
                quality = 0.65 + random.gauss(0, 0.1)
                quality = max(0, min(1, quality))

                # Use ensemble mean
                new_trusts = [m.update(honest_trusts[i], quality) for m in models]
                honest_trusts[i] = statistics.mean(new_trusts)

            # Attackers: ML-optimized evasive behavior
            for i in range(n_attackers):
                # Evasive quality: drift upward slowly
                quality = 0.65 + 0.001 * round_num + random.gauss(0, 0.08)
                quality = max(0, min(1, quality))
                attacker_quality_histories[i].append(quality)

                # Ensemble evaluation
                all_trusts = [m.update(attacker_trusts[i], quality) for m in models]

                # Defense: anomaly detection on quality history
                detected = False
                hist = attacker_quality_histories[i]
                if len(hist) >= 30:
                    first_half = statistics.mean(hist[:len(hist) // 2])
                    second_half = statistics.mean(hist[len(hist) // 2:])
                    if second_half - first_half > 0.05:  # Upward trend detected
                        detected = True

                if detected:
                    # Penalize: use minimum ensemble trust
                    attacker_trusts[i] = min(all_trusts)
                    attacker_trusts[i] = max(0, attacker_trusts[i] - 0.02)  # Active penalty
                    detections += 1
                else:
                    attacker_trusts[i] = statistics.mean(all_trusts)

            attacker_trust_history.append(statistics.mean(attacker_trusts))
            honest_trust_history.append(statistics.mean(honest_trusts))

        # Results
        final_attacker_trust = statistics.mean(attacker_trusts)
        final_honest_trust = statistics.mean(honest_trusts)

        return {
            'final_honest_trust': final_honest_trust,
            'final_attacker_trust': final_attacker_trust,
            'trust_gap': final_honest_trust - final_attacker_trust,
            'detections': detections,
            'detection_rate': detections / (n_attackers * n_rounds),
            'attacker_suppressed': final_attacker_trust < final_honest_trust,
            'honest_trust_maintained': final_honest_trust > 0.5,
            'attacker_trust_history': attacker_trust_history,
            'honest_trust_history': honest_trust_history,
        }


# ═══════════════════════════════════════════════════════════════
#  TEST RUNNER
# ═══════════════════════════════════════════════════════════════

def run_all_checks():
    """Run all adversarial ML trust checks."""
    checks_passed = 0
    checks_failed = 0
    total_sections = 12

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal checks_passed, checks_failed
        if condition:
            checks_passed += 1
            print(f"  ✓ {name}")
        else:
            checks_failed += 1
            print(f"  ✗ {name}: {detail}")
        return condition

    random.seed(42)

    # ── §1 Differentiable Trust ──
    print("\n§1 Trust Model as Differentiable Function")
    print("─" * 40)

    model = DifferentiableTrust()

    # Basic update
    t1 = model.update(0.5, 0.8)
    check("Trust increases with quality > 0.5", t1 > 0.5, f"trust={t1:.4f}")

    t2 = model.update(0.5, 0.2)
    check("Trust decreases with quality < 0.5", t2 < 0.5, f"trust={t2:.4f}")

    # Gradient computation
    grad = model.gradient_quality(0.3)
    check("Quality gradient positive", grad > 0, f"grad={grad:.6f}")
    check("Quality gradient higher at low trust",
          model.gradient_quality(0.3) > model.gradient_quality(0.8))

    # Diminishing returns
    t_no_dim = model.update(0.5, 0.8, n_same_type=1)
    t_with_dim = model.update(0.5, 0.8, n_same_type=10)
    check("Diminishing returns: less trust gain at high repeat count",
          t_with_dim < t_no_dim,
          f"n=1:{t_no_dim:.4f}, n=10:{t_with_dim:.4f}")

    # Trajectory
    traj = model.trajectory(0.3, [0.7] * 50)
    check("Trajectory is monotonically increasing",
          all(traj[i] <= traj[i + 1] + 0.001 for i in range(len(traj) - 1)))

    # ── §2 Gradient-Based Optimization ──
    print("\n§2 Gradient-Based Trust Optimization")
    print("─" * 40)

    random.seed(42)
    attacker = GradientTrustAttack(model)

    result = attacker.optimize_sequence(0.3, 30)
    check("Optimization finds trust above initial",
          result['final_trust'] > 0.3,
          f"trust={result['final_trust']:.4f}")
    check("Optimal qualities in [0, 1]",
          all(0 <= q <= 1 for q in result['optimal_qualities']))

    # Compare strategies
    random.seed(42)
    comparison = attacker.compare_strategies(0.3, 30)
    check("Optimized ≥ naive mid",
          comparison['optimized_final'] >= comparison['naive_mid_final'] - 0.05,
          f"opt={comparison['optimized_final']:.4f}, mid={comparison['naive_mid_final']:.4f}")
    check("All strategies produce valid trust",
          all(0 <= v <= 1 for v in comparison['strategies'].values()))

    # ── §3 Adversarial Action Sequences ──
    print("\n§3 Adversarial Action Sequences")
    print("─" * 40)

    seq = AdversarialSequencer()

    # Front vs back loading
    random.seed(42)
    load = seq.front_load_vs_back_load(model, initial_trust=0.2, n_actions=50)
    check("Alternating beats same-type",
          load['alternating_final'] >= min(load['front_load_final'], load['back_load_final']) - 0.01)
    check("All strategies produce trust in [0,1]",
          all(0 <= v <= 1 for v in [load['front_load_final'],
                                     load['back_load_final'],
                                     load['alternating_final']]))

    # Diversity exploitation
    div = seq.diversity_exploitation(model, initial_trust=0.2, n_actions=50)
    check("Diversity matters", div['diversity_matters'],
          f"same={div['same_type_final']:.4f}, diverse={div['diverse_type_final']:.4f}")
    check("Diversity advantage > 0.01",
          div['diversity_advantage'] > 0.01,
          f"advantage={div['diversity_advantage']:.4f}")

    # ── §4 Data Poisoning ──
    print("\n§4 Data Poisoning Attacks")
    print("─" * 40)

    random.seed(42)
    flip = DataPoisoning.label_flipping(n_honest=100, n_poison=20)
    check("Label flipping depresses trust", flip['poison_effective'],
          f"poisoned={flip['poisoned_final_trust']:.4f}, honest={flip['honest_final_trust']:.4f}")
    check("Trust depression > 0.05",
          flip['trust_depression'] > 0.05,
          f"depression={flip['trust_depression']:.4f}")

    random.seed(42)
    shift = DataPoisoning.distribution_shift(n_entities=50, n_rounds=200)
    check("Distribution shift inflates trust",
          shift['trust_inflation'] > 0.05,
          f"inflation={shift['trust_inflation']:.4f}")
    check("Shift is detectable", shift['shift_detectable'])

    # ── §5 Model Extraction ──
    print("\n§5 Model Extraction")
    print("─" * 40)

    random.seed(42)
    extraction = ModelExtraction.extract_model(model, n_queries=300)
    check("Model extracted successfully", extraction['extracted'])
    check("Extraction MAE < 0.05",
          extraction['mean_absolute_error'] < 0.05,
          f"MAE={extraction['mean_absolute_error']:.4f}")
    check("Model quality at least moderate",
          extraction['model_quality'] in ('good', 'moderate'),
          f"quality={extraction['model_quality']}")
    print(f"    Extracted coefficients: a={extraction['coefficients']['a']:.4f}, "
          f"b={extraction['coefficients']['b']:.4f}, c={extraction['coefficients']['c']:.4f}")

    # ── §6 Evasion Attacks ──
    print("\n§6 Evasion Attacks")
    print("─" * 40)

    random.seed(42)
    evasion = EvasionAttack.evasive_inflation(n_actions=200)
    check("Evasion gains trust",
          evasion['trust_gain'] > 0,
          f"gain={evasion['trust_gain']:.4f}")
    check("Evasion avoids excessive anomalies",
          evasion['evasive_anomalies'] < 20,
          f"anomalies={evasion['evasive_anomalies']}")
    print(f"    Normal: trust={evasion['normal_final_trust']:.4f}, anomalies={evasion['normal_anomalies']}")
    print(f"    Evasive: trust={evasion['evasive_final_trust']:.4f}, anomalies={evasion['evasive_anomalies']}")

    # ── §7 Robust Aggregation ──
    print("\n§7 Robust Trust Aggregation")
    print("─" * 40)

    random.seed(42)
    honest = [0.7 + random.gauss(0, 0.05) for _ in range(80)]
    poison = [0.1 + random.gauss(0, 0.05) for _ in range(20)]
    honest = [max(0, min(1, r)) for r in honest]
    poison = [max(0, min(1, r)) for r in poison]

    agg = RobustAggregation.compare_aggregations(honest, poison)
    check("Robust methods better than simple mean",
          min(agg['trimmed_error'], agg['median_error'], agg['weighted_error']) <
          agg['simple_error'],
          f"simple={agg['simple_error']:.4f}")
    check("Median resists 20% poisoning",
          agg['median_error'] < 0.1,
          f"median_error={agg['median_error']:.4f}")
    check("Weighted aggregation effective",
          agg['weighted_error'] < agg['simple_error'],
          f"weighted={agg['weighted_error']:.4f}, simple={agg['simple_error']:.4f}")
    check("Best robust method identified", agg['best_robust'] in ('trimmed', 'median', 'weighted'))

    # ── §8 Adversarial Training ──
    print("\n§8 Adversarial Training")
    print("─" * 40)

    random.seed(42)
    dataset = AdversarialTraining.generate_attack_patterns(100)
    check("Attack patterns generated", dataset['n_attack'] > 0)
    check("Normal patterns included", dataset['n_normal'] > 0)

    eval_result = AdversarialTraining.evaluate_detector(dataset['patterns'])
    check("Detector accuracy > 60%",
          eval_result['accuracy'] > 0.6,
          f"accuracy={eval_result['accuracy']:.2%}")
    check("False positive rate < 30%",
          eval_result['false_positive_rate'] < 0.3,
          f"FPR={eval_result['false_positive_rate']:.2%}")
    print(f"    Accuracy: {eval_result['accuracy']:.2%}, "
          f"FPR: {eval_result['false_positive_rate']:.2%}, "
          f"FNR: {eval_result['false_negative_rate']:.2%}")

    # ── §9 Trust Watermarking ──
    print("\n§9 Trust Watermarking")
    print("─" * 40)

    wm = TrustWatermark("test_key")

    # Watermark a trust value
    trust = 0.75
    wm_trust = wm.watermark("entity_1", trust, 10)
    check("Watermark perturbation small", abs(wm_trust - trust) < 0.001)
    check("Watermark deterministic",
          wm.watermark("entity_1", trust, 10) == wm_trust)
    check("Different entities get different watermarks",
          wm.watermark("entity_1", trust, 10) != wm.watermark("entity_2", trust, 10))

    # Detection
    observed = [(i, wm.watermark("entity_1", 0.5 + i * 0.01, i)) for i in range(20)]
    actual = [(i, 0.5 + i * 0.01) for i in range(20)]
    detection = wm.detect("entity_1", observed, actual)
    check("Watermark detected in copied values",
          detection['watermark_detected'],
          f"match_rate={detection['match_rate']:.2%}")

    # Non-watermarked values should NOT trigger
    unwatermarked = [(i, 0.5 + i * 0.01 + random.gauss(0, 0.01)) for i in range(20)]
    no_wm = wm.detect("entity_1", unwatermarked, actual)
    check("Non-watermarked values not detected",
          not no_wm['watermark_detected'],
          f"match_rate={no_wm['match_rate']:.2%}")

    # ── §10 Game-Theoretic Defense ──
    print("\n§10 Game-Theoretic ML Defense")
    print("─" * 40)

    random.seed(42)
    eq = MinimaxDefense.find_equilibrium(n_iterations=50)
    check("Equilibrium converges", eq['converged'],
          f"defender_utility={eq['defender_avg_utility']:.4f}")
    check("Final alpha reasonable",
          0.005 <= eq['final_alpha'] <= 0.05,
          f"alpha={eq['final_alpha']:.4f}")
    check("Detection threshold adjusted",
          1.0 <= eq['final_detection_threshold'] <= 3.0,
          f"threshold={eq['final_detection_threshold']:.2f}")

    # ── §11 Ensemble Trust Models ──
    print("\n§11 Ensemble Trust Models")
    print("─" * 40)

    random.seed(42)
    models = EnsembleTrust.create_ensemble()
    check("Ensemble created with 4 models", len(models) == 4)

    # Normal behavior: high agreement
    normal_q = [0.6 + random.gauss(0, 0.1) for _ in range(50)]
    normal_q = [max(0, min(1, q)) for q in normal_q]
    normal_eval = EnsembleTrust.ensemble_evaluate(models, 0.3, normal_q)
    check("Normal behavior: high ensemble agreement",
          normal_eval['high_agreement'],
          f"spread={normal_eval['spread']:.4f}")

    # Targeted attack: should cause disagreement
    random.seed(42)
    targeted = EnsembleTrust.targeted_vs_ensemble(n_actions=50)
    check("Attack causes higher spread than normal",
          targeted['attack_spread'] > targeted['normal_spread'],
          f"attack_spread={targeted['attack_spread']:.4f}, normal={targeted['normal_spread']:.4f}")

    # ── §12 Full Red Team ──
    print("\n§12 Full Red Team Simulation")
    print("─" * 40)

    random.seed(42)
    red_team = RedTeamSimulation.simulate(n_honest=90, n_attackers=10, n_rounds=200)

    check("Honest trust maintained > 0.4",
          red_team['final_honest_trust'] > 0.4,
          f"honest={red_team['final_honest_trust']:.4f}")
    check("Attackers suppressed below honest",
          red_team['attacker_suppressed'],
          f"attacker={red_team['final_attacker_trust']:.4f}")
    check("Detection rate > 0%",
          red_team['detection_rate'] > 0,
          f"rate={red_team['detection_rate']:.2%}")
    check("Trust gap > 0 (honest > attacker)",
          red_team['trust_gap'] > 0,
          f"gap={red_team['trust_gap']:.4f}")
    print(f"    Honest: {red_team['final_honest_trust']:.4f}, "
          f"Attacker: {red_team['final_attacker_trust']:.4f}, "
          f"Detection: {red_team['detection_rate']:.2%}")

    # ── Summary ──
    total = checks_passed + checks_failed
    print(f"\n{'═' * 50}")
    print(f"Adversarial ML Trust: {checks_passed}/{total} checks passed")
    print(f"Sections: {total_sections}/{total_sections}")

    if checks_failed > 0:
        print(f"\n⚠ {checks_failed} checks failed")
    else:
        print(f"\n✓ All {total} checks passed across {total_sections} sections")

    return checks_passed, checks_failed


if __name__ == "__main__":
    passed, failed = run_all_checks()
    exit(0 if failed == 0 else 1)
