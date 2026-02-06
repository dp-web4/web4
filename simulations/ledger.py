# SPDX-License-Identifier: PROPRIETARY
# Copyright (c) 2025 Hardbound Contributors
#
# Hardbound - SQLite Ledger for Enterprise Governance
# https://github.com/dp-web4/hardbound
#
# DERIVATION NOTICE:
# This module is derived from the open-source Web4 Lightweight Governance ledger
# (https://github.com/dp-web4/web4/claude-code-plugin/governance/ledger.py)
# Adapted for enterprise use with Hardbound-specific storage and features.
# The open-source version serves as reference implementation for the core concepts.
"""
SQLite-based ledger for enterprise governance.

Provides:
- Identity registration (soft LCT)
- Session tracking with sequential numbering
- Work product registration
- ATP (Allocation Transfer Packet) accounting
- Audit trail with hash-chain witnessing
- Heartbeat tracking for timing coherence

This is the local persistence layer for Hardbound enterprise teams.
For distributed consensus, see the full Web4 blockchain implementation.

Storage location: ~/.hardbound/ledger.db
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import re
import fnmatch


class Ledger:
    """SQLite-based ledger for session tracking and governance."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize ledger with SQLite database.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.hardbound/ledger.db
        """
        if db_path is None:
            db_path = Path.home() / ".hardbound" / "ledger.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self):
        """Get a database connection with proper settings for concurrency."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA busy_timeout = 30000")  # 30 second wait on locks
        return conn

    def _init_db(self):
        """Initialize database schema with concurrency support."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable WAL mode for better concurrent read/write access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout = 30000")

            conn.executescript("""
                -- Identities (soft LCT)
                CREATE TABLE IF NOT EXISTS identities (
                    lct_id TEXT PRIMARY KEY,
                    machine_hash TEXT NOT NULL,
                    user_hash TEXT NOT NULL,
                    binding TEXT DEFAULT 'software',
                    created_at TEXT NOT NULL,
                    metadata TEXT
                );

                -- Session sequence tracking per project
                CREATE TABLE IF NOT EXISTS session_sequence (
                    project TEXT PRIMARY KEY,
                    last_session_number INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                );

                -- Sessions
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    lct_id TEXT NOT NULL,
                    project TEXT,
                    session_number INTEGER,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    status TEXT DEFAULT 'active',
                    atp_budget INTEGER DEFAULT 100,
                    atp_consumed INTEGER DEFAULT 0,
                    metadata TEXT,
                    FOREIGN KEY (lct_id) REFERENCES identities(lct_id)
                );

                -- Work products (files, commits, etc.)
                CREATE TABLE IF NOT EXISTS work_products (
                    product_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    product_type TEXT NOT NULL,
                    path TEXT,
                    content_hash TEXT,
                    created_at TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );

                -- Audit trail (with witnessing chain)
                CREATE TABLE IF NOT EXISTS audit_trail (
                    audit_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    tool_name TEXT,
                    target TEXT,
                    input_hash TEXT,
                    output_hash TEXT,
                    status TEXT,
                    timestamp TEXT NOT NULL,
                    r6_data TEXT,
                    previous_hash TEXT,
                    record_hash TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );

                -- Heartbeats (timing coherence tracking)
                CREATE TABLE IF NOT EXISTS heartbeats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    delta_seconds REAL,
                    tool_name TEXT,
                    action_index INTEGER,
                    previous_hash TEXT,
                    entry_hash TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );

                -- Policy entities (enterprise policy tracking)
                CREATE TABLE IF NOT EXISTS policy_entities (
                    entity_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    config TEXT NOT NULL
                );

                -- Policy witnessing
                CREATE TABLE IF NOT EXISTS policy_witnesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_entity_id TEXT NOT NULL,
                    witness_entity TEXT NOT NULL,
                    witness_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (policy_entity_id) REFERENCES policy_entities(entity_id)
                );

                -- Indexes for common queries
                CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project);
                CREATE INDEX IF NOT EXISTS idx_sessions_lct ON sessions(lct_id);
                CREATE INDEX IF NOT EXISTS idx_audit_session ON audit_trail(session_id);
                CREATE INDEX IF NOT EXISTS idx_work_session ON work_products(session_id);
                CREATE INDEX IF NOT EXISTS idx_heartbeat_session ON heartbeats(session_id);
                CREATE INDEX IF NOT EXISTS idx_policy_witness ON policy_witnesses(policy_entity_id);
            """)

    # --- Identity Management ---

    def register_identity(self, lct_id: str, machine_hash: str, user_hash: str,
                          binding: str = "software", metadata: Optional[Dict] = None) -> bool:
        """Register a new identity (soft LCT)."""
        now = datetime.now(timezone.utc).isoformat() + "Z"

        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT INTO identities (lct_id, machine_hash, user_hash, binding, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (lct_id, machine_hash, user_hash, binding, now,
                      json.dumps(metadata) if metadata else None))
                return True
            except sqlite3.IntegrityError:
                return False

    def get_identity(self, lct_id: str) -> Optional[Dict]:
        """Get identity by LCT ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM identities WHERE lct_id = ?", (lct_id,)
            ).fetchone()
            return dict(row) if row else None

    # --- Session Sequence Management ---

    def get_next_session_number(self, project: str) -> int:
        """Get next session number for a project (atomic increment)."""
        now = datetime.now(timezone.utc).isoformat() + "Z"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE session_sequence
                SET last_session_number = last_session_number + 1, updated_at = ?
                WHERE project = ?
            """, (now, project))

            if cursor.rowcount == 0:
                conn.execute("""
                    INSERT INTO session_sequence (project, last_session_number, updated_at)
                    VALUES (?, 1, ?)
                """, (project, now))
                return 1

            row = conn.execute(
                "SELECT last_session_number FROM session_sequence WHERE project = ?",
                (project,)
            ).fetchone()
            return row[0]

    def sync_session_number(self, project: str, known_max: int) -> int:
        """Sync session number with filesystem reality."""
        now = datetime.now(timezone.utc).isoformat() + "Z"

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT last_session_number FROM session_sequence WHERE project = ?",
                (project,)
            ).fetchone()

            current = row[0] if row else 0

            if known_max > current:
                if row:
                    conn.execute("""
                        UPDATE session_sequence
                        SET last_session_number = ?, updated_at = ?
                        WHERE project = ?
                    """, (known_max, now, project))
                else:
                    conn.execute("""
                        INSERT INTO session_sequence (project, last_session_number, updated_at)
                        VALUES (?, ?, ?)
                    """, (project, known_max, now))
                return known_max

            return current

    # --- Session Management ---

    def start_session(self, session_id: str, lct_id: str, project: Optional[str] = None,
                      session_number: Optional[int] = None, atp_budget: int = 100,
                      metadata: Optional[Dict] = None) -> Dict:
        """Start a new session."""
        now = datetime.now(timezone.utc).isoformat() + "Z"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions
                (session_id, lct_id, project, session_number, started_at, atp_budget, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, lct_id, project, session_number, now, atp_budget,
                  json.dumps(metadata) if metadata else None))

        return {
            "session_id": session_id,
            "lct_id": lct_id,
            "project": project,
            "session_number": session_number,
            "started_at": now,
            "atp_budget": atp_budget,
            "atp_remaining": atp_budget
        }

    def end_session(self, session_id: str, status: str = "completed") -> bool:
        """End a session."""
        now = datetime.now(timezone.utc).isoformat() + "Z"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE sessions SET ended_at = ?, status = ?
                WHERE session_id = ?
            """, (now, status, session_id))
            return cursor.rowcount > 0

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if row:
                session = dict(row)
                session["atp_remaining"] = session["atp_budget"] - session["atp_consumed"]
                return session
            return None

    # --- ATP Accounting ---

    def consume_atp(self, session_id: str, amount: int = 1) -> int:
        """Consume ATP for an action. Returns remaining ATP."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sessions SET atp_consumed = atp_consumed + ?
                WHERE session_id = ?
            """, (amount, session_id))

            row = conn.execute(
                "SELECT atp_budget - atp_consumed FROM sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            return row[0] if row else 0

    # --- Work Products ---

    def register_work_product(self, session_id: str, product_type: str,
                               path: Optional[str] = None, content: Optional[str] = None,
                               metadata: Optional[Dict] = None) -> str:
        """Register a work product (file, commit, etc.)."""
        now = datetime.now(timezone.utc).isoformat() + "Z"
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16] if content else None
        product_id = f"wp:{hashlib.sha256(f'{session_id}:{now}'.encode()).hexdigest()[:12]}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO work_products
                (product_id, session_id, product_type, path, content_hash, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (product_id, session_id, product_type, path, content_hash, now,
                  json.dumps(metadata) if metadata else None))

        return product_id

    def get_session_work_products(self, session_id: str) -> List[Dict]:
        """Get all work products for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM work_products WHERE session_id = ? ORDER BY created_at",
                (session_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    # --- Audit Trail (with witnessing chain) ---

    def record_audit(self, session_id: str, action_type: str, tool_name: Optional[str] = None,
                     target: Optional[str] = None, input_hash: Optional[str] = None,
                     output_hash: Optional[str] = None, status: str = "success",
                     r6_data: Optional[Dict] = None) -> Dict:
        """Record an audit entry with hash-linked witnessing chain."""
        now = datetime.now(timezone.utc).isoformat() + "Z"

        with sqlite3.connect(self.db_path, timeout=30.0) as conn:
            conn.execute("PRAGMA busy_timeout = 30000")

            prev = conn.execute("""
                SELECT sequence, record_hash FROM audit_trail
                WHERE session_id = ?
                ORDER BY sequence DESC LIMIT 1
            """, (session_id,)).fetchone()

            if prev:
                sequence = prev[0] + 1
                previous_hash = prev[1]
            else:
                sequence = 1
                previous_hash = ""

            hash_input = f"{session_id}:{sequence}:{now}:{tool_name}:{target}:{input_hash}:{output_hash}:{previous_hash}"
            record_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:32]

            audit_id = f"audit:{record_hash[:12]}"

            conn.execute("""
                INSERT INTO audit_trail
                (audit_id, session_id, sequence, action_type, tool_name, target,
                 input_hash, output_hash, status, timestamp, r6_data, previous_hash, record_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (audit_id, session_id, sequence, action_type, tool_name, target,
                  input_hash, output_hash, status, now,
                  json.dumps(r6_data) if r6_data else None,
                  previous_hash, record_hash))

        return {
            "audit_id": audit_id,
            "sequence": sequence,
            "record_hash": record_hash,
            "previous_hash": previous_hash
        }

    def get_last_audit_record(self, session_id: str) -> Optional[Dict]:
        """Get the most recent audit record for chain verification."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM audit_trail
                WHERE session_id = ?
                ORDER BY sequence DESC LIMIT 1
            """, (session_id,)).fetchone()
            return dict(row) if row else None

    def verify_audit_chain(self, session_id: str) -> tuple:
        """Verify the audit trail hash chain integrity."""
        records = self.get_session_audit_trail(session_id)

        if not records:
            return (True, None)

        for i, record in enumerate(records):
            if i == 0:
                if record.get('previous_hash'):
                    return (False, f"Genesis record has non-empty previous_hash")
                continue

            prev = records[i - 1]

            if record['sequence'] != prev['sequence'] + 1:
                return (False, f"Sequence gap at {i}: {prev['sequence']} -> {record['sequence']}")

            if record['previous_hash'] != prev['record_hash']:
                return (False, f"Hash chain broken at sequence {record['sequence']}")

        return (True, None)

    def get_session_audit_trail(self, session_id: str) -> List[Dict]:
        """Get audit trail for a session, ordered by sequence."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM audit_trail WHERE session_id = ? ORDER BY sequence ASC",
                (session_id,)
            ).fetchall()
            return [dict(row) for row in rows]

    # --- Summary ---

    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get summary of a session."""
        session = self.get_session(session_id)
        if not session:
            return None

        with sqlite3.connect(self.db_path) as conn:
            audit_count = conn.execute(
                "SELECT COUNT(*) FROM audit_trail WHERE session_id = ?", (session_id,)
            ).fetchone()[0]

            work_count = conn.execute(
                "SELECT COUNT(*) FROM work_products WHERE session_id = ?", (session_id,)
            ).fetchone()[0]

        return {
            "session_id": session_id,
            "session_number": session["session_number"],
            "project": session["project"],
            "status": session["status"],
            "started_at": session["started_at"],
            "ended_at": session["ended_at"],
            "action_count": audit_count,
            "atp_consumed": session["atp_consumed"],
            "atp_remaining": session["atp_remaining"],
            "work_products": work_count,
            "audit_records": audit_count
        }

    # --- Heartbeat Tracking ---

    def record_heartbeat(self, session_id: str, sequence: int, timestamp: str,
                         status: str, delta_seconds: float, tool_name: str,
                         action_index: int, previous_hash: str, entry_hash: str) -> int:
        """Record a heartbeat entry."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO heartbeats
                (session_id, sequence, timestamp, status, delta_seconds,
                 tool_name, action_index, previous_hash, entry_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (session_id, sequence, timestamp, status, delta_seconds,
                  tool_name, action_index, previous_hash, entry_hash))
            return cursor.lastrowid

    def get_last_heartbeat(self, session_id: str) -> Optional[Dict]:
        """Get the most recent heartbeat for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM heartbeats
                WHERE session_id = ?
                ORDER BY sequence DESC LIMIT 1
            """, (session_id,)).fetchone()
            return dict(row) if row else None

    def get_heartbeats(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get heartbeats for a session."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if limit:
                rows = conn.execute("""
                    SELECT * FROM heartbeats
                    WHERE session_id = ?
                    ORDER BY sequence DESC LIMIT ?
                """, (session_id, limit)).fetchall()
                return [dict(row) for row in reversed(rows)]
            else:
                rows = conn.execute("""
                    SELECT * FROM heartbeats
                    WHERE session_id = ?
                    ORDER BY sequence ASC
                """, (session_id,)).fetchall()
                return [dict(row) for row in rows]

    def get_heartbeat_count(self, session_id: str) -> int:
        """Get total heartbeat count for a session."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM heartbeats WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            return row[0] if row else 0

    def get_heartbeat_status_distribution(self, session_id: str) -> Dict[str, int]:
        """Get distribution of heartbeat statuses for a session."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM heartbeats
                WHERE session_id = ?
                GROUP BY status
            """, (session_id,)).fetchall()
            return {row[0]: row[1] for row in rows}

    # --- Policy Entity Persistence ---

    def save_policy_entity(self, entity_id: str, name: str, version: str,
                           content_hash: str, source: str, config: Dict) -> bool:
        """Persist a policy entity to the ledger."""
        now = datetime.now(timezone.utc).isoformat() + "Z"

        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT INTO policy_entities
                    (entity_id, name, version, content_hash, created_at, source, config)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (entity_id, name, version, content_hash, now, source,
                      json.dumps(config)))
                return True
            except sqlite3.IntegrityError:
                return False

    def get_policy_entity(self, entity_id: str) -> Optional[Dict]:
        """Get a policy entity by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM policy_entities WHERE entity_id = ?", (entity_id,)
            ).fetchone()
            if row:
                result = dict(row)
                result["config"] = json.loads(result["config"])
                return result
            return None

    def record_policy_witness(self, policy_entity_id: str, witness_entity: str,
                               witness_type: str) -> int:
        """Record a witnessing event for a policy."""
        now = datetime.now(timezone.utc).isoformat() + "Z"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO policy_witnesses
                (policy_entity_id, witness_entity, witness_type, timestamp)
                VALUES (?, ?, ?, ?)
            """, (policy_entity_id, witness_entity, witness_type, now))
            return cursor.lastrowid

    def get_policy_witnesses(self, policy_entity_id: str) -> List[Dict]:
        """Get all witnesses for a policy."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM policy_witnesses
                WHERE policy_entity_id = ?
                ORDER BY timestamp ASC
            """, (policy_entity_id,)).fetchall()
            return [dict(row) for row in rows]

    # --- Audit Query & Filtering ---

    def query_audit(
        self,
        session_id: Optional[str] = None,
        tool: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        target_pattern: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Query and filter audit records."""
        conditions = []
        params: List[Any] = []

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        if tool:
            conditions.append("tool_name = ?")
            params.append(tool)

        if status:
            conditions.append("status = ?")
            params.append(status)

        if since:
            since_dt = self._parse_since(since)
            if since_dt:
                conditions.append("timestamp >= ?")
                params.append(since_dt.isoformat() + "Z")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(f"""
                SELECT * FROM audit_trail
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
            """, (*params, limit * 10)).fetchall()

        results = [dict(row) for row in rows]

        if category:
            filtered = []
            for r in results:
                if r.get("r6_data"):
                    try:
                        r6 = json.loads(r["r6_data"])
                        if r6.get("request", {}).get("category") == category:
                            filtered.append(r)
                    except (json.JSONDecodeError, TypeError):
                        pass
            results = filtered

        if target_pattern:
            filtered = []
            for r in results:
                target = r.get("target")
                if target and fnmatch.fnmatch(target, target_pattern):
                    filtered.append(r)
            results = filtered

        return results[:limit]

    def _parse_since(self, since: str) -> Optional[datetime]:
        """Parse a 'since' value: ISO date string or relative duration."""
        match = re.match(r"^(\d+)\s*(s|m|h|d)$", since)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            seconds = amount * multipliers[unit]
            return datetime.now(timezone.utc) - timedelta(seconds=seconds)

        try:
            if since.endswith("Z"):
                since = since[:-1] + "+00:00"
            return datetime.fromisoformat(since)
        except ValueError:
            return None

    def get_audit_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated audit statistics."""
        condition = "WHERE session_id = ?" if session_id else ""
        params = (session_id,) if session_id else ()

        with sqlite3.connect(self.db_path) as conn:
            tool_rows = conn.execute(f"""
                SELECT tool_name, COUNT(*) as count
                FROM audit_trail {condition}
                GROUP BY tool_name
                ORDER BY count DESC
            """, params).fetchall()
            tool_counts = {row[0]: row[1] for row in tool_rows if row[0]}

            status_rows = conn.execute(f"""
                SELECT status, COUNT(*) as count
                FROM audit_trail {condition}
                GROUP BY status
            """, params).fetchall()
            status_counts = {row[0]: row[1] for row in status_rows if row[0]}

            total_row = conn.execute(f"""
                SELECT COUNT(*) FROM audit_trail {condition}
            """, params).fetchone()
            total = total_row[0] if total_row else 0

        category_counts: Dict[str, int] = {}
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(f"""
                SELECT r6_data FROM audit_trail {condition}
            """, params).fetchall()
            for row in rows:
                if row[0]:
                    try:
                        r6 = json.loads(row[0])
                        cat = r6.get("request", {}).get("category")
                        if cat:
                            category_counts[cat] = category_counts.get(cat, 0) + 1
                    except (json.JSONDecodeError, TypeError):
                        pass

        return {
            "total": total,
            "tool_counts": tool_counts,
            "status_counts": status_counts,
            "category_counts": category_counts,
        }
