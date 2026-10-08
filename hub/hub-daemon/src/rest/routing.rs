// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Member-of routing, slice Hub A (hub/docs/PRD_MEMBER_OF_ROUTING.md rev 7: H1, H2, H4).
//!
//! - `POST /v1/hubs/:hub_id/routers` — a machine's hestia registers (or retires) itself as the
//!   router for its canonical LCT, presenting the dual-signed router-interface certificate.
//! - `POST /v1/hubs/:hub_id/member-of` — that router reports (or withdraws) "LCT-x is member-of
//!   LCT-y", carrying x's own consent signature.
//! - reads: the members-only `member_of` channel tool, and the operator plane.
//!
//! Every write is a signed envelope verified against the key the HUB pinned for the signer, and
//! every refusal witnesses nothing. Delivery along these edges (H3) is slice Hub B.
use super::*;
use hub_lib::ids::{CanonicalLctId, HubMemberId};
use hub_lib::events::MemberOfWithdrawnBy;
use hub_lib::routing::{route_target, Consent, RouterCert, REPORT_DOMAIN, WITHDRAW_DOMAIN};

#[derive(Deserialize)]
pub(super) struct RouterPayload {
    /// `router_register` | `router_retire`.
    action: String,
    #[serde(default)]
    certificate: Option<RouterCert>,
    #[serde(default)]
    router_lct: Option<String>,
}

#[derive(Deserialize)]
pub(super) struct MemberOfPayload {
    /// `member_of_report` | `member_of_withdraw`.
    action: String,
    member: String,
    #[serde(default)]
    of: Option<String>,
    #[serde(default)]
    consent: Option<Consent>,
}

/// Serialises every routing write: the projection checks (monotonic `issued_at` marks, one router per
/// LCT, router-is-never-a-child) and the `witness_event` they guard run under one lock, so two
/// concurrent reports cannot both pass a check that only one of them may (CBP, #899 review).
static ROUTING_LOCK: tokio::sync::Mutex<()> = tokio::sync::Mutex::const_new(());

fn forbidden(msg: impl Into<String>) -> ApiError {
    ApiError { status: StatusCode::FORBIDDEN, message: msg.into() }
}

fn conflict(msg: impl Into<String>) -> ApiError {
    ApiError { status: StatusCode::CONFLICT, message: msg.into() }
}

fn canonical(field: &str, v: &str) -> Result<CanonicalLctId, ApiError> {
    CanonicalLctId::parse(v).map_err(|e| ApiError::bad_request(format!("{field}: {e}")))
}

/// Verify the envelope against the LIVE resolver (the hub's own pins), returning the signer.
async fn verified_signer(s: &RestState, envelope: &SignedEnvelope) -> Result<Uuid, ApiError> {
    let resolver = s.resolver.read().await;
    verify_envelope(envelope, &s.nonces, &*resolver, Utc::now())?;
    Ok(envelope.signer_lct_id)
}

/// The key the hub pinned for `member`, as bytes — from the member pins or the council pins, and
/// compared as decoded bytes, never as hex spellings (the C9/C10 lessons of #883).
fn pinned_key(state: &HubState, member: Uuid) -> Option<[u8; 32]> {
    let hex_key = state.member_pubkeys.get(&member).or_else(|| state.council_pubkeys.get(&member))?;
    hex::decode(hex_key).ok()?.try_into().ok()
}

