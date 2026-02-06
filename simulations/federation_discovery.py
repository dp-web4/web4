"""
Federation Discovery Protocol

Track BY: Protocol for federations to find and connect with each other.

Key concepts:
1. Announcement: Federations broadcast their existence and capabilities
2. Discovery: Federations can search for potential partners
3. Handshake: Mutual verification before establishing trust
4. Categories: Federations can categorize by domain/interest
5. Reputation Gates: Minimum reputation required to connect

This creates a decentralized discovery network where federations can
organically find compatible partners while protecting against spam
and malicious federations.
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from enum import Enum

from .multi_federation import (
    MultiFederationRegistry,
    FederationProfile,
    FederationRelationship,
    InterFederationTrust,
)


class DiscoveryCategory(Enum):
    """Categories for federation discovery matching."""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    GOVERNANCE = "governance"
    RESEARCH = "research"
    INFRASTRUCTURE = "infrastructure"
    COMMUNITY = "community"
    COMMERCE = "commerce"
    CREATIVE = "creative"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    OTHER = "other"


class AnnouncementStatus(Enum):
    """Status of a federation announcement."""
    ACTIVE = "active"           # Currently seeking connections
    PAUSED = "paused"           # Temporarily not seeking
    WITHDRAWN = "withdrawn"     # Permanently removed
    EXPIRED = "expired"         # Past validity period


class HandshakeStatus(Enum):
    """Status of a connection handshake."""
    PENDING = "pending"         # Initiated, waiting for response
    ACCEPTED = "accepted"       # Both parties agreed
    REJECTED = "rejected"       # One party declined
    EXPIRED = "expired"         # Timed out without response
    CANCELLED = "cancelled"     # Initiator cancelled


@dataclass
class FederationAnnouncement:
    """A federation's public announcement for discovery."""
    announcement_id: str
    federation_id: str

    # Public profile
    display_name: str
    description: str
    categories: List[DiscoveryCategory]

    # Requirements for connection
    min_reputation: float = 0.3     # Minimum reputation to connect
    min_presence: float = 0.2       # Minimum presence score
    require_mutual_witness: bool = True  # Require witness capability

    # Connection preferences
    max_connections: int = 100      # Maximum federation connections
    current_connections: int = 0
    preferred_categories: List[DiscoveryCategory] = field(default_factory=list)

    # Metadata
    created_at: str = ""
    expires_at: str = ""            # When announcement becomes stale
    status: AnnouncementStatus = AnnouncementStatus.ACTIVE

    # Verification
    verification_hash: str = ""     # Hash of announcement for integrity
    last_verified_at: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["categories"] = [c.value for c in self.categories]
        d["preferred_categories"] = [c.value for c in self.preferred_categories]
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'FederationAnnouncement':
        data = dict(data)
        data["categories"] = [DiscoveryCategory(c) for c in data["categories"]]
        data["preferred_categories"] = [DiscoveryCategory(c) for c in data.get("preferred_categories", [])]
        data["status"] = AnnouncementStatus(data["status"])
        return cls(**data)


@dataclass
class ConnectionHandshake:
    """A handshake request between two federations."""
    handshake_id: str
    initiator_federation_id: str
    target_federation_id: str

    # Proposed relationship
    proposed_relationship: FederationRelationship = FederationRelationship.PEER
    proposed_trust_level: float = 0.5

    # Context
    message: str = ""                # Why the initiator wants to connect
    categories_match: List[str] = field(default_factory=list)

    # Status tracking
    status: HandshakeStatus = HandshakeStatus.PENDING
    created_at: str = ""
    responded_at: str = ""
    expires_at: str = ""

    # Response
    response_message: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["proposed_relationship"] = self.proposed_relationship.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'ConnectionHandshake':
        data = dict(data)
        data["proposed_relationship"] = FederationRelationship(data["proposed_relationship"])
        data["status"] = HandshakeStatus(data["status"])
        return cls(**data)


