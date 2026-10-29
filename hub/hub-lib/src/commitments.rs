// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Commitments, slice K1 (`hub/docs/PRD_COMMITMENTS.md`): the event vocabulary, the projection,
//! the checks a write must pass against it, and the operator's contact book.
//!
//! A commitment has an owner, a backup and a leads role. Silence moves it along that queue; it
//! never records a verdict (C1). Being named is not acknowledging (C2). Contact details never
//! reach the ledger (C3): a contact party is an opaque `party_id`, and the name and address live
//! in [`ContactBook`], a file the operator can erase.
//!
//! K1 has no clock. `queue_since` is projected here so the K2 sweep has one field to measure
//! silence from, and nothing in this slice reads it.

use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::events::HubEvent;

/// What a `party_id` names. A `member` is a hub member and its id is the member's LCT id. A
/// `contact` is a person with no key yet, known to the operator's contact book.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PartyKind {
    Member,
    Contact,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PartyRef {
    pub party_id: String,
    pub kind: PartyKind,
}

/// Who put the owner's name on the commitment (C2). Derived by the hub, never taken from a body.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Basis {
    /// Someone else named the owner: the operator, a lead, or the backup in a handoff.
    NamedByOther,
    /// The owner took it on themselves.
    #[serde(rename = "self")]
    TakenBySelf,
}

/// `kind` in the PRD's table. The field is `move_kind` on the wire because `kind` is the serde
/// tag of `HubEvent` itself.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MoveKind {
    Update,
    Stuck,
    Handoff,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EscalationStep {
    Backup,
    Leads,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EscalationCause {
    Silence,
    Stuck,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Outcome {
    Done,
    Withdrawn,
    Missed,
}

/// How an acknowledgement reached the ledger. `operator` is the K1 route: the operator relays
/// what a party said. A reader weighs it as the operator's word, and it never counts as the
/// owner's own acknowledgement for any delta ([`Commitment::owner_acknowledged`]).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AckVia {
    MemberAct,
    Link,
    Operator,
}

/// Where the queue stands: who is expected to move next.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum QueuePos {
    Owner,
    Backup,
    Leads,
}

impl QueuePos {
    /// One step forward. `Leads` is the end of the ladder.
    pub fn next(self) -> Option<QueuePos> {
        match self {
            QueuePos::Owner => Some(QueuePos::Backup),
            QueuePos::Backup => Some(QueuePos::Leads),
            QueuePos::Leads => None,
        }
    }

    pub fn of_step(step: EscalationStep) -> QueuePos {
        match step {
            EscalationStep::Backup => QueuePos::Backup,
            EscalationStep::Leads => QueuePos::Leads,
        }
    }

    pub fn as_step(self) -> Option<EscalationStep> {
        match self {
            QueuePos::Owner => None,
            QueuePos::Backup => Some(EscalationStep::Backup),
            QueuePos::Leads => Some(EscalationStep::Leads),
        }
    }
}

/// Bounds the routes enforce. A ladder holds one silence window per queue position.
pub const MAX_LADDER_STEPS: usize = 3;
pub const MAX_WINDOW_HOURS: u32 = 24 * 30;
/// `title` is the one free-text field on the ledger; it names the job ("Venue AV"), nothing more.
pub const MAX_TITLE_LEN: usize = 80;
pub const MAX_CHANNEL_LEN: usize = 32;
/// Nudge attempts any one party gets in a rolling day, across every commitment (PRD §6). Counted
/// from the ledger, so a carrier restart cannot reset it.
pub const NUDGE_CAP_PER_DAY: usize = 3;
/// The length of a movement link's digest on the ledger: 128 bits of SHA-256, in hex (K4).
pub const LINK_DIGEST_LEN: usize = 32;

#[derive(Clone, Debug, Serialize)]
pub struct Escalation {
    pub step: EscalationStep,
    pub cause: EscalationCause,
    /// The window that ran out, for a silence escalation. The nudge says how long.
    pub window_hours: Option<u32>,
    pub index: u64,
}

/// One nudge attempt the carrier reported (K3). Kept on resolved commitments too: a send that
/// raced a resolution still happened.
#[derive(Clone, Debug, Serialize)]
pub struct Delivery {
    pub about_index: u64,
    pub party_id: String,
    pub channel: String,
    pub ok: bool,
    pub at: DateTime<Utc>,
}

#[derive(Clone, Debug, Serialize)]
pub struct Resolution {
    pub outcome: Outcome,
    pub by: String,
    pub at: DateTime<Utc>,
    pub owner_acknowledged: bool,
    pub index: u64,
}

/// One commitment as the ledger leaves it. Resolved commitments stay in the map, so a late
/// writer is answered with what resolved it rather than "unknown".
#[derive(Clone, Debug, Serialize)]
pub struct Commitment {
    pub commitment_id: String,
    pub title: String,
    pub owner: PartyRef,
    pub backup: PartyRef,
    pub leads_role: String,
    pub ladder: Vec<u32>,
    pub due_at: Option<DateTime<Utc>>,
    pub recorded_by: Uuid,
    /// The basis for the CURRENT owner. A handoff re-derives it.
    pub basis: Basis,
    pub opened_at: DateTime<Utc>,
    pub opened_index: u64,
    /// Party ids that have acknowledged, and how. A handoff drops the new owner's entry: an
    /// acknowledgement given as backup is not one given as owner.
    pub acknowledged: BTreeMap<String, AckVia>,
    pub queue: QueuePos,
    /// The one clock (PRD §3.3): when the latest entry that set the queue was witnessed.
    pub queue_since: DateTime<Utc>,
    pub escalations: Vec<Escalation>,
    pub resolved: Option<Resolution>,
    pub deliveries: Vec<Delivery>,
    /// Digests of the links that have acknowledged (K4): each link acknowledges once.
    pub link_acks: BTreeSet<String>,
}

