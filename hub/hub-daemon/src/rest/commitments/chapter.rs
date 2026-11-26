//! The chapter layer's routes (`hub/docs/PRD_CHAPTER_PRODUCT.md`): what a volunteer sees.
//!
//! The rule for every surface here: **nobody does extra work.** Officers live in their email, so
//! everything is reachable from a link in an email they already got:
//!
//! - `/h/:token` is a person's chapter page: what needs them now, what they own and back up, the
//!   chapter's events, and who does what. The token is minted for one party, like a K4 movement
//!   link, and rides along in every nudge and notice. No login, nothing to install.
//! - `/h/:token/plan` (a lead) plans an event: name, date, owner, backup. The standard checklist
//!   becomes commitments in the event's group. Owner and backup each get ONE email for the whole
//!   event, not one per item.
//! - `/h/:token/e/:event_id` is the event's checklist and its record, in plain words, and where
//!   the owner or a lead closes it. Closing emails the recap to the committee.
//! - `/c/:token/pass/:committee_id` passes an inbound request to the committee it belongs with.
//! - `POST /admin/api/chapter/intake` is where the intake carrier hands over one email.
//! - `/admin/api/chapter/notices` is what the carrier should send besides nudges: a welcome with
//!   each person's chapter page, "you're on this event", and recaps.
//!
//! No page here uses a protocol word. The person reading is a volunteer, not an operator.

use super::*;
use std::collections::{BTreeMap, BTreeSet};
use hub_lib::chapter::{self as ch, Committee};
use hub_lib::commitments::Basis;

mod front_page;
mod front_text;
pub(crate) use front_page::*;

const HOME_LABEL: &[u8] = b"web4-hub chapter home v1\n";
const HOME_TTL_DAYS: i64 = 45;
/// Inbound requests move fast: a day for the owner, a day for the backup, then the leads.
/// `HUB_CHAPTER_REQUEST_HOURS` changes the day (1 to 720), e.g. to rehearse within an hour.
fn request_ladder() -> Vec<u32> {
    let h = std::env::var("HUB_CHAPTER_REQUEST_HOURS").ok().and_then(|v| v.trim().parse::<u32>().ok())
        .filter(|h| (1..=commitments::MAX_WINDOW_HOURS).contains(h)).unwrap_or(24);
    vec![h, h]
}
/// After an item's target date passes in silence, the backup gets two days before the leads.
const BACKUP_WINDOW_HOURS: u32 = 48;
const MAX_EXCERPT_CHARS: usize = 4000;
const MAX_SUBJECT_CHARS: usize = 200;
const NOTICE_MAX_ATTEMPTS: u32 = 3;

/// The standard checklist: what a chapter event needs, and how many days before the event each
/// should be done by. A lead unticks what doesn't apply.
///
/// It follows the chapter's own pipeline (core meeting 2026-10-27): the two people running the event
/// write the prospectus; Partnerships resources it (venue, sponsors); Marketing does the plan and the
/// Luma page; then speakers and the day-of. The fourth field names the committee that owns a step,
/// matched by name ("partnership", "marketing"); `None`, or no such committee with two people, means
/// the event's own owner and backup.
pub(crate) const CHECKLIST: [(&str, &str, i64, Option<&str>); 5] = [
    ("prospectus", "Prospectus written", 35, None),
    ("venue", "Venue and sponsors confirmed", 21, Some("partnership")),
    ("marketing", "Marketing plan and Luma page live", 14, Some("marketing")),
    ("speakers", "Speakers confirmed", 10, None),
    ("dayof", "Day-of roles and run of show", 2, None),
];

/// The committee a checklist step goes to, if the chapter has one that can take it.
fn team_for<'a>(state: &'a HubState, hint: Option<&str>, event_committee: &str) -> Option<&'a Committee> {
    let hint = hint?;
    state.chapter.live_committees()
        .find(|k| k.name.to_lowercase().contains(hint) && k.committee_id != event_committee && k.intake_pair().is_some())
}

// ---------------------------------------------------------------------------------------------
// Time: the chapter's local time, from HUB_CHAPTER_UTC_OFFSET ("-08:00"). Unset is UTC.
// ---------------------------------------------------------------------------------------------

pub(crate) fn chapter_offset() -> chrono::FixedOffset {
    let utc = chrono::FixedOffset::east_opt(0).expect("zero offset");
    let Ok(v) = std::env::var("HUB_CHAPTER_UTC_OFFSET") else { return utc };
    let v = v.trim();
    let (sign, rest) = match v.chars().next() {
        Some('-') => (-1, &v[1..]),
        Some('+') => (1, &v[1..]),
        _ => (1, v),
    };
    let mut parts = rest.split(':');
    let h: i32 = parts.next().and_then(|h| h.parse().ok()).unwrap_or(0);
    let m: i32 = parts.next().and_then(|m| m.parse().ok()).unwrap_or(0);
    chrono::FixedOffset::east_opt(sign * (h * 3600 + m * 60)).unwrap_or(utc)
}

pub(crate) fn local_day(t: DateTime<Utc>) -> String {
    t.with_timezone(&chapter_offset()).format("%a %b %-d").to_string()
}

pub(crate) fn local_time(t: DateTime<Utc>) -> String {
    t.with_timezone(&chapter_offset()).format("%a %b %-d, %-I:%M %p").to_string()
}

fn parse_local(date: &str, time: &str) -> Option<DateTime<Utc>> {
    let d = chrono::NaiveDate::parse_from_str(date.trim(), "%Y-%m-%d").ok()?;
    let t = if time.trim().is_empty() {
        chrono::NaiveTime::from_hms_opt(18, 0, 0)?
    } else {
        chrono::NaiveTime::parse_from_str(time.trim(), "%H:%M").ok()?
    };
    d.and_time(t).and_local_timezone(chapter_offset()).single().map(|t| t.with_timezone(&Utc))
}

// ---------------------------------------------------------------------------------------------
// Who leads a commitment, and naming
// ---------------------------------------------------------------------------------------------

/// The parties at the end of a commitment's ladder. A chapter commitment names its committee
/// (`committee:<id>`), whose leads may be contacts. Anything else is a role entity, as in K1.
pub(crate) fn lead_parties(state: &HubState, c: &Commitment) -> Vec<PartyRef> {
    if let Some(id) = ch::committee_of_role(&c.leads_role) {
        return state.chapter.committees.get(id).filter(|k| !k.retired)
            .map(|k| k.leads.iter().map(|p| canonical(state, p)).collect())
            .unwrap_or_default();
    }
    role_leads(state, c).into_iter().map(|id| PartyRef { party_id: id, kind: PartyKind::Member }).collect()
}

/// A party as who they are now: a contact who joined reads as the member they became.
pub(crate) fn canonical(state: &HubState, p: &PartyRef) -> PartyRef {
    let id = state.invites.canonical_id(&p.party_id);
    if id == p.party_id {
        p.clone()
    } else {
        PartyRef { party_id: id, kind: PartyKind::Member }
    }
}

fn name_of(state: &HubState, book: &ContactBook, p: &PartyRef) -> String {
    party_view(state, book, p)["name"].as_str().map(str::to_string).unwrap_or_else(|| "someone".to_string())
}

fn first_name(full: &str) -> String {
    full.split_whitespace().next().unwrap_or(full).to_string()
}

fn name_by_id(state: &HubState, book: &ContactBook, id: &str) -> String {
    if book.contacts.contains_key(id) {
        return name_of(state, book, &PartyRef { party_id: id.to_string(), kind: PartyKind::Contact });
    }
    if id == SWEEP_ACTOR {
        return "the reminder system".to_string();
    }
    name_of(state, book, &PartyRef { party_id: id.to_string(), kind: PartyKind::Member })
}

/// Every person the chapter knows, canonical, each once, in committee order.
fn chapter_people(state: &HubState) -> Vec<PartyRef> {
    let mut out: Vec<PartyRef> = Vec::new();
    for k in state.chapter.live_committees() {
        for p in k.people() {
            let p = canonical(state, &p);
            if !out.iter().any(|q| q.party_id == p.party_id) {
                out.push(p);
            }
        }
    }
    out
}

fn knows(state: &HubState, party_id: &str) -> bool {
    chapter_people(state).iter().any(|p| p.party_id == party_id)
}

fn is_lead_of(state: &HubState, k: &Committee, party_id: &str) -> bool {
    k.leads.iter().any(|p| canonical(state, p).party_id == party_id)
}

fn committee_people(state: &HubState, k: &Committee) -> Vec<PartyRef> {
    k.people().iter().map(|p| canonical(state, p)).collect()
}

fn committee_name(state: &HubState, id: &str) -> String {
    state.chapter.committees.get(id).map(|k| k.name.clone()).unwrap_or_else(|| "a committee".to_string())
}

fn ch_refused(r: ch::Refusal) -> ApiError {
    let status = match r {
        ch::Refusal::Unknown(_) => StatusCode::NOT_FOUND,
        ch::Refusal::Conflict(_) => StatusCode::CONFLICT,
        ch::Refusal::Invalid(_) => StatusCode::BAD_REQUEST,
    };
    ApiError { status, message: r.to_string() }
}

/// Check a chapter event against the projection, then witness it. The caller holds
/// [`COMMITMENT_LOCK`].
async fn chapter_witness(s: &RestState, event: HubEvent) -> Result<u64, ApiError> {
    {
        let ledger = s.ledger.lock().await;
        let state = s.projected(&ledger);
        ch::check(&state.chapter, &event).map_err(ch_refused)?;
    }
    witness_event(s, event).await
}

// ---------------------------------------------------------------------------------------------
// Off-ledger files: the intake file (who wrote, what they said) and the notices sent
// ---------------------------------------------------------------------------------------------

/// One inbound email as the intake carrier read it. Off the ledger (C3), 0600, erasable.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub(crate) struct IntakeMessage {
    pub message_id: String,
    pub from_name: String,
    pub from_address: String,
    pub subject: String,
    pub excerpt: String,
    pub received_at: DateTime<Utc>,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub(crate) struct IntakeFile {
    /// request_id → the message.
    pub requests: BTreeMap<String, IntakeMessage>,
}

fn intake_path(root: &std::path::Path) -> std::path::PathBuf {
    root.join("chapter-intake.json")
}

pub(crate) fn load_intake(root: &std::path::Path) -> Result<IntakeFile, ApiError> {
    match std::fs::read(intake_path(root)) {
        Ok(b) => serde_json::from_slice(&b).map_err(|e| ApiError::internal(anyhow::anyhow!("intake file: {e}"))),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(IntakeFile::default()),
        Err(e) => Err(ApiError::internal(e.into())),
    }
}

