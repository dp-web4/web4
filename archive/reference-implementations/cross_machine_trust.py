"""
Cross-Machine Trust Verification — Reference Implementation
=============================================================

Simulates the CMTVP (Cross-Machine Trust Verification Protocol)
using Web4Entity instances to represent hardware-bound entities
on different machines.

Demonstrates:
1. Discovery — LCT exchange between entities
2. Mutual AVP — Both sides prove aliveness
3. Trust Bridge — Relationship entity with health tracking
4. Witnessed Pairing — Third-party attestation of the bridge
5. Bridge Heartbeat — Ongoing trust maintenance
6. Trust Decay — What happens when a bridge degrades

Uses the fractal DNA pattern: the bridge itself is a Web4Entity.

Date: 2026-02-19
Spec: docs/strategy/cross-machine-trust-verification-protocol.md
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict
from enum import Enum

from web4_entity import (
    Web4Entity, EntityType, R6Request, R6Result, R6Decision,
    T3Tensor, V3Tensor, ATPBudget, WitnessRecord, MetabolicState
)


# ═══════════════════════════════════════════════════════════════
# Hardware Simulation — Represents different machines
# ═══════════════════════════════════════════════════════════════

class HardwareType(str, Enum):
    TPM2 = "tpm2"
    TRUSTZONE = "trustzone"
    SOFTWARE = "software"


@dataclass
class SimulatedHardware:
    """Simulates a hardware security module on a specific machine."""
    machine_name: str
    hardware_type: HardwareType
    trust_ceiling: float

    # Simulated key material
    _private_key: str = field(default_factory=lambda: uuid.uuid4().hex)
    _public_key: str = ""
    _pcr_values: Dict[int, str] = field(default_factory=dict)

    def __post_init__(self):
        self._public_key = hashlib.sha256(
            f"pub:{self._private_key}".encode()
        ).hexdigest()
        # Simulated PCR values (boot chain measurements)
        if self.hardware_type == HardwareType.TPM2:
            self._pcr_values = {
                0: hashlib.sha256(f"{self.machine_name}:bios".encode()).hexdigest()[:16],
                4: hashlib.sha256(f"{self.machine_name}:boot".encode()).hexdigest()[:16],
                7: hashlib.sha256(f"{self.machine_name}:secboot".encode()).hexdigest()[:16],
            }
        elif self.hardware_type == HardwareType.TRUSTZONE:
            self._pcr_values = {
                0: hashlib.sha256(f"{self.machine_name}:bl1".encode()).hexdigest()[:16],
                1: hashlib.sha256(f"{self.machine_name}:optee".encode()).hexdigest()[:16],
            }

    def sign(self, data: bytes) -> str:
        """Simulate hardware-bound signing."""
        return hashlib.sha256(
            self._private_key.encode() + data
        ).hexdigest()

    def verify(self, data: bytes, signature: str, public_key: str) -> bool:
        """Verify a signature (in simulation, we trust the hash chain)."""
        # In real implementation, this uses ECDSA/EdDSA verification
        # In simulation, we check that the signature matches the public key's private key
        # Since we don't have the private key, we verify structurally
        return len(signature) == 64  # Simplified: signature looks valid

    def get_attestation(self) -> dict:
        """Get hardware attestation (TPM quote or PSA token)."""
        return {
            "hardware_type": self.hardware_type.value,
            "machine": self.machine_name,
            "pcr_values": self._pcr_values,
            "trust_ceiling": self.trust_ceiling,
            "key_non_extractable": self.hardware_type != HardwareType.SOFTWARE,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# ═══════════════════════════════════════════════════════════════
# Discovery Record
# ═══════════════════════════════════════════════════════════════

@dataclass
class DiscoveryRecord:
    """LCT discovery record for cross-machine pairing."""
    lct_id: str
    entity_type: str
    hardware_type: str
    public_key: str
    trust_ceiling: float
    attestation_format: str
    machine_fingerprint: str
    timestamp: str
    signature: str

    @classmethod
    def from_entity(cls, entity: Web4Entity, hardware: SimulatedHardware) -> "DiscoveryRecord":
        record_data = f"{entity.lct_id}:{hardware.hardware_type.value}:{hardware._public_key}"
        return cls(
            lct_id=entity.lct_id,
            entity_type=entity.entity_type.value,
            hardware_type=hardware.hardware_type.value,
            public_key=hardware._public_key,
            trust_ceiling=hardware.trust_ceiling,
            attestation_format=f"{hardware.hardware_type.value}_quote",
            machine_fingerprint=hashlib.sha256(hardware.machine_name.encode()).hexdigest()[:16],
            timestamp=datetime.now(timezone.utc).isoformat(),
            signature=hardware.sign(record_data.encode())
        )


# ═══════════════════════════════════════════════════════════════
# AVP Challenge / Proof (Simplified simulation)
# ═══════════════════════════════════════════════════════════════

@dataclass
class PairingChallenge:
    """AVP challenge with cross-machine pairing context."""
    challenge_id: str
    nonce: str
    verifier_lct_id: str
    target_lct_id: str
    purpose: str
    timestamp: str

    @classmethod
    def create(cls, verifier_lct: str, target_lct: str, purpose: str = "cross-machine-pairing"):
        return cls(
            challenge_id=str(uuid.uuid4())[:8],
            nonce=uuid.uuid4().hex,
            verifier_lct_id=verifier_lct,
            target_lct_id=target_lct,
            purpose=purpose,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def get_canonical_payload(self) -> bytes:
        """Canonical payload that must be signed (prevents relay attacks)."""
        return hashlib.sha256(
            f"AVP-1.1:{self.challenge_id}:{self.nonce}:{self.verifier_lct_id}:{self.target_lct_id}".encode()
        ).digest()


@dataclass
class PairingProof:
    """AVP proof for cross-machine verification."""
    challenge_id: str
    signature: str
    hardware_type: str
    attestation: dict
    timestamp: str


# ═══════════════════════════════════════════════════════════════
# Trust Bridge — The relationship as an entity
# ═══════════════════════════════════════════════════════════════

class BridgeState(str, Enum):
    NEW = "new"
    ACTIVE = "active"
    ESTABLISHED = "established"
    DEGRADED = "degraded"
    BROKEN = "broken"


class TrustBridge(Web4Entity):
    """
    A trust bridge between two entities on different machines.
    The bridge itself is a Web4Entity (INFRASTRUCTURE type),
    following the fractal DNA pattern.
    """

    def __init__(
        self,
        entity_a: Web4Entity,
        entity_b: Web4Entity,
        hardware_a: SimulatedHardware,
        hardware_b: SimulatedHardware,
    ):
        # Bridge is an INFRASTRUCTURE entity
        bridge_name = f"bridge-{entity_a.name}-{entity_b.name}"
        super().__init__(EntityType.INFRASTRUCTURE, bridge_name, atp_allocation=50.0)

        # Endpoints
        self.entity_a = entity_a
        self.entity_b = entity_b
        self.hardware_a = hardware_a
        self.hardware_b = hardware_b

        # Bridge-specific state
        self.bridge_state = BridgeState.NEW
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.pairing_record: Optional[dict] = None
        self.heartbeat_log: List[dict] = []
        self.witness_records: List[dict] = []

        # Register relationships
        self.relationships[entity_a.lct_id] = "bridge_endpoint"
        self.relationships[entity_b.lct_id] = "bridge_endpoint"
        entity_a.relationships[self.lct_id] = "bridged_via"
        entity_b.relationships[self.lct_id] = "bridged_via"

    def execute_pairing(self) -> dict:
        """
        Execute the mutual AVP pairing ceremony.

        Both entities challenge each other simultaneously,
        prove aliveness, and exchange attestations.
        """
        print(f"\n  Pairing: {self.entity_a.name} ({self.hardware_a.hardware_type.value}) "
              f"↔ {self.entity_b.name} ({self.hardware_b.hardware_type.value})")

        # Phase 1: Mutual challenges
        challenge_a_to_b = PairingChallenge.create(
            self.entity_a.lct_id, self.entity_b.lct_id
        )
        challenge_b_to_a = PairingChallenge.create(
            self.entity_b.lct_id, self.entity_a.lct_id
        )

        # Phase 2: Both sign canonical payloads
        proof_a = PairingProof(
            challenge_id=challenge_b_to_a.challenge_id,
            signature=self.hardware_a.sign(challenge_b_to_a.get_canonical_payload()),
            hardware_type=self.hardware_a.hardware_type.value,
            attestation=self.hardware_a.get_attestation(),
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        proof_b = PairingProof(
            challenge_id=challenge_a_to_b.challenge_id,
            signature=self.hardware_b.sign(challenge_a_to_b.get_canonical_payload()),
            hardware_type=self.hardware_b.hardware_type.value,
            attestation=self.hardware_b.get_attestation(),
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Phase 3: Verify proofs
        a_verified = self.hardware_a.verify(
            challenge_b_to_a.get_canonical_payload(),
            proof_a.signature,
            self.hardware_a._public_key
        )
        b_verified = self.hardware_b.verify(
            challenge_a_to_b.get_canonical_payload(),
            proof_b.signature,
            self.hardware_b._public_key
        )

        # Phase 4: Compare attestations
        a_attestation_valid = proof_a.attestation["key_non_extractable"]
        b_attestation_valid = proof_b.attestation["key_non_extractable"]

        success = a_verified and b_verified

        # Build pairing record
        self.pairing_record = {
            "pairing_id": f"pair:web4:{self.entity_a.lct_id.split(':')[-1]}:{self.entity_b.lct_id.split(':')[-1]}",
            "status": "verified" if success else "failed",
            "initiator": {
                "lct_id": self.entity_a.lct_id,
                "hardware_type": self.hardware_a.hardware_type.value,
                "attestation_verified": a_attestation_valid,
                "avp_valid": a_verified
            },
            "responder": {
                "lct_id": self.entity_b.lct_id,
                "hardware_type": self.hardware_b.hardware_type.value,
                "attestation_verified": b_attestation_valid,
                "avp_valid": b_verified
            },
            "trust_ceiling": min(self.hardware_a.trust_ceiling, self.hardware_b.trust_ceiling),
            "trust_level": 0.3 if success else 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if success:
            self.bridge_state = BridgeState.ACTIVE
            self.consecutive_successes = 1

            # Mutual witnessing
            self.entity_a.witness(self.entity_b, "cross_machine_pairing")

        print(f"    Mutual AVP: {'VERIFIED' if success else 'FAILED'}")
        print(f"    {self.entity_a.name}: attestation={'valid' if a_attestation_valid else 'invalid'}")
        print(f"    {self.entity_b.name}: attestation={'valid' if b_attestation_valid else 'invalid'}")
        print(f"    Trust ceiling: {self.pairing_record['trust_ceiling']}")
        print(f"    Trust level: {self.pairing_record['trust_level']} (unwitnessed)")
        print(f"    Bridge state: {self.bridge_state.value}")

        return self.pairing_record

    def add_witness(self, witness: Web4Entity):
        """Add a witness to the pairing, elevating trust."""
        if self.pairing_record is None:
            raise ValueError("Cannot witness unpaired bridge")

        # Witness observes both endpoints
        witness.witness(self.entity_a, "bridge_witness")
        witness.witness(self.entity_b, "bridge_witness")
        witness.witness(self, "bridge_witness")

        witness_record = {
            "witness_lct": witness.lct_id,
            "witness_type": witness.entity_type.value,
            "witness_t3": witness.t3.composite(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.witness_records.append(witness_record)

        # Elevate trust based on witness quality
        trust_boost = min(0.3, witness.t3.composite() * 0.4)
        old_trust = self.pairing_record["trust_level"]
        self.pairing_record["trust_level"] = min(0.95, old_trust + trust_boost)

        print(f"\n  Witness added: {witness.name} (T3={witness.t3.composite():.3f})")
        print(f"    Trust: {old_trust:.2f} → {self.pairing_record['trust_level']:.2f}")

    def heartbeat(self, success: bool = True) -> dict:
        """
        Run a bridge heartbeat (periodic mutual AVP).
        In simulation, success is parameterized.
        """
        if success:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0

        # State transitions
        if self.consecutive_failures >= 5:
            self.bridge_state = BridgeState.BROKEN
        elif self.consecutive_failures > 0:
            self.bridge_state = BridgeState.DEGRADED
        elif self.consecutive_successes >= 10:
            self.bridge_state = BridgeState.ESTABLISHED
        elif self.consecutive_successes > 0:
            self.bridge_state = BridgeState.ACTIVE

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": success,
            "consecutive_successes": self.consecutive_successes,
            "consecutive_failures": self.consecutive_failures,
            "bridge_state": self.bridge_state.value,
            "trust_multiplier": self.trust_multiplier
        }
        self.heartbeat_log.append(record)
        return record

    @property
    def trust_multiplier(self) -> float:
        """Trust multiplier based on bridge health."""
        return {
            BridgeState.BROKEN: 0.0,
            BridgeState.DEGRADED: 0.3,
            BridgeState.NEW: 0.5,
            BridgeState.ACTIVE: 0.8,
            BridgeState.ESTABLISHED: 0.95
        }[self.bridge_state]

    @property
    def effective_trust(self) -> float:
        """
        Effective trust through the bridge.
        = bridge_multiplier * min(ceilings) * min(T3 composites)
        """
        if self.pairing_record is None:
            return 0.0

        ceiling = self.pairing_record["trust_ceiling"]
        t3_min = min(self.entity_a.t3.composite(), self.entity_b.t3.composite())
        return self.trust_multiplier * ceiling * t3_min

    def bridge_status(self) -> dict:
        """Complete bridge status."""
        return {
            "bridge_lct": self.lct_id,
            "state": self.bridge_state.value,
            "endpoints": {
                "a": {"lct": self.entity_a.lct_id, "name": self.entity_a.name,
                       "hardware": self.hardware_a.hardware_type.value},
                "b": {"lct": self.entity_b.lct_id, "name": self.entity_b.name,
                       "hardware": self.hardware_b.hardware_type.value},
            },
            "trust_multiplier": self.trust_multiplier,
            "effective_trust": round(self.effective_trust, 4),
            "consecutive_successes": self.consecutive_successes,
            "consecutive_failures": self.consecutive_failures,
            "witnesses": len(self.witness_records),
            "heartbeats": len(self.heartbeat_log),
            "pairing_trust_level": self.pairing_record["trust_level"] if self.pairing_record else 0.0
        }


# ═══════════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════════

def demo():
    """Demonstrate cross-machine trust verification."""
    print("=" * 65)
    print("  CROSS-MACHINE TRUST VERIFICATION PROTOCOL (CMTVP)")
    print("  Simulating Legion (TPM2) ↔ Thor (TrustZone)")
    print("=" * 65)

    # ─── Create machines ───
    print("\n--- Machine Setup ---")
    legion_hw = SimulatedHardware("legion", HardwareType.TPM2, trust_ceiling=1.0)
    thor_hw = SimulatedHardware("thor", HardwareType.TRUSTZONE, trust_ceiling=1.0)
    print(f"  Legion: {legion_hw.hardware_type.value}, ceiling={legion_hw.trust_ceiling}")
    print(f"  Thor:   {thor_hw.hardware_type.value}, ceiling={thor_hw.trust_ceiling}")

    # ─── Create entities ───
    print("\n--- Entity Creation ---")
    legion_agent = Web4Entity(EntityType.AI, "sage-legion", atp_allocation=200.0)
    thor_agent = Web4Entity(EntityType.AI, "sage-thor", atp_allocation=200.0)
    print(f"  {legion_agent}")
    print(f"  {thor_agent}")

    # ─── Phase 1: Discovery ───
    print("\n--- Phase 1: Discovery ---")
    disc_legion = DiscoveryRecord.from_entity(legion_agent, legion_hw)
    disc_thor = DiscoveryRecord.from_entity(thor_agent, thor_hw)
    print(f"  Legion discovery: lct={disc_legion.lct_id[:30]}... hw={disc_legion.hardware_type}")
    print(f"  Thor discovery:   lct={disc_thor.lct_id[:30]}... hw={disc_thor.hardware_type}")

    # ─── Phase 2: Pairing (Mutual AVP) ───
    print("\n--- Phase 2: Pairing (Mutual AVP) ---")
    bridge = TrustBridge(legion_agent, thor_agent, legion_hw, thor_hw)
    pairing = bridge.execute_pairing()

    # ─── Phase 3: Witnessed Pairing ───
    print("\n--- Phase 3: Witnessed Pairing ---")

    # Create a society as witness (high trust)
    society = Web4Entity(EntityType.SOCIETY, "web4-federation", atp_allocation=500.0)
    society.t3 = T3Tensor(talent=0.9, training=0.85, temperament=0.9)
    bridge.add_witness(society)

    # Create a human operator as witness
    human = Web4Entity(EntityType.HUMAN, "dp-operator", atp_allocation=100.0)
    human.t3 = T3Tensor(talent=0.8, training=0.7, temperament=0.9)
    bridge.add_witness(human)

    # ─── Phase 4: Bridge Heartbeat ───
    print("\n--- Phase 4: Bridge Heartbeat (Simulating 15 cycles) ---")
    for i in range(15):
        # Simulate: first 12 succeed, then 3 fail
        success = i < 12
        hb = bridge.heartbeat(success=success)
        if i in [0, 4, 9, 11, 12, 14]:  # Print selected cycles
            print(f"  Cycle {i+1:2d}: {'OK' if success else 'FAIL'} | "
                  f"state={hb['bridge_state']:12s} | "
                  f"trust_mult={hb['trust_multiplier']:.2f} | "
                  f"effective={bridge.effective_trust:.4f}")

    # ─── Phase 5: Bridge Recovery ───
    print("\n--- Phase 5: Bridge Recovery ---")
    print(f"  Bridge degraded: state={bridge.bridge_state.value}")
    print("  Recovering with successful heartbeats...")
    for i in range(5):
        hb = bridge.heartbeat(success=True)
    print(f"  After recovery: state={bridge.bridge_state.value}, "
          f"trust_mult={bridge.trust_multiplier:.2f}")

    # ─── Cross-Bridge Action ───
    print("\n--- Cross-Bridge Action ---")
    # Legion agent uses the bridge to delegate work to Thor
    request = R6Request(
        rules="federation-policy-v1",
        role=legion_agent.lct_id,
        request="delegate_analysis",
        reference=f"bridge:{bridge.lct_id}",
        resource_estimate=20.0
    )
    result = legion_agent.act(request)
    print(f"  Legion delegates via bridge: {result.decision.value}")
    print(f"  Effective cross-machine trust: {bridge.effective_trust:.4f}")

    # ─── Software Bridge Comparison ───
    print("\n--- Software Bridge (Lower Trust Ceiling) ---")
    cbp_hw = SimulatedHardware("cbp-wsl2", HardwareType.SOFTWARE, trust_ceiling=0.85)
    cbp_agent = Web4Entity(EntityType.AI, "sage-cbp", atp_allocation=200.0)
    sw_bridge = TrustBridge(legion_agent, cbp_agent, legion_hw, cbp_hw)
    sw_pairing = sw_bridge.execute_pairing()
    for _ in range(10):
        sw_bridge.heartbeat(success=True)
    print(f"  Software bridge effective trust: {sw_bridge.effective_trust:.4f}")
    print(f"  Hardware bridge effective trust: {bridge.effective_trust:.4f}")
    print(f"  Difference: hardware trust is {bridge.effective_trust / max(0.001, sw_bridge.effective_trust):.2f}x stronger")

    # ─── Final Summary ───
    print("\n--- Final Bridge Status ---")
    for b, name in [(bridge, "Legion↔Thor (HW↔HW)"), (sw_bridge, "Legion↔CBP (HW↔SW)")]:
        s = b.bridge_status()
        print(f"\n  {name}:")
        print(f"    State: {s['state']}")
        print(f"    Trust multiplier: {s['trust_multiplier']:.2f}")
        print(f"    Effective trust: {s['effective_trust']:.4f}")
        print(f"    Trust ceiling: {b.pairing_record['trust_ceiling']:.2f}")
        print(f"    Witnesses: {s['witnesses']}")
        print(f"    Heartbeats: {s['heartbeats']}")

    print("\n" + "=" * 65)
    print("  Trust bridges connect fractal DNA cells across machines.")
    print("  Hardware ↔ Hardware: full trust ceiling (1.0)")
    print("  Hardware ↔ Software: reduced ceiling (0.85)")
    print("  The bridge IS the synthon boundary layer.")
    print("=" * 65)


if __name__ == "__main__":
    demo()
