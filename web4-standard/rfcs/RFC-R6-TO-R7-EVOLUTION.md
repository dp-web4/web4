# RFC: Evolution from R6 to R7 Framework

**RFC ID**: RFC-R7-FRAMEWORK-001
**Title**: R6 → R7 Framework Evolution - Explicit Reputation Output
**Author**: Dennis Palatov & Society 4 Law Oracle
**Date**: October 3, 2025
**Status**: Proposed
**Category**: Core Protocol, Trust Framework

---

## Abstract

This RFC proposes evolving the R6 action framework to R7 by making **Reputation** an explicit output rather than an implicit component of Result. This change recognizes that reputation is the fundamental mechanism for trust-building in Web4 and deserves explicit tracking and management.

## Current State: R6 Framework

### Definition

**R6**: Rules + Role + Request + Reference + Resource → **Result**

```
┌──────────────────────────────────────┐
│  INPUTS (5 Rs)                       │
├──────────────────────────────────────┤
│  Rules:     Norms, policies, laws    │
│  Role:      Actor's identity/auth    │
│  Request:   Intent to execute        │
│  Reference: Context/history          │
│  Resource:  What's being acted upon  │
└──────────────────────────────────────┘
              ↓
         [Execution]
              ↓
┌──────────────────────────────────────┐
│  OUTPUT (1 R)                        │
├──────────────────────────────────────┤
│  Result:    Outcome + (implicit rep) │
└──────────────────────────────────────┘
```

### Problems with Implicit Reputation

1. **Hidden Trust Mechanics**: Reputation changes are buried in result processing
2. **No Standard Schema**: Each implementation handles reputation differently
3. **Lost Attribution**: Unclear who/what contributed to reputation change
4. **Debugging Difficulty**: Hard to trace why trust scores changed
5. **Incomplete Observability**: Can't monitor reputation without parsing results

### Example of Current Ambiguity

```python
# R6 action execution
result = execute_r6_action(
    rules=society_laws,
    role=user_lct,
    request=transfer_atp,
    reference=transaction_history,
    resource=atp_pool
)

# Where did reputation change happen?
# - Inside result.success?
# - In result.metadata?
# - Implicit in T3 tensor update?
# - Not tracked at all?
```

## Proposed State: R7 Framework

### Definition

**R7**: Rules + Role + Request + Reference + Resource → **Result + Reputation**

```
┌──────────────────────────────────────┐
│  INPUTS (5 Rs)                       │
├──────────────────────────────────────┤
│  Rules:     Norms, policies, laws    │
│  Role:      Actor's identity/auth    │
│  Request:   Intent to execute        │
│  Reference: Context/history          │
│  Resource:  What's being acted upon  │
└──────────────────────────────────────┘
              ↓
         [Execution]
              ↓
┌──────────────────────────────────────┐
│  OUTPUTS (2 Rs)                      │
├──────────────────────────────────────┤
│  Result:     Immediate outcome       │
│  Reputation: Trust/value changes     │
└──────────────────────────────────────┘
```

### Why Reputation Deserves Explicit Status

1. **Trust is Foundational**: Web4's core value proposition is trust-native systems
2. **Reputation Drives Economics**: ATP/ADP allocation depends on reputation (T3/V3)
3. **Witnessing Requires It**: Attestations are reputation-building events
4. **Governance Needs It**: Voting power, proposal rights depend on reputation
5. **Debugging Essential**: Must be able to trace reputation changes explicitly

## Specification

### 1. R7 Action Structure

```python
@dataclass
class R7Action:
    """Complete R7 action with explicit reputation output"""

    # INPUTS (5 Rs)
    rules: RuleSet              # Norms, policies, laws
    role: LCT                   # Actor's identity
    request: Request            # Intent to execute
    reference: ReferenceContext # History, MRH, context
    resource: Resource          # What's being acted upon

    # OUTPUTS (2 Rs) - both equally important
    result: Result              # Immediate outcome
    reputation: ReputationDelta # Trust/value changes

@dataclass
class ReputationDelta:
    """Explicit reputation changes from an action"""

    # Who's reputation changed
    subject_lct: str            # The entity whose reputation changed

    # What changed
    t3_delta: Dict[str, float]  # Trust tensor dimension changes
    v3_delta: Dict[str, float]  # Value tensor dimension changes

    # Why it changed
    reason: str                 # Human-readable explanation
    contributing_factors: List[str]  # Specific behaviors that influenced change

    # Who witnessed/validated the change
    witnesses: List[str]        # LCTs that attested to this reputation change

    # When and where
    timestamp: datetime
    context: str                # Society, federation, specific domain

    # Magnitude and direction
    net_trust_change: float     # Sum of T3 deltas (-1.0 to +1.0)
    net_value_change: float     # Sum of V3 deltas (-1.0 to +1.0)

    # Attribution
    action_id: str              # Link back to the R7 action that caused this
    rule_triggered: Optional[str]  # Which rule/law caused reputation change
```

