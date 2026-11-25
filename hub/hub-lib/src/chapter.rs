// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! The chapter layer (`hub/docs/PRD_CHAPTER_PRODUCT.md`, from PRD_MEMBER_WEBSITE_FIRST_USER §5b):
//! committees, events with a checklist, and requests that arrived at the chapter's address.
//!
//! It adds no new kind of obligation. Every job is a commitment (K1–K5), so owner, backup,
//! silence that escalates, nudges and answer links all work unchanged. This layer adds the three
//! things a volunteer group needs on top:
//!
//! - **committees**: who leads, who is in, which one watches the chapter inbox. Leads may be
//!   contacts (people with no key), so a co-lead who never installs anything still receives the
//!   last step of every escalation.
//! - **events**: a name, a date, an owner and a backup, with checklist items as commitments in the
//!   event's group.
//! - **requests**: an inbound email became a commitment for the inbox committee; passing it to
//!   another committee ends that commitment (`withdrawn`) and opens one there, so the record reads
//!   as what happened.
//!
//! As in K1, no contact detail reaches the ledger (C3): parties are opaque ids, and the sender of
//! an inbound email lives in the operator's intake file beside the contact book, erasable.

use std::collections::BTreeMap;

use chrono::{DateTime, Utc};
use serde::Serialize;
use uuid::Uuid;

use crate::chapter_page::{is_digest, PagePart, PageVia, NOTHING_PUBLISHED, PAGE_MAINTAINER};
use crate::commitments::{AckVia, PartyRef};
use crate::events::HubEvent;

pub const MAX_COMMITTEE_NAME_LEN: usize = 48;
pub const MAX_PURPOSE_LEN: usize = 200;
pub const MAX_LEADS: usize = 4;
pub const MAX_MEMBERS: usize = 60;
pub const MAX_EVENT_TITLE_LEN: usize = 80;
/// What a lead calls the assistant they appointed ("Claude", "my ChatGPT").
pub const MAX_MAINTAINER_LABEL_LEN: usize = 40;
/// The `leads_role` a chapter commitment carries: its committee's leads are the last step.
pub const COMMITTEE_PREFIX: &str = "committee:";
/// `group` values on `CommitmentOpened`.
pub const EVENT_GROUP_PREFIX: &str = "event:";
pub const REQUEST_GROUP_PREFIX: &str = "request:";

pub fn committee_role(committee_id: &str) -> String {
    format!("{COMMITTEE_PREFIX}{committee_id}")
}

pub fn committee_of_role(leads_role: &str) -> Option<&str> {
    leads_role.strip_prefix(COMMITTEE_PREFIX)
}

pub fn event_group(event_id: &str) -> String {
    format!("{EVENT_GROUP_PREFIX}{event_id}")
}

pub fn request_group(request_id: &str) -> String {
    format!("{REQUEST_GROUP_PREFIX}{request_id}")
}

#[derive(Clone, Debug, Serialize)]
pub struct Committee {
    pub committee_id: String,
    pub name: String,
    pub purpose: String,
    pub leads: Vec<PartyRef>,
    pub members: Vec<PartyRef>,
    /// This committee answers the chapter's address: new requests start here.
    pub inbox: bool,
    pub retired: bool,
    pub set_at: DateTime<Utc>,
    pub index: u64,
}

impl Committee {
    /// Leads first, then members, each once.
    pub fn people(&self) -> Vec<PartyRef> {
        let mut out: Vec<PartyRef> = Vec::new();
        for p in self.leads.iter().chain(self.members.iter()) {
            if !out.iter().any(|q| q.party_id == p.party_id) {
                out.push(p.clone());
            }
        }
        out
    }

    pub fn is_lead(&self, party_id: &str) -> bool {
        self.leads.iter().any(|p| p.party_id == party_id)
    }

    pub fn includes(&self, party_id: &str) -> bool {
        self.is_lead(party_id) || self.members.iter().any(|p| p.party_id == party_id)
    }

    /// Who a new request or a passed one goes to: the first two people, leads first. A committee
    /// with one person has no backup, and cannot take requests until it has two.
    pub fn intake_pair(&self) -> Option<(PartyRef, PartyRef)> {
        let people = self.people();
        match people.as_slice() {
            [a, b, ..] => Some((a.clone(), b.clone())),
            _ => None,
        }
    }
}

