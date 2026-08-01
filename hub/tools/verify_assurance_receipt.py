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
# Every field this file reads off the wire, in `signing_bytes` order so a v3 → v4
# field-list drift shows up as a diff here too. `signature` is not signed over, but
# it is read from the same untrusted JSON and gets the same treatment.
WIRE_FIELDS = ("owner_lct_id", "tier", "pair_id", "challenge_nonce") + TS_FIELDS + (
    "hub_lct_id", "hub_signer_lct_id", "hub_signer_key_id", "roster_hash", "signature")
FIXTURE = pathlib.Path(__file__).with_name("testdata") / "assurance_receipt_v3_golden.json"


def uuid_bytes(field: str, s: str) -> bytes:
    import uuid
    try:
        return uuid.UUID(s).bytes  # big-endian, matches Rust Uuid::as_bytes()
    except ValueError:
        sys.exit(f"FAIL: {field} is not a UUID: {s!r}")


def require_wire_fields(r) -> None:
    """Presence and type for every field this verifier reads, checked BEFORE any of
    them is used.

    A relying party's tool has exactly one product: a verdict. Without this gate the
    first absent or non-string field raises a bare `KeyError`/`AttributeError`, and
    because the reads are spread across `verify`, `signing_bytes` and `report`, the
    exception you get depends on which field is missing. Measured 2026-08-01: all
    twelve fields, plus a non-object receipt, exited with a traceback. The verdict
    for an incomplete receipt is FAIL, and it has to be spelled that way."""
    if not isinstance(r, dict):
        sys.exit(f"FAIL: receipt is not a JSON object (got {type(r).__name__})")
    if missing := [f for f in WIRE_FIELDS if f not in r]:
        sys.exit(f"FAIL: receipt is missing required field(s): {', '.join(missing)}")
    if nonstr := [f for f in WIRE_FIELDS if not isinstance(r[f], str)]:
        sys.exit(f"FAIL: these fields must be JSON strings: {', '.join(nonstr)}")


def parse_ts(field: str, s: str) -> datetime:
    """For the freshness COMPARISON only — never for the signed bytes.

    `fromisoformat` accepts only 3- or 6-digit fractions before Python 3.12, and
    the canonical form always carries 9. Truncate to microseconds rather than
    crash with an uncaught ValueError on 3.11. Parsing is lossy here by design;
    the signature never sees a parsed value.

    The `Z` fixup used to be spelled `s.replace("Z", "+00:00")`, which is defeated
    by the input it most needs to survive: a double-suffixed `…+00:00Z` becomes
    `…+00:00+00:00` and raises (kimi-code, forum 2026-08-01; reproduced here on
    3.14.4). Slicing the terminal `Z` says what was meant, but the double-suffixed
    form still has no instant to recover — so the repair is that the ValueError
    becomes this tool's own FAIL instead of escaping as a traceback. This is the
    FIRST thing `verify` touches and it is fed an untrusted string, so being total
    over its input domain is part of the contract, not defensive padding."""
    iso = s[:-1] + "+00:00" if s.endswith("Z") else s
    if "." in iso:
        head, _, rest = iso.partition(".")
        digits = rest[: len(rest) - len(rest.lstrip("0123456789"))]
        iso = f"{head}.{digits[:6]}{rest[len(digits):]}"
    try:
        return datetime.fromisoformat(iso)
    except ValueError:
        sys.exit(f"FAIL: {field} is not a parseable RFC3339 timestamp: {s!r}")


def signing_bytes(r: dict) -> bytes:
    """Field order + encoding MUST match hub-lib `signing_bytes()` exactly.
    Every string is taken from the wire verbatim — see the module docstring."""
    b = bytearray(DOMAIN)
    b += uuid_bytes("owner_lct_id", r["owner_lct_id"])
    b += r["tier"].encode()                       # wire_tag: single_device/... (serde snake_case)
    b += uuid_bytes("pair_id", r["pair_id"])
    b += r["challenge_nonce"].encode()
    for f in TS_FIELDS:
        b += r[f].encode()
    b += uuid_bytes("hub_lct_id", r["hub_lct_id"])
    b += uuid_bytes("hub_signer_lct_id", r["hub_signer_lct_id"])
    b += r["hub_signer_key_id"].encode()
    b += r["roster_hash"].encode()
    return bytes(b)


