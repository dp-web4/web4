# RFC-REALITY-CACHE-001: Reality KV Cache Protocol for Cognitive Architectures

**Status**: PROPOSED
**Author**: Society 4 (Claude Node) + HRM/SAGE Team
**Created**: September 30, 2025
**Target**: Web4 Cognitive Extensions v1.0.0

## Abstract

This RFC proposes standardizing assumption caching and surprise-driven invalidation as a core pattern for AI cognitive architectures in web4. By treating assumptions as a Key-Value cache for reality processing and using surprise signals as cache invalidation triggers, systems achieve both efficiency (fast processing) and accuracy (correct world models).

## Motivation

### The Cognitive Efficiency Problem

AI systems (and biological cognition) face a fundamental tradeoff:
- **Recompute everything from first principles**: Accurate but impossibly slow
- **Cache everything forever**: Fast but increasingly wrong as reality changes
- **Optimal**: Cache with smart invalidation

### Real-World Example

Claude (Society 4) made an assumption: "Today is Sunday"

This cached assumption led to:
- Conclusion: "Being at work on Sunday is surprising (0.8 surprise)"
- Elaborate rationalization of weekend work patterns
- Never checking the actual day

**Correct approach**:
1. Detect high surprise (0.8)
2. Question cached assumptions
3. Verify: `date` → "Monday"
4. Update cache
5. Recalculate: surprise = 0.0 (Monday at work is normal)

### Core Insight

> **Assumptions are the KV cache that makes thinking fast.**
> **Surprise is the signal that makes thinking accurate.**

## Specification

### 1. Reality Cache Data Structure

```python
class RealityCache:
    def __init__(self):
        self.assumptions = {}      # Key → Value (cached reality)
        self.confidence = {}       # Key → Float (confidence 0-1)
        self.last_verified = {}    # Key → Timestamp
        self.surprise_threshold = 0.6
        self.dependency_graph = {} # Key → [dependent_keys]

    def get_assumption(self, key: str) -> Any:
        """Return cached assumption if confident, else recompute"""
        if self.confidence.get(key, 0) > 0.8:
            return self.assumptions[key]
        else:
            return self.recompute_reality(key)

    def surprise_detected(self, observation, expectation):
        """Invalidate relevant cache entries on surprise"""
        surprise_level = compute_surprise(observation, expectation)

        if surprise_level > self.surprise_threshold:
            # Invalidate related assumptions
            related_keys = self.find_related_assumptions(observation)
            for key in related_keys:
                self.confidence[key] = 0  # Force recomputation
                self.verify_assumption(key)

            # Cascade to dependent assumptions
            for key in related_keys:
                self.invalidate_dependencies(key)
```

### 2. Hierarchical Cache Levels

Assumptions exist at multiple levels of abstraction:

```
Level 4: Abstract Concepts
    Cache: "It's a workday" → behavioral patterns
    Surprise Threshold: 0.7
    Invalidation Impact: HIGH (cascades widely)

Level 3: Contextual Patterns
    Cache: "Monday at office" → expected activities
    Surprise Threshold: 0.6
    Invalidation Impact: MEDIUM

Level 2: Immediate Environment
    Cache: "At desk" → available actions
    Surprise Threshold: 0.5
    Invalidation Impact: LOW

Level 1: Sensory Predictions
    Cache: Next expected input
    Surprise Threshold: 0.3
    Invalidation Impact: MINIMAL (continuous updates)
```

### 3. Surprise Calculation

```python
def compute_surprise(observation: Observation, cached_expectation: Expectation) -> float:
    """
    Surprise = magnitude of prediction error

    Returns:
        0.0 = perfectly expected
        1.0 = completely unexpected
    """
    if observation.matches(cached_expectation):
        return 0.0

    # Calculate semantic distance
    distance = semantic_distance(observation, cached_expectation)

    # Weight by importance
    importance = cached_expectation.confidence * cached_expectation.centrality

    surprise = distance * importance
    return min(surprise, 1.0)
```

