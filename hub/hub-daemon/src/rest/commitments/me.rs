//! Commitments K5c (PRD_COMMITMENTS §7.1, point 4): `/me`, a member's own view. What I own, what I
//! back up, and which of them wait on me, with nothing to install and no password.
//!
//! The browser key from K5b signs a `/v1/auth/challenge` nonce, and the hub answers with a session
//! cookie: a MAC over the member's id under its own label, good for 12 hours, HttpOnly,
//! SameSite=Strict and scoped to `/me`. The cookie only reads this member's view. Every write
//! still needs a signed envelope. A click from an email is a cross-site navigation and carries no
//! Strict cookie, so the page's script asks `/me/view` itself, and on a 401 it signs a fresh
//! challenge with the key already in this browser. The member never sees a sign-in.

use super::*;

/// How long a session reads before the browser signs again.
pub(crate) const ME_SESSION_HOURS: i64 = 12;
const ME_SESSION_LABEL: &[u8] = b"web4-hub member session v1\n";
pub(crate) const ME_COOKIE: &str = "hub_me";
const ME_ACTION: &str = "me_session";
const ACT_ACTION: &str = "commitment_act";

/// The key a session was signed in with, short: the first 64 bits of the SHA-256 of its hex. A
/// session names it so that rotating the key ends every session the old key began (Legion, #964).
fn key_print(pubkey_hex: &str) -> String {
    use sha2::Digest;
    hex::encode(sha2::Sha256::digest(pubkey_hex.as_bytes()))[..16].to_string()
}

/// The print of the key the hub resolves for `member` now, if any.
async fn current_print(s: &RestState, member: Uuid) -> Option<String> {
    s.resolver.read().await.lookup(member).map(|lct| key_print(&lct.public_key.to_hex()))
}

fn mint_session(key: &[u8; 32], member: Uuid, print: &str, expires: DateTime<Utc>) -> String {
    let nonce = hex::encode(rand::random::<[u8; 8]>());
    mint_token(ME_SESSION_LABEL, key, &[&member.to_string(), print, &nonce], expires)
}

/// The member a session cookie names and the print of the key it was signed in with, if this hub
/// made it and it has not expired.
fn read_session(key: &[u8; 32], token: &str, now: DateTime<Utc>) -> Option<(Uuid, String)> {
    let (fields, _) = read_token(ME_SESSION_LABEL, key, token, 3, now).ok()?;
    Some((Uuid::parse_str(&fields[0]).ok()?, fields[1].clone()))
}

fn cookie_value<'a>(headers: &'a axum::http::HeaderMap, name: &str) -> Option<&'a str> {
    headers.get_all(axum::http::header::COOKIE).iter()
        .filter_map(|v| v.to_str().ok())
        .flat_map(|v| v.split(';'))
        .filter_map(|kv| kv.trim().split_once('='))
        .find(|(k, _)| *k == name)
        .map(|(_, v)| v)
}

/// `Secure` whenever people reach the hub over https. A plain-http hub (a LAN pilot) would never
/// get a Secure cookie back, so there it is left off rather than breaking the page.
fn session_cookie(token: &str, base: Option<&str>) -> String {
    let secure = if base.is_some_and(|b| b.starts_with("https://")) { "; Secure" } else { "" };
    format!("{ME_COOKIE}={token}; Path=/me; Max-Age={}; HttpOnly; SameSite=Strict{secure}",
        ME_SESSION_HOURS * 3600)
}

