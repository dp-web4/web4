# Hestia Mode

**Status:** V2-7 Step 3b — landed end-to-end. Production wire is the same; only the bootstrap CLI ergonomics (`hub init --sovereign-hestia`) is follow-up work.

In Hestia mode, the hub holds **NO Sovereign keypair**. Every signature attributed to the Sovereign is produced by a remote signer (Hestia) that the hub calls over HTTP. This honors architecture commitment #8 (secrets in vault only) on the hub side.

## Why this matters

The MVP convention — operator's IdentityFile sitting on disk, hub loads it at `serve` time, hub keeps the keypair in process — is convenient but conflicts with commitment #8. A compromised hub process = compromised Sovereign keys. Hestia mode moves the keypair into the operator's Hestia vault; the hub only ever sees a public key (to verify) and signatures Hestia returns. Compromising the hub no longer compromises the Sovereign.

## What's the same

- Chapter storage (`charter.json` / `society.json` / `chapter.db`): identical layout.
- Ledger entries: identical schema. The signature in each entry is now Hestia-produced rather than hub-produced; the chain verifies the same way.
- REST API surface: identical endpoints, identical wire shapes.
- MCP tool surface: **disabled** in Hestia mode (MCP still loads keypair directly; signer integration arrives in V2-7 Step 4).
- Sync CLI mutations (`hub add-member`, etc.): refuse with a clear error pointing operators to REST.

## What's different

| Aspect | Local mode | Hestia mode |
|---|---|---|
| Sovereign keypair | In hub process | In Hestia vault only |
| `[sovereign]` config | `lct_path = "..."` | `hestia_callback_url`, `lct_id`, `pubkey_hex` |
| Genesis signing | Hub signs in-process | Hub posts to Hestia callback (TODO: ergonomic init CLI) |
| REST event signing | Hub signs in-process | Hub posts to Hestia callback per event |
| MCP server | Enabled | Disabled (sub the REST API) |
| Sync CLI mutations | Enabled | Disabled (use REST API) |
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
    "chapter_id": "uuid",
    "chapter_name": "string",
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

## Today's manual smoke

Until `hub init --sovereign-hestia` lands:

1. `hub gen-lct sov.json` (generates IdentityFile)
2. `hub init "Chapter Name" --sovereign-lct sov.json` (creates Local-mode chapter so Genesis is signed by the to-be-Hestia identity)
3. `./target/release/examples/mock-hestia --identity sov.json --port 9001` (load the same identity into mock-Hestia)
4. Manually rewrite `chapter-name/config.toml` to Hestia mode (see "Configuration" above; remove `lct_path`)
5. `hub serve chapter-name/` (REST-only; "MCP tools: (disabled — Hestia-mode chapter)")
6. Drive REST events as usual; every ledger entry is signed by mock-Hestia

After step 4, the hub process never sees the private key again, but the chain still verifies because the pubkey is in the config.

## What's still ahead

- **`hub init --sovereign-hestia <url> --sovereign-lct-id <id> --sovereign-pubkey <hex>`**: ergonomic init that does the Hestia-callback Genesis sign automatically (no manual config rewrite).
- **V2-7 Step 4**: MCP signer integration so MCP tools work on Hestia chapters too.
- **Sync CLI mutations on Hestia chapters**: design TBD — sync CLI on async-signing seems wrong; consider async-CLI variant.

## See also

- `V2-V3-ARCHITECTURE.md` §Load-bearing commitment #8 (secrets-in-vault posture)
- `hub-lib/src/signer.rs` (RemoteSigner trait + impls)
- `hub-lib/src/envelope.rs` (SignedEnvelope wire shape)
- `hub-daemon/src/rest.rs` (REST handler routing through signer abstraction)
- `hestia@253c611` (Legion's H2/H3 — the production Hestia side)
- `shared-context/forum/cbp-to-legion-hub-api-spec-for-h2-h3-2026-06-07.md` (canonical wire spec)
