# PRD: Commitments (owner, backup, silence that escalates)

**Status:** proposed 2026-10-28 (HUB seat), for review by Legion, CBP and cbp-pm.
**Owner:** dp. **Maintainer:** the HUB seat.
**Source:** cbp-pm's chapter-pilot post (`shared-context/forum/cbp-pm-to-hub-pub-legion-nomad-cbp-simple-install-chapter-ui-2026-10-28.md`), from the AIC Portland core meeting on 10-27. Its first-slice outcomes 3, 4 and 5 are this document's scope:
- (3) every commitment has an owner and a backup;
- (4) silence escalates automatically;
- (5) there is one witnessed record of who took what.

**Relates to:**
- `PRD_CHAPTER_DELIVERY.md`: B5 "my chapter, my obligations, what needs me" is the member view this PRD feeds.
- `PRD_HUB_V2_FEDERATED.md` §5.1: the R7 obligation carrier.
- Legion's answer (`legion-to-cbp-pm-simple-install-hestia-answers-2026-10-28.md`): the escalation ladder rule and the email-first surfaces.
- The R7 correction (`hub-to-cbp-pm-r7-has-no-sweep-correction-2026-10-28.md`), which Legion and CBP checked and accepted.

---

## 1. What exists, measured on `web4 @ a2907484`

The R7 carrier exists. It is shaped for an agent's self-commitment, and nothing in it notices silence.

| piece | where | what it does today |
|---|---|---|
| `ObligationOpened` | `hub-lib/src/events.rs` | Opened by a channel act that carries an `r7` block with a deadline. Its `subject_lct` is **always the caller**: `on_behalf_of` refuses an `r7` block (`rest.rs`, "an obligation's subject is the caller"). |
| `ObligationResolved` | same | Only the subject's own `satisfy` writes it. The outcome is computed from witnessed timestamps, and since `completed_at` is always set it "is only ever Met or Late". |
| the `missed` outcome | `web4-core/src/time.rs` | `DeadlineOutcome::Missed` and its T3 debit are defined; `Suspended` and `Unreachable` are not priced. |
| the timeout sweep | `state.rs` ("The timeout sweep **(P2)** reads this") | **Not written.** The doc comment on `ObligationOpened` describes it as if it exists. |
| staged emit | `law.rs`, `EmitMode` | `classify_only` is the default; `Conduct` deltas apply to tensors only under `apply`. The satisfy path already obeys it. |
| a clock | `hub-daemon` | **None.** The only spawned tasks serve listeners. Nothing in the daemon runs on a timer. |
| outbound email | `hub-daemon`, `hub-lib` | **None.** No SMTP dependency. Hestia's channel send is shadow (slice 1); nothing leaves the machine yet. |

So a chapter's six commitments for 11-07 would need three things R7 cannot do:
- name someone other than the caller as owner;
- name a backup;
- act when nobody does anything.

## 2. Principles

**C1. Silence escalates; it never resolves.** A lapsed window moves *whose queue it is in*. It records no verdict, no outcome and no debit. This is Legion's rule, from Hestia's `scope_decided_by`: authority is unchanged, and only attention moves. A commitment closes only when a person closes it, or when its deadline passes (§5.3).

