# Web4 Reputation Computation Specification

## Overview

This document specifies how reputation changes are computed in Web4's R7 framework. Reputation is not a simple score—it's a **multi-dimensional delta** capturing trust and value changes across multiple axes, with explicit attribution, witnessing, and contributing factors.

## Fundamental Principle

**In Web4, trust is not a side effect—it's the product.**

Every R7 transaction produces:
1. **Result**: The immediate outcome (data, status, resources consumed)
2. **Reputation**: The trust/value impact (T3/V3 deltas with attribution)

This separation makes trust mechanics **observable, attributable, and verifiable**.

## 1. Reputation Delta Structure

### Complete Schema

```json
{
  "reputation": {
    "subject_lct": "lct:web4:entity:...",
    "role_lct": "lct:web4:role:...",
    "role_pairing_in_mrh": {
      "entity": "lct:web4:entity:...",
      "role": "lct:web4:role:...",
      "paired_at": "2025-XX-XXT...",
      "mrh_link": "link:mrh:entity→role:..."
    },
    "action_type": "action_verb",
    "action_target": "resource:...",
    "action_id": "txn:0x...",
    "rule_triggered": "rule_identifier",
    "reason": "Human-readable explanation",

    "t3_delta": {
      "talent": {"change": +0.01, "from": 0.85, "to": 0.86},
      "training": {"change": +0.02, "from": 0.90, "to": 0.92},
      "temperament": {"change": +0.005, "from": 0.88, "to": 0.885}
    },

    "v3_delta": {
      "veracity": {"change": +0.01, "from": 0.80, "to": 0.81},
      "validity": {"change": 0.0, "from": 1.0, "to": 1.0},
      "value": {"change": +0.005, "from": 0.75, "to": 0.755}
    },

    "contributing_factors": [
      {"factor": "accuracy_threshold_exceeded", "weight": 0.5},
      {"factor": "deadline_met", "weight": 0.3},
      {"factor": "resource_efficiency", "weight": 0.2}
    ],

    "witnesses": [
      {"lct": "lct:web4:witness:...", "signature": "...", "timestamp": "..."}
    ],

    "net_trust_change": +0.035,
    "net_value_change": +0.015,
    "timestamp": "2025-10-14T..."
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject_lct` | LCT | Yes | Entity whose reputation changed |
| `role_lct` | LCT | Yes | Role LCT (MRH pairing link) |
| `role_pairing_in_mrh` | Object | Yes | Full MRH role pairing context |
| `action_type` | String | Yes | Action verb from request |
| `action_target` | LCT/URI | Yes | Target of the action |
| `action_id` | Hash | Yes | Transaction that caused the change |
| `rule_triggered` | String | No | Which reputation rule was triggered |
| `reason` | String | Yes | Human-readable explanation |
| `t3_delta` | Object | Yes | Trust tensor changes on this role (may be empty) |
| `v3_delta` | Object | Yes | Value tensor changes on this role (may be empty) |
| `contributing_factors` | Array | No | Factors that influenced the delta |
| `witnesses` | Array | No | Independent validators of change |
| `net_trust_change` | Number | Yes | Sum of T3 changes |
| `net_value_change` | Number | Yes | Sum of V3 changes |
| `timestamp` | ISO8601 | Yes | When reputation changed |

**CRITICAL**: Reputation is **role-contextualized**. The `t3_delta` and `v3_delta` apply to the specific MRH role pairing link, NOT globally to the entity. An entity can have different reputations in different roles.

## 2. Trust Tensor (T3) Dimensions

The **T3 tensor** captures **capability and character** across three dimensions:

### 2.1 Talent
**Definition**: Innate capability and aptitude for the role.

**Increases When**:
- Demonstrating exceptional skill
- Solving problems others cannot
- Showing creativity or innovation
- Achieving results beyond expectations

**Decreases When**:
- Consistent underperformance
- Inability to meet basic requirements
- Repeated errors in fundamental tasks

**Typical Range**: 0.0 (no demonstrated talent) to 1.0 (exceptional natural ability)

### 2.2 Training
**Definition**: Acquired knowledge, skills, and experience.

**Increases When**:
- Completing educational programs
- Gaining experience through practice
- Learning from mistakes
- Demonstrating mastery of complex topics

**Decreases When**:
- Skills atrophy from lack of use
- Outdated knowledge not updated
- Failure to adapt to new methods

**Typical Range**: 0.0 (no training) to 1.0 (master-level expertise)

### 2.3 Temperament
**Definition**: Reliability, consistency, and character.

