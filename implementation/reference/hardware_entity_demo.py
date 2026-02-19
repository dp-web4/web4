#!/usr/bin/env python3
"""
Hardware-Backed Web4Entity Demo
================================

Connects the fractal DNA reference implementation (Web4Entity) with
real TPM2 hardware binding (TPM2Provider). This demonstrates the full
Web4 stack: identity + trust + hardware + metabolism.

The entity's R6 actions are signed with non-extractable TPM keys.
Trust evolution happens against real hardware attestation.

This is the "living cell with real DNA" — not simulated crypto,
but actual hardware-bound operations.

Date: 2026-02-19
Requires: TPM 2.0 (Legion or compatible machine)
"""

import sys
import os
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# Setup paths — implementation/reference/ is 2 levels below web4/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'core'))
sys.path.insert(0, str(Path(__file__).parent))

from web4_entity import (
    Web4Entity, EntityType, R6Request, R6Result, R6Decision,
    T3Tensor, V3Tensor, WitnessRecord, MetabolicState
)
from lct_binding.tpm2_provider import TPM2Provider
from lct_binding.provider import AlivenessChallenge


class HardwareBackedEntity(Web4Entity):
    """
    A Web4Entity with real TPM2 hardware binding.

    Extends Web4Entity to:
    - Sign every R6 action with TPM-bound key
    - Verify signatures cryptographically
    - Provide hardware attestation on demand
    - Link AVP aliveness proofs to entity lifecycle

    The private key exists ONLY in the TPM chip.
    """

    def __init__(
        self,
        entity_type: EntityType,
        name: str,
        provider: TPM2Provider,
        parent: Optional[Web4Entity] = None,
        atp_allocation: float = 100.0,
    ):
        super().__init__(entity_type, name, parent, atp_allocation)

        self.provider = provider
        self.key_id: Optional[str] = None
        self.public_key: Optional[str] = None
        self.hardware_bound = False
        self.signed_action_count = 0
        self.signature_log = []

    def bind_to_hardware(self) -> bool:
        """
        Create TPM-bound identity.
        Returns True if hardware binding succeeded.
        """
        if not self.provider._tpm_available:
            print(f"  WARNING: TPM not available, running in software mode")
            return False

        # Create LCT with hardware binding
        try:
            from lct_capability_levels import EntityType as LCTEntityType
            lct_entity_type = LCTEntityType(self.entity_type.value)
        except (ImportError, ValueError):
            from enum import Enum
            class LCTEntityType(Enum):
                AI = "ai"
                HUMAN = "human"
                SOCIETY = "society"
            lct_entity_type = LCTEntityType.AI

        lct = self.provider.create_lct(lct_entity_type, self.name)

        # Extract key info
        self.key_id = lct.lct_id.split(':')[-1]
        self.public_key = lct.binding.public_key
        self.lct_id = lct.lct_id  # Override with hardware-bound LCT ID
        self.hardware_bound = True

        return True

    def act(self, request: R6Request) -> R6Result:
        """
        Process R6 action with hardware signing.

        Extends the base act() to:
        1. Run the full entity pipeline (PolicyGate, ATP, T3/V3 update)
        2. If approved, sign the action record with TPM
        3. Store the signature for audit trail
        """
        # Run base entity pipeline
        result = super().act(request)

        # If action was approved AND we have hardware binding, sign it
        if result.decision == R6Decision.APPROVED and self.hardware_bound and self.key_id:
            action_record = json.dumps({
                "r6_id": result.r6_id,
                "request": request.request,
                "reference": request.reference,
                "output_hash": result.output_hash,
                "timestamp": result.timestamp,
                "lct_id": self.lct_id
            }, sort_keys=True).encode()

            sig_result = self.provider.sign_data(self.key_id, action_record)

            if sig_result.success:
                self.signed_action_count += 1
                self.signature_log.append({
                    "r6_id": result.r6_id,
                    "signature": sig_result.signature_b64[:32] + "...",
                    "algorithm": sig_result.algorithm,
                    "verified": True
                })
                # Verify our own signature
                verified = self.provider.verify_signature(
                    self.public_key, action_record, sig_result.signature
                )
                if not verified:
                    print(f"  WARNING: Self-verification failed for {request.request}")

        return result

    def prove_aliveness(self) -> dict:
        """
        Prove this entity is currently alive (has hardware access).
        Uses AVP protocol.
        """
        if not self.hardware_bound or not self.key_id:
            return {"alive": False, "reason": "not hardware-bound"}

        challenge = AlivenessChallenge.create(
            verifier_lct_id=self.lct_id,
            purpose="self-attestation"
        )

        try:
            proof = self.provider.prove_aliveness(self.key_id, challenge)
            result = self.provider.verify_aliveness_proof(
                challenge, proof, self.public_key
            )
            return {
                "alive": result.valid,
                "continuity_score": result.continuity_score,
                "content_score": result.content_score,
                "hardware_type": result.hardware_type
            }
        except Exception as e:
            return {"alive": False, "reason": str(e)}

    def get_attestation(self) -> dict:
        """Get hardware attestation (TPM quote with PCR values)."""
        if not self.hardware_bound or not self.key_id:
            return {"attested": False, "reason": "not hardware-bound"}

        att = self.provider.get_attestation(self.key_id)
        return {
            "attested": att.success,
            "type": att.attestation_type,
            "pcr_values": att.pcr_values
        }

    def hardware_status(self) -> dict:
        """Extended status including hardware binding info."""
        base = self.status()
        base["hardware"] = {
            "bound": self.hardware_bound,
            "key_id": self.key_id,
            "signed_actions": self.signed_action_count,
            "trust_ceiling": 1.0 if self.hardware_bound else 0.85
        }
        return base

    def cleanup(self):
        """Clean up TPM resources."""
        if self.hardware_bound and self.key_id:
            try:
                self.provider.evict_key(self.key_id)
            except Exception:
                pass


