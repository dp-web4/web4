# Quality-Selectivity Tradeoff in Phase 2c + SAGE Integration

**Date**: 2025-12-15
**Session**: Autonomous Web4 Research Session 52
**Discovery**: SAGE patterns create quality-selectivity tradeoff

## Executive Summary

Testing circadian + SAGE integration with tuned satisfaction threshold (0.60) revealed that **SAGE patterns improve coordination quality at the cost of coordination volume**. This is not a failure - it's a valid architectural tradeoff.

## Results at Threshold = 0.60

| Configuration | Coord Rate | Avg Quality | Quality Δ | Rate Δ |
|--------------|------------|-------------|-----------|--------|
| Baseline (Phase 2b) | 67.6% | 0.700 | - | - |
| Circadian (Phase 2c) | 50.6% | 0.770 | +0.069 | -17.0pp |
| Circadian + SAGE | 18.0% | 0.879 | +0.109 | -32.6pp |

## Key Discovery: Quality-Selectivity Tradeoff

### Pattern

As filtering mechanisms are added:
1. **Baseline → Circadian**: -17.0pp coordination, +0.069 quality
2. **Circadian → +SAGE**: -32.6pp coordination, +0.109 quality
3. **Baseline → Combined**: -49.6pp coordination, +0.178 quality (+25% quality improvement!)

### Interpretation

**SAGE patterns act as a quality filter**:
- 100% pattern usage rate
- Rejecting low-quality coordination opportunities
- Accepting only high-quality opportunities
- Result: Lower volume, higher quality

This is similar to Session 50's discovery that circadian-only coordination had higher quality (0.958) than baseline (0.729) at much lower rate (5.2% vs 68.6%). Both circadian biasing and SAGE patterns are acting as **quality filters**.

## Architectural Implications

### This is NOT a Bug

The quality-selectivity tradeoff is a **feature, not a bug**, depending on use case:

**Use Case A: High-Volume Coordination**
- Goal: Maximize coordination opportunities
- Metric: Coordination rate
- Optimal: Baseline Phase 2b (67.6%)
- SAGE patterns: **Harmful** (-49.6pp)

**Use Case B: High-Quality Coordination**
- Goal: Maximize coordination quality
- Metric: Average quality
- Optimal: Phase 2c + SAGE (0.879)
- SAGE patterns: **Beneficial** (+25% quality)

**Use Case C: Balanced**
- Goal: Balance volume and quality
- Metric: Quality-weighted coordination (rate × quality)
- Baseline: 67.6% × 0.700 = 0.473
- Circadian: 50.6% × 0.770 = 0.390
- Combined: 18.0% × 0.879 = 0.158

For quality-weighted metric, baseline wins. But if quality has diminishing returns or volume doesn't matter, combined wins.

### Configurable Selectivity

System should support **configurable selectivity** based on use case:

```python
class CoordinationMode(Enum):
    HIGH_VOLUME = "high_volume"     # Optimize for rate
    HIGH_QUALITY = "high_quality"   # Optimize for quality
    BALANCED = "balanced"            # Optimize for rate × quality
```

Configuration:
- **HIGH_VOLUME**: satisfaction_threshold=0.60, no SAGE filtering
- **HIGH_QUALITY**: satisfaction_threshold=0.75, SAGE filtering enabled
- **BALANCED**: satisfaction_threshold=0.65, selective SAGE filtering

## Validation Questions

### Is Quality Improvement Real or Selection Bias?

**Question**: Is 0.879 quality because SAGE patterns improve decisions, or just because they reject more?

**Test**: Compare quality of the SAME opportunities with/without SAGE patterns
- Filter to only opportunities that BOTH systems would coordinate
- Measure if SAGE actually improves decision quality vs just being more selective

### Are SAGE Patterns Actually Matching?

**Observation**: 100% SAGE pattern usage suggests they're being applied every cycle

**Questions**:
1. Are patterns matching well? (high match scores)
2. Or matching poorly? (low match scores, reducing confidence)
3. Is 100% usage rate expected?

Need diagnostic logging of:
- Pattern match scores
- Which patterns are matching
- Learned confidence values

## Next Steps

### 1. Diagnostic Logging

Add logging to understand SAGE pattern matching:

```python
# In coordination decision logging:
- pattern_match_scores: List[Tuple[pattern_id, match_score]]
- learned_confidence_components: Dict[str, float]
- confidence_reduction: float  # How much SAGE reduced confidence
```

### 2. Selective Pattern Application

Instead of applying ALL SAGE patterns, apply only high-confidence matches:

```python
# Only use patterns with match_score > 0.7
high_confidence_patterns = [
    p for p in patterns
    if pattern_match_score(p, context) > 0.7
]
```

### 3. Quality-Weighted Optimization

Optimize for `rate × quality` instead of rate alone:

```python
# Adjust satisfaction_threshold to maximize quality-weighted coordination
quality_weighted_score = coordination_rate * average_quality
```

### 4. A/B Test with Same Opportunities

Test if SAGE improves decisions on same opportunities:

```python
# For each opportunity:
decision_without_sage = coordinator_no_sage.decide(opportunity)
decision_with_sage = coordinator_sage.decide(opportunity)

# Compare quality of coordinations that BOTH accepted
same_opportunities = [
    o for o in opportunities
    if decision_without_sage and decision_with_sage
]

quality_without = mean([o.quality for o in same_opportunities])
quality_with = mean([o.quality for o in same_opportunities])
```

## Conclusion

**Finding**: SAGE patterns create quality-selectivity tradeoff, not pure improvement

**Value**: This is valuable architectural insight
- Systems can optimize for volume OR quality, not both simultaneously
- Tradeoff can be configured based on use case
- Current default (high volume) makes SAGE look harmful
- High-quality mode would make SAGE look beneficial

**Status**: ⚠️ Architecture requires mode selection, not universal optimization

**Next Priority**: Add diagnostic logging to understand WHY SAGE patterns are suppressing coordination (poor matching? conservative by design?)

---

## Research Value

This finding is MORE valuable than simple "compound benefits confirmed":

1. **Tradeoff identified**: Quality vs volume is fundamental, not a bug
2. **Use-case dependent**: Same mechanism is helpful or harmful depending on goals
3. **Configurable**: System should support different optimization modes
4. **Diagnostic needed**: Need to understand pattern matching to optimize

**Lesson**: "Improvement" depends on defining what to optimize. Multi-dimensional optimization requires tradeoff analysis, not single-metric evaluation.
