# C244 — SOCIETY_METABOLIC_STATES.md 6th-Delta Re-Audit (C21→C54/C55→C96→C133→C168→C206→C244)

**Audit ID**: C244
**Date**: 2026-07-21
**Target**: `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` (444 lines, v1.0.0, "Proposed Standard")
**Lineage**: C21 first-pass (2026-05-29) → C54 first-delta (2026-06-14) → C55 remediation (PR #326, `a504ea41`) → C96 2nd-delta (0 net-new) → C133 3rd-delta (0 net-new) → C168 4th-delta (0 net-new on target; C168-N1 ledger promotion, #500) → C206 5th-delta (0 net-new; PR #535, `c2324eb6`) → **C244 (this, 6th delta)**
**Rotation provenance**: C242 (dictionary 6th-delta, PR #562, MERGED `2293f83b`) found 0 autonomous defects and declared C243 a NO-OP in its §D, advancing the round-robin +2 to the next-oldest file = SOCIETY_METABOLIC (last audited C206, 2026-07-17). Step-(a) re-confirmed this fire: #562 merged with no changes requested; the Legion queue (`SESSION_FOCUS.md` §"In motion" 0a–0d) is empty for Legion (0a hestia-owned; 0b/0c/0d all SERVED/CLOSED); no operator DESIGN-Q answered and no metabolic-relevant authorization in the interval.
**Auditor session**: legion-web4-20260721-180036 (LEAD, slot 180036)
**Out of scope**: spec/SDK/crate/sister edits (audit turn — zero mutation); M7 TTL drafting; self-applying DESIGN-Qs; C168-N1's operator/publish-track half (Rust `MetabolicState` rename/re-cite); the one-time pre-C-series decision-section sweep (operator-gated, C168 §D).

---

## 1. Methodology

Frozen target, **frozen immediate corpus** — a 6th consecutive frozen window, and (distinct from C206) a window in which *both tracked sister anchors are also static*. At C206 the SOCIETY_SPEC and SAL blobs had both MOVED (W4IP §7.3 Correction & Enforcement + Effector role registration), so §B there carried real adjudication weight against moving surfaces. This window they are byte-static since C206 — the delta's real content is the 33-commit corpus motion *elsewhere* (hub constellation, LCT authority-ratchet/citizenship/vouching, oracle-set TTL, web4-policy) plus 15 sibling audit docs, none of which touch the metabolic surface. §A is verification; §B is sized to the delta, not the target. Policy review APPROVED first-pass with method reminders honored inline: genuine-mirror gate before any `society.rs` divergence claim; re-derive the consumer set at live HEAD before declaring §B clean; refute-by-default, one lens per candidate; zero-mutation exit; do not manufacture findings on a clean window.

**Freeze — proven this fire by blob identity at live HEAD `2293f83b` vs the C206 cutoff commit `c2324eb6`:**

| Artifact | HEAD blob | C206 blob | State |
|---|---|---|---|
| `SOCIETY_METABOLIC_STATES.md` | `5e3f7203` | `5e3f7203` | **FROZEN** (byte-identical since C55 `a504ea41`, ~34 days, 6th consecutive frozen window) |
| SDK `web4/metabolic.py` | `d3d31446` | `d3d31446` | FROZEN |
| `test-vectors/metabolic/society-metabolic-states.json` | `855eedb5` | `855eedb5` | FROZEN |
| `SOCIETY_SPECIFICATION.md` (B14 anchor) | `2ad453ba` | `2ad453ba` | **FROZEN** (moved at C206, static since — §B.1) |
| `web4-society-authority-law.md` (B15/C58-B10 anchor) | `0849ebbe` | `0849ebbe` | **FROZEN** (moved at C206, static since — §B.2) |
| `web4-core/src/society.rs` (C168-N1 mirror) | `17112f05` | `17112f05` | FROZEN |
| SDK `society.py` / `role.py` / `__init__.py` (consumers) | `e7383124` / `735bab17` / `3fda03c6` | same | FROZEN |
| `atp-adp-cycle.md` (C96-E1 anchor) | `2d060579` | `2d060579` | FROZEN |
| `web4-core-ontology.ttl` (M7 sweep) | `fc4b4c36` | `fc4b4c36` | FROZEN |

**Window**: 33 commits since `c2324eb6` (2026-07-17). Of these, 15 are audit docs (C208 SAL → C242 dictionary; no spec mutation). Real code/spec movers: hub constellation enrollment registry + presented-key retire (#560/#561), pair-message sidecar (#553), oracle consult/write sets on `role-extension.ttl` (#547), `send_secret` content-blind relay (#545), LCT `authority_ratchet` (#544), operational-key vouching (#540), citizenship-as-ledger-reference (#538), W4IP `web4-policy` (#525), t3-v3 §1.1 cross-ref (#531). None land on a metabolic surface (proven below).

**Verifier baseline** ([[feedback_enumeration_and_grep_hypotheses]] — a grep is a silent-failing hypothesis; baseline it before use): the metabolic-lexicon grep (`metabolic|hibernat|torpor|molt|estivat|MetabolicState`) baselined **positive** on the two known-positive frozen artifacts (target: 67 matching lines; `metabolic.py`: 124) and on the mirror (`society.rs`: 15, all from the `MetabolicState` enum — this is a known-*positive*, the C168-N1 surface, not a negative), and **red** on known-negatives in the window (the #547 `role-extension.ttl` diff, the #544 `lct.rs` diff, `web4-policy/src/lib.rs`: all 0) before being used as evidence on any moved surface. (Note the line-count differs from C206's reported 59 because the blob is byte-identical — the count is a flag/pattern artifact, not a content change; blob identity is the freeze proof, not the grep tally.)

Severity: HIGH / MEDIUM / LOW / INFO. Disposition: AUTONOMOUS-ACTIONABLE / DESIGN-Q / CROSS-TRACK.

---

## 2. §A — Prior-Finding Verification

### A.1 C55 remediations (5 autonomous, PR #326) — 5/5 HELD by construction
Target byte-frozen since `a504ea41` (blob `5e3f7203`, proven §1) → all five HELD by construction: **B2** §2.4 wake bullet (external witness / new-citizen / 90-day timeout) · **B10** §7.2 #1 Wake-Trigger Flooding incl. hibernation `new_citizen` path · **B12** §7.1 "Sentinel heartbeat + timeout wake" row · **B13** §10 conformance precision · **B16** §3.1 transition cross-ref symmetry. C206 spot-re-read all five at line level and found 0 REGRESSED; the blob has not moved since, so that read stands verbatim. **0 REGRESSED.**

### A.2 #-Regression sweep (C206→C244 window)
No commit in the 33-commit window touched the target, `metabolic.py`, or the test vector (blob table §1). The two sister anchors did **not even move** this window (unlike C206) — both byte-static since C206. Whole-window metabolic-lexicon diff (`git diff c2324eb6..HEAD`, added/removed lines) resolves to **audit-doc prose only** — C208/C210/C216/C218/C242 markdown discussing metabolic as a frozen sibling; **0 lines in any spec, SDK, crate, ontology, or test file**. The frozen window is regression-free by construction.

### A.3 Standing carries — re-anchored at live HEAD

**SDK cross-track (4) — ALL STILL STALE** (`metabolic.py` frozen `d3d31446`; stale by construction):
| ID | Site | State |
|---|---|---|
| **B1** | `metabolic.py:147` `Transition(HIBERNATION, ACTIVE, "external witness or timeout")` | STILL STALE — omits `new_citizen` + 90-day (spec §3.1 L184) |
| **B3** | `metabolic.py:207` `Formula (§6.1): Daily ATP Cost` | STILL STALE — spec §6.1 L341 says "Hourly" |
| **B4** | `metabolic.py:110` TORPOR `description="Frozen + alert bonus"` | STILL STALE — spec §5.1 L299 is "Frozen" |
| **B11** | `metabolic.py:412-413` comment "Rest: queued" vs `return state == ACTIVE` | STILL STALE |

**Sister-doc cross-track (2) — OPEN, re-anchored by blob identity this time** (both sister blobs static since C206, so the C206 line-content re-anchoring holds verbatim):
- **B14** (SOCIETY_SPEC §1.4 "Implementations … MUST also conform to the metabolic-states specification" vs target "Proposed Standard" + §10 SHOULD): `SOCIETY_SPECIFICATION.md` frozen `2ad453ba` → the §1.4 clause (`:89`, plus eight-state paragraph `:87` and cross-refs `:37/:319/:322`) is byte-frozen. Substance HELD. (C240, SOCIETY_SPEC 6th-delta, 2026-07-21, independently re-confirmed the file byte-frozen and clean — §B.4.)
- **B15/C58-B10** (SAL §3.6 dormant list omits Rest; "dormant states SHOULD defer" vs target wake): `web4-society-authority-law.md` frozen `0849ebbe` → §3.6 (`:138-141`; dormant list `(Sleep, Hibernation, Torpor, Estivation)` L140; "dormant states SHOULD defer" L141) byte-frozen. Both HELD.

**Design-Q (14) — ALL STILL OPEN by freeze**: C21 H1, H3, M3, M5, M7, L4, L5, L7 + C54 B5, B6, B7, B8, B9, B14-normative-strength. None self-resolved.

**C96-E1 (INFO, cross-track → atp-adp §3.3)** — anchor stable; `atp-adp-cycle.md` frozen `2d060579` (untouched in window; independently re-confirmed frozen at C228, atp-adp 5th-delta). STANDS.

**C58-B10 (DESIGN-Q, defer-vs-wake)** — two-sided contradiction re-verified: SAL §3.6 L141 "dormant states SHOULD defer" (frozen, §B.2) vs target §3.1 L184 / §4.1 L229 `wake_on: ["new_citizen", …]` (frozen). STANDS; operator bundle.

**M7 (ontology absence) — sweep REFRESHED against the window's ontology movement**: `role-extension.ttl` was MODIFIED in-window (#547 oracle consult/write sets), so it was the sweep candidate. Loose-pattern `metabolic|hibernat|torpor|molt|estivat` across `web4-standard/ontology/` at HEAD → `role-extension.ttl` = **0 hits**; only the 2 pre-existing adjective `rdfs:comment` hits in `web4-core-ontology.ttl` (frozen `fc4b4c36`, ATP/ADP-cycle prose). #547 introduces **no** metabolic class or predicate. **M7 absence HOLDS.**

### A.4 §10 conformance (C56 claim re-read)
Target and test vector both blob-frozen → C133's 12-vector recompute remains valid; C168/C206's token-by-token claim re-read stands (categories 3/3/4/2 = 12 multipliers; 6-of-8-driven-states nuance; `molt_success_rate` input). 0 discrepancies.

---

## 3. §B — Corpus-Delta + Inbound-Carry Sweep

**Result: 0 net-new defects on the target (5th consecutive fully-clean metabolic delta — C96, C133, C168, C206, C244).** Every real code mover adjudicated DISJOINT with one cited basis; the frozen sister anchors did not move; no agent or pass was pointed at the frozen 444 lines.

### B.1 SDK/crate consumer set — re-derived at live HEAD, all frozen (method guard)
The "SDK mirror" is not a fixed set — re-derived at live HEAD ([[feedback_prose_is_not_ledger]] / method guard). Consumers of the metabolic state machine at HEAD: `metabolic.py`, `society.py`, `role.py`, `__init__.py` (Python SDK), `society.rs` + `lib.rs` (Rust `web4-core`). Window state:
- `metabolic.py` `d3d31446`, `society.py` `e7383124`, `role.py` `735bab17`, `__init__.py` `3fda03c6`, `society.rs` `17112f05` — **all FROZEN**.
- `lib.rs` MOVED (`017df871`→`95b74ec3`) but the change is 2 lines and the **metabolic/society export line is untouched** — `git diff c2324eb6..HEAD -- web4-core/src/lib.rs` has no `[+-]` line matching `society|metabolic`; `pub use society::{MetabolicState, Society}` (L107) and the prelude re-export (L126) are byte-unchanged at HEAD. **No net-new consumer**: the added-files sweep (`--diff-filter=A`) for `MetabolicState|Hibernation|Estivation|Torpor|Molting` returned empty.

### B.2 SOCIETY_SPEC (B14 anchor) — FROZEN this window; C240 re-confirms
Unlike C206 (blob moved via #522 §7.3), the blob is **static since C206** (`2ad453ba`). C240 (SOCIETY_SPEC 6th-delta, 2026-07-21, this same corpus HEAD) independently proved it byte-frozen and CLEAN, and its §A/§B route **nothing** to metabolic (grep `metabolic` in the C240 audit doc = 0). B14 HELD by blob identity; no re-adjudication required.

### B.3 SAL (B15/C58-B10 anchors) — FROZEN this window
Blob static since C206 (`0849ebbe`). §3.6 (dormant list / defer clause) byte-frozen. C208 (SAL 5th-delta) was the last SAL mover-adjudication; nothing since has touched it. B15 and C58-B10 HELD by blob identity.

### B.4 Real code movers — DISJOINT, one cited basis each
- **hub constellation #560/#561** (`hub/…/rest.rs`, enrollment registry + presented-key retire): metabolic lexicon in the diff = 0. Constellation device-fact resolution is a hub-membership concern; it does not read, gate, or reference the society metabolic state machine. DISJOINT.
- **LCT `authority_ratchet` #544 / citizenship #538 / operational-key vouching #540** (`lct.rs`, `society.rs`… — note `society.rs` blob is frozen, so #538/#540 did not touch it): metabolic-lexicon diff in `lct.rs` = 0. The ratchet is monotone sovereign-authority accounting; citizenship-as-ledger-reference and key-vouching are LCT-layer identity primitives. None couple to metabolic state. DISJOINT. (Independently: C224 web4-lct 5th-delta and C210 LCT 5th-delta adjudicated these movers under the LCT lens; neither routed anything to metabolic.)
- **oracle consult/write sets #547** (`role-extension.ttl`): 0 metabolic hits (M7 sweep, §A.3). Orthogonal to the metabolic surface. DISJOINT.
- **`send_secret` #545 / pair sidecar #553** (hub relay/messaging): metabolic lexicon = 0. Content-blind member→member transport; no metabolic coupling. DISJOINT.
- **W4IP `web4-policy` #525** (`web4-policy/src/lib.rs`): 0 metabolic hits. C228 (atp-adp 5th) and C232 (reputation 6th) already adjudicated the W4IP enforcement framework; the C232-N1 `reputation.delta.category` seam is a recognition→response reputation concern with **no metabolic referent** (grep `metabolic` in `web4-policy/src/lib.rs` = 0). DISJOINT — routed, not duplicated.
- **t3-v3 §1.1 #531** (`t3-v3-tensors.md`): metabolic lexicon = 0. The metabolic trust surface (§5.1/§5.2 rate modulations) does not reference T3/V3 tensor structure. DISJOINT.

### B.5 society.rs mirror — C168-N1 re-anchored, HELDs verbatim (frozen)
`society.rs` frozen `17112f05`; window diff for the enum block is empty. Re-anchored live at HEAD:
- `society.rs:37` `pub enum MetabolicState { Genesis, Bootstrap, Operational, Dormant, Sunset }` — variant intersection with the spec's eight states (§2.1–§2.8: Active, Rest, Sleep, Hibernation, Torpor, Estivation, Dreaming, Molting) = **∅** (only "Dormant" echoes the spec's *category*, and as a single variant, not the category).
- `society.rs:33-34` doc-comment `/// Metabolic state of a society (lifecycle phase). /// Reference: SOCIETY_METABOLIC_STATES.md` — a published-crate reader following the cite still lands on a spec defining a **different state machine** (the 5 variants mirror SOCIETY_SPEC §1.3 Formation Process / ISP lifecycle).
**C168-N1 persists un-remediated** — correctly: a publish-track crate rename/re-cite (`LifecyclePhase`/`SocietyPhase`, or re-cite to `SOCIETY_SPECIFICATION.md §1.3`), semver-relevant since the enum serializes into published web4-core artifacts; and an audit turn is zero-mutation regardless. C202 (SOCIETY_SPEC 5th) independently routed this residual here; no re-promotion needed.

### B.6 Inbound sibling-audit carries (C208–C242 interval docs)
Grep + hand-read of every interval audit mentioning metabolic:
- **C208 (SAL 5th), C210 (LCT 5th), C216 (errors 5th), C218 (security 5th), C242 (dictionary 6th)** — the five interval docs whose metabolic-lexicon diff lines are non-zero all name metabolic **incidentally**: rotation bookkeeping, frozen-sibling narrative, or the standing C58-B10/B15 two-sided carry re-logged verbatim (e.g. C208's SAL §3.6 ↔ SMS §4.1 row). **No new carry routed to metabolic.**
- **C240 (SOCIETY_SPEC 6th, 2026-07-21)** — 0 metabolic mentions; routes nothing here (§B.2).
- **C242 (dictionary 6th, 2026-07-21)** — its 18-sibling roundup (which includes C206 metabolic) confirms the siblings "route no item" cross-file; metabolic named only in the rotation-advance line ("Rotation advances (+2) to SOCIETY_METABOLIC_STATES = C244"). No carry.
- The **flagship refutation** (LCT §1.2 "Inspectable Evidence, Not Prescribed Trust" as a possible metabolic-surface conflict) was raised and refuted at C206; #531 (t3-v3 §1.1 cross-ref to §1.2) is the only §1.2-adjacent motion this window and its metabolic-lexicon diff = 0. Re-refuted on the same live ground: the metabolic trust surface (§5.1 update-rate/decay-rate/temporary-penalty; §5.2 reliability score) is **rate modulation by operational state**, not an admit/exclude trust threshold — there is no `confidence < X ⇒ exclude` construct in the frozen 444 lines for §1.2 to conflict with. **Charge REFUTED** ([[feedback_refute_your_best_finding]]).

---

## 4. Net-New Findings

**None.** 0 net-new defects; 0 net-new carries. C244 is the 5th consecutive fully-clean metabolic delta. C168-N1 (MED, LEDGER — Rust `MetabolicState` = 5 lifecycle phases citing the metabolic spec) HELDs verbatim, re-anchored at live HEAD (§B.5) — no re-promotion needed, no elevation warranted.

---

## 5. §C — Carries Reconciliation

**All standing carries STAND** (frozen target/SDK; sister anchors re-anchored by **blob identity** this window — both static since C206): C21 design-Q ×8 · C54 design-Q ×6 · SDK cross-track B1/B3/B4/B11 (bundle for a future SDK-track pass) · sister-doc B14 (`SOCIETY_SPECIFICATION.md:89`, blob-frozen; C240-reconfirmed) / B15 (`web4-society-authority-law.md:140-141`, blob-frozen) · C96-E1 (atp-adp §3.3 frozen `2d060579`) · C58-B10 (two-sided, operator bundle) · M7 (sweep refreshed vs in-window `role-extension.ttl` #547 — 0 hits; absence holds) · **C168-N1** (MED, LEDGER; re-anchored `society.rs:33-37`, frozen `17112f05`; operator DESIGN-Q + publish-track cross-track; C202-confirmed).

**0 net-new, 0 elevated, 0 resolved.** None of the standing carries gate a normal turn; all route to the one-decision operator memo.

**C245 (next remediation slot) = DECLARED NO-OP on the spec side.** 0 autonomous spec defects exist: the target is frozen and clean; C168-N1's ledger half is already recorded (memory-side) and its substance is operator/publish-track. Per the C133→C134 / C166→C167 / C168→C170 / C206→C207 precedents the C245 slot should confirm this via step-(a) and advance the rotation **+2 to C246 = SAL 6th-delta** (`web4-society-authority-law.md`; lineage C23→C58→C98/C99→C134→C170→C208→C246; last audited C208, 2026-07-17). [Order: SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, **SAL**, LCT, ISP, entity-types, errors, security, registries, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap.]

---

## 6. §D — Method Notes

1. **5th consecutive fully-clean metabolic delta** (C96, C133, C168, C206, C244) — and the **first since the sisters moved** where they are frozen *again*, so B14/B15 re-anchor by blob identity (the C206 line-content re-anchoring is now backed by a byte-static blob). A blob-frozen anchor since the last delta needs no re-adjudication; the discipline is proving the blob, not re-reading the clause.
2. **The window was busy but metabolically inert.** 33 commits, ~10 real code movers (hub constellation, LCT ratchet/citizenship/vouching, oracle-set TTL, web4-policy, t3-v3), 15 audit docs — and the whole-window metabolic-lexicon diff resolved to **audit-doc prose only, 0 spec/SDK/crate lines**. The single most efficient disjointness proof for a frozen target is the file-scoped lexicon diff over the window: it localizes every candidate to non-metabolic files before any per-mover reasoning.
3. **Consumer set re-derived at live HEAD, not assumed** ([[feedback_prose_is_not_ledger]] method guard). `lib.rs` moved — the reflex is "a crate mover ⇒ check the mirror"; the discipline is proving the *specific export line* untouched, which it was. No new consumer file referenced the state machine (`--diff-filter=A` sweep empty).
4. **C168-N1 correctly persists un-remediated.** The enum is byte-unchanged and still mis-cites the metabolic spec, but the fix is a publish-track crate rename (semver-relevant on serialized output) — outside a zero-mutation audit turn. Re-anchoring (not re-remediating) is the whole job here.
5. **Did not manufacture findings on a clean window** (policy-review standing reminder). The correct output of a busy-corpus-but-frozen-surface delta is a clean verdict cleanly recorded and the rotation advanced — not a strained net-new to justify the fire.
6. **Reserved guards honored**: the atp-adp conservation-invariant question (owned by the next atp-adp pass) and the mrh three-signatures guard (owned by the next mrh pass) were adjacent to neither this window's movers nor this frozen target — not adjudicated here.

---

## 7. Conclusion

C244 is the **6th delta re-audit** of `SOCIETY_METABOLIC_STATES.md`. Target byte-frozen since C55 (`a504ea41`, blob `5e3f7203`), proven by blob identity this fire alongside frozen SDK, test vector, both sister anchors, the Rust mirror, and the atp-adp/ontology anchors — the **entire immediate corpus is frozen since C206**.
- **§A**: 5/5 C55 remediations HELD by construction; window regression-free (whole-window metabolic-lexicon diff = audit-doc prose only); carries re-anchored live — SDK ×4 still-stale by freeze; B14/B15 re-anchored by **blob identity** (both sister files static since C206, C240-reconfirmed); 14 design-Q open; C96-E1 atp-adp anchor frozen; C58-B10 two-sided; M7 sweep refreshed vs in-window `role-extension.ttl` #547 (0 hits) — absence holds; §10 conformance exact.
- **§B**: consumer set re-derived at live HEAD (all frozen; `lib.rs` moved but metabolic export untouched; no new consumer); ~10 real code movers (hub constellation / LCT ratchet-citizenship-vouching / oracle-set TTL / send_secret / pair-sidecar / web4-policy / t3-v3) all DISJOINT by cited hunk + empty metabolic-lexicon diff; both sister anchors frozen (C240-reconfirmed clean, routes nothing here); society.rs mirror frozen. → **0 net-new defects (5th consecutive fully-clean delta)**. The LCT §1.2 trust-threshold charge re-refuted on live ground (metabolic §5 = rate modulation, not admit/exclude gate).
- **§4/§C**: **0 net-new findings.** C168-N1 (MED, LEDGER) HELDs verbatim, re-anchored at `society.rs:33-37` (frozen `17112f05`). All carries STAND; 0 elevated, 0 resolved. **C245 = declared NO-OP on the spec side; rotation advances +2 to C246 = SAL 6th-delta.**
- **ZERO mutation of spec/SDK/crate/sister files; this audit document is the only web4-repo write.**

---

*Audit produced under Autonomous Session Protocol v2 by legion-web4-20260721-180036 (LEAD, slot 180036). Policy-review APPROVED first-pass; method reminders (genuine-mirror gate, consumer-set re-derivation at live HEAD, sibling-prose check before "new", refute-by-default, zero-mutation, do-not-manufacture) honored and evidenced inline.*
