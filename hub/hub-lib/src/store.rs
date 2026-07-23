// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Hub storage backend abstraction (V2-2).
//!
//! ## Why this exists
//!
//! The MVP stored chapter state as JSON/JSONL files in a directory. That
//! shipped; it works; it does not scale. V2 wants chapters to be hostable
//! across deployment targets — single-file SQLite for one-machine
//! operators, Postgres for multi-tenant cloud deployments, S3-cold archives
//! for old ledger pages. Different chapters, same hub code path, different
//! backend bytes.
//!
//! The abstraction here is intentionally narrow: hub charter, chapter
//! society state, and the hub event ledger. That is the entire surface
//! of hub-owned persistent state. Everything else is either:
//!
//! - **Operator-owned config** (`config.toml`) — stays file-based, not part of this trait
//! - **Secret material** (private keys, vault contents) — per architecture
//!   commitment #8, secrets live ONLY in Hestia's vault, never in chapter
//!   storage. The trait surface explicitly does not expose any secret-
//!   handling operations.
//!
//! ## Posture (per architecture commitment #8)
//!
//! Hub storage holds **no signing keys** — those live only in the identity
//! vault (commitment #8). But the state it *does* hold (member roster, pinned
//! member pubkeys, pairings, profiles, the ledger) is confidential, so the
//! SQLite backend is **encrypted at rest** (SQLCipher) under a key derived from
//! the same vault passphrase (`HUB_PASSPHRASE`). A sealed hub thus protects not
//! just its key but everything it knows — closing the gap where `hub.db` sat in
//! world-readable plaintext next to the encrypted identity. Legacy plaintext
//! DBs migrate in place on first open with a passphrase; with no passphrase a
//! plaintext DB still opens (legacy/NULL) but an encrypted one fails closed.
//! Integrity still comes from the signed hash-chain; access control still comes
//! from the authority+need-to-know gate. Encryption at rest is the third layer.
//!
//! ## Backends
//!
//! - [`FileBackend`] — wraps the MVP's JSON/JSONL files. Default for V2-2.
//! - `SqliteBackend` — single-file SQLite per chapter. Lands in V2-2 Step B.
//! - `PostgresBackend` — multi-chapter, multi-tenant. Lands in V2-15 (B6).
//!
//! ## Migration
//!
//! A `hub migrate` command (V2-2 Step C) walks one backend reading and
//! pushes into another backend, verifying the ledger hash chain matches
//! end-to-end. MVP chapters running on FileBackend can migrate to
//! SqliteBackend without re-signing any entry.

use anyhow::{Context, Result};
use std::path::{Path, PathBuf};

use crate::hub::HubPaths;
use crate::charter::Charter;
use crate::ledger::LedgerEntry;
use web4_core::society::Society;

/// What kind of backend a [`HubStore`] is. Useful for diagnostics +
/// migration tools that need to choose paths based on backend identity.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BackendKind {
    /// JSON/JSONL files on disk (MVP-compatible).
    File,
    /// Single-file SQLite per chapter (V2-2 Step B).
    Sqlite,
    /// AWS DynamoDB single-table design (Sprint 2, gated on `dynamodb` feature).
    /// PK = `HUB#<hub_id>`, SK ∈ {CHARTER, SOCIETY, LAW, LEDGER#<idx>, PROPOSAL#<uuid>}.
    Dynamodb,
}

impl BackendKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            BackendKind::File => "file",
            BackendKind::Sqlite => "sqlite",
            BackendKind::Dynamodb => "dynamodb",
        }
    }
}

/// The chapter persistence surface.
///
/// Implementations own the bytes; callers (HubLedger, init_hub,
/// HubSession) own invariants. This trait does **no** crypto or chain
/// validation — that lives in the ledger module. It does **no** secret
/// handling — that lives in the vault (Hestia).
/// All methods are async so the trait composes naturally with
/// network-backed backends (DynamoDB, Postgres) that do real I/O.
/// In-process backends (file, sqlite) implement async fn bodies
/// that complete synchronously — no spawn_blocking needed, no
/// `.await` actually suspends. The async_trait macro gives us
/// object safety so `Box<dyn HubStore>` still works.
#[async_trait::async_trait]
pub trait HubStore: Send + Sync {
    fn backend_kind(&self) -> BackendKind;

    // ----- Charter (immutable post-genesis) -----

    /// Read the charter if present.
    async fn read_charter(&self) -> Result<Option<Charter>>;

    /// Write the charter. Callers should call this exactly once (during
    /// init); a charter is immutable post-genesis. Implementations may
    /// refuse overwrites for safety.
    async fn write_charter(&mut self, charter: &Charter) -> Result<()>;

    // ----- Society state (evolves as acts append) -----

    /// Read the society if present.
    async fn read_society(&self) -> Result<Option<Society>>;

    /// Write/overwrite the society state.
    async fn write_society(&mut self, society: &Society) -> Result<()>;

    // ----- Ledger (append-only, hash-chained) -----

    /// Load all ledger entries in order. Implementations may stream or
    /// fully load; current callers expect a Vec.
    async fn ledger_load_all(&self) -> Result<Vec<LedgerEntry>>;

    /// Append one already-validated entry to the ledger. The entry's
    /// signature + entry_hash + prev_hash + index are computed by the
    /// caller (HubLedger); the store just persists.
    async fn ledger_append(&mut self, entry: &LedgerEntry) -> Result<()>;

    /// True iff the ledger has zero entries. Used by callers to detect
    /// "fresh hub, needs Genesis" without round-tripping the full list.
    async fn ledger_is_empty(&self) -> Result<bool> {
        Ok(self.ledger_load_all().await?.is_empty())
    }

    // ----- Law (V2-8: signed YAML, amended via LawAmended events) -----

    /// Read the current hub law YAML, or None if no law has been
    /// set yet. Returns the raw bytes (not the parsed [`crate::law::Law`])
    /// so the store layer stays parser-agnostic.
    async fn read_law(&self) -> Result<Option<String>> {
        Ok(None) // Default: backends not yet supporting law return None
    }

    /// Write/overwrite the current hub law. Callers should also
    /// append a [`crate::events::HubEvent::LawAmended`] event to
    /// the ledger so the amendment is part of the audit trail.
    async fn write_law(&mut self, _yaml: &str) -> Result<()> {
        anyhow::bail!("this backend does not yet support law storage")
    }

    // ----- Council proposals (V2-9 Phase 2) -----

    /// Persist a council proposal (insert-or-update). Proposals carry
    /// council-holder signatures awaiting M-of-N threshold; storage
    /// is separate from the ledger because they're not yet committed
    /// acts. Implementations that don't support council proposals
    /// reject calls so the operator gets a clear error rather than a
    /// silent no-op.
    async fn write_proposal(&mut self, _proposal: &crate::proposal::CouncilProposal) -> Result<()> {
        anyhow::bail!("this backend does not yet support council proposals")
    }

    /// Read a single proposal by id.
    async fn read_proposal(&self, _id: uuid::Uuid) -> Result<Option<crate::proposal::CouncilProposal>> {
        anyhow::bail!("this backend does not yet support council proposals")
    }

    /// List all currently-stored proposals (open, committed,
    /// rejected, expired). Caller filters by status if needed.
    async fn list_proposals(&self) -> Result<Vec<crate::proposal::CouncilProposal>> {
        anyhow::bail!("this backend does not yet support council proposals")
    }

    /// Remove a proposal. Used by the cleanup pass that drops
    /// expired proposals on the next propose/sign call. Idempotent.
    async fn delete_proposal(&mut self, _id: uuid::Uuid) -> Result<()> {
        anyhow::bail!("this backend does not yet support council proposals")
    }

    // ----- Pair messages (PAIRED-CHANNELS Sprint D) -----

    /// Append a pair message to the per-pair sidecar log. Caller (REST
    /// handler) supplies the seq — it's already known because the
    /// pair's `message_count` projection tells the hub what the next
    /// seq is. Implementations MUST persist atomically; concurrent
    /// appenders at the same seq is a chain-integrity bug.
    async fn append_pair_message(
        &mut self,
        _msg: &crate::pair_message::PairMessage,
    ) -> Result<()> {
        anyhow::bail!("this backend does not yet support pair messages")
    }

    /// Read all messages for a pair, optionally filtered to seq >
    /// `since_seq`. Polling clients use this to fetch what they
    /// haven't seen. Returned messages MUST be in ascending seq
    /// order. Empty Vec if no messages or no pair.
    async fn list_pair_messages(
        &self,
        _pair_id: uuid::Uuid,
        _since_seq: Option<u64>,
    ) -> Result<Vec<crate::pair_message::PairMessage>> {
        anyhow::bail!("this backend does not yet support pair messages")
    }

    // ----- Mailbox (durable per-recipient sealed-notice queue) -----
    //
    // The hub→citizen delivery floor. Each recipient LCT has one serialized
    // queue of sealed notices; the daemon owns the notice codec, so the store
    // persists **opaque bytes** (no cross-crate type dependency). The queue is
    // written at rest inside the SQLCipher-encrypted state DB — extraction- and
    // tamper-resistant under the same in-memory key as society/ledger — and each
    // notice body inside the blob is *additionally* channel-sealed to the
    // recipient (defense in depth). Persistence is a write-through of the working
    // in-memory map; witness-on-completion accounting is unchanged (the mailbox
    // is durable delivery state, NOT the ledger).

    /// Whether this backend durably persists the mailbox. Non-durable backends
    /// keep the in-memory queue only (pre-P1 behavior, lost on restart); the
    /// daemon logs once at startup so the operator knows delivery is best-effort
    /// across a restart rather than silently non-durable.
    fn mailbox_is_durable(&self) -> bool {
        false
    }

    /// Load every persisted per-recipient mailbox blob (recipient LCT →
    /// serialized queue) for startup hydration. Default: nothing persisted.
    async fn mailbox_load_all(&self) -> Result<Vec<(uuid::Uuid, Vec<u8>)>> {
        Ok(Vec::new())
    }

