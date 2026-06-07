// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! ChapterSession — the operator-facing API for a chapter.
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

use crate::chapter::{ChapterConfig, ChapterPaths};
use crate::events::ChapterEvent;
use crate::identity::IdentityFile;
use crate::init::load_society;
use crate::ledger::{ChapterLedger, LedgerEntry};
use crate::state::{ChapterState, Member};
use crate::store::open_chapter_store;

/// One open chapter, ready for ops. Drop to close.
pub struct ChapterSession {
    pub paths: ChapterPaths,
    pub config: ChapterConfig,
    pub sovereign_lct_id: Uuid,
    pub sovereign_keypair: KeyPair,
    pub ledger: ChapterLedger,
}

impl ChapterSession {
    pub fn open(chapter_dir: impl AsRef<Path>) -> Result<Self> {
        let chapter_dir = chapter_dir.as_ref();
        let paths = ChapterPaths::new(chapter_dir.to_path_buf());
        let config = ChapterConfig::load(paths.config())
            .with_context(|| format!("loading config at {}", paths.config().display()))?;
        let sovereign = IdentityFile::load(&config.sovereign.lct_path)
            .with_context(|| format!(
                "loading Sovereign identity from {}",
                config.sovereign.lct_path.display()
            ))?;
        let keypair = sovereign.keypair()?;
        let store = open_chapter_store(chapter_dir)
            .context("opening chapter store for session")?;
        let ledger = ChapterLedger::open(store)
            .context("opening ledger via chapter store")?;
        Ok(Self {
            paths,
            config,
            sovereign_lct_id: sovereign.lct.id,
            sovereign_keypair: keypair,
            ledger,
        })
    }

    pub fn chapter_dir(&self) -> &Path { &self.paths.root }

    // ---------- mutations ----------

    pub fn add_member(&mut self, member_lct_id: Uuid, name: Option<String>) -> Result<&LedgerEntry> {
        let event = ChapterEvent::MemberAdded {
            member_lct_id,
            added_by: self.sovereign_lct_id,
            member_name: name,
        };
        self.append(event)
    }

    pub fn remove_member(&mut self, member_lct_id: Uuid, reason: Option<String>) -> Result<&LedgerEntry> {
        let event = ChapterEvent::MemberRemoved {
            member_lct_id,
            removed_by: self.sovereign_lct_id,
            reason,
        };
        self.append(event)
    }

    pub fn assign_role(&mut self, role: SocietyRole, role_lct_id: Uuid, member_lct_id: Uuid) -> Result<&LedgerEntry> {
        let event = ChapterEvent::RoleAssigned {
            role,
            role_lct_id,
            assigned_to: member_lct_id,
            assigned_by: self.sovereign_lct_id,
        };
        self.append(event)
    }

    pub fn record_event(
        &mut self,
        event_kind: String,
        title: String,
        attended_by: Vec<Uuid>,
        held_at: Option<DateTime<Utc>>,
    ) -> Result<&LedgerEntry> {
        let event = ChapterEvent::EventRecorded {
            event_kind,
            title,
            attended_by,
            recorded_by: self.sovereign_lct_id,
            held_at: held_at.unwrap_or_else(Utc::now),
        };
        self.append(event)
    }

    pub fn declare_skill(&mut self, member_lct_id: Uuid, skill: String) -> Result<&LedgerEntry> {
        let event = ChapterEvent::MemberSkillDeclared {
            member_lct_id,
            skill,
            declared_by: self.sovereign_lct_id,
        };
        self.append(event)
    }

    // ---------- queries ----------

    pub fn state(&self) -> ChapterState {
        ChapterState::project(&self.ledger)
    }

    pub fn list_members(&self) -> Vec<Member> {
        self.state().members.into_values().collect()
    }

    pub fn find_skill(&self, query: &str) -> Vec<Member> {
        self.state().find_skill(query).into_iter().cloned().collect()
    }

    pub fn society(&self) -> Result<Society> {
        load_society(self.chapter_dir())
    }

    /// Base-mandatory roles per Web4 spec that are NOT currently filled in
    /// the society state. Useful for status reporting and "what does the
    /// chapter still need to assign?" guidance.
    pub fn unfilled_base_roles(&self) -> Result<Vec<SocietyRole>> {
        let society = self.society()?;
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

    fn append(&mut self, event: ChapterEvent) -> Result<&LedgerEntry> {
        self.ledger.append(self.sovereign_lct_id, &self.sovereign_keypair, event)
    }
}

/// Status snapshot for CLI / API consumption.
#[derive(Debug)]
pub struct ChapterStatus {
    pub chapter_dir: PathBuf,
    pub chapter_name: String,
    pub member_count: usize,
    pub ledger_entries: u64,
    pub head_hash: String,
    pub mcp_port: u16,
}

impl ChapterSession {
    pub fn status(&self) -> ChapterStatus {
        let state = self.state();
        let member_count = state.member_count();
        ChapterStatus {
            chapter_dir: self.chapter_dir().to_path_buf(),
            chapter_name: state.chapter_name,
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

    fn fresh_chapter() -> (tempfile::TempDir, PathBuf) {
        let tmp = tempdir().unwrap();
        let sovereign_path = tmp.path().join("sovereign.json");
        IdentityFile::generate(EntityType::Human).save(&sovereign_path).unwrap();
        let chapter_dir = tmp.path().join("test-chapter");
        init_chapter(InitArgs {
            chapter_name: "Test Chapter".into(),
            chapter_dir: chapter_dir.clone(),
            sovereign_lct_path: sovereign_path,
        }).unwrap();
        (tmp, chapter_dir)
    }

    #[test]
    fn open_and_status_after_init() {
        let (_tmp, dir) = fresh_chapter();
        let session = ChapterSession::open(&dir).unwrap();
        let st = session.status();
        assert_eq!(st.chapter_name, "Test Chapter");
        assert_eq!(st.ledger_entries, 1); // Genesis
        assert_eq!(st.member_count, 1);   // Sovereign
    }

    #[test]
    fn end_to_end_session_ops() {
        let (_tmp, dir) = fresh_chapter();
        let mut session = ChapterSession::open(&dir).unwrap();

        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();

        session.add_member(alice, Some("Alice".into())).unwrap();
        session.add_member(bob, Some("Bob".into())).unwrap();
        session.declare_skill(alice, "Medical Imaging RAG".into()).unwrap();
        session.declare_skill(bob, "Distributed Systems".into()).unwrap();

        let st = session.status();
        assert_eq!(st.member_count, 3); // Sovereign + Alice + Bob
        assert_eq!(st.ledger_entries, 5); // Genesis + 4 ops

        let matches = session.find_skill("imaging");
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0].lct_id, alice);

        // Remove Alice; her skill should drop from the index
        session.remove_member(alice, Some("test removal".into())).unwrap();
        let matches = session.find_skill("imaging");
        assert!(matches.is_empty(), "skill index should drop with member");

        let st = session.status();
        assert_eq!(st.member_count, 2); // Sovereign + Bob
    }

    #[test]
    fn session_writes_persist_across_reopen() {
        let (_tmp, dir) = fresh_chapter();
        {
            let mut session = ChapterSession::open(&dir).unwrap();
            session.add_member(Uuid::new_v4(), Some("Alice".into())).unwrap();
            session.add_member(Uuid::new_v4(), Some("Bob".into())).unwrap();
        }
        let session = ChapterSession::open(&dir).unwrap();
        let st = session.status();
        assert_eq!(st.member_count, 3);
        assert_eq!(st.ledger_entries, 3);
    }
}
