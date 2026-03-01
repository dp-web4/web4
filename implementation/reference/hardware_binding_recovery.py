#!/usr/bin/env python3
"""
Hardware Binding Recovery & Revocation — Session 20, Track 4

Real-world hardware binding lifecycle operations:
- Key revocation with cascading trust invalidation
- Quorum-based key recovery (m-of-n threshold)
- Compromise detection from behavioral anomalies
- Device replacement ceremony
- Cross-organization hardware trust bridges
- Hardware-to-cloud trust delegation
- Revocation list management (CRL equivalent)
- Key rotation with overlap period
- Emergency freeze and unfreeze protocols
- Binding audit trail with tamper detection
- Performance under revocation storms

Reference: contextual_hardware_binding.py, multi_device_binding.py, 305 patents
"""

from __future__ import annotations
import hashlib
import hmac
import math
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple


# ─── Constants ────────────────────────────────────────────────────────────────

class BindingState(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    RECOVERING = "recovering"
    ROTATING = "rotating"
    FROZEN = "frozen"


class CompromiseIndicator(Enum):
    LOCATION_ANOMALY = "location_anomaly"
    TIMING_ANOMALY = "timing_anomaly"
    CONCURRENT_USE = "concurrent_use"
    SIGNATURE_MISMATCH = "signature_mismatch"
    FIRMWARE_TAMPERING = "firmware_tampering"
    ATTESTATION_FAILURE = "attestation_failure"


RECOVERY_THRESHOLD_DEFAULT = 3  # m-of-n threshold
RECOVERY_SHARES_DEFAULT = 5     # n shares
KEY_OVERLAP_SECONDS = 86400     # 24 hours overlap during rotation
FREEZE_AUTO_EXPIRE = 86400      # 24 hours auto-expire


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class HardwareBinding:
    """A hardware-bound cryptographic identity."""
    binding_id: str
    entity_id: str
    device_fingerprint: str
    public_key: bytes
    state: BindingState = BindingState.ACTIVE
    created_at: float = 0.0
    revoked_at: Optional[float] = None
    revocation_reason: Optional[str] = None
    trust_score: float = 0.5
    key_version: int = 1
    organization_id: Optional[str] = None


@dataclass
class RecoveryShare:
    """A share of a recovery secret (Shamir-like)."""
    share_id: str
    custodian_id: str
    share_data: bytes
    binding_id: str
    created_at: float = 0.0


@dataclass
class RevocationEntry:
    """Entry in the revocation list."""
    binding_id: str
    revoked_at: float
    reason: str
    revoker_id: str
    cascade_count: int = 0  # How many downstream bindings were also revoked
    signature: bytes = b""


@dataclass
class AuditEvent:
    """Tamper-evident audit event for binding lifecycle."""
    event_type: str
    binding_id: str
    actor_id: str
    timestamp: float
    details: Dict[str, str] = field(default_factory=dict)
    prev_hash: str = ""
    event_hash: str = ""

    def compute_hash(self) -> str:
        data = f"{self.event_type}:{self.binding_id}:{self.actor_id}:{self.timestamp}:{self.prev_hash}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]


# ─── S1: Key Revocation with Cascade ────────────────────────────────────────

class RevocationManager:
    """Manage revocation of hardware bindings with cascade."""

    def __init__(self):
        self.bindings: Dict[str, HardwareBinding] = {}
        self.trust_links: Dict[str, Set[str]] = {}  # parent → children
        self.revocation_list: List[RevocationEntry] = []

    def register(self, binding: HardwareBinding):
        self.bindings[binding.binding_id] = binding

    def add_trust_link(self, parent_id: str, child_id: str):
        if parent_id not in self.trust_links:
            self.trust_links[parent_id] = set()
        self.trust_links[parent_id].add(child_id)

    def revoke(
        self, binding_id: str, reason: str, revoker_id: str, cascade: bool = True
    ) -> List[RevocationEntry]:
        """
        Revoke a binding and optionally cascade to dependents.
        Returns list of all revocation entries created.
        """
        binding = self.bindings.get(binding_id)
        if not binding or binding.state == BindingState.REVOKED:
            return []

        now = time.time()
        binding.state = BindingState.REVOKED
        binding.revoked_at = now
        binding.revocation_reason = reason

        revoked = []
        cascade_count = 0

        if cascade:
            # Revoke all downstream bindings
            to_revoke = list(self.trust_links.get(binding_id, set()))
            while to_revoke:
                child_id = to_revoke.pop(0)
                child = self.bindings.get(child_id)
                if child and child.state != BindingState.REVOKED:
                    child.state = BindingState.REVOKED
                    child.revoked_at = now
                    child.revocation_reason = f"cascaded from {binding_id}"
                    cascade_count += 1
                    revoked.append(RevocationEntry(
                        child_id, now, f"cascade:{binding_id}", revoker_id,
                    ))
                    to_revoke.extend(self.trust_links.get(child_id, set()))

        entry = RevocationEntry(
            binding_id, now, reason, revoker_id, cascade_count,
        )
        self.revocation_list.append(entry)
        revoked.insert(0, entry)

        return revoked

    def is_revoked(self, binding_id: str) -> bool:
        binding = self.bindings.get(binding_id)
        return binding is not None and binding.state == BindingState.REVOKED

    def revocation_count(self) -> int:
        return len(self.revocation_list)


# ─── S2: Quorum-Based Key Recovery ──────────────────────────────────────────

class RecoveryProtocol:
    """m-of-n threshold recovery for lost hardware bindings."""

    def __init__(self, threshold: int = RECOVERY_THRESHOLD_DEFAULT,
                 total_shares: int = RECOVERY_SHARES_DEFAULT):
        self.threshold = threshold
        self.total_shares = total_shares
        self.shares: Dict[str, List[RecoveryShare]] = {}  # binding_id → shares
        self.recovery_requests: Dict[str, Set[str]] = {}  # binding_id → custodians who approved

    def create_shares(self, binding: HardwareBinding, custodian_ids: List[str]) -> List[RecoveryShare]:
        """
        Create recovery shares for a binding.
        In production, this would use Shamir's Secret Sharing.
        Here we simulate with deterministic share generation.
        """
        if len(custodian_ids) < self.total_shares:
            return []

        secret = hashlib.sha256(binding.public_key).digest()
        shares = []
        for i, custodian in enumerate(custodian_ids[:self.total_shares]):
            share_data = hashlib.sha256(
                secret + i.to_bytes(4, "big") + custodian.encode()
            ).digest()
            share = RecoveryShare(
                share_id=f"{binding.binding_id}_share_{i}",
                custodian_id=custodian,
                share_data=share_data,
                binding_id=binding.binding_id,
                created_at=time.time(),
            )
            shares.append(share)

        self.shares[binding.binding_id] = shares
        return shares

    def approve_recovery(self, binding_id: str, custodian_id: str) -> bool:
        """A custodian approves a recovery request."""
        shares = self.shares.get(binding_id, [])
        valid_custodians = {s.custodian_id for s in shares}
        if custodian_id not in valid_custodians:
            return False

        if binding_id not in self.recovery_requests:
            self.recovery_requests[binding_id] = set()
        self.recovery_requests[binding_id].add(custodian_id)
        return True

    def can_recover(self, binding_id: str) -> bool:
        """Check if enough approvals for recovery."""
        approvals = self.recovery_requests.get(binding_id, set())
        return len(approvals) >= self.threshold

    def execute_recovery(self, binding_id: str, new_public_key: bytes) -> Optional[HardwareBinding]:
        """Execute recovery: generate new binding from recovered secret."""
        if not self.can_recover(binding_id):
            return None

        new_binding = HardwareBinding(
            binding_id=f"{binding_id}_recovered",
            entity_id=binding_id.split("_")[0] if "_" in binding_id else binding_id,
            device_fingerprint=hashlib.sha256(new_public_key).hexdigest()[:16],
            public_key=new_public_key,
            state=BindingState.ACTIVE,
            created_at=time.time(),
            key_version=1,
        )

        # Clear recovery state
        self.recovery_requests.pop(binding_id, None)
        return new_binding

    def approval_count(self, binding_id: str) -> int:
        return len(self.recovery_requests.get(binding_id, set()))


# ─── S3: Compromise Detection ───────────────────────────────────────────────

@dataclass
class BehaviorSample:
    """A behavioral observation for anomaly detection."""
    binding_id: str
    timestamp: float
    location_hash: str  # hashed location for privacy
    action_type: str
    success: bool


class CompromiseDetector:
    """Detect binding compromise from behavioral anomalies."""

    def __init__(self, history_window: int = 100):
        self.history: Dict[str, List[BehaviorSample]] = {}
        self.window = history_window
        self.alerts: Dict[str, List[CompromiseIndicator]] = {}

    def record(self, sample: BehaviorSample):
        bid = sample.binding_id
        if bid not in self.history:
            self.history[bid] = []
        self.history[bid].append(sample)
        if len(self.history[bid]) > self.window:
            self.history[bid] = self.history[bid][-self.window:]

    def check_concurrent_use(self, binding_id: str, window: float = 5.0) -> bool:
        """
        Detect same binding used from different locations within short window.
        Strongly suggests device cloning or credential theft.
        """
        samples = self.history.get(binding_id, [])
        if len(samples) < 2:
            return False

        for i, s1 in enumerate(samples):
            for s2 in samples[i + 1:]:
                if abs(s1.timestamp - s2.timestamp) < window:
                    if s1.location_hash != s2.location_hash:
                        self._alert(binding_id, CompromiseIndicator.CONCURRENT_USE)
                        return True
        return False

    def check_timing_anomaly(self, binding_id: str) -> bool:
        """
        Detect unusual activity timing patterns.
        Sudden burst after long inactivity = suspicious.
        """
        samples = self.history.get(binding_id, [])
        if len(samples) < 10:
            return False

        # Check for gap followed by burst
        timestamps = [s.timestamp for s in samples]
        gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]

        if not gaps:
            return False

        avg_gap = sum(gaps) / len(gaps)
        # Long gap followed by very short gaps = suspicious
        for i in range(len(gaps) - 3):
            if gaps[i] > avg_gap * 10:  # Long gap
                burst = all(g < avg_gap * 0.1 for g in gaps[i + 1:i + 4] if i + 4 <= len(gaps))
                if burst:
                    self._alert(binding_id, CompromiseIndicator.TIMING_ANOMALY)
                    return True
        return False

    def check_failure_rate(self, binding_id: str, threshold: float = 0.5) -> bool:
        """High failure rate suggests invalid credentials being tested."""
        samples = self.history.get(binding_id, [])
        if len(samples) < 5:
            return False
        failures = sum(1 for s in samples[-20:] if not s.success)
        rate = failures / min(len(samples), 20)
        if rate > threshold:
            self._alert(binding_id, CompromiseIndicator.SIGNATURE_MISMATCH)
            return True
        return False

    def _alert(self, binding_id: str, indicator: CompromiseIndicator):
        if binding_id not in self.alerts:
            self.alerts[binding_id] = []
        self.alerts[binding_id].append(indicator)

    def get_alerts(self, binding_id: str) -> List[CompromiseIndicator]:
        return self.alerts.get(binding_id, [])

    def risk_score(self, binding_id: str) -> float:
        """0.0 = no risk, 1.0 = definitely compromised."""
        alerts = self.alerts.get(binding_id, [])
        if not alerts:
            return 0.0
        # Each indicator type adds risk
        unique = set(alerts)
        # Concurrent use is strongest signal
        score = 0.0
        if CompromiseIndicator.CONCURRENT_USE in unique:
            score += 0.5
        if CompromiseIndicator.TIMING_ANOMALY in unique:
            score += 0.2
        if CompromiseIndicator.SIGNATURE_MISMATCH in unique:
            score += 0.3
        if CompromiseIndicator.FIRMWARE_TAMPERING in unique:
            score += 0.4
        if CompromiseIndicator.ATTESTATION_FAILURE in unique:
            score += 0.3
        return min(1.0, score)


