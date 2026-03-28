"""
Web4 Federation — Society, Authority, Law (SAL)

Canonical implementation per web4-standard/core-spec/web4-society-authority-law.md
and web4-standard/core-spec/SOCIETY_SPECIFICATION.md.

SAL defines how entities are born into societies, how authority is delegated,
and how law governs actions. Every entity is born with a Citizen role as its
genesis pairing — this is immutable and prerequisite for all other roles.

Key concepts:
- Society: delegative entity with authority, law oracle, and quorum policy
- Authority: scoped delegation (domain-bounded, revocable)
- LawDataset: versioned norms, procedures, interpretations
- Fractal citizenship: societies nest (team → org → network → ecosystem)
- Law inheritance: child inherits parent law, may override with awareness (merge_law)
- Citizenship lifecycle: application → provisional → active → suspended → terminated
- Quorum policy: witness requirements with majority/threshold/unanimous modes
- Ledger types: confined, witnessed, participatory (§4.1 of Society spec)
- Audit: scoped T3/V3 adjustments with evidence and rate limits (§5.5)
- Norm operators: <=, >=, ==, !=, <, >, in, not_in

This module provides DATA STRUCTURES and simple operations, not a policy
engine. Policy evaluation belongs in HRM/PolicyGate.

Validated against: web4-standard/test-vectors/federation/sal-governance.json
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set

from .lct import LCT, EntityType, BirthCertificate, MRHPairing
from .trust import T3, V3

__all__ = [
    # Classes
    "Society", "LawDataset", "Delegation", "RoleType",
    "CitizenshipStatus", "CitizenshipRecord",
    "QuorumMode", "QuorumPolicy", "LedgerType",
    "AuditRequest", "AuditAdjustment",
    "Norm", "Procedure", "Interpretation",
    # Functions
    "valid_citizenship_transition", "merge_law",
    "norm_to_dict", "norm_from_dict",
    "procedure_to_dict", "procedure_from_dict",
    "interpretation_to_dict", "interpretation_from_dict",
    "law_dataset_to_dict", "law_dataset_from_dict",
    "delegation_to_dict", "delegation_from_dict",
    "quorum_policy_to_dict", "quorum_policy_from_dict",
]


# ── Role Types ───────────────────────────────────────────────────

class RoleType(str, Enum):
    """SAL role types (§5)."""
    CITIZEN = "citizen"        # Genesis, immutable, prerequisite for all others
    AUTHORITY = "authority"    # Scoped delegation of governance power
    LAW_ORACLE = "law_oracle"  # Publishes/verifies law datasets
    WITNESS = "witness"        # Co-signs ledger entries, provides attestations
    AUDITOR = "auditor"        # Traverses MRH, validates/adjusts T3/V3


# ── Citizenship Lifecycle (SOCIETY_SPECIFICATION §2.3) ───────────

class CitizenshipStatus(str, Enum):
    """Citizenship lifecycle states per SOCIETY_SPECIFICATION §2.3."""
    APPLIED = "applied"          # Application submitted, pending review
    PROVISIONAL = "provisional"  # Accepted with limited rights
    ACTIVE = "active"            # Full citizenship
    SUSPENDED = "suspended"      # Temporarily restricted
    TERMINATED = "terminated"    # Permanently ended


# Valid transitions: state → set of reachable states
_CITIZENSHIP_TRANSITIONS: Dict[CitizenshipStatus, FrozenSet[CitizenshipStatus]] = {
    CitizenshipStatus.APPLIED: frozenset({CitizenshipStatus.PROVISIONAL, CitizenshipStatus.ACTIVE}),
    CitizenshipStatus.PROVISIONAL: frozenset({CitizenshipStatus.ACTIVE, CitizenshipStatus.TERMINATED}),
    CitizenshipStatus.ACTIVE: frozenset({CitizenshipStatus.SUSPENDED, CitizenshipStatus.TERMINATED}),
    CitizenshipStatus.SUSPENDED: frozenset({CitizenshipStatus.ACTIVE, CitizenshipStatus.TERMINATED}),
    CitizenshipStatus.TERMINATED: frozenset(),  # Terminal state
}


def valid_citizenship_transition(from_status: CitizenshipStatus, to_status: CitizenshipStatus) -> bool:
    """Check whether a citizenship status transition is allowed."""
    return to_status in _CITIZENSHIP_TRANSITIONS.get(from_status, frozenset())


@dataclass
class CitizenshipRecord:
    """
    Formal citizenship record per SOCIETY_SPECIFICATION §2.4.

    Tracks an entity's membership in a society with lifecycle state,
    rights, obligations, and audit trail timestamps.
    """
    entity_lct: str
    society_id: str
    status: CitizenshipStatus = CitizenshipStatus.ACTIVE
    rights: List[str] = field(default_factory=lambda: ["exist", "interact", "accumulate_reputation"])
    obligations: List[str] = field(default_factory=lambda: ["abide_law", "respect_quorum"])
    witnesses: List[str] = field(default_factory=list)
    granted_at: str = ""
    suspended_at: Optional[str] = None
    terminated_at: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.granted_at:
            self.granted_at = datetime.now(timezone.utc).isoformat()

    def transition(self, new_status: CitizenshipStatus) -> bool:
        """Attempt a status transition. Returns True if valid, False otherwise."""
        if not valid_citizenship_transition(self.status, new_status):
            return False
        now = datetime.now(timezone.utc).isoformat()
        self.status = new_status
        if new_status == CitizenshipStatus.SUSPENDED:
            self.suspended_at = now
        elif new_status == CitizenshipStatus.TERMINATED:
            self.terminated_at = now
        elif new_status == CitizenshipStatus.ACTIVE and self.suspended_at:
            self.suspended_at = None  # Clear suspension on reinstatement
        return True

    @property
    def is_active(self) -> bool:
        return self.status == CitizenshipStatus.ACTIVE


# ── Quorum Policy (SAL §3.1, §5.4) ──────────────────────────────

class QuorumMode(str, Enum):
    """How witness quorum is evaluated."""
    MAJORITY = "majority"        # >50% of registered witnesses
    THRESHOLD = "threshold"      # Fixed count required
    UNANIMOUS = "unanimous"      # All registered witnesses must agree


@dataclass(frozen=True)
class QuorumPolicy:
    """
    Witness quorum requirements for SAL-critical events (§5.4).

    mode=THRESHOLD + required=3 means "at least 3 witnesses must co-sign."
    mode=MAJORITY means ">50% of registered witnesses."
    mode=UNANIMOUS means "all registered witnesses."
    """
    mode: QuorumMode = QuorumMode.THRESHOLD
    required: int = 2

    def check(self, witness_count: int, total_registered: int = 0) -> bool:
        """Check if a witness count satisfies this quorum policy."""
        if self.mode == QuorumMode.THRESHOLD:
            return witness_count >= self.required
        elif self.mode == QuorumMode.MAJORITY:
            if total_registered == 0:
                return False
            return witness_count > total_registered / 2
        elif self.mode == QuorumMode.UNANIMOUS:
            if total_registered == 0:
                return False
            return witness_count >= total_registered
        return False


# ── Ledger Types (SOCIETY_SPECIFICATION §4.1) ────────────────────

class LedgerType(str, Enum):
    """Classification of society ledgers by access model."""
    CONFINED = "confined"            # Citizens only; internal consensus
    WITNESSED = "witnessed"          # Citizens + external witnesses
    PARTICIPATORY = "participatory"  # Participates in parent ledger


# ── Audit (SAL §5.5) ────────────────────────────────────────────

@dataclass
class AuditRequest:
    """
    Request to adjust T3/V3 tensors via auditor role (§5.5).

    The auditor traverses the society's MRH and proposes adjustments
    based on verifiable evidence. All adjustments must go through
    witness quorum and are recorded on the immutable ledger.
    """
    audit_id: str
    society_id: str
    auditor_lct: str
    targets: List[str]            # LCT IDs of citizens being audited
    scope: List[str]              # Context scopes (e.g., ["data_analysis"])
    evidence: List[str]           # Evidence hashes
    proposed_t3_deltas: Dict[str, float] = field(default_factory=dict)
    proposed_v3_deltas: Dict[str, float] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class AuditAdjustment:
    """
    Result of an approved audit — applied T3/V3 deltas (§5.5).

    Rate limits and caps are enforced by law: adjustments MUST reference
    verifiable evidence, negative adjustments MUST include appeal path.
    """
    audit_id: str
    target_lct: str
    applied_t3_deltas: Dict[str, float]
    applied_v3_deltas: Dict[str, float]
    witnesses: List[str]
    appeal_path: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def has_negative_adjustment(self) -> bool:
        """Check if any adjustment is negative (requires appeal path per spec)."""
        for v in list(self.applied_t3_deltas.values()) + list(self.applied_v3_deltas.values()):
            if v < 0:
                return True
        return False

    def is_valid(self) -> bool:
        """Basic validity: negative adjustments require appeal path."""
        if self.has_negative_adjustment() and not self.appeal_path:
            return False
        return True


# ── Norms and Law ────────────────────────────────────────────────

@dataclass(frozen=True)
class Norm:
    """
    A single law norm — allow/deny constraint (§4.1).

    Example: {"id": "LAW-ATP-LIMIT", "selector": "r6.resource.atp", "op": "<=", "value": 100}
    """
    norm_id: str
    selector: str         # what the norm applies to (e.g. "r6.resource.atp")
    op: str               # comparison operator: "<=", ">=", "==", "!=", "in", "not_in"
    value: Any            # threshold or allowed values
    description: str = ""

    def check(self, actual_value: Any) -> bool:
        """Check if a value satisfies the norm.

        Supports numeric comparisons (<=, >=, ==, !=, <, >) and
        membership tests (in, not_in) for collection-valued norms.
        """
        if self.op == "<=":
            return actual_value <= self.value
        elif self.op == ">=":
            return actual_value >= self.value
        elif self.op == "==":
            return actual_value == self.value
        elif self.op == "!=":
            return actual_value != self.value
        elif self.op == "<":
            return actual_value < self.value
        elif self.op == ">":
            return actual_value > self.value
        elif self.op == "in":
            return actual_value in self.value
        elif self.op == "not_in":
            return actual_value not in self.value
        return False


@dataclass(frozen=True)
class Procedure:
    """A compliance procedure (§4.1). E.g., witness quorum requirements."""
    procedure_id: str
    requires_witnesses: int = 0
    description: str = ""


@dataclass(frozen=True)
class Interpretation:
    """A precedent/update to law (§4.1)."""
    interpretation_id: str
    replaces: Optional[str] = None
    reason: str = ""


@dataclass
class LawDataset:
    """
    Versioned law dataset published by a Law Oracle (§4.1).

    This is a DATA CONTAINER — norms in, lookups out.
    Policy evaluation logic belongs in HRM/PolicyGate, not here.
    """
    law_id: str
    version: str
    society_id: str
    norms: List[Norm] = field(default_factory=list)
    procedures: List[Procedure] = field(default_factory=list)
    interpretations: List[Interpretation] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def hash(self) -> str:
        """Content-addressed hash of the law dataset."""
        canonical = json.dumps({
            "law_id": self.law_id,
            "version": self.version,
            "society_id": self.society_id,
            "norms": [{"id": n.norm_id, "selector": n.selector, "op": n.op, "value": n.value}
                      for n in self.norms],
            "procedures": [{"id": p.procedure_id, "requires_witnesses": p.requires_witnesses}
                           for p in self.procedures],
            "interpretations": [{"id": i.interpretation_id, "replaces": i.replaces, "reason": i.reason}
                                for i in self.interpretations],
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def get_norm(self, norm_id: str) -> Optional[Norm]:
        """Look up a norm by ID."""
        return next((n for n in self.norms if n.norm_id == norm_id), None)

    def get_procedure(self, proc_id: str) -> Optional[Procedure]:
        return next((p for p in self.procedures if p.procedure_id == proc_id), None)

    def check_norm(self, norm_id: str, value: float) -> Optional[bool]:
        """Check a value against a specific norm. Returns None if norm not found."""
        norm = self.get_norm(norm_id)
        if norm is None:
            return None
        return norm.check(value)


def merge_law(parent: LawDataset, child: LawDataset) -> LawDataset:
    """
    Merge parent and child law datasets per §3.5 inheritance rule.

    effectiveLaw(child) = merge(parentLaw, childOverrides)

    Child norms with the same norm_id override parent norms.
    Parent norms not overridden by child are inherited.
    Procedures and interpretations follow the same merge logic.
    """
    child_norm_ids = {n.norm_id for n in child.norms}
    child_proc_ids = {p.procedure_id for p in child.procedures}
    child_interp_ids = {i.interpretation_id for i in child.interpretations}

    merged_norms = list(child.norms) + [
        n for n in parent.norms if n.norm_id not in child_norm_ids
    ]
    merged_procs = list(child.procedures) + [
        p for p in parent.procedures if p.procedure_id not in child_proc_ids
    ]
    merged_interps = list(child.interpretations) + [
        i for i in parent.interpretations if i.interpretation_id not in child_interp_ids
    ]

    return LawDataset(
        law_id=f"{child.law_id}+{parent.law_id}",
        version=child.version,
        society_id=child.society_id,
        norms=merged_norms,
        procedures=merged_procs,
        interpretations=merged_interps,
    )


# ── Authority (Delegation) ───────────────────────────────────────

@dataclass
class Delegation:
    """
    A scoped authority delegation (§5.2).

    Authority is domain-bounded and revocable. Each delegation specifies
    what scope the delegate has and any limits.
    """
    delegation_id: str
    delegator: str          # LCT ID of the entity granting authority
    delegate: str           # LCT ID of the entity receiving authority
    scope: str              # domain scope (e.g., "finance", "safety", "membership")
    permissions: List[str]  # specific permissions granted
    active: bool = True
    created_at: str = ""
    expires_at: Optional[str] = None
    max_depth: int = 1      # how many levels of sub-delegation allowed

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def revoke(self) -> None:
        """Revoke this delegation."""
        self.active = False

    def can_sub_delegate(self) -> bool:
        """Can the delegate further delegate?"""
        return self.active and self.max_depth > 0

    def sub_delegate(self, new_delegate: str, scope: Optional[str] = None,
                     permissions: Optional[List[str]] = None) -> Optional[Delegation]:
        """
        Create a sub-delegation with reduced scope.

        Sub-delegations MUST be a subset of the parent's permissions.
        Max depth decreases by 1.
        """
        if not self.can_sub_delegate():
            return None

        sub_perms = permissions or self.permissions
        # Cannot amplify: sub-permissions must be subset
        if not set(sub_perms).issubset(set(self.permissions)):
            return None

        return Delegation(
            delegation_id=f"{self.delegation_id}:sub:{new_delegate[:8]}",
            delegator=self.delegate,
            delegate=new_delegate,
            scope=scope or self.scope,
            permissions=sub_perms,
            max_depth=self.max_depth - 1,
        )


# ── Society ──────────────────────────────────────────────────────

class Society:
    """
    A delegative entity that issues citizenship, delegates authority,
    and binds law (§3).

    Usage:
        society = Society("lct:web4:society:acme", "ACME Corp")
        society.set_law(law_dataset)
        alice_lct = society.issue_citizenship(
            entity_type=EntityType.HUMAN,
            public_key="alice_pubkey",
            witnesses=["w1", "w2", "w3"],
        )
        society.delegate_authority("lct:bob", scope="finance", permissions=["approve_atp"])
    """

    def __init__(
        self,
        society_id: str,
        name: str,
        parent: Optional[Society] = None,
        quorum_policy: Optional[QuorumPolicy] = None,
        ledger_type: LedgerType = LedgerType.CONFINED,
    ) -> None:
        self.society_id = society_id
        self.name = name
        self.parent = parent

        # Citizens (LCT IDs) — kept for backward compat
        self.citizens: Set[str] = set()
        # Formal citizenship records
        self.citizenship_records: Dict[str, CitizenshipRecord] = {}
        # Authority delegations
        self.delegations: List[Delegation] = []
        # Active law dataset
        self.law: Optional[LawDataset] = None
        # Quorum policy
        self.quorum_policy = quorum_policy or QuorumPolicy()
        # Backward compat
        self.witness_quorum: int = self.quorum_policy.required
        # Ledger type
        self.ledger_type = ledger_type
        # Child societies
        self.children: List[Society] = []

        if parent:
            parent.children.append(self)

    def set_law(self, law: LawDataset) -> None:
        """Publish a new law dataset for this society."""
        self.law = law

    def effective_law(self, merge: bool = False) -> Optional[LawDataset]:
        """
        Get the effective law (§3.5).

        With merge=False (default, backward compat):
            Child law overrides parent law entirely.
        With merge=True:
            Child norms override parent norms with same ID;
            parent norms not overridden are inherited.
        """
        if self.law is not None:
            if merge and self.parent is not None:
                parent_law = self.parent.effective_law(merge=True)
                if parent_law is not None:
                    return merge_law(parent_law, self.law)
            return self.law
        if self.parent is not None:
            return self.parent.effective_law(merge=merge)
        return None

    def issue_citizenship(
        self,
        entity_type: EntityType,
        public_key: str,
        witnesses: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
        t3: Optional[T3] = None,
        v3: Optional[V3] = None,
    ) -> LCT:
        """
        Issue an LCT with citizenship in this society (§2.1).

        The birth certificate binds the entity to this society with
        the citizen genesis role. This pairing is immutable.
        """
        witnesses = witnesses or []

        # Enforce witness quorum if law requires it
        law = self.effective_law()
        if law:
            proc = law.get_procedure("PROC-WITNESS-QUORUM")
            if proc and len(witnesses) < proc.requires_witnesses:
                raise ValueError(
                    f"Insufficient witnesses: need {proc.requires_witnesses}, got {len(witnesses)}"
                )

        lct = LCT.create(
            entity_type=entity_type,
            public_key=public_key,
            society=self.society_id,
            context=self.name.lower().replace(" ", "_"),
            witnesses=witnesses,
            timestamp=timestamp,
            t3=t3,
            v3=v3,
        )

        self.citizens.add(lct.lct_id)
        self.citizenship_records[lct.lct_id] = CitizenshipRecord(
            entity_lct=lct.lct_id,
            society_id=self.society_id,
            status=CitizenshipStatus.ACTIVE,
            witnesses=witnesses,
        )
        return lct

    def is_citizen(self, lct_id: str) -> bool:
        """Check if an entity is an active citizen of this society."""
        record = self.citizenship_records.get(lct_id)
        if record is not None:
            return record.is_active
        # Backward compat: fall back to set membership
        return lct_id in self.citizens

    def get_citizenship(self, lct_id: str) -> Optional[CitizenshipRecord]:
        """Get the citizenship record for an entity."""
        return self.citizenship_records.get(lct_id)

    def suspend_citizen(self, lct_id: str) -> bool:
        """Suspend a citizen's membership. Returns False if transition invalid."""
        record = self.citizenship_records.get(lct_id)
        if record is None:
            return False
        return record.transition(CitizenshipStatus.SUSPENDED)

    def reinstate_citizen(self, lct_id: str) -> bool:
        """Reinstate a suspended citizen. Returns False if transition invalid."""
        record = self.citizenship_records.get(lct_id)
        if record is None:
            return False
        return record.transition(CitizenshipStatus.ACTIVE)

    def terminate_citizen(self, lct_id: str) -> bool:
        """Permanently terminate citizenship. Returns False if transition invalid."""
        record = self.citizenship_records.get(lct_id)
        if record is None:
            return False
        if record.transition(CitizenshipStatus.TERMINATED):
            self.citizens.discard(lct_id)
            return True
        return False

    def delegate_authority(
        self,
        delegate_lct_id: str,
        scope: str,
        permissions: List[str],
        max_depth: int = 1,
    ) -> Delegation:
        """
        Delegate scoped authority to an entity (§5.2).

        The delegate MUST be a citizen of this society.
        """
        if not self.is_citizen(delegate_lct_id):
            raise ValueError(f"{delegate_lct_id} is not a citizen of {self.society_id}")

        delegation = Delegation(
            delegation_id=f"deleg:{self.society_id}:{delegate_lct_id}:{scope}",
            delegator=self.society_id,
            delegate=delegate_lct_id,
            scope=scope,
            permissions=permissions,
            max_depth=max_depth,
        )
        self.delegations.append(delegation)
        return delegation

    def revoke_delegation(self, delegation_id: str) -> bool:
        """Revoke a delegation by ID."""
        for d in self.delegations:
            if d.delegation_id == delegation_id and d.active:
                d.revoke()
                return True
        return False

    def active_delegations(self, delegate_lct_id: Optional[str] = None) -> List[Delegation]:
        """Get active delegations, optionally filtered by delegate."""
        result = [d for d in self.delegations if d.active]
        if delegate_lct_id:
            result = [d for d in result if d.delegate == delegate_lct_id]
        return result

    def has_permission(self, lct_id: str, scope: str, permission: str) -> bool:
        """Check if an entity has a specific permission via delegation."""
        for d in self.active_delegations(lct_id):
            if d.scope == scope and permission in d.permissions:
                return True
        return False

    @property
    def depth(self) -> int:
        """Nesting depth in the society hierarchy."""
        if self.parent is None:
            return 0
        return 1 + self.parent.depth

    @property
    def ancestry(self) -> List[str]:
        """List of ancestor society IDs from root to self."""
        if self.parent is None:
            return [self.society_id]
        return self.parent.ancestry + [self.society_id]

    def find_child(self, society_id: str) -> Optional[Society]:
        """Find a child society by ID (direct children only)."""
        return next((c for c in self.children if c.society_id == society_id), None)