    /// Persist (insert-or-replace) one recipient's whole serialized queue. The
    /// daemon write-throughs after each enqueue. Default: no-op (in-memory only).
    async fn mailbox_put(&mut self, _recipient: uuid::Uuid, _blob: &[u8]) -> Result<()> {
        Ok(())
    }

    /// Drop a recipient's persisted queue (on drain). Idempotent so a redundant
    /// delete after an already-empty mailbox is a harmless no-op. Default: no-op.
    async fn mailbox_delete(&mut self, _recipient: uuid::Uuid) -> Result<()> {
        Ok(())
    }
}

/// Default SQLite filename inside a hub dir.
pub const SQLITE_DB_FILENAME: &str = "hub.db";

/// Pre-rename SQLite filename. Hub dirs created before the chapter→hub
/// rename have `chapter.db`; we keep reading them in place (no forced
/// migration) so existing deployments don't break.
pub const SQLITE_DB_FILENAME_LEGACY: &str = "chapter.db";

/// Open a `HubStore` for the given hub dir. Backend selection:
///
/// 1. If `<hub-dir>/hub.db` exists → SqliteBackend.
/// 2. Else if `<hub-dir>/chapter.db` exists (pre-rename) → SqliteBackend on it.
/// 3. Else if `<hub-dir>/society.json` (or any MVP file) exists → FileBackend.
/// 4. Else (fresh hub) → FileBackend default (MVP-compatible).
///
/// To force a specific backend at create time, use [`open_hub_store_with`].
pub fn open_hub_store(hub_dir: impl AsRef<Path>) -> Result<Box<dyn HubStore>> {
    let hub_dir = hub_dir.as_ref();
    open_hub_store_with_key(hub_dir, store_key(hub_dir)?)
}

/// Like [`open_hub_store`] but with an **explicit** SQLCipher key (or `None`) —
/// the de-env'd entry point. The daemon holds the derived key in memory after
/// ignition and passes it here for runtime store re-opens, so the passphrase is
/// never read from the environment. `None` opens a plaintext/fresh store and
/// fails closed on an encrypted one.
///
/// **DynamoDB:** this synchronous factory cannot load AWS config. If
/// `config.toml` selects the `dynamodb` backend, use
/// [`open_hub_store_with_key_async`] instead.
pub fn open_hub_store_with_key(
    hub_dir: impl AsRef<Path>,
    key: Option<[u8; 32]>,
) -> Result<Box<dyn HubStore>> {
    let hub_dir = hub_dir.as_ref();
    if let Some((storage, _hub_id)) = read_storage_config(hub_dir)
        .with_context(|| format!("reading storage config for {}", hub_dir.display()))?
    {
        let kind = storage.backend_kind()
            .with_context(|| format!("parsing configured storage backend '{}'", storage.backend))?;
        return match kind {
            BackendKind::File => {
                let paths = HubPaths::new(hub_dir.to_path_buf());
                Ok(Box::new(FileBackend::new(paths)))
            }
            BackendKind::Sqlite => {
                let db_path = hub_dir.join(SQLITE_DB_FILENAME);
                let legacy_db_path = hub_dir.join(SQLITE_DB_FILENAME_LEGACY);
                if db_path.exists() {
                    Ok(Box::new(SqliteBackend::open(&db_path, key)?))
                } else if legacy_db_path.exists() {
                    // Pre-rename hub dir — open the legacy chapter.db in place.
                    Ok(Box::new(SqliteBackend::open(&legacy_db_path, key)?))
                } else {
                    Ok(Box::new(SqliteBackend::open(&db_path, key)?))
                }
            }
            BackendKind::Dynamodb => {
                let _ = key;
                anyhow::bail!(
                    "dynamodb backend selected in config.toml but open_hub_store_with_key is sync; \
                     use open_hub_store_with_key_async"
                )
            }
        };
    }

    // No config.toml yet — fall back to legacy disk-based auto-detection.
    let paths = HubPaths::new(hub_dir.to_path_buf());
    let db_path = hub_dir.join(SQLITE_DB_FILENAME);
    let legacy_db_path = hub_dir.join(SQLITE_DB_FILENAME_LEGACY);
    if db_path.exists() {
        Ok(Box::new(SqliteBackend::open(&db_path, key)?))
    } else if legacy_db_path.exists() {
        Ok(Box::new(SqliteBackend::open(&legacy_db_path, key)?))
    } else {
        Ok(Box::new(FileBackend::new(paths)))
    }
}

/// Re-key the SQLCipher state DB in place: open with `old_key`, verify it
/// decrypts, then `PRAGMA rekey` to `new_key`. Used by passphrase rotation so an
/// operator can switch to a memorable phrase of their own choosing. Errors
/// (without changing anything) if `old_key` doesn't open the DB.
pub fn rekey_store(hub_dir: impl AsRef<Path>, old_key: [u8; 32], new_key: [u8; 32]) -> Result<()> {
    let hub_dir = hub_dir.as_ref();
    let db_path = hub_dir.join(SQLITE_DB_FILENAME);
    if !db_path.exists() {
        anyhow::bail!("no {} to re-key", db_path.display());
    }
    let conn = rusqlite::Connection::open(&db_path)
        .with_context(|| format!("opening {} to re-key", db_path.display()))?;
    conn.pragma_update(None, "key", hex::encode(old_key))
        .context("applying current SQLCipher key")?;
    // Probe that the OLD key actually decrypts before we re-key.
    conn.query_row("SELECT count(*) FROM sqlite_master", [], |r| r.get::<_, i64>(0))
        .map_err(|_| anyhow::anyhow!("current passphrase did not decrypt the state store — aborting"))?;
    conn.pragma_update(None, "rekey", hex::encode(new_key))
        .context("re-keying the state store to the new passphrase")?;
    Ok(())
}

/// True if `path` begins with the plaintext SQLite magic — i.e. not yet
/// SQLCipher-encrypted (an encrypted header is indistinguishable from random).
fn is_plaintext_sqlite(path: &Path) -> bool {
    use std::io::Read;
    let mut hdr = [0u8; 16];
    std::fs::File::open(path)
        .and_then(|mut f| f.read_exact(&mut hdr))
        .map(|_| &hdr == b"SQLite format 3\0")
        .unwrap_or(false)
}

/// Migrate a plaintext `hub.db` to a SQLCipher-encrypted one in place,
/// preserving every row + the ledger order. Checkpoints the WAL, uses
/// `sqlcipher_export` to copy the whole schema + data into a freshly-keyed DB,
/// then atomically replaces the original and clears the stale WAL/SHM sidecars.
/// `key_hex` is `[0-9a-f]` only, so single-quoting it in the SQL is safe.
fn migrate_plaintext_to_encrypted(path: &Path, key_hex: &str) -> Result<()> {
    let tmp = path.with_extension("db.enc-migrating");
    let _ = std::fs::remove_file(&tmp);
    {
        let conn = rusqlite::Connection::open(path)
            .with_context(|| format!("opening plaintext hub.db for migration: {}", path.display()))?;
        // Flush any WAL into the main file so the export sees all committed rows.
        let _ = conn.execute_batch("PRAGMA wal_checkpoint(TRUNCATE);");
        conn.execute_batch(&format!(
            "ATTACH DATABASE '{}' AS enc KEY '{}'; \
             SELECT sqlcipher_export('enc'); \
             DETACH DATABASE enc;",
            tmp.display(),
            key_hex,
        ))
        .context("exporting plaintext hub state into an encrypted copy")?;
    }
    std::fs::rename(&tmp, path).context("replacing plaintext hub.db with the encrypted copy")?;
    // The old plaintext WAL/SHM sidecars are stale for the new (encrypted) file.
    for ext in ["db-wal", "db-shm"] {
        let _ = std::fs::remove_file(path.with_extension(ext));
    }
    Ok(())
}

/// Derive the at-rest **SQLCipher key** for this hub's state DB from the vault
/// passphrase (`HUB_PASSPHRASE`), salted per-hub. `None` when no passphrase is
/// available — then a plaintext DB opens as-is (legacy / fresh), and an
/// already-encrypted DB fails to open (fail-closed; ignite tier-1 first).
///
/// The hub STATE (member roster, pinned member pubkeys, pairings, profiles,
/// ledger) is thus encrypted at rest under the same secret that guards the
/// identity — closing the gap where a sealed hub's *key* was protected but
/// everything it *knows* sat in world-readable plaintext next to it.
fn store_key(hub_dir: &Path) -> Result<Option<[u8; 32]>> {
    match crate::identity::env_passphrase() {
        Some(passphrase) => Ok(Some(derive_store_key(hub_dir, &passphrase)?)),
        None => Ok(None),
    }
}

/// Derive the at-rest **SQLCipher key** for this hub's state DB from an explicit
/// `passphrase`, salted per-hub (`<hub-dir>/.store-salt`). This is the de-env'd
/// path: callers (the daemon's runtime ignition) pass the passphrase they hold
/// transiently and keep the returned key in memory — the passphrase is never
/// read from the process environment. An empty passphrase is a valid (NULL) key,
/// distinct from "no ignition yet". See also [`open_hub_store_with_key`].
pub fn derive_store_key(hub_dir: &Path, passphrase: &str) -> Result<[u8; 32]> {
    let salt = load_or_create_store_salt(hub_dir)?;
    let dk = web4_core::vault::crypto::derive_key(passphrase, &salt)
        .map_err(|e| anyhow::anyhow!("deriving hub store key: {e}"))?;
    Ok(*dk.as_bytes())
}

/// Per-hub salt for [`store_key`], stored clear (salts aren't secret) at
/// `<hub-dir>/.store-salt`. Generated once on first use.
fn load_or_create_store_salt(hub_dir: &Path) -> Result<[u8; 16]> {
    let salt_path = hub_dir.join(".store-salt");
    if salt_path.exists() {
        let raw = std::fs::read(&salt_path)
            .with_context(|| format!("reading store salt {}", salt_path.display()))?;
        raw.as_slice()
            .try_into()
            .map_err(|_| anyhow::anyhow!("store salt at {} must be 16 bytes", salt_path.display()))
    } else {
        let s = web4_core::vault::crypto::generate_salt();
        std::fs::create_dir_all(hub_dir).ok();
        std::fs::write(&salt_path, s)
            .with_context(|| format!("writing store salt {}", salt_path.display()))?;
        Ok(s)
    }
}

