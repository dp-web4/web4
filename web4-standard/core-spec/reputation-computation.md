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
      "valuation": {"change": +0.005, "from": 0.75, "to": 0.755}
    },

    "contributing_factors": [
      {"factor": "high_accuracy", "weight": 0.4},
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
| `role_pairing_in_mrh` | Object | No | Full MRH role pairing context (derivable from `role_lct` via the entity↔role MRH pairing; carried only as a denormalized convenience) |
| `action_type` | String | Yes | Action verb from request |
| `action_target` | LCT/URI | Yes | Target of the action |
| `action_id` | Hash | Yes | Transaction that caused the change |
| `rule_triggered` | String | No | Which reputation rule(s) were triggered — when multiple rules fire, the ids are joined (comma-separated) and `reason` derives from the full set |
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

The **V3 tensor** captures **value creation** across three verification dimensions.

> **Canonical source**: V3 dimension semantics (names, measures, ranges) are
> defined canonically in [`t3-v3-tensors.md §3`](./t3-v3-tensors.md). This section
> describes how those dimensions move under reputation computation; where the two
> are read together, the canonical definitions govern.

### 3.1 Veracity (Objective Accuracy)
**Definition**: Objective accuracy — truthfulness, accuracy, and reproducibility of claims, established by external validation and witness attestation against domain-specific verification standards.

**Increases When**:
- Statements proven accurate by evidence
- Results are independently reproducible
- Honest disclosure of limitations
- Correcting own mistakes proactively

**Decreases When**:
- False or misleading statements
- Exaggeration of capabilities
- Hiding relevant information
- Failing to correct known errors

**Typical Range**: 0.0 (known liar) to 1.0 (proven truthful)

### 3.2 Validity (Confirmed Transfer)
**Definition**: Confirmed transfer — actual value delivery and receipt. Updated binary per transaction (`1.0` if value was transferred, else `0.0`) and averaged over time across completion of the value-transfer cycle. (Canonical: `t3-v3-tensors.md §3.1`, §3.3 `Validity = 1.0 if value_transferred else 0.0`.)

**Increases When**:
- Promised value is actually delivered and received
- The value-transfer cycle completes (ATP/ADP settled)
- Recipients confirm receipt of the delivered value

**Decreases When**:
- Value is not delivered despite the action completing
- The transfer cycle is left incomplete or fails to settle
- Delivery is claimed but receipt is never confirmed

**Typical Range**: 0.0 (no value transferred) to 1.0 (value confirmed delivered)

### 3.3 Valuation (Subjective Worth)
**Definition**: Subjective worth — the value perceived by recipients. Recipient-specific and use-case dependent; each transaction adds to the valuation history.

**Increases When**:
- Output solves real problems for recipients
- Work provides measurable benefit
- Contributions are appreciated by users
- Long-term positive impact

**Decreases When**:
- Output is not useful to recipients
- Work creates more problems than it solves
- Negative externalities
- Waste of resources

**Typical Range**: 0.0 (harmful) upward; commonly normalized toward 1.0 (extremely valuable). The canonical upper bound is an **open question** — `t3-v3-tensors.md §3.1` notes Valuation may exceed 1.0 (subjective worth) pending an operator decision; do not assume a hard [0,1] clamp here.

### V3 Interpretation

**High V3 Across All Dimensions** (e.g., 0.95, 0.95, 0.9):
- Truthful and accurate
- Value reliably delivered and received
- Highly valuable contributions
- **Result**: High-quality, trustworthy output

**Mixed V3** (e.g., 0.9 veracity, 0.5 validity, 0.8 valuation):
- Honest and accurate claims
- Inconsistent value delivery
- Useful despite flaws
- **Result**: Valuable but needs reliable delivery

**Low V3** (e.g., 0.4, 0.3, 0.2):
- Questionable truthfulness
- Value frequently undelivered
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
    "t3_impacts": {
      "training": {
        "base_delta": 0.01,
        "modifiers": [
          {"condition": "deadline_met", "multiplier": 1.5},
          {"condition": "high_accuracy", "multiplier": 1.2}
        ]
      },
      "temperament": {
        "base_delta": 0.005,
        "modifiers": [
          {"condition": "early_completion", "multiplier": 1.3}
        ]
      }
    },
    "v3_impacts": {
      "veracity": {
        "base_delta": 0.02,
        "modifiers": [
          {"condition": "high_accuracy", "multiplier": 1.1}
        ]
      }
    }
  },
  "witnesses_required": 2,
  "law_oracle": "lct:web4:oracle:data_science_society"
}
```

### Trigger Condition Semantics

`trigger_conditions` is an **open-ended** set of conjunctive checks (a rule
matches only when **all** stated conditions hold). The conditions in common use:

| Condition | Match semantics |
|-----------|-----------------|
| `action_type` | Equals the action's verb. |
| `result_status` | Equals the action result status (e.g. `success`). |
| `quality_threshold` | Matches **iff** `output.quality >= threshold`. A missing quality value is treated as `0.0`, so the threshold fails. |
| `min_atp_stake` | Matches **iff** the action's staked ATP `>= min_atp_stake`. Lets rules apply only above a minimum economic commitment. |

Implementations MAY define additional conditions. The reference SDK
(`reputation.py` `ReputationRule.matches()`) evaluates only the recognized
conditions above and **ignores** any it does not recognize (**fail-open**): a
rule matches when all recognized conditions pass, regardless of extra keys.
An implementation MAY instead treat an unrecognized condition as fail-closed
(cause the rule not to match); this is a stricter local choice and is **not
currently required** for conformance.

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
- `validity`: -0.01 (no value delivered — transfer cycle did not complete)

#### Exceptional Performance Rules
Triggered when performance significantly exceeds expectations.

**Example**: Solved problem in half expected time with 99% accuracy
- `talent`: +0.02 (demonstrated exceptional ability)
- `training`: +0.015 (applied advanced techniques)
- `valuation`: +0.03 (high-impact contribution)

#### Ethical Violation Rules
Triggered when unethical behavior is detected.

**Example**: Attempted to manipulate data or mislead stakeholders
- `temperament`: -0.10 (severe character issue)
- `veracity`: -0.20 (dishonesty)
- `validity`: -0.15 (fraudulent transfer — purported value not genuinely delivered)

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

    # 2. Compute contributing factors (rule-independent signals from the
    #    action outcome — computed once, as in the SDK)
    factors = analyze_factors(action, result)

    # 3. Compute T3 deltas
    t3_changes = {}
    for dimension in ['talent', 'training', 'temperament']:
        delta = compute_dimension_delta('t3', dimension, triggered_rules, factors)
        from_value = action.role.t3InRole[dimension]
        # Clamp the new value to [0,1] and recompute the effective change,
        # so a delta that would push the dimension past its range is truncated
        # and the recorded `change` reflects the truncation (SDK parity).
        to_value = max(0.0, min(1.0, from_value + delta))
        change = to_value - from_value
        if change != 0:
            t3_changes[dimension] = {
                'change': change,
                'from': from_value,
                'to': to_value
            }

    # 4. Compute V3 deltas
    v3_changes = {}
    for dimension in ['veracity', 'validity', 'valuation']:
        delta = compute_dimension_delta('v3', dimension, triggered_rules, factors)
        from_value = action.role.v3InRole[dimension]
        to_value = max(0.0, min(1.0, from_value + delta))
        change = to_value - from_value
        if change != 0:
            v3_changes[dimension] = {
                'change': change,
                'from': from_value,
                'to': to_value
            }

    # 5. Assemble reputation delta
    reputation.subject_lct = action.role.actor
    reputation.role_lct = action.role.role_lct          # role-contextualization key (Required)
    reputation.action_type = action.request.action
    reputation.action_target = action.request.target
    reputation.action_id = action.action_id             # pre-execution id, set at request time
    # Record the id of EVERY triggered rule (the delta loops above accumulate
    # across all of them), joined comma-separated — full provenance, SDK parity
    # (`reputation.py`: rule_ids = ", ".join(r.rule_id for r in triggered)).
    reputation.rule_triggered = ", ".join(r.rule_id for r in triggered_rules)
    reputation.reason = generate_reason(triggered_rules, factors)
    reputation.t3_delta = t3_changes
    reputation.v3_delta = v3_changes
    reputation.contributing_factors = factors
    reputation.net_trust_change = sum(c['change'] for c in t3_changes.values())
    reputation.net_value_change = sum(c['change'] for c in v3_changes.values())
    reputation.timestamp = now()

    return reputation


def compute_dimension_delta(tensor, dimension, rules, factors):
    """
    Compute delta for a single dimension of a tensor.

    `tensor` is 't3' or 'v3' — it selects which per-tensor impacts map to
    read. Rules nest impacts under `t3_impacts` / `v3_impacts` (see §4 Rule
    Structure), matching the SDK (`reputation.py` reads `rule.t3_impacts` for
    T3 dims, `rule.v3_impacts` for V3 dims) and the conformance vectors.
    """
    total_delta = 0.0
    impacts_attr = 't3_impacts' if tensor == 't3' else 'v3_impacts'

    for rule in rules:
        impacts = getattr(rule, impacts_attr)
        if dimension not in impacts:
            continue

        impact = impacts[dimension]
        base_delta = impact.base_delta

        # Apply modifiers based on contributing factors
        multiplier = 1.0
        for modifier in impact.modifiers:
            if factor_applies(modifier.condition, factors):
                multiplier *= modifier.multiplier

        total_delta += base_delta * multiplier

    # Clamp to [-1.0, +1.0] to prevent overflow
    return max(-1.0, min(1.0, total_delta))


def analyze_factors(action, result):
    """
    Analyze which factors contributed to this reputation change.

    Factors are rule-independent signals extracted from the action outcome
    (quality, timing, resource efficiency) — computed once per action and
    matched against each triggered rule's modifier conditions in
    `compute_dimension_delta`. Mirrors the SDK `analyze_factors(action)`.
    """
    factors = []

    # Quality-based factor: a single `high_accuracy` signal when output
    # quality clears the neutral midpoint (SDK parity — `reputation.py`
    # `analyze_factors` keys on quality/accuracy > 0.5, weight 0.4).
    quality = result.output.get('quality', result.output.get('accuracy'))
    if quality is not None and quality > 0.5:
        factors.append({
            'factor': 'high_accuracy',
            'weight': 0.4,
            'value': quality
        })

    # Time-based factors (SDK parity — `reputation.py` reads pre-resolved
    # boolean flags off `action.request.constraints`; it does NOT carry a
    # `deadline` datetime nor apply a fixed early-completion threshold). The
    # caller resolves these flags upstream (one illustrative resolution: set
    # `deadline_met` from `result.timestamp <= constraints.deadline` and
    # `early_completion` from a society-defined margin, e.g. > 1 hour early).
    if action.request.constraints.get('deadline_met'):
        factors.append({
            'factor': 'deadline_met',
            'weight': 0.3,
            'value': True
        })

    if action.request.constraints.get('early_completion'):
        factors.append({
            'factor': 'early_completion',
            'weight': 0.2,
            'value': True
        })

    # Resource efficiency factor (SDK parity — `reputation.py` reads
    # `resource.required_atp` / `result.atp_consumed`, guards `required > 0`,
    # and rounds the weight to 4 places).
    required = action.resource.required_atp
    consumed = result.atp_consumed

    if required > 0 and consumed < required:
        efficiency = 1.0 - (consumed / required)
        factors.append({
            'factor': 'resource_efficiency',
            'weight': round(efficiency * 0.2, 4),
            'value': efficiency
        })

    return factors
```

