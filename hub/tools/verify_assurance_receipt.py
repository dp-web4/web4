#!/usr/bin/env python3
"""Standalone reference verifier for a hub AssuranceReceipt (PRD_ASSURANCE A2).

The POINT of the receipt is that a relying party verifies it WITHOUT running the
hub or hestia — in any language. This is that verifier, in Python, depending only
on `cryptography` (Ed25519). It reproduces `signing_bytes` v3 from
`hub-lib/src/constellation.rs` and checks: freshness, signer-key attribution, and
the hub's signature.

Usage:
    verify_assurance_receipt.py <receipt.json> <hub_signer_pubkey_hex>
    verify_assurance_receipt.py --self-test      # verify the committed golden fixture

The pubkey is the hub's SIGNING key (resolve it from the receipt's
`hub_signer_lct_id` via the registry, or pin it out of band). Exit 0 = valid.

THE TIMESTAMPS ARE USED VERBATIM — and that is the v3 guarantee
---------------------------------------------------------------
This verifier feeds the transmitted timestamp strings straight into
`signing_bytes` with no reformatting, because under `signing_bytes` **v3** the hub
signs the exact string it sends: RFC3339, always nine fractional digits, always
`Z` (`hub-lib`'s `canonical_timestamp()` produces both the wire form and the
signed form, and its
`signed_bytes_are_reconstructable_from_the_wire_alone` test rebuilds the canonical
bytes from parsed JSON the way this file does).

Under the previous **v2** layout that was not true (measured 2026-07-30, chrono
pinned `=0.4.45`): the hub signed `DateTime::to_rfc3339()` while serialising
chrono's serde default, so the two differed by the offset suffix alone —

    signed (v2)   2026-07-30T04:03:13.302191724+00:00
    wire  (v2)    2026-07-30T04:03:13.302191724Z

— and this verifier carried a `Z` → `+00:00` shim to bridge it. **The shim is
gone deliberately.** Keeping it after v3 would mean a future re-divergence
verifies with a warning instead of failing, i.e. the regression detector would
have become the thing hiding the regression. A v3 receipt whose bytes cannot be
rebuilt from its own wire strings is now simply invalid.

v2 receipts do not verify here, and none exists to be broken by that: the receipt
primitive landed 2026-07-29 while the live daemon has been running since
2026-07-27, and the running image contains no `assurance-receipt` domain string
at all. The domain tag makes the refusal explicit rather than silent.
"""
import sys, json, hashlib, pathlib
from datetime import datetime, timezone

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
except ImportError:
    sys.exit("needs `cryptography` (pip install cryptography)")

DOMAIN = b"web4:assurance-receipt:v3:"
TS_FIELDS = ("issued_at", "bound_at", "valid_until")
FIXTURE = pathlib.Path(__file__).with_name("testdata") / "assurance_receipt_v3_golden.json"


def uuid_bytes(s: str) -> bytes:
    import uuid
    return uuid.UUID(s).bytes  # big-endian, matches Rust Uuid::as_bytes()


def parse_ts(s: str) -> datetime:
    """For the freshness COMPARISON only — never for the signed bytes.

    `fromisoformat` accepts only 3- or 6-digit fractions before Python 3.12, and
    the canonical form always carries 9. Truncate to microseconds rather than
    crash with an uncaught ValueError on 3.11. Parsing is lossy here by design;
    the signature never sees a parsed value."""
    if "." in s:
        head, _, rest = s.partition(".")
        digits = rest[: len(rest) - len(rest.lstrip("0123456789"))]
        s = f"{head}.{digits[:6]}{rest[len(digits):]}"
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def signing_bytes(r: dict) -> bytes:
    """Field order + encoding MUST match hub-lib `signing_bytes()` exactly.
    Every string is taken from the wire verbatim — see the module docstring."""
    b = bytearray(DOMAIN)
    b += uuid_bytes(r["owner_lct_id"])
    b += r["tier"].encode()                       # wire_tag: single_device/... (serde snake_case)
    b += uuid_bytes(r["pair_id"])
    b += r["challenge_nonce"].encode()
    for f in TS_FIELDS:
        b += r[f].encode()
    b += uuid_bytes(r["hub_lct_id"])
    b += uuid_bytes(r["hub_signer_lct_id"])
    b += r["hub_signer_key_id"].encode()
    b += r["roster_hash"].encode()
    return bytes(b)


