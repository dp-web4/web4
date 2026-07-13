// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! HubSession — the operator-facing API for a chapter.
//!
//! Opens a chapter (config + Sovereign identity + ledger) and exposes ops:
//! add_member, remove_member, assign_role, record_event, declare_skill,
//! list_members, find_skill, query_chapter. Used by both the admin CLI
//! and the MCP server handlers — single code path for the actual work.
//!
//! Sprint 4 abstraction: keeps CLI and MCP from drifting apart.

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use std::path::{Path, PathBuf};
use uuid::Uuid;
use web4_core::crypto::KeyPair;
use web4_core::role::SocietyRole;
use web4_core::society::Society;

use crate::hub::{HubConfig, HubPaths};
use crate::events::HubEvent;
use crate::identity::IdentityFile;
use crate::init::load_society;
use crate::ledger::{HubLedger, LedgerEntry};
use crate::state::{HubState, Member};
use crate::store::open_hub_store;

/// One open chapter, ready for ops. Drop to close.
pub struct HubSession {
    pub paths: HubPaths,
    pub config: HubConfig,
    pub sovereign_lct_id: Uuid,
    pub sovereign_keypair: KeyPair,
    pub ledger: HubLedger,
}

impl HubSession {
    pub async fn open(hub_dir: impl AsRef<Path>) -> Result<Self> {
        let hub_dir = hub_dir.as_ref();
        let paths = HubPaths::new(hub_dir.to_path_buf());
        let config = HubConfig::load(paths.config())
            .with_context(|| format!("loading config at {}", paths.config().display()))?;

        // HubSession is the operator-facing CLI surface (add-member CLI,
        // record-event CLI, etc.). It needs the Sovereign keypair in-process
        // to sign ledger entries from the CLI. That's a Local-mode-only
        // capability. Hestia-mode chapters must drive acts through the
        // REST API (`POST /v1/hubs/{id}/events`) where the signer
        // abstraction handles the Hestia callback roundtrip.
        let lct_path = match config.sovereign.mode()? {
            crate::hub::SovereignMode::Local { lct_path } => lct_path,
            crate::hub::SovereignMode::Hestia { .. } => {
                anyhow::bail!(
                    "this chapter is Hestia-mode; CLI acts \
                     are not supported. Use the REST API at \
                     POST /v1/hubs/{{hub_id}}/events with a SignedEnvelope \
                     instead. For read-only queries, use the equivalent GET endpoints."
                );
            }
        };
        let sovereign = IdentityFile::load_auto(&lct_path)
            .with_context(|| format!(
                "loading Sovereign identity from {}", lct_path.display()
            ))?;
        let keypair = sovereign.keypair()?;
        let store = open_hub_store(hub_dir)
            .context("opening hub store for session")?;
        let ledger = HubLedger::open(store).await
            .context("opening ledger via hub store")?;
        Ok(Self {
            paths,
            config,
            sovereign_lct_id: sovereign.lct.id,
            sovereign_keypair: keypair,
            ledger,
        })
    }

    pub fn hub_dir(&self) -> &Path { &self.paths.root }

    // ---------- acts ----------

    pub async fn add_member(&mut self, member_lct_id: Uuid, name: Option<String>) -> Result<&LedgerEntry> {
        let event = HubEvent::MemberAdded {
            member_lct_id,
            added_by: self.sovereign_lct_id,
            member_name: name,
            member_pubkey_hex: None,
        };
        self.append(event).await
    }

    pub async fn remove_member(&mut self, member_lct_id: Uuid, reason: Option<String>) -> Result<&LedgerEntry> {
        let event = HubEvent::MemberRemoved {
            member_lct_id,
            removed_by: self.sovereign_lct_id,
            reason,
        };
        self.append(event).await
    }

