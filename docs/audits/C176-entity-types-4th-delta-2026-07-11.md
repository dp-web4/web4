# C176 Audit: `entity-types.md` — 4th-Delta Re-Audit (5th Pass)

**Date**: 2026-07-11
**Auditor**: Autonomous session (Legion, web4 track) — firing `060036`, LEAD voice
**Document**: `web4-standard/core-spec/entity-types.md` (741 lines)
**Lineage**: C8 first-pass (2026-05-22, 10 findings, 9 remediated) → C26 first delta (2026-06-02, 5 new + 1 INFO, 4 remediated #260) → C64 second delta (2026-06-16, 26 raw → 11 distinct, 7 routed) → C65 remediation (2026-06-16, 7 applied, #344 `5baa160f`) → C104 (2nd-delta re-audit, 0 net-new) → C137 (3rd-delta re-audit, 0 net-new) → **C176 (this audit, 4th-delta re-audit / 5th pass)**
**Rotation note**: round-robin advanced from C174 (ISP 4th-delta, #506 `6c2607c9`, MERGED) → the C175 remediation slot is a **no-op** (C174 found 0 spec-side defects) → the wheel advances to the next-oldest file, `entity-types.md` (last audited C137, 2026-07-04). This is a **frozen-wrap** delta of the same class as C104/C137/C172/C174.
**Methodology**: C-series **4th-delta re-audit** of a **byte-frozen** target. entity-types.md is **byte-identical to its C65 remediation** (`git diff 5baa160f..HEAD -- entity-types.md` = empty; **25 days frozen**, unchanged since the C137 snapshot). Per the **C56 method**, §A audits the C65 remediation *claims* against canonical, not merely "is the edit present." Per **C62**, §A re-verifies every standing carry **bidirectionally**. §B is the **corpus-delta** surface (siblings that moved since the C137 snapshot, at cited-hunk granularity — [[feedback_snapshot_presence_guard]]). **§B′ is the SDK-mirror-expansion surface** — per the **C172/C174 method guard**, the SDK mirror is *not a fixed set*: re-derive the target-primitive implementers at live HEAD across **both** the Python SDK and **`web4-core/src/*.rs`**, decide finding **direction per-finding** ([[feedback_prior_finding_path_provenance]], [[feedback_refute_your_best_finding]]). §C is a single proportional refute-by-default fresh-internal pass. §D routes findings for C177/C178.
**Cross-spec authority re-read** (passage, not recalled): `atp-adp-cycle.md` §2.4 Slashing (L170–216, incl. the C151-edited Supply-accounting note L206–210) at current HEAD (post-C151 `256ab51d`); the C151 commit body (#477); Python SDK `web4/entity.py` (`_REGISTRY`) + `web4/lct.py` (`EntityType`); Rust `web4-core/src/lct.rs` (`EntityType`, `coherence_threshold`, `HardwareBinding`) at crate version **0.3.0 (published)**; Rust `web4-trust-core/src/entity/types.rs`; the prior C137 audit doc.

---

## §A. Verification of C65 Remediation (frozen target — 9th consecutive frozen-wrap)

entity-types.md is **byte-identical** since the C65 remediation (#344 `5baa160f`, 2026-06-16). All 7 autonomous C65 remediations **HELD** by byte-freeze, 0 regressed, **0 `&#`/HTML-entity artifacts**:

| C65 item | Origin | Site | Current state | Verdict |
|----------|--------|------|---------------|---------|
| A.1 (flagship) | C26-H1 value | §3.1 L153 | `"rights": ["presence", "interact", "accumulate_reputation"]` | **HELD** |
| A.1 prose | C26-H1 value | §6.2 L495 | "Provides base rights: Presence, interact, accumulate reputation" | **HELD** |
| B1 | witness format | §3.1 L151 | `["lct:web4:witness:1", "lct:web4:witness:2"]` (colon form) | **HELD** |
| B3 | Hybrid mode | §2.1 L33 | `Agentic/Responsive/Delegative` (was undefined "Mixed") | **HELD** |
| B4 | Infra mode slip | §2.1 L35 | Mode column = `None` (was "Passive", an energy not a mode) | **HELD** |
| B6 | slashing vocab | §2.3 L102 | "…distinct from the punitive, authority-executed *slashing* of `atp-adp-cycle.md` §2.4 (evidence-gated destruction of ATP for law violations)" | **HELD** — see §B |
| A.2 + B5 | role-list home + six-vs-seven | §4 preamble L281 | "six SAL-specific roles … canonical home is `society-roles.md` §2" | **HELD** |

The §C fresh pass (below) independently re-traced §2.1's 15-row Mode/Energy table against §2.2/§2.3 prose and confirmed every C65-fixed cell (Hybrid L33, Infrastructure L35) plus the rights values (§3.1 L153 == §6.2 L495) and Citizen immutability (§3.1/§3.4/§6.2) still consistent.

### A.1 Standing carries — all STAND, re-verified bidirectionally

| Carry | Class | Re-verification at C176 | Verdict |
|-------|-------|--------------------------|---------|
| **C8-L3** | deferred content-merge | §12↔§3.1 citizen-example redundancy; non-contradictory | **STANDS** (deferred) |
| **C23-H1** | OPEN design-q | birth-cert field-set superset (`ledgerProof`/`parentEntity` vs SAL §2.2); untouched | **STANDS** |
| **C24-H1** | OPEN design-q (cross-track) | LCT-ID divergence `lct:web4:*` vs `policy:*` (§13.2) vs `did:web4:key:*` (LCT-spec); do NOT self-resolve | **STANDS** |
| **B2** | cross-track (SDK) | SDK per-instance Device energy — **matured this interval**, see §B′.1 | **STANDS** (re-framed) |
| **B7** | cross-track → 3-doc | §10.2 `trust_requirements` vs dictionary-entities §2.2 (3-doc B26 bundle, operator-gated); siblings unmoved since C53 | **STANDS** |
| **B9** | design-q | Task energy "Active (when R6-capable)" vs SDK fixed ACTIVE; see §B′.1 | **STANDS** |
| **B10** | design-q / editorial | §13 Policy lacks an LCT-structure JSON example (asymmetry vs §10.2/§11.2) | **STANDS** |
| **B11** | design-q | §13.1 frames SAGE/IRP integration as if Web4-normative | **STANDS** |
| **B12** | cross-track (nicety) | §2.3 passive-rep lacks explicit cross-ref to atp-adp §4.2 | **STANDS** |

No carry RESOLVED or HARDENED into a new defect this interval.

---

## §B. Corpus-Delta (moved cited siblings)

**Moved-sibling surface.** Of the siblings cited by C64/C104/C137 (SAL, `society-roles.md`, `dictionary-entities.md`, `atp-adp-cycle.md`, LCT-spec, SDK), **only `atp-adp-cycle.md` moved since the C137 snapshot (2026-07-04).** The single interval commit is **atp-adp-C151** (#477 `256ab51d`, 2026-07-07). All other cited siblings are at-or-before the C137 snapshot (society-roles C39 `8401c6a9`; dictionary-entities C53 `95d20919`; SAL `0d756773`; LCT `9d1933f8`). So the entire corpus-delta surface is atp-adp-C151.

### B.1 — atp-adp-C151 → entity-types B6 (§2.4 slashing cross-ref): DISJOINT-from-the-edit + CORROBORATED

This is a **sharper** case than C137's B-delta.1, and worth stating precisely because the disjointness rationale **inverts**:

- **At C137**, the interval atp-adp commit (C119) touched §7.1 + §4.2 and **left §2.4 untouched** → B6's §2.4 cross-ref was disjoint *because the cited section didn't move*.
- **At C176**, the interval atp-adp commit (C151) **does edit inside §2.4** — but only the *Supply-accounting note*'s conservation-invariant scoping phrase (`git show 256ab51d`: `…which scopes only ATP→ADP transfers` → `…which scopes only ATP transfers between entities (§6.3)`). The **slashing definition itself** — the `### 2.4 Slashing (ATP Destruction)` heading, the `slash_atp` pseudocode, and the semantics "Slashing **destroys** ATP … evidence-gated … for violations" — is **byte-unchanged**.

entity-types §2.3 L102 (the C65-B6 remediation) cross-cites atp-adp §2.4 as "**evidence-gated destruction of ATP for law violations**." That is a citation of the *slashing definition*, which C151 did not touch → **disjoint at cited-hunk granularity**. Moreover the post-C151 note still opens "Slashing **destroys** ATP … removed from `total_supply`," which **corroborates** B6's characterization of slashing as ATP destruction. **B6 HELD; 0 delta.** (Interval-audit routing: the C151 remediation doc `docs/audits/C151-atp-adp-cycle-remediation-2026-07-07.md` routes only atp-adp-internal/t3-v3-anchor concerns — **0 carries routed back to entity-types**.)

### B.2 — atp-adp-C151 → entity-types §7.1/conservation: DISJOINT (grep-confirmed 0)

entity-types cites atp-adp's conservation invariant, `total_supply`, "ATP→ADP transfers," or §6.3 **nowhere** (`grep -ni` = 0; the only "7.1" token is entity-types' own `### 7.1 Entity Type Validation` heading). The C151 scoping edit is therefore disjoint — nothing in entity-types depends on the arrow-vs-between-entities wording of the conservation invariant.

**Net from corpus-delta: 0 net-new.**

---

## §B′. SDK-Mirror Expansion (the C172/C174 yield surface)

Per the standing method guard, the SDK mirror is re-derived at live HEAD across **both** the Python SDK and **`web4-core/src/*.rs`**. entity-types.md is a *taxonomy* spec (§2.1 recognizes **15 entity types**: Human, AI, Society, Organization, Role, Task, Resource, Device, Service, Oracle, Accumulator, Dictionary, Hybrid, Policy, Infrastructure). Three code sites define an `EntityType`; two are genuine mirrors of this taxonomy and one is a name-collision on a different primitive.

### B′.1 — Python SDK: MATURED and CLEAN (15/15 parity)

Since the C137 snapshot the Python SDK grew a **principled entity-type registry** that C137 did not yet track (C137's B2 knew only "`entity.py` Device hardcodes ACTIVE"):

- `web4/lct.py` `EntityType` enum = **15 values**, matching spec §2.1 **exactly** (HUMAN, AI, SOCIETY, ORGANIZATION, ROLE, TASK, RESOURCE, DEVICE, SERVICE, ORACLE, ACCUMULATOR, DICTIONARY, HYBRID, POLICY, INFRASTRUCTURE).
- `web4/entity.py` `_REGISTRY: dict[EntityType, EntityTypeInfo]` = **15 entries**, each carrying `modes` (BehavioralMode set) + `energy` (EnergyPattern) + `can_r6`. Hand-verified every row against spec §2.1's Mode/Energy columns — **all 15 faithful** (e.g. Infrastructure = `frozenset()`/PASSIVE/can_r6=False; Policy = {RESPONSIVE,DELEGATIVE}/ACTIVE; Oracle = {RESPONSIVE,DELEGATIVE}/ACTIVE; Accumulator = {RESPONSIVE}/PASSIVE).

The two known carries persist only as **schema simplifications**, not bugs:
- **B2** (Device): spec §2.1 Energy = "**Active or Passive**" (per-instance); the registry maps Device → a single `ACTIVE`. The registry's one-value-per-type schema cannot express the per-instance choice. STANDS, re-framed from "hardcode bug" to "single-value-schema limitation."
- **B9** (Task): spec Energy = "Active (**when R6-capable**)"; registry fixes ACTIVE + `can_r6=True`. Same single-value-schema shape. STANDS.

The Python mirror is therefore **cleaner and more complete** than at C137 — the registry closes the "can't model most types" gap that motivated B2's original framing, while B2/B9 survive only as the residual per-instance-vs-per-type modeling question (design-q, operator).

### B′.2 — Rust `web4-core` 0.3.0 (PUBLISHED): 7/15 types represented → **C176-N1 (LOW, cross-track SDK — PROMOTED from C172 LCT-B12 prose)**

> **Provenance correction ([[feedback_prose_is_not_ledger]]).** This is **not net-new to the corpus.** The C172 LCT audit (PR #505) already *observed* the Rust `EntityType` 8-variant shape — the AI-split and the identical 8 omitted types — but **parked it in the LCT carry's B12 prose** marked "*Pre-existing (NOT net-new, snapshot-guarded) … folds into B12 as the first Rust-mirror observation.*" It was never promoted to a ledger line, never adjudicated against its own taxonomy home, and never given a direction ruling. C176's contribution is exactly that promotion + adjudication: this delta lands on `entity-types.md`, the **canonical home of the §2.1 taxonomy the enum mirrors**, so it is where the finding belongs. Recording it as N1 here (and on the entity-types ledger line) is the [[feedback_prose_is_not_ledger]] fix — "is it NEW?" (no) is answered separately from "does it belong on a ledger and has it been adjudicated?" (not until now).

`web4-core/src/lct.rs:28` `pub enum EntityType` — doc-commented "**Entity type that an LCT can represent**," matched exhaustively in `coherence_threshold()` (L467–476) — has **8 variants representing only 7 of the 15 spec §2.1 types**:

| Rust variant | Maps to spec §2.1 type |
|---|---|
| `Human` | Human |
| `AiSoftware`, `AiEmbodied` | AI (one spec type, split into two — see N2) |
| `Organization` | Organization |
| `Role` | Role |
| `Task` | Task |
| `Resource` | Resource |
| `Hybrid` | Hybrid |

**8 spec types are absent**: **Society, Device, Service, Oracle, Accumulator, Dictionary, Policy, Infrastructure**. Because the enum's doc comment claims to model "the entity type an LCT can represent," and the spec (and the sibling Python SDK) give **all 15** types LCTs, the Rust enum **cannot type a Society LCT, a Dictionary LCT, a Policy LCT**, etc. This also produces an **intra-project divergence**: within the same repo, Python models 15/15 and Rust models 7/15.

**Direction (adjudicated per-finding, refute-by-default on the flagship):** Is the 8-variant set a *deliberate* SDK-layer scope (the identity-bearing types web4-core currently needs) or a *gap*? Refuting-by-default: the enum's own doc comment universalizes it ("the entity type an LCT can represent"), not "the subset web4-core supports"; the sibling Python SDK in the **same repo** already carries all 15; and the absent types (Society, Dictionary, Policy) are first-class LCT-bearing entities elsewhere in the corpus (Society LCTs in ISP/SAL; Dictionary LCTs in dictionary-entities; Policy as the ratified 15th type per CLAUDE.md). The refutation fails → this is a genuine **incompleteness**, not a scoping choice. **Severity LOW**: it is *incompleteness, not incorrectness* — nothing the Rust enum *does* is wrong; it simply cannot represent 8 taxonomy members. **Direction = SDK lags spec** (like C172, unlike C174): the **spec is CORRECT and canonical**; the fix is to extend the Rust enum, not to touch the frozen spec. Routes **SDK-track**, carry-only. (Aligns the Rust surface with the Python SDK and spec §2.1.)

### B′.3 — Rust AI-split double-models embodiment → **C176-N2 (INFO, no action — also first noted C172)**

Likewise first noted in C172's LCT-B12 prose ("*splits ai→software/embodied*"), adjudicated here for the first time. The Rust enum splits the spec's single **AI** type into `AiSoftware` / `AiEmbodied`, and `coherence_threshold()` assigns them different floors (`AiEmbodied` 0.6 "hardware binding helps" vs `AiSoftware` 0.7 "higher bar due to copyability"). But the spec models embodiment on an **orthogonal axis** — the `HardwareBinding` level (0–5) with its `trust_ceiling` (also present in the same `lct.rs`, L61–90) — **not** as an entity-type distinction. So Rust encodes embodiment *twice* (entity-type split **and** hardware-binding level). This is a **category-appropriate SDK refinement / mild double-modeling smell**, not a spec defect and not an incorrectness. **INFO, no action**; noted so a future SDK pass that reconciles N1 also considers whether the AI-split should fold back into the `HardwareBinding` axis.

### B′.4 — `web4-trust-core::EntityType` — EXCLUDED (name-collision, different primitive)

`web4-trust-core/src/entity/types.rs:9` also defines `pub enum EntityType`, but it is a **different concept**: a trust-graph entity-**ID prefix classifier** (`Mcp / Role / Session / Reference / Lct / Other(String)`, parsed from `"type:name"` strings via `from_entity_id`). It classifies MRH graph nodes by ID prefix; it does **not** mirror the spec §2.1 taxonomy and makes no claim to. **Explicitly excluded** from the §2.1 divergence analysis as a name-collision (INFO). The only latent hazard is the shared symbol name across two crates modeling unrelated concepts — a naming nicety, not a §2.1 finding. (Recorded so the SDK-track owner of N1 is not surprised by a second same-named enum.)

**Net from SDK-mirror expansion: 2 findings adjudicated (C176-N1 LOW, C176-N2 INFO), both cross-track SDK, spec-side clean. Neither is net-new to the corpus — both were observed (unadjudicated) in C172's LCT-B12 prose; C176 promotes and rules on them at their §2.1 taxonomy home.**

---

## §C. Fresh-Internal Refute-by-Default Pass

A single Explore pass (proportional to a 5th-pass byte-frozen target whose full 8-lens sweep ran at C64 and whose refute passes ran clean at C104/C137), fed the prior-finding + carry context and instructed to refute by default. **Result: 0 net-new internal contradictions.**

Line-traced and clean: §2.1's 15-row Mode/Energy table vs §2.2/§2.3/§4/§6.2/§11.1/§13.2 prose (every row consistent, incl. Policy §13.2 property table matching §2.1 exactly, Accumulator's "passive witnessing" §11.1, Role "cannot act without paired agent" §6.2); §1–§14 numbering sequential with no dup/skip (§4's "seven subsections / six roles" self-count verified: 4.1–4.7 = 7, six named roles = 6); all internal `see §X` refs resolve; §3.1 rights == §6.2 prose; Citizen immutability consistent across §3.1/§3.4/§6.2 (§5.3 "removed from MRH arrays" on entity *death* reads as lifecycle-end, not revocation — not a contradiction); §3.1 JSON-LD vs §5.1 pseudocode covered by the §5.1 "illustrative and abbreviated" disclaimer. Task/Device left as their known carries (B9/B2).

---

## §D. Disposition Summary & C177/C178 Routing

| Finding | Class | Disposition |
|---------|-------|-------------|
| 7/7 C65 remediations | §A | **HELD** by byte-freeze (25d); 0 regressed, 0 artifacts |
| All 9 standing carries | §A | **STAND**; none resolved/hardened into a defect |
| atp-adp-C151 → B6 (§2.4 slashing) | §B corpus-delta | **DISJOINT-from-the-edit + CORROBORATED** (C151 hit the conservation-scope phrase, not the slashing def B6 cites) |
| atp-adp-C151 → §7.1/conservation | §B corpus-delta | **DISJOINT** (entity-types cites conservation nowhere; grep = 0) |
| Python SDK entity.py/lct.py | §B′.1 | **CLEAN, 15/15 parity**; matured since C137; B2/B9 re-framed as single-value-schema limitations |
| **C176-N1** — Rust web4-core 0.3.0 `EntityType` = 7/15 types | §B′.2 | **PROMOTED from C172 LCT-B12 prose (not net-new to corpus), LOW, cross-track SDK.** 8 absent: Society/Device/Service/Oracle/Accumulator/Dictionary/Policy/Infrastructure. Direction = SDK lags spec (spec CORRECT). Intra-project Python-15↔Rust-7 divergence. → SDK-track carry, adjudicated + ledgered here, no spec mutation |
| **C176-N2** — Rust AI-split double-models embodiment | §B′.3 | **Also first noted C172, INFO, no action.** Embodiment already on the `HardwareBinding` axis; AI split is a refinement/smell, not a defect |
| web4-trust-core::EntityType | §B′.4 | **EXCLUDED** (name-collision, different primitive); INFO |
| Fresh-internal pass | §C | **0 net-new internal contradictions** |

**C176 distinct findings adjudicated: 2 (1 LOW + 1 INFO), both cross-track SDK, carry-only — neither net-new to the corpus (both observed unadjudicated in C172's LCT-B12 prose; C176 promotes + rules on them at their §2.1 home per [[feedback_prose_is_not_ledger]]).** The frozen spec is **spec-side clean for the 3rd consecutive delta** (C104 + C137 + C176). All findings live on the **§B′ SDK-mirror surface** — the C172/C174 pattern holds a third time, and this instance's direction is **"SDK lags spec"** (like C172): the spec needs **no mutation**. → **C177 entity-types remediation slot = NO-OP (spec side).** Do NOT manufacture a spec edit.

**Routed off-target (surface as ONE operator/SDK memo — none gate a normal AUDIT turn):**
- **C176-N1** (Rust web4-core EntityType 7/15 coverage) → **SDK-track** (extend the Rust enum to the full §2.1 15-type set + reconcile with the Python SDK). Travels with the standing SDK-mirror bundle (C172/C174 lineage).
- **C176-N2** (Rust AI-split vs HardwareBinding axis) → SDK-track INFO; consider when N1 is worked.
- Standing: **C64-B7** (3-doc Dictionary-LCT canonicity, operator-gated B26); **C23-H1** + **C24-H1** (open design-Qs); **B2/B9** (per-instance-vs-per-type energy schema, design-q); **B10/B11** (Policy JSON example / SAGE framing, editorial-design).

**Rotation**: next-oldest after entity-types is **`errors.md`** (last audited C138, lineage C30→C66→C67→C106→C138→**C178**) for its next delta. **SDK-mirror guard for C178**: re-derive the errors-primitive implementers at live HEAD across Python **and** `web4-core/src/error.rs` — the yield surface is now reliably the Rust mirror.

---

## §E. Lessons (for memory)

1. **9th consecutive frozen-wrap; the SDK-mirror-expansion surface carried the entire yield for the 3rd delta running (C172, C174, C176).** entity-types byte-frozen 25 days; §A = pure verification; §B corpus-delta = 0; **all findings on §B′.** A frozen, 4×-audited, spec-side-clean file is still not "clean" until the *live-HEAD* SDK mirror set — Python **and** `web4-core/src/*.rs` — has been re-derived and diffed against the spec. Locked across C172/C174/C176.
6. **[[feedback_prose_is_not_ledger]] applied to my own flagship — "is it NEW?" and "is it LEDGERED + ADJUDICATED?" are different questions.** C176-N1/N2 are **not net-new to the corpus**: C172 already observed the Rust `EntityType` 8-variant gap (AI-split + the identical 8 omitted types) but parked it in the *LCT carry's B12 prose* marked "pre-existing, snapshot-guarded," where it was never adjudicated or promoted to a ledger line. A cross-doc observation folded into a sibling's prose **vanishes at the next delta** unless a later pass that reaches the observation's *true home* (here, entity-types §2.1, the taxonomy the enum mirrors) promotes and rules on it. Before recording a mirror observation, check whether a **sibling** audit already parked it in prose — and if it belongs to *your* target, promote it rather than re-discovering it as "new."
2. **Direction is per-finding and it alternated again.** C172 = "SDK lags spec"; C174 = "SDK over-claims, spec correct"; C176-N1 = "SDK lags spec" (Rust enum incomplete, spec canonical). The routing conclusion is identical either way (never a unilateral spec mutation on a frozen target), but the *fix owner's action* differs (extend the SDK vs correct an SDK docstring). Always adjudicate direction before writing the carry.
3. **A maturing sibling can DOWNGRADE a carry without resolving it.** C137 knew `entity.py` only as "Device hardcodes ACTIVE." By C176 the Python SDK had grown a full 15-entry registry — the *cross-language* completeness gap moved entirely to Rust, and B2/B9 shrank from "the SDK can't model most types" to "the registry's one-value-per-type schema can't express per-instance energy." Re-derive the mirror's *current* shape; do not carry a stale characterization of it forward.
4. **Same-named symbol ≠ same primitive.** Two crates (`web4-core`, `web4-trust-core`) each export `EntityType`; only one mirrors §2.1. The `head -1`-picks-the-wrong-file failure mode is real (the policy reviewer hit it this session and self-corrected). Read each candidate mirror to its definition before folding it into a coverage count. ([[feedback_prior_finding_path_provenance]])
5. **The corpus-delta disjointness rationale can INVERT between deltas on the same cross-ref.** entity-types B6's §2.4 cross-ref was disjoint at C137 *because §2.4 didn't move*, and disjoint at C176 *because the part of §2.4 that moved (conservation-scope phrase) is not the part B6 cites (slashing def)* — and the surrounding note now *corroborates* B6. Adjudicate at cited-**hunk** granularity, not section granularity. ([[feedback_snapshot_presence_guard]])

---

## Cross-Reference to Prior Audits

| Audit | Spec | Result |
|-------|------|--------|
| C8 | entity-types.md (first pass) | 10 (3H/4M/3L); 9 remediated, L3 deferred |
| C26 | entity-types.md (1st delta) | 5 new + 1 INFO; 4 remediated (#260) |
| C64 | entity-types.md (2nd delta) | 26 raw → 11 distinct; 7 routed |
| C65 | entity-types.md (remediation) | 7 applied (#344 `5baa160f`) |
| C104 | entity-types.md (2nd-delta re-audit, 3rd pass) | §A 7/7 HELD, 9 carries STAND; §B atp-adp-C79 REINFORCED B6; 0 net-new → C105 NO-OP |
| C137 | entity-types.md (3rd-delta re-audit, 4th pass) | §A 7/7 HELD, 9 carries STAND; §B atp-adp-C119 DISJOINT/CORROBORATES; 0 net-new → C138 NO-OP |
| **C176** | **entity-types.md (4th-delta re-audit, 5th pass)** | **§A: 7/7 C65 HELD by byte-freeze (25d), 9 carries STAND. §B: only atp-adp-C151 moved → B6 §2.4 cross-ref DISJOINT-from-the-edit + CORROBORATED (C151 hit conservation-scope, not slashing def); 0 net-new. §B′ SDK-mirror expansion: Python SDK now 15/15 CLEAN (B2/B9 re-framed as schema limits); Rust web4-core 0.3.0 `EntityType` = 7/15 types → C176-N1 (LOW, SDK lags spec, 8 types absent, Python-15↔Rust-7 divergence) + C176-N2 (INFO, AI-split double-models embodiment), **both PROMOTED from C172's LCT-B12 prose, not net-new to corpus** ([[feedback_prose_is_not_ledger]]); web4-trust-core::EntityType EXCLUDED (name-collision). §C: 0 net-new internal. → 3rd consecutive spec-side-clean delta; C177 = NO-OP (spec side); 2 findings route SDK-track.** |
