"""
Web4 Trust - Core trust primitives for the Web4 ecosystem.

This module provides high-performance Rust-backed implementations of:
- T3Tensor: 6-dimensional trust tensor
- V3Tensor: 6-dimensional value tensor
- EntityTrust: Entity trust with witnessing relationships
- TrustStore: Persistent storage for trust data

Example:
    >>> from web4_trust import TrustStore, EntityTrust
    >>> store = TrustStore()  # Uses ~/.web4/governance/entities
    >>> trust = store.get("mcp:filesystem")
    >>> print(f"T3: {trust.t3_average():.3f}, Level: {trust.trust_level()}")
    >>> store.witness("session:abc", "mcp:filesystem", success=True, magnitude=0.1)
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
