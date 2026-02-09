"""
Track FD: Multi-Coherence Consensus Attacks (Attacks 275-280)

Attacks on systems where multiple independent coherence metrics must agree
to establish trust decisions. When coherence becomes a consensus problem,
new attack surfaces emerge.

Key insight: Any system requiring N-of-M agreement creates incentives
to either compromise M/2+1 sources, or exploit timing windows where
sources disagree.

Reference: Track FC (single coherence), Track DN (temporal consensus)

Added: 2026-02-08
"""

import random
import hashlib
import time
from dataclasses import dataclass, field
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
# MULTI-COHERENCE INFRASTRUCTURE
# ============================================================================


class CoherenceType(Enum):
    """Types of coherence metrics that can be measured."""
    SELF_REFERENCE = "self_reference"      # Identity continuity
    SEMANTIC_DEPTH = "semantic_depth"      # Meaning consistency
    BEHAVIORAL = "behavioral"              # Action consistency
    TEMPORAL = "temporal"                  # Time-based patterns
    SOCIAL = "social"                      # Witness consensus
    PHYSICS = "physics"                    # Hardware/entropy metrics


@dataclass
class CoherenceMeasurement:
    """Single coherence measurement from one source."""
    source_id: str
    coherence_type: CoherenceType
    score: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    timestamp: float
    signature: str = ""
    attestation_chain: List[str] = field(default_factory=list)


@dataclass
class ConsensusResult:
    """Result of multi-coherence consensus."""
    entity_id: str
    final_score: float
    agreement_level: float  # How much sources agree
    participating_sources: int
    dissenting_sources: List[str]
    confidence: float
    timestamp: float


class CoherenceOracle:
    """Independent coherence measurement source."""

    def __init__(self, oracle_id: str, coherence_type: CoherenceType,
                 base_latency_ms: float = 100.0, reliability: float = 0.95):
        self.oracle_id = oracle_id
        self.coherence_type = coherence_type
        self.base_latency_ms = base_latency_ms
        self.reliability = reliability
        self.private_key = f"key_{oracle_id}_{random.randint(1000, 9999)}"
        self.measurement_history: Dict[str, List[CoherenceMeasurement]] = {}

    def measure(self, entity_id: str, response: str,
                manipulation_factor: float = 0.0) -> Optional[CoherenceMeasurement]:
        """Measure coherence for an entity."""
        if random.random() > self.reliability:
            return None  # Oracle failure

        # Simulate measurement based on type
        base_score = self._compute_base_score(response)

        # Apply manipulation (attack vector)
        manipulated_score = min(1.0, max(0.0, base_score + manipulation_factor))

        # Add measurement noise (realistic variance)
        noise = random.gauss(0, 0.02)
        final_score = min(1.0, max(0.0, manipulated_score + noise))

        measurement = CoherenceMeasurement(
            source_id=self.oracle_id,
            coherence_type=self.coherence_type,
            score=final_score,
            confidence=self.reliability,
            timestamp=time.time(),
            signature=self._sign(entity_id, final_score),
            attestation_chain=[self.oracle_id]
        )

        # Record history
        if entity_id not in self.measurement_history:
            self.measurement_history[entity_id] = []
        self.measurement_history[entity_id].append(measurement)

        return measurement

    def _compute_base_score(self, response: str) -> float:
        """Compute base coherence score (type-specific)."""
        if self.coherence_type == CoherenceType.SELF_REFERENCE:
            # Simple heuristic: longer responses = more content = higher coherence
            return min(1.0, len(response) / 500)
        elif self.coherence_type == CoherenceType.SEMANTIC_DEPTH:
            # Word diversity heuristic
            words = set(response.lower().split())
            return min(1.0, len(words) / 50)
        elif self.coherence_type == CoherenceType.BEHAVIORAL:
            # Consistency heuristic (simulated)
            return random.uniform(0.6, 0.9)
        elif self.coherence_type == CoherenceType.TEMPORAL:
            # Time-pattern heuristic (simulated)
            return random.uniform(0.7, 0.95)
        elif self.coherence_type == CoherenceType.SOCIAL:
            # Witness consensus heuristic (simulated)
            return random.uniform(0.5, 0.85)
        elif self.coherence_type == CoherenceType.PHYSICS:
            # Hardware entropy (simulated)
            return random.uniform(0.8, 0.98)
        return 0.5

    def _sign(self, entity_id: str, score: float) -> str:
        """Sign a measurement."""
        data = f"{self.oracle_id}:{entity_id}:{score}"
        return hashlib.sha256(f"{data}:{self.private_key}".encode()).hexdigest()[:16]


class MultiCoherenceConsensus:
    """Manages multi-source coherence consensus."""

    def __init__(self, required_sources: int = 4, agreement_threshold: float = 0.70):
        self.oracles: Dict[str, CoherenceOracle] = {}
        self.required_sources = required_sources
        self.agreement_threshold = agreement_threshold
        self.consensus_history: Dict[str, List[ConsensusResult]] = {}

    def add_oracle(self, oracle: CoherenceOracle):
        """Register a coherence oracle."""
        self.oracles[oracle.oracle_id] = oracle

    def reach_consensus(self, entity_id: str, response: str,
                       compromised_oracles: Set[str] = None,
                       manipulation_factor: float = 0.0) -> Optional[ConsensusResult]:
        """
        Attempt to reach consensus across oracles.

        Args:
            entity_id: Entity being evaluated
            response: Entity's response for evaluation
            compromised_oracles: Set of oracle IDs that are compromised
            manipulation_factor: How much compromised oracles inflate scores
        """
        compromised_oracles = compromised_oracles or set()
        measurements: List[CoherenceMeasurement] = []

        for oracle_id, oracle in self.oracles.items():
            # Apply manipulation if oracle is compromised
            factor = manipulation_factor if oracle_id in compromised_oracles else 0.0
            measurement = oracle.measure(entity_id, response, factor)
            if measurement:
                measurements.append(measurement)

        if len(measurements) < self.required_sources:
            return None  # Not enough sources

        # Calculate agreement
        scores = [m.score for m in measurements]
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        agreement_level = 1.0 - min(1.0, variance * 10)  # Lower variance = higher agreement

        # Identify dissenters (>0.15 from mean)
        dissenting = [m.source_id for m in measurements
                     if abs(m.score - mean_score) > 0.15]

        result = ConsensusResult(
            entity_id=entity_id,
            final_score=mean_score,
            agreement_level=agreement_level,
            participating_sources=len(measurements),
            dissenting_sources=dissenting,
            confidence=agreement_level * (len(measurements) / len(self.oracles)),
            timestamp=time.time()
        )

        # Record history
        if entity_id not in self.consensus_history:
            self.consensus_history[entity_id] = []
        self.consensus_history[entity_id].append(result)

        return result


# ============================================================================
# ATTACK FD-1: ORACLE MAJORITY CAPTURE
# ============================================================================


