# Introduction

> **Status (2026-04-29)**: This whitepaper documents Web4 — a research program proposing trust-native architecture for an internet that includes AI agents as participants. Some of what's described below is **shipped and installable** (`web4-core` 0.1.1 and `web4-trust-core` 0.1.1 on crates.io and PyPI; the agent-commerce-delegation demo with 166 passing tests; the AttestationEnvelope hardware-trust primitive). Some is **operational in the Hardbound CLI** as protocol-validation work (R7 action framework, ACP, Sybil-resistance proofs, multi-device LCT binding). Some is **specified but not yet built**. The Executive Summary draws explicit lines between the three; the body sections that follow describe the full architecture, with current-state markers where they apply.

This document presents WEB4 — a proposed architecture for trust, value, and intelligence in an age of autonomous collaboration between humans and AI. The work is grounded in the conventions of Web1 (access), Web2 (participation), and Web3 (ownership): the framing question is whether *verifiable presence* is the next missing layer.

The document follows a fractal structure: conceptual foundations followed by technical implementations for those who wish to build. The conceptual layer borrows from the [Synchronism](https://dpcars.net/synchronism) research program (coherence and resonance as organizing principles for sustainable systems), but Web4 itself is practical architecture — protocols, schemas, ledger backends, attestation primitives — and is evaluable on those terms.

## Core Mechanisms

WEB4 introduces and interconnects several foundational components:

- **Linked Context Tokens (LCTs)**: The reification of presence itself—non-transferable, cryptographically anchored footprints that give every entity verifiable presence in the digital realm.

- **T3 and V3 Tensors**: Multidimensional trust and value representations whose three root dimensions—Talent, Training, Temperament (T3) and Valuation, Veracity, Validity (V3)—serve as root nodes in open-ended RDF sub-graphs of contextualized sub-dimensions, bound to entity-role pairs.

- **Allocation Transfer Packet (ATP)**: A semi-fungible energy-value exchange modeled on biological ATP/ADP cycles, where work creates value and value generates energy.

- **Markov Relevancy Horizon (MRH)**: A contextual boundary governing what is knowable, actionable, and relevant within each entity's scope, implemented as a typed RDF graph.

- **RDF Ontological Backbone**: All Web4 relationships—trust tensors, MRH edges, role bindings—are expressed as typed RDF triples, enabling semantic interoperability with existing web standards and open-ended extensibility without modifying the core protocol.

- **Memory as Temporal Sensor**: A reconception of memory not as storage but as active perception of temporal patterns, building trust through witnessed experience.

## Philosophical Grounding

WEB4 emerges from [Synchronism](https://dpcars.net/synchronism)—the recognition that sustainable systems arise from coherence (internal consistency), resonance (harmonious interaction), and shared intent. While Synchronism provides the philosophical substrate, WEB4 transforms these principles into concrete protocols, measurable metrics, and implementable architectures.

Where specific Synchronism concepts add meaningful depth—such as coherence ethics or fractal organization—we reference them directly. Otherwise, we focus on practical manifestation rather than philosophical abstraction.

## Legal and Organizational Framework

The LCT framework is protected by two issued U.S. patents—[US11477027](https://patents.google.com/patent/US11477027B1) and [US12278913](https://patents.google.com/patent/US12278913B1)—with additional patents pending. These filings ensure the foundational mechanisms are recognized, while preserving the option for wide deployment and public benefit.

Funding for portions of this research and development has been provided by **MetaLINXX Inc.**, which supports the evolution of decentralized, trust-based systems and the public infrastructure required to sustain them.

Substantial portions of this work — including the published `web4-core` / `web4-trust-core` packages, simulation code, governance tools, and Web4-native protocols — are released under **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)**, with the patent grant in [PATENTS.md](https://github.com/dp-web4/web4/blob/main/PATENTS.md) (royalty-free for non-commercial and research use, AGPL-bounded). The open-source license and patent grant together aim to foster an ecosystem open to audit, extension, and shared stewardship.

## An Invitation to Participate

To participate in ongoing development or collaborative application of the WEB4 framework, please contact:

📩 **dp@metalinxx.io**

We invite thoughtful critique and aligned contribution. This is not a finished system; it is research-stage work being developed in the open. Engagement at any depth — from running the published packages to challenging specification details — is welcome.