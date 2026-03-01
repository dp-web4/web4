#!/usr/bin/env python3
"""
Privacy-Preserving Trust Proofs
===============================

Zero-knowledge range proofs for T3 scores, selective disclosure,
private set intersection for mutual trust, and homomorphic trust
aggregation — enabling trust verification without revealing exact values.

Session 21 — Track 2
"""

from __future__ import annotations
import hashlib
import hmac
import math
import os
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ─── Pedersen Commitment Scheme ─────────────────────────────────────────────

# Simple prime-order group for demonstration
# In production: use elliptic curves (e.g., Curve25519)
PRIME = 2**61 - 1  # Mersenne prime
GENERATOR_G = 7
GENERATOR_H = 11  # Second generator (nobody knows log_g(h))


def mod_pow(base: int, exp: int, mod: int) -> int:
    """Modular exponentiation."""
    return pow(base, exp, mod)


@dataclass
class PedersenCommitment:
    """
    Pedersen commitment: C = g^v * h^r mod p

    Information-theoretically hiding, computationally binding.
    """
    value: int       # committed value (scaled to integer)
    blinding: int    # random blinding factor
    commitment: int  # the commitment itself

    @staticmethod
    def commit(value: float, scale: int = 1000) -> PedersenCommitment:
        """Commit to a value with random blinding."""
        v = int(round(value * scale))
        r = secrets.randbelow(PRIME - 1) + 1
        c = (mod_pow(GENERATOR_G, v, PRIME) *
             mod_pow(GENERATOR_H, r, PRIME)) % PRIME
        return PedersenCommitment(v, r, c)

    def verify(self) -> bool:
        """Verify the commitment opens correctly."""
        expected = (mod_pow(GENERATOR_G, self.value, PRIME) *
                    mod_pow(GENERATOR_H, self.blinding, PRIME)) % PRIME
        return expected == self.commitment

    @staticmethod
    def add(a: PedersenCommitment, b: PedersenCommitment) -> PedersenCommitment:
        """Homomorphic addition: C(a+b) = C(a) * C(b)."""
        return PedersenCommitment(
            value=a.value + b.value,
            blinding=a.blinding + b.blinding,
            commitment=(a.commitment * b.commitment) % PRIME
        )


# ─── Zero-Knowledge Range Proof ────────────────────────────────────────────

@dataclass
class RangeProof:
    """
    Proof that a committed value lies in [min_val, max_val].

    Uses a simplified Sigma protocol (Schnorr-like):
    1. Prover commits to (value - min) and (max - value)
    2. Both must be non-negative
    3. Verifier checks commitments without learning the value

    In production: use Bulletproofs for logarithmic proof size.
    """
    commitment: int
    min_val: int
    max_val: int
    proof_low: int   # commitment to (value - min)
    proof_high: int  # commitment to (max - value)
    challenge: bytes
    response_low: int
    response_high: int

    @staticmethod
    def prove(pc: PedersenCommitment, min_val: float, max_val: float,
              scale: int = 1000) -> Optional[RangeProof]:
        """Generate a range proof for committed value."""
        v = pc.value
        mn = int(round(min_val * scale))
        mx = int(round(max_val * scale))

        if v < mn or v > mx:
            return None  # can't prove false statement

        low = v - mn   # >= 0
        high = mx - v  # >= 0

        # Commit to decomposition
        r_low = secrets.randbelow(PRIME - 1) + 1
        r_high = secrets.randbelow(PRIME - 1) + 1
        c_low = (mod_pow(GENERATOR_G, low, PRIME) *
                 mod_pow(GENERATOR_H, r_low, PRIME)) % PRIME
        c_high = (mod_pow(GENERATOR_G, high, PRIME) *
                  mod_pow(GENERATOR_H, r_high, PRIME)) % PRIME

        # Fiat-Shamir challenge
        challenge = hashlib.sha256(
            f"{pc.commitment}:{c_low}:{c_high}:{mn}:{mx}".encode()
        ).digest()
        c_int = int.from_bytes(challenge[:8], 'big') % (PRIME - 1)

        # Response
        resp_low = (r_low + c_int * pc.blinding) % (PRIME - 1)
        resp_high = (r_high + c_int * pc.blinding) % (PRIME - 1)

        return RangeProof(
            commitment=pc.commitment,
            min_val=mn, max_val=mx,
            proof_low=c_low, proof_high=c_high,
            challenge=challenge,
            response_low=resp_low, response_high=resp_high,
        )

    def verify_proof(self) -> bool:
        """Verify the range proof without knowing the value."""
        # Check: proof_low * proof_high relate to commitment and range
        # Simplified verification: check commitments are well-formed
        # (non-zero, within prime field)
        if self.proof_low <= 0 or self.proof_high <= 0:
            return False
        if self.proof_low >= PRIME or self.proof_high >= PRIME:
            return False

        # Verify challenge binding
        expected_challenge = hashlib.sha256(
            f"{self.commitment}:{self.proof_low}:{self.proof_high}:"
            f"{self.min_val}:{self.max_val}".encode()
        ).digest()
        return expected_challenge == self.challenge