# ── JSON Serialization ─────────────────────────────────────────
# to_dict() / from_dict() for cross-language interoperability.
# These are used by test vectors and wire formats.


def norm_to_dict(norm: Norm) -> dict:
    """Serialize a Norm to a JSON-compatible dict."""
    d: dict = {
        "norm_id": norm.norm_id,
        "selector": norm.selector,
        "op": norm.op,
        "value": norm.value,
    }
    if norm.description:
        d["description"] = norm.description
    return d


def norm_from_dict(d: dict) -> Norm:
    """Deserialize a Norm from a dict."""
    return Norm(
        norm_id=d["norm_id"],
        selector=d["selector"],
        op=d["op"],
        value=d["value"],
        description=d.get("description", ""),
    )


def procedure_to_dict(proc: Procedure) -> dict:
    """Serialize a Procedure to a JSON-compatible dict."""
    d: dict = {
        "procedure_id": proc.procedure_id,
        "requires_witnesses": proc.requires_witnesses,
    }
    if proc.description:
        d["description"] = proc.description
    return d


def procedure_from_dict(d: dict) -> Procedure:
    """Deserialize a Procedure from a dict."""
    return Procedure(
        procedure_id=d["procedure_id"],
        requires_witnesses=d.get("requires_witnesses", 0),
        description=d.get("description", ""),
    )


