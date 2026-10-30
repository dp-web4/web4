//! Commitments K5b (PRD_COMMITMENTS §7.1): the operator's invite turns a contact into a member who
//! holds their own key, with nothing to install.
//!
//! An invite has the K4 token shape under its own MAC label, so it can never be read as a
//! movement link, or the reverse: `<party_id>.<nonce>.<expires>.<MAC>`. The nonce makes every
//! invite distinct, so one minted in the same second as a withdrawn one is not the dead one. It is evidence for law, never a
//! bypass: a verified invite reaches the join gate as `r6.resource.invite == "verified"`, and the
//! chapter's law decides what that is worth. It binds once (`ContactBound`), can be withdrawn
//! before then (`InviteRevoked`), and lives seven days.

use super::*;

/// Shorter than a movement link's 30 days: admission is a stronger act than an acknowledgement.
pub(crate) const INVITE_TTL_DAYS: i64 = 7;
const INVITE_MAC_LABEL: &[u8] = b"web4-hub invite v1\n";

/// What law sees on a join that carried a verified invite: `r6.resource.invite`.
pub(crate) const INVITE_RESOURCE: (&str, &str) = ("invite", "verified");

pub(crate) fn mint_invite(key: &[u8; 32], party_id: &str, expires: DateTime<Utc>) -> String {
    let nonce = hex::encode(rand::random::<[u8; 8]>());
    mint_token(INVITE_MAC_LABEL, key, &[party_id, &nonce], expires)
}

/// A verified invite: the contact it names, and the digest the ledger records in its place.
#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) struct InviteClaim {
    pub party_id: String,
    pub digest: String,
}

pub(crate) fn read_invite(key: &[u8; 32], token: &str, now: DateTime<Utc>) -> Result<InviteClaim, LinkError> {
    let (fields, digest) = read_token(INVITE_MAC_LABEL, key, token, 2, now)?;
    let party_id = fields.into_iter().next().expect("two fields");
    Ok(InviteClaim { party_id, digest })
}

/// An invite the join route was handed, verified by its MAC and date. Nothing here reads the
/// ledger: whether it is still unused is [`invite_standing`]'s question, asked under the lock.
pub(crate) fn verify_invite(s: &RestState, token: &str) -> Result<InviteClaim, ApiError> {
    let key = read_link_key(&s.paths.root).map_err(ApiError::internal)?;
    let invalid = || ApiError::bad_request("this invite is not valid");
    let key = key.ok_or_else(invalid)?;
    read_invite(&key, token, Utc::now()).map_err(|e| match e {
        LinkError::Invalid => invalid(),
        LinkError::Expired => ApiError { status: StatusCode::GONE, message: "this invite has expired".into() },
    })
}

/// Where a verified invite stands against the ledger and the contact book.
#[derive(Debug, PartialEq, Eq)]
pub(crate) enum InviteStanding {
    /// Unused, unwithdrawn, and its contact is still in the book and not yet a member.
    Open,
    /// It already bound its contact to this very member: opening it again is not an error.
    AlreadyThisMember,
    /// It bound its contact to this key, but the key was never admitted: the binding is written
    /// before the admission (Legion, #961), and something stopped in between. Only this key can
    /// finish, so a forwarded copy cannot use the gap.
    BoundToThisKey,
}

/// Is this invite still good for `member`? The caller holds `COMMITMENT_LOCK` from here until the
/// binding is witnessed, so two joins racing on one invite cannot both find it open.
pub(crate) fn invite_standing(s: &RestState, state: &HubState, claim: &InviteClaim, member: Uuid)
    -> Result<InviteStanding, ApiError>
{
    let gone = |m: &str| ApiError { status: StatusCode::GONE, message: m.to_string() };
    if state.invites.used.get(&claim.digest) == Some(&claim.party_id)
        && state.invites.bound.get(&claim.party_id) == Some(&member)
    {
        return Ok(if state.members.contains_key(&member) {
            InviteStanding::AlreadyThisMember
        } else {
            InviteStanding::BoundToThisKey
        });
    }
    if let Some(why) = state.invites.spent(&claim.digest) {
        return Err(gone(why));
    }
    if state.invites.bound.contains_key(&claim.party_id) {
        return Err(ApiError::conflict("this contact is already a member"));
    }
    // An erased contact's invite dies with the details it was for (C3).
    if !load_book(s)?.contacts.contains_key(&claim.party_id) {
        return Err(gone("this invite's contact is no longer in the hub's book"));
    }
    Ok(InviteStanding::Open)
}

