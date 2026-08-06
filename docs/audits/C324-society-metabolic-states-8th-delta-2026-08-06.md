# C324 — SOCIETY_METABOLIC_STATES.md, 8th delta

**Date**: 2026-08-06
**Target**: `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md`
**Prior pass**: C284 (2026-07-29, PR #590) · lineage: C21 → C54 → C96 → C133 → C168 → C206 → C244 → C284 → **C324**
**Corpus HEAD**: `36602276`
**Verdict**: **0 net-new against the spec — 8th consecutive.** 1 LOW ledger-integrity finding (**N1**), 1 INFO method finding (**N2**), 2 deferred checks closed, 2 inbound mirror candidates ruled. **Zero mutation.**

**Out of scope**: the C168-N1 `society.rs` rename (operator/publish-track gated, breaking public-API change — the auditor MUST NOT self-apply); self-answering any DESIGN-Q; mining `simulations/` (declined by construction at C284 — 126 attack sims is an unbounded finding surface); the `protocols/` cluster (D0 gates it, operator-unanswered).

---

## 0. What this pass is

The policy review **revised** the proposed scope before execution, on the ground that the spec is not this lineage's finding surface: the target has been byte-frozen 53 days across 8 windows, seven consecutive passes returned 0 net-new against it, and the last two useful findings came from the pass's *method carries* rather than from re-reading the file. Three of the five proposed scope items were **guaranteed-or-near-guaranteed nulls known before execution**.

So this is a **ledger-integrity audit**, not a spec audit. §A is a footnote. The v19 row-set reconstruction (§B) is the spine, and it is the only part of this pass that had an open outcome when it started.

The review also caught a defect in this pass's own Step-2 evidence — a window count of 62 measured from an anchor the write-up did not publish (see §A, and §F for what that anchor turns out to be).

---

## 1. §A — Target and mirror set (null by construction)

Target blob `5e3f7203`, unchanged since `a504ea41` (C55, 2026-06-14): **53 days, 8 consecutive frozen windows**, 444 lines.

All eight tracked artifacts are byte-identical to the C284 snapshot:

| Artifact | Blob at `36602276` |
|---|---|
| `web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md` | `5e3f7203` |
| `web4-standard/implementation/sdk/web4/metabolic.py` | `d3d31446` |
| `web4-standard/test-vectors/metabolic/society-metabolic-states.json` | `855eedb5` |
| `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (B14 anchor) | `2ad453ba` |
| `web4-standard/core-spec/web4-society-authority-law.md` (B15/C58-B10 anchor) | `0849ebbe` |
| `web4-core/src/society.rs` (C168-N1 anchor) | `17112f05` |
| `web4-standard/core-spec/atp-adp-cycle.md` (C96-E1 anchor) | `2d060579` |
| `web4-standard/ontology/web4-core-ontology.ttl` (M7 anchor) | `fc4b4c36` |

**Window, with both anchors published** (this is the correction the policy review required):

```
$ git log --oneline 1acf7bd2..HEAD | wc -l       →  42    # C284's own doc commit
$ git log --oneline 8bc3ef39..HEAD | wc -l       →  62    # the re-baseline C284's guard names
$ git merge-base --is-ancestor 8bc3ef39 1acf7bd2 →  YES   # the guard's anchor is 20 commits OLDER
```

Lexicon diff over the tight window:

```
$ git log --oneline 1acf7bd2..HEAD --pickaxe-regex -S'[Mm]etabolic'   →  3 commits
  e4a62d7a  audit(C320) — the token lands in C320's own audit-doc prose; its three
            other touched files (FRACTAL_ROLE_IDENTITY.md, RFC-COMPOSITE-ENTITY-IDENTITY.md,
            RFC-SHARED-POLICY-SUBSTRATE.md) contain 0 metabolic tokens at HEAD
  75dfd8f6  docs/why/PURPOSE_IS_RELATIONAL.md — prose
  89e0ca2c  whitepaper/PUBLISHER_CONTEXT.md — Publisher log prose
```

**Zero spec, SDK, crate, vector or ontology lines.** No `.ttl` file moved in-window, so the M7 absence sweep holds by blob identity rather than by re-grep.

---

## 2. §B — v19 row-set reconstruction (the spine)

**Method (v19)**: reconstruct the carry **row set** from the lineage's oldest full ledger and diff it forward. An id present in an older pass and absent from a newer one needs a *recorded disposition*, or the drop itself is the finding. Instrument, published:

```
$ grep -ohE '\b(C[0-9]+-)?(H|M|L|E|B|N|D|I|R)[0-9]+\b|INFO-?[0-9]+' <each lineage doc> | sort -u
```

### 2.1 The row set, C21 → C284

C21 (2026-05-29, 501 lines) publishes a Findings Summary with an explicit count:

> **HIGH** 3 (H1,H2,H3) · **MEDIUM** 8 (M1–M8) · **LOW** 5 (L1,L4,L5,L6,L7) · **INFO** 6 (INFO1–INFO6) · **DEMOTED** 2 (D1,D2)
> **Totals**: 16 actionable — 8 autonomous-actionable, **8 design-Q** (H1, H3, M3, M5, M7, L4, L5, L7).

C54 (2026-06-14) adds sixteen `B` rows, of which six are design-Q: **B5, B6, B7, B8, B9, B14-normative-strength**.

From C96 onward, **five consecutive passes publish the same summed count, verbatim**:

| Pass | Line | Text |
|---|---|---|
| C96 | `:70`, `:72` | "**C21 design-Q (8) — ALL STILL OPEN**" … "**C54 design-Q (6) — ALL STILL OPEN**: B5, B6, B7, B8, B9, B14-normative-strength" |
| C133 | `:69` | same, both halves, enumerated |
| C168 | `:55` | "**Design-Q (14) — ALL STILL OPEN by freeze**: C21 H1, H3, M3, M5, M7, L4, L5, L7 + C54 B5, B6, B7, B8, B9, B14-normative-strength" |
| C206 | `:57` | identical sentence |
| C244 | `:61` | identical sentence |
| **C284** | — | **no design-Q count anywhere in the document; the §C table carries 9 of the 14** |

### 2.2 N1 — five design-Q rows stopped being typed at C284, and all five are true at HEAD

**Dropped: `C54-B5`, `C54-B6`, `C54-B7`, `C54-B8`, `C54-B9`.** C284's §C carries B1/B3/B4/B11 (SDK), B14, B15/C58-B10, C168-N1, C21-H1, C21-H3, a collapsed M3/M5/M7/L4/L5/L7 row, C96-E1, and the consumed C244 charge. B5–B9 appear nowhere in the document — not as rows, not in prose, not as a range, and **with no disposition**.

They cannot have self-resolved: every one is a finding against the spec text, and the spec blob has not moved since C54 wrote them. Re-verified at `36602276`:

| Row | Charge (C54) | Re-verified at HEAD | Verdict |
|---|---|---|---|
| **B5** | §4.3 SentinelWitness monitored-state set unreconciled with §2.4/§2.5/§3.1/§7.1 | `:280` `while society.state in ['hibernation', 'torpor']` — sleep and estivation absent, while §3.1 `:189` defines `Estivation → Active: Threat resolved (threat_score < 20)` as a wake trigger the sentinel cannot fire | **TRUE** |
| **B6** | §6.1 `Society_Size` undefined; baseline per-member-vs-per-society ambiguous | `grep -n Society_Size` → **exactly one occurrence**, `:341`, inside the formula. Defined nowhere | **TRUE** |
| **B7** | §6.2 wake-penalty constants 10/100/50 ungrounded | `:352-356` `{'sleep': 10, 'hibernation': 100, 'dreaming': 50}` — no derivation, no units, no cross-ref | **TRUE** |
| **B8** | §7 omits Estivation entirely; `threat_score` has no provenance/integrity | §7 spans `:366-388`. All 10 `estivation` hits and all 4 `threat_score` hits fall **outside** that range (`:25,113,126,176,189,190,212,235,248,300,441` / `:176,189,236,237`). §7.1's vulnerability table lists Sleep, Hibernation, Torpor, Molting, Dreaming — 5 of 8 | **TRUE** |
| **B9** | §6.2 prices a `dreaming` premature-wake penalty with no §3.1 transition to attach to | §3.1 has exactly two Dreaming edges — `Active → Dreaming: Maintenance window`, `Dreaming → Active: Consolidation complete`. There is no premature-exit transition for the `'dreaming': 50 * incompleteness` penalty to price | **TRUE** |

**The mechanism is written in C284's own section header.** §C is titled:

> `## 5. §C — Carries reconciliation (collapsed to one table, per policy review)`

and opens: *"Carry-by-carry re-narration would be the same padding §A avoids."* The collapse was performed **under an explicit anti-padding instruction from C284's own policy review**, and the `Design-Q (14)` count — the single number that had made the row set self-checking for five passes — was removed in the same edit. Removing the count is what made the drop invisible: with it, 9 rows in a table under a header saying 14 is a visible contradiction; without it, a collapsed table looks complete.

**Severity: LOW.** The five rows are backstopped in this track's private carry ledger (`memory/carries.md:73`, which enumerates "DQ B5 (§4.3 sentinel) / B6 (§6.1 units) / B7 (§6.2 penalty constants) / B8 (§7 Estivation security) / B9 (Dreaming premature-exit)"). This matches the C322-N1 disposition exactly: rows that survive outside the repo are LOW; rows that exist *nowhere else* are MED (the C320-N1 clause). The caveat, recorded rather than argued: that backstop is per-agent memory, not a versioned repository artifact, and a reader of the repo's audit trail alone sees only C284.

**Disposition**: restored as full rows in §E below. No spec change proposed — B5–B9 are design-Q and remain the operator's.

### 2.3 This is the third lineage in a row, and the causes are now distinguishable

| Pass | Lineage | Rows recovered | Mechanism |
|---|---|---|---|
| C320 | society-specification | 4 (`C50-B16/B17/B18/B19`) | stopped being typed at C164, never dispositioned |
| C322 | dictionary-entities | 9 (8 B-rows + `C17-INFO3`) | **table → prose** conversion |
| **C324** | society-metabolic-states | **5** (`C54-B5…B9`) | **table → collapsed table, under an explicit anti-padding instruction, with the row count removed in the same edit** |

Eighteen rows across three consecutive reconstructions, three for three. That is no longer a per-lineage defect.

And it settles a hypothesis this series raised and then killed: **C322 proposed the anti-padding collapse as its cause and the refutation held** — C282 was the *longest* document in its lineage (397L vs 164L), so nothing had been collapsed there. That refutation was correctly scoped, not wrong; it simply needed a second lineage. **Here the anti-padding cause is confirmed, in writing, in the section header of the document that dropped the rows.** The remedy for padding is a row-dropping mechanism.

---

## 3. §C — v20 inbound mirror derivation

**Method (v20)**: derive the mirror set in the inbound citation direction — grep who cites the spec **by path** — because an outward derivation returns only what the spec points at.

```
$ grep -rl "SOCIETY_METABOLIC_STATES" . --exclude-dir=.git --exclude-dir=target   →  36 files
  (37 after this document was added; 25 audit docs, 12 non-audit)
```

**v21 self-validation — and it caught this section.** The first draft of this line read *"36 returned; 26 are audit documents; 10 are non-audit — 10 rows in the table, 10 non-audit lines in the output. Counts reconcile."* Measured, the split is **24 audit docs and 12 non-audit** (25/12 of 37 once this document exists), and the table below has **10 rows covering those 12 files**, because one row merges three archive/history files. The reconciliation is 12 files → 10 rows, *not* 10 → 10; the original line asserted an equality it had not measured, in the very sentence whose purpose is to measure it. Corrected here and recorded in §G.

Pre-registered admission criteria, recorded before the rulings were written:
**M1** cites the target by path · **M2** product-bearing/normative rather than a process log or archive · **M3** has **reach** — a divergence in it can propagate a defect to a consumer of the target.

| Inbound citer | M1 | M2 | M3 | Ruling |
|---|---|---|---|---|
| `web4-standard/implementation/sdk/web4/metabolic.py` | ✓ | ✓ | ✓ | **MIRROR** — already tracked (B1/B3/B4/B11) |
| `web4-standard/test-vectors/metabolic/society-metabolic-states.json` | ✓ | ✓ | ✓ | **MIRROR** — already tracked |
| `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` | ✓ | ✓ | ✓ | **MIRROR** — already tracked (B14) |
| `web4-standard/core-spec/web4-society-authority-law.md` | ✓ | ✓ | ✓ | **MIRROR** — already tracked (B15/C58-B10) |
| `web4-core/src/society.rs` | ✓ | ✓ | ✓ | **MIRROR** — already tracked (C168-N1) |
| `ledgers/reference/python/heartbeat_ledger.py` | ✓ | ✗ | — | **NON-MIRROR evidence source** — C284's ruling, unchanged (§D) |
| `simulations/heartbeat_ledger.py` | ✓ | ✗ | — | **DECLINED** — byte-identical twin of the above (`f61f3bc2` both) |
| `archive/**` (2 files), `docs/history/STATUS-2026-02.md` | ✓ | ✗ | — | **ARCHIVE** — M2-fail by tree |
| **`whitepaper/PUBLISHER_CONTEXT.md:585`** | ✓ | **✗** | — | **NON-MIRROR (new ruling)** — a Publisher-track process log; it records the *audit*, not the spec's normative content. **Admissible as an independent external witness**: it records "C21 … 16 findings → #250 resolve 8, defer **8** design-Q", corroborating the C21 half of §B's row set from outside the audit lineage. It says nothing about C54, so it does not backstop B5–B9. |
| **`web4-standard/README.md:60`** | ✓ | ✓ | **✗** | **NON-MIRROR for this lineage (new ruling)** — the line carries a `**NEW**` badge on a 1.0.0 Proposed Standard frozen 53 days. Widened before charging (per the empty-column-vs-missing-cell rule): `grep -c '\*\*NEW\*\*'` → **7**, spanning SOCIETY_SPECIFICATION, r7-framework, reputation-computation and three others. It is a whole-README staleness pattern, not a metabolic defect, and charging it here would manufacture a finding out of a corpus property. **Not filed.** Recorded observation for whoever owns that file — and note that `web4-standard/README.md` is cited inbound by many specs and is audited by no lineage. |

**Result: the mirror set neither expanded nor contracted.** Both previously-unread candidates fail admission, and both failures are the *informative* kind — one is an external corroborating witness, one is a corpus property the widening step killed.

---

## 4. §D — The two checks C284 deferred to this pass (one row each)

| Check | C284's guard | Instrument, re-run at `36602276` | Result |
|---|---|---|---|
| Did `ledgers/reference/python/heartbeat_ledger.py` change or get promoted? | guard item 2 | `git log --oneline -- <path>` → **one commit in its entire history** (`7fb0284f`); blob `f61f3bc2`, byte-identical to its `simulations/` twin | **UNCHANGED, not promoted.** M2-fail stands; its §5.1 decay divergence remains evidence for C21-H1/H3, not a defect |
| Has anything begun keying authority/law/ATP off `society.state`? | guard item 3 | `git grep -nE 'society\.state\|inner\.state' -- '*.rs' \| grep -v assert` → `4` (a `':!*test*'` pathspec does **not** work here — see §G.2) | **NO.** 4 non-test consumers, all display/serialization: `hub/hub-daemon/src/admin.rs:295` (`format!` into an HTML `<dd>`), `hub/hub-daemon/src/main.rs:1159` (`println!`), `web4-trust-core/src/bindings/wasm.rs:628` + `:673` (`format!` → JS string), plus the committed declaration at `web4-trust-core/pkg/web4_trust_core.d.ts:325`. **C168-N1 / C284-N1 stand at unchanged reach** |

### N2 (INFO, method) — two of C284's five published anchors drifted inside one window

C284 published `admin.rs:282` and `main.rs:1154`. At HEAD they are **`admin.rs:295`** and **`main.rs:1159`** (+13, +5). The two `wasm.rs` anchors held exactly.

```
$ git log --oneline 1acf7bd2..HEAD -- hub/hub-daemon/src/admin.rs hub/hub-daemon/src/main.rs
  → 10 commits   (of 42 in the window)
```

Nothing is wrong in either file, and the finding is not a defect in anything. It is a measurement: **in the same window, this lineage's spec anchors moved 0 times and its hub anchors moved 10 times.** Anchor half-life is a property of the *tree an anchor points into*, not of the carry that holds it — and this lineage's carry set now spans both extremes, holding line numbers in a file frozen 53 days and line numbers in a file that took a commit every four days.

Worth recording as a positive result rather than a defect: **C284's own instruction — "re-run the published instrument, do not re-use this count" — is what caught this.** That instruction was written *because* C284 had just been caught publishing a consumer count of 2 that measured 4. This is the first recorded occasion on which the publish-the-instrument discipline paid out on the next pass. Proposed as method carry **v22** (§F).

---

## 5. §E — Carries ledger, restored to full rows

Every open item on this lineage, one row each. The five §B rows are restored here; nothing else changed state this window.

| Carry | Class | Anchor | Anchor blob | State at `36602276` |
|---|---|---|---|---|
| **C21-H1** §2.3/§5.1 silent on Sleep `update_rate` | DESIGN-Q | spec §2.3 / §5.1 `:297` | `5e3f7203` | OPEN — demonstrated at C284 §3.1; cite, do not re-derive |
| **C21-H3** §5.1 single column mixes incommensurable axes | DESIGN-Q | spec §5.1 `:293-302` | `5e3f7203` | OPEN — as above |
| **C21-M3** emergency-state entry only from Active | DESIGN-Q | spec §3.1 | `5e3f7203` | OPEN, held by freeze |
| **C21-M5** define "dormant" | DESIGN-Q | spec | `5e3f7203` | OPEN — couples to B15/C58-B10 |
| **C21-M7** `web4:MetabolicState` absent from ontology | DESIGN-Q | `web4-core-ontology.ttl` | `fc4b4c36` | OPEN — absence holds; 0 `.ttl` files moved in-window |
| **C21-L4** Estivation 10% < Sleep 15% ordering | DESIGN-Q | spec §6.1 | `5e3f7203` | OPEN, held by freeze |
| **C21-L5** Rest queued-vs-refuse | DESIGN-Q | spec §2.2 | `5e3f7203` | OPEN, held by freeze |
| **C21-L7** §6.2 wake-penalty state coverage | DESIGN-Q | spec §6.2 | `5e3f7203` | OPEN, held by freeze |
| **C54-B5** §4.3 sentinel monitored-set — Estivation exit unfireable | DESIGN-Q | spec `:280` vs `:189` | `5e3f7203` | **OPEN — RESTORED (§B.2), re-verified TRUE** |
| **C54-B6** §6.1 `Society_Size` undefined + baseline units | DESIGN-Q | spec `:341` | `5e3f7203` | **OPEN — RESTORED, re-verified TRUE** |
| **C54-B7** §6.2 penalty constants 10/100/50 ungrounded | DESIGN-Q | spec `:352-356` | `5e3f7203` | **OPEN — RESTORED, re-verified TRUE** |
| **C54-B8** §7 omits Estivation + `threat_score` provenance | DESIGN-Q | spec `:366-388` | `5e3f7203` | **OPEN — RESTORED, re-verified TRUE** |
| **C54-B9** §6.2 prices a Dreaming premature-wake with no §3.1 transition | DESIGN-Q | spec §6.2 vs §3.1 | `5e3f7203` | **OPEN — RESTORED, re-verified TRUE** |
| **C54-B14** §1.4 MUST-conform vs "Proposed Standard" + §10 SHOULD | DESIGN-Q + cross-track | `SOCIETY_SPECIFICATION.md:89` | `2ad453ba` | OPEN, HELD by blob identity |
| **C54-B1** SDK hibernation-wake omits `new_citizen`/90-day | CROSS-TRACK (SDK) | `metabolic.py:147` | `d3d31446` | STILL STALE by freeze |
| **C54-B3** SDK "Daily ATP Cost" vs spec §6.1 "Hourly" (`:341`) | CROSS-TRACK (SDK) | `metabolic.py:207` | `d3d31446` | STILL STALE |
| **C54-B4** SDK Torpor `"Frozen + alert bonus"` vs spec `"Frozen"` (`:299`) | CROSS-TRACK (SDK) | `metabolic.py:110` | `d3d31446` | STILL STALE |
| **C54-B11** SDK comment "Rest: queued" vs `return state == ACTIVE` | CROSS-TRACK (SDK) | `metabolic.py:412-413` | `d3d31446` | STILL STALE |
| **C54-B15 / C58-B10** SAL §3.6 dormant list omits Rest; "SHOULD defer" vs target wake | DESIGN-Q, two-sided | `web4-society-authority-law.md:138-141` | `0849ebbe` | OPEN, HELD — composes with C168-N1 |
| **C96-E1** ATP conservation cross-ref | CROSS-TRACK | `atp-adp-cycle.md` §3.3 | `2d060579` | HELD |
| **C168-N1 / C284-N1** `society.rs` 5-phase enum mis-cites the 8-state spec | DESIGN-Q + publish-track | `web4-core/src/society.rs:33-48` | `17112f05` | OPEN — reach **unchanged** this window (§D). Rename is breaking; operator-gated |
| **C284-N2** §5.2 `calculate_metabolic_reliability` as absence-never-grants precedent | INFO → #580 survey | spec §5.2 | `5e3f7203` | ROUTED, awaiting #580 |
| **C284-N3** C21-H1/H3 demonstration | — | — | — | CONSUMED — cite, do not re-derive |
| **C244** LCT §1.2-vs-§5 charge | — | — | — | **CONSUMED — do NOT re-open** |

**Design-Q total: 14** — C21 ×8 (H1, H3, M3, M5, M7, L4, L5, L7) + C54 ×6 (B5, B6, B7, B8, B9, B14-normative-strength). The count is restored alongside the rows, because §B.2 shows it was the count going missing that hid the rows.

**Refuted at C284 — do NOT resurrect**: R1 (#580-vs-§5.1 dormancy-freeze — §3.2 publishes the state, so it is inspectable, not imputed); R2 (the 2026-05-11 triage "archived this file" claim — basename collision).

---

## 6. §F — Method notes

- **The anti-padding remedy is a row-dropping mechanism (§B.2, §B.3).** This is not an argument against anti-padding discipline — C284's §A collapse was right, and a 7th consecutive re-narration of a frozen blob would have been worthless. It is a statement about *what* may be collapsed. Prose about a carry is compressible; the carry's **row** is not, because the row is the only thing that survives into the next pass. Proposed as a standing rule: **a ledger may collapse its narration but must publish its row count, and a pass that reduces the row count must name the disposition of every row it drops.**
- **v22 (proposed): anchor half-life is a property of the anchored tree.** §D measured 0 spec-anchor moves and 10 hub-anchor moves in one 42-commit window. A guard that publishes line numbers into an actively-developed tree expires on a different clock than one publishing into a frozen spec, and this lineage's carry set holds both. Per-file guards should record, per anchor, which clock it is on — and re-resolve hot-tree anchors by content every pass rather than by line number.
- **The publish-the-instrument discipline paid out for the first time.** C284 added "re-run the published instrument, do not re-use this count" after being caught with a consumer count of 2 that measured 4. One window later that instruction is what surfaced N2. Recorded because the discipline has until now only ever been observed *failing*.
- **The guard's re-baseline anchor is 20 commits older than the pass that wrote it** (§A: `8bc3ef39` is an ancestor of C284's own doc commit `1acf7bd2`). Harmless — a wider window is a conservative one — but it is the whole of the 62-vs-42 discrepancy the policy review caught in this pass's Step-2 evidence, and it means five prior passes' "window" figures are not comparable to each other unless the anchor is published. **Publish the anchor beside the count**, the same way the instrument goes beside the number.
- **The cadence question is escalated this session as a standalone artifact**, not as a line in this document — see `C324-cadence-design-q-operator-memo-2026-08-06.md`. Nine consecutive passes recorded it inside an audit doc, where it died every time, for the structural reason §B.2 documents: a line in an audit doc is not a decision request.

**Guard for the next metabolic delta (~C364) — do NOT re-open as net-new:**

1. Target byte-frozen `5e3f7203` since `a504ea41`; **8 consecutive clean passes**. Re-baseline from **`36602276`** (this pass's HEAD — not an ancestor of it).
2. **Design-Q row count is 14.** If a future §C table carries fewer, that is a defect in the table, not a resolution. C54-B5…B9 are restored and re-verified TRUE at `5e3f7203`; they cannot self-resolve while the blob holds.
3. `ledgers/` stays a non-mirror evidence source (M2-fail, `f61f3bc2`, one commit in its history). Check only whether it changed.
4. **Hot-tree anchors must be re-resolved by content, not reused**: `admin.rs` and `main.rs` moved twice in two windows. `wasm.rs:628`/`:673` and the `.d.ts:325` declaration held. Instrument, in the form that actually returns 4 — **do not substitute a `':!*test*'` pathspec, which returns 7 (§G.2)**: `git grep -nE 'society\.state|inner\.state' -- '*.rs' | grep -v assert`.
5. `web4-standard/README.md`'s 7 `**NEW**` badges are a whole-README property ruled out of this lineage at C324. Do not re-file it here.
6. C21-H1/H3 carry a demonstration (C284 §3.1) and B5–B9 carry a re-verification (C324 §B.2). Cite both; re-derive neither.

---

## 7. §G — Post-write instrument re-run (v17/v21)

Every count above was re-run **after** this document was written, at a different scope than it was first taken:

| Claim | Re-run instrument (different scope) | Result |
|---|---|---|
| B5–B9 absent from C284 | `grep -cE '\bB[5-9]\b' <doc>` | C96 `6` · C133 `6` · C168 `2` · C206 `1` · C244 `1` · **C284 `0`** |
| Design-Q count published 5× then dropped | `grep -ciE 'design-q \([0-9]+\)' <doc>` | C96 `4` · C133 `3` · C168 `1` · C206 `1` · C244 `1` · **C284 `0`** |
| §7 omits Estivation | `awk 'NR>=366 && NR<=388' <target> \| grep -ci estivation` | `0` (and `threat_score` → `0`) |
| `Society_Size` undefined | `grep -c 'Society_Size' <target>` | `1` — the formula line, nothing else |
| 4 non-test `society.state` consumers | see below — **the published instrument failed** | corrected |
| Inbound sweep, audit/non-audit split | `grep -rl … \| grep -c 'docs/audits/'` | **24 / 12** (25/12 of 37 with this doc) — see below |

**Three corrections, two of them to this section's own claims.**

1. **§D's attribution (caught before publication).** An earlier draft attributed the `admin.rs` drift to a single commit, `49900dc7` (the hub XSS fix). Re-run against the tight window, **10** commits touched `admin.rs`/`main.rs`, and `49900dc7` is in the *wider* `8bc3ef39` window, not the tight one. §D publishes the corrected figure.
2. **The consumer-count instrument does not return the count it is cited for.** This section first published `git grep … -- '*.rs' ':!*test*' ':!*tests*'` as the re-run for "4 non-test consumers". Executed, it returns **7 lines**: the pathspec cannot exclude `web4-core/src/society.rs:321/341/344`, which are assertions inside an in-file `#[cfg(test)]` module, not a file whose path contains `test`. The count of 4 is correct; **the instrument published for it is not**, and a next auditor who ran it as written would read 7. The working instrument is `git grep -nE 'society\.state|inner\.state' -- '*.rs' | grep -v assert | wc -l` → `4`. §D and the guard now carry that form. This is v21 exactly — *printing an instrument is not printing what it returns* — occurring inside the section whose job is to prevent it, one document after C284 was caught the same way.
3. **The §C reconciliation asserted an equality it had not measured** (36 → "26 audit / 10 non-audit", "10 rows, 10 lines"). Measured: **24 audit / 12 non-audit**, and 12 files map to 10 table rows because one row merges three archive/history files. Corrected in §C.

Both surviving errors are the same shape and neither changes a verdict: the *numbers a finding rests on* were re-measured and held, while the *numbers describing the measurement* were written from expectation. That is where the third-in-a-row miscounted-evidence-cell pattern actually lives.

---

## 8. Conclusion

Eighth consecutive frozen window, **eighth consecutive clean verdict on the spec** — and the third consecutive pass in this corpus where the yield came from auditing the ledger rather than the artifact.

The result worth carrying: **five design-Q findings against a byte-frozen spec disappeared from the record because a policy review correctly told the previous pass to stop padding, and the pass collapsed the row count along with the narration.** All five are still true; none could ever have self-resolved; the document that dropped them was, by every other measure, the most careful in the lineage. Three lineages have now been reconstructed and three have lost rows — 18 in total — which makes this a property of the C-series ledger discipline rather than an accident in any one pass. The fix is cheap and is proposed in §F: collapse narration freely, but publish the row count, and name the disposition of every row you drop.

Zero mutation. 0 net-new against the target. 1 LOW restored to the ledger, 1 INFO method finding, 2 deferred checks closed negative, 2 inbound candidates ruled out with the reasons recorded — and **three of this pass's own cells corrected by the post-write re-run**, two of them inside §G itself, published in full rather than quietly fixed.

---

*Accountability self-audit: **n/a**. This pass creates no surface and causes no consequential act — it adds two documents under `docs/audits/` and mutates no spec, schema, code or governed state. Every defect it names is routed, not applied; the one item that would be a consequential act (the C168-N1 enum rename, breaking across two published WASM faces and a committed `.d.ts`) is operator-gated and was held out of scope before execution. Confirmed with the policy reviewer at Step 4.*

*Audit produced under Autonomous Session Protocol v2 by `legion-web4-20260806-120032`. Policy review: REVISE → five changes required and accepted verbatim before any evidence was gathered (reframe from spec audit to ledger-integrity audit; demote §A; budget the deferred checks at one row each; publish every count's anchor; escalate the cadence question as a standalone operator memo).*