fn save_intake(root: &std::path::Path, f: &IntakeFile) -> Result<(), ApiError> {
    let bytes = serde_json::to_vec_pretty(f).map_err(|e| ApiError::internal(e.into()))?;
    hub_lib::atomic_file::write_atomic_mode(&intake_path(root), bytes, 0o600).map_err(ApiError::internal)
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub(crate) struct NoticeFile {
    pub sent: BTreeSet<String>,
    pub failures: BTreeMap<String, u32>,
    /// Who a chapter lead has invited: only they get the welcome. Seeding someone into a committee
    /// is not inviting them; nobody hears from a tool before a co-lead has decided they should.
    #[serde(default)]
    pub invited: BTreeSet<String>,
}

fn notices_path(root: &std::path::Path) -> std::path::PathBuf {
    root.join("chapter-notices.json")
}

fn load_notices(root: &std::path::Path) -> Result<NoticeFile, ApiError> {
    match std::fs::read(notices_path(root)) {
        Ok(b) => serde_json::from_slice(&b).map_err(|e| ApiError::internal(anyhow::anyhow!("notices file: {e}"))),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(NoticeFile::default()),
        Err(e) => Err(ApiError::internal(e.into())),
    }
}

fn save_notices(root: &std::path::Path, f: &NoticeFile) -> Result<(), ApiError> {
    let bytes = serde_json::to_vec_pretty(f).map_err(|e| ApiError::internal(e.into()))?;
    hub_lib::atomic_file::write_atomic_mode(&notices_path(root), bytes, 0o600).map_err(ApiError::internal)
}

// ---------------------------------------------------------------------------------------------
// Home links
// ---------------------------------------------------------------------------------------------

pub(crate) fn mint_home(key: &[u8; 32], party_id: &str, now: DateTime<Utc>) -> String {
    mint_token(HOME_LABEL, key, &[party_id], now + chrono::Duration::days(HOME_TTL_DAYS))
}

fn read_home(key: &[u8; 32], token: &str, now: DateTime<Utc>) -> Result<(String, String), LinkError> {
    let (mut fields, digest) = read_token(HOME_LABEL, key, token, 1, now)?;
    Ok((fields.pop().expect("one field"), digest))
}

/// The chapter page link for a party, if the hub has a public address.
pub(crate) fn home_url(base: &str, key: &[u8; 32], party_id: &str, now: DateTime<Utc>) -> String {
    format!("{base}/h/{}", mint_home(key, party_id, now))
}

/// A home token, verified, with its party read as who they are now.
struct HomeClaim {
    token: String,
    party_id: String,
    digest: String,
    key: [u8; 32],
}

fn verified_home(s: &RestState, token: &str) -> Result<HomeClaim, axum::response::Response> {
    let key = match read_link_key(&s.paths.root) {
        Ok(Some(key)) => key,
        Ok(None) => return Err(link_error_page(LinkError::Invalid)),
        Err(e) => {
            tracing::warn!("chapter link key unreadable: {e:#}");
            return Err(link_page_response(StatusCode::INTERNAL_SERVER_ERROR, "Something went wrong",
                "<h1>Something went wrong</h1><p>Please try again later.</p>"));
        }
    };
    let (party_id, digest) = read_home(&key, token, Utc::now()).map_err(link_error_page)?;
    Ok(HomeClaim { token: token.to_string(), party_id, digest, key })
}

// ---------------------------------------------------------------------------------------------
// Plain-language record of a job: the minutes
// ---------------------------------------------------------------------------------------------

/// What happened to one job, in order, in plain words.
pub(crate) fn job_story(state: &HubState, book: &ContactBook, c: &Commitment) -> Vec<(u64, DateTime<Utc>, String)> {
    let n = |p: &PartyRef| first_name(&name_of(state, book, p));
    let by = |id: &str| first_name(&name_by_id(state, book, id));
    let mut lines: Vec<(u64, DateTime<Utc>, String)> = Vec::new();
    lines.push((c.opened_index, c.opened_at, match c.basis {
        Basis::TakenBySelf => format!("{} took it on, with {} as backup.", n(&c.owner), n(&c.backup)),
        Basis::NamedByOther => format!("Given to {}, with {} as backup.", n(&c.owner), n(&c.backup)),
    }));
    for h in &c.handoffs {
        lines.push((h.index, c.opened_at, format!("{} handed it on.", by(&h.previous_owner.party_id))));
    }
    for e in &c.escalations {
        let what = match (e.cause, e.step) {
            (commitments::EscalationCause::Stuck, _) => "Someone asked for help, so it moved up.".to_string(),
            (_, commitments::EscalationStep::Backup) => "It went quiet, so it went to the backup.".to_string(),
            (_, commitments::EscalationStep::Leads) => "It stayed quiet, so it reached the committee leads.".to_string(),
        };
        lines.push((e.index, c.opened_at, what));
    }
    if let Some(r) = &c.resolved {
        let what = match r.outcome {
            Outcome::Done => format!("Done, marked by {}.", by(&r.by)),
            Outcome::Withdrawn => format!("Closed without doing it, by {}.", by(&r.by)),
            Outcome::Missed => "The date passed with nobody on it.".to_string(),
        };
        lines.push((r.index, r.at, what));
    }
    lines.sort_by_key(|l| l.0);
    lines
}

/// One line on where a job stands, for lists.
fn job_status(state: &HubState, book: &ContactBook, c: &Commitment) -> String {
    if let Some(r) = &c.resolved {
        return match r.outcome {
            Outcome::Done => format!("done ({})", local_day(r.at)),
            Outcome::Withdrawn => "closed".to_string(),
            Outcome::Missed => "missed".to_string(),
        };
    }
    let owner = first_name(&name_of(state, book, &c.owner));
    if is_event_item(c) && c.queue == commitments::QueuePos::Owner {
        return match target_of(c) {
            Some(t) => format!("{owner}, by {}", local_day(t)),
            None => owner,
        };
    }
    match c.queue {
        commitments::QueuePos::Owner if c.owner_acknowledged() => format!("{owner} is on it"),
        commitments::QueuePos::Owner => format!("waiting for {owner} to say yes"),
        commitments::QueuePos::Backup => format!("with the backup, {}", first_name(&name_of(state, book, &c.backup))),
        commitments::QueuePos::Leads => "needs a lead".to_string(),
    }
}

/// The date an item aims for: the end of its owner's first silence window.
fn target_of(c: &Commitment) -> Option<DateTime<Utc>> {
    c.ladder.first().map(|h| c.opened_at + chrono::Duration::hours(i64::from(*h)))
}

pub(crate) fn is_event_item(c: &Commitment) -> bool {
    c.group.as_deref().is_some_and(|g| g.starts_with(ch::EVENT_GROUP_PREFIX))
}

/// "Aim to have it done by Thu Nov 26", for a checklist item's own page.
pub(crate) fn item_target_line(c: &Commitment) -> Option<String> {
    if !is_event_item(c) || !c.is_open() {
        return None;
    }
    target_of(c).map(|t| format!("Aim to have it done by {}. You'll only hear about it again if that date passes \
        and it isn't marked done.", local_day(t)))
}

/// Whether a job needs this person now. An event's checklist item doesn't need its owner until its
/// date is close; until then it sits under "Yours" without asking for anything.
fn needs(state: &HubState, c: &Commitment, me: &str, now: DateTime<Utc>) -> bool {
    match c.queue {
        commitments::QueuePos::Owner => c.owner.party_id == me && if is_event_item(c) {
            target_of(c).is_some_and(|t| t - now < chrono::Duration::days(3))
        } else {
            !c.owner_acknowledged()
        },
        commitments::QueuePos::Backup => c.backup.party_id == me,
        commitments::QueuePos::Leads => lead_parties(state, c).iter().any(|p| p.party_id == me),
    }
}

fn items_of_event<'a>(state: &'a HubState, event_id: &str) -> Vec<&'a Commitment> {
    let group = ch::event_group(event_id);
    let mut items: Vec<&Commitment> = state.commitments.values()
        .filter(|c| c.group.as_deref() == Some(group.as_str())).collect();
    items.sort_by_key(|c| c.opened_index);
    items
}

// ---------------------------------------------------------------------------------------------
// Pages
// ---------------------------------------------------------------------------------------------

fn options(state: &HubState, book: &ContactBook, people: &[PartyRef], selected: Option<&str>) -> String {
    people.iter().map(|p| {
        let sel = if Some(p.party_id.as_str()) == selected { " selected" } else { "" };
        format!("<option value=\"{}\"{sel}>{}</option>", esc(&p.party_id), esc(&name_of(state, book, p)))
    }).collect()
}

fn job_row(state: &HubState, book: &ContactBook, key: &[u8; 32], party_id: &str, c: &Commitment, now: DateTime<Utc>) -> String {
    let link = mint_link(key, &c.commitment_id, party_id, now + chrono::Duration::days(LINK_TTL_DAYS));
    // On your own page, your own checklist item reads "by Thu Nov 26", not "Ines, by Thu Nov 26".
    let status = match target_of(c) {
        Some(d) if is_event_item(c) && c.owner.party_id == party_id && c.queue == commitments::QueuePos::Owner =>
            format!("by {}", local_day(d)),
        _ => job_status(state, book, c),
    };
    format!("<li><a href=\"/c/{}\">{}</a> <span class=\"muted\">{}</span></li>",
        esc(&link), esc(&c.title), esc(&status))
}

/// `GET /h/:token` — a person's chapter page.
///
/// surface: chapter_home   act: none (a read of the chapter by one of its people)
/// S: low/reversible [construct: no write]   R: pass [construct: read_home, HMAC over party + expiry]
/// W: n/a (read) — discloses to one chapter person what PRD §5b says every member may read: committees,
///    leads, members, and who owns each open job. Nothing from the intake file appears here.
/// O: n/a   A: n/a (read)   V: n/a
/// verdict: PASS
pub(crate) async fn home_page(State(s): State<RestState>, Path(token): Path<String>) -> axum::response::Response {
    let claim = match verified_home(&s, &token) {
        Ok(c) => c,
        Err(page) => return page,
    };
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let book = load_book(&s).unwrap_or_default();
    let me = state.invites.canonical_id(&claim.party_id);
    if !knows(&state, &me) {
        return link_page_response(StatusCode::OK, &s.hub_name,
            "<h1>You're not on a committee right now</h1><p>Ask a chapter lead to add you.</p>");
    }
    let now = Utc::now();
    let my_name = first_name(&name_by_id(&state, &book, &me));
    let mut html = format!("<p class=\"muted\">{}</p><h1>Hi {}</h1>", esc(&s.hub_name), esc(&my_name));

    // What needs this person now: the queue stands at them.
    let open: Vec<&Commitment> = open_by_queue(&state);
    let waiting_on_me: Vec<&Commitment> = open.iter().copied().filter(|c| needs(&state, c, &me, now)).collect();
    let needed = |c: &&Commitment| waiting_on_me.iter().any(|w| w.commitment_id == c.commitment_id);
    html.push_str("<section><h2>Needs you</h2>");
    if waiting_on_me.is_empty() {
        html.push_str("<p class=\"ok\">Nothing right now.</p>");
    } else {
        html.push_str("<ul>");
        for c in &waiting_on_me {
            html.push_str(&job_row(&state, &book, &claim.key, &me, c, now));
        }
        html.push_str("</ul>");
    }
    html.push_str("</section>");

    let mine: Vec<&Commitment> = open.iter().copied().filter(|c| c.owner.party_id == me && !needed(c)).collect();
    let backing: Vec<&Commitment> = open.iter().copied().filter(|c| c.backup.party_id == me && !needed(c)).collect();
    if !mine.is_empty() || !backing.is_empty() {
        html.push_str("<section><h2>Yours</h2>");
        if mine.is_empty() {
            html.push_str("<p class=\"muted\">Nothing else in your name.</p>");
        } else {
            html.push_str("<ul>");
            for c in &mine {
                html.push_str(&job_row(&state, &book, &claim.key, &me, c, now));
            }
            html.push_str("</ul>");
        }
        if !backing.is_empty() {
            html.push_str("<h3>You're the backup</h3><ul>");
            for c in &backing {
                html.push_str(&job_row(&state, &book, &claim.key, &me, c, now));
            }
            html.push_str("</ul>");
        }
        html.push_str("</section>");
    }

    // The front page, for a chapter lead: hand it to their own assistant, and see what changed.
    // Near the top, because what members see first is the co-leads' to shape.
    html.push_str(&front_page_section(&s, &state, &book, &claim.key, &claim.token, &me).await);

    // Events, soonest first; closed ones from the last month after.
    let mut events: Vec<&ch::ChapterEvent> = state.chapter.events.values()
        .filter(|e| e.closed.is_none() || e.starts_at > now - chrono::Duration::days(30)).collect();
    events.sort_by_key(|e| (e.closed.is_some(), e.starts_at));
    html.push_str("<section><h2>Events</h2>");
    if events.is_empty() {
        html.push_str("<p class=\"muted\">No events planned yet.</p>");
    } else {
        html.push_str("<ul>");
        for e in events {
            let items = items_of_event(&state, &e.event_id);
            let done = items.iter().filter(|c| matches!(&c.resolved, Some(r) if r.outcome == Outcome::Done)).count();
            let status = if e.closed.is_some() { "finished".to_string() } else { format!("{done} of {} ready", items.len()) };
            html.push_str(&format!("<li><a href=\"/h/{}/e/{}\">{}</a> <span class=\"muted\">{} · {} · owner {}</span></li>",
                esc(&claim.token), esc(&e.event_id), esc(&e.title), esc(&local_day(e.starts_at)), esc(&status),
                esc(&first_name(&name_of(&state, &book, &e.owner)))));
        }
        html.push_str("</ul>");
    }
    html.push_str("</section>");

    // Who does what: every committee, its leads and people, and its open jobs with their owners.
    html.push_str("<section><h2>Who does what</h2>");
    let mut committees: Vec<&Committee> = state.chapter.live_committees().collect();
    committees.sort_by_key(|k| (!k.inbox, k.name.to_lowercase()));
    for k in committees {
        let leads: Vec<String> = k.leads.iter().map(|p| name_of(&state, &book, &canonical(&state, p))).collect();
        let others: Vec<String> = k.members.iter().map(|p| canonical(&state, p))
            .filter(|p| !is_lead_of(&state, k, &p.party_id))
            .map(|p| name_of(&state, &book, &p)).collect();
        html.push_str(&format!("<h3>{}{}</h3>", esc(&k.name),
            if k.inbox { " <span class=\"tag\">answers the chapter's email</span>" } else { "" }));
        if !k.purpose.is_empty() {
            html.push_str(&format!("<p class=\"muted\">{}</p>", esc(&k.purpose)));
        }
        html.push_str(&format!("<p>Led by {}{}</p>", esc(&leads.join(" and ")),
            if others.is_empty() { String::new() } else { format!(". With {}.", esc(&others.join(", "))) }));
        let role = ch::committee_role(&k.committee_id);
        let jobs: Vec<&&Commitment> = open.iter().filter(|c| c.leads_role == role && !is_event_item(c)).collect();
        for e in state.chapter.events.values().filter(|e| e.committee_id == k.committee_id && e.closed.is_none()) {
            let items = items_of_event(&state, &e.event_id);
            let done = items.iter().filter(|c| matches!(&c.resolved, Some(r) if r.outcome == Outcome::Done)).count();
            html.push_str(&format!("<p class=\"muted\">{}: {} of {} ready, owner {}, backup {}</p>", esc(&e.title), done,
                items.len(), esc(&first_name(&name_of(&state, &book, &e.owner))),
                esc(&first_name(&name_of(&state, &book, &e.backup)))));
        }
        if !jobs.is_empty() {
            html.push_str("<ul class=\"compact\">");
            for c in jobs {
                html.push_str(&format!("<li>{} <span class=\"muted\">{} · backup {}</span></li>", esc(&c.title),
                    esc(&job_status(&state, &book, c)), esc(&first_name(&name_of(&state, &book, &c.backup)))));
            }
            html.push_str("</ul>");
        }
    }
    html.push_str("</section>");

    // The roster: chapter leads run it; a committee lead adds to their own committee.
    let invited = load_notices(&s.paths.root).map(|f| f.invited).unwrap_or_default();
    let roster = roster_html(&state, &book, &claim.token, &me, &invited);
    if !roster.is_empty() {
        html.push_str("<section><h2>People</h2>");
        html.push_str(&roster);
        html.push_str("</section>");
    }


    // A lead can plan an event or add a to-do for a committee they lead.
    let led: Vec<&Committee> = state.chapter.live_committees().filter(|k| is_lead_of(&state, k, &me)).collect();
    if !led.is_empty() {
        let people = chapter_people(&state);
        let committees: String = led.iter()
            .map(|k| format!("<option value=\"{}\">{}</option>", esc(&k.committee_id), esc(&k.name))).collect();
        let checks: String = CHECKLIST.iter().map(|(id, label, days, hint)| {
            let who = team_for(&state, *hint, "").map(|k| format!(", {}", k.name)).unwrap_or_default();
            format!("<label class=\"check\"><input type=\"checkbox\" name=\"item_{id}\" checked> {label} \
                <span class=\"muted\">({days} days before{})</span></label>", esc(&who))
        }).collect();
        html.push_str(&format!(
            "<details><summary>Plan an event</summary>\
             <form method=\"post\" action=\"/h/{tok}/plan\" class=\"stack\">\
             <label>What is it<input name=\"title\" required maxlength=\"60\" placeholder=\"December social\"></label>\
             <label>Date<input type=\"date\" name=\"date\" required></label>\
             <label>Start time<input type=\"time\" name=\"time\" value=\"18:00\"></label>\
             <label>Committee<select name=\"committee_id\">{committees}</select></label>\
             <label>Owner<select name=\"owner\">{owners}</select></label>\
             <label>Backup<select name=\"backup\">{backups}</select></label>\
             <fieldset><legend>Checklist</legend>{checks}</fieldset>\
             <button>Plan it</button>\
             <p class=\"muted\">The owner and backup each get one email. After that you'll only hear about \
             an item if its date passes with nobody on it.</p></form></details>\
             <details><summary>Add a to-do</summary>\
             <form method=\"post\" action=\"/h/{tok}/todo\" class=\"stack\">\
             <label>What needs doing<input name=\"title\" required maxlength=\"80\"></label>\
             <label>By<input type=\"date\" name=\"date\" required></label>\
             <label>Committee<select name=\"committee_id\">{committees}</select></label>\
             <label>Owner<select name=\"owner\">{owners}</select></label>\
             <label>Backup<select name=\"backup\">{backups}</select></label>\
             <button>Add it</button></form></details>",
            tok = esc(&claim.token),
            owners = options(&state, &book, &people, Some(&me)),
            backups = options(&state, &book, &people, people.iter().map(|p| p.party_id.as_str()).find(|p| *p != me)),
        ));
    }
    html.push_str(&format!("<p class=\"muted\">This page is yours: it comes from your own link, so please don't forward it. \
        <a href=\"/h/{}/leave\">Not for you?</a></p>", esc(&claim.token)));
    link_page_response(StatusCode::OK, &s.hub_name, &html)
}

