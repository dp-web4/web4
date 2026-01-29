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
        require_outsider: bool = False,
        outsider_team_ids: List[str] = None,
        voting_mode: str = "veto",
        approval_threshold: float = 0.5,
    ) -> Dict:
        """
        Create a proposal that requires approval from multiple federation teams.

        This enables federation-level governance where actions affecting multiple
        teams require coordination. Examples:
        - Shared resource allocation
        - Cross-team access grants
        - Federation policy changes

        Voting modes:
        - "veto": Single rejection blocks proposal (default, strong minority protection)
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
            voting_mode: "veto" (default) or "weighted"
            approval_threshold: For weighted mode, required weighted approval ratio (0.0-1.0)

        Returns:
            Cross-team proposal record
        """
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
        }

        # Persist to database
        self._ensure_xteam_table()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO cross_team_proposals
                (proposal_id, data, status, created_at)
                VALUES (?, ?, ?, ?)
            """, (proposal_id, json.dumps(proposal), "pending", now.isoformat()))

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
