#!/usr/bin/env python3
"""
Hardbound CLI — Enterprise Team Management with Hardware-Backed Identity
=========================================================================

Command-line tool for creating and managing Web4 teams (societies)
with TPM2-backed identity. Wraps HardwareWeb4Entity and the
simulations/team infrastructure.

Commands:
    team create <name>         — Create a new team with hardware-bound root
    team info                  — Show team status and member list
    team add-member <name> <type> — Add a member to the team
    entity create <name> <type> — Create a standalone hardware entity
    entity info <name>         — Show entity status
    entity sign <name> <action> — Sign an R6 action with hardware key
    avp prove <name>           — Run AVP aliveness proof
    avp attest                 — Get TPM2 attestation
    ek info                    — Show EK certificate chain info
    ek verify                  — Verify EK certificate chain
    status                     — Show full system status

Enterprise Terminology Bridge:
    Society    → Team
    Citizen    → Member
    Law Oracle → Admin
    Blockchain → Ledger
    Birth Cert → Onboarding Record

Date: 2026-02-19
"""

import sys
import os
import json
import argparse
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


def detect_tpm2() -> bool:
    """Check if TPM2 is available."""
    try:
        from core.lct_binding.tpm2_provider import TPM2Provider
        provider = TPM2Provider()
        info = provider.get_platform_info()
        return info.has_tpm2
    except Exception:
        return False


def create_entity(name: str, entity_type: str, use_tpm: bool = True) -> HardwareWeb4Entity:
    """Create a hardware-backed entity."""
    etype = EntityType(entity_type)
    if use_tpm and detect_tpm2():
        return HardwareWeb4Entity.create_with_tpm2(etype, name)
    else:
        return HardwareWeb4Entity.create_simulated(etype, name)