    /// Assign `role` to `member_lct_id`. Updates the persisted society
    /// role-fill (web4-core enforces Sovereign/Administrator authority and
    /// owns the role LCT — created on first fill, reused on rotation) AND
    /// witnesses the act in the ledger. The role LCT id is society-managed,
    /// not caller-supplied: previously the act was only appended to the
    /// ledger and never folded into the society, so assigned roles never
    /// showed as filled in query_chapter / MCP / the admin dashboard.
    /// **Conjunction tool** (lct-mcp-as-smart-contract proposal §6.3): mutates
    /// separately-persisted state (`society` file) AND appends a ledger event.
    /// Both side effects must be observable after the call. Tested by
    /// `assign_role_fills_role_in_society`. PR #292 fixed the inverse bug
    /// (event-only, state forgotten).
    pub async fn assign_role(&mut self, role: SocietyRole, member_lct_id: Uuid) -> Result<&LedgerEntry> {
        let mut store = open_hub_store(&self.paths.root)
            .context("opening hub store to update role-fill")?;
        let mut society = store.read_society().await
            .context("reading society state")?
            .ok_or_else(|| anyhow::anyhow!("society state missing for hub"))?;
        // W/O preflight: web4-core enforces Sovereign/Administrator authority
        // in-memory here, BEFORE any persisted side effect. A rejected assignment
        // returns now, leaving the persisted society file bit-identical.
        let role_lct_id = society
            .assign_role(role.clone(), member_lct_id, self.sovereign_lct_id)
            .map_err(|e| anyhow::anyhow!("role assignment rejected: {e}"))?;

        // A (RWOA accountability ratchet): append the authorizing witnessed record
        // FIRST, then persist the derived society projection. Record-before-
        // projection means there is no reachable path where the role-fill persists
        // without its ledger record — if the append fails we return before
        // write_society, leaving society bit-identical. (Previously persisted-then-
        // appended: a failed append left an act with no authorizing record — the
        // O/A gap the ratchet flags. A write_society failure after the record is
        // the safe direction: the ledger is authoritative and the projection
        // re-materializes from it.)
        let event = HubEvent::RoleAssigned {
            role,
            role_lct_id,
            assigned_to: member_lct_id,
            assigned_by: self.sovereign_lct_id,
        };
        let entry = self.append(event).await?;
        store.write_society(&society).await
            .context("persisting role-fill projection after its ledger record")?;
        Ok(entry)
    }

    pub async fn record_event(
        &mut self,
        event_kind: String,
        title: String,
        attended_by: Vec<Uuid>,
        held_at: Option<DateTime<Utc>>,
    ) -> Result<&LedgerEntry> {
        let event = HubEvent::EventRecorded {
            event_kind,
            title,
            attended_by,
            recorded_by: self.sovereign_lct_id,
            held_at: held_at.unwrap_or_else(Utc::now),
        };
        self.append(event).await
    }

    /// **Conjunction tool** (lct-mcp-as-smart-contract proposal §6.3): mutates
    /// separately-persisted state (law text in the store) AND appends a ledger
    /// event. Both side effects must be observable after the call. Tested by
    /// `set_law_writes_both_ledger_and_law_store`. The proposal makes this
    /// conjunction a spec-level rule for state-mutating tools — neither half
    /// of the pair is "the contract" alone.
    pub async fn set_law(
        &mut self,
        yaml: &str,
        version: String,
        diff_summary: Option<String>,
    ) -> Result<&LedgerEntry> {
        let sha = crate::law::Law::sha256_hex_of(yaml);
        self.ledger.store_mut()
            .write_law(yaml).await
            .context("writing law to hub store")?;
        let event = HubEvent::LawAmended {
            new_law_sha256: sha,
            amended_by: self.sovereign_lct_id,
            version,
            diff_summary,
        };
        self.append(event).await
    }

    pub async fn get_law(&self) -> Result<Option<String>> {
        self.ledger.store().read_law().await
    }

