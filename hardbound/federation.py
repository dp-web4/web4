# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - Federation Registry
# https://github.com/dp-web4/web4

"""
Federation Registry: Cross-team discovery, witnessing, and trust.

Teams exist in isolation until they federate. The Federation Registry enables:

1. **Team Discovery**: Find teams by domain, capability, or role
2. **Witness Pool**: Qualified external witnesses for multi-sig proposals
3. **Cross-Team Trust**: Track team reputation as witnesses
4. **Collusion Detection**: Monitor witness reciprocity patterns

Architecture:
- Each team registers its public profile (team_id, name, domains, capabilities)
- The registry maintains a witness graph tracking which teams witness for which
- Witness reputation scores track accuracy (did witnessed proposals succeed?)
- Reciprocity analysis detects collusion rings

This is the "social layer" that makes cross-team witnessing practical.
Without it, external witnesses must be manually arranged.
"""

import hashlib
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Set, Tuple
from pathlib import Path
from enum import Enum


class FederationStatus(Enum):
    """Status of a team in the federation."""
    ACTIVE = "active"
    SUSPENDED = "suspended"  # Temporarily suspended (under review)
    REVOKED = "revoked"      # Permanently removed


@dataclass
class FederatedTeam:
    """A team's public profile in the federation registry."""
    team_id: str
    name: str
    registered_at: str
    status: FederationStatus = FederationStatus.ACTIVE

    # Public capabilities and domain tags
    domains: List[str] = field(default_factory=list)  # e.g., ["finance", "audit"]
    capabilities: List[str] = field(default_factory=list)  # e.g., ["external_witnessing"]

    # Contact/discovery info
    admin_lct: str = ""  # Public admin LCT for verification
    member_count: int = 0

    # Creation lineage - who created this team
    creator_lct: str = ""  # LCT of the entity that created this team

    # Activity tracking for reputation decay
    last_activity: str = ""  # ISO timestamp of last activity (proposal, approval, witness)

    # Witness reputation
    witness_score: float = 1.0  # 0.0 (terrible) to 1.0 (perfect)
    witness_count: int = 0      # Total times this team provided witnesses
    witness_successes: int = 0  # Proposals that succeeded after this team witnessed
    witness_failures: int = 0   # Proposals that failed/were reversed after witnessing

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'FederatedTeam':
        data = dict(data)
        data["status"] = FederationStatus(data.get("status", "active"))
        return cls(**data)


@dataclass
class WitnessRecord:
    """Record of a cross-team witnessing event."""
    witness_team_id: str    # Team that provided the witness
    proposal_team_id: str   # Team that had the proposal
    witness_lct: str        # LCT of the individual witness
    proposal_id: str        # ID of the proposal witnessed
    timestamp: str
    outcome: str = "pending"  # pending, succeeded, failed, reversed