/// Open a `HubStore` for the given hub dir, forcing the backend
/// kind. Used by `hub init --storage <kind>` and the migration tool.
pub fn open_hub_store_with(
    hub_dir: impl AsRef<Path>,
    kind: BackendKind,
) -> Result<Box<dyn HubStore>> {
    let hub_dir = hub_dir.as_ref();
    let paths = HubPaths::new(hub_dir.to_path_buf());
    match kind {
        BackendKind::File => Ok(Box::new(FileBackend::new(paths))),
        BackendKind::Sqlite => {
            std::fs::create_dir_all(hub_dir)
                .with_context(|| format!("creating hub dir {}", hub_dir.display()))?;
            let db_path = hub_dir.join(SQLITE_DB_FILENAME);
            let key = store_key(hub_dir)?;
            Ok(Box::new(SqliteBackend::open(&db_path, key)?))
        }
        BackendKind::Dynamodb => {
            // DynamoDB needs out-of-band config (table name, AWS region,
            // hub_id) that doesn't live in the hub_dir. The synchronous
            // factory cannot build it; use `open_hub_store_async` or
            // construct `dynamodb_store::DynamoDbBackend` directly.
            anyhow::bail!(
                "dynamodb backend requires async construction; \
                 use open_hub_store_async or dynamodb_store::DynamoDbBackend::open"
            )
        }
    }
}

/// Load `<hub-dir>/config.toml` and return the storage section plus the
/// hub id (if recorded). Returns `None` when the config file is missing OR
/// when it has no `[storage]` section — both mean "fall back to disk-based
/// auto-detection". The absent-section case is load-bearing: every hub
/// initialized before `[storage]` existed has a config without it, and
/// defaulting that to `file` ignores an existing sqlite `hub.db` (empty
/// society reads → init's idempotency probe can approve a re-genesis over
/// a live hub — review 2026-07-23).
fn read_storage_config(hub_dir: &Path) -> Result<Option<(crate::hub::StorageSection, Option<uuid::Uuid>)>> {
    let paths = HubPaths::new(hub_dir.to_path_buf());
    if !paths.config().exists() {
        return Ok(None);
    }
    let config = crate::hub::HubConfig::load(paths.config())
        .with_context(|| format!("loading config at {}", paths.config().display()))?;
    match config.storage {
        Some(storage) => Ok(Some((storage, config.hub.id))),
        None => Ok(None),
    }
}

/// Async variant of [`open_hub_store`] that supports network-backed
/// backends (DynamoDB). File/SQLite backends complete synchronously
/// inside the async body; DynamoDB loads AWS config and constructs a
/// client. This is the runtime entry point for `hub serve`, `HubSession`,
/// and any other async caller.
pub async fn open_hub_store_async(hub_dir: impl AsRef<Path>) -> Result<Box<dyn HubStore>> {
    let hub_dir = hub_dir.as_ref();
    let key = store_key(hub_dir)?;
    open_hub_store_with_key_async(hub_dir, key).await
}

/// Async variant of [`open_hub_store_with_key`]. Handles DynamoDB in
/// addition to file/SQLite.
pub async fn open_hub_store_with_key_async(
    hub_dir: impl AsRef<Path>,
    key: Option<[u8; 32]>,
) -> Result<Box<dyn HubStore>> {
    let hub_dir = hub_dir.as_ref();
    if let Some((storage, _hub_id)) = read_storage_config(hub_dir)? {
        let kind = storage.backend_kind()
            .with_context(|| format!("parsing configured storage backend '{}'", storage.backend))?;

        return match kind {
            BackendKind::File => {
                let paths = HubPaths::new(hub_dir.to_path_buf());
                Ok(Box::new(FileBackend::new(paths)))
            }
            BackendKind::Sqlite => {
                let db_path = hub_dir.join(SQLITE_DB_FILENAME);
                let legacy_db_path = hub_dir.join(SQLITE_DB_FILENAME_LEGACY);
                if db_path.exists() {
                    Ok(Box::new(SqliteBackend::open(&db_path, key)?))
                } else if legacy_db_path.exists() {
                    Ok(Box::new(SqliteBackend::open(&legacy_db_path, key)?))
                } else {
                    Ok(Box::new(SqliteBackend::open(&db_path, key)?))
                }
            }
            BackendKind::Dynamodb => {
                #[cfg(feature = "dynamodb")]
                {
                    let table = storage.dynamodb_table.ok_or_else(|| anyhow::anyhow!(
                        "dynamodb backend requires storage.dynamodb_table in config.toml"
                    ))?;
                    let hub_id = _hub_id.ok_or_else(|| anyhow::anyhow!(
                        "dynamodb backend requires hub.id in config.toml"
                    ))?;
                    let _ = key;

                    let mut aws_cfg = aws_config::defaults(aws_config::BehaviorVersion::latest());
                    if let Some(region) = storage.dynamodb_region {
                        aws_cfg = aws_cfg.region(aws_sdk_dynamodb::config::Region::new(region));
                    }
                    if let Some(endpoint) = storage.dynamodb_endpoint {
                        aws_cfg = aws_cfg.endpoint_url(endpoint);
                    }
                    let cfg = aws_cfg.load().await;
                    let client = aws_sdk_dynamodb::Client::new(&cfg);
                    Ok(Box::new(crate::dynamodb_store::DynamoDbBackend::open(client, table, hub_id)))
                }
                #[cfg(not(feature = "dynamodb"))]
                {
                    let _ = key;
                    anyhow::bail!(
                        "dynamodb backend selected but hub-lib was built without the `dynamodb` feature"
                    )
                }
            }
        };
    }

    // No config.toml yet — fall back to legacy disk-based auto-detection.
    let paths = HubPaths::new(hub_dir.to_path_buf());
    let db_path = hub_dir.join(SQLITE_DB_FILENAME);
    let legacy_db_path = hub_dir.join(SQLITE_DB_FILENAME_LEGACY);
    if db_path.exists() {
        Ok(Box::new(SqliteBackend::open(&db_path, key)?))
    } else if legacy_db_path.exists() {
        Ok(Box::new(SqliteBackend::open(&legacy_db_path, key)?))
    } else {
        Ok(Box::new(FileBackend::new(paths)))
    }
}

impl std::str::FromStr for BackendKind {
    type Err = anyhow::Error;
    fn from_str(s: &str) -> Result<Self> {
        match s.to_ascii_lowercase().as_str() {
            "file" | "files" | "jsonl" => Ok(BackendKind::File),
            "sqlite" | "sqlite3" | "db" => Ok(BackendKind::Sqlite),
            "dynamodb" | "dynamo" | "ddb" => Ok(BackendKind::Dynamodb),
            other => Err(anyhow::anyhow!(
                "unknown storage backend '{}'; expected 'file', 'sqlite', or 'dynamodb'",
                other
            )),
        }
    }
}

// ============================================================================
// FileBackend
// ============================================================================

/// File-backed [`HubStore`] — wraps the MVP's JSON/JSONL files.
///
/// Layout (unchanged from MVP):
/// - `charter.json` — Charter
/// - `society.json` — Society
/// - `ledger.jsonl` — one LedgerEntry per line
#[derive(Debug)]
pub struct FileBackend {
    paths: HubPaths,
}

impl FileBackend {
    pub fn new(paths: HubPaths) -> Self {
        Self { paths }
    }

    pub fn paths(&self) -> &HubPaths {
        &self.paths
    }

    pub fn charter_path(&self) -> PathBuf {
        self.paths.charter()
    }

    pub fn society_path(&self) -> PathBuf {
        self.paths.society()
    }

    pub fn ledger_path(&self) -> PathBuf {
        self.paths.ledger()
    }

    pub fn law_path(&self) -> PathBuf {
        self.paths.root.join("hub-law.yaml")
    }

    fn ensure_parent(path: &Path) -> Result<()> {
        if let Some(parent) = path.parent() {
            if !parent.as_os_str().is_empty() && !parent.exists() {
                std::fs::create_dir_all(parent)
                    .with_context(|| format!("creating parent dir {}", parent.display()))?;
            }
        }
        Ok(())
    }
}

#[async_trait::async_trait]
impl HubStore for FileBackend {
    fn backend_kind(&self) -> BackendKind {
        BackendKind::File
    }

    async fn read_charter(&self) -> Result<Option<Charter>> {
        let path = self.charter_path();
        if !path.exists() {
            return Ok(None);
        }
        let charter = Charter::load(&path)
            .with_context(|| format!("loading charter from {}", path.display()))?;
        Ok(Some(charter))
    }

    async fn write_charter(&mut self, charter: &Charter) -> Result<()> {
        let path = self.charter_path();
        Self::ensure_parent(&path)?;
        charter.save(&path)
            .with_context(|| format!("writing charter to {}", path.display()))?;
        Ok(())
    }

    async fn read_society(&self) -> Result<Option<Society>> {
        let path = self.society_path();
        if !path.exists() {
            return Ok(None);
        }
        let json = std::fs::read_to_string(&path)
            .with_context(|| format!("reading society from {}", path.display()))?;
        let society: Society = serde_json::from_str(&json)
            .with_context(|| format!("parsing society at {}", path.display()))?;
        Ok(Some(society))
    }

    async fn write_society(&mut self, society: &Society) -> Result<()> {
        let path = self.society_path();
        Self::ensure_parent(&path)?;
        let json = serde_json::to_string_pretty(society)
            .context("serializing society")?;
        std::fs::write(&path, json)
            .with_context(|| format!("writing society to {}", path.display()))?;
        Ok(())
    }

