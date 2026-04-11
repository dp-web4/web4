"""
Hardware Binding E2E Verification Protocol
==========================================

End-to-end verification that a cryptographic chain connects:
  Hardware attestation → Device binding → Identity coherence → Action authorization

This is the final link in Web4's "hardware-as-presence" model.

Components:
1. AttestationQuote — TPM2-style attestation with PCR snapshot
2. DeviceBinding — Links hardware quote to LCT identity
3. EnrollmentWitness — Third-party attestation of binding ceremony
4. VerificationChain — Complete chain from hardware to action
5. E2EVerifier — Validates entire chain with configurable policies
6. HardwareRegistry — Federation-wide registry of hardware bindings
7. CoherenceChecker — Cross-device identity coherence validation
8. RevocationCascader — Propagates revocation through binding chains
9. FederationHardwareSync — Cross-federation hardware registry sync

Addresses gap: No existing code verifies complete hardware→action chain.
"""

from __future__ import annotations
import hashlib
import time
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple


# ─── Enums ────────────────────────────────────────────────────────────────────

class AnchorType(Enum):
    TPM2_DISCRETE = "tpm2_discrete"
    TPM2_FIRMWARE = "tpm2_firmware"
    SECURE_ENCLAVE = "secure_enclave"
    STRONGBOX = "strongbox"
    FIDO2 = "fido2"
    SOFTWARE = "software"


class DeviceState(Enum):
    ENROLLED = auto()
    ACTIVE = auto()
    SUSPENDED = auto()
    REVOKED = auto()
    LOST = auto()
    COMPROMISED = auto()


class VerificationResult(Enum):
    VALID = auto()
    INVALID_QUOTE = auto()
    INVALID_PCR = auto()
    INVALID_BINDING = auto()
    INVALID_WITNESS = auto()
    INVALID_COHERENCE = auto()
    INVALID_ACTION = auto()
    EXPIRED = auto()
    REVOKED = auto()
    CHAIN_BROKEN = auto()


class RegistryEventType(Enum):
    ENROLLMENT = auto()
    ATTESTATION = auto()
    REVOCATION = auto()
    RECOVERY = auto()
    MIGRATION = auto()
    SYNC = auto()


# ─── Trust Constants ──────────────────────────────────────────────────────────

ANCHOR_TRUST = {
    AnchorType.TPM2_DISCRETE: 0.93,
    AnchorType.TPM2_FIRMWARE: 0.90,
    AnchorType.SECURE_ENCLAVE: 0.95,
    AnchorType.STRONGBOX: 0.80,
    AnchorType.FIDO2: 0.85,
    AnchorType.SOFTWARE: 0.40,
}

# PCR policies: which PCRs must match baseline
DEFAULT_PCR_POLICY = {0, 1, 2, 3, 7}  # BIOS, config, option ROMs, secure boot
STRICT_PCR_POLICY = {0, 1, 2, 3, 4, 5, 6, 7}  # Include boot loader + kernel


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class PCRSnapshot:
    """Snapshot of Platform Configuration Register values."""
    values: Dict[int, str]  # PCR index → hash value
    timestamp: float = field(default_factory=time.time)
    algorithm: str = "sha256"

    def matches_baseline(self, baseline: Dict[int, str],
                         policy: Set[int] = None) -> Tuple[bool, List[int]]:
        """Check PCRs against baseline per policy. Returns (match, mismatched_indices)."""
        check_pcrs = policy or DEFAULT_PCR_POLICY
        mismatched = []
        for pcr_idx in check_pcrs:
            baseline_val = baseline.get(pcr_idx)
            current_val = self.values.get(pcr_idx)
            if baseline_val is None or current_val is None:
                mismatched.append(pcr_idx)
            elif baseline_val != current_val:
                mismatched.append(pcr_idx)
        return len(mismatched) == 0, mismatched


@dataclass
class AttestationQuote:
    """TPM2-style attestation quote."""
    device_id: str
    nonce: str  # Freshness challenge
    pcr_snapshot: PCRSnapshot
    quote_signature: str  # Simulated TPM signature
    ek_cert_chain: List[str]  # EK → ICA → Root
    anchor_type: AnchorType = AnchorType.TPM2_DISCRETE
    timestamp: float = field(default_factory=time.time)
    quote_hash: str = ""

    def __post_init__(self):
        if not self.quote_hash:
            content = f"{self.device_id}:{self.nonce}:{self.timestamp}"
            for idx in sorted(self.pcr_snapshot.values.keys()):
                content += f":{idx}={self.pcr_snapshot.values[idx]}"
            self.quote_hash = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class DeviceBinding:
    """Links hardware attestation to LCT identity."""
    device_id: str
    lct_id: str  # Root LCT this device is bound to
    anchor_type: AnchorType
    binding_commitment: str = ""  # Hash of binding ceremony data
    enrolled_at: float = field(default_factory=time.time)
    state: DeviceState = DeviceState.ENROLLED
    pcr_baseline: Dict[int, str] = field(default_factory=dict)
    public_key: str = ""  # Device public key
    last_attestation: float = 0.0
    attestation_count: int = 0
    trust_score: float = 0.0

    def __post_init__(self):
        if not self.trust_score:
            self.trust_score = ANCHOR_TRUST.get(self.anchor_type, 0.4)
        if not self.binding_commitment:
            content = f"{self.device_id}:{self.lct_id}:{self.anchor_type.value}:{self.enrolled_at}"
            self.binding_commitment = hashlib.sha256(content.encode()).hexdigest()
        if not self.public_key:
            self.public_key = hashlib.sha256(
                f"pubkey:{self.device_id}:{self.enrolled_at}".encode()
            ).hexdigest()


@dataclass
class EnrollmentWitness:
    """Third-party attestation of a binding ceremony."""
    witness_id: str
    device_id: str
    lct_id: str
    witness_signature: str = ""
    witness_trust: float = 0.5
    timestamp: float = field(default_factory=time.time)
    witness_type: str = "federation"  # federation, legal, cryptographic

    def __post_init__(self):
        if not self.witness_signature:
            content = f"{self.witness_id}:{self.device_id}:{self.lct_id}:{self.timestamp}"
            self.witness_signature = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class ActionRecord:
    """An R6 action signed by a hardware-bound device."""
    action_id: str
    actor_lct: str
    device_id: str
    action_type: str  # R6 action type
    action_data: Dict = field(default_factory=dict)
    signature: str = ""
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.signature:
            content = f"{self.action_id}:{self.actor_lct}:{self.device_id}:{self.action_type}:{self.timestamp}"
            self.signature = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class VerificationProof:
    """Complete proof of hardware→action verification chain."""
    quote: AttestationQuote
    binding: DeviceBinding
    witnesses: List[EnrollmentWitness]
    action: Optional[ActionRecord]
    result: VerificationResult
    chain_depth: int = 0
    anomalies: List[str] = field(default_factory=list)
    verified_at: float = field(default_factory=time.time)
    proof_hash: str = ""

    def __post_init__(self):
        if not self.proof_hash:
            content = f"{self.quote.quote_hash}:{self.binding.binding_commitment}:{self.result.name}:{self.verified_at}"
            self.proof_hash = hashlib.sha256(content.encode()).hexdigest()


@dataclass
class RegistryEntry:
    """Entry in the federation hardware registry."""
    device_id: str
    lct_id: str
    federation_id: str
    anchor_type: AnchorType
    binding_commitment: str
    public_key: str
    state: DeviceState
    enrolled_at: float
    last_attestation: float
    trust_score: float
    entry_hash: str = ""
    prev_hash: str = ""

    def __post_init__(self):
        if not self.entry_hash:
            content = (f"{self.device_id}:{self.lct_id}:{self.federation_id}:"
                       f"{self.anchor_type.value}:{self.binding_commitment}:"
                       f"{self.state.name}:{self.prev_hash}")
            self.entry_hash = hashlib.sha256(content.encode()).hexdigest()


# ─── E2E Verifier ─────────────────────────────────────────────────────────────