/// `POST /v1/hubs/:hub_id/routers` — register or retire this member as a machine's router.
///
/// surface: POST /v1/hubs/:hub_id/routers   act: RouterRegistered / RouterRetired
/// S: med [construct: a router receives every routed member's mail]
/// R: n/a [construct: public plane; identity-gated by the pinned key]
/// W: pass [construct: verify_envelope against the hub's pin; certificate double-signed]
/// O: pass [construct: ROUTING_LOCK; H1.7 mark, H1.8, one LCT per member, all before witness_event]
/// A: pass [construct: signed chain entry naming router LCT and member]
/// V: n/a [construct: a member registering itself; law may still govern `router_registered`]
/// verdict: PASS
pub(super) async fn submit_router(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<serde_json::Value>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!("hub id {hub_id} does not match this hub {}", s.hub_id)));
    }
    let p: RouterPayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("router payload not parseable: {e}")))?;
    let signer = verified_signer(&s, &envelope).await?;
    let _serial = ROUTING_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };

    match p.action.as_str() {
        "router_register" => {
            let cert = p.certificate.ok_or_else(|| ApiError::bad_request("router_register requires `certificate`"))?;
            let v = cert.verify(s.hub_id, Utc::now()).map_err(|e| ApiError::bad_request(e.to_string()))?;
            if v.member.as_uuid() != signer {
                return Err(forbidden("the certificate's hub member must submit it itself"));
            }
            if pinned_key(&state, signer) != Some(v.member_key.to_bytes()) {
                return Err(conflict("the certificate's member key is not the key this hub has pinned for that member"));
            }
            let receipts = {
                let cache = s.notifications.lock().await;
                let store = s.open_store().await.map_err(ApiError::internal)?;
                let cached = cache.get(&signer).map(Vec::as_slice).unwrap_or(&[]);
                s.load_mailbox_record(&*store, signer, cached).await.map_err(ApiError::internal)?.is_receipts()
            };
            if !receipts {
                // One destructive drain would lose every child's mail at once (PRD D5).
                return Err(conflict(format!(
                    "{signer} is not enrolled for receipt mailbox delivery; a router must be (operator act)")));
            }
            // H1.7: two members holding valid certificates for one router LCT cannot flip it back and
            // forth — a registration must be strictly newer than any EVER registered for this LCT. The
            // mark survives `RouterRetired`, so a retire does not readmit an older certificate.
            if let Some(mark) = state.router_mark.get(&v.router_lct) {
                if v.issued_at <= *mark {
                    return Err(conflict(format!(
                        "a certificate issued at {mark} has already been registered for {}; a registration must be newer",
                        v.router_lct)));
                }
            }
            // Rev 7: a member holds at most one router LCT. A different one is refused — retire first —
            // so nothing is ever replaced silently.
            if let Some((held, _)) = state.routers.iter().find(|(l, r)| r.member == v.member && **l != v.router_lct) {
                return Err(conflict(format!("{signer} already holds router {held}; retire it before registering another")));
            }
            // H1.8: a router is never a child (hub edges are one level, D6).
            if state.member_of.contains_key(&v.router_lct) {
                return Err(conflict(format!("{} is member-of another router; a router is never a child", v.router_lct)));
            }
            let replaced = state.routers.get(&v.router_lct).map(|r| r.member).filter(|m| *m != v.member);
            if let Some(prev) = replaced {
                // PRD-permitted re-key to a different member; no child is stranded, but the operator
                // should see the router change hands.
                tracing::warn!(router = %v.router_lct, from = %prev, to = %signer, "router re-keyed to a different member");
            }
            let entry_index = witness_event(&s, HubEvent::RouterRegistered {
                router_lct: v.router_lct.to_string(), member: signer, issued_at: v.issued_at,
            }).await?;
            Ok(Json(serde_json::json!({
                "registered": true, "router_lct": v.router_lct, "member": signer,
                "replaced_member": replaced, "entry_index": entry_index,
            })))
        }
        "router_retire" => {
            let lct = canonical("router_lct", p.router_lct.as_deref().unwrap_or(""))?;
            match state.routers.get(&lct) {
                Some(r) if r.member.as_uuid() == signer => {}
                Some(_) => return Err(forbidden("only the registered router member may retire it")),
                None => return Err(ApiError::not_found(format!("{lct} has no registered router"))),
            }
            retire(&s, &state, &lct, "router").await
        }
        other => Err(ApiError::bad_request(format!("unknown router action '{other}'"))),
    }
}

/// Witness `RouterRetired`, LOUDLY (rev 2): its current children now take H3's retired-router path
/// (their own receipt membership, else 409), so the operator is told who they are.
async fn retire(s: &RestState, state: &HubState, lct: &CanonicalLctId, by: &str)
    -> Result<Json<serde_json::Value>, ApiError> {
    let children: Vec<&CanonicalLctId> = state.member_of.iter().filter(|(_, p)| *p == lct).map(|(x, _)| x).collect();
    let entry_index = witness_event(s, HubEvent::RouterRetired { router_lct: lct.to_string() }).await?;
    tracing::warn!(router = %lct, by, children = children.len(),
        "ROUTER RETIRED: its {} member-of child(ren) now get their own receipt mailbox or 409 until a router is registered again: {:?}",
        children.len(), children);
    Ok(Json(serde_json::json!({
        "retired": true, "router_lct": lct, "entry_index": entry_index, "children_affected": children,
    })))
}

