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

use std::collections::BTreeMap;
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

#[derive(Clone, Debug, Serialize)]
pub struct Escalation {
    pub step: EscalationStep,
    pub cause: EscalationCause,
    pub index: u64,
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
        | HubEvent::CommitmentResolved { commitment_id, .. } => Some(commitment_id),
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
    if let Some(r) = &c.resolved {
        return Err(Refusal::AlreadyResolved { commitment_id: id.to_string(), outcome: r.outcome, at: r.at });
    }
    match event {
        HubEvent::CommitmentAcknowledged { party_id, .. } => {
            if party_id != &c.owner.party_id && party_id != &c.backup.party_id {
                return Err(Refusal::Invalid(format!(
                    "{party_id} is neither the owner nor the backup of {id}; only they acknowledge")));
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
            });
        }
        HubEvent::CommitmentAcknowledged { commitment_id, party_id, via } => {
            let Some(c) = open_mut(commitments, commitment_id) else { return };
            c.acknowledged.insert(party_id.clone(), *via);
            c.queue = c.position_of(party_id);
            c.queue_since = ts;
        }
        HubEvent::CommitmentMoved { commitment_id, by, move_kind, to, .. } => {
            let Some(c) = open_mut(commitments, commitment_id) else { return };
            match (move_kind, to) {
                (MoveKind::Update, _) => c.queue = c.position_of(by),
                // "I need help": forward from where the queue stands. The escalation entry the
                // route writes beside it names the same position.
                (MoveKind::Stuck, _) => c.queue = c.queue.next().unwrap_or(QueuePos::Leads),
                (MoveKind::Handoff, Some(to)) => {
                    let previous = std::mem::replace(&mut c.owner, to.clone());
                    // Handing to the backup swaps the two, so the commitment keeps a backup.
                    if c.backup.party_id == to.party_id {
                        c.backup = previous;
                    }
                    c.basis = if by == &to.party_id { Basis::TakenBySelf } else { Basis::NamedByOther };
                    c.acknowledged.remove(&to.party_id);
                    c.queue = QueuePos::Owner;
                }
                (MoveKind::Handoff, None) => return,
            }
            c.queue_since = ts;
        }
        HubEvent::CommitmentEscalated { commitment_id, step, cause, .. } => {
            let Some(c) = open_mut(commitments, commitment_id) else { return };
            c.queue = QueuePos::of_step(*step);
            c.queue_since = ts;
            c.escalations.push(Escalation { step: *step, cause: *cause, index });
        }
        HubEvent::CommitmentResolved { commitment_id, outcome, by, resolved_at, owner_acknowledged } => {
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
        HubEvent::CommitmentMoved { commitment_id: "c".into(), by: by.into(), move_kind, to, note_ref: None }
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
            commitment_id: "c".into(), party_id: "alex".into(), via: AckVia::Operator }, 1);
        assert!(!m["c"].owner_acknowledged(), "the operator's relay is not the owner's own word");
        apply(&mut m, HubEvent::CommitmentAcknowledged {
            commitment_id: "c".into(), party_id: "alex".into(), via: AckVia::Link }, 2);
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
            commitment_id: "c".into(), party_id: "sam".into(), via: AckVia::Link }, 1);
        // Alex hands to the backup: the two swap, and Sam's acknowledgement as backup does not carry.
        apply(&mut m, moved("alex", MoveKind::Handoff, Some(member("sam"))), 2);
        let c = &m["c"];
        assert_eq!((c.owner.party_id.as_str(), c.backup.party_id.as_str()), ("sam", "alex"));
        assert_eq!((c.basis, c.queue), (Basis::NamedByOther, QueuePos::Owner));
        assert!(!c.owner_acknowledged());
        // A take-over is the new owner's own act.
        apply(&mut m, moved("alex", MoveKind::Handoff, Some(member("alex"))), 3);
        assert_eq!(m["c"].basis, Basis::TakenBySelf);
        assert!(m["c"].owner_acknowledged());
    }

    #[test]
    fn the_loser_of_a_resolution_is_told_what_won() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        apply(&mut m, HubEvent::CommitmentResolved {
            commitment_id: "c".into(), outcome: Outcome::Missed, by: "hub".into(),
            resolved_at: at(5), owner_acknowledged: false }, 5);
        let late = HubEvent::CommitmentResolved {
            commitment_id: "c".into(), outcome: Outcome::Done, by: "alex".into(),
            resolved_at: at(6), owner_acknowledged: false };
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

    #[test]
    fn only_the_owner_or_backup_acknowledges() {
        let mut m = BTreeMap::new();
        apply(&mut m, opened("c"), 0);
        let e = HubEvent::CommitmentAcknowledged { commitment_id: "c".into(), party_id: "zed".into(), via: AckVia::Link };
        assert!(matches!(check(&m, &e), Err(Refusal::Invalid(_))));
        let e = HubEvent::CommitmentAcknowledged { commitment_id: "nope".into(), party_id: "alex".into(), via: AckVia::Link };
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
}