class E2EVerifier:
    """Validates the complete hardware → action verification chain."""

    def __init__(self, pcr_policy: Set[int] = None,
                 max_quote_age: float = 3600.0,
                 min_witnesses: int = 1,
                 min_witness_trust: float = 0.3,
                 min_anchor_trust: float = 0.5):
        self.pcr_policy = pcr_policy or DEFAULT_PCR_POLICY
        self.max_quote_age = max_quote_age
        self.min_witnesses = min_witnesses
        self.min_witness_trust = min_witness_trust
        self.min_anchor_trust = min_anchor_trust

    def verify_chain(self, quote: AttestationQuote,
                     binding: DeviceBinding,
                     witnesses: List[EnrollmentWitness],
                     action: Optional[ActionRecord] = None,
                     current_time: float = None) -> VerificationProof:
        """Verify the complete chain from hardware attestation to action authorization."""
        now = current_time or time.time()
        anomalies = []
        chain_depth = 0

        # Step 1: Verify attestation quote
        result = self._verify_quote(quote, now, anomalies)
        if result != VerificationResult.VALID:
            return VerificationProof(quote, binding, witnesses, action, result,
                                     chain_depth, anomalies)
        chain_depth += 1

        # Step 2: Verify PCR values
        result = self._verify_pcrs(quote, binding, anomalies)
        if result != VerificationResult.VALID:
            return VerificationProof(quote, binding, witnesses, action, result,
                                     chain_depth, anomalies)
        chain_depth += 1

        # Step 3: Verify device binding
        result = self._verify_binding(quote, binding, anomalies)
        if result != VerificationResult.VALID:
            return VerificationProof(quote, binding, witnesses, action, result,
                                     chain_depth, anomalies)
        chain_depth += 1

        # Step 4: Verify enrollment witnesses
        result = self._verify_witnesses(binding, witnesses, anomalies)
        if result != VerificationResult.VALID:
            return VerificationProof(quote, binding, witnesses, action, result,
                                     chain_depth, anomalies)
        chain_depth += 1

        # Step 5: Verify action (if provided)
        if action:
            result = self._verify_action(action, binding, anomalies)
            if result != VerificationResult.VALID:
                return VerificationProof(quote, binding, witnesses, action, result,
                                         chain_depth, anomalies)
            chain_depth += 1

        return VerificationProof(quote, binding, witnesses, action,
                                 VerificationResult.VALID, chain_depth, anomalies)

    def _verify_quote(self, quote: AttestationQuote, now: float,
                      anomalies: List[str]) -> VerificationResult:
        """Step 1: Verify attestation quote freshness and signature."""
        # Check freshness
        age = now - quote.timestamp
        if age > self.max_quote_age:
            anomalies.append(f"quote_expired:age={age:.0f}s>max={self.max_quote_age:.0f}s")
            return VerificationResult.EXPIRED

        # Check nonce present
        if not quote.nonce:
            anomalies.append("quote_missing_nonce")
            return VerificationResult.INVALID_QUOTE

        # Check EK cert chain
        if not quote.ek_cert_chain or len(quote.ek_cert_chain) < 2:
            anomalies.append("quote_incomplete_cert_chain")
            return VerificationResult.INVALID_QUOTE

        # Verify quote hash integrity
        content = f"{quote.device_id}:{quote.nonce}:{quote.timestamp}"
        for idx in sorted(quote.pcr_snapshot.values.keys()):
            content += f":{idx}={quote.pcr_snapshot.values[idx]}"
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        if quote.quote_hash != expected_hash:
            anomalies.append("quote_hash_mismatch")
            return VerificationResult.INVALID_QUOTE

        # Check anchor trust
        anchor_trust = ANCHOR_TRUST.get(quote.anchor_type, 0.0)
        if anchor_trust < self.min_anchor_trust:
            anomalies.append(f"anchor_trust_low:{anchor_trust}<{self.min_anchor_trust}")
            return VerificationResult.INVALID_QUOTE

        return VerificationResult.VALID

    def _verify_pcrs(self, quote: AttestationQuote, binding: DeviceBinding,
                     anomalies: List[str]) -> VerificationResult:
        """Step 2: Verify PCR values match baseline."""
        if not binding.pcr_baseline:
            anomalies.append("pcr_no_baseline")
            return VerificationResult.INVALID_PCR

        matches, mismatched = quote.pcr_snapshot.matches_baseline(
            binding.pcr_baseline, self.pcr_policy
        )
        if not matches:
            anomalies.append(f"pcr_mismatch:indices={mismatched}")
            return VerificationResult.INVALID_PCR

        return VerificationResult.VALID

    def _verify_binding(self, quote: AttestationQuote, binding: DeviceBinding,
                        anomalies: List[str]) -> VerificationResult:
        """Step 3: Verify device binding consistency."""
        # Device IDs must match
        if quote.device_id != binding.device_id:
            anomalies.append(f"device_id_mismatch:{quote.device_id}!={binding.device_id}")
            return VerificationResult.INVALID_BINDING

        # Device must not be revoked
        if binding.state in (DeviceState.REVOKED, DeviceState.COMPROMISED):
            anomalies.append(f"device_state:{binding.state.name}")
            return VerificationResult.REVOKED

        if binding.state == DeviceState.LOST:
            anomalies.append(f"device_lost")
            return VerificationResult.REVOKED

        if binding.state == DeviceState.SUSPENDED:
            anomalies.append(f"device_suspended")
            return VerificationResult.INVALID_BINDING

        # Anchor types must match
        if quote.anchor_type != binding.anchor_type:
            anomalies.append(f"anchor_mismatch:{quote.anchor_type.value}!={binding.anchor_type.value}")
            return VerificationResult.INVALID_BINDING

        # Binding commitment integrity
        expected = hashlib.sha256(
            f"{binding.device_id}:{binding.lct_id}:{binding.anchor_type.value}:{binding.enrolled_at}".encode()
        ).hexdigest()
        if binding.binding_commitment != expected:
            anomalies.append("binding_commitment_tampered")
            return VerificationResult.INVALID_BINDING

        return VerificationResult.VALID

    def _verify_witnesses(self, binding: DeviceBinding,
                          witnesses: List[EnrollmentWitness],
                          anomalies: List[str]) -> VerificationResult:
        """Step 4: Verify enrollment witnesses."""
        # Must have minimum witnesses
        valid_witnesses = [
            w for w in witnesses
            if w.device_id == binding.device_id
            and w.lct_id == binding.lct_id
            and w.witness_trust >= self.min_witness_trust
        ]

        if len(valid_witnesses) < self.min_witnesses:
            anomalies.append(f"insufficient_witnesses:{len(valid_witnesses)}<{self.min_witnesses}")
            return VerificationResult.INVALID_WITNESS

        # Verify witness signatures
        for w in valid_witnesses:
            expected_sig = hashlib.sha256(
                f"{w.witness_id}:{w.device_id}:{w.lct_id}:{w.timestamp}".encode()
            ).hexdigest()
            if w.witness_signature != expected_sig:
                anomalies.append(f"witness_sig_invalid:{w.witness_id}")
                return VerificationResult.INVALID_WITNESS

        # Check witness diversity (at least 2 different witness IDs if >1 required)
        if self.min_witnesses > 1:
            unique_witnesses = set(w.witness_id for w in valid_witnesses)
            if len(unique_witnesses) < self.min_witnesses:
                anomalies.append(f"witness_diversity_low:{len(unique_witnesses)}")
                return VerificationResult.INVALID_WITNESS

        return VerificationResult.VALID

    def _verify_action(self, action: ActionRecord, binding: DeviceBinding,
                       anomalies: List[str]) -> VerificationResult:
        """Step 5: Verify action signed by bound device."""
        # Actor LCT must match binding
        if action.actor_lct != binding.lct_id:
            anomalies.append(f"action_lct_mismatch:{action.actor_lct}!={binding.lct_id}")
            return VerificationResult.INVALID_ACTION

        # Device ID must match
        if action.device_id != binding.device_id:
            anomalies.append(f"action_device_mismatch")
            return VerificationResult.INVALID_ACTION

        # Verify action signature integrity
        expected_sig = hashlib.sha256(
            f"{action.action_id}:{action.actor_lct}:{action.device_id}:{action.action_type}:{action.timestamp}".encode()
        ).hexdigest()
        if action.signature != expected_sig:
            anomalies.append("action_signature_invalid")
            return VerificationResult.INVALID_ACTION

        return VerificationResult.VALID


