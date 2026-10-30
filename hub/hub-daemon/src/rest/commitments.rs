// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Commitments, slice K1 (hub/docs/PRD_COMMITMENTS.md §7): the operator's routes.
//!
//! - `POST /admin/api/commitments` opens one; `/:id/move`, `/:id/acknowledge` and `/:id/resolve`
//!   record what the operator was told; `GET /admin/api/commitments` lists them by queue.
//! - `/admin/api/contacts` is the contact book (C3): names and addresses held off the ledger,
//!   erasable. `/admin/api/contacts/members/:lct_id` holds a member's address there too (K3).
//! - K3: `GET /admin/api/commitments/nudges` is what the off-hub carrier should send, and
//!   `POST /admin/api/commitments/nudges/delivered` is its report of each attempt (C4).
//!
//! Every route is operator-plane only (loopback). Every write runs its checks and its witness
//! under [`COMMITMENT_LOCK`], so two writers cannot both pass a check only one of them may: the
//! loser of a resolution race is answered with what won (§4.1). K2's sweep takes the same lock.
use super::*;
use hub_lib::commitments::{
    self, AckVia, Commitment, Contact, ContactBook, MemberAddress, MoveKind, Outcome, PartyKind, PartyRef, Refusal,
};

/// Serialises every commitment write and every contact-book write.
pub(crate) static COMMITMENT_LOCK: tokio::sync::Mutex<()> = tokio::sync::Mutex::const_new(());

const MAX_CONTACT_NAME_LEN: usize = 64;
const MAX_ADDRESS_LEN: usize = 254;
const MAX_NOTE_REF_LEN: usize = 200;

fn refused(r: Refusal) -> ApiError {
    let status = match r {
        Refusal::Unknown(_) => StatusCode::NOT_FOUND,
        Refusal::AlreadyOpen(_) | Refusal::AlreadyResolved { .. } => StatusCode::CONFLICT,
        Refusal::Invalid(_) => StatusCode::BAD_REQUEST,
    };
    ApiError { status, message: r.to_string() }
}

fn book_path(s: &RestState) -> std::path::PathBuf {
    ContactBook::path(&s.paths.root)
}

fn load_book(s: &RestState) -> Result<ContactBook, ApiError> {
    ContactBook::load(&book_path(s)).map_err(ApiError::internal)
}

/// A party a body names must exist: a member in the projection, or a contact in the book.
fn check_party(state: &HubState, book: &ContactBook, p: &PartyRef, field: &str) -> Result<(), ApiError> {
    let known = match p.kind {
        PartyKind::Member => Uuid::parse_str(&p.party_id).map_or(false, |u| state.members.contains_key(&u)),
        PartyKind::Contact => book.contacts.contains_key(&p.party_id),
    };
    if known {
        Ok(())
    } else {
        Err(ApiError::bad_request(format!("{field}: {} is not a known {:?}", p.party_id, p.kind)))
    }
}

/// The leads role must be a live role entity: an escalation to nobody reaches nobody.
fn check_leads_role(state: &HubState, role: &str) -> Result<Uuid, ApiError> {
    let id = Uuid::parse_str(role)
        .map_err(|_| ApiError::bad_request(format!("leads_role: {role} is not a role entity id")))?;
    match state.roles.get(&id) {
        Some(r) if !r.retired => Ok(id),
        Some(_) => Err(ApiError::bad_request(format!("leads_role: role {id} is retired"))),
        None => Err(ApiError::bad_request(format!("leads_role: no role entity {id}"))),
    }
}

/// Who may be recorded as moving or resolving: the owner, the backup, whoever holds the leads
/// role or a seat within it, or, where `operator_may` says so, the operator in its own name.
/// An `update` or `stuck` is someone's movement on the job, so the operator relays it in that
/// person's name. Recorded under the operator's own id it would read as a lead's and send the
/// queue to leads (Legion, #947).
fn check_actor(s: &RestState, state: &HubState, c: &Commitment, by: &str, operator_may: bool) -> Result<(), ApiError> {
    if by == c.owner.party_id || by == c.backup.party_id {
        return Ok(());
    }
    if by == s.sovereign_lct_id.to_string() {
        return if operator_may {
            Ok(())
        } else {
            Err(ApiError::bad_request(
                "record an update or a stuck in the name of whoever moved: the owner, the backup, or a lead".to_string()))
        };
    }
    if leads_of(state, c).iter().any(|l| l == by) {
        Ok(())
    } else {
        Err(ApiError::bad_request(format!(
            "{by} is not the owner, the backup, a lead, or the operator of {}", c.commitment_id)))
    }
}

/// The members who hold the leads role, or a seat within it.
pub(crate) fn leads_of(state: &HubState, c: &Commitment) -> Vec<String> {
    let Ok(role) = Uuid::parse_str(&c.leads_role) else { return Vec::new() };
    let mut leads: Vec<String> = state.roles.values()
        .filter(|r| !r.retired && (r.role_lct_id == role || r.parent_role_lct_id == Some(role)))
        .filter_map(|r| r.occupant.map(|o| o.to_string()))
        .collect();
    leads.sort();
    leads.dedup();
    leads
}

/// Run the projection checks, then witness, both under [`COMMITMENT_LOCK`] (the caller holds it).
async fn checked_witness(s: &RestState, event: HubEvent) -> Result<u64, ApiError> {
    {
        let ledger = s.ledger.lock().await;
        commitments::check(&s.projected(&ledger).commitments, &event).map_err(refused)?;
    }
    witness_event(s, event).await
}

fn projected_commitment(state: &HubState, id: &str) -> Result<Commitment, ApiError> {
    let c = state.commitments.get(id).ok_or_else(|| refused(Refusal::Unknown(id.to_string())))?;
    if let Some(r) = &c.resolved {
        return Err(refused(Refusal::AlreadyResolved { commitment_id: id.to_string(), outcome: r.outcome, at: r.at }));
    }
    Ok(c.clone())
}

#[derive(Deserialize)]
pub(super) struct OpenBody {
    title: String,
    owner: PartyRef,
    backup: PartyRef,
    leads_role: String,
    ladder: Vec<u32>,
    #[serde(default)]
    due_at: Option<DateTime<Utc>>,
}

/// `POST /admin/api/commitments` — open a commitment on someone's behalf.
///
/// surface: admin_commitment_open   act: record that a party owns a job, with a backup and leads
/// S: low/reversible [construct: a queue entry; `withdrawn` ends it, and no outcome is recorded at open]
/// R: pass [construct: require_loopback on the operator listener]   W: pass [construct: operator plane; act by the Sovereign]
/// O: pass [construct: COMMITMENT_LOCK; parties, live leads role and shape checked before witness_event]
/// A: pass [construct: CommitmentOpened carries recorded_by and the derived basis]
/// V: n/a (reversible)
/// verdict: PASS
pub(super) async fn admin_commitment_open(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Json(body): Json<OpenBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    open_commitment(&s, body).await.map(Json)
}

async fn open_commitment(s: &RestState, body: OpenBody) -> Result<serde_json::Value, ApiError> {
    let _serial = COMMITMENT_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let book = load_book(s)?;
    check_party(&state, &book, &body.owner, "owner")?;
    check_party(&state, &book, &body.backup, "backup")?;
    check_leads_role(&state, &body.leads_role)?;
    let recorded_by = s.sovereign_lct_id;
    // C2: the operator naming someone else is not that person's word.
    let basis = if body.owner.party_id == recorded_by.to_string() {
        commitments::Basis::TakenBySelf
    } else {
        commitments::Basis::NamedByOther
    };
    let commitment_id = Uuid::new_v4().to_string();
    let entry_index = checked_witness(s, HubEvent::CommitmentOpened {
        commitment_id: commitment_id.clone(),
        title: body.title.trim().to_string(),
        owner: body.owner,
        backup: body.backup,
        leads_role: body.leads_role,
        ladder: body.ladder,
        due_at: body.due_at,
        recorded_by,
        basis,
    }).await?;
    Ok(serde_json::json!({ "opened": true, "commitment_id": commitment_id, "entry_index": entry_index }))
}

#[derive(Deserialize)]
pub(super) struct MoveBody {
    by: String,
    move_kind: MoveKind,
    #[serde(default)]
    to: Option<PartyRef>,
    #[serde(default)]
    note_ref: Option<String>,
}

/// `POST /admin/api/commitments/:id/move` — record movement: an update, "stuck", or a handoff.
/// A `stuck` also writes the escalation to the next position, under the same lock.
///
/// surface: admin_commitment_move   act: record that a party moved a commitment
/// S: low/reversible [construct: moves the queue; the next movement moves it again]
/// R: pass [construct: require_loopback]   W: pass [construct: operator plane; `by` must be a party, a lead, or the operator]
/// O: pass [construct: COMMITMENT_LOCK; unresolved + handoff `to` rule re-checked before each witness]
/// A: pass [construct: CommitmentMoved names `by`; a stuck's CommitmentEscalated names its cause]
/// V: n/a (reversible)
/// verdict: PASS
pub(super) async fn admin_commitment_move(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(commitment_id): Path<String>,
    Json(body): Json<MoveBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    move_commitment(&s, &commitment_id, body).await.map(Json)
}

async fn move_commitment(s: &RestState, id: &str, body: MoveBody) -> Result<serde_json::Value, ApiError> {
    if let Some(n) = &body.note_ref {
        if n.chars().count() > MAX_NOTE_REF_LEN || n.chars().any(char::is_control) {
            return Err(ApiError::bad_request(format!(
                "note_ref is a reference (at most {MAX_NOTE_REF_LEN} characters), not a note")));
        }
    }
    let _serial = COMMITMENT_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let c = projected_commitment(&state, id)?;
    check_actor(s, &state, &c, &body.by, body.move_kind == MoveKind::Handoff)?;
    if let Some(to) = &body.to {
        check_party(&state, &load_book(s)?, to, "to")?;
    }
    // The operator relaying what someone said. K4's links write `link`, K5 `member_act`.
    witness_move(s, &c, body, AckVia::Operator, None).await
}

/// Witness a move and, for a `stuck`, its escalation. The caller holds [`COMMITMENT_LOCK`], has
/// projected `c` under it, and has checked who `body.by` is.
async fn witness_move(
    s: &RestState, c: &Commitment, body: MoveBody, via: AckVia, link_digest: Option<String>,
) -> Result<serde_json::Value, ApiError> {
    let id = c.commitment_id.as_str();
    let move_kind = body.move_kind;
    let entry_index = checked_witness(s, HubEvent::CommitmentMoved {
        commitment_id: id.to_string(),
        by: body.by,
        via,
        move_kind,
        to: body.to,
        note_ref: body.note_ref,
        link_digest,
    }).await?;
    let mut out = serde_json::json!({ "moved": true, "entry_index": entry_index });
    // "I need help" moves the queue forward; the escalation names the position it moved to, so
    // K3 nudges it. At leads there is nowhere further, and nothing more is written.
    if move_kind == MoveKind::Stuck {
        if let Some(step) = c.queue.next().and_then(|p| p.as_step()) {
            let escalated = checked_witness(s, HubEvent::CommitmentEscalated {
                commitment_id: id.to_string(),
                step,
                cause: commitments::EscalationCause::Stuck,
                silent_since: None,
                window_hours: None,
                swept_at: Utc::now(),
            }).await.map_err(|e| ApiError { status: e.status, message: format!(
                "ledger entry {entry_index} records the stuck move, but its escalation was not witnessed \
                 ({}); the queue has moved, and K3 will not nudge until an escalation is on the ledger",
                e.message) })?;
            out["escalated_entry_index"] = serde_json::json!(escalated);
        }
    }
    Ok(out)
}

#[derive(Deserialize)]
pub(super) struct AckBody {
    party_id: String,
}

/// `POST /admin/api/commitments/:id/acknowledge` — the operator relays a party's acknowledgement.
/// Recorded `via: operator`: the operator's word, never the owner's own (C2, §5.1).
///
/// surface: admin_commitment_acknowledge   act: relay that a party accepted a commitment
/// S: low/reversible [construct: sets the queue; carries no delta weight (via operator)]
/// R: pass [construct: require_loopback]   W: pass [construct: operator plane; party must be owner or backup]
/// O: pass [construct: COMMITMENT_LOCK; unresolved re-checked before witness_event]
/// A: pass [construct: CommitmentAcknowledged carries via=operator]
/// V: n/a (reversible)
/// verdict: PASS
pub(super) async fn admin_commitment_acknowledge(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(commitment_id): Path<String>,
    Json(body): Json<AckBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    acknowledge_commitment(&s, &commitment_id, body).await.map(Json)
}

