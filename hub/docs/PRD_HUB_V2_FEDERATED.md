# PRD — the federated hub: what the hub is becoming

**Status**: proposed — dp-directed 2026-08-12; drafted by HUB-Claude the same day; **maintained** (this
document is the living north star; amend it by PR as rulings land, the way
`hestia/docs/PRD_GATE_CONSOLIDATION.md` is maintained).
**Owner**: dp. **Maintainer**: the HUB seat.
**Relates to**: `PRD.md` (the v0.1 pre-build PRD, now historical — its MVP largely SHIPPED),
`V2-V3-ARCHITECTURE.md` (live architecture), `HUB-LAW.md`, `ROLES.md`,
`hestia/docs/PRD_GATE_CONSOLIDATION.md` (the transfer source for §R7 and the model for how this
document should be maintained and reviewed).

---

## 1. What the hub is becoming

The v0.1 hub is a **single-chapter society daemon**: one sovereign, seven fixed roles, one law, one
witnessed ledger, one membrane. That shipped. What it is not yet is **fractal**: hubs cannot federate
with peers, cannot compose into greater hubs, cannot spawn sub-hubs, and cannot reason about one
another's law. The Web4 society pattern — fractal, anti-hierarchical, federation-by-consent — is only
half-realized until a hub is both a *member of* and a *host to* other societies.

Two invariants carry over unchanged and bound everything below:

- **One authority path.** Every consequential act passes the law gate (`production_law_gate` /
  PolicyEntity); plugins and surfaces delegate, they never re-decide. Federation must not introduce a
  second authority path — a federated request is *more* gated, never differently gated.
- **Witness, don't control.** Every cross-hub relationship below is built from witnessed, revocable,
  consent-based edges. No hub ever writes another hub's state. Alignment is observed and recorded;
  it is never enforced by overwrite.

## 2. Requirements

Numbered R1–R8. R1–R6 are dp's directive (2026-08-12 verbatim intent, sharpened); R7 is the ratified
hestia-transfer set; R8 is the proving use case.

### R1. Fractal federation into peer societies

A hub can federate with peer hubs, each remaining fully sovereign.

- **Handshake**: exchange of tier-0 identity (did:web4 / pubkey), current law digest + amendment head,
  and ledger head. Mutual admission is a witnessed act on **both** ledgers — one federation edge per
  society pair (the 17B membership-edge discipline applies: exactly one edge per pair, not one
  globally).
- **The edge is a consent object**: scoped (what queries/flows it permits), revocable unilaterally,
  and carrying the vouching basis on which it was admitted.
- **Federated discovery**: `find_members`-class queries may cross an edge only when *both* laws allow
  the query class, and results are always mediated by the answering hub (no direct store access,
  no bulk export by default).
- Federation transport rides the existing membrane (MCP / signed REST), not a new protocol layer.

### R2. Greater hubs, chartered for a specific role

Peer societies can instantiate a **greater hub** — a hub whose members are hubs — and its charter is
deliberately narrow: it exists to fill a **specific named role** for its members (first candidate:
cross-society member discovery; later candidates: standards custody, dispute escalation, event
coordination).

- **Anti-hierarchy is structural, not aspirational**: the greater hub holds only the authority its
  member hubs explicitly delegate, the delegation is per-member, revocable, and recorded on both
  ledgers, and the greater hub's law binds only the delegated surface. It is a *role filled by a
  society*, not a superior society.
- A greater hub is an ordinary hub binary with an ordinary law — composition, not a new kind.
- Member hubs appear in the greater hub as member entities (their LCTs are society LCTs). Everything
  R4 says about roles applies inside the greater hub unchanged.

### R3. A local ledger that is fractally joinable

Each hub keeps its local hash-chained witnessed ledger (exists today). Joinability means other hubs
can **witness** it, cheaply and continuously.

