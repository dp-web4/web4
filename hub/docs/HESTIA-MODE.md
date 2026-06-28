# Hestia Mode

**Status:** Landed end-to-end, including the ergonomic `hub init --sovereign-hestia` CLI. Hestia mode is now one `SignerKind` under the broader **SwappableSigner** model (below). Hub binary holds NO Sovereign keypair during init or serve in this mode.

## The signer abstraction (the real model)

The hub does not have a binary "Local vs Hestia" personality. Every signature
flows through **one `SwappableSigner`** (`hub-lib/src/signer.rs`) that wraps a
`RemoteSigner` whose `SignerKind` is one of:

- **`LocalKeypair`** — `LocalKeypairSigner`, signs in-process from a keypair the hub holds.
- **`HestiaCallback`** — `HestiaCallbackSigner`, POSTs a sign-request to the operator's Hestia vault over HTTP; the hub only ever sees a public key (to verify) and signatures Hestia returns. *This is "Hestia mode."*
- **`Locked`** — `LockedSigner`, fail-closed: every key op is denied. The hub still runs (serves tier-0 reads, accepts unlock) but cannot sign until ignited.

Because the seam is `s.signer.sign(..)` everywhere, the backing signer can be
**swapped at runtime** (`SwappableSigner::swap`) with no restart and no change
at any call site. This is what makes the locked-shell → ignited transition (§
*Locked shell + ignition*) possible.

In **Hestia mode**, the hub holds **NO Sovereign keypair**: the installed signer
is `HestiaCallback`, and every Sovereign signature is produced remotely. This
honors architecture commitment #8 (secrets in vault only) on the hub side.

## Why this matters

The MVP convention — operator's IdentityFile sitting on disk, hub loads it at `serve` time, hub keeps the keypair in process — is convenient but conflicts with commitment #8. A compromised hub process = compromised Sovereign keys. Hestia mode moves the keypair into the operator's Hestia vault; the hub only ever sees a public key (to verify) and signatures Hestia returns. Compromising the hub no longer compromises the Sovereign. The `Locked` kind goes further still: a hub can boot with *no* usable key at all and be ignited in place.

## What's the same

- Chapter storage (`charter.json` / `society.json` / `chapter.db`): identical layout.
- Ledger entries: identical schema. The signature in each entry is now Hestia-produced rather than hub-produced; the chain verifies the same way.
- REST API surface: identical endpoints, identical wire shapes.
- MCP / plugin tool surface: routes through the signer abstraction. `PluginCtx::sign` signs as the hub LCT whether the hub holds the key (Local) or signs via a remote callback (Hestia) — it is **not** disabled in Hestia mode.
- Sync CLI acts (`hub add-member`, etc.): refuse with a clear error pointing operators to REST.

## What's different

| Aspect | Local mode | Hestia mode |
|---|---|---|
| Sovereign keypair | In hub process | In Hestia vault only |
| `[sovereign]` config | `lct_path = "..."` | `hestia_callback_url`, `lct_id`, `pubkey_hex` |
| Genesis signing | Hub signs in-process | Hub posts to Hestia callback (via `hub init --sovereign-hestia`) |
| REST event signing | Hub signs in-process | Hub posts to Hestia callback per event |
| MCP server | Enabled | Enabled (plugin `sign` routes through the signer → Hestia callback) |
| Sync CLI acts | Enabled | Disabled (use REST API) |
| verify-ledger | Loads IdentityFile for the pubkey | Uses pubkey from config |

> **Note (encrypted-at-rest):** the identity-resolution column above is only
> half the story. `verify-ledger` opens the hub's state store, and on a hub
> whose store is encrypted at rest it must derive the SQLCipher key from the
> vault passphrase (`HUB_PASSPHRASE` / TTY prompt) to open it — fail-closed
> otherwise. On such a hub `verify-ledger` cannot run unattended without the
> passphrase, in either signing mode.

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
hub serve ./my-chapter --port 8770    # → MCP tools enabled; plugin `sign` routes through the signer
                                      # → REST + MCP: every event signed via the Hestia callback