/// `GET /h/:token/e/:event_id` — an event's checklist and its record.
pub(crate) async fn event_page(
    State(s): State<RestState>, Path((token, event_id)): Path<(String, String)>,
) -> axum::response::Response {
    let claim = match verified_home(&s, &token) {
        Ok(c) => c,
        Err(page) => return page,
    };
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let book = load_book(&s).unwrap_or_default();
    let me = state.invites.canonical_id(&claim.party_id);
    let Some(e) = state.chapter.events.get(&event_id).filter(|_| knows(&state, &me)) else {
        return link_page_response(StatusCode::NOT_FOUND, "Not found", "<h1>That event isn't here</h1>");
    };
    let now = Utc::now();
    let n = |p: &PartyRef| name_of(&state, &book, &canonical(&state, p));
    let mut html = format!("<p><a href=\"/h/{}\">← Your chapter page</a></p><h1>{}</h1><p>{} · {}</p>\
        <p>Owner {}, backup {}.</p>",
        esc(&claim.token), esc(&e.title), esc(&local_time(e.starts_at)), esc(&committee_name(&state, &e.committee_id)),
        esc(&n(&e.owner)), esc(&n(&e.backup)));
    let items = items_of_event(&state, &e.event_id);
    html.push_str("<section><h2>Checklist</h2><ul>");
    for c in &items {
        let named = c.owner.party_id == me || c.backup.party_id == me
            || lead_parties(&state, c).iter().any(|p| p.party_id == me);
        if named && c.is_open() {
            html.push_str(&job_row(&state, &book, &claim.key, &me, c, now));
        } else {
            html.push_str(&format!("<li>{} <span class=\"muted\">{}</span></li>",
                esc(&c.title), esc(&job_status(&state, &book, c))));
        }
    }
    html.push_str("</ul></section>");

    // The record: every job's story, merged in ledger order, plus the event's own lines.
    let mut record: Vec<(u64, String)> = vec![(e.index, format!("{} planned it.",
        first_name(&name_by_id(&state, &book, &e.planned_by))))];
    for c in &items {
        let short = c.title.rsplit(": ").next().unwrap_or(&c.title).to_string();
        for (i, _, line) in job_story(&state, &book, c) {
            record.push((i, format!("{short}: {line}")));
        }
    }
    if let Some(cl) = &e.closed {
        record.push((cl.index, format!("{} closed the event on {}.", first_name(&name_by_id(&state, &book, &cl.by)),
            local_day(cl.at))));
    }
    record.sort_by_key(|r| r.0);
    html.push_str("<section><h2>What happened</h2><ol class=\"record\">");
    for (_, line) in &record {
        html.push_str(&format!("<li>{}</li>", esc(line)));
    }
    html.push_str("</ol></section>");

    let may_close = e.closed.is_none() && (e.owner.party_id == me || e.backup.party_id == me
        || state.chapter.committees.get(&e.committee_id).is_some_and(|k| is_lead_of(&state, k, &me)));
    if may_close {
        html.push_str(&format!("<form method=\"post\" action=\"/h/{}/e/{}/close\"><button>The event is over: \
            close it and send the recap</button></form>", esc(&claim.token), esc(&e.event_id)));
    }
    link_page_response(StatusCode::OK, &e.title, &html)
}

fn form_page(status: StatusCode, title: &str, token: &str, msg: &str) -> axum::response::Response {
    link_page_response(status, title, &format!("<h1>{}</h1><p><a href=\"/h/{}\">Back to your chapter page</a></p>",
        esc(msg), esc(token)))
}

fn api_error_page(token: &str, e: ApiError) -> axum::response::Response {
    if e.status.is_server_error() {
        tracing::warn!("chapter form not saved: {}", e.message);
        return form_page(StatusCode::SERVICE_UNAVAILABLE, "Not saved", token,
            "That didn't save just now. Please try again later.");
    }
    form_page(e.status, "Not saved", token, &format!("Not saved: {}", e.message))
}

/// The parties a form names, checked: each must be someone the chapter knows.
fn known_party(state: &HubState, id: &str, field: &str) -> Result<PartyRef, ApiError> {
    chapter_people(state).into_iter().find(|p| p.party_id == id)
        .ok_or_else(|| ApiError::bad_request(format!("pick the {field} from the list")))
}

fn led_committee<'a>(state: &'a HubState, id: &str, me: &str, operator: bool) -> Result<&'a Committee, ApiError> {
    let k = state.chapter.committees.get(id).filter(|k| !k.retired)
        .ok_or_else(|| ApiError::bad_request("pick a committee from the list"))?;
    if !operator && !is_lead_of(state, k, me) {
        return Err(ApiError { status: StatusCode::FORBIDDEN, message: format!("only a lead of {} can do that", k.name) });
    }
    Ok(k)
}

/// What planning an event needs, from a form or the operator's JSON.
#[derive(Clone, Debug, Deserialize)]
pub(crate) struct PlanBody {
    pub title: String,
    pub date: String,
    #[serde(default)]
    pub time: String,
    pub committee_id: String,
    pub owner: String,
    pub backup: String,
    /// Checklist ids from [`CHECKLIST`]. Absent means all of them.
    #[serde(default)]
    pub items: Option<Vec<String>>,
}

/// Plan an event and open its checklist. `by` is the planner (a party, or the operator's id).
/// The caller holds [`COMMITMENT_LOCK`].
pub(crate) async fn plan_event(
    s: &RestState, body: PlanBody, by: &str, via: AckVia, digest: Option<String>, operator: bool,
) -> Result<serde_json::Value, ApiError> {
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let k = led_committee(&state, &body.committee_id, by, operator)?;
    let owner = known_party(&state, &body.owner, "owner")?;
    let backup = known_party(&state, &body.backup, "backup")?;
    let starts_at = parse_local(&body.date, &body.time)
        .ok_or_else(|| ApiError::bad_request("the date or time didn't read; use the date picker"))?;
    let now = Utc::now();
    if starts_at < now {
        return Err(ApiError::bad_request("that date has already passed"));
    }
    let title = body.title.trim().to_string();
    let event_id = ch::new_id();
    let entry = chapter_witness(s, HubEvent::ChapterEventPlanned {
        event_id: event_id.clone(),
        title: title.clone(),
        starts_at,
        committee_id: k.committee_id.clone(),
        owner: owner.clone(),
        backup: backup.clone(),
        planned_by: by.to_string(),
        via,
        link_digest: digest,
    }).await?;
    let short: String = title.chars().take(commitments::MAX_TITLE_LEN - 24).collect();
    let mut opened = Vec::new();
    for (id, label, days, hint) in CHECKLIST {
        if body.items.as_ref().is_some_and(|ids| !ids.iter().any(|i| i == id)) {
            continue;
        }
        let target = (starts_at - chrono::Duration::days(days)).max(now + chrono::Duration::hours(48));
        let hours = ((target - now).num_hours().max(48) as u32).min(commitments::MAX_WINDOW_HOURS);
        let commitment_id = Uuid::new_v4().to_string();
        // A step another committee owns goes to that committee's first two people, and its leads
        // are the last stop; the rest stay with the event's owner and backup.
        let (item_owner, item_backup, item_committee) = match team_for(&state, hint, &k.committee_id) {
            Some(team) => {
                let (o, b) = team.intake_pair().expect("team_for requires two people");
                (canonical(&state, &o), canonical(&state, &b), team.committee_id.clone())
            }
            None => (owner.clone(), backup.clone(), k.committee_id.clone()),
        };
        let basis = if item_owner.party_id == by { Basis::TakenBySelf } else { Basis::NamedByOther };
        let index = checked_witness(s, HubEvent::CommitmentOpened {
            commitment_id: commitment_id.clone(),
            title: format!("{short}: {label}"),
            owner: item_owner,
            backup: item_backup,
            leads_role: ch::committee_role(&item_committee),
            ladder: vec![hours, BACKUP_WINDOW_HOURS],
            due_at: None,
            recorded_by: s.sovereign_lct_id,
            basis,
            group: Some(ch::event_group(&event_id)),
        }).await?;
        opened.push(serde_json::json!({ "commitment_id": commitment_id, "title": label, "entry_index": index }));
    }
    Ok(serde_json::json!({ "planned": true, "event_id": event_id, "entry_index": entry, "items": opened }))
}

#[derive(Clone, Debug, Deserialize)]
pub(crate) struct TodoBody {
    pub title: String,
    pub date: String,
    pub committee_id: String,
    pub owner: String,
    pub backup: String,
}

pub(crate) async fn add_todo(
    s: &RestState, body: TodoBody, by: &str, operator: bool,
) -> Result<serde_json::Value, ApiError> {
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let k = led_committee(&state, &body.committee_id, by, operator)?;
    let owner = known_party(&state, &body.owner, "owner")?;
    let backup = known_party(&state, &body.backup, "backup")?;
    let by_when = parse_local(&body.date, "17:00").ok_or_else(|| ApiError::bad_request("the date didn't read"))?;
    let now = Utc::now();
    let hours = (((by_when - now).num_hours()).max(24) as u32).min(commitments::MAX_WINDOW_HOURS);
    let title: String = body.title.trim().chars().take(commitments::MAX_TITLE_LEN).collect();
    let commitment_id = Uuid::new_v4().to_string();
    let index = checked_witness(s, HubEvent::CommitmentOpened {
        commitment_id: commitment_id.clone(),
        title,
        owner: owner.clone(),
        backup,
        leads_role: ch::committee_role(&k.committee_id),
        ladder: vec![hours, BACKUP_WINDOW_HOURS],
        due_at: None,
        recorded_by: s.sovereign_lct_id,
        basis: if owner.party_id == by { Basis::TakenBySelf } else { Basis::NamedByOther },
        group: None,
    }).await?;
    Ok(serde_json::json!({ "opened": true, "commitment_id": commitment_id, "entry_index": index }))
}

fn form_items(form: &std::collections::HashMap<String, String>) -> Vec<String> {
    CHECKLIST.iter().filter(|(id, ..)| form.contains_key(&format!("item_{id}"))).map(|(id, ..)| id.to_string()).collect()
}

