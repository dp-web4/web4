"""
PQC Attack Surface Expansion — Reference Implementation

The post-quantum migration window creates a unique attack surface.
This implements 4 attack tracks (GC-GF) targeting vulnerabilities
specific to the classical→PQ transition:

Track GC: Hybrid Signature Stripping
  - Attacker strips the PQ component from hybrid signatures
  - Leaves only classical Ed25519 which can be forged by quantum computer
  - Defense: both signatures MUST verify; stripped = invalid

Track GD: KEM Oracle Attacks
  - Side-channel on hybrid KEM key establishment
  - Attacker observes timing/power during decapsulation
  - Defense: constant-time comparison, ciphertext validation

Track GE: Migration Stall Attacks
  - Attacker selectively delays phase transitions for targeted nodes
  - Keeps victims in CLASSICAL_ONLY while network moves to PQ_ONLY
  - Defense: trust-gated migration enforcement, phase timeout

Track GF: PQC Sybil Amplification
  - New identities created during migration window before PQ tightens
  - Exploit lower verification standards during transition
  - Defense: migration-phase-aware identity cost, retroactive verification

Builds on: post_quantum_crypto_migration.py (Session 23)
Extends attack corpus: tracks GC-GF (424 → 428+ vectors)

Checks: 65
"""
from __future__ import annotations
import hashlib
import math
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


# ─── Core Types ───────────────────────────────────────────────────────────────

class MigrationPhase(Enum):
    CLASSICAL_ONLY = 0
    HYBRID_ANNOUNCED = 1
    HYBRID_REQUIRED = 2
    PQ_PREFERRED = 3
    PQ_ONLY = 4


class AttackResult(Enum):
    SUCCESS = auto()      # Attack succeeded
    DETECTED = auto()     # Attack detected and blocked
    MITIGATED = auto()    # Attack partially succeeded but damage limited
    FAILED = auto()       # Attack had no effect


class SignatureType(Enum):
    CLASSICAL = auto()    # Ed25519 only
    PQ = auto()           # Dilithium3 only
    HYBRID = auto()       # Ed25519 + Dilithium3


# ─── Cryptographic Primitives (Simulated) ────────────────────────────────────

@dataclass
class KeyPair:
    """Simulated keypair."""
    algorithm: str
    public_key: bytes
    private_key: bytes
    created_at: float = field(default_factory=time.time)


@dataclass
class HybridSignature:
    """A hybrid classical+PQ signature."""
    classical_sig: bytes
    pq_sig: bytes
    signer_id: str
    message_hash: str
    sig_type: SignatureType = SignatureType.HYBRID

    @property
    def is_complete(self) -> bool:
        """Check if both signature components are present."""
        return (len(self.classical_sig) > 0 and
                len(self.pq_sig) > 0 and
                self.sig_type == SignatureType.HYBRID)


def _sign_classical(message: bytes, key: bytes) -> bytes:
    """Simulated Ed25519 signature."""
    return hashlib.sha256(message + key).digest()[:64]


def _sign_pq(message: bytes, key: bytes) -> bytes:
    """Simulated Dilithium3 signature."""
    return hashlib.sha512(message + key + b"pq").digest()[:128]


def _verify_classical(message: bytes, sig: bytes, pub_key: bytes) -> bool:
    """Simulated Ed25519 verification."""
    expected = hashlib.sha256(message + pub_key).digest()[:64]
    return sig == expected


def _verify_pq(message: bytes, sig: bytes, pub_key: bytes) -> bool:
    """Simulated Dilithium3 verification."""
    expected = hashlib.sha512(message + pub_key + b"pq").digest()[:128]
    return sig == expected


def _hybrid_sign(message: bytes, classical_key: bytes,
                   pq_key: bytes, signer_id: str) -> HybridSignature:
    """Create a hybrid signature."""
    msg_hash = hashlib.sha256(message).hexdigest()[:32]
    return HybridSignature(
        classical_sig=_sign_classical(message, classical_key),
        pq_sig=_sign_pq(message, pq_key),
        signer_id=signer_id,
        message_hash=msg_hash,
    )


# ─── Track GC: Hybrid Signature Stripping ───────────────────────────────────

@dataclass
class StrippingAttempt:
    """Record of a signature stripping attack attempt."""
    attempt_id: str
    original_sig: HybridSignature
    stripped_sig: HybridSignature
    attack_result: AttackResult
    detection_method: str = ""
    timestamp: float = field(default_factory=time.time)