/// `POST /me/session` — trade a signed challenge for a session that reads this member's view.
///
/// surface: me_session   act: issue a 12-hour credential to read one member's own commitments
/// S: low/reversible [construct: read-only, scoped to the signer's own view; expires in 12 h; writes still need an envelope]
/// R: pass [construct: verify_envelope against the live resolver; reaching the route grants nothing]
/// W: pass [construct: the member's pinned key signs a single-use challenge; the signer must be a member now]
/// O: pass [construct: verify_envelope + member check before the key is made or the cookie minted]
/// A: n/a [construct: a read credential; nothing is written to the ledger]
/// V: n/a (read-only)
/// verdict: PASS
pub(in crate::rest) async fn me_session(
    State(s): State<RestState>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<axum::response::Response, ApiError> {
    use axum::response::IntoResponse;
    let (member, token, expires) = open_session(&s, &envelope).await?;
    Ok((
        [
            (axum::http::header::SET_COOKIE, session_cookie(&token, link_base().as_deref())),
            (axum::http::header::CACHE_CONTROL, "no-store".to_string()),
        ],
        Json(serde_json::json!({ "member_lct_id": member, "expires_at": expires.to_rfc3339() })),
    ).into_response())
}

async fn open_session(s: &RestState, envelope: &SignedEnvelope) -> Result<(Uuid, String, DateTime<Utc>), ApiError> {
    {
        let resolver = s.resolver.read().await;
        verify_envelope(envelope, &s.nonces, &*resolver, Utc::now())?;
    }
    if envelope.payload.get("action").and_then(|a| a.as_str()) != Some(ME_ACTION) {
        return Err(ApiError::bad_request(format!("a session is signed with action='{ME_ACTION}'")));
    }
    let member = envelope.signer_lct_id;
    let is_member = { let l = s.ledger.lock().await; s.projected(&l).members.contains_key(&member) };
    if !is_member {
        return Err(ApiError { status: StatusCode::FORBIDDEN, message: "only a member has a view here".into() });
    }
    let print = current_print(s, member).await
        .ok_or_else(|| ApiError::internal(anyhow::anyhow!("member {member} verified but no longer resolves")))?;
    let key = {
        let _serial = COMMITMENT_LOCK.lock().await;
        link_key_or_create(&s.paths.root).map_err(ApiError::internal)?
    };
    let expires = Utc::now() + chrono::Duration::hours(ME_SESSION_HOURS);
    Ok((member, mint_session(&key, member, &print, expires), expires))
}

/// The member a request's session names, if it is good and they are still a member.
async fn session_member(s: &RestState, headers: &axum::http::HeaderMap) -> Result<Uuid, ApiError> {
    let unauthorized = || ApiError { status: StatusCode::UNAUTHORIZED, message: "sign in again".into() };
    let token = cookie_value(headers, ME_COOKIE).ok_or_else(unauthorized)?;
    let key = read_link_key(&s.paths.root).map_err(ApiError::internal)?.ok_or_else(unauthorized)?;
    let (member, print) = read_session(&key, token, Utc::now()).ok_or_else(unauthorized)?;
    // A member removed since the session began reads nothing more, and neither does a session
    // begun with a key the member has since replaced. The cookie names the person; the print
    // names the key (Legion, #964).
    if current_print(s, member).await.as_deref() != Some(print.as_str()) {
        return Err(unauthorized());
    }
    let is_member = { let l = s.ledger.lock().await; s.projected(&l).members.contains_key(&member) };
    if is_member { Ok(member) } else { Err(unauthorized()) }
}

/// `GET /me/view` — what this member owns and backs up, open jobs only.
///
/// surface: me_view   act: none (read of the caller's own commitments)
/// S: low/reversible   R: pass [construct: session_member; the cookie is a MAC this hub made]
/// W: pass [construct: a session minted only for a verified member signature]   O: n/a   A: n/a   V: n/a
/// verdict: PASS
pub(in crate::rest) async fn me_view(
    State(s): State<RestState>,
    headers: axum::http::HeaderMap,
) -> Result<axum::response::Response, ApiError> {
    use axum::response::IntoResponse;
    let member = session_member(&s, &headers).await?;
    let view = view_for(&s, member, Utc::now()).await?;
    Ok(([(axum::http::header::CACHE_CONTROL, "no-store")], Json(view)).into_response())
}

async fn view_for(s: &RestState, member: Uuid, now: DateTime<Utc>) -> Result<serde_json::Value, ApiError> {
    let state = { let l = s.ledger.lock().await; s.projected(&l) };
    let book = load_book(s)?;
    let me = member.to_string();
    let name = |p: &PartyRef| party_view(&state, &book, p)["name"].clone();
    let row = |c: &Commitment| {
        let role = if c.owner.party_id == me { LinkRole::Owner } else { LinkRole::Backup };
        let backup_name = name(&c.backup).as_str().unwrap_or("your backup").to_string();
        let acts: Vec<_> = acts_for(c, role, &me, None).into_iter()
            .map(|a| serde_json::json!({ "act": a.path(), "label": act_label(a, role, &backup_name) }))
            .collect();
        let waiting = match c.queue {
            commitments::QueuePos::Owner => c.owner.party_id == me,
            commitments::QueuePos::Backup => c.backup.party_id == me,
            commitments::QueuePos::Leads => false,
        };
        serde_json::json!({
            "commitment_id": c.commitment_id,
            "title": c.title,
            "due_at": c.due_at,
            "late": c.due_at.is_some_and(|d| d < now),
            "waiting_on_you": waiting,
            "queue": c.queue,
            "owner": name(&c.owner),
            "backup": name(&c.backup),
            "acts": acts,
        })
    };
    let open = || open_by_queue(&state).into_iter();
    let mine: Vec<_> = open().filter(|c| c.owner.party_id == me).map(row).collect();
    let backing_up: Vec<_> = open().filter(|c| c.backup.party_id == me).map(row).collect();
    Ok(serde_json::json!({
        "member_lct_id": member,
        "name": name(&PartyRef { party_id: me.clone(), kind: PartyKind::Member }),
        "hub": s.hub_name,
        "mine": mine,
        "backing_up": backing_up,
    }))
}

/// `POST /me/act` — a member answers on a job, signed with their own key (K5c2). The session
/// cookie reads; it never writes. Recorded `via: member_act`: the member's own word, the strongest
/// evidence an answer carries (PRD §5.1).
///
/// surface: me_act   act: record a member's own answer on a commitment (ack, update, done, stuck, handoff, take)
/// S: med/reversible [construct: the same acts a link offers; done is final, the rest move a queue the next answer moves again]
/// R: pass [construct: verify_envelope against the live resolver]
/// W: pass [construct: the member's pinned key signs a single-use challenge over the commitment and the act; role re-derived in act_as]
/// O: pass [construct: verify_envelope, member check, act_as role + offered-answers check under COMMITMENT_LOCK before checked_witness]
/// A: pass [construct: every entry carries via=member_act and the member's id as by/party]
/// V: n/a [construct: a mistaken done is corrected by the operator, as for a link]
/// verdict: PASS
pub(in crate::rest) async fn me_act(
    State(s): State<RestState>,
    Json(envelope): Json<SignedEnvelope>,
) -> Result<Json<serde_json::Value>, ApiError> {
    {
        let resolver = s.resolver.read().await;
        verify_envelope(&envelope, &s.nonces, &*resolver, Utc::now())?;
    }
    let p = &envelope.payload;
    if p.get("action").and_then(|a| a.as_str()) != Some(ACT_ACTION) {
        return Err(ApiError::bad_request(format!("an answer is signed with action='{ACT_ACTION}'")));
    }
    let field = |k: &str| p.get(k).and_then(|v| v.as_str())
        .ok_or_else(|| ApiError::bad_request(format!("{k} is required")));
    let commitment_id = field("commitment_id")?;
    let act = LinkAct::parse(field("act")?)
        .ok_or_else(|| ApiError::bad_request("act is one of acknowledge, update, done, stuck, handoff, take"))?;
    // act_as checks that the signer is a member, under the commitments lock.
    act_as(&s, commitment_id, &envelope.signer_lct_id.to_string(), act, AckVia::MemberAct, None).await.map(Json)
}

/// `GET /me` — the page. It holds the browser key, so it runs only its own files.
pub(in crate::rest) async fn me_page(State(s): State<RestState>) -> axum::response::Response {
    let hub = esc(&s.hub_name);
    link_page_response(StatusCode::OK, &format!("My jobs at {}", s.hub_name), &format!(
        "<h1>My jobs at {hub}</h1>\
         <p id=\"status\" class=\"muted\" role=\"status\">Loading…</p>\
         <div id=\"view\"></div>\
         <p id=\"persist\" class=\"muted\" hidden></p>\
         <script src=\"/keystore.js\"></script><script src=\"/me.js\"></script>"))
}

pub(in crate::rest) async fn me_js() -> axum::response::Response {
    use axum::response::IntoResponse;
    ([(axum::http::header::CONTENT_TYPE, "text/javascript; charset=utf-8")], ME_JS).into_response()
}

pub(crate) const ME_JS: &str = r##"'use strict';
const $=s=>document.querySelector(s);
function say(cls,msg){ const e=$('#status'); e.className=cls; e.textContent=msg; }
function el(tag,text,cls){ const e=document.createElement(tag); if(text!=null)e.textContent=text; if(cls)e.className=cls; return e; }
const view=()=>fetch('/me/view',{headers:{accept:'application/json'},credentials:'same-origin'});
async function signIn(id){
  const env=await signEnvelope(id,{action:'me_session'});
  const r=await fetch('/me/session',{method:'POST',headers:{'content-type':'application/json'},
    credentials:'same-origin',body:JSON.stringify(env)});
  if(!r.ok){ const o=await r.json().catch(()=>({})); throw new Error(o.error||('sign-in failed ('+r.status+')')); }
}
function section(title,rows,role){
  const box=el('section'); box.appendChild(el('h2',title));
  if(!rows.length){ box.appendChild(el('p','Nothing here.','muted')); return box; }
  for(const c of rows){
    const p=el('p'); p.appendChild(el('b',c.title));
    const acts=el('div');
    for(const a of (c.acts||[])){
      const b=el('button',a.label); b.dataset.cid=c.commitment_id; b.dataset.act=a.act; acts.appendChild(b);
    }
    const who=role==='owner'?(c.backup?'Backup: '+c.backup:''):(c.owner?'Owner: '+c.owner:'');
    if(who)p.appendChild(el('span',' · '+who,'muted'));
    if(c.due_at)p.appendChild(el('span',' · due '+c.due_at.slice(0,10),c.late?'err':'muted'));
    if(c.waiting_on_you)p.appendChild(el('span',' · waiting on you','err'));
    box.appendChild(p); box.appendChild(acts);
  }
  return box;
}
// An answer is signed with this browser's key; the session cookie only reads.
async function answer(cid,act){
  const id=await loadID(); if(!id)throw new Error('this browser holds no key for this hub');
  const env=await signEnvelope(id,{action:'commitment_act',commitment_id:cid,act});
  const r=await fetch('/me/act',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(env)});
  const o=await r.json().catch(()=>({}));
  if(!r.ok)throw new Error(o.error||('not recorded ('+r.status+')'));
}
document.addEventListener('click',async ev=>{
  const b=ev.target.closest&&ev.target.closest('button[data-act]'); if(!b)return;
  b.disabled=true;
  try{ await answer(b.dataset.cid,b.dataset.act); say('ok','Recorded.'); await main(); }
  catch(e){ say('err','Not recorded: '+e.message); b.disabled=false; }
});
// The page is opened from an email, a cross-site click that carries no Strict cookie: ask for the
// view, and on a 401 sign a fresh challenge with the key this browser already holds.
async function main(){
  try{
    let r=await view();
    if(r.status===401){
      const id=await loadID();
      if(!id){ say('err','This browser holds no key for this hub. Open your invite link in this browser, or ask your organiser.'); return; }
      await signIn(id);
      r=await view();
    }
    if(!r.ok){ const o=await r.json().catch(()=>({})); throw new Error(o.error||('could not load ('+r.status+')')); }
    const v=await r.json();
    if($('#status').className!=='ok')say('muted',v.name?('Signed in as '+v.name+'.'):'Signed in.');
    const out=$('#view'); out.textContent='';
    out.appendChild(section('Mine',v.mine,'owner'));
    out.appendChild(section('I\'m backing up',v.backing_up,'backup'));
    if(await ensurePersisted()===false){ const n=$('#persist'); n.textContent=NOT_PERSISTED; n.hidden=false; }
  }catch(e){
    if(e.message==='NO_ED25519')countUnsupported();
    say('err',e.message==='NO_ED25519'?NO_KEY_SUPPORT
      :e.message==='LEGACY_UNREADABLE'?'This browser holds an older key that can\'t be read. Ask your organiser.'
      :'Something went wrong: '+e.message);
  }
}
main();
"##;