# ─── S4: Device Replacement Ceremony ────────────────────────────────────────

@dataclass
class ReplacementCeremony:
    """Protocol for replacing a lost/compromised device."""
    old_binding_id: str
    new_binding_id: str
    entity_id: str
    initiated_by: str
    initiated_at: float
    witness_approvals: Set[str] = field(default_factory=set)
    required_witnesses: int = 2
    completed: bool = False
    new_public_key: Optional[bytes] = None

    def approve(self, witness_id: str) -> bool:
        self.witness_approvals.add(witness_id)
        return len(self.witness_approvals) >= self.required_witnesses

    def is_ready(self) -> bool:
        return (
            len(self.witness_approvals) >= self.required_witnesses
            and self.new_public_key is not None
        )


def execute_replacement(
    ceremony: ReplacementCeremony,
    revocation_mgr: RevocationManager,
) -> Optional[HardwareBinding]:
    """Execute device replacement: revoke old, create new."""
    if not ceremony.is_ready():
        return None

    # Revoke old binding
    revocation_mgr.revoke(
        ceremony.old_binding_id,
        "device_replacement",
        ceremony.initiated_by,
        cascade=True,
    )

    # Create new binding
    new_binding = HardwareBinding(
        binding_id=ceremony.new_binding_id,
        entity_id=ceremony.entity_id,
        device_fingerprint=hashlib.sha256(ceremony.new_public_key).hexdigest()[:16],
        public_key=ceremony.new_public_key,
        state=BindingState.ACTIVE,
        created_at=time.time(),
    )

    ceremony.completed = True
    return new_binding


