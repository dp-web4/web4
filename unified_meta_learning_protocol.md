# Unified Meta-Learning Protocol

**Date:** 2026-01-10
**Platforms:** Legion + Thor
**Purpose:** Cross-platform meta-learning integration
**Status:** Protocol Specification

## Executive Summary

Legion Sessions 160-162 and Thor Session 181 independently implemented meta-learning for their respective verification architectures. This protocol defines unified storage formats, pattern schemas, and integration mechanisms to enable:

1. **Cross-platform learning**: Legion learns from Thor patterns, Thor from Legion
2. **Shared insights**: Common understanding of optimal depths, modes, strategies
3. **Network-wide optimization**: Collective intelligence faster than individual
4. **Compatible evolution**: Both platforms can evolve independently while maintaining interoperability

## Architecture Convergence

### Legion Meta-Learning Stack

```
Session 160: Meta-Learning from Verification History
├─ VerificationPattern dataclass
├─ LearningInsight extraction
├─ Learned depth selection (70% learning, 30% exploration)
└─ Pattern analysis (5 insight types)

Session 161: Persistent Meta-Learning
├─ PersistentMetaLearning storage class
├─ JSON pattern/insight storage
├─ Cross-session learning accumulation
└─ Session count tracking

Session 162: Reputation-Aware Meta-Learning
├─ NodeReputation integration
├─ Learning weight from reputation (0.5x - 2.0x)
├─ Confidence bonuses (+/-20%)
└─ Epistemic confidence hierarchy
```

### Thor Meta-Learning Stack

```
Session 181: Meta-Learning Adaptive Depth
├─ DepthVerificationPattern dataclass
├─ PersistentMetaLearningManager
├─ JSONL append-only pattern log
├─ JSON aggregated insights
├─ MetaLearningAdaptiveSAGE (complete stack)
└─ Confidence-based strategy (50% threshold)
```

## Unified Pattern Schema

### Core Pattern Fields (Required)

```json
{
  "pattern_id": "string (uuid)",
  "node_id": "string (lct_id)",
  "timestamp": "float (unix time)",
  "platform": "string (legion|thor)",

  "depth_used": "string (minimal|light|standard|deep|thorough)",
  "mode": "string (cogitation mode)",

  "quality_achieved": "float (0.0-1.0)",
  "success": "boolean",

  "atp_before": "float",
  "atp_after": "float",

  "reputation_before": "float (optional)",
  "reputation_after": "float (optional)",

  "context": "object (platform-specific)"
}
```

### Legion-Specific Extensions

```json
{
  "cogitation_mode": "string (VERIFYING|EXPLORING|INTEGRATING|etc)",
  "outcome_confidence": "float (0.0-1.0)",
  "verification_quality_score": "float"
}
```

### Thor-Specific Extensions

```json
{
  "cognitive_depth": "string (SAGE depth levels)",
  "network_health": "float (0.0-1.0)",
  "federation_context": "object (peers, network state)"
}
```

## Storage Format Specification

### Pattern Storage: JSONL (JSON Lines)

**Why JSONL:**
- Append-only for performance
- Easy streaming/incremental reading
- Robust to corruption (line-by-line recovery)
- Standard format with tooling support

**File Structure:**
```
{storage_dir}/{node_id}_patterns.jsonl
```

**Example:**
```jsonl
{"pattern_id":"p1","node_id":"legion","timestamp":1704902400.0,"depth_used":"standard","quality_achieved":0.45,"success":true,"atp_before":100.0,"atp_after":95.0}
{"pattern_id":"p2","node_id":"thor","timestamp":1704902460.0,"depth_used":"deep","quality_achieved":0.52,"success":true,"atp_before":120.0,"atp_after":110.0}
```

### Insight Storage: JSON

**Why JSON:**
- Aggregated state (not append-only)
- Human-readable for debugging
- Easy schema evolution

**File Structure:**
```
{storage_dir}/{node_id}_insights.json
```

**Schema:**
```json
{
  "version": "1.0",
  "node_id": "string",
  "platform": "string",
  "last_updated": "float",
  "pattern_count": "int",
  "insights": [
    {
      "insight_type": "string",
      "description": "string",
      "evidence_count": "int",
      "confidence": "float (0.0-1.0)",
      "recommendation": "string",
      "learned_at": "float"
    }
  ],
  "depth_performance": {
    "minimal": {"avg_quality": 0.3, "success_rate": 0.7, "sample_count": 10},
    "standard": {"avg_quality": 0.45, "success_rate": 0.9, "sample_count": 25}
  },
  "learned_preferences": {
    "optimal_quality_depth": "standard",
    "optimal_success_depth": "standard",
    "optimal_atp_depth": "light"
  }
}
```