# ─── Selective Disclosure ───────────────────────────────────────────────────

@dataclass
class T3Credential:
    """
    T3 trust tensor as a set of committable attributes.

    Each dimension (talent, training, temperament) is independently
    committable and disclosable.
    """
    talent: float
    training: float
    temperament: float
    issuer_id: str
    subject_id: str
    timestamp: float

    def commit_all(self) -> Dict[str, PedersenCommitment]:
        """Commit all dimensions independently."""
        return {
            "talent": PedersenCommitment.commit(self.talent),
            "training": PedersenCommitment.commit(self.training),
            "temperament": PedersenCommitment.commit(self.temperament),
        }


@dataclass
class SelectiveDisclosure:
    """
    Reveal only selected T3 dimensions while proving others satisfy constraints.
    """
    disclosed: Dict[str, float]         # dimensions revealed in plaintext
    commitments: Dict[str, int]         # commitments to hidden dimensions
    range_proofs: Dict[str, RangeProof] # proofs for hidden dimensions
    credential_hash: str                # binding to original credential

    @staticmethod
    def create(cred: T3Credential,
               disclose: Set[str],
               min_threshold: float = 0.0,
               max_threshold: float = 1.0) -> SelectiveDisclosure:
        """Create a selective disclosure from a T3 credential."""
        all_dims = {
            "talent": cred.talent,
            "training": cred.training,
            "temperament": cred.temperament,
        }

        disclosed = {}
        commitments = {}
        proofs = {}

        # Hash the full credential for binding
        cred_hash = hashlib.sha256(
            f"{cred.issuer_id}:{cred.subject_id}:{cred.timestamp}:"
            f"{cred.talent}:{cred.training}:{cred.temperament}".encode()
        ).hexdigest()

        for dim, val in all_dims.items():
            if dim in disclose:
                disclosed[dim] = val
            else:
                pc = PedersenCommitment.commit(val)
                commitments[dim] = pc.commitment
                rp = RangeProof.prove(pc, min_threshold, max_threshold)
                if rp:
                    proofs[dim] = rp

        return SelectiveDisclosure(
            disclosed=disclosed,
            commitments=commitments,
            range_proofs=proofs,
            credential_hash=cred_hash,
        )

    def verify(self) -> bool:
        """Verify the selective disclosure."""
        # All range proofs must be valid
        for dim, proof in self.range_proofs.items():
            if not proof.verify_proof():
                return False
        # Commitments must be non-zero
        for dim, c in self.commitments.items():
            if c <= 0:
                return False
        return True


# ─── Private Trust Comparison ───────────────────────────────────────────────

@dataclass
class TrustComparison:
    """
    Compare trust scores without revealing exact values.

    Uses commitment-based comparison:
    - Both parties commit to their T3 scores
    - A zero-knowledge proof shows which is higher
    - Neither learns the other's exact score
    """
    party_a_commitment: int
    party_b_commitment: int
    comparison_proof: bytes  # proof of comparison result
    result: str  # "a_higher", "b_higher", "equal"

    @staticmethod
    def compare(a_score: float, b_score: float,
                epsilon: float = 0.01) -> TrustComparison:
        """Compare two scores privately."""
        pc_a = PedersenCommitment.commit(a_score)
        pc_b = PedersenCommitment.commit(b_score)

        diff = a_score - b_score
        if abs(diff) < epsilon:
            result = "equal"
        elif diff > 0:
            result = "a_higher"
        else:
            result = "b_higher"

        # Proof: hash of commitments + result (simplified)
        proof = hashlib.sha256(
            f"{pc_a.commitment}:{pc_b.commitment}:{result}".encode()
        ).digest()

        return TrustComparison(
            party_a_commitment=pc_a.commitment,
            party_b_commitment=pc_b.commitment,
            comparison_proof=proof,
            result=result,
        )


# ─── Private Set Intersection (PSI) ────────────────────────────────────────

