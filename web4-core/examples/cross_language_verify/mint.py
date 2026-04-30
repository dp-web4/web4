#!/usr/bin/env python3
"""Cross-language interop demo, Python side.

Mints an LCT into a hash-chained `LocalLedger` on disk. The Rust verifier
(`cargo run --example cross_language_verify`) opens the *same file* and
verifies the chain integrity + anchor proof — proving that the on-disk
format is the contract, not the language.

Usage:

    python mint.py                          # writes ./shared_ledger.jsonl
    python mint.py --ledger /tmp/demo.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import web4_core


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ledger",
        default="./shared_ledger.jsonl",
        help="Path to ledger.jsonl (default: ./shared_ledger.jsonl)",
    )
    parser.add_argument(
        "--out",
        default="./shared_lct.json",
        help="Path to write the public LCT id sidecar (default: ./shared_lct.json)",
    )
    args = parser.parse_args()

    ledger_path = Path(args.ledger).resolve()
    out_path = Path(args.out).resolve()

    print(f"[python] Opening LocalLedger at {ledger_path}")
    ledger = web4_core.PyLocalLedger.open(str(ledger_path))

    print("[python] Creating LCT (PyEntityType.Human, no parent)...")
    lct, kp = web4_core.PyLct.new(web4_core.PyEntityType.Human, None)

    print(f"[python] Minting LCT {lct.id}...")
    receipt = ledger.mint(lct)
    print(
        f"[python]   entry_index = {receipt.entry_index}, "
        f"entry_hash = {receipt.entry_hash[:16]}..."
    )

    proof = ledger.anchor(lct.id)
    assert ledger.verify_proof(proof), "self-verify failed (Python side)"
    print("[python] Anchor proof verifies on the Python side.")

    out_path.write_text(
        json.dumps(
            {
                "lct_id": lct.id,
                "fingerprint": lct.fingerprint(),
                "public_key_hex": bytes(kp.public_key_bytes()).hex(),
                "ledger_path": str(ledger_path),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"[python] Wrote public sidecar to {out_path}")
    print()
    print(
        f"Now run from the web4-core/ directory:\n"
        f"    cargo run --example cross_language_verify -- "
        f"--ledger {ledger_path} --lct-sidecar {out_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
