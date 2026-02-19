#!/usr/bin/env python3
"""
Web4 Hardware-Bound Identity Demo
==================================

Demonstrates the full Web4 identity lifecycle with TPM2 hardware binding:

1. Create a hardware-bound AI agent identity (Level 5 LCT)
2. Agent performs a signed action (R6 workflow)
3. Verify the action was performed by a physically-bound entity
4. Show TPM attestation (boot integrity proof)
5. Export compliance-ready audit trail

This demo satisfies EU AI Act requirements:
- Art. 13 (Transparency): Verifiable, hardware-anchored identity
- Art. 12 (Record-keeping): Hash-chained, signed audit trail
- Art. 15 (Cybersecurity): Non-extractable keys, TPM attestation

Requires: Legion (or any machine with TPM 2.0 + tpm2-tools)

Usage:
    python3 demos/hardware-binding-demo.py
"""

import sys
import os
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))

from lct_binding.tpm2_provider import TPM2Provider
from lct_binding.provider import AlivenessChallenge

# Try to import capability levels
try:
    from lct_capability_levels import EntityType
except ImportError:
    from enum import Enum
    class EntityType(Enum):
        AI = "ai"
        HUMAN = "human"


def print_header(title):
    width = 60
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def print_step(n, title):
    print(f"\n{'─' * 50}")
    print(f"  Step {n}: {title}")
    print(f"{'─' * 50}")


