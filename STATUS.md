# Web4 Implementation Status

**Last updated:** September 8, 2026

---

## Headline

Web4 is a **working open substrate with published core packages and live reference deployments**, plus substantial unfinished work in assurance, interoperability and conformance.

The most useful evidence today is operational rather than benchmark-based:

- `web4-core` and the trust family are publicly installable;
- the **Hub** runs as a Web4 society daemon with membership, roles, signed law, sealed channels and a witnessed ledger;
- **Hestia** governs multiple agent vendors on the local machine boundary under one law, with witnessed actions, human escalation and trust derived from the chain;
- the lab developing the standard uses those same mechanisms in its own fleet;
- the current open assurance profile is explicitly **A1** - cooperative and tamper-evident, not adversary-proof containment.

**R&D, not production.** The core is real; the assurance ceiling and remaining gaps are real too.

## Current stack

| Layer | Purpose | Status |
|---|---|---|
| **Web4 core / standard** | Identity, trust, roles, action grammar, resource accounting, law, witnessing, federation | Core packages published; standard draft in places |
| **Hestia** | Local human/agent governance, vault, delegation, policy, witnessing, escalation | Running daily; A1 assurance |
| **Hub** | Society/community runtime: membership, roles, law, sealed channels, ledger | Running reference implementation |
| **Hardbound** | Metalinxx enterprise assurance: hardware roots, stronger fail-closed enforcement, evidence packaging | Private/proprietary; building |
| **SAGE** | Persistent cognition / embodiment research under the same identity and governance model | Public architecture + active research |

---

## Published artifacts

Current published package line:

| Package | Registry | Version | Install |
|---|---|---:|---|
| **web4-core** (Rust) | [crates.io](https://crates.io/crates/web4-core) | **0.3.0** | `cargo add web4-core` |
| **web4-core** (Python) | [PyPI](https://pypi.org/project/web4-core/) | **0.3.0** | `pip install web4-core` |
| **web4-trust-core** (Rust) | [crates.io](https://crates.io/crates/web4-trust-core) | **0.2.0** | `cargo add web4-trust-core` |
| **web4-trust** (Python) | [PyPI](https://pypi.org/project/web4-trust/) | **0.2.0** | `pip install web4-trust` |

`web4-core` source on `main` is **0.4.0**. The publication trail, including the yanked 0.1.0 Python wheel and subsequent correction, is in [`docs/proof/PUBLISHED.md`](docs/proof/PUBLISHED.md).

All packages are AGPL-3.0-or-later unless a subdirectory states otherwise. Patent terms and commercial licensing boundaries are in [PATENTS.md](PATENTS.md).

---

## What is working

### Core identity and trust primitives

`web4-core` provides:

- LCT presence and key binding;
- canonical T3/V3 trust/value tensors;
- identity coherence;
- local and in-memory ledger anchoring;
- witnessed `Act` primitives and reputation deltas;
- first-class role entities and role issuance;
- DID / SD-JWT-VC / OpenID4VCI/VP implementation paths;
- recursive encrypted vault substrate.

Cross-language examples demonstrate Python and Rust reading/verifying the same hash-chained ledger format.

### Hub: Web4 society runtime

[`hub/`](hub/) is a runnable Rust society daemon with:

- LCT-pinned membership;
- seven base roles;
- signed machine-readable law;
- append-only witnessed ledger;
- sealed member-to-hub channels;
- MCP, REST and admin surfaces;
- council/admission governance paths;
- governance decisions written into the same record as other consequential acts.

A standalone mirror is published at [dp-web4/4-hub](https://github.com/dp-web4/4-hub).

### Hestia: local governance runtime

[Hestia](https://github.com/dp-web4/hestia) is the local governance layer at the human/agent boundary. The reference deployment is used daily across multiple agent vendors.

Measured / exercised areas include:

- persistent local identity;
- one policy surface across different agent vendors;
- scoped delegation;
- encrypted vault;
- witnessed allow/deny/outcome records;
- human escalation;
- peer-arbitration paths;
- trust derived from the witnessed chain rather than self-reported.

**Assurance ceiling:** A1. The gate runs cooperatively in the same user security domain. It is useful for governance, attribution and stopping ordinary mistakes, but a sufficiently capable same-UID process can route around it. Hestia documents known bypasses rather than treating them as impossible.

### Standards interoperability

The repository includes implementation/spec work for:

- `did:web4`;
- SD-JWT-VC;
- OpenID4VCI / OpenID4VP;
- EUDI-oriented credential interoperability.

The honest boundary: protocol/code paths exist, but broad wallet interoperability, trust-list/legal acceptance and conformance are not finished.

### Security research

The simulation corpus contains **424 attack vectors across 84 tracks**, with roughly **85% synthetic detection** in the current test suite. This is useful regression/security research, **not a substitute for an external red team or production assurance certification**.

---

## Architectural shape now specified

Three properties that were once mostly conceptual are now explicit in the spec corpus:

1. **Self-sovereign societies.** Societies can bootstrap, federate and secede; higher-order societies are overlays formed by constituent consent, not owners of the members below them.
2. **First-class roles.** Seven base roles provide a common authority skeleton; roles may be filled by humans, AI agents, sub-societies or federations, and role law composes with society law.
3. **Cross-society action over MCP.** MCP is the inter-society I/O membrane for scoped actions/resources, with LCT-bound evidence and witnessing carried across the exchange.

See:

- [`web4-standard/core-spec/inter-society-protocol.md`](web4-standard/core-spec/inter-society-protocol.md)
- [`web4-standard/core-spec/society-roles.md`](web4-standard/core-spec/society-roles.md)
- [`web4-standard/core-spec/mcp-protocol.md`](web4-standard/core-spec/mcp-protocol.md)
- [`web4-standard/core-spec/web4-society-authority-law.md`](web4-standard/core-spec/web4-society-authority-law.md)

---

## What is not finished

| Gap | Current state |
|---|---|
| **A2+ isolation** | Not available in the open reference stack; separate principals / stronger OS boundaries remain roadmap work |
| **Kernel / relying-party enforcement** | Architectural target, not current open implementation |
| **Enterprise hardware roots** | Higher-assurance implementation belongs to Hardbound; open reference work remains partial |
| **DID/EUDI interoperability** | Code/spec paths exist; broad real-wallet / trust-list interoperability incomplete |
| **Conformance suite** | In progress; alternative implementations are not yet provably interoperable end to end |
| **Formal Sybil resistance** | Empirical defenses; no complete formal proof |
| **Economic attacks at scale** | Research/simulation only, no real-market validation |
| **External red team** | Not yet a substitute for the synthetic attack corpus |
| **Production certification** | Not claimed |

---

## Assurance model

A recurring design principle is to keep **governance** distinct from **containment**.

A1 can make rules explicit, record whether they were followed, stop many ordinary mistakes and make some bypass behavior attributable. It should not be sold as a prison for a capable process that shares the operator's privileges.

The higher-assurance path is layered:

```text
A1  cooperative user-space governance + witnessing
A2  separate principal / process isolation
A3+ stronger relying-party, hardware and OS enforcement
```

Exact profiles continue to evolve, but the direction is fixed: **the more consequential the act, the less the relying party should depend on the actor voluntarily honoring its own gate.**

---

## Historical ARC-AGI-3 note

A spring-2026 SAGE/ARC harness produced a published **94.85%** public scorecard using Claude Opus 4.6.

That artifact remains public because it was a real research milestone and because provenance matters. It is **not a current Web4 proof point or a current competition claim**:

- it used a frontier model;
- it used public engine-source / per-game solver affordances outside strict competition play;
- it did not establish the local/edge SAGE thesis;
- current competition-legal local-model work is well behind the leaders.

The archived record is in [`docs/proof/ARC-AGI-3.md`](docs/proof/ARC-AGI-3.md) and [ARC-SAGE](https://github.com/dp-web4/ARC-SAGE).

The useful historical lesson was simply that **the structure around a model can materially change behavior**. The current program is about making that structure persistent, governable, learnable and defensible under real operational constraints.

---

## Current evidence hierarchy

For evaluating Web4 today, prefer evidence in this order:

1. **Published artifacts** - crates/PyPI packages and reproducible examples.
2. **Running reference deployments** - Hub and Hestia.
3. **Measured operational behavior** - witnessed records, escalation paths, trust derivation and failure artifacts.
4. **Synthetic security simulations** - useful but limited.
5. **Specs / PRDs** - statements of intended behavior, not proof of deployment.
6. **Historical benchmark results** - provenance and research history, not current maturity evidence.
7. **Aspirational architecture** - roadmap only until exercised.

---

## Pointers

- **Start here:** [`docs/START_HERE.md`](docs/START_HERE.md)
- **Published packages:** [`docs/proof/PUBLISHED.md`](docs/proof/PUBLISHED.md)
- **Hub:** [`hub/`](hub/)
- **Hestia:** https://github.com/dp-web4/hestia
- **Ecosystem map:** [`docs/reference/RELATED_REPOS.md`](docs/reference/RELATED_REPOS.md)
- **Security:** [`SECURITY.md`](SECURITY.md)
- **Standard:** [`web4-standard/core-spec/`](web4-standard/core-spec/)
- **Historical ARC artifact:** [`docs/proof/ARC-AGI-3.md`](docs/proof/ARC-AGI-3.md)

---

*This is the living status document. Historical detail belongs in dated audit/history files rather than being allowed to masquerade as current state.*