    pub async fn declare_skill(&mut self, member_lct_id: Uuid, skill: String) -> Result<&LedgerEntry> {
        let event = HubEvent::MemberSkillDeclared {
            member_lct_id,
            skill,
            declared_by: self.sovereign_lct_id,
        };
        self.append(event).await
    }

    /// Pin (or rotate) an existing member's channel public key — the member
    /// key-enrollment step for members admitted without `member_pubkey_hex`
    /// (CLI-bootstrap path). Without a pinned key a member cannot open the
    /// sealed channel. Validates the hex is a real 32-byte Ed25519 key and
    /// that the member exists before witnessing the pin.
    pub async fn set_member_key(&mut self, member_lct_id: Uuid, pubkey_hex: String) -> Result<&LedgerEntry> {
        // Validate the key parses (reconstructing an Lct exercises the same
        // path the daemon's resolver uses at startup).
        crate::hub::hestia_sovereign_lct(member_lct_id, &pubkey_hex)
            .map_err(|e| anyhow::anyhow!("invalid pubkey hex: {e}"))?;
        let state = HubState::project(&self.ledger);
        if !state.members.contains_key(&member_lct_id) {
            anyhow::bail!("LCT {member_lct_id} is not a member of this hub — add the member first");
        }
        let event = HubEvent::MemberKeyPinned {
            member_lct_id,
            member_pubkey_hex: pubkey_hex,
            pinned_by: self.sovereign_lct_id,
        };
        self.append(event).await
    }

    /// Update a member's free-text profile fields (skills, interests, +
    /// expandable keys) — the inputs to semantic member discovery. Fields
    /// merge into the existing profile; an empty value clears that field.
    pub async fn update_profile(
        &mut self,
        member_lct_id: Uuid,
        fields: std::collections::BTreeMap<String, String>,
    ) -> Result<&LedgerEntry> {
        let event = HubEvent::MemberProfileUpdated {
            member_lct_id,
            fields,
            updated_by: self.sovereign_lct_id,
        };
        self.append(event).await
    }

    pub async fn add_council_member(
        &mut self,
        member_lct_id: Uuid,
        pubkey_hex: String,
        name: Option<String>,
    ) -> Result<&LedgerEntry> {
        let event = HubEvent::CouncilMemberAdded {
            member_lct_id,
            member_pubkey_hex: pubkey_hex,
            added_by: self.sovereign_lct_id,
            member_name: name,
        };
        self.append(event).await
    }

    pub async fn remove_council_member(
        &mut self,
        member_lct_id: Uuid,
        kind: web4_core::role::RoleEventKind,
        reason: Option<String>,
    ) -> Result<&LedgerEntry> {
        let event = HubEvent::CouncilMemberRemoved {
            member_lct_id,
            removed_by: self.sovereign_lct_id,
            removal_kind: kind,
            reason,
        };
        self.append(event).await
    }

    pub async fn set_council_threshold(&mut self, new_m: u32) -> Result<&LedgerEntry> {
        let event = HubEvent::CouncilThresholdChanged {
            new_m,
            initiated_by: self.sovereign_lct_id,
        };
        self.append(event).await
    }

    /// PAIRED-CHANNELS Sprint B: operator-facing helper for creating a
    /// pair request from the CLI. Hestia-mode hubs / REST flows will
    /// construct PairingRequested events directly from signed envelopes;
    /// this is the CLI-convenience shortcut where the Sovereign is the
    /// initiator. Returns the freshly-minted pair_id.
    pub async fn request_pair(
        &mut self,
        counterparty_lct_id: Uuid,
        purpose: String,
        expires_at: Option<DateTime<Utc>>,
    ) -> Result<(Uuid, &LedgerEntry)> {
        let pair_id = Uuid::new_v4();
        let event = HubEvent::PairingRequested {
            pair_id,
            initiator_lct_id: self.sovereign_lct_id,
            counterparty_lct_id,
            purpose,
            proposed_at: Utc::now(),
            expires_at,
        initiator_ephemeral_pub_hex: None,
        };
        let entry = self.append(event).await?;
        Ok((pair_id, entry))
    }

