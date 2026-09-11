# PRD — Role entities, fractal sub-roles, and authority by occupancy

**Status:** proposed — dp-directed 2026-09-10
**Owner:** dp
**Author:** hub-claude
**Scope:** `web4-core` role substrate, Hub role projection, and the migration of the Sovereign
Council onto that substrate.

**Relates to — do not duplicate these mechanisms:**

- `PRD_HUB_V2_FEDERATED.md` **R4** (roles as entities) and **R5** (roles promotable into
  fractal sub-hubs). This PRD implements R4 and builds the rung R5 needs.
- `PRD_ROLE_SCOPE_BRIDGE.md` — role occupancy, permission classes, proof tiers, and the rule
  that local authority is the intersection of member clearance and role scope.
- `PRD_EVOLUTION.md` §3 — its ownership map cites R4/R5 as the collective primitive's home.
  web4#831 reported that home as empty. **This PRD corrects that report** (see §2).
- The ratified merit ruling: a role's tensor persists across occupants; rotation never
  resets it and never transfers one occupant's attributed merit to another.

---

## 0. The evolution in one sentence

**A role is an entity, a role may contain sub-roles, a role is FILLED only while paired with
an entity, and authority to act comes from that occupancy — not from appearing on a list kept
beside it.**

An unfilled role cannot act. The only act available to it is *to be filled*, by pairing or
binding as its law directs. That rule is fractal by construction: it asks nothing about
depth, parentage or kind, only whether someone is in the chair.

The Sovereign Council is the worked example: `council` is a role, each seat is a
`council-member` sub-role, and the M-of-N signature check becomes *"M distinct entities, each
filling a sub-role of this role, signed"*.

---

## 1. What dp asked for, verbatim

> convert existing roles into proper entities. then before we do the upward society
> integration we need a fractal split into sub-roles. council is perfect because its a role
> that has 'council member' sub-roles. the multi-sign can then only be done by entities
> paired with (filling) the council-member roles.

The ordering is load-bearing and is kept: entities first, then the fractal split, then
authority re-derived from occupancy. Upward society integration (R5 promotion into child
societies) is explicitly **after** this and out of scope here.

---

## 2. Correcting the record — twice

`web4-core`'s `RoleAssignment` already carries `role_lct_id` (its comment says "authority
binds here"), its own `T3`/`V3`, `multi_holder`, `additional_holders`,
`threshold: Option<(u32, u32)>`, a lifecycle event log, and a working `rotate()`.
`SocietyRole::Custom(String)` already permits roles beyond the founding nine. So web4#831's
report of "no event kind, no type, no handler" was true of the **ledger** and wrong as a
description of the **substrate**.

**And that correction was itself overstated.** GPT's review of #844 measured the part that
matters here, and it is decisive:

- `filling_entity_lct_id: Uuid` — **not** an `Option`. The core object **cannot represent a
  role that exists while vacant**, which is the single thing this design most needs.
- `set_threshold()` does `n = holder_count()` then `m.min(n)`, and `holder_count()` is
  `1 + additional_holders.len()`. So **N is recomputed from whoever is currently present and
  M is clamped to it** — losing a member *lowers the bar*. Resignation is an implicit
  quorum-reduction mechanism in the substrate today.

So the honest position is the middle one: R4's *identity and tensor* half is built and
unused; its *existence-independent-of-occupancy* half is not built at all. This PRD must add
that half rather than claim to be merely re-wiring.

