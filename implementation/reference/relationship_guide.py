#!/usr/bin/env python3
"""
Web4 Entity Relationship Guide — Reference Implementation
Spec: web4-standard/RELATIONSHIP_GUIDE.md (486 lines)

Covers:
  4 Relationship Mechanisms:
    BINDING — Permanent identity attachment, hierarchical
    PAIRING — Authorized operational (Direct/Witnessed/Authorized modes)
    WITNESSING — Trust building through observation
    BROADCAST — Unidirectional discovery, accumulator witnessing
  Relationship Lifecycle Management (creation + termination patterns)
  Interaction Rules Matrix (11 entity types × 11)
  Pairing Mode Decision Tree
  4 Common Patterns (Org onboarding, Service discovery, Distributed task, Trust network)
  Security Considerations and Troubleshooting

Run:  python3 relationship_guide.py
"""

import time, hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum

# ─────────────────────────────────────────────
# Entity Types
# ─────────────────────────────────────────────

class EntityType(Enum):
    HUMAN = "human"
    AI = "ai"
    ORGANIZATION = "organization"
    ROLE = "role"
    TASK = "task"
    RESOURCE = "resource"
    DEVICE = "device"
    SERVICE = "service"
    ORACLE = "oracle"
    ACCUMULATOR = "accumulator"
    DICTIONARY = "dictionary"

# ─────────────────────────────────────────────
# Relationship Types
# ─────────────────────────────────────────────

class RelType(Enum):
    BINDING = "binding"
    PAIRING = "pairing"
    WITNESSING = "witnessing"
    BROADCAST = "broadcast"

class PairingMode(Enum):
    DIRECT = "DIRECT"           # Peer-to-peer, lowest latency
    WITNESSED = "WITNESSED"      # Notarized by third party
    AUTHORIZED = "AUTHORIZED"    # Mediated by authority

# ─────────────────────────────────────────────
# Interaction Rules Matrix (from spec)
# ─────────────────────────────────────────────

# B=Binding, P=Pairing, W=Witnessing, C=Broadcast collection
# Matrix: From → To → allowed relationship types
INTERACTION_MATRIX: Dict[str, Dict[str, Set[str]]] = {
    "human":        {"human": {"P","W"}, "ai": {"P","W"}, "organization": {"B","P"}, "role": {"P"}, "task": {"W"}, "resource": {"P","W"}, "device": {"B","P","W"}, "service": {"P","W"}, "oracle": {"W"}, "accumulator": set(), "dictionary": {"P","W"}},
    "ai":           {"human": {"P","W"}, "ai": {"P","W"}, "organization": {"B","P"}, "role": {"P"}, "task": {"W"}, "resource": {"P","W"}, "device": {"B","P","W"}, "service": {"P","W"}, "oracle": {"W"}, "accumulator": set(), "dictionary": {"P","W"}},
    "organization": {"human": {"B"}, "ai": {"B"}, "organization": {"P","W"}, "role": {"B"}, "task": {"B"}, "resource": {"B"}, "device": {"B"}, "service": {"B","P"}, "oracle": {"W"}, "accumulator": set(), "dictionary": {"B","P"}},
    "role":         {"human": set(), "ai": set(), "organization": set(), "role": {"B"}, "task": {"B"}, "resource": {"P"}, "device": set(), "service": {"P"}, "oracle": {"W"}, "accumulator": set(), "dictionary": {"P"}},
    "task":         {"human": set(), "ai": set(), "organization": set(), "role": set(), "task": {"W"}, "resource": {"P"}, "device": set(), "service": {"P"}, "oracle": {"W"}, "accumulator": set(), "dictionary": {"P"}},
    "resource":     {"human": set(), "ai": set(), "organization": set(), "role": set(), "task": set(), "resource": {"W"}, "device": {"P"}, "service": {"P"}, "oracle": {"W"}, "accumulator": set(), "dictionary": set()},
    "device":       {"human": {"W"}, "ai": {"W"}, "organization": set(), "role": set(), "task": {"W"}, "resource": {"W"}, "device": {"P","W"}, "service": {"P","W"}, "oracle": {"W"}, "accumulator": set(), "dictionary": {"P"}},
    "service":      {"human": set(), "ai": set(), "organization": set(), "role": set(), "task": set(), "resource": set(), "device": set(), "service": {"P","W"}, "oracle": {"W"}, "accumulator": set(), "dictionary": {"P"}},
    "oracle":       {"human": {"W"}, "ai": {"W"}, "organization": {"W"}, "role": {"W"}, "task": {"W"}, "resource": {"W"}, "device": {"W"}, "service": {"W"}, "oracle": {"W"}, "accumulator": set(), "dictionary": {"W"}},
    "accumulator":  {"human": {"C"}, "ai": {"C"}, "organization": {"C"}, "role": {"C"}, "task": {"C"}, "resource": {"C"}, "device": {"C"}, "service": {"C"}, "oracle": {"C"}, "accumulator": set(), "dictionary": {"C"}},
    "dictionary":   {"human": set(), "ai": set(), "organization": set(), "role": set(), "task": set(), "resource": set(), "device": set(), "service": set(), "oracle": set(), "accumulator": set(), "dictionary": {"P"}},
}