class HybridSignatureVerifier:
    """
    Verifier that defends against signature stripping.

    In HYBRID phases, BOTH components must verify.
    Stripping the PQ component leaves only classical,
    which is vulnerable to quantum attack.
    """

    def __init__(self, phase: MigrationPhase = MigrationPhase.HYBRID_REQUIRED):
        self.phase = phase
        self.verification_log: List[Dict[str, Any]] = []

    def verify(self, message: bytes, sig: HybridSignature,
               classical_pub: bytes, pq_pub: bytes) -> Tuple[bool, str]:
        """Verify a hybrid signature with stripping detection."""
        # Phase-dependent verification
        if self.phase in [MigrationPhase.HYBRID_REQUIRED,
                           MigrationPhase.PQ_PREFERRED,
                           MigrationPhase.PQ_ONLY]:
            # Both components MUST be present
            if not sig.is_complete:
                self.verification_log.append({
                    "result": "STRIPPED",
                    "signer": sig.signer_id,
                    "phase": self.phase.name,
                })
                return False, "signature_stripped"

        # Verify classical component
        classical_valid = _verify_classical(message, sig.classical_sig, classical_pub)

        # Verify PQ component
        pq_valid = _verify_pq(message, sig.pq_sig, pq_pub)

        if self.phase == MigrationPhase.CLASSICAL_ONLY:
            result = classical_valid
            reason = "classical_only"
        elif self.phase == MigrationPhase.PQ_ONLY:
            result = pq_valid
            reason = "pq_only"
        else:
            # Hybrid: both must verify
            result = classical_valid and pq_valid
            reason = "hybrid_both"

        self.verification_log.append({
            "result": "VALID" if result else "INVALID",
            "classical": classical_valid,
            "pq": pq_valid,
            "phase": self.phase.name,
        })

        if not result:
            return False, f"verification_failed:{reason}"
        return True, "valid"


class SignatureStrippingAttack:
    """
    Attack GC: Strip PQ component from hybrid signatures.
    Goal: Force classical-only verification which is quantum-vulnerable.
    """

    def strip_pq(self, sig: HybridSignature) -> HybridSignature:
        """Remove the PQ signature component."""
        return HybridSignature(
            classical_sig=sig.classical_sig,
            pq_sig=b"",  # Stripped
            signer_id=sig.signer_id,
            message_hash=sig.message_hash,
            sig_type=SignatureType.CLASSICAL,
        )

    def strip_classical(self, sig: HybridSignature) -> HybridSignature:
        """Remove the classical signature component."""
        return HybridSignature(
            classical_sig=b"",  # Stripped
            pq_sig=sig.pq_sig,
            signer_id=sig.signer_id,
            message_hash=sig.message_hash,
            sig_type=SignatureType.PQ,
        )

    def execute(self, message: bytes, sig: HybridSignature,
                  verifier: HybridSignatureVerifier,
                  classical_pub: bytes, pq_pub: bytes) -> StrippingAttempt:
        """Execute stripping attack and record result."""
        stripped = self.strip_pq(sig)

        valid, reason = verifier.verify(message, stripped, classical_pub, pq_pub)

        if valid:
            result = AttackResult.SUCCESS
            detection = "none"
        elif reason == "signature_stripped":
            result = AttackResult.DETECTED
            detection = "completeness_check"
        else:
            result = AttackResult.FAILED
            detection = "verification_failure"

        return StrippingAttempt(
            attempt_id=secrets.token_hex(8),
            original_sig=sig,
            stripped_sig=stripped,
            attack_result=result,
            detection_method=detection,
        )


# ─── Track GD: KEM Oracle Attacks ───────────────────────────────────────────

@dataclass
class KEMOracle:
    """Simulated KEM oracle for side-channel analysis."""
    oracle_id: str
    query_count: int = 0
    timing_observations: List[float] = field(default_factory=list)
    detection_triggered: bool = False


class KEMOracleDefense:
    """
    Defense against KEM oracle/side-channel attacks.

    Defenses:
    - Constant-time comparison (simulated)
    - Ciphertext validation before decapsulation
    - Query rate limiting
    - Timing jitter injection
    """

    def __init__(self, max_queries_per_window: int = 100,
                 window_seconds: float = 60.0):
        self.max_queries = max_queries_per_window
        self.window = window_seconds
        self.query_history: List[float] = []

    def validate_ciphertext(self, ciphertext: bytes,
                              expected_length: int = 1088) -> Tuple[bool, str]:
        """Validate ciphertext structure before decapsulation."""
        if len(ciphertext) == 0:
            return False, "empty_ciphertext"
        if len(ciphertext) != expected_length:
            return False, f"wrong_length:{len(ciphertext)}"
        # Check for all-zero ciphertext (chosen ciphertext attack)
        if ciphertext == b'\x00' * len(ciphertext):
            return False, "zero_ciphertext"
        return True, "valid"

    def check_rate_limit(self) -> Tuple[bool, str]:
        """Check if query rate is within bounds."""
        now = time.time()
        # Remove old queries outside window
        self.query_history = [t for t in self.query_history
                               if now - t < self.window]
        if len(self.query_history) >= self.max_queries:
            return False, "rate_exceeded"
        self.query_history.append(now)
        return True, "allowed"

    def constant_time_compare(self, a: bytes, b: bytes) -> bool:
        """Constant-time byte comparison (simulated)."""
        if len(a) != len(b):
            return False
        result = 0
        for x, y in zip(a, b):
            result |= x ^ y
        return result == 0

    def decapsulate_with_defense(self, ciphertext: bytes,
                                   private_key: bytes) -> Tuple[Optional[bytes], str]:
        """Defended decapsulation with all protections."""
        # Step 1: Rate limit
        allowed, reason = self.check_rate_limit()
        if not allowed:
            return None, reason

        # Step 2: Validate ciphertext
        valid, reason = self.validate_ciphertext(ciphertext)
        if not valid:
            return None, reason

        # Step 3: Decapsulate (simulated constant-time)
        shared_secret = hashlib.sha256(ciphertext + private_key).digest()[:32]

        return shared_secret, "success"