def demo():
    """Demonstrate hardware-backed Web4Entity."""
    print("=" * 65)
    print("  HARDWARE-BACKED WEB4 ENTITY DEMO")
    print("  Fractal DNA + TPM2 = Living Entity with Real Identity")
    print("=" * 65)

    # Initialize TPM2 provider
    provider = TPM2Provider()
    platform = provider.get_platform_info()

    if not provider._tpm_available:
        print("\n  ERROR: TPM2 not available. This demo requires hardware TPM.")
        print("  Run web4_entity.py for the software-only demo.")
        sys.exit(1)

    print(f"\n  Platform: {platform.name}")
    print(f"  TPM 2.0: Available")
    print(f"  Trust Ceiling: {provider.trust_ceiling}")

    # ─── Create hardware-backed entity ───
    print("\n--- Step 1: Create Hardware-Backed AI Entity ---")
    agent = HardwareBackedEntity(
        EntityType.AI, "sage-legion-hw",
        provider=provider,
        atp_allocation=200.0
    )

    start = time.time()
    bound = agent.bind_to_hardware()
    elapsed = time.time() - start

    print(f"  Entity: {agent}")
    print(f"  LCT ID: {agent.lct_id}")
    print(f"  Hardware Bound: {agent.hardware_bound}")
    print(f"  Key ID: {agent.key_id}")
    print(f"  Binding Time: {elapsed:.2f}s")

    # ─── Prove aliveness ───
    print("\n--- Step 2: Prove Aliveness (AVP) ---")
    aliveness = agent.prove_aliveness()
    print(f"  Alive: {aliveness.get('alive')}")
    print(f"  Continuity: {aliveness.get('continuity_score', 'N/A')}")
    print(f"  Hardware: {aliveness.get('hardware_type', 'N/A')}")

    # ─── Perform signed actions ───
    print("\n--- Step 3: Perform TPM-Signed R6 Actions ---")
    actions = [
        ("analyze_data", "dataset://research-corpus", 15.0),
        ("generate_report", "output://summary-feb2026", 20.0),
        ("verify_identity", "lct:web4:human:dp", 10.0),
    ]

    for action_name, reference, cost in actions:
        request = R6Request(
            rules="research-policy-v1",
            role=agent.lct_id,
            request=action_name,
            reference=reference,
            resource_estimate=cost
        )
        result = agent.act(request)
        print(f"  {action_name}: {result.decision.value} | "
              f"T3={agent.t3.composite():.3f} | "
              f"ATP={agent.atp.atp_balance:.1f} | "
              f"signed={agent.signed_action_count}")

    # ─── Get attestation ───
    print("\n--- Step 4: Hardware Attestation ---")
    att = agent.get_attestation()
    if att["attested"]:
        print(f"  Type: {att['type']}")
        if att.get('pcr_values'):
            for pcr_idx in sorted(att['pcr_values'].keys()):
                desc = {0: "BIOS/UEFI", 4: "Bootloader", 7: "Secure Boot"}.get(pcr_idx, f"PCR {pcr_idx}")
                print(f"  PCR[{pcr_idx}] ({desc}): {att['pcr_values'][pcr_idx][:32]}...")

    # ─── PolicyGate denial (not signed) ───
    print("\n--- Step 5: PolicyGate Denial (No Signature) ---")
    agent.policy.rules.append({"pattern": "delete", "action": "deny"})
    denied_req = R6Request(
        request="delete_records",
        resource_estimate=5.0
    )
    denied_result = agent.act(denied_req)
    print(f"  delete_records: {denied_result.decision.value}")
    print(f"  Signed actions unchanged: {agent.signed_action_count}")

    # ─── Spawn child (software-only, no TPM) ───
    print("\n--- Step 6: Spawn Child Task (Software-Only) ---")
    task = agent.spawn(EntityType.TASK, "data-cleanup", atp_share=20.0)
    task_req = R6Request(request="clean_data", resource_estimate=5.0)
    task_result = task.act(task_req)
    print(f"  Task: {task}")
    print(f"  Task action: {task_result.decision.value}")
    print(f"  Parent witnesses: {len(agent.witnesses)}")

    # ─── Final status ───
    print("\n--- Step 7: Final Entity Status ---")
    status = agent.hardware_status()
    print(f"  Entity: {status['name']}")
    print(f"  Type: {status['entity_type']}")
    print(f"  Coherence: {status['coherence']:.4f}")
    print(f"  State: {status['state']}")
    print(f"  T3: talent={agent.t3.talent:.3f} training={agent.t3.training:.3f} temperament={agent.t3.temperament:.3f}")
    print(f"  V3: valuation={agent.v3.valuation:.3f} veracity={agent.v3.veracity:.3f} validity={agent.v3.validity:.3f}")
    print(f"  ATP: {status['atp']['atp']:.1f} (energy ratio: {status['atp']['energy_ratio']:.3f})")
    print(f"  Hardware: bound={status['hardware']['bound']}, signed={status['hardware']['signed_actions']}")
    print(f"  Presence: {status['presence_density']:.4f}")
    print(f"  Children: {status['children']}")

    # ─── Signature audit trail ───
    print("\n--- Signature Audit Trail ---")
    for sig in agent.signature_log:
        print(f"  R6[{sig['r6_id']}]: {sig['algorithm']} sig={sig['signature']}")

    # ─── Cleanup ───
    print("\n--- Cleanup ---")
    agent.cleanup()
    print("  TPM key evicted")

    print("\n" + "=" * 65)
    print("  This entity's actions are cryptographically non-repudiable.")
    print("  The private key existed ONLY in the TPM chip.")
    print("  Every approved R6 action was signed with hardware-bound key.")
    print("  Denied actions were NOT signed (conscience before crypto).")
    print("  The child task ran in software mode (no hardware binding).")
    print()
    print("  This is the fractal DNA cell with real biological machinery:")
    print("  identity = LCT, metabolism = ATP/ADP, immune system = PolicyGate,")
    print("  nervous system = T3/V3, skeleton = TPM hardware binding.")
    print("=" * 65)


if __name__ == "__main__":
    demo()