class HardboundTeam:
    """
    A Hardbound team: enterprise wrapper around Web4Entity hierarchy.

    The team root is a SOCIETY-type HardwareWeb4Entity.
    Members are child entities (HUMAN, AI, ORGANIZATION, etc.).
    Admin is a HUMAN-type hardware-bound entity with elevated privileges.
    """

    def __init__(self, name: str, use_tpm: bool = True):
        self.name = name
        self.use_tpm = use_tpm and detect_tpm2()
        self.root: HardwareWeb4Entity = None
        self.admin: HardwareWeb4Entity = None
        self.members: dict = {}  # name → HardwareWeb4Entity
        self.action_log: list = []
        self.created_at = datetime.now(timezone.utc).isoformat()

    def create(self) -> dict:
        """Create the team with hardware-bound root and admin."""
        # Create team root (SOCIETY type)
        if self.use_tpm:
            self.root = HardwareWeb4Entity.create_with_tpm2(
                EntityType.SOCIETY, self.name, atp_allocation=500.0
            )
        else:
            self.root = HardwareWeb4Entity.create_simulated(
                EntityType.SOCIETY, self.name, atp_allocation=500.0
            )

        # Create admin (HUMAN type, hardware-bound)
        if self.use_tpm:
            self.admin = HardwareWeb4Entity.create_with_tpm2(
                EntityType.HUMAN, f"{self.name}-admin", atp_allocation=200.0
            )
        else:
            self.admin = HardwareWeb4Entity.create_simulated(
                EntityType.HUMAN, f"{self.name}-admin", atp_allocation=200.0
            )

        # Root witnesses admin (binding ceremony)
        self.root.witness(self.admin, "admin_binding")
        self.members[f"{self.name}-admin"] = self.admin

        return self.info()

    def add_member(self, name: str, entity_type: str) -> dict:
        """Add a member to the team."""
        etype = EntityType(entity_type)

        # Software entities can be spawned as children of the root
        # Hardware entities need their own TPM key
        if entity_type in ("human",) and self.use_tpm:
            member = HardwareWeb4Entity.create_with_tpm2(
                etype, name, atp_allocation=100.0
            )
        elif etype in (EntityType.AI, EntityType.TASK, EntityType.SERVICE):
            # AI/Task/Service entities are software spawns from root
            member = self.root.spawn(etype, name, atp_share=50.0)
            self.members[name] = member
            return {
                "name": name,
                "type": entity_type,
                "lct_id": member.lct_id,
                "level": 4,
                "binding": "software (spawned child)",
                "parent": self.root.lct_id,
            }
        else:
            member = HardwareWeb4Entity.create_simulated(
                etype, name, atp_allocation=100.0
            )

        # Root witnesses the new member
        self.root.witness(member, "member_binding")
        self.members[name] = member

        return {
            "name": name,
            "type": entity_type,
            "lct_id": member.lct_id if hasattr(member, 'lct_id') else "unknown",
            "level": getattr(member, 'capability_level', 4),
            "binding": "hardware" if isinstance(member, HardwareWeb4Entity) and hasattr(member, 'tpm_handle') else "software",
        }

    def info(self) -> dict:
        """Get team status."""
        result = {
            "team": self.name,
            "created": self.created_at,
            "hardware_binding": "tpm2" if self.use_tpm else "simulated",
        }

        if self.root:
            result["root"] = {
                "lct_id": self.root.lct_id,
                "level": self.root.capability_level,
                "trust_ceiling": self.root.trust_ceiling,
                "coherence": round(self.root.coherence, 4),
                "atp": round(self.root.atp.atp_balance, 1),
                "handle": self.root.tpm_handle,
            }

        if self.admin:
            result["admin"] = {
                "lct_id": self.admin.lct_id,
                "level": self.admin.capability_level,
                "coherence": round(self.admin.coherence, 4),
            }

        result["members"] = []
        for name, member in self.members.items():
            result["members"].append({
                "name": name,
                "type": member.entity_type.value if hasattr(member, 'entity_type') else "unknown",
                "level": getattr(member, 'capability_level', 4),
                "coherence": round(member.coherence, 4),
            })

        return result

    def sign_action(self, actor_name: str, action: str) -> dict:
        """Sign an R6 action with a member's hardware key."""
        member = self.members.get(actor_name)
        if not member:
            return {"error": f"Member '{actor_name}' not found"}

        request = R6Request(
            rules="team-policy-v1",
            role=member.lct_id if hasattr(member, 'lct_id') else "unknown",
            request=action,
            resource_estimate=10.0,
        )

        result = member.act(request)
        record = {
            "actor": actor_name,
            "action": action,
            "decision": result.decision.value,
            "atp_cost": result.atp_consumed,
        }

        if isinstance(member, HardwareWeb4Entity) and result.decision == R6Decision.APPROVED:
            record["hw_signed"] = True
            record["signed_actions"] = len(member.signed_actions)

        self.action_log.append(record)
        return record


# ═══════════════════════════════════════════════════════════════
# CLI Commands
# ═══════════════════════════════════════════════════════════════

def cmd_team_create(args):
    """Create a new team."""
    team = HardboundTeam(args.name, use_tpm=not args.no_tpm)
    result = team.create()
    print(json.dumps(result, indent=2))
    return team


def cmd_entity_create(args):
    """Create a standalone entity."""
    use_tpm = not args.no_tpm and detect_tpm2()
    entity = create_entity(args.name, args.type, use_tpm=use_tpm)
    status = entity.status()
    print(json.dumps(status, indent=2, default=str))


def cmd_entity_sign(args):
    """Sign an action with an entity's hardware key."""
    use_tpm = not args.no_tpm and detect_tpm2()
    entity = create_entity(args.name, args.type or "ai", use_tpm=use_tpm)

    request = R6Request(
        rules="cli-policy-v1",
        role=entity.lct_id,
        request=args.action,
        resource_estimate=5.0,
    )
    result = entity.act(request)
    print(json.dumps({
        "entity": args.name,
        "action": args.action,
        "decision": result.decision.value,
        "hw_signed": len(entity.signed_actions) > 0,
        "signed_actions": len(entity.signed_actions),
        "atp_remaining": round(entity.atp.atp_balance, 1),
    }, indent=2))