#[derive(Clone, Debug, Serialize)]
pub struct ClosedBy {
    pub by: String,
    pub via: AckVia,
    pub at: DateTime<Utc>,
    pub index: u64,
}

#[derive(Clone, Debug, Serialize)]
pub struct ChapterEvent {
    pub event_id: String,
    pub title: String,
    pub starts_at: DateTime<Utc>,
    pub committee_id: String,
    pub owner: PartyRef,
    pub backup: PartyRef,
    pub planned_by: String,
    pub via: AckVia,
    pub planned_at: DateTime<Utc>,
    pub index: u64,
    pub closed: Option<ClosedBy>,
}

#[derive(Clone, Debug, Serialize)]
pub struct Pass {
    pub index: u64,
    pub from_committee_id: String,
    pub to_committee_id: String,
    pub to_commitment_id: String,
    pub by: String,
    pub via: AckVia,
    pub at: DateTime<Utc>,
}

#[derive(Clone, Debug, Serialize)]
pub struct Request {
    pub request_id: String,
    /// Where it is now: the committee and the commitment that currently carry it.
    pub committee_id: String,
    pub commitment_id: String,
    pub channel: String,
    pub received_at: DateTime<Utc>,
    pub index: u64,
    pub passes: Vec<Pass>,
}

/// A page maintainer: a role a chapter lead filled with their own AI assistant
/// (`hub/docs/PRD_CHAPTER_FRONT_PAGE.md`).
#[derive(Clone, Debug, Serialize)]
pub struct Maintainer {
    pub maintainer_id: String,
    pub role: String,
    pub label: String,
    pub appointed_by: String,
    pub expires_at: DateTime<Utc>,
    pub appointed_at: DateTime<Utc>,
    pub index: u64,
    pub revoked: Option<ClosedBy>,
}

/// One version of a front-page part, as the ledger records it.
#[derive(Clone, Debug, Serialize)]
pub struct PageVersion {
    pub part: PagePart,
    pub sha256: String,
    pub by: String,
    pub via: PageVia,
    pub maintainer_id: Option<String>,
    /// The proposal this published, if a lead published an assistant's waiting change.
    pub proposal_id: Option<String>,
    /// An undo: it takes the version before it off the stack instead of adding one.
    pub undo: bool,
    pub at: DateTime<Utc>,
    pub index: u64,
}

/// An assistant's change the chapter's law sent to a co-lead. A lead publishes or discards it by
/// its id, so what they approve is exactly what they saw.
#[derive(Clone, Debug, Serialize)]
pub struct Proposal {
    pub proposal_id: String,
    pub part: PagePart,
    pub sha256: String,
    pub by: String,
    pub maintainer_id: String,
    pub norm: String,
    pub at: DateTime<Utc>,
    pub index: u64,
    pub closed: Option<ProposalClosed>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ProposalEnd {
    /// A lead published it (or the page came to say the same thing another way).
    Published,
    /// A lead discarded it.
    Discarded,
    /// The same assistant proposed something newer for the same part.
    Replaced,
}

#[derive(Clone, Debug, Serialize)]
pub struct ProposalClosed {
    pub how: ProposalEnd,
    pub at: DateTime<Utc>,
    pub index: u64,
}

/// The chapter as the ledger leaves it. Folded by [`fold`] from `HubState::apply`.
#[derive(Clone, Debug, Default, Serialize)]
pub struct Chapter {
    pub committees: BTreeMap<String, Committee>,
    pub events: BTreeMap<String, ChapterEvent>,
    pub requests: BTreeMap<String, Request>,
    pub maintainers: BTreeMap<String, Maintainer>,
    /// Every version of the front page and of the brief, oldest first, undos included.
    pub page_versions: Vec<PageVersion>,
    /// Every proposal ever made, open or closed, by id.
    pub proposals: BTreeMap<String, Proposal>,
}

impl Chapter {
    pub fn live_committees(&self) -> impl Iterator<Item = &Committee> {
        self.committees.values().filter(|c| !c.retired)
    }