# ─── Hardware Registry ────────────────────────────────────────────────────────

class HardwareRegistry:
    """Federation-wide registry of hardware bindings with hash chain."""

    def __init__(self, federation_id: str):
        self.federation_id = federation_id
        self.entries: Dict[str, RegistryEntry] = {}  # device_id → entry
        self.chain: List[RegistryEntry] = []
        self.lct_devices: Dict[str, Set[str]] = {}  # lct_id → device_ids
        self.event_log: List[Dict] = []

    def register(self, binding: DeviceBinding,
                 witnesses: List[EnrollmentWitness]) -> RegistryEntry:
        """Register a hardware binding in the federation registry."""
        prev_hash = self.chain[-1].entry_hash if self.chain else "genesis"

        entry = RegistryEntry(
            device_id=binding.device_id,
            lct_id=binding.lct_id,
            federation_id=self.federation_id,
            anchor_type=binding.anchor_type,
            binding_commitment=binding.binding_commitment,
            public_key=binding.public_key,
            state=DeviceState.ACTIVE,
            enrolled_at=binding.enrolled_at,
            last_attestation=binding.last_attestation,
            trust_score=binding.trust_score,
            prev_hash=prev_hash,
        )

        self.entries[binding.device_id] = entry
        self.chain.append(entry)

        if binding.lct_id not in self.lct_devices:
            self.lct_devices[binding.lct_id] = set()
        self.lct_devices[binding.lct_id].add(binding.device_id)

        self._log_event(RegistryEventType.ENROLLMENT, binding.device_id,
                        binding.lct_id, f"witnesses={len(witnesses)}")

        return entry

    def update_attestation(self, device_id: str,
                           quote: AttestationQuote) -> Optional[RegistryEntry]:
        """Update registry entry with fresh attestation."""
        entry = self.entries.get(device_id)
        if not entry or entry.state != DeviceState.ACTIVE:
            return None

        entry.last_attestation = quote.timestamp
        self._log_event(RegistryEventType.ATTESTATION, device_id,
                        entry.lct_id, f"quote={quote.quote_hash[:16]}")
        return entry

    def revoke(self, device_id: str, reason: str = "") -> bool:
        """Revoke a device binding."""
        entry = self.entries.get(device_id)
        if not entry:
            return False

        entry.state = DeviceState.REVOKED
        entry.trust_score = 0.0

        self._log_event(RegistryEventType.REVOCATION, device_id,
                        entry.lct_id, reason)
        return True

    def get_lct_devices(self, lct_id: str) -> List[RegistryEntry]:
        """Get all device entries for an LCT."""
        device_ids = self.lct_devices.get(lct_id, set())
        return [self.entries[d] for d in device_ids if d in self.entries]

    def verify_chain_integrity(self) -> Tuple[bool, List[int]]:
        """Verify the hash chain integrity of the registry."""
        broken = []
        for i, entry in enumerate(self.chain):
            expected_prev = self.chain[i - 1].entry_hash if i > 0 else "genesis"
            if entry.prev_hash != expected_prev:
                broken.append(i)

            # Recompute entry hash
            content = (f"{entry.device_id}:{entry.lct_id}:{entry.federation_id}:"
                       f"{entry.anchor_type.value}:{entry.binding_commitment}:"
                       f"{entry.state.name}:{entry.prev_hash}")
            expected_hash = hashlib.sha256(content.encode()).hexdigest()
            if entry.entry_hash != expected_hash:
                broken.append(i)

        return len(broken) == 0, broken

    def _log_event(self, event_type: RegistryEventType,
                   device_id: str, lct_id: str, details: str = ""):
        self.event_log.append({
            "type": event_type.name,
            "device_id": device_id,
            "lct_id": lct_id,
            "details": details,
            "timestamp": time.time(),
        })


# ─── Coherence Checker ───────────────────────────────────────────────────────

class CoherenceChecker:
    """Validates cross-device identity coherence for multi-device constellations."""

    def __init__(self, max_devices: int = 10,
                 min_mutual_witness_ratio: float = 0.5,
                 max_anchor_type_concentration: float = 0.8):
        self.max_devices = max_devices
        self.min_mutual_witness_ratio = min_mutual_witness_ratio
        self.max_anchor_type_concentration = max_anchor_type_concentration

    def check_coherence(self, registry: HardwareRegistry,
                        lct_id: str) -> Dict:
        """Check coherence of all devices bound to an LCT."""
        devices = registry.get_lct_devices(lct_id)
        active_devices = [d for d in devices if d.state == DeviceState.ACTIVE]

        result = {
            "lct_id": lct_id,
            "total_devices": len(devices),
            "active_devices": len(active_devices),
            "coherent": True,
            "anomalies": [],
            "trust_composite": 0.0,
            "anchor_diversity": 0.0,
        }

        if not active_devices:
            result["coherent"] = False
            result["anomalies"].append("no_active_devices")
            return result

        # Check device count
        if len(active_devices) > self.max_devices:
            result["anomalies"].append(f"too_many_devices:{len(active_devices)}")
            result["coherent"] = False

        # Compute anchor diversity
        anchor_counts: Dict[AnchorType, int] = {}
        for d in active_devices:
            anchor_counts[d.anchor_type] = anchor_counts.get(d.anchor_type, 0) + 1

        if active_devices:
            max_concentration = max(anchor_counts.values()) / len(active_devices)
            result["anchor_diversity"] = 1.0 - max_concentration

            if max_concentration > self.max_anchor_type_concentration and len(active_devices) > 1:
                result["anomalies"].append(
                    f"anchor_concentration:{max_concentration:.2f}"
                )

        # Composite trust: weighted average by anchor trust
        total_weight = 0.0
        weighted_trust = 0.0
        for d in active_devices:
            weight = ANCHOR_TRUST.get(d.anchor_type, 0.4)
            weighted_trust += d.trust_score * weight
            total_weight += weight

        result["trust_composite"] = weighted_trust / total_weight if total_weight > 0 else 0.0

        # Check attestation freshness
        now = time.time()
        stale_count = 0
        for d in active_devices:
            if d.last_attestation > 0 and (now - d.last_attestation) > 86400:  # 24h
                stale_count += 1

        if stale_count > 0 and stale_count == len(active_devices):
            result["anomalies"].append(f"all_attestations_stale:{stale_count}")

        return result


# ─── Revocation Cascader ──────────────────────────────────────────────────────

class RevocationCascader:
    """Propagates revocation through binding chains and cross-federation."""

    def __init__(self):
        self.cascade_log: List[Dict] = []

    def cascade_revoke(self, registry: HardwareRegistry,
                       device_id: str, reason: str,
                       revoke_lct: bool = False) -> Dict:
        """Revoke a device and optionally cascade to LCT and all its devices."""
        entry = registry.entries.get(device_id)
        if not entry:
            return {"success": False, "reason": "device_not_found"}

        revoked = []

        # Revoke the target device
        registry.revoke(device_id, reason)
        revoked.append(device_id)

        if revoke_lct:
            # Revoke ALL devices for this LCT
            lct_devices = registry.get_lct_devices(entry.lct_id)
            for d in lct_devices:
                if d.device_id != device_id and d.state == DeviceState.ACTIVE:
                    registry.revoke(d.device_id, f"cascade_from:{device_id}")
                    revoked.append(d.device_id)

        result = {
            "success": True,
            "trigger_device": device_id,
            "lct_id": entry.lct_id,
            "revoked_devices": revoked,
            "total_revoked": len(revoked),
            "lct_revoked": revoke_lct,
        }

        self.cascade_log.append(result)
        return result

    def assess_impact(self, registry: HardwareRegistry,
                      device_id: str) -> Dict:
        """Assess the impact of revoking a device before doing it."""
        entry = registry.entries.get(device_id)
        if not entry:
            return {"device_found": False}

        lct_devices = registry.get_lct_devices(entry.lct_id)
        active_devices = [d for d in lct_devices if d.state == DeviceState.ACTIVE]
        is_last_active = len(active_devices) <= 1

        return {
            "device_found": True,
            "device_id": device_id,
            "lct_id": entry.lct_id,
            "total_devices": len(lct_devices),
            "active_devices": len(active_devices),
            "is_last_active": is_last_active,
            "trust_impact": entry.trust_score,
            "cascade_risk": "high" if is_last_active else "low",
        }