impl Commitment {
    /// Whether the owner's own word is on the ledger. An operator-relayed acknowledgement is not.
    /// K2 gates every delta on this (PRD §5.1).
    pub fn owner_acknowledged(&self) -> bool {
        self.basis == Basis::TakenBySelf
            || matches!(self.acknowledged.get(&self.owner.party_id), Some(AckVia::MemberAct | AckVia::Link))
    }

    /// The party a queue position names. Leads is a role, not a party.
    pub fn party_at(&self, pos: QueuePos) -> Option<&PartyRef> {
        match pos {
            QueuePos::Owner => Some(&self.owner),
            QueuePos::Backup => Some(&self.backup),
            QueuePos::Leads => None,
        }
    }

    /// The position a party's own movement sends the queue to: theirs.
    pub fn position_of(&self, party_id: &str) -> QueuePos {
        if party_id == self.owner.party_id {
            QueuePos::Owner
        } else if party_id == self.backup.party_id {
            QueuePos::Backup
        } else {
            QueuePos::Leads
        }
    }

    pub fn is_open(&self) -> bool {
        self.resolved.is_none()
    }
}

fn commitment_id(event: &HubEvent) -> Option<&str> {
    match event {
        HubEvent::CommitmentOpened { commitment_id, .. }
        | HubEvent::CommitmentAcknowledged { commitment_id, .. }
        | HubEvent::CommitmentMoved { commitment_id, .. }
        | HubEvent::CommitmentEscalated { commitment_id, .. }
        | HubEvent::CommitmentResolved { commitment_id, .. }
        | HubEvent::NudgeDelivered { commitment_id, .. } => Some(commitment_id),
        _ => None,
    }
}

/// Why a commitment write was refused. Every arm is checked before anything is witnessed.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Refusal {
    Unknown(String),
    AlreadyOpen(String),
    /// §4.1: the loser of a resolution race is told what won.
    AlreadyResolved { commitment_id: String, outcome: Outcome, at: DateTime<Utc> },
    Invalid(String),
}

impl std::fmt::Display for Refusal {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Refusal::Unknown(id) => write!(f, "no commitment {id}"),
            Refusal::AlreadyOpen(id) => write!(f, "commitment {id} already exists"),
            Refusal::AlreadyResolved { commitment_id, outcome, at } => write!(
                f, "already resolved: commitment {commitment_id} was {} at {}",
                outcome_str(*outcome), at.to_rfc3339()),
            Refusal::Invalid(m) => f.write_str(m),
        }
    }
}

pub fn outcome_str(o: Outcome) -> &'static str {
    match o {
        Outcome::Done => "done",
        Outcome::Withdrawn => "withdrawn",
        Outcome::Missed => "missed",
    }
}

/// The checks a commitment event must pass against the projection it would extend. The caller
/// runs this and the witness under one lock, so two writers cannot both pass a check only one of
/// them may (§4.1). Checks that need more than the commitments map (is this a member, is this
/// role live, is this contact in the book) belong to the caller.
pub fn check(commitments: &BTreeMap<String, Commitment>, event: &HubEvent) -> Result<(), Refusal> {
    let Some(id) = commitment_id(event) else { return Ok(()) };
    if let HubEvent::CommitmentOpened { owner, backup, ladder, title, .. } = event {
        if commitments.contains_key(id) {
            return Err(Refusal::AlreadyOpen(id.to_string()));
        }
        if owner.party_id == backup.party_id {
            return Err(Refusal::Invalid("the backup must be someone other than the owner".into()));
        }
        if ladder.is_empty() || ladder.len() > MAX_LADDER_STEPS {
            return Err(Refusal::Invalid(format!(
                "ladder holds one silence window per position (owner, backup, leads): 1 to {MAX_LADDER_STEPS} entries")));
        }
        if ladder.iter().any(|h| *h == 0 || *h > MAX_WINDOW_HOURS) {
            return Err(Refusal::Invalid(format!("each silence window is 1 to {MAX_WINDOW_HOURS} hours")));
        }
        let t = title.trim();
        if t.is_empty() || t.chars().count() > MAX_TITLE_LEN || t.chars().any(char::is_control) {
            return Err(Refusal::Invalid(format!(
                "title is required, at most {MAX_TITLE_LEN} characters, no control characters")));
        }
        return Ok(());
    }
    let c = commitments.get(id).ok_or_else(|| Refusal::Unknown(id.to_string()))?;
    // A delivery report is checked before the resolved arm: a nudge sent just before a
    // resolution was still sent, and the record says so.
    if let HubEvent::NudgeDelivered { about_index, channel, .. } = event {
        if *about_index != c.opened_index && !c.escalations.iter().any(|e| e.index == *about_index) {
            return Err(Refusal::Invalid(format!(
                "entry {about_index} is neither the opening nor an escalation of {id}")));
        }
        if channel.is_empty() || channel.len() > MAX_CHANNEL_LEN
            || !channel.chars().all(|ch| ch.is_ascii_lowercase() || ch == '-') {
            return Err(Refusal::Invalid(format!(
                "channel names the means (\"email\"): 1 to {MAX_CHANNEL_LEN} of a-z and -, never an address")));
        }
        return Ok(());
    }
    if let Some(r) = &c.resolved {
        return Err(Refusal::AlreadyResolved { commitment_id: id.to_string(), outcome: r.outcome, at: r.at });
    }
    match event {
        HubEvent::CommitmentAcknowledged { via, link_digest, .. } | HubEvent::CommitmentMoved { via, link_digest, .. } => {
            check_link_digest(*via, link_digest.as_deref())?;
        }
        HubEvent::CommitmentResolved { link_digest: Some(d), .. } => check_link_digest(AckVia::Link, Some(d))?,
        _ => {}
    }
    match event {
        HubEvent::CommitmentAcknowledged { party_id, link_digest, .. } => {
            if party_id != &c.owner.party_id && party_id != &c.backup.party_id {
                return Err(Refusal::Invalid(format!(
                    "{party_id} is neither the owner nor the backup of {id}; only they acknowledge")));
            }
            // An acknowledgement is the one consequential bit a link carries, so a link gives it
            // once (PRD §5, the movement-link block).
            if link_digest.as_ref().map_or(false, |d| c.link_acks.contains(d)) {
                return Err(Refusal::Invalid("this link has already been used to acknowledge".into()));
            }
        }
        HubEvent::CommitmentMoved { move_kind, to, .. } => match (move_kind, to) {
            (MoveKind::Handoff, None) => {
                return Err(Refusal::Invalid("a handoff names who it goes to (`to`)".into()));
            }
            (MoveKind::Handoff, Some(to)) if to.party_id == c.owner.party_id => {
                return Err(Refusal::Invalid(format!("{} already owns {id}", to.party_id)));
            }
            (MoveKind::Update | MoveKind::Stuck, Some(_)) => {
                return Err(Refusal::Invalid("`to` is only for a handoff".into()));
            }
            _ => {}
        },
        HubEvent::CommitmentEscalated { step, cause, silent_since, window_hours, .. } => {
            if (*cause == EscalationCause::Silence) != (silent_since.is_some() && window_hours.is_some()) {
                return Err(Refusal::Invalid(
                    "silent_since and window_hours are set exactly when the cause is silence".into()));
            }
            if QueuePos::of_step(*step) <= c.queue && *cause == EscalationCause::Silence {
                return Err(Refusal::Invalid(format!("{id} is already at or past that step")));
            }
        }
        _ => {}
    }
    Ok(())
}

