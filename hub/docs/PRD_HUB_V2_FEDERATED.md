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

Numbered R1–R10. R1–R6 are dp's directive (2026-08-12 verbatim intent, sharpened); R7 is the ratified
hestia-transfer set; R8 is the proving use case; **R9 and R10 were added 2026-08-18** — the two
capabilities the AIC Portland pitch requires that this PRD did not previously ask for.

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
  means independent ledgers can establish cryptographically witnessed **causal anchors** between
  their histories without either containing the other. A witness establishes what one hub had
  observed of another at a particular local ledger point; timestamps are evidence, not a global
  consensus clock or an implied total ordering across societies.

### R4. New roles as entities

Roles become first-class, creatable at runtime — today's seven are the founding set, not the type.

- A role is an **entity**: it has an LCT, a charter (the policy-action set it may perform — which is
  exactly the hub-law gate's vocabulary already), and a persistent institutional history/tensor.
  Occupant merit remains attributed to occupant-scoped sub-dimensions; it is not inherited by the
  next filler merely because that entity occupies the same role.
- **Creating a role is a witnessed governed act** (law-gated, quorum per law); **filling** a role is
  conferral (17A pattern: quorum of witnesses, backing attestations recorded).
- Per the ratified merit ruling: the role's tensor persists across occupants; the occupant is a
  sub-dimension ("when filled by X") under temperament. Rotation never resets the role's record and
  never transfers one occupant's attributed merit to another.
- The seven founding roles migrate onto this substrate (they become role-entities with founding
  charters) rather than remaining a parallel hard-coded system — one mechanism, no legacy fork.

### R5. Roles promotable into fractal sub-hubs

Some roles outgrow a single occupant: a committee, a working group, an events team. A role-entity can
be **promoted into a sub-hub relationship**: promotion creates a new sovereign child-society entity
with its own society LCT and charter derived from the role's charter, then witnesses a binding by
which that child society fills the persistent parent role. The role does **not** change ontological
type or become the society.

- The promotion is a witnessed governed act in the parent (quorum per law) plus an ignition of the
  child (its own sovereign act — the child is born sovereign, not owned). The parent role LCT and
  child society LCT remain distinct identities throughout their lifetimes.
- The parent–child relationship is an ordinary **federation edge (R1) with a role-scoped delegation
  (R2 semantics)**: the child fills, for the parent, exactly the role from which it was promoted.
  Fractal recursion falls out: same binary, same law machinery, same conferral discipline at every
  scale, without entity-type mutation.
- Demotion/dissolution: the edge is revocable from either side; the parent revoking the delegation
  reclaims the role (the role-entity persists — R4 — with its tensor intact); the child dissolving
  returns a terminal witnessed entry. A later child society may fill the same persistent role without
  inheriting the prior child's identity.

### R6. Law-sync for related hubs = an edge-scoped compatibility ledger, not shared law

Related hubs (parent/child, member/greater) do **not** share law and never auto-sync it.

- Each hub already publishes a witnessed law-amendment history (law digest at each head). Federation
  peers exchange law heads as part of R3 witnessing.
- Each side maintains a **compatibility record per federation/delegation edge**, evaluated only over
  the law surface relevant to that edge's charter and permitted flows — the relationship's MRH. The
  record is therefore contextual, not a claim that two sovereign laws are globally "aligned." A
  useful v0 state is `compatible | incompatible | unknown | irrelevant`, with section-level evidence
  as the cheap baseline and rule-level evidence where the edge charter requires precision. The
  record is recomputed whenever either law head advances and witnessed when its state changes.
- **Incompatibility is a fact to surface, not an error to fix.** A difference outside the edge MRH is
  `irrelevant`; an incompatibility inside the delegated surface triggers law-defined responses — flag
  on the operator surface, escalate, suspend that delegated surface — but never an overwrite of
  anyone's law. Raw digest difference is evidence that evaluation must be refreshed, not by itself
  proof of semantic disagreement. (This is the fail-closed+warn default doing federation work:
  unresolved compatibility defaults to flag-and-continue for peers, deny-delegated-surface for
  chartered relationships, both law-overridable.)

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

### R8. The proving use case — AIC Portland: split without fragmenting

**Sharpened 2026-08-18** after dp met the AI Collective Portland chapter. The pilot now has a
governing question, a scale, and a working draft (*"Scaling Without Fragmenting"*), which turns R8
from a mapping table into a deliverable list. The mapping below is unchanged where it held; what is
new is the **question the pilot must answer** and the **two capabilities it needs that this PRD did
not previously require**.

**The governing question, verbatim from the chapter:**

> How does Portland split without fragmenting?

**Scale and constraints.** ~4,500 members, volunteer-led. Leadership attention is the scarce
resource; administrative overhead competes directly with community work. Splitting risks silos;
choosing one organizing axis (geography / interest / project / cause) too early may lock in the wrong
structure for years.

**The load-bearing design constraint this adds to R4/R5.** Communities, working groups, projects and
events **MUST NOT** be four unrelated features. They differ in lifespan and purpose, not in kind —
each is a context with membership, governance, relationships and a lifecycle. That is exactly the
(role-entity | child-society) substrate R4 and R5 already specify, and stating it here makes it a
requirement rather than an implementation preference. A fifth group shape must cost approximately
nothing to add.

| AIC operational need | Hub mechanism |
|---|---|
| Stand up a chapter | `hub init` — society + founding charter + role defaults |
| Onboard a member, verifiably | Admission queue + witnessed conferral with vouching basis (17A/17B) |
| Officers / responsibilities | Role-entities (R4): chartered, conferrable, rotating without history loss |
| Communities / working groups / projects / events | **One primitive** — role-entity or child society, differing only in lifecycle (R4 + R5) |
| Bylaws that are actually enforced | Hub law: inspectable, machine-enforced at the gate, amendable by due process, every amendment witnessed |
| Meeting / decision record | The witnessed ledger — append-only, tamper-evident, exportable |
| Contribution that travels | Reputation per (entity, role), portable across chapters via federation edges (R1) |
| "Who knows X?" | Semantic member discovery (**R9**) — the chapter's stated need is meaning, not keywords |
| Getting two members talking | Consent-based introduction (**R10**) |
| National ↔ chapters without capture | Greater hub chartered for a narrow role (R2) + edge-scoped law compatibility (R6) |
| Chapter splits / working groups | Persistent role + newly ignited child society bound through a federation edge (R5) |
| Trust in the record itself | Fractal ledger witnessing (R3) |

**Pain points CONFIRMED (dp, 2026-08-12; re-confirmed and extended 2026-08-18)**: organizer time,
non-portable reputation, invisible cross-chapter discovery, governance opacity — plus **premature
axis lock-in**, which is the new one and the reason the pilot's first phase is modelling rather than
building. Governing frame unchanged: a **nonprofit, volunteer-run** org, so governance must be
**frictionless but well organized, and above all transparent/accountable**.

#### R8.1 The burden criterion — measured, not asserted

The chapter's own success test is *"the desired outcome is less administration."* Every other
criterion in §6 is a differential test on mechanism; this one is about humans, and it is the one the
pilot is actually judged on. It therefore needs a **baseline taken before anything is built**:

- time and manual steps to stand up a new working group **today**;
- manual steps per admission **today**;
- who currently performs each, and how long the queue is.

Without that baseline "less administration" is unfalsifiable — the failure mode this PRD keeps
naming in other contexts, applied to its own proving use case.

#### R8.2 Exit is a requirement, not a courtesy

The chapter states as success that *"relationships can leave the platform without penalty"* and that
another chapter can adopt the model *without Portland becoming its central administrator*. So
**portability is a requirement**: the ledger, the member graph and a member's own context must be
exportable in an open format, and a member or group leaving must not forfeit their record. A system a
volunteer organization cannot leave is one it should not adopt.

### R9. Member context and semantic discovery

Members are more than profile keywords. Over time a member-controlled contextual profile accumulates
interests, skills, experience, current projects, questions, causes, capabilities, and needs — and
discovery operates over **meaning**, so that a member can ask *"who here has experience with
distributed AI systems and might enjoy thinking about decentralized governance?"* rather than
`Python + Portland + ML engineer`.

- **Member-controlled.** The subject decides what enters their context and can inspect, correct and
  withdraw it. Context accrues **only** with the member's knowledge — a profile silently assembled
  from observed behaviour is a different product and is out of scope.
- **Bounded results.** A small number of candidates, never a ranked feed. The absence of an infinite
  result set is a design requirement, not a limitation to be lifted later.
- **Least disclosure at match time.** A match **MUST NOT** reveal what it matched on. The system may
  know two members are relevant to one another without exposing either's context to the other — this
  is `PRD_AGENT_CONTEXT_ACCESS.md` §6.2's rule (*derived information counts as disclosure*) applied
  to discovery, and it is what keeps semantic search from becoming an inference channel.
- **Not a ranking of people.** Discovery surfaces relevance, never a score, standing, or league
  table. A T3/V3 threshold gating who is discoverable would reproduce the `satisfied_by` inversion at
  the discovery grain — evidence in, verdict with the relying party.
- **Federated later, local first.** Cross-chapter discovery rides R1 and must satisfy both laws; the
  pilot's phase 3 is local-only.

### R10. Consent-based introduction

The protocol, in full: **Discovery → Introduction request → Consent → Private channel.** Being
findable is not being reachable.

- **Consent precedes contact.** Discovery grants no channel. The addressed member's decline is
  final, is **not** disclosed to the requester as a signal beyond "no", and is not published.
- **The channel already exists**: sealed member↔hub paired channels ship today; R10 is the
  authorization and consent flow in front of them, not a new transport.
- **Authorization model is not re-derived.** `PRD_AGENT_CONTEXT_ACCESS.md` (dp, 2026-08-14) holds it
  — citizenship as a floor and never sufficient, need-to-know narrowing, the receptionist surface for
  callers with no standing, `ConversationGrant`, revocation, and authorization-before-retrieval. R10
  **cites** that PRD; a second outward-authorization system would fork the model, which is the
  failure the role-scope bridge §9 exists to prevent.
- **Then get out of the way.** After the introduction the hub's job is done. Participants may
  continue in the channel or leave entirely, and **leaving must carry no penalty** (R8.2).
- **The metric is introductions, not engagement.** Time-on-platform is explicitly *not* a success
  measure. Any feature justified by attention rather than by a successful introduction is out of
  scope by construction.


## 3. Design questions needing dp rulings

1. **R3 — witnessing depth.** Ratify the layered recommendation (hash-witness always-on; checkpoints
   per-edge opt-in by law)? Or one mechanism only?
2. **R2 — first greater-hub charter.** Recommend the minimum: cross-society member discovery only.
   Ratify, or charter more at birth?
3. **R5 — promotion authority + identity.** Recommend: quorum conferral in the parent per parent law
   **plus** sovereign ignition of a distinct child-society entity (child born sovereign), with a
   witnessed role-filling binding between persistent role LCT and child society LCT. Ratify?
4. **R6 — compatibility scope/granularity.** Recommend edge/MRH-scoped compatibility, never global
   law alignment: section-level evidence as the cheap v0 baseline; rule-level evidence where a
   delegation charter demands it. Ratify?
5. **Sequencing** — endorse §5's phase order (in particular: R7a gates the reputation seam, and
   R4 lands before R2/R5 because both compose out of role-entities)?