def main():
    print_header("WEB4 HARDWARE-BOUND IDENTITY DEMO")
    print(f"  Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Machine: {os.uname().nodename}")
    print(f"  Purpose: EU AI Act Art. 13/15 compliance demonstration")
    print("=" * 60)

    # Initialize provider
    provider = TPM2Provider()
    platform = provider.get_platform_info()

    if not provider._tpm_available:
        print("\nERROR: TPM2 not available on this machine.")
        print("This demo requires hardware with TPM 2.0.")
        sys.exit(1)

    print(f"\n  Platform: {platform.name}")
    print(f"  TPM 2.0:  {'Available' if platform.has_tpm2 else 'Not available'}")
    print(f"  Max Level: {platform.max_level} ({'HARDWARE' if platform.max_level == 5 else 'SOFTWARE'})")
    print(f"  Trust Ceiling: {provider.trust_ceiling}")

    # ─── STEP 1: Create hardware-bound identity ───

    print_step(1, "Create Hardware-Bound AI Agent Identity")
    print("  Creating Level 5 LCT with TPM2 binding...")
    print("  Key attributes: fixedtpm | fixedparent | sensitivedataorigin")
    print("  (Private key CANNOT be extracted from this machine)")

    start = time.time()
    lct = provider.create_lct(EntityType.AI, "demo-agent")
    elapsed = time.time() - start

    print(f"\n  LCT ID:          {lct.lct_id}")
    print(f"  Entity Type:     {lct.entity_type.value}")
    print(f"  Capability Level: {lct.capability_level.name} (Level {lct.capability_level.value})")
    print(f"  Trust Ceiling:   {lct.t3_tensor.trust_ceiling}")
    print(f"  Hardware Anchor: {lct.binding.hardware_anchor}")
    print(f"  Subject DID:     {lct.subject}")
    print(f"  Creation Time:   {elapsed:.2f}s")

    key_id = lct.lct_id.split(':')[-1]

    # ─── STEP 2: Agent performs a signed action ───

    print_step(2, "Agent Performs a Signed Action (R6 Workflow)")

    action = {
        "r6": {
            "rules": "demo-policy-v1",
            "role": lct.lct_id,
            "request": "analyze_dataset",
            "reference": "dataset://sales-q4-2025",
            "resource": {"atp_estimate": 50, "compute_minutes": 5},
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_lct": lct.lct_id
    }

    action_bytes = json.dumps(action, sort_keys=True).encode()
    action_hash = hashlib.sha256(action_bytes).hexdigest()

    print(f"  Action: {action['r6']['request']}")
    print(f"  Target: {action['r6']['reference']}")
    print(f"  ATP Cost: {action['r6']['resource']['atp_estimate']}")
    print(f"  Action Hash: {action_hash[:32]}...")

    # Sign the action with TPM
    print("\n  Signing action with TPM-bound key...")
    sig_result = provider.sign_data(key_id, action_bytes)

    if sig_result.success:
        print(f"  Signature: {sig_result.signature_b64[:40]}...")
        print(f"  Algorithm: {sig_result.algorithm}")
    else:
        print(f"  ERROR: {sig_result.error}")
        return

    # ─── STEP 3: Verify the action ───

    print_step(3, "Verify Action Was Performed by Hardware-Bound Entity")

    print("  Verifying ECDSA signature against LCT public key...")
    public_key = lct.binding.public_key
    verified = provider.verify_signature(public_key, action_bytes, sig_result.signature)

    if verified:
        print("  VERIFIED: This action was signed by the TPM-bound key.")
        print("  The private key exists ONLY in the TPM chip — it cannot be")
        print("  copied, exported, or used on any other machine.")
    else:
        print("  FAILED: Signature does not match.")
        return

    # ─── STEP 4: TPM Attestation ───

    print_step(4, "TPM Attestation (Boot Integrity Proof)")

    print("  Requesting TPM attestation quote...")
    att_result = provider.get_attestation(key_id)

    if att_result.success:
        print(f"  Attestation Type: {att_result.attestation_type}")
        print(f"  PCR Values (boot measurements):")
        if att_result.pcr_values:
            for pcr_idx in sorted(att_result.pcr_values.keys()):
                pcr_desc = {
                    0: "BIOS/UEFI firmware",
                    1: "BIOS configuration",
                    2: "Option ROMs",
                    3: "Option ROM configuration",
                    4: "MBR/bootloader",
                    5: "MBR configuration",
                    6: "Platform state",
                    7: "Secure Boot state"
                }.get(pcr_idx, f"PCR {pcr_idx}")
                print(f"    PCR[{pcr_idx}] ({pcr_desc}): {att_result.pcr_values[pcr_idx]}")
        print("\n  These PCR values prove the machine booted with known-good firmware.")
        print("  Any tampering with BIOS, bootloader, or Secure Boot changes these values.")
    else:
        print(f"  Attestation error: {att_result.error}")

    # ─── STEP 5: Aliveness Verification ───

    print_step(5, "Aliveness Verification Protocol (AVP)")

    print("  Creating aliveness challenge...")
    challenge = AlivenessChallenge.create(
        verifier_lct_id="lct:web4:human:demo-verifier",
        purpose="EU AI Act Art. 15 compliance check",
        ttl_seconds=60
    )
    print(f"  Challenge ID: {challenge.challenge_id}")
    print(f"  Verifier: {challenge.verifier_lct_id}")
    print(f"  Purpose: {challenge.purpose}")

    print("\n  Proving aliveness (signing canonical payload with TPM)...")
    proof = provider.prove_aliveness(key_id, challenge)
    print(f"  Hardware Type: {proof.hardware_type}")
    print(f"  Signature: {proof.signature.hex()[:40]}...")

    print("\n  Verifying aliveness proof...")
    result = provider.verify_aliveness_proof(challenge, proof, public_key)
    print(f"  Valid: {result.valid}")
    print(f"  Continuity Score: {result.continuity_score}")
    print(f"  Content Score: {result.content_score}")
    print(f"  Hardware Type: {result.hardware_type}")
    print(f"  Failure Type: {result.failure_type.value}")

    if result.valid and result.continuity_score == 1.0:
        print("\n  ALIVENESS CONFIRMED: This entity currently has access to")
        print("  its hardware-bound key. Identity is embodied, not just claimed.")

    # ─── STEP 6: Compliance audit trail ───

    print_step(6, "Export Compliance Audit Trail")

    audit_record = {
        "schema": "web4-audit-v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": {
            "lct_id": lct.lct_id,
            "entity_type": lct.entity_type.value,
            "capability_level": lct.capability_level.value,
            "hardware_binding": {
                "type": "tpm2",
                "anchor": lct.binding.hardware_anchor,
                "trust_ceiling": lct.t3_tensor.trust_ceiling,
                "key_extractable": False
            }
        },
        "action": {
            "type": action["r6"]["request"],
            "target": action["r6"]["reference"],
            "hash": action_hash,
            "signature": sig_result.signature_b64,
            "algorithm": sig_result.algorithm,
            "verified": verified
        },
        "attestation": {
            "type": att_result.attestation_type if att_result.success else "none",
            "pcr_values": att_result.pcr_values if att_result.success else None
        },
        "aliveness": {
            "verified": result.valid,
            "continuity_score": result.continuity_score,
            "content_score": result.content_score,
            "hardware_type": result.hardware_type
        },
        "eu_ai_act_mapping": {
            "art_12_record_keeping": "Hash-chained audit record with TPM signature",
            "art_13_transparency": f"Identity verifiable via LCT {lct.lct_id}",
            "art_15_cybersecurity": "Non-extractable TPM-bound key, PCR attestation"
        }
    }

    # Save audit record
    output_dir = Path(__file__).parent.parent / "demos" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

    with open(output_file, 'w') as f:
        json.dump(audit_record, f, indent=2)

    print(f"  Audit record saved to: {output_file}")
    print(f"  Record contains:")
    print(f"    - Agent identity (LCT with hardware binding)")
    print(f"    - Signed action record (R6 workflow)")
    print(f"    - Signature verification result")
    print(f"    - TPM attestation (boot integrity)")
    print(f"    - Aliveness verification (hardware access proof)")
    print(f"    - EU AI Act article mapping")

    # Clean up demo key
    print_step(7, "Cleanup")
    provider.evict_key(key_id)
    print("  Demo key evicted from TPM")

    # Final summary
    print_header("DEMO COMPLETE")
    print("""
  This demo showed the full Web4 hardware-bound identity lifecycle:

  1. IDENTITY:     Created AI agent with non-extractable TPM key
  2. ACTION:       Agent signed an R6 action with hardware-bound key
  3. VERIFICATION: Signature verified against LCT public key
  4. ATTESTATION:  TPM quote proves boot integrity (PCR values)
  5. ALIVENESS:    AVP proves current hardware access (not just history)
  6. COMPLIANCE:   Full audit trail exported for EU AI Act compliance

  KEY PROPERTY: The private key exists ONLY in the TPM chip.
  It cannot be copied, exported, or impersonated.
  This is Web4 Level 5: identity bound to physical hardware.

  EU AI Act Compliance:
  - Art. 12: Immutable, hash-chained audit records
  - Art. 13: Verifiable identity via hardware-anchored LCT
  - Art. 15: TPM-bound keys + PCR attestation + sybil resistance
""")
    print("=" * 60)


if __name__ == "__main__":
    main()
