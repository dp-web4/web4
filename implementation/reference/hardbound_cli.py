#!/usr/bin/env python3
"""
Hardbound CLI — Enterprise Team Management with Hardware-Backed Identity
=========================================================================

Command-line tool for creating and managing Web4 teams (societies)
with TPM2-backed identity. Wraps HardwareWeb4Entity and the
simulations/team infrastructure.

Commands:
    team create <name>         — Create a new team with hardware-bound root
    team info [name]           — Show team status and member list
    team list                  — List all teams
    team add-member <team> <name> <type> — Add a member to the team
    team sign <team> <actor> <action>    — Sign an R6 action
    entity create <name> <type> — Create a standalone hardware entity
    entity sign <name> <action> — Sign an R6 action with hardware key
    avp prove <name>           — Run AVP aliveness proof
    avp attest                 — Get TPM2 attestation
    ek info                    — Show EK certificate chain info
    ek verify                  — Verify EK certificate chain
    status                     — Show full system status

State is persisted to .hardbound/teams/<name>/ directory.

Enterprise Terminology Bridge:
    Society    → Team
    Citizen    → Member
    Law Oracle → Admin
    Blockchain → Ledger
    Birth Cert → Onboarding Record

Date: 2026-02-19 (persistent state: 2026-02-20)
"""

import sys
import os
import json
import hashlib
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

