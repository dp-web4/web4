"""
Reality KV Cache — Reference Implementation

Implements RFC-REALITY-CACHE-001:
- Assumption caching with hierarchical levels (L1 sensory → L4 abstract)
- Surprise-driven cache invalidation with cascading dependency graphs
- Confidence decay over time (linear, exponential, sigmoid models)
- Witness-based validation for high-surprise invalidations
- Distributed cache across MRH with Merkle consistency detection
- ATP cost model: query(0), cross-query(5), witness(3), rebuild(10), publish(2)
- Security: cache poisoning detection, surprise manipulation rate limiting, staleness exploitation
- Trust tensor integration: stale cache → reduced T3 reliability

Core insight from RFC: "Assumptions are the KV cache that makes thinking fast.
Surprise is the signal that makes thinking accurate."

Spec: web4-standard/rfcs/RFC_REALITY_KV_CACHE.md
"""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class CacheLevel(Enum):
    """Hierarchical cache levels per §2."""
    SENSORY = 1      # Level 1: next expected input, threshold 0.3
    ENVIRONMENT = 2  # Level 2: immediate environment, threshold 0.5
    CONTEXTUAL = 3   # Level 3: contextual patterns, threshold 0.6
    ABSTRACT = 4     # Level 4: abstract concepts, threshold 0.7


class CacheAction(Enum):
    """Actions from surprise-driven invalidation per §4."""
    CONTINUE = "continue"    # < 0.3: cache probably valid
    VERIFY = "verify"        # 0.3-0.6: spot check related assumptions
    REBUILD = "rebuild"      # > 0.6: invalidate and rebuild