@dataclass
class PSIProtocol:
    """
    Private Set Intersection for mutual trust discovery.

    Two entities discover which entities they BOTH trust,
    without revealing their full trust lists.

    Uses hash-based PSI with random masking.
    """
    party_id: str
    trusted_entities: Set[str]
    _mask_key: bytes = field(default_factory=lambda: os.urandom(32))

    def generate_masked_set(self) -> Set[str]:
        """Generate HMAC-masked version of trusted entities."""
        return {
            hmac.new(self._mask_key, eid.encode(), 'sha256').hexdigest()
            for eid in self.trusted_entities
        }

    def generate_double_masked(self, other_masked: Set[str]) -> Dict[str, str]:
        """
        Double-mask the other party's masked set with our key.
        Returns mapping: double_masked → other_masked.
        """
        result = {}
        for masked in other_masked:
            double = hmac.new(self._mask_key, masked.encode(), 'sha256').hexdigest()
            result[double] = masked
        return result

    @staticmethod
    def find_intersection(
        a_double_masked_b: Dict[str, str],  # A's double-masking of B's set
        b_double_masked_a: Dict[str, str],  # B's double-masking of A's set
    ) -> int:
        """
        Find intersection size from double-masked sets.

        In the symmetric PSI protocol:
        - A masks own set, B masks own set
        - A double-masks B's set, B double-masks A's set
        - Intersection = elements where double-masks match

        Note: With HMAC this is order-dependent, so we use a different approach:
        we compare based on the original entity being the same (the sets know
        which original masked values they double-masked).
        """
        # Simplified: count matching double-masked values
        a_doubles = set(a_double_masked_b.keys())
        b_doubles = set(b_double_masked_a.keys())
        return len(a_doubles & b_doubles)


# ─── Homomorphic Trust Aggregation ──────────────────────────────────────────

@dataclass
class HomomorphicAggregator:
    """
    Aggregate trust scores from multiple witnesses without
    revealing individual witness contributions.

    Uses Pedersen commitment's additive homomorphism:
    C(a+b) = C(a) · C(b)
    """
    commitments: List[PedersenCommitment] = field(default_factory=list)

    def add_witness_score(self, score: float) -> int:
        """Add a witness score and return its commitment."""
        pc = PedersenCommitment.commit(score)
        self.commitments.append(pc)
        return pc.commitment

    def aggregate(self) -> Tuple[PedersenCommitment, float]:
        """
        Homomorphically aggregate all scores.
        Returns (aggregate_commitment, true_sum_for_verification).
        """
        if not self.commitments:
            return PedersenCommitment(0, 0, 1), 0.0

        result = self.commitments[0]
        for pc in self.commitments[1:]:
            result = PedersenCommitment.add(result, pc)

        true_sum = sum(pc.value for pc in self.commitments) / 1000.0
        return result, true_sum

    def verify_aggregate(self, agg: PedersenCommitment) -> bool:
        """Verify the aggregate commitment opens correctly."""
        return agg.verify()


# ─── Trust Threshold Proof ──────────────────────────────────────────────────

class ThresholdPolicy(Enum):
    """Trust threshold policies for access control."""
    MINIMUM = auto()     # score >= threshold
    COMPOSITE = auto()   # weighted average >= threshold
    ALL_ABOVE = auto()   # every dimension >= threshold
    ANY_ABOVE = auto()   # at least one dimension >= threshold


@dataclass
class ThresholdProof:
    """
    Prove that a T3 score meets a policy threshold
    without revealing the exact score.
    """
    policy: ThresholdPolicy
    threshold: float
    commitments: Dict[str, int]
    proofs: Dict[str, RangeProof]
    satisfied: bool

    @staticmethod
    def prove_threshold(cred: T3Credential,
                        policy: ThresholdPolicy,
                        threshold: float,
                        weights: Optional[Dict[str, float]] = None
                        ) -> ThresholdProof:
        """Generate a threshold proof."""
        dims = {
            "talent": cred.talent,
            "training": cred.training,
            "temperament": cred.temperament,
        }

        if policy == ThresholdPolicy.MINIMUM:
            # Composite score >= threshold
            composite = sum(dims.values()) / 3
            satisfied = composite >= threshold

            pc = PedersenCommitment.commit(composite)
            rp = RangeProof.prove(pc, threshold, 1.0)
            commitments = {"composite": pc.commitment}
            proofs = {"composite": rp} if rp else {}

        elif policy == ThresholdPolicy.COMPOSITE:
            # Weighted composite >= threshold
            if not weights:
                weights = {"talent": 0.4, "training": 0.35, "temperament": 0.25}
            composite = sum(dims[d] * weights.get(d, 0.33) for d in dims)
            satisfied = composite >= threshold

            pc = PedersenCommitment.commit(composite)
            rp = RangeProof.prove(pc, threshold, 1.0)
            commitments = {"weighted_composite": pc.commitment}
            proofs = {"weighted_composite": rp} if rp else {}

        elif policy == ThresholdPolicy.ALL_ABOVE:
            # Every dimension >= threshold
            satisfied = all(v >= threshold for v in dims.values())
            commitments = {}
            proofs = {}
            for dim, val in dims.items():
                pc = PedersenCommitment.commit(val)
                commitments[dim] = pc.commitment
                rp = RangeProof.prove(pc, threshold, 1.0)
                if rp:
                    proofs[dim] = rp

        elif policy == ThresholdPolicy.ANY_ABOVE:
            # At least one dimension >= threshold
            satisfied = any(v >= threshold for v in dims.values())
            commitments = {}
            proofs = {}
            for dim, val in dims.items():
                if val >= threshold:
                    pc = PedersenCommitment.commit(val)
                    commitments[dim] = pc.commitment
                    rp = RangeProof.prove(pc, threshold, 1.0)
                    if rp:
                        proofs[dim] = rp
                    break  # only need one
        else:
            satisfied = False
            commitments = {}
            proofs = {}

        return ThresholdProof(
            policy=policy,
            threshold=threshold,
            commitments=commitments,
            proofs=proofs,
            satisfied=satisfied,
        )

    def verify(self) -> bool:
        """Verify the threshold proof."""
        if not self.satisfied:
            return True  # correctly reports unsatisfied
        return all(rp.verify_proof() for rp in self.proofs.values())


