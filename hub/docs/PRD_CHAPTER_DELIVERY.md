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
| Stylesheets | **no `.css` file exists under `hub/`** (four exist elsewhere in the repo — visualizer, whitepaper, archived site — none reachable by the daemon); **five** inline `<style>` blocks (`admin.rs:40,108,1101`, `rest.rs:6094,6147`) |
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
(`WEB4_MEMBOX_URL`, default `http://127.0.0.1:8771`). The hub refuses a non-loopback value **unless
`WEB4_MEMBOX_ALLOW_REMOTE=1`** (`rest.rs:4699`; the 503 body advertises the escape hatch) — so the
guard is a default, not a wall, and one platform secret disables it. The managed-host deploy path (PR #728) provisions a single
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

**Tracked as `dp-web4/hestia#563`** (opened 2026-08-21) so these stop living only in prose;
the table below stays as the rationale the issue cites.

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

| # | surface | plane | exposure | today | needed |
|---|---|---|---|---|---|
| B1 | Chapter profile — name, charter summary, what we do, how to join | D | public | landing page only | public page + `GET /v1/hubs/:id/chapter` |
| B2a | **Groups list** — existence, purpose, lifecycle, open/closed | D | public | **absent** | `GET …/groups` |
| B2b | **Group detail** — membership, roles, channel references | C | member | **absent** | `GET …/groups/:id` |
| B3 | **Roles directory** — what each office does, who fills it, term, rotation | C | public | operator-only (`/admin/roles`) | `GET …/roles` + public page |
| B4a | Member roster — who currently holds membership | C | member | `list_members` over the channel — no page | `GET …/members` |
| B4b | Member profile records — display name, bio, **verified references** (§3.2 H4) | D | member | flattened by `hub_fields()` | `GET …/members/:id/profile`, verification preserved |
| B5 | My chapter — my roles, my groups, my obligations, what needs me | C | member | **absent** | member home; the highest-value member page |
| B6a | Events list — upcoming and past | D | public | **absent** | lifecycle-aware group kind |
| B6b | Event participation — RSVP, attendance | C | member | **absent** | — |
| B7a | Join application — submit a request | C | public | `/client` | — |
| B7b | Join status — the state of *my* request, vouching, decision, appeal | C | **applicant** — see §4.4 | **absent** | surface the request's state to the asker |
| B8a | Group formation — propose, quorum, charter derived from parent | A | member | **absent** (R4 unbuilt) | the act the pilot's phase 2 measures |
| B8b | Group formation — operator administration of the same act | A | operator | **absent** | — |
| B9a | **Public decision record** — what was decided, under which law, when (redacted) | D | public | `/admin/ledger` operator-only | public transparency is the deck's promise |
| B9b | Member decision record — the unredacted projection | D | member | operator-only | — |
| B10 | Discussion | **see §4.4** | member | `/discuss` exists | scope per group, not chapter-wide |
| B11 | Discovery + introductions | C | member | **engine live, no UI** (§1.1) | screens for search, candidate review, request, consent, resulting channel |
| B12a | Export — my own record (R8.2) | D | member | **absent** | "leave without penalty" is a stated success criterion |
| B12b | Export — the chapter's record (R8.2) | D | operator | **absent** | — |

**Why the rows split.** `interface-planes.md` §2.1 makes it a **MUST** that every surface be assignable
to exactly one fact plane, §2.2 a **MUST** that it declare exactly one exposure class, and §8.2 a
conformance clause that no surface serves two planes without decomposition. An earlier draft of this
table had 5 of 12 rows conformant — three rows naming two planes, six naming two exposures. Since
§4.2's rows are *work items* consumed by §4.3 and §5.2, a row naming two planes specifies a handler
serving two planes, which is exactly what the standard this document cites forbids.

The split is not bookkeeping. **B4 was the standard's own worked counterexample**: "member directory"
bundles *proven occupancy* (C — authorization-bearing, answers whether a party may act now) with
*attestation records* (D — answers what is recorded and must never grant authority), and §3's
`MUST NOT` sits exactly between them. Likewise B9a/B9b: a redacted public projection and a full member
projection are two authorizations, which is the safer thing to build regardless of the standard.

**B9a deserves a note.** "Governance opacity" is a confirmed AIC pain point and "transparent" is the
deck's headline promise, yet the ledger is currently visible only to the operator. A public,
appropriately-redacted decision record is arguably the single most persuasive surface the hub could
ship for this audience — it is the thing no incumbent tool offers.

### 4.3 Accountability self-audit — the new public surfaces

```
surface: public groups + member directory (B2a/B3/B4a/B4b)   act: disclose member and group data to unauthenticated callers
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

### 4.4 Two surfaces that do not fit the vocabulary — canon-track, not assigned here

`interface-planes.md` §2.1/§2.2 require exactly one plane and one exposure per surface. Two rows
cannot satisfy that honestly, and assigning them by nearest neighbour would hide a real gap in the
spec rather than surface it. Both belong to the standard, not to this PRD.

**B10 — discussion has no fact plane.** Plane C is *"proven identity; who fills which role, bounded in
time; the occupancy boundary; revocation."* A discussion surface is none of those. If posts are
recorded it leans D, but discussion *content* is not attestation about members either — D is the
witness chain and its projections, and chapter chatter must never enter it (that would make ordinary
conversation governance evidence). The honest reading is that **member-generated content is outside
A–E**, and the standard should either add a plane for it or say explicitly that content is out of
scope and carries no plane.

**B7b — the applicant is neither public nor member.** The exposure classes are public / member /
operator / internal. Someone who has applied and is awaiting a decision is **identified but not
admitted**: showing their own request's state to the world fails least-disclosure, and gating it
behind `member` makes it unreachable exactly while it matters. This is the same party
`PRD_AGENT_CONTEXT_ACCESS.md` §2.2 calls the **receptionist** case — a caller with standing but no
citizenship — so the gap is already named on the authorization side and simply has no exposure class
on the presentation side.

Recommend both be raised against `interface-planes.md` rather than resolved here. Until they are,
B10's plane and B7b's exposure are marked *see §4.4* rather than guessed, so a reader cannot mistake a
placeholder for a decision.

---

## 5. Theming — the architectural work

### 5.1 Why this is not a CSS task

There is nowhere to put a theme. HTML is `format!`-interpolated in Rust across 122 call sites in one
file; styles are **five** inline `<style>` literals; no `.css` file exists under `hub/`; no template engine is a
dependency. **A per-community theme cannot be expressed in the current architecture at all** — which
is why this is listed as architecture, not polish.

### 5.2 Proposed model

1. **Extract**: move markup out of `format!` into templates, and **all five** inline `<style>` blocks
   (`admin.rs:40,108,1101`, `rest.rs:6094,6147` — count them from the list, not from memory) into one
   stylesheet built from custom properties. This is the prerequisite for everything else and
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

**Amended 2026-08-21** after review. Two changes: discovery is no longer held behind channel work,
and Phase A no longer blocks the first slice.

- **Phase A — establish the pattern, don't migrate everything.** Stand up the template + token +
  data-endpoint pattern (§5.2 steps 1–2) and prove it **on the new surfaces of Phase B**. Migrating
  every legacy `format!` call in the operator plane is *not* a prerequisite — it happens
  incrementally unless a concrete coupling forces it. (The earlier draft made full mechanical
  extraction a gate; that delays every persuasive surface behind a refactor with no user-visible
  result.)
- **Phase B — open the public plane, in persuasion order.** **B9a** public redacted decision record
  first — it is the thing no incumbent tool offers and it answers the confirmed "governance opacity"
  pain point directly. Then **B1** chapter profile. Neither needs R4.
- **Phase C — the member plane, and put the existing engine in front of people.** **B5** (my chapter),
  **B4a/B4b** (roster + profile records, with H4 fixed), **B11** (discovery + introduction screens),
  **B7a/B7b** (join + status). **B11 sits here, not at the end**: the engine is already built and
  running (§1.1), so this is UI over shipped capability, and it is a pitch-critical promise.
- **Phase D — groups as first-class.** B2a/B2b, B6a/B6b, B8a/B8b — gated on R4, and on R5 built as a
  **restricted parent–child subset of the canonical R1 edge** rather than a temporary subgroup
  mechanism that later needs replacing. This is the pilot's phase 2.
- **Phase E — themes.** §5.2 steps 3–6, after the surfaces exist. Theming an incomplete UI means
  doing it twice.
- **Phase F — channels (independent lane).** hestia H1–H6, then group-owned channel references.
  **This no longer gates anything above it.** An earlier draft sequenced channels before discovery,
  which would have held a shipped, pitch-critical capability behind unrelated third-party reference
  work. The internal agent-managed plane (§3.3) stays later still.

**Export (B12a/B12b) is not a phase** — it is a standing requirement each phase satisfies for the data
it adds. Retrofitting export is how systems become impossible to leave.

**Deployment runs alongside, not after.** Semantic discovery needs the membot sidecar, and the
managed-host path does not provision it (§1.1). Tracked as **#749** with a two-posture acceptance —
provision and health-check it, or advertise discovery as degraded. Phase C must not ship a discovery
UI onto a hosted chapter whose engine is dark.

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