async fn acknowledge_commitment(s: &RestState, id: &str, body: AckBody) -> Result<serde_json::Value, ApiError> {
    let _serial = COMMITMENT_LOCK.lock().await;
    let entry_index = checked_witness(s, HubEvent::CommitmentAcknowledged {
        commitment_id: id.to_string(),
        party_id: body.party_id,
        via: AckVia::Operator,
        link_digest: None,
    }).await?;
    Ok(serde_json::json!({ "acknowledged": true, "via": "operator", "entry_index": entry_index }))
}

#[derive(Deserialize)]
pub(super) struct ResolveBody {
    outcome: Outcome,
    by: String,
}

/// `POST /admin/api/commitments/:id/resolve` — done or withdrawn. `missed` is the sweep's alone
/// (K2), so an operator cannot record a miss against a named party by hand.
///
/// surface: admin_commitment_resolve   act: record the one resolution a commitment gets
/// S: med/irreversible [construct: the commitment leaves the queue for good]
/// R: pass [construct: require_loopback]   W: pass [construct: operator plane; `by` must be a party, a lead, or the operator]
/// O: pass [construct: COMMITMENT_LOCK; unresolved re-checked before witness_event; the loser is told what won]
/// A: pass [construct: CommitmentResolved carries by + owner_acknowledged]
/// V: present [construct: `missed` refused here; withdrawn is the reversal path for a mistaken open]
/// verdict: PASS
pub(super) async fn admin_commitment_resolve(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(commitment_id): Path<String>,
    Json(body): Json<ResolveBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    resolve_commitment(&s, &commitment_id, body).await.map(Json)
}

async fn resolve_commitment(s: &RestState, id: &str, body: ResolveBody) -> Result<serde_json::Value, ApiError> {
    if body.outcome == Outcome::Missed {
        return Err(ApiError::bad_request(
            "`missed` is recorded by the sweep against a deadline, never by hand".to_string()));
    }
    let _serial = COMMITMENT_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let c = projected_commitment(&state, id)?;
    check_actor(s, &state, &c, &body.by, true)?;
    witness_resolution(s, &c, body, None).await
}

/// Witness a `done` or `withdrawn`. The caller holds [`COMMITMENT_LOCK`] and has checked `by`.
async fn witness_resolution(
    s: &RestState, c: &Commitment, body: ResolveBody, link_digest: Option<String>,
) -> Result<serde_json::Value, ApiError> {
    let entry_index = checked_witness(s, HubEvent::CommitmentResolved {
        commitment_id: c.commitment_id.clone(),
        outcome: body.outcome,
        by: body.by,
        resolved_at: Utc::now(),
        owner_acknowledged: c.owner_acknowledged(),
        link_digest,
    }).await?;
    Ok(serde_json::json!({ "resolved": true, "outcome": commitments::outcome_str(body.outcome),
        "entry_index": entry_index }))
}

/// A party for the operator's eyes: the contact book's name, or the member's roster name. An
/// erased contact reads as erased; the ledger keeps only its id.
pub(crate) fn party_view(state: &HubState, book: &ContactBook, p: &PartyRef) -> serde_json::Value {
    let name = match p.kind {
        PartyKind::Contact => book.contacts.get(&p.party_id).map(|c| c.name.clone()),
        PartyKind::Member => Uuid::parse_str(&p.party_id).ok()
            .and_then(|u| state.members.get(&u)).and_then(|m| m.name.clone()),
    };
    serde_json::json!({ "party_id": p.party_id, "kind": p.kind,
        "name": name, "erased": p.kind == PartyKind::Contact && !book.contacts.contains_key(&p.party_id) })
}

/// Open commitments ordered by queue position, then by how long the queue has waited.
pub(crate) fn open_by_queue(state: &HubState) -> Vec<&Commitment> {
    let mut open: Vec<&Commitment> = state.commitments.values().filter(|c| c.is_open()).collect();
    open.sort_by(|a, b| (a.queue, a.queue_since).cmp(&(b.queue, b.queue_since)));
    open
}

/// `GET /admin/api/commitments` — open commitments by queue, with names from the contact book.
pub(super) async fn admin_commitments_list(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let book = load_book(&s)?;
    let rows: Vec<serde_json::Value> = open_by_queue(&state).into_iter().map(|c| serde_json::json!({
        "commitment_id": c.commitment_id,
        "title": c.title,
        "owner": party_view(&state, &book, &c.owner),
        "backup": party_view(&state, &book, &c.backup),
        "leads_role": c.leads_role,
        "queue": c.queue,
        "queue_since": c.queue_since,
        "due_at": c.due_at,
        "basis": c.basis,
        "owner_acknowledged": c.owner_acknowledged(),
        "acknowledged": c.acknowledged,
        "escalations": c.escalations,
    })).collect();
    Ok(Json(serde_json::json!({ "open": rows.len(), "commitments": rows })))
}

#[derive(Deserialize)]
pub(super) struct ContactBody {
    name: String,
    address: String,
}

fn check_contact(body: &ContactBody) -> Result<(String, String), ApiError> {
    let name = body.name.trim();
    if name.is_empty() || name.chars().count() > MAX_CONTACT_NAME_LEN || name.chars().any(char::is_control) {
        return Err(ApiError::bad_request(format!(
            "name is required, at most {MAX_CONTACT_NAME_LEN} characters, no control characters")));
    }
    Ok((name.to_string(), check_address(&body.address)?))
}

/// `POST /admin/api/contacts` — add a person with no key yet. Off the ledger (C3).
///
/// surface: admin_contact_add   act: hold a volunteer's name and address for delivery
/// S: low/reversible [construct: an erasable file entry; nothing is witnessed]
/// R: pass [construct: require_loopback]   W: pass [construct: operator plane only]
/// O: pass [construct: COMMITMENT_LOCK around read-modify-write; a misread book is an error, never empty]
/// A: n/a [construct: deliberately unwitnessed — PII stays off the ledger]
/// V: n/a (erasable)
/// verdict: PASS
pub(super) async fn admin_contact_add(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Json(body): Json<ContactBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    add_contact(&s, body).await.map(Json)
}

async fn add_contact(s: &RestState, body: ContactBody) -> Result<serde_json::Value, ApiError> {
    let (name, address) = check_contact(&body)?;
    let _serial = COMMITMENT_LOCK.lock().await;
    let mut book = load_book(s)?;
    let party_id = Uuid::new_v4().to_string();
    book.contacts.insert(party_id.clone(), Contact { name, address, added_at: Utc::now() });
    book.save(&book_path(s)).map_err(ApiError::internal)?;
    Ok(serde_json::json!({ "added": true, "party": { "party_id": party_id, "kind": "contact" } }))
}

/// `GET /admin/api/contacts` — the contact book.
pub(super) async fn admin_contacts_list(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    Ok(Json(serde_json::to_value(load_book(&s)?).map_err(|e| ApiError::internal(e.into()))?))
}

/// `POST /admin/api/contacts/:party_id/erase` — remove a person's details. The ledger keeps the
/// opaque id, which then names nobody. Commitments that still name it are reported, not refused:
/// erasure is the person's right, and the operator re-assigns.
///
/// surface: admin_contact_erase   act: erase a volunteer's name and address
/// S: med/irreversible [construct: the details are gone; the ledger id stays, resolving to nothing]
/// R: pass [construct: require_loopback]   W: pass [construct: operator plane only]
/// O: pass [construct: COMMITMENT_LOCK around read-modify-write]
/// A: n/a [construct: deliberately unwitnessed — recording an erasure of PII would need the PII's id only, which the ledger already has]
/// V: n/a [construct: erasure on request is the point]
/// verdict: PASS
pub(super) async fn admin_contact_erase(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(party_id): Path<String>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    erase_contact(&s, &party_id).await.map(Json)
}

async fn erase_contact(s: &RestState, party_id: &str) -> Result<serde_json::Value, ApiError> {
    let _serial = COMMITMENT_LOCK.lock().await;
    let mut book = load_book(s)?;
    if book.contacts.remove(party_id).is_none() {
        return Err(ApiError::not_found(format!("no contact {party_id}")));
    }
    book.save(&book_path(s)).map_err(ApiError::internal)?;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let still_named: Vec<&str> = state.commitments.values()
        .filter(|c| c.is_open() && (c.owner.party_id == party_id || c.backup.party_id == party_id))
        .map(|c| c.commitment_id.as_str()).collect();
    Ok(serde_json::json!({ "erased": true, "open_commitments_still_naming": still_named }))
}

#[derive(Deserialize)]
pub(super) struct MemberAddressBody {
    address: String,
}

fn check_address(address: &str) -> Result<String, ApiError> {
    let address = address.trim();
    let shaped = address.len() <= MAX_ADDRESS_LEN
        && !address.chars().any(|c| c.is_whitespace() || c.is_control())
        && address.split_once('@').map_or(false, |(l, d)| !l.is_empty() && d.contains('.'));
    if shaped {
        Ok(address.to_string())
    } else {
        Err(ApiError::bad_request("address must be an email address".to_string()))
    }
}

/// `POST /admin/api/contacts/members/:lct_id` — where to reach a member (K3). Members are named on
/// the ledger by LCT id and had no delivery address anywhere; this holds one off the ledger (C3).
///
/// surface: admin_member_address_set   act: hold a member's address for delivery
/// S: low/reversible [construct: an erasable file entry; nothing is witnessed]
/// R: pass [construct: require_loopback]   W: pass [construct: operator plane only]
/// O: pass [construct: COMMITMENT_LOCK around read-modify-write; the member must be on the roster]
/// A: n/a [construct: deliberately unwitnessed — PII stays off the ledger]
/// V: n/a (erasable)
/// verdict: PASS
pub(super) async fn admin_member_address_set(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(lct_id): Path<String>,
    Json(body): Json<MemberAddressBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    set_member_address(&s, &lct_id, body).await.map(Json)
}

async fn set_member_address(s: &RestState, lct_id: &str, body: MemberAddressBody) -> Result<serde_json::Value, ApiError> {
    let address = check_address(&body.address)?;
    let _serial = COMMITMENT_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let member = Uuid::parse_str(lct_id).ok().filter(|u| state.members.contains_key(u))
        .ok_or_else(|| ApiError::not_found(format!("no member {lct_id}")))?;
    let mut book = load_book(s)?;
    book.members.insert(member.to_string(), MemberAddress { address, added_at: Utc::now() });
    book.save(&book_path(s)).map_err(ApiError::internal)?;
    Ok(serde_json::json!({ "set": true, "member": member }))
}

/// `POST /admin/api/contacts/members/:lct_id/erase` — forget where to reach a member.
///
/// surface: admin_member_address_erase   act: erase a member's delivery address
/// S: low/irreversible [construct: the address is gone; the member and the ledger are untouched]
/// R: pass [construct: require_loopback]   W: pass [construct: operator plane only]
/// O: pass [construct: COMMITMENT_LOCK around read-modify-write]
/// A: n/a [construct: deliberately unwitnessed — PII stays off the ledger]
/// V: n/a [construct: erasure on request is the point]
/// verdict: PASS
pub(super) async fn admin_member_address_erase(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(lct_id): Path<String>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let _serial = COMMITMENT_LOCK.lock().await;
    let mut book = load_book(&s)?;
    if book.members.remove(&lct_id).is_none() {
        return Err(ApiError::not_found(format!("no address held for member {lct_id}")));
    }
    book.save(&book_path(&s)).map_err(ApiError::internal)?;
    Ok(Json(serde_json::json!({ "erased": true })))
}