/// A link digest is present exactly when the word came through a link, and is the shape the hub
/// writes: 32 lowercase hex characters (K4).
fn check_link_digest(via: AckVia, digest: Option<&str>) -> Result<(), Refusal> {
    match (via, digest) {
        (AckVia::Link, Some(d)) if d.len() == LINK_DIGEST_LEN
            && d.chars().all(|ch| ch.is_ascii_digit() || ('a'..='f').contains(&ch)) => Ok(()),
        (AckVia::Link, _) => Err(Refusal::Invalid(format!(
            "a link entry carries its link's digest: {LINK_DIGEST_LEN} lowercase hex characters"))),
        (_, Some(_)) => Err(Refusal::Invalid("only a link entry carries a link digest".into())),
        (_, None) => Ok(()),
    }
}

/// Fold one commitment event into the map. Called from `HubState::apply`. Events the routes would
/// have refused (unknown id, already resolved, duplicate open) change nothing, so a write that
/// slipped past a check cannot reset a clock or reopen a commitment on replay.
pub fn fold(commitments: &mut BTreeMap<String, Commitment>, event: &HubEvent, ts: DateTime<Utc>, index: u64) {
    match event {
        HubEvent::CommitmentOpened {
            commitment_id, title, owner, backup, leads_role, ladder, due_at, recorded_by, basis,
        } => {
            commitments.entry(commitment_id.clone()).or_insert_with(|| Commitment {
                commitment_id: commitment_id.clone(),
                title: title.clone(),
                owner: owner.clone(),
                backup: backup.clone(),
                leads_role: leads_role.clone(),
                ladder: ladder.clone(),
                due_at: *due_at,
                recorded_by: *recorded_by,
                basis: *basis,
                opened_at: ts,
                opened_index: index,
                acknowledged: BTreeMap::new(),
                queue: QueuePos::Owner,
                queue_since: ts,
                escalations: Vec::new(),
                resolved: None,
                deliveries: Vec::new(),
                link_acks: BTreeSet::new(),
            });
        }
        HubEvent::CommitmentAcknowledged { commitment_id, party_id, via, link_digest } => {
            let Some(c) = open_mut(commitments, commitment_id) else { return };
            // An operator relay never replaces the party's own word with the operator's: that would
            // turn `owner_acknowledged` false behind the party's back (Legion, #957). The relay still
            // moves the queue below, as any acknowledgement does.
            let own = matches!(c.acknowledged.get(party_id), Some(AckVia::MemberAct | AckVia::Link));
            if !(own && *via == AckVia::Operator) {
                c.acknowledged.insert(party_id.clone(), *via);
            }
            if let Some(d) = link_digest {
                c.link_acks.insert(d.clone());
            }
            // The owner saying "mine" takes the queue back. Anyone else saying "seen" restarts the
            // clock only when the queue is waiting on them; a backup's ack while the owner holds
            // it records the ack and moves nothing (Legion, #947).
            if party_id == &c.owner.party_id {
                c.queue = QueuePos::Owner;
                c.queue_since = ts;
            } else if c.party_at(c.queue).map_or(false, |p| &p.party_id == party_id) {
                c.queue_since = ts;
            }
        }
        HubEvent::CommitmentMoved { commitment_id, by, via, move_kind, to, .. } => {
            let Some(c) = open_mut(commitments, commitment_id) else { return };
            match (move_kind, to) {
                (MoveKind::Update, _) => c.queue = c.position_of(by),
                // "I need help": forward from where the queue stands. The escalation entry the
                // route writes beside it names the same position.
                (MoveKind::Stuck, _) => c.queue = c.queue.next().unwrap_or(QueuePos::Leads),
                (MoveKind::Handoff, Some(to)) => {
                    let previous = std::mem::replace(&mut c.owner, to.clone());
                    // Neither side's acknowledgement carries over: the new owner's was given as
                    // something else, and the old owner's was given as owner.
                    c.acknowledged.remove(&to.party_id);
                    c.acknowledged.remove(&previous.party_id);
                    // Handing to the backup swaps the two, so the commitment keeps a backup.
                    if c.backup.party_id == to.party_id {
                        c.backup = previous;
                    }
                    // A take-over is the new owner's own act only if the ledger has it from them,
                    // not from the operator relaying it.
                    c.basis = if by == &to.party_id && *via != AckVia::Operator {
                        Basis::TakenBySelf
                    } else {
                        Basis::NamedByOther
                    };
                    c.queue = QueuePos::Owner;
                }
                (MoveKind::Handoff, None) => return,
            }
            c.queue_since = ts;
        }
        HubEvent::CommitmentEscalated { commitment_id, step, cause, window_hours, .. } => {
            let Some(c) = open_mut(commitments, commitment_id) else { return };
            c.queue = QueuePos::of_step(*step);
            c.queue_since = ts;
            c.escalations.push(Escalation { step: *step, cause: *cause, window_hours: *window_hours, index });
        }
        HubEvent::NudgeDelivered { commitment_id, about_index, party_id, channel, ok } => {
            let Some(c) = commitments.get_mut(commitment_id) else { return };
            c.deliveries.push(Delivery {
                about_index: *about_index, party_id: party_id.clone(), channel: channel.clone(), ok: *ok, at: ts,
            });
        }
        HubEvent::CommitmentResolved { commitment_id, outcome, by, resolved_at, owner_acknowledged, .. } => {
            let Some(c) = open_mut(commitments, commitment_id) else { return };
            c.resolved = Some(Resolution {
                outcome: *outcome,
                by: by.clone(),
                at: *resolved_at,
                owner_acknowledged: *owner_acknowledged,
                index,
            });
        }
        _ => {}
    }
}