**Increases When**:
- Meeting commitments consistently
- Handling stress gracefully
- Demonstrating integrity
- Building long-term trust through behavior

**Decreases When**:
- Missing deadlines or commitments
- Inconsistent quality of work
- Dishonest or unethical behavior
- Unprofessional conduct

**Typical Range**: 0.0 (unreliable) to 1.0 (highly dependable)

### T3 Interpretation

**High T3 Across All Dimensions** (e.g., 0.9, 0.9, 0.9):
- Exceptional talent
- Deep training and experience
- Highly reliable temperament
- **Result**: Maximum trust in role

**Mixed T3** (e.g., 0.9 talent, 0.6 training, 0.7 temperament):
- Natural ability present
- Needs more experience
- Somewhat inconsistent reliability
- **Result**: Potential but needs development

**Low T3** (e.g., 0.3, 0.4, 0.5):
- Limited demonstrated capability
- Minimal training
- Questionable reliability
- **Result**: High-risk for critical roles

## 3. Value Tensor (V3) Dimensions

The **V3 tensor** captures **output quality and trustworthiness**:

### 3.1 Veracity
**Definition**: Truthfulness and honesty of claims and statements.

**Increases When**:
- Statements proven accurate by evidence
- Honest disclosure of limitations
- Transparent communication
- Correcting own mistakes proactively

**Decreases When**:
- False or misleading statements
- Exaggeration of capabilities
- Hiding relevant information
- Failing to correct known errors

**Typical Range**: 0.0 (known liar) to 1.0 (proven truthful)

### 3.2 Validity
**Definition**: Logical soundness and methodological correctness.

**Increases When**:
- Arguments are logically sound
- Methods are scientifically rigorous
- Evidence properly supports conclusions
- Reasoning is transparent and reproducible

**Decreases When**:
- Logical fallacies in arguments
- Methodological flaws in work
- Conclusions not supported by evidence
- Opaque or irreproducible processes

**Typical Range**: 0.0 (invalid reasoning) to 1.0 (formally valid)

### 3.3 Value
**Definition**: Usefulness and benefit provided to others.

**Increases When**:
- Output solves real problems
- Work provides measurable benefit
- Contributions are appreciated by users
- Long-term positive impact

**Decreases When**:
- Output is not useful
- Work creates more problems than it solves
- Negative externalities
- Waste of resources

**Typical Range**: 0.0 (harmful) to 1.0 (extremely valuable)

### V3 Interpretation

**High V3 Across All Dimensions** (e.g., 0.95, 0.95, 0.9):
- Truthful and honest
- Logically sound work
- Highly valuable contributions
- **Result**: High-quality, trustworthy output

**Mixed V3** (e.g., 0.9 veracity, 0.5 validity, 0.8 value):
- Honest intentions
- Methodological weaknesses
- Useful despite flaws
- **Result**: Valuable but needs rigor

**Low V3** (e.g., 0.4, 0.3, 0.2):
- Questionable truthfulness
- Invalid reasoning
- Little value provided
- **Result**: Low-quality, untrustworthy output

## 4. Reputation Rules

Reputation changes are **rule-triggered**, not arbitrary. Law Oracles define reputation rules that map outcomes to T3/V3 deltas.

### Rule Structure

```json
{
  "rule_id": "successful_analysis_completion",
  "trigger_conditions": {
    "action_type": "analyze_dataset",
    "result_status": "success",
    "quality_threshold": 0.95
  },
  "reputation_impact": {
    "t3_changes": {
      "training": {
        "base_delta": 0.01,
        "modifiers": [
          {"condition": "deadline_met", "multiplier": 1.5},
          {"condition": "exceed_quality", "multiplier": 1.2}
        ]
      },
      "temperament": {
        "base_delta": 0.005,
        "modifiers": [
          {"condition": "early_completion", "multiplier": 1.3}
        ]
      }
    },
    "v3_changes": {
      "veracity": {
        "base_delta": 0.02,
        "modifiers": [
          {"condition": "high_confidence", "multiplier": 1.1}
        ]
      }
    }
  },
  "witnesses_required": 2,
  "law_oracle": "lct:web4:oracle:data_science_society"
}
```

### Rule Categories

#### Success Rules
Triggered when actions complete successfully with quality above threshold.

**Example**: Data analysis succeeds with 95% accuracy
- `training`: +0.01 (gained experience)
- `temperament`: +0.005 (met commitment)
- `veracity`: +0.02 (results proven accurate)

#### Failure Rules
Triggered when actions fail or produce errors.