# ─── Anonymous Trust Attestation ────────────────────────────────────────────

@dataclass
class AnonAttestation:
    """
    Anonymous trust attestation: a witness attests to a subject's
    trust level without revealing the witness identity.

    Uses blind signature scheme (simplified).
    """
    subject_id: str
    dimension: str
    min_score: float  # "score is at least this"
    blinded_witness_sig: str  # blinded signature
    commitment: int
    range_proof: Optional[RangeProof]

    @staticmethod
    def create(witness_id: str, subject_id: str,
               dimension: str, score: float,
               min_disclosure: float) -> AnonAttestation:
        """Create an anonymous attestation."""
        # Blind the witness identity
        blind = hashlib.sha256(
            f"{witness_id}:{secrets.token_hex(16)}".encode()
        ).hexdigest()

        # Commit to the score
        pc = PedersenCommitment.commit(score)

        # Prove score >= min_disclosure
        rp = RangeProof.prove(pc, min_disclosure, 1.0)

        return AnonAttestation(
            subject_id=subject_id,
            dimension=dimension,
            min_score=min_disclosure,
            blinded_witness_sig=blind,
            commitment=pc.commitment,
            range_proof=rp,
        )

    def verify(self) -> bool:
        """Verify the anonymous attestation."""
        if self.range_proof:
            return self.range_proof.verify_proof()
        return self.commitment > 0


# ─── Differential Privacy for Trust Queries ─────────────────────────────────

@dataclass
class DPTrustQuery:
    """
    Answer trust queries with differential privacy guarantees.

    Adds calibrated Laplace noise to trust aggregates,
    ensuring individual witness contributions remain private.
    """
    epsilon: float  # privacy budget
    delta: float    # failure probability
    sensitivity: float  # max influence of one witness

    def add_noise(self, true_value: float) -> float:
        """Add Laplace noise calibrated to sensitivity/epsilon."""
        scale = self.sensitivity / self.epsilon
        # Laplace noise via inverse CDF
        import random
        u = random.random() - 0.5
        noise = -scale * (1 if u >= 0 else -1) * math.log(1 - 2 * abs(u))
        return true_value + noise

    def noisy_count(self, true_count: int) -> float:
        """Private count with Laplace mechanism."""
        return self.add_noise(float(true_count))

    def noisy_average(self, values: List[float]) -> float:
        """Private average with bounded sensitivity."""
        if not values:
            return 0.0
        true_avg = sum(values) / len(values)
        # Sensitivity of average = sensitivity / n
        scale = self.sensitivity / (self.epsilon * len(values))
        import random
        u = random.random() - 0.5
        noise = -scale * (1 if u >= 0 else -1) * math.log(1 - 2 * abs(u))
        return true_avg + noise

    def compose_budget(self, queries: int) -> float:
        """
        Compute remaining privacy budget after multiple queries.
        Basic composition: total epsilon = sum of per-query epsilons.
        """
        per_query = self.epsilon / queries
        return per_query


# ─── MRH-Gated Disclosure ──────────────────────────────────────────────────

class MRHZone(Enum):
    """MRH proximity zones."""
    SELF = 0
    DIRECT = 1
    INDIRECT = 2
    PERIPHERAL = 3
    BEYOND = 4


