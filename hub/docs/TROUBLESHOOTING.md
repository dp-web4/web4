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

## `hub init`

### "Sovereign LCT path / No such file or directory"

You passed `--sovereign-lct path/to/file.json` but the file doesn't exist. Generate one first:

```bash
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

The verifier needs to look up the actor LCT to validate signatures. MVP only knows the Sovereign LCT (loaded from `config.toml`'s `sovereign.lct_path`). If a ledger entry's actor is *not* the Sovereign (e.g. a member who signed their own action — V2 capability), the MVP verifier can't look them up.

Workarounds:
- Ensure all your ledger entries' `actor_lct_id` is the Sovereign's (which is what MVP CLI/MCP both produce — they always sign as Sovereign).
- For V2 / client-signed entries, the verifier needs an extended LCT registry. Not in MVP.

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

# Remove chapter dir (this destroys all chapter state — irreversible)
rm -rf ./your-chapter-name/

# Remove or regenerate the Sovereign LCT (this orphans any prior chapters
# signed by it — only do this if you're fully resetting)
rm ./sovereign.json
hub gen-lct ./sovereign.json

# Re-init
hub init "Your Chapter Name" --sovereign-lct ./sovereign.json
```

If you want to keep your chapter dir but start with a fresh ledger, that's not directly supported — the ledger IS the chapter's history; clearing it discards the chapter's identity for verification purposes. Better to start a fresh chapter than to clear a ledger.
