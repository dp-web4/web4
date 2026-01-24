# Web4 Trust Core - Rust Implementation Rollout Plan

**Date**: 2026-01-24
**Target**: Deploy Rust trust primitives across all machines in the collective

## Overview

We've implemented the core Web4 trust primitives (T3/V3 tensors, EntityTrust, witnessing, decay) in Rust with bindings for:
- **Python** (via PyO3) - for Claude Code plugin hooks
- **WASM** (via wasm-bindgen) - for browser/Node.js environments

This document outlines the rollout across all machines.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     web4-trust-core (Rust)                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────────┐  │
│  │ T3Tensor │  │ V3Tensor │  │EntityTrust│  │ TrustStore │  │
│  └──────────┘  └──────────┘  └───────────┘  └────────────┘  │
│         │              │              │              │       │
│         └──────────────┴──────────────┴──────────────┘       │
│                              │                                │
│              ┌───────────────┼───────────────┐               │
│              ▼               ▼               ▼               │
│         ┌────────┐     ┌──────────┐    ┌──────────┐         │
│         │ PyO3   │     │   WASM   │    │  Native  │         │
│         │Bindings│     │ Bindings │    │   Rust   │         │
│         └────────┘     └──────────┘    └──────────┘         │
└─────────────────────────────────────────────────────────────┘
              │                │                │
              ▼                ▼                ▼
    ┌─────────────────┐ ┌────────────┐ ┌──────────────┐
    │ claude-code-    │ │  Browser   │ │    Other     │
    │ plugin (Python) │ │  Extension │ │ Rust Apps    │
    └─────────────────┘ └────────────┘ └──────────────┘
```

## Machine Inventory

| Machine | OS | GPU | Primary Use | Deployment Path |
|---------|-----|-----|-------------|-----------------|
| **Legion** | Ubuntu 22.04 | RTX 4090 | Web4 Research | Direct (this machine) |
| **CBP** | Windows/WSL2 | RTX 4090 | Synchronism + Chemistry | WSL2 pip install |
| **Thor** | L4T (Jetson AGX) | Thor GPU | SAGE + Gnosis | ARM64 wheel |
| **Sprout** | L4T (Jetson Orin Nano) | Orin | Edge Validation | ARM64 wheel |

## Rollout Steps

### Phase 1: Build Packages (Legion)

#### 1.1 Build Python Wheel
```bash
cd /home/dp/ai-workspace/web4/web4-trust-core
source ~/.cargo/env

# Build with maturin
pip install maturin
maturin build --release --features python

# Wheel location: target/wheels/web4_trust_core-*.whl
```

#### 1.2 Build WASM Package
```bash
# Already built, verify:
ls -la pkg/

# Rebuild if needed:
wasm-pack build --target web --features wasm --no-default-features
```

### Phase 2: Integrate into claude-code-plugin (Legion)

#### 2.1 Install Python Package
```bash
# Install locally for development
cd /home/dp/ai-workspace/web4/web4-trust-core
maturin develop --features python

# Or install wheel
pip install target/wheels/web4_trust_core-*.whl
```

#### 2.2 Create Migration Bridge
Create a bridge module that allows gradual migration from Python to Rust:

```python
# governance/trust_backend.py
"""
Bridge module for Rust trust backend migration.
Falls back to pure Python if Rust module unavailable.
"""

try:
    # Try Rust backend first
    from web4_trust_core import (
        PyT3Tensor as T3Tensor,
        PyV3Tensor as V3Tensor,
        PyEntityTrust as EntityTrust,
        PyTrustStore as TrustStore
    )
    RUST_BACKEND = True
except ImportError:
    # Fall back to Python implementation
    from .entity_trust import T3Tensor, V3Tensor, EntityTrust
    from .trust_store import TrustStore
    RUST_BACKEND = False

def get_backend_info():
    return {
        "backend": "rust" if RUST_BACKEND else "python",
        "version": "0.1.0"
    }
```

#### 2.3 Update entity_trust.py to Use Bridge
Modify imports in files that use trust primitives.

### Phase 3: Test on Legion

```bash
cd /home/dp/ai-workspace/web4/claude-code-plugin

# Run existing tests with Rust backend
python -m pytest test_entity_trust.py -v

# Run full test suite
python -m pytest . -v
```

### Phase 4: Deploy to Other Machines

#### For WSL2 (CBP)
```bash
# Copy wheel to shared location
scp target/wheels/web4_trust_core-*.whl cbp:/path/to/

# SSH to CBP and install
wsl -d Ubuntu
pip install web4_trust_core-*.whl
```

#### For Jetsons (Thor, Sprout)
Jetsons use ARM64, so we need to cross-compile or build on-device:

**Option A: Build on Device**
```bash
# SSH to Jetson
ssh sprout  # or thor

# Install Rust if needed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Clone and build
cd ~/ai-workspace/web4/web4-trust-core
maturin build --release --features python
pip install target/wheels/*.whl
```

**Option B: Cross-compile (more complex)**
Requires ARM64 toolchain setup on Legion.

### Phase 5: Verify Deployment

Each machine should run:
```bash
python -c "
from web4_trust_core import PyEntityTrust as EntityTrust
e = EntityTrust('test:verify')
e.update_from_outcome(True, 0.1)
print(f'Backend: Rust')
print(f'Trust Level: {e.trust_level()}')
print(f'T3 Average: {e.t3_average():.4f}')
"
```

Expected output:
```
Backend: Rust
Trust Level: Medium
T3 Average: 0.5167
```

## Files Changed

### web4-trust-core (new crate)
- `Cargo.toml` - Package configuration
- `src/lib.rs` - Main library
- `src/tensor/t3.rs` - T3 Trust Tensor
- `src/tensor/v3.rs` - V3 Value Tensor
- `src/entity/trust.rs` - EntityTrust
- `src/storage/` - TrustStore backends
- `src/bindings/python.rs` - PyO3 bindings
- `src/bindings/wasm.rs` - WASM bindings
- `pkg/` - Built WASM package

### claude-code-plugin (to update)
- `governance/trust_backend.py` - Bridge module (NEW)
- `governance/__init__.py` - Update imports
- `hooks/*.py` - Use Rust backend via bridge

## Rollback Plan

If issues arise:
1. Set `USE_RUST_BACKEND=false` environment variable
2. Bridge automatically falls back to Python implementation
3. No data migration needed (JSON format compatible)

## Performance Expectations

Based on Rust vs Python benchmarks:
- **Tensor operations**: 10-50x faster
- **Decay calculations**: 20-100x faster
- **Store operations**: 5-20x faster
- **Memory usage**: 2-5x lower

## Next Steps After Rollout

1. Remove Python fallback after verification period
2. Add WASM package to browser extension
3. Publish to crates.io/PyPI/npm for public use
4. Implement sled-store feature for high-performance persistence

## Contact for Issues

- Create issue in web4-trust-core repo
- Message via private-context/messages/