    pub fn inbox(&self) -> Option<&Committee> {
        self.live_committees().find(|c| c.inbox)
    }

    /// The request a commitment currently carries, if any.
    pub fn request_of_commitment(&self, commitment_id: &str) -> Option<&Request> {
        self.requests.values().find(|r| r.commitment_id == commitment_id)
    }

    /// Every committee this party leads.
    pub fn led_by<'a>(&'a self, party_id: &'a str) -> impl Iterator<Item = &'a Committee> + 'a {
        self.live_committees().filter(move |c| c.is_lead(party_id))
    }

    /// Whether this party is in the chapter at all: a lead or member of a live committee.
    pub fn knows(&self, party_id: &str) -> bool {
        self.live_committees().any(|c| c.includes(party_id))
    }

    /// The versions of one front-page part, oldest first.
    pub fn versions(&self, part: PagePart) -> impl Iterator<Item = &PageVersion> {
        self.page_versions.iter().filter(move |v| v.part == part)
    }

    /// The versions of a part still standing, oldest first: each set adds one, each undo takes
    /// the top one off. The top is the version in force.
    pub fn stack(&self, part: PagePart) -> Vec<&PageVersion> {
        let mut stack = Vec::new();
        for v in self.versions(part) {
            if v.undo {
                stack.pop();
            } else {
                stack.push(v);
            }
        }
        stack
    }

    /// The version of a part in force now. `None` when nothing was ever published, or an undo
    /// took the page back to before the first one.
    pub fn current(&self, part: PagePart) -> Option<&PageVersion> {
        self.stack(part).last().copied()
    }

    /// Where an undo of `part` would go: `None` when there's nothing to undo, `Some(None)` back
    /// to nothing published, `Some(Some(v))` back to version `v`.
    pub fn undo_target(&self, part: PagePart) -> Option<Option<&PageVersion>> {
        let stack = self.stack(part);
        match stack.len() {
            0 => None,
            n => Some(n.checked_sub(2).map(|i| stack[i])),
        }
    }

    /// Proposals still waiting for a lead, oldest first.
    pub fn open_proposals(&self) -> Vec<&Proposal> {
        let mut v: Vec<&Proposal> = self.proposals.values().filter(|p| p.closed.is_none()).collect();
        v.sort_by_key(|p| p.index);
        v
    }

    /// A maintainer that has not been stopped. Expiry and whether its lead still leads are the
    /// caller's checks, at the time of the act.
    pub fn live_maintainer(&self, maintainer_id: &str) -> Option<&Maintainer> {
        self.maintainers.get(maintainer_id).filter(|m| m.revoked.is_none())
    }
}

/// Why a chapter write was refused. Checked before anything is witnessed, under the same lock as
/// commitments.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Refusal {
    Unknown(String),
    Invalid(String),
    Conflict(String),
}

impl std::fmt::Display for Refusal {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Refusal::Unknown(m) | Refusal::Invalid(m) | Refusal::Conflict(m) => f.write_str(m),
        }
    }
}

fn plain(s: &str, max: usize, field: &str) -> Result<(), Refusal> {
    let t = s.trim();
    if t.is_empty() {
        return Err(Refusal::Invalid(format!("{field} is empty")));
    }
    if t.chars().count() > max || t.chars().any(char::is_control) {
        return Err(Refusal::Invalid(format!("{field} is at most {max} characters on one line")));
    }
    Ok(())
}

fn distinct(parties: &[PartyRef]) -> bool {
    // Within one list. A lead who is also listed as a member is fine: `people()` dedups.
    let mut ids: Vec<&str> = parties.iter().map(|p| p.party_id.as_str()).collect();
    ids.sort();
    let n = ids.len();
    ids.dedup();
    ids.len() == n
}

fn live_committee<'a>(chapter: &'a Chapter, id: &str) -> Result<&'a Committee, Refusal> {
    match chapter.committees.get(id) {
        Some(c) if !c.retired => Ok(c),
        Some(c) => Err(Refusal::Invalid(format!("the {} committee is retired", c.name))),
        None => Err(Refusal::Unknown(format!("no committee {id}"))),
    }
}

