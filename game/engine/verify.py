from __future__ import annotations

"""Chain verification helpers for the Web4 game engine (v0).

These helpers allow external verifiers (or test code) to check
structural integrity of a society's microchain:
- Hash-chain correctness (previous_hash / header_hash).
- Presence of stub signatures (TPM-ready, not yet validated).

Future work can plug in real signature verification against
HardwareIdentity / TPM-backed keys.
"""

from typing import Dict, Any
import hashlib
import json

from .models import Society


def _compute_header_hash(header: Dict[str, Any]) -> str:
    header_json = json.dumps(header, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(header_json.encode("utf-8")).hexdigest()


def verify_chain_structure(society: Society) -> Dict[str, Any]:
    """Verify basic hash-chain structure of a society's blocks.

    Returns a dict with:
    - valid: bool
    - errors: list of error strings
    - block_count: int
    """

    errors: list[str] = []
    prev_header_hash: str | None = None

    for block in society.blocks:
        index = block.get("index")
        society_lct = block.get("society_lct")
        previous_hash = block.get("previous_hash")
        header_hash = block.get("header_hash")

        header = {
            "index": index,
            "society_lct": society_lct,
            "previous_hash": previous_hash,
            "timestamp": block.get("timestamp"),
        }
        computed = _compute_header_hash(header)
        if header_hash != computed:
            errors.append(f"block {index}: header_hash mismatch")

        if prev_header_hash is not None and previous_hash != prev_header_hash:
            errors.append(f"block {index}: previous_hash mismatch")

        prev_header_hash = header_hash

    return {
        "valid": not errors,
        "errors": errors,
        "block_count": len(society.blocks),
    }


def verify_hardware_binding(society: Society) -> Dict[str, Any]:
    """Verify minimal hardware binding invariants for a society (v0).

    Checks (best-effort, research-stage only):
    - The society has a hardware_fingerprint set.
    - The first block exists and contains a genesis event.
    - The genesis event's hardware_fingerprint matches the society's.
    """

    errors: list[str] = []

    if not society.hardware_fingerprint:
        errors.append("society missing hardware_fingerprint metadata")
        return {"valid": False, "errors": errors}

    if not society.blocks:
        errors.append("society has no blocks (missing genesis)")
        return {"valid": False, "errors": errors}

    genesis = society.blocks[0]
    events = genesis.get("events", [])
    if not events:
        errors.append("genesis block has no events")
        return {"valid": False, "errors": errors}

    genesis_ev = events[0]
    if genesis_ev.get("type") != "genesis":
        errors.append("first event is not a genesis event")
    if genesis_ev.get("hardware_fingerprint") != society.hardware_fingerprint:
        errors.append("hardware_fingerprint mismatch between society and genesis event")

    return {
        "valid": not errors,
        "errors": errors,
    }


def verify_stub_signatures(society: Society) -> Dict[str, Any]:
    """Placeholder signature verification.

    In v0 we only check that a signature field is present; later this
    will be replaced with real public-key verification.
    """

    errors: list[str] = []
    for block in society.blocks:
        index = block.get("index")
        sig = block.get("signature")
        if not sig:
            errors.append(f"block {index}: missing signature")

    return {
        "valid": not errors,
        "errors": errors,
        "block_count": len(society.blocks),
    }
