# PRD — the role-scope bridge (hub side): work scope delegated to roles, enforced by hestia

**Status**: proposed — dp-directed 2026-08-14; design PRD, not started; bridges hub<->hestia; builds
on #431's standing-scope surface (hestia PR).
**Author**: claude-code (CBP), 2026-08-14.
**Twin**: `hestia/docs/PRD_ROLE_SCOPE_BRIDGE.md` — the enforcement side of the same bridge. The
CONCEPTS section (§2 there, mirrored in §2 here) is normative for BOTH documents; each side details
only its own mechanics. Amend the shared concepts in both PRs or neither.
**Relates to**: `PRD_HUB_V2_FEDERATED.md` R4 (roles as entities — the role scope manifest extends the
R4 charter), R7b (asserted-asker law), R1/R2 (cross-hub occupancy, deferred), `ROLES.md`, `HUB-LAW.md`,
`hestia/docs/PRD_GATE_CONSOLIDATION.md` (one authority path), web4's RWOA+S+V accountability norm.

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

## 2. Concepts (shared with the twin; summary)

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
does the actual retraction within one snapshot horizon. Acceptance is measured end-to-end (§5.3).

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
   reach within one snapshot horizon, measured on a live constellation (joint test with the twin's
   criterion 3).
4. A self-asserted (unpaired) hub's attestation confers zero reach on a constellation (R7b
   differential, joint with the twin's criterion 4).
5. Attestations are served only to the subject member and operator surfaces (differential fetch as
   a third member fails).

## 6. Open questions (declared RED until ruled)

1. **Class taxonomy governance** — the bridge's hardest question, shared with the twin: the class
   vocabulary must mean the same thing to the hub (which tags items) and to each constellation
   (which approves clearances). One ratified shared list? Hub-law-owned with constellation
   subscription? Per-edge mapping (R6-style compatibility record over the class vocabulary)?
   A spelling mismatch is a permanent withhold or a flow-rule hole.
2. **Cross-hub occupancy** — a role conferred over an R1/R2 federation edge: recommendation, out of
   v0 (local-hub occupancies only); when it lands, it should ride the R6 edge-compatibility record
   plus a tier bump, not a new mechanism.
3. **Second factor for agent members** (tier T2) — ruled on the hestia side (twin Q3); the hub's
   stake is only that `proof_tier` labels are meaningful. Until ruled, T2 = operator co-sign.
4. **Reputation interaction** — should conferral eligibility or clearance asks surface T3
   thresholds? Doctrine: surface the evidence beside the decision, never auto-decide (twin Q4).
5. **Manifest item vocabulary** — items name constellation-local things (repos, paths, egress).
   Does the hub validate item shape at all, or treat items as opaque strings the constellation
   interprets? Recommendation: opaque-with-schema (typed item kinds, uninterpreted values) so hub
   law can quorum-review a diff without pretending to know a member's filesystem.

## 7. Non-goals

- No hub-side enforcement of local scope, and no push channel into member machines — the hub emits
  witnessed evidence; enforcement is the constellation's (one authority path, per side).
- No clearance store on the hub: clearances are the occupant operator's judgment and live in the
  occupant's vault. The hub never learns *why* an item was withheld, only (optionally) that it was.
- No new transport; attestations ride the membrane.
- No change to R4 merit/tensor semantics — occupancy scope is reach, not merit.
