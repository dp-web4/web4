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


def set_default_signer(signer: BlockSigner) -> None:
    """Set the default block signer for the game engine.

    This allows replacing the stub signer with a real cryptographic
    signer (e.g., SAGE-backed Ed25519) at runtime.

    Args:
        signer: A BlockSigner implementation (must have sign_block_header method)

    Example:
        from sage.federation import create_sage_block_signer_from_identity
        sage_signer = create_sage_block_signer_from_identity("Thor", "thor_sage_lct")
        set_default_signer(sage_signer)
    """
    global _default_signer
    _default_signer = signer


def create_sage_block_signer(platform_name: str, lct_id: str, key_path: str = None) -> BlockSigner:
    """Create a SAGE-backed Ed25519 block signer (optional integration).

    This function attempts to import and use SAGE federation cryptography.
    If SAGE is not available, it falls back to StubBlockSigner with a warning.

    Args:
        platform_name: Platform name (e.g., "Thor", "Sprout")
        lct_id: LCT identifier (e.g., "thor_sage_lct")
        key_path: Optional path to Ed25519 key file

    Returns:
        BlockSigner instance (SAGE-backed if available, stub otherwise)

    Example:
        signer = create_sage_block_signer("Thor", "thor_sage_lct")
        set_default_signer(signer)
    """
    try:
        # Attempt to import SAGE federation
        import sys
        from pathlib import Path

        # Add HRM to path if not already there
        # Look for HRM in ../HRM (sibling to web4) or ../../HRM
        current_file = Path(__file__).resolve()

        # Try sibling directory (ai-workspace/HRM)
        hrm_path = current_file.parent.parent.parent.parent / "HRM"
        if not hrm_path.exists():
            # Try parent of web4 (for different layouts)
            hrm_path = current_file.parent.parent.parent / "HRM"

        if hrm_path.exists() and str(hrm_path) not in sys.path:
            sys.path.insert(0, str(hrm_path))

        from sage.federation import create_sage_block_signer_from_identity

        # Create SAGE-backed signer
        signer = create_sage_block_signer_from_identity(platform_name, lct_id, key_path)
        print(f"✓ SAGE Ed25519 block signer created for platform: {platform_name}")
        return signer

    except ImportError as e:
        print(f"⚠ SAGE not available ({e}), using stub signer")
        return StubBlockSigner(label=f"stub-{platform_name}")
    except Exception as e:
        print(f"⚠ Error creating SAGE signer ({e}), using stub signer")
        return StubBlockSigner(label=f"stub-{platform_name}")
