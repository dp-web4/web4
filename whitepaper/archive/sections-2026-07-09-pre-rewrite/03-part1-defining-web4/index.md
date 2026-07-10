# Part 1: Introduction to WEB4

## 1.1. Defining WEB4

WEB4 is a proposed framework for an internet layer in which interactions are based on **verifiable trust and shared context** — particularly in environments where AI agents are participants alongside humans. Web2 was defined by platform-centric structures where centralized entities controlled data and user interaction. Web3 emphasized decentralization through token-driven economies and blockchain technologies. Web4 proposes a further transition: trust as a first-class primitive of the protocol layer, not an emergent property of platforms or financial incentives.

The core question Web4 asks is whether trust can be made cryptographically verifiable, dynamically updated, and ontologically structured (via RDF) — and whether such an architecture provides a useful substrate for human–AI collaboration that current architectures don't.

The framing — Web2 platform-driven, Web3 token-driven, Web4 trust-driven — is positioning, not science. It is evaluable on whether the resulting protocols and primitives carve a useful joint that current alternatives (DIDs, VCs, MCP authorization, OAuth, Solid) don't already address. Subsequent parts of this whitepaper describe those primitives in detail; the [STATUS.md](https://github.com/dp-web4/web4/blob/main/STATUS.md) and [Executive Summary](../00-executive-summary/) draw explicit lines between what is currently shipped, what is operational in the Hardbound CLI as protocol-validation work, and what remains specification.

## 1.2. The Problem Web4 Is Trying to Address

The concrete problem: AI agents are increasingly autonomous — making purchases, executing code, interacting with services, taking decisions on behalf of users — and current authorization architectures don't answer two questions cleanly:

1. **How do I know an agent will act appropriately in a given context, before it acts?** Current approaches: trusting the platform that hosts it (Web2), trusting whoever holds the keys (Web3). Neither addresses behavioral capability or contextual fit.
2. **How do I prove what an agent actually did, after the fact, in a way that doesn't depend on a single trusted intermediary?** Current approaches: platform logs (revocable, manipulable), blockchain records (limited expressivity, often incompatible with off-chain action). Neither produces a witnessed audit trail with the granularity to support trust-graph reasoning.

These are not future problems. They are current problems in agent-commerce delegation, agent-tool authorization, and any system where multiple agents (human or AI) need to coordinate without a single trusted referee. Web4's proposal is that solving them requires:

- A **non-transferable presence primitive** anchored in cryptographic identity, with extensible context (LCT)
- A **multi-dimensional trust representation** that captures behavioral capability beyond identity (T3 tensor)
- A **value-creation accounting** that links contribution to allocation (ATP/ADP cycle)
- A **contextual scoping mechanism** that bounds what's relevant for any decision (MRH)
- A **shared ontological layer** so all of the above interoperate across implementations (RDF)

The presence and trust layers — LCT and T3 — are partially shipped as of 2026-04-29 (`web4-core` 0.1.1, `web4-trust-core` 0.1.1, working agent-commerce demo). The ATP/ADP value cycle is operational in the Hardbound CLI as protocol-validation work but is **not yet in the public packages**. MRH and the full RDF graph are specified and being progressively implemented. Whether this is the right *factoring* of the problem — versus, say, building on DIDs/VCs or extending MCP authorization — is a sociological question about adoption, evaluable only over time.

## 1.3. Goals

Web4's stated design goals, in evaluable form:

1. **Verifiable trust without central declaration.** Trust should be a computable function of witnessed interactions, not a permission granted by a platform. Status: partially implemented. T3 tensors in `web4-trust-core` 0.1.1 capture the multidimensional structure (Talent / Training / Temperament, each a fractally extensible RDF sub-graph). Witnessing primitives in `web4-core` 0.1.1's Ledger backends. Cross-machine peer-witness scans operational across the dp-web4 fleet (see [`heterogeneous-identity` design note](https://github.com/dp-web4/web4/blob/main/docs/specs/heterogeneous-identity.md)).

2. **Value tied to contribution, not speculation.** Allocation tracked through an ATP/ADP cycle modeled on biological energy metabolism: discharge through use, reload through witnessed contribution. Status: protocol-level mechanics operational in the Hardbound CLI (recharge, team pools, dynamic action costs, anti-gaming caps). Public reference implementation: pending.