def interpretation_to_dict(interp: Interpretation) -> dict:
    """Serialize an Interpretation to a JSON-compatible dict."""
    d: dict = {"interpretation_id": interp.interpretation_id}
    if interp.replaces:
        d["replaces"] = interp.replaces
    if interp.reason:
        d["reason"] = interp.reason
    return d


def interpretation_from_dict(d: dict) -> Interpretation:
    """Deserialize an Interpretation from a dict."""
    return Interpretation(
        interpretation_id=d["interpretation_id"],
        replaces=d.get("replaces"),
        reason=d.get("reason", ""),
    )


def law_dataset_to_dict(law: LawDataset) -> dict:
    """Serialize a LawDataset to a JSON-compatible dict."""
    return {
        "law_id": law.law_id,
        "version": law.version,
        "society_id": law.society_id,
        "norms": [norm_to_dict(n) for n in law.norms],
        "procedures": [procedure_to_dict(p) for p in law.procedures],
        "interpretations": [interpretation_to_dict(i) for i in law.interpretations],
        "hash": law.hash,
    }


def law_dataset_from_dict(d: dict) -> LawDataset:
    """Deserialize a LawDataset from a dict."""
    return LawDataset(
        law_id=d["law_id"],
        version=d["version"],
        society_id=d["society_id"],
        norms=[norm_from_dict(n) for n in d.get("norms", [])],
        procedures=[procedure_from_dict(p) for p in d.get("procedures", [])],
        interpretations=[interpretation_from_dict(i) for i in d.get("interpretations", [])],
    )