def cmd_avp_prove(args):
    """Run AVP aliveness proof."""
    use_tpm = not args.no_tpm and detect_tpm2()
    entity = create_entity(args.name, args.type or "ai", use_tpm=use_tpm)

    proof = entity.prove_aliveness("cli-verifier", "cli-check")
    print(json.dumps(proof, indent=2, default=str))


def cmd_avp_attest(args):
    """Get TPM2 attestation."""
    use_tpm = not args.no_tpm and detect_tpm2()
    entity = create_entity(args.name or "attest-check", args.type or "ai", use_tpm=use_tpm)

    attestation = entity.get_attestation()
    print(json.dumps(attestation, indent=2, default=str))


def cmd_ek_info(args):
    """Show EK certificate info."""
    try:
        from core.lct_binding.ek_attestation import EKAttestationProvider
        provider = EKAttestationProvider()
        identity = provider.get_platform_identity()
        print(json.dumps(identity.to_dict(), indent=2))
        provider.cleanup()
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_ek_verify(args):
    """Verify EK certificate chain."""
    try:
        from core.lct_binding.ek_attestation import EKAttestationProvider
        provider = EKAttestationProvider()
        bundle = provider.create_attestation_bundle()
        print(json.dumps(bundle, indent=2))
        provider.cleanup()
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_status(args):
    """Show full system status."""
    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tpm2_available": detect_tpm2(),
    }

    if status["tpm2_available"]:
        try:
            from core.lct_binding.tpm2_provider import TPM2Provider
            provider = TPM2Provider()
            info = provider.get_platform_info()
            status["platform"] = info.to_dict()
        except Exception as e:
            status["platform_error"] = str(e)

        try:
            from core.lct_binding.ek_attestation import EKAttestationProvider
            ek = EKAttestationProvider()
            identity = ek.get_platform_identity()
            status["ek_identity"] = identity.to_dict()
            ek.cleanup()
        except Exception as e:
            status["ek_error"] = str(e)

    print(json.dumps(status, indent=2))


# ═══════════════════════════════════════════════════════════════
# Interactive Demo
# ═══════════════════════════════════════════════════════════════

def demo():
    """Interactive demo showing the Hardbound CLI workflow."""
    print("=" * 65)
    print("  HARDBOUND CLI — Enterprise Team Management")
    print("  Hardware-backed identity for AI governance")
    print("=" * 65)

    tpm_available = detect_tpm2()
    print(f"\n  TPM2: {'available (real hardware)' if tpm_available else 'not available (simulation mode)'}")

    # ─── Create team ───
    print("\n--- Creating Team ---")
    team = HardboundTeam("acme-ai-ops", use_tpm=tpm_available)
    result = team.create()
    print(f"  Team: {result['team']}")
    print(f"  Hardware: {result['hardware_binding']}")
    print(f"  Root LCT: {result['root']['lct_id'][:40]}...")
    print(f"  Root level: {result['root']['level']} ({'HARDWARE' if result['root']['level'] == 5 else 'SOFTWARE'})")
    print(f"  Root handle: {result['root']['handle']}")
    print(f"  Admin LCT: {result['admin']['lct_id'][:40]}...")

    # ─── Add members ───
    print("\n--- Adding Team Members ---")

    members_to_add = [
        ("data-analyst-agent", "ai"),
        ("code-review-agent", "ai"),
        ("deploy-service", "service"),
        ("qa-engineer", "human"),
    ]

    for name, mtype in members_to_add:
        info = team.add_member(name, mtype)
        binding = info.get('binding', 'unknown')
        level = info.get('level', '?')
        print(f"  Added: {name} ({mtype}) — level={level}, binding={binding}")

    # ─── Team status ───
    print("\n--- Team Status ---")
    info = team.info()
    print(f"  Members: {len(info['members'])}")
    for m in info['members']:
        print(f"    {m['name']:25s} | {m['type']:12s} | level={m['level']} | C={m['coherence']:.4f}")

    # ─── Signed actions ───
    print("\n--- Hardware-Signed Actions ---")
    actions = [
        (f"{team.name}-admin", "approve_deployment"),
        (f"{team.name}-admin", "set_resource_limit"),
        ("data-analyst-agent", "run_analysis"),
        ("code-review-agent", "review_pr"),
        ("deploy-service", "deploy_staging"),
    ]

    for actor, action in actions:
        record = team.sign_action(actor, action)
        hw = "HW" if record.get("hw_signed") else "SW"
        print(f"  [{hw}] {actor:25s} → {action:20s} : {record['decision']}")

    # ─── Final summary ───
    print("\n--- Summary ---")
    hw_members = sum(1 for m in team.members.values()
                    if isinstance(m, HardwareWeb4Entity))
    sw_members = len(team.members) - hw_members
    print(f"  Team: {team.name}")
    print(f"  Total members: {len(team.members)} ({hw_members} hardware, {sw_members} software)")
    print(f"  Actions logged: {len(team.action_log)}")
    hw_signed = sum(1 for a in team.action_log if a.get("hw_signed"))
    print(f"  Hardware-signed: {hw_signed}")
    print(f"  Root coherence: {team.root.coherence:.4f}")

    print("\n" + "=" * 65)
    print("  Hardbound: Enterprise AI governance with hardware trust.")
    print("  Every identity hardware-bound. Every action signed.")
    print("  The ledger remembers. The TPM guarantees.")
    print("=" * 65)


