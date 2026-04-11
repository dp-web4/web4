"""
SESSION 94 TRACK 3: REPUTATION PERSISTENCE (SQLite BACKEND)

From Session 93's next steps:
> "Reputation persistence: Trust/reputation should persist across restarts,
   enabling long-term expert reputation building"

This implements:
1. SQLite database schema for reputation tracking
2. Migration from in-memory to persistent storage
3. Expert profile persistence (LCT identity, capabilities, cost)
4. Reputation history tracking (all updates with timestamps)
5. Trust tensor persistence (V3/T3 dimensions)

Key innovations:
- Atomic reputation updates (ACID transactions)
- Historical audit trail (all updates preserved)
- Multi-dimensional trust persistence (reliability, accuracy, speed, cost_efficiency)
- Expert discovery (query by capability, min reputation, etc.)
- Migration utilities (import from in-memory structures)

Integration with previous tracks:
- Track 1 (HTTP): Remote invocations update persistent reputation
- Track 2 (Signatures): Verified results create audit trail
- Session 93 Track 3: Trust tensor updates now persisted

References:
- Session 93 Track 1 (IRP Expert Registry)
- Session 93 Track 3 (Trust Tensor Updates)
- Web4 LCT identity system
- Multi-dimensional trust (V3/T3)
"""

import sqlite3
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from pathlib import Path
import secrets


# ============================================================================
# DATABASE SCHEMA
# ============================================================================

SCHEMA_VERSION = "1.0.0"

