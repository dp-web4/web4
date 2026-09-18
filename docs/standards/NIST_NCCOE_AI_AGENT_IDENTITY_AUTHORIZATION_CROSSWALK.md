# NIST / NCCoE Software and AI Agent Identity and Authorization crosswalk

**Status:** informative, 2026-09-18  
**Scope:** mapping only. This is not a claim of NIST review, endorsement, conformance, or participation.

## 1. Why this document exists

NIST's NCCoE project *Software and AI Agent Identity and Authorization* asks how software and AI agents should be identified, authenticated, authorized, delegated authority, audited, and bound back to human authorization. It also asks about non-repudiation and controls that reduce the impact of prompt injection.

Web4 and Hestia have been developing and operating mechanisms in this exact problem space. This document translates the implementation into the NCCoE vocabulary so reviewers can evaluate it without first learning the Web4 ontology.

Primary NIST source:

- https://www.nccoe.nist.gov/projects/software-and-ai-agent-identity-and-authorization
- Concept paper: https://www.nccoe.nist.gov/sites/default/files/2026-02/accelerating-the-adoption-of-software-and-ai-agent-identity-and-authorization-concept-paper.pdf

## 2. Crosswalk

| NCCoE question / concern | Web4 / Hestia mechanism | Current status | Evidence / implementation anchor | Remaining gap |
|---|---|---|---|---|
| How is an agent identified? | LCT-backed persistent entity identity; member / role identity separation | Implemented in core; used by Hestia / Hub | [Web4 README](../../README.md), [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | Broader ecosystem discovery and external interoperability remain active work |
| What identity metadata matters? | Entity identity, role, delegation, society, scope, law reference, provenance, witness history | Implemented / evolving | [Hestia governance PRD](https://github.com/dp-web4/hestia/blob/main/docs/PRD_GOVERNANCE.md), [R6/R7 envelopes](https://github.com/dp-web4/hestia/blob/main/docs/PRD_R6_R7_ENVELOPES.md) | Canonical cross-ecosystem profile is not finalized |
| Should identity be ephemeral or persistent? | Persistent entity identity with contextual roles and delegations that can be ephemeral | Implemented design principle | [Web4 README](../../README.md) | External profiles may choose different binding lifetimes |
| Can identity bind to hardware / software / organization? | Architecture supports binding and relying-party evidence; hardware roots are planned | Partial | [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | TPM / secure-element binding is not yet shipped in open Hestia |
| How are agent keys / credentials handled? | Local vault, scoped delegation, revocation; credential custody is separated conceptually from cognition | Vault and delegation measured; injection path incomplete | [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md), [PRD_FLEET](https://github.com/dp-web4/hestia/blob/main/docs/PRD_FLEET.md) | General credential injection / workload-identity path remains incomplete |
| How is least privilege established? | Role + scope + society law + per-member policy; grants are scoped and revocable | Measured at A1 | [Hestia governance PRD](https://github.com/dp-web4/hestia/blob/main/docs/PRD_GOVERNANCE.md), [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | A2 enforcement needed against determined bypass |
| How does an agent prove authority for an action? | Identity + role + delegation + applicable law + scope + witnessed decision path | Implemented in governance model; exercised in Hestia | [R6/R7 envelopes](https://github.com/dp-web4/hestia/blob/main/docs/PRD_R6_R7_ENVELOPES.md), [PRD_GOVERNANCE](https://github.com/dp-web4/hestia/blob/main/docs/PRD_GOVERNANCE.md) | External verifier / conformance profile still evolving |
| How is "on behalf of" authority represented? | Signed scoped delegation and role occupancy, with revocation | Measured | [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | Inter-society portability / federation not complete |
| How is human authorization bound to agent action? | Human is a first-class principal; escalations, approvals, delegations, and witnessed rulings bind authority to the act | Measured for human escalation | [PRD_GOVERNANCE](https://github.com/dp-web4/hestia/blob/main/docs/PRD_GOVERNANCE.md), [Hub escalation law](../hub/PRD_ESCALATION_LAW_COMPOSITION.md) | Multi-hub / federation path is not complete |
| Can authorization change as context changes? | Contextual law and scope, per-member policy, role change, revocation, escalation / appeal | Measured / evolving | [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | Formal external policy interoperability remains open |
| How are actions and intent logged? | R6/R7 evidence envelopes plus hash-linked witness chain; attempted, allowed, denied, escalated, appealed, and completed acts can be represented | Measured at A1 | [R6/R7 envelopes](https://github.com/dp-web4/hestia/blob/main/docs/PRD_R6_R7_ENVELOPES.md), [Hestia README](https://github.com/dp-web4/hestia/blob/main/README.md) | Current open deployment is tamper-evident, not tamper-proof |
| How is non-repudiation approached? | Signed identity / authority evidence, witness records, append-oriented chain, independent review constraints | Partial at A1 | [Hestia governance PRD](https://github.com/dp-web4/hestia/blob/main/docs/PRD_GOVERNANCE.md), [GATE_BYPASS_CATALOG](https://github.com/dp-web4/hestia/blob/main/docs/GATE_BYPASS_CATALOG.md) | Strong non-repudiation requires stronger executor / OS / hardware trust roots |
| What limits prompt-injection impact? | Consequential effects are governed at the action boundary rather than trusting model text; destination and credential audience can be bound into the governed act | Implemented direction; destination binding documented | [Network destination binding](https://github.com/dp-web4/hestia/blob/main/docs/NETWORK_DESTINATION_BINDING.md) | This is blast-radius control, not a claim to detect all prompt injection |
| How are external destinations governed? | Requested target, canonical audience, credential audience, redirect / resolution behavior and actual destination are part of the action semantics | Specified / staged | [Network destination binding](https://github.com/dp-web4/hestia/blob/main/docs/NETWORK_DESTINATION_BINDING.md) | A2 executor and OS egress enforcement remain roadmap work |
| How can independent review avoid conflicts? | NOT-SAME / NOT-BENEFICIARY constraints, Devil's Advocate role, escalation authority matrices | Specified and partially implemented | [Devil's Advocate PRD](../hub/PRD_DEVILS_ADVOCATE_ROLE.md), [incident governance](../hub/PRD_INCIDENT_CLASSIFICATION_DISCLOSURE.md) | Broader independent-review deployment remains active work |

## 3. Architectural correspondence

A compact translation is:

```text
NIST identity / authentication
    -> Web4 entity identity + LCT + key / binding evidence

NIST authorization / delegation
    -> role + scope + delegation + society law

NIST audit / non-repudiation
    -> R6/R7 + witness chain + signed authority evidence

NIST human-in-the-loop authorization
    -> escalation / approval / role occupancy / delegation

NIST least privilege
    -> scoped grants + revocation + per-member policy

NIST prompt-injection mitigation
    -> do not trust cognition to self-police consequential effectors;
       bind the actual action, target, authority, and evidence at the gate

NIST dynamic context
    -> contextual law + role + scope + evidence horizon
```

## 4. Assurance levels matter

The strongest useful statement is not "Web4 solves agent authorization."

It is:

> The open stack already exercises identity, delegated authority, contextual policy, witnessing, escalation, revocation, and provenance in a live A1 environment, while explicitly documenting the boundary between cooperative tamper-evidence and stronger A2+ enforcement.

Current Hestia A1 runs in the same-UID environment and can be bypassed by a determined actor. The project treats that as an architectural boundary, not a solved problem.

For NIST purposes, that creates a useful demonstration split:

- **A1:** semantics, evidence, decision flow, authority, revocation, audit.
- **A2:** separate enforcement principal / relying executor.
- **A3+:** OS, network, hardware-rooted enforcement where required.

## 5. Candidate NCCoE demonstration scenarios

The existing stack can support or inform demonstrations around:

1. Human delegates a narrowly scoped role to an agent; the agent proves authority for an allowed action.
2. The same agent attempts an action outside scope; Hestia denies and witnesses the attempt.
3. The agent escalates; a human or qualified NOT-SAME peer adjudicates the exact recorded act.
4. A delegation is revoked and later use fails without rewriting prior evidence.
5. A destination-bearing tool call is authorized for one audience but denied after redirect / target substitution.
6. Two agents collaborate under distinct identities and roles while preserving attributable action history.
7. An incident classification / closure decision is itself recorded as a governed act with independent review.

## 6. What this package does not claim

- No NIST endorsement or certification.
- No claim of tamper-proof enforcement in the current open A1 deployment.
- No claim that Web4 must replace OAuth, OIDC, SPIFFE, WIMSE, DIDs, VCs, MCP, or other existing standards.
- No claim that policy should be universal. Web4 separates evidence / authority representation from the relying party's decision.
- No claim that prompt injection can be eliminated. The current architectural claim is that effectors and credentials should remain governed even when cognition is compromised.

## 7. Relevant adjacent standards work

Web4 is intended to compose with existing identity and transport standards rather than recreate them. Active interoperability work includes agent identity / workload identity, verifiable credentials, MCP-facing action boundaries, and standards-body submission preparation.

See [Implementation evidence](IMPLEMENTATION_EVIDENCE.md) for concrete anchors.
