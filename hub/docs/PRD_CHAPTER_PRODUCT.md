# PRD: Chapter product, the first real-community slice (F0b)

**Status:** built on branch `cbp-pm/chapter-product`. Tested in-process; no chapter has used it yet.
**Parent:** [PRD_MEMBER_WEBSITE_FIRST_USER_2026-11-11.md](PRD_MEMBER_WEBSITE_FIRST_USER_2026-11-11.md) §5b and §6 (F0b), issue web4#993 (F1b).
**Builds on:** [PRD_COMMITMENTS.md](PRD_COMMITMENTS.md) K1–K5c2. Every job here is a commitment.

## 1. The problem, in the chapter's words

From the AI Collective Portland core meeting on 2026-10-27:
- inbound emails get missed;
- each event is owned by one person, with no backup;
- nothing happens when nobody acts.

The chapter's own fixes were a shared inbox with a bot, two DRIs per event, a prospectus template and a RACI, coordinated in Slack, in "baby steps".

## 2. The rule: nobody does extra work

Officers already live in email and Slack, and they shouldn't have to learn a new tool to get the benefit. So:

- **Everything is reachable from an email they already got.** Every nudge and notice carries one-click answers (K4 links) and a link to the person's own chapter page. There's no login, nothing to install and no password. A volunteer never needs a key: contacts can own jobs, back them up, and lead committees.
- **You hear from it only when something is slipping.** The rules:
  - an event's checklist is announced once per person, not once per item;
  - an item stays quiet until its date passes with nobody on it;
  - only then does it go to the backup, and after that to the committee leads.
- **No protocol words on any page a volunteer sees.** That means no "ledger", "law", "LCT" or "society". The record is shown as "What happened".
- **The chapter keeps its tools.** The chapter address keeps working; a copy of its mail feeds intake. Replies go out from each person's own mail program, through a Reply button.

## 3. What a person sees

| Who | What happens | Where |
|---|---|---|
| Whoever is on inbox duty | An email reaches the chapter. They get one email: who wrote, the subject, and a link. The page shows the message, a **Reply from your email** button, and **Pass to Partnerships** (or any other committee). After replying, they press **It's done**. | `/c/:token` |
| Their backup | Hears only if a day goes by in silence. | nudge |
| A committee lead | Plans an event with one short form: name, date, owner, backup. The standard checklist (venue, sponsor, event page, speakers, day-of) is ticked by default. | `/h/:token` |
| Event owner and backup | Get one email each for the whole event. After that, a reminder comes only for an item whose date passes in silence. | notice |
| Anyone in the chapter | Their chapter page answers four questions: what needs me, what's mine, which events are coming, and who does what (committees, leads, people, and who owns each open job). | `/h/:token` |
| The committee, after the event | The owner or a lead presses **close it**. Everyone on the committee gets the recap: what was done, by whom, what was handed on, and what went quiet. | `/h/:token/e/:id`, recap notice |

## 4. How it's built

- **Committees** (`committee_set`): a name, a purpose, leads and members, as opaque party ids. One committee is marked `inbox`: it answers the chapter's address. Its first two people (leads first) are the owner and backup of each new request.
- **A chapter commitment** carries `leads_role = committee:<id>`, so the last step of the ladder is that committee's leads. Those leads may be contacts.
- **Events** (`chapter_event_planned`, `chapter_event_closed`): the checklist items are commitments with `group = event:<id>`.
  - No item has a `due_at`. On a commitment, a due date means "missed" when it passes, and a late venue still needs a venue.
  - Instead, each item's owner window ends on its target date, then the backup gets 48 hours, then the leads.
- **Requests** (`request_received`, `request_passed`): an email becomes a commitment with `group = request:<id>` for the inbox committee.
  - Passing it withdraws that commitment and opens one for the receiving committee's first two people, in one act. The record reads as what happened.
  - The sender, the address and the text live in `chapter-intake.json` (0600, erasable) beside the contact book. Only the subject reaches the ledger, as the job's title (C3).
- **Chapter page links** (`/h/:token`): an HMAC over the party and an expiry, under the commitment link key with its own label. They last 45 days and are re-sent in every nudge and notice. Possession is the credential, read as `via: link`, the same as K4.
- **Notices** (`/admin/api/chapter/notices`): a welcome per person, "you're on this event", and recaps.
  - They're sent by `hub-nudge` alongside nudges and recorded off the ledger in `chapter-notices.json`.
  - A notice moves no job.
- **Intake** (`hub-intake`): reads new mail from a mailbox over IMAP, through `curl` with a netrc file, so the hub never holds the mailbox login.
  - It skips auto-replies and the hub's own sender.
  - The hub dedups by Message-ID.

## 5. Privacy and authority

- **What's disclosed:** a chapter page shows any chapter person what §5b says every member may read: committees, leads, members, and who owns each open job. The text of inbound mail appears only on that job's own page, to the people named on it.
- **Who may act:**
  - planning an event or adding a to-do needs a lead of that committee;
  - closing an event needs its owner, its backup, or a lead;
  - passing a request needs someone named on it.
  - All of these are re-checked under `COMMITMENT_LOCK`.
- **What a link is worth:** like K4, it's possession only, and the ledger records `via: link` plus the token's digest. A forwarded chapter page acts as its person. The page says so, and the operator can void every link by rotating the link key.

## 6. Not yet

- Slack as a nudge channel (an incoming webhook in the carrier).
- An operator GUI for committees. Today it's a seed script against `/admin/api/chapter/committees`.
- Time zones with daylight saving. `HUB_CHAPTER_UTC_OFFSET` is a fixed offset.
- Editing an event's date after planning.

## 7. Pass

Per the parent PRD §5b, the chapter's own officers run one real event cycle on it, with no fleet member doing the work, and their verdict is recorded word for word, including a no. A demo shown to them is not a pass.
