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
use crate::store::open_chapter_store;

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
        let sovereign = IdentityFile::load(&lct_path)
            .with_context(|| format!(
                "loading Sovereign identity from {}", lct_path.display()
            ))?;
        let keypair = sovereign.keypair()?;
        let store = open_chapter_store(hub_dir)
            .context("opening chapter store for session")?;
        let ledger = HubLedger::open(store).await
            .context("opening ledger via chapter store")?;
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

    pub async fn assign_role(&mut self, role: SocietyRole, role_lct_id: Uuid, member_lct_id: Uuid) -> Result<&LedgerEntry> {
        let event = HubEvent::RoleAssigned {
            role,
            role_lct_id,
            assigned_to: member_lct_id,
            assigned_by: self.sovereign_lct_id,
        };
        self.append(event).await
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

    pub async fn set_law(
        &mut self,
        yaml: &str,
        version: String,
        diff_summary: Option<String>,
    ) -> Result<&LedgerEntry> {
        let sha = crate::law::Law::sha256_hex_of(yaml);
        self.ledger.store_mut()
            .write_law(yaml).await
            .context("writing law to chapter store")?;
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
pub struct ChapterStatus {
    pub hub_dir: PathBuf,
    pub hub_name: String,
    pub member_count: usize,
    pub ledger_entries: u64,
    pub head_hash: String,
    pub mcp_port: u16,
}

impl HubSession {
    pub fn status(&self) -> ChapterStatus {
        let state = self.state();
        let member_count = state.member_count();
        ChapterStatus {
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
    use crate::init::{init_chapter, InitArgs};
    use tempfile::tempdir;
    use web4_core::lct::EntityType;

    async fn fresh_chapter() -> (tempfile::TempDir, PathBuf) {
        let tmp = tempdir().unwrap();
        let sovereign_path = tmp.path().join("sovereign.json");
        IdentityFile::generate(EntityType::Human).save(&sovereign_path).unwrap();
        let hub_dir = tmp.path().join("test-chapter");
        init_chapter(InitArgs {
            hub_name: "Test Chapter".into(),
            hub_dir: hub_dir.clone(),
            sovereign_lct_path: sovereign_path,
            storage: None,
        }).await.unwrap();
        (tmp, hub_dir)
    }

    #[tokio::test]
    async fn open_and_status_after_init() {
        let (_tmp, dir) = fresh_chapter().await;
        let session = HubSession::open(&dir).await.unwrap();
        let st = session.status();
        assert_eq!(st.hub_name, "Test Chapter");
        assert_eq!(st.ledger_entries, 1); // Genesis
        assert_eq!(st.member_count, 1);   // Sovereign
    }

    #[tokio::test]
    async fn end_to_end_session_ops() {
        let (_tmp, dir) = fresh_chapter().await;
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

    #[tokio::test]
    async fn session_writes_persist_across_reopen() {
        let (_tmp, dir) = fresh_chapter().await;
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
}
