# Start Here

**30 seconds to understand Web4**

Web4 is an open substrate for **verifiable presence and agent accountability**. Instead of asking a platform to declare who is trusted, Web4 lets humans, AI agents, services and societies carry evidence of identity, authority, governing law and witnessed behavior.

**Core insight:** trust should be computed by the relying party from evidence, in context, at the stakes of the action.

---

## What Makes Web4 Different

| Web2 | Web3 | Web4 |
|------|------|------|
| Platform controls identity | User owns keys | Identity is persistent, contextual and witnessed |
| Permissions are declared | Access is token-gated | Authority is scoped by role and law |
| Central database decides | Ledger proves ownership/state | Relying party evaluates witnessed evidence |

---

## The operational stack

| Layer | Role |
|---|---|
| **Web4** | Open standard + core primitives: LCT identity, T3/V3 trust, R6/R7 action grammar, MRH context, ATP/ADP resource accounting, witnessed law |
| **Hestia** | Local governance at the human/agent boundary: multi-vendor agents under one law, scoped authority, witnessed action history and escalation |
| **Hub** | Society/community runtime: membership, seven base roles, signed law, sealed channels and a witnessed ledger |
| **Hardbound** | Metalinxx enterprise assurance tier: hardware-bound identity, stronger fail-closed enforcement and audit packaging |
| **SAGE** | Research environment carrying the same ideas into persistent cognition, local models and embodiment |

---

## Quick Navigation

| You Are... | Your Goal | Start Here |
|------------|-----------|------------|
| **Curious newcomer** | Understand the vision | [why/EXECUTIVE_SUMMARY.md](why/EXECUTIVE_SUMMARY.md) |
| **Developer** | Implement Web4 | [how/README.md](how/README.md) → [how/guides/](how/guides/) |
| **Researcher** | Check what is real | [../STATUS.md](../STATUS.md) → [../whitepaper/](../whitepaper/) |
| **Operator / risk lead** | See the running governance layer | [Hestia](https://github.com/dp-web4/hestia) → [Hub](../hub/) |
| **AI agent** | Integrate with Web4 | [how/AGENT_INTEGRATION.md](how/AGENT_INTEGRATION.md) |
| **Contributor** | Help the project | [../CONTRIBUTING.md](../CONTRIBUTING.md) |

---

## Key Concepts (2-minute overview)

**LCT (Linked Context Token):** persistent, witnessable identity/presence bound to context.

**Trust Tensor (T3/V3):** multi-dimensional trust and value records. Not just "trusted" but "trusted for what, by whom, in what context."

**MRH (Markov Relevancy Horizon):** the context boundary within which evidence is relevant.

**R6/R7:** the grammar and accountability record around consequential actions.

**ATP/ADP:** resource allocation/accounting primitives. ATP is a society-defined unit of account, not a protocol currency.

**Society law:** machine-readable rules that bind roles and actions. Web4 does not dictate policy; it makes the chosen policy explicit and auditable.

---

## Current Status

Web4 is research-stage, but the core is no longer just a concept:

- **Published packages:** `web4-core` 0.3.0 is on crates.io and PyPI; `web4-trust-core` / `web4-trust` 0.2.0 are published; `web4-core` 0.4.0 is in source on `main`.
- **Hub is running:** a Rust society daemon with LCT-pinned membership, seven base roles, signed law, sealed member channels and an append-only witnessed ledger.
- **Hestia is running:** multiple agent vendors share one local governance surface with witnessed actions, human escalation and derived trust. The current open assurance level is **A1** - useful for governance and attribution, not containment against a determined same-UID adversary.
- **The lab uses its own machinery:** the fleet operates as a Web4 society while developing the standard.
- **Higher assurance is still building:** A2 isolation, kernel/relying-party enforcement, production hardware roots and broader DID/EUDI interoperability remain roadmap work.

**Honest assessment:** working open primitives + live reference deployments + substantial security/interoperability work ahead. R&D, not a finished production platform.

See [STATUS.md](../STATUS.md) for the long version and [docs/proof/PUBLISHED.md](proof/PUBLISHED.md) for the publication trail.

### Historical ARC-AGI-3 note

A spring-2026 SAGE/ARC harness produced a published 94.85% scorecard with Claude Opus 4.6. It remains documented in [proof/ARC-AGI-3.md](proof/ARC-AGI-3.md) as a research milestone, not as Web4's current headline proof point or a claim of present competition leadership. The run used a frontier model and affordances outside strict competition play; current competition-legal local-model work is well behind the leaders.

---

## Next Steps

1. **Quick read:** [why/EXECUTIVE_SUMMARY.md](why/EXECUTIVE_SUMMARY.md) (5 min)
2. **Calibration:** [../STATUS.md](../STATUS.md)
3. **Running reference:** [Hub](../hub/) + [Hestia](https://github.com/dp-web4/hestia)
4. **Concepts:** [reference/GLOSSARY.md](reference/GLOSSARY.md)
5. **Deep dive:** [../whitepaper/](../whitepaper/)

---

*Web4: trust computed from witnessed evidence, not declared by a platform.*