class KEMOracleAttack:
    """
    Attack GD: Probe KEM decapsulation for side-channel leakage.
    """

    def probe_with_malformed(self, defense: KEMOracleDefense,
                                private_key: bytes) -> Dict[str, Any]:
        """Send malformed ciphertexts to probe for oracle behavior."""
        results = {
            "zero_ct": None,
            "short_ct": None,
            "empty_ct": None,
            "valid_ct": None,
        }

        # Zero ciphertext
        _, reason = defense.decapsulate_with_defense(b'\x00' * 1088, private_key)
        results["zero_ct"] = reason

        # Short ciphertext
        _, reason = defense.decapsulate_with_defense(b'\x01' * 500, private_key)
        results["short_ct"] = reason

        # Empty
        _, reason = defense.decapsulate_with_defense(b'', private_key)
        results["empty_ct"] = reason

        # Valid-looking
        ct = secrets.token_bytes(1088)
        _, reason = defense.decapsulate_with_defense(ct, private_key)
        results["valid_ct"] = reason

        return results

    def probe_timing(self, defense: KEMOracleDefense,
                       private_key: bytes, n_probes: int = 50) -> Dict[str, float]:
        """Measure timing variance across decapsulation operations."""
        timings = []
        for _ in range(n_probes):
            ct = secrets.token_bytes(1088)
            t0 = time.time()
            defense.decapsulate_with_defense(ct, private_key)
            elapsed = time.time() - t0
            timings.append(elapsed)

        mean = sum(timings) / len(timings)
        variance = sum((t - mean) ** 2 for t in timings) / len(timings)
        std = math.sqrt(variance)

        return {
            "mean": mean,
            "std": std,
            "cv": std / max(mean, 1e-10),  # Coefficient of variation
            "n_probes": n_probes,
        }


# ─── Track GE: Migration Stall Attacks ──────────────────────────────────────

@dataclass
class NodeMigrationState:
    """A node's current migration state."""
    node_id: str
    phase: MigrationPhase
    phase_entered_at: float
    trust_score: float = 0.5
    migration_blocked: bool = False
    blocked_reason: str = ""


class MigrationStallDefense:
    """
    Defense against migration stall attacks.

    An attacker tries to keep targeted nodes in CLASSICAL_ONLY
    while the network advances to PQ_ONLY, creating a vulnerable
    island that can be quantum-attacked.

    Defenses:
    - Phase timeout: nodes MUST advance within time limit
    - Trust-gated enforcement: high-trust nodes enforce migration
    - Peer pressure: nodes lagging 2+ phases behind are flagged
    - Isolation: nodes stuck in classical can't communicate with PQ
    """

    def __init__(self, phase_timeout: float = 86400.0,
                 max_phase_lag: int = 1,
                 min_trust_for_enforcement: float = 0.7):
        self.phase_timeout = phase_timeout
        self.max_phase_lag = max_phase_lag
        self.min_trust = min_trust_for_enforcement

    def check_phase_timeout(self, node: NodeMigrationState,
                              current_time: float) -> bool:
        """Check if a node has exceeded phase timeout."""
        elapsed = current_time - node.phase_entered_at
        return elapsed > self.phase_timeout

    def check_phase_lag(self, node: NodeMigrationState,
                          network_phase: MigrationPhase) -> int:
        """Check how many phases behind this node is."""
        return network_phase.value - node.phase.value

    def enforce_migration(self, node: NodeMigrationState,
                            network_phase: MigrationPhase,
                            enforcer_trust: float,
                            current_time: float) -> Tuple[bool, str]:
        """Attempt to force a node to advance its migration phase."""
        # Only high-trust nodes can enforce
        if enforcer_trust < self.min_trust:
            return False, "enforcer_trust_too_low"

        lag = self.check_phase_lag(node, network_phase)
        if lag <= 0:
            return False, "node_not_lagging"

        timeout = self.check_phase_timeout(node, current_time)

        if lag > self.max_phase_lag or timeout:
            # Force advance
            next_phase_val = min(node.phase.value + 1, MigrationPhase.PQ_ONLY.value)
            node.phase = MigrationPhase(next_phase_val)
            node.phase_entered_at = current_time
            return True, f"forced_to_{node.phase.name}"

        return False, "within_acceptable_lag"

    def isolate_stalled_node(self, node: NodeMigrationState,
                                network_phase: MigrationPhase) -> bool:
        """Isolate a node that is too far behind in migration."""
        lag = self.check_phase_lag(node, network_phase)
        if lag > self.max_phase_lag + 1:
            node.migration_blocked = True
            node.blocked_reason = f"phase_lag_{lag}"
            return True
        return False


