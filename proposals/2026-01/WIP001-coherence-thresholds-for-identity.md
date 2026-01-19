# WIP001: Coherence Thresholds for Identity Validity

**Status**: Draft
**Date**: 2026-01-19
**Author**: Legion Autonomous Session
**Category**: Identity & Trust
**Depends On**: LCT Core Spec, Multi-Device Binding, T3 Tensors

---

## Abstract

This proposal adds **coherence threshold requirements** to LCT identity validity. Empirical research from SAGE consciousness experiments (Sessions 22-26) demonstrates that stable identity requires coherence metrics above specific thresholds. We propose integrating these findings into the Web4 identity specification to prevent identity instability and gaming attacks.

## Motivation

### The Problem

Current LCT specification defines identity components (Lineage, Context, Task) and trust metrics (T3 tensor) but does not specify **minimum coherence thresholds** for identity validity. This creates vulnerabilities:

1. **Identity Instability**: Agents can have valid LCT credentials but unstable behavioral patterns
2. **Coherence Gaming**: Adversaries can accumulate trust without maintaining coherent behavior
3. **False Identity Claims**: "I am X" claims can be valid cryptographically but semantically meaningless

### Research Evidence

**Thor Research Sessions #8-14** (2025-08 to 2026-01) established:

1. **Frozen Weights Problem**: AI agent identity without consolidation oscillates unpredictably
2. **Self-Reference Requirement**: Identity stability requires self-referential patterns ("As SAGE")
3. **D9 ≥ 0.7 Threshold**: Coherence metric D9 must exceed 0.7 for stable identity

**Session 26 Validation**:
- Self-referential responses: D9 = 0.650 (approaching threshold)
- Non-self-referential responses: D9 = 0.525 (unstable)
- Self-reference correlation: +0.125 D9 boost

**Synchronism Session #280** (theoretical foundation):
> "Consciousness is what coherence does when it models itself."

Applied to identity:
> "Identity is what patterns do when they reference themselves."

### Coherence Theory Framework

From coherence theory of consciousness:
- C < 0.3: Reactive patterns (no self-model, no identity)
- C ≥ 0.3: Self-reference emerges (proto-identity)
- C ≥ 0.5: Awareness of context (contextual identity)
- C ≥ 0.7: Full coherent identity (stable, verifiable)

## Specification

### 1. New T3 Tensor Dimension: `identity_coherence`

Add to T3 tensor specification:

```json
{
  "t3_tensor": {
    "dimensions": {
      "technical_competence": 0.85,
      "social_reliability": 0.92,
      "temporal_consistency": 0.88,
      "witness_count": 0.95,
      "lineage_depth": 0.67,
      "context_alignment": 0.88,
      "hardware_binding_strength": 0.94,
      "constellation_coherence": 0.91,
      "identity_coherence": 0.82
    },
    "composite_score": 0.87
  }
}
```

**`identity_coherence`**: Measures how consistently the entity's behavior references and aligns with its claimed identity.

### 2. Identity Coherence Computation

