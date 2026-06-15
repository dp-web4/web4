// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! `hub init` logic — bootstrap a hub society.
//!
//! Flow:
//! 1. Validate hub dir doesn't already contain a society (idempotent).
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

use crate::hub::{HubConfig, HubPaths};
use crate::charter::Charter;
use crate::identity::IdentityFile;
use crate::ledger::{build_lookup, HubLedger};
use crate::store::{open_hub_store, open_hub_store_with, BackendKind};

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
    /// Newly initialized — fresh hub ready to use.
    Initialized {
        society_lct_id: Uuid,
        hub_dir: PathBuf,
        role_lcts: Vec<(SocietyRole, Uuid)>,
    },
    /// Chapter dir already contained a society. State reported, nothing written.
    AlreadyInitialized {
        society_lct_id: Uuid,
        hub_dir: PathBuf,
        hub_name: String,
    },
}

/// Parameters for chapter initialization.
pub struct InitArgs {
    /// Human-readable hub name (e.g. "Lisbon Chapter").
    pub hub_name: String,

    /// Where the chapter will live on disk.
    pub hub_dir: PathBuf,

    /// Path to the Sovereign identity file (see IdentityFile).
    /// For Local-mode init only — Hestia-mode uses [`init_hub_with_signer`]
    /// and doesn't need a local IdentityFile.
    pub sovereign_lct_path: PathBuf,

    /// Which storage backend to use. `None` = file-backed (MVP-compatible default).
    /// V2-2 added SQLite as an option; future backends slot here.
    pub storage: Option<BackendKind>,
}

/// Hestia-mode init parameters. Distinct from [`InitArgs`] because the
/// hub holds NO IdentityFile in Hestia mode — it knows only the
/// Sovereign's LCT id + public key + callback URL.
pub struct HestiaInitArgs {
    pub hub_name: String,
    pub hub_dir: PathBuf,
    /// The Sovereign's LCT id (what Hestia signs for).
    pub sovereign_lct_id: Uuid,
    /// The Sovereign's public key (hex-encoded 32 bytes).
    pub sovereign_pubkey_hex: String,
    /// URL where the hub POSTs SignRequest for Sovereign signatures.
    pub hestia_callback_url: String,
    pub storage: Option<BackendKind>,
}