6. **R1 split (new, 2026-08-18)** — ratify §5.1's recommendation to build the **local parent↔child
   edge** as a restriction of the R1 object, ahead of the peer edge, so R5 promotion can land at the
   pilot's phase 2 instead of waiting for full peer federation? The alternative is to keep this
   plan's order and tell Portland that subdivision waits on cross-organization federation it does not
   need until phase 5.
7. **R9/R10 scope (new, 2026-08-18)** — are member context, semantic discovery and consent-based
   introductions in scope for *this* PRD, or do they belong in a companion product PRD that cites it?
   They are requirements of the pitch either way; the question is whether the federated-hub document
   is where they live. Related: `PRD_AGENT_CONTEXT_ACCESS.md` already holds R10's authorization
   model and is itself awaiting review.

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
- **Phase 2 — R1 peer federation MVP** + R3 hash witnessing + R6 edge-scoped compatibility record v0.
  Two real hubs, two machines, witnessed edge, law heads exchanged, federated discovery behind both
  laws.
- **Phase 3 — R2 greater hub** (discovery charter) + R7d parity instrument reading federation calls.
- **Phase 4 — R5 promotion** (persistent role + distinct child society + witnessed role-filling edge),
  demotion/dissolution paths.
- **Phase 5 — R3 checkpoints** (if ruled in) for the edges whose law asks for them.
- **Throughout — R8**: validate each phase against a real AIC chapter workflow; the presentation
  artifact follows the pain-point confirmation, not the other way around.

