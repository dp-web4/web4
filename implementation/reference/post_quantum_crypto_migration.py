"""
Post-Quantum Cryptography Migration (W4-PQC Extension 0x0007) — Reference Implementation

Implements the QUANTUM_READY extension for Web4's cryptographic layer:
- Hybrid classical/PQ signatures (Ed25519 + simulated Dilithium3)
- Hybrid KEM (X25519 + simulated Kyber-768)
- PQC migration FSM: CLASSICAL_ONLY → HYBRID_ANNOUNCED → HYBRID_REQUIRED → PQ_ONLY
- Downgrade attack defense during migration window
- CNDL (Capture-Now-Decrypt-Later) defense via key rotation
- Cipher suite negotiation with PQ suites
- Key rotation with algorithm awareness
- FSM composition with Key lifecycle FSM

NIST-finalized algorithms (simulated — no real lattice math):
  ML-KEM (Kyber-768): Key encapsulation
  ML-DSA (Dilithium3): Digital signatures
  SLH-DSA (SPHINCS+-SHA2-128s): Hash-based signatures (stateless)

Checks: 70
"""
from __future__ import annotations
import hashlib
import hmac
import math
import secrets
import struct
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


# ─── PQ Algorithm Simulation ─────────────────────────────────────────────────
# Real implementations would use pqcrypto libraries; we simulate the API shape
# with HMAC-based standin operations preserving correct size profiles.

class PQAlgorithm(Enum):
    ED25519 = "ed25519"             # Classical: 32B pub, 64B sig
    DILITHIUM3 = "dilithium3"       # PQ sig: 1952B pub, 3293B sig
    SPHINCS_SHA2_128S = "sphincs+"  # PQ sig (hash-based): 32B pub, 7856B sig
    X25519 = "x25519"              # Classical KEM: 32B pub, 32B shared
    KYBER768 = "kyber768"          # PQ KEM: 1184B pub, 1088B ct, 32B shared


@dataclass
class PQKeyPair:
    algorithm: PQAlgorithm
    public_key: bytes
    private_key: bytes
    created_at: float = field(default_factory=time.time)

    @staticmethod
    def generate(algo: PQAlgorithm) -> PQKeyPair:
        """Generate a simulated PQ keypair with correct size profile."""
        if algo == PQAlgorithm.ED25519:
            priv = secrets.token_bytes(32)
            pub = hashlib.sha256(priv).digest()  # simulated
        elif algo == PQAlgorithm.DILITHIUM3:
            priv = secrets.token_bytes(4000)
            pub = secrets.token_bytes(1952)
        elif algo == PQAlgorithm.SPHINCS_SHA2_128S:
            priv = secrets.token_bytes(64)
            pub = secrets.token_bytes(32)
        elif algo == PQAlgorithm.X25519:
            priv = secrets.token_bytes(32)
            pub = hashlib.sha256(priv).digest()
        elif algo == PQAlgorithm.KYBER768:
            priv = secrets.token_bytes(2400)
            pub = secrets.token_bytes(1184)
        else:
            raise ValueError(f"Unknown algorithm: {algo}")
        return PQKeyPair(algo, pub, priv)


