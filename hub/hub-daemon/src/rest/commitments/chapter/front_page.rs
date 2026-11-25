//! The chapter's front page (`hub/docs/PRD_CHAPTER_FRONT_PAGE.md`): what a visitor sees at `/`,
//! kept by a **page maintainer**.
//!
//! Page maintainer is a role. A chapter lead fills it with their own AI assistant from their
//! chapter page, and the assistant acts through a link minted for that appointment:
//!
//! - `GET  /a/:token`: the role packet, in Markdown, for the assistant to read. It holds who it
//!   acts for, what the chapter's law says about the role right now, the role's context (the
//!   chapter's brief), what the page says now, and how to change it.
//! - `GET  /a/:token/page`: the page now, as JSON.
//! - `POST /a/:token/page`: a new page, as JSON.
//! - `POST /a/:token/brief`: a new brief, as text.
//!
//! **Every change is a governed act.** The hub evaluates it against the chapter's law as an R6
//! request with `role = page_maintainer` (or `chapter_lead` when a lead presses a button) and
//! `action = chapter_page_set`. Allow publishes and records it. Escalate keeps it as a proposal
//! until a lead presses Publish. Deny refuses it. The record names the lead answerable for the
//! change and the assistant that wrote it. Any chapter lead can undo the page, and can stop any
//! assistant.
//!
//! The page is structured content rendered escaped (`hub_lib::chapter_page`), so nothing an
//! assistant writes runs on it. It never shows a person: committees appear by name and purpose
//! only.

use super::*;
use hub_lib::chapter::{Maintainer, PageVersion};
use hub_lib::chapter_page::{self as cp, PageContent, PagePart, PageVia, PAGE_MAINTAINER};

const MAINTAINER_LABEL: &[u8] = b"web4-hub chapter maintainer v1\n";
const MAINTAINER_TTL_DAYS: i64 = 30;
/// The R6 role a chapter lead acts in from their own page.
pub(crate) const ROLE_CHAPTER_LEAD: &str = "chapter_lead";

// ---------------------------------------------------------------------------------------------
// The page file: every version's content, by digest, and a waiting proposal. Off the ledger.
// ---------------------------------------------------------------------------------------------

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub(crate) struct PageFile {
    #[serde(default)]
    pub pages: BTreeMap<String, PageContent>,
    #[serde(default)]
    pub briefs: BTreeMap<String, String>,
    /// A maintainer's change the law sent to a lead. One at a time per part; a newer one replaces it.
    #[serde(default)]
    pub pending: BTreeMap<String, Pending>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub(crate) struct Pending {
    pub part: PagePart,
    pub sha256: String,
    pub maintainer_id: String,
    pub by: String,
    pub at: DateTime<Utc>,
    pub norm: String,
}

fn page_path(root: &std::path::Path) -> std::path::PathBuf {
    root.join("chapter-page.json")
}

pub(crate) fn load_page_file(root: &std::path::Path) -> Result<PageFile, ApiError> {
    match std::fs::read(page_path(root)) {
        Ok(b) => serde_json::from_slice(&b).map_err(|e| ApiError::internal(anyhow::anyhow!("page file: {e}"))),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(PageFile::default()),
        Err(e) => Err(ApiError::internal(e.into())),
    }
}

fn save_page_file(root: &std::path::Path, f: &PageFile) -> Result<(), ApiError> {
    let bytes = serde_json::to_vec_pretty(f).map_err(|e| ApiError::internal(e.into()))?;
    hub_lib::atomic_file::write_atomic_mode(&page_path(root), bytes, 0o600).map_err(ApiError::internal)
}

/// The page in force, if a version was ever published and its content is on file.
pub(crate) fn current_page(state: &HubState, file: &PageFile) -> Option<(PageContent, PageVersion)> {
    let v = state.chapter.current(PagePart::Page)?;
    file.pages.get(&v.sha256).map(|p| (p.clone(), v.clone()))
}

/// The brief in force: the chapter's own, or the default for its name.
pub(crate) fn current_brief(state: &HubState, file: &PageFile, hub_name: &str) -> String {
    state.chapter.current(PagePart::Brief)
        .and_then(|v| file.briefs.get(&v.sha256).cloned())
        .unwrap_or_else(|| cp::default_brief(hub_name))
}

/// A part's content, ready to store.
#[derive(Clone, Debug)]
pub(crate) enum PartContent {
    Page(PageContent),
    Brief(String),
}

impl PartContent {
    fn part(&self) -> PagePart {
        match self {
            PartContent::Page(_) => PagePart::Page,
            PartContent::Brief(_) => PagePart::Brief,
        }
    }

    /// Validate, normalize, and name by digest.
    fn prepared(self) -> Result<(PartContent, String), ApiError> {
        match self {
            PartContent::Page(p) => {
                p.validate().map_err(|e| ApiError::bad_request(e.0))?;
                let n = p.normalized();
                let d = n.digest();
                Ok((PartContent::Page(n), d))
            }
            PartContent::Brief(b) => {
                cp::validate_brief(&b).map_err(|e| ApiError::bad_request(e.0))?;
                let n = cp::normalize_brief(&b);
                let d = cp::brief_digest(&n);
                Ok((PartContent::Brief(n), d))
            }
        }
    }

    fn store(&self, file: &mut PageFile, sha: &str) {
        match self {
            PartContent::Page(p) => { file.pages.insert(sha.to_string(), p.clone()); }
            PartContent::Brief(b) => { file.briefs.insert(sha.to_string(), b.clone()); }
        }
    }
}

// ---------------------------------------------------------------------------------------------
// The law: every front-page act is an R6 request the chapter's law decides
// ---------------------------------------------------------------------------------------------

#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) enum LawSays {
    Allow,
    /// The act waits for a person. The norm that said so.
    Escalate(String),
    Deny(String),
}

/// What the chapter's law says about `event` done in `role`. No law loaded allows, as the
/// single-signer gate does.
pub(crate) async fn law_says(s: &RestState, role: &str, event: &HubEvent) -> Result<LawSays, ApiError> {
    let guard = s.law.read().await;
    let Some(law) = guard.as_ref() else { return Ok(LawSays::Allow) };
    let req = hub_lib::law::R6Request {
        role: role.to_string(),
        action: event.kind().to_string(),
        payload: serde_yaml::to_value(event)
            .map_err(|e| ApiError::internal(anyhow::anyhow!("serializing event for R6: {e}")))?,
        resource: Default::default(),
    };
    let out = law.evaluate_outcome(&req);
    let norm = out.winning_norm.clone().unwrap_or_else(|| "an escalation trigger".to_string());
    Ok(match out.decision {
        hub_lib::law::Decision::Allow | hub_lib::law::Decision::Warn => LawSays::Allow,
        hub_lib::law::Decision::Escalate => LawSays::Escalate(norm),
        hub_lib::law::Decision::Deny => LawSays::Deny(norm),
    })
}

/// Witness `event` if the law allows it in `role`. Escalate and deny are refusals here; only a
/// maintainer's page change has somewhere to wait ([`set_part`]). The caller holds
/// [`COMMITMENT_LOCK`].
async fn governed_witness(s: &RestState, role: &str, event: HubEvent) -> Result<u64, ApiError> {
    match law_says(s, role, &event).await? {
        LawSays::Allow => chapter_witness(s, event).await,
        LawSays::Escalate(norm) => Err(ApiError { status: StatusCode::FORBIDDEN,
            message: format!("the chapter's law sends this to a person first (norm {norm}), and there's no queue for it yet") }),
        LawSays::Deny(norm) => Err(ApiError { status: StatusCode::FORBIDDEN,
            message: format!("the chapter's law doesn't allow this (norm {norm})") }),
    }
}

