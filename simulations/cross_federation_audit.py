"""
Cross-Federation Audit Trail

Track CC: Audit trail spanning multiple federations.

Key concepts:
1. Unified audit view: See actions across all federations
2. Cross-federation events: Track actions affecting multiple federations
3. Audit synchronization: Ensure consistency across federation boundaries
4. Compliance export: Export unified audit for regulatory compliance

This extends governance_audit.py to support multi-federation scenarios where
actions in one federation affect others (e.g., cross-federation proposals,
trust establishment, witness events).
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from enum import Enum

from .governance_audit import (
    GovernanceAuditTrail, AuditEventType, AuditRecord
)


class CrossFederationEventType(Enum):
    """Events that span multiple federations."""
    # Cross-federation proposals
    CROSS_FED_PROPOSAL_CREATED = "cross_fed_proposal_created"
    CROSS_FED_PROPOSAL_VOTED = "cross_fed_proposal_voted"
    CROSS_FED_PROPOSAL_APPROVED = "cross_fed_proposal_approved"
    CROSS_FED_PROPOSAL_REJECTED = "cross_fed_proposal_rejected"
    CROSS_FED_PROPOSAL_EXECUTED = "cross_fed_proposal_executed"

    # Inter-federation trust
    INTER_FED_TRUST_ESTABLISHED = "inter_fed_trust_established"
    INTER_FED_TRUST_UPDATED = "inter_fed_trust_updated"
    INTER_FED_TRUST_REVOKED = "inter_fed_trust_revoked"

    # Discovery and connection
    DISCOVERY_HANDSHAKE_INITIATED = "discovery_handshake_initiated"
    DISCOVERY_HANDSHAKE_ACCEPTED = "discovery_handshake_accepted"
    DISCOVERY_HANDSHAKE_REJECTED = "discovery_handshake_rejected"

    # Witness events
    CROSS_FED_WITNESS_PROVIDED = "cross_fed_witness_provided"
    CROSS_FED_WITNESS_CHALLENGED = "cross_fed_witness_challenged"

    # Reputation events
    REPUTATION_ENDORSEMENT = "reputation_endorsement"
    REPUTATION_DISPUTE = "reputation_dispute"


@dataclass
class CrossFederationAuditRecord:
    """An audit record that spans multiple federations."""
    record_id: str
    event_type: CrossFederationEventType
    timestamp: str

    # Primary actors
    source_federation_id: str  # Initiating federation
    target_federation_ids: List[str]  # Affected federations

    # Event context
    actor_lct: str  # Who initiated the action
    event_data: Dict = field(default_factory=dict)

    # Cross-references
    related_proposal_id: str = ""
    related_trust_id: str = ""
    related_handshake_id: str = ""

    # Local audit references
    local_audit_ids: Dict[str, str] = field(default_factory=dict)  # fed_id -> audit_record_id

    # Integrity
    previous_hash: str = ""
    record_hash: str = ""

    # Status
    acknowledged_by: List[str] = field(default_factory=list)  # Federations that acknowledged

    def to_dict(self) -> dict:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'CrossFederationAuditRecord':
        data = dict(data)
        data["event_type"] = CrossFederationEventType(data["event_type"])
        return cls(**data)


class CrossFederationAudit:
    """
    Unified audit trail across multiple federations.

    Track CC: Cross-Federation Audit

    Features:
    - Record events that span federation boundaries
    - Maintain cross-references to local audit trails
    - Provide unified compliance export
    - Track acknowledgment status across federations
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize cross-federation audit.

        Args:
            db_path: Path to SQLite database (None for in-memory)
        """
        if db_path:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.db_path = ":memory:"

        self._init_db()
        self._last_hash = self._get_last_hash()

        # Registry of local audit trails
        self._local_audits: Dict[str, GovernanceAuditTrail] = {}

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cross_fed_audit (
                    record_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source_federation_id TEXT NOT NULL,
                    target_federation_ids TEXT NOT NULL,
                    actor_lct TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    related_proposal_id TEXT DEFAULT '',
                    related_trust_id TEXT DEFAULT '',
                    related_handshake_id TEXT DEFAULT '',
                    local_audit_ids TEXT DEFAULT '{}',
                    previous_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL,
                    acknowledged_by TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL
                )
            """)

            # Indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cross_source
                ON cross_fed_audit(source_federation_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cross_timestamp
                ON cross_fed_audit(timestamp)
            """)

            conn.commit()
        finally:
            conn.close()

    def _get_last_hash(self) -> str:
        """Get the hash of the most recent record."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT record_hash FROM cross_fed_audit
                ORDER BY created_at DESC LIMIT 1
            """).fetchone()
            if row:
                return row["record_hash"]
            return "cross_genesis"
        finally:
            conn.close()

    def _compute_hash(self, record: CrossFederationAuditRecord) -> str:
        """Compute SHA-256 hash of a record."""
        data = {
            "record_id": record.record_id,
            "event_type": record.event_type.value,
            "timestamp": record.timestamp,
            "source_federation_id": record.source_federation_id,
            "target_federation_ids": json.dumps(record.target_federation_ids, sort_keys=True),
            "actor_lct": record.actor_lct,
            "event_data": json.dumps(record.event_data, sort_keys=True),
            "previous_hash": record.previous_hash,
        }
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def register_local_audit(self, federation_id: str, audit: GovernanceAuditTrail):
        """Register a local audit trail for cross-referencing."""
        self._local_audits[federation_id] = audit

    def record_cross_federation_event(
        self,
        event_type: CrossFederationEventType,
        source_federation_id: str,
        target_federation_ids: List[str],
        actor_lct: str,
        event_data: Optional[Dict] = None,
        related_proposal_id: str = "",
        related_trust_id: str = "",
        related_handshake_id: str = "",
    ) -> CrossFederationAuditRecord:
        """
        Record a cross-federation event.

        Args:
            event_type: Type of cross-federation event
            source_federation_id: Initiating federation
            target_federation_ids: Affected federations
            actor_lct: Who initiated the action
            event_data: Event-specific data
            related_proposal_id: Related proposal if any
            related_trust_id: Related trust relationship if any
            related_handshake_id: Related handshake if any

        Returns:
            CrossFederationAuditRecord
        """
        import uuid

        now = datetime.now(timezone.utc).isoformat()

        record = CrossFederationAuditRecord(
            record_id=f"xaudit:{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            timestamp=now,
            source_federation_id=source_federation_id,
            target_federation_ids=target_federation_ids,
            actor_lct=actor_lct,
            event_data=event_data or {},
            related_proposal_id=related_proposal_id,
            related_trust_id=related_trust_id,
            related_handshake_id=related_handshake_id,
            previous_hash=self._last_hash,
            acknowledged_by=[source_federation_id],  # Source auto-acknowledges
        )

        # Compute hash
        record.record_hash = self._compute_hash(record)

        # Also record to local audit trails if registered
        local_ids = {}
        all_feds = [source_federation_id] + target_federation_ids
        for fed_id in all_feds:
            if fed_id in self._local_audits:
                # Map to standard AuditEventType
                local_type = self._map_to_local_event_type(event_type)
                if local_type:
                    local_record = self._local_audits[fed_id].record_event(
                        local_type,
                        fed_id,
                        actor_lct,
                        event_data=event_data,
                    )
                    local_ids[fed_id] = local_record.record_id

        record.local_audit_ids = local_ids

        # Store
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO cross_fed_audit
                (record_id, event_type, timestamp, source_federation_id,
                 target_federation_ids, actor_lct, event_data,
                 related_proposal_id, related_trust_id, related_handshake_id,
                 local_audit_ids, previous_hash, record_hash, acknowledged_by,
                 created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.record_id,
                record.event_type.value,
                record.timestamp,
                record.source_federation_id,
                json.dumps(record.target_federation_ids),
                record.actor_lct,
                json.dumps(record.event_data),
                record.related_proposal_id,
                record.related_trust_id,
                record.related_handshake_id,
                json.dumps(record.local_audit_ids),
                record.previous_hash,
                record.record_hash,
                json.dumps(record.acknowledged_by),
                now,
            ))
            conn.commit()
        finally:
            conn.close()

        self._last_hash = record.record_hash
        return record

    def _map_to_local_event_type(self, cross_type: CrossFederationEventType) -> Optional[AuditEventType]:
        """Map cross-federation event to local audit event type."""
        mapping = {
            CrossFederationEventType.CROSS_FED_PROPOSAL_CREATED: AuditEventType.PROPOSAL_CREATED,
            CrossFederationEventType.CROSS_FED_PROPOSAL_VOTED: AuditEventType.PROPOSAL_VOTED,
            CrossFederationEventType.CROSS_FED_PROPOSAL_APPROVED: AuditEventType.PROPOSAL_APPROVED,
            CrossFederationEventType.CROSS_FED_PROPOSAL_REJECTED: AuditEventType.PROPOSAL_REJECTED,
            CrossFederationEventType.CROSS_FED_PROPOSAL_EXECUTED: AuditEventType.PROPOSAL_EXECUTED,
            CrossFederationEventType.INTER_FED_TRUST_ESTABLISHED: AuditEventType.TRUST_ESTABLISHED,
            CrossFederationEventType.INTER_FED_TRUST_UPDATED: AuditEventType.TRUST_UPDATED,
            CrossFederationEventType.CROSS_FED_WITNESS_PROVIDED: AuditEventType.WITNESS_PROVIDED,
        }
        return mapping.get(cross_type)

    def acknowledge_event(
        self,
        record_id: str,
        federation_id: str,
    ) -> bool:
        """
        Mark a cross-federation event as acknowledged by a federation.

        Args:
            record_id: The audit record to acknowledge
            federation_id: The acknowledging federation

        Returns:
            True if acknowledged, False if already acknowledged or not found
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT acknowledged_by FROM cross_fed_audit WHERE record_id = ?
            """, (record_id,)).fetchone()

            if not row:
                return False

            acknowledged = json.loads(row["acknowledged_by"])
            if federation_id in acknowledged:
                return False  # Already acknowledged

            acknowledged.append(federation_id)

            conn.execute("""
                UPDATE cross_fed_audit
                SET acknowledged_by = ?
                WHERE record_id = ?
            """, (json.dumps(acknowledged), record_id))
            conn.commit()

            return True
        finally:
            conn.close()

    def get_events_for_federation(
        self,
        federation_id: str,
        include_as_source: bool = True,
        include_as_target: bool = True,
        limit: int = 100,
    ) -> List[CrossFederationAuditRecord]:
        """
        Get all cross-federation events involving a federation.

        Args:
            federation_id: The federation
            include_as_source: Include events where federation is source
            include_as_target: Include events where federation is target
            limit: Maximum records to return

        Returns:
            List of records, most recent first
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row

            conditions = []
            params = []

            if include_as_source:
                conditions.append("source_federation_id = ?")
                params.append(federation_id)

            if include_as_target:
                conditions.append(f"target_federation_ids LIKE ?")
                params.append(f"%{federation_id}%")

            if not conditions:
                return []

            where_clause = " OR ".join(conditions)
            params.append(limit)

            rows = conn.execute(f"""
                SELECT * FROM cross_fed_audit
                WHERE {where_clause}
                ORDER BY timestamp DESC LIMIT ?
            """, params).fetchall()

            return [self._row_to_record(row) for row in rows]
        finally:
            conn.close()

    def _row_to_record(self, row) -> CrossFederationAuditRecord:
        """Convert database row to CrossFederationAuditRecord."""
        return CrossFederationAuditRecord(
            record_id=row["record_id"],
            event_type=CrossFederationEventType(row["event_type"]),
            timestamp=row["timestamp"],
            source_federation_id=row["source_federation_id"],
            target_federation_ids=json.loads(row["target_federation_ids"]),
            actor_lct=row["actor_lct"],
            event_data=json.loads(row["event_data"]),
            related_proposal_id=row["related_proposal_id"],
            related_trust_id=row["related_trust_id"],
            related_handshake_id=row["related_handshake_id"],
            local_audit_ids=json.loads(row["local_audit_ids"]),
            previous_hash=row["previous_hash"],
            record_hash=row["record_hash"],
            acknowledged_by=json.loads(row["acknowledged_by"]),
        )

    def get_unacknowledged_events(
        self,
        federation_id: str,
    ) -> List[CrossFederationAuditRecord]:
        """Get events involving a federation that it hasn't acknowledged."""
        events = self.get_events_for_federation(federation_id)
        return [e for e in events if federation_id not in e.acknowledged_by]

    def verify_chain_integrity(self) -> Dict:
        """Verify integrity of the cross-federation audit chain."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM cross_fed_audit
                ORDER BY created_at ASC
            """).fetchall()

            if not rows:
                return {
                    "valid": True,
                    "records_checked": 0,
                    "issues": [],
                }

            issues = []
            expected_prev_hash = "cross_genesis"

            for row in rows:
                record = self._row_to_record(row)

                # Verify chain link
                if record.previous_hash != expected_prev_hash:
                    issues.append({
                        "record_id": record.record_id,
                        "issue": "broken_chain",
                    })

                # Verify hash
                computed = self._compute_hash(record)
                if computed != record.record_hash:
                    issues.append({
                        "record_id": record.record_id,
                        "issue": "hash_mismatch",
                    })

                expected_prev_hash = record.record_hash

            return {
                "valid": len(issues) == 0,
                "records_checked": len(rows),
                "issues": issues,
            }
        finally:
            conn.close()

    def export_unified_audit(
        self,
        federation_ids: List[str],
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict:
        """
        Export unified audit for multiple federations.

        Args:
            federation_ids: Federations to include
            start: Start time (optional)
            end: End time (optional)

        Returns:
            Dict with unified audit report
        """
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row

            # Build query for cross-federation events
            conditions = []
            params = []

            for fed_id in federation_ids:
                conditions.append("source_federation_id = ?")
                params.append(fed_id)
                conditions.append("target_federation_ids LIKE ?")
                params.append(f"%{fed_id}%")

            where_clause = " OR ".join(conditions)

            if start:
                where_clause = f"({where_clause}) AND timestamp >= ?"
                params.append(start.isoformat())
            if end:
                where_clause = f"({where_clause}) AND timestamp <= ?"
                params.append(end.isoformat())

            rows = conn.execute(f"""
                SELECT * FROM cross_fed_audit
                WHERE {where_clause}
                ORDER BY timestamp ASC
            """, params).fetchall()

            records = [self._row_to_record(row) for row in rows]

            # Verify chain integrity
            verification = self.verify_chain_integrity()

            # Collect local audit references
            local_references = {}
            for record in records:
                for fed_id, audit_id in record.local_audit_ids.items():
                    if fed_id not in local_references:
                        local_references[fed_id] = []
                    local_references[fed_id].append(audit_id)

            return {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "federations": federation_ids,
                "period_start": start.isoformat() if start else "beginning",
                "period_end": end.isoformat() if end else "now",
                "record_count": len(records),
                "chain_verified": verification["valid"],
                "records": [r.to_dict() for r in records],
                "local_audit_references": local_references,
            }
        finally:
            conn.close()

    def get_statistics(self) -> Dict:
        """Get cross-federation audit statistics."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row

            total = conn.execute("""
                SELECT COUNT(*) as count FROM cross_fed_audit
            """).fetchone()["count"]

            by_type = conn.execute("""
                SELECT event_type, COUNT(*) as count
                FROM cross_fed_audit
                GROUP BY event_type
            """).fetchall()

            # Unique federations involved
            fed_count = conn.execute("""
                SELECT COUNT(DISTINCT source_federation_id) as count
                FROM cross_fed_audit
            """).fetchone()["count"]

            return {
                "total_records": total,
                "by_event_type": {row["event_type"]: row["count"] for row in by_type},
                "unique_source_federations": fed_count,
            }
        finally:
            conn.close()


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Cross-Federation Audit - Self Test")
    print("=" * 60)

    import tempfile

    tmp_dir = Path(tempfile.mkdtemp())

    # Create cross-federation audit
    cross_audit = CrossFederationAudit(db_path=tmp_dir / "cross_audit.db")

    # Create local audit trails
    local_alpha = GovernanceAuditTrail(db_path=tmp_dir / "alpha_audit.db")
    local_beta = GovernanceAuditTrail(db_path=tmp_dir / "beta_audit.db")

    cross_audit.register_local_audit("fed:alpha", local_alpha)
    cross_audit.register_local_audit("fed:beta", local_beta)

    # Record cross-federation events
    print("\n1. Record cross-federation events:")

    r1 = cross_audit.record_cross_federation_event(
        CrossFederationEventType.INTER_FED_TRUST_ESTABLISHED,
        "fed:alpha",
        ["fed:beta"],
        "lct:alice",
        event_data={"trust_score": 0.7},
    )
    print(f"   Trust established: {r1.record_id}")

    r2 = cross_audit.record_cross_federation_event(
        CrossFederationEventType.CROSS_FED_PROPOSAL_CREATED,
        "fed:alpha",
        ["fed:beta", "fed:gamma"],
        "lct:bob",
        event_data={"action": "joint_venture"},
        related_proposal_id="prop:joint:001",
    )
    print(f"   Proposal created: {r2.record_id}")

    # Acknowledge event
    print("\n2. Acknowledge events:")
    cross_audit.acknowledge_event(r2.record_id, "fed:beta")
    print(f"   fed:beta acknowledged {r2.record_id}")

    # Query events
    print("\n3. Query events for fed:alpha:")
    events = cross_audit.get_events_for_federation("fed:alpha")
    for e in events:
        print(f"   - {e.event_type.value}: {e.source_federation_id} -> {e.target_federation_ids}")

    # Check unacknowledged
    print("\n4. Unacknowledged events for fed:gamma:")
    unack = cross_audit.get_unacknowledged_events("fed:gamma")
    print(f"   {len(unack)} unacknowledged events")

    # Verify chain
    print("\n5. Verify chain integrity:")
    verification = cross_audit.verify_chain_integrity()
    print(f"   Valid: {verification['valid']}")
    print(f"   Records checked: {verification['records_checked']}")

    # Export
    print("\n6. Export unified audit:")
    export = cross_audit.export_unified_audit(["fed:alpha", "fed:beta"])
    print(f"   Records: {export['record_count']}")
    print(f"   Chain verified: {export['chain_verified']}")

    # Statistics
    print("\n7. Statistics:")
    stats = cross_audit.get_statistics()
    print(f"   Total records: {stats['total_records']}")
    print(f"   Unique sources: {stats['unique_source_federations']}")

    print("\n" + "=" * 60)
    print("Self-test complete.")
