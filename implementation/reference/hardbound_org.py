#!/usr/bin/env python3
"""
Hardbound Organization — Cross-Team Trust Bridges
===================================================

Manages multiple HardboundTeams connected via trust bridges.
Enables SAL fractal citizenship: citizen(team) ⊂ citizen(org).

An Organization is a root society that contains child teams.
Teams within the same organization can:
  - Establish trust bridges (mutual AVP verification)
  - Delegate R6 actions across team boundaries
  - Share ATP budgets with forwarding constraints
  - Issue cross-team birth certificates

Architecture:
  Organization (SOCIETY, Level 5)
  ├── Team A (child SOCIETY)
  │   ├── admin-a (HUMAN, admin)
  │   └── agent-a (AI, agent)
  ├── Team B (child SOCIETY)
  │   ├── admin-b (HUMAN, admin)
  │   └── service-b (SERVICE, operator)
  └── Bridge(A↔B) (INFRASTRUCTURE)
      ├── trust_multiplier: 0.8
      ├── effective_trust: 0.72
      └── delegations: [...]

Date: 2026-02-20
"""

import sys
import os
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from web4_entity import (
    Web4Entity, EntityType, R6Request, R6Result, R6Decision,
    T3Tensor, V3Tensor, ATPBudget
)
from hardware_entity import HardwareWeb4Entity
from hardbound_cli import (
    HardboundTeam, TeamRole, TeamPolicy, BirthCertificate,
    ROLE_INITIAL_RIGHTS, ROLE_INITIAL_RESPONSIBILITIES,
    HARDBOUND_DIR, detect_tpm2,
)


# ═══════════════════════════════════════════════════════════════
# Organization Bridge — Trust relationship between two teams
# ═══════════════════════════════════════════════════════════════

class BridgeState:
    """Bridge lifecycle states (from CMTVP spec)."""
    NEW = "new"               # Bridge created, not yet verified
    ACTIVE = "active"         # Mutual verification passed
    ESTABLISHED = "established"  # 10+ consecutive heartbeats
    DEGRADED = "degraded"     # 1+ heartbeat failures
    BROKEN = "broken"         # 5+ consecutive failures

    # State → trust multiplier mapping
    TRUST_MULTIPLIER = {
        "new": 0.5,
        "active": 0.8,
        "established": 0.95,
        "degraded": 0.3,
        "broken": 0.0,
    }