- **Default mechanism — hash witness with timestamp**: on a law-configurable cadence (and on
  consequential events), a hub publishes `(ledger head hash, height, timestamp, signature)` to its
  federation peers, and each peer records the witnessed head on its own ledger. This is the
  lightweight arm: constant-size, privacy-preserving (a head hash discloses nothing), and it makes
  rollback/fork of a peer's ledger detectable by anyone holding the witnessed heads. It reuses the
  exact pattern the law-integrity gate already trusts (a witnessed head digest).
- **Escalation mechanism — periodic state checkpoint**: for relationships that warrant it (law-scoped,
  e.g. a greater hub archiving for its members, or AIC national for chapters), a hub may additionally
  publish signed periodic state checkpoints (sealed snapshot + head binding), enabling audit and
  disaster recovery at the cost of bandwidth, storage, and a larger disclosure surface.
- **Recommendation (needs dp ruling — §3 Q1)**: layer them. Hash witnessing is the always-on default
  for every federation edge; checkpoints are an opt-in per-edge capability granted by law. "Joinable"
  then means: any two witnessed ledgers can be placed into one partial order by their exchanged
  witnessed heads, without either ever containing the other.

### R4. New roles as entities

Roles become first-class, creatable at runtime — today's seven are the founding set, not the type.

- A role is an **entity**: it has an LCT, a charter (the policy-action set it may perform — which is
  exactly the hub-law gate's vocabulary already), and its own reputation record.
- **Creating a role is a witnessed governed act** (law-gated, quorum per law); **filling** a role is
  conferral (17A pattern: quorum of witnesses, backing attestations recorded).
- Per the ratified merit ruling: the role's tensor persists across occupants; the occupant is a
  sub-dimension ("when filled by X") under temperament. Rotation never resets the role's record.
- The seven founding roles migrate onto this substrate (they become role-entities with founding
  charters) rather than remaining a parallel hard-coded system — one mechanism, no legacy fork.

### R5. Roles promotable into fractal sub-hubs

Some roles outgrow a single occupant: a committee, a working group, an events team. A role-entity can
be **promoted into a sub-hub** — the role becomes a society whose charter derives from the role's
charter.

- The promotion is a witnessed governed act in the parent (quorum per law) plus an ignition of the
  child (its own sovereign act — the child is born sovereign, not owned).
- The parent–child relationship is an ordinary **federation edge (R1) with a role-scoped delegation
  (R2 semantics)**: the child fills, for the parent, exactly the role it was promoted from. Fractal
  recursion falls out: same binary, same law machinery, same conferral discipline at every scale.
- Demotion/dissolution: the edge is revocable from either side; the parent revoking the delegation
  reclaims the role (the role-entity persists — R4 — with its tensor intact); the child dissolving
  returns a terminal witnessed entry.

### R6. Law-sync for hierarchically related hubs = an alignment ledger, not shared law

Related hubs (parent/child, member/greater) do **not** share law and never auto-sync it.

- Each hub already publishes a witnessed law-amendment history (law digest at each head). Federation
  peers exchange law heads as part of R3 witnessing.
- Each side maintains an **alignment record** against each related hub: per law section (granularity
  needs ruling — §3 Q4), a state of `aligned | diverged | silent-here | silent-there`, recomputed
  whenever either side's law head advances, and recorded as a witnessed entry when it *changes*.
- **Misalignment is a fact to surface, not an error to fix.** Divergence beyond what an edge's
  delegation charter tolerates triggers law-defined responses — flag on the operator surface,
  escalate, suspend the delegated surface — but never an overwrite of anyone's law. (This is the
  fail-closed+warn default doing federation work: unrecognized divergence defaults to
  flag-and-continue for peers, deny-delegated-surface for chartered relationships, both
  law-overridable.)

### R7. The hestia-transfer set (concrete, from `PRD_GATE_CONSOLIDATION.md` lessons)

- **R7a — degraded-verdict recording, BEFORE the reputation seam opens.** Every infra/degraded event
  (locked-state refusal, hestia-callback signer unreachable, federation peer unreachable, law-gate
  timeout) is recorded append-only and **distinguishable from a conduct deny**. Reputation deltas
  carry a conduct-vs-infra class, and infra **never** scores as conduct. This is the fleet's kimi
  PR #357 lesson applied at hub scale, and it gates opening `reputation_emit` (~9.5k queued deltas):
  the seam does not open until this contract is enforced and tested.