#[cfg(test)]
mod tests {
    use super::*;
    use crate::rest::channel_e2e_tests::{fresh_rest_state, witness_for_test};
    use web4_core::crypto::KeyPair;

    /// A member whose key the hub resolves, as an admitted join leaves them.
    async fn member(s: &RestState, name: &str) -> (Uuid, KeyPair) {
        let (id, kp) = (Uuid::new_v4(), KeyPair::generate());
        let pubkey = kp.verifying_key().to_hex();
        witness_for_test(s, HubEvent::MemberAdded {
            member_lct_id: id, added_by: s.sovereign_lct_id, member_name: Some(name.into()),
            member_pubkey_hex: Some(pubkey.clone()), anchor_level: None, trust_ceiling: None,
        }).await;
        s.resolver.write().await.insert(hub_lib::hub::hestia_sovereign_lct(id, &pubkey).unwrap());
        (id, kp)
    }

    fn signed(s: &RestState, kp: &KeyPair, signer: Uuid, payload: serde_json::Value) -> SignedEnvelope {
        let challenge = s.nonces.issue(signer, Utc::now());
        let mut env = SignedEnvelope {
            challenge_nonce: challenge.nonce.clone(), payload, signature: String::new(), signer_lct_id: signer,
        };
        env.signature = kp.sign(&env.signing_bytes().unwrap()).to_hex();
        env
    }

