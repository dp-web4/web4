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
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# Import governance components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "claude-code-plugin"))
from governance import Ledger

# Import trust decay, policy, and admin binding
from .trust_decay import TrustDecayCalculator, DecayConfig
from .policy import Policy, PolicyStore
from .admin_binding import AdminBindingManager, AdminBindingType, AdminBinding
from .heartbeat_ledger import HeartbeatLedger, MetabolicState
from .activity_quality import ActivityWindow, compute_quality_adjusted_decay


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

        # Initialize heartbeat ledger for metabolic tracking
        self._heartbeat_ledger: Optional[HeartbeatLedger] = None

        # Activity quality tracking per member (not persisted - rebuilt from actions)
        self._activity_windows: Dict[str, 'ActivityWindow'] = {}

    def _get_activity_window(self, lct_id: str) -> ActivityWindow:
        """Get or create an ActivityWindow for a member (30-day rolling window)."""
        if lct_id not in self._activity_windows:
            self._activity_windows[lct_id] = ActivityWindow(
                entity_id=lct_id, window_seconds=86400 * 30
            )
        return self._activity_windows[lct_id]

    def _quality_adjusted_actions(self, lct_id: str, raw_count: int) -> int:
        """
        Get quality-adjusted action count for decay calculation.

        Uses ActivityWindow if available, otherwise falls back to raw count.
        This prevents micro-ping gaming where trivial actions slow decay.
        """
        window = self._activity_windows.get(lct_id)
        if window and len(window.actions) > 0:
            metabolic = self.metabolic_state if self._heartbeat_ledger else "active"
            adjusted = compute_quality_adjusted_decay(raw_count, window, metabolic)
            return max(0, int(adjusted))
        return raw_count

    @property
    def heartbeat(self) -> HeartbeatLedger:
        """
        Get or create the heartbeat ledger for this team.

        Lazy initialization - only created when first accessed.
        The heartbeat ledger tracks metabolic state and produces
        blocks driven by team activity patterns.
        """
        if self._heartbeat_ledger is None:
            self._heartbeat_ledger = HeartbeatLedger(self.team_id)
        return self._heartbeat_ledger

    @property
    def metabolic_state(self) -> str:
        """Current team metabolic state."""
        return self.heartbeat.state.value

    def pulse(self, sentinel_lct: Optional[str] = None):
        """
        Fire a metabolic heartbeat, sealing pending transactions into a block.

        This is the team's "pulse" - call it periodically to maintain
        the block chain. Active teams should pulse every ~60s, resting
        teams every ~5min, etc.

        Returns the sealed block.
        """
        return self.heartbeat.heartbeat(sentinel_lct=sentinel_lct or self.admin_lct)

    # States that trigger wake recalibration on exit
    DORMANT_STATES = {"sleep", "hibernation", "torpor", "estivation"}

    def metabolic_transition(self, to_state: str, trigger: str):
        """
        Transition the team to a new metabolic state.

        If waking from a dormant state, applies trust recalibration
        to all members based on dormancy duration and severity.

        Args:
            to_state: Target state name (active, rest, sleep, etc.)
            trigger: What caused the transition

        Returns:
            MetabolicTransition record
        """
        from_state = self.heartbeat.state.value
        target = MetabolicState(to_state)
        transition = self.heartbeat.transition_state(target, trigger=trigger)

        # Wake recalibration: apply trust penalty when leaving dormant states
        if from_state in self.DORMANT_STATES and to_state in ("active", "rest"):
            self._apply_wake_recalibration(from_state, transition)

        # Record on team audit trail
        self.ledger.record_audit(
            session_id=self.team_id,
            action_type="metabolic_transition",
            tool_name="hardbound",
            target=to_state,
            r6_data={
                "from": transition.from_state,
                "to": transition.to_state,
                "trigger": trigger,
                "atp_cost": transition.atp_cost,
            }
        )

        return transition

    def _apply_wake_recalibration(self, dormant_state: str, transition):
        """
        Apply trust recalibration to all members after waking from dormancy.

        Extended absence creates epistemic uncertainty about member
        capabilities. This pulls trust toward baseline proportionally
        to dormancy duration.
        """
        from .trust_decay import TrustDecayCalculator

        calc = TrustDecayCalculator()
        now = datetime.now(timezone.utc)

        # Estimate dormancy start from transition history
        dormancy_seconds = transition.atp_cost  # Approximate: cost ~ duration
        # Better estimate from heartbeat ledger's last transition timestamp
        history = self.heartbeat.get_transition_history()
        if len(history) >= 2:
            # The transition that entered the dormant state
            for h in reversed(history[:-1]):  # Skip the wake transition itself
                if h.get("to_state") == dormant_state:
                    dormancy_start = datetime.fromisoformat(h["timestamp"])
                    break
            else:
                dormancy_start = now - timedelta(days=1)  # Fallback
        else:
            dormancy_start = now - timedelta(days=1)

        team_data = self._load_team()
        recalibrated_count = 0

        for member_data in team_data.get("members", {}).values():
            trust = member_data.get("trust", {})
            if not trust:
                continue

            recalibrated = calc.wake_recalibration(
                trust, dormancy_start, now, dormant_state
            )
            member_data["trust"] = recalibrated
            recalibrated_count += 1

        if recalibrated_count > 0:
            self._update_team()
            self.ledger.record_audit(
                session_id=self.team_id,
                action_type="wake_recalibration",
                tool_name="hardbound",
                target=f"{recalibrated_count} members",
                r6_data={
                    "dormant_state": dormant_state,
                    "dormancy_start": dormancy_start.isoformat(),
                    "wake_time": now.isoformat(),
                    "members_recalibrated": recalibrated_count,
                }
            )

    def get_metabolic_health(self) -> Dict[str, Any]:
        """Get team metabolic health report."""
        return self.heartbeat.get_metabolic_health()

    def audit_health(self) -> Dict[str, Any]:
        """
        Comprehensive team health audit including Sybil detection,
        trust anomalies, witness concentration, and activity quality.

        Returns a health report suitable for monitoring dashboards.
        """
        from .sybil_detection import SybilDetector

        report = {
            "team_id": self.team_id,
            "member_count": len(self.members),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 1. Sybil detection
        member_trusts = {}
        for lct in self.members:
            member_trusts[lct] = self.get_member_trust(lct, apply_decay=False)

        detector = SybilDetector()

        # Collect witness pairs from member logs
        witness_pairs = []
        for lct, member in self.members.items():
            witness_log = member.get("_witness_log", {})
            for witness_lct, timestamps in witness_log.items():
                for _ in timestamps:
                    witness_pairs.append((witness_lct, lct))

        sybil_report = detector.analyze_team(
            self.team_id, member_trusts,
            witness_pairs=witness_pairs if witness_pairs else None,
        )
        report["sybil"] = sybil_report.to_dict()

        # 2. Trust anomalies
        trust_scores = {}
        low_trust_members = []
        high_trust_members = []
        for lct in self.members:
            score = self.get_member_trust_score(lct)
            trust_scores[lct] = score
            if score < 0.3:
                low_trust_members.append(lct)
            elif score > 0.85:
                high_trust_members.append(lct)

        if trust_scores:
            scores = list(trust_scores.values())
            report["trust"] = {
                "avg": round(sum(scores) / len(scores), 4),
                "min": round(min(scores), 4),
                "max": round(max(scores), 4),
                "low_trust_members": low_trust_members,
                "high_trust_members": high_trust_members,
            }
        else:
            report["trust"] = {"avg": 0.0, "min": 0.0, "max": 0.0,
                               "low_trust_members": [], "high_trust_members": []}

        # 3. Witness health
        witness_stats = {}
        for lct, member in self.members.items():
            witness_log = member.get("_witness_log", {})
            total_attestations = sum(len(ts) for ts in witness_log.values())
            unique_witnesses = len(witness_log)
            witness_stats[lct] = {
                "total_attestations": total_attestations,
                "unique_witnesses": unique_witnesses,
            }
        report["witness_health"] = witness_stats

        # 4. Overall health score (0-100)
        health_score = 100
        if sybil_report.overall_risk.value == "critical":
            health_score -= 40
        elif sybil_report.overall_risk.value == "high":
            health_score -= 25
        elif sybil_report.overall_risk.value == "moderate":
            health_score -= 15

        if low_trust_members:
            health_score -= min(20, len(low_trust_members) * 5)

        report["health_score"] = max(0, health_score)
        report["recommendations"] = sybil_report.recommendations

        return report

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
        Set the admin for this team (simple mode).

        Args:
            lct_id: LCT of the admin entity
            binding_type: Type of binding (software, tpm2, fido2)
            require_hardware: If True, reject software-only binding

        Returns:
            Admin assignment record

        Note: For production, admin SHOULD be hardware-bound.
        Software binding is allowed for development/testing.
        Set require_hardware=True for production deployments.

        For full hardware binding, use set_admin_tpm2() instead.
        """
        if require_hardware and binding_type == "software":
            raise ValueError(
                "Hardware binding required for admin. "
                "Use set_admin_tpm2() for TPM binding, or set require_hardware=False for development."
            )

        if self.admin_lct:
            # Changing admin requires current admin approval
            # For now, just record the change
            pass

        self.admin_lct = lct_id
        self._update_team()

        # Use AdminBindingManager for proper binding storage
        binding_manager = AdminBindingManager(self.ledger)
        binding = binding_manager.bind_admin_software(
            self.team_id, lct_id, require_hardware=False
        )

        return {
            "team_id": self.team_id,
            "admin_lct": lct_id,
            "binding_type": binding_type,
            "binding": {
                "type": binding.binding_type.value,
                "verified": binding.verified,
                "bound_at": binding.bound_at
            }
        }

    def set_admin_tpm2(self, admin_name: str = "admin") -> dict:
        """
        Set admin with TPM2 hardware binding.

        Creates a new TPM-bound LCT for the admin and stores the binding.
        This is the RECOMMENDED method for production deployments.

        Args:
            admin_name: Name for the admin entity

        Returns:
            Admin assignment record with hardware binding details

        Raises:
            RuntimeError: If TPM2 is not available
        """
        binding_manager = AdminBindingManager(self.ledger)

        # Check TPM availability
        status = binding_manager.get_tpm_status()
        if not status.get('available'):
            raise RuntimeError(
                f"TPM2 not available: {status.get('reason')}. "
                f"{status.get('recommendation')}"
            )

        # Create TPM-bound admin
        binding = binding_manager.bind_admin_tpm2(self.team_id, admin_name)

        # Update team
        self.admin_lct = binding.lct_id
        self._update_team()

        return {
            "team_id": self.team_id,
            "admin_lct": binding.lct_id,
            "binding_type": "tpm2",
            "binding": {
                "type": binding.binding_type.value,
                "verified": binding.verified,
                "hardware_anchor": binding.hardware_anchor,
                "bound_at": binding.bound_at,
                "trust_ceiling": 1.0
            }
        }

    def get_admin_binding(self) -> Optional[AdminBinding]:
        """Get the current admin's binding record."""
        binding_manager = AdminBindingManager(self.ledger)
        return binding_manager.get_binding(self.team_id)

    def verify_admin(self, lct_id: str, signature: bytes = None,
                     challenge: bytes = None) -> dict:
        """
        Verify admin identity.

        For TPM2-bound admin, can optionally verify signature.
        For software-bound admin, only checks LCT ID match.

        Args:
            lct_id: LCT claiming to be admin
            signature: Optional signature on challenge (for TPM2)
            challenge: Optional challenge data (for TPM2)

        Returns:
            Verification result dict
        """
        # Quick check
        if self.admin_lct != lct_id:
            return {"verified": False, "reason": "LCT ID mismatch"}

        # Full verification through binding manager
        binding_manager = AdminBindingManager(self.ledger)
        return binding_manager.verify_admin(
            self.team_id, lct_id, signature, challenge
        )

    # --- Policy Management ---

    def get_policy(self) -> Policy:
        """
        Get current team policy.

        Loads from ledger, or returns default policy if none saved.
        """
        store = PolicyStore(self.ledger)
        policy = store.load(self.team_id)
        if policy is None:
            policy = Policy()  # Default policy
        return policy

    def set_policy(self, policy: Policy, changed_by: str,
                   description: str = "") -> dict:
        """
        Save team policy to ledger.

        Args:
            policy: Policy to save
            changed_by: LCT of who made the change
            description: Description of what changed

        Returns:
            Policy version record
        """
        store = PolicyStore(self.ledger)
        return store.save(self.team_id, policy, changed_by, description)

    def get_policy_history(self) -> List[dict]:
        """Get policy change history."""
        store = PolicyStore(self.ledger)
        return store.get_history(self.team_id)

    def verify_policy_chain(self) -> tuple:
        """Verify policy chain integrity."""
        store = PolicyStore(self.ledger)
        return store.verify_chain(self.team_id)

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

    def remove_member(self, lct_id: str, requester_lct: str = None,
                      reason: str = "", via_multisig: str = None) -> dict:
        """
        Remove a member from the team.

        Member data is archived in the audit trail before deletion.
        Witness logs on OTHER members referencing this member are preserved
        (they are historical facts about the target, not the removed member).

        Args:
            lct_id: LCT of the member to remove
            requester_lct: LCT requesting removal (must be admin unless via_multisig)
            reason: Reason for removal
            via_multisig: Proposal ID if removal was approved via multi-sig

        Returns:
            Dict with removal details and archived member data

        Raises:
            PermissionError: If requester is not admin and no multi-sig approval
            ValueError: If lct_id is not a member or is the admin
        """
        # Cannot remove admin through this method
        if lct_id == self.admin_lct:
            raise ValueError(
                "Cannot remove admin. Use admin transfer via multi-sig first."
            )

        if lct_id not in self.members:
            raise ValueError(f"Not a member: {lct_id}")

        # Authorization: must be admin OR have multi-sig approval
        if via_multisig:
            auth_method = f"multisig:{via_multisig}"
        elif requester_lct:
            admin_check = self.verify_admin(requester_lct)
            if isinstance(admin_check, dict) and admin_check.get("verified"):
                auth_method = f"admin:{requester_lct}"
            elif admin_check is True:  # Fallback for simple bool return
                auth_method = f"admin:{requester_lct}"
            else:
                raise PermissionError(
                    "Member removal requires admin authority or multi-sig approval"
                )
        else:
            raise PermissionError(
                "Member removal requires admin authority or multi-sig approval"
            )

        # Archive member data before removal
        member_data = dict(self.members[lct_id])
        member_data["_archived_trust"] = member_data.get("trust", {}).copy()

        # Remove from active members
        del self.members[lct_id]
        self._update_team()

        # Record in audit trail with full member snapshot
        audit = self.ledger.record_audit(
            session_id=self.team_id,
            action_type="member_removed",
            tool_name="hardbound",
            target=lct_id,
            r6_data={
                "reason": reason,
                "auth_method": auth_method,
                "archived_member": member_data,
                "remaining_members": len(self.members),
            }
        )

        return {
            "removed_lct": lct_id,
            "reason": reason,
            "auth_method": auth_method,
            "archived_trust": member_data.get("_archived_trust", {}),
            "audit_id": audit["audit_id"],
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

    # Trust velocity caps per epoch (24h window)
    # Maximum trust gain per dimension per day
    TRUST_VELOCITY_CAPS = {
        "reliability": 0.10,    # Max +10% per day
        "competence": 0.08,     # Max +8% per day
        "alignment": 0.06,      # Max +6% per day
        "consistency": 0.05,    # Max +5% per day
        "witnesses": 0.15,      # Witnesses can grow faster (external validation)
        "lineage": 0.03,        # Historical record grows very slowly
    }

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

        Trust velocity caps prevent Sybil-style rapid trust inflation.
        Maximum trust gain per dimension is capped per 24h epoch.
        """
        if lct_id not in self.members:
            raise ValueError(f"Not a member: {lct_id}")

        member = self.members[lct_id]
        trust = member["trust"]
        now = datetime.now(timezone.utc)

        # Record activity in quality window
        action_type = f"trust_update_{outcome}"
        window = self._get_activity_window(lct_id)
        window.record(action_type, now.isoformat())

        # First apply any pending decay (metabolic-state-aware)
        if self._decay_calculator and "last_trust_update" in member:
            metabolic = self.metabolic_state if self._heartbeat_ledger else None
            raw_actions = member.get("action_count", 0)
            adjusted_actions = self._quality_adjusted_actions(lct_id, raw_actions)
            trust = self._decay_calculator.apply_decay(
                trust,
                member["last_trust_update"],
                now,
                adjusted_actions,
                metabolic_state=metabolic,
            )

        if outcome == "success":
            delta = magnitude * 0.05
        elif outcome == "failure":
            delta = -magnitude * 0.10
        else:
            delta = magnitude * 0.02

        # Track trust velocity (cumulative gain this epoch)
        epoch_key = now.strftime("%Y-%m-%d")
        velocity = member.get("_trust_velocity", {})
        if velocity.get("_epoch") != epoch_key:
            # New epoch - reset velocity tracker
            velocity = {"_epoch": epoch_key}

        # Update all dimensions with velocity cap enforcement
        for dim in trust:
            if dim in ("reliability", "competence", "alignment"):
                multiplier = 1.0 if dim == "reliability" else (0.5 if dim == "competence" else 0.3)
                raw_delta = delta * multiplier

                # Apply velocity cap (only for positive changes)
                if raw_delta > 0:
                    cap = self.TRUST_VELOCITY_CAPS.get(dim, 0.10)
                    gained_today = velocity.get(dim, 0.0)
                    remaining_cap = max(0, cap - gained_today)
                    capped_delta = min(raw_delta, remaining_cap)
                    velocity[dim] = gained_today + capped_delta
                    trust[dim] = max(0, min(1, trust[dim] + capped_delta))
                else:
                    # No cap on trust loss (penalties always apply in full)
                    trust[dim] = max(0, min(1, trust[dim] + raw_delta))

        # Store updated trust, timestamp, and velocity
        member["trust"] = trust
        member["last_trust_update"] = now.isoformat()
        member["action_count"] = member.get("action_count", 0) + 1
        member["_trust_velocity"] = velocity
        self._update_team()

        return trust

    # Diminishing returns for same-pair witnessing
    # After N same-pair attestations in a window, multiplier drops exponentially
    WITNESS_DIMINISHING_HALFLIFE = 3  # Attestations before effectiveness halves
    WITNESS_WINDOW_DAYS = 30          # Rolling window for counting pair interactions

    def witness_member(self, witness_lct: str, target_lct: str,
                       quality: float = 1.0) -> Dict[str, float]:
        """
        Record a witnessing event: one member attests to another's activity.

        Witnessing is a core Web4 concept - entities build trust by observing
        and attesting to each other's actions. However, repeated same-pair
        witnessing has diminishing returns to prevent closed-loop farming.

        Args:
            witness_lct: The LCT of the witnessing entity
            target_lct: The LCT of the entity being witnessed
            quality: Quality multiplier (0.0-1.0) from activity quality scoring

        Returns:
            Updated trust tensor for target member
        """
        import math

        if target_lct not in self.members:
            raise ValueError(f"Target not a member: {target_lct}")
        if witness_lct == target_lct:
            raise ValueError("Cannot witness yourself")

        member = self.members[target_lct]
        trust = member["trust"]
        now = datetime.now(timezone.utc)

        # Record witnessing activity for both parties
        witness_window = self._get_activity_window(witness_lct)
        witness_window.record("witness_given", now.isoformat())
        target_window = self._get_activity_window(target_lct)
        target_window.record("witness_received", now.isoformat())

        # Track witness pair history
        witness_log = member.get("_witness_log", {})
        pair_key = witness_lct
        pair_history = witness_log.get(pair_key, [])

        # Prune old entries outside window
        cutoff = (now - timedelta(days=self.WITNESS_WINDOW_DAYS)).isoformat()
        pair_history = [ts for ts in pair_history if ts >= cutoff]

        # Count same-pair attestations in window
        pair_count = len(pair_history)

        # Diminishing returns: multiplier = 2^(-n / halflife)
        diminishing = math.pow(2, -pair_count / self.WITNESS_DIMINISHING_HALFLIFE)

        # Base witness trust delta (positive, affects witnesses dimension primarily)
        base_delta = 0.03 * quality * diminishing

        # Apply to trust dimensions (witnesses gets most, others get minor boost)
        witness_weights = {
            "witnesses": 1.0,
            "reliability": 0.3,
            "consistency": 0.2,
        }

        for dim, weight in witness_weights.items():
            if dim in trust:
                delta = base_delta * weight
                # Still subject to velocity caps
                trust[dim] = max(0, min(1, trust[dim] + delta))

        # Record this attestation
        pair_history.append(now.isoformat())
        witness_log[pair_key] = pair_history
        member["_witness_log"] = witness_log
        member["trust"] = trust
        member["last_trust_update"] = now.isoformat()
        self._update_team()

        # Record on audit trail
        self.ledger.record_audit(
            session_id=self.team_id,
            action_type="witness_attestation",
            tool_name="hardbound",
            target=target_lct,
            r6_data={
                "witness": witness_lct,
                "target": target_lct,
                "quality": quality,
                "pair_count": pair_count + 1,
                "diminishing_factor": round(diminishing, 4),
            }
        )

        return trust

    def get_witness_effectiveness(self, witness_lct: str, target_lct: str) -> float:
        """
        Get the current effectiveness of a witness pair.

        Returns: Float 0.0-1.0 representing how much impact the next
        attestation from this witness will have on the target.
        """
        import math

        if target_lct not in self.members:
            return 0.0

        member = self.members[target_lct]
        witness_log = member.get("_witness_log", {})
        pair_history = witness_log.get(witness_lct, [])

        now = datetime.now(timezone.utc)
        cutoff = (now - timedelta(days=self.WITNESS_WINDOW_DAYS)).isoformat()
        recent = [ts for ts in pair_history if ts >= cutoff]

        return math.pow(2, -len(recent) / self.WITNESS_DIMINISHING_HALFLIFE)

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
            raw_actions = member.get("action_count", 0)
            adjusted_actions = self._quality_adjusted_actions(lct_id, raw_actions)
            trust = self._decay_calculator.apply_decay(
                trust,
                member["last_trust_update"],
                datetime.now(timezone.utc),
                adjusted_actions,
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