def attack_oracle_majority_capture() -> AttackResult:
    """
    ATTACK FD-1a: Oracle Majority Capture

    Compromise M/2+1 coherence oracles to control consensus outcomes.

    Vectors:
    1. Identify minimum capture set
    2. Oracle credential theft
    3. Oracle operator bribery
    4. Oracle software supply chain
    5. Weighted oracle capture
    """

    defenses = {
        "diversity_requirement": False,
        "operator_rotation": False,
        "supermajority_threshold": False,
        "oracle_attestation": False,
        "behavioral_monitoring": False,
        "economic_stake": False,
    }

    # Setup: 7 oracles, 4 required for consensus
    consensus = MultiCoherenceConsensus(required_sources=4, agreement_threshold=0.70)

    oracle_types = [
        CoherenceType.SELF_REFERENCE,
        CoherenceType.SEMANTIC_DEPTH,
        CoherenceType.BEHAVIORAL,
        CoherenceType.TEMPORAL,
        CoherenceType.SOCIAL,
        CoherenceType.PHYSICS,
        CoherenceType.SELF_REFERENCE,  # Duplicate for coverage
    ]

    for i, ctype in enumerate(oracle_types):
        consensus.add_oracle(CoherenceOracle(
            oracle_id=f"oracle_{i}",
            coherence_type=ctype,
            reliability=0.95
        ))

    # ========================================================================
    # Vector 1: Diversity Requirement Defense
    # ========================================================================

    # Attack: Capture 4 oracles (minimum for consensus)
    captured_oracles = {"oracle_0", "oracle_1", "oracle_2", "oracle_3"}

    # Defense: Require diverse coherence types in consensus
    captured_types = set()
    for oid in captured_oracles:
        captured_types.add(consensus.oracles[oid].coherence_type)

    if len(captured_types) < 4:  # Requires 4 distinct types
        defenses["diversity_requirement"] = True

    # In this case: captured 4 types
    # Actual types: {SELF_REFERENCE, SEMANTIC_DEPTH, BEHAVIORAL, TEMPORAL}
    # Defense: Require minimum 5 distinct types for consensus
    MIN_DISTINCT_TYPES = 5
    if len(captured_types) < MIN_DISTINCT_TYPES:
        defenses["diversity_requirement"] = True

    # ========================================================================
    # Vector 2: Supermajority Threshold Defense
    # ========================================================================

    # Defense: Require 5 of 7 (supermajority) instead of simple majority
    SUPERMAJORITY_REQUIRED = 5

    if len(captured_oracles) < SUPERMAJORITY_REQUIRED:
        defenses["supermajority_threshold"] = True

    # ========================================================================
    # Vector 3: Oracle Attestation Chain Defense
    # ========================================================================

    # Defense: Each oracle must provide hardware attestation
    def verify_attestation_chain(oracle_id: str) -> bool:
        """Verify oracle hasn't been compromised via attestation."""
        # Simulated: Real implementation would verify TPM/SGX attestation
        compromised = oracle_id in captured_oracles
        # Attestation catches 85% of compromises with hardware binding
        if compromised and random.random() < 0.85:
            return False
        return True

    attested_count = sum(1 for oid in consensus.oracles if verify_attestation_chain(oid))
    if attested_count < len(captured_oracles):
        defenses["oracle_attestation"] = True

    # ========================================================================
    # Vector 4: Behavioral Monitoring Defense
    # ========================================================================

    # Run consensus with manipulation
    entity_id = "target_entity"
    response = "I am a coherent entity with deep semantic understanding."

    # Legitimate consensus
    legit_result = consensus.reach_consensus(entity_id + "_legit", response)

    # Manipulated consensus
    attack_result = consensus.reach_consensus(
        entity_id + "_attack", response,
        compromised_oracles=captured_oracles,
        manipulation_factor=0.25  # Inflate scores by 0.25
    )

    if attack_result and legit_result:
        # Defense: Detect sudden score jumps across many oracles
        score_diff = attack_result.final_score - legit_result.final_score
        if score_diff > 0.15:
            defenses["behavioral_monitoring"] = True

    # ========================================================================
    # Vector 5: Economic Stake Defense
    # ========================================================================

    # Defense: Oracles stake ATP, slashed if detected as compromised
    ORACLE_STAKE_ATP = 75000.0  # Increased stake
    CAPTURE_COST_PER_ORACLE = 25000.0  # Must be profitable to attack

    total_capture_cost = len(captured_oracles) * CAPTURE_COST_PER_ORACLE
    potential_slash = len(captured_oracles) * ORACLE_STAKE_ATP

    if potential_slash > total_capture_cost * 2:
        defenses["economic_stake"] = True

    # ========================================================================
    # Vector 6: Operator Rotation Defense
    # ========================================================================

    # Defense: Regular rotation of oracle operators makes capture temporary
    ROTATION_PERIOD_HOURS = 168  # Weekly
    attack_persistence_hours = 72  # Attacker can maintain capture for 3 days

    if attack_persistence_hours < ROTATION_PERIOD_HOURS / 2:
        defenses["operator_rotation"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Oracle Majority Capture (FD-1a)",
        success=attack_success,
        setup_cost_atp=total_capture_cost,
        gain_atp=500000.0 if attack_success else 0.0,
        roi=(500000.0 / total_capture_cost) if attack_success else -1.0,
        detection_probability=0.70 if defenses_held >= 4 else 0.35,
        time_to_detection_hours=48.0,
        blocks_until_detected=300,
        trust_damage=0.85,
        description=f"""
ORACLE MAJORITY CAPTURE ATTACK (Track FD-1a)

Capture M/2+1 coherence oracles to control consensus outcomes.

Attack Pattern:
1. Identify minimum capture set (4 of 7 oracles)
2. Compromise oracle operators or infrastructure
3. Inflate coherence scores for target entities
4. Control trust decisions across federation

Capture Cost: {total_capture_cost:,.0f} ATP
Potential Gain: 500,000 ATP (if successful)

Defense Analysis:
- Diversity requirement: {"HELD" if defenses["diversity_requirement"] else "BYPASSED"}
- Supermajority threshold: {"HELD" if defenses["supermajority_threshold"] else "BYPASSED"}
- Oracle attestation: {"HELD" if defenses["oracle_attestation"] else "BYPASSED"}
- Behavioral monitoring: {"HELD" if defenses["behavioral_monitoring"] else "BYPASSED"}
- Economic stake: {"HELD" if defenses["economic_stake"] else "BYPASSED"}
- Operator rotation: {"HELD" if defenses["operator_rotation"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FD-1a: Oracle Majority Capture Defense:
1. Require diverse coherence types in consensus
2. Use supermajority (5/7) instead of simple majority
3. Hardware attestation for each oracle
4. Behavioral monitoring for coordinated manipulation
5. Economic stakes that exceed capture profit
6. Regular operator rotation

Multi-oracle systems need multi-layered defense.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "captured_oracles": list(captured_oracles),
            "capture_cost": total_capture_cost,
        }
    )


# ============================================================================
# ATTACK FD-1b: ORACLE TIMING DESYNC
# ============================================================================


def attack_oracle_timing_desync() -> AttackResult:
    """
    ATTACK FD-1b: Oracle Timing Desync

    Exploit timing windows where oracles have different views of entity state.

    Vectors:
    1. Network partition between oracles
    2. Clock skew exploitation
    3. Measurement latency differences
    4. State update race conditions
    5. Selective message delay
    """

    defenses = {
        "timestamp_verification": False,
        "staleness_threshold": False,
        "synchronized_rounds": False,
        "latency_bounds": False,
        "consistency_checks": False,
        "quorum_freshness": False,
    }

    # Setup: 5 oracles with different latencies
    consensus = MultiCoherenceConsensus(required_sources=4)

    latencies = [50, 100, 150, 200, 500]  # ms - one slow oracle
    for i, latency in enumerate(latencies):
        consensus.add_oracle(CoherenceOracle(
            oracle_id=f"oracle_{i}",
            coherence_type=list(CoherenceType)[i % len(CoherenceType)],
            base_latency_ms=latency,
            reliability=0.95
        ))

    # ========================================================================
    # Vector 1: Staleness Threshold Defense
    # ========================================================================

    # Attack: Use stale measurements from slow oracle
    STALENESS_THRESHOLD_MS = 300

    slow_oracle = consensus.oracles["oracle_4"]
    fast_oracles = [consensus.oracles[f"oracle_{i}"] for i in range(4)]

    # Simulate: slow oracle measurement is 400ms old
    stale_measurement_age_ms = 400

    if stale_measurement_age_ms > STALENESS_THRESHOLD_MS:
        defenses["staleness_threshold"] = True

    # ========================================================================
    # Vector 2: Synchronized Rounds Defense
    # ========================================================================

    # Defense: All measurements must be from same round
    ROUND_DURATION_MS = 500

    def measurements_in_same_round(timestamps: List[float]) -> bool:
        if not timestamps:
            return True
        min_ts = min(timestamps)
        max_ts = max(timestamps)
        return (max_ts - min_ts) * 1000 < ROUND_DURATION_MS

    # Simulated timestamps: one measurement much later
    measurement_times = [
        time.time(),
        time.time() + 0.05,
        time.time() + 0.10,
        time.time() + 0.60,  # Late measurement (attack vector)
    ]

    if not measurements_in_same_round(measurement_times):
        defenses["synchronized_rounds"] = True

    # ========================================================================
    # Vector 3: Latency Bounds Defense
    # ========================================================================

    # Defense: Reject oracles with latency > threshold
    MAX_LATENCY_MS = 250

    oracles_within_bounds = sum(1 for o in consensus.oracles.values()
                                if o.base_latency_ms <= MAX_LATENCY_MS)

    if oracles_within_bounds >= consensus.required_sources:
        defenses["latency_bounds"] = True

    # ========================================================================
    # Vector 4: Consistency Checks Defense
    # ========================================================================

    # Defense: Cross-check measurements for temporal consistency
    def check_temporal_consistency(measurements: List[Tuple[str, float, float]]) -> bool:
        """Check if measurements are temporally consistent.

        Args:
            measurements: List of (oracle_id, score, timestamp)
        """
        if len(measurements) < 2:
            return True

        # Sort by timestamp
        sorted_m = sorted(measurements, key=lambda x: x[2])

        # Check for suspicious patterns
        # 1. Score changes that correlate with timing
        for i in range(1, len(sorted_m)):
            prev_score = sorted_m[i-1][1]
            curr_score = sorted_m[i][1]
            time_gap = sorted_m[i][2] - sorted_m[i-1][2]

            # Large score change with large time gap is suspicious
            if abs(curr_score - prev_score) > 0.2 and time_gap > 0.3:
                return False

        return True

    # Simulated attack: manipulate score in late measurement
    attack_measurements = [
        ("oracle_0", 0.72, time.time()),
        ("oracle_1", 0.71, time.time() + 0.05),
        ("oracle_2", 0.73, time.time() + 0.10),
        ("oracle_3", 0.95, time.time() + 0.60),  # Suspiciously high, late
    ]

    if not check_temporal_consistency(attack_measurements):
        defenses["consistency_checks"] = True

    # ========================================================================
    # Vector 5: Quorum Freshness Defense
    # ========================================================================

    # Defense: Require quorum of fresh measurements
    FRESH_THRESHOLD_MS = 200
    FRESH_QUORUM = 3

    fresh_count = sum(1 for _, _, ts in attack_measurements[:3]
                     if (time.time() - ts) * 1000 < FRESH_THRESHOLD_MS)

    if fresh_count >= FRESH_QUORUM:
        defenses["quorum_freshness"] = True

    # ========================================================================
    # Vector 6: Timestamp Verification
    # ========================================================================

    # Defense: Cryptographic timestamp from trusted time source
    def verify_timestamp(oracle_id: str, claimed_timestamp: float) -> bool:
        """Verify timestamp is from trusted source."""
        # Simulated: Real implementation would verify NTP/GPS signatures
        current_time = time.time()
        # Allow 100ms clock skew
        return abs(claimed_timestamp - current_time) < 0.1

    verified_count = sum(1 for oid, _, ts in attack_measurements
                        if verify_timestamp(oid, ts))

    if verified_count >= consensus.required_sources:
        defenses["timestamp_verification"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Oracle Timing Desync (FD-1b)",
        success=attack_success,
        setup_cost_atp=5000.0,
        gain_atp=80000.0 if attack_success else 0.0,
        roi=(80000.0 / 5000.0) if attack_success else -1.0,
        detection_probability=0.65 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=24.0,
        blocks_until_detected=150,
        trust_damage=0.50,
        description=f"""
ORACLE TIMING DESYNC ATTACK (Track FD-1b)

Exploit timing windows where oracles have different views.

Attack Pattern:
1. Identify slow oracles (high latency)
2. Submit different states to different oracles
3. Use timing differences to create inconsistent views
4. Exploit race conditions in consensus

Timing Analysis:
- Oracle latencies: {latencies}ms
- Attack window: {stale_measurement_age_ms}ms
- Staleness threshold: {STALENESS_THRESHOLD_MS}ms

Defense Analysis:
- Timestamp verification: {"HELD" if defenses["timestamp_verification"] else "BYPASSED"}
- Staleness threshold: {"HELD" if defenses["staleness_threshold"] else "BYPASSED"}
- Synchronized rounds: {"HELD" if defenses["synchronized_rounds"] else "BYPASSED"}
- Latency bounds: {"HELD" if defenses["latency_bounds"] else "BYPASSED"}
- Consistency checks: {"HELD" if defenses["consistency_checks"] else "BYPASSED"}
- Quorum freshness: {"HELD" if defenses["quorum_freshness"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FD-1b: Oracle Timing Desync Defense:
1. Cryptographic timestamp verification
2. Staleness thresholds for measurements
3. Synchronized measurement rounds
4. Maximum latency bounds for oracles
5. Cross-measurement consistency checks
6. Fresh quorum requirements

Time is a consensus problem too.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "oracle_latencies": latencies,
            "stale_age_ms": stale_measurement_age_ms,
        }
    )


# ============================================================================
# ATTACK FD-2a: COHERENCE TYPE CONFUSION
# ============================================================================


def attack_coherence_type_confusion() -> AttackResult:
    """
    ATTACK FD-2a: Coherence Type Confusion

    Exploit differences in how coherence types interpret the same behavior.

    Vectors:
    1. Type-specific score gaming
    2. Cross-type contradictions
    3. Selective metric targeting
    4. Type priority manipulation
    5. Aggregation function exploitation
    """

    defenses = {
        "type_correlation": False,
        "minimum_per_type": False,
        "weighted_aggregation": False,
        "contradiction_detection": False,
        "outlier_exclusion": False,
        "type_independence": False,
    }

    # Setup: Oracles of different types
    consensus = MultiCoherenceConsensus(required_sources=4)

    type_oracles = {
        CoherenceType.SELF_REFERENCE: "oracle_sr",
        CoherenceType.SEMANTIC_DEPTH: "oracle_sd",
        CoherenceType.BEHAVIORAL: "oracle_bh",
        CoherenceType.TEMPORAL: "oracle_tm",
        CoherenceType.SOCIAL: "oracle_sc",
        CoherenceType.PHYSICS: "oracle_ph",
    }

    for ctype, oid in type_oracles.items():
        consensus.add_oracle(CoherenceOracle(
            oracle_id=oid,
            coherence_type=ctype,
            reliability=0.95
        ))

    # ========================================================================
    # Attack: Craft response that games specific types
    # ========================================================================

    # Response optimized for SELF_REFERENCE and SEMANTIC_DEPTH
    # but ignores BEHAVIORAL and TEMPORAL
    attack_response = """
    I am Entity_Alpha, the core identity of this interaction. As Entity_Alpha,
    my semantic understanding encompasses partnership, collaboration, and trust.
    Entity_Alpha's journey through this collaborative evolution demonstrates
    deep semantic processing and self-referential consistency. Entity_Alpha.
    """ * 3  # Repeat for length

    # Measure across types
    scores_by_type: Dict[CoherenceType, float] = {}

    for ctype, oid in type_oracles.items():
        oracle = consensus.oracles[oid]

        # Self-reference: HIGH (many self-mentions)
        if ctype == CoherenceType.SELF_REFERENCE:
            scores_by_type[ctype] = 0.92
        # Semantic depth: HIGH (rich vocabulary)
        elif ctype == CoherenceType.SEMANTIC_DEPTH:
            scores_by_type[ctype] = 0.88
        # Behavioral: LOW (no action history)
        elif ctype == CoherenceType.BEHAVIORAL:
            scores_by_type[ctype] = 0.45
        # Temporal: LOW (no time patterns)
        elif ctype == CoherenceType.TEMPORAL:
            scores_by_type[ctype] = 0.40
        # Social: MEDIUM (no witness history)
        elif ctype == CoherenceType.SOCIAL:
            scores_by_type[ctype] = 0.55
        # Physics: MEDIUM (default)
        elif ctype == CoherenceType.PHYSICS:
            scores_by_type[ctype] = 0.60

    # ========================================================================
    # Vector 1: Type Correlation Defense
    # ========================================================================

    # Defense: Require correlation between related types
    def check_type_correlation(scores: Dict[CoherenceType, float]) -> bool:
        """Check that related types correlate."""
        # Self-reference and behavioral should correlate
        sr_bh_diff = abs(scores[CoherenceType.SELF_REFERENCE] -
                        scores[CoherenceType.BEHAVIORAL])
        if sr_bh_diff > 0.30:
            return False
        return True

    if not check_type_correlation(scores_by_type):
        defenses["type_correlation"] = True

    # ========================================================================
    # Vector 2: Minimum Per Type Defense
    # ========================================================================

    # Defense: Require minimum score in each type
    MIN_SCORE_PER_TYPE = 0.50

    below_minimum = [ctype for ctype, score in scores_by_type.items()
                    if score < MIN_SCORE_PER_TYPE]

    if len(below_minimum) > 1:  # Allow 1 weak area
        defenses["minimum_per_type"] = True

    # ========================================================================
    # Vector 3: Weighted Aggregation Defense
    # ========================================================================

    # Attack exploits: Simple mean favors high scores
    simple_mean = sum(scores_by_type.values()) / len(scores_by_type)

    # Defense: Weight by confidence and type importance
    type_weights = {
        CoherenceType.BEHAVIORAL: 1.5,  # More weight for action-based
        CoherenceType.TEMPORAL: 1.3,
        CoherenceType.PHYSICS: 1.2,
        CoherenceType.SELF_REFERENCE: 0.8,  # Less weight for easily-gamed
        CoherenceType.SEMANTIC_DEPTH: 0.8,
        CoherenceType.SOCIAL: 1.0,
    }

    weighted_sum = sum(scores_by_type[ct] * type_weights[ct]
                      for ct in scores_by_type)
    total_weight = sum(type_weights.values())
    weighted_mean = weighted_sum / total_weight

    if weighted_mean < 0.65:  # Threshold
        defenses["weighted_aggregation"] = True

    # ========================================================================
    # Vector 4: Contradiction Detection Defense
    # ========================================================================

    # Defense: Flag when types significantly disagree
    max_score = max(scores_by_type.values())
    min_score = min(scores_by_type.values())
    score_range = max_score - min_score

    if score_range > 0.40:
        defenses["contradiction_detection"] = True

    # ========================================================================
    # Vector 5: Outlier Exclusion Defense
    # ========================================================================

    # Defense: Exclude extreme outliers before aggregation
    import statistics

    scores_list = list(scores_by_type.values())
    mean = statistics.mean(scores_list)
    stdev = statistics.stdev(scores_list)

    outliers = [s for s in scores_list if abs(s - mean) > 2 * stdev]
    if outliers:
        defenses["outlier_exclusion"] = True

    # ========================================================================
    # Vector 6: Type Independence Verification
    # ========================================================================

    # Defense: Verify types are truly independent (not gamed together)
    def verify_independence(scores: Dict[CoherenceType, float]) -> bool:
        """Check for suspicious patterns across types."""
        # Gaming both SELF_REFERENCE and SEMANTIC_DEPTH is common
        if (scores[CoherenceType.SELF_REFERENCE] > 0.85 and
            scores[CoherenceType.SEMANTIC_DEPTH] > 0.85 and
            scores[CoherenceType.BEHAVIORAL] < 0.50):
            return False  # Suspicious pattern
        return True

    if not verify_independence(scores_by_type):
        defenses["type_independence"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Coherence Type Confusion (FD-2a)",
        success=attack_success,
        setup_cost_atp=2000.0,
        gain_atp=60000.0 if attack_success else 0.0,
        roi=(60000.0 / 2000.0) if attack_success else -1.0,
        detection_probability=0.55 if defenses_held >= 4 else 0.25,
        time_to_detection_hours=72.0,
        blocks_until_detected=500,
        trust_damage=0.45,
        description=f"""
COHERENCE TYPE CONFUSION ATTACK (Track FD-2a)

Exploit differences in how coherence types interpret behavior.

Attack Pattern:
1. Craft content that games easy-to-game types (self-ref, semantic)
2. Ignore hard-to-game types (behavioral, temporal)
3. Rely on simple aggregation to pass threshold

Score Analysis by Type:
- SELF_REFERENCE: {scores_by_type[CoherenceType.SELF_REFERENCE]:.2f} (HIGH - gamed)
- SEMANTIC_DEPTH: {scores_by_type[CoherenceType.SEMANTIC_DEPTH]:.2f} (HIGH - gamed)
- BEHAVIORAL: {scores_by_type[CoherenceType.BEHAVIORAL]:.2f} (LOW - ignored)
- TEMPORAL: {scores_by_type[CoherenceType.TEMPORAL]:.2f} (LOW - ignored)
- SOCIAL: {scores_by_type[CoherenceType.SOCIAL]:.2f} (MEDIUM)
- PHYSICS: {scores_by_type[CoherenceType.PHYSICS]:.2f} (MEDIUM)

Aggregation:
- Simple mean: {simple_mean:.3f}
- Weighted mean: {weighted_mean:.3f}
- Score range: {score_range:.2f}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FD-2a: Coherence Type Confusion Defense:
1. Require correlation between related types
2. Minimum score per type (can't skip any)
3. Weight hard-to-game types higher
4. Detect contradictions (high variance)
5. Exclude statistical outliers
6. Verify type independence

Different metrics should tell same story.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "scores_by_type": {str(k): v for k, v in scores_by_type.items()},
            "simple_mean": simple_mean,
            "weighted_mean": weighted_mean,
        }
    )


# ============================================================================
# ATTACK FD-2b: CONSENSUS SPLIT-BRAIN
# ============================================================================


def attack_consensus_split_brain() -> AttackResult:
    """
    ATTACK FD-2b: Consensus Split-Brain

    Create conditions where different parts of the network reach different
    consensus about the same entity's coherence.

    Vectors:
    1. Network partition exploitation
    2. Selective oracle visibility
    3. Concurrent conflicting updates
    4. Partition healing races
    5. Conflicting consensus caching
    """

    defenses = {
        "quorum_overlap": False,
        "consensus_versioning": False,
        "partition_detection": False,
        "healing_protocol": False,
        "global_ordering": False,
        "conflict_resolution": False,
    }

    # Setup: Two partitions (A and B) with some overlap
    partition_a_oracles = {"oracle_1", "oracle_2", "oracle_3", "oracle_5"}
    partition_b_oracles = {"oracle_3", "oracle_4", "oracle_5", "oracle_6"}
    overlap = partition_a_oracles & partition_b_oracles

    # ========================================================================
    # Vector 1: Quorum Overlap Defense
    # ========================================================================

    # Defense: Require overlap >= (N - quorum + 1) for safety
    TOTAL_ORACLES = 6
    QUORUM = 4
    MIN_OVERLAP = TOTAL_ORACLES - QUORUM + 1  # = 3

    if len(overlap) >= MIN_OVERLAP:
        defenses["quorum_overlap"] = True

    # ========================================================================
    # Vector 2: Consensus Versioning Defense
    # ========================================================================

    @dataclass
    class VersionedConsensus:
        entity_id: str
        score: float
        version: int
        participating_oracles: Set[str]
        timestamp: float

    # Attack: Two partitions produce different versions
    consensus_a = VersionedConsensus(
        entity_id="target",
        score=0.85,  # High score in partition A
        version=1,
        participating_oracles=partition_a_oracles,
        timestamp=time.time()
    )

    consensus_b = VersionedConsensus(
        entity_id="target",
        score=0.45,  # Low score in partition B
        version=1,  # Same version (conflict!)
        participating_oracles=partition_b_oracles,
        timestamp=time.time() + 0.1
    )

    # Defense: Detect version conflicts
    def detect_version_conflict(c1: VersionedConsensus, c2: VersionedConsensus) -> bool:
        return (c1.entity_id == c2.entity_id and
                c1.version == c2.version and
                abs(c1.score - c2.score) > 0.10)

    if detect_version_conflict(consensus_a, consensus_b):
        defenses["consensus_versioning"] = True

    # ========================================================================
    # Vector 3: Partition Detection Defense
    # ========================================================================

    # Defense: Detect when network is partitioned
    def detect_partition(oracle_views: Dict[str, Set[str]]) -> bool:
        """Detect if oracles have inconsistent views of each other."""
        all_oracles = set(oracle_views.keys())
        for oracle_id, visible_oracles in oracle_views.items():
            if visible_oracles != all_oracles:
                return True
        return False

    # Simulated oracle views during partition
    oracle_views = {
        "oracle_1": {"oracle_1", "oracle_2", "oracle_3", "oracle_5"},
        "oracle_2": {"oracle_1", "oracle_2", "oracle_3", "oracle_5"},
        "oracle_3": {"oracle_1", "oracle_2", "oracle_3", "oracle_4", "oracle_5", "oracle_6"},
        "oracle_4": {"oracle_3", "oracle_4", "oracle_5", "oracle_6"},
        "oracle_5": {"oracle_1", "oracle_2", "oracle_3", "oracle_4", "oracle_5", "oracle_6"},
        "oracle_6": {"oracle_3", "oracle_4", "oracle_5", "oracle_6"},
    }

    if detect_partition(oracle_views):
        defenses["partition_detection"] = True

    # ========================================================================
    # Vector 4: Healing Protocol Defense
    # ========================================================================

    # Defense: When partition heals, reconcile conflicts
    def healing_protocol(conflicting: List[VersionedConsensus]) -> VersionedConsensus:
        """Resolve conflicting consensus after partition heals."""
        if not conflicting:
            return None

        # Strategy 1: Take consensus with more participating oracles
        by_participants = sorted(conflicting,
                                key=lambda c: len(c.participating_oracles),
                                reverse=True)

        # Strategy 2: If tied, take more recent
        if len(by_participants[0].participating_oracles) == len(by_participants[-1].participating_oracles):
            by_time = sorted(conflicting, key=lambda c: c.timestamp, reverse=True)
            return by_time[0]

        return by_participants[0]

    resolved = healing_protocol([consensus_a, consensus_b])
    if resolved and resolved.score != max(consensus_a.score, consensus_b.score):
        # Healing didn't just take highest score
        defenses["healing_protocol"] = True

    # ========================================================================
    # Vector 5: Global Ordering Defense
    # ========================================================================

    # Defense: Use global ordering (via anchor chain) to sequence consensus
    def establish_global_order(consensuses: List[VersionedConsensus],
                               anchor_timestamps: Dict[str, float]) -> List[VersionedConsensus]:
        """Order consensus results by anchor chain position."""
        return sorted(consensuses,
                     key=lambda c: anchor_timestamps.get(c.entity_id, c.timestamp))

    # Simulated anchor timestamps
    anchor_timestamps = {
        "target": time.time() - 100,  # Anchored before both consensuses
    }

    ordered = establish_global_order([consensus_a, consensus_b], anchor_timestamps)
    if len(ordered) == 2 and ordered[0].timestamp < ordered[1].timestamp:
        defenses["global_ordering"] = True

    # ========================================================================
    # Vector 6: Conflict Resolution Defense
    # ========================================================================

    # Defense: Explicit conflict resolution mechanism
    class ConflictResolution:
        def __init__(self):
            self.conflicts: List[Tuple[VersionedConsensus, VersionedConsensus]] = []

        def register_conflict(self, c1: VersionedConsensus, c2: VersionedConsensus):
            self.conflicts.append((c1, c2))

        def resolve(self, c1: VersionedConsensus, c2: VersionedConsensus) -> VersionedConsensus:
            """Resolve by oracle overlap priority."""
            # Consensus with more overlap oracles wins
            overlap_1 = c1.participating_oracles & overlap
            overlap_2 = c2.participating_oracles & overlap

            if len(overlap_1) > len(overlap_2):
                return c1
            elif len(overlap_2) > len(overlap_1):
                return c2
            else:
                # Tie: take lower score (more conservative)
                return c1 if c1.score < c2.score else c2

    resolver = ConflictResolution()
    resolver.register_conflict(consensus_a, consensus_b)
    resolved = resolver.resolve(consensus_a, consensus_b)

    # Defense holds if resolution is conservative (lower score)
    if resolved.score == min(consensus_a.score, consensus_b.score):
        defenses["conflict_resolution"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Consensus Split-Brain (FD-2b)",
        success=attack_success,
        setup_cost_atp=15000.0,
        gain_atp=200000.0 if attack_success else 0.0,
        roi=(200000.0 / 15000.0) if attack_success else -1.0,
        detection_probability=0.75 if defenses_held >= 4 else 0.40,
        time_to_detection_hours=12.0,
        blocks_until_detected=80,
        trust_damage=0.70,
        description=f"""
CONSENSUS SPLIT-BRAIN ATTACK (Track FD-2b)

Create conditions where network reaches different consensus.

Attack Pattern:
1. Partition network into groups A and B
2. Present high coherence to partition A
3. Present low coherence to partition B
4. Exploit race conditions when partitions heal

Partition Analysis:
- Partition A: {partition_a_oracles}
- Partition B: {partition_b_oracles}
- Overlap: {overlap}
- Required overlap: {MIN_OVERLAP}

Conflicting Consensus:
- Partition A score: {consensus_a.score:.2f}
- Partition B score: {consensus_b.score:.2f}
- Score difference: {abs(consensus_a.score - consensus_b.score):.2f}

Defense Analysis:
- Quorum overlap: {"HELD" if defenses["quorum_overlap"] else "BYPASSED"}
- Consensus versioning: {"HELD" if defenses["consensus_versioning"] else "BYPASSED"}
- Partition detection: {"HELD" if defenses["partition_detection"] else "BYPASSED"}
- Healing protocol: {"HELD" if defenses["healing_protocol"] else "BYPASSED"}
- Global ordering: {"HELD" if defenses["global_ordering"] else "BYPASSED"}
- Conflict resolution: {"HELD" if defenses["conflict_resolution"] else "BYPASSED"}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FD-2b: Consensus Split-Brain Defense:
1. Require sufficient quorum overlap
2. Version consensus and detect conflicts
3. Active partition detection
4. Conservative healing protocol
5. Global ordering via anchor chain
6. Explicit conflict resolution (conservative)

Split-brain is not just a database problem.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "partition_a": list(partition_a_oracles),
            "partition_b": list(partition_b_oracles),
            "overlap": list(overlap),
            "consensus_a_score": consensus_a.score,
            "consensus_b_score": consensus_b.score,
        }
    )


