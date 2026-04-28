"""
Web4-Core: Foundational primitives for the Web4 trust-native ontology.

Provides Rust-backed implementations (via PyO3) of:

- PyLct: Linked Context Token (non-transferable presence with Ed25519 binding)
- PyT3: Trust Tensor — 3 root dimensions (Talent / Training / Temperament),
  each itself a fractal RDF sub-graph of context-specific sub-dimensions
  via web4:subDimensionOf
- PyV3: Value Tensor — 3 root dimensions (Valuation / Veracity / Validity),
  same fractal RDF pattern
- PyCoherence: Identity coherence (C × S × Φ × R)
- PyKeyPair: Ed25519 sign/verify
- PyInMemoryLedger / PyLocalLedger: Ledger backends for anchoring LCTs
- PyMintReceipt / PyLedgerProof: ledger receipts and proofs

Pure-Python additions:

- web4_core.trust.attestation: AttestationEnvelope + anchor verification
  (TPM2, FIDO2, Secure Enclave, software fallback)

Quick start:

    >>> import web4_core
    >>> lct, kp = web4_core.PyLct.new(web4_core.PyEntityType.Human, None)
    >>> ledger = web4_core.PyInMemoryLedger()
    >>> receipt = ledger.mint(lct)
    >>> proof = ledger.anchor(lct.id)
    >>> assert ledger.verify_proof(proof)

For the full API and ledger architecture, see:
https://github.com/dp-web4/web4/blob/main/web4-core/README.md
"""

from .web4_core import (
    # Enums
    PyEntityType,
    PyTrustDimension,
    PyValueDimension,
    # Core types
    PyKeyPair,
    PyLct,
    PyT3,
    PyV3,
    PyCoherence,
    # Ledger types
    PyInMemoryLedger,
    PyLocalLedger,
    PyMintReceipt,
    PyLedgerProof,
    # Functions
    sha256,
    sha256_hex,
    version,
)

__version__ = version()

__all__ = [
    "PyEntityType",
    "PyTrustDimension",
    "PyValueDimension",
    "PyKeyPair",
    "PyLct",
    "PyT3",
    "PyV3",
    "PyCoherence",
    "PyInMemoryLedger",
    "PyLocalLedger",
    "PyMintReceipt",
    "PyLedgerProof",
    "sha256",
    "sha256_hex",
    "version",
    "__version__",
]
