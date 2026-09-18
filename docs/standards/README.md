# Standards and public-sector review entry point

**Status:** informative mapping package, 2026-09-18  
**Purpose:** make the existing Web4 / Hestia implementation legible to standards bodies, public-sector reviewers, implementers, and independent researchers.

This directory is the shortest path into the project if your vocabulary is:

- AI agent identity
- agent authentication
- agent authorization
- delegated authority
- agent provenance
- runtime governance
- non-repudiation
- auditability
- allow / deny / revoke
- least privilege
- agent discovery
- multi-agent governance
- prompt-injection blast-radius control
- tamper-evident action records
- NIST
- NCCoE
- CAISI
- AI Agent Standards Initiative

Web4 is not presented here as a policy recommendation. These documents map public requirements and open questions onto an existing open implementation so reviewers can inspect what is implemented, what is only specified, and what remains unbuilt.

## Start here

1. [NIST / NCCoE AI Agent Identity and Authorization crosswalk](NIST_NCCOE_AI_AGENT_IDENTITY_AUTHORIZATION_CROSSWALK.md)
2. [Implementation evidence index](IMPLEMENTATION_EVIDENCE.md)
3. [Stop Rogue AI Act technical crosswalk](STOP_ROGUE_AI_ACT_TECHNICAL_CROSSWALK.md)
4. [One-page technical introduction](OUTREACH_ONE_PAGER.md)

## Stack in standards vocabulary

| Layer | Standards-facing description |
|---|---|
| **Web4** | Open identity, authority, provenance, evidence, trust, law, and federation primitives |
| **Hestia** | Local runtime governance and evidence plane for humans and agents |
| **Hub** | Society / multi-agent coordination, delegation, discovery, escalation, and federation layer |
| **SAGE** | Persistent agent architecture consuming the same identity and governance primitives |

The layers are separable. A reviewer does not need to adopt the whole Web4 ontology to inspect or reuse a mechanism.

## Assurance statement

Current open Hestia deployment is **A1**: cooperative and tamper-evident, not tamper-proof against a determined same-UID actor. Higher-assurance A2 isolation and relying-party / OS enforcement are roadmap work.

That distinction is intentional and should be preserved in any citation or standards discussion.

## Primary public references

- NIST / NCCoE: *Software and AI Agent Identity and Authorization*  
  https://www.nccoe.nist.gov/projects/software-and-ai-agent-identity-and-authorization
- NIST / CAISI: *AI Agent Standards Initiative*  
  https://www.nist.gov/artificial-intelligence/ai-agent-standards-initiative
- NCCoE technical collaboration process  
  https://www.nccoe.nist.gov/get-involved/collaborate-us-technical-contributions
- Stop Rogue AI Act sponsor description, 2026-09-09  
  https://gottheimer.house.gov/posts/release-gottheimer-introduces-bipartisan-bill-to-stop-rogue-ai-agents-and-keep-people-in-control

## Reviewer principle

The project should be judged by inspectable artifacts, not project vocabulary.

Where the implementation does not yet satisfy a requested assurance property, the crosswalk says so.
