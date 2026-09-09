# Web4: Executive Summary

## The problem

AI is moving from producing information to taking consequential actions: editing code, moving money, operating infrastructure, coordinating with other agents and acting on behalf of people and organizations.

The missing layer is not another model. It is **accountability infrastructure**.

A relying party needs to answer, for each consequential act:

- Who is acting?
- Under whose authority?
- What law or policy applies?
- What evidence supports the action?
- What has this entity done before?
- Was the decision witnessed and can it be audited later?

Today's systems usually answer those questions with platform-local permissions, bearer credentials, logs and policy engines that do not compose across vendors or organizations.

## The Web4 thesis

**Trust should be computed from witnessed evidence, in context, by the party doing the relying.**

Web4 is an open substrate for making that possible. An acting entity can carry persistent identity, scoped role authority, the governing law consulted for an act, contextual trust evidence and a witnessed history. The relying party remains sovereign over whether that evidence is sufficient for the stakes.

Web4 does not define one universal policy. It makes a society's chosen policy explicit, machine-readable and auditable.

## The stack

### Web4 - open standard and primitives

The protocol layer defines:

- **LCT identity/presence** - persistent, non-transferable, witnessable entity identity
- **T3/V3** - contextual trust/value tensors
- **MRH** - relevance/context boundaries
- **R6/R7** - action and accountability grammar
- **ATP/ADP** - society-defined resource accounting
- **Societies, roles and law** - composable authority under signed machine-readable rules
- **Witnessed ledgers** - durable evidence of consequential acts and governance decisions

`web4-core` 0.3.0 is published on crates.io and PyPI. `web4-trust-core` / `web4-trust` 0.2.0 are published, and `web4-core` 0.4.0 is in source on `main`.

### Hestia - local governance for humans and agents

[Hestia](https://github.com/dp-web4/hestia) is the open local runtime at the person/agent boundary. Agents from different vendors can operate on one machine under one law, with scoped authority, a vault, witnessed actions, human escalation and trust derived from the record rather than self-reported.

The current open assurance grade is **A1**: cooperative and tamper-evident. It is useful for governance, attribution and stopping ordinary mistakes, but it is not containment against a determined same-UID adversary. Higher assurance requires stronger process/OS isolation and relying parties that demand policy-signed acts.

### Hub - society and community governance

[Hub](https://github.com/dp-web4/4-hub) is the society runtime. It packages membership, seven base roles, signed law, sealed member channels and an append-only witnessed ledger into a small Rust daemon.

A Hub can represent a team, community, company, chapter or other self-governing group. Hestia governs the local member/agent boundary; Hub governs the society boundary.

### Hardbound - enterprise assurance

**Hardbound** is Metalinxx's proprietary enterprise tier. Its role is to raise the assurance grade with hardware-bound identity, stronger fail-closed enforcement and audit-ready evidence packaging for regulated or high-stakes deployments.

### SAGE - persistent cognition research

[SAGE](https://github.com/dp-web4/SAGE) is the research environment that carries the same identity and governance ideas into persistent local agents with memory, context, sensors, learning and eventually physical effectors. It is research-stage, not the product layer.

## What is real today

- Published Rust and Python Web4 packages.
- A running Hub reference society with roles, law, sealed channels and a witnessed ledger.
- A running Hestia daemon used daily across multiple agent vendors.
- Exercised human escalation and built peer-arbitration paths.
- Trust derived from the witnessed chain rather than asserted by the acting agent.
- A heterogeneous eight-machine research fleet that operates through the same governance machinery it develops.

## What is not being claimed

- The open Hestia A1 gate is **not adversary-proof containment**.
- Web4 is **not a finished standard**; parts of DID/EUDI interoperability, conformance, federation and higher-assurance enforcement are still building.
- A published implementation is not the same as a production-certified enterprise deployment.
- No benchmark result substitutes for the security and interoperability work above.

This distinction is intentional. The project keeps **measured**, **implemented but unexercised**, **specified**, and **aspirational** states separate in [STATUS.md](../../STATUS.md).

## Why this can matter commercially

The enterprise problem is becoming concrete: organizations want the productivity of autonomous agents without giving up accountability.

The Web4 stack is aimed at the layer underneath agent products:

1. **Identity** that survives model/vendor changes.
2. **Authority** that is scoped and revocable.
3. **Law** that is explicit and machine-readable.
4. **Evidence** that travels with consequential acts.
5. **Witnessing** that makes later audit possible.
6. **Trust** that is contextual and recomputable by the relying party.

That creates a natural split between an open protocol ecosystem and a proprietary enterprise assurance layer. The open standard creates interoperability and avoids vendor lock-in; Hardbound can monetize higher-assurance enforcement, hardware roots, deployment, evidence export and enterprise integration.

## The strategic bet

If agentic AI becomes infrastructure, then **trust and authority must become infrastructure too**.

The long-term target is not a dashboard that says an agent is "safe." It is a network in which humans, agents, services and organizations can prove enough about identity, authority, law and past conduct for another party to make its own decision.

That is what "trust is computable" means here.

## Historical ARC-AGI-3 note

A spring-2026 SAGE/ARC harness produced a published 94.85% scorecard using Claude Opus 4.6. It remains a useful historical research artifact, but it is **not a current competitive claim and no longer serves as Web4's primary proof point**. The run used a frontier model and engine-level/public-game affordances outside strict competition play. Current competition-legal local-model work is well behind the leaders.

The durable lesson was methodological: changing the structure around a model can materially change behavior. The current program is focused on making that structure persistent, governable, learnable and operationally trustworthy.

## Five-minute diligence path

1. [STATUS.md](../../STATUS.md) - current calibration.
2. [Publication proof](../proof/PUBLISHED.md) - released packages and history.
3. [Hub](../../hub/) - running society reference implementation.
4. [Hestia](https://github.com/dp-web4/hestia) - running local governance layer and assurance limits.
5. [SAGE](https://github.com/dp-web4/SAGE) - persistent cognition research.
6. [Web4 standard](../../web4-standard/core-spec/) - normative protocol work.

---

**Web4: trust computed from witnessed evidence, under explicit authority and law.**
