#!/usr/bin/env python3
"""
Heartbeat-Driven Ledger for Web4 Hardbound Teams.

Instead of fixed-interval blocks (like traditional blockchains), this ledger
creates blocks driven by the team's metabolic heartbeat. Active teams produce
blocks frequently; dormant teams produce sparse blocks.

Key concepts:
- Blocks are sealed by heartbeat events, not wall-clock timers
- The heartbeat interval adapts to the team's metabolic state
- Each block contains all transactions since the previous heartbeat
- Empty heartbeats (no transactions) still produce a block (presence proof)
- The block chain maintains hash integrity across metabolic state transitions

This implements the "Idle isn't" principle: even at rest, the team proves
its continued existence through sentinel heartbeats.
"""

import hashlib
import json
import math
import sqlite3
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple


# ---------------------------------------------------------------------------
# Metabolic States
# ---------------------------------------------------------------------------

class MetabolicState(Enum):
    """Team metabolic states (from SOCIETY_METABOLIC_STATES spec)."""
    ACTIVE = "active"          # Full operations
    REST = "rest"              # Reduced, predictable low activity
    SLEEP = "sleep"            # Deep rest, minimal maintenance
    HIBERNATION = "hibernation"  # Long-term dormancy
    TORPOR = "torpor"          # Emergency conservation
    ESTIVATION = "estivation"  # Protective dormancy (hostile environment)
    DREAMING = "dreaming"      # Memory consolidation / reorganization
    MOLTING = "molting"        # Structural renewal (vulnerable)


# Energy multipliers per state (from spec section 4.1)
STATE_ENERGY_MULTIPLIER = {
    MetabolicState.ACTIVE: 1.0,
    MetabolicState.REST: 0.4,
    MetabolicState.SLEEP: 0.15,
    MetabolicState.HIBERNATION: 0.05,
    MetabolicState.TORPOR: 0.02,
    MetabolicState.ESTIVATION: 0.10,
    MetabolicState.DREAMING: 0.20,
    MetabolicState.MOLTING: 0.60,
}

# Heartbeat interval per state (seconds)
# Active: every 60s, Rest: every 5min, Sleep: every 30min, etc.
STATE_HEARTBEAT_INTERVAL = {
    MetabolicState.ACTIVE: 60,
    MetabolicState.REST: 300,
    MetabolicState.SLEEP: 1800,
    MetabolicState.HIBERNATION: 3600,
    MetabolicState.TORPOR: 7200,
    MetabolicState.ESTIVATION: 1800,
    MetabolicState.DREAMING: 600,
    MetabolicState.MOLTING: 120,
}

# Trust decay rate multiplier per state (from spec section 5.1)
STATE_TRUST_DECAY_RATE = {
    MetabolicState.ACTIVE: 1.0,     # Normal
    MetabolicState.REST: 0.9,       # 90% rate
    MetabolicState.SLEEP: 0.1,      # 10% rate
    MetabolicState.HIBERNATION: 0.0,  # Frozen
    MetabolicState.TORPOR: 0.0,     # Frozen
    MetabolicState.ESTIVATION: 0.0,  # Internal only
    MetabolicState.DREAMING: 0.0,   # Recalibrating
    MetabolicState.MOLTING: 1.2,    # Slightly accelerated (vulnerability)
}


# ---------------------------------------------------------------------------
# Transition Rules
# ---------------------------------------------------------------------------

# Valid state transitions: {from_state: [to_states]}
VALID_TRANSITIONS = {
    MetabolicState.ACTIVE: [
        MetabolicState.REST, MetabolicState.SLEEP, MetabolicState.TORPOR,
        MetabolicState.DREAMING, MetabolicState.MOLTING, MetabolicState.ESTIVATION,
    ],
    MetabolicState.REST: [
        MetabolicState.ACTIVE, MetabolicState.SLEEP,
    ],
    MetabolicState.SLEEP: [
        MetabolicState.ACTIVE, MetabolicState.HIBERNATION,
    ],
    MetabolicState.HIBERNATION: [
        MetabolicState.ACTIVE,
    ],
    MetabolicState.TORPOR: [
        MetabolicState.ACTIVE, MetabolicState.HIBERNATION,
    ],
    MetabolicState.ESTIVATION: [
        MetabolicState.ACTIVE, MetabolicState.HIBERNATION,
    ],
    MetabolicState.DREAMING: [
        MetabolicState.ACTIVE,
    ],
    MetabolicState.MOLTING: [
        MetabolicState.ACTIVE,
    ],
}

