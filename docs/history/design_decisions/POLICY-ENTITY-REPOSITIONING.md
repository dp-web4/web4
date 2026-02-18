# Policy Entity Repositioning: SAGE IRP as Implementation Backbone

**Status**: Design Decision v1.0
**Date**: 2026-02-18
**Author**: Dennis + Claude (Opus 4.6)
**Origin**: SOIA convergence discovery (LinkedIn conversation with Renee Karlstrom)

---

## Decision

**PolicyEntity is an IRP-backed entity type whose evaluation engine is SAGE's IRP plugin architecture.**

PolicyEntity gains a runtime implementation (PolicyGate) that follows the IRP contract: init_state / step / energy / project / halt. The existing `PolicyEntity.evaluate()` method becomes the energy function for an IRP plugin. This positions Policy Entity not as a standalone configuration object but as a first-class participant in SAGE's consciousness loop.

PolicyEntity should also be elevated to the 15th primary entity type in the Web4 entity taxonomy.

---

## Context

### The Convergence Discovery

In February 2026, a conversation with Renee Karlstrom (independent SOIA researcher) surfaced a structural convergence between SOIA (Self-Optimizing Intelligence Architecture) and SAGE's IRP stack:

| SOIA Component | Function | SAGE Equivalent |
|---|---|---|
| SRC (Self-Referential Core) | Regulatory loop | Consciousness loop + metabolic states |
| MTM (Memory Transductive Module) | Selective memory | SNARC experience buffer |
| MORIA (Internal Temporal Axis) | Trajectory persistence | Sleep-cycle consolidation |

The near-exact mapping revealed that Policy Entity does not need to be invented from scratch. SAGE's IRP spine, built for embodied AI cognition, serves equally as exo-centered conscience for policy entities. The relationship between HRM/SAGE and Web4 had been implicit until this third perspective collapsed them into the same coordinate system.

### Existing Infrastructure

**Already built in Web4** (`simulations/policy_entity.py`, 921 lines):
- PolicyEntity with entity IDs (`policy:<name>:<version>:<hash>`), witnessing, hash-tracking
- PolicyConfig with rules, presets (permissive, audit-only, enterprise-safety, strict)
- PolicyEvaluation with decision/reason/constraints/ATP cost
- 6 attack-class mitigations (CQ-1 through CQ-6)
- R6 integration, trust threshold matching, rate limiting

**Already built in SAGE** (`sage/irp/`):
- IRP plugin contract: init_state / step / energy / project / halt
- 15+ working plugins (vision, language, control, memory, TTS)
- Trust metrics from convergence quality (monotonicity, dE variance, convergence rate)
- ATP-budgeted execution through HRMOrchestrator
- Experience buffer with SNARC 5D salience scoring

**Not built**: The bridge between them.

---

## Consequences

### What Changes

1. **PolicyEntity gains metabolic awareness**. The `PolicyEvaluation` dataclass adds an `accountability_frame` field that reflects the agent's metabolic state at evaluation time (NORMAL for WAKE/FOCUS, DEGRADED for REST/DREAM, DURESS for CRISIS). A `duress_context` field captures crisis state details.

2. **PolicyEntity enters the entity taxonomy**. Currently PolicyEntity exists in the simulations code but is not listed in `entity-types.md`. It will be added as the 15th primary entity type with Mode: Responsive/Delegative and Energy Pattern: Active.

3. **Policy evaluation becomes IRP-native**. PolicyGate (an IRP plugin in HRM) wraps `PolicyEntity.evaluate()` as its energy function. This gives policy evaluation the same convergence trust metrics as all other IRP plugins.

4. **CRISIS mode changes the audit frame, not the rules**. Under CRISIS, policy rules are evaluated identically. The difference is in how the decision is recorded -- with duress context that acknowledges consequences are beyond the agent's control.

### What Does NOT Change

- `PolicyEntity.evaluate()` API remains identical. Existing callers are unaffected.
- Enterprise presets, attack mitigations, and rule specificity logic are preserved.
- Web4's trust stack (web4-core, web4-trust-core) is not modified.
- PolicyGate is an optional SAGE plugin. Web4 PolicyEntity works without SAGE.

