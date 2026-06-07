# Web4 Published Artifacts

This document records the package family releases, what shipped, where to find it, and how to pin it. For granular release notes, see the top-level [`CHANGELOG.md`](../../CHANGELOG.md).

---

## Current Release: v0.2.0 (2026-05-15)

First coordinated release closing the publish-vs-main gap accumulated since v0.1.1 (2026-04-28). Roughly 17 days and 66 commits of substantive spec, SDK, and conformance work.

### Quick install

**Rust** (add to `Cargo.toml`):

```toml
[dependencies]
web4-core = "0.2"
web4-trust-core = "0.2"
```

**Python**:

```bash
pip install web4-core
pip install web4-trust
pip install web4-sdk        # high-level SDK (import web4)
```

**JavaScript / WASM** (npm):

```bash
npm install web4-trust-core
```

### What was published

| Package | Registry | Version | Released | License |
|---|---|---|---|---|
| `web4-core` | [crates.io](https://crates.io/crates/web4-core) | **0.2.0** | 2026-05-15 | AGPL-3.0-or-later |
| `web4-core` | [PyPI](https://pypi.org/project/web4-core/) | **0.2.0** | 2026-05-15 | AGPL-3.0-or-later |
| `web4-trust-core` | [crates.io](https://crates.io/crates/web4-trust-core) | **0.2.0** | 2026-05-15 | AGPL-3.0-or-later |
| `web4-trust-core` | [npm](https://www.npmjs.com/package/web4-trust-core) | **0.2.0** | 2026-05-15 | AGPL-3.0-or-later |
| `web4-trust` | [PyPI](https://pypi.org/project/web4-trust/) | **0.2.0** | 2026-05-15 | AGPL-3.0-or-later |
| `web4-sdk` | [PyPI](https://pypi.org/project/web4-sdk/) | **0.27.0** | 2026-05-15 | AGPL-3.0-or-later |

Git tag marking the v0.2.0 release: `v0.2.0`.

### What's new in v0.2.0

#### `web4-core` (Rust crate + Python bindings)

Everything from v0.1.1, plus:

- **Society** — Self-governing collective type with law oracle, ledger, treasury, and society LCT
- **SocietyRole** — Seven base-mandatory roles (Sovereign, LawOracle, PolicyEntity, Treasurer, Administrator, Archivist, Citizen) with three-tier taxonomy
- **RoleAssignment** — Entity-to-role binding with assigner tracking and timestamps
- **ATPAccount** — Conservation-invariant transfer with society-configurable fees and max_balance
- **R6Action** — Base action grammar (Rules + Role + Request + Reference + Resource → Result)
- **R7Action** — Reputation-tracking superset of R6 (adds Reputation as first-class output)
- T3/V3 cross-language alignment: 38 tensor tests, all passing

#### `web4-trust-core` (Rust crate + npm WASM bindings)

Everything from v0.1.1, plus:

- **WASM bindings** — first npm publish (~337KB). Browser-side Society, SocietyRole, RoleAssignment, ATPAccount, R7Action
- 57 tests, all passing
- Cross-language T3/V3 alignment verified

#### `web4-sdk` (Python, high-level SDK)

New package in the v0.2.0 family. Previously published on PyPI as `web4`; renamed to `web4-sdk` because the PyPI name `web4` is held by an unrelated dormant project (author Sahil Prasad, continual.ai, last release 0.0.1). The Python import path is unchanged — `from web4 import ...` works as before.

- 23 library modules (trust, lct, atp, federation, r6, mrh, acp, dictionary, entity, capability, errors, metabolic, binding, society, role, reputation, security, protocol, mcp, attestation, validation, deserialize, generate)
- 369 exports via `web4/__init__.py`
- 2,709 tests (2,701 passing, 8 xfailed conformance gaps)
- Cross-society types: `CrossSocietyContext`, `ReputationEnvelope`, `MCPContextResource`
- Conformance test runner: 35 operator-created vectors across 4 suites
- `validate_minimum_viable()` for cross-language parity with Rust
- 7 CLI subcommands: `web4 info/validate/list-schemas/roundtrip/generate/selftest/trust`
- MCP server: 8 tools exposing SDK data operations + behavioral trust/reputation resolution
- 3 behavioral functions: `evaluate_trust_query()`, `resolve_trust()`, `process_action_outcome()`

### Spec additions shipped with v0.2.0

- **Inter-society protocol** (`core-spec/inter-society-protocol.md`): society genesis, first-contact, ATP reification sovereignty, secession/dissolution
- **Society roles** (`core-spec/society-roles.md`): three-tier role taxonomy with corporate analogues
- **MCP protocol amendments** (`core-spec/mcp-protocol.md`): §7.3–§7.6 cross-society R6/R7 via MCP; §7.7 (WIP) referent-grounded exchange rates

### Test coverage (v0.2.0)

- `web4-core` (Rust): 52 unit tests + 4 doctests + 38 T3/V3 alignment tests, all passing
- `web4-trust-core` (Rust): 57 tests, all passing
- `web4-sdk` (Python): 2,709 tests (2,701 passing, 8 xfailed conformance gaps)
- Conformance: 35 cross-language behavioral vectors across 4 suites (tensor ops, ATP, R6/R7, society/roles)

---

## What's NOT in this release (deferred to v0.3+)

- `ActLedger` — HTTP/REST client to ACT's Cosmos SDK chain. The `Ledger` trait in `web4-core` is the contract; backend implementations are pluggable.
- Cross-platform Python wheels — v0.2.0 ships Linux x86_64 wheels plus source distributions. Other platforms build from source (requires Rust toolchain).
- Hardware binding demo — `AttestationEnvelope` spec and SDK types exist; actual TPM/FIDO2/Secure Enclave binding requires the Hardbound implementation (private repo).
- Formal sybil-resistance proofs — empirical attack testing corpus (424+ vectors in `simulations/`) exists; formal proofs are intentionally deferred.

---

## Patent grant

Implementations are covered by US Patents 11,477,027 and 12,278,913, and pending application 19/178,619 (assigned to MetaLINXX Inc.). A royalty-free patent license is granted under AGPL-3.0 terms for non-commercial / research / open-source AGPL-compliant use. For commercial licensing, see [`PATENTS.md`](../../PATENTS.md).

---

## How this compares to the canonical Web4 equation

```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

v0.2.0 coverage across the package family:

| Component | Package(s) | Status |
|---|---|---|
| **LCT** (presence tokens) | `web4-core` (Rust + Python) | Published |
| **T3/V3** (trust/value tensors) | `web4-core` + `web4-trust-core` (Rust + Python + WASM) | Published |
| **ATP/ADP** (energy economics) | `web4-core` (ATPAccount) + `web4-sdk` (full lifecycle) | Published |
| **MCP** (I/O membrane) | `web4-sdk` (MCP server, 8 tools) | Published (SDK) |
| **RDF** (ontology backbone) | `web4-standard/ontology/` (Turtle files) | Spec only |
| **MRH** (context scoping) | `web4-sdk` (MRHGraph, resolve_trust) | Published (SDK) |

All equation components now have at least SDK-level implementations in published packages.

---

## Release History

### v0.2.0 (2026-05-15)

See above.

### v0.1.1 (2026-04-28)

The first public Web4 packages. Four packages across crates.io and PyPI (`web4-core`, `web4-trust-core`, `web4-trust`). Covered LCT + T3/V3 + Ledger primitives. Same-day re-publish from v0.1.0 after two defects caught by clean-install verification:

1. **Python wheel import path broken**: `web4_core` shipped without `__init__.py`. Fixed in v0.1.1.
2. **Stale tensor docstring**: described T3/V3 as "6-dimensional" vs canonical 3-root + fractal RDF. Fixed in v0.1.1.

v0.1.0 was yanked from crates.io. Both defects were only catchable by clean-install verification in a fresh environment — now mandatory before any registry publish.

### v0.1.0 (2026-04-27)

Initial release. Yanked; see v0.1.1.