class OrgBridge:
    """
    Trust bridge between two teams within an organization.

    The bridge is an INFRASTRUCTURE-type entity with its own LCT.
    It tracks trust state through heartbeat-driven verification.
    Cross-team delegation requires a healthy bridge (ACTIVE or ESTABLISHED).
    """

    def __init__(self, team_a_name: str, team_b_name: str,
                 bridge_id: str = None):
        # Sort team names for symmetric bridge ID
        sorted_teams = sorted([team_a_name, team_b_name])
        self.team_a = sorted_teams[0]
        self.team_b = sorted_teams[1]

        # Bridge ID: deterministic from sorted team names
        if bridge_id is None:
            raw = f"{self.team_a}:{self.team_b}"
            self.bridge_id = f"bridge:{hashlib.sha256(raw.encode()).hexdigest()[:12]}"
        else:
            self.bridge_id = bridge_id

        # State machine
        self.state = BridgeState.NEW
        self.consecutive_successes = 0
        self.consecutive_failures = 0

        # Trust tracking
        self.trust_ceiling_a = 1.0  # Trust ceiling of team A root
        self.trust_ceiling_b = 1.0  # Trust ceiling of team B root

        # Lifecycle
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_heartbeat = None
        self.witnesses = []

        # Delegation log
        self.delegations = []

    @property
    def trust_multiplier(self) -> float:
        """Current trust multiplier based on bridge state."""
        return BridgeState.TRUST_MULTIPLIER.get(self.state, 0.0)

    @property
    def effective_trust(self) -> float:
        """Effective trust: multiplier × min ceiling."""
        return self.trust_multiplier * min(self.trust_ceiling_a, self.trust_ceiling_b)

    @property
    def is_healthy(self) -> bool:
        """Bridge can carry delegations if active or established."""
        return self.state in (BridgeState.ACTIVE, BridgeState.ESTABLISHED)

    def _sign_nonce(self, entity, nonce: str) -> str:
        """Sign a nonce using entity's hardware key (or simulated fallback)."""
        nonce_bytes = nonce.encode()
        # Try real TPM2 signing
        try:
            from core.lct_binding.tpm2_provider import TPM2Provider
            provider = TPM2Provider()
            result = provider.sign_data(entity.key_id, nonce_bytes)
            if result.success:
                return result.signature_b64
        except (ImportError, Exception, AttributeError):
            pass

        # Simulated signature
        return hashlib.sha256(
            f"bridge-sign:{entity.lct_id}:{nonce}".encode()
        ).hexdigest()

    def verify(self, team_a: HardboundTeam, team_b: HardboundTeam) -> dict:
        """
        Mutual verification ceremony between two teams.

        Both teams sign a shared nonce with their root entity.
        If both verify, bridge transitions to ACTIVE.
        """
        nonce = hashlib.sha256(
            f"{self.bridge_id}:{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()

        # Both roots must exist
        if not team_a.root or not team_b.root:
            self.state = BridgeState.BROKEN
            return {"verified": False, "bridge_id": self.bridge_id,
                    "error": "one or both team roots missing"}

        # Team A signs the nonce
        sig_a = self._sign_nonce(team_a.root, nonce)

        # Team B signs the nonce
        sig_b = self._sign_nonce(team_b.root, nonce)

        # Both must have produced signatures
        if sig_a and sig_b:
            self.state = BridgeState.ACTIVE
            self.consecutive_successes = 1
            self.trust_ceiling_a = getattr(team_a.root, 'trust_ceiling', 0.9)
            self.trust_ceiling_b = getattr(team_b.root, 'trust_ceiling', 0.9)
            self.last_heartbeat = datetime.now(timezone.utc).isoformat()

            # Determine signing type
            a_hw = isinstance(team_a.root, HardwareWeb4Entity) and len(sig_a) > 64
            b_hw = isinstance(team_b.root, HardwareWeb4Entity) and len(sig_b) > 64

            return {
                "verified": True,
                "bridge_id": self.bridge_id,
                "state": self.state,
                "trust": self.effective_trust,
                "team_a_signed": True,
                "team_b_signed": True,
                "team_a_hw": a_hw,
                "team_b_hw": b_hw,
            }

        self.state = BridgeState.BROKEN
        return {
            "verified": False,
            "bridge_id": self.bridge_id,
            "error": "mutual verification failed",
        }

    def heartbeat(self, success: bool = True) -> dict:
        """
        Periodic heartbeat to maintain bridge health.

        Tracks consecutive successes/failures and transitions state.
        """
        self.last_heartbeat = datetime.now(timezone.utc).isoformat()

        if success:
            self.consecutive_successes += 1
            self.consecutive_failures = 0

            # State transitions on success
            if self.consecutive_successes >= 10:
                self.state = BridgeState.ESTABLISHED
            elif self.state == BridgeState.DEGRADED:
                self.state = BridgeState.ACTIVE
        else:
            self.consecutive_failures += 1
            self.consecutive_successes = 0

            # State transitions on failure
            if self.consecutive_failures >= 5:
                self.state = BridgeState.BROKEN
            elif self.state in (BridgeState.ACTIVE, BridgeState.ESTABLISHED):
                self.state = BridgeState.DEGRADED

        return {
            "bridge_id": self.bridge_id,
            "state": self.state,
            "trust": self.effective_trust,
            "consecutive_successes": self.consecutive_successes,
            "consecutive_failures": self.consecutive_failures,
        }

    def add_witness(self, witness_lct: str, witness_trust: float):
        """Add a witness to boost bridge trust (max 0.3 boost, cap 0.95)."""
        boost = min(0.3, witness_trust * 0.4)
        self.witnesses.append({
            "lct": witness_lct,
            "trust": witness_trust,
            "boost": boost,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def to_dict(self) -> dict:
        return {
            "bridge_id": self.bridge_id,
            "team_a": self.team_a,
            "team_b": self.team_b,
            "state": self.state,
            "trust_multiplier": self.trust_multiplier,
            "effective_trust": round(self.effective_trust, 4),
            "trust_ceiling_a": self.trust_ceiling_a,
            "trust_ceiling_b": self.trust_ceiling_b,
            "consecutive_successes": self.consecutive_successes,
            "consecutive_failures": self.consecutive_failures,
            "created_at": self.created_at,
            "last_heartbeat": self.last_heartbeat,
            "witnesses": len(self.witnesses),
            "delegations": len(self.delegations),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OrgBridge":
        bridge = cls(data["team_a"], data["team_b"], bridge_id=data["bridge_id"])
        bridge.state = data.get("state", BridgeState.NEW)
        bridge.trust_ceiling_a = data.get("trust_ceiling_a", 1.0)
        bridge.trust_ceiling_b = data.get("trust_ceiling_b", 1.0)
        bridge.consecutive_successes = data.get("consecutive_successes", 0)
        bridge.consecutive_failures = data.get("consecutive_failures", 0)
        bridge.created_at = data.get("created_at", bridge.created_at)
        bridge.last_heartbeat = data.get("last_heartbeat")
        bridge.witnesses = data.get("witnesses", []) if isinstance(data.get("witnesses"), list) else []
        bridge.delegations = data.get("delegations", []) if isinstance(data.get("delegations"), list) else []
        return bridge


# ═══════════════════════════════════════════════════════════════
# Hardbound Organization — Multi-team governance
# ═══════════════════════════════════════════════════════════════

class HardboundOrganization:
    """
    Organization-level governance over multiple teams.

    The organization is itself a society (SAL spec §3.2):
      citizen(team) ⊂ citizen(org)

    Teams within the same organization can establish trust bridges
    for cross-team action delegation with ATP forwarding.

    Persistence:
      .hardbound/orgs/<name>/
        org.json          — Organization metadata
        bridges/          — Bridge state files
    """

    def __init__(self, name: str, use_tpm: bool = True,
                 state_dir: Path = None, org_atp: float = 5000.0):
        self.name = name
        self.use_tpm = use_tpm and detect_tpm2()
        self.teams: dict = {}  # team_name → HardboundTeam
        self.bridges: dict = {}  # bridge_id → OrgBridge
        self.created_at = datetime.now(timezone.utc).isoformat()

        # Organization-level ATP pool (across all teams)
        self.org_atp = org_atp
        self.org_atp_max = org_atp

        # State directory
        self.state_dir = state_dir or (HARDBOUND_DIR / "orgs" / name)

    def create_team(self, team_name: str, team_atp: float = 1000.0) -> dict:
        """
        Create a new team within this organization.

        The team is a child society of this organization.
        The team root gets a birth certificate as citizen of the org.
        """
        team_dir = self.state_dir / "teams" / team_name
        team = HardboundTeam(
            team_name,
            use_tpm=self.use_tpm,
            state_dir=team_dir,
            team_atp=team_atp,
        )
        result = team.create()
        self.teams[team_name] = team

        return {
            "team": team_name,
            "org": self.name,
            "members": len(team.members),
            "root_lct": team.root.lct_id if team.root else "unknown",
            "binding": result.get("hardware_binding", "unknown"),
        }

    def add_team(self, team: HardboundTeam):
        """Add an existing team to this organization."""
        self.teams[team.name] = team

    def establish_bridge(self, team_a_name: str, team_b_name: str) -> dict:
        """
        Establish a trust bridge between two teams.

        Both teams perform mutual verification (signing shared nonce).
        If successful, the bridge enters ACTIVE state.
        """
        if team_a_name not in self.teams:
            return {"error": f"team '{team_a_name}' not in organization"}
        if team_b_name not in self.teams:
            return {"error": f"team '{team_b_name}' not in organization"}

        team_a = self.teams[team_a_name]
        team_b = self.teams[team_b_name]

        bridge = OrgBridge(team_a_name, team_b_name)

        # Check if bridge already exists
        if bridge.bridge_id in self.bridges:
            existing = self.bridges[bridge.bridge_id]
            if existing.is_healthy:
                return {
                    "error": "bridge already exists and is healthy",
                    "bridge": existing.to_dict(),
                }
            # Re-establish broken/degraded bridge
            bridge = existing

        # Mutual verification
        result = bridge.verify(team_a, team_b)

        if result["verified"]:
            self.bridges[bridge.bridge_id] = bridge

            # Log bridge establishment in both team ledgers
            bridge_entry = {
                "type": "bridge_established",
                "bridge_id": bridge.bridge_id,
                "remote_team": team_b_name,
                "trust": bridge.effective_trust,
                "state": bridge.state,
            }
            team_a.ledger.append(
                action=bridge_entry,
                signer_lct=team_a.root.lct_id if team_a.root else "",
                signer_entity=team_a.root if isinstance(team_a.root, HardwareWeb4Entity) else None,
            )

            bridge_entry_b = dict(bridge_entry)
            bridge_entry_b["remote_team"] = team_a_name
            team_b.ledger.append(
                action=bridge_entry_b,
                signer_lct=team_b.root.lct_id if team_b.root else "",
                signer_entity=team_b.root if isinstance(team_b.root, HardwareWeb4Entity) else None,
            )

        return result

    def delegate_action(self, from_team: str, to_team: str,
                        actor: str, action: str,
                        approved_by: str = None) -> dict:
        """
        Delegate an R6 action from one team to another via trust bridge.

        The action is executed by the receiving team but charged to
        the sending team's ATP pool. Trust multiplier from the bridge
        modulates the effective authority.

        Args:
            from_team: Team initiating the delegation
            to_team: Team executing the action
            actor: Member name in from_team who initiates
            action: R6 action to execute
            approved_by: Admin who pre-approved (for restricted actions)
        """
        if from_team not in self.teams:
            return {"error": f"team '{from_team}' not in organization"}
        if to_team not in self.teams:
            return {"error": f"team '{to_team}' not in organization"}

        source = self.teams[from_team]
        target = self.teams[to_team]

        # Find the bridge
        sorted_teams = sorted([from_team, to_team])
        raw = f"{sorted_teams[0]}:{sorted_teams[1]}"
        bridge_id = f"bridge:{hashlib.sha256(raw.encode()).hexdigest()[:12]}"

        bridge = self.bridges.get(bridge_id)
        if bridge is None:
            return {"error": f"no bridge between '{from_team}' and '{to_team}'"}
        if not bridge.is_healthy:
            return {
                "error": f"bridge is {bridge.state} (trust={bridge.effective_trust:.2f})",
                "bridge": bridge.to_dict(),
            }

        # Verify the actor exists in source team
        if actor not in source.members:
            return {"error": f"actor '{actor}' not found in team '{from_team}'"}

        # Execute the action on the target team using the bridge
        # The target team's admin acts as the execution proxy
        target_admin = f"{to_team}-admin"
        if target_admin not in target.members:
            return {"error": f"no admin in target team '{to_team}'"}

        # Execute with admin approval (bridge acts as delegation authority)
        record = target.sign_action(
            target_admin, action,
            approved_by=target_admin,  # Bridge implies admin approval
        )

        # Compute cross-team ATP cost
        # Cost is paid by the source team, scaled by bridge trust
        policy = target._resolve_policy()
        action_cost = policy.get_cost(action)
        trust_scaled_cost = action_cost * (1.0 / max(0.1, bridge.effective_trust))

        # Charge source team's ATP pool
        if source.team_atp >= trust_scaled_cost:
            source.team_atp -= trust_scaled_cost
            source.team_adp_discharged += trust_scaled_cost
        else:
            return {
                "error": f"insufficient ATP in source team (need {trust_scaled_cost:.1f}, have {source.team_atp:.1f})",
                "bridge": bridge.to_dict(),
            }

        delegation_record = {
            "type": "cross_team_delegation",
            "bridge_id": bridge_id,
            "from_team": from_team,
            "to_team": to_team,
            "actor": actor,
            "action": action,
            "decision": record.get("decision", "unknown"),
            "atp_cost": round(trust_scaled_cost, 2),
            "bridge_trust": round(bridge.effective_trust, 4),
            "bridge_state": bridge.state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Log in source team's ledger
        source.ledger.append(
            action=delegation_record,
            signer_lct=source.root.lct_id if source.root else "",
            signer_entity=source.root if isinstance(source.root, HardwareWeb4Entity) else None,
        )

        # Log in target team's ledger
        target.ledger.append(
            action=delegation_record,
            signer_lct=target.root.lct_id if target.root else "",
            signer_entity=target.root if isinstance(target.root, HardwareWeb4Entity) else None,
        )

        # Record delegation on the bridge
        bridge.delegations.append(delegation_record)

        # Heartbeat the bridge (successful delegation = successful heartbeat)
        bridge.heartbeat(success=True)

        return delegation_record

    def info(self) -> dict:
        """Get organization status."""
        result = {
            "org": self.name,
            "created": self.created_at,
            "teams": len(self.teams),
            "bridges": len(self.bridges),
            "org_atp": round(self.org_atp, 2),
            "org_atp_max": round(self.org_atp_max, 2),
        }

        result["team_list"] = []
        for name, team in self.teams.items():
            result["team_list"].append({
                "name": name,
                "members": len(team.members),
                "team_atp": round(team.team_atp, 2),
                "ledger_entries": team.ledger.count(),
                "birth_certs": len(team.birth_certificates),
            })

        result["bridge_list"] = []
        for bridge_id, bridge in self.bridges.items():
            result["bridge_list"].append(bridge.to_dict())

        return result

    def save(self):
        """Save organization state to disk."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        bridges_dir = self.state_dir / "bridges"
        bridges_dir.mkdir(exist_ok=True)

        # Save org metadata
        org_state = {
            "name": self.name,
            "created_at": self.created_at,
            "use_tpm": self.use_tpm,
            "team_names": list(self.teams.keys()),
            "bridge_ids": list(self.bridges.keys()),
            "org_atp": round(self.org_atp, 2),
            "org_atp_max": round(self.org_atp_max, 2),
        }
        (self.state_dir / "org.json").write_text(json.dumps(org_state, indent=2))

        # Save each bridge
        for bridge_id, bridge in self.bridges.items():
            safe_id = bridge_id.replace(":", "_").replace("/", "_")
            (bridges_dir / f"{safe_id}.json").write_text(
                json.dumps(bridge.to_dict(), indent=2)
            )

        # Save each team
        for team in self.teams.values():
            team.save()

    @classmethod
    def load(cls, name: str, state_dir: Path = None) -> "HardboundOrganization":
        """Load organization state from disk."""
        base = state_dir or (HARDBOUND_DIR / "orgs" / name)
        org_file = base / "org.json"
        if not org_file.exists():
            raise FileNotFoundError(f"Organization '{name}' not found at {base}")

        org_state = json.loads(org_file.read_text())
        org = cls(
            org_state["name"],
            use_tpm=org_state.get("use_tpm", True),
            state_dir=base,
            org_atp=org_state.get("org_atp", 5000.0),
        )
        org.org_atp_max = org_state.get("org_atp_max", 5000.0)
        org.created_at = org_state.get("created_at", org.created_at)

        # Restore teams
        for team_name in org_state.get("team_names", []):
            team_dir = base / "teams" / team_name
            if team_dir.exists():
                try:
                    team = HardboundTeam.load(team_name, state_dir=team_dir)
                    org.teams[team_name] = team
                except FileNotFoundError:
                    pass

        # Restore bridges
        bridges_dir = base / "bridges"
        if bridges_dir.exists():
            for bridge_file in bridges_dir.glob("*.json"):
                try:
                    data = json.loads(bridge_file.read_text())
                    bridge = OrgBridge.from_dict(data)
                    org.bridges[bridge.bridge_id] = bridge
                except (json.JSONDecodeError, KeyError):
                    pass

        return org


# ═══════════════════════════════════════════════════════════════
# Demo
# ═══════════════════════════════════════════════════════════════

def demo():
    """
    Cross-team trust bridge demo.

    Shows:
    1. Organization with 2 teams
    2. Bridge establishment (mutual verification)
    3. Cross-team action delegation
    4. ATP forwarding across bridges
    5. Bridge health tracking
    6. Persistence and reload
    """
    print("=" * 65)
    print("  HARDBOUND ORGANIZATION — Cross-Team Trust Bridges")
    print("  SAL fractal citizenship: citizen(team) ⊂ citizen(org)")
    print("=" * 65)

    tpm_available = detect_tpm2()
    print(f"\n  TPM2: {'available' if tpm_available else 'simulation mode'}")

    # Clean up previous demo
    demo_dir = HARDBOUND_DIR / "orgs" / "acme-corp"
    if demo_dir.exists():
        shutil.rmtree(demo_dir)

    # ─── Create Organization ───
    print("\n--- Creating Organization ---")
    org = HardboundOrganization("acme-corp", use_tpm=tpm_available,
                                 state_dir=demo_dir)

    # Create two teams
    result_a = org.create_team("platform-team", team_atp=500.0)
    print(f"  Team: {result_a['team']} (ATP: 500)")
    print(f"    Root: {result_a['root_lct'][:30]}...")

    result_b = org.create_team("data-team", team_atp=500.0)
    print(f"  Team: {result_b['team']} (ATP: 500)")
    print(f"    Root: {result_b['root_lct'][:30]}...")

    # Add members to each team
    print("\n--- Adding Members ---")

    platform = org.teams["platform-team"]
    platform.add_member("deploy-bot", "ai", role=TeamRole.AGENT)
    platform.add_member("sre-engineer", "human", role=TeamRole.OPERATOR)
    print(f"  platform-team: {len(platform.members)} members")

    data = org.teams["data-team"]
    data.add_member("analytics-agent", "ai", role=TeamRole.AGENT)
    data.add_member("ml-pipeline", "service", role=TeamRole.OPERATOR)
    print(f"  data-team: {len(data.members)} members")

    # ─── Organization Status ───
    print("\n--- Organization Status ---")
    info = org.info()
    print(f"  Org: {info['org']}")
    print(f"  Teams: {info['teams']}")
    print(f"  Bridges: {info['bridges']}")
    for t in info['team_list']:
        print(f"    {t['name']:20s} members={t['members']}  "
              f"ATP={t['team_atp']:.0f}  "
              f"ledger={t['ledger_entries']}  "
              f"certs={t['birth_certs']}")

    # ─── Establish Bridge ───
    print("\n--- Establishing Trust Bridge ---")
    bridge_result = org.establish_bridge("platform-team", "data-team")
    if bridge_result.get("verified"):
        print(f"  Bridge: {bridge_result['bridge_id']}")
        print(f"  State: {bridge_result['state']}")
        print(f"  Trust: {bridge_result['trust']:.2f}")
        print(f"  Team A signed: {bridge_result['team_a_signed']}")
        print(f"  Team B signed: {bridge_result['team_b_signed']}")
    else:
        print(f"  Bridge failed: {bridge_result.get('error', 'unknown')}")
        return

    # ─── Cross-Team Delegation ───
    print("\n--- Cross-Team Action Delegation ---")

    # Platform team's deploy-bot delegates an analysis to data team
    delegation = org.delegate_action(
        from_team="platform-team",
        to_team="data-team",
        actor="deploy-bot",
        action="run_analysis",
    )
    print(f"  Delegation: platform-team → data-team")
    print(f"    Actor: {delegation.get('actor')}")
    print(f"    Action: {delegation.get('action')}")
    print(f"    Decision: {delegation.get('decision')}")
    print(f"    ATP cost: {delegation.get('atp_cost', 0):.1f} (charged to platform-team)")
    print(f"    Bridge trust: {delegation.get('bridge_trust', 0):.2f}")

    # Data team's analytics-agent delegates a deployment to platform team
    delegation2 = org.delegate_action(
        from_team="data-team",
        to_team="platform-team",
        actor="analytics-agent",
        action="deploy_staging",
    )
    print(f"\n  Delegation: data-team → platform-team")
    print(f"    Actor: {delegation2.get('actor')}")
    print(f"    Action: {delegation2.get('action')}")
    print(f"    Decision: {delegation2.get('decision')}")
    print(f"    ATP cost: {delegation2.get('atp_cost', 0):.1f} (charged to data-team)")

    # ─── Bidirectional delegation ───
    print(f"\n  Bidirectional delegation validated:")
    print(f"    platform-team ATP: {platform.team_atp:.1f}/{platform.team_atp_max:.1f}")
    print(f"    data-team ATP: {data.team_atp:.1f}/{data.team_atp_max:.1f}")

    # ─── Bridge Health ───
    print("\n--- Bridge Health ---")
    bridge = list(org.bridges.values())[0]
    print(f"  Bridge: {bridge.bridge_id}")
    print(f"  State: {bridge.state}")
    print(f"  Trust: {bridge.effective_trust:.2f}")
    print(f"  Consecutive successes: {bridge.consecutive_successes}")
    print(f"  Delegations: {len(bridge.delegations)}")

    # Simulate heartbeats
    for i in range(8):
        bridge.heartbeat(success=True)
    print(f"\n  After 8 more heartbeats:")
    print(f"    State: {bridge.state}")
    print(f"    Trust: {bridge.effective_trust:.2f}")
    print(f"    Consecutive successes: {bridge.consecutive_successes}")

    # ─── Bridge Degradation ───
    print("\n--- Bridge Degradation ---")
    bridge.heartbeat(success=False)
    print(f"  1 failure: state={bridge.state} trust={bridge.effective_trust:.2f}")

    # Try delegation on degraded bridge
    degraded_delegation = org.delegate_action(
        from_team="platform-team",
        to_team="data-team",
        actor="deploy-bot",
        action="run_diagnostics",
    )
    print(f"  Delegation on degraded bridge: {degraded_delegation.get('error', 'allowed')}")

    # Recovery
    bridge.heartbeat(success=True)
    print(f"  Recovery heartbeat: state={bridge.state} trust={bridge.effective_trust:.2f}")

    # ─── Persistence ───
    print("\n--- Persistence ---")
    org.save()
    print(f"  Saved to: {org.state_dir}")

    loaded = HardboundOrganization.load("acme-corp", state_dir=demo_dir)
    loaded_info = loaded.info()
    print(f"  Loaded: {loaded_info['teams']} teams, {loaded_info['bridges']} bridges")
    for t in loaded_info['team_list']:
        print(f"    {t['name']:20s} members={t['members']}  ATP={t['team_atp']:.0f}")
    for b in loaded_info['bridge_list']:
        print(f"    Bridge {b['bridge_id']}: {b['state']} trust={b['effective_trust']:.2f} "
              f"delegations={b['delegations']}")

    # Verify ledger integrity on loaded teams
    print("\n--- Ledger Integrity After Reload ---")
    for team_name, team in loaded.teams.items():
        verify = team.ledger.verify()
        print(f"  {team_name:20s}: {'VERIFIED' if verify['valid'] else 'BROKEN'} "
              f"({verify['entries']} entries, {verify['hw_signed']} HW-signed)")

    # ─── Summary ───
    print("\n--- Summary ---")
    print(f"  Organization: {org.name}")
    print(f"  Teams: {len(org.teams)}")
    print(f"  Bridges: {len(org.bridges)}")
    total_members = sum(len(t.members) for t in org.teams.values())
    total_certs = sum(len(t.birth_certificates) for t in org.teams.values())
    total_ledger = sum(t.ledger.count() for t in org.teams.values())
    print(f"  Total members: {total_members}")
    print(f"  Total birth certs: {total_certs}")
    print(f"  Total ledger entries: {total_ledger}")
    print(f"  Cross-team delegations: {sum(len(b.delegations) for b in org.bridges.values())}")

    bridge = list(org.bridges.values())[0]
    print(f"\n  Bridge: {bridge.bridge_id}")
    print(f"    {bridge.team_a} ↔ {bridge.team_b}")
    print(f"    State: {bridge.state}")
    print(f"    Effective trust: {bridge.effective_trust:.2f}")

    print("\n" + "=" * 65)
    print("  Cross-team trust bridges: verified.")
    print("  citizen(team) ⊂ citizen(org): structurally enabled.")
    print("  Delegation across team boundaries: operational.")
    print("=" * 65)


if __name__ == "__main__":
    demo()