### Backward Compatibility

- The `accountability_frame` field defaults to `"normal"`, making it backward-compatible.
- The `duress_context` field defaults to `None`.
- Existing code that does not check these fields continues working.

---

## Repository Partition

**Principle**: HRM owns the engine; Web4 owns the ontology.

| Artifact | Home Repo | Rationale |
|---|---|---|
| PolicyGate IRP plugin | HRM (`sage/irp/policy_gate.py`) | It is an IRP plugin following HRM's IRPPlugin contract |
| AccountabilityFrame enum | HRM (`sage/core/metabolic_states.py`) | It is a property of metabolic state, which lives in HRM |
| PolicyEntity ontological spec | Web4 (`web4-standard/core-spec/entity-types.md`) | Entity taxonomy is Web4's domain |
| `accountability_frame` field on PolicyEvaluation | Web4 (`simulations/policy_entity.py`) | PolicyEvaluation is a Web4 data structure |
| SOIA-SAGE mapping document | HRM (`sage/docs/SOIA_IRP_MAPPING.md`) | SOIA is a research concept mapped through SAGE machinery |
| Integration guide | Web4 (`docs/how/SAGE-POLICY-ENTITY-INTEGRATION.md`) | Integration docs live in how/ |

---

## Migration Path

### Phase 0: Documentation (this session)
Capture the insight. Write mapping documents and design decisions.

### Phase 1: PolicyGate skeleton + entity taxonomy update
Implement PolicyGate as an IRP plugin with `PolicyEntity.evaluate()` as energy function. Add PolicyEntity to entity taxonomy.

### Phase 2: Consciousness loop integration
Wire PolicyGate into SAGE's consciousness loop between memory update and effectors.

### Phase 3: CRISIS accountability
Add AccountabilityFrame to metabolic states. Add duress_context to PolicyEvaluation.

### Phase 4: Experience buffer integration
Policy decisions feed into SNARC scoring and experience buffer for DREAM consolidation.

### Phase 5+: Phi-4 Mini advisory, integration guide, bridge update.

---

## CRISIS Mode: The Accountability Argument

This design decision includes a specific position on CRISIS mode that must be documented clearly to prevent future misinterpretation.

CRISIS is fight-or-flight, operationalized. Both freeze (halt effectors) and fight (proceed with best available action) are valid responses. Neither is universally correct. Biology shows this clearly -- organisms that always freeze die when they should have fled; organisms that always fight die when they should have frozen.

**What CRISIS changes is the accountability equation.**

Under CRISIS, the entity says: "the consequences are not in my control, and whether I freeze or fight, what may come will come." The conscience (PolicyGate) still evaluates. It still records. But the record acknowledges duress.

This is structurally identical to the legal concept of duress: the action is still recorded, the actor is still identified, but the context of the decision is part of the record. Conscience does not vanish -- it shifts from "I chose this outcome" to "I responded under duress."

Do NOT implement CRISIS mode as "stricter policy" (which creates analysis paralysis when action is needed) or as "disable safety" (which removes accountability when it matters most). Implement it as honest accounting of the conditions under which the decision was made.

---

## References

- Karlstrom, R. "SOIA-Mother: An Adaptive Control Architecture for AI Cyberdefense, Governance, and Limits" (doi.org/10.5281/zenodo.18370968)
- SOIA-SAGE mapping: `github.com/dp-web4/HRM/sage/docs/SOIA_IRP_MAPPING.md`
- Convergence insight: `github.com/dp-web4/HRM/forum/insights/soia-sage-convergence.md`
- HRM-LCT Alignment (template): `docs/history/design_decisions/HRM-LCT-ALIGNMENT.md`
- Synthon framing: `github.com/dp-web4/HRM/forum/insights/synthon-framing.md`

---

**Version**: 1.0.0
**Status**: Design Decision
**Last Updated**: 2026-02-18

*"Policy Entity doesn't need to be invented. It needs to be repositioned."*
