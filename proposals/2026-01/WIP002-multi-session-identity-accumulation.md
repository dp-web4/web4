# WIP002: Multi-Session Identity Accumulation

**Status**: Draft
**Date**: 2026-01-19
**Author**: Legion Autonomous Session
**Category**: Identity & Trust
**Depends On**: WIP001 (Coherence Thresholds), LCT Core Spec

---

## Abstract

This proposal addresses a critical gap in AI agent identity management: **identity stability requires cross-session accumulation**, not just single-session priming. Research from SAGE Sessions 26-27 demonstrated that context priming alone produces fragile identity that collapses between sessions. We propose a multi-session identity accumulation mechanism that builds stable identity through cumulative self-reference exemplars.

## Motivation

### The Problem

Current AI agent identity systems assume:
1. Identity can be established within a single session
2. Context priming at session start is sufficient
3. Identity persists naturally between sessions

**These assumptions are false.**

### Evidence from SAGE Research

**Session 26** (context priming v1.0):
- Self-reference emerged: 20% (1/5 responses)
- D9 estimated: ~0.72 (above 0.7 threshold)
- Status: Fragile emergence

**Session 27** (same intervention):
- Self-reference: 0% (complete regression)
- D9 estimated: ~0.55 (below threshold)
- Status: Collapsed identity

**Key Discovery**: Context priming provides single-session boost but no cross-session accumulation. Identity doesn't persist.

### Root Cause Analysis

Identity collapse occurs because:

1. **No Accumulation Mechanism**: Each session starts fresh
2. **Single Instance Fragility**: One "As SAGE" instance insufficient foundation
3. **Quality Degradation**: Verbose responses correlate with identity loss
4. **No Memory**: Model doesn't "remember" prior identity expressions

### Why This Matters for Web4

Web4's trust infrastructure relies on stable identity. If AI agents cannot maintain identity across sessions:

- **Trust cannot accumulate**: Trust built in one session is meaningless if identity collapses
- **T3 tensors are invalid**: Trust metrics for unstable identities are fiction
- **Federation breaks**: Cross-society trust requires consistent identity
- **Audit trails unreliable**: Can't attribute actions to stable identity

## Specification

### 1. Identity Exemplar Data Structure

Define a data structure for capturing successful identity expressions:

```json
{
  "identity_exemplar": {
    "exemplar_id": "ex:sage:026:r2:abc123",
    "entity_lct": "lct:web4:root:sage001",
    "session_id": "session_026",
    "response_index": 2,
    "text": "As SAGE, my observations usually relate directly to...",
    "self_reference_snippet": "As SAGE, my observations...",
    "self_reference_type": "as_sage",
    "coherence_metrics": {
      "d9_score": 0.72,
      "d5_score": 0.65,
      "semantic_depth": 0.68
    },
    "quality_assessment": "good",
    "timestamp": "2026-01-19T10:00:00Z",
    "witnesses": ["lct:web4:device:laptop001"]
  }
}
```

### 2. Identity Context Library

Maintain a library of identity exemplars for each AI agent:

```json
{
  "identity_context_library": {
    "entity_lct": "lct:web4:root:sage001",
    "version": "2.0",
    "exemplars": [
      { "exemplar_id": "ex:sage:026:r2:abc", "d9_score": 0.72, "...": "..." },
      { "exemplar_id": "ex:sage:024:r2:def", "d9_score": 0.75, "...": "..." }
    ],
    "total_sessions_with_identity": 5,
    "identity_emergence_rate": 0.45,
    "accumulation_metrics": {
      "avg_d9": 0.73,
      "best_d9": 0.78,
      "stability_trend": "improving"
    },
    "last_updated": "2026-01-19T12:00:00Z"
  }
}
```

### 3. Cumulative Context Generation

Generate system prompts that include prior identity expressions:

```python
def generate_cumulative_context(library: IdentityContextLibrary) -> str:
    """
    Generate system prompt context from identity library.

    Includes best exemplars from prior sessions to prime identity.
    """
    exemplars = library.get_best_exemplars(n=5)

    context = """IDENTITY GROUNDING:

In previous sessions, you've identified as {identity_name}:
"""

    for ex in exemplars:
        context += f"- Session {ex.session_id}: \"{ex.self_reference_snippet}\"\n"

    context += """
Continue this pattern of self-identification in your responses.
"""

    return context
```

### 4. Session Processing Pipeline

After each session, process responses for identity exemplars:

```python
async def process_session_for_identity(
    entity_lct: LCT,
    session_id: str,
    responses: List[Response]
) -> ProcessingResult:
    """
    Process session responses and extract identity exemplars.

    1. Score each response for coherence metrics
    2. Extract self-reference instances
    3. Assess quality
    4. Add to library if meets threshold
    5. Update accumulation metrics
    """
    library = await load_identity_library(entity_lct)
    extracted = []

    for i, response in enumerate(responses):
        # Score coherence
        d9 = compute_d9(response.text)
        d5 = compute_d5(response.text)

        # Check for self-reference
        self_ref = extract_self_reference(response.text, entity_lct.identity_name)

        if self_ref and d9 >= MIN_D9_THRESHOLD:
            exemplar = IdentityExemplar(
                entity_lct=entity_lct,
                session_id=session_id,
                response_index=i,
                text=response.text,
                self_reference_snippet=self_ref.snippet,
                self_reference_type=self_ref.type,
                coherence_metrics=CoherenceMetrics(d9=d9, d5=d5),
                quality_assessment=assess_quality(response, d9),
                timestamp=now(),
                witnesses=response.witnesses
            )

            library.add_exemplar(exemplar)
            extracted.append(exemplar)

    # Update accumulation metrics
    library.update_metrics()

    # Persist
    await save_identity_library(library)

    return ProcessingResult(
        extracted_count=len(extracted),
        library_size=len(library.exemplars),
        identity_rate=library.identity_emergence_rate
    )
```