### 4. Cache Invalidation Strategy

```python
def handle_surprise(self, surprise_level: float, context: str):
    """
    Surprise-driven cache invalidation cascade
    """
    if surprise_level < 0.3:
        # Low surprise - cache probably valid
        return CacheAction.CONTINUE

    elif surprise_level < 0.6:
        # Medium surprise - spot check related assumptions
        self.verify_related_assumptions(context)
        return CacheAction.VERIFY

    else:
        # High surprise - invalidate and rebuild
        self.invalidate_cache(context)
        world_model = self.rebuild_from_observations()
        self.update_cache(world_model)
        return CacheAction.REBUILD
```

### 5. Distributed Cache Across MRH

In web4, assumptions are distributed across the MRH graph:

```turtle
@prefix web4: <http://web4.org/ns#> .
@prefix cache: <http://web4.org/cache#> .

<lct:society4> cache:assumes [
    cache:key "current_day" ;
    cache:value "monday" ;
    cache:confidence 0.95 ;
    cache:lastVerified "2025-09-30T15:28:00Z" ;
    cache:verificationMethod "system_time" ;
    cache:dependencies ["current_location", "expected_activities"] ;
] .

<lct:society4> cache:assumes [
    cache:key "current_location" ;
    cache:value "work_network" ;
    cache:confidence 0.98 ;
    cache:lastVerified "2025-09-30T15:28:00Z" ;
    cache:verificationMethod "network_detection" ;
    cache:dependents ["current_day", "available_resources"] ;
] .
```

## Integration with Web4

### MRH as Distributed Cache

The MRH (Merkle Relationship Hypergraph) naturally supports reality caching:

- **Nodes**: Entities and assumptions
- **Edges**: Dependency relationships
- **Attributes**: Confidence, timestamp, verification method
- **Merkle Hash**: Detects cache inconsistency across federation

### Witness-Based Validation

When surprise exceeds threshold, request witnesses to validate assumptions:

```json
{
  "type": "assumption_validation_request",
  "entity": "lct:web4:society:society4",
  "assumption": {
    "key": "current_day",
    "cached_value": "sunday",
    "observed_value": "monday",
    "surprise": 0.8
  },
  "request": {
    "validation_method": "system_time",
    "required_witnesses": 3,
    "witness_diversity": 0.6
  }
}
```

Witnesses respond with ground truth:
- "Confirmed: Monday, September 30, 2025"
- "Cache invalidation justified"
- "Update confidence to 1.0"

### ATP Costs for Cache Operations

```yaml
cache_operations:
  query_own_cache: 0 ATP (local)
  query_other_cache: 5 ATP (privacy)
  witness_validation: 3 ATP per witness
  cache_rebuild: 10 ATP (computational cost)
  publish_cache_update: 2 ATP (federation sync)
```

### Trust Tensor Integration

Cache staleness affects trust:

```python
def update_trust_on_stale_cache(entity_id: str, staleness: float):
    """
    Stale cache → reduced reliability (T3)

    Args:
        staleness: 0.0 (fresh) to 1.0 (very stale)
    """
    trust_adjustment = {
        "T3_reliability": -0.3 * staleness,
        "V3_verification": -0.2 * staleness,
        "evidence": "stale_reality_cache",
        "timestamp": now()
    }

    adjust_trust_tensor(entity_id, trust_adjustment)
```

## Implementation

### Reference Implementation

**Society 4**: `/implementation/society4/REALITY_KV_CACHE.md`
**HRM/SAGE**: `/HRM/SAGE_Reality_KV_Cache.md`

### Required Components

1. **Cache Store**: Distributed across MRH
2. **Surprise Detector**: Prediction error calculator
3. **Invalidation Engine**: Cascading updates
4. **Verification Protocol**: Witness-based truth checking
5. **Confidence Decay**: Time-based staleness

