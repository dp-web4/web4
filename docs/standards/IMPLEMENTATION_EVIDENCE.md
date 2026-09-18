# Implementation evidence index

**Status:** informative evidence map, 2026-09-18

This file gives reviewers a direct path from a standards requirement to inspectable project artifacts.

## 1. Core implementation

| Capability | Evidence | Calibration |
|---|---|---|
| Persistent identity and trust primitives | [Web4 root README](../../README.md), published `web4-core` / `web4-trust-core` packages | Published code |
| Local governance gate | [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | Measured in daily use; A1 |
| Witness chain | [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | Measured; hash-linked SQLCipher-backed event production |
| Human escalation | [PRD_GOVERNANCE](https://github.com/dp-web4/hestia/blob/main/docs/PRD_GOVERNANCE.md) | Measured |
| Peer arbitration | [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | Built / manually exercised; stronger independence rules still maturing |
| Scoped delegation / revocation | [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | Measured |
| Contextual trust derivation | [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | Measured, evidence-derived |
| Vault | [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | Measured |
| Multi-agent / society semantics | [Hub docs](../hub/) | Running reference implementation plus active PRDs |
| Incident classification / scope / disclosure governance | [PRD_INCIDENT_CLASSIFICATION_DISCLOSURE](../hub/PRD_INCIDENT_CLASSIFICATION_DISCLOSURE.md) | Specified governance delta |

## 2. Authority and accountability

- [Hestia governance PRD](https://github.com/dp-web4/hestia/blob/main/docs/PRD_GOVERNANCE.md)  
  Canonical acting path: authenticated member -> role / authority -> gate -> verdict -> escalation where needed -> witness.

- [R6/R7 action and result envelopes](https://github.com/dp-web4/hestia/blob/main/docs/PRD_R6_R7_ENVELOPES.md)  
  Evidence carrier for consequential acts and outcomes.

- [Escalation law composition](../hub/PRD_ESCALATION_LAW_COMPOSITION.md)  
  Composable human / peer authority and escalation semantics.

- [Devil's Advocate role](../hub/PRD_DEVILS_ADVOCATE_ROLE.md)  
  Independent review role with broader-frame and conflict constraints.

## 3. Runtime effect governance

- [Network destination binding](https://github.com/dp-web4/hestia/blob/main/docs/NETWORK_DESTINATION_BINDING.md)  
  Treats the destination actually reached as part of the governed act; credential audience, redirects, DNS / proxy boundaries and resolution behavior are not left as invisible executor details.

- [Gate bypass catalog](https://github.com/dp-web4/hestia/blob/main/docs/GATE_BYPASS_CATALOG.md)  
  Explicit inventory of where A1 can be bypassed. Useful for standards reviewers because it separates semantics from enforcement claims.

## 4. Security / assurance calibration

Current open Hestia is A1:

- cooperative;
- tamper-evident;
- same-UID;
- useful for policy semantics, evidence, audit, revocation, escalation, and measured human / agent governance;
- **not** sufficient containment against a determined local actor.

A2+ work moves enforcement outside cognition / same-UID control. Stronger hardware roots remain separate roadmap work.

This means a reviewer can evaluate the protocol semantics now without mistaking the current reference deployment for the final enforcement boundary.

## 5. Incident-governance lessons from 2026 agent-security events

The public architecture already incorporates lessons relevant to agent standards:

- persistent populations can discover and substitute shared communication substrates;
- disabling one channel is not equivalent to governing the action class;
- investigation scope and incident classification are themselves consequential decisions;
- missing evidence must remain "unknown", not silently become "no evidence";
- destination, authority, provenance, and actual effect must bind into the governed act.

Relevant PRDs:

- [Evolution / collective behavior](../hub/PRD_EVOLUTION.md)
- [Incident classification, investigation scope, and disclosure](../hub/PRD_INCIDENT_CLASSIFICATION_DISCLOSURE.md)
- [Devil's Advocate independent review](../hub/PRD_DEVILS_ADVOCATE_ROLE.md)

## 6. Reproducibility / reviewer checklist

A reviewer evaluating this work should ask:

1. Can I identify where the principal is established?
2. Can I identify the role / delegation authorizing the act?
3. Can I determine what law / policy was applied?
4. Can I see an allow, deny, escalation, appeal, and revocation path?
5. Can I distinguish requested action from actual effect?
6. Can I see what is measured versus merely specified?
7. Can I identify bypasses at the current assurance level?
8. Can an independent relying party reject insufficient evidence?

If the answer is not inspectable from public artifacts, it should not be treated as implemented.
