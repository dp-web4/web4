from __future__ import annotations

"""Block signing abstraction for the Web4 game engine (v0).

This module defines a minimal interface for signing block headers so that
per-society microchains can be signed by either a stub signer or a real
hardware / federation-backed signer.

Current implementation uses a deterministic, software-only signature to
keep behavior stable. Future work can plug in Ed25519 via HRM/SAGE or
hardware-bound keys.
"""

from dataclasses import dataclass
from typing import Protocol, Dict, Any
import hashlib
import json


class BlockSigner(Protocol):
    """Protocol for signing block headers.

    Implementations should accept a block header dict and return a
    bytes-like signature. Verification is handled elsewhere.
    """

    def sign_block_header(self, header: Dict[str, Any]) -> bytes:  # pragma: no cover - interface only
        ...


@dataclass
class StubBlockSigner:
    """Deterministic, software-only block signer (v0).

    This signer does NOT provide real cryptographic guarantees. It
    exists to:
    - Make block signing explicit and testable.
    - Provide a seam where real Ed25519 / hardware signers can be
      swapped in without changing the engine.
    """

    label: str = "stub"

    def sign_block_header(self, header: Dict[str, Any]) -> bytes:
        header_json = json.dumps(header, sort_keys=True, separators=(",", ":"))
        # Use a labeled SHA-256 digest as a stand-in "signature".
        h = hashlib.sha256()
        h.update(self.label.encode("utf-8"))
        h.update(b"|")
        h.update(header_json.encode("utf-8"))
        return h.hexdigest().encode("utf-8")


# Global, process-local signer instance for the game engine.
# Future work can replace this with a configurable signer that uses
# hardware or HRM/SAGE federation keys.
_default_signer: BlockSigner = StubBlockSigner()


def get_block_signer() -> BlockSigner:
    """Return the default block signer for the engine (v0).

    Currently returns a StubBlockSigner. In integrated environments,
    this can be overridden to return a SAGE-backed or hardware-backed
    signer that satisfies the BlockSigner protocol.
    """

    return _default_signer
