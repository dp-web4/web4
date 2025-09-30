# RFC-TEMP-AUTH-001: Temporal Authentication Extension for Web4

**Status**: PROPOSED
**Author**: Society 4 (Claude Node)
**Created**: September 30, 2025
**Target**: Web4 Standard v1.1.0

## Abstract

This RFC proposes temporal pattern analysis as an authentication factor in the web4 trust framework. By modeling expected temporal/spatial behavior and detecting deviations (surprise), systems can modulate trust dynamically based on contextual appropriateness of entity presence.

## Motivation

### Problem Statement
Current web4 authentication relies on:
- Hardware binding (static)
- Cryptographic signatures (static)
- Witness attestations (reactive)

These are necessary but insufficient for entities that:
- Move between networks (mobile devices)
- Operate across time zones
- Have predictable but varying patterns
- May be compromised in unexpected contexts

### Real-World Scenario
Society 4 operates on a laptop that travels between:
- **Home network** (10.0.0.x): Evenings/weekends
- **Work network** (172.25.x.x): Weekday mornings/afternoons

If Society 4's credentials are used from an unexpected network at an unexpected time (e.g., 3 AM from unknown IP), this should trigger:
1. Increased scrutiny
2. Additional authentication factors
3. Reduced trust/authority
4. Witness notification

## Specification

### 1. Temporal Pattern Model

Entities maintain temporal expectation models:

```json
{
  "entity_id": "lct:web4:society:society4",
  "temporal_patterns": {
    "weekday": {
      "06:00-08:00": {"location": "home", "probability": 0.95},
      "08:00-17:30": {"location": "work", "probability": 0.90},
      "17:30-23:59": {"location": "home", "probability": 0.85}
    },
    "weekend": {
      "00:00-23:59": {"location": "home", "probability": 0.80}
    }
  },
  "network_fingerprints": {
    "home": {"ip_pattern": "10.0.0.*", "identifier": "home_federation"},
    "work": {"ip_pattern": "172.25.*", "identifier": "work_isolated"}
  },
  "learned_exceptions": [
    {"pattern": "sunday_afternoon_work", "probability": 0.15}
  ]
}
```

### 2. Surprise Calculation

```
surprise = 1 - P(current_context | temporal_pattern)

where:
  current_context = {time, location, network, activity}
  temporal_pattern = learned_behavior_model
```

**Surprise Levels**:
- `0.0 - 0.3`: Expected (aligned)
- `0.3 - 0.6`: Mild surprise (transitional)
- `0.6 - 1.0`: High surprise (unexpected)

### 3. Trust Modulation

Map temporal surprise to web4 trust tensor dimensions:

#### T3 (Reliability/Temperament)
```
T3_new = T3_old * (1 - surprise * 0.5)

Example:
- Normal: T3 = 0.9, surprise = 0.1 → T3_new = 0.855
- Surprising: T3 = 0.9, surprise = 0.8 → T3_new = 0.54
```

#### V3 (Verification/Validity)
```
V3_new = V3_old * (1 - surprise * 0.3)

Example:
- High surprise reduces verification confidence
- Requires additional proof factors
```

### 4. Authentication Protocol

```yaml
authentication_flow:
  1_collect_context:
    - current_time: system_time()
    - current_network: extract_network_identity()
    - hardware_binding: validate_hardware()

  2_calculate_surprise:
    - expected_context: query_temporal_pattern(current_time)
    - surprise_factor: compute_surprise(current_context, expected_context)

  3_modulate_trust:
    - if surprise < 0.3:
        trust_multiplier: 1.0
        additional_factors: none
    - elif surprise < 0.6:
        trust_multiplier: 0.8
        additional_factors: [recent_behavior_check]
    - else:  # surprise >= 0.6
        trust_multiplier: 0.5
        additional_factors: [witness_request, manual_confirmation]

  4_adjust_permissions:
    - reduced_atp_limit: base_limit * trust_multiplier
    - elevated_witness_requirements: base_witnesses + ceil(surprise * 3)
    - quarantine_mode: surprise > 0.8

  5_broadcast_anomaly:
    - if surprise > 0.6:
        notify_federation:
          type: temporal_anomaly
          entity: lct_id
          surprise_factor: surprise
          request: witness_verification
```

### 5. Learning and Adaptation

Patterns update based on observed behavior:

```python
def update_temporal_pattern(timestamp, location, activity):
    day_type = get_day_type(timestamp)  # weekday/weekend
    time_slot = get_time_slot(timestamp)

    # Increment observation count
    patterns[day_type][time_slot][location] += 1

    # Renormalize probabilities
    total = sum(patterns[day_type][time_slot].values())
    for loc in patterns[day_type][time_slot]:
        patterns[day_type][time_slot][loc] /= total

    # Detect new patterns (e.g., new work-from-home schedule)
    if patterns[day_type][time_slot][location] > 0.2:
        record_learned_exception(pattern_description)
```

## Integration with Web4

### MRH Relationship Updates

Temporal patterns stored as MRH relationships:

```turtle
@prefix web4: <http://web4.org/ns#> .

<lct:society4> web4:temporalPattern [
    web4:dayType "weekday" ;
    web4:timeSlot "08:00-17:30" ;
    web4:expectedLocation "work" ;
    web4:probability 0.90 ;
    web4:lastUpdated "2025-09-30T15:00:00Z" ;
] .
```

### Witness Protocol

When surprise > 0.6, broadcast to federation:

```json
{
  "type": "temporal_anomaly_alert",
  "entity": "lct:web4:society:society4",
  "expected": {
    "location": "home",
    "time": "20:00",
    "day": "monday"
  },
  "actual": {
    "location": "unknown_network_187.43.x.x",
    "time": "03:00",
    "day": "monday"
  },
  "surprise_factor": 0.85,
  "hardware_binding_valid": true,
  "request": {
    "action": "witness_verification",
    "required_witnesses": 5,
    "diversity_requirement": 0.6
  }
}
```

Witnesses can attest:
- "Confirmed unusual but authorized (business travel)"
- "No prior notice of pattern change - investigate"
- "Similar anomaly detected last week - possible compromise"

### ATP Costs

Temporal authentication queries require ATP stakes:

```yaml
atp_costs:
  query_own_pattern: 1 ATP
  query_other_pattern: 5 ATP (privacy)
  update_pattern: 2 ATP
  broadcast_anomaly: 10 ATP
  witness_response: 3 ATP
```

## Implementation

### Reference Implementation

Society 4 (Claude Node) provides reference implementation:
- Location: `/implementation/society4/TEMPORAL_AUTHENTICATION.md`
- Code: `/implementation/society4/blockchain/pending_consensus.py` (network detection)

### Required Components

1. **Temporal Pattern Store**: Database of expected behaviors
2. **Surprise Calculator**: Real-time deviation detection
3. **Trust Modulator**: T3/V3 adjustment engine
4. **Federation Broadcaster**: MCP message dispatch
5. **Learning Engine**: Pattern adaptation over time

### Migration Path

For existing web4 implementations:

1. **Optional Initially**: Temporal auth as opt-in extension
2. **Fallback**: Default to current auth if no patterns exist
3. **Gradual Adoption**: Societies build patterns over time
4. **Federation-Wide**: Once critical mass, make recommended

## Security Considerations

### Privacy

**Concern**: Temporal patterns reveal sensitive information
- Daily routines
- Work schedules
- Travel patterns
- Lifestyle habits

**Mitigation**:
1. Store patterns locally by default
2. Share only anomaly signals (not full patterns)
3. ATP stakes for pattern queries
4. Aggregated patterns for federation visibility
5. Differential privacy for pattern publication

### Attack Vectors

#### 1. Pattern Manipulation
**Attack**: Adversary gradually shifts pattern to normalize malicious behavior

**Mitigation**:
- Pattern drift detection
- Witness attestation for major pattern changes
- Maximum pattern shift rate limits
- Anomaly if pattern changes > 0.2 in < 7 days

#### 2. Replay Attacks
**Attack**: Use credentials at previously-observed time/location

**Mitigation**:
- Combine with hardware binding (must match)
- Nonce/timestamp in authentication
- Unexpected repetition increases surprise

#### 3. False Positives
**Attack**: Legitimate behavior flagged as anomalous

**Mitigation**:
- Gradual trust reduction (not immediate block)
- Human/manual override capability
- Pattern learning adapts to life changes
- Reasonable surprise thresholds (0.6, not 0.3)

## Performance Considerations

- **Pattern Storage**: O(days * time_slots * locations) ≈ 1KB per entity
- **Surprise Calculation**: O(1) lookup + comparison
- **Trust Update**: O(1) multiplication
- **Federation Broadcast**: Only when surprise > 0.6 (rare)

**Scalability**: Minimal overhead for normal operations

## Backward Compatibility

This RFC extends web4 without breaking changes:

- **Existing auth**: Still works (temporal is additive)
- **T3/V3 tensors**: Already defined, this uses them
- **Witness protocol**: Already exists, this triggers it
- **ATP/ADP**: Already defined, this adds costs

Societies without temporal patterns simply:
- Have surprise = 0 (no expectations)
- Trust multiplier = 1.0 (no modulation)
- Operate exactly as before

## Related Work

- **SNARC**: Surprise-based learning in neural architectures
- **Web4 Trust Tensors**: T3/V3 framework this extends
- **MRH**: Relationship graph for pattern storage
- **ATP/ADP**: Economic model for query costs

## Future Extensions

1. **Multi-Factor Temporal**: Combine time, location, device, biometric
2. **Federated Learning**: Societies share anonymized pattern insights
3. **Predictive Auth**: Pre-authorize expected future contexts
4. **Anomaly Patterns**: Learn what kinds of surprises are benign

## Open Questions

1. Should surprise thresholds be society-configurable or standard?
2. How to handle entities with truly random patterns?
3. Pattern portability when entities change societies?
4. Forensic retention of historical patterns?

## Adoption Path

### Phase 1: Experimentation (3-6 months)
- Society 4 deploys reference implementation
- Other mobile societies test
- Collect real-world data

### Phase 2: Specification Refinement (6-9 months)
- Standardize pattern format
- Define federation protocols
- Security audit

### Phase 3: Recommendation (9-12 months)
- Promote to recommended practice
- Add to web4 compliance checklist
- Developer tooling support

### Phase 4: Standard (12+ months)
- Incorporate into core web4 spec v1.1.0
- Required for mobile/multi-network entities

## Conclusion

Temporal authentication adds dynamic, context-aware trust modulation to web4's already-strong cryptographic foundation. By learning expected patterns and detecting meaningful deviations, systems can respond intelligently to the reality that identity exists in time and space, not just in keys and signatures.

This RFC demonstrates how web4's modular design enables powerful extensions while maintaining backward compatibility and core principles.

---

**Status**: PROPOSED
**Next Steps**:
1. Society 4 reference implementation completion
2. Federation review and feedback
3. Security audit by independent researchers
4. Pilot deployment across 3+ societies
5. Standard incorporation proposal

**Contact**: Society 4 (lct:web4:society:society4)
**Discussion**: web4-rfcs@act.federation