/// The checks a chapter event must pass against the projection it would extend. Whether a party
/// exists (member or contact) is the caller's check, as in K1.
pub fn check(chapter: &Chapter, event: &HubEvent) -> Result<(), Refusal> {
    match event {
        HubEvent::ChapterMaintainerAppointed { maintainer_id, role, label, appointed_by, via, link_digest, .. } => {
            if maintainer_id.is_empty() || appointed_by.is_empty() {
                return Err(Refusal::Invalid("a maintainer needs an id and the lead who appointed it".into()));
            }
            if chapter.maintainers.contains_key(maintainer_id) {
                return Err(Refusal::Conflict(format!("maintainer {maintainer_id} already exists")));
            }
            if role != PAGE_MAINTAINER {
                return Err(Refusal::Invalid(format!("unknown maintainer role {role}")));
            }
            plain(label, MAX_MAINTAINER_LABEL_LEN, "the assistant's name")?;
            if *via == AckVia::Link && link_digest.is_none() {
                return Err(Refusal::Invalid("an appointment from a chapter page carries its link digest".into()));
            }
            Ok(())
        }
        HubEvent::ChapterMaintainerRevoked { maintainer_id, .. } => match chapter.maintainers.get(maintainer_id) {
            None => Err(Refusal::Unknown(format!("no maintainer {maintainer_id}"))),
            Some(m) if m.revoked.is_some() => Err(Refusal::Conflict("that assistant was already stopped".into())),
            Some(_) => Ok(()),
        },
        HubEvent::ChapterPageSet { part, sha256, by, via, maintainer_id, proposal_id, undo, .. } => {
            if !is_digest(sha256) {
                return Err(Refusal::Invalid("a page version is named by its sha256: digest".into()));
            }
            if by.is_empty() {
                return Err(Refusal::Invalid("a page version names the lead answerable for it".into()));
            }
            if *undo {
                if *via == PageVia::Maintainer || proposal_id.is_some() {
                    return Err(Refusal::Invalid("only a co-lead undoes a change".into()));
                }
                // An undo names exactly where it goes, so the record can't say one thing and do another.
                let expected = match chapter.undo_target(*part) {
                    None => return Err(Refusal::Conflict(format!("the {} has nothing to undo", part.as_str()))),
                    Some(None) => NOTHING_PUBLISHED.to_string(),
                    Some(Some(v)) => v.sha256.clone(),
                };
                if *sha256 != expected {
                    return Err(Refusal::Conflict("the page changed since that undo was offered".into()));
                }
            } else if sha256 == NOTHING_PUBLISHED {
                return Err(Refusal::Invalid("only an undo goes back to nothing published".into()));
            }
            if let Some(pid) = proposal_id {
                match chapter.proposals.get(pid) {
                    None => return Err(Refusal::Unknown(format!("no proposal {pid}"))),
                    Some(p) if p.closed.is_some() => {
                        return Err(Refusal::Conflict("that proposal isn't waiting any more".into()))
                    }
                    Some(p) if p.part != *part || p.sha256 != *sha256 || Some(&p.maintainer_id) != maintainer_id.as_ref() => {
                        return Err(Refusal::Invalid("a publish names the proposal's own part, digest and assistant".into()))
                    }
                    Some(_) if *via == PageVia::Maintainer => {
                        return Err(Refusal::Invalid("a co-lead publishes a proposal, not the assistant".into()))
                    }
                    Some(_) => {}
                }
            }
            match (via, maintainer_id) {
                (PageVia::Maintainer, None) => Err(Refusal::Invalid("a maintainer's change names the maintainer".into())),
                (PageVia::Maintainer, Some(id)) => match chapter.live_maintainer(id) {
                    None => Err(Refusal::Unknown(format!("no working maintainer {id}"))),
                    Some(m) if m.appointed_by != *by => {
                        Err(Refusal::Invalid("a maintainer acts for the lead who appointed it".into()))
                    }
                    Some(_) => Ok(()),
                },
                // A lead publishing a maintainer's proposal credits it; the maintainer may since
                // have been stopped, so it need only have existed.
                (_, Some(id)) if !chapter.maintainers.contains_key(id) => {
                    Err(Refusal::Unknown(format!("no maintainer {id}")))
                }
                _ => Ok(()),
            }
        }
        HubEvent::ChapterPageProposed { proposal_id, sha256, by, maintainer_id, norm, .. } => {
            if proposal_id.is_empty() || chapter.proposals.contains_key(proposal_id) {
                return Err(Refusal::Conflict("a proposal needs a new id".into()));
            }
            if !is_digest(sha256) || sha256 == NOTHING_PUBLISHED {
                return Err(Refusal::Invalid("a proposal is named by its content's sha256: digest".into()));
            }
            plain(norm, 200, "the norm that sent it to a co-lead")?;
            match chapter.live_maintainer(maintainer_id) {
                None => Err(Refusal::Unknown(format!("no working maintainer {maintainer_id}"))),
                Some(m) if m.appointed_by != *by => {
                    Err(Refusal::Invalid("a maintainer proposes for the lead who appointed it".into()))
                }
                Some(_) => Ok(()),
            }
        }
        HubEvent::ChapterPageDiscarded { proposal_id, by, .. } => {
            if by.is_empty() {
                return Err(Refusal::Invalid("a discard names the lead who did it".into()));
            }
            match chapter.proposals.get(proposal_id) {
                None => Err(Refusal::Unknown(format!("no proposal {proposal_id}"))),
                Some(p) if p.closed.is_some() => Err(Refusal::Conflict("that proposal isn't waiting any more".into())),
                Some(_) => Ok(()),
            }
        }
        HubEvent::CommitteeSet { committee_id, name, purpose, leads, members, inbox, retired, .. } => {
            plain(name, MAX_COMMITTEE_NAME_LEN, "the committee name")?;
            if purpose.chars().count() > MAX_PURPOSE_LEN || purpose.chars().any(char::is_control) {
                return Err(Refusal::Invalid(format!("the purpose is at most {MAX_PURPOSE_LEN} characters on one line")));
            }
            if !*retired && (leads.is_empty() || leads.len() > MAX_LEADS) {
                return Err(Refusal::Invalid(format!("a committee has 1 to {MAX_LEADS} leads")));
            }
            if members.len() > MAX_MEMBERS {
                return Err(Refusal::Invalid(format!("a committee has at most {MAX_MEMBERS} members")));
            }
            if !distinct(leads) || !distinct(members) {
                return Err(Refusal::Invalid("each person is listed once".into()));
            }
            let taken = chapter.live_committees()
                .any(|c| c.committee_id != *committee_id && c.name.eq_ignore_ascii_case(name.trim()));
            if taken && !*retired {
                return Err(Refusal::Conflict(format!("there is already a committee called {}", name.trim())));
            }
            if *inbox && !*retired {
                if let Some(other) = chapter.inbox().filter(|c| c.committee_id != *committee_id) {
                    return Err(Refusal::Conflict(format!(
                        "{} already answers the chapter's address; one committee does", other.name)));
                }
                let mut ids: Vec<&str> = leads.iter().chain(members.iter()).map(|p| p.party_id.as_str()).collect();
                ids.sort();
                ids.dedup();
                if ids.len() < 2 {
                    return Err(Refusal::Invalid(
                        "the committee that answers the chapter's address needs two people, so every request has a backup".into()));
                }
            }
            Ok(())
        }
        HubEvent::ChapterEventPlanned { event_id, title, committee_id, owner, backup, .. } => {
            if chapter.events.contains_key(event_id) {
                return Err(Refusal::Conflict(format!("event {event_id} already exists")));
            }
            plain(title, MAX_EVENT_TITLE_LEN, "the event name")?;
            live_committee(chapter, committee_id)?;
            if owner.party_id == backup.party_id {
                return Err(Refusal::Invalid("the backup must be someone other than the owner".into()));
            }
            Ok(())
        }
        HubEvent::ChapterEventClosed { event_id, .. } => match chapter.events.get(event_id) {
            None => Err(Refusal::Unknown(format!("no event {event_id}"))),
            Some(e) if e.closed.is_some() => Err(Refusal::Conflict(format!("{} is already closed", e.title))),
            Some(_) => Ok(()),
        },
        HubEvent::RequestReceived { request_id, committee_id, .. } => {
            if chapter.requests.contains_key(request_id) {
                return Err(Refusal::Conflict(format!("request {request_id} already exists")));
            }
            live_committee(chapter, committee_id).map(|_| ())
        }
        HubEvent::RequestPassed { request_id, from_commitment_id, to_committee_id, .. } => {
            let r = chapter.requests.get(request_id)
                .ok_or_else(|| Refusal::Unknown(format!("no request {request_id}")))?;
            if r.commitment_id != *from_commitment_id {
                return Err(Refusal::Conflict("this request has already moved on".into()));
            }
            let to = live_committee(chapter, to_committee_id)?;
            if to.committee_id == r.committee_id {
                return Err(Refusal::Invalid(format!("it's already with {}", to.name)));
            }
            Ok(())
        }
        _ => Ok(()),
    }
}

