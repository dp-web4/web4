# PRD: The chapter's front page, kept by a page maintainer

**Status:** built on branch `cbp-pm/chapter-front-page`, for the AI Collective Portland chapter hub.
**Parent:** [PRD_CHAPTER_PRODUCT.md](PRD_CHAPTER_PRODUCT.md). This adds the public face of the chapter product.
**Templates:** [`examples/chapter/page-maintainer/`](../examples/chapter/page-maintainer/).

## 1. The problem

The global AI Collective site gives each chapter a template page. Portland's says "Join our vibrant AI community in Portland", has an empty "Upcoming Events" list, and below that the same boilerplate every chapter gets. The co-leads didn't like it, for two reasons:
- they can't edit it;
- it doesn't say Portland the way they want to say it.

Until this change, the hub's own `/` was worse. It was the protocol landing page, with a society UUID, a charter hash, "6 norms, 1 procedure", and an "Install Hestia" join path. That breaks the chapter product's rule against protocol words.

Nobody maintains websites by hand any more. The chapter's officers have AI assistants. So the page should be **kept by an assistant**, and keeping it should be a **governed role**, built in from the start rather than bolted on.

## 2. Who it's for

- **First: the chapter co-leads.** Their chapter page shows what the front page can do for members, and how to hand it to their assistant. The public page never shows instructions: before anything is published, every slot falls back to a finished-looking starter (a bridge print, "Next event coming soon", the committees).
- **Then: anyone who heard the chapter's name.** In a few seconds, on a phone, they want to know: is this for me, what's next, how do I get in. The page answers in one screen: a hero poster (headline over a print of a Portland bridge) with the next event right under it, then Lately, Get involved, the committees, and where questions go. The design ("Pole Flyer") and its stylesheet and prints are in `hub-daemon/src/rest/commitments/chapter/front_assets/`.

## 3. The role: page maintainer

**Page maintainer is a role.** Its particulars live in two places:

| | What it holds | Where | Who changes it |
|---|---|---|---|
| **Law** | What the role may do: publish directly, wait for a co-lead, or nothing | Hub law norms on `r6.role == page_maintainer` (`CHAPTER-PAGE-MAINTAINER` in `starter-law.yaml`) | The society, by law amendment |
| **Context** | Voice, audience, the page's story, rules (no names), chapter facts | The **brief**, a front-page part like the page itself; default `brief.md` | The co-leads, usually through their assistant |