/// Run the init flow.
pub async fn init_hub(args: InitArgs) -> Result<InitResult> {
    let paths = HubPaths::new(&args.hub_dir);

    // 1. Idempotency check — through the store, not the filesystem directly.
    // open_hub_store auto-detects existing backend (sqlite if chapter.db
    // present, else file).
    if args.hub_dir.exists() {
        let probe_store = open_hub_store(&args.hub_dir)
            .context("opening hub store for idempotency probe")?;
        if let Some(existing) = probe_store.read_society().await
            .context("probing for existing society")? {
            return Ok(InitResult::AlreadyInitialized {
                society_lct_id: existing.lct_id,
                hub_dir: args.hub_dir.clone(),
                hub_name: existing.name,
            });
        }
        drop(probe_store);
    }

    std::fs::create_dir_all(&args.hub_dir)
        .with_context(|| format!("creating hub dir {}", args.hub_dir.display()))?;

    // 2. Load Sovereign identity. NOTE per architecture commitment #8:
    // identity-file-as-secret-store is the MVP bootstrap pattern; secrets
    // belong in Hestia's vault and the file pattern deprecates with
    // V2-7 (Hestia-as-Sovereign). Kept here until that sync point lands.
    let sovereign = IdentityFile::load_auto(&args.sovereign_lct_path)
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
    let mut store = open_hub_store_with(&args.hub_dir, backend)
        .with_context(|| format!("opening hub store with backend {:?}", backend))?;
    tracing::info!(backend = backend.as_str(), "chapter storage backend selected");

    // 3. Compose + hash founding charter; write through store.
    let charter = Charter::found(args.hub_name.clone(), sovereign_lct_id);
    let charter_hash = charter.hash().context("hashing charter")?;
    store.write_charter(&charter).await.context("writing charter via store")?;

    // 4. Bootstrap the society, then V2-1 unfill: founder fills only
    // Sovereign + Citizen at genesis. The other 5 base-mandatory roles
    // (LawOracle, PolicyEntity, Treasurer, Administrator, Archivist) start
    // unfilled and are assigned later via `hub assign-role` per chapter law.
    //
    // This is a hub-side workaround until web4-core upstream PR U1 lands a
    // proper "fill which roles at bootstrap" API. Tracked at
    // `web4/hub/docs/V2-V3-ARCHITECTURE.md` §Track U.
    let (mut society, all_role_lcts) = Society::bootstrap(
        args.hub_name.clone(),
        charter_hash,
        sovereign_lct_id,
    );
    let role_lcts = v2_unfill_non_founder_roles(&mut society, all_role_lcts);

    let society_lct_id = society.lct_id;

    // 5. Persist society state via store.
    store.write_society(&society).await.context("writing society via store")?;

    // 6. Persist config.toml (operator-owned; file-based by design — not
    // part of the storage backend abstraction). Canonicalize the Sovereign
    // path so it survives `cd` between init and later commands.
    let sovereign_abs = std::fs::canonicalize(&args.sovereign_lct_path)
        .with_context(|| format!(
            "canonicalizing Sovereign LCT path {}",
            args.sovereign_lct_path.display()
        ))?;
    let config = HubConfig::new(args.hub_name.clone(), sovereign_abs);
    config.save(paths.config())
        .with_context(|| format!("writing config to {}", paths.config().display()))?;

    // 7. Initialize the hub ledger via store + write Genesis entry.
    // Genesis is signed by the Sovereign; subsequent events get signed by
    // their respective actors.
    let mut ledger = HubLedger::open(store).await
        .context("opening hub ledger via store")?;
    let sovereign_keypair = sovereign.keypair()
        .context("reconstructing Sovereign keypair for Genesis signing")?;
    ledger.write_genesis(
        sovereign_lct_id,
        &sovereign_keypair,
        args.hub_name.clone(),
        society.charter_hash.clone(),
    ).await.context("writing Genesis entry to hub ledger")?;

    tracing::info!(
        society_lct_id = %society_lct_id,
        hub_name = %args.hub_name,
        hub_dir = %args.hub_dir.display(),
        roles_wired = role_lcts.len(),
        ledger_entries = ledger.len(),
        "hub society bootstrapped"
    );

    Ok(InitResult::Initialized {
        society_lct_id,
        hub_dir: args.hub_dir,
        role_lcts,
    })
}

/// Load an already-initialized chapter's society state. Routes through
/// the storage backend abstraction, so works against any backend.
pub async fn load_society(hub_dir: impl AsRef<Path>) -> Result<Society> {
    let store = open_hub_store(hub_dir.as_ref())
        .context("opening hub store")?;
    store.read_society().await
        .context("reading society via store")?
        .ok_or_else(|| anyhow::anyhow!("no society found in hub store"))
}

