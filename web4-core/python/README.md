# Web4-Core Python Bindings

Python bindings for the Web4 trust-native infrastructure core library, implemented in Rust via PyO3.

## Installation

### From source (requires Rust and maturin)

```bash
pip install maturin
cd web4-core/python
maturin develop
```

### Building a wheel

```bash
maturin build --release
pip install target/wheels/*.whl
```

## Usage

```python
import web4_core

# 1. Create an LCT (in-memory primitive)
lct, keypair = web4_core.PyLct.new(web4_core.PyEntityType.Human, None)

# 2. Anchor to a ledger — LCTs are blockchain tokens, must be minted
ledger = web4_core.PyInMemoryLedger()
receipt = ledger.mint(lct)
print(f"Minted at index {receipt.entry_index}, hash {receipt.entry_hash[:16]}...")

# 3. Sign and verify
message = b"Hello, Web4!"
signature = keypair.sign(message)
assert lct.verify_signature(message, signature)

# 4. Generate proof of existence
proof = ledger.anchor(lct.id)
assert ledger.verify_proof(proof)

# 5. Trust tensor — 3 root dimensions, fractally extensible
trust = web4_core.PyT3()
trust.observe(web4_core.PyTrustDimension.Talent, 0.9)
trust.observe(web4_core.PyTrustDimension.Training, 0.85)
trust.observe(web4_core.PyTrustDimension.Temperament, 0.88)
print(f"Aggregate trust: {trust.aggregate():.3f}")

# Fractal sub-dimension observation
trust.observe_sub_dimension("rust_proficiency", web4_core.PyTrustDimension.Training, 0.92)

# 6. Value tensor — same pattern
value = web4_core.PyV3()
value.observe(web4_core.PyValueDimension.Valuation, 0.9)
value.observe(web4_core.PyValueDimension.Veracity, 0.85)
value.observe(web4_core.PyValueDimension.Validity, 0.88)

# 7. Identity coherence (C × S × Φ × R)
coherence = web4_core.PyCoherence.with_values(0.8, 0.8, 0.7, 0.9)
print(f"Total coherence: {coherence.total():.3f}")
print(f"Limiting factor: {coherence.limiting_factor()}")
```

For persistence, swap `PyInMemoryLedger` for `PyLocalLedger`:

```python
ledger = web4_core.PyLocalLedger.open("./team-ledger.jsonl")
lct, _ = web4_core.PyLct.new(web4_core.PyEntityType.AiSoftware, None)
receipt = ledger.mint(lct)

# Reopen later — state is replayed from the file with chain-integrity checks
ledger = web4_core.PyLocalLedger.open("./team-ledger.jsonl")
restored = ledger.lookup(lct.id)
assert restored is not None
```

### Worked example: durable host identity

The snippet above shows the primitives. The repo ships a small,
self-contained script that turns them into a one-command setup for a
host's persistent presence — keypair on disk (`chmod 600`), local
hash-chained ledger, public LCT sidecar, and an idempotent re-run that
verifies the chain instead of regenerating:

```bash
# Generate identity (or verify, if it already exists)
python examples/identity_bootstrap.py --name laptop-01

# Read-only attestation check
python examples/identity_bootstrap.py --name laptop-01 --verify
```

Source: [`python/examples/identity_bootstrap.py`](examples/identity_bootstrap.py).
Copy and adapt — change the entity type, point at a different base
directory, layer hardware-binding (TPM / secure enclave) on top, etc.

### Ledger backends

| Backend | Use case |
|---|---|
| `PyInMemoryLedger` | Tests, prototyping, ephemeral runs |
| `PyLocalLedger` | Solo dev, team-scoped accountability, regulated/air-gapped environments — persistent, hash-chained, tamper-evident |
| ACT chain backend *(separate package, future)* | Federation-wide consensus via Cosmos SDK gateway |

## API Reference

### Entity Types

- `PyEntityType.Human` — Human user
- `PyEntityType.AiSoftware` — Software-bound AI agent
- `PyEntityType.AiEmbodied` — Hardware-bound AI agent
- `PyEntityType.Organization` — Organization
- `PyEntityType.Role` — Role (first-class entity)
- `PyEntityType.Task` — Task
- `PyEntityType.Resource` — Resource
- `PyEntityType.Hybrid` — Hybrid entity

### Trust Tensor (T3) — 3 Root Dimensions

T3 is fractally multidimensional. The three root dimensions below are each themselves open-ended RDF sub-graphs of context-specific sub-dimensions, linked via `web4:subDimensionOf`.

- `PyTrustDimension.Talent` — Natural aptitude and capability for a specific role
- `PyTrustDimension.Training` — Acquired expertise, certifications, and experience
- `PyTrustDimension.Temperament` — Behavioral consistency, reliability, ethical disposition

Use `observe(dimension, score)` to record a root-level observation, or `observe_sub_dimension(name, parent, score)` to record a sub-dimension under one of the roots.

### Value Tensor (V3) — 3 Root Dimensions

Same fractal structure as T3.

- `PyValueDimension.Valuation` — Worth ascribed to the contribution
- `PyValueDimension.Veracity` — Truthfulness and reliability of the claim
- `PyValueDimension.Validity` — Soundness and applicability in context

### Identity Coherence (C × S × Φ × R)

- `C` (Continuity) — Temporal consistency
- `S` (Stability) — Resistance to perturbation
- `Φ` (Phi) — Information integration
- `R` (Reachability) — Network connection

Coherence is multiplicative: a low score in any factor limits the whole. Use `limiting_factor()` to identify the bottleneck.

### Crypto

- `PyKeyPair.generate()` — Generate a fresh Ed25519 keypair
- `PyKeyPair.from_secret_bytes(bytes)` — Reconstruct from 32-byte secret
- `keypair.sign(message)` — Sign bytes (returns 64-byte signature)
- `lct.verify_signature(message, signature)` — Verify against the LCT's public key
- `web4_core.sha256(data)` / `sha256_hex(data)` — SHA-256 helpers

## Patent Notice

This software implements technology covered by US Patents 11,477,027 and 12,278,913, and pending application 19/178,619. See [PATENTS.md](../../PATENTS.md) for the patent grant terms.

## License

AGPL-3.0-or-later. See [LICENSE](../LICENSE).
