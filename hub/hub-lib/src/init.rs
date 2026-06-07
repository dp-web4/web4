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
use crate::ledger::{build_lookup, ChapterLedger};
use crate::store::{open_chapter_store, open_chapter_store_with, BackendKind};

/// Roles the founder fills at genesis per V2-1 architecture.
///
/// Founder is Sovereign (constitutional) + Citizen (base membership).
/// Other roles (LawOracle, PolicyEntity, Treasurer, Administrator, Archivist)
/// start unfilled. Assignment happens via `hub assign-role` per chapter law.
/// Witness + Auditor are context-mandatory and stay unfilled until federation
/// or trust-issuance starts.
pub const FOUNDER_ROLES_AT_GENESIS: &[SocietyRole] =
    &[SocietyRole::Sovereign, SocietyRole::Citizen];

/// V2-1 transitional helper: walks the society's role map after
/// `Society::bootstrap` (which fills all 7 base-mandatory roles by default)
/// and drops every role assignment except Sovereign + Citizen.
///
/// Will be replaced when web4-core PR U1 lands a "fill which roles at
/// bootstrap" API. See `web4/hub/docs/V2-V3-ARCHITECTURE.md` §Track U.
fn v2_unfill_non_founder_roles(
    society: &mut Society,
    all_role_lcts: Vec<(SocietyRole, Uuid)>,
) -> Vec<(SocietyRole, Uuid)> {
    // Build the set of role keys the founder keeps.
    let keep: std::collections::HashSet<String> = FOUNDER_ROLES_AT_GENESIS
        .iter()
        .map(role_key_for)
        .collect();

    // Drop role assignments for the others.
    society.roles.retain(|key, _| keep.contains(key));

    // Filter the role_lcts return to just the kept roles (others were
    // freshly minted Uuids not anchored anywhere; orphaning is benign).
    all_role_lcts
        .into_iter()
        .filter(|(role, _)| FOUNDER_ROLES_AT_GENESIS.contains(role))
        .collect()
}

/// Map a SocietyRole to its serde-snake_case key (matches the convention
/// `Society::bootstrap` uses for the HashMap keys).
fn role_key_for(role: &SocietyRole) -> String {
    // Use serde to get the canonical snake_case rendering — this is the same
    // discipline `web4-core` uses internally and stays consistent if the
    // serde tag scheme changes upstream.
    serde_json::to_value(role)
        .ok()
        .and_then(|v| v.as_str().map(|s| s.to_string()))
        .unwrap_or_else(|| format!("{:?}", role).to_lowercase())
}

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

    /// Which storage backend to use. `None` = file-backed (MVP-compatible default).
    /// V2-2 added SQLite as an option; future backends slot here.
    pub storage: Option<BackendKind>,
}

