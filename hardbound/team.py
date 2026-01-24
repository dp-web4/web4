# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - Team (Society) Implementation
# https://github.com/dp-web4/web4

"""
Team: A governed organization of entities.

A Team is a Web4 Society with enterprise terminology:
- Root LCT identifying the team itself
- Ledger for immutable record keeping
- Admin role for governance
- Members with assigned roles
- Policy for rules enforcement

Key insight: A team IS an entity. It has its own LCT, can be a member
of other teams (fractal structure), and accumulates its own trust.
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# Import governance components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "claude-code-plugin"))
from governance import Ledger

# Import trust decay
from .trust_decay import TrustDecayCalculator, DecayConfig


@dataclass
class TeamConfig:
    """Configuration for a team."""
    name: str
    description: str = ""

    # Heartbeat policy (metabolic timing)
    heartbeat_min_seconds: int = 30
    heartbeat_max_seconds: int = 3600

    # ATP defaults
    default_member_budget: int = 100

    # Trust thresholds for actions
    action_trust_threshold: float = 0.5
    admin_trust_threshold: float = 0.8

    # Trust decay settings
    enable_trust_decay: bool = True
    decay_config: Optional[DecayConfig] = None


class Team:
    """
    A governed team (Web4 society with enterprise terminology).

    Structure:
        Team (root LCT)
        ├── Ledger (immutable records)
        ├── Members (each with LCT)
        ├── Roles (admin required, others optional)
        └── Policy (rules from ledger)
    """

    def __init__(self, team_id: Optional[str] = None, config: Optional[TeamConfig] = None,
                 ledger: Optional[Ledger] = None):
        """
        Initialize or load a team.

        Args:
            team_id: Existing team ID to load, or None to create new
            config: Team configuration (required for new teams)
            ledger: Ledger instance (creates default if None)
        """
        self.ledger = ledger or Ledger()
        self._decay_calculator: Optional[TrustDecayCalculator] = None

        if team_id:
            # Load existing team
            self._load_team(team_id)
        else:
            # Create new team
            if config is None:
                raise ValueError("config required for new team")
            self._create_team(config)

        # Initialize decay calculator if enabled
        if self.config.enable_trust_decay:
            decay_config = self.config.decay_config or DecayConfig()
            self._decay_calculator = TrustDecayCalculator(decay_config)

    def _create_team(self, config: TeamConfig):
        """Create a new team."""
        # Generate team LCT (the team itself is an entity)
        timestamp = datetime.now(timezone.utc)
        seed = f"team:{config.name}:{timestamp.isoformat()}"
        team_hash = hashlib.sha256(seed.encode()).hexdigest()[:12]

        self.team_id = f"web4:team:{team_hash}"
        self.config = config
        self.created_at = timestamp.isoformat() + "Z"
        self.members: Dict[str, dict] = {}
        self.admin_lct: Optional[str] = None

        # Store team in ledger
        self._store_team()

        # Record genesis entry in audit trail
        self.ledger.record_audit(
            session_id=self.team_id,
            action_type="team_created",
            tool_name="hardbound",
            target=config.name,
            r6_data={
                "config": asdict(config),
                "created_at": self.created_at
            }
        )

    def _load_team(self, team_id: str):
        """Load existing team from ledger."""
        team_data = self._get_team_data(team_id)
        if not team_data:
            raise ValueError(f"Team not found: {team_id}")

        self.team_id = team_id
        self.config = TeamConfig(**json.loads(team_data["config"]))
        self.created_at = team_data["created_at"]
        self.admin_lct = team_data.get("admin_lct")
        self.members = json.loads(team_data.get("members", "{}"))

    def _store_team(self):
        """Store team data in ledger database."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            # Create teams table if not exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    team_id TEXT PRIMARY KEY,
                    config TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    admin_lct TEXT,
                    members TEXT DEFAULT '{}'
                )
            """)

            conn.execute("""
                INSERT OR REPLACE INTO teams (team_id, config, created_at, admin_lct, members)
                VALUES (?, ?, ?, ?, ?)
            """, (
                self.team_id,
                json.dumps(asdict(self.config)),
                self.created_at,
                self.admin_lct,
                json.dumps(self.members)
            ))

    def _get_team_data(self, team_id: str) -> Optional[dict]:
        """Get team data from database."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM teams WHERE team_id = ?", (team_id,)
            ).fetchone()
            return dict(row) if row else None

    def _update_team(self):
        """Update team data in database."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.execute("""
                UPDATE teams SET admin_lct = ?, members = ?
                WHERE team_id = ?
            """, (self.admin_lct, json.dumps(self.members), self.team_id))

    # --- Admin Management ---

    def set_admin(self, lct_id: str, binding_type: str = "software",
                  require_hardware: bool = False) -> dict:
        """
        Set the admin for this team.

        Args:
            lct_id: LCT of the admin entity
            binding_type: Type of binding (software, tpm, fido2)
            require_hardware: If True, reject software-only binding

        Returns:
            Admin assignment record

        Note: For production, admin SHOULD be hardware-bound.
        Software binding is allowed for development/testing.
        Set require_hardware=True for production deployments.
        """
        if require_hardware and binding_type == "software":
            raise ValueError(
                "Hardware binding required for admin. "
                "Use TPM or FIDO2, or set require_hardware=False for development."
            )

        if self.admin_lct:
            # Changing admin requires current admin approval
            # For now, just record the change
            pass

        self.admin_lct = lct_id
        self._update_team()

        # Record in audit trail
        audit = self.ledger.record_audit(
            session_id=self.team_id,
            action_type="admin_assigned",
            tool_name="hardbound",
            target=lct_id,
            r6_data={
                "binding_type": binding_type,
                "trust_note": "Hardware binding recommended for production"
                    if binding_type == "software" else "Hardware-bound admin"
            }
        )

        return {
            "team_id": self.team_id,
            "admin_lct": lct_id,
            "binding_type": binding_type,
            "audit_id": audit["audit_id"]
        }

    def verify_admin(self, lct_id: str) -> bool:
        """Check if LCT is the current admin."""
        return self.admin_lct == lct_id

    # --- Member Management ---

    def add_member(self, lct_id: str, role: str = "member",
                   atp_budget: Optional[int] = None) -> dict:
        """
        Add a member to the team.

        Args:
            lct_id: LCT of the entity to add
            role: Role assignment (member, reviewer, deployer, etc.)
            atp_budget: Initial ATP budget (uses default if None)

        Returns:
            Member record
        """
        if lct_id in self.members:
            raise ValueError(f"Already a member: {lct_id}")

        budget = atp_budget if atp_budget is not None else self.config.default_member_budget

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        member = {
            "lct_id": lct_id,
            "role": role,
            "atp_budget": budget,
            "atp_consumed": 0,
            "joined_at": now_iso,
            "trust": {
                "competence": 0.5,
                "reliability": 0.5,
                "alignment": 0.5,
                "consistency": 0.5,
                "witnesses": 0.5,
                "lineage": 0.5
            },
            "last_trust_update": now_iso,
            "action_count": 0
        }

        self.members[lct_id] = member
        self._update_team()

        # Record in audit trail
        audit = self.ledger.record_audit(
            session_id=self.team_id,
            action_type="member_added",
            tool_name="hardbound",
            target=lct_id,
            r6_data={
                "role": role,
                "atp_budget": budget
            }
        )

        return {
            **member,
            "audit_id": audit["audit_id"]
        }

    def get_member(self, lct_id: str) -> Optional[dict]:
        """Get member info by LCT."""
        return self.members.get(lct_id)

    def list_members(self) -> List[dict]:
        """List all members."""
        return list(self.members.values())

    def update_member_role(self, lct_id: str, new_role: str,
                           requester_lct: str) -> dict:
        """
        Update a member's role.

        Requires admin approval (requester must be admin).
        """
        if not self.verify_admin(requester_lct):
            raise PermissionError("Only admin can change roles")

        if lct_id not in self.members:
            raise ValueError(f"Not a member: {lct_id}")

        old_role = self.members[lct_id]["role"]
        self.members[lct_id]["role"] = new_role
        self._update_team()

        audit = self.ledger.record_audit(
            session_id=self.team_id,
            action_type="role_changed",
            tool_name="hardbound",
            target=lct_id,
            r6_data={
                "old_role": old_role,
                "new_role": new_role,
                "approved_by": requester_lct
            }
        )

        return {
            "lct_id": lct_id,
            "old_role": old_role,
            "new_role": new_role,
            "audit_id": audit["audit_id"]
        }

    # --- ATP Management ---

    def consume_member_atp(self, lct_id: str, amount: int) -> int:
        """
        Consume ATP from member's budget.

        Returns remaining ATP.
        """
        if lct_id not in self.members:
            raise ValueError(f"Not a member: {lct_id}")

        member = self.members[lct_id]
        remaining = member["atp_budget"] - member["atp_consumed"]

        if amount > remaining:
            raise ValueError(f"Insufficient ATP: need {amount}, have {remaining}")

        member["atp_consumed"] += amount
        member["action_count"] += 1
        self._update_team()

        return member["atp_budget"] - member["atp_consumed"]

    def get_member_atp(self, lct_id: str) -> int:
        """Get member's remaining ATP."""
        if lct_id not in self.members:
            return 0
        member = self.members[lct_id]
        return member["atp_budget"] - member["atp_consumed"]

    # --- Trust Management ---

    def update_member_trust(self, lct_id: str, outcome: str,
                            magnitude: float = 0.1) -> dict:
        """
        Update member's trust based on action outcome.

        Args:
            lct_id: Member LCT
            outcome: "success", "failure", or "partial"
            magnitude: Update magnitude (0.0 to 1.0)

        Returns:
            Updated trust tensor (after decay applied)
        """
        if lct_id not in self.members:
            raise ValueError(f"Not a member: {lct_id}")

        member = self.members[lct_id]
        trust = member["trust"]
        now = datetime.now(timezone.utc)

        # First apply any pending decay
        if self._decay_calculator and "last_trust_update" in member:
            trust = self._decay_calculator.apply_decay(
                trust,
                member["last_trust_update"],
                now,
                member.get("action_count", 0)
            )

        if outcome == "success":
            delta = magnitude * 0.05
        elif outcome == "failure":
            delta = -magnitude * 0.10
        else:
            delta = magnitude * 0.02

        # Update all dimensions
        for dim in trust:
            if dim in ("reliability", "competence", "alignment"):
                multiplier = 1.0 if dim == "reliability" else (0.5 if dim == "competence" else 0.3)
                trust[dim] = max(0, min(1, trust[dim] + delta * multiplier))

        # Store updated trust and timestamp
        member["trust"] = trust
        member["last_trust_update"] = now.isoformat()
        member["action_count"] = member.get("action_count", 0) + 1
        self._update_team()

        return trust

    def get_member_trust(self, lct_id: str, apply_decay: bool = True) -> Dict[str, float]:
        """
        Get member's full trust tensor.

        Args:
            lct_id: Member LCT
            apply_decay: Whether to apply time-based decay

        Returns:
            Trust tensor with all dimensions
        """
        if lct_id not in self.members:
            return {}

        member = self.members[lct_id]
        trust = member["trust"].copy()

        if apply_decay and self._decay_calculator and "last_trust_update" in member:
            trust = self._decay_calculator.apply_decay(
                trust,
                member["last_trust_update"],
                datetime.now(timezone.utc),
                member.get("action_count", 0)
            )

        return trust

    def get_member_trust_score(self, lct_id: str, apply_decay: bool = True) -> float:
        """
        Get member's aggregate trust score (0.0 to 1.0).

        Args:
            lct_id: Member LCT
            apply_decay: Whether to apply time-based decay

        Returns:
            Weighted trust score
        """
        trust = self.get_member_trust(lct_id, apply_decay=apply_decay)
        if not trust:
            return 0.0

        # Weighted average (using only the primary dimensions)
        return (trust.get("competence", 0.5) * 0.25 +
                trust.get("reliability", 0.5) * 0.20 +
                trust.get("consistency", 0.5) * 0.15 +
                trust.get("witnesses", 0.5) * 0.15 +
                trust.get("lineage", 0.5) * 0.15 +
                trust.get("alignment", 0.5) * 0.10)

    # --- Team Info ---

    def summary(self) -> dict:
        """Get team summary."""
        return {
            "team_id": self.team_id,
            "name": self.config.name,
            "description": self.config.description,
            "created_at": self.created_at,
            "admin_lct": self.admin_lct,
            "member_count": len(self.members),
            "members": [
                {
                    "lct_id": m["lct_id"],
                    "role": m["role"],
                    "trust_score": self.get_member_trust_score(m["lct_id"]),
                    "atp_remaining": m["atp_budget"] - m["atp_consumed"]
                }
                for m in self.members.values()
            ]
        }

    def get_audit_trail(self) -> List[dict]:
        """Get team's audit trail."""
        return self.ledger.get_session_audit_trail(self.team_id)

    def verify_audit_chain(self) -> tuple:
        """Verify team's audit chain integrity."""
        return self.ledger.verify_audit_chain(self.team_id)


def list_teams(ledger: Optional[Ledger] = None) -> List[dict]:
    """List all teams in the ledger."""
    ledger = ledger or Ledger()

    with sqlite3.connect(ledger.db_path) as conn:
        conn.row_factory = sqlite3.Row

        # Check if teams table exists
        exists = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='teams'
        """).fetchone()

        if not exists:
            return []

        rows = conn.execute("SELECT team_id, config, created_at FROM teams").fetchall()

        return [
            {
                "team_id": row["team_id"],
                "config": json.loads(row["config"]),
                "created_at": row["created_at"]
            }
            for row in rows
        ]