/// Witness `ContactBound` and copy the contact's address to the member's entry, so nudges keep
/// reaching the same person once they are named as the member. The caller holds `COMMITMENT_LOCK`
/// and has just admitted `member` (or found them already a member).
pub(crate) async fn bind_contact(s: &RestState, claim: &InviteClaim, member: Uuid) -> Result<u64, ApiError> {
    let event = HubEvent::ContactBound {
        party_id: claim.party_id.clone(),
        member_lct_id: member,
        invite_digest: claim.digest.clone(),
        bound_by: s.sovereign_lct_id,
    };
    {
        let ledger = s.ledger.lock().await;
        s.projected(&ledger).invites.check(&event).map_err(refused)?;
    }
    let index = witness_event(s, event).await?;
    // The binding is on the ledger now, so a book that can't be written does not undo it or fail
    // the join (Legion, #961). Until the address is copied, nudges to the member have nowhere to go,
    // and the operator's log says why.
    if let Err(e) = copy_address(s, &claim.party_id, member) {
        tracing::warn!("contact {} is bound to member {member}, but the address was not copied: {}",
            claim.party_id, e.message);
    }
    tracing::info!("contact {} joined from an invite as member {member} (entry {index})", claim.party_id);
    Ok(index)
}

fn copy_address(s: &RestState, party_id: &str, member: Uuid) -> Result<(), ApiError> {
    let mut book = load_book(s)?;
    if let Some(address) = book.contacts.get(party_id).map(|c| c.address.clone()) {
        book.members.entry(member.to_string())
            .or_insert(MemberAddress { address, added_at: Utc::now() });
        book.save(&book_path(s)).map_err(ApiError::internal)?;
    }
    Ok(())
}

/// The invite a queued join carried, bound now that the operator admits it (Legion, #961). The
/// caller holds `COMMITMENT_LOCK` through the admission. An invite that stopped being good while
/// the join waited (withdrawn, its contact erased or bound by another) binds nothing: the
/// operator's admission stands on its own, and the log says why.
pub(crate) async fn bind_queued(s: &RestState, jr: &hub_lib::state::JoinRequest) -> Result<Option<u64>, ApiError> {
    let (Some(party_id), Some(digest)) = (&jr.invite_party_id, &jr.invite_digest) else { return Ok(None) };
    let claim = InviteClaim { party_id: party_id.clone(), digest: digest.clone() };
    let state = { let l = s.ledger.lock().await; s.projected(&l) };
    match invite_standing(s, &state, &claim, jr.member_lct_id) {
        Ok(InviteStanding::Open) => bind_contact(s, &claim, jr.member_lct_id).await.map(Some),
        Ok(_) => Ok(None),
        Err(e) if e.status.is_server_error() => Err(e),
        Err(e) => {
            tracing::warn!("admitting {} without binding contact {}: {}", jr.member_lct_id, claim.party_id, e.message);
            Ok(None)
        }
    }
}

/// `POST /admin/api/contacts/:party_id/invite` — mint an invite for one contact.
///
/// surface: admin_invite_mint   act: issue a credential that admits its holder (subject to law)
/// S: med/reversible [construct: InviteRevoked withdraws it unused; 7-day expiry; law still decides]
/// R: pass [construct: require_loopback]   W: pass [construct: operator plane only; the contact must be in the book]
/// O: pass [construct: COMMITMENT_LOCK; the key is made only after every check]
/// A: n/a [construct: minting writes nothing to the ledger; the use (ContactBound) and the withdrawal (InviteRevoked) are witnessed]
/// V: present [construct: admin_invite_revoke]
/// verdict: PASS
pub(in crate::rest) async fn admin_invite_mint(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(party_id): Path<String>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    mint_for(&s, &party_id, link_base()).await.map(Json)
}

async fn mint_for(s: &RestState, party_id: &str, base: Option<String>) -> Result<serde_json::Value, ApiError> {
    let base = base.ok_or_else(|| ApiError::conflict(
        "set HUB_PUBLIC_BASE_URL: an invite must point where people reach the hub"))?;
    let _serial = COMMITMENT_LOCK.lock().await;
    if !load_book(s)?.contacts.contains_key(party_id) {
        return Err(ApiError::not_found(format!("no contact {party_id}")));
    }
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    if let Some(member) = state.invites.bound.get(party_id) {
        return Err(ApiError::conflict(format!("contact {party_id} is already member {member}")));
    }
    let key = link_key_or_create(&s.paths.root).map_err(ApiError::internal)?;
    let expires = Utc::now() + chrono::Duration::days(INVITE_TTL_DAYS);
    let token = mint_invite(&key, party_id, expires);
    let digest = token_digest(&token);
    Ok(serde_json::json!({
        "link": format!("{base}/j/{token}"),
        "invite_digest": digest,
        "expires_at": expires.to_rfc3339(),
    }))
}

