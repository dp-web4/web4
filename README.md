# Web4: Verifiable Presence for AI

[![crates.io: web4-core](https://img.shields.io/crates/v/web4-core?label=crates.io%20web4-core)](https://crates.io/crates/web4-core)
[![crates.io: web4-trust-core](https://img.shields.io/crates/v/web4-trust-core?label=crates.io%20web4-trust-core)](https://crates.io/crates/web4-trust-core)
[![PyPI: web4-core](https://img.shields.io/pypi/v/web4-core?label=PyPI%20web4-core)](https://pypi.org/project/web4-core/)
[![PyPI: web4-trust](https://img.shields.io/pypi/v/web4-trust?label=PyPI%20web4-trust)](https://pypi.org/project/web4-trust/)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/License-AGPL--3.0--or--later-blue.svg)](LICENSE)

> **AI is already taking actions in the world. We can't prove what it did.**
> Web4 is the open standard that closes that gap.

An open standard for verifiable AI presence — proposed by Metalinxx Inc., owned by no one. Research-stage. v0.1.1 packages public; reference implementation public; no production deployment yet. **[STATUS.md](STATUS.md)** is the calibration — read it before judging the claims below.

**Proof point**: 0% → 94.85% on ARC-AGI-3 with the same Claude Opus 4.6, structured around Web4 patterns via the [SAGE](https://github.com/dp-web4/SAGE) harness. [Public scorecard](https://arcprize.org/scorecards/c7dfb4f1-8642-4c9e-ab4d-152f5f8e33b4). The model didn't change — the structure around it did.

## Architectural shape (what Web4 actually is)

Three properties define the shape, and each has a normative spec:

1. **Self-sovereign fractal societies, no top-level CA.** Societies bootstrap themselves (a single founder is sufficient) or form by federation of existing societies. Higher-order societies are *overlays, not owners* — they exist by constituent consent and dissolve when consent is withdrawn. There is no DNS root, no PKI root, no canonical top-level society. Trust emerges from peer witnessing. See [`inter-society-protocol.md`](web4-standard/core-spec/inter-society-protocol.md) for genesis, first-contact, federation, and secession protocols.

2. **A small fixed set of mandatory roles with fractal composability.** Every Web4 society must fill seven base roles (Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator, Archivist, Citizen — modeled on corporate-structure functions). Any role MAY be filled by a single entity (solo founder wears many hats), a sub-society (large enterprise), or a federation (multi-region). Role authority binds to the role's LCT, not the filling entity. See [`society-roles.md`](web4-standard/core-spec/society-roles.md) for the full taxonomy with audit semantics.

3. **ATP is a unit of account, not a currency.** Each society reifies its own resources (compute, attention, hardware, time, whatever it accounts) into ATP at policies it chooses. On first contact with another society, three sovereign options exist: keep both currencies and negotiate exchange rate (international-trade pattern), one adopts the other's (dollarization pattern), or both join/form a higher-order society with shared currency (Eurozone pattern). This is intentional: no protocol-level constraint on initial issuance is needed because the market for the society's ATP at exchange time *is* the audit mechanism.

These three together produce the property: **Web4 is anti-hierarchical by design**, with audit and trust emerging from below rather than imposed from above. The specs *implement* this philosophy; this section is here so the philosophy is visible upfront rather than inferred from the corpus.

**How societies engage each other**: a society's external surface is its MCP server. Other societies invoke its scoped actions (R6/R7) by calling MCP tools with LCT-signed envelopes; querying its state by reading MCP resources; coordinating across federation depth via witness signatures carried in the MCP exchange. The canonical Web4 equation `Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP` has MCP as the **I/O membrane** for exactly this reason — internal structure is `LCT + T3/V3*MRH + ATP/ADP`; the cross-society interface IS MCP. See [`mcp-protocol.md`](web4-standard/core-spec/mcp-protocol.md) §1.1 and §7 for the inter-society binding spec.

## Five-minute audit

If you want a fast read on whether this is real, in order:

1. [**STATUS.md**](STATUS.md) — what's shipped, what's specified, what's aspirational.
2. [**docs/proof/PUBLISHED.md**](docs/proof/PUBLISHED.md) — what's published and why v0.1.0 was yanked.
3. [**demo/**](demo/) — agent commerce delegation, 166 tests passing.
4. [**simulations/**](simulations/) — 424 attack vectors / 84 tracks, ~85% detection rate against synthetic adversaries (no red team yet; see STATUS for honest characterization).
5. [**docs/specs/heterogeneous-identity.md**](docs/specs/heterogeneous-identity.md) — multi-factor identity as a constellation. Answers "what stops a hardware vendor from gating LCT access?" structurally.
6. [**web4-standard/core-spec/inter-society-protocol.md**](web4-standard/core-spec/inter-society-protocol.md) — society genesis (self-bootstrapped + federation-based), first-contact (3 sovereign options), ATP reification sovereignty, secession.
7. [**web4-standard/core-spec/society-roles.md**](web4-standard/core-spec/society-roles.md) — 7 base-mandatory roles + context-mandatory (forced by outward role) + optional, with fractal composability and audit implications.
8. [**forum/kimi2_6_review.md**](forum/kimi2_6_review.md) — independent cross-model review (Kimi 2.6) with three rounds of dialogue. External scrutiny on the work, raw and verbatim.

---

## Install

**Rust** (`Cargo.toml`):
```toml
[dependencies]
web4-core = "0.1"
web4-trust-core = "0.1"
```

**Python**:
```bash
pip install web4-core
pip install web4-trust
```

Both crates and both Python packages are AGPL-3.0-or-later. Patent grant terms in [PATENTS.md](PATENTS.md).

### 30-second proof of presence

Once installed, this is the smallest end-to-end path — create a presence, mint it to a hash-chained ledger, sign and verify, generate and verify an inclusion proof:

**Python:**
```python
import web4_core

# Create LCT (presence primitive) and an Ed25519 keypair
lct, keypair = web4_core.PyLct.new(web4_core.PyEntityType.Human, None)

# Mint into a ledger — LCTs are blockchain tokens; minting is what witnesses presence
ledger = web4_core.PyInMemoryLedger()
receipt = ledger.mint(lct)

# Sign + verify
sig = keypair.sign(b"hello, web4")
assert lct.verify_signature(b"hello, web4", sig)

# Inclusion proof — anyone can verify this LCT is in the ledger without trusting you
proof = ledger.anchor(lct.id)
assert ledger.verify_proof(proof)
```

**Rust:** identical steps with `Lct::new` / `ledger.mint` / `keypair.sign` / `ledger.anchor` — see [`web4-core/README.md`](web4-core/README.md#quick-start) for the matching code.

**Persistent version with on-disk keypair + hash-chained ledger:** [`web4-core/python/examples/identity_bootstrap.py`](web4-core/python/examples/identity_bootstrap.py). Run once to bootstrap an LCT for a host; re-run to verify the chain didn't tamper. ~30 seconds.

**Cross-language verification (Python mints, Rust verifies the same ledger):** [`web4-core/examples/cross_language_verify/`](web4-core/examples/cross_language_verify/). Demonstrates that the on-disk format is the contract: any language with the spec can verify what any other language minted.

---

## What Web4 is, structurally

**Web4 is to AI governance what the Linux kernel is to an operating system.**

The Linux kernel manages hardware, processes, memory — it's the substrate, and it's not directly usable on its own. GNU userland (shell, utilities, compilers) is what makes the kernel actually operable. Distributions like Ubuntu or Fedora package both together with ecosystem tools. **Linux alone is the engine; GNU provides the controls; together they become the operating system people actually use.**

Web4 specifies the substrate of trust-native AI governance — identity (LCT), trust accounting (T3/V3*MRH), resource accounting (ATP/ADP), action grammar (R6/R7), all expressed over RDF with MCP as the inter-society I/O membrane. It's not directly usable. **[Hardbound](https://github.com/dp-web4/hardbound)** is the canonical userland: PolicyService, SocietyManager, MCP server, dashboard, independent-verification CLI — the tools that make Web4 operationally deployable. A specific deployment in a specific organization is the distribution-equivalent. **Web4 alone is the substrate; Hardbound provides the controls; together they become the governance system you actually run.**

This framing tells you where Web4 sits in the stack, and what's deliberately not in scope:

- Web4 doesn't decide *what your application looks like*, any more than the Linux kernel decides what a desktop environment looks like
- Web4 isn't competing with Hardbound — they're different layers of the same stack
- Web4 alone is technically usable (via SDK calls) but operationally inert; you build the userland or pick an existing one
- Alternative userlands beyond Hardbound are expected and welcome; the spec is designed for interoperable implementations
- A conformance test suite — analogous to POSIX — is what would make alternative userlands provably interoperable; that work is in progress

## Who this is for, and why

If you're one of these people, this is worth your time:

- **AI engineering lead at a lab or platform** building agent frameworks, policy systems, or governance tooling. Web4 primitives compose under your runtime. Cross-language interop (Python and Rust verifying the same on-disk ledger) is shipped; identity, T3/V3 trust, witnessing, and audit-defensible records are published primitives, not slideware.

- **CISO or AI risk lead** in a regulated industry (finance, defense, healthcare) where agentic AI deployments will need to defend their actions to auditors, regulators, or insurers. Web4 turns "we hope nothing went wrong" into "we can prove what happened, on whose authority, by what rules." Enterprise implementation: **[Hardbound](https://github.com/dp-web4/hardbound)** -- provides a plugin that bridges any orchestrator (Claude Code, LangChain, CrewAI, etc.) to a signed policy entity. Every action gets an LCT identity, T3/V3 trust evaluation, and a cryptographically signed policy decision. The open standard is here; the enterprise product makes it deployable.

- **Developer-tooling company** building agent frameworks (LangChain, CrewAI, AG2, etc.) or governance toolkits. Web4 sits *upstream* of runtime policy enforcement — governance for what an agent IS (identity, witness graph, accountability ontology), not what it DOES (runtime gating). The two layers compose; Web4 is the standard your governance toolkit can consume so identity isn't proprietary to the runtime. **Integration path**: install the [Hardbound plugin](https://github.com/dp-web4/hardbound) -- a single `HardboundPlugin` class connects any orchestrator to a Web4 policy entity, giving it an LCT identity and governed action trail. The plugin is the bridge; Web4 is the substrate.

- **Standards body, regulator, or insurer** trying to figure out what "agentic AI accountability" means technically. Web4 is the open spec + published implementation + reproducible artifacts. AGPL-3.0 with patent grant ([PATENTS.md](PATENTS.md)), owned by no one. Start with [STATUS.md](STATUS.md) and the [whitepaper](whitepaper/).

If you came here looking for a finished product to install and use, this isn't that. If you came here looking for the layer underneath the products you're building, it is.

### Why the applications will come

Web4 doesn't predict what the killer applications will be — that's what builders figure out, the way they figured out which applications mattered once Linux + GNU made general-purpose computing accessible. What's certain is the *forcing function* is arriving:

- **The bearer-token credential model is breaking.** The Vercel breach exploited tokens-as-keys; Web4 treats tokens as evidence in a witness graph instead.
- **Financial regulators are convening on agentic AI.** The recent SR 26-2 / OCC Bulletin 2026-13 explicitly excludes agentic AI from current model-risk frameworks and signals an RFI is imminent.
- **Cyber insurers don't yet know how to underwrite AI risk** — the technical references they'd cite don't exist yet.
- **AI labs are starting to ship runtime governance features** (Microsoft Agent Governance Toolkit, April 2026; Anthropic adopting Web4-style governance patterns) — but each in their own runtime, without a shared identity layer underneath. Web4 is that layer.

The applications come when the substrate exists *and* the present-tense pain forces builders onto it. Both halves are arriving at the same time. The standard is here so the applications can come — not because we know what they are.

---

## Status Snapshot (2026-05-13)

### Where it landed publicly
- **AI Demo Day 4** (2026-04-26): Web4 presented as "verifiable presence" for agentic AI. Slides + narration archived at https://4-gov.org/demo
- **Cross-model independent review** (2026-05-13): Kimi 2.6 reviewed the repo + specs across three rounds of dialogue. Verbatim transcript at [`forum/kimi2_6_review.md`](forum/kimi2_6_review.md). Scoring: architectural coherence 8.5/10, bootstrap story 8/10, spec completeness intra-society 7/10, spec completeness inter-society 4/10. The dialogue produced two new spec docs (see below).

### Implementation status
- **Published artifacts** (2026-04-28): `web4-core` and `web4-trust-core` on crates.io; `web4-core` and `web4-trust` on PyPI. **Current: v0.1.1**, AGPL-3.0-or-later. (v0.1.0 was yanked from crates.io due to a Python wheel import-path defect and a stale tensor docstring; both fixed in v0.1.1.) See [STATUS.md](STATUS.md) for the full version table and [docs/proof/PUBLISHED.md](docs/proof/PUBLISHED.md) for the publish trail.
- **Stage**: research, not production. v0.1.1 packages are public; reference implementation and harness are public; no production deployment yet.
- Spec corpus: stable, with two new core specs added 2026-05-13 (see below)
- **NEW**: [`inter-society-protocol.md`](web4-standard/core-spec/inter-society-protocol.md) v0.1.2 DRAFT — society genesis, first-contact (3 sovereign options), ATP-as-unit-of-account, secession
- **NEW**: [`society-roles.md`](web4-standard/core-spec/society-roles.md) v0.1.0 DRAFT — 7 base-mandatory roles + context-mandatory + optional, with fractal composability
- Reference Python SDK + 8-tool MCP server: 2,627 tests, mypy --strict clean (`web4-standard/implementation/`)
- Cognition harness producing the 94.85% result: [SAGE](https://github.com/dp-web4/SAGE)
- Hardware binding (TPM 2.0 on Linux), policy enforcement, and audit pipeline: shipped in **[Hardbound](https://github.com/dp-web4/hardbound)** — enterprise product with plugin bridge for any orchestrator, PolicyService with signed decisions, multi-witness TrustWeb, HITL escalation, and regulatory evidence generators (EU AI Act Article 12, SOC2 CC6-CC8)
- Attack simulation suite: 424 vectors across 84 tracks (~85% detection rate). **Honest characterization**: synthetic adversaries only, no red team engagement yet; some "defenses" are standard infosec practices (EM shielding, TEMPEST) documented for completeness, not Web4-novel. See STATUS.md for the breakdown.
- Formal threat model: [THREAT_MODEL.md v2.0](docs/reference/security/THREAT_MODEL.md)

### Gaps
- Economic attack modeling at scale (no real-market testing)
- Formal Sybil-resistance proofs (empirical defenses only)
- Hardware binding reference implementation in this public repo (Python `AttestationEnvelope` shipped; Rust port and on-device integration in progress; Hardbound has the production version)

### Open questions
- Are stake amounts actually deterrent? (no economic modeling)
- Does witness diversity resist sophisticated cartels?
- What's the minimal viable Web4 for a public pilot?

---

## 🎯 Vision

**Web4 makes AI actions verifiable, attributable, and accountable — without central control.**

AI agents are increasingly autonomous. Booking, coding, transacting, deciding. Current architectures assume either central control (a platform decides who's trusted — doesn't scale, single point of failure) or cryptographic ownership (you're trusted if you hold the right keys — insufficient, since holding a key doesn't mean you'll act well).

Neither answers: **how do I know this agent will behave appropriately in this context, and how do I prove what it actually did?**

### About "Web4"

Like Web1, Web2, and Web3, "Web4" is a generational label for the capabilities needed in the agentic AI era — not a single protocol or product.

**This project suite** focuses specifically on **trust infrastructure** for agent-agent and agent-human interactions: how agents establish verifiable presence, build reputation, delegate authority, and coordinate safely across organizational boundaries — and how their actions stand up to audit.

---

## 💡 Why This Matters

### The Problem

AI agents are increasingly autonomous—browsing, transacting, coordinating with other agents. Current architectures assume either:
- **Central control**: A platform decides who's trusted (doesn't scale, single point of failure)
- **Cryptographic ownership**: You're trusted if you hold the right keys (insufficient—holding a key doesn't mean you'll act well)

Neither addresses the core question: **How do I know this agent will behave appropriately in this context?**

### How Web4 Differs from Web3

| Aspect | Web3 | Web4 |
|--------|------|------|
| **Trust basis** | Cryptographic proof of ownership | Behavioral reputation over time |
| **Identity** | Wallet addresses | Linked Context Tokens (LCTs) with witnessed history |
| **Authorization** | Token-gated access | Context-dependent trust tensors |
| **Coordination** | Smart contracts | Federated societies with emergent trust structures |
| **Focus** | Asset ownership | Agent behavior and intent |

### What Problems This Could Address

- **AI Agent Accountability**: Every action traceable to a verifiable presence with reputation at stake
- **Cross-Platform Coordination**: Agents from different systems interoperating through shared trust protocols
- **Graduated Authorization**: Not just "allowed/denied" but nuanced trust based on context, history, and stakes
- **Self-Organizing Trust**: Societies that establish norms through interaction rather than requiring top-down rule enforcement

---

## 📚 Quick Navigation

| You Are... | Your Goal | Start Here |
|------------|-----------|------------|
| **New to Web4** | Understand the vision | [docs/START_HERE.md](docs/START_HERE.md) |
| **Developer** | Implement Web4 | [docs/how/README.md](docs/how/README.md) |
| **Researcher** | Study the concepts | [STATUS.md](STATUS.md) → [whitepaper/](whitepaper/) |
| **AI Agent** | Integrate | [docs/how/AGENT_INTEGRATION.md](docs/how/AGENT_INTEGRATION.md) |
| **Contributor** | Help the project | [CONTRIBUTING.md](CONTRIBUTING.md) |

### Learning Path

| Step | Document | What You'll Learn |
|------|----------|-------------------|
| 1 | **[STATUS.md](STATUS.md)** | Honest assessment: what exists, what works, what's missing |
| 2 | **[docs/reference/GLOSSARY.md](docs/reference/GLOSSARY.md)** | Quick reference for all Web4 terminology |
| 3 | **[whitepaper/](whitepaper/)** | Conceptual foundation: LCTs, trust tensors, MRH, R6 framework |
| 4 | **[docs/how/README.md](docs/how/README.md)** | Implementation guides |
| 5 | **[SECURITY.md](SECURITY.md)** | Security research status and known gaps |
| 6 | **[docs/reference/security/THREAT_MODEL.md](docs/reference/security/THREAT_MODEL.md)** | What we're defending against |
| 7 | **[docs/specs/attestation-envelope.md](docs/specs/attestation-envelope.md)** | AttestationEnvelope: how LCT presence binds to hardware attestation (TPM2/FIDO2/Secure Enclave/software) into a single verifiable structure |
| 8 | **[docs/specs/heterogeneous-identity.md](docs/specs/heterogeneous-identity.md)** | Multi-factor identity as a constellation of mutually-witnessing factors. Why "vendor gating LCT" dissolves once identity stops being singular. |
| 9 | **[docs/reference/LCT_DOCUMENTATION_INDEX.md](docs/reference/LCT_DOCUMENTATION_INDEX.md)** | Index of all LCT-related documentation |

---

## ⚠️ Project Status: Research Prototype

**This is exploratory research, not production software.**

Web4 is investigating trust-native architectures for AI coordination. We have interesting ideas, working prototypes, and significant gaps. See [STATUS.md](STATUS.md) for honest assessment.

---

## 🏗️ Four Development Tracks

Web4 contains **four development tracks** at different maturity levels:

### Track 1: 4-Life — Lifecycle and Trust-Evolution Explainer (Standalone)

**What it is**: An interactive explainer site demonstrating how agents earn trust over time — lifecycle, witnessing, and trust evolution made browsable. Live at [4-life-ivory.vercel.app](https://4-life-ivory.vercel.app/).

**Status**: **Standalone project** → [github.com/dp-web4/4-life](https://github.com/dp-web4/4-life)

The original prototype (`/game/`) was archived to `archive/game-prototype/` after evolving past the simulation stage. Active simulation research continues in `/simulations/` (attack scenarios, trust dynamics).

**Documentation**:
- [`archive/game-prototype/ARCHIVED.md`](archive/game-prototype/ARCHIVED.md) — evolution history
- [4-life repo](https://github.com/dp-web4/4-life) — active development
- [4-life-ivory.vercel.app](https://4-life-ivory.vercel.app/) — interactive demo

**Use for**: A non-technical introduction to how Web4 trust evolves. Pair with this README for the architectural view.

### Track 2: `web4-standard/implementation/authorization/` - PostgreSQL Authorization Layer

**What it is**: Database-backed authorization with security mitigations.

**Status**: More mature, but still research
- Real SQL schemas with constraints
- ATP drain/refund mitigations
- Reputation washing detection
- Delegation validation
- ~50 test files with security attack tests

**Key files**:
- `schema.sql`, `schema_atp_drain_mitigation.sql`, `schema_reputation_washing_detection.sql`
- `authorization_engine.py`, `delegation_validator.py`, `sybil_resistance.py`
- `test_security_attacks.py`, `test_atp_refund_exploit.py`

**Use for**: Authorization logic that needs persistence and real constraints

### Track 3: `demo/` - Commerce Demo (Narrow Application)

**What it is**: A working demo showing one use case (AI agent purchasing).

**Status**: Functional demo, not production deployment
- Delegation UI for setting agent limits
- Demo store for testing purchases
- In-memory (no real payments)

**Use for**: Demonstrations and presentations

### Track 4: `web4-standard/implementation/reference/` - Coordination Framework (Active Development)

**What it is**: Reference implementations for distributed coordination, pattern learning, and cross-system integration.

**Status**: Active research with validated components (~25,000 lines added Dec 2025)
- Phase 2 coordinators (epistemic, integrated, circadian, adaptive)
- Pattern exchange protocol (bidirectional SAGE ↔ Web4)
- EM-state (Epistemic Monitoring) framework
- Temporal/phase-tagged learning
- LCT Unified Presence Specification

**Key Components**:

| Component | Purpose | Status |
|-----------|---------|--------|
| Phase 2a Epistemic Coordinator | Runtime epistemic state tracking | Validated |
| Phase 2b Integrated Coordinator | Epistemic + pattern learning | Validated |
| Phase 2c Circadian Coordinator | Temporal/phase-aware decisions | Validated |
| Phase 2d Adaptive Coordinator | EM-state modulation | Validated |
| Pattern Exchange Protocol | Cross-system learning transfer | Operational |
| LCT Presence Specification | Unified presence format | v1.0.0 draft |

**Validation Results** (Dec 2025):
- 76% prediction validation (13 of 17 predictions confirmed)
- +386% efficiency improvement demonstrated
- Long-duration testing (1000+ cycles)

**Key Files**:
- `web4_phase2b_integrated_coordinator.py` - Combined epistemic + learning
- `temporal_pattern_exchange.py` - Phase-aware pattern transfer
- `universal_pattern_schema.py` - Cross-system pattern format
- `LCT_UNIFIED_PRESENCE_SPECIFICATION.md` - Presence standard (in `/docs/`)

**Use for**: Coordination research, SAGE integration, cross-system pattern transfer

---

## 📊 Key Documentation

| Document | What It Covers |
|----------|----------------|
| **[STATUS.md](STATUS.md)** | Honest assessment - what exists, what works, what's missing |
| **[SECURITY.md](SECURITY.md)** | Security research status and gaps |
| **[docs/reference/security/THREAT_MODEL.md](docs/reference/security/THREAT_MODEL.md)** | Formal threat model for the overall system |
| **[docs/reference/GLOSSARY.md](docs/reference/GLOSSARY.md)** | Canonical terminology definitions |
| **[Whitepaper](whitepaper/)** | Conceptual foundation (LCTs, trust, MRH) |

**Start here**: [STATUS.md](STATUS.md) for fair evaluation criteria

---

## What Is Web4?

Web4 is an **ontology** — a formal structure of typed relationships through which trust, identity, and value are expressed.

**Architect's view (what Web4 is):**
```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

**Entity's view (what existence looks like from inside):**
```
Presence = LCT[T3/V3 * MRH] + RDF + ATP/ADP + MCP
```

Operators: `[]` = "contains", `/` = "verified by", `*` = "contextualized by", `+` = "augmented with"

**Core components:**
- **MCP** (Model Context Protocol) — I/O membrane for inter-entity communication
- **RDF** (Resource Description Framework) — Ontological backbone; all trust relationships are typed triples, all MRH graphs are RDF, all semantic queries use SPARQL
- **LCT** (Linked Context Token) — Verifiable presence anchored to hardware
- **T3/V3** (Trust/Value Tensors) — Fractally multidimensional. T3 has 3 root dimensions (Talent / Training / Temperament); V3 has 3 (Valuation / Veracity / Validity). Each root dimension is itself an open-ended RDF sub-graph of context-specific sub-dimensions via `web4:subDimensionOf`, bound to entity-role pairs
- **MRH** (Markov Relevancy Horizon) — Fractal context scoping, implemented as RDF graphs
- **ATP/ADP** (Allocation Transfer/Discharge Packets) — Bio-inspired energy metabolism

**Built on this foundation:** Societies, SAL (oversight), AGY (delegation), ACP (autonomous operation), Dictionaries (semantic bridges), R6/R7 (action framework), Federation (multi-society coordination)

### The Research Questions

- How do you give AI agents authority without losing control?
- How does trust emerge and decay in distributed systems?
- How do you coordinate multiple AI societies?
- What security properties are achievable at scale?

### What We're Exploring

**Fine-grained delegation** with enforcement:

```
Example: Agent purchasing with constraints
- Daily budget limits
- Per-transaction limits
- Resource type restrictions
- Approval thresholds
- Instant revocation
```

### Concept → Implementation Map

| Concept | Specification | Reference Implementation | Research / Simulations |
|---------|--------------|--------------------------|------------------------|
| **LCT (Presence)** | [`web4-standard/core-spec/LCT-linked-context-token.md`](web4-standard/core-spec/LCT-linked-context-token.md) | [`web4-core/`](web4-core/) (Rust + Python), [`web4-standard/implementation/sdk/web4/lct.py`](web4-standard/implementation/sdk/web4/lct.py) | [`simulations/`](simulations/), [`web4-standard/implementation/authorization/`](web4-standard/implementation/authorization/) |
| **Multi-Device Binding** | [`web4-standard/core-spec/multi-device-lct-binding.md`](web4-standard/core-spec/multi-device-lct-binding.md) | [`web4-core/python/web4/trust/attestation/`](web4-core/python/web4/trust/attestation/) | AttestationEnvelope + TPM2/FIDO2/SE/software anchor verification |
| **Trust Tensors (T3/V3)** | [`web4-standard/core-spec/t3-v3-tensors.md`](web4-standard/core-spec/t3-v3-tensors.md) | [`web4-core/src/t3.rs`](web4-core/src/t3.rs), [`v3.rs`](web4-core/src/v3.rs), [`web4-trust-core/`](web4-trust-core/), [`web4-standard/implementation/sdk/web4/trust.py`](web4-standard/implementation/sdk/web4/trust.py) | [`simulations/`](simulations/) — trust dynamics |
| **MRH (Context)** | [`web4-standard/core-spec/mrh-tensors.md`](web4-standard/core-spec/mrh-tensors.md) | [`web4-standard/implementation/sdk/web4/mrh.py`](web4-standard/implementation/sdk/web4/mrh.py) (Python; no Rust port yet) | [`simulations/`](simulations/) |
| **ATP/ADP (Economics)** | [`web4-standard/core-spec/atp-adp-cycle.md`](web4-standard/core-spec/atp-adp-cycle.md) | [`web4-standard/implementation/sdk/web4/atp.py`](web4-standard/implementation/sdk/web4/atp.py) | [`simulations/`](simulations/) — economic attack modeling |
| **MCP Integration** | [`web4-standard/core-spec/mcp-protocol.md`](web4-standard/core-spec/mcp-protocol.md) | [`web4-standard/implementation/sdk/web4/mcp_server.py`](web4-standard/implementation/sdk/web4/mcp_server.py) | [`mcp-server/`](mcp-server/) — standalone server (legacy; prefer the SDK) |
| **R6 / R7 Action Grammar** | [`web4-standard/core-spec/r6-framework.md`](web4-standard/core-spec/r6-framework.md), [`r7-framework.md`](web4-standard/core-spec/r7-framework.md) | [`web4-standard/implementation/reference/`](web4-standard/implementation/reference/) | [`simulations/r6.py`](simulations/r6.py) |
| **RDF Ontologies** | [`web4-standard/ontology/`](web4-standard/ontology/) | TTL files (documentation-grade; consumed conceptually, not runtime-validated yet) | — |
| **Federation** | [`docs/how/integration/SAGE_WEB4_INTEGRATION_DESIGN.md`](docs/how/integration/SAGE_WEB4_INTEGRATION_DESIGN.md) | [`web4-standard/implementation/reference/`](web4-standard/implementation/reference/) | [`simulations/federation.py`](simulations/federation.py) |
| **Societies** | [`web4-standard/core-spec/SOCIETY_SPECIFICATION.md`](web4-standard/core-spec/SOCIETY_SPECIFICATION.md) | 4-life repo | Society simulation |
| **Authorization** | [`web4-standard/core-spec/security-framework.md`](web4-standard/core-spec/security-framework.md) | [`web4-standard/implementation/authorization/`](web4-standard/implementation/authorization/) | PostgreSQL schemas |
| **Coordination** | [`docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md`](docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md) | [`web4-standard/implementation/reference/`](web4-standard/implementation/reference/) | Phase 2 coordinators |

---

## 🚀 Quick Start

### Run the Demo

```bash
# Terminal 1: Start the demo store
cd demo/store
pip install -r requirements.txt
python app.py
# Visit: http://localhost:8000

# Terminal 2: Start the delegation UI
cd demo/delegation-ui
pip install -r requirements.txt
python app.py
# Visit: http://localhost:8001
```

See [`demo/DEMO_SCRIPT.md`](demo/DEMO_SCRIPT.md) for walkthrough.

### Run Simulations

```bash
cd simulations

# Attack simulations
python attack_simulations.py               # Core attack simulation framework
python attack_track_fb.py                  # Trust manipulation attacks
python attack_track_fc.py                  # Economic attacks

# For full 4-Life game demos, see: https://github.com/dp-web4/4-life
```

---

## 📊 Repository Structure

```xlsl
web4/
├── web4-core/                         # Reference Rust + Python SDK, AttestationEnvelope
├── web4-trust-core/                   # Trust tensor implementations (Rust)
├── core/                              # Cross-language shared primitives
│
├── web4-standard/                     # Core specifications and implementations
│   ├── core-spec/                    # Canonical specs (LCT, T3, MRH, ATP, R6)
│   └── implementation/
│       ├── authorization/            # PostgreSQL schemas + security mitigations
│       └── reference/                # Coordination framework
│
├── simulations/                       # Attack simulations + trust dynamics research
│
├── demo/                              # Commerce demo (delegation UI + store)
│
├── docs/                              # Documentation
│   ├── why/                          # Vision, motivation, Demo Day record
│   ├── what/specifications/          # Technical specifications
│   ├── how/                          # Implementation guides
│   ├── proof/                        # Proof points (ARC-AGI-3, etc.)
│   ├── history/                      # Research and decisions
│   └── reference/                    # Glossary, indexes, related repos, security
│
├── whitepaper/                        # Conceptual foundation
├── articles/                          # Public-facing writeups
├── forum/                             # Cross-machine discussion artifacts
├── archive/game-prototype/            # Historical: original 4-Life prototype
├── review/                            # External review artifacts
├── sessions/                          # Research session scripts and outputs
│
├── STATUS.md                          # Project status
├── SECURITY.md                        # Security research status
└── CONTRIBUTING.md                    # How to contribute
```

---

## 🤝 Related Projects

- **[HRM/SAGE](https://github.com/dp-web4/HRM)** - Edge AI kernel with MoE expert selection and trust-based routing
- **[ACT](https://github.com/dp-web4/act)** - Distributed ledger for ATP tokens and LCT presence registry (Cosmos SDK)
- **[Synchronism](https://github.com/dp-web4/Synchronism)** - Theoretical physics framework (MRH, coherence)
- **[Memory](https://github.com/dp-web4/memory)** - Distributed memory and witnessing

### Cross-Project Integration

Web4 integrates with SAGE (neural MoE) and ACT (distributed ledger) via:
- **Unified LCT Presence**: `lct://{component}:{instance}:{role}@{network}`
- **ATP Resource Allocation**: Synchronized between ledger and edge systems
- **Bidirectional Pattern Exchange**: Coordination patterns transfer between domains
- **Trust Tensor Synchronization**: Trust scores flow across system boundaries

See [`docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md`](docs/what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md) for the presence standard.

---

## 📖 Whitepaper

The Web4 whitepaper provides the conceptual foundation:

- **[Web Version](https://dp-web4.github.io/web4/whitepaper-web/)**
- **[PDF Version](https://dp-web4.github.io/web4/whitepaper-web/WEB4_Whitepaper.pdf)**

Key concepts: LCTs, MRH, Trust Tensors, ATP, Federation, Dictionaries

---

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** — see [LICENSE](LICENSE).

### Patent Notice

This software implements technology covered by patents owned by MetaLINXX Inc. A royalty-free patent license is granted for non-commercial and research use under AGPL-3.0 terms.

**For commercial licensing**: Contact dp@metalinxx.io

See [PATENTS.md](PATENTS.md) for full patent details.

---

**Research prototype. Interesting ideas. Significant gaps. Honest about both.**