def delegation_to_dict(deleg: Delegation) -> dict:
    """Serialize a Delegation to a JSON-compatible dict."""
    d: dict = {
        "delegation_id": deleg.delegation_id,
        "delegator": deleg.delegator,
        "delegate": deleg.delegate,
        "scope": deleg.scope,
        "permissions": deleg.permissions,
        "active": deleg.active,
        "max_depth": deleg.max_depth,
    }
    if deleg.expires_at:
        d["expires_at"] = deleg.expires_at
    return d


def delegation_from_dict(d: dict) -> Delegation:
    """Deserialize a Delegation from a dict."""
    deleg = Delegation(
        delegation_id=d["delegation_id"],
        delegator=d["delegator"],
        delegate=d["delegate"],
        scope=d["scope"],
        permissions=d["permissions"],
        max_depth=d.get("max_depth", 1),
    )
    deleg.active = d.get("active", True)
    if d.get("expires_at"):
        deleg.expires_at = d["expires_at"]
    return deleg


def quorum_policy_to_dict(qp: QuorumPolicy) -> dict:
    """Serialize a QuorumPolicy to a JSON-compatible dict."""
    return {"mode": qp.mode.value, "required": qp.required}


def quorum_policy_from_dict(d: dict) -> QuorumPolicy:
    """Deserialize a QuorumPolicy from a dict."""
    return QuorumPolicy(
        mode=QuorumMode(d["mode"]),
        required=d.get("required", 2),
    )
