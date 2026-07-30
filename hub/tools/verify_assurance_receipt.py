#!/usr/bin/env python3
"""Standalone reference verifier for a hub AssuranceReceipt (PRD_ASSURANCE A2).

The POINT of the receipt is that a relying party verifies it WITHOUT running the
hub or hestia — in any language. This is that verifier, in ~40 lines of Python,
depending only on `cryptography` (Ed25519). It reproduces `signing_bytes` v2 from
`hub-lib/src/constellation.rs` and checks: freshness, signer-key attribution, and
the hub's signature.

Usage:
    verify_assurance_receipt.py <receipt.json> <hub_signer_pubkey_hex>

The pubkey is the hub's SIGNING key (resolve it from the receipt's
`hub_signer_lct_id` via the registry, or pin it out of band). Exit 0 = valid.

NOTE (portability finding, 2026-07-29): the Rust hub signs over
`DateTime::to_rfc3339()`, which emits NANOSECOND precision and a `+00:00` suffix.
Most languages (incl. Python) format at microsecond precision and/or `Z`, so a
non-Rust verifier CANNOT reproduce the signed bytes from a parsed datetime — it
must use the timestamp string EXACTLY as transmitted in the JSON. This script
therefore signs over the raw JSON string fields verbatim (never a re-parsed
datetime). If the JSON string and the hub's `to_rfc3339()` output differ, the
receipt is not portable and the hub should sign a precision-stable form (unix
millis, or a fixed-precision RFC3339). See the companion forum note.
"""
import sys, json, hashlib
from datetime import datetime, timezone

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
except ImportError:
    sys.exit("needs `cryptography` (pip install cryptography)")

DOMAIN = b"web4:assurance-receipt:v2:"

def uuid_bytes(s: str) -> bytes:
    import uuid
    return uuid.UUID(s).bytes  # big-endian, matches Rust Uuid::as_bytes()

def signing_bytes(r: dict) -> bytes:
    # Field order + encoding MUST match hub-lib signing_bytes() exactly. Timestamps
    # are taken as the raw JSON strings (see the portability note above).
    b = bytearray(DOMAIN)
    b += uuid_bytes(r["owner_lct_id"])
    b += r["tier"].encode()                       # wire_tag: single_device/... (serde snake_case)
    b += uuid_bytes(r["pair_id"])
    b += r["challenge_nonce"].encode()
    b += r["issued_at"].encode()
    b += r["bound_at"].encode()
    b += r["valid_until"].encode()
    b += uuid_bytes(r["hub_lct_id"])
    b += uuid_bytes(r["hub_signer_lct_id"])
    b += r["hub_signer_key_id"].encode()
    b += r["roster_hash"].encode()
    return bytes(b)

def key_id(pubkey_bytes: bytes) -> str:
    return hashlib.sha256(pubkey_bytes).digest()[:8].hex()

def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    receipt = json.load(open(sys.argv[1]))
    pub_hex = sys.argv[2].strip()
    pub_bytes = bytes.fromhex(pub_hex)

    # 1. freshness
    va = receipt["valid_until"].replace("Z", "+00:00")
    if datetime.now(timezone.utc) > datetime.fromisoformat(va):
        sys.exit("FAIL: receipt is expired (valid_until in the past)")
    # 2. signer-key attribution — the key must be the one the receipt claims
    if key_id(pub_bytes) != receipt["hub_signer_key_id"]:
        sys.exit(f"FAIL: key_id mismatch — this pubkey ({key_id(pub_bytes)}) is not "
                 f"the receipt's signer ({receipt['hub_signer_key_id']})")
    # 3. the hub's signature over the canonical bytes
    try:
        Ed25519PublicKey.from_public_bytes(pub_bytes).verify(
            bytes.fromhex(receipt["signature"]), signing_bytes(receipt))
    except InvalidSignature:
        sys.exit("FAIL: hub signature does not verify (tampered receipt, or the "
                 "timestamp string differs from what the hub signed — see the note)")
    print(f"VALID: tier={receipt['tier']} owner={receipt['owner_lct_id']} "
          f"valid_until={receipt['valid_until']} — verified WITHOUT the hub or hestia")

if __name__ == "__main__":
    main()
