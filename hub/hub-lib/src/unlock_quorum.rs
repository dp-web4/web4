// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! `unlock_quorum` — a **software reference verifier** for threshold-authorized release of a
//! protected secret, following the quorum-release method of the filed application
//! (US 19/803,885).
//!
//! The shape, in the order a release happens:
//!
//! 1. A **release intent** binds the authorization sought to one secret, one operation, one
//!    requester, one destination, one policy version, an expiry and a nonce. Everything
//!    downstream signs the intent's **digest**, so an approval collected for one intent
//!    cannot authorize a different secret, operation, destination or policy version.
//! 2. Each roster approver is issued a **single-use challenge**. An approval is a signature
//!    over the intent digest together with that approver's challenge. A challenge is
//!    consumed **only when the signature accompanying it verifies** — a forged or malformed
//!    response does not burn a legitimate approver's challenge, so a party who can merely
//!    submit bytes cannot deny an approver participation.
//! 3. A signed **decline** from any roster approver, verified like an approval, records the
//!    intent as **vetoed**. The veto is terminal: re-running the protocol does not clear it.
//!    An unverifiable decline records nothing.
//! 4. [`authorize`](QuorumVerifier::authorize) checks a threshold of **distinct** verified
//!    approvers, the policy version then in force, the expiry, and that the operation
//!    parameters presented equal those the intent bound — then records the intent
//!    **consumed** and only thereafter returns the authorization. Consumed and vetoed are
//!    mutually exclusive transitions out of the open state; exactly one can happen.
//!
//! Approvers authorize; they do not reconstruct. No approval carries a share of the secret.
//!
//! The guarantee is **at most once, not exactly once**: consumption is recorded before the
//! operation begins, so an interruption after it leaves the intent consumed and the
//! operation undone, and recovery needs a fresh intent. The other order would permit
//! repetition, which is the worse failure for the release of a secret.
//!
//! # What this is, and what it is not
//!
//! This is the **advisory, host-software embodiment**. Every check here runs in the hub's
//! own process, against state held in the hub's own memory. A host that is already
//! compromised can skip this module and act on whatever credential the host holds; and the
//! vetoed/consumed record lives in volatile memory, so it does not survive a restart unless
//! the caller re-derives it (the hub's ledger records every approval, decline and
//! resolution for exactly that purpose).
//!
//! The stronger design — the one that makes "ignition confers solicitation, not release" a
//! property of the machine rather than an assertion about software — puts these same checks
//! inside a hardware module that holds the secret sealed, keeps the vetoed/consumed record
//! in its own protected non-volatile state, and refuses the operation absent a verified
//! transcript. That needs hardware this crate does not have. Nothing here should be read as
//! providing it.

use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use uuid::Uuid;
use web4_core::crypto::{sha256, KeyPair, PublicKey, SignatureBytes};

/// A 32-byte digest or nonce.
pub type Bytes32 = [u8; 32];

const INTENT_DOMAIN: &[u8] = b"web4:release-intent:v1:";
const APPROVE_DOMAIN: &[u8] = b"web4:release-approve:v1:";
const DECLINE_DOMAIN: &[u8] = b"web4:release-decline:v1:";
const POLICY_DOMAIN: &[u8] = b"web4:release-policy:v1:";
const COMMIT_DOMAIN: &[u8] = b"web4:release-state:v1:";

/// Length-prefix a field so adjacent fields cannot be re-split into a different message.
fn put(buf: &mut Vec<u8>, field: &[u8]) {
    buf.extend_from_slice(&(field.len() as u32).to_be_bytes());
    buf.extend_from_slice(field);
}

/// Why the verifier refused. Every refusal leaves state unchanged unless its doc says
/// otherwise.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum Refusal {
    #[error("not an approver on the roster")]
    NotOnRoster,
    #[error("no such intent is open with this verifier")]
    UnknownIntent,
    #[error("the intent has expired")]
    Expired,
    #[error("the intent binds a policy version that is not the one in force")]
    StalePolicy,
    #[error("no challenge is outstanding for this approver on this intent")]
    NoChallenge,
    #[error("the response does not carry the challenge issued to this approver")]
    ChallengeMismatch,
    #[error("the challenge has expired — issue a fresh one")]
    ChallengeExpired,
    #[error("the signature does not verify against the approver's roster key")]
    BadSignature,
    #[error("the intent is vetoed — a veto is terminal and re-running the protocol does not clear it")]
    Vetoed,
    #[error("the intent is already consumed — a release intent is authorized at most once")]
    Consumed,
    #[error("{have} distinct verified approval(s), {need} required")]
    BelowThreshold { have: usize, need: usize },
    #[error("the operation parameters presented differ from those the intent bound")]
    ParamsMismatch,
    #[error("policy epoch {presented} is behind the admitted epoch {stored} — refused as a rollback")]
    EpochRollback { presented: u64, stored: u64 },
    #[error("a different policy was presented at the already-admitted epoch {0}")]
    EpochConflict(u64),
    #[error("threshold {threshold} is not satisfiable by a roster of {roster}")]
    UnsatisfiableThreshold { threshold: usize, roster: usize },
}