/// `POST /admin/api/invites/:invite_digest/revoke` — withdraw an unused invite.
///
/// surface: admin_invite_revoke   act: stop an invite admitting anyone
/// S: low/irreversible [construct: the invite is dead; a fresh one is one call away]
/// R: pass [construct: require_loopback]   W: pass [construct: operator plane only]
/// O: pass [construct: COMMITMENT_LOCK; Invites::check before witness_event]
/// A: pass [construct: InviteRevoked carries the digest and revoked_by]
/// V: n/a (narrows access)
/// verdict: PASS
pub(in crate::rest) async fn admin_invite_revoke(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
    Path(invite_digest): Path<String>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    revoke(&s, &invite_digest).await.map(Json)
}

async fn revoke(s: &RestState, invite_digest: &str) -> Result<serde_json::Value, ApiError> {
    let _serial = COMMITMENT_LOCK.lock().await;
    let event = HubEvent::InviteRevoked { invite_digest: invite_digest.to_string(), revoked_by: s.sovereign_lct_id };
    {
        let ledger = s.ledger.lock().await;
        s.projected(&ledger).invites.check(&event).map_err(refused)?;
    }
    let entry_index = witness_event(s, event).await?;
    Ok(serde_json::json!({ "revoked": true, "entry_index": entry_index }))
}

/// `GET /admin/api/invites` — who joined from an invite, newest first, and what was withdrawn.
/// Whoever opens an invite first becomes the member, so a forwarded email admits the wrong
/// person: this list is how the operator sees that it happened.
///
/// surface: admin_invites_list   act: none (read)
/// S: low/reversible   R: pass [construct: require_loopback]   W: n/a (read)   O: n/a   A: n/a   V: n/a
/// verdict: PASS
pub(in crate::rest) async fn admin_invites_list(
    State(s): State<RestState>,
    ConnectInfo(peer): ConnectInfo<SocketAddr>,
) -> Result<Json<serde_json::Value>, ApiError> {
    require_loopback(&peer)?;
    list(&s).await.map(Json)
}

async fn list(s: &RestState) -> Result<serde_json::Value, ApiError> {
    let book = load_book(s)?;
    let ledger = s.ledger.lock().await;
    let mut joined = Vec::new();
    let mut revoked = Vec::new();
    for e in ledger.entries().iter().rev() {
        match &e.event {
            HubEvent::ContactBound { party_id, member_lct_id, invite_digest, .. } => joined.push(serde_json::json!({
                "party_id": party_id,
                "name": book.contacts.get(party_id).map(|c| c.name.as_str()),
                "member_lct_id": member_lct_id,
                "invite_digest": invite_digest,
                "entry_index": e.index,
                "at": e.timestamp.to_rfc3339(),
            })),
            HubEvent::InviteRevoked { invite_digest, .. } => revoked.push(serde_json::json!({
                "invite_digest": invite_digest, "entry_index": e.index, "at": e.timestamp.to_rfc3339(),
            })),
            _ => {}
        }
    }
    Ok(serde_json::json!({ "joined": joined, "revoked": revoked }))
}

/// `GET /j/:token` — the page an invite opens: "Join <hub>". Reading it writes nothing; the
/// browser makes its key and signs the join only when the person presses the button.
///
/// surface: invite_page   act: none (a read; the join is the separate signed POST)
/// S: low/reversible [construct: no write; it names only the contact the invite was for]
/// R: pass [construct: read_invite, an HMAC over (party, expiry) under its own label]   W: n/a (read)
/// O: n/a   A: n/a (read)   V: n/a
/// verdict: PASS
pub(in crate::rest) async fn invite_page(
    State(s): State<RestState>,
    Path(token): Path<String>,
) -> axum::response::Response {
    let claim = match read_link_key(&s.paths.root) {
        Ok(Some(key)) => match read_invite(&key, &token, Utc::now()) {
            Ok(claim) => claim,
            Err(e) => return invite_error_page(e),
        },
        Ok(None) => return invite_error_page(LinkError::Invalid),
        Err(e) => {
            tracing::warn!("invite key unreadable: {e:#}");
            return link_page_response(StatusCode::INTERNAL_SERVER_ERROR, "Something went wrong",
                "<h1>Something went wrong</h1><p>Please try again later.</p>");
        }
    };
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let book = match load_book(&s) {
        Ok(book) => book,
        Err(e) => {
            tracing::warn!("contact book unreadable for an invite page: {}", e.message);
            return link_page_response(StatusCode::INTERNAL_SERVER_ERROR, "Something went wrong",
                "<h1>Something went wrong</h1><p>Please try again later.</p>");
        }
    };
    let hub = esc(&s.hub_name);
    let Some(contact) = book.contacts.get(&claim.party_id) else { return used_page() };
    // An invite bound to a key that was never admitted still shows its button: only that key can
    // finish, and the route refuses every other.
    let unfinished = state.invites.bound.get(&claim.party_id)
        .is_some_and(|m| !state.members.contains_key(m) && state.invites.used.get(&claim.digest) == Some(&claim.party_id));
    if !unfinished
        && (state.invites.spent(&claim.digest).is_some() || state.invites.bound.contains_key(&claim.party_id))
    {
        return used_page();
    }
    let body = format!(
        "<h1>Join {hub}</h1>\
         <p>Hi {name}. {hub} has invited you to join. Your jobs and your answers will then be yours, \
         signed by a key that stays in this browser. There is nothing to install.</p>\
         <p id=\"webview\" class=\"muted\" hidden>This looks like an app's built-in browser. Open this page \
         in Safari or Chrome instead, so that your key stays with you.</p>\
         <button id=\"join\">Join {hub}</button>\
         <p id=\"status\" class=\"muted\" role=\"status\"></p>\
         <script src=\"/keystore.js\"></script><script src=\"/join.js\"></script>",
        name = esc(&contact.name));
    link_page_response(StatusCode::OK, &format!("Join {}", s.hub_name), &body)
}