/// Run the Hestia-mode init flow. The hub holds NO Sovereign keypair;
/// Genesis is signed by Hestia via HTTP callback.
///
/// Per architecture commitment #8: secrets live in Hestia's vault.
/// This entry point is the canonical Hestia-mode bootstrap.
pub async fn init_hub_hestia(args: HestiaInitArgs) -> Result<InitResult> {
    use crate::signer::{HestiaCallbackSigner, RemoteSigner, SignIntent};
    use web4_core::crypto::SignatureBytes;

    let paths = HubPaths::new(&args.hub_dir);

    // 1. Idempotency check.
    if args.hub_dir.exists() {
        let probe_store = open_hub_store(&args.hub_dir)
            .context("opening hub store for idempotency probe")?;
        if let Some(existing) = probe_store.read_society().await
            .context("probing for existing society")? {
            return Ok(InitResult::AlreadyInitialized {
                society_lct_id: existing.lct_id,
                hub_dir: args.hub_dir.clone(),
                hub_name: existing.name,
            });
        }
        drop(probe_store);
    }

    std::fs::create_dir_all(&args.hub_dir)
        .with_context(|| format!("creating hub dir {}", args.hub_dir.display()))?;

    // 2. Synthesize the Sovereign's Lct from the supplied pubkey
    // (no IdentityFile in Hestia mode).
    let sovereign_lct = crate::hub::hestia_sovereign_lct(
        args.sovereign_lct_id, &args.sovereign_pubkey_hex,
    ).context("synthesizing Sovereign Lct from Hestia init args")?;
    tracing::info!(
        sovereign_lct_id = %args.sovereign_lct_id,
        callback_url = %args.hestia_callback_url,
        "Hestia-mode init: Sovereign LCT synthesized from pubkey",
    );

    // 3. Open store.
    let backend = args.storage.unwrap_or(BackendKind::File);
    let mut store = open_hub_store_with(&args.hub_dir, backend)
        .with_context(|| format!("opening hub store with backend {:?}", backend))?;

    // 4. Charter.
    let charter = Charter::found(args.hub_name.clone(), args.sovereign_lct_id);
    let charter_hash = charter.hash().context("hashing charter")?;
    store.write_charter(&charter).await.context("writing charter via store")?;

    // 5. Bootstrap society + V2-1 unfill.
    let (mut society, all_role_lcts) = Society::bootstrap(
        args.hub_name.clone(),
        charter_hash,
        args.sovereign_lct_id,
    );
    let role_lcts = v2_unfill_non_founder_roles(&mut society, all_role_lcts);
    let society_lct_id = society.lct_id;
    let society_charter_hash = society.charter_hash.clone();
    store.write_society(&society).await.context("writing society via store")?;

    // 6. Persist Hestia-mode config.
    let config = HubConfig::new_hestia(
        args.hub_name.clone(),
        args.hestia_callback_url.clone(),
        args.sovereign_lct_id,
        args.sovereign_pubkey_hex.clone(),
    );
    config.save(paths.config())
        .with_context(|| format!("writing config to {}", paths.config().display()))?;

    // 7. Open ledger + build unsigned Genesis.
    let mut ledger = HubLedger::open(store).await
        .context("opening hub ledger via store")?;
    let (unsigned, _ts) = ledger.build_genesis(
        args.sovereign_lct_id,
        args.hub_name.clone(),
        society_charter_hash,
    ).context("building unsigned Genesis entry")?;

    // 8. Ask Hestia to sign the Genesis. The hub never sees the
    // private key on this path.
    let signer = HestiaCallbackSigner::new(args.sovereign_lct_id, args.hestia_callback_url.clone())
        .context("constructing HestiaCallbackSigner")?;
    let intent = SignIntent {
        request_id: Uuid::new_v4(),
        hub_id: society_lct_id,
        hub_name: args.hub_name.clone(),
        actor_lct_id: args.sovereign_lct_id,
        ledger_index: unsigned.entry.index,
        event_kind: unsigned.entry.event.kind().to_string(),
        event: serde_json::to_value(&unsigned.entry.event)
            .context("serializing Genesis event for intent")?,
    };
    let signing_bytes = unsigned.signing_bytes.clone();
    let signature: SignatureBytes = signer
        .sign(args.sovereign_lct_id, &signing_bytes, &intent)
        .await
        .map_err(|e| anyhow::anyhow!("Hestia denied or failed Genesis signing: {}", e))?;

    // 9. Commit signed Genesis.
    ledger.append_signed(unsigned, signature).await
        .context("committing signed Genesis entry to ledger")?;

    // 10. Sanity verify with synthesized Lct.
    let lookup = build_lookup([sovereign_lct]);
    ledger.verify_chain(|id| lookup.get(&id).cloned())
        .context("post-Genesis verify_chain failed — likely a wire mismatch with Hestia")?;

    tracing::info!(
        society_lct_id = %society_lct_id,
        hub_name = %args.hub_name,
        hub_dir = %args.hub_dir.display(),
        roles_wired = role_lcts.len(),
        ledger_entries = ledger.len(),
        "Hestia-mode hub society bootstrapped"
    );

    Ok(InitResult::Initialized {
        society_lct_id,
        hub_dir: args.hub_dir,
        role_lcts,
    })
}

/// Result of a ledger verification pass.
#[derive(Debug)]
pub struct VerifyResult {
    pub hub_dir: PathBuf,
    pub hub_name: String,
    pub entries: usize,
    pub head_hash: String,
}