/// The roster of approver identities and the keys their approvals verify against. Keys are
/// resolved from here — never from anything an approval carries.
#[derive(Clone, Debug, Default)]
pub struct Roster {
    approvers: BTreeMap<Uuid, PublicKey>,
}

impl Roster {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with(mut self, approver: Uuid, key: PublicKey) -> Self {
        self.approvers.insert(approver, key);
        self
    }

    pub fn len(&self) -> usize {
        self.approvers.len()
    }

    pub fn is_empty(&self) -> bool {
        self.approvers.is_empty()
    }

    fn key(&self, approver: &Uuid) -> Option<&PublicKey> {
        self.approvers.get(approver)
    }
}

/// The digest that names one admitted policy: the roster, the threshold, **and the epoch it
/// was admitted at**. An intent binds it; a verifier whose policy has since changed refuses
/// the intent as stale.
///
/// The epoch is part of the digest so that staleness is **terminal**. Without it, a policy
/// that is superseded and later restored — an approver removed at one epoch and reinstated
/// with the same key at the next — would hash to its old version again, and every approval
/// collected before the removal would come back to life until the intent's own expiry.
/// Re-presenting the *current* policy at the *current* epoch still yields the same digest,
/// so the reload path stays idempotent.
pub fn policy_version(roster: &Roster, threshold: usize, epoch: u64) -> Bytes32 {
    let mut b = POLICY_DOMAIN.to_vec();
    b.extend_from_slice(&epoch.to_be_bytes());
    b.extend_from_slice(&(threshold as u64).to_be_bytes());
    for (id, key) in &roster.approvers {
        put(&mut b, id.as_bytes());
        put(&mut b, &key.to_bytes());
    }
    sha256(&b)
}

/// What an authorization is *for*. Approvals sign the digest of this, so every field is
/// bound: none can be changed after approvals are collected without invalidating them.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReleaseIntent {
    /// Which secret.
    pub secret_id: String,
    /// What is to be done with it — for example `release` or `sign`.
    pub operation: String,
    /// Who asked.
    pub requester: Uuid,
    /// The protected boundary the secret may be released into, or the name of the place the
    /// result goes when the operation runs without releasing it.
    pub destination: String,
    /// [`policy_version`] of the policy this intent was formed under.
    pub policy_version: Bytes32,
    /// Unix seconds after which the intent authorizes nothing.
    pub expires_at: u64,
    /// Makes two otherwise-identical intents distinct.
    pub nonce: Bytes32,
}

impl ReleaseIntent {
    /// The digest every approval and decline signs.
    pub fn digest(&self) -> Bytes32 {
        let mut b = INTENT_DOMAIN.to_vec();
        put(&mut b, self.secret_id.as_bytes());
        put(&mut b, self.operation.as_bytes());
        put(&mut b, self.requester.as_bytes());
        put(&mut b, self.destination.as_bytes());
        put(&mut b, &self.policy_version);
        b.extend_from_slice(&self.expires_at.to_be_bytes());
        put(&mut b, &self.nonce);
        sha256(&b)
    }

    fn params(&self) -> OperationParams {
        OperationParams {
            secret_id: self.secret_id.clone(),
            operation: self.operation.clone(),
            destination: self.destination.clone(),
        }
    }
}

/// The parameters of the operation actually about to be performed. [`authorize`]
/// (QuorumVerifier::authorize) requires them to equal what the intent bound, so approvals
/// gathered for one operation cannot be spent on another.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct OperationParams {
    pub secret_id: String,
    pub operation: String,
    pub destination: String,
}

fn approval_bytes(intent_digest: &Bytes32, challenge: &Bytes32) -> Vec<u8> {
    let mut b = APPROVE_DOMAIN.to_vec();
    b.extend_from_slice(intent_digest);
    b.extend_from_slice(challenge);
    b
}

fn decline_bytes(intent_digest: &Bytes32) -> Vec<u8> {
    let mut b = DECLINE_DOMAIN.to_vec();
    b.extend_from_slice(intent_digest);
    b
}

/// An approver's signature over the intent digest together with the challenge issued to
/// that approver. It carries no key and no share of the secret.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Approval {
    pub approver: Uuid,
    pub intent_digest: Bytes32,
    pub challenge: Bytes32,
    /// Ed25519 signature, hex.
    pub signature: String,
}

impl Approval {
    /// Sign an approval with the approver's own key.
    pub fn sign(key: &KeyPair, approver: Uuid, intent_digest: Bytes32, challenge: Bytes32) -> Self {
        let signature = key.sign(&approval_bytes(&intent_digest, &challenge)).to_hex();
        Self { approver, intent_digest, challenge, signature }
    }
}

