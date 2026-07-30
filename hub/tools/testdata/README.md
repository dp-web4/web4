# A2 golden fixture — `assurance_receipt_v3_golden.{json,pubkey}`

A real `AssuranceReceipt` produced by `hub-lib`'s own signer (`signing_bytes` **v3**,
`hub-lib/src/constellation.rs`), plus the Ed25519 public key that signed it.
Consumed by `../verify_assurance_receipt.py --self-test`.

It exists so the standalone Python verifier cannot silently drift from the Rust
canonical bytes: any field-order, domain-tag or timestamp-form change breaks the
self-test instead of surfacing at a relying party.

Properties chosen deliberately:

- **Deterministic** — fixed secret key and fixed timestamps, so regenerating
  reproduces these bytes exactly. The v3 regeneration kept the v2 UUIDs, nonce and
  `roster_hash` verbatim, so the committed diff is *only* the timestamp form and the
  signature — and the unchanged `.pubkey`/`hub_signer_key_id` prove the same secret
  was used.
- **`valid_until: 2099-01-01`** — the fixture must never expire out from under CI.
- **9 fractional digits on every timestamp** — v3's canonical form is fixed-width, so
  `valid_until` carries `.000000000` even though it is a whole second. That is the
  half of v3 a signature check alone would not catch (v2 varied the width with the
  value), and it is asserted directly against these bytes by the self-test. It also
  keeps exercising the arm `datetime.fromisoformat()` rejects before Python 3.12.
- **`Z` on the wire, and the signature covers exactly that** — under v2 the signed
  form was `…+00:00` while the wire form was `…Z`, so the canonical bytes were not
  reconstructable from a received receipt. This fixture is the cross-implementation
  proof that the divergence is gone: Python rebuilds the bytes from these strings
  verbatim and the Rust-produced signature verifies.

To regenerate (e.g. after a `signing_bytes` v4 bump), build a `hub-lib` example that
constructs the receipt with the same fixed secret (`secret[i] = i*7 + 11`, wrapping)
and the same UUIDs/timestamps, signs it, and prints `serde_json::to_string_pretty`
plus `hex::encode(kp.public_key_bytes())`. The generator is intentionally not
committed: it is a one-shot, and a stale generator alongside a fresh fixture is a
worse trap than no generator.
