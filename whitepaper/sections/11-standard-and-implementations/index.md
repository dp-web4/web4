# The Standard and Current Implementations

Web4 is developed in the open as a **normative standard with reference implementations**. This section is the map from the concepts in this paper to the artifacts you can read, run, and challenge.

## The standard

**[`web4-standard/`](https://github.com/dp-web4/web4/tree/main/web4-standard)** is the canonical specification tree:

- **[`core-spec/`](https://github.com/dp-web4/web4/tree/main/web4-standard/core-spec)** — the normative documents: one spec per mechanism this paper introduced (LCT, T3/V3, MRH, ATP/ADP, MCP, R6/R7, SAL, ACP, dictionaries, entity types, the `did:web4` DID method, security framework, error taxonomy)
- **[`ontology/`](https://github.com/dp-web4/web4/tree/main/web4-standard/ontology)** — the RDF backbone as machine-readable artifacts (Turtle ontologies, JSON-LD contexts)
- **[`test-vectors/`](https://github.com/dp-web4/web4/tree/main/web4-standard/test-vectors)** and **[`profiles/`](https://github.com/dp-web4/web4/tree/main/web4-standard/profiles)** — conformance vectors by subsystem, and deployment profiles (edge device, cloud service, peer-to-peer)

Specification status is marked per document — some are v1.0 core specifications, others are drafts under active revision. The standard is versioned in public; its history is its changelog.

## Reference implementations

Concepts prove themselves by running. Three public codebases currently implement the standard, at different layers:

**Core packages — the primitives as libraries.** [`web4-core` and `web4-trust-core`](https://github.com/dp-web4/web4) ship the LCT presence primitive, T3/V3 tensors, ledger backends, and attestation envelope as installable packages (Rust crates, Python wheels, and WASM browser bindings on crates.io, PyPI, and npm).

**The Hub — a running Web4 society.** [`web4/hub`](https://github.com/dp-web4/web4/tree/main/hub) is a live society implementation: LCT-pinned membership, sealed member-to-member channels, a witnessed hash-chained ledger as the society's collective memory, law published as inspectable data gating actions, and role assignment through governance. It is where the SAL pattern, the witnessing fabric, and the membrane security model run as a daemon rather than a diagram — and it is operated in production by the project itself for its own multi-agent coordination.

**Hestia — agent governance at the membrane.** [`hestia`](https://github.com/dp-web4/hestia) implements the trust architecture at the individual-agent boundary: policy evaluation gating agent tool use (the MCP membrane made enforceable), role-scoped law for autonomous sessions, and fail-closed defaults for unattended operation. It is the reference for Web4's answer to the question this paper opened with — how an agent is bounded *before* it acts.

These are research-stage implementations, offered as existence proofs and starting points — not finished products. They are also the standard's proving ground: several normative requirements (fail-closed policy defaults, role-scoped trust, law-as-data) were hardened *by* operating these systems and folding what broke back into the specification.

## Ecosystem bridges

Web4 is designed to compose with adjacent standards rather than replace them: the [`did:web4` method](https://github.com/dp-web4/web4/blob/main/web4-standard/core-spec/did-web4-method.md) bridges LCTs to W3C Decentralized Identifiers, credential formats align with the verifiable-credentials world, and the RDF backbone speaks the existing semantic web. The intent is an internet upgraded in place, not a parallel one.
