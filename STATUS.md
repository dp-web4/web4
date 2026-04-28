# Web4 Implementation Status

**Last Updated**: April 27, 2026

---

## Headline

Web4 is a **working ontology** with **real proof points** and **real gaps**. R&D, not production. The spec corpus is stable; reference implementations exist; some demonstrations have moved from inferred to measured.

The strongest single proof point: **the same Claude Opus 4.6 you can use today scores 0% on ARC-AGI-3 by default and 94.85% with a Web4-shaped harness around it**. The model didn't change. The structure around the model did.

Public scorecard: https://arcprize.org/scorecards/c7dfb4f1-8642-4c9e-ab4d-152f5f8e33b4

---

## What's working

| Layer | Status | Where |
|---|---|---|
| **Spec corpus** (LCT, T3/V3, MRH, ATP/ADP, R6) | Stable | [`web4-standard/core-spec/`](web4-standard/core-spec/) |
| **Reference Python SDK** | 2,627 tests, mypy --strict clean | [`web4-standard/implementation/`](web4-standard/implementation/) |
| **`web4-core` (MIT)** | AttestationEnvelope spec + Python impl shipped | [`web4-core/`](web4-core/) |
| **`web4-trust-core` (Rust, MIT)** | Trust tensors in Rust | [`web4-trust-core/`](web4-trust-core/) |
| **Cognition harness producing 94.85%** | Open source | [SAGE](https://github.com/dp-web4/SAGE) |
| **Attack simulation suite** | 424 vectors / 84 tracks, ~85% detection | [`simulations/`](simulations/) |
| **Threat model** | v2.0 | [`docs/reference/security/THREAT_MODEL.md`](docs/reference/security/THREAT_MODEL.md) |
| **Authorization layer** | PostgreSQL schemas + security mitigations | [`web4-standard/implementation/authorization/`](web4-standard/implementation/authorization/) |
| **Coordination framework** (Phase 2a–2d) | Validated | [`web4-standard/implementation/reference/`](web4-standard/implementation/reference/) |

---

## What's missing (this public repo)

| Gap | Where it stands | Where production lives |
|---|---|---|
| Hardware binding reference (TPM 2.0 on real devices) | Python `AttestationEnvelope` shipped; Rust port and on-device integration in progress | **Hardbound** (enterprise, contact dp@metalinxx.io) |
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
