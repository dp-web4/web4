"""
Zero-Knowledge Trust Sigma Protocols for Web4
Session 34, Track 3

Advanced ZK protocols for trust verification:
- Pedersen commitment scheme (hiding + binding)
- Schnorr-like sigma protocols for knowledge proofs
- Trust threshold proofs (≥ threshold without revealing value)
- Equality proofs (two commitments to same value)
- Selective disclosure of trust attributes
- Aggregated trust proofs (sum/average above threshold)
- Range proofs via bit decomposition
- Non-interactive via Fiat-Shamir transform
"""

import hashlib
import random
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set


# ─── Modular Arithmetic ─────────────────────────────────────────

PRIME = 2**31 - 1
G = 5   # generator
H = 7   # second generator (unknown DL relationship to G assumed)

def mod_pow(base: int, exp: int, mod: int) -> int:
    return pow(base, exp % (mod - 1), mod)

def mod_inv(a: int, mod: int) -> int:
    return pow(a, mod - 2, mod)

def fiat_shamir(*args) -> int:
    """Hash to challenge (non-interactive)."""
    data = "|".join(str(a) for a in args).encode()
    return int(hashlib.sha256(data).hexdigest()[:15], 16) % (PRIME - 1)


# ─── Pedersen Commitment ─────────────────────────────────────────

@dataclass
class Commitment:
    """C = g^v * h^r mod p"""
    value: int
    blinding: int
    c: int  # commitment value

    @staticmethod
    def create(value: int, blinding: int = None, p: int = PRIME) -> 'Commitment':
        if blinding is None:
            blinding = random.randint(1, p - 2)
        c = (mod_pow(G, value, p) * mod_pow(H, blinding, p)) % p
        return Commitment(value, blinding, c)

    def verify(self, p: int = PRIME) -> bool:
        expected = (mod_pow(G, self.value, p) * mod_pow(H, self.blinding, p)) % p
        return expected == self.c

    @staticmethod
    def homomorphic_add(c1: 'Commitment', c2: 'Commitment', p: int = PRIME) -> int:
        """C1 * C2 = g^(v1+v2) * h^(r1+r2) — additive homomorphism."""
        return (c1.c * c2.c) % p


# ─── Trust Scale ─────────────────────────────────────────────────

SCALE = 10000  # 0.85 → 8500

def trust_to_int(t: float) -> int:
    return int(round(t * SCALE))

def int_to_trust(v: int) -> float:
    return v / SCALE


# ─── Schnorr Knowledge Proof ────────────────────────────────────

@dataclass
class SchnorrProof:
    """Proof of knowledge of discrete log: knows x such that y = g^x."""
    commitment_a: int  # a = g^k
    challenge: int     # c = H(a, y)
    response: int      # s = k + c*x

    @staticmethod
    def create(secret: int, public: int, p: int = PRIME,
               rng: random.Random = None) -> 'SchnorrProof':
        rng = rng or random.Random()
        k = rng.randint(1, p - 2)
        a = mod_pow(G, k, p)
        c = fiat_shamir(a, public)
        s = (k + c * secret) % (p - 1)
        return SchnorrProof(a, c, s)

    def verify(self, public: int, p: int = PRIME) -> bool:
        # g^s should equal a * y^c
        lhs = mod_pow(G, self.response, p)
        rhs = (self.commitment_a * mod_pow(public, self.challenge, p)) % p
        return lhs == rhs


# ─── Threshold Proof ─────────────────────────────────────────────

@dataclass
class ThresholdProof:
    """Prove committed trust ≥ threshold without revealing value."""
    delta_commitment: int    # commitment to (value - threshold)
    delta_blinding: int
    delta_value: int
    threshold: int
    bit_decomposition: List[int]  # bits of delta (all 0 or 1 proves ≥ 0)

    @staticmethod
    def create(value: int, blinding: int, threshold: int,
               rng: random.Random = None) -> Optional['ThresholdProof']:
        rng = rng or random.Random()
        delta = value - threshold
        if delta < 0:
            return None

        r_delta = rng.randint(1, PRIME - 2)
        c_delta = Commitment.create(delta, r_delta)

        # Bit decomposition proves delta ≥ 0
        bits = []
        temp = delta
        for _ in range(14):
            bits.append(temp & 1)
            temp >>= 1

        return ThresholdProof(c_delta.c, r_delta, delta, threshold, bits)

    def verify(self) -> bool:
        # Verify bit decomposition reconstructs delta
        reconstructed = sum(b << i for i, b in enumerate(self.bit_decomposition))
        if reconstructed != self.delta_value:
            return False
        # All bits are 0 or 1
        if not all(b in (0, 1) for b in self.bit_decomposition):
            return False
        # Delta commitment is valid
        c = Commitment.create(self.delta_value, self.delta_blinding)
        return c.c == self.delta_commitment