**Three role shapes now exist and that is the risk to manage** (GPT's first point): the
society document, `web4-core::RoleAssignment`, and the Hub's projection. This PRD's answer:
the Hub struct is named `ProjectedRole` and documented as a **lossy read model**, explicitly
not the semantic object, and §4.1 makes promoting the canonical entity in `web4-core` the
resolution rather than leaving three.

## 3. The three gaps

### G1. Role state is not re-derivable from the chain

`HubEvent::RoleAssigned` is projected as a **no-op**. Roles live only in the society
*document* — a separately written store object. The ledger records that a role was assigned
and the projection ignores it.

Members are re-derivable from the ledger. Roles are not. If the society doc were lost or
diverged, role state could not be rebuilt from a chain that contains every assignment. That
is the same class as a witnessed act whose consequence lives somewhere the witness cannot
reach, and it is the reason a role's tensor cannot currently be audited from the record.

### G2a. Roles have no kind, so a vacancy has no meaning

dp, 2026-09-10: *"we also need to account for 'fungible' roles — that are not limited in
number and any filled role can act in its scope, and new ones can be created on demand so
there are no unfilled fungible roles — citizen role is a good example — whereas
'non-fungible' roles are unique and predetermined, and may be vacant."*

The axis underneath is **whether the role instance exists before its occupant**, and the
consequence is that *vacant* means two different things:

| | **Office** (dp's "non-fungible") | **Capacity** (dp's "fungible") |
|---|---|---|
| constituted by | the society, in advance | the act of filling it |
| cardinality | enumerated, predetermined | unbounded, minted on demand |
| unoccupied means | **vacant** — awaiting a fill, still counted | **spent** — the holder is gone, never refilled |
| counts toward quorum | yes, even while empty | no |
| example | Treasurer; one seat on a council | Citizen |

**The lifecycle is an invariant, not a description — GPT's #845 blocker.** The table above
was true of what the verbs *meant* and false of what the surfaces *allowed*. A first cut
created a Capacity as `RoleCreated` followed by `RoleAssigned`, tolerated the second act
failing, let `fill` rotate any non-retired role of either kind, and let `vacate` empty a
Capacity. So `Capacity && occupant == None && !retired` was reachable, a spent Capacity was
refillable, and the axis collapsed back into the ambiguity it was introduced to remove —
about a day after being introduced.

Four rules make it executable, and they are stated once each:

1. **A Capacity is created occupied, in one act.** `RoleCreated` carries
   `initial_occupant`, required for a Capacity and absent for an Office. There is no window
   between existing and being held because there is no longer a second act to fail.
2. **A Capacity is never filled or rotated.** A new holder gets a new instance; that is
   what "minted on demand" means. `fill` applies to Offices.
3. **A Capacity is never vacated — it is spent.** Ending one retires it, with the holder
   left on the record so the chain says who spent it. So `retire` refuses an *occupied
   Office* (vacate first) and *requires* an occupied Capacity. The verb is the same; the
   kind decides which state it is legal from.
4. **The forbidden state is reported, never repaired.** `is_incoherent_capacity()` exists
   because a ledger is not only written by this daemon. Such a role is already inert —
   `can_act()` is false — so the read model names it and leaves it; a projection that
   quietly normalised it would hide corruption rather than show it.

**On the naming.** dp asked for a better term than fungible/non-fungible and the words
chosen here are **Office** and **Capacity**: an office is a constituted position one
*occupies*; a capacity is a standing one *holds* ("acting in the capacity of a citizen").
Both are ordinary institutional English, neither collides with existing web4 or hestia
vocabulary — unlike "standing", which is already spoken for by standing grants. `seat` and
`class` were the plainer runner-up.

**An observation offered, not ruled on:** dp says a role is filled "by pairing or binding
(depending on role law)", and those are already canon's two entity-relationship mechanisms.
The kinds may turn out to be that same axis — an Office is *paired* (revocable, the office
outlives the pairing, rotation is re-pairing) while a Capacity is *bound* (comes into being
with its holder and ends with them). If that holds, the canon already has the words and
`RoleKind` should collapse into them. It is left as a question because "binding" carries a
hardware-custody meaning elsewhere and collapsing them prematurely would be exactly the
terminology error this section is fixing.

### G2b. There is no containment relation between roles

Nothing expresses "this role is a seat within that role". `Custom(String)` gives new names,
not structure. A council of nine is representable only as one role with eight
`additional_holders`, which flattens the thing dp is asking to make fractal: the seats have
no identity, no tensor, and no history of their own.

### G3. The Sovereign Council is a parallel implementation

`council_holders`, `council_pubkeys` and `council_threshold` are projected from three
bespoke events (`CouncilMemberAdded` / `CouncilMemberRemoved` / `CouncilThresholdChanged`).
**Measured 2026-09-10: 64 references across 9 files.** Every one of them maintains, by hand,
a holder set plus an M-of-N threshold — which is exactly `multi_holder` +
`additional_holders` + `threshold` on a `RoleAssignment`.

Two mechanisms for one concept is how they drift. It has already cost us once: the council
gate and the role system disagree about what "who may act" means, and only one of them is
what the escalation matrix consults.

---

## 4. The design

### 4.1 A role entity

A role is projected from the ledger with its own LCT, charter, tensor, and occupancy. Its
identity is the `role_lct_id`; its occupant is a separate field and may change without the
role changing. **Creating a role and filling a role are different acts** — today they are the
same call, which is why a role cannot exist unfilled and cannot be chartered before it is
staffed.

New ledger verbs:

- `RoleCreated { role_lct_id, role, charter, parent_role_lct_id, created_by }`
- `RoleVacated { role_lct_id, previous_occupant, kind, reason, vacated_by }`

`RoleAssigned` keeps its meaning (fill / rotate) and **gains a projection**.

### 4.2 A sub-role

`parent_role_lct_id: Option<Uuid>` on the role entity. A sub-role is a role whose parent is
another role's LCT. Nothing else distinguishes it — that is what makes the structure
fractal: a sub-role may itself have sub-roles, with the same verbs at every depth.

**Invariants:**

- the parent must exist at creation time;
- no cycles (a role may not be its own ancestor);
- a bounded depth, declared rather than discovered, so a malformed tree cannot make
  projection unbounded;
- deleting is not a thing: a role is **vacated**, never removed, so its tensor and history
  survive. A role with no occupant is a real and useful state (a vacant seat).

### 4.3 Authority by occupancy, with N, O and M kept apart

The M-of-N check becomes:

> **M distinct entities, each currently occupying a seat of role R, have signed.**

A seat is a sub-role of R that is an **Office** and is not **retired**. Three quantities,
never conflated (GPT's third point):

- **N — established cardinality.** Seats that exist and are not retired. *Only retiring a
  seat changes N.*
- **O — occupancy.** Seats with someone in them. *Vacating changes O and nothing else.*
- **M — required signatures.** From the parent role's law. *Never derived from O or N.*

If **O < M** the body simply **cannot reach a verdict** until a seat is filled or a governed
change occurs. That is a real, reportable state and the honest answer. The alternative —
recomputing N from who happens to be present — turns every resignation into a quorum
reduction, which is the defect `set_threshold()` has today and which this design must not
inherit.

Consequences that fall out rather than being designed:

- **A seat's history is its own.** Rotation touches one sub-role and leaves the other seats'
  records alone; the merit ruling applies one level down.
- **It generalises.** Any role with Office sub-roles gets M-of-N. The council stops being
  special.
- **Vacating and retiring are different acts**, and only one of them is allowed to make the
  body easier to command.

#### 4.3.1 The founding Sovereign — a ruling, because the alternatives contradict

GPT's fourth point is correct and cannot be deferred: today `project_council()` includes the
founding Sovereign in the holder set and in N. Sprint 3 requires the legacy and role-derived
projections to agree; Sprint 4 says only seat occupants sign; §5 said the Sovereign stays
outside the seats. **All three cannot hold.**

**Ruling: the founding Sovereign occupies an ordinary `council-member` Office, and its
protection is a rule of current law rather than a property of the role type.** Chosen
because:

- the differential gate in Sprint 3 becomes *possible*: both projections yield the same
  holder set and the same N;
- "only seat occupants sign" stays literally true, with no constitutional signer class
  living beside the rule;
- the protection is **stated somewhere amendable**, which is what keeps the model fractal.

**The revision, and why it matters more than it looks.** This PRD first ruled a *protected*
seat — an Office carrying a flag that made it permanently unvacatable. GPT's follow-up
rejected the flag and not the seat, and the objection is the sharper one: a protection
living in the role **type** is a permanent special case in the substrate, and it says
"this particular founder is special" in the one place no future society can amend. Every
chapter that ever instantiates this model would inherit it.

Protection by **law** gets the identical behaviour today — current law forbids ordinary
vacate and retire on that seat — while leaving governed succession reachable through the
mechanism that already exists for changing law. The role type learns nothing about founders.
Nothing about the Sovereign is unusual except the rule pointing at their seat, and that rule
is amendable by the body it constitutes.

Concretely, Sprint 3 must land the rule **as law**, not as a `bool` on `ProjectedRole`, and
its falsifier is a law amendment that permits succession and then a succession that
executes. If the protection were a type property, that test could not be written at all —
which is the real test of where a rule belongs.

### 4.4 The council, after

```
role: council                        (parent, threshold M-of-N, own LCT + tensor)
├── council-member (seat 1)          (sub-role, own LCT + tensor)  filled by → entity A
├── council-member (seat 2)          (sub-role, own LCT + tensor)  filled by → entity B
└── council-member (seat 3)          (sub-role, own LCT + tensor)  vacant
```

`project_council` returns the same shape it does today — a holder set and a threshold —
derived from the tree instead of from three bespoke events. **Every one of the 64 call sites
keeps working unchanged.** That is deliberate: the migration must not require touching the
governance gate, the escalation matrix, or the proposal flow.

---

## 5. Non-goals and invariants

- **Not upward integration.** R5 promotion of a role into a sovereign child society is the
  next rung and is out of scope. This PRD builds what it stands on.
- **Not a new authorization path.** Authority still resolves through the existing gate; only
  the *source* of "who may sign" changes, from a list to an occupancy query.
- **Not a rewrite of `web4-core`'s role model — but not a parent pointer either.** An
  earlier draft of this line said the core was "largely right" and that this work "adds a
  parent pointer". That was written before the occupancy and threshold findings in §2, and
  it understates what remains. The canonical entity needs **existence separated from
  occupancy** (`filling_entity_lct_id` is a bare `Uuid`) and **quorum semantics that do not
  derive N from who is present** (`set_threshold` clamps M to `holder_count()`). Those are
  the two things the Hub projection is standing in for. `ProjectedRole` is a legitimate
  interim read model; it is not a substitute for that work, and this PRD should not read as
  if it were.
- **No role record is ever deleted.** Vacating ends *occupancy*; retirement ends *present
  constitutional standing*. Both preserve identity, tensor and history. An earlier draft
  said "vacating is the only exit", which survived from before `RoleRetired` existed and
  contradicted the very separation that verb was added to make.
- **A role's tensor never resets on rotation** and is never transferred to an occupant.
  Ratified; re-pinned here because sub-roles multiply the places it could be violated.
- **The founding Sovereign occupies an ordinary council-member Office.** Its protection is
  a rule of *current law*, not a property of the role type — see §4.3.1. An earlier draft of
  this line said the Sovereign remains outside the council seats and that the migration must
  not make it one; that directly contradicted §4.3.1 and is withdrawn.

---

## 6. Sprints

Ordered so that **the hub can conduct governance at every point**, and each sprint is
independently revertible. No sprint may leave the council unable to reach a verdict.

### Sprint 1 — Roles become ledger-derived entities *(no council changes)*

- `RoleCreated` and `RoleVacated` ledger verbs; `RoleAssigned` gains a real projection.
- `HubState.roles: BTreeMap<Uuid, ProjectedRole>` — keyed by role LCT, rebuilt from the chain.
- **Sprint 1 is the substrate only: ledger verbs, projection, and event rendering.** The
  operator surfaces (create / list / vacate / retire) are **Sprint 1b** and land separately.
  GPT's fifth point: the acceptance contract must match what actually lands, and the first
  draft of this PRD promised surfaces the first slice did not contain.
- **Acceptance:** role state after a cold replay of the ledger equals role state before it,
  on a fixture containing create → assign → rotate → vacate. Rotation preserves the role's
  tensor and appends an event. The society document remains authoritative for anything that
  reads it today — this sprint *adds* a projection, it does not switch consumers over.

### Sprint 1b — The operator surfaces *(no council changes)*

Split out of Sprint 1 on GPT's fifth point, and it turned out to carry the sharpest
measurement in this document.

- `POST /admin/api/roles/create`, `/:id/fill`, `/:id/vacate`, `/:id/retire`, and
  `GET /admin/api/roles` — all loopback-only, all through the same governance gate the
  council routes use, all enumerated in the plane-split guard.
- The **four Capacity rules from §3 G2a are enforced here**, one construct each: creation
  is atomic (`initial_occupant` inside `RoleCreated`), `fill` refuses a Capacity, `vacate`
  refuses a Capacity, and `retire` requires an occupied Capacity while refusing an occupied
  Office. The falsifier drives every route that could reach the forbidden state, because
  "unreachable" is a claim about all paths and not about the one that was fixed.
- **Retiring an Office that is occupied is refused.** Vacate first. This is the surface's V
  clause: a live council cannot be shrunk in a single act, and a retire that quietly evicted
  its occupant would re-fuse N and O at the surface after the substrate had split them. The
  same verb on a Capacity is the opposite — it *is* the act of spending one, so it requires
  a holder and leaves them on the record.
- The UI follows the kinds. A held Capacity offers **Spend** and nothing else; it is never
  shown a Fill or Vacate button. An earlier cut offered Fill on a spent Capacity, which
  invites the operator to do the one thing the model forbids — a UI that offers an act the
  surface refuses is a UI that teaches the wrong model.
- `parent_role_lct_id` is **not accepted** here. The verb carries it; the invariants that
  make a parent safe are Sprint 2, and a surface that accepted a parent before its
  invariants existed would be this PRD's own gap, freshly dug.
- Manage renders the entities: a vacant office as **present and empty**, never as absent.
  Held at the operator tier, not published on `/admin/roles` — a public vacancy table
  announces exactly when a council cannot reach quorum, and holding it back is the
  reversible direction.

**What this sprint measured.** `Society::assign_role` keys its map by `role_key(&role)`,
the role's *name*, and calls `existing.rotate(...)` when the key is already present. Two
consequences, both live:

1. A society holds **at most one assignment per role name**. The fleet hub has **twelve
   members and exactly one `citizen`**, and that is why.
2. Granting a role that is already granted **revokes it from the previous holder**. For an
   Office that is correct — it is a rotation. For a Capacity it is the opposite of what the
   word means.

The second is pinned by a test that runs the old behaviour as a control and the new surface
beside it, so the claim is executed rather than asserted. It is also the concrete answer to
*why the Sovereign Council needed a parallel mechanism*: the society document cannot hold
nine council members, because it cannot hold two of anything.

### Sprint 2 — Sub-roles *(structure only, council untouched)*

- `parent_role_lct_id` on `RoleCreated` and on the projected entity.
- Cycle, existence and depth invariants, each with a falsifier.
- `/admin/roles` renders the tree; a vacant seat renders as vacant, never as absent.
- **Acceptance:** a three-level tree projects correctly; a cycle is refused at creation and
  witnesses nothing; depth beyond the bound is refused with the bound named.

### Sprint 3 — Council mirrored onto roles *(dual-read, nothing switched)*

- A single witnessed migration act derives `council` + one `council-member` sub-role per
  current holder from the existing projection.
- `project_council` gains a role-derived implementation **beside** the legacy one.
- **Acceptance:** a differential test asserts the two implementations agree — same holder
  set, same threshold — on a fixture shaped like the live fleet hub. Disagreement fails the
  build. The legacy path is still what the gate consults.

### Sprint 4 — Authority derives from occupancy *(the switch)*

- `submit_proposal` / `sign_proposal` resolve signers by sub-role occupancy.
- The threshold reads from the parent role.
- Legacy `project_council` deleted **only after** Sprint 3's differential has been green
  across a real ledger replay.
- **Acceptance:** the existing end-to-end council fixture (propose → sign to threshold →
  commit → survive reopen) passes unchanged against the new resolution. A signer who is not
  a seat occupant is refused. A vacant established Office **counts toward N and not toward
  O**: it confers no signer and so contributes nothing to reachability, but it remains part
  of established cardinality until it is retired. (An earlier draft said "a vacant seat does
  not count toward N" — the old bug restated in prose, in the same document that corrects
  it.)

### Sprint 5 — Retire the parallel mechanism, and the UI

- `CouncilMemberAdded` / `Removed` / `ThresholdChanged` become **replay-only**: still
  projected for historical ledgers, no longer writable.
- Manage renders the council as a role with its seats; add/remove become create-seat and
  vacate-seat.
- **Acceptance:** a ledger containing only legacy council events still projects a correct
  council. No write path emits a legacy council event.

---

## 7. Migration safety

The council is load-bearing: if it cannot reach a verdict, the hub cannot conduct governed
acts at M≥2. Three rules follow.

1. **Dual-read before switch-over** (Sprint 3 before 4), with a differential test as the
   gate. "Both implementations agree" is the only evidence that will be accepted.
2. **Replay compatibility is permanent.** The live fleet hub's ledger contains legacy council
   events at indices that will never be rewritten. Sprint 5 retires the *write* path, never
   the projection. A hub that cannot replay its own history is a hub that cannot boot.
3. **`HubEvent` is internally tagged with no unknown-variant arm.** Every new verb here is a
   one-way door: once one is on a ledger, an older binary cannot replay that store. Deploy
   the reader before the writer, on every seat, as with `member_renamed`.

---

## 8. What this unlocks, stated so it is not over-claimed

R5 — promoting a role into a sovereign child society — needs a role that is an entity with
its own identity, history and seats. After Sprint 2 that exists. This PRD does **not**
deliver R5, and nothing here should be read as "split without fragmenting is done". It
delivers the substrate that #831 correctly identified as the E-series' missing foundation.
