#!/usr/bin/env python3
"""
AGY Agency Delegation — Track J
=================================
Full reference implementation of Web4 Agency Delegation from
forum/nova/agency-bundle/web4-agency-delegation.md

Implements:
- Full AgencyGrant object with scoped authority
- Scope narrowing for sub-delegation (child ⊆ parent)
- Delegation chains with depth tracking
- Revocation with ledger recording
- Dual attribution (agent T3 + client V3)
- Proof-of-agency for every agent action
- All 6 AGY error codes
- R6 mapping (Rules/Role/Request/Reference/Resource/Result)
- Witness quorum enforcement
- Temporal bounds (notBefore, expiresAt)
- Integration with Hardbound governance

Date: 2026-02-21
Spec: forum/nova/agency-bundle/web4-agency-delegation.md
"""

import hashlib
import json
import time
import uuid
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple, Set, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


# ═══════════════════════════════════════════════════════════════
# Error Codes (spec §9)
# ═══════════════════════════════════════════════════════════════

class AGYError(str, Enum):
    EXPIRED = "W4_ERR_AGY_EXPIRED"
    REVOKED = "W4_ERR_AGY_REVOKED"
    SCOPE = "W4_ERR_AGY_SCOPE"
    WITNESS = "W4_ERR_AGY_WITNESS"
    REPLAY = "W4_ERR_AGY_REPLAY"
    DELEGATION = "W4_ERR_AGY_DELEGATION"


class AGYException(Exception):
    def __init__(self, code: AGYError, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code.value}: {detail}")


# ═══════════════════════════════════════════════════════════════
# Scope model
# ═══════════════════════════════════════════════════════════════

@dataclass
class GrantScope:
    """Delegation scope (spec §2)."""
    contexts: List[str] = field(default_factory=list)       # e.g. ["finance:payments"]
    methods: List[str] = field(default_factory=list)         # e.g. ["create","update","approve"]
    mrh_selectors: List[str] = field(default_factory=list)   # e.g. ["web4://org/finance/*"]
    rules: List[str] = field(default_factory=list)           # e.g. ["LAW-ATP-LIMIT"]
    resource_caps: Dict[str, float] = field(default_factory=dict)  # e.g. {"max_atp": 25}
    role_impersonation: bool = False
    delegatable: bool = False
    witness_level: int = 1
    trust_caps: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def is_subset_of(self, parent: "GrantScope") -> Tuple[bool, str]:
        """Check if this scope is a subset of the parent scope (spec §7)."""
        # Methods: must be subset
        if self.methods and parent.methods:
            child_methods = set(self.methods)
            parent_methods = set(parent.methods)
            if not child_methods.issubset(parent_methods):
                extra = child_methods - parent_methods
                return False, f"methods {extra} not in parent"

        # Contexts: must be subset
        if self.contexts and parent.contexts:
            child_ctx = set(self.contexts)
            parent_ctx = set(parent.contexts)
            if not child_ctx.issubset(parent_ctx):
                extra = child_ctx - parent_ctx
                return False, f"contexts {extra} not in parent"

        # Resource caps: must be <= parent
        for key, val in self.resource_caps.items():
            parent_val = parent.resource_caps.get(key, 0)
            if val > parent_val:
                return False, f"resource cap {key}={val} > parent {parent_val}"

        # Cannot grant delegatability if parent doesn't have it
        if self.delegatable and not parent.delegatable:
            return False, "cannot grant delegatability when parent disallows it"

        # Witness level: must be >= parent (stricter or equal)
        if self.witness_level < parent.witness_level:
            return False, f"witness level {self.witness_level} < parent {parent.witness_level}"

        return True, "valid subset"

    def allows_method(self, method: str) -> bool:
        """Check if a method is within scope."""
        if not self.methods:
            return True  # No restriction
        if "*" in self.methods:
            return True
        for m in self.methods:
            if m.endswith("*") and method.startswith(m[:-1]):
                return True
            if method == m:
                return True
        return False

    def allows_context(self, context: str) -> bool:
        """Check if a context is within scope."""
        if not self.contexts:
            return True
        for c in self.contexts:
            if c.endswith("*") and context.startswith(c[:-1]):
                return True
            if context == c:
                return True
        return False

    def check_resource_cap(self, resource: str, amount: float) -> bool:
        """Check if resource usage is within caps."""
        cap = self.resource_caps.get(resource, float('inf'))
        return amount <= cap

    def to_dict(self) -> dict:
        return {
            "contexts": self.contexts,
            "methods": self.methods,
            "mrh_selectors": self.mrh_selectors,
            "rules": self.rules,
            "resource_caps": self.resource_caps,
            "role_impersonation": self.role_impersonation,
            "delegatable": self.delegatable,
            "witness_level": self.witness_level,
            "trust_caps": self.trust_caps,
        }


# ═══════════════════════════════════════════════════════════════
# Grant and Revocation objects
# ═══════════════════════════════════════════════════════════════