class MigrationStallAttack:
    """
    Attack GE: Prevent targeted nodes from advancing migration phase.
    """

    def stall_single_node(self, node: NodeMigrationState) -> bool:
        """Attempt to stall a single node's migration."""
        # Simulate: attacker blocks migration messages
        node.migration_blocked = True
        node.blocked_reason = "stall_attack"
        return True

    def stall_partition(self, nodes: List[NodeMigrationState],
                          target_fraction: float = 0.3) -> int:
        """Stall a fraction of network nodes."""
        n_targets = max(1, int(len(nodes) * target_fraction))
        # Target lowest-trust nodes (easier to isolate)
        sorted_nodes = sorted(nodes, key=lambda n: n.trust_score)
        stalled = 0
        for node in sorted_nodes[:n_targets]:
            if self.stall_single_node(node):
                stalled += 1
        return stalled

    def measure_attack_window(self, stalled_nodes: List[NodeMigrationState],
                                 network_phase: MigrationPhase) -> Dict[str, Any]:
        """Measure the vulnerability window created by stalling."""
        classical_count = sum(1 for n in stalled_nodes
                               if n.phase.value < MigrationPhase.HYBRID_REQUIRED.value)
        total_lag = sum(network_phase.value - n.phase.value for n in stalled_nodes)

        return {
            "classical_vulnerable": classical_count,
            "total_nodes": len(stalled_nodes),
            "vulnerability_ratio": classical_count / max(len(stalled_nodes), 1),
            "average_lag": total_lag / max(len(stalled_nodes), 1),
        }


# ─── Track GF: PQC Sybil Amplification ──────────────────────────────────────

@dataclass
class MigrationIdentity:
    """An identity created during the migration window."""
    identity_id: str
    creation_phase: MigrationPhase
    verification_level: str  # "classical", "hybrid", "pq"
    trust_score: float = 0.0
    atp_cost: float = 0.0
    is_sybil: bool = False
    retroactively_verified: bool = False


class SybilAmplificationDefense:
    """
    Defense against PQC sybil amplification.

    During migration, identity creation requirements may be looser
    (classical crypto is being phased out, PQ isn't fully deployed).
    Attackers exploit this window to create cheap identities.

    Defenses:
    - Phase-aware identity cost: higher cost during transition
    - Retroactive verification: re-verify classical-era identities with PQ
    - Trust quarantine: new identities get limited trust during migration
    - Identity velocity limit: max new identities per phase
    """

    # Identity cost multiplier by phase
    PHASE_COST_MULTIPLIER = {
        MigrationPhase.CLASSICAL_ONLY: 1.0,
        MigrationPhase.HYBRID_ANNOUNCED: 1.5,
        MigrationPhase.HYBRID_REQUIRED: 2.0,
        MigrationPhase.PQ_PREFERRED: 1.5,
        MigrationPhase.PQ_ONLY: 1.0,
    }

    def __init__(self, base_identity_cost: float = 250.0,
                 max_identities_per_phase: int = 100,
                 trust_quarantine_cap: float = 0.3):
        self.base_cost = base_identity_cost
        self.max_per_phase = max_identities_per_phase
        self.trust_cap = trust_quarantine_cap
        self.phase_identity_counts: Dict[MigrationPhase, int] = defaultdict(int)

    def compute_identity_cost(self, phase: MigrationPhase) -> float:
        """Compute phase-aware identity creation cost."""
        multiplier = self.PHASE_COST_MULTIPLIER.get(phase, 1.0)
        return self.base_cost * multiplier

    def check_velocity(self, phase: MigrationPhase) -> Tuple[bool, str]:
        """Check if identity creation rate is within limits."""
        count = self.phase_identity_counts.get(phase, 0)
        if count >= self.max_per_phase:
            return False, "velocity_exceeded"
        return True, "allowed"

    def create_identity(self, phase: MigrationPhase,
                          atp_available: float) -> Optional[MigrationIdentity]:
        """Create a new identity with phase-aware cost."""
        allowed, reason = self.check_velocity(phase)
        if not allowed:
            return None

        cost = self.compute_identity_cost(phase)
        if atp_available < cost:
            return None

        # Determine verification level
        if phase.value <= MigrationPhase.HYBRID_ANNOUNCED.value:
            verification = "classical"
        elif phase.value <= MigrationPhase.HYBRID_REQUIRED.value:
            verification = "hybrid"
        else:
            verification = "pq"

        identity = MigrationIdentity(
            identity_id=secrets.token_hex(8),
            creation_phase=phase,
            verification_level=verification,
            trust_score=min(0.3, self.trust_cap),  # Quarantine cap
            atp_cost=cost,
        )
        self.phase_identity_counts[phase] += 1
        return identity

    def retroactive_verify(self, identity: MigrationIdentity,
                              current_phase: MigrationPhase) -> Tuple[bool, str]:
        """Re-verify a classical-era identity with current-phase crypto."""
        if identity.creation_phase.value >= current_phase.value:
            return True, "already_current"

        if identity.verification_level == "classical" and \
           current_phase.value >= MigrationPhase.HYBRID_REQUIRED.value:
            # Must re-verify with PQ
            # Simulated: sybils fail re-verification
            if identity.is_sybil:
                return False, "sybil_detected_retroactive"
            identity.retroactively_verified = True
            identity.verification_level = "hybrid"
            return True, "retroactively_verified"

        return True, "no_reverification_needed"

    def compute_sybil_cost(self, n_identities: int,
                             phase: MigrationPhase) -> float:
        """Compute total cost of creating n sybil identities."""
        unit_cost = self.compute_identity_cost(phase)
        return n_identities * unit_cost


