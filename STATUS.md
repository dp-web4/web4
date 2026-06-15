# Web4 Implementation Status

**Last Updated**: June 15, 2026

---

## Headline

Web4 is a **working ontology** with **real proof points** and **real gaps**. R&D, not production. The spec corpus is stable; reference implementations exist; some demonstrations have moved from inferred to measured. **As of 2026-04-28, the core primitives are publicly installable.**

**The architectural shape is now explicitly specified.** Three core-spec updates (2026-05-13 + 2026-05-14) make the previously-inferable structural properties normative:
- [`inter-society-protocol.md`](web4-standard/core-spec/inter-society-protocol.md) — society genesis (self-bootstrapped + federation-based), first-contact protocol (three sovereign options), ATP as unit-of-account with society-sovereign reification, secession/dissolution
- [`society-roles.md`](web4-standard/core-spec/society-roles.md) — seven base-mandatory roles (Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator, Archivist, Citizen) + context-mandatory (forced by outward role) + optional, with fractal composability semantics
- [`mcp-protocol.md`](web4-standard/core-spec/mcp-protocol.md) — **v0.1.3 amendment (2026-05-14)** adds explicit cross-society binding (§1.1, §7.3 R7, §7.4 cross-society LCT envelope, §7.5 witnessing + Reputation propagation). **Cross-society R6/R7 action protocol is now spec'd** — and the spec recognizes that MCP IS the inter-society interface per the canonical equation, not a missing layer. Three previously-deferred inter-society gaps (cross-society actions, society-society trust tensors, exchange-rate negotiation transport) are resolved by this amendment.

The Web4 anti-hierarchical-by-design property is now stated normatively in spec rather than inferred from the ontology.

The strongest single proof point: **the same Claude Opus 4.6 you can use today scores 0% on ARC-AGI-3 by default and 94.85% with a Web4-shaped harness around it**. The model didn't change. The structure around the model did.

Public scorecard: https://arcprize.org/scorecards/c7dfb4f1-8642-4c9e-ab4d-152f5f8e33b4

The strongest single external validation: a 2026-05-13 three-round Kimi 2.6 cross-model review scored architectural coherence 8.5/10 and bootstrap-story 8/10, while sharpening the unit-of-account framing for ATP and surfacing the inter-society protocol gap that the two new specs now address. Verbatim transcript: [`forum/kimi2_6_review.md`](forum/kimi2_6_review.md).

**Recent (June 2026): standards interop + a storage doctrine.**

- **EUDI / W3C-DID interop (code; Phase 0–2 done).** An LCT is now resolvable as a `did:web4` DID Document (W3C DID Core) and expressible as an IETF **SD-JWT-VC** credential, issued/presented over **OpenID4VCI / OpenID4VP** — all in `web4-core` (`did`, `sd_jwt_vc`, `oid4vc`). Person-scale (hestia) and society-scale (hub) issuers, plus a society-scale verifier, complete the round trip. The honest framing: inside the EUDI envelope Web4 is a *credential-format + protocol citizen*; its native trust layer (T3/V3, witnessing) lives outside the envelope, and the remaining gate is **trusted-list membership — governance/legal, not code**. Plan: [`docs/strategy/eudi-resolvability-plan.md`](docs/strategy/eudi-resolvability-plan.md); method spec: [`web4-standard/core-spec/did-web4-method.md`](web4-standard/core-spec/did-web4-method.md).
- **Vault doctrine (code; in progress).** All settings, identity, and state across the stack move into an encrypted, **recursive, memory-only-unlock** vault (`web4_core::vault`): no plaintext secrets or config at rest, per-item independent locking + liveness gating, and fresh-launch naivety (nothing instance-specific is readable until unlock). Reference substrate is in `web4-core`; rollout is underway across hub/hestia/hardbound.

---

## Published artifacts (current: v0.1.1, 2026-04-28)

