# Cross-language verification: Python mints, Rust verifies the same ledger

The point of this example is not the LCT itself — it's that **the on-disk
ledger format is the contract**. Any language with a Web4 spec implementation
can verify what any other language minted, with no shared runtime.

## What it shows

1. Python writes a hash-chained `LocalLedger` to disk and mints an LCT into it.
2. Rust opens the *same file*, replays + verifies the hash chain on load, looks
   up the LCT by id, checks the fingerprint matches, and verifies an anchor
   proof — all under the Rust implementation.
3. If the chain were tampered between steps, `LocalLedger::open` would refuse
   to load it. If the LCT were modified, the fingerprint wouldn't match. If
   the inclusion proof were forged, `verify_proof` would return false.

The verifier never trusts the minter. It only trusts the format and its own
implementation of the spec.

## Run it

Prerequisites: `pip install web4-core` (>= 0.1.1) and a Rust toolchain.

```sh
# From web4-core/examples/cross_language_verify/
python mint.py

# Then from the web4-core/ directory:
cd ../..
cargo run --example cross_language_verify -- \
    --ledger examples/cross_language_verify/shared_ledger.jsonl \
    --lct-sidecar examples/cross_language_verify/shared_lct.json
```

You should see Python report mint + self-verify, then Rust report chain replay,
LCT lookup, fingerprint match, and anchor-proof verification.

## What this is *not*

- **Not** a transport protocol. It's an on-disk-file demo. Real cross-fleet
  Web4 deployments coordinate ledgers via published spec mechanisms; this
  demo isolates the file-format-as-contract claim from those concerns.
- **Not** a benchmark. The chain-replay step in `LocalLedger::open` reads
  every entry; for large ledgers a production verifier would use
  incremental-proof primitives instead.
- **Not** the only language pair. The same pattern works for any
  spec-conforming implementation. Python and Rust are the two we ship; a
  Go, Java, or TypeScript verifier would behave identically given the same
  bytes on disk.

## Why this matters for the standard

A standard whose implementations only interoperate within one vendor's
runtime isn't a standard — it's a vendor product with extra steps. This
example is the cheapest possible artifact that demonstrates Web4 doesn't
have that problem at the ledger layer. The same demo at the LCT/T3/V3
layer is the next step (cross-language verification of trust observations
and witness chains, not just presence).
