#!/usr/bin/env python3
"""
AGY Agency Delegation — Track J
=================================
First reference implementation of the Web4 Agency Delegation framework.

Formal authority transfer mechanism:
- Client delegates specific authorities to Agent within scoped, attestable contexts
- Sub-delegation with scope narrowing (scope ⊆ parent_scope)
- Dual attribution: Agent T3 (execution), Client V3 (validity of delegation)
- Proof-of-agency on every agent action (grantId + ledger proof + nonce)
- ATP resource caps prevent runaway delegation
- Revocation with immediate effect

Closes the grantId placeholder in ACP executor.
"""

import hashlib
import json
import time
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set, Any
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════
# Core Types
# ═══════════════════════════════════════════════════════════════

class GrantStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"  # Awaiting witness signatures


class AGYError(str, Enum):
    EXPIRED = "W4_ERR_AGY_EXPIRED"
    REVOKED = "W4_ERR_AGY_REVOKED"
    SCOPE = "W4_ERR_AGY_SCOPE"
    WITNESS = "W4_ERR_AGY_WITNESS"
    REPLAY = "W4_ERR_AGY_REPLAY"
    DELEGATION = "W4_ERR_AGY_DELEGATION"
    TRUST = "W4_ERR_AGY_TRUST"
    RESOURCE = "W4_ERR_AGY_RESOURCE"


@dataclass
class ResourceCaps:
    """ATP and other resource limits for a grant."""
    max_atp: float = 100.0
    max_executions: int = 100
    rate_limit_per_hour: int = 10
    max_concurrent: int = 1

    def is_subset_of(self, parent: "ResourceCaps") -> bool:
        """Check if these caps are within parent caps."""
        return (self.max_atp <= parent.max_atp and
                self.max_executions <= parent.max_executions and
                self.rate_limit_per_hour <= parent.rate_limit_per_hour and
                self.max_concurrent <= parent.max_concurrent)

    def to_dict(self) -> dict:
        return {
            "max_atp": self.max_atp,
            "max_executions": self.max_executions,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "max_concurrent": self.max_concurrent,
        }


@dataclass
class TrustCaps:
    """Minimum T3/V3 trust requirements for a grant."""
    min_talent: float = 0.0
    min_training: float = 0.0
    min_temperament: float = 0.0
    min_veracity: float = 0.0
    min_validity: float = 0.0

    def is_subset_of(self, parent: "TrustCaps") -> bool:
        """Child trust caps must be >= parent (stricter or equal)."""
        return (self.min_talent >= parent.min_talent and
                self.min_training >= parent.min_training and
                self.min_temperament >= parent.min_temperament and
                self.min_veracity >= parent.min_veracity and
                self.min_validity >= parent.min_validity)

    def to_dict(self) -> dict:
        return {
            "t3_min": {"talent": self.min_talent, "training": self.min_training,
                       "temperament": self.min_temperament},
            "v3_floor": {"veracity": self.min_veracity, "validity": self.min_validity},
        }


@dataclass
class GrantScope:
    """What the agent is authorized to do."""
    methods: List[str]                          # Allowed actions
    contexts: List[str] = field(default_factory=list)  # Domain contexts
    mrh_selectors: List[str] = field(default_factory=list)  # MRH graph selectors
    resource_caps: ResourceCaps = field(default_factory=ResourceCaps)
    trust_caps: TrustCaps = field(default_factory=TrustCaps)
    delegatable: bool = False                   # Can agent sub-delegate?
    witness_level: int = 1                      # Required witness quorum
    role_impersonation: bool = False             # Agent cannot assume client role

    def is_subset_of(self, parent: "GrantScope") -> bool:
        """Verify this scope is within parent scope (for sub-delegation)."""
        # Methods must be a subset
        if not set(self.methods).issubset(set(parent.methods)):
            return False
        # Contexts must be a subset
        if self.contexts and not set(self.contexts).issubset(set(parent.contexts)):
            return False
        # Resource caps must be within parent's
        if not self.resource_caps.is_subset_of(parent.resource_caps):
            return False
        # Trust caps must be at least as strict
        if not self.trust_caps.is_subset_of(parent.trust_caps):
            return False
        # Can't grant delegation if parent doesn't allow it
        if self.delegatable and not parent.delegatable:
            return False
        # Witness level must be at least parent's
        if self.witness_level < parent.witness_level:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "methods": self.methods,
            "contexts": self.contexts,
            "mrh_selectors": self.mrh_selectors,
            "resource_caps": self.resource_caps.to_dict(),
            "trust_caps": self.trust_caps.to_dict(),
            "delegatable": self.delegatable,
            "witness_level": self.witness_level,
            "role_impersonation": self.role_impersonation,
        }


# ═══════════════════════════════════════════════════════════════
# Agency Grant
# ═══════════════════════════════════════════════════════════════

