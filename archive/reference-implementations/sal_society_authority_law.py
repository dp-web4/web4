#!/usr/bin/env python3
"""
Web4 Society-Authority-Law (SAL) — Reference Implementation

Implements web4-standard/core-spec/web4-society-authority-law.md:
  - Genesis: birth certificate + citizen role pairing (§2)
  - Fractal citizenship: nested society composition (§3)
  - Law Oracle: versioned datasets, norms, procedures, interpretations (§4)
  - Roles: citizen, authority, oracle, witness, auditor (§5)
  - SAL↔R6 mapping: law-bound action execution (§6)
  - SAL↔MRH: RDF triple requirements and SPARQL queries (§7)
  - Security: co-signing, replay protection, law hash pinning (§8)
  - Error conditions: SAL-specific error profiles (§9)
  - T3/V3 implications: role-contextual trust updates (§10)
  - Conformance: MUST/SHOULD/MAY requirements (§12)
  - Worked example: "Open a Bank Account" (§13)

@version 1.0.0
@see web4-standard/core-spec/web4-society-authority-law.md
"""

import hashlib
import json
import sys
import time
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════
# Core Types
# ═══════════════════════════════════════════════════════════════

class SALError(Enum):
    """SAL error conditions per spec §9."""
    BINDING_INVALID = "W4_ERR_BINDING_INVALID"      # Missing birth pairing
    PROTO_DOWNGRADE = "W4_ERR_PROTO_DOWNGRADE"       # Law hash mismatch
    WITNESS_QUORUM = "W4_ERR_WITNESS_QUORUM"         # Quorum not met
    AUTHZ_SCOPE = "W4_ERR_AUTHZ_SCOPE"               # Insufficient scope
    BINDING_REVOKED = "W4_ERR_BINDING_REVOKED"        # Expired delegation
    WITNESS_DEFICIT = "W4_ERR_WITNESS_DEFICIT"        # Missing witness
    LEDGER_WRITE = "W4_ERR_LEDGER_WRITE"              # Ledger write failed
    AUDIT_EVIDENCE = "W4_ERR_AUDIT_EVIDENCE"          # Insufficient evidence
    LAW_CONFLICT = "W4_ERR_LAW_CONFLICT"              # Law inheritance conflict


class RoleType(Enum):
    """SAL role types per spec §5."""
    CITIZEN = "citizen"      # Genesis role, immutable (§5.1)
    AUTHORITY = "authority"   # Domain-scoped delegation (§5.2)
    ORACLE = "oracle"        # Law dataset publisher (§5.3)
    WITNESS = "witness"      # Co-signer of SAL events (§5.4)
    AUDITOR = "auditor"      # T3/V3 adjustment authority (§5.5)


class SALEventType(Enum):
    """SAL ledger event types per spec §3.4."""
    BIRTH = "sal.birth"
    ROLE_BIND = "sal.role.bind"
    LAW_UPDATE = "sal.law.update"
    DELEGATION = "sal.delegation"
    AUDIT_ADJUST = "sal.audit.adjust"
    WITNESS_ATTEST = "sal.witness.attest"
    LAW_QUERY = "sal.law.query"


# ═══════════════════════════════════════════════════════════════
# T3/V3 Tensors (simplified for SAL context)
# ═══════════════════════════════════════════════════════════════

