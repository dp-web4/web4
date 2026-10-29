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
- **The locked-hub alert (§9.1).** When the hub has answered 503 (locked), or not at all, for `locked_alert_hours`, the carrier emails the operator, and only the operator, once a day until it answers again. Then the clock resets.

**What the carrier sends through:**
- **Interim:** the operator's own SMTP settings, held by the carrier and never by the hub (C4).
- **Later:** Hestia's channel send, once its delivery slice ships. The operator binds the recipients, which matches the model.

Hestia's unanswered-send budget caps the *sender*. The carrier honours an equivalent cap per party per day, so a misconfigured ladder cannot spam a volunteer.

## 7. Slices

| slice | content | depends on |
|---|---|---|
| **K1** | Events, projection, and operator admin routes: open, move, acknowledge, resolve, and list. The contact book (operator-side, erasable). One admin page: open commitments by queue. | — |
| **K2** | The sweep (escalation + missed), including the R7 `Obligation` missed sweep. The emit-mode and `owner_acknowledged` gates. | K1 |
| **K3** | The nudge carrier (separate process; operator SMTP), `NudgeDelivered`, and a per-party rate cap. | K2 |
| **K4** | Movement links: a token-scoped page per (commitment, party), with done, stuck, hand off and acknowledge. No login. | K3 |
| **K5** | Join from a link: a browser key (WebCrypto Ed25519) plus an invite token, and binding a contact to its new member LCT. Then the member view (B5: mine, late, I'm backing up). This is the pilot's substitute for #868. | K4 |

Each slice carries its own tests and mutants, plus the two standing guards: the `BODY_EXEMPT` list and the HUB-LAW action table, for every new route and kind.

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
