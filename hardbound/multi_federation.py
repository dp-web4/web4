"""
Multi-Federation Witness Requirements

Extends the federation registry to support cross-federation governance:

1. Federation Identity: Each federation has its own unique ID and profile
2. Inter-Federation Trust: Federations can establish trust relationships
3. Cross-Federation Witnessing: Proposals affecting multiple federations
   require witnesses from each affected federation

Use cases:
- Global proposals that span organizations
- Inter-company collaborations with shared governance
- Decentralized autonomous organizations (DAOs) with sub-DAOs

Track BF: Multi-federation witness requirements
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from enum import Enum


class FederationRelationship(Enum):
    """Type of relationship between two federations."""
    NONE = "none"           # No established relationship
    PEER = "peer"           # Equal status, mutual recognition
    PARENT = "parent"       # This federation is parent of the other
    CHILD = "child"         # This federation is child of the other
    TRUSTED = "trusted"     # Unilateral trust (we trust them)
    ALLIED = "allied"       # Mutual alliance (we trust each other)


@dataclass
class FederationProfile:
    """Profile of a federation in the multi-federation registry."""
    federation_id: str
    name: str
    created_at: str
    status: str = "active"  # active, suspended, dissolved

    # Governance parameters
    min_team_count: int = 3  # Minimum teams to be considered operational
    requires_external_witness: bool = True  # Require witness from outside federation

    # Trust metrics
    reputation_score: float = 0.5  # Overall federation reputation
    active_team_count: int = 0
    proposal_count: int = 0
    success_rate: float = 0.5


@dataclass
class InterFederationTrust:
    """Trust relationship between two federations."""
    source_federation_id: str
    target_federation_id: str
    relationship: FederationRelationship
    established_at: str
    trust_score: float = 0.5  # How much source trusts target (0-1)
    witness_allowed: bool = True  # Can target witness for source's proposals
    last_interaction: str = ""
    successful_interactions: int = 0  # Track BI: Count of successful interactions
    failed_interactions: int = 0  # Track BI: Count of failed interactions


@dataclass
class CrossFederationProposal:
    """A proposal that spans multiple federations."""
    proposal_id: str
    proposing_federation_id: str
    proposing_team_id: str
    affected_federation_ids: List[str]
    action_type: str
    description: str
    created_at: str
    status: str = "pending"  # pending, approved, rejected

    # Approval tracking per federation
    federation_approvals: Dict[str, Dict] = field(default_factory=dict)
    # {federation_id: {"approved": bool, "timestamp": str, "approving_teams": [...]}}

    # Witness requirements
    requires_external_federation_witness: bool = True
    external_witnesses: List[str] = field(default_factory=list)


class MultiFederationRegistry:
    """
    Registry for managing multiple federations and their relationships.

    This sits above individual FederationRegistry instances to coordinate
    cross-federation governance.
    """

    # Minimum trust score for cross-federation witnessing
    MIN_CROSS_FED_TRUST = 0.4

    # Trust Bootstrap Limits (Track BI)
    # Maximum trust that can be claimed for a new relationship
    MAX_INITIAL_TRUST = 0.5

    # Maximum trust boost per successful interaction
    TRUST_INCREMENT_PER_SUCCESS = 0.05

    # Federation age requirements (days) for trust levels
    TRUST_AGE_REQUIREMENTS = {
        0.5: 0,     # Immediate - up to 0.5
        0.6: 7,     # 1 week - up to 0.6
        0.7: 30,    # 1 month - up to 0.7
        0.8: 90,    # 3 months - up to 0.8
        0.9: 180,   # 6 months - up to 0.9
        1.0: 365,   # 1 year - up to 1.0
    }

    # Minimum successful interactions for trust levels
    TRUST_INTERACTION_REQUIREMENTS = {
        0.5: 0,     # No interactions needed for baseline
        0.6: 3,     # 3 successful interactions
        0.7: 10,    # 10 successful interactions
        0.8: 25,    # 25 successful interactions
        0.9: 50,    # 50 successful interactions
        1.0: 100,   # 100 successful interactions
    }

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the multi-federation registry.

        Args:
            db_path: Path to SQLite database (default: in-memory)
        """
        if db_path:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.db_path = ":memory:"

        self._ensure_tables()

    def _ensure_tables(self):
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS federations (
                    federation_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    min_team_count INTEGER DEFAULT 3,
                    requires_external_witness INTEGER DEFAULT 1,
                    reputation_score REAL DEFAULT 0.5,
                    active_team_count INTEGER DEFAULT 0,
                    proposal_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.5
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS inter_federation_trust (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_federation_id TEXT NOT NULL,
                    target_federation_id TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    established_at TEXT NOT NULL,
                    trust_score REAL DEFAULT 0.5,
                    witness_allowed INTEGER DEFAULT 1,
                    last_interaction TEXT DEFAULT '',
                    successful_interactions INTEGER DEFAULT 0,
                    failed_interactions INTEGER DEFAULT 0,
                    UNIQUE(source_federation_id, target_federation_id)
                )
            """)

            # Migration: add columns if they don't exist
            try:
                conn.execute("ALTER TABLE inter_federation_trust ADD COLUMN successful_interactions INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE inter_federation_trust ADD COLUMN failed_interactions INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass

            conn.execute("""
                CREATE TABLE IF NOT EXISTS cross_federation_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    proposing_federation_id TEXT NOT NULL,
                    proposing_team_id TEXT NOT NULL,
                    affected_federation_ids TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    federation_approvals TEXT DEFAULT '{}',
                    requires_external_federation_witness INTEGER DEFAULT 1,
                    external_witnesses TEXT DEFAULT '[]'
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trust_source
                ON inter_federation_trust(source_federation_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_proposals_status
                ON cross_federation_proposals(status)
            """)

    def register_federation(
        self,
        federation_id: str,
        name: str,
        min_team_count: int = 3,
        requires_external_witness: bool = True,
    ) -> FederationProfile:
        """
        Register a new federation in the multi-federation registry.

        Args:
            federation_id: Unique identifier for the federation
            name: Human-readable name
            min_team_count: Minimum teams required
            requires_external_witness: Whether external witnesses are required

        Returns:
            FederationProfile for the registered federation
        """
        now = datetime.now(timezone.utc).isoformat()

        profile = FederationProfile(
            federation_id=federation_id,
            name=name,
            created_at=now,
            min_team_count=min_team_count,
            requires_external_witness=requires_external_witness,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO federations
                (federation_id, name, created_at, min_team_count, requires_external_witness)
                VALUES (?, ?, ?, ?, ?)
            """, (
                profile.federation_id,
                profile.name,
                profile.created_at,
                profile.min_team_count,
                1 if profile.requires_external_witness else 0,
            ))

        return profile

    def get_federation(self, federation_id: str) -> Optional[FederationProfile]:
        """Get a federation's profile."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM federations WHERE federation_id = ?",
                (federation_id,)
            ).fetchone()

            if not row:
                return None

            return FederationProfile(
                federation_id=row["federation_id"],
                name=row["name"],
                created_at=row["created_at"],
                status=row["status"],
                min_team_count=row["min_team_count"],
                requires_external_witness=bool(row["requires_external_witness"]),
                reputation_score=row["reputation_score"],
                active_team_count=row["active_team_count"],
                proposal_count=row["proposal_count"],
                success_rate=row["success_rate"],
            )

    def establish_trust(
        self,
        source_federation_id: str,
        target_federation_id: str,
        relationship: FederationRelationship = FederationRelationship.PEER,
        initial_trust: float = 0.5,
        witness_allowed: bool = True,
    ) -> InterFederationTrust:
        """
        Establish a trust relationship between two federations.

        Track BI: Applies trust bootstrap limits to prevent gaming.

        Args:
            source_federation_id: Federation establishing the trust
            target_federation_id: Federation being trusted
            relationship: Type of relationship
            initial_trust: Requested initial trust score (0-1), will be capped
            witness_allowed: Whether target can witness for source

        Returns:
            InterFederationTrust record with capped trust score
        """
        now = datetime.now(timezone.utc).isoformat()

        # Track BI: Apply bootstrap limits
        # 1. Cap initial trust at MAX_INITIAL_TRUST
        effective_trust = min(initial_trust, self.MAX_INITIAL_TRUST)

        # 2. Further cap based on target federation age
        target_fed = self.get_federation(target_federation_id)
        if target_fed:
            max_by_age = self._get_max_trust_by_age(target_fed.created_at)
            effective_trust = min(effective_trust, max_by_age)

        trust = InterFederationTrust(
            source_federation_id=source_federation_id,
            target_federation_id=target_federation_id,
            relationship=relationship,
            established_at=now,
            trust_score=effective_trust,
            witness_allowed=witness_allowed,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO inter_federation_trust
                (source_federation_id, target_federation_id, relationship,
                 established_at, trust_score, witness_allowed,
                 successful_interactions, failed_interactions)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
            """, (
                trust.source_federation_id,
                trust.target_federation_id,
                trust.relationship.value,
                trust.established_at,
                trust.trust_score,
                1 if trust.witness_allowed else 0,
            ))

        return trust

    def _get_max_trust_by_age(self, created_at: str) -> float:
        """
        Calculate maximum trust allowed based on federation age.

        Track BI: Newer federations have lower trust ceilings.
        """
        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            age_days = (datetime.now(timezone.utc) - created).days

            max_trust = 0.5  # Default
            for trust_level, required_days in sorted(self.TRUST_AGE_REQUIREMENTS.items()):
                if age_days >= required_days:
                    max_trust = trust_level
            return max_trust
        except (ValueError, TypeError):
            return 0.5  # Default if parsing fails

    def _get_max_trust_by_interactions(
        self,
        source_federation_id: str,
        target_federation_id: str,
    ) -> float:
        """
        Calculate maximum trust allowed based on successful interactions.

        Track BI: Trust must be earned through successful collaborations.
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT successful_interactions
                FROM inter_federation_trust
                WHERE source_federation_id = ? AND target_federation_id = ?
            """, (source_federation_id, target_federation_id)).fetchone()

            if not row:
                return 0.5

            interactions = row[0] or 0
            max_trust = 0.5
            for trust_level, required_interactions in sorted(self.TRUST_INTERACTION_REQUIREMENTS.items()):
                if interactions >= required_interactions:
                    max_trust = trust_level
            return max_trust

    def record_interaction(
        self,
        source_federation_id: str,
        target_federation_id: str,
        success: bool,
        auto_adjust_trust: bool = True,
    ) -> Dict:
        """
        Record an interaction between federations and optionally adjust trust.

        Track BI: Trust is earned through successful interactions.

        Args:
            source_federation_id: Federation that initiated
            target_federation_id: Federation that participated
            success: Whether the interaction was successful
            auto_adjust_trust: Whether to automatically adjust trust scores

        Returns:
            Updated trust status
        """
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Update interaction counts
            if success:
                conn.execute("""
                    UPDATE inter_federation_trust
                    SET successful_interactions = successful_interactions + 1,
                        last_interaction = ?
                    WHERE source_federation_id = ? AND target_federation_id = ?
                """, (now, source_federation_id, target_federation_id))
            else:
                conn.execute("""
                    UPDATE inter_federation_trust
                    SET failed_interactions = failed_interactions + 1,
                        last_interaction = ?
                    WHERE source_federation_id = ? AND target_federation_id = ?
                """, (now, source_federation_id, target_federation_id))

            # Get current trust data
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT trust_score, successful_interactions, failed_interactions
                FROM inter_federation_trust
                WHERE source_federation_id = ? AND target_federation_id = ?
            """, (source_federation_id, target_federation_id)).fetchone()

            if not row:
                return {"error": "No trust relationship found"}

            current_trust = row["trust_score"]
            successful = row["successful_interactions"]
            failed = row["failed_interactions"]

            # Calculate new trust if auto-adjusting
            new_trust = current_trust
            if auto_adjust_trust:
                # Get caps
                max_by_age = self._get_max_trust_by_age(
                    self.get_federation(target_federation_id).created_at
                    if self.get_federation(target_federation_id) else now
                )
                max_by_interactions = self._get_max_trust_by_interactions(
                    source_federation_id, target_federation_id
                )
                max_trust = min(max_by_age, max_by_interactions)

                if success:
                    # Increase trust up to cap
                    new_trust = min(
                        current_trust + self.TRUST_INCREMENT_PER_SUCCESS,
                        max_trust
                    )
                else:
                    # Decrease trust on failure
                    new_trust = max(0.1, current_trust - 0.1)

                conn.execute("""
                    UPDATE inter_federation_trust
                    SET trust_score = ?
                    WHERE source_federation_id = ? AND target_federation_id = ?
                """, (new_trust, source_federation_id, target_federation_id))

        return {
            "source_federation": source_federation_id,
            "target_federation": target_federation_id,
            "success": success,
            "previous_trust": current_trust,
            "new_trust": new_trust,
            "successful_interactions": successful,
            "failed_interactions": failed,
            "trust_adjusted": auto_adjust_trust,
        }

    def get_trust_bootstrap_status(
        self,
        source_federation_id: str,
        target_federation_id: str,
    ) -> Dict:
        """
        Get detailed trust bootstrap status between two federations.

        Track BI: Transparency into trust constraints.

        Returns:
            Dict with current trust, caps, and requirements for increase
        """
        trust = self.get_trust_relationship(source_federation_id, target_federation_id)
        target_fed = self.get_federation(target_federation_id)

        if not trust:
            return {"error": "No trust relationship exists"}

        # Get interaction counts
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT successful_interactions, failed_interactions
                FROM inter_federation_trust
                WHERE source_federation_id = ? AND target_federation_id = ?
            """, (source_federation_id, target_federation_id)).fetchone()
            successful = row[0] if row else 0
            failed = row[1] if row else 0

        # Calculate caps
        max_by_age = self._get_max_trust_by_age(
            target_fed.created_at if target_fed else datetime.now(timezone.utc).isoformat()
        )
        max_by_interactions = self._get_max_trust_by_interactions(
            source_federation_id, target_federation_id
        )
        effective_cap = min(max_by_age, max_by_interactions)

        # Calculate what's needed for next level
        next_level = None
        interactions_needed = None
        days_needed = None

        for trust_level in sorted(self.TRUST_AGE_REQUIREMENTS.keys()):
            if trust_level > trust.trust_score:
                next_level = trust_level
                interactions_needed = max(
                    0,
                    self.TRUST_INTERACTION_REQUIREMENTS.get(trust_level, 0) - successful
                )
                if target_fed:
                    created = datetime.fromisoformat(target_fed.created_at.replace('Z', '+00:00'))
                    current_age = (datetime.now(timezone.utc) - created).days
                    days_needed = max(
                        0,
                        self.TRUST_AGE_REQUIREMENTS.get(trust_level, 0) - current_age
                    )
                break

        return {
            "source_federation": source_federation_id,
            "target_federation": target_federation_id,
            "current_trust": trust.trust_score,
            "max_initial_trust": self.MAX_INITIAL_TRUST,
            "max_trust_by_age": max_by_age,
            "max_trust_by_interactions": max_by_interactions,
            "effective_trust_cap": effective_cap,
            "successful_interactions": successful,
            "failed_interactions": failed,
            "next_trust_level": next_level,
            "interactions_needed_for_next": interactions_needed,
            "days_needed_for_next": days_needed,
            "can_increase": trust.trust_score < effective_cap,
        }

    def get_trust_relationship(
        self,
        source_federation_id: str,
        target_federation_id: str,
    ) -> Optional[InterFederationTrust]:
        """Get the trust relationship from source to target."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM inter_federation_trust
                WHERE source_federation_id = ? AND target_federation_id = ?
            """, (source_federation_id, target_federation_id)).fetchone()

            if not row:
                return None

            # Handle columns that may not exist in older schemas
            try:
                successful = row["successful_interactions"] or 0
            except (KeyError, IndexError):
                successful = 0
            try:
                failed = row["failed_interactions"] or 0
            except (KeyError, IndexError):
                failed = 0

            return InterFederationTrust(
                source_federation_id=row["source_federation_id"],
                target_federation_id=row["target_federation_id"],
                relationship=FederationRelationship(row["relationship"]),
                established_at=row["established_at"],
                trust_score=row["trust_score"],
                witness_allowed=bool(row["witness_allowed"]),
                last_interaction=row["last_interaction"] or "",
                successful_interactions=successful,
                failed_interactions=failed,
            )

    # Alias for economic_federation compatibility
    def get_trust(
        self,
        source_federation_id: str,
        target_federation_id: str,
    ) -> Optional[InterFederationTrust]:
        """Alias for get_trust_relationship."""
        return self.get_trust_relationship(source_federation_id, target_federation_id)

    def update_trust(
        self,
        source_federation_id: str,
        target_federation_id: str,
        new_trust_score: float,
    ) -> float:
        """
        Update the trust score for an existing relationship.

        Track BN: Used by EconomicFederationRegistry for trust increases.

        Args:
            source_federation_id: Federation updating trust
            target_federation_id: Federation being trusted
            new_trust_score: New trust score

        Returns:
            The actual trust score after update (may be capped)
        """
        # Apply bootstrap limits
        max_by_age = self._get_max_trust_by_age(
            self.get_federation(target_federation_id).created_at
        )
        max_by_interactions = self._get_max_trust_by_interactions(
            source_federation_id, target_federation_id
        )
        effective_trust = min(new_trust_score, max_by_age, max_by_interactions)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE inter_federation_trust
                SET trust_score = ?
                WHERE source_federation_id = ? AND target_federation_id = ?
            """, (effective_trust, source_federation_id, target_federation_id))

        return effective_trust

    def find_eligible_witness_federations(
        self,
        requesting_federation_id: str,
        exclude_federations: List[str] = None,
        min_trust: float = None,
    ) -> List[Tuple[str, float]]:
        """
        Find federations eligible to provide witnesses.

        Args:
            requesting_federation_id: Federation needing witnesses
            exclude_federations: Federations to exclude
            min_trust: Minimum trust score (default: MIN_CROSS_FED_TRUST)

        Returns:
            List of (federation_id, trust_score) tuples, sorted by trust
        """
        min_trust = min_trust or self.MIN_CROSS_FED_TRUST
        exclude = set(exclude_federations or [])
        exclude.add(requesting_federation_id)  # Can't witness for self

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT target_federation_id, trust_score
                FROM inter_federation_trust
                WHERE source_federation_id = ?
                  AND witness_allowed = 1
                  AND trust_score >= ?
                ORDER BY trust_score DESC
            """, (requesting_federation_id, min_trust)).fetchall()

        return [
            (row[0], row[1])
            for row in rows
            if row[0] not in exclude
        ]

    def create_cross_federation_proposal(
        self,
        proposing_federation_id: str,
        proposing_team_id: str,
        affected_federation_ids: List[str],
        action_type: str,
        description: str,
        require_external_witness: bool = True,
    ) -> CrossFederationProposal:
        """
        Create a proposal that spans multiple federations.

        Args:
            proposing_federation_id: Federation creating the proposal
            proposing_team_id: Team within federation creating proposal
            affected_federation_ids: All federations affected by this proposal
            action_type: Type of action being proposed
            description: Human-readable description
            require_external_witness: Whether external federation witness needed

        Returns:
            CrossFederationProposal object
        """
        now = datetime.now(timezone.utc).isoformat()
        proposal_id = f"xfed:{hashlib.sha256(f'{proposing_team_id}:{now}'.encode()).hexdigest()[:12]}"

        # Ensure proposing federation is in affected list
        if proposing_federation_id not in affected_federation_ids:
            affected_federation_ids = [proposing_federation_id] + affected_federation_ids

        proposal = CrossFederationProposal(
            proposal_id=proposal_id,
            proposing_federation_id=proposing_federation_id,
            proposing_team_id=proposing_team_id,
            affected_federation_ids=affected_federation_ids,
            action_type=action_type,
            description=description,
            created_at=now,
            requires_external_federation_witness=require_external_witness,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO cross_federation_proposals
                (proposal_id, proposing_federation_id, proposing_team_id,
                 affected_federation_ids, action_type, description,
                 created_at, requires_external_federation_witness)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal.proposal_id,
                proposal.proposing_federation_id,
                proposal.proposing_team_id,
                json.dumps(proposal.affected_federation_ids),
                proposal.action_type,
                proposal.description,
                proposal.created_at,
                1 if proposal.requires_external_federation_witness else 0,
            ))

        return proposal

    def approve_from_federation(
        self,
        proposal_id: str,
        approving_federation_id: str,
        approving_teams: List[str],
    ) -> Dict:
        """
        Record approval from a federation for a cross-federation proposal.

        Args:
            proposal_id: Proposal being approved
            approving_federation_id: Federation providing approval
            approving_teams: Teams within federation that approved

        Returns:
            Updated approval status
        """
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM cross_federation_proposals WHERE proposal_id = ?",
                (proposal_id,)
            ).fetchone()

            if not row:
                raise ValueError(f"Proposal not found: {proposal_id}")

            affected = json.loads(row["affected_federation_ids"])
            if approving_federation_id not in affected:
                raise ValueError(
                    f"Federation {approving_federation_id} not affected by this proposal"
                )

            approvals = json.loads(row["federation_approvals"])
            approvals[approving_federation_id] = {
                "approved": True,
                "timestamp": now,
                "approving_teams": approving_teams,
            }

            # Check if all affected federations have approved
            all_approved = all(
                fed_id in approvals and approvals[fed_id].get("approved")
                for fed_id in affected
            )

            new_status = "approved" if all_approved else "pending"

            conn.execute("""
                UPDATE cross_federation_proposals
                SET federation_approvals = ?, status = ?
                WHERE proposal_id = ?
            """, (json.dumps(approvals), new_status, proposal_id))

        return {
            "proposal_id": proposal_id,
            "approving_federation": approving_federation_id,
            "approving_teams": approving_teams,
            "all_approved": all_approved,
            "new_status": new_status,
        }

    def add_external_witness(
        self,
        proposal_id: str,
        witness_federation_id: str,
        witness_team_id: str,
    ) -> Dict:
        """
        Add an external federation witness to a proposal.

        The witness must be from a federation not affected by the proposal
        but trusted by the proposing federation.

        Args:
            proposal_id: Proposal being witnessed
            witness_federation_id: Federation providing witness
            witness_team_id: Specific team providing witness

        Returns:
            Status of witness addition
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM cross_federation_proposals WHERE proposal_id = ?",
                (proposal_id,)
            ).fetchone()

            if not row:
                raise ValueError(f"Proposal not found: {proposal_id}")

            affected = json.loads(row["affected_federation_ids"])
            proposing_fed = row["proposing_federation_id"]

            # Witness federation must not be affected
            if witness_federation_id in affected:
                raise ValueError(
                    f"Witness federation {witness_federation_id} is affected by proposal"
                )

            # Check trust relationship
            trust = self.get_trust_relationship(proposing_fed, witness_federation_id)
            if not trust or not trust.witness_allowed:
                raise ValueError(
                    f"No witness trust from {proposing_fed} to {witness_federation_id}"
                )

            if trust.trust_score < self.MIN_CROSS_FED_TRUST:
                raise ValueError(
                    f"Trust score {trust.trust_score} below minimum {self.MIN_CROSS_FED_TRUST}"
                )

            witnesses = json.loads(row["external_witnesses"])
            witness_entry = f"{witness_federation_id}:{witness_team_id}"
            if witness_entry not in witnesses:
                witnesses.append(witness_entry)

            conn.execute("""
                UPDATE cross_federation_proposals
                SET external_witnesses = ?
                WHERE proposal_id = ?
            """, (json.dumps(witnesses), proposal_id))

        return {
            "proposal_id": proposal_id,
            "witness_federation": witness_federation_id,
            "witness_team": witness_team_id,
            "total_external_witnesses": len(witnesses),
        }

    def check_proposal_requirements(self, proposal_id: str) -> Dict:
        """
        Check if a cross-federation proposal meets all requirements.

        Returns:
            Dict with requirement status
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM cross_federation_proposals WHERE proposal_id = ?",
                (proposal_id,)
            ).fetchone()

            if not row:
                raise ValueError(f"Proposal not found: {proposal_id}")

        affected = json.loads(row["affected_federation_ids"])
        approvals = json.loads(row["federation_approvals"])
        witnesses = json.loads(row["external_witnesses"])
        requires_external = bool(row["requires_external_federation_witness"])

        # Check federation approvals
        missing_approvals = [
            fed_id for fed_id in affected
            if fed_id not in approvals or not approvals[fed_id].get("approved")
        ]

        # Check external witness requirement
        has_external_witness = len(witnesses) > 0

        all_requirements_met = (
            len(missing_approvals) == 0 and
            (not requires_external or has_external_witness)
        )

        return {
            "proposal_id": proposal_id,
            "affected_federations": affected,
            "approved_federations": [
                fed_id for fed_id in affected
                if fed_id in approvals and approvals[fed_id].get("approved")
            ],
            "missing_approvals": missing_approvals,
            "external_witnesses": witnesses,
            "requires_external_witness": requires_external,
            "has_external_witness": has_external_witness,
            "all_requirements_met": all_requirements_met,
            "current_status": row["status"],
        }

    # =========================================================================
    # Track BJ: Federation-Level Reciprocity Detection
    # =========================================================================

    # Maximum reciprocity ratio before flagging (Track BJ)
    MAX_FEDERATION_RECIPROCITY = 0.7  # >70% reciprocal = suspicious

    # Minimum approvals to analyze
    MIN_APPROVALS_FOR_ANALYSIS = 5

    def analyze_federation_reciprocity(
        self,
        federation_id: str,
        time_window_days: int = 30,
    ) -> Dict:
        """
        Analyze reciprocal approval patterns between federations.

        Track BJ: Detects collusion where federations approve each other's
        proposals at suspiciously high rates.

        Args:
            federation_id: Federation to analyze
            time_window_days: Number of days to look back

        Returns:
            Dict with reciprocity analysis
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=time_window_days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get all proposals this federation approved
            rows = conn.execute("""
                SELECT proposal_id, proposing_federation_id, federation_approvals
                FROM cross_federation_proposals
                WHERE created_at >= ?
                  AND status IN ('approved', 'pending')
            """, (cutoff,)).fetchall()

        # Count approvals given to each federation
        approvals_given: Dict[str, int] = {}
        approvals_received: Dict[str, int] = {}

        for row in rows:
            proposer = row["proposing_federation_id"]
            approvals = json.loads(row["federation_approvals"])

            # Did this federation approve this proposal?
            if federation_id in approvals and approvals[federation_id].get("approved"):
                if proposer != federation_id:  # Don't count self-approval
                    approvals_given[proposer] = approvals_given.get(proposer, 0) + 1

            # Did this federation propose and get approval?
            if proposer == federation_id:
                for approver, details in approvals.items():
                    if approver != federation_id and details.get("approved"):
                        approvals_received[approver] = approvals_received.get(approver, 0) + 1

        # Calculate reciprocity ratios
        reciprocity_scores = {}
        for partner_fed in set(approvals_given.keys()) | set(approvals_received.keys()):
            given = approvals_given.get(partner_fed, 0)
            received = approvals_received.get(partner_fed, 0)
            total = given + received

            if total >= self.MIN_APPROVALS_FOR_ANALYSIS:
                # Reciprocity = min(given, received) / max(given, received)
                # High ratio means balanced give/take (potentially collusion)
                if max(given, received) > 0:
                    reciprocity = min(given, received) / max(given, received)
                else:
                    reciprocity = 0.0

                reciprocity_scores[partner_fed] = {
                    "approvals_given": given,
                    "approvals_received": received,
                    "total_interactions": total,
                    "reciprocity_ratio": reciprocity,
                    "suspicious": reciprocity > self.MAX_FEDERATION_RECIPROCITY,
                }

        # Identify suspicious pairs
        suspicious_pairs = [
            (partner, data) for partner, data in reciprocity_scores.items()
            if data["suspicious"]
        ]

        return {
            "federation_id": federation_id,
            "time_window_days": time_window_days,
            "partner_analysis": reciprocity_scores,
            "total_approvals_given": sum(approvals_given.values()),
            "total_approvals_received": sum(approvals_received.values()),
            "suspicious_partners": [p[0] for p in suspicious_pairs],
            "suspicion_count": len(suspicious_pairs),
            "has_suspicious_patterns": len(suspicious_pairs) > 0,
        }

    def get_federation_collusion_report(
        self,
        time_window_days: int = 30,
    ) -> Dict:
        """
        Generate system-wide federation collusion report.

        Track BJ: Identifies all suspicious reciprocity patterns.

        Returns:
            Dict with system-wide collusion analysis
        """
        with sqlite3.connect(self.db_path) as conn:
            federations = conn.execute(
                "SELECT federation_id FROM federations WHERE status = 'active'"
            ).fetchall()

        federation_ids = [f[0] for f in federations]

        # Analyze each federation
        analyses = {}
        for fed_id in federation_ids:
            analyses[fed_id] = self.analyze_federation_reciprocity(
                fed_id, time_window_days
            )

        # Find mutual suspicion (both sides flag each other)
        collusion_rings = []
        checked = set()
        for fed_id, analysis in analyses.items():
            for partner in analysis["suspicious_partners"]:
                pair = tuple(sorted([fed_id, partner]))
                if pair not in checked:
                    checked.add(pair)
                    # Check if partner also flagged fed_id
                    if (partner in analyses and
                        fed_id in analyses[partner]["suspicious_partners"]):
                        collusion_rings.append({
                            "federations": list(pair),
                            "mutual_suspicion": True,
                            "fed_a_to_b": analyses[fed_id]["partner_analysis"].get(partner),
                            "fed_b_to_a": analyses[partner]["partner_analysis"].get(fed_id),
                        })

        return {
            "time_window_days": time_window_days,
            "federations_analyzed": len(federation_ids),
            "individual_analyses": analyses,
            "collusion_rings": collusion_rings,
            "total_suspicious_pairs": len(collusion_rings),
            "overall_health": "healthy" if len(collusion_rings) == 0 else "warning",
        }

    def check_approval_for_collusion(
        self,
        proposal_id: str,
        approving_federation_id: str,
    ) -> Dict:
        """
        Check if approving a proposal would contribute to suspicious patterns.

        Track BJ: Pre-approval collusion check.

        Args:
            proposal_id: Proposal being approved
            approving_federation_id: Federation about to approve

        Returns:
            Dict with collusion risk assessment
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT proposing_federation_id FROM cross_federation_proposals WHERE proposal_id = ?",
                (proposal_id,)
            ).fetchone()

        if not row:
            return {"error": "Proposal not found"}

        proposer = row["proposing_federation_id"]

        if proposer == approving_federation_id:
            return {
                "proposal_id": proposal_id,
                "approving_federation": approving_federation_id,
                "proposing_federation": proposer,
                "collusion_risk": "none",
                "reason": "Self-approval (proposer)",
            }

        # Analyze current reciprocity with proposer
        analysis = self.analyze_federation_reciprocity(approving_federation_id)
        partner_data = analysis["partner_analysis"].get(proposer)

        if not partner_data:
            return {
                "proposal_id": proposal_id,
                "approving_federation": approving_federation_id,
                "proposing_federation": proposer,
                "collusion_risk": "low",
                "reason": "Insufficient history to assess",
                "current_reciprocity": None,
            }

        # Calculate what reciprocity would be after this approval
        new_given = partner_data["approvals_given"] + 1
        new_received = partner_data["approvals_received"]
        new_reciprocity = (
            min(new_given, new_received) / max(new_given, new_received)
            if max(new_given, new_received) > 0 else 0.0
        )

        risk_level = "low"
        if new_reciprocity > self.MAX_FEDERATION_RECIPROCITY:
            risk_level = "high"
        elif new_reciprocity > self.MAX_FEDERATION_RECIPROCITY - 0.1:
            risk_level = "medium"

        return {
            "proposal_id": proposal_id,
            "approving_federation": approving_federation_id,
            "proposing_federation": proposer,
            "current_reciprocity": partner_data["reciprocity_ratio"],
            "projected_reciprocity": new_reciprocity,
            "collusion_risk": risk_level,
            "threshold": self.MAX_FEDERATION_RECIPROCITY,
            "already_suspicious": partner_data["suspicious"],
            "would_become_suspicious": new_reciprocity > self.MAX_FEDERATION_RECIPROCITY,
        }


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Multi-Federation Registry - Self Test")
    print("=" * 60)

    import tempfile

    # Create test registry
    db_path = Path(tempfile.mkdtemp()) / "multi_fed_test.db"
    registry = MultiFederationRegistry(db_path=db_path)

    # Register federations
    fed_a = registry.register_federation("fed:acme", "ACME Corporation")
    fed_b = registry.register_federation("fed:globex", "Globex Industries")
    fed_c = registry.register_federation("fed:initech", "Initech Solutions")

    print(f"\nRegistered federations:")
    print(f"  {fed_a.federation_id}: {fed_a.name}")
    print(f"  {fed_b.federation_id}: {fed_b.name}")
    print(f"  {fed_c.federation_id}: {fed_c.name}")

    # Establish trust relationships
    trust_ab = registry.establish_trust(
        "fed:acme", "fed:globex",
        FederationRelationship.ALLIED,
        initial_trust=0.7,
    )
    trust_ac = registry.establish_trust(
        "fed:acme", "fed:initech",
        FederationRelationship.PEER,
        initial_trust=0.5,
    )

    print(f"\nTrust relationships:")
    print(f"  ACME -> Globex: {trust_ab.relationship.value} (trust={trust_ab.trust_score})")
    print(f"  ACME -> Initech: {trust_ac.relationship.value} (trust={trust_ac.trust_score})")

    # Find eligible witnesses for ACME
    eligible = registry.find_eligible_witness_federations("fed:acme")
    print(f"\nEligible witnesses for ACME:")
    for fed_id, trust in eligible:
        print(f"  {fed_id}: trust={trust}")

    # Create cross-federation proposal
    proposal = registry.create_cross_federation_proposal(
        "fed:acme",
        "team:acme:engineering",
        ["fed:acme", "fed:globex"],
        "resource_sharing",
        "Share computing resources between ACME and Globex",
    )
    print(f"\nCreated proposal: {proposal.proposal_id}")
    print(f"  Affected federations: {proposal.affected_federation_ids}")

    # Approve from both federations
    registry.approve_from_federation(
        proposal.proposal_id,
        "fed:acme",
        ["team:acme:engineering", "team:acme:legal"],
    )
    result = registry.approve_from_federation(
        proposal.proposal_id,
        "fed:globex",
        ["team:globex:ops"],
    )
    print(f"\nApproval status: {result['new_status']}")

    # Add external witness from Initech (not affected by proposal)
    witness_result = registry.add_external_witness(
        proposal.proposal_id,
        "fed:initech",
        "team:initech:compliance",
    )
    print(f"External witness added: {witness_result}")

    # Check requirements
    reqs = registry.check_proposal_requirements(proposal.proposal_id)
    print(f"\nRequirements check:")
    print(f"  All requirements met: {reqs['all_requirements_met']}")
    print(f"  Missing approvals: {reqs['missing_approvals']}")
    print(f"  External witnesses: {reqs['external_witnesses']}")

    print("\n" + "=" * 60)
    print("Self-test complete.")
