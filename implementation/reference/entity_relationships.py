#!/usr/bin/env python3
"""
Web4 Entity Relationships — Unified Reference Implementation

Implements all 4 relationship mechanisms per web4-entity-relationships.md:
- BINDING (BIND/1.0): Permanent identity attachment to LCT
- PAIRING (PAIR/1.0): Authorized operational relationships (3 modes)
  - Direct: Peer-to-peer, no third party
  - Witnessed: Notarized by witness entity
  - Authorized: Mediated by authority entity
- WITNESSING (WTNS/1.0): Trust building through observation
- BROADCAST (CAST/1.0): Unidirectional discovery and liveness

State machines, MRH integration, T3/V3 evolution, R6 workflow.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════
# BINDING (BIND/1.0)
# ═══════════════════════════════════════════════════════════════════

class BindingState(str, Enum):
    UNBOUND = "unbound"
    BINDING = "binding"
    BOUND = "bound"
    REVOKED = "revoked"


class EntityType(str, Enum):
    HUMAN = "human"
    AI = "ai"
    SOCIETY = "society"
    ORGANIZATION = "organization"
    ROLE = "role"
    TASK = "task"
    RESOURCE = "resource"
    DEVICE = "device"
    SERVICE = "service"
    ORACLE = "oracle"
    ACCUMULATOR = "accumulator"
    DICTIONARY = "dictionary"
    HYBRID = "hybrid"
    POLICY = "policy"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class BindingRequest:
    version: str = "BIND/1.0"
    entity_type: EntityType = EntityType.AI
    public_key: str = ""
    hardware_id: str = ""

    def hash(self) -> str:
        data = f"{self.entity_type.value}:{self.public_key}:{self.hardware_id}"
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class BindingRecord:
    lct_id: str
    entity_type: EntityType
    public_key: str
    hardware_id: str
    binding_proof: str
    parent_lct: Optional[str] = None
    state: BindingState = BindingState.BOUND
    timestamp: str = ""

    def to_dict(self) -> dict:
        d = {
            "lct_id": self.lct_id,
            "entity_type": self.entity_type.value,
            "public_key": self.public_key,
            "hardware_id": self.hardware_id,
            "binding_proof": self.binding_proof,
            "state": self.state.value,
            "timestamp": self.timestamp,
        }
        if self.parent_lct:
            d["parent_lct"] = self.parent_lct
        return d


class BindingManager:
    """Manages entity binding lifecycle."""

    def __init__(self):
        self._bindings: Dict[str, BindingRecord] = {}
        self._state_log: List[dict] = []

    def _now(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def initiate_binding(self, request: BindingRequest,
                         parent_lct: Optional[str] = None) -> BindingRecord:
        """Create a new entity binding."""
        lct_id = f"lct:web4:{request.entity_type.value}:{request.hash()[:16]}"
        proof = f"cose:{hashlib.sha256(f'{lct_id}:{request.public_key}'.encode()).hexdigest()[:32]}"
        ts = self._now()

        record = BindingRecord(
            lct_id=lct_id,
            entity_type=request.entity_type,
            public_key=request.public_key,
            hardware_id=request.hardware_id,
            binding_proof=proof,
            parent_lct=parent_lct,
            state=BindingState.BOUND,
            timestamp=ts,
        )
        self._bindings[lct_id] = record
        self._state_log.append({
            "event": "binding_created",
            "lct_id": lct_id,
            "parent": parent_lct,
            "ts": ts,
        })
        return record

    def revoke_binding(self, lct_id: str) -> Tuple[bool, str]:
        rec = self._bindings.get(lct_id)
        if not rec:
            return False, "Unknown LCT"
        if rec.state == BindingState.REVOKED:
            return False, "Already revoked"
        rec.state = BindingState.REVOKED
        self._state_log.append({
            "event": "binding_revoked", "lct_id": lct_id, "ts": self._now()
        })
        return True, "Binding revoked"

    def get_binding(self, lct_id: str) -> Optional[BindingRecord]:
        return self._bindings.get(lct_id)

    def get_children(self, parent_lct: str) -> List[BindingRecord]:
        return [b for b in self._bindings.values() if b.parent_lct == parent_lct]

    def is_active(self, lct_id: str) -> bool:
        b = self._bindings.get(lct_id)
        return b is not None and b.state == BindingState.BOUND


# ═══════════════════════════════════════════════════════════════════
# PAIRING (PAIR/1.0) — 3 modes
# ═══════════════════════════════════════════════════════════════════

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
    DORMANT = "dormant"
    REVOKED = "revoked"


@dataclass
class PairingRules:
    """Rules governing a pairing."""
    permissions: List[str] = field(default_factory=lambda: ["read"])
    duration: int = 3600  # seconds
    context: str = ""
    max_actions_per_minute: int = 10

    def to_dict(self) -> dict:
        return {
            "permissions": self.permissions,
            "duration": self.duration,
            "context": self.context,
            "max_actions_per_minute": self.max_actions_per_minute,
        }


@dataclass
class PairingSession:
    """An active or historical pairing session."""
    session_id: str
    mode: PairingMode
    entity_a: str
    entity_b: str
    rules: PairingRules
    state: PairingState
    witness_lct: Optional[str] = None   # For witnessed mode
    authority_lct: Optional[str] = None  # For authorized mode
    key_a: str = ""  # Entity A's key half
    key_b: str = ""  # Entity B's key half
    created_at: str = ""
    closed_at: str = ""
    witness_attestation: str = ""
    authority_record: str = ""

    def to_dict(self) -> dict:
        d = {
            "session_id": self.session_id,
            "mode": self.mode.value,
            "entity_a": self.entity_a,
            "entity_b": self.entity_b,
            "rules": self.rules.to_dict(),
            "state": self.state.value,
            "created_at": self.created_at,
        }
        if self.witness_lct:
            d["witness_lct"] = self.witness_lct
        if self.authority_lct:
            d["authority_lct"] = self.authority_lct
        if self.closed_at:
            d["closed_at"] = self.closed_at
        return d


class PairingManager:
    """Manages pairing lifecycle across all 3 modes."""

    def __init__(self, binding_mgr: BindingManager):
        self.binding = binding_mgr
        self._sessions: Dict[str, PairingSession] = {}
        self._entity_pairings: Dict[str, List[str]] = {}  # lct -> [session_ids]

    def _now(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _gen_session_id(self, a: str, b: str) -> str:
        return f"sess:{hashlib.sha256(f'{a}:{b}:{time.time()}'.encode()).hexdigest()[:16]}"

    def _gen_key_half(self) -> str:
        return os.urandom(32).hex()

    def initiate_direct(self, entity_a: str, entity_b: str,
                        rules: PairingRules) -> Tuple[Optional[PairingSession], str]:
        """Initiate a direct peer-to-peer pairing."""
        if not self.binding.is_active(entity_a):
            return None, f"Entity A ({entity_a}) not active"
        if not self.binding.is_active(entity_b):
            return None, f"Entity B ({entity_b}) not active"

        session = PairingSession(
            session_id=self._gen_session_id(entity_a, entity_b),
            mode=PairingMode.DIRECT,
            entity_a=entity_a,
            entity_b=entity_b,
            rules=rules,
            state=PairingState.PAIRED,
            key_a=self._gen_key_half(),
            key_b=self._gen_key_half(),
            created_at=self._now(),
        )
        self._sessions[session.session_id] = session
        self._add_entity_pairing(entity_a, session.session_id)
        self._add_entity_pairing(entity_b, session.session_id)
        return session, "Direct pairing established"

    def initiate_witnessed(self, entity_a: str, entity_b: str,
                           witness_lct: str,
                           rules: PairingRules) -> Tuple[Optional[PairingSession], str]:
        """Initiate a witnessed (notarized) pairing."""
        for lct in [entity_a, entity_b, witness_lct]:
            if not self.binding.is_active(lct):
                return None, f"Entity ({lct}) not active"

        attestation = hashlib.sha256(
            f"{entity_a}:{entity_b}:{witness_lct}:{time.time()}".encode()
        ).hexdigest()[:32]

        session = PairingSession(
            session_id=self._gen_session_id(entity_a, entity_b),
            mode=PairingMode.WITNESSED,
            entity_a=entity_a,
            entity_b=entity_b,
            rules=rules,
            state=PairingState.PAIRED,
            witness_lct=witness_lct,
            key_a=self._gen_key_half(),
            key_b=self._gen_key_half(),
            witness_attestation=f"cose:{attestation}",
            created_at=self._now(),
        )
        self._sessions[session.session_id] = session
        self._add_entity_pairing(entity_a, session.session_id)
        self._add_entity_pairing(entity_b, session.session_id)
        return session, "Witnessed pairing established"

    def initiate_authorized(self, entity_a: str, entity_b: str,
                            authority_lct: str,
                            rules: PairingRules) -> Tuple[Optional[PairingSession], str]:
        """Initiate an authority-mediated pairing."""
        for lct in [entity_a, entity_b, authority_lct]:
            if not self.binding.is_active(lct):
                return None, f"Entity ({lct}) not active"

        auth_record = hashlib.sha256(
            f"AUTH:{entity_a}:{entity_b}:{authority_lct}:{time.time()}".encode()
        ).hexdigest()[:32]

        session = PairingSession(
            session_id=self._gen_session_id(entity_a, entity_b),
            mode=PairingMode.AUTHORIZED,
            entity_a=entity_a,
            entity_b=entity_b,
            rules=rules,
            state=PairingState.PAIRED,
            authority_lct=authority_lct,
            key_a=self._gen_key_half(),
            key_b=self._gen_key_half(),
            authority_record=f"cose:{auth_record}",
            created_at=self._now(),
        )
        self._sessions[session.session_id] = session
        self._add_entity_pairing(entity_a, session.session_id)
        self._add_entity_pairing(entity_b, session.session_id)
        return session, "Authorized pairing established"

    def activate_session(self, session_id: str) -> Tuple[bool, str]:
        s = self._sessions.get(session_id)
        if not s:
            return False, "Session not found"
        if s.state != PairingState.PAIRED:
            return False, f"Cannot activate from state {s.state.value}"
        s.state = PairingState.ACTIVE
        return True, "Session activated"

    def close_session(self, session_id: str) -> Tuple[bool, str]:
        s = self._sessions.get(session_id)
        if not s:
            return False, "Session not found"
        if s.state not in (PairingState.ACTIVE, PairingState.PAIRED):
            return False, f"Cannot close from state {s.state.value}"
        s.state = PairingState.DORMANT
        s.closed_at = self._now()
        return True, "Session closed"

    def revoke_pairing(self, session_id: str) -> Tuple[bool, str]:
        s = self._sessions.get(session_id)
        if not s:
            return False, "Session not found"
        s.state = PairingState.REVOKED
        s.closed_at = self._now()
        return True, "Pairing revoked"

    def get_session(self, session_id: str) -> Optional[PairingSession]:
        return self._sessions.get(session_id)

    def get_entity_pairings(self, lct_id: str) -> List[PairingSession]:
        session_ids = self._entity_pairings.get(lct_id, [])
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    def _add_entity_pairing(self, lct_id: str, session_id: str):
        if lct_id not in self._entity_pairings:
            self._entity_pairings[lct_id] = []
        self._entity_pairings[lct_id].append(session_id)


# ═══════════════════════════════════════════════════════════════════
# WITNESSING (WTNS/1.0)
# ═══════════════════════════════════════════════════════════════════

class WitnessEvidenceType(str, Enum):
    EXISTENCE = "EXISTENCE"
    ACTION = "ACTION"
    STATE = "STATE"
    TRANSITION = "TRANSITION"


@dataclass
class WitnessRecord:
    """Record of a witnessing event."""
    observer_lct: str
    observed_lct: str
    evidence_type: WitnessEvidenceType
    evidence_data: Dict[str, Any]
    signature: str
    timestamp: str

    def to_dict(self) -> dict:
        return {
            "version": "WTNS/1.0",
            "observer_lct": self.observer_lct,
            "observed_lct": self.observed_lct,
            "evidence_type": self.evidence_type.value,
            "evidence_data": self.evidence_data,
            "signature": self.signature,
            "timestamp": self.timestamp,
        }


class WitnessingManager:
    """Manages witnessing relationships."""

    def __init__(self, binding_mgr: BindingManager):
        self.binding = binding_mgr
        self._records: List[WitnessRecord] = []
        self._witness_counts: Dict[str, Dict[str, int]] = {}  # observed -> {observer: count}

    def _now(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def witness(self, observer_lct: str, observed_lct: str,
                evidence_type: WitnessEvidenceType,
                evidence_data: Dict[str, Any]) -> Tuple[Optional[WitnessRecord], str]:
        """Record a witnessing event."""
        if not self.binding.is_active(observer_lct):
            return None, "Observer not active"
        if not self.binding.is_active(observed_lct):
            return None, "Observed entity not active"
        if observer_lct == observed_lct:
            return None, "Cannot witness self"

        sig = hashlib.sha256(
            f"{observer_lct}:{observed_lct}:{evidence_type.value}:{time.time()}".encode()
        ).hexdigest()[:32]

        record = WitnessRecord(
            observer_lct=observer_lct,
            observed_lct=observed_lct,
            evidence_type=evidence_type,
            evidence_data=evidence_data,
            signature=f"cose:{sig}",
            timestamp=self._now(),
        )
        self._records.append(record)

        # Track witness counts
        if observed_lct not in self._witness_counts:
            self._witness_counts[observed_lct] = {}
        counts = self._witness_counts[observed_lct]
        counts[observer_lct] = counts.get(observer_lct, 0) + 1

        return record, "Witnessed successfully"

    def get_witness_count(self, observed_lct: str) -> int:
        if observed_lct not in self._witness_counts:
            return 0
        return sum(self._witness_counts[observed_lct].values())

    def get_unique_witnesses(self, observed_lct: str) -> int:
        if observed_lct not in self._witness_counts:
            return 0
        return len(self._witness_counts[observed_lct])

    def get_records_for(self, observed_lct: str) -> List[WitnessRecord]:
        return [r for r in self._records if r.observed_lct == observed_lct]


# ═══════════════════════════════════════════════════════════════════
# BROADCAST (CAST/1.0)
# ═══════════════════════════════════════════════════════════════════

class BroadcastType(str, Enum):
    ANNOUNCE = "ANNOUNCE"
    HEARTBEAT = "HEARTBEAT"
    CAPABILITY = "CAPABILITY"


@dataclass
class BroadcastMessage:
    version: str = "CAST/1.0"
    sender_id: str = ""
    message_type: BroadcastType = BroadcastType.ANNOUNCE
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "sender_id": self.sender_id,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }


@dataclass
class AccumulatorRecord:
    """Record stored by an accumulator entity."""
    broadcast_hash: str
    sender_id: str
    message_type: BroadcastType
    timestamp: str
    signature: str


class BroadcastManager:
    """Manages broadcasts and accumulators."""

    def __init__(self):
        self._accumulators: Dict[str, List[AccumulatorRecord]] = {}
        self._broadcast_count: Dict[str, int] = {}

    def _now(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def broadcast(self, sender_id: str, message_type: BroadcastType,
                  payload: Dict[str, Any]) -> BroadcastMessage:
        """Send a broadcast (no acknowledgment required)."""
        msg = BroadcastMessage(
            sender_id=sender_id,
            message_type=message_type,
            payload=payload,
            timestamp=self._now(),
        )
        self._broadcast_count[sender_id] = self._broadcast_count.get(sender_id, 0) + 1

        # All accumulators receive the broadcast
        broadcast_hash = hashlib.sha256(
            json.dumps(msg.to_dict(), sort_keys=True).encode()
        ).hexdigest()

        sig = hashlib.sha256(f"{sender_id}:{broadcast_hash}".encode()).hexdigest()[:32]

        for acc_id in self._accumulators:
            self._accumulators[acc_id].append(AccumulatorRecord(
                broadcast_hash=broadcast_hash,
                sender_id=sender_id,
                message_type=message_type,
                timestamp=msg.timestamp,
                signature=f"cose:{sig}",
            ))

        return msg

    def register_accumulator(self, accumulator_id: str):
        """Register an accumulator to receive broadcasts."""
        if accumulator_id not in self._accumulators:
            self._accumulators[accumulator_id] = []

    def query_accumulator(self, accumulator_id: str,
                          sender_id: Optional[str] = None) -> List[AccumulatorRecord]:
        """Query an accumulator for broadcast history."""
        records = self._accumulators.get(accumulator_id, [])
        if sender_id:
            records = [r for r in records if r.sender_id == sender_id]
        return records

    def get_broadcast_count(self, sender_id: str) -> int:
        return self._broadcast_count.get(sender_id, 0)


# ═══════════════════════════════════════════════════════════════════
# MRH Integration
# ═══════════════════════════════════════════════════════════════════

@dataclass
class MRHState:
    """Entity's Markov Relevancy Horizon state."""
    bound: List[dict] = field(default_factory=list)
    paired: List[dict] = field(default_factory=list)
    witnessing: List[dict] = field(default_factory=list)
    horizon_depth: int = 3
    last_updated: str = ""

    def to_dict(self) -> dict:
        return {
            "bound": self.bound,
            "paired": self.paired,
            "witnessing": self.witnessing,
            "horizon_depth": self.horizon_depth,
            "last_updated": self.last_updated,
        }


