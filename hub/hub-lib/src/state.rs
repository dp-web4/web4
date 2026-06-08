// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Event-sourced chapter state projection.
//!
//! The ledger is the source of truth. This module folds the ledger's events
//! into current state (member list, skill index, role-fill snapshot, etc.)
//! for query-time access by MCP tools and the admin CLI.
//!
//! Rebuilt from scratch on each query in MVP; future sprints may cache and
//! incrementally update.

use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use uuid::Uuid;

use crate::events::HubEvent;
use crate::ledger::HubLedger;

/// Projected current state of a chapter, derived from ledger events.
#[derive(Clone, Debug, Default, Serialize)]
pub struct HubState {
    pub hub_name: String,
    pub founding_sovereign_lct_id: Option<Uuid>,
    pub charter_hash: Option<String>,

    /// LCT id → Member record. Members removed via MemberRemoved are dropped.
    pub members: BTreeMap<Uuid, Member>,

    /// Skill index: skill (lowercase) → set of member LCT ids who declared it.
    pub skill_index: BTreeMap<String, BTreeSet<Uuid>>,

    /// Member LCT id → hex-encoded public key (V2-12). Populated from
    /// MemberAdded events that carry a pubkey. Used to seed the envelope
    /// resolver at hub serve startup so member-signed envelopes verify
    /// without an external registry. Members added pre-V2-12 (no pubkey
    /// in their MemberAdded event) are absent here and can't sign
    /// envelopes until re-added with a pubkey.
    pub member_pubkeys: BTreeMap<Uuid, String>,

    /// V2-9 Phase 1: Sovereign Council holders beyond the founding
    /// Sovereign. Empty for single-Sovereign chapters. Each holder
    /// can sign chapter acts as a co-Sovereign; their pubkey is in
    /// `council_pubkeys`.
    pub council_holders: BTreeSet<Uuid>,

    /// V2-9 Phase 1: pubkeys of council holders. Resolver bootstrap
    /// merges these with `member_pubkeys` at hub serve startup so any
    /// council holder's envelope verifies.
    pub council_pubkeys: BTreeMap<Uuid, String>,

    /// V2-9 Phase 1: current M-of-N threshold for council-gated acts.
    /// `None` means single-signer mode. The N component is recomputed
    /// from `council_holders.len() + 1` (the founding Sovereign counts)
    /// at apply time. **Not yet enforced** — informational until
    /// V2-9 Phase 2 ships the proposal/aggregation flow.
    pub council_threshold: Option<(u32, u32)>,

    /// Last seen index from the ledger (for cache invalidation in future).
    pub last_index: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Member {
    pub lct_id: Uuid,
    pub name: Option<String>,
    pub skills: BTreeSet<String>,
}

impl HubState {
    /// Build the projection from a ledger.
    pub fn project(ledger: &HubLedger) -> Self {
        let mut state = HubState::default();
        for entry in ledger.entries() {
            state.apply(&entry.event);
            state.last_index = entry.index;
        }
        state
    }

    fn apply(&mut self, event: &HubEvent) {
        match event {
            HubEvent::Genesis { hub_name, charter_hash, founding_sovereign_lct_id, .. } => {
                self.hub_name = hub_name.clone();
                self.charter_hash = Some(charter_hash.clone());
                self.founding_sovereign_lct_id = Some(*founding_sovereign_lct_id);
                // Sovereign is implicitly a member.
                self.members.entry(*founding_sovereign_lct_id)
                    .or_insert_with(|| Member {
                        lct_id: *founding_sovereign_lct_id,
                        name: Some("Sovereign".into()),
                        skills: BTreeSet::new(),
                    });
            }
            HubEvent::MemberAdded { member_lct_id, member_name, member_pubkey_hex, .. } => {
                self.members.entry(*member_lct_id).or_insert_with(|| Member {
                    lct_id: *member_lct_id,
                    name: member_name.clone(),
                    skills: BTreeSet::new(),
                });
                if let Some(pk) = member_pubkey_hex {
                    self.member_pubkeys.insert(*member_lct_id, pk.clone());
                }
            }
            HubEvent::MemberRemoved { member_lct_id, .. } => {
                if let Some(removed) = self.members.remove(member_lct_id) {
                    // Also drop from skill index.
                    for skill in &removed.skills {
                        if let Some(set) = self.skill_index.get_mut(skill) {
                            set.remove(member_lct_id);
                            if set.is_empty() {
                                self.skill_index.remove(skill);
                            }
                        }
                    }
                }
            }
            HubEvent::MemberSkillDeclared { member_lct_id, skill, .. } => {
                let key = skill.to_lowercase();
                if let Some(member) = self.members.get_mut(member_lct_id) {
                    member.skills.insert(key.clone());
                    self.skill_index.entry(key).or_default().insert(*member_lct_id);
                }
                // If member doesn't exist, silently ignore — event predates
                // their MemberAdded. (Real impl would error or queue.)
            }
            HubEvent::RoleAssigned { .. }
            | HubEvent::EventRecorded { .. }
            | HubEvent::CharterAmended { .. }
            | HubEvent::LawAmended { .. } => {
                // Not projected into HubState yet — these affect society.json /
                // charter.json / hub-law.yaml instead. Future sprints surface
                // them here too.
            }
            HubEvent::CouncilMemberAdded { member_lct_id, member_pubkey_hex, member_name, .. } => {
                self.council_holders.insert(*member_lct_id);
                self.council_pubkeys.insert(*member_lct_id, member_pubkey_hex.clone());
                // Council holders are also members (co-Sovereigns participate
                // in chapter life). Auto-add them to the member registry if
                // not already present, so /admin/members shows them.
                self.members.entry(*member_lct_id).or_insert_with(|| Member {
                    lct_id: *member_lct_id,
                    name: member_name.clone(),
                    skills: BTreeSet::new(),
                });
                // Rebalance N component of threshold if set.
                if let Some((m, _)) = self.council_threshold {
                    let n = (self.council_holders.len() + 1) as u32;
                    self.council_threshold = Some((m, n));
                }
            }
            HubEvent::CouncilMemberRemoved { member_lct_id, .. } => {
                self.council_holders.remove(member_lct_id);
                self.council_pubkeys.remove(member_lct_id);
                if let Some((m, _)) = self.council_threshold {
                    let n = (self.council_holders.len() + 1) as u32;
                    // If removing a holder drops N below M, clamp M to N.
                    let m_clamped = m.min(n.max(1));
                    self.council_threshold = Some((m_clamped, n));
                }
            }
            HubEvent::CouncilThresholdChanged { new_m, .. } => {
                let n = (self.council_holders.len() + 1) as u32;
                let m = (*new_m).clamp(1, n.max(1));
                self.council_threshold = Some((m, n));
            }
        }
    }

