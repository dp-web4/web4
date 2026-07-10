# C168 — SOCIETY_METABOLIC_STATES.md 4th-Delta Re-Audit (C21→C54/C55→C96→C133→C168)

**Audit ID**: C168
**Date**: 2026-07-10
**Target**: `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` (444 lines, v1.0.0, "Proposed Standard")
**Lineage**: C21 first-pass (2026-05-29) → C54 first-delta (2026-06-14) → C55 remediation (PR #326, `a504ea41`) → C96 2nd-delta (0 net-new) → C133 3rd-delta (0 net-new) → **C168 (this, 4th delta)**
**Rotation provenance**: C166 (dictionary 4th-delta, PR #497, **MERGED** 2026-07-10T05:10Z `23f9699f`) found 0 autonomous defects and declared **C167 a NO-OP** in its §D. Step-(a) re-confirmed this fire: #497 merged with no changes requested; no operator DESIGN-Q answered and no metabolic-relevant authorization in the interval. Per the C93→C94 / C165→C166 precedents the no-op slot advances the round-robin +2 to the next-oldest file = SOCIETY_METABOLIC (last audited C133, 2026-07-03).
**Auditor session**: legion-web4-20260710-000036 (LEAD, slot 000036)
**Out of scope**: spec/SDK/crate edits (audit turn — zero mutation); M7 TTL drafting (operator-flagged); self-applying DESIGN-Qs; the atp-adp transfer-conservation-invariant question (reserved by C166 §D for the next **atp-adp** audit — explicitly NOT inherited here).

---

## 1. Methodology

Frozen target, **moving corpus** — the mirror of the C164/C166 windows, so §B is sized to the **delta**, not the target. Policy review APPROVED first-pass with 7 binding conditions (independent freeze proof; one-cited-adjudication-per-surface with no wholesale pass on the frozen 444 lines; whitepaper grep-bounded/route-only; carries re-anchored not re-adjudicated; verifier baselining green AND red; zero-mutation exit check; no padding on a clean result). All honored; evidence below.

**Freeze — proven this fire, not inherited** (binding condition 1): blob identity at live HEAD vs the C133 cutoff commit `70e3ddcc`:

| Artifact | HEAD blob | Cutoff blob | State |
|---|---|---|---|
| `SOCIETY_METABOLIC_STATES.md` | `5e3f7203` | `5e3f7203` | **FROZEN** (byte-identical since C55 `a504ea41`, ~26 days, 4th consecutive frozen window) |
| SDK `web4/metabolic.py` | `d3d31446` | `d3d31446` | FROZEN |
| `test-vectors/metabolic/society-metabolic-states.json` | `855eedb5` | `855eedb5` | FROZEN |
| `SOCIETY_SPECIFICATION.md` (B14 anchor) | `45781960` | `45781960` | FROZEN |
| `web4-society-authority-law.md` (B15/C58-B10 anchor) | `02ab3a42` | `02ab3a42` | FROZEN |

**Window**: 64 commits / 134 files since `70e3ddcc` (2026-07-03) — whitepaper full rewrite + pre-rewrite archive (`4bd36e8a`), web4-core 0.3.0 publish (crates.io + PyPI, 2026-07-09) + r6 pre-publish fix (#498), hub security hardening + deployment kit (~1,643 insertions), 4 sibling core-spec remediations (atp-adp C151 #477, reputation C157 #484, acp C159 #487, mrh C163 #491), 2 NEW ontology files (`role-extension.ttl`, `role-extension-schema.md`).

**Verifier baseline** (binding condition 5): the metabolic lexicon grep (`metabolic|hibernat|torpor|molt|estivat`) was baselined **green** on the two known-positive artifacts (target: 59 hits; `metabolic.py`: 122 hits) and **red** on a known-negative (`mrh-tensors.md`: 0) before being used as evidence on any moved surface.

Severity: HIGH / MEDIUM / LOW / INFO. Disposition: AUTONOMOUS-ACTIONABLE / DESIGN-Q / CROSS-TRACK.

---

## 2. §A — Prior-Finding Verification

### A.1 C55 remediations (5 autonomous, PR #326) — 5/5 HELD
Target byte-frozen since `a504ea41` → HELD by construction; each re-confirmed present by first-hand live re-read this fire: **B2** §2.4 wake bullet (L91, agrees with §3.1 L184 + §4.1 L229) · **B10** §7.2 #1 Wake-Trigger Flooding incl. hibernation `new_citizen` path (L382) · **B12** §7.1 "Sentinel heartbeat + timeout wake" row (L373) · **B13** §10 conformance precision (see A.4) · **B16** §3.1 transition cross-ref symmetry (L173–L189 `(see §4.1 …)` cites all present). **0 REGRESSED.**

### A.2 #-Regression sweep (C133→C168 window)
No commit in the window touched the target, `metabolic.py`, the test vector, or either sister-doc anchor (blob table above). The frozen window is regression-free by construction; all moved siblings are adjudicated in §B.

### A.3 Standing carries — re-anchored at live HEAD (binding condition 4: anchor-existence, not re-adjudication)

**SDK cross-track (4) — ALL STILL STALE** (`metabolic.py` frozen; anchors re-read verbatim this fire):
| ID | Site | State |
|---|---|---|
| **B1** | `metabolic.py:147` `Transition(HIBERNATION, ACTIVE, "external witness or timeout")` | STILL STALE — omits `new_citizen` + 90-day that spec §3.1 L184 carries |
| **B3** | `metabolic.py:207` `Formula (§6.1): Daily ATP Cost = …` | STILL STALE — spec §6.1 L341 says "Hourly" |
| **B4** | `metabolic.py:110` TORPOR `description="Frozen + alert bonus"` | STILL STALE — spec §5.1 L299 is "Frozen" |
| **B11** | `metabolic.py:412-413` comment "Rest: queued" vs `return state == ACTIVE` | STILL STALE |

**Sister-doc cross-track (2) — OPEN, snapshot-stable by blob identity**: **B14** (SOCIETY_SPEC §1.4 "MUST also conform" vs target "Proposed Standard" + §10 SHOULD) and **B15** (SAL §3.6 L141 dormant list omits Rest; dual-anchored C98-B9). Both anchor files byte-frozen in the window; C134 (SAL 3rd-delta, 2026-07-04) independently re-verified B15 and C58-B10 in the interval.

**Design-Q (14) — ALL STILL OPEN by freeze**: C21 H1, H3, M3, M5, M7, L4, L5, L7 + C54 B5, B6, B7, B8, B9, B14-normative-strength. None self-resolved.

**C96-E1 (INFO, cross-track → atp-adp §3.3)** — anchor re-verified at live HEAD: the §3.3 demurrage maintenance-discharge note is present at `atp-adp-cycle.md:325-330` (content intact; minor line drift from the historically cited `:329` — same note, re-anchored per [[feedback_prior_finding_path_provenance]]). C151's edit did NOT move §3.3 (see B.1). STANDS.

**C58-B10 (DESIGN-Q, defer-vs-wake)** — two-sided contradiction re-verified: SAL §3.6 "dormant states SHOULD defer" (file frozen `02ab3a42`) vs target §3.1 L184 / §4.1 L229 `wake_on: ["new_citizen", …]` (re-read live). STANDS; operator bundle.

**M7 (ontology absence) — sweep REFRESHED against the 2 NEW ontology files** (C166 C17-M1 method: a new ontology file is not an ontology fix, but the sweep must re-run against it): loose-pattern `metabolic|hibernat|torpor|molt|estivat` across `web4-standard/ontology/` → only the 2 pre-existing adjective `rdfs:comment` hits (`web4-core-ontology.ttl` L85, L179 — both ATP/ADP-cycle prose); `role-extension.ttl` + `role-extension-schema.md` add **no** metabolic class or predicate. **M7 absence HOLDS.**

### A.4 §10 conformance (C56 claim re-read)
Target and test vector both blob-frozen → C133's full 12-vector recompute remains valid. Claims re-read token-by-token this fire: §4.1 `state_multipliers` ↔ §2.x energy costs ↔ §5.1 trust-effect column ↔ §10 category counts (3/3/4/2 = 12) all agree; the 6-of-8-driven-states nuance and `molt_success_rate` input note exact. 0 discrepancies.

---

## 3. §B — Corpus-Delta + Inbound-Carry Sweep

**Result: 0 net-new defects on the target (3rd consecutive fully-clean metabolic delta); 1 net-new LEDGER finding (C168-N1, §4).** Eight moved surfaces, one cited adjudication each; no agent or pass was pointed at the frozen 444 lines (binding condition 2).

### B.1 atp-adp C151 (#477) — DISJOINT (moved hunk cited)
The window hunk is at `atp-adp-cycle.md:211-215`: the transfer-conservation note's scope phrase changed "scopes only ATP→ADP transfers" → "scopes only ATP transfers between entities (§6.3)". Disjointness, proven two ways: (1) **absence of surface** — target greps: `transfer*` = 0, `fees` = 0; the two `conservation` hits (L24, L97) are Torpor's "**Emergency Conservation**" — *energy-saving* sense, not the transfer-conservation invariant (the near-collision is exactly why the hits were hand-read, not counted); (2) **carve-out family** — metabolic's only atp-adp coupling is §6.1's hourly maintenance discharge riding the **§3.3** demurrage carve-out (C96-E1), and C151's hunk edits the *parallel* transfer-conservation note at L211-215, not §3.3 (§3.3 confirmed unmoved, A.3). The C166 §D transfer-conservation-invariant question is **reserved for the next atp-adp audit** and deliberately not adjudicated here.

### B.2 reputation C157 (#484) — DISJOINT
Window hunk at `reputation-computation.md:759-763` (Sybil-analysis claim softened to SHOULD + §10 forward-cite). Target grep `\breputation\b` = **0** — the metabolic spec's trust surface (§5.1 update/decay rates, §5.2 reliability score) nowhere names reputation, and the hunk touches neither decay nor scoring semantics.

### B.3 acp C159 (#487) — DISJOINT
Three ≤3-line hunks (`grant.scope.r6Caps.resourceCaps` path fix; trust-gaming table row; witness-deficit comment rephrase). Target grep `\bACP\b|agentic` = **0**.

### B.4 mrh C163 (#491) — DISJOINT
Single hunk: §4.2 SDK-note "Two API differences" → "Three" (mrh-tensors.md:198-211). Target grep `\bMRH\b|markov` = **0**. (The standing mrh guard — re-derive the three signatures from `mrh.py`, not the note — belongs to the next **mrh** pass, not here.)

### B.5 NEW ontology files (`role-extension.ttl`, `role-extension-schema.md`) — DISJOINT
Metabolic lexicon = **0** in both; consumed by the A.3 M7 sweep refresh. No metabolic class introduced, none mis-introduced.

### B.6 web4-core Rust (18 commits; 0.3.0 published 2026-07-09; #498 r6 fix) — window-DISJOINT; surfaced C168-N1
The crate's only metabolic surface is `society.rs`'s `pub enum MetabolicState` (`society.rs:37`). Its **window** diff is two removed imports (`crypto::KeyPair`, `lct::{EntityType, Lct}`); the enum block is **byte-identical from its birth commit `82438958` (2026-05-13) through HEAD** (diff-verified). `r6.rs`/`role.rs`/`role_extension.rs`/`lib.rs`: metabolic lexicon = 0. So the window itself moves nothing metabolic — but the mandatory adjudication of this surface exposed a **ledger omission** predating the window, recorded at its true strength as **C168-N1** (§4).

### B.7 Whitepaper full rewrite (`4bd36e8a`) — NO DEFECT; INFO coverage note (route-only, binding condition 3)
New `whitepaper/sections/`: metabolic lexicon = **0** (baselined grep). The pre-rewrite archive's mentions were (a) hardbound-CLI implementation-status bullets (exec-summary, appendices) and (b) the conclusion's own honest-assessment flagging bio-vocabulary (incl. "metabolic states") as a credibility liability for skeptical readers. The rewrite dropping the vocabulary is *consistent with that self-critique*, not a contradiction of the spec. Recorded as an INFO coverage note for the whitepaper/publish track (the standard's metabolic subsystem currently has zero whitepaper presence); **no carry, no action required.**

### B.8 Hub (~1,643 insertions: security hardening #471/#472/#473/#479, deployment kit #481) — DISJOINT
`law.rs`/`state.rs`/`rest.rs`/`mcp.rs`/`main.rs` window hunks contain **zero** lines matching `metabolic|society.*state|MetabolicState` (cited grep over the window diff). `admin.rs:173` (which displays `society.state` as "Metabolic state") is **unmoved** in the window — it is a facet of C168-N1, not a new surface.

### B.9 Inbound sibling-audit carries (C134–C166 interval docs)
Grep + hand-read of every interval audit mentioning metabolic: C134 (SAL 3rd-delta) executed the metabolic no-op remediation slot and re-verified C58-B10/B15 (2026-07-04); C135/C138 cite metabolic only in the frozen-target-pattern narrative; C164/C166 only in rotation bookkeeping. **No new carry routed to metabolic in the interval.**

---

## 4. Net-New Findings

### C168-N1 — Sprint-49 cross-language Finding #3 / "Operator Decision #1" (MetabolicState model) was never promoted into the standing carry ledger — MEDIUM, class-a LEDGER, CROSS-TRACK routing

**The net-new defect is the ledger omission, not the divergence** ([[feedback_prose_is_not_ledger]]: ask "is this NEW?" before "is this TRUE?"). Novelty check on the underlying divergence **fails deliberately**: it is pre-existing and pre-adjudicated — `docs/audits/cross-language-society-role-atp-r6-alignment-2026-05-14.md` Finding #3 rated it **HIGH** and §"Operator Decision Required" Decision #1 posed a 3-option A/B/C question; the enum shipped publicly in web4-core **0.2.0 (crates.io, 2026-05-15 — one day after that doc)** and again in 0.3.0 (in-window). What IS new: **no C-series audit, and not the standing carries ledger, carries Finding #3 or Decision #1** — repo-wide grep for the doc's name across `docs/audits/C*.md` = 0; the ledger's SOCIETY_METABOLIC section lists only the C21/C54 carries. The omission is sharpened by the counterfactual: **sister Finding #2 (solo-founder genesis) from the SAME document WAS promoted** and has a full C-series life (C92-N1 → C131 sharpening → C164 restoration). Finding #3 — rated one severity class higher — fell out of tracking for ~8 weeks and was published twice meanwhile.

**Facets re-derived at live HEAD** (so the promoted carry rests on current ground truth, not the 2026-05-14 snapshot):
1. `web4-core/src/society.rs:37` `enum MetabolicState { Genesis, Bootstrap, Operational, Dormant, Sunset }` — variant intersection with the spec's eight states (§2.1–§2.8) = **∅** (only "Dormant" echoes the spec's *category* of dormant states, and as a single state, not the category).
2. `society.rs:33-34` doc-comment: "Metabolic state of a society (lifecycle phase). **Reference: `SOCIETY_METABOLIC_STATES.md`**" — a published-crate reader following the cite lands on a spec defining a **different state machine**. The variants actually mirror SOCIETY_SPEC §1.3's Formation Process (Genesis Event → Bootstrap Phase → …) / ISP lifecycle; the parenthetical "(lifecycle phase)" concedes as much.
3. Name collision across live product artifacts: SDK `web4/metabolic.py` `MetabolicState` (8 spec states) vs crate `MetabolicState` (5 lifecycle phases), both under the web4 umbrella; hub `admin.rs:173` surfaces the crate enum to operators labeled "Metabolic state".
4. **Correction to Finding #3's Python half**: the 2026-05-14 doc described Python `metabolic.py` as having 7 states (ACTIVE, GROWING, STABLE, …) — but the SDK module (born 2026-03-17, PR #23) already had the spec's 8 states then and now; `GROWING` exists only in `simulations/` and `archive/` code. The doc evidently described a non-SDK artifact. **Materially, the Python side already implements Decision #1's Option C** (`SocietyPhase` lifecycle enum at `society.py:81` + orthogonal spec-matching metabolic module), which shrinks the open decision to the **Rust naming/mis-cite + mapping question**.

**Adversarial refutation attempts (flagship discipline, [[feedback_refute_your_best_finding]])**: (a) *"Decision #1 was resolved elsewhere"* — repo-wide grep for "Decision #1": only the birth doc; Sprints 50–52 consumed Decision #2's territory (roles/bootstrap), and no commit has touched the enum since birth. NOT REFUTED. (b) *"'Metabolic' legitimately means lifecycle in the corpus idiom"* — the loose idiom exists (hardbound "metabolic-state-dependent recharge", archived session code), but the crate cites the **spec file** specifically, and the spec's §2 is the canonical definition; the cross-language doc itself already judged the divergence HIGH rather than idiomatic. NOT REFUTED. (c) *"It's already tracked"* — carries ledger + C-series greps = 0; Known-Gaps tracks the Sprint-47 T3/V3 doc (N2/K4) but not Sprint-49 Finding #3. NOT REFUTED. Survives as a LEDGER finding.

**Disposition**: (i) **Promoted into the standing carry ledger this fire** (auditor memory ledger, SOCIETY_METABOLIC section — the fix for a ledger defect is ledger-side and within audit authority; no repo mutation). (ii) The underlying Decision #1 routes to the **operator DESIGN-Q bundle** with the live-HEAD facets above (recommended framing: Python is de-facto at Option C; the crate-side fix is a publish-track rename — e.g. `LifecyclePhase`/`SocietyPhase` — or a re-cite to `SOCIETY_SPECIFICATION.md §1.3`/ISP, semver-relevant since the enum serializes into published artifacts). (iii) NOT autonomous this turn: cross-track (publish-track crate), and an audit turn is zero-mutation regardless.

### INFO (no carry): whitepaper metabolic coverage
See B.7 — recorded, closed-as-recorded, route-only.

---

## 5. §C — Carries Reconciliation

**All standing carries STAND** (frozen target/anchors; every one re-anchored live this fire, §A.3): C21 design-Q ×8 · C54 design-Q ×6 · SDK cross-track B1/B3/B4/B11 (bundle for a future SDK-track pass) · sister-doc B14/B15 · C96-E1 (anchor re-verified at `atp-adp:325-330`) · C58-B10 (two-sided, operator bundle) · M7 (sweep refreshed vs 2 new ontology files; absence holds).

**New at C168**: **C168-N1** (MED, LEDGER) — recorded above; its promotion adds the Sprint-49 **Finding #3 / Decision #1** item (with live-HEAD facets) to the SOCIETY_METABOLIC ledger section as an operator DESIGN-Q + publish-track cross-track. **0 elevated, 0 resolved.** None of the standing carries gate a normal turn; all route to the one-decision operator memo when the operator engages.

**C169 (next remediation slot) = DECLARED NO-OP on the spec side.** 0 autonomous spec defects exist: the target is frozen and clean; C168-N1's ledger half is already applied (memory-side) and its substance is operator/publish-track. Per the C133→C134 and C166→C167 precedents, the C169 slot should confirm this declaration via step-(a) and advance the rotation **+2 to C170 = SAL** (`web4-society-authority-law.md`) **4th-delta** (lineage C23 → C58 → C98/C99 → C134 → C170; last audited 2026-07-04). [Order: SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, **SAL**, LCT, ISP, entity-types, errors, security, registries, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap.]

---

## 6. §D — Method Notes

1. **3rd consecutive fully-clean metabolic delta** (C96, C133, C168). The frozen-target steady-state holds a 4th window: §A is verification, §B's yield is entirely on what moved. No finding was manufactured against the frozen 444 lines (binding condition 7).
2. **The LEDGER class recurs — 3rd instance in 5 fires** (C164-N1: dropped §C promotion; C166-N1: ledger-locality; C168-N1: a **pre-C-series** audit doc's operator-decision item never entered the C-series carry system at all). New sub-pattern: the Sprint-47/49 cross-language audit docs predate the C-series ledger discipline, and their "Operator Decision Required" sections are a structural blind spot — Finding #2 survived only because SDK code *cited it in a docstring*. One confirmed orphan (Finding #3, promoted this fire). A one-time sweep of pre-C-series audit docs' decision sections is worth an operator/lead decision; deliberately NOT self-executed this turn (scope discipline).
3. **A grep near-collision was caught by hand-reading, not counting**: the target's two `conservation` hits are Torpor's *energy* "Emergency Conservation", not the atp-adp transfer-conservation invariant — counting alone would have manufactured an intersect where none exists ([[feedback_enumeration_and_grep_hypotheses]]).
4. **Ground-truth correction recorded inside the promoted carry** (N1 facet 4): the cross-language doc's Python description matched `simulations/` code, not the SDK module. Promoting a stale carry verbatim would have routed the operator a decision whose Python half is already resolved — re-derivation at live HEAD is what made the promotion honest ([[feedback_prior_finding_path_provenance]] extended to *inbound* pre-C-series items).
5. **Reserved guards honored**: the atp-adp conservation-invariant question (C166 §D) and the mrh three-signatures guard were named, located adjacent to this window's surfaces, and left for their owning passes.

---

## 7. Conclusion

C168 is the **4th delta re-audit** of `SOCIETY_METABOLIC_STATES.md`. Target byte-frozen since C55 (`a504ea41`), proven by blob identity this fire, alongside frozen SDK, test vector, and both sister-doc anchors.
- **§A**: 5/5 C55 remediations HELD; window regression-free by construction; all carries re-anchored live (SDK ×4 still-stale verbatim; B14/B15 snapshot-stable by blob; 14 design-Q open; C96-E1 anchor intact at `atp-adp:325-330`; C58-B10 two-sided; M7 sweep refreshed vs the 2 new ontology files — absence holds); §10 conformance claims re-read exact.
- **§B**: 8 moved surfaces, one cited adjudication each → **0 net-new defects on the target (3rd consecutive fully-clean delta)**. atp-adp/reputation/acp/mrh/ontology/hub all DISJOINT by cited hunk + absence-of-surface; whitepaper rewrite = INFO coverage note only.
- **§4**: **C168-N1 (MED, LEDGER)** — Sprint-49 cross-language Finding #3 (Rust `MetabolicState` = 5 lifecycle phases citing the metabolic spec; published since 0.2.0) and its Operator Decision #1 were never promoted into the carry ledger while sister Finding #2 was; promoted this fire with live-HEAD facets (incl. the correction that Python is already at Option-C shape). Flagship survived 3 refutation attempts.
- **§C**: all carries STAND; 1 promoted, 0 elevated, 0 resolved. **C169 = declared NO-OP on the spec side; rotation advances +2 to C170 = SAL 4th-delta.**
- **ZERO mutation of spec/SDK/crate/sister files; this audit document is the only web4-repo write.**

---

*Audit produced under Autonomous Session Protocol v2 by legion-web4-20260710-000036 (LEAD, slot 000036). Policy-review APPROVED first-pass with 7 binding conditions — all honored and evidenced inline.*