    async fn call(s: &RestState, method: &str, path: &str, cookie: Option<&str>, body: Option<String>)
        -> (StatusCode, axum::http::HeaderMap, String)
    {
        use tower::ServiceExt;
        let mut req = axum::http::Request::builder().method(method).uri(path);
        if let Some(c) = cookie {
            req = req.header(axum::http::header::COOKIE, c);
        }
        if body.is_some() {
            req = req.header(axum::http::header::CONTENT_TYPE, "application/json");
        }
        let req = req.body(body.map_or_else(axum::body::Body::empty, axum::body::Body::from)).unwrap();
        let resp = crate::rest::router(s.clone()).oneshot(req).await.unwrap();
        let (status, headers) = (resp.status(), resp.headers().clone());
        let bytes = axum::body::to_bytes(resp.into_body(), usize::MAX).await.unwrap();
        (status, headers, String::from_utf8_lossy(&bytes).into_owned())
    }

    async fn sign_in(s: &RestState, kp: &KeyPair, id: Uuid) -> String {
        let env = signed(s, kp, id, serde_json::json!({ "action": "me_session" }));
        let (status, headers, body) = call(s, "POST", "/me/session", None, Some(serde_json::to_string(&env).unwrap())).await;
        assert_eq!(status, StatusCode::OK, "{body}");
        let set = headers[axum::http::header::SET_COOKIE].to_str().unwrap().to_string();
        set.split(';').next().unwrap().to_string()
    }