/// Every nudge owed now, sendable or held. The carrier sends the rows with `held: null`; the
/// others are for the operator's eyes: `no_address` (nobody can reach this party yet) or `capped`
/// (this party has had [`commitments::NUDGE_CAP_PER_DAY`] attempts in the last day).
///
/// With `links` (K4), each row carries a movement link for its party, also appended to the body.
pub(crate) fn due_nudges(
    state: &HubState, book: &ContactBook, now: DateTime<Utc>, links: Option<&LinkMinter>,
) -> Vec<serde_json::Value> {
    let since = now - chrono::Duration::hours(24);
    let mut budget: std::collections::BTreeMap<String, usize> = std::collections::BTreeMap::new();
    let mut rows = Vec::new();
    let name = |p: &PartyRef| party_view(state, book, p)["name"].as_str()
        .map(str::to_string).unwrap_or_else(|| "someone".to_string());
    for c in open_by_queue(state) {
        for t in c.nudge_targets(&leads_of(state, c)) {
            if c.delivered(t.about_index, &t.party.party_id) {
                continue;
            }
            let address = book.address_of(&t.party);
            let left = budget.entry(t.party.party_id.clone()).or_insert_with(|| {
                commitments::NUDGE_CAP_PER_DAY
                    .saturating_sub(commitments::nudge_attempts_since(&state.commitments, &t.party.party_id, since))
            });
            let held = if address.is_none() {
                Some("no_address")
            } else if *left == 0 {
                Some("capped")
            } else {
                *left -= 1;
                None
            };
            let (subject, mut body) = c.nudge_message(&t, &name);
            let link = links.map(|m| format!("{}/c/{}", m.base, mint_link(m.key, &c.commitment_id, &t.party.party_id,
                now + chrono::Duration::days(LINK_TTL_DAYS))));
            if let Some(link) = &link {
                body.push_str(&format!("\n\nSay where it stands (done, stuck, or hand it on): {link}"));
            }
            rows.push(serde_json::json!({
                "commitment_id": c.commitment_id,
                "about_index": t.about_index,
                "about": t.about,
                "party": party_view(state, book, &t.party),
                "address": address,
                "held": held,
                "subject": subject,
                "body": body,
                "link": link,
            }));
        }
    }
    rows
}

/// `GET /admin/api/commitments/nudges` — what the carrier should send now (K3). The hub decides
/// what is owed, the cap and the wording; the carrier only delivers and reports.
pub(super) async fn admin_nudges_due(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    list_nudges(&s, link_base()).await.map(Json)
}

/// The listing behind [`admin_nudges_due`], with the public base passed in rather than read from
/// the environment.
async fn list_nudges(s: &RestState, base: Option<String>) -> Result<serde_json::Value, ApiError> {
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let book = load_book(s)?;
    // The key is made by the first listing that has a link to carry, not by any listing.
    let owed = !due_nudges(&state, &book, Utc::now(), None).is_empty();
    let key = match &base {
        Some(_) if owed => {
            let _serial = COMMITMENT_LOCK.lock().await;
            Some(link_key_or_create(&s.paths.root).map_err(ApiError::internal)?)
        }
        _ => None,
    };
    let minter = base.as_deref().zip(key.as_ref()).map(|(base, key)| LinkMinter { base, key });
    let rows = due_nudges(&state, &book, Utc::now(), minter.as_ref());
    // Without a public base URL a nudge still goes out, with no link in it; say so where the
    // operator looks.
    Ok(serde_json::json!({ "cap_per_day": commitments::NUDGE_CAP_PER_DAY,
        "links": if base.is_some() { "on" } else { "off: set HUB_PUBLIC_BASE_URL" }, "nudges": rows }))
}

#[derive(Deserialize)]
pub(super) struct DeliveredBody {
    commitment_id: String,
    about_index: u64,
    party_id: String,
    channel: String,
    ok: bool,
}

/// `POST /admin/api/commitments/nudges/delivered` — the carrier's report of one attempt.
///
/// surface: admin_nudge_delivered   act: record that a nudge was sent, or failed
/// S: low/reversible [construct: a delivery record; it moves no queue and records no outcome]
/// R: pass [construct: require_loopback on the operator listener]   W: pass [construct: operator plane; the carrier runs as the operator]
/// O: pass [construct: COMMITMENT_LOCK; entry, party and channel checked before witness_event]
/// A: pass [construct: NudgeDelivered carries the entry it was about and the outcome]
/// V: n/a (reversible)
/// verdict: PASS
pub(super) async fn admin_nudge_delivered(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Json(body): Json<DeliveredBody>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    record_delivery(&s, body).await.map(Json)
}

async fn record_delivery(s: &RestState, body: DeliveredBody) -> Result<serde_json::Value, ApiError> {
    let _serial = COMMITMENT_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let c = state.commitments.get(&body.commitment_id)
        .ok_or_else(|| refused(Refusal::Unknown(body.commitment_id.clone())))?;
    // The party must be one this commitment could have nudged. Not "is owed now": the queue may
    // have moved between the send and this report, and the send still happened.
    // An owner a handoff took off the job is told so (K4b), and the report of that send names them.
    let party_of_it = body.party_id == c.owner.party_id || body.party_id == c.backup.party_id
        || leads_of(&state, c).iter().any(|l| l == &body.party_id)
        || c.handoffs.iter().any(|h| h.index == body.about_index && h.previous_owner.party_id == body.party_id);
    if !party_of_it {
        return Err(ApiError::bad_request(format!(
            "{} is not the owner, the backup or a lead of {}, nor an owner a handoff took it from",
            body.party_id, body.commitment_id)));
    }
    if body.ok && c.delivered(body.about_index, &body.party_id) {
        return Err(ApiError {
            status: StatusCode::CONFLICT,
            message: format!("already delivered: entry {} to {}", body.about_index, body.party_id),
        });
    }
    let index = checked_witness(s, HubEvent::NudgeDelivered {
        commitment_id: body.commitment_id,
        about_index: body.about_index,
        party_id: body.party_id,
        channel: body.channel,
        ok: body.ok,
    }).await?;
    Ok(serde_json::json!({ "recorded": true, "index": index }))
}

// ---------------------------------------------------------------------------------------------
// K4: movement links (PRD §5, the movement-link block). Each nudge carries a link minted for one
// (commitment, party). Opening it shows the job and what this party can say; each answer is a
// POST, so a mail scanner that fetches the link moves nothing. The link is the whole credential:
// possession of it, recorded on the entry as `via: link` plus the token's digest.
// ---------------------------------------------------------------------------------------------

/// How long a link works. Long enough to outlast a commitment's ladder; a resolved commitment
/// refuses every answer anyway.
pub(crate) const LINK_TTL_DAYS: i64 = 30;
/// Domain separation: this key MACs nothing else, but the label says what a MAC is for.
const LINK_MAC_LABEL: &[u8] = b"web4-hub commitment link v1\n";
const LINK_MAC_LEN: usize = 16;

fn link_key_path(root: &std::path::Path) -> std::path::PathBuf {
    root.join("commitment-links.key")
}

/// The hub's link key, if one exists. Reading never creates it: a hub that has minted no link
/// has none to honour. Deleting the file voids every link sent so far.
pub(crate) fn read_link_key(root: &std::path::Path) -> anyhow::Result<Option<[u8; 32]>> {
    let path = link_key_path(root);
    match std::fs::read(&path) {
        Ok(bytes) => {
            // Anyone who can read the key can mint any party's link: refuse, never warn and go on.
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                let mode = std::fs::metadata(&path)?.permissions().mode();
                if mode & 0o077 != 0 {
                    anyhow::bail!("the link key is readable by others (mode {:o}); chmod 600 it", mode & 0o777);
                }
            }
            <[u8; 32]>::try_from(bytes.as_slice()).map(Some)
                .map_err(|_| anyhow::anyhow!("the link key is not 32 bytes"))
        }
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(e) => Err(e.into()),
    }
}

/// The link key, created on first use. The caller holds [`COMMITMENT_LOCK`], so two first uses
/// cannot each write a key and void the other's links.
fn link_key_or_create(root: &std::path::Path) -> anyhow::Result<[u8; 32]> {
    if let Some(key) = read_link_key(root)? {
        return Ok(key);
    }
    let mut key = [0u8; 32];
    rand::RngCore::fill_bytes(&mut rand::rngs::OsRng, &mut key);
    hub_lib::atomic_file::write_atomic_mode(&link_key_path(root), key.to_vec(), 0o600)?;
    Ok(key)
}

fn link_mac(key: &[u8; 32], payload: &str) -> hmac::Hmac<sha2::Sha256> {
    use hmac::Mac;
    let mut mac = <hmac::Hmac<sha2::Sha256> as Mac>::new_from_slice(key).expect("HMAC takes any key length");
    mac.update(LINK_MAC_LABEL);
    mac.update(payload.as_bytes());
    mac
}

/// `<commitment_id>.<party_id>.<expires, unix seconds>.<MAC, hex>`. The ids are UUIDs the hub
/// made, so `.` never occurs inside one.
pub(crate) fn mint_link(key: &[u8; 32], commitment_id: &str, party_id: &str, expires: DateTime<Utc>) -> String {
    use hmac::Mac;
    let payload = format!("{commitment_id}.{party_id}.{}", expires.timestamp());
    let tag = link_mac(key, &payload).finalize().into_bytes();
    format!("{payload}.{}", hex::encode(&tag[..LINK_MAC_LEN]))
}

/// What a verified link says, and the digest the ledger records in place of the token.
#[derive(Debug, PartialEq, Eq)]
pub(crate) struct LinkClaim {
    pub commitment_id: String,
    pub party_id: String,
    pub digest: String,
}

#[derive(Debug, PartialEq, Eq)]
pub(crate) enum LinkError {
    /// Not a link this hub made. Indistinguishable on purpose: no oracle for a forger.
    Invalid,
    /// A link this hub made, past its date.
    Expired,
}

pub(crate) fn read_link(key: &[u8; 32], token: &str, now: DateTime<Utc>) -> Result<LinkClaim, LinkError> {
    use hmac::Mac;
    let (payload, tag) = token.rsplit_once('.').ok_or(LinkError::Invalid)?;
    // One link, one spelling: `hex::decode` also takes uppercase, and a re-cased MAC would verify
    // with a different digest, so "acknowledges once" would hold per spelling (Legion, #957).
    if !tag.chars().all(|ch| ch.is_ascii_digit() || ('a'..='f').contains(&ch)) {
        return Err(LinkError::Invalid);
    }
    let tag = hex::decode(tag).map_err(|_| LinkError::Invalid)?;
    // `verify_truncated_left` accepts any prefix length, a 1-byte one included: pin the length.
    if tag.len() != LINK_MAC_LEN {
        return Err(LinkError::Invalid);
    }
    link_mac(key, payload).verify_truncated_left(&tag).map_err(|_| LinkError::Invalid)?;
    let mut parts = payload.split('.');
    let (Some(commitment_id), Some(party_id), Some(expires), None) =
        (parts.next(), parts.next(), parts.next(), parts.next()) else { return Err(LinkError::Invalid) };
    let expires = expires.parse::<i64>().ok().and_then(|t| DateTime::from_timestamp(t, 0)).ok_or(LinkError::Invalid)?;
    if now >= expires {
        return Err(LinkError::Expired);
    }
    use sha2::Digest;
    let digest = hex::encode(sha2::Sha256::digest(token.as_bytes()))[..commitments::LINK_DIGEST_LEN].to_string();
    Ok(LinkClaim { commitment_id: commitment_id.to_string(), party_id: party_id.to_string(), digest })
}

/// Where links point: `HUB_PUBLIC_BASE_URL`, the origin people reach the hub at. Unset, nudges
/// go out without a link: the operator plane's own address would reach nobody.
pub(crate) fn link_base() -> Option<String> {
    std::env::var("HUB_PUBLIC_BASE_URL").ok()
        .map(|b| b.trim().trim_end_matches('/').to_string())
        .filter(|b| !b.is_empty())
}

/// What a nudge listing needs to put a link in each row.
pub(crate) struct LinkMinter<'a> {
    pub base: &'a str,
    pub key: &'a [u8; 32],
}

/// Who a link's party is on the commitment now. A handoff can take someone off it.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum LinkRole {
    Owner,
    Backup,
    Lead,
}

fn role_of(state: &HubState, c: &Commitment, party_id: &str) -> Option<LinkRole> {
    if party_id == c.owner.party_id {
        Some(LinkRole::Owner)
    } else if party_id == c.backup.party_id {
        Some(LinkRole::Backup)
    } else if leads_of(state, c).iter().any(|l| l == party_id) {
        Some(LinkRole::Lead)
    } else {
        None
    }
}

/// The answers a link offers. Each is its own POST path, so a form needs no body.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum LinkAct {
    Ack,
    Update,
    Done,
    Stuck,
    Handoff,
    Take,
}

impl LinkAct {
    const ALL: [LinkAct; 6] =
        [LinkAct::Ack, LinkAct::Update, LinkAct::Done, LinkAct::Stuck, LinkAct::Handoff, LinkAct::Take];

