# web4-trust-core

Core trust primitives for the Web4 ecosystem, implemented in Rust with Python bindings.

## Features

- **T3 Trust Tensor** — 3 root dimensions (Talent / Training / Temperament), each itself an open-ended RDF sub-graph of context-specific sub-dimensions via `web4:subDimensionOf`. Fractally extensible.
- **V3 Value Tensor** — 3 root dimensions (Valuation / Veracity / Validity), same fractal RDF pattern.
- **EntityTrust** — Combines T3 + V3 with witnessing relationships, role-binding, and decay.
- **TrustStore** — Persistent storage with JSON format compatibility. Includes `from_legacy_6d` migration helper for prior 6-flat-dimension data.

## T3 Root Dimensions

- **Talent** — Natural aptitude and capability for a specific role
- **Training** — Acquired expertise, certifications, and experience
- **Temperament** — Behavioral consistency, reliability, ethical disposition

## V3 Root Dimensions

- **Valuation** — Worth ascribed to the contribution
- **Veracity** — Truthfulness and reliability of the claim
- **Validity** — Soundness and applicability in context

Each root dimension is fractally extensible via `web4:subDimensionOf` — sub-dimensions form an RDF sub-graph that aggregates back into the root scalar. T3 and V3 are not fixed-size 6-vectors; they are typed multidimensional ontologies with 3 anchor roots.

Formal ontology: [`web4-standard/ontology/t3v3-ontology.ttl`](../web4-standard/ontology/t3v3-ontology.ttl)

## Installation

```bash
pip install web4-trust
```

Or build from source:

```bash
pip install maturin
maturin develop
```

## Usage

```python
from web4_trust import TrustStore, EntityTrust

# Open the default store (~/.web4/governance/entities)
store = TrustStore()

# Get or create entity trust
trust = store.get("mcp:filesystem")
print(f"T3 average: {trust.t3_average():.3f}")
print(f"Trust level: {trust.trust_level()}")

# Update from action outcome
store.update("mcp:filesystem", success=True, magnitude=0.1)

# Witness event: session observes MCP server
witness_trust, target_trust = store.witness(
    "session:abc",
    "mcp:filesystem",
    success=True,
    magnitude=0.1
)
print(f"MCP trust after witnessing: {target_trust.t3_average():.3f}")
```

## Architecture

```
┌─────────────────────────────────────────┐
│  web4-trust-core (Rust)                 │
│  - T3/V3 tensor math (3 roots, fractal) │
│  - EntityTrust with witnessing          │
│  - Decay calculations                   │
│  - Storage backends                     │
│  - from_legacy_6d migration helper      │
└─────────────────────────────────────────┘
              │
    ┌─────────┴─────────┐
    │  PyO3 Bindings    │
    └─────────┬─────────┘
              │
    ┌─────────┴─────────┐
    │  Python Package   │
    │  (web4_trust)     │
    └───────────────────┘
```

## Patent Notice

This software implements technology covered by US Patents 11,477,027 and 12,278,913, and pending application 19/178,619. See the repo-root [PATENTS.md](../PATENTS.md) for the patent grant terms.

## License

AGPL-3.0-or-later. See repo-root [LICENSE](../LICENSE).

## Successor research track

A derivation-as-law successor for this crate's update/decay arithmetic is being
developed at [`dp-web4/web4-trust-core`](https://github.com/dp-web4/web4-trust-core)
(a *repo*, distinct from this crate; nothing there is published to crates.io).
When its merge gate passes — a DerivationSpec reproducing this crate's normative
t3v3 vectors — that work ships as a new release **of this crate, under this name**.
Until then, this crate is the enforced semantics.