fn form_field(form: &std::collections::HashMap<String, String>, k: &str) -> String {
    form.get(k).cloned().unwrap_or_default()
}

/// `POST /h/:token/plan` — a lead plans an event from their chapter page.
///
/// surface: chapter_plan_event   act: record an event and open its checklist, as a lead of its committee
/// S: low/reversible [construct: each item is a commitment; withdrawn ends one]
/// R: weak (possession of the lead's home link) [construct: read_home]
/// W: pass [construct: the party must lead the committee, re-checked under COMMITMENT_LOCK]
/// O: pass [construct: chapter::check and commitments::check before each witness]
/// A: pass [construct: ChapterEventPlanned names planned_by, via=link and the token's digest]
/// V: n/a (reversible)
/// verdict: PASS, read as possession-only like every link act
pub(crate) async fn home_plan(
    State(s): State<RestState>, Path(token): Path<String>,
    axum::extract::Form(form): axum::extract::Form<std::collections::HashMap<String, String>>,
) -> axum::response::Response {
    let claim = match verified_home(&s, &token) {
        Ok(c) => c,
        Err(page) => return page,
    };
    let _serial = COMMITMENT_LOCK.lock().await;
    let me = { let ledger = s.ledger.lock().await; s.projected(&ledger).invites.canonical_id(&claim.party_id) };
    let body = PlanBody {
        title: form_field(&form, "title"), date: form_field(&form, "date"), time: form_field(&form, "time"),
        committee_id: form_field(&form, "committee_id"), owner: form_field(&form, "owner"),
        backup: form_field(&form, "backup"), items: Some(form_items(&form)),
    };
    match plan_event(&s, body, &me, AckVia::Link, Some(claim.digest.clone()), false).await {
        Ok(v) => {
            let id = v["event_id"].as_str().unwrap_or_default().to_string();
            link_page_response(StatusCode::OK, "Planned", &format!(
                "<h1>Planned.</h1><p>The owner and backup will each get an email.</p>\
                 <p><a href=\"/h/{t}/e/{id}\">See the checklist</a> · <a href=\"/h/{t}\">Your chapter page</a></p>",
                t = esc(&claim.token), id = esc(&id)))
        }
        Err(e) => api_error_page(&claim.token, e),
    }
}

/// `POST /h/:token/todo` — a lead adds a to-do for their committee. Same reading as plan.
pub(crate) async fn home_todo(
    State(s): State<RestState>, Path(token): Path<String>,
    axum::extract::Form(form): axum::extract::Form<std::collections::HashMap<String, String>>,
) -> axum::response::Response {
    let claim = match verified_home(&s, &token) {
        Ok(c) => c,
        Err(page) => return page,
    };
    let _serial = COMMITMENT_LOCK.lock().await;
    let me = { let ledger = s.ledger.lock().await; s.projected(&ledger).invites.canonical_id(&claim.party_id) };
    let body = TodoBody {
        title: form_field(&form, "title"), date: form_field(&form, "date"),
        committee_id: form_field(&form, "committee_id"), owner: form_field(&form, "owner"),
        backup: form_field(&form, "backup"),
    };
    match add_todo(&s, body, &me, false).await {
        Ok(_) => form_page(StatusCode::OK, "Added", &claim.token, "Added. The owner and backup will hear about it."),
        Err(e) => api_error_page(&claim.token, e),
    }
}

/// `POST /h/:token/e/:event_id/close` — the owner, backup or a lead closes the event.
pub(crate) async fn home_close_event(
    State(s): State<RestState>, Path((token, event_id)): Path<(String, String)>,
) -> axum::response::Response {
    let claim = match verified_home(&s, &token) {
        Ok(c) => c,
        Err(page) => return page,
    };
    let _serial = COMMITMENT_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let me = state.invites.canonical_id(&claim.party_id);
    let Some(e) = state.chapter.events.get(&event_id) else {
        return form_page(StatusCode::NOT_FOUND, "Not found", &claim.token, "That event isn't here.");
    };
    let may = e.owner.party_id == me || e.backup.party_id == me
        || state.chapter.committees.get(&e.committee_id).is_some_and(|k| is_lead_of(&state, k, &me));
    if !may {
        return form_page(StatusCode::FORBIDDEN, "Not yours", &claim.token,
            "Only the event's owner, its backup or a committee lead can close it.");
    }
    let r = chapter_witness(&s, HubEvent::ChapterEventClosed {
        event_id: event_id.clone(), by: me, via: AckVia::Link, link_digest: Some(claim.digest.clone()),
        closed_at: Utc::now(),
    }).await;
    match r {
        Ok(_) => link_page_response(StatusCode::OK, "Closed", &format!(
            "<h1>Closed. The recap is on its way to the committee.</h1><p><a href=\"/h/{t}/e/{id}\">See the record</a></p>",
            t = esc(&claim.token), id = esc(&event_id))),
        Err(e) => api_error_page(&claim.token, e),
    }
}

/// Chapter wording for a nudge about an email to the chapter or a checklist item. `None` for
/// anything else, which keeps the commitments wording.
pub(crate) fn chapter_nudge_message(
    state: &HubState, c: &Commitment, t: &commitments::NudgeTarget, name: &dyn Fn(&PartyRef) -> String,
) -> Option<(String, String)> {
    use commitments::{EscalationStep, NudgeAbout};
    let owner = first_name(&name(&c.owner));
    let backup = first_name(&name(&c.backup));
    if let Some(r) = state.chapter.request_of_commitment(&c.commitment_id) {
        let subject = c.title.trim_start_matches("Email: ").to_string();
        let team = committee_name(state, &r.committee_id);
        return Some(match t.about {
            NudgeAbout::NamedOwner | NudgeAbout::HandedOwner => (format!("New email to the chapter: {subject}"),
                format!("An email came in to the chapter, and it's yours to answer ({team}). {backup} is your backup.")),
            NudgeAbout::NamedBackup | NudgeAbout::HandedBackup => (format!("You're backup on: {subject}"),
                format!("{owner} is answering an email to the chapter. If it goes unanswered, it comes to you. \
                    Nothing to do now.")),
            NudgeAbout::HandedAway => (format!("Off your list: {subject}"), format!("{owner} has it now.")),
            NudgeAbout::Escalated => {
                let step = c.escalations.iter().find(|e| e.index == t.about_index).map(|e| e.step);
                match step {
                    Some(EscalationStep::Leads) => (format!("Nobody has answered: {subject}"), format!(
                        "An email to the chapter has gone unanswered by {owner} and then {backup}. It's with the \
                         leads now: one of you, please take it or pass it on.")),
                    _ => (format!("Still unanswered: {subject}"), format!(
                        "{owner} hasn't answered this email to the chapter yet, so as backup it's with you now.")),
                }
            }
        });
    }
    if is_event_item(c) {
        let (event, item) = c.title.split_once(": ").map(|(e, i)| (e.to_string(), i.to_string()))
            .unwrap_or((String::new(), c.title.clone()));
        let when = target_of(c).map(|d| format!(" It was due {}.", local_day(d))).unwrap_or_default();
        if let NudgeAbout::Escalated = t.about {
            let step = c.escalations.iter().find(|e| e.index == t.about_index).map(|e| (e.step, e.cause));
            return Some(match step {
                Some((_, commitments::EscalationCause::Stuck)) => (format!("{event}: help needed on {item}"),
                    format!("{owner} asked for help with {item} for {event}. It's with you now.")),
                Some((EscalationStep::Leads, _)) => (format!("{event}: {item} still isn't done"), format!(
                    "{item} for {event} isn't marked done, and neither {owner} nor {backup} has picked it up.{when} \
                     It's with the committee leads now.")),
                _ => (format!("{event}: {item} isn't done yet"), format!(
                    "{item} for {event} isn't marked done.{when} {owner} owns it; as backup, it's with you now.")),
            });
        }
    }
    None
}

// ---------------------------------------------------------------------------------------------
// Requests: the inbound email on its job page, and passing it on
// ---------------------------------------------------------------------------------------------

fn mailto(to: &str, subject: &str) -> String {
    let enc = |s: &str| s.bytes().map(|b| match b {
        b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'.' | b'_' | b'~' => (b as char).to_string(),
        _ => format!("%{b:02X}"),
    }).collect::<String>();
    let subj = if subject.to_ascii_lowercase().starts_with("re:") { subject.to_string() } else { format!("Re: {subject}") };
    format!("mailto:{}?subject={}", enc(to), enc(&subj))
}

/// The top of a job page for an email to the chapter: who wrote, what they said, and a reply
/// button that opens the person's own mail program. The answers follow it.
pub(crate) fn request_head(s: &RestState, state: &HubState, c: &Commitment, owner_view: bool, owner: &str, backup: &str) -> String {
    let Some(r) = state.chapter.request_of_commitment(&c.commitment_id) else { return String::new() };
    let intake = load_intake(&s.paths.root).unwrap_or_default();
    let who = if owner_view {
        format!("It's yours to answer. {} is your backup.", first_name(backup))
    } else {
        format!("{} has it. You're named on it too.", first_name(owner))
    };
    let mut html = format!("<p class=\"kicker\">An email to the chapter · {}</p>", esc(&committee_name(state, &r.committee_id)));
    match intake.requests.get(&r.request_id) {
        Some(m) => {
            html.push_str(&format!("<h1>{}</h1><p><b>{}</b> &lt;{}&gt;<br><span class=\"muted\">{}</span></p><pre>{}</pre>",
                esc(&m.subject), esc(&m.from_name), esc(&m.from_address), esc(&local_time(m.received_at)), esc(&m.excerpt)));
            html.push_str(&format!("<p>{}</p>", esc(&who)));
            html.push_str(&format!("<p><a class=\"button\" href=\"{}\">Reply from your email</a></p>",
                esc(&mailto(&m.from_address, &m.subject))));
            html.push_str("<p class=\"muted\">Reply as you normally would, then press \"I've answered it\" below.</p>");
        }
        None => html.push_str(&format!("<h1>{}</h1><p class=\"muted\">The original message has been erased.</p><p>{}</p>",
            esc(c.title.trim_start_matches("Email: ")), esc(&who))),
    }
    html
}

pub(crate) fn request_act_label(act: LinkAct, backup: &str) -> String {
    match act {
        LinkAct::Ack => "I'll answer it".to_string(),
        LinkAct::Done => "I've answered it".to_string(),
        LinkAct::Handoff => format!("Hand it to {}", first_name(backup)),
        LinkAct::Take => "I'll answer it instead".to_string(),
        LinkAct::Update => "Still on it".to_string(),
        LinkAct::Stuck => "I need help".to_string(),
    }
}

/// The rest of a request's page: where else it could go, and where it has been.
pub(crate) fn request_panel(s: &RestState, state: &HubState, c: &Commitment, token: &str) -> String {
    let Some(r) = state.chapter.request_of_commitment(&c.commitment_id) else { return String::new() };
    let mut html = String::from("<section class=\"request\">");
    if c.is_open() {
        let mut others: Vec<&Committee> = state.chapter.live_committees()
            .filter(|k| k.committee_id != r.committee_id && k.intake_pair().is_some()).collect();
        others.sort_by_key(|k| k.name.to_lowercase());
        if !others.is_empty() {
            html.push_str("<details><summary>Belongs with another committee?</summary><div class=\"chips\">");
            for k in others {
                html.push_str(&format!("<form method=\"post\" action=\"/c/{}/pass/{}\"><button>{}</button></form>",
                    esc(token), esc(&k.committee_id), esc(&k.name)));
            }
            html.push_str("</div><p class=\"muted\">Their lead gets it, with a backup, and it leaves your list.</p></details>");
        }
    }
    if !r.passes.is_empty() {
        let book = load_book(s).unwrap_or_default();
        html.push_str("<p class=\"muted\">");
        for p in &r.passes {
            html.push_str(&format!("{} passed it from {} to {}. ", esc(&first_name(&name_by_id(state, &book, &p.by))),
                esc(&committee_name(state, &p.from_committee_id)), esc(&committee_name(state, &p.to_committee_id))));
        }
        html.push_str("</p>");
    }
    html.push_str("</section>");
    html
}

