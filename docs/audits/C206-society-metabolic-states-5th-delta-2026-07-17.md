# C206 — SOCIETY_METABOLIC_STATES.md 5th-Delta Re-Audit (C21→C54/C55→C96→C133→C168→C206)

**Audit ID**: C206
**Date**: 2026-07-17
**Target**: `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` (444 lines, v1.0.0, "Proposed Standard")
**Lineage**: C21 first-pass (2026-05-29) → C54 first-delta (2026-06-14) → C55 remediation (PR #326, `a504ea41`) → C96 2nd-delta (0 net-new) → C133 3rd-delta (0 net-new) → C168 4th-delta (0 net-new on target; C168-N1 ledger promotion, #500) → **C206 (this, 5th delta)**
**Rotation provenance**: C204 (dictionary 5th-delta, PR #534, MERGED `53d8f038`) found 0 autonomous defects and declared C205 a NO-OP in its §D. Step-(a) re-confirmed this fire: #534 merged with no changes requested; the Legion queue (`SESSION_FOCUS.md` §"In motion" 0a–0d) is empty/in-motion/hestia-owned; no operator DESIGN-Q answered and no metabolic-relevant authorization in the interval. Per the C93→C94 / C165→C166 / C167→C168 precedents the no-op slot advances the round-robin +2 to the next-oldest file = SOCIETY_METABOLIC (last audited C168, 2026-07-10).
**Auditor session**: legion-web4-20260717-000036 (LEAD, slot 000036)
**Out of scope**: spec/SDK/crate/sister edits (audit turn — zero mutation); M7 TTL drafting; self-applying DESIGN-Qs; C168-N1's operator/publish-track half (Rust `MetabolicState` rename/re-cite); the one-time pre-C-series decision-section sweep (operator-gated, C168 §D).

---

## 1. Methodology

Frozen target, **moving corpus** — a 5th consecutive frozen window. §A is verification; §B is sized to the **delta**, not the target. Distinctive from C96/C133/C168: **the two tracked sister-doc anchors both MOVED this window** (SOCIETY_SPEC `45781960`→`2ad453ba`; SAL `02ab3a42`→`0849ebbe`), so §B carries real adjudication weight rather than resting on a byte-frozen corpus. Policy review APPROVED first-pass with method reminders honored inline: genuine-mirror gate before any `society.rs` divergence claim; check-if-a-sibling-delta-already-parked-it before recording "new"; refute-by-default, one lens per candidate; zero-mutation exit.

**Freeze — proven this fire, not inherited**: blob identity at live HEAD vs the C168 cutoff commit `8ac6edee`:

| Artifact | HEAD blob | C168 blob | State |
|---|---|---|---|
| `SOCIETY_METABOLIC_STATES.md` | `5e3f7203` | `5e3f7203` | **FROZEN** (byte-identical since C55 `a504ea41`, ~33 days, 5th consecutive frozen window) |
| SDK `web4/metabolic.py` | `d3d31446` | `d3d31446` | FROZEN |
| `test-vectors/metabolic/society-metabolic-states.json` | `855eedb5` | `855eedb5` | FROZEN |
| `SOCIETY_SPECIFICATION.md` (B14 anchor) | `2ad453ba` | `45781960` | **MOVED** — §B.1 |
| `web4-society-authority-law.md` (B15/C58-B10 anchor) | `0849ebbe` | `02ab3a42` | **MOVED** — §B.2 |

**Window**: 55 commits since `8ac6edee` (2026-07-10). Metabolic-relevant movers: the ratchet #529 (`ratchet.rs` NEW + `lib.rs` export); W4IP governance-immune-enforcement #521/#522/#523/#525 (Effector role, `notice|quarantine|correct|rehabilitate` response vocab, Coercive/Extractive category — landing in SOCIETY_SPEC §7.3 + SAL); LCT §1.2 "Inspectable Evidence, Not Prescribed Trust" #531; birth-certificate + attestation #527 (`attestation.rs` NEW, `lct.rs`); web4-core 0.4.0 `EntityType::Society` #516; reputation C195 remediation #526; five sibling 5th/4th-delta audits (mrh C200, presence C198, acp C196, SOCIETY_SPEC C202, dictionary C204).

**Verifier baseline**: the metabolic lexicon grep (`metabolic|hibernat|torpor|molt|estivat`) baselined **green** on the two known-positive artifacts (target: 59 hits; `metabolic.py`: 122 hits, both frozen) and **red** on known-negatives (`ratchet.rs`: 0; `lct.rs`/`attestation.rs` #527 diff: 0; LCT §1.2 #531 diff: 0) before being used as evidence on any moved surface.

Severity: HIGH / MEDIUM / LOW / INFO. Disposition: AUTONOMOUS-ACTIONABLE / DESIGN-Q / CROSS-TRACK.

---

## 2. §A — Prior-Finding Verification

### A.1 C55 remediations (5 autonomous, PR #326) — 5/5 HELD
Target byte-frozen since `a504ea41` → HELD by construction; spot-re-read live this fire: **B2** §2.4 wake bullet (L91 "Wake requires external witness, new-citizen trigger, or 90-day timeout (see §3.1)") · **B10** §7.2 #1 Wake-Trigger Flooding incl. hibernation `new_citizen` path (L382) · **B12** §7.1 "Sentinel heartbeat + timeout wake" row (L373) · **B13** §10 conformance precision (A.4) · **B16** §3.1 transition cross-ref symmetry. **0 REGRESSED.**

### A.2 #-Regression sweep (C168→C206 window)
No commit in the 55-commit window touched the target, `metabolic.py`, or the test vector (blob table above). The two sister anchors MOVED but their **metabolic-referencing lines did not** (proven in §B.1/§B.2 by empty metabolic-lexicon diff + non-metabolic hunk localization). The frozen window is regression-free by construction; all moved siblings adjudicated in §B.

### A.3 Standing carries — re-anchored at live HEAD

**SDK cross-track (4) — ALL STILL STALE** (`metabolic.py` frozen `d3d31446`; stale by construction):
| ID | Site | State |
|---|---|---|
| **B1** | `metabolic.py:147` `Transition(HIBERNATION, ACTIVE, "external witness or timeout")` | STILL STALE — omits `new_citizen` + 90-day (spec §3.1 L184) |
| **B3** | `metabolic.py:207` `Formula (§6.1): Daily ATP Cost` | STILL STALE — spec §6.1 L341 says "Hourly" |
| **B4** | `metabolic.py:110` TORPOR `description="Frozen + alert bonus"` | STILL STALE — spec §5.1 L299 is "Frozen" |
| **B11** | `metabolic.py:412-413` comment "Rest: queued" vs `return state == ACTIVE` | STILL STALE |

**Sister-doc cross-track (2) — OPEN, re-anchored inside the MOVED files (not by blob identity this time — by line-content identity)**:
- **B14** (SOCIETY_SPEC §1.4 "Implementations … MUST also conform to the metabolic-states specification" vs target "Proposed Standard" + §10 SHOULD): the SOCIETY_SPEC blob moved, but the §1.4 clause is byte-unchanged — re-read live at **`SOCIETY_SPECIFICATION.md:89`** (plus the eight-states paragraph L87 and cross-refs L37/L319/L322), all outside the window's single §7-area hunk (§B.1). Substance HELD.
- **B15/C58-B10** (SAL §3.6 dormant list omits Rest; "dormant states SHOULD defer" vs target wake): SAL blob moved, but §3.6 is byte-unchanged — re-read live at **`web4-society-authority-law.md:138-141`** (dormant list `(Sleep, Hibernation, Torpor, Estivation)` L140; "dormant states SHOULD defer" L141), outside the window's two hunks (§B.2). Both HELD. C170 (SAL 4th-delta, 2026-07-10) independently logged `SOCIETY_METABOLIC_STATES §3.6 | 0 | frozen — B10/M3 carries stable`.

**Design-Q (14) — ALL STILL OPEN by freeze**: C21 H1, H3, M3, M5, M7, L4, L5, L7 + C54 B5, B6, B7, B8, B9, B14-normative-strength. None self-resolved.

**C96-E1 (INFO, cross-track → atp-adp §3.3)** — anchor stable; `atp-adp-cycle.md` untouched in window. STANDS.

**C58-B10 (DESIGN-Q, defer-vs-wake)** — two-sided contradiction re-verified: SAL §3.6 L141 "dormant states SHOULD defer" (unchanged, §B.2) vs target §3.1 L184 / §4.1 L229 `wake_on: ["new_citizen", …]` (frozen). STANDS; operator bundle.

**M7 (ontology absence) — sweep REFRESHED against the window's ontology movement**: `hub-law.ttl` was MODIFIED in-window; loose-pattern `metabolic|hibernat|torpor|molt|estivat` across `web4-standard/ontology/` at HEAD → only the 2 pre-existing adjective `rdfs:comment` hits in `web4-core-ontology.ttl` (L85, L179 — both ATP/ADP-cycle prose). `hub-law.ttl` introduces **no** metabolic class or predicate. **M7 absence HOLDS.**

### A.4 §10 conformance (C56 claim re-read)
Target and test vector both blob-frozen → C133's 12-vector recompute remains valid; C168's token-by-token claim re-read stands (categories 3/3/4/2 = 12 multipliers; 6-of-8-driven-states nuance; `molt_success_rate` input). 0 discrepancies.

---

## 3. §B — Corpus-Delta + Inbound-Carry Sweep

**Result: 0 net-new defects on the target (4th consecutive fully-clean metabolic delta — C96, C133, C168, C206).** Every moved surface adjudicated DISJOINT with one cited basis; no agent or pass was pointed at the frozen 444 lines.

### B.1 SOCIETY_SPEC move (#522 §7.3 Correction & Enforcement) — DISJOINT; B14 anchor HELD
The blob moved `45781960`→`2ad453ba`, but the window diff (`git diff 8ac6edee HEAD`) contains **exactly one hunk**, at `@@ -471,11 +471,28 @@` — inside the §7 secession/federation-dissolution area, where #522 inserted the §7.3 Correction & Enforcement subsection. Disjointness proven two ways: (1) **metabolic-lexicon diff = 0** — no added/removed line matches `metabolic|hibernat|torpor|molt|estivat|MUST also conform`; (2) **anchor untouched** — the §1.4 metabolic clause (L87–L89, incl. B14's "MUST also conform" and the eight-state enumeration) and the cross-refs at L37/L319/L322 are all outside the single hunk. The §7.3 response vocabulary (Effector/`notice|quarantine|correct`) governs *society enforcement of law*, an orthogonal axis from *metabolic operational mode*; the two never intersect on the frozen target.

### B.2 SAL move (#523 Effector role registration) — DISJOINT; B15/C58-B10 anchors HELD
The blob moved `02ab3a42`→`0849ebbe` via **two hunks**: `@@ -230,6 +230,15 @@ def audit_adjust(...)` (the §5.x Effector/response-vocab code block) and `@@ -261,11 +270,13 @@ Implementations MUST maintain triples for:` (the §7.1.1 RDF-triples section). Neither touches §3.6 (L138–141, the SAL↔metabolic operational-mode-interaction section). Metabolic-lexicon diff = 0. The Effector role (Auditor's always-R7 response-side sibling) is a *governance-actor* registration; SAL §3.6's metabolic sensitivity (Molting for law amendments; `accepts_new_citizens` per state) is untouched. DISJOINT; B15 (dormant list omits Rest) and C58-B10 (defer-vs-wake) both HELD verbatim at L140–141.

### B.3 The ratchet #529 (`ratchet.rs` NEW, +306 lines; `lib.rs` export) — DISJOINT
`git show --stat 7b048a78`: touches only `web4-core/src/ratchet.rs` (new) and `lib.rs` (+2 export). Metabolic lexicon in `ratchet.rs` = **0**. The ratchet is monotone sovereign-authority accounting; it does not read, gate, or reference the metabolic state machine. Did **not** touch `society.rs` (the `MetabolicState` mirror) — §B.6.

### B.4 LCT §1.2 "Inspectable Evidence, Not Prescribed Trust" (#531) — DISJOINT
`git show d89595e8`: LCT-linked-context-token.md (+31), t3-v3-tensors.md, README, CLAUDE.md. Metabolic-lexicon diff = 0. **Candidate refuted** (mirroring the dictionary-C204 Candidate-2 refutation, [[feedback_refute_your_best_finding]]): §1.2 forbids a surface from encoding a universal admit/exclude *trust threshold*. The metabolic spec's trust surface (§5.1 update-rate/decay-rate/temporary-penalty; §5.2 reliability score) is a set of **rate modulations by operational state**, not an admit/exclude gate — there is no `confidence < X ⇒ exclude` construct in the frozen 444 lines to conflict with the principle. No intersection.

### B.5 birth-certificate + attestation (#527) — DISJOINT
`git show e8f313e4`: `attestation.rs` (new), `lct.rs` (+135), `hub.rs`. Metabolic-lexicon diff in `lct.rs`/`attestation.rs` = **0**. Near-adjacent concern probed and refuted: "birth certificate" touches §2.1 Citizenship issuance, which SAL §3.6 ties to `accepts_new_citizens` — but the #527 schema lives entirely in the Rust LCT/attestation layer and introduces no metabolic-state coupling; SAL §3.6 (the only place the coupling is stated) is itself unchanged (§B.2).

### B.6 web4-core `society.rs` (#516 v0.4.0 `EntityType::Society`) — window-DISJOINT; C168-N1 re-anchored, HELDs verbatim
The crate's only metabolic surface is `society.rs`'s `pub enum MetabolicState`. Its **window diff is empty** for the enum block and its doc-comment — `git diff 8ac6edee HEAD -- web4-core/src/society.rs` shows no `[+-]` line matching `MetabolicState|Genesis|Bootstrap|Operational|Dormant|Sunset`. Re-anchored live at HEAD:
- `society.rs:37` `pub enum MetabolicState { Genesis, Bootstrap, Operational, Dormant, Sunset }` — variant intersection with the spec's eight states (§2.1–§2.8) = **∅** (only "Dormant" echoes the spec's *category*, and as a single variant, not the category).
- `society.rs:33-34` doc-comment `/// Metabolic state of a society (lifecycle phase). /// Reference: SOCIETY_METABOLIC_STATES.md` — a published-crate reader following the cite still lands on a spec defining a **different state machine** (the 5 variants mirror SOCIETY_SPEC §1.3 Formation Process / ISP lifecycle).
**C168-N1 persists un-remediated** — correctly: it is a publish-track crate rename/re-cite (`LifecyclePhase`/`SocietyPhase`, or re-cite to `SOCIETY_SPECIFICATION.md §1.3`), semver-relevant since the enum serializes into published 0.4.0 artifacts; and an audit turn is zero-mutation regardless.

### B.7 reputation C195 remediation (#526) — DISJOINT
`reputation-computation.md` §5 no-match `return None` + dropped spec-only `value` key. Target grep `\breputation\b` = **0** (frozen). The metabolic trust surface (§5.1/§5.2) nowhere names reputation; the hunk touches neither decay nor scoring semantics.

### B.8 Inbound sibling-audit carries (C170–C204 interval docs)
Grep + hand-read of every interval audit mentioning metabolic:
- **C170 (SAL 4th-delta, 2026-07-10)** — metabolic appears only in rotation bookkeeping (L11) and as a frozen SAL-cited sibling (L34: `SOCIETY_METABOLIC_STATES §3.6 | 0 | frozen — B10/M3 carries stable; C168 confirmed clean`). No new carry routed here; confirms B10/M3 stable.
- **C202 (SOCIETY_SPEC 5th-delta, 2026-07-16)** — **explicitly routes the `MetabolicState` divergence to this audit as cross-track** (L68 point (3): "the MetabolicState divergence — cross-track — `SOCIETY_METABOLIC_STATES.md`'s concern, not this file's"; L72: the Rust society mirror "*was* gated (2026-05-14), its flagship is stale (`role.py`), and its residual is routed"). This is an **inbound-carry confirmation of C168-N1**, not a new finding ([[feedback_cross_doc_carry_inbound]]): C202 independently re-derived that the live residual of the 2026-05-14 cross-language alignment doc reduces to C92-N1 (genesis, SOCIETY_SPEC-owned) + the MetabolicState divergence (metabolic-owned = C168-N1). It **validates** the C168-N1 promotion and its disposition (operator/publish-track). C202 also confirmed §7.3 "has no web4-core twin to diverge from" (`grep quarantine|rehabilitate|Correction|ResponseClass web4-core/src/*.rs` → NONE), reinforcing §B.1's DISJOINT.
- C174/C178/C180/C204 — metabolic only in rotation bookkeeping / frozen-target-pattern narrative. **No new carry routed to metabolic in the interval.**

---

## 4. Net-New Findings

**None.** 0 net-new defects; 0 net-new carries. C206 is the 4th consecutive fully-clean metabolic delta. C168-N1 (MED, LEDGER — Rust `MetabolicState` = 5 lifecycle phases citing the metabolic spec) HELDs verbatim, re-anchored at live HEAD (§B.6), and was independently routed here by C202 (§B.8) — no re-promotion needed, no elevation warranted.

---

## 5. §C — Carries Reconciliation

**All standing carries STAND** (frozen target/SDK; sister anchors re-anchored by line-content within the moved files, §A.3/§B.1/§B.2): C21 design-Q ×8 · C54 design-Q ×6 · SDK cross-track B1/B3/B4/B11 (bundle for a future SDK-track pass) · sister-doc B14 (`SOCIETY_SPECIFICATION.md:89`, unchanged in the moved file) / B15 (`web4-society-authority-law.md:140-141`, unchanged in the moved file) · C96-E1 (atp-adp §3.3 untouched) · C58-B10 (two-sided, operator bundle) · M7 (sweep refreshed vs in-window `hub-law.ttl`; absence holds) · **C168-N1** (MED, LEDGER; re-anchored `society.rs:33-37`; operator DESIGN-Q + publish-track cross-track; C202-confirmed).

**0 net-new, 0 elevated, 0 resolved.** None of the standing carries gate a normal turn; all route to the one-decision operator memo.

**C207 (next remediation slot) = DECLARED NO-OP on the spec side.** 0 autonomous spec defects exist: the target is frozen and clean; C168-N1's ledger half is already recorded (memory-side) and its substance is operator/publish-track. Per the C133→C134 / C166→C167 / C168→C170 precedents the C207 slot should confirm this via step-(a) and advance the rotation **+2 to C208 = SAL 5th-delta** (`web4-society-authority-law.md`; lineage C23→C58→C98/C99→C134→C170→C208; last audited C170, 2026-07-10). [Order: SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, **SAL**, LCT, ISP, entity-types, errors, security, registries, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap.]

---

## 6. §D — Method Notes

1. **4th consecutive fully-clean metabolic delta** (C96, C133, C168, C206) — but the **first** where the tracked sister anchors moved, so the clean result was *earned in §B*, not inherited from a byte-frozen corpus. B14/B15 required re-anchoring by **line-content identity inside the moved files**, not blob identity ([[feedback_snapshot_presence_guard]] applied to a moved-but-locally-unchanged anchor).
2. **The single-hunk localization is the disjointness proof.** For both sister moves, the decisive evidence was two-part: (a) an empty metabolic-lexicon diff, and (b) the actual hunks landing in demonstrably non-metabolic sections (SOCIETY_SPEC §7 secession/enforcement; SAL `audit_adjust` + RDF-triples). Either alone is weaker; together they close the surface. A blob-moved anchor is not a moved *finding*.
3. **C202 pre-adjudicated this window's biggest temptation.** The W4IP Effector/response-vocab inbound *looks* like it could redefine or extend the metabolic surface; C202 had already established §7.3 "has no web4-core twin" and routed the only live Rust-mirror residual (MetabolicState) here as C168-N1. Reading the sibling audit first ([[feedback_cross_doc_carry_inbound]], [[feedback_prose_is_not_ledger]]) prevented re-discovering a routed item as "net-new."
4. **C168-N1 correctly persists un-remediated.** The enum is byte-unchanged and still mis-cites the metabolic spec, but the fix is a publish-track crate rename (semver-relevant on serialized 0.4.0 output) — outside a zero-mutation audit turn. Re-anchoring (not re-remediating) is the whole job here.
5. **Reserved guards honored**: the atp-adp conservation-invariant question (owned by the next atp-adp pass) and the mrh three-signatures guard (owned by the next mrh pass) were adjacent to neither this window's metabolic surfaces nor this frozen target — not adjudicated here.

---

## 7. Conclusion

C206 is the **5th delta re-audit** of `SOCIETY_METABOLIC_STATES.md`. Target byte-frozen since C55 (`a504ea41`), proven by blob identity this fire alongside frozen SDK, test vector.
- **§A**: 5/5 C55 remediations HELD; window regression-free by construction; carries re-anchored live — SDK ×4 still-stale by freeze; **B14/B15 re-anchored by line-content inside the two moved sister files** (§1.4 L89 / §3.6 L140-141, both untouched by the window's hunks); 14 design-Q open; C96-E1 atp-adp anchor stable; C58-B10 two-sided; M7 sweep refreshed vs in-window `hub-law.ttl` — absence holds; §10 conformance exact.
- **§B**: 8 moved surfaces, one cited adjudication each → **0 net-new defects (4th consecutive fully-clean delta)**. SOCIETY_SPEC §7.3 / SAL Effector / ratchet #529 / LCT §1.2 / birth-cert #527 / society.rs / reputation #526 all DISJOINT by cited hunk + empty metabolic-lexicon diff + non-metabolic hunk localization. The LCT §1.2 trust-threshold candidate was refuted (metabolic §5 = rate modulation, not admit/exclude gate).
- **§4/§C**: **0 net-new findings.** C168-N1 (MED, LEDGER) HELDs verbatim, re-anchored at `society.rs:33-37`, and was independently routed here by C202 — validated, not re-promoted. All carries STAND; 0 elevated, 0 resolved. **C207 = declared NO-OP on the spec side; rotation advances +2 to C208 = SAL 5th-delta.**
- **ZERO mutation of spec/SDK/crate/sister files; this audit document is the only web4-repo write.**

---

*Audit produced under Autonomous Session Protocol v2 by legion-web4-20260717-000036 (LEAD, slot 000036). Policy-review APPROVED first-pass; method reminders (genuine-mirror gate, sibling-prose check before "new", refute-by-default, zero-mutation) honored and evidenced inline.*