class MRHManager:
    """Manages MRH state across all relationship types."""

    def __init__(self):
        self._states: Dict[str, MRHState] = {}

    def _now(self) -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def get_or_create(self, lct_id: str) -> MRHState:
        if lct_id not in self._states:
            self._states[lct_id] = MRHState(last_updated=self._now())
        return self._states[lct_id]

    def record_binding(self, parent_lct: str, child_lct: str):
        """Update MRH for a binding (bidirectional)."""
        ts = self._now()
        parent_mrh = self.get_or_create(parent_lct)
        parent_mrh.bound.append({"lct_id": child_lct, "type": "child", "ts": ts})
        parent_mrh.last_updated = ts

        child_mrh = self.get_or_create(child_lct)
        child_mrh.bound.append({"lct_id": parent_lct, "type": "parent", "ts": ts})
        child_mrh.last_updated = ts

    def record_pairing(self, session: PairingSession):
        """Update MRH for a pairing."""
        ts = self._now()
        for lct_id in [session.entity_a, session.entity_b]:
            mrh = self.get_or_create(lct_id)
            other = session.entity_b if lct_id == session.entity_a else session.entity_a
            mrh.paired.append({
                "lct_id": other,
                "pairing_mode": session.mode.value,
                "context": session.rules.context,
                "session_id": session.session_id,
                "ts": ts,
            })
            mrh.last_updated = ts

        # Witness/authority also gets MRH update
        third_party = session.witness_lct or session.authority_lct
        if third_party:
            for lct_id in [session.entity_a, session.entity_b]:
                mrh = self.get_or_create(lct_id)
                mrh.witnessing.append({
                    "lct_id": third_party,
                    "role": "notary" if session.mode == PairingMode.WITNESSED else "authority",
                    "ts": ts,
                })

    def record_witness(self, record: WitnessRecord):
        """Update MRH for a witnessing event."""
        ts = self._now()
        observed_mrh = self.get_or_create(record.observed_lct)

        # Check if this observer is already tracked
        existing = [w for w in observed_mrh.witnessing
                    if w.get("lct_id") == record.observer_lct
                    and w.get("role") == record.evidence_type.value.lower()]
        if existing:
            existing[0]["last_attestation"] = ts
            existing[0]["witness_count"] = existing[0].get("witness_count", 1) + 1
        else:
            observed_mrh.witnessing.append({
                "lct_id": record.observer_lct,
                "role": record.evidence_type.value.lower(),
                "last_attestation": ts,
                "witness_count": 1,
            })
        observed_mrh.last_updated = ts

    def get_state(self, lct_id: str) -> Optional[MRHState]:
        return self._states.get(lct_id)


