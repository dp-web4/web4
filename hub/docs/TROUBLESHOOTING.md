# Web4 Community Hub — Troubleshooting

Common stumbles + recovery. If your issue isn't here, run the failing command with `RUST_LOG=debug` for more detail.

## Build

### `cargo build` fails with "could not find Cargo.toml"

You're in the wrong directory. The hub workspace is at `web4/hub/`, not at `web4/` itself. `cd web4/hub` before building.

### `cargo build` fails with OpenSSL / pkg-config errors

The hub depends on web4-trust-core which links against system OpenSSL. On Debian/Ubuntu:

```bash
sudo apt install pkg-config libssl-dev
```

On macOS:

```bash
brew install openssl pkg-config
```

Then `cargo build --release` again.

---

## Vault & passphrase

The hub follows a **vault doctrine**: private keys are never written in the clear,
and hub state is encrypted at rest. Most of the "why won't this run?" surprises
trace back to `HUB_PASSPHRASE` not being set. See [`QUICKSTART.md`](QUICKSTART.md)
Step 0 for the full model.

### `hub gen-lct` / `hub init` fail: "refusing to write a plaintext private key"

The full message is *"HUB_PASSPHRASE is not set and there is no terminal to prompt
— refusing to write a plaintext private key (vault doctrine)."* You hit this in a
script, CI job, or container where there's no TTY to prompt. Set the passphrase:

```bash
export HUB_PASSPHRASE='your-passphrase'
hub gen-lct ./sovereign.json
```

An empty passphrase is allowed but must be **explicit** — `HUB_PASSPHRASE=`
(empty value) is a deliberate NULL choice (encrypted, but openable by anyone).
Leaving the variable *unset* is what triggers the error. At an interactive shell
the command will instead prompt you rather than erroring.

### "identity at X is an encrypted vault — set HUB_PASSPHRASE to unlock it"

A command tried to load your `sovereign.json` (or another identity file) and found
an encrypted vault (it starts with the `W4VT` magic) but no passphrase to open it.
Set `HUB_PASSPHRASE` (an empty value `HUB_PASSPHRASE=` is accepted if the vault was
sealed with a NULL passphrase):

```bash
export HUB_PASSPHRASE='your-passphrase'
```

### "hub state at X is encrypted but no HUB_PASSPHRASE is set"

Seen from `hub verify-ledger` (and other commands that open the state store) on an
encrypted hub. **This is expected, not corruption** — the SQLCipher state store
needs tier-1 ignition (the passphrase) to open. Set `HUB_PASSPHRASE` and re-run:

```bash
export HUB_PASSPHRASE='your-passphrase'
hub verify-ledger ./your-chapter-name
```

(Note: `hub serve` is the exception — it deliberately does *not* read the
passphrase from the environment at serve time; instead it boots a locked shell and
waits for `hub unlock`. See "Locked hub" below.)

### Rotating or recovering the passphrase

To change the vault passphrase to a new operator-chosen one:

```bash
# Stop the hub first.
pkill -f 'target/release/hub serve'

# Re-keys the Sovereign identity + the SQLCipher state store + the protected tier.
# Prompts for the current passphrase, then the new one (twice).
hub rotate-passphrase ./your-chapter-name

# Start the hub again — it boots LOCKED. Ignite with the NEW phrase:
hub serve ./your-chapter-name
hub unlock     # in another terminal; enter the new passphrase
```

**There is no passphrase recovery.** The passphrase is never stored anywhere. If
you lose it, the encrypted identity and state store are **unrecoverable** — there
is no backdoor and no reset that preserves the data. Back up the passphrase the
way you'd back up a root key.

---

## Locked hub / `hub unlock`

### `hub serve` came up but everything returns 503

Your hub state is encrypted, so on boot/restart the daemon comes up in a
**degraded locked shell**. The error body reads:

> `hub vault is locked — ignite it first (run hub unlock); only the unlock path is served while locked`

While locked, only a tiny tier-0 allowlist answers: the discovery doc
(`/.well-known/web4-hub.json`), the public law (`.../law`), the OID4VCI issuer
metadata (`.../.well-known/openid-credential-issuer`), and the unlock slot itself.
Everything else is `503` by design. Ignite it from the hub host:

```bash
hub unlock      # defaults to port 8770; prompts for the passphrase (or reads HUB_PASSPHRASE)
```

The unlock slot is loopback-only (127.0.0.1) and rate-limited; the passphrase is
used once and never stored.

### `hub unlock` can't identify the hub / no `public-identity.json`

A locked shell needs a clear `public-identity.json` to self-identify on
`/.well-known` and accept the unlock. If you never exported it, run once (with
`HUB_PASSPHRASE` set):

```bash
hub export-public-identity ./your-chapter-name
```

Then restart `hub serve` and try `hub unlock` again.

### Operator plane (port 8772) is unreachable

`hub serve` starts a second listener — the **operator plane** — at
`127.0.0.1:8772` (admit/deny/remove/re-key + write GUI at `/admin`). Common
reasons it's not reachable:

- **It's loopback-only by design.** It is *never* bound to the network, even with
  `--bind 0.0.0.0`. To reach it on a remote host, tunnel: `ssh -L 8772:127.0.0.1:8772 user@host`.
- **It was disabled.** `--admin-port 0` turns the operator plane off entirely.
  Pick a port (default 8772) with `--admin-port`. (8771 is taken by the membox
  sidecar, hence the 8772 default.)
- **The hub is still locked.** The operator plane is behind the same lock-gate —
  it also returns 503 until you `hub unlock`.

### tier-2 M-of-N unlock returns 501

`POST .../unlock/challenge` (the Sovereign-Council M-of-N unlock) returns *"tier-2
M-of-N unlock is not available on this hub (no unlock verifier plugin
configured)"*. **This is expected, not a bug** — the M-of-N quorum logic lives in a
separate verifier binary that isn't installed by default. It's N/A unless you set
`HUB_UNLOCK_VERIFIER` to point at that verifier. Use the tier-1 passphrase path
(`hub unlock`) instead.

---

## `hub init`

### "Sovereign LCT path / No such file or directory"

You passed `--sovereign-lct path/to/file.json` but the file doesn't exist. Generate one first (with `HUB_PASSPHRASE` set — see "Vault & passphrase" above):

```bash
export HUB_PASSPHRASE='your-passphrase'
hub gen-lct ./sovereign.json
hub init "Chapter Name" --sovereign-lct ./sovereign.json
```

### "Chapter already initialized — no changes made"

This is the idempotency report, not an error. The chapter dir already contains a `society.json`. Either:

- You're rerunning `hub init` and seeing the friendly no-op message — that's the intended behavior, exit code 0
- Or you want a different chapter in a new dir — pass `--hub-dir ./new-chapter-dir`

The hub refuses to overwrite an existing chapter to prevent accidental data loss. If you genuinely want to reset, delete the chapter directory manually and re-init.

---

## `hub serve`

### "Address already in use (os error 98)"

Port 8770 (or your configured port) is already bound. Either:

- A leftover `hub serve` from a previous run is still alive. Find + kill it:

  ```bash
  ss -ltnp | grep 8770
  pkill -f 'target/release/hub serve'
  ```

- Something else is using the port. Use a different port:

  ```bash
  hub serve <chapter-dir> --port 18770
  ```

### MCP requests work but state changes don't persist

You may have been hitting a different `hub serve` instance than you intended (e.g. one from a prior dir). Check `ss -ltnp | grep 8770` to confirm only one daemon is bound. The smoke scripts in `examples/` use randomized high ports to avoid this class of issue.

### MCP request returns "Failed to deserialize the JSON body"

The request payload doesn't match the expected schema. Check the `Content-Type: application/json` header is set, and that the JSON matches the field names the endpoint expects. Endpoint shapes are in [`README.md`](../README.md) under "MCP HTTP endpoints" — or call `GET /tools` for the live catalog.

---

## `hub verify-ledger`

### "entry N entry_hash mismatch"

The ledger file was tampered with after the entry was originally written. The chain's tamper-evidence is doing its job. Investigate:

- Did someone hand-edit `<chapter-dir>/ledger.jsonl`? (Should never happen in normal use — all acts go through CLI / MCP.)
- Was the file corrupted by a crash mid-write? Unlikely with the `OpenOptions::append` pattern but possible on power loss.

