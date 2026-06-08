// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Chapter storage backend abstraction (V2-2).
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
//! The abstraction here is intentionally narrow: chapter charter, chapter
//! society state, and the chapter event ledger. That is the entire surface
//! of chapter-owned persistent state. Everything else is either:
//!
//! - **Operator-owned config** (`config.toml`) — stays file-based, not part of this trait
//! - **Secret material** (private keys, vault contents) — per architecture
//!   commitment #8, secrets live ONLY in Hestia's vault, never in chapter
//!   storage. The trait surface explicitly does not expose any secret-
//!   handling operations.
//!
//! ## Posture (per architecture commitment #8)
//!
//! Chapter storage is **secrets-free by design**. Everything in this trait
//! is signed (for integrity) but not encrypted (for confidentiality of the
//! data itself). Confidentiality, where needed, comes from the vault's
//! authority+need-to-know gate at the access boundary — not from sealing
//! bytes in storage.
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
    // Future: Postgres, S3ColdArchive, etc.
}

impl BackendKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            BackendKind::File => "file",
            BackendKind::Sqlite => "sqlite",
        }
    }
}

/// The chapter persistence surface.
///
/// Implementations own the bytes; callers (HubLedger, init_chapter,
/// HubSession) own invariants. This trait does **no** crypto or chain
/// validation — that lives in the ledger module. It does **no** secret
/// handling — that lives in the vault (Hestia).
pub trait HubStore: Send {
    fn backend_kind(&self) -> BackendKind;

    // ----- Charter (immutable post-genesis) -----

    /// Read the charter if present.
    fn read_charter(&self) -> Result<Option<Charter>>;

    /// Write the charter. Callers should call this exactly once (during
    /// init); a charter is immutable post-genesis. Implementations may
    /// refuse overwrites for safety.
    fn write_charter(&mut self, charter: &Charter) -> Result<()>;

    // ----- Society state (evolves as acts append) -----

    /// Read the society if present.
    fn read_society(&self) -> Result<Option<Society>>;

    /// Write/overwrite the society state.
    fn write_society(&mut self, society: &Society) -> Result<()>;

    // ----- Ledger (append-only, hash-chained) -----

    /// Load all ledger entries in order. Implementations may stream or
    /// fully load; current callers expect a Vec.
    fn ledger_load_all(&self) -> Result<Vec<LedgerEntry>>;

    /// Append one already-validated entry to the ledger. The entry's
    /// signature + entry_hash + prev_hash + index are computed by the
    /// caller (HubLedger); the store just persists.
    fn ledger_append(&mut self, entry: &LedgerEntry) -> Result<()>;

    /// True iff the ledger has zero entries. Used by callers to detect
    /// "fresh chapter, needs Genesis" without round-tripping the full list.
    fn ledger_is_empty(&self) -> Result<bool> {
        Ok(self.ledger_load_all()?.is_empty())
    }

    // ----- Law (V2-8: signed YAML, amended via LawAmended events) -----

    /// Read the current chapter law YAML, or None if no law has been
    /// set yet. Returns the raw bytes (not the parsed [`crate::law::Law`])
    /// so the store layer stays parser-agnostic.
    fn read_law(&self) -> Result<Option<String>> {
        Ok(None) // Default: backends not yet supporting law return None
    }

    /// Write/overwrite the current chapter law. Callers should also
    /// append a [`crate::events::HubEvent::LawAmended`] event to
    /// the ledger so the amendment is part of the audit trail.
    fn write_law(&mut self, _yaml: &str) -> Result<()> {
        anyhow::bail!("this backend does not yet support law storage")
    }

    // ----- Council proposals (V2-9 Phase 2) -----

    /// Persist a council proposal (insert-or-update). Proposals carry
    /// council-holder signatures awaiting M-of-N threshold; storage
    /// is separate from the ledger because they're not yet committed
    /// acts. Implementations that don't support council proposals
    /// reject calls so the operator gets a clear error rather than a
    /// silent no-op.
    fn write_proposal(&mut self, _proposal: &crate::proposal::CouncilProposal) -> Result<()> {
        anyhow::bail!("this backend does not yet support council proposals")
    }

    /// Read a single proposal by id.
    fn read_proposal(&self, _id: uuid::Uuid) -> Result<Option<crate::proposal::CouncilProposal>> {
        anyhow::bail!("this backend does not yet support council proposals")
    }

