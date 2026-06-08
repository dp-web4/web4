# Storage Backends

**Status:** V2-2 shipped (file + sqlite). Postgres is V2-15.

The hub stores chapter state — charter, society, ledger — behind a `HubStore` trait. Two backends ship today; more are planned. Operators choose at `hub init` time, and `hub migrate` moves an existing chapter between backends without re-signing anything.

---

## Posture: secrets-free by design

The storage layer NEVER holds secrets. Private keys, vault contents, API credentials — none of these belong here. They live in Hestia's vault and are accessed under the vault's authority + need-to-know gate. Chapter storage is signed (for integrity) but not encrypted (for confidentiality of the data itself). If something in the chapter must be confidential, that's a vault-side concern, not a storage-side concern.

This is constitutional. See `V2-V3-ARCHITECTURE.md` §Load-bearing commitment #8.

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
├── chapter.db           # SQLite database — all chapter state
├── chapter.db-wal       # SQLite WAL (transient)
└── chapter.db-shm       # SQLite shared-memory (transient)
```

Schema:
```sql
CREATE TABLE metadata (
    key   TEXT PRIMARY KEY,   -- "charter" | "society"
    value TEXT NOT NULL        -- canonical JSON
);

CREATE TABLE ledger_entries (
    idx        INTEGER PRIMARY KEY,  -- append-only via PRIMARY KEY constraint
    entry_json TEXT NOT NULL         -- full LedgerEntry as canonical JSON
);
```

Pragmas: `foreign_keys=ON`, `journal_mode=WAL`, `synchronous=NORMAL`.

Best for:
- Single-machine operators who want a single-file artifact
- Faster ledger queries (indexed by `idx`)
- Transactional charter / society writes
- Operators wanting cleaner filesystem layout

Trade-offs:
- Less human-inspectable than JSON files (need `sqlite3 chapter.db`)
- One file holds everything → backup strategy concentrates on one artifact

### `postgres` (V2-15, planned)

For multi-chapter / multi-tenant deployments. Schema-per-chapter (default), one Postgres deployment hosting thousands of chapters. Implements the same `HubStore` trait.

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

The `--storage` flag accepts: `file`, `sqlite` (aliases: `files`, `jsonl`, `sqlite3`, `db`).

---

## Migration

```bash
hub migrate <chapter-dir> --to <file|sqlite>
```

What it does:

1. Auto-detects the source backend (`chapter.db` present → sqlite; else → file).
2. If source == target, no-op.
3. Opens the target backend (creates `chapter.db` for sqlite).
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
2. Delete `chapter.db` (and any `.db-wal` / `.db-shm` files).
3. Rename `.pre-migration` files back to their originals (strip the suffix).
4. Run `hub verify-ledger <chapter-dir>` to confirm.

### When to remove the `.pre-migration` backups

Operator discretion. Some patterns:
- Keep them for one full chapter cycle to ensure no edge cases surface.
- Remove them after a backup of `chapter.db` is taken.
- Long-term retention is harmless except for disk-space pressure.

---

## What's outside the storage abstraction

- **`config.toml`** — operator-owned config (chapter name, MCP port, Sovereign LCT pointer). File-based by design, not part of `HubStore`.
- **Sovereign identity file** — MVP convention; deprecates with V2-7 (Hestia-as-Sovereign). Per commitment #8, secrets belong in the vault, not in files the hub reads.
- **Anything in vault scope** — by definition not in chapter storage.

---

## Extending: adding a new backend

Implement the `HubStore` trait:

```rust
pub trait HubStore: Send {
    fn backend_kind(&self) -> BackendKind;
    fn read_charter(&self) -> Result<Option<Charter>>;
    fn write_charter(&mut self, charter: &Charter) -> Result<()>;
    fn read_society(&self) -> Result<Option<Society>>;
    fn write_society(&mut self, society: &Society) -> Result<()>;
    fn ledger_load_all(&self) -> Result<Vec<LedgerEntry>>;
    fn ledger_append(&mut self, entry: &LedgerEntry) -> Result<()>;
    fn ledger_is_empty(&self) -> Result<bool> { /* default */ }
}
```

Wire into `BackendKind` enum + `BackendKind::FromStr` parser + `open_chapter_store_with` factory + the migration tool's `preserved_artifacts` step (so source-side cleanup knows what to rename).

Don't add secret-handling operations to the trait. Don't add anything that requires the trait to learn about chapter-specific business logic. The trait is bytes-in / bytes-out for chapter state; everything else (validation, signing, authorization) is the layers above.

---

## See also

- `V2-V3-ARCHITECTURE.md` §Load-bearing commitment #8 (secrets posture)
- `hub-lib/src/store.rs` (trait + backends)
- `hub-lib/src/ledger.rs` (uses `HubStore` for persistence; owns chain integrity)