# Auto-transition triggers: {from_state: (condition_name, to_state, threshold)}
AUTO_TRANSITIONS = {
    MetabolicState.ACTIVE: [
        ("no_transactions", MetabolicState.REST, 3600),  # 1h no txns
        ("atp_critical", MetabolicState.TORPOR, 0.10),   # ATP < 10%
    ],
    MetabolicState.REST: [
        ("transaction_received", MetabolicState.ACTIVE, None),
        ("no_activity", MetabolicState.SLEEP, 21600),     # 6h no activity
    ],
    MetabolicState.SLEEP: [
        ("wake_trigger", MetabolicState.ACTIVE, None),
        ("no_activity", MetabolicState.HIBERNATION, 2592000),  # 30 days
    ],
}


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class Transaction:
    """A single ledger transaction within a block."""
    tx_id: str
    tx_type: str          # "r6_request", "member_added", "trust_update", etc.
    actor_lct: str
    target_lct: Optional[str]
    data: Dict[str, Any]
    timestamp: str
    atp_cost: float = 0.0

    @staticmethod
    def create(tx_type: str, actor_lct: str, data: Dict[str, Any],
               target_lct: Optional[str] = None, atp_cost: float = 0.0) -> 'Transaction':
        return Transaction(
            tx_id=f"tx:{uuid.uuid4().hex[:12]}",
            tx_type=tx_type,
            actor_lct=actor_lct,
            target_lct=target_lct,
            data=data,
            timestamp=datetime.now(timezone.utc).isoformat() + "Z",
            atp_cost=atp_cost,
        )


