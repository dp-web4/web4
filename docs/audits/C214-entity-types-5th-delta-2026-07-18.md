# C214 Audit: `entity-types.md` — 5th-Delta Re-Audit (6th Pass)

**Date**: 2026-07-18
**Auditor**: Autonomous session (Legion, web4 track) — firing `000036`, LEAD voice
**Document**: `web4-standard/core-spec/entity-types.md` (804 lines)
**Lineage**: C8 (2026-05-22, 10 findings, 9 remediated) → C26 (1st delta, #260) → C64 (2nd delta, 26 raw → 11 distinct) → C65 (remediation, 7 applied, #344 `5baa160f`) → C104 (2nd-delta re-audit, 0 net-new) → C137 (3rd-delta re-audit, 0 net-new) → C176 (4th-delta re-audit, 0 spec-side net-new; C176-N1/N2 SDK-track) → **C214 (this audit, 5th-delta re-audit / 6th pass)**
**Rotation note**: round-robin advanced from C212 (ISP 5th-delta, #539 OPEN) → the C213 remediation slot is a **no-op** (C212 found 0 spec-side defects on ISP) → the wheel advances to the next-oldest file, `entity-types.md` (last audited C176, 2026-07-11).

## Headline: FIRST NON-FROZEN entity-types delta since C65

entity-types.md was **byte-frozen** across C104/C137/C176 (identical to the C65 remediation `5baa160f`, 741 lines, 25+ days). **It has now MOVED.** The current blob is `1354e4c2` — **#523 "W4IP Phase 3 (N2): Effector Role"** (2026-07-14), which grew the file to **804 lines (+63)** by inserting **§4.8 Effector Role** plus the forced §4-preamble count edit. C214 is therefore a **genuine mover-audit**, not a frozen-wrap. Methodology follows the standard delta method (C56 claim-verify, C62 bidirectional carry re-verify, [[feedback_remediation_introduced_regression]] on the mover, [[feedback_prose_is_not_ledger]] on carry promotion, refute-your-own-flagship), with the **primary surface = the #523 insertion's additivity + tri-file citation consistency**.

**Cross-spec authority re-read** (passage, not recalled, at live HEAD): the #523 commit body + `--stat`; `hub-law-schema.md` §"Response vocabulary" (L148–224, W4IP N3 prescriptive, #522 `87377c3`) + §"Gating — RWOA+S+V+F" (F-a L217, F-b L224); `reputation-computation.md` §4 "Coercive/Extractive Behavior Rules" (L339) + the "Evidence-basis role" note (L386–393, introduced by #521 `767eb564`); `society-roles.md` §4.1 (L206–238); `web4-society-authority-law.md` §5.6 (L233–241) + §7.1.1 (L273–279); Rust `web4-core/src/lct.rs` `EntityType`, `web4-core/src/role.rs` `SocietyRole`, `web4-core/src/act.rs` `ConsequenceClass`; Python `web4/role.py` `SocietyRole`, `web4/entity.py`; the C176 prior audit doc.

---

## §A. Regression Check on the #523 Mover ([[feedback_remediation_introduced_regression]])

The #523 change to entity-types.md is **two hunks** (`git show 1354e4c2 -- entity-types.md`):

1. **§4-preamble count edit (L281)** — "seven subsections … six SAL-specific roles (Authority, Law Oracle, Witness, Auditor, Agent, Client)" → "**eight** subsections … **seven** SAL-specific roles (Authority, Law Oracle, Witness, Auditor, Agent, Client, **Effector**)". Everything else in the note (the base-mandatory-role home ruling, the SAL-vs-base overlap-on-Law-Oracle claim, the C51/SOCIETY_SPEC §1.2.5 attribution) is **byte-unchanged**.
2. **§4.8 Effector Role insertion (L399–461, +63 lines)** — role prose + Effector Enactment Request JSON, inserted between §4.7 (Client) and §5 (Entity Lifecycle).

### A.1 — The count edit is numerically exact (verified by ground-truth re-derivation, [[feedback_enumeration_and_grep_hypotheses]])

`grep '^### 4\.'` yields exactly **eight** subsections: §4.1 Society, §4.2 Authority, §4.3 Law Oracle, §4.4 Witness, §4.5 Auditor, §4.6 Agent, §4.7 Client, §4.8 Effector. Excluding §4.1 (an *entity-type context* per §2.1, not a role), the **seven** role headers §4.2–§4.8 are exactly "Authority, Law Oracle, Witness, Auditor, Agent, Client, Effector" in order — matching the preamble list nominally and positionally. **The count edit is correct.** L281 is the **only** subsection/role-count claim in §4 (grep for `seven|eight|six|nine|subsection|SAL-specific role` across the file confirms no other count assertion the insertion could have left stale). No orphaned count.

### A.2 — The 7 held C65 remediations are DISJOINT from the insertion → all HELD

The #523 hunks touch only §4-preamble L281 and the §4.7→§5 boundary. All 7 C65 remediation sites are **outside** that region and **byte-unchanged**:

| C65 item | Site | In #523 hunk? | Verdict |
|----------|------|---------------|---------|
| A.1 flagship (rights value) | §3.1 L153 | No | **HELD** |
| A.1 prose | §6.2 | No | **HELD** |
| B1 (witness colon-form) | §3.1 | No | **HELD** |
| B3 (Hybrid modes) | §2.1 | No | **HELD** |
| B4 (Infra mode=None) | §2.1 | No | **HELD** |
| B6 (slashing vocab) | §2.3 L102 | No | **HELD** (`slash` reappears in §4.8's *kinetic class* but is explicitly `parse-don't-enact` / MUST-NOT-enact — no live conflict with §2.3's authority-executed slashing) |
| A.2+B5 (role-list home + count) | §4 preamble L281 | **YES** — the count numerals only | **HELD + correctly updated** (six→seven / seven→eight; the home-ruling prose is byte-unchanged) |

**0 C65 remediation regressed by the mover.** The one hunk that touches a C65 site (L281, A.2+B5) updates exactly the count numerals the insertion forced and preserves the home-ruling prose intact.

### A.3 — Standing carries: all 9 STAND, disjoint from §4

All 9 C176 standing carries live at sites **outside §4** (C8-L3 §12↔§3.1; C23-H1 birth-cert §5.1; C24-H1 LCT-ID §13.2; B2/B9 §2.1 energy; B7 §10.2; B10/B11 §13; B12 §2.3). The §4.8 insertion is disjoint from every carry site. **All 9 STAND unchanged**; none resolved or hardened into a defect.

---

## §B. Tri-File Citation Consistency (the #523 registration surface)

#523 is a **tri-file** registration: entity-types §4.8 (role shape), `society-roles.md` §4.1 (taxonomy entry), `web4-society-authority-law.md` §5.6 + §7.1.1 (SAL normative bullets + RDF triples). The audit's job is to confirm every citation §4.8 makes **resolves at live HEAD** and the three registrations are **mutually consistent**.

### B.1 — Outbound citations from §4.8 all RESOLVE

| §4.8 citation | Target at live HEAD | Verdict |
|---|---|---|
| response vocabulary `notice \| quarantine \| correct \| rehabilitate` | `hub-law-schema.md` §"Response vocabulary" L185–188 (W4IP N3 prescriptive, #522) — exact 4-verb set | **RESOLVES** |
| kinetic class `slash \| suspend \| revoke \| terminate \| halt` "parse-don't-enact" | `hub-law-schema.md` kinetic-class rows + parse-don't-enact framing | **RESOLVES** |
| gate "RWOA + S + V + F (F-a forfeiture, F-b proportionality)" | `hub-law-schema.md` §"Gating — RWOA+S+V+F" L212, F-a L217, F-b L224 | **RESOLVES** |
| recognition evidence "Coercive/Extractive Behavior Rules category (`reputation-computation.md` §4)" | `reputation-computation.md` §4 "Coercive/Extractive Behavior Rules" L339 | **RESOLVES** (see §B.3 for a freshness gap on the *reverse* pointer) |
| Auditor "recognition-side sibling (§4.5)" | entity-types §4.5 L324–330 "Validates and adjusts T3/V3 tensors" — matches §4.8's characterization verbatim in substance | **RESOLVES** |
| SAL delegation `web4-society-authority-law.md §3.3, §5.6` | SAL §5.6 present (L233); §3.3 delegation machinery present | **RESOLVES** |
| `consequenceClass: "reversible"` wire value | `web4-core/src/act.rs` `ConsequenceClass` (L123) with `#[serde(rename_all="snake_case")]` → variants Reversible/Costly/Irreversible → wire `reversible` | **RESOLVES** — #523's claim "ConsequenceClass wire value per web4-core act.rs snake_case" is VERIFIED against the crate |
| lawRule example `QUARANTINE-ON-AGENCY-OVERRIDE` | `hub-law-schema.md` L239 `id: QUARANTINE-ON-AGENCY-OVERRIDE`, `response: quarantine` | **RESOLVES** (example rule id + response verb both match) |

### B.2 — Tri-file registration is mutually consistent

- **society-roles.md §4.1** registers `#### Effector` under "## 4. Optional Roles → ### 4.1 Trust / Accountability" (grouped with Witness/Auditor/Mediator/Validator). The #523 claim "registers Effector in §4.1 Trust/Accountability (**optional** tier)" is **VERIFIED**. It cross-refs entity-types §4.8 + SAL §5.6 and names Auditor as "the Effector's recognition-side sibling" — consistent with §4.8.
- **SAL §5.6** carries the normative bullets #523 describes (R7-only Reference binding to recognition evidence; RWOA+S+V+F gate; Enactment Transcript; witness-quorum immutable record; kinetic parse-don't-enact; reversible-rung appeal/cool-down; rate-limits/caps by Law Oracle; fractal delegation via `web4:delegatesTo` §3.3). Names Auditor §5.5 as recognition-side sibling — consistent.
- **SAL §7.1.1** adds triples `web4:hasEffector` (society→effector role) + `web4:respondedBy` (entity→effector enactment), explicitly "mirroring hasAuditor/adjustedBy" — the section header is "Additional Required Triples (Witness/Auditor/Effector/Ledger)", consistent.

The three files agree on: role name, response vocabulary, R7-only-with-recognition-evidence, RWOA+S+V+F gate, parse-don't-enact kinetic deference, Auditor-as-recognition-sibling, and "shape is Web4-normative / who-fills-it is society law." **Tri-file registration is internally coherent.**

### B.3 — **C214-N1 (LOW, spec-side, applied): the reputation-computation.md:389 forward-ref note is stale post-#523/#522**

The #523 commit body states it "**Resolves the standing forward reference at `reputation-computation.md:389`**." But `git show 1354e4c2 --stat` shows #523 touched **only** entity-types.md, society-roles.md, and web4-society-authority-law.md — **it did not edit reputation-computation.md**. It added the *target* the forward reference points to, but left the *reference itself* unchanged.

The note at `reputation-computation.md` L386–393 (introduced by **#521** `767eb564`, 2026-07-14 01:03, *before* #522/#523 landed at 13:03 the same day) reads:

> "The response side (**effector roles, response verbs, cross-boundary adjudication**) is proposed in `proposals/W4IP-DRAFT-…` and is **not normative until ratified** …"

Two of the three bundled items have **since been ratified into normative core-spec text**:
- **response verbs** → `hub-law-schema.md` §"Response vocabulary" (W4IP N3, prescriptive, #522 merged).
- **effector roles** → entity-types §4.8 / society-roles §4.1 / SAL §5.6 (W4IP N2, #523 merged; §4.8 provenance: "this section is the normative expression of its N2 item").
Only **cross-boundary adjudication** (N4) remains draft-only.

So the note now under-states the current normative state — a reader at :389 is told the whole response side is non-normative when the effector role and response vocabulary are live normative spec. This is a **freshness defect**, not a normative contradiction, in a note explicitly marked "(informative)".

**Direction (per-finding):** the audit **target** (entity-types §4.8) is **CORRECT and complete**; the staleness is entirely in the **sibling** reputation-computation.md, and it is the *unfulfilled half* of the #523 mover's own claimed resolution ([[feedback_remediation_introduced_regression]] — the mover asserted a resolution it did not deliver). **Severity LOW** (informative, no wire/behavior impact, reversible).

**Disposition — APPLIED (this session).** Precedent: C208 applied a trivial low-stakes sibling fix (C170-N1, CLAUDE.md glossary path) during an audit turn. C214-N1 is the same class: an unambiguous, well-verified, low-stakes, reversible freshness edit to an informative note, directly caused by the mover under audit. The note was refreshed to state that response verbs (hub-law-schema §Response vocabulary, #522) and the Effector role (entity-types §4.8 / society-roles §4.1 / SAL §5.6, #523) are now ratified, while cross-boundary adjudication (N4) remains draft. This delivers the forward-ref resolution #523 claimed. entity-types.md itself is **not touched** (no spec mutation on the audit target).

### B.4 — Corpus-delta (other moved cited siblings): 0 net-new

Aside from the #521/#522/#523 W4IP cluster (adjudicated above), the siblings entity-types cites (atp-adp, dictionary-entities, LCT-spec, SOCIETY_SPEC) have not moved in a way that touches an entity-types citation since C176 in a manner not already consumed. B6's §2.4 slashing cross-ref remains DISJOINT+CORROBORATED (unchanged from C176). **0 net-new from corpus-delta.**

---

## §B′. SDK-Mirror Expansion (Python + `web4-core/src/*.rs` at live HEAD)

Per the standing method guard, the mirror set is re-derived at live HEAD across **both** SDKs. Two surfaces this delta: the **role** enums (where Effector would mirror) and the standing **EntityType** taxonomy carry (C176-N1).

### B′.1 — Effector has NO SDK role-enum mirror yet → INFO (already routed to HUB-track, not net-new)

Both role enums carry Effector's recognition-side sibling **Auditor** but **not Effector**:
- `web4-core/src/role.rs` `pub enum SocietyRole` (L33): Sovereign/LawOracle/…/Witness/**Auditor**/Custom — **no `Effector` variant**.
- `web4/role.py` `class SocietyRole` (L43): SOVEREIGN/LAW_ORACLE/POLICY_ENTITY/TREASURER/ADMINISTRATOR/ARCHIVIST/CITIZEN/WITNESS/**AUDITOR** — **no `EFFECTOR`**.

This is the expected SDK-lags-spec shape (spec added Effector across 3 files; the role enums don't yet mirror it). **It is NOT net-new**: `SESSION_FOCUS.md` item 0d explicitly routes the **implementation ("code half")** of the W4IP response side to **HUB-track's pending Phase-2 PR** ("Legion reviews when it's up"), sequenced *after* the spec half (#522/#523, both merged). Recording per [[feedback_prose_is_not_ledger]]: this observation is already parked/owned in the queue — do **not** create a competing route. **Direction = SDK lags spec (spec CORRECT)**; owner = HUB-track; Legion's action = review the enactment PR when it lands (carry the `unwrap_or_default()` NIT + parse-don't-enact enforcement check per the queue note). INFO, carry-only.

### B′.2 — C176-N1 (Rust `EntityType` coverage) has NARROWED: 7/15 → 8/15 (Society added by #516)

Re-derived at live HEAD: `web4-core/src/lct.rs` `EntityType` now has **9 variants covering 8 spec §2.1 types** — `Human`, `AiSoftware`, `AiEmbodied` (AI split), `Organization`, **`Society`**, `Role`, `Task`, `Resource`, `Hybrid`. **`Society` was ADDED by #516 (`fed64b51`, 2026-07-13 16:09, "EntityType::Society + version 0.4.0").**

**Provenance check ([[feedback_prior_finding_path_provenance]]):** #516 landed **2026-07-13**, *after* the C176 snapshot (2026-07-11). C176-N1 listed Society among "8 absent types" and read "crate version 0.3.0 (published)" — so **C176 was ACCURATE at its snapshot** (Society was genuinely absent on 07-11; the doc-comment date "HUB concord vote, 2026-07-10" is the *vote* date, not the code-landing date). This is **interval progress, not a C176 error, and not a re-discovery**: C176-N1 **NARROWS** from "8 absent (Society, Device, Service, Oracle, Accumulator, Dictionary, Policy, Infrastructure)" to **"7 absent: Device, Service, Oracle, Accumulator, Dictionary, Policy, Infrastructure."** Direction unchanged = **SDK lags spec (spec CORRECT)**; routes SDK-track, carry-only, no spec mutation. C176-N2 (AI-split double-models embodiment vs `HardwareBinding` axis) **STANDS** unchanged (INFO).

**Net from SDK-mirror: 0 net-new. Effector-mirror = already-routed HUB-track INFO; C176-N1 NARROWS (still open, SDK-track); C176-N2 STANDS.**

---

## §C. Fresh-Internal Refute-by-Default Pass

An independent adversarial Explore pass was tasked to **REFUTE** the claim "the §4.8 insertion is a clean additive insertion with zero internal contradictions, and the L281 count edit is exact." It checked §4.8 against §2.1/§4.2/§4.5/§6.2, re-counted §4 subsections from ground truth, verified the Auditor characterization against §4.5, compared the Enactment Request JSON conventions against the §4.5 Auditor JSON, grepped the new terms (RWOA+S+V+F, parse-don't-enact, consequenceClass, R7, F-a/F-b) for inconsistent in-document reuse, and resolved intra-doc cross-refs. **Result: NO CONTRADICTIONS FOUND.** (One noted non-issue: §4.8 uses singular `"target"` vs the Auditor block's plural `"targets"` — semantically justified by distinct message schemas `Web4EffectorEnactment` vs `Web4AuditRequest`, not a contradiction.) The flagship survives adversarial verification.

---

## §D. Disposition Summary & C215 Routing

| Finding | Class | Disposition |
|---------|-------|-------------|
| §4-preamble count edit (six→seven / seven→eight) | §A mover-regression | **CORRECT** — numerically exact vs ground-truth §4.1–§4.8; only count claim in §4 |
| 7 C65 remediations | §A | **HELD** — all disjoint from the #523 hunks; 0 regressed |
| 9 standing carries | §A | **STAND** — all disjoint from §4; none resolved/hardened |
| §4.8 outbound citations (8) | §B.1 | **ALL RESOLVE** at live HEAD (incl. act.rs snake_case `consequenceClass` verified against crate) |
| Tri-file registration (entity-types §4.8 / society-roles §4.1 / SAL §5.6+§7.1.1) | §B.2 | **MUTUALLY CONSISTENT** |
| **C214-N1** — reputation-computation.md:389 forward-ref note stale post-#522/#523 | §B.3 | **LOW, spec-side sibling, APPLIED this session** (freshness edit; entity-types.md untouched). Resolves the forward reference #523 claimed but did not deliver |
| Corpus-delta (non-W4IP siblings) | §B.4 | **0 net-new** |
| Effector SDK role-enum mirror (Rust + Python) | §B′.1 | **INFO, already-routed to HUB-track Phase-2 code half (SESSION_FOCUS 0d); not net-new** |
| **C176-N1** — Rust `EntityType` coverage | §B′.2 | **NARROWED 7/15 → 8/15** (Society added #516, post-C176 interval progress; C176 accurate at snapshot). STANDS, SDK-track, 7 types still absent |
| C176-N2 — AI-split double-models embodiment | §B′.2 | **STANDS** (INFO) |
| Fresh-internal refute pass | §C | **0 net-new internal contradictions** |

**C214 distinct net-new findings: 1 (C214-N1, LOW, spec-side sibling, APPLIED).** The audit **target** entity-types.md is **spec-side clean**: the #523 Effector insertion is additive, regression-CLEAN, count-exact, tri-file-consistent, and all 8 outbound citations resolve — this is the **first non-frozen entity-types delta to pass regression-check clean** (parallel to C202/C208/C210's clean non-frozen deltas). **→ C215 entity-types remediation slot = NO-OP** (the sole net-new landed in a sibling and was applied this session; entity-types.md needs no edit — do NOT manufacture one).

**Routed / carry-forward:**
- **C214-N1** — APPLIED to reputation-computation.md; will verify HELD when reputation-computation.md next reaches an audit turn (do not re-open).
- **Effector SDK role-enum mirror** → HUB-track Phase-2 code half (already queued, SESSION_FOCUS 0d); Legion reviews the enactment PR when up (carry `unwrap_or_default()` NIT + parse-don't-enact enforcement check).
- **C176-N1** (NARROWED, Rust `EntityType` 7 types absent: Device/Service/Oracle/Accumulator/Dictionary/Policy/Infrastructure) + **C176-N2** (AI-split) → SDK-track, travels with the C172/C174/C176 SDK-mirror bundle.
- Standing design-Qs (C23-H1, C24-H1, B7, B2/B9, B10/B11) → operator memo, unchanged.

**Rotation**: next-oldest after entity-types is **`errors.md`** (lineage C30→C66→C67→C106→C138→C178→**C216**). SDK-mirror guard for C216: re-derive the errors-primitive implementers at live HEAD across Python **and** `web4-core/src/error.rs`.

---

## §E. Lessons (for memory)

1. **A byte-frozen file can un-freeze — and when it does on a mover you pre-flagged, the audit is genuine, not a wrap.** entity-types was frozen 25+d across C104/C137/C176; #523 moved it. The C214 guard in memory ("it was itself a #523 Effector mover — regression-check") was exactly right; the audit's center of mass shifted from §A-verification to **mover-regression + tri-file-citation-resolution**. Frozen ≠ permanently frozen; check the blob hash every delta.
2. **A commit's "Resolves X" claim is a hypothesis to test against `--stat`, not a fact.** #523's body said it "Resolves the standing forward reference at reputation-computation.md:389" — but `--stat` shows it never touched that file. It added the *target* and left the *reference* stale. Always verify a mover's self-described cross-file effects against what it actually changed ([[feedback_remediation_introduced_regression]] extends to *claimed-but-undelivered* resolutions, not just introduced regressions).
3. **A same-day sibling commit can strand a note between "written" and "obsolete."** The reputation-computation.md:389 note was written by #521 at 01:03 (when the response side was draft-only) and rendered stale by #522/#523 at 13:03 the same day. Freshness defects cluster around fast-moving multi-PR feature landings; when auditing one PR of a same-day cluster, check whether an *earlier* PR's prose is now stale.
4. **A maturing SDK NARROWS a coverage carry without a re-audit re-discovering it.** C176-N1 said "8 absent"; #516 added Society (post-C176) → "7 absent." Re-deriving the mirror at live HEAD and *checking the landing date against the prior snapshot* distinguishes interval-progress (narrow the carry) from a prior-audit error (neither here — C176 was accurate at 07-11). ([[feedback_prior_finding_path_provenance]])
5. **"Is it net-new?" before "is it a finding?" — the Effector SDK gap was already owned.** The role enums lack Effector, which *looks* like fresh §B′ yield — but SESSION_FOCUS 0d already routes the code half to HUB-track. Recording it as net-new would have double-counted owned work; the [[feedback_prose_is_not_ledger]] discipline cuts both ways (promote un-ledgered observations; do NOT re-discover already-ledgered ones).

---

## Cross-Reference to Prior Audits

| Audit | Result |
|-------|--------|
| C8 | entity-types.md first pass — 10 (3H/4M/3L); 9 remediated |
| C26 | 1st delta — 5 new + 1 INFO; 4 remediated (#260) |
| C64 | 2nd delta — 26 raw → 11 distinct; 7 routed |
| C65 | remediation — 7 applied (#344 `5baa160f`) |
| C104 | 2nd-delta re-audit — 0 net-new → C105 NO-OP |
| C137 | 3rd-delta re-audit — 0 net-new → C138 NO-OP |
| C176 | 4th-delta re-audit — 0 spec-side net-new; C176-N1 (Rust EntityType 7/15) + C176-N2 SDK-track |
| **C214** | **5th-delta re-audit (6th pass) — FIRST NON-FROZEN delta since C65 (#523 Effector §4.8, +63 lines). §A: count edit exact, 7 C65 HELD, 9 carries STAND (all disjoint from the insertion). §B: 8/8 §4.8 citations resolve (act.rs snake_case `consequenceClass` verified against crate); tri-file registration (entity-types §4.8 / society-roles §4.1 / SAL §5.6+§7.1.1) mutually consistent; ONE net-new C214-N1 (reputation-computation.md:389 forward-ref note stale post-#522/#523 — the unfulfilled half of #523's own claimed resolution) — LOW, APPLIED to the sibling this session, entity-types.md untouched. §B′: Effector SDK role-enum mirror absent but already-routed to HUB-track (not net-new); C176-N1 NARROWED 7/15→8/15 (Society added #516); C176-N2 STANDS. §C: 0 net-new internal (adversarial refute of §4.8 insertion CLEAN). → C215 = NO-OP (spec target clean); 1 sibling fix applied.** |