    fn path(self) -> &'static str {
        match self {
            LinkAct::Ack => "acknowledge",
            LinkAct::Update => "update",
            LinkAct::Done => "done",
            LinkAct::Stuck => "stuck",
            LinkAct::Handoff => "handoff",
            LinkAct::Take => "take",
        }
    }

    fn parse(s: &str) -> Option<LinkAct> {
        LinkAct::ALL.into_iter().find(|a| a.path() == s)
    }
}

/// What this party may say now. The owner hands to the backup or asks for help; the backup or a
/// lead can take the job over. Acknowledging is offered until the party's own word is recorded.
///
/// A link that has already acknowledged never offers it again, even after a handoff cleared the
/// acknowledgement: the ledger would refuse it (Legion, #957). The new owner of a handoff is sent
/// a fresh link (K4b), and that one can acknowledge.
fn acts_for(c: &Commitment, role: LinkRole, claim: &LinkClaim) -> Vec<LinkAct> {
    let own_word = matches!(c.acknowledged.get(&claim.party_id), Some(AckVia::MemberAct | AckVia::Link));
    let mut acts = Vec::new();
    if role != LinkRole::Lead && !own_word && !c.link_acks.contains(&claim.digest) {
        acts.push(LinkAct::Ack);
    }
    acts.extend([LinkAct::Update, LinkAct::Done]);
    match role {
        LinkRole::Owner => acts.extend([LinkAct::Stuck, LinkAct::Handoff]),
        LinkRole::Backup | LinkRole::Lead => acts.push(LinkAct::Take),
    }
    acts
}

fn act_label(act: LinkAct, role: LinkRole, backup: &str) -> String {
    match (act, role) {
        (LinkAct::Ack, LinkRole::Owner) => "Yes, it's mine".to_string(),
        (LinkAct::Ack, _) => "Yes, I'll back this up".to_string(),
        (LinkAct::Update, _) => "Still on it".to_string(),
        (LinkAct::Done, _) => "It's done".to_string(),
        (LinkAct::Stuck, _) => "I'm stuck and need help".to_string(),
        (LinkAct::Handoff, _) => format!("Hand it to {backup}"),
        (LinkAct::Take, _) => "I'll take it over".to_string(),
    }
}

/// Record one answer from a link, under [`COMMITMENT_LOCK`]. The role and the offered answers are
/// worked out again here, not trusted from the page: the queue may have moved since it loaded.
async fn act_by_link(s: &RestState, claim: &LinkClaim, act: LinkAct) -> Result<serde_json::Value, ApiError> {
    let _serial = COMMITMENT_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let c = projected_commitment(&state, &claim.commitment_id)?;
    let role = role_of(&state, &c, &claim.party_id).ok_or_else(|| ApiError {
        status: StatusCode::FORBIDDEN,
        message: "you're no longer named on this job".to_string(),
    })?;
    if !acts_for(&c, role, claim).contains(&act) {
        return Err(ApiError { status: StatusCode::CONFLICT, message: "that answer isn't open to you now".to_string() });
    }
    let by = claim.party_id.clone();
    let digest = Some(claim.digest.clone());
    let moved = |move_kind, to| MoveBody { by: by.clone(), move_kind, to, note_ref: None };
    match act {
        LinkAct::Ack => {
            let entry_index = checked_witness(s, HubEvent::CommitmentAcknowledged {
                commitment_id: c.commitment_id.clone(),
                party_id: by,
                via: AckVia::Link,
                link_digest: digest,
            }).await?;
            Ok(serde_json::json!({ "acknowledged": true, "entry_index": entry_index }))
        }
        LinkAct::Update => witness_move(s, &c, moved(MoveKind::Update, None), AckVia::Link, digest).await,
        LinkAct::Stuck => witness_move(s, &c, moved(MoveKind::Stuck, None), AckVia::Link, digest).await,
        LinkAct::Handoff => {
            let to = Some(c.backup.clone());
            witness_move(s, &c, moved(MoveKind::Handoff, to), AckVia::Link, digest).await
        }
        LinkAct::Take => {
            let me = if role == LinkRole::Backup {
                c.backup.clone()
            } else {
                PartyRef { party_id: by.clone(), kind: PartyKind::Member }
            };
            witness_move(s, &c, moved(MoveKind::Handoff, Some(me)), AckVia::Link, digest).await
        }
        LinkAct::Done => witness_resolution(s, &c, ResolveBody { outcome: Outcome::Done, by }, digest).await,
    }
}

const LINK_PAGE_CSS: &str = "body{font:17px/1.5 system-ui,sans-serif;max-width:32rem;margin:2rem auto;padding:0 1rem}\
    form{margin:.5rem 0}button{font:inherit;width:100%;padding:.8rem;border-radius:.5rem;\
    border:1px solid #888;background:#f4f4f4;cursor:pointer}.muted{color:#666}";

/// `GET /c.css`: the link pages' style, a file of its own so their policy can forbid inline style.
pub(super) async fn link_page_css() -> axum::response::Response {
    use axum::response::IntoResponse;
    ([(axum::http::header::CONTENT_TYPE, "text/css; charset=utf-8")], LINK_PAGE_CSS).into_response()
}

fn link_page_response(status: StatusCode, title: &str, body_html: &str) -> axum::response::Response {
    use axum::response::IntoResponse;
    let page = format!(
        "<!doctype html><html><head><meta charset=\"utf-8\">\
         <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\
         <meta name=\"robots\" content=\"noindex\"><title>{}</title>\
         <link rel=\"stylesheet\" href=\"/c.css\"></head><body>{}</body></html>",
        esc(title), body_html);
    (
        status,
        [
            // The token is in the URL: keep it out of caches and out of any Referer.
            (axum::http::header::CACHE_CONTROL, "no-store"),
            (axum::http::header::REFERRER_POLICY, "no-referrer"),
            // The page acts for its party: nothing runs on it, and its forms post only here.
            (axum::http::header::CONTENT_SECURITY_POLICY, super::KEY_PAGE_CSP),
        ],
        axum::response::Html(page),
    ).into_response()
}

fn link_error_page(e: LinkError) -> axum::response::Response {
    match e {
        LinkError::Invalid => link_page_response(StatusCode::NOT_FOUND, "Link not found",
            "<h1>This link doesn't work</h1><p>Check that the whole link was copied from the email.</p>"),
        LinkError::Expired => link_page_response(StatusCode::GONE, "Link expired",
            "<h1>This link has expired</h1><p>Ask your organiser to send a new one.</p>"),
    }
}

/// The key and the claim, or the page to answer with instead.
fn verified_link(s: &RestState, token: &str) -> Result<LinkClaim, axum::response::Response> {
    let key = match read_link_key(&s.paths.root) {
        Ok(Some(key)) => key,
        Ok(None) => return Err(link_error_page(LinkError::Invalid)),
        Err(e) => {
            tracing::warn!("commitment link key unreadable: {e:#}");
            return Err(link_page_response(StatusCode::INTERNAL_SERVER_ERROR, "Something went wrong",
                "<h1>Something went wrong</h1><p>Please try again later.</p>"));
        }
    };
    read_link(&key, token, Utc::now()).map_err(link_error_page)
}

/// `GET /c/:token` — the page a nudge links to: the job, where it stands, and the answers open
/// to this party. Reading it changes nothing.
///
/// surface: commitment_link_page   act: none (a read of one commitment by one of its parties)
/// S: low/reversible [construct: no write; names shown are the ones the nudge already carried]
/// R: pass [construct: read_link, an HMAC over (commitment, party, expiry)]   W: n/a (read)
/// O: n/a   A: n/a (read)   V: n/a
/// verdict: PASS
pub(super) async fn link_page(
    State(s): State<RestState>,
    Path(token): Path<String>,
) -> axum::response::Response {
    let claim = match verified_link(&s, &token) {
        Ok(claim) => claim,
        Err(page) => return page,
    };
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let book = match load_book(&s) {
        Ok(book) => book,
        Err(e) => {
            tracing::warn!("contact book unreadable for a link page: {}", e.message);
            ContactBook::default()
        }
    };
    let Some(c) = state.commitments.get(&claim.commitment_id) else {
        return link_error_page(LinkError::Invalid);
    };
    let name = |p: &PartyRef| party_view(&state, &book, p)["name"].as_str()
        .map(str::to_string).unwrap_or_else(|| "someone".to_string());
    let title = c.title.clone();
    let mut html = format!("<h1>{}</h1>", esc(&title));
    if let Some(r) = &c.resolved {
        html.push_str(&format!("<p>This is closed: {} on {}.</p>",
            commitments::outcome_str(r.outcome), r.at.format("%Y-%m-%d")));
        return link_page_response(StatusCode::OK, &title, &html);
    }
    let Some(role) = role_of(&state, c, &claim.party_id) else {
        html.push_str("<p>You're no longer named on this job, so there is nothing to answer here.</p>");
        return link_page_response(StatusCode::OK, &title, &html);
    };
    let owner = name(&c.owner);
    let backup = name(&c.backup);
    html.push_str(&match role {
        LinkRole::Owner => format!("<p>You're the owner. Your backup is {}.</p>", esc(&backup)),
        LinkRole::Backup => format!("<p>{} owns this. You're the backup.</p>", esc(&owner)),
        LinkRole::Lead => format!("<p>{} owns this, and {} is the backup. You're one of the leads.</p>",
            esc(&owner), esc(&backup)),
    });
    if let Some(due) = c.due_at {
        html.push_str(&format!("<p class=\"muted\">Due {}.</p>", due.format("%Y-%m-%d %H:%M UTC")));
    }
    for act in acts_for(c, role, &claim) {
        // Relative to /c/<token>, so the form posts back to this hub whatever origin served it.
        html.push_str(&format!("<form method=\"post\" action=\"{}/{}\"><button>{}</button></form>",
            esc(&token), act.path(), esc(&act_label(act, role, &backup))));
    }
    html.push_str("<p class=\"muted\">Your answer goes on the chapter's record, marked as sent from this link.</p>");
    link_page_response(StatusCode::OK, &title, &html)
}

/// `POST /c/:token/:act` — one answer from a link: acknowledge, update, done, stuck, handoff,
/// or take. No body: the act is the path.
///
/// surface: commitment_link_act   act: record movement, an acknowledgement or done, as a named party
/// S: low/reversible for movement; med for acknowledge and done [construct: acknowledge decides
///    whether a later miss can carry a delta (§5.1); done ends the commitment]
/// R: weak (possession of the link) [construct: read_link, HMAC over commitment + party + expiry]
/// W: escalate-for-ack [construct: the link binds one commitment and one party, expires, and acknowledges once (link_acks)]
/// O: pass [construct: read_link, then act_by_link re-derives role and offered answers under COMMITMENT_LOCK before checked_witness]
/// A: pass [construct: every entry carries via=link and the token's digest]
/// V: n/a [construct: a mistaken done or handoff is corrected by the operator; nothing here is irreversible beyond done]
/// verdict: PASS for movement; a link acknowledgement is recorded as via=link so a reader weighs it as possession-only
pub(super) async fn link_act(
    State(s): State<RestState>,
    Path((token, act)): Path<(String, String)>,
) -> axum::response::Response {
    let claim = match verified_link(&s, &token) {
        Ok(claim) => claim,
        Err(page) => return page,
    };
    let Some(act) = LinkAct::parse(&act) else {
        return link_page_response(StatusCode::NOT_FOUND, "Not found", "<h1>That isn't an answer this page offers</h1>");
    };
    let back = format!("<p><a href=\"../{}\">Back to the job</a></p>", esc(&token));
    match act_by_link(&s, &claim, act).await {
        Ok(_) => {
            let said = match act {
                LinkAct::Ack => "Thanks. It's recorded that you've seen this and said yes.",
                LinkAct::Update => "Thanks. It's recorded that you're still on it.",
                LinkAct::Done => "Thanks. It's recorded as done.",
                LinkAct::Stuck => "Recorded. Your backup has been asked to help.",
                LinkAct::Handoff => "Recorded. It's with your backup now.",
                LinkAct::Take => "Recorded. It's yours now.",
            };
            link_page_response(StatusCode::OK, "Recorded", &format!("<h1>{said}</h1>{back}"))
        }
        Err(e) => {
            let status = if e.status.is_server_error() { StatusCode::SERVICE_UNAVAILABLE } else { e.status };
            if e.status.is_server_error() {
                tracing::warn!("commitment link answer not recorded: {}", e.message);
            }
            let why = if e.status.is_server_error() {
                "The hub couldn't record it just now. Please try again later.".to_string()
            } else {
                e.message
            };
            link_page_response(status, "Not recorded", &format!("<h1>Not recorded</h1><p>{}</p>{back}", esc(&why)))
        }
    }
}