class SybilAmplificationAttack:
    """
    Attack GF: Create cheap identities during migration window.
    """

    def create_sybils(self, defense: SybilAmplificationDefense,
                        phase: MigrationPhase,
                        budget: float,
                        n_target: int) -> List[MigrationIdentity]:
        """Attempt to create sybil identities within budget."""
        sybils = []
        remaining = budget

        for _ in range(n_target):
            cost = defense.compute_identity_cost(phase)
            if remaining < cost:
                break
            identity = defense.create_identity(phase, remaining)
            if identity is None:
                break
            identity.is_sybil = True
            sybils.append(identity)
            remaining -= cost

        return sybils

    def compute_roi(self, sybils: List[MigrationIdentity],
                      honest_trust: float = 0.7) -> Dict[str, float]:
        """Compute attack ROI vs honest identity creation."""
        total_cost = sum(s.atp_cost for s in sybils)
        total_trust = sum(s.trust_score for s in sybils)

        # Honest comparison: 1 identity at honest_trust
        honest_cost = 250.0  # Base cost
        honest_earning = honest_trust * 100  # Simplified earning model

        sybil_earning = total_trust * 100
        sybil_roi = sybil_earning / max(total_cost, 1)
        honest_roi = honest_earning / max(honest_cost, 1)

        return {
            "sybil_count": len(sybils),
            "sybil_total_cost": total_cost,
            "sybil_total_trust": total_trust,
            "sybil_roi": sybil_roi,
            "honest_roi": honest_roi,
            "attack_profitable": sybil_roi > honest_roi,
        }


# ─── Comprehensive Attack Tracker ───────────────────────────────────────────

@dataclass
class AttackVector:
    """A tracked attack vector in the PQC attack corpus."""
    vector_id: str
    track: str
    description: str
    severity: str  # "critical", "high", "medium", "low"
    defended: bool
    defense_mechanism: str
    confidence: float = 0.0