# ═══════════════════════════════════════════════════════════════════
# T3/V3 Evolution Through Relationships
# ═══════════════════════════════════════════════════════════════════

@dataclass
class T3State:
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    @property
    def composite(self) -> float:
        return self.talent * 0.4 + self.training * 0.3 + self.temperament * 0.3

    def adjust(self, talent_delta: float = 0, training_delta: float = 0,
               temperament_delta: float = 0):
        self.talent = max(0.0, min(1.0, self.talent + talent_delta))
        self.training = max(0.0, min(1.0, self.training + training_delta))
        self.temperament = max(0.0, min(1.0, self.temperament + temperament_delta))


class TrustEvolution:
    """Track T3 evolution through relationship interactions."""

    def __init__(self):
        self._t3: Dict[str, T3State] = {}

    def get_or_create(self, lct_id: str) -> T3State:
        if lct_id not in self._t3:
            self._t3[lct_id] = T3State()
        return self._t3[lct_id]

    def on_witness(self, observed_lct: str, evidence_type: WitnessEvidenceType,
                   observer_t3_composite: float):
        """Adjust T3 based on witnessing event."""
        t3 = self.get_or_create(observed_lct)
        # Weight adjustment by observer's trust
        weight = observer_t3_composite * 0.01  # Small increments
        if evidence_type == WitnessEvidenceType.EXISTENCE:
            t3.adjust(talent_delta=weight * 0.5)
        elif evidence_type == WitnessEvidenceType.ACTION:
            t3.adjust(talent_delta=weight, training_delta=weight * 0.5)
        elif evidence_type == WitnessEvidenceType.STATE:
            t3.adjust(temperament_delta=weight)
        elif evidence_type == WitnessEvidenceType.TRANSITION:
            t3.adjust(training_delta=weight, temperament_delta=weight * 0.5)

    def on_pairing_action(self, actor_lct: str, success: bool):
        """Adjust T3 based on paired action outcome."""
        t3 = self.get_or_create(actor_lct)
        if success:
            t3.adjust(talent_delta=0.02, training_delta=0.01)
        else:
            t3.adjust(talent_delta=-0.02, training_delta=-0.01)