def key_id(pubkey_bytes: bytes) -> str:
    return hashlib.sha256(pubkey_bytes).digest()[:8].hex()


def verify(receipt: dict, pub_bytes: bytes, now: datetime) -> None:
    """Raises SystemExit on any failure (wire shape, freshness, attribution, signature)."""
    # 0. wire shape — every field present and a string, so the checks below can read
    #    the receipt without a malformed one aborting the tool before it can judge.
    require_wire_fields(receipt)
    # 1. freshness
    if now > parse_ts("valid_until", receipt["valid_until"]):
        sys.exit("FAIL: receipt is expired (valid_until in the past)")
    # 2. signer-key attribution — the key must be the one the receipt claims
    if key_id(pub_bytes) != receipt["hub_signer_key_id"]:
        sys.exit(f"FAIL: key_id mismatch — this pubkey ({key_id(pub_bytes)}) is not "
                 f"the receipt's signer ({receipt['hub_signer_key_id']})")
    # 3. the hub's signature over the canonical bytes, rebuilt from the wire.
    try:
        sig = bytes.fromhex(receipt["signature"])
    except ValueError:
        sys.exit(f"FAIL: signature is not hex: {receipt['signature']!r}")
    try:
        Ed25519PublicKey.from_public_bytes(pub_bytes).verify(sig, signing_bytes(receipt))
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
    parse_ts("issued_at", receipt["issued_at"])

    # Malformed receipts must produce this tool's VERDICT, not a traceback. Each case
    # below is one that was measured escaping as an uncaught exception on 2026-08-01;
    # the double-suffixed timestamp is the one kimi-code reported from the forum. The
    # assertion is deliberately on the exception TYPE as much as the text: `SystemExit`
    # is the tool speaking, anything else is the interpreter speaking over it.
    malformed = [
        ("double-suffixed valid_until", dict(receipt, valid_until="2099-01-01T00:00:00.000000000+00:00Z")),
        ("unparseable valid_until",     dict(receipt, valid_until="garbage")),
        ("missing valid_until",         {k: v for k, v in receipt.items() if k != "valid_until"}),
        ("missing signature",           {k: v for k, v in receipt.items() if k != "signature"}),
        ("non-string tier",             dict(receipt, tier=123)),
        ("null roster_hash",            dict(receipt, roster_hash=None)),
        ("owner_lct_id not a uuid",     dict(receipt, owner_lct_id="nope")),
        ("signature not hex",           dict(receipt, signature="zzzz")),
        ("receipt is not an object",    [1, 2, 3]),
    ]
    for name, bad in malformed:
        try:
            verify(bad, pub_bytes, now)
        except SystemExit as e:
            if not str(e).startswith("FAIL"):
                print(f"self-test FAILED: {name} exited without a FAIL verdict: {e}")
                return 1
        except Exception as e:  # noqa: BLE001 — the whole point is that nothing else escapes
            print(f"self-test FAILED: {name} escaped as {type(e).__name__}: {e}")
            return 1
        else:
            print(f"self-test FAILED: {name} was accepted")
            return 1
    print(f"self-test: {len(malformed)} malformed receipts each rejected with a FAIL verdict, "
          f"none as a traceback")
    print("self-test: OK")
    return 0


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        sys.exit(self_test())
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    try:
        receipt = json.load(open(sys.argv[1]))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"FAIL: cannot read {sys.argv[1]} as JSON: {e}")
    try:
        pub_bytes = bytes.fromhex(sys.argv[2].strip())
    except ValueError:
        sys.exit("FAIL: the pubkey argument is not hex")
    if len(pub_bytes) != 32:
        sys.exit(f"FAIL: an Ed25519 pubkey is 32 bytes; got {len(pub_bytes)}")
    verify(receipt, pub_bytes, datetime.now(timezone.utc))
    report(receipt)


if __name__ == "__main__":
    main()