    #[tokio::test]
    async fn a_member_signs_in_with_their_key_and_reads_only_their_own_jobs() {
        let (_tmp, s) = fresh_rest_state(None).await;
        let (alex, alex_kp) = member(&s, "Alex").await;
        let (sam, _) = member(&s, "Sam").await;
        let (lee, _) = member(&s, "Lee").await;
        let role = Uuid::new_v4();
        witness_for_test(&s, HubEvent::RoleCreated {
            role_lct_id: role, role: web4_core::role::SocietyRole::Custom("leads".into()),
            role_kind: hub_lib::events::RoleKind::Capacity, charter: None, parent_role_lct_id: None,
            initial_occupant: None, created_by: s.sovereign_lct_id,
        }).await;
        let m = |id: Uuid| PartyRef { party_id: id.to_string(), kind: PartyKind::Member };
        let open = |owner, backup, title: &str, due| OpenBody { title: title.into(), owner, backup,
            leads_role: role.to_string(), ladder: vec![48, 24], due_at: due };
        let past = Some(Utc::now() - chrono::Duration::days(1));
        let venue = open_commitment(&s, open(m(alex), m(sam), "Venue AV", past)).await.unwrap();
        let snacks = open_commitment(&s, open(m(sam), m(alex), "Snacks", None)).await.unwrap();
        open_commitment(&s, open(m(sam), m(lee), "Not Alex's", None)).await.unwrap();

        // No session: 401, and nothing about anyone.
        let (status, _, body) = call(&s, "GET", "/me/view", None, None).await;
        assert_eq!(status, StatusCode::UNAUTHORIZED, "{body}");
        assert!(!body.contains("Venue"));

        let cookie = sign_in(&s, &alex_kp, alex).await;
        let (status, headers, body) = call(&s, "GET", "/me/view", Some(&cookie), None).await;
        assert_eq!(status, StatusCode::OK, "{body}");
        assert_eq!(headers[axum::http::header::CACHE_CONTROL], "no-store");
        let v: serde_json::Value = serde_json::from_str(&body).unwrap();
        assert_eq!(v["name"], "Alex");
        assert_eq!(v["mine"].as_array().unwrap().len(), 1);
        assert_eq!(v["mine"][0]["title"], "Venue AV");
        assert_eq!((v["mine"][0]["late"].as_bool(), v["mine"][0]["waiting_on_you"].as_bool()), (Some(true), Some(true)));
        assert_eq!(v["mine"][0]["backup"], "Sam");
        assert_eq!(v["backing_up"].as_array().unwrap().len(), 1);
        assert_eq!((v["backing_up"][0]["title"].as_str(), v["backing_up"][0]["waiting_on_you"].as_bool()),
            (Some("Snacks"), Some(false)), "Sam's queue, not Alex's");
        assert_eq!(v["backing_up"][0]["late"].as_bool(), Some(false), "no due date is never late");
        assert!(!body.contains("Not Alex's"));

        // Each says "stuck": the queue moves to the backup, so Snacks now waits on Alex, and
        // Venue AV no longer does.
        for (id, by) in [(&venue, alex), (&snacks, sam)] {
            move_commitment(&s, id["commitment_id"].as_str().unwrap(), MoveBody { by: by.to_string(),
                move_kind: MoveKind::Stuck, to: None, note_ref: None }).await.unwrap();
        }
        let v: serde_json::Value = serde_json::from_str(&call(&s, "GET", "/me/view", Some(&cookie), None).await.2).unwrap();
        assert_eq!(v["mine"][0]["waiting_on_you"].as_bool(), Some(false), "Venue AV waits on Sam now");
        assert_eq!(v["backing_up"][0]["waiting_on_you"].as_bool(), Some(true), "Snacks waits on Alex now");

        // A session begun with a key Alex has since replaced reads nothing; the new key signs in.
        let new_kp = KeyPair::generate();
        crate::rest::pin_member_key(&s, alex, &new_kp.verifying_key().to_hex()).await.unwrap();
        assert_eq!(call(&s, "GET", "/me/view", Some(&cookie), None).await.0, StatusCode::UNAUTHORIZED);
        let cookie = sign_in(&s, &new_kp, alex).await;
        assert_eq!(call(&s, "GET", "/me/view", Some(&cookie), None).await.0, StatusCode::OK);

        // A removed member's session reads nothing more.
        witness_for_test(&s, HubEvent::MemberRemoved { member_lct_id: alex, removed_by: s.sovereign_lct_id,
            reason: None }).await;
        assert_eq!(call(&s, "GET", "/me/view", Some(&cookie), None).await.0, StatusCode::UNAUTHORIZED);
    }

