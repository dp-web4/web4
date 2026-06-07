// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! `hub init` logic — bootstrap a chapter society.
//!
//! Flow:
//! 1. Validate chapter dir doesn't already contain a society (idempotent).
//! 2. Load the Sovereign identity (LCT + keypair) from the path given.
//! 3. Compose a founding charter (Charter::found), hash it.
//! 4. Bootstrap a web4_core::Society — wires all 7 base-mandatory roles with
//!    the Sovereign as initial filler for each (solo founder pattern).
//! 5. Persist: charter.json, society.json, config.toml. Leave ledger.jsonl
//!    empty (sprint 2 populates).
//!
//! Idempotency: if `chapter-dir/society.json` already exists, the function
//! returns `InitResult::AlreadyInitialized` without overwriting anything.

use anyhow::{Context, Result};
use std::path::{Path, PathBuf};
use web4_core::society::Society;
use web4_core::role::SocietyRole;
use uuid::Uuid;

use crate::chapter::{ChapterConfig, ChapterPaths};
use crate::charter::Charter;
use crate::identity::IdentityFile;

/// Outcome of an `init` call.
#[derive(Debug)]
pub enum InitResult {
    /// Newly initialized — fresh chapter ready to use.
    Initialized {
        society_lct_id: Uuid,
        chapter_dir: PathBuf,
        role_lcts: Vec<(SocietyRole, Uuid)>,
    },
    /// Chapter dir already contained a society. State reported, nothing written.
    AlreadyInitialized {
        society_lct_id: Uuid,
        chapter_dir: PathBuf,
        chapter_name: String,
    },
}

/// Parameters for chapter initialization.
pub struct InitArgs {
    /// Human-readable chapter name (e.g. "Lisbon Chapter").
    pub chapter_name: String,

    /// Where the chapter will live on disk.
    pub chapter_dir: PathBuf,

    /// Path to the Sovereign identity file (see IdentityFile).
    pub sovereign_lct_path: PathBuf,
}

/// Run the init flow.
pub fn init_chapter(args: InitArgs) -> Result<InitResult> {
    let paths = ChapterPaths::new(&args.chapter_dir);

    // 1. Idempotency check.
    if paths.is_initialized() {
        let existing_society = std::fs::read_to_string(paths.society())
            .with_context(|| format!("reading existing society at {}", paths.society().display()))?;
        let society: Society = serde_json::from_str(&existing_society)
            .context("parsing existing society.json")?;
        return Ok(InitResult::AlreadyInitialized {
            society_lct_id: society.lct_id,
            chapter_dir: args.chapter_dir.clone(),
            chapter_name: society.name,
        });
    }

    std::fs::create_dir_all(&args.chapter_dir)
        .with_context(|| format!("creating chapter dir {}", args.chapter_dir.display()))?;

    // 2. Load Sovereign identity.
    let sovereign = IdentityFile::load(&args.sovereign_lct_path)
        .with_context(|| format!(
            "loading Sovereign LCT from {}",
            args.sovereign_lct_path.display()
        ))?;
    let sovereign_lct_id = sovereign.lct.id;
    tracing::info!(
        sovereign_lct_id = %sovereign_lct_id,
        sovereign_entity_type = ?sovereign.lct.entity_type,
        "loaded Sovereign identity"
    );

    // 3. Compose + hash founding charter.
    let charter = Charter::found(args.chapter_name.clone(), sovereign_lct_id);
    let charter_hash = charter.hash().context("hashing charter")?;
    charter.save(paths.charter())
        .with_context(|| format!("writing charter to {}", paths.charter().display()))?;

    // 4. Bootstrap the society. Sprint 1 uses the founder for all 7 roles
    // (solo organizer pattern). Role rotation lands in later sprints.
    let (society, role_lcts) = Society::bootstrap(
        args.chapter_name.clone(),
        charter_hash,
        sovereign_lct_id,
    );

    let society_lct_id = society.lct_id;

    // 5. Persist society state.
    let society_json = serde_json::to_string_pretty(&society)
        .context("serializing society")?;
    std::fs::write(paths.society(), society_json)
        .with_context(|| format!("writing society to {}", paths.society().display()))?;

    // 6. Persist config.toml (so subsequent `hub` commands know where the
    // chapter lives + where to find the Sovereign).
    let config = ChapterConfig::new(
        args.chapter_name.clone(),
        args.sovereign_lct_path.clone(),
    );
    config.save(paths.config())
        .with_context(|| format!("writing config to {}", paths.config().display()))?;

    // 7. Create empty ledger file (sprint 2 fills it with witnessed events).
    std::fs::write(paths.ledger(), "")
        .with_context(|| format!("creating empty ledger at {}", paths.ledger().display()))?;

    tracing::info!(
        society_lct_id = %society_lct_id,
        chapter_name = %args.chapter_name,
        chapter_dir = %args.chapter_dir.display(),
        roles_wired = role_lcts.len(),
        "chapter society bootstrapped"
    );

    Ok(InitResult::Initialized {
        society_lct_id,
        chapter_dir: args.chapter_dir,
        role_lcts,
    })
}