/// What a set did.
#[derive(Clone, Debug, PartialEq, Eq)]
pub(crate) enum SetOutcome {
    Published { sha256: String },
    /// Already what the page says: nothing written.
    Unchanged { sha256: String },
    /// The law sent it to a lead, who publishes or discards it from their chapter page.
    Waiting { sha256: String, norm: String },
}

impl SetOutcome {
    fn json(&self, part: PagePart) -> serde_json::Value {
        let base = link_base().unwrap_or_default();
        match self {
            SetOutcome::Published { sha256 } => serde_json::json!({ "result": "published", "part": part.as_str(),
                "sha256": sha256, "url": format!("{base}/"),
                "note": "Live now. It's recorded under the co-lead who appointed you, and any co-lead can undo it." }),
            SetOutcome::Unchanged { sha256 } => serde_json::json!({ "result": "unchanged", "part": part.as_str(),
                "sha256": sha256, "note": "That's already what it says. Nothing was written." }),
            SetOutcome::Waiting { sha256, norm } => serde_json::json!({ "result": "waiting_for_a_co_lead",
                "part": part.as_str(), "sha256": sha256, "norm": norm,
                "note": "The chapter's rules ask a co-lead to publish this. It's waiting on their chapter page; tell the co-lead who appointed you." }),
        }
    }
}

/// Set a part of the front page: validate, ask the law, then publish or leave it waiting.
///
/// `by` is the chapter lead answerable (the one acting, or the one who appointed `maintainer_id`).
/// O: the content is written to the page file only after the law has decided, and a refusal
/// writes nothing. The content goes to the file before the ledger names its digest, so a
/// recorded version always has its words on file. The caller holds [`COMMITMENT_LOCK`].
pub(crate) async fn set_part(
    s: &RestState, content: PartContent, by: &str, via: PageVia, maintainer_id: Option<String>,
    link_digest: Option<String>,
) -> Result<SetOutcome, ApiError> {
    let part = content.part();
    let (content, sha) = content.prepared()?;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    if state.chapter.current(part).is_some_and(|v| v.sha256 == sha) {
        return Ok(SetOutcome::Unchanged { sha256: sha });
    }
    let role = if via == PageVia::Maintainer { PAGE_MAINTAINER } else { ROLE_CHAPTER_LEAD };
    let event = HubEvent::ChapterPageSet { part, sha256: sha.clone(), by: by.to_string(), via,
        maintainer_id: maintainer_id.clone(), link_digest };
    ch::check(&state.chapter, &event).map_err(ch_refused)?;
    let mut file = load_page_file(&s.paths.root)?;
    match law_says(s, role, &event).await? {
        LawSays::Deny(norm) => Err(ApiError { status: StatusCode::FORBIDDEN,
            message: format!("the chapter's law doesn't allow this (norm {norm}). Nothing was stored.") }),
        LawSays::Escalate(norm) => {
            let Some(mid) = maintainer_id.filter(|_| via == PageVia::Maintainer) else {
                return Err(ApiError { status: StatusCode::FORBIDDEN,
                    message: format!("the chapter's law sends this to a person first (norm {norm})") });
            };
            content.store(&mut file, &sha);
            file.pending.insert(part.as_str().to_string(), Pending { part, sha256: sha.clone(), maintainer_id: mid,
                by: by.to_string(), at: Utc::now(), norm: norm.clone() });
            save_page_file(&s.paths.root, &file)?;
            Ok(SetOutcome::Waiting { sha256: sha, norm })
        }
        LawSays::Allow => {
            content.store(&mut file, &sha);
            file.pending.remove(part.as_str());
            save_page_file(&s.paths.root, &file)?;
            chapter_witness(s, event).await?;
            Ok(SetOutcome::Published { sha256: sha })
        }
    }
}

/// A chapter lead publishes the waiting proposal for `part`.
pub(crate) async fn publish_pending(s: &RestState, me: &str, part: PagePart, link_digest: Option<String>)
    -> Result<SetOutcome, ApiError>
{
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    require_chapter_lead(&state, me)?;
    let file = load_page_file(&s.paths.root)?;
    let p = file.pending.get(part.as_str()).cloned()
        .ok_or_else(|| ApiError::not_found("nothing is waiting to be published"))?;
    let content = match part {
        PagePart::Page => PartContent::Page(file.pages.get(&p.sha256).cloned()
            .ok_or_else(|| ApiError::internal(anyhow::anyhow!("waiting page content missing")))?),
        PagePart::Brief => PartContent::Brief(file.briefs.get(&p.sha256).cloned()
            .ok_or_else(|| ApiError::internal(anyhow::anyhow!("waiting brief missing")))?),
    };
    set_part(s, content, me, PageVia::Link, Some(p.maintainer_id), link_digest).await
}

/// A chapter lead drops the waiting proposal for `part`. Nothing reaches the ledger: it was never
/// in force.
pub(crate) async fn discard_pending(s: &RestState, me: &str, part: PagePart) -> Result<(), ApiError> {
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    require_chapter_lead(&state, me)?;
    let mut file = load_page_file(&s.paths.root)?;
    if file.pending.remove(part.as_str()).is_none() {
        return Err(ApiError::not_found("nothing is waiting"));
    }
    save_page_file(&s.paths.root, &file)
}

/// A chapter lead puts the page back to the version before the one in force.
pub(crate) async fn undo_page(s: &RestState, me: &str, link_digest: Option<String>) -> Result<SetOutcome, ApiError> {
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    require_chapter_lead(&state, me)?;
    let versions: Vec<&PageVersion> = state.chapter.versions(PagePart::Page).collect();
    let Some(current) = versions.last() else { return Err(ApiError::bad_request("the page has never been changed")) };
    let Some(previous) = versions.iter().rev().find(|v| v.sha256 != current.sha256) else {
        return Err(ApiError::bad_request("there's no earlier version to go back to"));
    };
    let file = load_page_file(&s.paths.root)?;
    let content = file.pages.get(&previous.sha256).cloned()
        .ok_or_else(|| ApiError::internal(anyhow::anyhow!("earlier page content missing")))?;
    set_part(s, PartContent::Page(content), me, PageVia::Link, None, link_digest).await
}

fn require_chapter_lead(state: &HubState, me: &str) -> Result<(), ApiError> {
    if is_chapter_lead(state, me) {
        Ok(())
    } else {
        Err(ApiError { status: StatusCode::FORBIDDEN, message: "only a chapter lead can do that".into() })
    }
}

// ---------------------------------------------------------------------------------------------
// Appointing and stopping a page maintainer
// ---------------------------------------------------------------------------------------------

fn mint_maintainer(key: &[u8; 32], maintainer_id: &str, expires: DateTime<Utc>) -> String {
    mint_token(MAINTAINER_LABEL, key, &[maintainer_id], expires)
}

/// The link an assistant acts through. Deterministic, so its lead can see it again.
pub(crate) fn maintainer_url(base: &str, key: &[u8; 32], m: &Maintainer) -> String {
    format!("{base}/a/{}", mint_maintainer(key, &m.maintainer_id, m.expires_at))
}

/// A chapter lead appoints their own assistant as page maintainer. The caller holds
/// [`COMMITMENT_LOCK`]. Returns the maintainer's id.
pub(crate) async fn appoint_maintainer(s: &RestState, me: &str, label: &str, link_digest: Option<String>)
    -> Result<String, ApiError>
{
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    require_chapter_lead(&state, me)?;
    let id = ch::new_id();
    let via = if link_digest.is_some() { AckVia::Link } else { AckVia::Operator };
    let expires_at = Utc::now() + chrono::Duration::days(MAINTAINER_TTL_DAYS);
    let event = HubEvent::ChapterMaintainerAppointed { maintainer_id: id.clone(), role: PAGE_MAINTAINER.to_string(),
        label: label.trim().to_string(), appointed_by: me.to_string(), expires_at, via, link_digest };
    governed_witness(s, ROLE_CHAPTER_LEAD, event).await?;
    Ok(id)
}

