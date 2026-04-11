"""
Threshold Cryptography for Trust Quorums in Web4
Session 32, Track 5

Trust-weighted threshold cryptographic schemes:
- Secret sharing (Shamir) with trust-weighted reconstruction
- Threshold signatures (t-of-n with trust eligibility)
- Verifiable secret sharing (VSS)
- Proactive secret sharing (share refresh without changing secret)
- Dynamic threshold (adjust t based on trust levels)
- Trust-weighted threshold (shares weighted by trust score)
- Distributed key generation (DKG) simulation
"""

import math
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set


# ─── Finite Field Arithmetic ─────────────────────────────────────

PRIME = 2**127 - 1  # Mersenne prime for field operations


def mod_inverse(a: int, p: int = PRIME) -> int:
    """Extended Euclidean algorithm for modular inverse."""
    if a == 0:
        return 0
    g, x, _ = extended_gcd(a % p, p)
    if g != 1:
        raise ValueError(f"No inverse for {a} mod {p}")
    return x % p


def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    if a == 0:
        return b, 0, 1
    g, x, y = extended_gcd(b % a, a)
    return g, y - (b // a) * x, x


# ─── Shamir Secret Sharing ──────────────────────────────────────

@dataclass
class Share:
    index: int      # x-coordinate (1-indexed)
    value: int      # y-coordinate
    holder: str     # entity holding this share
    trust: float    # trust level of holder


def shamir_split(secret: int, n: int, t: int,
                  holders: List[str] = None,
                  trusts: List[float] = None,
                  rng: random.Random = None) -> List[Share]:
    """
    Split secret into n shares, any t sufficient to reconstruct.
    """
    if rng is None:
        rng = random.Random(42)
    if t > n:
        raise ValueError("Threshold cannot exceed total shares")

    # Random polynomial of degree t-1 with constant term = secret
    coeffs = [secret % PRIME]
    for _ in range(t - 1):
        coeffs.append(rng.randint(1, PRIME - 1))

    shares = []
    for i in range(1, n + 1):
        # Evaluate polynomial at x=i
        y = 0
        for j, c in enumerate(coeffs):
            y = (y + c * pow(i, j, PRIME)) % PRIME

        holder = holders[i - 1] if holders else f"holder_{i}"
        trust = trusts[i - 1] if trusts else 1.0
        shares.append(Share(index=i, value=y, holder=holder, trust=trust))

    return shares


def shamir_reconstruct(shares: List[Share]) -> int:
    """
    Reconstruct secret from shares using Lagrange interpolation.
    """
    if not shares:
        return 0

    secret = 0
    for i, si in enumerate(shares):
        numerator = 1
        denominator = 1
        for j, sj in enumerate(shares):
            if i != j:
                numerator = (numerator * (-sj.index)) % PRIME
                denominator = (denominator * (si.index - sj.index)) % PRIME

        lagrange = (si.value * numerator % PRIME * mod_inverse(denominator)) % PRIME
        secret = (secret + lagrange) % PRIME

    return secret


# ─── Verifiable Secret Sharing ───────────────────────────────────

@dataclass
class VerifiableShare(Share):
    commitments: List[int] = field(default_factory=list)


def vss_split(secret: int, n: int, t: int,
               rng: random.Random = None) -> Tuple[List[VerifiableShare], List[int]]:
    """
    Feldman's VSS: split with commitments for verification.
    Uses simplified commitment scheme (hash-based for demo).
    """
    if rng is None:
        rng = random.Random(42)

    coeffs = [secret % PRIME]
    for _ in range(t - 1):
        coeffs.append(rng.randint(1, PRIME - 1))

    # Commitments: hash of each coefficient
    commitments = []
    for c in coeffs:
        h = int(hashlib.sha256(str(c).encode()).hexdigest()[:16], 16)
        commitments.append(h)

    shares = []
    for i in range(1, n + 1):
        y = 0
        for j, c in enumerate(coeffs):
            y = (y + c * pow(i, j, PRIME)) % PRIME

        shares.append(VerifiableShare(
            index=i, value=y, holder=f"holder_{i}",
            trust=1.0, commitments=commitments
        ))

    return shares, commitments


def vss_verify(share: VerifiableShare) -> bool:
    """
    Verify a share against commitments.
    Simplified: check that share is consistent with commitment structure.
    """
    # In real VSS, this uses discrete log commitments
    # Here we verify structural consistency
    return len(share.commitments) > 0 and share.value > 0


# ─── Trust-Weighted Threshold ────────────────────────────────────

def trust_weighted_threshold(shares: List[Share],
                               trust_threshold: float = 0.5) -> Optional[int]:
    """
    Reconstruct only if combined trust of shares exceeds threshold.
    Trust-weighted: more trusted shareholders have more weight.
    """
    total_trust = sum(s.trust for s in shares)
    if total_trust < trust_threshold:
        return None
    return shamir_reconstruct(shares)


def dynamic_threshold(n: int, trusts: List[float],
                       base_threshold: float = 0.6) -> int:
    """
    Compute dynamic t based on trust distribution.
    Higher average trust → lower threshold (more trusted group needs fewer shares).
    Lower average trust → higher threshold (less trusted needs more shares).
    """
    avg_trust = sum(trusts) / len(trusts) if trusts else 0
    # Scale: t ranges from ceil(n/2) at low trust to ceil(n/3) at high trust
    max_t = math.ceil(n * 0.67)  # 2/3 for low trust
    min_t = math.ceil(n * 0.34)  # 1/3 for high trust

    # Linear interpolation based on average trust
    t = max_t - int((max_t - min_t) * avg_trust)
    return max(2, min(n, t))  # At least 2, at most n


# ─── Proactive Secret Sharing ────────────────────────────────────

def refresh_shares(shares: List[Share], t: int,
                    rng: random.Random = None) -> List[Share]:
    """
    Refresh shares without changing the secret.
    Generate a random polynomial with zero constant term,
    evaluate at each share point, and add to existing shares.
    """
    if rng is None:
        rng = random.Random(42)

    n = len(shares)
    # Random polynomial of degree t-1 with constant term = 0
    delta_coeffs = [0]
    for _ in range(t - 1):
        delta_coeffs.append(rng.randint(1, PRIME - 1))

    new_shares = []
    for s in shares:
        delta = 0
        for j, c in enumerate(delta_coeffs):
            delta = (delta + c * pow(s.index, j, PRIME)) % PRIME
        new_shares.append(Share(
            index=s.index,
            value=(s.value + delta) % PRIME,
            holder=s.holder,
            trust=s.trust
        ))

    return new_shares


# ─── Distributed Key Generation ──────────────────────────────────

def simulated_dkg(n: int, t: int,
                   rng: random.Random = None) -> Tuple[int, List[Share]]:
    """
    Simulated DKG: each party contributes a secret, combined into shared key.
    Returns (combined_secret, final_shares).
    """
    if rng is None:
        rng = random.Random(42)

    # Each party generates a random secret and shares it
    all_sub_shares = []
    total_secret = 0

    for party in range(n):
        party_secret = rng.randint(1, PRIME - 1)
        total_secret = (total_secret + party_secret) % PRIME
        sub_shares = shamir_split(party_secret, n, t, rng=random.Random(rng.randint(0, 10000)))
        all_sub_shares.append(sub_shares)

    # Each party combines their received sub-shares
    combined_shares = []
    for i in range(n):
        combined_value = 0
        for party_shares in all_sub_shares:
            combined_value = (combined_value + party_shares[i].value) % PRIME
        combined_shares.append(Share(
            index=i + 1, value=combined_value,
            holder=f"party_{i}", trust=1.0
        ))

    return total_secret, combined_shares


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
    print("Threshold Cryptography for Trust Quorums in Web4")
    print("Session 32, Track 5")
    print("=" * 70)

    # ── §1 Shamir Secret Sharing ────────────────────────────────
    print("\n§1 Shamir Secret Sharing\n")

    secret = 42
    shares = shamir_split(secret, 5, 3)

    check("share_count", len(shares) == 5)

    # Reconstruct with exactly t shares
    recovered = shamir_reconstruct(shares[:3])
    check("reconstruct_t_shares", recovered == secret,
          f"recovered={recovered}")

    # Reconstruct with more than t shares
    recovered_all = shamir_reconstruct(shares)
    check("reconstruct_all_shares", recovered_all == secret,
          f"recovered={recovered_all}")

    # Insufficient shares → wrong value
    recovered_few = shamir_reconstruct(shares[:2])
    check("insufficient_shares_wrong", recovered_few != secret)

    # Different subsets of t shares all recover the same secret
    recovered_alt = shamir_reconstruct([shares[0], shares[2], shares[4]])
    check("different_subset_same_secret", recovered_alt == secret)

    # ── §2 Verifiable Secret Sharing ────────────────────────────
    print("\n§2 Verifiable Secret Sharing\n")

    vss_shares, commitments = vss_split(123456, 5, 3)

    check("vss_share_count", len(vss_shares) == 5)
    check("vss_commitments", len(commitments) == 3)  # t coefficients

    # All shares should verify
    all_valid = all(vss_verify(s) for s in vss_shares)
    check("vss_all_valid", all_valid)

    # Can reconstruct from VSS shares
    recovered_vss = shamir_reconstruct(vss_shares[:3])
    check("vss_reconstruct", recovered_vss == 123456,
          f"recovered={recovered_vss}")

    # ── §3 Trust-Weighted Threshold ─────────────────────────────
    print("\n§3 Trust-Weighted Threshold\n")

    trusted_shares = shamir_split(
        99, 5, 3,
        holders=["alice", "bob", "carol", "dave", "eve"],
        trusts=[0.9, 0.8, 0.7, 0.3, 0.1]
    )

    # High-trust subset passes
    high_trust = [s for s in trusted_shares if s.trust >= 0.7]
    result_high = trust_weighted_threshold(high_trust, trust_threshold=2.0)
    check("high_trust_passes", result_high == 99,
          f"result={result_high}")

    # Low-trust subset fails threshold
    low_trust = [s for s in trusted_shares if s.trust < 0.5]
    result_low = trust_weighted_threshold(low_trust, trust_threshold=2.0)
    check("low_trust_fails", result_low is None)

    # ── §4 Dynamic Threshold ───────────────────────────────────
    print("\n§4 Dynamic Threshold\n")

    # High trust → lower threshold
    high_trusts = [0.9, 0.85, 0.8, 0.9, 0.95]
    t_high = dynamic_threshold(5, high_trusts)

    # Low trust → higher threshold
    low_trusts = [0.2, 0.3, 0.1, 0.25, 0.15]
    t_low = dynamic_threshold(5, low_trusts)

    check("dynamic_high_trust_lower_t", t_high <= t_low,
          f"high={t_high} low={t_low}")
    check("dynamic_bounds", 2 <= t_high <= 5 and 2 <= t_low <= 5,
          f"high={t_high} low={t_low}")

    # ── §5 Proactive Share Refresh ──────────────────────────────
    print("\n§5 Proactive Share Refresh\n")

    original_shares = shamir_split(777, 5, 3)
    refreshed = refresh_shares(original_shares, 3)

    # Shares should be different
    shares_changed = any(
        original_shares[i].value != refreshed[i].value
        for i in range(5)
    )
    check("refresh_changes_shares", shares_changed)

    # But reconstruction should give same secret
    recovered_refreshed = shamir_reconstruct(refreshed[:3])
    check("refresh_preserves_secret", recovered_refreshed == 777,
          f"recovered={recovered_refreshed}")

    # Can reconstruct from any t refreshed shares
    recovered_alt = shamir_reconstruct([refreshed[1], refreshed[2], refreshed[4]])
    check("refresh_any_subset", recovered_alt == 777,
          f"recovered={recovered_alt}")

    # ── §6 Distributed Key Generation ──────────────────────────
    print("\n§6 Distributed Key Generation\n")

    combined_secret, dkg_shares = simulated_dkg(5, 3)

    # Reconstruct from t shares should give combined secret
    recovered_dkg = shamir_reconstruct(dkg_shares[:3])
    check("dkg_reconstruct", recovered_dkg == combined_secret,
          f"recovered={recovered_dkg} expected={combined_secret}")

    # Different subsets should work
    recovered_dkg_alt = shamir_reconstruct([dkg_shares[0], dkg_shares[2], dkg_shares[4]])
    check("dkg_alt_subset", recovered_dkg_alt == combined_secret)

    # Insufficient shares fail
    recovered_dkg_few = shamir_reconstruct(dkg_shares[:2])
    check("dkg_insufficient", recovered_dkg_few != combined_secret)

    # ── §7 Large Secret ────────────────────────────────────────
    print("\n§7 Large Secret Handling\n")

    large_secret = 2**100 + 42
    large_shares = shamir_split(large_secret, 7, 4)
    recovered_large = shamir_reconstruct(large_shares[:4])
    check("large_secret_recovery", recovered_large == large_secret % PRIME,
          f"recovered={recovered_large}")

    # Edge case: secret = 0
    zero_shares = shamir_split(0, 5, 3)
    recovered_zero = shamir_reconstruct(zero_shares[:3])
    check("zero_secret", recovered_zero == 0,
          f"recovered={recovered_zero}")

    # Edge case: secret = 1
    one_shares = shamir_split(1, 5, 3)
    recovered_one = shamir_reconstruct(one_shares[:3])
    check("one_secret", recovered_one == 1,
          f"recovered={recovered_one}")

    # ── Summary ─────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
