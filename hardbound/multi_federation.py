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
                    UNIQUE(source_federation_id, target_federation_id)
                )
            """)

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

        Args:
            source_federation_id: Federation establishing the trust
            target_federation_id: Federation being trusted
            relationship: Type of relationship
            initial_trust: Initial trust score (0-1)
            witness_allowed: Whether target can witness for source

        Returns:
            InterFederationTrust record
        """
        now = datetime.now(timezone.utc).isoformat()

        trust = InterFederationTrust(
            source_federation_id=source_federation_id,
            target_federation_id=target_federation_id,
            relationship=relationship,
            established_at=now,
            trust_score=initial_trust,
            witness_allowed=witness_allowed,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO inter_federation_trust
                (source_federation_id, target_federation_id, relationship,
                 established_at, trust_score, witness_allowed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                trust.source_federation_id,
                trust.target_federation_id,
                trust.relationship.value,
                trust.established_at,
                trust.trust_score,
                1 if trust.witness_allowed else 0,
            ))

        return trust

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

            return InterFederationTrust(
                source_federation_id=row["source_federation_id"],
                target_federation_id=row["target_federation_id"],
                relationship=FederationRelationship(row["relationship"]),
                established_at=row["established_at"],
                trust_score=row["trust_score"],
                witness_allowed=bool(row["witness_allowed"]),
                last_interaction=row["last_interaction"] or "",
            )

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