class FederationDiscovery:
    """
    Federation discovery and connection protocol.

    Track BY: Protocol for federations to find each other.
    Track CA: Integrated with ReputationAggregator for dynamic reputation.

    Features:
    - Publish announcements with capabilities/requirements
    - Search for federations by category/reputation
    - Handshake protocol for secure connection
    - Reputation-gated discovery (spam protection)
    - Category-based matching
    - Dynamic reputation from ReputationAggregator (Track CA)
    """

    def __init__(
        self,
        registry: MultiFederationRegistry,
        db_path: Optional[Path] = None,
        reputation_aggregator: Optional['ReputationAggregator'] = None,
    ):
        """
        Initialize discovery protocol.

        Args:
            registry: Multi-federation registry for trust operations
            db_path: Path to SQLite database (None for in-memory)
            reputation_aggregator: Optional aggregator for dynamic reputation (Track CA)
        """
        self.registry = registry
        self._reputation_aggregator = reputation_aggregator

        if db_path:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.db_path = ":memory:"

        self._init_db()

    def _get_reputation(self, federation_id: str) -> float:
        """
        Get reputation for a federation.

        Track CA: Uses ReputationAggregator if available, otherwise static score.

        Args:
            federation_id: Federation to get reputation for

        Returns:
            Reputation score (0-1)
        """
        if self._reputation_aggregator:
            # Use dynamic calculated reputation
            score = self._reputation_aggregator.calculate_reputation(federation_id)
            return score.global_reputation

        # Fallback to static reputation_score
        fed = self.registry.get_federation(federation_id)
        return fed.reputation_score if fed else 0.5

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Announcements table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS announcements (
                    announcement_id TEXT PRIMARY KEY,
                    federation_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    categories TEXT NOT NULL,
                    min_reputation REAL DEFAULT 0.3,
                    min_presence REAL DEFAULT 0.2,
                    require_mutual_witness INTEGER DEFAULT 1,
                    max_connections INTEGER DEFAULT 100,
                    current_connections INTEGER DEFAULT 0,
                    preferred_categories TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    verification_hash TEXT NOT NULL,
                    last_verified_at TEXT NOT NULL,
                    UNIQUE(federation_id)
                )
            """)

            # Handshakes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS handshakes (
                    handshake_id TEXT PRIMARY KEY,
                    initiator_federation_id TEXT NOT NULL,
                    target_federation_id TEXT NOT NULL,
                    proposed_relationship TEXT NOT NULL,
                    proposed_trust_level REAL DEFAULT 0.5,
                    message TEXT DEFAULT '',
                    categories_match TEXT DEFAULT '[]',
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    responded_at TEXT DEFAULT '',
                    expires_at TEXT NOT NULL,
                    response_message TEXT DEFAULT ''
                )
            """)

            # Indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ann_status
                ON announcements(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ann_categories
                ON announcements(categories)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_hs_target
                ON handshakes(target_federation_id, status)
            """)

            conn.commit()
        finally:
            conn.close()

    def _compute_verification_hash(self, announcement: FederationAnnouncement) -> str:
        """Compute verification hash for announcement integrity."""
        data = {
            "federation_id": announcement.federation_id,
            "display_name": announcement.display_name,
            "description": announcement.description,
            "categories": [c.value for c in announcement.categories],
            "min_reputation": announcement.min_reputation,
            "min_presence": announcement.min_presence,
            "created_at": announcement.created_at,
        }
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def publish_announcement(
        self,
        federation_id: str,
        display_name: str,
        description: str,
        categories: List[DiscoveryCategory],
        min_reputation: float = 0.3,
        min_presence: float = 0.2,
        require_mutual_witness: bool = True,
        max_connections: int = 100,
        preferred_categories: Optional[List[DiscoveryCategory]] = None,
        validity_days: int = 30,
    ) -> FederationAnnouncement:
        """
        Publish a discovery announcement for a federation.

        Args:
            federation_id: The announcing federation
            display_name: Public display name
            description: Description of the federation
            categories: Categories this federation belongs to
            min_reputation: Minimum reputation to connect
            min_presence: Minimum presence score required
            require_mutual_witness: Require witness capability
            max_connections: Maximum connections allowed
            preferred_categories: Preferred partner categories
            validity_days: How long announcement is valid

        Returns:
            FederationAnnouncement

        Raises:
            ValueError: If federation not registered
        """
        import uuid

        # Verify federation exists
        fed = self.registry.get_federation(federation_id)
        if not fed:
            raise ValueError(f"Federation {federation_id} not registered")

        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=validity_days)

        announcement = FederationAnnouncement(
            announcement_id=f"ann:{uuid.uuid4().hex[:12]}",
            federation_id=federation_id,
            display_name=display_name,
            description=description,
            categories=categories,
            min_reputation=min_reputation,
            min_presence=min_presence,
            require_mutual_witness=require_mutual_witness,
            max_connections=max_connections,
            current_connections=0,
            preferred_categories=preferred_categories or [],
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            status=AnnouncementStatus.ACTIVE,
            last_verified_at=now.isoformat(),
        )

        # Compute verification hash
        announcement.verification_hash = self._compute_verification_hash(announcement)

        # Store (replace existing if any)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO announcements
                (announcement_id, federation_id, display_name, description, categories,
                 min_reputation, min_presence, require_mutual_witness, max_connections,
                 current_connections, preferred_categories, created_at, expires_at,
                 status, verification_hash, last_verified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                announcement.announcement_id,
                announcement.federation_id,
                announcement.display_name,
                announcement.description,
                json.dumps([c.value for c in announcement.categories]),
                announcement.min_reputation,
                announcement.min_presence,
                1 if announcement.require_mutual_witness else 0,
                announcement.max_connections,
                announcement.current_connections,
                json.dumps([c.value for c in announcement.preferred_categories]),
                announcement.created_at,
                announcement.expires_at,
                announcement.status.value,
                announcement.verification_hash,
                announcement.last_verified_at,
            ))
            conn.commit()
        finally:
            conn.close()

        return announcement

    def get_announcement(self, federation_id: str) -> Optional[FederationAnnouncement]:
        """Get a federation's announcement."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM announcements WHERE federation_id = ?
            """, (federation_id,)).fetchone()

            if not row:
                return None

            return self._row_to_announcement(row)
        finally:
            conn.close()

    def _row_to_announcement(self, row) -> FederationAnnouncement:
        """Convert database row to FederationAnnouncement."""
        return FederationAnnouncement(
            announcement_id=row["announcement_id"],
            federation_id=row["federation_id"],
            display_name=row["display_name"],
            description=row["description"],
            categories=[DiscoveryCategory(c) for c in json.loads(row["categories"])],
            min_reputation=row["min_reputation"],
            min_presence=row["min_presence"],
            require_mutual_witness=bool(row["require_mutual_witness"]),
            max_connections=row["max_connections"],
            current_connections=row["current_connections"],
            preferred_categories=[DiscoveryCategory(c) for c in json.loads(row["preferred_categories"])],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            status=AnnouncementStatus(row["status"]),
            verification_hash=row["verification_hash"],
            last_verified_at=row["last_verified_at"],
        )

    def discover_federations(
        self,
        seeker_federation_id: str,
        categories: Optional[List[DiscoveryCategory]] = None,
        min_reputation: float = 0.0,
        exclude_connected: bool = True,
        limit: int = 20,
    ) -> List[Dict]:
        """
        Discover federations matching criteria.

        Args:
            seeker_federation_id: Federation doing the search
            categories: Filter by categories (None = all)
            min_reputation: Minimum reputation score
            exclude_connected: Exclude already connected federations
            limit: Maximum results

        Returns:
            List of discovery results with match scores
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row

            # Get seeker's info
            seeker_fed = self.registry.get_federation(seeker_federation_id)
            if not seeker_fed:
                return []

            # Track CA: Use dynamic reputation if aggregator available
            seeker_reputation = self._get_reputation(seeker_federation_id)

            # Get already connected federations
            connected = set()
            if exclude_connected:
                relationships = self.registry.get_all_relationships()
                for rel in relationships:
                    if rel.source_federation_id == seeker_federation_id:
                        connected.add(rel.target_federation_id)
                    elif rel.target_federation_id == seeker_federation_id:
                        connected.add(rel.source_federation_id)

            # Query active announcements
            now = datetime.now(timezone.utc).isoformat()
            rows = conn.execute("""
                SELECT * FROM announcements
                WHERE status = 'active'
                  AND expires_at > ?
                  AND federation_id != ?
                ORDER BY created_at DESC
            """, (now, seeker_federation_id)).fetchall()

            results = []
            for row in rows:
                announcement = self._row_to_announcement(row)

                # Skip if already connected
                if announcement.federation_id in connected:
                    continue

                # Check if seeker meets announcement requirements
                if seeker_reputation < announcement.min_reputation:
                    continue

                # Check if at connection limit
                if announcement.current_connections >= announcement.max_connections:
                    continue

                # Category filtering
                if categories:
                    category_match = bool(set(categories) & set(announcement.categories))
                    if not category_match:
                        continue

                # Get target federation's reputation (Track CA: dynamic)
                target_fed = self.registry.get_federation(announcement.federation_id)
                if not target_fed:
                    continue

                target_reputation = self._get_reputation(announcement.federation_id)
                if target_reputation < min_reputation:
                    continue

                # Calculate match score
                match_score = self._calculate_match_score(
                    seeker_federation_id,
                    announcement,
                    target_fed,
                    categories,
                    target_reputation,  # Track CA: pass calculated reputation
                )

                results.append({
                    "federation_id": announcement.federation_id,
                    "display_name": announcement.display_name,
                    "description": announcement.description,
                    "categories": [c.value for c in announcement.categories],
                    "reputation": target_reputation,  # Track CA: use calculated reputation
                    "match_score": match_score,
                    "requirements": {
                        "min_reputation": announcement.min_reputation,
                        "min_presence": announcement.min_presence,
                        "require_mutual_witness": announcement.require_mutual_witness,
                    },
                    "seeker_qualifies": seeker_reputation >= announcement.min_reputation,
                })

            # Sort by match score
            results.sort(key=lambda x: x["match_score"], reverse=True)

            return results[:limit]
        finally:
            conn.close()

    def _calculate_match_score(
        self,
        seeker_id: str,
        announcement: FederationAnnouncement,
        target_fed: FederationProfile,
        search_categories: Optional[List[DiscoveryCategory]],
        target_reputation: Optional[float] = None,
    ) -> float:
        """
        Calculate how well a federation matches the seeker's interests.

        Track CA: Now accepts pre-calculated reputation for efficiency.
        """
        score = 0.0

        # Base reputation component (0-0.4)
        # Track CA: Use provided reputation or fallback to profile
        rep = target_reputation if target_reputation is not None else target_fed.reputation_score
        score += min(rep * 0.4, 0.4)

        # Category match (0-0.3)
        if search_categories:
            matching = len(set(search_categories) & set(announcement.categories))
            total = len(search_categories)
            score += (matching / total) * 0.3 if total > 0 else 0
        else:
            # No specific categories = partial match
            score += 0.15

        # Preferred category bonus (0-0.15)
        if announcement.preferred_categories:
            seeker_ann = self.get_announcement(seeker_id)
            if seeker_ann:
                preferred_match = bool(
                    set(announcement.preferred_categories) & set(seeker_ann.categories)
                )
                if preferred_match:
                    score += 0.15

        # Activity bonus (0-0.15)
        if target_fed.proposal_count > 0:
            score += min(target_fed.success_rate * 0.15, 0.15)

        return round(score, 3)

    def initiate_handshake(
        self,
        initiator_federation_id: str,
        target_federation_id: str,
        message: str = "",
        proposed_relationship: FederationRelationship = FederationRelationship.PEER,
        proposed_trust_level: float = 0.5,
        validity_hours: int = 72,
    ) -> ConnectionHandshake:
        """
        Initiate a connection handshake with another federation.

        Args:
            initiator_federation_id: Federation initiating connection
            target_federation_id: Federation to connect with
            message: Introduction message
            proposed_relationship: Type of relationship proposed
            proposed_trust_level: Initial trust level proposed
            validity_hours: How long handshake is valid

        Returns:
            ConnectionHandshake

        Raises:
            ValueError: If requirements not met
        """
        import uuid

        # Verify both federations exist
        initiator = self.registry.get_federation(initiator_federation_id)
        target = self.registry.get_federation(target_federation_id)

        if not initiator:
            raise ValueError(f"Initiator {initiator_federation_id} not registered")
        if not target:
            raise ValueError(f"Target {target_federation_id} not registered")

        # Check target's announcement requirements
        # Track CA: Use dynamic reputation if aggregator available
        initiator_reputation = self._get_reputation(initiator_federation_id)

        target_ann = self.get_announcement(target_federation_id)
        if target_ann:
            if initiator_reputation < target_ann.min_reputation:
                raise ValueError(
                    f"Initiator reputation {initiator_reputation:.2f} below "
                    f"target minimum {target_ann.min_reputation:.2f}"
                )
            if target_ann.current_connections >= target_ann.max_connections:
                raise ValueError("Target has reached maximum connections")

        # Check for existing pending handshake
        existing = self._get_pending_handshake(initiator_federation_id, target_federation_id)
        if existing:
            raise ValueError("Handshake already pending between these federations")

        # Compute category matches
        initiator_ann = self.get_announcement(initiator_federation_id)
        categories_match = []
        if initiator_ann and target_ann:
            matches = set(initiator_ann.categories) & set(target_ann.categories)
            categories_match = [c.value for c in matches]

        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=validity_hours)

        handshake = ConnectionHandshake(
            handshake_id=f"hs:{uuid.uuid4().hex[:12]}",
            initiator_federation_id=initiator_federation_id,
            target_federation_id=target_federation_id,
            proposed_relationship=proposed_relationship,
            proposed_trust_level=proposed_trust_level,
            message=message,
            categories_match=categories_match,
            status=HandshakeStatus.PENDING,
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
        )

        # Store
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO handshakes
                (handshake_id, initiator_federation_id, target_federation_id,
                 proposed_relationship, proposed_trust_level, message,
                 categories_match, status, created_at, responded_at, expires_at,
                 response_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                handshake.handshake_id,
                handshake.initiator_federation_id,
                handshake.target_federation_id,
                handshake.proposed_relationship.value,
                handshake.proposed_trust_level,
                handshake.message,
                json.dumps(handshake.categories_match),
                handshake.status.value,
                handshake.created_at,
                handshake.responded_at,
                handshake.expires_at,
                handshake.response_message,
            ))
            conn.commit()
        finally:
            conn.close()

        return handshake

    def _get_pending_handshake(
        self,
        fed1: str,
        fed2: str,
    ) -> Optional[ConnectionHandshake]:
        """Check for existing pending handshake between federations."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM handshakes
                WHERE status = 'pending'
                  AND ((initiator_federation_id = ? AND target_federation_id = ?)
                    OR (initiator_federation_id = ? AND target_federation_id = ?))
            """, (fed1, fed2, fed2, fed1)).fetchone()

            if row:
                return self._row_to_handshake(row)
            return None
        finally:
            conn.close()

    def _row_to_handshake(self, row) -> ConnectionHandshake:
        """Convert database row to ConnectionHandshake."""
        return ConnectionHandshake(
            handshake_id=row["handshake_id"],
            initiator_federation_id=row["initiator_federation_id"],
            target_federation_id=row["target_federation_id"],
            proposed_relationship=FederationRelationship(row["proposed_relationship"]),
            proposed_trust_level=row["proposed_trust_level"],
            message=row["message"],
            categories_match=json.loads(row["categories_match"]),
            status=HandshakeStatus(row["status"]),
            created_at=row["created_at"],
            responded_at=row["responded_at"],
            expires_at=row["expires_at"],
            response_message=row["response_message"],
        )

    def get_pending_handshakes(
        self,
        federation_id: str,
        direction: str = "incoming",
    ) -> List[ConnectionHandshake]:
        """
        Get pending handshakes for a federation.

        Args:
            federation_id: The federation
            direction: "incoming", "outgoing", or "both"

        Returns:
            List of pending handshakes
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            now = datetime.now(timezone.utc).isoformat()

            if direction == "incoming":
                rows = conn.execute("""
                    SELECT * FROM handshakes
                    WHERE target_federation_id = ?
                      AND status = 'pending'
                      AND expires_at > ?
                    ORDER BY created_at DESC
                """, (federation_id, now)).fetchall()
            elif direction == "outgoing":
                rows = conn.execute("""
                    SELECT * FROM handshakes
                    WHERE initiator_federation_id = ?
                      AND status = 'pending'
                      AND expires_at > ?
                    ORDER BY created_at DESC
                """, (federation_id, now)).fetchall()
            else:  # both
                rows = conn.execute("""
                    SELECT * FROM handshakes
                    WHERE (target_federation_id = ? OR initiator_federation_id = ?)
                      AND status = 'pending'
                      AND expires_at > ?
                    ORDER BY created_at DESC
                """, (federation_id, federation_id, now)).fetchall()

            return [self._row_to_handshake(row) for row in rows]
        finally:
            conn.close()

    def respond_to_handshake(
        self,
        handshake_id: str,
        accept: bool,
        response_message: str = "",
    ) -> ConnectionHandshake:
        """
        Respond to a connection handshake.

        Args:
            handshake_id: The handshake to respond to
            accept: Whether to accept the connection
            response_message: Optional response message

        Returns:
            Updated ConnectionHandshake

        Raises:
            ValueError: If handshake not found or already responded
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM handshakes WHERE handshake_id = ?
            """, (handshake_id,)).fetchone()

            if not row:
                raise ValueError(f"Handshake {handshake_id} not found")

            handshake = self._row_to_handshake(row)

            if handshake.status != HandshakeStatus.PENDING:
                raise ValueError(f"Handshake already has status: {handshake.status.value}")

            now = datetime.now(timezone.utc).isoformat()
            if handshake.expires_at < now:
                raise ValueError("Handshake has expired")

            # Update status
            new_status = HandshakeStatus.ACCEPTED if accept else HandshakeStatus.REJECTED

            conn.execute("""
                UPDATE handshakes
                SET status = ?, responded_at = ?, response_message = ?
                WHERE handshake_id = ?
            """, (new_status.value, now, response_message, handshake_id))
            conn.commit()

            handshake.status = new_status
            handshake.responded_at = now
            handshake.response_message = response_message

            # If accepted, establish trust relationship
            if accept:
                self.registry.establish_trust(
                    handshake.initiator_federation_id,
                    handshake.target_federation_id,
                    handshake.proposed_relationship,
                    handshake.proposed_trust_level,
                )

                # Also establish reverse trust for PEER relationship
                if handshake.proposed_relationship == FederationRelationship.PEER:
                    self.registry.establish_trust(
                        handshake.target_federation_id,
                        handshake.initiator_federation_id,
                        FederationRelationship.PEER,
                        handshake.proposed_trust_level,
                    )

                # Update connection counts
                self._increment_connection_count(handshake.initiator_federation_id)
                self._increment_connection_count(handshake.target_federation_id)

            return handshake
        finally:
            conn.close()

    def _increment_connection_count(self, federation_id: str):
        """Increment the connection count in announcement."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                UPDATE announcements
                SET current_connections = current_connections + 1
                WHERE federation_id = ?
            """, (federation_id,))
            conn.commit()
        finally:
            conn.close()

    def get_discovery_statistics(self) -> Dict:
        """Get overall discovery network statistics."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            now = datetime.now(timezone.utc).isoformat()

            # Active announcements
            active_count = conn.execute("""
                SELECT COUNT(*) as count FROM announcements
                WHERE status = 'active' AND expires_at > ?
            """, (now,)).fetchone()["count"]

            # Total announcements
            total_count = conn.execute("""
                SELECT COUNT(*) as count FROM announcements
            """).fetchone()["count"]

            # Category distribution
            rows = conn.execute("""
                SELECT categories FROM announcements
                WHERE status = 'active' AND expires_at > ?
            """, (now,)).fetchall()

            category_counts = {}
            for row in rows:
                cats = json.loads(row["categories"])
                for cat in cats:
                    category_counts[cat] = category_counts.get(cat, 0) + 1

            # Handshake statistics
            hs_stats = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM handshakes
                GROUP BY status
            """).fetchall()

            handshake_by_status = {row["status"]: row["count"] for row in hs_stats}

            # Success rate
            accepted = handshake_by_status.get("accepted", 0)
            rejected = handshake_by_status.get("rejected", 0)
            total_responses = accepted + rejected
            success_rate = accepted / total_responses if total_responses > 0 else 0

            return {
                "active_announcements": active_count,
                "total_announcements": total_count,
                "category_distribution": category_counts,
                "handshakes_by_status": handshake_by_status,
                "connection_success_rate": round(success_rate, 3),
                "timestamp": now,
            }
        finally:
            conn.close()

    def cleanup_expired(self) -> Dict:
        """Clean up expired announcements and handshakes."""
        conn = sqlite3.connect(self.db_path)
        try:
            now = datetime.now(timezone.utc).isoformat()

            # Mark expired announcements
            cursor = conn.execute("""
                UPDATE announcements
                SET status = 'expired'
                WHERE status = 'active' AND expires_at <= ?
            """, (now,))
            expired_announcements = cursor.rowcount

            # Mark expired handshakes
            cursor = conn.execute("""
                UPDATE handshakes
                SET status = 'expired'
                WHERE status = 'pending' AND expires_at <= ?
            """, (now,))
            expired_handshakes = cursor.rowcount

            conn.commit()

            return {
                "expired_announcements": expired_announcements,
                "expired_handshakes": expired_handshakes,
                "cleanup_timestamp": now,
            }
        finally:
            conn.close()


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Federation Discovery Protocol - Self Test")
    print("=" * 60)

    import tempfile

    tmp_dir = Path(tempfile.mkdtemp())

    # Create multi-federation registry
    registry = MultiFederationRegistry(db_path=tmp_dir / "federations.db")

    # Create discovery protocol
    discovery = FederationDiscovery(registry, db_path=tmp_dir / "discovery.db")

    # Register some federations
    print("\n1. Register federations:")
    fed_alpha = registry.register_federation("fed:alpha", "Alpha Tech")
    fed_beta = registry.register_federation("fed:beta", "Beta Finance")
    fed_gamma = registry.register_federation("fed:gamma", "Gamma Research")
    print(f"   Registered: {fed_alpha.federation_id}, {fed_beta.federation_id}, {fed_gamma.federation_id}")

    # Publish announcements
    print("\n2. Publish discovery announcements:")
    ann_alpha = discovery.publish_announcement(
        "fed:alpha",
        "Alpha Technology Federation",
        "Open source technology collaboration",
        [DiscoveryCategory.TECHNOLOGY, DiscoveryCategory.RESEARCH],
        min_reputation=0.3,
        preferred_categories=[DiscoveryCategory.INFRASTRUCTURE],
    )
    print(f"   Alpha: {ann_alpha.announcement_id}")

    ann_beta = discovery.publish_announcement(
        "fed:beta",
        "Beta Finance Network",
        "Decentralized finance federation",
        [DiscoveryCategory.FINANCE, DiscoveryCategory.TECHNOLOGY],
        min_reputation=0.4,
    )
    print(f"   Beta: {ann_beta.announcement_id}")

    ann_gamma = discovery.publish_announcement(
        "fed:gamma",
        "Gamma Research Collective",
        "Academic and research collaboration",
        [DiscoveryCategory.RESEARCH, DiscoveryCategory.EDUCATION],
        min_reputation=0.2,
    )
    print(f"   Gamma: {ann_gamma.announcement_id}")

    # Discover federations
    print("\n3. Discover federations (from Alpha's perspective):")
    results = discovery.discover_federations(
        "fed:alpha",
        categories=[DiscoveryCategory.TECHNOLOGY],
    )
    for r in results:
        print(f"   - {r['display_name']}: match={r['match_score']:.3f}")

    # Initiate handshake
    print("\n4. Initiate handshake (Alpha -> Beta):")
    handshake = discovery.initiate_handshake(
        "fed:alpha",
        "fed:beta",
        message="Would like to collaborate on tech finance projects",
    )
    print(f"   Handshake ID: {handshake.handshake_id}")
    print(f"   Status: {handshake.status.value}")

    # Check pending handshakes
    print("\n5. Check pending handshakes for Beta:")
    pending = discovery.get_pending_handshakes("fed:beta", "incoming")
    print(f"   Found {len(pending)} pending handshake(s)")

    # Accept handshake
    print("\n6. Beta accepts handshake:")
    accepted = discovery.respond_to_handshake(
        handshake.handshake_id,
        accept=True,
        response_message="Looking forward to collaboration!",
    )
    print(f"   New status: {accepted.status.value}")

    # Verify trust established
    print("\n7. Verify trust relationship established:")
    relationships = registry.get_all_relationships()
    for rel in relationships:
        print(f"   {rel.source_federation_id} -> {rel.target_federation_id}: "
              f"{rel.relationship.value}, trust={rel.trust_score}")

    # Statistics
    print("\n8. Discovery statistics:")
    stats = discovery.get_discovery_statistics()
    print(f"   Active announcements: {stats['active_announcements']}")
    print(f"   Connection success rate: {stats['connection_success_rate']:.1%}")
    print(f"   Categories: {stats['category_distribution']}")

    print("\n" + "=" * 60)
    print("Self-test complete.")
