#!/usr/bin/env python3
"""
Web4 Witness Protocol — Unified Reference Implementation

Implements BOTH web4-witness.md and web4-witnessing.md specifications:
- 8 witness classes: time, audit, audit-minimal, oracle, existence, action, state, quality
- Attestation formats: COSE/CBOR and JOSE/JSON envelopes
- Witness discovery: bootstrap list, registry, peer recommendation, broadcast
- Witness quorum: Byzantine-tolerant multi-witness validation
- Witness incentives: ATP credits for valid attestations
- Witness reputation: accuracy, availability, diversity scoring
- Security: replay protection, nonce uniqueness, timestamp validation

Spec refs:
  web4-standard/protocols/web4-witness.md
  web4-standard/protocols/web4-witnessing.md
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ── §2 Witness Classes ──────────────────────────────────────────────

class WitnessClass(str, Enum):
    TIME = "time"
    AUDIT = "audit"
    AUDIT_MINIMAL = "audit-minimal"
    ORACLE = "oracle"
    EXISTENCE = "existence"
    ACTION = "action"
    STATE = "state"
    QUALITY = "quality"


# Required claims per witness class (§4.1-§4.8)
REQUIRED_CLAIMS: Dict[WitnessClass, List[str]] = {
    WitnessClass.TIME: ["ts", "nonce"],
    WitnessClass.AUDIT: ["policy_met", "evidence", "policy_id"],
    WitnessClass.AUDIT_MINIMAL: ["digest_valid", "rate_ok", "window_checked"],
    WitnessClass.ORACLE: ["source", "data", "ts"],
    WitnessClass.EXISTENCE: ["observed_at", "method"],
    WitnessClass.ACTION: ["action_type", "result"],
    WitnessClass.STATE: ["state", "measurement"],
    WitnessClass.QUALITY: ["metric", "value", "unit"],
}

# Optional claims per witness class
OPTIONAL_CLAIMS: Dict[WitnessClass, List[str]] = {
    WitnessClass.TIME: ["accuracy"],
    WitnessClass.AUDIT: [],
    WitnessClass.AUDIT_MINIMAL: [],
    WitnessClass.ORACLE: ["method"],
    WitnessClass.EXISTENCE: ["challenge"],
    WitnessClass.ACTION: ["actor"],
    WitnessClass.STATE: ["previous_state"],
    WitnessClass.QUALITY: ["period"],
}


# ── §3 Attestation Format ───────────────────────────────────────────

@dataclass
class WitnessAttestation:
    """Canonical witness attestation per §3.1."""
    witness: str          # did:web4:key:...
    type: WitnessClass
    claims: Dict[str, Any]
    sig: str              # "cose:..." or "jose:..."
    ts: str               # ISO 8601
    nonce: str            # multibase

    def to_dict(self) -> dict:
        return {
            "witness": self.witness,
            "type": self.type.value,
            "claims": self.claims,
            "sig": self.sig,
            "ts": self.ts,
            "nonce": self.nonce,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WitnessAttestation":
        return cls(
            witness=d["witness"],
            type=WitnessClass(d["type"]),
            claims=d["claims"],
            sig=d["sig"],
            ts=d["ts"],
            nonce=d["nonce"],
        )

    def hash(self) -> str:
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


def validate_claims(witness_type: WitnessClass, claims: dict) -> Tuple[bool, List[str]]:
    """Validate claims contain all required fields for witness type."""
    errors = []
    required = REQUIRED_CLAIMS.get(witness_type, [])
    for field_name in required:
        if field_name not in claims:
            errors.append(f"Missing required claim '{field_name}' for {witness_type.value}")
    return len(errors) == 0, errors


# ── §3.1/§3.2 Signature Envelopes ───────────────────────────────────

@dataclass
class COSEWitnessEnvelope:
    """COSE_Sign1 witness attestation per §3.2."""
    protected: dict
    payload: dict
    signature: bytes

    @classmethod
    def create(cls, witness_did: str, witness_type: WitnessClass,
               payload: dict, key_id: str) -> "COSEWitnessEnvelope":
        protected = {
            "alg": -8,  # EdDSA
            "kid": key_id,
            "content_type": "application/web4+witness+cbor",
            "witness_type": witness_type.value,
            "witness_did": witness_did,
            "ts": int(time.time()),
        }
        # Simulated signature (reference impl)
        sig_input = json.dumps({"protected": protected, "payload": payload},
                               sort_keys=True).encode()
        signature = hashlib.sha256(sig_input).digest()
        return cls(protected=protected, payload=payload, signature=signature)

    def verify(self, expected_key_id: str) -> Tuple[bool, str]:
        if self.protected.get("kid") != expected_key_id:
            return False, f"Key ID mismatch: {self.protected.get('kid')} != {expected_key_id}"
        if self.protected.get("alg") != -8:
            return False, f"Algorithm must be EdDSA (-8), got {self.protected.get('alg')}"
        sig_input = json.dumps({"protected": self.protected, "payload": self.payload},
                               sort_keys=True).encode()
        expected = hashlib.sha256(sig_input).digest()
        if self.signature != expected:
            return False, "Signature verification failed"
        return True, "OK"


@dataclass
class JOSEWitnessEnvelope:
    """JWS compact witness attestation per §3.2 JOSE variant."""
    header: dict
    payload: dict
    signature: str  # base64url

    @classmethod
    def create(cls, witness_did: str, witness_type: WitnessClass,
               payload: dict, key_id: str) -> "JOSEWitnessEnvelope":
        header = {
            "alg": "ES256",
            "kid": key_id,
            "typ": "JWT",
            "witness_type": witness_type.value,
            "witness_did": witness_did,
            "ts": payload.get("ts", ""),
        }
        sig_input = json.dumps({"header": header, "payload": payload},
                               sort_keys=True).encode()
        sig_hash = hashlib.sha256(sig_input).hexdigest()
        return cls(header=header, payload=payload, signature=sig_hash)

    def verify(self, expected_key_id: str) -> Tuple[bool, str]:
        if self.header.get("kid") != expected_key_id:
            return False, f"Key ID mismatch"
        sig_input = json.dumps({"header": self.header, "payload": self.payload},
                               sort_keys=True).encode()
        expected = hashlib.sha256(sig_input).hexdigest()
        if self.signature != expected:
            return False, "Signature verification failed"
        return True, "OK"


# ── §3.3/§3.4 Witnessing Protocol (web4-witnessing.md) ──────────────

@dataclass
class WitnessRequest:
    """Request for witness attestation per web4-witnessing.md §2."""
    requester: str       # did:web4:key:...
    witness_type: WitnessClass
    target: str          # lct:web4:...
    nonce: str
    claims_requested: List[str]
    event_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "type": "WitnessRequest",
            "requester": self.requester,
            "witness_type": self.witness_type.value,
            "target": self.target,
            "nonce": self.nonce,
            "claims_requested": self.claims_requested,
            "event_hash": self.event_hash,
        }


# ── Witness Freshness / Replay / Nonce ──────────────────────────────

class WitnessReplayGuard:
    """Prevents witness attestation replay per §7.2."""
    FRESHNESS_WINDOW_S = 300  # ±300s per spec

    def __init__(self, max_nonces: int = 10000):
        self._seen_nonces: Dict[str, float] = {}  # nonce -> timestamp
        self._max_nonces = max_nonces

    def check_freshness(self, ts_iso: str) -> Tuple[bool, str]:
        try:
            from datetime import datetime, timezone
            ts = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = abs((now - ts).total_seconds())
            if delta > self.FRESHNESS_WINDOW_S:
                return False, f"Timestamp {ts_iso} outside ±{self.FRESHNESS_WINDOW_S}s window (delta={delta:.0f}s)"
            return True, "OK"
        except Exception as e:
            return False, f"Invalid timestamp: {e}"

    def check_nonce(self, nonce: str) -> Tuple[bool, str]:
        if nonce in self._seen_nonces:
            return False, f"Nonce already used at {self._seen_nonces[nonce]}"
        self._seen_nonces[nonce] = time.time()
        self._evict_old()
        return True, "OK"

    def _evict_old(self):
        if len(self._seen_nonces) > self._max_nonces:
            cutoff = time.time() - self.FRESHNESS_WINDOW_S * 2
            self._seen_nonces = {
                k: v for k, v in self._seen_nonces.items() if v > cutoff
            }


# ── §5 Witness Discovery ────────────────────────────────────────────

class DiscoveryMethod(str, Enum):
    BOOTSTRAP = "bootstrap"
    REGISTRY = "registry"
    PEER_RECOMMENDATION = "peer_recommendation"
    BROADCAST = "broadcast"


@dataclass
class WitnessInfo:
    """Describes a known witness."""
    did: str
    classes: List[WitnessClass]
    key_id: str
    reputation: float = 0.5     # 0.0-1.0
    availability: float = 1.0   # 0.0-1.0
    last_seen: float = 0.0
    atp_rate: float = 1.0       # ATP per attestation
    discovery_method: DiscoveryMethod = DiscoveryMethod.BOOTSTRAP
    operator: str = ""          # operator ID for diversity

    def is_available(self) -> bool:
        return self.availability > 0.1 and (time.time() - self.last_seen) < 3600


class WitnessDiscovery:
    """Witness discovery per §5.1."""

    def __init__(self):
        self._bootstrap: List[WitnessInfo] = []
        self._registry: Dict[str, WitnessInfo] = {}
        self._peer_recommended: List[WitnessInfo] = []
        self._broadcast_discovered: List[WitnessInfo] = []

    def add_bootstrap(self, info: WitnessInfo):
        info.discovery_method = DiscoveryMethod.BOOTSTRAP
        self._bootstrap.append(info)
        self._registry[info.did] = info

    def add_peer_recommendation(self, info: WitnessInfo, recommender_trust: float):
        info.discovery_method = DiscoveryMethod.PEER_RECOMMENDATION
        info.reputation = min(info.reputation, recommender_trust)
        self._peer_recommended.append(info)
        self._registry[info.did] = info

    def add_broadcast(self, info: WitnessInfo):
        info.discovery_method = DiscoveryMethod.BROADCAST
        info.reputation = min(info.reputation, 0.3)  # broadcast witnesses start low
        self._broadcast_discovered.append(info)
        self._registry[info.did] = info

    def find_witnesses(self, witness_class: WitnessClass,
                       min_count: int = 1,
                       min_reputation: float = 0.3,
                       require_diversity: bool = False) -> List[WitnessInfo]:
        """Find witnesses supporting a given class, sorted by reputation."""
        candidates = [
            w for w in self._registry.values()
            if witness_class in w.classes
            and w.reputation >= min_reputation
            and w.is_available()
        ]
        candidates.sort(key=lambda w: w.reputation, reverse=True)

        if require_diversity:
            # Select witnesses from different operators
            seen_operators = set()
            diverse = []
            for w in candidates:
                op = w.operator or w.did
                if op not in seen_operators:
                    diverse.append(w)
                    seen_operators.add(op)
            candidates = diverse

        return candidates[:max(min_count, len(candidates))]

    def get_all(self) -> List[WitnessInfo]:
        return list(self._registry.values())


# ── §5.2 Witness Quorum ─────────────────────────────────────────────

class QuorumPolicy(str, Enum):
    SIMPLE_MAJORITY = "simple_majority"
    TWO_OF_THREE = "2_of_3"
    BYZANTINE = "byzantine"
    UNANIMOUS = "unanimous"


@dataclass
class QuorumResult:
    met: bool
    required: int
    received: int
    valid: int
    invalid: int
    attestations: List[WitnessAttestation]
    errors: List[str]


class WitnessQuorum:
    """Witness quorum verification per §5.2."""

    def __init__(self, policy: QuorumPolicy = QuorumPolicy.TWO_OF_THREE):
        self.policy = policy

    def required_count(self, total_witnesses: int) -> int:
        if self.policy == QuorumPolicy.SIMPLE_MAJORITY:
            return (total_witnesses // 2) + 1
        elif self.policy == QuorumPolicy.TWO_OF_THREE:
            return max(2, (total_witnesses * 2 + 2) // 3)
        elif self.policy == QuorumPolicy.BYZANTINE:
            # Tolerates (n-1)/3 malicious
            return (total_witnesses * 2 + 2) // 3
        elif self.policy == QuorumPolicy.UNANIMOUS:
            return total_witnesses
        return total_witnesses

    def verify_quorum(self, attestations: List[WitnessAttestation],
                      total_witnesses: int,
                      replay_guard: Optional[WitnessReplayGuard] = None) -> QuorumResult:
        required = self.required_count(total_witnesses)
        valid_attestations = []
        errors = []
        invalid_count = 0

        for att in attestations:
            # Validate claims
            claims_ok, claim_errors = validate_claims(att.type, att.claims)
            if not claims_ok:
                errors.extend(claim_errors)
                invalid_count += 1
                continue

            # Check nonce uniqueness
            if replay_guard:
                nonce_ok, nonce_err = replay_guard.check_nonce(att.nonce)
                if not nonce_ok:
                    errors.append(f"Witness {att.witness}: {nonce_err}")
                    invalid_count += 1
                    continue

            valid_attestations.append(att)

        met = len(valid_attestations) >= required
        return QuorumResult(
            met=met,
            required=required,
            received=len(attestations),
            valid=len(valid_attestations),
            invalid=invalid_count,
            attestations=valid_attestations,
            errors=errors,
        )

    def check_diversity(self, attestations: List[WitnessAttestation],
                        witness_registry: WitnessDiscovery) -> Tuple[bool, str]:
        """Check that witnesses come from different operators (§5.2 diversity)."""
        operators = set()
        for att in attestations:
            info = witness_registry._registry.get(att.witness)
            op = info.operator if info and info.operator else att.witness
            operators.add(op)
        if len(operators) < 2:
            return False, f"Insufficient diversity: {len(operators)} operator(s)"
        return True, f"Diverse: {len(operators)} operators"


# ── §6 Witness Incentives ───────────────────────────────────────────

@dataclass
class WitnessIncentiveSchedule:
    """ATP rewards for witness services per §6.1."""
    attestation_reward: float = 1.0   # ATP per valid attestation
    audit_reward: float = 10.0        # ATP per audit service
    oracle_reward: float = 5.0        # ATP per oracle attestation
    penalty_invalid: float = -2.0     # ATP penalty for invalid attestation
    penalty_timeout: float = -1.0     # ATP penalty for timeout


class WitnessIncentiveTracker:
    """Track ATP rewards/penalties for witnesses."""

    def __init__(self, schedule: Optional[WitnessIncentiveSchedule] = None):
        self.schedule = schedule or WitnessIncentiveSchedule()
        self._balances: Dict[str, float] = {}
        self._history: List[dict] = []

    def reward_attestation(self, witness_did: str, witness_class: WitnessClass):
        if witness_class == WitnessClass.AUDIT:
            amount = self.schedule.audit_reward
        elif witness_class == WitnessClass.ORACLE:
            amount = self.schedule.oracle_reward
        else:
            amount = self.schedule.attestation_reward

        self._balances[witness_did] = self._balances.get(witness_did, 0.0) + amount
        self._history.append({
            "witness": witness_did,
            "type": "reward",
            "amount": amount,
            "class": witness_class.value,
            "ts": time.time(),
        })

    def penalize(self, witness_did: str, reason: str):
        amount = self.schedule.penalty_invalid
        self._balances[witness_did] = self._balances.get(witness_did, 0.0) + amount
        self._history.append({
            "witness": witness_did,
            "type": "penalty",
            "amount": amount,
            "reason": reason,
            "ts": time.time(),
        })

    def get_balance(self, witness_did: str) -> float:
        return self._balances.get(witness_did, 0.0)

    def get_total_earned(self) -> float:
        return sum(e["amount"] for e in self._history if e["type"] == "reward")

    def get_total_penalties(self) -> float:
        return sum(abs(e["amount"]) for e in self._history if e["type"] == "penalty")


# ── §6.2 Witness Reputation ─────────────────────────────────────────

@dataclass
class WitnessReputation:
    """Witness reputation tracking per §6.2."""
    accuracy: float = 0.5      # correctness of attestations
    availability: float = 0.5  # uptime and responsiveness
    diversity: float = 0.5     # range of attestation types
    total_attestations: int = 0
    valid_attestations: int = 0
    invalid_attestations: int = 0
    classes_served: set = field(default_factory=set)

    @property
    def composite(self) -> float:
        return self.accuracy * 0.5 + self.availability * 0.3 + self.diversity * 0.2

    def update_accuracy(self, was_valid: bool):
        self.total_attestations += 1
        if was_valid:
            self.valid_attestations += 1
        else:
            self.invalid_attestations += 1
        if self.total_attestations > 0:
            self.accuracy = self.valid_attestations / self.total_attestations


class WitnessReputationTracker:
    """Track reputation across all witnesses."""

    def __init__(self):
        self._reputations: Dict[str, WitnessReputation] = {}

    def get_or_create(self, witness_did: str) -> WitnessReputation:
        if witness_did not in self._reputations:
            self._reputations[witness_did] = WitnessReputation()
        return self._reputations[witness_did]

    def record_attestation(self, witness_did: str, witness_class: WitnessClass,
                           was_valid: bool):
        rep = self.get_or_create(witness_did)
        rep.update_accuracy(was_valid)
        if was_valid:
            rep.classes_served.add(witness_class)
            # Diversity = unique classes / total classes
            rep.diversity = len(rep.classes_served) / len(WitnessClass)

    def record_availability(self, witness_did: str, was_available: bool):
        rep = self.get_or_create(witness_did)
        # Exponential moving average
        alpha = 0.1
        rep.availability = alpha * (1.0 if was_available else 0.0) + (1 - alpha) * rep.availability

    def get_composite(self, witness_did: str) -> float:
        rep = self.get_or_create(witness_did)
        return rep.composite

    def get_all(self) -> Dict[str, WitnessReputation]:
        return dict(self._reputations)


# ── Unified Witness Manager ─────────────────────────────────────────

class WitnessManager:
    """Orchestrates the full witness lifecycle."""

    def __init__(self):
        self.discovery = WitnessDiscovery()
        self.quorum = WitnessQuorum(QuorumPolicy.TWO_OF_THREE)
        self.replay_guard = WitnessReplayGuard()
        self.incentives = WitnessIncentiveTracker()
        self.reputation = WitnessReputationTracker()
        self._attestation_log: List[WitnessAttestation] = []

    def register_witness(self, info: WitnessInfo):
        self.discovery.add_bootstrap(info)

    def request_attestation(self, request: WitnessRequest,
                            witness_did: str) -> Optional[WitnessAttestation]:
        """Create an attestation from a registered witness."""
        info = self.discovery._registry.get(witness_did)
        if not info:
            return None
        if request.witness_type not in info.classes:
            return None
        if not info.is_available():
            self.reputation.record_availability(witness_did, False)
            return None

        self.reputation.record_availability(witness_did, True)

        # Build claims based on type
        claims = self._build_claims(request)
        nonce = request.nonce or f"mb32:{os.urandom(16).hex()}"

        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Create COSE envelope
        envelope = COSEWitnessEnvelope.create(
            witness_did=witness_did,
            witness_type=request.witness_type,
            payload={
                "role": request.witness_type.value,
                "ts": ts,
                "subject": request.target,
                "event_hash": request.event_hash or hashlib.sha256(
                    request.target.encode()).hexdigest(),
                "nonce": nonce,
            },
            key_id=info.key_id,
        )

        attestation = WitnessAttestation(
            witness=witness_did,
            type=request.witness_type,
            claims=claims,
            sig=f"cose:{envelope.signature.hex()[:32]}",
            ts=ts,
            nonce=nonce,
        )

        return attestation

    def _build_claims(self, request: WitnessRequest) -> dict:
        """Build type-specific claims."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        if request.witness_type == WitnessClass.TIME:
            return {"ts": now, "nonce": request.nonce, "accuracy": 50}
        elif request.witness_type == WitnessClass.AUDIT:
            return {"policy_met": True, "evidence": f"mb64:{os.urandom(16).hex()}",
                    "policy_id": "policy://baseline-v1"}
        elif request.witness_type == WitnessClass.AUDIT_MINIMAL:
            return {"digest_valid": True, "rate_ok": True, "window_checked": now}
        elif request.witness_type == WitnessClass.ORACLE:
            return {"source": "https://oracle.web4.io/price", "data": {"value": 42},
                    "ts": now}
        elif request.witness_type == WitnessClass.EXISTENCE:
            return {"observed_at": now, "method": "challenge-response"}
        elif request.witness_type == WitnessClass.ACTION:
            return {"action_type": "r6:execute", "result": "success"}
        elif request.witness_type == WitnessClass.STATE:
            return {"state": "active", "measurement": "heartbeat"}
        elif request.witness_type == WitnessClass.QUALITY:
            return {"metric": "response_time", "value": 0.05, "unit": "seconds"}
        return {}

    def submit_attestation(self, attestation: WitnessAttestation) -> Tuple[bool, str]:
        """Validate and record an attestation."""
        # Validate claims
        ok, errors = validate_claims(attestation.type, attestation.claims)
        if not ok:
            self.reputation.record_attestation(attestation.witness, attestation.type, False)
            self.incentives.penalize(attestation.witness, f"Invalid claims: {errors}")
            return False, f"Invalid claims: {errors}"

        # Check nonce replay
        nonce_ok, nonce_err = self.replay_guard.check_nonce(attestation.nonce)
        if not nonce_ok:
            self.reputation.record_attestation(attestation.witness, attestation.type, False)
            self.incentives.penalize(attestation.witness, nonce_err)
            return False, nonce_err

        # Record valid attestation
        self._attestation_log.append(attestation)
        self.reputation.record_attestation(attestation.witness, attestation.type, True)
        self.incentives.reward_attestation(attestation.witness, attestation.type)
        return True, "Attestation recorded"

    def verify_quorum(self, attestations: List[WitnessAttestation],
                      total_witnesses: int) -> QuorumResult:
        """Verify a quorum of attestations."""
        return self.quorum.verify_quorum(attestations, total_witnesses, self.replay_guard)

    def get_attestation_log(self) -> List[WitnessAttestation]:
        return list(self._attestation_log)


