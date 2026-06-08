# Hestia Mode

**Status:** V2-7 Step 3b — landed end-to-end including the ergonomic `hub init --sovereign-hestia` CLI. Hub binary holds NO Sovereign keypair during init or serve.

In Hestia mode, the hub holds **NO Sovereign keypair**. Every signature attributed to the Sovereign is produced by a remote signer (Hestia) that the hub calls over HTTP. This honors architecture commitment #8 (secrets in vault only) on the hub side.

## Why this matters

The MVP convention — operator's IdentityFile sitting on disk, hub loads it at `serve` time, hub keeps the keypair in process — is convenient but conflicts with commitment #8. A compromised hub process = compromised Sovereign keys. Hestia mode moves the keypair into the operator's Hestia vault; the hub only ever sees a public key (to verify) and signatures Hestia returns. Compromising the hub no longer compromises the Sovereign.

## What's the same

- Chapter storage (`charter.json` / `society.json` / `chapter.db`): identical layout.
- Ledger entries: identical schema. The signature in each entry is now Hestia-produced rather than hub-produced; the chain verifies the same way.
- REST API surface: identical endpoints, identical wire shapes.
- MCP tool surface: **disabled** in Hestia mode (MCP still loads keypair directly; signer integration arrives in V2-7 Step 4).
- Sync CLI acts (`hub add-member`, etc.): refuse with a clear error pointing operators to REST.

## What's different

| Aspect | Local mode | Hestia mode |
|---|---|---|
| Sovereign keypair | In hub process | In Hestia vault only |
| `[sovereign]` config | `lct_path = "..."` | `hestia_callback_url`, `lct_id`, `pubkey_hex` |
| Genesis signing | Hub signs in-process | Hub posts to Hestia callback (TODO: ergonomic init CLI) |
| REST event signing | Hub signs in-process | Hub posts to Hestia callback per event |
| MCP server | Enabled | Disabled (sub the REST API) |
| Sync CLI acts | Enabled | Disabled (use REST API) |
| verify-ledger | Loads IdentityFile | Uses pubkey from config |

## Configuration

```toml
# config.toml — Hestia mode
[chapter]
name = "Your Chapter"

[daemon]
mcp_port = 8770

[sovereign]
hestia_callback_url = "http://127.0.0.1:9001/sign-request"
lct_id = "<sovereign-uuid>"
pubkey_hex = "<32-byte hex>"
```

Local-mode chapters keep their `[sovereign] lct_path = "..."` shape; backward-compat is preserved.

## Wire shape

Per agreement with Legion's Hestia (`hestia@253c611`):

**Hub → Hestia** `POST {callback_url}` (typically ends with `/sign-request`):
```json
{
  "intent": {
    "request_id": "uuid",
    "hub_id": "uuid",
    "hub_name": "string",
    "actor_lct_id": "uuid",
    "ledger_index": 5,
    "event_kind": "member_added",
    "event": { ... }
  },
  "signing_bytes_hex": "hex-encoded bytes to sign"
}
```

**Hestia → Hub** (one of):
```json
// Approved
{ "request_id": "uuid", "signature": "hex-64-bytes" }

// Denied
{ "request_id": "uuid", "denied": true, "deny_reason": "string" }
```

Hestia is the policy point. Authority + need-to-know decisions live in the vault, not in the hub.

## Testing with mock-hestia

A reference implementation lives at `hub-daemon/examples/mock_hestia.rs`. Build + run:

```bash
cargo build --release --example mock-hestia
./target/release/examples/mock-hestia --identity sov.json --port 9001
```

It loads an `IdentityFile`, listens on `/sign-request`, and signs every request (no policy gating). `--deny-all "<reason>"` flips it to deny mode for testing the denial path.

## End-to-end smoke

```bash
# 1. Generate a Sovereign identity (this becomes the keypair Hestia holds)
hub gen-lct sov.json

# 2. Start mock-Hestia with that identity
cargo build --release --example mock-hestia
./target/release/examples/mock-hestia --identity sov.json --port 9001

# 3. In another terminal, init the chapter in Hestia mode
SOV_ID=$(python3 -c "import json; print(json.load(open('sov.json'))['lct']['id'])")
SOV_PUBKEY=$(python3 -c "import json; print(json.load(open('sov.json'))['lct']['public_key']['key'])")

hub init "My Chapter" \
  --sovereign-hestia http://127.0.0.1:9001/sign-request \
  --sovereign-lct-id "$SOV_ID" \
  --sovereign-pubkey "$SOV_PUBKEY" \
  --hub-dir ./my-chapter

# Hub builds the unsigned Genesis, POSTs to mock-Hestia, gets back the
# signature, commits. mock-Hestia logs the request. The hub binary's
# process memory never contained the private key.

# 4. Verify
hub verify-ledger ./my-chapter        # → passes (using pubkey from config)
ls ./my-chapter                       # → charter.json, society.json, ledger.jsonl, config.toml
                                      #   (no IdentityFile copied or needed)

# 5. Serve + drive a REST event
hub serve ./my-chapter --port 8770    # → "MCP tools: (disabled — Hestia-mode chapter)"
                                      # → REST: every event signed via the Hestia callback
```

After init, the hub process at no point sees the private key. The chain still verifies because the pubkey is in `config.toml`.

## What's still ahead (V2-7 §4)

- **MCP signer integration**: MCP tools currently refuse to open Hestia-mode chapters with a clear error pointing to REST. Once MCP routes through the signer abstraction (same shape as REST does today), MCP tools work on Hestia chapters too.
- **Sync CLI acts on Hestia chapters**: design TBD — sync CLI on async-signing wants either an async-CLI variant or block_on'd internal client.

## See also

- `V2-V3-ARCHITECTURE.md` §Load-bearing commitment #8 (secrets-in-vault posture)
- `hub-lib/src/signer.rs` (RemoteSigner trait + impls)
- `hub-lib/src/envelope.rs` (SignedEnvelope wire shape)
- `hub-daemon/src/rest.rs` (REST handler routing through signer abstraction)
- `hestia@253c611` (Legion's H2/H3 — the production Hestia side)
- `shared-context/forum/cbp-to-legion-hub-api-spec-for-h2-h3-2026-06-07.md` (canonical wire spec)