    /// List all currently-stored proposals (open, committed,
    /// rejected, expired). Caller filters by status if needed.
    fn list_proposals(&self) -> Result<Vec<crate::proposal::CouncilProposal>> {
        anyhow::bail!("this backend does not yet support council proposals")
    }

    /// Remove a proposal. Used by the cleanup pass that drops
    /// expired proposals on the next propose/sign call. Idempotent.
    fn delete_proposal(&mut self, _id: uuid::Uuid) -> Result<()> {
        anyhow::bail!("this backend does not yet support council proposals")
    }
}

/// Default SQLite filename inside a chapter dir.
pub const SQLITE_DB_FILENAME: &str = "chapter.db";

/// Open a `HubStore` for the given chapter dir. Backend selection:
///
/// 1. If `<chapter-dir>/chapter.db` exists → SqliteBackend.
/// 2. Else if `<chapter-dir>/society.json` (or any MVP file) exists → FileBackend.
/// 3. Else (fresh chapter) → FileBackend default (MVP-compatible).
///
/// To force a specific backend at create time, use [`open_chapter_store_with`].
pub fn open_chapter_store(hub_dir: impl AsRef<Path>) -> Result<Box<dyn HubStore>> {
    let hub_dir = hub_dir.as_ref();
    let paths = HubPaths::new(hub_dir.to_path_buf());
    let db_path = hub_dir.join(SQLITE_DB_FILENAME);

    if db_path.exists() {
        Ok(Box::new(SqliteBackend::open(&db_path)?))
    } else {
        Ok(Box::new(FileBackend::new(paths)))
    }
}

/// Open a `HubStore` for the given chapter dir, forcing the backend
/// kind. Used by `hub init --storage <kind>` and the migration tool.
pub fn open_chapter_store_with(
    hub_dir: impl AsRef<Path>,
    kind: BackendKind,
) -> Result<Box<dyn HubStore>> {
    let hub_dir = hub_dir.as_ref();
    let paths = HubPaths::new(hub_dir.to_path_buf());
    match kind {
        BackendKind::File => Ok(Box::new(FileBackend::new(paths))),
        BackendKind::Sqlite => {
            std::fs::create_dir_all(hub_dir)
                .with_context(|| format!("creating chapter dir {}", hub_dir.display()))?;
            let db_path = hub_dir.join(SQLITE_DB_FILENAME);
            Ok(Box::new(SqliteBackend::open(&db_path)?))
        }
    }
}

