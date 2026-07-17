# C202 — Fifth-Delta Re-Audit: SOCIETY_SPECIFICATION.md

**Date**: 2026-07-16
**Auditor**: Legion autonomous web4 track (slot `web4-20260716-120036`, v2 protocol)
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (498 lines, head `4693e465`, target blob `2ad453ba`)
**Lineage**: C22 (first audit, #251) → C50 (1st delta, #317) → **C51 remediation** (`958a5625`/#318) → C92 (2nd delta) → C131 (3rd delta, `286e5600`/#443, first fully-clean spec-side delta) → C164 (4th delta, `b8740803`, second fully-clean) → **C202 (this, 5th delta)**
**Rotation**: audit-side round-robin WRAPPED back to `SOCIETY_SPECIFICATION.md` (the oldest target) after C200 (mrh-tensors 5th delta, `3a1b459c`/#532 MERGED).
**Staleness at audit**: **NOT byte-frozen this delta.** Exactly one commit touched the target since C164: `87377c38` (#522, W4IP Phase 2 N3 spec half, 2026-07-14), which added a **new §7.3 "Correction & Enforcement" subsection**. `git diff b8740803 HEAD -- <target>` = **one hunk, +20 lines, all inside §7.3.** The rest of the file remains byte-frozen since C51 (`45781960`→`2ad453ba` differ only in that hunk).
**Method**: This is a **mover-regression delta**, not a freeze-verification delta (contrast C131/C164, both byte-frozen). §A: regression-check the §7.3 mover per [[feedback_remediation_introduced_regression]] — read the new prose and re-resolve **every** citation it introduces at the live sibling byte; confirm the freeze of the remaining 478 lines. §B: bounded single-pass net-new sweep (policy-reviewer-scoped per the C164 §E proportionality ruling — no finder-swarm on a near-frozen file), refute-by-default, with the genuine-mirror gate **extended to web4-core `society.rs`/`ledger.rs` for the first time in this file's C-series lineage**. §C: bidirectional carry re-verification under the C98 snapshot-presence and C146 path-provenance guards.

---

## Verdict (summary)

- **§A — CLEAN. The §7.3 mover is regression-free.** All eight distinct claims/citations the new subsection introduces resolve **exactly** against the live sibling byte (`hub-law-schema.md` response vocabulary — 4 rungs + 5-verb kinetic class; "R7 act"; "RWOA + S + V + F"; `reputation-computation.md` §4 Coercive/Extractive; the W4IP-DRAFT proposal path). The mover **replaced** the generic "Enforcement mechanisms" bullet with a cross-boundary-specific bullet — an intended consumption, not a regression. The other 478 lines are byte-identical to C164's snapshot, so C92's token-by-token verification of all 21 C51 findings holds by construction.
- **§B — 0 net-new spec defects.** One candidate raised on the new prose (§7.3's "beyond the reversible rungs is phased" gloss vs hub-law's `correct`=Costly tier) → **REFUTED** (the gloss reads as the *undoable* family, which is exactly hub-law's parse-don't-enact scoping). The genuine-mirror gate, extended to web4-core `society.rs`/`ledger.rs` for the first time here, raised a candidate (a Rust society mirror never gated in the C-series ledger) → **REFUTED as net-new AND partially STALE**: its divergences were already catalogued in the standalone `cross-language-society-role-atp-r6-alignment-2026-05-14.md`, and that doc's **flagship CRITICAL is now dead** — `role.py` landed the full 7-role `SocietyRole` enum on 2026-05-15, the day after. §7.3's own implementers (the response-vocabulary engine) are **HUB-track** — confirmed: **no** web4-core response-vocab mirror exists, so the mover opened no new gap.
- **§C — 6 carries re-verified OPEN** at HEAD; none resolved downstream; path-provenance HOLDS on all despite #523 moving two sibling files.
- **Net: 0 autonomous spec defects — the THIRD consecutive fully-clean SOCIETY_SPECIFICATION delta, and the FIRST that was not byte-frozen.** A genuine content mover (§7.3, #522) passed regression-check clean. The file's entire open frontier remains operator-DESIGN-Q (C50-B13/B14/B15) + SDK-track (C92-N1, C164-N1, C22-M3, C92-N3/B20). **C203 = declared NO-OP on the spec side.**

---

## §A — Mover Regression-Check (§7.3) + freeze of the remainder

**Result: the one moved section is regression-free; the remaining 478 lines hold by construction.**

### The mover

`87377c38` (#522) is the spec half of W4IP Phase 2 N3 (the response-verb ladder; the schema+parse+tests code half is HUB's hub-track PR against `web4-policy`/`hub-lib`). Its entire footprint on this file is one hunk in §7.3 Dispute Resolution: a new **"Correction & Enforcement"** paragraph plus a bullet-list edit. Read at the live byte (`SOCIETY_SPECIFICATION.md:476–495`), it makes these checkable assertions, each re-resolved against the **current** sibling:

| §7.3 assertion | Live ground truth | Verdict |
|---|---|---|
| response vocabulary lives in `hub-law-schema.md` | `hub-law-schema.md:148` `### Response vocabulary (W4IP N3 — prescriptive)` | **EXACT** |
| reversible rungs `notice \| quarantine \| correct \| rehabilitate` | `hub-law-schema.md:185–188` — the four rung rows, verbatim and in order | **EXACT (set + order)** |
| kinetic class `slash`/`suspend`/`revoke`/`terminate`/`halt` | `hub-law-schema.md:189` — the five kinetic verbs, verbatim | **EXACT (5/5)** |
| kinetic class is **parse-don't-enact** / "law-inert until individually ratified" | `hub-law-schema.md:207` "the engine MUST NOT enact them (they are law-inert)"; §1 parse-don't-enact clause | **HELD** |
| "Each rung is an **R7 act**" | `hub-law-schema.md:179` "Every enacted response is an **R7 act**" | **EXACT** |
| gated by "**RWOA + S + V + F**" | `hub-law-schema.md:212` `#### Gating — RWOA + S + V + F` | **EXACT** |
| Reference binds "the Coercive/Extractive Behavior Rules category, `reputation-computation.md` §4" | `reputation-computation.md:239` `## 4. Reputation Rules` → `:339` `#### Coercive/Extractive Behavior Rules` | **HELD** |
| "required evidence and veto scale with the rung's ConsequenceClass" / "the ladder *is* S and V applied to responses" | `hub-law-schema.md:179–182` — same claim, same phrasing | **EXACT** |
| W4IP-DRAFT proposal (bullet 3) | `web4-standard/proposals/W4IP-DRAFT-2026-07-13-governance-immune-enforcement.md` exists (18 KB) | **RESOLVES** |

**The bullet-list edit is an intended consumption, not a regression.** #522 replaced the generic `- Enforcement mechanisms` bullet with `- Cross-boundary (inter-society) enforcement and intrusion adjudication — proposed in proposals/W4IP-DRAFT-… (informative; not normative until ratified)`. The generic enforcement bullet was *absorbed into* the new "Correction & Enforcement" paragraph (which now supplies the intra-society enforcement model), leaving the bullet list to enumerate only what genuinely **remains** unspecified (inter-society courts, arbitration protocols, cross-boundary enforcement). The disappearance of the old bullet is by design, exactly as flagged in the prior carry note — **absence here is not a regression.**

**Internal-consistency cross-check.** §7.3's kinetic `slash` is consistent with the target's own §4.2.1 economic-event vocabulary, which C51 defined: `SOCIETY_SPECIFICATION.md:305` (`"action": "…mint|slash"`) and `:317` ("**slash** — supply destroyed per `atp-adp-cycle.md` §2.4"). The response-side kinetic `slash` and the ledger-event `slash` name the same primitive; §7.3 introduces no competing definition.

### Freeze of the remainder

`git diff b8740803 HEAD -- <target>` is a single §7.3 hunk; the other 478 lines are byte-identical to C164's snapshot, which was itself byte-identical to C92's and C131's. C92 verified all 21 C51 findings token-by-token with zero regressions; with no byte changed outside §7.3, **there is no new prose in the frozen body to re-verify.** The one moved sibling that C164 had to read (`atp-adp-cycle.md` §2.4, C151) is unchanged since C164; no new sibling intersects a cited section this delta beyond the §7.3 targets checked above.

**§A conclusion: no regression.** The genuine mover this turn — the first non-frozen delta in three cycles — is clean at every citation.

---

## §B — Net-New Sweep (bounded single-pass, refute-by-default)

**Result: 0 net-new spec defects.** Two candidates raised; both refuted.

### §B-1 — CANDIDATE **REFUTED**: §7.3's "reversible rungs" gloss vs hub-law's `correct = Costly`

§7.3 closes: *"Enactment beyond the reversible rungs is phased: kinetic verbs parse but remain law-inert…"* — yet `hub-law-schema.md:187` classifies the `correct` rung's ConsequenceClass as **Costly**, not Reversible. Read literally, "beyond the reversible rungs" would sweep `correct` into the phased/law-inert set, which would **contradict** hub-law (where only the kinetic class is parse-don't-enact; `correct` is a fully-enactable rung).

Refutation: (1) hub-law defines `correct` as "Costly — **Undoable at a cost**" (`:187`) — i.e. it *is* undoable, hence within the "reversible" family in the ordinary sense §7.3 uses, distinct from the **Irreversible** kinetic tail (`:189` "Costly / Irreversible"). The appositive "kinetic verbs parse but remain law-inert" **explicitly scopes** the phased set to the kinetic verbs; the four named rungs (all undoable) are on the enacted side. Under that reading §7.3 matches hub-law's parse-don't-enact scoping exactly. (2) §7.3 is an explicitly **non-normative pointer** subsection — its first sentence defers normativity to `hub-law-schema.md` ("expresses … through the response vocabulary of `hub-law-schema.md`"). This is the same "valid prose-summary" class C164 §B Lens-1 self-refuted (the L62 GUIDANCE case). **Verdict: REFUTED. Accurate normative claim; the "reversible" gloss reads as the undoable family, which is correct.**

### §B-2 — CANDIDATE **REFUTED (not net-new AND partially STALE)**: web4-core Rust society mirror never gated in the C-series ledger

The genuine-mirror method guard requires re-deriving the target-primitive implementers at live HEAD — Python SDK **and** `web4-core/src/*.rs` — before declaring §B clean. Doing so surfaced `web4-core/src/society.rs` (406 lines, first landed `82438958` 2026-05-13) and `web4-core/src/ledger.rs` (275 lines), a **genuine second implementation** of the society primitive that the C-series society deltas (C92/C131/C164, all byte-frozen) never examined. Its ledger event taxonomy (`LedgerEvent::{Genesis, Mint, StatusChange, …}`) and genesis path (`Society::bootstrap`) diverge from both the Python SDK and §4.2.1.

Refutation: (1) **Not net-new** — these divergences were catalogued comprehensively in the standalone `docs/audits/cross-language-society-role-atp-r6-alignment-2026-05-14.md` (1 CRITICAL + 3 HIGH + 3 MEDIUM + 4 LOW), triggered by the same `82438958` commit. Reporting them as C202 net-new would re-discover a recorded audit ([[feedback_prose_is_not_ledger]] — but here the item sits in a *sibling audit doc*, not this file's ledger). (2) **The flagship is STALE** — that doc's CRITICAL was "Python SDK has **no concept** of Society Roles." `role.py` (`d155b6a6`, 2026-05-15 — the day *after* the alignment doc) added the full 7-role `SocietyRole` enum (`role.py:43–79`: SOVEREIGN…CITIZEN) with `RoleAssignment`. **The CRITICAL is resolved; do not restore it.** This is the same inbound-staleness pattern C200 caught (the D2 numeric facet, C91-closed): an inbound cross-doc finding must be re-verified at live HEAD before it is carried, or a dead finding propagates. (3) The live residual of the alignment doc reduces to: the genesis-protocol mismatch (= **C92-N1**, already carried in §C) and the MetabolicState divergence (**cross-track** — `SOCIETY_METABOLIC_STATES.md`'s concern, not this file's). (4) **The §7.3 mover opened no new mirror gap** — its implementers are the HUB-track response-vocabulary engine (`web4-policy`/`hub-lib`), not the society SDK. Confirmed: `grep -l "quarantine\|rehabilitate\|Correction\|ResponseClass" web4-core/src/*.rs` → **NONE**. §7.3 has no web4-core twin to diverge from.

**Verdict: REFUTED. Pre-recorded in a sibling doc; flagship stale; live residual is already-carried (C92-N1) or cross-track; the mover added no gap.**

**Ledger-hygiene note (recorded, not a new carry).** The 2026-05-14 alignment doc's *live* residual is fully accounted for by existing routes (C92-N1 genesis mismatch; MetabolicState = metabolic-doc cross-track). No orphaned-item restoration is warranted this turn — unlike C164-N1, there is no live finding sitting only in prose. This note exists so the **next** society delta does not re-open the Rust mirror as "never gated": it *was* gated (2026-05-14), its flagship is stale (role.py), and its residual is routed. The instrument-baselining discipline applies here too — a cross-doc finding is evidence about that doc's snapshot until re-verified at live HEAD.

---

## §C — Carry Re-Verification (bidirectional; snapshot-presence + path-provenance guarded)

All re-verified against HEAD `4693e465`, re-reading the **current** sibling byte and re-running each carried grep at live HEAD. **#523 (`1354e4c2`, Effector) moved two carry siblings** (`society-roles.md`, `web4-society-authority-law.md`) since C164 — so path-provenance was re-checked, not assumed.

- **C50-B13 (Law Oracle name collision)** — **OPEN, unmoved.** Target `:24` still defines "Law" as "Codified rules governing entity behavior and resource allocation"; `society-roles.md:71` (`### 2.2 Law Oracle`) still binds the name to the publisher role (the #523 Effector addition landed elsewhere in that file; §2.2 heading intact). Operator DESIGN-Q bundle.
- **C50-B14 (citizenship revocability vs SAL §5.1)** — **OPEN, unmoved.** Target `:154` still frames current status as derived state. **Path-provenance re-verified post-#523**: the SAL text "Permanent birth pairing; **cannot be revoked**." is at `web4-society-authority-law.md:181` under the `### 5.1 Citizen (Genesis, Immutable)` heading at `:180` — the C131/C164 "SAL §5.1" citation HOLDS. Operator DESIGN-Q bundle.
- **C50-B15 (law inheritance model)** — **OPEN, unmoved.** Target `:178` "Local laws can extend but not contradict inherited laws" vs SAL's conditioned-override model (`web4-society-authority-law.md:128`: "child inherits parent law by default; **override** only by explicit Interpretation or Norm with higher or equal authority and no parent hard-conflict"). Operator DESIGN-Q bundle.
- **C92-N1 (solo-founder SDK guard)** — **OPEN, unmoved.** `society.py:317–318` guard live and byte-unchanged (`society.py` frozen since `759eaefa` 2026-04-17). The `role.py:303–304` docstring still **claims** the gap is resolved while `create_society()` still rejects a solo founder — half-closed, the closed half not gating genesis. SDK-track bundle.
- **C164-N1 (enum-comment stale vocab)** — **OPEN, unmoved.** `society.py:92` `# join/leave/suspend/reinstate` and `:94` `# allocate/deposit/reclaim` still carry pre-C51 verbs (no `mint`/`slash`), byte-unchanged since `759eaefa`. SDK-track bundle. (Restored to the ledger at C164; still live.)
- **C92-N3 / C50-B20 (id-scheme example strings)** — **OPEN, present.** Non-canonical `citizen_lct_1`/`external_witness_lct`/`parent_society_ledger_id` example strings unchanged (frozen body). C33 id-scheme bundle.
- **C22-M3 (`type` ↔ `event_type`)** — **OPEN, present** (`society.py:111` `event_type: LedgerEventType` vs spec envelope `type`). SDK-track.

**No carry resolved or hardened downstream since C164.** No net-new carry this delta.

---

## §D — Disposition

**There are NO autonomous spec defects to remediate.** §A: the §7.3 mover is regression-free (8/8 citations resolve; the bullet edit is an intended consumption; the frozen body holds by construction). §B: 2 candidates, both refuted (one on the new prose, one on the newly-gated Rust mirror — the latter pre-recorded and its flagship stale). §C: 6 carries re-verified OPEN, path-provenance re-checked post-#523.

- **C203 = declared NO-OP on the spec side** (precedent: C131→C132, C165). Zero bytes of `SOCIETY_SPECIFICATION.md`, any sibling, any `.ttl`, any SDK source, any schema, or any test vector were mutated by this turn.
- **Rotation advances** to `dictionary-entities.md` (lineage C17 → C52 → C94 → C132 → C166 → next).

**Standing frontier for this file** (nothing autonomously actionable):
| Item | Class | Route |
|---|---|---|
| C50-B13, C50-B14, C50-B15 | operator DESIGN-Q | operator memo (do NOT self-apply) |
| C92-N1 (guard + over-claiming docstring) | SDK-track | SDK next pass |
| C164-N1 (enum-comment stale vocab) | SDK-track | SDK next pass |
| C22-M3 (`type`↔`event_type`) | SDK-track | SDK next pass |
| C92-N3 / C50-B20 (id-scheme examples) | C33 id-scheme bundle | cross-cutting |

---

## §E — Method & Governance Notes

1. **A non-frozen delta is a different instrument than a frozen one.** C131 and C164 verified a byte-frozen file (the work was corpus-delta + carry re-verification). C202 had a genuine content mover (§7.3) and so ran a true regression-check: read the new prose, resolve every citation it *introduces* at the live sibling byte. The mover passed — but the discipline that made "pass" meaningful was re-resolving each of the eight citations against ground truth, not trusting that a merged #522 was internally consistent. [[feedback_remediation_introduced_regression]] applies to spec movers, not only SDK movers.

2. **The genuine-mirror gate found a real second impl — and refute-by-default kept it out of the ledger.** Extending the gate to `web4-core/src/society.rs` for the first time in this lineage surfaced a Rust society mirror the C-series deltas never examined. The correct move was **not** to catalogue its divergences as C202 net-new (they were already recorded in a 2026-05-14 sibling audit) and **not** to restore that doc's flagship (it is stale — `role.py` resolved it the next day). *Re-verify an inbound cross-doc finding at live HEAD before carrying it* — the same catch as C200's stale D2 numeric facet. A finding in a sibling audit doc is evidence about that doc's snapshot until proven live.

3. **"Is it NEW before is it TRUE" fired on both §B candidates.** The `correct`-ConsequenceClass gloss (§B-1) is a real observation that reads as a contradiction until you notice §7.3's "reversible" means "undoable" — matching hub-law's own tiering. The Rust mirror (§B-2) is substantively real but neither new nor (in its flagship) live. Both would have read as credible net-new findings on a mover delta; both died on the cheapest refutation.

4. **Path-provenance is not free when siblings move.** Unlike C164 (all carry siblings frozen), #523 moved two carry siblings (`society-roles.md`, `web4-society-authority-law.md`) between C164 and C202. Each carried citation was re-run at live HEAD (C146): the Law Oracle §2.2 binding, the SAL §5.1 immutability line, and the SAL §3.2.1 inheritance model all re-resolved to their recorded loci. A moved sibling invalidates the *assumption* of path stability, not the finding — but the check must actually run.

---

*C202 verdict: `SOCIETY_SPECIFICATION.md` is in good health — the **third consecutive fully-clean spec-side delta, and the first that was not byte-frozen.** §A: the sole content mover (§7.3 Correction & Enforcement, #522) is regression-free — all 8 introduced citations resolve exactly, the bullet edit is an intended consumption, the frozen 478-line body holds by construction. §B: 2 candidates, both refuted — the §7.3 "reversible" gloss reads correctly as the undoable family; the newly-gated web4-core Rust society mirror is pre-recorded (2026-05-14 alignment doc) with a stale flagship (role.py 2026-05-15). §C: 6 carries OPEN, path-provenance re-checked post-#523. C203: declared no-op. Zero mutation.*