3. **Coordination across human and AI agents.** Roles, responsibilities, and authorization expressed cryptographically and revocably. Status: working agent-commerce-delegation demo with 166 passing tests; R7 action framework operational in Hardbound; ACP (Agentic Context Protocol) lifecycle integration validated end-to-end.

4. **Systemic coherence as observable property.** The protocol should make it possible to *measure* coherence (e.g., the C × S × Φ × R coherence formula in `web4-core`), not just assume it. Status: coherence primitives shipped; sociotechnical-scale validation pending real deployment.

These goals are testable. The whitepaper sections that follow describe the mechanisms in detail; the [Implementation Examples](../09-part7-implementation-examples/) section shows what currently runs.

## 1.4. Overview of Key Components

Web4's architecture has five tightly-coupled components. Each is described in detail in subsequent parts; this section is the orientation map. Status notes indicate what is currently shipped, operational in Hardbound, or specified.

The components are listed in **dependency order** — each builds on the ones before it, from presence up to value feedback.

1. **Linked Context Tokens (LCTs)** — non-transferable, cryptographically bound presence primitives. Each LCT is permanently associated with one entity (human, AI, organization, role, task, or resource) and accumulates witnessed interactions over its lifecycle. LCTs are the substrate from which identity and reputation are built; they support multi-device binding, multi-factor witnessing (the [constellation pattern](https://github.com/dp-web4/web4/blob/main/docs/specs/heterogeneous-identity.md)), and parent/child lineage with cryptographically-anchored revocation. **Status**: core primitive shipped in `web4-core` 0.1.1; multi-device binding operational in Hardbound; full witness-web protocol specified.

2. **T3/V3 Tensors** — multi-dimensional records of capability and contribution, built directly on LCT presence.
   * **T3** (Trust Tensor): three root dimensions — **T**alent, **T**raining, **T**emperament — each itself an open-ended RDF sub-graph of context-specific sub-dimensions linked via `web4:subDimensionOf`. Not a fixed-size 3-vector; a fractal extensibility pattern.
   * **V3** (Value Tensor): three root dimensions — **V**aluation, **V**eracity, **V**alidity — same fractal RDF pattern.
   Both tensors are bound to **entity-role pairs** via RDF triples — trust is a relationship, not a property. **Status**: T3 and V3 shipped in `web4-trust-core` 0.1.1; sub-dimension extensibility working; observation/decay logic shipped.

3. **Markov Relevancy Horizon (MRH)** — contextual scoping mechanism. Defines an entity's zone of influence, comprehension, and authorization as a typed RDF graph rather than a flat boundary. Trust propagates through MRH edges with decay. **Status**: 134 RDF triples operational in Hardbound, Turtle export, trust-propagation through graph paths with decay (41/41 integration checks).

4. **R6 / R7 Action Framework** — the grammar of every Web4 action. R6 = **R**ules / **R**ole / **R**equest / **R**eference / **R**esource → **R**esult. R7 = R6 + **R**eputation as a first-class output. Every cryptographically-signed action in Web4 follows this shape, making cross-system audit possible. **Status**: R7 operational in Hardbound (62/62 integration checks); composes with the ACP (Agentic Context Protocol) plan→intent→law-check→approve→execute→record lifecycle (28/28 checks).

5. **Allocation Transfer Packet (ATP/ADP cycle)** — the value-feedback layer that rides on top of the foundation above. A semi-fungible energy-value cycle modeled on biological ATP/ADP: use discharges ATP into ADP; witnessed contribution (assessed through the trust tensors) recharges ADP back to ATP. The cycle is both a metaphor and a concrete protocol — discharge and recharge are first-class operations with anti-gaming constraints — and it closes the loop from contribution back to allocation. It is a *feedback mechanism, not a foundation*, and it is the least-mature of the five in public code. **Status**: protocol operational in Hardbound CLI (recharge, team pools, dynamic action costs, anti-gaming caps, formally proven Sybil resistance via 5 theorems and 4 game-theoretic models); **not** in the public `web4-core` packages — public reference implementation pending.

These five components share a common substrate: **RDF triples** as the typed-relationship backbone. RDF is what makes Web4 extensible without central coordination — anyone can add a sub-dimension to T3, an MRH edge type, or a witness relationship without modifying the core protocol. LCTs anchor presence; T3/V3 measure capability and contribution; MRH bounds context; R6/R7 grammar it all together as auditable actions; and the ATP/ADP cycle feeds value back to where work was done.