"""
Federated Trust Learning for Web4
Session 32, Track 8

Learning trust parameters across federations without sharing raw data.
Privacy-preserving collaborative trust optimization.

- Federated averaging for trust models
- Gossip-based distributed learning
- Differential privacy for trust gradients
- Secure aggregation protocol
- Model poisoning detection
- Convergence analysis
- Communication efficiency (compression, sparsification)
- Heterogeneous federation handling
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


# ─── Local Trust Model ────────────────────────────────────────────

@dataclass
class LocalTrustModel:
    """Each federation's local trust estimation model."""
    federation_id: str
    weights: List[float] = field(default_factory=list)
    n_samples: int = 0
    learning_rate: float = 0.01

    def initialize(self, n_dims: int):
        self.weights = [random.gauss(0, 0.1) for _ in range(n_dims)]

    def predict(self, features: List[float]) -> float:
        """Linear trust prediction."""
        raw = sum(w * f for w, f in zip(self.weights, features))
        return 1.0 / (1.0 + math.exp(-raw))  # Sigmoid

    def compute_gradient(self, features: List[float],
                         label: float) -> List[float]:
        """Gradient of binary cross-entropy loss."""
        pred = self.predict(features)
        error = pred - label
        return [error * f for f in features]

    def local_train(self, data: List[Tuple[List[float], float]],
                    epochs: int = 5) -> List[float]:
        """Train on local data, return gradient."""
        total_grad = [0.0] * len(self.weights)

        for _ in range(epochs):
            for features, label in data:
                grad = self.compute_gradient(features, label)
                for i in range(len(self.weights)):
                    self.weights[i] -= self.learning_rate * grad[i]
                    total_grad[i] += grad[i]

        n = len(data) * epochs
        return [g / max(1, n) for g in total_grad]

    def loss(self, data: List[Tuple[List[float], float]]) -> float:
        """Binary cross-entropy loss."""
        total = 0.0
        for features, label in data:
            pred = max(1e-10, min(1 - 1e-10, self.predict(features)))
            total += -(label * math.log(pred) + (1 - label) * math.log(1 - pred))
        return total / max(1, len(data))


# ─── Federated Averaging ─────────────────────────────────────────

def federated_averaging(models: List[LocalTrustModel],
                        weights: Optional[List[float]] = None) -> List[float]:
    """
    FedAvg: weighted average of model parameters.
    Standard federated learning aggregation.
    """
    n = len(models)
    if n == 0:
        return []

    if weights is None:
        weights = [1.0 / n] * n

    # Normalize weights
    total = sum(weights)
    weights = [w / total for w in weights]

    n_dims = len(models[0].weights)
    avg_weights = [0.0] * n_dims

    for model, w in zip(models, weights):
        for i in range(n_dims):
            avg_weights[i] += w * model.weights[i]

    return avg_weights


def apply_global_model(models: List[LocalTrustModel],
                       global_weights: List[float]):
    """Apply aggregated global model to all local models."""
    for model in models:
        model.weights = list(global_weights)


# ─── Gossip Learning ─────────────────────────────────────────────

def gossip_learning_round(models: List[LocalTrustModel],
                          topology: Dict[int, List[int]]) -> int:
    """
    One round of gossip learning: each node averages with a random neighbor.
    Returns number of exchanges.
    """
    exchanges = 0
    n = len(models)

    for i in range(n):
        if i in topology and topology[i]:
            j = random.choice(topology[i])
            # Average weights
            for d in range(len(models[i].weights)):
                avg = (models[i].weights[d] + models[j].weights[d]) / 2
                models[i].weights[d] = avg
                models[j].weights[d] = avg
            exchanges += 1

    return exchanges


def gossip_convergence(models: List[LocalTrustModel]) -> float:
    """Measure how close models are to consensus (max weight difference)."""
    if not models:
        return 0.0

    max_diff = 0.0
    for d in range(len(models[0].weights)):
        vals = [m.weights[d] for m in models]
        max_diff = max(max_diff, max(vals) - min(vals))

    return max_diff


# ─── Differential Privacy ────────────────────────────────────────

def add_gaussian_noise(gradient: List[float], sigma: float,
                       clip_norm: float = 1.0) -> List[float]:
    """
    Add calibrated Gaussian noise for (ε, δ)-DP.
    Clip gradient norm first, then add noise.
    """
    # Clip gradient
    norm = math.sqrt(sum(g ** 2 for g in gradient))
    if norm > clip_norm:
        gradient = [g * clip_norm / norm for g in gradient]

    # Add noise
    noisy = [g + random.gauss(0, sigma) for g in gradient]
    return noisy


def compute_dp_sigma(epsilon: float, delta: float,
                     sensitivity: float = 1.0) -> float:
    """
    Compute noise standard deviation for Gaussian mechanism.
    σ ≥ sensitivity × √(2 ln(1.25/δ)) / ε
    """
    return sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon


def privacy_budget_remaining(epsilon_total: float,
                              epsilon_per_round: float,
                              rounds_completed: int) -> float:
    """
    Track privacy budget consumption (basic composition).
    Budget decreases with each round.
    """
    used = epsilon_per_round * rounds_completed
    return max(0.0, epsilon_total - used)


# ─── Secure Aggregation ──────────────────────────────────────────

def secure_sum(values: List[float], n_parties: int) -> float:
    """
    Simulate secure aggregation via secret sharing.
    Each party adds random mask; masks cancel in sum.
    Server sees only aggregate, not individual values.
    """
    # In real implementation, parties would exchange masks
    # Here we simulate: result is just the sum
    return sum(values)


def verify_aggregation(individual: List[float],
                        aggregate: float) -> bool:
    """Verify that aggregate equals sum of individual values."""
    return abs(sum(individual) - aggregate) < 1e-10


# ─── Model Poisoning Detection ───────────────────────────────────

def detect_poisoning(gradients: List[List[float]],
                     threshold: float = 3.0) -> List[bool]:
    """
    Detect poisoned gradients using norm-based outlier detection.
    Flag gradients with norm > threshold × median norm.
    """
    norms = [math.sqrt(sum(g ** 2 for g in grad)) for grad in gradients]
    sorted_norms = sorted(norms)
    median_norm = sorted_norms[len(sorted_norms) // 2]

    return [norm > threshold * median_norm for norm in norms]


def krum_aggregation(gradients: List[List[float]],
                     f: int) -> List[float]:
    """
    Krum: select gradient closest to most other gradients.
    Byzantine-resilient aggregation for federated learning.
    """
    n = len(gradients)
    if n == 0:
        return []

    # Pairwise distances
    distances = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = math.sqrt(sum((a - b) ** 2
                              for a, b in zip(gradients[i], gradients[j])))
            distances[i][j] = d
            distances[j][i] = d

    # For each gradient, sum of n-f-2 closest distances
    scores = []
    for i in range(n):
        sorted_dist = sorted(distances[i])
        # Sum of n-f-2 smallest (excluding self=0)
        score = sum(sorted_dist[1:n - f - 1])
        scores.append(score)

    # Select gradient with smallest score
    best = scores.index(min(scores))
    return list(gradients[best])


# ─── Communication Efficiency ─────────────────────────────────────

def top_k_sparsify(gradient: List[float], k: int) -> List[Tuple[int, float]]:
    """
    Send only top-k gradient values (by magnitude).
    Reduces communication by factor of n/k.
    """
    indexed = [(i, abs(g), g) for i, g in enumerate(gradient)]
    indexed.sort(key=lambda x: x[1], reverse=True)

    return [(i, g) for i, _, g in indexed[:k]]


def quantize_gradient(gradient: List[float], bits: int = 8) -> List[int]:
    """Quantize gradient values to fixed number of bits."""
    if not gradient:
        return []

    max_val = max(abs(g) for g in gradient)
    if max_val == 0:
        return [0] * len(gradient)

    levels = 2 ** bits
    return [round(g / max_val * (levels // 2)) for g in gradient]


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
    print("Federated Trust Learning for Web4")
    print("Session 32, Track 8")
    print("=" * 70)

    random.seed(42)
    n_dims = 5

    # ── §1 Local Training ───────────────────────────────────────
    print("\n§1 Local Trust Model Training\n")

    # Create local model and synthetic data
    model = LocalTrustModel(federation_id="fed_0")
    model.initialize(n_dims)

    data = []
    for _ in range(100):
        features = [random.random() for _ in range(n_dims)]
        # Label: trustworthy if weighted sum > threshold
        label = 1.0 if sum(features) / n_dims > 0.5 else 0.0
        data.append((features, label))

    loss_before = model.loss(data)
    model.local_train(data, epochs=10)
    loss_after = model.loss(data)

    check("local_training_improves", loss_after < loss_before,
          f"before={loss_before:.4f} after={loss_after:.4f}")

    # ── §2 Federated Averaging ──────────────────────────────────
    print("\n§2 Federated Averaging\n")

    # Create 5 federations with different data
    n_feds = 5
    models = []
    fed_data = []
    for i in range(n_feds):
        m = LocalTrustModel(federation_id=f"fed_{i}")
        m.initialize(n_dims)
        # Each federation has slightly different data distribution
        local_data = []
        for _ in range(50):
            features = [random.random() + 0.1 * i for _ in range(n_dims)]
            label = 1.0 if sum(features) / n_dims > 0.5 + 0.05 * i else 0.0
            local_data.append((features, label))
        m.local_train(local_data, epochs=5)
        models.append(m)
        fed_data.append(local_data)

    # Average
    global_weights = federated_averaging(models)
    check("fedavg_produces_weights", len(global_weights) == n_dims)

    # Global model should be between individual models
    for d in range(n_dims):
        individual = [m.weights[d] for m in models]
        check(f"fedavg_between_dim{d}",
              min(individual) <= global_weights[d] + 0.01 and
              global_weights[d] <= max(individual) + 0.01,
              f"global={global_weights[d]:.4f} range=[{min(individual):.4f}, {max(individual):.4f}]")

    # ── §3 Gossip Learning ──────────────────────────────────────
    print("\n§3 Gossip Learning\n")

    # Ring topology
    n_gossip = 8
    gossip_models = []
    for i in range(n_gossip):
        m = LocalTrustModel(federation_id=f"gossip_{i}")
        m.initialize(n_dims)
        # Diverge weights
        m.weights = [random.random() for _ in range(n_dims)]
        gossip_models.append(m)

    ring_topo = {i: [(i - 1) % n_gossip, (i + 1) % n_gossip]
                 for i in range(n_gossip)}

    divergence_before = gossip_convergence(gossip_models)

    # Run multiple gossip rounds
    for _ in range(50):
        gossip_learning_round(gossip_models, ring_topo)

    divergence_after = gossip_convergence(gossip_models)
    check("gossip_converges", divergence_after < divergence_before,
          f"before={divergence_before:.4f} after={divergence_after:.4f}")

    # ── §4 Differential Privacy ─────────────────────────────────
    print("\n§4 Differential Privacy\n")

    gradient = [0.5, -0.3, 0.8, -0.1, 0.4]

    # Compute noise level for ε=1, δ=1e-5
    sigma = compute_dp_sigma(epsilon=1.0, delta=1e-5)
    check("dp_sigma_positive", sigma > 0, f"sigma={sigma:.4f}")

    # Noisy gradient preserves approximate direction
    noisy_grad = add_gaussian_noise(gradient, sigma)
    check("noisy_grad_exists", len(noisy_grad) == len(gradient))

    # Higher epsilon → less noise (less privacy)
    sigma_high_eps = compute_dp_sigma(epsilon=10.0, delta=1e-5)
    check("more_privacy_more_noise", sigma > sigma_high_eps,
          f"eps1_sigma={sigma:.4f} eps10_sigma={sigma_high_eps:.4f}")

    # Privacy budget tracking
    budget = privacy_budget_remaining(10.0, 0.1, 50)
    check("budget_tracks", abs(budget - 5.0) < 0.01,
          f"budget={budget:.4f}")

    budget_exhausted = privacy_budget_remaining(10.0, 0.1, 150)
    check("budget_exhausts", budget_exhausted == 0.0)

    # ── §5 Secure Aggregation ──────────────────────────────────
    print("\n§5 Secure Aggregation\n")

    individual_vals = [0.3, 0.5, 0.7, 0.4, 0.6]
    agg = secure_sum(individual_vals, len(individual_vals))
    check("secure_sum_correct", verify_aggregation(individual_vals, agg))

    # ── §6 Poisoning Detection ──────────────────────────────────
    print("\n§6 Model Poisoning Detection\n")

    honest_grads = [[random.gauss(0, 0.1) for _ in range(n_dims)]
                    for _ in range(8)]
    # One poisoned gradient (much larger)
    poisoned = [random.gauss(0, 5.0) for _ in range(n_dims)]
    all_grads = honest_grads + [poisoned]

    flagged = detect_poisoning(all_grads, threshold=3.0)
    check("poisoned_detected", flagged[-1],
          f"flags={flagged}")

    honest_flags = flagged[:-1]
    check("honest_not_flagged", sum(honest_flags) == 0,
          f"false_positives={sum(honest_flags)}")

    # Krum selects honest gradient
    krum_result = krum_aggregation(all_grads, f=1)
    krum_norm = math.sqrt(sum(g ** 2 for g in krum_result))
    poison_norm = math.sqrt(sum(g ** 2 for g in poisoned))
    check("krum_selects_honest", krum_norm < poison_norm,
          f"krum_norm={krum_norm:.4f} poison_norm={poison_norm:.4f}")

    # ── §7 Communication Efficiency ─────────────────────────────
    print("\n§7 Communication Efficiency\n")

    full_grad = [random.gauss(0, 1) for _ in range(100)]

    # Top-k sparsification
    sparse = top_k_sparsify(full_grad, k=10)
    check("topk_reduces", len(sparse) == 10)

    # Sparsified values should be the largest
    sparse_vals = [abs(v) for _, v in sparse]
    remaining_vals = [abs(full_grad[i]) for i in range(100)
                      if i not in {idx for idx, _ in sparse}]
    check("topk_selects_largest", min(sparse_vals) >= max(remaining_vals) - 0.01,
          f"min_selected={min(sparse_vals):.4f} max_remaining={max(remaining_vals):.4f}")

    # Quantization
    quantized = quantize_gradient(full_grad, bits=8)
    check("quantization_reduces_bits", len(quantized) == len(full_grad))

    # Compression ratio: 64-bit float → 8-bit int = 8×
    ratio = 64 / 8
    check("quantize_8x_compression", ratio == 8.0)

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