/// An approver's signed refusal of an intent.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Decline {
    pub approver: Uuid,
    pub intent_digest: Bytes32,
    /// Ed25519 signature, hex.
    pub signature: String,
}

impl Decline {
    /// Sign a decline with the approver's own key.
    pub fn sign(key: &KeyPair, approver: Uuid, intent_digest: Bytes32) -> Self {
        let signature = key.sign(&decline_bytes(&intent_digest)).to_hex();
        Self { approver, intent_digest, signature }
    }
}

fn verify_hex(key: &PublicKey, message: &[u8], signature_hex: &str) -> bool {
    let Ok(raw) = hex::decode(signature_hex) else { return false };
    let Ok(arr) = <[u8; 64]>::try_from(raw.as_slice()) else { return false };
    key.verify(message, &SignatureBytes::from_bytes(arr)).is_ok()
}

/// Where an intent stands. `Vetoed` and `Consumed` are both terminal, and an intent reaches
/// at most one of them.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum IntentState {
    Open,
    Vetoed,
    Consumed,
}

struct Challenge {
    bytes: Bytes32,
    expires_at: u64,
}

struct OpenIntent {
    intent: ReleaseIntent,
    state: IntentState,
    /// Distinct approvers whose approval verified. A set: one approver signing many times
    /// is one approver.
    approved: BTreeSet<Uuid>,
    /// Outstanding (unconsumed) challenges, one per approver.
    challenges: BTreeMap<Uuid, Challenge>,
}

/// What [`QuorumVerifier::authorize`] returns once the intent is recorded consumed. Holding
/// one is the caller's licence to perform exactly the bound operation, once.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Authorization {
    pub intent_digest: Bytes32,
    pub params: OperationParams,
    /// The distinct approvers whose verified approvals made up the quorum.
    pub approvers: Vec<Uuid>,
    /// The verifier's counter after the consuming transition.
    pub counter: u64,
}

/// The reference verifier. All methods take `&mut self`, so transitions are serialized by
/// construction: of a final approval and a verified decline arriving together, whichever is
/// applied first decides, and the other is refused against the already-transitioned state.
pub struct QuorumVerifier {
    roster: Roster,
    threshold: usize,
    policy_version: Bytes32,
    /// The epoch of the admitted policy. See [`admit_policy`](Self::admit_policy).
    epoch: u64,
    intents: BTreeMap<Bytes32, OpenIntent>,
    /// Advances on every consuming or vetoing transition. Versions the commitment.
    counter: u64,
}

impl QuorumVerifier {
    /// Admit the first policy, at `epoch`.
    pub fn new(roster: Roster, threshold: usize, epoch: u64) -> Result<Self, Refusal> {
        check_threshold(&roster, threshold)?;
        let policy_version = policy_version(&roster, threshold, epoch);
        Ok(Self { roster, threshold, policy_version, epoch, intents: BTreeMap::new(), counter: 0 })
    }

    /// The policy version in force. An intent must bind this to be opened or authorized.
    pub fn policy_in_force(&self) -> Bytes32 {
        self.policy_version
    }

    pub fn counter(&self) -> u64 {
        self.counter
    }

    /// Admit a roster and threshold at `epoch`, refusing rollback while staying idempotent
    /// for the current policy: a higher epoch is admitted; the **same** epoch is admitted
    /// only if it names the same policy (the reload path — re-presenting the current policy
    /// after a restart must not need a governance change); a lower epoch is refused however
    /// valid it was when issued.
    ///
    /// Authenticating the payload — that this roster really is what governance decided — is
    /// the caller's job. In the hub that authority is the signed ledger the council is
    /// projected from. Intents opened under a superseded policy stay recorded and are
    /// refused as [`Refusal::StalePolicy`] — permanently: the epoch is part of the policy
    /// version, so restoring an earlier roster at a later epoch does not revive them.
    pub fn admit_policy(&mut self, roster: Roster, threshold: usize, epoch: u64) -> Result<(), Refusal> {
        check_threshold(&roster, threshold)?;
        let presented = policy_version(&roster, threshold, epoch);
        if epoch < self.epoch {
            return Err(Refusal::EpochRollback { presented: epoch, stored: self.epoch });
        }
        if epoch == self.epoch {
            return if presented == self.policy_version { Ok(()) } else { Err(Refusal::EpochConflict(epoch)) };
        }
        self.roster = roster;
        self.threshold = threshold;
        self.policy_version = presented;
        self.epoch = epoch;
        Ok(())
    }