# Default state directory
HARDBOUND_DIR = Path.cwd() / ".hardbound"


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

    State is persisted to .hardbound/teams/<name>/ as JSON files:
        team.json          — Team metadata and root entity state
        members/<name>.json — Per-member entity state
        actions.jsonl       — Append-only action log (ledger)
    """

    def __init__(self, name: str, use_tpm: bool = True, state_dir: Path = None):
        self.name = name
        self.use_tpm = use_tpm and detect_tpm2()
        self.root: HardwareWeb4Entity = None
        self.admin: HardwareWeb4Entity = None
        self.members: dict = {}  # name → HardwareWeb4Entity
        self.action_log: list = []
        self.created_at = datetime.now(timezone.utc).isoformat()

        # State directory
        self.state_dir = state_dir or (HARDBOUND_DIR / "teams" / name)

    # ─── Persistence ────────────────────────────────────────────

    def _entity_to_state(self, entity) -> dict:
        """Serialize entity state for persistence."""
        state = {
            "entity_type": entity.entity_type.value,
            "name": entity.name,
            "lct_id": entity.lct_id,
            "coherence": round(entity.coherence, 4),
            "t3": {
                "talent": entity.t3.talent,
                "training": entity.t3.training,
                "temperament": entity.t3.temperament,
            },
            "v3": {
                "valuation": entity.v3.valuation,
                "veracity": entity.v3.veracity,
                "validity": entity.v3.validity,
            },
            "atp_balance": round(entity.atp.atp_balance, 2),
            "adp_discharged": round(entity.atp.adp_discharged, 2),
        }

        if isinstance(entity, HardwareWeb4Entity):
            state.update({
                "key_id": entity.key_id,
                "public_key": entity.public_key,
                "tpm_handle": entity.tpm_handle,
                "hardware_type": entity.hardware_type,
                "capability_level": entity.capability_level,
                "trust_ceiling": entity.trust_ceiling,
                "binding_proof": entity.binding_proof,
                "signed_action_count": len(entity.signed_actions),
            })
        else:
            state["capability_level"] = getattr(entity, 'capability_level', 4)

        return state

    def _entity_from_state(self, state: dict) -> HardwareWeb4Entity:
        """Reconstruct entity from persisted state."""
        if "key_id" in state:
            # Hardware entity
            entity = HardwareWeb4Entity(
                entity_type=EntityType(state["entity_type"]),
                name=state["name"],
                lct_id=state["lct_id"],
                key_id=state["key_id"],
                public_key=state["public_key"],
                tpm_handle=state.get("tpm_handle", ""),
                hardware_type=state.get("hardware_type", "tpm2"),
                atp_allocation=state.get("atp_balance", 100.0),
            )
            entity.binding_proof = state.get("binding_proof")
        else:
            # Software entity (reconstruct as Web4Entity)
            entity = Web4Entity(
                EntityType(state["entity_type"]),
                state["name"],
                atp_allocation=state.get("atp_balance", 100.0),
            )
            entity.lct_id = state["lct_id"]

        # Restore trust state
        if "t3" in state:
            entity.t3 = T3Tensor(**state["t3"])
        if "v3" in state:
            entity.v3 = V3Tensor(**state["v3"])

        return entity

    def save(self):
        """Save team state to disk."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        members_dir = self.state_dir / "members"
        members_dir.mkdir(exist_ok=True)

        # Save team metadata
        team_state = {
            "name": self.name,
            "created_at": self.created_at,
            "use_tpm": self.use_tpm,
            "member_names": list(self.members.keys()),
        }
        if self.root:
            team_state["root"] = self._entity_to_state(self.root)
        if self.admin:
            team_state["admin_name"] = f"{self.name}-admin"

        (self.state_dir / "team.json").write_text(
            json.dumps(team_state, indent=2)
        )

        # Save each member
        for name, member in self.members.items():
            member_state = self._entity_to_state(member)
            safe_name = name.replace("/", "_").replace(" ", "_")
            (members_dir / f"{safe_name}.json").write_text(
                json.dumps(member_state, indent=2)
            )

        # Append new actions to ledger
        if self.action_log:
            with open(self.state_dir / "actions.jsonl", "a") as f:
                for action in self.action_log:
                    action["saved_at"] = datetime.now(timezone.utc).isoformat()
                    f.write(json.dumps(action) + "\n")
            self.action_log = []  # Clear after saving

    @classmethod
    def load(cls, name: str, state_dir: Path = None) -> "HardboundTeam":
        """Load team state from disk."""
        base = state_dir or (HARDBOUND_DIR / "teams" / name)
        team_file = base / "team.json"
        if not team_file.exists():
            raise FileNotFoundError(f"Team '{name}' not found at {base}")

        team_state = json.loads(team_file.read_text())
        team = cls(team_state["name"], use_tpm=team_state.get("use_tpm", True))
        team.created_at = team_state.get("created_at", "unknown")
        team.state_dir = base

        # Restore root
        if "root" in team_state:
            team.root = team._entity_from_state(team_state["root"])

        # Restore members
        members_dir = base / "members"
        if members_dir.exists():
            for member_file in sorted(members_dir.glob("*.json")):
                member_state = json.loads(member_file.read_text())
                member = team._entity_from_state(member_state)
                team.members[member_state["name"]] = member

        # Restore admin reference
        admin_name = team_state.get("admin_name")
        if admin_name and admin_name in team.members:
            team.admin = team.members[admin_name]

        # Load action count
        actions_file = base / "actions.jsonl"
        if actions_file.exists():
            team._action_count = sum(1 for _ in open(actions_file))
        else:
            team._action_count = 0

        return team

    @staticmethod
    def list_teams(state_dir: Path = None) -> list:
        """List all persisted teams."""
        base = state_dir or (HARDBOUND_DIR / "teams")
        if not base.exists():
            return []
        teams = []
        for team_dir in sorted(base.iterdir()):
            if team_dir.is_dir() and (team_dir / "team.json").exists():
                try:
                    state = json.loads((team_dir / "team.json").read_text())
                    teams.append({
                        "name": state["name"],
                        "created": state.get("created_at", "unknown"),
                        "members": len(state.get("member_names", [])),
                        "use_tpm": state.get("use_tpm", False),
                    })
                except Exception:
                    teams.append({"name": team_dir.name, "error": "corrupt state"})
        return teams

    # ─── Team Operations ────────────────────────────────────────

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

        # Persist immediately
        self.save()

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
            self.save()
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

        # Persist
        self.save()

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
            "state_dir": str(self.state_dir),
        }

        if self.root:
            result["root"] = {
                "lct_id": self.root.lct_id,
                "level": self.root.capability_level,
                "trust_ceiling": self.root.trust_ceiling,
                "coherence": round(self.root.coherence, 4),
                "atp": round(self.root.atp.atp_balance, 1),
                "handle": getattr(self.root, 'tpm_handle', None),
            }

        if self.admin:
            result["admin"] = {
                "lct_id": self.admin.lct_id,
                "level": getattr(self.admin, 'capability_level', 4),
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

        # Action count from ledger
        actions_file = self.state_dir / "actions.jsonl"
        action_count = getattr(self, '_action_count', 0)
        if actions_file.exists():
            action_count = sum(1 for _ in open(actions_file))
        result["total_actions"] = action_count + len(self.action_log)

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
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if isinstance(member, HardwareWeb4Entity) and result.decision == R6Decision.APPROVED:
            record["hw_signed"] = True
            record["signed_actions"] = len(member.signed_actions)

        self.action_log.append(record)

        # Auto-save after each action
        self.save()

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


def cmd_team_info(args):
    """Show team info (loads from disk)."""
    try:
        team = HardboundTeam.load(args.name)
        print(json.dumps(team.info(), indent=2))
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_team_list(args):
    """List all teams."""
    teams = HardboundTeam.list_teams()
    print(json.dumps({"teams": teams}, indent=2))


def cmd_team_add_member(args):
    """Add a member to an existing team."""
    try:
        team = HardboundTeam.load(args.team)
        result = team.add_member(args.name, args.type)
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_team_sign(args):
    """Sign an action within a team."""
    try:
        team = HardboundTeam.load(args.team)
        result = team.sign_action(args.actor, args.action)
        print(json.dumps(result, indent=2))
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e)}, indent=2))