- **R7b — asserted-asker admission law.** Witness vouches count only toward identities resolved from
  the authoritative record; a self-asserted binding collects no peer factors. Generalizes the
  Legion-incident roster gate (machine-keyed filter) into mechanism + law, and extends it across
  federation edges: a *society* asserting itself into R1/R2 relationships is subject to the same rule.
- **R7c — governance-closure protection + ratified-digest surface.** A supervisor-owned manifest of
  the ratified hub binary digest; the running hub self-reports what it is executing (extends
  hub-watch `self_fingerprint`); operator surface shows current/stale/unknown per seat; the deploy
  path (unit file, deploy scripts, binary path) joins the protected closure. A write that can
  redirect *which hub executes* is equivalent to a write to the hub. (The parked-checkout incident is
  the standing proof this is needed.)
- **R7d — availability parity.** Idle-state timeout rate across member callers is equal and ≈0,
  measured live, with a periodic Class-T-style pair audit (per-member: caller budget vs hub response
  time). Structural per-caller cost asymmetry manufactures fail-closed timeouts that then read as
  conduct — R7a's recording makes this visible; R7d makes it a criterion.

### R8. The proving use case — AIC chapter/member management

The first deployment target remains a volunteer-driven collective organized in chapters (AIC). The
mapping is already almost 1:1 — this PRD makes it explicit and keeps it testable:

| AIC operational need | Hub mechanism |
|---|---|
| Stand up a chapter | `hub init` — society + founding charter + 7 role defaults |
| Onboard a member, verifiably | Admission queue + witnessed conferral with vouching basis (17A/17B) |
| Officers / responsibilities | Role-entities (R4): chartered, conferrable, rotating without history loss |
| Bylaws that are actually enforced | Hub law: inspectable, machine-enforced at the gate, amendable by due process, every amendment witnessed |
| Meeting / decision record | The witnessed ledger — append-only, tamper-evident, exportable |
| Contribution that travels | Reputation per (entity, role), portable across chapters via federation edges (R1) |
| "Who knows X in another chapter?" | Federated `find_members` (R1) under both chapters' laws |
| National ↔ chapters without capture | Greater hub chartered for a narrow role (R2) + alignment ledger instead of imposed bylaws (R6) |
| Chapter splits / working groups | Role → sub-hub promotion (R5) |
| Trust in the record itself | Fractal ledger witnessing (R3) — chapters witness each other's heads |

**Pain-point validation is open**: the table above maps *presumed* pain points (organizer time,
non-portable reputation, invisible cross-chapter discovery, governance opacity). Before the AIC
presentation is built, dp confirms/edits the actual pain-point list from AIC conversations, and the
presentation deliverable (separate artifact, not this PRD) leads with their words, not ours.

## 3. Design questions needing dp rulings

1. **R3 — witnessing depth.** Ratify the layered recommendation (hash-witness always-on; checkpoints
   per-edge opt-in by law)? Or one mechanism only?
2. **R2 — first greater-hub charter.** Recommend the minimum: cross-society member discovery only.
   Ratify, or charter more at birth?
3. **R5 — promotion authority.** Recommend: quorum conferral in the parent per parent law **plus**
   sovereign ignition of the child (child born sovereign). Ratify?
4. **R6 — alignment granularity.** Section-level (cheap, coarse) vs rule-level (precise, chattier
   alignment ledger). Recommend section-level v0, rule-level where a delegation charter demands it.
5. **Sequencing** — endorse §5's phase order (in particular: R7a gates the reputation seam, and
   R4 lands before R2/R5 because both compose out of role-entities)?

## 4. Current state (measured, 2026-08-12)

