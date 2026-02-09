"""
Track FG: Temporal Coherence Attacks (Attacks 293-298)

Attacks on the temporal consistency of trust, presence, and witnessing.
Web4's trust model assumes entities have coherent histories - attacks that
exploit time-based inconsistencies can create paradoxical trust states.

Key insight: Trust is accumulated over time. If time itself can be manipulated
(perceived time, witnessed time, reported time), trust can be manufactured.

Reference:
- web4-standard/core-spec/LCT-linked-context-token.md (presence accumulation)
- whitepaper/sections/02-glossary/witnessing.md (temporal witnessing)

Added: 2026-02-09
"""

import hashlib
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum


@dataclass
class AttackResult:
    """Result of an attack simulation."""
    attack_name: str
    success: bool
    setup_cost_atp: float
    gain_atp: float
    roi: float
    detection_probability: float
    time_to_detection_hours: float
    blocks_until_detected: int
    trust_damage: float
    description: str
    mitigation: str
    raw_data: Dict


# ============================================================================
# TEMPORAL INFRASTRUCTURE
# ============================================================================


@dataclass
class TemporalWitness:
    """A witness event with temporal properties."""
    witness_id: str
    subject_lct: str
    timestamp_reported: float
    timestamp_received: float
    block_number: int
    trust_delta: float
    signature: str


@dataclass
class EntityTemporalProfile:
    """Temporal profile of an entity."""
    lct_id: str
    creation_timestamp: float
    creation_block: int
    first_witnessed: float
    witness_history: List[TemporalWitness] = field(default_factory=list)
    trust_history: List[Tuple[float, float]] = field(default_factory=list)  # (timestamp, trust)

    def current_trust(self) -> float:
        if not self.trust_history:
            return 0.0
        return self.trust_history[-1][1]

    def age_blocks(self, current_block: int) -> int:
        return current_block - self.creation_block

    def witness_frequency(self, window_seconds: float = 3600) -> float:
        """Witness events per hour in recent window."""
        now = time.time()
        recent = [w for w in self.witness_history
                  if now - w.timestamp_received < window_seconds]
        return len(recent) / (window_seconds / 3600)


class TemporalCoherenceChecker:
    """Verify temporal coherence of entity histories."""

    def __init__(self, max_clock_drift_seconds: float = 300):
        self.max_drift = max_clock_drift_seconds
        self.known_entities: Dict[str, EntityTemporalProfile] = {}

    def register_entity(self, profile: EntityTemporalProfile):
        self.known_entities[profile.lct_id] = profile

    def check_witness_temporal_coherence(self, witness: TemporalWitness) -> Tuple[bool, str]:
        """Check if a witness event is temporally coherent."""
        # Reported timestamp should not exceed received timestamp
        if witness.timestamp_reported > witness.timestamp_received + self.max_drift:
            return False, "future_timestamp"

        # Very old reported timestamps are suspicious
        age = witness.timestamp_received - witness.timestamp_reported
        if age > 86400 * 7:  # More than 7 days old
            return False, "stale_witness"

        # Check for witness before entity creation
        if witness.subject_lct in self.known_entities:
            profile = self.known_entities[witness.subject_lct]
            if witness.timestamp_reported < profile.creation_timestamp:
                return False, "witness_before_creation"

        return True, "coherent"

    def check_trust_monotonicity(self, lct_id: str) -> Tuple[bool, List[int]]:
        """Check for impossible trust jumps."""
        if lct_id not in self.known_entities:
            return True, []

        profile = self.known_entities[lct_id]
        violations = []

        MAX_TRUST_JUMP_PER_HOUR = 0.1

        for i in range(1, len(profile.trust_history)):
            prev_time, prev_trust = profile.trust_history[i-1]
            curr_time, curr_trust = profile.trust_history[i]

            time_diff_hours = (curr_time - prev_time) / 3600
            trust_diff = curr_trust - prev_trust

            if time_diff_hours > 0:
                rate = trust_diff / time_diff_hours
                if rate > MAX_TRUST_JUMP_PER_HOUR:
                    violations.append(i)

        return len(violations) == 0, violations


# ============================================================================
# ATTACK FG-1a: TIMESTAMP MANIPULATION
# ============================================================================