**Example**: Model training fails due to parameter errors
- `training`: -0.005 (demonstrated knowledge gap)
- `temperament`: -0.01 (wasted resources)
- `validity`: -0.01 (flawed methodology)

#### Exceptional Performance Rules
Triggered when performance significantly exceeds expectations.

**Example**: Solved problem in half expected time with 99% accuracy
- `talent`: +0.02 (demonstrated exceptional ability)
- `training`: +0.015 (applied advanced techniques)
- `value`: +0.03 (high-impact contribution)

#### Ethical Violation Rules
Triggered when unethical behavior is detected.

**Example**: Attempted to manipulate data or mislead stakeholders
- `temperament`: -0.10 (severe character issue)
- `veracity`: -0.20 (dishonesty)
- `validity`: -0.15 (methodological fraud)

**Note**: Ethical violations have **severe** reputation penalties.

## 5. Multi-Factor Computation

Reputation deltas are computed from **multiple contributing factors** with explicit weights.

### Algorithm

```python
def compute_reputation_delta(action, result, rules):
    """
    Compute reputation delta based on action outcome and triggered rules.
    """
    reputation = ReputationDelta()

    # 1. Identify triggered rules
    triggered_rules = []
    for rule in rules:
        if matches_trigger_conditions(rule, action, result):
            triggered_rules.append(rule)

    if not triggered_rules:
        # No rules triggered = no reputation change
        return empty_reputation_delta()

    # 2. Compute contributing factors
    factors = []
    for rule in triggered_rules:
        rule_factors = analyze_factors(action, result, rule)
        factors.extend(rule_factors)

    # 3. Normalize factor weights
    total_weight = sum(f.weight for f in factors)
    for factor in factors:
        factor.normalized_weight = factor.weight / total_weight

    # 4. Compute T3 deltas
    t3_changes = {}
    for dimension in ['talent', 'training', 'temperament']:
        delta = compute_dimension_delta(
            dimension,
            triggered_rules,
            factors,
            action,
            result
        )
        if delta != 0:
            t3_changes[dimension] = {
                'change': delta,
                'from': action.role.t3InRole[dimension],
                'to': action.role.t3InRole[dimension] + delta
            }

    # 5. Compute V3 deltas
    v3_changes = {}
    for dimension in ['veracity', 'validity', 'value']:
        delta = compute_dimension_delta(
            dimension,
            triggered_rules,
            factors,
            action,
            result
        )
        if delta != 0:
            v3_changes[dimension] = {
                'change': delta,
                'from': get_current_v3(action.role.actor, dimension),
                'to': get_current_v3(action.role.actor, dimension) + delta
            }

    # 6. Assemble reputation delta
    reputation.subject_lct = action.role.actor
    reputation.action_id = result.ledgerProof.txHash
    reputation.rule_triggered = triggered_rules[0].rule_id
    reputation.reason = generate_reason(triggered_rules, factors)
    reputation.t3_delta = t3_changes
    reputation.v3_delta = v3_changes
    reputation.contributing_factors = factors
    reputation.net_trust_change = sum(c['change'] for c in t3_changes.values())
    reputation.net_value_change = sum(c['change'] for c in v3_changes.values())

    return reputation


def compute_dimension_delta(dimension, rules, factors, action, result):
    """
    Compute delta for a single T3 or V3 dimension.
    """
    total_delta = 0.0

    for rule in rules:
        if dimension not in rule.reputation_impact:
            continue

        impact = rule.reputation_impact[dimension]
        base_delta = impact.base_delta

        # Apply modifiers based on contributing factors
        multiplier = 1.0
        for modifier in impact.modifiers:
            if factor_applies(modifier.condition, factors):
                multiplier *= modifier.multiplier

        total_delta += base_delta * multiplier

    # Clamp to [-1.0, +1.0] to prevent overflow
    return max(-1.0, min(1.0, total_delta))


def analyze_factors(action, result, rule):
    """
    Analyze which factors contributed to this reputation change.
    """
    factors = []

    # Quality-based factors
    if 'quality_threshold' in rule.trigger_conditions:
        actual_quality = extract_quality(result)
        threshold = rule.trigger_conditions.quality_threshold

        if actual_quality > threshold:
            exceed_ratio = (actual_quality - threshold) / threshold
            factors.append({
                'factor': 'exceed_quality',
                'weight': exceed_ratio,
                'value': actual_quality
            })

    # Time-based factors
    if 'deadline' in action.request.constraints:
        deadline = action.request.constraints.deadline
        completion = result.timestamp

        if completion <= deadline:
            factors.append({
                'factor': 'deadline_met',
                'weight': 0.3,
                'value': True
            })

            time_saved = deadline - completion
            if time_saved > timedelta(hours=1):
                factors.append({
                    'factor': 'early_completion',
                    'weight': 0.2,
                    'value': time_saved.total_seconds()
                })

    # Resource efficiency factors
    required = action.resource.required
    consumed = result.resourceConsumed

    if consumed < required:
        efficiency = 1.0 - (consumed / required)
        factors.append({
            'factor': 'resource_efficiency',
            'weight': efficiency * 0.2,
            'value': efficiency
        })

    # Accuracy factors (domain-specific)
    if 'accuracy' in result.output:
        accuracy = result.output.accuracy
        if accuracy > 0.95:
            factors.append({
                'factor': 'high_accuracy',
                'weight': 0.4,
                'value': accuracy
            })

    return factors
```