/// Pass a request to another committee: the job that carried it is withdrawn, and a new one opens
/// for that committee's first two people. The caller holds [`COMMITMENT_LOCK`].
pub(crate) async fn pass_request(
    s: &RestState, commitment_id: &str, party_id: &str, to_committee_id: &str, via: AckVia, digest: Option<String>,
) -> Result<serde_json::Value, ApiError> {
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let party_id = state.invites.canonical_id(party_id);
    let c = projected_commitment(&state, commitment_id)?;
    let named = c.owner.party_id == party_id || c.backup.party_id == party_id
        || lead_parties(&state, &c).iter().any(|p| p.party_id == party_id) || party_id == s.sovereign_lct_id.to_string();
    if !named {
        return Err(ApiError { status: StatusCode::FORBIDDEN, message: "you're no longer named on this".into() });
    }
    let r = state.chapter.request_of_commitment(&c.commitment_id)
        .ok_or_else(|| ApiError::bad_request("this isn't an inbound request"))?.clone();
    let to = state.chapter.committees.get(to_committee_id).filter(|k| !k.retired)
        .ok_or_else(|| ApiError::bad_request("no such committee"))?;
    let (owner, backup) = to.intake_pair()
        .ok_or_else(|| ApiError::bad_request(format!("{} needs two people before it can take requests", to.name)))?;
    let (owner, backup) = (canonical(&state, &owner), canonical(&state, &backup));
    let new_id = Uuid::new_v4().to_string();
    let passed = HubEvent::RequestPassed {
        request_id: r.request_id.clone(), from_commitment_id: c.commitment_id.clone(),
        to_committee_id: to.committee_id.clone(), to_commitment_id: new_id.clone(),
        by: party_id.clone(), via, link_digest: digest.clone(),
    };
    // Check the pass before writing anything, so a refused pass leaves the job where it was.
    ch::check(&state.chapter, &passed).map_err(ch_refused)?;
    witness_resolution(s, &c, ResolveBody { outcome: Outcome::Withdrawn, by: party_id.clone() }, digest).await?;
    checked_witness(s, HubEvent::CommitmentOpened {
        commitment_id: new_id.clone(),
        title: c.title.clone(),
        owner,
        backup,
        leads_role: ch::committee_role(&to.committee_id),
        ladder: request_ladder(),
        due_at: None,
        recorded_by: s.sovereign_lct_id,
        basis: Basis::NamedByOther,
        group: Some(ch::request_group(&r.request_id)),
    }).await?;
    let index = chapter_witness(s, passed).await?;
    Ok(serde_json::json!({ "passed": true, "to": to.name, "commitment_id": new_id, "entry_index": index }))
}

/// `POST /c/:token/pass/:committee_id` — pass an inbound request on, from its job link.
///
/// surface: chapter_pass_request   act: move a request to another committee
/// S: low/reversible [construct: the new committee can pass it back]
/// R: weak (possession of the job link) [construct: read_link]
/// W: pass [construct: owner, backup or a lead of the job, re-derived under COMMITMENT_LOCK]
/// O: pass [construct: the pass is checked before the withdrawal is written]
/// A: pass [construct: RequestPassed and the withdrawal both carry the link's digest]
/// V: n/a (reversible)
/// verdict: PASS
pub(crate) async fn link_pass(
    State(s): State<RestState>, Path((token, committee_id)): Path<(String, String)>,
) -> axum::response::Response {
    let claim = match verified_link(&s, &token) {
        Ok(claim) => claim,
        Err(page) => return page,
    };
    let _serial = COMMITMENT_LOCK.lock().await;
    match pass_request(&s, &claim.commitment_id, &claim.party_id, &committee_id, AckVia::Link, Some(claim.digest.clone())).await {
        Ok(v) => link_page_response(StatusCode::OK, "Passed", &format!(
            "<h1>Passed to {}. They'll get an email.</h1>", esc(v["to"].as_str().unwrap_or("them")))),
        Err(e) => {
            let msg = if e.status.is_server_error() { "That didn't save just now. Please try again later.".to_string() } else { e.message };
            link_page_response(StatusCode::CONFLICT, "Not passed", &format!("<h1>Not passed</h1><p>{}</p>", esc(&msg)))
        }
    }
}

// ---------------------------------------------------------------------------------------------
// Operator routes: committees, intake, planning, notices
// ---------------------------------------------------------------------------------------------

#[derive(Deserialize)]
pub(crate) struct CommitteeBody {
    #[serde(default)]
    committee_id: Option<String>,
    name: String,
    #[serde(default)]
    purpose: String,
    leads: Vec<PartyRef>,
    #[serde(default)]
    members: Vec<PartyRef>,
    #[serde(default)]
    inbox: bool,
    #[serde(default)]
    retired: bool,
}

/// `POST /admin/api/chapter/committees` — create a committee, or replace one whole (with its id).
///
/// surface: admin_committee_set   act: record a committee's name, leads and members
/// S: low/reversible [construct: the next set replaces it; retired ends it]
/// R: pass [construct: require_loopback]   W: pass [construct: operator plane; every party checked]
/// O: pass [construct: COMMITMENT_LOCK; chapter::check before witness_event]
/// A: pass [construct: CommitteeSet carries set_by]
/// V: n/a (reversible)
/// verdict: PASS
pub(crate) async fn admin_committee_set(
    State(s): State<RestState>, ConnectInfo(peer): ConnectInfo<SocketAddr>, Json(body): Json<CommitteeBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let _serial = COMMITMENT_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let book = load_book(&s)?;
    for p in body.leads.iter().chain(body.members.iter()) {
        check_party(&state, &book, p, "committee")?;
    }
    let committee_id = body.committee_id.unwrap_or_else(ch::new_id);
    let index = chapter_witness(&s, HubEvent::CommitteeSet {
        committee_id: committee_id.clone(),
        name: body.name.trim().to_string(),
        purpose: body.purpose.trim().to_string(),
        leads: body.leads,
        members: body.members,
        inbox: body.inbox,
        retired: body.retired,
        set_by: s.sovereign_lct_id,
    }).await?;
    Ok(Json(serde_json::json!({ "set": true, "committee_id": committee_id, "entry_index": index })))
}

/// `GET /admin/api/chapter` — committees, events and requests, with names, for the operator.
pub(crate) async fn admin_chapter(
    State(s): State<RestState>, ConnectInfo(peer): ConnectInfo<SocketAddr>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let book = load_book(&s)?;
    let pv = |p: &PartyRef| party_view(&state, &book, &canonical(&state, p));
    let committees: Vec<serde_json::Value> = state.chapter.committees.values().map(|k| serde_json::json!({
        "committee_id": k.committee_id, "name": k.name, "purpose": k.purpose, "inbox": k.inbox, "retired": k.retired,
        "leads": k.leads.iter().map(pv).collect::<Vec<_>>(), "members": k.members.iter().map(pv).collect::<Vec<_>>(),
    })).collect();
    let events: Vec<serde_json::Value> = state.chapter.events.values().map(|e| serde_json::json!({
        "event_id": e.event_id, "title": e.title, "starts_at": e.starts_at, "committee_id": e.committee_id,
        "owner": pv(&e.owner), "backup": pv(&e.backup), "closed": e.closed.is_some(),
        "items": items_of_event(&state, &e.event_id).iter().map(|c| serde_json::json!({
            "commitment_id": c.commitment_id, "title": c.title, "status": job_status(&state, &book, c) })).collect::<Vec<_>>(),
    })).collect();
    let requests: Vec<serde_json::Value> = state.chapter.requests.values().map(|r| serde_json::json!({
        "request_id": r.request_id, "committee_id": r.committee_id, "commitment_id": r.commitment_id,
        "received_at": r.received_at, "passes": r.passes.len(),
    })).collect();
    Ok(Json(serde_json::json!({ "committees": committees, "events": events, "requests": requests })))
}

/// `GET /admin/api/chapter/home-link/:party_id` — the operator's copy of one person's chapter page
/// link, to hand over in person or paste into a first email.
pub(crate) async fn admin_home_link(
    State(s): State<RestState>, ConnectInfo(peer): ConnectInfo<SocketAddr>, Path(party_id): Path<String>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let base = link_base().ok_or_else(|| ApiError::bad_request("set HUB_PUBLIC_BASE_URL first"))?;
    let _serial = COMMITMENT_LOCK.lock().await;
    let key = link_key_or_create(&s.paths.root).map_err(ApiError::internal)?;
    Ok(Json(serde_json::json!({ "link": home_url(&base, &key, &party_id, Utc::now()) })))
}

#[derive(Deserialize)]
pub(crate) struct IntakeBody {
    pub message_id: String,
    #[serde(default)]
    pub from_name: String,
    pub from_address: String,
    #[serde(default)]
    pub subject: String,
    #[serde(default)]
    pub text: String,
    #[serde(default)]
    pub received_at: Option<DateTime<Utc>>,
}

/// `POST /admin/api/chapter/intake` — one inbound email, from the intake carrier. It becomes a
/// job for the committee that answers the chapter's address: its first two people are owner and
/// backup, and its leads are the last step. The same message twice opens one job.
///
/// surface: admin_chapter_intake   act: turn an inbound email into a job
/// S: low/reversible [construct: a commitment; the owner can close it or pass it on]
/// R: pass [construct: require_loopback; the carrier runs as the operator]
/// W: pass [construct: operator plane]
/// O: pass [construct: COMMITMENT_LOCK; dedup by Message-ID in the intake file before any witness]
/// A: pass [construct: RequestReceived; the sender and text stay in the 0600 intake file (C3)]
/// V: present [construct: the intake file entry is erasable; the ledger keeps the subject line only]
/// verdict: PASS
pub(crate) async fn admin_intake(
    State(s): State<RestState>, ConnectInfo(peer): ConnectInfo<SocketAddr>, Json(body): Json<IntakeBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    intake(&s, body).await.map(Json)
}

fn clip(s: &str, n: usize) -> String {
    let t: String = s.chars().filter(|c| !c.is_control() || *c == '\n').take(n).collect();
    t.trim().to_string()
}

pub(crate) async fn intake(s: &RestState, body: IntakeBody) -> Result<serde_json::Value, ApiError> {
    let message_id = body.message_id.trim().to_string();
    if message_id.is_empty() || message_id.len() > 300 {
        return Err(ApiError::bad_request("message_id is required"));
    }
    let from_address = check_address(&body.from_address)?;
    let _serial = COMMITMENT_LOCK.lock().await;
    let mut file = load_intake(&s.paths.root)?;
    if let Some((rid, _)) = file.requests.iter().find(|(_, m)| m.message_id == message_id) {
        return Ok(serde_json::json!({ "received": true, "duplicate": true, "request_id": rid }));
    }
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let inbox = state.chapter.inbox()
        .ok_or_else(|| ApiError::bad_request("no committee answers the chapter's address yet"))?;
    let (owner, backup) = inbox.intake_pair()
        .ok_or_else(|| ApiError::bad_request("the inbox committee needs two people"))?;
    let subject = clip(body.subject.lines().next().unwrap_or(""), MAX_SUBJECT_CHARS);
    let subject = if subject.is_empty() { "(no subject)".to_string() } else { subject };
    let request_id = ch::new_id();
    let commitment_id = Uuid::new_v4().to_string();
    let title: String = format!("Email: {subject}").chars().take(commitments::MAX_TITLE_LEN).collect();
    let received_at = body.received_at.unwrap_or_else(Utc::now);
    // The message goes to the intake file first: a job whose message is missing is worse than a
    // stored message whose job failed to open (the carrier retries; dedup finds the message).
    file.requests.insert(request_id.clone(), IntakeMessage {
        message_id,
        from_name: clip(&body.from_name, 80),
        from_address,
        subject,
        excerpt: clip(&body.text, MAX_EXCERPT_CHARS),
        received_at,
    });
    save_intake(&s.paths.root, &file)?;
    checked_witness(s, HubEvent::CommitmentOpened {
        commitment_id: commitment_id.clone(),
        title,
        owner: canonical(&state, &owner),
        backup: canonical(&state, &backup),
        leads_role: ch::committee_role(&inbox.committee_id),
        ladder: request_ladder(),
        due_at: None,
        recorded_by: s.sovereign_lct_id,
        basis: Basis::NamedByOther,
        group: Some(ch::request_group(&request_id)),
    }).await?;
    let index = chapter_witness(s, HubEvent::RequestReceived {
        request_id: request_id.clone(), commitment_id: commitment_id.clone(),
        committee_id: inbox.committee_id.clone(), channel: "email".into(), received_at,
    }).await?;
    Ok(serde_json::json!({ "received": true, "request_id": request_id, "commitment_id": commitment_id, "entry_index": index }))
}

/// `POST /admin/api/chapter/events` — the operator plans an event on a lead's behalf.
pub(crate) async fn admin_plan_event(
    State(s): State<RestState>, ConnectInfo(peer): ConnectInfo<SocketAddr>, Json(body): Json<PlanBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let _serial = COMMITMENT_LOCK.lock().await;
    let by = s.sovereign_lct_id.to_string();
    plan_event(&s, body, &by, AckVia::Operator, None, true).await.map(Json)
}

