# Storage Backends

**Status:** V2-2 shipped (`file` + `sqlite`, operator-selectable). The `dynamodb` backend is
**implemented** (`hub_lib::dynamodb_store`) but not yet CLI-wired — see the [`dynamodb`](#dynamodb-v2-sprint2-opt-in-via-dynamodb-feature) section. All three carry the durable per-pair message sidecar (`append_pair_message` / `list_pair_messages`). Postgres is V2-15.

The hub stores chapter state — charter, society, ledger, pinned member keys, pairings, and per-pair messages — behind a `HubStore` trait. Operators choose the backend at `hub init` time, and `hub migrate` moves an existing chapter between backends without re-signing anything.

---

## Posture: secrets-free AND encrypted-at-rest

The storage layer NEVER holds secrets. Private keys, vault contents, API credentials — none of these belong here. They live in Hestia's vault and are accessed under the vault's authority + need-to-know gate. That part is unchanged and constitutional.

What *is* in the store — the member roster, pinned member pubkeys, pairings, profiles, the ledger — is confidential even though it isn't a signing key. So the `sqlite` backend is now **encrypted at rest** (SQLCipher) under a key derived from the same vault passphrase that guards the identity. Storage is therefore signed (for integrity), access-gated (authority + need-to-know), *and* encrypted (for confidentiality of the bytes on disk). The on-disk `hub.db` is ciphertext; opening it requires the vault passphrase. See [§At-rest encryption model](#at-rest-encryption-model) below.

This closes the gap where a sealed hub protected its key but everything it *knew* sat in world-readable plaintext next to the encrypted identity. The secrets-free invariant (no private keys in the store) still holds. This is constitutional. See `V2-V3-ARCHITECTURE.md` §Load-bearing commitment #8.

---

## At-rest encryption model

Applies to the `sqlite` backend (the `file` backend is plaintext on disk; pair it with an encrypted volume / TPM-sealed dir for confidentiality).

**Key derivation.** The SQLCipher key is derived from the vault passphrase with **Argon2id**, salted per-hub. The salt lives clear (salts aren't secret) at `<hub-dir>/.store-salt`, generated once on first use. Same passphrase + same salt → same 32-byte key.

**De-env'd, held in memory.** The passphrase is **not read from the environment at runtime**. After ignition the daemon derives the key once and holds it in memory, then re-opens the store via `open_hub_store_with_key(hub_dir, Some(key))`. The key is applied to each connection with `PRAGMA key` before any other access. (`derive_store_key` is the explicit-passphrase entry point used at ignition.)

**Ignition / locked-shell boot (fail-closed).** On `hub serve`, the daemon tries to open the store with whatever key is available — which is *none*, since no passphrase sits on disk or in env. If the store opens (plaintext / NULL-keyed / fresh hub), it boots normally. If it fails closed (encrypted, no key), it boots a **LOCKED SHELL** that serves only the unlock path; `hub unlock` ignites it at runtime, deriving the key and swapping in the real store in memory. An encrypted DB with no key never opens silently and is never corrupted — it fails closed.

**Plaintext → encrypted in-place migration.** A legacy plaintext `hub.db` is upgraded to ciphertext on its first keyed open: the WAL is checkpointed, `sqlcipher_export` copies the full schema + data into a freshly-keyed copy, and that copy atomically replaces the original (stale plaintext WAL/SHM sidecars are cleared). All rows and ledger order are preserved; the operation is crash-safe (it writes a temp file then renames).

**Rekey via `rotate-passphrase`.** `hub rotate-passphrase <hub-dir>` re-keys the state DB in place: it opens with the current key, verifies it decrypts, then `PRAGMA rekey`s to the new key (and re-seeds the protected vault tier under the new phrase). It's interactive (console only) and aborts without changing anything if the current passphrase doesn't decrypt. Restart the hub afterward — it boots locked and is ignited with `hub unlock` using the new phrase.

**Ledger included.** The ledger lives in the same encrypted DB, so it is encrypted at rest too. Integrity still comes from the signed hash-chain; encryption at rest is an added confidentiality layer, not a replacement for signatures.

---

## Backends

### `file` (default, MVP-compatible)

```
<chapter-dir>/
├── config.toml          # operator config — outside the storage abstraction
├── charter.json         # charter (immutable post-genesis)
├── society.json         # society state
└── ledger.jsonl         # one signed HubEvent per line, hash-chained
```

Best for:
- Single-machine operators
- Small chapters (≤ a few thousand members)
- Easy filesystem-level inspection / backup
- The MVP layout — existing chapters are file-backed by default

Trade-offs:
- Append-only ledger is robust but does full-file rewrites on JSON state changes
- No transactional guarantees across multiple files
- Ledger query performance is O(file size) for full scans

### `sqlite` (V2-2)

```
<chapter-dir>/
├── config.toml          # operator config
├── .store-salt          # per-hub salt for the SQLCipher key derivation
├── hub.db               # SQLite database — all chapter state (SQLCipher-encrypted at rest)
├── hub.db-wal           # SQLite WAL (transient)
└── hub.db-shm           # SQLite shared-memory (transient)
```

(Hub dirs created before the chapter→hub rename hold a legacy `chapter.db`; it is read in place as a fallback — no forced rename. New stores are always `hub.db`.)

Schema:
```sql
CREATE TABLE metadata (
    key   TEXT PRIMARY KEY,   -- "charter" | "society" | "law"
    value TEXT NOT NULL        -- canonical JSON (or law YAML)
);

CREATE TABLE ledger_entries (
    idx        INTEGER PRIMARY KEY,  -- append-only via PRIMARY KEY constraint
    entry_json TEXT NOT NULL         -- full LedgerEntry as canonical JSON
);
```

Encryption: when a key is available, the connection is **SQLCipher-keyed** via `PRAGMA key` *before any other access* (and a legacy plaintext DB is migrated to ciphertext in place on first keyed open). With no key, a plaintext/fresh DB opens as-is but an already-encrypted DB fails closed. See [§At-rest encryption model](#at-rest-encryption-model).

Pragmas (set after keying): `foreign_keys=ON`, `journal_mode=WAL`, `synchronous=NORMAL`.

Best for:
- Single-machine operators who want a single-file artifact
- Faster ledger queries (indexed by `idx`)
- Transactional charter / society writes
- Operators wanting cleaner filesystem layout

Trade-offs:
- Less human-inspectable than JSON files (need `sqlite3 hub.db` — and a plain `sqlite3` build **can't open the encrypted DB at all** without the SQLCipher key; you'd open it with a SQLCipher-enabled build and `PRAGMA key`)
- One file holds everything → backup strategy concentrates on one artifact

### `dynamodb` (V2-Sprint2, opt-in via `dynamodb` feature)

AWS DynamoDB single-table backend. Operator picks a table name; many chapters share it, partitioned by `PK = HUB#<hub_id>`. Implements the same `HubStore` trait. Build with `--features dynamodb` to compile in the AWS SDK dep; default build stays slim.

Schema (single-table-design):

| PK              | SK                 | item                  |
|-----------------|--------------------|-----------------------|
| `HUB#<hub_id>`  | `CHARTER`          | charter JSON          |
| `HUB#<hub_id>`  | `SOCIETY`          | society JSON          |
| `HUB#<hub_id>`  | `LAW`              | law YAML              |
| `HUB#<hub_id>`  | `LEDGER#<idx20>`   | ledger entry JSON     |
| `HUB#<hub_id>`  | `PROPOSAL#<uuid>`  | council proposal JSON |

`<idx20>` is the 20-digit zero-padded entry index so DynamoDB's lexicographic Sort Key ordering matches numeric ledger order through u64::MAX.

**Atomic append.** `PutItem` with `ConditionExpression: attribute_not_exists(SK)` is the primitive — equivalent to sqlite's `INTEGER PRIMARY KEY` constraint. Concurrent appenders racing at the same index → exactly one commits, the other gets `ConditionalCheckFailedException` and propagates as the existing "ledger advanced between build_entry and append_signed" stale-detection.

**Wiring status.** The backend implementation is shipped (`hub_lib::dynamodb_store::DynamoDbBackend`). CLI integration for `hub init --storage dynamodb` and `hub serve` against a dynamodb-backed chapter is **not yet** wired — `open_hub_store_with(dir, BackendKind::Dynamodb)` returns an error pointing operators at the Rust API. Wiring needs a `[storage]` block in `config.toml` to record table name + hub_id (so future `hub serve` can dispatch). That's a follow-up sprint.

**Testing.** No in-process tests (AWS SDK doesn't have a clean offline mode). Manual smoke against DynamoDB Local:

```bash
# Download DynamoDB Local once (one-time setup)
wget https://s3.us-west-2.amazonaws.com/dynamodb-local/dynamodb_local_latest.zip
unzip dynamodb_local_latest.zip -d ./ddb-local

# Run the smoke
bash web4/hub/examples/dynamodb_local_smoke.sh
```

The smoke exercises charter/society/law round-trips, ledger append+load+atomicity, and proposal CRUD. The CI build verifies the code compiles with `--features dynamodb`.

### `postgres` (planned)

For multi-chapter / multi-tenant SQL deployments. Schema-per-chapter (default), one Postgres deployment hosting many chapters. Implements the same `HubStore` trait.

### `s3-cold` (later)

Archive tier for old ledger pages. Not in V2; will land if/when needed.

---

## Choosing a backend at init

```bash
# Default (file-backed, MVP-compatible)
hub init "Lisbon" --sovereign-lct sov.json

# SQLite-backed
hub init "Lisbon" --sovereign-lct sov.json --storage sqlite
```

The `--storage` flag accepts: `file` (aliases: `files`, `jsonl`) and `sqlite` (aliases: `sqlite3`, `db`). `dynamodb` (aliases: `dynamo`, `ddb`) parses but errors at store-open time — it can't be constructed from a hub dir alone (see the dynamodb section). Anything else is rejected.

---

## Migration

```bash
hub migrate <chapter-dir> --to <file|sqlite>
```

What it does:

1. Auto-detects the source backend (`hub.db` — or legacy `chapter.db` — present → sqlite; else → file).
2. If source == target, no-op.
3. Opens the target backend (creates `hub.db` for sqlite; if a passphrase is set, the new sqlite DB is SQLCipher-encrypted).
4. Copies charter, society, and every ledger entry **byte-for-byte**. No re-signing, no chain rebuild — the migrated chapter's `head_hash` is identical to the source's.
5. Renames source artifacts to `.pre-migration` suffixes so they remain recoverable for rollback but don't interfere with auto-detection on future opens.
6. Runs `verify-ledger` end-to-end on the migrated chapter. Errors loudly if anything failed.

Example output:
```
$ hub migrate ./lisbon --to sqlite
Migrating ./lisbon → sqlite
  Source backend:  file
  Target backend:  sqlite
  Charter copied:  true
  Society copied:  true
  Ledger entries:  42
  Preserved (rollback-recoverable):
    ./lisbon/charter.json.pre-migration
    ./lisbon/society.json.pre-migration
    ./lisbon/ledger.jsonl.pre-migration

Verifying migrated chapter end-to-end ...
Ledger verified on sqlite backend.
  Entries:        42
  Head hash:      219ef70be31bb74eeeb180ca524161285273b5c3279c171bb53f41bc89176a97
```

The `head_hash` after migration matches the source's head_hash. That equality is the canonical proof the chain is intact.

### Rollback

If you decide to roll back:
1. Stop any running `hub serve` for this chapter.
2. Delete `hub.db` (and any `.db-wal` / `.db-shm` files).
3. Rename `.pre-migration` files back to their originals (strip the suffix).
4. Run `hub verify-ledger <chapter-dir>` to confirm.

### When to remove the `.pre-migration` backups

Operator discretion. Some patterns:
- Keep them for one full chapter cycle to ensure no edge cases surface.
- Remove them after a backup of `hub.db` is taken.
- Long-term retention is harmless except for disk-space pressure.

---

## What's outside the storage abstraction

- **`config.toml`** — operator-owned config (chapter name, MCP port, Sovereign LCT pointer). File-based by design, not part of `HubStore`.
- **Sovereign identity file** — MVP convention; deprecates with V2-7 (Hestia-as-Sovereign). Per commitment #8, secrets belong in the vault, not in files the hub reads.
- **Anything in vault scope** — by definition not in chapter storage.

---

## Extending: adding a new backend

Implement the `HubStore` trait. It is an **`#[async_trait]`** trait (`Send + Sync`); every method is `async` so the trait composes with network-backed backends that do real I/O, while in-process backends (`file`, `sqlite`) just complete synchronously inside the async body. Several methods have defaults (law, council proposals, pair messages) so a minimal backend only has to implement charter/society/ledger:

```rust
#[async_trait::async_trait]
pub trait HubStore: Send + Sync {
    fn backend_kind(&self) -> BackendKind;

    // Charter (immutable post-genesis)
    async fn read_charter(&self) -> Result<Option<Charter>>;
    async fn write_charter(&mut self, charter: &Charter) -> Result<()>;

    // Society state
    async fn read_society(&self) -> Result<Option<Society>>;
    async fn write_society(&mut self, society: &Society) -> Result<()>;

    // Ledger (append-only, hash-chained)
    async fn ledger_load_all(&self) -> Result<Vec<LedgerEntry>>;
    async fn ledger_append(&mut self, entry: &LedgerEntry) -> Result<()>;
    async fn ledger_is_empty(&self) -> Result<bool> { /* default: load_all */ }

    // Law (signed YAML; default impls return None / bail)
    async fn read_law(&self) -> Result<Option<String>> { /* default */ }
    async fn write_law(&mut self, yaml: &str) -> Result<()> { /* default */ }

    // Council proposals (default impls bail "unsupported")
    async fn write_proposal(&mut self, p: &CouncilProposal) -> Result<()> { /* default */ }
    async fn read_proposal(&self, id: Uuid) -> Result<Option<CouncilProposal>> { /* default */ }
    async fn list_proposals(&self) -> Result<Vec<CouncilProposal>> { /* default */ }
    async fn delete_proposal(&mut self, id: Uuid) -> Result<()> { /* default */ }

    // Pair messages (default impls bail "unsupported")
    async fn append_pair_message(&mut self, msg: &PairMessage) -> Result<()> { /* default */ }
    async fn list_pair_messages(&self, pair_id: Uuid, since_seq: Option<u64>)
        -> Result<Vec<PairMessage>> { /* default */ }
}
```

Wire into `BackendKind` enum + `BackendKind::FromStr` parser + `open_hub_store_with` factory + the migration tool's `preserved_artifacts` step (so source-side cleanup knows what to rename).

Don't add secret-handling operations to the trait. Don't add anything that requires the trait to learn about chapter-specific business logic. The trait is bytes-in / bytes-out for chapter state; everything else (validation, signing, authorization) is the layers above.

---

## See also

- `BACKEND-OPTIONS.md` — design exploration of the wider backend space
  (DynamoDB, Postgres, S3, edge-SQL, distributed consensus) + the
  (now-resolved) async-trait decision behind the network-backed backends
- `V2-V3-ARCHITECTURE.md` §Load-bearing commitment #8 (secrets posture)
- `hub-lib/src/store.rs` (trait + backends)
- `hub-lib/src/ledger.rs` (uses `HubStore` for persistence; owns chain integrity)