### Example Computation

**Action**: Analyze dataset
**Result**: Success, 97% accuracy, completed 2 hours early

**Triggered Rule**: `successful_analysis_completion` (the rule defined in §4)

**Contributing Factors** (exactly as `analyze_factors` emits them — 97% accuracy clears the 0.5 quality midpoint, the deadline is met, and completion is >1h early):
```json
[
  {"factor": "high_accuracy", "weight": 0.4},
  {"factor": "deadline_met", "weight": 0.3},
  {"factor": "early_completion", "weight": 0.2}
]
```

**T3 Deltas** (per §4's `successful_analysis_completion` modifier→dimension mapping):
- `training`: base +0.01 × deadline_met (1.5) × high_accuracy (1.2) = **+0.018**
- `temperament`: base +0.005 × early_completion (1.3) = **+0.0065**

**V3 Deltas**:
- `veracity`: base +0.02 × high_accuracy (1.1) = **+0.022**

**Net Changes**:
- Trust: +0.018 + 0.0065 = **+0.0245**
- Value: **+0.022**

> **Note**: This worked example deliberately exercises a *richer* factor set
> than conformance vector `rep-001` (`test-vectors/reputation/reputation-operations.json`).
> Here the rule instance includes the `early_completion`×1.3 temperament
> modifier and the scenario completes early, yielding temperament **+0.0065**;
> `rep-001` uses a rule without that modifier and records temperament **+0.005**.
> Both are internally consistent against their own rule instance — they are not
> the same instance of `successful_analysis_completion`.

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
    role_validators = get_validators_for_role(action.role.role_lct)
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
    Compute current reputation by time-weighted aggregation of deltas
    onto the 0.5 neutral baseline.

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
        age_days = max(0.0, (now() - delta.timestamp).total_seconds() / 86400.0)  # fractional days, floored at 0 for clock skew (SDK parity)
        recency_weight = math.exp(-age_days / 30.0)  # exp decay, 30-day time constant (1/e; ≈20.8-day half-life)

        weighted_sum += delta.change * recency_weight
        weight_sum += recency_weight

    # Deltas are CHANGES, not absolute values (§1), so the recency-weighted
    # average accumulates onto the 0.5 neutral baseline rather than replacing it.
    current_value = 0.5 + (weighted_sum / weight_sum) if weight_sum > 0 else 0.5

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, current_value))
```

### Example: Role-Specific Reputation Query

```python
# Alice has reputation in multiple roles
alice = "lct:web4:entity:alice"

