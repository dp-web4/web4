# Web4 Community Hub — Chapter Organizer Quickstart

**Audience:** chapter lead, comfortable with a terminal, no DevOps experience required.
**Reading time:** 5 minutes.
**Time to first running chapter:** 10-30 minutes depending on whether you build from source or use Docker.

---

## Five-minute mental model

Your chapter is going to operate as a **Web4 society**. Three things to picture:

1. **A chapter directory** — one folder on disk (e.g. `~/chapter-data/`). All chapter state lives here: founding charter, ledger of every action ever taken, configuration.
2. **A Sovereign identity** — a cryptographic keypair you (or your chapter's leadership) hold. The Sovereign signs the founding charter and (in MVP) acts as the chapter's witness for member-list changes, role assignments, recorded events, etc.
3. **The hub daemon** — a small binary that owns those files and exposes an MCP HTTP server. Members, AI tools, and downstream applications query and update chapter state through the daemon.

The daemon is local-first. There is no central server, no cloud account, no vendor relationship. You hold your data; you can fork the code.

---

## What you'll do in the next 30 minutes

1. Get a `hub` binary (build from source OR pull the Docker image)
2. Set `HUB_PASSPHRASE` (the secret that guards your hub's vault)
3. Generate a Sovereign identity
4. Initialize your chapter
5. Add 1-2 members + declare skills
6. Record a first event
7. Start the server, unlock (ignite) it, and query it

If any step doesn't work, see [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

---

## Step 0: Set `HUB_PASSPHRASE` first

The hub follows a **vault doctrine**: a private key is never written to disk in
the clear, and "no passphrase" must be an *explicit* choice rather than a silent
default. Several commands — `hub gen-lct`, `hub init`, `hub verify-ledger`,
`hub export-public-identity` — therefore need a passphrase to run. The cleanest
way to supply it is the `HUB_PASSPHRASE` environment variable:

```bash
export HUB_PASSPHRASE='choose-a-strong-passphrase'
```

This one secret encrypts your Sovereign identity **and** your hub's state store
(both at rest). Guard it like the master key it is — **if you lose it, the
identity and state are unrecoverable** (see Step 2).

Two important nuances:

- **Empty is allowed, but must be explicit.** `HUB_PASSPHRASE=` (set to an empty
  value) is a deliberate *NULL passphrase* choice — the vault is still encrypted,
  but it's openable by anyone. Use this only for throwaway demos.
- **Unset + no terminal = hard error.** If `HUB_PASSPHRASE` is unset and there's
  no TTY to prompt (CI, a script, a container), the affected commands fail closed
  with *"refusing to write a plaintext private key"*. At an interactive shell
  they'll instead prompt you for the passphrase.

The examples below assume `HUB_PASSPHRASE` is exported in your shell.

---

## Step 1: Get the binary

### Option A: Build from source (requires Rust toolchain)

```bash
git clone https://github.com/dp-web4/web4.git
cd web4/hub
cargo build --release
export PATH="$PWD/target/release:$PATH"
hub --version    # should print: hub 0.1.0-alpha.0
```

### Option B: Docker

```bash
git clone https://github.com/dp-web4/web4.git
cd web4/hub
docker compose build hub
alias hub='docker compose run --rm hub'
```

Docker version is convenient but adds the wrap-everything-in-a-container layer to every command. For the first chapter, source build is usually friendlier.

---

## Step 2: Generate a Sovereign identity

```bash
# HUB_PASSPHRASE must be set (see Step 0) — gen-lct refuses to write a
# plaintext key.
hub gen-lct ./sovereign.json
```

This creates `sovereign.json` as an **encrypted vault** (it starts with the
`W4VT` magic, not JSON). The private key is encrypted at rest under your
`HUB_PASSPHRASE` — so the file itself is no longer the secret to protect; the
**passphrase is**.

That changes the old "treat it like an SSH key" advice:

- **Guard `HUB_PASSPHRASE`, not the file.** The encrypted vault is useless to an
  attacker without the passphrase. Conversely, **lose the passphrase and the
  identity is gone** — there is no recovery path and no stored copy.
- A `chmod 600 ./sovereign.json` is still tidy hygiene, and you should still keep
  a backup of the file, but neither helps if the passphrase is lost.
- Don't commit `sovereign.json` to git, and never put `HUB_PASSPHRASE` in a file
  that lands in git either.

(Used an empty `HUB_PASSPHRASE=`? Then the vault *is* openable by anyone — re-key
it with a real passphrase via `hub rotate-passphrase` before going live.)

---

## Step 3: Initialize your chapter

`hub init` reads your (encrypted) Sovereign identity and writes the hub's state
store, so `HUB_PASSPHRASE` must still be set (Step 0):

```bash
# File-backed (default; MVP-compatible JSON/JSONL layout)
hub init "Your Chapter Name" --sovereign-lct ./sovereign.json

# Or SQLite-backed (one chapter.db file; better for ops — encrypted at rest)
hub init "Your Chapter Name" --sovereign-lct ./sovereign.json --storage sqlite
```

This creates a `your-chapter-name/` directory (slug derived from the name). With the file backend you get:

- `charter.json` — your chapter's founding charter (auto-generated; see [`HUB-LAW.md`](HUB-LAW.md) to amend later)
- `society.json` — society state (V2-1: founder fills Sovereign + Citizen; other roles assigned later per hub law — see [`ROLES.md`](ROLES.md))
- `ledger.jsonl` — the witnessed event log (Genesis entry already written)
- `config.toml` — daemon config (MCP port, Sovereign LCT path)

With the sqlite backend, all chapter state lives in `chapter.db`; only `config.toml` sits alongside.

The output prints the founder's role LCT ids. **Save these somewhere** — you'll need them when assigning roles to other members later.

See [`STORAGE.md`](STORAGE.md) for backend comparison and migration (`hub migrate <dir> --to sqlite`).

---

## Step 4: Add members + declare skills

Each member needs their own LCT. For an MVP demo, you can generate test ones
(again with `HUB_PASSPHRASE` set — these are encrypted vaults too):

```bash
hub gen-lct ./alice.json
hub gen-lct ./bob.json
```

(In real use, a member generates their own LCT on their machine and gives you the public id; you don't hold their private key.)

Grab the LCT ids and add them:

```bash
ALICE_ID=$(python3 -c "import json; print(json.load(open('alice.json'))['lct']['id'])")
BOB_ID=$(python3 -c "import json; print(json.load(open('bob.json'))['lct']['id'])")

hub add-member ./your-chapter-name "$ALICE_ID" --name "Alice"
hub add-member ./your-chapter-name "$BOB_ID" --name "Bob"

hub declare-skill ./your-chapter-name "$ALICE_ID" "Medical Imaging RAG"
hub declare-skill ./your-chapter-name "$BOB_ID" "Distributed Systems"
```

### Two ways members get in

The `hub add-member` above is the **Sovereign-side** path: you, holding the
chapter's authority, add a member you already know. Use it for bootstrapping and
for members whose public id you've been handed out-of-band.

Once your hub is serving (Step 7), there's also a **request-driven** path that
needs no Sovereign action up front:

1. A prospective member POSTs a signed join request to
   `POST /v1/hubs/<hub-id>/members/join` (the request carries their own LCT id +
   public key, signed with their key).
2. Your hub's **law gate** (the PolicyEntity, evaluating the request as
   `role="applicant"`) decides: *Allow* admits them immediately, *Deny* rejects
   with a 403, *Escalate* parks the request in an operator review queue.
3. For escalated requests you (the operator) **Admit** or **Deny** them live from
   the operator plane (Step 7) — no restart, no re-keying. Admission appends a
   Sovereign-signed `MemberAdded` and pins their pubkey so their next request
   authenticates as a citizen.

Both paths converge on the same witnessed ledger entry; pick whichever fits.

---

## Step 5: Record a first event

```bash
hub record-event ./your-chapter-name demo_night "First Demo Night" \
  --attended-by "$ALICE_ID,$BOB_ID"
```

---

## Step 6: Query the chapter

```bash
hub query members ./your-chapter-name
hub query skill ./your-chapter-name imaging       # finds Alice
hub query chapter ./your-chapter-name             # full identity + role-fill
hub status ./your-chapter-name                    # one-line summary
```

---

## Step 7: Start the server, then unlock (ignite) it

```bash
hub serve ./your-chapter-name
```

`hub serve` starts **two listeners**:

- **Fleet plane** — default `127.0.0.1:8770` (`--bind` / `--port` to change). This
  is the read-only dashboard + the MCP tools and REST APIs.
- **Operator plane** — `127.0.0.1:8772`, **always loopback-only** (never bound to
  the network, regardless of `--bind`). This carries the admit/deny/remove/re-key
  admin actions and the write GUI. Change it with `--admin-port`, or disable it
  entirely with `--admin-port 0`.

### Ignite the vault (`hub unlock`)

Because your hub's state store is encrypted (Step 0) and the daemon never reads
the passphrase from the environment at serve time, an encrypted hub **boots into
a locked shell**: it comes up, but returns `503` on essentially everything except
the unlock path (and a little tier-0 discovery: `/.well-known/web4-hub.json`,
the public law, and OID4VCI issuer metadata). You'll see a warning in the log and
this on requests:

> `hub vault is locked — ignite it first (run hub unlock)`

Ignite it at runtime, from the hub host, in another terminal:

```bash
# export-public-identity ONCE per hub first (see below), then:
hub unlock            # defaults to the hub on port 8770; prompts for the passphrase
```

`hub unlock` prompts for the passphrase in *its* UI (or reads `HUB_PASSPHRASE`),
uses it once over the loopback-only `/unlock` slot, and **never stores it**. The
slot is rate-limited and 127.0.0.1-only. After it succeeds the hub serves
citizen-tier requests normally.

> First-time setup: run `hub export-public-identity ./your-chapter-name` once
> (needs `HUB_PASSPHRASE`). It writes a clear `public-identity.json` so a locked
> shell can identify itself on `/.well-known` and accept your `hub unlock`. Skip
> this and the locked shell can't self-identify.

### Query it

Once unlocked, in another terminal:

```bash
curl http://127.0.0.1:8770/tools | python3 -m json.tool
curl http://127.0.0.1:8770/tools/list_members | python3 -m json.tool
```

Operator actions (admitting the join requests from Step 4, removing members,
re-keying channels) live on the operator plane:

```
http://127.0.0.1:8772/admin
```

Stop the server with Ctrl-C.

For network-accessible deploy (e.g. on a small VPS for chapter-wide access), bind
the **fleet** plane to all interfaces — the operator plane stays loopback-only by
design:

```bash
hub serve ./your-chapter-name --bind 0.0.0.0 --port 8770
```

Pair with a reverse proxy + TLS termination (caddy/nginx) for production. MVP
itself doesn't terminate TLS. To reach the operator plane on a remote box, tunnel
to it over SSH (`ssh -L 8772:127.0.0.1:8772 ...`) rather than exposing it.

### Changing the passphrase later

To rotate the vault secret to a new operator-chosen one: stop the hub, run
`hub rotate-passphrase ./your-chapter-name` (re-keys the identity + state store),
then start it again — it boots locked, so ignite it with `hub unlock` using the
**new** phrase.

---

## Step 8 (later): Verify the ledger

Periodically (or after any concerning event):

```bash
# Needs HUB_PASSPHRASE: verify-ledger opens the encrypted state store, so on an
# encrypted hub it errors without the passphrase (that's expected, not corruption).
hub verify-ledger ./your-chapter-name
```

This walks the entire chain, recomputes every entry's hash, validates every signature, checks prev-hash links. If anything was tampered with, it errors loudly.

---

## What to do next

- Read [`HUB-LAW.md`](HUB-LAW.md) and amend your charter to reflect how your chapter actually wants to operate
- Read [`ROLES.md`](ROLES.md) and decide whether to delegate any roles
- For real members, have them generate their LCT on their own machine and share only the public id with you
- For automated coordination, hand the MCP URL to your chapter's AI tools (Claude Code, Cursor, custom agents)
- If something stumbles, [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) covers the common ones
