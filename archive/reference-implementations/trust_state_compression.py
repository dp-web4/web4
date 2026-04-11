"""
Trust State Compression for Web4
Session 32, Track 5

How efficiently can trust state be represented and communicated?
Information-theoretic limits on trust compression.

- Entropy of trust distributions
- Rate-distortion theory for trust scores
- Quantization levels and error bounds
- Trust sketches (approximate data structures)
- Bloom filter attestation sets
- Count-Min Sketch for trust counters
- Delta encoding for trust updates
- Compression ratio analysis
"""

import math
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set


# ─── Entropy & Information ────────────────────────────────────────

def entropy(distribution: List[float], eps: float = 1e-15) -> float:
    """Shannon entropy of a probability distribution."""
    return -sum(p * math.log2(max(eps, p)) for p in distribution if p > eps)


def conditional_entropy(joint: List[List[float]], eps: float = 1e-15) -> float:
    """H(Y|X) from joint distribution."""
    h_xy = 0.0
    for row in joint:
        for p in row:
            if p > eps:
                h_xy -= p * math.log2(p)

    # H(X)
    px = [sum(row) for row in joint]
    h_x = -sum(p * math.log2(max(eps, p)) for p in px if p > eps)

    return h_xy - h_x


def trust_entropy(scores: List[float], n_bins: int = 10) -> float:
    """Compute entropy of trust score distribution."""
    bins = [0] * n_bins
    for s in scores:
        idx = min(int(s * n_bins), n_bins - 1)
        bins[idx] += 1

    total = sum(bins)
    if total == 0:
        return 0.0

    dist = [b / total for b in bins]
    return entropy(dist)


# ─── Rate-Distortion ─────────────────────────────────────────────

def rate_distortion_binary(distortion: float) -> float:
    """
    Rate-distortion function for binary source with Hamming distortion.
    R(D) = 1 - H(D) for D ∈ [0, 0.5].
    Minimum bits needed to represent with at most D distortion.
    """
    if distortion <= 0:
        return 1.0
    if distortion >= 0.5:
        return 0.0

    h = -distortion * math.log2(distortion) - (1 - distortion) * math.log2(1 - distortion)
    return 1.0 - h


def rate_distortion_gaussian(variance: float, distortion: float) -> float:
    """
    Rate-distortion for Gaussian source with MSE distortion.
    R(D) = 0.5 * log2(variance / D) for D ≤ variance.
    """
    if distortion >= variance or distortion <= 0:
        return 0.0
    return 0.5 * math.log2(variance / distortion)


# ─── Quantization ────────────────────────────────────────────────

def uniform_quantize(value: float, levels: int) -> Tuple[int, float]:
    """
    Uniform quantization of trust score [0,1] into discrete levels.
    Returns (quantized_level, reconstruction_value).
    """
    step = 1.0 / levels
    level = min(int(value / step), levels - 1)
    reconstruction = (level + 0.5) * step
    return level, reconstruction


def quantization_error(values: List[float], levels: int) -> float:
    """Mean squared quantization error for given number of levels."""
    total_error = 0.0
    for v in values:
        _, recon = uniform_quantize(v, levels)
        total_error += (v - recon) ** 2
    return total_error / len(values) if values else 0.0


def optimal_levels_for_error(target_error: float,
                              values: List[float]) -> int:
    """Find minimum quantization levels to achieve target MSE."""
    for levels in range(1, 1001):
        if quantization_error(values, levels) <= target_error:
            return levels
    return 1000


def bits_per_score(levels: int) -> float:
    """Bits needed to represent a quantized trust score."""
    if levels <= 1:
        return 0.0
    return math.ceil(math.log2(levels))


# ─── Bloom Filter (Attestation Sets) ─────────────────────────────

@dataclass
class BloomFilter:
    """
    Probabilistic set membership for attestation tracking.
    Space-efficient: fixed size regardless of set cardinality.
    """
    size: int = 1000
    n_hashes: int = 7
    bits: List[bool] = field(default_factory=list)
    count: int = 0

    def __post_init__(self):
        if not self.bits:
            self.bits = [False] * self.size

    def _hashes(self, item: str) -> List[int]:
        positions = []
        for i in range(self.n_hashes):
            h = hashlib.sha256(f"{item}:{i}".encode()).hexdigest()
            positions.append(int(h, 16) % self.size)
        return positions

    def add(self, item: str):
        for pos in self._hashes(item):
            self.bits[pos] = True
        self.count += 1

    def might_contain(self, item: str) -> bool:
        return all(self.bits[pos] for pos in self._hashes(item))

    def false_positive_rate(self) -> float:
        """Theoretical false positive rate."""
        if self.count == 0:
            return 0.0
        return (1 - math.exp(-self.n_hashes * self.count / self.size)) ** self.n_hashes

    def bits_per_element(self) -> float:
        if self.count == 0:
            return float('inf')
        return self.size / self.count