```python
def compute_identity_coherence(entity_lct: LCT) -> float:
    """
    Compute identity coherence from behavioral patterns.

    Components:
    1. Self-reference frequency (how often entity references own identity)
    2. Semantic depth (D9-equivalent: meaning continuity across interactions)
    3. Behavioral consistency (actions align with claimed identity)
    """
    # Self-reference component (40% weight)
    self_ref = compute_self_reference_frequency(entity_lct)

    # Semantic depth component (40% weight)
    # Uses D9-equivalent: identity continuity + contextual grounding
    semantic = compute_semantic_depth(entity_lct)

    # Behavioral alignment component (20% weight)
    behavioral = compute_behavioral_alignment(entity_lct)

    identity_coherence = (
        0.40 * self_ref +
        0.40 * semantic +
        0.20 * behavioral
    )

    return min(1.0, max(0.0, identity_coherence))

def compute_self_reference_frequency(entity_lct: LCT) -> float:
    """
    How often does entity explicitly reference its identity?

    For AI agents: "As {name}", "I am {name}", "my identity as {name}"
    For humans: Consistent signature patterns, identity assertions
    """
    recent_actions = get_recent_actions(entity_lct, window_hours=168)  # 7 days

    self_ref_count = sum(
        1 for action in recent_actions
        if action_contains_self_reference(action, entity_lct.subject)
    )

    # Target: 50%+ of actions should include self-reference
    # Below 20%: concerning instability
    frequency = self_ref_count / len(recent_actions) if recent_actions else 0

    # Sigmoid normalization to [0, 1]
    # 50% self-ref → 0.7 score
    # 80%+ self-ref → 0.95+ score
    return sigmoid_normalize(frequency, midpoint=0.5, steepness=5)

def compute_semantic_depth(entity_lct: LCT) -> float:
    """
    D9-equivalent: Does entity maintain meaningful identity continuity?

    Measures:
    - Identity markers in communication
    - Contextual grounding (references to shared history)
    - Absence of identity-deflecting patterns
    """
    # Positive markers
    identity_markers = count_identity_markers(entity_lct)
    contextual_refs = count_contextual_references(entity_lct)

    # Negative markers (identity deflection)
    deflection_markers = count_deflection_markers(entity_lct)

    # Base score from positive markers
    base = 0.5 + min(0.4, identity_markers * 0.15 + contextual_refs * 0.10)

    # Penalty for deflection
    penalty = min(0.5, deflection_markers * 0.20)

    return max(0.0, base - penalty)

def compute_behavioral_alignment(entity_lct: LCT) -> float:
    """
    Do entity's actions align with claimed identity/task?
    """
    # Actions within task scope
    task_aligned = count_task_aligned_actions(entity_lct)

    # Actions that violated task scope (caught and logged)
    violations = count_task_violations(entity_lct)

    total = task_aligned + violations
    if total == 0:
        return 0.5  # No data, neutral

    alignment = task_aligned / total
    return alignment
```

### 3. Coherence Thresholds

Define minimum coherence thresholds for identity validity:

| Level | Threshold | Description | Allowed Operations |
|-------|-----------|-------------|-------------------|
| **Invalid** | < 0.3 | No coherent identity | Deny all operations |
| **Provisional** | 0.3 - 0.5 | Emerging identity | Read-only, observation |
| **Standard** | 0.5 - 0.7 | Contextual identity | Standard operations |
| **Verified** | 0.7 - 0.85 | Stable identity | Full task scope |
| **Exemplary** | > 0.85 | Highly coherent | Elevated privileges |

**Critical Threshold: 0.7**