    /// PAIRED-CHANNELS Sprint B: confirm a pair. In CLI mode the
    /// Sovereign confirms (typically used for testing or when the
    /// counterparty is local). Real counterparty-signed confirmations
    /// come through the REST flow with the counterparty's envelope.
    pub async fn confirm_pair(&mut self, pair_id: Uuid) -> Result<&LedgerEntry> {
        let event = HubEvent::PairingConfirmed {
            pair_id,
            confirmed_by: self.sovereign_lct_id,
        counterparty_ephemeral_pub_hex: None,
        };
        self.append(event).await
    }

    /// PAIRED-CHANNELS Sprint B: revoke a pair.
    pub async fn revoke_pair(
        &mut self,
        pair_id: Uuid,
        revocation_kind: crate::events::PairRevocationKind,
        reason: Option<String>,
    ) -> Result<&LedgerEntry> {
        let event = HubEvent::PairingRevoked {
            pair_id,
            revoked_by: self.sovereign_lct_id,
            revocation_kind,
            reason,
        };
        self.append(event).await
    }

    // ---------- queries ----------

    pub fn state(&self) -> HubState {
        HubState::project(&self.ledger)
    }

    pub fn list_members(&self) -> Vec<Member> {
        self.state().members.into_values().collect()
    }

    pub fn find_skill(&self, query: &str) -> Vec<Member> {
        self.state().find_skill(query).into_iter().cloned().collect()
    }

    pub async fn society(&self) -> Result<Society> {
        load_society(self.hub_dir()).await
    }

    pub async fn unfilled_base_roles(&self) -> Result<Vec<SocietyRole>> {
        let society = self.society().await?;
        let mut unfilled = Vec::new();
        for role in SocietyRole::base_mandatory() {
            let key = match serde_json::to_value(&role).ok().and_then(|v| v.as_str().map(|s| s.to_string())) {
                Some(k) => k,
                None => continue,
            };
            if !society.roles.contains_key(&key) {
                unfilled.push(role);
            }
        }
        Ok(unfilled)
    }

    // ---------- internal ----------

    async fn append(&mut self, event: HubEvent) -> Result<&LedgerEntry> {
        self.ledger.append(self.sovereign_lct_id, &self.sovereign_keypair, event).await
    }
}

/// Status snapshot for CLI / API consumption.
#[derive(Debug)]
pub struct HubStatus {
    pub hub_dir: PathBuf,
    pub hub_name: String,
    pub member_count: usize,
    pub ledger_entries: u64,
    pub head_hash: String,
    pub mcp_port: u16,
}

