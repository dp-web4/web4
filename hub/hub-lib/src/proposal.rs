// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! V2-9 Phase 2: Sovereign Council proposal + aggregation flow.
//!
//! A `CouncilProposal` is a draft chapter act awaiting M-of-N
//! counter-signatures from the Sovereign Council. Each "vote" is a
//! full [`crate::envelope::SignedEnvelope`] from a council holder; we
//! store envelopes (not bare signatures) so each vote remains
//! independently verifiable after the fact — anyone can re-verify
//! `envelope.signature` against `envelope.signing_bytes()` and the
//! signer's pubkey, no trust in the hub required.
//!
//! When the unique-signer count reaches M (per the chapter's current
//! `council_threshold` at commit-time), the hub appends the proposed
//! event to the ledger normally — actor = founding Sovereign (the
//! daemon's executor), signed by the hub's signer. The proposal
//! record persists the M holder signatures as the authorization
//! audit trail, linked to the ledger by `entry_index` in the
//! Committed status.
//!
//! Per architecture commitment #5 (multi-Sovereign Council from the
//! start) + commitment #1 (law always signed and auditable). Phase 1
//! shipped the state model + management; this module ships enforcement.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use uuid::Uuid;

use crate::envelope::SignedEnvelope;
use crate::events::HubEvent;

/// Maximum lifetime of an open proposal before it expires. Operators
/// can extend by re-proposing. 24 hours is a defensible default — long
/// enough for asynchronous councils across time zones, short enough
/// that stale proposals don't pile up indefinitely.
pub const DEFAULT_PROPOSAL_TTL_HOURS: i64 = 24;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CouncilProposal {
    pub id: Uuid,
    /// The HubEvent this proposal would commit to the ledger.
    pub proposed_event: HubEvent,
    /// The council holder who created the proposal (first vote).
    pub proposed_by: Uuid,
    pub proposed_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    /// Recorded votes. Each is a full envelope; same signer voting
    /// twice is deduplicated by `unique_signers()`. Envelope nonces
    /// are still consumed from the NonceStore on receipt, so two
    /// votes from the same signer must use distinct nonces — that's
    /// fine, we just count unique `signer_lct_id` values.
    pub votes: Vec<ProposalVote>,
    pub status: ProposalStatus,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ProposalVote {
    pub signer_lct_id: Uuid,
    pub envelope: SignedEnvelope,
    pub voted_at: DateTime<Utc>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum ProposalStatus {
    /// Awaiting more signatures.
    Open,
    /// Threshold met; act was appended to the ledger.
    Committed {
        entry_index: u64,
        committed_at: DateTime<Utc>,
    },
    /// Operator (or law-driven escalation) rejected the proposal.
    Rejected { reason: String },
    /// Past `expires_at`; cleaned up by next propose/sign call.
    Expired,
}

impl CouncilProposal {
    /// Create a fresh proposal. The creator's vote is added separately
    /// via [`Self::add_vote`] after the envelope verifies.
    pub fn new(proposed_event: HubEvent, proposed_by: Uuid, now: DateTime<Utc>) -> Self {
        Self {
            id: Uuid::new_v4(),
            proposed_event,
            proposed_by,
            proposed_at: now,
            expires_at: now + chrono::Duration::hours(DEFAULT_PROPOSAL_TTL_HOURS),
            votes: Vec::new(),
            status: ProposalStatus::Open,
        }
    }

    /// Record a vote. Caller has already verified the envelope.
    pub fn add_vote(&mut self, envelope: SignedEnvelope, now: DateTime<Utc>) {
        self.votes.push(ProposalVote {
            signer_lct_id: envelope.signer_lct_id,
            envelope,
            voted_at: now,
        });
    }

    /// Unique council-holder LCT ids who have voted.
    pub fn unique_signers(&self) -> BTreeSet<Uuid> {
        self.votes.iter().map(|v| v.signer_lct_id).collect()
    }

    /// Check whether the recorded votes meet the threshold, given
    /// the current set of valid council holders (founding Sovereign
    /// included). M-of-N: at least M unique votes from holders in
    /// the `holders` set.
    pub fn meets_threshold(&self, m: u32, holders: &BTreeSet<Uuid>) -> bool {
        let valid = self.unique_signers().intersection(holders).count();
        valid >= m as usize
    }

    pub fn is_open(&self) -> bool {
        matches!(self.status, ProposalStatus::Open)
    }

    pub fn is_expired_at(&self, now: DateTime<Utc>) -> bool {
        now >= self.expires_at
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn mk_envelope(signer: Uuid) -> SignedEnvelope {
        SignedEnvelope {
            challenge_nonce: format!("nonce-{}", signer),
            payload: serde_json::json!({}),
            signature: "00".repeat(64),
            signer_lct_id: signer,
        }
    }

    fn mk_proposal() -> CouncilProposal {
        let event = HubEvent::MemberAdded {
            member_lct_id: Uuid::new_v4(),
            added_by: Uuid::new_v4(),
            member_name: Some("test".into()),
            member_pubkey_hex: None,
        };
        CouncilProposal::new(event, Uuid::new_v4(), Utc::now())
    }

    #[test]
    fn unique_signers_dedupes() {
        let mut p = mk_proposal();
        let a = Uuid::new_v4();
        let b = Uuid::new_v4();
        let now = Utc::now();
        p.add_vote(mk_envelope(a), now);
        p.add_vote(mk_envelope(a), now); // duplicate
        p.add_vote(mk_envelope(b), now);
        assert_eq!(p.unique_signers().len(), 2);
    }

    #[test]
    fn meets_threshold_counts_only_current_holders() {
        let mut p = mk_proposal();
        let a = Uuid::new_v4();
        let b = Uuid::new_v4();
        let c = Uuid::new_v4(); // not a holder
        let now = Utc::now();
        p.add_vote(mk_envelope(a), now);
        p.add_vote(mk_envelope(b), now);
        p.add_vote(mk_envelope(c), now);
        let holders: BTreeSet<Uuid> = [a, b].into_iter().collect();
        assert!(p.meets_threshold(2, &holders));
        assert!(!p.meets_threshold(3, &holders));
    }

    #[test]
    fn status_round_trips_through_serde() {
        let s = ProposalStatus::Committed { entry_index: 42, committed_at: Utc::now() };
        let json = serde_json::to_string(&s).unwrap();
        assert!(json.contains("\"kind\":\"committed\""));
        let back: ProposalStatus = serde_json::from_str(&json).unwrap();
        assert!(matches!(back, ProposalStatus::Committed { entry_index: 42, .. }));
    }
}
