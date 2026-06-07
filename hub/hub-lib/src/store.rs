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

use crate::chapter::ChapterPaths;
use crate::charter::Charter;
use crate::ledger::LedgerEntry;
use web4_core::society::Society;

/// What kind of backend a [`ChapterStore`] is. Useful for diagnostics +
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
/// Implementations own the bytes; callers (ChapterLedger, init_chapter,
/// ChapterSession) own invariants. This trait does **no** crypto or chain
/// validation — that lives in the ledger module. It does **no** secret
/// handling — that lives in the vault (Hestia).
pub trait ChapterStore: Send {
    fn backend_kind(&self) -> BackendKind;

    // ----- Charter (immutable post-genesis) -----

    /// Read the charter if present.
    fn read_charter(&self) -> Result<Option<Charter>>;

    /// Write the charter. Callers should call this exactly once (during
    /// init); a charter is immutable post-genesis. Implementations may
    /// refuse overwrites for safety.
    fn write_charter(&mut self, charter: &Charter) -> Result<()>;

    // ----- Society state (mutates as roles/members change) -----

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
    /// caller (ChapterLedger); the store just persists.
    fn ledger_append(&mut self, entry: &LedgerEntry) -> Result<()>;

    /// True iff the ledger has zero entries. Used by callers to detect
    /// "fresh chapter, needs Genesis" without round-tripping the full list.
    fn ledger_is_empty(&self) -> Result<bool> {
        Ok(self.ledger_load_all()?.is_empty())
    }
}

/// Open a `ChapterStore` for the given chapter dir, choosing backend by
/// what's already on disk. If neither a `chapter.db` nor a `society.json`
/// is present, defaults to file-backed for V2-2 Step A.
///
/// V2-2 Step B will look at `config.toml`'s `[storage]` section to decide.
pub fn open_chapter_store(chapter_dir: impl AsRef<Path>) -> Result<Box<dyn ChapterStore>> {
    let paths = ChapterPaths::new(chapter_dir.as_ref().to_path_buf());
    Ok(Box::new(FileBackend::new(paths)))
}

// ============================================================================
// FileBackend
// ============================================================================

/// File-backed [`ChapterStore`] — wraps the MVP's JSON/JSONL files.
///
/// Layout (unchanged from MVP):
/// - `charter.json` — Charter
/// - `society.json` — Society
/// - `ledger.jsonl` — one LedgerEntry per line
#[derive(Debug)]
pub struct FileBackend {
    paths: ChapterPaths,
}

impl FileBackend {
    pub fn new(paths: ChapterPaths) -> Self {
        Self { paths }
    }

    pub fn paths(&self) -> &ChapterPaths {
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

impl ChapterStore for FileBackend {
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
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use uuid::Uuid;

    fn fresh_backend() -> (tempfile::TempDir, FileBackend) {
        let tmp = tempdir().unwrap();
        let chapter_dir = tmp.path().join("test-chapter");
        std::fs::create_dir_all(&chapter_dir).unwrap();
        let backend = FileBackend::new(ChapterPaths::new(chapter_dir));
        (tmp, backend)
    }

    #[test]
    fn file_backend_kind_is_file() {
        let (_tmp, b) = fresh_backend();
        assert_eq!(b.backend_kind(), BackendKind::File);
    }

    #[test]
    fn read_returns_none_when_empty() {
        let (_tmp, b) = fresh_backend();
        assert!(b.read_charter().unwrap().is_none());
        assert!(b.read_society().unwrap().is_none());
        assert!(b.ledger_load_all().unwrap().is_empty());
        assert!(b.ledger_is_empty().unwrap());
    }

    #[test]
    fn charter_round_trips() {
        let (_tmp, mut b) = fresh_backend();
        let founder = Uuid::new_v4();
        let charter = Charter::found("Test".into(), founder);
        b.write_charter(&charter).unwrap();
        let loaded = b.read_charter().unwrap().expect("charter present");
        assert_eq!(loaded.chapter_name, charter.chapter_name);
        assert_eq!(loaded.founding_sovereign_lct_id, founder);
    }

    #[test]
    fn society_round_trips() {
        let (_tmp, mut b) = fresh_backend();
        let founder = Uuid::new_v4();
        let (society, _) = Society::bootstrap("Test".into(), "0".repeat(64), founder);
        b.write_society(&society).unwrap();
        let loaded = b.read_society().unwrap().expect("society present");
        assert_eq!(loaded.name, society.name);
        assert_eq!(loaded.founder_lct_id, founder);
    }
}