@dataclass
class Block:
    """A ledger block sealed by a heartbeat event."""
    block_number: int
    previous_hash: str
    block_hash: str = ""
    timestamp: str = ""
    metabolic_state: str = "active"
    heartbeat_interval: float = 60.0   # actual seconds since last block
    expected_interval: float = 60.0    # expected seconds for current state
    transactions: List[Dict] = field(default_factory=list)
    tx_count: int = 0
    energy_cost: float = 0.0           # ATP cost of this block
    sentinel_witness: Optional[str] = None  # LCT of witness that sealed block
    team_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        """Compute block hash from contents."""
        payload = json.dumps({
            "block_number": self.block_number,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "metabolic_state": self.metabolic_state,
            "heartbeat_interval": self.heartbeat_interval,
            "tx_count": self.tx_count,
            "transactions": self.transactions,
            "energy_cost": self.energy_cost,
            "team_id": self.team_id,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def seal(self) -> str:
        """Seal the block by computing its hash."""
        self.block_hash = self.compute_hash()
        return self.block_hash


@dataclass
class MetabolicTransition:
    """Record of a metabolic state transition."""
    from_state: str
    to_state: str
    trigger: str          # What caused the transition
    timestamp: str
    block_number: int     # Block at which transition occurred
    atp_cost: float = 0.0  # Wake penalty or transition cost
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Heartbeat-Driven Ledger
# ---------------------------------------------------------------------------

class HeartbeatLedger:
    """
    Ledger driven by team metabolic heartbeat.

    Instead of producing blocks at fixed intervals, blocks are produced
    when the team's heartbeat fires. The heartbeat interval adapts to
    the team's current metabolic state.

    Example:
        ledger = HeartbeatLedger("web4:team:abc123")

        # Submit transactions during active state
        ledger.submit_transaction("r6_request", actor_lct, data)
        ledger.submit_transaction("trust_update", actor_lct, data)

        # Heartbeat fires -> seal block with pending transactions
        block = ledger.heartbeat()

        # Team goes quiet -> auto-transition to REST
        ledger.transition_state(MetabolicState.REST, trigger="no_transactions")

        # Now heartbeats are every 5 minutes instead of 60 seconds
        block = ledger.heartbeat()  # sparse block, may be empty
    """

    def __init__(self, team_id: str, db_path: Optional[Path] = None):
        self.team_id = team_id

        if db_path is None:
            db_path = Path.home() / ".web4" / "heartbeat_ledger.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory pending transactions (not yet in a block)
        self._pending_transactions: List[Transaction] = []
        self._in_transition = False  # Guard against recursive transitions

        # Current metabolic state
        self._state = MetabolicState.ACTIVE
        self._state_entered_at = datetime.now(timezone.utc)
        self._last_heartbeat_at = datetime.now(timezone.utc)
        self._last_transaction_at: Optional[datetime] = None

        self._init_db()
        self._load_state()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout = 30000")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS blocks (
                    block_number INTEGER NOT NULL,
                    team_id TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    block_hash TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metabolic_state TEXT NOT NULL,
                    heartbeat_interval REAL NOT NULL,
                    expected_interval REAL NOT NULL,
                    tx_count INTEGER NOT NULL,
                    transactions TEXT NOT NULL,
                    energy_cost REAL NOT NULL,
                    sentinel_witness TEXT,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS metabolic_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_id TEXT NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    trigger TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    block_number INTEGER NOT NULL,
                    atp_cost REAL DEFAULT 0.0,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS team_state (
                    team_id TEXT PRIMARY KEY,
                    current_state TEXT NOT NULL,
                    state_entered_at TEXT NOT NULL,
                    last_heartbeat_at TEXT NOT NULL,
                    last_transaction_at TEXT,
                    total_blocks INTEGER DEFAULT 0,
                    total_transactions INTEGER DEFAULT 0,
                    total_energy_spent REAL DEFAULT 0.0,
                    atp_reserves REAL DEFAULT 1000.0
                );

                CREATE UNIQUE INDEX IF NOT EXISTS idx_blocks_team_number ON blocks(team_id, block_number);
                CREATE INDEX IF NOT EXISTS idx_blocks_team ON blocks(team_id);
                CREATE INDEX IF NOT EXISTS idx_transitions_team ON metabolic_transitions(team_id);
            """)

    def _load_state(self):
        """Load persisted state or initialize."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM team_state WHERE team_id = ?", (self.team_id,)
            ).fetchone()

            if row:
                self._state = MetabolicState(row["current_state"])
                self._state_entered_at = datetime.fromisoformat(row["state_entered_at"])
                self._last_heartbeat_at = datetime.fromisoformat(row["last_heartbeat_at"])
                if row["last_transaction_at"]:
                    self._last_transaction_at = datetime.fromisoformat(row["last_transaction_at"])
            else:
                # Initialize team state
                now = datetime.now(timezone.utc).isoformat()
                conn.execute("""
                    INSERT INTO team_state
                    (team_id, current_state, state_entered_at, last_heartbeat_at)
                    VALUES (?, ?, ?, ?)
                """, (self.team_id, self._state.value, now, now))

    def _save_state(self):
        """Persist current state."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE team_state SET
                    current_state = ?,
                    state_entered_at = ?,
                    last_heartbeat_at = ?,
                    last_transaction_at = ?
                WHERE team_id = ?
            """, (
                self._state.value,
                self._state_entered_at.isoformat(),
                self._last_heartbeat_at.isoformat(),
                self._last_transaction_at.isoformat() if self._last_transaction_at else None,
                self.team_id,
            ))

    # -------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------

    @property
    def state(self) -> MetabolicState:
        return self._state

    @property
    def heartbeat_interval(self) -> int:
        """Current expected heartbeat interval in seconds."""
        return STATE_HEARTBEAT_INTERVAL[self._state]

    @property
    def energy_multiplier(self) -> float:
        return STATE_ENERGY_MULTIPLIER[self._state]

    @property
    def trust_decay_rate(self) -> float:
        return STATE_TRUST_DECAY_RATE[self._state]

    @property
    def pending_count(self) -> int:
        return len(self._pending_transactions)

    # -------------------------------------------------------------------
    # Transaction Submission
    # -------------------------------------------------------------------

    def submit_transaction(self, tx_type: str, actor_lct: str,
                           data: Dict[str, Any],
                           target_lct: Optional[str] = None,
                           atp_cost: float = 0.0) -> Transaction:
        """
        Submit a transaction to the pending pool.

        Transactions accumulate until the next heartbeat seals them into a block.

        In dormant states (sleep, hibernation, torpor), transactions may trigger
        a wake event depending on the metabolic rules.
        """
        tx = Transaction.create(tx_type, actor_lct, data, target_lct, atp_cost)
        self._pending_transactions.append(tx)
        self._last_transaction_at = datetime.now(timezone.utc)

        # Check if transaction should wake the team (guard against recursion)
        if not self._in_transition and self._state in (MetabolicState.REST,):
            # REST -> ACTIVE on any transaction
            self.transition_state(MetabolicState.ACTIVE, trigger="transaction_received")

        return tx

    # -------------------------------------------------------------------
    # Heartbeat (Block Production)
    # -------------------------------------------------------------------

    def heartbeat(self, sentinel_lct: Optional[str] = None) -> Block:
        """
        Fire a heartbeat, sealing pending transactions into a new block.

        This is the core mechanism: the heartbeat drives the ledger.
        - Active teams: heartbeat every ~60s, blocks contain many transactions
        - Resting teams: heartbeat every ~5min, blocks may be empty
        - Sleeping teams: heartbeat every ~30min, blocks are empty (presence proof)
        - Hibernating: heartbeat every ~1h, single sentinel witnesses

        Returns the sealed block.
        """
        now = datetime.now(timezone.utc)
        actual_interval = (now - self._last_heartbeat_at).total_seconds()
        expected = float(self.heartbeat_interval)

        # Get previous block
        prev_block = self._get_latest_block()
        prev_hash = prev_block["block_hash"] if prev_block else "genesis"
        block_number = (prev_block["block_number"] + 1) if prev_block else 0

        # Gather pending transactions
        tx_dicts = [asdict(tx) for tx in self._pending_transactions]
        tx_count = len(tx_dicts)

        # Calculate energy cost for this block
        # Base cost scales with energy multiplier and actual time elapsed
        base_cost_per_second = 0.01  # 0.01 ATP/second at full active
        energy_cost = base_cost_per_second * actual_interval * self.energy_multiplier
        # Add per-transaction cost
        tx_energy = sum(tx.atp_cost for tx in self._pending_transactions)
        total_energy = energy_cost + tx_energy

        # Build block
        block = Block(
            block_number=block_number,
            previous_hash=prev_hash,
            timestamp=now.isoformat() + "Z",
            metabolic_state=self._state.value,
            heartbeat_interval=actual_interval,
            expected_interval=expected,
            transactions=tx_dicts,
            tx_count=tx_count,
            energy_cost=total_energy,
            sentinel_witness=sentinel_lct,
            team_id=self.team_id,
        )
        block.seal()

        # Persist block
        self._persist_block(block)

        # Update state
        self._pending_transactions.clear()
        self._last_heartbeat_at = now
        self._save_state()

        # Update aggregate stats
        self._update_stats(tx_count, total_energy)

        # Check auto-transitions
        self._check_auto_transitions(now)

        return block

    # -------------------------------------------------------------------
    # State Transitions
    # -------------------------------------------------------------------

    def transition_state(self, to_state: MetabolicState, trigger: str,
                         metadata: Optional[Dict] = None) -> MetabolicTransition:
        """
        Transition to a new metabolic state.

        Validates transition is legal per the state machine, records it on the
        ledger, and adjusts heartbeat parameters.
        """
        from_state = self._state
        self._in_transition = True

        try:
            return self._do_transition(from_state, to_state, trigger, metadata)
        finally:
            self._in_transition = False

    def _do_transition(self, from_state: MetabolicState, to_state: MetabolicState,
                       trigger: str, metadata: Optional[Dict]) -> MetabolicTransition:
        # Validate transition
        if to_state not in VALID_TRANSITIONS.get(from_state, []):
            raise ValueError(
                f"Invalid transition: {from_state.value} -> {to_state.value}. "
                f"Valid targets: {[s.value for s in VALID_TRANSITIONS.get(from_state, [])]}"
            )

        now = datetime.now(timezone.utc)

        # Calculate wake penalty if applicable
        atp_cost = self._calculate_transition_cost(from_state, to_state, now)

        # Get current block number
        prev_block = self._get_latest_block()
        block_number = (prev_block["block_number"] + 1) if prev_block else 0

        transition = MetabolicTransition(
            from_state=from_state.value,
            to_state=to_state.value,
            trigger=trigger,
            timestamp=now.isoformat() + "Z",
            block_number=block_number,
            atp_cost=atp_cost,
            metadata=metadata or {},
        )

        # Record transition
        self._persist_transition(transition)

        # Also submit as a transaction (so it appears in the next block)
        self.submit_transaction(
            tx_type="metabolic_transition",
            actor_lct=self.team_id,
            data={
                "from": from_state.value,
                "to": to_state.value,
                "trigger": trigger,
            },
            atp_cost=atp_cost,
        )

        # Update state
        self._state = to_state
        self._state_entered_at = now
        self._save_state()

        return transition

    def _calculate_transition_cost(self, from_state: MetabolicState,
                                   to_state: MetabolicState,
                                   now: datetime) -> float:
        """Calculate ATP cost of state transition (wake penalties etc)."""
        # Wake penalties for premature exit from dormant states
        if from_state in (MetabolicState.SLEEP, MetabolicState.HIBERNATION, MetabolicState.DREAMING):
            time_in_state = (now - self._state_entered_at).total_seconds()
            # Minimum expected durations
            min_durations = {
                MetabolicState.SLEEP: 3600,       # 1 hour minimum sleep
                MetabolicState.HIBERNATION: 86400,  # 1 day minimum hibernation
                MetabolicState.DREAMING: 600,      # 10 min minimum dream cycle
            }
            min_dur = min_durations.get(from_state, 0)
            if time_in_state < min_dur and min_dur > 0:
                incompleteness = 1 - (time_in_state / min_dur)
                penalties = {
                    MetabolicState.SLEEP: 10,
                    MetabolicState.HIBERNATION: 100,
                    MetabolicState.DREAMING: 50,
                }
                return penalties.get(from_state, 0) * incompleteness

        # Molting entry cost (preparing for vulnerability)
        if to_state == MetabolicState.MOLTING:
            return 25.0  # Fixed entry cost for structural renewal

        return 0.0

    def _check_auto_transitions(self, now: datetime):
        """Check if any auto-transition conditions are met."""
        rules = AUTO_TRANSITIONS.get(self._state, [])

        for condition, to_state, threshold in rules:
            if condition == "no_transactions" and threshold is not None:
                if self._last_transaction_at is None:
                    time_since = (now - self._state_entered_at).total_seconds()
                else:
                    time_since = (now - self._last_transaction_at).total_seconds()
                if time_since >= threshold:
                    self.transition_state(to_state, trigger=f"auto:{condition}")
                    return

            elif condition == "no_activity" and threshold is not None:
                if self._last_transaction_at is None:
                    time_since = (now - self._state_entered_at).total_seconds()
                else:
                    time_since = (now - self._last_transaction_at).total_seconds()
                if time_since >= threshold:
                    self.transition_state(to_state, trigger=f"auto:{condition}")
                    return

            elif condition == "atp_critical" and threshold is not None:
                reserves = self._get_atp_reserves()
                max_reserves = self._get_max_atp()
                if max_reserves > 0 and (reserves / max_reserves) < threshold:
                    self.transition_state(to_state, trigger=f"auto:{condition}")
                    return

    # -------------------------------------------------------------------
    # Metabolic Analytics
    # -------------------------------------------------------------------

    def get_metabolic_health(self) -> Dict[str, Any]:
        """
        Calculate team metabolic health metrics.

        Returns a health report with:
        - Heartbeat regularity (how close to expected intervals)
        - Energy efficiency (actual vs expected consumption)
        - Transaction density (txns per block)
        - State stability (time in current state)
        - Metabolic reliability score (predictable cycles build trust)
        """
        now = datetime.now(timezone.utc)

        # Recent blocks for analysis
        recent_blocks = self._get_recent_blocks(50)

        if not recent_blocks:
            return {
                "state": self._state.value,
                "heartbeat_regularity": 0.0,
                "energy_efficiency": 0.0,
                "transaction_density": 0.0,
                "state_stability": 0.0,
                "metabolic_reliability": 0.0,
                "blocks_analyzed": 0,
            }

        # Heartbeat regularity: how close actual intervals are to expected
        regularity_scores = []
        for b in recent_blocks:
            expected = b["expected_interval"]
            actual = b["heartbeat_interval"]
            if expected > 0:
                ratio = actual / expected
                # Perfect = 1.0, deviance penalized exponentially
                regularity = math.exp(-abs(math.log(max(ratio, 0.01))))
                regularity_scores.append(regularity)

        heartbeat_regularity = sum(regularity_scores) / len(regularity_scores) if regularity_scores else 0.0

        # Energy efficiency: lower actual vs expected is better
        total_energy = sum(b["energy_cost"] for b in recent_blocks)
        total_time = sum(b["heartbeat_interval"] for b in recent_blocks)
        expected_energy = total_time * 0.01  # base rate at active
        energy_efficiency = min(1.0, expected_energy / max(total_energy, 0.001))

        # Transaction density
        total_txns = sum(b["tx_count"] for b in recent_blocks)
        transaction_density = total_txns / len(recent_blocks)

        # State stability: longer in current state = more stable
        time_in_state = (now - self._state_entered_at).total_seconds()
        state_stability = min(1.0, time_in_state / 86400)  # normalize to 1 day

        # Metabolic reliability: composite score
        metabolic_reliability = (
            heartbeat_regularity * 0.35 +
            energy_efficiency * 0.25 +
            min(1.0, transaction_density / 10) * 0.20 +
            state_stability * 0.20
        )

        return {
            "state": self._state.value,
            "heartbeat_regularity": round(heartbeat_regularity, 4),
            "energy_efficiency": round(energy_efficiency, 4),
            "transaction_density": round(transaction_density, 2),
            "state_stability": round(state_stability, 4),
            "metabolic_reliability": round(metabolic_reliability, 4),
            "blocks_analyzed": len(recent_blocks),
            "total_transactions": total_txns,
            "total_energy_spent": round(total_energy, 4),
            "time_in_state_seconds": round(time_in_state, 1),
            "heartbeat_interval_seconds": self.heartbeat_interval,
        }

    def get_block_timeline(self, limit: int = 20) -> List[Dict]:
        """Get recent block summaries for visualization."""
        blocks = self._get_recent_blocks(limit)
        return [{
            "block_number": b["block_number"],
            "timestamp": b["timestamp"],
            "state": b["metabolic_state"],
            "tx_count": b["tx_count"],
            "interval": round(b["heartbeat_interval"], 1),
            "expected": round(b["expected_interval"], 1),
            "energy": round(b["energy_cost"], 4),
            "hash": b["block_hash"][:12],
        } for b in blocks]

    def get_transition_history(self) -> List[Dict]:
        """Get metabolic state transition history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM metabolic_transitions
                WHERE team_id = ?
                ORDER BY timestamp ASC
            """, (self.team_id,)).fetchall()
            return [dict(r) for r in rows]

    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """Verify the entire block chain integrity."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM blocks WHERE team_id = ?
                ORDER BY block_number ASC
            """, (self.team_id,)).fetchall()
            blocks = [dict(r) for r in rows]

        if not blocks:
            return (True, None)

        for i, block in enumerate(blocks):
            # Verify genesis
            if i == 0:
                if block["previous_hash"] != "genesis":
                    return (False, f"Block 0 should have 'genesis' as previous_hash")
                continue

            prev = blocks[i - 1]

            # Verify sequence
            if block["block_number"] != prev["block_number"] + 1:
                return (False, f"Block number gap at {i}: {prev['block_number']} -> {block['block_number']}")

            # Verify hash chain
            if block["previous_hash"] != prev["block_hash"]:
                return (False, f"Hash chain broken at block {block['block_number']}")

        return (True, None)

    # -------------------------------------------------------------------
    # Persistence helpers
    # -------------------------------------------------------------------

    def _persist_block(self, block: Block):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO blocks
                (block_number, team_id, previous_hash, block_hash, timestamp,
                 metabolic_state, heartbeat_interval, expected_interval,
                 tx_count, transactions, energy_cost, sentinel_witness, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                block.block_number, block.team_id,
                block.previous_hash, block.block_hash,
                block.timestamp, block.metabolic_state,
                block.heartbeat_interval, block.expected_interval,
                block.tx_count, json.dumps(block.transactions),
                block.energy_cost, block.sentinel_witness,
                json.dumps(block.metadata),
            ))

    def _persist_transition(self, transition: MetabolicTransition):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO metabolic_transitions
                (team_id, from_state, to_state, trigger, timestamp,
                 block_number, atp_cost, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.team_id, transition.from_state, transition.to_state,
                transition.trigger, transition.timestamp,
                transition.block_number, transition.atp_cost,
                json.dumps(transition.metadata),
            ))

    def _get_latest_block(self) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM blocks WHERE team_id = ?
                ORDER BY block_number DESC LIMIT 1
            """, (self.team_id,)).fetchone()
            return dict(row) if row else None

    def _get_recent_blocks(self, limit: int) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM blocks WHERE team_id = ?
                ORDER BY block_number DESC LIMIT ?
            """, (self.team_id, limit)).fetchall()
            return [dict(r) for r in reversed(rows)]

    def _update_stats(self, tx_count: int, energy: float):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE team_state SET
                    total_blocks = total_blocks + 1,
                    total_transactions = total_transactions + ?,
                    total_energy_spent = total_energy_spent + ?,
                    atp_reserves = atp_reserves - ?
                WHERE team_id = ?
            """, (tx_count, energy, energy, self.team_id))

    def _get_atp_reserves(self) -> float:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT atp_reserves FROM team_state WHERE team_id = ?",
                (self.team_id,)
            ).fetchone()
            return row[0] if row else 0.0

    def _get_max_atp(self) -> float:
        """Get max ATP (initial allocation)."""
        return 1000.0  # Default, should be team-configurable


# ---------------------------------------------------------------------------
# Demo / Test
# ---------------------------------------------------------------------------

def demo_heartbeat_ledger():
    """Demonstrate the heartbeat-driven ledger."""
    import tempfile
    import time

    print("=" * 70)
    print("HEARTBEAT-DRIVEN LEDGER DEMONSTRATION")
    print("=" * 70)

    # Use temp DB for demo
    db_path = Path(tempfile.mkdtemp()) / "demo_heartbeat.db"

    team_id = "web4:team:demo-alpha"
    ledger = HeartbeatLedger(team_id, db_path=db_path)

    print(f"\nTeam: {team_id}")
    print(f"Initial state: {ledger.state.value}")
    print(f"Heartbeat interval: {ledger.heartbeat_interval}s")

    # --- Phase 1: Active work ---
    print(f"\n--- Phase 1: Active Work ---")

    # Submit several transactions
    ledger.submit_transaction("member_added", "web4:lct:admin:001", {
        "member_lct": "web4:lct:dev:002", "role": "developer"
    }, target_lct="web4:lct:dev:002")

    ledger.submit_transaction("r6_request", "web4:lct:dev:002", {
        "action": "commit", "target": "feature-branch", "description": "Add auth module"
    }, atp_cost=2.0)

    ledger.submit_transaction("trust_update", "web4:lct:admin:001", {
        "target": "web4:lct:dev:002", "dimension": "reliability", "delta": 0.05
    }, target_lct="web4:lct:dev:002")

    print(f"  Pending transactions: {ledger.pending_count}")

    # Heartbeat fires -> seal block
    block1 = ledger.heartbeat(sentinel_lct="web4:lct:admin:001")
    print(f"  Block {block1.block_number}: {block1.tx_count} txns, "
          f"state={block1.metabolic_state}, energy={block1.energy_cost:.4f}")

    # More work
    ledger.submit_transaction("r6_request", "web4:lct:dev:002", {
        "action": "deploy", "target": "staging"
    }, atp_cost=5.0)

    block2 = ledger.heartbeat(sentinel_lct="web4:lct:admin:001")
    print(f"  Block {block2.block_number}: {block2.tx_count} txns, "
          f"state={block2.metabolic_state}, energy={block2.energy_cost:.4f}")

    # --- Phase 2: Transition to REST ---
    print(f"\n--- Phase 2: Transition to REST ---")

    transition = ledger.transition_state(MetabolicState.REST, trigger="end_of_workday")
    print(f"  Transitioned: {transition.from_state} -> {transition.to_state}")
    print(f"  New heartbeat interval: {ledger.heartbeat_interval}s")

    # Heartbeat during rest (includes the transition tx)
    block3 = ledger.heartbeat(sentinel_lct="web4:lct:admin:001")
    print(f"  Block {block3.block_number}: {block3.tx_count} txns (includes transition), "
          f"state={block3.metabolic_state}, energy={block3.energy_cost:.4f}")

    # Empty rest heartbeat
    block4 = ledger.heartbeat(sentinel_lct="web4:lct:admin:001")
    print(f"  Block {block4.block_number}: {block4.tx_count} txns (empty - presence proof), "
          f"state={block4.metabolic_state}, energy={block4.energy_cost:.4f}")

    # --- Phase 3: Wake on transaction ---
    print(f"\n--- Phase 3: Wake on Transaction ---")

    # Incoming request wakes the team
    ledger.submit_transaction("r6_request", "web4:lct:dev:002", {
        "action": "hotfix", "target": "production", "priority": "high"
    }, atp_cost=3.0)

    print(f"  State after transaction: {ledger.state.value}")
    print(f"  Heartbeat interval: {ledger.heartbeat_interval}s")

    block5 = ledger.heartbeat(sentinel_lct="web4:lct:admin:001")
    print(f"  Block {block5.block_number}: {block5.tx_count} txns, "
          f"state={block5.metabolic_state}")

    # --- Phase 4: Transition to SLEEP ---
    print(f"\n--- Phase 4: Deep Sleep ---")

    ledger.transition_state(MetabolicState.REST, trigger="work_complete")
    ledger.heartbeat()

    ledger.transition_state(MetabolicState.SLEEP, trigger="scheduled_sleep")
    block6 = ledger.heartbeat(sentinel_lct="web4:lct:admin:001")
    print(f"  Block {block6.block_number}: state={block6.metabolic_state}, "
          f"interval={ledger.heartbeat_interval}s")

    # --- Phase 5: Dreaming (consolidation) ---
    print(f"\n--- Phase 5: Dreaming (Memory Consolidation) ---")

    ledger.transition_state(MetabolicState.ACTIVE, trigger="wake_trigger")
    ledger.heartbeat()

    ledger.transition_state(MetabolicState.DREAMING, trigger="maintenance_window")
    block7 = ledger.heartbeat(sentinel_lct="web4:lct:admin:001")
    print(f"  Block {block7.block_number}: state={block7.metabolic_state}, "
          f"interval={ledger.heartbeat_interval}s")
    print(f"  Trust decay rate: {ledger.trust_decay_rate} (frozen during dreams)")

    # Return to active
    ledger.transition_state(MetabolicState.ACTIVE, trigger="consolidation_complete")
    ledger.heartbeat()

    # --- Analytics ---
    print(f"\n--- Metabolic Health Report ---")
    health = ledger.get_metabolic_health()
    for k, v in health.items():
        print(f"  {k}: {v}")

    print(f"\n--- Block Timeline ---")
    timeline = ledger.get_block_timeline()
    for entry in timeline:
        state_marker = {
            "active": ">>", "rest": "..", "sleep": "zz",
            "dreaming": "~~", "hibernation": "  ",
        }.get(entry["state"], "??")
        print(f"  [{state_marker}] Block {entry['block_number']:3d} | "
              f"state={entry['state']:12s} | txns={entry['tx_count']:2d} | "
              f"energy={entry['energy']:8.4f} | hash={entry['hash']}")

    print(f"\n--- Transition History ---")
    transitions = ledger.get_transition_history()
    for t in transitions:
        print(f"  {t['from_state']:12s} -> {t['to_state']:12s} | "
              f"trigger={t['trigger']:30s} | cost={t['atp_cost']:.2f}")

    # Verify chain
    print(f"\n--- Chain Verification ---")
    valid, error = ledger.verify_chain()
    print(f"  Chain valid: {valid}")
    if error:
        print(f"  Error: {error}")

    print(f"\n{'=' * 70}")
    print("DEMO COMPLETE")
    print(f"{'=' * 70}")

    # Cleanup
    import shutil
    shutil.rmtree(db_path.parent)

    return health


if __name__ == "__main__":
    demo_heartbeat_ledger()