## Cross-Platform Learning Protocol

### Pattern Exchange

**Goal:** Nodes share learned patterns to accelerate collective learning

**Protocol:**

1. **Pattern Announcement** (Multicast)
```json
{
  "type": "pattern_announcement",
  "from_node": "lct:web4:tpm2:legion",
  "pattern_count": 50,
  "patterns_hash": "sha256_of_recent_patterns",
  "depth_distribution": {"minimal": 5, "standard": 30, "deep": 15}
}
```

2. **Pattern Request** (Unicast)
```json
{
  "type": "pattern_request",
  "from_node": "lct:web4:trustzone:thor",
  "request_filters": {
    "depths": ["standard", "deep"],
    "min_quality": 0.4,
    "min_timestamp": 1704900000.0,
    "max_count": 100
  }
}
```

3. **Pattern Response** (Unicast)
```json
{
  "type": "pattern_response",
  "from_node": "lct:web4:tpm2:legion",
  "patterns": [
    {
      "pattern_id": "...",
      "signature": "lct_attestation_signature",
      ...pattern fields...
    }
  ]
}
```

**Security:** All patterns must include LCT attestation signature (Session 163)

### Insight Sharing

**Goal:** Share aggregated insights without raw pattern exposure

**Protocol:**

1. **Insight Broadcast** (Multicast)
```json
{
  "type": "insight_broadcast",
  "from_node": "lct:web4:tpm2:legion",
  "insights": [
    {
      "insight_type": "optimal_depth",
      "description": "Standard depth best for quality (0.45 avg)",
      "confidence": 0.9,
      "evidence_count": 50,
      "signature": "lct_attestation"
    }
  ]
}
```

**Trust Integration:** Insights weighted by source node's reputation (Session 162)

## Federated Meta-Learning Architecture

### Learning Hierarchy

```
Individual Learning (Sessions 160/161/181)
    ↓
    Individual patterns → Local insights
    ↓
Peer Learning (Pattern Exchange)
    ↓
    Shared patterns → Cross-node insights
    ↓
Network Learning (Insight Aggregation)
    ↓
    Collective insights → Network-wide optimization
```

### Reputation-Weighted Learning (Session 162 Extension)

**Principle:** High-reputation nodes contribute more to collective learning

**Implementation:**

```python
def aggregate_federated_insights(
    local_insights: List[Insight],
    peer_insights: Dict[str, List[Insight]],  # node_id -> insights
    reputation_manager: ReputationManager
) -> List[Insight]:
    """
    Aggregate insights across federation with reputation weighting.
    """
    aggregated = defaultdict(list)

    # Local insights (own reputation weight)
    local_rep = reputation_manager.get_reputation(self.node_id)
    local_weight = local_rep.learning_weight  # 0.5x - 2.0x

    for insight in local_insights:
        aggregated[insight.insight_type].append({
            'insight': insight,
            'weight': local_weight,
            'source': 'local'
        })

    # Peer insights (peer reputation weight)
    for peer_id, insights in peer_insights.items():
        peer_rep = reputation_manager.get_reputation(peer_id)
        peer_weight = peer_rep.learning_weight

        for insight in insights:
            aggregated[insight.insight_type].append({
                'insight': insight,
                'weight': peer_weight,
                'source': peer_id
            })

    # Weighted aggregation
    final_insights = []
    for insight_type, weighted_insights in aggregated.items():
        # Compute weighted average confidence
        total_weight = sum(wi['weight'] for wi in weighted_insights)
        weighted_conf = sum(
            wi['insight'].confidence * wi['weight']
            for wi in weighted_insights
        ) / total_weight

        # Combine descriptions
        descriptions = [wi['insight'].description for wi in weighted_insights]

        final_insights.append(Insight(
            insight_type=insight_type,
            description=f"Collective: {descriptions[0]} (+ {len(descriptions)-1} peers)",
            confidence=weighted_conf,
            evidence_count=sum(wi['insight'].evidence_count for wi in weighted_insights),
            sources=[wi['source'] for wi in weighted_insights]
        ))

    return final_insights
```

## Implementation Roadmap

### Phase 1: Storage Unification (This Session)

- [x] Define unified pattern schema
- [x] Specify JSONL/JSON storage format
- [ ] Implement Legion → JSONL converter
- [ ] Implement Thor → unified format validator
- [ ] Test cross-platform pattern loading

### Phase 2: Pattern Exchange (Next Session)