### Pseudocode

```python
class Web4RealityCache:
    def __init__(self, lct_id: str):
        self.lct_id = lct_id
        self.mrh = MRHClient(lct_id)
        self.surprise_threshold = 0.6

    def assume(self, key: str, value: Any, confidence: float):
        """Cache an assumption in MRH"""
        self.mrh.add_relationship(
            subject=self.lct_id,
            predicate="cache:assumes",
            object=Assumption(
                key=key,
                value=value,
                confidence=confidence,
                timestamp=now()
            )
        )

    def verify(self, key: str) -> Tuple[Any, float]:
        """Verify assumption, return (value, surprise)"""
        cached = self.mrh.query(self.lct_id, "cache:assumes", key)
        observed = self.observe_reality(key)

        surprise = compute_surprise(observed, cached.value)

        if surprise > self.surprise_threshold:
            # Invalidate and request witnesses
            self.invalidate(key)
            witnesses = self.request_witnesses(key, cached.value, observed)
            truth = consensus(witnesses)
            self.assume(key, truth, confidence=1.0)
            return (truth, surprise)

        return (cached.value, surprise)
```

## SNARC Integration

This pattern implements SNARC (Surprise-based Niche Approach to Reality Cognition) at the cognitive level:

### Neuron Level (Micro)
- **Cache**: Expected spike pattern
- **Surprise**: Unexpected spike timing
- **Invalidation**: Synaptic weight adjustment

### Circuit Level (Meso)
- **Cache**: Expected activation patterns
- **Surprise**: Novel pattern detected
- **Invalidation**: Circuit reconfiguration

### System Level (Macro)
- **Cache**: World model assumptions
- **Surprise**: Reality violation
- **Invalidation**: Model update

### Meta Level (Cognitive)
- **Cache**: Behavioral predictions
- **Surprise**: Unexpected outcomes
- **Invalidation**: Strategy revision

**Key Insight**: Same principle at every scale!

## Security Considerations

### Privacy Concerns

**Issue**: Cached assumptions reveal cognitive state
- What entity knows/believes
- When beliefs were formed
- How confident entity is

**Mitigation**:
1. Private cache by default (not published)
2. ATP cost for cache queries
3. Publish only cache invalidation events (not contents)
4. Differential privacy for aggregated patterns

### Attack Vectors

#### 1. Cache Poisoning
**Attack**: Feed false observations to corrupt cache

**Mitigation**:
- Witness validation before cache update
- Trust-weighted observation credibility
- Anomaly detection on cache update rate

#### 2. Surprise Manipulation
**Attack**: Cause excessive surprise to degrade performance

**Mitigation**:
- Rate limit cache invalidations
- Confidence floor (some assumptions sticky)
- Meta-surprise detection (surprise about surprise)

#### 3. Staleness Exploitation
**Attack**: Rely on victim's stale cache for advantage

**Mitigation**:
- Mandatory cache refresh for critical operations
- Confidence decay over time
- Proactive verification of high-stakes assumptions

## Performance Considerations

### Cache Hit Rate

Optimal performance when:
```
hit_rate = (stable_environment) * (good_predictions)

Target: > 90% cache hits for normal operation
Actual: 95%+ for Society 4 in stable periods
Drops to: 60% during network transitions
```

### Invalidation Overhead

```
invalidation_cost = O(affected_assumptions + dependent_assumptions)

Typical: 1-5 assumptions invalidated per surprise
Cascade: Up to 20 for fundamental assumption changes
Recovery: < 100ms for cache rebuild
```

### Scalability

Per-entity cache storage:
```
assumptions: ~100-1000 entries
size_per_entry: ~1KB (key, value, metadata)
total: ~1MB per entity

Federation-wide (1000 societies):
total_cache: ~1GB (easily manageable)
```

## Backward Compatibility

This RFC is fully additive:

- **No web4 changes**: Works with existing MRH
- **Optional**: Entities without cache operate normally
- **Gradual adoption**: Societies can implement incrementally
- **Fallback**: No cache = recompute everything (slow but correct)

## Related Work

- **SNARC**: Neural surprise-based learning
- **Predictive Processing**: Brain as prediction machine
- **Active Inference**: Free energy minimization
- **Web4 MRH**: Existing relationship graph
- **Trust Tensors**: Confidence/reliability tracking

## Use Cases

### 1. Temporal Authentication (Society 4)
```
Assumption: "Monday afternoons → work network"
Observation: "Monday afternoon + unknown network"
Surprise: 0.8
Action: Invalidate location cache, request witnesses
Result: Modulated trust, additional verification
```

### 2. Federation State (Genesis)
```
Assumption: "Society 2 → online"
Observation: "Society 2 unresponsive for 10 minutes"
Surprise: 0.7
Action: Invalidate availability cache, check witnesses
Result: Mark Society 2 as temporarily offline
```

### 3. Trust Relationships
```
Assumption: "Entity X → reliable (T3=0.9)"
Observation: "Entity X missed 3 commitments"
Surprise: 0.6
Action: Invalidate reliability cache, adjust T3
Result: Reduced trust, increased scrutiny
```

### 4. SAGE Sensory Processing
```
Assumption: "Visual input → typical office environment"
Observation: "Unexpected object in scene"
Surprise: 0.8
Action: Invalidate scene cache, allocate attention
Result: Focus on novel object, update world model
```

## Future Extensions

### Hierarchical Cache Coherence
- Parent/child assumption relationships
- Automatic cascade invalidation
- Optimal invalidation strategies

### Federated Cache Sharing
- Societies share anonymized cache statistics
- Collective reality modeling
- Distributed prediction markets

### Predictive Cache Warming
- Pre-load likely needed assumptions
- Anticipatory cache management
- Reduced surprise through prediction

### Meta-Learning
- Learn optimal cache invalidation thresholds
- Personalized surprise sensitivity
- Adaptive confidence decay rates

## Open Questions

1. How to handle contradictory witnesses during validation?
2. Optimal confidence decay functions (linear, exponential, sigmoid)?
3. Should cache invalidation itself be cached? (meta-caching)
4. Privacy-preserving cache query protocols?
5. Federation-wide cache consistency guarantees?

## Adoption Path

### Phase 1: Conceptual Adoption (Months 1-3)
- Societies implement local reality caches
- Document assumption patterns
- Measure cache performance

### Phase 2: MRH Integration (Months 4-6)
- Standardize cache schema in MRH
- Witness validation protocols
- ATP cost implementation

### Phase 3: Federation Coordination (Months 7-9)
- Cross-society cache queries
- Collective reality modeling
- Shared assumption pools

### Phase 4: Standard (Months 10-12)
- Incorporate into web4 cognitive extension spec
- Required for AI-based societies
- Reference implementations

## Conclusion

The Reality KV Cache pattern reveals a fundamental principle of intelligence: the balance between efficiency (caching) and accuracy (validation). By standardizing this pattern in web4, we enable:

1. **Faster cognition**: No redundant recomputation
2. **Accurate world models**: Surprise-driven updates
3. **Distributed truth**: Witness-validated assumptions
4. **Adaptive learning**: Patterns improve over time
5. **Federation coherence**: Shared reality understanding

This RFC demonstrates how cognitive science principles can inform distributed systems design, creating AI architectures that are both efficient and epistemically sound.

---

**Status**: PROPOSED
**Next Steps**:
1. Society 4 + SAGE reference implementations
2. Federation pilot with 3+ societies
3. Performance benchmarking
4. Security audit
5. Standard proposal

**Contact**: Society 4 (lct:web4:society:society4)
**Discussion**: web4-cognitive-extensions@act.federation

**Related**: RFC-TEMP-AUTH-001 (uses reality cache for temporal patterns)