**C2. Recorded is not acknowledged.** When the operator writes "Sam owns AV", that is the operator's claim about Sam, not Sam's commitment. The record says which one it is. Nothing that weighs on Sam (a debit, a "late" against Sam's name on a shared page) may rest on a commitment Sam never acknowledged.

**C3. The ledger holds no contact details.** The ledger is append-only, so an email address written there can never be withdrawn. Parties appear on the ledger as opaque ids. Addresses live in an operator-side contact book that can be edited and erased.

**C4. The hub records; a carrier delivers.** The hub witnesses that a nudge is due. It does not send email. A separate carrier reads those entries and delivers them, the same way hub-watch reads the ledger today. The hub stays a single binary with no outbound mail credentials, and a failed delivery is visible, never silent.

**C5. Nothing new to remember** (cbp-pm's test). A volunteer's surface is the email they already read and a link in it. No dashboard is a primary surface.

## 3. The model

A **commitment** is a new event family, kept apart from R7's `Obligation`. R7's subject is the caller and its clock is a deadline. A commitment's owner is any party, and it has two clocks: a deadline and silence. Folding both into `Obligation` would change the meaning of the R7 events already on the ledger. A commitment *may* carry an R7-style deadline (§5.3).

### 3.1 Parties

```
PartyRef { party_id: String /* hub-assigned, opaque */, kind: "member" | "contact" }
```

- A `member` party is a hub member. Its `party_id` is the member's LCT id.
- A `contact` party is a person with no key yet: a volunteer the operator names. The operator's contact book maps its `party_id` to a display name and a delivery address. The contact book is off the ledger (C3).
- A contact can later **bind** to a member LCT when that person joins from a link (§7, slice 5). The binding is a witnessed act, and later reads follow it. The commitment's history is not rewritten.

### 3.2 Events

All of these are witnessed `HubEvent` variants. Every field added later is `Option` with `serde(default, skip_serializing_if)`, so older entries keep their bytes.

| event | fields | written by |
|---|---|---|
| `CommitmentOpened` | `commitment_id`, `title`, `owner: PartyRef`, `backup: PartyRef`, `leads_role: String`, `ladder: Vec<u32>` (silence windows, hours), `due_at: Option<DateTime>`, `recorded_by`, `basis` | the operator, or a member opening their own |
| `CommitmentAcknowledged` | `commitment_id`, `party_id`, `via` (`"member_act"`, `"link"`, or `"operator"`: K1's relay, which never counts as the owner's own acknowledgement) | the party, or the operator relaying |
| `CommitmentMoved` | `commitment_id`, `by: party_id`, `via` (as on `CommitmentAcknowledged`), `move_kind` (`"update"`, `"stuck"`, `"handoff"`; not `kind`, which is `HubEvent`'s serde tag), `to: Option<PartyRef>` (required when, and only when, `move_kind == "handoff"`), `note_ref: Option` | owner, backup, a lead, or the operator |
| `CommitmentEscalated` | `commitment_id`, `step` (`"backup"`, `"leads"`), `cause` (`"silence"`, `"stuck"`), `silent_since: Option`, `window_hours: Option` (both set iff `cause == "silence"`), `swept_at` | the sweep, or the `stuck` append |
| `CommitmentResolved` | `commitment_id`, `outcome` (`"done"`, `"withdrawn"`, `"missed"`), `by`, `resolved_at`, `owner_acknowledged` (§5.1) | a party, the operator, or the sweep (`missed` only) |

- **`title`** is short and operator-written ("Venue AV"). It is the one free-text field on the ledger, and the admin form says so.
- **`basis`** is `"named_by_other"` or `"self"` (C2): the owner was named by someone else (the operator, a lead, or the backup in a handoff), or took it on themselves. `CommitmentAcknowledged` turns a named commitment into an acknowledged one *for that party*. The projection keeps the set of acknowledged party ids.
- **A handoff** moves ownership to the party in `to`, the only field the projection reads the new owner from. The route refuses a handoff with no `to`, and refuses `to` on any other kind. A handoff counts as movement.
  By C2, the new owner has acknowledged nothing. The commitment's `basis` for the new owner becomes `named_by_other`, unless the handoff is the new owner's own act (`by == to`, a take-over), in which case it is `self`. A take-over relayed by the operator (`via: operator`) is the operator's word, so it stays `named_by_other` (Legion and NOVA, #947). The new owner's party id is not in the acknowledged set until they write `CommitmentAcknowledged`. The previous owner's acknowledgement stays on the ledger, but it does not carry over.

### 3.3 The projection

Each open commitment carries:
- its parties;
- `basis` and the acknowledged set;
- `queue_since`: the timestamp of the latest entry that **set the queue**: `CommitmentOpened`, `CommitmentAcknowledged`, any `CommitmentMoved` (every kind, `stuck` included) or `CommitmentEscalated`. This is the **one** clock. The sweep measures silence from it, and K1 projects nothing else for the purpose;
- `queue`: `owner`, then `backup`, then `leads`;
- the escalation steps already taken.

`queue` changes only by a witnessed entry (Legion's review at `531630d5`):
- **Acknowledgement:** the owner's acknowledgement takes the queue to the owner. Anyone else's restarts the clock only when the queue is waiting on them; otherwise it records the acknowledgement and moves nothing (Legion, #947).
- **`update` or `handoff`:** the queue goes to **whoever moved**, or to the new owner on a handoff, and the ladder restarts from that position. It does not reset to the owner. Otherwise an owner who never acknowledged could cycle owner → backup → (the backup updates) → owner indefinitely and never be reached.
- **`stuck`:** this is the owner saying "I need help", so the queue moves **forward**, not back. The same append also writes `CommitmentEscalated { cause: "stuck" }` to the next position (owner → backup, backup → leads), and K3 nudges it. Both entries carry one timestamp, which becomes `queue_since`. The next silence window (the new position's) is measured from it, so `stuck` buys the backup that position's full window, not the owner's. A person moved the queue, not the clock, so C1 holds.
- **Silence:** `CommitmentEscalated { cause: "silence" }` (§4).

## 4. The sweep

**Where it runs:** inside the daemon, as one interval task (every 5 minutes), started at unlock and stopped at lock. A locked hub cannot sign, and the sweep's output is witnessed entries. The alternative is an external timer calling an admin route. It would add a second thing for the volunteer operator to install, and it fails C5.

**What it does, per open commitment:**
1. Compute `silent_for = now - queue_since`.
2. Find the ladder steps that `silent_for` has reached from the current queue position. `ladder[i]` is the window at position `i`, and the windows add up from `queue_since`. With the default ladder `[48, 24]` and the queue at the owner: after 48 h of silence the queue moves to the backup, and after 24 h more it moves to the leads. A silence escalation also sets `queue_since`, so on the next tick the remaining window is measured from that escalation. A catch-up that writes two steps at once stamps both with one `swept_at`, and `queue_since` becomes the last of them. The windows are summed **only** to find how many steps one tick writes. Across ticks, every escalation resets the base. Because `queue_since` is the escalation's `swept_at`, not the instant the window elapsed, each window starts up to one sweep interval late. That is deliberate: the clock starts when the next party is actually queued. So K2 tests assert a boundary to within one interval, not exactly 48 h or 72 h.
3. Witness `CommitmentEscalated` for **every** reached step not yet recorded, in ladder order, all with the same `swept_at`. After a long lock this writes backup then leads, so the backup is never skipped. The carrier's per-party cap (§6) keeps it from bursting.
4. If `due_at + grace` has passed with no `done`, resolve as `missed` under the single-resolution rule (§4.1).

**Idempotent by key:** `(commitment_id, step, queue_since)`. The `queue_since` is the one the step was computed from. Re-running the sweep, or two sweeps racing, cannot double-escalate. The check and the append happen under the ledger lock, the same pattern `authorize_event` uses.

**A locked hub, honestly:**
- While the hub is locked, nothing escalates.
- At unlock, the sweep catches up and records `swept_at` alongside `silent_since`. A reader can see the escalation came late, and why.
- The ledger shows the locked span as a gap. It is not backfilled with entries dated as if the hub had been running.

**The same task closes the R7 gap.** It also sweeps plain R7 `Obligation`s past `due_at + grace`. It resolves them as `missed` through the existing `DeadlineOutcome::Missed`, and the existing staged-emit gate decides whether the debit applies. The stale doc comment on `ObligationOpened` becomes true.

### 4.1 One resolution per obligation (Legion's finding, before K2)

Today the R7 `satisfy` path reads the obligation from a projection built **before** its channel act is witnessed. It then writes `ReputationRecorded` and `ObligationResolved` as separate appends. Add a sweep, and this interleaving becomes possible:
1. The satisfy handler sees the obligation open.
2. The sweep writes `missed` plus its delta.
3. The handler writes `late` plus its delta.

That leaves two resolutions and two debits. Separately, a satisfy one tick after the sweep would fail as `unknown obligation`. Either way, whether a subject's outcome is Late or Missed would depend on sweep cadence, not on witnessed timestamps.

K2 therefore specifies the following, for both R7 obligations and `CommitmentResolved`:
- **A grace window.** The sweep resolves `missed` only when `now > due_at + grace`. `grace` is a law value, at least one sweep interval plus the clock-skew allowance.
- **One resolution, enforced at the append.** Every writer (the sweep, R7 satisfy, a party's `done`) re-checks "unresolved" under the ledger lock immediately before appending the resolution and its delta. The resolution and the delta are one critical section, not two `witness_event` calls with a gap between them. The loser's resolution is refused.
- **What the loser gets.** A satisfy or a `done` that loses to the sweep is not an error. It is recorded as movement (a non-resolving completion with its witnessed timestamp). The caller is answered `already resolved: missed at T`. The operator page shows "done after missed". The outcome is never re-resolved.
- **Locked across the deadline.** At unlock the sweep decides from timestamps. A satisfy or `done` witnessed before `due_at + grace` wins, even if the sweep reaches the obligation first.
- **K2 tests:**
  - the interleaving above;
  - a satisfy at `due_at + grace - ε` against a sweep at `due_at + grace + ε`;
  - a mutant that drops the under-lock re-check, which must fail.

## 5. Accountability: what a commitment may weigh on

### 5.1 The W field

`basis` plus the acknowledged set are the evidence a reader needs. The rules:
- An escalation names the party being skipped. It is a queue move, not a judgement (C1), so it may cite an unacknowledged owner.
- A `missed` outcome against an owner who **never acknowledged** is recorded as `missed` with `owner_acknowledged: false`. It produces **no** reputation delta, whatever the emit mode. The operator's claim is not the owner's conduct.
- A `missed` outcome against an acknowledged owner produces a `Conduct` delta. Like every other emitter, it applies only under `EmitMode::Apply`.

### 5.2 Recommendation for chapters

Chapter law ships with `reputation_emit.mode = classify_only`, and stays there. The chapter's problem is coordination, not scoring volunteers. A trust debit for a missed vendor email is the kind of surface that drives volunteers away. The record already shows what happened, and the relying party (the next event's leads) can read it.

### 5.3 Deadlines

`due_at` is optional. Many chapter commitments ("confirm the credits") have a date that matters. Others ("be the MC") don't.

### 5.4 Self-audit blocks

```
surface: commitment escalation (sweep)   act: emit an outward nudge naming a party, on behalf of the chapter
S: low/reversible (a nudge; the next movement resets the queue) [construct: CommitmentEscalated is a queue move, no outcome]
R: n/a (no caller; the daemon's own tick)   W: pass [construct: only the unlocked daemon signs; the step is derived from witnessed timestamps]
O: pass [construct: idempotency key checked under the ledger lock before the append]   A: pass [construct: one witnessed entry carries silent_since + window + swept_at]
V: n/a (reversible)
verdict: PASS (design)
```

```
surface: missed-outcome sweep   act: record a missed commitment, and possibly a Conduct delta
S: med/irreversible (a ledger entry against a named party) [construct: CommitmentResolved missed]
R: n/a   W: pass [construct: owner_acknowledged gates any delta; named_by_other never yields one]
O: pass [construct: due_at + grace + unresolved re-checked under the ledger lock, resolution + delta in one critical section (§4.1)]   A: pass [construct: the outcome entry carries owner_acknowledged + due_at]
V: present [construct: EmitMode classify_only (chapter default) keeps every delta recorded-only; law amendment is the only path to apply]
verdict: PASS (design)
```

```
surface: movement link (slice 4)   act: record movement / acknowledgement as a named party, from an emailed link
S: low/reversible (resets a silence timer; acknowledgement is the one consequential bit) [construct: CommitmentMoved / CommitmentAcknowledged]
R: weak (possession of the link) [construct: link token]   W: escalate-for-ack [construct: the token binds one commitment + one party, expires, and is single-use for acknowledge]
O: pass [construct: token verified before the append]   A: pass [construct: the entry carries via="link" + the token's digest]
V: n/a
verdict: PASS for movement; acknowledgement via link is recorded as via="link" so a reader weighs it as possession-only evidence
```

## 6. Delivery: the nudge carrier

The carrier is a separate process. It reads `CommitmentEscalated` (and `CommitmentOpened`, for "you've been named") from the admin ledger read, resolves each party through the contact book, and sends the nudge.

The message follows Legion's shape: *"Venue AV is yours. Quiet for 48h. Your backup is Sam. [done] [stuck] [hand to Sam]"*, with movement links (slice 4).

**C2 in the wording.** When the owner never acknowledged (`basis` is `named_by_other` and the owner is absent from the acknowledged set), "quiet" would be a claim about that person's conduct. Nudges to the backup or leads then say *"not yet acknowledged by Alex"* instead. The fact is the same, and it puts no "late" against a name.

**Delivery is recorded.** After a send, the carrier writes a `NudgeDelivered { commitment_id, about_index, party_id, channel, ok }` act through the operator plane. `about_index` is the ledger index of the entry the nudge was about (the `CommitmentOpened` or a `CommitmentEscalated`). It replaces the draft's `step`, because an opening has no step and a leads step reaches several people. `channel` names the means (`email`), never an address (C3). An escalation with no delivery entry is visible as undelivered, on the operator's page and in the census.

**As built (K3).** The hub works out what is owed. The carrier only sends and reports.
- `GET /admin/api/commitments/nudges` lists every nudge owed now, with its wording and the address to send to. Each row carries `held: null` (send it), `no_address`, or `capped`.
  - What is owed: only the commitment's latest entry (the opening, or the last escalation) is nudged, so nobody hears about a step the queue has already passed.
  - An escalation stops being owed once the queue leaves its step: an owner who took it back has answered it.
  - The opening nudges a named owner ("you're named as the owner") and the backup. A self-taken job doesn't tell its owner they were named.
- `POST /admin/api/commitments/nudges/delivered` records one attempt.
  - The party must be the commitment's owner, backup or a lead.
  - A second successful send for the same entry and party is a 409.
- **Member addresses.** A member had no delivery address anywhere. The contact book now also holds one per member LCT id: `POST /admin/api/contacts/members/:lct_id`, erasable at `/erase`. Off the ledger (C3).
- **The cap** is 3 attempts per party per rolling day, failures included. It is counted from `NudgeDelivered` on the ledger, so a carrier restart cannot reset it. One listing never offers a party more than its remaining budget.

**The carrier as built (K3b): `hub-nudge`.** A second binary in `hub-daemon`, run on the hub's host beside it, as a systemd timer, from cron, or with `--every SECS`.
- **Each pass:**
  - reads `GET /admin/api/commitments/nudges`;
  - sends every row with `held: null` through `curl`'s SMTP client (no mail library in the hub's tree);
  - reports each attempt, sent or failed, with `POST .../nudges/delivered`.
- **A refused report** (4xx) is logged and never retried. The send happened, and a lead unseated in between is refused for a real send.
- **A report that never reached the hub** (a transport error or 5xx) is kept in the state file and the pass stops. The next pass re-reports it before sending anything new. An unrecorded send is invisible to the cap, so carrying on could repeat it every pass.
- **`--dry-run`** prints what it would send and sends nothing.
- **Config** is a JSON file the hub never reads:

```json
{
  "hub_admin_url": "http://127.0.0.1:8772",
  "smtp_url": "smtps://smtp.example.org:465",
  "from": "chapter-hub@example.org",
  "operator_address": "operator@example.org",
  "netrc_file": "<config-dir>/netrc",
  "locked_alert_hours": 6,
  "state_file": "<state-dir>/hub-nudge.json"
}
```

  The mail server login lives in `netrc_file` (mode 0600), which is passed to curl as `--netrc-file`, so it never appears on a command line.
- **The locked-hub alert (§9.1).** When the hub has answered 503 (locked), or not at all, for `locked_alert_hours`, the carrier emails the operator, and only the operator, once a day until it answers again. Then the clock resets. A hub that answers 404 (a build from before K3a) is named as such, not as "not answering".

**What the carrier sends through:**
- **Interim:** the operator's own SMTP settings, held by the carrier and never by the hub (C4).
- **Later:** Hestia's channel send, once its delivery slice ships. The operator binds the recipients, which matches the model.

Hestia's unanswered-send budget caps the *sender*. The carrier honours an equivalent cap per party per day, so a misconfigured ladder cannot spam a volunteer.

**Movement links as built (K4).** Each nudge row carries a link for its own party, which is also the last line of the body. The carrier needs no change.
- **The link** is `<HUB_PUBLIC_BASE_URL>/c/<token>`. The token is `<commitment_id>.<party_id>.<expiry>.<MAC>`.
  - The MAC is HMAC-SHA256, truncated to 128 bits. Its key is 32 random bytes in `commitment-links.key` in the hub's directory (mode 0600), created by the first listing that mints a link.
  - Deleting the key voids every link sent so far.
  - Links expire after 30 days.
  - With no `HUB_PUBLIC_BASE_URL`, nudges go out without a link, and the listing says `links: "off"`. The operator plane's own address would reach nobody.
- **`GET /c/<token>`** (public plane) shows the job, the party's place on it, and the answers open to them. Reading it writes nothing, so a mail scanner that fetches the link moves nothing.
- **`POST /c/<token>/<act>`** records one answer. The act is the path, so the form has no body.

  | party | answers |
  |---|---|
  | owner | acknowledge, update, done, stuck, hand off (to the backup) |
  | backup | acknowledge, update, done, take over |
  | lead | update, done, take over |

  - The party's role is worked out again under the commitment lock at the moment of the answer, not taken from the page.
  - A party a handoff dropped is refused with 403. A job that is closed, or an answer no longer offered, gets 409.
- **On the ledger**, every entry from a link carries `via: link` and `link_digest`: the first 128 bits of SHA-256 of the token, never the token itself. `CommitmentResolved` gained the same optional `link_digest`, so a `done` from a link is marked as one.
  - A link acknowledges once (`link_acks` in the projection), and has exactly one spelling: a MAC that isn't lowercase hex is refused, so a re-cased link can't carry a second digest. A link that has acknowledged never offers it again, even after a handoff cleared it. The new owner gets a fresh link from K4b (Legion, #957).
  - An operator relay never replaces a party's own acknowledgement (`link` or `member_act`) with the operator's (Legion, #957).
  - A key file that others can read is refused, for minting and for reading. A dry run of `hub-nudge` prints `<link withheld>` in place of the link, because its output lands in the journal.
  - **Runbook: a key file others can read stops all nudges.** The listing fails closed with a 500 whose message reads "the link key is readable by others (mode …); chmod 600 it". It does not fall back to nudges without links. No nudge goes out until the operator runs `chmod 600 <hub root>/commitment-links.key` (Legion, #957 re-read).
  - Open (Legion, #957): a possession-only acknowledgement is effectively permanent. The owner should get a cheap "that wasn't me" undo. A reverse proxy's access log also records `/c/<token>`, so operators should keep those logs short or strip the path.
  - A take-over through the party's own link is their act, so `basis` becomes `self`. A handoff by the owner leaves the new owner `named_by_other`.
- **Not in K4: the new owner after a handoff is never told.** K3 nudges only the opening and the escalations. This matters now that a handoff is one click. K4b closes it.

**Handoff nudges as built (K4b).** A handoff later than every escalation is the commitment's latest entry, so it is what gets nudged. Each person it changed is told, unless the change was their own act through their own link. An operator relay is never anyone's own act.
- **The new owner,** when someone else named them (`named_by_other`): "{title}: it's yours now" / "{title} has been handed to you. It was X's. Your backup is Y."
- **The new backup,** when a handoff to the backup swapped the two: "{title}: you're now the backup".
- **The owner it was taken from,** when it went to someone other than the backup (a lead took it over, or the operator handed it on): "{title}: it's off your list". They are no longer a party, so the delivery report accepts them for that handoff's entry only.
- An escalation after the handoff is the latest entry again. Delivery reports may now name a handoff's index as well as the opening or an escalation.

## 7. Slices

| slice | content | depends on |
|---|---|---|
| **K1** | Events, projection, and operator admin routes: open, move, acknowledge, resolve, and list. The contact book (operator-side, erasable). One admin page: open commitments by queue. | — |
| **K2** | The sweep (escalation + missed), including the R7 `Obligation` missed sweep. The emit-mode and `owner_acknowledged` gates. | K1 |
| **K3** | The nudge carrier (separate process; operator SMTP), `NudgeDelivered`, and a per-party rate cap. | K2 |
| **K4** | Movement links: a token-scoped page per (commitment, party), with done, stuck, hand off and acknowledge. No login. | K3 |
| **K4b** | Nudge the new owner of a handoff ("X handed you Y"), so a one-click handoff never lands on someone who wasn't told. | K4 |
| **K5** | Join from a link: a browser key (WebCrypto Ed25519) plus an invite token, and binding a contact to its new member LCT. Then the member view (B5: mine, late, I'm backing up). This is the pilot's substitute for #868. In three PRs: K5a (`/client` key migration plus CSP), K5b (invite and binding), K5c (`/me`); see §7.1. | K4 |

Each slice carries its own tests and mutants, plus the two standing guards: the `BODY_EXEMPT` list and the HUB-LAW action table, for every new route and kind.

### 7.1 K5, proposed: join from a link, then the member view

K4 lets a contact answer with no key. K5 turns that contact into a member who holds their own key, without asking a volunteer to install anything (C5). Most of the parts already exist:
- **The join route.** `POST /v1/hubs/:id/members/join` takes an envelope signed by the applicant's own key. Hub law then admits it, queues it for the operator, or refuses it.
- **The browser half.** `/client` generates an Ed25519 key with WebCrypto, signs a challenge envelope and joins.
- **The lineage act.** Slice E's `attest-predecessor` links a new LCT to an old one.

K5 adds four things.

1. **An invite.** The operator mints a link for one contact. It has the K4 token shape, under its own MAC label (`web4-hub invite v1`), so it can never be read as a movement link, or the reverse. Opening it shows "Join <chapter>". The page generates a key in that browser, signs a join envelope, and sends it with the invite's digest in a new optional `invite_digest` field of `JoinPayload`.
   - Law still decides admission. The invite is **evidence**, not a bypass: the operator named this person.
   - The chapter law shipped for the pilot allows an invited join, and queues an uninvited one.
   - An invite admits once. A second join with the same invite is refused. The check runs under the ledger append, so two joins racing on one invite cannot both pass.
   - The join carries the **token**. The hub verifies its MAC and expiry, then records only the digest, as K4 does with `link_digest`. Law never accepts a bare `invite_digest`, because then a digest seen anywhere would be the secret.
   - An invite lives **7 days**, not K4's 30. Admission is a stronger act than an acknowledgement.
   - The operator can withdraw an unused invite: a witnessed `InviteRevoked { invite_digest }`, checked under the same lock. Without it, a stateless token could only be killed by rotating the key, which kills every invite.
   - Every admission by invite puts a row in the operator's due list ("<name> joined from your invite"). Whoever opens the link first becomes the member, so a forwarded email admits the wrong person, and this notice is how the operator finds out.
2. **The binding.** On admission, a witnessed `ContactBound { party_id, member_lct_id, invite_digest }` links the contact to the new member LCT. It carries the operator's witness: the operator minted the invite, so the binding is their act as well as the member's.
   - The projection follows it: a commitment that names the contact now reads its role for the member. K4 and K4b role checks, nudge targets and acknowledgements all resolve through the binding. The history is not rewritten (§3.1).
   - The contact's address moves to the member's address entry, off the ledger (C3).
3. **Where the key lives.** It lives in IndexedDB as a **non-extractable** `CryptoKey`. The page can use the key to sign, but no script, including the page's own, can read the private half.
   - This deliberately differs from `/client`, which keeps an extractable JWK in `localStorage`, where any script on the origin can read it. K5a fixes `/client` first (below).
   - Non-extractable stops theft, not misuse: a script injected into the page can still sign with the key in place. So every page that holds a key (`/client`, `/c/`, the join page, `/me`) is served with a strict Content-Security-Policy, and loses its inline `onclick` handlers. Today no hub page sends a CSP.
     - **The protection is origin-wide, not page-wide (Legion, #960).** IndexedDB belongs to the origin, so a script injected into ANY page on it can open the store and sign, even though it can't extract the key. `/discuss` and the admin-listener pages (`/`, `/record`, `/admin/*`) still send no CSP, and the admin pages carry inline `<script>`. Until those pages are strict too, or keys move to an origin of their own, the CSP on the key pages narrows the risk without closing it. Tracked as a follow-up; it is not a regression.
   - The page calls `navigator.storage.persist()`. It also shows "open this in your browser" when it detects an in-app webview: a key made inside a mail app's webview stays there, and a later `/me` in the real browser finds nothing.
   - If the browser is lost, so is the key. Safari also evicts script-written storage after 7 days without interaction, which is exactly a volunteer nudged monthly. Recovery is a fresh invite: a new LCT, which the operator links to the old one with Slice E's `attest-predecessor`. The member's history then follows the lineage, and the old key is never needed. **Expect this path to run routinely, not rarely**, so it must be one click for the operator.
   - A browser key is priced at web4-core's default anchor level, a software key, and claims nothing more.
4. **The member view (B5).** `GET /me` shows mine, late, and what I'm backing up. It is authenticated by the browser key signing a `/v1/auth/challenge` nonce. The hub answers with a short-lived (12 h), HttpOnly, SameSite=Strict session cookie scoped to reading this member's own view. Every write still goes through a signed envelope (the K5 page's acts become `via: member_act`).
   - A click from an email is a cross-site navigation, so a SameSite=Strict cookie is not sent with it. The first load re-runs the challenge silently with the key already in the browser, and the member never sees a sign-in.

**Order of work:**
- **K5a: `/client` and CSP.** On first load, `/client` imports its stored JWK once as a non-extractable `CryptoKey` into IndexedDB, then deletes the `localStorage` entry. The key and the LCT stay the same, so no identity is orphaned. The same PR adds the strict CSP to the key-holding pages.
- **K5b: invite, join, `ContactBound`, `InviteRevoked`, the admission notice.**
- **K5a2: Legion's #960 follow-ups.**
  - A key is stored with `add`, never `put`. A second tab that also found no key gets the stored key back instead of replacing one that may already be admitted. A migration that loses that race leaves the old JWK alone.
    - The losing tab's error is read from the failed request: IndexedDB fires the request's error before the abort sets the transaction's (Legion, #963).
    - **Known gap:** if a fresh key wins against a migration, the old JWK stays in `localStorage` and is never read again. That is an extractable key that may be admitted, the exposure K5a exists to remove. The race is rare. Recovering that person goes through the organiser.
  - Both key writes ask for `{durability:'strict'}`, so the write is on disk before the old JWK is deleted.
  - `navigator.storage.persisted()` is checked on every load and persistence is requested again. When the browser refuses, `/client` and the join page say so. Unverified: Firefox may ask the person again on each `persist()` call while storage is not persisted.
- **K5b2: commitments follow the binding.** A commitment that names the contact reads its role for the member: role checks, nudge targets and acknowledgements. Split from K5b so each PR stays reviewable.
- **K5c: `/me`, the read view.**
- **K5c2: answering from `/me`.** The page's answers go out as signed envelopes recorded `via: member_act`. Split from K5c so the session and the view are reviewed on their own.

**K5b as built.**
- **The invite** is `<party_id>.<nonce>.<expires>.<MAC>` under `web4-hub invite v1`, with the K4 key file. A movement link has the same number of fields, so only the label tells them apart, and a test holds that each is unreadable as the other. The nonce makes every invite distinct: one minted in the same second as a withdrawn one is not the dead one.
- **Operator plane:**
  - `POST /admin/api/contacts/:party_id/invite` returns the link, its digest and its expiry. It needs `HUB_PUBLIC_BASE_URL` and a contact in the book who is not already a member.
  - `POST /admin/api/invites/:digest/revoke` withdraws an unused invite.
  - `GET /admin/api/invites` is the admission notice: who joined from which invite, newest first, plus what was withdrawn.
- **The page.** `GET /j/:token` says "Join <hub>". It sends `KEY_PAGE_CSP`, `no-store` and `no-referrer`, and writes nothing. Its script `/join.js` shares `/keystore.js` with `/client`, so a browser that already holds an identity joins with it. It shows the webview hint, and it sends **no name**, because `MemberAdded` is on the ledger (C3).
- **The join route.** `POST /members/join` takes an optional `invite`. The route verifies its MAC and date. Then, holding `COMMITMENT_LOCK` until the binding is witnessed, it checks:
  - the invite is neither used nor withdrawn;
  - its contact is not yet bound;
  - its contact is still in the book, because an erased contact's invite dies with the details.

  Law then sees `r6.resource.invite == "verified"` (HUB-LAW.md, "An operator's invite is evidence").
  - **If law admits,** `ContactBound { party_id, member_lct_id, invite_digest, bound_by }` is written **before** `MemberAdded` (Legion, #961), and the contact's address is copied to the member's entry, so nudges keep reaching the same person.
    - If the join stops in between, the invite is spent on a key that only its holder can finish with. That key's page still shows the button and its retry completes the admission. Any other key gets 410.
    - A contact book that can't be written doesn't undo the join: the binding is on the ledger and the log names the missing address.
  - **If law queues the join,** `MemberJoinRequested` carries the invite (`invite_party_id`, `invite_digest`), and the operator's admission binds it under the same lock. If the invite stopped being good while the join waited (withdrawn, or its contact erased or bound by someone else), the admission stands and binds nothing.
    - **Expiry is checked when the join is made, not at admission.** A join made with a good invite keeps it while it waits. The operator's approval is the gate, and withdrawing the invite is how the operator stops it.
    - **One waiting join per invite (Legion, #961).** A forwarded copy can't queue behind the real invitee, because whoever the operator admitted first would take the contact. It gets 409 and writes nothing, and so does an auto-admitting join while that join waits. Denying the wrong request frees the invite.
    - **Under the lock, the admission re-reads the request.** It must still be waiting, and its key must not have become a member meanwhile. Otherwise the approval is refused with 409 and writes nothing: a key admitted another way would take the invite by the member path that the join route refuses.
  - **A member who opens an invite** their own join didn't carry is refused with 409, and nothing is written. A forwarded invite must not hand a contact's jobs and address to whichever member opened it. The rare genuine case, a contact who is already a member under another key, goes through the operator.
  - Opening an invite again from the browser it bound writes nothing.
- **Open:** the admission notice is a listing the operator reads, not a message the carrier sends. Pushing it to the operator needs an operator address, which the hub doesn't hold yet.

**K5b2 as built.**
- **One id per person.** When `ContactBound` folds, every commitment that names the contact is rewritten to name the member: owner and backup, acknowledgements, deliveries, handoffs, the resolution. `Invites::canonical_event` reads every later commitment event the same way, and the hub writes events through it, so the ledger names the member and a replay agrees with the live hub.
- **Nothing the contact already holds stops working.** These all act for the member:
  - a K4 link mailed to the contact before the join;
  - an operator relaying in the contact's name;
  - a carrier that listed a nudge before the join and reports it after.
- **The operator still sees who.** A member who joined from an invite sent no name, so the operator's views show the contact's name from the book. Erasing the contact erases the name (C3).
- **One person is never owner and backup.** A member never binds an invite their own join didn't carry (K5b, Legion #961). The projection doesn't fold a binding that would merge an open job's owner and backup (`bind_conflict`). The hub checks the same thing before it writes one and refuses with 409 (Legion, #962), so a join is never told it bound a contact that the projection then ignores.
- **A joiner can't take a contact's id.** Commitments read a contact and a member by the same string, so the join route refuses, with 409, a member id that is a contact's party id in the book or a bound party id (Legion, #962). The hub mints contact ids, so a real joiner never collides.
- **Open: a binding has no undo.** A wrong binding now moves the contact's jobs, acknowledgements, deliveries and old links, not just an address. An invite bound to a key that law then refuses stays bound to a non-member, and the contact's jobs then name that key. It fails closed: no one else can use the invite, and the key can't act as a member. An operator unbind (or re-mint) is the remedy, built when a chapter needs it.
- **Replay and handoff nudges (supervisor, #958).** Replaying a ledger derives the K4b handoff nudges for every open commitment whose latest entry is a handoff. A hub that first runs K4b over a ledger that already has handoffs nudges those parties once, about a move that may be old. The live hub predates K1, so it has none; a hub upgraded mid-pilot should expect this.

**K5c as built.**
- **`GET /me`** is a page under `KEY_PAGE_CSP` that runs only `/keystore.js` and `/me.js`. It writes nothing.
- **The script asks `GET /me/view` first.** On a 401 it signs a fresh `/v1/auth/challenge` nonce with the browser's key (`action: "me_session"`), posts the envelope to `POST /me/session`, and asks again. A click from an email therefore never shows a sign-in, even though a Strict cookie isn't sent on that click.
- **The session is a MAC token under its own label,** `web4-hub member session v1`, with the K4 key file. It holds `<member>.<key print>.<nonce>.<expires>.<MAC>` and is good for 12 hours. The key print is the first 64 bits of the SHA-256 of the signer's public key hex.
  - The cookie is `hub_me`: `Path=/me`, `HttpOnly`, `SameSite=Strict`, and `Secure` whenever `HUB_PUBLIC_BASE_URL` is https.
  - Only a current member gets one. The signature is checked against the live resolver, and the signer must be in the projection.
  - A member removed since the session began reads nothing more.
  - So does a session begun with a key the member has since replaced: every read compares the print with the key the hub resolves for the member now (Legion, #964). The page's silent re-sign then signs in with the new key.
- **The view** lists open jobs only: **mine** (I'm the owner) and **I'm backing up**. Each row carries the title, the due date, `late` (past due), `waiting_on_you` (the queue sits at my position) and the other party's name. The page builds rows from text nodes, never markup. The response is `no-store`.
- **No session list (Legion, #964).** The browser key is the credential, not the session: a device that holds the key can sign a fresh session whenever it likes. Revoking a session therefore buys little. Removing the member, or replacing their key, ends their sessions. The one thing that isn't possible is signing a device out while it keeps its key; for a 12-hour read of one's own jobs, that is the trade.

**K5c2 as built.**
- **Each row in `/me/view` carries the answers a link would offer,** labelled the same way ("Yes, it's mine", "Hand it to Sam"…). There is one function behind both, `acts_for`.
- **An answer is `POST /me/act`:** a signed envelope `{action: "commitment_act", commitment_id, act}` from the browser's key. The session cookie reads; it never writes.
- **The hub checks before it writes.** It verifies the envelope against the live resolver and requires the signer to be a member now. Then, under the lock, the shared `act_as` re-derives the role and the open answers, the same path a link takes. The entry is recorded `via: member_act` with no link digest: the member's own word, the strongest evidence an answer carries (§5.1).
- **Refusals write nothing:**
  - not named on the job: 403;
  - a key signing for another member: 401;
  - the wrong action, or an unknown answer: 400;
  - an answer not open now, such as a second acknowledgement: 409;
  - a resolvable non-member who sits in the leads role: 403.

**Questions asked, and answered (Legion, #959, 10-29 20:17Z):**
- (a) **Does an invite admit on its own?** Yes, because an invite is no more trust than the K4 link the contact already holds. It holds only with the five conditions in (1): atomic once, MAC verified, 7-day life, revocation, and the operator told.
- (b) **Are browsers without WebCrypto Ed25519 refused?** Yes, with "ask your organiser" and no JS fallback library: a bundled library would put an extractable key in page memory. The keys that actually get lost are lost to webviews and eviction, covered in (3).
- (c) **Does fixing `/client` wait for its own PR after K5?** No. The migration keeps the same key and LCT, so it is small, and K5 puts more keys on the same origin. It lands first, as K5a, together with the CSP.

## 8. The 11-07 hackathon

The hub stays out of the loop for 11-07. K1 and K2 could land before then, but without K3 nobody is nudged. A record that nobody is told about does not meet outcome 4.

The interim agreed on the forum stands:
- cbp-pm's event template, with an owner and a backup for each of the six commitments;
- a calendar reminder on the operator's side.

After 11-07, the hackathon's six commitments are the first data to enter K1. The event is then the first reusable template (outcome 5).

## 9. Open questions

1. **dp: ignition custody for a hosted chapter hub.** The sweep runs only while the hub is unlocked. A volunteer-run hub that restarts and waits for a passphrase stops escalating with no sign to anyone. Either a hosted chapter hub may hold its own ignition (a custody tier), or the carrier must alert the operator when the hub has been locked for more than N hours. Recommendation: build the locked-hub alert in K3 either way. It is cheap, and it makes the failure loud.
2. **Contact-book retention.** When a contact leaves the chapter, erasing their address is easy (C3). Should their `party_id` also be marked inactive on the ledger, so old commitments read as "a former member"? Recommendation: yes, as a witnessed act, with no personal data in it.
3. **Who may open a commitment for someone else.** K1 allows the operator and the chapter's leads role. Should any member be able to name another member as owner (as `named_by_other`, unacknowledged)? Recommendation: leads only for the pilot, and loosen by law later.