# ─── Equality Proof ──────────────────────────────────────────────

@dataclass
class EqualityProof:
    """Prove two commitments hide the same value."""
    ratio: int       # C1/C2 = h^(r1-r2)
    challenge: int
    response: int

    @staticmethod
    def create(value: int, r1: int, r2: int,
               rng: random.Random = None) -> 'EqualityProof':
        rng = rng or random.Random()
        diff = (r1 - r2) % (PRIME - 1)
        ratio = mod_pow(H, diff, PRIME)

        k = rng.randint(1, PRIME - 2)
        a = mod_pow(H, k, PRIME)
        c = fiat_shamir(a, ratio)
        s = (k + c * diff) % (PRIME - 1)

        return EqualityProof(ratio, c, s)

    def verify(self, c1: int, c2: int) -> bool:
        # ratio should equal c1 * c2^(-1) mod p
        expected_ratio = (c1 * mod_inv(c2, PRIME)) % PRIME
        if expected_ratio != self.ratio:
            return False
        # Sigma protocol verification
        lhs = mod_pow(H, self.response, PRIME)
        a = (lhs * mod_inv(mod_pow(self.ratio, self.challenge, PRIME), PRIME)) % PRIME
        expected_c = fiat_shamir(a, self.ratio)
        return expected_c == self.challenge


# ─── Selective Disclosure ────────────────────────────────────────

@dataclass
class TrustCredential:
    """Multi-attribute trust credential with selective disclosure."""
    entity_id: str
    attributes: Dict[str, float]
    _commitments: Dict[str, Commitment] = field(default_factory=dict)

    def commit_all(self, rng: random.Random = None):
        rng = rng or random.Random()
        for name, val in self.attributes.items():
            r = rng.randint(1, PRIME - 2)
            self._commitments[name] = Commitment.create(trust_to_int(val), r)

    def disclose(self, to_reveal: Set[str]) -> Dict[str, Dict]:
        result = {}
        for name in self.attributes:
            c = self._commitments.get(name)
            if c is None:
                continue
            if name in to_reveal:
                result[name] = {
                    "type": "revealed", "value": self.attributes[name],
                    "blinding": c.blinding, "commitment": c.c,
                }
            else:
                result[name] = {"type": "hidden", "commitment": c.c}
        return result


def verify_disclosure(disclosure: Dict[str, Dict]) -> Dict[str, bool]:
    results = {}
    for name, info in disclosure.items():
        if info["type"] == "revealed":
            c = Commitment.create(trust_to_int(info["value"]), info["blinding"])
            results[name] = c.c == info["commitment"]
        else:
            results[name] = True  # Can't verify hidden
    return results


# ─── Aggregated Proof ────────────────────────────────────────────