# ─── Count-Min Sketch (Trust Counters) ───────────────────────────

@dataclass
class CountMinSketch:
    """
    Approximate frequency counter for trust events.
    Space: O(w × d), overestimates by at most ε with probability 1-δ.
    """
    width: int = 100
    depth: int = 5
    table: List[List[float]] = field(default_factory=list)

    def __post_init__(self):
        if not self.table:
            self.table = [[0.0] * self.width for _ in range(self.depth)]

    def _hash(self, item: str, row: int) -> int:
        h = hashlib.sha256(f"{item}:{row}".encode()).hexdigest()
        return int(h, 16) % self.width

    def add(self, item: str, count: float = 1.0):
        for row in range(self.depth):
            col = self._hash(item, row)
            self.table[row][col] += count

    def estimate(self, item: str) -> float:
        """Returns minimum across all hash rows (least overestimate)."""
        return min(self.table[row][self._hash(item, row)]
                   for row in range(self.depth))


# ─── Delta Encoding ───────────────────────────────────────────────

def delta_encode(values: List[float], precision: int = 100) -> List[int]:
    """
    Delta encoding for trust score sequences.
    Stores differences instead of absolute values.
    Typically more compressible (smaller deltas).
    """
    if not values:
        return []

    quantized = [round(v * precision) for v in values]
    deltas = [quantized[0]]
    for i in range(1, len(quantized)):
        deltas.append(quantized[i] - quantized[i - 1])

    return deltas


def delta_decode(deltas: List[int], precision: int = 100) -> List[float]:
    """Reconstruct values from delta encoding."""
    if not deltas:
        return []

    values = [deltas[0]]
    for i in range(1, len(deltas)):
        values.append(values[-1] + deltas[i])

    return [v / precision for v in values]


