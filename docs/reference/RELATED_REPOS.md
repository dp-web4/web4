# Related Repositories

This is the single source of truth for the public-facing Web4 ecosystem. If a doc elsewhere describes one of these repos differently, prefer this file.

---

## Public repositories

### [dp-web4/web4](https://github.com/dp-web4/web4)
**The open substrate.** Canonical Web4 specifications, published core packages, Hub source, trust primitives, simulations, attestation work and whitepapers. Identity, authority, contextual trust, witnessed action and machine-readable society law live here.

License: AGPL-3.0-or-later; see each package directory and [PATENTS.md](../../PATENTS.md) for exact terms.

### [dp-web4/hestia](https://github.com/dp-web4/hestia)
**The local governance runtime.** Gives humans and AI agents from multiple vendors one local law, scoped authority, an encrypted vault, witnessed action history, escalation and trust derived from the record.

Current assurance: **A1** - cooperative and tamper-evident, useful for governance and attribution, not containment against a determined same-UID adversary.

Use when: governing agents at the person/machine boundary or evaluating the open reference implementation of Web4 action law.

### [dp-web4/4-hub](https://github.com/dp-web4/4-hub)
**The Web4 society/community runtime, standalone.** A read-only mirror of this monorepo's [`hub/`](../../hub/) directory plus the core crates it builds on. Single-binary Rust daemon: membership, seven base roles, signed machine-readable law, sealed member channels, MCP + REST surfaces and an append-only witnessed ledger.

Use when: you want to run or inspect a Web4 society without cloning the full standard.

### [dp-web4/SAGE](https://github.com/dp-web4/SAGE)
**Persistent cognition and embodiment research.** Extends Web4 identity and governance into local agents with memory, context, sensors, learning and eventually physical effectors. The public repo contains the kernel architecture and frozen research milestones; active capability work also continues in private research repos.

Use when: studying how persistent agents can learn and act under the same identity, authority and accountability substrate.

**Historical ARC note:** SAGE/ARC work produced a published spring-2026 94.85% scorecard with Claude Opus 4.6. It is preserved as a research milestone, not a current competition-leadership claim. The run used a frontier model and affordances outside strict competition play; current competition-legal local-model work is well behind the leaders. See [docs/proof/ARC-AGI-3.md](../proof/ARC-AGI-3.md) for the historical record.

### [dp-web4/4-life](https://github.com/dp-web4/4-life)
**Interactive lifecycle and trust-evolution explainer.** A browsable demo of how agents earn trust over time - witnessing, accumulation, decay. Live deployment: https://4-life-ivory.vercel.app/

Use when: introducing Web4 trust evolution to a non-technical audience, or sanity-checking that the spec doesn't assume too much.

### 4-gov - https://4-gov.org
**Public-facing governance site and demo material.** The live site hosts the long-form framing around AI accountability and governance. The site's source repo is private; the deployed site is the public artifact.

Use when: needing audience-facing framing rather than the technical spec.

### [dp-web4/Synchronism](https://github.com/dp-web4/Synchronism)
**Blue-sky theoretical exploration.** Synchronism influenced Web4's MRH framing and some of the lab's coherence vocabulary, but it is not an engineering dependency and its physics claims remain conjectural.

Use when: tracing conceptual origins or exploring the broader theoretical program.

### [dp-web4/ACT](https://github.com/dp-web4/ACT)
**Earlier distributed-ledger exploration around ATP/LCT state.** A Cosmos SDK implementation from the broader research lineage.

### HRM → SAGE
The former **dp-web4/HRM** edge-AI research lineage became **SAGE**. The old HRM URL redirects there; use the [SAGE](https://github.com/dp-web4/SAGE) entry above.

---

## Enterprise

### Hardbound
**Metalinxx's proprietary enterprise assurance tier.** Hardware-bound identity, stronger fail-closed enforcement and audit-ready evidence packaging for deployments where the open A1 governance profile is not sufficient.

Built on the open Web4 substrate. Hardbound is the enterprise assurance layer; Web4 is the interoperable foundation.

**Contact:** Metalinxx Inc. via [dp@metalinxx.io](mailto:dp@metalinxx.io).

---

## Quick chooser

| You want to... | Go to |
|---|---|
| Read the standard and current calibration | [Web4](https://github.com/dp-web4/web4) + [STATUS.md](../../STATUS.md) |
| See the running local governance layer | [Hestia](https://github.com/dp-web4/hestia) |
| Run or inspect a Web4 society | [4-hub](https://github.com/dp-web4/4-hub) |
| Study persistent cognition / embodiment | [SAGE](https://github.com/dp-web4/SAGE) |
| Understand trust evolution interactively | [4-life](https://4-life-ivory.vercel.app/) |
| See the audience-facing governance framing | [4-gov.org](https://4-gov.org) |
| Evaluate the enterprise assurance path | Contact Metalinxx Inc. about Hardbound |
| Trace the historical ARC research milestone | [docs/proof/ARC-AGI-3.md](../proof/ARC-AGI-3.md) + [ARC-SAGE](https://github.com/dp-web4/ARC-SAGE) |