@dataclass
class AgencyGrant:
    """A formal authority delegation from client to agent."""
    grant_id: str
    client_lct: str                             # Principal (delegating authority)
    agent_lct: str                              # Agent (receiving authority)
    society_lct: str                            # Governance context
    scope: GrantScope
    not_before: float                           # Earliest activation (epoch)
    expires_at: float                           # Expiration deadline (epoch)
    law_hash: str = ""                          # Law version binding
    parent_grant_id: Optional[str] = None       # For sub-delegation chains
    nonce: str = ""                             # Session/replay protection
    witnesses: List[str] = field(default_factory=list)
    status: GrantStatus = GrantStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    atp_spent: float = 0.0                      # Running ATP consumption
    executions: int = 0                          # Running execution count
    last_execution_at: float = 0.0
    revocation_reason: str = ""

    def __post_init__(self):
        if not self.nonce:
            self.nonce = hashlib.sha256(
                f"{self.grant_id}:{self.client_lct}:{time.time()}".encode()
            ).hexdigest()[:16]

    def is_active(self) -> bool:
        now = time.time()
        return (self.status == GrantStatus.ACTIVE and
                now >= self.not_before and
                now <= self.expires_at)

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def compute_hash(self) -> str:
        """Compute grant hash for ledger proof."""
        data = json.dumps({
            "grant_id": self.grant_id,
            "client": self.client_lct,
            "agent": self.agent_lct,
            "society": self.society_lct,
            "scope": self.scope.to_dict(),
            "not_before": self.not_before,
            "expires_at": self.expires_at,
            "law_hash": self.law_hash,
            "nonce": self.nonce,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "@context": ["https://web4.io/contexts/sal.jsonld",
                         "https://web4.io/contexts/agy.jsonld"],
            "type": "Web4AgencyGrant",
            "grantId": self.grant_id,
            "client": self.client_lct,
            "agent": self.agent_lct,
            "society": self.society_lct,
            "scope": self.scope.to_dict(),
            "duration": {
                "notBefore": self.not_before,
                "expiresAt": self.expires_at,
            },
            "lawHash": self.law_hash,
            "parentGrant": self.parent_grant_id,
            "session": {"nonce": self.nonce},
            "witnesses": self.witnesses,
            "status": self.status.value,
            "grantHash": self.compute_hash(),
        }


# ═══════════════════════════════════════════════════════════════
# Agency Revocation
# ═══════════════════════════════════════════════════════════════

@dataclass
class AgencyRevocation:
    """Revocation of a delegation grant."""
    grant_id: str
    revoked_by: str                             # Must be client or authority
    reason: str
    timestamp: float = field(default_factory=time.time)
    witnesses: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "@context": ["https://web4.io/contexts/sal.jsonld",
                         "https://web4.io/contexts/agy.jsonld"],
            "type": "Web4AgencyRevocation",
            "grantId": self.grant_id,
            "revokedBy": self.revoked_by,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "witnesses": self.witnesses,
        }


# ═══════════════════════════════════════════════════════════════
# Proof of Agency
# ═══════════════════════════════════════════════════════════════

@dataclass
class ProofOfAgency:
    """Proof carried on every agent-originated action."""
    grant_id: str
    client_lct: str
    agent_lct: str
    scope_methods: List[str]
    grant_hash: str
    nonce: str
    action: str                                  # The action being performed
    action_nonce: str = ""                       # Per-action replay protection

    def __post_init__(self):
        if not self.action_nonce:
            self.action_nonce = hashlib.sha256(
                f"{self.grant_id}:{self.action}:{time.time()}".encode()
            ).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "grantId": self.grant_id,
            "principal": self.client_lct,
            "agent": self.agent_lct,
            "scope": self.scope_methods,
            "grantHash": self.grant_hash,
            "nonce": self.nonce,
            "action": self.action,
            "actionNonce": self.action_nonce,
        }


# ═══════════════════════════════════════════════════════════════
# Dual Attribution
# ═══════════════════════════════════════════════════════════════

@dataclass
class AttributionResult:
    """Reputation changes from a delegated action."""
    agent_t3_deltas: Dict[str, float]          # T3 updates for agent
    client_v3_deltas: Dict[str, float]         # V3 updates for client
    atp_cost: float
    action: str
    grant_id: str

    def to_dict(self) -> dict:
        return {
            "agent_t3": self.agent_t3_deltas,
            "client_v3": self.client_v3_deltas,
            "atp_cost": self.atp_cost,
            "action": self.action,
            "grant_id": self.grant_id,
        }


