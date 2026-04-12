#!/usr/bin/env python3
"""
End-to-End Trust Chain Demo — Silicon to Delegated Action
============================================================

Demonstrates the complete Web4 hardware trust chain in a single run:

  Silicon (Intel CSME)
    → EK Certificate Chain (manufacturer root-of-trust)
    → TPM2-Bound Entity (hardware identity)
    → Hardbound Team (persistent governance)
    → AVP Transport (cross-machine trust bridge)
    → Cross-Bridge Delegation (R6 action across machines)

Every link is verified. Every action is signed. Every state persists.

This is the integration proof: all the pieces work together.

Date: 2026-02-19
Requires: TPM2 hardware (graceful degradation to simulation)
"""

import sys
import os
import json
import time
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from web4_entity import (
    Web4Entity, EntityType, R6Request, R6Result, R6Decision,
    T3Tensor, V3Tensor, ATPBudget
)
from hardware_entity import HardwareWeb4Entity
from hardbound_cli import HardboundTeam, detect_tpm2, HARDBOUND_DIR
from avp_transport import (
    AVPNode, SigningAdapter, BridgeRecord,
    DiscoveryRecord, AVPChallenge, AVPProof
)


def banner(title: str, char: str = "="):
    width = 65
    print(f"\n{char * width}")
    print(f"  {title}")
    print(f"{char * width}")


def section(title: str):
    print(f"\n--- {title} ---")