# ── MRH Witnessing Integration ──────────────────────────────────────

@dataclass
class MRHWitnessEntry:
    """Entry in MRH witnessing array per entity-relationships spec."""
    lct_id: str
    role: WitnessClass
    last_attestation: str
    witness_count: int = 0

    def to_dict(self) -> dict:
        return {
            "lct_id": self.lct_id,
            "role": self.role.value,
            "last_attestation": self.last_attestation,
            "witness_count": self.witness_count,
        }


class MRHWitnessTracker:
    """Track bidirectional witness relationships in MRH."""

    def __init__(self):
        self._entries: Dict[str, Dict[str, MRHWitnessEntry]] = {}

    def record_witness(self, observed_lct: str, witness_lct: str,
                       role: WitnessClass, ts: str):
        """Record that witness_lct witnessed observed_lct."""
        # Observed entity's MRH
        if observed_lct not in self._entries:
            self._entries[observed_lct] = {}
        key = f"{witness_lct}:{role.value}"
        if key in self._entries[observed_lct]:
            entry = self._entries[observed_lct][key]
            entry.witness_count += 1
            entry.last_attestation = ts
        else:
            self._entries[observed_lct][key] = MRHWitnessEntry(
                lct_id=witness_lct, role=role,
                last_attestation=ts, witness_count=1
            )

    def get_witnesses(self, lct_id: str) -> List[MRHWitnessEntry]:
        if lct_id not in self._entries:
            return []
        return list(self._entries[lct_id].values())

    def get_witness_count(self, lct_id: str) -> int:
        return sum(e.witness_count for e in self.get_witnesses(lct_id))

    def get_unique_witness_count(self, lct_id: str) -> int:
        entries = self.get_witnesses(lct_id)
        return len(set(e.lct_id for e in entries))