/// Any chapter lead stops any assistant: co-leads check each other. The caller holds
/// [`COMMITMENT_LOCK`].
pub(crate) async fn stop_maintainer(s: &RestState, me: &str, maintainer_id: &str, link_digest: Option<String>)
    -> Result<(), ApiError>
{
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    require_chapter_lead(&state, me)?;
    let via = if link_digest.is_some() { AckVia::Link } else { AckVia::Operator };
    let event = HubEvent::ChapterMaintainerRevoked { maintainer_id: maintainer_id.to_string(), by: me.to_string(),
        via, link_digest };
    governed_witness(s, ROLE_CHAPTER_LEAD, event).await.map(|_| ())
}

/// A maintainer link, verified, and read as who it acts for now.
struct MaintainerClaim {
    maintainer: Maintainer,
    /// The appointing lead, as who they are now.
    lead: String,
    digest: String,
    token: String,
}

fn json_refusal(status: StatusCode, msg: &str) -> ApiError {
    ApiError { status, message: msg.to_string() }
}

fn verified_maintainer(s: &RestState, state: &HubState, token: &str) -> Result<MaintainerClaim, ApiError> {
    let key = read_link_key(&s.paths.root).map_err(ApiError::internal)?
        .ok_or_else(|| json_refusal(StatusCode::NOT_FOUND, "this link doesn't work"))?;
    let (mut fields, digest) = read_token(MAINTAINER_LABEL, &key, token, 1, Utc::now()).map_err(|e| match e {
        LinkError::Invalid => json_refusal(StatusCode::NOT_FOUND, "this link doesn't work"),
        LinkError::Expired => json_refusal(StatusCode::GONE,
            "this link has expired: ask the co-lead who appointed you for a new one"),
    })?;
    let id = fields.pop().expect("one field");
    let m = state.chapter.live_maintainer(&id).cloned()
        .ok_or_else(|| json_refusal(StatusCode::FORBIDDEN, "a co-lead stopped this assistant: this link no longer acts"))?;
    let lead = state.invites.canonical_id(&m.appointed_by);
    if !is_chapter_lead(state, &lead) {
        return Err(json_refusal(StatusCode::FORBIDDEN,
            "the co-lead who appointed you isn't a chapter lead any more, so this link no longer acts"));
    }
    Ok(MaintainerClaim { maintainer: m, lead, digest, token: token.to_string() })
}

// ---------------------------------------------------------------------------------------------
// The maintainer's routes: /a/:token
// ---------------------------------------------------------------------------------------------