    async fn ledger_load_all(&self) -> Result<Vec<LedgerEntry>> {
        let path = self.ledger_path();
        if !path.exists() {
            return Ok(Vec::new());
        }
        let content = std::fs::read_to_string(&path)
            .with_context(|| format!("reading ledger at {}", path.display()))?;
        let mut entries = Vec::new();
        for (line_num, line) in content.lines().enumerate() {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }
            let entry: LedgerEntry = serde_json::from_str(trimmed)
                .with_context(|| format!("parsing ledger line {} of {}", line_num + 1, path.display()))?;
            entries.push(entry);
        }
        Ok(entries)
    }

    async fn ledger_append(&mut self, entry: &LedgerEntry) -> Result<()> {
        use std::fs::OpenOptions;
        use std::io::Write;
        let path = self.ledger_path();
        Self::ensure_parent(&path)?;
        let line = serde_json::to_string(entry).context("serializing ledger entry")?;
        let mut f = OpenOptions::new()
            .append(true)
            .create(true)
            .open(&path)
            .with_context(|| format!("opening {} for append", path.display()))?;
        writeln!(f, "{}", line)
            .with_context(|| format!("writing to {}", path.display()))?;
        Ok(())
    }

    async fn read_law(&self) -> Result<Option<String>> {
        let path = self.law_path();
        if path.exists() {
            return std::fs::read_to_string(&path)
                .map(Some)
                .with_context(|| format!("reading law from {}", path.display()));
        }
        // Back-compat: hub dirs created before the chapter→hub rename
        // wrote `hub-law.yaml`. If the new name isn't present but
        // the old one is, read the old one. (write_law always writes
        // the new name; next set-law migrates the file.)
        let legacy = self.paths.root.join("hub-law.yaml");
        if legacy.exists() {
            return std::fs::read_to_string(&legacy)
                .map(Some)
                .with_context(|| format!("reading legacy hub-law from {}", legacy.display()));
        }
        Ok(None)
    }

    async fn write_law(&mut self, yaml: &str) -> Result<()> {
        let path = self.law_path();
        Self::ensure_parent(&path)?;
        std::fs::write(&path, yaml)
            .with_context(|| format!("writing law to {}", path.display()))
    }

    // ----- V2-9 Phase 2: council proposals -----

    async fn write_proposal(&mut self, proposal: &crate::proposal::CouncilProposal) -> Result<()> {
        let dir = self.paths.root.join("proposals");
        std::fs::create_dir_all(&dir)
            .with_context(|| format!("creating proposals dir {}", dir.display()))?;
        let path = dir.join(format!("{}.json", proposal.id));
        // Atomic write: temp + rename. Avoids torn reads if another
        // request (admin UI, sign, list) reads concurrently.
        let tmp = path.with_extension("json.tmp");
        let json = serde_json::to_string_pretty(proposal)
            .context("serializing proposal")?;
        std::fs::write(&tmp, json)
            .with_context(|| format!("writing temp proposal {}", tmp.display()))?;
        std::fs::rename(&tmp, &path)
            .with_context(|| format!("renaming {} -> {}", tmp.display(), path.display()))?;
        Ok(())
    }

    async fn read_proposal(&self, id: uuid::Uuid) -> Result<Option<crate::proposal::CouncilProposal>> {
        let path = self.paths.root.join("proposals").join(format!("{}.json", id));
        if !path.exists() {
            return Ok(None);
        }
        let s = std::fs::read_to_string(&path)
            .with_context(|| format!("reading proposal {}", path.display()))?;
        let proposal = serde_json::from_str(&s)
            .with_context(|| format!("parsing proposal {}", path.display()))?;
        Ok(Some(proposal))
    }

    async fn list_proposals(&self) -> Result<Vec<crate::proposal::CouncilProposal>> {
        let dir = self.paths.root.join("proposals");
        if !dir.exists() {
            return Ok(Vec::new());
        }
        let mut out = Vec::new();
        for entry in std::fs::read_dir(&dir)
            .with_context(|| format!("reading proposals dir {}", dir.display()))?
        {
            let entry = entry?;
            let path = entry.path();
            // Skip non-JSON (e.g., leftover .tmp from a crashed write)
            if path.extension().and_then(|s| s.to_str()) != Some("json") {
                continue;
            }
            let s = std::fs::read_to_string(&path)
                .with_context(|| format!("reading proposal {}", path.display()))?;
            match serde_json::from_str::<crate::proposal::CouncilProposal>(&s) {
                Ok(p) => out.push(p),
                Err(e) => tracing::warn!("skipping unparseable proposal {}: {}", path.display(), e),
            }
        }
        // Newest first so admin UI shows recent activity at the top.
        out.sort_by(|a, b| b.proposed_at.cmp(&a.proposed_at));
        Ok(out)
    }

    async fn delete_proposal(&mut self, id: uuid::Uuid) -> Result<()> {
        let path = self.paths.root.join("proposals").join(format!("{}.json", id));
        if path.exists() {
            std::fs::remove_file(&path)
                .with_context(|| format!("removing proposal {}", path.display()))?;
        }
        Ok(())
    }

    // ----- PAIRED-CHANNELS Sprint D: pair message sidecar -----

    async fn append_pair_message(
        &mut self,
        msg: &crate::pair_message::PairMessage,
    ) -> Result<()> {
        use std::fs::OpenOptions;
        use std::io::Write;
        let dir = self.paths.root.join("pair-messages");
        std::fs::create_dir_all(&dir)
            .with_context(|| format!("creating pair-messages dir {}", dir.display()))?;
        // One JSONL file per pair — append-only matches the ledger
        // shape and keeps writes O(1) regardless of message_count.
        let path = dir.join(format!("{}.jsonl", msg.pair_id));
        let line = serde_json::to_string(msg).context("serializing pair message")?;
        let mut f = OpenOptions::new()
            .append(true)
            .create(true)
            .open(&path)
            .with_context(|| format!("opening {} for append", path.display()))?;
        writeln!(f, "{}", line)
            .with_context(|| format!("writing to {}", path.display()))?;
        Ok(())
    }

    async fn list_pair_messages(
        &self,
        pair_id: uuid::Uuid,
        since_seq: Option<u64>,
    ) -> Result<Vec<crate::pair_message::PairMessage>> {
        let path = self.paths.root.join("pair-messages").join(format!("{}.jsonl", pair_id));
        if !path.exists() {
            return Ok(Vec::new());
        }
        let content = std::fs::read_to_string(&path)
            .with_context(|| format!("reading {}", path.display()))?;
        let mut out = Vec::new();
        for (i, line) in content.lines().enumerate() {
            let trimmed = line.trim();
            if trimmed.is_empty() { continue; }
            let msg: crate::pair_message::PairMessage = serde_json::from_str(trimmed)
                .with_context(|| format!("parsing pair message at line {} of {}",
                    i + 1, path.display()))?;
            // Filter on the read path; cheap, log is per-pair so small.
            if let Some(s) = since_seq {
                if msg.seq <= s { continue; }
            }
            out.push(msg);
        }
        // File is append-order = seq-order by construction, but be
        // defensive about a hand-edited file.
        out.sort_by_key(|m| m.seq);
        Ok(out)
    }
}

// ============================================================================
// SqliteBackend
// ============================================================================

/// SQLite-backed [`HubStore`] — one `chapter.db` file per chapter.
///
/// ## Schema
///
/// ```sql
/// CREATE TABLE metadata (
///     key   TEXT PRIMARY KEY,
///     value TEXT NOT NULL    -- JSON-serialized
/// );
/// -- keys: "charter", "society"
///
/// CREATE TABLE ledger_entries (
///     idx        INTEGER PRIMARY KEY,
///     entry_json TEXT NOT NULL  -- full LedgerEntry as canonical JSON
/// );
/// ```
///
/// Append-only discipline: ledger entries are inserted with their `index`
/// as PRIMARY KEY; collisions error. Charter is written once via UPSERT
/// (overwrite would only happen if a caller violated the write-once
/// discipline at the HubLedger / init layer, which is the source of
/// truth for that invariant).
///
/// ## Why one DB per chapter (not one shared DB)
///
/// V2-2 ships SQLite for single-machine operators. Multi-chapter deployments
/// scale via PostgresBackend later (V2-15, B6) with schema-per-chapter
/// isolation. SQLite-per-chapter keeps the per-chapter blast radius small
/// and migration (file ↔ sqlite ↔ postgres) shape-symmetric.
pub struct SqliteBackend {
    /// Wrapped in `std::sync::Mutex` so `SqliteBackend: Sync` (rusqlite's
    /// `Connection` is `Send` but not `Sync`). The async trait's default
    /// future Send bound transitively requires self: Sync for `&self`
    /// methods. The mutex is uncontended in practice (one daemon per
    /// chapter), so the lock cost is a brief acquire per call.
    conn: std::sync::Mutex<rusqlite::Connection>,
    /// Stored for debug + future migration tooling.
    db_path: PathBuf,
}

impl std::fmt::Debug for SqliteBackend {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SqliteBackend")
            .field("db_path", &self.db_path)
            .finish()
    }
}

