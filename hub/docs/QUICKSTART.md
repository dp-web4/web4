# AIC Hub — Chapter Organizer Quickstart

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
2. Generate a Sovereign identity
3. Initialize your chapter
4. Add 1-2 members + declare skills
5. Record a first event
6. Start the MCP server and query it

If any step doesn't work, see [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

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
hub gen-lct ./sovereign.json
```

This creates `sovereign.json`. **It contains private key material.** Treat it like an SSH key:

```bash
chmod 600 ./sovereign.json
```

Do not commit this file to git. Keep a backup somewhere safe.

---

## Step 3: Initialize your chapter

```bash
hub init "Your Chapter Name" --sovereign-lct ./sovereign.json
```

This creates a `your-chapter-name/` directory (slug derived from the name) containing:

- `charter.json` — your chapter's founding charter (auto-generated; see [`CHAPTER-LAW.md`](CHAPTER-LAW.md) to amend later)
- `society.json` — the 7-role society state (all roles initially filled by Sovereign; see [`ROLES.md`](ROLES.md) to delegate)
- `ledger.jsonl` — the witnessed event log (Genesis entry already written)
- `config.toml` — daemon config (MCP port, Sovereign LCT path)

The output prints 7 role LCT ids. **Save these somewhere** — you'll need them when delegating roles to other people later.

---

## Step 4: Add members + declare skills

Each member needs their own LCT. For an MVP demo, you can generate test ones:

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

## Step 7: Start the MCP server

```bash
hub serve ./your-chapter-name
```

By default this binds to `127.0.0.1:8770` (local-only, safe). In another terminal:

```bash
curl http://127.0.0.1:8770/tools | python3 -m json.tool
curl http://127.0.0.1:8770/tools/list_members | python3 -m json.tool
```

Stop the server with Ctrl-C.

For network-accessible deploy (e.g. on a small VPS for chapter-wide access), bind to all interfaces:

```bash
hub serve ./your-chapter-name --bind 0.0.0.0 --port 8770
```

Pair with a reverse proxy + TLS termination (caddy/nginx) for production. MVP itself doesn't terminate TLS.

---

## Step 8 (later): Verify the ledger

Periodically (or after any concerning event):

```bash
hub verify-ledger ./your-chapter-name
```

This walks the entire chain, recomputes every entry's hash, validates every signature, checks prev-hash links. If anything was tampered with, it errors loudly.

---

## What to do next

- Read [`CHAPTER-LAW.md`](CHAPTER-LAW.md) and amend your charter to reflect how your chapter actually wants to operate
- Read [`ROLES.md`](ROLES.md) and decide whether to delegate any roles
- For real members, have them generate their LCT on their own machine and share only the public id with you
- For automated coordination, hand the MCP URL to your chapter's AI tools (Claude Code, Cursor, custom agents)
- If something stumbles, [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) covers the common ones
