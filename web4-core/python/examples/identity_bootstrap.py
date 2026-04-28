#!/usr/bin/env python3
"""
Identity bootstrap example — persistent Web4 LCT for one host.

The README's quickstart shows in-process LCT creation + InMemoryLedger.
This example shows what comes next: a one-command setup that gives a host
a durable, verifiable presence — keypair on disk (chmod 600), local
hash-chained ledger, JSON sidecar with the public LCT data, and an
idempotent re-run that verifies the chain instead of regenerating.

Usage:

    python identity_bootstrap.py                     # name from $HOSTNAME
    python identity_bootstrap.py --name laptop-01
    python identity_bootstrap.py --verify            # read-only attestation
    python identity_bootstrap.py --base-dir /var/lib/web4

Layout (under --base-dir, default ~/.web4):

    {name}/
      keypair.bin       0600  Ed25519 secret key (32 bytes)        # NEVER commit
      public_key.bin    0644  Ed25519 public key (32 bytes)
      ledger.jsonl      0644  Hash-chained ledger (LocalLedger)
      lct.json          0644  Public LCT metadata (id, fingerprint, ...)

Re-running the script is safe: if `lct.json` already exists, the script
verifies that the keypair on disk derives the stored public key, replays
the ledger to confirm chain integrity, and re-checks the anchor proof.
It exits non-zero on any inconsistency.

This is intended as a starting point — copy it, adapt the entity type,
add hardware-binding (TPM / secure enclave), commit the public sidecar
to your fleet directory, etc. It is deliberately small.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path

import web4_core


def public_lct_dict(lct: web4_core.PyLct, public: bytes, name: str) -> dict:
    return {
        "schema": "web4-core.example.identity/v1",
        "name": name,
        "lct_id": lct.id,
        "entity_type": str(lct.entity_type).split(".")[-1],
        "fingerprint": lct.fingerprint(),
        "lineage_depth": lct.lineage_depth,
        "parent_id": lct.parent_id,
        "trust_ceiling": lct.trust_ceiling(),
        "coherence_threshold": lct.coherence_threshold(),
        "is_active": lct.is_active(),
        "public_key_alg": "Ed25519",
        "public_key_hex": public.hex(),
    }


def _write(path: Path, data, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, dict):
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    elif isinstance(data, bytes):
        path.write_bytes(data)
    else:
        raise TypeError(f"unsupported payload: {type(data)}")
    os.chmod(path, mode)


def bootstrap(name: str, base_dir: Path, entity_type: web4_core.PyEntityType) -> int:
    home = base_dir / name
    keypair_path = home / "keypair.bin"
    pubkey_path = home / "public_key.bin"
    ledger_path = home / "ledger.jsonl"
    lct_path = home / "lct.json"

    if lct_path.exists() and keypair_path.exists() and ledger_path.exists():
        print(f"[{name}] already bootstrapped; verifying...")
        return verify(name, base_dir)

    print(f"[{name}] generating fresh LCT (entity_type={entity_type})...")
    lct, kp = web4_core.PyLct.new(entity_type, None)
    secret = bytes(kp.secret_key_bytes())
    public = bytes(kp.public_key_bytes())

    home.mkdir(parents=True, exist_ok=True)
    ledger = web4_core.PyLocalLedger.open(str(ledger_path))
    receipt = ledger.mint(lct)
    proof = ledger.anchor(lct.id)
    if not ledger.verify_proof(proof):
        print(f"[{name}] FAIL: anchor proof did not verify after mint", file=sys.stderr)
        return 4

    _write(keypair_path, secret, 0o600)
    _write(pubkey_path, public, 0o644)
    _write(lct_path, public_lct_dict(lct, public, name), 0o644)

    print(f"[{name}] LCT minted: {lct.id}")
    print(f"[{name}]   fingerprint:  {lct.fingerprint()}")
    print(f"[{name}]   public key:   {public.hex()[:32]}...")
    print(f"[{name}]   ledger entry: {receipt.entry_index} (hash {receipt.entry_hash[:16]}...)")
    print()
    print(f"[{name}] Files:")
    print(f"  SECRET (chmod 600):  {keypair_path}")
    print(f"  public key:          {pubkey_path}")
    print(f"  ledger:              {ledger_path}")
    print(f"  public LCT data:     {lct_path}")
    return 0


def verify(name: str, base_dir: Path) -> int:
    home = base_dir / name
    keypair_path = home / "keypair.bin"
    pubkey_path = home / "public_key.bin"
    ledger_path = home / "ledger.jsonl"
    lct_path = home / "lct.json"

    missing = [p for p in [keypair_path, pubkey_path, ledger_path, lct_path] if not p.exists()]
    if missing:
        print(f"[{name}] NOT bootstrapped — missing: {[str(p) for p in missing]}", file=sys.stderr)
        return 1

    secret = keypair_path.read_bytes()
    kp = web4_core.PyKeyPair.from_secret_bytes(secret)
    derived_public = bytes(kp.public_key_bytes())
    stored_public = pubkey_path.read_bytes()
    if derived_public != stored_public:
        print(f"[{name}] FAIL: keypair-derived public key != stored public key",
              file=sys.stderr)
        return 2

    ledger = web4_core.PyLocalLedger.open(str(ledger_path))
    lct_data = json.loads(lct_path.read_text())
    proof = ledger.anchor(lct_data["lct_id"])
    if not ledger.verify_proof(proof):
        print(f"[{name}] FAIL: ledger proof for {lct_data['lct_id']} does not verify",
              file=sys.stderr)
        return 3
    if lct_data["public_key_hex"] != derived_public.hex():
        print(f"[{name}] FAIL: lct.json public key != keypair-derived", file=sys.stderr)
        return 4

    print(f"[{name}] OK")
    print(f"  lct_id:      {lct_data['lct_id']}")
    print(f"  fingerprint: {lct_data['fingerprint']}")
    print(f"  entity:      {lct_data['entity_type']}")
    print(f"  ledger:      {ledger_path} (chain verified)")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Bootstrap a persistent Web4 identity.")
    p.add_argument("--name", default=None,
                   help="Identity name (default: hostname). Used as the subdirectory name.")
    p.add_argument("--base-dir", default=str(Path.home() / ".web4"),
                   help="Parent directory for identity files (default: ~/.web4).")
    p.add_argument("--entity-type", default="AiSoftware",
                   choices=["Human", "AiSoftware", "AiEmbodied", "Organization",
                            "Role", "Task", "Resource", "Hybrid"],
                   help="Entity type for the LCT (default: AiSoftware).")
    p.add_argument("--verify", action="store_true",
                   help="Verify existing identity without mutating anything.")
    args = p.parse_args()

    name = (args.name or socket.gethostname()).lower().split(".")[0].strip()
    base_dir = Path(args.base_dir).expanduser()
    entity_type = getattr(web4_core.PyEntityType, args.entity_type)

    if args.verify:
        return verify(name, base_dir)
    return bootstrap(name, base_dir, entity_type)


if __name__ == "__main__":
    sys.exit(main())