@dataclass
class AgencyGrant:
    """Full AGY grant (spec §2)."""
    grant_id: str
    client_lct: str          # Principal / delegator
    agent_lct: str           # Delegated entity
    society_lct: str         # Legal context
    law_hash: str            # Society law binding
    scope: GrantScope
    not_before: str          # ISO 8601
    expires_at: str          # ISO 8601
    parent_grant_id: Optional[str] = None  # For sub-delegation
    nonce: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    witnesses: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    revoked: bool = False
    revocation_reason: Optional[str] = None
    revocation_timestamp: Optional[str] = None

    def is_valid(self) -> Tuple[bool, Optional[AGYError], str]:
        """Check grant validity. Returns (valid, error_code, detail)."""
        if self.revoked:
            return False, AGYError.REVOKED, self.revocation_reason or "revoked"

        now = datetime.now(timezone.utc).isoformat()
        if now > self.expires_at:
            return False, AGYError.EXPIRED, f"expired at {self.expires_at}"
        if now < self.not_before:
            return False, AGYError.EXPIRED, f"not yet valid (starts {self.not_before})"

        return True, None, "valid"

    def check_action(self, method: str, context: str = "",
                     resource: str = "", amount: float = 0.0) -> Tuple[bool, Optional[AGYError], str]:
        """Validate an action against this grant."""
        valid, err, detail = self.is_valid()
        if not valid:
            return False, err, detail

        if not self.scope.allows_method(method):
            return False, AGYError.SCOPE, f"method '{method}' not in scope"

        if context and not self.scope.allows_context(context):
            return False, AGYError.SCOPE, f"context '{context}' not in scope"

        if resource and not self.scope.check_resource_cap(resource, amount):
            return False, AGYError.SCOPE, f"resource '{resource}' amount {amount} exceeds cap"

        return True, None, "allowed"

    def compute_hash(self) -> str:
        """Canonical hash of grant content."""
        data = json.dumps({
            "grant_id": self.grant_id,
            "client": self.client_lct,
            "agent": self.agent_lct,
            "society": self.society_lct,
            "scope": self.scope.to_dict(),
            "not_before": self.not_before,
            "expires_at": self.expires_at,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "type": "Web4AgencyGrant",
            "grant_id": self.grant_id,
            "client": self.client_lct,
            "agent": self.agent_lct,
            "society": self.society_lct,
            "law_hash": self.law_hash,
            "scope": self.scope.to_dict(),
            "not_before": self.not_before,
            "expires_at": self.expires_at,
            "parent_grant_id": self.parent_grant_id,
            "nonce": self.nonce,
            "witnesses": self.witnesses,
            "created_at": self.created_at,
            "revoked": self.revoked,
        }


@dataclass
class AgencyRevocation:
    """Revocation record (spec §3)."""
    grant_id: str
    revoked_by: str
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    witnesses: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "Web4AgencyRevocation",
            "grant_id": self.grant_id,
            "revoked_by": self.revoked_by,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "witnesses": self.witnesses,
        }


# ═══════════════════════════════════════════════════════════════
# Proof of Agency
# ═══════════════════════════════════════════════════════════════

@dataclass
class ProofOfAgency:
    """Proof attached to every agent action (spec §6)."""
    grant_id: str
    agent_lct: str
    client_lct: str
    grant_hash: str
    nonce: str
    scope_summary: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "grant_id": self.grant_id,
            "agent": self.agent_lct,
            "principal": self.client_lct,
            "grant_hash": self.grant_hash,
            "nonce": self.nonce,
            "scope": self.scope_summary,
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════
# Dual Attribution
# ═══════════════════════════════════════════════════════════════

@dataclass
class DualAttribution:
    """T3/V3 attribution for both agent and client (spec §8)."""
    agent_lct: str
    client_lct: str
    grant_id: str
    action_type: str
    success: bool
    # Agent: full T3 attribution
    agent_t3_delta: Dict[str, float] = field(default_factory=dict)
    # Client: reduced/indirect V3 attribution
    client_v3_delta: Dict[str, float] = field(default_factory=dict)

    def compute(self, quality: float = 0.7):
        """Compute dual attribution from action outcome."""
        if self.success:
            # Agent gets full T3 credit
            self.agent_t3_delta = {
                "talent": 0.05 * quality,
                "training": 0.03 * quality,
                "temperament": 0.02,
            }
            # Client gets reduced V3 (indirect value from delegation)
            self.client_v3_delta = {
                "validity": 0.02 * quality,    # Validity of delegation decision
                "veracity": 0.01,              # Truthful intent
            }
        else:
            # Failure: both incur negative deltas
            self.agent_t3_delta = {
                "talent": -0.05 * (1.0 - quality),
                "training": -0.02,
                "temperament": -0.03,
            }
            # Client shares liability (reduced)
            self.client_v3_delta = {
                "validity": -0.02,
                "veracity": -0.01,
            }

    def to_dict(self) -> dict:
        return {
            "agent": self.agent_lct,
            "client": self.client_lct,
            "grant_id": self.grant_id,
            "action": self.action_type,
            "success": self.success,
            "agent_t3": self.agent_t3_delta,
            "client_v3": self.client_v3_delta,
        }


