#!/usr/bin/env python3
"""Standalone reference verifier for a hub AssuranceReceipt (PRD_ASSURANCE A2).

The POINT of the receipt is that a relying party verifies it WITHOUT running the
hub or hestia — in any language. This is that verifier, in Python, depending only
on `cryptography` (Ed25519). It reproduces `signing_bytes` v2 from
`hub-lib/src/constellation.rs` and checks: freshness, signer-key attribution, and
the hub's signature.

Usage:
    verify_assurance_receipt.py <receipt.json> <hub_signer_pubkey_hex>
    verify_assurance_receipt.py --self-test      # verify the committed golden fixture

The pubkey is the hub's SIGNING key (resolve it from the receipt's
`hub_signer_lct_id` via the registry, or pin it out of band). Exit 0 = valid.

PORTABILITY FINDING (measured 2026-07-30, chrono pinned `=0.4.45`)
------------------------------------------------------------------
The bytes the hub signs are NOT byte-identical to the timestamps it transmits,
so a verifier cannot simply feed the wire strings into `signing_bytes`:

    signed (`DateTime::to_rfc3339()`)  2026-07-30T04:03:13.302191724+00:00
    wire   (plain serde)               2026-07-30T04:03:13.302191724Z

**The offset suffix is the entire difference — precision is not the problem.**
Both sides use chrono's `SecondsFormat::AutoSi`, so the fractional digits are
identical on the wire and in the signed bytes (0, 3 or 9, same value). Any "fix"
that only pins precision changes nothing.

This verifier therefore tries the VERBATIM wire strings first and, only if that
fails, retries with the reconstructed signed form (trailing `Z` → `+00:00`),
reporting loudly when the fallback is what carried the verification. Two
consequences worth keeping:

  * a genuine receipt verifies TODAY, and is never mislabelled as tampered;
  * the fallback is a regression detector — once the hub signs the transmitted
    string, the verbatim path starts succeeding and the shim goes quiet.

The hub still SHOULD sign a wire-identical, precision-stable form (sign the
transmitted string, or unix millis): today the canonical bytes are
unreconstructable from the wire without knowing a chrono-specific quirk. That
Rust-side change is a v2 → v3 tag bump. See the companion forum note.
"""
import sys, json, hashlib, pathlib
from datetime import datetime, timezone

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
except ImportError:
    sys.exit("needs `cryptography` (pip install cryptography)")

DOMAIN = b"web4:assurance-receipt:v2:"
TS_FIELDS = ("issued_at", "bound_at", "valid_until")
FIXTURE = pathlib.Path(__file__).with_name("testdata") / "assurance_receipt_v2_golden.json"


def uuid_bytes(s: str) -> bytes:
    import uuid
    return uuid.UUID(s).bytes  # big-endian, matches Rust Uuid::as_bytes()


def as_signed_form(s: str) -> str:
    """The `to_rfc3339()` spelling of a wire timestamp: `...Z` → `...+00:00`."""
    return s[:-1] + "+00:00" if s.endswith("Z") else s


def parse_ts(s: str) -> datetime:
    """`fromisoformat` accepts only 3- or 6-digit fractions before Python 3.12;
    chrono emits 9 whenever nanos are nonzero, which is the common case. Truncate
    to microseconds rather than crash with an uncaught ValueError on 3.11."""
    s = as_signed_form(s)
    if "." in s:
        head, _, rest = s.partition(".")
        digits = rest[: len(rest) - len(rest.lstrip("0123456789"))]
        s = f"{head}.{digits[:6]}{rest[len(digits):]}"
    return datetime.fromisoformat(s)


def signing_bytes(r: dict, timestamps: dict) -> bytes:
    # Field order + encoding MUST match hub-lib signing_bytes() exactly.
    # `timestamps` supplies the three time fields (verbatim wire, or the
    # reconstructed signed form) — see the portability finding above.
    b = bytearray(DOMAIN)
    b += uuid_bytes(r["owner_lct_id"])
    b += r["tier"].encode()                       # wire_tag: single_device/... (serde snake_case)
    b += uuid_bytes(r["pair_id"])
    b += r["challenge_nonce"].encode()
    b += timestamps["issued_at"].encode()
    b += timestamps["bound_at"].encode()
    b += timestamps["valid_until"].encode()
    b += uuid_bytes(r["hub_lct_id"])
    b += uuid_bytes(r["hub_signer_lct_id"])
    b += r["hub_signer_key_id"].encode()
    b += r["roster_hash"].encode()
    return bytes(b)


