# R6 Implementation Guide

## Overview

The R6 framework (Rules + Role + Request + Reference + Resource → Result) is implemented across multiple projects with different purposes and levels of enforcement.

## Implementation Tiers

### Tier 1: Observational (Open Source)
**Projects**:
- `web4/claude-code-plugin` (Python, standalone)
- `moltbot/extensions/web4-governance` (TypeScript, moltbot plugin)

Purpose: Audit trail without authorization overhead. Safe for public adoption.

```
R6 Components (Lite):
├── Rules: preferences only (audit_level)
├── Role: session_token + binding type
├── Request: tool, category, target, input_hash
├── Reference: session_id, prev_r6, chain_length
├── Resource: optional estimates
└── Result: status, output_hash, error, durationMs (in after_tool_call)
```

**Characteristics**:
- No approval workflow - records everything
- No ATP tracking
- No trust tensor updates
- Hash-linked JSONL audit chain with SHA-256 provenance verification
- `before_tool_call` hook surface ready for policy enforcement (Tier 1.5)
- TypeScript implementation (moltbot), Python implementation (standalone)

**Moltbot Integration**:
- Typed `before_tool_call`/`after_tool_call` hooks wired into the agent tool pipeline
- web4-governance plugin uses `after_tool_call` for R6 audit records
- Hooks enable both observation and policy-engine enforcement
- See: `moltbot/extensions/web4-governance/ARCHITECTURE.md`

### Tier 2: Authorization (Proprietary)
**Project**: `hardbound/hardbound-core`

Purpose: Full governance with role-based access control and approval workflows.

```
R6 Components (Full):
├── Rules: applicable_rules from policy engine
├── Role: actor_lct, actor_role, team_lct
├── Request: action_type, target, description, rationale, success_criteria
├── Reference: prev_bundle_id, related_requests, context_notes
├── Resource: atp_estimate, atp_actual, resource_requirements
└── Result: status, success, reason, atp_consumed, trust_delta, coherence, bundle_id
```

**Characteristics**:
- Requires admin approval for actions
- Role-based permissions (admin, developer, reviewer, viewer)
- ATP tracking and consumption
- Trust tensor (T3) updates
- Includes learnings, surprises, recommendations
- Rust implementation with PyO3 bindings

### Tier 3: Training Evaluation
**Project**: `HRM/sage/raising/tracks/training`

Purpose: Structured evaluation of AI training exercises.

```
R6 Components (Training):
├── Rules: mode, success_criteria, allow_meta_cognitive
├── Role: lct, position, relationship_to, phase, permissions
├── Request: exercise_type, prompt, intent, expected_pattern, parameters
├── Reference: previous_session, skill_track, session_exercises_so_far
├── Resource: model, atp_budget, context_window, temperature
└── Result: status, mode_detection, quality, meta_cognitive signals, t3_updates
```

**Characteristics**:
- Operational modes (conversation, refinement, philosophical)
- Training roles (learning_partner, practice_student, skill_practitioner)
- Meta-cognitive detection (clarification requests, modal awareness)
- T3 trust tensor integration
- Python implementation

## R6Status States

The three blocks below are **distinct per-tier lifecycles**, not one shared state machine — each tier/product defines its own status vocabulary. These tier-internal states are separate from the canonical R6 **Result** status set `{success, failure, error}` defined in `r6-framework.md` §7; e.g. the Hardbound `Approved`/`Rejected`/`Completed`/`Failed` tokens are a product-specific approval lifecycle, not canonical R6 Result statuses.

### Hardbound (Authorization)
```
Pending → InProgress → Approved/Rejected → Completed/Failed
                    ↳ Cancelled (by requester)
```

### Web4 Plugin (Observational)
```
(implicit) → request_created → result_recorded
```

### SAGE (Training Evaluation)
```
(implicit) → include/exclude/review (evaluation outcome)
```

## Trust Integration

| Tier | Trust Model |
|------|-------------|
| Observational | Relying party decides (no built-in trust) |
| Authorization | T3 tensor (competence, reliability, integrity) |
| Training | T3 tensor with developmental trajectory |

## Upgrade Path

Organizations can adopt progressively:

1. **Start**: Web4 plugin (observational audit trail)
2. **Grow**: Hardbound (add authorization + trust)
3. **Extend**: Custom policy engine integration

The audit trail format is compatible across tiers - Tier 1 records can be imported into Tier 2/3 systems.

## ID Formats

> These are **illustrative implementation-specific formats**, not canonical Web4 identifier schemes. The canonical identifier grammar is the W4ID form defined in `data-formats.md`; the formats below show how individual tier implementations label their own records.

| Context | Format | Example |
|---------|--------|---------|
| R6 Request | `r6:{uuid8}` | `r6:f8e9a1b2` |
| Audit Record | `audit:{uuid8}` | `audit:f8e9a1b2` |
| Session Token | `web4:session:{hash12}` | `web4:session:bc8332c04ca5` |
| LCT (Hardbound) | `lct:web4:{type}:{id}` | `lct:web4:root:abc123` |

## Security Considerations

See: `r6-security-analysis.md` for attack vectors and mitigations.

## References

- R6 Framework (normative): `r6-framework.md`
- Web4 Spec: `web4-standard/README.md`
- Hardbound: `hardbound/README.md`
- Moltbot Plugin: `moltbot/extensions/web4-governance/ARCHITECTURE.md`
- SAGE Training: `HRM/sage/raising/tracks/training/README.md`
