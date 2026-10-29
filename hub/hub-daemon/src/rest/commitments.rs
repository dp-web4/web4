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
    let move_kind = body.move_kind;
    let entry_index = checked_witness(s, HubEvent::CommitmentMoved {
        commitment_id: id.to_string(),
        by: body.by,
        // Every K1 move is the operator relaying it. K4/K5 write link and member_act.
        via: AckVia::Operator,
        move_kind,
        to: body.to,
        note_ref: body.note_ref,
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
    let entry_index = checked_witness(s, HubEvent::CommitmentResolved {
        commitment_id: id.to_string(),
        outcome: body.outcome,
        by: body.by,
        resolved_at: Utc::now(),
        owner_acknowledged: c.owner_acknowledged(),
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
pub(crate) fn due_nudges(state: &HubState, book: &ContactBook, now: DateTime<Utc>) -> Vec<serde_json::Value> {
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
            let (subject, body) = c.nudge_message(&t, &name);
            rows.push(serde_json::json!({
                "commitment_id": c.commitment_id,
                "about_index": t.about_index,
                "about": t.about,
                "party": party_view(state, book, &t.party),
                "address": address,
                "held": held,
                "subject": subject,
                "body": body,
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
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let book = load_book(&s)?;
    let rows = due_nudges(&state, &book, Utc::now());
    Ok(Json(serde_json::json!({ "cap_per_day": commitments::NUDGE_CAP_PER_DAY, "nudges": rows })))
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
    let party_of_it = body.party_id == c.owner.party_id || body.party_id == c.backup.party_id
        || leads_of(&state, c).iter().any(|l| l == &body.party_id);
    if !party_of_it {
        return Err(ApiError::bad_request(format!(
            "{} is not the owner, the backup or a lead of {}", body.party_id, body.commitment_id)));
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
            commitment_id: acked.clone(), party_id: sam.to_string(), via: AckVia::Link }).await;
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
        due_nudges(&state, &load_book(s).unwrap(), Utc::now())
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
}