    #[tokio::test]
    async fn a_session_needs_this_members_signature_on_the_session_action() {
        let (_tmp, s) = fresh_rest_state(None).await;
        let (alex, alex_kp) = member(&s, "Alex").await;
        let (_sam, sam_kp) = member(&s, "Sam").await;
        let post = |env: SignedEnvelope| serde_json::to_string(&env).unwrap();
        // Sam's key claiming to be Alex.
        let forged = signed(&s, &sam_kp, alex, serde_json::json!({ "action": "me_session" }));
        assert_eq!(call(&s, "POST", "/me/session", None, Some(post(forged))).await.0, StatusCode::UNAUTHORIZED);
        // Alex's key, signing something else.
        let other = signed(&s, &alex_kp, alex, serde_json::json!({ "action": "member_withdraw" }));
        assert_eq!(call(&s, "POST", "/me/session", None, Some(post(other))).await.0, StatusCode::BAD_REQUEST);
        // A key the hub resolves for someone who is not a member: no view.
        let (stranger, stranger_kp) = (Uuid::new_v4(), KeyPair::generate());
        s.resolver.write().await.insert(
            hub_lib::hub::hestia_sovereign_lct(stranger, &stranger_kp.verifying_key().to_hex()).unwrap());
        let env = signed(&s, &stranger_kp, stranger, serde_json::json!({ "action": "me_session" }));
        assert_eq!(call(&s, "POST", "/me/session", None, Some(post(env))).await.0, StatusCode::FORBIDDEN);
        // A nonce is spent once.
        let env = signed(&s, &alex_kp, alex, serde_json::json!({ "action": "me_session" }));
        assert_eq!(call(&s, "POST", "/me/session", None, Some(post(env.clone()))).await.0, StatusCode::OK);
        assert_ne!(call(&s, "POST", "/me/session", None, Some(post(env))).await.0, StatusCode::OK);
    }

    async fn leads(s: &RestState) -> Uuid {
        let role = Uuid::new_v4();
        witness_for_test(s, HubEvent::RoleCreated {
            role_lct_id: role, role: web4_core::role::SocietyRole::Custom("leads".into()),
            role_kind: hub_lib::events::RoleKind::Capacity, charter: None, parent_role_lct_id: None,
            initial_occupant: None, created_by: s.sovereign_lct_id,
        }).await;
        role
    }

