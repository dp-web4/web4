"""
Web4 Trust - Core trust primitives for the Web4 ecosystem.

This module provides high-performance Rust-backed implementations of:

- T3Tensor: Trust tensor with 3 root dimensions (Talent / Training /
  Temperament). Each root is itself an open-ended RDF sub-graph of
  context-specific sub-dimensions via web4:subDimensionOf — fractally
  extensible, not a fixed-size 3-vector.
- V3Tensor: Value tensor with 3 root dimensions (Valuation / Veracity /
  Validity). Same fractal RDF pattern as T3.
- EntityTrust: Combines T3 + V3 with witnessing relationships and decay.
- TrustStore: Persistent storage for entity trust data.

Example:
    >>> from web4_trust import TrustStore, EntityTrust
    >>> store = TrustStore()  # Uses ~/.web4/governance/entities
    >>> trust = store.get("mcp:filesystem")
    >>> print(f"T3 average: {trust.t3_average():.3f}")
    >>> print(f"Trust level: {trust.trust_level()}")
    >>> store.witness("session:abc", "mcp:filesystem", success=True, magnitude=0.1)

For the full API and the Ledger trait that anchors LCTs (in the sister
crate web4-core), see https://github.com/dp-web4/web4.
"""

# Import from the Rust extension
from .web4_trust import (
    T3Tensor,
    V3Tensor,
    EntityTrust,
    TrustStore,
    create_memory_store,
    __version__,
)

__all__ = [
    "T3Tensor",
    "V3Tensor",
    "EntityTrust",
    "TrustStore",
    "create_memory_store",
    "__version__",
]