/// Rev 7: when a member's membership ends, every router it holds is retired by a witnessed, loud
/// `RouterRetired` BEFORE the removal — never silently dropped from the projection. Called by every
/// daemon path that ends a membership (operator removal, self-withdrawal).
///
/// Returns the `ROUTING_LOCK` guard: the caller must hold it until the removal itself is witnessed
/// (and the live resolver evicted), or a `router_register` from the departing member could land in
/// between and leave a router held by a non-member (Legion, #899 re-review).
pub(super) async fn retire_routers_of(s: &RestState, member: Uuid)
    -> Result<(tokio::sync::MutexGuard<'static, ()>, Vec<serde_json::Value>), ApiError> {
    let serial = ROUTING_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let held: Vec<CanonicalLctId> = state.routers.iter()
        .filter(|(_, r)| r.member.as_uuid() == member).map(|(l, _)| l.clone()).collect();
    let mut out = Vec::new();
    for lct in held {
        out.push(retire(s, &state, &lct, "membership ended").await?.0);
    }
    Ok((serial, out))
}

/// `POST /admin/api/routers/:lct/retire` — the operator retires a router (loopback).
pub(super) async fn admin_retire_router(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(lct): Path<String>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let lct = canonical("lct", &lct)?;
    let _serial = ROUTING_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    if !state.routers.contains_key(&lct) {
        return Err(ApiError::not_found(format!("{lct} has no registered router")));
    }
    retire(&s, &state, &lct, "operator").await
}