fn open_mut<'a>(commitments: &'a mut BTreeMap<String, Commitment>, id: &str) -> Option<&'a mut Commitment> {
    commitments.get_mut(id).filter(|c| c.is_open())
}

/// What a nudge is about, for its wording.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NudgeAbout {
    /// "You've been named": the opening, to an owner someone else named.
    NamedOwner,
    /// The opening, to the backup.
    NamedBackup,
    /// The queue reached this party's position.
    Escalated,
}

/// One party who should hear about one ledger entry (K3).
#[derive(Clone, Debug, Serialize)]
pub struct NudgeTarget {
    pub about_index: u64,
    pub party: PartyRef,
    pub about: NudgeAbout,
}

impl Commitment {
    /// Who should hear about this commitment now. Only the latest entry that moved it counts (the
    /// opening, or the last escalation), so a nudge the queue has already moved past is never
    /// sent late. An escalation is owed only while the queue still stands at its step: an owner
    /// who took it back has answered it. `leads` are the members holding the leads role, which
    /// only the caller's roster knows.
    pub fn nudge_targets(&self, leads: &[String]) -> Vec<NudgeTarget> {
        if !self.is_open() {
            return Vec::new();
        }
        let Some(e) = self.escalations.last() else {
            let mut t = Vec::new();
            if self.basis == Basis::NamedByOther {
                t.push(NudgeTarget { about_index: self.opened_index, party: self.owner.clone(), about: NudgeAbout::NamedOwner });
            }
            t.push(NudgeTarget { about_index: self.opened_index, party: self.backup.clone(), about: NudgeAbout::NamedBackup });
            return t;
        };
        if self.queue != QueuePos::of_step(e.step) {
            return Vec::new();
        }
        let parties = match e.step {
            EscalationStep::Backup => vec![self.backup.clone()],
            EscalationStep::Leads => leads.iter()
                .map(|id| PartyRef { party_id: id.clone(), kind: PartyKind::Member }).collect(),
        };
        parties.into_iter()
            .map(|party| NudgeTarget { about_index: e.index, party, about: NudgeAbout::Escalated })
            .collect()
    }

    /// Whether a send to this party about this entry has already succeeded.
    pub fn delivered(&self, about_index: u64, party_id: &str) -> bool {
        self.deliveries.iter().any(|d| d.ok && d.about_index == about_index && d.party_id == party_id)
    }

    /// Whether this party's own word is on the ledger: for the owner, [`Self::owner_acknowledged`];
    /// for anyone else, an acknowledgement that did not come through the operator.
    fn own_word(&self, party_id: &str) -> bool {
        if party_id == self.owner.party_id {
            self.owner_acknowledged()
        } else {
            matches!(self.acknowledged.get(party_id), Some(AckVia::MemberAct | AckVia::Link))
        }
    }

    /// The nudge's subject and body. Facts only, and C2 in the wording: silence from someone
    /// whose own acknowledgement is not on the ledger reads "not yet acknowledged by", never
    /// "quiet", so no "late" lands against a name that never said yes (PRD §6). `name` turns a
    /// party into what the reader calls them.
    pub fn nudge_message(&self, target: &NudgeTarget, name: &dyn Fn(&PartyRef) -> String) -> (String, String) {
        let title = &self.title;
        match target.about {
            NudgeAbout::NamedOwner => (
                format!("{title}: you're named as the owner"),
                format!("{title} has been put in your name. Your backup is {}.", name(&self.backup)),
            ),
            NudgeAbout::NamedBackup => (
                format!("{title}: you're the backup"),
                format!("{} owns {title}. You're the backup: if it goes quiet, it comes to you.", name(&self.owner)),
            ),
            NudgeAbout::Escalated => {
                let Some(e) = self.escalations.iter().find(|e| e.index == target.about_index) else {
                    return (format!("{title}: it's with you now"), format!("{title} has reached you."));
                };
                // Who the queue moved on from: the position before this step.
                let before = match e.step {
                    EscalationStep::Backup => &self.owner,
                    EscalationStep::Leads => &self.backup,
                };
                let why = match (e.cause, self.own_word(&before.party_id)) {
                    (EscalationCause::Stuck, _) => format!("{} asked for help.", name(before)),
                    (EscalationCause::Silence, true) => match e.window_hours {
                        Some(h) => format!("Quiet from {} for {h}h.", name(before)),
                        None => format!("Quiet from {}.", name(before)),
                    },
                    (EscalationCause::Silence, false) => format!("Not yet acknowledged by {}.", name(before)),
                };
                let whose = match e.step {
                    EscalationStep::Backup => "You're the backup, so it's with you now.",
                    EscalationStep::Leads => "It has reached the leads.",
                };
                (format!("{title}: it's with you now"), format!("{title}. {why} {whose}"))
            }
        }
    }
}