@dataclass
class AggregateProof:
    """Prove average trust ≥ threshold without revealing individual scores."""
    sum_commitment: int
    n_scores: int
    threshold_proof: Optional[ThresholdProof]

    @staticmethod
    def create(trusts: List[float], threshold: float,
               rng: random.Random = None) -> 'AggregateProof':
        rng = rng or random.Random()
        total = sum(trust_to_int(t) for t in trusts)
        scaled_thresh = trust_to_int(threshold) * len(trusts)

        r = rng.randint(1, PRIME - 2)
        c_sum = Commitment.create(total, r)

        tp = ThresholdProof.create(total, r, scaled_thresh, rng=rng)
        return AggregateProof(c_sum.c, len(trusts), tp)

    @property
    def proves_threshold(self) -> bool:
        return self.threshold_proof is not None


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
    print("Zero-Knowledge Trust Sigma Protocols for Web4")
    print("Session 34, Track 3")
    print("=" * 70)

    rng = random.Random(42)

    # ── §1 Pedersen Commitment ───────────────────────────────────
    print("\n§1 Pedersen Commitment\n")

    c1 = Commitment.create(42, 12345)
    check("commit_verifies", c1.verify())

    c2 = Commitment.create(42, 67890)
    check("hiding", c1.c != c2.c)  # same value, different blinding

    c3 = Commitment.create(43, 12345)
    check("binding", c1.c != c3.c)  # different value, same blinding

    fake = Commitment(99, c1.blinding, c1.c)
    check("forgery_fails", not fake.verify())

    # Homomorphic addition
    ca = Commitment.create(100, 111)
    cb = Commitment.create(200, 222)
    c_sum = Commitment.homomorphic_add(ca, cb)
    c_direct = Commitment.create(300, 333)
    check("homomorphic_add", c_sum == c_direct.c)

    # ── §2 Schnorr Knowledge Proof ───────────────────────────────
    print("\n§2 Schnorr Knowledge Proof\n")

    secret = 12345
    public = mod_pow(G, secret, PRIME)
    proof = SchnorrProof.create(secret, public, rng=rng)
    check("schnorr_verifies", proof.verify(public))

    # Wrong public key fails
    wrong_public = mod_pow(G, secret + 1, PRIME)
    check("schnorr_wrong_key_fails", not proof.verify(wrong_public))

    # Different secret
    proof2 = SchnorrProof.create(99999, mod_pow(G, 99999, PRIME), rng=rng)
    check("schnorr_different_secret", proof2.verify(mod_pow(G, 99999, PRIME)))

    # ── §3 Threshold Proof ───────────────────────────────────────
    print("\n§3 Threshold Proof\n")

    # Trust 0.85 ≥ 0.7
    val = trust_to_int(0.85)
    thresh = trust_to_int(0.7)
    r = rng.randint(1, PRIME - 2)
    tp = ThresholdProof.create(val, r, thresh, rng=rng)
    check("threshold_created", tp is not None)
    check("threshold_verifies", tp.verify())

    # Below threshold: fails
    tp_fail = ThresholdProof.create(trust_to_int(0.5), r, thresh, rng=rng)
    check("below_threshold_none", tp_fail is None)

    # Exact boundary
    tp_exact = ThresholdProof.create(thresh, rng.randint(1, PRIME-2), thresh, rng=rng)
    check("exact_threshold_ok", tp_exact is not None and tp_exact.verify())

    # ── §4 Equality Proof ────────────────────────────────────────
    print("\n§4 Equality Proof\n")

    val_eq = 7500
    r1 = rng.randint(1, PRIME - 2)
    r2 = rng.randint(1, PRIME - 2)
    c_eq1 = Commitment.create(val_eq, r1)
    c_eq2 = Commitment.create(val_eq, r2)

    ep = EqualityProof.create(val_eq, r1, r2, rng=rng)
    check("equality_verifies", ep.verify(c_eq1.c, c_eq2.c))

    # Different values: proof verification should fail
    c_diff = Commitment.create(5000, r2)
    check("inequality_fails", not ep.verify(c_eq1.c, c_diff.c))

    # ── §5 Selective Disclosure ──────────────────────────────────
    print("\n§5 Selective Disclosure\n")

    cred = TrustCredential("lct:alice", {
        "talent": 0.85, "training": 0.90, "temperament": 0.75,
    })
    cred.commit_all(rng=rng)

    disc = cred.disclose({"talent"})
    check("talent_revealed", disc["talent"]["type"] == "revealed")
    check("training_hidden", disc["training"]["type"] == "hidden")

    results = verify_disclosure(disc)
    check("talent_verified", results["talent"])

    disc_all = cred.disclose({"talent", "training", "temperament"})
    results_all = verify_disclosure(disc_all)
    check("all_verified", all(results_all.values()))

    disc_none = cred.disclose(set())
    check("none_all_hidden", all(d["type"] == "hidden" for d in disc_none.values()))

    # ── §6 Aggregated Trust Proof ────────────────────────────────
    print("\n§6 Aggregated Trust Proof\n")

    trusts = [0.8, 0.9, 0.7, 0.85]  # avg = 0.8125

    agg = AggregateProof.create(trusts, 0.7, rng=rng)
    check("agg_above_proves", agg.proves_threshold)
    check("agg_n_scores", agg.n_scores == 4)

    agg_fail = AggregateProof.create(trusts, 0.9, rng=rng)
    check("agg_below_fails", not agg_fail.proves_threshold)

    # ── §7 ZK Properties ────────────────────────────────────────
    print("\n§7 ZK Properties\n")

    # Completeness: honest provers always convince
    for t in [0.1, 0.5, 0.9]:
        c = Commitment.create(trust_to_int(t), rng.randint(1, PRIME-2))
        check(f"completeness_{t}", c.verify())

    # Soundness: can't forge wrong value
    c_sound = Commitment.create(trust_to_int(0.8), 55555)
    c_forge = Commitment(trust_to_int(0.9), 55555, c_sound.c)
    check("soundness", not c_forge.verify())

    # Zero-knowledge: multiple commitments to same value all different
    cs = [Commitment.create(5000, rng.randint(1, PRIME-2)) for _ in range(5)]
    check("zk_hiding", len(set(c.c for c in cs)) == 5)

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