/// The notices owed now: one welcome per chapter person, one "you're on this event" per owner and
/// backup the planner didn't name themselves, and one recap per committee person when an event
/// closes. Each is sent once; a failure is retried up to [`NOTICE_MAX_ATTEMPTS`] times.
pub(crate) fn due_notices(
    s: &RestState, state: &HubState, book: &ContactBook, file: &NoticeFile, base: Option<&str>, key: Option<&[u8; 32]>,
    now: DateTime<Utc>,
) -> Vec<serde_json::Value> {
    let mut out = Vec::new();
    let home = |party: &str| match (base, key) {
        (Some(b), Some(k)) => format!("\n\nYour chapter page: {}", home_url(b, k, party, now)),
        _ => String::new(),
    };
    let mut push = |id: String, p: &PartyRef, subject: String, body: String| {
        if file.sent.contains(&id) || file.failures.get(&id).copied().unwrap_or(0) >= NOTICE_MAX_ATTEMPTS {
            return;
        }
        let Some(address) = book.address_of(p) else { return };
        out.push(serde_json::json!({ "notice_id": id, "party_id": p.party_id, "address": address,
            "subject": subject, "body": format!("{body}{}", home(&p.party_id)) }));
    };
    let chapter = &s.hub_name;
    for p in chapter_people(state) {
        if !file.invited.contains(&p.party_id) {
            continue;
        }
        let who = first_name(&name_of(state, book, &p));
        let roles: Vec<String> = state.chapter.live_committees().filter(|k| committee_people(state, k).iter().any(|q| q.party_id == p.party_id))
            .map(|k| if is_lead_of(state, k, &p.party_id) { format!("{} (lead)", k.name) } else { k.name.clone() }).collect();
        push(format!("welcome:{}", p.party_id), &p, format!("{chapter}: who owns what, from now on"), format!(
            "Hi {who},\n\n{chapter} now keeps track of who owns what, so nothing gets dropped. You're on: {}.\n\n\
             How it works: when something is yours, you get one email with a link where you can say yes, mark it \
             done, or hand it to your backup. Every job has a backup. If something goes quiet, it goes to the backup, then to the committee \
             leads. You don't need to log in or install anything; keep using email and Slack as you do now.\n\n\
             Your chapter page shows what needs you, upcoming events, and who does what.{}",
            roles.join(", "),
            match (base, key) {
                (Some(b), Some(k)) => format!("\n\nNot for you? One click takes you off: {}/leave",
                    home_url(b, k, &p.party_id, now)),
                _ => String::new(),
            }));
    }
    for e in state.chapter.events.values() {
        let planner = state.invites.canonical_id(&e.planned_by);
        let items: Vec<String> = items_of_event(state, &e.event_id).iter()
            .map(|c| c.title.rsplit(": ").next().unwrap_or(&c.title).to_string()).collect();
        let by = first_name(&name_by_id(state, book, &planner));
        let owner = canonical(state, &e.owner);
        let backup = canonical(state, &e.backup);
        let _ = &items;
        // One email per person per event, listing every step they own or back up.
        let event_items = items_of_event(state, &e.event_id);
        let mut people: Vec<PartyRef> = vec![owner.clone(), backup.clone()];
        for c in &event_items {
            for p in [&c.owner, &c.backup] {
                if !people.iter().any(|q| q.party_id == p.party_id) {
                    people.push(p.clone());
                }
            }
        }
        for p in people {
            if p.party_id == planner {
                continue;
            }
            let short = |c: &&Commitment| c.title.rsplit(": ").next().unwrap_or(&c.title).to_string();
            let owns: Vec<String> = event_items.iter().filter(|c| c.owner.party_id == p.party_id)
                .map(|c| match target_of(c) { Some(d) => format!("{} (by {})", short(c), local_day(d)), None => short(c) }).collect();
            let backs: Vec<String> = event_items.iter().filter(|c| c.backup.party_id == p.party_id).map(short).collect();
            let role = if p.party_id == owner.party_id {
                format!("and put you down as the event's owner, with {} as backup", first_name(&name_of(state, book, &backup)))
            } else if p.party_id == backup.party_id {
                format!("with {} as owner and you as backup", first_name(&name_of(state, book, &owner)))
            } else {
                format!("run by {}", first_name(&name_of(state, book, &owner)))
            };
            let mut body = format!("{by} planned {} for {}, {role}.\n", e.title, local_time(e.starts_at));
            if !owns.is_empty() {
                body.push_str(&format!("\nYours: {}.\n", owns.join(", ")));
            }
            if !backs.is_empty() {
                body.push_str(&format!("\nYou're the backup on: {}.\n", backs.join(", ")));
            }
            body.push_str("\nThere's nothing to answer now. You'll get a reminder only if a date passes and the step isn't \
                marked done.");
            let subject = if owns.is_empty() { format!("{}: you're a backup", e.title) } else { format!("{}: what's yours", e.title) };
            push(format!("planned:{}:{}", e.event_id, p.party_id), &p, subject, body);
        }
        if let Some(cl) = &e.closed {
            let mut lines = Vec::new();
            for c in items_of_event(state, &e.event_id) {
                let short = c.title.rsplit(": ").next().unwrap_or(&c.title).to_string();
                let story: Vec<String> = job_story(state, book, c).into_iter().map(|(_, _, l)| l).collect();
                lines.push(format!("- {short}: {}", story.join(" ")));
            }
            let closer = first_name(&name_by_id(state, book, &cl.by));
            let mut to = state.chapter.committees.get(&e.committee_id).map(|k| committee_people(state, k)).unwrap_or_default();
            for p in [owner.clone(), backup.clone()] {
                if !to.iter().any(|q| q.party_id == p.party_id) {
                    to.push(p);
                }
            }
            for p in to {
                push(format!("recap:{}:{}", e.event_id, p.party_id), &p, format!("{}: what happened", e.title), format!(
                    "{} on {} is finished; {closer} closed it.\n\nWhat happened:\n{}", e.title, local_day(e.starts_at),
                    lines.join("\n")));
            }
        }
    }
    out
}

#[derive(Deserialize)]
pub(crate) struct InviteBody {
    party_ids: Vec<String>,
}

/// `POST /admin/api/chapter/invite` — the operator invites people (at setup: the chapter leads),
/// so their welcome goes out. Everyone else is invited by a chapter lead from their own page.
pub(crate) async fn admin_invite(
    State(s): State<RestState>, ConnectInfo(peer): ConnectInfo<SocketAddr>, Json(body): Json<InviteBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let _serial = COMMITMENT_LOCK.lock().await;
    invite(&s, &body.party_ids)?;
    Ok(Json(serde_json::json!({ "invited": body.party_ids.len() })))
}

/// `GET /admin/api/chapter/notices` — what the carrier should send besides nudges.
pub(crate) async fn admin_notices_due(
    State(s): State<RestState>, ConnectInfo(peer): ConnectInfo<SocketAddr>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let book = load_book(&s)?;
    let file = load_notices(&s.paths.root)?;
    let base = link_base();
    let key = if base.is_some() {
        let _serial = COMMITMENT_LOCK.lock().await;
        Some(link_key_or_create(&s.paths.root).map_err(ApiError::internal)?)
    } else {
        None
    };
    let rows = due_notices(&s, &state, &book, &file, base.as_deref(), key.as_ref(), Utc::now());
    Ok(Json(serde_json::json!({ "notices": rows })))
}

#[derive(Deserialize)]
pub(crate) struct NoticeSentBody {
    notice_id: String,
    ok: bool,
}

/// `POST /admin/api/chapter/notices/sent` — the carrier's report of one notice. Off the ledger: a
/// notice moves no job, and its id names the party only as the opaque id it already is.
pub(crate) async fn admin_notice_sent(
    State(s): State<RestState>, ConnectInfo(peer): ConnectInfo<SocketAddr>, Json(body): Json<NoticeSentBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let _serial = COMMITMENT_LOCK.lock().await;
    let mut file = load_notices(&s.paths.root)?;
    if body.ok {
        file.sent.insert(body.notice_id.clone());
        file.failures.remove(&body.notice_id);
    } else {
        *file.failures.entry(body.notice_id.clone()).or_insert(0) += 1;
    }
    save_notices(&s.paths.root, &file)?;
    Ok(Json(serde_json::json!({ "recorded": true })))
}


// ---------------------------------------------------------------------------------------------
// The roster, run by the chapter itself: chapter leads add, move and invite people; a committee
// lead adds people to their own committee; anyone can leave. No operator in the loop.
// ---------------------------------------------------------------------------------------------

/// A chapter lead leads the committee that answers the chapter's email.
pub(crate) fn is_chapter_lead(state: &HubState, party_id: &str) -> bool {
    state.chapter.inbox().is_some_and(|k| is_lead_of(state, k, party_id))
}

/// Replace a committee whole, keeping its name, purpose and inbox mark. The caller holds
/// [`COMMITMENT_LOCK`].
async fn reset_committee(s: &RestState, k: &Committee, leads: Vec<PartyRef>, members: Vec<PartyRef>) -> Result<u64, ApiError> {
    chapter_witness(s, HubEvent::CommitteeSet {
        committee_id: k.committee_id.clone(),
        name: k.name.clone(),
        purpose: k.purpose.clone(),
        leads,
        members,
        inbox: k.inbox,
        retired: false,
        set_by: s.sovereign_lct_id,
    }).await
}

fn without(list: &[PartyRef], state: &HubState, party_id: &str) -> Vec<PartyRef> {
    list.iter().map(|p| canonical(state, p)).filter(|p| p.party_id != party_id).collect()
}

/// Invite people: their welcome goes out on the carrier's next pass. The caller holds the lock.
fn invite(s: &RestState, ids: &[String]) -> Result<(), ApiError> {
    let mut file = load_notices(&s.paths.root)?;
    for id in ids {
        file.invited.insert(id.clone());
    }
    save_notices(&s.paths.root, &file)
}

/// Add someone to a committee: a new contact, or the one already in the book at that address.
/// Returns their party.
pub(crate) async fn add_person(
    s: &RestState, me: &str, name: &str, email: &str, committee_id: &str, as_lead: bool, operator: bool,
) -> Result<PartyRef, ApiError> {
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let k = state.chapter.committees.get(committee_id).filter(|k| !k.retired)
        .ok_or_else(|| ApiError::bad_request("pick a committee from the list"))?.clone();
    let chapter_lead = operator || is_chapter_lead(&state, me);
    if !chapter_lead && !is_lead_of(&state, &k, me) {
        return Err(ApiError { status: StatusCode::FORBIDDEN, message: format!("only a lead of {} can add people to it", k.name) });
    }
    if as_lead && !chapter_lead {
        return Err(ApiError { status: StatusCode::FORBIDDEN, message: "only a chapter lead can make someone a lead".into() });
    }
    let address = check_address(email)?;
    let name = name.trim();
    if name.is_empty() || name.chars().count() > MAX_CONTACT_NAME_LEN || name.chars().any(char::is_control) {
        return Err(ApiError::bad_request("give their name (up to 64 characters)"));
    }
    let mut book = load_book(s)?;
    let existing = book.contacts.iter().find(|(_, c)| c.address.eq_ignore_ascii_case(&address)).map(|(id, _)| id.clone());
    let party_id = match existing {
        Some(id) => id,
        None => {
            let id = Uuid::new_v4().to_string();
            book.contacts.insert(id.clone(), Contact { name: name.to_string(), address, added_at: Utc::now() });
            book.save(&book_path(s)).map_err(ApiError::internal)?;
            id
        }
    };
    let person = canonical(&state, &PartyRef { party_id: party_id.clone(), kind: PartyKind::Contact });
    let mut leads = without(&k.leads, &state, &person.party_id);
    let mut members = without(&k.members, &state, &person.party_id);
    let was_lead = is_lead_of(&state, &k, &person.party_id);
    if as_lead || was_lead {
        leads.push(person.clone());
    } else {
        members.push(person.clone());
    }
    reset_committee(s, &k, leads, members).await?;
    invite(s, &[person.party_id.clone()])?;
    Ok(person)
}

/// A chapter lead sets someone's place on one committee: lead, member, or not on it.
pub(crate) async fn set_place(
    s: &RestState, me: &str, party_id: &str, committee_id: &str, place: &str, operator: bool,
) -> Result<(), ApiError> {
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    if !operator && !is_chapter_lead(&state, me) {
        return Err(ApiError { status: StatusCode::FORBIDDEN, message: "only a chapter lead can move people".into() });
    }
    let person = known_party(&state, party_id, "person")?;
    let k = state.chapter.committees.get(committee_id).filter(|k| !k.retired)
        .ok_or_else(|| ApiError::bad_request("pick a committee from the list"))?.clone();
    let mut leads = without(&k.leads, &state, &person.party_id);
    let mut members = without(&k.members, &state, &person.party_id);
    match place {
        "lead" => leads.push(person),
        "member" => members.push(person),
        "out" => {}
        _ => return Err(ApiError::bad_request("choose lead, member or off")),
    }
    if leads.is_empty() {
        return Err(ApiError::bad_request(format!("{} needs a lead: make someone else lead first", k.name)));
    }
    reset_committee(s, &k, leads, members).await.map(|_| ())
}

/// A chapter lead starts a committee, with its first lead.
pub(crate) async fn add_committee(
    s: &RestState, me: &str, name: &str, purpose: &str, lead: &str, operator: bool,
) -> Result<String, ApiError> {
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    if !operator && !is_chapter_lead(&state, me) {
        return Err(ApiError { status: StatusCode::FORBIDDEN, message: "only a chapter lead can start a committee".into() });
    }
    let name = name.trim();
    if name.is_empty() || name.chars().count() > ch::MAX_COMMITTEE_NAME_LEN || name.chars().any(char::is_control) {
        return Err(ApiError::bad_request(format!(
            "give the committee a name (up to {} characters)", ch::MAX_COMMITTEE_NAME_LEN)));
    }
    let purpose = purpose.trim();
    if purpose.chars().count() > ch::MAX_PURPOSE_LEN || purpose.chars().any(char::is_control) {
        return Err(ApiError::bad_request(format!("keep the purpose to one line (up to {} characters)", ch::MAX_PURPOSE_LEN)));
    }
    let lead = known_party(&state, lead, "lead")?;
    let committee_id = ch::new_id();
    chapter_witness(s, HubEvent::CommitteeSet {
        committee_id: committee_id.clone(), name: name.to_string(), purpose: purpose.to_string(),
        leads: vec![lead], members: Vec::new(), inbox: false, retired: false, set_by: s.sovereign_lct_id,
    }).await?;
    Ok(committee_id)
}

