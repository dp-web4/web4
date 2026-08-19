# PRD — Chapter delivery: what hub + hestia need to run the pitch

**Status**: proposed — dp-directed 2026-08-19, after the AIC Portland deck was shared with the chapter.
**Owner**: dp. **Maintainer**: the HUB seat.
**Scope**: everything hub and hestia would need to actually deliver what the deck proposes — not the
governance mechanisms (those are `PRD_HUB_V2_FEDERATED.md` R1–R10), but the **planes, presentation
and channel surfaces** that make those mechanisms usable by a volunteer chapter.
**Relates to**: `PRD_HUB_V2_FEDERATED.md` (R4 role-entities, R5 sub-hubs, R8 the pilot, R9 discovery,
R10 introductions), `PRD_ROLE_SCOPE_BRIDGE.md` §9 (outward direction),
`PRD_AGENT_CONTEXT_ACCESS.md` (outward authorization),
`web4-standard/core-spec/interface-planes.md` (the plane vocabulary this document uses).

---

## 0. Directive (dp, 2026-08-19, verbatim)

> there are a number of things missing from hub and hestia that would be necessary to actually build
> a chapter. hestia should have a way of integrating all the social channels - external plane
> presented to outside world as references and internal plane (later implementation) for agents to
> manage the channels. hub needs a way to have its external/internal plane present the roles,
> communities, projects, etc. in other words - go through and list everything that would be
> needed/desirable for hub+hestia to actually implement what we propose in the pitch deck. we have
> most of the plumbing but only partial ui/presentation. the visuals on ui should have our default
> but be style-agnostic, each community will want their own (and, fractally,
> sub-communities/roles also).

## 1. The finding in one line

**dp's read is right, and the measurement sharpens it**: the plumbing is real, the *presentation* is
not merely partial — it is **structurally unable to be themed**, and the **public plane is nearly
empty**. Those are two different problems and only one of them is UI work.

Measured 2026-08-19 on `web4 @ 4319296`:

| | measured |
|---|---|
| HTML production | `format!` string interpolation in Rust — **122 `format!` calls in `hub-daemon/src/admin.rs`** alone |
| Templates | **none** — no `askama` / `tera` / `handlebars` / `maud` / `minijinja` in any `Cargo.toml` |
| Stylesheets | **no `.css` file exists in the repo**; at least **four** separate inline `<style>` blocks (`admin.rs:40`, `admin.rs:108`, `admin.rs:1101`, `rest.rs:6094`, `rest.rs:6147`) |
| Public plane HTML | `/`, `/client`, `/discuss`, `/.well-known/web4-hub.json` — and nothing else |
| Public group/role data | **no directory route** — `/v1/hubs/:id/members/join` and `/members/:uuid/pubkey` exist, but nothing lists roles, groups, communities or projects |
| Member tool surface | **rich, and live** — 11 tools over the sealed channel (below), reachable only as protocol calls |
| Operator plane | 10 HTML pages + 12 JSON endpoints under `/admin` — the only rich surface that exists |

So: **the operator can see everything, a member can see almost nothing, and the outside world can see
a landing page.** The deck promises the opposite emphasis.

### 1.1 Correction — the member plumbing is further along than assumed

A first pass at this document (and the pitch deck as first shared) recorded semantic discovery and
introductions as *not started*. **Both are built and running**, as tools over the sealed member↔hub
channel (`POST /v1/hubs/:id/channel`). Verified in source, not in docs:

| tool | source | note |
|---|---|---|
| `find_members` | `rest.rs:4124` | **semantic** — embedding + 3-signal search via the membot sidecar; tier-scoped `top_k`; hits enriched from the hub registry so member PII lives once, in the hub, not the index |
| `request_intro` / `list_intros` / `respond_intro` | `rest.rs:4169`+ | the consent half; mutual approval yields each side's pubkey for a direct member↔member channel |
| `list_members`, `find_skill`, `notifications`, `referenced_act`, `request_citizenship`, `query_hub`, `constellation_challenge`, `present_constellation` | `rest.rs` | the rest of the channel tool set |

This **sharpens dp's thesis rather than softening it**: R9 and R10 in the federated PRD are largely
*implemented* and entirely *unpresented*. The gap this document addresses is not "build discovery" —
it is "a member has no way to reach discovery that is not a protocol call."

