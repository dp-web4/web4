"""
Trust Capability Security for Web4
Session 34, Track 7

Object-capability model for Web4 authorization:
- Capabilities as unforgeable references
- Capability attenuation (narrowing permissions)
- Capability revocation via caretakers
- Confinement (preventing capability leaks)
- Powerbox pattern for safe capability introduction
- Membrane pattern for boundary enforcement
- Trust-gated capability granting
- Capability audit trail
- POLA (Principle of Least Authority) verification
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Set, Dict, List, Tuple, Optional, FrozenSet
from collections import defaultdict
from enum import Enum, auto


# ─── Permission Types ────────────────────────────────────────────

class Permission(Enum):
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    DELEGATE = auto()
    ADMIN = auto()
    ATTEST = auto()
    REVOKE = auto()


# ─── Capability ──────────────────────────────────────────────────

@dataclass
class Capability:
    """An unforgeable reference granting specific permissions on a resource."""
    cap_id: str
    resource: str
    permissions: FrozenSet[Permission]
    holder: str
    granter: str
    valid: bool = True
    parent_cap: Optional[str] = None   # capability this was derived from
    trust_threshold: float = 0.0        # minimum trust to use
    created_at: float = 0.0

    @property
    def is_attenuated(self) -> bool:
        return self.parent_cap is not None

    def attenuate(self, new_permissions: FrozenSet[Permission],
                   new_holder: str, cap_id: str = None) -> Optional['Capability']:
        """
        Create an attenuated (narrower) capability.
        New permissions MUST be a subset of current permissions.
        """
        if not new_permissions.issubset(self.permissions):
            return None  # Cannot amplify
        if not self.valid:
            return None

        return Capability(
            cap_id=cap_id or f"{self.cap_id}:{new_holder}",
            resource=self.resource,
            permissions=new_permissions,
            holder=new_holder,
            granter=self.holder,
            parent_cap=self.cap_id,
            trust_threshold=max(self.trust_threshold, 0.0),
            created_at=time.time(),
        )

    def can(self, perm: Permission) -> bool:
        """Check if this capability grants a permission."""
        return self.valid and perm in self.permissions


# ─── Caretaker (Revocation Proxy) ────────────────────────────────

@dataclass
class Caretaker:
    """
    Revocation proxy: wraps a capability and can revoke it.
    Pattern from E language / Mark Miller's capability security.
    """
    capability: Capability
    revoked: bool = False
    revocation_reason: str = ""

    def use(self, perm: Permission) -> bool:
        """Check permission through caretaker."""
        if self.revoked:
            return False
        return self.capability.can(perm)

    def revoke(self, reason: str = ""):
        """Revoke the capability."""
        self.revoked = True
        self.revocation_reason = reason
        self.capability.valid = False


# ─── Capability Store ────────────────────────────────────────────

class CapabilityStore:
    """
    Central capability registry for tracking and auditing.
    """

    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self.caretakers: Dict[str, Caretaker] = {}
        self.audit_log: List[Dict] = []

    def register(self, cap: Capability) -> str:
        """Register a capability."""
        self.capabilities[cap.cap_id] = cap
        self._audit("register", cap.cap_id, cap.holder, cap.resource)
        return cap.cap_id

    def create_caretaker(self, cap_id: str) -> Optional[Caretaker]:
        """Create a caretaker for revocable access."""
        cap = self.capabilities.get(cap_id)
        if cap is None:
            return None
        ct = Caretaker(cap)
        self.caretakers[cap_id] = ct
        self._audit("caretaker_created", cap_id, cap.holder, cap.resource)
        return ct

    def attenuate(self, cap_id: str, new_perms: FrozenSet[Permission],
                   new_holder: str) -> Optional[Capability]:
        """Attenuate a capability and register the result."""
        cap = self.capabilities.get(cap_id)
        if cap is None:
            return None
        new_cap = cap.attenuate(new_perms, new_holder)
        if new_cap is None:
            return None
        self.register(new_cap)
        self._audit("attenuate", cap_id, new_holder, cap.resource,
                     detail=f"perms={set(new_perms)}")
        return new_cap

    def revoke(self, cap_id: str, reason: str = "") -> bool:
        """Revoke a capability (and all derived capabilities)."""
        cap = self.capabilities.get(cap_id)
        if cap is None:
            return False

        cap.valid = False
        if cap_id in self.caretakers:
            self.caretakers[cap_id].revoke(reason)

        # Cascade: revoke all derived capabilities
        self._cascade_revoke(cap_id, reason)
        self._audit("revoke", cap_id, cap.holder, cap.resource, detail=reason)
        return True

    def _cascade_revoke(self, parent_id: str, reason: str):
        """Revoke all capabilities derived from parent."""
        for cap in self.capabilities.values():
            if cap.parent_cap == parent_id and cap.valid:
                cap.valid = False
                if cap.cap_id in self.caretakers:
                    self.caretakers[cap.cap_id].revoke(reason)
                self._cascade_revoke(cap.cap_id, reason)

    def check_access(self, holder: str, resource: str,
                      perm: Permission, trust: float = 1.0) -> bool:
        """Check if holder has permission on resource."""
        for cap in self.capabilities.values():
            if (cap.holder == holder and cap.resource == resource and
                cap.valid and perm in cap.permissions and
                trust >= cap.trust_threshold):
                return True
        return False

    def holder_capabilities(self, holder: str) -> List[Capability]:
        """Get all valid capabilities for a holder."""
        return [c for c in self.capabilities.values()
                if c.holder == holder and c.valid]

    def _audit(self, action: str, cap_id: str, holder: str,
               resource: str, detail: str = ""):
        self.audit_log.append({
            "action": action, "cap_id": cap_id,
            "holder": holder, "resource": resource,
            "detail": detail, "timestamp": time.time(),
        })


# ─── Powerbox Pattern ────────────────────────────────────────────

class Powerbox:
    """
    Safe capability introduction via user consent.
    Pattern: entity requests capability → powerbox mediates → approval → grant.
    """

    def __init__(self, store: CapabilityStore):
        self.store = store
        self.pending: List[Dict] = []
        self.granted: List[str] = []

    def request(self, requester: str, resource: str,
                permissions: FrozenSet[Permission]) -> str:
        """Submit a capability request."""
        req_id = f"req:{requester}:{resource}:{len(self.pending)}"
        self.pending.append({
            "id": req_id, "requester": requester,
            "resource": resource, "permissions": permissions,
        })
        return req_id

    def approve(self, req_id: str, granter: str,
                trust_threshold: float = 0.0) -> Optional[Capability]:
        """Approve a pending request."""
        req = next((r for r in self.pending if r["id"] == req_id), None)
        if req is None:
            return None

        cap = Capability(
            cap_id=f"cap:{req['requester']}:{req['resource']}",
            resource=req["resource"],
            permissions=req["permissions"],
            holder=req["requester"],
            granter=granter,
            trust_threshold=trust_threshold,
        )
        self.store.register(cap)
        self.pending = [r for r in self.pending if r["id"] != req_id]
        self.granted.append(cap.cap_id)
        return cap

    def deny(self, req_id: str):
        """Deny a request."""
        self.pending = [r for r in self.pending if r["id"] != req_id]


# ─── Membrane Pattern ────────────────────────────────────────────

class Membrane:
    """
    Boundary enforcer: wraps a set of capabilities with additional constraints.
    Crossing the membrane attenuates capabilities automatically.
    """

    def __init__(self, name: str, allowed_perms: FrozenSet[Permission],
                 min_trust: float = 0.0):
        self.name = name
        self.allowed_perms = allowed_perms
        self.min_trust = min_trust
        self.crossings: List[Dict] = []

    def cross(self, cap: Capability, entity_trust: float) -> Optional[Capability]:
        """
        Cross the membrane: attenuate capability to allowed permissions.
        Returns None if trust is insufficient.
        """
        if entity_trust < self.min_trust:
            self.crossings.append({"cap": cap.cap_id, "allowed": False, "reason": "trust"})
            return None

        allowed = cap.permissions & self.allowed_perms
        if not allowed:
            self.crossings.append({"cap": cap.cap_id, "allowed": False, "reason": "no_perms"})
            return None

        crossed_cap = Capability(
            cap_id=f"membrane:{self.name}:{cap.cap_id}",
            resource=cap.resource,
            permissions=frozenset(allowed),
            holder=cap.holder,
            granter=f"membrane:{self.name}",
            parent_cap=cap.cap_id,
            trust_threshold=self.min_trust,
        )
        self.crossings.append({"cap": cap.cap_id, "allowed": True})
        return crossed_cap


# ─── POLA Verification ───────────────────────────────────────────

def verify_pola(capabilities: List[Capability],
                 required: Dict[str, Set[Permission]]) -> Dict[str, object]:
    """
    Verify Principle of Least Authority:
    Each entity should have only the permissions it needs.

    Args:
        capabilities: all capabilities held
        required: {holder: set of actually needed permissions}

    Returns analysis per holder.
    """
    analysis = {}
    holder_perms: Dict[str, Set[Permission]] = defaultdict(set)

    for cap in capabilities:
        if cap.valid:
            holder_perms[cap.holder] |= set(cap.permissions)

    for holder, held in holder_perms.items():
        needed = required.get(holder, set())
        excess = held - needed
        missing = needed - held

        analysis[holder] = {
            "held": held,
            "needed": needed,
            "excess": excess,
            "missing": missing,
            "pola_compliant": len(excess) == 0 and len(missing) == 0,
            "over_privileged": len(excess) > 0,
            "under_privileged": len(missing) > 0,
        }

    return analysis


# ══════════════════════════════════════════════════════════════════
#  TESTS
# ══════════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(name, condition, detail=""):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {name} — {detail}")

    print("=" * 70)
    print("Trust Capability Security for Web4")
    print("Session 34, Track 7")
    print("=" * 70)

    # ── §1 Capability Basics ────────────────────────────────────
    print("\n§1 Capability Basics\n")

    cap = Capability(
        cap_id="cap:1", resource="ledger:main",
        permissions=frozenset({Permission.READ, Permission.WRITE, Permission.DELEGATE}),
        holder="alice", granter="admin",
    )
    check("can_read", cap.can(Permission.READ))
    check("can_write", cap.can(Permission.WRITE))
    check("cannot_admin", not cap.can(Permission.ADMIN))
    check("is_valid", cap.valid)

    # Invalidate
    cap2 = Capability("c2", "r", frozenset({Permission.READ}), "x", "y", valid=False)
    check("invalid_cant_read", not cap2.can(Permission.READ))

    # ── §2 Attenuation ──────────────────────────────────────────
    print("\n§2 Capability Attenuation\n")

    # Narrow permissions
    narrow = cap.attenuate(frozenset({Permission.READ}), "bob")
    check("attenuation_succeeds", narrow is not None)
    check("narrow_can_read", narrow.can(Permission.READ))
    check("narrow_cannot_write", not narrow.can(Permission.WRITE))
    check("narrow_is_attenuated", narrow.is_attenuated)
    check("narrow_parent", narrow.parent_cap == cap.cap_id)

    # Cannot amplify
    amplified = cap.attenuate(
        frozenset({Permission.READ, Permission.ADMIN}), "bob")
    check("amplification_blocked", amplified is None)

    # Attenuating attenuated
    narrower = narrow.attenuate(frozenset({Permission.READ}), "carol")
    check("double_attenuation", narrower is not None)
    check("chain_parent", narrower.parent_cap == narrow.cap_id)

    # Empty permissions
    empty = cap.attenuate(frozenset(), "nobody")
    check("empty_perms_ok", empty is not None)
    check("empty_cant_do_anything", not empty.can(Permission.READ))

    # ── §3 Caretaker (Revocation) ────────────────────────────────
    print("\n§3 Caretaker Revocation\n")

    cap3 = Capability("c3", "res", frozenset({Permission.READ, Permission.WRITE}),
                       "dave", "admin")
    ct = Caretaker(cap3)
    check("caretaker_allows_read", ct.use(Permission.READ))
    check("caretaker_allows_write", ct.use(Permission.WRITE))

    ct.revoke("suspicious behavior")
    check("revoked_blocks_read", not ct.use(Permission.READ))
    check("revoked_blocks_write", not ct.use(Permission.WRITE))
    check("revocation_reason", ct.revocation_reason == "suspicious behavior")
    check("underlying_cap_invalid", not cap3.valid)

    # ── §4 Capability Store ──────────────────────────────────────
    print("\n§4 Capability Store\n")

    store = CapabilityStore()
    root_cap = Capability(
        "root", "ledger:main",
        frozenset({Permission.READ, Permission.WRITE, Permission.DELEGATE, Permission.ADMIN}),
        "admin", "system",
    )
    store.register(root_cap)

    check("access_admin", store.check_access("admin", "ledger:main", Permission.READ))
    check("no_access_bob", not store.check_access("bob", "ledger:main", Permission.READ))

    # Attenuate through store
    bob_cap = store.attenuate("root", frozenset({Permission.READ}), "bob")
    check("bob_cap_created", bob_cap is not None)
    check("bob_can_read", store.check_access("bob", "ledger:main", Permission.READ))
    check("bob_cant_write", not store.check_access("bob", "ledger:main", Permission.WRITE))

    # Revoke root → cascade to bob
    store.revoke("root", "system shutdown")
    check("root_revoked", not store.check_access("admin", "ledger:main", Permission.READ))
    check("bob_cascade_revoked", not store.check_access("bob", "ledger:main", Permission.READ))

    # Audit trail
    check("audit_log_populated", len(store.audit_log) >= 3)

    # ── §5 Powerbox ──────────────────────────────────────────────
    print("\n§5 Powerbox Pattern\n")

    store2 = CapabilityStore()
    pb = Powerbox(store2)

    req = pb.request("alice", "data:sensitive", frozenset({Permission.READ}))
    check("request_pending", len(pb.pending) == 1)

    cap_granted = pb.approve(req, "admin", trust_threshold=0.7)
    check("powerbox_approved", cap_granted is not None)
    check("pending_cleared", len(pb.pending) == 0)
    check("access_granted", store2.check_access("alice", "data:sensitive", Permission.READ, trust=0.8))
    check("low_trust_blocked", not store2.check_access("alice", "data:sensitive", Permission.READ, trust=0.5))

    # Deny
    req2 = pb.request("mallory", "data:secret", frozenset({Permission.ADMIN}))
    pb.deny(req2)
    check("denied_cleared", len(pb.pending) == 0)

    # ── §6 Membrane ──────────────────────────────────────────────
    print("\n§6 Membrane Pattern\n")

    membrane = Membrane("trust_boundary",
                         allowed_perms=frozenset({Permission.READ, Permission.ATTEST}),
                         min_trust=0.6)

    full_cap = Capability("full", "resource",
                           frozenset({Permission.READ, Permission.WRITE, Permission.ATTEST}),
                           "agent", "system")

    # High trust: crosses successfully, but WRITE is stripped
    crossed = membrane.cross(full_cap, entity_trust=0.8)
    check("membrane_crosses", crossed is not None)
    check("membrane_strips_write", not crossed.can(Permission.WRITE))
    check("membrane_keeps_read", crossed.can(Permission.READ))
    check("membrane_keeps_attest", crossed.can(Permission.ATTEST))

    # Low trust: blocked
    blocked = membrane.cross(full_cap, entity_trust=0.3)
    check("membrane_blocks_low_trust", blocked is None)

    # No matching permissions: blocked
    write_only = Capability("wo", "r", frozenset({Permission.WRITE}), "x", "y")
    no_match = membrane.cross(write_only, entity_trust=0.9)
    check("membrane_blocks_no_perms", no_match is None)

    # ── §7 POLA Verification ────────────────────────────────────
    print("\n§7 POLA Verification\n")

    caps_pola = [
        Capability("c1", "r1", frozenset({Permission.READ, Permission.WRITE}), "alice", "sys"),
        Capability("c2", "r2", frozenset({Permission.READ}), "bob", "sys"),
    ]
    required = {
        "alice": {Permission.READ},        # alice has WRITE excess
        "bob": {Permission.READ, Permission.WRITE},  # bob is missing WRITE
    }

    analysis = verify_pola(caps_pola, required)
    check("alice_over_privileged", analysis["alice"]["over_privileged"])
    check("alice_excess_write", Permission.WRITE in analysis["alice"]["excess"])
    check("bob_under_privileged", analysis["bob"]["under_privileged"])
    check("bob_missing_write", Permission.WRITE in analysis["bob"]["missing"])

    # Perfect POLA
    caps_perfect = [
        Capability("c3", "r3", frozenset({Permission.READ}), "carol", "sys"),
    ]
    analysis_p = verify_pola(caps_perfect, {"carol": {Permission.READ}})
    check("carol_pola_compliant", analysis_p["carol"]["pola_compliant"])

    # ── §8 Trust-Gated Capabilities ──────────────────────────────
    print("\n§8 Trust-Gated Capabilities\n")

    store3 = CapabilityStore()
    gated = Capability("gated", "high_value_resource",
                        frozenset({Permission.READ, Permission.WRITE}),
                        "agent", "admin", trust_threshold=0.8)
    store3.register(gated)

    check("high_trust_ok", store3.check_access("agent", "high_value_resource",
                                                 Permission.READ, trust=0.9))
    check("low_trust_blocked", not store3.check_access("agent", "high_value_resource",
                                                        Permission.READ, trust=0.5))
    check("exact_threshold_ok", store3.check_access("agent", "high_value_resource",
                                                      Permission.READ, trust=0.8))
    check("below_threshold", not store3.check_access("agent", "high_value_resource",
                                                       Permission.READ, trust=0.79))

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    print(f"{'='*70}")
    return passed, failed


if __name__ == "__main__":
    run_checks()