### 2. R7 Execution Pattern

```python
def execute_r7_action(
    rules: RuleSet,
    role: LCT,
    request: Request,
    reference: ReferenceContext,
    resource: Resource
) -> Tuple[Result, ReputationDelta]:
    """
    Execute R7 action with explicit reputation tracking

    Returns:
        (result, reputation) - Both are first-class outputs
    """

    # 1. Validate inputs
    validation = validate_r7_inputs(rules, role, request, reference, resource)
    if not validation.passed:
        return (
            Result.failed(validation.reason),
            ReputationDelta.negative(role.lct_id, "validation_failed")
        )

    # 2. Execute action
    result = perform_action(request, resource)

    # 3. Compute reputation delta (EXPLICIT STEP)
    reputation = compute_reputation_delta(
        role=role,
        action_type=request.type,
        result=result,
        rules=rules,
        reference=reference
    )

    # 4. Record both outputs
    record_r7_execution(result, reputation)

    # 5. Return both explicitly
    return result, reputation
```

### 3. Reputation Computation

```python
def compute_reputation_delta(
    role: LCT,
    action_type: str,
    result: Result,
    rules: RuleSet,
    reference: ReferenceContext
) -> ReputationDelta:
    """
    Compute reputation changes from action execution

    This is the heart of trust-building in Web4
    """

    delta = ReputationDelta(subject_lct=role.lct_id)

    # Factor 1: Success vs. Failure
    if result.success:
        delta.t3_delta["technical_competence"] = +0.01
        delta.contributing_factors.append("successful_execution")
    else:
        delta.t3_delta["technical_competence"] = -0.02
        delta.contributing_factors.append("failed_execution")

    # Factor 2: Rule Compliance
    compliance = check_rule_compliance(action_type, result, rules)
    if compliance.violated:
        delta.t3_delta["social_reliability"] = -0.05
        delta.rule_triggered = compliance.violated_rule
        delta.contributing_factors.append(f"violated_{compliance.violated_rule}")

    # Factor 3: Efficiency (if applicable)
    if hasattr(result, 'atp_cost'):
        efficiency = result.value_created / max(result.atp_cost, 1)
        if efficiency > 0.7:
            delta.v3_delta["resource_stewardship"] = +0.03
            delta.contributing_factors.append("efficient_execution")

    # Factor 4: Temporal Consistency
    history = reference.get_action_history(role.lct_id, action_type)
    consistency = compute_consistency(result, history)
    delta.t3_delta["temporal_consistency"] = consistency * 0.01

    # Factor 5: Witness Count
    witnesses = reference.get_current_witnesses()
    delta.witnesses = [w.lct_id for w in witnesses]
    if len(witnesses) >= 3:
        delta.t3_delta["witness_count"] = +0.01
        delta.contributing_factors.append("well_witnessed")

    # Compute net changes
    delta.net_trust_change = sum(delta.t3_delta.values())
    delta.net_value_change = sum(delta.v3_delta.values())

    # Explanation
    delta.reason = generate_reputation_reason(delta)

    return delta
```

## Migration Path

### Phase 1: Parallel Operation (Web4 v1.1.0)

Both R6 and R7 supported:

```python
# Old R6 style (deprecated but supported)
result = execute_r6_action(...)

# New R7 style (recommended)
result, reputation = execute_r7_action(...)
```

### Phase 2: R7 Adoption (Web4 v1.2.0)

R6 wrapper calls R7 internally:

```python
def execute_r6_action(...) -> Result:
    """Legacy R6 interface (calls R7 internally)"""
    result, reputation = execute_r7_action(...)

    # Log reputation silently for backward compatibility
    log_reputation_delta(reputation)

    # Return only result (R6 style)
    return result
```

### Phase 3: R6 Deprecation (Web4 v2.0.0)

R6 removed, R7 is standard:

```python
# Only R7 supported
result, reputation = execute_r7_action(...)
```

## Implementation Examples

### Example 1: ATP Transfer