class FederationRegistry:
    """
    Registry for cross-team discovery and witness coordination.

    The federation registry is the backbone of cross-team trust.
    It enables teams to find qualified external witnesses and
    tracks the reputation of teams as witnesses over time.
    """

    # Minimum witness score to be eligible as external witness
    MIN_WITNESS_SCORE = 0.3

    # Number of recent witness events to analyze for reciprocity
    RECIPROCITY_WINDOW = 50

    # Maximum reciprocity ratio before flagging collusion
    MAX_RECIPROCITY_RATIO = 0.6  # If >60% of witnessing is reciprocal, flag it

    # Severity levels for adaptive thresholds
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"

    # Default adaptive threshold policies per severity level
    # These can be overridden per-federation
    DEFAULT_SEVERITY_POLICIES = {
        "low": {
            "approval_threshold": 0.5,       # Simple majority
            "require_outsider": False,
            "min_approvals_ratio": 0.5,      # 50% of target teams
            "min_reputation": 0.3,           # Any active team can participate
            "voting_mode": "weighted",
        },
        "medium": {
            "approval_threshold": 0.6,       # 60% weighted approval
            "require_outsider": False,
            "min_approvals_ratio": 0.6,
            "min_reputation": 0.5,           # Moderate reputation required
            "voting_mode": "weighted",
        },
        "high": {
            "approval_threshold": 0.75,      # 75% weighted approval
            "require_outsider": True,        # Neutral third party required
            "min_approvals_ratio": 0.75,
            "min_reputation": 0.7,           # High reputation required
            "voting_mode": "weighted",
        },
        "critical": {
            "approval_threshold": 0.9,       # Near-unanimous
            "require_outsider": True,
            "min_approvals_ratio": 1.0,      # All teams must approve
            "min_reputation": 0.8,           # Only trusted teams
            "voting_mode": "veto",           # Any team can block
        },
    }

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the federation registry.

        Args:
            db_path: Path to SQLite database. Defaults to temp file.
        """
        if db_path:
            self.db_path = db_path
        else:
            import tempfile
            self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
            self.db_path = self._tmp.name
        self._ensure_tables()

    def _ensure_tables(self):
        """Create federation tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS federated_teams (
                    team_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    registered_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    domains TEXT DEFAULT '[]',
                    capabilities TEXT DEFAULT '[]',
                    admin_lct TEXT DEFAULT '',
                    creator_lct TEXT DEFAULT '',
                    member_count INTEGER DEFAULT 0,
                    last_activity TEXT DEFAULT '',
                    witness_score REAL DEFAULT 1.0,
                    witness_count INTEGER DEFAULT 0,
                    witness_successes INTEGER DEFAULT 0,
                    witness_failures INTEGER DEFAULT 0
                )
            """)
            # Add last_activity column if not exists (migration)
            try:
                conn.execute("ALTER TABLE federated_teams ADD COLUMN last_activity TEXT DEFAULT ''")
            except sqlite3.OperationalError:
                pass  # Column already exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS witness_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    witness_team_id TEXT NOT NULL,
                    proposal_team_id TEXT NOT NULL,
                    witness_lct TEXT NOT NULL,
                    proposal_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    outcome TEXT DEFAULT 'pending',
                    FOREIGN KEY (witness_team_id) REFERENCES federated_teams(team_id),
                    FOREIGN KEY (proposal_team_id) REFERENCES federated_teams(team_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_witness_records_teams
                ON witness_records(witness_team_id, proposal_team_id)
            """)
            # Backwards-compatible schema migration for creator_lct
            try:
                conn.execute(
                    "ALTER TABLE federated_teams ADD COLUMN creator_lct TEXT DEFAULT ''"
                )
            except sqlite3.OperationalError:
                pass  # Column already exists
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_creator_lct
                ON federated_teams(creator_lct)
            """)

    def register_team(self, team_id: str, name: str,
                      domains: List[str] = None,
                      capabilities: List[str] = None,
                      admin_lct: str = "",
                      creator_lct: str = "",
                      member_count: int = 0) -> FederatedTeam:
        """
        Register a team in the federation.

        Args:
            team_id: Unique team identifier
            name: Human-readable team name
            domains: Domain tags for discovery
            capabilities: Capability tags
            admin_lct: Public admin LCT
            creator_lct: LCT of the entity that created this team (for lineage tracking)
            member_count: Number of team members

        Returns:
            FederatedTeam registration record

        Raises:
            ValueError: If team already registered
        """
        # Check for existing registration
        existing = self.get_team(team_id)
        if existing:
            raise ValueError(f"Team already registered: {team_id}")

        now = datetime.now(timezone.utc).isoformat()
        team = FederatedTeam(
            team_id=team_id,
            name=name,
            registered_at=now,
            domains=domains or [],
            capabilities=capabilities or ["external_witnessing"],
            admin_lct=admin_lct,
            creator_lct=creator_lct,
            member_count=member_count,
            last_activity=now,  # Registration counts as activity
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO federated_teams
                (team_id, name, registered_at, status, domains, capabilities,
                 admin_lct, creator_lct, member_count, last_activity, witness_score, witness_count,
                 witness_successes, witness_failures)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                team.team_id, team.name, team.registered_at,
                team.status.value,
                json.dumps(team.domains), json.dumps(team.capabilities),
                team.admin_lct, team.creator_lct, team.member_count,
                team.last_activity,
                team.witness_score, team.witness_count,
                team.witness_successes, team.witness_failures,
            ))

        return team

    def get_team(self, team_id: str) -> Optional[FederatedTeam]:
        """Get a federated team by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM federated_teams WHERE team_id = ?",
                (team_id,)
            ).fetchone()
            if not row:
                return None
            return self._row_to_team(row)

    def find_teams(self, domain: str = None, capability: str = None,
                   min_witness_score: float = None,
                   exclude_team_id: str = None,
                   status: FederationStatus = FederationStatus.ACTIVE,
                   limit: int = 20) -> List[FederatedTeam]:
        """
        Find teams matching criteria. Core discovery mechanism.

        Args:
            domain: Filter by domain tag
            capability: Filter by capability tag
            min_witness_score: Minimum witness reputation score
            exclude_team_id: Exclude this team (usually the requesting team)
            status: Filter by status (default: active)
            limit: Maximum results

        Returns:
            List of matching teams, ordered by witness_score descending
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM federated_teams WHERE status = ?"
            params = [status.value]

            if exclude_team_id:
                query += " AND team_id != ?"
                params.append(exclude_team_id)

            if min_witness_score is not None:
                query += " AND witness_score >= ?"
                params.append(min_witness_score)

            query += " ORDER BY witness_score DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            teams = [self._row_to_team(row) for row in rows]

            # Post-filter for domain/capability (stored as JSON arrays)
            if domain:
                teams = [t for t in teams if domain in t.domains]
            if capability:
                teams = [t for t in teams if capability in t.capabilities]

            return teams

    def find_witness_pool(self, requesting_team_id: str,
                          count: int = 5,
                          min_score: float = None) -> List[FederatedTeam]:
        """
        Find qualified external witness candidates for a team.

        Excludes the requesting team and any teams with collusion flags.

        Args:
            requesting_team_id: Team seeking witnesses
            count: Number of candidates to return
            min_score: Minimum witness reputation score

        Returns:
            List of qualified witness candidate teams
        """
        effective_min = min_score if min_score is not None else self.MIN_WITNESS_SCORE

        # Get candidates
        candidates = self.find_teams(
            exclude_team_id=requesting_team_id,
            min_witness_score=effective_min,
            capability="external_witnessing",
            limit=count * 2,  # Get extra to account for collusion filtering
        )

        # Get requesting team's creator for lineage check
        requesting_team = self.get_team(requesting_team_id)
        requesting_creator = requesting_team.creator_lct if requesting_team else ""

        # Check for collusion and lineage conflicts
        clean_candidates = []
        for candidate in candidates:
            # Skip teams created by the same entity (lineage conflict)
            if (requesting_creator and candidate.creator_lct
                    and requesting_creator == candidate.creator_lct):
                continue

            reciprocity = self.check_reciprocity(
                requesting_team_id, candidate.team_id
            )
            if reciprocity["reciprocity_ratio"] <= self.MAX_RECIPROCITY_RATIO:
                clean_candidates.append(candidate)
            if len(clean_candidates) >= count:
                break

        return clean_candidates

    def select_witnesses(self, requesting_team_id: str,
                         count: int = 1,
                         min_score: float = None,
                         seed: int = None) -> List[FederatedTeam]:
        """
        Randomly select witnesses from the qualified pool, weighted by reputation.

        Higher-reputation teams are more likely to be selected, but randomness
        ensures that no single team becomes the permanent witness. This prevents
        witness concentration attacks.

        Args:
            requesting_team_id: Team seeking witnesses
            count: Number of witnesses to select
            min_score: Minimum witness reputation score
            seed: Optional random seed for reproducibility (testing)

        Returns:
            List of selected witness teams (may be fewer than count if pool is small)
        """
        import random

        pool = self.find_witness_pool(
            requesting_team_id, count=count * 3, min_score=min_score
        )

        if not pool:
            return []

        if len(pool) <= count:
            return pool

        # Weight by witness_score (reputation-proportional selection)
        weights = [max(t.witness_score, 0.01) for t in pool]

        rng = random.Random(seed)
        selected = []
        remaining = list(zip(pool, weights))

        for _ in range(min(count, len(remaining))):
            total = sum(w for _, w in remaining)
            r = rng.uniform(0, total)
            cumulative = 0.0
            for idx, (team, weight) in enumerate(remaining):
                cumulative += weight
                if cumulative >= r:
                    selected.append(team)
                    remaining.pop(idx)
                    break

        return selected

    def record_witness_event(self, witness_team_id: str,
                              proposal_team_id: str,
                              witness_lct: str,
                              proposal_id: str) -> WitnessRecord:
        """
        Record a cross-team witnessing event.

        Called when an external witness is added to a proposal.
        """
        now = datetime.now(timezone.utc).isoformat()
        record = WitnessRecord(
            witness_team_id=witness_team_id,
            proposal_team_id=proposal_team_id,
            witness_lct=witness_lct,
            proposal_id=proposal_id,
            timestamp=now,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO witness_records
                (witness_team_id, proposal_team_id, witness_lct, proposal_id,
                 timestamp, outcome)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                record.witness_team_id, record.proposal_team_id,
                record.witness_lct, record.proposal_id,
                record.timestamp, record.outcome,
            ))

            # Update witness count
            conn.execute("""
                UPDATE federated_teams
                SET witness_count = witness_count + 1
                WHERE team_id = ?
            """, (witness_team_id,))

        return record

    def update_witness_outcome(self, proposal_id: str,
                                outcome: str) -> int:
        """
        Update the outcome of a witnessed proposal.

        Called when a proposal completes execution.
        Updates witness reputation scores based on outcome.

        Args:
            proposal_id: The proposal that completed
            outcome: "succeeded", "failed", or "reversed"

        Returns:
            Number of witness records updated
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get affected witness records
            cursor = conn.execute(
                "SELECT witness_team_id FROM witness_records WHERE proposal_id = ?",
                (proposal_id,)
            )
            witness_teams = [row[0] for row in cursor.fetchall()]

            if not witness_teams:
                return 0

            # Update outcome
            conn.execute(
                "UPDATE witness_records SET outcome = ? WHERE proposal_id = ?",
                (outcome, proposal_id)
            )

            # Update witness reputation for each team
            for team_id in set(witness_teams):
                if outcome == "succeeded":
                    conn.execute("""
                        UPDATE federated_teams
                        SET witness_successes = witness_successes + 1
                        WHERE team_id = ?
                    """, (team_id,))
                elif outcome in ("failed", "reversed"):
                    conn.execute("""
                        UPDATE federated_teams
                        SET witness_failures = witness_failures + 1
                        WHERE team_id = ?
                    """, (team_id,))

                # Recalculate witness score
                self._recalculate_witness_score(conn, team_id)

            return len(witness_teams)

    def _recalculate_witness_score(self, conn, team_id: str):
        """Recalculate witness reputation score for a team."""
        row = conn.execute(
            "SELECT witness_count, witness_successes, witness_failures "
            "FROM federated_teams WHERE team_id = ?",
            (team_id,)
        ).fetchone()

        if not row or row[0] == 0:
            return

        total, successes, failures = row
        # Score = success rate with Bayesian smoothing (prior of 1.0 with 5 pseudo-observations)
        # This prevents a single failure from tanking a new team's score
        pseudo_successes = 5
        pseudo_total = 5
        score = (successes + pseudo_successes) / (total + pseudo_total)
        score = max(0.0, min(1.0, score))

        conn.execute(
            "UPDATE federated_teams SET witness_score = ? WHERE team_id = ?",
            (score, team_id)
        )

    def _update_last_activity(self, team_id: str, timestamp: str = None):
        """Update the last activity timestamp for a team."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE federated_teams SET last_activity = ? WHERE team_id = ?",
                (timestamp, team_id)
            )

    def _log_governance_audit(
        self,
        audit_type: str,
        details: Dict,
        proposal_id: str = None,
        team_id: str = None,
        actor_lct: str = None,
        action_type: str = None,
        risk_level: str = "info",
    ):
        """
        Log a governance audit event.

        Used to track policy overrides, anomalies, and security-relevant events.

        Args:
            audit_type: Type of audit event (e.g., "severity_override", "policy_override")
            details: Dict with event-specific details
            proposal_id: Associated proposal ID if applicable
            team_id: Team involved in the event
            actor_lct: LCT of the actor who triggered the event
            action_type: Type of action being performed
            risk_level: One of "info", "warning", "critical"
        """
        self._ensure_xteam_table()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO governance_audit
                (timestamp, audit_type, proposal_id, team_id, actor_lct, action_type, details, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(timezone.utc).isoformat(),
                audit_type,
                proposal_id,
                team_id,
                actor_lct,
                action_type,
                json.dumps(details),
                risk_level,
            ))

    def get_governance_audit_log(
        self,
        audit_type: str = None,
        risk_level: str = None,
        team_id: str = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        Retrieve governance audit events.

        Args:
            audit_type: Filter by audit type
            risk_level: Filter by risk level
            team_id: Filter by team
            limit: Maximum events to return

        Returns:
            List of audit events, newest first
        """
        self._ensure_xteam_table()
        query = "SELECT * FROM governance_audit WHERE 1=1"
        params = []

        if audit_type:
            query += " AND audit_type = ?"
            params.append(audit_type)
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level)
        if team_id:
            query += " AND team_id = ?"
            params.append(team_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "audit_type": row["audit_type"],
                "proposal_id": row["proposal_id"],
                "team_id": row["team_id"],
                "actor_lct": row["actor_lct"],
                "action_type": row["action_type"],
                "details": json.loads(row["details"]) if row["details"] else {},
                "risk_level": row["risk_level"],
            }
            for row in rows
        ]

    def apply_reputation_decay(self, decay_threshold_days: int = 30,
                                decay_rate: float = 0.1,
                                min_score: float = 0.3) -> Dict:
        """
        Apply reputation decay to inactive teams.

        Teams that haven't participated (proposed, approved, witnessed) in the
        specified period see their witness_score decay. This prevents stale
        high-reputation teams from having unearned influence.

        Args:
            decay_threshold_days: Days of inactivity before decay starts
            decay_rate: Fraction of score to decay per application (0.1 = 10%)
            min_score: Minimum score floor (won't decay below this)

        Returns:
            Report of decayed teams and new scores
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=decay_threshold_days)).isoformat()
        decayed_teams = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT team_id, name, witness_score, last_activity
                FROM federated_teams
                WHERE status = 'active'
                  AND (last_activity IS NULL OR last_activity = '' OR last_activity < ?)
                  AND witness_score > ?
            """, (cutoff, min_score)).fetchall()

            for row in rows:
                old_score = row["witness_score"]
                new_score = max(min_score, old_score * (1 - decay_rate))

                conn.execute(
                    "UPDATE federated_teams SET witness_score = ? WHERE team_id = ?",
                    (new_score, row["team_id"])
                )

                decayed_teams.append({
                    "team_id": row["team_id"],
                    "name": row["name"],
                    "old_score": old_score,
                    "new_score": new_score,
                    "decay": old_score - new_score,
                    "last_activity": row["last_activity"] or "never",
                })

        return {
            "threshold_days": decay_threshold_days,
            "decay_rate": decay_rate,
            "min_score": min_score,
            "teams_decayed": len(decayed_teams),
            "decayed_teams": decayed_teams,
        }

    def get_inactive_teams(self, days: int = 30) -> List[Dict]:
        """
        Get teams that have been inactive for the specified period.

        Args:
            days: Number of days to consider as inactive

        Returns:
            List of inactive team info with last activity details
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT team_id, name, witness_score, last_activity, registered_at
                FROM federated_teams
                WHERE status = 'active'
                  AND (last_activity IS NULL OR last_activity = '' OR last_activity < ?)
                ORDER BY last_activity ASC
            """, (cutoff,)).fetchall()

        inactive = []
        now = datetime.now(timezone.utc)
        for row in rows:
            last_act = row["last_activity"]
            if last_act:
                try:
                    last_dt = datetime.fromisoformat(last_act.rstrip("Z"))
                    if last_dt.tzinfo is None:
                        last_dt = last_dt.replace(tzinfo=timezone.utc)
                    inactive_days = (now - last_dt).days
                except:
                    inactive_days = None
            else:
                # Never active, use registration date
                try:
                    reg_dt = datetime.fromisoformat(row["registered_at"].rstrip("Z"))
                    if reg_dt.tzinfo is None:
                        reg_dt = reg_dt.replace(tzinfo=timezone.utc)
                    inactive_days = (now - reg_dt).days
                except:
                    inactive_days = None

            inactive.append({
                "team_id": row["team_id"],
                "name": row["name"],
                "witness_score": row["witness_score"],
                "last_activity": row["last_activity"] or "never",
                "inactive_days": inactive_days,
            })

        return inactive

    def federation_heartbeat(
        self,
        apply_decay: bool = True,
        decay_threshold_days: int = 30,
        decay_rate: float = 0.1,
        min_score: float = 0.3,
        ledger: "Ledger" = None,
        session_id: str = None,
    ) -> Dict:
        """
        Federation heartbeat - periodic health check and maintenance.

        This method should be called periodically (e.g., weekly) to:
        1. Apply reputation decay to inactive teams
        2. Check federation health metrics
        3. Optionally record to ledger for audit trail

        Args:
            apply_decay: Whether to apply reputation decay (default True)
            decay_threshold_days: Days of inactivity before decay
            decay_rate: Decay rate per heartbeat (default 10%)
            min_score: Minimum reputation score floor
            ledger: Optional Ledger instance for recording heartbeat
            session_id: Session ID for ledger recording

        Returns:
            Dict with heartbeat results and health metrics
        """
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()

        # Track heartbeat sequence in DB
        self._ensure_federation_heartbeat_table()
        self._ensure_xteam_table()  # Ensure xteam tables exist for metrics
        sequence = self._get_next_heartbeat_sequence()

        # Gather health metrics
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Total active teams
            active_count = conn.execute(
                "SELECT COUNT(*) FROM federated_teams WHERE status = 'active'"
            ).fetchone()[0]

            # Average reputation
            avg_rep = conn.execute(
                "SELECT AVG(witness_score) FROM federated_teams WHERE status = 'active'"
            ).fetchone()[0] or 0.0

            # Teams below minimum threshold
            low_rep_count = conn.execute(
                "SELECT COUNT(*) FROM federated_teams WHERE status = 'active' AND witness_score < ?",
                (self.MIN_WITNESS_SCORE,)
            ).fetchone()[0]

            # Pending proposals
            pending_proposals = conn.execute(
                "SELECT COUNT(*) FROM cross_team_proposals WHERE status = 'pending'"
            ).fetchone()[0]

        # Get inactive teams
        inactive_teams = self.get_inactive_teams(decay_threshold_days)

        # Apply decay if enabled
        decay_result = None
        if apply_decay and inactive_teams:
            decay_result = self.apply_reputation_decay(
                decay_threshold_days=decay_threshold_days,
                decay_rate=decay_rate,
                min_score=min_score,
            )

        # Build health assessment
        health_status = "healthy"
        health_issues = []

        if active_count < 3:
            health_status = "degraded"
            health_issues.append(f"Low team count: {active_count}")

        if avg_rep < 0.5:
            health_status = "warning"
            health_issues.append(f"Low average reputation: {avg_rep:.2f}")

        if len(inactive_teams) > active_count * 0.5:
            health_status = "warning"
            health_issues.append(f"High inactivity: {len(inactive_teams)}/{active_count} teams inactive")

        if low_rep_count > active_count * 0.3:
            health_status = "critical"
            health_issues.append(f"Many low-rep teams: {low_rep_count}")

        # Record heartbeat
        heartbeat_entry = {
            "sequence": sequence,
            "timestamp": timestamp,
            "active_teams": active_count,
            "average_reputation": round(avg_rep, 3),
            "inactive_teams": len(inactive_teams),
            "low_rep_teams": low_rep_count,
            "pending_proposals": pending_proposals,
            "decay_applied": decay_result is not None,
            "teams_decayed": len(decay_result["decayed_teams"]) if decay_result else 0,
            "health_status": health_status,
            "health_issues": health_issues,
        }

        self._record_federation_heartbeat(heartbeat_entry)

        # Optionally record to ledger
        if ledger and session_id:
            import hashlib
            entry_hash = hashlib.sha256(
                f"{sequence}:{timestamp}:{health_status}".encode()
            ).hexdigest()[:16]

            ledger.record_heartbeat(
                session_id=session_id,
                sequence=sequence,
                timestamp=timestamp,
                status=health_status,
                delta_seconds=0.0,  # No previous for federation heartbeat
                tool_name="federation_heartbeat",
                action_index=0,
                previous_hash="",
                entry_hash=entry_hash,
            )

        return {
            "heartbeat": heartbeat_entry,
            "decay_result": decay_result,
            "inactive_teams": inactive_teams,
        }

    def _ensure_federation_heartbeat_table(self):
        """Ensure federation heartbeat tracking table exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS federation_heartbeats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sequence INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    active_teams INTEGER,
                    average_reputation REAL,
                    inactive_teams INTEGER,
                    low_rep_teams INTEGER,
                    pending_proposals INTEGER,
                    decay_applied INTEGER,
                    teams_decayed INTEGER,
                    health_status TEXT,
                    health_issues TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fed_heartbeat_seq
                ON federation_heartbeats(sequence DESC)
            """)

    def _get_next_heartbeat_sequence(self) -> int:
        """Get next heartbeat sequence number."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT MAX(sequence) FROM federation_heartbeats"
            ).fetchone()
            return (row[0] or 0) + 1

    def _record_federation_heartbeat(self, entry: Dict):
        """Record a federation heartbeat entry."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO federation_heartbeats
                (sequence, timestamp, active_teams, average_reputation, inactive_teams,
                 low_rep_teams, pending_proposals, decay_applied, teams_decayed,
                 health_status, health_issues)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry["sequence"],
                entry["timestamp"],
                entry["active_teams"],
                entry["average_reputation"],
                entry["inactive_teams"],
                entry["low_rep_teams"],
                entry["pending_proposals"],
                1 if entry["decay_applied"] else 0,
                entry["teams_decayed"],
                entry["health_status"],
                json.dumps(entry["health_issues"]),
            ))

    def get_heartbeat_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent federation heartbeat history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of heartbeat entries, most recent first
        """
        self._ensure_federation_heartbeat_table()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM federation_heartbeats
                ORDER BY sequence DESC
                LIMIT ?
            """, (limit,)).fetchall()

        return [
            {
                "sequence": row["sequence"],
                "timestamp": row["timestamp"],
                "active_teams": row["active_teams"],
                "average_reputation": row["average_reputation"],
                "inactive_teams": row["inactive_teams"],
                "low_rep_teams": row["low_rep_teams"],
                "pending_proposals": row["pending_proposals"],
                "decay_applied": bool(row["decay_applied"]),
                "teams_decayed": row["teams_decayed"],
                "health_status": row["health_status"],
                "health_issues": json.loads(row["health_issues"]) if row["health_issues"] else [],
            }
            for row in rows
        ]

    def check_reciprocity(self, team_a_id: str, team_b_id: str) -> Dict:
        """
        Check witness reciprocity between two teams.

        High reciprocity (teams always witnessing for each other) is a
        collusion signal. Legitimate cross-team witnessing should show
        diverse witness patterns, not tight bidirectional relationships.

        Args:
            team_a_id: First team
            team_b_id: Second team

        Returns:
            Dict with reciprocity analysis
        """
        with sqlite3.connect(self.db_path) as conn:
            # A witnesses for B (within reciprocity window)
            a_for_b = conn.execute(
                "SELECT COUNT(*) FROM ("
                "  SELECT 1 FROM witness_records "
                "  WHERE witness_team_id = ? AND proposal_team_id = ? "
                "  ORDER BY timestamp DESC LIMIT ?"
                ")",
                (team_a_id, team_b_id, self.RECIPROCITY_WINDOW)
            ).fetchone()[0]

            # B witnesses for A
            b_for_a = conn.execute(
                "SELECT COUNT(*) FROM ("
                "  SELECT 1 FROM witness_records "
                "  WHERE witness_team_id = ? AND proposal_team_id = ? "
                "  ORDER BY timestamp DESC LIMIT ?"
                ")",
                (team_b_id, team_a_id, self.RECIPROCITY_WINDOW)
            ).fetchone()[0]

            # Total witnessing for both teams
            a_total = conn.execute(
                "SELECT COUNT(*) FROM ("
                "  SELECT 1 FROM witness_records "
                "  WHERE witness_team_id = ? "
                "  ORDER BY timestamp DESC LIMIT ?"
                ")",
                (team_a_id, self.RECIPROCITY_WINDOW)
            ).fetchone()[0]

            b_total = conn.execute(
                "SELECT COUNT(*) FROM ("
                "  SELECT 1 FROM witness_records "
                "  WHERE witness_team_id = ? "
                "  ORDER BY timestamp DESC LIMIT ?"
                ")",
                (team_b_id, self.RECIPROCITY_WINDOW)
            ).fetchone()[0]

        # Calculate reciprocity ratio
        pair_total = a_for_b + b_for_a
        total_witnessing = a_total + b_total

        if total_witnessing == 0:
            reciprocity_ratio = 0.0
        else:
            reciprocity_ratio = pair_total / total_witnessing

        # Is it suspicious?
        is_suspicious = (
            reciprocity_ratio > self.MAX_RECIPROCITY_RATIO
            and pair_total >= 4  # Need minimum evidence
        )

        return {
            "team_a": team_a_id,
            "team_b": team_b_id,
            "a_witnesses_b": a_for_b,
            "b_witnesses_a": b_for_a,
            "a_total_witnessing": a_total,
            "b_total_witnessing": b_total,
            "reciprocity_ratio": reciprocity_ratio,
            "is_suspicious": is_suspicious,
            "pair_total": pair_total,
        }

    def get_collusion_report(self) -> Dict:
        """
        Analyze the entire witness graph for collusion patterns.

        Returns:
            Report with flagged team pairs and overall health metrics
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get all teams
            teams = conn.execute(
                "SELECT team_id FROM federated_teams WHERE status = 'active'"
            ).fetchall()
            team_ids = [row["team_id"] for row in teams]

        # Check all pairs
        flagged_pairs = []
        pair_count = 0
        for i, a in enumerate(team_ids):
            for b in team_ids[i + 1:]:
                pair_count += 1
                reciprocity = self.check_reciprocity(a, b)
                if reciprocity["is_suspicious"]:
                    flagged_pairs.append(reciprocity)

        # Include lineage analysis
        lineage = self.get_lineage_report()

        # Combine reciprocity and lineage health
        if lineage["health"] == "critical" or len(flagged_pairs) > 2:
            health = "critical"
        elif lineage["health"] == "warning" or len(flagged_pairs) > 0:
            health = "concerning"
        else:
            health = "healthy"

        return {
            "total_teams": len(team_ids),
            "pairs_analyzed": pair_count,
            "flagged_pairs": flagged_pairs,
            "collusion_ratio": len(flagged_pairs) / max(pair_count, 1),
            "lineage": lineage,
            "health": health,
        }

    def find_teams_by_creator(self, creator_lct: str) -> List[FederatedTeam]:
        """
        Find all teams created by a specific LCT.

        Useful for detecting Sybil team creation where one entity
        creates multiple teams to bypass cross-team witnessing.

        Args:
            creator_lct: LCT of the creator to search for

        Returns:
            List of teams created by this LCT
        """
        if not creator_lct:
            return []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM federated_teams WHERE creator_lct = ?",
                (creator_lct,)
            ).fetchall()
            return [self._row_to_team(row) for row in rows]

    def get_lineage_report(self) -> Dict:
        """
        Analyze team creation lineage for suspicious patterns.

        Flags:
        - Single LCT creating multiple teams (team Sybil attack)
        - Teams with the same creator witnessing for each other

        Returns:
            Dict with lineage analysis
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Find creators with multiple teams
            rows = conn.execute("""
                SELECT creator_lct, COUNT(*) as team_count,
                       GROUP_CONCAT(team_id) as team_ids
                FROM federated_teams
                WHERE creator_lct != '' AND status = 'active'
                GROUP BY creator_lct
                HAVING COUNT(*) > 1
            """).fetchall()

        multi_creators = []
        same_creator_witness_pairs = []

        for row in rows:
            creator = row["creator_lct"]
            team_ids = row["team_ids"].split(",")
            team_count = row["team_count"]

            multi_creators.append({
                "creator_lct": creator,
                "team_count": team_count,
                "team_ids": team_ids,
            })

            # Check if same-creator teams are witnessing for each other
            for i in range(len(team_ids)):
                for j in range(i + 1, len(team_ids)):
                    recip = self.check_reciprocity(team_ids[i], team_ids[j])
                    if recip["pair_total"] > 0:
                        same_creator_witness_pairs.append({
                            "creator_lct": creator,
                            "team_a": team_ids[i],
                            "team_b": team_ids[j],
                            "witness_events": recip["pair_total"],
                            "reciprocity_ratio": recip["reciprocity_ratio"],
                        })

        return {
            "multi_team_creators": multi_creators,
            "same_creator_witness_count": len(same_creator_witness_pairs),
            "same_creator_witness_pairs": same_creator_witness_pairs,
            "health": (
                "critical" if same_creator_witness_pairs else
                "warning" if multi_creators else
                "healthy"
            ),
        }

    def analyze_member_overlap(self, team_member_maps: Dict[str, List[str]]) -> Dict:
        """
        Analyze member overlap across teams to detect shared LCTs.

        Same LCT appearing in multiple teams can be legitimate (cross-team
        contributor) or suspicious (Sybil operating across team boundaries).

        The analysis distinguishes:
        - **Low overlap** (1-2 shared members): Normal cross-team work
        - **High overlap** (>30% of smaller team): Suspicious coordination
        - **Full overlap**: Likely duplicate or shell teams

        Args:
            team_member_maps: Dict of {team_id: [list of member LCTs]}

        Returns:
            Dict with overlap analysis including shared members, overlap
            ratios, and risk assessment per team pair.
        """
        team_ids = list(team_member_maps.keys())
        member_sets = {tid: set(members) for tid, members in team_member_maps.items()}

        # Track which LCTs appear in multiple teams
        lct_to_teams: Dict[str, List[str]] = defaultdict(list)
        for tid, members in team_member_maps.items():
            for lct in members:
                lct_to_teams[lct].append(tid)

        multi_team_lcts = {
            lct: teams for lct, teams in lct_to_teams.items()
            if len(teams) > 1
        }

        # Pairwise overlap analysis
        pair_analysis = []
        for i, tid_a in enumerate(team_ids):
            for tid_b in team_ids[i + 1:]:
                shared = member_sets[tid_a] & member_sets[tid_b]
                if not shared:
                    continue

                smaller_size = min(len(member_sets[tid_a]), len(member_sets[tid_b]))
                overlap_ratio = len(shared) / max(smaller_size, 1)

                if overlap_ratio >= 0.8:
                    risk = "critical"
                elif overlap_ratio >= 0.3:
                    risk = "high"
                elif len(shared) >= 3:
                    risk = "moderate"
                else:
                    risk = "low"

                pair_analysis.append({
                    "team_a": tid_a,
                    "team_b": tid_b,
                    "shared_members": sorted(shared),
                    "shared_count": len(shared),
                    "team_a_size": len(member_sets[tid_a]),
                    "team_b_size": len(member_sets[tid_b]),
                    "overlap_ratio": round(overlap_ratio, 3),
                    "risk": risk,
                })

        # Overall assessment
        critical_pairs = [p for p in pair_analysis if p["risk"] == "critical"]
        high_pairs = [p for p in pair_analysis if p["risk"] == "high"]

        if critical_pairs:
            health = "critical"
        elif high_pairs:
            health = "warning"
        elif pair_analysis:
            health = "info"
        else:
            health = "healthy"

        return {
            "teams_analyzed": len(team_ids),
            "multi_team_members": {
                lct: teams for lct, teams in sorted(multi_team_lcts.items())
            },
            "multi_team_count": len(multi_team_lcts),
            "pair_analysis": pair_analysis,
            "health": health,
        }

    def sign_pattern(self, pattern_type: str, pattern_data: Dict,
                     signer_lct: str = "") -> Dict:
        """
        Create a cryptographic signature for a federation pattern.

        Pattern signing creates a tamper-evident seal on federation analysis
        results (collusion reports, lineage reports, overlap analysis).
        The signature can be verified to confirm the data hasn't been
        modified since it was generated.

        Uses HMAC-SHA256 with the pattern content as the message.
        The signing key is derived from the signer LCT and the federation
        DB path (acting as a domain separator).

        Args:
            pattern_type: Type of pattern (collusion_report, lineage_report,
                         overlap_analysis, witness_event)
            pattern_data: The data to sign (dict)
            signer_lct: LCT of the entity creating the signature

        Returns:
            Dict with original data, signature, and verification metadata
        """
        import hmac

        timestamp = datetime.now(timezone.utc).isoformat()

        # Canonical representation for signing
        canonical = json.dumps({
            "type": pattern_type,
            "data": pattern_data,
            "signer": signer_lct,
            "timestamp": timestamp,
        }, sort_keys=True, separators=(',', ':'))

        # Derive signing key from signer identity + DB path (domain separator)
        key_material = f"{signer_lct}:{self.db_path}".encode()
        signing_key = hashlib.sha256(key_material).digest()

        # HMAC-SHA256 signature
        signature = hmac.new(signing_key, canonical.encode(), hashlib.sha256).hexdigest()

        return {
            "pattern_type": pattern_type,
            "data": pattern_data,
            "signer_lct": signer_lct,
            "signed_at": timestamp,
            "signature": signature,
            "algorithm": "hmac-sha256",
        }

    def verify_pattern_signature(self, signed_pattern: Dict) -> bool:
        """
        Verify a signed federation pattern.

        Args:
            signed_pattern: The signed pattern dict (from sign_pattern())

        Returns:
            True if signature is valid, False if tampered
        """
        import hmac

        canonical = json.dumps({
            "type": signed_pattern["pattern_type"],
            "data": signed_pattern["data"],
            "signer": signed_pattern["signer_lct"],
            "timestamp": signed_pattern["signed_at"],
        }, sort_keys=True, separators=(',', ':'))

        key_material = f"{signed_pattern['signer_lct']}:{self.db_path}".encode()
        signing_key = hashlib.sha256(key_material).digest()

        expected = hmac.new(signing_key, canonical.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signed_pattern["signature"])

    def get_federation_health(self, team_member_maps: Dict[str, List[str]] = None,
                              teams_data: Dict[str, Dict] = None) -> Dict:
        """
        Aggregate federation health dashboard combining all sub-reports.

        Produces a single health assessment from:
        - Collusion report (witness reciprocity)
        - Lineage report (team creation patterns)
        - Member overlap analysis (shared LCTs)
        - Per-team Sybil analysis (if trust data provided)
        - Pattern signing verification

        Args:
            team_member_maps: Optional {team_id: [member LCTs]} for overlap analysis
            teams_data: Optional {team_id: {member_id: trust_dict}} for Sybil analysis

        Returns:
            Comprehensive health report with per-subsystem status and overall score
        """
        from .sybil_detection import FederatedSybilDetector

        subsystems = {}
        issues = []
        score = 100  # Start at 100, deduct for problems

        # 1. Collusion report
        collusion = self.get_collusion_report()
        subsystems["collusion"] = {
            "health": collusion["health"],
            "flagged_pairs": len(collusion.get("flagged_pairs", [])),
            "total_teams": collusion["total_teams"],
        }
        if collusion["health"] == "critical":
            score -= 30
            issues.append("Critical collusion detected between teams")
        elif collusion["health"] == "concerning":
            score -= 15
            issues.append(f"{len(collusion['flagged_pairs'])} suspicious team pairs")

        # 2. Lineage report
        lineage = self.get_lineage_report()
        subsystems["lineage"] = {
            "health": lineage["health"],
            "multi_team_creators": len(lineage.get("multi_team_creators", [])),
            "cross_witness_pairs": len(lineage.get("same_creator_witness_pairs", [])),
        }
        if lineage["health"] == "critical":
            score -= 25
            issues.append("Same-creator teams witnessing for each other")
        elif lineage["health"] == "warning":
            score -= 10
            issues.append(f"{len(lineage['multi_team_creators'])} entities with multiple teams")

        # 3. Member overlap (if data provided)
        if team_member_maps:
            overlap = self.analyze_member_overlap(team_member_maps)
            subsystems["member_overlap"] = {
                "health": overlap["health"],
                "multi_team_count": overlap["multi_team_count"],
                "critical_pairs": sum(
                    1 for p in overlap.get("pair_analysis", [])
                    if p["risk"] == "critical"
                ),
            }
            if overlap["health"] == "critical":
                score -= 20
                issues.append("Fully overlapping teams detected (shell teams)")
            elif overlap["health"] == "warning":
                score -= 10
                issues.append("High member overlap between teams")
        else:
            subsystems["member_overlap"] = {"health": "not_analyzed", "reason": "no data"}

        # 4. Cross-team Sybil detection (if trust data provided)
        if teams_data:
            detector = FederatedSybilDetector(federation=self)
            sybil_report = detector.analyze_federation(teams_data)
            subsystems["sybil"] = {
                "health": sybil_report.overall_risk.value,
                "cross_team_clusters": len(sybil_report.cross_team_clusters),
                "teams_analyzed": sybil_report.teams_analyzed,
            }
            if sybil_report.overall_risk.value == "critical":
                score -= 25
                issues.append(
                    f"{len(sybil_report.cross_team_clusters)} cross-team Sybil clusters")
            elif sybil_report.overall_risk.value in ("high", "elevated"):
                score -= 10
                issues.append("Elevated cross-team Sybil risk")
        else:
            subsystems["sybil"] = {"health": "not_analyzed", "reason": "no data"}

        # 5. Federation size stats
        all_teams = self.find_teams()
        active = [t for t in all_teams if t.status == FederationStatus.ACTIVE]
        suspended = [t for t in all_teams if t.status == FederationStatus.SUSPENDED]
        subsystems["federation_size"] = {
            "total_teams": len(all_teams),
            "active_teams": len(active),
            "suspended_teams": len(suspended),
        }
        if len(suspended) > len(active):
            score -= 15
            issues.append("More suspended than active teams")

        # Overall assessment
        score = max(0, score)
        if score >= 80:
            overall = "healthy"
        elif score >= 60:
            overall = "warning"
        elif score >= 40:
            overall = "degraded"
        else:
            overall = "critical"

        report = {
            "overall_health": overall,
            "health_score": score,
            "subsystems": subsystems,
            "issues": issues,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Auto-sign the dashboard
        signed = self.sign_pattern("federation_health", report, signer_lct="federation:system")
        report["signature"] = signed["signature"]

        return report

    def suspend_team(self, team_id: str, reason: str = "") -> bool:
        """Suspend a team from the federation (e.g., for collusion)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE federated_teams SET status = ? WHERE team_id = ?",
                (FederationStatus.SUSPENDED.value, team_id)
            )
        return True

    def get_severity_policy(self, severity: str) -> Dict:
        """
        Get the governance policy for a given severity level.

        Args:
            severity: One of "low", "medium", "high", "critical"

        Returns:
            Policy dict with approval_threshold, require_outsider, etc.
        """
        severity = severity.lower()
        if severity not in self.DEFAULT_SEVERITY_POLICIES:
            raise ValueError(f"Invalid severity level: {severity}. "
                           f"Valid: {list(self.DEFAULT_SEVERITY_POLICIES.keys())}")
        return dict(self.DEFAULT_SEVERITY_POLICIES[severity])

    def classify_action_severity(self, action_type: str, parameters: Dict = None) -> str:
        """
        Automatically classify action severity based on type and parameters.

        This provides default classification. Federation-specific rules can override.

        Args:
            action_type: Type of cross-team action
            parameters: Optional action parameters

        Returns:
            Severity level: "low", "medium", "high", or "critical"
        """
        parameters = parameters or {}

        # Critical actions: irreversible, high-impact
        critical_actions = {
            "team_dissolution", "federation_exit", "admin_transfer",
            "key_rotation", "emergency_override", "policy_override",
        }
        if action_type in critical_actions:
            return self.SEVERITY_CRITICAL

        # High-impact actions: significant changes
        high_actions = {
            "resource_transfer", "role_change", "access_grant",
            "member_removal", "permission_escalation", "config_change",
        }
        if action_type in high_actions:
            return self.SEVERITY_HIGH

        # Check parameters for severity hints
        amount = parameters.get("amount", 0)
        if isinstance(amount, (int, float)):
            if amount > 1000:
                return self.SEVERITY_HIGH
            if amount > 100:
                return self.SEVERITY_MEDIUM

        # Medium: standard operations
        medium_actions = {
            "proposal_submit", "resource_allocation", "schedule_change",
            "notification", "status_update",
        }
        if action_type in medium_actions:
            return self.SEVERITY_MEDIUM

        # Default to low for unknown actions
        return self.SEVERITY_LOW

    def _row_to_team(self, row) -> FederatedTeam:
        """Convert database row to FederatedTeam."""
        # Handle creator_lct which may not exist in old schemas
        try:
            creator_lct = row["creator_lct"] or ""
        except (IndexError, KeyError):
            creator_lct = ""

        return FederatedTeam(
            team_id=row["team_id"],
            name=row["name"],
            registered_at=row["registered_at"],
            status=FederationStatus(row["status"]),
            domains=json.loads(row["domains"]) if row["domains"] else [],
            capabilities=json.loads(row["capabilities"]) if row["capabilities"] else [],
            admin_lct=row["admin_lct"] or "",
            creator_lct=creator_lct,
            member_count=row["member_count"] or 0,
            last_activity=row["last_activity"] if "last_activity" in row.keys() and row["last_activity"] else "",
            witness_score=row["witness_score"] if row["witness_score"] is not None else 1.0,
            witness_count=row["witness_count"] or 0,
            witness_successes=row["witness_successes"] or 0,
            witness_failures=row["witness_failures"] or 0,
        )


    # -----------------------------------------------------------------------
    # Cross-Team R6 Proposals
    # -----------------------------------------------------------------------

    def create_cross_team_proposal(
        self,
        proposing_team_id: str,
        proposer_lct: str,
        action_type: str,
        description: str,
        target_team_ids: List[str],
        required_approvals: int = None,
        parameters: Dict = None,
        require_outsider: bool = None,  # Now can be auto-set by severity
        outsider_team_ids: List[str] = None,
        voting_mode: str = None,  # Now can be auto-set by severity
        approval_threshold: float = None,  # Now can be auto-set by severity
        severity: str = None,  # NEW: auto-classify or explicit
    ) -> Dict:
        """
        Create a proposal that requires approval from multiple federation teams.

        This enables federation-level governance where actions affecting multiple
        teams require coordination. Examples:
        - Shared resource allocation
        - Cross-team access grants
        - Federation policy changes

        Severity-based adaptive thresholds:
        - If severity is provided, policy defaults are applied automatically
        - Explicit parameters override policy defaults
        - Without severity, falls back to legacy defaults

        Voting modes:
        - "veto": Single rejection blocks proposal (strong minority protection)
        - "weighted": Reputation-weighted voting, passes if weighted approval >= threshold

        Args:
            proposing_team_id: Team initiating the proposal
            proposer_lct: LCT of the proposing entity
            action_type: Type of cross-team action
            description: Human-readable description
            target_team_ids: Teams that must approve
            required_approvals: Number of target team approvals needed (default: all)
            parameters: Action-specific parameters
            require_outsider: If True, at least one approval must come from a team
                             not in the proposing group (anti-collusion measure)
            outsider_team_ids: Optional list of eligible outsider teams.
                               If None, any team not in target_team_ids qualifies.
            voting_mode: "veto" or "weighted" (or None for severity-based)
            approval_threshold: For weighted mode, required weighted approval ratio (0.0-1.0)
            severity: "low", "medium", "high", "critical" (or None for auto-classify)

        Returns:
            Cross-team proposal record
        """
        # Track severity override for audit
        auto_classified_severity = self.classify_action_severity(action_type, parameters)
        severity_was_overridden = False

        if severity is None:
            severity = auto_classified_severity
        elif severity != auto_classified_severity:
            severity_was_overridden = True

        # Get policy for this severity level
        policy = self.get_severity_policy(severity)

        # Track parameter overrides for audit
        policy_overrides = []
        if voting_mode is not None and voting_mode != policy["voting_mode"]:
            policy_overrides.append(f"voting_mode: {policy['voting_mode']} -> {voting_mode}")
        if approval_threshold is not None and approval_threshold != policy["approval_threshold"]:
            policy_overrides.append(f"threshold: {policy['approval_threshold']} -> {approval_threshold}")
        if require_outsider is not None and require_outsider != policy["require_outsider"]:
            policy_overrides.append(f"outsider: {policy['require_outsider']} -> {require_outsider}")

        # Apply policy defaults (explicit parameters override)
        if voting_mode is None:
            voting_mode = policy["voting_mode"]
        if approval_threshold is None:
            approval_threshold = policy["approval_threshold"]
        if require_outsider is None:
            require_outsider = policy["require_outsider"]

        # Validate voting mode
        if voting_mode not in ("veto", "weighted"):
            raise ValueError(f"Invalid voting_mode: {voting_mode}")
        if voting_mode == "weighted" and not (0.0 < approval_threshold <= 1.0):
            raise ValueError(f"approval_threshold must be between 0 and 1")

        # Validate proposing team
        proposing_team = self.get_team(proposing_team_id)
        if not proposing_team or proposing_team.status != FederationStatus.ACTIVE:
            raise ValueError(f"Proposing team not active: {proposing_team_id}")

        # Validate target teams
        for tid in target_team_ids:
            target = self.get_team(tid)
            if not target or target.status != FederationStatus.ACTIVE:
                raise ValueError(f"Target team not active: {tid}")

        # Generate proposal ID
        now = datetime.now(timezone.utc)
        seed = f"xteam:{proposing_team_id}:{action_type}:{now.isoformat()}"
        proposal_id = f"xteam:{hashlib.sha256(seed.encode()).hexdigest()[:12]}"

        required = required_approvals or len(target_team_ids)
        if required > len(target_team_ids):
            raise ValueError(f"Required approvals ({required}) > target teams ({len(target_team_ids)})")

        proposal = {
            "proposal_id": proposal_id,
            "proposing_team_id": proposing_team_id,
            "proposer_lct": proposer_lct,
            "action_type": action_type,
            "description": description,
            "target_team_ids": target_team_ids,
            "required_approvals": required,
            "parameters": parameters or {},
            "status": "pending",
            "approvals": {},  # team_id -> {"approver_lct": ..., "timestamp": ...}
            "rejections": {},
            "created_at": now.isoformat(),
            "closed_at": "",
            "outcome": "",
            # Outsider requirement for anti-collusion
            "require_outsider": require_outsider,
            "outsider_team_ids": outsider_team_ids or [],
            "has_outsider_approval": False,
            # Voting mode configuration
            "voting_mode": voting_mode,
            "approval_threshold": approval_threshold,
            # Severity and policy tracking
            "severity": severity,
            "applied_policy": policy,
        }

        # Persist to database
        self._ensure_xteam_table()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO cross_team_proposals
                (proposal_id, data, status, created_at)
                VALUES (?, ?, ?, ?)
            """, (proposal_id, json.dumps(proposal), "pending", now.isoformat()))

        # Update activity timestamp for the proposing team
        self._update_last_activity(proposing_team_id, now.isoformat())

        # Audit log for severity/policy overrides
        if severity_was_overridden or policy_overrides:
            audit_details = {
                "auto_classified_severity": auto_classified_severity,
                "explicit_severity": severity if severity_was_overridden else None,
                "severity_override": severity_was_overridden,
                "policy_overrides": policy_overrides,
                "action_type": action_type,
            }
            # Determine risk level based on override direction
            if severity_was_overridden:
                severity_levels = ["low", "medium", "high", "critical"]
                auto_idx = severity_levels.index(auto_classified_severity)
                explicit_idx = severity_levels.index(severity)
                if explicit_idx < auto_idx:
                    # Downgrade: potential security risk
                    risk_level = "warning"
                else:
                    # Upgrade: conservative, low risk
                    risk_level = "info"
            else:
                risk_level = "info"

            self._log_governance_audit(
                audit_type="severity_override" if severity_was_overridden else "policy_override",
                proposal_id=proposal_id,
                team_id=proposing_team_id,
                actor_lct=proposer_lct,
                action_type=action_type,
                details=audit_details,
                risk_level=risk_level,
            )

        return proposal

    def _ensure_xteam_table(self):
        """Create cross_team_proposals and approval_records tables if not exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cross_team_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            # Track approval events for reciprocity analysis
            conn.execute("""
                CREATE TABLE IF NOT EXISTS xteam_approval_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposing_team_id TEXT NOT NULL,
                    approving_team_id TEXT NOT NULL,
                    proposal_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    outcome TEXT DEFAULT 'pending'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_xteam_approvals_teams
                ON xteam_approval_records(proposing_team_id, approving_team_id)
            """)
            # Governance audit log for policy overrides and anomalies
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    audit_type TEXT NOT NULL,
                    proposal_id TEXT,
                    team_id TEXT,
                    actor_lct TEXT,
                    action_type TEXT,
                    details TEXT NOT NULL,
                    risk_level TEXT DEFAULT 'info'
                )
            """)

    def approve_cross_team_proposal(
        self,
        proposal_id: str,
        approving_team_id: str,
        approver_lct: str,
    ) -> Dict:
        """
        Approve a cross-team proposal on behalf of a target team.

        The approver must be the admin of the approving team (or have delegation).

        Returns:
            Updated proposal, with status changed to "approved" if threshold met
        """
        proposal = self._load_xteam_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")

        if proposal["status"] != "pending":
            raise ValueError(f"Proposal not pending: {proposal['status']}")

        if approving_team_id not in proposal["target_team_ids"]:
            raise ValueError(f"Team {approving_team_id} not a target of this proposal")

        if approving_team_id in proposal["approvals"]:
            raise ValueError(f"Team {approving_team_id} already approved")

        # Record approval
        now = datetime.now(timezone.utc).isoformat()
        proposal["approvals"][approving_team_id] = {
            "approver_lct": approver_lct,
            "timestamp": now,
        }

        # Update activity timestamp for the approving team
        self._update_last_activity(approving_team_id, now)

        # Record for reciprocity analysis
        self._record_xteam_approval(
            proposing_team_id=proposal["proposing_team_id"],
            approving_team_id=approving_team_id,
            proposal_id=proposal_id,
            timestamp=now,
        )

        # Check if this is an outsider approval
        if proposal.get("require_outsider"):
            outsider_ids = proposal.get("outsider_team_ids", [])
            if outsider_ids:
                # Specific outsider list provided
                if approving_team_id in outsider_ids:
                    proposal["has_outsider_approval"] = True
            else:
                # Any team not in target list is an outsider
                if approving_team_id not in proposal["target_team_ids"]:
                    proposal["has_outsider_approval"] = True

        # Check if threshold met (depends on voting mode)
        voting_mode = proposal.get("voting_mode", "veto")
        outsider_met = (not proposal.get("require_outsider") or
                       proposal.get("has_outsider_approval", False))

        if voting_mode == "weighted":
            # Calculate weighted approval ratio
            weighted_result = self._calculate_weighted_votes(proposal)
            proposal["weighted_approval"] = weighted_result["weighted_approval"]
            proposal["weighted_rejection"] = weighted_result["weighted_rejection"]
            threshold = proposal.get("approval_threshold", 0.5)
            approvals_met = weighted_result["weighted_approval"] >= threshold
        else:
            # Veto mode: need required_approvals count
            approvals_met = len(proposal["approvals"]) >= proposal["required_approvals"]

        if approvals_met and outsider_met:
            proposal["status"] = "approved"
            proposal["closed_at"] = datetime.now(timezone.utc).isoformat()
            proposal["outcome"] = "approved"

        self._save_xteam_proposal(proposal)
        return proposal

    def _calculate_weighted_votes(self, proposal: Dict) -> Dict:
        """
        Calculate reputation-weighted voting totals.

        Each team's vote is weighted by their witness_score (reputation).
        """
        target_teams = proposal["target_team_ids"]
        approvals = proposal.get("approvals", {})
        rejections = proposal.get("rejections", {})

        total_weight = 0.0
        approval_weight = 0.0
        rejection_weight = 0.0

        for team_id in target_teams:
            team = self.get_team(team_id)
            weight = team.witness_score if team else 1.0
            total_weight += weight

            if team_id in approvals:
                approval_weight += weight
            if team_id in rejections:
                rejection_weight += weight

        return {
            "total_weight": total_weight,
            "approval_weight": approval_weight,
            "rejection_weight": rejection_weight,
            "weighted_approval": approval_weight / total_weight if total_weight > 0 else 0.0,
            "weighted_rejection": rejection_weight / total_weight if total_weight > 0 else 0.0,
        }

    def reject_cross_team_proposal(
        self,
        proposal_id: str,
        rejecting_team_id: str,
        rejector_lct: str,
        reason: str = "",
    ) -> Dict:
        """
        Reject a cross-team proposal on behalf of a target team.

        In veto mode: single rejection blocks proposal.
        In weighted mode: rejection is counted as negative vote weight.
        """
        proposal = self._load_xteam_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")

        if proposal["status"] != "pending":
            raise ValueError(f"Proposal not pending: {proposal['status']}")

        if rejecting_team_id not in proposal["target_team_ids"]:
            raise ValueError(f"Team {rejecting_team_id} not a target of this proposal")

        # Record rejection
        proposal["rejections"][rejecting_team_id] = {
            "rejector_lct": rejector_lct,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        voting_mode = proposal.get("voting_mode", "veto")

        if voting_mode == "veto":
            # Veto mode: single rejection blocks proposal
            proposal["status"] = "rejected"
            proposal["closed_at"] = datetime.now(timezone.utc).isoformat()
            proposal["outcome"] = "rejected"
        else:
            # Weighted mode: check if rejection weight is enough to block
            weighted_result = self._calculate_weighted_votes(proposal)
            proposal["weighted_approval"] = weighted_result["weighted_approval"]
            proposal["weighted_rejection"] = weighted_result["weighted_rejection"]

            # Rejected if rejection weight exceeds (1 - threshold)
            threshold = proposal.get("approval_threshold", 0.5)
            if weighted_result["weighted_rejection"] > (1 - threshold):
                proposal["status"] = "rejected"
                proposal["closed_at"] = datetime.now(timezone.utc).isoformat()
                proposal["outcome"] = "rejected"

        self._save_xteam_proposal(proposal)
        return proposal

    def approve_as_outsider(
        self,
        proposal_id: str,
        outsider_team_id: str,
        approver_lct: str,
    ) -> Dict:
        """
        Approve a cross-team proposal as an outsider (neutral third party).

        Only valid for proposals with require_outsider=True.
        The outsider team must be in outsider_team_ids (if specified) or
        must not be in target_team_ids.

        Args:
            proposal_id: The proposal to approve
            outsider_team_id: The outsider team providing validation
            approver_lct: LCT of the approving entity

        Returns:
            Updated proposal
        """
        proposal = self._load_xteam_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")

        if proposal["status"] != "pending":
            raise ValueError(f"Proposal not pending: {proposal['status']}")

        if not proposal.get("require_outsider"):
            raise ValueError("This proposal does not require outsider approval")

        # Validate outsider eligibility
        outsider_ids = proposal.get("outsider_team_ids", [])
        if outsider_ids:
            if outsider_team_id not in outsider_ids:
                raise ValueError(f"Team {outsider_team_id} not an eligible outsider")
        else:
            # Must not be in target list
            if outsider_team_id in proposal["target_team_ids"]:
                raise ValueError(f"Team {outsider_team_id} is a target, not an outsider")
            if outsider_team_id == proposal["proposing_team_id"]:
                raise ValueError("Proposing team cannot be an outsider")

        if proposal.get("has_outsider_approval"):
            raise ValueError("Proposal already has outsider approval")

        # Record outsider approval
        now = datetime.now(timezone.utc).isoformat()
        proposal["outsider_approval"] = {
            "team_id": outsider_team_id,
            "approver_lct": approver_lct,
            "timestamp": now,
        }
        proposal["has_outsider_approval"] = True

        # Check if now fully approved
        approvals_met = len(proposal["approvals"]) >= proposal["required_approvals"]
        if approvals_met:
            proposal["status"] = "approved"
            proposal["closed_at"] = now
            proposal["outcome"] = "approved"

        self._save_xteam_proposal(proposal)
        return proposal

    def get_cross_team_proposal(self, proposal_id: str) -> Optional[Dict]:
        """Get a cross-team proposal by ID."""
        return self._load_xteam_proposal(proposal_id)

    def get_pending_cross_team_proposals(self, team_id: str) -> List[Dict]:
        """Get all pending cross-team proposals where team_id is a target."""
        self._ensure_xteam_table()
        proposals = []
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT data FROM cross_team_proposals WHERE status = 'pending'"
            ).fetchall()
            for row in rows:
                proposal = json.loads(row[0])
                if team_id in proposal["target_team_ids"]:
                    proposals.append(proposal)
        return proposals

    def _load_xteam_proposal(self, proposal_id: str) -> Optional[Dict]:
        """Load a cross-team proposal from database."""
        self._ensure_xteam_table()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT data FROM cross_team_proposals WHERE proposal_id = ?",
                (proposal_id,)
            ).fetchone()
            return json.loads(row[0]) if row else None

    def _save_xteam_proposal(self, proposal: Dict):
        """Save a cross-team proposal to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE cross_team_proposals SET data = ?, status = ? WHERE proposal_id = ?",
                (json.dumps(proposal), proposal["status"], proposal["proposal_id"])
            )

    def _record_xteam_approval(self, proposing_team_id: str, approving_team_id: str,
                                proposal_id: str, timestamp: str):
        """Record a cross-team approval event for reciprocity analysis."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO xteam_approval_records
                (proposing_team_id, approving_team_id, proposal_id, timestamp)
                VALUES (?, ?, ?, ?)
            """, (proposing_team_id, approving_team_id, proposal_id, timestamp))

    def check_approval_reciprocity(self, team_a: str, team_b: str) -> Dict:
        """
        Check if two teams have suspicious mutual approval patterns.

        Returns analysis of how often A approves B's proposals and vice versa.
        High reciprocity (>0.8) is suspicious - indicates potential collusion.
        """
        self._ensure_xteam_table()
        with sqlite3.connect(self.db_path) as conn:
            # Count A approving B's proposals
            a_approves_b = conn.execute("""
                SELECT COUNT(*) FROM xteam_approval_records
                WHERE proposing_team_id = ? AND approving_team_id = ?
            """, (team_b, team_a)).fetchone()[0]

            # Count B approving A's proposals
            b_approves_a = conn.execute("""
                SELECT COUNT(*) FROM xteam_approval_records
                WHERE proposing_team_id = ? AND approving_team_id = ?
            """, (team_a, team_b)).fetchone()[0]

            # Total approvals by each team
            a_total = conn.execute("""
                SELECT COUNT(*) FROM xteam_approval_records
                WHERE approving_team_id = ?
            """, (team_a,)).fetchone()[0]

            b_total = conn.execute("""
                SELECT COUNT(*) FROM xteam_approval_records
                WHERE approving_team_id = ?
            """, (team_b,)).fetchone()[0]

        # Calculate reciprocity metrics
        pair_total = a_approves_b + b_approves_a
        if pair_total == 0:
            reciprocity_ratio = 0.0
        else:
            # How balanced is the mutual approval?
            min_val = min(a_approves_b, b_approves_a)
            max_val = max(a_approves_b, b_approves_a)
            reciprocity_ratio = min_val / max_val if max_val > 0 else 0.0

        # Concentration: what % of A's approvals go to B?
        a_concentration = a_approves_b / a_total if a_total > 0 else 0.0
        b_concentration = b_approves_a / b_total if b_total > 0 else 0.0

        # Suspicious if:
        # 1. High reciprocity (balanced mutual approval)
        # 2. High concentration (most approvals to each other)
        # 3. Significant volume (not just 1-2 approvals)
        is_suspicious = (
            reciprocity_ratio > 0.7 and
            pair_total >= 4 and
            (a_concentration > 0.5 or b_concentration > 0.5)
        )

        return {
            "team_a": team_a,
            "team_b": team_b,
            "a_approves_b": a_approves_b,
            "b_approves_a": b_approves_a,
            "a_total_approvals": a_total,
            "b_total_approvals": b_total,
            "pair_total": pair_total,
            "reciprocity_ratio": reciprocity_ratio,
            "a_concentration": a_concentration,
            "b_concentration": b_concentration,
            "is_suspicious": is_suspicious,
        }

    def get_approval_reciprocity_report(self) -> Dict:
        """
        Analyze the entire approval graph for collusion patterns.

        Returns report with flagged team pairs and overall health metrics.
        """
        self._ensure_xteam_table()
        with sqlite3.connect(self.db_path) as conn:
            # Get all teams that have participated in cross-team approvals
            rows = conn.execute("""
                SELECT DISTINCT proposing_team_id FROM xteam_approval_records
                UNION
                SELECT DISTINCT approving_team_id FROM xteam_approval_records
            """).fetchall()
            participating_teams = [row[0] for row in rows]

        if len(participating_teams) < 2:
            return {
                "total_teams": len(participating_teams),
                "pairs_analyzed": 0,
                "flagged_pairs": [],
                "health": "healthy",
            }

        # Check all pairs
        flagged_pairs = []
        pair_count = 0
        for i, a in enumerate(participating_teams):
            for b in participating_teams[i + 1:]:
                pair_count += 1
                reciprocity = self.check_approval_reciprocity(a, b)
                if reciprocity["is_suspicious"]:
                    flagged_pairs.append(reciprocity)

        # Determine health
        if len(flagged_pairs) > 2:
            health = "critical"
        elif len(flagged_pairs) > 0:
            health = "warning"
        else:
            health = "healthy"

        return {
            "total_teams": len(participating_teams),
            "pairs_analyzed": pair_count,
            "flagged_pairs": flagged_pairs,
            "collusion_ratio": len(flagged_pairs) / max(pair_count, 1),
            "health": health,
        }

    def detect_approval_cycles(self, min_cycle_length: int = 3, min_approvals: int = 2) -> Dict:
        """
        Detect cyclic approval patterns that evade pairwise reciprocity detection.

        Chain-pattern collusion: A approves B's proposals, B approves C's, C approves A's.
        This forms a cycle that benefits all participants but each pairwise check
        shows one-directional approval (not suspicious in isolation).

        Args:
            min_cycle_length: Minimum cycle size to flag (default 3 = A->B->C->A)
            min_approvals: Minimum approvals per edge to consider it significant

        Returns:
            Report with detected cycles and risk assessment
        """
        self._ensure_xteam_table()

        # Build directed approval graph: edge (A, B) exists if A approves B's proposals
        # Note: Edge direction is approver -> proposer (who benefits)
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT approving_team_id, proposing_team_id, COUNT(*) as count
                FROM xteam_approval_records
                GROUP BY approving_team_id, proposing_team_id
                HAVING count >= ?
            """, (min_approvals,)).fetchall()

        # Build adjacency list
        graph: Dict[str, Set[str]] = defaultdict(set)
        edge_counts: Dict[Tuple[str, str], int] = {}
        nodes: Set[str] = set()

        for approver, proposer, count in rows:
            graph[approver].add(proposer)
            edge_counts[(approver, proposer)] = count
            nodes.add(approver)
            nodes.add(proposer)

        # Find all cycles using DFS
        def find_cycles_from(start: str) -> List[List[str]]:
            """Find all cycles starting from a given node."""
            cycles = []
            stack = [(start, [start], set([start]))]

            while stack:
                node, path, visited = stack.pop()

                for neighbor in graph.get(node, []):
                    if neighbor == start and len(path) >= min_cycle_length:
                        # Found a cycle back to start
                        cycles.append(path + [start])
                    elif neighbor not in visited:
                        stack.append((neighbor, path + [neighbor], visited | {neighbor}))

            return cycles

        # Find cycles from each node, deduplicate
        all_cycles = []
        seen_cycle_sets = set()

        for node in nodes:
            cycles = find_cycles_from(node)
            for cycle in cycles:
                # Normalize cycle to avoid duplicates (same cycle, different start)
                # Use frozenset of edges
                edges = frozenset(
                    (cycle[i], cycle[i + 1]) for i in range(len(cycle) - 1)
                )
                if edges not in seen_cycle_sets:
                    seen_cycle_sets.add(edges)
                    all_cycles.append(cycle)

        # Analyze each cycle
        flagged_cycles = []
        for cycle in all_cycles:
            # Calculate total approvals in cycle
            total_approvals = sum(
                edge_counts.get((cycle[i], cycle[i + 1]), 0)
                for i in range(len(cycle) - 1)
            )
            avg_per_edge = total_approvals / (len(cycle) - 1)

            # Check if balanced (similar approval counts across edges)
            edge_weights = [
                edge_counts.get((cycle[i], cycle[i + 1]), 0)
                for i in range(len(cycle) - 1)
            ]
            min_weight = min(edge_weights)
            max_weight = max(edge_weights)
            balance_ratio = min_weight / max_weight if max_weight > 0 else 0.0

            # Suspicious if balanced and significant volume
            is_suspicious = balance_ratio > 0.5 and avg_per_edge >= min_approvals

            flagged_cycles.append({
                "cycle": cycle,
                "length": len(cycle) - 1,  # Number of edges
                "total_approvals": total_approvals,
                "avg_per_edge": avg_per_edge,
                "balance_ratio": balance_ratio,
                "is_suspicious": is_suspicious,
                "edge_weights": edge_weights,
            })

        # Sort by suspiciousness
        flagged_cycles.sort(key=lambda c: (c["is_suspicious"], c["total_approvals"]), reverse=True)

        # Determine health
        suspicious_count = sum(1 for c in flagged_cycles if c["is_suspicious"])
        if suspicious_count > 2:
            health = "critical"
        elif suspicious_count > 0:
            health = "warning"
        else:
            health = "healthy"

        return {
            "total_cycles": len(all_cycles),
            "suspicious_cycles": suspicious_count,
            "cycles": flagged_cycles,
            "graph_nodes": len(nodes),
            "graph_edges": len(edge_counts),
            "health": health,
        }

    def analyze_approval_timing(self, proposal_id: str) -> Dict:
        """
        Analyze how quickly a proposal was approved.

        Fast approval (within minutes of creation) suggests pre-arranged collusion.
        Normal workflow should take hours/days for teams to review.

        Returns:
            Analysis with timing metrics and suspicion flags
        """
        proposal = self._load_xteam_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal not found: {proposal_id}")

        created_at = datetime.fromisoformat(proposal["created_at"].rstrip("Z"))
        approvals = proposal.get("approvals", {})

        if not approvals:
            return {
                "proposal_id": proposal_id,
                "approval_count": 0,
                "fastest_approval_seconds": None,
                "average_approval_seconds": None,
                "is_suspicious": False,
                "reason": "no approvals yet",
            }

        # Calculate time to each approval
        approval_times = []
        for team_id, approval_data in approvals.items():
            approval_ts = datetime.fromisoformat(approval_data["timestamp"].rstrip("Z"))
            delta = (approval_ts - created_at).total_seconds()
            approval_times.append({
                "team_id": team_id,
                "seconds": delta,
            })

        fastest = min(t["seconds"] for t in approval_times)
        average = sum(t["seconds"] for t in approval_times) / len(approval_times)

        # Suspicious thresholds:
        # - Any approval within 60 seconds: very suspicious
        # - Average under 5 minutes: suspicious
        # - All approvals within 10 minutes: suspicious
        very_fast = fastest < 60
        fast_average = average < 300
        all_fast = max(t["seconds"] for t in approval_times) < 600

        is_suspicious = very_fast or (fast_average and all_fast)

        reasons = []
        if very_fast:
            reasons.append(f"approval within {fastest:.0f}s")
        if fast_average:
            reasons.append(f"average {average:.0f}s")
        if all_fast:
            reasons.append("all approvals within 10 minutes")

        return {
            "proposal_id": proposal_id,
            "approval_count": len(approvals),
            "fastest_approval_seconds": fastest,
            "average_approval_seconds": average,
            "approval_times": approval_times,
            "is_suspicious": is_suspicious,
            "reason": "; ".join(reasons) if reasons else "normal timing",
        }

    def get_temporal_analysis_report(self) -> Dict:
        """
        Analyze timing patterns across all cross-team proposals.

        Identifies proposals with suspiciously fast approval times.
        """
        self._ensure_xteam_table()
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT proposal_id FROM cross_team_proposals WHERE status = 'approved'"
            ).fetchall()

        flagged_proposals = []
        normal_proposals = []

        for row in rows:
            proposal_id = row[0]
            try:
                analysis = self.analyze_approval_timing(proposal_id)
                if analysis["is_suspicious"]:
                    flagged_proposals.append(analysis)
                else:
                    normal_proposals.append(analysis)
            except Exception:
                pass

        # Health assessment
        total = len(flagged_proposals) + len(normal_proposals)
        if total == 0:
            health = "healthy"
        elif len(flagged_proposals) / total > 0.5:
            health = "critical"
        elif len(flagged_proposals) > 0:
            health = "warning"
        else:
            health = "healthy"

        return {
            "total_proposals": total,
            "flagged_count": len(flagged_proposals),
            "normal_count": len(normal_proposals),
            "flagged_proposals": flagged_proposals,
            "health": health,
        }

    def get_cross_domain_temporal_analysis(
        self,
        time_window_hours: int = 24,
        min_proposals: int = 3,
        correlation_threshold: float = 0.8,
    ) -> Dict:
        """
        Analyze timing patterns across multiple proposals and teams.

        Cross-domain temporal analysis detects sophisticated coordination that
        individual proposal analysis might miss:
        - Multiple proposals from same team all getting fast approvals
        - "Burst" patterns where many proposals are created/approved together
        - Timing correlation between proposals from different teams

        Args:
            time_window_hours: Window to consider proposals "related" (default 24h)
            min_proposals: Minimum proposals to trigger burst detection (default 3)
            correlation_threshold: How correlated timing must be to flag (0-1)

        Returns:
            Cross-domain temporal analysis with patterns and flags
        """
        self._ensure_xteam_table()
        now = datetime.now(timezone.utc)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT proposal_id, data, status, created_at
                FROM cross_team_proposals
                WHERE status IN ('approved', 'pending')
                ORDER BY created_at DESC
            """).fetchall()

        if not rows:
            return {
                "analysis_window_hours": time_window_hours,
                "proposals_analyzed": 0,
                "burst_patterns": [],
                "team_patterns": {},
                "correlated_approvals": [],
                "health_status": "healthy",
                "issues": [],
            }

        # Parse proposals
        proposals = []
        for row in rows:
            try:
                data = json.loads(row["data"])
                created_at = datetime.fromisoformat(row["created_at"].rstrip("Z"))
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                proposals.append({
                    "proposal_id": row["proposal_id"],
                    "proposing_team": data.get("proposing_team_id", ""),
                    "target_teams": data.get("target_team_ids", []),
                    "action_type": data.get("action_type", ""),
                    "created_at": created_at,
                    "status": row["status"],
                    "approvals": data.get("approvals", {}),
                })
            except (json.JSONDecodeError, ValueError):
                continue

        # Analysis 1: Burst detection - many proposals in short window
        burst_patterns = self._detect_proposal_bursts(
            proposals, time_window_hours, min_proposals
        )

        # Analysis 2: Per-team patterns - does one team always get fast approvals?
        team_patterns = self._analyze_team_approval_patterns(proposals)

        # Analysis 3: Correlated approvals - same approvers, same timing
        correlated_approvals = self._detect_correlated_approvals(
            proposals, correlation_threshold
        )

        # Health assessment
        issues = []
        health_status = "healthy"

        if burst_patterns:
            health_status = "warning"
            for burst in burst_patterns:
                issues.append(
                    f"Burst detected: {burst['count']} proposals in {burst['window_minutes']:.0f} min"
                )

        suspicious_teams = [
            t for t, d in team_patterns.items()
            if d.get("suspicion_level", "normal") in ("high", "critical")
        ]
        if suspicious_teams:
            health_status = "warning"
            issues.extend([
                f"Suspicious timing pattern for team {t}"
                for t in suspicious_teams
            ])

        if correlated_approvals:
            if len(correlated_approvals) > 3:
                health_status = "critical"
            else:
                health_status = "warning"
            issues.append(
                f"Detected {len(correlated_approvals)} correlated approval patterns"
            )

        return {
            "analysis_window_hours": time_window_hours,
            "proposals_analyzed": len(proposals),
            "burst_patterns": burst_patterns,
            "team_patterns": team_patterns,
            "correlated_approvals": correlated_approvals,
            "health_status": health_status,
            "issues": issues,
        }

    def _detect_proposal_bursts(
        self,
        proposals: List[Dict],
        window_hours: int,
        min_count: int,
    ) -> List[Dict]:
        """
        Detect bursts of proposals created in short time windows.

        A burst indicates potential coordination - legitimate proposals
        are usually spread over time.
        """
        if len(proposals) < min_count:
            return []

        bursts = []
        window = timedelta(hours=window_hours)

        # Sort by creation time
        sorted_proposals = sorted(proposals, key=lambda p: p["created_at"])

        # Sliding window detection
        i = 0
        while i < len(sorted_proposals):
            window_start = sorted_proposals[i]["created_at"]
            window_end = window_start + window

            # Find all proposals in this window
            window_proposals = [
                p for p in sorted_proposals[i:]
                if p["created_at"] <= window_end
            ]

            if len(window_proposals) >= min_count:
                # Check if they share common characteristics
                proposing_teams = [p["proposing_team"] for p in window_proposals]
                unique_teams = set(proposing_teams)

                # Suspicious if many from same team or all to same targets
                team_concentration = max(
                    proposing_teams.count(t) for t in unique_teams
                ) / len(window_proposals)

                actual_minutes = (
                    window_proposals[-1]["created_at"] - window_proposals[0]["created_at"]
                ).total_seconds() / 60

                bursts.append({
                    "window_start": window_start.isoformat(),
                    "window_end": window_end.isoformat(),
                    "count": len(window_proposals),
                    "window_minutes": actual_minutes,
                    "proposal_ids": [p["proposal_id"] for p in window_proposals],
                    "team_concentration": round(team_concentration, 2),
                    "unique_teams": len(unique_teams),
                    "suspicious": team_concentration > 0.7 or actual_minutes < 60,
                })

                # Skip past this burst
                i += len(window_proposals)
            else:
                i += 1

        return [b for b in bursts if b["suspicious"]]

    def _analyze_team_approval_patterns(self, proposals: List[Dict]) -> Dict:
        """
        Analyze approval patterns per team.

        Suspicious patterns:
        - Team consistently receives fast approvals
        - Team consistently gives fast approvals
        - Team has abnormal approval timing distribution
        """
        team_stats = {}

        for proposal in proposals:
            proposing_team = proposal["proposing_team"]
            approvals = proposal.get("approvals", {})

            if proposing_team not in team_stats:
                team_stats[proposing_team] = {
                    "proposals_created": 0,
                    "approvals_received": 0,
                    "approvals_given": 0,
                    "fast_approvals_received": 0,
                    "fast_approvals_given": 0,
                    "avg_time_to_approval": [],
                    "avg_time_to_give_approval": [],
                }

            stats = team_stats[proposing_team]
            stats["proposals_created"] += 1

            created_at = proposal["created_at"]
            for approver_team, approval_data in approvals.items():
                try:
                    approval_ts = datetime.fromisoformat(
                        approval_data["timestamp"].rstrip("Z")
                    )
                    if approval_ts.tzinfo is None:
                        approval_ts = approval_ts.replace(tzinfo=timezone.utc)

                    delta_seconds = (approval_ts - created_at).total_seconds()
                    stats["approvals_received"] += 1
                    stats["avg_time_to_approval"].append(delta_seconds)

                    if delta_seconds < 300:  # Under 5 minutes = fast
                        stats["fast_approvals_received"] += 1

                    # Track the approver's stats too
                    if approver_team not in team_stats:
                        team_stats[approver_team] = {
                            "proposals_created": 0,
                            "approvals_received": 0,
                            "approvals_given": 0,
                            "fast_approvals_received": 0,
                            "fast_approvals_given": 0,
                            "avg_time_to_approval": [],
                            "avg_time_to_give_approval": [],
                        }

                    approver_stats = team_stats[approver_team]
                    approver_stats["approvals_given"] += 1
                    approver_stats["avg_time_to_give_approval"].append(delta_seconds)

                    if delta_seconds < 300:
                        approver_stats["fast_approvals_given"] += 1

                except (ValueError, KeyError):
                    continue

        # Calculate final stats and suspicion levels
        result = {}
        for team_id, stats in team_stats.items():
            avg_received = (
                sum(stats["avg_time_to_approval"]) / len(stats["avg_time_to_approval"])
                if stats["avg_time_to_approval"] else None
            )
            avg_given = (
                sum(stats["avg_time_to_give_approval"]) / len(stats["avg_time_to_give_approval"])
                if stats["avg_time_to_give_approval"] else None
            )

            # Suspicion level based on fast approval ratio
            fast_ratio_received = (
                stats["fast_approvals_received"] / stats["approvals_received"]
                if stats["approvals_received"] > 0 else 0
            )
            fast_ratio_given = (
                stats["fast_approvals_given"] / stats["approvals_given"]
                if stats["approvals_given"] > 0 else 0
            )

            suspicion_level = "normal"
            if fast_ratio_received > 0.8 and stats["approvals_received"] >= 3:
                suspicion_level = "high"
            elif fast_ratio_received > 0.5 and stats["approvals_received"] >= 5:
                suspicion_level = "medium"
            elif fast_ratio_given > 0.8 and stats["approvals_given"] >= 3:
                suspicion_level = "high"
            elif fast_ratio_given > 0.5 and stats["approvals_given"] >= 5:
                suspicion_level = "medium"

            if (fast_ratio_received > 0.9 and fast_ratio_given > 0.9 and
                stats["approvals_received"] >= 3 and stats["approvals_given"] >= 3):
                suspicion_level = "critical"

            result[team_id] = {
                "proposals_created": stats["proposals_created"],
                "approvals_received": stats["approvals_received"],
                "approvals_given": stats["approvals_given"],
                "fast_approvals_received": stats["fast_approvals_received"],
                "fast_approvals_given": stats["fast_approvals_given"],
                "avg_time_to_receive_approval_seconds": round(avg_received, 1) if avg_received else None,
                "avg_time_to_give_approval_seconds": round(avg_given, 1) if avg_given else None,
                "fast_approval_ratio_received": round(fast_ratio_received, 2),
                "fast_approval_ratio_given": round(fast_ratio_given, 2),
                "suspicion_level": suspicion_level,
            }

        return result

    def _detect_correlated_approvals(
        self,
        proposals: List[Dict],
        threshold: float,
    ) -> List[Dict]:
        """
        Detect proposals with suspiciously correlated approval timing.

        If the same approvers approve multiple proposals within similar
        timeframes, it suggests coordination rather than independent review.
        """
        correlations = []

        # Compare pairs of proposals
        for i, prop1 in enumerate(proposals):
            if not prop1.get("approvals"):
                continue

            for prop2 in proposals[i + 1:]:
                if not prop2.get("approvals"):
                    continue

                # Find common approvers
                common_approvers = set(prop1["approvals"].keys()) & set(prop2["approvals"].keys())

                if len(common_approvers) < 2:
                    continue

                # Check timing correlation for common approvers
                timing_diffs = []
                for approver in common_approvers:
                    try:
                        ts1 = datetime.fromisoformat(
                            prop1["approvals"][approver]["timestamp"].rstrip("Z")
                        )
                        ts2 = datetime.fromisoformat(
                            prop2["approvals"][approver]["timestamp"].rstrip("Z")
                        )

                        # Time between same approver's approvals
                        diff = abs((ts2 - ts1).total_seconds())
                        timing_diffs.append(diff)
                    except (ValueError, KeyError):
                        continue

                if not timing_diffs:
                    continue

                # Correlation score: low variance in timing diffs = high correlation
                avg_diff = sum(timing_diffs) / len(timing_diffs)
                if avg_diff < 600:  # All within 10 minutes
                    variance = sum((d - avg_diff) ** 2 for d in timing_diffs) / len(timing_diffs)
                    # Normalize variance to correlation score
                    correlation = 1 / (1 + variance / 10000)  # Higher = more correlated

                    if correlation > threshold:
                        correlations.append({
                            "proposal_1": prop1["proposal_id"],
                            "proposal_2": prop2["proposal_id"],
                            "common_approvers": list(common_approvers),
                            "avg_time_between_approvals_seconds": round(avg_diff, 1),
                            "timing_variance": round(variance, 1),
                            "correlation_score": round(correlation, 3),
                        })

        return correlations

    def get_federation_health_dashboard(
        self,
        include_heartbeat: bool = True,
        include_temporal: bool = True,
        include_cross_domain: bool = True,
        include_reciprocity: bool = True,
        include_cycles: bool = True,
        include_audit: bool = True,
    ) -> Dict:
        """
        Comprehensive federation health dashboard.

        Aggregates all health metrics and analysis into a single view:
        - Heartbeat status and history
        - Temporal pattern analysis
        - Cross-domain correlation
        - Reciprocity patterns
        - Approval cycle detection
        - Governance audit alerts

        Args:
            include_*: Toggle individual analysis sections

        Returns:
            Consolidated health dashboard with all metrics and alerts
        """
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()

        dashboard = {
            "generated_at": timestamp,
            "overall_health": "healthy",
            "alerts": [],
            "summary": {},
            "details": {},
        }

        # Track health issues for overall assessment
        critical_issues = []
        warning_issues = []
        info_notes = []

        # --- Heartbeat Analysis ---
        if include_heartbeat:
            try:
                history = self.get_heartbeat_history(limit=5)
                if history:
                    latest = history[0]
                    dashboard["details"]["heartbeat"] = {
                        "latest": latest,
                        "recent_history": history,
                    }
                    dashboard["summary"]["last_heartbeat"] = latest["timestamp"]
                    dashboard["summary"]["heartbeat_status"] = latest["health_status"]

                    if latest["health_status"] == "critical":
                        critical_issues.append("Heartbeat status critical")
                    elif latest["health_status"] in ("warning", "degraded"):
                        warning_issues.append(f"Heartbeat status: {latest['health_status']}")

                    for issue in latest.get("health_issues", []):
                        warning_issues.append(f"Heartbeat: {issue}")
                else:
                    dashboard["details"]["heartbeat"] = {"status": "no_data"}
                    info_notes.append("No heartbeat history")
            except Exception as e:
                dashboard["details"]["heartbeat"] = {"error": str(e)}

        # --- Temporal Pattern Analysis ---
        if include_temporal:
            try:
                temporal = self.get_temporal_analysis_report()
                dashboard["details"]["temporal"] = temporal
                dashboard["summary"]["proposals_flagged"] = temporal["flagged_count"]
                dashboard["summary"]["temporal_health"] = temporal["health"]

                if temporal["health"] == "critical":
                    critical_issues.append(f"Temporal: {temporal['flagged_count']} suspicious proposals")
                elif temporal["health"] == "warning":
                    warning_issues.append(f"Temporal: {temporal['flagged_count']} suspicious proposals")
            except Exception as e:
                dashboard["details"]["temporal"] = {"error": str(e)}

        # --- Cross-Domain Temporal Analysis ---
        if include_cross_domain:
            try:
                cross_domain = self.get_cross_domain_temporal_analysis()
                dashboard["details"]["cross_domain"] = cross_domain
                dashboard["summary"]["burst_patterns"] = len(cross_domain["burst_patterns"])
                dashboard["summary"]["correlated_approvals"] = len(cross_domain["correlated_approvals"])

                if cross_domain["health_status"] == "critical":
                    critical_issues.extend(cross_domain["issues"])
                elif cross_domain["health_status"] == "warning":
                    warning_issues.extend(cross_domain["issues"])
            except Exception as e:
                dashboard["details"]["cross_domain"] = {"error": str(e)}

        # --- Reciprocity Analysis ---
        if include_reciprocity:
            try:
                reciprocity = self.get_approval_reciprocity_report()
                dashboard["details"]["reciprocity"] = reciprocity
                dashboard["summary"]["reciprocity_flags"] = len(reciprocity.get("suspicious_pairs", []))

                if reciprocity.get("health") == "critical":
                    critical_issues.append("High reciprocity concentration detected")
                elif reciprocity.get("health") == "warning":
                    warning_issues.append(f"{len(reciprocity.get('suspicious_pairs', []))} suspicious approval pairs")
            except Exception as e:
                dashboard["details"]["reciprocity"] = {"error": str(e)}

        # --- Cycle Detection ---
        if include_cycles:
            try:
                cycles = self.detect_approval_cycles()
                dashboard["details"]["cycles"] = cycles
                dashboard["summary"]["approval_cycles"] = len(cycles.get("cycles", []))

                suspicious_cycles = [
                    c for c in cycles.get("cycles", [])
                    if c.get("suspicious", False)
                ]
                if suspicious_cycles:
                    critical_issues.append(f"{len(suspicious_cycles)} suspicious approval cycles")
            except Exception as e:
                dashboard["details"]["cycles"] = {"error": str(e)}

        # --- Governance Audit Analysis ---
        if include_audit:
            try:
                # Get recent warnings
                audit_warnings = self.get_governance_audit_log(risk_level="warning", limit=10)
                dashboard["details"]["audit_warnings"] = audit_warnings
                dashboard["summary"]["audit_warnings"] = len(audit_warnings)

                if audit_warnings:
                    recent = audit_warnings[0]
                    warning_issues.append(
                        f"Recent audit warning: {recent.get('audit_type', 'unknown')}"
                    )
            except Exception as e:
                dashboard["details"]["audit_warnings"] = {"error": str(e)}

        # --- Team Health Summary ---
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                active_count = conn.execute(
                    "SELECT COUNT(*) FROM federated_teams WHERE status = 'active'"
                ).fetchone()[0]

                avg_rep = conn.execute(
                    "SELECT AVG(witness_score) FROM federated_teams WHERE status = 'active'"
                ).fetchone()[0] or 0.0

                low_rep = conn.execute(
                    "SELECT COUNT(*) FROM federated_teams WHERE status = 'active' AND witness_score < ?",
                    (self.MIN_WITNESS_SCORE,)
                ).fetchone()[0]

            dashboard["summary"]["active_teams"] = active_count
            dashboard["summary"]["average_reputation"] = round(avg_rep, 3)
            dashboard["summary"]["low_reputation_teams"] = low_rep

            if active_count < 3:
                warning_issues.append(f"Low team count: {active_count}")
            if avg_rep < 0.5:
                warning_issues.append(f"Low average reputation: {avg_rep:.2f}")
            if low_rep > active_count * 0.3:
                critical_issues.append(f"Many low-reputation teams: {low_rep}/{active_count}")

        except Exception as e:
            dashboard["summary"]["team_error"] = str(e)

        # --- Calculate Overall Health ---
        if critical_issues:
            dashboard["overall_health"] = "critical"
            dashboard["alerts"] = critical_issues + warning_issues
        elif warning_issues:
            dashboard["overall_health"] = "warning"
            dashboard["alerts"] = warning_issues
        else:
            dashboard["overall_health"] = "healthy"
            dashboard["alerts"] = info_notes

        # Summary counts
        dashboard["summary"]["critical_count"] = len(critical_issues)
        dashboard["summary"]["warning_count"] = len(warning_issues)

        return dashboard


if __name__ == "__main__":
    print("=" * 60)
    print("Federation Registry - Self Test")
    print("=" * 60)

    reg = FederationRegistry()

    # Register teams
    teams = [
        ("team:alpha", "Alpha Corp", ["finance", "audit"]),
        ("team:beta", "Beta Labs", ["engineering", "security"]),
        ("team:gamma", "Gamma Gov", ["governance", "compliance"]),
        ("team:delta", "Delta Data", ["analytics", "audit"]),
    ]

    for tid, name, domains in teams:
        t = reg.register_team(tid, name, domains=domains, member_count=5)
        print(f"  Registered: {t.name} ({t.team_id})")

    # Find witness pool for Alpha
    print("\nWitness pool for Alpha:")
    pool = reg.find_witness_pool("team:alpha", count=3)
    for t in pool:
        print(f"  {t.name} (score={t.witness_score:.2f})")

    # Simulate witness events
    print("\nSimulating witness events...")
    reg.record_witness_event("team:beta", "team:alpha", "beta:member1", "msig:001")
    reg.record_witness_event("team:gamma", "team:alpha", "gamma:member1", "msig:001")
    reg.record_witness_event("team:alpha", "team:beta", "alpha:member1", "msig:002")
    reg.record_witness_event("team:alpha", "team:beta", "alpha:member2", "msig:003")

    # Update outcomes
    reg.update_witness_outcome("msig:001", "succeeded")
    reg.update_witness_outcome("msig:002", "succeeded")
    reg.update_witness_outcome("msig:003", "failed")

    # Check reciprocity
    print("\nReciprocity analysis (Alpha <-> Beta):")
    recip = reg.check_reciprocity("team:alpha", "team:beta")
    print(f"  Alpha witnesses Beta: {recip['a_witnesses_b']}")
    print(f"  Beta witnesses Alpha: {recip['b_witnesses_a']}")
    print(f"  Reciprocity ratio: {recip['reciprocity_ratio']:.2f}")
    print(f"  Suspicious: {recip['is_suspicious']}")

    # Collusion report
    print("\nCollusion report:")
    report = reg.get_collusion_report()
    print(f"  Teams: {report['total_teams']}")
    print(f"  Pairs analyzed: {report['pairs_analyzed']}")
    print(f"  Flagged: {len(report['flagged_pairs'])}")
    print(f"  Health: {report['health']}")

    # Check witness scores
    print("\nWitness scores after outcomes:")
    for tid, name, _ in teams:
        t = reg.get_team(tid)
        print(f"  {t.name}: {t.witness_score:.3f} "
              f"({t.witness_successes}S/{t.witness_failures}F/{t.witness_count}T)")

    print("\nSelf-test complete.")