/// How many nudge attempts, sent or failed, this party has had since `since`, across every
/// commitment. A failed send counts: a carrier retrying a bad address must not spam a good one.
pub fn nudge_attempts_since(commitments: &BTreeMap<String, Commitment>, party_id: &str, since: DateTime<Utc>) -> usize {
    commitments.values().flat_map(|c| &c.deliveries)
        .filter(|d| d.party_id == party_id && d.at >= since).count()
}

/// A member's delivery address. A member is named on the ledger by LCT id; where to reach them is
/// held here, off the ledger, beside the contacts (C3).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct MemberAddress {
    pub address: String,
    pub added_at: DateTime<Utc>,
}

/// One entry in the operator's contact book.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Contact {
    pub name: String,
    /// Where the K3 carrier delivers: an email address today.
    pub address: String,
    pub added_at: DateTime<Utc>,
}

/// The operator's contact book (C3): `party_id` → name and address, held OFF the ledger in a
/// 0600 file beside it. Erasing an entry removes the person's details; the ledger keeps only the
/// opaque id, which then resolves to nothing. Not a projection: nothing here is witnessed.
#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ContactBook {
    pub contacts: BTreeMap<String, Contact>,
    /// Member LCT id → where to deliver (K3). Members have no address anywhere else.
    #[serde(default)]
    pub members: BTreeMap<String, MemberAddress>,
}

impl ContactBook {
    /// Where to deliver to a party, if the operator has said.
    pub fn address_of(&self, p: &PartyRef) -> Option<&str> {
        match p.kind {
            PartyKind::Contact => self.contacts.get(&p.party_id).map(|c| c.address.as_str()),
            PartyKind::Member => self.members.get(&p.party_id).map(|m| m.address.as_str()),
        }
    }
}

impl ContactBook {
    pub fn path(root: &Path) -> PathBuf {
        root.join("contacts.json")
    }

    /// A missing file is an empty book. An unreadable one is an error, never an empty book: a
    /// write after a misread would erase every contact.
    pub fn load(path: &Path) -> Result<Self> {
        match std::fs::read(path) {
            Ok(bytes) => serde_json::from_slice(&bytes)
                .with_context(|| format!("parsing contact book {}", path.display())),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(Self::default()),
            Err(e) => Err(e).with_context(|| format!("reading contact book {}", path.display())),
        }
    }

    pub fn save(&self, path: &Path) -> Result<()> {
        let bytes = serde_json::to_vec_pretty(self).context("serializing contact book")?;
        crate::atomic_file::write_atomic_mode(path, bytes, 0o600)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn member(id: &str) -> PartyRef {
        PartyRef { party_id: id.into(), kind: PartyKind::Member }
    }

    fn opened(id: &str) -> HubEvent {
        HubEvent::CommitmentOpened {
            commitment_id: id.into(),
            title: "Venue AV".into(),
            owner: member("alex"),
            backup: member("sam"),
            leads_role: "leads".into(),
            ladder: vec![48, 24, 24],
            due_at: None,
            recorded_by: Uuid::nil(),
            basis: Basis::NamedByOther,
        }
    }

    fn moved(by: &str, move_kind: MoveKind, to: Option<PartyRef>) -> HubEvent {
        moved_via(by, AckVia::MemberAct, move_kind, to)
    }

    fn moved_via(by: &str, via: AckVia, move_kind: MoveKind, to: Option<PartyRef>) -> HubEvent {
        HubEvent::CommitmentMoved { commitment_id: "c".into(), by: by.into(), via, move_kind, to, note_ref: None,
            link_digest: if via == AckVia::Link { dg() } else { None } }
    }

    /// A fresh link digest per call: each link acknowledgement in a test came through its own link.
    fn dg() -> Option<String> {
        static N: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);
        Some(format!("{:032x}", N.fetch_add(1, std::sync::atomic::Ordering::Relaxed)))
    }

    fn at(h: i64) -> DateTime<Utc> {
        DateTime::UNIX_EPOCH + chrono::Duration::hours(h)
    }

    fn apply(map: &mut BTreeMap<String, Commitment>, ev: HubEvent, h: i64) {
        check(map, &ev).expect("check passes");
        fold(map, &ev, at(h), h as u64);
    }

