# Grounding Integration Notes

**Date**: 2025-12-27
**Related Proposal**: `/proposals/MRH_GROUNDING_PROPOSAL.md`

---

## Cross-Project Connections

### AI Agent Accountability (Today)

The [AI Agent Accountability](./AI_AGENT_ACCOUNTABILITY_BINDING.md) document discusses hardware binding as the trust foundation. Grounding adds the dynamic layer:

| Layer | What It Provides | Persistence |
|-------|------------------|-------------|
| Hardware Binding | Identity anchor | Permanent |
| LCT | Cryptographic identity | Permanent |
| T3 | Earned trust scores | Long-lived |
| **Grounding** | **Current presence & capability** | **Ephemeral** |

The trust gradient (anonymous 0.1 → hardware-bound 0.95) now has a **coherence multiplier** that modulates effective trust in real-time.

### Fractal IRP Architecture (HRM)

The [Fractal IRP proposals](https://github.com/dp-web4/HRM/tree/main/sage/docs/proposals) define IRP expert descriptors. Grounding can extend these:

```python
# Current descriptor
ExpertDescriptor(
    id, kind, capabilities, cost_model, endpoint, policy
)

# With grounding
ExpertDescriptor(
    id, kind, capabilities, cost_model, endpoint, policy,
    grounding: GroundingContext,  # Current presence
    coherence_index: float        # Computed CI
)
```

### Sessions 95/129 Emotional IRP

The autonomous sessions created `EmotionalIRPExpert` with metabolic state. This IS grounding:

```python
# Session 95/129 emotional state
emotional_state: EmotionalStateAdvertisement
  metabolic_state: WAKE | FOCUS | REST | DREAM | CRISIS
  emotional_state: {curiosity, frustration, engagement, progress}
  capacity_ratio: float
  accepting_tasks: bool

# Maps directly to grounding
grounding.capabilities.resource_state = derived_from(emotional_state)
```

---

## Implementation Priority

1. **Phase 1**: Add grounding edge type to MRH (Web4 core)
2. **Phase 2**: Implement CI calculation (Web4 core)
3. **Phase 3**: Integrate with SAGE IRP (HRM)
4. **Phase 4**: Federation coherence (multi-machine SAGE)

---

## Key Insight

Grounding unifies several concepts we've been developing:
- **Emotional/metabolic state** (Sessions 95/129) → capability grounding
- **Hardware attestation** (P0 blocker) → identity grounding
- **Federation sync** (Thor/Legion/Sprout) → relational grounding
- **Activity patterns** (SNARC) → temporal grounding

The proposal formalizes these into a single coherent framework.

---

## Files

- **Proposal**: `/proposals/MRH_GROUNDING_PROPOSAL.md`
- **HRM Brief**: `/HRM/sage/docs/AUTO_SESSION_BRIEF_MRH_GROUNDING.md`
- **Private Context**: `/private-context/moments/2025-12-27-mrh-grounding-proposal.md`
