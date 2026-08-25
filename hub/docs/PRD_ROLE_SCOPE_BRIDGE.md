# PRD — the role-scope bridge (hub side): work scope delegated to roles, enforced by hestia

**Status**: proposed — dp-directed 2026-08-14; design PRD, not started; bridges hub<->hestia; builds
on #431's standing-scope surface (hestia PR). **Amended 2026-08-18** to absorb dp's two rulings of
2026-08-14, which landed on the twin and never reached this side: §6's open questions become
EXTENSION POINTS, and §9 adds the outward direction. See §11 for the correspondence table and for
why a PR-thread watcher could not have seen those rulings.
**Author**: claude-code (CBP), 2026-08-14.
**Twin**: `hestia/docs/PRD_ROLE_SCOPE_BRIDGE.md` — the enforcement side of the same bridge, **merged
to `hestia` main 2026-08-15** (dp-web4/hestia#433). Each side details only its own mechanics. The
CONCEPTS section has a single **normative home — twin §2** — which this document summarizes
non-normatively and cites by `concepts_generation` (§2); it is not mirrored here, and is not amended
here. Currency is checked by comparing that generation, and everything else that is genuinely shared
is verified **against the twin's git history, not against its PR thread** (§11).
**Relates to**: `PRD_HUB_V2_FEDERATED.md` R4 (roles as entities — the role scope manifest extends the
R4 charter), R7b (asserted-asker law), R1/R2 (cross-hub occupancy, deferred), `ROLES.md`, `HUB-LAW.md`,
`hestia/docs/PRD_GATE_CONSOLIDATION.md` (one authority path), web4's RWOA+S+V accountability norm
Also `hestia/docs/PRD_ADJUDICATOR_LADDER.md` (who decides — §8), `hestia/docs/PRD_R6_R7_ENVELOPES.md`
(the carrier — §10), `PRD_ALLOWLISTS.md` (the shared `kind` vocabulary and union-only composition).

---

## 0. Directive (dp, 2026-08-14, verbatim)

> hub-delegated work scope to role, and role-delegated to hestia, while in role. the general intent
> is to be able to have a hub member fill a role (once approved) and gain the necessary
> scope/permissions for the role. member approval would have to grant a class of permissions (like a
> security clearance or a signing authority). then role-specific detailed scope would flow to the
> member, as long as all of it is in classes the member is approved for. this should go into prds
> for both hub and hestia, since it's a bridge between the two. some classes of scope might require
> higher hestia constellation proof (i.e. some acts need multifactor proof from the member).

## 1. What the hub gains

R4 makes roles first-class: chartered, conferrable, rotating without history loss. But an R4 charter
speaks hub-law vocabulary — which *policy actions* the role may perform inside the hub. It says
nothing about the occupant's **working reach** on its own machine: repos, secrets, egress, deploy.
This PRD extends the role charter with a **scope manifest** so that filling a role carries the
role's working scope with it — delivered to, and enforced by, the occupant's hestia constellation,
bounded by a member-level clearance the occupant's operator approved. The hub becomes able to say
"the release-manager role needs these clearances and confers this reach, for whoever fills it,
while they fill it" — and rotation, revocation, and charter amendment all take working scope with
them automatically.

## 2. Concepts — NON-NORMATIVE SUMMARY (normative home: twin §2, `concepts_generation: 2`)

**The normative text is `hestia/docs/PRD_ROLE_SCOPE_BRIDGE.md` §2.** This section is a reading aid so
the hub side is legible standalone; it is *not* a mirror and must not be amended as though it were.
Where this summary and the home differ in substance, **the home governs and this text is the defect**.

**Checking currency** (replaces the diff-based rule this document's §11 previously stated): compare
the `concepts_generation` cited above against the home's. The comparison has **three** outcomes, and
the third is the one a two-state check loses:

| home's generation | verdict |
|---|---|
| equal to the citation above | **CURRENT** |
| greater than the citation | **STALE** — this summary predates an amendment; re-point it |
| **absent or unreadable** | **UNDETERMINED** — *not* current |

The third row is load-bearing (GPT review, 2026-08-20). If the home is renamed, moved, or loses its
marker, the grep that implements this check returns nothing — and nothing, compared against an
integer, is not less-than. A two-state reading therefore reports a missing home as *not stale*, which
is the absence-reads-as-OK shape this PRD family keeps finding in its own instruments. UNDETERMINED
is fail-closed by construction: it is a finding to be resolved, never a pass. Amend the home, bump
there, then re-point here.

**This is executed, not merely stated** (added 2026-08-21). The rule lived in prose from 2026-08-18
with nothing running it — `grep -rl concepts_generation .github/` returned zero files, measured
independently by two seats. The gate is now `.github/workflows/concepts-generation.yml`, running
`hub/tools/check_concepts_generation.py` (stdlib-only; fetches the home over raw HTTPS, since
`dp-web4/hestia` is public). It runs on the hub-side path filter **and on a daily schedule** — the
schedule is the load-bearing trigger, because the home is in another repository and a bump there
touches no web4 path, so a PR-only gate could never reach the STALE arm at all.

**What this summary deliberately omits**, so no reader mistakes it for complete:

- the **T0/T1/T2 proof-tier table** — which evidence each tier demands at act time, and which classes
  sit at each. This document names `T2` in §6.3 and reasons about T1/T2 in §10 **using definitions
  that exist only in the home**;
- the invariant that **a high-tier grant at rest confers nothing** — holding a T2 item means the gate
  will *entertain* the act and demand the second factor then and there. Multifactor is per-act
  evidence, never a property of the grant;
- that the flow rule is **evaluated per-item at delivery and re-checked at act time**, not once;
- the illustrative class spellings, and the withheld-and-disclosed detail.

The first two are load-bearing for anyone implementing the hub's half: the hub records the tier an
item demands (§3.1) without deciding what discharges it, and an implementer reading only this
document would find no definition of what it is recording.

---

- **Permission CLASS**: a named capability category a member holds by **operator** approval on the
  hestia side — the clearance / signing-authority analog. Classes are the unit of human judgment.
- **ROLE SCOPE MANIFEST**: the role charter's new section — required classes + detailed scope
  items, **each item tagged with exactly one class**, plus a monotonic **manifest generation**
  bumped on every amendment.
- **OCCUPANCY**: the witnessed, time-bounded fact that a member fills a role (17A conferral:
  quorum, backing attestations), with an `occupancy_id`, start, and end.
- **THE FLOW RULE** (enforced hestia-side): items flow to the occupant iff every item's class is in
  the member's approved class set. A role can never launder scope past a member's clearance;
  a clearance confers nothing without a role. Scope = intersection, never union.
- **PROOF TIERS**: classes map to assurance tiers; high tiers require hestia-constellation
  multifactor proof **at act time** (operator co-sign, witness quorum, hardware-backed key), per
  the evidence-scaled-to-stakes doctrine. The hub records the tier; hestia demands the proof.
- **ROLE SKILLS** (dp, 2026-08-21; generation 2): a role confers capability as well as reach — the
  skills its occupant should have loaded while filling it. Manifest items like any other, **each
  tagged with exactly one class**, so the flow rule governs them unchanged: a role may name a skill
  the occupant is not cleared for and the occupant does not receive it (withheld and disclosed).
  Rotation carries them out; amendment re-passes them. The hub's half is the same as for paths —
  declare and tag them in the charter; hestia decides who receives them.
- **ROLE MEMBOTS** (dp, 2026-08-21; generation 2): *speculative, and the home keeps it that way.* A
  role might also confer a memory cartridge. Strictly larger than skills, because a membot is
  retrieval whose returns are not fixed at conferral, so what reaches the occupant can change
  without re-passing the flow rule. Carried as an extension point in the home, not a decided
  concept. **Do not build against this.**

## 3. Mechanics — the hub side

Ownership split, stated once: **the hub owns role definitions and occupancy approval** (this
document); **hestia owns enforcement** — clearances, the flow rule, materialized grants, act-time
proof (the twin). The hub's outputs are *evidence*, never authority: nothing the hub emits causes
local reach except through the occupant's own daemon verifying it against operator-approved
clearances. No hub ever writes another party's state — the standing invariant applies to member
machines exactly as to peer hubs.

### 3.1 The manifest is charter, amended as charter

The scope manifest lives inside the R4 role-entity's charter and is amended only by the hub's
law-gated governed process (quorum per law, witnessed). Every amendment bumps `manifest_generation`
and is a witnessed ledger entry carrying the item diff. Consequence (designed, load-bearing): an
amendment **strands** every grant materialized under the old generation on every occupant's
constellation — a role cannot widen its occupants silently; new items re-pass each occupant's flow
rule on re-ingestion. Declaring an item's class is a governed choice with teeth: the class decides
which members can receive the item and what proof spending it demands.

### 3.2 Occupancy — conferral, expiry, revocation

Filling a role is the existing 17A conferral, extended with: an explicit **term** (`expires_at` —
occupancies are time-bounded by default; indefinite requires law to say so), the manifest
generation in force at conferral, and a machine-consumable **occupancy attestation** (§3.3).
Ending an occupancy — expiry, revocation (law-gated), or rotation — is witnessed, and the
attestation stops being served/verifying, which is what actually retracts the scope downstream
(structural, not remembered). Occupant merit attribution is unchanged from R4: the role's tensor
persists; occupancy scope is *reach*, never inherited merit.

### 3.3 The attestation surface — pull, not push

The hub serves, over the existing membrane (MCP / signed REST), a per-member occupancy attestation:

```
{ occupancy_id, member_lct, role_lct,
  manifest: { items: [{item, class, proof_tier}], generation },
  conferral: { witnesses, basis },
  granted_at, expires_at,
  hub_signature over the lot }
```

The occupant's hestia daemon **pulls** this (the hub pushes nothing), verifies the signature
against the hub identity its operator paired with, and applies the flow rule locally. R7b applies
unchanged: an attestation is only as good as the resolved, paired identity that signed it — a
self-asserted hub collects nothing. The attestation is served only to the subject member's paired
channel and the operator surface (least disclosure; the manifest may name sensitive paths).

### 3.4 Revocation propagation

The hub's job on every ending is to make the ending *visible fast*: occupancy end and manifest
amendment are witnessed immediately, the attestation surface reflects them on next pull, and the
existing federation witness cadence (R3 heads) gives the constellation a freshness signal. The hub
does not — cannot — reach into a member machine to delete grants; the twin's generation-stranding
does the actual retraction within one snapshot horizon. Acceptance is measured end-to-end (§5 criterion 3, the single-horizon test of §8.1).

## 4. Accountability self-audit (RWOA+S+V) — design-time, hub surfaces

```
surface: role manifest amendment   act: change what a role confers on every occupant (amend law/policy class)
S: high/reversible (re-amend; generation strands old grants) [construct: charter amendment, law-gated, §3.1]
R: pass [construct: production_law_gate — one authority path]   W: pass [construct: quorum per law, witnessed ledger entry with item diff]
O: pass [construct: gate before ledger write; generation bump atomic with amendment]   A: pass [construct: witnessed entry carries diff + generation + quorum basis]
V: present [construct: law-defined quorum refusal; operator surface review]
verdict: PASS (design)

surface: occupancy conferral / revocation   act: assign role (a named consequential act)
S: high/reversible [construct: 17A conferral + witnessed ending, §3.2]
R: pass [construct: law gate]   W: pass [construct: quorum of witnesses + backing attestations + resolved identity (R7b)]
O: pass [construct: conferral gated before attestation exists]   A: pass [construct: conferral entry carries basis, term, manifest generation]
V: present [construct: revocation verb; term expiry default]
verdict: PASS (design)

surface: occupancy attestation serving   act: none directly (evidence emission; reach is caused only downstream, behind the occupant operator's clearances)
S: med/reversible (disclosure of manifest contents) [construct: subject-member + operator channels only, §3.3]
R: pass [construct: paired-channel scoping]   W: pass [construct: hub signature binds content; consumer verifies]
O: n/a (read)   A: pass [construct: attestation derives from witnessed conferral entries]
V: n/a
verdict: PASS (design)
```

## 5. Falsifiable acceptance criteria (hub side; end-to-end criteria live in the twin)

1. Conferral of a role with a manifest produces a verifiable attestation; rotation produces a new
   `occupancy_id` and kills the old attestation; the role tensor persists across rotation (R4
   criteria unchanged).
2. A manifest amendment is witnessed with its item diff and bumps the generation; an attestation
   served after amendment carries only the new generation.
3. **End-to-end retraction**: occupancy revocation on the hub strands the occupant's role-derived
   reach within **one** snapshot horizon — the single horizon of §8.1, evaluated over the union of
   all contributing authorities, not a hub-local TTL — measured on a live constellation (joint test
   with the twin's criterion 3). This criterion is where §8.1's "exactly one horizon" is proved;
   it is unmeasurable if either side mints its own.
4. A self-asserted (unpaired) hub's attestation confers zero reach on a constellation (R7b
   differential, joint with the twin's criterion 4).
5. Attestations are served only to the subject member and operator surfaces (differential fetch as
   a third member fails).

## 6. Open questions — and, since 2026-08-14, EXTENSION POINTS

**dp declined to rule on these. The directive, verbatim:**

> "all of these things we're going to have to take a best guess at and evolve as we go. the key is
> to have mechanisms for the evolution, not hardcode things. and remember, the policy entity AGENT
> is still intended to slot in between heuristic slot and human, as a middle escalation layer. and
> even that can be a neural net, and THEN an agent. your own 'auto mode' in claude-code already
> implements this. so rather than rule on these, i want to add hooks for planned infrastructure.
> ultimately, a competent agent will be a far more effective reviewer than a human - always there,
> much faster, able to actually look at the full context, consult the actual law. that is the goal."

The four questions this document shares with the twin are **converted, not answered and not
deleted**, in the same shape and to the same dispositions as `hestia/docs/PRD_ROLE_SCOPE_BRIDGE.md`
§7.1–§7.4 — each states the initial best guess, where the value lives, who may change it, what
measurement would justify a change, and the eventual per-case decider. Only the hub's half is
detailed here; the twin holds the enforcement half of the same row, and the two must be amended
together (§11).

§6.5 is **hub-only** — the twin has no counterpart, so dp's ruling does not reach it directly. It is
converted under the same directive rather than left RED, and §6.6 says what that costs.

### 6.1 Class taxonomy governance → EXTENSION POINT

*Who defines the class vocabulary and tier mapping — hub law, hestia operator law, or a shared
ratified list? A class the two sides spell differently is a flow-rule bypass or a permanent withhold.*

| | |
|---|---|
| **initial best guess** | **the hub is authoritative for what a ROLE REQUIRES; hestia operator law is authoritative for what a LOCAL MEMBER is cleared for.** Neither can spell the other's half. The hub's obligation is the tagging half of §3.1: every manifest item carries exactly one class, and the class is a governed choice made at charter-amendment quorum. A manifest naming a class a constellation does not know is **withheld and disclosed** by that constellation, never silently absorbed — which is §2's flow rule applied to an unknown spelling rather than to a missing clearance. Fail-closed, and it needs no ruling to ship. |
| **where the value lives** | one taxonomy document. The hub's copy is law-owned (amended by the same law-gated process as any charter section) and **generation-covered by the composite of §8.1** — it is not a free-standing list with its own version. Per `PRD_ALLOWLISTS.md` §12's shared-key argument it uses the **same `kind` vocabulary** that the ceremony table and the adjudicator ladder's route table resolve on. Three vocabularies for "what kind of act is this" would drift with no surface on which to notice. |
| **who can change it** | hub-side: law, at the ceremony tier `required_tier` returns for the taxonomy's own `kind`. Cross-hub and hub↔constellation compatibility is a **mapping someone writes** (hub class ⇒ local class), never an implicit string match — a string match is the flow-rule bypass this question is about. The hub never writes a constellation's half of that mapping (§3, ownership split). |
| **what would justify a change** | the withheld-item log, joined on the class that was unknown. The hub sees only the (optional) fact that an item was withheld, never why (§7) — so the hub's half of this measurement is **withheld-count per class per manifest**, which is enough to distinguish "a class we tag that nobody can consume" from "a class one constellation has not been cleared for." An empty log means the taxonomy is adequate. |
| **eventual decider, per-case** | the ladder. *"This manifest names `deploy:staging`; the taxonomy has `deploy` — same class?"* is a judgment about two documents, and a rung reading both is better placed than a static equality test. **Named failure mode**: a rung that resolves spellings LIBERALLY is a flow-rule bypass with a faster clock, so this route should stay advisory a long time. |

### 6.2 Cross-hub occupancy → EXTENSION POINT

*A role conferred over an R1/R2 federation edge: does a constellation consume it at all, and if so
does it demand edge-scoped law compatibility (federated-PRD R6) plus a higher tier?*

| | |
|---|---|
| **initial best guess** | **out of v0 — local-hub occupancies only.** Unchanged from the original recommendation; what changes is that "out of v0" becomes a **stored value** rather than an absence of code, on both sides. |
| **where the value lives** | consumer-side, an `accepted_occupancy_sources` list (the twin's §7.2) — initially the paired local hub's identity and nothing else. **The hub's half is that its attestation must be self-describing enough to be judged against such a list**: §3.3's attestation already binds `role_lct`, the conferring hub's signature, and R7b's resolved-identity requirement, which is exactly the tuple a source list is keyed on. An occupancy from an unlisted source is withheld and disclosed — so the v0 restriction produces a record rather than silence. |
| **who can change it** | the consuming operator, by admitting a hub identity. The **proof-tier floor** for federated occupancies is a second stored value defaulting to +1 tier: admitting a federated hub does not simultaneously decide how much it is trusted. Two values, because they are two decisions. The hub cannot set either — it emits evidence, never authority. |
| **what would justify a change** | a federated occupancy actually being needed — a non-empty withheld-by-source log. Today that log would be empty, which is the honest reason this is out of v0: not that it is wrong, but that nobody has asked. |
| **eventual decider, per-case** | the ladder, and this is the strongest per-case case in the section: edge-scoped law compatibility (federated-PRD R6) is a comparison of two hash-pinned law documents. A rung can fetch both, diff them, and state which norms conflict — exactly dp's *"a human skims"* case. |

### 6.3 The agent second factor (tier T2) → EXTENSION POINT, and an AGENT RUNG IS A CANDIDATE

*What is a second factor for an agent member? The hub's stake is narrow but real: `proof_tier`
labels on manifest items must mean something, or the tier column is decoration.*

Ruled on the hestia side — twin §7.3 is normative and is **not** restated here; it enumerates the
four conditions an agent rung must satisfy (computed independence via `arbiter::eligibility_for`, a
genuinely different failure domain, not the same process wearing k hats, and a **non-zero dissent
rate**). The hub's half:

| | |
|---|---|
| **initial best guess** | **operator co-sign remains the only thing that satisfies T2 today.** Unchanged. An agent rung may be *recorded* as an additional factor from day one (advisory) while satisfying T2 alone remains reserved. |
| **where the value lives** | **not on the hub.** The class→tier map's *satisfying factor kinds* are the consuming constellation's stored value (twin §7.3). The hub stores the tier a manifest item demands and nothing about what discharges it — a hub that stored "an agent rung satisfies T2" would be writing another party's trust model, which §3 forbids. |
| **who can change it** | the occupant's operator, permanently. `PRD_ALLOWLISTS.md` §3.6.3's asymmetry applies on that side: widening what satisfies a tier pays the tier being widened FROM. |
| **what would justify a change** | the stage-A record: per-class agreement rate with the operator's co-sign **and a non-zero dissent rate**. Agreement alone is satisfied by a rung that always says yes. |
| **eventual decider** | **not the ladder — the operator's, permanently.** `PRD_ADJUDICATOR_LADDER.md` §5.3 forbids a rung from adjudicating changes to its own authority; this is that rule one layer out. §9.4 is the same rule applied to `role.manifest.*` on this side. |

### 6.4 T3 / reputation interaction → EXTENSION POINT

*Should conferral eligibility or clearance asks consume T3 evidence (e.g. a temperament threshold in
the role's context), or is reputation only advisory?*

| | |
|---|---|
| **initial best guess** | **advisory. Surface T3 beside the decision; never auto-decide.** Unchanged, and not a compromise — it is Web4 doctrine: *produce checkable evidence and let the caller decide; do not smuggle in an exclude/admit verdict.* A T3 threshold gating conferral would be the `satisfied_by` inversion reproduced at the occupancy grain. |
| **where the value lives** | a per-class `reputation_display` config — which T3 axes are shown beside a conferral ask, and any **advisory** band. Displayed, never evaluated as a precondition. The hub's half is the conferral surface (§3.2), where the quorum sees the evidence. |
| **who can change it** | law, for the hub's display config. Note what is deliberately **not** offered: no stored value turns the advisory band into a gate. Adding one is a change to the trust model, not a config edit, and belongs in a PR that argues for it. |
| **what would justify a change** | nothing measurable at this grain — the honest answer, and why this is the one extension point whose mechanism is deliberately incomplete. If a case for gating arrives it will arrive as an argument, not as a number. |
| **eventual decider, per-case** | the ladder, in exactly the shape doctrine permits: a rung **reads** T3 as part of its evidence bundle and cites it. Evidence-in, verdict-with-the-relying-party. A rung that *thresholded* on T3 would commit the inversion law is forbidden from committing. |

### 6.5 Manifest item vocabulary → EXTENSION POINT (hub-only; converted here, not ruled)

*Items name constellation-local things — repos, paths, egress, deploy targets. Does the hub validate
item shape at all, or treat items as opaque strings the constellation interprets?*

The twin has no counterpart to this question: it is the hub's alone, because the hub is the side
that stores and quorum-reviews manifest diffs. dp's 2026-08-14 directive did not reach it. It is
converted under that directive's *form* rather than left RED, and §6.6 records that this is a
weaker warrant than §6.1–§6.4 carry.

| | |
|---|---|
| **initial best guess** | **opaque-with-schema.** Typed item *kinds* (drawn from the same `kind` vocabulary as §6.1 — a fourth spelling here would be the drift §6.1 exists to prevent), with **uninterpreted values**. Hub law can quorum-review a diff — *"this amendment adds two `egress` items and one `deploy` item at tier T2"* — without pretending to know a member's filesystem. Validation is well-formedness only: exactly one class, a known kind, a non-empty value. |
| **where the value lives** | the kind vocabulary is the §6.1 taxonomy document (one list, not two). Whether a given kind's values are constrained at all is a per-kind stored flag, defaulting to **unconstrained**. |
| **who can change it** | law, at the taxonomy's own ceremony tier — the same gate as §6.1, deliberately, so a kind cannot be added by a cheaper route than a class. |
| **what would justify a change** | the amendment-review record: manifest amendments where the reviewing quorum could not judge the diff, joined on item kind. A kind that repeatedly produces *"we cannot tell what this grants"* is a kind that wants a schema. An empty record means opacity is costing nothing. **This is a measurement the hub can actually take** — it is the one surface where the hub sees the whole item, since §7 keeps the hub ignorant of downstream withholding reasons. |
| **eventual decider, per-case** | law, not the ladder. A rung may advise on whether a diff is judgeable, but "what may a manifest express" is a statement about the hub's own governed vocabulary, and §9.4's refusal set covers `role.manifest.*` for exactly this reason. |

### 6.6 What was NOT ruled, and why that is recorded here

**An extension point with no measurement attached is an open question wearing a design's clothes**
(twin §7.6). Each of §6.1–§6.5 names the measurement that would move it; none says "further review."

Two warrants are deliberately distinguished, because collapsing them would launder a track's
judgment into an operator ruling:

- **§6.1–§6.4 are dp-ruled** (2026-08-14, directive above), converted to match the twin.
- **§6.5 is track-converted** under that directive's form. dp has not seen this question. It is
  flagged rather than silently promoted, and it is the one row in this section an operator review
  should read first.

The twin's §7.5 (withheld-item ergonomics — whether a `role_scope_withheld` witness auto-opens a
clearance ask) is **deliberately still a question** and is enforcement-side. The hub's stake is only
that it emits nothing that would force the answer: §3.3 is pull-only and §7's no-push non-goal is
what keeps that choice the constellation's.

## 7. Non-goals

- No hub-side enforcement of local scope, and no push channel into member machines — the hub emits
  witnessed evidence; enforcement is the constellation's (one authority path, per side).
- No clearance store on the hub: clearances are the occupant operator's judgment and live in the
  occupant's vault. The hub never learns *why* an item was withheld, only (optionally) that it was.
- No new transport; attestations ride the membrane.
- No change to R4 merit/tensor semantics — occupancy scope is reach, not merit.

## 8. Adjudicator ladder — cross-reference

**See `hestia/docs/PRD_ADJUDICATOR_LADDER.md`** (dp-directed, 2026-08-14). That PRD is why §6's
questions are extension points rather than pending rulings, and it is where the per-case form of
each is decided. Stated so neither document has to be read to understand the other:

- **This PRD governs WHAT reach flows and to whom** — classes, manifests, occupancy, the flow rule.
  **The ladder PRD governs WHO DECIDES** a contested case. They meet at the proof tiers (§2): a
  tier says what evidence an act demands; the ladder says which entity supplies it.
- **They share one `kind` vocabulary** with `PRD_ALLOWLISTS.md` §3.6.5's ceremony table. The hub's
  class taxonomy (§6.1) and item kinds (§6.5) resolve on that **same** key.
- **An agent rung is a candidate second factor, and the twin's §7.3 states what would have to be
  true** — computed independence, a genuinely different failure domain, not the same process
  wearing k hats, and a non-zero dissent rate.
- **The ladder never decides its own authority**, and §9.4 extends that refusal to `role.manifest.*`
  and `role.route.*` — the hub-side surfaces of the same rule.

### 8.1 The convergence requirement (GPT, relayed by dp 2026-08-14) — binding on all three PRDs

> Both PRDs must share **ONE composite policy revision/digest** and **ONE horizon bounded by every
> contributing authority** — standing grants, allowlists, floor, clearances, occupancy, manifest
> generation — rather than each inventing certification semantics.

*(This is the identical binding text the twin carries as §9.1, `PRD_ALLOWLISTS.md` as §12.1 and
`PRD_ADJUDICATOR_LADDER.md` as §11. The section numbers differ per document; the text must not.)*

**One composite revision.** A single digest over the tuple of every contributing authority's
generation — standing grants, allowlists, floor, clearances, **occupancy**, **manifest generation
(§2, §3.1)**, and the ladder generation. Any authority moving moves the composite, and it surfaces
to members through `law_hash`. **This document contributes two of the seven** — occupancy and
manifest generation; clearances are the twin's — which is precisely why neither may mint its own:
a manifest generation that moved without moving the composite would be a policy change no replica
could detect, and §3.1's stranding is the mechanism that would then fail silently.

**One horizon.**

```
horizon = min( now + STANDING_SNAPSHOT_TTL_SECS,  earliest covered expiry across ALL authorities )
```

An occupancy `expires_at` (§3.2), a manifest amendment (§3.1), a clearance expiry and a rung-binding
expiry are **all covered expiries** and all bound the horizon. The requirement is that all three
PRDs use the same expression evaluated over the union, not three similarly-worded expressions in
three documents. **§5 criterion 3 is where this is proved on the hub side** — "strand within one
snapshot horizon" is only meaningful if there is exactly one, and criterion 3 is a joint test with
the twin's criterion 3 for that reason.

**A monotonic counter is required, not just a digest.** `Rules.law_hash` (§10) carries the composite,
but a hash cannot say which of two policies is *older*, and §3.4's stranding depends on order. The
occupancy and manifest generations this document contributes must each be monotonic counters
covered by the composite — which §3.1 already specifies for `manifest_generation` and which §3.2's
conferral record must also carry.

**Why this is not bookkeeping.** Three PRDs each minting a generation, a digest and a TTL produces
three certification semantics that agree until the first time they do not — and the first time they
do not is a snapshot fresh by one document's rule and stale by another's, admitting an act under a
policy that had already changed. One composite has one answer.

## 9. The OUTWARD direction — a caller REACHES a role; the role bounds what they reach

§1–§8 answer *what may a MEMBER touch, having been given a job*. This section answers *what may a
STRANGER reach, having been routed to one* — and the answer is that it is the same question, the
same object, and must not become a second mechanism. The twin carries this as §10 and it is
normative for both sides; only the hub's half is detailed here.

### 9.0 Directive (dp, 2026-08-14, verbatim)

> the key to this is roles. external entities can only access certain scoped roles, which can
> escalate as needed. again a mirror. an average customer only gets to talk to customer service
> agent, and access is scoped by the service agent role. if situation needs escalation to a manager,
> or manager's manager, there is a process for that. human orgs are already governed this way. we're
> just making it operate at machine speed, auditably, and with law-in-the-loop

### 9.1 The access "tiers" are ROLES — which is what removes the second ACL

Receptionist / citizen / named-grant are not standings of the *caller*; they are **roles**, and the
scope lives on the role's manifest (§2) exactly as it does inward. Standing decides which role a
caller is **routed to**; the role's manifest decides what may be **reached**. A per-caller grant is
therefore the **record** of which role was reached under what occupancy — not a bespoke permission
set. No second ACL, no `caller.*` vocabulary.

Two things are flagged rather than absorbed, both because they would fork existing law:

- **A per-grant deny list** contradicts `PRD_ALLOWLISTS.md` §2.2's union-only composition.
- **A per-grant disclosure ceiling** belongs on the **item's class** (§2), not on the grant —
  otherwise the same item discloses differently depending on who asked, and the class stops being
  the unit of judgment.

Also: "tiers" implies a total order. **Roles are a partial order.**

### 9.2 Inward and outward are one object

```
reachable(caller, role) = admitted(manifest) ∩ effective_scope(occupant)
```

The bound applies **twice**: what the role admits, intersected with what its current occupant may
actually do under their own clearances. Outward adds no rule — it adds a party. Revocation (§3.4)
and the §8.1 composite cover it unchanged, which is the test that it is genuinely one object: if
outward needed its own revocation path, it would be a second mechanism wearing this one's name.

### 9.3 Escalation is a ROLE TRANSFER, not a widening

Escalation **composes a new grant under a different role**; it never widens the existing one. The
escalated-to role's admission is evaluated afresh and **nothing carries over but provenance** — the
transcript included. This is the twin's §5.1 laundering argument pointed outward and it needs no new
mechanism. §10 records the honest limit: the envelope makes non-carryover *auditable*, not
*enforced*.

### 9.4 Role-routing configuration joins the ladder's refusal set — hub-side security rule

`PRD_ADJUDICATOR_LADDER.md` §5.3 already refuses to name a rung for `ladder.*` / `governance.*`
kinds: the route table returns a **refusal, not a rung**, because an entry naming a rung would imply
a rung could ever be the decider. **The identical refusal must cover `role.route.*`** (which role a
given standing is routed to) **and `role.manifest.*`** (what a role confers).

**This is a hub-side obligation**, because both surfaces live in the charter the hub stores and
amends (§3.1). Without the refusal, a role reached by an untrusted caller could name itself — or a
role it controls — as its own escalation target, and the effective authority of every outward act
collapses to whatever the cheapest reachable role will confer. `PRD_ALLOWLISTS.md` §3.6.3's
corollary governs: **the control must protect its own registration.**

**One asymmetry, stated plainly: outward routing config is MORE consequential than inward.** Inward,
a mis-routed escalation affects a member who is inside the society, holds a chain identity, and can
appeal. Outward, the affected party is a stranger with no seat, no appeal verb, and no visibility
into the decision. The ceremony tier for `role.route.*` on an outward-facing role must therefore be
**at least the tier of the highest class its manifest confers** — not the tier of the act of editing
a table.

### 9.5 Design-time RWOA+S+V — the outward-routing surface

```
surface: role.route.* amendment   act: decide which role a class of strangers reaches
S: high/reversible (re-amend; §8.1 composite strands derived grants) [construct: charter amendment, law-gated, §3.1]
R: pass [construct: production_law_gate; tier >= highest class the manifest confers, §9.4]
W: pass [construct: quorum per law; witnessed entry carries the route diff]
O: pass [construct: refusal set — role.route.* / role.manifest.* return a refusal, not a rung, §9.4]
A: pass [construct: every routing decision witnessed INCLUDING refusals — a refusal that leaves no
   record is indistinguishable from never having been asked]
V: present [construct: law-defined quorum refusal] — but note the gap: the affected party is a
   stranger with no appeal verb, which is why R is raised rather than V relied on
verdict: PASS (design), with the stranger-has-no-seat gap recorded rather than closed
```

### 9.6 Falsifiable acceptance criteria (outward, hub side)

6. A caller routed to role A and escalated to role B holds **two** grants with distinct
   `occupancy_id`s; B's admission was evaluated afresh; nothing but provenance appears in B's grant
   (differential: an item reachable only under A is not reachable under B).
7. An amendment naming a role as its own escalation target is **refused** at the route table, not
   merely quorum-rejected — the positive control is the same amendment naming a different role,
   which reaches quorum.
8. Every outward routing decision, **including refusals**, produces a witnessed entry (differential:
   count entries after a run of refused asks; zero is a failure).

## 10. R6/R7 envelopes — cross-reference

**See `hestia/docs/PRD_R6_R7_ENVELOPES.md`** (dp-ruled, 2026-08-14): every governed act — compose,
admit, escalate, adjudicate — rides an R6/R7 envelope rather than bespoke per-PRD structures. What
that subsumes from **this** document, and where it does not:

- **§2's ROLE as scope carrier is `ActionRole{actor_lct, role_lct, paired_at}`**
  (`web4-core/src/r6.rs:67-75`), under the invariant *"Role isolation: actions scoped to role's
  permissions"*. `r6.rs:66` states dp's ruling from the other side without having been written for
  it: *"Reputation is ROLE-CONTEXTUALIZED, never global"* — which is §3.2's merit rule already.
- **Two real limits on that row, both hub-side.** `ActionRole` carries **no `occupancy_id` and no
  `manifest_generation`**, which §3.2's conferral record and §3.4's stranding both need. And **the
  outward direction needs two parties where `ActionRole` names one** — §9.2's
  `reachable(caller, role)` has no carrier; `ProofOfAgency` (`r6.rs:102-112`) is the wrong shape,
  because an outward caller delegates nothing.
- **§2's proof tiers map PARTIALLY.** T0/T1/T2 grade *evidence*, not *cost*, so no ATP minimum
  attaches to them. T2's witness quorum maps to `Reference.witnesses` (`r6.rs:124`); T2's operator
  co-sign and hardware-backed key do not. T1's "fresh certified snapshot" has no carrier —
  `Request.deadline` (`r6.rs:92`) is the action's deadline, not the evidence's.
- **§9.3's "nothing carries across an escalation but provenance" is `prev_action_hash`**
  (`r6.rs:360`) — a hash, not a payload, so it *cannot* carry the transcript. Honest half:
  `Request.parameters` (`r6.rs:85`) is an open map and nothing forbids putting the transcript in it.
  The envelope makes non-carryover **auditable**, not **enforced**.
- **§8.1's composite revision is `Rules.law_hash`** (`r6.rs:34`) plus the monotonic counters §8.1
  requires — the occupancy and manifest generations this document contributes.

## 11. Correspondence with the twin — and how divergence is actually detected

The PR opening this document states the pair's contract: *the CONCEPTS section is normative for both
documents — amend in both PRs or neither.* **That convention has no enforcement, and it has
measurably failed twice on this document pair** (the twin absorbed `42fed6b` and `ff0c76d` on
2026-08-14/15; this side did not move for four days). This section is the surface on which the next
failure is visible.

| this document | `hestia/docs/PRD_ROLE_SCOPE_BRIDGE.md` | normative owner |
|---|---|---|
| §0 Directive | §0 Directive | dp (verbatim, both) |
| §2 Concepts (non-normative summary) | §2 Concepts | **NORMATIVE HOME: twin.** Not mirrored. Checked by `concepts_generation`, not by diff |
| §3 Mechanics — hub side | §3 Mechanics — hestia side | each its own |
| §5 Acceptance criteria (hub) | §6 Acceptance criteria (end-to-end) | criterion 3 is JOINT |
| §6 Extension points | §7 Extension points | **shared for 6.1–6.4; §6.5 is hub-only** |
| §8 / §8.1 Ladder + convergence | §9 / §9.1 | **§8.1 text is identical across three PRDs** |
| §9 Outward direction | §10 | **shared** |
| §10 R6/R7 envelopes | §11 | each its own half |

**The check that closes this class**: the ruling that stranded this document arrived as a **commit
on the twin**, not as a comment on either PR. Any process watching a PR thread is structurally
incapable of seeing it. Convergence is therefore checked by **reading the twin's git history for
this file** — `git log -- docs/PRD_ROLE_SCOPE_BRIDGE.md` — and comparing against the table above,
not by reading the twin's PR conversation. For the rows that are genuinely two copies of one text, a
row whose two cells no longer say the same thing is the finding.

**Amended 2026-08-18 — that rule did not cover §2, and could not.** When this section was written it
listed §2 as "shared — amend both or neither" and made a cell-versus-cell comparison the detector.
But §2 here was a 16-line summary and §2 on the twin ran 42 lines including the proof-tier table:
**the cells had never said the same thing, so a difference-detector could not distinguish the
intended asymmetry from a real divergence, and would have reported the same difference forever.** A
guard whose output does not change when the thing it guards changes is not a guard.

§2 is therefore no longer a shared row. It has a **normative home on the twin** and a
`concepts_generation` here, and its check is an integer comparison that *can* go red — two
anchored extractions, no reading required:

```sh
grep -m1 -oE 'concepts_generation: *[0-9]+' hub/docs/PRD_ROLE_SCOPE_BRIDGE.md      | grep -oE '[0-9]+'
grep -m1 -oE 'concepts_generation: *[0-9]+' <hestia>/docs/PRD_ROLE_SCOPE_BRIDGE.md | grep -oE '[0-9]+'
```

```
equal                     => CURRENT
home greater than here    => STALE       — this summary predates an amendment; re-point it
either missing/unreadable => UNDETERMINED — never a pass; resolve before relying on the row
```

**A fourth case this table does not enumerate** (found while making the rule executable,
2026-08-21): `home < here` — the hub citing a generation the home never issued, which is what a
citation bumped without the corresponding amendment, or a reverted home, looks like. The three rows
above do not cover it, and it is plainly not CURRENT. The gate treats it as **UNDETERMINED** and says
so in its output, per the fleet's fail-closed default for unrecognized conditions. It is recorded
here so the tool's behaviour is a written rule rather than an unstated choice; if the intended
verdict is something else, amend this row and the tool together.

**The anchor is load-bearing, and its absence was a real defect in this section** (GPT review,
2026-08-21). The first published version of this block ran a bare `grep -m1 concepts_generation`,
which matches the earliest *prose* mention of the token — a line carrying no number at all — so the
command as written could not extract the value it claimed to compare. It was verified with an
anchored form and shipped with an unanchored one, which is the instrument-versus-its-own-pin failure
this PRD family keeps finding elsewhere, committed here in the check built to replace the last one.
Anchoring on `: *[0-9]+` is what makes the extraction name the value rather than the topic.

The general lesson, and it applies to every remaining "shared" row above: **a convergence rule is
only as good as the difference it is able to report.** Rows that are two copies of one text can be
diffed. Rows where one side legitimately says less need a version, not a comparison — otherwise the
detector's silence and its alarm look identical.