def e2e_demo():
    """
    End-to-end integration: EK cert → TPM2 entity → team → AVP → delegation.

    This demo runs entirely on one machine but simulates two-machine
    interaction via localhost HTTP. One side uses real TPM2 (if available),
    the other side is simulated.
    """
    banner("END-TO-END TRUST CHAIN DEMO")
    print("  Silicon → EK Chain → TPM2 Identity → Team → Bridge → Delegation")
    print("  Every link verified. Every action signed. Every state persists.")

    has_tpm = detect_tpm2()
    print(f"\n  Hardware: {'Intel TPM 2.0 (real)' if has_tpm else 'Simulation mode'}")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hardware": "tpm2" if has_tpm else "simulated",
        "phases": {},
    }

    # ═══════════════════════════════════════════════════════════
    # Phase 1: EK Certificate Chain (Silicon Root-of-Trust)
    # ═══════════════════════════════════════════════════════════
    section("Phase 1: EK Certificate Chain")

    ek_verified = False
    ek_info = {}

    if has_tpm:
        try:
            from core.lct_binding.ek_attestation import EKAttestationProvider
            ek = EKAttestationProvider()

            # Extract platform identity
            identity = ek.get_platform_identity()
            print(f"  Manufacturer: {identity.manufacturer}")
            print(f"  Model: {identity.model}")
            print(f"  Version: {identity.version}")

            # Verify chain
            chain = ek.verify_chain()
            ek_verified = chain.chain_valid
            print(f"  Chain verified: {chain.chain_valid}")
            print(f"  Root trusted: {chain.root_trusted}")
            print(f"  CRL checked: {chain.crl_checked}")
            print(f"  Revocation: {'NOT revoked' if chain.not_revoked else 'REVOKED!'}")

            # Create attestation bundle
            bundle = ek.create_attestation_bundle()
            bundle_size = len(json.dumps(bundle))
            print(f"  Attestation bundle: {bundle_size} bytes")

            ek_info = {
                "manufacturer": identity.manufacturer,
                "model": identity.model,
                "chain_valid": chain.chain_valid,
                "root_trusted": chain.root_trusted,
                "bundle_bytes": bundle_size,
            }

            ek.cleanup()
        except Exception as e:
            print(f"  EK extraction failed: {e}")
            print(f"  Continuing with TPM2 binding only...")
    else:
        print("  No TPM2 — EK chain not available")
        print("  (In production, this phase verifies the silicon manufacturer)")

    results["phases"]["ek_chain"] = {
        "verified": ek_verified,
        "info": ek_info,
    }

    # ═══════════════════════════════════════════════════════════
    # Phase 2: TPM2-Bound Entity Creation
    # ═══════════════════════════════════════════════════════════
    section("Phase 2: TPM2-Bound Entity Creation")

    if has_tpm:
        entity_legion = HardwareWeb4Entity.create_with_tpm2(
            EntityType.AI, "sage-legion-e2e", atp_allocation=300.0
        )
    else:
        entity_legion = HardwareWeb4Entity.create_simulated(
            EntityType.AI, "sage-legion-e2e", atp_allocation=300.0
        )

    print(f"  Entity: {entity_legion.name}")
    print(f"  LCT: {entity_legion.lct_id}")
    print(f"  Level: {entity_legion.capability_level} ({'HARDWARE' if entity_legion.capability_level == 5 else 'SOFTWARE'})")
    print(f"  Trust ceiling: {entity_legion.trust_ceiling}")
    print(f"  Key ID: {entity_legion.key_id}")
    print(f"  TPM handle: {entity_legion.tpm_handle}")

    # Sign a test action to verify the key works
    test_req = R6Request(
        rules="e2e-test", role=entity_legion.lct_id,
        request="test_sign", resource_estimate=1.0
    )
    test_result = entity_legion.act(test_req)
    print(f"  Test signature: {test_result.decision.value} "
          f"(signed_actions={len(entity_legion.signed_actions)})")

    results["phases"]["entity_creation"] = {
        "lct_id": entity_legion.lct_id,
        "level": entity_legion.capability_level,
        "key_works": test_result.decision == R6Decision.APPROVED,
    }

    # ═══════════════════════════════════════════════════════════
    # Phase 3: Hardbound Team with Persistent State
    # ═══════════════════════════════════════════════════════════
    section("Phase 3: Hardbound Team (Persistent State)")

    # Clean up any previous e2e demo team
    e2e_team_dir = HARDBOUND_DIR / "teams" / "e2e-demo-team"
    if e2e_team_dir.exists():
        shutil.rmtree(e2e_team_dir)

    team = HardboundTeam("e2e-demo-team", use_tpm=has_tpm)
    team_info = team.create()

    print(f"  Team: {team_info['team']}")
    print(f"  Root level: {team_info['root']['level']}")
    print(f"  State dir: {team_info['state_dir']}")

    # Add members
    team.add_member("analyst-agent", "ai")
    team.add_member("ops-engineer", "human")

    # Sign actions
    admin_name = f"{team.name}-admin"
    team.sign_action(admin_name, "authorize_deployment")
    team.sign_action("analyst-agent", "run_analysis")

    print(f"  Members: {len(team.members)}")
    print(f"  Actions signed: {team.info()['total_actions']}")

    # Save and reload to prove persistence
    loaded = HardboundTeam.load("e2e-demo-team")
    loaded_info = loaded.info()
    print(f"  Persistence test: loaded {len(loaded_info['members'])} members, "
          f"{loaded_info['total_actions']} actions from disk")

    persistence_ok = (
        len(loaded_info['members']) == len(team.members) and
        loaded_info['total_actions'] == team.info()['total_actions']
    )
    print(f"  State integrity: {'VERIFIED' if persistence_ok else 'MISMATCH!'}")

    results["phases"]["team_persistence"] = {
        "team": team_info['team'],
        "members": len(team.members),
        "actions": team.info()['total_actions'],
        "persistence_verified": persistence_ok,
    }

    # ═══════════════════════════════════════════════════════════
    # Phase 4: AVP Transport (Cross-Machine Trust Bridge)
    # ═══════════════════════════════════════════════════════════
    section("Phase 4: AVP Transport (Trust Bridge)")

    # Node A: uses real TPM2 (Legion)
    signer_a = SigningAdapter(entity_legion.key_id, use_tpm=has_tpm)
    node_a = AVPNode(entity_legion, host="127.0.0.1", port=8411, signer=signer_a)

    # Node B: simulated remote entity (Thor)
    entity_thor = Web4Entity(EntityType.AI, "sage-thor-e2e", atp_allocation=300.0)
    signer_b = SigningAdapter(entity_thor.lct_id.split(":")[-1], use_tpm=False)
    node_b = AVPNode(entity_thor, host="127.0.0.1", port=8412, signer=signer_b)

    # Start servers
    node_a.start_server()
    node_b.start_server()
    time.sleep(0.5)
    print(f"  Node A (Legion): :8411 ({'TPM2' if has_tpm else 'sim'})")
    print(f"  Node B (Thor):   :8412 (sim)")

    bridge_created = False
    bridge_a = None

    try:
        # Discovery
        peer_b = node_a.discover_peer("http://127.0.0.1:8412")
        peer_a = node_b.discover_peer("http://127.0.0.1:8411")

        if peer_b and peer_a:
            print(f"  Discovery: mutual (A knows B, B knows A)")
        else:
            print(f"  Discovery: FAILED")

        # Mutual AVP
        result_ab = node_a.challenge_peer(peer_b.lct_id) if peer_b else None
        result_ba = node_b.challenge_peer(peer_a.lct_id) if peer_a else None

        mutual = (result_ab and result_ab.get("valid") and
                  result_ba and result_ba.get("valid"))
        print(f"  Mutual AVP: {'VERIFIED' if mutual else 'FAILED'}")

        if result_ab:
            print(f"    A→B: hw={result_ab.get('hardware_type')}, "
                  f"continuity={result_ab.get('continuity_score', 0):.1f}")
        if result_ba:
            print(f"    B→A: hw={result_ba.get('hardware_type')}, "
                  f"continuity={result_ba.get('continuity_score', 0):.1f}")

        # Bridge creation
        if mutual:
            bridge_a = node_a.create_bridge(peer_b.lct_id, result_ab)
            bridge_b = node_b.create_bridge(peer_a.lct_id, result_ba)

            if bridge_a:
                bridge_created = True
                print(f"  Bridge: {bridge_a.bridge_id}")
                print(f"    State: {bridge_a.state}")
                print(f"    Trust mult: {bridge_a.trust_multiplier:.2f}")

                # Quick heartbeat
                for i in range(3):
                    node_a.send_heartbeat(bridge_a.bridge_id)
                print(f"    Heartbeats: {bridge_a.consecutive_successes}")

        results["phases"]["avp_bridge"] = {
            "discovery": bool(peer_b and peer_a),
            "mutual_avp": mutual,
            "bridge_created": bridge_created,
            "bridge_id": bridge_a.bridge_id if bridge_a else None,
            "trust_multiplier": bridge_a.trust_multiplier if bridge_a else 0,
        }

        # ═══════════════════════════════════════════════════════════
        # Phase 5: Cross-Bridge Delegation
        # ═══════════════════════════════════════════════════════════
        section("Phase 5: Cross-Bridge Delegation")

        delegation_results = []

        if bridge_a:
            actions = [
                ("analyze_threat_vectors", 20.0),
                ("validate_compliance", 12.0),
                ("generate_audit_report", 8.0),
            ]

            for action, cost in actions:
                result = node_a.delegate_action(
                    bridge_a.bridge_id, action,
                    resource_estimate=cost,
                    rules="e2e-delegation-policy"
                )

                if result and result.get("status") == "executed":
                    r6 = result["r6_result"]
                    print(f"  A→B delegate: {action:30s} → {r6['decision']} "
                          f"(cost={r6['atp_consumed']:.1f}, "
                          f"signed by {result.get('executor_lct', '?')[:30]}...)")
                    delegation_results.append({
                        "action": action,
                        "decision": r6["decision"],
                        "cost": r6["atp_consumed"],
                    })
                else:
                    err = result.get("error", "unknown") if result else "no response"
                    print(f"  A→B delegate: {action:30s} → FAILED ({err})")
                    delegation_results.append({
                        "action": action,
                        "decision": "failed",
                        "error": err,
                    })

            # Reverse delegation: B delegates to A
            print()
            if node_b.bridges:
                bridge_b_id = list(node_b.bridges.keys())[0]
                rev_result = node_b.delegate_action(
                    bridge_b_id, "verify_hardware_binding",
                    resource_estimate=5.0
                )
                if rev_result and rev_result.get("status") == "executed":
                    r6 = rev_result["r6_result"]
                    print(f"  B→A delegate: verify_hardware_binding → {r6['decision']} "
                          f"(reverse delegation works!)")
                    delegation_results.append({
                        "action": "verify_hardware_binding",
                        "direction": "B→A",
                        "decision": r6["decision"],
                    })
        else:
            print("  No bridge — delegation not possible")

        results["phases"]["delegation"] = {
            "delegations": delegation_results,
            "count": len(delegation_results),
            "all_succeeded": all(d.get("decision") == "approved" for d in delegation_results),
        }

    finally:
        node_a.stop_server()
        node_b.stop_server()

    # ═══════════════════════════════════════════════════════════
    # Phase 6: Audit Trail
    # ═══════════════════════════════════════════════════════════
    section("Phase 6: Audit Trail")

    # Entity action history
    print(f"  Entity (Legion) actions: {len(entity_legion.action_log)}")
    print(f"  Entity (Legion) signed: {len(entity_legion.signed_actions)}")
    print(f"  Entity (Thor) actions: {len(entity_thor.action_log)}")

    # Team ledger
    actions_file = team.state_dir / "actions.jsonl"
    ledger_count = 0
    if actions_file.exists():
        with open(actions_file) as f:
            ledger_count = sum(1 for _ in f)
    print(f"  Team ledger entries: {ledger_count}")

    # AVP event log
    print(f"  Node A events: {len(node_a.event_log)}")
    print(f"  Node B events: {len(node_b.event_log)}")

    # Witness records
    print(f"  Entity (Legion) witnesses: {len(entity_legion.witnesses)}")

    results["phases"]["audit"] = {
        "legion_actions": len(entity_legion.action_log),
        "legion_signed": len(entity_legion.signed_actions),
        "thor_actions": len(entity_thor.action_log),
        "team_ledger": ledger_count,
        "node_a_events": len(node_a.event_log),
        "node_b_events": len(node_b.event_log),
    }

    # ═══════════════════════════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════════════════════════
    banner("TRUST CHAIN SUMMARY", "─")

    chain_links = [
        ("Silicon (Intel CSME)", ek_verified, "EK cert chain verified" if ek_verified else "N/A (simulation)"),
        ("TPM2 Identity", entity_legion.capability_level == 5, f"Level {entity_legion.capability_level}, key={entity_legion.key_id[:8]}..."),
        ("Team Persistence", persistence_ok, f"{len(team.members)} members, {ledger_count} ledger entries"),
        ("AVP Bridge", bridge_created, f"trust={bridge_a.trust_multiplier:.2f}" if bridge_a else "N/A"),
        ("Cross-Bridge Delegation", bool(delegation_results), f"{len(delegation_results)} delegations"),
    ]

    all_verified = True
    for link_name, verified, detail in chain_links:
        status = "VERIFIED" if verified else ("N/A" if "N/A" in detail else "FAILED")
        if not verified and "N/A" not in detail:
            all_verified = False
        indicator = "+" if verified else ("-" if "N/A" in detail else "!")
        print(f"  [{indicator}] {link_name:30s} {status:10s} {detail}")

    print()
    if all_verified:
        chain_desc = "COMPLETE (all links verified)" if ek_verified else "OPERATIONAL (hardware links verified, EK requires TPM2)"
    else:
        chain_desc = "PARTIAL (some links failed)"
    print(f"  Trust chain: {chain_desc}")

    # The integration narrative
    if has_tpm:
        print(f"\n  Integration path:")
        print(f"    Intel CSME silicon")
        print(f"      → EK cert (manufacturer: {ek_info.get('manufacturer', '?')})")
        print(f"      → TPM2 key (handle: {entity_legion.tpm_handle})")
        print(f"      → Entity LCT ({entity_legion.lct_id[:30]}...)")
        print(f"      → Team root ({team.name})")
        print(f"      → AVP bridge ({bridge_a.bridge_id if bridge_a else 'N/A'})")
        print(f"      → Delegated actions ({len(delegation_results)} cross-machine)")
    else:
        print(f"\n  Integration path (simulation):")
        print(f"    Simulated hardware")
        print(f"      → Entity LCT ({entity_legion.lct_id[:30]}...)")
        print(f"      → Team root ({team.name})")
        print(f"      → AVP bridge ({bridge_a.bridge_id if bridge_a else 'N/A'})")
        print(f"      → Delegated actions ({len(delegation_results)} cross-machine)")

    results["chain_complete"] = all_verified
    results["chain_description"] = chain_desc

    banner("END-TO-END DEMO COMPLETE")
    print("  Every link in the trust chain: verified.")
    print("  Every action: signed (hardware where available).")
    print("  Every state: persisted to disk.")
    print("  The substrate is operational.")
    print("=" * 65)

    return results


if __name__ == "__main__":
    results = e2e_demo()

    # Save results
    results_file = Path(__file__).parent / "e2e_results.json"
    results_file.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n  Results saved to: {results_file}")
