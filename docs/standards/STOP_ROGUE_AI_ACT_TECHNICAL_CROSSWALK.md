# Stop Rogue AI Act technical crosswalk

**Status:** informative, 2026-09-18  
**Purpose:** map the sponsor-described technical requirements of the proposed Stop Rogue AI Act to existing Web4 / Hestia mechanisms and gaps.

This document is **not an endorsement or opposition statement** about the legislation. It is a technical feasibility / implementation mapping.

Primary sponsor description, 2026-09-09:

https://gottheimer.house.gov/posts/release-gottheimer-introduces-bipartisan-bill-to-stop-rogue-ai-agents-and-keep-people-in-control

The sponsor description says the proposal would direct NIST to develop standards / guidance for discovering, verifying, monitoring, and controlling AI agents, including:

1. continuous inventory;
2. verifiable identity and provenance;
3. real-time monitoring for behavior outside approved limits and related threats;
4. allow / deny / revoke control over access, actions, and interactions;
5. open / interoperable approaches rather than exclusive reliance on vendor self-attestation.

## Crosswalk

| Sponsor-described requirement | Existing Web4 / Hestia mechanism | Current state | Important limitation |
|---|---|---|---|
| Find and track agents | Persistent member / entity identities; Hestia member registry; Hub society membership | Local / society-level identity exists | General network-wide discovery of unknown agents is not solved |
| Verify who built / operates / stands behind an agent | Identity, role, delegation, society provenance, witness evidence | Core mechanisms implemented | External ecosystem attestation profile remains active work |
| Verifiable provenance rather than vendor assertion | Signed / witnessed authority and action evidence; relying party evaluates evidence | Implemented direction | Strength depends on root of trust and assurance level |
| Real-time monitoring | Hestia policy gate and witness chain observe governed acts | Measured in daily use | Does not imply visibility into bypassed A1 paths |
| Detect out-of-scope behavior | Scope / role / law checked at action boundary | Measured at A1 | A2 needed for stronger mandatory mediation |
| Prompt injection | Consequential effectors remain policy-gated even if cognition is compromised | Architectural mitigation | Not a universal prompt-injection detector |
| Data theft / unintended destination | Destination and credential audience can be bound into act semantics | Specified / staged | A2 executor / OS egress enforcement remains roadmap work |
| Allow an action | Policy decision path | Measured |
| Deny an action | Policy decision path + witnessed denial | Measured |
| Revoke authority | Scoped delegation revocation / policy change | Measured | Federation propagation remains incomplete |
| Control agent interactions | Hub / Hestia law, scope, channels, escalation | Partial / evolving | Multi-hub federation not complete |
| Human final authority where required | Human escalation / approval; society law can require human-only decisions | Measured / specified | Human authority is policy, not hard-coded universal law |
| Open and interoperable standards | Web4 protocol + open Hestia / Hub implementation; standards interoperability work | Active | No claim of current NIST conformance |

## Two distinctions that matter for implementation

### Discovery is not identity

Finding a process, network client, model session, or service does not prove who or what it is.

Web4 separates:

- **discovery:** something is present;
- **identity:** evidence for which entity it is;
- **authority:** evidence for what that entity may do;
- **provenance:** evidence for how the current act relates to operator, role, delegation, law, and prior events.

A federal standard will likely need all four.

### Monitoring is not control

A telemetry system can observe an agent while being unable to stop it.

The Hestia assurance model separates:

- A1: cooperative gate, tamper-evident;
- A2: enforcement outside the agent's own same-UID control;
- stronger OS / network / hardware-rooted enforcement as needed.

That distinction should remain explicit in any standards implementation.

## Candidate contribution to NIST

The project can contribute practical evidence around:

- entity vs role identity;
- scoped delegation and revocation;
- human / agent authority chains;
- witnessed allow / deny / escalate / appeal;
- provenance as an evidence graph rather than a vendor label;
- binding the actual destination / effect into authorization;
- independence constraints for reviewers and witnesses;
- honest assurance-level labeling.

See:

- [NIST / NCCoE crosswalk](NIST_NCCOE_AI_AGENT_IDENTITY_AUTHORIZATION_CROSSWALK.md)
- [Implementation evidence](IMPLEMENTATION_EVIDENCE.md)