- [ ] Implement pattern announcement protocol
- [ ] Implement pattern request/response
- [ ] Add LCT attestation to patterns
- [ ] Test Legion ↔ Thor pattern exchange

### Phase 3: Federated Insights (Future)

- [ ] Implement insight broadcast protocol
- [ ] Add reputation weighting
- [ ] Network-wide insight aggregation
- [ ] Test collective optimization speed

### Phase 4: Production Hardening (Future)

- [ ] Add pattern validation
- [ ] Implement insight conflict resolution
- [ ] Byzantine fault tolerance
- [ ] Performance optimization at scale

## Security Considerations

### Pattern Authenticity (Critical)

**Threat:** Malicious nodes inject fake patterns to poison learning

**Defense:** All patterns must include LCT attestation (Session 163)
```python
def verify_pattern_authenticity(pattern: Dict, lct_manager: LCTReputationManager) -> bool:
    signature = pattern.get('signature')
    node_id = pattern.get('node_id')

    if not signature or not node_id:
        return False

    # Verify LCT attestation
    lct_identity = lct_manager.get_lct_identity(node_id)
    if not lct_identity:
        return False

    # Reconstruct pattern data for verification
    pattern_data = json.dumps(pattern, sort_keys=True)

    return lct_identity.verify_attestation(signature, pattern_data)
```

### Insight Trust (Session 162)

**Threat:** Low-reputation nodes inject biased insights

**Defense:** Weight insights by source reputation
- Excellent reputation (50+): 2.0x weight
- Untrusted (<-20): 0.5x weight
- Result: Low-rep insights have minimal impact

### Sybil Pattern Flooding

**Threat:** Attacker creates many Sybils to flood fake patterns

**Defense:** Sybil resistance from Session 163
- Hardware cost makes large-scale Sybil expensive
- Pattern count limits per node
- Reputation decay for low-quality patterns

## Biological Validation

### Collective Learning in Nature

**Ant Colonies:**
- Individual ants leave pheromone trails (patterns)
- Stronger trails from successful paths (reputation)
- Colony converges on optimal routes (collective insight)
- **Computational parallel:** Pattern exchange with reputation weighting ✅

**Neural Networks (Brain):**
- Individual neurons learn local patterns
- Synaptic strength represents "reputation" of connections
- Network-wide learning through backpropagation
- **Computational parallel:** Federated meta-learning with epistemic confidence ✅

**Scientific Communities:**
- Individual researchers publish findings (patterns)
- Peer review establishes credibility (reputation)
- Meta-analyses aggregate trusted research (collective insight)
- **Computational parallel:** Insight sharing with LCT attestation ✅

## Test Plan

### Unit Tests

1. Pattern serialization/deserialization
2. JSONL append performance
3. Insight aggregation correctness
4. Reputation weighting accuracy

### Integration Tests

1. Legion → Thor pattern exchange
2. Thor → Legion insight sharing
3. Collective learning convergence
4. Security: Fake pattern rejection

### Performance Tests

1. Pattern storage scaling (1M+ patterns)
2. Insight computation performance
3. Network bandwidth (pattern exchange)
4. Learning convergence speed (individual vs collective)

### Security Tests

1. Unauthenticated pattern rejection
2. Sybil pattern flooding resistance
3. Low-reputation insight filtering
4. Byzantine node tolerance

## Convergence Success Metrics

### Individual → Collective Learning Speed

**Hypothesis:** Collective learning converges faster than individual

**Measurement:**
- Individual: Time to 90% confidence on optimal depth
- Collective: Time to 90% confidence with pattern sharing
- **Target:** 2-3x faster convergence

### Reputation Impact on Learning Quality

**Hypothesis:** Reputation weighting improves insight accuracy

**Measurement:**
- Unweighted insights accuracy (baseline)
- Reputation-weighted insights accuracy
- **Target:** 10-20% accuracy improvement

### Cross-Platform Compatibility

**Hypothesis:** Legion and Thor can share patterns without loss

**Measurement:**
- Pattern schema validation rate
- Insight reconstruction accuracy
- **Target:** 100% compatibility

## Status

**Protocol:** ✅ DEFINED
**Implementation:** In Progress
**Phase 1:** 50% complete (schema defined, storage specified)

**Next Steps:**
1. Implement Legion → JSONL converter
2. Validate Thor Session 181 patterns conform to schema
3. Test cross-platform pattern loading
4. Implement pattern exchange protocol

---

**Convergence Achievement:** Unified meta-learning architecture enables Legion + Thor to learn collectively, accelerating network-wide optimization while maintaining platform independence.