# Role 1: Financial Analyst — sustained history of positive training deltas
role_analyst = "lct:web4:role:analyst_financial:abc"
training_as_analyst = compute_current_reputation(alice, role_analyst, "training")
# Returns: > 0.5 — positive training deltas accumulated above the 0.5 baseline
#          (exact level depends on delta magnitudes and recency)

# Role 2: Medical Surgeon — never acted in this role
role_surgeon = "lct:web4:role:surgeon_cardiac:xyz"
training_as_surgeon = compute_current_reputation(alice, role_surgeon, "training")
# Returns: 0.50 — neutral baseline; no training deltas recorded in this role

# Same entity, different roles, different reputations!
```

**Modeling note**: This `baseline + recency-weighted average` model keeps reputation near 0.5 for the small per-action deltas defined in §4 (typically ±0.005–0.03); the absolute level reflects the **direction and consistency** of accumulated deltas, not their count. Driving the level toward the [0.0, 1.0] extremes from many small deltas would require an *accumulation* (rather than averaging) model — see §10 (Future Evolution). The SDK (`reputation.py`, `ReputationStore.current()`) implements this same baseline+average form.

### Reputation Decay

Reputation naturally decays without activity:

```python
def apply_reputation_decay(entity_lct, role_lct, last_action_timestamp):
    """
    Apply natural decay to reputation based on inactivity.

    CRITICAL: Decay is role-contextualized, like every other reputation
    operation in this spec (§1, §7 `compute_current_reputation`). It is keyed
    by the (entity_lct, role_lct) pairing — an entity active in role A but idle
    in role B decays only in role B. The SDK (`reputation.py`
    `inactivity_decay(entity_lct, role_lct)`) keys decay state the same way.
    """
    days_inactive = max(0.0, (now() - last_action_timestamp).total_seconds() / 86400.0)  # floored at 0 for clock skew (SDK parity)

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