def key_id(pubkey_bytes: bytes) -> str:
    return hashlib.sha256(pubkey_bytes).digest()[:8].hex()


def verify(receipt: dict, pub_bytes: bytes, now: datetime) -> None:
    """Raises SystemExit on any failure (freshness, attribution, signature)."""
    # 1. freshness
    if now > parse_ts(receipt["valid_until"]):
        sys.exit("FAIL: receipt is expired (valid_until in the past)")
    # 2. signer-key attribution — the key must be the one the receipt claims
    if key_id(pub_bytes) != receipt["hub_signer_key_id"]:
        sys.exit(f"FAIL: key_id mismatch — this pubkey ({key_id(pub_bytes)}) is not "
                 f"the receipt's signer ({receipt['hub_signer_key_id']})")
    # 3. the hub's signature over the canonical bytes, rebuilt from the wire.
    try:
        Ed25519PublicKey.from_public_bytes(pub_bytes).verify(
            bytes.fromhex(receipt["signature"]), signing_bytes(receipt)
        )
    except InvalidSignature:
        sys.exit("FAIL: hub signature does not verify over the bytes rebuilt from this "
                 "receipt's own wire strings — the receipt is tampered with, was signed "
                 "by a different key than it claims, or predates signing_bytes v3")


def report(receipt: dict) -> None:
    print(f"VALID: tier={receipt['tier']} owner={receipt['owner_lct_id']} "
          f"valid_until={receipt['valid_until']} — verified WITHOUT the hub or hestia")


def self_test() -> int:
    """Verify the committed golden fixture — a real receipt signed by hub-lib's own
    `signing_bytes()` (deterministic key + timestamps; regenerate with the
    `gen_receipt_fixture` example named in the fixture README). This is what
    catches a silent v3 → v4 drift in this file."""
    receipt = json.loads(FIXTURE.read_text())
    pub_bytes = bytes.fromhex(FIXTURE.with_suffix(".pubkey").read_text().strip())
    now = datetime.now(timezone.utc)

    verify(receipt, pub_bytes, now)
    print("self-test: golden fixture VERIFIES against its verbatim wire timestamps")

    # The canonical form, asserted on the committed bytes: 9 fractional digits and a
    # `Z` on EVERY timestamp, including the whole-second one. A fixed-width fraction
    # is the half of v3 that a signature check alone would not notice — v2 varied it
    # with the value, so `valid_until` and `issued_at` had different shapes.
    for f in TS_FIELDS:
        v = receipt[f]
        if not v.endswith("Z") or "+" in v:
            print(f"self-test FAILED: {f}={v} is not Z-suffixed")
            return 1
        if len(v.partition(".")[2].rstrip("Z")) != 9:
            print(f"self-test FAILED: {f}={v} does not carry 9 fractional digits")
            return 1
    print("self-test: all timestamps are Z-suffixed, fixed-width 9 — canonical form holds")

    # A tampered receipt must fail. There is no fallback form left to rescue it.
    try:
        verify(dict(receipt, tier="single_device"), pub_bytes, now)
    except SystemExit as e:
        assert "tampered" in str(e), f"unexpected failure text: {e}"
        print("self-test: tampered tier correctly rejected")
    else:
        print("self-test FAILED: a tampered receipt verified")
        return 1

    # A v2-era receipt must be refused, not silently accepted by a lingering shim.
    v2 = dict(receipt, **{f: receipt[f].replace("Z", "+00:00") for f in TS_FIELDS})
    try:
        verify(v2, pub_bytes, now)
    except SystemExit as e:
        assert "tampered" in str(e), f"unexpected failure text: {e}"
        print("self-test: v2 offset-suffix timestamps correctly rejected (shim is gone)")
    else:
        print("self-test FAILED: the v2 timestamp form still verifies — a shim survives")
        return 1

    # And the freshness parse must survive 9 fractional digits (the fixture has them).
    parse_ts(receipt["issued_at"])
    print("self-test: OK")
    return 0


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        sys.exit(self_test())
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    receipt = json.load(open(sys.argv[1]))
    pub_bytes = bytes.fromhex(sys.argv[2].strip())
    verify(receipt, pub_bytes, datetime.now(timezone.utc))
    report(receipt)


if __name__ == "__main__":
    main()