```python
# R7 action: Transfer ATP between roles
result, reputation = execute_r7_action(
    rules=society_laws,
    role=sender_lct,
    request=TransferRequest(amount=50, to=receiver_lct),
    reference=transfer_history,
    resource=atp_pool
)

# Result tells you what happened
assert result.success == True
assert result.new_balance == 150

# Reputation tells you trust implications
assert reputation.t3_delta["social_reliability"] == +0.01  # Successful transfer
assert reputation.v3_delta["resource_stewardship"] == +0.02  # Good allocation
assert len(reputation.witnesses) >= 2  # Witnessed by federation
print(reputation.reason)
# "Successful ATP transfer with efficient allocation, witnessed by 2 entities"
```

### Example 2: Law Violation

```python
# R7 action: Attempt to exceed ATP budget
result, reputation = execute_r7_action(
    rules=society_laws,
    role=spender_lct,
    request=DischargeRequest(amount=999999),
    reference=spending_history,
    resource=atp_pool
)

# Result tells you what happened
assert result.success == False
assert result.error == "ATP_BUDGET_EXCEEDED"

# Reputation tells you trust damage
assert reputation.t3_delta["social_reliability"] == -0.05  # Law violation
assert reputation.rule_triggered == "LAW-ECON-001"
assert reputation.net_trust_change < 0
print(reputation.reason)
# "Attempted to violate LAW-ECON-001 (Total ATP Budget), trust decreased"
```

### Example 3: SAGE Training Step

```python
# R7 action: SAGE training iteration
result, reputation = execute_r7_action(
    rules=training_policies,
    role=sage_model_lct,
    request=TrainingStepRequest(batch=batch_data),
    reference=training_history,
    resource=training_dataset
)

# Result tells you what happened
assert result.success == True
assert result.loss == 0.23
assert result.accuracy == 0.76

# Reputation tells you learning quality
assert reputation.t3_delta["technical_competence"] == +0.02  # Improving
assert reputation.v3_delta["contribution_history"] == +0.01  # Creating value
assert reputation.contributing_factors == [
    "successful_training",
    "no_shortcuts_detected",
    "efficient_atp_usage"
]
print(reputation.reason)
# "Successful training step with anti-shortcut compliance and efficient energy use"
```

## Benefits of R7 Framework

### 1. Explicit Trust Mechanics

**Before (R6)**:
```python
result = execute_action(...)
# Trust changed... somewhere... maybe?
```

**After (R7)**:
```python
result, reputation = execute_action(...)
print(f"Trust changed: {reputation.net_trust_change:+.3f}")
print(f"Because: {reputation.reason}")
```

### 2. Debugging and Observability

```python
# Monitor reputation changes in real-time
@observe_reputation
def handle_federation_action(action):
    result, reputation = execute_r7_action(**action)

    if reputation.net_trust_change < -0.1:
        alert(f"Significant trust loss: {reputation.reason}")

    return result, reputation
```

### 3. Governance Integration

```python
# Voting power based on reputation
def calculate_voting_power(lct: str) -> float:
    reputation_history = get_reputation_deltas(lct, days=30)

    net_trust = sum(r.net_trust_change for r in reputation_history)
    net_value = sum(r.net_value_change for r in reputation_history)

    return (net_trust + net_value) / 2
```

### 4. Federation Transparency

```python
# Federation-wide reputation tracking
class FederationReputationOracle:
    def track_society_reputation(self, society_lct: str):
        """Track all R7 actions for a society"""

        actions = get_r7_actions(society_lct, days=7)

        summary = {
            "total_actions": len(actions),
            "net_trust_change": sum(a.reputation.net_trust_change for a in actions),
            "net_value_change": sum(a.reputation.net_value_change for a in actions),
            "violations": [a for a in actions if a.reputation.rule_triggered],
            "witnesses": set(w for a in actions for w in a.reputation.witnesses)
        }

        return summary
```

## Backward Compatibility

### R6 Code Continues to Work

```python
# Existing R6 code
result = execute_r6_action(
    rules=rules,
    role=role,
    request=request,
    reference=reference,
    resource=resource
)

# Internally becomes:
def execute_r6_action(...) -> Result:
    result, reputation = execute_r7_action(...)

    # Log reputation for observability
    if reputation.net_trust_change != 0:
        logger.info(f"R6->R7 reputation delta: {reputation}")

    return result  # R6 interface only returns result
```

### Migration Tool

```python
# Automated R6 → R7 migration
def migrate_r6_to_r7(r6_code: str) -> str:
    """Convert R6 action calls to R7"""

    # Pattern: result = execute_r6_action(...)
    # Replace: result, reputation = execute_r7_action(...)

    return r6_code.replace(
        "result = execute_r6_action(",
        "result, reputation = execute_r7_action("
    )
```