**Composing decay with the aggregate**: `apply_reputation_decay` returns a
*negative delta*, not a reputation value. It composes with
`compute_current_reputation` additively — the effective reputation is the
time-weighted aggregate plus the inactivity decay, re-clamped to [0.0, 1.0]:

```python
def effective_reputation(entity_lct, role_lct, dimension, last_action_timestamp):
    base = compute_current_reputation(entity_lct, role_lct, dimension)
    decay = apply_reputation_decay(entity_lct, role_lct, last_action_timestamp)
    return max(0.0, min(1.0, base + decay))
```

This mirrors the SDK (`reputation.py`, `ReputationStore.effective_reputation()`
= `current() + inactivity_decay()`), and is what the checklist item below means
by applying decay.

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
- **Diminishing returns**: Repeated identical actions yield less reputation. The mechanism is defined canonically in [`t3-v3-tensors.md §7.1`](./t3-v3-tensors.md) (`max(0.8^(n−1), 0.1)`; test vector t3v3-007); the per-action delta path in §5 does not itself apply it.
- **Quality thresholds**: Minimum standards must be met
- **Multi-dimensional**: Can't maximize one dimension while ignoring others

### Privacy
Reputation is public by design in Web4:
- All reputation changes recorded in the society ledger
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
- **Observable**: All changes recorded in the society ledger and auditable

**R7 makes trust-building the explicit product of every Web4 transaction.**

---

*For implementation examples, see ACT blockchain federation governance (reputation-based participation tracking).*

*For the complete R7 specification, see `r7-framework.md`.*
