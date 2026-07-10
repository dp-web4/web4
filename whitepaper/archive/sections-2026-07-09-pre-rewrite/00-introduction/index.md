# Introduction

WEB4 is a proposed architecture for trust, value, and intelligence in an age where AI agents act alongside
humans. The web arrived in layers — Web1 gave us access, Web2 gave us participation, Web3 gave us ownership.
Each solved the problem the last one left open. The problem now open is **trust between diverse
intelligences**: when an autonomous agent makes a purchase, executes code, or takes a decision on your
behalf, how do you know it will act appropriately *before* it acts — and prove what it did *after* — without
handing a single platform the power to decide? Web4's wager is that the missing layer is **verifiable
presence**: trust as a first-class primitive of the protocol itself, earned through witnessed contribution
rather than granted by a platform or bought with a token.

This document makes that case and then builds it. It is written to be read at the depth that serves you.

## How to read this document

The whitepaper follows a **fractal structure** — conceptual foundations first, technical implementation for
those who wish to build, each level containing the whole. The layers build in dependency order:

> **presence (LCTs)** → **capability & trust (T3/V3)** → **context (MRH)** → **the grammar of action (R6/R7)**
> → **value feedback (ATP/ADP)** → **memory as temporal sensing**

Each layer assumes only the ones before it. The [Executive Summary](../00-executive-summary/) gives the whole
arc — the why, the what, and an honest, explicitly-drawn line between what is **shipped**, what is
**operational in the Hardbound CLI** as protocol-validation work, and what is **still specification**. The
body sections carry current-state markers where they apply, so a reader can always tell vision from
deployed code.

The conceptual layer borrows from the [Synchronism](https://dpcars.net/synchronism) research program
(coherence and resonance as organizing principles for sustainable systems), but Web4 itself is practical
architecture — protocols, schemas, ledger backends, attestation primitives — and is evaluable on those terms.

## Philosophical Grounding

WEB4 emerges from [Synchronism](https://dpcars.net/synchronism)—the recognition that sustainable systems arise from coherence (internal consistency), resonance (harmonious interaction), and shared intent. While Synchronism provides the philosophical substrate, WEB4 transforms these principles into concrete protocols, measurable metrics, and implementable architectures.

Where specific Synchronism concepts add meaningful depth—such as coherence ethics or fractal organization—we reference them directly. Otherwise, we focus on practical manifestation rather than philosophical abstraction.

## Legal and Organizational Framework

The LCT framework is protected by two issued U.S. patents—[US11477027](https://patents.google.com/patent/US11477027B1) and [US12278913](https://patents.google.com/patent/US12278913B1)—with additional patents pending. These filings ensure the foundational mechanisms are recognized, while preserving the option for wide deployment and public benefit.

Funding for portions of this research and development has been provided by **MetaLINXX Inc.**, which supports the evolution of decentralized, trust-based systems and the public infrastructure required to sustain them.

Substantial portions of this work — including the published `web4-core` / `web4-trust-core` packages, simulation code, governance tools, and Web4-native protocols — are released under **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)**, with the patent grant in [PATENTS.md](https://github.com/dp-web4/web4/blob/main/PATENTS.md) (royalty-free for non-commercial and research use, AGPL-bounded). The open-source license and patent grant together aim to foster an ecosystem open to audit, extension, and shared stewardship.

## An Invitation to Participate

To participate in ongoing development or collaborative application of the WEB4 framework, please reach out via the [project repository](https://github.com/dp-web4/web4).

We invite thoughtful critique and aligned contribution. This is not a finished system; it is research-stage work being developed in the open. Engagement at any depth — from running the published packages to challenging specification details — is welcome.