# ── Evidence Types (web4-entity-relationships.md §3.4) ───────────────

class EvidenceType(str, Enum):
    EXISTENCE = "EXISTENCE"
    ACTION = "ACTION"
    STATE = "STATE"
    TRANSITION = "TRANSITION"


@dataclass
class WitnessEvidence:
    """Evidence attached to a witnessing event."""
    evidence_type: EvidenceType
    observer_lct: str
    observed_lct: str
    evidence_data: Dict[str, Any]
    signature: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "version": "WTNS/1.0",
            "evidence_type": self.evidence_type.value,
            "observer_lct": self.observer_lct,
            "observed_lct": self.observed_lct,
            "evidence_data": self.evidence_data,
            "signature": self.signature,
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════════

def run_tests():
    from datetime import datetime, timezone
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # ── T1: Witness Classes ──────────────────────────────────────
    print("T1: Witness Classes")
    check("T1.1 Eight witness classes", len(WitnessClass) == 8)
    check("T1.2 All have required claims", all(c in REQUIRED_CLAIMS for c in WitnessClass))
    check("T1.3 Time requires ts+nonce", REQUIRED_CLAIMS[WitnessClass.TIME] == ["ts", "nonce"])
    check("T1.4 Audit requires policy_met+evidence+policy_id",
          REQUIRED_CLAIMS[WitnessClass.AUDIT] == ["policy_met", "evidence", "policy_id"])
    check("T1.5 Quality requires metric+value+unit",
          REQUIRED_CLAIMS[WitnessClass.QUALITY] == ["metric", "value", "unit"])
    check("T1.6 Optional claims exist for all", all(c in OPTIONAL_CLAIMS for c in WitnessClass))
    check("T1.7 Time optional has accuracy", "accuracy" in OPTIONAL_CLAIMS[WitnessClass.TIME])
    check("T1.8 Action optional has actor", "actor" in OPTIONAL_CLAIMS[WitnessClass.ACTION])

    # ── T2: Attestation Format ───────────────────────────────────
    print("T2: Attestation Format")
    att = WitnessAttestation(
        witness="did:web4:key:z6MkWitness1",
        type=WitnessClass.TIME,
        claims={"ts": now_iso, "nonce": "mb32:abc123"},
        sig="cose:deadbeef",
        ts=now_iso,
        nonce="mb32:abc123",
    )
    d = att.to_dict()
    check("T2.1 to_dict has witness", d["witness"] == "did:web4:key:z6MkWitness1")
    check("T2.2 to_dict has type string", d["type"] == "time")
    check("T2.3 to_dict has claims", "ts" in d["claims"])
    check("T2.4 from_dict roundtrip", WitnessAttestation.from_dict(d).witness == att.witness)
    h = att.hash()
    check("T2.5 hash is 64-char hex", len(h) == 64 and all(c in "0123456789abcdef" for c in h))
    check("T2.6 hash is deterministic", att.hash() == h)

    # ── T3: Claims Validation ────────────────────────────────────
    print("T3: Claims Validation")
    ok, errs = validate_claims(WitnessClass.TIME, {"ts": now_iso, "nonce": "n1"})
    check("T3.1 Valid time claims pass", ok)
    ok, errs = validate_claims(WitnessClass.TIME, {"ts": now_iso})
    check("T3.2 Missing nonce fails", not ok)
    check("T3.3 Error mentions nonce", "nonce" in errs[0])
    ok, errs = validate_claims(WitnessClass.AUDIT, {"policy_met": True, "evidence": "e", "policy_id": "p"})
    check("T3.4 Valid audit claims pass", ok)
    ok, errs = validate_claims(WitnessClass.AUDIT, {})
    check("T3.5 Empty audit claims fail", not ok)
    check("T3.6 Three errors for audit", len(errs) == 3)
    ok, errs = validate_claims(WitnessClass.QUALITY, {"metric": "m", "value": 1, "unit": "u"})
    check("T3.7 Valid quality claims pass", ok)
    ok, errs = validate_claims(WitnessClass.ORACLE, {"source": "s", "data": {}, "ts": now_iso})
    check("T3.8 Valid oracle claims pass", ok)
    ok, errs = validate_claims(WitnessClass.EXISTENCE, {"observed_at": now_iso, "method": "ping"})
    check("T3.9 Valid existence claims pass", ok)
    ok, errs = validate_claims(WitnessClass.STATE, {"state": "active", "measurement": "heartbeat"})
    check("T3.10 Valid state claims pass", ok)

    # ── T4: COSE Envelope ────────────────────────────────────────
    print("T4: COSE Envelope")
    envelope = COSEWitnessEnvelope.create(
        witness_did="did:web4:key:z6MkW1",
        witness_type=WitnessClass.TIME,
        payload={"role": "time", "ts": now_iso, "subject": "w4idp:test", "nonce": "n1"},
        key_id="kid-1",
    )
    check("T4.1 Protected has alg=-8", envelope.protected["alg"] == -8)
    check("T4.2 Protected has kid", envelope.protected["kid"] == "kid-1")
    check("T4.3 Protected has witness_type", envelope.protected["witness_type"] == "time")
    check("T4.4 Protected has content_type",
          envelope.protected["content_type"] == "application/web4+witness+cbor")
    ok, msg = envelope.verify("kid-1")
    check("T4.5 Verify with correct kid succeeds", ok)
    ok, msg = envelope.verify("kid-wrong")
    check("T4.6 Verify with wrong kid fails", not ok)
    check("T4.7 Signature is bytes", isinstance(envelope.signature, bytes))
    check("T4.8 Signature is 32 bytes (SHA-256)", len(envelope.signature) == 32)

    # ── T5: JOSE Envelope ────────────────────────────────────────
    print("T5: JOSE Envelope")
    jose = JOSEWitnessEnvelope.create(
        witness_did="did:web4:key:z6MkW2",
        witness_type=WitnessClass.AUDIT,
        payload={"role": "audit", "ts": now_iso, "subject": "w4idp:test2"},
        key_id="kid-2",
    )
    check("T5.1 Header has alg=ES256", jose.header["alg"] == "ES256")
    check("T5.2 Header has kid", jose.header["kid"] == "kid-2")
    check("T5.3 Header has typ=JWT", jose.header["typ"] == "JWT")
    check("T5.4 Header has witness_type=audit", jose.header["witness_type"] == "audit")
    ok, msg = jose.verify("kid-2")
    check("T5.5 Verify with correct kid succeeds", ok)
    ok, msg = jose.verify("kid-wrong")
    check("T5.6 Verify with wrong kid fails", not ok)
    check("T5.7 Signature is hex string", isinstance(jose.signature, str) and len(jose.signature) == 64)

    # ── T6: Witness Request ──────────────────────────────────────
    print("T6: Witness Request")
    req = WitnessRequest(
        requester="did:web4:key:z6MkReq1",
        witness_type=WitnessClass.TIME,
        target="lct:web4:test:abc123",
        nonce="mb32:nonce1",
        claims_requested=["ts", "accuracy"],
        event_hash="deadbeef",
    )
    d = req.to_dict()
    check("T6.1 Request has type field", d["type"] == "WitnessRequest")
    check("T6.2 Request has requester", d["requester"] == "did:web4:key:z6MkReq1")
    check("T6.3 Request has witness_type", d["witness_type"] == "time")
    check("T6.4 Request has target", d["target"] == "lct:web4:test:abc123")
    check("T6.5 Request has nonce", d["nonce"] == "mb32:nonce1")
    check("T6.6 Request has claims_requested", d["claims_requested"] == ["ts", "accuracy"])
    check("T6.7 Request has event_hash", d["event_hash"] == "deadbeef")

    # ── T7: Replay Guard ────────────────────────────────────────
    print("T7: Replay Guard")
    guard = WitnessReplayGuard()
    ok, _ = guard.check_nonce("nonce-1")
    check("T7.1 First nonce accepted", ok)
    ok, msg = guard.check_nonce("nonce-1")
    check("T7.2 Duplicate nonce rejected", not ok)
    check("T7.3 Rejection mentions 'already used'", "already used" in msg)
    ok, _ = guard.check_nonce("nonce-2")
    check("T7.4 Different nonce accepted", ok)

    # Freshness checks
    ok, _ = guard.check_freshness(now_iso)
    check("T7.5 Current timestamp passes", ok)
    old_ts = "2020-01-01T00:00:00Z"
    ok, msg = guard.check_freshness(old_ts)
    check("T7.6 Old timestamp rejected", not ok)
    check("T7.7 Rejection mentions window", "window" in msg.lower() or "300" in msg)

    # ── T8: Witness Discovery ───────────────────────────────────
    print("T8: Witness Discovery")
    disc = WitnessDiscovery()
    w1 = WitnessInfo(did="did:web4:key:w1", classes=[WitnessClass.TIME, WitnessClass.EXISTENCE],
                     key_id="kid-w1", reputation=0.8, last_seen=time.time(), operator="op-A")
    w2 = WitnessInfo(did="did:web4:key:w2", classes=[WitnessClass.TIME, WitnessClass.AUDIT],
                     key_id="kid-w2", reputation=0.6, last_seen=time.time(), operator="op-B")
    w3 = WitnessInfo(did="did:web4:key:w3", classes=[WitnessClass.TIME],
                     key_id="kid-w3", reputation=0.4, last_seen=time.time(), operator="op-A")
    disc.add_bootstrap(w1)
    disc.add_bootstrap(w2)
    disc.add_bootstrap(w3)

    time_witnesses = disc.find_witnesses(WitnessClass.TIME)
    check("T8.1 Find 3 time witnesses", len(time_witnesses) == 3)
    check("T8.2 Sorted by reputation (highest first)", time_witnesses[0].reputation >= time_witnesses[1].reputation)
    audit_witnesses = disc.find_witnesses(WitnessClass.AUDIT)
    check("T8.3 Find 1 audit witness", len(audit_witnesses) == 1)
    check("T8.4 Audit witness is w2", audit_witnesses[0].did == "did:web4:key:w2")

    diverse = disc.find_witnesses(WitnessClass.TIME, require_diversity=True)
    check("T8.5 Diversity filters to 2 operators", len(diverse) == 2)

    w4 = WitnessInfo(did="did:web4:key:w4", classes=[WitnessClass.ORACLE],
                     key_id="kid-w4", reputation=0.7, last_seen=time.time())
    disc.add_peer_recommendation(w4, recommender_trust=0.5)
    check("T8.6 Peer recommendation caps reputation", w4.reputation <= 0.5)

    w5 = WitnessInfo(did="did:web4:key:w5", classes=[WitnessClass.QUALITY],
                     key_id="kid-w5", reputation=0.9, last_seen=time.time())
    disc.add_broadcast(w5)
    check("T8.7 Broadcast witness capped at 0.3", w5.reputation <= 0.3)
    check("T8.8 All witnesses in registry", len(disc.get_all()) == 5)

    low_rep = disc.find_witnesses(WitnessClass.QUALITY, min_reputation=0.5)
    check("T8.9 Reputation filter excludes low-rep broadcast", len(low_rep) == 0)

    # ── T9: Witness Quorum ──────────────────────────────────────
    print("T9: Witness Quorum")
    quorum = WitnessQuorum(QuorumPolicy.TWO_OF_THREE)
    check("T9.1 2-of-3: requires 2 from 3", quorum.required_count(3) == 2)
    check("T9.2 2-of-3: requires 2 from 2", quorum.required_count(2) == 2)
    check("T9.3 2-of-3: requires 4 from 5", quorum.required_count(5) == 4)

    quorum_byz = WitnessQuorum(QuorumPolicy.BYZANTINE)
    check("T9.4 Byzantine: requires 2 from 3", quorum_byz.required_count(3) == 2)

    quorum_unan = WitnessQuorum(QuorumPolicy.UNANIMOUS)
    check("T9.5 Unanimous: requires all", quorum_unan.required_count(5) == 5)

    quorum_maj = WitnessQuorum(QuorumPolicy.SIMPLE_MAJORITY)
    check("T9.6 Majority: requires 3 from 5", quorum_maj.required_count(5) == 3)
    check("T9.7 Majority: requires 2 from 3", quorum_maj.required_count(3) == 2)

    # Quorum verification with attestations
    atts = [
        WitnessAttestation("did:web4:key:w1", WitnessClass.TIME,
                           {"ts": now_iso, "nonce": "n1"}, "cose:s1", now_iso, "nonce-q1"),
        WitnessAttestation("did:web4:key:w2", WitnessClass.TIME,
                           {"ts": now_iso, "nonce": "n2"}, "cose:s2", now_iso, "nonce-q2"),
    ]
    guard2 = WitnessReplayGuard()
    result = quorum.verify_quorum(atts, total_witnesses=3, replay_guard=guard2)
    check("T9.8 Quorum met with 2/3", result.met)
    check("T9.9 Required is 2", result.required == 2)
    check("T9.10 Valid count is 2", result.valid == 2)

    # Single attestation doesn't meet quorum
    result2 = quorum.verify_quorum(atts[:1], total_witnesses=3, replay_guard=WitnessReplayGuard())
    check("T9.11 Quorum not met with 1/3", not result2.met)

    # Invalid claims fail quorum
    bad_atts = [
        WitnessAttestation("did:web4:key:w1", WitnessClass.TIME,
                           {}, "cose:s1", now_iso, "nonce-bad1"),
    ]
    result3 = quorum.verify_quorum(bad_atts, total_witnesses=1, replay_guard=WitnessReplayGuard())
    check("T9.12 Invalid claims don't count", result3.valid == 0)
    check("T9.13 Invalid count tracked", result3.invalid == 1)

    # Diversity check
    disc2 = WitnessDiscovery()
    disc2.add_bootstrap(WitnessInfo("did:web4:key:w1", [WitnessClass.TIME], "k1",
                                     operator="op-A", last_seen=time.time()))
    disc2.add_bootstrap(WitnessInfo("did:web4:key:w2", [WitnessClass.TIME], "k2",
                                     operator="op-B", last_seen=time.time()))
    ok, msg = quorum.check_diversity(atts, disc2)
    check("T9.14 Diversity check passes with 2 operators", ok)

    same_op_atts = [
        WitnessAttestation("did:web4:key:w1", WitnessClass.TIME,
                           {"ts": now_iso, "nonce": "n1"}, "cose:s1", now_iso, "nonce-div1"),
    ]
    disc3 = WitnessDiscovery()
    disc3.add_bootstrap(WitnessInfo("did:web4:key:w1", [WitnessClass.TIME], "k1",
                                     operator="op-A", last_seen=time.time()))
    ok, _ = quorum.check_diversity(same_op_atts, disc3)
    check("T9.15 Diversity fails with 1 operator", not ok)

    # ── T10: Witness Incentives ──────────────────────────────────
    print("T10: Witness Incentives")
    incentives = WitnessIncentiveTracker()
    incentives.reward_attestation("did:web4:key:w1", WitnessClass.TIME)
    check("T10.1 Time attestation earns 1 ATP", incentives.get_balance("did:web4:key:w1") == 1.0)

    incentives.reward_attestation("did:web4:key:w1", WitnessClass.AUDIT)
    check("T10.2 Audit earns 10 ATP (total 11)", incentives.get_balance("did:web4:key:w1") == 11.0)

    incentives.reward_attestation("did:web4:key:w1", WitnessClass.ORACLE)
    check("T10.3 Oracle earns 5 ATP (total 16)", incentives.get_balance("did:web4:key:w1") == 16.0)

    incentives.penalize("did:web4:key:w1", "invalid claims")
    check("T10.4 Penalty reduces balance (14)", incentives.get_balance("did:web4:key:w1") == 14.0)

    check("T10.5 Total earned is 16", incentives.get_total_earned() == 16.0)
    check("T10.6 Total penalties is 2", incentives.get_total_penalties() == 2.0)

    incentives.penalize("did:web4:key:w2", "timeout")
    check("T10.7 New witness starts at penalty", incentives.get_balance("did:web4:key:w2") == -2.0)

    # ── T11: Witness Reputation ──────────────────────────────────
    print("T11: Witness Reputation")
    rep_tracker = WitnessReputationTracker()
    rep_tracker.record_attestation("did:web4:key:w1", WitnessClass.TIME, True)
    rep_tracker.record_attestation("did:web4:key:w1", WitnessClass.TIME, True)
    rep_tracker.record_attestation("did:web4:key:w1", WitnessClass.TIME, False)

    rep = rep_tracker.get_or_create("did:web4:key:w1")
    check("T11.1 Total attestations is 3", rep.total_attestations == 3)
    check("T11.2 Valid is 2", rep.valid_attestations == 2)
    check("T11.3 Invalid is 1", rep.invalid_attestations == 1)
    check("T11.4 Accuracy is 2/3", abs(rep.accuracy - 2/3) < 0.001)

    rep_tracker.record_attestation("did:web4:key:w1", WitnessClass.AUDIT, True)
    rep_tracker.record_attestation("did:web4:key:w1", WitnessClass.ORACLE, True)
    check("T11.5 Diversity is 3/8", abs(rep.diversity - 3/8) < 0.001)
    check("T11.6 Classes served", WitnessClass.TIME in rep.classes_served)
    check("T11.7 Audit class served", WitnessClass.AUDIT in rep.classes_served)

    rep_tracker.record_availability("did:web4:key:w1", True)
    check("T11.8 Availability updated", rep.availability > 0.5)

    composite = rep_tracker.get_composite("did:web4:key:w1")
    check("T11.9 Composite score > 0", composite > 0)
    check("T11.10 Composite score < 1", composite < 1)

    # New witness starts at defaults
    rep2 = rep_tracker.get_or_create("did:web4:key:new")
    check("T11.11 New witness accuracy=0.5", rep2.accuracy == 0.5)
    check("T11.12 New witness availability=0.5", rep2.availability == 0.5)

    # ── T12: WitnessManager Lifecycle ────────────────────────────
    print("T12: WitnessManager Lifecycle")
    mgr = WitnessManager()
    w_info = WitnessInfo(
        did="did:web4:key:z6MkManager1",
        classes=[WitnessClass.TIME, WitnessClass.EXISTENCE, WitnessClass.AUDIT],
        key_id="kid-mgr-1",
        reputation=0.9,
        last_seen=time.time(),
        operator="op-main",
    )
    mgr.register_witness(w_info)
    check("T12.1 Witness registered", len(mgr.discovery.get_all()) == 1)

    req = WitnessRequest(
        requester="did:web4:key:z6MkAlice",
        witness_type=WitnessClass.TIME,
        target="lct:web4:ai:alice123",
        nonce="mb32:mgr-nonce-1",
        claims_requested=["ts", "accuracy"],
    )
    att = mgr.request_attestation(req, "did:web4:key:z6MkManager1")
    check("T12.2 Attestation created", att is not None)
    check("T12.3 Attestation has correct witness", att.witness == "did:web4:key:z6MkManager1")
    check("T12.4 Attestation has correct type", att.type == WitnessClass.TIME)
    check("T12.5 Claims have ts", "ts" in att.claims)
    check("T12.6 Claims have nonce", "nonce" in att.claims)

    # Submit attestation
    ok, msg = mgr.submit_attestation(att)
    check("T12.7 Attestation submitted successfully", ok)
    check("T12.8 Attestation in log", len(mgr.get_attestation_log()) == 1)

    # Incentive check (before replay test which penalizes)
    balance = mgr.incentives.get_balance("did:web4:key:z6MkManager1")
    check("T12.9 Witness earned ATP from valid attestation", balance > 0)

    # Reputation check
    comp = mgr.reputation.get_composite("did:web4:key:z6MkManager1")
    check("T12.10 Witness has reputation > 0", comp > 0)

    # Replay prevention
    att_copy = WitnessAttestation(
        att.witness, att.type, att.claims, att.sig, att.ts, att.nonce
    )
    ok2, msg2 = mgr.submit_attestation(att_copy)
    check("T12.11 Duplicate nonce rejected", not ok2)

    # Request for unsupported class
    req_bad = WitnessRequest(
        requester="did:web4:key:z6MkAlice",
        witness_type=WitnessClass.QUALITY,  # Not in w_info.classes
        target="lct:web4:ai:alice123",
        nonce="mb32:mgr-nonce-2",
        claims_requested=["metric", "value"],
    )
    att_bad = mgr.request_attestation(req_bad, "did:web4:key:z6MkManager1")
    check("T12.12 Unsupported class returns None", att_bad is None)

    # Request for unknown witness
    att_unknown = mgr.request_attestation(req, "did:web4:key:z6MkUnknown")
    check("T12.13 Unknown witness returns None", att_unknown is None)

    # ── T13: Multi-Witness Quorum Scenario ───────────────────────
    print("T13: Multi-Witness Quorum Scenario")
    mgr2 = WitnessManager()
    witnesses = []
    for i in range(5):
        wi = WitnessInfo(
            did=f"did:web4:key:z6MkQuorum{i}",
            classes=[WitnessClass.TIME, WitnessClass.EXISTENCE],
            key_id=f"kid-q{i}",
            reputation=0.7 + i * 0.05,
            last_seen=time.time(),
            operator=f"op-{i}",
        )
        mgr2.register_witness(wi)
        witnesses.append(wi)

    # Collect attestations from 3 witnesses
    attestations = []
    for i in range(3):
        req = WitnessRequest(
            requester="did:web4:key:z6MkBob",
            witness_type=WitnessClass.TIME,
            target="lct:web4:human:bob456",
            nonce=f"mb32:quorum-n{i}",
            claims_requested=["ts"],
        )
        att = mgr2.request_attestation(req, witnesses[i].did)
        if att:
            attestations.append(att)

    check("T13.1 Got 3 attestations", len(attestations) == 3)
    # 2-of-3 policy with 3 total witnesses requires 2; we have 3 → quorum met
    result = mgr2.quorum.verify_quorum(attestations, total_witnesses=3,
                                        replay_guard=WitnessReplayGuard())
    check("T13.2 Quorum met (3/3 with 2-of-3 policy)", result.met)
    check("T13.3 All valid", result.valid == 3)
    check("T13.4 None invalid", result.invalid == 0)

    # Submit all and check incentives
    for att in attestations:
        mgr2.submit_attestation(att)

    total_earned = mgr2.incentives.get_total_earned()
    check("T13.5 Total earned = 3 ATP (3 time attestations)", total_earned == 3.0)

    # ── T14: MRH Witness Tracking ────────────────────────────────
    print("T14: MRH Witness Tracking")
    mrh = MRHWitnessTracker()
    mrh.record_witness("lct:web4:ai:alice", "lct:web4:oracle:timestamp",
                       WitnessClass.TIME, now_iso)
    mrh.record_witness("lct:web4:ai:alice", "lct:web4:oracle:timestamp",
                       WitnessClass.TIME, now_iso)
    mrh.record_witness("lct:web4:ai:alice", "lct:web4:audit:compliance",
                       WitnessClass.AUDIT, now_iso)

    entries = mrh.get_witnesses("lct:web4:ai:alice")
    check("T14.1 Two distinct witness entries", len(entries) == 2)

    time_entry = [e for e in entries if e.role == WitnessClass.TIME][0]
    check("T14.2 Time witness count is 2", time_entry.witness_count == 2)

    total = mrh.get_witness_count("lct:web4:ai:alice")
    check("T14.3 Total witness count is 3", total == 3)

    unique = mrh.get_unique_witness_count("lct:web4:ai:alice")
    check("T14.4 Unique witness count is 2", unique == 2)

    check("T14.5 Unknown entity has 0 witnesses", mrh.get_witness_count("lct:web4:unknown") == 0)

    entries_dict = [e.to_dict() for e in entries]
    check("T14.6 Entries serializable", all("lct_id" in e for e in entries_dict))
    check("T14.7 Entries have role", all("role" in e for e in entries_dict))

    # ── T15: Evidence Types ──────────────────────────────────────
    print("T15: Evidence Types")
    check("T15.1 Four evidence types", len(EvidenceType) == 4)
    check("T15.2 EXISTENCE type", EvidenceType.EXISTENCE.value == "EXISTENCE")
    check("T15.3 ACTION type", EvidenceType.ACTION.value == "ACTION")
    check("T15.4 STATE type", EvidenceType.STATE.value == "STATE")
    check("T15.5 TRANSITION type", EvidenceType.TRANSITION.value == "TRANSITION")

    evidence = WitnessEvidence(
        evidence_type=EvidenceType.ACTION,
        observer_lct="lct:web4:oracle:audit1",
        observed_lct="lct:web4:ai:alice",
        evidence_data={"action": "r6:execute", "quality": "high"},
        signature="cose:evid_sig",
        timestamp=now_iso,
    )
    d = evidence.to_dict()
    check("T15.6 Evidence has version WTNS/1.0", d["version"] == "WTNS/1.0")
    check("T15.7 Evidence has evidence_type", d["evidence_type"] == "ACTION")
    check("T15.8 Evidence has observer", d["observer_lct"] == "lct:web4:oracle:audit1")
    check("T15.9 Evidence has observed", d["observed_lct"] == "lct:web4:ai:alice")
    check("T15.10 Evidence has data", "action" in d["evidence_data"])

    # ── T16: All 8 Witness Classes Attestation ───────────────────
    print("T16: All 8 Witness Classes Attestation")
    mgr3 = WitnessManager()
    all_class_witness = WitnessInfo(
        did="did:web4:key:z6MkAllClass",
        classes=list(WitnessClass),
        key_id="kid-all",
        reputation=0.95,
        last_seen=time.time(),
        operator="op-universal",
    )
    mgr3.register_witness(all_class_witness)

    for i, wc in enumerate(WitnessClass):
        req = WitnessRequest(
            requester="did:web4:key:z6MkTest",
            witness_type=wc,
            target=f"lct:web4:test:{wc.value}",
            nonce=f"mb32:allclass-{i}",
            claims_requested=REQUIRED_CLAIMS[wc],
        )
        att = mgr3.request_attestation(req, all_class_witness.did)
        check(f"T16.{i+1} {wc.value} attestation created", att is not None)
        if att:
            ok, msg = mgr3.submit_attestation(att)
            check(f"T16.{i+9} {wc.value} attestation valid", ok)

    check("T16.17 All 8 classes in log", len(mgr3.get_attestation_log()) == 8)
    check("T16.18 All 8 classes earned ATP", mgr3.incentives.get_total_earned() > 0)

    # ── T17: Edge Cases ──────────────────────────────────────────
    print("T17: Edge Cases")

    # Empty claims
    ok, errs = validate_claims(WitnessClass.TIME, {})
    check("T17.1 Empty claims fail for time", not ok)
    check("T17.2 Two errors for time (ts, nonce)", len(errs) == 2)

    # Extra claims are allowed (open-ended)
    ok, errs = validate_claims(WitnessClass.TIME, {"ts": now_iso, "nonce": "n", "extra": "ok"})
    check("T17.3 Extra claims allowed", ok)

    # Witness with no classes
    empty_witness = WitnessInfo(
        did="did:web4:key:z6MkEmpty", classes=[], key_id="kid-empty",
        reputation=0.5, last_seen=time.time()
    )
    mgr.register_witness(empty_witness)
    att_empty = mgr.request_attestation(
        WitnessRequest("did:web4:key:req", WitnessClass.TIME,
                       "lct:web4:test:x", "mb32:e1", ["ts"]),
        "did:web4:key:z6MkEmpty"
    )
    check("T17.4 No-class witness returns None", att_empty is None)

    # Stale witness (last_seen long ago)
    stale = WitnessInfo(
        did="did:web4:key:z6MkStale", classes=[WitnessClass.TIME],
        key_id="kid-stale", reputation=0.9, last_seen=0.0  # epoch
    )
    check("T17.5 Stale witness not available", not stale.is_available())

    # Quorum with 0 attestations
    result_zero = mgr.quorum.verify_quorum([], total_witnesses=3)
    check("T17.6 Zero attestations = quorum not met", not result_zero.met)

    # Single witness quorum (degenerate case)
    q_single = WitnessQuorum(QuorumPolicy.TWO_OF_THREE)
    check("T17.7 Required from 1 witness is 2 (can't be met)", q_single.required_count(1) == 2)

    # Attestation hash stability
    att1 = WitnessAttestation("w1", WitnessClass.TIME, {"ts": "t1", "nonce": "n1"},
                              "cose:s1", "t1", "n1")
    att2 = WitnessAttestation("w1", WitnessClass.TIME, {"ts": "t1", "nonce": "n1"},
                              "cose:s1", "t1", "n1")
    check("T17.8 Same attestation = same hash", att1.hash() == att2.hash())

    att3 = WitnessAttestation("w2", WitnessClass.TIME, {"ts": "t1", "nonce": "n1"},
                              "cose:s1", "t1", "n1")
    check("T17.9 Different witness = different hash", att1.hash() != att3.hash())

    # ── T18: Incentive Schedule Customization ────────────────────
    print("T18: Incentive Schedule Customization")
    custom_schedule = WitnessIncentiveSchedule(
        attestation_reward=2.0,
        audit_reward=20.0,
        oracle_reward=10.0,
        penalty_invalid=-5.0,
    )
    tracker = WitnessIncentiveTracker(custom_schedule)
    tracker.reward_attestation("w1", WitnessClass.TIME)
    check("T18.1 Custom time reward = 2 ATP", tracker.get_balance("w1") == 2.0)
    tracker.reward_attestation("w1", WitnessClass.AUDIT)
    check("T18.2 Custom audit reward = 22 ATP", tracker.get_balance("w1") == 22.0)
    tracker.penalize("w1", "bad")
    check("T18.3 Custom penalty = 17 ATP", tracker.get_balance("w1") == 17.0)

    # ── T19: Witness Reputation Composite Weights ────────────────
    print("T19: Witness Reputation Composite")
    rep = WitnessReputation(accuracy=1.0, availability=1.0, diversity=1.0)
    check("T19.1 Perfect reputation = 1.0", abs(rep.composite - 1.0) < 0.001)

    rep2 = WitnessReputation(accuracy=0.0, availability=0.0, diversity=0.0)
    check("T19.2 Zero reputation = 0.0", abs(rep2.composite - 0.0) < 0.001)

    rep3 = WitnessReputation(accuracy=0.8, availability=0.6, diversity=0.4)
    expected = 0.8 * 0.5 + 0.6 * 0.3 + 0.4 * 0.2
    check("T19.3 Weighted composite correct", abs(rep3.composite - expected) < 0.001)

    # Accuracy dominates (0.5 weight)
    rep4 = WitnessReputation(accuracy=1.0, availability=0.0, diversity=0.0)
    check("T19.4 Accuracy alone = 0.5", abs(rep4.composite - 0.5) < 0.001)

    # ── T20: Full End-to-End Scenario ────────────────────────────
    print("T20: Full End-to-End Scenario")
    e2e = WitnessManager()
    mrh_tracker = MRHWitnessTracker()

    # Register 3 witnesses from different operators
    for i in range(3):
        wi = WitnessInfo(
            did=f"did:web4:key:z6MkE2E{i}",
            classes=[WitnessClass.TIME, WitnessClass.EXISTENCE, WitnessClass.AUDIT],
            key_id=f"kid-e2e-{i}",
            reputation=0.7 + i * 0.1,
            last_seen=time.time(),
            operator=f"e2e-op-{i}",
        )
        e2e.register_witness(wi)

    target_lct = "lct:web4:ai:e2e-agent-123"

    # Phase 1: Collect attestations from all 3 witnesses
    all_atts = []
    for i in range(3):
        req = WitnessRequest(
            requester="did:web4:key:z6MkAgent",
            witness_type=WitnessClass.EXISTENCE,
            target=target_lct,
            nonce=f"mb32:e2e-{i}",
            claims_requested=["observed_at", "method"],
        )
        att = e2e.request_attestation(req, f"did:web4:key:z6MkE2E{i}")
        if att:
            ok, _ = e2e.submit_attestation(att)
            if ok:
                all_atts.append(att)
                mrh_tracker.record_witness(
                    target_lct, f"lct:web4:oracle:e2e-{i}",
                    WitnessClass.EXISTENCE, att.ts
                )

    check("T20.1 All 3 attestations collected", len(all_atts) == 3)

    # Phase 2: Verify quorum
    result = e2e.quorum.verify_quorum(all_atts, total_witnesses=3,
                                       replay_guard=WitnessReplayGuard())
    check("T20.2 Quorum met", result.met)

    # Phase 3: Check diversity
    ok, msg = e2e.quorum.check_diversity(all_atts, e2e.discovery)
    check("T20.3 Diversity satisfied", ok)

    # Phase 4: Verify MRH updated
    mrh_entries = mrh_tracker.get_witnesses(target_lct)
    check("T20.4 MRH has 3 witness entries", len(mrh_entries) == 3)
    check("T20.5 Total witness count is 3", mrh_tracker.get_witness_count(target_lct) == 3)

    # Phase 5: Check incentives
    total = e2e.incentives.get_total_earned()
    check("T20.6 Total earned = 3 ATP (3 existence attestations)", total == 3.0)

    # Phase 6: Reputation should be updated
    for i in range(3):
        comp = e2e.reputation.get_composite(f"did:web4:key:z6MkE2E{i}")
        check(f"T20.{7+i} Witness {i} reputation > 0", comp > 0)

    # Phase 7: Attestation log integrity
    log = e2e.get_attestation_log()
    check("T20.10 Log has 3 entries", len(log) == 3)
    hashes = [a.hash() for a in log]
    check("T20.11 All hashes unique", len(set(hashes)) == 3)

    # ── Summary ──────────────────────────────────────────────────
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"Witness Protocol Unified: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  FAILED: {failed}")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