/// Load an already-initialized chapter's society state.
pub fn load_society(chapter_dir: impl AsRef<Path>) -> Result<Society> {
    let paths = ChapterPaths::new(chapter_dir.as_ref());
    let json = std::fs::read_to_string(paths.society())
        .with_context(|| format!("reading {}", paths.society().display()))?;
    let society: Society = serde_json::from_str(&json)
        .context("parsing society.json")?;
    Ok(society)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use web4_core::lct::EntityType;

    fn fresh_sovereign(dir: &Path) -> PathBuf {
        let path = dir.join("sovereign.json");
        let identity = IdentityFile::generate(EntityType::Human);
        identity.save(&path).unwrap();
        path
    }

    #[test]
    fn init_wires_all_seven_base_roles() {
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let chapter_dir = tmp.path().join("lisbon");

        let result = init_chapter(InitArgs {
            chapter_name: "Lisbon Chapter".into(),
            chapter_dir: chapter_dir.clone(),
            sovereign_lct_path: sovereign_path,
        }).unwrap();

        let role_lcts = match result {
            InitResult::Initialized { role_lcts, .. } => role_lcts,
            other => panic!("expected Initialized, got {:?}", other),
        };

        let role_names: std::collections::HashSet<_> = role_lcts
            .iter()
            .map(|(r, _)| format!("{:?}", r))
            .collect();

        for expected in &["Sovereign", "LawOracle", "PolicyEntity", "Treasurer",
                          "Administrator", "Archivist", "Citizen"] {
            assert!(role_names.contains(*expected),
                "missing base-mandatory role: {}", expected);
        }
    }

    #[test]
    fn init_creates_expected_files() {
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let chapter_dir = tmp.path().join("lisbon");

        init_chapter(InitArgs {
            chapter_name: "Lisbon".into(),
            chapter_dir: chapter_dir.clone(),
            sovereign_lct_path: sovereign_path,
        }).unwrap();

        let paths = ChapterPaths::new(&chapter_dir);
        assert!(paths.config().exists(), "config.toml missing");
        assert!(paths.charter().exists(), "charter.json missing");
        assert!(paths.society().exists(), "society.json missing");
        assert!(paths.ledger().exists(), "ledger.jsonl missing (should be empty)");
        assert_eq!(std::fs::read_to_string(paths.ledger()).unwrap(), "");
    }

    #[test]
    fn init_is_idempotent() {
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let chapter_dir = tmp.path().join("lisbon");

        // First init
        let first = init_chapter(InitArgs {
            chapter_name: "Lisbon".into(),
            chapter_dir: chapter_dir.clone(),
            sovereign_lct_path: sovereign_path.clone(),
        }).unwrap();
        let first_id = match first {
            InitResult::Initialized { society_lct_id, .. } => society_lct_id,
            other => panic!("expected Initialized, got {:?}", other),
        };

        // Capture original file contents
        let charter_before = std::fs::read_to_string(chapter_dir.join("charter.json")).unwrap();
        let society_before = std::fs::read_to_string(chapter_dir.join("society.json")).unwrap();

        // Second init on same dir
        let second = init_chapter(InitArgs {
            chapter_name: "Different Name (should be ignored)".into(),
            chapter_dir: chapter_dir.clone(),
            sovereign_lct_path: sovereign_path,
        }).unwrap();

        match second {
            InitResult::AlreadyInitialized { society_lct_id, chapter_name, .. } => {
                assert_eq!(society_lct_id, first_id, "must report the existing society LCT");
                assert_eq!(chapter_name, "Lisbon",
                    "must report the existing chapter name, not the new one passed in");
            }
            other => panic!("expected AlreadyInitialized, got {:?}", other),
        }

        // Verify files were NOT rewritten
        let charter_after = std::fs::read_to_string(chapter_dir.join("charter.json")).unwrap();
        let society_after = std::fs::read_to_string(chapter_dir.join("society.json")).unwrap();
        assert_eq!(charter_before, charter_after, "charter must not be overwritten");
        assert_eq!(society_before, society_after, "society must not be overwritten");
    }

    #[test]
    fn charter_hash_round_trips_through_society() {
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let chapter_dir = tmp.path().join("lisbon");

        init_chapter(InitArgs {
            chapter_name: "Lisbon".into(),
            chapter_dir: chapter_dir.clone(),
            sovereign_lct_path: sovereign_path,
        }).unwrap();

        // Re-read charter, hash it, compare against society.charter_hash
        let paths = ChapterPaths::new(&chapter_dir);
        let charter = Charter::load(paths.charter()).unwrap();
        let society = load_society(&chapter_dir).unwrap();

        assert_eq!(charter.hash().unwrap(), society.charter_hash,
            "society.charter_hash must equal hash of the on-disk charter");
    }

    #[test]
    fn sovereign_signature_verifies_through_loaded_identity() {
        // Sanity-check that the on-disk Sovereign identity can still sign +
        // verify after the init flow runs. This isn't testing init itself —
        // it confirms the identity file format survives the round-trip.
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let chapter_dir = tmp.path().join("lisbon");

        init_chapter(InitArgs {
            chapter_name: "Lisbon".into(),
            chapter_dir,
            sovereign_lct_path: sovereign_path.clone(),
        }).unwrap();

        let sovereign = IdentityFile::load(&sovereign_path).unwrap();
        let keypair = sovereign.keypair().unwrap();
        let msg = b"post-init signing test";
        let sig = keypair.sign(msg);
        sovereign.lct.verify_signature(msg, &sig).unwrap();
    }
}