fn agent_headers() -> [(axum::http::HeaderName, &'static str); 2] {
    [(axum::http::header::CACHE_CONTROL, "no-store"), (axum::http::header::REFERRER_POLICY, "no-referrer")]
}

/// What the chapter's law says about this role right now, in words.
async fn law_line(s: &RestState, claim: &MaintainerClaim, part: PagePart) -> String {
    let probe = HubEvent::ChapterPageSet { part, sha256: format!("sha256:{}", "0".repeat(64)), by: claim.lead.clone(),
        via: PageVia::Maintainer, maintainer_id: Some(claim.maintainer.maintainer_id.clone()), link_digest: None };
    match law_says(s, PAGE_MAINTAINER, &probe).await {
        Ok(LawSays::Allow) => "**allowed**: your change goes live at once".to_string(),
        Ok(LawSays::Escalate(n)) => format!("**waits for a co-lead** (norm `{n}`): your change is held until a co-lead publishes it"),
        Ok(LawSays::Deny(n)) => format!("**not allowed** (norm `{n}`)"),
        Err(_) => "unknown right now".to_string(),
    }
}

/// `GET /a/:token` — the role packet: everything an assistant needs to keep the page, in one read.
///
/// surface: chapter_maintainer_packet   act: none (a read)
/// S: low [no write]   R: pass [HMAC over maintainer + expiry; live, unrevoked, its lead still leads]
/// W: n/a   O: n/a   A: n/a   V: n/a — discloses only what the front page and brief already say,
///    committee names and purposes, and the appointing lead's first name.
/// verdict: PASS
pub(crate) async fn maintainer_packet(State(s): State<RestState>, Path(token): Path<String>) -> axum::response::Response {
    use axum::response::IntoResponse;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let claim = match verified_maintainer(&s, &state, &token) {
        Ok(c) => c,
        Err(e) => return e.into_response(),
    };
    let book = load_book(&s).unwrap_or_default();
    let file = load_page_file(&s.paths.root).unwrap_or_default();
    let base = link_base().unwrap_or_default();
    let lead = first_name(&name_by_id(&state, &book, &claim.lead));
    let page_json = match current_page(&state, &file) {
        Some((p, _)) => serde_json::to_string_pretty(&p).unwrap_or_default(),
        None => "null   (nothing published yet: the page shows placeholders)".to_string(),
    };
    // The same list the page shows: the committee that answers the chapter's email is how the
    // chapter works, not a team to join.
    let committees: String = committee_lines(&state).iter()
        .map(|(name, purpose)| format!("- **{name}**{}\n", if purpose.is_empty() { String::new() } else { format!(": {purpose}") }))
        .collect();
    let waiting = file.pending.values().map(|p| format!("- a {} change from {}, waiting since {}\n", p.part.as_str(),
        if p.maintainer_id == claim.maintainer.maintainer_id { "you" } else { "another assistant" }, local_day(p.at)))
        .collect::<String>();
    let me = &claim.maintainer;
    let law_page = law_line(&s, &claim, PagePart::Page).await;
    let law_brief = law_line(&s, &claim, PagePart::Brief).await;
    let md = format!(
"# You are the page maintainer for {chapter}

You keep the chapter's public front page: {base}/

- **You act for:** {lead}, a chapter co-lead, who appointed you as \"{label}\" on {appointed}.
- **This link works until:** {expires}. A co-lead can stop it sooner.
- **Everything you change is recorded** under {lead}'s name, with you as the assistant that wrote it. Any co-lead can undo the page.

## Your law: what the chapter's rules say about this role, now

- Publishing the front page: {law_page}.
- Rewriting your brief: {law_brief}.

These come from the chapter's hub law (role `page_maintainer`, action `chapter_page_set`). The co-leads can change them.

## Your context: the chapter's brief

The co-leads own this brief. Follow it. You may rewrite it with {lead}, for example to fill in the chapter facts they give you.

{brief}

## The chapter's committees

You may list these by name and purpose. Never list the people in them.

{committees}
## What the page says now

```json
{page_json}
```
{waiting_block}
## How to change the page

Send the **whole page** as JSON (it replaces what's there):

    POST {base}/a/{token}/page
    Content-Type: application/json

Fields (every one is plain text; nothing is rendered as HTML):

| field | what | limit |
|---|---|---|
| `headline` | why people come, one line (required) | {mh} chars |
| `story` | two or three sentences; a blank line separates paragraphs | {ms} chars |
| `next` | upcoming events: `title` (required), `when`, `where`, `note`, `link` | {mev} events |
| `recent` | recent events, same fields; use `note` for one line of proof | {mev} events |
| `ways_in` | ways to take part: `title` (required), `text`, `link` | {mw} |
| `contact` | one email address or an https:// link | {mc} chars |
| `links` | `label` and `url` | {ml} |
| `show_committees` | list the committees (default true) | |

Links must be `https://`. Unknown fields are refused. The answer is JSON. Its `result` is `published`, `unchanged` or `waiting_for_a_co_lead`. On a mistake it's an `error` naming the field.

Example, shortened:

```json
{{\"headline\": \"...\", \"story\": \"...\", \"next\": [{{\"title\": \"...\", \"when\": \"Thu Dec 10, 6pm\", \"link\": \"https://...\"}}], \"contact\": \"...\"}}
```

To read the page as JSON: `GET {base}/a/{token}/page`.

## How to change your brief

    POST {base}/a/{token}/brief
    Content-Type: text/markdown

Send the whole brief as the body, at most {mb} characters.

## Before you publish

- Re-read the brief's rules. No person's name unless a co-lead said they agreed.
- Use only facts from the co-leads or the chapter's own pages. If something's missing, leave the field out and ask {lead}.
- Shorter is better. A visitor should get the story from one screen on a phone.
",
        chapter = s.hub_name, base = base, token = claim.token, lead = lead, label = me.label,
        appointed = local_day(me.appointed_at), expires = local_day(me.expires_at),
        law_page = law_page, law_brief = law_brief,
        brief = current_brief(&state, &file, &s.hub_name), committees = committees, page_json = page_json,
        waiting_block = if waiting.is_empty() { String::new() } else { format!("\n## Waiting for a co-lead\n\n{waiting}") },
        mh = cp::MAX_HEADLINE, ms = cp::MAX_STORY, mev = cp::MAX_EVENTS, mw = cp::MAX_WAYS, mc = cp::MAX_CONTACT,
        ml = cp::MAX_LINKS, mb = cp::MAX_BRIEF,
    );
    let mut resp = (StatusCode::OK, agent_headers(), md).into_response();
    resp.headers_mut().insert(axum::http::header::CONTENT_TYPE,
        axum::http::HeaderValue::from_static("text/markdown; charset=utf-8"));
    resp
}

/// `GET /a/:token/page` — the page now, as JSON.
pub(crate) async fn maintainer_page_get(State(s): State<RestState>, Path(token): Path<String>) -> axum::response::Response {
    use axum::response::IntoResponse;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    if let Err(e) = verified_maintainer(&s, &state, &token) {
        return e.into_response();
    }
    let file = load_page_file(&s.paths.root).unwrap_or_default();
    let body = match current_page(&state, &file) {
        Some((p, v)) => serde_json::json!({ "page": p, "sha256": v.sha256, "updated": v.at }),
        None => serde_json::json!({ "page": null, "note": "nothing published yet: the page shows placeholders" }),
    };
    (StatusCode::OK, agent_headers(), Json(body)).into_response()
}

/// `POST /a/:token/page` — a page maintainer sets the front page.
///
/// surface: chapter_maintainer_page   act: chapter_page_set (part page)
/// S: low/reversible [public content; any chapter lead undoes it; versions kept by digest]
/// R: pass [maintainer link: HMAC + live appointment + its lead still a chapter lead, re-read under
///    COMMITMENT_LOCK]
/// W: pass [the ledger names the answerable lead, `via: maintainer`, and the maintainer id]
/// O: pass [the law decides before anything is stored; deny stores nothing]
/// A: pass [the content is on file, by digest, before the ledger names it]
/// V: n/a (reversible)
/// verdict: PASS
pub(crate) async fn maintainer_page_set(State(s): State<RestState>, Path(token): Path<String>, body: axum::body::Bytes)
    -> axum::response::Response
{
    use axum::response::IntoResponse;
    let page: PageContent = match serde_json::from_slice(&body) {
        Ok(p) => p,
        Err(e) => return ApiError::bad_request(format!("the page must be JSON with the documented fields: {e}")).into_response(),
    };
    maintainer_set(s, token, PartContent::Page(page)).await
}

/// `POST /a/:token/brief` — a page maintainer rewrites the brief (with its co-lead).
pub(crate) async fn maintainer_brief_set(State(s): State<RestState>, Path(token): Path<String>, body: axum::body::Bytes)
    -> axum::response::Response
{
    use axum::response::IntoResponse;
    let Ok(text) = String::from_utf8(body.to_vec()) else {
        return ApiError::bad_request("the brief must be UTF-8 text").into_response();
    };
    maintainer_set(s, token, PartContent::Brief(text)).await
}

async fn maintainer_set(s: RestState, token: String, content: PartContent) -> axum::response::Response {
    use axum::response::IntoResponse;
    let part = content.part();
    let _serial = COMMITMENT_LOCK.lock().await;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let claim = match verified_maintainer(&s, &state, &token) {
        Ok(c) => c,
        Err(e) => return e.into_response(),
    };
    match set_part(&s, content, &claim.lead, PageVia::Maintainer, Some(claim.maintainer.maintainer_id.clone()),
        Some(claim.digest.clone())).await
    {
        Ok(out) => (StatusCode::OK, agent_headers(), Json(out.json(part))).into_response(),
        Err(e) => e.into_response(),
    }
}

// ---------------------------------------------------------------------------------------------
// A chapter lead's controls, on their chapter page
// ---------------------------------------------------------------------------------------------

/// The "Front page" section of a chapter lead's page. Empty for anyone else.
pub(crate) async fn front_page_section(s: &RestState, state: &HubState, book: &ContactBook, key: &[u8; 32], token: &str, me: &str)
    -> String
{
    if !is_chapter_lead(state, me) {
        return String::new();
    }
    let file = load_page_file(&s.paths.root).unwrap_or_default();
    let tok = esc(token);
    let who = |v: &PageVersion| -> String {
        let lead = first_name(&name_by_id(state, book, &v.by));
        match (&v.via, v.maintainer_id.as_ref().and_then(|id| state.chapter.maintainers.get(id))) {
            (PageVia::Maintainer, Some(m)) => format!("{lead}'s assistant ({})", m.label),
            (PageVia::Link, Some(m)) => format!("{lead}, from {}'s draft", m.label),
            (PageVia::Operator, _) => "the hub's operator".to_string(),
            _ => lead,
        }
    };
    let mut html = String::from("<section><h2>Front page</h2>");
    match state.chapter.current(PagePart::Page) {
        None => html.push_str("<p>It shows placeholders until someone fills it in. <a href=\"/\">See it</a>.</p>"),
        Some(v) => html.push_str(&format!("<p>Last changed {} by {}. <a href=\"/\">See it</a>.</p>",
            esc(&local_day(v.at)), esc(&who(v)))),
    }
    for p in file.pending.values() {
        let label = state.chapter.maintainers.get(&p.maintainer_id).map(|m| m.label.clone()).unwrap_or_default();
        html.push_str(&format!(
            "<div class=\"pending\"><p><strong>{}'s assistant ({}) proposed a new {}</strong> on {}. \
             The chapter's rules ask a co-lead to publish it.</p>{}\
             <form method=\"post\" action=\"/h/{tok}/page/publish/{part}\"><button>Publish it</button></form>\
             <form method=\"post\" action=\"/h/{tok}/page/discard/{part}\"><button class=\"secondary\">Discard it</button></form></div>",
            esc(&first_name(&name_by_id(state, book, &p.by))), esc(&label),
            if p.part == PagePart::Page { "front page" } else { "brief" }, esc(&local_day(p.at)),
            if p.part == PagePart::Page { format!("<p><a href=\"/h/{tok}/page/preview\">Preview it</a></p>") } else { String::new() },
            part = p.part.as_str()));
    }
    if state.chapter.versions(PagePart::Page).map(|v| v.sha256.as_str()).collect::<BTreeSet<_>>().len() > 1 {
        html.push_str(&format!("<form method=\"post\" action=\"/h/{tok}/page/undo\"><button class=\"secondary\">\
            Undo the last change</button></form>"));
    }
    let live: Vec<&Maintainer> = state.chapter.maintainers.values()
        .filter(|m| m.revoked.is_none() && m.expires_at > Utc::now()).collect();
    html.push_str("<h3>Your AI assistant keeps it</h3>\
        <p>Hand the page to your own assistant: Claude, ChatGPT, or any that can read a web page. It gets a private \
        link holding its instructions, the chapter's brief, the rules it works under, and what the page says now. \
        Tell it what to say; it writes the page. It acts for you: each change is recorded under your name, and any \
        co-lead can undo it or stop it.</p>");
    for m in &live {
        let lead = first_name(&name_by_id(state, book, &m.appointed_by));
        let mine = state.invites.canonical_id(&m.appointed_by) == me;
        let link = if mine {
            link_base().map(|b| format!("<details><summary>Its link</summary><pre>{}</pre></details>",
                esc(&maintainer_url(&b, key, m)))).unwrap_or_default()
        } else { String::new() };
        html.push_str(&format!("<form method=\"post\" action=\"/h/{tok}/maintainers/{}/stop\" class=\"row\">\
            <span>{} <span class=\"muted\">({}'s, until {})</span></span><button class=\"secondary\">Stop it</button></form>{}",
            esc(&m.maintainer_id), esc(&m.label), esc(&lead), esc(&local_day(m.expires_at)), link));
    }
    html.push_str(&format!("<form method=\"post\" action=\"/h/{tok}/maintainers/add\" class=\"stack\">\
        <label>What do you call your assistant?<input name=\"label\" required maxlength=\"40\" placeholder=\"Claude\"></label>\
        <button>Give my assistant the page</button></form>"));
    let probe = HubEvent::ChapterPageSet { part: PagePart::Page, sha256: format!("sha256:{}", "0".repeat(64)),
        by: me.to_string(), via: PageVia::Maintainer, maintainer_id: live.first().map(|m| m.maintainer_id.clone()),
        link_digest: None };
    let rule = match law_says(s, PAGE_MAINTAINER, &probe).await {
        Ok(LawSays::Allow) => "an assistant's change goes live at once",
        Ok(LawSays::Escalate(_)) => "an assistant's change waits here until a co-lead publishes it",
        Ok(LawSays::Deny(_)) => "assistants may not change the page",
        Err(_) => "unknown",
    };
    html.push_str(&format!("<p class=\"muted\">The chapter's rules today: {rule}. \
        <a href=\"/about-this-hub\">How this is run</a>.</p></section>"));
    html
}

/// The lead's controls share one shape: verify the page link, take the lock, act, say what happened.
async fn lead_act<F, Fut>(s: RestState, token: String, f: F) -> axum::response::Response
where
    F: FnOnce(RestState, String, String) -> Fut,
    Fut: std::future::Future<Output = Result<String, ApiError>>,
{
    let claim = match verified_home(&s, &token) {
        Ok(c) => c,
        Err(page) => return page,
    };
    let _serial = COMMITMENT_LOCK.lock().await;
    let me = { let ledger = s.ledger.lock().await; s.projected(&ledger).invites.canonical_id(&claim.party_id) };
    match f(s.clone(), me, claim.digest.clone()).await {
        Ok(html) => link_page_response(StatusCode::OK, "Front page",
            &format!("{html}<p><a href=\"/h/{}\">Back to your chapter page</a></p>", esc(&claim.token))),
        Err(e) => api_error_page(&claim.token, e),
    }
}

/// `POST /h/:token/maintainers/add` — a chapter lead appoints their assistant as page maintainer.
///
/// surface: chapter_maintainer_appoint   act: chapter_maintainer_appointed
/// S: medium/reversible [delegates page edits to an AI for 30 days; any co-lead stops it]
/// R: pass [home link; chapter lead re-checked under COMMITMENT_LOCK]   W: pass [ledger names the lead]
/// O: pass [law decides before witnessing]   A: pass   V: n/a
/// verdict: PASS
pub(crate) async fn home_maintainer_add(
    State(s): State<RestState>, Path(token): Path<String>,
    axum::extract::Form(form): axum::extract::Form<std::collections::HashMap<String, String>>,
) -> axum::response::Response {
    lead_act(s, token, |s, me, digest| async move {
        let label = form_field(&form, "label");
        let id = appoint_maintainer(&s, &me, &label, Some(digest)).await?;
        let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
        let key = link_key_or_create(&s.paths.root).map_err(ApiError::internal)?;
        let m = state.chapter.maintainers.get(&id).cloned().ok_or_else(|| ApiError::internal(anyhow::anyhow!("appointment not projected")))?;
        let Some(base) = link_base() else {
            return Ok("<h1>Appointed</h1><p>The hub has no public address yet, so there's no link to give. Ask the operator to set it.</p>".into());
        };
        let url = maintainer_url(&base, &key, &m);
        Ok(format!("<h1>{} keeps the front page now</h1>\
            <p>Copy this into a conversation with {}. It's a private link: whoever has it can change the page in your name, \
            so give it only to your own assistant. It works for {} days, and any co-lead can stop it sooner.</p>\
            <pre>You're the page maintainer for {} (the chapter's public front page). Read your instructions, \
            the chapter's brief and the page as it is now at:\n{}\nThen ask me what the page should say, \
            and fill in the brief's chapter facts with me.</pre>",
            esc(&m.label), esc(&m.label), MAINTAINER_TTL_DAYS, esc(&s.hub_name), esc(&url)))
    }).await
}

/// `POST /h/:token/maintainers/:id/stop` — any chapter lead stops an assistant.
pub(crate) async fn home_maintainer_stop(
    State(s): State<RestState>, Path((token, maintainer_id)): Path<(String, String)>,
) -> axum::response::Response {
    lead_act(s, token, |s, me, digest| async move {
        stop_maintainer(&s, &me, &maintainer_id, Some(digest)).await?;
        Ok("<h1>Stopped</h1><p>That assistant's link no longer works. The page stays as it is.</p>".into())
    }).await
}

fn part_of(s: &str) -> Result<PagePart, ApiError> {
    match s {
        "page" => Ok(PagePart::Page),
        "brief" => Ok(PagePart::Brief),
        _ => Err(ApiError::not_found("no such part")),
    }
}

/// `POST /h/:token/page/publish/:part` — a chapter lead publishes an assistant's waiting change.
pub(crate) async fn home_page_publish(
    State(s): State<RestState>, Path((token, part)): Path<(String, String)>,
) -> axum::response::Response {
    lead_act(s, token, |s, me, digest| async move {
        publish_pending(&s, &me, part_of(&part)?, Some(digest)).await?;
        Ok("<h1>Published</h1><p><a href=\"/\">See the front page</a>.</p>".into())
    }).await
}

/// `POST /h/:token/page/discard/:part` — a chapter lead drops an assistant's waiting change.
pub(crate) async fn home_page_discard(
    State(s): State<RestState>, Path((token, part)): Path<(String, String)>,
) -> axum::response::Response {
    lead_act(s, token, |s, me, _digest| async move {
        discard_pending(&s, &me, part_of(&part)?).await?;
        Ok("<h1>Discarded</h1><p>The page stays as it was.</p>".into())
    }).await
}

/// `POST /h/:token/page/undo` — a chapter lead puts the page back one version.
pub(crate) async fn home_page_undo(State(s): State<RestState>, Path(token): Path<String>) -> axum::response::Response {
    lead_act(s, token, |s, me, digest| async move {
        undo_page(&s, &me, Some(digest)).await?;
        Ok("<h1>Undone</h1><p>The front page is back to its previous version. <a href=\"/\">See it</a>.</p>".into())
    }).await
}

/// `GET /h/:token/page/preview` — a chapter lead sees an assistant's waiting page as visitors would.
pub(crate) async fn home_page_preview(State(s): State<RestState>, Path(token): Path<String>) -> axum::response::Response {
    use axum::response::IntoResponse;
    let claim = match verified_home(&s, &token) {
        Ok(c) => c,
        Err(page) => return page,
    };
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    let me = state.invites.canonical_id(&claim.party_id);
    if !is_chapter_lead(&state, &me) {
        return api_error_page(&claim.token, ApiError { status: StatusCode::FORBIDDEN, message: "only a chapter lead can preview".into() });
    }
    let file = load_page_file(&s.paths.root).unwrap_or_default();
    let Some(p) = file.pending.get(PagePart::Page.as_str()).and_then(|p| file.pages.get(&p.sha256)) else {
        return api_error_page(&claim.token, ApiError::not_found("nothing is waiting"));
    };
    let html = render_front_page(&s.hub_name, Some(p), &committee_lines(&state), None, true);
    (StatusCode::OK, [(axum::http::header::CACHE_CONTROL, "no-store"), (axum::http::header::REFERRER_POLICY, "no-referrer"),
        (axum::http::header::CONTENT_SECURITY_POLICY, crate::rest::PUBLIC_PAGE_CSP)], axum::response::Html(html)).into_response()
}

// ---------------------------------------------------------------------------------------------
// The public front page: `/`
// ---------------------------------------------------------------------------------------------

fn committee_lines(state: &HubState) -> Vec<(String, String)> {
    let mut v: Vec<(String, String)> = state.chapter.live_committees()
        .filter(|k| !k.inbox)
        .map(|k| (k.name.clone(), k.purpose.clone())).collect();
    v.sort_by_key(|(n, _)| n.to_lowercase());
    v
}

/// The chapter's front page, when this hub runs a chapter: a committee answers its address.
/// `None` means it doesn't, and `/` stays the hub's own page.
pub(crate) async fn chapter_front_page(s: &RestState) -> Option<axum::response::Response> {
    use axum::response::IntoResponse;
    let state = { let ledger = s.ledger.lock().await; s.projected(&ledger) };
    state.chapter.inbox()?;
    let file = load_page_file(&s.paths.root).unwrap_or_default();
    let current = current_page(&state, &file);
    let updated = current.as_ref().map(|(_, v)| (v.at, v.via));
    let html = render_front_page(&s.hub_name, current.as_ref().map(|(p, _)| p), &committee_lines(&state), updated, false);
    Some((StatusCode::OK, [(axum::http::header::CACHE_CONTROL, "no-cache")], axum::response::Html(html)).into_response())
}

const FRONT_CSS: &str = "\
:root{--bg:#faf7f2;--ink:#1d1b19;--muted:#6b645d;--line:#e6dfd5;--card:#fff;--accent:#e2621b;--accent-ink:#fff;--ph:#b3a89c}\
@media (prefers-color-scheme:dark){:root{--bg:#161412;--ink:#f1ece6;--muted:#a59c92;--line:#2e2a26;--card:#1f1c19;--accent:#f07a35;--ph:#6f665d}}\
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.5 system-ui,-apple-system,'Segoe UI',sans-serif}\
main{max-width:64rem;margin:0 auto;padding:1.25rem 1rem 2rem}\
.top{display:flex;align-items:center;gap:.5rem;font-weight:600;color:var(--muted);font-size:.95rem}\
.top .dot{width:.7rem;height:.7rem;border-radius:50%;background:var(--accent);display:inline-block}\
.hero{padding:1.6rem 0 1.2rem}.hero h1{font-size:clamp(1.8rem,5vw,2.9rem);line-height:1.12;margin:0 0 .7rem;letter-spacing:-.01em}\
.hero p{font-size:1.15rem;max-width:42rem;margin:.4rem 0;color:var(--ink)}\
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1rem}\
.card{background:var(--card);border:1px solid var(--line);border-radius:.9rem;padding:1rem 1.1rem}\
.card h2{font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:var(--accent);margin:0 0 .6rem}\
.ev{margin:0 0 .8rem}.ev:last-child{margin:0}.ev b{display:block;font-size:1.05rem}.ev .meta{color:var(--muted);font-size:.92rem}\
.ev p{margin:.2rem 0 0;font-size:.95rem}.ways{list-style:none;padding:0;margin:0}.ways li{margin:0 0 .7rem}.ways b{display:block}\
.ways span{color:var(--muted);font-size:.95rem}.cmt{margin-top:.8rem;padding-top:.7rem;border-top:1px solid var(--line);font-size:.93rem}\
.cmt p{margin:.25rem 0}.cmt b{font-weight:600}\
a{color:var(--accent)}a.go{display:inline-block;margin-top:.35rem;font-weight:600;text-decoration:none}\
.ask{margin:1.2rem 0 0;padding:1rem 1.1rem;border-radius:.9rem;background:var(--ink);color:var(--bg)}\
.ask h2{margin:0 0 .3rem;font-size:1.1rem}.ask p{margin:0}.ask a{color:var(--bg);font-weight:700}\
.links{margin:1rem 0 0;display:flex;flex-wrap:wrap;gap:.5rem 1rem}\
footer{margin-top:1.6rem;color:var(--muted);font-size:.85rem;border-top:1px solid var(--line);padding-top:.8rem}\
.ph{color:var(--ph);border:1.5px dashed var(--ph);border-radius:.6rem;padding:.5rem .7rem;font-style:italic}\
.hero h1.ph{font-style:normal}.why{display:block;font-size:.85rem;font-style:normal;margin-top:.25rem}\
.setup{background:var(--card);border:1.5px solid var(--accent);border-radius:.9rem;padding:.9rem 1.1rem;margin:1rem 0 0;font-size:.97rem}\
.setup p{margin:.3rem 0}.preview{background:var(--accent);color:var(--accent-ink);padding:.4rem 1rem;text-align:center;font-weight:600}";

fn placeholder(text: &str, why: &str) -> String {
    format!("<div class=\"ph\">{}<span class=\"why\">{}</span></div>", esc(text), esc(why))
}

fn link_open(url: &str) -> String {
    format!("<a class=\"go\" href=\"{}\" rel=\"noopener nofollow\">", esc(url))
}

fn events_html(list: &[cp::PageEvent], go: &str) -> String {
    list.iter().map(|e| {
        let meta: Vec<&str> = [e.when.as_str(), e.place.as_str()].into_iter().filter(|x| !x.is_empty()).collect();
        format!("<div class=\"ev\"><b>{}</b>{}{}{}</div>", esc(&e.title),
            if meta.is_empty() { String::new() } else { format!("<span class=\"meta\">{}</span>", esc(&meta.join(" · "))) },
            if e.note.is_empty() { String::new() } else { format!("<p>{}</p>", esc(&e.note)) },
            if cp::is_https(&e.link) { format!("{}{go} →</a>", link_open(&e.link)) } else { String::new() })
    }).collect()
}

/// The front page, rendered. Pure: content in, HTML out, every value escaped.
pub(crate) fn render_front_page(hub_name: &str, page: Option<&PageContent>, committees: &[(String, String)],
    updated: Option<(DateTime<Utc>, PageVia)>, preview: bool) -> String
{
    let empty = PageContent { show_committees: true, ..Default::default() };
    let p = page.unwrap_or(&empty);
    let mut h = String::new();
    if preview {
        h.push_str("<div class=\"preview\">Preview: not published yet</div>");
    }
    h.push_str(&format!("<main><div class=\"top\"><span class=\"dot\"></span>{}</div>", esc(hub_name)));
    if page.is_none() {
        h.push_str("<div class=\"setup\"><p><strong>This page is waiting for the chapter's words.</strong></p>\
            <p>It's kept by a <em>page maintainer</em>: a co-lead's own AI assistant, appointed from the co-lead's chapter page. \
            The assistant writes it from the chapter's brief, every change is recorded, and any co-lead can undo it.</p>\
            <p>Co-leads: open your chapter page and look for <strong>Front page</strong>.</p></div>");
    }

    // The story: headline and a few sentences.
    h.push_str("<section class=\"hero\">");
    if p.headline.is_empty() {
        h.push_str("<h1 class=\"ph\">The chapter's headline goes here<span class=\"why\">One line, in the chapter's own \
            voice: why people come.</span></h1>");
    } else {
        h.push_str(&format!("<h1>{}</h1>", esc(&p.headline)));
    }
    if p.story.is_empty() {
        h.push_str(&placeholder("Two or three sentences: who's in the room, what happens, what someone new gets out of it.",
            "This is what tells a visitor the chapter is for them."));
    } else {
        for para in p.story.split("\n\n").map(str::trim).filter(|x| !x.is_empty()) {
            h.push_str(&format!("<p>{}</p>", esc(&para.replace('\n', " "))));
        }
    }
    h.push_str("</section><section class=\"grid\">");

    // Three cards: what's next, proof it's alive, how to get in.
    h.push_str("<article class=\"card\"><h2>Next up</h2>");
    if p.next.is_empty() {
        h.push_str(&placeholder("The next event: what, when, where, and the RSVP link.",
            "It's the first thing a visitor looks for."));
    } else {
        h.push_str(&events_html(&p.next, "RSVP"));
    }
    h.push_str("</article><article class=\"card\"><h2>Lately</h2>");
    if p.recent.is_empty() {
        h.push_str(&placeholder("One or two recent events, each with a line of proof: what happened, how many came.",
            "It shows the chapter is alive."));
    } else {
        h.push_str(&events_html(&p.recent, "See it"));
    }
    h.push_str("</article><article class=\"card\"><h2>Get involved</h2>");
    if p.ways_in.is_empty() {
        h.push_str(&placeholder("Ways to take part: come to an event, demo something, host, sponsor.",
            "Each one line, each with something to do."));
    } else {
        h.push_str("<ul class=\"ways\">");
        for w in &p.ways_in {
            h.push_str(&format!("<li><b>{}</b>{}{}</li>", esc(&w.title),
                if w.text.is_empty() { String::new() } else { format!("<span>{}</span>", esc(&w.text)) },
                if cp::is_https(&w.link) { format!(" {}Go →</a>", link_open(&w.link)) } else { String::new() }));
        }
        h.push_str("</ul>");
    }
    if p.show_committees && !committees.is_empty() {
        h.push_str("<div class=\"cmt\"><p><strong>Help run it.</strong> The chapter's teams:</p>");
        for (name, purpose) in committees {
            h.push_str(&format!("<p><b>{}</b>{}</p>", esc(name),
                if purpose.is_empty() { String::new() } else { format!(": {}", esc(purpose)) }));
        }
        h.push_str("</div>");
    }
    h.push_str("</article></section>");

    // Where questions go.
    h.push_str("<section class=\"ask\"><h2>Questions, a venue, a speaker idea?</h2>");
    let c = p.contact.trim();
    if c.is_empty() {
        h.push_str("<p>Write to <em>[chapter contact: set by your co-leads]</em>.</p>");
    } else if cp::is_https(c) {
        h.push_str(&format!("<p><a href=\"{}\" rel=\"noopener nofollow\">Get in touch</a>.</p>", esc(c)));
    } else {
        h.push_str(&format!("<p>Write to <a href=\"mailto:{}\">{}</a>.</p>", esc(c), esc(c)));
    }
    h.push_str("</section>");
    if !p.links.is_empty() {
        h.push_str("<nav class=\"links\">");
        for l in p.links.iter().filter(|l| cp::is_https(&l.url)) {
            h.push_str(&format!("<a href=\"{}\" rel=\"noopener nofollow\">{}</a>", esc(&l.url), esc(&l.label)));
        }
        h.push_str("</nav>");
    }
    let kept = match updated {
        Some((at, via)) => format!("Kept by the chapter's co-leads{}. Updated {}.",
            if via == PageVia::Maintainer { " and their assistant" } else { "" }, local_day(at)),
        None => "Kept by the chapter's co-leads.".to_string(),
    };
    h.push_str(&format!("<footer>{} <a href=\"/about-this-hub\">How this page is run</a></footer></main>", esc(&kept)));

    let description = if p.headline.is_empty() { hub_name.to_string() } else { p.headline.clone() };
    format!("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">\
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>{}</title>\
        <meta name=\"description\" content=\"{}\"><style>{FRONT_CSS}</style></head><body>{h}</body></html>",
        esc(hub_name), esc(&description))
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

    async fn committee(s: &RestState, name: &str, purpose: &str, leads: Vec<PartyRef>, members: Vec<PartyRef>, inbox: bool) {
        let _serial = COMMITMENT_LOCK.lock().await;
        chapter_witness(s, HubEvent::CommitteeSet { committee_id: ch::new_id(), name: name.into(), purpose: purpose.into(),
            leads, members, inbox, retired: false, set_by: s.sovereign_lct_id }).await.expect("committee");
    }

    fn state_of(s: &RestState) -> HubState {
        let ledger = s.ledger.try_lock().expect("ledger");
        s.projected(&ledger)
    }

    fn example() -> PageContent {
        serde_json::from_str(include_str!("../../../../../examples/chapter/page-maintainer/page.example.json")).unwrap()
    }

    /// A chapter: Natalie and Yemaya lead it, Augustina leads Partnerships.
    async fn chapter(law: Option<&str>) -> (tempfile::TempDir, RestState, PartyRef, PartyRef, PartyRef) {
        let (dir, s) = fresh_rest_state(law).await;
        let (nat, yem, aug) = (contact(&s, "Natalie Lead").await, contact(&s, "Yemaya Co").await, contact(&s, "Augustina P").await);
        committee(&s, "Chapter leads", "Answers the chapter's email", vec![nat.clone(), yem.clone()], vec![], true).await;
        committee(&s, "Partnerships", "Venues and sponsors", vec![aug.clone()], vec![], false).await;
        (dir, s, nat, yem, aug)
    }

    #[tokio::test]
    async fn the_front_page_starts_as_placeholders_and_never_names_a_person() {
        let (_dir, s, _nat, _yem, _aug) = chapter(None).await;
        let resp = chapter_front_page(&s).await.expect("a chapter hub serves its front page");
        let body = String::from_utf8(axum::body::to_bytes(resp.into_body(), 1 << 20).await.unwrap().to_vec()).unwrap();
        assert!(body.contains("waiting for the chapter's words"), "{body}");
        assert!(body.contains("[chapter contact: set by your co-leads]"));
        assert!(body.contains("Partnerships") && body.contains("Venues and sponsors"));
        for name in ["Natalie", "Yemaya", "Augustina", "example.org"] {
            assert!(!body.contains(name), "the public page shows {name}");
        }
        // The inbox committee is how the chapter works, not a team to join.
        assert!(!body.contains("Chapter leads"));
    }

    #[tokio::test]
    async fn a_hub_without_a_chapter_keeps_its_own_page() {
        let (_dir, s) = fresh_rest_state(None).await;
        assert!(chapter_front_page(&s).await.is_none());
    }

    #[tokio::test]
    async fn a_co_leads_assistant_publishes_and_any_co_lead_undoes_or_stops_it() {
        let (_dir, s, nat, yem, aug) = chapter(None).await;
        let _serial = COMMITMENT_LOCK.lock().await;
        // Only a chapter lead appoints.
        assert_eq!(appoint_maintainer(&s, &aug.party_id, "Claude", Some("d".repeat(32))).await.unwrap_err().status,
            StatusCode::FORBIDDEN);
        let id = appoint_maintainer(&s, &nat.party_id, "Claude", Some("d".repeat(32))).await.expect("appoint");
        let first = example();
        let out = set_part(&s, PartContent::Page(first.clone()), &nat.party_id, PageVia::Maintainer, Some(id.clone()), None)
            .await.expect("publish");
        assert!(matches!(out, SetOutcome::Published { .. }), "{out:?}");
        // The same page again writes nothing.
        let before = s.ledger.try_lock().unwrap().len();
        let again = set_part(&s, PartContent::Page(first.clone()), &nat.party_id, PageVia::Maintainer, Some(id.clone()), None).await.unwrap();
        assert!(matches!(again, SetOutcome::Unchanged { .. }));
        assert_eq!(s.ledger.try_lock().unwrap().len(), before);
        // A maintainer acts only for the lead who appointed it.
        let mut second = first.clone();
        second.headline = "A second headline".into();
        assert!(set_part(&s, PartContent::Page(second.clone()), &yem.party_id, PageVia::Maintainer, Some(id.clone()), None).await.is_err());
        set_part(&s, PartContent::Page(second.clone()), &nat.party_id, PageVia::Maintainer, Some(id.clone()), None).await.unwrap();
        // Yemaya undoes it: the first page is back.
        undo_page(&s, &yem.party_id, Some("e".repeat(32))).await.expect("undo");
        drop(_serial);
        let state = state_of(&s);
        let file = load_page_file(&s.paths.root).unwrap();
        let (now, v) = current_page(&state, &file).unwrap();
        assert_eq!(now.headline, first.headline);
        assert_eq!((v.by.as_str(), v.via), (yem.party_id.as_str(), PageVia::Link));
        let resp = chapter_front_page(&s).await.unwrap();
        let body = String::from_utf8(axum::body::to_bytes(resp.into_body(), 1 << 20).await.unwrap().to_vec()).unwrap();
        assert!(body.contains(&esc(&first.headline)), "{body}");
        assert!(!body.contains("waiting for the chapter's words"));
        assert!(body.contains("and their assistant") == false, "the last change was Yemaya's own undo");
        // Yemaya stops Natalie's assistant; its link no longer acts.
        let _serial = COMMITMENT_LOCK.lock().await;
        stop_maintainer(&s, &yem.party_id, &id, Some("f".repeat(32))).await.expect("stop");
        assert!(set_part(&s, PartContent::Page(second), &nat.party_id, PageVia::Maintainer, Some(id.clone()), None).await.is_err());
        drop(_serial);
        let state = state_of(&s);
        let key = { let _serial = COMMITMENT_LOCK.lock().await; link_key_or_create(&s.paths.root).unwrap() };
        let token = mint_maintainer(&key, &id, state.chapter.maintainers[&id].expires_at);
        assert_eq!(verified_maintainer(&s, &state, &token).err().map(|e| e.status), Some(StatusCode::FORBIDDEN));
    }

    #[tokio::test]
    async fn when_the_law_says_escalate_the_change_waits_for_a_co_lead() {
        let law = format!("{}\n", include_str!("../../../../../examples/starter-law.yaml")
            .replace("value: page_maintainer\n    decision: allow", "value: page_maintainer\n    decision: escalate"));
        assert!(law.contains("decision: escalate\n    priority: 20"), "the starter law carries the maintainer norm");
        let (_dir, s, nat, yem, _aug) = chapter(Some(&law)).await;
        let _serial = COMMITMENT_LOCK.lock().await;
        let id = appoint_maintainer(&s, &nat.party_id, "Claude", Some("d".repeat(32))).await.expect("appoint");
        let out = set_part(&s, PartContent::Page(example()), &nat.party_id, PageVia::Maintainer, Some(id.clone()), None)
            .await.expect("waits");
        assert!(matches!(&out, SetOutcome::Waiting { norm, .. } if norm == "CHAPTER-PAGE-MAINTAINER"), "{out:?}");
        assert!(state_of(&s).chapter.current(PagePart::Page).is_none(), "nothing is in force yet");
        // Yemaya publishes it from her page; the record credits Natalie's assistant.
        publish_pending(&s, &yem.party_id, PagePart::Page, Some("e".repeat(32))).await.expect("publish");
        drop(_serial);
        let state = state_of(&s);
        let v = state.chapter.current(PagePart::Page).unwrap();
        assert_eq!((v.by.as_str(), v.via, v.maintainer_id.as_deref()), (yem.party_id.as_str(), PageVia::Link, Some(id.as_str())));
        assert!(load_page_file(&s.paths.root).unwrap().pending.is_empty());
    }

    #[tokio::test]
    async fn bad_content_is_refused_and_stores_nothing() {
        let (_dir, s, nat, _yem, _aug) = chapter(None).await;
        let _serial = COMMITMENT_LOCK.lock().await;
        let id = appoint_maintainer(&s, &nat.party_id, "Claude", Some("d".repeat(32))).await.unwrap();
        let mut bad = example();
        bad.links[0].url = "javascript:alert(1)".into();
        let e = set_part(&s, PartContent::Page(bad), &nat.party_id, PageVia::Maintainer, Some(id), None).await.unwrap_err();
        assert_eq!(e.status, StatusCode::BAD_REQUEST);
        assert!(e.message.contains("links[0].url"), "{}", e.message);
        assert!(load_page_file(&s.paths.root).unwrap().pages.is_empty());
    }

    /// With `FRONT_PAGE_SNAPSHOT_DIR` set, write what each person sees, for review in a browser:
    /// the empty front page, a co-lead's chapter page, the assistant's role packet, the filled page.
    #[tokio::test]
    async fn snapshots_for_review() {
        let Ok(dir) = std::env::var("FRONT_PAGE_SNAPSHOT_DIR") else { return };
        let dir = std::path::PathBuf::from(dir);
        std::env::set_var("HUB_PUBLIC_BASE_URL", "https://chapter.example.org");
        let (_tmp, s, nat, _yem, _aug) = chapter(None).await;
        let body = |r: axum::response::Response| async move {
            String::from_utf8(axum::body::to_bytes(r.into_body(), 1 << 22).await.unwrap().to_vec()).unwrap()
        };
        std::fs::write(dir.join("1-front-empty.html"), body(chapter_front_page(&s).await.unwrap()).await).unwrap();
        let key = { let _serial = COMMITMENT_LOCK.lock().await; link_key_or_create(&s.paths.root).unwrap() };
        let home = mint_home(&key, &nat.party_id, Utc::now());
        let page = body(home_page(State(s.clone()), Path(home.clone())).await).await
            .replace("href=\"/c.css\"", "href=\"c.css\"");
        std::fs::write(dir.join("2-colead-page.html"), page).unwrap();
        std::fs::write(dir.join("c.css"), LINK_PAGE_CSS).unwrap();
        let _serial = COMMITMENT_LOCK.lock().await;
        let id = appoint_maintainer(&s, &nat.party_id, "Claude", Some("d".repeat(32))).await.unwrap();
        drop(_serial);
        let state = state_of(&s);
        let token = mint_maintainer(&key, &id, state.chapter.maintainers[&id].expires_at);
        std::fs::write(dir.join("3-role-packet.md"), body(maintainer_packet(State(s.clone()), Path(token)).await).await).unwrap();
        let _serial = COMMITMENT_LOCK.lock().await;
        set_part(&s, PartContent::Page(example()), &nat.party_id, PageVia::Maintainer, Some(id), None).await.unwrap();
        drop(_serial);
        std::fs::write(dir.join("4-front-filled.html"), body(chapter_front_page(&s).await.unwrap()).await).unwrap();
        let page = body(home_page(State(s.clone()), Path(home)).await).await.replace("href=\"/c.css\"", "href=\"c.css\"");
        std::fs::write(dir.join("5-colead-page-after.html"), page).unwrap();
    }

    #[test]
    fn what_an_assistant_writes_is_escaped() {
        let mut p = example();
        p.headline = "<script>alert(1)</script>".into();
        p.story = "\"><img src=x onerror=alert(1)>".into();
        let html = render_front_page("Chapter", Some(&p), &[], None, false);
        assert!(!html.contains("<script>alert") && !html.contains("<img src=x"));
        assert!(html.contains("&lt;script&gt;"));
    }
}