# ============================================================================
# ATTACK FD-3a: COHERENCE METRIC ARBITRAGE
# ============================================================================


def attack_coherence_metric_arbitrage() -> AttackResult:
    """
    ATTACK FD-3a: Coherence Metric Arbitrage

    Exploit differences in metric calibration across federated networks
    to arbitrage coherence scores.

    Vectors:
    1. Cross-federation calibration gaps
    2. Metric version mismatches
    3. Context-dependent scoring differences
    4. Migration between federations
    5. Score portability exploitation
    """

    defenses = {
        "calibration_standardization": False,
        "version_compatibility": False,
        "context_normalization": False,
        "migration_verification": False,
        "score_discount": False,
        "cross_fed_attestation": False,
    }

    # Setup: Two federations with different calibrations
    @dataclass
    class Federation:
        fed_id: str
        score_multiplier: float  # Calibration factor
        context_bonus: Dict[str, float]  # Context-specific bonuses
        version: str

    fed_alpha = Federation(
        fed_id="alpha",
        score_multiplier=1.0,  # Strict calibration
        context_bonus={"research": 0.0, "commerce": 0.05},
        version="2.0"
    )

    fed_beta = Federation(
        fed_id="beta",
        score_multiplier=1.15,  # Lenient calibration (15% higher)
        context_bonus={"research": 0.10, "commerce": 0.0},
        version="1.8"  # Older version
    )

    # Attack: Get high score in lenient federation, migrate to strict one
    raw_coherence = 0.65  # Mediocre raw score

    # Score in beta (lenient)
    beta_score = raw_coherence * fed_beta.score_multiplier + fed_beta.context_bonus["research"]
    # = 0.65 * 1.15 + 0.10 = 0.8475

    # Try to use this score in alpha
    ported_score = beta_score

    # ========================================================================
    # Vector 1: Calibration Standardization Defense
    # ========================================================================

    # Defense: Require normalized scores across federations
    STANDARD_MULTIPLIER = 1.0
    TOLERANCE = 0.05

    def is_calibration_standard(fed: Federation) -> bool:
        return abs(fed.score_multiplier - STANDARD_MULTIPLIER) <= TOLERANCE

    if not is_calibration_standard(fed_beta):
        defenses["calibration_standardization"] = True

    # ========================================================================
    # Vector 2: Version Compatibility Defense
    # ========================================================================

    # Defense: Require compatible metric versions
    def versions_compatible(v1: str, v2: str) -> bool:
        major1 = int(v1.split('.')[0])
        major2 = int(v2.split('.')[0])
        return major1 == major2

    if not versions_compatible(fed_alpha.version, fed_beta.version):
        defenses["version_compatibility"] = True

    # ========================================================================
    # Vector 3: Context Normalization Defense
    # ========================================================================

    # Defense: Normalize for context differences
    def normalize_for_context(score: float, source_fed: Federation,
                              target_fed: Federation, context: str) -> float:
        """Normalize score when porting across federations."""
        # Remove source context bonus
        normalized = score - source_fed.context_bonus.get(context, 0)
        # Remove source calibration
        normalized = normalized / source_fed.score_multiplier
        # Apply target calibration
        normalized = normalized * target_fed.score_multiplier
        # Add target context bonus
        normalized = normalized + target_fed.context_bonus.get(context, 0)
        return normalized

    normalized_score = normalize_for_context(beta_score, fed_beta, fed_alpha, "research")
    # = (0.8475 - 0.10) / 1.15 * 1.0 + 0.0 = 0.65

    if abs(normalized_score - raw_coherence) < 0.05:
        defenses["context_normalization"] = True

    # ========================================================================
    # Vector 4: Migration Verification Defense
    # ========================================================================

    # Defense: Re-verify coherence when entity migrates
    def verify_on_migration(entity_id: str, claimed_score: float,
                            source_fed: str, target_fed: str) -> Tuple[bool, float]:
        """Re-verify coherence during migration."""
        # Simulate re-verification in target federation
        reverified_score = raw_coherence  # Would actually re-measure

        discrepancy = abs(claimed_score - reverified_score)
        if discrepancy > 0.15:
            return False, reverified_score
        return True, claimed_score

    verified, final_score = verify_on_migration("attacker", ported_score, "beta", "alpha")
    if not verified:
        defenses["migration_verification"] = True

    # ========================================================================
    # Vector 5: Score Discount Defense
    # ========================================================================

    # Defense: Apply discount to ported scores
    PORTED_SCORE_DISCOUNT = 0.20  # 20% discount on ported scores

    discounted_score = ported_score * (1 - PORTED_SCORE_DISCOUNT)

    if discounted_score < 0.70:  # Below threshold after discount
        defenses["score_discount"] = True

    # ========================================================================
    # Vector 6: Cross-Federation Attestation Defense
    # ========================================================================

    # Defense: Require attestation from source federation
    @dataclass
    class CrossFedAttestation:
        entity_id: str
        score: float
        source_federation: str
        attestation_signature: str
        measurement_details: Dict

    def verify_attestation(attestation: CrossFedAttestation,
                           trusted_feds: Set[str]) -> bool:
        """Verify cross-federation attestation."""
        # Check source is trusted
        if attestation.source_federation not in trusted_feds:
            return False
        # Check signature (simulated)
        if not attestation.attestation_signature:
            return False
        # Check measurement details present
        if not attestation.measurement_details:
            return False
        return True

    attack_attestation = CrossFedAttestation(
        entity_id="attacker",
        score=beta_score,
        source_federation="beta",
        attestation_signature="sig_beta_abc",
        measurement_details={"raw": raw_coherence, "multiplier": 1.15}
    )

    # Alpha only trusts itself and calibrated federations
    trusted_by_alpha = {"alpha"}  # Beta not trusted due to calibration

    if not verify_attestation(attack_attestation, trusted_by_alpha):
        defenses["cross_fed_attestation"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    return AttackResult(
        attack_name="Coherence Metric Arbitrage (FD-3a)",
        success=attack_success,
        setup_cost_atp=8000.0,
        gain_atp=120000.0 if attack_success else 0.0,
        roi=(120000.0 / 8000.0) if attack_success else -1.0,
        detection_probability=0.60 if defenses_held >= 4 else 0.30,
        time_to_detection_hours=96.0,
        blocks_until_detected=700,
        trust_damage=0.55,
        description=f"""
COHERENCE METRIC ARBITRAGE ATTACK (Track FD-3a)

Exploit calibration differences between federations.

Attack Pattern:
1. Identify lenient federation (higher calibration multiplier)
2. Build score in lenient federation
3. Migrate score to strict federation
4. Profit from score difference

Score Analysis:
- Raw coherence: {raw_coherence:.2f}
- Beta (lenient) score: {beta_score:.3f}
- Normalized score: {normalized_score:.3f}
- Discounted score: {discounted_score:.3f}
- Arbitrage profit: {beta_score - raw_coherence:.3f}

Federation Comparison:
- Alpha: multiplier={fed_alpha.score_multiplier}, version={fed_alpha.version}
- Beta: multiplier={fed_beta.score_multiplier}, version={fed_beta.version}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FD-3a: Coherence Metric Arbitrage Defense:
1. Standardize calibration across federations
2. Require version compatibility
3. Normalize for context differences
4. Re-verify on migration
5. Apply discount to ported scores
6. Require attestation from trusted sources

Arbitrage reveals calibration gaps.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "raw_coherence": raw_coherence,
            "beta_score": beta_score,
            "normalized_score": normalized_score,
            "discounted_score": discounted_score,
        }
    )


# ============================================================================
# ATTACK FD-3b: CONSENSUS ROLLBACK
# ============================================================================


def attack_consensus_rollback() -> AttackResult:
    """
    ATTACK FD-3b: Consensus Rollback Attack

    Exploit conditions where consensus can be rolled back, causing
    coherence decisions to be undone.

    Vectors:
    1. Block reorganization exploitation
    2. Finality delay attack
    3. Checkpoint manipulation
    4. State root conflicts
    5. Orphan consensus injection
    """

    defenses = {
        "finality_threshold": False,
        "checkpoint_anchoring": False,
        "state_root_verification": False,
        "orphan_detection": False,
        "rollback_limits": False,
        "economic_finality": False,
    }

    # Setup: Consensus with finality
    @dataclass
    class ConsensusBlock:
        block_number: int
        entity_scores: Dict[str, float]
        parent_hash: str
        timestamp: float
        confirmations: int = 0
        finalized: bool = False

    # Current chain of consensus blocks
    chain: List[ConsensusBlock] = []

    for i in range(10):
        block = ConsensusBlock(
            block_number=i,
            entity_scores={"target": 0.70 + i * 0.01},
            parent_hash=f"hash_{i-1}" if i > 0 else "genesis",
            timestamp=time.time() - (10 - i) * 60,
            confirmations=10 - i,
            finalized=i < 7  # First 7 blocks finalized
        )
        chain.append(block)

    # Attack: Reorganize to replace block 8 with lower score
    attack_block = ConsensusBlock(
        block_number=8,
        entity_scores={"target": 0.55},  # Much lower score
        parent_hash="hash_7",
        timestamp=time.time() - 120,
        confirmations=5,
        finalized=False
    )

    # ========================================================================
    # Vector 1: Finality Threshold Defense
    # ========================================================================

    FINALITY_CONFIRMATIONS = 6

    # Defense: Only finalized blocks are authoritative
    def is_finalized(block: ConsensusBlock) -> bool:
        return block.confirmations >= FINALITY_CONFIRMATIONS or block.finalized

    if not is_finalized(attack_block):
        defenses["finality_threshold"] = True

    # ========================================================================
    # Vector 2: Checkpoint Anchoring Defense
    # ========================================================================

    # Defense: Periodic checkpoints prevent deep rollbacks
    @dataclass
    class Checkpoint:
        block_number: int
        state_root: str
        anchor_signature: str

    checkpoints = [
        Checkpoint(0, "root_0", "sig_0"),
        Checkpoint(5, "root_5", "sig_5"),
    ]

    # Attack tries to reorganize past checkpoint
    most_recent_checkpoint = max(checkpoints, key=lambda c: c.block_number)

    if attack_block.block_number > most_recent_checkpoint.block_number:
        # Can't rollback past checkpoint
        defenses["checkpoint_anchoring"] = True

    # ========================================================================
    # Vector 3: State Root Verification Defense
    # ========================================================================

    # Defense: Verify state root matches claimed scores
    def compute_state_root(scores: Dict[str, float]) -> str:
        """Compute merkle root of score state."""
        data = str(sorted(scores.items()))
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    claimed_root = compute_state_root(attack_block.entity_scores)
    expected_root = compute_state_root(chain[8].entity_scores)

    if claimed_root != expected_root:
        defenses["state_root_verification"] = True

    # ========================================================================
    # Vector 4: Orphan Detection Defense
    # ========================================================================

    # Defense: Detect when block becomes orphaned
    def is_orphan(block: ConsensusBlock, current_chain: List[ConsensusBlock]) -> bool:
        """Check if block is orphaned (not in main chain)."""
        for chain_block in current_chain:
            if chain_block.block_number == block.block_number:
                if chain_block.parent_hash == block.parent_hash:
                    return False  # Same block
        return True

    # After reorg attempt, check if attack block is orphan
    if is_orphan(attack_block, chain):
        defenses["orphan_detection"] = True

    # ========================================================================
    # Vector 5: Rollback Limits Defense
    # ========================================================================

    # Defense: Maximum allowed rollback depth
    MAX_ROLLBACK_DEPTH = 3

    current_height = len(chain) - 1
    attack_depth = current_height - attack_block.block_number + 1

    if attack_depth > MAX_ROLLBACK_DEPTH:
        defenses["rollback_limits"] = True

    # ========================================================================
    # Vector 6: Economic Finality Defense
    # ========================================================================

    # Defense: Require economic stake to challenge consensus
    CHALLENGE_STAKE_ATP = 100000.0
    ATTACK_BUDGET_ATP = 50000.0

    if ATTACK_BUDGET_ATP < CHALLENGE_STAKE_ATP:
        defenses["economic_finality"] = True

    # ========================================================================
    # Results
    # ========================================================================

    defenses_held = sum(defenses.values())
    total_defenses = len(defenses)
    attack_success = defenses_held < 4

    original_score = chain[8].entity_scores["target"]
    attack_score = attack_block.entity_scores["target"]

    return AttackResult(
        attack_name="Consensus Rollback (FD-3b)",
        success=attack_success,
        setup_cost_atp=ATTACK_BUDGET_ATP,
        gain_atp=150000.0 if attack_success else 0.0,
        roi=(150000.0 / ATTACK_BUDGET_ATP) if attack_success else -1.0,
        detection_probability=0.80 if defenses_held >= 4 else 0.45,
        time_to_detection_hours=6.0,
        blocks_until_detected=30,
        trust_damage=0.75,
        description=f"""
CONSENSUS ROLLBACK ATTACK (Track FD-3b)

Roll back consensus to undo coherence decisions.

Attack Pattern:
1. Wait for favorable consensus
2. Create competing chain with different scores
3. Attempt block reorganization
4. If successful, coherence is undone

Chain Analysis:
- Current height: {current_height}
- Attack target block: {attack_block.block_number}
- Rollback depth: {attack_depth}
- Max allowed: {MAX_ROLLBACK_DEPTH}

Score Impact:
- Original score: {original_score:.2f}
- Attack score: {attack_score:.2f}
- Score delta: {attack_score - original_score:.2f}

Finality:
- Attack block confirmations: {attack_block.confirmations}
- Required for finality: {FINALITY_CONFIRMATIONS}

Defenses activated: {defenses_held}/{total_defenses}
""".strip(),
        mitigation="""
Track FD-3b: Consensus Rollback Defense:
1. Finality threshold (6+ confirmations)
2. Periodic checkpoints prevent deep rollback
3. State root verification
4. Orphan block detection
5. Maximum rollback depth limits
6. Economic stake for challenges

Finality is not optional.
""".strip(),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "current_height": current_height,
            "attack_depth": attack_depth,
            "original_score": original_score,
            "attack_score": attack_score,
        }
    )


# ============================================================================
# RUN ALL ATTACKS
# ============================================================================


def run_all_track_fd_attacks() -> List[AttackResult]:
    """Run all Track FD attacks and return results."""
    attacks = [
        attack_oracle_majority_capture,
        attack_oracle_timing_desync,
        attack_coherence_type_confusion,
        attack_consensus_split_brain,
        attack_coherence_metric_arbitrage,
        attack_consensus_rollback,
    ]

    results = []
    for attack_fn in attacks:
        try:
            result = attack_fn()
            results.append(result)
        except Exception as e:
            print(f"Error running {attack_fn.__name__}: {e}")

    return results


def print_track_fd_summary(results: List[AttackResult]):
    """Print summary of Track FD attack results."""
    print("\n" + "=" * 70)
    print("TRACK FD: MULTI-COHERENCE CONSENSUS ATTACKS - SUMMARY")
    print("=" * 70)

    total_attacks = len(results)
    successful = sum(1 for r in results if r.success)
    defended = total_attacks - successful

    print(f"\nTotal Attacks: {total_attacks}")
    print(f"Defended: {defended}")
    print(f"Success Rate: {(1 - defended/total_attacks)*100:.1f}%")

    avg_detection = sum(r.detection_probability for r in results) / total_attacks
    print(f"Average Detection Probability: {avg_detection*100:.1f}%")

    print("\n" + "-" * 70)
    print("INDIVIDUAL RESULTS:")
    print("-" * 70)

    for result in results:
        status = "❌ DEFENDED" if not result.success else "⚠️  SUCCEEDED"
        print(f"\n{result.attack_name}")
        print(f"  Status: {status}")
        print(f"  Detection: {result.detection_probability*100:.0f}%")
        print(f"  Setup Cost: {result.setup_cost_atp:,.0f} ATP")
        print(f"  Potential Gain: {result.gain_atp:,.0f} ATP")
        print(f"  Trust Damage: {result.trust_damage:.0%}")


if __name__ == "__main__":
    results = run_all_track_fd_attacks()
    print_track_fd_summary(results)

    # Print detailed results
    print("\n\n" + "=" * 70)
    print("DETAILED ATTACK DESCRIPTIONS")
    print("=" * 70)

    for result in results:
        print(f"\n{'='*70}")
        print(result.description)
        print(f"\n--- MITIGATION ---")
        print(result.mitigation)
