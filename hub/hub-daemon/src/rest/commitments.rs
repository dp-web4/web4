// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Commitments, slice K1 (hub/docs/PRD_COMMITMENTS.md §7): the operator's routes.
//!
//! - `POST /admin/api/commitments` opens one; `/:id/move`, `/:id/acknowledge` and `/:id/resolve`
//!   record what the operator was told; `GET /admin/api/commitments` lists them by queue.
//! - `/admin/api/contacts` is the contact book (C3): names and addresses held off the ledger,
//!   erasable.
//!
//! Every route is operator-plane only (loopback). Every write runs its checks and its witness
//! under [`COMMITMENT_LOCK`], so two writers cannot both pass a check only one of them may: the
//! loser of a resolution race is answered with what won (§4.1). K2's sweep takes the same lock.
use super::*;
use hub_lib::commitments::{
    self, AckVia, Commitment, Contact, ContactBook, MoveKind, Outcome, PartyKind, PartyRef, Refusal,
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
/// role or a seat within it, or the operator.
fn check_actor(s: &RestState, state: &HubState, c: &Commitment, by: &str) -> Result<(), ApiError> {
    if by == c.owner.party_id || by == c.backup.party_id || by == s.sovereign_lct_id.to_string() {
        return Ok(());
    }
    let lead = Uuid::parse_str(&c.leads_role).ok().map_or(false, |role| {
        Uuid::parse_str(by).map_or(false, |who| {
            state.roles.values().any(|r| {
                !r.retired && r.occupant == Some(who)
                    && (r.role_lct_id == role || r.parent_role_lct_id == Some(role))
            })
        })
    });
    if lead {
        Ok(())
    } else {
        Err(ApiError::bad_request(format!(
            "{by} is not the owner, the backup, a lead, or the operator of {}", c.commitment_id)))
    }
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
    check_actor(s, &state, &c, &body.by)?;
    if let Some(to) = &body.to {
        check_party(&state, &load_book(s)?, to, "to")?;
    }
    let move_kind = body.move_kind;
    let entry_index = checked_witness(s, HubEvent::CommitmentMoved {
        commitment_id: id.to_string(),
        by: body.by,
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
    check_actor(s, &state, &c, &body.by)?;
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
    let address = body.address.trim();
    let shaped = address.len() <= MAX_ADDRESS_LEN
        && !address.chars().any(|c| c.is_whitespace() || c.is_control())
        && address.split_once('@').map_or(false, |(l, d)| !l.is_empty() && d.contains('.'));
    if !shaped {
        return Err(ApiError::bad_request("address must be an email address".to_string()));
    }
    Ok((name.to_string(), address.to_string()))
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
}