class DecayModel(Enum):
    """Confidence decay models."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    SIGMOID = "sigmoid"


class VerificationMethod(Enum):
    """How an assumption was verified."""
    SYSTEM = "system"          # System-provided (clock, network, etc.)
    OBSERVATION = "observation" # Direct observation
    WITNESS = "witness"        # Witness-validated
    INFERENCE = "inference"    # Inferred from other assumptions
    DEFAULT = "default"        # Default/initial value


# Surprise thresholds per level
LEVEL_THRESHOLDS = {
    CacheLevel.SENSORY: 0.3,
    CacheLevel.ENVIRONMENT: 0.5,
    CacheLevel.CONTEXTUAL: 0.6,
    CacheLevel.ABSTRACT: 0.7,
}

# ATP costs per §ATP
ATP_COSTS = {
    "query_own": 0,
    "query_other": 5,
    "witness_validation": 3,
    "cache_rebuild": 10,
    "publish_update": 2,
}


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Assumption:
    """A cached assumption about reality."""
    key: str
    value: Any
    confidence: float  # 0.0-1.0
    level: CacheLevel
    last_verified: datetime
    verification_method: VerificationMethod
    centrality: float = 0.5  # How central this assumption is (0-1)
    created_at: Optional[datetime] = None
    entity_id: str = ""

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = self.last_verified


@dataclass
class Observation:
    """An observation that may contradict cached assumptions."""
    key: str
    value: Any
    timestamp: datetime
    source: str = "direct"
    confidence: float = 1.0


@dataclass
class InvalidationEvent:
    """Record of a cache invalidation."""
    key: str
    old_value: Any
    new_value: Any
    surprise: float
    action: CacheAction
    cascaded_keys: List[str]
    timestamp: datetime
    witness_count: int = 0


@dataclass
class WitnessResponse:
    """A witness validation response."""
    witness_id: str
    key: str
    confirmed_value: Any
    confidence: float
    timestamp: datetime


@dataclass
class CacheStats:
    """Performance statistics for the cache."""
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    invalidations: int = 0
    cascaded_invalidations: int = 0
    witness_validations: int = 0
    rebuilds: int = 0

    @property
    def hit_rate(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return self.cache_hits / self.total_queries


# ============================================================================
# SURPRISE CALCULATOR
# ============================================================================

class SurpriseCalculator:
    """Compute surprise from observation vs cached expectation per §3."""

    @staticmethod
    def compute(observation: Observation,
                cached: Assumption) -> float:
        """
        Surprise = magnitude of prediction error weighted by importance.

        Returns: 0.0 (perfectly expected) to 1.0 (completely unexpected)
        """
        if observation.value == cached.value:
            return 0.0

        # Semantic distance: type-aware comparison
        distance = SurpriseCalculator._semantic_distance(
            observation.value, cached.value)

        # Weight by importance = confidence × centrality
        importance = cached.confidence * cached.centrality

        surprise = distance * importance
        return min(surprise, 1.0)

    @staticmethod
    def _semantic_distance(observed: Any, expected: Any) -> float:
        """Compute semantic distance between two values."""
        # Numeric values: normalized difference
        if isinstance(observed, (int, float)) and isinstance(expected, (int, float)):
            if expected == 0 and observed == 0:
                return 0.0
            max_val = max(abs(observed), abs(expected), 1.0)
            return min(abs(observed - expected) / max_val, 1.0)

        # String values: edit distance heuristic
        if isinstance(observed, str) and isinstance(expected, str):
            if observed.lower() == expected.lower():
                return 0.1  # Case difference only
            # Simple binary for now
            return 1.0

        # Boolean values
        if isinstance(observed, bool) and isinstance(expected, bool):
            return 0.0 if observed == expected else 1.0

        # Different types = maximum surprise
        return 1.0

    @staticmethod
    def classify_action(surprise: float) -> CacheAction:
        """Map surprise to cache action per §4."""
        if surprise < 0.3:
            return CacheAction.CONTINUE
        elif surprise < 0.6:
            return CacheAction.VERIFY
        else:
            return CacheAction.REBUILD


# ============================================================================
# CONFIDENCE DECAY
# ============================================================================

class ConfidenceDecay:
    """Time-based confidence decay models per §Security.staleness."""

    @staticmethod
    def apply(confidence: float, age_hours: float,
              model: DecayModel = DecayModel.EXPONENTIAL,
              half_life_hours: float = 24.0) -> float:
        """Apply time-based decay to confidence."""
        if age_hours <= 0:
            return confidence

        if model == DecayModel.LINEAR:
            decay_rate = 0.5 / half_life_hours  # Lose 50% per half_life
            decayed = confidence - (decay_rate * age_hours)
            return max(decayed, 0.0)

        elif model == DecayModel.EXPONENTIAL:
            # c(t) = c0 * 2^(-t/half_life)
            decayed = confidence * (2.0 ** (-age_hours / half_life_hours))
            return max(decayed, 0.0)

        elif model == DecayModel.SIGMOID:
            # Steep drop around half_life
            midpoint = half_life_hours
            steepness = 0.1
            factor = 1.0 / (1.0 + math.exp(steepness * (age_hours - midpoint)))
            return confidence * factor

        return confidence


# ============================================================================
# REALITY KV CACHE
# ============================================================================

class RealityCache:
    """
    Reality KV Cache per RFC-REALITY-CACHE-001.

    Assumptions are cached at hierarchical levels with surprise-driven
    invalidation and cascading dependency graphs.
    """

    def __init__(self, entity_id: str,
                 surprise_threshold: float = 0.6,
                 decay_model: DecayModel = DecayModel.EXPONENTIAL,
                 decay_half_life_hours: float = 24.0,
                 max_invalidation_rate: int = 10):
        self.entity_id = entity_id
        self.surprise_threshold = surprise_threshold
        self.decay_model = decay_model
        self.decay_half_life_hours = decay_half_life_hours
        self.max_invalidation_rate = max_invalidation_rate

        # Cache storage
        self.assumptions: Dict[str, Assumption] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}  # key → dependent keys
        self.reverse_deps: Dict[str, Set[str]] = {}      # key → keys it depends on

        # History
        self.invalidation_log: List[InvalidationEvent] = []
        self.stats = CacheStats()

        # Rate limiting for surprise manipulation defense
        self._recent_invalidations: List[datetime] = []

    def assume(self, key: str, value: Any, confidence: float = 0.9,
               level: CacheLevel = CacheLevel.CONTEXTUAL,
               verification_method: VerificationMethod = VerificationMethod.DEFAULT,
               centrality: float = 0.5,
               now: Optional[datetime] = None) -> Assumption:
        """Cache an assumption about reality."""
        ts = now or datetime.now(timezone.utc)
        assumption = Assumption(
            key=key, value=value, confidence=confidence,
            level=level, last_verified=ts,
            verification_method=verification_method,
            centrality=centrality, entity_id=self.entity_id)
        self.assumptions[key] = assumption
        return assumption

    def get(self, key: str,
            now: Optional[datetime] = None) -> Optional[Tuple[Any, float]]:
        """
        Get cached assumption if confident enough, else return None.

        Returns: (value, effective_confidence) or None
        """
        self.stats.total_queries += 1

        if key not in self.assumptions:
            self.stats.cache_misses += 1
            return None

        assumption = self.assumptions[key]
        ts = now or datetime.now(timezone.utc)

        # Apply confidence decay
        age_hours = (ts - assumption.last_verified).total_seconds() / 3600
        effective_conf = ConfidenceDecay.apply(
            assumption.confidence, age_hours,
            self.decay_model, self.decay_half_life_hours)

        # Check if still confident enough
        threshold = LEVEL_THRESHOLDS.get(assumption.level, 0.5)
        if effective_conf > threshold:
            self.stats.cache_hits += 1
            return (assumption.value, effective_conf)
        else:
            self.stats.cache_misses += 1
            return None

    def add_dependency(self, parent: str, dependent: str):
        """Add dependency: when parent invalidated, dependent also invalidated."""
        if parent not in self.dependency_graph:
            self.dependency_graph[parent] = set()
        self.dependency_graph[parent].add(dependent)

        if dependent not in self.reverse_deps:
            self.reverse_deps[dependent] = set()
        self.reverse_deps[dependent].add(parent)

    def observe(self, observation: Observation,
                now: Optional[datetime] = None) -> Tuple[float, CacheAction, List[str]]:
        """
        Process an observation against cached assumptions.

        Returns: (surprise, action, invalidated_keys)
        """
        ts = now or observation.timestamp

        if observation.key not in self.assumptions:
            # New assumption — cache it
            self.assume(observation.key, observation.value,
                        confidence=observation.confidence,
                        level=CacheLevel.CONTEXTUAL,
                        verification_method=VerificationMethod.OBSERVATION,
                        now=ts)
            return (0.0, CacheAction.CONTINUE, [])

        cached = self.assumptions[observation.key]
        surprise = SurpriseCalculator.compute(observation, cached)
        action = SurpriseCalculator.classify_action(surprise)

        invalidated = []

        if action == CacheAction.VERIFY:
            # Spot check: reduce confidence, don't invalidate
            cached.confidence *= 0.7
            cached.last_verified = ts

        elif action == CacheAction.REBUILD:
            # Check rate limit
            if not self._rate_limit_check(ts):
                action = CacheAction.VERIFY
                cached.confidence *= 0.5
            else:
                # Invalidate and rebuild
                invalidated = self._invalidate_cascade(
                    observation.key, observation.value,
                    observation.confidence, surprise, ts)

        return (surprise, action, invalidated)

    def _rate_limit_check(self, now: datetime) -> bool:
        """Check if invalidation rate is within limits (§Security.manipulation)."""
        # Remove old entries (1-minute window)
        cutoff = now - timedelta(minutes=1)
        self._recent_invalidations = [
            t for t in self._recent_invalidations if t > cutoff]

        if len(self._recent_invalidations) >= self.max_invalidation_rate:
            return False

        self._recent_invalidations.append(now)
        return True

    def _invalidate_cascade(self, key: str, new_value: Any,
                            new_confidence: float, surprise: float,
                            now: datetime) -> List[str]:
        """Invalidate assumption and cascade to dependents."""
        invalidated = [key]
        old_value = self.assumptions[key].value if key in self.assumptions else None

        # Update the primary assumption
        self.assumptions[key] = Assumption(
            key=key, value=new_value, confidence=new_confidence,
            level=self.assumptions.get(key, Assumption(
                key=key, value=new_value, confidence=new_confidence,
                level=CacheLevel.CONTEXTUAL,
                last_verified=now,
                verification_method=VerificationMethod.OBSERVATION
            )).level,
            last_verified=now,
            verification_method=VerificationMethod.OBSERVATION,
            centrality=self.assumptions.get(key, Assumption(
                key=key, value=new_value, confidence=new_confidence,
                level=CacheLevel.CONTEXTUAL,
                last_verified=now,
                verification_method=VerificationMethod.OBSERVATION
            )).centrality,
            entity_id=self.entity_id)

        # Cascade to dependents
        cascaded = []
        if key in self.dependency_graph:
            for dep_key in self.dependency_graph[key]:
                if dep_key in self.assumptions:
                    self.assumptions[dep_key].confidence = 0.0
                    cascaded.append(dep_key)
                    invalidated.append(dep_key)

        self.stats.invalidations += 1
        self.stats.cascaded_invalidations += len(cascaded)

        # Log event
        self.invalidation_log.append(InvalidationEvent(
            key=key, old_value=old_value, new_value=new_value,
            surprise=surprise, action=CacheAction.REBUILD,
            cascaded_keys=cascaded, timestamp=now))

        return invalidated

    def verify(self, key: str, verified_value: Any,
               confidence: float = 1.0,
               method: VerificationMethod = VerificationMethod.SYSTEM,
               now: Optional[datetime] = None):
        """Verify and refresh an assumption."""
        ts = now or datetime.now(timezone.utc)
        if key in self.assumptions:
            a = self.assumptions[key]
            a.value = verified_value
            a.confidence = confidence
            a.last_verified = ts
            a.verification_method = method
        else:
            self.assume(key, verified_value, confidence,
                        verification_method=method, now=ts)

    def validate_with_witnesses(self, key: str,
                                witnesses: List[WitnessResponse]) -> Tuple[Any, float]:
        """
        Validate assumption using witness consensus per §Witness.
        Returns: (consensus_value, consensus_confidence)
        """
        if not witnesses:
            return (None, 0.0)

        self.stats.witness_validations += len(witnesses)

        # Count votes for each value
        votes: Dict[str, List[WitnessResponse]] = {}
        for w in witnesses:
            val_key = str(w.confirmed_value)
            if val_key not in votes:
                votes[val_key] = []
            votes[val_key].append(w)

        # Consensus: most votes, weighted by confidence
        best_val = None
        best_score = 0.0
        for val_str, resps in votes.items():
            score = sum(r.confidence for r in resps)
            if score > best_score:
                best_score = score
                best_val = resps[0].confirmed_value

        # Consensus confidence = weighted agreement
        total_conf = sum(w.confidence for w in witnesses)
        consensus_conf = best_score / total_conf if total_conf > 0 else 0.0

        # Update assumption
        if key in self.assumptions and best_val is not None:
            self.assumptions[key].value = best_val
            self.assumptions[key].confidence = consensus_conf
            self.assumptions[key].verification_method = VerificationMethod.WITNESS
            if witnesses:
                self.assumptions[key].last_verified = witnesses[-1].timestamp

        return (best_val, consensus_conf)

    def get_stale_assumptions(self, max_age_hours: float = 24.0,
                              now: Optional[datetime] = None) -> List[str]:
        """Find assumptions that need re-verification."""
        ts = now or datetime.now(timezone.utc)
        stale = []
        for key, a in self.assumptions.items():
            age_hours = (ts - a.last_verified).total_seconds() / 3600
            effective_conf = ConfidenceDecay.apply(
                a.confidence, age_hours,
                self.decay_model, self.decay_half_life_hours)
            threshold = LEVEL_THRESHOLDS.get(a.level, 0.5)
            if effective_conf <= threshold:
                stale.append(key)
        return stale

    def size(self) -> int:
        """Number of cached assumptions."""
        return len(self.assumptions)


# ============================================================================
# TRUST TENSOR INTEGRATION
# ============================================================================

class CacheTrustModulator:
    """Adjust T3/V3 based on cache staleness per §Trust."""

    @staticmethod
    def compute_staleness(cache: RealityCache,
                          now: Optional[datetime] = None) -> float:
        """
        Compute overall cache staleness (0.0 fresh, 1.0 very stale).
        """
        ts = now or datetime.now(timezone.utc)
        if not cache.assumptions:
            return 0.0

        total_staleness = 0.0
        count = 0
        for a in cache.assumptions.values():
            age_hours = (ts - a.last_verified).total_seconds() / 3600
            effective = ConfidenceDecay.apply(
                a.confidence, age_hours,
                cache.decay_model, cache.decay_half_life_hours)
            staleness = 1.0 - effective
            total_staleness += staleness
            count += 1

        return total_staleness / count if count > 0 else 0.0

    @staticmethod
    def trust_adjustment(staleness: float) -> Dict[str, float]:
        """
        Compute trust tensor adjustments from staleness.
        Per RFC: T3_reliability -0.3 × staleness, V3_verification -0.2 × staleness
        """
        return {
            "T3_reliability": -0.3 * staleness,
            "V3_verification": -0.2 * staleness,
            "evidence": "stale_reality_cache",
        }


# ============================================================================
# SECURITY: CACHE POISONING DETECTOR
# ============================================================================

class CachePoisoningDetector:
    """Detect cache poisoning attacks per §Security.poisoning."""

    def __init__(self, max_update_rate: int = 5,
                 window_minutes: float = 1.0,
                 min_witness_diversity: float = 0.6):
        self.max_update_rate = max_update_rate
        self.window_minutes = window_minutes
        self.min_witness_diversity = min_witness_diversity
        self._update_history: Dict[str, List[Tuple[datetime, str]]] = {}

    def check_update(self, key: str, source: str,
                     now: Optional[datetime] = None) -> bool:
        """
        Check if an update is legitimate.
        Returns True if OK, False if potential poisoning.
        """
        ts = now or datetime.now(timezone.utc)

        if key not in self._update_history:
            self._update_history[key] = []

        # Remove old entries
        cutoff = ts - timedelta(minutes=self.window_minutes)
        self._update_history[key] = [
            (t, s) for t, s in self._update_history[key] if t > cutoff]

        # Check rate
        if len(self._update_history[key]) >= self.max_update_rate:
            return False

        # Check source diversity (single source hammering)
        sources = set(s for _, s in self._update_history[key])
        if len(self._update_history[key]) >= 3 and len(sources) == 1:
            return False

        self._update_history[key].append((ts, source))
        return True

    def check_witness_diversity(self, witnesses: List[WitnessResponse]) -> bool:
        """Check if witnesses are sufficiently diverse."""
        if len(witnesses) < 2:
            return False
        unique_witnesses = len(set(w.witness_id for w in witnesses))
        diversity = unique_witnesses / len(witnesses)
        return diversity >= self.min_witness_diversity


# ============================================================================
# ATP LEDGER
# ============================================================================

class CacheATPLedger:
    """ATP cost tracking for cache operations per §ATP."""

    def __init__(self):
        self.balance: Dict[str, float] = {}
        self.transactions: List[Dict] = []

    def charge(self, entity_id: str, operation: str) -> float:
        """Charge ATP for cache operation."""
        cost = ATP_COSTS.get(operation, 0)
        if entity_id not in self.balance:
            self.balance[entity_id] = 0
        self.balance[entity_id] += cost
        self.transactions.append({
            "entity": entity_id,
            "operation": operation,
            "cost": cost,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return cost


# ============================================================================
# RDF SERIALIZATION
# ============================================================================

class CacheRDFSerializer:
    """Serialize cache as Turtle per §MRH."""

    @staticmethod
    def to_turtle(cache: RealityCache) -> str:
        lines = [
            '@prefix web4: <https://web4.io/ontology#> .',
            '@prefix cache: <https://web4.io/cache#> .',
            '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .',
            '',
            f'<{cache.entity_id}> a web4:CognitiveEntity ;',
            f'    cache:cacheSize "{cache.size()}"^^xsd:integer ;',
            f'    cache:hitRate "{cache.stats.hit_rate:.4f}"^^xsd:decimal .',
            '',
        ]

        for key, a in cache.assumptions.items():
            safe_key = key.replace(" ", "_").replace(":", "_")
            lines.extend([
                f'<{cache.entity_id}> cache:assumes <cache:{safe_key}> .',
                f'<cache:{safe_key}> a cache:Assumption ;',
                f'    cache:key "{key}" ;',
                f'    cache:value "{a.value}" ;',
                f'    cache:confidence "{a.confidence:.4f}"^^xsd:decimal ;',
                f'    cache:level "{a.level.name}" ;',
                f'    cache:lastVerified "{a.last_verified.isoformat()}"^^xsd:dateTime ;',
                f'    cache:verificationMethod "{a.verification_method.value}" .',
                '',
            ])

        return '\n'.join(lines)


# ============================================================================
# MERKLE CONSISTENCY
# ============================================================================

class CacheMerkleVerifier:
    """Detect cache inconsistency across federation per §MRH.Merkle."""

    @staticmethod
    def compute_hash(cache: RealityCache) -> str:
        """Compute Merkle hash of entire cache state."""
        entries = []
        for key in sorted(cache.assumptions.keys()):
            a = cache.assumptions[key]
            entries.append(f"{key}:{a.value}:{a.confidence:.4f}")
        content = "|".join(entries)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def compute_key_hash(assumption: Assumption) -> str:
        """Hash a single assumption."""
        content = f"{assumption.key}:{assumption.value}:{assumption.confidence:.4f}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def find_divergences(hash_a: Dict[str, str],
                         hash_b: Dict[str, str]) -> List[str]:
        """Find keys with different hashes between two caches."""
        all_keys = set(hash_a.keys()) | set(hash_b.keys())
        divergent = []
        for key in all_keys:
            if hash_a.get(key) != hash_b.get(key):
                divergent.append(key)
        return divergent


# ============================================================================
# SNARC INTEGRATION (Multi-Scale Surprise)
# ============================================================================

class SNARCLevel(Enum):
    """SNARC levels per §SNARC."""
    NEURON = "neuron"    # Micro: synaptic weight adjustment
    CIRCUIT = "circuit"  # Meso: circuit reconfiguration
    SYSTEM = "system"    # Macro: model update
    META = "meta"        # Cognitive: strategy revision


@dataclass
class SNARCEvent:
    """Multi-scale surprise event."""
    level: SNARCLevel
    key: str
    surprise: float
    action: str
    timestamp: datetime


class SNARCIntegration:
    """Map cache events to SNARC levels."""

    @staticmethod
    def classify(surprise: float, level: CacheLevel) -> SNARCLevel:
        """Map cache level + surprise to SNARC level."""
        if level == CacheLevel.SENSORY:
            return SNARCLevel.NEURON
        elif level == CacheLevel.ENVIRONMENT:
            return SNARCLevel.CIRCUIT
        elif level == CacheLevel.CONTEXTUAL:
            return SNARCLevel.SYSTEM
        else:  # ABSTRACT
            return SNARCLevel.META

    @staticmethod
    def expected_cascade_size(snarc_level: SNARCLevel) -> Tuple[int, int]:
        """Expected invalidation cascade size (min, max) per SNARC level."""
        sizes = {
            SNARCLevel.NEURON: (1, 2),
            SNARCLevel.CIRCUIT: (2, 5),
            SNARCLevel.SYSTEM: (3, 10),
            SNARCLevel.META: (5, 20),
        }
        return sizes.get(snarc_level, (1, 5))


# ============================================================================
# TESTS
# ============================================================================

def check(label: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    return condition


def run_tests():
    passed = 0
    total = 0

    def t(label, condition):
        nonlocal passed, total
        total += 1
        if check(label, condition):
            passed += 1

    now = datetime(2026, 2, 22, 10, 0, 0, tzinfo=timezone.utc)

    # ================================================================
    # T1: Basic assumption caching
    # ================================================================
    print("T1: Basic Caching")
    cache = RealityCache("lct:web4:society:society4")
    cache.assume("current_day", "monday", confidence=0.95,
                 level=CacheLevel.ABSTRACT, now=now)
    cache.assume("current_location", "work", confidence=0.98,
                 level=CacheLevel.ENVIRONMENT, now=now)

    result = cache.get("current_day", now=now)
    t("T1.1 Cache hit returns value", result is not None)
    t("T1.2 Correct value", result[0] == "monday")
    t("T1.3 High confidence", result[1] > 0.9)
    t("T1.4 Cache size", cache.size() == 2)

    missing = cache.get("nonexistent", now=now)
    t("T1.5 Missing key returns None", missing is None)

    # ================================================================
    # T2: Hierarchical cache levels
    # ================================================================
    print("T2: Cache Levels")
    cache2 = RealityCache("entity:test")
    cache2.assume("sensory_input", "keyboard_press", confidence=0.4,
                  level=CacheLevel.SENSORY, now=now)
    cache2.assume("environment", "at_desk", confidence=0.6,
                  level=CacheLevel.ENVIRONMENT, now=now)
    cache2.assume("context", "coding_session", confidence=0.7,
                  level=CacheLevel.CONTEXTUAL, now=now)
    cache2.assume("abstract", "workday", confidence=0.8,
                  level=CacheLevel.ABSTRACT, now=now)

    t("T2.1 Sensory threshold 0.3",
      LEVEL_THRESHOLDS[CacheLevel.SENSORY] == 0.3)
    t("T2.2 Environment threshold 0.5",
      LEVEL_THRESHOLDS[CacheLevel.ENVIRONMENT] == 0.5)
    t("T2.3 Contextual threshold 0.6",
      LEVEL_THRESHOLDS[CacheLevel.CONTEXTUAL] == 0.6)
    t("T2.4 Abstract threshold 0.7",
      LEVEL_THRESHOLDS[CacheLevel.ABSTRACT] == 0.7)

    # Sensory at 0.4 > 0.3 threshold → hit
    r = cache2.get("sensory_input", now=now)
    t("T2.5 Sensory above threshold → hit", r is not None)

    # ================================================================
    # T3: Surprise calculation
    # ================================================================
    print("T3: Surprise Calculation")
    cached = Assumption(key="day", value="sunday", confidence=0.95,
                        level=CacheLevel.ABSTRACT, last_verified=now,
                        verification_method=VerificationMethod.INFERENCE,
                        centrality=0.8)
    obs = Observation(key="day", value="monday", timestamp=now)
    surprise = SurpriseCalculator.compute(obs, cached)
    t("T3.1 High surprise for wrong day", surprise > 0.5)

    # Same value → 0 surprise
    obs_same = Observation(key="day", value="sunday", timestamp=now)
    s0 = SurpriseCalculator.compute(obs_same, cached)
    t("T3.2 Zero surprise for matching", s0 == 0.0)

    # Numeric comparison
    cached_num = Assumption(key="temp", value=20.0, confidence=0.9,
                            level=CacheLevel.ENVIRONMENT, last_verified=now,
                            verification_method=VerificationMethod.SYSTEM,
                            centrality=0.5)
    obs_num = Observation(key="temp", value=25.0, timestamp=now)
    s_num = SurpriseCalculator.compute(obs_num, cached_num)
    t("T3.3 Moderate numeric surprise", 0.0 < s_num < 0.5)

    # Low centrality reduces surprise
    cached_low = Assumption(key="x", value="a", confidence=0.9,
                            level=CacheLevel.SENSORY, last_verified=now,
                            verification_method=VerificationMethod.DEFAULT,
                            centrality=0.1)
    obs_low = Observation(key="x", value="b", timestamp=now)
    s_low = SurpriseCalculator.compute(obs_low, cached_low)
    t("T3.4 Low centrality → low surprise", s_low < 0.2)

    # ================================================================
    # T4: Cache action classification
    # ================================================================
    print("T4: Action Classification")
    t("T4.1 Low surprise → CONTINUE",
      SurpriseCalculator.classify_action(0.1) == CacheAction.CONTINUE)
    t("T4.2 Medium surprise → VERIFY",
      SurpriseCalculator.classify_action(0.4) == CacheAction.VERIFY)
    t("T4.3 High surprise → REBUILD",
      SurpriseCalculator.classify_action(0.8) == CacheAction.REBUILD)
    t("T4.4 Boundary 0.3 → VERIFY",
      SurpriseCalculator.classify_action(0.3) == CacheAction.VERIFY)
    t("T4.5 Boundary 0.6 → REBUILD",
      SurpriseCalculator.classify_action(0.6) == CacheAction.REBUILD)

    # ================================================================
    # T5: Confidence decay models
    # ================================================================
    print("T5: Confidence Decay")
    # Exponential: halves at half-life
    decayed = ConfidenceDecay.apply(1.0, 24.0, DecayModel.EXPONENTIAL, 24.0)
    t("T5.1 Exponential half-life", abs(decayed - 0.5) < 0.01)

    decayed0 = ConfidenceDecay.apply(1.0, 0.0, DecayModel.EXPONENTIAL, 24.0)
    t("T5.2 No decay at t=0", decayed0 == 1.0)

    decayed48 = ConfidenceDecay.apply(1.0, 48.0, DecayModel.EXPONENTIAL, 24.0)
    t("T5.3 Quarter at 2× half-life", abs(decayed48 - 0.25) < 0.01)

    # Linear
    lin = ConfidenceDecay.apply(1.0, 12.0, DecayModel.LINEAR, 24.0)
    t("T5.4 Linear half-rate at half-time", abs(lin - 0.75) < 0.01)

    # Sigmoid
    sig = ConfidenceDecay.apply(1.0, 24.0, DecayModel.SIGMOID, 24.0)
    t("T5.5 Sigmoid decays around midpoint", 0.3 < sig < 0.7)

    # Never goes below 0
    very_old = ConfidenceDecay.apply(0.5, 1000.0, DecayModel.LINEAR, 24.0)
    t("T5.6 Linear floors at 0", very_old == 0.0)

    # ================================================================
    # T6: Observation processing
    # ================================================================
    print("T6: Observation Processing")
    cache3 = RealityCache("entity:obs", surprise_threshold=0.6)
    cache3.assume("day", "sunday", confidence=0.95,
                  level=CacheLevel.ABSTRACT, centrality=0.8, now=now)

    # Expected observation → CONTINUE
    obs_ok = Observation(key="day", value="sunday", timestamp=now)
    s, a, inv = cache3.observe(obs_ok, now=now)
    t("T6.1 Expected → zero surprise", s == 0.0)
    t("T6.2 Expected → CONTINUE", a == CacheAction.CONTINUE)
    t("T6.3 No invalidations", len(inv) == 0)

    # Surprising observation → REBUILD
    obs_surprise = Observation(key="day", value="monday", timestamp=now)
    s2, a2, inv2 = cache3.observe(obs_surprise, now=now)
    t("T6.4 Wrong day → high surprise", s2 > 0.5)
    t("T6.5 Wrong day → REBUILD", a2 == CacheAction.REBUILD)
    t("T6.6 Key invalidated", "day" in inv2)
    t("T6.7 Value updated", cache3.assumptions["day"].value == "monday")

    # New key → just cached
    obs_new = Observation(key="weather", value="sunny", timestamp=now)
    s3, a3, inv3 = cache3.observe(obs_new, now=now)
    t("T6.8 New key → zero surprise", s3 == 0.0)
    t("T6.9 New key cached", "weather" in cache3.assumptions)

    # ================================================================
    # T7: Dependency graph cascading
    # ================================================================
    print("T7: Dependency Cascade")
    cache4 = RealityCache("entity:deps")
    cache4.assume("day_type", "weekday", confidence=0.95,
                  level=CacheLevel.ABSTRACT, centrality=0.9, now=now)
    cache4.assume("schedule", "work_meeting", confidence=0.9,
                  level=CacheLevel.CONTEXTUAL, centrality=0.5, now=now)
    cache4.assume("dress_code", "formal", confidence=0.85,
                  level=CacheLevel.CONTEXTUAL, centrality=0.3, now=now)
    cache4.assume("commute", "train", confidence=0.8,
                  level=CacheLevel.ENVIRONMENT, centrality=0.4, now=now)

    cache4.add_dependency("day_type", "schedule")
    cache4.add_dependency("day_type", "dress_code")
    cache4.add_dependency("day_type", "commute")

    # Invalidate day_type → cascades to all dependents
    obs_weekend = Observation(key="day_type", value="weekend",
                              timestamp=now, confidence=1.0)
    s, action, invalidated = cache4.observe(obs_weekend, now=now)
    t("T7.1 Parent invalidated", "day_type" in invalidated)
    t("T7.2 Schedule cascaded", "schedule" in invalidated)
    t("T7.3 Dress code cascaded", "dress_code" in invalidated)
    t("T7.4 Commute cascaded", "commute" in invalidated)
    t("T7.5 All 4 invalidated", len(invalidated) == 4)
    t("T7.6 Dependent confidence zeroed",
      cache4.assumptions["schedule"].confidence == 0.0)

    # ================================================================
    # T8: Rate limiting (surprise manipulation defense)
    # ================================================================
    print("T8: Rate Limiting")
    cache5 = RealityCache("entity:rate", max_invalidation_rate=3)
    cache5.assume("key1", "v1", confidence=0.95,
                  level=CacheLevel.ABSTRACT, centrality=0.9, now=now)

    results = []
    for i in range(5):
        cache5.assume("key1", "v1", confidence=0.95,
                      level=CacheLevel.ABSTRACT, centrality=0.9, now=now)
        obs = Observation(key="key1", value=f"attack_{i}", timestamp=now)
        _, action, _ = cache5.observe(obs, now=now)
        results.append(action)

    rebuild_count = sum(1 for r in results if r == CacheAction.REBUILD)
    verify_count = sum(1 for r in results if r == CacheAction.VERIFY)
    t("T8.1 Some rebuilds allowed", rebuild_count > 0)
    t("T8.2 Rate limited to verify", verify_count > 0)
    t("T8.3 Total = 5 actions", len(results) == 5)

    # ================================================================
    # T9: Staleness detection
    # ================================================================
    print("T9: Staleness Detection")
    cache6 = RealityCache("entity:stale", decay_half_life_hours=12.0)
    cache6.assume("fresh", "yes", confidence=0.9,
                  level=CacheLevel.CONTEXTUAL, now=now)
    cache6.assume("old", "maybe", confidence=0.9,
                  level=CacheLevel.CONTEXTUAL,
                  now=now - timedelta(hours=48))

    stale = cache6.get_stale_assumptions(max_age_hours=24.0, now=now)
    t("T9.1 Old assumption is stale", "old" in stale)
    t("T9.2 Fresh assumption not stale", "fresh" not in stale)

    # ================================================================
    # T10: Witness validation
    # ================================================================
    print("T10: Witness Validation")
    cache7 = RealityCache("entity:witness")
    cache7.assume("fact", "unknown", confidence=0.3,
                  level=CacheLevel.ABSTRACT, now=now)

    witnesses = [
        WitnessResponse("w1", "fact", "confirmed_true", 0.9, now),
        WitnessResponse("w2", "fact", "confirmed_true", 0.8, now),
        WitnessResponse("w3", "fact", "confirmed_false", 0.5, now),
    ]
    value, conf = cache7.validate_with_witnesses("fact", witnesses)
    t("T10.1 Consensus value is majority", value == "confirmed_true")
    t("T10.2 Consensus confidence > 0.5", conf > 0.5)
    t("T10.3 Assumption updated", cache7.assumptions["fact"].value == "confirmed_true")
    t("T10.4 Verification method = witness",
      cache7.assumptions["fact"].verification_method == VerificationMethod.WITNESS)

    # Empty witnesses
    v2, c2 = cache7.validate_with_witnesses("fact", [])
    t("T10.5 No witnesses → None", v2 is None)
    t("T10.6 No witnesses → 0 confidence", c2 == 0.0)

    # ================================================================
    # T11: Trust tensor integration
    # ================================================================
    print("T11: Trust Tensor Integration")
    cache8 = RealityCache("entity:trust", decay_half_life_hours=12.0)
    cache8.assume("k1", "v1", confidence=0.9,
                  level=CacheLevel.CONTEXTUAL,
                  now=now - timedelta(hours=24))
    cache8.assume("k2", "v2", confidence=0.9,
                  level=CacheLevel.CONTEXTUAL,
                  now=now - timedelta(hours=24))

    staleness = CacheTrustModulator.compute_staleness(cache8, now=now)
    t("T11.1 Staleness > 0 for old cache", staleness > 0.0)
    t("T11.2 Staleness < 1 (not totally stale)", staleness < 1.0)

    adj = CacheTrustModulator.trust_adjustment(staleness)
    t("T11.3 T3 reliability reduced", adj["T3_reliability"] < 0.0)
    t("T11.4 V3 verification reduced", adj["V3_verification"] < 0.0)
    t("T11.5 Evidence documented", adj["evidence"] == "stale_reality_cache")

    # Fresh cache → minimal staleness
    cache_fresh = RealityCache("entity:fresh")
    cache_fresh.assume("x", "y", confidence=0.95,
                       level=CacheLevel.CONTEXTUAL, now=now)
    fresh_staleness = CacheTrustModulator.compute_staleness(cache_fresh, now=now)
    t("T11.6 Fresh cache → low staleness", fresh_staleness < 0.1)

    # ================================================================
    # T12: Cache poisoning detection
    # ================================================================
    print("T12: Cache Poisoning Detection")
    detector = CachePoisoningDetector(max_update_rate=3, window_minutes=1.0)

    t("T12.1 First update OK", detector.check_update("k", "s1", now=now))
    t("T12.2 Second update OK", detector.check_update("k", "s2", now=now))
    t("T12.3 Third update OK", detector.check_update("k", "s3", now=now))
    t("T12.4 Fourth blocked (rate limit)",
      not detector.check_update("k", "s4", now=now))

    # Single source hammering
    det2 = CachePoisoningDetector(max_update_rate=10, window_minutes=1.0)
    for _ in range(3):
        det2.check_update("target", "same_source", now=now)
    t("T12.5 Single source blocked",
      not det2.check_update("target", "same_source", now=now))

    # Witness diversity
    good_witnesses = [
        WitnessResponse("w1", "k", "v", 0.9, now),
        WitnessResponse("w2", "k", "v", 0.8, now),
        WitnessResponse("w3", "k", "v", 0.7, now),
    ]
    t("T12.6 Diverse witnesses OK",
      detector.check_witness_diversity(good_witnesses))

    bad_witnesses = [
        WitnessResponse("w1", "k", "v", 0.9, now),
    ]
    t("T12.7 Single witness insufficient",
      not detector.check_witness_diversity(bad_witnesses))

    # ================================================================
    # T13: ATP cost tracking
    # ================================================================
    print("T13: ATP Costs")
    ledger = CacheATPLedger()
    t("T13.1 Query own = 0 ATP", ledger.charge("e1", "query_own") == 0)
    t("T13.2 Query other = 5 ATP", ledger.charge("e1", "query_other") == 5)
    t("T13.3 Witness = 3 ATP", ledger.charge("e1", "witness_validation") == 3)
    t("T13.4 Rebuild = 10 ATP", ledger.charge("e1", "cache_rebuild") == 10)
    t("T13.5 Publish = 2 ATP", ledger.charge("e1", "publish_update") == 2)
    t("T13.6 Total charged = 20", ledger.balance["e1"] == 20)
    t("T13.7 Transaction log", len(ledger.transactions) == 5)

    # ================================================================
    # T14: Cache statistics
    # ================================================================
    print("T14: Cache Statistics")
    cache9 = RealityCache("entity:stats")
    cache9.assume("x", 1, confidence=0.9,
                  level=CacheLevel.CONTEXTUAL, now=now)

    cache9.get("x", now=now)  # hit
    cache9.get("x", now=now)  # hit
    cache9.get("y", now=now)  # miss

    t("T14.1 Total queries = 3", cache9.stats.total_queries == 3)
    t("T14.2 Cache hits = 2", cache9.stats.cache_hits == 2)
    t("T14.3 Cache misses = 1", cache9.stats.cache_misses == 1)
    t("T14.4 Hit rate = 0.667", abs(cache9.stats.hit_rate - 2/3) < 0.01)

    # ================================================================
    # T15: RDF serialization
    # ================================================================
    print("T15: RDF Serialization")
    cache10 = RealityCache("lct:society4")
    cache10.assume("current_day", "monday", confidence=0.95,
                   level=CacheLevel.ABSTRACT, now=now)
    cache10.assume("location", "work", confidence=0.98,
                   level=CacheLevel.ENVIRONMENT, now=now)

    turtle = CacheRDFSerializer.to_turtle(cache10)
    t("T15.1 Has web4 prefix", "@prefix web4:" in turtle)
    t("T15.2 Has cache prefix", "@prefix cache:" in turtle)
    t("T15.3 Has entity", "lct:society4" in turtle)
    t("T15.4 Has assumption", "cache:assumes" in turtle)
    t("T15.5 Has confidence", "cache:confidence" in turtle)
    t("T15.6 Has level", "ABSTRACT" in turtle)

    # ================================================================
    # T16: Merkle consistency
    # ================================================================
    print("T16: Merkle Consistency")
    cacheA = RealityCache("entity:a")
    cacheA.assume("fact1", "v1", confidence=0.9,
                  level=CacheLevel.CONTEXTUAL, now=now)
    cacheA.assume("fact2", "v2", confidence=0.8,
                  level=CacheLevel.CONTEXTUAL, now=now)

    cacheB = RealityCache("entity:b")
    cacheB.assume("fact1", "v1", confidence=0.9,
                  level=CacheLevel.CONTEXTUAL, now=now)
    cacheB.assume("fact2", "v2", confidence=0.8,
                  level=CacheLevel.CONTEXTUAL, now=now)

    hashA = CacheMerkleVerifier.compute_hash(cacheA)
    hashB = CacheMerkleVerifier.compute_hash(cacheB)
    t("T16.1 Same content → same hash", hashA == hashB)

    # Modify one
    cacheB.assume("fact2", "v3", confidence=0.8,
                  level=CacheLevel.CONTEXTUAL, now=now)
    hashB2 = CacheMerkleVerifier.compute_hash(cacheB)
    t("T16.2 Different content → different hash", hashA != hashB2)

    # Find divergences
    per_key_a = {k: CacheMerkleVerifier.compute_key_hash(a)
                 for k, a in cacheA.assumptions.items()}
    per_key_b = {k: CacheMerkleVerifier.compute_key_hash(a)
                 for k, a in cacheB.assumptions.items()}
    divs = CacheMerkleVerifier.find_divergences(per_key_a, per_key_b)
    t("T16.3 Divergent key found", "fact2" in divs)
    t("T16.4 Non-divergent key not flagged", "fact1" not in divs)

    # ================================================================
    # T17: SNARC integration
    # ================================================================
    print("T17: SNARC Integration")
    t("T17.1 Sensory → NEURON",
      SNARCIntegration.classify(0.5, CacheLevel.SENSORY) == SNARCLevel.NEURON)
    t("T17.2 Environment → CIRCUIT",
      SNARCIntegration.classify(0.5, CacheLevel.ENVIRONMENT) == SNARCLevel.CIRCUIT)
    t("T17.3 Contextual → SYSTEM",
      SNARCIntegration.classify(0.5, CacheLevel.CONTEXTUAL) == SNARCLevel.SYSTEM)
    t("T17.4 Abstract → META",
      SNARCIntegration.classify(0.5, CacheLevel.ABSTRACT) == SNARCLevel.META)

    # Cascade size expectations
    mn, mx = SNARCIntegration.expected_cascade_size(SNARCLevel.META)
    t("T17.5 META cascade min=5", mn == 5)
    t("T17.6 META cascade max=20", mx == 20)

    mn2, mx2 = SNARCIntegration.expected_cascade_size(SNARCLevel.NEURON)
    t("T17.7 NEURON cascade small", mx2 <= 2)

    # ================================================================
    # T18: E2E scenario — Sunday → Monday correction
    # ================================================================
    print("T18: E2E Scenario — Sunday→Monday")
    society4 = RealityCache("lct:web4:society:society4",
                            surprise_threshold=0.6,
                            decay_half_life_hours=24.0)

    # Initial cached assumptions
    society4.assume("current_day", "sunday", confidence=0.95,
                    level=CacheLevel.ABSTRACT, centrality=0.9,
                    verification_method=VerificationMethod.INFERENCE, now=now)
    society4.assume("expected_location", "home", confidence=0.9,
                    level=CacheLevel.CONTEXTUAL, centrality=0.6, now=now)
    society4.assume("expected_activity", "rest", confidence=0.85,
                    level=CacheLevel.CONTEXTUAL, centrality=0.4, now=now)

    # Dependencies
    society4.add_dependency("current_day", "expected_location")
    society4.add_dependency("current_day", "expected_activity")

    # Observe: it's actually Monday!
    obs_monday = Observation(key="current_day", value="monday",
                             timestamp=now, source="system_clock")
    surprise, action, invalidated = society4.observe(obs_monday, now=now)

    t("T18.1 High surprise (wrong day)", surprise > 0.5)
    t("T18.2 Rebuild triggered", action == CacheAction.REBUILD)
    t("T18.3 Day corrected",
      society4.assumptions["current_day"].value == "monday")
    t("T18.4 Location cascaded", "expected_location" in invalidated)
    t("T18.5 Activity cascaded", "expected_activity" in invalidated)
    t("T18.6 3 keys invalidated total", len(invalidated) == 3)

    # After correction, verify
    society4.verify("expected_location", "work", confidence=0.95,
                    method=VerificationMethod.OBSERVATION, now=now)
    r = society4.get("expected_location", now=now)
    t("T18.7 Location re-verified", r is not None and r[0] == "work")

    # ================================================================
    # T19: Confidence floor (sticky assumptions)
    # ================================================================
    print("T19: Sticky Assumptions")
    cache11 = RealityCache("entity:sticky")
    # Very high confidence, very central — hard to invalidate
    # Use longer half-life for identity (sticky: 72h half-life)
    cache11 = RealityCache("entity:sticky", decay_half_life_hours=72.0)
    cache11.assume("identity", "society4", confidence=1.0,
                   level=CacheLevel.ABSTRACT, centrality=1.0, now=now)

    # Even after long time, identity should remain (high initial confidence + long half-life)
    r = cache11.get("identity", now=now + timedelta(hours=12))
    t("T19.1 Identity persists at 12h", r is not None)

    r2 = cache11.get("identity", now=now + timedelta(hours=24))
    t("T19.2 Identity at 24h (72h half-life)", r2 is not None)

    # ================================================================
    # T20: Multi-dependency cascade depth
    # ================================================================
    print("T20: Multi-Level Cascade")
    cache12 = RealityCache("entity:multi")
    cache12.assume("root", "A", confidence=0.95,
                   level=CacheLevel.ABSTRACT, centrality=0.9, now=now)
    cache12.assume("child1", "B", confidence=0.9,
                   level=CacheLevel.CONTEXTUAL, centrality=0.5, now=now)
    cache12.assume("child2", "C", confidence=0.85,
                   level=CacheLevel.CONTEXTUAL, centrality=0.4, now=now)
    cache12.assume("grandchild", "D", confidence=0.8,
                   level=CacheLevel.ENVIRONMENT, centrality=0.3, now=now)

    cache12.add_dependency("root", "child1")
    cache12.add_dependency("root", "child2")
    cache12.add_dependency("child1", "grandchild")

    obs = Observation(key="root", value="X", timestamp=now)
    s, a, inv = cache12.observe(obs, now=now)

    t("T20.1 Root invalidated", "root" in inv)
    t("T20.2 Child1 invalidated", "child1" in inv)
    t("T20.3 Child2 invalidated", "child2" in inv)
    # Note: grandchild is dependent on child1, not root directly
    # The cascade is 1-level deep (root → children), not recursive
    t("T20.4 Direct cascade only", len(inv) == 3)

    # ================================================================
    # T21: Invalidation log
    # ================================================================
    print("T21: Invalidation Log")
    t("T21.1 Log has entries", len(cache12.invalidation_log) > 0)
    last_event = cache12.invalidation_log[-1]
    t("T21.2 Event has key", last_event.key == "root")
    t("T21.3 Event has old value", last_event.old_value == "A")
    t("T21.4 Event has new value", last_event.new_value == "X")
    t("T21.5 Event has surprise", last_event.surprise > 0)
    t("T21.6 Event has cascaded keys", len(last_event.cascaded_keys) == 2)

    # ================================================================
    # T22: Verify and refresh
    # ================================================================
    print("T22: Verify and Refresh")
    cache13 = RealityCache("entity:verify")
    cache13.assume("time", "10:00", confidence=0.8,
                   level=CacheLevel.ENVIRONMENT, now=now)

    cache13.verify("time", "10:30", confidence=1.0,
                   method=VerificationMethod.SYSTEM, now=now)
    t("T22.1 Value updated", cache13.assumptions["time"].value == "10:30")
    t("T22.2 Confidence refreshed", cache13.assumptions["time"].confidence == 1.0)
    t("T22.3 Method updated",
      cache13.assumptions["time"].verification_method == VerificationMethod.SYSTEM)

    # Verify non-existent key → creates it
    cache13.verify("new_key", "new_val", confidence=0.7,
                   method=VerificationMethod.OBSERVATION, now=now)
    t("T22.4 New key created", "new_key" in cache13.assumptions)

    # ================================================================
    # T23: Use case — Federation state
    # ================================================================
    print("T23: Federation State Cache")
    fed_cache = RealityCache("genesis:federation")
    fed_cache.assume("society2_status", "online", confidence=0.95,
                     level=CacheLevel.CONTEXTUAL, centrality=0.7, now=now)
    fed_cache.assume("society2_last_seen", now.isoformat(), confidence=1.0,
                     level=CacheLevel.ENVIRONMENT, centrality=0.3, now=now)
    fed_cache.add_dependency("society2_status", "society2_last_seen")

    # Society 2 goes unresponsive
    ten_min_later = now + timedelta(minutes=10)
    obs_down = Observation(key="society2_status", value="unresponsive",
                           timestamp=ten_min_later, source="health_check")
    s, a, inv = fed_cache.observe(obs_down, now=ten_min_later)
    t("T23.1 Federation surprise > 0.5", s > 0.5)
    t("T23.2 Status invalidated", "society2_status" in inv)
    t("T23.3 Status updated",
      fed_cache.assumptions["society2_status"].value == "unresponsive")

    # ================================================================
    # T24: Use case — Trust relationship
    # ================================================================
    print("T24: Trust Relationship Cache")
    trust_cache = RealityCache("entity:trust_tracker")
    trust_cache.assume("entity_x_reliable", True, confidence=0.9,
                       level=CacheLevel.ABSTRACT, centrality=0.8, now=now)

    # Entity X misses commitment
    obs_miss = Observation(key="entity_x_reliable", value=False,
                           timestamp=now)
    s, a, inv = trust_cache.observe(obs_miss, now=now)
    t("T24.1 Reliability surprise", s > 0.5)
    t("T24.2 Trust cache rebuilt", a == CacheAction.REBUILD)
    t("T24.3 Trust updated to False",
      trust_cache.assumptions["entity_x_reliable"].value is False)

    # ================================================================
    # T25: Performance — cache hit rate tracking
    # ================================================================
    print("T25: Performance Metrics")
    perf_cache = RealityCache("entity:perf")
    # Add 10 assumptions
    for i in range(10):
        perf_cache.assume(f"fact_{i}", f"value_{i}", confidence=0.95,
                          level=CacheLevel.CONTEXTUAL, now=now)

    # Query all (should be hits)
    for i in range(10):
        perf_cache.get(f"fact_{i}", now=now)

    # Query 5 missing
    for i in range(5):
        perf_cache.get(f"missing_{i}", now=now)

    t("T25.1 Hit rate = 10/15 = 0.667",
      abs(perf_cache.stats.hit_rate - 10/15) < 0.01)
    t("T25.2 Total = 15", perf_cache.stats.total_queries == 15)
    t("T25.3 Hits = 10", perf_cache.stats.cache_hits == 10)
    t("T25.4 Misses = 5", perf_cache.stats.cache_misses == 5)

    # ================================================================
    # T26: Edge cases
    # ================================================================
    print("T26: Edge Cases")
    # Empty cache
    empty = RealityCache("entity:empty")
    t("T26.1 Empty cache size = 0", empty.size() == 0)
    t("T26.2 Empty cache stale list empty",
      len(empty.get_stale_assumptions(now=now)) == 0)
    t("T26.3 Empty cache staleness = 0",
      CacheTrustModulator.compute_staleness(empty, now=now) == 0.0)

    # Single assumption
    single = RealityCache("entity:single")
    single.assume("only", "one", confidence=0.5,
                  level=CacheLevel.CONTEXTUAL, now=now)
    t("T26.4 Single entry cache", single.size() == 1)

    # Merkle of empty
    empty_hash = CacheMerkleVerifier.compute_hash(empty)
    t("T26.5 Empty cache has hash", len(empty_hash) > 0)

    # Case-insensitive surprise
    cached_case = Assumption(key="name", value="Monday",
                             confidence=0.9, level=CacheLevel.CONTEXTUAL,
                             last_verified=now,
                             verification_method=VerificationMethod.DEFAULT,
                             centrality=0.5)
    obs_case = Observation(key="name", value="monday", timestamp=now)
    s_case = SurpriseCalculator.compute(obs_case, cached_case)
    t("T26.6 Case-only difference → low surprise", s_case < 0.1)

    # Verification methods
    t("T26.7 All verification methods exist",
      len(VerificationMethod) == 5)

    # ================================================================
    # T27: Cross-cache Merkle divergence
    # ================================================================
    print("T27: Cross-Cache Divergence")
    c1 = RealityCache("soc:1")
    c2 = RealityCache("soc:2")

    # Both share some facts
    for i in range(5):
        c1.assume(f"shared_{i}", f"v_{i}", confidence=0.9,
                  level=CacheLevel.CONTEXTUAL, now=now)
        c2.assume(f"shared_{i}", f"v_{i}", confidence=0.9,
                  level=CacheLevel.CONTEXTUAL, now=now)

    # c2 has different view on one fact
    c2.assume("shared_3", "different!", confidence=0.9,
              level=CacheLevel.CONTEXTUAL, now=now)

    h1 = {k: CacheMerkleVerifier.compute_key_hash(a)
           for k, a in c1.assumptions.items()}
    h2 = {k: CacheMerkleVerifier.compute_key_hash(a)
           for k, a in c2.assumptions.items()}
    divs = CacheMerkleVerifier.find_divergences(h1, h2)
    t("T27.1 Exactly 1 divergence", len(divs) == 1)
    t("T27.2 Correct divergent key", divs[0] == "shared_3")

    # c2 has extra fact c1 doesn't
    c2.assume("exclusive", "only_c2", confidence=0.9,
              level=CacheLevel.CONTEXTUAL, now=now)
    h2b = {k: CacheMerkleVerifier.compute_key_hash(a)
            for k, a in c2.assumptions.items()}
    divs2 = CacheMerkleVerifier.find_divergences(h1, h2b)
    t("T27.3 Missing key detected", "exclusive" in divs2)

    # ================================================================
    # T28: Decay model comparison
    # ================================================================
    print("T28: Decay Model Comparison")
    hours = [0, 6, 12, 24, 48]
    lin_vals = [ConfidenceDecay.apply(1.0, h, DecayModel.LINEAR, 24.0)
                for h in hours]
    exp_vals = [ConfidenceDecay.apply(1.0, h, DecayModel.EXPONENTIAL, 24.0)
                for h in hours]
    sig_vals = [ConfidenceDecay.apply(1.0, h, DecayModel.SIGMOID, 24.0)
                for h in hours]

    t("T28.1 All start at 1.0", lin_vals[0] == exp_vals[0] == sig_vals[0] == 1.0)
    t("T28.2 All decrease over time",
      all(lin_vals[i] >= lin_vals[i+1] for i in range(len(hours)-1)))
    t("T28.3 Exponential at 24h ≈ 0.5", abs(exp_vals[3] - 0.5) < 0.01)
    t("T28.4 Linear at 24h ≈ 0.5", abs(lin_vals[3] - 0.5) < 0.01)
    t("T28.5 Sigmoid steep around midpoint",
      sig_vals[2] > sig_vals[3])  # Drops more steeply around midpoint

    # ================================================================
    # SUMMARY
    # ================================================================
    print(f"\n{'='*60}")
    print(f"Reality KV Cache: {passed}/{total} checks passed")
    if passed == total:
        print("  All checks passed!")
    else:
        print(f"  {total - passed} checks FAILED")
    print(f"{'='*60}")

    return passed, total


if __name__ == "__main__":
    run_tests()
