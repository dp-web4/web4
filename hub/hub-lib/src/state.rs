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

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use uuid::Uuid;

use crate::events::{HubEvent, PairRevocationKind};
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

    /// PAIRED-CHANNELS Sprint B: pair_id → PairState. Tracks the
    /// lifecycle of every LCT-to-LCT pair the chapter has hosted.
    /// Cleared on hub recovery via projection from the ledger.
    pub pairs: BTreeMap<Uuid, PairState>,

    /// Last seen index from the ledger (for cache invalidation in future).
    pub last_index: u64,
}

/// PAIRED-CHANNELS Sprint B: projected state of a single pair.
/// Built from PairingRequested / PairingConfirmed / PairingRevoked
/// events. Status transitions are strictly monotonic:
/// `Pending` → `Active` → `Revoked`; or `Pending` → `Revoked`
/// (request cancelled before confirm).
///
/// Note: `Expired` is a derived state computed against current time
/// (see [`PairState::effective_status`]); the stored `status` only
/// transitions on explicit events. This keeps projection deterministic
/// (no time-dependent rebuilds) while still surfacing expiry to
/// queries.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PairState {
    pub id: Uuid,
    pub initiator: Uuid,
    pub counterparty: Uuid,
    pub purpose: String,
    pub status: PairStatus,
    pub proposed_at: DateTime<Utc>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub expires_at: Option<DateTime<Utc>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub confirmed_at: Option<DateTime<Utc>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub revoked_at: Option<DateTime<Utc>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub revocation_kind: Option<PairRevocationKind>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub revocation_reason: Option<String>,
    /// PAIRED-CHANNELS Sprint D will increment this per relayed message.
    /// Used as a trust-accrual signal in Sprint G. Sprint B leaves it at 0.
    #[serde(default)]
    pub message_count: u64,
    /// PAIRED-CHANNELS Sprint F: initiator's per-session ephemeral
    /// X25519 public key (hex), surfaced from PairingRequested. The
    /// counterparty reads this from the pair detail + uses it (with
    /// their own ephemeral secret) to derive the v2 session key.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub initiator_ephemeral_pub_hex: Option<String>,
    /// PAIRED-CHANNELS Sprint F: counterparty's per-session ephemeral
    /// X25519 public key (hex), surfaced from PairingConfirmed.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub counterparty_ephemeral_pub_hex: Option<String>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PairStatus {
    /// Initiator requested; counterparty hasn't confirmed yet.
    Pending,
    /// Both parties have signed; the pair is live.
    Active,
    /// Explicitly revoked (any `PairRevocationKind`).
    Revoked,
}

impl PairState {
    /// True iff either initiator or counterparty matches `lct_id`.
    /// Used by queries like "show me my pairs".
    pub fn includes(&self, lct_id: Uuid) -> bool {
        self.initiator == lct_id || self.counterparty == lct_id
    }