### Example Computation

**Action**: Train ML model
**Result**: Success, 97% accuracy, completed 2 hours early, used 90% of allocated compute

**Triggered Rule**: `successful_model_training`

**Contributing Factors**:
```json
[
  {"factor": "high_accuracy", "weight": 0.4, "normalized_weight": 0.40},
  {"factor": "deadline_met", "weight": 0.3, "normalized_weight": 0.30},
  {"factor": "early_completion", "weight": 0.2, "normalized_weight": 0.20},
  {"factor": "resource_efficiency", "weight": 0.1, "normalized_weight": 0.10}
]
```

**T3 Deltas**:
- `training`: base +0.01, multipliers (quality 1.2, early 1.3) = **+0.0156**
- `temperament`: base +0.005, multiplier (deadline 1.5) = **+0.0075**

**V3 Deltas**:
- `veracity`: base +0.02, no multipliers = **+0.02**
- `validity`: base +0.01, multiplier (accuracy 1.1) = **+0.011**

**Net Changes**:
- Trust: +0.0231
- Value: +0.031

## 6. Witnessing Reputation Changes

Reputation changes should be **witnessed** by independent validators.

### Witness Selection

```python
def select_reputation_witnesses(action, reputation_delta, rule):
    """
    Select witnesses for reputation change based on rule requirements.
    """
    required_count = rule.witnesses_required
    candidates = []

    # 1. Law Oracle witness (if rule specifies)
    if rule.law_oracle:
        candidates.append({
            'lct': rule.law_oracle,
            'type': 'law_oracle',
            'priority': 1
        })

    # 2. Role-specific validators
    role_validators = get_validators_for_role(action.role.roleType)
    for validator in role_validators:
        candidates.append({
            'lct': validator,
            'type': 'role_validator',
            'priority': 2
        })

    # 3. MRH-proximate entities (trust network)
    mrh_witnesses = get_mrh_witnesses(action.role.actor, depth=2)
    for witness in mrh_witnesses:
        candidates.append({
            'lct': witness,
            'type': 'mrh_witness',
            'priority': 3
        })

    # 4. Select required count by priority
    selected = []
    for priority in [1, 2, 3]:
        priority_candidates = [c for c in candidates if c.priority == priority]
        for candidate in priority_candidates:
            if len(selected) >= required_count:
                break
            selected.append(candidate)

    return selected
```

### Witness Attestation

Each witness signs the reputation delta:

```json
{
  "witness": {
    "lct": "lct:web4:witness:validator_123",
    "type": "role_validator",
    "signature": "0x...",
    "timestamp": "2025-10-14T...",
    "attestation": {
      "action_id": "txn:0x...",
      "reputation_hash": "sha256:...",
      "verified": true,
      "confidence": 0.95
    }
  }
}
```

## 7. Reputation Aggregation Over Time

Individual reputation deltas aggregate to form long-term reputation:

### Time-Weighted Aggregation