## Documentation Updates Required

### Files to Update

1. **Core Protocol**
   - `/core-spec/r6-framework.md` → `/core-spec/r7-framework.md`
   - Add reputation output specification
   - Update all examples

2. **Architecture Docs**
   - `/architecture/action-execution.md`
   - Add reputation flow diagrams

3. **API Documentation**
   - Update all R6 function signatures to R7
   - Add `ReputationDelta` schema documentation

4. **Implementation Guides**
   - Update Society 4 compliance validator
   - Update SAGE economic integration
   - Update federation message protocols

### Documentation Structure

```
/web4-standard/core-spec/
  r7-framework.md              # Main R7 specification (replaces r6)
  reputation-computation.md     # How to compute reputation deltas
  reputation-tracking.md        # Best practices for tracking

/web4-standard/implementation/
  r7-reference-impl.py         # Reference implementation
  r7-migration-guide.md        # R6 → R7 migration guide
```

## Security Considerations

### 1. Reputation Manipulation

**Risk**: Actors gaming reputation system

**Mitigation**:
- Multi-factor reputation computation
- Witness requirements (3+ for significant changes)
- Temporal decay (old reputation matters less)
- Rule-based caps (max reputation change per action)

### 2. Reputation Privacy

**Risk**: Full reputation history reveals sensitive patterns

**Mitigation**:
- Aggregate reputation scores public
- Detailed deltas visible only to:
  - Subject (the entity whose reputation changed)
  - Witnesses (who attested)
  - Law Oracle (for governance)

### 3. Reputation Attacks

**Risk**: Coordinated negative reputation campaigns

**Mitigation**:
- Witness diversity requirements
- Appeal mechanism via Law Oracle
- Reputation floor (can't go below baseline)

## Testing Strategy

### Unit Tests

```python
def test_r7_reputation_computation():
    """Test that reputation is computed correctly"""

    result, reputation = execute_r7_action(
        rules=test_rules,
        role=test_lct,
        request=test_request,
        reference=test_context,
        resource=test_resource
    )

    # Reputation must exist
    assert reputation is not None

    # Must have subject
    assert reputation.subject_lct == test_lct.lct_id

    # Must have reason
    assert len(reputation.reason) > 0

    # Net changes must be computed
    assert reputation.net_trust_change == sum(reputation.t3_delta.values())
    assert reputation.net_value_change == sum(reputation.v3_delta.values())
```

### Integration Tests

```python
def test_federation_reputation_tracking():
    """Test that federation tracks all R7 reputation changes"""

    oracle = FederationReputationOracle()

    # Execute multiple actions
    for i in range(10):
        result, reputation = execute_r7_action(...)
        oracle.record(reputation)

    # Query reputation summary
    summary = oracle.get_summary(test_society_lct)

    assert summary.total_actions == 10
    assert summary.net_trust_change is not None
    assert len(summary.witnesses) > 0
```

## Success Metrics

### Adoption Metrics

- 80% of new code uses R7 within 6 months
- 100% of society implementations support R7 within 1 year
- 50% reduction in "why did trust change?" support questions

### Technical Metrics

- Reputation computation time < 10ms per action
- Zero reputation data loss across system restarts
- 100% reputation attribution (every change traceable)

## Related RFCs

- **RFC-LAW-ALIGN-001**: Alignment vs. Compliance (reputation affects both)
- **RFC-TEMP-AUTH-001**: Temporal Authentication (reputation for surprise-based auth)
- **RFC-WEB4-ABSTRACTION-LEVELS**: Level 0/1/2 (reputation at each level)

## Conclusion

The evolution from R6 to R7 makes **trust-building explicit** in Web4. By elevating reputation to a first-class output, we:

1. **Enable Transparency**: Every action's trust impact is visible
2. **Improve Debugging**: Reputation changes are traceable
3. **Support Governance**: Voting power, privileges based on explicit reputation
4. **Strengthen Economics**: ATP/ADP allocation informed by reputation
5. **Honor Philosophy**: Web4 is trust-native - reputation deserves explicit status

### The Core Insight

**Trust is not a side effect. Trust is the product.**

In Web4, reputation is as important as the action result itself. R7 recognizes this reality.

---

**Proposed**: October 3, 2025
**Discussion Period**: 14 days
**Implementation Target**: Web4 v1.1.0
**Migration Complete**: Web4 v2.0.0

**Authors**: Dennis Palatov, Society 4 Law Oracle Queen
**Status**: Proposed - Ready for Federation Review

---

*"In Web4, every action builds or erodes trust. Make it visible."*