    /// Members who declared a skill matching the query (case-insensitive substring).
    pub fn find_skill(&self, query: &str) -> Vec<&Member> {
        let q = query.to_lowercase();
        let mut out = Vec::new();
        let mut seen: BTreeSet<Uuid> = BTreeSet::new();
        for (skill, lct_ids) in &self.skill_index {
            if skill.contains(&q) {
                for id in lct_ids {
                    if seen.insert(*id) {
                        if let Some(m) = self.members.get(id) {
                            out.push(m);
                        }
                    }
                }
            }
        }
        out
    }

    pub fn member_count(&self) -> usize { self.members.len() }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hub::HubPaths;
    use crate::identity::IdentityFile;
    use crate::ledger::HubLedger;
    use crate::store::FileBackend;
    use chrono::Utc;
    use tempfile::tempdir;
    use web4_core::lct::EntityType;

    fn make_ledger_with(events: Vec<(Uuid, &web4_core::crypto::KeyPair, HubEvent)>)
        -> (tempfile::TempDir, HubLedger)
    {
        let tmp = tempdir().unwrap();
        let chap = tmp.path().join("chap");
        std::fs::create_dir_all(&chap).unwrap();
        let store: Box<dyn crate::store::HubStore> =
            Box::new(FileBackend::new(HubPaths::new(chap)));
        let mut ledger = HubLedger::open(store).unwrap();
        for (actor, kp, event) in events {
            // First event must be Genesis; for tests we treat all as plain entries
            // but use write_genesis for the first.
            if ledger.is_empty() {
                if let HubEvent::Genesis { hub_name, charter_hash, founding_sovereign_lct_id, .. } = &event {
                    ledger.write_genesis(
                        *founding_sovereign_lct_id, kp,
                        hub_name.clone(),
                        charter_hash.clone(),
                    ).unwrap();
                    continue;
                } else {
                    panic!("first event in test fixture must be Genesis");
                }
            }
            ledger.append(actor, kp, event).unwrap();
        }
        (tmp, ledger)
    }

    #[test]
    fn project_genesis_seeds_sovereign_as_member() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: Utc::now(),
            }),
        ]);
        let state = HubState::project(&ledger);
        assert_eq!(state.member_count(), 1);
        assert!(state.members.contains_key(&sov.lct.id));
    }

    #[test]
    fn member_added_and_removed_round_trip() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: Utc::now(),
            }),
            (sov.lct.id, &kp, HubEvent::MemberAdded {
                member_lct_id: alice,
                added_by: sov.lct.id,
                member_name: Some("Alice".into()),
                member_pubkey_hex: None,
            }),
            (sov.lct.id, &kp, HubEvent::MemberSkillDeclared {
                member_lct_id: alice,
                skill: "Rust".into(),
                declared_by: sov.lct.id,
            }),
            (sov.lct.id, &kp, HubEvent::MemberRemoved {
                member_lct_id: alice,
                removed_by: sov.lct.id,
                reason: Some("left chapter".into()),
            }),
        ]);
        let state = HubState::project(&ledger);
        assert_eq!(state.member_count(), 1); // just Sovereign
        assert!(!state.members.contains_key(&alice));
        // Skill index should also drop the orphaned skill entry.
        assert!(state.find_skill("rust").is_empty());
    }

    #[test]
    fn find_skill_is_case_insensitive_substring() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: Utc::now(),
            }),
            (sov.lct.id, &kp, HubEvent::MemberAdded { member_lct_id: alice, added_by: sov.lct.id, member_name: Some("Alice".into()), member_pubkey_hex: None }),
            (sov.lct.id, &kp, HubEvent::MemberAdded { member_lct_id: bob, added_by: sov.lct.id, member_name: Some("Bob".into()), member_pubkey_hex: None }),
            (sov.lct.id, &kp, HubEvent::MemberSkillDeclared { member_lct_id: alice, skill: "Medical Imaging RAG".into(), declared_by: sov.lct.id }),
            (sov.lct.id, &kp, HubEvent::MemberSkillDeclared { member_lct_id: bob, skill: "Distributed Systems".into(), declared_by: sov.lct.id }),
        ]);
        let state = HubState::project(&ledger);
        let matches = state.find_skill("RAG");
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0].lct_id, alice);

        let matches = state.find_skill("imaging");
        assert_eq!(matches.len(), 1);

        let matches = state.find_skill("nothing");
        assert_eq!(matches.len(), 0);
    }
}
