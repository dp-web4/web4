# A2 golden fixture — `assurance_receipt_v2_golden.{json,pubkey}`

A real `AssuranceReceipt` produced by `hub-lib`'s own signer (`signing_bytes` **v2**,
`hub-lib/src/constellation.rs`), plus the Ed25519 public key that signed it.
Consumed by `../verify_assurance_receipt.py --self-test`.

It exists so the standalone Python verifier cannot silently drift from the Rust
canonical bytes: any field-order, domain-tag or timestamp-form change breaks the
self-test instead of surfacing at a relying party.

Properties chosen deliberately:

- **Deterministic** — fixed secret key and fixed timestamps, so regenerating
  reproduces these bytes exactly.
- **`valid_until: 2099-01-01`** — the fixture must never expire out from under CI.
- **9 fractional digits on `issued_at`/`bound_at`** — what chrono emits whenever
  nanos are nonzero, and the arm `datetime.fromisoformat()` rejects before Python 3.12.
- **`Z` on the wire** — the divergence from the signed `+00:00` form is visible in
  the committed bytes, so the finding is reproducible from this directory alone.

To regenerate (e.g. after a `signing_bytes` v3 bump), build a `hub-lib` example that
constructs the receipt with the same fixed secret (`secret[i] = i*7 + 11`, wrapping)
and the same UUIDs/timestamps, signs it, and prints `serde_json::to_string_pretty`
plus `hex::encode(kp.public_key_bytes())`. The generator is intentionally not
committed: it is a one-shot, and a stale generator alongside a fresh fixture is a
worse trap than no generator.