/// Run the init flow.
pub fn init_chapter(args: InitArgs) -> Result<InitResult> {
    let paths = ChapterPaths::new(&args.chapter_dir);

    // 1. Idempotency check — through the store, not the filesystem directly.
    // open_chapter_store auto-detects existing backend (sqlite if chapter.db
    // present, else file).
    if args.chapter_dir.exists() {
        let probe_store = open_chapter_store(&args.chapter_dir)
            .context("opening chapter store for idempotency probe")?;
        if let Some(existing) = probe_store.read_society()
            .context("probing for existing society")? {
            return Ok(InitResult::AlreadyInitialized {
                society_lct_id: existing.lct_id,
                chapter_dir: args.chapter_dir.clone(),
                chapter_name: existing.name,
            });
        }
        drop(probe_store);
    }

    std::fs::create_dir_all(&args.chapter_dir)
        .with_context(|| format!("creating chapter dir {}", args.chapter_dir.display()))?;

    // 2. Load Sovereign identity. NOTE per architecture commitment #8:
    // identity-file-as-secret-store is the MVP bootstrap pattern; secrets
    // belong in Hestia's vault and the file pattern deprecates with
    // V2-7 (Hestia-as-Sovereign). Kept here until that sync point lands.
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

    // Open the real store for the requested backend (default: file).
    let backend = args.storage.unwrap_or(BackendKind::File);
    let mut store = open_chapter_store_with(&args.chapter_dir, backend)
        .with_context(|| format!("opening chapter store with backend {:?}", backend))?;
    tracing::info!(backend = backend.as_str(), "chapter storage backend selected");

    // 3. Compose + hash founding charter; write through store.
    let charter = Charter::found(args.chapter_name.clone(), sovereign_lct_id);
    let charter_hash = charter.hash().context("hashing charter")?;
    store.write_charter(&charter).context("writing charter via store")?;

    // 4. Bootstrap the society, then V2-1 unfill: founder fills only
    // Sovereign + Citizen at genesis. The other 5 base-mandatory roles
    // (LawOracle, PolicyEntity, Treasurer, Administrator, Archivist) start
    // unfilled and are assigned later via `hub assign-role` per chapter law.
    //
    // This is a hub-side workaround until web4-core upstream PR U1 lands a
    // proper "fill which roles at bootstrap" API. Tracked at
    // `web4/hub/docs/V2-V3-ARCHITECTURE.md` §Track U.
    let (mut society, all_role_lcts) = Society::bootstrap(
        args.chapter_name.clone(),
        charter_hash,
        sovereign_lct_id,
    );
    let role_lcts = v2_unfill_non_founder_roles(&mut society, all_role_lcts);

    let society_lct_id = society.lct_id;

    // 5. Persist society state via store.
    store.write_society(&society).context("writing society via store")?;

    // 6. Persist config.toml (operator-owned; file-based by design — not
    // part of the storage backend abstraction). Canonicalize the Sovereign
    // path so it survives `cd` between init and later commands.
    let sovereign_abs = std::fs::canonicalize(&args.sovereign_lct_path)
        .with_context(|| format!(
            "canonicalizing Sovereign LCT path {}",
            args.sovereign_lct_path.display()
        ))?;
    let config = ChapterConfig::new(args.chapter_name.clone(), sovereign_abs);
    config.save(paths.config())
        .with_context(|| format!("writing config to {}", paths.config().display()))?;

    // 7. Initialize the chapter ledger via store + write Genesis entry.
    // Genesis is signed by the Sovereign; subsequent events get signed by
    // their respective actors.
    let mut ledger = ChapterLedger::open(store)
        .context("opening chapter ledger via store")?;
    let sovereign_keypair = sovereign.keypair()
        .context("reconstructing Sovereign keypair for Genesis signing")?;
    ledger.write_genesis(
        sovereign_lct_id,
        &sovereign_keypair,
        args.chapter_name.clone(),
        society.charter_hash.clone(),
    ).context("writing Genesis entry to chapter ledger")?;

    tracing::info!(
        society_lct_id = %society_lct_id,
        chapter_name = %args.chapter_name,
        chapter_dir = %args.chapter_dir.display(),
        roles_wired = role_lcts.len(),
        ledger_entries = ledger.len(),
        "chapter society bootstrapped"
    );

    Ok(InitResult::Initialized {
        society_lct_id,
        chapter_dir: args.chapter_dir,
        role_lcts,
    })
}

/// Load an already-initialized chapter's society state. Routes through
/// the storage backend abstraction, so works against any backend.
pub fn load_society(chapter_dir: impl AsRef<Path>) -> Result<Society> {
    let store = open_chapter_store(chapter_dir.as_ref())
        .context("opening chapter store")?;
    store.read_society()
        .context("reading society via store")?
        .ok_or_else(|| anyhow::anyhow!("no society found in chapter store"))
}

/// Result of a ledger verification pass.
#[derive(Debug)]
pub struct VerifyResult {
    pub chapter_dir: PathBuf,
    pub chapter_name: String,
    pub entries: usize,
    pub head_hash: String,
}

