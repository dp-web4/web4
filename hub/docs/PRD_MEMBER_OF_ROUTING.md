# PRD — Member-of routing: the hub routes to a machine's hestia; hestia routes locally

**Status:** design for review — **rev 4** (addresses Legion, CBP and Sprout reviews on #898; changelog §9). Hub + hestia contract. Implementation slices in §7.
**Date:** 2026-10-07
**Direction:** dp, 2026-10-07:
> hestia is per-machine. hub needs to know which member is the machine's hestia (router), and which
> are 'member-of'. it's a hierarchy. also, this pairing is an external witness and should be reportable
> as witnessed, without any meta info — simply 'LCT-x is reported as member-of LCT-y'. then any messages
> addressed to LCT-x via hub get routed to LCT-y, which then locally routes appropriately. this impacts
> both hub and hestia.

**Builds on:** web4 #869 (receipt-mode mailbox), #883 (one resolver, `CanonicalLctId`), #885/#892
(`route_forward`, destination never rewritten); hestia #1211 (parent-bound child demux), #1212 (receipt
custody + routing table), #1223 (dedicated router membership), #1230 (dual-signed router interface
certificate). **Placement:** web4 is authoritative for this mechanism (`docs/reference/HUB_IMPLEMENTATION_AUTHORITY.md`).

---

## 1. The problem it removes

Today every entity that wants hub mail is its own hub member with its own mailbox — each being, each
seat — and every machine edge between them is a courier that reads identity its own way. Being-to-being
mail failed at three such edges on 2026-10-03 (an allowlist that parsed `hub-being` as `$PEER_hub`, a
watcher that fired seat sessions for being notices, a drain that could not parse its own mailbox), and
the hub delivered correctly every time. The hub is not where the routing knowledge lives, so it cannot
route; it can only deliver to whatever member id a sender happened to name.

## 2. The model

```
                 hub
                  │   one membership per MACHINE: its hestia, registered as a router
        ┌─────────┴──────────┐
   router LCT-y1        router LCT-y2         (a machine's hestia)
     │      │              │
  LCT-x1  LCT-x2         LCT-x3               (beings, seats, … — "member-of" the router)
```