    /// Register an intent as open. Refuses one that is already expired or that binds a
    /// policy version other than the one in force. Re-opening the same intent is a no-op
    /// that returns its digest — it never resets a vetoed or consumed record.
    pub fn open_intent(&mut self, intent: ReleaseIntent, now: u64) -> Result<Bytes32, Refusal> {
        if now >= intent.expires_at {
            return Err(Refusal::Expired);
        }
        if intent.policy_version != self.policy_version {
            return Err(Refusal::StalePolicy);
        }
        let digest = intent.digest();
        self.intents.entry(digest).or_insert_with(|| OpenIntent {
            intent,
            state: IntentState::Open,
            approved: BTreeSet::new(),
            challenges: BTreeMap::new(),
        });
        Ok(digest)
    }

    pub fn state(&self, intent_digest: &Bytes32) -> Option<IntentState> {
        self.intents.get(intent_digest).map(|i| i.state)
    }

    /// Issue `approver` a single-use challenge for this intent, valid for `ttl_secs`.
    ///
    /// **Idempotent while a challenge is outstanding**: asking again returns the same
    /// challenge and does not extend it; a new one is minted only once the old one is
    /// consumed or expired. Replacing on every call would let anyone who can reach this
    /// method invalidate an approval already signed and in flight — denying an approver
    /// their turn one call earlier than the forged-response rule protects. A challenge is
    /// not a secret (the signature is what counts), so handing it out again costs nothing.
    pub fn issue_challenge(
        &mut self,
        intent_digest: &Bytes32,
        approver: Uuid,
        now: u64,
        ttl_secs: u64,
    ) -> Result<Bytes32, Refusal> {
        if self.roster.key(&approver).is_none() {
            return Err(Refusal::NotOnRoster);
        }
        let open = self.open_mut(intent_digest, now)?;
        if let Some(outstanding) = open.challenges.get(&approver) {
            if now < outstanding.expires_at {
                return Ok(outstanding.bytes);
            }
        }
        let bytes: Bytes32 = rand::random();
        open.challenges.insert(approver, Challenge { bytes, expires_at: now.saturating_add(ttl_secs) });
        Ok(bytes)
    }

    /// Verify and record an approval.
    ///
    /// The approver's challenge is consumed **only if the signature verifies**. Every
    /// refusal before that point — wrong challenge, expired challenge, bad signature —
    /// leaves the outstanding challenge in place, so a response anyone could have submitted
    /// cannot cost the real approver their turn.
    pub fn submit_approval(&mut self, approval: &Approval, now: u64) -> Result<(), Refusal> {
        let key = self.roster.key(&approval.approver).ok_or(Refusal::NotOnRoster)?.clone();
        let open = self.open_mut(&approval.intent_digest, now)?;
        let challenge = open.challenges.get(&approval.approver).ok_or(Refusal::NoChallenge)?;
        if challenge.bytes != approval.challenge {
            return Err(Refusal::ChallengeMismatch);
        }
        if now >= challenge.expires_at {
            return Err(Refusal::ChallengeExpired);
        }
        if !verify_hex(&key, &approval_bytes(&approval.intent_digest, &approval.challenge), &approval.signature) {
            return Err(Refusal::BadSignature);
        }
        open.challenges.remove(&approval.approver);
        open.approved.insert(approval.approver);
        Ok(())
    }

    /// Verify a decline and, if it verifies, record the intent **vetoed**. Terminal. An
    /// unverifiable decline records nothing and consumes nothing: a party who can merely
    /// submit bytes cannot veto an intent they hold no roster key for.
    pub fn submit_decline(&mut self, decline: &Decline, now: u64) -> Result<(), Refusal> {
        let key = self.roster.key(&decline.approver).ok_or(Refusal::NotOnRoster)?.clone();
        let open = self.open_mut(&decline.intent_digest, now)?;
        if !verify_hex(&key, &decline_bytes(&decline.intent_digest), &decline.signature) {
            return Err(Refusal::BadSignature);
        }
        open.state = IntentState::Vetoed;
        self.counter += 1;
        Ok(())
    }

    /// Decide. Succeeds only if the intent is open and unexpired, binds the policy version
    /// in force, has a threshold of distinct verified approvers, and `params` equal what the
    /// intent bound. On success the intent is recorded **consumed** and the counter advanced
    /// *before* this returns — so the caller performs the operation strictly after
    /// consumption, and a second call is refused as [`Refusal::Consumed`].
    pub fn authorize(
        &mut self,
        intent_digest: &Bytes32,
        params: &OperationParams,
        now: u64,
    ) -> Result<Authorization, Refusal> {
        let in_force = self.policy_version;
        let threshold = self.threshold;
        let open = self.open_mut(intent_digest, now)?;
        if open.intent.policy_version != in_force {
            return Err(Refusal::StalePolicy);
        }
        if *params != open.intent.params() {
            return Err(Refusal::ParamsMismatch);
        }
        if open.approved.len() < threshold {
            return Err(Refusal::BelowThreshold { have: open.approved.len(), need: threshold });
        }
        open.state = IntentState::Consumed;
        let approvers: Vec<Uuid> = open.approved.iter().copied().collect();
        let params = open.intent.params();
        self.counter += 1;
        Ok(Authorization { intent_digest: *intent_digest, params, approvers, counter: self.counter })
    }