### 5.1 Amendment (2026-08-18) — the pilot's proving order inverts this plan

The Portland pilot proves capabilities in the order **subdivision first, federation last**: model the
chapter and its proposed subdivisions (phase 1), perform one real subdivision (phase 2), then member
context and discovery (3), introductions (4), and only then invite another chapter to federate (5).

This plan sequences **R1 peer federation at Phase 2 and R5 promotion at Phase 4** — the opposite
order. The tension is real and is **not** resolved by simply swapping them, because R5's mechanism is
*"an ordinary federation edge (R1) with a role-scoped delegation"*: promotion needs an edge to exist.

**Recommended resolution — split R1 by trust domain, not by feature.** A **parent↔child edge inside
one operator's control** is a materially smaller problem than a peer edge between two sovereign hubs
on two machines under two organizations:

| | local (parent↔child) edge | peer edge |
|---|---|---|
| both endpoints | one operator, often one host | two organizations, two machines |
| law compatibility (R6) | parent charter derives the child's | two independently amended laws |
| identity resolution (R7b) | child ignited by the parent's operator | must resolve an asserted society |
| transport | same membrane, may be loopback | network, availability, revocation latency |

Building the local subset first delivers **R5 without R1's hard half**, which is what the pilot needs
in its phase 2, and leaves the peer edge to be built when the pilot actually reaches phase 5. The
risk to name: a local edge that quietly assumes shared operator control is not a federation edge, and
if the two diverge, phase 5 pays. The subset must therefore be a **restriction** of the R1 object —
same consent, same witnessing, same revocation — never a parallel one.

