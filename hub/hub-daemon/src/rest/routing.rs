// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Member-of routing, slice Hub A (hub/docs/PRD_MEMBER_OF_ROUTING.md H1, H2, H4).
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
use hub_lib::routing::{check_edge, route_target, Consent, RouterCert};

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
/// O: pass [construct: all checks before witness_event; refusals witness nothing]
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
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };

    match p.action.as_str() {
        "router_register" => {
            let cert = p.certificate.ok_or_else(|| ApiError::bad_request("router_register requires `certificate`"))?;
            let v = cert.verify(s.hub_id).map_err(|e| ApiError::bad_request(e.to_string()))?;
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
            let replaced = state.routers.get(&v.router_lct).copied().filter(|m| *m != v.member);
            let entry_index = witness_event(&s, HubEvent::RouterRegistered {
                router_lct: v.router_lct.to_string(), member: signer,
            }).await?;
            Ok(Json(serde_json::json!({
                "registered": true, "router_lct": v.router_lct, "member": signer,
                "replaced_member": replaced, "entry_index": entry_index,
            })))
        }
        "router_retire" => {
            let lct = canonical("router_lct", p.router_lct.as_deref().unwrap_or(""))?;
            match state.routers.get(&lct) {
                Some(m) if m.as_uuid() == signer => {}
                Some(_) => return Err(forbidden("only the registered router member may retire it")),
                None => return Err(ApiError::not_found(format!("{lct} has no registered router"))),
            }
            let entry_index = witness_event(&s, HubEvent::RouterRetired { router_lct: lct.to_string() }).await?;
            Ok(Json(serde_json::json!({ "retired": true, "router_lct": lct, "entry_index": entry_index })))
        }
        other => Err(ApiError::bad_request(format!("unknown router action '{other}'"))),
    }
}

/// `POST /v1/hubs/:hub_id/member-of` — report or withdraw "LCT-x is member-of LCT-y".
///
/// surface: POST /v1/hubs/:hub_id/member-of   act: MemberOfReported / MemberOfWithdrawn
/// S: med [construct: an edge redirects x's mail to y's router (slice Hub B)]
/// R: n/a [construct: public plane; identity-gated]
/// W: pass [construct: signer = y's registered router (pinned key); x's consent by x's binding key]
/// O: pass [construct: consent, cycle and depth checks before witness_event]
/// A: pass [construct: signed chain entry with the bare edge only]
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
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let x = canonical("member", &p.member)?;

    match p.action.as_str() {
        "member_of_report" => {
            let y = canonical("of", p.of.as_deref().unwrap_or(""))?;
            if state.routers.get(&y) != Some(&signer) {
                return Err(forbidden(format!("only the registered router of {y} may report members of it")));
            }
            let consent = p.consent.ok_or_else(|| forbidden("member_of_report requires the member's `consent`"))?;
            consent.verify(s.hub_id, &x, &y, Utc::now()).map_err(|e| forbidden(e.to_string()))?;
            check_edge(&state, &x, &y).map_err(|e| conflict(e.to_string()))?;
            let previous = state.member_of.get(&x).cloned();
            if previous.as_ref() == Some(&y) {
                return Ok(Json(serde_json::json!({
                    "reported": true, "already": true, "member": x, "of": y,
                    "entry_index": state.member_of_at.get(&x),
                })));
            }
            let entry_index = witness_event(&s, HubEvent::MemberOfReported {
                member: x.to_string(), of: y.to_string(),
            }).await?;
            Ok(Json(serde_json::json!({
                "reported": true, "member": x, "of": y, "superseded": previous, "entry_index": entry_index,
            })))
        }
        "member_of_withdraw" => {
            let parent = state.member_of.get(&x)
                .ok_or_else(|| ApiError::not_found(format!("{x} has no member-of edge")))?;
            if state.routers.get(parent) != Some(&signer) {
                return Err(forbidden(format!("only the registered router of {parent} may withdraw its member")));
            }
            let entry_index = witness_event(&s, HubEvent::MemberOfWithdrawn { member: x.to_string() }).await?;
            Ok(Json(serde_json::json!({ "withdrawn": true, "member": x, "entry_index": entry_index })))
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
        .map(|(lct, m)| serde_json::json!({ "router_lct": lct, "member": m }))
        .collect();
    Ok(Json(serde_json::json!({ "routers": routers })))
}