| Package | Registry | Version | Install |
|---|---|---|---|
| **web4-core** (Rust) | [crates.io](https://crates.io/crates/web4-core) | 0.1.1 | `cargo add web4-core` |
| **web4-core** (Python) | [PyPI](https://pypi.org/project/web4-core/) | 0.1.1 | `pip install web4-core` |
| **web4-trust-core** (Rust) | [crates.io](https://crates.io/crates/web4-trust-core) | 0.1.1 | `cargo add web4-trust-core` |
| **web4-trust** (Python) | [PyPI](https://pypi.org/project/web4-trust/) | 0.1.1 | `pip install web4-trust` |

> v0.1.0 yanked from crates.io: the Python `web4-core` wheel shipped without `__init__.py`, so `import web4_core` returned an empty module. Fixed in v0.1.1; v0.1.0 PyPI artifacts remain installable but `web4-trust`'s docstring also incorrectly described tensors as "6-dimensional" (canonical: 3 root dims, fractally extensible via `web4:subDimensionOf`). Use v0.1.1.

All AGPL-3.0-or-later. Patent grant terms: [PATENTS.md](PATENTS.md). Commercial licensing: contact Metalinxx Inc. via the [project repository](https://github.com/dp-web4/web4).

`web4-core` provides LCT (Linked Context Token) primitives + T3/V3 trust tensors + identity coherence + ledger anchoring (`InMemoryLedger`, `LocalLedger`). `web4-trust-core` adds trust persistence and witnessing primitives. The Python wheels are PyO3-built bindings over the same Rust core.

---

## What's working

| Layer | Status | Where |
|---|---|---|
| **Spec corpus** (LCT, T3/V3, MRH, ATP/ADP, R6/R7) | Stable | [`web4-standard/core-spec/`](web4-standard/core-spec/) |
| **Inter-society protocol spec** (genesis, first-contact, federation, secession) | v0.1.2 DRAFT, 2026-05-13 | [`web4-standard/core-spec/inter-society-protocol.md`](web4-standard/core-spec/inter-society-protocol.md) |
| **Society roles spec** (7 base-mandatory + context-mandatory + optional) | v0.1.0 DRAFT, 2026-05-13 | [`web4-standard/core-spec/society-roles.md`](web4-standard/core-spec/society-roles.md) |
| **`web4-core`** | **Published v0.1.1** (crates.io + PyPI). LCT, T3/V3, Coherence, Ledger trait + 2 backends (InMemory, Local file). 52 unit tests + 4 doctests. | [`web4-core/`](web4-core/) |
| **`web4-trust-core`** | **Published v0.1.1** (crates.io + PyPI). Trust storage, witnessing, decay. | [`web4-trust-core/`](web4-trust-core/) |
| **Runnable proof of presence** | `python identity_bootstrap.py` — bootstraps a host LCT (keypair on disk, hash-chained `LocalLedger`, public `lct.json` sidecar); `--verify` re-checks the chain on re-run. ~30 sec. | [`web4-core/python/examples/identity_bootstrap.py`](web4-core/python/examples/identity_bootstrap.py) |
| **Cross-language interop demo** | Python mints an LCT to a hash-chained ledger; a Rust binary reads the same `ledger.jsonl` and verifies chain integrity + anchor proof. The on-disk format is the contract. | [`web4-core/examples/cross_language_verify/`](web4-core/examples/cross_language_verify/) |
| **Reference Python SDK** | 2,627 tests, mypy --strict clean (not yet on PyPI separately) | [`web4-standard/implementation/`](web4-standard/implementation/) |
| **Cognition harness producing 94.85%** | Open source | [SAGE](https://github.com/dp-web4/SAGE) |
| **Attack simulation suite** | 424 vectors / 84 tracks, ~85% detection rate against **synthetic** adversaries. No red team engagement yet; some "defenses" are standard infosec practices (TEMPEST, Faraday) documented for completeness rather than as Web4-novel mechanisms. See [`simulations/README.md`](simulations/README.md) for honest breakdown. | [`simulations/`](simulations/) |
| **Threat model** | v2.0 | [`docs/reference/security/THREAT_MODEL.md`](docs/reference/security/THREAT_MODEL.md) |
| **Authorization layer** | PostgreSQL schemas + security mitigations | [`web4-standard/implementation/authorization/`](web4-standard/implementation/authorization/) |
| **Coordination framework** (Phase 2a–2d) | Validated | [`web4-standard/implementation/reference/`](web4-standard/implementation/reference/) |

---

## What's missing (this public repo)

| Gap | Where it stands | Where production lives |
|---|---|---|
| Hardware binding reference (TPM 2.0 on real devices) | Python `AttestationEnvelope` shipped; Rust port and on-device integration in progress | **Hardbound** (Metalinxx Inc. enterprise; inquire via [project repository](https://github.com/dp-web4/web4)) |
| Economic attack modeling at scale | Empirical defenses only; no real-market testing | Open research |
| Formal Sybil-resistance proofs | Empirical defenses only | Open research |
| Production deployment | All testing is synthetic | Hardbound for regulated environments |

---

## Where it landed publicly

- **AI Demo Day 4** (2026-04-26): Web4 presented as "verifiable presence" for agentic AI. See [`docs/why/DEMO_DAY_2026-04.md`](docs/why/DEMO_DAY_2026-04.md). Slides + narration archived at https://4-gov.org/demo.
- **Public scorecard**: https://arcprize.org/scorecards/c7dfb4f1-8642-4c9e-ab4d-152f5f8e33b4 (verifiable from any browser).

---

## Open questions

These are not gaps to fix; they are research questions:

- Are stake amounts actually deterrent? (no economic modeling at scale)
- Does witness diversity resist sophisticated cartels?
- What's the minimal viable Web4 for a public pilot?
- How does the harness-effect (the 94.85% delta) generalize across reasoning tasks beyond ARC-AGI-3?
- How does the same harness perform with smaller models?

---

## Pointers for deeper reading

- **Public framing**: [`docs/why/DEMO_DAY_2026-04.md`](docs/why/DEMO_DAY_2026-04.md)
- **The proof point in detail**: [`docs/proof/ARC-AGI-3.md`](docs/proof/ARC-AGI-3.md)
- **Ecosystem map**: [`docs/reference/RELATED_REPOS.md`](docs/reference/RELATED_REPOS.md)
- **Conceptual foundation**: [`whitepaper/`](whitepaper/)
- **Full historical status (Q4 2025 – Q1 2026)**: [`docs/history/STATUS-2026-02.md`](docs/history/STATUS-2026-02.md)

---

*This is the living STATUS.md, kept short and current. Long-form historical detail lives in `docs/history/`.*
