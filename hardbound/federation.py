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
                    witness_score REAL DEFAULT 1.0,
                    witness_count INTEGER DEFAULT 0,
                    witness_successes INTEGER DEFAULT 0,
                    witness_failures INTEGER DEFAULT 0
                )
            """)
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
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO federated_teams
                (team_id, name, registered_at, status, domains, capabilities,
                 admin_lct, creator_lct, member_count, witness_score, witness_count,
                 witness_successes, witness_failures)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                team.team_id, team.name, team.registered_at,
                team.status.value,
                json.dumps(team.domains), json.dumps(team.capabilities),
                team.admin_lct, team.creator_lct, team.member_count,
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

    def suspend_team(self, team_id: str, reason: str = "") -> bool:
        """Suspend a team from the federation (e.g., for collusion)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE federated_teams SET status = ? WHERE team_id = ?",
                (FederationStatus.SUSPENDED.value, team_id)
            )
        return True

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
            witness_score=row["witness_score"] if row["witness_score"] is not None else 1.0,
            witness_count=row["witness_count"] or 0,
            witness_successes=row["witness_successes"] or 0,
            witness_failures=row["witness_failures"] or 0,
        )


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