fn used_page() -> axum::response::Response {
    link_page_response(StatusCode::GONE, "This invite has been used",
        "<h1>This invite has been used</h1><p>It has already been used, or it was withdrawn. \
         If you didn't use it, ask your organiser for a new one.</p>")
}

fn invite_error_page(e: LinkError) -> axum::response::Response {
    match e {
        LinkError::Invalid => link_page_response(StatusCode::NOT_FOUND, "Invite not found",
            "<h1>Invite not found</h1><p>Check that the whole link was copied.</p>"),
        LinkError::Expired => link_page_response(StatusCode::GONE, "This invite has expired",
            "<h1>This invite has expired</h1><p>Ask your organiser for a new one.</p>"),
    }
}

/// `GET /join.js` — the invite page's script. It reuses `/keystore.js`, so a browser that already
/// holds an identity from `/client` joins with that one rather than making a second.
pub(in crate::rest) async fn join_js() -> axum::response::Response {
    use axum::response::IntoResponse;
    ([(axum::http::header::CONTENT_TYPE, "text/javascript; charset=utf-8")], JOIN_JS).into_response()
}

pub(crate) const JOIN_JS: &str = r##"'use strict';
const $=s=>document.querySelector(s);
const invite=decodeURIComponent(location.pathname.split('/').pop());
function say(cls,msg){ const e=$('#status'); e.className=cls; e.textContent=msg; }
// A key made inside a mail or social app's own browser stays in that app.
if(/FBAN|FBAV|Instagram|Line\/|GSA\/|MicroMessenger|Snapchat|; wv\)/.test(navigator.userAgent))$('#webview').hidden=false;
async function join(){
  const b=$('#join'); b.disabled=true;
  try{
    let id=await loadID();
    if(!id)id=await newID();
    const w=await (await fetch('/.well-known/web4-hub.json')).json();
    // No name: the join is recorded on the ledger, and a person's name never goes there.
    const p={action:'member_join_request',member_lct_id:id.lct_id,member_pubkey_hex:id.pubHex,invite};
    const r=await fetch('/v1/hubs/'+w.hub_lct_id+'/members/join',{method:'POST',
      headers:{'content-type':'application/json'},body:JSON.stringify(await signEnvelope(id,p))});
    const out=await r.json().catch(()=>({}));
    if(r.status===200){ b.hidden=true; say('ok','You\'re in. Keep using this browser: your key lives here.'); }
    else if(r.status===202){ b.hidden=true; say('muted','Your organiser will confirm you. Once they have, open this link again.'); }
    else { say('err',out.error||('Something went wrong ('+r.status+').')); b.disabled=false; }
  }catch(e){
    say('err',e.message==='NO_ED25519'?'This browser cannot hold a signing key. Ask your organiser.'
      :'Something went wrong: '+e.message);
    b.disabled=false;
  }
}
$('#join').addEventListener('click',join);
"##;

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rest::channel_e2e_tests::fresh_rest_state;
    use web4_core::crypto::KeyPair;

    /// The pilot's admission law (PRD_COMMITMENTS §7.1): an uninvited join queues for the
    /// operator, and a verified invite admits. The invite norm outranks the queue norm.
    const PILOT_LAW: &str = r#"
version: "1.0.0"
norms:
  - id: ADMISSION-QUEUES
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
  - id: INVITED-JOIN-ADMITS
    selector: r6.resource.invite
    operator: "=="
    value: verified
    decision: allow
    priority: 200
admission:
  open: false
  requires_sponsor: false
"#;

    /// The same law without the invite norm: every join queues, invited or not.
    const QUEUE_LAW: &str = r#"
version: "1.0.0"
norms:
  - id: ADMISSION-QUEUES
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
admission:
  open: false
  requires_sponsor: false