/// Someone leaves: off every committee, and their name and address erased. A committee they led
/// alone falls to the chapter leads until someone takes it. Jobs in their name stay, and go to
/// their backups when they go quiet.
///
/// Every refusal is decided before anything is written: either the person comes off every
/// committee, or nothing changes and the page says why.
pub(crate) async fn leave(s: &RestState, me: &str) -> Result<(), ApiError> {
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let other_chapter_leads: Vec<PartyRef> = state.chapter.inbox()
        .map(|k| without(&k.leads, &state, me)).unwrap_or_default();
    if is_chapter_lead(&state, me) && other_chapter_leads.is_empty() {
        return Err(ApiError::bad_request(
            "you're the last chapter lead: make someone else a chapter lead first, so the chapter's email still has an owner. Nothing was changed."));
    }
    let mut plan: Vec<(&Committee, Vec<PartyRef>, Vec<PartyRef>)> = Vec::new();
    for k in state.chapter.live_committees().filter(|k| committee_people(&state, k).iter().any(|p| p.party_id == me)) {
        let mut leads = without(&k.leads, &state, me);
        let mut members = without(&k.members, &state, me);
        if leads.is_empty() {
            // A committee they led alone falls to the chapter leads (as leads, not twice over).
            leads = other_chapter_leads.clone();
            members.retain(|m| !leads.iter().any(|l| l.party_id == m.party_id));
        }
        if leads.is_empty() {
            return Err(ApiError::bad_request(format!(
                "{} needs a lead: make someone else lead first. Nothing was changed.", k.name)));
        }
        plan.push((k, leads, members));
    }
    for (k, leads, members) in plan {
        reset_committee(s, k, leads, members).await?;
    }
    let mut book = load_book(s)?;
    let contact_id = state.invites.contact_of(me).map(str::to_string).unwrap_or_else(|| me.to_string());
    if book.contacts.remove(&contact_id).is_some() {
        book.save(&book_path(s)).map_err(ApiError::internal)?;
    }
    let mut file = load_notices(&s.paths.root)?;
    file.invited.remove(me);
    save_notices(&s.paths.root, &file)
}

/// The "Give it to someone else" control on a job page, for its owner or a lead.
pub(crate) fn give_form(state: &HubState, book: &ContactBook, c: &Commitment, token: &str) -> String {
    let people: Vec<PartyRef> = chapter_people(state).into_iter().filter(|p| p.party_id != c.owner.party_id).collect();
    if people.is_empty() || !c.is_open() {
        return String::new();
    }
    format!("<details><summary>Give it to someone else</summary><form method=\"post\" action=\"/g/{}\" class=\"stack\">\
        <label>Who<select name=\"to\">{}</select></label><button>Give it to them</button>\
        <p class=\"muted\">They get an email, and {} stays the backup.</p></form></details>",
        esc(token), options(state, book, &people, None), esc(&first_name(&name_of(state, book, &c.backup))))
}

/// `POST /g/:token` — the owner or a lead gives the job to anyone in the chapter.
///
/// surface: chapter_give   act: hand a job to a named person, from its link
/// S: low/reversible [construct: a handoff; the new owner can hand it on]
/// R: weak (possession of the job link) [construct: read_link]
/// W: pass [construct: owner or a lead only, re-derived under COMMITMENT_LOCK; the recipient must be in the chapter]
/// O: pass [construct: commitments::check before witness]   A: pass [construct: via=link + digest]
/// V: n/a (reversible)
/// verdict: PASS
pub(crate) async fn link_give(
    State(s): State<RestState>, Path(token): Path<String>,
    axum::extract::Form(form): axum::extract::Form<std::collections::HashMap<String, String>>,
) -> axum::response::Response {
    let claim = match verified_link(&s, &token) {
        Ok(claim) => claim,
        Err(page) => return page,
    };
    let _serial = COMMITMENT_LOCK.lock().await;
    let r: Result<String, ApiError> = async {
        let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
        let me = state.invites.canonical_id(&claim.party_id);
        let c = projected_commitment(&state, &claim.commitment_id)?;
        if !matches!(role_of(&state, &c, &me), Some(LinkRole::Owner | LinkRole::Lead)) {
            return Err(ApiError { status: StatusCode::FORBIDDEN, message: "only its owner or a lead can give it away".into() });
        }
        let to = known_party(&state, &form_field(&form, "to"), "person")?;
        if to.party_id == c.owner.party_id {
            return Err(ApiError::bad_request("it's already theirs"));
        }
        let name = name_of(&state, &load_book(&s).unwrap_or_default(), &to);
        witness_move(&s, &c, MoveBody { by: me, move_kind: MoveKind::Handoff, to: Some(to), note_ref: None },
            AckVia::Link, Some(claim.digest.clone())).await?;
        Ok(name)
    }.await;
    let back = format!("<p><a href=\"/c/{}\">Back to the job</a></p>", esc(&token));
    match r {
        Ok(name) => link_page_response(StatusCode::OK, "Given", &format!("<h1>It's {}'s now. They'll get an email.</h1>{back}",
            esc(&first_name(&name)))),
        Err(e) => {
            let msg = if e.status.is_server_error() { "That didn't save just now. Please try again later.".to_string() } else { e.message };
            link_page_response(StatusCode::CONFLICT, "Not given", &format!("<h1>Not given</h1><p>{}</p>{back}", esc(&msg)))
        }
    }
}

async fn home_form<F, Fut>(s: RestState, token: String, f: F) -> axum::response::Response
where
    F: FnOnce(RestState, String) -> Fut,
    Fut: std::future::Future<Output = Result<String, ApiError>>,
{
    let claim = match verified_home(&s, &token) {
        Ok(c) => c,
        Err(page) => return page,
    };
    let _serial = COMMITMENT_LOCK.lock().await;
    let me = { let ledger = s.ledger.lock().await; s.projected(&ledger).invites.canonical_id(&claim.party_id) };
    match f(s.clone(), me).await {
        Ok(msg) => form_page(StatusCode::OK, "Saved", &claim.token, &msg),
        Err(e) => api_error_page(&claim.token, e),
    }
}

/// `POST /h/:token/people/add` — add someone (a chapter lead: to any committee, as lead or member;
/// a committee lead: to their own committee). They're invited, so their welcome goes out.
pub(crate) async fn home_people_add(
    State(s): State<RestState>, Path(token): Path<String>,
    axum::extract::Form(form): axum::extract::Form<std::collections::HashMap<String, String>>,
) -> axum::response::Response {
    home_form(s, token, |s, me| async move {
        let p = add_person(&s, &me, &form_field(&form, "name"), &form_field(&form, "email"),
            &form_field(&form, "committee_id"), form.contains_key("lead"), false).await?;
        let _ = p;
        Ok(format!("Added {}. They'll get a welcome email with their own chapter page.", form_field(&form, "name").trim()))
    }).await
}

/// `POST /h/:token/people/set` — a chapter lead sets someone's place on a committee.
pub(crate) async fn home_people_set(
    State(s): State<RestState>, Path(token): Path<String>,
    axum::extract::Form(form): axum::extract::Form<std::collections::HashMap<String, String>>,
) -> axum::response::Response {
    home_form(s, token, |s, me| async move {
        set_place(&s, &me, &form_field(&form, "party_id"), &form_field(&form, "committee_id"),
            &form_field(&form, "place"), false).await?;
        Ok("Saved.".to_string())
    }).await
}

/// `POST /h/:token/committees/add` — a chapter lead starts a committee.
pub(crate) async fn home_committee_add(
    State(s): State<RestState>, Path(token): Path<String>,
    axum::extract::Form(form): axum::extract::Form<std::collections::HashMap<String, String>>,
) -> axum::response::Response {
    home_form(s, token, |s, me| async move {
        add_committee(&s, &me, &form_field(&form, "name"), &form_field(&form, "purpose"), &form_field(&form, "lead"), false).await?;
        Ok(format!("{} is set up.", form_field(&form, "name").trim()))
    }).await
}

/// `POST /h/:token/invite` — a chapter lead sends the welcome to everyone not yet invited.
pub(crate) async fn home_invite_all(State(s): State<RestState>, Path(token): Path<String>) -> axum::response::Response {
    home_form(s, token, |s, me| async move {
        let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
        if !is_chapter_lead(&state, &me) {
            return Err(ApiError { status: StatusCode::FORBIDDEN, message: "only a chapter lead can invite everyone".into() });
        }
        let file = load_notices(&s.paths.root)?;
        let ids: Vec<String> = chapter_people(&state).into_iter().map(|p| p.party_id).filter(|id| !file.invited.contains(id)).collect();
        invite(&s, &ids)?;
        Ok(format!("Invited {}. Their welcome emails go out within a few minutes.", ids.len()))
    }).await
}

/// `GET /h/:token/leave` — the confirm page a welcome links to.
pub(crate) async fn leave_page(State(s): State<RestState>, Path(token): Path<String>) -> axum::response::Response {
    if let Err(page) = verified_home(&s, &token) {
        return page;
    }
    link_page_response(StatusCode::OK, "Leave", &format!(
        "<h1>Take yourself off?</h1><p>You'll be removed from every committee and your name and email erased here. \
         You won't get more email from it.</p><form method=\"post\" action=\"/h/{}/leave\"><button>Yes, take me off</button></form>\
         <p><a href=\"/h/{}\">No, keep me on</a></p>", esc(&token), esc(&token)))
}

/// `POST /h/:token/leave` — leave the chapter's tool.
pub(crate) async fn leave_act(State(s): State<RestState>, Path(token): Path<String>) -> axum::response::Response {
    let claim = match verified_home(&s, &token) {
        Ok(c) => c,
        Err(page) => return page,
    };
    let _serial = COMMITMENT_LOCK.lock().await;
    let me = { let ledger = s.ledger.lock().await; s.projected(&ledger).invites.canonical_id(&claim.party_id) };
    match leave(&s, &me).await {
        Ok(()) => link_page_response(StatusCode::OK, "Done", "<h1>Done. You're off, and you won't hear from it again.</h1>"),
        Err(e) => api_error_page(&claim.token, e),
    }
}