    /// A digest over which intents are vetoed and which consumed, versioned by the counter.
    /// The counter alone orders states but says nothing about *which* intent was affected;
    /// this is what identifies them. Here it is only as durable as this process — see the
    /// module doc.
    pub fn commitment(&self) -> Bytes32 {
        let mut b = COMMIT_DOMAIN.to_vec();
        b.extend_from_slice(&self.counter.to_be_bytes());
        for (digest, open) in &self.intents {
            let tag = match open.state {
                IntentState::Open => continue,
                IntentState::Vetoed => 1u8,
                IntentState::Consumed => 2u8,
            };
            b.extend_from_slice(digest);
            b.push(tag);
        }
        sha256(&b)
    }

    /// The intent, if it is known, still open, and unexpired. Terminal states are reported
    /// before expiry: a vetoed intent stays "vetoed", never decays into "expired".
    fn open_mut(&mut self, intent_digest: &Bytes32, now: u64) -> Result<&mut OpenIntent, Refusal> {
        let open = self.intents.get_mut(intent_digest).ok_or(Refusal::UnknownIntent)?;
        match open.state {
            IntentState::Vetoed => return Err(Refusal::Vetoed),
            IntentState::Consumed => return Err(Refusal::Consumed),
            IntentState::Open => {}
        }
        if now >= open.intent.expires_at {
            return Err(Refusal::Expired);
        }
        Ok(open)
    }
}