def cmd_team_actions(args):
    """Show action log for a team."""
    team_dir = HARDBOUND_DIR / "teams" / args.team
    actions_file = team_dir / "actions.jsonl"
    if not actions_file.exists():
        print(json.dumps({"actions": [], "count": 0}, indent=2))
        return

    actions = []
    for line in open(actions_file):
        try:
            actions.append(json.loads(line.strip()))
        except json.JSONDecodeError:
            continue

    # Show last N actions
    limit = args.limit if hasattr(args, 'limit') else 20
    recent = actions[-limit:]
    print(json.dumps({
        "team": args.team,
        "total_actions": len(actions),
        "showing_last": len(recent),
        "actions": recent,
    }, indent=2))


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
        "teams": HardboundTeam.list_teams(),
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
    """Interactive demo showing the Hardbound CLI workflow with persistence."""
    print("=" * 65)
    print("  HARDBOUND CLI — Enterprise Team Management")
    print("  Hardware-backed identity with persistent state")
    print("=" * 65)

    tpm_available = detect_tpm2()
    print(f"\n  TPM2: {'available (real hardware)' if tpm_available else 'not available (simulation mode)'}")
    print(f"  State dir: {HARDBOUND_DIR}/teams/")

    # ─── Create team ───
    print("\n--- Creating Team ---")
    team = HardboundTeam("acme-ai-ops", use_tpm=tpm_available)
    result = team.create()
    print(f"  Team: {result['team']}")
    print(f"  Hardware: {result['hardware_binding']}")
    print(f"  Root LCT: {result['root']['lct_id'][:40]}...")
    level = result['root']['level']
    print(f"  Root level: {level} ({'HARDWARE' if level == 5 else 'SOFTWARE'})")
    print(f"  Root handle: {result['root'].get('handle')}")
    print(f"  Admin LCT: {result['admin']['lct_id'][:40]}...")
    print(f"  State saved to: {result['state_dir']}")

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

    # ─── Persistence test ───
    print("\n--- Persistence Test ---")
    print("  Loading team from disk...")
    loaded = HardboundTeam.load("acme-ai-ops")
    loaded_info = loaded.info()
    print(f"  Loaded team: {loaded_info['team']}")
    print(f"  Members restored: {len(loaded_info['members'])}")
    print(f"  Actions in ledger: {loaded_info['total_actions']}")
    for m in loaded_info['members']:
        print(f"    {m['name']:25s} | {m['type']:12s} | level={m['level']}")

    # Sign one more action on the loaded team
    print("\n  Signing action on loaded team...")
    record = loaded.sign_action(f"{loaded.name}-admin", "rotate_credentials")
    print(f"  [{('HW' if record.get('hw_signed') else 'SW')}] rotate_credentials: {record['decision']}")
    print(f"  Total actions now: {loaded.info()['total_actions']}")

    # ─── List teams ───
    print("\n--- Teams on This Machine ---")
    teams = HardboundTeam.list_teams()
    for t in teams:
        print(f"  {t['name']:20s} | members={t.get('members', '?')} | tpm={t.get('use_tpm')}")

    # ─── State directory contents ───
    print("\n--- Persisted State Files ---")
    state_dir = team.state_dir
    for f in sorted(state_dir.rglob("*")):
        if f.is_file():
            rel = f.relative_to(state_dir)
            print(f"  {str(rel):30s} ({f.stat().st_size:,} bytes)")

    # ─── Summary ───
    print("\n--- Summary ---")
    hw_members = sum(1 for m in team.members.values()
                    if isinstance(m, HardwareWeb4Entity))
    sw_members = len(team.members) - hw_members
    print(f"  Team: {team.name}")
    print(f"  Total members: {len(team.members)} ({hw_members} hardware, {sw_members} software)")
    print(f"  Actions in ledger: {team.info()['total_actions']}")
    print(f"  State persisted: {team.state_dir}")
    print(f"  Root coherence: {team.root.coherence:.4f}")

    print("\n" + "=" * 65)
    print("  Hardbound: Persistent enterprise AI governance.")
    print("  Teams survive sessions. Actions append to ledger.")
    print("  State is JSON. Trust is hardware. The TPM remembers.")
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

    # team info
    team_info = subparsers.add_parser("team-info", help="Show team info")
    team_info.add_argument("name", help="Team name")

    # team list
    subparsers.add_parser("team-list", help="List all teams")

    # team add-member
    team_add = subparsers.add_parser("team-add-member", help="Add member to team")
    team_add.add_argument("team", help="Team name")
    team_add.add_argument("name", help="Member name")
    team_add.add_argument("type", help="Member type (ai, human, service, etc.)")

    # team sign
    team_sign = subparsers.add_parser("team-sign", help="Sign action in team context")
    team_sign.add_argument("team", help="Team name")
    team_sign.add_argument("actor", help="Actor name")
    team_sign.add_argument("action", help="Action to sign")

    # team actions
    team_actions = subparsers.add_parser("team-actions", help="Show team action log")
    team_actions.add_argument("team", help="Team name")
    team_actions.add_argument("--limit", type=int, default=20, help="Max actions to show")

    # demo
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

    dispatch = {
        "team-create": cmd_team_create,
        "team-info": cmd_team_info,
        "team-list": cmd_team_list,
        "team-add-member": cmd_team_add_member,
        "team-sign": cmd_team_sign,
        "team-actions": cmd_team_actions,
        "demo": lambda a: demo(),
        "entity-create": cmd_entity_create,
        "entity-sign": cmd_entity_sign,
        "avp-prove": cmd_avp_prove,
        "avp-attest": cmd_avp_attest,
        "ek-info": cmd_ek_info,
        "ek-verify": cmd_ek_verify,
        "status": cmd_status,
    }

    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        demo()


if __name__ == "__main__":
    main()