```python
def compute_current_reputation(entity_lct, role_lct, dimension, time_horizon_days=90):
    """
    Compute current reputation by time-weighted aggregation of deltas.

    CRITICAL: Reputation is role-contextualized. This function computes
    reputation for a specific entity+role pairing, not globally.

    Args:
        entity_lct: The entity whose reputation to compute
        role_lct: The specific role LCT (from MRH pairing)
        dimension: Which T3/V3 dimension to compute
        time_horizon_days: How far back to aggregate

    Returns:
        Current reputation value [0.0, 1.0] for this entity in this role
    """
    # Get deltas for this specific entity+role pairing
    deltas = get_reputation_deltas(
        entity_lct=entity_lct,
        role_lct=role_lct,  # Filter by role!
        dimension=dimension,
        since=now() - timedelta(days=time_horizon_days)
    )

    if not deltas:
        return 0.5  # Neutral starting point for new role pairings

    # Recent deltas weighted more heavily
    weighted_sum = 0.0
    weight_sum = 0.0

    for delta in deltas:
        age_days = (now() - delta.timestamp).days
        recency_weight = math.exp(-age_days / 30.0)  # 30-day half-life

        weighted_sum += delta.change * recency_weight
        weight_sum += recency_weight

    current_value = weighted_sum / weight_sum if weight_sum > 0 else 0.5

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, current_value))
```

### Example: Role-Specific Reputation Query

```python
# Alice has reputation in multiple roles
alice = "lct:web4:entity:alice"

# Role 1: Financial Analyst
role_analyst = "lct:web4:role:analyst_financial:abc"
training_as_analyst = compute_current_reputation(alice, role_analyst, "training")
# Returns: 0.90 (highly trained financial analyst)

# Role 2: Medical Surgeon
role_surgeon = "lct:web4:role:surgeon_cardiac:xyz"
training_as_surgeon = compute_current_reputation(alice, role_surgeon, "training")
# Returns: 0.20 (no medical training)

# Same entity, different roles, different reputations!
```

### Reputation Decay

Reputation naturally decays without activity:

```python
def apply_reputation_decay(entity_lct, dimension, last_action_timestamp):
    """
    Apply natural decay to reputation based on inactivity.
    """
    days_inactive = (now() - last_action_timestamp).days

    if days_inactive < 30:
        return 0.0  # No decay within 30 days

    # Decay rate: -0.01 per month of inactivity
    months_inactive = days_inactive / 30.0
    decay = -0.01 * months_inactive

    # Decay accelerates after 6 months
    if months_inactive > 6:
        decay *= 1.5

    return max(-0.5, decay)  # Cap at -0.5 total decay
```

## 8. Implementation Checklist

For R7 implementations:

- [ ] Define reputation rules in Law Oracle
- [ ] Implement `compute_reputation_delta()` function
- [ ] Implement `compute_dimension_delta()` for each T3/V3 dimension
- [ ] Implement `analyze_factors()` for multi-factor analysis
- [ ] Implement witness selection and attestation
- [ ] Store ReputationDelta in ledger alongside Result
- [ ] Implement reputation aggregation over time
- [ ] Implement reputation decay for inactive entities
- [ ] Create reputation query APIs
- [ ] Build reputation analytics dashboards

## 9. Security Considerations

### Sybil Resistance
Reputation cannot be easily gamed through fake identities because:
1. Each action costs ATP (economic barrier)
2. Reputation is role-specific (can't transfer across roles)
3. Witnesses validate changes (collusion is detectable)
4. Historical patterns are analyzed (sudden changes flagged)

### Gaming Prevention
Rules must be designed to prevent gaming:
- **No self-attestation**: Witnesses must be independent
- **Diminishing returns**: Repeated identical actions yield less reputation
- **Quality thresholds**: Minimum standards must be met
- **Multi-dimensional**: Can't maximize one dimension while ignoring others

### Privacy
Reputation is public by design in Web4:
- All reputation changes on-chain
- Witnessed and auditable
- Transparent trust mechanics

However, **specific action details** may be private (encrypted result data).

## 10. Future Evolution

Potential reputation system enhancements:

### Machine Learning Reputation Models
Use historical patterns to predict reputation changes and detect anomalies.

### Cross-Society Reputation
Allow reputation earned in one society to partially transfer to related societies.

### Reputation Staking
Allow entities to stake their reputation as collateral for high-trust actions.

### Reputation Markets
Enable trading of reputation-weighted tokens (ATP/ADP modified by T3/V3).

### Reputation Insurance
Third parties insure against reputation loss in case of unforeseen failures.

## Summary

Web4's reputation computation:
- **Multi-dimensional**: T3 (trust) and V3 (value) across 6 dimensions
- **Rule-triggered**: Law Oracles define reputation rules
- **Multi-factor**: Contributing factors with explicit weights
- **Witnessed**: Independent validation of changes
- **Aggregated**: Time-weighted accumulation over history
- **Observable**: All changes on-chain and auditable

**R7 makes trust-building the explicit product of every Web4 transaction.**

---

*For implementation examples, see ACT blockchain federation governance (reputation-based participation tracking).*

*For the complete R7 specification, see `r7-framework.md`.*