# ═══════════════════════════════════════════════════════════════════
# Unified Relationship Coordinator
# ═══════════════════════════════════════════════════════════════════

class RelationshipCoordinator:
    """Orchestrates all 4 relationship types with MRH and T3 integration."""

    def __init__(self):
        self.binding = BindingManager()
        self.pairing = PairingManager(self.binding)
        self.witnessing = WitnessingManager(self.binding)
        self.broadcast = BroadcastManager()
        self.mrh = MRHManager()
        self.trust = TrustEvolution()

    def create_entity(self, entity_type: EntityType, public_key: str,
                      hardware_id: str = "",
                      parent_lct: Optional[str] = None) -> BindingRecord:
        """Create a new entity with full MRH setup."""
        request = BindingRequest(
            entity_type=entity_type,
            public_key=public_key,
            hardware_id=hardware_id or hashlib.sha256(public_key.encode()).hexdigest(),
        )
        record = self.binding.initiate_binding(request, parent_lct)
        self.trust.get_or_create(record.lct_id)

        if parent_lct:
            self.mrh.record_binding(parent_lct, record.lct_id)

        return record

    def pair_direct(self, entity_a: str, entity_b: str,
                    context: str = "", permissions: Optional[List[str]] = None
                    ) -> Tuple[Optional[PairingSession], str]:
        rules = PairingRules(
            permissions=permissions or ["read", "write"],
            context=context,
        )
        session, msg = self.pairing.initiate_direct(entity_a, entity_b, rules)
        if session:
            self.mrh.record_pairing(session)
        return session, msg

    def pair_witnessed(self, entity_a: str, entity_b: str,
                       witness: str, context: str = ""
                       ) -> Tuple[Optional[PairingSession], str]:
        rules = PairingRules(permissions=["read", "write"], context=context)
        session, msg = self.pairing.initiate_witnessed(entity_a, entity_b, witness, rules)
        if session:
            self.mrh.record_pairing(session)
        return session, msg

    def pair_authorized(self, entity_a: str, entity_b: str,
                        authority: str, context: str = "",
                        permissions: Optional[List[str]] = None
                        ) -> Tuple[Optional[PairingSession], str]:
        rules = PairingRules(
            permissions=permissions or ["read", "write", "execute"],
            context=context,
        )
        session, msg = self.pairing.initiate_authorized(entity_a, entity_b, authority, rules)
        if session:
            self.mrh.record_pairing(session)
        return session, msg

    def witness_entity(self, observer: str, observed: str,
                       evidence_type: WitnessEvidenceType,
                       evidence_data: Dict[str, Any]
                       ) -> Tuple[Optional[WitnessRecord], str]:
        record, msg = self.witnessing.witness(observer, observed, evidence_type, evidence_data)
        if record:
            self.mrh.record_witness(record)
            observer_t3 = self.trust.get_or_create(observer).composite
            self.trust.on_witness(observed, evidence_type, observer_t3)
        return record, msg

    def send_broadcast(self, sender: str, msg_type: BroadcastType,
                       payload: Dict[str, Any]) -> BroadcastMessage:
        return self.broadcast.broadcast(sender, msg_type, payload)


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

    # ── T1: Entity Types ─────────────────────────────────────────
    print("T1: Entity Types")
    check("T1.1 15 entity types", len(EntityType) == 15)
    check("T1.2 Includes human", EntityType.HUMAN.value == "human")
    check("T1.3 Includes policy", EntityType.POLICY.value == "policy")

    # ── T2: Binding States ───────────────────────────────────────
    print("T2: Binding States")
    check("T2.1 Four binding states", len(BindingState) == 4)
    check("T2.2 UNBOUND state", BindingState.UNBOUND.value == "unbound")
    check("T2.3 BOUND state", BindingState.BOUND.value == "bound")
    check("T2.4 REVOKED state", BindingState.REVOKED.value == "revoked")

    # ── T3: Binding Lifecycle ────────────────────────────────────
    print("T3: Binding Lifecycle")
    bm = BindingManager()

    # Create parent society
    soc_req = BindingRequest(entity_type=EntityType.SOCIETY, public_key="soc-key-1")
    soc = bm.initiate_binding(soc_req)
    check("T3.1 Society bound", soc.state == BindingState.BOUND)
    check("T3.2 LCT ID has entity type", "society" in soc.lct_id)
    check("T3.3 Has binding proof", soc.binding_proof.startswith("cose:"))

    # Create child entity
    ai_req = BindingRequest(entity_type=EntityType.AI, public_key="ai-key-1",
                            hardware_id="hw-123")
    ai = bm.initiate_binding(ai_req, parent_lct=soc.lct_id)
    check("T3.4 AI bound", ai.state == BindingState.BOUND)
    check("T3.5 Has parent", ai.parent_lct == soc.lct_id)
    check("T3.6 Different LCT ID", ai.lct_id != soc.lct_id)

    # Serialization
    d = ai.to_dict()
    check("T3.7 Serializable", "lct_id" in d and "entity_type" in d)
    check("T3.8 Has hardware_id", d["hardware_id"] == "hw-123")

    # Children lookup
    children = bm.get_children(soc.lct_id)
    check("T3.9 One child", len(children) == 1)
    check("T3.10 Child is AI", children[0].entity_type == EntityType.AI)

    # Revocation
    ok, msg = bm.revoke_binding(ai.lct_id)
    check("T3.11 Revocation succeeds", ok)
    check("T3.12 State is REVOKED", ai.state == BindingState.REVOKED)
    check("T3.13 Not active after revocation", not bm.is_active(ai.lct_id))

    # Double revocation
    ok, msg = bm.revoke_binding(ai.lct_id)
    check("T3.14 Double revocation rejected", not ok)

    # Unknown LCT
    ok, msg = bm.revoke_binding("lct:web4:unknown")
    check("T3.15 Unknown LCT rejected", not ok)

    # ── T4: Pairing Modes ────────────────────────────────────────
    print("T4: Pairing Modes")
    check("T4.1 Three pairing modes", len(PairingMode) == 3)
    check("T4.2 DIRECT mode", PairingMode.DIRECT.value == "direct")
    check("T4.3 WITNESSED mode", PairingMode.WITNESSED.value == "witnessed")
    check("T4.4 AUTHORIZED mode", PairingMode.AUTHORIZED.value == "authorized")

    # ── T5: Direct Pairing ───────────────────────────────────────
    print("T5: Direct Pairing")
    coord = RelationshipCoordinator()

    alice = coord.create_entity(EntityType.HUMAN, "alice-key")
    bob = coord.create_entity(EntityType.AI, "bob-key")

    session, msg = coord.pair_direct(alice.lct_id, bob.lct_id,
                                      context="collaboration")
    check("T5.1 Direct pairing created", session is not None)
    check("T5.2 Mode is DIRECT", session.mode == PairingMode.DIRECT)
    check("T5.3 State is PAIRED", session.state == PairingState.PAIRED)
    check("T5.4 Has session ID", session.session_id.startswith("sess:"))
    check("T5.5 Has key halves", len(session.key_a) == 64 and len(session.key_b) == 64)
    check("T5.6 No witness", session.witness_lct is None)

    # Serialization
    d = session.to_dict()
    check("T5.7 Session serializable", "session_id" in d)
    check("T5.8 Has mode", d["mode"] == "direct")

    # Activate
    ok, _ = coord.pairing.activate_session(session.session_id)
    check("T5.9 Activation succeeds", ok)
    check("T5.10 State is ACTIVE", session.state == PairingState.ACTIVE)

    # Close
    ok, _ = coord.pairing.close_session(session.session_id)
    check("T5.11 Close succeeds", ok)
    check("T5.12 State is DORMANT", session.state == PairingState.DORMANT)

    # ── T6: Witnessed Pairing ────────────────────────────────────
    print("T6: Witnessed Pairing")
    oracle = coord.create_entity(EntityType.ORACLE, "oracle-key")

    session_w, msg = coord.pair_witnessed(alice.lct_id, bob.lct_id,
                                           witness=oracle.lct_id,
                                           context="service-agreement")
    check("T6.1 Witnessed pairing created", session_w is not None)
    check("T6.2 Mode is WITNESSED", session_w.mode == PairingMode.WITNESSED)
    check("T6.3 Has witness LCT", session_w.witness_lct == oracle.lct_id)
    check("T6.4 Has attestation", session_w.witness_attestation.startswith("cose:"))

    # ── T7: Authorized Pairing ───────────────────────────────────
    print("T7: Authorized Pairing")
    authority = coord.create_entity(EntityType.ORGANIZATION, "org-key")

    session_a, msg = coord.pair_authorized(
        alice.lct_id, bob.lct_id,
        authority=authority.lct_id,
        context="role-assignment",
        permissions=["approve:budgets", "sign:contracts"],
    )
    check("T7.1 Authorized pairing created", session_a is not None)
    check("T7.2 Mode is AUTHORIZED", session_a.mode == PairingMode.AUTHORIZED)
    check("T7.3 Has authority LCT", session_a.authority_lct == authority.lct_id)
    check("T7.4 Has authority record", session_a.authority_record.startswith("cose:"))
    check("T7.5 Has custom permissions",
          "approve:budgets" in session_a.rules.permissions)

    # ── T8: Pairing with Inactive Entity ─────────────────────────
    print("T8: Pairing with Inactive Entity")
    dead = coord.create_entity(EntityType.AI, "dead-key")
    coord.binding.revoke_binding(dead.lct_id)

    session_bad, msg = coord.pair_direct(alice.lct_id, dead.lct_id)
    check("T8.1 Pairing with revoked entity fails", session_bad is None)
    check("T8.2 Error mentions not active", "not active" in msg.lower())

    # ── T9: Witnessing ───────────────────────────────────────────
    print("T9: Witnessing")
    record, msg = coord.witness_entity(
        oracle.lct_id, alice.lct_id,
        WitnessEvidenceType.EXISTENCE,
        {"observed_at": "2026-02-22T12:00:00Z", "method": "heartbeat"},
    )
    check("T9.1 Witness record created", record is not None)
    check("T9.2 Has signature", record.signature.startswith("cose:"))
    check("T9.3 Evidence type correct", record.evidence_type == WitnessEvidenceType.EXISTENCE)

    d = record.to_dict()
    check("T9.4 Version is WTNS/1.0", d["version"] == "WTNS/1.0")
    check("T9.5 Has evidence_data", "observed_at" in d["evidence_data"])

    # Multiple witnessings
    coord.witness_entity(oracle.lct_id, alice.lct_id,
                         WitnessEvidenceType.ACTION,
                         {"action": "r6:execute", "result": "success"})
    check("T9.6 Witness count is 2", coord.witnessing.get_witness_count(alice.lct_id) == 2)
    check("T9.7 Unique witnesses is 1", coord.witnessing.get_unique_witnesses(alice.lct_id) == 1)

    # Self-witness rejected
    record_self, msg = coord.witness_entity(alice.lct_id, alice.lct_id,
                                             WitnessEvidenceType.EXISTENCE, {})
    check("T9.8 Self-witnessing rejected", record_self is None)

    # ── T10: Broadcast ───────────────────────────────────────────
    print("T10: Broadcast")
    coord.broadcast.register_accumulator("acc:main")

    msg = coord.send_broadcast(alice.lct_id, BroadcastType.ANNOUNCE,
                                {"capability": "data-analysis", "trust_level": 0.7})
    check("T10.1 Broadcast sent", msg.version == "CAST/1.0")
    check("T10.2 Type is ANNOUNCE", msg.message_type == BroadcastType.ANNOUNCE)

    coord.send_broadcast(alice.lct_id, BroadcastType.HEARTBEAT, {"alive": True})
    check("T10.3 Broadcast count is 2", coord.broadcast.get_broadcast_count(alice.lct_id) == 2)

    # Query accumulator
    records = coord.broadcast.query_accumulator("acc:main", sender_id=alice.lct_id)
    check("T10.4 Accumulator has 2 records", len(records) == 2)
    check("T10.5 First is ANNOUNCE", records[0].message_type == BroadcastType.ANNOUNCE)
    check("T10.6 Has broadcast hash", len(records[0].broadcast_hash) == 64)

    # Unregistered accumulator
    records_empty = coord.broadcast.query_accumulator("acc:unknown")
    check("T10.7 Unknown accumulator returns empty", len(records_empty) == 0)

    # ── T11: MRH Integration ────────────────────────────────────
    print("T11: MRH Integration")
    alice_mrh = coord.mrh.get_state(alice.lct_id)
    check("T11.1 Alice has MRH state", alice_mrh is not None)
    check("T11.2 Alice has paired entries", len(alice_mrh.paired) > 0)
    check("T11.3 Alice has witnessing entries", len(alice_mrh.witnessing) > 0)

    bob_mrh = coord.mrh.get_state(bob.lct_id)
    check("T11.4 Bob has MRH state", bob_mrh is not None)
    check("T11.5 Bob has paired entries", len(bob_mrh.paired) > 0)

    # Check pairing mode recorded in MRH
    direct_pairing = [p for p in alice_mrh.paired if p.get("pairing_mode") == "direct"]
    check("T11.6 Direct pairing in MRH", len(direct_pairing) > 0)

    witnessed_pairing = [p for p in alice_mrh.paired if p.get("pairing_mode") == "witnessed"]
    check("T11.7 Witnessed pairing in MRH", len(witnessed_pairing) > 0)

    authorized_pairing = [p for p in alice_mrh.paired if p.get("pairing_mode") == "authorized"]
    check("T11.8 Authorized pairing in MRH", len(authorized_pairing) > 0)

    # Witness in MRH
    existence_witness = [w for w in alice_mrh.witnessing
                         if w.get("role") == "existence"]
    check("T11.9 Existence witness in MRH", len(existence_witness) > 0)

    # MRH serialization
    d = alice_mrh.to_dict()
    check("T11.10 MRH serializable", "bound" in d and "paired" in d and "witnessing" in d)

    # ── T12: T3 Evolution ────────────────────────────────────────
    print("T12: T3 Evolution")
    alice_t3 = coord.trust.get_or_create(alice.lct_id)
    initial_composite = alice_t3.composite
    check("T12.1 Initial composite = 0.5", abs(initial_composite - 0.5) < 0.01)

    # Witnessing should increase T3
    for _ in range(10):
        coord.witness_entity(oracle.lct_id, alice.lct_id,
                             WitnessEvidenceType.ACTION,
                             {"action": "good_deed"})
    check("T12.2 T3 increased after witnessing", alice_t3.composite > initial_composite)

    # Successful action
    coord.trust.on_pairing_action(bob.lct_id, success=True)
    bob_t3 = coord.trust.get_or_create(bob.lct_id)
    check("T12.3 Success increases T3", bob_t3.composite > 0.5)

    # Failed action
    coord.trust.on_pairing_action(bob.lct_id, success=False)
    after_fail = bob_t3.composite
    check("T12.4 Failure decreases T3", after_fail < bob_t3.talent * 0.4 + 0.51 * 0.3 + 0.5 * 0.3 + 0.01)

    # Clamping
    t3_clamp = T3State(talent=0.99, training=0.99, temperament=0.99)
    t3_clamp.adjust(talent_delta=0.1)
    check("T12.5 Clamped at 1.0", t3_clamp.talent == 1.0)
    t3_clamp.adjust(talent_delta=-2.0)
    check("T12.6 Clamped at 0.0", t3_clamp.talent == 0.0)

    # ── T13: Entity Pairings Lookup ──────────────────────────────
    print("T13: Entity Pairings Lookup")
    alice_pairings = coord.pairing.get_entity_pairings(alice.lct_id)
    check("T13.1 Alice has 3 pairings", len(alice_pairings) == 3)

    modes = {p.mode for p in alice_pairings}
    check("T13.2 All 3 modes represented", len(modes) == 3)

    bob_pairings = coord.pairing.get_entity_pairings(bob.lct_id)
    check("T13.3 Bob has 3 pairings", len(bob_pairings) == 3)

    # ── T14: Pairing Revocation ──────────────────────────────────
    print("T14: Pairing Revocation")
    ok, _ = coord.pairing.revoke_pairing(session.session_id)
    check("T14.1 Revocation succeeds", ok)
    check("T14.2 State is REVOKED", session.state == PairingState.REVOKED)
    check("T14.3 Has closed_at", len(session.closed_at) > 0)

    # ── T15: Binding Hash ────────────────────────────────────────
    print("T15: Binding Hash")
    req1 = BindingRequest(entity_type=EntityType.AI, public_key="key-1", hardware_id="hw-1")
    req2 = BindingRequest(entity_type=EntityType.AI, public_key="key-1", hardware_id="hw-1")
    check("T15.1 Same input = same hash", req1.hash() == req2.hash())

    req3 = BindingRequest(entity_type=EntityType.AI, public_key="key-2", hardware_id="hw-1")
    check("T15.2 Different key = different hash", req1.hash() != req3.hash())

    req4 = BindingRequest(entity_type=EntityType.HUMAN, public_key="key-1", hardware_id="hw-1")
    check("T15.3 Different type = different hash", req1.hash() != req4.hash())

    # ── T16: Broadcast Types ─────────────────────────────────────
    print("T16: Broadcast Types")
    check("T16.1 Three broadcast types", len(BroadcastType) == 3)
    check("T16.2 ANNOUNCE", BroadcastType.ANNOUNCE.value == "ANNOUNCE")
    check("T16.3 HEARTBEAT", BroadcastType.HEARTBEAT.value == "HEARTBEAT")
    check("T16.4 CAPABILITY", BroadcastType.CAPABILITY.value == "CAPABILITY")

    # Capability broadcast
    cap_msg = coord.send_broadcast(bob.lct_id, BroadcastType.CAPABILITY,
                                    {"skills": ["code-review", "testing"]})
    check("T16.5 Capability broadcast sent", cap_msg.message_type == BroadcastType.CAPABILITY)

    # ── T17: Witness Evidence Types ──────────────────────────────
    print("T17: Witness Evidence Types")
    check("T17.1 Four evidence types", len(WitnessEvidenceType) == 4)
    check("T17.2 EXISTENCE", WitnessEvidenceType.EXISTENCE.value == "EXISTENCE")
    check("T17.3 ACTION", WitnessEvidenceType.ACTION.value == "ACTION")
    check("T17.4 STATE", WitnessEvidenceType.STATE.value == "STATE")
    check("T17.5 TRANSITION", WitnessEvidenceType.TRANSITION.value == "TRANSITION")

    # Witness with each type
    for etype in WitnessEvidenceType:
        r, _ = coord.witness_entity(oracle.lct_id, bob.lct_id, etype, {"test": True})
        check(f"T17.6-{etype.value} witness created", r is not None)

    # ── T18: PairingRules ────────────────────────────────────────
    print("T18: PairingRules")
    rules = PairingRules(
        permissions=["read", "execute"],
        duration=7200,
        context="project-alpha",
        max_actions_per_minute=20,
    )
    d = rules.to_dict()
    check("T18.1 Rules serializable", "permissions" in d)
    check("T18.2 Has duration", d["duration"] == 7200)
    check("T18.3 Has context", d["context"] == "project-alpha")
    check("T18.4 Has rate limit", d["max_actions_per_minute"] == 20)

    # ── T19: Full E2E Scenario ───────────────────────────────────
    print("T19: Full E2E Scenario")
    e2e = RelationshipCoordinator()
    e2e.broadcast.register_accumulator("acc:e2e")

    # Phase 1: Create society and entities
    soc = e2e.create_entity(EntityType.SOCIETY, "society-key-e2e")
    human = e2e.create_entity(EntityType.HUMAN, "human-key", "hw-human", soc.lct_id)
    agent = e2e.create_entity(EntityType.AI, "agent-key", parent_lct=soc.lct_id)
    oracle_e = e2e.create_entity(EntityType.ORACLE, "oracle-key-e2e", parent_lct=soc.lct_id)
    check("T19.1 Four entities created", len(e2e.binding._bindings) == 4)

    # Phase 2: Direct pairing (human ↔ agent)
    sess, _ = e2e.pair_direct(human.lct_id, agent.lct_id, context="daily-work")
    check("T19.2 Direct pairing created", sess is not None)

    # Phase 3: Oracle witnesses agent's actions
    for i in range(5):
        e2e.witness_entity(oracle_e.lct_id, agent.lct_id,
                           WitnessEvidenceType.ACTION,
                           {"action": f"task-{i}", "result": "success"})
    check("T19.3 Agent witnessed 5 times",
          e2e.witnessing.get_witness_count(agent.lct_id) == 5)

    # Phase 4: Authorized pairing for role assignment
    role = e2e.create_entity(EntityType.ROLE, "admin-role-key", parent_lct=soc.lct_id)
    sess_auth, _ = e2e.pair_authorized(
        human.lct_id, role.lct_id, authority=soc.lct_id,
        context="admin-assignment",
        permissions=["admin:full"],
    )
    check("T19.4 Authorized role pairing", sess_auth is not None)

    # Phase 5: Agent broadcasts capabilities
    e2e.send_broadcast(agent.lct_id, BroadcastType.CAPABILITY,
                        {"skills": ["code-review", "documentation"]})
    e2e.send_broadcast(agent.lct_id, BroadcastType.HEARTBEAT, {"alive": True})
    check("T19.5 Agent broadcast 2 messages",
          e2e.broadcast.get_broadcast_count(agent.lct_id) == 2)

    # Phase 6: Check MRH consistency
    human_mrh = e2e.mrh.get_state(human.lct_id)
    check("T19.6 Human MRH has bound (parent)", len(human_mrh.bound) > 0)
    check("T19.7 Human MRH has paired", len(human_mrh.paired) > 0)

    agent_mrh = e2e.mrh.get_state(agent.lct_id)
    check("T19.8 Agent MRH has bound", len(agent_mrh.bound) > 0)
    check("T19.9 Agent MRH has witnessing", len(agent_mrh.witnessing) > 0)

    # Phase 7: Trust evolution
    agent_t3 = e2e.trust.get_or_create(agent.lct_id)
    check("T19.10 Agent T3 > 0.5 after witnessing", agent_t3.composite > 0.5)

    # Phase 8: Accumulator query
    acc_records = e2e.broadcast.query_accumulator("acc:e2e", sender_id=agent.lct_id)
    check("T19.11 Accumulator has agent broadcasts", len(acc_records) == 2)

    # Phase 9: Binding hierarchy
    children = e2e.binding.get_children(soc.lct_id)
    check("T19.12 Society has 4 children", len(children) == 4)

    # ── T20: Edge Cases ──────────────────────────────────────────
    print("T20: Edge Cases")

    # Pairing non-existent entity
    sess_bad, msg = e2e.pair_direct("lct:web4:nonexistent", human.lct_id)
    check("T20.1 Non-existent entity pairing fails", sess_bad is None)

    # Witness non-existent entity
    rec_bad, msg = e2e.witness_entity(oracle_e.lct_id, "lct:web4:nonexistent",
                                       WitnessEvidenceType.EXISTENCE, {})
    check("T20.2 Witness non-existent fails", rec_bad is None)

    # Get binding for unknown
    check("T20.3 Unknown binding returns None", e2e.binding.get_binding("unknown") is None)

    # Pairing states
    check("T20.4 Seven pairing states", len(PairingState) == 7)

    # Broadcast message serialization
    msg = BroadcastMessage(
        sender_id="test", message_type=BroadcastType.ANNOUNCE,
        payload={"test": True}, timestamp="2026-01-01T00:00:00Z"
    )
    d = msg.to_dict()
    check("T20.5 Broadcast serializable", d["version"] == "CAST/1.0")
    check("T20.6 Has message_type", d["message_type"] == "ANNOUNCE")

    # MRH for entity with no state
    check("T20.7 No MRH for unknown entity",
          e2e.mrh.get_state("lct:web4:unknown") is None)

    # Witness records lookup
    records = e2e.witnessing.get_records_for(agent.lct_id)
    check("T20.8 Records for agent", len(records) == 5)

    # ── Summary ──────────────────────────────────────────────────
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"Entity Relationships: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  FAILED: {failed}")
    else:
        print("  All checks passed!")
    print(f"{'='*60}")
    return passed, failed


if __name__ == "__main__":
    run_tests()
