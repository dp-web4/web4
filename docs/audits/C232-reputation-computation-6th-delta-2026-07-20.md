# C232 — reputation-computation.md 6th Delta Re-Audit

**Date**: 2026-07-20 (06:00 slot `web4-20260720-060036`)
**Target**: `web4-standard/core-spec/reputation-computation.md` (blob `bfdac3ba` at HEAD)
**Lineage**: C15 → C44/C45 → C84/C85 → C123/C124 → C156/C157 → C194/C195 → **C232**
**Method**: v2 protocol; direct delta re-audit (focused-delta file — two remediations + one
note-update since C194) with refute-by-default verification and independent live-HEAD re-reads.

---

## Headline

Since C194 (2026-07-14) the target moved through exactly three commits, all of which this
audit re-verifies as **regression-clean**:

1. **#526 (`062fd24b`, C195 remediation)** applied C194-N2 (`return None` in the §5 no-match
   branch) and C194-N6 (drop the spec-only `value` key from `analyze_factors`).
2. **#541 (`2bc3bafb`, C214-N1 application)** rewrote the §4 "Evidence-basis role" note to
   reflect W4IP Phase 2 ratification (response vocabulary + Effector role).

Both remediations are **verified correct and self-consistent** — the C194-N6 intra-file
self-contradiction (§5 worked example claiming to show factors "exactly as `analyze_factors`
emits them" while the pseudocode emitted an extra `value` key) is now **CLOSED**, and #541's
four new cross-references all resolve faithfully. The SDK mirror set
(`reputation.py`/`r6.py`/`r6.rs`/`wasm.rs`) is **byte-frozen since C194**, so every C194
SDK-track carry (N1 HIGH, N7, N8, INFO-4/5) stands unchanged.

The single net-new yield is **C232-N1 (LOW)**: the W4IP N3 Phase 2 **response side**
(`web4-policy` #525 `cb788768` + hub-law-schema §240/§291 — all net-new since C194) adopts
`reputation.delta.category` as its canonical response-rule selector, but the recognition side
this file owns exposes **no `category` field** on the delta (§1 carries only `rule_triggered`)
and **no machine identifier** for its §4 categories. The recognition→response integration seam
is currently unbridged. It is non-blocking under parse-don't-enact and routes cross-track.

**C233 disposition: NO remediation owed** — spec substantive-CLEAN; C232-N1 routes to the
W4IP/response-side owner, not an autonomous in-file edit.

---

## §A — Regression Verification (all HELD, zero regressions)

| Check | Result |
|---|---|
| **#526 C194-N2** — §5 no-match returns `None` | **HELD & correct** — `:420 return None  # no delta emitted` (was `empty_reputation_delta()`); matches SDK `reputation.py evaluate()` ("Returns None") + vector rep-002 `delta: null`. Success path (`:457-475`) still assembles and returns the `reputation` object; the early `None` bypasses the `:410` allocation harmlessly (pseudocode structure mirrors the SDK). No new inconsistency introduced. |
| **#526 C194-N6** — §5 `value`-key drop | **HELD & self-consistency RESTORED** — `analyze_factors` now appends `{factor, weight}` only (`:525/:538/:545/:559` value-key gone). §5 worked example `:575-577` now shows `{"factor":..., "weight":...}` with no `value`, so the `:572` claim ("exactly as `analyze_factors` emits them") is now **TRUE**. The C194-N6 intra-file contradiction is CLOSED. §1 example (`:49-53`) and SDK `ContributingFactor` already concordant. |
| **#541 C214-N1** — §4 note rewrite (`:386-397`) | **HELD & faithful** — all four cross-refs resolve: (1) `hub-law-schema.md` "Response vocabulary" → `§148` header tagged **W4IP N3** (exact); (2) `entity-types.md §4.8` → `:399 ### 4.8 Effector Role`; (3) `society-roles.md §4.1` → `#### Effector` (`:234`) confirmed **under** `### 4.1 Trust / Accountability` (`:206`, before §4.2 `:240`); (4) `web4-society-authority-law.md §5.6` → `:233 ### 5.6 Effector`. Ratification status accurate ("partially ratified" for vocab+Effector; "cross-boundary adjudication remains proposed"). |
| **#541 boundary-intrusion pointer integrity** | **HELD** — `:363-366` boundary intrusion still says "its adjudication protocol is proposed separately, see the informative note below"; the rewritten note still covers "cross-boundary adjudication remains proposed" → pointer resolves. #541 did not break the intra-§4 reference. |
| **#541 "enacts" over-claim** (candidate) | **REFUTED** — note `:392` "the **Effector role** that enacts it" matches `entity-types.md §4.8` `:417-422` own framing ("Enacts only the ratified response vocabulary `notice\|quarantine\|correct\|rehabilitate`, plus the kinetic class … which remains parse-don't-enact"). The four ratified rungs ARE enactable (`hub-law-schema.md §189`: only the kinetic class is parse-don't-enact). No defect. |
| SDK mirror set frozen | **HELD** — `reputation.py` (`759eaefa` 04-17), `r6.py` (`766611ef` 05-14), `r6.rs` (`3f941988` 07-09), `wasm.rs` all byte-frozen since C194. No mirror drift. |
| Inbound §4 citations | **ALL RESOLVE** — `entity-types.md:425`, `hub-law-schema.md:188` (rehab→§7 N5-pending, accurate as pending) + `:220`, `SOCIETY_SPECIFICATION.md:483`, `web4-society-authority-law.md:235`, `mcp-protocol.md:415` (C154-N1 **stays consumed**), `acp-framework.md:418` (§10 future). |
| C194 open carries | **ALL STAND** — N1 (HIGH, Rust `ReputationDelta` wire shape from/to/factor + net_* — SDK frozen), N3/N4 (§7 Talent-decay layer split, operator DESIGN-Q — §7 + t3-v3 §2.3 both untouched), N5 (bad-faith-emergency disclaimer, W4IP-N5 owner — `:367-371` untouched by #541), N7 (r6.py jsonld truthiness-drop), N8 (wasm factors param). |
| Standing carries | **STAND** — C156-3 (`sovereign_strength` r6.rs-only), C156-4 (hub temporal fold), carry-C46 (`role_pairing_in_mrh` still `:26-31`/`:72` denormalized-convenience, absent both SDK deltas). |

**§A verdict: 0 regressions; both C195 remediations correct; #541 application faithful.**

---

## §B — Net-New Finding

### C232-N1 (LOW, cross-spec forward-dependency seam — route to W4IP/response-side owner + reputation §1/§4 note) — the response selector `reputation.delta.category` has no producer-side field or category identifier

**Provenance (net-new since C194):** the W4IP N3 Phase 2 **response side** landed in
`web4-policy/src/lib.rs` via **#525 `cb788768` (2026-07-15)** — the `ResponseRule` struct +
the `reputation.delta.category` selector — and in `hub-law-schema.md` via #522 (`87377c38`,
07-14) + #525. All postdate the C194 audit (2026-07-14), which examined only the
delta-shape mirrors (`reputation.py`/`r6.py`/`r6.rs`/`wasm.rs`), not the newly-ratified
**consumer**. C228 (07-19, atp-adp) noted the selector once, only as evidence the response
namespace is disjoint from the norm namespace (`r6.resource.atp`); it did not examine the
delta-shape seam. Genuinely net-new and unrecorded.

**The seam:**
- The response side's **canonical** selector is `reputation.delta.category`, used consistently
  as: the `ResponseRule` docstring namespace (`web4-policy lib.rs:135`), the parse-don't-enact
  rejection error message (`:359`), the `responses_parse_all_nine_verbs` test fixture
  (`:869-881`, e.g. `selector: reputation.delta.category, value: coercive_extractive`), the
  hub-law-schema YAML surface (`§240`), and normative list item 13 (`§291-292`:
  "response selectors range over recognition evidence (e.g. `reputation.delta.category`)").
- The recognition side this file owns exposes **no `category`**: `ReputationDelta` §1
  (`:22-84`) has 15 fields — the only path to the §4 category is `rule_triggered` (a rule-id
  string, e.g. `successful_analysis_completion`), never the category. Grep for a `"category"`
  field or a machine identifier (`coercive_extractive`) in `reputation-computation.md` = **0**;
  §4 category names are prose headers only ("Coercive/Extractive Behavior Rules").
- So a ratified response rule `selector: reputation.delta.category, value: coercive_extractive`
  selects over an attribute the emitted delta does not carry, keyed on an identifier no spec
  defines. The category is *derivable* (map `rule_triggered` → its §4 grouping), exactly as
  `role_pairing_in_mrh` is "derivable from `role_lct`" (§1 `:72`), but no spec states the
  mapping.

**Why LOW / non-blocking now:** parse-don't-enact — `web4-policy` validates that a response
`selector` is non-empty and not `r6.*` but **never resolves** it (`Law::evaluate*` never reads
responses; `law-inert` regression tests confirm). No conformance vector or shipped behavior is
contradicted. The seam bites only when response *enactment* is ratified (parse-don't-enact
lifted), at which point an evaluator must resolve `category` from the delta.

**Remediation shape (owner to choose; do NOT self-apply):** either (A) §1 adds a `category`
field to `ReputationDelta` (Required: No, derivable from the triggered rule's §4 grouping) with
canonical category identifiers defined in §4 (`coercive_extractive`, `ethical_violation`, …),
or (B) the selector-namespace resolution (`reputation.delta.category` ← `rule_triggered` → §4
category) is defined on the response side (hub-law-schema). **Ownership is ambiguous**:
hub-law-schema owns the selector namespace; reputation §1/§4 owns the delta shape + category
taxonomy — the mapping is the bridge between them and belongs to whichever side the
response-enactment ratification assigns it. → **W4IP/response-side owner + reputation §1/§4
note.** Do NOT self-apply (design content + cross-track).

### INFO ledger

- **INFO-1**: `web4-policy` is a **consumer** of reputation §4, not a delta-shape mirror — it
  selects over `reputation.delta.category` to choose responses; it does not compute deltas
  (no `compute_reputation_delta`/`analyze_factors`/`inactivity` in the crate). This is exactly
  the "recognition input the response side consumes" relationship the §4 note (`:396-397`)
  describes. Its addition does not change the mirror set: `reputation.py` remains the sole
  §5/§7 engine.
- **INFO-2 (corroboration)**: this reputation-side seam is the direct analog of C228-I1
  (atp-adp Effector/slashing-authority harmonization). Unlike atp-adp's `slash` — which
  refuted to CONSISTENT because `has_slashing_authority` is *abstract* — the reputation
  `category` selector is *concrete* (`value: coercive_extractive`) with no producer-side
  field, so it does **not** compose clean. The response framework revives a distinct salience
  on this file: the recognition delta must eventually expose category.

### Negative results (verifiable)

- §5 `compute_reputation_delta` success path (`:457-475`) intact and consistent with the
  `return None` early branch; `compute_dimension_delta` (`:478+`) unchanged.
- §7 Talent-decay section untouched since C194; t3-v3 §2.3 frozen (per C230) → C194-N3/N4
  layer-split adjudication unchanged, no re-open.
- Response vocabulary list `notice | quarantine | correct | rehabilitate` matches its source
  in all three sibling specs (hub-law-schema `§185-188`, society-roles §4.1 Effector,
  entity-types §4.8 `:417-418`); kinetic class `slash | suspend | revoke | terminate | halt`
  consistently parse-don't-enact across hub-law-schema `§189/§206`, entity-types `§4.8`, SAL
  `§5.6`.

---

## §C — Carry Ledger (post-C232)

**Consumed/closed this audit**: C194-N2 + C194-N6 **CLOSED** (remediated by #526, verified);
C214-N1 application **VERIFIED faithful** (per the C214 forward-note "verify at reputation's
next audit"). C154-N1 remains consumed (re-verified). C192-N1 remains closed.

**New outbound route (TWO named referents — one seam, dual ownership; record both so it
cannot drop into single-side prose at the next delta, per [[feedback_prose_is_not_ledger]]):**
- **C232-N1 → referent A: W4IP/response-side selector-namespace owner** (hub-law-schema §240/
  §291 + `web4-policy`): define how `reputation.delta.category` resolves against the emitted
  delta (`rule_triggered` → §4 category), OR
- **C232-N1 → referent B: reputation §1/§4 delta-shape + taxonomy owner** (this file): add a
  `category` field to `ReputationDelta` §1 (Required: No, derivable) + canonical category
  identifiers in §4 (`coercive_extractive`, `ethical_violation`, …).
- Whichever side the response-*enactment* ratification assigns the bridge to owns the fix.
  Cross-track, do NOT self-apply.

**Standing carries re-verified and unchanged**: C194-N1 (HIGH, SDK wire shape), C194-N3/N4
(operator DESIGN-Q §7 decay), C194-N5 (W4IP-N5 bad-faith disclaimer), C194-N7 (r6.py jsonld),
C194-N8 (wasm factors); C156-3 (`sovereign_strength`), C156-4 (temporal fold), carry-C46
(`role_pairing_in_mrh`).

**C233 disposition: NO remediation owed** (spec substantive-CLEAN).

**Rotation** → next fire = **acp = C234** (per fixed round-robin; reputation followed by acp).

---

*Audit instrument: focused-delta method (frozen-except-three-commits file). The one net-new
finding came from the SDK-mirror-expansion lens re-derived at live HEAD — treating the
newly-ratified `web4-policy` response engine as a consumer, not a mirror, surfaced the
recognition↔response `category` seam that the delta-shape-only lens of C194 could not have
seen. The one candidate over-claim ("enacts") REFUTED against the source's own framing.*