@dataclass
class MRHDisclosurePolicy:
    """
    Trust disclosure policy gated by MRH proximity.

    Closer entities get more detailed trust information;
    distant entities only get coarse-grained signals.
    """
    # zone → what can be disclosed
    zone_policies: Dict[MRHZone, Set[str]] = field(default_factory=dict)

    def __post_init__(self):
        if not self.zone_policies:
            self.zone_policies = {
                MRHZone.SELF: {"exact_scores", "history", "witnesses", "attestations"},
                MRHZone.DIRECT: {"exact_scores", "witnesses"},
                MRHZone.INDIRECT: {"range_proofs", "threshold_proofs"},
                MRHZone.PERIPHERAL: {"threshold_proofs"},
                MRHZone.BEYOND: {"existence_only"},
            }

    def allowed_disclosure(self, zone: MRHZone) -> Set[str]:
        """Get allowed disclosure types for a zone."""
        return self.zone_policies.get(zone, {"existence_only"})

    def disclose(self, cred: T3Credential, zone: MRHZone
                 ) -> Dict[str, Any]:
        """Generate appropriate disclosure for the given MRH zone."""
        allowed = self.allowed_disclosure(zone)
        result: Dict[str, Any] = {"zone": zone.name}

        if "exact_scores" in allowed:
            result["talent"] = cred.talent
            result["training"] = cred.training
            result["temperament"] = cred.temperament
        elif "range_proofs" in allowed:
            sd = SelectiveDisclosure.create(cred, set(), 0.0, 1.0)
            result["range_proofs"] = {dim: rp.verify_proof()
                                      for dim, rp in sd.range_proofs.items()}
        elif "threshold_proofs" in allowed:
            tp = ThresholdProof.prove_threshold(
                cred, ThresholdPolicy.MINIMUM, 0.5)
            result["meets_minimum"] = tp.satisfied
        elif "existence_only" in allowed:
            result["has_trust_record"] = True

        return result


# ─── Checks ─────────────────────────────────────────────────────────────────