/// Verify the entire chapter ledger end-to-end. For MVP, the only LCT in
/// the lookup is the Sovereign (loaded from config.toml's sovereign.lct_path).
/// Later sprints will extend the lookup to include member LCTs (extracted
/// from MemberAdded events).
pub fn verify_chapter(chapter_dir: impl AsRef<Path>) -> Result<VerifyResult> {
    let chapter_dir = chapter_dir.as_ref();
    let paths = ChapterPaths::new(chapter_dir);

    let config = ChapterConfig::load(paths.config())
        .with_context(|| format!("loading config at {}", paths.config().display()))?;

    // Resolve the Sovereign LCT for envelope/ledger verification.
    // Local mode: load the IdentityFile (which carries the Lct).
    // Hestia mode: synthesize an Lct from the config's stored pubkey.
    let sovereign_lct = match config.sovereign.mode()? {
        crate::chapter::SovereignMode::Local { lct_path } => {
            let sov_path = if lct_path.is_absolute() {
                lct_path
            } else {
                chapter_dir.join(&lct_path)
            };
            let identity = IdentityFile::load(&sov_path)
                .with_context(|| format!("loading Sovereign identity from {}", sov_path.display()))?;
            identity.lct
        }
        crate::chapter::SovereignMode::Hestia { lct_id, pubkey_hex, .. } => {
            crate::chapter::hestia_sovereign_lct(lct_id, &pubkey_hex)
                .context("synthesizing Sovereign Lct from Hestia-mode config")?
        }
    };

    let society = load_society(chapter_dir).context("loading society")?;
    let store = open_chapter_store(chapter_dir)
        .context("opening chapter store for verify")?;
    let ledger = ChapterLedger::open(store)
        .context("opening ledger via store")?;
    // Build LCT lookup. MVP: just the Sovereign. Extension point: as the
    // ledger replays MemberAdded events, we'd need to register their LCTs
    // too — but member LCTs aren't yet stored alongside the ledger (V2
    // adds a per-member identity registry). For sprint 2 the only signer
    // is the Sovereign, so this lookup is complete.
    let lookup = build_lookup([sovereign_lct]);

    ledger.verify_chain(|id| lookup.get(&id).cloned())
        .context("ledger chain verification failed")?;

    Ok(VerifyResult {
        chapter_dir: chapter_dir.to_path_buf(),
        chapter_name: society.name,
        entries: ledger.len(),
        head_hash: ledger.head_hash().to_string(),
    })
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
    fn init_fills_only_sovereign_and_citizen_at_genesis() {
        // V2-1: founder fills Sovereign + Citizen only. Other 5 base-mandatory
        // roles (LawOracle, PolicyEntity, Treasurer, Administrator, Archivist)
        // start unfilled and are assigned later per chapter law.
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let chapter_dir = tmp.path().join("lisbon");

        let result = init_chapter(InitArgs {
            chapter_name: "Lisbon Chapter".into(),
            chapter_dir: chapter_dir.clone(),
            sovereign_lct_path: sovereign_path,
            storage: None,
        }).unwrap();

        let role_lcts = match result {
            InitResult::Initialized { role_lcts, .. } => role_lcts,
            other => panic!("expected Initialized, got {:?}", other),
        };

        assert_eq!(role_lcts.len(), 2,
            "V2-1: only 2 roles wired at genesis (Sovereign + Citizen), got {}: {:?}",
            role_lcts.len(),
            role_lcts.iter().map(|(r, _)| format!("{:?}", r)).collect::<Vec<_>>());

        let role_set: std::collections::HashSet<_> = role_lcts
            .iter()
            .map(|(r, _)| format!("{:?}", r))
            .collect();
        assert!(role_set.contains("Sovereign"));
        assert!(role_set.contains("Citizen"));

        // Verify the society state on disk reflects this too
        let society = load_society(&chapter_dir).unwrap();
        assert_eq!(society.roles.len(), 2,
            "society.json should hold 2 role assignments at genesis (V2-1)");
        assert!(society.roles.contains_key("sovereign"));
        assert!(society.roles.contains_key("citizen"));
        for unfilled in &["law_oracle", "policy_entity", "treasurer",
                          "administrator", "archivist"] {
            assert!(!society.roles.contains_key(*unfilled),
                "role '{}' should be unfilled at genesis (V2-1)", unfilled);
        }
    }

    #[test]
    fn founder_lct_holds_both_sovereign_and_citizen() {
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let chapter_dir = tmp.path().join("lisbon");

        init_chapter(InitArgs {
            chapter_name: "Lisbon".into(),
            chapter_dir: chapter_dir.clone(),
            sovereign_lct_path: sovereign_path,
            storage: None,
        }).unwrap();

        let society = load_society(&chapter_dir).unwrap();
        let sovereign = society.roles.get("sovereign").unwrap();
        let citizen = society.roles.get("citizen").unwrap();
        assert_eq!(sovereign.filling_entity_lct_id, citizen.filling_entity_lct_id,
            "founder should fill both Sovereign and Citizen at genesis");
        assert_eq!(sovereign.filling_entity_lct_id, society.founder_lct_id);
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
            storage: None,
        }).unwrap();

        let paths = ChapterPaths::new(&chapter_dir);
        assert!(paths.config().exists(), "config.toml missing");
        assert!(paths.charter().exists(), "charter.json missing");
        assert!(paths.society().exists(), "society.json missing");
        assert!(paths.ledger().exists(), "ledger.jsonl missing");

        // Sprint 2: ledger now starts with Genesis entry (not empty)
        let store = open_chapter_store(&chapter_dir).unwrap();
        let ledger = crate::ledger::ChapterLedger::open(store).unwrap();
        assert_eq!(ledger.len(), 1, "expected single Genesis entry after init");
    }

    #[test]
    fn init_writes_signed_genesis_entry_verifiable_end_to_end() {
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let chapter_dir = tmp.path().join("lisbon");

        init_chapter(InitArgs {
            chapter_name: "Lisbon".into(),
            chapter_dir: chapter_dir.clone(),
            sovereign_lct_path: sovereign_path,
            storage: None,
        }).unwrap();

        // verify_chapter does end-to-end: config → identity → society → ledger
        let result = verify_chapter(&chapter_dir).unwrap();
        assert_eq!(result.chapter_name, "Lisbon");
        assert_eq!(result.entries, 1, "Genesis is the only entry post-init");
        assert!(!result.head_hash.is_empty());
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
            storage: None,
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
            storage: None,
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
            storage: None,
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
            storage: None,
        }).unwrap();

        let sovereign = IdentityFile::load(&sovereign_path).unwrap();
        let keypair = sovereign.keypair().unwrap();
        let msg = b"post-init signing test";
        let sig = keypair.sign(msg);
        sovereign.lct.verify_signature(msg, &sig).unwrap();
    }
}
