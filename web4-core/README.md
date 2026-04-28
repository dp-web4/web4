# web4-core

[![License: AGPL-3.0-or-later](https://img.shields.io/badge/License-AGPL--3.0--or--later-blue.svg)](LICENSE)

Foundational primitives for the Web4 trust-native ontology, implemented in Rust with optional Python bindings via PyO3.

> **AI is already taking actions in the world. We can't prove what it did.**
> Web4 is the open standard that closes that gap.

This crate provides the cryptographic and semantic primitives — Linked Context Tokens, Trust/Value tensors, identity coherence, and Ed25519-bound presence — that compose into the larger Web4 standard.

## What's in here

- **LCT (Linked Context Token)** — Non-transferable presence tokens with hardware-bindable cryptographic identity. Parent/child lineage, status (Active/Dormant/Void/Slashed), 5-level hardware-binding ladder.
- **T3 (Trust Tensor)** — 3 root dimensions (Talent / Training / Temperament). Each root is itself an open-ended RDF sub-graph of context-specific sub-dimensions via `web4:subDimensionOf`. Fractally extensible, not a fixed-size vector.
- **V3 (Value Tensor)** — 3 root dimensions (Valuation / Veracity / Validity). Same fractal RDF pattern as T3.
- **Coherence** — Identity coherence scoring `C × S × Φ × R` (Continuity × Stability × Phi × Reachability). Multiplicative — a low score in any factor limits the whole.
- **Crypto** — Ed25519 signing/verification, SHA-256 hashing.

## Quick start

LCTs are inherently blockchain tokens. The canonical creation path **mints
them into a ledger** — `Lct::new()` alone leaves the LCT unanchored, which is
fine for tests and prototyping but not for any deployment where presence
needs to be verifiable.

```rust
use web4_core::{Lct, EntityType, T3, TrustDimension, Coherence, InMemoryLedger, Ledger};

// 1. Create an LCT (in-memory primitive)
let (lct, keypair) = Lct::new(EntityType::Human, None);

// 2. Anchor to a ledger
let mut ledger = InMemoryLedger::new();
let receipt = lct.mint(&mut ledger).unwrap();
println!("Minted at index {}, hash {}", receipt.entry_index, receipt.entry_hash);

// 3. Sign and verify
let message = b"Hello, Web4!";
let signature = keypair.sign(message);
assert!(lct.verify_signature(message, &signature).is_ok());

// 4. Generate proof of existence
let proof = ledger.anchor(lct.id).unwrap();
assert!(ledger.verify_proof(&proof).unwrap());

// 5. Build a trust tensor by observation
let mut trust = T3::new();
trust.observe(TrustDimension::Talent, 0.9).unwrap();
trust.observe(TrustDimension::Training, 0.85).unwrap();
let score = trust.aggregate();

// 6. Identity coherence
let coherence = Coherence::with_values(0.92, 0.92, 0.92, 0.92).unwrap();
assert!(coherence.meets_threshold(lct.coherence_threshold()));
```

For persistence, swap `InMemoryLedger` for `LocalLedger`:

```rust
use web4_core::{Lct, EntityType, LocalLedger, Ledger};

let mut ledger = LocalLedger::open("./team-ledger.jsonl").unwrap();
let (lct, _kp) = Lct::new(EntityType::AiSoftware, None);
let receipt = lct.mint(&mut ledger).unwrap();

// Reopen later — state is replayed from the file with chain-integrity checks
let ledger = LocalLedger::open("./team-ledger.jsonl").unwrap();
assert_eq!(ledger.lookup(lct.id).unwrap().map(|l| l.id), Some(lct.id));
```

## Ledger backends

| Backend | Use case | Persistence | Distribution |
|---|---|---|---|
| `InMemoryLedger` | Tests, prototyping, ephemeral runs | None | Single process |
| `LocalLedger` | Solo dev, team-scoped accountability, regulated/air-gapped | File (JSON-lines, hash-chained) | Single host |
| `ActLedger` *(separate crate, future)* | Federation-wide consensus | ACT Cosmos chain | Distributed |

All backends implement the [`Ledger`] trait — the canonical surface is stable across them. Swap backends without changing your minting code.

## Web4 ontology context

```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

`web4-core` implements the **LCT + T3/V3 + Coherence** primitives. The remaining Web4 components (MCP integration, MRH context scoping, ATP/ADP energy economics, RDF ontology) live in [`web4-standard/`](https://github.com/dp-web4/web4/tree/main/web4-standard) and the broader Web4 SDK.

## Python bindings

Available via [maturin](https://github.com/PyO3/maturin) at [`web4-core/python/`](python/). Install:

```bash
pip install web4-core
```

Or build from source:

```bash
pip install maturin
cd python
maturin develop
```

Python API mirrors the Rust API — see [`python/README.md`](python/README.md).

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the rationale on why Web4 is implemented in Rust with Python bindings, and how this crate fits into the larger ecosystem.

## Status

Working ontology with growing proof points. Demonstrated 0% → 94.85% on ARC-AGI-3 (same Claude Opus 4.6, structured around Web4 patterns via the SAGE harness). Public scorecard: <https://arcprize.org/scorecards/c7dfb4f1-8642-4c9e-ab4d-152f5f8e33b4>.

R&D — not production. See parent repo [STATUS.md](https://github.com/dp-web4/web4/blob/main/STATUS.md) for honest assessment.

## Patent notice

This software implements technology covered by US Patents 11,477,027 and 12,278,913, and pending application 19/178,619 (assigned to MetaLINXX Inc.). A royalty-free patent license is granted under AGPL-3.0 terms for non-commercial / research / open-source use. For commercial licensing, contact dp@metalinxx.io. See [PATENTS.md](PATENTS.md) for full terms.

## License

AGPL-3.0-or-later. See [LICENSE](LICENSE).