def compute_dual_attribution(action: str, success: bool,
                              quality: float = 0.7) -> AttributionResult:
    """
    Compute dual attribution for a delegated action.

    Agent gets T3 updates (execution quality).
    Client gets V3 updates (delegation validity).
    """
    base_delta = 0.01 * quality

    if success:
        agent_t3 = {
            "talent": round(base_delta, 4),
            "training": round(base_delta, 4),
            "temperament": round(base_delta * 0.5, 4),
        }
        client_v3 = {
            "veracity": round(base_delta * 2, 4),
            "validity": round(base_delta, 4),
        }
    else:
        agent_t3 = {
            "talent": round(-base_delta * 0.5, 4),
            "training": round(base_delta * 0.2, 4),  # Still learned
            "temperament": round(-base_delta, 4),
        }
        client_v3 = {
            "veracity": round(-base_delta, 4),
            "validity": round(-base_delta * 0.5, 4),  # Poor delegation design
        }

    return AttributionResult(
        agent_t3_deltas=agent_t3,
        client_v3_deltas=client_v3,
        atp_cost=5.0,
        action=action,
        grant_id="",  # Filled by caller
    )


# ═══════════════════════════════════════════════════════════════
# Agency Registry
# ═══════════════════════════════════════════════════════════════

class AgencyRegistry:
    """
    Central registry for managing agency grants.

    Handles creation, validation, execution, revocation,
    and sub-delegation chain verification.
    """

    def __init__(self, society_lct: str):
        self.society_lct = society_lct
        self.grants: Dict[str, AgencyGrant] = {}
        self.revocations: List[AgencyRevocation] = []
        self.used_nonces: Set[str] = set()
        self.attribution_log: List[AttributionResult] = []
        self._grant_counter = 0

    def create_grant(
        self,
        client_lct: str,
        agent_lct: str,
        scope: GrantScope,
        duration_hours: float = 24.0,
        law_hash: str = "",
        witnesses: Optional[List[str]] = None,
        parent_grant_id: Optional[str] = None,
    ) -> Tuple[AgencyGrant, Optional[str]]:
        """
        Create a new agency grant.

        Returns (grant, error). error is None on success.
        """
        # Validate sub-delegation
        if parent_grant_id:
            error = self._validate_sub_delegation(parent_grant_id, scope, duration_hours)
            if error:
                return AgencyGrant(  # dummy
                    grant_id="", client_lct=client_lct, agent_lct=agent_lct,
                    society_lct=self.society_lct, scope=scope,
                    not_before=0, expires_at=0
                ), error

        self._grant_counter += 1
        now = time.time()
        grant = AgencyGrant(
            grant_id=f"agy:grant:{self.society_lct.split(':')[-1]}:{self._grant_counter:04d}",
            client_lct=client_lct,
            agent_lct=agent_lct,
            society_lct=self.society_lct,
            scope=scope,
            not_before=now,
            expires_at=now + (duration_hours * 3600),
            law_hash=law_hash,
            parent_grant_id=parent_grant_id,
            witnesses=witnesses or [],
        )

        self.grants[grant.grant_id] = grant
        return grant, None

    def _validate_sub_delegation(self, parent_id: str, child_scope: GrantScope,
                                  child_duration_hours: float) -> Optional[str]:
        """Validate sub-delegation constraints."""
        parent = self.grants.get(parent_id)
        if not parent:
            return f"{AGYError.DELEGATION.value}: Parent grant {parent_id} not found"

        if not parent.is_active():
            return f"{AGYError.DELEGATION.value}: Parent grant {parent_id} is not active"

        if not parent.scope.delegatable:
            return f"{AGYError.DELEGATION.value}: Parent grant does not allow sub-delegation"

        # Scope must be subset
        if not child_scope.is_subset_of(parent.scope):
            return f"{AGYError.DELEGATION.value}: Child scope not subset of parent"

        # Duration must be within parent's remaining duration
        child_expires = time.time() + (child_duration_hours * 3600)
        if child_expires > parent.expires_at:
            return f"{AGYError.DELEGATION.value}: Child expires after parent"

        return None

    def validate_action(self, grant_id: str, action: str,
                         action_nonce: str = "") -> Tuple[bool, Optional[str], Optional[ProofOfAgency]]:
        """
        Validate that an action is authorized under a grant.

        Returns (valid, error, proof_of_agency).
        """
        grant = self.grants.get(grant_id)
        if not grant:
            return False, f"{AGYError.EXPIRED.value}: Grant {grant_id} not found", None

        # Check status
        if grant.status == GrantStatus.REVOKED:
            return False, f"{AGYError.REVOKED.value}: Grant {grant_id} revoked: {grant.revocation_reason}", None

        if grant.is_expired():
            grant.status = GrantStatus.EXPIRED
            return False, f"{AGYError.EXPIRED.value}: Grant {grant_id} expired", None

        if not grant.is_active():
            return False, f"{AGYError.EXPIRED.value}: Grant {grant_id} not yet active", None

        # Check scope — action must be in allowed methods
        if action not in grant.scope.methods:
            return False, f"{AGYError.SCOPE.value}: Action '{action}' not in scope {grant.scope.methods}", None

        # Check resource caps
        if grant.executions >= grant.scope.resource_caps.max_executions:
            return False, f"{AGYError.RESOURCE.value}: Execution limit reached ({grant.scope.resource_caps.max_executions})", None

        if grant.atp_spent >= grant.scope.resource_caps.max_atp:
            return False, f"{AGYError.RESOURCE.value}: ATP cap reached ({grant.scope.resource_caps.max_atp})", None

        # Check replay (action nonce)
        if action_nonce:
            nonce_key = f"{grant_id}:{action_nonce}"
            if nonce_key in self.used_nonces:
                return False, f"{AGYError.REPLAY.value}: Action nonce already used", None
            self.used_nonces.add(nonce_key)

        # Build proof of agency
        proof = ProofOfAgency(
            grant_id=grant_id,
            client_lct=grant.client_lct,
            agent_lct=grant.agent_lct,
            scope_methods=grant.scope.methods,
            grant_hash=grant.compute_hash(),
            nonce=grant.nonce,
            action=action,
            action_nonce=action_nonce,
        )

        return True, None, proof

    def execute_action(self, grant_id: str, action: str,
                        quality: float = 0.7) -> Tuple[bool, Optional[str], Optional[AttributionResult]]:
        """
        Execute a delegated action: validate, record, attribute.

        Returns (success, error, attribution).
        """
        valid, error, proof = self.validate_action(grant_id, action)
        if not valid:
            return False, error, None

        grant = self.grants[grant_id]

        # Compute dual attribution
        attribution = compute_dual_attribution(action, True, quality)
        attribution.grant_id = grant_id

        # Update grant usage
        grant.executions += 1
        grant.atp_spent += attribution.atp_cost
        grant.last_execution_at = time.time()

        self.attribution_log.append(attribution)

        return True, None, attribution

    def revoke_grant(self, grant_id: str, revoked_by: str,
                      reason: str) -> Tuple[bool, str]:
        """Revoke a grant. Must be called by client or authority."""
        grant = self.grants.get(grant_id)
        if not grant:
            return False, f"Grant {grant_id} not found"

        if grant.status == GrantStatus.REVOKED:
            return False, "Already revoked"

        # Only client can revoke
        if revoked_by != grant.client_lct:
            return False, f"Only client ({grant.client_lct}) can revoke"

        grant.status = GrantStatus.REVOKED
        grant.revocation_reason = reason

        revocation = AgencyRevocation(
            grant_id=grant_id,
            revoked_by=revoked_by,
            reason=reason,
        )
        self.revocations.append(revocation)

        # Cascade: recursively revoke all descendant grants
        self._cascade_revoke(grant_id, revoked_by, reason)

        return True, "Revoked"

    def _cascade_revoke(self, parent_id: str, revoked_by: str, reason: str):
        """Recursively revoke all descendant grants."""
        children = [g for g in self.grants.values()
                    if g.parent_grant_id == parent_id and g.status == GrantStatus.ACTIVE]
        for child in children:
            child.status = GrantStatus.REVOKED
            child.revocation_reason = f"Parent grant {parent_id} revoked"
            self.revocations.append(AgencyRevocation(
                grant_id=child.grant_id,
                revoked_by=revoked_by,
                reason=f"Cascaded from {parent_id}: {reason}",
            ))
            # Recurse into grandchildren
            self._cascade_revoke(child.grant_id, revoked_by, reason)

    def get_delegation_chain(self, grant_id: str) -> List[AgencyGrant]:
        """Walk the delegation chain from grant to root."""
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

    def verify_chain_integrity(self, grant_id: str) -> Tuple[bool, str]:
        """Verify entire delegation chain is valid."""
        chain = self.get_delegation_chain(grant_id)
        if not chain:
            return False, "Grant not found"

        for grant in chain:
            if not grant.is_active():
                return False, f"Grant {grant.grant_id} is not active (status={grant.status.value})"

        # Verify scope narrowing at each level
        for i in range(len(chain) - 1):
            child = chain[i]
            parent = chain[i + 1]
            if not child.scope.is_subset_of(parent.scope):
                return False, f"Scope violation: {child.grant_id} not subset of {parent.grant_id}"
            if child.expires_at > parent.expires_at:
                return False, f"Temporal violation: {child.grant_id} expires after {parent.grant_id}"

        return True, f"Chain valid: {len(chain)} grants"

    def stats(self) -> dict:
        """Registry statistics."""
        active = sum(1 for g in self.grants.values() if g.status == GrantStatus.ACTIVE)
        revoked = sum(1 for g in self.grants.values() if g.status == GrantStatus.REVOKED)
        expired = sum(1 for g in self.grants.values() if g.status == GrantStatus.EXPIRED)
        total_atp = sum(g.atp_spent for g in self.grants.values())
        total_exec = sum(g.executions for g in self.grants.values())

        return {
            "society": self.society_lct,
            "total_grants": len(self.grants),
            "active": active,
            "revoked": revoked,
            "expired": expired,
            "total_atp_spent": round(total_atp, 2),
            "total_executions": total_exec,
            "revocations": len(self.revocations),
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

    # ─── T1: Grant creation ───────────────────────────────
    print("\n═══ T1: Grant Creation ═══")
    registry = AgencyRegistry("lct:web4:test-society")

    scope = GrantScope(
        methods=["create", "update", "approve"],
        contexts=["finance:payments"],
        resource_caps=ResourceCaps(max_atp=50.0, max_executions=20),
        trust_caps=TrustCaps(min_talent=0.5, min_training=0.6),
        delegatable=True,
        witness_level=2,
    )

    grant, err = registry.create_grant(
        client_lct="lct:web4:alice",
        agent_lct="lct:web4:agent-001",
        scope=scope,
        duration_hours=24.0,
        law_hash="sha256-test-law",
        witnesses=["lct:web4:witness-a", "lct:web4:witness-b"],
    )

    check("T1: Grant created", err is None, f"err={err}")
    check("T1: Grant ID format", grant.grant_id.startswith("agy:grant:"))
    check("T1: Grant is active", grant.is_active())
    check("T1: Grant has hash", len(grant.compute_hash()) == 64)
    check("T1: Grant has nonce", len(grant.nonce) > 0)
    check("T1: Scope has 3 methods", len(grant.scope.methods) == 3)
    check("T1: Delegatable", grant.scope.delegatable)

    # ─── T2: Action validation ────────────────────────────
    print("\n═══ T2: Action Validation ═══")
    valid, err, proof = registry.validate_action(grant.grant_id, "create")
    check("T2: 'create' is valid", valid, f"err={err}")
    check("T2: Proof generated", proof is not None)
    check("T2: Proof has grant_id", proof.grant_id == grant.grant_id)
    check("T2: Proof has client", proof.client_lct == "lct:web4:alice")
    check("T2: Proof has agent", proof.agent_lct == "lct:web4:agent-001")

    # Invalid action
    valid, err, proof = registry.validate_action(grant.grant_id, "delete")
    check("T2: 'delete' rejected (not in scope)", not valid)
    check("T2: Scope error code", AGYError.SCOPE.value in err)

    # ─── T3: Action execution with dual attribution ──────
    print("\n═══ T3: Dual Attribution ═══")
    ok, err, attr = registry.execute_action(grant.grant_id, "update", quality=0.8)
    check("T3: Action executed", ok, f"err={err}")
    check("T3: Attribution returned", attr is not None)
    check("T3: Agent T3 positive (talent)", attr.agent_t3_deltas["talent"] > 0,
          f"talent_delta={attr.agent_t3_deltas['talent']}")
    check("T3: Agent T3 positive (training)", attr.agent_t3_deltas["training"] > 0)
    check("T3: Client V3 positive (veracity)", attr.client_v3_deltas["veracity"] > 0,
          f"veracity_delta={attr.client_v3_deltas['veracity']}")
    check("T3: Client V3 positive (validity)", attr.client_v3_deltas["validity"] > 0)
    check("T3: ATP cost recorded", attr.atp_cost > 0)
    check("T3: Grant execution count updated", grant.executions == 1)
    check("T3: Grant ATP spent updated", grant.atp_spent == attr.atp_cost)

    # Failed action attribution
    fail_attr = compute_dual_attribution("bad_action", False, quality=0.5)
    check("T3: Failed action: agent talent negative", fail_attr.agent_t3_deltas["talent"] < 0)
    check("T3: Failed action: agent training positive (still learned)",
          fail_attr.agent_t3_deltas["training"] > 0)
    check("T3: Failed action: client veracity negative", fail_attr.client_v3_deltas["veracity"] < 0)

    # ─── T4: Resource cap enforcement ─────────────────────
    print("\n═══ T4: Resource Cap Enforcement ═══")
    cap_scope = GrantScope(
        methods=["read"],
        resource_caps=ResourceCaps(max_atp=15.0, max_executions=3),
    )
    cap_grant, _ = registry.create_grant(
        client_lct="lct:web4:bob",
        agent_lct="lct:web4:agent-002",
        scope=cap_scope,
    )

    # Execute until cap
    for i in range(3):
        ok, err, _ = registry.execute_action(cap_grant.grant_id, "read")
        check(f"T4: Execution {i+1}/3", ok)

    # 4th execution should fail
    ok, err, _ = registry.execute_action(cap_grant.grant_id, "read")
    check("T4: Execution limit enforced", not ok)
    check("T4: Resource error code", AGYError.RESOURCE.value in err)

    # ─── T5: Sub-delegation with scope narrowing ─────────
    print("\n═══ T5: Sub-Delegation ═══")
    parent_scope = GrantScope(
        methods=["create", "update", "approve", "delegate"],
        contexts=["finance:payments", "finance:invoices"],
        resource_caps=ResourceCaps(max_atp=100.0, max_executions=50),
        delegatable=True,
        witness_level=1,
    )
    parent_grant, _ = registry.create_grant(
        client_lct="lct:web4:ceo",
        agent_lct="lct:web4:manager",
        scope=parent_scope,
        duration_hours=48.0,
    )

    # Valid sub-delegation (narrower scope)
    child_scope = GrantScope(
        methods=["update", "approve"],  # Subset
        contexts=["finance:payments"],  # Subset
        resource_caps=ResourceCaps(max_atp=25.0, max_executions=10),  # Less
        delegatable=True,
        witness_level=1,
    )
    child_grant, err = registry.create_grant(
        client_lct="lct:web4:manager",
        agent_lct="lct:web4:analyst",
        scope=child_scope,
        duration_hours=24.0,
        parent_grant_id=parent_grant.grant_id,
    )
    check("T5: Sub-delegation created", err is None, f"err={err}")
    check("T5: Parent reference set", child_grant.parent_grant_id == parent_grant.grant_id)

    # Valid grandchild (even narrower)
    grandchild_scope = GrantScope(
        methods=["approve"],  # Even narrower
        resource_caps=ResourceCaps(max_atp=10.0, max_executions=5),
        delegatable=False,
        witness_level=1,
    )
    grandchild_grant, err = registry.create_grant(
        client_lct="lct:web4:analyst",
        agent_lct="lct:web4:intern",
        scope=grandchild_scope,
        duration_hours=8.0,
        parent_grant_id=child_grant.grant_id,
    )
    check("T5: Grandchild delegation created", err is None)

    # Invalid: scope expansion
    bad_scope = GrantScope(
        methods=["create", "update", "approve", "delete"],  # 'delete' not in parent
        resource_caps=ResourceCaps(max_atp=200.0),  # Exceeds parent
    )
    _, err = registry.create_grant(
        client_lct="lct:web4:manager",
        agent_lct="lct:web4:hacker",
        scope=bad_scope,
        parent_grant_id=parent_grant.grant_id,
    )
    check("T5: Scope expansion blocked", err is not None)
    check("T5: Delegation error code", AGYError.DELEGATION.value in err)

    # Invalid: non-delegatable parent
    _, err = registry.create_grant(
        client_lct="lct:web4:intern",
        agent_lct="lct:web4:sub-intern",
        scope=GrantScope(methods=["approve"]),
        parent_grant_id=grandchild_grant.grant_id,
    )
    check("T5: Non-delegatable parent blocked", err is not None,
          f"err={err}")

    # ─── T6: Delegation chain verification ────────────────
    print("\n═══ T6: Delegation Chain Verification ═══")
    chain = registry.get_delegation_chain(grandchild_grant.grant_id)
    check("T6: Chain has 3 levels", len(chain) == 3,
          f"chain={[g.grant_id for g in chain]}")
    check("T6: Chain order: grandchild → child → parent",
          chain[0].grant_id == grandchild_grant.grant_id and
          chain[2].grant_id == parent_grant.grant_id)

    valid, msg = registry.verify_chain_integrity(grandchild_grant.grant_id)
    check("T6: Chain integrity verified", valid, msg)

    # ─── T7: Revocation with cascade ─────────────────────
    print("\n═══ T7: Revocation with Cascade ═══")
    ok, msg = registry.revoke_grant(parent_grant.grant_id,
                                     "lct:web4:ceo", "key compromise")
    check("T7: Parent revoked", ok)
    check("T7: Parent status = revoked", parent_grant.status == GrantStatus.REVOKED)
    check("T7: Child cascaded", child_grant.status == GrantStatus.REVOKED)
    check("T7: Grandchild cascaded", grandchild_grant.status == GrantStatus.REVOKED)

    # Revoked grant can't execute
    ok, err, _ = registry.execute_action(child_grant.grant_id, "update")
    check("T7: Revoked grant can't execute", not ok)
    check("T7: Revoked error code", AGYError.REVOKED.value in err)

    # Non-client can't revoke
    simple_grant, _ = registry.create_grant(
        client_lct="lct:web4:dave",
        agent_lct="lct:web4:agent-x",
        scope=GrantScope(methods=["read"]),
    )
    ok, msg = registry.revoke_grant(simple_grant.grant_id,
                                     "lct:web4:eve", "unauthorized")
    check("T7: Non-client revocation blocked", not ok)

    # ─── T8: Replay protection ────────────────────────────
    print("\n═══ T8: Replay Protection ═══")
    replay_grant, _ = registry.create_grant(
        client_lct="lct:web4:frank",
        agent_lct="lct:web4:agent-r",
        scope=GrantScope(methods=["read", "write"]),
    )

    # First use of nonce
    valid, err, _ = registry.validate_action(
        replay_grant.grant_id, "read", action_nonce="nonce-001")
    check("T8: First nonce accepted", valid)

    # Replay same nonce
    valid, err, _ = registry.validate_action(
        replay_grant.grant_id, "read", action_nonce="nonce-001")
    check("T8: Replay blocked", not valid)
    check("T8: Replay error code", AGYError.REPLAY.value in err)

    # Different nonce works
    valid, err, _ = registry.validate_action(
        replay_grant.grant_id, "read", action_nonce="nonce-002")
    check("T8: Different nonce accepted", valid)

    # ─── T9: Scope subset validation ─────────────────────
    print("\n═══ T9: Scope Subset Validation ═══")
    parent_s = GrantScope(
        methods=["a", "b", "c", "d"],
        contexts=["x", "y", "z"],
        resource_caps=ResourceCaps(max_atp=100, max_executions=50),
        trust_caps=TrustCaps(min_talent=0.5),
        delegatable=True,
        witness_level=2,
    )

    # Valid subset
    child_s = GrantScope(
        methods=["a", "b"],
        contexts=["x"],
        resource_caps=ResourceCaps(max_atp=50, max_executions=20),
        trust_caps=TrustCaps(min_talent=0.7),  # Stricter = OK
        delegatable=False,
        witness_level=2,
    )
    check("T9: Valid scope subset", child_s.is_subset_of(parent_s))

    # Method expansion
    bad_s1 = GrantScope(methods=["a", "b", "EXTRA"])
    check("T9: Method expansion detected", not bad_s1.is_subset_of(parent_s))

    # ATP expansion
    bad_s2 = GrantScope(
        methods=["a"],
        resource_caps=ResourceCaps(max_atp=200),
    )
    check("T9: ATP expansion detected", not bad_s2.is_subset_of(parent_s))

    # Trust relaxation
    bad_s3 = GrantScope(
        methods=["a"],
        trust_caps=TrustCaps(min_talent=0.3),  # Looser than parent's 0.5
    )
    check("T9: Trust relaxation detected", not bad_s3.is_subset_of(parent_s))

    # Witness reduction
    bad_s4 = GrantScope(methods=["a"], witness_level=1)
    check("T9: Witness reduction detected", not bad_s4.is_subset_of(parent_s))

    # Delegation escalation
    bad_s5 = GrantScope(methods=["a"])
    bad_s5.delegatable = True
    parent_no_del = GrantScope(methods=["a"], delegatable=False)
    check("T9: Delegation escalation detected", not bad_s5.is_subset_of(parent_no_del))

    # ─── T10: Proof of Agency serialization ───────────────
    print("\n═══ T10: Proof of Agency ═══")
    poa = ProofOfAgency(
        grant_id="agy:grant:test:0001",
        client_lct="lct:web4:alice",
        agent_lct="lct:web4:agent-001",
        scope_methods=["create", "update"],
        grant_hash="a" * 64,
        nonce="test-nonce-123",
        action="create",
    )

    d = poa.to_dict()
    check("T10: Proof serializes", isinstance(d, dict))
    check("T10: Has grantId", d["grantId"] == "agy:grant:test:0001")
    check("T10: Has principal", d["principal"] == "lct:web4:alice")
    check("T10: Has action", d["action"] == "create")
    check("T10: Has actionNonce", len(d["actionNonce"]) > 0)
    check("T10: JSON-serializable", len(json.dumps(d)) > 0)

    # ─── T11: Grant serialization (JSON-LD) ───────────────
    print("\n═══ T11: Grant Serialization ═══")
    g = list(registry.grants.values())[0]
    d = g.to_dict()
    check("T11: Has @context", "@context" in d)
    check("T11: Has type", d["type"] == "Web4AgencyGrant")
    check("T11: Has grantId", d["grantId"].startswith("agy:grant:"))
    check("T11: Has scope", "scope" in d)
    check("T11: Has duration", "duration" in d)
    check("T11: Has grantHash", len(d["grantHash"]) == 64)
    check("T11: JSON-LD roundtrip", len(json.dumps(d, default=str)) > 0)

    # Revocation serialization
    rev = registry.revocations[0]
    rd = rev.to_dict()
    check("T11: Revocation has type", rd["type"] == "Web4AgencyRevocation")
    check("T11: Revocation has reason", len(rd["reason"]) > 0)

    # ─── T12: Registry statistics ─────────────────────────
    print("\n═══ T12: Registry Statistics ═══")
    stats = registry.stats()
    check("T12: Total grants tracked", stats["total_grants"] > 0,
          f"total={stats['total_grants']}")
    check("T12: Active grants", stats["active"] > 0)
    check("T12: Revoked grants tracked", stats["revoked"] > 0)
    check("T12: Revocations logged", stats["revocations"] > 0)
    check("T12: Attributions logged", stats["attributions"] > 0)
    check("T12: ATP spend tracked", stats["total_atp_spent"] > 0)

    # ─── T13: ACP integration (grantId placeholder) ──────
    print("\n═══ T13: ACP Integration ═══")
    # Simulate ACP plan referencing a grant
    acp_grant, _ = registry.create_grant(
        client_lct="lct:web4:principal",
        agent_lct="lct:web4:acp-agent",
        scope=GrantScope(
            methods=["scan_repository", "generate_report", "submit_review"],
            resource_caps=ResourceCaps(max_atp=30.0, max_executions=10),
        ),
        duration_hours=2.0,
    )

    # Simulate ACP plan registration: verify grant exists
    check("T13: ACP can look up grant by ID",
          acp_grant.grant_id in registry.grants)

    # Simulate intent creation: build proof of agency
    valid, err, proof = registry.validate_action(
        acp_grant.grant_id, "scan_repository")
    check("T13: ACP intent validated", valid)
    check("T13: Proof of agency for MCP call", proof is not None)

    # Simulate MCP tool call with proof
    mcp_context = {
        "web4_context": {
            "proofOfAgency": proof.to_dict()
        }
    }
    check("T13: MCP context includes proof", "proofOfAgency" in mcp_context["web4_context"])

    # Simulate execution and recording
    ok, _, attr = registry.execute_action(
        acp_grant.grant_id, "generate_report", quality=0.9)
    check("T13: ACP execution recorded", ok)
    check("T13: Attribution for ACP action", attr.grant_id == acp_grant.grant_id)

    # ─── T14: Multi-level delegation simulation ──────────
    print("\n═══ T14: Multi-Level Delegation Simulation ═══")
    reg = AgencyRegistry("lct:web4:enterprise")

    # CEO → VP (full authority)
    vp_scope = GrantScope(
        methods=["hire", "fire", "budget", "review", "delegate"],
        contexts=["engineering", "product"],
        resource_caps=ResourceCaps(max_atp=1000, max_executions=500),
        delegatable=True,
        witness_level=1,
    )
    ceo_to_vp, _ = reg.create_grant(
        client_lct="lct:web4:ceo",
        agent_lct="lct:web4:vp-eng",
        scope=vp_scope,
        duration_hours=720,  # 30 days
    )

    # VP → Team Lead (narrower)
    tl_scope = GrantScope(
        methods=["review", "budget", "delegate"],
        contexts=["engineering"],
        resource_caps=ResourceCaps(max_atp=200, max_executions=100),
        delegatable=True,
        witness_level=1,
    )
    vp_to_tl, _ = reg.create_grant(
        client_lct="lct:web4:vp-eng",
        agent_lct="lct:web4:team-lead",
        scope=tl_scope,
        duration_hours=168,  # 7 days
        parent_grant_id=ceo_to_vp.grant_id,
    )

    # Team Lead → Dev (very narrow)
    dev_scope = GrantScope(
        methods=["review"],
        contexts=["engineering"],
        resource_caps=ResourceCaps(max_atp=20, max_executions=10),
        delegatable=False,
        witness_level=1,
    )
    tl_to_dev, _ = reg.create_grant(
        client_lct="lct:web4:team-lead",
        agent_lct="lct:web4:dev-alice",
        scope=dev_scope,
        duration_hours=24,
        parent_grant_id=vp_to_tl.grant_id,
    )

    # Verify chain
    chain = reg.get_delegation_chain(tl_to_dev.grant_id)
    check("T14: 3-level chain", len(chain) == 3)
    valid, msg = reg.verify_chain_integrity(tl_to_dev.grant_id)
    check("T14: Chain integrity verified", valid, msg)

    # Dev can review
    ok, _, attr = reg.execute_action(tl_to_dev.grant_id, "review", quality=0.85)
    check("T14: Dev can review", ok)

    # Dev cannot hire (not in scope)
    ok, err, _ = reg.execute_action(tl_to_dev.grant_id, "hire")
    check("T14: Dev cannot hire", not ok)

    # CEO revokes VP → cascade to all
    reg.revoke_grant(ceo_to_vp.grant_id, "lct:web4:ceo", "restructuring")
    check("T14: VP revoked", ceo_to_vp.status == GrantStatus.REVOKED)
    check("T14: TL cascaded", vp_to_tl.status == GrantStatus.REVOKED)
    check("T14: Dev cascaded", tl_to_dev.status == GrantStatus.REVOKED)

    # Dev can no longer act
    ok, err, _ = reg.execute_action(tl_to_dev.grant_id, "review")
    check("T14: Dev blocked after cascade", not ok)

    # ─── Summary ──────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  AGY Agency Delegation — Track J Results")
    print(f"  {passed} passed, {failed} failed out of {passed+failed} checks")
    print(f"{'='*60}")

    return passed, failed


if __name__ == "__main__":
    passed, failed = main()
    sys.exit(0 if failed == 0 else 1)