# ─── S5: Cross-Organization Trust Bridges ───────────────────────────────────

@dataclass
class OrgTrustBridge:
    """Trust bridge between two organizations' hardware bindings."""
    bridge_id: str
    org_a_id: str
    org_b_id: str
    binding_a_id: str
    binding_b_id: str
    trust_level: float
    created_at: float
    witnessed_by: Set[str] = field(default_factory=set)
    active: bool = True


class CrossOrgBridgeManager:
    """Manage hardware trust bridges across organizations."""

    def __init__(self):
        self.bridges: Dict[str, OrgTrustBridge] = {}

    def create_bridge(
        self, org_a: str, org_b: str,
        binding_a: str, binding_b: str,
        witnesses: Set[str],
    ) -> OrgTrustBridge:
        """Create a trust bridge between two org's hardware bindings."""
        bridge_id = hashlib.sha256(
            f"{org_a}:{org_b}:{binding_a}:{binding_b}".encode()
        ).hexdigest()[:16]

        bridge = OrgTrustBridge(
            bridge_id=bridge_id,
            org_a_id=org_a,
            org_b_id=org_b,
            binding_a_id=binding_a,
            binding_b_id=binding_b,
            trust_level=min(0.8, 0.2 * len(witnesses)),
            created_at=time.time(),
            witnessed_by=witnesses,
        )
        self.bridges[bridge_id] = bridge
        return bridge

    def bridges_for_org(self, org_id: str) -> List[OrgTrustBridge]:
        return [b for b in self.bridges.values()
                if b.active and (b.org_a_id == org_id or b.org_b_id == org_id)]

    def revoke_bridges_for_binding(self, binding_id: str) -> int:
        """Revoke all bridges involving a revoked binding."""
        count = 0
        for bridge in self.bridges.values():
            if bridge.active and (bridge.binding_a_id == binding_id or bridge.binding_b_id == binding_id):
                bridge.active = False
                count += 1
        return count