/// `POST /v1/hubs/:hub_id/member-of` — report or withdraw "LCT-x is member-of LCT-y".
///
/// surface: POST /v1/hubs/:hub_id/member-of   act: MemberOfReported / MemberOfWithdrawn
/// S: med [construct: an edge redirects x's mail to y's router (slice Hub B)]
/// R: n/a [construct: public plane; identity-gated]
/// W: pass [construct: signer = y's registered router (pinned key); x's consent by x's binding key]
/// O: pass [construct: ROUTING_LOCK; one-level, consent and strict-mark checks before witness_event]
/// A: pass [construct: signed chain entry carrying the member's consent as evidence]
/// V: n/a [construct: law may govern `member_of_reported`]
/// verdict: PASS
pub(super) async fn submit_member_of(
    State(s): State<RestState>,
    Path(hub_id): Path<Uuid>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<serde_json::Value>, ApiError> {
    if hub_id != s.hub_id {
        return Err(ApiError::not_found(format!("hub id {hub_id} does not match this hub {}", s.hub_id)));
    }
    let p: MemberOfPayload = serde_json::from_value(envelope.payload.clone())
        .map_err(|e| ApiError::bad_request(format!("member-of payload not parseable: {e}")))?;
    let signer = HubMemberId::from_uuid(verified_signer(&s, &envelope).await?);
    let _serial = ROUTING_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let x = canonical("member", &p.member)?;

    match p.action.as_str() {
        "member_of_report" => {
            let y = canonical("of", p.of.as_deref().unwrap_or(""))?;
            if state.routers.get(&y).map(|r| r.member) != Some(signer) {
                return Err(forbidden(format!("only the registered router of {y} may report members of it")));
            }
            if x == y || state.routers.contains_key(&x) {
                return Err(conflict(format!("{x} is a router (or {y} itself); a router is never a child")));
            }
            let consent = p.consent.ok_or_else(|| forbidden("member_of_report requires the member's `consent`"))?;
            let at = consent.verify(REPORT_DOMAIN, s.hub_id, &x, &y, Utc::now()).map_err(|e| forbidden(e.to_string()))?;
            let previous = state.member_of.get(&x).cloned();
            if previous.as_ref() == Some(&y) {
                return Ok(Json(serde_json::json!({
                    "reported": true, "already": true, "member": x, "of": y,
                    "entry_index": state.member_of_at.get(&x),
                })));
            }
            // Strictly increasing per member (report or self-withdrawal): a former parent cannot
            // replay x's earlier consent inside the window to pull x back after a move.
            if let Some(mark) = state.member_of_mark.get(&x) {
                if at <= *mark {
                    return Err(conflict(format!("consent issued_at must be later than {x}'s last accepted ({mark})")));
                }
            }
            let entry_index = witness_event(&s, HubEvent::MemberOfReported {
                member: x.to_string(), of: y.to_string(), consent,
            }).await?;
            Ok(Json(serde_json::json!({
                "reported": true, "member": x, "of": y, "superseded": previous, "entry_index": entry_index,
            })))
        }
        "member_of_withdraw" => {
            let parent = state.member_of.get(&x)
                .ok_or_else(|| ApiError::not_found(format!("{x} has no member-of edge")))?.clone();
            let by = match p.consent {
                // The member itself, over the separate withdrawal domain string; any member may carry it.
                Some(consent) => {
                    let at = consent.verify(WITHDRAW_DOMAIN, s.hub_id, &x, &parent, Utc::now())
                        .map_err(|e| forbidden(e.to_string()))?;
                    if state.member_of_mark.get(&x).is_some_and(|mark| at <= *mark) {
                        return Err(conflict(format!("withdrawal issued_at must be later than {x}'s last accepted")));
                    }
                    MemberOfWithdrawnBy::Member { of: parent.to_string(), consent }
                }
                None => {
                    if state.routers.get(&parent).map(|r| r.member) != Some(signer) {
                        return Err(forbidden(format!(
                            "only the registered router of {parent}, or {x} itself with its withdrawal signature, may withdraw this edge")));
                    }
                    MemberOfWithdrawnBy::Router { member: signer.as_uuid() }
                }
            };
            let entry_index = witness_event(&s, HubEvent::MemberOfWithdrawn { member: x.to_string(), by }).await?;
            Ok(Json(serde_json::json!({ "withdrawn": true, "member": x, "of": parent, "entry_index": entry_index })))
        }
        other => Err(ApiError::bad_request(format!("unknown member-of action '{other}'"))),
    }
}

/// The H4 read body for one LCT: its edge (bare, with the witnessing entry) and where its mail
/// would route today. Shared by the channel tool and the operator plane.
pub(super) fn member_of_view(state: &HubState, lct: &CanonicalLctId) -> serde_json::Value {
    serde_json::json!({
        "lct": lct,
        "member_of": state.member_of.get(lct),
        "pubkey_hex": state.member_of_consent_key.get(lct),
        "witnessed_at": state.member_of_at.get(lct),
        "routes_to": route_target(state, lct).map(|(router_lct, member)| serde_json::json!({
            "router_lct": router_lct, "member": member,
        })),
    })
}

/// `GET /admin/api/member-of/:lct` — operator plane (loopback).
pub(super) async fn admin_member_of(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(lct): Path<String>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let x = canonical("lct", &lct)?;
    let ledger = s.ledger.lock().await;
    Ok(Json(member_of_view(&s.projected(&ledger), &x)))
}

/// `GET /admin/api/routers` — every registered router and its member (operator plane).
pub(super) async fn admin_routers(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    let ledger = s.ledger.lock().await;
    let state = s.projected(&ledger);
    let routers: Vec<_> = state.routers.iter()
        .map(|(lct, r)| serde_json::json!({ "router_lct": lct, "member": r.member, "issued_at": r.issued_at }))
        .collect();
    Ok(Json(serde_json::json!({ "routers": routers })))
}

/// A child's share of its router's receipt mailbox (PRD H3, rev 6): ⌊MAX / N⌋, minimum 1, where N is
/// the number of current member-of children of the router `router_member` serves. share × N never
/// exceeds the mailbox total, so dead children cannot reach the router-wide 507.
pub(super) fn routed_share(state: &HubState, router_member: Uuid) -> usize {
    let lcts: Vec<&CanonicalLctId> = state.routers.iter()
        .filter(|(_, r)| r.member.as_uuid() == router_member).map(|(l, _)| l).collect();
    let n = state.member_of.values().filter(|p| lcts.contains(p)).count().max(1);
    (MAX_NOTICES_PER_MEMBER / n).max(1)
}

/// The key a hub-sealed notice for child `lct` is sealed to (PRD H3 Sealing, Hub B1), and the
/// `sealed_to` label. The child's own hub pin when it is a member (`member` given and pinned),
/// else its current edge's consent key (a pure-LCT child). NEVER the router's key: the router
/// relays ciphertext it cannot open. `None` when neither exists — the caller must refuse (409),
/// never fall back to sealing to the router.
pub(super) fn seal_key_for(state: &HubState, member: Option<Uuid>, lct: &CanonicalLctId)
    -> Option<(web4_core::crypto::PublicKey, &'static str)> {
    let hex_key = member.and_then(|m| state.member_pubkeys.get(&m).or_else(|| state.council_pubkeys.get(&m)))
        .or_else(|| state.member_of_consent_key.get(lct))?;
    let bytes: [u8; 32] = hex::decode(hex_key).ok()?.try_into().ok()?;
    Some((web4_core::crypto::PublicKey::from_bytes(&bytes).ok()?, "member"))
}