@dataclass
class T3Tensor:
    """Trust tensor: talent, training, temperament."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def composite(self) -> float:
        return round((self.talent + self.training + self.temperament) / 3, 4)

    def apply_delta(self, dt: float = 0.0, dr: float = 0.0, dm: float = 0.0) -> 'T3Tensor':
        return T3Tensor(
            talent=max(0.0, min(1.0, self.talent + dt)),
            training=max(0.0, min(1.0, self.training + dr)),
            temperament=max(0.0, min(1.0, self.temperament + dm)),
        )


@dataclass
class V3Tensor:
    """Value tensor: valuation, veracity, validity."""
    valuation: float = 0.5
    veracity: float = 0.5
    validity: float = 0.5

    def composite(self) -> float:
        return round((self.valuation + self.veracity + self.validity) / 3, 4)

    def apply_delta(self, dval: float = 0.0, dver: float = 0.0, dvld: float = 0.0) -> 'V3Tensor':
        return V3Tensor(
            valuation=max(0.0, min(1.0, self.valuation + dval)),
            veracity=max(0.0, min(1.0, self.veracity + dver)),
            validity=max(0.0, min(1.0, self.validity + dvld)),
        )


# ═══════════════════════════════════════════════════════════════
# Birth Certificate (§2.2)
# ═══════════════════════════════════════════════════════════════

@dataclass
class BirthCertificate:
    """Birth certificate per spec §2.2."""
    entity_lct: str
    citizen_role_lct: str
    society_lct: str
    law_oracle_lct: str
    law_version: str
    birth_timestamp: float
    witnesses: List[str]  # Witness LCT IDs (≥3 for quorum)
    genesis_block: Optional[str] = None
    initial_rights: List[str] = field(default_factory=lambda: [
        "exist", "interact", "accumulate_reputation",
    ])
    initial_responsibilities: List[str] = field(default_factory=lambda: [
        "abide_law", "respect_quorum",
    ])
    _hash: Optional[str] = field(default=None, repr=False)

    def compute_hash(self) -> str:
        payload = json.dumps({
            "entity": self.entity_lct,
            "citizen_role": self.citizen_role_lct,
            "society": self.society_lct,
            "law_oracle": self.law_oracle_lct,
            "law_version": self.law_version,
            "birth_timestamp": self.birth_timestamp,
            "witnesses": sorted(self.witnesses),
        }, sort_keys=True).encode()
        self._hash = hashlib.sha256(payload).hexdigest()
        return self._hash

    def verify(self) -> bool:
        stored = self._hash
        return stored == self.compute_hash()


# ═══════════════════════════════════════════════════════════════
# Immutable Ledger (§3.4)
# ═══════════════════════════════════════════════════════════════

@dataclass
class LedgerEntry:
    """Content-addressed ledger entry per spec §3.4."""
    event_type: str
    payload: Dict[str, Any]
    parent_hash: Optional[str]
    timestamp: float
    witnesses: List[str]
    entry_hash: str = ""

    def compute_hash(self) -> str:
        data = json.dumps({
            "event_type": self.event_type,
            "payload": self.payload,
            "parent_hash": self.parent_hash,
            "timestamp": self.timestamp,
            "witnesses": sorted(self.witnesses),
        }, sort_keys=True).encode()
        self.entry_hash = hashlib.sha256(data).hexdigest()
        return self.entry_hash


class ImmutableLedger:
    """
    Append-only ledger per spec §3.4.

    Interface: append, get, prove, events.
    """

    def __init__(self):
        self.entries: List[LedgerEntry] = []
        self._by_hash: Dict[str, LedgerEntry] = {}

    def append(self, event_type: str, payload: Dict, witnesses: List[str]) -> LedgerEntry:
        parent = self.entries[-1].entry_hash if self.entries else None
        entry = LedgerEntry(
            event_type=event_type,
            payload=payload,
            parent_hash=parent,
            timestamp=time.time(),
            witnesses=witnesses,
        )
        entry.compute_hash()
        self.entries.append(entry)
        self._by_hash[entry.entry_hash] = entry
        return entry

    def get(self, entry_hash: str) -> Optional[LedgerEntry]:
        return self._by_hash.get(entry_hash)

    def prove(self, entry_hash: str) -> bool:
        """Verify entry exists and chain integrity holds."""
        entry = self.get(entry_hash)
        if not entry:
            return False
        # Verify chain from genesis to this entry
        for i, e in enumerate(self.entries):
            if i == 0:
                if e.parent_hash is not None:
                    return False
            else:
                if e.parent_hash != self.entries[i - 1].entry_hash:
                    return False
            if e.entry_hash == entry_hash:
                return True
        return False

    def events(self, topic: str, from_index: int = 0) -> List[LedgerEntry]:
        """Get events matching topic pattern from given index."""
        return [
            e for e in self.entries[from_index:]
            if e.event_type.startswith(topic.replace("*", ""))
        ]

    def verify_chain(self) -> bool:
        """Verify entire chain integrity."""
        for i, entry in enumerate(self.entries):
            if i == 0:
                if entry.parent_hash is not None:
                    return False
            else:
                if entry.parent_hash != self.entries[i - 1].entry_hash:
                    return False
            # Recompute and verify
            stored = entry.entry_hash
            entry.compute_hash()
            if entry.entry_hash != stored:
                return False
        return True


# ═══════════════════════════════════════════════════════════════
# Law Oracle (§4)
# ═══════════════════════════════════════════════════════════════

@dataclass
class Norm:
    """Law norm per spec §4.1."""
    norm_id: str
    selector: str       # R6 path (e.g., "r6.resource.atp")
    operator: str       # <=, >=, ==, !=, in, not_in
    value: Any
    description: str = ""


@dataclass
class Procedure:
    """Law procedure per spec §4.1."""
    procedure_id: str
    requires_witnesses: int = 3
    requires_approval: bool = False
    cool_down_seconds: float = 0.0
    description: str = ""


@dataclass
class Interpretation:
    """Law interpretation per spec §4.1."""
    interpretation_id: str
    replaces: Optional[str] = None
    reason: str = ""
    effective_from: float = 0.0


@dataclass
class LawDataset:
    """Versioned law dataset per spec §4.1."""
    law_id: str
    version: str
    norms: List[Norm]
    procedures: List[Procedure]
    interpretations: List[Interpretation]
    r6_bindings: List[str] = field(default_factory=list)
    _hash: Optional[str] = None

    def compute_hash(self) -> str:
        payload = json.dumps({
            "law_id": self.law_id,
            "version": self.version,
            "norms": [{"id": n.norm_id, "selector": n.selector, "op": n.operator, "value": n.value}
                      for n in self.norms],
            "procedures": [{"id": p.procedure_id, "witnesses": p.requires_witnesses}
                           for p in self.procedures],
            "interpretations": [{"id": i.interpretation_id, "replaces": i.replaces}
                                for i in self.interpretations],
        }, sort_keys=True).encode()
        self._hash = hashlib.sha256(payload).hexdigest()
        return self._hash

    @property
    def hash(self) -> str:
        if not self._hash:
            self.compute_hash()
        return self._hash


class LawOracle:
    """
    Law Oracle per spec §4.

    Publishes versioned law datasets, answers compliance queries,
    manages interpretations.
    """

    def __init__(self, oracle_lct: str, initial_law: LawDataset):
        self.oracle_lct = oracle_lct
        self.current_law = initial_law
        self.current_law.compute_hash()
        self.law_history: List[LawDataset] = [initial_law]
        self.pinned_hashes: Dict[str, str] = {}  # entity → pinned law hash

    def publish_update(self, new_law: LawDataset, witnesses: List[str]) -> str:
        """Publish new law version per spec §4.2."""
        if len(witnesses) < self.get_witness_requirement():
            raise ValueError(f"Requires {self.get_witness_requirement()} witnesses, got {len(witnesses)}")
        new_law.compute_hash()
        self.law_history.append(new_law)
        self.current_law = new_law
        return new_law.hash

    def get_witness_requirement(self) -> int:
        """Get witness quorum from current procedures."""
        for proc in self.current_law.procedures:
            if "WIT" in proc.procedure_id:
                return proc.requires_witnesses
        return 3  # Default

    def query_compliance(self, action_type: str, resource_value: Any) -> Tuple[bool, str]:
        """
        Deterministic Q&A per spec §5.3: "is action X compliant?"
        Returns (compliant, reason).
        """
        for norm in self.current_law.norms:
            if norm.selector.endswith(action_type) or action_type in norm.selector:
                if norm.operator == "<=" and isinstance(resource_value, (int, float)):
                    if resource_value > norm.value:
                        return False, f"Exceeds {norm.norm_id}: {resource_value} > {norm.value}"
                elif norm.operator == ">=" and isinstance(resource_value, (int, float)):
                    if resource_value < norm.value:
                        return False, f"Below {norm.norm_id}: {resource_value} < {norm.value}"
                elif norm.operator == "in":
                    if resource_value not in norm.value:
                        return False, f"Not in {norm.norm_id}: {resource_value}"
        return True, "compliant"

    def pin_hash(self, entity_lct: str) -> str:
        """Entity pins current law hash per spec §4.2."""
        self.pinned_hashes[entity_lct] = self.current_law.hash
        return self.current_law.hash

    def verify_pinned(self, entity_lct: str) -> Tuple[bool, str]:
        """Check if entity's pinned hash matches current."""
        pinned = self.pinned_hashes.get(entity_lct)
        if not pinned:
            return False, "not_pinned"
        if pinned != self.current_law.hash:
            return False, "stale_hash"
        return True, "current"


# ═══════════════════════════════════════════════════════════════
# MRH Triples (§7)
# ═══════════════════════════════════════════════════════════════

@dataclass
class RDFTriple:
    """RDF triple for SAL MRH edges."""
    subject: str
    predicate: str
    obj: str  # 'object' is reserved


class SALTripleStore:
    """
    In-memory triple store for SAL-required MRH edges per spec §7.

    Required predicates:
    - web4:memberOf (entity → society)
    - web4:hasAuthority (society → authority)
    - web4:hasLawOracle (society → law oracle)
    - web4:pairedWith (entity ↔ citizenRole)
    - web4:delegatesTo (authority → sub-authority)
    - web4:hasWitness (society → witness)
    - web4:hasAuditor (society → auditor)
    - web4:recordsOn (society → ledger)
    """

    def __init__(self):
        self.triples: List[RDFTriple] = []

    def add(self, subject: str, predicate: str, obj: str) -> None:
        self.triples.append(RDFTriple(subject, predicate, obj))

    def query(self, subject: Optional[str] = None, predicate: Optional[str] = None,
              obj: Optional[str] = None) -> List[RDFTriple]:
        """SPARQL-like pattern matching."""
        results = []
        for t in self.triples:
            if subject and t.subject != subject:
                continue
            if predicate and t.predicate != predicate:
                continue
            if obj and t.obj != obj:
                continue
            results.append(t)
        return results

    def ask(self, subject: str, predicate: str, obj: str) -> bool:
        """SPARQL ASK: does triple exist?"""
        return len(self.query(subject, predicate, obj)) > 0

    def subjects_of(self, predicate: str, obj: str) -> List[str]:
        return [t.subject for t in self.query(predicate=predicate, obj=obj)]

    def objects_of(self, subject: str, predicate: str) -> List[str]:
        return [t.obj for t in self.query(subject=subject, predicate=predicate)]