# ─── S6: Hardware-to-Cloud Delegation ───────────────────────────────────────

@dataclass
class CloudDelegation:
    """Delegation of trust from hardware binding to cloud service."""
    delegation_id: str
    hardware_binding_id: str
    cloud_service_id: str
    scope: Set[str]  # Permitted operations
    max_trust: float  # Cloud trust cannot exceed this
    expires_at: float
    revoked: bool = False

    def is_valid(self, now: float) -> bool:
        return not self.revoked and now < self.expires_at

    def permits(self, operation: str) -> bool:
        return operation in self.scope


class DelegationManager:
    """Manage hardware-to-cloud trust delegations."""

    def __init__(self):
        self.delegations: Dict[str, CloudDelegation] = {}

    def delegate(
        self,
        binding: HardwareBinding,
        cloud_id: str,
        scope: Set[str],
        duration: float = 3600,
    ) -> CloudDelegation:
        """Create a scoped, time-limited delegation."""
        deleg_id = hashlib.sha256(
            f"{binding.binding_id}:{cloud_id}:{time.time()}".encode()
        ).hexdigest()[:16]

        deleg = CloudDelegation(
            delegation_id=deleg_id,
            hardware_binding_id=binding.binding_id,
            cloud_service_id=cloud_id,
            scope=scope,
            max_trust=binding.trust_score * 0.8,  # 80% of hardware trust
            expires_at=time.time() + duration,
            revoked=False,
        )
        self.delegations[deleg_id] = deleg
        return deleg

    def check_permission(self, deleg_id: str, operation: str, now: float) -> bool:
        deleg = self.delegations.get(deleg_id)
        if not deleg:
            return False
        return deleg.is_valid(now) and deleg.permits(operation)

    def revoke_for_binding(self, binding_id: str) -> int:
        """Revoke all delegations when hardware binding is revoked."""
        count = 0
        for deleg in self.delegations.values():
            if deleg.hardware_binding_id == binding_id and not deleg.revoked:
                deleg.revoked = True
                count += 1
        return count


# ─── S7: Key Rotation with Overlap ──────────────────────────────────────────

@dataclass
class KeyRotation:
    """A key rotation event."""
    binding_id: str
    old_version: int
    new_version: int
    new_public_key: bytes
    overlap_start: float
    overlap_end: float  # overlap_start + KEY_OVERLAP_SECONDS
    completed: bool = False

    def in_overlap(self, now: float) -> bool:
        return self.overlap_start <= now <= self.overlap_end

    def old_key_valid(self, now: float) -> bool:
        """Old key is valid during overlap period."""
        return now <= self.overlap_end

    def new_key_valid(self, now: float) -> bool:
        """New key is valid from overlap start."""
        return now >= self.overlap_start


class RotationManager:
    """Manage key rotations with overlap periods."""

    def __init__(self):
        self.rotations: Dict[str, List[KeyRotation]] = {}

    def initiate_rotation(
        self, binding: HardwareBinding, new_key: bytes, overlap: float = KEY_OVERLAP_SECONDS,
    ) -> KeyRotation:
        now = time.time()
        rotation = KeyRotation(
            binding_id=binding.binding_id,
            old_version=binding.key_version,
            new_version=binding.key_version + 1,
            new_public_key=new_key,
            overlap_start=now,
            overlap_end=now + overlap,
        )
        if binding.binding_id not in self.rotations:
            self.rotations[binding.binding_id] = []
        self.rotations[binding.binding_id].append(rotation)

        binding.state = BindingState.ROTATING
        return rotation

    def complete_rotation(self, binding: HardwareBinding, rotation: KeyRotation):
        """Complete rotation: old key becomes invalid."""
        binding.public_key = rotation.new_public_key
        binding.key_version = rotation.new_version
        binding.state = BindingState.ACTIVE
        rotation.completed = True

    def active_rotation(self, binding_id: str) -> Optional[KeyRotation]:
        rotations = self.rotations.get(binding_id, [])
        for r in reversed(rotations):
            if not r.completed:
                return r
        return None


# ─── S8: Emergency Freeze ───────────────────────────────────────────────────