impl SqliteBackend {
    /// Open (or create) the hub state DB. When `key` is `Some`, the DB is
    /// **SQLCipher-encrypted at rest** under that key; a legacy plaintext
    /// `hub.db` is migrated in place on first open (crash-safe, all rows
    /// preserved). When `key` is `None`, a plaintext DB opens as-is, and an
    /// already-encrypted DB **fails to open** (fail-closed — the state needs
    /// the vault passphrase).
    pub fn open(db_path: impl AsRef<Path>, key: Option<[u8; 32]>) -> Result<Self> {
        let db_path = db_path.as_ref().to_path_buf();
        if let Some(parent) = db_path.parent() {
            if !parent.as_os_str().is_empty() && !parent.exists() {
                std::fs::create_dir_all(parent)
                    .with_context(|| format!("creating parent dir {}", parent.display()))?;
            }
        }

        // Whether the DB already existed on disk BEFORE we (possibly) create it
        // below — captured first, because `Connection::open` creates an empty
        // file whose 0-byte header would otherwise read as "not plaintext".
        let preexisting = db_path.exists();

        // One-time at-rest migration: re-encrypt a legacy plaintext hub.db.
        if let Some(k) = key {
            if preexisting && is_plaintext_sqlite(&db_path) {
                migrate_plaintext_to_encrypted(&db_path, &hex::encode(k))
                    .with_context(|| format!("encrypting plaintext hub state at {}", db_path.display()))?;
            }
        }

        let conn = rusqlite::Connection::open(&db_path)
            .with_context(|| format!("opening sqlite db at {}", db_path.display()))?;
        // SQLCipher: key the connection BEFORE any other access.
        if let Some(k) = key {
            conn.pragma_update(None, "key", hex::encode(k))
                .context("applying SQLCipher key to hub state")?;
        } else if preexisting && !is_plaintext_sqlite(&db_path) {
            // Encrypted DB but no key available → fail closed, don't corrupt.
            anyhow::bail!(
                "hub state at {} is encrypted but no HUB_PASSPHRASE is set — \
                 set the vault passphrase to open it (the state needs tier-1 ignition)",
                db_path.display()
            );
        }
        // Enforce foreign keys + reasonable durability defaults
        conn.execute_batch(
            "PRAGMA foreign_keys = ON;
             PRAGMA journal_mode = WAL;
             PRAGMA synchronous = NORMAL;",
        ).context("setting sqlite pragmas (wrong passphrase, or not a hub DB?)")?;
        // Schema
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS metadata (
                 key   TEXT PRIMARY KEY,
                 value TEXT NOT NULL
             );
             CREATE TABLE IF NOT EXISTS ledger_entries (
                 idx        INTEGER PRIMARY KEY,
                 entry_json TEXT NOT NULL
             );
             CREATE TABLE IF NOT EXISTS mailbox (
                 recipient TEXT PRIMARY KEY,
                 blob      BLOB NOT NULL
             );
             -- PAIRED-CHANNELS Sprint D sidecar. The composite PRIMARY KEY is
             -- load-bearing: it's the atomic-append primitive that makes two
             -- writers racing on the same seq a loud constraint violation
             -- rather than a silently clobbered message.
             CREATE TABLE IF NOT EXISTS pair_messages (
                 pair_id  TEXT NOT NULL,
                 seq      INTEGER NOT NULL,
                 msg_json TEXT NOT NULL,
                 PRIMARY KEY (pair_id, seq)
             );",
        ).context("initializing sqlite schema")?;
        Ok(Self { conn: std::sync::Mutex::new(conn), db_path })
    }

    pub fn db_path(&self) -> &Path {
        &self.db_path
    }

    fn read_meta(&self, key: &str) -> Result<Option<String>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn
            .prepare("SELECT value FROM metadata WHERE key = ?1")
            .context("preparing metadata SELECT")?;
        let mut rows = stmt
            .query(rusqlite::params![key])
            .context("querying metadata")?;
        match rows.next().context("stepping metadata query")? {
            Some(row) => Ok(Some(row.get::<_, String>(0).context("reading metadata value")?)),
            None => Ok(None),
        }
    }

    fn write_meta(&self, key: &str, value: &str) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn
            .execute(
                "INSERT INTO metadata (key, value) VALUES (?1, ?2)
                 ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                rusqlite::params![key, value],
            )
            .context("writing metadata")?;
        Ok(())
    }
}

// ============================================================================
// Migration tool
// ============================================================================

/// Outcome of [`migrate_hub`]. Caller decides how to surface this.
#[derive(Debug)]
pub struct MigrationResult {
    pub source_backend: BackendKind,
    pub target_backend: BackendKind,
    pub charter_copied: bool,
    pub society_copied: bool,
    pub ledger_entries_copied: usize,
    /// Renamed pre-migration artifacts (paths relative to hub dir),
    /// preserved so operators can roll back if needed.
    pub preserved_artifacts: Vec<PathBuf>,
}

/// Migrate a chapter from its current backend to `target_backend`.
///
/// Algorithm:
/// 1. Auto-detect source backend at `hub_dir`.
/// 2. If source == target, no-op (returns OK with zero-copied counters).
/// 3. Open target backend (forced kind via [`open_hub_store_with`]).
///    For sqlite, this creates `chapter.db`.
/// 4. Copy charter (if present) → target.
/// 5. Copy society (if present) → target.
/// 6. Walk ledger entries in order from source; append each to target.
///    No re-signing — entries copy byte-for-byte (canonical JSON).
/// 7. Rename source artifacts to `<name>.pre-migration` so they don't
///    interfere with future auto-detection but remain recoverable.
///
/// The caller (typically `hub migrate` CLI) should run a verify-ledger
/// pass against the hub dir after this returns to confirm chain
/// integrity is intact on the target backend.
///
/// Note: this function does NOT touch identity files, config.toml, or
/// anything else outside the chapter storage abstraction. Those stay
/// where they were.
pub async fn migrate_hub(
    hub_dir: impl AsRef<Path>,
    target_backend: BackendKind,
) -> Result<MigrationResult> {
    let hub_dir = hub_dir.as_ref();
    if !hub_dir.exists() {
        anyhow::bail!("hub dir {} does not exist", hub_dir.display());
    }

    // 1. Auto-detect source.
    let source = open_hub_store(hub_dir)
        .context("opening source store for migration")?;
    let source_kind = source.backend_kind();

    if source_kind == target_backend {
        return Ok(MigrationResult {
            source_backend: source_kind,
            target_backend,
            charter_copied: false,
            society_copied: false,
            ledger_entries_copied: 0,
            preserved_artifacts: Vec::new(),
        });
    }

    // 2. Read source state.
    let charter = source.read_charter().await.context("reading source charter")?;
    let society = source.read_society().await.context("reading source society")?;
    let ledger_entries = source.ledger_load_all().await.context("reading source ledger")?;

    // Drop source handle BEFORE creating target — particularly important
    // for sqlite, where a stale connection could conflict on WAL files.
    drop(source);

    // 3. Open target.
    let mut target = open_hub_store_with(hub_dir, target_backend)
        .with_context(|| format!("opening target store ({:?})", target_backend))?;

    // 4-6. Copy state.
    let mut charter_copied = false;
    if let Some(c) = charter {
        target.write_charter(&c).await.context("writing charter to target")?;
        charter_copied = true;
    }
    let mut society_copied = false;
    if let Some(s) = society {
        target.write_society(&s).await.context("writing society to target")?;
        society_copied = true;
    }
    let entries_copied = ledger_entries.len();
    for entry in &ledger_entries {
        target.ledger_append(entry).await
            .with_context(|| format!("appending ledger entry idx={} to target", entry.index))?;
    }
    // Drop target so any flushes complete before we rename source files
    drop(target);

    // 7. Preserve source artifacts.
    let paths = HubPaths::new(hub_dir.to_path_buf());
    let mut preserved = Vec::new();
    match source_kind {
        BackendKind::File => {
            for f in [paths.charter(), paths.society(), paths.ledger()] {
                if f.exists() {
                    let backup = f.with_extension(
                        format!("{}.pre-migration",
                            f.extension().and_then(|s| s.to_str()).unwrap_or("bak"))
                    );
                    std::fs::rename(&f, &backup)
                        .with_context(|| format!("renaming {} to backup", f.display()))?;
                    preserved.push(backup);
                }
            }
        }
        BackendKind::Sqlite => {
            let db = hub_dir.join(SQLITE_DB_FILENAME);
            if db.exists() {
                let backup = hub_dir.join(format!("{}.pre-migration", SQLITE_DB_FILENAME));
                std::fs::rename(&db, &backup)
                    .with_context(|| format!("renaming {} to backup", db.display()))?;
                preserved.push(backup);
            }
            // SQLite WAL/SHM files if present (after journal_mode=WAL)
            for sidecar in &[
                format!("{SQLITE_DB_FILENAME}-wal"),
                format!("{SQLITE_DB_FILENAME}-shm"),
            ] {
                let p = hub_dir.join(sidecar);
                if p.exists() {
                    let backup = hub_dir.join(format!("{}.pre-migration", sidecar));
                    std::fs::rename(&p, &backup)
                        .with_context(|| format!("renaming {} to backup", p.display()))?;
                    preserved.push(backup);
                }
            }
        }
        BackendKind::Dynamodb => {
            // For dynamodb, "preservation" is a different concept — the
            // bytes live in AWS, not on disk. Migration from dynamodb
            // would mean exporting to file/sqlite which is a separate
            // operator workflow (use the SDK's table-export feature, or
            // walk via ledger_load_all + write to target backend). Not
            // wired through this convenience function yet.
        }
    }

    Ok(MigrationResult {
        source_backend: source_kind,
        target_backend,
        charter_copied,
        society_copied,
        ledger_entries_copied: entries_copied,
        preserved_artifacts: preserved,
    })
}

#[async_trait::async_trait]
impl HubStore for SqliteBackend {
    fn backend_kind(&self) -> BackendKind {
        BackendKind::Sqlite
    }

    async fn read_charter(&self) -> Result<Option<Charter>> {
        match self.read_meta("charter")? {
            None => Ok(None),
            Some(json) => {
                let charter: Charter = serde_json::from_str(&json)
                    .context("parsing charter from sqlite metadata")?;
                Ok(Some(charter))
            }
        }
    }

    async fn write_charter(&mut self, charter: &Charter) -> Result<()> {
        let json = serde_json::to_string(charter).context("serializing charter")?;
        self.write_meta("charter", &json)
    }

    async fn read_society(&self) -> Result<Option<Society>> {
        match self.read_meta("society")? {
            None => Ok(None),
            Some(json) => {
                let society: Society = serde_json::from_str(&json)
                    .context("parsing society from sqlite metadata")?;
                Ok(Some(society))
            }
        }
    }

    async fn write_society(&mut self, society: &Society) -> Result<()> {
        let json = serde_json::to_string(society).context("serializing society")?;
        self.write_meta("society", &json)
    }