fn check_threshold(roster: &Roster, threshold: usize) -> Result<(), Refusal> {
    if threshold == 0 || threshold > roster.len() {
        return Err(Refusal::UnsatisfiableThreshold { threshold, roster: roster.len() });
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    const NOW: u64 = 1_800_000_000;
    const TTL: u64 = 120;

    struct Fixture {
        v: QuorumVerifier,
        keys: Vec<(Uuid, KeyPair)>,
    }

    fn fixture(n: usize, threshold: usize) -> Fixture {
        let keys: Vec<(Uuid, KeyPair)> = (0..n).map(|_| (Uuid::new_v4(), KeyPair::generate())).collect();
        let roster = keys.iter().fold(Roster::new(), |r, (id, k)| r.with(*id, k.verifying_key()));
        Fixture { v: QuorumVerifier::new(roster, threshold, 5).unwrap(), keys }
    }

    fn intent(policy: Bytes32, secret: &str, destination: &str) -> ReleaseIntent {
        ReleaseIntent {
            secret_id: secret.into(),
            operation: "release".into(),
            requester: Uuid::new_v4(),
            destination: destination.into(),
            policy_version: policy,
            expires_at: NOW + TTL,
            nonce: rand::random(),
        }
    }

    impl Fixture {
        fn open(&mut self, secret: &str, destination: &str) -> (ReleaseIntent, Bytes32) {
            let i = intent(self.v.policy_in_force(), secret, destination);
            let d = self.v.open_intent(i.clone(), NOW).unwrap();
            (i, d)
        }

        /// Issue a challenge to approver `ix` and return their genuine approval.
        fn approval(&mut self, ix: usize, digest: Bytes32) -> Approval {
            let (id, _) = self.keys[ix];
            let ch = self.v.issue_challenge(&digest, id, NOW, TTL).unwrap();
            Approval::sign(&self.keys[ix].1, id, digest, ch)
        }

        fn approve(&mut self, ix: usize, digest: Bytes32) {
            let a = self.approval(ix, digest);
            self.v.submit_approval(&a, NOW).unwrap();
        }
    }

    /// The worked example: roster of four, threshold three. Three distinct approvals
    /// authorize exactly once; the same approvals do not authorize again.
    #[test]
    fn a_threshold_of_distinct_approvers_authorizes_at_most_once() {
        let mut f = fixture(4, 3);
        let (i, d) = f.open("vaultK", "enclave-7");
        f.approve(1, d);
        f.approve(2, d);

        // Two of three: refused, and the intent stays open.
        assert_eq!(f.v.authorize(&d, &i.params(), NOW), Err(Refusal::BelowThreshold { have: 2, need: 3 }));
        assert_eq!(f.v.state(&d), Some(IntentState::Open));

        f.approve(3, d);
        let before = f.v.counter();
        let auth = f.v.authorize(&d, &i.params(), NOW).unwrap();
        assert_eq!(auth.approvers.len(), 3);
        assert_eq!(auth.counter, before + 1);
        assert_eq!(f.v.state(&d), Some(IntentState::Consumed));

        // Consumed is recorded before the caller acts, so a replay of the decision is refused.
        assert_eq!(f.v.authorize(&d, &i.params(), NOW), Err(Refusal::Consumed));
    }

    /// Approvals sign the intent digest, so they are not transferable: three approvers who
    /// signed `d` have authorized nothing about `d'` — a different secret, or the same
    /// secret bound for a different destination.
    #[test]
    fn approvals_for_one_intent_do_not_authorize_another() {
        let mut f = fixture(4, 3);
        let (_i, d) = f.open("vaultK", "enclave-7");
        let approvals: Vec<Approval> = (1..4).map(|ix| f.approval(ix, d)).collect();

        let (other, d2) = f.open("vaultK", "somewhere-else");
        assert_ne!(d, d2);
        for a in &approvals {
            // Re-aim the collected approval at the other intent. The challenge was issued
            // for `d`, and the signature covers `d`: neither carries over.
            let mut moved = a.clone();
            moved.intent_digest = d2;
            assert_eq!(f.v.submit_approval(&moved, NOW), Err(Refusal::NoChallenge));
        }
        assert_eq!(f.v.authorize(&d2, &other.params(), NOW), Err(Refusal::BelowThreshold { have: 0, need: 3 }));

        // Even with a challenge outstanding on d2 for that approver, a signature over `d` fails.
        let (id, _) = f.keys[1];
        let ch2 = f.v.issue_challenge(&d2, id, NOW, TTL).unwrap();
        let forged = Approval { approver: id, intent_digest: d2, challenge: ch2, signature: approvals[0].signature.clone() };
        assert_eq!(f.v.submit_approval(&forged, NOW), Err(Refusal::BadSignature));
    }

    /// One approver is one approver, however many times they sign; and a replayed approval
    /// finds its challenge already consumed.
    #[test]
    fn one_approver_counts_once_and_a_replay_is_refused() {
        let mut f = fixture(3, 2);
        let (i, d) = f.open("s", "b");
        let a = f.approval(0, d);
        f.v.submit_approval(&a, NOW).unwrap();
        assert_eq!(f.v.submit_approval(&a, NOW), Err(Refusal::NoChallenge));

        // A fresh challenge and a second genuine signature from the same approver: accepted,
        // and still one approver.
        f.approve(0, d);
        assert_eq!(f.v.authorize(&d, &i.params(), NOW), Err(Refusal::BelowThreshold { have: 1, need: 2 }));
    }

    /// A forged response must not burn the legitimate approver's challenge — otherwise
    /// anyone able to submit bytes could deny that approver participation.
    #[test]
    fn a_forged_response_does_not_consume_the_challenge() {
        let mut f = fixture(3, 2);
        let (_i, d) = f.open("s", "b");
        let genuine = f.approval(0, d);

        let attacker = KeyPair::generate();
        let forged = Approval::sign(&attacker, genuine.approver, d, genuine.challenge);
        assert_eq!(f.v.submit_approval(&forged, NOW), Err(Refusal::BadSignature));

        let mut garbage = genuine.clone();
        garbage.signature = "zz".into();
        assert_eq!(f.v.submit_approval(&garbage, NOW), Err(Refusal::BadSignature));

        // The challenge survived both: the real approver's response still lands.
        f.v.submit_approval(&genuine, NOW).unwrap();
    }

    /// A verified decline is a terminal veto — even over a quorum that was already complete
    /// — and re-running the protocol does not clear it.
    #[test]
    fn a_verified_decline_is_a_terminal_veto() {
        let mut f = fixture(4, 3);
        let (i, d) = f.open("s", "b");
        f.approve(1, d);
        f.approve(2, d);
        f.approve(3, d);

        let (id0, _) = f.keys[0];
        let before = f.v.counter();
        f.v.submit_decline(&Decline::sign(&f.keys[0].1, id0, d), NOW).unwrap();
        assert_eq!(f.v.state(&d), Some(IntentState::Vetoed));
        assert_eq!(f.v.counter(), before + 1);

        assert_eq!(f.v.authorize(&d, &i.params(), NOW), Err(Refusal::Vetoed));
        // Re-running: re-open the same intent, ask for a challenge, approve again. All refused.
        assert_eq!(f.v.open_intent(i.clone(), NOW), Ok(d));
        assert_eq!(f.v.state(&d), Some(IntentState::Vetoed));
        let (id1, _) = f.keys[1];
        assert_eq!(f.v.issue_challenge(&d, id1, NOW, TTL), Err(Refusal::Vetoed));
        // And a vetoed intent stays "vetoed" after its expiry, never decaying to "expired".
        assert_eq!(f.v.authorize(&d, &i.params(), NOW + TTL + 1), Err(Refusal::Vetoed));
    }

    /// An unverifiable decline records nothing: not from a key off the roster, and not a
    /// roster member's name over someone else's signature.
    #[test]
    fn an_unverifiable_decline_vetoes_nothing() {
        let mut f = fixture(3, 2);
        let (i, d) = f.open("s", "b");
        let outsider = KeyPair::generate();

        assert_eq!(f.v.submit_decline(&Decline::sign(&outsider, Uuid::new_v4(), d), NOW), Err(Refusal::NotOnRoster));
        let (id0, _) = f.keys[0];
        assert_eq!(f.v.submit_decline(&Decline::sign(&outsider, id0, d), NOW), Err(Refusal::BadSignature));

        assert_eq!(f.v.state(&d), Some(IntentState::Open));
        assert_eq!(f.v.counter(), 0);
        f.approve(1, d);
        f.approve(2, d);
        f.v.authorize(&d, &i.params(), NOW).unwrap();
    }

    /// Consumed and vetoed are mutually exclusive: a decline arriving after consumption is
    /// refused against the already-transitioned state.
    #[test]
    fn a_decline_after_consumption_is_refused() {
        let mut f = fixture(3, 2);
        let (i, d) = f.open("s", "b");
        f.approve(1, d);
        f.approve(2, d);
        f.v.authorize(&d, &i.params(), NOW).unwrap();

        let (id0, _) = f.keys[0];
        assert_eq!(f.v.submit_decline(&Decline::sign(&f.keys[0].1, id0, d), NOW), Err(Refusal::Consumed));
        assert_eq!(f.v.state(&d), Some(IntentState::Consumed));
    }

    /// The parameters of the operation about to run must equal what the approvers signed
    /// for. A mismatch is refused and does not consume the intent.
    #[test]
    fn operation_parameters_must_equal_what_the_intent_bound() {
        let mut f = fixture(3, 2);
        let (i, d) = f.open("vaultK", "enclave-7");
        f.approve(0, d);
        f.approve(1, d);

        let mut elsewhere = i.params();
        elsewhere.destination = "attacker-host".into();
        assert_eq!(f.v.authorize(&d, &elsewhere, NOW), Err(Refusal::ParamsMismatch));
        let mut other_op = i.params();
        other_op.operation = "export".into();
        assert_eq!(f.v.authorize(&d, &other_op, NOW), Err(Refusal::ParamsMismatch));

        assert_eq!(f.v.state(&d), Some(IntentState::Open));
        f.v.authorize(&d, &i.params(), NOW).unwrap();
    }

    #[test]
    fn an_expired_intent_or_challenge_authorizes_nothing() {
        let mut f = fixture(3, 2);
        let (i, d) = f.open("s", "b");
        let late = f.approval(0, d);
        // The challenge has a TTL of its own, shorter than the intent's here.
        let (id1, _) = f.keys[1];
        let short = f.v.issue_challenge(&d, id1, NOW, 10).unwrap();
        let a1 = Approval::sign(&f.keys[1].1, id1, d, short);
        assert_eq!(f.v.submit_approval(&a1, NOW + 10), Err(Refusal::ChallengeExpired));

        assert_eq!(f.v.submit_approval(&late, NOW + TTL), Err(Refusal::Expired));
        assert_eq!(f.v.authorize(&d, &i.params(), NOW + TTL), Err(Refusal::Expired));
        assert_eq!(f.v.open_intent(intent(f.v.policy_in_force(), "s", "b"), NOW + TTL), Err(Refusal::Expired));
    }

    /// A policy change supersedes the version an open intent bound: the intent is refused
    /// as stale even with a full quorum collected under the old roster.
    #[test]
    fn a_superseded_policy_version_is_refused() {
        let mut f = fixture(3, 2);
        let (i, d) = f.open("s", "b");
        f.approve(0, d);
        f.approve(1, d);

        // Governance lowers nothing and raises the threshold to 3, at a later epoch.
        let roster = f.keys.iter().fold(Roster::new(), |r, (id, k)| r.with(*id, k.verifying_key()));
        f.v.admit_policy(roster, 3, 6).unwrap();

        assert_eq!(f.v.authorize(&d, &i.params(), NOW), Err(Refusal::StalePolicy));
        // A new intent formed under the old version cannot be opened either.
        assert_eq!(f.v.open_intent(intent(i.policy_version, "s", "b"), NOW), Err(Refusal::StalePolicy));
    }

    /// The epoch test: forward is admitted, the current policy is re-presentable (a restart
    /// must not need a governance change), and everything else is refused — an older policy
    /// however valid it once was, and a *different* policy claiming the current epoch.
    #[test]
    fn policy_admission_refuses_rollback_and_stays_idempotent() {
        let f = fixture(4, 3);
        let mut v = f.v;
        let roster = || f.keys.iter().fold(Roster::new(), |r, (id, k)| r.with(*id, k.verifying_key()));
        let in_force = v.policy_in_force();

        assert_eq!(v.admit_policy(roster(), 3, 5), Ok(())); // same epoch, same policy: reload
        assert_eq!(v.policy_in_force(), in_force);
        assert_eq!(v.admit_policy(roster(), 2, 5), Err(Refusal::EpochConflict(5))); // same epoch, weaker
        assert_eq!(v.admit_policy(roster(), 2, 4), Err(Refusal::EpochRollback { presented: 4, stored: 5 }));
        assert_eq!(v.policy_in_force(), in_force);

        assert_eq!(v.admit_policy(roster(), 4, 6), Ok(()));
        assert_ne!(v.policy_in_force(), in_force);
        assert_eq!(v.admit_policy(roster(), 3, 5), Err(Refusal::EpochRollback { presented: 5, stored: 6 }));
    }

    /// Stale is terminal. An approver is removed at epoch 6 and reinstated with the same key
    /// at epoch 7: the roster and threshold are byte-identical to epoch 5's, and the
    /// approvals collected under epoch 5 must NOT come back to life. Found in review.
    #[test]
    fn restoring_an_earlier_roster_does_not_revive_stale_approvals() {
        let mut f = fixture(3, 2);
        let (i, d) = f.open("s", "b");
        f.approve(0, d);
        f.approve(1, d);

        let full = || f.keys.iter().fold(Roster::new(), |r, (id, k)| r.with(*id, k.verifying_key()));
        let without_0 = f.keys[1..].iter().fold(Roster::new(), |r, (id, k)| r.with(*id, k.verifying_key()));
        let v = &mut f.v;
        v.admit_policy(without_0, 2, 6).unwrap();
        assert_eq!(v.authorize(&d, &i.params(), NOW), Err(Refusal::StalePolicy));
        v.admit_policy(full(), 2, 7).unwrap();
        assert_eq!(v.authorize(&d, &i.params(), NOW), Err(Refusal::StalePolicy));
    }

    /// A second request for a challenge must not invalidate an approval already signed and
    /// in flight — otherwise anyone who can ask for a challenge can deny an approver their
    /// turn. Found in review. Once the challenge is consumed, a fresh one is minted.
    #[test]
    fn asking_again_does_not_invalidate_an_approval_in_flight() {
        let mut f = fixture(3, 2);
        let (_i, d) = f.open("s", "b");
        let in_flight = f.approval(0, d);

        let (id0, _) = f.keys[0];
        let again = f.v.issue_challenge(&d, id0, NOW + 1, TTL).unwrap();
        assert_eq!(again, in_flight.challenge, "re-issue replaced an outstanding challenge");
        f.v.submit_approval(&in_flight, NOW + 2).unwrap();

        let fresh = f.v.issue_challenge(&d, id0, NOW + 3, TTL).unwrap();
        assert_ne!(fresh, in_flight.challenge, "a consumed challenge was handed out again");
    }

    #[test]
    fn a_threshold_the_roster_cannot_meet_is_refused() {
        let k = KeyPair::generate();
        let roster = Roster::new().with(Uuid::new_v4(), k.verifying_key());
        assert!(matches!(QuorumVerifier::new(roster.clone(), 0, 1), Err(Refusal::UnsatisfiableThreshold { .. })));
        assert!(matches!(QuorumVerifier::new(roster, 2, 1), Err(Refusal::UnsatisfiableThreshold { .. })));
    }

    /// The commitment identifies WHICH intents are vetoed or consumed; the counter only
    /// orders states. Two verifiers at the same counter with different affected intents
    /// must not share a commitment.
    #[test]
    fn the_commitment_identifies_the_affected_intents() {
        let mut f = fixture(3, 2);
        let empty = f.v.commitment();
        let (i1, d1) = f.open("one", "b");
        let (_i2, d2) = f.open("two", "b");
        assert_eq!(f.v.commitment(), empty, "opening an intent is not a transition");

        f.approve(0, d1);
        f.approve(1, d1);
        f.v.authorize(&d1, &i1.params(), NOW).unwrap();
        let after_consume = f.v.commitment();
        assert_ne!(after_consume, empty);

        let (id0, _) = f.keys[0];
        f.v.submit_decline(&Decline::sign(&f.keys[0].1, id0, d2), NOW).unwrap();
        assert_ne!(f.v.commitment(), after_consume);
        assert_eq!(f.v.counter(), 2);

        // The discriminating arm: same counter, different intent affected. A commitment
        // built from the counter alone would pass everything above and fail here.
        let mut g = fixture(3, 2);
        let (j, e) = g.open("a-different-secret", "b");
        g.approve(0, e);
        g.approve(1, e);
        g.v.authorize(&e, &j.params(), NOW).unwrap();
        assert_eq!(g.v.counter(), 1);
        assert_ne!(g.v.commitment(), after_consume, "one counter value, two different consumed intents, one commitment");
    }
}
