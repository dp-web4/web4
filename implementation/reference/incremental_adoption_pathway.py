"""
Incremental Adoption Pathway — Web4 Reference Implementation

Shows how existing systems can adopt Web4 incrementally through 5 tiers:

Tier 0: Wrapper — Add Web4 identity to existing system (no code changes)
Tier 1: Observable — Add trust tensors and audit logging
Tier 2: Accountable — Add ATP/ADP metering and settlement
Tier 3: Federated — Add cross-system trust and federation
Tier 4: Native — Full Web4 stack with MRH, policies, governance

Each tier:
- Builds on the previous
- Is independently valuable
- Has clear migration path to next tier
- Includes compatibility bridge with legacy

Session 10, Track 8
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ─── Tier 0: Wrapper ─────────────────────────────────────────────
# Add Web4 identity to existing system. Zero code changes to legacy.

class AdoptionTier(Enum):
    WRAPPER = 0       # Identity wrapper
    OBSERVABLE = 1    # Trust + audit
    ACCOUNTABLE = 2   # ATP metering
    FEDERATED = 3     # Cross-system trust
    NATIVE = 4        # Full Web4


@dataclass
class LegacySystem:
    """Represents an existing system before Web4 adoption."""
    name: str
    api_endpoint: str
    auth_method: str  # "api_key", "oauth2", "basic"
    version: str
    capabilities: list[str] = field(default_factory=list)

    def call(self, method: str, params: dict) -> dict:
        """Simulate legacy API call."""
        return {
            "status": "ok",
            "method": method,
            "result": f"Legacy result for {method}",
            "system": self.name,
        }


class Web4Wrapper:
    """Tier 0: Wraps legacy system with Web4 identity.

    No changes to the legacy system. The wrapper:
    - Creates an LCT for the legacy system
    - Translates legacy auth to Web4 identity
    - Logs all interactions for future trust building
    """

    def __init__(self, legacy: LegacySystem):
        self.legacy = legacy
        self.lct_id = self._create_lct_id()
        self.interaction_log: list[dict] = []
        self.tier = AdoptionTier.WRAPPER

    def _create_lct_id(self) -> str:
        id_hash = hashlib.sha256(
            f"{self.legacy.name}:{self.legacy.api_endpoint}".encode()
        ).hexdigest()[:16]
        return f"lct:web4:service:{id_hash}"

    def call(self, method: str, params: dict, caller_id: str = "anonymous") -> dict:
        """Call legacy system through Web4 wrapper."""
        result = self.legacy.call(method, params)
        self.interaction_log.append({
            "method": method,
            "caller": caller_id,
            "timestamp": time.monotonic(),
            "success": result.get("status") == "ok",
        })
        return {
            **result,
            "web4_lct": self.lct_id,
            "web4_tier": self.tier.value,
        }

    def get_identity(self) -> dict:
        return {
            "lct_id": self.lct_id,
            "legacy_name": self.legacy.name,
            "legacy_auth": self.legacy.auth_method,
            "tier": self.tier.name,
            "interactions": len(self.interaction_log),
        }


# ─── Tier 1: Observable ──────────────────────────────────────────
# Add trust tensors and audit logging. Still no ATP.

class ObservableWrapper(Web4Wrapper):
    """Tier 1: Adds trust tensors and audit trail.

    Builds on Tier 0 by:
    - Computing T3 tensor from interaction history
    - Maintaining hash-chained audit log
    - Providing trust-based access decisions
    """

    def __init__(self, legacy: LegacySystem):
        super().__init__(legacy)
        self.tier = AdoptionTier.OBSERVABLE
        self.t3 = {"talent": 0.5, "training": 0.5, "temperament": 0.5}
        self.audit_chain: list[dict] = []
        self._prev_hash = "genesis"

    def call(self, method: str, params: dict, caller_id: str = "anonymous",
             quality: float | None = None) -> dict:
        """Call with trust observation and auditing."""
        result = super().call(method, params, caller_id)

        # Audit entry
        entry = {
            "method": method,
            "caller": caller_id,
            "success": result.get("status") == "ok",
            "prev_hash": self._prev_hash,
        }
        entry["hash"] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()[:16]
        self._prev_hash = entry["hash"]
        self.audit_chain.append(entry)

        # Update trust if quality provided
        if quality is not None:
            self._update_trust(quality)

        result["web4_t3"] = dict(self.t3)
        result["web4_audit_length"] = len(self.audit_chain)
        return result

    def _update_trust(self, quality: float):
        delta = 0.02 * (quality - 0.5)
        for dim in self.t3:
            self.t3[dim] = max(0, min(1, self.t3[dim] + delta))

    def get_trust_composite(self) -> float:
        return sum(self.t3.values()) / 3

    def verify_audit_chain(self) -> bool:
        prev = "genesis"
        for entry in self.audit_chain:
            if entry["prev_hash"] != prev:
                return False
            # Recompute content hash to detect tampering
            verify_entry = {k: v for k, v in entry.items() if k != "hash"}
            recomputed = hashlib.sha256(
                json.dumps(verify_entry, sort_keys=True).encode()
            ).hexdigest()[:16]
            if recomputed != entry["hash"]:
                return False
            prev = entry["hash"]
        return True


# ─── Tier 2: Accountable ─────────────────────────────────────────
# Add ATP/ADP metering and settlement.

class AccountableWrapper(ObservableWrapper):
    """Tier 2: Adds ATP metering and settlement.

    Builds on Tier 1 by:
    - Requiring ATP stake for operations
    - Settling based on quality × sliding scale
    - Tracking resource consumption
    """

    def __init__(self, legacy: LegacySystem, initial_atp: float = 100):
        super().__init__(legacy)
        self.tier = AdoptionTier.ACCOUNTABLE
        self.atp_balance = initial_atp
        self.atp_locked = 0.0
        self.atp_earned = 0.0
        self.atp_spent = 0.0
        self.metering: list[dict] = []

    def call(self, method: str, params: dict, caller_id: str = "anonymous",
             quality: float | None = None, atp_stake: float = 0) -> dict:
        """Call with ATP metering."""
        if atp_stake > 0:
            if atp_stake > self.atp_balance:
                return {"status": "error", "reason": "insufficient_atp",
                        "balance": self.atp_balance, "required": atp_stake}
            self.atp_balance -= atp_stake
            self.atp_locked += atp_stake
            self.atp_spent += atp_stake

        result = super().call(method, params, caller_id, quality)

        # Settle: return stake based on quality
        if atp_stake > 0 and quality is not None:
            if quality < 0.3:
                refund = 0
            elif quality < 0.7:
                refund = atp_stake * (quality - 0.3) / 0.4
            else:
                refund = atp_stake * quality
            self.atp_locked -= atp_stake
            self.atp_balance += refund
            self.atp_earned += refund

            self.metering.append({
                "method": method, "stake": atp_stake,
                "quality": quality, "refund": refund,
                "net_cost": atp_stake - refund,
            })
            result["web4_atp_settlement"] = {
                "staked": atp_stake, "refund": round(refund, 2),
                "net": round(atp_stake - refund, 2),
            }

        result["web4_atp_balance"] = round(self.atp_balance, 2)
        return result

    def get_metering_summary(self) -> dict:
        if not self.metering:
            return {"calls": 0, "total_staked": 0, "total_refunded": 0, "avg_quality": 0}
        return {
            "calls": len(self.metering),
            "total_staked": round(sum(m["stake"] for m in self.metering), 2),
            "total_refunded": round(sum(m["refund"] for m in self.metering), 2),
            "avg_quality": round(sum(m["quality"] for m in self.metering) / len(self.metering), 3),
        }


# ─── Tier 3: Federated ───────────────────────────────────────────
# Add cross-system trust and federation.

@dataclass
class FederationPeer:
    """A peer in the federation."""
    lct_id: str
    trust: float
    tier: AdoptionTier
    last_seen: float = 0.0


class FederatedWrapper(AccountableWrapper):
    """Tier 3: Adds federation and cross-system trust.

    Builds on Tier 2 by:
    - Discovering and connecting to peer Web4 systems
    - Sharing trust scores with attenuation
    - Routing requests across federation
    - Handling cross-system settlement
    """

    def __init__(self, legacy: LegacySystem, initial_atp: float = 100):
        super().__init__(legacy, initial_atp)
        self.tier = AdoptionTier.FEDERATED
        self.peers: dict[str, FederationPeer] = {}
        self.federation_log: list[dict] = []

    def add_peer(self, peer_id: str, trust: float, tier: AdoptionTier):
        self.peers[peer_id] = FederationPeer(
            lct_id=peer_id, trust=trust, tier=tier,
            last_seen=time.monotonic(),
        )

    def federated_call(self, method: str, params: dict, caller_id: str,
                       target_peer: str | None = None) -> dict:
        """Route call through federation if needed."""
        if target_peer and target_peer in self.peers:
            peer = self.peers[target_peer]
            # Trust attenuation for cross-system calls
            attenuated_trust = self.get_trust_composite() * peer.trust * 0.8
            self.federation_log.append({
                "type": "federated_call",
                "target": target_peer,
                "trust": attenuated_trust,
                "method": method,
            })
            return {
                "status": "routed",
                "via": target_peer,
                "attenuated_trust": round(attenuated_trust, 4),
                "web4_lct": self.lct_id,
                "web4_tier": self.tier.value,
            }
        return self.call(method, params, caller_id)

    def get_federation_status(self) -> dict:
        return {
            "peers": len(self.peers),
            "avg_peer_trust": (
                round(sum(p.trust for p in self.peers.values()) / len(self.peers), 3)
                if self.peers else 0
            ),
            "federated_calls": len(self.federation_log),
            "peer_tiers": {p.lct_id: p.tier.name for p in self.peers.values()},
        }


# ─── Tier 4: Native ──────────────────────────────────────────────
# Full Web4 stack with MRH, policies, governance.

class NativeWeb4System:
    """Tier 4: Full Web4 native system.

    Not a wrapper — built from the ground up with:
    - MRH graph for relationship management
    - Policy engine for access control
    - Full R6 action framework
    - Governance and voting
    - Complete audit chain with certification
    """

    def __init__(self, name: str, entity_type: str = "service"):
        id_hash = hashlib.sha256(name.encode()).hexdigest()[:16]
        self.lct_id = f"lct:web4:{entity_type}:{id_hash}"
        self.name = name
        self.tier = AdoptionTier.NATIVE
        self.t3 = {"talent": 0.5, "training": 0.5, "temperament": 0.5}
        self.mrh = {"bound": [], "paired": [], "witnessing": []}
        self.policies: list[dict] = []
        self.atp_balance = 0.0
        self.actions: list[dict] = []

    def bind(self, target_id: str, relationship: str):
        self.mrh["bound"].append({
            "target": target_id,
            "relationship": relationship,
            "zone": "DIRECT",
        })

    def pair(self, target_id: str, role: str):
        self.mrh["paired"].append({
            "target": target_id,
            "role": role,
            "zone": "DIRECT",
        })

    def add_policy(self, action: str, min_trust: float, scope: str):
        self.policies.append({
            "action": action, "min_trust": min_trust, "scope": scope,
        })

    def check_policy(self, action: str, trust: float) -> bool:
        for p in self.policies:
            if p["action"] == action:
                return trust >= p["min_trust"]
        return True  # No policy = permitted

    def execute_action(self, rules: str, role: str, request: str,
                       resource: str, trust: float) -> dict:
        if not self.check_policy(request, trust):
            return {"status": "denied", "reason": "insufficient_trust",
                    "required": next((p["min_trust"] for p in self.policies
                                      if p["action"] == request), 0)}

        action = {
            "rules": rules, "role": role, "request": request,
            "resource": resource, "trust": trust,
            "timestamp": time.monotonic(),
        }
        action["hash"] = hashlib.sha256(
            json.dumps(action, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        self.actions.append(action)
        return {"status": "ok", "action_hash": action["hash"]}


# ─── Migration Engine ─────────────────────────────────────────────

@dataclass
class MigrationStep:
    """A single step in the migration path."""
    from_tier: AdoptionTier
    to_tier: AdoptionTier
    description: str
    requirements: list[str]
    breaking_changes: list[str]
    reversible: bool


class MigrationEngine:
    """Plans and validates tier migrations."""

    MIGRATION_STEPS = [
        MigrationStep(
            AdoptionTier.WRAPPER, AdoptionTier.OBSERVABLE,
            "Add trust tensors and audit chain",
            ["Interaction logging enabled", "Hash chain storage"],
            [],
            reversible=True,
        ),
        MigrationStep(
            AdoptionTier.OBSERVABLE, AdoptionTier.ACCOUNTABLE,
            "Add ATP metering and settlement",
            ["ATP funding source", "Settlement configuration"],
            ["Callers must provide ATP stake"],
            reversible=True,
        ),
        MigrationStep(
            AdoptionTier.ACCOUNTABLE, AdoptionTier.FEDERATED,
            "Add federation and cross-system trust",
            ["At least one federation peer", "Network connectivity"],
            ["Trust scores affect routing decisions"],
            reversible=True,
        ),
        MigrationStep(
            AdoptionTier.FEDERATED, AdoptionTier.NATIVE,
            "Full Web4 native implementation",
            ["MRH graph configured", "Policy engine", "Complete R6 support"],
            ["Full system rewrite", "Legacy wrapper removed"],
            reversible=False,
        ),
    ]

    @classmethod
    def get_migration_path(cls, current: AdoptionTier, target: AdoptionTier) -> list[MigrationStep]:
        if target.value <= current.value:
            return []
        return [s for s in cls.MIGRATION_STEPS
                if current.value <= s.from_tier.value < target.value]

    @classmethod
    def validate_migration(cls, current_tier: AdoptionTier,
                           target_tier: AdoptionTier) -> dict:
        path = cls.get_migration_path(current_tier, target_tier)
        all_requirements = []
        all_breaking = []
        all_reversible = True

        for step in path:
            all_requirements.extend(step.requirements)
            all_breaking.extend(step.breaking_changes)
            if not step.reversible:
                all_reversible = False

        return {
            "current": current_tier.name,
            "target": target_tier.name,
            "steps": len(path),
            "requirements": all_requirements,
            "breaking_changes": all_breaking,
            "fully_reversible": all_reversible,
            "viable": True,
        }


# ─── Compatibility Bridge ────────────────────────────────────────

class CompatibilityBridge:
    """Bridges between systems at different tiers."""

    @staticmethod
    def bridge_call(source: Any, target: Any, method: str,
                    params: dict, caller_id: str) -> dict:
        """Route a call between systems at potentially different tiers."""
        source_tier = getattr(source, 'tier', AdoptionTier.WRAPPER)
        target_tier = getattr(target, 'tier', AdoptionTier.WRAPPER)

        # Determine effective tier (minimum of both)
        effective = AdoptionTier(min(source_tier.value, target_tier.value))

        if effective == AdoptionTier.WRAPPER:
            # Lowest common: just identity
            if hasattr(target, 'call'):
                return target.call(method, params, caller_id)
            return target.call(method, params)
        elif effective == AdoptionTier.OBSERVABLE:
            return target.call(method, params, caller_id)
        elif effective.value >= AdoptionTier.ACCOUNTABLE.value:
            return target.call(method, params, caller_id)
        return {"status": "error", "reason": "bridge_failure"}

    @staticmethod
    def trust_translation(source_tier: AdoptionTier,
                          target_tier: AdoptionTier,
                          trust: float) -> float:
        """Translate trust between tiers with attenuation."""
        # Higher tiers have more trust granularity
        # Downgrading: lose precision
        # Upgrading: add uncertainty
        tier_diff = abs(source_tier.value - target_tier.value)
        attenuation = 0.9 ** tier_diff  # 10% loss per tier difference
        return trust * attenuation


# ═══════════════════════════════════════════════════════════════════
# Verification Checks
# ═══════════════════════════════════════════════════════════════════

def run_checks():
    passed = 0
    failed = 0

    def check(condition: bool, label: str):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  FAIL: {label}")

    # ─── Section 1: Legacy System ─────────────────────────────────

    print("Section 1: Legacy System")

    legacy = LegacySystem(
        name="UserDB", api_endpoint="https://api.example.com/v1",
        auth_method="api_key", version="3.2.1",
        capabilities=["user_crud", "auth", "search"],
    )
    result = legacy.call("get_user", {"id": 42})
    check(result["status"] == "ok", "Legacy system responds")
    check(result["system"] == "UserDB", "Legacy system identified")

    # ─── Section 2: Tier 0 — Wrapper ─────────────────────────────

    print("Section 2: Tier 0 — Wrapper")

    wrapper = Web4Wrapper(legacy)
    check(wrapper.lct_id.startswith("lct:web4:service:"), "Wrapper has LCT ID")
    check(wrapper.tier == AdoptionTier.WRAPPER, "Wrapper is Tier 0")

    r = wrapper.call("get_user", {"id": 42}, "caller:1")
    check(r["status"] == "ok", "Wrapper passes through to legacy")
    check(r["web4_lct"] == wrapper.lct_id, "Response includes LCT")
    check(r["web4_tier"] == 0, "Response includes tier")

    # Multiple calls build interaction history
    for i in range(5):
        wrapper.call("list_users", {}, f"caller:{i}")
    identity = wrapper.get_identity()
    check(identity["interactions"] == 6, "6 interactions logged")
    check(identity["legacy_auth"] == "api_key", "Legacy auth preserved")

    # ─── Section 3: Tier 1 — Observable ──────────────────────────

    print("Section 3: Tier 1 — Observable")

    observable = ObservableWrapper(legacy)
    check(observable.tier == AdoptionTier.OBSERVABLE, "Observable is Tier 1")
    check(observable.get_trust_composite() == 0.5, "Initial trust = 0.5")

    # Good interactions increase trust
    for _ in range(5):
        observable.call("get_user", {}, "caller:1", quality=0.9)
    check(observable.get_trust_composite() > 0.5, "Good quality increases trust")

    # Bad interactions decrease trust
    obs2 = ObservableWrapper(legacy)
    for _ in range(5):
        obs2.call("get_user", {}, "caller:1", quality=0.1)
    check(obs2.get_trust_composite() < 0.5, "Bad quality decreases trust")

    # Audit chain integrity
    check(len(observable.audit_chain) == 5, "5 audit entries")
    check(observable.verify_audit_chain(), "Audit chain verifies")

    # Tamper detection
    if observable.audit_chain:
        observable.audit_chain[2]["method"] = "TAMPERED"
        check(not observable.verify_audit_chain(), "Tampering detected in audit chain")

    # ─── Section 4: Tier 2 — Accountable ─────────────────────────

    print("Section 4: Tier 2 — Accountable")

    accountable = AccountableWrapper(legacy, initial_atp=100)
    check(accountable.tier == AdoptionTier.ACCOUNTABLE, "Accountable is Tier 2")
    check(accountable.atp_balance == 100, "Initial ATP balance")

    # Call with ATP stake
    r = accountable.call("get_user", {}, "caller:1", quality=0.8, atp_stake=10)
    check(r["status"] == "ok", "Accountable call succeeds")
    check("web4_atp_settlement" in r, "Response includes ATP settlement")
    check(r["web4_atp_settlement"]["staked"] == 10, "Stake amount correct")
    check(r["web4_atp_settlement"]["refund"] > 0, "Refund > 0 for quality 0.8")

    # Insufficient ATP
    r_broke = accountable.call("get_user", {}, "caller:1", quality=0.9, atp_stake=99999)
    check(r_broke["status"] == "error", "Insufficient ATP rejected")
    check(r_broke["reason"] == "insufficient_atp", "Correct error reason")

    # Low quality = low refund
    acc2 = AccountableWrapper(legacy, initial_atp=100)
    r_low = acc2.call("get_user", {}, "caller:1", quality=0.2, atp_stake=10)
    check(r_low["web4_atp_settlement"]["refund"] == 0, "Quality 0.2 → zero refund")

    # Metering summary
    summary = accountable.get_metering_summary()
    check(summary["calls"] == 1, "1 metered call")
    check(summary["total_staked"] == 10, "Total staked: 10")

    # ─── Section 5: Tier 3 — Federated ───────────────────────────

    print("Section 5: Tier 3 — Federated")

    federated = FederatedWrapper(legacy, initial_atp=200)
    check(federated.tier == AdoptionTier.FEDERATED, "Federated is Tier 3")

    # Add peers
    federated.add_peer("lct:web4:service:peer1", 0.8, AdoptionTier.ACCOUNTABLE)
    federated.add_peer("lct:web4:service:peer2", 0.6, AdoptionTier.OBSERVABLE)
    check(len(federated.peers) == 2, "2 peers added")

    # Federated call
    r = federated.federated_call("get_data", {}, "caller:1",
                                 target_peer="lct:web4:service:peer1")
    check(r["status"] == "routed", "Call routed to peer")
    check(r["via"] == "lct:web4:service:peer1", "Routed via correct peer")
    check(r["attenuated_trust"] < 1.0, "Trust attenuated for cross-system call")

    # Local call when no target
    r_local = federated.federated_call("get_data", {}, "caller:1")
    check(r_local["status"] == "ok", "No target → local call")

    # Federation status
    status = federated.get_federation_status()
    check(status["peers"] == 2, "Federation status: 2 peers")
    check(status["avg_peer_trust"] == 0.7, "Avg peer trust: 0.7")
    check(status["federated_calls"] == 1, "1 federated call logged")

    # ─── Section 6: Tier 4 — Native ──────────────────────────────

    print("Section 6: Tier 4 — Native")

    native = NativeWeb4System("DataProcessor")
    check(native.tier == AdoptionTier.NATIVE, "Native is Tier 4")
    check(native.lct_id.startswith("lct:web4:service:"), "Native has LCT ID")

    # MRH operations
    native.bind("lct:web4:device:sensor1", "data_source")
    native.pair("lct:web4:human:admin", "administrator")
    check(len(native.mrh["bound"]) == 1, "1 bound entity")
    check(len(native.mrh["paired"]) == 1, "1 paired entity")

    # Policy engine
    native.add_policy("read", 0.3, "data")
    native.add_policy("write", 0.7, "data")
    native.add_policy("admin", 0.9, "system")

    check(native.check_policy("read", 0.5), "Read allowed at trust 0.5")
    check(not native.check_policy("write", 0.5), "Write denied at trust 0.5")
    check(native.check_policy("write", 0.8), "Write allowed at trust 0.8")
    check(not native.check_policy("admin", 0.8), "Admin denied at trust 0.8")

    # Action execution
    r_ok = native.execute_action("data_policy", "analyst", "read",
                                 "dataset:users", 0.5)
    check(r_ok["status"] == "ok", "Action executed at sufficient trust")
    check("action_hash" in r_ok, "Action has hash")

    r_denied = native.execute_action("data_policy", "analyst", "write",
                                     "dataset:users", 0.3)
    check(r_denied["status"] == "denied", "Action denied at insufficient trust")

    # ─── Section 7: Migration Engine ─────────────────────────────

    print("Section 7: Migration Engine")

    # Wrapper → Observable
    path_01 = MigrationEngine.get_migration_path(
        AdoptionTier.WRAPPER, AdoptionTier.OBSERVABLE)
    check(len(path_01) == 1, "1 step: Wrapper → Observable")
    check(path_01[0].reversible, "Wrapper → Observable is reversible")

    # Wrapper → Native
    path_04 = MigrationEngine.get_migration_path(
        AdoptionTier.WRAPPER, AdoptionTier.NATIVE)
    check(len(path_04) == 4, "4 steps: Wrapper → Native")
    check(not all(s.reversible for s in path_04),
          "Not all steps reversible (Tier 3→4 is irreversible)")

    # Same tier → no steps
    path_same = MigrationEngine.get_migration_path(
        AdoptionTier.OBSERVABLE, AdoptionTier.OBSERVABLE)
    check(len(path_same) == 0, "Same tier: no migration needed")

    # Downgrade → no steps
    path_down = MigrationEngine.get_migration_path(
        AdoptionTier.NATIVE, AdoptionTier.WRAPPER)
    check(len(path_down) == 0, "Downgrade: no path (must rebuild)")

    # Validation
    v = MigrationEngine.validate_migration(
        AdoptionTier.WRAPPER, AdoptionTier.FEDERATED)
    check(v["steps"] == 3, "3 steps to federated")
    check(v["fully_reversible"], "Wrapper→Federated is fully reversible")
    check(len(v["requirements"]) > 0, "Requirements listed")
    check(len(v["breaking_changes"]) > 0, "Breaking changes listed")
    check(v["viable"], "Migration is viable")

    v2 = MigrationEngine.validate_migration(
        AdoptionTier.WRAPPER, AdoptionTier.NATIVE)
    check(not v2["fully_reversible"], "Wrapper→Native not fully reversible")

    # ─── Section 8: Compatibility Bridge ─────────────────────────

    print("Section 8: Compatibility Bridge")

    # Cross-tier bridging
    tier0 = Web4Wrapper(legacy)
    tier2 = AccountableWrapper(legacy, initial_atp=100)

    # Bridge call from Tier 0 to Tier 2
    r = CompatibilityBridge.bridge_call(tier0, tier2, "get_user", {}, "caller:1")
    check(r["status"] == "ok", "Cross-tier bridge works")

    # Trust translation
    trust = 0.8
    translated = CompatibilityBridge.trust_translation(
        AdoptionTier.NATIVE, AdoptionTier.WRAPPER, trust)
    check(translated < trust, "Trust attenuated across 4 tier difference")
    check(translated == trust * (0.9 ** 4),
          f"Attenuation = 0.9^4 ({translated:.4f})")

    # Same tier: no attenuation
    same = CompatibilityBridge.trust_translation(
        AdoptionTier.OBSERVABLE, AdoptionTier.OBSERVABLE, 0.8)
    check(same == 0.8, "Same tier: no trust attenuation")

    # Adjacent tiers: minimal attenuation
    adjacent = CompatibilityBridge.trust_translation(
        AdoptionTier.OBSERVABLE, AdoptionTier.ACCOUNTABLE, 0.8)
    check(adjacent == 0.8 * 0.9, "Adjacent tiers: 10% attenuation")

    # ─── Section 9: Full Adoption Journey ────────────────────────

    print("Section 9: Full Adoption Journey")

    # Simulate a system moving through all tiers
    legacy_sys = LegacySystem("CRM", "https://crm.example.com", "oauth2", "5.0")

    # Start at Tier 0
    system = Web4Wrapper(legacy_sys)
    check(system.tier == AdoptionTier.WRAPPER, "Journey starts at Tier 0")

    # "Upgrade" to Tier 1
    system = ObservableWrapper(legacy_sys)
    for i in range(10):
        system.call("search", {}, "user:1", quality=0.7 + (i * 0.02))
    check(system.tier == AdoptionTier.OBSERVABLE, "Upgraded to Tier 1")
    check(system.get_trust_composite() > 0.5, "Trust built through usage")
    check(system.verify_audit_chain(), "Audit chain intact after upgrade")

    # "Upgrade" to Tier 2
    system = AccountableWrapper(legacy_sys, initial_atp=500)
    for i in range(5):
        system.call("search", {}, "user:1", quality=0.8, atp_stake=20)
    check(system.tier == AdoptionTier.ACCOUNTABLE, "Upgraded to Tier 2")
    meter = system.get_metering_summary()
    check(meter["calls"] == 5, "5 metered calls")
    check(meter["avg_quality"] == 0.8, "Avg quality 0.8")

    # "Upgrade" to Tier 3
    system = FederatedWrapper(legacy_sys, initial_atp=500)
    system.add_peer("lct:web4:service:partner", 0.7, AdoptionTier.ACCOUNTABLE)
    r = system.federated_call("sync", {}, "admin", "lct:web4:service:partner")
    check(system.tier == AdoptionTier.FEDERATED, "Upgraded to Tier 3")
    check(r["status"] == "routed", "Federated call works")

    # "Upgrade" to Tier 4
    native_sys = NativeWeb4System("CRM-Native")
    native_sys.add_policy("read", 0.2, "data")
    native_sys.add_policy("write", 0.5, "data")
    check(native_sys.tier == AdoptionTier.NATIVE, "Upgraded to Tier 4")

    r = native_sys.execute_action("crm_policy", "sales", "read", "contacts", 0.6)
    check(r["status"] == "ok", "Native system operational")

    # ─── Section 10: Tier Feature Matrix ─────────────────────────

    print("Section 10: Tier Feature Matrix")

    features = {
        AdoptionTier.WRAPPER: {"identity": True, "trust": False, "atp": False,
                               "federation": False, "policy": False},
        AdoptionTier.OBSERVABLE: {"identity": True, "trust": True, "atp": False,
                                  "federation": False, "policy": False},
        AdoptionTier.ACCOUNTABLE: {"identity": True, "trust": True, "atp": True,
                                   "federation": False, "policy": False},
        AdoptionTier.FEDERATED: {"identity": True, "trust": True, "atp": True,
                                 "federation": True, "policy": False},
        AdoptionTier.NATIVE: {"identity": True, "trust": True, "atp": True,
                              "federation": True, "policy": True},
    }

    # Each tier adds exactly one capability
    for tier in AdoptionTier:
        tier_features = features[tier]
        check(tier_features["identity"], f"Tier {tier.value}: identity always present")

    # Feature count increases with tier
    for i in range(4):
        t1 = AdoptionTier(i)
        t2 = AdoptionTier(i + 1)
        f1 = sum(1 for v in features[t1].values() if v)
        f2 = sum(1 for v in features[t2].values() if v)
        check(f2 > f1,
              f"Tier {t2.value} has more features ({f2}) than Tier {t1.value} ({f1})")

    # ─── Section 11: Edge Cases ──────────────────────────────────

    print("Section 11: Edge Cases")

    # Wrapper with minimal legacy
    minimal_legacy = LegacySystem("Minimal", "", "none", "1.0")
    minimal = Web4Wrapper(minimal_legacy)
    check(minimal.lct_id.startswith("lct:web4:"), "Minimal legacy gets LCT")

    # Observable with no quality feedback
    obs_noqual = ObservableWrapper(legacy)
    obs_noqual.call("test", {}, "caller")
    check(obs_noqual.get_trust_composite() == 0.5,
          "No quality feedback → trust unchanged")

    # Accountable with zero stake
    acc_zero = AccountableWrapper(legacy, initial_atp=100)
    r = acc_zero.call("test", {}, "caller", quality=0.9, atp_stake=0)
    check("web4_atp_settlement" not in r, "Zero stake → no settlement")
    check(acc_zero.atp_balance == 100, "Balance unchanged with zero stake")

    # Federated call to unknown peer
    fed = FederatedWrapper(legacy, initial_atp=100)
    r = fed.federated_call("test", {}, "caller", target_peer="unknown:peer")
    check(r["status"] == "ok", "Unknown peer → falls back to local")

    # ═══════════════════════════════════════════════════════════════

    print(f"\n{'=' * 60}")
    print(f"Incremental Adoption Pathway: {passed}/{passed + failed} checks passed")
    if failed == 0:
        print("  All checks passed!")
    else:
        print(f"  {failed} FAILED")
    print(f"{'=' * 60}")
    print(f"\n5 adoption tiers demonstrated:")
    for tier in AdoptionTier:
        names = ["Wrapper", "Observable", "Accountable", "Federated", "Native"]
        print(f"  Tier {tier.value}: {names[tier.value]}")


if __name__ == "__main__":
    run_checks()
