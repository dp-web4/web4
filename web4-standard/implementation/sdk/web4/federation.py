"""
Web4 Federation — Society, Authority, Law (SAL)

Canonical implementation per web4-standard/core-spec/web4-society-authority-law.md.

SAL defines how entities are born into societies, how authority is delegated,
and how law governs actions. Every entity is born with a Citizen role as its
genesis pairing — this is immutable and prerequisite for all other roles.

Key concepts:
- Society: delegative entity with authority, law oracle, and quorum policy
- Authority: scoped delegation (domain-bounded, revocable)
- LawDataset: versioned norms, procedures, interpretations
- Fractal citizenship: societies nest (team → org → network → ecosystem)
- Law inheritance: child inherits parent law, may override with awareness

This module provides DATA STRUCTURES and simple operations, not a policy
engine. Policy evaluation belongs in HRM/PolicyGate.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set

from .lct import LCT, EntityType, BirthCertificate, MRHPairing
from .trust import T3, V3


# ── Role Types ───────────────────────────────────────────────────

class RoleType(str, Enum):
    """SAL role types (§5)."""
    CITIZEN = "citizen"        # Genesis, immutable, prerequisite for all others
    AUTHORITY = "authority"    # Scoped delegation of governance power
    LAW_ORACLE = "law_oracle"  # Publishes/verifies law datasets
    WITNESS = "witness"        # Co-signs ledger entries, provides attestations
    AUDITOR = "auditor"        # Traverses MRH, validates/adjusts T3/V3


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
    value: object         # threshold or allowed values
    description: str = ""

    def check(self, actual_value: float) -> bool:
        """Simple threshold check. Returns True if value satisfies the norm."""
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

    def __post_init__(self):
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

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def revoke(self):
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

    def __init__(self, society_id: str, name: str, parent: Optional[Society] = None):
        self.society_id = society_id
        self.name = name
        self.parent = parent

        # Citizens (LCT IDs)
        self.citizens: Set[str] = set()
        # Authority delegations
        self.delegations: List[Delegation] = []
        # Active law dataset
        self.law: Optional[LawDataset] = None
        # Quorum requirements
        self.witness_quorum: int = 2
        # Child societies
        self.children: List[Society] = []

        if parent:
            parent.children.append(self)

    def set_law(self, law: LawDataset):
        """Publish a new law dataset for this society."""
        self.law = law

    def effective_law(self) -> Optional[LawDataset]:
        """
        Get the effective law (§3.5).

        Child inherits parent law if no local law is set.
        If both exist, child law takes precedence (overrides parent).
        """
        if self.law is not None:
            return self.law
        if self.parent is not None:
            return self.parent.effective_law()
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
        return lct

    def is_citizen(self, lct_id: str) -> bool:
        """Check if an entity is a citizen of this society."""
        return lct_id in self.citizens

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