A **chapter lead** (a lead of the committee that answers the chapter's email) fills the role with their own assistant from their chapter page. The steps:
1. The lead types what they call the assistant ("Claude") and presses *Give my assistant the page*.
2. The hub records `chapter_maintainer_appointed` and shows a private **maintainer link** (`/a/:token`, 30 days), with a ready-to-paste message.
3. The lead pastes it into a conversation with their assistant.

**The assistant acts for that lead, and only while they are a chapter lead.** Every change it makes is recorded under the lead's name, with the maintainer's id. Any chapter lead can stop any assistant, and can undo the page. Co-leads check each other.

## 4. The assistant's interface

| Route | What |
|---|---|
| `GET /a/:token` | **The role packet**, in Markdown, in one read: who it acts for and until when, what the law says about the role *right now*, the brief, the committees (names and purposes), the page as it stands, and how to change it. |
| `GET /a/:token/page` | The page now, as JSON. |
| `POST /a/:token/page` | A whole new page, as JSON. The answer's `result` is `published`, `unchanged` or `waiting_for_a_co_lead`; on a mistake, an `error` naming the field. |
| `POST /a/:token/brief` | A whole new brief, as text (at most 8000 characters). |

The page is **structured content, never markup**: `headline`, `story`, `next[]`, `recent[]`, `ways_in[]`, `contact`, `links[]`, `show_committees` and `members` (the chapter's own member count, like "2,500+"; optional, and left out of the stored JSON when empty so older pages keep their digests).
- Every value is plain text, rendered escaped.
- Links must be `https://`.
- `contact` is one email address or an https link.
- Unknown fields are refused.
- The page runs no script (the public listener's CSP has no `script-src`).

So nothing an assistant is told to write can run on the page or reach a visitor's key store.

## 5. Every change is a governed act

One act covers both parts: `chapter_page_set { part: page | brief, sha256, by, via, maintainer_id, proposal_id, undo }`.

**The words stay off the ledger.** The ledger records only the content's digest. The text lives in the operator's `chapter-page.json` (0600) under that digest, every version kept.

**The ledger is the record; the file only holds words.** What's in force and what's waiting are read from the ledger, never from the file. The file is checked against the ledger's digest on every read:
- content that's missing or doesn't match shows as **damaged**: visitors get a short "being updated" page, co-leads get a warning with what to do, and the assistant is told to send it again;
- it is never shown quietly as the placeholders, or as the starting brief;
- sending the same content again repairs it, with nothing new recorded.

Content goes to the file before the ledger names its digest. A failed ledger write leaves an unused file entry and loses no decision.

**Before anything is stored, the hub asks the chapter's law,** with an R6 request:
- `role`: `page_maintainer` through a maintainer link, or `chapter_lead` from a lead's page;
- `action`: `chapter_page_set`;
- `payload`: the event.

The law's answer:

| Law says | What happens |
|---|---|
| allow | Content to the page file, then the act is witnessed; the page changes. |
| escalate | The change waits as a proposal, recorded as `chapter_page_proposed` with its own id. Co-leads see *Look at it first / Publish it / Discard it* on their chapter page, each bound to that id. Publishing is a lead's own `chapter_page_set` naming the proposal, crediting the assistant; discarding is `chapter_page_discarded`. |
| deny | Refused. Nothing is stored. |

**Appointing and stopping are governed acts too:** `chapter_maintainer_appointed` and `chapter_maintainer_revoked`, in role `chapter_lead`. So are discarding a proposal and undoing.

**Proposals** (decided 11-25, after the post-merge review of #999):
- **A lead approves exactly what they looked at.** Publish and Discard name the proposal's id, and the ledger refuses a publish whose digest isn't that proposal's. A proposal that was replaced or discarded can't be published.
- **One waiting proposal per assistant per part.** An assistant's newer proposal replaces its own older one. Different assistants' proposals wait side by side.
- **Stopping is not discarding** (dp, 11-25). They're separate acts, and both are always available. Stopping an assistant ends its link. What it left waiting stays on the co-leads' pages, marked "that assistant has since been stopped", for a lead to publish or discard. The same holds when a link expires.
- **A lead answers for what they publish.** Publishing a stopped assistant's proposal is the lead's own act, recorded under their name, crediting the assistant.

**Undo** takes the page back one version each time: to the version before, and from the first one back to the placeholders. The undo names exactly where it goes, and the ledger refuses one that names anywhere else. The button names the version it undoes, so a stale button (the page changed since the lead looked) does nothing.

**The default lets an assistant publish.** The page is public, reversible, and every change names a lead. A chapter that wants a person in the loop changes one word in its law (`allow` to `escalate`). No law loaded behaves as allow, as with the hub's single-signer gate.

**The public record** (`/record`) shows that the front page changed or was undone, and whether a co-lead's assistant, a co-lead or the operator changed it. It shows that a change is waiting for a co-lead, and that one was discarded. It also shows that an assistant was appointed and until when. It never shows whose assistant: the lead is a member fact.

**What a maintainer link is.** It's delegated authority: whoever holds it acts for the lead who appointed it, within the role's law. It is not a verified identity for the AI behind it. Its responses are `no-store` and `no-referrer`, and the hub logs no request paths. The tunnel in front of the hub sees full URLs, as it does for every chapter link.

## 6. What the page never shows

- **People.** Committees appear by name and purpose only. The committee that answers the chapter's email is omitted, because it's how the chapter works, not a team to join.
- **Internal work:** jobs, owners, inbound email.
- **Protocol words.** "How this page is run" in the footer links to `/about-this-hub`, which is the old hub landing page, for the curious.

The brief adds the rules a renderer can't enforce:
- no person's name unless a co-lead says they agreed;
- facts only from the chapter;
- plain words;
- shorter is better.

## 7. Not yet

- **An MCP endpoint** for assistants that speak MCP but can't send an HTTP POST from chat. The role packet is plain Markdown over GET, so any assistant that can read a page can at least draft.
- **A notice to the other co-leads** when an assistant publishes. Today they see it on their chapter page ("Last changed … by Natalie's assistant").
- **Images.**
- **Events pulled automatically** from the chapter's event platform. The maintainer writes them from the chapter's event page.
- **A content-rule check** (e.g. names) beyond what the brief asks.

## 8. Pass

A co-lead appoints their assistant, the assistant fills the page and the brief with them, and the other co-lead sees and can undo it. Then the co-leads point people at the page instead of the global one. Their verdict is recorded word for word, including a no.