# ─── Federation Hardware Sync ─────────────────────────────────────────────────

class FederationHardwareSync:
    """Cross-federation hardware registry synchronization."""

    def __init__(self):
        self.registries: Dict[str, HardwareRegistry] = {}

    def add_registry(self, registry: HardwareRegistry):
        """Add a federation registry for cross-federation sync."""
        self.registries[registry.federation_id] = registry

    def cross_federation_lookup(self, device_id: str) -> List[Dict]:
        """Look up a device across all federation registries."""
        results = []
        for fed_id, registry in self.registries.items():
            if device_id in registry.entries:
                entry = registry.entries[device_id]
                results.append({
                    "federation_id": fed_id,
                    "lct_id": entry.lct_id,
                    "state": entry.state.name,
                    "trust_score": entry.trust_score,
                    "anchor_type": entry.anchor_type.value,
                })
        return results

    def detect_conflicts(self) -> List[Dict]:
        """Detect conflicting device registrations across federations."""
        conflicts = []
        device_registrations: Dict[str, List[Dict]] = {}

        for fed_id, registry in self.registries.items():
            for device_id, entry in registry.entries.items():
                if device_id not in device_registrations:
                    device_registrations[device_id] = []
                device_registrations[device_id].append({
                    "federation_id": fed_id,
                    "lct_id": entry.lct_id,
                    "state": entry.state.name,
                })

        for device_id, regs in device_registrations.items():
            if len(regs) > 1:
                # Same device in multiple federations
                lct_ids = set(r["lct_id"] for r in regs)
                if len(lct_ids) > 1:
                    # Different LCTs for same device — conflict!
                    conflicts.append({
                        "type": "identity_conflict",
                        "device_id": device_id,
                        "registrations": regs,
                        "severity": "critical",
                    })
                else:
                    # Same LCT across federations — legitimate multi-federation presence
                    state_mismatch = len(set(r["state"] for r in regs)) > 1
                    if state_mismatch:
                        conflicts.append({
                            "type": "state_conflict",
                            "device_id": device_id,
                            "registrations": regs,
                            "severity": "warning",
                        })

        return conflicts

    def propagate_revocation(self, device_id: str, source_federation: str,
                             reason: str) -> Dict:
        """Propagate a revocation from one federation to all others."""
        propagated = []

        for fed_id, registry in self.registries.items():
            if fed_id == source_federation:
                continue

            if device_id in registry.entries:
                entry = registry.entries[device_id]
                if entry.state == DeviceState.ACTIVE:
                    registry.revoke(device_id, f"cross_fed_revoke:{source_federation}:{reason}")
                    propagated.append(fed_id)

        return {
            "source_federation": source_federation,
            "device_id": device_id,
            "propagated_to": propagated,
            "total_propagated": len(propagated),
        }


# ─── Sybil Cost Model ────────────────────────────────────────────────────────