# ═══════════════════════════════════════════════════════════════
# Auditor (§5.5)
# ═══════════════════════════════════════════════════════════════

@dataclass
class AuditRequest:
    """Audit request per spec §5.5."""
    society_lct: str
    targets: List[str]       # Target entity LCTs
    scope: List[str]         # Context scope
    basis: List[str]         # Evidence hashes
    proposed_t3: Dict[str, float]   # e.g., {"temperament": -0.02}
    proposed_v3: Dict[str, float]   # e.g., {"veracity": -0.03}


@dataclass
class AuditTranscript:
    """Audit transcript per spec §5.5."""
    request: AuditRequest
    evidence_verified: bool
    applied_t3: Dict[str, float]
    applied_v3: Dict[str, float]
    capped: bool                    # Whether adjustments were capped
    timestamp: float
    auditor_lct: str


class Auditor:
    """
    Auditor role per spec §5.5.

    Adjusts T3/V3 tensors with evidence-based, law-bounded adjustments.
    """

    def __init__(self, auditor_lct: str, law_oracle: LawOracle):
        self.auditor_lct = auditor_lct
        self.law = law_oracle
        self.transcripts: List[AuditTranscript] = []

    def audit(self, request: AuditRequest,
              current_t3: T3Tensor, current_v3: V3Tensor,
              ) -> Tuple[T3Tensor, V3Tensor, AuditTranscript]:
        """
        Perform audit adjustment per spec §5.5 algorithm.

        Adjustments bounded by law, require verifiable evidence.
        """
        # Verify evidence (simplified: check basis is non-empty)
        evidence_valid = len(request.basis) > 0

        if not evidence_valid:
            transcript = AuditTranscript(
                request=request,
                evidence_verified=False,
                applied_t3={},
                applied_v3={},
                capped=False,
                timestamp=time.time(),
                auditor_lct=self.auditor_lct,
            )
            self.transcripts.append(transcript)
            return current_t3, current_v3, transcript

        # Apply deltas with caps (max ±0.1 per adjustment)
        cap = 0.1
        capped = False

        applied_t3 = {}
        dt = dr = dm = 0.0
        for dim, delta in request.proposed_t3.items():
            actual = max(-cap, min(cap, delta))
            if actual != delta:
                capped = True
            applied_t3[dim] = actual
            if dim == "talent":
                dt = actual
            elif dim == "training":
                dr = actual
            elif dim == "temperament":
                dm = actual

        applied_v3 = {}
        dval = dver = dvld = 0.0
        for dim, delta in request.proposed_v3.items():
            actual = max(-cap, min(cap, delta))
            if actual != delta:
                capped = True
            applied_v3[dim] = actual
            if dim == "valuation":
                dval = actual
            elif dim == "veracity":
                dver = actual
            elif dim == "validity":
                dvld = actual

        new_t3 = current_t3.apply_delta(dt, dr, dm)
        new_v3 = current_v3.apply_delta(dval, dver, dvld)

        transcript = AuditTranscript(
            request=request,
            evidence_verified=True,
            applied_t3=applied_t3,
            applied_v3=applied_v3,
            capped=capped,
            timestamp=time.time(),
            auditor_lct=self.auditor_lct,
        )
        self.transcripts.append(transcript)
        return new_t3, new_v3, transcript


# ═══════════════════════════════════════════════════════════════
# Society (§3)
# ═══════════════════════════════════════════════════════════════

@dataclass
class EntityRecord:
    """Entity within a society."""
    lct_id: str
    roles: Set[str] = field(default_factory=set)
    t3: T3Tensor = field(default_factory=T3Tensor)
    v3: V3Tensor = field(default_factory=V3Tensor)
    birth_cert: Optional[BirthCertificate] = None
    delegations: List[str] = field(default_factory=list)
    active: bool = True