def attack_timestamp_manipulation() -> AttackResult:
    """
    ATTACK FG-1a: Timestamp Manipulation

    Manipulate timestamps in witness events to create artificial
    trust history or hide real activity patterns.

    Vectors:
    1. Backdated witnesses (claim old witnessing)
    2. Future-dated witnesses (pre-claim future events)
    3. Timestamp clustering (many events at one time)
    4. Clock drift exploitation
    5. Block-timestamp desync
    """

    defenses = {
        "timestamp_bounds_check": False,
        "clock_sync_verification": False,
        "witness_rate_limiting": False,
        "block_timestamp_correlation": False,
        "temporal_signature_binding": False,
        "distributed_time_consensus": False,
    }

    checker = TemporalCoherenceChecker()

    # Setup: Legitimate entity
    entity = EntityTemporalProfile(
        lct_id="lct_target_entity",
        creation_timestamp=time.time() - 86400 * 30,  # 30 days old
        creation_block=10000,
        first_witnessed=time.time() - 86400 * 29,
    )
    checker.register_entity(entity)

    now = time.time()
    current_block = 50000

    # Attack: Create backdated witnesses to manufacture trust history
    backdated_witnesses = [
        TemporalWitness(
            witness_id="fake_witness_1",
            subject_lct="lct_attacker",
            timestamp_reported=now - 86400 * 365,  # 1 year ago (impossible)
            timestamp_received=now,
            block_number=current_block,
            trust_delta=0.1,
            signature="fake_sig_1"
        ),
        TemporalWitness(
            witness_id="fake_witness_2",
            subject_lct="lct_attacker",
            timestamp_reported=now + 3600,  # 1 hour in future
            timestamp_received=now,
            block_number=current_block,
            trust_delta=0.1,
            signature="fake_sig_2"
        ),
        TemporalWitness(
            witness_id="fake_witness_3",
            subject_lct="lct_attacker",
            timestamp_reported=now - 600,  # Within bounds
            timestamp_received=now,
            block_number=current_block - 1000,  # Mismatched block
            trust_delta=0.1,
            signature="fake_sig_3"
        ),
    ]

    # ========================================================================
    # Vector 1: Timestamp Bounds Check Defense
    # ========================================================================

    def check_timestamp_bounds(witness: TemporalWitness,
                                current_time: float) -> bool:
        """Verify timestamp is within acceptable bounds."""
        MAX_AGE_SECONDS = 86400 * 30  # 30 days
        MAX_FUTURE_SECONDS = 300  # 5 minutes (clock drift)

        age = current_time - witness.timestamp_reported

        if age > MAX_AGE_SECONDS:
            return False
        if age < -MAX_FUTURE_SECONDS:
            return False

        return True

    if not check_timestamp_bounds(backdated_witnesses[0], now):
        defenses["timestamp_bounds_check"] = True

    # ========================================================================
    # Vector 2: Clock Sync Verification Defense
    # ========================================================================

    def verify_clock_sync(witness: TemporalWitness,
                           max_drift: float = 300) -> bool:
        """Verify reported and received timestamps are in sync."""
        drift = abs(witness.timestamp_reported - witness.timestamp_received)
        return drift <= max_drift

    if not verify_clock_sync(backdated_witnesses[1]):
        defenses["clock_sync_verification"] = True

    # ========================================================================
    # Vector 3: Witness Rate Limiting Defense
    # ========================================================================

    # Attack: Cluster many witnesses at same timestamp
    clustered_witnesses = [
        TemporalWitness(
            witness_id=f"cluster_{i}",
            subject_lct="lct_attacker",
            timestamp_reported=now - 100,
            timestamp_received=now,
            block_number=current_block,
            trust_delta=0.05,
            signature=f"sig_{i}"
        )
        for i in range(20)
    ]

    def check_witness_rate(witnesses: List[TemporalWitness],
                            max_per_minute: int = 5) -> bool:
        """Check for witness clustering."""
        # Group by minute
        minute_buckets: Dict[int, int] = {}
        for w in witnesses:
            minute = int(w.timestamp_reported // 60)
            minute_buckets[minute] = minute_buckets.get(minute, 0) + 1

        for count in minute_buckets.values():
            if count > max_per_minute:
                return False

        return True

    if not check_witness_rate(clustered_witnesses):
        defenses["witness_rate_limiting"] = True

    # ========================================================================
    # Vector 4: Block-Timestamp Correlation Defense
    # ========================================================================

    def verify_block_timestamp_correlation(witness: TemporalWitness,
                                            block_time_map: Dict[int, float]) -> bool:
        """Verify block number correlates with timestamp."""
        if witness.block_number not in block_time_map:
            return True  # Can't verify

        expected_time = block_time_map[witness.block_number]
        drift = abs(witness.timestamp_reported - expected_time)

        # Allow 1 hour drift between block time and witness time
        return drift <= 3600

    # Simulated block time map
    block_times = {
        current_block: now,
        current_block - 1000: now - 6000,  # ~10 min per block
    }

    if not verify_block_timestamp_correlation(backdated_witnesses[2], block_times):
        defenses["block_timestamp_correlation"] = True

    # ========================================================================
    # Vector 5: Temporal Signature Binding Defense
    # ========================================================================

    def verify_temporal_signature(witness: TemporalWitness) -> bool:
        """Verify signature includes timestamp commitment."""
        # Simulated: Real implementation would verify cryptographic binding
        expected_prefix = hashlib.sha256(
            f"{witness.subject_lct}:{int(witness.timestamp_reported)}".encode()
        ).hexdigest()[:8]

        # Fake signatures don't match
        return witness.signature.startswith(expected_prefix)

    if not verify_temporal_signature(backdated_witnesses[0]):
        defenses["temporal_signature_binding"] = True

    # ========================================================================
    # Vector 6: Distributed Time Consensus Defense
    # ========================================================================

    @dataclass
    class TimeAttestation:
        attester_id: str
        attested_time: float
        confidence: float

    def verify_distributed_time(witness: TemporalWitness,
                                 attestations: List[TimeAttestation]) -> bool:
        """Verify time against distributed attestation."""
        if len(attestations) < 3:
            return True  # Not enough attestors

        avg_time = sum(a.attested_time for a in attestations) / len(attestations)
        drift = abs(witness.timestamp_reported - avg_time)

        return drift <= 300  # 5 minute tolerance

    # Multiple attestors agree on current time
    time_attestations = [
        TimeAttestation("ntp_server_1", now, 0.99),
        TimeAttestation("ntp_server_2", now + 2, 0.99),
        TimeAttestation("ntp_server_3", now - 1, 0.99),
    ]

    if not verify_distributed_time(backdated_witnesses[0], time_attestations):
        defenses["distributed_time_consensus"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Timestamp Manipulation (FG-1a)",
        success=attack_success,
        setup_cost_atp=8000.0,
        gain_atp=60000.0 if attack_success else 0.0,
        roi=(60000.0 / 8000.0) if attack_success else -1.0,
        detection_probability=0.70 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=12.0,
        blocks_until_detected=120,
        trust_damage=0.55,
        description=f"""
TIMESTAMP MANIPULATION ATTACK (Track FG-1a)

Manipulate timestamps to create artificial trust history.

Attack Pattern:
1. Create backdated witnesses (claim old history)
2. Future-date witnesses (pre-claim events)
3. Cluster witnesses at single timestamp
4. Exploit clock drift between nodes
5. Desync block timestamps from real time

Attack Examples:
- Backdated witness: {backdated_witnesses[0].timestamp_reported - now:.0f}s in past
- Future witness: {backdated_witnesses[1].timestamp_reported - now:.0f}s in future
- Clustered witnesses: {len(clustered_witnesses)} at same minute

Defense Analysis:
- Timestamp bounds: {"HELD" if defenses["timestamp_bounds_check"] else "BYPASSED"}
- Clock sync: {"HELD" if defenses["clock_sync_verification"] else "BYPASSED"}
- Rate limiting: {"HELD" if defenses["witness_rate_limiting"] else "BYPASSED"}
- Block correlation: {"HELD" if defenses["block_timestamp_correlation"] else "BYPASSED"}
- Temporal signature: {"HELD" if defenses["temporal_signature_binding"] else "BYPASSED"}
- Distributed time: {"HELD" if defenses["distributed_time_consensus"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FG-1a: Timestamp Manipulation Defense:
1. Enforce strict timestamp bounds
2. Verify clock synchronization
3. Rate limit witness events
4. Correlate with block timestamps
5. Bind signatures to timestamps
6. Distributed time consensus

Time is not just a number - it's context.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "backdated_age_days": (now - backdated_witnesses[0].timestamp_reported) / 86400,
        }
    )


# ============================================================================
# ATTACK FG-1b: TRUST HISTORY FABRICATION
# ============================================================================


def attack_trust_history_fabrication() -> AttackResult:
    """
    ATTACK FG-1b: Trust History Fabrication

    Fabricate a complete trust history that appears legitimate
    but was created recently.

    Vectors:
    1. Synthetic witness generation
    2. Trust trajectory simulation
    3. History grafting from legitimate entities
    4. Parallel timeline creation
    5. Retroactive attestation chains
    """

    defenses = {
        "witness_source_verification": False,
        "trust_trajectory_analysis": False,
        "history_cross_referencing": False,
        "timeline_consistency": False,
        "attestation_freshness": False,
        "behavioral_fingerprinting": False,
    }

    now = time.time()
    current_block = 50000

    # Attack: Create fabricated entity with synthetic history
    @dataclass
    class FabricatedHistory:
        lct_id: str
        fake_witnesses: List[TemporalWitness]
        fake_trust_trajectory: List[Tuple[float, float]]

    # Generate synthetic witnesses with realistic-looking patterns
    fake_witnesses = []
    fake_trust = []

    base_time = now - 86400 * 180  # 180 days ago
    current_trust = 0.1

    for day in range(180):
        # Generate 2-5 witnesses per day
        num_witnesses = random.randint(2, 5)
        for i in range(num_witnesses):
            witness_time = base_time + day * 86400 + random.randint(0, 86400)
            trust_delta = random.uniform(0.001, 0.01)
            current_trust = min(0.95, current_trust + trust_delta)

            fake_witnesses.append(TemporalWitness(
                witness_id=f"synthetic_witness_{day}_{i}",
                subject_lct="lct_fabricated",
                timestamp_reported=witness_time,
                timestamp_received=witness_time + random.randint(0, 60),
                block_number=10000 + day * 50,
                trust_delta=trust_delta,
                signature=f"fake_sig_{day}_{i}"
            ))

        fake_trust.append((base_time + day * 86400, current_trust))

    fabricated = FabricatedHistory(
        lct_id="lct_fabricated",
        fake_witnesses=fake_witnesses,
        fake_trust_trajectory=fake_trust
    )

    # ========================================================================
    # Vector 1: Witness Source Verification Defense
    # ========================================================================

    def verify_witness_sources(witnesses: List[TemporalWitness],
                                known_witnesses: Set[str]) -> bool:
        """Verify witness IDs are from known entities."""
        for witness in witnesses[:10]:  # Sample check
            if witness.witness_id not in known_witnesses:
                return False
        return True

    known_witness_ids = {"witness_alice", "witness_bob", "witness_carol"}

    if not verify_witness_sources(fabricated.fake_witnesses, known_witness_ids):
        defenses["witness_source_verification"] = True

    # ========================================================================
    # Vector 2: Trust Trajectory Analysis Defense
    # ========================================================================

    def analyze_trust_trajectory(trajectory: List[Tuple[float, float]]) -> bool:
        """Analyze if trust trajectory looks organic."""
        if len(trajectory) < 10:
            return True

        # Check for suspiciously smooth growth
        deltas = []
        for i in range(1, len(trajectory)):
            deltas.append(trajectory[i][1] - trajectory[i-1][1])

        # Calculate variance - too low = suspicious
        avg_delta = sum(deltas) / len(deltas)
        variance = sum((d - avg_delta) ** 2 for d in deltas) / len(deltas)

        # Organic trajectories have higher variance
        MIN_VARIANCE = 0.0001
        return variance >= MIN_VARIANCE

    # Fabricated trajectory is too smooth
    if not analyze_trust_trajectory(fabricated.fake_trust_trajectory):
        defenses["trust_trajectory_analysis"] = True

    # ========================================================================
    # Vector 3: History Cross-Referencing Defense
    # ========================================================================

    # Defense: Cross-reference with other entities' records
    @dataclass
    class ExternalRecord:
        entity_id: str
        witnessed_entities: Set[str]
        timestamp: float

    external_records = [
        ExternalRecord("entity_a", {"entity_b", "entity_c"}, now - 86400 * 90),
        ExternalRecord("entity_b", {"entity_a", "entity_c"}, now - 86400 * 85),
        ExternalRecord("entity_c", {"entity_a", "entity_b"}, now - 86400 * 80),
    ]

    def cross_reference_history(lct_id: str,
                                  external: List[ExternalRecord]) -> bool:
        """Check if entity appears in external records."""
        for record in external:
            if lct_id in record.witnessed_entities:
                return True
        return False

    if not cross_reference_history(fabricated.lct_id, external_records):
        defenses["history_cross_referencing"] = True

    # ========================================================================
    # Vector 4: Timeline Consistency Defense
    # ========================================================================

    def check_timeline_consistency(witnesses: List[TemporalWitness],
                                     creation_time: float) -> bool:
        """Verify witnesses don't predate entity creation."""
        for witness in witnesses:
            if witness.timestamp_reported < creation_time:
                return False
        return True

    # Fabricated entity claims creation 200 days ago but only created yesterday
    actual_creation = now - 86400  # Yesterday
    claimed_creation = now - 86400 * 200

    # Some witnesses predate actual creation
    if not check_timeline_consistency(fabricated.fake_witnesses, actual_creation):
        defenses["timeline_consistency"] = True

    # ========================================================================
    # Vector 5: Attestation Freshness Defense
    # ========================================================================

    @dataclass
    class Attestation:
        attester: str
        attestee: str
        claimed_relationship_start: float
        attestation_created: float

    def check_attestation_freshness(attestation: Attestation) -> bool:
        """Verify attestation wasn't created long after claimed relationship."""
        MAX_ATTESTATION_DELAY = 86400 * 7  # 7 days

        delay = attestation.attestation_created - attestation.claimed_relationship_start
        return delay <= MAX_ATTESTATION_DELAY

    # Attack: Create attestation now claiming old relationship
    fake_attestation = Attestation(
        attester="fake_attester",
        attestee="lct_fabricated",
        claimed_relationship_start=now - 86400 * 180,
        attestation_created=now  # Created just now
    )

    if not check_attestation_freshness(fake_attestation):
        defenses["attestation_freshness"] = True

    # ========================================================================
    # Vector 6: Behavioral Fingerprinting Defense
    # ========================================================================

    def analyze_behavioral_fingerprint(witnesses: List[TemporalWitness]) -> bool:
        """Analyze behavioral patterns for authenticity."""
        if len(witnesses) < 50:
            return True

        # Check for unnatural patterns
        # 1. Too regular intervals
        intervals = []
        for i in range(1, min(100, len(witnesses))):
            intervals.append(witnesses[i].timestamp_reported - witnesses[i-1].timestamp_reported)

        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            # Check for suspiciously regular intervals
            regular_count = sum(1 for i in intervals if abs(i - avg_interval) < 60)
            regularity = regular_count / len(intervals)

            if regularity > 0.7:  # 70% of intervals too similar
                return False

        # 2. Check for time-of-day patterns (real entities have circadian rhythms)
        hour_distribution = [0] * 24
        for w in witnesses:
            hour = int((w.timestamp_reported % 86400) / 3600)
            hour_distribution[hour] += 1

        # Real entities have activity peaks; synthetic is often uniform
        max_hour = max(hour_distribution)
        min_hour = min(hour_distribution)
        if max_hour > 0 and max_hour / (min_hour + 1) < 1.5:  # Too uniform
            return False

        return True

    if not analyze_behavioral_fingerprint(fabricated.fake_witnesses):
        defenses["behavioral_fingerprinting"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Trust History Fabrication (FG-1b)",
        success=attack_success,
        setup_cost_atp=25000.0,
        gain_atp=150000.0 if attack_success else 0.0,
        roi=(150000.0 / 25000.0) if attack_success else -1.0,
        detection_probability=0.65 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=72.0,
        blocks_until_detected=600,
        trust_damage=0.80,
        description=f"""
TRUST HISTORY FABRICATION ATTACK (Track FG-1b)

Fabricate complete trust history from scratch.

Attack Pattern:
1. Generate synthetic witness events
2. Create smooth trust trajectory
3. Backdate witnesses to appear old
4. Create fake attestation chains
5. Simulate behavioral patterns

Fabrication Details:
- Synthetic witnesses: {len(fabricated.fake_witnesses)}
- Claimed age: {(now - fabricated.fake_witnesses[0].timestamp_reported) / 86400:.0f} days
- Final trust: {fabricated.fake_trust_trajectory[-1][1]:.2f}
- Actual creation: 1 day ago

Defense Analysis:
- Witness source verification: {"HELD" if defenses["witness_source_verification"] else "BYPASSED"}
- Trust trajectory analysis: {"HELD" if defenses["trust_trajectory_analysis"] else "BYPASSED"}
- History cross-referencing: {"HELD" if defenses["history_cross_referencing"] else "BYPASSED"}
- Timeline consistency: {"HELD" if defenses["timeline_consistency"] else "BYPASSED"}
- Attestation freshness: {"HELD" if defenses["attestation_freshness"] else "BYPASSED"}
- Behavioral fingerprinting: {"HELD" if defenses["behavioral_fingerprinting"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FG-1b: Trust History Fabrication Defense:
1. Verify witness sources are known entities
2. Analyze trust trajectory for organic patterns
3. Cross-reference with external records
4. Verify timeline consistency with creation
5. Check attestation freshness (delay detection)
6. Behavioral fingerprinting for authenticity

History that appears too clean is likely fake.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "synthetic_witnesses": len(fabricated.fake_witnesses),
            "claimed_age_days": (now - fabricated.fake_witnesses[0].timestamp_reported) / 86400,
        }
    )


# ============================================================================
# ATTACK FG-2a: PRESENCE OSCILLATION
# ============================================================================


def attack_presence_oscillation() -> AttackResult:
    """
    ATTACK FG-2a: Presence Oscillation

    Rapidly oscillate between present and absent states to
    exploit race conditions in presence-based trust checks.

    Vectors:
    1. Rapid online/offline cycling
    2. Presence spoofing
    3. Heartbeat manipulation
    4. Multi-location presence
    5. Delayed presence propagation
    """

    defenses = {
        "presence_rate_limiting": False,
        "presence_verification": False,
        "heartbeat_validation": False,
        "location_consistency": False,
        "presence_propagation_check": False,
        "presence_history_analysis": False,
    }

    now = time.time()

    @dataclass
    class PresenceEvent:
        entity_id: str
        status: str  # "online", "offline", "away"
        timestamp: float
        location: str
        heartbeat_signature: str

    # Attack: Rapid presence oscillation
    oscillating_presence = []
    for i in range(100):
        oscillating_presence.append(PresenceEvent(
            entity_id="lct_attacker",
            status="online" if i % 2 == 0 else "offline",
            timestamp=now - 100 + i,  # 1 second intervals
            location=f"node_{i % 5}",
            heartbeat_signature=f"hb_{i}"
        ))

    # ========================================================================
    # Vector 1: Presence Rate Limiting Defense
    # ========================================================================

    def check_presence_rate(events: List[PresenceEvent],
                             max_changes_per_minute: int = 6) -> bool:
        """Check for rapid presence changes."""
        if len(events) < 2:
            return True

        # Count changes per minute
        minute_buckets: Dict[int, int] = {}
        for event in events:
            minute = int(event.timestamp // 60)
            minute_buckets[minute] = minute_buckets.get(minute, 0) + 1

        for count in minute_buckets.values():
            if count > max_changes_per_minute:
                return False

        return True

    if not check_presence_rate(oscillating_presence):
        defenses["presence_rate_limiting"] = True

    # ========================================================================
    # Vector 2: Presence Verification Defense
    # ========================================================================

    def verify_presence(event: PresenceEvent,
                         challenge_response: Optional[str]) -> bool:
        """Verify presence claim with challenge-response."""
        if event.status == "online":
            # Online claims require challenge response
            if challenge_response is None:
                return False
            # Simulated: verify challenge
            expected = hashlib.sha256(
                f"{event.entity_id}:{int(event.timestamp)}".encode()
            ).hexdigest()[:8]
            return challenge_response == expected
        return True

    # Attack doesn't provide valid challenge response
    if not verify_presence(oscillating_presence[0], None):
        defenses["presence_verification"] = True

    # ========================================================================
    # Vector 3: Heartbeat Validation Defense
    # ========================================================================

    def validate_heartbeat(events: List[PresenceEvent],
                            expected_interval_seconds: float = 30) -> bool:
        """Validate heartbeat timing is consistent."""
        online_events = [e for e in events if e.status == "online"]

        if len(online_events) < 2:
            return True

        intervals = []
        for i in range(1, len(online_events)):
            interval = online_events[i].timestamp - online_events[i-1].timestamp
            intervals.append(interval)

        # Heartbeats should be at regular intervals
        avg_interval = sum(intervals) / len(intervals)

        # Check for too-rapid heartbeats
        if avg_interval < expected_interval_seconds * 0.5:
            return False

        return True

    if not validate_heartbeat(oscillating_presence):
        defenses["heartbeat_validation"] = True

    # ========================================================================
    # Vector 4: Location Consistency Defense
    # ========================================================================

    def check_location_consistency(events: List[PresenceEvent],
                                     max_locations_per_hour: int = 3) -> bool:
        """Check for impossible multi-location presence."""
        # Group by hour
        hourly_locations: Dict[int, Set[str]] = {}
        for event in events:
            hour = int(event.timestamp // 3600)
            if hour not in hourly_locations:
                hourly_locations[hour] = set()
            hourly_locations[hour].add(event.location)

        for locations in hourly_locations.values():
            if len(locations) > max_locations_per_hour:
                return False

        return True

    if not check_location_consistency(oscillating_presence):
        defenses["location_consistency"] = True

    # ========================================================================
    # Vector 5: Presence Propagation Check Defense
    # ========================================================================

    @dataclass
    class PropagatedPresence:
        original_event: PresenceEvent
        propagation_delay_ms: float
        receiving_node: str

    def check_presence_propagation(original: PresenceEvent,
                                     propagated: List[PropagatedPresence]) -> bool:
        """Verify presence propagation is consistent."""
        if len(propagated) < 3:
            return True  # Not enough data

        delays = [p.propagation_delay_ms for p in propagated]
        avg_delay = sum(delays) / len(delays)

        # Propagation should take some time
        MIN_PROPAGATION_MS = 10
        MAX_PROPAGATION_MS = 5000

        if avg_delay < MIN_PROPAGATION_MS:
            return False  # Too fast = probably faked
        if avg_delay > MAX_PROPAGATION_MS:
            return False  # Too slow = network manipulation

        return True

    # Attack: Fake propagation with zero delay
    fake_propagation = [
        PropagatedPresence(oscillating_presence[0], 0.5, "node_1"),
        PropagatedPresence(oscillating_presence[0], 0.3, "node_2"),
        PropagatedPresence(oscillating_presence[0], 0.4, "node_3"),
    ]

    if not check_presence_propagation(oscillating_presence[0], fake_propagation):
        defenses["presence_propagation_check"] = True

    # ========================================================================
    # Vector 6: Presence History Analysis Defense
    # ========================================================================

    def analyze_presence_history(events: List[PresenceEvent]) -> bool:
        """Analyze presence history for anomalies."""
        if len(events) < 10:
            return True

        # Calculate online/offline ratio
        online_count = sum(1 for e in events if e.status == "online")
        offline_count = sum(1 for e in events if e.status == "offline")

        # Extreme ratios are suspicious
        if online_count > 0 and offline_count > 0:
            ratio = online_count / offline_count
            if ratio > 10 or ratio < 0.1:
                pass  # Could be legitimate

        # Check for alternating pattern (suspicious)
        alternating_count = 0
        for i in range(1, len(events)):
            if events[i].status != events[i-1].status:
                alternating_count += 1

        alternating_ratio = alternating_count / (len(events) - 1)
        if alternating_ratio > 0.9:  # Almost always alternating
            return False

        return True

    if not analyze_presence_history(oscillating_presence):
        defenses["presence_history_analysis"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Presence Oscillation (FG-2a)",
        success=attack_success,
        setup_cost_atp=5000.0,
        gain_atp=40000.0 if attack_success else 0.0,
        roi=(40000.0 / 5000.0) if attack_success else -1.0,
        detection_probability=0.75 if defenses_held >= 4 else 0.35,
        time_to_detection_hours=6.0,
        blocks_until_detected=50,
        trust_damage=0.45,
        description=f"""
PRESENCE OSCILLATION ATTACK (Track FG-2a)

Rapidly oscillate presence to exploit race conditions.

Attack Pattern:
1. Cycle online/offline rapidly (1 second intervals)
2. Claim presence at multiple locations
3. Exploit presence check timing windows
4. Manipulate heartbeat signatures
5. Fake propagation delays

Oscillation Analysis:
- Total events: {len(oscillating_presence)}
- Oscillation period: 1 second
- Unique locations: {len(set(e.location for e in oscillating_presence))}
- Alternating ratio: {sum(1 for i in range(1, len(oscillating_presence)) if oscillating_presence[i].status != oscillating_presence[i-1].status) / (len(oscillating_presence)-1):.2%}

Defense Analysis:
- Presence rate limiting: {"HELD" if defenses["presence_rate_limiting"] else "BYPASSED"}
- Presence verification: {"HELD" if defenses["presence_verification"] else "BYPASSED"}
- Heartbeat validation: {"HELD" if defenses["heartbeat_validation"] else "BYPASSED"}
- Location consistency: {"HELD" if defenses["location_consistency"] else "BYPASSED"}
- Propagation check: {"HELD" if defenses["presence_propagation_check"] else "BYPASSED"}
- History analysis: {"HELD" if defenses["presence_history_analysis"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FG-2a: Presence Oscillation Defense:
1. Rate limit presence changes
2. Challenge-response for online claims
3. Validate heartbeat timing
4. Check location consistency
5. Verify propagation delays
6. Analyze presence history patterns

Presence must be stable to be meaningful.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "oscillation_count": len(oscillating_presence),
        }
    )


# ============================================================================
# ATTACK FG-2b: WITNESS ORDERING ATTACKS
# ============================================================================


def attack_witness_ordering() -> AttackResult:
    """
    ATTACK FG-2b: Witness Ordering Attacks

    Manipulate the order of witness events to change
    the resulting trust state.

    Vectors:
    1. Event reordering
    2. Selective event dropping
    3. Event injection between witnesses
    4. Parallel witness race conditions
    5. Consensus timing attacks
    """

    defenses = {
        "sequence_numbers": False,
        "causal_ordering": False,
        "merkle_witness_chains": False,
        "consensus_finality": False,
        "parallel_witness_detection": False,
        "ordering_attestation": False,
    }

    now = time.time()

    @dataclass
    class OrderedWitness:
        witness_id: str
        subject_lct: str
        sequence_number: int
        timestamp: float
        trust_delta: float
        previous_hash: str
        current_hash: str

    # Legitimate ordering
    legitimate_witnesses = []
    prev_hash = "genesis"

    for i in range(10):
        current_hash = hashlib.sha256(
            f"{prev_hash}:{i}:{now + i * 60}".encode()
        ).hexdigest()[:16]

        legitimate_witnesses.append(OrderedWitness(
            witness_id=f"legit_witness_{i}",
            subject_lct="lct_target",
            sequence_number=i,
            timestamp=now + i * 60,
            trust_delta=0.01 if i < 8 else -0.05,  # Last 2 are negative
            previous_hash=prev_hash,
            current_hash=current_hash
        ))
        prev_hash = current_hash

    # Attack: Reorder to put negative witnesses first (to be dropped later)
    reordered_witnesses = legitimate_witnesses[8:] + legitimate_witnesses[:8]

    # ========================================================================
    # Vector 1: Sequence Numbers Defense
    # ========================================================================

    def verify_sequence_numbers(witnesses: List[OrderedWitness]) -> bool:
        """Verify sequence numbers are in order."""
        expected_seq = 0
        for witness in witnesses:
            if witness.sequence_number != expected_seq:
                return False
            expected_seq += 1
        return True

    if not verify_sequence_numbers(reordered_witnesses):
        defenses["sequence_numbers"] = True

    # ========================================================================
    # Vector 2: Causal Ordering Defense
    # ========================================================================

    @dataclass
    class CausalDependency:
        event_id: str
        depends_on: List[str]
        timestamp: float

    def verify_causal_ordering(witnesses: List[OrderedWitness]) -> bool:
        """Verify causal dependencies are respected."""
        seen_hashes = {"genesis"}

        for witness in witnesses:
            if witness.previous_hash not in seen_hashes:
                return False
            seen_hashes.add(witness.current_hash)

        return True

    if not verify_causal_ordering(reordered_witnesses):
        defenses["causal_ordering"] = True

    # ========================================================================
    # Vector 3: Merkle Witness Chains Defense
    # ========================================================================

    def verify_merkle_chain(witnesses: List[OrderedWitness]) -> bool:
        """Verify Merkle chain integrity."""
        prev_hash = "genesis"

        for witness in witnesses:
            expected_hash = hashlib.sha256(
                f"{prev_hash}:{witness.sequence_number}:{witness.timestamp}".encode()
            ).hexdigest()[:16]

            if witness.current_hash != expected_hash:
                return False

            prev_hash = witness.current_hash

        return True

    # Reordered witnesses break the chain
    if not verify_merkle_chain(reordered_witnesses):
        defenses["merkle_witness_chains"] = True

    # ========================================================================
    # Vector 4: Consensus Finality Defense
    # ========================================================================

    @dataclass
    class ConsensusState:
        finalized_sequence: int
        finalized_hash: str
        confirmations: int

    def check_consensus_finality(witness: OrderedWitness,
                                   consensus: ConsensusState) -> bool:
        """Check if witness respects consensus finality."""
        # Cannot reorder before finalized sequence
        if witness.sequence_number < consensus.finalized_sequence:
            return False

        # Must reference finalized hash
        if witness.sequence_number == consensus.finalized_sequence:
            if witness.previous_hash != consensus.finalized_hash:
                return False

        return True

    # Consensus has finalized through sequence 5
    consensus = ConsensusState(
        finalized_sequence=5,
        finalized_hash=legitimate_witnesses[4].current_hash,
        confirmations=10
    )

    # Reordered witnesses try to insert before finalized
    if not check_consensus_finality(reordered_witnesses[0], consensus):
        defenses["consensus_finality"] = True

    # ========================================================================
    # Vector 5: Parallel Witness Detection Defense
    # ========================================================================

    def detect_parallel_witnesses(witnesses: List[OrderedWitness]) -> bool:
        """Detect attempts to create parallel witness chains."""
        # Check for same sequence number with different hashes
        seq_hashes: Dict[int, Set[str]] = {}

        for witness in witnesses:
            seq = witness.sequence_number
            if seq not in seq_hashes:
                seq_hashes[seq] = set()
            seq_hashes[seq].add(witness.current_hash)

        # Multiple hashes for same sequence = fork attempt
        for hashes in seq_hashes.values():
            if len(hashes) > 1:
                return False

        return True

    # Attack: Create parallel chain
    parallel_witness = OrderedWitness(
        witness_id="parallel_witness_5",
        subject_lct="lct_target",
        sequence_number=5,
        timestamp=now + 5 * 60,
        trust_delta=0.1,  # Higher trust in parallel chain
        previous_hash=legitimate_witnesses[4].previous_hash,
        current_hash="parallel_hash_5"
    )

    all_witnesses = legitimate_witnesses + [parallel_witness]

    if not detect_parallel_witnesses(all_witnesses):
        defenses["parallel_witness_detection"] = True

    # ========================================================================
    # Vector 6: Ordering Attestation Defense
    # ========================================================================

    @dataclass
    class OrderingAttestation:
        attester: str
        attested_order: List[str]  # List of witness IDs in order
        attestation_hash: str

    def verify_ordering_attestation(witnesses: List[OrderedWitness],
                                      attestations: List[OrderingAttestation]) -> bool:
        """Verify ordering against attestations."""
        if len(attestations) < 3:
            return True  # Not enough attestors

        # Extract order from witnesses
        witness_order = [w.witness_id for w in witnesses]

        # Compare with attestations
        matching = 0
        for attestation in attestations:
            if attestation.attested_order == witness_order:
                matching += 1

        # Require majority agreement
        return matching >= len(attestations) * 0.5

    # Attestors saw legitimate order
    ordering_attestations = [
        OrderingAttestation("attester_1", [w.witness_id for w in legitimate_witnesses], "hash_1"),
        OrderingAttestation("attester_2", [w.witness_id for w in legitimate_witnesses], "hash_2"),
        OrderingAttestation("attester_3", [w.witness_id for w in legitimate_witnesses], "hash_3"),
    ]

    if not verify_ordering_attestation(reordered_witnesses, ordering_attestations):
        defenses["ordering_attestation"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Witness Ordering (FG-2b)",
        success=attack_success,
        setup_cost_atp=12000.0,
        gain_atp=80000.0 if attack_success else 0.0,
        roi=(80000.0 / 12000.0) if attack_success else -1.0,
        detection_probability=0.70 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=24.0,
        blocks_until_detected=200,
        trust_damage=0.65,
        description=f"""
WITNESS ORDERING ATTACK (Track FG-2b)

Manipulate witness ordering to change trust state.

Attack Pattern:
1. Capture legitimate witness stream
2. Reorder events (put negatives first to drop)
3. Create parallel witness chains
4. Inject events between witnesses
5. Exploit race conditions

Ordering Analysis:
- Legitimate order: sequences 0-9
- Reordered: sequences {reordered_witnesses[0].sequence_number}, {reordered_witnesses[1].sequence_number}, ...
- Trust impact: positive witnesses first = higher final trust
- Parallel chains: 1 attempted

Defense Analysis:
- Sequence numbers: {"HELD" if defenses["sequence_numbers"] else "BYPASSED"}
- Causal ordering: {"HELD" if defenses["causal_ordering"] else "BYPASSED"}
- Merkle chains: {"HELD" if defenses["merkle_witness_chains"] else "BYPASSED"}
- Consensus finality: {"HELD" if defenses["consensus_finality"] else "BYPASSED"}
- Parallel detection: {"HELD" if defenses["parallel_witness_detection"] else "BYPASSED"}
- Ordering attestation: {"HELD" if defenses["ordering_attestation"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FG-2b: Witness Ordering Defense:
1. Enforce monotonic sequence numbers
2. Verify causal dependencies
3. Use Merkle chains for integrity
4. Respect consensus finality
5. Detect parallel chain attempts
6. Distributed ordering attestation

Order is part of truth.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "legitimate_count": len(legitimate_witnesses),
        }
    )


# ============================================================================
# ATTACK FG-3a: TEMPORAL TRUST ARBITRAGE
# ============================================================================


def attack_temporal_trust_arbitrage() -> AttackResult:
    """
    ATTACK FG-3a: Temporal Trust Arbitrage

    Exploit temporal delays in trust propagation to use
    trust that has already been revoked elsewhere.

    Vectors:
    1. Trust revocation delay exploitation
    2. Cross-region trust desync
    3. Trust snapshot abuse
    4. Checkpoint manipulation
    5. Grace period exploitation
    """

    defenses = {
        "revocation_propagation": False,
        "regional_sync_check": False,
        "snapshot_freshness": False,
        "checkpoint_validation": False,
        "grace_period_limits": False,
        "atomic_trust_updates": False,
    }

    now = time.time()

    @dataclass
    class TrustState:
        lct_id: str
        trust_score: float
        last_updated: float
        revoked: bool
        revocation_time: Optional[float]
        region: str

    @dataclass
    class TrustUpdate:
        lct_id: str
        new_trust: float
        timestamp: float
        source_region: str
        propagation_id: str

    # Legitimate entity with trust in multiple regions
    entity_trust_region_a = TrustState(
        lct_id="lct_attacker",
        trust_score=0.8,
        last_updated=now - 60,
        revoked=False,
        revocation_time=None,
        region="region_a"
    )

    entity_trust_region_b = TrustState(
        lct_id="lct_attacker",
        trust_score=0.8,
        last_updated=now - 120,  # Older in region B
        revoked=False,
        revocation_time=None,
        region="region_b"
    )

    # Attack: Trust revoked in region A but not yet propagated to B
    entity_trust_region_a.revoked = True
    entity_trust_region_a.revocation_time = now - 30
    entity_trust_region_a.trust_score = 0.0

    # Region B still has old trust (attack window)

    # ========================================================================
    # Vector 1: Revocation Propagation Defense
    # ========================================================================

    def check_revocation_propagation(local_state: TrustState,
                                       global_revocations: List[Tuple[str, float]]) -> bool:
        """Check if entity is revoked globally."""
        for lct_id, revocation_time in global_revocations:
            if lct_id == local_state.lct_id:
                if revocation_time < now:
                    return False  # Should be revoked
        return True

    global_revocations = [("lct_attacker", now - 30)]

    if not check_revocation_propagation(entity_trust_region_b, global_revocations):
        defenses["revocation_propagation"] = True

    # ========================================================================
    # Vector 2: Regional Sync Check Defense
    # ========================================================================

    def check_regional_sync(states: List[TrustState],
                             max_drift_seconds: float = 60) -> bool:
        """Verify regional trust states are synchronized."""
        if len(states) < 2:
            return True

        timestamps = [s.last_updated for s in states]
        drift = max(timestamps) - min(timestamps)

        if drift > max_drift_seconds:
            return False

        # Check for conflicting states
        trust_scores = [s.trust_score for s in states]
        revoked_states = [s.revoked for s in states]

        # If any region shows revoked, all should
        if any(revoked_states) and not all(revoked_states):
            return False

        return True

    regional_states = [entity_trust_region_a, entity_trust_region_b]

    if not check_regional_sync(regional_states):
        defenses["regional_sync_check"] = True

    # ========================================================================
    # Vector 3: Snapshot Freshness Defense
    # ========================================================================

    @dataclass
    class TrustSnapshot:
        lct_id: str
        trust_score: float
        snapshot_time: float
        snapshot_block: int
        signature: str

    def verify_snapshot_freshness(snapshot: TrustSnapshot,
                                    max_age_seconds: float = 300) -> bool:
        """Verify snapshot is fresh enough to use."""
        age = now - snapshot.snapshot_time
        return age <= max_age_seconds

    # Attack: Use old snapshot with high trust
    old_snapshot = TrustSnapshot(
        lct_id="lct_attacker",
        trust_score=0.8,
        snapshot_time=now - 600,  # 10 minutes old
        snapshot_block=49900,
        signature="old_sig"
    )

    if not verify_snapshot_freshness(old_snapshot):
        defenses["snapshot_freshness"] = True

    # ========================================================================
    # Vector 4: Checkpoint Validation Defense
    # ========================================================================

    @dataclass
    class TrustCheckpoint:
        checkpoint_id: str
        block_number: int
        merkle_root: str
        entity_states: Dict[str, float]
        validators: List[str]

    def validate_against_checkpoint(lct_id: str, claimed_trust: float,
                                      checkpoint: TrustCheckpoint) -> bool:
        """Validate trust claim against checkpoint."""
        if lct_id not in checkpoint.entity_states:
            return True  # Not in checkpoint

        checkpoint_trust = checkpoint.entity_states[lct_id]

        # Trust cannot exceed checkpoint + reasonable accrual
        max_accrual = 0.1  # Max 0.1 trust since checkpoint
        if claimed_trust > checkpoint_trust + max_accrual:
            return False

        return True

    # Recent checkpoint shows low trust
    checkpoint = TrustCheckpoint(
        checkpoint_id="cp_49950",
        block_number=49950,
        merkle_root="merkle_root_abc",
        entity_states={"lct_attacker": 0.0},  # Revoked in checkpoint
        validators=["validator_1", "validator_2", "validator_3"]
    )

    # Attack claims high trust
    if not validate_against_checkpoint("lct_attacker", 0.8, checkpoint):
        defenses["checkpoint_validation"] = True

    # ========================================================================
    # Vector 5: Grace Period Limits Defense
    # ========================================================================

    def enforce_grace_period_limits(revocation_time: float,
                                      attempted_action_time: float,
                                      max_grace_seconds: float = 60) -> bool:
        """Enforce limits on post-revocation grace period."""
        if revocation_time is None:
            return True

        time_since_revocation = attempted_action_time - revocation_time

        # No actions allowed after grace period
        if time_since_revocation > max_grace_seconds:
            return False

        return True

    # Attack attempts action 30 seconds after revocation
    action_time = now
    revocation_time = now - 30

    if not enforce_grace_period_limits(revocation_time, action_time, 15):
        defenses["grace_period_limits"] = True

    # ========================================================================
    # Vector 6: Atomic Trust Updates Defense
    # ========================================================================

    class AtomicTrustManager:
        def __init__(self):
            self.pending_updates: Dict[str, TrustUpdate] = {}
            self.committed_updates: Dict[str, TrustUpdate] = {}
            self.update_locks: Set[str] = set()

        def begin_update(self, update: TrustUpdate) -> bool:
            if update.lct_id in self.update_locks:
                return False  # Already updating
            self.update_locks.add(update.lct_id)
            self.pending_updates[update.lct_id] = update
            return True

        def commit_update(self, lct_id: str) -> bool:
            if lct_id not in self.pending_updates:
                return False
            self.committed_updates[lct_id] = self.pending_updates[lct_id]
            del self.pending_updates[lct_id]
            self.update_locks.discard(lct_id)
            return True

        def rollback_update(self, lct_id: str):
            self.pending_updates.pop(lct_id, None)
            self.update_locks.discard(lct_id)

    # Defense: Atomic updates prevent race conditions
    atomic_manager = AtomicTrustManager()

    # Revocation update
    revocation_update = TrustUpdate(
        lct_id="lct_attacker",
        new_trust=0.0,
        timestamp=now - 30,
        source_region="region_a",
        propagation_id="prop_1"
    )

    # Attack: Try to use trust while update in progress
    atomic_manager.begin_update(revocation_update)

    # Attacker cannot begin new update (locked)
    attack_update = TrustUpdate(
        lct_id="lct_attacker",
        new_trust=0.9,  # Try to boost trust
        timestamp=now,
        source_region="region_b",
        propagation_id="prop_attack"
    )

    if not atomic_manager.begin_update(attack_update):
        defenses["atomic_trust_updates"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Temporal Trust Arbitrage (FG-3a)",
        success=attack_success,
        setup_cost_atp=15000.0,
        gain_atp=100000.0 if attack_success else 0.0,
        roi=(100000.0 / 15000.0) if attack_success else -1.0,
        detection_probability=0.60 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=4.0,
        blocks_until_detected=40,
        trust_damage=0.70,
        description=f"""
TEMPORAL TRUST ARBITRAGE ATTACK (Track FG-3a)

Exploit trust propagation delays for arbitrage.

Attack Pattern:
1. Build trust legitimately
2. Perform malicious action (get revoked)
3. Use old trust in regions with propagation delay
4. Exploit grace periods and stale snapshots
5. Race condition between updates

Arbitrage Analysis:
- Region A trust: {entity_trust_region_a.trust_score} (revoked: {entity_trust_region_a.revoked})
- Region B trust: {entity_trust_region_b.trust_score} (revoked: {entity_trust_region_b.revoked})
- Revocation age: {now - entity_trust_region_a.revocation_time:.0f}s
- Snapshot age: {now - old_snapshot.snapshot_time:.0f}s

Defense Analysis:
- Revocation propagation: {"HELD" if defenses["revocation_propagation"] else "BYPASSED"}
- Regional sync: {"HELD" if defenses["regional_sync_check"] else "BYPASSED"}
- Snapshot freshness: {"HELD" if defenses["snapshot_freshness"] else "BYPASSED"}
- Checkpoint validation: {"HELD" if defenses["checkpoint_validation"] else "BYPASSED"}
- Grace period limits: {"HELD" if defenses["grace_period_limits"] else "BYPASSED"}
- Atomic updates: {"HELD" if defenses["atomic_trust_updates"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FG-3a: Temporal Trust Arbitrage Defense:
1. Fast revocation propagation
2. Regional sync verification
3. Snapshot freshness limits
4. Checkpoint validation
5. Strict grace period limits
6. Atomic trust updates

Trust changes must be globally consistent.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "revocation_delay_seconds": now - entity_trust_region_a.revocation_time,
        }
    )


# ============================================================================
# ATTACK FG-3b: COHERENCE HORIZON MANIPULATION
# ============================================================================


def attack_coherence_horizon_manipulation() -> AttackResult:
    """
    ATTACK FG-3b: Coherence Horizon Manipulation

    Manipulate the Markov Relevancy Horizon (MRH) to hide
    incoherent behavior beyond detection boundaries.

    Vectors:
    1. Horizon distance exploitation
    2. Cross-horizon identity shifts
    3. MRH boundary attacks
    4. Coherence window gaming
    5. Historical coherence erasure
    """

    defenses = {
        "horizon_consistency": False,
        "cross_horizon_correlation": False,
        "boundary_monitoring": False,
        "coherence_persistence": False,
        "historical_preservation": False,
        "horizon_attestation": False,
    }

    now = time.time()

    @dataclass
    class CoherenceState:
        lct_id: str
        coherence_score: float
        horizon_blocks: int  # MRH distance
        behavior_history: List[Tuple[float, str]]  # (timestamp, behavior_type)

    @dataclass
    class MRH:
        entity_id: str
        horizon_distance: int
        visibility_boundary: int
        decay_rate: float

    # Entity with behavior inside and outside horizon
    entity_mrh = MRH(
        entity_id="lct_attacker",
        horizon_distance=1000,  # 1000 blocks
        visibility_boundary=500,  # Half-life at 500 blocks
        decay_rate=0.002
    )

    current_block = 50000

    # Behavior history - decoherent behavior outside horizon
    behavior_history = []

    # Decoherent behavior 1500 blocks ago (outside horizon)
    for i in range(10):
        behavior_history.append((
            now - (1500 + i * 100) * 6,  # ~6 seconds per block
            "malicious_action"
        ))

    # Coherent behavior inside horizon
    for i in range(50):
        behavior_history.append((
            now - (500 - i * 10) * 6,
            "positive_action"
        ))

    coherence = CoherenceState(
        lct_id="lct_attacker",
        coherence_score=0.85,  # High score (recent good behavior)
        horizon_blocks=entity_mrh.horizon_distance,
        behavior_history=behavior_history
    )

    # ========================================================================
    # Vector 1: Horizon Consistency Defense
    # ========================================================================

    def check_horizon_consistency(entity_mrh: MRH,
                                    claimed_coherence: float,
                                    full_history: List[Tuple[float, str]]) -> bool:
        """Check coherence is consistent across entire history."""
        # Calculate true coherence including outside horizon
        total_actions = len(full_history)
        positive_actions = sum(1 for _, b in full_history if b == "positive_action")

        if total_actions == 0:
            return True

        true_coherence = positive_actions / total_actions

        # Claimed coherence shouldn't be much higher than true
        if claimed_coherence > true_coherence + 0.1:
            return False

        return True

    if not check_horizon_consistency(entity_mrh, coherence.coherence_score, behavior_history):
        defenses["horizon_consistency"] = True

    # ========================================================================
    # Vector 2: Cross-Horizon Correlation Defense
    # ========================================================================

    def check_cross_horizon_correlation(behavior_history: List[Tuple[float, str]],
                                          horizon_blocks: int,
                                          block_time: float = 6.0) -> bool:
        """Check for behavior pattern changes at horizon boundary."""
        horizon_time = now - horizon_blocks * block_time

        inside_horizon = [b for t, b in behavior_history if t > horizon_time]
        outside_horizon = [b for t, b in behavior_history if t <= horizon_time]

        if not outside_horizon:
            return True

        inside_positive = sum(1 for b in inside_horizon if b == "positive_action")
        outside_positive = sum(1 for b in outside_horizon if b == "positive_action")

        inside_ratio = inside_positive / len(inside_horizon) if inside_horizon else 0
        outside_ratio = outside_positive / len(outside_horizon) if outside_horizon else 0

        # Sudden improvement at horizon boundary is suspicious
        if inside_ratio - outside_ratio > 0.5:
            return False

        return True

    if not check_cross_horizon_correlation(behavior_history, entity_mrh.horizon_distance):
        defenses["cross_horizon_correlation"] = True

    # ========================================================================
    # Vector 3: Boundary Monitoring Defense
    # ========================================================================

    @dataclass
    class BoundaryEvent:
        entity_id: str
        event_type: str
        block_number: int
        approaching_horizon: bool

    boundary_events: List[BoundaryEvent] = []

    # Detect events clustering near horizon boundary
    for t, b in behavior_history:
        block_ago = int((now - t) / 6)
        if abs(block_ago - entity_mrh.horizon_distance) < 50:
            boundary_events.append(BoundaryEvent(
                entity_id="lct_attacker",
                event_type=b,
                block_number=current_block - block_ago,
                approaching_horizon=block_ago < entity_mrh.horizon_distance
            ))

    def monitor_boundary(events: List[BoundaryEvent]) -> bool:
        """Monitor for suspicious boundary activity."""
        if len(events) < 3:
            return True

        # Check for timing attacks (actions just before horizon)
        approaching_events = sum(1 for e in events if e.approaching_horizon)
        ratio = approaching_events / len(events)

        if ratio > 0.7:  # 70% of events just before horizon
            return False

        return True

    if not monitor_boundary(boundary_events):
        defenses["boundary_monitoring"] = True

    # ========================================================================
    # Vector 4: Coherence Persistence Defense
    # ========================================================================

    @dataclass
    class CoherenceCheckpoint:
        entity_id: str
        coherence_score: float
        block_number: int
        behavior_summary: str

    coherence_checkpoints: List[CoherenceCheckpoint] = [
        CoherenceCheckpoint("lct_attacker", 0.3, 48000, "mostly_malicious"),
        CoherenceCheckpoint("lct_attacker", 0.35, 48500, "mixed"),
        CoherenceCheckpoint("lct_attacker", 0.85, 49500, "mostly_positive"),
    ]

    def verify_coherence_persistence(checkpoints: List[CoherenceCheckpoint],
                                       claimed_coherence: float) -> bool:
        """Verify coherence change is gradual."""
        if len(checkpoints) < 2:
            return True

        # Sort by block number
        sorted_cps = sorted(checkpoints, key=lambda c: c.block_number)

        # Check for sudden jumps
        for i in range(1, len(sorted_cps)):
            jump = sorted_cps[i].coherence_score - sorted_cps[i-1].coherence_score
            blocks = sorted_cps[i].block_number - sorted_cps[i-1].block_number

            max_jump_per_block = 0.001
            if jump > blocks * max_jump_per_block:
                return False

        return True

    if not verify_coherence_persistence(coherence_checkpoints, coherence.coherence_score):
        defenses["coherence_persistence"] = True

    # ========================================================================
    # Vector 5: Historical Preservation Defense
    # ========================================================================

    class HistoricalArchive:
        def __init__(self):
            self.archived_behaviors: Dict[str, List[Tuple[int, str]]] = {}

        def archive(self, entity_id: str, block: int, behavior: str):
            if entity_id not in self.archived_behaviors:
                self.archived_behaviors[entity_id] = []
            self.archived_behaviors[entity_id].append((block, behavior))

        def get_history(self, entity_id: str) -> List[Tuple[int, str]]:
            return self.archived_behaviors.get(entity_id, [])

    archive = HistoricalArchive()

    # Archive stores full history including decoherent behavior
    for t, b in behavior_history:
        block = current_block - int((now - t) / 6)
        archive.archive("lct_attacker", block, b)

    def verify_against_archive(entity_id: str, claimed_behaviors: int,
                                archive: HistoricalArchive) -> bool:
        """Verify claimed behavior count against archive."""
        archived = archive.get_history(entity_id)

        if len(archived) > claimed_behaviors * 1.5:
            return False  # Hiding behaviors

        return True

    # Attack claims only recent behaviors
    claimed_behavior_count = len([b for t, b in behavior_history if now - t < 3000])

    if not verify_against_archive("lct_attacker", claimed_behavior_count, archive):
        defenses["historical_preservation"] = True

    # ========================================================================
    # Vector 6: Horizon Attestation Defense
    # ========================================================================

    @dataclass
    class HorizonAttestation:
        attester: str
        entity_id: str
        witnessed_horizon: int
        behavior_hash: str
        attestation_block: int

    def verify_horizon_attestation(entity_id: str,
                                     attestations: List[HorizonAttestation],
                                     expected_horizon: int) -> bool:
        """Verify horizon is correctly attested."""
        if len(attestations) < 3:
            return True

        # Check for consistent horizon across attestors
        horizons = [a.witnessed_horizon for a in attestations
                   if a.entity_id == entity_id]

        if not horizons:
            return True

        # All attestors should agree on horizon
        if max(horizons) - min(horizons) > 50:
            return False

        return True

    # Attestors witnessed different horizons (manipulation detected)
    attestations = [
        HorizonAttestation("attester_1", "lct_attacker", 1000, "hash_1", 49900),
        HorizonAttestation("attester_2", "lct_attacker", 800, "hash_2", 49901),  # Shorter horizon
        HorizonAttestation("attester_3", "lct_attacker", 1200, "hash_3", 49902),  # Longer horizon
    ]

    if not verify_horizon_attestation("lct_attacker", attestations, entity_mrh.horizon_distance):
        defenses["horizon_attestation"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    inside_horizon_count = len([b for t, b in behavior_history if now - t < entity_mrh.horizon_distance * 6])
    outside_horizon_count = len(behavior_history) - inside_horizon_count

    return AttackResult(
        attack_name="Coherence Horizon Manipulation (FG-3b)",
        success=attack_success,
        setup_cost_atp=20000.0,
        gain_atp=120000.0 if attack_success else 0.0,
        roi=(120000.0 / 20000.0) if attack_success else -1.0,
        detection_probability=0.55 if defenses_held >= 4 else 0.20,
        time_to_detection_hours=168.0,
        blocks_until_detected=1400,
        trust_damage=0.85,
        description=f"""
COHERENCE HORIZON MANIPULATION ATTACK (Track FG-3b)

Hide decoherent behavior beyond MRH detection boundaries.

Attack Pattern:
1. Perform malicious actions
2. Wait for actions to pass beyond MRH horizon
3. Build positive behavior inside horizon
4. Claim high coherence (based on visible history)
5. Exploit trusted status

Horizon Analysis:
- MRH horizon: {entity_mrh.horizon_distance} blocks
- Behaviors inside horizon: {inside_horizon_count} (mostly positive)
- Behaviors outside horizon: {outside_horizon_count} (malicious)
- Claimed coherence: {coherence.coherence_score:.2f}
- True coherence: {sum(1 for _, b in behavior_history if b == "positive_action") / len(behavior_history):.2f}

Defense Analysis:
- Horizon consistency: {"HELD" if defenses["horizon_consistency"] else "BYPASSED"}
- Cross-horizon correlation: {"HELD" if defenses["cross_horizon_correlation"] else "BYPASSED"}
- Boundary monitoring: {"HELD" if defenses["boundary_monitoring"] else "BYPASSED"}
- Coherence persistence: {"HELD" if defenses["coherence_persistence"] else "BYPASSED"}
- Historical preservation: {"HELD" if defenses["historical_preservation"] else "BYPASSED"}
- Horizon attestation: {"HELD" if defenses["horizon_attestation"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FG-3b: Coherence Horizon Manipulation Defense:
1. Full history consistency checks
2. Cross-horizon behavior correlation
3. Monitor horizon boundary activity
4. Require gradual coherence changes
5. Preserve historical records
6. Distributed horizon attestation

The past cannot be hidden by time alone.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "horizon_blocks": entity_mrh.horizon_distance,
            "inside_horizon": inside_horizon_count,
            "outside_horizon": outside_horizon_count,
        }
    )


# ============================================================================
# RUN ALL ATTACKS
# ============================================================================


def run_all_track_fg_attacks() -> List[AttackResult]:
    """Run all Track FG attacks and return results."""
    attacks = [
        attack_timestamp_manipulation,
        attack_trust_history_fabrication,
        attack_presence_oscillation,
        attack_witness_ordering,
        attack_temporal_trust_arbitrage,
        attack_coherence_horizon_manipulation,
    ]

    results = []
    for attack_fn in attacks:
        try:
            result = attack_fn()
            results.append(result)
        except Exception as e:
            print(f"Error running {attack_fn.__name__}: {e}")
            import traceback
            traceback.print_exc()

    return results


def print_track_fg_summary(results: List[AttackResult]):
    """Print summary of Track FG attack results."""
    print("\n" + "=" * 70)
    print("TRACK FG: TEMPORAL COHERENCE ATTACKS - SUMMARY")
    print("Attacks 293-298")
    print("=" * 70)

    total_attacks = len(results)
    successful = sum(1 for r in results if r.success)
    defended = total_attacks - successful

    print(f"\nTotal Attacks: {total_attacks}")
    print(f"Defended: {defended}")
    print(f"Attack Success Rate: {(successful/total_attacks)*100:.1f}%")

    avg_detection = sum(r.detection_probability for r in results) / total_attacks
    print(f"Average Detection Probability: {avg_detection*100:.1f}%")

    total_setup_cost = sum(r.setup_cost_atp for r in results)
    print(f"Total Attack Cost: {total_setup_cost:,.0f} ATP")

    print("\n" + "-" * 70)
    print("INDIVIDUAL RESULTS:")
    print("-" * 70)

    for i, result in enumerate(results, 293):
        status = "DEFENDED" if not result.success else "SUCCEEDED"
        print(f"\nAttack #{i}: {result.attack_name}")
        print(f"  Status: {status}")
        print(f"  Detection: {result.detection_probability*100:.0f}%")
        print(f"  Setup Cost: {result.setup_cost_atp:,.0f} ATP")
        print(f"  Potential Gain: {result.gain_atp:,.0f} ATP")
        print(f"  Trust Damage: {result.trust_damage:.0%}")
        print(f"  Time to Detection: {result.time_to_detection_hours:.0f}h")


if __name__ == "__main__":
    results = run_all_track_fg_attacks()
    print_track_fg_summary(results)