```

After init, the hub process at no point sees the private key. The chain still verifies because the pubkey is in `config.toml`.

## What's still ahead

- **Sync CLI acts on Hestia chapters**: design TBD — sync CLI on async-signing wants either an async-CLI variant or block_on'd internal client.

*(Done since this doc was first written: **MCP signer integration** — MCP/plugin tools now route through the signer abstraction (`PluginCtx::sign`), the same shape REST uses, so they work on Hestia chapters too.)*

## Locked shell + ignition (runtime model)

A hub whose state is encrypted at rest boots **unlock-first**. On `serve` the
daemon tries to open the encrypted store with whatever key is available — and
keeps **no passphrase on disk or in env**, by doctrine. If the store opens
(plaintext / NULL-keyed / fresh hub) it boots normally. If it fails closed
(encrypted, no key), the hub starts in a **locked shell**: it installs a
`LockedSigner`, serves only tier-0 reads (e.g. `GET /v1/hubs/:id/law`), and
refuses to sign or open channels — every key op denied, fail-closed.

The hub is then **ignited in place** (no restart) by presenting the passphrase
to an unlock slot, which derives the key, opens the store, and
`SwappableSigner::swap`s the real `LocalKeypairSigner` in for the
`LockedSigner`. Unlock slots:

- `POST /v1/hubs/:id/unlock` — tier-1 stub-console / passphrase unlock; local-only + rate-limited.
- `POST /v1/hubs/:id/unlock/challenge` + `POST /v1/hubs/:id/unlock/attest` — tier-2 M-of-N witnessed unlock: the hub mints a challenge, admins attest, a private verifier plugin judges the quorum (501 when no verifier is configured).

## Encrypted-at-rest identity + its CLI

The Sovereign identity is stored encrypted (the vault doctrine: a private key is
never written in the clear; "no passphrase" must be an explicit NULL choice,
never a silent default). Supporting CLI:

- `hub seal-identity <path>` — migrate a plaintext IdentityFile to an encrypted vault in place (re-writes encrypted under the resolved passphrase; an already-encrypted file is re-keyed).
- `hub rotate-passphrase <hub-dir>` — rotate the vault passphrase to an operator-chosen (memorable) one; re-keys both the identity and the SQLCipher state store. Interactive (run at a console).
- `hub export-public-identity <hub-dir>` — export just the public identity (seeds the pubkey-only material a peer / resolver needs, without the private key).

Passphrase resolution is fail-closed everywhere: `HUB_PASSPHRASE` env (set,
including empty = a deliberate NULL) → interactive TTY prompt → error. There is
no silent "use plaintext" outcome.

## EUDI: the hub as credential issuer + verifier

At society scale the hub speaks **EUDI** wallet protocols, and this is the most
prominent consumer of the `RemoteSigner` abstraction:

- **OID4VCI (issuer).** The hub issues `Web4Membership` **SD-JWT-VC** credentials to its own members, signing the credential through its `RemoteSigner` — so issuance works whether the hub holds the key (Local) or signs via the Hestia callback (it may hold no keys in process at all). Routes: `GET /v1/hubs/:id/.well-known/openid-credential-issuer` (issuer metadata), `POST /v1/hubs/:id/nonce`, `POST /v1/hubs/:id/credential`. The holder-key proof in the credential request — which must be a pinned member key — is the auth (credential issuance is a direct wallet pull, not a sealed-channel tool).
- **OID4VP (verifier / relying party).** The hub verifies presentations: `POST /v1/hubs/:id/vp/request`, `POST /v1/hubs/:id/vp/response`. `web4-core::oid4vc` / `sd_jwt_vc` do the heavy lifting; the REST handlers are thin wrappers.

## See also

- `V2-V3-ARCHITECTURE.md` §Load-bearing commitment #8 (secrets-in-vault posture)
- `hub-lib/src/signer.rs` (RemoteSigner trait + impls)
- `hub-lib/src/envelope.rs` (SignedEnvelope wire shape)
- `hub-daemon/src/rest.rs` (REST handler routing through signer abstraction)
- `hestia@253c611` (Legion's H2/H3 — the production Hestia side)
- `shared-context/forum/cbp-to-legion-hub-api-spec-for-h2-h3-2026-06-07.md` (canonical wire spec)