/// How often the sweep runs. Silence boundaries are accurate to ±1 interval (PRD §4).
pub(crate) const SWEEP_INTERVAL: std::time::Duration = std::time::Duration::from_secs(300);

/// Who the ledger says resolved a `missed`: the hub's own sweep, not a party.
pub(crate) const SWEEP_ACTOR: &str = "hub:sweep";

/// What one sweep wrote.
#[derive(Debug, Default, PartialEq, Eq, Serialize)]
pub(crate) struct SweepReport {
    pub escalated: u32,
    pub commitments_missed: u32,
    pub obligations_missed: u32,
    pub deltas: u32,
}

/// Start the in-daemon sweep (K2). It runs only while the hub is unlocked: a locked hub cannot
/// sign, and when it unlocks the next tick catches up from witnessed timestamps.
pub(crate) fn spawn_sweep(s: RestState) {
    tokio::spawn(async move {
        let mut tick = tokio::time::interval(SWEEP_INTERVAL);
        tick.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Delay);
        loop {
            tick.tick().await;
            if s.is_locked() {
                continue;
            }
            match sweep_once(&s, Utc::now()).await {
                Ok(r) if r != SweepReport::default() => tracing::info!(?r, "commitments sweep"),
                Ok(_) => {}
                Err(e) => tracing::warn!("commitments sweep failed (retries next tick): {}", e.message),
            }
        }
    });
}

/// The record a missed deadline leaves on the subject: the same temporal delta the R7 satisfy
/// path computes, classed Conduct, applied only under `EmitMode::Apply` (§5.1).
async fn missed_delta(
    s: &RestState, ob: &hub_lib::state::Obligation, request_id: &str, action_id: u64, action_kind: &str,
    now: DateTime<Utc>,
) -> Result<(), ApiError> {
    let deadline = web4_core::time::Deadline::new(ob.due_at).with_criticality(ob.criticality);
    let outcome = deadline.evaluate(&web4_core::time::Timing::started(ob.opened_at),
        web4_core::time::WitnessAvailability::Available, true, now);
    let impact = deadline.reputation_impact(&outcome);
    let delta = temporal_delta(ob, request_id, "missed", &impact, action_id, action_kind, now);
    let applied = {
        use hub_lib::law::{EmitMode, HubLawExt};
        let mode = s.law.read().await.as_ref().map(|l| l.reputation_emit_mode()).unwrap_or_default();
        mode == EmitMode::Apply && delta.class == web4_core::r6::DeltaClass::Conduct
    };
    witness_event(s, HubEvent::ReputationRecorded { delta, applied }).await.map(|_| ())
}