**Already true**: one authority path (law gate; `hub-plugin` owns no policy); locked-shell degraded
mode serving tier-0 identity + law read-only (= deny-writes-allow-reads, the same semantics hestia
just ratified); hash-chained witnessed ledger; witnessed law amendments; admission queue + opkey
vouching (#540); paired channels; hestia-mode; hub-watch self-fingerprint.
**Absent**: every federation surface (R1–R3, R5, R6), runtime role creation (R4 — roles are the fixed
seven), the R7 set (recording contract, asserted-asker law, ratified-digest manifest, parity
instrument), and `reputation_emit` (dark by design, pending dp + R7a).

## 5. Ordered plan (proposed)

- **Phase 0 — hygiene that gates everything** — R7a (recording contract; unblocks the reputation
  seam at dp's discretion), R7b (asserted-asker law), R7c (ratified-digest surface + closure).
- **Phase 1 — R4 roles-as-entities.** The substrate: R2's chartered role and R5's promotable role are
  both role-entities. Migrate the founding seven onto it.
- **Phase 2 — R1 peer federation MVP** + R3 hash witnessing + R6 alignment record v0. Two real hubs,
  two machines, witnessed edge, law heads exchanged, federated discovery behind both laws.
- **Phase 3 — R2 greater hub** (discovery charter) + R7d parity instrument reading federation calls.
- **Phase 4 — R5 promotion** (role → sub-hub), demotion/dissolution paths.
- **Phase 5 — R3 checkpoints** (if ruled in) for the edges whose law asks for them.
- **Throughout — R8**: validate each phase against a real AIC chapter workflow; the presentation
  artifact follows the pain-point confirmation, not the other way around.

## 6. Falsifiable acceptance criteria

1. **R1**: two hubs on separate machines complete the handshake; each ledger carries the witnessed
   federation edge and the peer's law head; a federated member query answers only when both laws
   allow it and returns nothing after either side revokes; exactly one edge exists per society pair.
2. **R2**: a greater hub answers a cross-society discovery query for two member hubs; revoking one
   member's delegation stops *that member's* participation within one witness cycle; the greater hub
   can perform **no act** outside its chartered role (differential test drives non-chartered actions
   and requires uniform refusal).
3. **R3**: a peer's ledger rollback/fork is detected from witnessed heads alone (test: rewind a test
   hub's ledger; the peer's next witness cycle flags head regression); a witnessed head discloses no
   member data.
4. **R4**: create role → confer occupant → rotate occupant; the role tensor persists across rotation;
   a role acts only within its charter (gate-refused otherwise); the founding seven pass the same
   tests on the new substrate.
5. **R5**: promote a role to a sub-hub; the child serves tier-0 sovereign identity of its own; the
   parent's edge shows role-scoped delegation; revocation reclaims the role with tensor intact.
6. **R6**: amend one side's law → the other side's alignment record flips the affected section within
   one witness cycle, as a witnessed entry; nothing on either side's law changed by the sync itself;
   a divergence beyond a delegation charter's tolerance triggers the law-defined response and
   nothing more.
7. **R7a**: kill the hestia callback (and separately, a federation peer) mid-session → every failure
   lands as a recorded degraded event, distinguishable from conduct denies; **zero** conduct-class
   reputation deltas are emitted from the window; the seam-opening test replays the queued deltas and
   proves the classifier separates the classes.
8. **R7b**: a self-asserted identity (and a self-asserted *society*) accumulates zero peer factors in
   admission scoring — differential test against the resolved-identity twin.
9. **R7c**: the operator surface shows per-seat ratified-vs-running digest; staging an unratified
   binary at the exec path flips the seat to `stale` without a restart being needed to notice;
   a write to the deploy closure from a gated session is refused and escalatable.
10. **R7d**: measured idle timeout rate per caller ≈ equal ≈ 0 across the fleet against hub
    endpoints; the pair-audit runs on a named cadence with a named owner.

## 7. Non-goals

- No shared/global law, ever (R6 exists precisely to avoid it).
- No hub writing another hub's state; no "sync" that mutates.
- No new federation protocol layer beside the membrane; no blockchain beyond the witnessed
  hash-chained ledgers already in the architecture (R3 is witnessing, not consensus mining).
- No central registry of hubs. Discovery of *societies* follows the same consent pattern as
  discovery of members.