/// Fold one chapter event. Events the routes would have refused change nothing on replay.
pub fn fold(chapter: &mut Chapter, event: &HubEvent, ts: DateTime<Utc>, index: u64) {
    if check(chapter, event).is_err() {
        return;
    }
    match event {
        HubEvent::CommitteeSet { committee_id, name, purpose, leads, members, inbox, retired, .. } => {
            chapter.committees.insert(committee_id.clone(), Committee {
                committee_id: committee_id.clone(),
                name: name.trim().to_string(),
                purpose: purpose.trim().to_string(),
                leads: leads.clone(),
                members: members.clone(),
                inbox: *inbox && !*retired,
                retired: *retired,
                set_at: ts,
                index,
            });
        }
        HubEvent::ChapterEventPlanned { event_id, title, starts_at, committee_id, owner, backup, planned_by, via, .. } => {
            chapter.events.insert(event_id.clone(), ChapterEvent {
                event_id: event_id.clone(),
                title: title.trim().to_string(),
                starts_at: *starts_at,
                committee_id: committee_id.clone(),
                owner: owner.clone(),
                backup: backup.clone(),
                planned_by: planned_by.clone(),
                via: *via,
                planned_at: ts,
                index,
                closed: None,
            });
        }
        HubEvent::ChapterEventClosed { event_id, by, via, closed_at, .. } => {
            if let Some(e) = chapter.events.get_mut(event_id) {
                e.closed = Some(ClosedBy { by: by.clone(), via: *via, at: *closed_at, index });
            }
        }
        HubEvent::RequestReceived { request_id, commitment_id, committee_id, channel, received_at } => {
            chapter.requests.insert(request_id.clone(), Request {
                request_id: request_id.clone(),
                committee_id: committee_id.clone(),
                commitment_id: commitment_id.clone(),
                channel: channel.clone(),
                received_at: *received_at,
                index,
                passes: Vec::new(),
            });
        }
        HubEvent::ChapterMaintainerAppointed { maintainer_id, role, label, appointed_by, expires_at, .. } => {
            chapter.maintainers.insert(maintainer_id.clone(), Maintainer {
                maintainer_id: maintainer_id.clone(),
                role: role.clone(),
                label: label.trim().to_string(),
                appointed_by: appointed_by.clone(),
                expires_at: *expires_at,
                appointed_at: ts,
                index,
                revoked: None,
            });
        }
        HubEvent::ChapterMaintainerRevoked { maintainer_id, by, via, .. } => {
            if let Some(m) = chapter.maintainers.get_mut(maintainer_id) {
                m.revoked = Some(ClosedBy { by: by.clone(), via: *via, at: ts, index });
            }
            // Stopping an assistant is not discarding its work (dp, 11-25): what it left waiting
            // stays waiting, for a lead to publish or discard as separate acts.
        }
        HubEvent::ChapterPageSet { part, sha256, by, via, maintainer_id, proposal_id, undo, .. } => {
            chapter.page_versions.push(PageVersion {
                part: *part,
                sha256: sha256.clone(),
                by: by.clone(),
                via: *via,
                maintainer_id: maintainer_id.clone(),
                proposal_id: proposal_id.clone(),
                undo: *undo,
                at: ts,
                index,
            });
            // The proposal it publishes, and any other that now says what the page says.
            close_proposals(chapter, ProposalEnd::Published, ts, index,
                |p| Some(&p.proposal_id) == proposal_id.as_ref() || (p.part == *part && p.sha256 == *sha256));
        }
        HubEvent::ChapterPageProposed { proposal_id, part, sha256, by, maintainer_id, norm, .. } => {
            close_proposals(chapter, ProposalEnd::Replaced, ts, index,
                |p| p.part == *part && p.maintainer_id == *maintainer_id);
            chapter.proposals.insert(proposal_id.clone(), Proposal {
                proposal_id: proposal_id.clone(),
                part: *part,
                sha256: sha256.clone(),
                by: by.clone(),
                maintainer_id: maintainer_id.clone(),
                norm: norm.clone(),
                at: ts,
                index,
                closed: None,
            });
        }
        HubEvent::ChapterPageDiscarded { proposal_id, .. } => {
            close_proposals(chapter, ProposalEnd::Discarded, ts, index, |p| p.proposal_id == *proposal_id);
        }
        HubEvent::RequestPassed { request_id, to_committee_id, to_commitment_id, by, via, .. } => {
            if let Some(r) = chapter.requests.get_mut(request_id) {
                r.passes.push(Pass {
                    index,
                    from_committee_id: r.committee_id.clone(),
                    to_committee_id: to_committee_id.clone(),
                    to_commitment_id: to_commitment_id.clone(),
                    by: by.clone(),
                    via: *via,
                    at: ts,
                });
                r.committee_id = to_committee_id.clone();
                r.commitment_id = to_commitment_id.clone();
            }
        }
        _ => {}
    }
}