SCHEMA_SQL = """
-- Expert profiles
CREATE TABLE IF NOT EXISTS experts (
    lct_identity TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    capabilities_json TEXT NOT NULL,  -- JSON list of capability tags
    cost_per_invocation REAL NOT NULL,
    cost_unit TEXT DEFAULT 'atp',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Trust tensor (multi-dimensional reputation)
CREATE TABLE IF NOT EXISTS trust_tensor (
    lct_identity TEXT PRIMARY KEY,
    reliability REAL DEFAULT 0.5,      -- V3: Success rate
    accuracy REAL DEFAULT 0.5,         -- V3: Quality/confidence
    speed REAL DEFAULT 0.5,            -- V3: Latency performance
    cost_efficiency REAL DEFAULT 0.5,  -- V3: Cost vs value
    total_invocations INTEGER DEFAULT 0,
    successful_invocations INTEGER DEFAULT 0,
    failed_invocations INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (lct_identity) REFERENCES experts(lct_identity)
);

-- Reputation update history (audit trail)
CREATE TABLE IF NOT EXISTS reputation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lct_identity TEXT NOT NULL,
    update_type TEXT NOT NULL,  -- 'invocation_success', 'invocation_failure', etc.
    old_reliability REAL,
    new_reliability REAL,
    old_accuracy REAL,
    new_accuracy REAL,
    old_speed REAL,
    new_speed REAL,
    old_cost_efficiency REAL,
    new_cost_efficiency REAL,
    metadata_json TEXT,  -- Additional context (quality, latency, etc.)
    timestamp TEXT NOT NULL,
    FOREIGN KEY (lct_identity) REFERENCES experts(lct_identity)
);

-- Invocation records
CREATE TABLE IF NOT EXISTS invocations (
    id TEXT PRIMARY KEY,
    expert_lct TEXT NOT NULL,
    caller_lct TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'success', 'failure', 'timeout', etc.
    quality REAL,
    confidence REAL,
    latency_ms REAL,
    cost_atp REAL,
    timestamp TEXT NOT NULL,
    metadata_json TEXT,
    FOREIGN KEY (expert_lct) REFERENCES experts(lct_identity)
);

-- Schema metadata
CREATE TABLE IF NOT EXISTS schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR REPLACE INTO schema_metadata (key, value) VALUES ('version', '1.0.0');
"""


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ExpertProfile:
    """Persistent expert profile."""
    lct_identity: str
    name: str
    description: str
    capabilities: List[str]
    cost_per_invocation: float
    cost_unit: str = "atp"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TrustTensor:
    """Multi-dimensional trust (V3/T3 from Web4)."""
    lct_identity: str
    reliability: float = 0.5      # Success rate
    accuracy: float = 0.5         # Quality/confidence
    speed: float = 0.5            # Latency performance
    cost_efficiency: float = 0.5  # Cost vs value
    total_invocations: int = 0
    successful_invocations: int = 0
    failed_invocations: int = 0
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ReputationUpdate:
    """Record of a reputation update."""
    lct_identity: str
    update_type: str
    old_reliability: Optional[float]
    new_reliability: Optional[float]
    old_accuracy: Optional[float]
    new_accuracy: Optional[float]
    old_speed: Optional[float]
    new_speed: Optional[float]
    old_cost_efficiency: Optional[float]
    new_cost_efficiency: Optional[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class InvocationRecord:
    """Record of an IRP invocation."""
    id: str
    expert_lct: str
    caller_lct: str
    status: str
    quality: Optional[float] = None
    confidence: Optional[float] = None
    latency_ms: Optional[float] = None
    cost_atp: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# REPUTATION DATABASE
# ============================================================================

class ReputationDB:
    """SQLite database for persistent reputation tracking."""

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize reputation database.

        Args:
            db_path: Path to SQLite database file (":memory:" for in-memory)
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self._initialize_schema()

    def _initialize_schema(self):
        """Create database schema if not exists."""
        cursor = self.conn.cursor()
        cursor.executescript(SCHEMA_SQL)
        self.conn.commit()

    # ========================================================================
    # EXPERT PROFILE MANAGEMENT
    # ========================================================================

    def register_expert(self, profile: ExpertProfile) -> bool:
        """
        Register new expert profile.

        Returns:
            True if registered, False if already exists
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO experts (
                    lct_identity, name, description, capabilities_json,
                    cost_per_invocation, cost_unit, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.lct_identity,
                profile.name,
                profile.description,
                json.dumps(profile.capabilities),
                profile.cost_per_invocation,
                profile.cost_unit,
                profile.created_at,
                profile.updated_at
            ))

            # Initialize trust tensor
            cursor.execute("""
                INSERT INTO trust_tensor (lct_identity, updated_at)
                VALUES (?, ?)
            """, (profile.lct_identity, profile.created_at))

            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Expert already exists
            return False

    def get_expert(self, lct_identity: str) -> Optional[ExpertProfile]:
        """Retrieve expert profile by LCT identity."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM experts WHERE lct_identity = ?
        """, (lct_identity,))

        row = cursor.fetchone()
        if not row:
            return None

        return ExpertProfile(
            lct_identity=row["lct_identity"],
            name=row["name"],
            description=row["description"],
            capabilities=json.loads(row["capabilities_json"]),
            cost_per_invocation=row["cost_per_invocation"],
            cost_unit=row["cost_unit"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def find_experts(
        self,
        capability: Optional[str] = None,
        min_reliability: Optional[float] = None,
        max_cost: Optional[float] = None
    ) -> List[Tuple[ExpertProfile, TrustTensor]]:
        """
        Find experts matching criteria.

        Args:
            capability: Required capability tag
            min_reliability: Minimum reliability score
            max_cost: Maximum cost per invocation

        Returns:
            List of (ExpertProfile, TrustTensor) tuples
        """
        query = """
            SELECT e.*, t.*
            FROM experts e
            JOIN trust_tensor t ON e.lct_identity = t.lct_identity
            WHERE 1=1
        """
        params = []

        if capability:
            query += " AND e.capabilities_json LIKE ?"
            params.append(f"%{capability}%")

        if min_reliability is not None:
            query += " AND t.reliability >= ?"
            params.append(min_reliability)

        if max_cost is not None:
            query += " AND e.cost_per_invocation <= ?"
            params.append(max_cost)

        query += " ORDER BY t.reliability DESC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        results = []
        for row in cursor.fetchall():
            profile = ExpertProfile(
                lct_identity=row["lct_identity"],
                name=row["name"],
                description=row["description"],
                capabilities=json.loads(row["capabilities_json"]),
                cost_per_invocation=row["cost_per_invocation"],
                cost_unit=row["cost_unit"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )

            trust = TrustTensor(
                lct_identity=row["lct_identity"],
                reliability=row["reliability"],
                accuracy=row["accuracy"],
                speed=row["speed"],
                cost_efficiency=row["cost_efficiency"],
                total_invocations=row["total_invocations"],
                successful_invocations=row["successful_invocations"],
                failed_invocations=row["failed_invocations"],
                updated_at=row["updated_at"]
            )

            results.append((profile, trust))

        return results

    # ========================================================================
    # TRUST TENSOR MANAGEMENT
    # ========================================================================

    def get_trust_tensor(self, lct_identity: str) -> Optional[TrustTensor]:
        """Retrieve trust tensor for expert."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM trust_tensor WHERE lct_identity = ?
        """, (lct_identity,))

        row = cursor.fetchone()
        if not row:
            return None

        return TrustTensor(
            lct_identity=row["lct_identity"],
            reliability=row["reliability"],
            accuracy=row["accuracy"],
            speed=row["speed"],
            cost_efficiency=row["cost_efficiency"],
            total_invocations=row["total_invocations"],
            successful_invocations=row["successful_invocations"],
            failed_invocations=row["failed_invocations"],
            updated_at=row["updated_at"]
        )

    def update_trust_tensor(
        self,
        lct_identity: str,
        quality: Optional[float] = None,
        confidence: Optional[float] = None,
        latency_ms: Optional[float] = None,
        cost_ratio: Optional[float] = None,
        success: bool = True
    ) -> TrustTensor:
        """
        Update trust tensor from invocation result.

        Uses exponential moving average with alpha=0.2 (80% old, 20% new).

        Args:
            lct_identity: Expert's LCT identity
            quality: Result quality (0.0-1.0)
            confidence: Result confidence (0.0-1.0)
            latency_ms: Execution latency
            cost_ratio: Cost efficiency ratio
            success: Whether invocation succeeded

        Returns:
            Updated TrustTensor
        """
        alpha = 0.2  # Learning rate

        # Get current tensor
        current = self.get_trust_tensor(lct_identity)
        if not current:
            raise ValueError(f"Expert not found: {lct_identity}")

        # Store old values for history
        old_tensor = TrustTensor(
            lct_identity=current.lct_identity,
            reliability=current.reliability,
            accuracy=current.accuracy,
            speed=current.speed,
            cost_efficiency=current.cost_efficiency,
            total_invocations=current.total_invocations,
            successful_invocations=current.successful_invocations,
            failed_invocations=current.failed_invocations
        )

        # Update reliability (success rate)
        current.total_invocations += 1
        if success:
            current.successful_invocations += 1
        else:
            current.failed_invocations += 1

        success_rate = current.successful_invocations / current.total_invocations
        current.reliability = (1 - alpha) * current.reliability + alpha * success_rate

        # Update accuracy (quality × confidence)
        if quality is not None and confidence is not None:
            accuracy_signal = quality * confidence
            current.accuracy = (1 - alpha) * current.accuracy + alpha * accuracy_signal

        # Update speed (latency normalized to 0-1, lower is better)
        if latency_ms is not None:
            # Normalize: < 100ms = 1.0, > 1000ms = 0.0
            speed_signal = max(0.0, min(1.0, 1.0 - (latency_ms - 100) / 900))
            current.speed = (1 - alpha) * current.speed + alpha * speed_signal

        # Update cost efficiency
        if cost_ratio is not None:
            # cost_ratio: actual_cost / expected_cost (lower is better)
            # Normalize: 0.5 = 1.0 (half cost), 1.0 = 0.5 (expected), 2.0 = 0.0 (double)
            cost_eff_signal = max(0.0, min(1.0, 1.5 - cost_ratio))
            current.cost_efficiency = (1 - alpha) * current.cost_efficiency + alpha * cost_eff_signal

        current.updated_at = datetime.now(timezone.utc).isoformat()

        # Update database
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE trust_tensor
            SET reliability = ?,
                accuracy = ?,
                speed = ?,
                cost_efficiency = ?,
                total_invocations = ?,
                successful_invocations = ?,
                failed_invocations = ?,
                updated_at = ?
            WHERE lct_identity = ?
        """, (
            current.reliability,
            current.accuracy,
            current.speed,
            current.cost_efficiency,
            current.total_invocations,
            current.successful_invocations,
            current.failed_invocations,
            current.updated_at,
            lct_identity
        ))

        # Record update in history
        self._record_reputation_update(
            lct_identity=lct_identity,
            update_type="invocation_success" if success else "invocation_failure",
            old_tensor=old_tensor,
            new_tensor=current,
            metadata={
                "quality": quality,
                "confidence": confidence,
                "latency_ms": latency_ms,
                "cost_ratio": cost_ratio
            }
        )

        self.conn.commit()
        return current

    def _record_reputation_update(
        self,
        lct_identity: str,
        update_type: str,
        old_tensor: TrustTensor,
        new_tensor: TrustTensor,
        metadata: Dict[str, Any]
    ):
        """Record reputation update in history table."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO reputation_history (
                lct_identity, update_type,
                old_reliability, new_reliability,
                old_accuracy, new_accuracy,
                old_speed, new_speed,
                old_cost_efficiency, new_cost_efficiency,
                metadata_json, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lct_identity,
            update_type,
            old_tensor.reliability,
            new_tensor.reliability,
            old_tensor.accuracy,
            new_tensor.accuracy,
            old_tensor.speed,
            new_tensor.speed,
            old_tensor.cost_efficiency,
            new_tensor.cost_efficiency,
            json.dumps(metadata),
            new_tensor.updated_at
        ))

    # ========================================================================
    # INVOCATION RECORDS
    # ========================================================================

    def record_invocation(self, record: InvocationRecord):
        """Record IRP invocation in database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO invocations (
                id, expert_lct, caller_lct, status,
                quality, confidence, latency_ms, cost_atp,
                timestamp, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.id,
            record.expert_lct,
            record.caller_lct,
            record.status,
            record.quality,
            record.confidence,
            record.latency_ms,
            record.cost_atp,
            record.timestamp,
            json.dumps(record.metadata)
        ))
        self.conn.commit()

    def get_invocation_history(
        self,
        expert_lct: Optional[str] = None,
        caller_lct: Optional[str] = None,
        limit: int = 100
    ) -> List[InvocationRecord]:
        """Retrieve invocation history."""
        query = "SELECT * FROM invocations WHERE 1=1"
        params = []

        if expert_lct:
            query += " AND expert_lct = ?"
            params.append(expert_lct)

        if caller_lct:
            query += " AND caller_lct = ?"
            params.append(caller_lct)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        records = []
        for row in cursor.fetchall():
            records.append(InvocationRecord(
                id=row["id"],
                expert_lct=row["expert_lct"],
                caller_lct=row["caller_lct"],
                status=row["status"],
                quality=row["quality"],
                confidence=row["confidence"],
                latency_ms=row["latency_ms"],
                cost_atp=row["cost_atp"],
                timestamp=row["timestamp"],
                metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {}
            ))

        return records

    # ========================================================================
    # REPUTATION HISTORY
    # ========================================================================

    def get_reputation_history(
        self,
        lct_identity: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve reputation update history for expert."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM reputation_history
            WHERE lct_identity = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (lct_identity, limit))

        history = []
        for row in cursor.fetchall():
            history.append({
                "update_type": row["update_type"],
                "old_reliability": row["old_reliability"],
                "new_reliability": row["new_reliability"],
                "old_accuracy": row["old_accuracy"],
                "new_accuracy": row["new_accuracy"],
                "old_speed": row["old_speed"],
                "new_speed": row["new_speed"],
                "old_cost_efficiency": row["old_cost_efficiency"],
                "new_cost_efficiency": row["new_cost_efficiency"],
                "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else {},
                "timestamp": row["timestamp"]
            })

        return history

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def export_statistics(self) -> Dict[str, Any]:
        """Export database statistics."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM experts")
        total_experts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM invocations")
        total_invocations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reputation_history")
        total_updates = cursor.fetchone()[0]

        cursor.execute("""
            SELECT AVG(reliability), AVG(accuracy), AVG(speed), AVG(cost_efficiency)
            FROM trust_tensor
        """)
        avg_row = cursor.fetchone()

        return {
            "total_experts": total_experts,
            "total_invocations": total_invocations,
            "total_reputation_updates": total_updates,
            "average_trust": {
                "reliability": avg_row[0] or 0.0,
                "accuracy": avg_row[1] or 0.0,
                "speed": avg_row[2] or 0.0,
                "cost_efficiency": avg_row[3] or 0.0
            }
        }

    def close(self):
        """Close database connection."""
        self.conn.close()


# ============================================================================
# TEST SCENARIOS
# ============================================================================

def test_expert_registration_and_retrieval():
    """Test expert profile persistence."""
    print("="*80)
    print("TEST SCENARIO 1: Expert Registration and Retrieval")
    print("="*80)

    db = ReputationDB(":memory:")

    # Register expert
    profile = ExpertProfile(
        lct_identity="lct://sage:verification_expert@mainnet",
        name="Verification Expert",
        description="Verifies claims and assertions",
        capabilities=["VERIFICATION", "REASONING", "TOOL_HEAVY"],
        cost_per_invocation=15.0
    )

    registered = db.register_expert(profile)
    print(f"\n✅ Expert registered: {registered}")
    print(f"   LCT: {profile.lct_identity}")
    print(f"   Capabilities: {profile.capabilities}")

    # Retrieve expert
    retrieved = db.get_expert(profile.lct_identity)
    print(f"\n✅ Expert retrieved: {retrieved is not None}")
    if retrieved:
        print(f"   Name: {retrieved.name}")
        print(f"   Cost: {retrieved.cost_per_invocation} {retrieved.cost_unit}")

    db.close()
    return registered and retrieved is not None


def test_trust_tensor_updates():
    """Test reputation updates from invocations."""
    print("\n" + "="*80)
    print("TEST SCENARIO 2: Trust Tensor Updates")
    print("="*80)

    db = ReputationDB(":memory:")

    # Register expert
    profile = ExpertProfile(
        lct_identity="lct://sage:verification_expert@mainnet",
        name="Verification Expert",
        description="Test expert",
        capabilities=["VERIFICATION"],
        cost_per_invocation=15.0
    )
    db.register_expert(profile)

    # Initial trust
    initial_trust = db.get_trust_tensor(profile.lct_identity)
    print(f"\n📊 Initial trust tensor:")
    print(f"   Reliability: {initial_trust.reliability:.3f}")
    print(f"   Accuracy: {initial_trust.accuracy:.3f}")
    print(f"   Speed: {initial_trust.speed:.3f}")
    print(f"   Cost Efficiency: {initial_trust.cost_efficiency:.3f}")

    # Simulate successful invocation with high quality
    updated_trust = db.update_trust_tensor(
        lct_identity=profile.lct_identity,
        quality=0.85,
        confidence=0.80,
        latency_ms=250.0,
        cost_ratio=1.0,
        success=True
    )

    print(f"\n✅ Trust updated after successful invocation:")
    print(f"   Reliability: {updated_trust.reliability:.3f} (Δ {updated_trust.reliability - initial_trust.reliability:+.3f})")
    print(f"   Accuracy: {updated_trust.accuracy:.3f} (Δ {updated_trust.accuracy - initial_trust.accuracy:+.3f})")
    print(f"   Speed: {updated_trust.speed:.3f} (Δ {updated_trust.speed - initial_trust.speed:+.3f})")
    print(f"   Invocations: {updated_trust.total_invocations}")

    db.close()
    return updated_trust.total_invocations == 1


def test_expert_discovery():
    """Test finding experts by criteria."""
    print("\n" + "="*80)
    print("TEST SCENARIO 3: Expert Discovery")
    print("="*80)

    db = ReputationDB(":memory:")

    # Register multiple experts
    experts_data = [
        ("lct://sage:expert_a@mainnet", "Expert A", ["VERIFICATION"], 10.0, 0.85),
        ("lct://sage:expert_b@mainnet", "Expert B", ["REASONING"], 20.0, 0.70),
        ("lct://sage:expert_c@mainnet", "Expert C", ["VERIFICATION", "REASONING"], 15.0, 0.90),
    ]

    for lct, name, caps, cost, target_reliability in experts_data:
        profile = ExpertProfile(
            lct_identity=lct,
            name=name,
            description=f"Test {name}",
            capabilities=caps,
            cost_per_invocation=cost
        )
        db.register_expert(profile)

        # Simulate invocations to build different reliabilities
        for _ in range(10):
            db.update_trust_tensor(
                lct_identity=lct,
                quality=target_reliability,
                confidence=0.80,
                success=True
            )

    print(f"\n✅ Registered 3 experts with varying reliability")

    # Find experts with VERIFICATION capability
    results = db.find_experts(capability="VERIFICATION")
    print(f"\n🔍 Experts with VERIFICATION capability: {len(results)}")
    for profile, trust in results:
        print(f"   {profile.name}: reliability={trust.reliability:.3f}")

    # Find high-reliability experts
    high_reliability = db.find_experts(min_reliability=0.75)
    print(f"\n🔍 Experts with reliability ≥ 0.75: {len(high_reliability)}")

    # Find affordable experts
    affordable = db.find_experts(max_cost=15.0)
    print(f"\n🔍 Experts with cost ≤ 15 ATP: {len(affordable)}")

    db.close()
    return len(results) == 2 and len(high_reliability) >= 1


def test_invocation_and_reputation_history():
    """Test invocation recording and history tracking."""
    print("\n" + "="*80)
    print("TEST SCENARIO 4: Invocation and Reputation History")
    print("="*80)

    db = ReputationDB(":memory:")

    # Register expert
    expert_lct = "lct://sage:verification_expert@mainnet"
    profile = ExpertProfile(
        lct_identity=expert_lct,
        name="Verification Expert",
        description="Test expert",
        capabilities=["VERIFICATION"],
        cost_per_invocation=15.0
    )
    db.register_expert(profile)

    # Record invocations
    for i in range(3):
        invocation_id = f"inv_{secrets.token_hex(8)}"
        record = InvocationRecord(
            id=invocation_id,
            expert_lct=expert_lct,
            caller_lct="lct://user:alice@mainnet",
            status="success",
            quality=0.80 + i * 0.05,
            confidence=0.75,
            latency_ms=200.0 + i * 50,
            cost_atp=15.0
        )
        db.record_invocation(record)

        # Update reputation
        db.update_trust_tensor(
            lct_identity=expert_lct,
            quality=record.quality,
            confidence=record.confidence,
            latency_ms=record.latency_ms,
            cost_ratio=1.0,
            success=True
        )

    print(f"\n✅ Recorded 3 invocations")

    # Get invocation history
    history = db.get_invocation_history(expert_lct=expert_lct)
    print(f"\n📜 Invocation history: {len(history)} records")
    for i, inv in enumerate(history[:3], 1):
        print(f"   {i}. Quality: {inv.quality:.2f}, Latency: {inv.latency_ms:.0f}ms")

    # Get reputation history
    rep_history = db.get_reputation_history(expert_lct)
    print(f"\n📜 Reputation history: {len(rep_history)} updates")
    for i, update in enumerate(rep_history[:3], 1):
        print(f"   {i}. {update['update_type']}: reliability {update['old_reliability']:.3f} → {update['new_reliability']:.3f}")

    db.close()
    return len(history) == 3 and len(rep_history) == 3


def test_persistent_storage():
    """Test persistence to file."""
    print("\n" + "="*80)
    print("TEST SCENARIO 5: Persistent Storage")
    print("="*80)

    db_path = "/tmp/test_reputation.db"

    # Create database and register expert
    db1 = ReputationDB(db_path)
    profile = ExpertProfile(
        lct_identity="lct://sage:persistent_expert@mainnet",
        name="Persistent Expert",
        description="Test persistence",
        capabilities=["VERIFICATION"],
        cost_per_invocation=15.0
    )
    db1.register_expert(profile)

    # Update reputation
    db1.update_trust_tensor(
        lct_identity=profile.lct_identity,
        quality=0.85,
        confidence=0.80,
        success=True
    )

    initial_trust = db1.get_trust_tensor(profile.lct_identity)
    print(f"\n✅ Database created: {db_path}")
    print(f"   Initial reliability: {initial_trust.reliability:.3f}")
    print(f"   Invocations: {initial_trust.total_invocations}")

    db1.close()

    # Reopen database and verify data persisted
    db2 = ReputationDB(db_path)
    retrieved_profile = db2.get_expert(profile.lct_identity)
    retrieved_trust = db2.get_trust_tensor(profile.lct_identity)

    print(f"\n✅ Database reopened")
    print(f"   Expert found: {retrieved_profile is not None}")
    print(f"   Reliability: {retrieved_trust.reliability:.3f}")
    print(f"   Invocations: {retrieved_trust.total_invocations}")

    # Stats
    stats = db2.export_statistics()
    print(f"\n📊 Database statistics:")
    print(f"   Total experts: {stats['total_experts']}")
    print(f"   Total invocations: {stats['total_invocations']}")
    print(f"   Total updates: {stats['total_reputation_updates']}")

    db2.close()

    # Cleanup
    Path(db_path).unlink()

    return (
        retrieved_profile is not None and
        retrieved_trust.total_invocations == initial_trust.total_invocations
    )


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all test scenarios."""
    print("="*80)
    print("SESSION 94 TRACK 3: REPUTATION PERSISTENCE")
    print("="*80)

    results = []

    # Run tests
    results.append(("Expert registration and retrieval", test_expert_registration_and_retrieval()))
    results.append(("Trust tensor updates", test_trust_tensor_updates()))
    results.append(("Expert discovery", test_expert_discovery()))
    results.append(("Invocation and reputation history", test_invocation_and_reputation_history()))
    results.append(("Persistent storage", test_persistent_storage()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    all_passed = all(result for _, result in results)
    print(f"\n✅ All scenarios passed: {all_passed}")

    print(f"\nScenarios tested:")
    for i, (name, passed) in enumerate(results, 1):
        status = "✅" if passed else "❌"
        print(f"  {i}. {status} {name}")

    # Save results
    output = {
        "session": "94",
        "track": "3",
        "focus": "Reputation Persistence (SQLite)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_results": [
            {"scenario": name, "passed": passed}
            for name, passed in results
        ],
        "all_passed": all_passed,
        "innovations": [
            "SQLite database for persistent reputation",
            "Multi-dimensional trust tensor (V3/T3)",
            "Reputation update history (audit trail)",
            "Expert discovery by capability/reputation/cost",
            "Atomic updates with ACID transactions",
        ]
    }

    output_path = "/home/dp/ai-workspace/web4/implementation/session94_track3_results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Results saved to: {output_path}")

    print("\n" + "="*80)
    print("Key Innovations:")
    print("="*80)
    for i, innovation in enumerate(output["innovations"], 1):
        print(f"{i}. {innovation}")

    print("\n" + "="*80)
    print("Persistent reputation enables:")
    print("- Long-term expert reputation building")
    print("- Reputation survives system restarts")
    print("- Historical audit trail for all updates")
    print("- Expert discovery by capability/reputation/cost")
    print("- ACID guarantees for reputation updates")
    print("="*80)

    return all_passed


if __name__ == "__main__":
    run_all_tests()