def is_allowed(from_type: str, to_type: str, rel: str) -> bool:
    """Check if relationship is allowed per interaction matrix"""
    return rel in INTERACTION_MATRIX.get(from_type, {}).get(to_type, set())

# ─────────────────────────────────────────────
# Core Entity
# ─────────────────────────────────────────────

@dataclass
class Entity:
    lct_id: str
    entity_type: EntityType
    public_key: str = ""
    mrh_bindings: List[Dict] = field(default_factory=list)
    mrh_pairings: List[Dict] = field(default_factory=list)
    mrh_witnessing: List[Dict] = field(default_factory=list)
    trust_score: float = 0.5

# ─────────────────────────────────────────────
# BINDING — Permanent Identity Attachment
# ─────────────────────────────────────────────

@dataclass
class BindingRecord:
    parent_lct: str
    child_lct: str
    entity_type: str
    hardware_id: str = ""
    timestamp: str = ""
    revoked: bool = False

class BindingManager:
    """Manages BINDING relationships per spec"""

    def __init__(self):
        self.bindings: List[BindingRecord] = []

    def create_binding(self, parent: Entity, child: Entity,
                       hardware_id: str = "") -> Optional[BindingRecord]:
        """Create permanent binding (hierarchical parent→child)"""
        # Validate per interaction matrix
        if not is_allowed(parent.entity_type.value, child.entity_type.value, "B"):
            return None

        record = BindingRecord(
            parent_lct=parent.lct_id,
            child_lct=child.lct_id,
            entity_type=child.entity_type.value,
            hardware_id=hardware_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        self.bindings.append(record)

        # Update both MRHs
        parent.mrh_bindings.append({"lct_id": child.lct_id, "type": "child", "ts": record.timestamp})
        child.mrh_bindings.append({"lct_id": parent.lct_id, "type": "parent", "ts": record.timestamp})
        return record

    def revoke_binding(self, parent_lct: str, child_lct: str) -> bool:
        """Revoke binding — propagates to children"""
        for b in self.bindings:
            if b.parent_lct == parent_lct and b.child_lct == child_lct and not b.revoked:
                b.revoked = True
                # Cascade revocation to children of child
                for cb in self.bindings:
                    if cb.parent_lct == child_lct and not cb.revoked:
                        self.revoke_binding(child_lct, cb.child_lct)
                return True
        return False

    def get_children(self, parent_lct: str) -> List[BindingRecord]:
        return [b for b in self.bindings if b.parent_lct == parent_lct and not b.revoked]

    def get_parent(self, child_lct: str) -> Optional[BindingRecord]:
        for b in self.bindings:
            if b.child_lct == child_lct and not b.revoked:
                return b
        return None

# ─────────────────────────────────────────────
# PAIRING — Authorized Operational Relationships
# ─────────────────────────────────────────────

@dataclass
class PairingRecord:
    lct_a: str
    lct_b: str
    mode: PairingMode
    context: str
    permissions: List[str] = field(default_factory=list)
    duration: int = 86400  # seconds
    witness: str = ""      # For WITNESSED mode
    authority: str = ""    # For AUTHORIZED mode
    session_key: str = ""
    active: bool = True
    created_at: float = 0.0
    performance_history: List[Dict] = field(default_factory=list)

class PairingManager:
    """Manages PAIRING relationships per spec (3 modes)"""

    def __init__(self):
        self.pairings: List[PairingRecord] = []

    def create_direct_pairing(self, a: Entity, b: Entity, context: str,
                              permissions: List[str] = None,
                              duration: int = 86400) -> Optional[PairingRecord]:
        """Direct pairing — peer-to-peer, no intermediary"""
        if not is_allowed(a.entity_type.value, b.entity_type.value, "P"):
            return None
        # Each generates half of session key
        half_a = hashlib.sha256(f"{a.lct_id}:{time.time()}".encode()).hexdigest()[:16]
        half_b = hashlib.sha256(f"{b.lct_id}:{time.time()}".encode()).hexdigest()[:16]
        session_key = half_a + half_b

        record = PairingRecord(
            lct_a=a.lct_id, lct_b=b.lct_id, mode=PairingMode.DIRECT,
            context=context, permissions=permissions or [],
            duration=duration, session_key=session_key,
            created_at=time.time()
        )
        self.pairings.append(record)
        a.mrh_pairings.append({"lct_id": b.lct_id, "context": context, "mode": "DIRECT"})
        b.mrh_pairings.append({"lct_id": a.lct_id, "context": context, "mode": "DIRECT"})
        return record

    def create_witnessed_pairing(self, a: Entity, b: Entity, witness: Entity,
                                 context: str, permissions: List[str] = None) -> Optional[PairingRecord]:
        """Witnessed pairing — notarized by third party"""
        if not is_allowed(a.entity_type.value, b.entity_type.value, "P"):
            return None
        session_key = hashlib.sha256(f"{a.lct_id}:{b.lct_id}:{witness.lct_id}".encode()).hexdigest()[:32]
        record = PairingRecord(
            lct_a=a.lct_id, lct_b=b.lct_id, mode=PairingMode.WITNESSED,
            context=context, permissions=permissions or [],
            witness=witness.lct_id, session_key=session_key,
            created_at=time.time()
        )
        self.pairings.append(record)
        a.mrh_pairings.append({"lct_id": b.lct_id, "context": context, "mode": "WITNESSED"})
        b.mrh_pairings.append({"lct_id": a.lct_id, "context": context, "mode": "WITNESSED"})
        return record

    def create_authorized_pairing(self, a: Entity, b: Entity, authority: Entity,
                                  context: str, permissions: List[str] = None) -> Optional[PairingRecord]:
        """Authorized pairing — mediated by authority"""
        if not is_allowed(a.entity_type.value, b.entity_type.value, "P"):
            return None
        # Authority generates and distributes keys
        session_key = hashlib.sha256(
            f"auth:{authority.lct_id}:{a.lct_id}:{b.lct_id}".encode()).hexdigest()[:32]
        record = PairingRecord(
            lct_a=a.lct_id, lct_b=b.lct_id, mode=PairingMode.AUTHORIZED,
            context=context, permissions=permissions or [],
            authority=authority.lct_id, session_key=session_key,
            created_at=time.time()
        )
        self.pairings.append(record)
        a.mrh_pairings.append({"lct_id": b.lct_id, "context": context, "mode": "AUTHORIZED"})
        b.mrh_pairings.append({"lct_id": a.lct_id, "context": context, "mode": "AUTHORIZED"})
        return record

    def terminate_pairing(self, lct_a: str, lct_b: str) -> bool:
        """Explicit session close"""
        for p in self.pairings:
            if p.lct_a == lct_a and p.lct_b == lct_b and p.active:
                p.active = False
                return True
        return False

    def get_active_pairings(self, lct_id: str) -> List[PairingRecord]:
        return [p for p in self.pairings
                if (p.lct_a == lct_id or p.lct_b == lct_id) and p.active]

# ─────────────────────────────────────────────
# WITNESSING — Trust Building Through Observation
# ─────────────────────────────────────────────

class EvidenceType(Enum):
    EXISTENCE = "EXISTENCE"     # Entity is present and active
    ACTION = "ACTION"           # Specific operation was performed
    STATE = "STATE"             # Current condition verification
    TRANSITION = "TRANSITION"   # State change confirmation

@dataclass
class WitnessAttestation:
    observer: str
    observed: str
    evidence_type: EvidenceType
    data: Dict[str, Any]
    signature: str = ""
    timestamp: str = ""

class WitnessingManager:
    """Manages WITNESSING relationships per spec"""

    def __init__(self):
        self.attestations: List[WitnessAttestation] = []

    def create_attestation(self, observer: Entity, observed: Entity,
                           evidence_type: EvidenceType,
                           data: Dict[str, Any]) -> Optional[WitnessAttestation]:
        """Create witness attestation"""
        if not is_allowed(observer.entity_type.value, observed.entity_type.value, "W"):
            return None

        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        att = WitnessAttestation(
            observer=observer.lct_id,
            observed=observed.lct_id,
            evidence_type=evidence_type,
            data={**data, "timestamp": ts,
                  "hash": hashlib.sha256(str(data).encode()).hexdigest()},
            signature=f"cose:{hashlib.sha256(f'{observer.lct_id}:{ts}'.encode()).hexdigest()[:16]}",
            timestamp=ts
        )
        self.attestations.append(att)

        # Bidirectional MRH update
        observer.mrh_witnessing.append({
            "lct_id": observed.lct_id, "role": "observer",
            "last_attestation": ts
        })
        observed.mrh_witnessing.append({
            "lct_id": observer.lct_id, "role": "witness",
            "last_attestation": ts
        })

        # Trust accumulation on observed entity
        observed.trust_score = min(1.0, observed.trust_score + 0.01)
        return att

    def get_attestations_for(self, lct_id: str) -> List[WitnessAttestation]:
        return [a for a in self.attestations if a.observed == lct_id]

    def witness_count(self, lct_id: str) -> int:
        witnesses = set()
        for a in self.attestations:
            if a.observed == lct_id:
                witnesses.add(a.observer)
        return len(witnesses)

# ─────────────────────────────────────────────
# BROADCAST — Unidirectional Discovery
# ─────────────────────────────────────────────

@dataclass
class BroadcastMessage:
    sender_id: str
    message_type: str  # CAPABILITY, HEARTBEAT, STATE_UPDATE
    payload: Dict[str, Any]
    timestamp: str = ""

@dataclass
class AccumulatorRecord:
    entity_id: str
    broadcasts: List[BroadcastMessage] = field(default_factory=list)

class BroadcastManager:
    """Manages BROADCAST and Accumulator collection per spec"""

    def __init__(self):
        self.broadcasts: List[BroadcastMessage] = []
        self.accumulators: Dict[str, AccumulatorRecord] = {}

    def broadcast(self, sender: Entity, message_type: str, payload: Dict) -> BroadcastMessage:
        """Send broadcast — no acknowledgment, no MRH updates"""
        msg = BroadcastMessage(
            sender_id=sender.lct_id,
            message_type=message_type,
            payload=payload,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        self.broadcasts.append(msg)
        # Accumulators automatically collect
        for acc_id, acc in self.accumulators.items():
            acc.broadcasts.append(msg)
        return msg

    def register_accumulator(self, acc_id: str):
        self.accumulators[acc_id] = AccumulatorRecord(entity_id=acc_id)

    def query_accumulator(self, acc_id: str, sender_filter: str = "") -> Dict:
        """Query accumulator for broadcast history"""
        acc = self.accumulators.get(acc_id)
        if not acc:
            return {"broadcast_count": 0, "consistency_score": 0.0, "presence_confirmed": False}
        broadcasts = acc.broadcasts
        if sender_filter:
            broadcasts = [b for b in broadcasts if b.sender_id == sender_filter]
        count = len(broadcasts)
        return {
            "broadcast_count": count,
            "consistency_score": min(1.0, count / max(1, 10)),  # Normalized to 10
            "gaps": [],
            "presence_confirmed": count > 0
        }

# ─────────────────────────────────────────────
# Pairing Mode Decision Tree
# ─────────────────────────────────────────────

def select_pairing_mode(high_risk: bool, compliance_required: bool,
                        both_trusted: bool) -> PairingMode:
    """Decision tree per spec §Pairing Mode Decision Tree"""
    if high_risk:
        return PairingMode.AUTHORIZED
    if compliance_required:
        return PairingMode.WITNESSED
    if both_trusted:
        return PairingMode.DIRECT
    return PairingMode.WITNESSED  # Default

# ─────────────────────────────────────────────
# Common Patterns
# ─────────────────────────────────────────────

class OrganizationOnboarding:
    """Pattern 1: Org onboarding per spec"""

    def __init__(self, binding_mgr: BindingManager, pairing_mgr: PairingManager,
                 witness_mgr: WitnessingManager):
        self.binding = binding_mgr
        self.pairing = pairing_mgr
        self.witness = witness_mgr

    def onboard(self, org: Entity, departments: List[Entity],
                roles: List[Tuple[Entity, Entity]],
                agents: List[Tuple[Entity, Entity]]) -> Dict[str, int]:
        """
        org → departments (bind)
        departments → roles (bind)
        agents → roles (pair)
        """
        counts = {"bindings": 0, "pairings": 0}
        for dept in departments:
            if self.binding.create_binding(org, dept):
                counts["bindings"] += 1
        for dept, role in roles:
            if self.binding.create_binding(dept, role):
                counts["bindings"] += 1
        for agent, role in agents:
            if self.pairing.create_direct_pairing(agent, role, "role_assignment"):
                counts["pairings"] += 1
        return counts

class ServiceDiscoveryPattern:
    """Pattern 2: Service discovery per spec"""

    def __init__(self, broadcast_mgr: BroadcastManager, pairing_mgr: PairingManager):
        self.broadcast = broadcast_mgr
        self.pairing = pairing_mgr

    def discover_and_pair(self, service: Entity, client: Entity,
                          acc_id: str) -> Optional[PairingRecord]:
        """Service broadcasts → accumulator → client queries → pairing"""
        # Step 1: Service broadcasts
        self.broadcast.broadcast(service, "CAPABILITY", {
            "services": ["energy:supply"], "rate_atp": 5
        })
        # Step 2: Client queries accumulator
        result = self.broadcast.query_accumulator(acc_id, service.lct_id)
        if result["presence_confirmed"]:
            # Step 3: Client initiates pairing
            return self.pairing.create_direct_pairing(
                client, service, "service_consumption", ["data:read"]
            )
        return None

class TrustNetworkFormation:
    """Pattern 4: Trust network formation per spec"""

    def __init__(self, broadcast_mgr: BroadcastManager,
                 witness_mgr: WitnessingManager, pairing_mgr: PairingManager):
        self.broadcast = broadcast_mgr
        self.witness = witness_mgr
        self.pairing = pairing_mgr

    def form_trust(self, new_entity: Entity, witnesses: List[Entity],
                   min_trust_for_pairing: float = 0.55) -> Dict[str, Any]:
        """New entity → broadcast → witnessing → trust builds → pairing enabled"""
        # Step 1: Broadcast for discovery
        self.broadcast.broadcast(new_entity, "HEARTBEAT", {"status": "active"})

        # Step 2-3: Witnesses attest
        for w in witnesses:
            self.witness.create_attestation(w, new_entity, EvidenceType.EXISTENCE,
                                            {"verified": True})

        # Step 4: Trust score
        trust = new_entity.trust_score
        # Step 5: Enable pairing if trusted enough
        pairings_enabled = trust >= min_trust_for_pairing
        return {
            "trust_score": trust,
            "witness_count": self.witness.witness_count(new_entity.lct_id),
            "pairings_enabled": pairings_enabled
        }


# ═══════════════════════════════════════════════
# TEST SUITE
# ═══════════════════════════════════════════════

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    # ─── Interaction Rules Matrix ───
    print("Interaction Rules Matrix")

    check("T1.1 Human→AI: P,W", is_allowed("human", "ai", "P") and is_allowed("human", "ai", "W"))
    check("T1.2 Human→AI: no B", not is_allowed("human", "ai", "B"))
    check("T1.3 Org→Human: B only", is_allowed("organization", "human", "B"))
    check("T1.4 Org→Human: no P", not is_allowed("organization", "human", "P"))
    check("T1.5 Oracle→anything: W", all(
        is_allowed("oracle", t, "W") for t in ["human", "ai", "organization", "role", "task",
                                                 "resource", "device", "service", "oracle", "dictionary"]))
    check("T1.6 Accumulator→anything: C", all(
        is_allowed("accumulator", t, "C") for t in ["human", "ai", "organization", "role", "task",
                                                     "resource", "device", "service", "oracle", "dictionary"]))
    check("T1.7 Dictionary→Dictionary: P", is_allowed("dictionary", "dictionary", "P"))
    check("T1.8 Dictionary→Human: no interaction", not is_allowed("dictionary", "human", "P"))
    check("T1.9 Human→Device: B,P,W", is_allowed("human", "device", "B") and
          is_allowed("human", "device", "P") and is_allowed("human", "device", "W"))
    check("T1.10 Role→Task: B", is_allowed("role", "task", "B"))
    check("T1.11 Service→Service: P,W", is_allowed("service", "service", "P") and
          is_allowed("service", "service", "W"))

    # ─── BINDING ───
    print("BINDING")

    bm = BindingManager()
    org = Entity("lct:org:acme", EntityType.ORGANIZATION)
    dept = Entity("lct:dept:eng", EntityType.ROLE)  # Departments as roles
    role = Entity("lct:role:dev", EntityType.ROLE)
    human = Entity("lct:human:alice", EntityType.HUMAN)

    # Org→Role (B allowed)
    binding1 = bm.create_binding(org, dept)
    check("T2.1 Org→Role binding", binding1 is not None)
    check("T2.2 Parent LCT set", binding1.parent_lct == org.lct_id)
    check("T2.3 Child LCT set", binding1.child_lct == dept.lct_id)
    check("T2.4 Parent MRH updated", len(org.mrh_bindings) == 1)
    check("T2.5 Child MRH updated", len(dept.mrh_bindings) == 1)
    check("T2.6 Parent→child direction", org.mrh_bindings[0]["type"] == "child")
    check("T2.7 Child→parent direction", dept.mrh_bindings[0]["type"] == "parent")

    # Human→Human (B NOT allowed per matrix)
    human2 = Entity("lct:human:bob", EntityType.HUMAN)
    binding_bad = bm.create_binding(human, human2)
    check("T2.8 Human→Human binding rejected", binding_bad is None)

    # Hierarchical: Org→Dept→Role
    binding2 = bm.create_binding(dept, role)
    check("T2.9 Dept→Role binding", binding2 is not None)
    check("T2.10 Get children of org", len(bm.get_children(org.lct_id)) == 1)
    check("T2.11 Get parent of role", bm.get_parent(role.lct_id).parent_lct == dept.lct_id)

    # Revocation cascading
    bm.revoke_binding(org.lct_id, dept.lct_id)
    check("T2.12 Revocation", bm.bindings[0].revoked)
    check("T2.13 Cascade revocation", bm.bindings[1].revoked)
    check("T2.14 No active children after revoke", len(bm.get_children(org.lct_id)) == 0)

    # Hardware binding
    device = Entity("lct:device:hw01", EntityType.DEVICE)
    hw_binding = bm.create_binding(human, device, hardware_id="sha256:tpm_ek_001")
    check("T2.15 Hardware binding", hw_binding is not None)
    check("T2.16 Hardware ID stored", hw_binding.hardware_id == "sha256:tpm_ek_001")

    # ─── PAIRING ───
    print("PAIRING")

    pm = PairingManager()
    alice = Entity("lct:human:alice", EntityType.HUMAN)
    ai_agent = Entity("lct:ai:claude", EntityType.AI)
    oracle_ent = Entity("lct:oracle:notary", EntityType.ORACLE)
    org_hr = Entity("lct:org:hr", EntityType.ORGANIZATION)
    role_cfo = Entity("lct:role:cfo", EntityType.ROLE)

    # Direct pairing
    dp = pm.create_direct_pairing(alice, ai_agent, "collaboration", ["read", "write"])
    check("T3.1 Direct pairing created", dp is not None)
    check("T3.2 Mode = DIRECT", dp.mode == PairingMode.DIRECT)
    check("T3.3 Session key generated", len(dp.session_key) == 32)
    check("T3.4 Permissions set", "read" in dp.permissions)
    check("T3.5 Alice MRH updated", len(alice.mrh_pairings) == 1)
    check("T3.6 AI MRH updated", len(ai_agent.mrh_pairings) == 1)

    # Witnessed pairing
    org_ent = Entity("lct:org:acme2", EntityType.ORGANIZATION)
    service = Entity("lct:service:api", EntityType.SERVICE)
    wp = pm.create_witnessed_pairing(org_ent, service, oracle_ent,
                                     "service_agreement", ["query"])
    check("T3.7 Witnessed pairing created", wp is not None)
    check("T3.8 Mode = WITNESSED", wp.mode == PairingMode.WITNESSED)
    check("T3.9 Witness recorded", wp.witness == oracle_ent.lct_id)

    # Authorized pairing
    ap = pm.create_authorized_pairing(alice, role_cfo, org_hr,
                                      "role_assignment", ["approve:budgets"])
    check("T3.10 Authorized pairing created", ap is not None)
    check("T3.11 Mode = AUTHORIZED", ap.mode == PairingMode.AUTHORIZED)
    check("T3.12 Authority recorded", ap.authority == org_hr.lct_id)

    # Termination
    check("T3.13 Active pairings for alice", len(pm.get_active_pairings(alice.lct_id)) == 2)
    term = pm.terminate_pairing(alice.lct_id, ai_agent.lct_id)
    check("T3.14 Termination succeeds", term)
    check("T3.15 Active pairings reduced", len(pm.get_active_pairings(alice.lct_id)) == 1)

    # Invalid pairing (Dictionary→Human not allowed)
    dict_ent = Entity("lct:dict:en", EntityType.DICTIONARY)
    invalid_pair = pm.create_direct_pairing(dict_ent, alice, "translate")
    check("T3.16 Invalid pairing rejected", invalid_pair is None)

    # ─── WITNESSING ───
    print("WITNESSING")

    wm = WitnessingManager()
    oracle = Entity("lct:oracle:time", EntityType.ORACLE)
    task = Entity("lct:task:analysis", EntityType.TASK, trust_score=0.5)

    att = wm.create_attestation(oracle, task, EvidenceType.ACTION,
                                {"action": "data_processed"})
    check("T4.1 Attestation created", att is not None)
    check("T4.2 Observer recorded", att.observer == oracle.lct_id)
    check("T4.3 Observed recorded", att.observed == task.lct_id)
    check("T4.4 Evidence type", att.evidence_type == EvidenceType.ACTION)
    check("T4.5 Signature present", att.signature.startswith("cose:"))
    check("T4.6 Hash in data", "hash" in att.data)
    check("T4.7 Oracle MRH updated", len(oracle.mrh_witnessing) == 1)
    check("T4.8 Task MRH updated", len(task.mrh_witnessing) == 1)
    check("T4.9 Trust increased", task.trust_score > 0.5)

    # Multiple witnesses
    oracle2 = Entity("lct:oracle:audit", EntityType.ORACLE)
    wm.create_attestation(oracle2, task, EvidenceType.STATE, {"verified": True})
    check("T4.10 Multiple attestations", len(wm.get_attestations_for(task.lct_id)) == 2)
    check("T4.11 Unique witness count = 2", wm.witness_count(task.lct_id) == 2)
    check("T4.12 Trust accumulates", task.trust_score > 0.51)

    # 4 evidence types
    for ev_type in EvidenceType:
        att_ev = wm.create_attestation(oracle, task, ev_type, {"test": True})
        check(f"T4.{12 + list(EvidenceType).index(ev_type) + 1} Evidence type {ev_type.value}",
              att_ev is not None)

    # Invalid witnessing (Human→Accumulator not allowed)
    acc_entity = Entity("lct:acc:main", EntityType.ACCUMULATOR)
    invalid_wit = wm.create_attestation(human, acc_entity, EvidenceType.EXISTENCE, {})
    check("T4.17 Invalid witnessing rejected", invalid_wit is None)

    # ─── BROADCAST ───
    print("BROADCAST")

    bcast = BroadcastManager()
    bcast.register_accumulator("acc:main")
    service2 = Entity("lct:service:energy", EntityType.SERVICE)

    msg = bcast.broadcast(service2, "CAPABILITY", {"services": ["energy:supply"], "rate_atp": 5})
    check("T5.1 Broadcast sent", msg is not None)
    check("T5.2 Message type", msg.message_type == "CAPABILITY")
    check("T5.3 Timestamp set", len(msg.timestamp) > 0)

    # Heartbeat broadcasts
    for _ in range(5):
        bcast.broadcast(service2, "HEARTBEAT", {"status": "active"})

    # Query accumulator
    acc_result = bcast.query_accumulator("acc:main", service2.lct_id)
    check("T5.4 Accumulator collected", acc_result["broadcast_count"] == 6)
    check("T5.5 Presence confirmed", acc_result["presence_confirmed"])
    check("T5.6 Consistency score > 0", acc_result["consistency_score"] > 0)

    # Query nonexistent accumulator
    no_acc = bcast.query_accumulator("acc:nonexistent")
    check("T5.7 Missing accumulator: count=0", no_acc["broadcast_count"] == 0)
    check("T5.8 Missing accumulator: not confirmed", not no_acc["presence_confirmed"])

    # No MRH updates from broadcasts (spec: broadcasts don't update MRH)
    check("T5.9 No MRH updates from broadcast", len(service2.mrh_bindings) == 0)
    check("T5.10 No witnessing MRH from broadcast", len(service2.mrh_witnessing) == 0)

    # ─── Pairing Mode Decision Tree ───
    print("Pairing Mode Decision Tree")

    check("T6.1 High risk → AUTHORIZED", select_pairing_mode(True, False, True) == PairingMode.AUTHORIZED)
    check("T6.2 Compliance → WITNESSED", select_pairing_mode(False, True, True) == PairingMode.WITNESSED)
    check("T6.3 Both trusted → DIRECT", select_pairing_mode(False, False, True) == PairingMode.DIRECT)
    check("T6.4 Default → WITNESSED", select_pairing_mode(False, False, False) == PairingMode.WITNESSED)

    # ─── Common Patterns ───
    print("Common Patterns")

    # Pattern 1: Organization Onboarding
    bm2 = BindingManager()
    pm2 = PairingManager()
    wm2 = WitnessingManager()
    onboard = OrganizationOnboarding(bm2, pm2, wm2)

    org2 = Entity("lct:org:test", EntityType.ORGANIZATION)
    dept1 = Entity("lct:role:dept1", EntityType.ROLE)
    dept2 = Entity("lct:role:dept2", EntityType.ROLE)
    role1 = Entity("lct:role:eng", EntityType.ROLE)
    agent1 = Entity("lct:ai:bot1", EntityType.AI)

    counts = onboard.onboard(org2, [dept1, dept2],
                             [(dept1, role1)],
                             [(agent1, role1)])
    check("T7.1 Onboarding bindings", counts["bindings"] == 3)  # 2 depts + 1 role
    check("T7.2 Onboarding pairings", counts["pairings"] == 1)  # 1 agent→role

    # Pattern 2: Service Discovery
    bcast2 = BroadcastManager()
    bcast2.register_accumulator("acc:1")
    pm3 = PairingManager()
    sdp = ServiceDiscoveryPattern(bcast2, pm3)

    svc = Entity("lct:service:energy", EntityType.SERVICE)
    client = Entity("lct:human:client", EntityType.HUMAN)
    pairing = sdp.discover_and_pair(svc, client, "acc:1")
    check("T7.3 Service discovery → pairing", pairing is not None)
    check("T7.4 Pairing context", pairing.context == "service_consumption")

    # Pattern 4: Trust Network Formation
    bcast3 = BroadcastManager()
    bcast3.register_accumulator("acc:2")
    wm3 = WitnessingManager()
    pm4 = PairingManager()
    tnf = TrustNetworkFormation(bcast3, wm3, pm4)

    new_ent = Entity("lct:ai:newcomer", EntityType.AI, trust_score=0.5)
    witnesses = [
        Entity("lct:oracle:w1", EntityType.ORACLE),
        Entity("lct:oracle:w2", EntityType.ORACLE),
        Entity("lct:oracle:w3", EntityType.ORACLE),
        Entity("lct:oracle:w4", EntityType.ORACLE),
        Entity("lct:oracle:w5", EntityType.ORACLE),
        Entity("lct:oracle:w6", EntityType.ORACLE),
    ]
    trust_result = tnf.form_trust(new_ent, witnesses)
    check("T7.5 Trust score increased", trust_result["trust_score"] > 0.5)
    check("T7.6 6 witnesses counted", trust_result["witness_count"] == 6)
    check("T7.7 Pairings enabled", trust_result["pairings_enabled"])

    # Low trust: not enough witnesses
    lonely = Entity("lct:ai:lonely", EntityType.AI, trust_score=0.5)
    lone_result = tnf.form_trust(lonely, [])
    check("T7.8 No witnesses: trust unchanged", lone_result["trust_score"] == 0.5)
    check("T7.9 No witnesses: pairings not enabled", not lone_result["pairings_enabled"])

    # ─── Security Considerations ───
    print("Security Considerations")

    # BINDING security: revocation propagation
    bm3 = BindingManager()
    org3 = Entity("lct:org:secure", EntityType.ORGANIZATION)
    child1 = Entity("lct:role:c1", EntityType.ROLE)
    child2 = Entity("lct:role:c2", EntityType.ROLE)
    bm3.create_binding(org3, child1)
    bm3.create_binding(child1, child2)
    bm3.revoke_binding(org3.lct_id, child1.lct_id)
    check("T8.1 Revocation cascades to grandchildren", bm3.bindings[1].revoked)

    # PAIRING security: context-specific
    pm5 = PairingManager()
    h = Entity("lct:human:h", EntityType.HUMAN)
    a = Entity("lct:ai:a", EntityType.AI)
    p1 = pm5.create_direct_pairing(h, a, "data-exchange", ["read"])
    check("T8.2 Context-specific permissions", p1.context == "data-exchange")
    check("T8.3 Limited permissions", p1.permissions == ["read"])

    # WITNESSING security: signatures present
    wm4 = WitnessingManager()
    o = Entity("lct:oracle:sec", EntityType.ORACLE)
    t = Entity("lct:task:sec", EntityType.TASK)
    att_sec = wm4.create_attestation(o, t, EvidenceType.ACTION, {"action": "verified"})
    check("T8.4 Signature on attestation", len(att_sec.signature) > 0)
    check("T8.5 Hash on attestation", len(att_sec.data["hash"]) == 64)  # SHA-256

    # BROADCAST security: signed broadcasts
    bm4 = BroadcastManager()
    b = bm4.broadcast(Entity("lct:s:s", EntityType.SERVICE), "HEARTBEAT", {"status": "ok"})
    check("T8.6 Broadcast has timestamp", len(b.timestamp) > 0)
    check("T8.7 Broadcast has sender", len(b.sender_id) > 0)

    # ─── Lifecycle Termination ───
    print("Lifecycle Termination")

    # PAIRING: explicit termination
    pm6 = PairingManager()
    e1 = Entity("lct:h:1", EntityType.HUMAN)
    e2 = Entity("lct:ai:2", EntityType.AI)
    pm6.create_direct_pairing(e1, e2, "temp")
    check("T9.1 Pairing active", pm6.get_active_pairings(e1.lct_id)[0].active)
    pm6.terminate_pairing(e1.lct_id, e2.lct_id)
    check("T9.2 Pairing terminated", len(pm6.get_active_pairings(e1.lct_id)) == 0)

    # WITNESSING: no explicit termination (historical attestations permanent)
    check("T9.3 Attestations persist", len(wm.attestations) > 0)

    # ─── Summary ───
    print()
    print("=" * 60)
    if failed == 0:
        print(f"Relationship Guide: {passed}/{total} checks passed")
        print("  All checks passed!")
    else:
        print(f"Relationship Guide: {passed}/{total} checks passed, {failed} FAILED")
    print("=" * 60)
    return failed == 0

if __name__ == "__main__":
    run_tests()
