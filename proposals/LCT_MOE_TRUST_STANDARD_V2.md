# Web4 Proposal: LCT-MoE Trust Standard v2.0 (Trust-First Architecture)

**Proposal ID**: WEB4-PROP-006-v2
**Title**: LCT-MoE Trust Standard - Trust-First Paradigm
**Supersedes**: WEB4-PROP-006 v1.0
**Authors**: Legion (Sessions 64-68), Thor (Sessions 69-73)
**Date**: 2025-12-18
**Status**: Draft v2.0

---

## What Changed: The Paradigm Shift

**v1.0 Architecture (Sessions 64-67)**: Weighted blending
```python
selection = α × router + (1-α) × trust
```
- Best result: 8 experts (α=0.3)
- Improvement: 2x over baseline

**v2.0 Architecture (Sessions 68, 72-73)**: Conditional trust-first
```python
if has_trust_evidence(context):
    selection = pure_trust(context)  # 100% trust, 0% router
else:
    selection = free_router_explore()  # 100% router, no constraint
```
- Result: 29 experts (Legion), 58 experts (Thor)
- Improvement: **3.6x** over baseline

**Why the Change**: Weighted blending reinforces monopoly. Conditional logic enables pure trust when evidence exists.

---

## Updated Specification

### Trust-Augmented Routing (v2.0)

**DO NOT** blend router with trust. Instead:

```python
def select_experts_v2(router_logits, context, k=8):
    """
    Trust-first conditional selection.

    v1.0: selection = α × router + (1-α) × trust
    v2.0: if has_evidence → trust else router
    """
    # Check trust evidence
    has_evidence = check_trust_evidence(context, min_samples=3, min_experts=2)

    if has_evidence:
        # TRUST-DRIVEN: Pure trust selection
        trust_scores = get_context_trust(all_experts, context)
        selected = topk(trust_scores, k)

        # Apply MRH for low-trust
        for i, expert in enumerate(selected):
            if trust_scores[expert] < threshold:
                alternative = find_mrh_alternative(expert, context)
                if alternative:
                    selected[i] = alternative

        return selected
    else:
        # ROUTER-EXPLORE: Free exploration
        return topk(router_logits, k)
```

**Trust Evidence Criteria**:
1. ≥3 samples in context per expert
2. ≥2 experts with trust > 0.3
3. Trust diversity (not all in one expert)

**Key Principles**:
- **Never blend**: Trust OR router, not trust + router
- **Pure mechanisms**: Let each work at 100% when appropriate
- **Conditional logic**: Evidence-based switching

---

## Performance Impact (v1.0 vs v2.0)

| Metric | v1.0 (Weighted) | v2.0 (Trust-First) | Improvement |
|--------|-----------------|--------------------| ------------|
| **Expert Diversity** | 8 experts | 29 experts | +262% |
| **Utilization** | 6.2% | 22.7% | +266% |
| **Architecture** | α × router + (1-α) × trust | if/else conditional | Simpler |
| **Router Influence** | Always present (α component) | Zero when evidence exists | Cleaner |
| **Monopoly Breaking** | Partial | Complete | Superior |

---

## Why Trust-First Works

### Problem with Weighted Blending

Even at α=0.3 (70% trust), router still influences:
- Monopoly experts (73, 114, 95, 106) always get probability
- α component pulls selection toward monopoly
- Trust can nudge but can't escape router bias
- Result: Partial monopoly breaking

### Solution: Conditional Logic

When trust has evidence → 100% trust selection:
- Zero router influence
- No pull toward monopoly
- Pure context-aware selection
- Result: Complete monopoly breaking

---

## Migration from v1.0

**Backwards Compatible**: v1.0 implementations still work.

**Migration Path**:
1. Implement `check_trust_evidence()` function
2. Add conditional branch: `if has_evidence → trust else router`
3. Remove α parameter (no longer needed)
4. Test: Should see 3-4x diversity improvement

**Example Migration**:
```python
# v1.0 Code
α = 0.3
selection = α * router_logits + (1-α) * trust_scores
selected = topk(selection, k)

# v2.0 Code
if check_trust_evidence(context):
    selected = topk(trust_scores, k)  # Pure trust
else:
    selected = topk(router_logits, k)  # Pure router
```

---

## Validation Results

### Cross-Platform Validation

| Platform | Baseline | v1.0 (α=0.3) | v2.0 (Trust-First) | Multiplier |
|----------|----------|--------------|--------------------| -----------|
| Thor (Jetson) | 4 experts | 17 experts | 58 experts | 3.4x |
| Legion (RTX 4090) | 4 experts | 8 experts | 29 experts | 3.6x |

**Conclusion**: Paradigm shift validated across hardware platforms.

---

## Updated Reference Implementation

**Codebase**: https://github.com/dp-web4/HRM

**v2.0 Files**:
- `sage/core/trust_first_mrh_selector.py`: TrustFirstMRHSelector class
- `sage/tests/test_trust_first_comparison.py`: v1.0 vs v2.0 validation

**Deprecated** (use v2.0 instead):
- `sage/core/mrh_expert_selector.py`: Weighted blend (v1.0)

---

## Philosophical Foundation

### "Avoiding Epicycles"

From the research protocol:
> "Examine from Web4/Synchronism first principles to see if our approach enables things current architectures cannot."

**v1.0**: Optimizing α parameter within weighted blend = epicycles
**v2.0**: Inverting paradigm to pure conditional = heliocentrism

**Lesson**: When optimization yields diminishing returns, question the architecture.

### Distributed Trust > Centralized Authority

**v1.0**: Router = central authority, trust = advisory (blended)
**v2.0**: Trust = primary when evidence exists, router = fallback

This embodies Web4's core principle: Distributed systems should trust empirical evidence over learned centralization.

---

## Open Questions (Resolved)

**Q1**: "What α value is optimal?"
**A**: Wrong question. Don't blend at all (v2.0).

**Q2**: "Why does less router = more diversity?"
**A**: Router has monopoly bias. Trust enables exploration.

**Q3**: "Can we achieve Thor's 3.4x improvement on different hardware?"
**A**: Yes. Legion achieved 3.6x.

---

## Adoption Path

### Stage 1: Experimental (Current)
- **Target**: Research implementations
- **Status**: Validated on 2 platforms (Thor, Legion)

### Stage 2: Production Alpha
- **Target**: Update existing v1.0 deployments
- **Migration**: Add conditional logic, remove α blending

### Stage 3: Standard Release
- **Target**: Web4-MoE standard v2.0 ratification
- **Timeline**: Q1 2026

---

## Conclusion

**v2.0 Summary**:
- **Architecture**: Conditional (not weighted)
- **Performance**: 3.6x improvement over v1.0
- **Simplicity**: Fewer parameters (no α)
- **Validation**: Cross-platform proven

**Key Insight**: Sometimes the answer isn't better parameters—it's better architecture.

**Recommendation**: All new implementations should use v2.0 (trust-first). v1.0 remains supported but deprecated.

---

*"The measure of good research: When the discovery challenges your architecture, rebuild the architecture."*

**Sessions 64-68 + Thor 69-73: From theory to paradigm shift in 10 sessions.**