    /// Status taking expiry into account. If `status == Active` and
    /// we're past `expires_at`, returns Expired. Otherwise returns
    /// the stored status as a corresponding effective string.
    ///
    /// String-typed so callers don't need to handle the synthetic
    /// `Expired` value vs. the projected `Revoked` value — both
    /// mean "no longer usable."
    pub fn effective_status(&self, now: DateTime<Utc>) -> &'static str {
        match self.status {
            PairStatus::Active => {
                if let Some(exp) = self.expires_at {
                    if now >= exp { return "expired"; }
                }
                "active"
            }
            PairStatus::Pending => "pending",
            PairStatus::Revoked => "revoked",
        }
    }
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
            state.apply(&entry.event, entry.timestamp);
            state.last_index = entry.index;
        }
        state
    }

    fn apply(&mut self, event: &HubEvent, ts: DateTime<Utc>) {
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
            HubEvent::PairingRequested {
                pair_id, initiator_lct_id, counterparty_lct_id,
                purpose, proposed_at, expires_at,
                initiator_ephemeral_pub_hex,
            } => {
                // Idempotent: if a pair with this id already exists
                // (replay scenario), keep the original — the ledger's
                // chain integrity says the first occurrence wins.
                self.pairs.entry(*pair_id).or_insert_with(|| PairState {
                    id: *pair_id,
                    initiator: *initiator_lct_id,
                    counterparty: *counterparty_lct_id,
                    purpose: purpose.clone(),
                    status: PairStatus::Pending,
                    proposed_at: *proposed_at,
                    expires_at: *expires_at,
                    confirmed_at: None,
                    revoked_at: None,
                    revocation_kind: None,
                    revocation_reason: None,
                    message_count: 0,
                    initiator_ephemeral_pub_hex: initiator_ephemeral_pub_hex.clone(),
                    counterparty_ephemeral_pub_hex: None,
                });
            }
            HubEvent::PairingConfirmed { pair_id, confirmed_by, counterparty_ephemeral_pub_hex } => {
                // Confirmation is only valid from the counterparty
                // (REST layer enforces this; here we defensively
                // re-check so a hand-crafted ledger entry can't
                // sneak through projection).
                if let Some(p) = self.pairs.get_mut(pair_id) {
                    if p.status == PairStatus::Pending
                        && *confirmed_by == p.counterparty
                    {
                        p.status = PairStatus::Active;
                        p.confirmed_at = Some(ts);
                        // Sprint F: record counterparty's ephemeral if supplied.
                        if counterparty_ephemeral_pub_hex.is_some() {
                            p.counterparty_ephemeral_pub_hex =
                                counterparty_ephemeral_pub_hex.clone();
                        }
                    }
                    // Else: confirmation from non-counterparty, or
                    // already-active/revoked — silent no-op. The
                    // REST layer should have prevented this; not
                    // worth crashing projection if it slips through.
                }
            }
            HubEvent::PairingRevoked {
                pair_id, revoked_by: _, revocation_kind, reason,
            } => {
                if let Some(p) = self.pairs.get_mut(pair_id) {
                    // Revocation is allowed from either party; chapter
                    // law / V2-9 council enforcement is the only way to
                    // restrict who can revoke. Once revoked, stays
                    // revoked (subsequent revoke events are no-ops).
                    if p.status != PairStatus::Revoked {
                        p.status = PairStatus::Revoked;
                        p.revoked_at = Some(ts);
                        p.revocation_kind = Some(revocation_kind.clone());
                        p.revocation_reason = reason.clone();
                    }
                }
            }
            HubEvent::PairMessagePosted { pair_id, .. } => {
                // Sprint D: bump per-pair message_count. The actual
                // payload lives in the sidecar (HubStore::append_pair_message);
                // projection just counts that a message happened. This
                // is what feeds V3 trust accrual in Sprint G.
                if let Some(p) = self.pairs.get_mut(pair_id) {
                    p.message_count = p.message_count.saturating_add(1);
                }
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

    async fn make_ledger_with(events: Vec<(Uuid, &web4_core::crypto::KeyPair, HubEvent)>)
        -> (tempfile::TempDir, HubLedger)
    {
        let tmp = tempdir().unwrap();
        let chap = tmp.path().join("chap");
        std::fs::create_dir_all(&chap).unwrap();
        let store: Box<dyn crate::store::HubStore> =
            Box::new(FileBackend::new(HubPaths::new(chap)));
        let mut ledger = HubLedger::open(store).await.unwrap();
        for (actor, kp, event) in events {
            // First event must be Genesis; for tests we treat all as plain entries
            // but use write_genesis for the first.
            if ledger.is_empty() {
                if let HubEvent::Genesis { hub_name, charter_hash, founding_sovereign_lct_id, .. } = &event {
                    ledger.write_genesis(
                        *founding_sovereign_lct_id, kp,
                        hub_name.clone(),
                        charter_hash.clone(),
                    ).await.unwrap();
                    continue;
                } else {
                    panic!("first event in test fixture must be Genesis");
                }
            }
            ledger.append(actor, kp, event).await.unwrap();
        }
        (tmp, ledger)
    }

    #[tokio::test]
    async fn project_genesis_seeds_sovereign_as_member() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: Utc::now(),
            }),
        ]).await;
        let state = HubState::project(&ledger);
        assert_eq!(state.member_count(), 1);
        assert!(state.members.contains_key(&sov.lct.id));
    }

    #[tokio::test]
    async fn member_added_and_removed_round_trip() {
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
        ]).await;
        let state = HubState::project(&ledger);
        assert_eq!(state.member_count(), 1); // just Sovereign
        assert!(!state.members.contains_key(&alice));
        // Skill index should also drop the orphaned skill entry.
        assert!(state.find_skill("rust").is_empty());
    }

    #[tokio::test]
    async fn find_skill_is_case_insensitive_substring() {
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
        ]).await;
        let state = HubState::project(&ledger);
        let matches = state.find_skill("RAG");
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0].lct_id, alice);

        let matches = state.find_skill("imaging");
        assert_eq!(matches.len(), 1);

        let matches = state.find_skill("nothing");
        assert_eq!(matches.len(), 0);
    }

    // ---------- PAIRED-CHANNELS Sprint B ----------

    /// Happy path: request → confirm → projection shows Active pair
    /// with correct initiator/counterparty/purpose; the entry's
    /// timestamp from the ledger is the `confirmed_at`.
    #[tokio::test]
    async fn pair_request_then_confirm_projects_active() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let pair_id = Uuid::new_v4();
        let t0 = Utc::now();

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Pairs Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: t0,
            }),
            (alice, &kp, HubEvent::PairingRequested {
                pair_id,
                initiator_lct_id: alice,
                counterparty_lct_id: bob,
                purpose: "code review collab".into(),
                proposed_at: t0,
                expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
            (bob, &kp, HubEvent::PairingConfirmed {
                pair_id,
                confirmed_by: bob,
            counterparty_ephemeral_pub_hex: None,
            }),
        ]).await;

        let state = HubState::project(&ledger);
        let pair = state.pairs.get(&pair_id).expect("pair projected");
        assert_eq!(pair.id, pair_id);
        assert_eq!(pair.initiator, alice);
        assert_eq!(pair.counterparty, bob);
        assert_eq!(pair.purpose, "code review collab");
        assert_eq!(pair.status, PairStatus::Active);
        assert!(pair.confirmed_at.is_some());
        assert!(pair.includes(alice));
        assert!(pair.includes(bob));
        assert!(!pair.includes(Uuid::new_v4()));
    }

    /// Confirmation from someone OTHER than the named counterparty
    /// must be a no-op at projection level (REST layer should have
    /// rejected; this is defense in depth).
    #[tokio::test]
    async fn pair_confirmation_from_wrong_signer_is_ignored() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let mallory = Uuid::new_v4();
        let pair_id = Uuid::new_v4();
        let t0 = Utc::now();

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Pairs Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: t0,
            }),
            (alice, &kp, HubEvent::PairingRequested {
                pair_id,
                initiator_lct_id: alice,
                counterparty_lct_id: bob,
                purpose: "p".into(),
                proposed_at: t0,
                expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
            // Mallory (not the counterparty) confirms — must be rejected.
            (mallory, &kp, HubEvent::PairingConfirmed {
                pair_id,
                confirmed_by: mallory,
            counterparty_ephemeral_pub_hex: None,
            }),
        ]).await;

        let state = HubState::project(&ledger);
        let pair = state.pairs.get(&pair_id).expect("pair exists");
        assert_eq!(pair.status, PairStatus::Pending,
            "confirmation from non-counterparty must not activate the pair");
        assert!(pair.confirmed_at.is_none());
    }

    /// Revoke-before-confirm cancels the pending pair. Status moves
    /// straight to Revoked without ever becoming Active.
    #[tokio::test]
    async fn pair_revoke_before_confirm_cancels() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let pair_id = Uuid::new_v4();
        let t0 = Utc::now();

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Pairs Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: t0,
            }),
            (alice, &kp, HubEvent::PairingRequested {
                pair_id,
                initiator_lct_id: alice,
                counterparty_lct_id: bob,
                purpose: "p".into(),
                proposed_at: t0,
                expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
            (alice, &kp, HubEvent::PairingRevoked {
                pair_id,
                revoked_by: alice,
                revocation_kind: PairRevocationKind::Voluntary,
                reason: Some("changed my mind".into()),
            }),
        ]).await;

        let state = HubState::project(&ledger);
        let pair = state.pairs.get(&pair_id).unwrap();
        assert_eq!(pair.status, PairStatus::Revoked);
        assert!(pair.confirmed_at.is_none(), "never reached Active");
        assert!(pair.revoked_at.is_some());
        assert_eq!(pair.revocation_kind, Some(PairRevocationKind::Voluntary));
        assert_eq!(pair.revocation_reason.as_deref(), Some("changed my mind"));
    }

    /// Once revoked, subsequent revoke events don't bump the revocation
    /// timestamp / kind. First revocation is canonical.
    #[tokio::test]
    async fn pair_revoke_is_idempotent() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let pair_id = Uuid::new_v4();
        let t0 = Utc::now();

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "Pairs Test".into(),
                charter_hash: "sha256:0".into(),
                founding_sovereign_lct_id: sov.lct.id,
                created_at: t0,
            }),
            (alice, &kp, HubEvent::PairingRequested {
                pair_id, initiator_lct_id: alice, counterparty_lct_id: bob,
                purpose: "p".into(), proposed_at: t0, expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
            (alice, &kp, HubEvent::PairingRevoked {
                pair_id, revoked_by: alice,
                revocation_kind: PairRevocationKind::Voluntary,
                reason: Some("first".into()),
            }),
            (alice, &kp, HubEvent::PairingRevoked {
                pair_id, revoked_by: alice,
                revocation_kind: PairRevocationKind::HubLaw,
                reason: Some("second — should be ignored".into()),
            }),
        ]).await;

        let state = HubState::project(&ledger);
        let pair = state.pairs.get(&pair_id).unwrap();
        assert_eq!(pair.revocation_kind, Some(PairRevocationKind::Voluntary),
            "first revocation wins; second is no-op");
        assert_eq!(pair.revocation_reason.as_deref(), Some("first"));
    }

    /// Multiple distinct pairs coexist without interference.
    #[tokio::test]
    async fn multiple_pairs_project_independently() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let carol = Uuid::new_v4();
        let p1 = Uuid::new_v4();
        let p2 = Uuid::new_v4();
        let t0 = Utc::now();

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "T".into(), charter_hash: "0".into(),
                founding_sovereign_lct_id: sov.lct.id, created_at: t0,
            }),
            // alice-bob: confirmed
            (alice, &kp, HubEvent::PairingRequested {
                pair_id: p1, initiator_lct_id: alice, counterparty_lct_id: bob,
                purpose: "p1".into(), proposed_at: t0, expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
            (bob, &kp, HubEvent::PairingConfirmed { pair_id: p1, confirmed_by: bob, counterparty_ephemeral_pub_hex: None }),
            // alice-carol: still pending
            (alice, &kp, HubEvent::PairingRequested {
                pair_id: p2, initiator_lct_id: alice, counterparty_lct_id: carol,
                purpose: "p2".into(), proposed_at: t0, expires_at: None,
            initiator_ephemeral_pub_hex: None,
            }),
        ]).await;

        let state = HubState::project(&ledger);
        assert_eq!(state.pairs.len(), 2);
        assert_eq!(state.pairs[&p1].status, PairStatus::Active);
        assert_eq!(state.pairs[&p2].status, PairStatus::Pending);
        // Alice is in both; bob in only p1; carol in only p2.
        let alices_pairs: Vec<_> = state.pairs.values()
            .filter(|p| p.includes(alice)).collect();
        assert_eq!(alices_pairs.len(), 2);
    }

    /// `effective_status` returns "expired" when past `expires_at`
    /// even though the stored status is still Active.
    #[tokio::test]
    async fn pair_effective_status_handles_expiry() {
        let sov = IdentityFile::generate(EntityType::Human);
        let kp = sov.keypair().unwrap();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let pair_id = Uuid::new_v4();
        let t0 = Utc::now();
        let expires = t0 + chrono::Duration::seconds(60);

        let (_tmp, ledger) = make_ledger_with(vec![
            (sov.lct.id, &kp, HubEvent::Genesis {
                hub_name: "T".into(), charter_hash: "0".into(),
                founding_sovereign_lct_id: sov.lct.id, created_at: t0,
            }),
            (alice, &kp, HubEvent::PairingRequested {
                pair_id, initiator_lct_id: alice, counterparty_lct_id: bob,
                purpose: "p".into(), proposed_at: t0,
                expires_at: Some(expires),
            initiator_ephemeral_pub_hex: None,
            }),
            (bob, &kp, HubEvent::PairingConfirmed { pair_id, confirmed_by: bob, counterparty_ephemeral_pub_hex: None }),
        ]).await;

        let state = HubState::project(&ledger);
        let pair = state.pairs.get(&pair_id).unwrap();
        assert_eq!(pair.effective_status(t0 + chrono::Duration::seconds(30)), "active");
        assert_eq!(pair.effective_status(t0 + chrono::Duration::seconds(120)), "expired");
    }

    /// Serde round-trip for the new event types via the existing
    /// HubEvent kind-tag machinery. Catches schema-level breakage.
    #[tokio::test]
    async fn pair_events_serde_round_trip() {
        let pair_id = Uuid::new_v4();
        let alice = Uuid::new_v4();
        let bob = Uuid::new_v4();
        let t0 = Utc::now();

        let req = HubEvent::PairingRequested {
            pair_id, initiator_lct_id: alice, counterparty_lct_id: bob,
            purpose: "x".into(), proposed_at: t0, expires_at: None,
        initiator_ephemeral_pub_hex: None,
        };
        let req_json = serde_json::to_string(&req).unwrap();
        assert!(req_json.contains("\"kind\":\"pairing_requested\""));
        let back: HubEvent = serde_json::from_str(&req_json).unwrap();
        assert_eq!(back.kind(), "pairing_requested");

        let conf = HubEvent::PairingConfirmed { pair_id, confirmed_by: bob, counterparty_ephemeral_pub_hex: None };
        let conf_json = serde_json::to_string(&conf).unwrap();
        assert!(conf_json.contains("\"kind\":\"pairing_confirmed\""));

        let rev = HubEvent::PairingRevoked {
            pair_id, revoked_by: alice,
            revocation_kind: PairRevocationKind::HubLaw,
            reason: None,
        };
        let rev_json = serde_json::to_string(&rev).unwrap();
        assert!(rev_json.contains("\"kind\":\"pairing_revoked\""));
        // Canonical form after the chapter→hub rename.
        assert!(rev_json.contains("\"revocation_kind\":\"hub_law\""));
        // No reason -> field skipped
        assert!(!rev_json.contains("\"reason\""));

        // Back-compat: pre-rename ledgers serialized this as "chapter_law";
        // the serde alias must still deserialize them.
        let legacy = rev_json.replace("\"hub_law\"", "\"chapter_law\"");
        let back: HubEvent = serde_json::from_str(&legacy).unwrap();
        match back {
            HubEvent::PairingRevoked { revocation_kind, .. } => {
                assert_eq!(revocation_kind, PairRevocationKind::HubLaw);
            }
            _ => panic!("expected PairingRevoked"),
        }
    }
}
