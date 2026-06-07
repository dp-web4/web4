# Related Repositories

This is the single source of truth for the public-facing Web4 ecosystem. If a doc elsewhere describes one of these repos differently, prefer this file.

---

## Public repositories

### [dp-web4/web4](https://github.com/dp-web4/web4)
**This repo.** Canonical Web4 specifications, reference Python SDK, attack-simulation suite, attestation envelope reference, whitepaper. Trust ontology and the spec corpus live here.

License: AGPL-3.0-or-later (with `web4-core/` MIT for ARIA grant compatibility).

### [dp-web4/SAGE](https://github.com/dp-web4/SAGE)
**The cognition harness.** Wraps an LLM with Web4-shaped context — typed world models, skill registry, trust-calibrated dispatch, structured perception. Produced the 94.85% on ARC-AGI-3 with same Claude Opus 4.6.

Use when: building agents that need to reason over complex, novel state with verifiable structure.

See: [`docs/proof/ARC-AGI-3.md`](../proof/ARC-AGI-3.md) for the headline result.

### [dp-web4/4-life](https://github.com/dp-web4/4-life)
**Interactive lifecycle and trust-evolution explainer.** A browsable demo of how agents earn trust over time — witnessing, accumulation, decay. Live deployment: https://4-life-ivory.vercel.app/

Use when: introducing Web4 trust evolution to a non-technical audience, or sanity-checking that the spec doesn't assume too much (visitor-friction logs surface invisible assumptions back to the spec).

### [dp-web4/4-gov](https://github.com/dp-web4/4-gov)
**Public-facing site for governance content + AI Demo Day 4 deck.** The site at https://4-gov.org hosts the long-form talk on AI accountability + the elevator-pitch demo deck at /demo.

Use when: needing the audience-tested public framing rather than the technical spec.

### [dp-web4/Synchronism](https://github.com/dp-web4/Synchronism)
**Theoretical foundation.** Coherence equations, MRH, phase transitions, compatibility lens. Web4's MRH primitive is grounded here; the math underlying trust formation (Hill function, p_crit ∝ 1/⟨C⟩) lives here.

Use when: reasoning about why MRH is fractal, how trust thresholds emerge, and the formal grounding of Web4's contextual primitives.

### [dp-web4/ACT](https://github.com/dp-web4/ACT)
**Distributed ledger for ATP tokens and LCT presence registry.** Cosmos SDK implementation. Use when: persistence and consensus around ATP economics or LCT registration is required.

### [dp-web4/Memory](https://github.com/dp-web4/memory)
**Distributed memory paradigms.** Lightchains, blockchain alternatives for edge devices, memory-as-temporal-sensor research. Use when: designing memory architectures for resource-constrained agentic deployments.

### [dp-web4/HRM](https://github.com/dp-web4/HRM)
**Edge AI kernel research.** MoE expert selection, trust-based routing. Active forum and insights archive (synthon framing, identity portability findings). Use when: studying how Web4 trust composes with neural architecture choices.

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