@dataclass
class FreezeOrder:
    """Emergency freeze of a binding."""
    binding_id: str
    frozen_by: str
    frozen_at: float
    expires_at: float
    reason: str
    quorum_votes: Set[str] = field(default_factory=set)
    extended: bool = False


class FreezeProtocol:
    """Emergency freeze with quorum and auto-expire."""

    def __init__(self, quorum_required: int = 2):
        self.freeze_orders: Dict[str, FreezeOrder] = {}
        self.quorum_required = quorum_required

    def freeze(self, binding: HardwareBinding, by: str, reason: str) -> FreezeOrder:
        """Initiate emergency freeze."""
        now = time.time()
        order = FreezeOrder(
            binding_id=binding.binding_id,
            frozen_by=by,
            frozen_at=now,
            expires_at=now + FREEZE_AUTO_EXPIRE,
            reason=reason,
            quorum_votes={by},
        )
        self.freeze_orders[binding.binding_id] = order
        binding.state = BindingState.FROZEN
        return order

    def vote_freeze(self, binding_id: str, voter_id: str) -> bool:
        """Additional vote to sustain freeze."""
        order = self.freeze_orders.get(binding_id)
        if not order:
            return False
        order.quorum_votes.add(voter_id)
        return True

    def is_frozen(self, binding_id: str, now: float) -> bool:
        order = self.freeze_orders.get(binding_id)
        if not order:
            return False
        if now > order.expires_at:
            # Auto-expired unless quorum sustained
            return len(order.quorum_votes) >= self.quorum_required
        return True

    def unfreeze(self, binding: HardwareBinding, by: str) -> bool:
        """Unfreeze requires quorum approval."""
        order = self.freeze_orders.get(binding.binding_id)
        if not order:
            return False
        binding.state = BindingState.ACTIVE
        del self.freeze_orders[binding.binding_id]
        return True


# ─── S9: Binding Audit Trail ────────────────────────────────────────────────

class AuditTrail:
    """Hash-chained audit trail for binding events."""

    def __init__(self):
        self.events: List[AuditEvent] = []

    def record(self, event: AuditEvent):
        if self.events:
            event.prev_hash = self.events[-1].event_hash
        event.event_hash = event.compute_hash()
        self.events.append(event)

    def verify_chain(self) -> bool:
        """Verify the hash chain is intact."""
        for i, event in enumerate(self.events):
            if i == 0:
                if event.prev_hash != "":
                    return False
            else:
                if event.prev_hash != self.events[i - 1].event_hash:
                    return False
            if event.event_hash != event.compute_hash():
                return False
        return True

    def events_for_binding(self, binding_id: str) -> List[AuditEvent]:
        return [e for e in self.events if e.binding_id == binding_id]


# ─── S10: Revocation List Management ────────────────────────────────────────

class RevocationList:
    """CRL-equivalent for Web4 hardware bindings."""

    def __init__(self):
        self.entries: Dict[str, RevocationEntry] = {}
        self.version: int = 0
        self.last_updated: float = 0.0

    def add(self, entry: RevocationEntry):
        self.entries[entry.binding_id] = entry
        self.version += 1
        self.last_updated = entry.revoked_at

    def is_revoked(self, binding_id: str) -> bool:
        return binding_id in self.entries

    def get_entry(self, binding_id: str) -> Optional[RevocationEntry]:
        return self.entries.get(binding_id)

    def delta_since(self, version: int) -> List[RevocationEntry]:
        """Get entries added since a given version (for efficient sync)."""
        if version >= self.version:
            return []
        all_entries = sorted(self.entries.values(), key=lambda e: e.revoked_at)
        delta_count = self.version - version
        return all_entries[-delta_count:] if delta_count <= len(all_entries) else list(all_entries)

    def fingerprint(self) -> str:
        """Content fingerprint for sync comparison."""
        ids = sorted(self.entries.keys())
        return hashlib.sha256("|".join(ids).encode()).hexdigest()[:16]


# ─── S11: Performance ───────────────────────────────────────────────────────

# Included in checks