**One consequence for deployment.** `find_members` requires the membot sidecar
(`WEB4_MEMBOX_URL`, default `http://127.0.0.1:8771`, and the hub **refuses a non-loopback value** to
prevent shipping member queries off-box). The managed-host deploy path (PR #728) provisions a single
container with no sidecar — so **semantic discovery would be dark on a hosted chapter today**. Either
the deploy path grows a second process, or the chapter's discovery degrades to `find_skill` and the
runbook must say so.

---

## 2. Principles this document adds

### P1. Every rendered page has a data endpoint behind it

Style-agnosticism is not a CSS feature. A community that wants its own look must be able to build its
own front end entirely — so **no page may be the only way to obtain its data**. Today the operator
pages compose HTML directly from state, which makes the HTML the API. Each surface in §4 is therefore
specified as *data first, reference UI second*.

This is also what makes the reference UI safely replaceable: if the hub's own pages are just a client
of the same endpoints, a chapter's custom front end is not a fork.

### P2. Theming is tokens, not stylesheets

A community supplies a **presentation profile** — a bounded token set (palette, type, spacing, logo,
optional wordmark) — not arbitrary CSS. Arbitrary CSS from a sub-community is a defacement and
exfiltration surface, and it silently destroys accessibility guarantees. Tokens are inspectable,
diffable, governable, and cannot express an attack.

### P3. Governance chrome is theme-limited

**A community MUST NOT be able to restyle the surfaces that carry a governance decision.** If a
sub-community can theme the consent dialog, it can make *decline* invisible, or make *deny* look like
the primary action. The consent prompt (R10), the admission decision, the law-amendment confirm, and
any refusal or veto control render from the **default** token set with contrast floors enforced,
regardless of the active theme. This is the interface-plane non-substitution invariant applied to
pixels: presentation must not become policy.

### P4. Themes inherit fractally, exactly like law

A sub-community inherits its parent's presentation profile and may override a subset. The resolution
order is the entity chain — global default → chapter → community → role — with each level able to set
only tokens it is permitted to set (P3 reserves some). Same shape as the R6 edge-scoped inheritance,
and it should reuse that machinery rather than invent a parallel one.

### P5. Reference, not integration, is the default for channels

A social channel appears on the external plane as a **reference** (a verified pointer), never as a
mirror of its content. The hub and hestia do not become a Slack archive. Reading or posting *into* a
channel is the internal plane (§3.3), is later, and is opt-in per channel.

---

## 3. hestia — social channels

### 3.1 What already exists (measured, `hestia @ 7380e077`)

More than expected. `core/src/profile.rs` already provides the whole reference substrate:

- **`ProfileLink { id, platform, url, label, visibility, verification, added_at }`**
- **`Visibility { Public, Member, Trusted, Private }`** with a `permits()` ranking and
  `links_for_tier()` — an external-plane projection **already implemented**
- **`Verification { Claimed, SelfVerified, Attested { by } }`** — the trust ladder for a reference
- **`Platform`**: GitHub, LinkedIn, Twitter, Bluesky, Mastodon, Website, Email, YouTube, Substack,
  Signal, Phone, `Custom(String)`
- A **hub bridge**: `ProfileStore::hub_fields()` → `HubClient::push_profile()` → a signed
  `update_profile` act → the hub's `find_members` index. Its doc comment states the discipline
  plainly: *"Only public + member-visible links travel; trusted/private stay home."*

The visibility boundary is therefore already enforced where it matters. This is a strong base.

### 3.2 Gaps

| # | gap | why it blocks the deck |
|---|---|---|
| H1 | **`Platform` has no community-channel variants** — no Slack, Discord, Matrix, Telegram, Meetup, Luma, Eventbrite, Zoom. The enum is *personal presence*, not *where a community actually meets*. | A chapter's channels are precisely these. `Custom(String)` works but is unverifiable and unindexable. |
| H2 | **Channels are per-member only.** There is no group/community profile — a working group cannot own "our Discord, our Meetup page, our repo". | Communities/working groups/projects/events each need channel references (§4). |
| H3 | **The external plane is not served.** `links_for_tier` is reachable from the CLI, the operator dashboard, and the hub push — but there is **no endpoint** that returns a member's public references to an outside caller. | "External plane presented to outside world as references" is exactly this, and it does not exist yet. |
| H4 | **`hub_fields()` flattens the model**: `platform → url`, last-wins, dropping `verification`, `label`, multiple links per platform, and the public/member distinction (it sends the Member tier wholesale). | The hub cannot render "verified GitHub" vs "claimed", and cannot show a public directory without leaking member-tier links. |
| H5 | **`SelfVerified` has no mechanism.** The variant exists; nothing performs a proof. | An unverified directory of links is a phishing surface, which a volunteer org cannot carry. |
| H6 | **No revocation/expiry on a reference.** A stale link outlives the account. | Members leave platforms; the directory must decay honestly. |

### 3.3 The internal plane (later, per dp)

Explicitly deferred, and specified only enough to keep §3.2 from foreclosing it:

- An **agent-managed channel** is a channel the member (or group) has granted an agent scope over —
  read, summarize, post, or moderate — under the role-scope bridge's clearances, at a proof tier.
- It is **opt-in per channel**, never implied by the reference existing. A reference is a pointer; a
  grant is authority. Conflating them would make publishing a link an authorization act.
- Credentials for a channel live in the member's own vault, never on the hub — same rule as §3.1's
  trusted/private tier.
- The first useful instance is almost certainly **announcement fan-out** (one governed act, posted to
  N channels the group already owns) rather than ingestion. It is one-directional, auditable, and
  needs no content mirroring.

---

## 4. hub — presenting roles, communities, projects, events

### 4.1 The shape

Per `PRD_HUB_V2_FEDERATED.md` R8, these four are **one primitive** (role-entity or child society)
differing by lifecycle. Presentation must follow: one renderer, one data shape, a `kind` and a
lifecycle field — **not four page types**. A fifth shape must cost approximately nothing.

### 4.2 Surface matrix

Plane names per `interface-planes.md`. **Every row is data-first (P1).**

| # | surface | plane / exposure | today | needed |
|---|---|---|---|---|
| B1 | Chapter profile — name, charter summary, what we do, how to join | D / public | landing page only | public page + `GET /v1/hubs/:id/chapter` |
| B2 | **Groups directory** — communities, working groups, projects, events; each with purpose, lifecycle, open/closed, channel references | C+D / public (listed) · member (detail) | **absent** | `GET …/groups`, `…/groups/:id` |
| B3 | **Roles directory** — what each office does, who fills it, term, how it rotates | C / public | operator-only (`/admin/roles`) | `GET …/roles` + public page |
| B4 | Member directory — display name, bio, **verified references** (§3.2 H4) | C+D / member | `list_members`/`find_members` over the channel — no page | `GET …/members` with tier-correct projection + a page |
| B5 | My chapter — my roles, my groups, my obligations, what needs me | C / member | **absent** | member home; the single highest-value member page |
| B6 | Events — upcoming, RSVP, past with record | C+D / public + member | **absent** | needs a lifecycle-aware group kind |
| B7 | Join flow — apply, vouching status, decision, appeal | C / public → member | `/client` (join+discuss) | surface the *state* of a request to the asker |
| B8 | Group formation — propose, quorum, charter derived from parent | A / member + operator | **absent** (R4 unbuilt) | the act the pilot's phase 2 measures |
| B9 | Decision record — what was decided, by whom, under which law, when | D / public (redacted) + member | `/admin/ledger` operator-only | public transparency is the deck's promise |
| B10 | Discussion | C / member | `/discuss` exists | scope per group, not chapter-wide |
| B11 | Discovery + introductions | C / member | **engine live, no UI** (§1.1) | screens for search, candidate review, request, consent, and the resulting channel |
| B12 | Export — my record, our record (R8.2) | D / member + operator | **absent** | "leave without penalty" is a stated success criterion |

**B9 deserves a note.** "Governance opacity" is a confirmed AIC pain point and "transparent" is the
deck's headline promise, yet the ledger is currently visible only to the operator. A public,
appropriately-redacted decision record is arguably the single most persuasive surface the hub could
ship for this audience — it is the thing no incumbent tool offers.

### 4.3 Accountability self-audit — the new public surfaces

```
surface: public groups + member directory (B2/B3/B4)   act: disclose member and group data to unauthenticated callers
S: med/irreversible (disclosure cannot be recalled) [construct: tier projection at the serialization boundary]
R: n/a for read of PUBLIC tier — public exposure IS the classification, not a shortcut past one
W: pass [construct: only Visibility::Public projects to the public plane; member tier requires a proven member]
O: pass [construct: projection applied before serialization, never filtered in the template]
A: pass [construct: disclosure config is law-governed; changes are witnessed amendments]
V: present [construct: a member can withdraw any reference; a group can go unlisted]
verdict: PASS (design) — with the standing caution that a tier mistake here is irreversible in a way
         a governance mistake is not, so the projection must be tested as a differential, not reviewed.
```

```
surface: presentation profile (theme) on any entity   act: change what every viewer of that entity sees
S: med/reversible [construct: token set, versioned with the entity]
R: n/a   W: pass [construct: only the entity's own governance may set its tokens]
O: pass [construct: tokens resolved server-side before render]
A: pass [construct: theme changes are witnessed like any charter field]
V: present [construct: P3 reserves governance chrome from all themes; contrast floors enforced]
verdict: PASS (design) — P3 is the load-bearing clause; without it this surface fails V outright.
```

---

## 5. Theming — the architectural work

### 5.1 Why this is not a CSS task

There is nowhere to put a theme. HTML is `format!`-interpolated in Rust across 122 call sites in one
file; styles are four inline `<style>` literals; no `.css` file exists; no template engine is a
dependency. **A per-community theme cannot be expressed in the current architecture at all** — which
is why this is listed as architecture, not polish.

### 5.2 Proposed model

1. **Extract**: move markup out of `format!` into templates, and the four inline `<style>` blocks
   into one stylesheet built from custom properties. This is the prerequisite for everything else and
   is a mechanical, reviewable change.
2. **Tokenize**: define the token vocabulary once — ground, surface, ink, accent, semantic
   good/warn/critical, type family + scale, radius, spacing unit, logo, wordmark. This is a small,
   closed list on purpose (P2).
3. **Store**: a `presentation` section on the entity — chapter charter, role-entity charter, child
   society charter. Amended by that entity's own governed process, witnessed like any other charter
   field.
4. **Resolve fractally** (P4): default → chapter → community → role, each overriding a subset, using
   the same inheritance machinery as R6 rather than a parallel one.
5. **Reserve** (P3): governance chrome always renders from default tokens with enforced contrast.
6. **Serve**: expose the resolved token set at a data endpoint too, so a custom front end (P1) can
   match the community's own look without reimplementing resolution.

### 5.3 Falsifiable acceptance criteria

1. A chapter sets a palette and type scale; every non-reserved surface changes; **the consent dialog,
   admission decision, and any refusal control do not** (differential: screenshot-diff the reserved
   set across two themes — it must be pixel-identical).
2. A sub-community overrides **one** token; the rest resolve from its parent (differential: change
   the parent's accent and confirm the child follows for everything it did not override).
3. A theme that would drop text/background contrast below the floor is **refused at amendment time**,
   with the failing pair named — not silently clamped at render, which would make the stored value a
   lie.
4. Every page in §4.2 has a data endpoint returning the same content, and the reference UI consumes
   only that endpoint (differential: the page and the endpoint cannot disagree because there is one
   source).
5. A chapter running an entirely custom front end can perform the full member journey — join,
   see my chapter, browse groups, request an introduction — against public endpoints only.

---

## 6. Ordered plan

Sequenced so each step unblocks the next and the pilot's phases are served in order.

- **Phase A — make it presentable.** §5.2 steps 1–2 (extract markup + tokenize). Nothing
  user-visible changes; everything after this depends on it.
- **Phase B — open the public plane.** B1, B3, B9 (chapter profile, roles directory, public decision
  record) with data endpoints. Highest persuasive value per unit of work, and none of it needs R4.
- **Phase C — the member plane.** B5 (my chapter), B4 (directory with §3.2 H4 fixed), B7 (join
  state), B10 scoped discussion.
- **Phase D — groups as first-class.** B2, B6, B8 — gated on R4/R5 landing. This is the pilot's
  phase 2.
- **Phase E — themes.** §5.2 steps 3–6. Deliberately after the surfaces exist: theming an incomplete
  UI means doing it twice.
- **Phase F — channels.** hestia H1–H6, then the hub-side group channel references. The internal
  plane (§3.3) follows only if a chapter asks for it.
- **Phase G — discovery + introductions.** R9/R10, pilot phases 3–4.

**Export (B12) is not a phase** — it is a standing requirement that each phase satisfies for the data
it adds. Retrofitting export is how systems become impossible to leave.

## 7. Non-goals

- The hub does not mirror, archive, or index third-party channel content (P5).
- No arbitrary CSS or script from a community (P2).
- No engagement surfaces — feeds, notifications-as-retention, activity scores. The deck rules these
  out explicitly and the architecture should make them awkward to add.
- No per-community forks of the reference UI: custom front ends consume the same endpoints (P1).

## 8. Open questions for dp

1. **Public-by-default or listed-by-consent?** Does a group appear publicly unless it opts out, or
   only when it opts in? Recommend opt-in for member data (B4) and opt-out for group existence (B2) —
   but this is a chapter-culture decision, and it should be *law*, not a constant.
2. **Where does a group's channel reference live** — on the group's charter (hub) or in a member-like
   profile store the group owns (hestia)? Recommend the hub, since a group has no vault; the cost is
   that the hub then holds references it cannot verify without hestia's help (H5).
3. **Does the reference UI ship as part of the hub binary** (as today) or as a separate artifact? P1
   makes separation possible; shipping it in-binary keeps single-binary deployment, which the
   managed-host path (#728) depends on.
4. **Theme scope for roles** — dp's directive says sub-communities *and roles* theme fractally. A role
   is an office, not a place; does an office need its own look, or is the useful granularity
   community-level? Recommend building the resolution chain to include roles but shipping only
   community-level overrides until someone asks.