/// The roster controls on a chapter page: what a chapter lead or a committee lead can change.
fn roster_html(state: &HubState, book: &ContactBook, token: &str, me: &str, invited: &BTreeSet<String>) -> String {
    let chapter_lead = is_chapter_lead(state, me);
    let mut committees: Vec<&Committee> = state.chapter.live_committees()
        .filter(|k| chapter_lead || is_lead_of(state, k, me)).collect();
    if committees.is_empty() {
        return String::new();
    }
    committees.sort_by_key(|k| (!k.inbox, k.name.to_lowercase()));
    let tok = esc(token);
    let committee_opts: String = committees.iter()
        .map(|k| format!("<option value=\"{}\">{}</option>", esc(&k.committee_id), esc(&k.name))).collect();
    let mut html = format!("<details><summary>Add someone</summary><form method=\"post\" action=\"/h/{tok}/people/add\" class=\"stack\">\
        <label>Name<input name=\"name\" required maxlength=\"64\"></label>\
        <label>Email<input type=\"email\" name=\"email\" required></label>\
        <label>Committee<select name=\"committee_id\">{committee_opts}</select></label>{}\
        <button>Add</button><p class=\"muted\">They get a welcome email with their own page. Nothing else to do.</p>\
        </form></details>",
        if chapter_lead { "<label class=\"check\"><input type=\"checkbox\" name=\"lead\"> as a lead of that committee</label>" } else { "" });
    if !chapter_lead {
        return html;
    }
    let people = chapter_people(state);
    let waiting = people.iter().filter(|p| !invited.contains(&p.party_id)).count();
    if waiting > 0 {
        html.push_str(&format!("<form method=\"post\" action=\"/h/{tok}/invite\"><button class=\"secondary\">Send the welcome to the \
            {waiting} people who haven't had it</button></form>"));
    }
    html.push_str("<details><summary>Move people between committees</summary>");
    for k in &committees {
        html.push_str(&format!("<h3>{}</h3>", esc(&k.name)));
        for p in committee_people(state, k) {
            let place = if is_lead_of(state, k, &p.party_id) { "lead" } else { "member" };
            let opt = |v: &str, label: &str| format!("<option value=\"{v}\"{}>{label}</option>", if v == place { " selected" } else { "" });
            html.push_str(&format!("<form method=\"post\" action=\"/h/{tok}/people/set\" class=\"row\">\
                <input type=\"hidden\" name=\"party_id\" value=\"{}\"><input type=\"hidden\" name=\"committee_id\" value=\"{}\">\
                <span>{}</span><select name=\"place\">{}{}{}</select><button class=\"secondary\">Save</button></form>",
                esc(&p.party_id), esc(&k.committee_id), esc(&name_of(state, book, &p)),
                opt("lead", "lead"), opt("member", "member"), opt("out", "off this committee")));
        }
        let others: Vec<PartyRef> = people.iter().filter(|p| !committee_people(state, k).iter().any(|q| q.party_id == p.party_id))
            .cloned().collect();
        if !others.is_empty() {
            html.push_str(&format!("<form method=\"post\" action=\"/h/{tok}/people/set\" class=\"row\">\
                <input type=\"hidden\" name=\"committee_id\" value=\"{}\"><input type=\"hidden\" name=\"place\" value=\"member\">\
                <select name=\"party_id\">{}</select><button class=\"secondary\">Add to {}</button></form>",
                esc(&k.committee_id), options(state, book, &others, None), esc(&k.name)));
        }
    }
    html.push_str("</details>");
    html.push_str(&format!("<details><summary>Start a committee</summary><form method=\"post\" action=\"/h/{tok}/committees/add\" class=\"stack\">\
        <label>Name<input name=\"name\" required maxlength=\"48\"></label>\
        <label>What it does<input name=\"purpose\" maxlength=\"200\"></label>\
        <label>Lead<select name=\"lead\">{}</select></label><button>Start it</button></form></details>",
        options(state, book, &people, Some(me))));
    html
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rest::channel_e2e_tests::fresh_rest_state;

    async fn contact(s: &RestState, name: &str) -> PartyRef {
        let v = add_contact(s, ContactBody { name: name.into(), address: format!("{}@example.org", name.to_lowercase().replace(' ', ".")) })
            .await.expect("contact");
        PartyRef { party_id: v["party"]["party_id"].as_str().unwrap().into(), kind: PartyKind::Contact }
    }

    async fn committee(s: &RestState, name: &str, leads: Vec<PartyRef>, members: Vec<PartyRef>, inbox: bool) -> String {
        let _serial = COMMITMENT_LOCK.lock().await;
        let id = ch::new_id();
        chapter_witness(s, HubEvent::CommitteeSet { committee_id: id.clone(), name: name.into(), purpose: String::new(),
            leads, members, inbox, retired: false, set_by: s.sovereign_lct_id }).await.expect("committee");
        id
    }

    fn state_of(s: &RestState) -> HubState {
        let ledger = s.ledger.try_lock().expect("ledger");
        s.projected(&ledger)
    }

    #[tokio::test]
    async fn an_email_becomes_a_job_for_the_inbox_committee_and_twice_is_once() {
        let (_dir, s) = fresh_rest_state(None).await;
        let (nat, yem, pat, quinn) = (contact(&s, "Natalie Lead").await, contact(&s, "Yemaya Co").await,
            contact(&s, "Pat Partner").await, contact(&s, "Quinn Q").await);
        committee(&s, "Chapter leads", vec![nat.clone(), yem.clone()], vec![], true).await;
        let partners = committee(&s, "Partnerships", vec![pat.clone()], vec![quinn.clone()], false).await;
        let body = || IntakeBody { message_id: "<abc@example.org>".into(), from_name: "Venue Person".into(),
            from_address: "venue@example.org".into(), subject: "Hosting your January event?".into(),
            text: "We'd love to host.".into(), received_at: None };
        let first = intake(&s, body()).await.expect("intake");
        let again = intake(&s, body()).await.expect("intake again");
        assert_eq!(again["duplicate"], true);
        let state = state_of(&s);
        let c = &state.commitments[first["commitment_id"].as_str().unwrap()];
        assert_eq!((c.owner.party_id.as_str(), c.backup.party_id.as_str()), (nat.party_id.as_str(), yem.party_id.as_str()));
        assert_eq!(c.title, "Email: Hosting your January event?");
        let book = load_book(&s).unwrap();
        let rows = due_nudges(&state, &book, Utc::now(), None);
        assert!(rows.iter().any(|r| r["subject"] == "New email to the chapter: Hosting your January event?"), "{rows:?}");
        assert!(rows.iter().any(|r| r["subject"] == "You're backup on: Hosting your January event?"));
        // The sender is not on the ledger.
        let ledger_text = serde_json::to_string(&state.commitments).unwrap();
        assert!(!ledger_text.contains("venue@example.org"));

        // Natalie passes it to Partnerships: her job is withdrawn, Pat owns a new one, Quinn backs it up.
        let rid = first["request_id"].as_str().unwrap();
        let _serial = COMMITMENT_LOCK.lock().await;
        let passed = pass_request(&s, &c.commitment_id, &nat.party_id, &partners, AckVia::Link, None).await.expect("pass");
        drop(_serial);
        let state = state_of(&s);
        let old = &state.commitments[&c.commitment_id];
        assert_eq!(old.resolved.as_ref().map(|r| r.outcome), Some(Outcome::Withdrawn));
        let new = &state.commitments[passed["commitment_id"].as_str().unwrap()];
        assert_eq!((new.owner.party_id.as_str(), new.backup.party_id.as_str()), (pat.party_id.as_str(), quinn.party_id.as_str()));
        assert_eq!(state.chapter.requests[rid].commitment_id, new.commitment_id);
        // Escalation from Pat's job ends at Partnerships' lead, a contact.
        assert_eq!(lead_parties(&state, new).iter().map(|p| p.party_id.clone()).collect::<Vec<_>>(), vec![pat.party_id.clone()]);
    }

    #[tokio::test]
    async fn a_planned_event_opens_its_checklist_and_mails_owner_and_backup_once() {
        let (_dir, s) = fresh_rest_state(None).await;
        let (ev, al, sam) = (contact(&s, "Eve Events").await, contact(&s, "Alex Owner").await, contact(&s, "Sam Backup").await);
        let events = committee(&s, "Technical Events", vec![ev.clone()], vec![al.clone(), sam.clone()], false).await;
        let date = (Utc::now() + chrono::Duration::days(30)).with_timezone(&chapter_offset()).format("%Y-%m-%d").to_string();
        let _serial = COMMITMENT_LOCK.lock().await;
        let planned = plan_event(&s, PlanBody { title: "December social".into(), date, time: "18:00".into(),
            committee_id: events.clone(), owner: al.party_id.clone(), backup: sam.party_id.clone(), items: None },
            &ev.party_id, AckVia::Link, None, false).await.expect("plan");
        // Someone who doesn't lead the committee can't plan for it.
        let refused = plan_event(&s, PlanBody { title: "Not mine".into(), date: "2099-01-01".into(), time: String::new(),
            committee_id: events.clone(), owner: al.party_id.clone(), backup: sam.party_id.clone(), items: None },
            &al.party_id, AckVia::Link, None, false).await;
        drop(_serial);
        assert_eq!(refused.unwrap_err().status, StatusCode::FORBIDDEN);
        let state = state_of(&s);
        let event_id = planned["event_id"].as_str().unwrap();
        let items = items_of_event(&state, event_id);
        assert_eq!(items.len(), CHECKLIST.len());
        // The venue item aims 21 days out: its owner window is about 9 days from now.
        let venue = items.iter().find(|c| c.title.ends_with("Venue and sponsors confirmed")).unwrap();
        assert!((200..=240).contains(&venue.ladder[0]), "venue window {:?}", venue.ladder);

        // Per-item "you're named" nudges are folded into one notice each for owner and backup.
        let book = load_book(&s).unwrap();
        assert!(due_nudges(&state, &book, Utc::now(), None).iter()
            .all(|n| n["commitment_id"].as_str().map_or(true, |id| !items.iter().any(|c| c.commitment_id == id))));
        let everyone = NoticeFile { invited: chapter_people(&state).into_iter().map(|p| p.party_id).collect(),
            ..Default::default() };
        assert!(due_notices(&s, &state, &book, &NoticeFile::default(), None, None, Utc::now()).iter()
            .all(|n| !n["notice_id"].as_str().unwrap().starts_with("welcome:")), "nobody is welcomed before they're invited");
        let notices = due_notices(&s, &state, &book, &everyone, None, None, Utc::now());
        let ids: Vec<&str> = notices.iter().filter_map(|n| n["notice_id"].as_str()).collect();
        assert!(ids.contains(&format!("planned:{event_id}:{}", al.party_id).as_str()));
        assert!(ids.contains(&format!("planned:{event_id}:{}", sam.party_id).as_str()));
        assert_eq!(ids.iter().filter(|i| i.starts_with("welcome:")).count(), 3);

        // Closing sends the recap to the committee.
        let _serial = COMMITMENT_LOCK.lock().await;
        chapter_witness(&s, HubEvent::ChapterEventClosed { event_id: event_id.into(), by: ev.party_id.clone(),
            via: AckVia::Link, link_digest: None, closed_at: Utc::now() }).await.expect("close");
        drop(_serial);
        let state = state_of(&s);
        let notices = due_notices(&s, &state, &book, &NoticeFile::default(), None, None, Utc::now());
        assert_eq!(notices.iter().filter(|n| n["notice_id"].as_str().unwrap().starts_with("recap:")).count(), 3);
        let recap = notices.iter().find(|n| n["notice_id"].as_str().unwrap().starts_with("recap:")).unwrap();
        assert!(recap["body"].as_str().unwrap().contains("Venue and sponsors confirmed: Given to Alex"));
    }

    #[tokio::test]
    async fn the_chapter_runs_its_own_roster() {
        let (_dir, s) = fresh_rest_state(None).await;
        let (nat, yem, aug) = (contact(&s, "Natalie Co").await, contact(&s, "Yemaya Co").await, contact(&s, "Augustina P").await);
        committee(&s, "Chapter leads", vec![nat.clone(), yem.clone()], vec![], true).await;
        let partners = committee(&s, "Partnerships", vec![aug.clone()], vec![], false).await;
        let _serial = COMMITMENT_LOCK.lock().await;
        // A committee lead adds a member to their own committee, and that person is invited.
        let arne = add_person(&s, &aug.party_id, "Arne W", "arne@example.org", &partners, false, false).await.expect("add");
        assert!(load_notices(&s.paths.root).unwrap().invited.contains(&arne.party_id));
        // ...but can't make anyone a lead; a chapter lead can.
        assert_eq!(add_person(&s, &aug.party_id, "X Y", "xy@example.org", &partners, true, false).await.unwrap_err().status,
            StatusCode::FORBIDDEN);
        set_place(&s, &nat.party_id, &arne.party_id, &partners, "lead", false).await.expect("make lead");
        // The last lead can't be moved off.
        set_place(&s, &nat.party_id, &aug.party_id, &partners, "out", false).await.expect("aug off");
        assert!(set_place(&s, &nat.party_id, &arne.party_id, &partners, "out", false).await.is_err());
        // Arne leaves: off the committee (which falls to the chapter leads), his address erased.
        leave(&s, &arne.party_id).await.expect("leave");
        drop(_serial);
        let state = state_of(&s);
        let k = &state.chapter.committees[&partners];
        assert!(!k.includes(&arne.party_id));
        assert!(k.is_lead(&nat.party_id) && k.is_lead(&yem.party_id));
        assert!(!load_book(&s).unwrap().contacts.contains_key(&arne.party_id));
    }

    #[tokio::test]
    async fn the_last_chapter_lead_cannot_leave_and_nothing_is_written() {
        let (_dir, s) = fresh_rest_state(None).await;
        let (nat, yem, aug) = (contact(&s, "Natalie Solo").await, contact(&s, "Yemaya Member").await, contact(&s, "Augustina P").await);
        // Natalie is the only chapter lead, leads Partnerships alone, and is a member elsewhere.
        committee(&s, "Chapter leads", vec![nat.clone()], vec![yem.clone()], true).await;
        let partners = committee(&s, "Partnerships", vec![nat.clone()], vec![], false).await;
        let wellness = committee(&s, "Wellness", vec![aug.clone()], vec![nat.clone()], false).await;
        let before = s.ledger.try_lock().expect("ledger").len();
        let _serial = COMMITMENT_LOCK.lock().await;
        let e = leave(&s, &nat.party_id).await.unwrap_err();
        assert_eq!(e.status, StatusCode::BAD_REQUEST);
        assert!(e.message.contains("last chapter lead") && e.message.contains("Nothing was changed"));
        drop(_serial);
        assert_eq!(s.ledger.try_lock().expect("ledger").len(), before, "a refused leave writes nothing");
        let state = state_of(&s);
        assert!(state.chapter.committees[&partners].is_lead(&nat.party_id));
        assert!(state.chapter.committees[&wellness].includes(&nat.party_id));
        assert!(load_book(&s).unwrap().contacts.contains_key(&nat.party_id));
    }

    #[tokio::test]
    async fn a_committee_needs_a_real_name() {
        let (_dir, s) = fresh_rest_state(None).await;
        let (nat, yem) = (contact(&s, "Natalie Co").await, contact(&s, "Yemaya Co").await);
        committee(&s, "Chapter leads", vec![nat.clone(), yem.clone()], vec![], true).await;
        let _serial = COMMITMENT_LOCK.lock().await;
        let before = s.ledger.try_lock().expect("ledger").len();
        for name in ["", "   ", &"x".repeat(49)] {
            let e = add_committee(&s, &nat.party_id, name, "", &yem.party_id, false).await.unwrap_err();
            assert_eq!(e.status, StatusCode::BAD_REQUEST, "name {name:?}");
        }
        assert_eq!(s.ledger.try_lock().expect("ledger").len(), before);
        add_committee(&s, &nat.party_id, &"x".repeat(48), "", &yem.party_id, false).await.expect("48 is fine");
    }

    #[test]
    fn local_dates_read_in_the_chapter_offset() {
        let t = parse_local("2026-12-08", "18:30").unwrap();
        assert_eq!(t.with_timezone(&chapter_offset()).format("%H:%M").to_string(), "18:30");
        assert!(parse_local("12/08/2026", "").is_none());
        assert!(mailto("a b@example.org", "Hi & bye").starts_with("mailto:a%20b%40example.org?subject=Re%3A%20Hi%20%26%20bye"));
    }
}
