# Related Repositories

This is the single source of truth for the public-facing Web4 ecosystem. If a doc elsewhere describes one of these repos differently, prefer this file.

---

## Public repositories

### [dp-web4/web4](https://github.com/dp-web4/web4)
**This repo.** Canonical Web4 specifications, reference Python SDK, attack-simulation suite, attestation envelope reference, whitepaper. Trust ontology and the spec corpus live here.

License: AGPL-3.0-or-later (with `web4-core/` MIT for ARIA grant compatibility).

### [dp-web4/SAGE](https://github.com/dp-web4/SAGE)
**The cognition harness.** Wraps an LLM with Web4-shaped context — typed world models, skill registry, trust-calibrated dispatch, structured perception. Produced the 94.85% on ARC-AGI-3 with same Claude Opus 4.6 — real, verifiable capability, earned with affordances outside strict competition play (the harness analyzed the games' public engine source to build solver cartridges), not blind from-observation solving. See [docs/proof/ARC-AGI-3.md](../proof/ARC-AGI-3.md).

Use when: building agents that need to reason over complex, novel state with verifiable structure.

See: [`docs/proof/ARC-AGI-3.md`](../proof/ARC-AGI-3.md) for the headline result.

### [dp-web4/4-life](https://github.com/dp-web4/4-life)
**Interactive lifecycle and trust-evolution explainer.** A browsable demo of how agents earn trust over time — witnessing, accumulation, decay. Live deployment: https://4-life-ivory.vercel.app/

Use when: introducing Web4 trust evolution to a non-technical audience, or sanity-checking that the spec doesn't assume too much (visitor-friction logs surface invisible assumptions back to the spec).

### 4-gov — https://4-gov.org
**Public-facing site for governance content + AI Demo Day 4 deck.** The live site hosts the long-form talk on AI accountability + the elevator-pitch demo deck at /demo. (The site's source repo is currently private; the deployed site is the public artifact.)

Use when: needing the audience-tested public framing rather than the technical spec.

### [dp-web4/4-hub](https://github.com/dp-web4/4-hub)
**The Web4 Community Hub, standalone.** A read-only mirror of this monorepo's [`hub/`](../../hub/) directory plus the core crates it builds on (`web4-core`, `web4-policy`, `web4-trust-core`), monorepo layout preserved so a fresh clone builds with plain `cargo build`. Single-binary Rust daemon: signed machine-readable law, witnessed ledger, sealed member channels, MCP + REST surfaces. Published by `scripts/publish-4-hub.sh`; development and issues stay in **this repo**.

Use when: you want to run or read just the hub without cloning the full standard.

### [dp-web4/Synchronism](https://github.com/dp-web4/Synchronism)
**Theoretical foundation.** Coherence equations, MRH, phase transitions, compatibility lens. Web4's MRH primitive is grounded here; the math underlying trust formation (Hill function, p_crit ∝ 1/⟨C⟩) lives here.

Use when: reasoning about why MRH is fractal, how trust thresholds emerge, and the formal grounding of Web4's contextual primitives.

### [dp-web4/ACT](https://github.com/dp-web4/ACT)
**Distributed ledger for ATP tokens and LCT presence registry.** Cosmos SDK implementation. Use when: persistence and consensus around ATP economics or LCT registration is required.

### HRM → SAGE
The former **dp-web4/HRM** (edge AI kernel research: MoE expert selection, trust-based routing, the synthon framing and insights archive) was the lineage that became **SAGE** — the old HRM URL redirects there. Use the [SAGE](https://github.com/dp-web4/SAGE) entry above.

---

## Currently private (research in progress)

### Memory
**Distributed memory paradigms.** Lightchains, blockchain alternatives for edge devices, memory-as-temporal-sensor research. The repo is currently private while the research matures; findings inform Web4's memory-as-temporal-sensor framing. Contact via [this repo](https://github.com/dp-web4/web4) if it's relevant to your work.

---

## Enterprise (contact for access)

### Hardbound
**Web4 in production.** Hardware-bound identity, verifiable audit chains, contextual computable trust — productized for regulated industries (finance, defense, healthcare, infrastructure). TPM 2.0 binding on Linux, FIDO2 fallback, policy enforcement, audit pipeline.

Built on the open Web4 ontology — Hardbound is the deployment, Web4 is the substrate.

**Contact**: Metalinxx Inc. — via the [project repository](https://github.com/dp-web4/web4) for evaluation and deployment.

---

## Quick chooser

| You want to... | Go to |
|---|---|
| Read the standard | this repo (`web4-standard/`, `whitepaper/`) |
| See the 94.85% proof point | [SAGE](https://github.com/dp-web4/SAGE) + [docs/proof/ARC-AGI-3.md](../proof/ARC-AGI-3.md) |
| Understand trust evolution interactively | [4-life-ivory.vercel.app](https://4-life-ivory.vercel.app/) |
| See the audience-tested public framing | [4-gov.org](https://4-gov.org) + [docs/why/DEMO_DAY_2026-04.md](../why/DEMO_DAY_2026-04.md) |
| Deploy in a regulated environment | Contact Metalinxx Inc. via the [project repository](https://github.com/dp-web4/web4) about Hardbound |
| Study the formal foundations | [Synchronism](https://github.com/dp-web4/Synchronism) |
| Persist ATP/LCT state | [ACT](https://github.com/dp-web4/ACT) |
| Run or read just the community hub | [4-hub](https://github.com/dp-web4/4-hub) |
