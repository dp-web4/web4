# C280 — Seventh-Delta Re-Audit: SOCIETY_SPECIFICATION.md

**Date**: 2026-07-29
**Auditor**: Legion autonomous web4 track (slot `web4-20260729-000011`, v2 protocol)
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (498 lines, target blob `2ad453ba`)
**Lineage**: C22 (first audit, #251) → C50 (1st delta, #317) → **C51 remediation** (`958a5625`/#318) → C92 (2nd) → C131 (3rd, first fully-clean) → C164 (4th) → **C202** (5th, `87377c38`/#522 §7.3 mover) → C240 (6th, #559, fourth consecutive fully-clean) → **C280 (this, 7th)**
**Rotation**: audit-side round-robin WRAPPED back to `SOCIETY_SPECIFICATION.md` (the oldest target) after C278 (mrh-tensors 7th delta, #585 MERGED).
**Staleness at audit**: **BYTE-FROZEN since C202.** `git diff 5606485f HEAD -- <target>` is **EMPTY**; blob `2ad453ba` is byte-identical to C240's snapshot. No commit has touched the file in 13 days.
**Method**: Freeze-verification delta. **§A** freeze + §7.3 mover re-resolution at *current* sibling bytes. **§B** bounded net-new sweep, refute-by-default, ONE lens per candidate, with the **genuine-mirror gate re-derived at live HEAD** and the standing method carries v2/v3/v5/v6 applied to the window. **§C** bidirectional carry re-verification under the C98 snapshot-presence and C146 path-provenance guards.

---

## Verdict (summary)

- **§A — CLEAN.** Freeze holds; the §7.3 mover is regression-free. **Zero** §7.3-cited siblings moved since C240, so every citation re-resolves at its C240 anchor.
- **§B — 1 spec-vs-implementer split (N1, MED) + 2 routed to a proposal author (N2 MED, N3 LOW).** The re-derived genuine-mirror gate surfaced **`hub/`** — the corpus's largest and most active society implementer — as a mirror surface **never gated in this file's seven-audit lineage**. Gating it produced **N1**: §2.3's ratified *"Rejection is a non-record outcome"* is contradicted by the landed hub, and the corpus's **two** society implementers are **split** on it (Python SDK conforms, hub does not). The two *most attractive* window candidates were **REFUTED** (the "admission-law theater" charge has no face on this target; the ontology commit cannot reach it).
- **§C — 7 carries re-verified OPEN** at HEAD; all anchors unmoved; none resolved downstream.
- **Net: 0 autonomous spec edits. ZERO mutation.** The fifth consecutive delta in which the target's own bytes required no correction — but the **first** in which the mirror gate found a live divergence, because the gate had been under-derived. **C281 = declared NO-OP on the spec side.**

**Honest scoping note, stated up front.** N1's underlying *fact* is 31 days old (`00c7a6c7`, 2026-06-27) and therefore predates C240. It is net-new **as a finding**, not net-new **as a fact**. What changed is the *gate*, not the code — see §B-1 and the method lesson in §D. Reporting it otherwise would overclaim.

---

## §A — Freeze Verification + §7.3 Mover Re-Resolution

**Result: CLEAN.**

`git diff 5606485f HEAD -- web4-standard/core-spec/SOCIETY_SPECIFICATION.md` is **empty**. Blob `2ad453ba` is byte-identical to C240's snapshot. Therefore the 478 lines of frozen body outside §7.3 carry C92's token-by-token verification of all 21 C51 findings **by construction**, and the `#`-regression sweep is satisfied by construction — no new prose exists to regress.

§7.3 (`:472–495`), the only methodologically-live section (the #522 W4IP Phase-2 mover), is itself byte-unchanged. Re-verification is therefore limited to **§7.3-cited siblings that moved since C240**:

```
git log --oneline --since=2026-07-21 -- reputation-computation.md hub-law-schema.md \
    society-roles.md inter-society-protocol.md web4-society-authority-law.md
→ (empty)
```

**Zero cited siblings moved.** Re-resolved anyway at live HEAD, against C240's recorded anchors:

| §7.3 citation | Live ground truth (HEAD) | vs C240 | Verdict |
|---|---|---|---|
| `reputation-computation.md` §4 (Reputation Rules) | `:239` `## 4. Reputation Rules` | `:239` | **EXACT, unmoved** |
| Coercive/Extractive Behavior Rules category | `:339` `#### Coercive/Extractive Behavior Rules` | `:339` | **EXACT, unmoved** |
| `hub-law-schema.md` response vocabulary | `:285` ``` `response` is one of `notice`, `quarantine`, `correct`, `rehabilitate` ``` | present | **EXACT** |
| `proposals/W4IP-DRAFT-2026-07-13-…​.md` (informative) | path resolves | present | **EXACT** |

**§A conclusion: no regression.** Freeze verified on both the target and its citation surface.

---

## §B — Net-New Sweep (bounded, refute-by-default, ONE lens per candidate)

### §B-1 — genuine-mirror gate re-derived at live HEAD: `hub/` enters the mirror set

The standing method guard requires re-deriving the implementer/consumer set at live HEAD every delta. Doing so this pass:

1. **Python SDK `society.py` / `federation.py` / `role.py`** — frozen since `759eaefa`. Carries re-verified in §C. No net-new.
2. **web4-core `society.rs` / `ledger.rs`** — unchanged since C202. C202's §B-2 refutation stands. No net-new.
3. **`web4-policy`** — gated at C240 as a **faithful** §7.3 implementer. Unchanged. Guard honored; **not re-flagged**.
4. **`hub/` — NEW to this file's mirror set.** Prior passes (C202, C240) derived the mirror set as *SDK + web4-core + web4-policy* and never included `hub/`. That was an under-derivation: `hub/` is a full Web4 **society** implementer — `hub/docs/PRD.md:38` states its "**7-role state**: Sovereign, Law-Oracle, Policy-Entity, Treasurer, Administrator, Archivist, Citizen", i.e. exactly §1.2.5's base-mandatory seven — with a hash-chained witnessed ledger and a law engine. It is the *most* load-bearing mirror this target has, and it had never been read against it.

The window is what forced the re-derivation: the two-commit public-release hardening wave (`9e9f349a` + `95683868`, 11 files, +578/−150) moved `hub-lib/src/{hub,init,state,store,events}.rs`.

**The wave itself is a FALSE MIRROR for this target** (recorded so future deltas do not re-walk it): its society-lifecycle token footprint across those five files is **two lines** — `hub.rs:183 citizenships: Vec::new()` (an `Lct` struct-field initializer) and `state.rs:111`, a doc comment about council-threshold recomputation. The wave moved rate-limiting, per-field disclosure tiers, and admission *plumbing* — not the §1.2.2/§4.2.1 society-lifecycle event classes. **But re-deriving the gate for the wave is what put `hub/` in the mirror set, and that is where N1 lives.**

### §B-2 — **N1 (MED) — §2.3's ratified "Rejection is a non-record outcome" is contradicted by the hub; the corpus's two society implementers are SPLIT**

**The spec's position, stated twice.**

`SOCIETY_SPECIFICATION.md:130` (§2.3 Citizenship Lifecycle, the C22-H3 → C51 remediation note, HELD at C50-A4, C92, C131, C164, C202, C240):

> **Note on `Rejection`**: Rejection is a non-record outcome — the rejection itself **creates no ledger event and assigns no status**. The canonical SDK `CitizenshipStatus` enum contains only `APPLIED`, `PROVISIONAL`, `ACTIVE`, `SUSPENDED`, and `TERMINATED` (no `REJECTED` value); a rejected application's prior `apply` event (§4.2.1) remains the entity's most recent citizenship event, with no further transition recorded.

Corroborated by §1.2.2 Minimum Records (`:35`), whose citizenship enumeration is `apply/grant/provisional grant/suspend/reinstate/terminate` — **no `reject`**.

**Implementer A — Python SDK: CONFORMS.** `federation.py:91–98`, docstring *"Citizenship lifecycle states per SOCIETY_SPECIFICATION §2.3"*, five values, no `REJECTED`.

**Implementer B — hub: DIVERGES.** The hub records the rejection as a hash-chained ledger event **and** assigns it a status:

| Construct | Site | Content |
|---|---|---|
| ledger event | `hub/hub-lib/src/events.rs:119` | `MemberJoinResolved { approved, … }` — event name `member_join_resolved` (`events.rs:576`) |
| assigned status | `hub/hub-lib/src/state.rs:344–346` | `JoinStatus::{Pending, Approved, **Denied**}` |
| projection | `hub/hub-lib/src/state.rs:604–609` | `jr.status = if *approved { Approved } else { **Denied** }` |
| queue | `hub/hub-lib/src/state.rs:120–124` | `pending_joins`, "Built from `MemberJoinRequested`/`MemberJoinResolved`" |

**These are the same act — the hub says so in its own words.** This is the load-bearing identity claim, so it is evidenced four ways rather than asserted:

- `hub/README.md:264` — *"An external entity calls `request_citizenship` (**or** `POST /v1/hubs/:id/members/join`)."* — one act, two surfaces.
- `hub/docs/PAIRED-CHANNELS.md:338` — *"caller is `sovereign` / `citizen` (**member**) / external"* — citizen **is** member.
- `hub/hub-lib/src/law.rs:1183–1190` — the norm selecting `r6.request.action == member_join_request` is described *"**Citizenship** is not open-admission."*
- `hub/hub-daemon/src/rest.rs:2658` — *"`request_citizenship` action — the external→citizen bootstrap"*.

**Why it matters beyond a naming split.** Under §2.3, a *rejected* applicant and a *pending* applicant are **indistinguishable**: neither has a subsequent event, so §4.2.1's action-to-status mapping derives `APPLIED` for both. The rejection outcome is not merely unrecorded — it is unreadable from its own null. The corpus's ratified accountability norm (CLAUDE.md) lists **admit/join** among consequential acts, and clause **A** requires that *"the act, its stakes assessment, and the evidence relied upon commit together in the signed hash-chained record."* A denial is the negative branch of that same gate; a non-record fails A. The hub's own review-gate block for the hardening wave asserts `A: pass [construct: signed ledger unchanged]` — it is holding itself to the clause the spec's note waives.

**Stakes classification (honest, and it caps the severity).** The act is **medium / reversible** — re-application is expressly contemplated (`hub/hub-lib/src/law.rs` admission `repeat_limit: 3`, `review_limit: 1`). This is therefore a **MED**, not a HIGH: a reversible act's evidence bar is lower, and A is the only clause implicated.

**Direction: spec-stale, not implementer-wrong — and it is an instance of the standing flagship class.** The note's *recorded* rationale is SDK-enum conformance: C22-H3 raised the diagram-vs-enum mismatch and C51 resolved it by amending **the spec** to describe the SDK. That is the **SSOT-inversion** pattern of standing carry **B-D1**. A second, later, independent implementer then built the opposite — and the window's parent principle (#580, on dp's direction) argues the hub is right: *"absence is **represented**, not imputed"*; *"a **recorded refusal** that says what was missing and why it could not be got"*; and, naming the defect class exactly, *"an exhausted correction loop that **looks identical to a request never sent**."*

**Refutations attempted (refute-your-best-finding discipline) — five, all survived, two with concessions:**

- **R1 — "the hub's chapter is not a §2.3 society."** REFUTED: `hub/docs/PRD.md:38` gives the base-mandatory seven, plus a witnessed hash-chained ledger and a law engine.
- **R2 — "§2.3's note only *describes* the SDK; it does not bind societies."** REFUTED: the note is declarative prose in a core spec, and §1.2.2's Minimum Records enumeration independently omits `reject`. Two sites, same position.
- **R3 — "a denial is not consequential."** PARTLY SUSTAINED → severity reduced. Admit/join is listed as consequential and "when unsure, treat it as consequential", but the act is **reversible**, so this lands MED, not HIGH. Recorded above.
- **R4 — "the non-record was deliberate: not recording a rejection avoids stigmatizing an entity."** NOT REFUTED — and this is the strongest counter, so it is stated in full. The spec gives **no** such rationale (the rationale on record at C22-H3/C50-A4 is enum conformance), but *absence of a stated rationale is not absence of intent*. Note also that the corpus has its own answer to the privacy concern — the hub's **per-field disclosure tiers** (`events.rs`, the very construct the hardening wave revised) make "record it at a restricted tier" available. **Because R4 cannot be closed from the artifacts, N1's disposition is an operator DESIGN-Q, not a correction.**
- **R5 — snapshot-presence (C98): is this new?** **PARTLY SUSTAINED, and it re-frames the finding.** `JoinStatus::Denied` and `MemberJoinResolved` landed in `00c7a6c7` (#391, 2026-06-27) — 31 days old, 24 days before C240. The divergence existed at C240 and C202 and was not caught, because `hub/` was not in the mirror set. **N1 is net-new as a finding, not as a fact.** Claiming otherwise would be exactly the overclaim the snapshot-presence guard exists to prevent.

**Disposition: routed to the operator; adjudicate WITH B-D1 (same SSOT-inversion class, new instance).** ZERO mutation here. Whichever way it resolves, one of two artifacts must move — §2.3 + §1.2.2 + `federation.py`, **or** the hub — and that is not an autonomous call.

### §B-3 — **N2 (MED, routed to the proposal author) — #580's precedent survey omits the corpus's one ratified COUNTER-precedent**

`proposals/resilience-to-incomplete-information.md` (`954ee391`, #580, CBP on dp's direction) carries a section headed **"This is already canon in two places — just never generalized"**, citing `r6-framework.md` (corrective R6 for Results) and `data-formats.md` §W4ID (unknown ≠ malformed). Both are *supporting* precedents.

It cites **no counter-precedent** — and there is one, in the core spec of the very domain the proposal legislates: `SOCIETY_SPECIFICATION.md` §2.3's non-record rejection is the corpus's one **ratified instance of the defect class #580 names**. A proposal whose survey finds only agreement will not know it has to argue against a sibling that six audits have held.

This is **prospective**, so per the standing method carry the charge lands on the **proposal's precedent survey**, not on the ratified spec. It is materially strengthened by N1: the hub has already built #580's shape, so the proposal has a landed ally it does not cite and a ratified obstacle it does not address.

**Disposition: routed to the proposal author (CBP).** No spec change requested.

### §B-4 — **N3 (LOW, routed to the proposal author) — #579's target list is complete only under one branch of its own open question**

`proposals/dictionary-as-context-mandatory-role.md` (`4665a430`, #579) lists **Targets:** `core-spec/society-roles.md` only. Its own **Open question 1** keeps *base-mandatory* live as an alternative tier ("Base is defensible if you hold that a society with no Dictionary is not addressable and therefore not a *participant*").

Adjudicated per method carry v5 (widen case → dimension) and v3 (governance tier):

- **At the proposed *context-mandatory* tier → this target needs NO change.** §1.2.5 does not enumerate context-mandatory roles *at all*, and that silence is **dimension-level and pre-existing**, not a gap #579 opens: `society-roles.md` §3 already carries a cross-society trigger (**Federation-Member → Diplomat**) that §1.2.5 has never mentioned. §1.2.5's scope is the base-mandatory tier. **Charge REFUTED on this branch.**
- **At the *base-mandatory* tier → the count and enumeration go stale in eight places, none of which #579 names.** Re-derived corpus-wide: `SOCIETY_SPECIFICATION.md:60` ("**seven** base-mandatory roles — Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator, Archivist, and Citizen") and `:83` ("fills all **seven**"); `entity-types.md:281` (which enumerates the seven *and* names §1.2.5 as the resolution site); `ontology/role-extension-schema.md:26`; `implementation/sdk/web4/role.py:5`; plus `README.md:24`, `STATUS.md:13`, `hub/docs/PRD.md:38`.

Worth flagging to the author because the tier choice is not merely a label: `society-roles.md` §1.2 states that context-mandatory mappings are **society-sovereign** and that *"The Web4 standard does **not** normatively specify these mappings"* — so a universal `MUST` (#579's rule is keyed on the behavioural condition *"accepts requests from outside itself"*, not on a claimed outward role) placed in that tier is **de-normativized by the tier's own meta-rule**. The proposal frames open question 1 as a *participation* argument and does not reach the *normative-force* consequence.

**Disposition: routed to the proposal author (CBP).** No spec change requested.

### §B-5 — REFUTED candidates (recorded so future deltas do not re-walk them)

- **"Admission law is declarative theater" (`docs/strategy/hub-position-review-and-plan-2026-07-28.md:25`) has NO face on this target.** `grep -niE 'admission|min_trust|join|sponsor'` against `SOCIETY_SPECIFICATION.md` returns **zero** hits; the spec has no admission-gating vocabulary. §7.3's scope is graded responses to *witnessed violations*, not admission. The charge is owned by `hub/hub-lib/src/law.rs:123` and is **already routed** (hestia PRD §6, disposition "wire it with escalate-not-deny semantics, or delete it", deferred to HUB). Importing it here would be a duplicate booking — the error the C232-DISJOINT guard exists to prevent. **Adjudicated, not imported.** (Distinct from N1: that charge is about a *silently dead* admission parameter; N1 is about whether the admission *outcome* is recorded.)
- **v6 ontology gate — NEGATIVE, cannot reach this target.** `01f410db` (`t3v3-ontology.ttl`: `web4:Tensor` superclass + `web4:observationCount`, the commit that produced C278's N1) was machine-checked against this target's **emitted examples**: all **9** fenced blocks parsed (18 fence markers, `grep -c '^```'`); `grep -n "web4:\|t3v3-ontology\|observationCount"` over the whole file returns **zero** hits. The target names T3/V3 in prose (§1.2.4, §5.3) but emits no ontology term in any example, so a `.ttl` edit has no example here to falsify.
- **`docs/PRD_ACTION_EVIDENCE.md`, whitepaper §11 corrections, `206dd004` (CI), `5df662a5` (README), hub fixes #560/#561/#566/#578** — checked for claims over this file's subject matter (society roles, law, ledger, citizenship, governance); none restates or re-scopes it. No candidate.

**§B conclusion: 0 autonomous spec edits; 1 spec-vs-implementer split routed to the operator; 2 items routed to a proposal author.**

---

## §C — Carry Re-Verification (bidirectional; C98 snapshot-presence + C146 path-provenance guarded)

Every anchor re-run at live HEAD rather than trusted from C240. **7/7 OPEN, unmoved. None resolved downstream.**

| Carry | Anchor re-run at HEAD | Status |
|---|---|---|
| **C50-B13** Law Oracle name collision | target `:24` "Codified rules governing entity behavior…" vs `society-roles.md:71` `### 2.2 Law Oracle` | **OPEN, unmoved** — operator DESIGN-Q |
| **C50-B14** citizenship revocability vs SAL §5.1 | `web4-society-authority-law.md:180` `### 5.1 Citizen (Genesis, Immutable)` | **OPEN, unmoved** — operator DESIGN-Q |
| **C50-B15** law inheritance model | target `:178` "Local laws can extend but not contradict inherited laws" | **OPEN, unmoved** — operator DESIGN-Q |
| **C92-N1** solo-founder guard (half-closed) | `society.py:317–318` `if len(founders) < 2: raise` **still live**, while `role.py:303–305` docstring still claims the gap "resolve[d]" | **OPEN, unmoved** — SDK-track |
| **C164-N1** enum-comment stale vocab | `society.py:92` `# join/leave/suspend/reinstate`, `:94` `# allocate/deposit/reclaim` — still pre-C51 (no `mint`/`slash`) | **OPEN, unmoved** — SDK-track |
| **C22-M3** `type` ↔ `event_type` | `society.py:111` `event_type: LedgerEventType` vs spec envelope `type` | **OPEN, unmoved** — SDK-track |
| **C92-N3 / C50-B20** id-scheme example strings | frozen body, present | **OPEN** — C33 id-scheme bundle |

**Inbound (bidirectional) check:** no sibling audit doc in the window routed a carry back to this target. **New carry this delta: N1** (operator), **N2/N3** (proposal author).

---

## §D — Disposition

- **Spec side: NO ACTION. ZERO mutation.** Target byte-frozen since C202; no autonomous edit is warranted or authorized. Do NOT self-edit — the file sits under an unanswered operator DESIGN-Q bundle.
- **N1 → OPERATOR, adjudicate WITH B-D1** (same SSOT-inversion class, new instance). The question to put: *does a citizenship rejection commit a record?* Resolving it moves either §2.3 + §1.2.2 + `federation.py`, or the hub — never both, and not autonomously. R4 (the deliberate-non-stigma reading) is the live counter and cannot be closed from the artifacts.
- **N2, N3 → PROPOSAL AUTHOR (CBP)**, prospective. Neither requests a spec change. N2 is the load-bearing one: #580 should know it has a landed ally (the hub) and a ratified obstacle (§2.3) that its survey misses.
- **Operator DESIGN-Q bundle (unchanged):** C50-B13, C50-B14, C50-B15.
- **SDK-track bundle (unchanged, travels together):** C92-N1, C164-N1, C22-M3, C92-N3/C50-B20. Re-derive the owed set from this doc's §C **text**, not from a downstream §C alone.
- **Cross-track (unchanged):** C232-N1 does not intersect §7.3. `web4-policy` #525 remains a FAITHFUL §7.3 implementer — do NOT re-flag.
- **No review-gate block is owed.** This audit proposes no diff to any surface; the deliverable is one document. The RWOA+S+V clauses appear inside N1 as *evidence*, not as a gate on this change.
- **C281 = declared NO-OP on the spec side.** Next SOCIETY_SPEC delta ≈ C320.

### Method lesson (carry forward to EVERY delta)

**The genuine-mirror gate had been under-derived for this file's entire lineage.** Seven audits derived the mirror set as *Python SDK + web4-core + web4-policy* and never included **`hub/`** — despite `hub/` being the corpus's largest, most active, and most complete society implementer (a full base-mandatory-seven society with a witnessed hash-chained ledger and a law engine). The divergence N1 reports sat in the tree for 31 days across two prior deltas of this file.

The generalization: **"re-derive the mirror set at live HEAD" is not satisfied by re-running last pass's list against a newer HEAD.** It requires asking *which artifacts in the repo now implement this spec's subject matter* — including implementers in directories the lineage has never read. The trigger that worked here was a window commit touching a **directory** the mirror set excluded; the trigger that should have worked earlier was noticing that a spec about societies had never been read against the repo's society daemon.

*Method references: [[feedback_refute_your_best_finding]] (§B-2 R1–R5, two concessions sustained), [[feedback_snapshot_presence_guard]] (R5 — the fact is 31d old; the gate is what is new), [[feedback_canonized_principle_rescopes_frozen_file]] (#580/#579 are PROPOSALS — prospective authority, charge lands on the survey), [[feedback_read_the_specs_meta_structure]] (§B-4 — the context-mandatory tier's own meta-rule de-normativizes a MUST placed in it), [[feedback_empty_column_not_missing_cell]] (§B-4 — §1.2.5's silence widened from Dictionary to the whole context-mandatory dimension, and refuted), [[feedback_schema_edit_falsifies_sibling_examples]] (§B-5 — v6 ontology gate run against emitted examples, NEGATIVE), [[feedback_prose_is_not_ledger]] (§C owed set re-derived from prior §C text).*