def key_id(pubkey_bytes: bytes) -> str:
    return hashlib.sha256(pubkey_bytes).digest()[:8].hex()


def verify(receipt: dict, pub_bytes: bytes, now: datetime) -> str:
    """Returns which timestamp form verified: "wire" or "reconstructed".
    Raises SystemExit on any failure (freshness, attribution, signature)."""
    # 1. freshness
    if now > parse_ts(receipt["valid_until"]):
        sys.exit("FAIL: receipt is expired (valid_until in the past)")
    # 2. signer-key attribution — the key must be the one the receipt claims
    if key_id(pub_bytes) != receipt["hub_signer_key_id"]:
        sys.exit(f"FAIL: key_id mismatch — this pubkey ({key_id(pub_bytes)}) is not "
                 f"the receipt's signer ({receipt['hub_signer_key_id']})")
    # 3. the hub's signature over the canonical bytes. Verbatim wire FIRST; the
    #    reconstructed signed form only as a fallback, so that the day the hub
    #    signs what it transmits, the shim silently stops being needed.
    pub = Ed25519PublicKey.from_public_bytes(pub_bytes)
    sig = bytes.fromhex(receipt["signature"])
    wire = {f: receipt[f] for f in TS_FIELDS}
    for form, timestamps in (("wire", wire),
                             ("reconstructed", {f: as_signed_form(v) for f, v in wire.items()})):
        try:
            pub.verify(sig, signing_bytes(receipt, timestamps))
            return form
        except InvalidSignature:
            continue
    # BOTH forms failed — only now is "tampered" the right word.
    sys.exit("FAIL: hub signature does not verify under either the transmitted "
             "timestamps or their to_rfc3339() form — the receipt is tampered with, "
             "or it was signed by a different key than the one it claims")


def report(receipt: dict, form: str) -> None:
    if form == "reconstructed":
        print("WARNING: verified only after reconstructing the SIGNED timestamp form "
              "(`Z` → `+00:00`) — the hub does not sign the string it transmits. The "
              "receipt is genuine; the FORMAT is not portable. See the docstring.")
    else:
        print("note: verified against the transmitted timestamps verbatim — the hub "
              "now signs what it sends, and the portability shim is no longer needed.")
    print(f"VALID: tier={receipt['tier']} owner={receipt['owner_lct_id']} "
          f"valid_until={receipt['valid_until']} — verified WITHOUT the hub or hestia")


def self_test() -> int:
    """Verify the committed golden fixture — a real receipt signed by hub-lib's own
    `signing_bytes()` (deterministic key + timestamps; regenerate with the
    `gen_receipt_fixture` example named in the fixture README). This is what
    catches a silent v2 → v3 drift in this file."""
    receipt = json.loads(FIXTURE.read_text())
    pub_bytes = bytes.fromhex(FIXTURE.with_suffix(".pubkey").read_text().strip())
    now = datetime.now(timezone.utc)

    form = verify(receipt, pub_bytes, now)
    print(f"self-test: golden fixture VERIFIES (form={form})")
    if form == "reconstructed":
        print("self-test: the Z vs +00:00 divergence is still present in signing_bytes v2 "
              "(expected today; the wire form starting to pass is the Rust-side fix landing)")

    # A tampered receipt must fail under BOTH forms — the shim must not rescue it.
    try:
        verify(dict(receipt, tier="single_device"), pub_bytes, now)
    except SystemExit as e:
        assert "tampered" in str(e), f"unexpected failure text: {e}"
        print("self-test: tampered tier correctly rejected under both forms")
    else:
        print("self-test FAILED: a tampered receipt verified")
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
    report(receipt, verify(receipt, pub_bytes, datetime.now(timezone.utc)))


if __name__ == "__main__":
    main()