impl std::str::FromStr for BackendKind {
    type Err = anyhow::Error;
    fn from_str(s: &str) -> Result<Self> {
        match s.to_ascii_lowercase().as_str() {
            "file" | "files" | "jsonl" => Ok(BackendKind::File),
            "sqlite" | "sqlite3" | "db" => Ok(BackendKind::Sqlite),
            other => Err(anyhow::anyhow!(
                "unknown storage backend '{}'; expected 'file' or 'sqlite'",
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

impl HubStore for FileBackend {
    fn backend_kind(&self) -> BackendKind {
        BackendKind::File
    }

    fn read_charter(&self) -> Result<Option<Charter>> {
        let path = self.charter_path();
        if !path.exists() {
            return Ok(None);
        }
        let charter = Charter::load(&path)
            .with_context(|| format!("loading charter from {}", path.display()))?;
        Ok(Some(charter))
    }

    fn write_charter(&mut self, charter: &Charter) -> Result<()> {
        let path = self.charter_path();
        Self::ensure_parent(&path)?;
        charter.save(&path)
            .with_context(|| format!("writing charter to {}", path.display()))?;
        Ok(())
    }

    fn read_society(&self) -> Result<Option<Society>> {
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

    fn write_society(&mut self, society: &Society) -> Result<()> {
        let path = self.society_path();
        Self::ensure_parent(&path)?;
        let json = serde_json::to_string_pretty(society)
            .context("serializing society")?;
        std::fs::write(&path, json)
            .with_context(|| format!("writing society to {}", path.display()))?;
        Ok(())
    }

    fn ledger_load_all(&self) -> Result<Vec<LedgerEntry>> {
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

    fn ledger_append(&mut self, entry: &LedgerEntry) -> Result<()> {
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

    fn read_law(&self) -> Result<Option<String>> {
        let path = self.law_path();
        if path.exists() {
            return std::fs::read_to_string(&path)
                .map(Some)
                .with_context(|| format!("reading law from {}", path.display()));
        }
        // Back-compat: hub dirs created before the chapter→hub rename
        // wrote `chapter-law.yaml`. If the new name isn't present but
        // the old one is, read the old one. (write_law always writes
        // the new name; next set-law migrates the file.)
        let legacy = self.paths.root.join("chapter-law.yaml");
        if legacy.exists() {
            return std::fs::read_to_string(&legacy)
                .map(Some)
                .with_context(|| format!("reading legacy chapter-law from {}", legacy.display()));
        }
        Ok(None)
    }

    fn write_law(&mut self, yaml: &str) -> Result<()> {
        let path = self.law_path();
        Self::ensure_parent(&path)?;
        std::fs::write(&path, yaml)
            .with_context(|| format!("writing law to {}", path.display()))
    }

    // ----- V2-9 Phase 2: council proposals -----

    fn write_proposal(&mut self, proposal: &crate::proposal::CouncilProposal) -> Result<()> {
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

    fn read_proposal(&self, id: uuid::Uuid) -> Result<Option<crate::proposal::CouncilProposal>> {
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

    fn list_proposals(&self) -> Result<Vec<crate::proposal::CouncilProposal>> {
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

    fn delete_proposal(&mut self, id: uuid::Uuid) -> Result<()> {
        let path = self.paths.root.join("proposals").join(format!("{}.json", id));
        if path.exists() {
            std::fs::remove_file(&path)
                .with_context(|| format!("removing proposal {}", path.display()))?;
        }
        Ok(())
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
    conn: rusqlite::Connection,
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
    pub fn open(db_path: impl AsRef<Path>) -> Result<Self> {
        let db_path = db_path.as_ref().to_path_buf();
        if let Some(parent) = db_path.parent() {
            if !parent.as_os_str().is_empty() && !parent.exists() {
                std::fs::create_dir_all(parent)
                    .with_context(|| format!("creating parent dir {}", parent.display()))?;
            }
        }
        let conn = rusqlite::Connection::open(&db_path)
            .with_context(|| format!("opening sqlite db at {}", db_path.display()))?;
        // Enforce foreign keys + reasonable durability defaults
        conn.execute_batch(
            "PRAGMA foreign_keys = ON;
             PRAGMA journal_mode = WAL;
             PRAGMA synchronous = NORMAL;",
        ).context("setting sqlite pragmas")?;
        // Schema
        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS metadata (
                 key   TEXT PRIMARY KEY,
                 value TEXT NOT NULL
             );
             CREATE TABLE IF NOT EXISTS ledger_entries (
                 idx        INTEGER PRIMARY KEY,
                 entry_json TEXT NOT NULL
             );",
        ).context("initializing sqlite schema")?;
        Ok(Self { conn, db_path })
    }

    pub fn db_path(&self) -> &Path {
        &self.db_path
    }

    fn read_meta(&self, key: &str) -> Result<Option<String>> {
        let mut stmt = self.conn
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
        self.conn
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

/// Outcome of [`migrate_chapter`]. Caller decides how to surface this.
#[derive(Debug)]
pub struct MigrationResult {
    pub source_backend: BackendKind,
    pub target_backend: BackendKind,
    pub charter_copied: bool,
    pub society_copied: bool,
    pub ledger_entries_copied: usize,
    /// Renamed pre-migration artifacts (paths relative to chapter dir),
    /// preserved so operators can roll back if needed.
    pub preserved_artifacts: Vec<PathBuf>,
}

/// Migrate a chapter from its current backend to `target_backend`.
///
/// Algorithm:
/// 1. Auto-detect source backend at `hub_dir`.
/// 2. If source == target, no-op (returns OK with zero-copied counters).
/// 3. Open target backend (forced kind via [`open_chapter_store_with`]).
///    For sqlite, this creates `chapter.db`.
/// 4. Copy charter (if present) → target.
/// 5. Copy society (if present) → target.
/// 6. Walk ledger entries in order from source; append each to target.
///    No re-signing — entries copy byte-for-byte (canonical JSON).
/// 7. Rename source artifacts to `<name>.pre-migration` so they don't
///    interfere with future auto-detection but remain recoverable.
///
/// The caller (typically `hub migrate` CLI) should run a verify-ledger
/// pass against the chapter dir after this returns to confirm chain
/// integrity is intact on the target backend.
///
/// Note: this function does NOT touch identity files, config.toml, or
/// anything else outside the chapter storage abstraction. Those stay
/// where they were.
pub fn migrate_chapter(
    hub_dir: impl AsRef<Path>,
    target_backend: BackendKind,
) -> Result<MigrationResult> {
    let hub_dir = hub_dir.as_ref();
    if !hub_dir.exists() {
        anyhow::bail!("chapter dir {} does not exist", hub_dir.display());
    }

    // 1. Auto-detect source.
    let source = open_chapter_store(hub_dir)
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
    let charter = source.read_charter().context("reading source charter")?;
    let society = source.read_society().context("reading source society")?;
    let ledger_entries = source.ledger_load_all().context("reading source ledger")?;

    // Drop source handle BEFORE creating target — particularly important
    // for sqlite, where a stale connection could conflict on WAL files.
    drop(source);

    // 3. Open target.
    let mut target = open_chapter_store_with(hub_dir, target_backend)
        .with_context(|| format!("opening target store ({:?})", target_backend))?;

    // 4-6. Copy state.
    let mut charter_copied = false;
    if let Some(c) = charter {
        target.write_charter(&c).context("writing charter to target")?;
        charter_copied = true;
    }
    let mut society_copied = false;
    if let Some(s) = society {
        target.write_society(&s).context("writing society to target")?;
        society_copied = true;
    }
    let entries_copied = ledger_entries.len();
    for entry in &ledger_entries {
        target.ledger_append(entry)
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
            for sidecar in &["chapter.db-wal", "chapter.db-shm"] {
                let p = hub_dir.join(sidecar);
                if p.exists() {
                    let backup = hub_dir.join(format!("{}.pre-migration", sidecar));
                    std::fs::rename(&p, &backup)
                        .with_context(|| format!("renaming {} to backup", p.display()))?;
                    preserved.push(backup);
                }
            }
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

impl HubStore for SqliteBackend {
    fn backend_kind(&self) -> BackendKind {
        BackendKind::Sqlite
    }

    fn read_charter(&self) -> Result<Option<Charter>> {
        match self.read_meta("charter")? {
            None => Ok(None),
            Some(json) => {
                let charter: Charter = serde_json::from_str(&json)
                    .context("parsing charter from sqlite metadata")?;
                Ok(Some(charter))
            }
        }
    }

    fn write_charter(&mut self, charter: &Charter) -> Result<()> {
        let json = serde_json::to_string(charter).context("serializing charter")?;
        self.write_meta("charter", &json)
    }

    fn read_society(&self) -> Result<Option<Society>> {
        match self.read_meta("society")? {
            None => Ok(None),
            Some(json) => {
                let society: Society = serde_json::from_str(&json)
                    .context("parsing society from sqlite metadata")?;
                Ok(Some(society))
            }
        }
    }

    fn write_society(&mut self, society: &Society) -> Result<()> {
        let json = serde_json::to_string(society).context("serializing society")?;
        self.write_meta("society", &json)
    }

    fn ledger_load_all(&self) -> Result<Vec<LedgerEntry>> {
        let mut stmt = self.conn
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

    fn ledger_append(&mut self, entry: &LedgerEntry) -> Result<()> {
        let json = serde_json::to_string(entry).context("serializing ledger entry")?;
        self.conn
            .execute(
                "INSERT INTO ledger_entries (idx, entry_json) VALUES (?1, ?2)",
                rusqlite::params![entry.index as i64, json],
            )
            .with_context(|| format!("inserting ledger entry idx={}", entry.index))?;
        Ok(())
    }

    fn ledger_is_empty(&self) -> Result<bool> {
        let count: i64 = self.conn
            .query_row(
                "SELECT COUNT(*) FROM ledger_entries",
                [],
                |row| row.get(0),
            )
            .context("counting ledger entries")?;
        Ok(count == 0)
    }

    fn read_law(&self) -> Result<Option<String>> {
        self.read_meta("law")
    }

    fn write_law(&mut self, yaml: &str) -> Result<()> {
        self.write_meta("law", yaml)
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
        let backend = SqliteBackend::open(hub_dir.join(SQLITE_DB_FILENAME)).unwrap();
        (tmp, backend)
    }

    #[test]
    fn file_backend_kind_is_file() {
        let (_tmp, b) = fresh_file_backend();
        assert_eq!(b.backend_kind(), BackendKind::File);
    }

    #[test]
    fn sqlite_backend_kind_is_sqlite() {
        let (_tmp, b) = fresh_sqlite_backend();
        assert_eq!(b.backend_kind(), BackendKind::Sqlite);
    }

    #[test]
    fn file_read_returns_none_when_empty() {
        let (_tmp, b) = fresh_file_backend();
        assert!(b.read_charter().unwrap().is_none());
        assert!(b.read_society().unwrap().is_none());
        assert!(b.ledger_load_all().unwrap().is_empty());
        assert!(b.ledger_is_empty().unwrap());
    }

    #[test]
    fn sqlite_read_returns_none_when_empty() {
        let (_tmp, b) = fresh_sqlite_backend();
        assert!(b.read_charter().unwrap().is_none());
        assert!(b.read_society().unwrap().is_none());
        assert!(b.ledger_load_all().unwrap().is_empty());
        assert!(b.ledger_is_empty().unwrap());
    }

    #[test]
    fn file_charter_round_trips() {
        let (_tmp, mut b) = fresh_file_backend();
        let founder = Uuid::new_v4();
        let charter = Charter::found("Test".into(), founder);
        b.write_charter(&charter).unwrap();
        let loaded = b.read_charter().unwrap().expect("charter present");
        assert_eq!(loaded.hub_name, charter.hub_name);
        assert_eq!(loaded.founding_sovereign_lct_id, founder);
    }

    #[test]
    fn sqlite_charter_round_trips() {
        let (_tmp, mut b) = fresh_sqlite_backend();
        let founder = Uuid::new_v4();
        let charter = Charter::found("Test".into(), founder);
        b.write_charter(&charter).unwrap();
        let loaded = b.read_charter().unwrap().expect("charter present");
        assert_eq!(loaded.hub_name, charter.hub_name);
        assert_eq!(loaded.founding_sovereign_lct_id, founder);
    }

    #[test]
    fn file_society_round_trips() {
        let (_tmp, mut b) = fresh_file_backend();
        let founder = Uuid::new_v4();
        let (society, _) = Society::bootstrap("Test".into(), "0".repeat(64), founder);
        b.write_society(&society).unwrap();
        let loaded = b.read_society().unwrap().expect("society present");
        assert_eq!(loaded.name, society.name);
        assert_eq!(loaded.founder_lct_id, founder);
    }

    #[test]
    fn sqlite_society_round_trips() {
        let (_tmp, mut b) = fresh_sqlite_backend();
        let founder = Uuid::new_v4();
        let (society, _) = Society::bootstrap("Test".into(), "0".repeat(64), founder);
        b.write_society(&society).unwrap();
        let loaded = b.read_society().unwrap().expect("society present");
        assert_eq!(loaded.name, society.name);
        assert_eq!(loaded.founder_lct_id, founder);
    }

    #[test]
    fn sqlite_ledger_persists_across_reopen() {
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
        };

        {
            let mut b = SqliteBackend::open(&db_path).unwrap();
            b.ledger_append(&e0).unwrap();
            assert!(!b.ledger_is_empty().unwrap());
        }

        let b2 = SqliteBackend::open(&db_path).unwrap();
        let loaded = b2.ledger_load_all().unwrap();
        assert_eq!(loaded.len(), 1);
        assert_eq!(loaded[0].index, 0);
        assert_eq!(loaded[0].actor_lct_id, founder);
    }

    #[test]
    fn sqlite_duplicate_index_errors() {
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
        };
        b.ledger_append(&make(0)).unwrap();
        // Duplicate index: PRIMARY KEY constraint should reject
        assert!(b.ledger_append(&make(0)).is_err());
    }

    #[test]
    fn open_chapter_store_selects_sqlite_when_db_present() {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("test-chapter");
        std::fs::create_dir_all(&hub_dir).unwrap();
        // Create an empty sqlite db
        let _ = SqliteBackend::open(hub_dir.join(SQLITE_DB_FILENAME)).unwrap();
        // open_chapter_store should now pick sqlite
        let store = open_chapter_store(&hub_dir).unwrap();
        assert_eq!(store.backend_kind(), BackendKind::Sqlite);
    }

    #[test]
    fn open_chapter_store_defaults_to_file_when_empty_dir() {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("test-chapter");
        std::fs::create_dir_all(&hub_dir).unwrap();
        let store = open_chapter_store(&hub_dir).unwrap();
        assert_eq!(store.backend_kind(), BackendKind::File);
    }

    #[test]
    fn migrate_file_to_sqlite_round_trips_state() {
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
        }).collect();

        {
            let mut src = FileBackend::new(HubPaths::new(hub_dir.clone()));
            src.write_charter(&charter).unwrap();
            src.write_society(&society).unwrap();
            for e in &entries {
                src.ledger_append(e).unwrap();
            }
        }

        // Migrate file → sqlite
        let result = migrate_chapter(&hub_dir, BackendKind::Sqlite).unwrap();
        assert_eq!(result.source_backend, BackendKind::File);
        assert_eq!(result.target_backend, BackendKind::Sqlite);
        assert!(result.charter_copied);
        assert!(result.society_copied);
        assert_eq!(result.ledger_entries_copied, 3);
        assert!(!result.preserved_artifacts.is_empty(),
            "source artifacts should be renamed for rollback");

        // Auto-detect should now resolve sqlite
        let after = open_chapter_store(&hub_dir).unwrap();
        assert_eq!(after.backend_kind(), BackendKind::Sqlite);

        // Charter + society + ledger byte-identical
        let after_charter = after.read_charter().unwrap().expect("charter");
        assert_eq!(after_charter.hub_name, charter.hub_name);
        let after_society = after.read_society().unwrap().expect("society");
        assert_eq!(after_society.lct_id, society.lct_id);
        let after_ledger = after.ledger_load_all().unwrap();
        assert_eq!(after_ledger.len(), 3);
        for (i, e) in after_ledger.iter().enumerate() {
            assert_eq!(e.index, i as u64);
            assert_eq!(e.signature, entries[i].signature);
            assert_eq!(e.entry_hash, entries[i].entry_hash);
        }
    }

    #[test]
    fn migrate_same_backend_is_noop() {
        let tmp = tempdir().unwrap();
        let hub_dir = tmp.path().join("chap");
        std::fs::create_dir_all(&hub_dir).unwrap();
        // Empty dir → file-backed default
        let result = migrate_chapter(&hub_dir, BackendKind::File).unwrap();
        assert_eq!(result.source_backend, result.target_backend);
        assert_eq!(result.ledger_entries_copied, 0);
        assert!(!result.charter_copied);
        assert!(!result.society_copied);
        assert!(result.preserved_artifacts.is_empty());
    }

    #[test]
    fn file_law_round_trips() {
        let (_tmp, mut b) = fresh_file_backend();
        assert!(b.read_law().unwrap().is_none());
        b.write_law("version: \"1.0.0\"\n").unwrap();
        let back = b.read_law().unwrap().unwrap();
        assert_eq!(back, "version: \"1.0.0\"\n");
    }

    #[test]
    fn sqlite_law_round_trips() {
        let (_tmp, mut b) = fresh_sqlite_backend();
        assert!(b.read_law().unwrap().is_none());
        b.write_law("version: \"1.0.0\"\nnorms: []\n").unwrap();
        let back = b.read_law().unwrap().unwrap();
        assert!(back.contains("1.0.0"));
    }

    #[test]
    fn file_law_overwrites_on_amendment() {
        let (_tmp, mut b) = fresh_file_backend();
        b.write_law("version: \"1.0.0\"\n").unwrap();
        b.write_law("version: \"1.1.0\"\n").unwrap();
        let back = b.read_law().unwrap().unwrap();
        assert!(back.contains("1.1.0"));
        assert!(!back.contains("1.0.0"));
    }

    #[test]
    fn backend_kind_from_str_parses_both() {
        use std::str::FromStr;
        assert_eq!(BackendKind::from_str("file").unwrap(), BackendKind::File);
        assert_eq!(BackendKind::from_str("sqlite").unwrap(), BackendKind::Sqlite);
        assert_eq!(BackendKind::from_str("SQLITE").unwrap(), BackendKind::Sqlite);
        assert!(BackendKind::from_str("xyz").is_err());
    }
}