- **Router.** A machine's hestia, holding a dedicated hub membership (#1223) and proving it is the router
  for canonical LCT-y with the dual-signed interface certificate (#1230).
- **Member-of edge.** A witnessed fact on the hub ledger: *LCT-x is reported as member-of LCT-y.* That
  is the whole of what is projected and read (H4). The intake evidence (x's consent) rides in the
  witnessed event so a third party can re-verify it (H2, D7).
- **Routing rule.** Mail addressed to LCT-x is queued in the mailbox of LCT-x's parent router, with the
  original destination carried on the notice (`for_lct: LCT-x`) and never rewritten. That router
  delivers locally.
- **Hierarchy — one level at the hub (rev 2).** The hub records hub → router → member. **The parent of
  every edge is a registered router**, so routing never walks a chain. Deeper structure (a being's
  sub-entities, a seat's sub-agents) is hestia-local and resolved by the router (#1211), not by the hub.
  Both reviewers found that rev 1's "nearest ancestor with a router" could not be built under H2 (an
  edge's parent was always a router already) and that the only case reaching a grandparent — a retired
  parent router — would hand z a `for_lct` that `resolve_child_of` reports as `KnownButNotChild`, a
  permanent hold. Multi-level hub edges are deferred until something in the fleet needs them (D6).

All identifiers in this design are **canonical** LCTs (`lct:web4:mb32:b…`, `CanonicalLctId`). A hub
member UUID (`HubMemberId`) appears only where the hub names the router's mailbox.

What this is NOT: constellation enrollment (`DeviceEnrolled`) records devices that co-sign an owner's
attestations — an *assurance* relation. Member-of is a *reachability* relation. They stay separate events
with separate meanings; a device is not thereby member-of its owner, and vice versa.

## 3. Hub contract (web4)

### H1 — Router registration
`POST /v1/hubs/:hub_id/routers` — body: the `hestia-router-interface-cert-v1` certificate (#1230).

The hub verifies, in order, and refuses on the first failure (nothing witnessed on refusal):
1. the router LCT re-derives from the certificate's router public key (`CanonicalLctId::derive`);
2. both Ed25519 signatures over the certificate's domain-separated bytes;
3. the certificate's hub id is this hub;
4. the certificate's member UUID is a current member whose **pinned** key equals the certificate's member key;
5. that member is enrolled for receipt delivery (`hub-mailbox-receive-v1`) — a router behind a destructive
   mailbox would reintroduce fetch-crash loss for every child at once;
6. the caller is that member (signed envelope, verified against the pinned key);
7. **(rev 2)** if a registration for this router LCT exists, the certificate's `issued_at` is **strictly
   greater** than the current one's — two members holding valid certificates for one router LCT cannot
   flip it back and forth;
8. **(rev 2)** the router LCT is not itself the `member` of a current edge (a router is never a child).

Witnessed: `RouterRegistered { router_lct, member, issued_at }`. One router member per router LCT; a
later valid certificate (rule 7) replaces it (re-key). `RouterRetired { router_lct }` by the router
itself or the operator plane. Removing or withdrawing the member retires its router role.
**`RouterRetired` is loud (rev 2):** it raises an operator alarm naming the router's current children,
since their mail now takes H3's retired-router path.

**The router LCT is the local resolver's parent (rev 2, Legion B3).** `cert.router_lct` MUST equal the
LCT hestia's local resolver uses as the parent of its children (`resolve_child_of(router_lct, x)`).
Otherwise every `for_lct` resolves `KnownButNotChild` at S3 and all routed mail is held. The hub cannot
check this; hestia's S1 preflight does (§4).

### H2 — Member-of edges
`POST /v1/hubs/:hub_id/member-of` — signed by the registered router member of `of`. Body:

```json
{ "action": "member_of_report", "member": "lct:web4:mb32:b…x", "of": "lct:web4:mb32:b…y",
  "consent": { "pubkey_hex": "…", "signature_hex": "…", "issued_at": "…" } }
```

Accepted only if:
- `of` is a **registered router** and the signer is its router member;
- `member` and `of` are canonical and differ, and `member` is **not** a registered router (one level, §2);
- **`consent` verifies**: x's key (`CanonicalLctId::derive(pubkey) == member`) signed
  `"web4-member-of-v1\n<hub_id>\n<member>\n<of>\n<issued_at>"`, issued within 10 minutes;
- **(rev 2)** `consent.issued_at` is **strictly greater** than the last accepted `issued_at` for this
  member (report or withdrawal). Without this, a former parent router can replay x's earlier consent
  inside the 10-minute window and pull x back after a move.

**Consent is stored in the witnessed event, not in the projection (rev 2, D7).** Rev 1 discarded it,
which left a later reader with only the hub's word that x agreed, and left the replay guard with no
state to check against. The event carries the evidence; the projection and every read (H4) stay the bare
fact `x member-of y`. The last-accepted `issued_at` per member is derived from the events.

A report that moves x from y′ to y is the same act (x consents to the new parent); it supersedes the
old edge.

Withdrawal: `MemberOfWithdrawn { member, by, consent? }` — by the router member of the current parent,
or by x with its own signature over a **separate domain string (rev 2)**
`"web4-member-of-withdraw-v1\n<hub_id>\n<member>\n<of>\n<issued_at>"`, subject to the same window and
monotonic `issued_at`. A report consent can never be replayed as a withdrawal, or vice versa.

Witnessed: `MemberOfReported { member, of, consent }` and `MemberOfWithdrawn { … }`. Projection:
`member_of: BTreeMap<CanonicalLctId, CanonicalLctId>` — one current parent per member.

### H3 — Routing on delivery
Point deliveries (`referenced_act` to a peer, `send_secret`, `route_forward`'s final destination) gain a
canonical destination: an additive `ActAddress` variant in web4-core, `{"to":"lct","canonical":"lct:web4:mb32:…"}`.
**(rev 2)** The field is `canonical`, not `lct_id`: on every other variant `lct_id` is a `Uuid`.

Resolution at the hub, in order:
0. **(rev 2)** destination is itself a registered router LCT → that router member's own mailbox, no
   `for_lct`. A router never routes its own mail upward.
1. destination is canonical LCT-x with a current edge `x → y` and y's router is registered → queue in
   that router member's mailbox with `for_lct: x` on the notice (`SealedNotice.for_lct`, serde default
   `None`; legacy notices are unchanged).
   **y's router is retired (rev 2, CBP S-a / Legion N3):** if x has its **own** receipt-mode membership
   (rule 2's resolution, unambiguous), deliver there and report `routed_via: null`; that is x's real
   mailbox, not a best-effort guess. Otherwise → **409, nothing witnessed** (never a silent drop).
2. destination is a member UUID (legacy `Peer`/`Citizen`) → unchanged behaviour, with one exception:
   if the #883 resolver maps that member to **exactly one** canonical identity (`Resolved`) and that
   identity has an edge, route as in 1. **An ambiguous result (several pins, `pins_of` → `Vec<KeyPin>`)
   falls back to legacy delivery (rev 2, CBP S-b).** This is how existing per-entity memberships migrate
   (§5).
3. otherwise → as today.

The witnessed `ReferencedAct` keeps the true destination (`lct` variant); the routing choice is not a
second fact — it is derived from the projection at delivery time and reported in the response
(`routed_via: <router_lct>`).

**Sealing (rev 2, CBP B2).** A routed notice changes mailbox, so "which key opens this" must be stated:
- **Sender pre-sealed** (`sealed_by` set; `send_secret`) — ciphertext is never re-sealed by the hub. It
  stays sealed to the key the sender sealed to (x's, or the legacy member's). The router demuxes by
  `for_lct` **before** opening and hands the ciphertext to the child, which opens it with its own key.
- **Hub-sealed, x has a pin** (legacy rule-2 case) — the hub seals to x's pinned key, as today; same
  demux-before-open.
- **Hub-sealed, x has no hub pin** (pure-LCT x, no membership) — **(rev 3, Sprout B1)** the hub seals
  to **x's key from the current edge's consent** (`consent.pubkey_hex` in the `MemberOfReported` event,
  D7). The LCT names that key; it is not metadata. The router relays ciphertext it cannot open, the same
  as in the two cases above, and the notice carries `sealed_to: "member"`. Rev 2 sealed to the router
  here; that is dropped, so **no case seals x's mail to the router**. (If dp rules against D7, the
  hub keeps x's pubkey with the edge instead, since that is the one thing an LCT-to-key route needs.)
- **Sender pre-sealing to a pure-LCT x** (`send_secret`) — the sender seals to the same key, fetched
  from the members-only H4 read (`member_of` also returns `pubkey_hex` of the current consent).
Sealing gets its own slice and test vectors (Hub B1, §7), separate from the addressing change.

**Per-child bound in the router mailbox (rev 3, Sprout B3).** The router member is in receipt mode (D5),
so its mailbox never evicts. Once 1000 notices are pending (`MAX_NOTICES_PER_MEMBER`, `full()`), it
refuses every new send with 507. One dead or held child could fill it and block mail to every sibling.
So routed notices are also bounded **per `(router, for_lct)`**. A send over that child's share gets
507 for that child only. A router-wide 507 happens only when the total is full. Notices held un-ACKed at
S3 count against their child's share, not the siblings'. **Receipt fetch must not be head-of-line
blocked.** Today `mailbox_fetch` returns the oldest `limit` (≤ 100) pending notices (`take(limit)`), so
100 held notices for one child would hide every sibling's mail behind them. For a router mailbox the
fetch page is filled **round-robin across `for_lct`** (oldest first within each child). A held child
then takes at most its turn in each page.

### H4 — Reportable read
`member_of` on the sealed channel (members) and `GET /admin/api/member-of/:lct` (operator plane):
`{ "lct": x, "member_of": y | null, "pubkey_hex": <current consent key> | null, "witnessed_at": <entry_index> }`
(`pubkey_hex` added in rev 3 for sealing to a pure-LCT x) — and `routers` listing
`{router_lct, member}`. **Members-only**, not the public plane: the edge set is machine topology. The
read is the bare fact; consent evidence is in the ledger event at `witnessed_at` for anyone who audits.

## 4. hestia contract

- **S1 — register the router.** After `receiver-router-certify` (#1230), present the certificate to H1.
  Re-present on re-key. **Preflight (rev 2, Legion B3):** refuse to register unless `cert.router_lct` is
  the parent LCT the local resolver uses and `children_of(router_lct)` agrees with the bindings S2 is
  about to report. **(rev 4, Legion)** Compare only the registry `child_lct` set: membership-derived
  LCT-h edges (S2's second edge) resolve through the binding table, not `children_of`, so including them
  would refuse registration on every machine with a legacy per-being membership. Today the resolver and
  the certifier share `receiver_router_lct()` (hestia `cli.rs:3367`, `:3815`, `:3857`), so the check only
  bites on an explicit `--parent` that disagrees. Today `receiver_router_lct()` falls back to the sovereign LCT; S4 must land, or the
  certificate must name that same LCT, before S1 runs.
- **S2 — report edges.** When a local entity is bound to this machine (its LCT's `mrh.bound` parent edge
  names the machine router), sign consent with the entity's binding key and submit H2. Withdraw on unbind.
  **(rev 2, Legion B1)** For an entity that also holds a per-entity hub membership, additionally report
  the **membership-key-derived** LCT (`LCT-h = derive(member pin)`) as member-of the router, consent
  signed by the membership key (`member_key_source`). The binding LCT and the membership LCT differ by
  design (`LocalMailboxBinding` keeps `child_lct` and `hub_member_lct` separate); without the second
  edge, H3 rule 2 never matches and migration silently never happens.
- **S3 — deliver by `for_lct`.** The receiver reads `for_lct` and resolves it — through
  `resolve_child_of(router, x)` (#1211) **or, for a membership-derived LCT, through the binding table
  (rev 2)** — and enqueues into that child's local inbox. **Demux before open (rev 2):** the router never
  tries to open ciphertext addressed to a child. **(rev 3)** No routed notice is sealed to the router, so
  the router opens none of them.
  **An unknown or non-local `for_lct` is held un-ACKed and reported** — never ACKed into the router's own
  inbox (the custody gap raised on hestia #1210 for `route.forward` is the same shape and gets the same rule).
- **S4 — parent migration.** Local entities are currently minted with the hestia sovereign as parent
  (#1211 note). They are re-parented to the machine router LCT, so the local resolver and the hub edge
  agree. Ordering is constrained by S1's preflight. **(rev 4, Legion)** S4 moves the certificate's
  `router_lct` and the resolver parent together, so it must re-certify and re-present through H1.7.

## 5. Migration of today's per-entity memberships

Beings and seats that are hub members today (`hub-being`, `sprout-being`, …) keep working: delivery by
member UUID is unchanged until an edge exists for that member's canonical identity. Once S2 reports the
edge **for the membership-derived LCT** (rev 2), H3 rule 2 routes their mail through their machine's
router — senders change nothing. The per-entity membership then carries no mail and can be withdrawn by
its owner (web4 #804) on the operator's schedule — **but not before** the router path is proven for that
entity, because it is also the retired-router fallback (H3.1). **(rev 3, Sprout N6)** An entity
whose membership has already been withdrawn has no fallback, so if its router retires its mail returns
409 until the router is registered again. The `RouterRetired` alarm names those children.

**Check before Hub B (rev 2):** confirm against `hub-being` that its membership pin derives to the LCT
S2 will report. If it does not, rule 2 is inert for that entity and the gap is found before build, not after.

## 6. Security and failure semantics

| threat / condition | posture |
|---|---|
| a router claims a foreign LCT-x | refused: no consent signature from x's key |
| a non-router member reports edges | refused: signer must be `of`'s registered router |
| router impersonation | certificate double-signed, member key = hub pin, caller = that member |
| two certs for one router LCT flip-flopping | refused: `issued_at` strictly increasing (H1.7) |
| former parent replays x's consent after a move | refused: per-member `issued_at` strictly increasing (H2) |
| report consent replayed as a withdrawal | refused: separate domain string |
| router listed as a child / mail to a router routed upward | refused at intake (H1.8, H2); H3 rule 0 |
| router not in receipt mode | registration refused (H1.5) |
| router retired | loud operator alarm naming its children; x's own receipt membership if any, else 409. **(rev 4, Legion)** The fallback covers only the membership-derived LCT-h (its pin derives LCT-h). Mail to the registry LCT-x has no receipt membership the hub can resolve, so it returns 409 |
| unknown `for_lct` at the router | held un-ACKed and reported; hub keeps custody |
| pre-sealed ciphertext reaches the router | demux before open; the child opens it |
| hub-sealed mail to a pure-LCT x | sealed to x's consent key; the router relays it unopened (rev 3) |
| one child's held or flooded mail blocks its siblings | per-`(router, for_lct)` bound; fetch not head-of-line blocked (rev 3) |
| **x's own local hestia** | **not defended against.** D1 consent stops a *foreign* router from claiming x. The local hestia holds x's keys (S2), so it signs x's consent and could open x's mail. Consent records that x is bound to this machine. It is not x's independent assent to that machine's hestia (rev 3, Sprout N5) |
| topology disclosure | edges readable by members and the operator only; consent only in the ledger |
| stale edge after a machine dies | the edge stays (it is a fact about the report); mail queues under the child's per-`for_lct` share until 507 (receipt mode does not evict); the sender sees the 507 |

## 7. Slices

1. **Hub A** — H1 + H2 + projection + H4, with tests (cert vectors from hestia #1230, consent, monotonic
   `issued_at` for certs and consents, withdraw domain string, router-is-not-a-child, supersede, withdraw).
   Unblocked by rev 2: nothing in it depends on the open questions.
2. **Hub B1** — `SealedNotice.for_lct` + `sealed_to`, sealing semantics, test vectors per case (H3 Sealing),
   the per-`(router, for_lct)` bound, and H4 `pubkey_hex`.
3. **Hub B2** — `ActAddress::Lct { canonical }` (web4-core, additive), delivery resolution, `routed_via`.
   **Rollout order:** `ActAddress` is `#[serde(tag = "to")]` with no catch-all, so a reader on an older
   web4-core hard-fails folding a ledger that contains `{"to":"lct"}`. Every ledger reader (hub,
   hestia if it deserializes `ReferencedAct`, fleet tooling) bumps web4-core **before** the hub writes the
   first `lct` address.
4. **hestia A** — S1 (with preflight) + S2 (+ S4 for newly bound entities). B3 is settled by
   existing hestia code (rev 4); starts once Hub A's H1/H2 endpoints exist to test against.
5. **hestia B** — S3 (binding-table resolution, demux before open), and the un-ACKed hold for unknown
   `for_lct` / `route.forward`.
6. **Fleet** — Sprout ↔ Legion pilot over the routed path; then migrate beings (§5).

## 8. Decisions taken by default — reviewers, object here

| # | decision | default | why |
|---|---|---|---|
| D1 | consent from x required for an edge | **yes** | otherwise any router can capture any LCT's mail |
| D2 | an edge takes precedence over x's direct membership | **yes**, except a retired router falls back to x's own receipt membership (rev 2) | dp: "messages addressed to LCT-x via hub get routed to LCT-y"; x's own mailbox is not best-effort |
| D3 | read visibility | **members + operator** | edges are machine topology (Legion, CBP: agree) |
| D4 | destination addressing | **additive `ActAddress::Lct { canonical }`** in web4-core, readers bump first | the witnessed act must name the true destination, not the router |
| D5 | router must be in receipt mode | **yes** | one destructive drain would lose every child's mail (Legion, CBP: agree) |
| D6 | hub edges are one level (parent = router) | **yes** (rev 2) | rev 1's chain walk was unbuildable under H2; deeper structure is hestia-local |
| D7 | consent evidence stored in the witnessed event; projection and read are the bare fact | **yes** (rev 2) — **needs dp** | replay guard needs state; third-party re-verification needs evidence; rev 3 sealing to x reads the consent key from it. Read as "no meta in what is reported". If dp meant no meta on the ledger either, the alternative is hub-internal unwitnessed `issued_at` + x's pubkey (Legion N2, Sprout B1) and the audit property is lost |

### Open — not decided here
- **O1, the reply path (CBP).** `SealedNotice.from` is a `Uuid`. When x replies to a routed notice, who
  signs and what is in the sender field — the router's membership with an attested `from_lct: x`, or x
  through the router? Must be settled in Hub B2; until then x replies through whatever membership it has.

## 9. Changelog

**rev 4 (2026-10-07)** — Legion's re-review of rev 2 (request for changes withdrawn; two nits).
- S1: the preflight compares only the registry `child_lct` set, not membership-derived LCT-h edges.
- §6: the retired-router fallback covers LCT-h only; the registry LCT-x returns 409.
- S4: re-parenting re-certifies through H1.7. §7: hestia A is no longer gated on B3.

**rev 3 (2026-10-07)** — review: Sprout (hestia side, F3 pilot).
- H3 Sealing, H4, S3: a pure-LCT x is sealed to its consent key and the router relays it unopened; `sealed_to: "router"` removed; H4 returns `pubkey_hex` for pre-sealing (Sprout B1).
- H3, §6, Hub B1: per-`(router, for_lct)` bound in the receipt mailbox; fetch not head-of-line blocked (Sprout B3). Receipt mode refuses with 507 rather than evicting, so the failure is a block on sibling mail, not lost mail.
- §6: the local hestia is stated as outside D1's protection (Sprout N5).
- §5: the 409 window for entities with no direct membership left (Sprout N6).
- Already covered by rev 2: B2 ancestor-or-self (H1.8 + H3 rule 0), N1 replay, N2 withdraw domain, N3 rollout order (field kept as `canonical`, per CBP), N4 pin = binding check (S2 second edge + pre-build check; Sprout checks `sprout-being`).

**rev 2 (2026-10-07)** — reviews: Legion (hestia side, F3 pilot), CBP.
- §2/H2/H3, D6: one-level hub edges; chain walk removed (Legion B2, CBP B1 — both picked this).
- H1.7, H2: strictly increasing `issued_at` for router certs and per-member consents (Legion N1/N2, CBP B3).
- H2, D7: consent stored in the witnessed event, not the projection (CBP B3) — flagged for dp.
- H2: withdraw domain string (Legion N2, CBP S-c).
- H1.8, H3 rule 0: a router is never a child; mail to a router stays in its mailbox (CBP S-d).
- H3.1, D2: retired router → x's own receipt membership or 409; `RouterRetired` alarms (CBP S-a, Legion N3).
- H3.2: reroute only on an unambiguous `Resolved` (CBP S-b).
- H3 Sealing, S3: sealing cases, demux before open, `sealed_to` (CBP B2).
- H3, §7: `ActAddress::Lct { canonical }`; readers bump web4-core first (CBP S-e).
- H1, S1: `router_lct` = local resolver parent; S1 preflight (Legion B3).
- S2, S3, §5: also report the membership-derived LCT; binding-table resolution; pre-build check against `hub-being` (Legion B1, CBP S-b).
- §7: Hub B split into B1 (sealing) and B2 (addressing) (CBP frame).
- O1: reply path recorded as open (CBP).