"#;

    async fn hub(law: &str) -> (tempfile::TempDir, RestState, String) {
        let (tmp, s) = fresh_rest_state(Some(law)).await;
        let v = add_contact(&s, ContactBody { name: "Robin".into(), address: "robin@example.org".into() })
            .await.unwrap();
        let party = v["party"]["party_id"].as_str().unwrap().to_string();
        (tmp, s, party)
    }

    async fn invite(s: &RestState, party: &str) -> String {
        let v = mint_for(s, party, Some("https://hub.example.org".into())).await.unwrap();
        v["link"].as_str().unwrap().strip_prefix("https://hub.example.org/j/").unwrap().to_string()
    }

    /// A join exactly as `/join.js` sends it: signed over a real challenge, no name.
    async fn join(s: &RestState, kp: &KeyPair, lct: Uuid, invite: Option<&str>) -> (StatusCode, serde_json::Value) {
        use axum::response::IntoResponse;
        let challenge = s.nonces.issue(lct, Utc::now());
        let mut payload = serde_json::json!({
            "action": "member_join_request",
            "member_lct_id": lct,
            "member_pubkey_hex": kp.verifying_key().to_hex(),
        });
        if let Some(t) = invite {
            payload["invite"] = serde_json::json!(t);
        }
        let mut env = hub_lib::envelope::SignedEnvelope {
            challenge_nonce: challenge.nonce.clone(), payload, signature: String::new(), signer_lct_id: lct,
        };
        env.signature = kp.sign(&env.signing_bytes().unwrap()).to_hex();
        let resp = match crate::rest::submit_join(State(s.clone()), Path(s.hub_id), Json(env)).await {
            Ok(r) => r,
            Err(e) => e.into_response(),
        };
        let status = resp.status();
        let bytes = axum::body::to_bytes(resp.into_body(), usize::MAX).await.unwrap();
        (status, serde_json::from_slice(&bytes).unwrap_or_default())
    }

    async fn page(s: &RestState, path: &str) -> (StatusCode, axum::http::HeaderMap, String) {
        use tower::ServiceExt;
        let req = axum::http::Request::builder().uri(path).body(axum::body::Body::empty()).unwrap();
        let resp = crate::rest::router(s.clone()).oneshot(req).await.unwrap();
        let (status, headers) = (resp.status(), resp.headers().clone());
        let bytes = axum::body::to_bytes(resp.into_body(), usize::MAX).await.unwrap();
        (status, headers, String::from_utf8_lossy(&bytes).into_owned())
    }

    async fn bindings(s: &RestState) -> Vec<(String, Uuid, String)> {
        s.ledger.lock().await.entries().iter().filter_map(|e| match &e.event {
            HubEvent::ContactBound { party_id, member_lct_id, invite_digest, bound_by } => {
                assert_eq!(*bound_by, s.sovereign_lct_id, "the operator's witness");
                Some((party_id.clone(), *member_lct_id, invite_digest.clone()))
            }
            _ => None,
        }).collect()
    }

    async fn len(s: &RestState) -> usize {
        s.ledger.lock().await.len()
    }

    #[test]
    fn an_invite_and_a_movement_link_never_read_as_each_other() {
        let key = [7u8; 32];
        let later = Utc::now() + chrono::Duration::days(1);
        let inv = mint_invite(&key, "p1", later);
        let claim = read_invite(&key, &inv, Utc::now()).unwrap();
        assert_ne!(inv, mint_invite(&key, "p1", later), "two invites for one contact in one second differ");
        assert_eq!(claim, InviteClaim { party_id: "p1".into(), digest: token_digest(&inv) });
        // Same key, same shape of fields: only the label tells them apart, and it does.
        let link = mint_link(&key, "p1", "p2", later);
        assert_eq!(read_invite(&key, &link, Utc::now()), Err(LinkError::Invalid));
        let forged = format!("c1.{}", inv);
        assert_eq!(read_link(&key, &forged, Utc::now()), Err(LinkError::Invalid));
        assert_eq!(read_invite(&[8u8; 32], &inv, Utc::now()), Err(LinkError::Invalid));
        assert_eq!(read_invite(&key, &inv, later), Err(LinkError::Expired));
        let (payload, tag) = inv.rsplit_once('.').unwrap();
        assert_eq!(read_invite(&key, &format!("{payload}.{}", tag.to_uppercase()), Utc::now()), Err(LinkError::Invalid));
    }

    #[tokio::test]
    async fn an_invited_join_admits_binds_once_and_puts_no_name_on_the_ledger() {
        let (_tmp, s, robin) = hub(PILOT_LAW).await;
        let token = invite(&s, &robin).await;

        let (status, headers, html) = page(&s, &format!("/j/{token}")).await;
        assert_eq!(status, StatusCode::OK, "{html}");
        assert!(html.contains("Hi Robin.") && html.contains("<script src=\"/join.js\"></script>"), "{html}");
        assert_eq!(headers["content-security-policy"], crate::rest::KEY_PAGE_CSP);
        assert_eq!(headers["cache-control"], "no-store");

        let (kp, lct) = (KeyPair::generate(), Uuid::new_v4());
        let (status, out) = join(&s, &kp, lct, Some(&token)).await;
        assert_eq!(status, StatusCode::OK, "{out}");
        assert_eq!(bindings(&s).await, vec![(robin.clone(), lct, token_digest(&token))]);
        let state = { let l = s.ledger.lock().await; s.projected(&l) };
        assert!(state.members.contains_key(&lct));
        assert_eq!(state.invites.bound.get(&robin), Some(&lct));
        let added = s.ledger.lock().await.entries().iter().find_map(|e| match &e.event {
            HubEvent::MemberAdded { member_lct_id, member_name, .. } if *member_lct_id == lct => Some(member_name.clone()),
            _ => None,
        });
        assert_eq!(added, Some(None), "a person's name never reaches the ledger (C3)");
        let kinds: Vec<&str> = s.ledger.lock().await.entries().iter().map(|e| e.event.kind())
            .filter(|k| *k == "contact_bound" || *k == "member_added").collect();
        assert_eq!(kinds, vec!["contact_bound", "member_added"], "the binding is written before the admission");
        let book = load_book(&s).unwrap();
        assert_eq!(book.members[&lct.to_string()].address, "robin@example.org", "nudges follow the person");

        // Opening it again from the same browser is not an error and writes nothing.
        let before = len(&s).await;
        let (status, out) = join(&s, &kp, lct, Some(&token)).await;
        assert_eq!((status, out["status"].as_str()), (StatusCode::OK, Some("already_member")));
        assert_eq!(len(&s).await, before);

        // Anyone else holding it is refused, and nothing is written.
        let (status, out) = join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&token)).await;
        assert_eq!(status, StatusCode::GONE, "{out}");
        assert!(out["error"].as_str().unwrap().contains("already been used"), "{out}");
        assert_eq!(len(&s).await, before);
        assert_eq!(page(&s, &format!("/j/{token}")).await.0, StatusCode::GONE);

        // The operator's notice: who joined from which invite.
        let listed = list(&s).await.unwrap();
        assert_eq!(listed["joined"][0]["name"], "Robin");
        assert_eq!(listed["joined"][0]["member_lct_id"], serde_json::json!(lct));
        // And no fresh invite for a contact who is already a member.
        let again = mint_for(&s, &robin, Some("https://hub.example.org".into())).await.unwrap_err();
        assert_eq!(again.status, StatusCode::CONFLICT);
    }

    #[tokio::test]
    async fn without_a_good_invite_the_pilot_law_queues_or_refuses_and_binds_nothing() {
        let (_tmp, s, robin) = hub(PILOT_LAW).await;
        let token = invite(&s, &robin).await;
        let (status, _) = join(&s, &KeyPair::generate(), Uuid::new_v4(), None).await;
        assert_eq!(status, StatusCode::ACCEPTED, "an uninvited join queues");

        let before = len(&s).await;
        let bad = mint_invite(&[1u8; 32], &robin, Utc::now() + chrono::Duration::days(1));
        let (status, out) = join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&bad)).await;
        assert_eq!(status, StatusCode::BAD_REQUEST, "{out}");
        let key = read_link_key(&s.paths.root).unwrap().unwrap();
        let stale = mint_invite(&key, &robin, Utc::now() - chrono::Duration::seconds(1));
        let (status, _) = join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&stale)).await;
        assert_eq!(status, StatusCode::GONE);
        // A movement link is not an invite, even for the same party.
        let link = mint_link(&key, &robin, &robin, Utc::now() + chrono::Duration::days(1));
        assert_eq!(join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&link)).await.0, StatusCode::BAD_REQUEST);
        assert_eq!(len(&s).await, before, "a refused invite writes nothing, not even a queue entry");
        assert!(bindings(&s).await.is_empty());
        // The good one still works afterwards.
        assert_eq!(join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&token)).await.0, StatusCode::OK);
    }

    #[tokio::test]
    async fn an_invite_is_evidence_for_law_not_a_way_around_it() {
        let (_tmp, s, robin) = hub(QUEUE_LAW).await;
        let token = invite(&s, &robin).await;
        let (kp, lct) = (KeyPair::generate(), Uuid::new_v4());
        let (status, out) = join(&s, &kp, lct, Some(&token)).await;
        assert_eq!(status, StatusCode::ACCEPTED, "this law queues invited joins too: {out}");
        assert!(bindings(&s).await.is_empty(), "nothing is bound before admission");

        // The operator admits from the queue; opening the invite again then binds.
        let request = out["request_id"].as_str().unwrap().parse().unwrap();
        crate::rest::approve_join(&s, request, s.sovereign_lct_id).await.unwrap();
        assert_eq!(bindings(&s).await, vec![(robin.clone(), lct, token_digest(&token))],
            "the operator's admission binds the invite the join carried");
        let before = len(&s).await;
        let (status, out) = join(&s, &kp, lct, Some(&token)).await;
        assert_eq!((status, out["status"].as_str()), (StatusCode::OK, Some("already_member")));
        assert_eq!(len(&s).await, before);
    }

    #[tokio::test]
    async fn an_invite_withdrawn_while_its_join_waits_binds_nothing_at_admission() {
        let (_tmp, s, robin) = hub(QUEUE_LAW).await;
        let token = invite(&s, &robin).await;
        let (status, out) = join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&token)).await;
        assert_eq!(status, StatusCode::ACCEPTED, "{out}");
        revoke(&s, &token_digest(&token)).await.unwrap();
        let request = out["request_id"].as_str().unwrap().parse().unwrap();
        crate::rest::approve_join(&s, request, s.sovereign_lct_id).await.unwrap();
        assert!(bindings(&s).await.is_empty(), "the operator admitted a person, not a withdrawn invite");
    }

    /// A member admitted from the queue with no invite, holding `kp`: someone already in the hub.
    async fn existing_member(s: &RestState, kp: &KeyPair) -> Uuid {
        let lct = Uuid::new_v4();
        let (status, out) = join(s, kp, lct, None).await;
        assert_eq!(status, StatusCode::ACCEPTED, "{out}");
        let request = out["request_id"].as_str().unwrap().parse().unwrap();
        crate::rest::approve_join(s, request, s.sovereign_lct_id).await.unwrap();
        lct
    }

    #[tokio::test]
    async fn a_member_opening_someone_elses_invite_binds_nothing() {
        let (_tmp, s, robin) = hub(PILOT_LAW).await;
        let sam_kp = KeyPair::generate();
        let sam = existing_member(&s, &sam_kp).await;
        let token = invite(&s, &robin).await;
        let before = len(&s).await;
        let (status, out) = join(&s, &sam_kp, sam, Some(&token)).await;
        assert_eq!(status, StatusCode::CONFLICT, "{out}");
        assert!(out["error"].as_str().unwrap().contains("isn't yours"), "{out}");
        assert_eq!(len(&s).await, before, "nothing is written");
        assert!(!load_book(&s).unwrap().members.contains_key(&sam.to_string()), "nor is Robin's address moved");
        // Robin, with Robin's own key, still can.
        assert_eq!(join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&token)).await.0, StatusCode::OK);
    }

    #[tokio::test]
    async fn a_join_stopped_between_binding_and_admission_fails_closed() {
        let (_tmp, s, robin) = hub(PILOT_LAW).await;
        let token = invite(&s, &robin).await;
        let (alice_kp, alice) = (KeyPair::generate(), Uuid::new_v4());
        // Alice's join bound the invite and then stopped before admitting her.
        {
            let _serial = COMMITMENT_LOCK.lock().await;
            bind_contact(&s, &verify_invite(&s, &token).unwrap(), alice).await.unwrap();
        }
        // Bob, holding a forwarded copy, is refused.
        let (status, out) = join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&token)).await;
        assert_eq!(status, StatusCode::GONE, "{out}");
        // Alice's page still offers the button, and her retry finishes the admission.
        assert_eq!(page(&s, &format!("/j/{token}")).await.0, StatusCode::OK);
        let (status, out) = join(&s, &alice_kp, alice, Some(&token)).await;
        assert_eq!(status, StatusCode::OK, "{out}");
        assert!({ let l = s.ledger.lock().await; s.projected(&l) }.members.contains_key(&alice));
        assert_eq!(bindings(&s).await.len(), 1, "bound once");
        assert_eq!(page(&s, &format!("/j/{token}")).await.0, StatusCode::GONE);
    }

    #[tokio::test]
    async fn a_contact_book_that_cannot_be_written_does_not_undo_a_join() {
        use std::os::unix::fs::PermissionsExt;
        let (_tmp, s, robin) = hub(PILOT_LAW).await;
        let token = invite(&s, &robin).await;
        let root = s.paths.root.clone();
        std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o555)).unwrap();
        let lct = Uuid::new_v4();
        let (status, out) = join(&s, &KeyPair::generate(), lct, Some(&token)).await;
        std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o755)).unwrap();
        assert_eq!(status, StatusCode::OK, "{out}");
        assert_eq!(bindings(&s).await.len(), 1);
        assert!(!load_book(&s).unwrap().members.contains_key(&lct.to_string()), "the save really failed");
    }

    #[tokio::test]
    async fn a_withdrawn_invite_admits_nobody_and_a_used_one_cannot_be_withdrawn() {
        let (_tmp, s, robin) = hub(PILOT_LAW).await;
        let token = invite(&s, &robin).await;
        let digest = token_digest(&token);
        revoke(&s, &digest).await.unwrap();
        assert!(matches!(s.ledger.lock().await.entries().last().unwrap().event,
            HubEvent::InviteRevoked { ref invite_digest, revoked_by } if *invite_digest == digest && revoked_by == s.sovereign_lct_id));
        let before = len(&s).await;
        let (status, out) = join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&token)).await;
        assert_eq!(status, StatusCode::GONE);
        assert!(out["error"].as_str().unwrap().contains("withdrawn"), "{out}");
        assert_eq!(len(&s).await, before);
        assert_eq!(page(&s, &format!("/j/{token}")).await.0, StatusCode::GONE);
        assert_eq!(revoke(&s, &digest).await.unwrap_err().status, StatusCode::BAD_REQUEST, "withdrawn twice");
        assert_eq!(revoke(&s, "NOT-A-DIGEST").await.unwrap_err().status, StatusCode::BAD_REQUEST);

        let fresh = invite(&s, &robin).await;
        assert_eq!(join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&fresh)).await.0, StatusCode::OK);
        let used = revoke(&s, &token_digest(&fresh)).await.unwrap_err();
        assert_eq!(used.status, StatusCode::BAD_REQUEST);
        assert!(used.message.contains("already been used"), "{}", used.message);
    }

    #[tokio::test]
    async fn an_erased_contacts_invite_dies_with_the_details() {
        let (_tmp, s, robin) = hub(PILOT_LAW).await;
        let token = invite(&s, &robin).await;
        erase_contact(&s, &robin).await.unwrap();
        let before = len(&s).await;
        assert_eq!(join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&token)).await.0, StatusCode::GONE);
        assert_eq!(len(&s).await, before);
        assert_eq!(page(&s, &format!("/j/{token}")).await.0, StatusCode::GONE);
    }

    /// Real threads, several rounds: on a single-threaded runtime two joins never interleave, and
    /// the test would pass with no lock at all.
    #[tokio::test(flavor = "multi_thread", worker_threads = 4)]
    async fn two_joins_racing_on_one_invite_bind_one_member() {
        let (_tmp, s, _) = hub(PILOT_LAW).await;
        for round in 0..12 {
            let v = add_contact(&s, ContactBody { name: format!("R{round}"), address: format!("r{round}@example.org") })
                .await.unwrap();
            let party = v["party"]["party_id"].as_str().unwrap().to_string();
            let token = invite(&s, &party).await;
            let racers: Vec<_> = (0..2).map(|_| {
                let (s, token) = (s.clone(), token.clone());
                tokio::spawn(async move { join(&s, &KeyPair::generate(), Uuid::new_v4(), Some(&token)).await })
            }).collect();
            let mut statuses = Vec::new();
            for r in racers {
                statuses.push(r.await.unwrap().0);
            }
            statuses.sort();
            assert_eq!(statuses, vec![StatusCode::OK, StatusCode::GONE], "round {round}");
        }
        assert_eq!(bindings(&s).await.len(), 12);
        let admitted = s.ledger.lock().await.entries().iter()
            .filter(|e| matches!(e.event, HubEvent::MemberAdded { .. })).count();
        assert_eq!(admitted, 12, "no loser was admitted either");
    }

    #[tokio::test]
    async fn an_invite_is_minted_only_for_a_contact_in_the_book_with_somewhere_to_point() {
        let (_tmp, s, robin) = hub(PILOT_LAW).await;
        assert_eq!(mint_for(&s, &robin, None).await.unwrap_err().status, StatusCode::CONFLICT);
        assert_eq!(read_link_key(&s.paths.root).unwrap(), None, "no key made for a refused mint");
        assert_eq!(mint_for(&s, "nobody", Some("https://h".into())).await.unwrap_err().status, StatusCode::NOT_FOUND);
        let v = mint_for(&s, &robin, Some("https://h".into())).await.unwrap();
        let token = v["link"].as_str().unwrap().strip_prefix("https://h/j/").unwrap();
        assert_eq!(v["invite_digest"], token_digest(token));
        let expires = DateTime::parse_from_rfc3339(v["expires_at"].as_str().unwrap()).unwrap();
        let days = (expires.with_timezone(&Utc) - Utc::now()).num_hours();
        assert!((7 * 24 - 1..=7 * 24).contains(&days), "an invite lives 7 days (Legion, #959), not {days}h");
    }

    #[test]
    fn the_join_script_sends_no_name_and_runs_under_the_key_page_policy() {
        for inline in ["style=", "onclick", "localStorage.setItem", "exportKey('jwk'", "name:'", "p.name"] {
            assert!(!JOIN_JS.contains(inline), "join script carries {inline}");
        }
        let dir = tempfile::tempdir().unwrap();
        let js = dir.path().join("join.js");
        std::fs::write(&js, JOIN_JS).unwrap();
        match std::process::Command::new("node").arg("--check").arg(&js).output() {
            Ok(out) => assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr)),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => eprintln!("SKIPPED: node is not on PATH"),
            Err(e) => panic!("running node: {e}"),
        }
    }
}