def main():
    """Parse CLI arguments and dispatch commands."""
    parser = argparse.ArgumentParser(
        description="Hardbound CLI — Enterprise Team Management with Hardware-Backed Identity",
        prog="hardbound"
    )
    parser.add_argument("--no-tpm", action="store_true", help="Force simulation mode")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # team create
    team_create = subparsers.add_parser("team-create", help="Create a new team")
    team_create.add_argument("name", help="Team name")

    # team info (demo)
    subparsers.add_parser("demo", help="Run interactive demo")

    # entity create
    entity_create = subparsers.add_parser("entity-create", help="Create an entity")
    entity_create.add_argument("name", help="Entity name")
    entity_create.add_argument("type", help="Entity type (ai, human, service, etc.)")

    # entity sign
    entity_sign = subparsers.add_parser("entity-sign", help="Sign an R6 action")
    entity_sign.add_argument("name", help="Entity name")
    entity_sign.add_argument("action", help="Action to sign")
    entity_sign.add_argument("--type", default="ai", help="Entity type")

    # avp prove
    avp_prove = subparsers.add_parser("avp-prove", help="Run AVP aliveness proof")
    avp_prove.add_argument("name", help="Entity name")
    avp_prove.add_argument("--type", default="ai", help="Entity type")

    # avp attest
    avp_attest = subparsers.add_parser("avp-attest", help="Get TPM2 attestation")
    avp_attest.add_argument("--name", default=None, help="Entity name")
    avp_attest.add_argument("--type", default="ai", help="Entity type")

    # ek info
    subparsers.add_parser("ek-info", help="Show EK certificate info")

    # ek verify
    subparsers.add_parser("ek-verify", help="Verify EK certificate chain")

    # status
    subparsers.add_parser("status", help="Show system status")

    args = parser.parse_args()

    if args.command == "team-create":
        cmd_team_create(args)
    elif args.command == "demo":
        demo()
    elif args.command == "entity-create":
        cmd_entity_create(args)
    elif args.command == "entity-sign":
        cmd_entity_sign(args)
    elif args.command == "avp-prove":
        cmd_avp_prove(args)
    elif args.command == "avp-attest":
        cmd_avp_attest(args)
    elif args.command == "ek-info":
        cmd_ek_info(args)
    elif args.command == "ek-verify":
        cmd_ek_verify(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        # Default: run demo
        demo()


if __name__ == "__main__":
    main()