def compression_ratio(original: List[float], encoded: List[int]) -> float:
    """
    Estimate compression ratio.
    Original: 64-bit floats. Encoded: variable-width integers.
    """
    original_bits = len(original) * 64
    # Encoded bits: log2(|max_value|) + 1 sign bit per element
    max_val = max(abs(v) for v in encoded) if encoded else 1
    bits_per_val = math.ceil(math.log2(max(2, max_val + 1))) + 1
    encoded_bits = len(encoded) * bits_per_val

    if encoded_bits == 0:
        return 1.0

    return original_bits / encoded_bits


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
    print("Trust State Compression for Web4")
    print("Session 32, Track 5")
    print("=" * 70)

    random.seed(42)

    # ── §1 Trust Entropy ────────────────────────────────────────
    print("\n§1 Trust Entropy\n")

    # Uniform distribution: maximum entropy
    uniform = [0.1] * 10
    h_uniform = entropy(uniform)
    check("uniform_max_entropy", abs(h_uniform - math.log2(10)) < 0.01,
          f"h={h_uniform:.4f} expected={math.log2(10):.4f}")

    # Concentrated distribution: low entropy
    concentrated = [0.9] + [0.01] * 10
    # Normalize
    total = sum(concentrated)
    concentrated = [c / total for c in concentrated]
    h_concentrated = entropy(concentrated)
    check("concentrated_low_entropy", h_concentrated < h_uniform,
          f"conc={h_concentrated:.4f} uniform={h_uniform:.4f}")

    # Trust score entropy
    diverse_scores = [random.random() for _ in range(1000)]
    uniform_scores = [0.5] * 1000
    h_diverse = trust_entropy(diverse_scores)
    h_uniform_scores = trust_entropy(uniform_scores)
    check("diverse_higher_entropy", h_diverse > h_uniform_scores,
          f"diverse={h_diverse:.4f} uniform={h_uniform_scores:.4f}")

    # ── §2 Rate-Distortion ──────────────────────────────────────
    print("\n§2 Rate-Distortion Theory\n")

    # Zero distortion → maximum rate (1 bit for binary)
    r_zero = rate_distortion_binary(0.0)
    check("rd_zero_distortion", abs(r_zero - 1.0) < 0.01,
          f"R(0)={r_zero:.4f}")

    # Maximum distortion → zero rate
    r_max = rate_distortion_binary(0.5)
    check("rd_max_distortion", abs(r_max) < 0.01,
          f"R(0.5)={r_max:.4f}")

    # Rate decreases with distortion (tradeoff)
    r_low = rate_distortion_binary(0.1)
    r_high = rate_distortion_binary(0.3)
    check("rd_monotone_decreasing", r_low > r_high,
          f"R(0.1)={r_low:.4f} R(0.3)={r_high:.4f}")

    # Gaussian rate-distortion
    rg = rate_distortion_gaussian(1.0, 0.1)
    check("rd_gaussian_positive", rg > 0,
          f"R(0.1)={rg:.4f}")

    # ── §3 Quantization ────────────────────────────────────────
    print("\n§3 Trust Score Quantization\n")

    scores = [random.random() for _ in range(1000)]

    # More levels → less error
    err_10 = quantization_error(scores, 10)
    err_100 = quantization_error(scores, 100)
    check("more_levels_less_error", err_100 < err_10,
          f"err_10={err_10:.6f} err_100={err_100:.6f}")

    # Error bounded by 1/(4*L²) for L levels (uniform on [0,1])
    for levels in [10, 50, 100]:
        err = quantization_error(scores, levels)
        bound = 1.0 / (4 * levels ** 2)
        # Allow 2x slack for finite sample
        check(f"quant_bound_{levels}", err < bound * 2,
              f"err={err:.6f} bound={bound:.6f}")

    # Bits per score
    check("bits_10_levels", bits_per_score(10) == 4)
    check("bits_100_levels", bits_per_score(100) == 7)
    check("bits_256_levels", bits_per_score(256) == 8)

    # ── §4 Bloom Filter ────────────────────────────────────────
    print("\n§4 Bloom Filter Attestation Sets\n")

    bf = BloomFilter(size=1000, n_hashes=7)

    # Add some attestations
    attested = [f"entity_{i}" for i in range(50)]
    for a in attested:
        bf.add(a)

    # All added items should be found
    all_found = all(bf.might_contain(a) for a in attested)
    check("bloom_no_false_negative", all_found)

    # Some not-added items may be found (false positives)
    not_attested = [f"unknown_{i}" for i in range(1000)]
    fp_count = sum(1 for a in not_attested if bf.might_contain(a))
    fp_rate = fp_count / len(not_attested)
    theoretical_fp = bf.false_positive_rate()
    check("bloom_low_fp_rate", fp_rate < 0.1,
          f"fp_rate={fp_rate:.4f} theoretical={theoretical_fp:.4f}")

    # Space efficiency
    bpe = bf.bits_per_element()
    check("bloom_space_efficient", bpe < 30,
          f"bits_per_element={bpe:.1f}")

    # ── §5 Count-Min Sketch ─────────────────────────────────────
    print("\n§5 Count-Min Sketch Trust Counters\n")

    cms = CountMinSketch(width=100, depth=5)

    # Track attestation counts
    true_counts = {"alice": 10, "bob": 5, "carol": 20}
    for entity, count in true_counts.items():
        for _ in range(count):
            cms.add(entity)

    # Estimates should be >= true count (overestimate property)
    for entity, true_count in true_counts.items():
        est = cms.estimate(entity)
        check(f"cms_{entity}_overestimate", est >= true_count,
              f"est={est} true={true_count}")

    # ── §6 Delta Encoding ──────────────────────────────────────
    print("\n§6 Delta Encoding\n")

    # Slowly changing trust scores compress well
    slow_change = [0.5 + 0.001 * i for i in range(100)]
    deltas = delta_encode(slow_change)

    # Deltas should be small (1 per step)
    max_delta = max(abs(d) for d in deltas[1:])
    check("small_deltas", max_delta <= 2,
          f"max_delta={max_delta}")

    # Decode reconstructs original
    decoded = delta_decode(deltas)
    max_err = max(abs(a - b) for a, b in zip(slow_change, decoded))
    check("decode_reconstructs", max_err < 0.02,
          f"max_err={max_err:.4f}")

    # Compression ratio
    ratio = compression_ratio(slow_change, deltas)
    check("good_compression", ratio > 3.0,
          f"ratio={ratio:.1f}×")

    # Random scores compress poorly
    random_scores = [random.random() for _ in range(100)]
    random_deltas = delta_encode(random_scores)
    random_ratio = compression_ratio(random_scores, random_deltas)
    check("random_worse_compression", random_ratio < ratio,
          f"random={random_ratio:.1f}× slow={ratio:.1f}×")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
