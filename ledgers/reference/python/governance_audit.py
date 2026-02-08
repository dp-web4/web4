"""
Governance Audit Trail: Immutable Log for Federation Decisions

Track BX: Connects governance decisions to an immutable audit log.

Key principles:
1. Every governance action is recorded with full context
2. Records are append-only (immutable once written)
3. Includes cryptographic hashing for integrity verification
4. Enables reconstruction of governance history
5. Supports compliance and accountability requirements

This creates a tamper-evident record of all federation governance.
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path


class AuditEventType(Enum):
    """Types of auditable governance events."""
    # Proposal lifecycle
    PROPOSAL_CREATED = "proposal_created"
    PROPOSAL_VOTED = "proposal_voted"
    PROPOSAL_APPROVED = "proposal_approved"
    PROPOSAL_REJECTED = "proposal_rejected"
    PROPOSAL_EXECUTED = "proposal_executed"
    PROPOSAL_EXPIRED = "proposal_expired"

    # Trust operations
    TRUST_ESTABLISHED = "trust_established"
    TRUST_UPDATED = "trust_updated"
    TRUST_DECAYED = "trust_decayed"
    TRUST_MAINTAINED = "trust_maintained"

    # Federation operations
    FEDERATION_REGISTERED = "federation_registered"
    FEDERATION_SUSPENDED = "federation_suspended"
    TEAM_BOUND = "team_bound"
    WITNESS_PROVIDED = "witness_provided"

    # Reputation events
    REPUTATION_CALCULATED = "reputation_calculated"
    REPUTATION_TIER_CHANGED = "reputation_tier_changed"

    # Economic operations
    ATP_TRANSFERRED = "atp_transferred"
    ATP_LOCKED = "atp_locked"
    ATP_RETURNED = "atp_returned"


@dataclass
class AuditRecord:
    """An immutable audit record for a governance event."""
    record_id: str
    event_type: AuditEventType
    timestamp: str
    federation_id: str
    actor_lct: str  # Who initiated the action

    # Event context
    event_data: Dict = field(default_factory=dict)

    # Related entities
    target_federation_id: str = ""
    proposal_id: str = ""
    related_record_ids: List[str] = field(default_factory=list)

    # Integrity
    previous_hash: str = ""  # Hash of previous record (chain)
    record_hash: str = ""    # Hash of this record

    # Metadata
    source_ip: str = ""
    user_agent: str = ""
    session_id: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'AuditRecord':
        data = dict(data)
        data["event_type"] = AuditEventType(data["event_type"])
        return cls(**data)


class GovernanceAuditTrail:
    """
    Immutable audit trail for federation governance.

    Track BX: Connects governance decisions to immutable log.

    Features:
    - Append-only records
    - Cryptographic hash chain
    - Query by federation, time range, event type
    - Integrity verification
    - Export for compliance
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize audit trail.

        Args:
            db_path: Path to SQLite database. Defaults to in-memory.
        """
        if db_path:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._in_memory = False
        else:
            self.db_path = ":memory:"
            self._in_memory = True

        self._init_db()
        self._last_hash = self._get_last_hash()

    def _get_conn(self):
        """Get database connection."""
        if self._in_memory:
            return sqlite3.connect(":memory:")
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_records (
                    record_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    federation_id TEXT NOT NULL,
                    actor_lct TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    target_federation_id TEXT DEFAULT '',
                    proposal_id TEXT DEFAULT '',
                    related_record_ids TEXT DEFAULT '[]',
                    previous_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL,
                    source_ip TEXT DEFAULT '',
                    user_agent TEXT DEFAULT '',
                    session_id TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_federation
                ON audit_records(federation_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_records(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_event_type
                ON audit_records(event_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_proposal
                ON audit_records(proposal_id)
            """)
            conn.commit()
        finally:
            if not self._in_memory:
                conn.close()

    def _get_last_hash(self) -> str:
        """Get the hash of the most recent record (or genesis hash)."""
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT record_hash FROM audit_records
                ORDER BY created_at DESC LIMIT 1
            """).fetchone()
            if row:
                return row["record_hash"]
            return "genesis"  # Initial hash for empty chain
        finally:
            if not self._in_memory:
                conn.close()

    def _compute_hash(self, record: AuditRecord) -> str:
        """Compute SHA-256 hash of a record."""
        # Create deterministic representation
        data = {
            "record_id": record.record_id,
            "event_type": record.event_type.value,
            "timestamp": record.timestamp,
            "federation_id": record.federation_id,
            "actor_lct": record.actor_lct,
            "event_data": json.dumps(record.event_data, sort_keys=True),
            "target_federation_id": record.target_federation_id,
            "proposal_id": record.proposal_id,
            "previous_hash": record.previous_hash,
        }
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def record_event(
        self,
        event_type: AuditEventType,
        federation_id: str,
        actor_lct: str,
        event_data: Optional[Dict] = None,
        target_federation_id: str = "",
        proposal_id: str = "",
        related_record_ids: Optional[List[str]] = None,
        source_ip: str = "",
        user_agent: str = "",
        session_id: str = "",
    ) -> AuditRecord:
        """
        Record a governance event to the audit trail.

        Returns:
            The created AuditRecord with computed hash
        """
        import uuid

        record = AuditRecord(
            record_id=f"audit:{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            federation_id=federation_id,
            actor_lct=actor_lct,
            event_data=event_data or {},
            target_federation_id=target_federation_id,
            proposal_id=proposal_id,
            related_record_ids=related_record_ids or [],
            previous_hash=self._last_hash,
            source_ip=source_ip,
            user_agent=user_agent,
            session_id=session_id,
        )

        # Compute hash
        record.record_hash = self._compute_hash(record)

        # Store
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT INTO audit_records (
                    record_id, event_type, timestamp, federation_id, actor_lct,
                    event_data, target_federation_id, proposal_id, related_record_ids,
                    previous_hash, record_hash, source_ip, user_agent, session_id,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.record_id,
                record.event_type.value,
                record.timestamp,
                record.federation_id,
                record.actor_lct,
                json.dumps(record.event_data),
                record.target_federation_id,
                record.proposal_id,
                json.dumps(record.related_record_ids),
                record.previous_hash,
                record.record_hash,
                record.source_ip,
                record.user_agent,
                record.session_id,
                datetime.now(timezone.utc).isoformat(),
            ))
            conn.commit()
        finally:
            if not self._in_memory:
                conn.close()

        # Update chain
        self._last_hash = record.record_hash

        return record

    def get_record(self, record_id: str) -> Optional[AuditRecord]:
        """Get a specific audit record by ID."""
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM audit_records WHERE record_id = ?
            """, (record_id,)).fetchone()

            if row:
                return self._row_to_record(row)
            return None
        finally:
            if not self._in_memory:
                conn.close()

    def _row_to_record(self, row) -> AuditRecord:
        """Convert database row to AuditRecord."""
        return AuditRecord(
            record_id=row["record_id"],
            event_type=AuditEventType(row["event_type"]),
            timestamp=row["timestamp"],
            federation_id=row["federation_id"],
            actor_lct=row["actor_lct"],
            event_data=json.loads(row["event_data"]),
            target_federation_id=row["target_federation_id"],
            proposal_id=row["proposal_id"],
            related_record_ids=json.loads(row["related_record_ids"]),
            previous_hash=row["previous_hash"],
            record_hash=row["record_hash"],
            source_ip=row["source_ip"],
            user_agent=row["user_agent"],
            session_id=row["session_id"],
        )

    def get_federation_history(
        self,
        federation_id: str,
        limit: int = 100,
        event_types: Optional[List[AuditEventType]] = None,
    ) -> List[AuditRecord]:
        """
        Get audit history for a federation.

        Args:
            federation_id: Federation to query
            limit: Maximum records to return
            event_types: Filter by event types (optional)

        Returns:
            List of AuditRecords, newest first
        """
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row

            if event_types:
                type_placeholders = ",".join("?" * len(event_types))
                type_values = [t.value for t in event_types]
                rows = conn.execute(f"""
                    SELECT * FROM audit_records
                    WHERE federation_id = ? AND event_type IN ({type_placeholders})
                    ORDER BY timestamp DESC LIMIT ?
                """, (federation_id, *type_values, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM audit_records
                    WHERE federation_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (federation_id, limit)).fetchall()

            return [self._row_to_record(row) for row in rows]
        finally:
            if not self._in_memory:
                conn.close()

    def get_proposal_history(self, proposal_id: str) -> List[AuditRecord]:
        """Get all audit records for a specific proposal."""
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM audit_records
                WHERE proposal_id = ?
                ORDER BY timestamp ASC
            """, (proposal_id,)).fetchall()

            return [self._row_to_record(row) for row in rows]
        finally:
            if not self._in_memory:
                conn.close()

    def get_records_by_time_range(
        self,
        start: datetime,
        end: datetime,
        federation_id: Optional[str] = None,
    ) -> List[AuditRecord]:
        """Get audit records within a time range."""
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row

            if federation_id:
                rows = conn.execute("""
                    SELECT * FROM audit_records
                    WHERE timestamp >= ? AND timestamp <= ? AND federation_id = ?
                    ORDER BY timestamp ASC
                """, (start.isoformat(), end.isoformat(), federation_id)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM audit_records
                    WHERE timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp ASC
                """, (start.isoformat(), end.isoformat())).fetchall()

            return [self._row_to_record(row) for row in rows]
        finally:
            if not self._in_memory:
                conn.close()

    def verify_chain_integrity(
        self,
        federation_id: Optional[str] = None,
    ) -> Dict:
        """
        Verify the integrity of the audit chain.

        Returns:
            Dict with verification results
        """
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row

            if federation_id:
                rows = conn.execute("""
                    SELECT * FROM audit_records
                    WHERE federation_id = ?
                    ORDER BY created_at ASC
                """, (federation_id,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM audit_records
                    ORDER BY created_at ASC
                """).fetchall()

            if not rows:
                return {
                    "valid": True,
                    "records_checked": 0,
                    "issues": [],
                }

            issues = []
            expected_prev_hash = "genesis"

            for row in rows:
                record = self._row_to_record(row)

                # Verify hash chain
                if record.previous_hash != expected_prev_hash:
                    issues.append({
                        "record_id": record.record_id,
                        "issue": "broken_chain",
                        "expected_prev": expected_prev_hash,
                        "actual_prev": record.previous_hash,
                    })

                # Verify record hash
                computed_hash = self._compute_hash(record)
                if computed_hash != record.record_hash:
                    issues.append({
                        "record_id": record.record_id,
                        "issue": "hash_mismatch",
                        "expected_hash": computed_hash,
                        "actual_hash": record.record_hash,
                    })

                expected_prev_hash = record.record_hash

            return {
                "valid": len(issues) == 0,
                "records_checked": len(rows),
                "issues": issues,
                "last_hash": expected_prev_hash,
            }
        finally:
            if not self._in_memory:
                conn.close()

    def export_for_compliance(
        self,
        federation_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict:
        """
        Export audit records for compliance purposes.

        Returns:
            Dict with records, verification, and metadata
        """
        if start and end:
            records = self.get_records_by_time_range(start, end, federation_id)
        else:
            records = self.get_federation_history(federation_id, limit=10000)

        # Verify GLOBAL chain integrity (federation filter breaks chain by design)
        # Hash chain is global to prevent selective deletion
        global_verification = self.verify_chain_integrity()

        # Verify individual record hashes for this federation
        record_hashes_valid = True
        for record in records:
            computed = self._compute_hash(record)
            if computed != record.record_hash:
                record_hashes_valid = False
                break

        return {
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "federation_id": federation_id,
            "period_start": start.isoformat() if start else "beginning",
            "period_end": end.isoformat() if end else "now",
            "record_count": len(records),
            "global_chain_verified": global_verification["valid"],
            "record_hashes_verified": record_hashes_valid,
            "records": [r.to_dict() for r in records],
            "verification_details": global_verification,
        }

    def get_statistics(
        self,
        federation_id: Optional[str] = None,
    ) -> Dict:
        """Get audit trail statistics."""
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row

            if federation_id:
                total = conn.execute("""
                    SELECT COUNT(*) as count FROM audit_records
                    WHERE federation_id = ?
                """, (federation_id,)).fetchone()["count"]

                by_type = conn.execute("""
                    SELECT event_type, COUNT(*) as count
                    FROM audit_records WHERE federation_id = ?
                    GROUP BY event_type
                """, (federation_id,)).fetchall()
            else:
                total = conn.execute("""
                    SELECT COUNT(*) as count FROM audit_records
                """).fetchone()["count"]

                by_type = conn.execute("""
                    SELECT event_type, COUNT(*) as count
                    FROM audit_records
                    GROUP BY event_type
                """).fetchall()

            return {
                "total_records": total,
                "by_event_type": {row["event_type"]: row["count"] for row in by_type},
                "federation_id": federation_id or "all",
            }
        finally:
            if not self._in_memory:
                conn.close()


# Self-test
if __name__ == "__main__":
    print("=" * 60)
    print("Governance Audit Trail - Self Test")
    print("=" * 60)

    import tempfile

    tmp_dir = Path(tempfile.mkdtemp())
    audit = GovernanceAuditTrail(db_path=tmp_dir / "audit.db")

    # Record some events
    print("\n1. Record governance events:")

    r1 = audit.record_event(
        AuditEventType.PROPOSAL_CREATED,
        "fed:alpha",
        "lct:proposer:alice",
        event_data={"description": "Alliance proposal", "action_type": "cross_fed"},
        proposal_id="gov:alpha:001",
    )
    print(f"   Created proposal: {r1.record_id}")

    r2 = audit.record_event(
        AuditEventType.PROPOSAL_VOTED,
        "fed:beta",
        "lct:voter:bob",
        event_data={"vote": "approve", "weight": 0.65},
        proposal_id="gov:alpha:001",
        related_record_ids=[r1.record_id],
    )
    print(f"   Recorded vote: {r2.record_id}")

    r3 = audit.record_event(
        AuditEventType.PROPOSAL_APPROVED,
        "fed:alpha",
        "system",
        event_data={"approval_ratio": 0.75, "votes": 3},
        proposal_id="gov:alpha:001",
        related_record_ids=[r1.record_id, r2.record_id],
    )
    print(f"   Approved: {r3.record_id}")

    # Query history
    print("\n2. Query proposal history:")
    history = audit.get_proposal_history("gov:alpha:001")
    for record in history:
        print(f"   - {record.event_type.value}: {record.actor_lct}")

    # Verify chain
    print("\n3. Verify chain integrity:")
    verification = audit.verify_chain_integrity()
    print(f"   Valid: {verification['valid']}")
    print(f"   Records checked: {verification['records_checked']}")
    print(f"   Last hash: {verification['last_hash'][:16]}...")

    # Statistics
    print("\n4. Statistics:")
    stats = audit.get_statistics()
    print(f"   Total records: {stats['total_records']}")
    for event_type, count in stats["by_event_type"].items():
        print(f"   - {event_type}: {count}")

    # Export
    print("\n5. Export for compliance:")
    export = audit.export_for_compliance("fed:alpha")
    print(f"   Records exported: {export['record_count']}")
    print(f"   Global chain verified: {export['global_chain_verified']}")
    print(f"   Record hashes verified: {export['record_hashes_verified']}")

    print("\n" + "=" * 60)
    print("Self-test complete.")