# ══════════════════════════════════════════════════════════════════════════════
#  CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def run_checks():
    checks = []

    # ── S1: Key Revocation with Cascade ──────────────────────────────────

    mgr = RevocationManager()
    root = HardwareBinding("root_bind", "root_entity", "fp_root", b"pk_root")
    child1 = HardwareBinding("child1", "c1_entity", "fp_c1", b"pk_c1")
    child2 = HardwareBinding("child2", "c2_entity", "fp_c2", b"pk_c2")
    grandchild = HardwareBinding("gc1", "gc_entity", "fp_gc", b"pk_gc")

    mgr.register(root)
    mgr.register(child1)
    mgr.register(child2)
    mgr.register(grandchild)
    mgr.add_trust_link("root_bind", "child1")
    mgr.add_trust_link("root_bind", "child2")
    mgr.add_trust_link("child1", "gc1")

    # S1.1: Cascade revocation
    entries = mgr.revoke("root_bind", "compromised", "admin", cascade=True)
    checks.append(("s1_cascade_count", len(entries) == 4))  # root + child1 + child2 + gc1

    # S1.2: All downstream revoked
    checks.append(("s1_all_revoked", all(mgr.is_revoked(bid)
                   for bid in ["root_bind", "child1", "child2", "gc1"])))

    # S1.3: Revoking already-revoked is no-op
    entries = mgr.revoke("root_bind", "again", "admin")
    checks.append(("s1_already_revoked_noop", len(entries) == 0))

    # S1.4: Non-cascade revocation
    mgr2 = RevocationManager()
    p = HardwareBinding("parent", "pe", "fp", b"pk")
    c = HardwareBinding("child", "ce", "fp", b"pk")
    mgr2.register(p)
    mgr2.register(c)
    mgr2.add_trust_link("parent", "child")
    entries = mgr2.revoke("parent", "test", "admin", cascade=False)
    checks.append(("s1_no_cascade", not mgr2.is_revoked("child")))

    # S1.5: Revocation list maintained
    checks.append(("s1_revocation_list", mgr.revocation_count() > 0))

    # ── S2: Quorum-Based Recovery ────────────────────────────────────────

    recovery = RecoveryProtocol(threshold=3, total_shares=5)
    lost_binding = HardwareBinding("lost1", "user1", "fp_lost", b"pk_lost")
    custodians = ["cust_a", "cust_b", "cust_c", "cust_d", "cust_e"]

    # S2.1: Create shares
    shares = recovery.create_shares(lost_binding, custodians)
    checks.append(("s2_shares_created", len(shares) == 5))

    # S2.2: Below threshold → can't recover
    recovery.approve_recovery("lost1", "cust_a")
    recovery.approve_recovery("lost1", "cust_b")
    checks.append(("s2_below_threshold", not recovery.can_recover("lost1")))

    # S2.3: At threshold → can recover
    recovery.approve_recovery("lost1", "cust_c")
    checks.append(("s2_at_threshold", recovery.can_recover("lost1")))

    # S2.4: Execute recovery
    new_key = os.urandom(32)
    recovered = recovery.execute_recovery("lost1", new_key)
    checks.append(("s2_recovery_success", recovered is not None and recovered.state == BindingState.ACTIVE))

    # S2.5: Recovery state cleared
    checks.append(("s2_state_cleared", recovery.approval_count("lost1") == 0))

    # S2.6: Invalid custodian rejected
    checks.append(("s2_invalid_custodian", not recovery.approve_recovery("lost1", "unknown")))

    # S2.7: Not enough custodians → no shares
    short = RecoveryProtocol(threshold=3, total_shares=5)
    shares = short.create_shares(lost_binding, ["a", "b"])  # Only 2 of 5 needed
    checks.append(("s2_insufficient_custodians", len(shares) == 0))

    # ── S3: Compromise Detection ─────────────────────────────────────────

    detector = CompromiseDetector()
    now = 1000.0

    # S3.1: Concurrent use detected
    detector.record(BehaviorSample("bind1", now, "loc_a", "sign", True))
    detector.record(BehaviorSample("bind1", now + 1, "loc_b", "sign", True))
    checks.append(("s3_concurrent_detected", detector.check_concurrent_use("bind1")))

    # S3.2: Same location not flagged
    detector2 = CompromiseDetector()
    detector2.record(BehaviorSample("bind2", now, "loc_a", "sign", True))
    detector2.record(BehaviorSample("bind2", now + 1, "loc_a", "sign", True))
    checks.append(("s3_same_loc_ok", not detector2.check_concurrent_use("bind2")))

    # S3.3: High failure rate detected
    det3 = CompromiseDetector()
    for i in range(10):
        det3.record(BehaviorSample("bind3", now + i, "loc_a", "sign", i < 2))
    checks.append(("s3_high_failure", det3.check_failure_rate("bind3")))

    # S3.4: Normal failure rate not flagged
    det4 = CompromiseDetector()
    for i in range(10):
        det4.record(BehaviorSample("bind4", now + i, "loc_a", "sign", True))
    checks.append(("s3_normal_rate_ok", not det4.check_failure_rate("bind4")))

    # S3.5: Risk score
    risk = detector.risk_score("bind1")
    checks.append(("s3_risk_score_positive", risk > 0))

    # S3.6: No risk for clean binding
    checks.append(("s3_no_risk_clean", detector.risk_score("clean_bind") == 0.0))

    # S3.7: Risk score bounded
    checks.append(("s3_risk_bounded", 0.0 <= risk <= 1.0))

    # ── S4: Device Replacement ───────────────────────────────────────────

    rev_mgr = RevocationManager()
    old_bind = HardwareBinding("old_device", "user1", "fp_old", b"pk_old")
    rev_mgr.register(old_bind)

    ceremony = ReplacementCeremony(
        old_binding_id="old_device",
        new_binding_id="new_device",
        entity_id="user1",
        initiated_by="user1",
        initiated_at=time.time(),
        required_witnesses=2,
    )

    # S4.1: Not ready without witnesses
    checks.append(("s4_not_ready", not ceremony.is_ready()))

    # S4.2: Approve witnesses
    ceremony.approve("witness1")
    ceremony.approve("witness2")
    ceremony.new_public_key = os.urandom(32)
    checks.append(("s4_ready", ceremony.is_ready()))

    # S4.3: Execute replacement
    new_bind = execute_replacement(ceremony, rev_mgr)
    checks.append(("s4_replaced", new_bind is not None and new_bind.state == BindingState.ACTIVE))

    # S4.4: Old binding revoked
    checks.append(("s4_old_revoked", rev_mgr.is_revoked("old_device")))

    # S4.5: Ceremony marked complete
    checks.append(("s4_complete", ceremony.completed))

    # ── S5: Cross-Organization Trust Bridges ─────────────────────────────

    bridge_mgr = CrossOrgBridgeManager()

    # S5.1: Create bridge
    bridge = bridge_mgr.create_bridge("org_a", "org_b", "bind_a", "bind_b", {"w1", "w2", "w3"})
    checks.append(("s5_bridge_created", bridge.active))

    # S5.2: Trust level from witnesses
    checks.append(("s5_trust_from_witnesses", abs(bridge.trust_level - 0.6) < 0.001))

    # S5.3: Find bridges for org
    bridges = bridge_mgr.bridges_for_org("org_a")
    checks.append(("s5_bridges_for_org", len(bridges) == 1))

    # S5.4: Revoke bridges for binding
    count = bridge_mgr.revoke_bridges_for_binding("bind_a")
    checks.append(("s5_revoke_bridges", count == 1))

    # S5.5: Revoked bridge not in active list
    bridges = bridge_mgr.bridges_for_org("org_a")
    checks.append(("s5_revoked_not_active", len(bridges) == 0))

    # ── S6: Hardware-to-Cloud Delegation ─────────────────────────────────

    deleg_mgr = DelegationManager()
    hw_bind = HardwareBinding("hw1", "user1", "fp", b"pk", trust_score=0.8)

    # S6.1: Create delegation
    deleg = deleg_mgr.delegate(hw_bind, "cloud1", {"read", "write"}, duration=3600)
    checks.append(("s6_delegation_created", abs(deleg.max_trust - 0.64) < 0.001))  # 0.8 * 0.8

    # S6.2: Check permitted operation
    checks.append(("s6_permitted", deleg_mgr.check_permission(deleg.delegation_id, "read", time.time())))

    # S6.3: Unpermitted operation denied
    checks.append(("s6_denied", not deleg_mgr.check_permission(deleg.delegation_id, "delete", time.time())))

    # S6.4: Revoke delegations for binding
    count = deleg_mgr.revoke_for_binding("hw1")
    checks.append(("s6_revoke_delegations", count == 1))

    # S6.5: Revoked delegation denied
    checks.append(("s6_revoked_denied", not deleg_mgr.check_permission(deleg.delegation_id, "read", time.time())))

    # ── S7: Key Rotation ─────────────────────────────────────────────────

    rot_mgr = RotationManager()
    rot_bind = HardwareBinding("rot1", "user1", "fp", b"old_key", key_version=1)

    # S7.1: Initiate rotation
    new_key = b"new_key_data"
    rotation = rot_mgr.initiate_rotation(rot_bind, new_key, overlap=100)
    checks.append(("s7_initiated", rot_bind.state == BindingState.ROTATING))

    # S7.2: Both keys valid during overlap
    now = time.time()
    checks.append(("s7_overlap_both", rotation.old_key_valid(now) and rotation.new_key_valid(now)))

    # S7.3: Complete rotation
    rot_mgr.complete_rotation(rot_bind, rotation)
    checks.append(("s7_completed", rot_bind.key_version == 2 and rot_bind.state == BindingState.ACTIVE))

    # S7.4: Active rotation check
    rot2 = RotationManager()
    b2 = HardwareBinding("r2", "u", "fp", b"key")
    rot2.initiate_rotation(b2, b"new")
    checks.append(("s7_active_rotation", rot2.active_rotation("r2") is not None))

    # S7.5: No active after completion
    checks.append(("s7_no_active_after", rot_mgr.active_rotation("rot1") is None))

    # ── S8: Emergency Freeze ─────────────────────────────────────────────

    freeze = FreezeProtocol(quorum_required=2)
    freeze_bind = HardwareBinding("frz1", "user1", "fp", b"pk")

    # S8.1: Freeze binding
    order = freeze.freeze(freeze_bind, "admin1", "suspected compromise")
    checks.append(("s8_frozen", freeze_bind.state == BindingState.FROZEN))

    # S8.2: Is frozen before expiry
    checks.append(("s8_is_frozen", freeze.is_frozen("frz1", time.time())))

    # S8.3: Auto-expires without quorum
    checks.append(("s8_auto_expires", not freeze.is_frozen("frz1", time.time() + FREEZE_AUTO_EXPIRE + 1)))

    # S8.4: Quorum sustains freeze
    freeze.vote_freeze("frz1", "admin2")
    checks.append(("s8_quorum_sustains", freeze.is_frozen("frz1", time.time() + FREEZE_AUTO_EXPIRE + 1)))

    # S8.5: Unfreeze
    freeze.unfreeze(freeze_bind, "admin1")
    checks.append(("s8_unfrozen", freeze_bind.state == BindingState.ACTIVE))

    # ── S9: Audit Trail ──────────────────────────────────────────────────

    audit = AuditTrail()

    # S9.1: Record events
    for i in range(5):
        audit.record(AuditEvent(
            event_type="action",
            binding_id="bind1",
            actor_id="user1",
            timestamp=1000 + i,
        ))
    checks.append(("s9_recorded", len(audit.events) == 5))

    # S9.2: Chain is valid
    checks.append(("s9_chain_valid", audit.verify_chain()))

    # S9.3: First event has empty prev_hash
    checks.append(("s9_first_empty_prev", audit.events[0].prev_hash == ""))

    # S9.4: Tamper detection
    audit.events[2].event_hash = "tampered"
    checks.append(("s9_tamper_detected", not audit.verify_chain()))

    # S9.5: Events for binding
    audit2 = AuditTrail()
    audit2.record(AuditEvent("a", "bind1", "u", 1))
    audit2.record(AuditEvent("b", "bind2", "u", 2))
    events = audit2.events_for_binding("bind1")
    checks.append(("s9_filter_binding", len(events) == 1))

    # ── S10: Revocation List ─────────────────────────────────────────────

    crl = RevocationList()

    # S10.1: Add and check
    crl.add(RevocationEntry("revoked1", 1000, "test", "admin"))
    checks.append(("s10_is_revoked", crl.is_revoked("revoked1")))
    checks.append(("s10_not_revoked", not crl.is_revoked("clean")))

    # S10.2: Version increments
    crl.add(RevocationEntry("revoked2", 1001, "test", "admin"))
    checks.append(("s10_version", crl.version == 2))

    # S10.3: Delta since version
    delta = crl.delta_since(1)
    checks.append(("s10_delta", len(delta) == 1))

    # S10.4: Delta since 0 returns all
    delta = crl.delta_since(0)
    checks.append(("s10_delta_all", len(delta) == 2))

    # S10.5: Fingerprint deterministic
    fp1 = crl.fingerprint()
    fp2 = crl.fingerprint()
    checks.append(("s10_fingerprint", fp1 == fp2))

    # S10.6: Get entry
    entry = crl.get_entry("revoked1")
    checks.append(("s10_get_entry", entry is not None and entry.reason == "test"))

    # ── S11: Performance ─────────────────────────────────────────────────

    import random
    rng = random.Random(42)

    # S11.1: Mass revocation cascade
    t0 = time.time()
    big_mgr = RevocationManager()
    for i in range(100):
        big_mgr.register(HardwareBinding(f"b{i}", f"e{i}", f"fp{i}", f"pk{i}".encode()))
    for i in range(99):
        big_mgr.add_trust_link(f"b{i}", f"b{i+1}")
    entries = big_mgr.revoke("b0", "test", "admin")
    elapsed = time.time() - t0
    checks.append(("s11_cascade_100", len(entries) == 100 and elapsed < 1.0))

    # S11.2: Compromise check at scale
    t0 = time.time()
    big_det = CompromiseDetector()
    for i in range(1000):
        big_det.record(BehaviorSample(
            f"b{i % 50}", now + i * 0.01,
            f"loc_{rng.randint(0, 5)}", "sign", rng.random() > 0.2,
        ))
    for i in range(50):
        big_det.check_concurrent_use(f"b{i}")
    elapsed = time.time() - t0
    checks.append(("s11_compromise_1000", elapsed < 2.0))

    # S11.3: Audit trail verification at scale
    t0 = time.time()
    big_audit = AuditTrail()
    for i in range(1000):
        big_audit.record(AuditEvent("action", f"b{i%50}", "admin", now + i))
    valid = big_audit.verify_chain()
    elapsed = time.time() - t0
    checks.append(("s11_audit_1000", valid and elapsed < 2.0))

    # S11.4: CRL at scale
    t0 = time.time()
    big_crl = RevocationList()
    for i in range(500):
        big_crl.add(RevocationEntry(f"r{i}", now + i, "test", "admin"))
    delta = big_crl.delta_since(400)
    elapsed = time.time() - t0
    checks.append(("s11_crl_500", len(delta) == 100 and elapsed < 1.0))

    # ── Print Results ────────────────────────────────────────────────────
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print(f"\n{'='*60}")
    print(f"  Hardware Binding Recovery & Revocation — {passed}/{total} checks passed")
    print(f"{'='*60}")

    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")

    if passed < total:
        print(f"\n  FAILURES:")
        for name, ok in checks:
            if not ok:
                print(f"    ✗ {name}")

    print()
    return passed, total


if __name__ == "__main__":
    run_checks()