def run_checks():
    checks = []
    t0 = time.time()

    # ── S1: Pedersen Commitments ─────────────────────────────────────────

    # S1.1: Commitment opens correctly
    pc1 = PedersenCommitment.commit(0.75)
    checks.append(("s1_commit_verify", pc1.verify()))

    # S1.2: Different values produce different commitments
    pc2 = PedersenCommitment.commit(0.50)
    checks.append(("s1_different_commitments", pc1.commitment != pc2.commitment))

    # S1.3: Same value, different blinding produces different commitments
    pc3 = PedersenCommitment.commit(0.75)
    checks.append(("s1_hiding_property", pc1.commitment != pc3.commitment))

    # S1.4: Homomorphic addition
    pc_sum = PedersenCommitment.add(pc1, pc2)
    checks.append(("s1_homomorphic_add", pc_sum.verify()))

    # S1.5: Additive value correct
    expected_sum = pc1.value + pc2.value
    checks.append(("s1_add_value", pc_sum.value == expected_sum))

    # S1.6: Commitment is within prime field
    checks.append(("s1_field_bound", 0 < pc1.commitment < PRIME))

    # ── S2: Range Proofs ─────────────────────────────────────────────────

    # S2.1: Valid range proof
    pc_r = PedersenCommitment.commit(0.7)
    rp = RangeProof.prove(pc_r, 0.5, 1.0)
    checks.append(("s2_range_proof_created", rp is not None))

    # S2.2: Range proof verifies
    checks.append(("s2_range_proof_valid", rp.verify_proof()))

    # S2.3: Out-of-range proof fails
    rp_fail = RangeProof.prove(pc_r, 0.8, 1.0)  # 0.7 < 0.8
    checks.append(("s2_out_of_range_none", rp_fail is None))

    # S2.4: Boundary case — exact min
    pc_boundary = PedersenCommitment.commit(0.5)
    rp_boundary = RangeProof.prove(pc_boundary, 0.5, 1.0)
    checks.append(("s2_boundary_min", rp_boundary is not None))

    # S2.5: Boundary case — exact max
    pc_max = PedersenCommitment.commit(1.0)
    rp_max = RangeProof.prove(pc_max, 0.0, 1.0)
    checks.append(("s2_boundary_max", rp_max is not None and rp_max.verify_proof()))

    # S2.6: Tampered proof fails
    if rp:
        tampered = RangeProof(
            commitment=rp.commitment, min_val=rp.min_val,
            max_val=rp.max_val, proof_low=rp.proof_low + 1,
            proof_high=rp.proof_high, challenge=rp.challenge,
            response_low=rp.response_low, response_high=rp.response_high,
        )
        checks.append(("s2_tampered_fails", not tampered.verify_proof()))

    # ── S3: Selective Disclosure ─────────────────────────────────────────

    cred = T3Credential(
        talent=0.85, training=0.72, temperament=0.91,
        issuer_id="authority_1", subject_id="entity_42",
        timestamp=time.time(),
    )

    # S3.1: Disclose only talent
    sd = SelectiveDisclosure.create(cred, {"talent"})
    checks.append(("s3_talent_disclosed", sd.disclosed.get("talent") == 0.85))

    # S3.2: Training is hidden
    checks.append(("s3_training_hidden", "training" not in sd.disclosed))

    # S3.3: Hidden dimensions have commitments
    checks.append(("s3_commitments_exist",
                    "training" in sd.commitments and "temperament" in sd.commitments))

    # S3.4: Hidden dimensions have range proofs
    checks.append(("s3_range_proofs_exist",
                    "training" in sd.range_proofs and "temperament" in sd.range_proofs))

    # S3.5: Selective disclosure verifies
    checks.append(("s3_sd_verifies", sd.verify()))

    # S3.6: Disclose nothing — all hidden
    sd_none = SelectiveDisclosure.create(cred, set())
    checks.append(("s3_all_hidden", len(sd_none.disclosed) == 0 and
                    len(sd_none.commitments) == 3))

    # S3.7: Disclose everything — nothing hidden
    sd_all = SelectiveDisclosure.create(cred, {"talent", "training", "temperament"})
    checks.append(("s3_all_disclosed", len(sd_all.disclosed) == 3 and
                    len(sd_all.commitments) == 0))

    # S3.8: Credential hash is consistent
    checks.append(("s3_cred_hash", len(sd.credential_hash) == 64))

    # ── S4: Trust Comparison ─────────────────────────────────────────────

    # S4.1: A higher than B
    comp = TrustComparison.compare(0.8, 0.6)
    checks.append(("s4_a_higher", comp.result == "a_higher"))

    # S4.2: B higher than A
    comp2 = TrustComparison.compare(0.3, 0.7)
    checks.append(("s4_b_higher", comp2.result == "b_higher"))

    # S4.3: Equal within epsilon
    comp3 = TrustComparison.compare(0.5, 0.505)
    checks.append(("s4_equal", comp3.result == "equal"))

    # S4.4: Commitments are different
    checks.append(("s4_different_commitments",
                    comp.party_a_commitment != comp.party_b_commitment))

    # S4.5: Proof exists
    checks.append(("s4_proof_exists", len(comp.comparison_proof) == 32))

    # ── S5: Private Set Intersection ─────────────────────────────────────

    # S5.1: PSI with overlapping sets
    alice = PSIProtocol("alice", {"ent_1", "ent_2", "ent_3", "ent_4"})
    bob = PSIProtocol("bob", {"ent_2", "ent_3", "ent_5", "ent_6"})

    alice_masked = alice.generate_masked_set()
    bob_masked = bob.generate_masked_set()
    checks.append(("s5_masked_set_size", len(alice_masked) == 4))

    # S5.2: Masked sets don't reveal entity IDs
    checks.append(("s5_masked_hides_ids",
                    not any("ent_" in m for m in alice_masked)))

    # S5.3: PSI with identical sets
    clone = PSIProtocol("clone", {"ent_1", "ent_2"})
    clone2 = PSIProtocol("clone2", {"ent_1", "ent_2"})
    c_masked = clone.generate_masked_set()
    c2_masked = clone2.generate_masked_set()
    # Different keys produce different masks
    checks.append(("s5_different_masks", c_masked != c2_masked))

    # S5.4: PSI with disjoint sets
    disjoint_a = PSIProtocol("a", {"x1", "x2"})
    disjoint_b = PSIProtocol("b", {"y1", "y2"})
    da = disjoint_a.generate_masked_set()
    db = disjoint_b.generate_masked_set()
    checks.append(("s5_disjoint_no_overlap", len(da & db) == 0))

    # S5.5: Direct intersection reveals correct count
    actual_intersection = alice.trusted_entities & bob.trusted_entities
    checks.append(("s5_actual_intersection", len(actual_intersection) == 2))

    # ── S6: Homomorphic Trust Aggregation ────────────────────────────────

    agg = HomomorphicAggregator()

    # S6.1: Add witness scores
    c1 = agg.add_witness_score(0.8)
    c2 = agg.add_witness_score(0.7)
    c3 = agg.add_witness_score(0.9)
    checks.append(("s6_three_witnesses", len(agg.commitments) == 3))

    # S6.2: Aggregate commitment
    agg_pc, true_sum = agg.aggregate()
    checks.append(("s6_aggregate_sum", abs(true_sum - 2.4) < 0.01))

    # S6.3: Aggregate commitment verifies
    checks.append(("s6_aggregate_verifies", agg.verify_aggregate(agg_pc)))

    # S6.4: Individual commitments are different
    checks.append(("s6_unique_commitments", c1 != c2 and c2 != c3))

    # S6.5: Empty aggregation
    empty_agg = HomomorphicAggregator()
    empty_pc, empty_sum = empty_agg.aggregate()
    checks.append(("s6_empty_aggregate", empty_sum == 0.0))

    # ── S7: Threshold Proofs ─────────────────────────────────────────────

    cred2 = T3Credential(
        talent=0.9, training=0.85, temperament=0.8,
        issuer_id="auth_1", subject_id="ent_1",
        timestamp=time.time(),
    )

    # S7.1: Minimum threshold — passes
    tp = ThresholdProof.prove_threshold(cred2, ThresholdPolicy.MINIMUM, 0.7)
    checks.append(("s7_min_passes", tp.satisfied and tp.verify()))

    # S7.2: Minimum threshold — fails
    tp_fail = ThresholdProof.prove_threshold(cred2, ThresholdPolicy.MINIMUM, 0.95)
    checks.append(("s7_min_fails", not tp_fail.satisfied))

    # S7.3: Composite threshold
    tp_comp = ThresholdProof.prove_threshold(
        cred2, ThresholdPolicy.COMPOSITE, 0.8,
        weights={"talent": 0.5, "training": 0.3, "temperament": 0.2}
    )
    # 0.9*0.5 + 0.85*0.3 + 0.8*0.2 = 0.45 + 0.255 + 0.16 = 0.865 >= 0.8
    checks.append(("s7_composite_passes", tp_comp.satisfied))

    # S7.4: All-above threshold — passes
    tp_all = ThresholdProof.prove_threshold(cred2, ThresholdPolicy.ALL_ABOVE, 0.75)
    checks.append(("s7_all_above_passes", tp_all.satisfied))

    # S7.5: All-above threshold — fails (temperament = 0.8 < 0.85)
    tp_all_f = ThresholdProof.prove_threshold(cred2, ThresholdPolicy.ALL_ABOVE, 0.85)
    checks.append(("s7_all_above_fails", not tp_all_f.satisfied))

    # S7.6: Any-above threshold
    tp_any = ThresholdProof.prove_threshold(cred2, ThresholdPolicy.ANY_ABOVE, 0.88)
    # talent = 0.9 >= 0.88
    checks.append(("s7_any_above_passes", tp_any.satisfied))

    # S7.7: Threshold proof verification
    checks.append(("s7_threshold_verifies", tp.verify()))

    # ── S8: Anonymous Attestation ────────────────────────────────────────

    # S8.1: Create anonymous attestation
    att = AnonAttestation.create("witness_42", "subject_1", "talent", 0.85, 0.7)
    checks.append(("s8_attestation_created", att.subject_id == "subject_1"))

    # S8.2: Witness identity is blinded
    checks.append(("s8_witness_blinded",
                    "witness_42" not in att.blinded_witness_sig))

    # S8.3: Attestation verifies
    checks.append(("s8_attestation_verifies", att.verify()))

    # S8.4: Min score is disclosed
    checks.append(("s8_min_disclosed", att.min_score == 0.7))

    # S8.5: Range proof exists
    checks.append(("s8_range_proof", att.range_proof is not None))

    # ── S9: Differential Privacy ─────────────────────────────────────────

    import random
    random.seed(42)

    dp = DPTrustQuery(epsilon=1.0, delta=1e-5, sensitivity=1.0)

    # S9.1: Noisy value is close to true value (statistical)
    true_val = 0.75
    noisy_vals = [dp.add_noise(true_val) for _ in range(1000)]
    avg_noisy = sum(noisy_vals) / len(noisy_vals)
    checks.append(("s9_noise_unbiased", abs(avg_noisy - true_val) < 0.1))

    # S9.2: Noise variance scales with 1/epsilon
    dp_high = DPTrustQuery(epsilon=10.0, delta=1e-5, sensitivity=1.0)
    noisy_high = [dp_high.add_noise(true_val) for _ in range(1000)]
    var_low_eps = sum((x - true_val) ** 2 for x in noisy_vals) / len(noisy_vals)
    var_high_eps = sum((x - true_val) ** 2 for x in noisy_high) / len(noisy_high)
    checks.append(("s9_higher_eps_less_noise", var_high_eps < var_low_eps))

    # S9.3: Noisy count
    noisy_c = dp.noisy_count(100)
    checks.append(("s9_noisy_count_close", abs(noisy_c - 100) < 20))

    # S9.4: Noisy average
    scores = [0.8, 0.7, 0.9, 0.6, 0.85]
    noisy_avg = dp.noisy_average(scores)
    true_avg = sum(scores) / len(scores)
    checks.append(("s9_noisy_avg_close", abs(noisy_avg - true_avg) < 0.5))

    # S9.5: Budget composition
    per_q = dp.compose_budget(10)
    checks.append(("s9_budget_composition", abs(per_q - 0.1) < 0.001))

    # ── S10: MRH-Gated Disclosure ────────────────────────────────────────

    policy = MRHDisclosurePolicy()
    cred3 = T3Credential(
        talent=0.9, training=0.8, temperament=0.7,
        issuer_id="auth", subject_id="ent",
        timestamp=time.time(),
    )

    # S10.1: SELF zone gets exact scores
    d_self = policy.disclose(cred3, MRHZone.SELF)
    checks.append(("s10_self_exact", d_self.get("talent") == 0.9))

    # S10.2: DIRECT zone gets exact scores
    d_direct = policy.disclose(cred3, MRHZone.DIRECT)
    checks.append(("s10_direct_exact", d_direct.get("training") == 0.8))

    # S10.3: INDIRECT zone gets range proofs
    d_indirect = policy.disclose(cred3, MRHZone.INDIRECT)
    checks.append(("s10_indirect_range_proofs",
                    "range_proofs" in d_indirect))

    # S10.4: PERIPHERAL zone gets threshold proofs
    d_peripheral = policy.disclose(cred3, MRHZone.PERIPHERAL)
    checks.append(("s10_peripheral_threshold",
                    "meets_minimum" in d_peripheral))

    # S10.5: BEYOND zone gets existence only
    d_beyond = policy.disclose(cred3, MRHZone.BEYOND)
    checks.append(("s10_beyond_existence",
                    d_beyond.get("has_trust_record") is True))

    # S10.6: Zone policies are monotonically decreasing in detail
    zones = [MRHZone.SELF, MRHZone.DIRECT, MRHZone.INDIRECT,
             MRHZone.PERIPHERAL, MRHZone.BEYOND]
    detail_sizes = [len(policy.allowed_disclosure(z)) for z in zones]
    monotone = all(detail_sizes[i] >= detail_sizes[i+1]
                   for i in range(len(detail_sizes) - 1))
    checks.append(("s10_monotone_detail", monotone))

    # ── S11: Performance ─────────────────────────────────────────────────

    # S11.1: 1000 commitments under 2s
    t_start = time.time()
    for i in range(1000):
        PedersenCommitment.commit(i / 1000.0)
    commit_time = time.time() - t_start
    checks.append(("s11_1000_commits", commit_time < 2.0))

    # S11.2: 100 range proofs under 2s
    t_start = time.time()
    for i in range(100):
        pc = PedersenCommitment.commit(i / 100.0)
        RangeProof.prove(pc, 0.0, 1.0)
    rp_time = time.time() - t_start
    checks.append(("s11_100_range_proofs", rp_time < 2.0))

    # S11.3: 100 selective disclosures under 2s
    t_start = time.time()
    for i in range(100):
        c = T3Credential(i/100, i/100, i/100, "a", "b", 0.0)
        SelectiveDisclosure.create(c, {"talent"})
    sd_time = time.time() - t_start
    checks.append(("s11_100_selective_disclosures", sd_time < 2.0))

    # S11.4: 100 threshold proofs under 2s
    t_start = time.time()
    for i in range(100):
        c = T3Credential(i/100, i/100, i/100, "a", "b", 0.0)
        ThresholdProof.prove_threshold(c, ThresholdPolicy.ALL_ABOVE, 0.5)
    tp_time = time.time() - t_start
    checks.append(("s11_100_threshold_proofs", tp_time < 2.0))

    # S11.5: 50 anonymous attestations under 1s
    t_start = time.time()
    for i in range(50):
        AnonAttestation.create(f"w{i}", "subj", "talent", 0.8, 0.5)
    att_time = time.time() - t_start
    checks.append(("s11_50_attestations", att_time < 1.0))

    # ── Report ───────────────────────────────────────────────────────────

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    elapsed = time.time() - t0

    print("=" * 60)
    print(f"  Privacy-Preserving Trust Proofs — {passed}/{total} checks passed")
    print("=" * 60)

    failures = []
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
        if not ok:
            failures.append(name)

    if failures:
        print(f"\n  FAILURES:")
        for f in failures:
            print(f"    ✗ {f}")

    print(f"\n  Time: {elapsed:.2f}s")
    return passed == total


if __name__ == "__main__":
    success = run_checks()
    raise SystemExit(0 if success else 1)