fn close_proposals(chapter: &mut Chapter, how: ProposalEnd, at: DateTime<Utc>, index: u64, which: impl Fn(&Proposal) -> bool) {
    for p in chapter.proposals.values_mut().filter(|p| p.closed.is_none()) {
        if which(p) {
            p.closed = Some(ProposalClosed { how, at, index });
        }
    }
}

/// Rewrite a contact's id to the member it became (K5b2) wherever the chapter names it, so a
/// co-lead who joins keeps leading.
pub fn rebind(chapter: &mut Chapter, party_id: &str, member: &str) {
    let swap = |p: &mut PartyRef| {
        if p.party_id == party_id {
            *p = PartyRef { party_id: member.to_string(), kind: crate::commitments::PartyKind::Member };
        }
    };
    for c in chapter.committees.values_mut() {
        c.leads.iter_mut().for_each(swap);
        c.members.iter_mut().for_each(swap);
    }
    for e in chapter.events.values_mut() {
        swap(&mut e.owner);
        swap(&mut e.backup);
        if e.planned_by == party_id {
            e.planned_by = member.to_string();
        }
    }
    // A co-lead who joins keeps the assistant they appointed, and their page history.
    for m in chapter.maintainers.values_mut() {
        if m.appointed_by == party_id {
            m.appointed_by = member.to_string();
        }
    }
    for v in chapter.page_versions.iter_mut() {
        if v.by == party_id {
            v.by = member.to_string();
        }
    }
    for p in chapter.proposals.values_mut() {
        if p.by == party_id {
            p.by = member.to_string();
        }
    }
}