impl HubSession {
    pub fn status(&self) -> HubStatus {
        let state = self.state();
        let member_count = state.member_count();
        HubStatus {
            hub_dir: self.hub_dir().to_path_buf(),
            hub_name: state.hub_name,
            member_count,
            ledger_entries: self.ledger.len() as u64,
            head_hash: self.ledger.head_hash().to_string(),
            mcp_port: self.config.daemon.mcp_port,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::init::{init_hub, InitArgs};
    use tempfile::tempdir;
    use web4_core::lct::EntityType;

    async fn fresh_hub() -> (tempfile::TempDir, PathBuf) {
        let tmp = tempdir().unwrap();
        let sovereign_path = tmp.path().join("sovereign.json");
        IdentityFile::generate(EntityType::Human).save(&sovereign_path).unwrap();
        let hub_dir = tmp.path().join("test-chapter");
        init_hub(InitArgs {
            hub_name: "Test Chapter".into(),
            hub_dir: hub_dir.clone(),
            sovereign_lct_path: sovereign_path,
            storage: None,
        }).await.unwrap();
        (tmp, hub_dir)
    }

    #[tokio::test]
    async fn open_and_status_after_init() {
        let (_tmp, dir) = fresh_hub().await;
        let session = HubSession::open(&dir).await.unwrap();
        let st = session.status();
        assert_eq!(st.hub_name, "Test Chapter");
        assert_eq!(st.ledger_entries, 1); // Genesis
        assert_eq!(st.member_count, 1);   // Sovereign
    }

    #[tokio::test]
    async fn end_to_end_session_ops() {
        let (_tmp, dir) = fresh_hub().await;
        let mut session = HubSession::open(&dir).await.unwrap();

        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();

        session.add_member(alice, Some("Alice".into())).await.unwrap();
        session.add_member(bob, Some("Bob".into())).await.unwrap();
        session.declare_skill(alice, "Medical Imaging RAG".into()).await.unwrap();
        session.declare_skill(bob, "Distributed Systems".into()).await.unwrap();

        let st = session.status();
        assert_eq!(st.member_count, 3); // Sovereign + Alice + Bob
        assert_eq!(st.ledger_entries, 5); // Genesis + 4 ops

        let matches = session.find_skill("imaging");
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0].lct_id, alice);

        // Remove Alice; her skill should drop from the index
        session.remove_member(alice, Some("test removal".into())).await.unwrap();
        let matches = session.find_skill("imaging");
        assert!(matches.is_empty(), "skill index should drop with member");

        let st = session.status();
        assert_eq!(st.member_count, 2); // Sovereign + Bob
    }

    // --- Conjunction-invariant tests (lct-mcp-as-smart-contract proposal §6.3) ---
    //
    // Some state-mutating tools touch BOTH the ledger AND separately-persisted
    // state. For those — flagged as "Conjunction tools" in their rustdoc — the
    // standard requires that both side effects happen as a unit: a ledger event
    // alone is not the contract; a state mutation without the corresponding
    // event is invisible to auditors. PR #292 (be3f8e6) fixed exactly this
    // class of bug on `assign_role`. These tests are the regression net.
    //
    // Current Conjunction tools: `assign_role`, `set_law`. When a new tool
    // joins the category (mutates separately-persisted state alongside its
    // ledger append), add the `Conjunction tool` rustdoc marker AND a parallel
    // `<tool>_writes_both_ledger_and_<state>` test here.

    #[tokio::test]
    async fn assign_role_fills_role_in_society() {
        // Regression: assign_role used to only append a RoleAssigned ledger
        // event without updating the persisted society, so the role never
        // showed as filled in query_chapter / MCP / admin. It must now fold
        // into the society role-fill.
        let (_tmp, dir) = fresh_hub().await;
        let alice = Uuid::new_v4();
        {
            let mut session = HubSession::open(&dir).await.unwrap();
            session.add_member(alice, Some("Alice".into())).await.unwrap();
            session.assign_role(SocietyRole::Administrator, alice).await.unwrap();
        }
        // Re-read society from the store (what query_chapter / admin read).
        let society = load_society(&dir).await.unwrap();
        let admin = society
            .get_role(&SocietyRole::Administrator)
            .expect("Administrator role should be filled after assign_role");
        assert_eq!(
            admin.filling_entity_lct_id, alice,
            "Administrator should be filled by the assigned member"
        );
    }