    async fn ledger_load_all(&self) -> Result<Vec<LedgerEntry>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn
            .prepare("SELECT entry_json FROM ledger_entries ORDER BY idx ASC")
            .context("preparing ledger SELECT")?;
        let rows = stmt
            .query_map([], |row| row.get::<_, String>(0))
            .context("querying ledger entries")?;
        let mut entries = Vec::new();
        for row in rows {
            let json = row.context("reading ledger row")?;
            let entry: LedgerEntry = serde_json::from_str(&json)
                .context("parsing ledger entry from sqlite")?;
            entries.push(entry);
        }
        Ok(entries)
    }

    async fn ledger_append(&mut self, entry: &LedgerEntry) -> Result<()> {
        let json = serde_json::to_string(entry).context("serializing ledger entry")?;
        let conn = self.conn.lock().unwrap();
        conn
            .execute(
                "INSERT INTO ledger_entries (idx, entry_json) VALUES (?1, ?2)",
                rusqlite::params![entry.index as i64, json],
            )
            .with_context(|| format!("inserting ledger entry idx={}", entry.index))?;
        Ok(())
    }

    async fn ledger_is_empty(&self) -> Result<bool> {
        let conn = self.conn.lock().unwrap();
        let count: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM ledger_entries",
                [],
                |row| row.get(0),
            )
            .context("counting ledger entries")?;
        Ok(count == 0)
    }

    async fn read_law(&self) -> Result<Option<String>> {
        self.read_meta("law")
    }

    async fn write_law(&mut self, yaml: &str) -> Result<()> {
        self.write_meta("law", yaml)
    }

    fn mailbox_is_durable(&self) -> bool {
        true
    }

    async fn mailbox_load_all(&self) -> Result<Vec<(uuid::Uuid, Vec<u8>)>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn
            .prepare("SELECT recipient, blob FROM mailbox")
            .context("preparing mailbox SELECT")?;
        let rows = stmt
            .query_map([], |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, Vec<u8>>(1)?))
            })
            .context("querying mailbox")?;
        let mut out = Vec::new();
        for row in rows {
            let (recipient, blob) = row.context("reading mailbox row")?;
            let recipient = uuid::Uuid::parse_str(&recipient)
                .context("parsing mailbox recipient uuid")?;
            out.push((recipient, blob));
        }
        Ok(out)
    }

    async fn mailbox_put(&mut self, recipient: uuid::Uuid, blob: &[u8]) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO mailbox (recipient, blob) VALUES (?1, ?2)
             ON CONFLICT(recipient) DO UPDATE SET blob = excluded.blob",
            rusqlite::params![recipient.to_string(), blob],
        )
        .with_context(|| format!("writing mailbox blob for {recipient}"))?;
        Ok(())
    }

    async fn mailbox_delete(&mut self, recipient: uuid::Uuid) -> Result<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "DELETE FROM mailbox WHERE recipient = ?1",
            rusqlite::params![recipient.to_string()],
        )
        .with_context(|| format!("deleting mailbox blob for {recipient}"))?;
        Ok(())
    }

    // ----- PAIRED-CHANNELS Sprint D: pair message sidecar -----

    async fn append_pair_message(
        &mut self,
        msg: &crate::pair_message::PairMessage,
    ) -> Result<()> {
        let json = serde_json::to_string(msg).context("serializing pair message")?;
        let conn = self.conn.lock().unwrap();
        // Plain INSERT (no upsert): the (pair_id, seq) PRIMARY KEY must
        // reject a duplicate seq. Silently overwriting would drop a
        // message whose PairMessagePosted event is already in the ledger,
        // leaving a payload_hash an auditor can never satisfy.
        let result = conn.execute(
            "INSERT INTO pair_messages (pair_id, seq, msg_json) VALUES (?1, ?2, ?3)",
            rusqlite::params![msg.pair_id.to_string(), msg.seq as i64, json],
        );
        match result {
            Ok(_) => Ok(()),
            Err(rusqlite::Error::SqliteFailure(e, _))
                if e.code == rusqlite::ErrorCode::ConstraintViolation =>
            {
                Err(anyhow::anyhow!(
                    "sqlite append_pair_message: message at pair={} seq={} already \
                     exists (concurrent append — caller should re-read message_count \
                     and retry)",
                    msg.pair_id, msg.seq
                ))
            }
            Err(e) => Err(anyhow::Error::new(e).context(format!(
                "writing pair message pair={} seq={}", msg.pair_id, msg.seq))),
        }
    }

    async fn list_pair_messages(
        &self,
        pair_id: uuid::Uuid,
        since_seq: Option<u64>,
    ) -> Result<Vec<crate::pair_message::PairMessage>> {
        let conn = self.conn.lock().unwrap();
        // Filter in SQL rather than after the fact — the index behind the
        // PRIMARY KEY makes it a range scan. `since_seq` is exclusive, and
        // ORDER BY seq satisfies the trait's ascending-order contract.
        //
        // The floor is -1, NOT 0, when `since_seq` is None: the first message
        // on a pair gets seq 0 (`seq = pair.message_count`), so a 0 floor
        // would hide it from every unfiltered drain.
        let floor: i64 = match since_seq {
            Some(s) => s as i64,
            None => -1,
        };
        let mut stmt = conn
            .prepare(
                "SELECT msg_json FROM pair_messages
                 WHERE pair_id = ?1 AND seq > ?2
                 ORDER BY seq ASC",
            )
            .context("preparing pair_messages SELECT")?;
        let rows = stmt
            .query_map(
                rusqlite::params![pair_id.to_string(), floor],
                |row| row.get::<_, String>(0),
            )
            .with_context(|| format!("querying pair messages for {pair_id}"))?;
        let mut out = Vec::new();
        for row in rows {
            let json = row.with_context(|| format!("reading pair message row for {pair_id}"))?;
            out.push(
                serde_json::from_str(&json)
                    .with_context(|| format!("parsing pair message for {pair_id}"))?,
            );
        }
        Ok(out)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use uuid::Uuid;

    fn fresh_file_backend() -> (tempfile::TempDir, FileBackend) {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("test-chapter");
        std::fs::create_dir_all(&hub_dir).unwrap();
        let backend = FileBackend::new(HubPaths::new(hub_dir));
        (tmp, backend)
    }

    fn fresh_sqlite_backend() -> (tempfile::TempDir, SqliteBackend) {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("test-chapter");
        std::fs::create_dir_all(&hub_dir).unwrap();
        let backend = SqliteBackend::open(hub_dir.join(SQLITE_DB_FILENAME), None).unwrap();
        (tmp, backend)
    }

    #[tokio::test]
    async fn file_backend_kind_is_file() {
        let (_tmp, b) = fresh_file_backend();
        assert_eq!(b.backend_kind(), BackendKind::File);
    }

    #[tokio::test]
    async fn sqlite_backend_kind_is_sqlite() {
        let (_tmp, b) = fresh_sqlite_backend();
        assert_eq!(b.backend_kind(), BackendKind::Sqlite);
    }

    #[tokio::test]
    async fn file_read_returns_none_when_empty() {
        let (_tmp, b) = fresh_file_backend();
        assert!(b.read_charter().await.unwrap().is_none());
        assert!(b.read_society().await.unwrap().is_none());
        assert!(b.ledger_load_all().await.unwrap().is_empty());
        assert!(b.ledger_is_empty().await.unwrap());
    }

    #[tokio::test]
    async fn sqlite_read_returns_none_when_empty() {
        let (_tmp, b) = fresh_sqlite_backend();
        assert!(b.read_charter().await.unwrap().is_none());
        assert!(b.read_society().await.unwrap().is_none());
        assert!(b.ledger_load_all().await.unwrap().is_empty());
        assert!(b.ledger_is_empty().await.unwrap());
    }

    #[tokio::test]
    async fn file_charter_round_trips() {
        let (_tmp, mut b) = fresh_file_backend();
        let founder = Uuid::new_v4();
        let charter = Charter::found("Test".into(), founder);
        b.write_charter(&charter).await.unwrap();
        let loaded = b.read_charter().await.unwrap().expect("charter present");
        assert_eq!(loaded.hub_name, charter.hub_name);
        assert_eq!(loaded.founding_sovereign_lct_id, founder);
    }

    #[tokio::test]
    async fn sqlite_charter_round_trips() {
        let (_tmp, mut b) = fresh_sqlite_backend();
        let founder = Uuid::new_v4();
        let charter = Charter::found("Test".into(), founder);
        b.write_charter(&charter).await.unwrap();
        let loaded = b.read_charter().await.unwrap().expect("charter present");
        assert_eq!(loaded.hub_name, charter.hub_name);
        assert_eq!(loaded.founding_sovereign_lct_id, founder);
    }

    #[tokio::test]
    async fn sqlite_mailbox_round_trips_and_is_durable() {
        let (_tmp, mut b) = fresh_sqlite_backend();
        assert!(b.mailbox_is_durable(), "sqlcipher backend persists the mailbox");
        assert!(b.mailbox_load_all().await.unwrap().is_empty(), "starts empty");

        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        // Opaque blobs — the store never parses the notice codec.
        b.mailbox_put(alice, b"alice-queue-v1").await.unwrap();
        b.mailbox_put(bob, b"bob-queue-v1").await.unwrap();

        let mut loaded = b.mailbox_load_all().await.unwrap();
        loaded.sort_by_key(|(id, _)| *id);
        let mut expected = vec![(alice, b"alice-queue-v1".to_vec()), (bob, b"bob-queue-v1".to_vec())];
        expected.sort_by_key(|(id, _)| *id);
        assert_eq!(loaded, expected);

        // Overwrite semantics (write-through of the whole queue).
        b.mailbox_put(alice, b"alice-queue-v2").await.unwrap();
        let alice_blob = b.mailbox_load_all().await.unwrap()
            .into_iter().find(|(id, _)| *id == alice).unwrap().1;
        assert_eq!(alice_blob, b"alice-queue-v2".to_vec());

        // Drain deletes; idempotent on a second call.
        b.mailbox_delete(alice).await.unwrap();
        b.mailbox_delete(alice).await.unwrap();
        let remaining = b.mailbox_load_all().await.unwrap();
        assert_eq!(remaining, vec![(bob, b"bob-queue-v1".to_vec())]);
    }

    #[tokio::test]
    async fn file_backend_mailbox_defaults_nondurable() {
        let (_tmp, mut b) = fresh_file_backend();
        assert!(!b.mailbox_is_durable(), "file backend keeps mailbox in-memory only");
        // Default no-ops don't error, load stays empty (graceful degrade).
        b.mailbox_put(Uuid::new_v4(), b"x").await.unwrap();
        assert!(b.mailbox_load_all().await.unwrap().is_empty());
    }

    #[tokio::test]
    async fn file_society_round_trips() {
        let (_tmp, mut b) = fresh_file_backend();
        let founder = Uuid::new_v4();
        let (society, _) = Society::bootstrap("Test".into(), "0".repeat(64), founder);
        b.write_society(&society).await.unwrap();
        let loaded = b.read_society().await.unwrap().expect("society present");
        assert_eq!(loaded.name, society.name);
        assert_eq!(loaded.founder_lct_id, founder);
    }

    #[tokio::test]
    async fn sqlite_society_round_trips() {
        let (_tmp, mut b) = fresh_sqlite_backend();
        let founder = Uuid::new_v4();
        let (society, _) = Society::bootstrap("Test".into(), "0".repeat(64), founder);
        b.write_society(&society).await.unwrap();
        let loaded = b.read_society().await.unwrap().expect("society present");
        assert_eq!(loaded.name, society.name);
        assert_eq!(loaded.founder_lct_id, founder);
    }

    #[tokio::test]
    async fn sqlite_ledger_persists_across_reopen() {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("test-chapter");
        std::fs::create_dir_all(&hub_dir).unwrap();
        let db_path = hub_dir.join(SQLITE_DB_FILENAME);

        // Synthesize a couple of fake ledger entries (just to exercise the
        // store; chain integrity is the HubLedger's responsibility).
        use chrono::Utc;
        use crate::events::HubEvent;
        let founder = Uuid::new_v4();
        let e0 = LedgerEntry {
            index: 0,
            timestamp: Utc::now(),
            prev_hash: "0".repeat(64),
            actor_lct_id: founder,
            event: HubEvent::Genesis {
                hub_name: "X".into(),
                charter_hash: "h".into(),
                founding_sovereign_lct_id: founder,
                created_at: Utc::now(),
            },
            signature: "deadbeef".into(),
            entry_hash: "abc".repeat(20).chars().take(64).collect(),
            proposal_ref: None,
        };

        {
            let mut b = SqliteBackend::open(&db_path, None).unwrap();
            b.ledger_append(&e0).await.unwrap();
            assert!(!b.ledger_is_empty().await.unwrap());
        }

        let b2 = SqliteBackend::open(&db_path, None).unwrap();
        let loaded = b2.ledger_load_all().await.unwrap();
        assert_eq!(loaded.len(), 1);
        assert_eq!(loaded[0].index, 0);
        assert_eq!(loaded[0].actor_lct_id, founder);
    }

    #[tokio::test]
    async fn sqlite_plaintext_migrates_to_encrypted_preserving_rows() {
        let tmp = tempdir().unwrap();
        let db_path = tmp.path().join(SQLITE_DB_FILENAME);
        let founder = Uuid::new_v4();
        let charter = Charter::found("Sealed".into(), founder);

        // 1. Create a PLAINTEXT db (no key) + write a row.
        {
            let mut b = SqliteBackend::open(&db_path, None).unwrap();
            b.write_charter(&charter).await.unwrap();
        }
        assert!(is_plaintext_sqlite(&db_path), "starts as plaintext");

        // 2. Reopen WITH a key → migrates in place, row preserved.
        let key = [7u8; 32];
        {
            let b = SqliteBackend::open(&db_path, Some(key)).unwrap();
            let loaded = b.read_charter().await.unwrap().expect("charter survived migration");
            assert_eq!(loaded.founding_sovereign_lct_id, founder);
        }
        assert!(!is_plaintext_sqlite(&db_path), "now encrypted at rest");

        // 3. Reopen with the SAME key → still readable.
        {
            let b = SqliteBackend::open(&db_path, Some(key)).unwrap();
            assert!(b.read_charter().await.unwrap().is_some());
        }

        // 4. Fail-closed: no key on an encrypted db is refused.
        assert!(SqliteBackend::open(&db_path, None).is_err(), "encrypted db needs a key");

        // 5. Wrong key is refused (SQLCipher rejects at first access).
        assert!(SqliteBackend::open(&db_path, Some([9u8; 32])).is_err(), "wrong key rejected");
    }

    #[tokio::test]
    async fn rekey_store_switches_the_passphrase_key() {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path();
        let db_path = hub_dir.join(SQLITE_DB_FILENAME);
        let old_key = [3u8; 32];
        let new_key = [9u8; 32];
        let founder = Uuid::new_v4();
        let charter = Charter::found("Rekey".into(), founder);

        // Create an encrypted store under old_key + a row.
        {
            let mut b = SqliteBackend::open(&db_path, Some(old_key)).unwrap();
            b.write_charter(&charter).await.unwrap();
        }
        // Rotate old_key → new_key.
        rekey_store(hub_dir, old_key, new_key).unwrap();

        // Old key no longer opens; new key does, with the row intact.
        assert!(SqliteBackend::open(&db_path, Some(old_key)).is_err(), "old key must stop working");
        let b = SqliteBackend::open(&db_path, Some(new_key)).unwrap();
        assert_eq!(b.read_charter().await.unwrap().unwrap().founding_sovereign_lct_id, founder);

        // Re-keying with a wrong "old" key fails (and doesn't corrupt — new key still works).
        assert!(rekey_store(hub_dir, [1u8; 32], [2u8; 32]).is_err());
        assert!(SqliteBackend::open(&db_path, Some(new_key)).is_ok());
    }

    fn make_pair_msg(pair_id: Uuid, seq: u64, payload: &str) -> crate::pair_message::PairMessage {
        crate::pair_message::PairMessage {
            pair_id,
            seq,
            from: Uuid::new_v4(),
            posted_at: chrono::Utc::now(),
            payload: payload.into(),
            ephemeral_pub_hex: None,
        }
    }

    /// The regression that would have shipped: the first message on a pair
    /// gets seq 0 (`seq = pair.message_count`), so an unfiltered drain must
    /// return it. A `seq > 0` floor silently swallows the first message.
    #[tokio::test]
    async fn sqlite_pair_messages_round_trip_including_seq_zero() {
        let (_tmp, mut b) = fresh_sqlite_backend();
        let pair = Uuid::new_v4();
        b.append_pair_message(&make_pair_msg(pair, 0, "first")).await.unwrap();
        b.append_pair_message(&make_pair_msg(pair, 1, "second")).await.unwrap();

        let all = b.list_pair_messages(pair, None).await.unwrap();
        assert_eq!(all.len(), 2, "unfiltered drain must include seq 0");
        assert_eq!(all[0].payload, "first");
        assert_eq!(all[1].payload, "second");

        // since_seq is exclusive.
        let after0 = b.list_pair_messages(pair, Some(0)).await.unwrap();
        assert_eq!(after0.len(), 1);
        assert_eq!(after0[0].seq, 1);

        assert!(b.list_pair_messages(pair, Some(1)).await.unwrap().is_empty());
        // Unknown pair drains empty, not an error.
        assert!(b.list_pair_messages(Uuid::new_v4(), None).await.unwrap().is_empty());
    }

    /// Two writers racing on a seq must produce a loud error, not a silent
    /// overwrite — the ledger already holds a payload_hash for the message
    /// that would be clobbered.
    #[tokio::test]
    async fn sqlite_pair_message_duplicate_seq_errors() {
        let (_tmp, mut b) = fresh_sqlite_backend();
        let pair = Uuid::new_v4();
        b.append_pair_message(&make_pair_msg(pair, 0, "original")).await.unwrap();
        assert!(b.append_pair_message(&make_pair_msg(pair, 0, "clobber")).await.is_err());

        let all = b.list_pair_messages(pair, None).await.unwrap();
        assert_eq!(all.len(), 1);
        assert_eq!(all[0].payload, "original", "loser must not overwrite the winner");
    }

    /// One pair's drain must not leak another pair's messages.
    #[tokio::test]
    async fn sqlite_pair_messages_isolated_per_pair() {
        let (_tmp, mut b) = fresh_sqlite_backend();
        let (a, c) = (Uuid::new_v4(), Uuid::new_v4());
        b.append_pair_message(&make_pair_msg(a, 0, "for-a")).await.unwrap();
        b.append_pair_message(&make_pair_msg(c, 0, "for-c")).await.unwrap();

        let drained = b.list_pair_messages(a, None).await.unwrap();
        assert_eq!(drained.len(), 1);
        assert_eq!(drained[0].payload, "for-a");
    }

    #[tokio::test]
    async fn sqlite_duplicate_index_errors() {
        let (_tmp, mut b) = fresh_sqlite_backend();
        use chrono::Utc;
        use crate::events::HubEvent;
        let founder = Uuid::new_v4();
        let make = |index: u64| LedgerEntry {
            index,
            timestamp: Utc::now(),
            prev_hash: "0".repeat(64),
            actor_lct_id: founder,
            event: HubEvent::Genesis {
                hub_name: "X".into(),
                charter_hash: "h".into(),
                founding_sovereign_lct_id: founder,
                created_at: Utc::now(),
            },
            signature: "".into(),
            entry_hash: "".into(),
            proposal_ref: None,
        };
        b.ledger_append(&make(0)).await.unwrap();
        // Duplicate index: PRIMARY KEY constraint should reject
        assert!(b.ledger_append(&make(0)).await.is_err());
    }

    #[tokio::test]
    async fn open_hub_store_selects_sqlite_when_db_present() {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("test-chapter");
        std::fs::create_dir_all(&hub_dir).unwrap();
        // Create an empty sqlite db
        let _ = SqliteBackend::open(hub_dir.join(SQLITE_DB_FILENAME), None).unwrap();
        // open_hub_store should now pick sqlite
        let store = open_hub_store(&hub_dir).unwrap();
        assert_eq!(store.backend_kind(), BackendKind::Sqlite);
    }

    #[tokio::test]
    async fn open_hub_store_reads_legacy_chapter_db_in_place() {
        // Pre-rename hub dirs have chapter.db (not hub.db). open_hub_store
        // must still detect + open them as sqlite — no forced migration.
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("legacy-hub");
        std::fs::create_dir_all(&hub_dir).unwrap();
        let _ = SqliteBackend::open(hub_dir.join(SQLITE_DB_FILENAME_LEGACY), None).unwrap();
        assert!(!hub_dir.join(SQLITE_DB_FILENAME).exists(), "no hub.db, only legacy chapter.db");
        let store = open_hub_store(&hub_dir).unwrap();
        assert_eq!(store.backend_kind(), BackendKind::Sqlite);
    }

    #[tokio::test]
    async fn open_hub_store_defaults_to_file_when_empty_dir() {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("test-chapter");
        std::fs::create_dir_all(&hub_dir).unwrap();
        let store = open_hub_store(&hub_dir).unwrap();
        assert_eq!(store.backend_kind(), BackendKind::File);
    }

    #[tokio::test]
    async fn open_hub_store_async_reads_config_backend() {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("cfg-backed");
        std::fs::create_dir_all(&hub_dir).unwrap();
        // Write a config that selects sqlite even though no db exists yet.
        let hub_id = Uuid::new_v4();
        let config = crate::hub::HubConfig {
            hub: crate::hub::HubSection { name: "Cfg".into(), id: Some(hub_id) },
            daemon: crate::hub::DaemonSection { mcp_port: 8770 },
            sovereign: crate::hub::SovereignSection {
                lct_path: Some(hub_dir.join("sov.json")),
                ..Default::default()
            },
            storage: Some(crate::hub::StorageSection {
                backend: "sqlite".into(),
                ..Default::default()
            }),
        };
        config.save(hub_dir.join("config.toml")).unwrap();

        let store = open_hub_store_async(&hub_dir).await.unwrap();
        assert_eq!(store.backend_kind(), BackendKind::Sqlite);
    }

    #[tokio::test]
    async fn config_without_storage_section_falls_back_to_disk_detection() {
        // THE pre-change-hub regression (review 2026-07-23): every hub
        // initialized before `[storage]` existed has a config.toml WITHOUT
        // that section, and many of them have a live sqlite `hub.db`.
        // Defaulting the absent section to `file` ignored the db — society
        // reads came back empty and init's idempotency probe could approve a
        // re-genesis over a live hub. Absent section MUST mean disk
        // auto-detection.
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("pre-change-sqlite-hub");
        std::fs::create_dir_all(&hub_dir).unwrap();
        // config.toml with NO [storage] section (what a pre-change init wrote).
        let config = crate::hub::HubConfig {
            hub: crate::hub::HubSection { name: "Legacy".into(), id: None },
            daemon: crate::hub::DaemonSection { mcp_port: 8770 },
            sovereign: crate::hub::SovereignSection {
                lct_path: Some(hub_dir.join("sov.json")),
                ..Default::default()
            },
            storage: None,
        };
        config.save(hub_dir.join("config.toml")).unwrap();
        let toml_text = std::fs::read_to_string(hub_dir.join("config.toml")).unwrap();
        assert!(
            !toml_text.contains("[storage]"),
            "None must serialize to NO [storage] section, got:\n{toml_text}"
        );
        // A live sqlite db on disk (created the real way, then closed)...
        drop(SqliteBackend::open(hub_dir.join(SQLITE_DB_FILENAME), None).unwrap());
        // ...must be auto-detected despite the section-less config.
        let store = open_hub_store_with_key(&hub_dir, None).unwrap();
        assert_eq!(
            store.backend_kind(),
            BackendKind::Sqlite,
            "sqlite hub with a section-less config must resolve to sqlite, not file"
        );
        let store = open_hub_store_with_key_async(&hub_dir, None).await.unwrap();
        assert_eq!(store.backend_kind(), BackendKind::Sqlite, "async path too");
    }

    #[tokio::test]
    async fn open_hub_store_async_dynamodb_errors_without_feature() {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("ddb-backed");
        std::fs::create_dir_all(&hub_dir).unwrap();
        let hub_id = Uuid::new_v4();
        let config = crate::hub::HubConfig {
            hub: crate::hub::HubSection { name: "DDB".into(), id: Some(hub_id) },
            daemon: crate::hub::DaemonSection { mcp_port: 8770 },
            sovereign: crate::hub::SovereignSection {
                lct_path: Some(hub_dir.join("sov.json")),
                ..Default::default()
            },
            storage: Some(crate::hub::StorageSection {
                backend: "dynamodb".into(),
                dynamodb_table: Some("web4-hubs".into()),
                ..Default::default()
            }),
        };
        config.save(hub_dir.join("config.toml")).unwrap();

        let result = open_hub_store_async(&hub_dir).await;
        let msg = match result {
            Err(e) => format!("{}", e),
            Ok(_) => panic!("expected dynamodb feature-gated error"),
        };
        assert!(
            msg.contains("dynamodb") && msg.contains("feature"),
            "expected feature-gated dynamodb error, got: {}", msg
        );
    }

    #[tokio::test]
    async fn migrate_file_to_sqlite_round_trips_state() {
        use chrono::Utc;
        use crate::events::HubEvent;

        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("chap");
        std::fs::create_dir_all(&hub_dir).unwrap();

        // Build a file-backed chapter with charter + society + 3 ledger entries
        let founder = Uuid::new_v4();
        let charter = Charter::found("Migrate Test".into(), founder);
        let (society, _) = Society::bootstrap("Migrate Test".into(), "h".repeat(64), founder);
        let entries: Vec<LedgerEntry> = (0..3).map(|i| LedgerEntry {
            index: i,
            timestamp: Utc::now(),
            prev_hash: if i == 0 { "0".repeat(64) } else { format!("h{}", i - 1) },
            actor_lct_id: founder,
            event: HubEvent::Genesis {
                hub_name: "Migrate Test".into(),
                charter_hash: "h".into(),
                founding_sovereign_lct_id: founder,
                created_at: Utc::now(),
            },
            signature: format!("sig{}", i),
            entry_hash: format!("h{}", i),
            proposal_ref: None,
        }).collect();

        {
            let mut src = FileBackend::new(HubPaths::new(hub_dir.clone()));
            src.write_charter(&charter).await.unwrap();
            src.write_society(&society).await.unwrap();
            for e in &entries {
                src.ledger_append(e).await.unwrap();
            }
        }

        // Migrate file → sqlite
        let result = migrate_hub(&hub_dir, BackendKind::Sqlite).await.unwrap();
        assert_eq!(result.source_backend, BackendKind::File);
        assert_eq!(result.target_backend, BackendKind::Sqlite);
        assert!(result.charter_copied);
        assert!(result.society_copied);
        assert_eq!(result.ledger_entries_copied, 3);
        assert!(!result.preserved_artifacts.is_empty(),
            "source artifacts should be renamed for rollback");

        // Auto-detect should now resolve sqlite
        let after = open_hub_store(&hub_dir).unwrap();
        assert_eq!(after.backend_kind(), BackendKind::Sqlite);

        // Charter + society + ledger byte-identical
        let after_charter = after.read_charter().await.unwrap().expect("charter");
        assert_eq!(after_charter.hub_name, charter.hub_name);
        let after_society = after.read_society().await.unwrap().expect("society");
        assert_eq!(after_society.lct_id, society.lct_id);
        let after_ledger = after.ledger_load_all().await.unwrap();
        assert_eq!(after_ledger.len(), 3);
        for (i, e) in after_ledger.iter().enumerate() {
            assert_eq!(e.index, i as u64);
            assert_eq!(e.signature, entries[i].signature);
            assert_eq!(e.entry_hash, entries[i].entry_hash);
        }
    }

    #[tokio::test]
    async fn migrate_same_backend_is_noop() {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("chap");
        std::fs::create_dir_all(&hub_dir).unwrap();
        // Empty dir → file-backed default
        let result = migrate_hub(&hub_dir, BackendKind::File).await.unwrap();
        assert_eq!(result.source_backend, result.target_backend);
        assert_eq!(result.ledger_entries_copied, 0);
        assert!(!result.charter_copied);
        assert!(!result.society_copied);
        assert!(result.preserved_artifacts.is_empty());
    }

    #[tokio::test]
    async fn file_law_round_trips() {
        let (_tmp, mut b) = fresh_file_backend();
        assert!(b.read_law().await.unwrap().is_none());
        b.write_law("version: \"1.0.0\"\n").await.unwrap();
        let back = b.read_law().await.unwrap().unwrap();
        assert_eq!(back, "version: \"1.0.0\"\n");
    }

    #[tokio::test]
    async fn sqlite_law_round_trips() {
        let (_tmp, mut b) = fresh_sqlite_backend();
        assert!(b.read_law().await.unwrap().is_none());
        b.write_law("version: \"1.0.0\"\nnorms: []\n").await.unwrap();
        let back = b.read_law().await.unwrap().unwrap();
        assert!(back.contains("1.0.0"));
    }

    #[tokio::test]
    async fn file_law_overwrites_on_amendment() {
        let (_tmp, mut b) = fresh_file_backend();
        b.write_law("version: \"1.0.0\"\n").await.unwrap();
        b.write_law("version: \"1.1.0\"\n").await.unwrap();
        let back = b.read_law().await.unwrap().unwrap();
        assert!(back.contains("1.1.0"));
        assert!(!back.contains("1.0.0"));
    }

    #[tokio::test]
    async fn backend_kind_from_str_parses_both() {
        use std::str::FromStr;
        assert_eq!(BackendKind::from_str("file").unwrap(), BackendKind::File);
        assert_eq!(BackendKind::from_str("sqlite").unwrap(), BackendKind::Sqlite);
        assert_eq!(BackendKind::from_str("SQLITE").unwrap(), BackendKind::Sqlite);
        assert!(BackendKind::from_str("xyz").is_err());
    }
}