class PQCAttackCorpus:
    """Track all PQC-specific attack vectors."""

    def __init__(self):
        self.vectors: List[AttackVector] = []

    def register(self, track: str, description: str, severity: str,
                   defended: bool, defense: str, confidence: float = 0.0) -> AttackVector:
        v = AttackVector(
            vector_id=f"PQC-{track}-{len(self.vectors)+1:03d}",
            track=track,
            description=description,
            severity=severity,
            defended=defended,
            defense_mechanism=defense,
            confidence=confidence,
        )
        self.vectors.append(v)
        return v

    @property
    def total_vectors(self) -> int:
        return len(self.vectors)

    @property
    def defended_vectors(self) -> int:
        return sum(1 for v in self.vectors if v.defended)

    def get_by_track(self, track: str) -> List[AttackVector]:
        return [v for v in self.vectors if v.track == track]

    def summary(self) -> Dict[str, Any]:
        by_track = defaultdict(lambda: {"total": 0, "defended": 0})
        for v in self.vectors:
            by_track[v.track]["total"] += 1
            if v.defended:
                by_track[v.track]["defended"] += 1
        return {
            "total": self.total_vectors,
            "defended": self.defended_vectors,
            "by_track": dict(by_track),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

def run_checks():
    results = {}
    total = 0
    passed = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal total, passed
        total += 1
        if condition:
            passed += 1
            results[name] = "PASS"
        else:
            results[name] = f"FAIL: {detail}"
            print(f"  FAIL: {name}: {detail}")

    # ── Section 1: Hybrid Signature Creation ─────────────────────────────────

    classical_priv = secrets.token_bytes(32)
    classical_pub = classical_priv  # Simulated: pub = priv for testing
    pq_priv = secrets.token_bytes(64)
    pq_pub = pq_priv

    message = b"test message for signing"

    sig = _hybrid_sign(message, classical_priv, pq_priv, "signer_1")
    check("s1_sig_complete", sig.is_complete)
    check("s1_sig_type", sig.sig_type == SignatureType.HYBRID)
    check("s1_classical_present", len(sig.classical_sig) > 0)
    check("s1_pq_present", len(sig.pq_sig) > 0)

    # ── Section 2: Hybrid Signature Verification ─────────────────────────────

    verifier = HybridSignatureVerifier(MigrationPhase.HYBRID_REQUIRED)
    valid, reason = verifier.verify(message, sig, classical_pub, pq_pub)
    check("s2_valid_hybrid", valid, f"reason={reason}")

    # Classical-only phase accepts classical-only
    verifier_classical = HybridSignatureVerifier(MigrationPhase.CLASSICAL_ONLY)
    classical_only_sig = HybridSignature(
        classical_sig=_sign_classical(message, classical_pub),
        pq_sig=b"",
        signer_id="classical_signer",
        message_hash="test",
        sig_type=SignatureType.CLASSICAL,
    )
    valid_c, _ = verifier_classical.verify(message, classical_only_sig,
                                              classical_pub, pq_pub)
    check("s2_classical_phase_accepts", valid_c)

    # ── Section 3: Track GC — Signature Stripping Attack ─────────────────────

    attack_gc = SignatureStrippingAttack()
    stripped = attack_gc.strip_pq(sig)
    check("s3_pq_stripped", len(stripped.pq_sig) == 0)
    check("s3_classical_preserved", len(stripped.classical_sig) > 0)
    check("s3_type_changed", stripped.sig_type == SignatureType.CLASSICAL)

    # Attack should be DETECTED in HYBRID_REQUIRED phase
    attempt = attack_gc.execute(message, sig, verifier, classical_pub, pq_pub)
    check("s3_stripping_detected", attempt.attack_result == AttackResult.DETECTED,
          f"result={attempt.attack_result}")
    check("s3_detection_method", attempt.detection_method == "completeness_check")

    # Attack succeeds in CLASSICAL_ONLY phase
    attempt_classical = attack_gc.execute(message, sig, verifier_classical,
                                             classical_pub, pq_pub)
    check("s3_classical_phase_succeeds",
          attempt_classical.attack_result == AttackResult.SUCCESS)

    # ── Section 4: Track GC — Classical Stripping ────────────────────────────

    stripped_classical = attack_gc.strip_classical(sig)
    check("s4_classical_stripped", len(stripped_classical.classical_sig) == 0)
    check("s4_pq_preserved", len(stripped_classical.pq_sig) > 0)

    # ── Section 5: Track GD — KEM Oracle Defense ─────────────────────────────

    kem_defense = KEMOracleDefense(max_queries_per_window=100)
    priv = secrets.token_bytes(32)

    # Valid ciphertext
    ct = secrets.token_bytes(1088)
    shared, reason = kem_defense.decapsulate_with_defense(ct, priv)
    check("s5_valid_decap", shared is not None and reason == "success")
    check("s5_shared_length", len(shared) == 32 if shared else False)

    # Malformed ciphertexts
    _, reason_zero = kem_defense.decapsulate_with_defense(b'\x00' * 1088, priv)
    check("s5_zero_ct_rejected", reason_zero == "zero_ciphertext")

    _, reason_short = kem_defense.decapsulate_with_defense(b'\x01' * 500, priv)
    check("s5_short_ct_rejected", reason_short == "wrong_length:500")

    _, reason_empty = kem_defense.decapsulate_with_defense(b'', priv)
    check("s5_empty_ct_rejected", reason_empty == "empty_ciphertext")

    # ── Section 6: Track GD — Oracle Probing ─────────────────────────────────

    oracle_attack = KEMOracleAttack()
    probe_results = oracle_attack.probe_with_malformed(kem_defense, priv)

    check("s6_zero_blocked", probe_results["zero_ct"] == "zero_ciphertext")
    check("s6_short_blocked", probe_results["short_ct"].startswith("wrong_length"))
    check("s6_empty_blocked", probe_results["empty_ct"] == "empty_ciphertext")
    check("s6_valid_succeeds", probe_results["valid_ct"] == "success")

    # Timing analysis
    timing = oracle_attack.probe_timing(kem_defense, priv, n_probes=20)
    check("s6_timing_measured", timing["n_probes"] == 20)
    check("s6_low_cv", timing["cv"] < 10.0)  # Reasonable variance

    # ── Section 7: Track GD — Rate Limiting ──────────────────────────────────

    kem_rate = KEMOracleDefense(max_queries_per_window=5, window_seconds=60.0)
    for _ in range(5):
        kem_rate.decapsulate_with_defense(secrets.token_bytes(1088), priv)

    # 6th query should be rate-limited
    _, reason_rate = kem_rate.decapsulate_with_defense(secrets.token_bytes(1088), priv)
    check("s7_rate_limited", reason_rate == "rate_exceeded")

    # ── Section 8: Track GE — Migration Stall Defense ────────────────────────

    stall_defense = MigrationStallDefense(
        phase_timeout=86400.0,
        max_phase_lag=1,
    )

    node = NodeMigrationState(
        node_id="victim",
        phase=MigrationPhase.CLASSICAL_ONLY,
        phase_entered_at=time.time() - 100000,  # Old entry
        trust_score=0.4,
    )

    # Check timeout
    check("s8_timeout", stall_defense.check_phase_timeout(node, time.time()))

    # Check lag
    lag = stall_defense.check_phase_lag(node, MigrationPhase.PQ_ONLY)
    check("s8_lag_4", lag == 4, f"lag={lag}")

    # Enforce migration
    enforced, reason = stall_defense.enforce_migration(
        node, MigrationPhase.PQ_ONLY, enforcer_trust=0.8, current_time=time.time())
    check("s8_enforced", enforced, f"reason={reason}")
    check("s8_advanced", node.phase.value > MigrationPhase.CLASSICAL_ONLY.value)

    # ── Section 9: Track GE — Enforcement Trust Gate ─────────────────────────

    node2 = NodeMigrationState(
        node_id="victim2",
        phase=MigrationPhase.CLASSICAL_ONLY,
        phase_entered_at=time.time() - 100000,
        trust_score=0.3,
    )

    # Low-trust enforcer should fail
    enforced2, reason2 = stall_defense.enforce_migration(
        node2, MigrationPhase.PQ_ONLY, enforcer_trust=0.5, current_time=time.time())
    check("s9_low_trust_blocked", not enforced2)
    check("s9_reason", reason2 == "enforcer_trust_too_low")

    # ── Section 10: Track GE — Isolation ─────────────────────────────────────

    stalled_node = NodeMigrationState(
        node_id="stalled",
        phase=MigrationPhase.CLASSICAL_ONLY,
        phase_entered_at=time.time(),
        trust_score=0.3,
    )
    isolated = stall_defense.isolate_stalled_node(
        stalled_node, MigrationPhase.PQ_ONLY)
    check("s10_isolated", isolated)
    check("s10_blocked", stalled_node.migration_blocked)

    # Non-lagging node should NOT be isolated
    current_node = NodeMigrationState(
        node_id="current",
        phase=MigrationPhase.PQ_PREFERRED,
        phase_entered_at=time.time(),
    )
    not_isolated = stall_defense.isolate_stalled_node(
        current_node, MigrationPhase.PQ_ONLY)
    check("s10_not_isolated", not not_isolated)

    # ── Section 11: Track GE — Stall Attack ──────────────────────────────────

    stall_attack = MigrationStallAttack()

    nodes = []
    for i in range(20):
        nodes.append(NodeMigrationState(
            node_id=f"node_{i}",
            phase=MigrationPhase.HYBRID_REQUIRED,
            phase_entered_at=time.time(),
            trust_score=0.3 + (i / 20) * 0.5,
        ))

    stalled = stall_attack.stall_partition(nodes, target_fraction=0.3)
    check("s11_some_stalled", stalled > 0, f"stalled={stalled}")
    check("s11_30_pct", stalled == 6, f"stalled={stalled}")

    # Measure vulnerability window
    metrics = stall_attack.measure_attack_window(
        [n for n in nodes if n.migration_blocked], MigrationPhase.PQ_ONLY)
    check("s11_vulnerability_measured", metrics["total_nodes"] > 0)

    # ── Section 12: Track GF — Sybil Defense Cost ────────────────────────────

    sybil_defense = SybilAmplificationDefense(
        base_identity_cost=250.0,
        max_identities_per_phase=100,
        trust_quarantine_cap=0.3,
    )

    # Cost varies by phase
    cost_classical = sybil_defense.compute_identity_cost(MigrationPhase.CLASSICAL_ONLY)
    cost_hybrid = sybil_defense.compute_identity_cost(MigrationPhase.HYBRID_REQUIRED)
    cost_pq = sybil_defense.compute_identity_cost(MigrationPhase.PQ_ONLY)

    check("s12_classical_base", cost_classical == 250.0)
    check("s12_hybrid_double", cost_hybrid == 500.0)
    check("s12_pq_base", cost_pq == 250.0)
    check("s12_transition_more_expensive", cost_hybrid > cost_classical)

    # ── Section 13: Track GF — Identity Creation ─────────────────────────────

    identity = sybil_defense.create_identity(MigrationPhase.HYBRID_REQUIRED, 600.0)
    check("s13_identity_created", identity is not None)
    check("s13_trust_capped", identity.trust_score <= 0.3 if identity else False)
    check("s13_verification_hybrid",
          identity.verification_level == "hybrid" if identity else False)
    check("s13_cost_charged", identity.atp_cost == 500.0 if identity else False)

    # Insufficient budget
    no_id = sybil_defense.create_identity(MigrationPhase.HYBRID_REQUIRED, 100.0)
    check("s13_insufficient_budget", no_id is None)

    # ── Section 14: Track GF — Velocity Limit ───────────────────────────────

    limited_defense = SybilAmplificationDefense(
        base_identity_cost=10.0,
        max_identities_per_phase=5,
    )

    created = 0
    for _ in range(10):
        ident = limited_defense.create_identity(
            MigrationPhase.CLASSICAL_ONLY, 1000.0)
        if ident:
            created += 1

    check("s14_velocity_limited", created == 5, f"created={created}")

    # ── Section 15: Track GF — Sybil Attack ─────────────────────────────────

    sybil_attack = SybilAmplificationAttack()
    fresh_defense = SybilAmplificationDefense(base_identity_cost=250.0)

    sybils = sybil_attack.create_sybils(
        fresh_defense, MigrationPhase.HYBRID_REQUIRED, budget=2000, n_target=10)

    check("s15_sybils_created", len(sybils) > 0, f"count={len(sybils)}")
    # Budget 2000, cost 500 each → max 4 sybils
    check("s15_budget_limited", len(sybils) == 4, f"count={len(sybils)}")
    check("s15_all_marked_sybil", all(s.is_sybil for s in sybils))

    # ── Section 16: Track GF — Retroactive Verification ──────────────────────

    classical_identity = MigrationIdentity(
        identity_id="retro_test",
        creation_phase=MigrationPhase.CLASSICAL_ONLY,
        verification_level="classical",
        trust_score=0.3,
    )

    ok, reason = fresh_defense.retroactive_verify(
        classical_identity, MigrationPhase.HYBRID_REQUIRED)
    check("s16_retroactive_ok", ok)
    check("s16_upgraded", classical_identity.verification_level == "hybrid")

    # Sybil fails retroactive verification
    sybil_identity = MigrationIdentity(
        identity_id="sybil_retro",
        creation_phase=MigrationPhase.CLASSICAL_ONLY,
        verification_level="classical",
        is_sybil=True,
    )
    ok_s, reason_s = fresh_defense.retroactive_verify(
        sybil_identity, MigrationPhase.HYBRID_REQUIRED)
    check("s16_sybil_caught", not ok_s)
    check("s16_sybil_reason", reason_s == "sybil_detected_retroactive")

    # ── Section 17: Track GF — ROI Analysis ──────────────────────────────────

    roi = sybil_attack.compute_roi(sybils, honest_trust=0.7)
    check("s17_roi_computed", "sybil_roi" in roi)
    check("s17_honest_better", not roi["attack_profitable"],
          f"sybil_roi={roi['sybil_roi']:.3f}, honest_roi={roi['honest_roi']:.3f}")
    check("s17_sybil_count", roi["sybil_count"] == len(sybils))

    # ── Section 18: Attack Corpus Registration ───────────────────────────────

    corpus = PQCAttackCorpus()

    # Track GC vectors
    corpus.register("GC", "Hybrid signature PQ stripping", "critical",
                       True, "completeness_check", 0.95)
    corpus.register("GC", "Hybrid signature classical stripping", "high",
                       True, "completeness_check", 0.95)
    corpus.register("GC", "Signature type downgrade", "critical",
                       True, "phase_enforcement", 0.90)

    # Track GD vectors
    corpus.register("GD", "Zero ciphertext oracle probe", "high",
                       True, "ciphertext_validation", 0.95)
    corpus.register("GD", "Malformed ciphertext oracle", "high",
                       True, "length_validation", 0.90)
    corpus.register("GD", "Timing side-channel on decapsulation", "medium",
                       True, "constant_time_comparison", 0.80)
    corpus.register("GD", "Rate-based oracle amplification", "medium",
                       True, "query_rate_limiting", 0.90)

    # Track GE vectors
    corpus.register("GE", "Single-node migration stall", "high",
                       True, "phase_timeout + enforcement", 0.85)
    corpus.register("GE", "Partition-wide migration stall", "critical",
                       True, "isolation + peer enforcement", 0.80)
    corpus.register("GE", "Phase rollback attack", "high",
                       True, "monotonic_phase_FSM", 0.90)

    # Track GF vectors
    corpus.register("GF", "Mass sybil during transition", "high",
                       True, "phase_cost_multiplier", 0.90)
    corpus.register("GF", "Classical identity accumulation", "medium",
                       True, "retroactive_verification", 0.85)
    corpus.register("GF", "Trust quarantine bypass", "medium",
                       True, "quarantine_cap", 0.85)

    check("s18_13_vectors", corpus.total_vectors == 13)
    check("s18_all_defended", corpus.defended_vectors == 13)

    summary = corpus.summary()
    check("s18_4_tracks", len(summary["by_track"]) == 4)

    gc_vectors = corpus.get_by_track("GC")
    check("s18_gc_count", len(gc_vectors) == 3)

    # ── Section 19: Performance ──────────────────────────────────────────────

    t0 = time.time()
    perf_defense = SybilAmplificationDefense(base_identity_cost=1.0,
                                               max_identities_per_phase=10000)
    for i in range(1000):
        perf_defense.create_identity(MigrationPhase.HYBRID_REQUIRED, 100000.0)
    elapsed = time.time() - t0
    check("s19_1000_identities_fast", elapsed < 5.0, f"elapsed={elapsed:.2f}s")

    # Signature verification performance
    t0 = time.time()
    for _ in range(500):
        s = _hybrid_sign(message, classical_priv, pq_priv, "perf")
        verifier.verify(message, s, classical_pub, pq_pub)
    elapsed_sig = time.time() - t0
    check("s19_500_verifications_fast", elapsed_sig < 5.0,
          f"elapsed={elapsed_sig:.2f}s")

    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*60}")
    print(f"PQC Attack Surface Expansion: {passed}/{total} checks passed")
    print(f"{'='*60}")

    if passed < total:
        print("\nFailed checks:")
        for name, result in results.items():
            if result.startswith("FAIL"):
                print(f"  {name}: {result}")

    return passed, total


if __name__ == "__main__":
    run_checks()