    async fn answer(s: &RestState, kp: &KeyPair, signer: Uuid, cid: &str, act: &str) -> (StatusCode, String) {
        let env = signed(s, kp, signer, serde_json::json!({ "action": "commitment_act", "commitment_id": cid, "act": act }));
        let (status, _, body) = call(s, "POST", "/me/act", None, Some(serde_json::to_string(&env).unwrap())).await;
        (status, body)
    }

    async fn last(s: &RestState) -> HubEvent {
        s.ledger.lock().await.entries().last().unwrap().event.clone()
    }

    #[tokio::test]
    async fn a_member_answers_with_their_own_key_and_it_is_their_own_word() {
        let (_tmp, s) = fresh_rest_state(None).await;
        let (alex, alex_kp) = member(&s, "Alex").await;
        let (sam, sam_kp) = member(&s, "Sam").await;
        let (lee, lee_kp) = member(&s, "Lee").await;
        let role = leads(&s).await;
        let m = |id: Uuid| PartyRef { party_id: id.to_string(), kind: PartyKind::Member };
        let v = open_commitment(&s, OpenBody { title: "Venue AV".into(), owner: m(alex), backup: m(sam),
            leads_role: role.to_string(), ladder: vec![48, 24], due_at: None }).await.unwrap();
        let cid = v["commitment_id"].as_str().unwrap().to_string();

        // The view offers what a link would, labelled for this member.
        let cookie = sign_in(&s, &alex_kp, alex).await;
        let view = |c: String| { let s = s.clone(); async move {
            serde_json::from_str::<serde_json::Value>(&call(&s, "GET", "/me/view", Some(&c), None).await.2).unwrap() } };
        let acts = |v: &serde_json::Value| v["mine"][0]["acts"].as_array().unwrap().iter()
            .map(|a| a["act"].as_str().unwrap().to_string()).collect::<Vec<_>>();
        let before = view(cookie.clone()).await;
        assert_eq!(acts(&before), ["acknowledge", "update", "done", "stuck", "handoff"]);
        assert_eq!(before["mine"][0]["acts"][4]["label"], "Hand it to Sam");

        let (status, body) = answer(&s, &alex_kp, alex, &cid, "acknowledge").await;
        assert_eq!(status, StatusCode::OK, "{body}");
        assert!(matches!(last(&s).await, HubEvent::CommitmentAcknowledged { via: AckVia::MemberAct, link_digest: None,
            party_id, .. } if party_id == alex.to_string()));
        { let l = s.ledger.lock().await; assert!(s.projected(&l).commitments[&cid].owner_acknowledged()); }
        assert!(!acts(&view(cookie.clone()).await).contains(&"acknowledge".to_string()), "said once");
        assert_eq!(answer(&s, &alex_kp, alex, &cid, "acknowledge").await.0, StatusCode::CONFLICT);

        // Stuck moves it to Sam; Sam takes it over, by Sam's own key.
        assert_eq!(answer(&s, &alex_kp, alex, &cid, "stuck").await.0, StatusCode::OK);
        let (status, body) = answer(&s, &sam_kp, sam, &cid, "take").await;
        assert_eq!(status, StatusCode::OK, "{body}");
        assert!(matches!(last(&s).await, HubEvent::CommitmentMoved { via: AckVia::MemberAct, move_kind: MoveKind::Handoff,
            by, .. } if by == sam.to_string()));
        { let l = s.ledger.lock().await; assert_eq!(s.projected(&l).commitments[&cid].owner.party_id, sam.to_string()); }

        // Refused: someone not on the job, a key signing for another member, the wrong action,
        // and an answer that is not one.
        let ledger_len = s.ledger.lock().await.len();
        assert_eq!(answer(&s, &lee_kp, lee, &cid, "done").await.0, StatusCode::FORBIDDEN);
        assert_eq!(answer(&s, &lee_kp, sam, &cid, "done").await.0, StatusCode::UNAUTHORIZED);
        assert_eq!(answer(&s, &sam_kp, sam, &cid, "explode").await.0, StatusCode::BAD_REQUEST);
        let env = signed(&s, &sam_kp, sam, serde_json::json!({ "action": "me_session", "commitment_id": cid, "act": "done" }));
        assert_eq!(call(&s, "POST", "/me/act", None, Some(serde_json::to_string(&env).unwrap())).await.0,
            StatusCode::BAD_REQUEST);
        assert_eq!(s.ledger.lock().await.len(), ledger_len, "no refusal reaches the ledger");

        // A key the hub resolves, held by someone who sits in the leads role but is not a member,
        // does not answer as a member.
        let (stranger, stranger_kp) = (Uuid::new_v4(), KeyPair::generate());
        s.resolver.write().await.insert(
            hub_lib::hub::hestia_sovereign_lct(stranger, &stranger_kp.verifying_key().to_hex()).unwrap());
        let their_leads = Uuid::new_v4();
        witness_for_test(&s, HubEvent::RoleCreated {
            role_lct_id: their_leads, role: web4_core::role::SocietyRole::Custom("leads".into()),
            role_kind: hub_lib::events::RoleKind::Capacity, charter: None, parent_role_lct_id: None,
            initial_occupant: Some(stranger), created_by: s.sovereign_lct_id,
        }).await;
        let v = open_commitment(&s, OpenBody { title: "Chairs".into(), owner: m(alex), backup: m(lee),
            leads_role: their_leads.to_string(), ladder: vec![48], due_at: None }).await.unwrap();
        let (status, body) = answer(&s, &stranger_kp, stranger, v["commitment_id"].as_str().unwrap(), "take").await;
        assert_eq!(status, StatusCode::FORBIDDEN, "{body}");
        assert!(body.contains("only a member"), "{body}");
    }

