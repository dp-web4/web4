# Executive Summary: The Trust-Native Internet

AI agents now make purchases, execute code, and take decisions on behalf of the humans they serve. Our
internet has no native way to answer the two questions this raises: *how do I know an agent will act
appropriately, before it acts?* and *how do I prove what it actually did, after the fact, without trusting a
single intermediary?* Platforms answer with revocable logs; blockchains answer with tokens and limited
expressivity. Neither makes **trust itself** verifiable.

WEB4 asks whether trust can be a first-class primitive of an internet for humans and AI agents — earned through witnessed contribution, expressed through a typed RDF ontology, anchored cryptographically. The framing borrows from the conventions of Web1 (access), Web2 (participation), Web3 (ownership): the question is whether *verifiable presence* is the next missing layer.

The vision below is ambitious. The work tests the vision. The boundary between what's tested and what's still vision is named explicitly throughout — and drawn out in full in the [Implementation Status](#implementation-status) section, not glossed. Most of what follows is specification, not deployed code, and the document says so wherever it applies.

> **Findings vs Framings**: This whitepaper mixes two categories of claim — *findings* (working implementations, passing tests, the public scorecard) and *framings* (analogies and philosophical positioning that orient how the architecture is read). Both matter; conflating them is the failure mode external reviewers flag most often. The "Implementation Status" subsection below lists the findings; the analogies in the body sections (Linux/GNU/distribution, biological-membrane, trust-as-gravity, memory-as-temporal-sensor) are framings. The Conclusion expands this distinction; Appendix J discloses the methodology that makes the distinction load-bearing.

## The Core Innovation

At the heart of WEB4 lies a simple yet profound shift: **presence is witnessed, witnessed presence builds trust, and contribution generates value**—and the relationships between them are expressed through a formal ontology, typed, extensible, and machine-readable.

The architecture builds in layers, each assuming only the ones before it.

**Presence — Linked Context Tokens (LCTs).** Every entity—human, AI, device, organization, or role—gains a cryptographic footprint in the digital realm. This is not merely an identifier but a reification of presence itself—a node in a cross-linked graph of witnessed interactions. An LCT crystallizes the moment an entity enters Web4 and accompanies it throughout its participation. Its strength is not absolute security but structural resilience: the more an LCT is witnessed, linked, and contextualized, the more robust its presence becomes. Every action, every contribution, every interaction accumulates into a trust history that belongs to no one else.

**Trust — the T3/V3 tensors.** On that presence, Web4 measures capability and contribution as multi-dimensional, typed relationships rather than flat scores. **T3** (Talent, Training, Temperament) captures what an entity can be trusted to do; **V3** (Valuation, Veracity, Validity) captures the worth of what it produces. Each dimension is not a number but an open-ended RDF sub-graph, refinable with context-specific sub-dimensions, and bound to an entity-*role* pair — trust is a relationship, contextual, not a global reputation score. Presence makes an entity real; the tensors make it *trustable*.

**Value feedback — the Allocation Transfer Packet (ATP/ADP cycle).** Built on top of the trust layer, ATP closes the loop from contribution back to allocation. Modeled on the biological ATP/ADP cycle, work discharges energy (ATP→ADP) and witnessed, recognized contribution recharges it (ADP→ATP). This is not mining or staking—it's genuine contribution recognized by genuine benefit, a thermodynamic accounting that makes value track work rather than speculation. It is a *feedback mechanism riding on presence and trust, not a foundation beneath them* — and, of the core components, the least far along toward a public reference implementation (see Implementation Status).

**Memory as Temporal Sensing.** Finally, memory is reconceived from storage into active perception. Memory doesn't just record the past; it actively perceives temporal patterns, building trust through witnessed experience. Every interaction leaves a trace, every trace can be witnessed, and every witness strengthens the fabric of collective trust.

## Why Now?

Artificial intelligence has reached a threshold. AI agents can now engage in complex reasoning, creative problem-solving, and autonomous action. Yet our internet remains built for human-to-human or human-to-server interaction. We lack the infrastructure for genuine human-AI collaboration, for trust between diverse intelligences, for value that transcends financial tokens.

Meanwhile, the limitations of previous paradigms grow clearer. Web2's platform monopolies extract value rather than create it. Web3's token speculation often rewards hype over utility. Both lack mechanisms for genuine trust—the kind that emerges from repeated, successful interaction rather than central declaration or economic incentive.

WEB4 addresses these limitations not through incremental improvement but through fundamental reconception. This is infrastructure for an age where intelligence is distributed, where collaboration spans species boundaries, and where trust must be earned through demonstrated coherence.

## The Path Forward

WEB4 emerges from the philosophical framework of [Synchronism](https://dp-web4.github.io/Synchronism/)—the recognition that coherence, resonance, and shared intent form the basis of all sustainable systems. But it manifests as practical architecture: protocols you can implement, structures you can build upon, networks you can join.

This whitepaper presents both vision and blueprint. The conceptual sections explore what becomes possible when trust becomes native to the internet itself. The implementation sections describe proposed architectures for those exploring the design space. Like a fractal, each level contains the whole—you can engage at the depth that serves your purpose.

### Implementation Status

**This whitepaper primarily presents the Web4 vision architecture.** Implementation is in early stages, with components at varying levels of maturity.

The strongest single proof point to date: **0% → 94.85% on ARC-AGI-3** with the same Claude Opus 4.6 driven through the SAGE harness ([public scorecard](https://arcprize.org/scorecards/c7dfb4f1-8642-4c9e-ab4d-152f5f8e33b4)) — a measurable demonstration that the coherence/trust architecture changes what an unchanged model can do. Below, components by maturity:

**Currently Available** (ready for testing):
- **`web4-core` and `web4-trust-core` v0.2.0** (published 2026-05-15 to crates.io, PyPI, and npm; supersedes v0.1.1 from 2026-04-28): the LCT presence primitive, T3/V3 trust tensors (3 root dims, fractally extensible via `web4:subDimensionOf`), coherence scoring, in-memory and on-disk Ledger backends, the AttestationEnvelope hardware-trust primitive, and new in v0.2.0 — Society / SocietyRole / RoleAssignment types, ATPAccount with conservation-invariant transfer (society-configurable fees + max_balance), and R7Action with reputation as first-class output. Install: `cargo add web4-core` / `pip install web4-core` / `npm install web4-trust-core` (the npm package is WASM bindings for the browser surface, ~337KB). Release record: [`docs/proof/PUBLISHED.md`](https://github.com/dp-web4/web4/blob/main/docs/proof/PUBLISHED.md) and [`CHANGELOG.md`](https://github.com/dp-web4/web4/blob/main/CHANGELOG.md).
- **`web4-sdk` v0.27.0** (PyPI, first publish under the renamed name; previously named `web4`): the high-level Python SDK consolidating the v0.2.0 primitives plus cross-society types (`CrossSocietyContext`, `ReputationEnvelope`, `MCPContextResource`), the inter-society protocol, and a 35-vector conformance test runner (39 tests; 5 xfailed gaps awaiting operator architectural decisions). 23 modules, 369 exports, 2,709 tests in CI. `pip install web4-sdk`; `from web4 import ...` import path unchanged.
- **Agent Authorization for Commerce**: A working proof-of-concept demonstrating core Web4 principles in a commerce context. Users can safely delegate purchasing authority to AI agents with cryptographically enforced limits, resource constraints, and instant revocation. See `/demo` for working implementation with 166 passing tests.

**Emerging Implementation** (operational in Hardbound CLI, validating Web4 protocol concepts):
- ATP/ADP energy-value metabolic cycles: recharge, team pools, dynamic action costs, anti-gaming caps
- Hash-chained team ledger with heartbeat-driven metabolic timing and Merkle-tree aggregation (8.26× ledger reduction)
- Policy-from-ledger with versioning, temporal queries, and multi-sig quorum approval
- Role-based trust infrastructure (admin/operator/agent/viewer permissions)
- End-to-end hardware trust chain: EK → TPM2 → team → AVP bridge → delegation
- Cross-bridge action delegation across trust boundaries
- **R7 action framework**: Rules/Role/Request/Reference/Resource → Result + Reputation as first-class output; composes with 10-layer governance (62/62 integration checks)
- **ACP (Agentic Context Protocol)**: plan → intent → law check → approve → execute → record lifecycle; full E2E integration with R7 + Hardbound (28/28 checks)
- **Sybil resistance**: formally proven via 5 theorems — ATP economic floor, witness detection, T3 reputation wall, combined cost analysis, 4.6× PoW / 13× PoS efficiency
- **ATP game theory**: 4 formal models proving stake deterrence; Nash-dominant cooperation when stake ≥ 2× expected gain
- **Dictionary Entity**: living semantic bridges with forward/reverse translation, multi-hop chains, ATP-staked confidence, drift detection (30/30 checks)
- **LCT federation registry**: peer-to-peer bilateral bridges, BFS resolution (max 3 hops), trust path as product of bridge trusts (29/29 checks)
- **Multi-device LCT binding**: TPM2/Phone SE/FIDO2/Software anchors, enrollment ceremony, cross-device witnessing, quorum recovery (45/45 checks)
- **Unified trust decay**: 5 composable models (exponential, metabolic, cosmological, tidal, diversity) with R7 observation reset (24/24 checks)
- **Law Oracle**: SAL "Law as Data" principle observable end-to-end; ATP limits and witness requirements enforced from versioned law norms (45/45 checks)
- **MRH graph**: trust as relational RDF — 134 triples, Turtle export, trust propagation through graph paths with decay (41/41 checks)

**Vision Components** (described in this document, not yet implemented):
- Full LCT presence and trust system with witness webs and lifecycle management
- T3/V3 tensor-based trust and value assessment, built on a formal RDF ontology with fractal sub-dimensions
- Memory as temporal sensing architecture
- Blockchain typology (Compost/Leaf/Stem/Root chains)
- Witness acknowledgment protocols

The agent authorization system and the Hardbound CLI governance stack — now including R7 reputation, ACP agent workflows, Sybil-resistance proofs, and multi-device binding — demonstrate that Web4's core principles can be implemented and tested today. The broader vision provides a roadmap for further development.

## An Invitation

This is not a product to purchase or a platform to join. This is a living fabric we weave together. Every implementation strengthens the protocol. Every participant enriches the network. Every contribution adds to our collective wisdom.

The code is open. The patents are filed for public benefit. The vision is shared.

Join us in building the trust-native internet—where memory becomes wisdom, interaction becomes trust, and intelligence becomes truly distributed.

*The revolution is not in the technology alone, but in what becomes possible when every interaction carries verifiable trust.*