# Web4: Verifiable Presence for AI

[![crates.io: web4-core](https://img.shields.io/crates/v/web4-core?label=crates.io%20web4-core)](https://crates.io/crates/web4-core)
[![crates.io: web4-trust-core](https://img.shields.io/crates/v/web4-trust-core?label=crates.io%20web4-trust-core)](https://crates.io/crates/web4-trust-core)
[![PyPI: web4-core](https://img.shields.io/pypi/v/web4-core?label=PyPI%20web4-core)](https://pypi.org/project/web4-core/)
[![PyPI: web4-trust](https://img.shields.io/pypi/v/web4-trust?label=PyPI%20web4-trust)](https://pypi.org/project/web4-trust/)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/License-AGPL--3.0--or--later-blue.svg)](LICENSE)

> **AI is already taking consequential actions. Identity, authority and accountability have not caught up.**

**Web4 is the open substrate for agent accountability: persistent identity, contextual trust, scoped authority, witnessed action and machine-readable law.**

The design goal is not a platform that decides who is trusted. It is a protocol in which an acting entity can bring evidence of **who it is, under whose authority it acts, what law applies, and what happened before**, while the relying party remains sovereign over whether that evidence is sufficient for the context and stakes.

**Status:** research-stage, but no longer only a specification. Core packages are published. The [Hub](hub/) and [Hestia](https://github.com/dp-web4/hestia) reference deployments are running on the live fleet. Higher-assurance enforcement, broader standards interoperability and conformance remain active work. Read [STATUS.md](STATUS.md) for the calibrated split between shipped, implemented, specified and aspirational.

## The stack

| Layer | Role | Current state |
|---|---|---|
| **Web4** | Open protocol and primitives for identity, trust, action, law, witnessing and federation | Core implementation published; standard draft in places |
| **[Hestia](https://github.com/dp-web4/hestia)** | Local governance at the human/agent boundary | Running daily; multi-vendor; **A1** assurance |
| **[Hub](hub/)** | Society/community runtime | Running Rust reference implementation |
| **Hardbound** | Metalinxx enterprise assurance tier | Private/proprietary; building |
| **[SAGE](https://github.com/dp-web4/SAGE)** | Persistent cognition and embodiment research under the same identity/governance model | Public architecture + active research |

The layers are intentionally separable. Web4 is the substrate. Hestia and Hub are open operational layers at different boundaries. Hardbound raises the assurance grade for enterprise deployments. SAGE explores what persistent, learning agents look like when identity and governance are first-class rather than bolted on afterward.

## Why Web4 exists

Most current systems answer one of these questions:

- **Who holds this credential?**
- **What does this platform permit?**

Agentic AI increasingly needs a third:

> **Should I trust this entity to perform this action, here, now, under these rules, given its evidence and history?**

Web4 makes the ingredients of that decision machine-readable:

- **Identity:** a persistent entity presence, not a disposable session label.
- **Authority:** roles and delegations with explicit scope.
- **Law:** signed rules that govern consequential acts.
- **Witnessing:** durable records of what was attempted, allowed, denied, escalated and completed.
- **Trust:** contextual evidence derived from behavior, not a self-reported score.
- **Relying-party sovereignty:** the receiver decides how much evidence is enough.

## Core primitives

```text
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

- **LCT - Linked Context Token:** persistent, non-transferable, witnessable entity presence.
- **T3 / V3:** contextual trust and value tensors.
- **MRH - Markov Relevancy Horizon:** the boundary within which evidence is relevant.
- **R6 / R7:** action and accountability grammar around consequential acts.
- **ATP / ADP:** society-defined resource accounting. ATP is a unit of account, not a protocol currency.
- **Societies, roles and law:** composable authority under signed machine-readable rules.
- **MCP:** the inter-society I/O membrane for tools/resources/actions.
- **RDF:** the extensible semantic substrate tying identities, roles, trust and context together.

Web4 does **not** dictate one policy. A society writes its own law. The protocol requirement is that the law, authority and resulting acts are inspectable and auditable.

## What works today

### Published core

Published packages:

```bash
pip install web4-core
pip install web4-trust
```

Rust:

```toml
[dependencies]
web4-core = "0.3"
web4-trust-core = "0.2"
```

Current published versions:

- `web4-core` 0.3.0 on crates.io + PyPI
- `web4-trust-core` 0.2.0 on crates.io
- `web4-trust` 0.2.0 on PyPI
- `web4-core` 0.4.0 in source on `main`

See [docs/proof/PUBLISHED.md](docs/proof/PUBLISHED.md) for the publication trail.

### Hub: a running Web4 society

The [Hub](hub/) is a small Rust daemon that turns a community or organization into a sovereign Web4 society:

- LCT-pinned membership
- seven base roles
- signed machine-readable law
- sealed member-to-hub channels
- append-only witnessed ledger
- MCP, REST and admin surfaces
- governance decisions recorded as acts rather than disappearing into chat history

A standalone mirror is published at [dp-web4/4-hub](https://github.com/dp-web4/4-hub).

### Hestia: one local law across agent vendors

[Hestia](https://github.com/dp-web4/hestia) is the open local governance layer. Claude Code, Codex, Kimi, Gemini, Cursor and other agents can transit one policy/witness surface on the same machine.

The running layer includes:

- persistent local identity
- scoped delegation
- encrypted vault
- policy checks before consequential actions
- witnessed allow/deny/outcome records
- human escalation
- peer-arbitration paths
- trust derived from the witnessed chain

**Assurance ceiling:** the current open profile is **A1**. It is cooperative and tamper-evident. It can stop ordinary mistakes and make bypass attributable, but it is not containment against a determined same-UID adversary. A2 isolation, kernel/relying-party enforcement and stronger hardware roots are roadmap work. See Hestia's README and bypass catalog before relying on it for high-stakes enforcement.

### The lab uses the system it is building

The research fleet operates as a Web4 society while developing the standard. This is useful because governance failures, stale evidence, escalation gaps and deployment mistakes appear as operational defects rather than only design arguments.

## Architectural shape

### Self-sovereign societies

There is no required top-level CA or global owner. Societies can bootstrap, federate and secede. Higher-order societies are overlays formed by constituent consent, not owners of the members below them.

See [inter-society-protocol.md](web4-standard/core-spec/inter-society-protocol.md).

### Roles are first-class entities

Authority binds to roles rather than being hard-coded to a particular person or agent. Roles can be filled by humans, AI agents, sub-societies or federations, and role law composes with society law.

See [society-roles.md](web4-standard/core-spec/society-roles.md).

### Law is witnessed, not dictated

Web4 does not prescribe the content of a society's policy. It requires the chosen law to be explicit enough that consequential acts can be evaluated against it and the decision can be audited later.

See [web4-society-authority-law.md](web4-standard/core-spec/web4-society-authority-law.md).

## Standards interoperability

Web4 is designed to compose with, not replace, existing identity/credential standards. Work in the repository includes `did:web4`, SD-JWT-VC and OpenID4VCI/VP paths, with broader DID/EUDI wallet interoperability still building.

Start with:

- [Web4 and Standard Credentials](docs/whitepapers/web4-and-standard-credentials.md)
- [EUDI resolvability plan](docs/strategy/eudi-resolvability-plan.md)
- [did:web4 method](web4-standard/core-spec/did-web4-method.md)

## Who this is for

- **AI platform and agent-framework teams** that need identity and governance to survive model/vendor changes.
- **CISOs and AI risk leaders** who need evidence of what an agent did, under whose authority and under what policy.
- **Communities and organizations** that want self-governing agent/human societies rather than one platform-owned trust database.
- **Standards bodies, regulators and insurers** looking for concrete accountability primitives rather than another high-level safety taxonomy.
- **Enterprise builders** who need the open interoperability layer plus a path to higher-assurance enforcement.

## Five-minute audit

If you want to decide quickly whether this is real, read these in order:

1. [STATUS.md](STATUS.md) - calibration: shipped vs. implemented vs. specified vs. aspirational.
2. [docs/START_HERE.md](docs/START_HERE.md) - two-minute conceptual map.
3. [docs/proof/PUBLISHED.md](docs/proof/PUBLISHED.md) - package publication history.
4. [hub/](hub/) - running society reference implementation.
5. [Hestia](https://github.com/dp-web4/hestia) - running local governance layer and honest A1 assurance boundary.
6. [docs/reference/RELATED_REPOS.md](docs/reference/RELATED_REPOS.md) - ecosystem map.
7. [web4-standard/core-spec/](web4-standard/core-spec/) - normative protocol work.

## Historical ARC-AGI-3 note

A spring-2026 SAGE/ARC harness produced a published **94.85%** scorecard using Claude Opus 4.6. The artifact is preserved in [docs/proof/ARC-AGI-3.md](docs/proof/ARC-AGI-3.md) and [ARC-SAGE](https://github.com/dp-web4/ARC-SAGE) because it is part of the research history.

It is **not a current competitive claim and no longer serves as Web4's primary proof point**. The run used a frontier model and engine-level/public-game affordances outside strict competition play. Current competition-legal local-model work is well behind the leaders.

The enduring lesson was narrower and more useful: the structure around a model can materially change behavior. Current work is about making that structure persistent, governable, learnable and trustworthy under real operational constraints.

## Enterprise path

Web4 is open infrastructure. **Hardbound** is Metalinxx's proprietary enterprise assurance tier for hardware-bound identity, stronger fail-closed enforcement and audit-ready evidence packaging.

That split is deliberate: interoperability and core accountability primitives belong in the open; enterprise assurance, deployment and integration can be commercial.

## License and patents

Code is AGPL-3.0-or-later unless a subdirectory states otherwise. Patent terms are in [PATENTS.md](PATENTS.md); commercial licensing is separate where applicable.

---

**Web4: trust computed from witnessed evidence, under explicit authority and law.**