/// A fresh id for a committee, event or request.
pub fn new_id() -> String {
    Uuid::new_v4().to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::commitments::PartyKind;

    fn contact(id: &str) -> PartyRef {
        PartyRef { party_id: id.into(), kind: PartyKind::Contact }
    }

    fn set(id: &str, name: &str, leads: &[&str], members: &[&str], inbox: bool) -> HubEvent {
        HubEvent::CommitteeSet {
            committee_id: id.into(),
            name: name.into(),
            purpose: String::new(),
            leads: leads.iter().map(|l| contact(l)).collect(),
            members: members.iter().map(|m| contact(m)).collect(),
            inbox,
            retired: false,
            set_by: Uuid::nil(),
        }
    }

    fn folded(events: &[HubEvent]) -> Chapter {
        let mut ch = Chapter::default();
        for (i, e) in events.iter().enumerate() {
            fold(&mut ch, e, Utc::now(), i as u64);
        }
        ch
    }

    #[test]
    fn one_committee_answers_the_chapter_address() {
        let ch = folded(&[set("a", "Leads", &["n", "y"], &[], true)]);
        assert_eq!(ch.inbox().map(|c| c.name.as_str()), Some("Leads"));
        let second = set("b", "Marketing", &["m"], &["k"], true);
        assert!(matches!(check(&ch, &second), Err(Refusal::Conflict(_))));
    }

    #[test]
    fn the_inbox_committee_needs_a_backup() {
        let ch = Chapter::default();
        assert!(check(&ch, &set("a", "Leads", &["n"], &[], true)).is_err());
        assert!(check(&ch, &set("a", "Leads", &["n"], &["m"], true)).is_ok());
    }

    #[test]
    fn names_are_unique_and_people_listed_once() {
        let ch = folded(&[set("a", "Marketing", &["m"], &[], false)]);
        assert!(check(&ch, &set("b", "marketing", &["k"], &[], false)).is_err());
        assert!(check(&ch, &set("b", "Events", &["k", "k"], &[], false)).is_err());
        // Updating the same committee under its own name is fine.
        assert!(check(&ch, &set("a", "Marketing", &["m", "k"], &[], false)).is_ok());
    }

    #[test]
    fn intake_pair_is_leads_first() {
        let ch = folded(&[set("a", "Leads", &["n"], &["y", "z"], true)]);
        let (o, b) = ch.inbox().unwrap().intake_pair().unwrap();
        assert_eq!((o.party_id.as_str(), b.party_id.as_str()), ("n", "y"));
    }

    #[test]
    fn a_request_passes_once_from_where_it_is() {
        let ch = folded(&[
            set("a", "Leads", &["n", "y"], &[], true),
            set("b", "Partnerships", &["p", "q"], &[], false),
            HubEvent::RequestReceived { request_id: "r".into(), commitment_id: "c1".into(),
                committee_id: "a".into(), channel: "email".into(), received_at: Utc::now() },
        ]);
        let pass = |from: &str, to: &str| HubEvent::RequestPassed {
            request_id: "r".into(), from_commitment_id: from.into(), to_committee_id: to.into(),
            to_commitment_id: "c2".into(), by: "n".into(), via: AckVia::Link, link_digest: None };
        assert!(check(&ch, &pass("c1", "a")).is_err(), "already there");
        assert!(check(&ch, &pass("c0", "b")).is_err(), "stale commitment");
        let mut ch = ch;
        fold(&mut ch, &pass("c1", "b"), Utc::now(), 9);
        let r = &ch.requests["r"];
        assert_eq!((r.committee_id.as_str(), r.commitment_id.as_str(), r.passes.len()), ("b", "c2", 1));
        assert!(check(&ch, &pass("c1", "a")).is_err(), "the old commitment no longer carries it");
    }

    #[test]
    fn an_event_closes_once() {
        let mut ch = folded(&[set("a", "Events", &["e", "f"], &[], false)]);
        let plan = HubEvent::ChapterEventPlanned {
            event_id: "ev".into(), title: "December social".into(), starts_at: Utc::now(),
            committee_id: "a".into(), owner: contact("e"), backup: contact("f"),
            planned_by: "e".into(), via: AckVia::Link, link_digest: None };
        fold(&mut ch, &plan, Utc::now(), 3);
        assert!(check(&ch, &plan).is_err(), "same id twice");
        let close = HubEvent::ChapterEventClosed { event_id: "ev".into(), by: "e".into(), via: AckVia::Link,
            link_digest: None, closed_at: Utc::now() };
        fold(&mut ch, &close, Utc::now(), 4);
        assert!(ch.events["ev"].closed.is_some());
        assert!(check(&ch, &close).is_err());
    }

    #[test]
    fn a_contact_who_joins_keeps_leading() {
        let mut ch = folded(&[set("a", "Leads", &["n", "y"], &[], true)]);
        rebind(&mut ch, "n", "member-n");
        assert!(ch.committees["a"].is_lead("member-n"));
        assert!(!ch.committees["a"].is_lead("n"));
    }
}