/// Verify the entire hub ledger end-to-end. For MVP, the only LCT in
/// the lookup is the Sovereign (loaded from config.toml's sovereign.lct_path).
/// Later sprints will extend the lookup to include member LCTs (extracted
/// from MemberAdded events).
pub async fn verify_hub(hub_dir: impl AsRef<Path>) -> Result<VerifyResult> {
    let hub_dir = hub_dir.as_ref();
    let paths = HubPaths::new(hub_dir);

    let config = HubConfig::load(paths.config())
        .with_context(|| format!("loading config at {}", paths.config().display()))?;

    // Resolve the Sovereign LCT for envelope/ledger verification.
    // Local mode: load the IdentityFile (which carries the Lct).
    // Hestia mode: synthesize an Lct from the config's stored pubkey.
    let sovereign_lct = match config.sovereign.mode()? {
        crate::hub::SovereignMode::Local { lct_path } => {
            let sov_path = if lct_path.is_absolute() {
                lct_path
            } else {
                hub_dir.join(&lct_path)
            };
            let identity = IdentityFile::load_auto(&sov_path)
                .with_context(|| format!("loading Sovereign identity from {}", sov_path.display()))?;
            identity.lct
        }
        crate::hub::SovereignMode::Hestia { lct_id, pubkey_hex, .. } => {
            crate::hub::hestia_sovereign_lct(lct_id, &pubkey_hex)
                .context("synthesizing Sovereign Lct from Hestia-mode config")?
        }
    };

    let society = load_society(hub_dir).await.context("loading society")?;
    let store = open_hub_store(hub_dir)
        .context("opening hub store for verify")?;
    let ledger = HubLedger::open(store).await
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
        hub_dir: hub_dir.to_path_buf(),
        hub_name: society.name,
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

    #[tokio::test]
    async fn init_fills_only_sovereign_and_citizen_at_genesis() {
        // V2-1: founder fills Sovereign + Citizen only. Other 5 base-mandatory
        // roles (LawOracle, PolicyEntity, Treasurer, Administrator, Archivist)
        // start unfilled and are assigned later per chapter law.
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let hub_dir = tmp.path().join("lisbon");

        let result = init_hub(InitArgs {
            hub_name: "Lisbon Chapter".into(),
            hub_dir: hub_dir.clone(),
            sovereign_lct_path: sovereign_path,
            storage: None,
        }).await.unwrap();

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
        let society = load_society(&hub_dir).await.unwrap();
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

    #[tokio::test]
    async fn founder_lct_holds_both_sovereign_and_citizen() {
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let hub_dir = tmp.path().join("lisbon");

        init_hub(InitArgs {
            hub_name: "Lisbon".into(),
            hub_dir: hub_dir.clone(),
            sovereign_lct_path: sovereign_path,
            storage: None,
        }).await.unwrap();

        let society = load_society(&hub_dir).await.unwrap();
        let sovereign = society.roles.get("sovereign").unwrap();
        let citizen = society.roles.get("citizen").unwrap();
        assert_eq!(sovereign.filling_entity_lct_id, citizen.filling_entity_lct_id,
            "founder should fill both Sovereign and Citizen at genesis");
        assert_eq!(sovereign.filling_entity_lct_id, society.founder_lct_id);
    }

    #[tokio::test]
    async fn init_creates_expected_files() {
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let hub_dir = tmp.path().join("lisbon");

        init_hub(InitArgs {
            hub_name: "Lisbon".into(),
            hub_dir: hub_dir.clone(),
            sovereign_lct_path: sovereign_path,
            storage: None,
        }).await.unwrap();

        let paths = HubPaths::new(&hub_dir);
        assert!(paths.config().exists(), "config.toml missing");
        assert!(paths.charter().exists(), "charter.json missing");
        assert!(paths.society().exists(), "society.json missing");
        assert!(paths.ledger().exists(), "ledger.jsonl missing");

        // Sprint 2: ledger now starts with Genesis entry (not empty)
        let store = open_hub_store(&hub_dir).unwrap();
        let ledger = crate::ledger::HubLedger::open(store).await.unwrap();
        assert_eq!(ledger.len(), 1, "expected single Genesis entry after init");
    }

    #[tokio::test]
    async fn init_writes_signed_genesis_entry_verifiable_end_to_end() {
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let hub_dir = tmp.path().join("lisbon");

        init_hub(InitArgs {
            hub_name: "Lisbon".into(),
            hub_dir: hub_dir.clone(),
            sovereign_lct_path: sovereign_path,
            storage: None,
        }).await.unwrap();

        // verify_hub does end-to-end: config → identity → society → ledger
        let result = verify_hub(&hub_dir).await.unwrap();
        assert_eq!(result.hub_name, "Lisbon");
        assert_eq!(result.entries, 1, "Genesis is the only entry post-init");
        assert!(!result.head_hash.is_empty());
    }

    #[tokio::test]
    async fn init_is_idempotent() {
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let hub_dir = tmp.path().join("lisbon");

        // First init
        let first = init_hub(InitArgs {
            hub_name: "Lisbon".into(),
            hub_dir: hub_dir.clone(),
            sovereign_lct_path: sovereign_path.clone(),
            storage: None,
        }).await.unwrap();
        let first_id = match first {
            InitResult::Initialized { society_lct_id, .. } => society_lct_id,
            other => panic!("expected Initialized, got {:?}", other),
        };

        // Capture original file contents
        let charter_before = std::fs::read_to_string(hub_dir.join("charter.json")).unwrap();
        let society_before = std::fs::read_to_string(hub_dir.join("society.json")).unwrap();

        // Second init on same dir
        let second = init_hub(InitArgs {
            hub_name: "Different Name (should be ignored)".into(),
            hub_dir: hub_dir.clone(),
            sovereign_lct_path: sovereign_path,
            storage: None,
        }).await.unwrap();

        match second {
            InitResult::AlreadyInitialized { society_lct_id, hub_name, .. } => {
                assert_eq!(society_lct_id, first_id, "must report the existing society LCT");
                assert_eq!(hub_name, "Lisbon",
                    "must report the existing chapter name, not the new one passed in");
            }
            other => panic!("expected AlreadyInitialized, got {:?}", other),
        }

        // Verify files were NOT rewritten
        let charter_after = std::fs::read_to_string(hub_dir.join("charter.json")).unwrap();
        let society_after = std::fs::read_to_string(hub_dir.join("society.json")).unwrap();
        assert_eq!(charter_before, charter_after, "charter must not be overwritten");
        assert_eq!(society_before, society_after, "society must not be overwritten");
    }

    #[tokio::test]
    async fn charter_hash_round_trips_through_society() {
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let hub_dir = tmp.path().join("lisbon");

        init_hub(InitArgs {
            hub_name: "Lisbon".into(),
            hub_dir: hub_dir.clone(),
            sovereign_lct_path: sovereign_path,
            storage: None,
        }).await.unwrap();

        // Re-read charter, hash it, compare against society.charter_hash
        let paths = HubPaths::new(&hub_dir);
        let charter = Charter::load(paths.charter()).unwrap();
        let society = load_society(&hub_dir).await.unwrap();

        assert_eq!(charter.hash().unwrap(), society.charter_hash,
            "society.charter_hash must equal hash of the on-disk charter");
    }

    #[tokio::test]
    async fn sovereign_signature_verifies_through_loaded_identity() {
        // Sanity-check that the on-disk Sovereign identity can still sign +
        // verify after the init flow runs. This isn't testing init itself —
        // it confirms the identity file format survives the round-trip.
        let tmp = tempdir().unwrap();
        let sovereign_path = fresh_sovereign(tmp.path());
        let hub_dir = tmp.path().join("lisbon");

        init_hub(InitArgs {
            hub_name: "Lisbon".into(),
            hub_dir,
            sovereign_lct_path: sovereign_path.clone(),
            storage: None,
        }).await.unwrap();

        let sovereign = IdentityFile::load(&sovereign_path).unwrap();
        let keypair = sovereign.keypair().unwrap();
        let msg = b"post-init signing test";
        let sig = keypair.sign(msg);
        sovereign.lct.verify_signature(msg, &sig).unwrap();
    }
}