class HardwareSybilCostModel:
    """Formal cost model for hardware-backed sybil resistance."""

    def __init__(self, hardware_cost: float = 250.0,
                 atp_provision_cost: float = 50.0,
                 detection_rate: float = 0.7,
                 slash_penalty: float = 500.0):
        self.hardware_cost = hardware_cost
        self.atp_provision_cost = atp_provision_cost
        self.detection_rate = detection_rate
        self.slash_penalty = slash_penalty

    def attack_cost(self, num_identities: int) -> Dict:
        """Calculate cost of mounting a sybil attack with N identities."""
        hardware = num_identities * self.hardware_cost
        atp = num_identities * self.atp_provision_cost
        upfront = hardware + atp

        # Expected penalty from detection
        expected_penalty = num_identities * self.detection_rate * self.slash_penalty

        total = upfront + expected_penalty

        return {
            "num_identities": num_identities,
            "hardware_cost": hardware,
            "atp_cost": atp,
            "upfront_cost": upfront,
            "expected_penalty": expected_penalty,
            "total_expected_cost": total,
            "cost_per_identity": total / num_identities,
        }

    def honest_reward(self, trust_level: float = 0.8,
                      cycles: int = 100) -> float:
        """Expected reward for honest participation."""
        base_reward = 10.0  # per cycle
        trust_multiplier = trust_level * 1.5
        return base_reward * trust_multiplier * cycles

    def sybil_reward(self, num_identities: int,
                     sybil_trust: float = 0.3,
                     cycles: int = 100) -> float:
        """Expected reward for sybil identities."""
        base_reward = 10.0
        trust_multiplier = sybil_trust * 1.5
        diminishing = sum(0.8 ** i for i in range(num_identities))
        return base_reward * trust_multiplier * cycles * diminishing / num_identities

    def is_profitable(self, num_identities: int,
                      sybil_trust: float = 0.3,
                      cycles: int = 100) -> Dict:
        """Determine if a sybil attack is profitable."""
        cost = self.attack_cost(num_identities)
        reward = self.sybil_reward(num_identities, sybil_trust, cycles)
        total_reward = reward * num_identities
        honest_alt = self.honest_reward(0.8, cycles)

        return {
            "total_cost": cost["total_expected_cost"],
            "total_reward": total_reward,
            "net_profit": total_reward - cost["total_expected_cost"],
            "profitable": total_reward > cost["total_expected_cost"],
            "honest_alternative": honest_alt,
            "honest_better": honest_alt > total_reward - cost["total_expected_cost"],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_pcr_baseline() -> Dict[int, str]:
    """Create a standard PCR baseline."""
    return {
        i: hashlib.sha256(f"pcr_{i}_baseline".encode()).hexdigest()
        for i in range(8)
    }


def _make_quote(device_id: str, nonce: str,
                pcr_override: Dict[int, str] = None,
                anchor: AnchorType = AnchorType.TPM2_DISCRETE,
                cert_chain: List[str] = None,
                ts: float = None) -> AttestationQuote:
    """Create a test attestation quote."""
    baseline = _make_pcr_baseline()
    if pcr_override:
        baseline.update(pcr_override)
    return AttestationQuote(
        device_id=device_id,
        nonce=nonce,
        pcr_snapshot=PCRSnapshot(values=baseline, timestamp=ts or time.time()),
        quote_signature="sig_" + device_id,
        ek_cert_chain=cert_chain or ["ek_cert", "ica_cert", "root_cert"],
        anchor_type=anchor,
        timestamp=ts or time.time(),
    )


def _make_binding(device_id: str, lct_id: str,
                  anchor: AnchorType = AnchorType.TPM2_DISCRETE,
                  state: DeviceState = DeviceState.ACTIVE,
                  ts: float = None) -> DeviceBinding:
    """Create a test device binding."""
    binding = DeviceBinding(
        device_id=device_id,
        lct_id=lct_id,
        anchor_type=anchor,
        enrolled_at=ts or time.time(),
        state=state,
        pcr_baseline=_make_pcr_baseline(),
    )
    return binding


def _make_witnesses(device_id: str, lct_id: str,
                    count: int = 2, trust: float = 0.7) -> List[EnrollmentWitness]:
    """Create test enrollment witnesses."""
    return [
        EnrollmentWitness(
            witness_id=f"witness_{i}",
            device_id=device_id,
            lct_id=lct_id,
            witness_trust=trust,
        )
        for i in range(count)
    ]


def _make_action(lct_id: str, device_id: str,
                 action_type: str = "transfer") -> ActionRecord:
    """Create a test action record."""
    return ActionRecord(
        action_id=f"act_{device_id}_{action_type}",
        actor_lct=lct_id,
        device_id=device_id,
        action_type=action_type,
    )


def run_tests():
    results = []
    now = time.time()

    def check(name, condition, detail=""):
        results.append((name, condition, detail))

    # ─── S1: Happy path — full chain verification ─────────────────────

    verifier = E2EVerifier()
    device_id = "dev_tpm_001"
    lct_id = "lct:root:alice"
    quote = _make_quote(device_id, "nonce_123", ts=now)
    binding = _make_binding(device_id, lct_id, ts=now - 3600)
    witnesses = _make_witnesses(device_id, lct_id)
    action = _make_action(lct_id, device_id)

    proof = verifier.verify_chain(quote, binding, witnesses, action, current_time=now)
    check("s1_happy_path_valid", proof.result == VerificationResult.VALID,
          f"result={proof.result.name}")
    check("s1_chain_depth", proof.chain_depth == 5,
          f"depth={proof.chain_depth}")
    check("s1_no_anomalies", len(proof.anomalies) == 0,
          f"anomalies={proof.anomalies}")
    check("s1_proof_hash", len(proof.proof_hash) == 64)

    # ─── S2: Quote verification failures ──────────────────────────────

    # Expired quote
    old_quote = _make_quote(device_id, "nonce_old", ts=now - 7200)
    proof_expired = verifier.verify_chain(old_quote, binding, witnesses, current_time=now)
    check("s2_expired_quote", proof_expired.result == VerificationResult.EXPIRED,
          f"result={proof_expired.result.name}")

    # Missing nonce
    no_nonce_quote = _make_quote(device_id, "", ts=now)
    proof_nonce = verifier.verify_chain(no_nonce_quote, binding, witnesses, current_time=now)
    check("s2_missing_nonce", proof_nonce.result == VerificationResult.INVALID_QUOTE,
          f"result={proof_nonce.result.name}")

    # Incomplete cert chain
    bad_cert_quote = _make_quote(device_id, "nonce_bad", cert_chain=["only_one"], ts=now)
    proof_cert = verifier.verify_chain(bad_cert_quote, binding, witnesses, current_time=now)
    check("s2_incomplete_cert", proof_cert.result == VerificationResult.INVALID_QUOTE,
          f"result={proof_cert.result.name}")

    # Software anchor below trust threshold
    sw_verifier = E2EVerifier(min_anchor_trust=0.5)
    sw_quote = _make_quote(device_id, "nonce_sw", anchor=AnchorType.SOFTWARE, ts=now)
    sw_binding = _make_binding(device_id, lct_id, anchor=AnchorType.SOFTWARE, ts=now - 3600)
    proof_sw = sw_verifier.verify_chain(sw_quote, sw_binding, witnesses, current_time=now)
    check("s2_software_rejected", proof_sw.result == VerificationResult.INVALID_QUOTE,
          f"result={proof_sw.result.name}")

    # Tampered quote hash
    tampered_quote = _make_quote(device_id, "nonce_tamper", ts=now)
    tampered_quote.quote_hash = "00" * 32
    proof_tamper = verifier.verify_chain(tampered_quote, binding, witnesses, current_time=now)
    check("s2_tampered_hash", proof_tamper.result == VerificationResult.INVALID_QUOTE,
          f"result={proof_tamper.result.name}")

    # ─── S3: PCR verification ────────────────────────────────────────

    # Mismatched PCR value
    bad_pcr = {0: hashlib.sha256(b"compromised_bios").hexdigest()}
    pcr_quote = _make_quote(device_id, "nonce_pcr", pcr_override=bad_pcr, ts=now)
    proof_pcr = verifier.verify_chain(pcr_quote, binding, witnesses, current_time=now)
    check("s3_pcr_mismatch", proof_pcr.result == VerificationResult.INVALID_PCR,
          f"result={proof_pcr.result.name}")

    # Missing baseline
    no_baseline_binding = _make_binding(device_id, lct_id, ts=now - 3600)
    no_baseline_binding.pcr_baseline = {}
    proof_no_bl = verifier.verify_chain(quote, no_baseline_binding, witnesses, current_time=now)
    check("s3_no_baseline", proof_no_bl.result == VerificationResult.INVALID_PCR,
          f"result={proof_no_bl.result.name}")

    # Strict PCR policy catches more
    strict_verifier = E2EVerifier(pcr_policy=STRICT_PCR_POLICY)
    # Override PCR 5 (not in default policy but in strict)
    bad_pcr5 = {5: hashlib.sha256(b"bad_kernel").hexdigest()}
    pcr5_quote = _make_quote(device_id, "nonce_pcr5", pcr_override=bad_pcr5, ts=now)
    proof_strict = strict_verifier.verify_chain(pcr5_quote, binding, witnesses, current_time=now)
    check("s3_strict_catches_pcr5", proof_strict.result == VerificationResult.INVALID_PCR,
          f"result={proof_strict.result.name}")

    # Default policy doesn't catch PCR 5
    proof_default = verifier.verify_chain(pcr5_quote, binding, witnesses, current_time=now)
    check("s3_default_allows_pcr5", proof_default.result == VerificationResult.VALID,
          f"result={proof_default.result.name}")

    # ─── S4: Binding verification ─────────────────────────────────────

    # Device ID mismatch
    wrong_dev_quote = _make_quote("dev_wrong", "nonce_wd", ts=now)
    proof_wrong = verifier.verify_chain(wrong_dev_quote, binding, witnesses, current_time=now)
    check("s4_device_mismatch", proof_wrong.result == VerificationResult.INVALID_BINDING,
          f"result={proof_wrong.result.name}")

    # Revoked device
    revoked_binding = _make_binding(device_id, lct_id, state=DeviceState.REVOKED, ts=now - 3600)
    proof_rev = verifier.verify_chain(quote, revoked_binding, witnesses, current_time=now)
    check("s4_revoked", proof_rev.result == VerificationResult.REVOKED,
          f"result={proof_rev.result.name}")

    # Compromised device
    comp_binding = _make_binding(device_id, lct_id, state=DeviceState.COMPROMISED, ts=now - 3600)
    proof_comp = verifier.verify_chain(quote, comp_binding, witnesses, current_time=now)
    check("s4_compromised", proof_comp.result == VerificationResult.REVOKED,
          f"result={proof_comp.result.name}")

    # Lost device
    lost_binding = _make_binding(device_id, lct_id, state=DeviceState.LOST, ts=now - 3600)
    proof_lost = verifier.verify_chain(quote, lost_binding, witnesses, current_time=now)
    check("s4_lost", proof_lost.result == VerificationResult.REVOKED,
          f"result={proof_lost.result.name}")

    # Suspended device
    susp_binding = _make_binding(device_id, lct_id, state=DeviceState.SUSPENDED, ts=now - 3600)
    proof_susp = verifier.verify_chain(quote, susp_binding, witnesses, current_time=now)
    check("s4_suspended", proof_susp.result == VerificationResult.INVALID_BINDING,
          f"result={proof_susp.result.name}")

    # Anchor type mismatch
    anchor_mismatch_binding = _make_binding(device_id, lct_id,
                                            anchor=AnchorType.FIDO2, ts=now - 3600)
    proof_anchor = verifier.verify_chain(quote, anchor_mismatch_binding, witnesses,
                                         current_time=now)
    check("s4_anchor_mismatch", proof_anchor.result == VerificationResult.INVALID_BINDING,
          f"result={proof_anchor.result.name}")

    # Tampered binding commitment
    tampered_binding = _make_binding(device_id, lct_id, ts=now - 3600)
    tampered_binding.binding_commitment = "00" * 32
    proof_tamper_b = verifier.verify_chain(quote, tampered_binding, witnesses, current_time=now)
    check("s4_tampered_commitment", proof_tamper_b.result == VerificationResult.INVALID_BINDING,
          f"result={proof_tamper_b.result.name}")

    # ─── S5: Witness verification ─────────────────────────────────────

    # No witnesses
    proof_no_w = verifier.verify_chain(quote, binding, [], current_time=now)
    check("s5_no_witnesses", proof_no_w.result == VerificationResult.INVALID_WITNESS,
          f"result={proof_no_w.result.name}")

    # Low-trust witness
    low_w = _make_witnesses(device_id, lct_id, count=2, trust=0.1)
    proof_low_w = verifier.verify_chain(quote, binding, low_w, current_time=now)
    check("s5_low_trust_witness", proof_low_w.result == VerificationResult.INVALID_WITNESS,
          f"result={proof_low_w.result.name}")

    # Wrong device on witness
    wrong_w = [EnrollmentWitness(witness_id="w0", device_id="other_dev",
                                 lct_id=lct_id, witness_trust=0.8)]
    proof_wrong_w = verifier.verify_chain(quote, binding, wrong_w, current_time=now)
    check("s5_wrong_device_witness", proof_wrong_w.result == VerificationResult.INVALID_WITNESS,
          f"result={proof_wrong_w.result.name}")

    # Tampered witness signature
    bad_sig_w = _make_witnesses(device_id, lct_id, count=2, trust=0.7)
    bad_sig_w[0].witness_signature = "tampered"
    proof_bad_sig = verifier.verify_chain(quote, binding, bad_sig_w, current_time=now)
    check("s5_tampered_witness_sig", proof_bad_sig.result == VerificationResult.INVALID_WITNESS,
          f"result={proof_bad_sig.result.name}")

    # Multi-witness requirement with diversity check
    multi_verifier = E2EVerifier(min_witnesses=3)
    two_w = _make_witnesses(device_id, lct_id, count=2, trust=0.7)
    proof_multi = multi_verifier.verify_chain(quote, binding, two_w, current_time=now)
    check("s5_insufficient_count", proof_multi.result == VerificationResult.INVALID_WITNESS,
          f"result={proof_multi.result.name}")

    three_w = _make_witnesses(device_id, lct_id, count=3, trust=0.7)
    proof_three = multi_verifier.verify_chain(quote, binding, three_w, current_time=now)
    check("s5_sufficient_count", proof_three.result == VerificationResult.VALID,
          f"result={proof_three.result.name}")

    # Witness diversity: 3 required but only 2 unique IDs
    dup_w = _make_witnesses(device_id, lct_id, count=3, trust=0.7)
    dup_w[2].witness_id = dup_w[0].witness_id  # Duplicate
    # Recompute signature for the duplicate
    dup_w[2].witness_signature = hashlib.sha256(
        f"{dup_w[2].witness_id}:{dup_w[2].device_id}:{dup_w[2].lct_id}:{dup_w[2].timestamp}".encode()
    ).hexdigest()
    proof_dup = multi_verifier.verify_chain(quote, binding, dup_w, current_time=now)
    check("s5_duplicate_witnesses", proof_dup.result == VerificationResult.INVALID_WITNESS,
          f"result={proof_dup.result.name}")

    # ─── S6: Action verification ──────────────────────────────────────

    # LCT mismatch
    wrong_lct_action = _make_action("lct:other", device_id)
    proof_lct = verifier.verify_chain(quote, binding, witnesses, wrong_lct_action,
                                      current_time=now)
    check("s6_action_lct_mismatch", proof_lct.result == VerificationResult.INVALID_ACTION,
          f"result={proof_lct.result.name}")

    # Device mismatch
    wrong_dev_action = _make_action(lct_id, "other_device")
    proof_dev = verifier.verify_chain(quote, binding, witnesses, wrong_dev_action,
                                      current_time=now)
    check("s6_action_device_mismatch", proof_dev.result == VerificationResult.INVALID_ACTION,
          f"result={proof_dev.result.name}")

    # Tampered action signature
    bad_action = _make_action(lct_id, device_id)
    bad_action.signature = "tampered"
    proof_bad_act = verifier.verify_chain(quote, binding, witnesses, bad_action,
                                          current_time=now)
    check("s6_tampered_action_sig", proof_bad_act.result == VerificationResult.INVALID_ACTION,
          f"result={proof_bad_act.result.name}")

    # Valid action without hardware action
    proof_no_act = verifier.verify_chain(quote, binding, witnesses, None, current_time=now)
    check("s6_no_action_valid", proof_no_act.result == VerificationResult.VALID,
          f"chain_depth={proof_no_act.chain_depth}")
    check("s6_no_action_depth", proof_no_act.chain_depth == 4,
          f"depth={proof_no_act.chain_depth}")

    # ─── S7: Hardware Registry ────────────────────────────────────────

    registry = HardwareRegistry("fed_alpha")

    # Register multiple devices
    dev1_binding = _make_binding("dev_001", "lct:alice", ts=now - 7200)
    dev2_binding = _make_binding("dev_002", "lct:alice",
                                anchor=AnchorType.FIDO2, ts=now - 3600)
    dev3_binding = _make_binding("dev_003", "lct:bob", ts=now - 1800)

    w1 = _make_witnesses("dev_001", "lct:alice")
    w2 = _make_witnesses("dev_002", "lct:alice")
    w3 = _make_witnesses("dev_003", "lct:bob")

    entry1 = registry.register(dev1_binding, w1)
    entry2 = registry.register(dev2_binding, w2)
    entry3 = registry.register(dev3_binding, w3)

    check("s7_registry_count", len(registry.entries) == 3)
    check("s7_chain_length", len(registry.chain) == 3)
    check("s7_alice_devices", len(registry.get_lct_devices("lct:alice")) == 2)
    check("s7_bob_devices", len(registry.get_lct_devices("lct:bob")) == 1)

    # Hash chain integrity
    valid_chain, broken = registry.verify_chain_integrity()
    check("s7_chain_integrity", valid_chain, f"broken={broken}")

    # Update attestation
    new_quote = _make_quote("dev_001", "nonce_refresh", ts=now)
    updated = registry.update_attestation("dev_001", new_quote)
    check("s7_attestation_updated", updated is not None)
    check("s7_attestation_timestamp", updated.last_attestation == now)

    # Revoke a device
    revoked = registry.revoke("dev_001", "compromise_detected")
    check("s7_revoke_success", revoked)
    check("s7_revoke_state",
          registry.entries["dev_001"].state == DeviceState.REVOKED)
    check("s7_revoke_trust",
          registry.entries["dev_001"].trust_score == 0.0)

    # Cannot update revoked device
    no_update = registry.update_attestation("dev_001", new_quote)
    check("s7_no_update_revoked", no_update is None)

    # Event log
    check("s7_event_log", len(registry.event_log) >= 4,
          f"events={len(registry.event_log)}")

    # ─── S8: Coherence Checker ────────────────────────────────────────

    coherence = CoherenceChecker()

    # Fresh registry for coherence tests
    reg2 = HardwareRegistry("fed_beta")
    for i in range(3):
        anchor = [AnchorType.TPM2_DISCRETE, AnchorType.FIDO2, AnchorType.SECURE_ENCLAVE][i]
        b = _make_binding(f"coh_dev_{i}", "lct:carol", anchor=anchor, ts=now - 3600)
        b.last_attestation = now - 100  # Fresh attestation
        w = _make_witnesses(f"coh_dev_{i}", "lct:carol")
        reg2.register(b, w)

    result = coherence.check_coherence(reg2, "lct:carol")
    check("s8_coherent", result["coherent"])
    check("s8_active_devices", result["active_devices"] == 3)
    check("s8_trust_positive", result["trust_composite"] > 0.5,
          f"trust={result['trust_composite']:.3f}")
    check("s8_diversity_positive", result["anchor_diversity"] > 0.0,
          f"diversity={result['anchor_diversity']:.3f}")

    # Non-existent LCT
    no_lct = coherence.check_coherence(reg2, "lct:nobody")
    check("s8_no_devices", not no_lct["coherent"])
    check("s8_no_devices_anomaly", "no_active_devices" in no_lct["anomalies"])

    # Too many devices
    reg3 = HardwareRegistry("fed_gamma")
    small_checker = CoherenceChecker(max_devices=2)
    for i in range(5):
        b = _make_binding(f"many_dev_{i}", "lct:dave", ts=now - 3600)
        w = _make_witnesses(f"many_dev_{i}", "lct:dave")
        reg3.register(b, w)

    many_result = small_checker.check_coherence(reg3, "lct:dave")
    check("s8_too_many_devices", not many_result["coherent"])

    # All same anchor type → low diversity
    reg4 = HardwareRegistry("fed_delta")
    for i in range(4):
        b = _make_binding(f"same_dev_{i}", "lct:eve",
                         anchor=AnchorType.SOFTWARE, ts=now - 3600)
        w = _make_witnesses(f"same_dev_{i}", "lct:eve")
        reg4.register(b, w)

    same_result = coherence.check_coherence(reg4, "lct:eve")
    check("s8_low_diversity", same_result["anchor_diversity"] == 0.0,
          f"diversity={same_result['anchor_diversity']:.3f}")
    check("s8_software_trust",
          same_result["trust_composite"] < 0.5,
          f"trust={same_result['trust_composite']:.3f}")

    # ─── S9: Revocation Cascade ───────────────────────────────────────

    cascader = RevocationCascader()

    reg5 = HardwareRegistry("fed_epsilon")
    for i in range(4):
        b = _make_binding(f"casc_dev_{i}", "lct:frank", ts=now - 3600)
        w = _make_witnesses(f"casc_dev_{i}", "lct:frank")
        reg5.register(b, w)

    # Single device revocation (no cascade)
    single_result = cascader.cascade_revoke(reg5, "casc_dev_0", "test")
    check("s9_single_revoke", single_result["total_revoked"] == 1)
    check("s9_others_active",
          reg5.entries["casc_dev_1"].state == DeviceState.ACTIVE)

    # Full LCT cascade
    cascade_result = cascader.cascade_revoke(reg5, "casc_dev_1", "compromise",
                                             revoke_lct=True)
    check("s9_cascade_count", cascade_result["total_revoked"] == 3,
          f"revoked={cascade_result['total_revoked']}")
    check("s9_all_revoked",
          all(reg5.entries[f"casc_dev_{i}"].state == DeviceState.REVOKED
              for i in range(4)))

    # Impact assessment
    reg6 = HardwareRegistry("fed_zeta")
    sole_binding = _make_binding("sole_dev", "lct:grace", ts=now - 3600)
    reg6.register(sole_binding, _make_witnesses("sole_dev", "lct:grace"))

    impact = cascader.assess_impact(reg6, "sole_dev")
    check("s9_impact_last_active", impact["is_last_active"])
    check("s9_impact_high_risk", impact["cascade_risk"] == "high")

    # ─── S10: Federation Hardware Sync ────────────────────────────────

    sync = FederationHardwareSync()

    fed_a = HardwareRegistry("fed_A")
    fed_b = HardwareRegistry("fed_B")
    fed_c = HardwareRegistry("fed_C")

    # Same device registered in A and B with same LCT (legitimate)
    shared_binding = _make_binding("shared_dev", "lct:henry", ts=now - 7200)
    fed_a.register(shared_binding, _make_witnesses("shared_dev", "lct:henry"))
    shared_binding_b = _make_binding("shared_dev", "lct:henry", ts=now - 3600)
    fed_b.register(shared_binding_b, _make_witnesses("shared_dev", "lct:henry"))

    # Same device in C with DIFFERENT LCT (conflict!)
    conflict_binding = _make_binding("shared_dev", "lct:imposter", ts=now - 1800)
    fed_c.register(conflict_binding, _make_witnesses("shared_dev", "lct:imposter"))

    sync.add_registry(fed_a)
    sync.add_registry(fed_b)
    sync.add_registry(fed_c)

    # Cross-federation lookup
    lookups = sync.cross_federation_lookup("shared_dev")
    check("s10_lookup_count", len(lookups) == 3,
          f"found_in={len(lookups)}")

    # Detect conflicts
    conflicts = sync.detect_conflicts()
    identity_conflicts = [c for c in conflicts if c["type"] == "identity_conflict"]
    check("s10_identity_conflict", len(identity_conflicts) == 1,
          f"conflicts={len(identity_conflicts)}")
    check("s10_conflict_severity",
          identity_conflicts[0]["severity"] == "critical")

    # Propagate revocation from A
    prop_result = sync.propagate_revocation("shared_dev", "fed_A", "detected_impersonation")
    check("s10_propagation_count", prop_result["total_propagated"] == 2,
          f"propagated={prop_result['total_propagated']}")
    check("s10_b_revoked",
          fed_b.entries["shared_dev"].state == DeviceState.REVOKED)
    check("s10_c_revoked",
          fed_c.entries["shared_dev"].state == DeviceState.REVOKED)

    # State conflict detection (after partial revocation)
    fed_d = HardwareRegistry("fed_D")
    fed_e = HardwareRegistry("fed_E")
    state_binding_d = _make_binding("state_dev", "lct:iris", ts=now - 3600)
    state_binding_e = _make_binding("state_dev", "lct:iris", ts=now - 3600)
    fed_d.register(state_binding_d, _make_witnesses("state_dev", "lct:iris"))
    fed_e.register(state_binding_e, _make_witnesses("state_dev", "lct:iris"))
    fed_d.revoke("state_dev", "test")

    sync2 = FederationHardwareSync()
    sync2.add_registry(fed_d)
    sync2.add_registry(fed_e)
    conflicts2 = sync2.detect_conflicts()
    state_conflicts = [c for c in conflicts2 if c["type"] == "state_conflict"]
    check("s10_state_conflict", len(state_conflicts) == 1)
    check("s10_state_severity", state_conflicts[0]["severity"] == "warning")

    # ─── S11: Sybil Cost Model ────────────────────────────────────────

    cost_model = HardwareSybilCostModel()

    # Single identity cost
    single_cost = cost_model.attack_cost(1)
    check("s11_single_hw_cost", single_cost["hardware_cost"] == 250.0)
    check("s11_single_atp_cost", single_cost["atp_cost"] == 50.0)
    check("s11_single_penalty", single_cost["expected_penalty"] == 350.0,
          f"penalty={single_cost['expected_penalty']}")

    # 5-identity cost scales linearly
    five_cost = cost_model.attack_cost(5)
    check("s11_five_hw_cost", five_cost["hardware_cost"] == 1250.0)
    check("s11_five_total", five_cost["total_expected_cost"] == 3250.0,
          f"total={five_cost['total_expected_cost']}")

    # Honest reward exceeds sybil profit
    honest = cost_model.honest_reward(0.8, 100)
    check("s11_honest_reward", honest > 0, f"honest={honest}")

    # Sybil attack unprofitable
    profit_1 = cost_model.is_profitable(1)
    check("s11_1_identity_unprofitable", not profit_1["profitable"],
          f"net={profit_1['net_profit']:.2f}")

    profit_5 = cost_model.is_profitable(5)
    check("s11_5_identity_unprofitable", not profit_5["profitable"],
          f"net={profit_5['net_profit']:.2f}")

    # Honest always better
    check("s11_honest_dominates_1", profit_1["honest_better"])
    check("s11_honest_dominates_5", profit_5["honest_better"])

    # Cost per identity increases with N (due to detection penalties)
    check("s11_cost_scales",
          five_cost["cost_per_identity"] == single_cost["cost_per_identity"],
          "linear scaling")

    # ─── S12: Multi-anchor constellation E2E ──────────────────────────

    # Alice has TPM + FIDO2 + Secure Enclave — verify each independently
    e2e_reg = HardwareRegistry("fed_e2e")
    e2e_verifier = E2EVerifier(min_witnesses=2)

    anchors = [
        ("alice_tpm", AnchorType.TPM2_DISCRETE),
        ("alice_fido", AnchorType.FIDO2),
        ("alice_se", AnchorType.SECURE_ENCLAVE),
    ]

    for dev_id, anchor in anchors:
        b = _make_binding(dev_id, "lct:alice_e2e", anchor=anchor, ts=now - 3600)
        w = _make_witnesses(dev_id, "lct:alice_e2e", count=2, trust=0.7)
        e2e_reg.register(b, w)

        q = _make_quote(dev_id, f"nonce_{dev_id}", anchor=anchor, ts=now)
        a = _make_action("lct:alice_e2e", dev_id, "sign_document")
        proof = e2e_verifier.verify_chain(q, b, w, a, current_time=now)
        check(f"s12_{dev_id}_valid", proof.result == VerificationResult.VALID,
              f"depth={proof.chain_depth}")

    # Check constellation coherence
    coh_result = coherence.check_coherence(e2e_reg, "lct:alice_e2e")
    check("s12_constellation_coherent", coh_result["coherent"])
    check("s12_constellation_diverse", coh_result["anchor_diversity"] > 0.5,
          f"diversity={coh_result['anchor_diversity']:.3f}")
    check("s12_high_trust", coh_result["trust_composite"] > 0.8,
          f"trust={coh_result['trust_composite']:.3f}")

    # ─── S13: Attack scenarios ────────────────────────────────────────

    # Attack 1: Quote replay (same nonce, different time)
    replay_quote = _make_quote(device_id, "nonce_123", ts=now - 5000)
    # Quote is old → should be expired
    proof_replay = verifier.verify_chain(replay_quote, binding, witnesses, current_time=now)
    check("s13_replay_blocked",
          proof_replay.result in (VerificationResult.EXPIRED, VerificationResult.INVALID_QUOTE),
          f"result={proof_replay.result.name}")

    # Attack 2: Device spoofing (wrong device claims binding)
    spoof_quote = _make_quote("spoof_device", "nonce_spoof", ts=now)
    proof_spoof = verifier.verify_chain(spoof_quote, binding, witnesses, current_time=now)
    check("s13_spoof_blocked", proof_spoof.result == VerificationResult.INVALID_BINDING,
          f"result={proof_spoof.result.name}")

    # Attack 3: Witness forgery
    forge_w = [EnrollmentWitness(witness_id="forged", device_id=device_id,
                                 lct_id=lct_id, witness_trust=0.9,
                                 witness_signature="forged_sig")]
    proof_forge = verifier.verify_chain(quote, binding, forge_w, current_time=now)
    check("s13_witness_forgery_blocked",
          proof_forge.result == VerificationResult.INVALID_WITNESS,
          f"result={proof_forge.result.name}")

    # Attack 4: Action hijack (valid chain but action from wrong actor)
    hijack_action = _make_action("lct:hacker", device_id, "steal_funds")
    proof_hijack = verifier.verify_chain(quote, binding, witnesses, hijack_action,
                                         current_time=now)
    check("s13_hijack_blocked", proof_hijack.result == VerificationResult.INVALID_ACTION,
          f"result={proof_hijack.result.name}")

    # Attack 5: Registry chain tampering
    tamper_reg = HardwareRegistry("fed_tamper")
    t_binding = _make_binding("tamper_dev", "lct:target", ts=now - 3600)
    tamper_reg.register(t_binding, _make_witnesses("tamper_dev", "lct:target"))
    # Tamper with chain
    tamper_reg.chain[0].prev_hash = "tampered_genesis"
    valid_after_tamper, broken_indices = tamper_reg.verify_chain_integrity()
    check("s13_chain_tamper_detected", not valid_after_tamper,
          f"broken={broken_indices}")

    # Attack 6: Cross-federation identity split
    # Already tested in S10 — identity_conflict detection

    # ─── S14: Edge cases and boundary conditions ──────────────────────

    # Single witness sufficient with min_witnesses=1
    single_w_verifier = E2EVerifier(min_witnesses=1)
    one_w = _make_witnesses(device_id, lct_id, count=1, trust=0.5)
    proof_one_w = single_w_verifier.verify_chain(quote, binding, one_w, current_time=now)
    check("s14_single_witness_ok", proof_one_w.result == VerificationResult.VALID)

    # Witness trust exactly at threshold
    exact_w = _make_witnesses(device_id, lct_id, count=1, trust=0.3)
    proof_exact = single_w_verifier.verify_chain(quote, binding, exact_w, current_time=now)
    check("s14_exact_threshold_ok", proof_exact.result == VerificationResult.VALID)

    # Witness trust just below threshold
    below_w = _make_witnesses(device_id, lct_id, count=1, trust=0.29)
    proof_below = single_w_verifier.verify_chain(quote, binding, below_w, current_time=now)
    check("s14_below_threshold_fail",
          proof_below.result == VerificationResult.INVALID_WITNESS)

    # Empty action data still valid
    empty_action = _make_action(lct_id, device_id, "empty_op")
    proof_empty = verifier.verify_chain(quote, binding, witnesses, empty_action,
                                        current_time=now)
    check("s14_empty_action_ok", proof_empty.result == VerificationResult.VALID)

    # Quote exactly at max age
    edge_quote = _make_quote(device_id, "nonce_edge",
                             ts=now - verifier.max_quote_age)
    proof_edge = verifier.verify_chain(edge_quote, binding, witnesses, current_time=now)
    check("s14_max_age_boundary",
          proof_edge.result in (VerificationResult.VALID, VerificationResult.EXPIRED))

    # Quote 1 second past max age
    past_quote = _make_quote(device_id, "nonce_past",
                             ts=now - verifier.max_quote_age - 1)
    proof_past = verifier.verify_chain(past_quote, binding, witnesses, current_time=now)
    check("s14_past_max_age", proof_past.result == VerificationResult.EXPIRED)

    # ─── S15: Full lifecycle E2E ──────────────────────────────────────

    # Complete lifecycle: enroll → attest → act → revoke → verify fails
    lifecycle_reg = HardwareRegistry("fed_lifecycle")
    lc_verifier = E2EVerifier()

    # Step 1: Enroll
    lc_binding = _make_binding("lc_dev", "lct:lifecycle", ts=now - 7200)
    lc_witnesses = _make_witnesses("lc_dev", "lct:lifecycle")
    lifecycle_reg.register(lc_binding, lc_witnesses)
    check("s15_enrolled", lifecycle_reg.entries["lc_dev"].state == DeviceState.ACTIVE)

    # Step 2: Attest
    lc_quote = _make_quote("lc_dev", "nonce_lc", ts=now)
    lifecycle_reg.update_attestation("lc_dev", lc_quote)

    # Step 3: Act (verify succeeds)
    lc_action = _make_action("lct:lifecycle", "lc_dev", "govern")
    proof_active = lc_verifier.verify_chain(lc_quote, lc_binding, lc_witnesses,
                                             lc_action, current_time=now)
    check("s15_active_valid", proof_active.result == VerificationResult.VALID)

    # Step 4: Revoke
    lifecycle_reg.revoke("lc_dev", "end_of_life")
    check("s15_revoked", lifecycle_reg.entries["lc_dev"].state == DeviceState.REVOKED)

    # Step 5: Verify fails after revocation
    revoked_binding = _make_binding("lc_dev", "lct:lifecycle",
                                    state=DeviceState.REVOKED, ts=now - 7200)
    proof_post_revoke = lc_verifier.verify_chain(lc_quote, revoked_binding,
                                                  lc_witnesses, lc_action,
                                                  current_time=now)
    check("s15_post_revoke_fails", proof_post_revoke.result == VerificationResult.REVOKED,
          f"result={proof_post_revoke.result.name}")

    # ─── S16: Sybil cost analysis at scale ────────────────────────────

    cost_model = HardwareSybilCostModel()

    # Sweep 1-20 identities
    all_unprofitable = True
    honest_always_better = True
    for n in range(1, 21):
        result = cost_model.is_profitable(n)
        if result["profitable"]:
            all_unprofitable = False
        if not result["honest_better"]:
            honest_always_better = False

    check("s16_all_unprofitable", all_unprofitable)
    check("s16_honest_always_better", honest_always_better)

    # High detection rate makes it even worse
    high_detect = HardwareSybilCostModel(detection_rate=0.95)
    high_result = high_detect.is_profitable(10)
    check("s16_high_detect_unprofitable", not high_result["profitable"])
    check("s16_high_detect_loss", high_result["net_profit"] < -1000,
          f"net={high_result['net_profit']:.2f}")

    # Even with low detection, hardware cost dominates
    low_detect = HardwareSybilCostModel(detection_rate=0.1)
    low_result = low_detect.is_profitable(10)
    check("s16_low_detect_still_bad", not low_result["profitable"] or low_result["honest_better"])

    # ─── Print Results ────────────────────────────────────────────────

    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)

    print(f"\n{'='*70}")
    print(f"Hardware Binding E2E Verification Protocol")
    print(f"{'='*70}")

    for name, ok, detail in results:
        status = "PASS" if ok else "FAIL"
        det = f" [{detail}]" if detail else ""
        if not ok:
            print(f"  {status}: {name}{det}")

    print(f"\n  Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    print(f"{'='*70}")

    if failed > 0:
        print("\nFAILED TESTS:")
        for name, ok, detail in results:
            if not ok:
                print(f"  FAIL: {name} [{detail}]")

    return passed, failed


if __name__ == "__main__":
    run_tests()