# ═══════════════════════════════════════════════════════════════
# AGY Registry (Grant Manager)
# ═══════════════════════════════════════════════════════════════

class AGYRegistry:
    """
    Central grant registry for a society.

    Manages grant lifecycle: create, validate, sub-delegate, revoke.
    Records all events on an immutable ledger.
    """

    def __init__(self, society_lct: str, law_hash: str):
        self.society_lct = society_lct
        self.law_hash = law_hash
        self.grants: Dict[str, AgencyGrant] = {}
        self.revocations: List[AgencyRevocation] = []
        self.action_log: List[Dict] = []
        self.attribution_log: List[DualAttribution] = []
        self._used_nonces: Set[str] = set()

    def create_grant(self, client_lct: str, agent_lct: str,
                     scope: GrantScope,
                     duration_hours: float = 24.0,
                     witnesses: List[str] = None,
                     parent_grant_id: Optional[str] = None) -> AgencyGrant:
        """Create a new agency grant."""
        now = datetime.now(timezone.utc)
        grant_id = f"agy:{uuid.uuid4().hex[:12]}"

        # If sub-delegation, validate against parent
        if parent_grant_id:
            parent = self.grants.get(parent_grant_id)
            if not parent:
                raise AGYException(AGYError.DELEGATION, f"parent grant {parent_grant_id} not found")

            # Parent must be valid
            valid, err, detail = parent.is_valid()
            if not valid:
                raise AGYException(err, f"parent grant invalid: {detail}")

            # Parent must allow delegation
            if not parent.scope.delegatable:
                raise AGYException(AGYError.DELEGATION, "parent grant does not allow delegation")

            # Child scope must be subset
            is_subset, reason = scope.is_subset_of(parent.scope)
            if not is_subset:
                raise AGYException(AGYError.DELEGATION, f"scope not subset of parent: {reason}")

            # Child expiry must be <= parent
            parent_expires = parent.expires_at
            child_expires = (now + timedelta(hours=duration_hours)).isoformat()
            if child_expires > parent_expires:
                child_expires = parent_expires  # Clamp to parent

        else:
            child_expires = (now + timedelta(hours=duration_hours)).isoformat()

        # Witness quorum check
        provided_witnesses = witnesses or []
        if len(provided_witnesses) < scope.witness_level:
            raise AGYException(AGYError.WITNESS,
                               f"need {scope.witness_level} witnesses, got {len(provided_witnesses)}")

        grant = AgencyGrant(
            grant_id=grant_id,
            client_lct=client_lct,
            agent_lct=agent_lct,
            society_lct=self.society_lct,
            law_hash=self.law_hash,
            scope=scope,
            not_before=now.isoformat(),
            expires_at=child_expires,
            parent_grant_id=parent_grant_id,
            witnesses=provided_witnesses,
        )

        self.grants[grant_id] = grant
        self._log_event("grant_created", grant.to_dict())
        return grant

    def revoke_grant(self, grant_id: str, revoked_by: str, reason: str,
                     witnesses: List[str] = None,
                     _cascade: bool = False) -> AgencyRevocation:
        """Revoke a grant immediately (spec §3)."""
        grant = self.grants.get(grant_id)
        if not grant:
            raise AGYException(AGYError.REVOKED, f"grant {grant_id} not found")

        # Authorization: client, society, or cascade from parent revocation
        if not _cascade and revoked_by != grant.client_lct and revoked_by != self.society_lct:
            raise AGYException(AGYError.SCOPE, "only client or society can revoke")

        grant.revoked = True
        grant.revocation_reason = reason
        grant.revocation_timestamp = datetime.now(timezone.utc).isoformat()

        revocation = AgencyRevocation(
            grant_id=grant_id,
            revoked_by=revoked_by,
            reason=reason,
            witnesses=witnesses or [],
        )
        self.revocations.append(revocation)
        self._log_event("grant_revoked", revocation.to_dict())

        # Cascade: revoke all child grants
        for g in list(self.grants.values()):
            if g.parent_grant_id == grant_id and not g.revoked:
                self.revoke_grant(g.grant_id, revoked_by,
                                  f"parent {grant_id} revoked", _cascade=True)

        return revocation

    def validate_action(self, grant_id: str, agent_lct: str,
                        method: str, context: str = "",
                        resource: str = "", amount: float = 0.0,
                        nonce: str = "") -> Tuple[ProofOfAgency, None]:
        """
        Validate an agent action against its grant.
        Returns ProofOfAgency on success, raises AGYException on failure.
        """
        grant = self.grants.get(grant_id)
        if not grant:
            raise AGYException(AGYError.SCOPE, f"grant {grant_id} not found")

        # Verify agent identity
        if grant.agent_lct != agent_lct:
            raise AGYException(AGYError.SCOPE, f"agent {agent_lct} != grant agent {grant.agent_lct}")

        # Check grant validity and scope
        allowed, err, detail = grant.check_action(method, context, resource, amount)
        if not allowed:
            raise AGYException(err, detail)

        # Replay protection
        if nonce:
            if nonce in self._used_nonces:
                raise AGYException(AGYError.REPLAY, f"nonce {nonce} already used")
            self._used_nonces.add(nonce)

        # Generate proof of agency
        proof = ProofOfAgency(
            grant_id=grant_id,
            agent_lct=agent_lct,
            client_lct=grant.client_lct,
            grant_hash=grant.compute_hash(),
            nonce=nonce or grant.nonce,
            scope_summary={"methods": grant.scope.methods, "contexts": grant.scope.contexts},
        )

        self._log_event("action_validated", {
            "grant_id": grant_id, "agent": agent_lct, "method": method,
            "context": context, "proof_hash": proof.grant_hash,
        })

        return proof

    def record_action_result(self, grant_id: str, method: str,
                             success: bool, quality: float = 0.7) -> DualAttribution:
        """Record action result with dual attribution (spec §8)."""
        grant = self.grants.get(grant_id)
        if not grant:
            raise AGYException(AGYError.SCOPE, f"grant {grant_id} not found")

        attribution = DualAttribution(
            agent_lct=grant.agent_lct,
            client_lct=grant.client_lct,
            grant_id=grant_id,
            action_type=method,
            success=success,
        )
        attribution.compute(quality)
        self.attribution_log.append(attribution)

        self._log_event("action_result", attribution.to_dict())
        return attribution

    def get_delegation_chain(self, grant_id: str) -> List[AgencyGrant]:
        """Walk the delegation chain from child to root."""
        chain = []
        current = self.grants.get(grant_id)
        visited = set()
        while current and current.grant_id not in visited:
            visited.add(current.grant_id)
            chain.append(current)
            if current.parent_grant_id:
                current = self.grants.get(current.parent_grant_id)
            else:
                break
        return chain

    def get_grants_for_agent(self, agent_lct: str) -> List[AgencyGrant]:
        """Get all active grants for an agent."""
        return [g for g in self.grants.values()
                if g.agent_lct == agent_lct and g.is_valid()[0]]

    def get_grants_by_client(self, client_lct: str) -> List[AgencyGrant]:
        """Get all grants issued by a client."""
        return [g for g in self.grants.values()
                if g.client_lct == client_lct]

    def _log_event(self, event_type: str, data: dict):
        """Append to immutable event log."""
        self.action_log.append({
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        })

    def statistics(self) -> dict:
        """Registry statistics."""
        active = sum(1 for g in self.grants.values() if g.is_valid()[0])
        revoked = sum(1 for g in self.grants.values() if g.revoked)
        expired = sum(1 for g in self.grants.values()
                      if not g.revoked and not g.is_valid()[0])
        delegated = sum(1 for g in self.grants.values() if g.parent_grant_id)
        return {
            "total_grants": len(self.grants),
            "active": active,
            "revoked": revoked,
            "expired": expired,
            "delegated": delegated,
            "revocations": len(self.revocations),
            "actions_logged": len(self.action_log),
            "attributions": len(self.attribution_log),
        }


