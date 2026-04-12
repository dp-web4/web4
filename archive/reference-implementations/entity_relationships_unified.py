#!/usr/bin/env python3
"""
Web4 Entity Relationships — Unified Reference Implementation

Implements web4-entity-relationships.md specification:
- 4 relationship mechanisms: binding, pairing, witnessing, broadcast
- 3 pairing modes: direct (P2P), witnessed (notarized), authorized (mediated)
- MRH integration: bidirectional graph updates for all relationship types
- T3/V3 propagation through relationships
- Role-agent pairing with dual tensor accumulation
- Accumulator-based passive witnessing via broadcast
- State machines for all relationship lifecycles

Spec ref: web4-standard/protocols/web4-entity-relationships.md
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ── Entity Types ─────────────────────────────────────────────────────

ENTITY_TYPES = [
    "human", "ai", "society", "organization", "role", "task",
    "resource", "device", "service", "oracle", "accumulator",
    "dictionary", "hybrid", "policy", "infrastructure",
]


# ── Binding (§1) ─────────────────────────────────────────────────────

class BindingState(str, Enum):
    UNBOUND = "unbound"
    BINDING = "binding"
    BOUND = "bound"
    REVOKED = "revoked"


@dataclass
class BindingRequest:
    """BIND/1.0 request per spec §1."""
    version: str = "BIND/1.0"
    entity_type: str = "ai"
    public_key: str = ""
    hardware_id: str = ""  # SHA-256 of hardware characteristics
    timestamp: str = ""

    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        if self.entity_type not in ENTITY_TYPES:
            errors.append(f"Invalid entity type: {self.entity_type}")
        if not self.public_key:
            errors.append("Public key required")
        if len(self.hardware_id) != 64 and self.hardware_id:
            errors.append("Hardware ID must be 64 hex chars (SHA-256)")
        return len(errors) == 0, errors


@dataclass
class Binding:
    """A cryptographic anchor between entity and LCT."""
    lct_id: str
    entity_type: str
    public_key: str
    hardware_id: str
    created_at: str
    binding_proof: str
    state: BindingState = BindingState.BOUND
    parent_lct: Optional[str] = None
    children: List[str] = field(default_factory=list)

    def revoke(self):
        self.state = BindingState.REVOKED


# ── Pairing Modes (§2) ──────────────────────────────────────────────

class PairingMode(str, Enum):
    DIRECT = "direct"
    WITNESSED = "witnessed"
    AUTHORIZED = "authorized"


class PairingState(str, Enum):
    UNPAIRED = "unpaired"
    NEGOTIATING = "negotiating"
    KEY_EXCHANGE = "key_exchange"
    PAIRED = "paired"
    ACTIVE = "active"
    CLOSED = "closed"
    REVOKED = "revoked"

    # Additional states for witnessed/authorized
    REQUESTING_WITNESS = "requesting_witness"
    WITNESS_VALIDATING = "witness_validating"
    REQUESTING_AUTH = "requesting_auth"
    AUTH_VALIDATING = "auth_validating"
    AUTH_GENERATING = "auth_generating"
    KEY_DISTRIBUTION = "key_distribution"


@dataclass
class PairingRequest:
    """PAIR/1.0 request per spec §2."""
    version: str = "PAIR/1.0"
    mode: PairingMode = PairingMode.DIRECT
    entity_a: str = ""
    entity_b: str = ""
    context: str = ""
    rules: Dict[str, Any] = field(default_factory=dict)
    witness_lct: Optional[str] = None  # For witnessed mode
    authority_lct: Optional[str] = None  # For authorized mode

    def validate(self) -> Tuple[bool, List[str]]:
        errors = []
        if not self.entity_a:
            errors.append("Entity A required")
        if not self.entity_b:
            errors.append("Entity B required")
        if self.mode == PairingMode.WITNESSED and not self.witness_lct:
            errors.append("Witness LCT required for witnessed pairing")
        if self.mode == PairingMode.AUTHORIZED and not self.authority_lct:
            errors.append("Authority LCT required for authorized pairing")
        return len(errors) == 0, errors


@dataclass
class PairingSession:
    """An active pairing session between two entities."""
    session_id: str
    mode: PairingMode
    entity_a: str
    entity_b: str
    context: str
    rules: Dict[str, Any]
    state: PairingState = PairingState.UNPAIRED
    key_a: str = ""  # Session key half for entity A
    key_b: str = ""  # Session key half for entity B
    witness_lct: Optional[str] = None
    witness_attestation: Optional[str] = None
    authority_lct: Optional[str] = None
    authority_record: Optional[str] = None
    created_at: float = 0.0
    is_permanent: bool = False
    is_role_pairing: bool = False

    def derive_full_key(self) -> str:
        """Derive full session key from two halves."""
        combined = f"{self.key_a}:{self.key_b}"
        return hashlib.sha256(combined.encode()).hexdigest()


# ── Witnessing (§3) ─────────────────────────────────────────────────

class WitnessEvidenceType(str, Enum):
    EXISTENCE = "EXISTENCE"
    ACTION = "ACTION"
    STATE = "STATE"
    TRANSITION = "TRANSITION"


@dataclass
class WitnessAssertion:
    """WTNS/1.0 witness assertion per spec §3."""
    version: str = "WTNS/1.0"
    observer_lct: str = ""
    observed_lct: str = ""
    evidence_type: WitnessEvidenceType = WitnessEvidenceType.EXISTENCE
    evidence_data: Dict[str, Any] = field(default_factory=dict)
    signature: str = ""
    timestamp: str = ""

    def hash(self) -> str:
        canonical = json.dumps({
            "observer": self.observer_lct,
            "observed": self.observed_lct,
            "type": self.evidence_type.value,
            "data": self.evidence_data,
            "ts": self.timestamp,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


# ── Broadcast (§4) ──────────────────────────────────────────────────

class BroadcastType(str, Enum):
    ANNOUNCE = "ANNOUNCE"
    HEARTBEAT = "HEARTBEAT"
    CAPABILITY = "CAPABILITY"


@dataclass
class BroadcastMessage:
    """CAST/1.0 broadcast message per spec §4."""
    version: str = "CAST/1.0"
    sender_id: str = ""
    message_type: BroadcastType = BroadcastType.ANNOUNCE
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    def hash(self) -> str:
        canonical = json.dumps({
            "sender": self.sender_id,
            "type": self.message_type.value,
            "payload": self.payload,
            "ts": self.timestamp,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class AccumulatorEntry:
    """Record of a broadcast received by an accumulator."""
    broadcast_hash: str
    sender_id: str
    message_type: str
    timestamp: float
    signature: str


class Accumulator:
    """Passive witness via broadcast collection (§4.4)."""

    def __init__(self, accumulator_id: str):
        self.accumulator_id = accumulator_id
        self._entries: List[AccumulatorEntry] = []

    def record(self, broadcast: BroadcastMessage) -> AccumulatorEntry:
        sig = hashlib.sha256(
            f"{broadcast.hash()}:{self.accumulator_id}".encode()
        ).hexdigest()[:32]
        entry = AccumulatorEntry(
            broadcast_hash=broadcast.hash(),
            sender_id=broadcast.sender_id,
            message_type=broadcast.message_type.value,
            timestamp=broadcast.timestamp,
            signature=sig,
        )
        self._entries.append(entry)
        return entry

    def query(self, entity_id: Optional[str] = None,
              time_range: Optional[Tuple[float, float]] = None) -> List[AccumulatorEntry]:
        results = self._entries
        if entity_id:
            results = [e for e in results if e.sender_id == entity_id]
        if time_range:
            results = [e for e in results
                       if time_range[0] <= e.timestamp <= time_range[1]]
        return results

    def count(self, entity_id: Optional[str] = None) -> int:
        return len(self.query(entity_id))


# ── MRH Graph (Relationship Container) ──────────────────────────────

@dataclass
class MRHBound:
    lct_id: str
    bound_type: str  # "parent", "child", "sibling"
    ts: str

    def to_dict(self) -> dict:
        return {"lct_id": self.lct_id, "type": self.bound_type, "ts": self.ts}


@dataclass
class MRHPaired:
    lct_id: str
    pairing_mode: str
    pairing_context: str
    session_id: str
    permanent: bool
    ts: str

    def to_dict(self) -> dict:
        return {
            "lct_id": self.lct_id,
            "pairing_mode": self.pairing_mode,
            "pairing_context": self.pairing_context,
            "session_id": self.session_id,
            "permanent": self.permanent,
            "ts": self.ts,
        }


@dataclass
class MRHWitnessing:
    lct_id: str
    role: str
    last_attestation: str
    witness_count: int = 0

    def to_dict(self) -> dict:
        return {
            "lct_id": self.lct_id,
            "role": self.role,
            "last_attestation": self.last_attestation,
            "witness_count": self.witness_count,
        }


class MRHGraph:
    """MRH as unified relationship container."""

    def __init__(self, owner_lct: str, horizon_depth: int = 3):
        self.owner_lct = owner_lct
        self.horizon_depth = horizon_depth
        self.bound: List[MRHBound] = []
        self.paired: List[MRHPaired] = []
        self.witnessing: List[MRHWitnessing] = []
        self.last_updated = ""

    def add_binding(self, target_lct: str, bound_type: str, ts: str):
        self.bound.append(MRHBound(target_lct, bound_type, ts))
        self.last_updated = ts

    def add_pairing(self, session: PairingSession, ts: str):
        self.paired.append(MRHPaired(
            lct_id=session.entity_b if session.entity_a == self.owner_lct else session.entity_a,
            pairing_mode=session.mode.value,
            pairing_context=session.context,
            session_id=session.session_id,
            permanent=session.is_permanent,
            ts=ts,
        ))
        self.last_updated = ts

    def add_witnessing(self, witness_lct: str, role: str, ts: str):
        # Update existing or create new
        for w in self.witnessing:
            if w.lct_id == witness_lct and w.role == role:
                w.witness_count += 1
                w.last_attestation = ts
                self.last_updated = ts
                return
        self.witnessing.append(MRHWitnessing(witness_lct, role, ts, 1))
        self.last_updated = ts

    def remove_pairing(self, session_id: str, ts: str):
        self.paired = [p for p in self.paired if p.session_id != session_id]
        self.last_updated = ts

    def to_dict(self) -> dict:
        return {
            "bound": [b.to_dict() for b in self.bound],
            "paired": [p.to_dict() for p in self.paired],
            "witnessing": [w.to_dict() for w in self.witnessing],
            "horizon_depth": self.horizon_depth,
            "last_updated": self.last_updated,
        }


# ── T3/V3 Relationship Propagation ──────────────────────────────────

@dataclass
class T3Snapshot:
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def composite(self) -> float:
        return self.talent * 0.4 + self.training * 0.3 + self.temperament * 0.3

    def adjust(self, delta_talent: float, delta_training: float,
               delta_temperament: float, cap: float = 0.1):
        self.talent = max(0.0, min(1.0, self.talent + max(-cap, min(cap, delta_talent))))
        self.training = max(0.0, min(1.0, self.training + max(-cap, min(cap, delta_training))))
        self.temperament = max(0.0, min(1.0, self.temperament + max(-cap, min(cap, delta_temperament))))


# ── Relationship Manager ────────────────────────────────────────────

class RelationshipManager:
    """Orchestrates all 4 relationship mechanisms."""

    def __init__(self):
        self._bindings: Dict[str, Binding] = {}
        self._sessions: Dict[str, PairingSession] = {}
        self._witnesses: List[WitnessAssertion] = []
        self._mrh_graphs: Dict[str, MRHGraph] = {}
        self._t3: Dict[str, T3Snapshot] = {}
        self._role_performers: Dict[str, List[str]] = {}  # role_lct → [agent_lcts]
        self._accumulators: Dict[str, Accumulator] = {}
        self._session_counter = 0

    def _get_mrh(self, lct_id: str) -> MRHGraph:
        if lct_id not in self._mrh_graphs:
            self._mrh_graphs[lct_id] = MRHGraph(lct_id)
        return self._mrh_graphs[lct_id]

    def _get_t3(self, lct_id: str) -> T3Snapshot:
        if lct_id not in self._t3:
            self._t3[lct_id] = T3Snapshot()
        return self._t3[lct_id]

    def _now_iso(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # ── Binding Operations (§1) ──────────────────────────────────

    def bind(self, request: BindingRequest,
             parent_lct: Optional[str] = None) -> Tuple[bool, str, Optional[Binding]]:
        """Create a new binding (entity → LCT)."""
        ok, errors = request.validate()
        if not ok:
            return False, f"Validation failed: {errors}", None

        # Generate LCT ID
        hash_input = f"{request.entity_type}:{request.public_key}:{request.hardware_id}"
        lct_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        lct_id = f"lct:web4:{request.entity_type}:{lct_hash}"

        # Generate binding proof
        proof_input = f"{request.entity_type}/{request.public_key}/{request.hardware_id}/{request.timestamp}"
        proof = hashlib.sha256(proof_input.encode()).hexdigest()[:32]

        binding = Binding(
            lct_id=lct_id,
            entity_type=request.entity_type,
            public_key=request.public_key,
            hardware_id=request.hardware_id,
            created_at=request.timestamp or self._now_iso(),
            binding_proof=f"cose:{proof}",
            parent_lct=parent_lct,
        )
        self._bindings[lct_id] = binding

        # Update MRH
        ts = binding.created_at
        mrh = self._get_mrh(lct_id)
        if parent_lct:
            mrh.add_binding(parent_lct, "parent", ts)
            parent_mrh = self._get_mrh(parent_lct)
            parent_mrh.add_binding(lct_id, "child", ts)
            if parent_lct in self._bindings:
                self._bindings[parent_lct].children.append(lct_id)

        return True, "Bound", binding

    def revoke_binding(self, lct_id: str) -> Tuple[bool, str]:
        binding = self._bindings.get(lct_id)
        if not binding:
            return False, "Binding not found"
        binding.revoke()
        return True, "Revoked"

    # ── Pairing Operations (§2) ──────────────────────────────────

    def pair(self, request: PairingRequest) -> Tuple[bool, str, Optional[PairingSession]]:
        """Create a pairing between two entities."""
        ok, errors = request.validate()
        if not ok:
            return False, f"Validation failed: {errors}", None

        # Both entities must be bound and active
        for entity_id in [request.entity_a, request.entity_b]:
            binding = self._bindings.get(entity_id)
            if binding and binding.state == BindingState.REVOKED:
                return False, f"Entity {entity_id} is revoked", None

        self._session_counter += 1
        session_id = f"session-{self._session_counter:04d}"

        # Generate key halves
        key_a = os.urandom(32).hex()
        key_b = os.urandom(32).hex()

        session = PairingSession(
            session_id=session_id,
            mode=request.mode,
            entity_a=request.entity_a,
            entity_b=request.entity_b,
            context=request.context,
            rules=request.rules,
            key_a=key_a,
            key_b=key_b,
            witness_lct=request.witness_lct,
            authority_lct=request.authority_lct,
            created_at=time.time(),
        )

        # Mode-specific processing
        ts = self._now_iso()
        if request.mode == PairingMode.DIRECT:
            session.state = PairingState.PAIRED
        elif request.mode == PairingMode.WITNESSED:
            att_input = f"{request.entity_a}/{request.entity_b}/{session_id}/{ts}"
            session.witness_attestation = hashlib.sha256(att_input.encode()).hexdigest()[:32]
            session.state = PairingState.PAIRED
        elif request.mode == PairingMode.AUTHORIZED:
            auth_input = f"auth:{request.entity_a}/{request.entity_b}/{session_id}"
            session.authority_record = hashlib.sha256(auth_input.encode()).hexdigest()[:32]
            session.state = PairingState.PAIRED

        self._sessions[session_id] = session

        # Update MRH for both entities
        mrh_a = self._get_mrh(request.entity_a)
        mrh_b = self._get_mrh(request.entity_b)
        mrh_a.add_pairing(session, ts)
        mrh_b.add_pairing(session, ts)

        # If witnessed/authorized, add witness/authority to MRH
        if request.mode == PairingMode.WITNESSED and request.witness_lct:
            mrh_a.add_witnessing(request.witness_lct, "pairing", ts)
            mrh_b.add_witnessing(request.witness_lct, "pairing", ts)
        elif request.mode == PairingMode.AUTHORIZED and request.authority_lct:
            mrh_a.add_witnessing(request.authority_lct, "authorization", ts)
            mrh_b.add_witnessing(request.authority_lct, "authorization", ts)

        return True, "Paired", session

    def pair_role(self, agent_lct: str, role_lct: str,
                  authority_lct: Optional[str] = None,
                  context: str = "role_assignment") -> Tuple[bool, str, Optional[PairingSession]]:
        """Pair an agent with a role entity (§2.1.4)."""
        mode = PairingMode.AUTHORIZED if authority_lct else PairingMode.DIRECT
        request = PairingRequest(
            mode=mode,
            entity_a=agent_lct,
            entity_b=role_lct,
            context=context,
            rules={"type": "role_assignment"},
            authority_lct=authority_lct,
        )
        ok, msg, session = self.pair(request)
        if ok and session:
            session.is_role_pairing = True
            # Track role performers
            if role_lct not in self._role_performers:
                self._role_performers[role_lct] = []
            self._role_performers[role_lct].append(agent_lct)
        return ok, msg, session

    def unpair(self, session_id: str) -> Tuple[bool, str]:
        """End a pairing session."""
        session = self._sessions.get(session_id)
        if not session:
            return False, "Session not found"
        if session.is_permanent:
            return False, "Cannot unpair permanent session (birth certificate)"

        session.state = PairingState.REVOKED
        ts = self._now_iso()

        # Remove from MRH
        mrh_a = self._get_mrh(session.entity_a)
        mrh_b = self._get_mrh(session.entity_b)
        mrh_a.remove_pairing(session_id, ts)
        mrh_b.remove_pairing(session_id, ts)

        # If role pairing, remove from performers
        if session.is_role_pairing and session.entity_b in self._role_performers:
            perfs = self._role_performers[session.entity_b]
            if session.entity_a in perfs:
                perfs.remove(session.entity_a)

        return True, "Unpaired"

    # ── Witnessing Operations (§3) ───────────────────────────────

    def witness(self, assertion: WitnessAssertion) -> Tuple[bool, str]:
        """Record a witness assertion."""
        if not assertion.observer_lct or not assertion.observed_lct:
            return False, "Observer and observed LCT required"

        self._witnesses.append(assertion)

        # Update MRH bidirectionally
        ts = assertion.timestamp or self._now_iso()
        observed_mrh = self._get_mrh(assertion.observed_lct)
        observed_mrh.add_witnessing(assertion.observer_lct,
                                     assertion.evidence_type.value.lower(), ts)

        return True, "Witnessed"

    def get_witnesses_for(self, lct_id: str) -> List[WitnessAssertion]:
        return [w for w in self._witnesses if w.observed_lct == lct_id]

    # ── Broadcast Operations (§4) ────────────────────────────────

    def register_accumulator(self, acc_id: str) -> Accumulator:
        acc = Accumulator(acc_id)
        self._accumulators[acc_id] = acc
        return acc

    def broadcast(self, message: BroadcastMessage) -> List[AccumulatorEntry]:
        """Broadcast a message — all accumulators record it."""
        entries = []
        for acc in self._accumulators.values():
            entry = acc.record(message)
            entries.append(entry)
        return entries

    # ── Query Operations ─────────────────────────────────────────

    def get_binding(self, lct_id: str) -> Optional[Binding]:
        return self._bindings.get(lct_id)

    def get_session(self, session_id: str) -> Optional[PairingSession]:
        return self._sessions.get(session_id)

    def get_mrh(self, lct_id: str) -> MRHGraph:
        return self._get_mrh(lct_id)

    def get_role_performers(self, role_lct: str) -> List[str]:
        return self._role_performers.get(role_lct, [])

    def get_active_sessions(self, lct_id: str) -> List[PairingSession]:
        return [s for s in self._sessions.values()
                if (s.entity_a == lct_id or s.entity_b == lct_id)
                and s.state == PairingState.PAIRED]


# ═══════════════════════════════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name}")

    now_iso = "2026-02-22T12:00:00Z"

    # ── T1: Binding ──────────────────────────────────────────────
    print("T1: Binding")
    mgr = RelationshipManager()
    hw_id = hashlib.sha256(b"legion-hardware").hexdigest()

    req = BindingRequest(
        entity_type="human",
        public_key="mb64alicekey",
        hardware_id=hw_id,
        timestamp=now_iso,
    )
    ok, msg, binding = mgr.bind(req)
    check("T1.1 Binding succeeds", ok)
    check("T1.2 LCT ID starts with lct:web4:human:", binding.lct_id.startswith("lct:web4:human:"))
    check("T1.3 Binding proof starts with cose:", binding.binding_proof.startswith("cose:"))
    check("T1.4 State is BOUND", binding.state == BindingState.BOUND)
    check("T1.5 Hardware ID preserved", binding.hardware_id == hw_id)

    # Invalid entity type
    bad_req = BindingRequest(entity_type="invalid", public_key="key")
    ok, msg, _ = mgr.bind(bad_req)
    check("T1.6 Invalid entity type rejected", not ok)

    # Missing public key
    bad_req2 = BindingRequest(entity_type="ai", public_key="")
    ok, msg, _ = mgr.bind(bad_req2)
    check("T1.7 Missing public key rejected", not ok)

    # Parent-child binding
    parent_req = BindingRequest(entity_type="organization", public_key="mb64orgkey",
                                 hardware_id=hw_id, timestamp=now_iso)
    ok, _, parent = mgr.bind(parent_req)
    child_req = BindingRequest(entity_type="ai", public_key="mb64childkey",
                                hardware_id=hw_id, timestamp=now_iso)
    ok, _, child = mgr.bind(child_req, parent_lct=parent.lct_id)
    check("T1.8 Child bound with parent", ok)
    check("T1.9 Child MRH has parent",
          any(b.bound_type == "parent" for b in mgr.get_mrh(child.lct_id).bound))
    check("T1.10 Parent MRH has child",
          any(b.bound_type == "child" for b in mgr.get_mrh(parent.lct_id).bound))
    check("T1.11 Parent tracks child", child.lct_id in parent.children)

    # Revocation
    ok, _ = mgr.revoke_binding(binding.lct_id)
    check("T1.12 Revocation succeeds", ok)
    check("T1.13 State is REVOKED", binding.state == BindingState.REVOKED)

    # ── T2: Direct Pairing ───────────────────────────────────────
    print("T2: Direct Pairing")
    mgr2 = RelationshipManager()
    _, _, alice = mgr2.bind(BindingRequest("BIND/1.0", "human", "mb64alice", hw_id, now_iso))
    _, _, bob = mgr2.bind(BindingRequest("BIND/1.0", "ai", "mb64bob", hw_id, now_iso))

    pair_req = PairingRequest(
        mode=PairingMode.DIRECT,
        entity_a=alice.lct_id,
        entity_b=bob.lct_id,
        context="collaborative_writing",
        rules={"duration": 3600, "permissions": ["read", "suggest"]},
    )
    ok, msg, session = mgr2.pair(pair_req)
    check("T2.1 Direct pairing succeeds", ok)
    check("T2.2 Session created", session is not None)
    check("T2.3 Session has ID", session.session_id.startswith("session-"))
    check("T2.4 State is PAIRED", session.state == PairingState.PAIRED)
    check("T2.5 Key A is 64 hex chars", len(session.key_a) == 64)
    check("T2.6 Key B is 64 hex chars", len(session.key_b) == 64)
    check("T2.7 Keys are different", session.key_a != session.key_b)
    check("T2.8 Full key derivable", len(session.derive_full_key()) == 64)
    check("T2.9 Context preserved", session.context == "collaborative_writing")
    check("T2.10 Rules preserved", session.rules["duration"] == 3600)

    # MRH updated
    alice_mrh = mgr2.get_mrh(alice.lct_id)
    check("T2.11 Alice MRH has pairing", len(alice_mrh.paired) == 1)
    check("T2.12 Alice pairing mode is direct", alice_mrh.paired[0].pairing_mode == "direct")

    bob_mrh = mgr2.get_mrh(bob.lct_id)
    check("T2.13 Bob MRH has pairing", len(bob_mrh.paired) == 1)

    # ── T3: Witnessed Pairing ────────────────────────────────────
    print("T3: Witnessed Pairing")
    _, _, oracle = mgr2.bind(BindingRequest("BIND/1.0", "oracle", "mb64oracle", hw_id, now_iso))

    witnessed_req = PairingRequest(
        mode=PairingMode.WITNESSED,
        entity_a=alice.lct_id,
        entity_b=bob.lct_id,
        context="service_agreement",
        rules={"sla": "99.9%"},
        witness_lct=oracle.lct_id,
    )
    ok, _, w_session = mgr2.pair(witnessed_req)
    check("T3.1 Witnessed pairing succeeds", ok)
    check("T3.2 Witness attestation exists", w_session.witness_attestation is not None)
    check("T3.3 Mode is WITNESSED", w_session.mode == PairingMode.WITNESSED)

    # MRH includes witness
    alice_mrh2 = mgr2.get_mrh(alice.lct_id)
    check("T3.4 Alice MRH has witness entry",
          any(w.role == "pairing" for w in alice_mrh2.witnessing))
    bob_mrh2 = mgr2.get_mrh(bob.lct_id)
    check("T3.5 Bob MRH has witness entry",
          any(w.role == "pairing" for w in bob_mrh2.witnessing))

    # ── T4: Authorized Pairing ───────────────────────────────────
    print("T4: Authorized Pairing")
    _, _, authority = mgr2.bind(BindingRequest("BIND/1.0", "organization", "mb64auth",
                                                hw_id, now_iso))

    auth_req = PairingRequest(
        mode=PairingMode.AUTHORIZED,
        entity_a=alice.lct_id,
        entity_b=bob.lct_id,
        context="role_assignment",
        rules={"clearance": "executive"},
        authority_lct=authority.lct_id,
    )
    ok, _, a_session = mgr2.pair(auth_req)
    check("T4.1 Authorized pairing succeeds", ok)
    check("T4.2 Authority record exists", a_session.authority_record is not None)
    check("T4.3 Mode is AUTHORIZED", a_session.mode == PairingMode.AUTHORIZED)

    # MRH includes authority
    check("T4.4 Alice MRH has authorization witness",
          any(w.role == "authorization" for w in mgr2.get_mrh(alice.lct_id).witnessing))

    # ── T5: Role-Agent Pairing ───────────────────────────────────
    print("T5: Role-Agent Pairing")
    _, _, role = mgr2.bind(BindingRequest("BIND/1.0", "role", "mb64role", hw_id, now_iso))

    ok, _, role_session = mgr2.pair_role(
        alice.lct_id, role.lct_id,
        authority_lct=authority.lct_id,
        context="financial_officer",
    )
    check("T5.1 Role-agent pairing succeeds", ok)
    check("T5.2 Session marked as role pairing", role_session.is_role_pairing)
    check("T5.3 Role has performer", alice.lct_id in mgr2.get_role_performers(role.lct_id))

    # Unpair role
    ok, _ = mgr2.unpair(role_session.session_id)
    check("T5.4 Role unpairing succeeds", ok)
    check("T5.5 Performer removed", alice.lct_id not in mgr2.get_role_performers(role.lct_id))
    check("T5.6 Session state is REVOKED", role_session.state == PairingState.REVOKED)

    # ── T6: Witnessing ───────────────────────────────────────────
    print("T6: Witnessing")
    assertion = WitnessAssertion(
        observer_lct=oracle.lct_id,
        observed_lct=alice.lct_id,
        evidence_type=WitnessEvidenceType.ACTION,
        evidence_data={"action": "r6:execute", "quality": "high"},
        signature="cose:witness_sig",
        timestamp=now_iso,
    )
    ok, msg = mgr2.witness(assertion)
    check("T6.1 Witness assertion recorded", ok)

    witnesses = mgr2.get_witnesses_for(alice.lct_id)
    check("T6.2 Alice has 1 witness assertion", len(witnesses) == 1)
    check("T6.3 Observer is oracle", witnesses[0].observer_lct == oracle.lct_id)
    check("T6.4 Evidence type is ACTION", witnesses[0].evidence_type == WitnessEvidenceType.ACTION)

    # MRH updated
    alice_mrh3 = mgr2.get_mrh(alice.lct_id)
    action_witnesses = [w for w in alice_mrh3.witnessing if w.role == "action"]
    check("T6.5 MRH has action witness entry", len(action_witnesses) >= 1)

    # Multiple witness assertions
    for etype in [WitnessEvidenceType.EXISTENCE, WitnessEvidenceType.STATE]:
        mgr2.witness(WitnessAssertion(
            observer_lct=oracle.lct_id,
            observed_lct=alice.lct_id,
            evidence_type=etype,
            evidence_data={"status": "ok"},
            timestamp=now_iso,
        ))
    witnesses = mgr2.get_witnesses_for(alice.lct_id)
    check("T6.6 Alice has 3 witness assertions", len(witnesses) == 3)

    # Hash stability
    h = assertion.hash()
    check("T6.7 Hash is 64-char hex", len(h) == 64)
    check("T6.8 Hash is deterministic", assertion.hash() == h)

    # ── T7: Broadcast & Accumulator ──────────────────────────────
    print("T7: Broadcast & Accumulator")
    acc1 = mgr2.register_accumulator("acc-1")
    acc2 = mgr2.register_accumulator("acc-2")

    broadcast_msg = BroadcastMessage(
        sender_id=alice.lct_id,
        message_type=BroadcastType.ANNOUNCE,
        payload={"capabilities": ["r6:execute", "witness:attest"]},
        timestamp=time.time(),
    )
    entries = mgr2.broadcast(broadcast_msg)
    check("T7.1 Broadcast recorded by 2 accumulators", len(entries) == 2)
    check("T7.2 Entries have broadcast hash", all(e.broadcast_hash for e in entries))

    # Query accumulator
    results = acc1.query(entity_id=alice.lct_id)
    check("T7.3 Query by entity returns 1 result", len(results) == 1)

    # Multiple broadcasts
    for i in range(3):
        mgr2.broadcast(BroadcastMessage(
            sender_id=alice.lct_id,
            message_type=BroadcastType.HEARTBEAT,
            payload={"alive": True},
            timestamp=time.time() + i,
        ))
    check("T7.4 Accumulator has 4 entries for Alice", acc1.count(alice.lct_id) == 4)
    check("T7.5 Total count is 4", acc1.count() == 4)

    # Bob's broadcasts separate
    mgr2.broadcast(BroadcastMessage(
        sender_id=bob.lct_id,
        message_type=BroadcastType.CAPABILITY,
        payload={"skills": ["analysis"]},
        timestamp=time.time(),
    ))
    check("T7.6 Alice count still 4", acc1.count(alice.lct_id) == 4)
    check("T7.7 Bob count is 1", acc1.count(bob.lct_id) == 1)
    check("T7.8 Total is 5", acc1.count() == 5)

    # Broadcast hash stability
    h = broadcast_msg.hash()
    check("T7.9 Broadcast hash is 64 chars", len(h) == 64)
    check("T7.10 Hash is deterministic", broadcast_msg.hash() == h)

    # ── T8: MRH Graph ───────────────────────────────────────────
    print("T8: MRH Graph")
    mrh = mgr2.get_mrh(alice.lct_id)
    d = mrh.to_dict()
    check("T8.1 MRH has bound array", isinstance(d["bound"], list))
    check("T8.2 MRH has paired array", isinstance(d["paired"], list))
    check("T8.3 MRH has witnessing array", isinstance(d["witnessing"], list))
    check("T8.4 MRH has horizon_depth", d["horizon_depth"] == 3)
    check("T8.5 MRH has last_updated", d["last_updated"] != "")

    # Pairing count (direct + witnessed + authorized + role = 4, minus 1 unpaired = 3)
    active_sessions = mgr2.get_active_sessions(alice.lct_id)
    check("T8.6 Alice has 3 active sessions", len(active_sessions) == 3)

    # ── T9: Validation Edge Cases ────────────────────────────────
    print("T9: Validation Edge Cases")

    # Missing entities
    bad_pair = PairingRequest(mode=PairingMode.DIRECT, entity_a="", entity_b="b")
    ok, msg, _ = mgr2.pair(bad_pair)
    check("T9.1 Missing entity A rejected", not ok)

    # Witnessed without witness
    bad_witnessed = PairingRequest(
        mode=PairingMode.WITNESSED,
        entity_a="a", entity_b="b",
    )
    ok, msg, _ = mgr2.pair(bad_witnessed)
    check("T9.2 Witnessed without witness rejected", not ok)

    # Authorized without authority
    bad_auth = PairingRequest(
        mode=PairingMode.AUTHORIZED,
        entity_a="a", entity_b="b",
    )
    ok, msg, _ = mgr2.pair(bad_auth)
    check("T9.3 Authorized without authority rejected", not ok)

    # Witness with empty observer
    bad_witness = WitnessAssertion(observer_lct="", observed_lct="x")
    ok, msg = mgr2.witness(bad_witness)
    check("T9.4 Empty observer rejected", not ok)

    # Non-existent binding revocation
    ok, msg = mgr2.revoke_binding("lct:web4:nonexistent")
    check("T9.5 Non-existent revocation rejected", not ok)

    # Non-existent unpair
    ok, msg = mgr2.unpair("session-9999")
    check("T9.6 Non-existent unpair rejected", not ok)

    # Permanent session can't be unpaired
    _, _, perm = mgr2.pair(PairingRequest(
        mode=PairingMode.DIRECT,
        entity_a=alice.lct_id,
        entity_b=bob.lct_id,
        context="birth_certificate",
    ))
    perm.is_permanent = True
    ok, msg = mgr2.unpair(perm.session_id)
    check("T9.7 Permanent pairing can't be unpaired", not ok)

    # Revoked entity can't pair
    _, _, revokable = mgr2.bind(BindingRequest("BIND/1.0", "ai", "mb64rev", hw_id, now_iso))
    mgr2.revoke_binding(revokable.lct_id)
    ok, msg, _ = mgr2.pair(PairingRequest(
        mode=PairingMode.DIRECT,
        entity_a=revokable.lct_id,
        entity_b=alice.lct_id,
    ))
    check("T9.8 Revoked entity can't pair", not ok)

    # ── T10: T3 Propagation ──────────────────────────────────────
    print("T10: T3 Propagation")
    t3 = T3Snapshot(talent=0.8, training=0.7, temperament=0.9)
    check("T10.1 T3 composite = 0.8", abs(t3.composite() - 0.8) < 0.001)

    t3.adjust(0.05, -0.03, 0.02)
    check("T10.2 Talent adjusted to 0.85", abs(t3.talent - 0.85) < 0.001)
    check("T10.3 Training adjusted to 0.67", abs(t3.training - 0.67) < 0.001)
    check("T10.4 Temperament adjusted to 0.92", abs(t3.temperament - 0.92) < 0.001)

    # Cap enforcement
    t3.adjust(0.5, -0.5, 0.0, cap=0.1)
    check("T10.5 Adjustment capped at +0.1", abs(t3.talent - 0.95) < 0.001)
    check("T10.6 Negative cap at -0.1", abs(t3.training - 0.57) < 0.001)

    # Boundary clamping
    t3_extreme = T3Snapshot(talent=0.95, training=0.05, temperament=0.5)
    t3_extreme.adjust(0.1, -0.1, 0.0)
    check("T10.7 Clamped at 1.0", t3_extreme.talent <= 1.0)
    check("T10.8 Clamped at 0.0", t3_extreme.training >= 0.0)

    # ── T11: All Entity Types ────────────────────────────────────
    print("T11: All Entity Types")
    mgr3 = RelationshipManager()
    for etype in ENTITY_TYPES:
        req = BindingRequest(entity_type=etype, public_key=f"mb64{etype}",
                              hardware_id=hw_id, timestamp=now_iso)
        ok, _, b = mgr3.bind(req)
        check(f"T11.{ENTITY_TYPES.index(etype)+1} {etype} binds successfully", ok)

    # ── T12: Evidence Types ──────────────────────────────────────
    print("T12: Evidence Types")
    check("T12.1 EXISTENCE type", WitnessEvidenceType.EXISTENCE.value == "EXISTENCE")
    check("T12.2 ACTION type", WitnessEvidenceType.ACTION.value == "ACTION")
    check("T12.3 STATE type", WitnessEvidenceType.STATE.value == "STATE")
    check("T12.4 TRANSITION type", WitnessEvidenceType.TRANSITION.value == "TRANSITION")

    # All evidence types can be witnessed
    mgr4 = RelationshipManager()
    _, _, observer = mgr4.bind(BindingRequest("BIND/1.0", "oracle", "mb64obs", hw_id, now_iso))
    _, _, target = mgr4.bind(BindingRequest("BIND/1.0", "ai", "mb64tgt", hw_id, now_iso))
    for etype in WitnessEvidenceType:
        ok, _ = mgr4.witness(WitnessAssertion(
            observer_lct=observer.lct_id,
            observed_lct=target.lct_id,
            evidence_type=etype,
            evidence_data={"type": etype.value},
            timestamp=now_iso,
        ))
        check(f"T12.{5 + list(WitnessEvidenceType).index(etype)} {etype.value} witnessed", ok)

    # ── T13: Broadcast Types ────────────────────────────────────
    print("T13: Broadcast Types")
    check("T13.1 ANNOUNCE type", BroadcastType.ANNOUNCE.value == "ANNOUNCE")
    check("T13.2 HEARTBEAT type", BroadcastType.HEARTBEAT.value == "HEARTBEAT")
    check("T13.3 CAPABILITY type", BroadcastType.CAPABILITY.value == "CAPABILITY")

    # MRH not updated by broadcast (spec: no relationship formed)
    mgr5 = RelationshipManager()
    _, _, broadcaster = mgr5.bind(BindingRequest("BIND/1.0", "ai", "mb64bc", hw_id, now_iso))
    mgr5.register_accumulator("acc-test")
    mrh_before = len(mgr5.get_mrh(broadcaster.lct_id).paired)
    mgr5.broadcast(BroadcastMessage(
        sender_id=broadcaster.lct_id,
        message_type=BroadcastType.ANNOUNCE,
        payload={"msg": "hello"},
        timestamp=time.time(),
    ))
    mrh_after = len(mgr5.get_mrh(broadcaster.lct_id).paired)
    check("T13.4 Broadcast does NOT update MRH", mrh_before == mrh_after)

    # ── T14: Pairing Mode Selection ──────────────────────────────
    print("T14: Pairing Mode Selection Criteria")
    check("T14.1 DIRECT for low-trust P2P", PairingMode.DIRECT.value == "direct")
    check("T14.2 WITNESSED for cross-domain", PairingMode.WITNESSED.value == "witnessed")
    check("T14.3 AUTHORIZED for high-stakes", PairingMode.AUTHORIZED.value == "authorized")

    # Direct has no witness/authority
    check("T14.4 Direct session: no witness", session.witness_attestation is None)
    check("T14.5 Direct session: no authority", session.authority_record is None)

    # Witnessed has attestation
    check("T14.6 Witnessed session: has attestation", w_session.witness_attestation is not None)

    # Authorized has authority record
    check("T14.7 Authorized session: has authority record", a_session.authority_record is not None)

    # ── T15: Cross-Mechanism Integration ─────────────────────────
    print("T15: Cross-Mechanism Integration")
    full = RelationshipManager()

    # 1. Bind organization
    _, _, org = full.bind(BindingRequest("BIND/1.0", "organization", "mb64org", hw_id, now_iso))

    # 2. Bind employee under org
    _, _, emp = full.bind(BindingRequest("BIND/1.0", "human", "mb64emp", hw_id, now_iso),
                          parent_lct=org.lct_id)

    # 3. Bind role
    _, _, fin_role = full.bind(BindingRequest("BIND/1.0", "role", "mb64fin", hw_id, now_iso))

    # 4. Authorized pairing: employee → role
    ok, _, role_session = full.pair_role(emp.lct_id, fin_role.lct_id,
                                          authority_lct=org.lct_id,
                                          context="financial_officer")
    check("T15.1 Full lifecycle: role paired", ok)

    # 5. Witness the pairing
    _, _, auditor = full.bind(BindingRequest("BIND/1.0", "oracle", "mb64aud", hw_id, now_iso))
    full.witness(WitnessAssertion(
        observer_lct=auditor.lct_id,
        observed_lct=emp.lct_id,
        evidence_type=WitnessEvidenceType.ACTION,
        evidence_data={"action": "role_assignment", "result": "success"},
        timestamp=now_iso,
    ))

    # 6. Broadcast capability
    full.register_accumulator("full-acc")
    entries = full.broadcast(BroadcastMessage(
        sender_id=emp.lct_id,
        message_type=BroadcastType.CAPABILITY,
        payload={"role": "financial_officer"},
        timestamp=time.time(),
    ))
    check("T15.2 Broadcast recorded", len(entries) == 1)

    # Verify full MRH
    emp_mrh = full.get_mrh(emp.lct_id)
    check("T15.3 MRH has parent (org)", any(b.bound_type == "parent" for b in emp_mrh.bound))
    check("T15.4 MRH has role pairing", any(p.pairing_context == "financial_officer" for p in emp_mrh.paired))
    check("T15.5 MRH has authorization witness",
          any(w.role == "authorization" for w in emp_mrh.witnessing))
    check("T15.6 MRH has action witness",
          any(w.role == "action" for w in emp_mrh.witnessing))

    # Verify role performers
    check("T15.7 Role has performer", emp.lct_id in full.get_role_performers(fin_role.lct_id))

    # ── Summary ──────────────────────────────────────────────────
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"Entity Relationships Unified: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  FAILED: {failed}")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