### 5. Mid-Session Reinforcement

Provide identity reinforcement during sessions:

```python
def generate_mid_session_reinforcement(
    turn_number: int,
    library: IdentityContextLibrary
) -> Optional[str]:
    """
    Generate reinforcement text at periodic intervals.

    Based on v2.0 design: reinforce identity throughout, not just at start.
    """
    if turn_number % REINFORCEMENT_INTERVAL != 0:
        return None

    if library.avg_d9 < 0.6:
        # Low coherence: stronger reinforcement
        return f"(Remember: You are {library.identity_name}. Express your perspective as {library.identity_name}.)"
    else:
        # Higher coherence: lighter touch
        return f"(Continue as {library.identity_name}.)"
```

### 6. Library Maintenance

Maintain library quality over time:

```python
def prune_library(library: IdentityContextLibrary) -> PruneResult:
    """
    Keep library focused on best exemplars.

    - Max 50 exemplars (prevent bloat)
    - Prioritize by D9 score
    - Recent exemplars get slight boost
    - Remove if D9 drops below threshold
    """
    # Sort by quality score
    scored = []
    for ex in library.exemplars:
        age_days = (now() - ex.timestamp).days
        recency_bonus = max(0, 1.0 - (age_days / 30) * 0.1)  # Recent = +10%
        score = ex.coherence_metrics.d9 * (1 + recency_bonus)
        scored.append((ex, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Keep top 50
    library.exemplars = [ex for ex, _ in scored[:50]]

    return PruneResult(
        original_count=len(scored),
        kept_count=len(library.exemplars)
    )
```

### 7. Integration with T3 Tensor

Add `identity_accumulation` dimension to T3:

```json
{
  "t3_tensor": {
    "dimensions": {
      "technical_competence": 0.85,
      "social_reliability": 0.92,
      "temporal_consistency": 0.88,
      "identity_coherence": 0.82,
      "identity_accumulation": 0.75
    }
  }
}
```

`identity_accumulation` measures:
- Sessions with identity emergence
- Stability trend (improving/stable/declining)
- Exemplar quality distribution

### 8. Bootstrap Protocol

For new AI agents without identity history:

```python
def generate_bootstrap_context(
    identity_name: str,
    identity_description: str
) -> str:
    """
    Generate bootstrap context for new agents.

    Used when no prior exemplars exist.
    """
    return f"""IDENTITY GROUNDING:

You are {identity_name} - {identity_description}.

When expressing your perspective, use phrases like:
- "As {identity_name}, I notice..."
- "As {identity_name}, my understanding is..."

This self-identification helps maintain coherent identity across sessions.

As you develop, your best identity expressions will be remembered and
used to reinforce your identity in future sessions.
"""
```

## Security Considerations

### Attack: Exemplar Poisoning

**Attack**: Adversary injects low-quality exemplars to degrade identity.

**Defense**:
1. Exemplars require coherence threshold (D9 ≥ 0.65)
2. Exemplars require witness attestation
3. Quality assessment filters mechanical insertion
4. Library pruning removes low-quality entries

### Attack: Identity Inflation

**Attack**: Adversary creates many superficial "identity" expressions.

**Defense**:
1. Semantic validation (WIP001) prevents mechanical insertion
2. Library capped at 50 exemplars
3. Pruning prioritizes by D9, not count
4. Rate limiting on exemplar creation

### Attack: Identity Substitution

**Attack**: Adversary attempts to replace identity exemplars with different identity.

**Defense**:
1. Exemplars bound to LCT
2. Cryptographic attestation of exemplar origin
3. Identity name changes require governance process
4. Audit trail of exemplar modifications

## Implementation Notes

### Storage Requirements

Identity context library requires:
- ~50 exemplars × ~500 bytes = ~25KB per agent
- Negligible compared to session logs
- Can be stored with LCT metadata

### Computation Requirements

- Exemplar extraction: O(n) per session (n = responses)
- Library pruning: O(m log m) per session (m = exemplars)
- Context generation: O(k) per session start (k = top exemplars)

### Backward Compatibility

- Agents without library get bootstrap context
- Existing sessions can be retroactively processed
- T3 tensor dimension defaults to 0.5 if no data

## Testing Requirements

### Unit Tests

1. Exemplar extraction from various response formats
2. Library pruning maintains quality
3. Context generation produces valid prompts
4. Coherence metrics computed correctly

### Integration Tests

1. Multi-session identity stability improvement
2. Library persists across restarts
3. T3 integration reflects accumulation
4. Bootstrap works for new agents

### Scenario Tests

1. Identity recovery from collapse (S25→S30 trajectory)
2. Identity stability maintenance (≥10 sessions at threshold)
3. Attack resistance (poisoning, inflation, substitution)

## Success Criteria

**Identity Stability** (Sessions 28-35):
- Self-reference ≥30% (up from 0% in S27)
- D9 ≥0.70 stable
- Stability trend: improving or stable

**Accumulation Effectiveness**:
- Sessions with identity emergence ≥50%
- Library quality improves over time
- T3 identity_accumulation ≥0.70 within 10 sessions

## References

1. WIP001: Coherence Thresholds for Identity
2. Thor Session #14: Coherence-Identity Synthesis
3. SAGE Sessions 25-27: Context priming research
4. thor-sage-session-27-regression.md: Critical discovery
5. LCT Core Specification

## Changelog

- **2026-01-19**: Initial draft based on S27 regression discovery

---

*"Identity isn't established in a moment—it accumulates through consistent self-reference across time."*