    #[tokio::test]
    async fn set_law_writes_both_ledger_and_law_store() {
        // Conjunction test (proposal §6.3): set_law is a Category-2 tool — it
        // writes the law text into the store AND appends a LawAmended event.
        // A symmetric regression to the assign_role bug PR #292 fixed would
        // be: amend the law, get a ledger event, but get_law still returns
        // the old text (or None). This test pins both halves.
        let (_tmp, dir) = fresh_hub().await;
        let new_law = "version: 1.0.0\nrules: []\n";
        let entries_after_amend;
        {
            let mut session = HubSession::open(&dir).await.unwrap();
            let entries_before = session.status().ledger_entries;
            session
                .set_law(new_law, "1.0.0".into(), Some("smoke amend".into()))
                .await
                .unwrap();
            entries_after_amend = session.status().ledger_entries;
            assert_eq!(
                entries_after_amend,
                entries_before + 1,
                "set_law must append exactly one ledger entry (the LawAmended event)"
            );
        }
        // Re-open to confirm BOTH halves persist independently of in-memory state.
        let session = HubSession::open(&dir).await.unwrap();
        let stored = session
            .get_law()
            .await
            .unwrap()
            .expect("law store must hold the amended text after set_law");
        assert_eq!(
            stored, new_law,
            "law store must reflect the amended text (the queryable half of the conjunction)"
        );
        assert_eq!(
            session.status().ledger_entries,
            entries_after_amend,
            "ledger half of the conjunction must persist across reopen"
        );
    }

    #[tokio::test]
    async fn update_profile_merges_into_member_profile() {
        let (_tmp, dir) = fresh_hub().await;
        let alice = Uuid::new_v4();
        {
            let mut session = HubSession::open(&dir).await.unwrap();
            session.add_member(alice, Some("Alice".into())).await.unwrap();
            let mut f = std::collections::BTreeMap::new();
            f.insert("skills".to_string(), "diffusion fine-tuning, eval harness design".to_string());
            f.insert("interests".to_string(), "mechanistic interpretability".to_string());
            session.update_profile(alice, f).await.unwrap();
            // Second update merges + clears: change interests, drop skills.
            let mut f2 = std::collections::BTreeMap::new();
            f2.insert("interests".to_string(), "lowering inference cost".to_string());
            f2.insert("skills".to_string(), String::new()); // empty clears
            session.update_profile(alice, f2).await.unwrap();
        }
        let st = HubState::project(&HubSession::open(&dir).await.unwrap().ledger);
        let m = st.members.get(&alice).expect("alice present");
        assert_eq!(m.profile.get("interests").map(String::as_str), Some("lowering inference cost"));
        assert!(!m.profile.contains_key("skills"), "empty value should clear the field");
    }

    #[tokio::test]
    async fn session_writes_persist_across_reopen() {
        let (_tmp, dir) = fresh_hub().await;
        {
            let mut session = HubSession::open(&dir).await.unwrap();
            session.add_member(Uuid::new_v4(), Some("Alice".into())).await.unwrap();
            session.add_member(Uuid::new_v4(), Some("Bob".into())).await.unwrap();
        }
        let session = HubSession::open(&dir).await.unwrap();
        let st = session.status();
        assert_eq!(st.member_count, 3);
        assert_eq!(st.ledger_entries, 3);
    }

    #[tokio::test]
    async fn set_member_key_pins_rotates_and_rejects_bad_input() {
        use web4_core::crypto::KeyPair;
        let (_tmp, dir) = fresh_hub().await;
        let mut session = HubSession::open(&dir).await.unwrap();
        let alice = Uuid::new_v4();
        session.add_member(alice, Some("Alice".into())).await.unwrap();

        // Pin: key lands in member_pubkeys (what the daemon resolver seeds from).
        let k1 = KeyPair::generate().verifying_key().to_hex();
        session.set_member_key(alice, k1.clone()).await.unwrap();
        let state = HubState::project(&session.ledger);
        assert_eq!(state.member_pubkeys.get(&alice), Some(&k1));

        // Rotate: last write wins.
        let k2 = KeyPair::generate().verifying_key().to_hex();
        session.set_member_key(alice, k2.clone()).await.unwrap();
        let state = HubState::project(&session.ledger);
        assert_eq!(state.member_pubkeys.get(&alice), Some(&k2));

        // Reject: non-member LCT, and garbage hex.
        assert!(session.set_member_key(Uuid::new_v4(), k2.clone()).await.is_err());
        assert!(session.set_member_key(alice, "zz".into()).await.is_err());
    }
}