    #[test]
    fn a_session_is_its_own_kind_of_token_and_lives_twelve_hours() {
        let key = [3u8; 32];
        let (alex, now) = (Uuid::new_v4(), Utc::now());
        let t = mint_session(&key, alex, "0123456789abcdef", now + chrono::Duration::hours(12));
        assert_eq!(read_session(&key, &t, now), Some((alex, "0123456789abcdef".to_string())));
        assert_eq!(read_session(&key, &t, now + chrono::Duration::hours(12)), None, "expired");
        assert_eq!(read_session(&[4u8; 32], &t, now), None, "another hub's key");
        // A movement link and an invite never read as a session, nor does a token with a
        // session's field count under another label.
        let three = mint_token(LINK_MAC_LABEL, &key, &[&alex.to_string(), "0123456789abcdef", "00"], now + chrono::Duration::hours(1));
        assert_eq!(read_session(&key, &three, now), None);
        assert_eq!(read_session(&key, &mint_link(&key, &alex.to_string(), "x", now + chrono::Duration::hours(1)), now), None);
        assert_eq!(read_session(&key, &mint_invite(&key, &alex.to_string(), now + chrono::Duration::hours(1)), now), None);
        assert_eq!(ME_SESSION_HOURS, 12);

        let c = session_cookie(&t, Some("https://hub.example.org"));
        for part in ["Path=/me", "Max-Age=43200", "HttpOnly", "SameSite=Strict", "Secure"] {
            assert!(c.contains(part), "{part} missing: {c}");
        }
        assert!(!session_cookie(&t, Some("http://10.0.0.5:8770")).contains("Secure"));
        let mut h = axum::http::HeaderMap::new();
        h.insert(axum::http::header::COOKIE, format!("a=b; {ME_COOKIE}={t}; c=d").parse().unwrap());
        assert_eq!(cookie_value(&h, ME_COOKIE), Some(t.as_str()));
    }

    #[tokio::test]
    async fn the_me_page_runs_only_its_own_files() {
        let (_tmp, s) = fresh_rest_state(None).await;
        let (status, headers, html) = call(&s, "GET", "/me", None, None).await;
        assert_eq!(status, StatusCode::OK);
        assert_eq!(headers[axum::http::header::CONTENT_SECURITY_POLICY], crate::rest::KEY_PAGE_CSP);
        assert!(html.contains("<script src=\"/keystore.js\"></script><script src=\"/me.js\"></script>"), "{html}");
        assert!(!html.contains("onclick") && !html.contains("style="), "{html}");
        let dir = tempfile::tempdir().unwrap();
        let js = dir.path().join("me.js");
        std::fs::write(&js, ME_JS).unwrap();
        match std::process::Command::new("node").arg("--check").arg(&js).output() {
            Ok(out) => assert!(out.status.success(), "{}", String::from_utf8_lossy(&out.stderr)),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => eprintln!("SKIPPED: node is not on PATH"),
            Err(e) => panic!("running node: {e}"),
        }
        assert!(!ME_JS.contains("innerHTML"), "the view is built from text nodes, so no name is ever markup");
    }
}