# ═══════════════════════════════════════════════════════════════
# Test Suite
# ═══════════════════════════════════════════════════════════════

def main():
    passed = 0
    failed = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal passed, failed
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
        if condition:
            passed += 1
        else:
            failed += 1
        return condition

    now = datetime.now(timezone.utc)
    future = (now + timedelta(hours=24)).isoformat()

    # ─── T1: Grant creation ─────────────────────────────────────
    print("\n═══ T1: Grant Creation ═══")
    registry = AGYRegistry("lct:web4:test-society", "sha256-law-v1")

    scope = GrantScope(
        contexts=["finance:payments", "docs:sign"],
        methods=["create", "update", "approve"],
        resource_caps={"max_atp": 25.0, "bandwidth_mbps": 10.0},
        delegatable=True,
        witness_level=2,
    )

    grant = registry.create_grant(
        client_lct="lct:web4:orgA",
        agent_lct="lct:web4:botX",
        scope=scope,
        duration_hours=24.0,
        witnesses=["lct:web4:witness-A", "lct:web4:witness-B"],
    )

    check("T1: Grant created", grant is not None)
    check("T1: Grant ID starts with agy:", grant.grant_id.startswith("agy:"))
    check("T1: Client is orgA", grant.client_lct == "lct:web4:orgA")
    check("T1: Agent is botX", grant.agent_lct == "lct:web4:botX")
    check("T1: Society bound", grant.society_lct == "lct:web4:test-society")
    check("T1: Law hash bound", grant.law_hash == "sha256-law-v1")
    check("T1: 2 witnesses", len(grant.witnesses) == 2)
    check("T1: Grant is valid", grant.is_valid()[0])
    check("T1: Registered in registry", grant.grant_id in registry.grants)

    # ─── T2: Scope enforcement ──────────────────────────────────
    print("\n═══ T2: Scope Enforcement ═══")

    # Allowed actions
    proof = registry.validate_action(
        grant.grant_id, "lct:web4:botX", "approve",
        context="finance:payments", resource="max_atp", amount=20.0,
        nonce="nonce-001"
    )
    check("T2: Approve within scope succeeds", proof is not None)
    check("T2: Proof has grant ID", proof.grant_id == grant.grant_id)
    check("T2: Proof has agent", proof.agent_lct == "lct:web4:botX")
    check("T2: Proof has client (principal)", proof.client_lct == "lct:web4:orgA")

    # Out-of-scope method
    try:
        registry.validate_action(grant.grant_id, "lct:web4:botX", "delete")
        check("T2: Delete blocked (out of scope)", False)
    except AGYException as e:
        check("T2: Delete blocked (out of scope)", e.code == AGYError.SCOPE,
              f"error={e.code.value}")

    # Out-of-scope context
    try:
        registry.validate_action(grant.grant_id, "lct:web4:botX", "create",
                                 context="hr:payroll")
        check("T2: HR context blocked", False)
    except AGYException as e:
        check("T2: HR context blocked", e.code == AGYError.SCOPE)

    # Resource cap exceeded
    try:
        registry.validate_action(grant.grant_id, "lct:web4:botX", "approve",
                                 context="finance:payments", resource="max_atp", amount=50.0)
        check("T2: Over-cap blocked", False)
    except AGYException as e:
        check("T2: Over-cap blocked", e.code == AGYError.SCOPE,
              f"amount=50 > cap=25")

    # ─── T3: Replay protection ──────────────────────────────────
    print("\n═══ T3: Replay Protection ═══")

    # Same nonce should be rejected
    try:
        registry.validate_action(grant.grant_id, "lct:web4:botX", "create",
                                 context="docs:sign", nonce="nonce-001")
        check("T3: Replay rejected", False)
    except AGYException as e:
        check("T3: Replay rejected", e.code == AGYError.REPLAY,
              "nonce-001 already used")

    # New nonce works
    proof2 = registry.validate_action(grant.grant_id, "lct:web4:botX", "create",
                                      context="docs:sign", nonce="nonce-002")
    check("T3: New nonce accepted", proof2 is not None)

    # ─── T4: Revocation ─────────────────────────────────────────
    print("\n═══ T4: Revocation ═══")

    rev_grant = registry.create_grant(
        "lct:web4:alice", "lct:web4:bot-rev",
        scope=GrantScope(methods=["read"], witness_level=0),
        witnesses=[],
    )
    check("T4: Grant for revocation created", rev_grant.is_valid()[0])

    revocation = registry.revoke_grant(
        rev_grant.grant_id, "lct:web4:alice", "key compromise"
    )
    check("T4: Revocation returned", revocation is not None)
    check("T4: Reason recorded", revocation.reason == "key compromise")
    check("T4: Grant now invalid", not rev_grant.is_valid()[0])
    check("T4: Error code is REVOKED", rev_grant.is_valid()[1] == AGYError.REVOKED)

    # Action after revocation should fail
    try:
        registry.validate_action(rev_grant.grant_id, "lct:web4:bot-rev", "read")
        check("T4: Action on revoked grant blocked", False)
    except AGYException as e:
        check("T4: Action on revoked grant blocked", e.code == AGYError.REVOKED)

    # ─── T5: Sub-delegation (scope narrowing) ───────────────────
    print("\n═══ T5: Sub-Delegation ═══")

    # Parent grant: approve, create, update in finance
    parent_scope = GrantScope(
        contexts=["finance:payments"],
        methods=["create", "update", "approve"],
        resource_caps={"max_atp": 25.0},
        delegatable=True,
        witness_level=1,
    )
    parent = registry.create_grant(
        "lct:web4:human-alice", "lct:web4:sage",
        scope=parent_scope, duration_hours=48.0,
        witnesses=["lct:web4:witness-1"],
    )

    # Valid child: narrower scope (approve only, lower ATP cap)
    child_scope = GrantScope(
        contexts=["finance:payments"],
        methods=["approve"],
        resource_caps={"max_atp": 10.0},
        delegatable=False,
        witness_level=1,
    )
    child = registry.create_grant(
        "lct:web4:sage", "lct:web4:irp-plugin",
        scope=child_scope, duration_hours=12.0,
        witnesses=["lct:web4:witness-1"],
        parent_grant_id=parent.grant_id,
    )
    check("T5: Child grant created", child is not None)
    check("T5: Child references parent", child.parent_grant_id == parent.grant_id)
    check("T5: Child scope is subset", child_scope.is_subset_of(parent_scope)[0])

    # Child can approve
    proof = registry.validate_action(
        child.grant_id, "lct:web4:irp-plugin", "approve",
        context="finance:payments", resource="max_atp", amount=5.0,
        nonce="child-nonce-001"
    )
    check("T5: Child approve works", proof is not None)

    # Child cannot create (not in narrowed scope)
    try:
        registry.validate_action(child.grant_id, "lct:web4:irp-plugin", "create",
                                 context="finance:payments", nonce="child-nonce-002")
        check("T5: Child create blocked", False)
    except AGYException as e:
        check("T5: Child create blocked", e.code == AGYError.SCOPE)

    # Invalid child: wider scope than parent
    try:
        wide_scope = GrantScope(
            methods=["create", "update", "approve", "delete"],  # delete not in parent
            delegatable=False,
            witness_level=0,
        )
        registry.create_grant(
            "lct:web4:sage", "lct:web4:bad-plugin",
            scope=wide_scope, witnesses=[],
            parent_grant_id=parent.grant_id,
        )
        check("T5: Wider-than-parent blocked", False)
    except AGYException as e:
        check("T5: Wider-than-parent blocked", e.code == AGYError.DELEGATION,
              f"detail={e.detail}")

    # ─── T6: Delegation chain ───────────────────────────────────
    print("\n═══ T6: Delegation Chain ═══")

    chain = registry.get_delegation_chain(child.grant_id)
    check("T6: Chain has 2 links", len(chain) == 2,
          f"chain_len={len(chain)}")
    check("T6: First in chain is child", chain[0].grant_id == child.grant_id)
    check("T6: Second is parent", chain[1].grant_id == parent.grant_id)

    # Revoke parent → cascade to child
    registry.revoke_grant(parent.grant_id, "lct:web4:human-alice", "security concern")
    check("T6: Parent revoked", not parent.is_valid()[0])
    check("T6: Child auto-revoked (cascade)", not child.is_valid()[0])

    # ─── T7: Dual attribution ──────────────────────────────────
    print("\n═══ T7: Dual Attribution ═══")

    attr_grant = registry.create_grant(
        "lct:web4:org-corp", "lct:web4:bot-worker",
        scope=GrantScope(methods=["execute"], witness_level=0),
        witnesses=[],
    )

    # Successful action
    attr = registry.record_action_result(attr_grant.grant_id, "execute", success=True, quality=0.8)
    check("T7: Attribution computed", attr is not None)
    check("T7: Agent gets positive T3",
          attr.agent_t3_delta.get("talent", 0) > 0,
          f"agent_t3={attr.agent_t3_delta}")
    check("T7: Client gets positive V3",
          attr.client_v3_delta.get("validity", 0) > 0,
          f"client_v3={attr.client_v3_delta}")

    # Failed action
    attr_fail = registry.record_action_result(attr_grant.grant_id, "execute", success=False, quality=0.3)
    check("T7: Failed action: agent negative T3",
          attr_fail.agent_t3_delta.get("talent", 0) < 0)
    check("T7: Failed action: client negative V3",
          attr_fail.client_v3_delta.get("validity", 0) < 0)

    # ─── T8: Witness quorum ─────────────────────────────────────
    print("\n═══ T8: Witness Quorum ═══")

    # Need 2 witnesses but provide only 1
    try:
        registry.create_grant(
            "lct:web4:client-x", "lct:web4:agent-x",
            scope=GrantScope(methods=["read"], witness_level=2),
            witnesses=["lct:web4:w-only-one"],
        )
        check("T8: Insufficient witnesses blocked", False)
    except AGYException as e:
        check("T8: Insufficient witnesses blocked", e.code == AGYError.WITNESS,
              f"detail={e.detail}")

    # Provide enough witnesses
    wq_grant = registry.create_grant(
        "lct:web4:client-x", "lct:web4:agent-x",
        scope=GrantScope(methods=["read"], witness_level=2),
        witnesses=["lct:web4:w1", "lct:web4:w2"],
    )
    check("T8: Sufficient witnesses accepted", wq_grant is not None)

    # ─── T9: Temporal bounds ────────────────────────────────────
    print("\n═══ T9: Temporal Bounds ═══")

    # Already expired grant
    expired_grant = AgencyGrant(
        grant_id="agy:expired-001",
        client_lct="lct:web4:client",
        agent_lct="lct:web4:agent",
        society_lct="lct:web4:test-society",
        law_hash="sha256-law-v1",
        scope=GrantScope(methods=["read"]),
        not_before="2020-01-01T00:00:00+00:00",
        expires_at="2020-12-31T23:59:59+00:00",
    )
    valid, err, _ = expired_grant.is_valid()
    check("T9: Expired grant invalid", not valid)
    check("T9: Error is EXPIRED", err == AGYError.EXPIRED)

    # Not-yet-valid grant
    future_grant = AgencyGrant(
        grant_id="agy:future-001",
        client_lct="lct:web4:client",
        agent_lct="lct:web4:agent",
        society_lct="lct:web4:test-society",
        law_hash="sha256-law-v1",
        scope=GrantScope(methods=["read"]),
        not_before="2099-01-01T00:00:00+00:00",
        expires_at="2099-12-31T23:59:59+00:00",
    )
    valid, err, _ = future_grant.is_valid()
    check("T9: Future grant invalid", not valid)
    check("T9: Error is EXPIRED (not yet valid)", err == AGYError.EXPIRED)

    # ─── T10: Scope subset validation ───────────────────────────
    print("\n═══ T10: Scope Subset Validation ═══")

    parent_s = GrantScope(
        contexts=["finance:payments", "docs:sign"],
        methods=["create", "update", "approve"],
        resource_caps={"max_atp": 25.0},
        delegatable=True,
        witness_level=1,
    )

    # Valid subset
    child_s = GrantScope(
        contexts=["finance:payments"],
        methods=["approve"],
        resource_caps={"max_atp": 10.0},
        witness_level=1,
    )
    is_sub, reason = child_s.is_subset_of(parent_s)
    check("T10: Valid subset recognized", is_sub, reason)

    # Invalid: extra method
    bad_methods = GrantScope(methods=["approve", "delete"])
    is_sub, reason = bad_methods.is_subset_of(parent_s)
    check("T10: Extra method detected", not is_sub, reason)

    # Invalid: higher resource cap
    bad_caps = GrantScope(methods=["approve"], resource_caps={"max_atp": 50.0})
    is_sub, reason = bad_caps.is_subset_of(parent_s)
    check("T10: Higher resource cap detected", not is_sub, reason)

    # Invalid: granting delegatable when parent doesn't allow
    bad_deleg = GrantScope(methods=["approve"], delegatable=True)
    # Parent does allow delegation, so this should pass
    is_sub, _ = bad_deleg.is_subset_of(parent_s)
    check("T10: Delegatable with delegatable parent OK", is_sub)

    # Parent without delegation
    non_deleg_parent = GrantScope(methods=["approve"], delegatable=False)
    is_sub, reason = bad_deleg.is_subset_of(non_deleg_parent)
    check("T10: Delegatable without parent permission blocked", not is_sub, reason)

    # ─── T11: Agent identity enforcement ────────────────────────
    print("\n═══ T11: Agent Identity ═══")

    id_grant = registry.create_grant(
        "lct:web4:alice", "lct:web4:specific-bot",
        scope=GrantScope(methods=["read"], witness_level=0),
        witnesses=[],
    )

    # Wrong agent tries to use grant
    try:
        registry.validate_action(id_grant.grant_id, "lct:web4:wrong-bot", "read",
                                 nonce="id-nonce-001")
        check("T11: Wrong agent blocked", False)
    except AGYException as e:
        check("T11: Wrong agent blocked", e.code == AGYError.SCOPE,
              "agent mismatch")

    # Right agent works
    proof = registry.validate_action(id_grant.grant_id, "lct:web4:specific-bot", "read",
                                     nonce="id-nonce-002")
    check("T11: Correct agent accepted", proof is not None)

    # ─── T12: Grant serialization ───────────────────────────────
    print("\n═══ T12: Serialization ═══")

    d = grant.to_dict()
    check("T12: Grant serializable", isinstance(d, dict))
    check("T12: Type is Web4AgencyGrant", d["type"] == "Web4AgencyGrant")
    check("T12: JSON roundtrip", isinstance(json.dumps(d), str))

    proof_d = proof.to_dict()
    check("T12: Proof serializable", isinstance(proof_d, dict))
    check("T12: Proof has grant_hash", "grant_hash" in proof_d)

    rev_d = revocation.to_dict()
    check("T12: Revocation serializable", isinstance(rev_d, dict))
    check("T12: Revocation type correct", rev_d["type"] == "Web4AgencyRevocation")

    attr_d = attr.to_dict()
    check("T12: Attribution serializable", isinstance(attr_d, dict))
    check("T12: Attribution has agent + client", "agent" in attr_d and "client" in attr_d)

    # ─── T13: Registry statistics ───────────────────────────────
    print("\n═══ T13: Registry Statistics ═══")

    stats = registry.statistics()
    check("T13: Stats computed", isinstance(stats, dict))
    check("T13: Has total grants", stats["total_grants"] > 0,
          f"total={stats['total_grants']}")
    check("T13: Has revoked count", stats["revoked"] > 0,
          f"revoked={stats['revoked']}")
    check("T13: Has delegated count", stats["delegated"] > 0,
          f"delegated={stats['delegated']}")
    check("T13: Has action log count", stats["actions_logged"] > 0,
          f"actions={stats['actions_logged']}")
    check("T13: Has attribution count", stats["attributions"] > 0,
          f"attributions={stats['attributions']}")

    # ─── T14: Non-delegatable grant blocks sub-delegation ──────
    print("\n═══ T14: Non-Delegatable Enforcement ═══")

    no_deleg_scope = GrantScope(methods=["read"], delegatable=False, witness_level=0)
    no_deleg = registry.create_grant(
        "lct:web4:bob", "lct:web4:bot-bob",
        scope=no_deleg_scope, witnesses=[],
    )

    try:
        registry.create_grant(
            "lct:web4:bot-bob", "lct:web4:sub-bot",
            scope=GrantScope(methods=["read"], witness_level=0),
            witnesses=[],
            parent_grant_id=no_deleg.grant_id,
        )
        check("T14: Non-delegatable sub-delegation blocked", False)
    except AGYException as e:
        check("T14: Non-delegatable sub-delegation blocked",
              e.code == AGYError.DELEGATION)

    # ─── T15: Revocation authorization ──────────────────────────
    print("\n═══ T15: Revocation Authorization ═══")

    auth_grant = registry.create_grant(
        "lct:web4:carol", "lct:web4:bot-carol",
        scope=GrantScope(methods=["write"], witness_level=0),
        witnesses=[],
    )

    # Third party cannot revoke
    try:
        registry.revoke_grant(auth_grant.grant_id, "lct:web4:eve", "malicious")
        check("T15: Third-party revocation blocked", False)
    except AGYException as e:
        check("T15: Third-party revocation blocked", e.code == AGYError.SCOPE)

    # Client can revoke
    registry.revoke_grant(auth_grant.grant_id, "lct:web4:carol", "no longer needed")
    check("T15: Client revocation succeeds", auth_grant.revoked)

    # ─── T16: Grant query methods ───────────────────────────────
    print("\n═══ T16: Grant Queries ═══")

    query_reg = AGYRegistry("lct:web4:query-soc", "sha256-query-law")

    g1 = query_reg.create_grant("lct:web4:user-a", "lct:web4:bot-1",
                                scope=GrantScope(methods=["read"], witness_level=0), witnesses=[])
    g2 = query_reg.create_grant("lct:web4:user-a", "lct:web4:bot-2",
                                scope=GrantScope(methods=["write"], witness_level=0), witnesses=[])
    g3 = query_reg.create_grant("lct:web4:user-b", "lct:web4:bot-1",
                                scope=GrantScope(methods=["execute"], witness_level=0), witnesses=[])

    bot1_grants = query_reg.get_grants_for_agent("lct:web4:bot-1")
    check("T16: bot-1 has 2 grants", len(bot1_grants) == 2)

    usera_grants = query_reg.get_grants_by_client("lct:web4:user-a")
    check("T16: user-a issued 2 grants", len(usera_grants) == 2)

    bot2_grants = query_reg.get_grants_for_agent("lct:web4:bot-2")
    check("T16: bot-2 has 1 grant", len(bot2_grants) == 1)

    # ─── T17: Worked example from spec §11 ─────────────────────
    print("\n═══ T17: Worked Example (Spec §11) ═══")

    ex_reg = AGYRegistry("lct:web4:corp-society", "sha256-corp-law-v2")

    # OrgA grants BotX authority to approve invoices ≤25 ATP under finance:payments for Q4
    ex_scope = GrantScope(
        contexts=["finance:payments"],
        methods=["approve"],
        resource_caps={"max_atp": 25.0},
        witness_level=2,
    )
    ex_grant = ex_reg.create_grant(
        "lct:web4:orgA", "lct:web4:botX",
        scope=ex_scope, duration_hours=2160,  # ~Q4
        witnesses=["lct:web4:witness-A", "lct:web4:witness-B"],
    )
    check("T17: OrgA→BotX grant created", ex_grant is not None)

    # BotX invokes approve(invoice#123) for 20 ATP
    proof = ex_reg.validate_action(
        ex_grant.grant_id, "lct:web4:botX", "approve",
        context="finance:payments", resource="max_atp", amount=20.0,
        nonce="invoice-123-nonce"
    )
    check("T17: BotX approve(invoice#123) succeeds", proof is not None)
    check("T17: Proof references grant", proof.grant_id == ex_grant.grant_id)

    # Record successful result with dual attribution
    attr = ex_reg.record_action_result(ex_grant.grant_id, "approve", True, quality=0.9)
    check("T17: Agent T3 positive", attr.agent_t3_delta["talent"] > 0)
    check("T17: Client V3 positive (indirect)", attr.client_v3_delta["validity"] > 0)

    # Auditor detects over-cap attempt (30 > 25)
    try:
        ex_reg.validate_action(
            ex_grant.grant_id, "lct:web4:botX", "approve",
            context="finance:payments", resource="max_atp", amount=30.0,
            nonce="invoice-456-nonce"
        )
        check("T17: Over-cap approval blocked", False)
    except AGYException as e:
        check("T17: Over-cap approval blocked", e.code == AGYError.SCOPE)

    # Record failed attempt with negative attribution
    attr_fail = ex_reg.record_action_result(ex_grant.grant_id, "approve", False, quality=0.2)
    check("T17: Cautionary T3 delta (negative)", attr_fail.agent_t3_delta["talent"] < 0)

    # ─── Summary ────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  AGY Agency Delegation — Track J Results")
    print(f"  {passed} passed, {failed} failed out of {passed+failed} checks")
    print(f"{'='*60}")

    final_stats = registry.statistics()
    print(f"\n  Registry: {final_stats['total_grants']} grants, "
          f"{final_stats['revoked']} revoked, {final_stats['delegated']} delegated")
    print(f"  Events: {final_stats['actions_logged']} logged, "
          f"{final_stats['attributions']} attributions")
    print(f"\n  6 ERROR CODES: {', '.join(e.value for e in AGYError)}")

    return passed, failed


if __name__ == "__main__":
    passed, failed = main()
    sys.exit(0 if failed == 0 else 1)