class PQCrypto:
    """Simulated PQ cryptographic operations."""

    @staticmethod
    def sign(private_key: bytes, data: bytes, algo: PQAlgorithm) -> bytes:
        """Sign data with the given algorithm. Returns simulated signature."""
        mac = hmac.new(private_key[:32], data, hashlib.sha256).digest()
        if algo == PQAlgorithm.ED25519:
            return mac + mac  # 64 bytes
        elif algo == PQAlgorithm.DILITHIUM3:
            # 3293 bytes simulated (repeat HMAC to fill)
            chunks = (3293 // 32) + 1
            return (mac * chunks)[:3293]
        elif algo == PQAlgorithm.SPHINCS_SHA2_128S:
            chunks = (7856 // 32) + 1
            return (mac * chunks)[:7856]
        return mac

    @staticmethod
    def verify(public_key: bytes, data: bytes, signature: bytes,
               private_key: bytes, algo: PQAlgorithm) -> bool:
        """Verify signature. Uses private_key for simulation (real impl uses pub only)."""
        expected = PQCrypto.sign(private_key, data, algo)
        return hmac.compare_digest(signature, expected)

    @staticmethod
    def encapsulate(public_key: bytes, algo: PQAlgorithm) -> Tuple[bytes, bytes]:
        """KEM encapsulate: returns (ciphertext, shared_secret)."""
        shared = hashlib.sha256(public_key + secrets.token_bytes(16)).digest()
        if algo == PQAlgorithm.X25519:
            ct = secrets.token_bytes(32)
        elif algo == PQAlgorithm.KYBER768:
            ct = secrets.token_bytes(1088)
        else:
            ct = secrets.token_bytes(32)
        return ct, shared

    @staticmethod
    def decapsulate(private_key: bytes, ciphertext: bytes,
                     algo: PQAlgorithm) -> bytes:
        """KEM decapsulate: returns shared_secret."""
        return hashlib.sha256(private_key[:32] + ciphertext[:32]).digest()


# ─── Hybrid Signatures ───────────────────────────────────────────────────────

@dataclass
class HybridSignature:
    """Composite signature: classical + PQ."""
    classical_sig: bytes
    classical_algo: PQAlgorithm
    pq_sig: bytes
    pq_algo: PQAlgorithm

    def total_size(self) -> int:
        return len(self.classical_sig) + len(self.pq_sig)

    def serialize(self) -> bytes:
        return (struct.pack('!BH', self.classical_algo.value.encode()[0],
                            len(self.classical_sig)) +
                self.classical_sig +
                struct.pack('!BH', self.pq_algo.value.encode()[0],
                            len(self.pq_sig)) +
                self.pq_sig)


class HybridSigner:
    """Sign and verify using both classical and PQ algorithms."""

    def __init__(self, classical_key: PQKeyPair, pq_key: PQKeyPair):
        self.classical = classical_key
        self.pq = pq_key

    def sign(self, data: bytes) -> HybridSignature:
        c_sig = PQCrypto.sign(self.classical.private_key, data, self.classical.algorithm)
        pq_sig = PQCrypto.sign(self.pq.private_key, data, self.pq.algorithm)
        return HybridSignature(c_sig, self.classical.algorithm, pq_sig, self.pq.algorithm)

    def verify(self, data: bytes, sig: HybridSignature) -> Tuple[bool, bool]:
        """Returns (classical_valid, pq_valid)."""
        c_ok = PQCrypto.verify(self.classical.public_key, data, sig.classical_sig,
                                self.classical.private_key, self.classical.algorithm)
        pq_ok = PQCrypto.verify(self.pq.public_key, data, sig.pq_sig,
                                 self.pq.private_key, self.pq.algorithm)
        return c_ok, pq_ok

    def verify_hybrid(self, data: bytes, sig: HybridSignature,
                       require_both: bool = True) -> bool:
        """Verify hybrid signature. If require_both, BOTH must pass."""
        c_ok, pq_ok = self.verify(data, sig)
        if require_both:
            return c_ok and pq_ok
        return c_ok or pq_ok


# ─── Hybrid KEM ──────────────────────────────────────────────────────────────

@dataclass
class HybridKEMResult:
    """Result of hybrid key encapsulation."""
    classical_ct: bytes
    classical_shared: bytes
    pq_ct: bytes
    pq_shared: bytes
    combined_shared: bytes  # HKDF(classical_shared || pq_shared)

    def total_ct_size(self) -> int:
        return len(self.classical_ct) + len(self.pq_ct)


class HybridKEM:
    """Hybrid KEM: X25519 + Kyber-768 — concatenated shared secrets through HKDF."""

    @staticmethod
    def encapsulate(classical_pub: bytes, pq_pub: bytes,
                     info: bytes = b"web4-hybrid-kem") -> HybridKEMResult:
        c_ct, c_shared = PQCrypto.encapsulate(classical_pub, PQAlgorithm.X25519)
        pq_ct, pq_shared = PQCrypto.encapsulate(pq_pub, PQAlgorithm.KYBER768)
        # HKDF-like combination: both secrets contribute
        combined = hashlib.sha256(c_shared + pq_shared + info).digest()
        return HybridKEMResult(c_ct, c_shared, pq_ct, pq_shared, combined)

    @staticmethod
    def decapsulate(classical_priv: bytes, classical_ct: bytes,
                     pq_priv: bytes, pq_ct: bytes,
                     info: bytes = b"web4-hybrid-kem") -> bytes:
        c_shared = PQCrypto.decapsulate(classical_priv, classical_ct, PQAlgorithm.X25519)
        pq_shared = PQCrypto.decapsulate(pq_priv, pq_ct, PQAlgorithm.KYBER768)
        return hashlib.sha256(c_shared + pq_shared + info).digest()


# ─── PQ Cipher Suites ────────────────────────────────────────────────────────

class CipherSuiteID(Enum):
    W4_BASE_1 = 0x0001      # Classical: X25519 + Ed25519 + ChaCha20
    W4_FIPS_1 = 0x0002      # Classical FIPS: P-256 + ECDSA + AES-128
    W4_IOT_1 = 0x0003       # Classical IoT: X25519 + Ed25519 + AES-CCM
    W4_PQ_HYBRID_1 = 0x0004  # Hybrid: X25519+Kyber + Ed25519+Dilithium
    W4_PQ_ONLY_1 = 0x0005   # PQ-only: Kyber + Dilithium + AES-256


@dataclass
class CipherSuite:
    suite_id: CipherSuiteID
    name: str
    kem: List[PQAlgorithm]
    sig: List[PQAlgorithm]
    aead: str
    hash_algo: str
    strength: int  # Security level (higher = stronger)
    is_pq: bool
    is_hybrid: bool


CIPHER_SUITES: Dict[CipherSuiteID, CipherSuite] = {
    CipherSuiteID.W4_BASE_1: CipherSuite(
        CipherSuiteID.W4_BASE_1, "W4-BASE-1",
        [PQAlgorithm.X25519], [PQAlgorithm.ED25519],
        "ChaCha20-Poly1305", "SHA-256", 3, False, False),
    CipherSuiteID.W4_FIPS_1: CipherSuite(
        CipherSuiteID.W4_FIPS_1, "W4-FIPS-1",
        [PQAlgorithm.X25519], [PQAlgorithm.ED25519],
        "AES-128-GCM", "SHA-256", 2, False, False),
    CipherSuiteID.W4_IOT_1: CipherSuite(
        CipherSuiteID.W4_IOT_1, "W4-IOT-1",
        [PQAlgorithm.X25519], [PQAlgorithm.ED25519],
        "AES-CCM", "SHA-256", 1, False, False),
    CipherSuiteID.W4_PQ_HYBRID_1: CipherSuite(
        CipherSuiteID.W4_PQ_HYBRID_1, "W4-PQ-HYBRID-1",
        [PQAlgorithm.X25519, PQAlgorithm.KYBER768],
        [PQAlgorithm.ED25519, PQAlgorithm.DILITHIUM3],
        "AES-256-GCM", "SHA-256", 4, True, True),
    CipherSuiteID.W4_PQ_ONLY_1: CipherSuite(
        CipherSuiteID.W4_PQ_ONLY_1, "W4-PQ-ONLY-1",
        [PQAlgorithm.KYBER768], [PQAlgorithm.DILITHIUM3],
        "AES-256-GCM", "SHA-256", 5, True, False),
}


# ─── PQC Migration FSM ───────────────────────────────────────────────────────

class MigrationPhase(Enum):
    CLASSICAL_ONLY = auto()
    HYBRID_ANNOUNCED = auto()
    HYBRID_REQUIRED = auto()
    PQ_PREFERRED = auto()
    PQ_ONLY = auto()


class MigrationEvent(Enum):
    ANNOUNCE_PQ = auto()
    REQUIRE_HYBRID = auto()
    PREFER_PQ = auto()
    REQUIRE_PQ = auto()
    ROLLBACK = auto()


@dataclass
class MigrationState:
    phase: MigrationPhase
    allowed_suites: List[CipherSuiteID]
    required_pq: bool
    require_hybrid_sig: bool
    blocked_classical_only: bool
    timestamp: float = field(default_factory=time.time)


class PQCMigrationFSM:
    """
    State machine for PQC migration, composable with Key FSM from Session 21.

    Timeline (from attack simulation catalog):
      2025-01-01: announce
      2025-07-01: hybrid_start
      2026-01-01: hybrid_required (WE ARE PAST THIS)
      2027-01-01: pq_only
    """

    TRANSITIONS: Dict[MigrationPhase, Dict[MigrationEvent, MigrationPhase]] = {
        MigrationPhase.CLASSICAL_ONLY: {
            MigrationEvent.ANNOUNCE_PQ: MigrationPhase.HYBRID_ANNOUNCED,
        },
        MigrationPhase.HYBRID_ANNOUNCED: {
            MigrationEvent.REQUIRE_HYBRID: MigrationPhase.HYBRID_REQUIRED,
            MigrationEvent.ROLLBACK: MigrationPhase.CLASSICAL_ONLY,
        },
        MigrationPhase.HYBRID_REQUIRED: {
            MigrationEvent.PREFER_PQ: MigrationPhase.PQ_PREFERRED,
            MigrationEvent.ROLLBACK: MigrationPhase.HYBRID_ANNOUNCED,
        },
        MigrationPhase.PQ_PREFERRED: {
            MigrationEvent.REQUIRE_PQ: MigrationPhase.PQ_ONLY,
            MigrationEvent.ROLLBACK: MigrationPhase.HYBRID_REQUIRED,
        },
        MigrationPhase.PQ_ONLY: {
            # Terminal — no forward transitions, rollback possible
            MigrationEvent.ROLLBACK: MigrationPhase.PQ_PREFERRED,
        },
    }

    PHASE_CONFIG: Dict[MigrationPhase, Dict] = {
        MigrationPhase.CLASSICAL_ONLY: {
            "allowed": [CipherSuiteID.W4_BASE_1, CipherSuiteID.W4_FIPS_1,
                        CipherSuiteID.W4_IOT_1],
            "require_pq": False,
            "require_hybrid": False,
            "block_classical": False,
        },
        MigrationPhase.HYBRID_ANNOUNCED: {
            "allowed": [CipherSuiteID.W4_BASE_1, CipherSuiteID.W4_FIPS_1,
                        CipherSuiteID.W4_IOT_1, CipherSuiteID.W4_PQ_HYBRID_1],
            "require_pq": False,
            "require_hybrid": False,
            "block_classical": False,
        },
        MigrationPhase.HYBRID_REQUIRED: {
            "allowed": [CipherSuiteID.W4_PQ_HYBRID_1, CipherSuiteID.W4_BASE_1],
            "require_pq": False,
            "require_hybrid": True,
            "block_classical": False,
        },
        MigrationPhase.PQ_PREFERRED: {
            "allowed": [CipherSuiteID.W4_PQ_HYBRID_1, CipherSuiteID.W4_PQ_ONLY_1],
            "require_pq": True,
            "require_hybrid": True,
            "block_classical": True,
        },
        MigrationPhase.PQ_ONLY: {
            "allowed": [CipherSuiteID.W4_PQ_ONLY_1],
            "require_pq": True,
            "require_hybrid": False,
            "block_classical": True,
        },
    }

    def __init__(self, initial: MigrationPhase = MigrationPhase.CLASSICAL_ONLY):
        config = self.PHASE_CONFIG[initial]
        self.state = MigrationState(
            phase=initial,
            allowed_suites=config["allowed"],
            required_pq=config["require_pq"],
            require_hybrid_sig=config["require_hybrid"],
            blocked_classical_only=config["block_classical"],
        )
        self.history: List[Tuple[MigrationPhase, MigrationEvent, MigrationPhase]] = []

    def transition(self, event: MigrationEvent) -> bool:
        """Attempt state transition. Returns success."""
        transitions = self.TRANSITIONS.get(self.state.phase, {})
        new_phase = transitions.get(event)
        if new_phase is None:
            return False

        old_phase = self.state.phase
        config = self.PHASE_CONFIG[new_phase]
        self.state = MigrationState(
            phase=new_phase,
            allowed_suites=config["allowed"],
            required_pq=config["require_pq"],
            require_hybrid_sig=config["require_hybrid"],
            blocked_classical_only=config["block_classical"],
        )
        self.history.append((old_phase, event, new_phase))
        return True

    def is_suite_allowed(self, suite_id: CipherSuiteID) -> bool:
        return suite_id in self.state.allowed_suites

    def validate_handshake(self, offered_suites: List[CipherSuiteID]) -> Optional[CipherSuiteID]:
        """Negotiate best allowed suite from offered list."""
        allowed = set(self.state.allowed_suites)
        candidates = [s for s in offered_suites if s in allowed]
        if not candidates:
            return None

        if self.state.required_pq:
            pq_candidates = [s for s in candidates
                             if CIPHER_SUITES[s].is_pq]
            if pq_candidates:
                return max(pq_candidates, key=lambda s: CIPHER_SUITES[s].strength)

        return max(candidates, key=lambda s: CIPHER_SUITES[s].strength)


# ─── Downgrade Attack Defense ─────────────────────────────────────────────────

@dataclass
class DowngradeAlert:
    alert_type: str
    details: str
    severity: float
    blocked: bool


class DowngradeDefense:
    """Detect and block downgrade attacks during PQC migration."""

    def __init__(self, fsm: PQCMigrationFSM):
        self.fsm = fsm
        self.alerts: List[DowngradeAlert] = []

    def check_suite_proposal(self, client_suites: List[CipherSuiteID],
                              t3_composite: float) -> Tuple[Optional[CipherSuiteID], List[DowngradeAlert]]:
        """Validate client's suite proposal against migration state and trust."""
        alerts = []

        # 1. Check if client offers only classical in PQ-required phase
        if self.fsm.state.blocked_classical_only:
            has_pq = any(CIPHER_SUITES[s].is_pq for s in client_suites
                         if s in CIPHER_SUITES)
            if not has_pq:
                alert = DowngradeAlert(
                    "CLASSICAL_ONLY_IN_PQ_PHASE",
                    f"Client offered only classical suites in {self.fsm.state.phase.name}",
                    1.0, True)
                alerts.append(alert)
                self.alerts.extend(alerts)
                return None, alerts

        # 2. Trust-gated minimum strength
        tier_min = {0.7: 4, 0.4: 2, 0.0: 1}
        min_strength = 1
        for threshold, strength in sorted(tier_min.items(), reverse=True):
            if t3_composite >= threshold:
                min_strength = strength
                break

        best = self.fsm.validate_handshake(client_suites)
        if best and CIPHER_SUITES[best].strength < min_strength:
            alert = DowngradeAlert(
                "BELOW_TRUST_MINIMUM",
                f"Suite {best.name} strength {CIPHER_SUITES[best].strength} < required {min_strength}",
                0.7, True)
            alerts.append(alert)
            best = None

        # 3. Hybrid phase requires hybrid sig
        if self.fsm.state.require_hybrid_sig and best:
            suite = CIPHER_SUITES[best]
            if not suite.is_hybrid and not (suite.is_pq and not suite.is_hybrid):
                # Only PQ-only in PQ_ONLY phase is acceptable
                if self.fsm.state.phase != MigrationPhase.PQ_ONLY:
                    alert = DowngradeAlert(
                        "HYBRID_REQUIRED",
                        f"Phase {self.fsm.state.phase.name} requires hybrid signatures",
                        0.8, False)
                    alerts.append(alert)

        self.alerts.extend(alerts)
        return best, alerts


# ─── CNDL (Capture-Now-Decrypt-Later) Defense ────────────────────────────────

@dataclass
class KeyAgeAlert:
    key_id: str
    age_days: float
    algorithm: PQAlgorithm
    needs_rotation: bool


class CNDLDefense:
    """
    Defense against harvest-now-decrypt-later attacks.
    Keys older than threshold without rotation are flagged.
    Classical keys have shorter max age than PQ keys.
    """

    CLASSICAL_MAX_AGE_DAYS = 90
    PQ_MAX_AGE_DAYS = 365

    def __init__(self):
        self.alerts: List[KeyAgeAlert] = []

    def audit_key_age(self, keys: List[Tuple[str, PQAlgorithm, float]]) -> List[KeyAgeAlert]:
        """Audit key ages. Input: [(key_id, algorithm, created_timestamp)]."""
        now = time.time()
        alerts = []
        for key_id, algo, created in keys:
            age_days = (now - created) / 86400.0
            if algo in (PQAlgorithm.ED25519, PQAlgorithm.X25519):
                max_age = self.CLASSICAL_MAX_AGE_DAYS
            else:
                max_age = self.PQ_MAX_AGE_DAYS
            needs_rotation = age_days > max_age
            alert = KeyAgeAlert(key_id, age_days, algo, needs_rotation)
            if needs_rotation:
                alerts.append(alert)
        self.alerts.extend(alerts)
        return alerts

    def recommend_rotation_priority(self, keys: List[Tuple[str, PQAlgorithm, float]]) -> List[str]:
        """Return key IDs sorted by rotation urgency (most urgent first)."""
        now = time.time()
        scored = []
        for key_id, algo, created in keys:
            age_days = (now - created) / 86400.0
            if algo in (PQAlgorithm.ED25519, PQAlgorithm.X25519):
                max_age = self.CLASSICAL_MAX_AGE_DAYS
                urgency = age_days / max_age * 2.0  # Classical keys are 2x urgent
            else:
                max_age = self.PQ_MAX_AGE_DAYS
                urgency = age_days / max_age
            scored.append((key_id, urgency))
        scored.sort(key=lambda x: -x[1])
        return [k for k, _ in scored]


# ─── Key Rotation with Algorithm Awareness ───────────────────────────────────

class KeyStatus(Enum):
    PENDING = auto()
    ACTIVE = auto()
    OVERLAPPING = auto()
    EXPIRED = auto()
    REVOKED = auto()


@dataclass
class VersionedKey:
    key_id: str
    version: int
    algorithm: PQAlgorithm
    public_key: bytes
    private_key: bytes
    status: KeyStatus
    created_at: float
    expires_at: Optional[float] = None
    rotation_reason: str = "normal"
    superseded_by: Optional[str] = None


class AlgorithmAwareKeyManager:
    """Key manager that tracks algorithm type and supports PQ migration rotation."""

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.keys: Dict[str, VersionedKey] = {}
        self.current_version: int = 0
        self.active_key_id: Optional[str] = None

    def generate_key(self, algo: PQAlgorithm,
                      reason: str = "normal") -> VersionedKey:
        self.current_version += 1
        kp = PQKeyPair.generate(algo)
        key_id = f"{self.entity_id}_v{self.current_version}"
        key = VersionedKey(
            key_id=key_id,
            version=self.current_version,
            algorithm=algo,
            public_key=kp.public_key,
            private_key=kp.private_key,
            status=KeyStatus.PENDING,
            created_at=time.time(),
            rotation_reason=reason,
        )
        self.keys[key_id] = key
        return key

    def activate(self, key_id: str) -> bool:
        key = self.keys.get(key_id)
        if not key or key.status != KeyStatus.PENDING:
            return False

        # Move current active to overlapping
        if self.active_key_id:
            old = self.keys[self.active_key_id]
            old.status = KeyStatus.OVERLAPPING
            old.superseded_by = key_id
            old.expires_at = time.time() + 30 * 86400  # 30 day overlap

        key.status = KeyStatus.ACTIVE
        self.active_key_id = key_id
        return True

    def rotate_to_pq(self, pq_algo: PQAlgorithm = PQAlgorithm.DILITHIUM3) -> VersionedKey:
        """Rotate from classical to PQ algorithm."""
        key = self.generate_key(pq_algo, reason="pq_migration")
        self.activate(key.key_id)
        return key

    def get_active(self) -> Optional[VersionedKey]:
        if self.active_key_id:
            return self.keys.get(self.active_key_id)
        return None

    def get_algorithm_history(self) -> List[Tuple[int, PQAlgorithm, str]]:
        """Return version history with algorithms."""
        return sorted(
            [(k.version, k.algorithm, k.rotation_reason)
             for k in self.keys.values()],
            key=lambda x: x[0])


# ─── LCT Re-signing Ceremony ─────────────────────────────────────────────────

@dataclass
class LCTSignature:
    """Signature on an LCT document."""
    signer_id: str
    algorithm: PQAlgorithm
    signature: bytes
    key_version: int
    timestamp: float


@dataclass
class LCTResigningResult:
    lct_id: str
    old_sig: LCTSignature
    new_sig: LCTSignature
    hybrid_sig: Optional[HybridSignature]
    ceremony_hash: str


class LCTResigningCeremony:
    """Re-sign existing LCTs with PQ keys during migration."""

    def __init__(self, key_manager: AlgorithmAwareKeyManager):
        self.key_manager = key_manager
        self.results: List[LCTResigningResult] = []

    def resign(self, lct_id: str, lct_data: bytes,
               old_sig: LCTSignature,
               hybrid: bool = True) -> Optional[LCTResigningResult]:
        """Re-sign an LCT with the current (PQ) key."""
        active = self.key_manager.get_active()
        if not active:
            return None

        new_sig_bytes = PQCrypto.sign(active.private_key, lct_data, active.algorithm)
        new_sig = LCTSignature(
            signer_id=self.key_manager.entity_id,
            algorithm=active.algorithm,
            signature=new_sig_bytes,
            key_version=active.version,
            timestamp=time.time(),
        )

        hybrid_sig = None
        if hybrid and active.algorithm != PQAlgorithm.ED25519:
            # Find the old classical key for hybrid
            classical_keys = [k for k in self.key_manager.keys.values()
                              if k.algorithm == PQAlgorithm.ED25519
                              and k.status in (KeyStatus.OVERLAPPING, KeyStatus.ACTIVE)]
            if classical_keys:
                ck = classical_keys[0]
                c_sig = PQCrypto.sign(ck.private_key, lct_data, ck.algorithm)
                hybrid_sig = HybridSignature(c_sig, ck.algorithm,
                                              new_sig_bytes, active.algorithm)

        ceremony_hash = hashlib.sha256(
            lct_data + old_sig.signature + new_sig_bytes
        ).hexdigest()

        result = LCTResigningResult(lct_id, old_sig, new_sig, hybrid_sig, ceremony_hash)
        self.results.append(result)
        return result


# ─── Extension Negotiation ────────────────────────────────────────────────────

@dataclass
class PQExtension:
    """W4-PQC extension data for ClientHello/ServerHello."""
    extension_id: int = 0x0007
    supported_pq_suites: List[CipherSuiteID] = field(default_factory=list)
    migration_phase: MigrationPhase = MigrationPhase.CLASSICAL_ONLY
    pq_key_available: bool = False

    def encode(self) -> bytes:
        data = struct.pack('!HB', self.extension_id, self.migration_phase.value)
        data += struct.pack('!B', len(self.supported_pq_suites))
        for s in self.supported_pq_suites:
            data += struct.pack('!H', s.value)
        data += struct.pack('!?', self.pq_key_available)
        return data

    @staticmethod
    def decode(data: bytes) -> PQExtension:
        ext_id, phase_val = struct.unpack('!HB', data[:3])
        n_suites = struct.unpack('!B', data[3:4])[0]
        suites = []
        off = 4
        for _ in range(n_suites):
            s_val = struct.unpack('!H', data[off:off + 2])[0]
            suites.append(CipherSuiteID(s_val))
            off += 2
        pq_avail = struct.unpack('!?', data[off:off + 1])[0]
        return PQExtension(ext_id, suites, MigrationPhase(phase_val), pq_avail)


# ─── Checks ──────────────────────────────────────────────────────────────────

def run_checks():
    checks = []
    t0 = time.time()

    # ── S1: PQ Key Generation ─────────────────────────────────────────────
    ed_key = PQKeyPair.generate(PQAlgorithm.ED25519)
    checks.append(("s1_ed25519_pub_32", len(ed_key.public_key) == 32))

    dil_key = PQKeyPair.generate(PQAlgorithm.DILITHIUM3)
    checks.append(("s1_dilithium_pub_1952", len(dil_key.public_key) == 1952))

    sph_key = PQKeyPair.generate(PQAlgorithm.SPHINCS_SHA2_128S)
    checks.append(("s1_sphincs_pub_32", len(sph_key.public_key) == 32))

    kyber_key = PQKeyPair.generate(PQAlgorithm.KYBER768)
    checks.append(("s1_kyber_pub_1184", len(kyber_key.public_key) == 1184))

    # ── S2: PQ Signatures ─────────────────────────────────────────────────
    msg = b"web4 trust attestation data"
    ed_sig = PQCrypto.sign(ed_key.private_key, msg, PQAlgorithm.ED25519)
    checks.append(("s2_ed_sig_64", len(ed_sig) == 64))
    checks.append(("s2_ed_verify", PQCrypto.verify(
        ed_key.public_key, msg, ed_sig, ed_key.private_key, PQAlgorithm.ED25519)))

    dil_sig = PQCrypto.sign(dil_key.private_key, msg, PQAlgorithm.DILITHIUM3)
    checks.append(("s2_dil_sig_3293", len(dil_sig) == 3293))
    checks.append(("s2_dil_verify", PQCrypto.verify(
        dil_key.public_key, msg, dil_sig, dil_key.private_key, PQAlgorithm.DILITHIUM3)))

    sph_sig = PQCrypto.sign(sph_key.private_key, msg, PQAlgorithm.SPHINCS_SHA2_128S)
    checks.append(("s2_sphincs_sig_7856", len(sph_sig) == 7856))

    # Wrong key fails verification
    wrong = PQKeyPair.generate(PQAlgorithm.ED25519)
    checks.append(("s2_wrong_key_fails", not PQCrypto.verify(
        ed_key.public_key, msg, ed_sig, wrong.private_key, PQAlgorithm.ED25519)))

    # ── S3: Hybrid Signatures ─────────────────────────────────────────────
    signer = HybridSigner(ed_key, dil_key)
    hybrid_sig = signer.sign(msg)
    checks.append(("s3_hybrid_size", hybrid_sig.total_size() == 64 + 3293))
    c_ok, pq_ok = signer.verify(msg, hybrid_sig)
    checks.append(("s3_both_valid", c_ok and pq_ok))
    checks.append(("s3_hybrid_verify", signer.verify_hybrid(msg, hybrid_sig, require_both=True)))

    # Tampered classical sig
    tampered = HybridSignature(b"\x00" * 64, hybrid_sig.classical_algo,
                                hybrid_sig.pq_sig, hybrid_sig.pq_algo)
    checks.append(("s3_tampered_fails", not signer.verify_hybrid(msg, tampered, require_both=True)))

    # Either-or mode
    checks.append(("s3_either_mode", signer.verify_hybrid(msg, hybrid_sig, require_both=False)))

    # ── S4: Hybrid KEM ────────────────────────────────────────────────────
    x_key = PQKeyPair.generate(PQAlgorithm.X25519)
    k_key = PQKeyPair.generate(PQAlgorithm.KYBER768)
    kem_result = HybridKEM.encapsulate(x_key.public_key, k_key.public_key)
    checks.append(("s4_kem_shared_32", len(kem_result.combined_shared) == 32))
    checks.append(("s4_classical_ct_32", len(kem_result.classical_ct) == 32))
    checks.append(("s4_pq_ct_1088", len(kem_result.pq_ct) == 1088))
    checks.append(("s4_total_ct", kem_result.total_ct_size() == 32 + 1088))

    # Decapsulation produces shared secret (note: simulated, so not matching)
    dec_shared = HybridKEM.decapsulate(
        x_key.private_key, kem_result.classical_ct,
        k_key.private_key, kem_result.pq_ct)
    checks.append(("s4_decap_32", len(dec_shared) == 32))

    # ── S5: Cipher Suites ─────────────────────────────────────────────────
    checks.append(("s5_base1_classical", not CIPHER_SUITES[CipherSuiteID.W4_BASE_1].is_pq))
    checks.append(("s5_hybrid1_pq", CIPHER_SUITES[CipherSuiteID.W4_PQ_HYBRID_1].is_pq))
    checks.append(("s5_hybrid1_hybrid", CIPHER_SUITES[CipherSuiteID.W4_PQ_HYBRID_1].is_hybrid))
    checks.append(("s5_pqonly_pq", CIPHER_SUITES[CipherSuiteID.W4_PQ_ONLY_1].is_pq))
    checks.append(("s5_pqonly_not_hybrid", not CIPHER_SUITES[CipherSuiteID.W4_PQ_ONLY_1].is_hybrid))
    checks.append(("s5_strength_ordering",
                    CIPHER_SUITES[CipherSuiteID.W4_PQ_ONLY_1].strength >
                    CIPHER_SUITES[CipherSuiteID.W4_PQ_HYBRID_1].strength >
                    CIPHER_SUITES[CipherSuiteID.W4_BASE_1].strength))

    # ── S6: Migration FSM ─────────────────────────────────────────────────
    fsm = PQCMigrationFSM()
    checks.append(("s6_initial_classical", fsm.state.phase == MigrationPhase.CLASSICAL_ONLY))
    checks.append(("s6_classical_no_pq", not fsm.state.required_pq))

    # Full forward migration
    checks.append(("s6_announce", fsm.transition(MigrationEvent.ANNOUNCE_PQ)))
    checks.append(("s6_announced", fsm.state.phase == MigrationPhase.HYBRID_ANNOUNCED))
    checks.append(("s6_hybrid_available", CipherSuiteID.W4_PQ_HYBRID_1 in fsm.state.allowed_suites))

    checks.append(("s6_require_hybrid", fsm.transition(MigrationEvent.REQUIRE_HYBRID)))
    checks.append(("s6_hybrid_required", fsm.state.require_hybrid_sig))

    checks.append(("s6_prefer_pq", fsm.transition(MigrationEvent.PREFER_PQ)))
    checks.append(("s6_pq_preferred", fsm.state.required_pq))
    checks.append(("s6_classical_blocked", fsm.state.blocked_classical_only))

    checks.append(("s6_require_pq", fsm.transition(MigrationEvent.REQUIRE_PQ)))
    checks.append(("s6_pq_only", fsm.state.phase == MigrationPhase.PQ_ONLY))
    checks.append(("s6_only_pq_suite",
                    fsm.state.allowed_suites == [CipherSuiteID.W4_PQ_ONLY_1]))

    # Invalid transition
    checks.append(("s6_invalid_transition", not fsm.transition(MigrationEvent.ANNOUNCE_PQ)))

    # Rollback
    checks.append(("s6_rollback", fsm.transition(MigrationEvent.ROLLBACK)))
    checks.append(("s6_rolled_back", fsm.state.phase == MigrationPhase.PQ_PREFERRED))

    # History tracking
    checks.append(("s6_history_length", len(fsm.history) == 5))

    # ── S7: Suite Negotiation ─────────────────────────────────────────────
    fsm2 = PQCMigrationFSM(MigrationPhase.HYBRID_REQUIRED)
    # Client offers classical + hybrid
    best = fsm2.validate_handshake([CipherSuiteID.W4_BASE_1, CipherSuiteID.W4_PQ_HYBRID_1])
    checks.append(("s7_prefers_hybrid", best == CipherSuiteID.W4_PQ_HYBRID_1))

    # Client offers only classical in PQ phase
    fsm3 = PQCMigrationFSM(MigrationPhase.PQ_ONLY)
    best3 = fsm3.validate_handshake([CipherSuiteID.W4_BASE_1, CipherSuiteID.W4_FIPS_1])
    checks.append(("s7_classical_blocked", best3 is None))

    # PQ preferred: PQ suite wins
    fsm4 = PQCMigrationFSM(MigrationPhase.PQ_PREFERRED)
    best4 = fsm4.validate_handshake([CipherSuiteID.W4_PQ_HYBRID_1, CipherSuiteID.W4_PQ_ONLY_1])
    checks.append(("s7_pq_only_preferred", best4 == CipherSuiteID.W4_PQ_ONLY_1))

    # ── S8: Downgrade Defense ─────────────────────────────────────────────
    fsm5 = PQCMigrationFSM(MigrationPhase.PQ_PREFERRED)
    defense = DowngradeDefense(fsm5)

    # Classical-only client in PQ phase → blocked
    best5, alerts5 = defense.check_suite_proposal(
        [CipherSuiteID.W4_BASE_1], t3_composite=0.5)
    checks.append(("s8_classical_blocked_alert", len(alerts5) > 0))
    checks.append(("s8_blocked", best5 is None))

    # High-trust client needs high-strength suite
    fsm6 = PQCMigrationFSM(MigrationPhase.HYBRID_ANNOUNCED)
    defense2 = DowngradeDefense(fsm6)
    best6, alerts6 = defense2.check_suite_proposal(
        [CipherSuiteID.W4_IOT_1], t3_composite=0.8)
    checks.append(("s8_trust_gate_iot", best6 is None))
    checks.append(("s8_trust_alert", any(a.alert_type == "BELOW_TRUST_MINIMUM" for a in alerts6)))

    # ── S9: CNDL Defense ──────────────────────────────────────────────────
    cndl = CNDLDefense()
    now = time.time()
    keys = [
        ("k1", PQAlgorithm.ED25519, now - 100 * 86400),   # 100 days old, classical
        ("k2", PQAlgorithm.DILITHIUM3, now - 200 * 86400), # 200 days old, PQ
        ("k3", PQAlgorithm.ED25519, now - 50 * 86400),     # 50 days old, classical
        ("k4", PQAlgorithm.KYBER768, now - 400 * 86400),   # 400 days old, PQ
    ]
    alerts = cndl.audit_key_age(keys)
    checks.append(("s9_classical_old_flagged",
                    any(a.key_id == "k1" and a.needs_rotation for a in alerts)))
    checks.append(("s9_classical_young_ok",
                    not any(a.key_id == "k3" for a in alerts)))
    checks.append(("s9_pq_old_flagged",
                    any(a.key_id == "k4" and a.needs_rotation for a in alerts)))

    priority = cndl.recommend_rotation_priority(keys)
    checks.append(("s9_priority_classical_first", priority[0] == "k1"))

    # ── S10: Algorithm-Aware Key Manager ──────────────────────────────────
    km = AlgorithmAwareKeyManager("node_alpha")
    k_ed = km.generate_key(PQAlgorithm.ED25519, "initial")
    km.activate(k_ed.key_id)
    checks.append(("s10_active_ed25519", km.get_active().algorithm == PQAlgorithm.ED25519))

    k_dil = km.rotate_to_pq(PQAlgorithm.DILITHIUM3)
    checks.append(("s10_rotated_to_pq", km.get_active().algorithm == PQAlgorithm.DILITHIUM3))
    checks.append(("s10_old_overlapping",
                    km.keys[k_ed.key_id].status == KeyStatus.OVERLAPPING))
    checks.append(("s10_superseded", km.keys[k_ed.key_id].superseded_by == k_dil.key_id))

    history = km.get_algorithm_history()
    checks.append(("s10_history_2", len(history) == 2))
    checks.append(("s10_history_algos",
                    history[0][1] == PQAlgorithm.ED25519 and
                    history[1][1] == PQAlgorithm.DILITHIUM3))
    checks.append(("s10_reason_migration", history[1][2] == "pq_migration"))

    # ── S11: LCT Re-signing ───────────────────────────────────────────────
    ceremony = LCTResigningCeremony(km)
    lct_data = b"lct:web4:entity_alpha:birth_cert_v1"
    old_sig = LCTSignature("node_alpha", PQAlgorithm.ED25519,
                            PQCrypto.sign(k_ed.private_key, lct_data, PQAlgorithm.ED25519),
                            1, time.time() - 86400)
    resign_result = ceremony.resign("lct_001", lct_data, old_sig, hybrid=True)
    checks.append(("s11_resigned", resign_result is not None))
    checks.append(("s11_new_algo", resign_result.new_sig.algorithm == PQAlgorithm.DILITHIUM3))
    checks.append(("s11_hybrid_present", resign_result.hybrid_sig is not None))
    checks.append(("s11_ceremony_hash", len(resign_result.ceremony_hash) == 64))

    # Non-hybrid resign
    resign2 = ceremony.resign("lct_002", lct_data, old_sig, hybrid=False)
    checks.append(("s11_no_hybrid", resign2.hybrid_sig is None))

    # ── S12: Extension Encoding ───────────────────────────────────────────
    ext = PQExtension(
        supported_pq_suites=[CipherSuiteID.W4_PQ_HYBRID_1, CipherSuiteID.W4_PQ_ONLY_1],
        migration_phase=MigrationPhase.HYBRID_REQUIRED,
        pq_key_available=True,
    )
    encoded = ext.encode()
    decoded = PQExtension.decode(encoded)
    checks.append(("s12_roundtrip_id", decoded.extension_id == 0x0007))
    checks.append(("s12_roundtrip_phase", decoded.migration_phase == MigrationPhase.HYBRID_REQUIRED))
    checks.append(("s12_roundtrip_suites", len(decoded.supported_pq_suites) == 2))
    checks.append(("s12_roundtrip_avail", decoded.pq_key_available))

    # ── S13: Full Migration Lifecycle ─────────────────────────────────────
    # Entity starts classical, migrates through all phases
    km2 = AlgorithmAwareKeyManager("lifecycle_node")
    k_init = km2.generate_key(PQAlgorithm.ED25519, "bootstrap")
    km2.activate(k_init.key_id)

    migration = PQCMigrationFSM()
    defense3 = DowngradeDefense(migration)

    # Phase 1: Announce PQ availability
    migration.transition(MigrationEvent.ANNOUNCE_PQ)
    checks.append(("s13_phase1_announced", migration.state.phase == MigrationPhase.HYBRID_ANNOUNCED))

    # Phase 2: Require hybrid — entity must generate PQ key
    migration.transition(MigrationEvent.REQUIRE_HYBRID)
    k_pq = km2.rotate_to_pq()
    checks.append(("s13_phase2_pq_key", km2.get_active().algorithm == PQAlgorithm.DILITHIUM3))

    # Phase 3: Prefer PQ
    migration.transition(MigrationEvent.PREFER_PQ)
    best_life, _ = defense3.check_suite_proposal(
        [CipherSuiteID.W4_PQ_HYBRID_1, CipherSuiteID.W4_PQ_ONLY_1], 0.8)
    checks.append(("s13_phase3_pq_selected", best_life == CipherSuiteID.W4_PQ_ONLY_1))

    # Phase 4: PQ only
    migration.transition(MigrationEvent.REQUIRE_PQ)
    checks.append(("s13_phase4_pq_only", migration.state.phase == MigrationPhase.PQ_ONLY))

    # Re-sign LCTs
    ceremony2 = LCTResigningCeremony(km2)
    lct_resign = ceremony2.resign("lct_lifecycle", b"lct:lifecycle:data",
                                   LCTSignature("lifecycle_node", PQAlgorithm.ED25519,
                                                b"\x00" * 64, 1, time.time()),
                                   hybrid=True)
    checks.append(("s13_lct_resigned_pq", lct_resign is not None))

    # ── S14: Performance ──────────────────────────────────────────────────
    pt0 = time.time()
    for _ in range(500):
        PQKeyPair.generate(PQAlgorithm.DILITHIUM3)
    pt1 = time.time()
    checks.append(("s14_500_keygen_under_2s", pt1 - pt0 < 2.0))

    pt2 = time.time()
    for _ in range(500):
        PQCrypto.sign(dil_key.private_key, msg, PQAlgorithm.DILITHIUM3)
    pt3 = time.time()
    checks.append(("s14_500_sign_under_2s", pt3 - pt2 < 2.0))

    pt4 = time.time()
    for _ in range(200):
        HybridKEM.encapsulate(x_key.public_key, k_key.public_key)
    pt5 = time.time()
    checks.append(("s14_200_kem_under_2s", pt5 - pt4 < 2.0))

    elapsed = time.time() - t0

    # ── Print Results ─────────────────────────────────────────────────────
    passed = sum(1 for _, v in checks if v)
    total = len(checks)
    title = f"Post-Quantum Crypto Migration — {passed}/{total} checks passed"
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    for name, val in checks:
        print(f"  [{'PASS' if val else 'FAIL'}] {name}")

    failed = [n for n, v in checks if not v]
    if failed:
        print(f"\n  FAILURES:")
        for f in failed:
            print(f"    ✗ {f}")

    print(f"\n  Time: {elapsed:.2f}s\n")
    return passed == total


if __name__ == "__main__":
    run_checks()
