# Web4 Published Artifacts (2026-04-28)

The first public Web4 packages are live on crates.io and PyPI. This document records what shipped, where to find it, and how to pin it.

---

## Quick install

**Rust** (add to `Cargo.toml`):

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

---

## What was published

| Package | Registry | Version | Released | License |
|---|---|---|---|---|
| `web4-core` | [crates.io](https://crates.io/crates/web4-core) | **0.1.1** (0.1.0 yanked) | 2026-04-28 | AGPL-3.0-or-later |
| `web4-core` | [PyPI](https://pypi.org/project/web4-core/) | **0.1.1** | 2026-04-28 | AGPL-3.0-or-later |
| `web4-trust-core` | [crates.io](https://crates.io/crates/web4-trust-core) | **0.1.1** (0.1.0 yanked) | 2026-04-28 | AGPL-3.0-or-later |
| `web4-trust` | [PyPI](https://pypi.org/project/web4-trust/) | **0.1.1** | 2026-04-28 | AGPL-3.0-or-later |

Git tag marking the v0.1.1 release: `v0.1.1`.

### v0.1.0 → v0.1.1 (same-day re-publish)

v0.1.0 was published earlier on 2026-04-28 and **yanked from crates.io the same day** after two defects were caught by clean-install verification:

1. **Python wheel import path broken**: the `web4_core` package directory shipped without `__init__.py`, so `import web4_core` returned an empty module and `web4_core.PyLct.new(...)` (the canonical README example) failed with `AttributeError`. Fixed in v0.1.1 by adding explicit re-exports of all PyO3 classes/functions.
2. **Stale tensor docstring** in `web4-trust`'s top-level docstring described T3/V3 as "6-dimensional," contradicting the canonical 3-root + fractal RDF framing used everywhere else in the spec. Fixed in v0.1.1.

Both defects were invisible to `cargo test`, `cargo publish --dry-run`, `maturin build --release`, and in-source doctests. They were only catchable by what a real user does: `pip install web4-core` in a fresh venv and run the README example. v0.1.0 PyPI artifacts remain installable (PyPI doesn't yank), but v0.1.1 is canonical; STATUS.md flags the gap.

Released-along-with-process discipline note: clean-install verification in a fresh environment is now mandatory before any registry publish. See `feedback_pre_publish_clean_install_check.md` in the cross-machine memory.

---

## What's in `web4-core`

The foundational primitives:

- **LCT (Linked Context Token)** — Non-transferable presence tokens with Ed25519 keypair binding, parent/child lineage, status tracking (Active / Dormant / Void / Slashed), and a 5-level hardware-binding ladder.
- **T3 (Trust Tensor)** — 3 root dimensions (Talent / Training / Temperament). Each root is itself a fractal RDF sub-graph of context-specific sub-dimensions via `web4:subDimensionOf`. Observations accumulate; aggregate scores; decay over time.
- **V3 (Value Tensor)** — 3 root dimensions (Valuation / Veracity / Validity). Same fractal pattern as T3.
- **Coherence** — Multiplicative identity coherence `C × S × Φ × R` (Continuity × Stability × Phi × Reachability) with limiting-factor identification.
- **Crypto** — Ed25519 sign/verify, SHA-256 hashing.
- **Ledger** — Trait + two built-in backends:
  - `InMemoryLedger` — for tests, prototyping, ephemeral runs
  - `LocalLedger` — file-based JSON-lines hash chain. Persistent, tamper-evident, suitable for solo dev / team-scoped accountability / regulated environments.

LCTs anchor to a ledger via `lct.mint(&mut ledger)`. The ledger trait makes additional backends (e.g., `web4-act-client::ActLedger` for the ACT Cosmos chain) pluggable without changing user code.

Quick start (Rust):

```rust
use web4_core::{Lct, EntityType, InMemoryLedger, Ledger};

let (lct, keypair) = Lct::new(EntityType::Human, None);
let mut ledger = InMemoryLedger::new();
let receipt = lct.mint(&mut ledger).unwrap();

let proof = ledger.anchor(lct.id).unwrap();
assert!(ledger.verify_proof(&proof).unwrap());
```

Quick start (Python):

```python
import web4_core

lct, keypair = web4_core.PyLct.new(web4_core.PyEntityType.Human, None)
ledger = web4_core.PyInMemoryLedger()
receipt = ledger.mint(lct)

proof = ledger.anchor(lct.id)
assert ledger.verify_proof(proof)
```

---

## What's in `web4-trust-core`

Trust persistence and witnessing primitives:

- `EntityTrust` — composite T3 + V3 with witnessing relationships
- `TrustStore` — persistent storage for entity trust; JSON format
- Decay calculations (configurable)
- Cross-language: Rust core, Python bindings via PyO3

`web4-trust-core` is independent of `web4-core` (no cross-crate path dependency); both are foundational and composable.

---

## Test coverage

- `web4-core`: 52 unit tests + 4 doctests, all passing. mypy --strict clean for Python bindings.
- `web4-trust-core`: 57 tests, all passing.

---

## What's NOT in this release (deferred to v0.2+)

- `ActLedger` — HTTP/REST client to ACT's Cosmos SDK chain. Will ship as a separate crate `web4-act-client` once stabilized. The `Ledger` trait in `web4-core` is the contract; backend implementations are pluggable.
- Cross-platform Python wheels. v0.1.0 ships Linux x86_64 wheels (manylinux_2_34) plus a source distribution. Other platforms build from source (requires Rust toolchain). Cross-platform CI via `maturin-action` is planned for v0.2.
- MRH (Markov Relevancy Horizon), ATP/ADP economics, MCP integration — these live in the broader `web4-standard/implementation/sdk/` Python codebase and may be packaged separately later.

---

## Patent grant

Implementations are covered by US Patents 11,477,027 and 12,278,913, and pending application 19/178,619 (assigned to MetaLINXX Inc.). A royalty-free patent license is granted under AGPL-3.0 terms for non-commercial / research / open-source AGPL-compliant use. For commercial licensing, contact dp@metalinxx.io. Full terms in [`PATENTS.md`](../../PATENTS.md).

---

## How this compares to the canonical Web4 equation

```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

`web4-core` and `web4-trust-core` cover **LCT + T3/V3** plus the ledger substrate that makes LCTs operationally meaningful. The remaining components:

| Component | Where it lives |
|---|---|
| **MCP** (I/O membrane) | [`web4-standard/implementation/sdk/web4/mcp_server.py`](../../web4-standard/implementation/sdk/web4/mcp_server.py) |
| **RDF** (ontology backbone) | [`web4-standard/ontology/`](../../web4-standard/ontology/) (Turtle files) |
| **MRH** (context scoping) | [`web4-standard/implementation/sdk/web4/mrh.py`](../../web4-standard/implementation/sdk/web4/mrh.py) |
| **ATP/ADP** (energy economics) | [`web4-standard/implementation/sdk/web4/atp.py`](../../web4-standard/implementation/sdk/web4/atp.py) |

These are SDK-only today (Python, not yet packaged for PyPI). Future releases may consolidate or split as patterns emerge from real adoption.
