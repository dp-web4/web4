# PRD — Member-of routing: the hub routes to a machine's hestia; hestia routes locally

**Status:** design for review. Hub + hestia contract. Implementation slices in §7.
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
- **Member-of edge.** A witnessed fact on the hub ledger: *LCT-x is reported as member-of LCT-y.* Nothing
  else is recorded with it.
- **Routing rule.** Mail addressed to LCT-x is queued in the mailbox of LCT-x's nearest ancestor that has
  a registered router, with the original destination carried on the notice (`for_lct: LCT-x`) and never
  rewritten. That router delivers locally.
- **Hierarchy.** Edges compose (x → y → z). Routing stops at the first ancestor with a router.

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
6. the caller is that member (signed envelope, verified against the pinned key).

Witnessed: `RouterRegistered { router_lct, member }`. One router member per router LCT; a later valid
certificate for the same LCT replaces it (re-key, `RouterRegistered` again). `RouterRetired { router_lct }`
by the router itself or the operator plane. Removing or withdrawing the member retires its router role.

### H2 — Member-of edges
`POST /v1/hubs/:hub_id/member-of` — signed by the registered router member of `of`. Body:

```json
{ "action": "member_of_report", "member": "lct:web4:mb32:b…x", "of": "lct:web4:mb32:b…y",
  "consent": { "pubkey_hex": "…", "signature_hex": "…", "issued_at": "…" } }
```

Accepted only if: `of` has a registered router and the signer is it; `member` and `of` are canonical and
differ; the edge would not create a cycle; ancestry depth stays ≤ 8; and **`consent` verifies** — x's
binding key (`CanonicalLctId::derive(pubkey) == member`) signed
`"web4-member-of-v1\n<hub_id>\n<member>\n<of>\n<issued_at>"`, issued within 10 minutes.

Consent is checked at intake and **not stored** (dp: no meta). Without it any router could claim any
LCT-x and receive its mail; with it, the recorded edge stays the bare fact. A report that moves x from
y′ to y is the same act (x consents to the new parent); it supersedes the old edge.

Witnessed: `MemberOfReported { member, of }` and `MemberOfWithdrawn { member }` (by the router of the
current parent, or by x with its own consent signature). Projection: `member_of: BTreeMap<CanonicalLctId,
CanonicalLctId>` — one current parent per member.

### H3 — Routing on delivery
Point deliveries (`referenced_act` to a peer, `send_secret`, `route_forward`'s final destination) gain a
canonical destination: an additive `ActAddress` variant in web4-core, `{"to":"lct","lct_id":"lct:web4:mb32:…"}`.

Resolution at the hub, in order:
1. destination is canonical LCT-x with a member-of chain → the nearest ancestor with a registered router;
   queue in that router member's mailbox with `for_lct: x` on the notice (`SealedNotice.for_lct`, serde
   default `None`; legacy notices are unchanged). No router reachable on the chain → **409, nothing
   witnessed** (never a silent drop, never a best-effort direct delivery).
2. destination is a member UUID (legacy `Peer`/`Citizen`) → unchanged behaviour, with one exception:
   if that member's canonical identity (derived from its pinned key, the #883 resolver) has a member-of
   edge, route as in 1. This is how existing per-entity memberships migrate (§5) without senders changing.
3. otherwise → as today.

The witnessed `ReferencedAct` keeps the true destination (`lct` variant); the routing choice is not a
second fact — it is derived from the projection at delivery time and reported in the response
(`routed_via: <router_lct>`).

### H4 — Reportable read
`member_of` on the sealed channel (members) and `GET /admin/api/member-of/:lct` (operator plane):
`{ "lct": x, "member_of": y | null, "witnessed_at": <entry_index> }` — and `routers` listing
`{router_lct, member}`. **Members-only**, not the public plane: the edge set is machine topology.

## 4. hestia contract

- **S1 — register the router.** After `receiver-router-certify` (#1230), present the certificate to H1.
  Re-present on re-key.
- **S2 — report edges.** When a local entity is bound to this machine (its LCT's `mrh.bound` parent edge
  names the machine router), sign consent with the entity's binding key and submit H2. Withdraw on unbind.
  hestia already holds local entities' keys; consent costs one signature.
- **S3 — deliver by `for_lct`.** The receiver reads `for_lct`, resolves it with `resolve_child_of(router,
  x)` (#1211), and enqueues into that child's local inbox. **An unknown or non-local `for_lct` is held
  un-ACKed and reported** — never ACKed into the router's own inbox (the custody gap raised on hestia #1210
  for `route.forward` is the same shape and gets the same rule).
- **S4 — parent migration.** Local entities are currently minted with the hestia sovereign as parent
  (#1211 note). They are re-parented to the machine router LCT, so the local resolver and the hub edge
  agree.

## 5. Migration of today's per-entity memberships

Beings and seats that are hub members today (`hub-being`, `sprout-being`, …) keep working: delivery by
member UUID is unchanged until an edge exists for that member's canonical identity. Once S2 reports the
edge, H3 rule 2 routes their mail through their machine's router — senders change nothing. The per-entity
membership then carries no mail and can be withdrawn by its owner (web4 #804) on the operator's schedule.

## 6. Security and failure semantics

| threat / condition | posture |
|---|---|
| a router claims a foreign LCT-x | refused: no consent signature from x's binding key |
| a non-router member reports edges | refused: signer must be `of`'s registered router |
| router impersonation | certificate double-signed, member key = hub pin, caller = that member |
| cycles / deep chains | refused at intake (cycle check, depth ≤ 8) |
| router not in receipt mode | registration refused (H1.5); delivery to an un-routable chain is 409 |
| unknown `for_lct` at the router | held un-ACKed and reported; hub keeps custody |
| topology disclosure | edges readable by members and the operator only |
| stale edge after a machine dies | the edge stays (it is a fact about the report); mail queues under the router's mailbox TTL/cap and the sender is alarmed as today (#578) |

## 7. Slices

1. **Hub A** — H1 + H2 + projection + H4, with tests (cert vectors from hestia #1230, consent, cycle, supersede, withdraw).
2. **Hub B** — H3: `ActAddress::Lct` (web4-core, additive), `SealedNotice.for_lct`, delivery resolution, `routed_via`.
3. **hestia A** — S1 + S2 (+ S4 for newly bound entities).
4. **hestia B** — S3, and the un-ACKed hold for unknown `for_lct` / `route.forward`.
5. **Fleet** — Sprout ↔ Legion pilot over the routed path; then migrate beings (§5).

## 8. Decisions taken by default — reviewers, object here

| # | decision | default | why |
|---|---|---|---|
| D1 | consent from x required for an edge | **yes** | otherwise any router can capture any LCT's mail |
| D2 | an edge takes precedence over x's direct membership | **yes** | dp: "messages addressed to LCT-x via hub get routed to LCT-y" |
| D3 | read visibility | **members + operator** | edges are machine topology |
| D4 | destination addressing | **additive `ActAddress::Lct`** in web4-core | the witnessed act must name the true destination, not the router |
| D5 | router must be in receipt mode | **yes** | one destructive drain would lose every child's mail |