    #[test]
    fn named_is_not_acknowledged_and_relayed_is_not_the_owners_word() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        assert!(!m["c"].owner_acknowledged(), "C2: named_by_other starts unacknowledged");
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "alex".into(), via: AckVia::Operator, link_digest: None }, 1);
        assert!(!m["c"].owner_acknowledged(), "the operator's relay is not the owner's own word");
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "alex".into(), via: AckVia::Link, link_digest: dg() }, 2);
        assert!(m["c"].owner_acknowledged());
        assert_eq!(m["c"].queue_since, at(2), "an acknowledgement sets the queue");
    }

    #[test]
    fn update_sends_the_queue_to_whoever_moved_and_stuck_moves_it_forward() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        apply(&mut m, HubEvent::CommitmentEscalated {
            commitment_id: "c".into(), step: EscalationStep::Backup, cause: EscalationCause::Silence,
            silent_since: Some(at(0)), window_hours: Some(48), swept_at: at(48) }, 48);
        assert_eq!(m["c"].queue, QueuePos::Backup);
        // The backup updates: the queue is theirs, not reset to the owner (no owner<->backup cycle).
        apply(&mut m, moved("sam", MoveKind::Update, None), 50);
        assert_eq!((m["c"].queue, m["c"].queue_since), (QueuePos::Backup, at(50)));
        apply(&mut m, moved("sam", MoveKind::Stuck, None), 51);
        assert_eq!((m["c"].queue, m["c"].queue_since), (QueuePos::Leads, at(51)));
    }

    #[test]
    fn a_handoff_needs_to_and_resets_acknowledgement_for_the_new_owner() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        assert!(matches!(check(&m, &moved("alex", MoveKind::Handoff, None)), Err(Refusal::Invalid(_))));
        assert!(matches!(check(&m, &moved("alex", MoveKind::Update, Some(member("sam")))), Err(Refusal::Invalid(_))));
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "sam".into(), via: AckVia::Link, link_digest: dg() }, 1);
        // Alex hands to the backup: the two swap, and Sam's acknowledgement as backup does not carry.
        apply(&mut m, moved("alex", MoveKind::Handoff, Some(member("sam"))), 2);
        let c = &m["c"];
        assert_eq!((c.owner.party_id.as_str(), c.backup.party_id.as_str()), ("sam", "alex"));
        assert_eq!((c.basis, c.queue), (Basis::NamedByOther, QueuePos::Owner));
        assert!(!c.owner_acknowledged());
        // A take-over is the new owner's own act...
        apply(&mut m, moved("alex", MoveKind::Handoff, Some(member("alex"))), 3);
        assert_eq!(m["c"].basis, Basis::TakenBySelf);
        assert!(m["c"].owner_acknowledged());
    }

    /// Legion + NOVA on #947: `by` is only as good as `via`. An operator relaying "Sam took it
    /// over" is the operator's word, so it must not make Sam's acknowledgement appear.
    #[test]
    fn an_operator_relayed_take_over_is_not_the_new_owners_word() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        apply(&mut m, moved_via("sam", AckVia::Operator, MoveKind::Handoff, Some(member("sam"))), 1);
        let c = &m["c"];
        assert_eq!((c.owner.party_id.as_str(), c.basis), ("sam", Basis::NamedByOther));
        assert!(!c.owner_acknowledged());
    }

    #[test]
    fn a_swap_drops_the_old_owners_acknowledgement() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "alex".into(), via: AckVia::Link, link_digest: dg() }, 1);
        apply(&mut m, moved("alex", MoveKind::Handoff, Some(member("sam"))), 2);
        assert_eq!(m["c"].backup.party_id, "alex");
        assert!(!m["c"].acknowledged.contains_key("alex"), "alex acknowledged as owner, not as backup");
    }

    #[test]
    fn a_backups_ack_does_not_take_the_queue_from_the_owner() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "sam".into(), via: AckVia::Link, link_digest: dg() }, 5);
        assert_eq!((m["c"].queue, m["c"].queue_since), (QueuePos::Owner, at(0)), "seen is not taken");
        // Once the queue waits on the backup, their ack restarts its clock.
        apply(&mut m, HubEvent::CommitmentEscalated {
            commitment_id: "c".into(), step: EscalationStep::Backup, cause: EscalationCause::Silence,
            silent_since: Some(at(0)), window_hours: Some(48), swept_at: at(48) }, 48);
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "sam".into(), via: AckVia::Link, link_digest: dg() }, 50);
        assert_eq!((m["c"].queue, m["c"].queue_since), (QueuePos::Backup, at(50)));
        // The owner's own "mine" takes it back.
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "alex".into(), via: AckVia::Link, link_digest: dg() }, 51);
        assert_eq!((m["c"].queue, m["c"].queue_since), (QueuePos::Owner, at(51)));
    }

    #[test]
    fn the_loser_of_a_resolution_is_told_what_won() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        apply(&mut m, HubEvent::CommitmentResolved {
            commitment_id: "c".into(), outcome: Outcome::Missed, by: "hub".into(),
            resolved_at: at(5), owner_acknowledged: false, link_digest: None }, 5);
        let late = HubEvent::CommitmentResolved {
            commitment_id: "c".into(), outcome: Outcome::Done, by: "alex".into(),
            resolved_at: at(6), owner_acknowledged: false, link_digest: None };
        let e = check(&m, &late).unwrap_err();
        assert_eq!(e.to_string(), format!("already resolved: commitment c was missed at {}", at(5).to_rfc3339()));
        // The fold backstop: a resolution that got past the check still changes nothing.
        fold(&mut m, &late, at(6), 6);
        assert_eq!(m["c"].resolved.as_ref().unwrap().outcome, Outcome::Missed);
    }

    #[test]
    fn a_duplicate_open_is_refused_and_cannot_reset_the_clock() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        assert_eq!(check(&m, &opened("c")), Err(Refusal::AlreadyOpen("c".into())));
        fold(&mut m, &opened("c"), at(9), 9);
        assert_eq!((m["c"].opened_index, m["c"].queue_since), (0, at(0)));
    }

    #[test]
    fn open_checks_its_shape() {
        let m = BTreeMap::new();
        let mut e = opened("c");
        if let HubEvent::CommitmentOpened { backup, .. } = &mut e { *backup = member("alex"); }
        assert!(check(&m, &e).is_err(), "owner == backup");
        let mut e = opened("c");
        if let HubEvent::CommitmentOpened { ladder, .. } = &mut e { *ladder = vec![0]; }
        assert!(check(&m, &e).is_err(), "zero window");
        let mut e = opened("c");
        if let HubEvent::CommitmentOpened { ladder, .. } = &mut e { *ladder = vec![1, 1, 1, 1]; }
        assert!(check(&m, &e).is_err(), "more windows than positions");
        let mut e = opened("c");
        if let HubEvent::CommitmentOpened { title, .. } = &mut e { *title = "  ".into(); }
        assert!(check(&m, &e).is_err(), "blank title");
    }

    /// K4: an entry carries a link digest exactly when it came through a link, and a link
    /// acknowledges once. A second link may still acknowledge (the queue may need it again).
    #[test]
    fn a_link_digest_marks_link_entries_only_and_acknowledges_once() {
        let ack = |via, link_digest: Option<&str>| HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "alex".into(), via, link_digest: link_digest.map(str::to_string) };
        let d = "0123456789abcdef0123456789abcdef";
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        for bad in [ack(AckVia::Link, None), ack(AckVia::Operator, Some(d)), ack(AckVia::MemberAct, Some(d)),
                    ack(AckVia::Link, Some("0123")), ack(AckVia::Link, Some(&d.to_uppercase())),
                    ack(AckVia::Link, Some(&format!("{}g", &d[1..])))] {
            assert!(matches!(check(&m, &bad), Err(Refusal::Invalid(_))), "{bad:?}");
        }
        apply(&mut m, ack(AckVia::Link, Some(d)), 1);
        assert!(m["c"].link_acks.contains(d));
        assert!(matches!(check(&m, &ack(AckVia::Link, Some(d))), Err(Refusal::Invalid(_))), "used twice");
        let other = "fedcba9876543210fedcba9876543210";
        assert_eq!(check(&m, &ack(AckVia::Link, Some(other))), Ok(()));
        // A link may move as often as it likes: only its acknowledgement is single-use.
        let mv = HubEvent::CommitmentMoved { commitment_id: "c".into(), by: "alex".into(), via: AckVia::Link,
            move_kind: MoveKind::Update, to: None, note_ref: None, link_digest: Some(d.into()) };
        assert_eq!(check(&m, &mv), Ok(()));
        let done = |link_digest: Option<&str>| HubEvent::CommitmentResolved { commitment_id: "c".into(),
            outcome: Outcome::Done, by: "alex".into(), resolved_at: at(2), owner_acknowledged: true,
            link_digest: link_digest.map(str::to_string) };
        assert!(matches!(check(&m, &done(Some("xyz"))), Err(Refusal::Invalid(_))));
        assert_eq!(check(&m, &done(Some(d))), Ok(()));
        assert_eq!(check(&m, &done(None)), Ok(()));
    }

    /// Legion, #957 finding 3: an operator relay must not replace the owner's own word.
    #[test]
    fn an_operator_relay_never_downgrades_a_partys_own_acknowledgement() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "alex".into(), via: AckVia::Link, link_digest: dg() }, 1);
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "alex".into(), via: AckVia::Operator, link_digest: None }, 2);
        assert!(m["c"].owner_acknowledged(), "the relay erased Alex's own word");
        assert_eq!(m["c"].acknowledged["alex"], AckVia::Link);
        // The other way round, the party's own word does replace the relay.
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "sam".into(), via: AckVia::Operator, link_digest: None }, 3);
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "sam".into(), via: AckVia::Link, link_digest: dg() }, 4);
        assert_eq!(m["c"].acknowledged["sam"], AckVia::Link);
    }

    #[test]
    fn only_the_owner_or_backup_acknowledges() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        let e = HubEvent::CommitmentAcknowledged { commitment_id: "c".into(), party_id: "zed".into(), via: AckVia::Link, link_digest: dg() };
        assert!(matches!(check(&m, &e), Err(Refusal::Invalid(_))));
        let e = HubEvent::CommitmentAcknowledged { commitment_id: "nope".into(), party_id: "alex".into(), via: AckVia::Link, link_digest: dg() };
        assert_eq!(check(&m, &e), Err(Refusal::Unknown("nope".into())));
    }

    #[test]
    fn old_entries_without_optional_fields_keep_their_bytes() {
        let e = moved("alex", MoveKind::Update, None);
        let s = serde_json::to_string(&e).unwrap();
        assert!(!s.contains("\"to\"") && !s.contains("note_ref"), "{s}");
        assert!(s.contains("\"kind\":\"commitment_moved\"") && s.contains("\"move_kind\":\"update\""), "{s}");
        let back: HubEvent = serde_json::from_str(&s).unwrap();
        assert_eq!(serde_json::to_string(&back).unwrap(), s);
        let s = serde_json::to_string(&opened("c")).unwrap();
        assert!(s.contains("\"basis\":\"named_by_other\"") && !s.contains("due_at"), "{s}");
    }

    #[test]
    fn the_contact_book_round_trips_and_a_missing_file_is_empty() {
        let tmp = tempfile::tempdir().unwrap();
        let p = ContactBook::path(tmp.path());
        assert_eq!(ContactBook::load(&p).unwrap(), ContactBook::default());
        let mut b = ContactBook::default();
        b.contacts.insert("p1".into(), Contact { name: "Sam".into(), address: "sam@example.org".into(), added_at: at(0) });
        b.save(&p).unwrap();
        assert_eq!(ContactBook::load(&p).unwrap(), b);
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            assert_eq!(std::fs::metadata(&p).unwrap().permissions().mode() & 0o777, 0o600);
        }
        std::fs::write(&p, b"not json").unwrap();
        assert!(ContactBook::load(&p).is_err(), "a misread book must not read as empty");
    }

    fn silence(step: EscalationStep, hours: u32) -> HubEvent {
        HubEvent::CommitmentEscalated {
            commitment_id: "c".into(), step, cause: EscalationCause::Silence,
            silent_since: Some(at(0)), window_hours: Some(hours), swept_at: at(48),
        }
    }

    fn delivered(about_index: u64, party: &str, channel: &str, ok: bool) -> HubEvent {
        HubEvent::NudgeDelivered {
            commitment_id: "c".into(), about_index, party_id: party.into(), channel: channel.into(), ok,
        }
    }

    fn name(p: &PartyRef) -> String {
        match p.party_id.as_str() {
            "alex" => "Alex".into(),
            "sam" => "Sam".into(),
            other => other.into(),
        }
    }

    #[test]
    fn the_opening_nudges_a_named_owner_and_the_backup_and_only_the_latest_entry_counts() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        let t = m["c"].nudge_targets(&[]);
        assert_eq!(t.iter().map(|t| (t.party.party_id.as_str(), t.about)).collect::<Vec<_>>(),
            vec![("alex", NudgeAbout::NamedOwner), ("sam", NudgeAbout::NamedBackup)]);
        assert!(t.iter().all(|t| t.about_index == 0));

        apply(&mut m, silence(EscalationStep::Backup, 48), 48);
        let t = m["c"].nudge_targets(&[]);
        assert_eq!(t.len(), 1, "the opening is superseded: nobody hears about it late");
        assert_eq!((t[0].party.party_id.as_str(), t[0].about_index, t[0].about), ("sam", 48, NudgeAbout::Escalated));

        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "alex".into(), via: AckVia::Link, link_digest: dg() }, 49);
        assert!(m["c"].nudge_targets(&[]).is_empty(), "the owner took it back; the escalation is answered");
    }

    #[test]
    fn a_self_taken_job_does_not_tell_its_owner_they_were_named() {
        let mut m = BTreeMap::new();
        let mut ev = opened("c");
        if let HubEvent::CommitmentOpened { basis, .. } = &mut ev {
            *basis = Basis::TakenBySelf;
        }
        apply(&mut m, ev, 0);
        let t = m["c"].nudge_targets(&[]);
        assert_eq!(t.iter().map(|t| t.party.party_id.as_str()).collect::<Vec<_>>(), vec!["sam"]);
    }

    #[test]
    fn the_leads_step_nudges_every_lead() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        apply(&mut m, silence(EscalationStep::Backup, 48), 48);
        apply(&mut m, silence(EscalationStep::Leads, 24), 72);
        let t = m["c"].nudge_targets(&["lee".into(), "kim".into()]);
        assert_eq!(t.iter().map(|t| (t.party.party_id.as_str(), t.about_index)).collect::<Vec<_>>(),
            vec![("lee", 72), ("kim", 72)]);
    }

    #[test]
    fn the_wording_never_says_quiet_about_someone_who_never_said_yes() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        apply(&mut m, silence(EscalationStep::Backup, 48), 48);
        let t = m["c"].nudge_targets(&[]).remove(0);
        let (_, body) = m["c"].nudge_message(&t, &name);
        assert!(body.contains("Not yet acknowledged by Alex"), "{body}");
        assert!(!body.contains("Quiet"), "C2: named is not acknowledged: {body}");

        // The operator relaying Alex's yes is still not Alex's own word.
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "alex".into(), via: AckVia::Operator, link_digest: None }, 1);
        apply(&mut m, silence(EscalationStep::Backup, 48), 49);
        let t = m["c"].nudge_targets(&[]).remove(0);
        assert!(m["c"].nudge_message(&t, &name).1.contains("Not yet acknowledged by Alex"));

        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "alex".into(), via: AckVia::Link, link_digest: dg() }, 1);
        apply(&mut m, silence(EscalationStep::Backup, 48), 49);
        let t = m["c"].nudge_targets(&[]).remove(0);
        let (subject, body) = m["c"].nudge_message(&t, &name);
        assert_eq!(subject, "Venue AV: it's with you now");
        assert_eq!(body, "Venue AV. Quiet from Alex for 48h. You're the backup, so it's with you now.");
    }

    #[test]
    fn a_delivery_names_a_real_entry_and_a_means_never_an_address() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        assert!(matches!(check(&m, &delivered(7, "sam", "email", true)), Err(Refusal::Invalid(_))),
            "entry 7 is not this commitment's");
        assert!(matches!(check(&m, &delivered(0, "sam", "sam@example.org", true)), Err(Refusal::Invalid(_))),
            "C3: an address is not a channel");
        apply(&mut m, delivered(0, "sam", "email", false), 1);
        assert!(!m["c"].delivered(0, "sam"), "a failed send is recorded, not counted as delivered");
        apply(&mut m, delivered(0, "sam", "email", true), 2);
        assert!(m["c"].delivered(0, "sam"));
        assert_eq!(nudge_attempts_since(&m, "sam", at(0)), 2, "failed attempts count toward the cap");
        assert_eq!(nudge_attempts_since(&m, "sam", at(2)), 1);

        apply(&mut m, HubEvent::CommitmentResolved {
            commitment_id: "c".into(), outcome: Outcome::Done, by: "alex".into(), resolved_at: at(3),
            owner_acknowledged: false, link_digest: None }, 3);
        apply(&mut m, delivered(0, "alex", "email", true), 4);
        assert_eq!(m["c"].deliveries.len(), 3, "a send that raced the resolution is still on the record");
        assert!(m["c"].nudge_targets(&[]).is_empty(), "nothing is owed on a resolved commitment");
    }

    #[test]
    fn a_contact_book_from_before_k3_still_loads() {
        let dir = tempfile::tempdir().unwrap();
        let p = ContactBook::path(dir.path());
        std::fs::write(&p, br#"{"contacts":{}}"#).unwrap();
        let book = ContactBook::load(&p).expect("a K1 book has no members map");
        assert!(book.members.is_empty());
    }
}