**Also newly sequenced**: R9 (member context + discovery) and R10 (introductions) land at pilot
phases 3 and 4, after the governance model has proved itself. Neither should start before R8.1's
baseline exists, or the burden claim they are partly justified by cannot be evaluated.

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
   member data; exchanged head witnesses establish reproducible causal anchors without requiring or
   claiming a global total order across the two ledgers.
4. **R4**: create role → confer occupant → rotate occupant; the role tensor persists across rotation;
   occupant-attributed merit remains distinguishable and does not transfer to the next occupant; a
   role acts only within its charter (gate-refused otherwise); the founding seven pass the same tests
   on the new substrate.
5. **R5**: promote a role relationship to a sub-hub; the persistent role LCT and newly ignited child
   society LCT are distinct; the child serves tier-0 sovereign identity of its own; the parent's edge
   shows role-scoped delegation; revocation reclaims the role with tensor intact; a replacement child
   can later fill the same role without inheriting the prior child's identity.
6. **R6**: amend one side's law inside the edge MRH → the other side's compatibility record changes
   within one witness cycle, as a witnessed entry; amend law outside the edge MRH → the edge records
   the difference as irrelevant (or leaves compatibility unchanged); nothing on either side's law is
   changed by the comparison itself; an incompatibility beyond a delegation charter's tolerance
   triggers the law-defined response and nothing more.
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
11. **R8.1 (burden)**: a baseline of time and manual steps — stand up a working group, process an
    admission — is recorded **before** the pilot builds anything, and the same measurement after
    phase 2 shows a reduction. A pilot that passes every mechanism criterion and fails this one has
    failed; that is the point of stating it as a criterion rather than a hope.
12. **R8.2 (exit)**: a member and a group can each export their record in an open format and leave;
    the export verifies against the ledger after removal, and nothing in the remaining record
    silently degrades. Differential: a chapter that adopts the model can be administered entirely by
    its own operator, with the originating chapter's access revoked and no capability lost.
13. **R9**: a member's context is inspectable, correctable and withdrawable by that member; a
    discovery query returns a bounded candidate set; and a **match discloses nothing about what it
    matched on** — differential: two members with materially different contexts that both match a
    query yield candidate entries indistinguishable to the requester.
14. **R10**: a declined introduction produces no channel, no retry-with-more-information affordance,
    and no disclosure beyond the decline itself; an accepted one produces a channel neither party
    needs the hub to keep using. Differential: after acceptance, both parties leave the hub entirely
    and the relationship is unaffected.

## 7. Non-goals

- No shared/global law, ever (R6 exists precisely to avoid it).
- No hub writing another hub's state; no "sync" that mutates.
- No new federation protocol layer beside the membrane; no blockchain beyond the witnessed
  hash-chained ledgers already in the architecture (R3 is witnessing, not consensus mining).
- No central registry of hubs. Discovery of *societies* follows the same consent pattern as
  discovery of members.