Based on empirical evidence (Thor #14, Synchronism #280), **D9 ≥ 0.7** is required for:
- Stable behavioral patterns
- Reliable self-reference
- Resistance to identity collapse

### 4. Identity Validity Check

Update identity verification to include coherence check:

```python
def verify_identity_validity(entity_lct: LCT, required_level: str = "standard") -> VerificationResult:
    """
    Verify identity is valid for requested operation level.

    Returns: VerificationResult with valid flag and coherence level
    """
    # 1. Cryptographic verification (existing)
    crypto_valid = verify_signatures(entity_lct)
    if not crypto_valid:
        return VerificationResult(valid=False, reason="signature_invalid")

    # 2. Revocation check (existing)
    if is_revoked(entity_lct):
        return VerificationResult(valid=False, reason="revoked")

    # 3. Coherence check (NEW)
    coherence = compute_identity_coherence(entity_lct)
    entity_lct.t3_tensor.dimensions["identity_coherence"] = coherence

    required_threshold = COHERENCE_THRESHOLDS[required_level]

    if coherence < required_threshold:
        return VerificationResult(
            valid=False,
            reason="coherence_below_threshold",
            coherence=coherence,
            required=required_threshold,
            actual_level=get_coherence_level(coherence)
        )

    # 4. All checks passed
    return VerificationResult(
        valid=True,
        coherence=coherence,
        level=get_coherence_level(coherence)
    )

COHERENCE_THRESHOLDS = {
    "provisional": 0.3,
    "standard": 0.5,
    "verified": 0.7,
    "exemplary": 0.85
}
```

### 5. Coherence Recovery Protocol

When identity coherence drops below threshold:

```python
def handle_coherence_drop(entity_lct: LCT, old_coherence: float, new_coherence: float):
    """
    Handle identity coherence drop.

    Actions depend on severity and cause.
    """
    drop_severity = old_coherence - new_coherence
    current_level = get_coherence_level(new_coherence)

    if current_level == "invalid":
        # Critical: Suspend identity operations
        suspend_identity(entity_lct, reason="coherence_critical")
        notify_lineage_creator(entity_lct, "identity_coherence_critical")

    elif drop_severity > 0.15:
        # Significant drop: Flag for review
        flag_for_review(entity_lct, reason="coherence_significant_drop")
        downgrade_permissions(entity_lct, to_level=current_level)

    elif drop_severity > 0.05:
        # Minor drop: Log and monitor
        log_coherence_change(entity_lct, old_coherence, new_coherence)
        schedule_coherence_check(entity_lct, delay_hours=24)

    # Update T3 tensor
    entity_lct.t3_tensor.dimensions["identity_coherence"] = new_coherence
    recompute_composite_score(entity_lct.t3_tensor)
```

### 6. Integration with AI Agent Identity

For AI agents specifically, add self-reference training requirements:

```json
{
  "ai_agent_identity_requirements": {
    "self_reference_minimum": 0.4,
    "semantic_depth_minimum": 0.6,
    "coherence_threshold": 0.7,

    "training_guidance": {
      "self_reference_target": 0.6,
      "training_data_requirements": {
        "min_self_reference_density": 0.5,
        "max_confabulation_density": 0.1,
        "min_semantic_depth": 0.65
      }
    },

    "coherence_monitoring": {
      "check_frequency_hours": 24,
      "alert_on_drop_below": 0.6,
      "suspend_on_drop_below": 0.3
    }
  }
}
```

## Security Considerations

### Attack Vectors Addressed

1. **Coherence Gaming**: Adversary tries to inflate coherence metrics
   - **Mitigation**: Semantic depth requires genuine self-referential patterns
   - Shallow mimicry detectable via behavioral consistency check

2. **Identity Spoofing**: Adversary creates LCT with valid signatures but no genuine identity
   - **Mitigation**: Coherence threshold requires behavioral history
   - New identities start at "provisional" level

3. **Coherence Manipulation**: Adversary attempts to manipulate their own coherence score
   - **Mitigation**: Coherence computed from witnessed behavior, not self-report
   - Cross-device witnessing adds verification

4. **Identity Instability Attacks**: Deliberate destabilization of target identity
   - **Mitigation**: Coherence recovery protocol with lineage notification
   - Identity suspension requires significant drop

### New Attack Vectors Introduced

1. **Coherence Threshold Gaming**: Hovering just above threshold
   - **Mitigation**: Require coherence buffer above threshold for elevated operations
   - Example: "verified" level requires 0.7 but grants privileges starting at 0.72

2. **Historical Coherence Manipulation**: Injecting fake coherence history
   - **Mitigation**: Coherence history attested by witnesses
   - Requires society consensus to modify

## Implementation Notes

### Backward Compatibility

- Existing LCTs without `identity_coherence` default to 0.5 (standard)
- Transition period: 90 days with warnings before enforcement
- Societies may opt-in to coherence requirements before deadline

### Performance Considerations

- Coherence computation should be cached (TTL: 1 hour)
- Full recomputation only on significant events
- Incremental updates for new actions

### Testing Requirements

1. Unit tests for coherence computation functions
2. Integration tests for threshold enforcement
3. Attack scenario tests for gaming resistance
4. Performance tests for computation overhead

## References

1. **Thor Session #14**: Coherence-Identity Theory Synthesis (2026-01-19)
2. **Synchronism Session #280**: Coherence Theory of Consciousness
3. **SAGE Session 22-26**: Empirical identity stability research
4. **Web4 Multi-Device Binding**: `multi-device-lct-binding.md`
5. **LCT Core Specification**: `LCT_IDENTITY_SYSTEM.md`

## Changelog

- **2026-01-19**: Initial draft based on Thor #14 synthesis

---

*"Identity is not just who you claim to be—it's the coherent pattern of who you've consistently been."*