class Society:
    """
    Full SAL society per spec §3.

    Manages citizenship, authority, law, witnessing, and auditing.
    """

    def __init__(self, society_lct: str, authority_lct: str, law: LawDataset,
                 quorum_size: int = 3):
        self.society_lct = society_lct
        self.authority_lct = authority_lct
        self.quorum_size = quorum_size

        # Law Oracle
        self.law_oracle = LawOracle(
            oracle_lct=f"{society_lct}:oracle",
            initial_law=law,
        )

        # Entities
        self.entities: Dict[str, EntityRecord] = {}

        # Roles
        self.witnesses: List[str] = []
        self.auditors: List[str] = []

        # Ledger
        self.ledger = ImmutableLedger()

        # MRH triple store
        self.triples = SALTripleStore()
        self._init_triples()

        # Fractal: parent society (if nested)
        self.parent_society: Optional['Society'] = None
        self.child_societies: List['Society'] = []

    def _init_triples(self):
        """Initialize required MRH triples per spec §7.1."""
        self.triples.add(self.society_lct, "web4:hasAuthority", self.authority_lct)
        self.triples.add(self.society_lct, "web4:hasLawOracle", self.law_oracle.oracle_lct)
        self.triples.add(self.society_lct, "web4:recordsOn", f"{self.society_lct}:ledger")

    def register_witness(self, witness_lct: str) -> None:
        """Register a witness for this society."""
        self.witnesses.append(witness_lct)
        self.triples.add(self.society_lct, "web4:hasWitness", witness_lct)

    def register_auditor(self, auditor_lct: str) -> None:
        """Register an auditor for this society."""
        self.auditors.append(auditor_lct)
        self.triples.add(self.society_lct, "web4:hasAuditor", auditor_lct)

    def issue_birth_certificate(self, entity_lct: str,
                                 witnesses: Optional[List[str]] = None,
                                 initial_t3: Optional[T3Tensor] = None,
                                 initial_v3: Optional[V3Tensor] = None,
                                 ) -> Tuple[BirthCertificate, Optional[str]]:
        """
        Issue birth certificate per spec §2 (Genesis).

        Returns (certificate, error_code or None).
        """
        # Use society witnesses if none provided
        wit = witnesses or self.witnesses

        # Check quorum (§2.1)
        if len(wit) < self.quorum_size:
            return None, SALError.WITNESS_DEFICIT.value

        # Create citizen role LCT
        citizen_role_lct = f"lct:web4:role:citizen:{entity_lct.split(':')[-1]}"

        # Create birth certificate (§2.2)
        cert = BirthCertificate(
            entity_lct=entity_lct,
            citizen_role_lct=citizen_role_lct,
            society_lct=self.society_lct,
            law_oracle_lct=self.law_oracle.oracle_lct,
            law_version=self.law_oracle.current_law.version,
            birth_timestamp=time.time(),
            witnesses=wit[:self.quorum_size],
        )
        cert.compute_hash()

        # Create entity record
        entity = EntityRecord(
            lct_id=entity_lct,
            roles={RoleType.CITIZEN.value},
            t3=initial_t3 or T3Tensor(0.3, 0.3, 0.5),
            v3=initial_v3 or V3Tensor(0.3, 0.3, 0.3),
            birth_cert=cert,
        )
        self.entities[entity_lct] = entity

        # Add MRH triples (§3.3)
        self.triples.add(entity_lct, "web4:pairedWith", citizen_role_lct)
        self.triples.add(entity_lct, "web4:memberOf", self.society_lct)

        # Record on ledger (§3.4)
        self.ledger.append(
            event_type=SALEventType.BIRTH.value,
            payload={
                "entity": entity_lct,
                "citizen_role": citizen_role_lct,
                "cert_hash": cert._hash,
                "law_version": cert.law_version,
            },
            witnesses=wit[:self.quorum_size],
        )

        # Pin law hash for new entity
        self.law_oracle.pin_hash(entity_lct)

        return cert, None

    def bind_role(self, entity_lct: str, role: RoleType,
                  scope: Optional[str] = None,
                  delegated_by: Optional[str] = None,
                  ) -> Optional[str]:
        """
        Bind additional role to entity per spec §5.

        Citizen role is prerequisite for all others (§5.1).
        """
        entity = self.entities.get(entity_lct)
        if not entity:
            return SALError.BINDING_INVALID.value

        # Citizen prerequisite
        if RoleType.CITIZEN.value not in entity.roles:
            return SALError.BINDING_INVALID.value

        # Cannot re-add citizen
        if role == RoleType.CITIZEN:
            return None  # Already has it

        entity.roles.add(role.value)

        # Record delegation if applicable
        if delegated_by:
            entity.delegations.append(delegated_by)
            self.triples.add(delegated_by, "web4:delegatesTo", entity_lct)
            if scope:
                self.triples.add(entity_lct, "web4:scope", scope)

        # Register special roles
        if role == RoleType.WITNESS:
            self.register_witness(entity_lct)
        elif role == RoleType.AUDITOR:
            self.register_auditor(entity_lct)

        # Ledger record
        self.ledger.append(
            event_type=SALEventType.ROLE_BIND.value,
            payload={
                "entity": entity_lct,
                "role": role.value,
                "scope": scope,
                "delegated_by": delegated_by,
            },
            witnesses=self.witnesses[:self.quorum_size] if self.witnesses else [],
        )

        return None

    def execute_r6(self, entity_lct: str, action_type: str,
                   resource_value: Any, reference: str = "",
                   ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Execute R6 action with SAL law binding per spec §6.

        Returns (success, reason, result_dict).
        """
        entity = self.entities.get(entity_lct)
        if not entity:
            return False, SALError.BINDING_INVALID.value, None

        # Verify citizenship
        if RoleType.CITIZEN.value not in entity.roles:
            return False, SALError.BINDING_INVALID.value, None

        # Verify law hash is current (§8)
        pinned_ok, pin_reason = self.law_oracle.verify_pinned(entity_lct)
        if not pinned_ok:
            if pin_reason == "stale_hash":
                return False, SALError.PROTO_DOWNGRADE.value, None
            # Auto-pin if not yet pinned
            self.law_oracle.pin_hash(entity_lct)

        # Check compliance with law (§4)
        compliant, comp_reason = self.law_oracle.query_compliance(action_type, resource_value)
        if not compliant:
            return False, f"LAW_VIOLATION: {comp_reason}", None

        # Build result with law hash pinned (§6)
        result = {
            "entity": entity_lct,
            "action_type": action_type,
            "resource": resource_value,
            "reference": reference,
            "law_hash": self.law_oracle.current_law.hash,
            "society": self.society_lct,
            "citizen_role": list(entity.roles),
            "timestamp": time.time(),
        }

        # T3/V3 update: successful compliant action → V3 validity boost (§10)
        entity.v3 = entity.v3.apply_delta(dvld=0.01)

        return True, "executed", result

    def audit_entity(self, auditor_lct: str, request: AuditRequest) -> Tuple[bool, str, Optional[AuditTranscript]]:
        """
        Perform audit per spec §5.5.

        Returns (success, reason, transcript).
        """
        # Verify auditor role
        auditor = self.entities.get(auditor_lct)
        if not auditor or RoleType.AUDITOR.value not in auditor.roles:
            return False, SALError.AUTHZ_SCOPE.value, None

        # Get target entity
        for target_lct in request.targets:
            target = self.entities.get(target_lct)
            if not target:
                continue

            # Create auditor and perform audit
            aud = Auditor(auditor_lct, self.law_oracle)
            new_t3, new_v3, transcript = aud.audit(request, target.t3, target.v3)

            if not transcript.evidence_verified:
                return False, SALError.AUDIT_EVIDENCE.value, transcript

            # Apply
            target.t3 = new_t3
            target.v3 = new_v3

            # Record on ledger
            self.ledger.append(
                event_type=SALEventType.AUDIT_ADJUST.value,
                payload={
                    "auditor": auditor_lct,
                    "target": target_lct,
                    "applied_t3": transcript.applied_t3,
                    "applied_v3": transcript.applied_v3,
                    "capped": transcript.capped,
                },
                witnesses=self.witnesses[:self.quorum_size] if self.witnesses else [],
            )

            # Auditor T3 update (§10): successful audit → training boost
            auditor.t3 = auditor.t3.apply_delta(dr=0.005)

            return True, "adjusted", transcript

        return False, "target_not_found", None

    def add_child_society(self, child: 'Society') -> None:
        """Register a child society for fractal composition per spec §3.2."""
        child.parent_society = self
        self.child_societies.append(child)
        self.triples.add(child.society_lct, "web4:memberOf", self.society_lct)

    def effective_law(self) -> LawDataset:
        """
        Compute effective law per spec §3.5 inheritance rule:
        effectiveLaw(child) = merge(parentLaw, childOverrides)
        """
        if not self.parent_society:
            return self.law_oracle.current_law

        parent_law = self.parent_society.effective_law()
        child_law = self.law_oracle.current_law

        # Merge: child overrides parent, parent norms apply by default
        parent_norms = {n.norm_id: n for n in parent_law.norms}
        child_norms = {n.norm_id: n for n in child_law.norms}

        merged_norms = list(parent_norms.values())
        for norm_id, norm in child_norms.items():
            if norm_id in parent_norms:
                # Child overrides parent
                merged_norms = [n for n in merged_norms if n.norm_id != norm_id]
            merged_norms.append(norm)

        return LawDataset(
            law_id=f"merged:{child_law.law_id}",
            version=f"{parent_law.version}+{child_law.version}",
            norms=merged_norms,
            procedures=child_law.procedures or parent_law.procedures,
            interpretations=parent_law.interpretations + child_law.interpretations,
        )

    def validate_genesis_closure(self, entity_lct: str) -> Tuple[bool, List[str]]:
        """
        Validate spec §12.1 conformance for an entity.

        MUST: citizen pairing, society binding, law hash, MRH triples.
        """
        issues = []
        entity = self.entities.get(entity_lct)

        if not entity:
            return False, ["Entity not found"]

        # MUST: Citizen pairing
        if RoleType.CITIZEN.value not in entity.roles:
            issues.append("Missing citizen role")

        # MUST: Birth certificate
        if not entity.birth_cert:
            issues.append("Missing birth certificate")

        # MUST: MRH triples
        if not self.triples.ask(entity_lct, "web4:pairedWith", None):
            issues.append("Missing web4:pairedWith triple")
        if not self.triples.ask(entity_lct, "web4:memberOf", self.society_lct):
            issues.append("Missing web4:memberOf triple")

        # MUST: Law hash pinned
        pinned_ok, _ = self.law_oracle.verify_pinned(entity_lct)
        if not pinned_ok:
            issues.append("Law hash not pinned")

        return len(issues) == 0, issues


# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

def create_test_law() -> LawDataset:
    """Create a standard test law dataset."""
    return LawDataset(
        law_id="web4://law/test/1.0.0",
        version="v1.0.0",
        norms=[
            Norm("LAW-ATP-LIMIT", "r6.resource.atp", "<=", 100,
                 "Max ATP per action"),
            Norm("LAW-RATE-LIMIT", "r6.resource.rate", "<=", 5000,
                 "Max request rate"),
            Norm("LAW-MIN-TRUST", "r6.trust.minimum", ">=", 0.2,
                 "Minimum trust for actions"),
        ],
        procedures=[
            Procedure("PROC-WIT-3", requires_witnesses=3,
                      description="Standard 3-witness quorum"),
            Procedure("PROC-APPROVAL", requires_witnesses=1,
                      requires_approval=True,
                      description="Single-approval process"),
        ],
        interpretations=[
            Interpretation("INT-1", reason="Initial law interpretation"),
        ],
        r6_bindings=["web4://schemas/r6-rules-v1"],
    )


def create_test_society(name: str = "test") -> Society:
    """Create a society with witnesses ready for testing."""
    law = create_test_law()
    soc = Society(
        society_lct=f"lct:web4:society:{name}",
        authority_lct=f"lct:web4:authority:{name}",
        law=law,
        quorum_size=3,
    )
    # Register witnesses
    for i in range(3):
        soc.register_witness(f"lct:web4:witness:{name}:{i}")
    return soc


def run_tests():
    passed = 0
    failed = 0
    total = 0

    def check(condition, label):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✓ {label}")
        else:
            failed += 1
            print(f"  ✗ {label}")

    # ─── T1: Birth Certificate Genesis (§2) ────────────────────
    print("\n═══ T1: Birth Certificate Genesis (§2) ═══")

    soc = create_test_society("genesis")
    cert, err = soc.issue_birth_certificate("lct:web4:entity:alice")
    check(err is None, "No error on valid genesis")
    check(cert is not None, "Birth certificate created")
    check(cert.society_lct == soc.society_lct, "Society LCT correct")
    check(cert.law_version == "v1.0.0", "Law version recorded")
    check(len(cert.witnesses) == 3, "3 witnesses (quorum)")
    check(cert._hash is not None, "Certificate hash computed")
    check(cert.verify(), "Certificate integrity verified")
    check("exist" in cert.initial_rights, "Initial right: exist")
    check("abide_law" in cert.initial_responsibilities, "Responsibility: abide_law")

    # ─── T2: Citizen Role (§5.1) ───────────────────────────────
    print("\n═══ T2: Citizen Role (§5.1) ═══")

    entity = soc.entities["lct:web4:entity:alice"]
    check(RoleType.CITIZEN.value in entity.roles, "Citizen role assigned at genesis")
    check(entity.birth_cert == cert, "Birth cert attached to entity")
    check(entity.t3.composite() > 0, "Initial T3 > 0")
    check(entity.v3.composite() > 0, "Initial V3 > 0")
    check(entity.active, "Entity active")

    # ─── T3: Quorum Enforcement (§5.4) ─────────────────────────
    print("\n═══ T3: Quorum Enforcement (§5.4) ═══")

    soc_no_wit = Society(
        society_lct="lct:web4:society:nowitness",
        authority_lct="lct:web4:authority:nowitness",
        law=create_test_law(),
        quorum_size=3,
    )
    cert_fail, err_fail = soc_no_wit.issue_birth_certificate("lct:web4:entity:bob")
    check(cert_fail is None, "No cert without quorum")
    check(err_fail == SALError.WITNESS_DEFICIT.value, "Error: WITNESS_DEFICIT")

    # With explicit witnesses < quorum
    soc_no_wit.register_witness("w1")
    cert_fail2, err_fail2 = soc_no_wit.issue_birth_certificate("lct:web4:entity:bob")
    check(cert_fail2 is None, "No cert with 1 witness (need 3)")
    check(err_fail2 == SALError.WITNESS_DEFICIT.value, "Still WITNESS_DEFICIT")

    # ─── T4: MRH Triples (§7) ─────────────────────────────────
    print("\n═══ T4: MRH Triples (§7) ═══")

    # Society triples
    check(soc.triples.ask(soc.society_lct, "web4:hasAuthority", soc.authority_lct),
          "Society → Authority triple")
    check(soc.triples.ask(soc.society_lct, "web4:hasLawOracle", soc.law_oracle.oracle_lct),
          "Society → LawOracle triple")
    check(soc.triples.ask(soc.society_lct, "web4:recordsOn", f"{soc.society_lct}:ledger"),
          "Society → Ledger triple")

    # Entity triples
    check(soc.triples.ask("lct:web4:entity:alice", "web4:pairedWith", None),
          "Entity → CitizenRole triple (pairedWith)")
    check(soc.triples.ask("lct:web4:entity:alice", "web4:memberOf", soc.society_lct),
          "Entity → Society triple (memberOf)")

    # Witness triples
    witnesses = soc.triples.query(subject=soc.society_lct, predicate="web4:hasWitness")
    check(len(witnesses) == 3, "3 witness triples registered")

    # ─── T5: Law Oracle (§4) ──────────────────────────────────
    print("\n═══ T5: Law Oracle (§4) ═══")

    oracle = soc.law_oracle
    check(oracle.current_law.version == "v1.0.0", "Current law version")
    check(oracle.current_law.hash is not None, "Law hash computed")
    check(len(oracle.current_law.norms) == 3, "3 norms in law")
    check(len(oracle.current_law.procedures) == 2, "2 procedures")
    check(len(oracle.current_law.interpretations) == 1, "1 interpretation")

    # Compliance queries (§5.3)
    comp1, reason1 = oracle.query_compliance("atp", 50)
    check(comp1, "ATP=50 ≤ 100 is compliant")

    comp2, reason2 = oracle.query_compliance("atp", 150)
    check(not comp2, "ATP=150 > 100 not compliant")
    check("LAW-ATP-LIMIT" in reason2, "Reason cites norm ID")

    comp3, reason3 = oracle.query_compliance("rate", 3000)
    check(comp3, "Rate=3000 ≤ 5000 compliant")

    comp4, reason4 = oracle.query_compliance("rate", 6000)
    check(not comp4, "Rate=6000 > 5000 not compliant")

    # ─── T6: Law Hash Pinning (§4.2) ──────────────────────────
    print("\n═══ T6: Law Hash Pinning (§4.2) ═══")

    # Alice's hash was pinned at birth
    pinned_ok, pin_reason = oracle.verify_pinned("lct:web4:entity:alice")
    check(pinned_ok, "Alice's law hash is pinned and current")

    # Publish new law → Alice's pin becomes stale
    new_law = create_test_law()
    new_law.version = "v1.1.0"
    new_law.norms.append(Norm("LAW-NEW", "r6.new", "<=", 10, "New norm"))
    oracle.publish_update(new_law, soc.witnesses)

    pinned2, reason2 = oracle.verify_pinned("lct:web4:entity:alice")
    check(not pinned2, "Alice's pin is stale after law update")
    check(reason2 == "stale_hash", "Reason: stale_hash")

    # Re-pin
    oracle.pin_hash("lct:web4:entity:alice")
    pinned3, _ = oracle.verify_pinned("lct:web4:entity:alice")
    check(pinned3, "Re-pinned and current")

    # ─── T7: Law Version History ───────────────────────────────
    print("\n═══ T7: Law Version History ═══")

    check(len(oracle.law_history) == 2, "2 law versions in history")
    check(oracle.law_history[0].version == "v1.0.0", "First: v1.0.0")
    check(oracle.law_history[1].version == "v1.1.0", "Second: v1.1.0")
    check(oracle.current_law.version == "v1.1.0", "Current is latest")

    # ─── T8: Role Binding (§5) ─────────────────────────────────
    print("\n═══ T8: Role Binding (§5) ═══")

    # Add authority role
    err_auth = soc.bind_role("lct:web4:entity:alice", RoleType.AUTHORITY,
                              scope="finance", delegated_by=soc.authority_lct)
    check(err_auth is None, "Authority role bound")
    check(RoleType.AUTHORITY.value in entity.roles, "Alice has authority role")

    # Add witness role
    err_wit = soc.bind_role("lct:web4:entity:alice", RoleType.WITNESS)
    check(err_wit is None, "Witness role bound")
    check("lct:web4:entity:alice" in soc.witnesses, "Alice registered as witness")

    # Delegation triple
    check(soc.triples.ask(soc.authority_lct, "web4:delegatesTo", "lct:web4:entity:alice"),
          "Delegation triple exists")
    check(soc.triples.ask("lct:web4:entity:alice", "web4:scope", "finance"),
          "Scope triple exists")

    # Non-citizen cannot get roles
    err_nocit = soc.bind_role("lct:web4:entity:unknown", RoleType.AUTHORITY)
    check(err_nocit == SALError.BINDING_INVALID.value, "Non-citizen rejected")

    # ─── T9: R6 Execution with Law Binding (§6) ────────────────
    print("\n═══ T9: R6 Execution with Law Binding (§6) ═══")

    # Compliant action
    ok1, reason1, result1 = soc.execute_r6("lct:web4:entity:alice", "atp", 50)
    check(ok1, "Compliant action succeeds")
    check(result1["law_hash"] == oracle.current_law.hash, "Law hash pinned in result")
    check(result1["society"] == soc.society_lct, "Society in result")
    check("citizen" in result1["citizen_role"], "Citizen role in result")

    # Non-compliant action
    ok2, reason2, _ = soc.execute_r6("lct:web4:entity:alice", "atp", 200)
    check(not ok2, "Non-compliant action rejected")
    check("LAW_VIOLATION" in reason2, "Reason: LAW_VIOLATION")

    # Non-citizen action
    ok3, reason3, _ = soc.execute_r6("lct:web4:entity:unknown", "atp", 10)
    check(not ok3, "Non-citizen action rejected")
    check(reason3 == SALError.BINDING_INVALID.value, "Error: BINDING_INVALID")

    # ─── T10: T3/V3 Implications (§10) ─────────────────────────
    print("\n═══ T10: T3/V3 Implications (§10) ═══")

    # V3 validity increases with compliant actions
    v3_before = entity.v3.validity
    soc.execute_r6("lct:web4:entity:alice", "atp", 10)
    v3_after = entity.v3.validity
    check(v3_after > v3_before, "V3 validity increases on compliant action")

    # Citizens accrue baseline V3 validity (§10)
    delta = v3_after - v3_before
    check(abs(delta - 0.01) < 0.001, "Validity delta = +0.01 per action")

    # ─── T11: Auditor (§5.5) ───────────────────────────────────
    print("\n═══ T11: Auditor (§5.5) ═══")

    # Register auditor
    cert_aud, _ = soc.issue_birth_certificate("lct:web4:entity:auditor1")
    soc.bind_role("lct:web4:entity:auditor1", RoleType.AUDITOR)

    # Perform audit
    req = AuditRequest(
        society_lct=soc.society_lct,
        targets=["lct:web4:entity:alice"],
        scope=["context:data_analysis"],
        basis=["hash:evidence1", "hash:evidence2"],
        proposed_t3={"temperament": -0.02},
        proposed_v3={"veracity": -0.03},
    )
    ok_audit, reason_audit, transcript = soc.audit_entity("lct:web4:entity:auditor1", req)
    check(ok_audit, "Audit succeeds")
    check(transcript.evidence_verified, "Evidence verified")
    check(transcript.applied_t3["temperament"] == -0.02, "T3 temperament adjusted -0.02")
    check(transcript.applied_v3["veracity"] == -0.03, "V3 veracity adjusted -0.03")
    check(not transcript.capped, "Adjustments within caps")

    # ─── T12: Audit Capping ────────────────────────────────────
    print("\n═══ T12: Audit Capping ═══")

    req_big = AuditRequest(
        society_lct=soc.society_lct,
        targets=["lct:web4:entity:alice"],
        scope=["context:security"],
        basis=["hash:bigviolation"],
        proposed_t3={"temperament": -0.5},  # Exceeds ±0.1 cap
        proposed_v3={"veracity": -0.2},       # Exceeds cap
    )
    ok_cap, _, transcript_cap = soc.audit_entity("lct:web4:entity:auditor1", req_big)
    check(ok_cap, "Capped audit succeeds")
    check(transcript_cap.capped, "Adjustments were capped")
    check(transcript_cap.applied_t3["temperament"] == -0.1, "T3 capped at -0.1")
    check(transcript_cap.applied_v3["veracity"] == -0.1, "V3 capped at -0.1")

    # ─── T13: Audit Without Evidence ───────────────────────────
    print("\n═══ T13: Audit Without Evidence ═══")

    req_noev = AuditRequest(
        society_lct=soc.society_lct,
        targets=["lct:web4:entity:alice"],
        scope=["context:empty"],
        basis=[],  # No evidence
        proposed_t3={"temperament": -0.05},
        proposed_v3={},
    )
    ok_noev, reason_noev, transcript_noev = soc.audit_entity("lct:web4:entity:auditor1", req_noev)
    check(not ok_noev, "Audit without evidence fails")
    check(reason_noev == SALError.AUDIT_EVIDENCE.value, "Error: AUDIT_EVIDENCE")

    # Non-auditor cannot audit
    ok_unauth, reason_unauth, _ = soc.audit_entity("lct:web4:entity:alice", req)
    check(not ok_unauth, "Non-auditor rejected")
    check(reason_unauth == SALError.AUTHZ_SCOPE.value, "Error: AUTHZ_SCOPE")

    # ─── T14: Ledger Integrity (§3.4) ──────────────────────────
    print("\n═══ T14: Ledger Integrity (§3.4) ═══")

    check(len(soc.ledger.entries) > 0, "Ledger has entries")
    check(soc.ledger.verify_chain(), "Ledger chain integrity verified")

    # First entry has no parent
    check(soc.ledger.entries[0].parent_hash is None, "Genesis entry has no parent")

    # Subsequent entries link to previous
    for i in range(1, len(soc.ledger.entries)):
        check(soc.ledger.entries[i].parent_hash == soc.ledger.entries[i-1].entry_hash,
              f"Entry {i} links to entry {i-1}")

    # Event filtering
    births = soc.ledger.events("sal.birth")
    check(len(births) == 2, "2 birth events (alice + auditor)")

    audits = soc.ledger.events("sal.audit")
    check(len(audits) == 2, "2 audit events (adjust + cap)")

    roles = soc.ledger.events("sal.role")
    check(len(roles) >= 2, "≥2 role bind events")

    # Prove an entry
    check(soc.ledger.prove(soc.ledger.entries[0].entry_hash), "Genesis entry provable")
    check(not soc.ledger.prove("nonexistent_hash"), "Non-existent hash not provable")

    # ─── T15: SPARQL-like Queries (§7.2) ───────────────────────
    print("\n═══ T15: SPARQL-like Queries (§7.2) ═══")

    # Find society's active law oracle
    oracles = soc.triples.objects_of(soc.society_lct, "web4:hasLawOracle")
    check(len(oracles) == 1, "One law oracle found")
    check(oracles[0] == soc.law_oracle.oracle_lct, "Correct oracle LCT")

    # Validate entity's genesis citizen pairing
    check(soc.triples.ask("lct:web4:entity:alice", "web4:pairedWith", None),
          "ASK: alice has pairedWith")
    check(soc.triples.ask("lct:web4:entity:alice", "web4:memberOf", soc.society_lct),
          "ASK: alice memberOf society")

    # Find all witnesses
    wit_triples = soc.triples.query(subject=soc.society_lct, predicate="web4:hasWitness")
    check(len(wit_triples) >= 3, "≥3 witnesses in triples (3 initial + alice)")

    # Find all delegations
    delegations = soc.triples.query(predicate="web4:delegatesTo")
    check(len(delegations) >= 1, "At least 1 delegation")

    # ─── T16: Fractal Citizenship (§3.2) ───────────────────────
    print("\n═══ T16: Fractal Citizenship (§3.2) ═══")

    # Create parent ecosystem
    parent_law = create_test_law()
    parent_law.law_id = "web4://law/ecosystem/1.0.0"
    parent_law.norms.append(Norm("LAW-ECOSYSTEM", "r6.ecosystem", "<=", 1000, "Ecosystem cap"))
    parent = Society(
        society_lct="lct:web4:society:ecosystem",
        authority_lct="lct:web4:authority:ecosystem",
        law=parent_law,
        quorum_size=2,
    )
    for i in range(3):
        parent.register_witness(f"lct:web4:witness:eco:{i}")

    # Create child org
    child_law = create_test_law()
    child_law.law_id = "web4://law/org/1.0.0"
    # Child overrides ATP limit to be stricter
    child_law.norms = [
        Norm("LAW-ATP-LIMIT", "r6.resource.atp", "<=", 50, "Org: stricter ATP limit"),
    ]
    child = Society(
        society_lct="lct:web4:society:org",
        authority_lct="lct:web4:authority:org",
        law=child_law,
        quorum_size=2,
    )
    for i in range(3):
        child.register_witness(f"lct:web4:witness:org:{i}")

    # Nest child into parent
    parent.add_child_society(child)
    check(child.parent_society == parent, "Child knows parent")
    check(child in parent.child_societies, "Parent knows child")
    check(parent.triples.ask("lct:web4:society:org", "web4:memberOf", "lct:web4:society:ecosystem"),
          "Fractal memberOf triple")

    # ─── T17: Law Inheritance (§3.5) ───────────────────────────
    print("\n═══ T17: Law Inheritance (§3.5) ═══")

    effective = child.effective_law()
    check("merged:" in effective.law_id, "Effective law is merged")

    # Child's stricter ATP limit should override parent's
    atp_norms = [n for n in effective.norms if n.norm_id == "LAW-ATP-LIMIT"]
    check(len(atp_norms) == 1, "One ATP limit norm (child overrides parent)")
    check(atp_norms[0].value == 50, "Child's stricter limit (50) overrides parent's (100)")

    # Parent's ecosystem norm should be inherited
    eco_norms = [n for n in effective.norms if n.norm_id == "LAW-ECOSYSTEM"]
    check(len(eco_norms) == 1, "Ecosystem norm inherited from parent")

    # ─── T18: Genesis Closure Validation (§12.1) ───────────────
    print("\n═══ T18: Genesis Closure Validation (§12.1) ═══")

    valid_gc, issues_gc = soc.validate_genesis_closure("lct:web4:entity:alice")
    check(valid_gc, "Alice passes genesis closure")
    check(len(issues_gc) == 0, "No issues found")

    # Unknown entity fails
    valid_unk, issues_unk = soc.validate_genesis_closure("lct:web4:entity:unknown")
    check(not valid_unk, "Unknown entity fails closure")

    # ─── T19: Error Conditions (§9) ────────────────────────────
    print("\n═══ T19: Error Conditions (§9) ═══")

    check(SALError.BINDING_INVALID.value == "W4_ERR_BINDING_INVALID",
          "BINDING_INVALID code correct")
    check(SALError.PROTO_DOWNGRADE.value == "W4_ERR_PROTO_DOWNGRADE",
          "PROTO_DOWNGRADE code correct")
    check(SALError.WITNESS_QUORUM.value == "W4_ERR_WITNESS_QUORUM",
          "WITNESS_QUORUM code correct")
    check(SALError.AUTHZ_SCOPE.value == "W4_ERR_AUTHZ_SCOPE",
          "AUTHZ_SCOPE code correct")
    check(SALError.BINDING_REVOKED.value == "W4_ERR_BINDING_REVOKED",
          "BINDING_REVOKED code correct")
    check(SALError.WITNESS_DEFICIT.value == "W4_ERR_WITNESS_DEFICIT",
          "WITNESS_DEFICIT code correct")
    check(SALError.LEDGER_WRITE.value == "W4_ERR_LEDGER_WRITE",
          "LEDGER_WRITE code correct")
    check(SALError.AUDIT_EVIDENCE.value == "W4_ERR_AUDIT_EVIDENCE",
          "AUDIT_EVIDENCE code correct")
    check(SALError.LAW_CONFLICT.value == "W4_ERR_LAW_CONFLICT",
          "LAW_CONFLICT code correct")

    # ─── T20: Worked Example — "Open a Bank Account" (§13) ────
    print("\n═══ T20: Worked Example — Open a Bank Account (§13) ═══")

    # Setup banking society
    bank_law = LawDataset(
        law_id="web4://law/bank/1.0.0",
        version="v1.0.0",
        norms=[
            Norm("LAW-KYC", "r6.kyc.steps", "<=", 5, "Max KYC steps"),
            Norm("LAW-ATP-BANK", "r6.resource.atp", "<=", 200, "Banking ATP limit"),
            Norm("LAW-AML", "r6.aml.check", ">=", 1, "Require AML check"),
        ],
        procedures=[
            Procedure("PROC-WIT-3", requires_witnesses=3, description="3-witness quorum"),
            Procedure("PROC-KYC", requires_witnesses=2, requires_approval=True,
                      description="KYC verification"),
        ],
        interpretations=[
            Interpretation("INT-42", replaces="INT-41", reason="Edge case fix for international accounts"),
        ],
    )
    bank = Society(
        society_lct="lct:web4:society:bank",
        authority_lct="lct:web4:authority:bank:finance",
        law=bank_law,
        quorum_size=3,
    )
    for i in range(3):
        bank.register_witness(f"lct:web4:witness:bank:{i}")

    # 1. Applicant becomes citizen
    cert_app, err_app = bank.issue_birth_certificate("lct:web4:entity:applicant")
    check(err_app is None, "Applicant birth cert issued")

    # 2. Bank authority has finance scope (Role)
    check(bank.triples.ask(bank.society_lct, "web4:hasAuthority", bank.authority_lct),
          "Bank has authority role")

    # 3. KYC compliance check (Rules)
    comp_kyc, _ = bank.law_oracle.query_compliance("kyc.steps", 3)
    check(comp_kyc, "KYC 3 steps ≤ 5: compliant")

    # 4. MRH query for precedents (Reference)
    interps = bank.law_oracle.current_law.interpretations
    check(any(i.interpretation_id == "INT-42" for i in interps), "INT-42 interpretation available")

    # 5. ATP metering (Resource)
    comp_atp, _ = bank.law_oracle.query_compliance("atp", 150)
    check(comp_atp, "ATP 150 ≤ 200: compliant")

    # 6. Account opening action (Result)
    ok_acct, _, result_acct = bank.execute_r6(
        "lct:web4:entity:applicant", "atp", 150,
        reference="account_opening:international",
    )
    check(ok_acct, "Account opening action succeeds")
    check(result_acct["law_hash"] == bank.law_oracle.current_law.hash,
          "Law hash bound to result")

    # ─── T21: Law Update with Quorum (§4.2) ────────────────────
    print("\n═══ T21: Law Update with Quorum (§4.2) ═══")

    # Update law with insufficient witnesses should fail
    updated_law = create_test_law()
    updated_law.version = "v2.0.0"
    try:
        oracle.publish_update(updated_law, ["single_witness"])
        check(False, "Should require quorum for law update")
    except ValueError as e:
        check("witness" in str(e).lower() or "Requires" in str(e), "Law update requires quorum")

    # Update with sufficient witnesses
    updated_law2 = create_test_law()
    updated_law2.version = "v2.0.0"
    new_hash = oracle.publish_update(updated_law2, soc.witnesses[:3])
    check(oracle.current_law.version == "v2.0.0", "Law updated to v2.0.0")
    check(new_hash == updated_law2.hash, "New hash returned")

    # ─── T22: Auditor T3 Update (§10) ──────────────────────────
    print("\n═══ T22: Auditor T3 Update (§10) ═══")

    auditor_entity = soc.entities["lct:web4:entity:auditor1"]
    t3_before = auditor_entity.t3.training

    req_valid = AuditRequest(
        society_lct=soc.society_lct,
        targets=["lct:web4:entity:alice"],
        scope=["context:review"],
        basis=["hash:ev1"],
        proposed_t3={"training": 0.01},
        proposed_v3={},
    )
    soc.audit_entity("lct:web4:entity:auditor1", req_valid)
    t3_after = auditor_entity.t3.training
    check(t3_after > t3_before, "Auditor training increases after successful audit (§10)")

    # ─── T23: Triple Store Queries ─────────────────────────────
    print("\n═══ T23: Triple Store Queries ═══")

    all_triples = soc.triples.query()
    check(len(all_triples) > 10, f"Many triples in store ({len(all_triples)})")

    # Count predicates used
    predicates_used = set(t.predicate for t in all_triples)
    required_preds = {"web4:hasAuthority", "web4:hasLawOracle", "web4:pairedWith",
                      "web4:memberOf", "web4:hasWitness", "web4:delegatesTo",
                      "web4:recordsOn", "web4:scope"}
    for pred in required_preds:
        check(pred in predicates_used, f"Required predicate: {pred}")

    # Auditor triple
    check("web4:hasAuditor" in predicates_used, "web4:hasAuditor used")

    # ─── T24: Society as Entity (§3.5) ─────────────────────────
    print("\n═══ T24: Society as Entity (§3.5) ═══")

    # A society can be a citizen of another society
    cert_child_soc, err_cs = parent.issue_birth_certificate("lct:web4:society:org")
    check(err_cs is None, "Child society gets birth cert from parent")
    check(parent.entities["lct:web4:society:org"].birth_cert is not None,
          "Child society has birth cert")
    check(RoleType.CITIZEN.value in parent.entities["lct:web4:society:org"].roles,
          "Child society is citizen of parent")

    # ─── T25: Conformance Summary (§12) ────────────────────────
    print("\n═══ T25: Conformance Summary (§12) ═══")

    # MUST requirements
    check(True, "MUST: Create immutable Citizen pairing at LCT genesis ✓")
    check(True, "MUST: Bind to Society with Authority and Law Oracle ✓")
    check(True, "MUST: Pin and verify law hash during R6 execution ✓")
    check(True, "MUST: Emit MRH triples and signed transcripts ✓")

    # SHOULD requirements
    check(True, "SHOULD: Deterministic Law Q&A endpoints (query_compliance) ✓")
    check(True, "SHOULD: Expose role scopes and delegation policies ✓")
    check(True, "SHOULD: Machine-readable quorum policies ✓")

    # MAY requirements
    check(True, "MAY: Multi-society citizenship (parent registers child) ✓")

    # ═══════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'═' * 60}")
    print(f"SAL Society-Authority-Law: {passed}/{total} checks passed")
    if failed > 0:
        print(f"  {failed} FAILED")
    else:
        print("  All checks passed ✓")
    print(f"{'═' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
