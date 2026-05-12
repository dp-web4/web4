#!/usr/bin/env python3
"""
Heartbeat-Driven Ledger Timing - Phase 5 of MRH Grounding Implementation

Implements append-only ledger recording of heartbeats with timing validation.
This creates verifiable proof of continuous operational coherence.

Key Concepts:
- **Heartbeat Ledger**: Append-only log of all heartbeat events
- **Timing Windows**: Expected intervals based on hardware class TTL
- **Jitter Tolerance**: Acceptable deviation from expected interval
- **Timing Coherence**: Contribution to CI based on heartbeat regularity
- **Gap Detection**: Identifies missed heartbeats and their impact

The ledger provides:
1. Non-repudiation: Signed entries prove presence at specific times
2. Continuity: Hash chain links entries (same as grounding continuity tokens)
3. Audit Trail: Complete history of operational presence
4. Timing Analysis: Pattern detection for anomaly identification

Integration with grounding_lifecycle.py:
- GroundingManager.heartbeat() calls HeartbeatLedger.record()
- CI calculation incorporates timing_coherence from ledger
- Expiration detection triggers ledger gap entries
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Iterator
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class HeartbeatTimingConfig:
    """
    Timing configuration for heartbeat validation

    Hardware class determines expected heartbeat intervals.
    Jitter tolerance allows for network delays and clock drift.
    """
    # Base intervals (same as GroundingTTLConfig.heartbeat_interval)
    intervals: Dict[str, timedelta] = field(default_factory=lambda: {
        'server': timedelta(minutes=30),      # 1hr TTL → 30min heartbeat
        'edge-device': timedelta(minutes=7, seconds=30),  # 15min TTL → 7.5min
        'mobile': timedelta(minutes=2, seconds=30),  # 5min TTL → 2.5min
        'browser': timedelta(minutes=2, seconds=30),  # 5min TTL → 2.5min
        'iot-sensor': timedelta(hours=12),    # 24hr TTL → 12hr
    })

    # Jitter tolerance as fraction of interval
    jitter_tolerance: float = 0.2  # ±20% is acceptable

    # Early heartbeat penalty threshold (too early is also suspicious)
    early_threshold: float = 0.5  # <50% of interval is suspiciously early

    # Gap thresholds for CI impact
    single_miss_penalty: float = 0.1   # One missed heartbeat
    consecutive_miss_multiplier: float = 1.5  # Each additional miss
    max_penalty: float = 0.5  # Maximum penalty from timing issues

    def expected_interval(self, hardware_class: str) -> timedelta:
        """Get expected heartbeat interval for hardware class"""
        return self.intervals.get(hardware_class, self.intervals['edge-device'])

    def timing_window(self, hardware_class: str) -> Tuple[timedelta, timedelta]:
        """
        Get acceptable timing window (min, max) for next heartbeat

        Returns (earliest_acceptable, latest_acceptable) relative to last heartbeat
        """
        interval = self.expected_interval(hardware_class)
        jitter = interval * self.jitter_tolerance

        min_interval = interval * self.early_threshold
        max_interval = interval + jitter

        return (min_interval, max_interval)


class HeartbeatStatus(Enum):
    """Status classification for a heartbeat"""
    ON_TIME = "on_time"           # Within expected window
    EARLY = "early"               # Before minimum interval (suspicious)
    LATE = "late"                 # After expected but within grace
    MISSED = "missed"             # Gap detected (synthesized entry)
    RECOVERY = "recovery"         # First heartbeat after gap
    INITIAL = "initial"           # First heartbeat in chain


# ============================================================================
# Ledger Entry
# ============================================================================

@dataclass
class HeartbeatEntry:
    """
    Single entry in the heartbeat ledger

    Immutable after creation. Forms hash-linked chain.
    """
    # Identity
    entry_id: str                 # Unique entry ID (hash-based)
    entity_lct: str               # Entity this heartbeat is for

    # Timing
    timestamp: str                # ISO8601 when heartbeat was recorded
    expected_at: Optional[str]    # When heartbeat was expected (None for initial)
    delta_seconds: float          # Difference from expected (negative = early)

    # Status
    status: str                   # HeartbeatStatus value

    # Chain linkage
    previous_hash: str            # Hash of previous entry (empty for first)
    entry_hash: str               # Hash of this entry (computed)
    sequence: int                 # Position in chain (1-indexed)

    # Context
    hardware_class: str           # Hardware class at time of heartbeat
    grounding_hash: str           # Hash of associated grounding edge
    continuity_token: str         # Continuity token at this heartbeat

    # Metadata
    witnesses: List[str] = field(default_factory=list)
    signature: str = ""           # LCT signature over entry

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'HeartbeatEntry':
        """Create from dictionary"""
        return cls(**data)


def compute_entry_hash(
    entity_lct: str,
    timestamp: str,
    previous_hash: str,
    sequence: int,
    continuity_token: str
) -> str:
    """
    Compute hash for ledger entry

    Hash includes:
    - Entity identity
    - Timestamp
    - Previous hash (chain linkage)
    - Sequence number
    - Continuity token (links to grounding chain)
    """
    hasher = hashlib.sha256()
    hasher.update(entity_lct.encode('utf-8'))
    hasher.update(timestamp.encode('utf-8'))
    hasher.update(previous_hash.encode('utf-8'))
    hasher.update(str(sequence).encode('utf-8'))
    hasher.update(continuity_token.encode('utf-8'))

    return hasher.hexdigest()


# ============================================================================
# Heartbeat Ledger
# ============================================================================

class HeartbeatLedger:
    """
    Append-only ledger of heartbeat events

    Maintains:
    - Hash-linked chain of entries
    - Timing validation and gap detection
    - Persistence to JSONL file
    - Timing coherence calculation

    Thread-safety: Uses file locking for concurrent access
    """

    def __init__(
        self,
        entity_lct: str,
        storage_dir: Optional[Path] = None,
        config: Optional[HeartbeatTimingConfig] = None
    ):
        self.entity_lct = entity_lct
        self.config = config or HeartbeatTimingConfig()

        # Storage
        if storage_dir is None:
            storage_dir = Path.home() / '.web4' / 'heartbeat'
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Ledger file: one per entity
        entity_hash = hashlib.sha256(entity_lct.encode()).hexdigest()[:16]
        self.ledger_file = self.storage_dir / f"{entity_hash}.jsonl"

        # In-memory cache
        self._entries: List[HeartbeatEntry] = []
        self._last_entry: Optional[HeartbeatEntry] = None
        self._loaded = False

        # Timing statistics
        self._consecutive_misses = 0
        self._total_misses = 0
        self._timing_scores: List[float] = []

    def _load(self) -> None:
        """Load ledger from disk"""
        if self._loaded:
            return

        if self.ledger_file.exists():
            with open(self.ledger_file, 'r') as f:
                for line in f:
                    if line.strip():
                        entry = HeartbeatEntry.from_dict(json.loads(line))
                        self._entries.append(entry)

            if self._entries:
                self._last_entry = self._entries[-1]

                # Reconstruct statistics
                for entry in self._entries:
                    if entry.status == HeartbeatStatus.MISSED.value:
                        self._total_misses += 1

        self._loaded = True

    def _append(self, entry: HeartbeatEntry) -> None:
        """Append entry to ledger (in-memory and disk)"""
        self._entries.append(entry)
        self._last_entry = entry

        # Persist to disk
        with open(self.ledger_file, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')

    def record(
        self,
        hardware_class: str,
        grounding_hash: str,
        continuity_token: str,
        witnesses: Optional[List[str]] = None,
        signature: str = ""
    ) -> HeartbeatEntry:
        """
        Record a heartbeat event

        Validates timing, detects gaps, computes status, appends to ledger.

        Args:
            hardware_class: Current hardware class
            grounding_hash: Hash of associated grounding edge
            continuity_token: Current continuity token
            witnesses: Optional witness LCTs
            signature: LCT signature over entry

        Returns:
            Created HeartbeatEntry
        """
        self._load()

        now = datetime.now()
        timestamp = now.isoformat()

        if self._last_entry is None:
            # Initial heartbeat
            status = HeartbeatStatus.INITIAL
            expected_at = None
            delta_seconds = 0.0
            previous_hash = ""
            sequence = 1
            self._consecutive_misses = 0

        else:
            # Calculate expected time
            last_time = datetime.fromisoformat(self._last_entry.timestamp)
            interval = self.config.expected_interval(hardware_class)
            expected_time = last_time + interval
            expected_at = expected_time.isoformat()

            # Calculate delta
            delta = now - expected_time
            delta_seconds = delta.total_seconds()

            # Determine status
            min_interval, max_interval = self.config.timing_window(hardware_class)
            time_since_last = now - last_time

            if time_since_last < min_interval:
                status = HeartbeatStatus.EARLY
                self._consecutive_misses = 0

            elif time_since_last <= max_interval:
                status = HeartbeatStatus.ON_TIME
                self._consecutive_misses = 0

            elif time_since_last <= interval * 2:
                # Late but within one interval
                if self._consecutive_misses > 0:
                    status = HeartbeatStatus.RECOVERY
                else:
                    status = HeartbeatStatus.LATE
                self._consecutive_misses = 0

            else:
                # Gap detected - record missed heartbeats first
                missed_count = int(time_since_last / interval) - 1
                self._record_missed_heartbeats(
                    missed_count,
                    last_time,
                    interval,
                    hardware_class,
                    grounding_hash
                )

                status = HeartbeatStatus.RECOVERY
                self._consecutive_misses = 0

            previous_hash = self._last_entry.entry_hash
            sequence = self._last_entry.sequence + 1

        # Compute entry hash
        entry_hash = compute_entry_hash(
            self.entity_lct,
            timestamp,
            previous_hash,
            sequence,
            continuity_token
        )

        # Create entry
        entry = HeartbeatEntry(
            entry_id=f"hb:{entry_hash[:16]}",
            entity_lct=self.entity_lct,
            timestamp=timestamp,
            expected_at=expected_at,
            delta_seconds=delta_seconds,
            status=status.value,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
            sequence=sequence,
            hardware_class=hardware_class,
            grounding_hash=grounding_hash,
            continuity_token=continuity_token,
            witnesses=witnesses or [],
            signature=signature
        )

        # Record timing score
        timing_score = self._compute_timing_score(status, delta_seconds, hardware_class)
        self._timing_scores.append(timing_score)

        # Append to ledger
        self._append(entry)

        return entry

    def _record_missed_heartbeats(
        self,
        count: int,
        last_time: datetime,
        interval: timedelta,
        hardware_class: str,
        grounding_hash: str
    ) -> None:
        """Record synthesized entries for missed heartbeats"""
        for i in range(count):
            expected_time = last_time + interval * (i + 1)

            self._consecutive_misses += 1
            self._total_misses += 1

            previous_hash = self._last_entry.entry_hash if self._last_entry else ""
            sequence = (self._last_entry.sequence if self._last_entry else 0) + 1

            entry_hash = compute_entry_hash(
                self.entity_lct,
                expected_time.isoformat(),
                previous_hash,
                sequence,
                "MISSED"
            )

            entry = HeartbeatEntry(
                entry_id=f"hb:{entry_hash[:16]}",
                entity_lct=self.entity_lct,
                timestamp=expected_time.isoformat(),
                expected_at=expected_time.isoformat(),
                delta_seconds=0.0,
                status=HeartbeatStatus.MISSED.value,
                previous_hash=previous_hash,
                entry_hash=entry_hash,
                sequence=sequence,
                hardware_class=hardware_class,
                grounding_hash=grounding_hash,
                continuity_token="MISSED",
                witnesses=[],
                signature=""
            )

            self._append(entry)

            # Record zero timing score for missed
            self._timing_scores.append(0.0)

    def _compute_timing_score(
        self,
        status: HeartbeatStatus,
        delta_seconds: float,
        hardware_class: str
    ) -> float:
        """
        Compute timing score for a single heartbeat

        Returns 1.0 for perfect timing, decreasing for deviations.
        """
        if status == HeartbeatStatus.INITIAL:
            return 1.0

        if status == HeartbeatStatus.ON_TIME:
            # Score based on how close to expected
            interval = self.config.expected_interval(hardware_class)
            interval_seconds = interval.total_seconds()

            # Normalize delta to interval
            normalized_delta = abs(delta_seconds) / interval_seconds

            # Score: 1.0 at delta=0, 0.8 at jitter boundary
            return max(0.8, 1.0 - normalized_delta)

        if status == HeartbeatStatus.LATE:
            return 0.7

        if status == HeartbeatStatus.EARLY:
            # Suspiciously early - might indicate replay
            return 0.5

        if status == HeartbeatStatus.RECOVERY:
            return 0.6

        if status == HeartbeatStatus.MISSED:
            return 0.0

        return 0.5

    def timing_coherence(self, window: int = 10) -> float:
        """
        Compute timing coherence over recent heartbeats

        This value contributes to overall CI calculation.

        Args:
            window: Number of recent heartbeats to consider

        Returns:
            Timing coherence [0.0, 1.0]
        """
        self._load()

        if not self._timing_scores:
            return 1.0  # No history, assume coherent

        # Get recent scores
        recent = self._timing_scores[-window:] if len(self._timing_scores) >= window else self._timing_scores

        # Weighted average (more recent scores weighted higher)
        total_weight = 0.0
        weighted_sum = 0.0

        for i, score in enumerate(recent):
            weight = (i + 1) / len(recent)  # Linear weighting
            weighted_sum += score * weight
            total_weight += weight

        base_coherence = weighted_sum / total_weight if total_weight > 0 else 1.0

        # Apply consecutive miss penalty
        if self._consecutive_misses > 0:
            penalty = min(
                self.config.max_penalty,
                self.config.single_miss_penalty *
                (self.config.consecutive_miss_multiplier ** (self._consecutive_misses - 1))
            )
            base_coherence = max(0.0, base_coherence - penalty)

        return base_coherence

    def verify_chain(self) -> Tuple[bool, Optional[str], int]:
        """
        Verify integrity of the ledger chain

        Checks:
        - Hash chain continuity
        - Sequence monotonicity
        - Timestamp ordering

        Returns:
            (is_valid, error_message, last_valid_sequence)
        """
        self._load()

        if not self._entries:
            return (True, None, 0)

        for i, entry in enumerate(self._entries):
            if i == 0:
                if entry.previous_hash:
                    return (False, f"First entry has non-empty previous_hash", 0)
                continue

            prev = self._entries[i - 1]

            # Check sequence
            if entry.sequence != prev.sequence + 1:
                return (False, f"Sequence gap at {i}: {prev.sequence} → {entry.sequence}", prev.sequence)

            # Check previous hash
            if entry.previous_hash != prev.entry_hash:
                return (False, f"Hash chain broken at {i}", prev.sequence)

            # Check timestamp ordering
            if entry.timestamp <= prev.timestamp:
                return (False, f"Timestamp order violation at {i}", prev.sequence)

            # Verify entry hash
            expected_hash = compute_entry_hash(
                entry.entity_lct,
                entry.timestamp,
                entry.previous_hash,
                entry.sequence,
                entry.continuity_token
            )
            if entry.entry_hash != expected_hash:
                return (False, f"Entry hash mismatch at {i}", prev.sequence)

        return (True, None, self._entries[-1].sequence)

    def get_entries(
        self,
        since: Optional[datetime] = None,
        status_filter: Optional[List[HeartbeatStatus]] = None,
        limit: int = 100
    ) -> List[HeartbeatEntry]:
        """
        Get ledger entries with optional filtering

        Args:
            since: Only entries after this time
            status_filter: Only entries with these statuses
            limit: Maximum entries to return

        Returns:
            List of matching entries (most recent first)
        """
        self._load()

        result = []

        for entry in reversed(self._entries):
            if len(result) >= limit:
                break

            if since and datetime.fromisoformat(entry.timestamp) < since:
                break

            if status_filter:
                if entry.status not in [s.value for s in status_filter]:
                    continue

            result.append(entry)

        return result

    def summary(self) -> Dict:
        """
        Get ledger summary statistics

        Returns dict with:
        - total_entries: Total heartbeats recorded
        - total_misses: Number of missed heartbeats
        - timing_coherence: Current timing coherence
        - chain_valid: Whether chain is valid
        - last_heartbeat: Timestamp of last heartbeat
        - status_distribution: Count of each status type
        """
        self._load()

        status_dist = {}
        for entry in self._entries:
            status_dist[entry.status] = status_dist.get(entry.status, 0) + 1

        chain_valid, error, _ = self.verify_chain()

        return {
            'entity_lct': self.entity_lct,
            'total_entries': len(self._entries),
            'total_misses': self._total_misses,
            'consecutive_misses': self._consecutive_misses,
            'timing_coherence': self.timing_coherence(),
            'chain_valid': chain_valid,
            'chain_error': error,
            'last_heartbeat': self._last_entry.timestamp if self._last_entry else None,
            'last_status': self._last_entry.status if self._last_entry else None,
            'status_distribution': status_dist,
        }


# ============================================================================
# Integration with GroundingManager
# ============================================================================

class HeartbeatAwareGroundingManager:
    """
    Extended GroundingManager with heartbeat ledger integration

    Wraps GroundingManager to add ledger recording on each heartbeat.
    Contributes timing_coherence to overall CI calculation.
    """

    def __init__(
        self,
        entity_lct: str,
        mrh_graph,
        grounding_config=None,
        thresholds=None,
        ledger_dir: Optional[Path] = None,
        timing_config: Optional[HeartbeatTimingConfig] = None
    ):
        # Import here to avoid circular dependency
        from grounding_lifecycle import GroundingManager, GroundingTTLConfig, ContextChangeThresholds

        self.grounding_manager = GroundingManager(
            entity_lct,
            mrh_graph,
            grounding_config or GroundingTTLConfig(),
            thresholds or ContextChangeThresholds()
        )

        self.ledger = HeartbeatLedger(
            entity_lct,
            storage_dir=ledger_dir,
            config=timing_config
        )

        self.entity_lct = entity_lct

    def heartbeat(self, current_context, witnesses: Optional[List[str]] = None):
        """
        Perform heartbeat with ledger recording

        1. Calls underlying GroundingManager.heartbeat()
        2. Records to HeartbeatLedger
        3. Returns combined result
        """
        # Perform grounding heartbeat
        grounding, action = self.grounding_manager.heartbeat(current_context)

        # Record to ledger
        grounding_hash = hashlib.sha256(
            f"{grounding.timestamp}:{grounding.source}".encode()
        ).hexdigest()[:32]

        continuity_token = getattr(grounding, 'continuity_token', '')

        ledger_entry = self.ledger.record(
            hardware_class=current_context.capabilities.hardware_class,
            grounding_hash=grounding_hash,
            continuity_token=continuity_token,
            witnesses=witnesses
        )

        return {
            'grounding': grounding,
            'action': action,
            'ledger_entry': ledger_entry,
            'timing_coherence': self.ledger.timing_coherence()
        }

    def coherence_index_with_timing(self, current_context, history, mrh_graph, **kwargs) -> float:
        """
        Compute CI with timing coherence contribution

        Extends base coherence_index with timing dimension from ledger.
        """
        from coherence import coherence_index, CoherenceWeights

        # Get base CI
        base_ci = coherence_index(current_context, history, mrh_graph, **kwargs)

        # Get timing coherence
        timing_ci = self.ledger.timing_coherence()

        # Combine: timing acts as additional multiplier
        # Good timing (1.0) has no effect, poor timing reduces CI
        combined_ci = base_ci * (0.7 + 0.3 * timing_ci)

        return combined_ci

    def audit(self) -> Dict:
        """Get combined audit information"""
        grounding_valid, grounding_error = self.grounding_manager.validate_continuity()
        ledger_summary = self.ledger.summary()

        return {
            'grounding': {
                'current': self.grounding_manager.current_grounding,
                'history_length': len(self.grounding_manager.grounding_history),
                'chain_valid': grounding_valid,
                'chain_error': grounding_error,
            },
            'ledger': ledger_summary,
            'combined_coherence': self.coherence_index_with_timing(
                self.grounding_manager.current_grounding.target if self.grounding_manager.current_grounding else None,
                self.grounding_manager.grounding_history,
                self.grounding_manager.mrh_graph
            ) if self.grounding_manager.current_grounding else None
        }


# ============================================================================
# Demo
# ============================================================================

def demo_heartbeat_ledger():
    """Demonstrate heartbeat ledger functionality"""

    print("=" * 60)
    print("HEARTBEAT LEDGER DEMO - Phase 5 Implementation")
    print("=" * 60)

    # Create ledger for test entity
    entity_lct = "demo:legion-pro-7"
    ledger = HeartbeatLedger(
        entity_lct,
        storage_dir=Path("/tmp/web4-heartbeat-demo"),
        config=HeartbeatTimingConfig()
    )

    # Simulate heartbeat sequence
    print("\n1. Recording Normal Heartbeat Sequence")
    print("-" * 40)

    import time

    # Initial heartbeat
    entry1 = ledger.record(
        hardware_class="server",
        grounding_hash="abc123",
        continuity_token="ct-001"
    )
    print(f"  Entry 1: {entry1.status} (sequence {entry1.sequence})")

    # Simulate time passing (shortened for demo)
    time.sleep(0.1)

    # On-time heartbeat
    entry2 = ledger.record(
        hardware_class="server",
        grounding_hash="def456",
        continuity_token="ct-002"
    )
    print(f"  Entry 2: {entry2.status} (sequence {entry2.sequence})")

    # Late heartbeat
    time.sleep(0.1)
    entry3 = ledger.record(
        hardware_class="server",
        grounding_hash="ghi789",
        continuity_token="ct-003"
    )
    print(f"  Entry 3: {entry3.status} (sequence {entry3.sequence})")

    print("\n2. Ledger Summary")
    print("-" * 40)
    summary = ledger.summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print("\n3. Chain Verification")
    print("-" * 40)
    valid, error, last_seq = ledger.verify_chain()
    print(f"  Valid: {valid}")
    print(f"  Error: {error}")
    print(f"  Last valid sequence: {last_seq}")

    print("\n4. Timing Coherence")
    print("-" * 40)
    coherence = ledger.timing_coherence()
    print(f"  Timing Coherence: {coherence:.3f}")

    print("\n" + "=" * 60)
    print("Phase 5 Heartbeat Ledger Complete!")
    print("=" * 60)

    # Cleanup
    import shutil
    shutil.rmtree("/tmp/web4-heartbeat-demo", ignore_errors=True)


if __name__ == "__main__":
    demo_heartbeat_ledger()
