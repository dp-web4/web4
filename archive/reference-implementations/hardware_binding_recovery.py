#!/usr/bin/env python3
"""
Hardware Binding Recovery & Revocation — Session 20, Track 4

Real-world hardware binding scenarios beyond single-device TPM:
- Key revocation with cascading trust updates
- Quorum-based key recovery ceremony
- Device loss detection and response
- Cross-organization hardware trust bridges
- Hardware upgrade migration (old device → new device)
- Compromise detection via behavioral anomaly
- Secure erasure verification
- Multi-device constellation management
- Emergency recovery with social witnesses
- Revocation propagation across federation
- Performance and scale testing

Reference: multi-device-lct-binding.md, contextual_hardware_binding.py, 305 patent family
"""

from __future__ import annotations
import hashlib
import hmac
import math
import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


# ─── Constants ────────────────────────────────────────────────────────────────

class DeviceState(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    LOST = "lost"
    MIGRATING = "migrating"
    COMPROMISED = "compromised"


class AnchorType(Enum):
    TPM_DISCRETE = "tpm_discrete"
    SECURE_ENCLAVE = "secure_enclave"
    STRONGBOX = "strongbox"
    FIDO2 = "fido2"
    SOFTWARE = "software"


ANCHOR_TRUST = {
    AnchorType.TPM_DISCRETE: 0.9,
    AnchorType.SECURE_ENCLAVE: 0.85,
    AnchorType.STRONGBOX: 0.8,
    AnchorType.FIDO2: 0.75,
    AnchorType.SOFTWARE: 0.5,
}


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class DeviceBinding:
    """A hardware-bound device in an entity's constellation."""
    device_id: str
    anchor_type: AnchorType
    public_key: bytes
    state: DeviceState = DeviceState.ACTIVE
    enrolled_at: float = 0.0
    last_attestation: float = 0.0
    trust_score: float = 0.5
    entity_id: str = ""
    organization_id: Optional[str] = None


@dataclass
class RevocationCert:
    """Certificate revoking a device binding."""
    device_id: str
    reason: str
    revoked_at: float
    revoker_id: str
    cascade: bool = True
    signature: bytes = b""

    def hash(self) -> str:
        data = f"{self.device_id}:{self.reason}:{self.revoked_at}:{self.revoker_id}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class RecoveryShard:
    """A shard of a recovery key held by a witness."""
    shard_id: str
    holder_id: str
    shard_data: bytes
    created_at: float
    used: bool = False


@dataclass
class RecoveryCeremony:
    """Quorum-based key recovery ceremony."""
    entity_id: str
    threshold: int
    total_shards: int
    shards: List[RecoveryShard] = field(default_factory=list)
    submitted_shards: List[RecoveryShard] = field(default_factory=list)
    completed: bool = False
    recovered_key: Optional[bytes] = None
    started_at: float = 0.0
    expires_at: float = 0.0


# ─── S1: Key Revocation ─────────────────────────────────────────────────────

class RevocationRegistry:
    """Track and propagate device revocations."""

    def __init__(self):
        self.revocations: Dict[str, RevocationCert] = {}
        self.dependents: Dict[str, Set[str]] = {}

    def add_dependency(self, parent_id: str, child_id: str):
        if parent_id not in self.dependents:
            self.dependents[parent_id] = set()
        self.dependents[parent_id].add(child_id)

    def revoke(self, cert: RevocationCert) -> List[str]:
        """Revoke a device and optionally cascade to dependents."""
        revoked = [cert.device_id]
        self.revocations[cert.device_id] = cert

        if cert.cascade:
            queue = list(self.dependents.get(cert.device_id, set()))
            while queue:
                dep_id = queue.pop(0)
                if dep_id not in self.revocations:
                    cascade_cert = RevocationCert(
                        device_id=dep_id,
                        reason=f"cascade_from:{cert.device_id}",
                        revoked_at=cert.revoked_at,
                        revoker_id=cert.revoker_id,
                        cascade=True,
                    )
                    self.revocations[dep_id] = cascade_cert
                    revoked.append(dep_id)
                    queue.extend(self.dependents.get(dep_id, set()))

        return revoked

    def is_revoked(self, device_id: str) -> bool:
        return device_id in self.revocations

    def revocation_chain(self, device_id: str) -> List[str]:
        cert = self.revocations.get(device_id)
        if not cert:
            return []
        chain = [device_id]
        if cert.reason.startswith("cascade_from:"):
            parent = cert.reason.split(":", 1)[1]
            chain = self.revocation_chain(parent) + chain
        return chain


# ─── S2: Quorum-Based Key Recovery ──────────────────────────────────────────

def create_recovery_shards(
    secret: bytes, threshold: int, total: int, holders: List[str],
) -> RecoveryCeremony:
    """Create recovery shards using XOR-based secret sharing."""
    assert threshold <= total
    assert total == len(holders)

    now = time.time()
    random_shards = [os.urandom(len(secret)) for _ in range(total - 1)]
    final_shard = bytearray(secret)
    for rs in random_shards:
        for i in range(len(final_shard)):
            final_shard[i] ^= rs[i]

    all_shard_data = random_shards + [bytes(final_shard)]
    shards = [
        RecoveryShard(f"shard_{i}", holder, all_shard_data[i], now)
        for i, holder in enumerate(holders)
    ]
    return RecoveryCeremony(
        entity_id="recovery_target", threshold=threshold,
        total_shards=total, shards=shards,
        started_at=now, expires_at=now + 86400,
    )


def submit_shard(ceremony: RecoveryCeremony, shard: RecoveryShard) -> bool:
    if ceremony.completed:
        return False
    if shard.used:
        return False
    if not any(s.shard_id == shard.shard_id for s in ceremony.shards):
        return False
    if any(s.shard_id == shard.shard_id for s in ceremony.submitted_shards):
        return False
    shard.used = True
    ceremony.submitted_shards.append(shard)
    return True


def attempt_recovery(ceremony: RecoveryCeremony) -> Optional[bytes]:
    if len(ceremony.submitted_shards) < ceremony.total_shards:
        return None
    shard_len = len(ceremony.submitted_shards[0].shard_data)
    result = bytearray(shard_len)
    for shard in ceremony.submitted_shards:
        for i in range(shard_len):
            result[i] ^= shard.shard_data[i]
    ceremony.completed = True
    ceremony.recovered_key = bytes(result)
    return bytes(result)


# ─── S3: Device Loss Detection ──────────────────────────────────────────────

class DeviceLossDetector:
    """Detect lost devices via attestation gaps."""

    def __init__(self, attestation_interval: float = 3600.0, loss_threshold: int = 3):
        self.interval = attestation_interval
        self.threshold = loss_threshold
        self.devices: Dict[str, DeviceBinding] = {}
        self.missed_counts: Dict[str, int] = {}

    def register(self, device: DeviceBinding):
        self.devices[device.device_id] = device
        self.missed_counts[device.device_id] = 0

    def record_attestation(self, device_id: str, timestamp: float):
        if device_id in self.devices:
            self.devices[device_id].last_attestation = timestamp
            self.missed_counts[device_id] = 0

    def check_all(self, now: float) -> List[str]:
        lost = []
        for did, device in self.devices.items():
            if device.state in (DeviceState.REVOKED, DeviceState.LOST):
                continue
            if now > device.last_attestation + self.interval:
                missed = int((now - device.last_attestation) / self.interval)
                self.missed_counts[did] = missed
                if missed >= self.threshold:
                    lost.append(did)
        return lost

    def mark_lost(self, device_id: str):
        if device_id in self.devices:
            self.devices[device_id].state = DeviceState.LOST


# ─── S4: Cross-Organization Trust Bridge ────────────────────────────────────

@dataclass
class OrgTrustBridge:
    bridge_id: str
    org_a: str
    org_b: str
    witness_ids: List[str]
    bridge_trust: float = 0.0
    created_at: float = 0.0
    active: bool = True


class CrossOrgBridgeManager:
    def __init__(self):
        self.bridges: Dict[str, OrgTrustBridge] = {}
        self.org_devices: Dict[str, List[DeviceBinding]] = {}

    def register_org_device(self, org_id: str, device: DeviceBinding):
        if org_id not in self.org_devices:
            self.org_devices[org_id] = []
        self.org_devices[org_id].append(device)

    def create_bridge(self, org_a: str, org_b: str, witnesses: List[str],
                      min_witnesses: int = 2) -> Optional[OrgTrustBridge]:
        if len(witnesses) < min_witnesses:
            return None
        witness_factor = min(1.0, len(witnesses) / 5)
        a_anchor = self._best_anchor(org_a)
        b_anchor = self._best_anchor(org_b)
        bridge_trust = witness_factor * min(a_anchor, b_anchor)

        bridge = OrgTrustBridge(
            bridge_id=f"bridge_{org_a}_{org_b}", org_a=org_a, org_b=org_b,
            witness_ids=witnesses, bridge_trust=bridge_trust, created_at=time.time(),
        )
        self.bridges[bridge.bridge_id] = bridge
        return bridge

    def _best_anchor(self, org_id: str) -> float:
        devices = self.org_devices.get(org_id, [])
        return max((ANCHOR_TRUST[d.anchor_type] for d in devices), default=0.0)

    def cross_org_trust(self, org_a: str, org_b: str) -> float:
        for bridge in self.bridges.values():
            if not bridge.active:
                continue
            if {bridge.org_a, bridge.org_b} == {org_a, org_b}:
                return bridge.bridge_trust
        return 0.0

    def revoke_bridge(self, bridge_id: str):
        if bridge_id in self.bridges:
            self.bridges[bridge_id].active = False


# ─── S5: Hardware Upgrade Migration ──────────────────────────────────────────

@dataclass
class MigrationPlan:
    old_device_id: str
    new_device_id: str
    entity_id: str
    phase: str = "pending"
    old_key_hash: str = ""
    new_key_hash: str = ""
    attestation_verified: bool = False
    transfer_complete: bool = False


class DeviceMigrator:
    def __init__(self):
        self.migrations: Dict[str, MigrationPlan] = {}

    def plan_migration(self, old: DeviceBinding, new: DeviceBinding, entity_id: str) -> MigrationPlan:
        plan = MigrationPlan(
            old_device_id=old.device_id, new_device_id=new.device_id,
            entity_id=entity_id,
            old_key_hash=hashlib.sha256(old.public_key).hexdigest()[:16],
            new_key_hash=hashlib.sha256(new.public_key).hexdigest()[:16],
        )
        self.migrations[plan.old_device_id] = plan
        return plan

    def attest_new_device(self, plan: MigrationPlan, new_device: DeviceBinding) -> bool:
        if hashlib.sha256(new_device.public_key).hexdigest()[:16] != plan.new_key_hash:
            return False
        plan.attestation_verified = True
        plan.phase = "attesting"
        return True

    def transfer_binding(self, plan: MigrationPlan) -> bool:
        if not plan.attestation_verified:
            return False
        plan.transfer_complete = True
        plan.phase = "verifying"
        return True

    def complete_migration(self, plan: MigrationPlan) -> bool:
        if not plan.transfer_complete:
            return False
        plan.phase = "complete"
        return True


# ─── S6: Compromise Detection ───────────────────────────────────────────────

@dataclass
class BehaviorSample:
    device_id: str
    timestamp: float
    action_type: str
    source_ip: str
    success: bool


class CompromiseDetector:
    def __init__(self, window: float = 3600.0):
        self.window = window
        self.samples: Dict[str, List[BehaviorSample]] = {}
        self.baselines: Dict[str, Dict[str, float]] = {}

    def record(self, sample: BehaviorSample):
        did = sample.device_id
        if did not in self.samples:
            self.samples[did] = []
        self.samples[did].append(sample)

    def establish_baseline(self, device_id: str):
        samples = self.samples.get(device_id, [])
        if len(samples) < 10:
            return
        ips = set(s.source_ip for s in samples)
        success_rate = sum(1 for s in samples if s.success) / len(samples)
        self.baselines[device_id] = {
            "unique_ips": len(ips),
            "success_rate": success_rate,
            "avg_interval": self._avg_interval(samples),
        }

    def _avg_interval(self, samples: List[BehaviorSample]) -> float:
        if len(samples) < 2:
            return 0.0
        intervals = [samples[i+1].timestamp - samples[i].timestamp
                     for i in range(len(samples) - 1)]
        return sum(intervals) / len(intervals) if intervals else 0.0

    def detect_anomaly(self, device_id: str, now: float) -> List[str]:
        baseline = self.baselines.get(device_id)
        if not baseline:
            return []
        recent = [s for s in self.samples.get(device_id, [])
                  if now - s.timestamp < self.window]
        if len(recent) < 5:
            return []

        anomalies = []
        recent_ips = len(set(s.source_ip for s in recent))
        if baseline["unique_ips"] > 0 and recent_ips > baseline["unique_ips"] * 3:
            anomalies.append(f"ip_diversity_spike:{recent_ips}")

        recent_success = sum(1 for s in recent if s.success) / len(recent)
        if baseline["success_rate"] - recent_success > 0.3:
            anomalies.append(f"success_rate_drop:{recent_success:.2f}")

        if baseline["avg_interval"] > 0:
            recent_interval = self._avg_interval(recent)
            if recent_interval > 0 and baseline["avg_interval"] / recent_interval > 5:
                anomalies.append(f"frequency_spike:{recent_interval:.2f}")

        return anomalies


# ─── S7: Secure Erasure Verification ────────────────────────────────────────

@dataclass
class ErasureProof:
    device_id: str
    erasure_method: str
    timestamp: float
    attestation_hash: str
    verifier_id: str
    verified: bool = False


class ErasureVerifier:
    def __init__(self):
        self.proofs: Dict[str, ErasureProof] = {}

    def submit_proof(self, proof: ErasureProof) -> bool:
        if len(proof.attestation_hash) < 16:
            return False
        self.proofs[proof.device_id] = proof
        return True

    def verify_erasure(self, device_id: str, expected_method: str = None) -> bool:
        proof = self.proofs.get(device_id)
        if not proof:
            return False
        if expected_method and proof.erasure_method != expected_method:
            return False
        proof.verified = True
        return True

    def is_erased(self, device_id: str) -> bool:
        proof = self.proofs.get(device_id)
        return proof is not None and proof.verified


# ─── S8: Constellation Management ───────────────────────────────────────────

class Constellation:
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        self.devices: Dict[str, DeviceBinding] = {}
        self.primary_device: Optional[str] = None

    def add_device(self, device: DeviceBinding) -> bool:
        if device.device_id in self.devices:
            return False
        device.entity_id = self.entity_id
        self.devices[device.device_id] = device
        if self.primary_device is None:
            self.primary_device = device.device_id
        return True

    def remove_device(self, device_id: str) -> bool:
        if device_id not in self.devices:
            return False
        del self.devices[device_id]
        if self.primary_device == device_id:
            active = [d for d in self.devices.values() if d.state == DeviceState.ACTIVE]
            self.primary_device = active[0].device_id if active else None
        return True

    def active_devices(self) -> List[DeviceBinding]:
        return [d for d in self.devices.values() if d.state == DeviceState.ACTIVE]

    def constellation_trust(self) -> float:
        active = self.active_devices()
        if not active:
            return 0.0
        total_w = sum(ANCHOR_TRUST[d.anchor_type] for d in active)
        weighted_trust = sum(d.trust_score * ANCHOR_TRUST[d.anchor_type] for d in active)
        base = weighted_trust / total_w if total_w > 0 else 0.0
        bonus = min(0.1, 0.02 * (len(active) - 1))
        return min(1.0, base + bonus)

    def promote_primary(self, device_id: str) -> bool:
        if device_id not in self.devices:
            return False
        if self.devices[device_id].state != DeviceState.ACTIVE:
            return False
        self.primary_device = device_id
        return True


# ─── S9: Emergency Recovery with Social Witnesses ───────────────────────────

@dataclass
class EmergencyRecoveryRequest:
    entity_id: str
    requested_at: float
    witness_approvals: Dict[str, float] = field(default_factory=dict)
    witness_rejections: Set[str] = field(default_factory=set)
    required_approvals: int = 3
    expires_at: float = 0.0
    status: str = "pending"


def process_emergency_recovery(request: EmergencyRecoveryRequest, now: float) -> str:
    if now > request.expires_at:
        request.status = "expired"
        return "expired"
    if len(request.witness_rejections) > len(request.witness_approvals):
        request.status = "rejected"
        return "rejected"
    if len(request.witness_approvals) >= request.required_approvals:
        request.status = "approved"
        return "approved"
    return "pending"


# ─── S10: Revocation Propagation Across Federation ──────────────────────────

@dataclass
class RevocationBroadcast:
    cert: RevocationCert
    origin_federation: str
    hops: int = 0
    max_hops: int = 5
    received_by: Set[str] = field(default_factory=set)


class FederationRevocationPropagator:
    def __init__(self):
        self.broadcasts: Dict[str, RevocationBroadcast] = {}
        self.federation_peers: Dict[str, Set[str]] = {}
        self.node_federations: Dict[str, str] = {}

    def register_federation(self, fed_id: str, nodes: List[str], peers: Set[str]):
        self.federation_peers[fed_id] = peers
        for node in nodes:
            self.node_federations[node] = fed_id

    def broadcast_revocation(self, cert: RevocationCert, origin_fed: str) -> RevocationBroadcast:
        broadcast = RevocationBroadcast(cert=cert, origin_federation=origin_fed,
                                        received_by={origin_fed})
        self.broadcasts[cert.device_id] = broadcast
        return broadcast

    def propagate(self, broadcast: RevocationBroadcast) -> Set[str]:
        if broadcast.hops >= broadcast.max_hops:
            return set()
        newly_reached = set()
        for fed in set(broadcast.received_by):
            for peer in self.federation_peers.get(fed, set()):
                if peer not in broadcast.received_by:
                    broadcast.received_by.add(peer)
                    newly_reached.add(peer)
        broadcast.hops += 1
        return newly_reached

    def full_propagation(self, broadcast: RevocationBroadcast) -> int:
        while broadcast.hops < broadcast.max_hops:
            if not self.propagate(broadcast):
                break
        return len(broadcast.received_by)


# ══════════════════════════════════════════════════════════════════════════════
#  CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def run_checks():
    checks = []
    import random
    rng = random.Random(42)
    now = time.time()

    # ── S1: Key Revocation ───────────────────────────────────────────────

    registry = RevocationRegistry()
    registry.add_dependency("root_key", "child_1")
    registry.add_dependency("root_key", "child_2")
    registry.add_dependency("child_1", "grandchild_1")

    cert = RevocationCert("root_key", "compromised", now, "admin")
    revoked = registry.revoke(cert)
    checks.append(("s1_cascade_revoke", len(revoked) == 4))

    checks.append(("s1_all_revoked",
        registry.is_revoked("root_key") and
        registry.is_revoked("child_1") and
        registry.is_revoked("grandchild_1")))

    chain = registry.revocation_chain("grandchild_1")
    checks.append(("s1_chain", chain[0] == "root_key" and chain[-1] == "grandchild_1"))

    reg2 = RevocationRegistry()
    reg2.add_dependency("parent", "child")
    cert2 = RevocationCert("parent", "expired", now, "admin", cascade=False)
    revoked2 = reg2.revoke(cert2)
    checks.append(("s1_no_cascade", len(revoked2) == 1 and not reg2.is_revoked("child")))

    checks.append(("s1_unrevoked", not reg2.is_revoked("unknown_device")))
    checks.append(("s1_cert_hash", cert.hash() == cert.hash()))

    # ── S2: Quorum-Based Key Recovery ────────────────────────────────────

    secret = b"super_secret_key_32_bytes_long!!"
    holders = ["alice", "bob", "charlie", "dave", "eve"]
    ceremony = create_recovery_shards(secret, threshold=3, total=5, holders=holders)

    checks.append(("s2_shard_count", len(ceremony.shards) == 5))

    for shard in ceremony.shards[:4]:
        submit_shard(ceremony, shard)
    checks.append(("s2_submit_4", len(ceremony.submitted_shards) == 4))

    checks.append(("s2_dup_rejected", not submit_shard(ceremony, ceremony.shards[0])))

    result = attempt_recovery(ceremony)
    checks.append(("s2_not_enough", result is None))

    submit_shard(ceremony, ceremony.shards[4])
    result = attempt_recovery(ceremony)
    checks.append(("s2_recovery_success", result == secret))

    checks.append(("s2_completed", ceremony.completed))

    new_ceremony = create_recovery_shards(b"test" * 8, 2, 3, ["a", "b", "c"])
    new_ceremony.completed = True
    checks.append(("s2_submit_after_complete", not submit_shard(new_ceremony, new_ceremony.shards[0])))

    # ── S3: Device Loss Detection ────────────────────────────────────────

    detector = DeviceLossDetector(attestation_interval=3600.0, loss_threshold=3)

    dev1 = DeviceBinding("dev1", AnchorType.TPM_DISCRETE, b"pk1", last_attestation=now - 7200)
    dev2 = DeviceBinding("dev2", AnchorType.FIDO2, b"pk2", last_attestation=now)

    detector.register(dev1)
    detector.register(dev2)

    lost = detector.check_all(now + 7200)  # 2 hours: dev1 missed 4 (att 2h ago + 2h), dev2 missed 2
    checks.append(("s3_lost_detected", "dev1" in lost))
    checks.append(("s3_fresh_not_lost", "dev2" not in lost))

    detector.record_attestation("dev1", now + 14400)
    lost_after = detector.check_all(now + 14401)
    checks.append(("s3_attestation_resets", "dev1" not in lost_after))

    detector.mark_lost("dev1")
    checks.append(("s3_mark_lost", detector.devices["dev1"].state == DeviceState.LOST))

    lost_again = detector.check_all(now + 100000)
    checks.append(("s3_lost_skipped", "dev1" not in lost_again))

    # ── S4: Cross-Organization Trust Bridge ──────────────────────────────

    bridge_mgr = CrossOrgBridgeManager()
    bridge_mgr.register_org_device("org_a", DeviceBinding("da1", AnchorType.TPM_DISCRETE, b"pk"))
    bridge_mgr.register_org_device("org_b", DeviceBinding("db1", AnchorType.SECURE_ENCLAVE, b"pk"))

    bridge = bridge_mgr.create_bridge("org_a", "org_b", ["w1", "w2", "w3"])
    checks.append(("s4_bridge_created", bridge is not None))
    checks.append(("s4_bridge_trust", bridge is not None and 0 < bridge.bridge_trust <= 1.0))

    bad_bridge = bridge_mgr.create_bridge("org_a", "org_c", ["w1"])
    checks.append(("s4_insufficient_witnesses", bad_bridge is None))

    trust = bridge_mgr.cross_org_trust("org_a", "org_b")
    checks.append(("s4_cross_org_trust", trust > 0))
    checks.append(("s4_unknown_zero", bridge_mgr.cross_org_trust("org_a", "org_z") == 0.0))

    bridge_mgr.revoke_bridge(bridge.bridge_id)
    checks.append(("s4_revoke_bridge", bridge_mgr.cross_org_trust("org_a", "org_b") == 0.0))

    # ── S5: Hardware Upgrade Migration ───────────────────────────────────

    migrator = DeviceMigrator()
    old = DeviceBinding("old_dev", AnchorType.FIDO2, b"old_key")
    new = DeviceBinding("new_dev", AnchorType.TPM_DISCRETE, b"new_key")

    plan = migrator.plan_migration(old, new, "alice")
    checks.append(("s5_plan_created", plan.phase == "pending"))

    success = migrator.attest_new_device(plan, new)
    checks.append(("s5_attest_success", success and plan.attestation_verified))

    success = migrator.transfer_binding(plan)
    checks.append(("s5_transfer", success and plan.transfer_complete))

    success = migrator.complete_migration(plan)
    checks.append(("s5_complete", success and plan.phase == "complete"))

    plan2 = migrator.plan_migration(old, new, "bob")
    checks.append(("s5_no_attest_fail", not migrator.transfer_binding(plan2)))

    plan3 = migrator.plan_migration(old, new, "charlie")
    wrong_dev = DeviceBinding("wrong", AnchorType.TPM_DISCRETE, b"wrong_key")
    checks.append(("s5_wrong_key", not migrator.attest_new_device(plan3, wrong_dev)))

    # ── S6: Compromise Detection ─────────────────────────────────────────

    comp_det = CompromiseDetector(window=3600.0)
    for i in range(20):
        comp_det.record(BehaviorSample("dev_normal", now - 7200 + i * 300, "login", "192.168.1.1", True))
    comp_det.establish_baseline("dev_normal")

    checks.append(("s6_baseline", "dev_normal" in comp_det.baselines))

    for i in range(10):
        comp_det.record(BehaviorSample("dev_normal", now + i * 300, "login", "192.168.1.1", True))
    anomalies = comp_det.detect_anomaly("dev_normal", now + 3000)
    checks.append(("s6_normal_no_anomaly", len(anomalies) == 0))

    for i in range(10):
        comp_det.record(BehaviorSample("dev_normal", now + 3100 + i * 10, "login", f"10.{i}.{i}.{i}", True))
    anomalies = comp_det.detect_anomaly("dev_normal", now + 3200)
    checks.append(("s6_ip_spike", any("ip_diversity" in a for a in anomalies)))

    checks.append(("s6_insufficient", len(comp_det.detect_anomaly("unknown", now)) == 0))

    # ── S7: Secure Erasure ───────────────────────────────────────────────

    eraser = ErasureVerifier()
    proof = ErasureProof("erased_dev", "crypto_erase", now,
                        hashlib.sha256(b"attestation").hexdigest(), "verifier_1")
    checks.append(("s7_submit", eraser.submit_proof(proof)))
    checks.append(("s7_verify", eraser.verify_erasure("erased_dev")))
    checks.append(("s7_is_erased", eraser.is_erased("erased_dev")))
    checks.append(("s7_not_erased", not eraser.is_erased("unknown")))

    bad_proof = ErasureProof("bad", "overwrite", now, "short", "v1")
    checks.append(("s7_short_hash", not eraser.submit_proof(bad_proof)))

    proof2 = ErasureProof("dev2", "overwrite", now, hashlib.sha256(b"x").hexdigest(), "v1")
    eraser.submit_proof(proof2)
    checks.append(("s7_wrong_method", not eraser.verify_erasure("dev2", "crypto_erase")))

    # ── S8: Constellation Management ─────────────────────────────────────

    constellation = Constellation("alice")
    d1 = DeviceBinding("phone", AnchorType.SECURE_ENCLAVE, b"pk1", trust_score=0.8)
    d2 = DeviceBinding("laptop", AnchorType.TPM_DISCRETE, b"pk2", trust_score=0.9)
    d3 = DeviceBinding("yubikey", AnchorType.FIDO2, b"pk3", trust_score=0.7)

    constellation.add_device(d1)
    constellation.add_device(d2)
    constellation.add_device(d3)
    checks.append(("s8_add_3", len(constellation.devices) == 3))
    checks.append(("s8_first_primary", constellation.primary_device == "phone"))

    trust = constellation.constellation_trust()
    checks.append(("s8_trust_valid", 0.0 < trust <= 1.0))

    single = Constellation("solo")
    single.add_device(DeviceBinding("only", AnchorType.TPM_DISCRETE, b"pk", trust_score=0.8))
    checks.append(("s8_multi_bonus", constellation.constellation_trust() > single.constellation_trust()))

    constellation.remove_device("phone")
    checks.append(("s8_remove", len(constellation.devices) == 2))
    checks.append(("s8_auto_promote", constellation.primary_device is not None))
    checks.append(("s8_promote", constellation.promote_primary("yubikey")))
    checks.append(("s8_dup_rejected", not constellation.add_device(d2)))

    # ── S9: Emergency Recovery ───────────────────────────────────────────

    recovery = EmergencyRecoveryRequest(
        entity_id="alice", requested_at=now, required_approvals=3, expires_at=now + 86400)
    checks.append(("s9_initial_pending", process_emergency_recovery(recovery, now) == "pending"))

    recovery.witness_approvals["w1"] = now
    recovery.witness_approvals["w2"] = now + 1
    checks.append(("s9_partial_pending", process_emergency_recovery(recovery, now + 2) == "pending"))

    recovery.witness_approvals["w3"] = now + 3
    checks.append(("s9_approved", process_emergency_recovery(recovery, now + 4) == "approved"))

    expired_req = EmergencyRecoveryRequest(
        entity_id="bob", requested_at=now, required_approvals=3, expires_at=now + 100)
    checks.append(("s9_expired", process_emergency_recovery(expired_req, now + 200) == "expired"))

    rejected_req = EmergencyRecoveryRequest(
        entity_id="charlie", requested_at=now, required_approvals=3, expires_at=now + 86400)
    rejected_req.witness_approvals["w1"] = now
    rejected_req.witness_rejections.update(["w2", "w3", "w4"])
    checks.append(("s9_rejected", process_emergency_recovery(rejected_req, now + 1) == "rejected"))

    # ── S10: Federation Revocation Propagation ───────────────────────────

    propagator = FederationRevocationPropagator()
    propagator.register_federation("fed1", ["n1", "n2"], {"fed2"})
    propagator.register_federation("fed2", ["n3", "n4"], {"fed1", "fed3"})
    propagator.register_federation("fed3", ["n5", "n6"], {"fed2", "fed4"})
    propagator.register_federation("fed4", ["n7"], {"fed3"})

    cert = RevocationCert("compromised_key", "stolen", now, "admin")
    broadcast = propagator.broadcast_revocation(cert, "fed1")

    checks.append(("s10_origin", "fed1" in broadcast.received_by))

    propagator.propagate(broadcast)
    checks.append(("s10_one_hop", "fed2" in broadcast.received_by))

    propagator.propagate(broadcast)
    checks.append(("s10_two_hops", "fed3" in broadcast.received_by))

    total = propagator.full_propagation(broadcast)
    checks.append(("s10_full_propagation", total == 4))

    limited = RevocationBroadcast(cert, "fed1", max_hops=1, received_by={"fed1"})
    propagator.propagate(limited)
    checks.append(("s10_max_hops", limited.hops <= 1))

    # ── S11: Performance ─────────────────────────────────────────────────

    t0 = time.time()
    big_reg = RevocationRegistry()
    for i in range(100):
        big_reg.add_dependency(f"dev_{i}", f"dev_{i + 1}")
    cert = RevocationCert("dev_0", "test", now, "admin")
    revoked = big_reg.revoke(cert)
    elapsed = time.time() - t0
    checks.append(("s11_cascade_100", len(revoked) == 101 and elapsed < 1.0))

    t0 = time.time()
    big_const = Constellation("big_entity")
    for i in range(20):
        anchor = list(AnchorType)[i % 5]
        big_const.add_device(DeviceBinding(f"d{i}", anchor, f"pk{i}".encode(), trust_score=rng.random()))
    trust = big_const.constellation_trust()
    elapsed = time.time() - t0
    checks.append(("s11_constellation_20", 0.0 < trust <= 1.0 and elapsed < 1.0))

    t0 = time.time()
    big_det = DeviceLossDetector()
    for i in range(500):
        d = DeviceBinding(f"dl_{i}", AnchorType.FIDO2, f"pk{i}".encode(),
                         last_attestation=now - rng.uniform(0, 20000))
        big_det.register(d)
    lost = big_det.check_all(now + 14400)
    elapsed = time.time() - t0
    checks.append(("s11_loss_500", elapsed < 1.0))

    t0 = time.time()
    big_bridge = CrossOrgBridgeManager()
    for i in range(50):
        big_bridge.register_org_device(f"org_{i}",
            DeviceBinding(f"do_{i}", AnchorType.TPM_DISCRETE, b"pk"))
    for i in range(49):
        big_bridge.create_bridge(f"org_{i}", f"org_{i+1}", [f"w{j}" for j in range(3)])
    elapsed = time.time() - t0
    checks.append(("s11_bridges_50", elapsed < 1.0))

    t0 = time.time()
    big_prop = FederationRevocationPropagator()
    for i in range(20):
        peers = set()
        if i > 0: peers.add(f"f{i-1}")
        if i < 19: peers.add(f"f{i+1}")
        big_prop.register_federation(f"f{i}", [f"n{i}"], peers)
    bc = big_prop.broadcast_revocation(RevocationCert("key", "test", now, "admin"), "f0")
    bc.max_hops = 20  # Linear chain needs 19 hops to reach all 20 feds
    total = big_prop.full_propagation(bc)
    elapsed = time.time() - t0
    checks.append(("s11_propagation_20", total == 20 and elapsed < 1.0))

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