/// One sweep at `now`, under [`COMMITMENT_LOCK`]. For each open commitment, in order:
/// - **missed:** past `due_at + grace`, resolve it `missed` (one resolution, re-checked under the
///   lock). A Conduct delta follows only if the owner's own acknowledgement is on the ledger (§5.1).
/// - **silence:** otherwise, write every escalation step the queue has reached since
///   `queue_since`, summing windows only within this tick (catch-up after a lock).
///
/// Then every open R7 obligation past `due_at + grace` is resolved `missed` with its delta.
/// The resolution is witnessed before its delta: a failed delta leaves a missing debit, which the
/// ledger shows, never a second one.
pub(crate) async fn sweep_once(s: &RestState, now: DateTime<Utc>) -> Result<SweepReport, ApiError> {
    let grace = {
        use hub_lib::law::HubLawExt;
        let minutes = s.law.read().await.as_ref().map(|l| l.commitment_grace_minutes())
            .unwrap_or(hub_lib::law::DEFAULT_COMMITMENT_GRACE_MINUTES);
        chrono::Duration::minutes(i64::from(minutes))
    };
    let _serial = COMMITMENT_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let mut report = SweepReport::default();

    for c in state.commitments.values().filter(|c| c.is_open()) {
        if c.due_at.map_or(false, |due| now >= due + grace) {
            let owner_acknowledged = c.owner_acknowledged();
            let index = checked_witness(s, HubEvent::CommitmentResolved {
                commitment_id: c.commitment_id.clone(),
                outcome: Outcome::Missed,
                by: SWEEP_ACTOR.to_string(),
                resolved_at: now,
                owner_acknowledged,
                link_digest: None,
            }).await?;
            report.commitments_missed += 1;
            // W: a named owner who never acknowledged is not debited for the operator's claim.
            if owner_acknowledged && c.owner.kind == PartyKind::Member {
                let ob = hub_lib::state::Obligation {
                    subject_lct: c.owner.party_id.clone(),
                    role_lct: c.leads_role.clone(),
                    due_at: c.due_at.expect("checked above"),
                    criticality: web4_core::time::Criticality::default(),
                    opened_at: c.opened_at,
                };
                missed_delta(s, &ob, &c.commitment_id, index, "commitment_missed", now).await?;
                report.deltas += 1;
            }
            continue;
        }
        // Silence: walk the ladder from where the queue stands.
        let mut pos = c.queue;
        let mut window_start = c.queue_since;
        while let (Some(hours), Some(next)) = (c.ladder.get(pos as usize).copied(), pos.next()) {
            let window_end = window_start + chrono::Duration::hours(i64::from(hours));
            if now < window_end {
                break;
            }
            checked_witness(s, HubEvent::CommitmentEscalated {
                commitment_id: c.commitment_id.clone(),
                step: next.as_step().expect("next() is never Owner"),
                cause: commitments::EscalationCause::Silence,
                silent_since: Some(window_start),
                window_hours: Some(hours),
                swept_at: now,
            }).await?;
            report.escalated += 1;
            pos = next;
            window_start = window_end;
        }
    }

    for (request_id, ob) in &state.obligations {
        if now < ob.due_at + grace {
            continue;
        }
        let index = witness_event(s, HubEvent::ObligationResolved {
            request_id: request_id.clone(),
            outcome: "missed".to_string(),
            resolved_by: None,
            resolved_at: now,
        }).await?;
        report.obligations_missed += 1;
        missed_delta(s, ob, request_id, index, "obligation_missed", now).await?;
        report.deltas += 1;
    }
    Ok(report)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rest::channel_e2e_tests::{fresh_rest_state, witness_for_test};

    fn member(id: Uuid) -> PartyRef {
        PartyRef { party_id: id.to_string(), kind: PartyKind::Member }
    }

    /// A chapter with two members and a live leads role held by a third.
    async fn chapter() -> (tempfile::TempDir, RestState, Uuid, Uuid, Uuid, Uuid) {
        let (tmp, s) = fresh_rest_state(None).await;
        let (alex, sam, lee) = (Uuid::new_v4(), Uuid::new_v4(), Uuid::new_v4());
        for (id, name) in [(alex, "Alex"), (sam, "Sam"), (lee, "Lee")] {
            witness_for_test(&s, HubEvent::MemberAdded {
                member_lct_id: id, added_by: s.sovereign_lct_id, member_name: Some(name.into()),
                member_pubkey_hex: None, anchor_level: None, trust_ceiling: None,
            }).await;
        }
        let role = Uuid::new_v4();
        witness_for_test(&s, HubEvent::RoleCreated {
            role_lct_id: role,
            role: web4_core::role::SocietyRole::Custom("leads".into()),
            role_kind: hub_lib::events::RoleKind::Capacity,
            charter: None,
            parent_role_lct_id: None,
            initial_occupant: Some(lee),
            created_by: s.sovereign_lct_id,
        }).await;
        (tmp, s, alex, sam, lee, role)
    }

    async fn open(s: &RestState, owner: PartyRef, backup: PartyRef, role: Uuid) -> Result<String, ApiError> {
        let v = open_commitment(s, OpenBody {
            title: "Venue AV".into(), owner, backup, leads_role: role.to_string(),
            ladder: vec![48, 24, 24], due_at: None,
        }).await?;
        Ok(v["commitment_id"].as_str().unwrap().to_string())
    }

    fn projection(s: &RestState, l: &hub_lib::ledger::HubLedger) -> HubState {
        s.projected(l)
    }

    async fn current(s: &RestState, id: &str) -> Commitment {
        let l = s.ledger.lock().await;
        projection(s, &l).commitments[id].clone()
    }

    #[tokio::test]
    async fn the_operator_opens_moves_and_resolves_and_the_ledger_reads_it_back() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let c = current(&s, &id).await;
        assert_eq!((c.basis, c.queue), (commitments::Basis::NamedByOther, commitments::QueuePos::Owner));
        assert!(!c.owner_acknowledged());

        acknowledge_commitment(&s, &id, AckBody { party_id: alex.to_string() }).await.unwrap();
        assert!(!current(&s, &id).await.owner_acknowledged(), "a relay is not the owner's own word");

        // Stuck writes the move and the escalation to the backup.
        let out = move_commitment(&s, &id, MoveBody {
            by: alex.to_string(), move_kind: MoveKind::Stuck, to: None, note_ref: None }).await.unwrap();
        assert!(out["escalated_entry_index"].is_u64(), "{out}");
        let c = current(&s, &id).await;
        assert_eq!(c.queue, commitments::QueuePos::Backup);
        assert_eq!(c.escalations.len(), 1);
        assert_eq!(c.escalations[0].cause, commitments::EscalationCause::Stuck);

        resolve_commitment(&s, &id, ResolveBody { outcome: Outcome::Done, by: sam.to_string() }).await.unwrap();
        let again = resolve_commitment(&s, &id, ResolveBody { outcome: Outcome::Withdrawn, by: sam.to_string() })
            .await.unwrap_err();
        assert_eq!(again.status, StatusCode::CONFLICT);
        assert!(again.message.starts_with("already resolved:"), "{}", again.message);
    }

    #[tokio::test]
    async fn refusals_witness_nothing() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let before = s.ledger.lock().await.len();
        let stranger = Uuid::new_v4();
        // Unknown party, unknown role, same owner and backup.
        assert!(open(&s, member(stranger), member(sam), role).await.is_err());
        assert!(open(&s, member(alex), member(sam), Uuid::new_v4()).await.is_err());
        assert!(open(&s, member(alex), member(alex), role).await.is_err());
        // A stranger cannot be recorded as moving; a handoff needs `to`; missed is the sweep's.
        assert!(move_commitment(&s, &id, MoveBody { by: stranger.to_string(), move_kind: MoveKind::Update,
            to: None, note_ref: None }).await.is_err());
        assert!(move_commitment(&s, &id, MoveBody { by: alex.to_string(), move_kind: MoveKind::Handoff,
            to: None, note_ref: None }).await.is_err());
        assert!(resolve_commitment(&s, &id, ResolveBody { outcome: Outcome::Missed, by: alex.to_string() })
            .await.is_err());
        assert!(acknowledge_commitment(&s, &id, AckBody { party_id: stranger.to_string() }).await.is_err());
        assert_eq!(s.ledger.lock().await.len(), before, "a refusal reached the ledger");
    }

    /// Legion + NOVA on #947: the operator-plane call `{by: sam, handoff, to: sam}` must not make
    /// Sam's acknowledgement appear. Sam never acted; the operator relayed it.
    #[tokio::test]
    async fn an_operator_relayed_self_handoff_does_not_acknowledge_for_the_new_owner() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        move_commitment(&s, &id, MoveBody { by: sam.to_string(), move_kind: MoveKind::Handoff,
            to: Some(member(sam)), note_ref: None }).await.unwrap();
        let c = current(&s, &id).await;
        assert_eq!((c.owner.party_id.clone(), c.basis), (sam.to_string(), commitments::Basis::NamedByOther));
        assert!(!c.owner_acknowledged());
    }

    #[tokio::test]
    async fn the_operator_relays_an_update_in_the_movers_name_not_its_own() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let before = s.ledger.lock().await.len();
        for kind in [MoveKind::Update, MoveKind::Stuck] {
            let e = move_commitment(&s, &id, MoveBody { by: s.sovereign_lct_id.to_string(), move_kind: kind,
                to: None, note_ref: None }).await.unwrap_err();
            assert_eq!(e.status, StatusCode::BAD_REQUEST);
        }
        assert_eq!(s.ledger.lock().await.len(), before);
        // The operator may still resolve, and hand off, in its own name.
        resolve_commitment(&s, &id, ResolveBody { outcome: Outcome::Withdrawn, by: s.sovereign_lct_id.to_string() })
            .await.unwrap();
    }

    #[tokio::test]
    async fn a_lead_may_move_and_the_queue_goes_to_the_leads() {
        let (_tmp, s, alex, sam, lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        move_commitment(&s, &id, MoveBody { by: lee.to_string(), move_kind: MoveKind::Update,
            to: None, note_ref: Some("forum/venue-av.md".into()) }).await.unwrap();
        assert_eq!(current(&s, &id).await.queue, commitments::QueuePos::Leads);
    }

    #[tokio::test]
    async fn a_contact_can_own_and_erasure_leaves_only_the_id() {
        let (_tmp, s, alex, _sam, _lee, role) = chapter().await;
        let out = add_contact(&s, ContactBody { name: "Robin".into(), address: "robin@example.org".into() })
            .await.unwrap();
        let pid = out["party"]["party_id"].as_str().unwrap().to_string();
        let robin = PartyRef { party_id: pid.clone(), kind: PartyKind::Contact };
        let id = open(&s, robin.clone(), member(alex), role).await.unwrap();
        // C3: the address is in the book, never on the ledger.
        {
            let l = s.ledger.lock().await;
            let bytes = serde_json::to_string(&l.entries()).unwrap();
            assert!(!bytes.contains("robin@example.org") && !bytes.contains("Robin"), "PII reached the ledger");
        }
        let out = erase_contact(&s, &pid).await.unwrap();
        assert_eq!(out["open_commitments_still_naming"], serde_json::json!([id]));
        let state = { let l = s.ledger.lock().await; projection(&s, &l) };
        let v = party_view(&state, &load_book(&s).unwrap(), &robin);
        assert_eq!((v["erased"].as_bool(), v["name"].is_null()), (Some(true), true));
        assert_eq!(erase_contact(&s, &pid).await.unwrap_err().status, StatusCode::NOT_FOUND);
        assert!(add_contact(&s, ContactBody { name: "X".into(), address: "not an address".into() }).await.is_err());
    }

    #[tokio::test]
    async fn the_operator_page_lists_by_queue_and_escapes_the_title() {
        let (_tmp, s, alex, _sam, _lee, role) = chapter().await;
        let out = add_contact(&s, ContactBody { name: "Robin".into(), address: "robin@example.org".into() })
            .await.unwrap();
        let robin = PartyRef { party_id: out["party"]["party_id"].as_str().unwrap().into(), kind: PartyKind::Contact };
        open_commitment(&s, OpenBody { title: "<script>x</script>".into(), owner: robin, backup: member(alex),
            leads_role: role.to_string(), ladder: vec![48], due_at: None }).await.unwrap();
        let Ok(axum::response::Html(html)) = crate::admin::commitments_page(State(s.clone())).await else {
            panic!("the commitments page failed to render");
        };
        assert!(!html.contains("<script>x</script>") && html.contains("&lt;script&gt;"), "title not escaped");
        assert!(html.contains("Robin") && html.contains("not yet acknowledged"), "{html}");
    }

    fn kinds(s_entries: &[hub_lib::ledger::LedgerEntry], kind: &str) -> usize {
        s_entries.iter().filter(|e| e.event.kind() == kind).count()
    }

    #[tokio::test]
    async fn silence_escalates_one_window_at_a_time_and_catches_up_within_a_tick() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let t0 = current(&s, &id).await.queue_since;
        let h = chrono::Duration::hours;
        // Inside the owner's 48h window: nothing.
        assert_eq!(sweep_once(&s, t0 + h(47)).await.unwrap(), SweepReport::default());
        // A hub locked for 73h unlocks: one tick writes both steps, in order.
        let r = sweep_once(&s, t0 + h(73)).await.unwrap();
        assert_eq!(r.escalated, 2, "{r:?}");
        let c = current(&s, &id).await;
        assert_eq!(c.queue, commitments::QueuePos::Leads);
        let steps: Vec<_> = c.escalations.iter().map(|e| (e.step, e.cause)).collect();
        assert_eq!(steps, vec![
            (commitments::EscalationStep::Backup, commitments::EscalationCause::Silence),
            (commitments::EscalationStep::Leads, commitments::EscalationCause::Silence)]);
        // The second entry's silence started where the first window ended.
        {
            let l = s.ledger.lock().await;
            let esc: Vec<_> = l.entries().iter().filter_map(|e| match &e.event {
                HubEvent::CommitmentEscalated { silent_since, window_hours, .. } => Some((*silent_since, *window_hours)),
                _ => None }).collect();
            assert_eq!(esc, vec![(Some(t0), Some(48)), (Some(t0 + h(48)), Some(24))]);
        }
        // Idempotent: the same tick again writes nothing, and leads is the end of the ladder.
        assert_eq!(sweep_once(&s, t0 + h(73)).await.unwrap(), SweepReport::default());
        assert_eq!(sweep_once(&s, t0 + h(500)).await.unwrap(), SweepReport::default());
    }

    #[tokio::test]
    async fn movement_restarts_the_clock_from_the_mover() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let t0 = current(&s, &id).await.queue_since;
        sweep_once(&s, t0 + chrono::Duration::hours(49)).await.unwrap();
        move_commitment(&s, &id, MoveBody { by: sam.to_string(), move_kind: MoveKind::Update,
            to: None, note_ref: None }).await.unwrap();
        let c = current(&s, &id).await;
        // The backup moved: the queue stays theirs, measured from their movement (24h window).
        assert_eq!(c.queue, commitments::QueuePos::Backup);
        let since = c.queue_since;
        assert_eq!(sweep_once(&s, since + chrono::Duration::hours(23)).await.unwrap().escalated, 0);
        assert_eq!(sweep_once(&s, since + chrono::Duration::hours(24)).await.unwrap().escalated, 1);
    }

    async fn open_due(s: &RestState, owner: Uuid, backup: Uuid, role: Uuid, due: DateTime<Utc>) -> String {
        let v = open_commitment(s, OpenBody { title: "Confirm credits".into(), owner: member(owner),
            backup: member(backup), leads_role: role.to_string(), ladder: vec![480], due_at: Some(due) })
            .await.unwrap();
        v["commitment_id"].as_str().unwrap().to_string()
    }

    #[tokio::test]
    async fn a_miss_waits_out_the_grace_and_debits_only_an_owner_who_acknowledged() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let now = Utc::now();
        let named = open_due(&s, alex, sam, role, now).await;
        let acked = open_due(&s, sam, alex, role, now).await;
        witness_for_test(&s, HubEvent::CommitmentAcknowledged {
            commitment_id: acked.clone(), party_id: sam.to_string(), via: AckVia::Link,
            link_digest: Some("0".repeat(32)) }).await;
        // Inside the 15-minute default grace: nothing is missed.
        assert_eq!(sweep_once(&s, now + chrono::Duration::minutes(14)).await.unwrap().commitments_missed, 0);
        let r = sweep_once(&s, now + chrono::Duration::minutes(15)).await.unwrap();
        assert_eq!((r.commitments_missed, r.deltas), (2, 1), "{r:?}");
        let (named_c, acked_c) = (current(&s, &named).await, current(&s, &acked).await);
        let (rn, ra) = (named_c.resolved.unwrap(), acked_c.resolved.unwrap());
        assert_eq!((rn.outcome, rn.owner_acknowledged, rn.by.as_str()), (Outcome::Missed, false, SWEEP_ACTOR));
        assert_eq!((ra.outcome, ra.owner_acknowledged), (Outcome::Missed, true));
        let l = s.ledger.lock().await;
        let delta = l.entries().iter().find_map(|e| match &e.event {
            HubEvent::ReputationRecorded { delta, applied } => Some((delta.subject_lct.clone(), *applied)),
            _ => None }).expect("one delta");
        // Only the owner who acknowledged, and recorded-only: no law means classify_only.
        assert_eq!(delta, (sam.to_string(), false));
        assert_eq!(kinds(l.entries(), "reputation_recorded"), 1);
    }

    /// NOVA on #947: pin it end to end. An operator-relayed take-over followed by a miss records
    /// `owner_acknowledged: false` and writes no Conduct debit.
    #[tokio::test]
    async fn a_relayed_take_over_then_a_miss_debits_nobody() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let now = Utc::now();
        let id = open_due(&s, alex, sam, role, now).await;
        move_commitment(&s, &id, MoveBody { by: sam.to_string(), move_kind: MoveKind::Handoff,
            to: Some(member(sam)), note_ref: None }).await.unwrap();
        let r = sweep_once(&s, now + chrono::Duration::minutes(15)).await.unwrap();
        assert_eq!((r.commitments_missed, r.deltas), (1, 0), "{r:?}");
        let res = current(&s, &id).await.resolved.unwrap();
        assert_eq!((res.outcome, res.owner_acknowledged), (Outcome::Missed, false));
        assert_eq!(kinds(s.ledger.lock().await.entries(), "reputation_recorded"), 0);
    }

    #[tokio::test]
    async fn the_sweep_resolves_a_past_due_r7_obligation_once() {
        let (_tmp, s, alex, _sam, _lee, _role) = chapter().await;
        let now = Utc::now();
        witness_for_test(&s, HubEvent::ObligationOpened {
            request_id: "req-9".into(), subject_lct: alex.to_string(), role_lct: "citizen".into(),
            due_at: now - chrono::Duration::hours(1), criticality: web4_core::time::Criticality::Firm,
            opened_at: now - chrono::Duration::hours(2) }).await;
        let r = sweep_once(&s, now).await.unwrap();
        assert_eq!((r.obligations_missed, r.deltas), (1, 1));
        assert_eq!(sweep_once(&s, now).await.unwrap(), SweepReport::default(), "resolved once");
        let state = { let l = s.ledger.lock().await; projection(&s, &l) };
        assert!(!state.obligations.contains_key("req-9"));
        assert_eq!(state.obligations_resolved["req-9"].0, "missed");
    }

    /// Every write holds COMMITMENT_LOCK across its checks and its witness. While another holder
    /// has the lock, a resolution must not reach the ledger at all (the deterministic form of
    /// "two resolutions, one wins": a join! of two calls does not interleave on the test runtime).
    #[tokio::test]
    async fn a_resolution_waits_for_the_commitment_lock_before_witnessing() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let before = s.ledger.lock().await.len();
        let held = COMMITMENT_LOCK.lock().await;
        let task = {
            let (s, id) = (s.clone(), id.clone());
            tokio::spawn(async move {
                resolve_commitment(&s, &id, ResolveBody { outcome: Outcome::Done, by: alex.to_string() }).await
            })
        };
        tokio::time::sleep(std::time::Duration::from_millis(50)).await;
        assert_eq!(s.ledger.lock().await.len(), before, "witnessed while another writer held the lock");
        drop(held);
        task.await.unwrap().unwrap();
        assert_eq!(s.ledger.lock().await.len(), before + 1);
    }

    async fn nudges(s: &RestState) -> Vec<serde_json::Value> {
        let state = { let l = s.ledger.lock().await; s.projected(&l) };
        due_nudges(&state, &load_book(s).unwrap(), Utc::now(), None)
    }

    fn row<'a>(rows: &'a [serde_json::Value], party: Uuid) -> &'a serde_json::Value {
        rows.iter().find(|r| r["party"]["party_id"] == party.to_string()).expect("a row for the party")
    }

    async fn address(s: &RestState, who: Uuid, addr: &str) {
        set_member_address(s, &who.to_string(), MemberAddressBody { address: addr.into() }).await.unwrap();
    }

    fn report(id: &str, about_index: u64, party: Uuid, ok: bool) -> DeliveredBody {
        DeliveredBody { commitment_id: id.into(), about_index, party_id: party.to_string(), channel: "email".into(), ok }
    }

    #[tokio::test]
    async fn the_carrier_is_told_what_is_owed_and_its_report_closes_it() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let opened = current(&s, &id).await.opened_index;

        // Members have no address until the operator gives one: owed, but held.
        let rows = nudges(&s).await;
        assert_eq!(rows.len(), 2);
        assert!(rows.iter().all(|r| r["held"] == "no_address" && r["address"].is_null()), "{rows:?}");

        address(&s, alex, "alex@example.org").await;
        address(&s, sam, "sam@example.org").await;
        let rows = nudges(&s).await;
        let a = row(&rows, alex);
        assert!(a["held"].is_null() && a["address"] == "alex@example.org", "{a}");
        assert_eq!(a["subject"], "Venue AV: you're named as the owner");
        assert_eq!(row(&rows, sam)["body"], "Alex owns Venue AV. You're the backup: if it goes quiet, it comes to you.");

        // C3: the ledger never sees an address, before or after the carrier reports.
        record_delivery(&s, report(&id, opened, alex, true)).await.unwrap();
        let dup = record_delivery(&s, report(&id, opened, alex, true)).await.unwrap_err();
        assert_eq!(dup.status, StatusCode::CONFLICT, "one successful send per party per entry");
        {
            let l = s.ledger.lock().await;
            let all = serde_json::to_string(l.entries()).unwrap();
            assert!(!all.contains("@example.org"), "an address reached the ledger");
        }
        let rows = nudges(&s).await;
        assert_eq!(rows.len(), 1, "alex's is delivered: {rows:?}");
        assert_eq!(rows[0]["party"]["party_id"], sam.to_string());

        // Silence moves it to the backup: the opening is superseded, and the wording is C2's.
        let t0 = current(&s, &id).await.queue_since;
        sweep_once(&s, t0 + chrono::Duration::hours(49)).await.unwrap();
        let esc = current(&s, &id).await.escalations[0].index;
        let rows = nudges(&s).await;
        assert_eq!(rows.len(), 1, "{rows:?}");
        assert_eq!((rows[0]["about_index"].as_u64(), rows[0]["party"]["party_id"].as_str()),
            (Some(esc), Some(sam.to_string().as_str())));
        assert_eq!(rows[0]["body"], "Venue AV. Not yet acknowledged by Alex. You're the backup, so it's with you now.");
    }

    #[tokio::test]
    async fn the_cap_holds_a_party_after_three_attempts_and_failures_count() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        address(&s, alex, "alex@example.org").await;
        address(&s, sam, "sam@example.org").await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let opened = current(&s, &id).await.opened_index;
        for _ in 0..commitments::NUDGE_CAP_PER_DAY {
            record_delivery(&s, report(&id, opened, sam, false)).await.unwrap();
        }
        let rows = nudges(&s).await;
        assert_eq!(row(&rows, sam)["held"], "capped", "a bad address must not be retried without end");
        assert!(row(&rows, alex)["held"].is_null(), "the cap is per party");

        // One listing never offers a party more than its remaining budget across commitments.
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        address(&s, alex, "alex@example.org").await;
        address(&s, sam, "sam@example.org").await;
        for _ in 0..4 {
            open(&s, member(alex), member(sam), role).await.unwrap();
        }
        let rows = nudges(&s).await;
        let sendable = rows.iter().filter(|r| r["party"]["party_id"] == sam.to_string() && r["held"].is_null()).count();
        assert_eq!(sendable, commitments::NUDGE_CAP_PER_DAY);
    }

    #[tokio::test]
    async fn the_leads_hear_when_it_reaches_them_and_an_erased_address_holds_it() {
        let (_tmp, s, alex, sam, lee, role) = chapter().await;
        address(&s, lee, "lee@example.org").await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let t0 = current(&s, &id).await.queue_since;
        sweep_once(&s, t0 + chrono::Duration::hours(73)).await.unwrap();
        let rows = nudges(&s).await;
        assert_eq!(rows.len(), 1, "only the latest step is owed: {rows:?}");
        let r = row(&rows, lee);
        assert!(r["held"].is_null(), "{r}");
        assert_eq!(r["body"], "Venue AV. Not yet acknowledged by Sam. It has reached the leads.");

        admin_member_address_erase(State(s.clone()), ConnectInfo("127.0.0.1:1".parse().unwrap()),
            Path(lee.to_string())).await.unwrap();
        assert_eq!(row(&nudges(&s).await, lee)["held"], "no_address");
    }

    #[tokio::test]
    async fn a_delivery_report_names_a_party_of_the_commitment_and_a_means() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let opened = current(&s, &id).await.opened_index;
        let before = s.ledger.lock().await.len();
        assert_eq!(record_delivery(&s, report(&id, opened, Uuid::new_v4(), true)).await.unwrap_err().status,
            StatusCode::BAD_REQUEST);
        let mut addr = report(&id, opened, sam, true);
        addr.channel = "sam@example.org".into();
        assert_eq!(record_delivery(&s, addr).await.unwrap_err().status, StatusCode::BAD_REQUEST);
        assert_eq!(record_delivery(&s, report(&id, opened + 1000, sam, true)).await.unwrap_err().status,
            StatusCode::BAD_REQUEST);
        assert_eq!(record_delivery(&s, report("nope", opened, sam, true)).await.unwrap_err().status,
            StatusCode::NOT_FOUND);
        assert_eq!(s.ledger.lock().await.len(), before, "a refused report witnesses nothing");
        assert_eq!(set_member_address(&s, &Uuid::new_v4().to_string(),
            MemberAddressBody { address: "x@example.org".into() }).await.unwrap_err().status, StatusCode::NOT_FOUND);
    }

    // ---- K4: movement links ----

    #[test]
    fn a_link_reads_back_only_as_minted_and_only_until_it_expires() {
        let key = [7u8; 32];
        let now = Utc::now();
        let t = mint_link(&key, "c1", "p1", now + chrono::Duration::days(1));
        let claim = read_link(&key, &t, now).unwrap();
        assert_eq!((claim.commitment_id.as_str(), claim.party_id.as_str()), ("c1", "p1"));
        assert_eq!(claim.digest.len(), commitments::LINK_DIGEST_LEN);
        // The digest is the token's SHA-256, cut to 128 bits: neither the token nor a piece of it.
        // (It once asserted the digest held no "c1"; a random 32-hex string does ~11% of the time.)
        use sha2::Digest;
        assert_eq!(claim.digest, hex::encode(sha2::Sha256::digest(t.as_bytes()))[..commitments::LINK_DIGEST_LEN]);
        assert!(!t.contains(&claim.digest), "the digest is not the token");

        assert_eq!(read_link(&key, &t, now + chrono::Duration::days(1)), Err(LinkError::Expired));
        assert_eq!(read_link(&[8u8; 32], &t, now), Err(LinkError::Invalid), "another hub's key");
        // Someone else's party id under this link's MAC.
        assert_eq!(read_link(&key, &t.replacen(".p1.", ".p2.", 1), now), Err(LinkError::Invalid));
        // A later expiry under this link's MAC.
        let (payload, tag) = t.rsplit_once('.').unwrap();
        let (head, exp) = payload.rsplit_once('.').unwrap();
        let stretched = format!("{head}.{}.{tag}", exp.parse::<i64>().unwrap() + 86_400);
        assert_eq!(read_link(&key, &stretched, now), Err(LinkError::Invalid));
        // A one-byte prefix of the right MAC: `verify_truncated_left` alone would accept it.
        assert_eq!(read_link(&key, &format!("{payload}.{}", &tag[..2]), now), Err(LinkError::Invalid));
        assert_eq!(read_link(&key, "nonsense", now), Err(LinkError::Invalid));
        // The same MAC in capitals decodes to the same bytes, and would carry another digest.
        assert_eq!(read_link(&key, &format!("{payload}.{}", tag.to_uppercase()), now), Err(LinkError::Invalid),
            "one link, one spelling (Legion, #957)");
    }

    async fn call(s: &RestState, method: &str, path: &str) -> (StatusCode, String) {
        use tower::ServiceExt;
        let req = axum::http::Request::builder().method(method).uri(path)
            .body(axum::body::Body::empty()).unwrap();
        let resp = crate::rest::router(s.clone()).oneshot(req).await.unwrap();
        let status = resp.status();
        let bytes = axum::body::to_bytes(resp.into_body(), usize::MAX).await.unwrap();
        (status, String::from_utf8_lossy(&bytes).into_owned())
    }

    async fn link_for(s: &RestState, id: &str, party: Uuid) -> String {
        let key = {
            let _serial = COMMITMENT_LOCK.lock().await;
            link_key_or_create(&s.paths.root).unwrap()
        };
        mint_link(&key, id, &party.to_string(), Utc::now() + chrono::Duration::days(LINK_TTL_DAYS))
    }

    fn last(entries: &[hub_lib::ledger::LedgerEntry]) -> &HubEvent {
        &entries.last().unwrap().event
    }

    #[tokio::test]
    async fn opening_a_link_writes_nothing_and_offers_the_partys_answers() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let token = link_for(&s, &id, alex).await;
        let before = s.ledger.lock().await.len();
        let (status, page) = call(&s, "GET", &format!("/c/{token}")).await;
        assert_eq!(status, StatusCode::OK, "{page}");
        assert_eq!(s.ledger.lock().await.len(), before, "a mail scanner fetching the link moved something");
        assert!(page.contains("You're the owner. Your backup is Sam."), "{page}");
        for act in ["acknowledge", "update", "done", "stuck", "handoff"] {
            assert!(page.contains(&format!("action=\"{token}/{act}\"")), "{act} missing: {page}");
        }
        assert!(!page.contains("/take\""), "the owner takes nothing over: {page}");
        assert!(page.contains("Hand it to Sam"));

        // A link this hub did not make, and a hub that has made none, both read as not found.
        let (status, _) = call(&s, "GET", &format!("/c/{}", mint_link(&[1u8; 32], &id, &alex.to_string(),
            Utc::now() + chrono::Duration::days(1)))).await;
        assert_eq!(status, StatusCode::NOT_FOUND);
        let (_tmp2, bare) = fresh_rest_state(None).await;
        assert_eq!(call(&bare, "GET", &format!("/c/{token}")).await.0, StatusCode::NOT_FOUND);
    }

    #[tokio::test]
    async fn a_link_acknowledges_once_and_the_entry_carries_via_link_and_the_digest() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let token = link_for(&s, &id, alex).await;
        let digest = read_link(&read_link_key(&s.paths.root).unwrap().unwrap(), &token, Utc::now()).unwrap().digest;

        let (status, page) = call(&s, "POST", &format!("/c/{token}/acknowledge")).await;
        assert_eq!(status, StatusCode::OK, "{page}");
        {
            let l = s.ledger.lock().await;
            assert!(matches!(last(l.entries()), HubEvent::CommitmentAcknowledged { via: AckVia::Link,
                link_digest: Some(d), party_id, .. } if *d == digest && *party_id == alex.to_string()));
            let all = serde_json::to_string(l.entries()).unwrap();
            assert!(!all.contains(&token), "the token reached the ledger");
        }
        assert!(current(&s, &id).await.owner_acknowledged(), "a link ack is the owner's word, by possession");

        let before = s.ledger.lock().await.len();
        let (status, _) = call(&s, "POST", &format!("/c/{token}/acknowledge")).await;
        assert_eq!(status, StatusCode::CONFLICT, "acknowledge is offered once");
        assert_eq!(s.ledger.lock().await.len(), before);
        assert!(!call(&s, "GET", &format!("/c/{token}")).await.1.contains("/acknowledge\""));
    }

    #[tokio::test]
    async fn the_owner_hands_to_the_backup_and_each_link_follows_the_new_roles() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let (alex_link, sam_link) = (link_for(&s, &id, alex).await, link_for(&s, &id, sam).await);

        assert_eq!(call(&s, "POST", &format!("/c/{alex_link}/handoff")).await.0, StatusCode::OK);
        let c = current(&s, &id).await;
        assert_eq!((c.owner.party_id.clone(), c.backup.party_id.clone()), (sam.to_string(), alex.to_string()));
        assert_eq!(c.basis, commitments::Basis::NamedByOther, "Alex's handoff is not Sam's word");

        // Alex's own link now speaks as the backup: no second handoff, no stuck.
        let before = s.ledger.lock().await.len();
        assert_eq!(call(&s, "POST", &format!("/c/{alex_link}/handoff")).await.0, StatusCode::CONFLICT);
        assert_eq!(call(&s, "POST", &format!("/c/{alex_link}/stuck")).await.0, StatusCode::CONFLICT);
        assert_eq!(s.ledger.lock().await.len(), before, "a refused answer reached the ledger");
        assert!(call(&s, "GET", &format!("/c/{alex_link}")).await.1.contains("Sam owns this. You're the backup."));

        // Sam's link, minted when Sam was the backup, now offers the owner's answers.
        let (_, page) = call(&s, "GET", &format!("/c/{sam_link}")).await;
        assert!(page.contains("You're the owner.") && page.contains("/stuck\""), "{page}");
    }

    #[tokio::test]
    async fn a_lead_takes_over_by_link_and_the_dropped_owner_can_no_longer_answer() {
        let (_tmp, s, alex, sam, lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let (alex_link, lee_link) = (link_for(&s, &id, alex).await, link_for(&s, &id, lee).await);
        assert!(call(&s, "GET", &format!("/c/{lee_link}")).await.1.contains("You're one of the leads."));

        assert_eq!(call(&s, "POST", &format!("/c/{lee_link}/take")).await.0, StatusCode::OK);
        let c = current(&s, &id).await;
        assert_eq!((c.owner.party_id.clone(), c.basis), (lee.to_string(), commitments::Basis::TakenBySelf),
            "a take-over through Lee's own link is Lee's act");
        {
            let l = s.ledger.lock().await;
            assert!(matches!(last(l.entries()), HubEvent::CommitmentMoved { via: AckVia::Link,
                link_digest: Some(_), move_kind: MoveKind::Handoff, .. }));
        }

        let before = s.ledger.lock().await.len();
        assert_eq!(call(&s, "POST", &format!("/c/{alex_link}/update")).await.0, StatusCode::FORBIDDEN);
        assert_eq!(s.ledger.lock().await.len(), before);
        assert!(call(&s, "GET", &format!("/c/{alex_link}")).await.1.contains("no longer named"));
    }

    #[tokio::test]
    async fn stuck_and_done_by_link_and_a_closed_job_takes_no_answers() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let (alex_link, sam_link) = (link_for(&s, &id, alex).await, link_for(&s, &id, sam).await);

        assert_eq!(call(&s, "POST", &format!("/c/{alex_link}/stuck")).await.0, StatusCode::OK);
        let c = current(&s, &id).await;
        assert_eq!((c.queue, c.escalations.len()), (commitments::QueuePos::Backup, 1), "stuck escalates as in K1");

        assert_eq!(call(&s, "POST", &format!("/c/{sam_link}/done")).await.0, StatusCode::OK);
        {
            let l = s.ledger.lock().await;
            assert!(matches!(last(l.entries()), HubEvent::CommitmentResolved { outcome: Outcome::Done,
                link_digest: Some(_), by, .. } if *by == sam.to_string()));
        }
        let before = s.ledger.lock().await.len();
        assert_eq!(call(&s, "POST", &format!("/c/{alex_link}/update")).await.0, StatusCode::CONFLICT);
        assert_eq!(call(&s, "POST", &format!("/c/{alex_link}/bogus")).await.0, StatusCode::NOT_FOUND);
        assert_eq!(s.ledger.lock().await.len(), before);
        assert!(call(&s, "GET", &format!("/c/{alex_link}")).await.1.contains("This is closed: done"));
    }

    #[tokio::test]
    async fn a_nudge_carries_a_link_for_its_own_party() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        address(&s, alex, "alex@example.org").await;
        let key = { let _serial = COMMITMENT_LOCK.lock().await; link_key_or_create(&s.paths.root).unwrap() };
        let minter = LinkMinter { base: "https://hub.example.org", key: &key };
        let state = { let l = s.ledger.lock().await; s.projected(&l) };
        let rows = due_nudges(&state, &load_book(&s).unwrap(), Utc::now(), Some(&minter));
        let a = row(&rows, alex);
        let link = a["link"].as_str().unwrap();
        let token = link.strip_prefix("https://hub.example.org/c/").expect("the public base");
        let claim = read_link(&key, token, Utc::now()).unwrap();
        assert_eq!((claim.commitment_id, claim.party_id), (id.clone(), alex.to_string()));
        assert!(a["body"].as_str().unwrap().ends_with(link), "{a}");
        // The backup's row carries the backup's link, not the owner's.
        let sam_link = row(&rows, sam)["link"].as_str().unwrap().rsplit('/').next().unwrap().to_string();
        assert_eq!(read_link(&key, &sam_link, Utc::now()).unwrap().party_id, sam.to_string());
        assert!(nudges(&s).await.iter().all(|r| r["link"].is_null()), "no base, no link");
    }

    /// Legion, #957 finding 2: Sam acknowledges as backup through his link, then the operator hands
    /// the job to Sam. The handoff clears Sam's acknowledgement, but his link has used its one
    /// acknowledgement, so the page must not offer one that the ledger will refuse.
    #[tokio::test]
    async fn a_link_that_has_acknowledged_does_not_offer_it_again_after_a_handoff() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let sam_link = link_for(&s, &id, sam).await;
        assert_eq!(call(&s, "POST", &format!("/c/{sam_link}/acknowledge")).await.0, StatusCode::OK);
        move_commitment(&s, &id, MoveBody { by: alex.to_string(), move_kind: MoveKind::Handoff,
            to: Some(member(sam)), note_ref: None }).await.unwrap();
        assert!(!current(&s, &id).await.acknowledged.contains_key(&sam.to_string()), "the handoff cleared it");

        let (_, page) = call(&s, "GET", &format!("/c/{sam_link}")).await;
        assert!(page.contains("You're the owner.") && !page.contains("/acknowledge\""), "{page}");
        let before = s.ledger.lock().await.len();
        assert_eq!(call(&s, "POST", &format!("/c/{sam_link}/acknowledge")).await.0, StatusCode::CONFLICT);
        assert_eq!(s.ledger.lock().await.len(), before);
        // A fresh link (K4b sends one to a new owner) can still give Sam's word. Minted in the
        // same second with the same expiry it would be the same link, so give it another.
        let key = read_link_key(&s.paths.root).unwrap().unwrap();
        let fresh = mint_link(&key, &id, &sam.to_string(), Utc::now() + chrono::Duration::days(LINK_TTL_DAYS - 1));
        assert_eq!(call(&s, "POST", &format!("/c/{fresh}/acknowledge")).await.0, StatusCode::OK);
        assert!(current(&s, &id).await.owner_acknowledged());
    }

    /// Legion, #957 nit: a key anyone can read lets anyone mint any party's link. Refuse it.
    #[tokio::test]
    async fn a_link_key_others_can_read_is_refused() {
        use std::os::unix::fs::PermissionsExt;
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let token = link_for(&s, &id, alex).await;
        assert_eq!(call(&s, "GET", &format!("/c/{token}")).await.0, StatusCode::OK);
        std::fs::set_permissions(link_key_path(&s.paths.root), std::fs::Permissions::from_mode(0o644)).unwrap();
        let (status, page) = call(&s, "GET", &format!("/c/{token}")).await;
        assert_eq!(status, StatusCode::INTERNAL_SERVER_ERROR);
        assert!(!page.contains("chmod") && !page.contains(&s.paths.root.display().to_string()), "{page}");
        assert!(list_nudges(&s, Some("https://hub.example.org".into())).await.is_err(), "nor is one minted with it");
    }

    /// Legion, #957 nit: the key is made by the first listing that carries a link, not by any.
    #[tokio::test]
    async fn the_link_key_is_made_only_when_a_link_is_owed() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let base = Some("https://hub.example.org".to_string());
        let empty = list_nudges(&s, base.clone()).await.unwrap();
        assert_eq!((empty["links"].as_str(), empty["nudges"].as_array().unwrap().len()), (Some("on"), 0));
        assert!(read_link_key(&s.paths.root).unwrap().is_none(), "no row, no key");
        open(&s, member(alex), member(sam), role).await.unwrap();
        let rows = list_nudges(&s, base).await.unwrap();
        assert!(rows["nudges"][0]["link"].as_str().unwrap().starts_with("https://hub.example.org/c/"));
        assert!(read_link_key(&s.paths.root).unwrap().is_some());
        assert_eq!(list_nudges(&s, None).await.unwrap()["links"], "off: set HUB_PUBLIC_BASE_URL");
    }

    /// K4b end to end: a lead takes the job over by link, the owner it was taken from is told,
    /// and the carrier's report of that send is accepted for that entry only.
    #[tokio::test]
    async fn an_owner_a_take_over_drops_is_told_and_the_report_names_them() {
        let (_tmp, s, alex, sam, lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let opened = current(&s, &id).await.opened_index;
        address(&s, alex, "alex@example.org").await;
        let lee_link = link_for(&s, &id, lee).await;
        assert_eq!(call(&s, "POST", &format!("/c/{lee_link}/take")).await.0, StatusCode::OK);
        let handed = current(&s, &id).await.handoffs[0].index;

        let rows = nudges(&s).await;
        assert_eq!(rows.len(), 1, "only Alex is owed: {rows:?}");
        let a = row(&rows, alex);
        assert_eq!((a["about"].as_str(), a["about_index"].as_u64()), (Some("handed_away"), Some(handed)));
        assert_eq!(a["body"], "Venue AV is now Lee's, so it's off your list.");

        let refused = record_delivery(&s, report(&id, opened, alex, true)).await.unwrap_err();
        assert_eq!(refused.status, StatusCode::BAD_REQUEST, "Alex is no longer a party to the opening");
        record_delivery(&s, report(&id, handed, alex, true)).await.unwrap();
        assert!(nudges(&s).await.is_empty());
    }

    async fn page(s: &RestState, path: &str) -> (StatusCode, axum::http::HeaderMap, String) {
        use tower::ServiceExt;
        let req = axum::http::Request::builder().uri(path).body(axum::body::Body::empty()).unwrap();
        let resp = crate::rest::router(s.clone()).oneshot(req).await.unwrap();
        let (status, headers) = (resp.status(), resp.headers().clone());
        let bytes = axum::body::to_bytes(resp.into_body(), usize::MAX).await.unwrap();
        (status, headers, String::from_utf8_lossy(&bytes).into_owned())
    }

    #[tokio::test]
    async fn pages_that_hold_a_key_or_act_for_a_party_run_only_their_own_files() {
        let (_tmp, s, alex, sam, _lee, role) = chapter().await;
        let id = open(&s, member(alex), member(sam), role).await.unwrap();
        let token = link_for(&s, &id, alex).await;
        let csp = super::super::KEY_PAGE_CSP;
        assert!(!csp.contains("unsafe") && csp.contains("script-src 'self'") && csp.contains("style-src 'self'"));
        for (path, sheet) in [
            ("/client".to_string(), "/client.css"),
            (format!("/c/{token}"), "/c.css"),
            ("/c/not-a-link".to_string(), "/c.css"),
        ] {
            let (_, headers, html) = page(&s, &path).await;
            assert_eq!(headers.get("content-security-policy").and_then(|v| v.to_str().ok()), Some(csp), "{path}");
            for inline in ["<style", "style=", "onclick", "<script>"] {
                assert!(!html.contains(inline), "{path} carries inline {inline}: {html}");
            }
            assert!(html.contains(&format!("<link rel=\"stylesheet\" href=\"{sheet}\">")), "{path}: {html}");
        }
        assert!(page(&s, "/client").await.2.contains("<script src=\"/client.js\"></script>"));
        // The script builds buttons too: those must not carry handlers or style either.
        for inline in ["style=", "onclick", "localStorage.setItem", "exportKey('jwk'"] {
            assert!(!super::super::CLIENT_JS.contains(inline), "client script carries {inline}");
        }
        for (path, kind) in [("/client.js", "text/javascript"), ("/client.css", "text/css"), ("/c.css", "text/css")] {
            let (status, headers, body) = page(&s, path).await;
            assert_eq!(status, StatusCode::OK, "{path}");
            assert!(headers["content-type"].to_str().unwrap().starts_with(kind), "{path}");
            assert!(!body.is_empty(), "{path}");
        }
    }

    /// The client's key store, run in node against real WebCrypto and a small in-memory
    /// IndexedDB (`js-tests/client_keystore.js`). Without node on PATH it says so and passes.
    #[test]
    fn the_client_moves_an_old_key_once_and_keeps_every_key_non_extractable() {
        let dir = tempfile::tempdir().unwrap();
        let js = dir.path().join("client.js");
        std::fs::write(&js, super::super::CLIENT_JS).unwrap();
        let harness = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("js-tests/client_keystore.js");
        let out = match std::process::Command::new("node").arg(&harness).arg(&js).output() {
            Ok(out) => out,
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
                eprintln!("SKIPPED: node is not on PATH, so the client key store went untested");
                return;
            }
            Err(e) => panic!("running node: {e}"),
        };
        let said = format!("{}{}", String::from_utf8_lossy(&out.stdout), String::from_utf8_lossy(&out.stderr));
        assert!(out.status.success(), "{said}");
        assert_eq!(said.matches("\nok ").count() + usize::from(said.starts_with("ok ")), 5, "{said}");
    }
}