Recovery: restore from a backup of `ledger.jsonl`. If no backup, the entries from the bad index forward are unrecoverable (the chain is broken). Future versions may add periodic ACT mainnet anchoring (V2) which would let you re-anchor a clean prefix.

### "entry N signature verification failed"

Same root cause class as hash mismatch — content was edited (signature now mismatches the underlying bytes), or the actor LCT changed. Same recovery path.

### "entry N actor LCT not found by lookup"

The verifier needs to look up the actor LCT to validate signatures. The resolver
is seeded from the ledger itself, so it now knows more than just the founding
Sovereign:

- the **founding Sovereign** (from `config.toml`'s `sovereign.lct_path`),
- every **Sovereign-Council holder** (their pubkey is pinned into the ledger when
  you run `hub council add`), and
- every **admitted member** whose pubkey was pinned at admission — both those
  added via `hub add-member`/`hub set-member-key` with a pinned key and those who
  self-joined via `POST /v1/hubs/<id>/members/join`.

So this error now means a ledger entry's actor genuinely isn't in any of those
sets — e.g. a member who signed an action but whose pubkey was never pinned. Fix
the gap by pinning that member's channel key (`hub set-member-key <dir> <lct-id>
<pubkey-hex>`) so future verification can resolve them; entries signed before a key
was pinned can't be retroactively resolved.

### Sovereign LCT path resolution errors after moving the chapter dir

`hub init` stores an **absolute** Sovereign LCT path in `config.toml`. If you move `sovereign.json` after init, edit `config.toml`'s `[sovereign].lct_path` to the new absolute path. Then `hub verify-ledger` will find it.

---

## CLI

### "unknown role 'xyz'"

`hub assign-role` expects one of: `sovereign`, `law_oracle`, `policy_entity`, `treasurer`, `administrator`, `archivist`, `citizen`, `witness`, `auditor`. The matcher is case-insensitive and accepts hyphens (`law-oracle` ≡ `law_oracle`). Custom roles aren't exposed via this CLI in MVP.

### `--attended-by` parsing error in `hub record-event`

Multiple UUIDs are comma-separated, no spaces:

```bash
hub record-event ./chapter demo_night "Title" --attended-by "uuid1,uuid2,uuid3"
```

---

## Docker

### `docker compose build` fails to find sibling crates

Build context must be the **web4 repo root**, not `web4/hub/`. The `docker-compose.yml` ships with `context: ..` (one level up from hub/) for this reason. If you've copied just the hub/ directory somewhere else, the build needs web4-core and web4-trust-core present as siblings.

### Container starts but port 8770 isn't reachable

Inside the container, `hub serve --bind 127.0.0.1` would only be reachable inside the container. The compose file uses `--bind 0.0.0.0` so the port maps to the host. If you've overridden the command, ensure `--bind 0.0.0.0` is still there.

### Chapter state lost on container restart

Check `docker-compose.yml`'s volume mount: it should map `./chapter-data` to `/chapter` (or whatever your config points at). If the chapter dir isn't a mounted volume, state lives inside the container's writable layer and dies with the container.

---

## Reset to clean slate

If something is wedged beyond troubleshooting and you want to start over:

```bash
# Stop any running daemons
pkill -f 'target/release/hub serve'

# Remove chapter dir (this destroys all chapter state — irreversible).
# This also removes the encrypted state store, the clear public-identity.json,
# and the protected.hvlt tier that live inside it. For a partial reset that
# keeps the dir, at minimum remove these two:
#   rm -f ./your-chapter-name/public-identity.json ./your-chapter-name/protected.hvlt
rm -rf ./your-chapter-name/

# Remove or regenerate the Sovereign LCT (this orphans any prior chapters
# signed by it — only do this if you're fully resetting)
rm ./sovereign.json

# HUB_PASSPHRASE must be set — gen-lct and init both need it (vault doctrine).
export HUB_PASSPHRASE='your-passphrase'
hub gen-lct ./sovereign.json

# Re-init (still needs HUB_PASSPHRASE)
hub init "Your Chapter Name" --sovereign-lct ./sovereign.json
```

If you want to keep your chapter dir but start with a fresh ledger, that's not directly supported — the ledger IS the chapter's history; clearing it discards the chapter's identity for verification purposes. Better to start a fresh chapter than to clear a ledger.
