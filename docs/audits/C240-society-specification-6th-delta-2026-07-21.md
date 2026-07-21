# C240 — Sixth-Delta Re-Audit: SOCIETY_SPECIFICATION.md

**Date**: 2026-07-21
**Auditor**: Legion autonomous web4 track (slot `web4-20260721-060036`, v2 protocol)
**Target**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md` (498 lines, target blob `2ad453ba`)
**Lineage**: C22 (first audit, #251) → C50 (1st delta, #317) → **C51 remediation** (`958a5625`/#318) → C92 (2nd delta) → C131 (3rd delta, first fully-clean) → C164 (4th delta, second fully-clean) → **C202** (5th delta, `87377c38`/#522 §7.3 mover, third fully-clean) → **C240 (this, 6th delta)**
**Rotation**: audit-side round-robin WRAPPED back to `SOCIETY_SPECIFICATION.md` (the oldest target) after C238 (mrh-tensors 6th delta, #558 MERGED).
**Staleness at audit**: **BYTE-FROZEN since C202.** `git diff 4693e465 HEAD -- <target>` is **EMPTY**; the target blob `2ad453ba` is byte-identical to C202's snapshot. Zero commits touched the file since the #522 mover. (Contrast C202, which was the first non-frozen delta in three cycles; C240 returns to freeze.)
**Method**: Freeze-verification delta. **§A**: confirm the empty diff + re-resolve the one still-"live" section — §7.3 "Correction & Enforcement" (the #522 W4IP mover) — at the **current** sibling bytes, because a §7.3-cited sibling (`reputation-computation.md`) was touched since C202 by #541. **§B**: bounded single-pass net-new sweep (policy-reviewer-scoped per the C164 §E proportionality ruling — no finder-swarm on a byte-frozen file), refute-by-default, with the **genuine-mirror gate re-derived at live HEAD** across the Python SDK, `web4-core/src/*.rs`, and — for the first time in this file's lineage — the **`web4-policy` crate**, which is the §7.3 response-vocabulary *implementer* and landed *after* C202 (#525). **§C**: bidirectional carry re-verification under C98 snapshot-presence + C146 path-provenance guards.

---

## Verdict (summary)

- **§A — CLEAN. Freeze holds; the §7.3 mover remains regression-free.** The diff since C202 is empty, so all 478 lines of the frozen body carry C92's token-by-token verification of the 21 C51 findings by construction. The one section C202 had to regression-check (§7.3, #522) is byte-unchanged; its single sibling that moved since C202 — `reputation-computation.md` (#541, C214-N1 note) — did **not** move the cited anchor: §7.3's "Coercive/Extractive Behavior Rules category, `reputation-computation.md` §4" still resolves EXACT (`:239` "## 4. Reputation Rules" → `:339` "#### Coercive/Extractive Behavior Rules"), and #541 was already verified faithful at C232.
- **§B — 0 net-new spec defects.** The genuine-mirror gate, re-derived at live HEAD, surfaced the **`web4-policy` crate** as a mirror never gated in this file's C-series lineage — it is the *implementer* of §7.3's response vocabulary and **landed post-C202** (#525, `cb788768`), so it is the correct new surface to inspect. It is a **faithful implementer**, not a divergence: `web4-policy/src/lib.rs` defines `Response::{Notice, Quarantine, Correct, Rehabilitate}` + a parse-don't-enact kinetic class, and classifies `Response::Correct => Costly` (`:219`) — matching `hub-law-schema.md:187`. This **corroborates C202's §B-1 refutation**: `correct` is *Costly-but-enactable*, so §7.3's "beyond the reversible rungs is phased … law-inert" set is the **kinetic class only**, exactly as written. No net-new gap. The C232-N1 `reputation.delta.category` seam does **not** intersect §7.3 (which references the vocabulary abstractly, without restating the selector) — routed, not duplicated.
- **§C — 7 carries re-verified OPEN** at HEAD; none resolved downstream; all anchors unmoved; path-provenance HOLDS.
- **Net: 0 autonomous spec defects — the FOURTH consecutive fully-clean SOCIETY_SPECIFICATION delta.** The one implementer that landed since the prior audit (web4-policy #525) proves the prior refutation correct rather than opening a gap. The file's entire open frontier remains operator-DESIGN-Q (C50-B13/B14/B15) + SDK-track (C92-N1, C164-N1, C22-M3, C92-N3/B20). **C241 = declared NO-OP on the spec side.**

---

## §A — Freeze Verification + §7.3 Mover Re-Resolution

**Result: freeze holds; the §7.3 mover is unchanged and its citations re-resolve at the live sibling byte.**

### Freeze of the whole file

`git diff 4693e465 HEAD -- web4-standard/core-spec/SOCIETY_SPECIFICATION.md` is **empty**. Target blob `2ad453ba` is byte-identical to C202's snapshot (which was itself C164's snapshot outside the §7.3 hunk). No commit touched the file since `87377c38` (#522). Therefore:

- The 478 lines of frozen body outside §7.3 carry C92's token-by-token verification of all 21 C51 findings **by construction** — no new prose exists to re-verify.
- §7.3 (`SOCIETY_SPECIFICATION.md:476–495`), the only section that was "live" at C202, is itself byte-unchanged. C202 verified its nine distinct citations EXACT/HELD. Re-verification this delta is therefore limited to **any §7.3-cited sibling that moved since C202**.

### The one §7.3-cited sibling that moved: `reputation-computation.md` (#541)

`git log --since=2026-07-16 -- reputation-computation.md` returns one commit: `2bc3bafb` (#541, the C214-N1 stale-forward-ref note, applied as a §4 annotation). §7.3 binds to *"the Coercive/Extractive Behavior Rules category, `reputation-computation.md` §4."* Re-resolved at live HEAD:

| §7.3 citation | Live ground truth (HEAD) | vs C202 | Verdict |
|---|---|---|---|
| `reputation-computation.md` §4 (Reputation Rules) | `reputation-computation.md:239` `## 4. Reputation Rules` | `:239` at C202 | **EXACT, unmoved** |
| Coercive/Extractive Behavior Rules category | `reputation-computation.md:339` `#### Coercive/Extractive Behavior Rules` | `:339` at C202 | **EXACT, unmoved** |

#541 added a note elsewhere in §4 (the Effector cross-ref, verified faithful at C232) without displacing the §4 heading or the Coercive/Extractive subheading. The §7.3 → reputation-§4 binding **HOLDS**. The other §7.3 siblings (`hub-law-schema.md` response vocabulary, the W4IP-DRAFT proposal path) were unchanged since C202 by the corpus log; no re-resolution owed.

**§A conclusion: no regression.** Freeze verified; §7.3's one moved sibling did not disturb the cited anchor.

---

## §B — Net-New Sweep (bounded single-pass, refute-by-default)

**Result: 0 net-new spec defects.** One mirror surfaced by the re-derived genuine-mirror gate; inspected and refuted as a divergence (it is a faithful implementer that *corroborates* a prior refutation).

### §B-1 — genuine-mirror gate re-derived at live HEAD

Per the standing method guard, the "SDK mirror" set is re-derived at live HEAD each delta (Python SDK **and** `web4-core/src/*.rs`, including new crates). Three surfaces bear on this file:

1. **Python SDK `society.py`** — frozen since `759eaefa` (2026-04-17). Its three carried divergences (C92-N1, C164-N1, C22-M3) are byte-unchanged; re-verified in §C. No net-new.
2. **web4-core `society.rs` / `ledger.rs`** — `git log --since=2026-07-16` is empty → frozen since C202. C202's §B-2 refutation (the Rust society mirror's divergences were already catalogued in the standalone `cross-language-society-role-atp-r6-alignment-2026-05-14.md`, whose flagship CRITICAL is dead since `role.py` landed the 7-role enum on 2026-05-15) STANDS unchanged. No net-new.
3. **`web4-policy` crate — NEW surface for this lineage.** This is the §7.3 response-vocabulary *implementer* (the code half of W4IP Phase 2 N3), and it **landed after C202**: `cb788768` (#525, `feat(policy): W4IP N3 Phase 2 code half — response vocabulary, parse-don't-enact`). It is therefore the correct new mirror to gate this delta. Inspected below.

### §B-2 — CANDIDATE **REFUTED (faithful implementer; corroborates C202 §B-1)**: web4-policy `Response` vocabulary vs §7.3

`web4-policy/src/lib.rs` defines the response vocabulary §7.3 governs. Checked against §7.3's assertions:

| §7.3 assertion | web4-policy at HEAD | Verdict |
|---|---|---|
| reversible rungs `notice \| quarantine \| correct \| rehabilitate` | `Response::{Notice, Quarantine, Correct, Rehabilitate}` (lib.rs:170–179) | **present, set-exact** |
| "Each rung is an R7 act" / RWOA+S+V+F gating | ConsequenceClass mapping (lib.rs:215–222) drives per-rung gating | **HELD** |
| kinetic class "parse but remain law-inert" | lib.rs:139 "this engine parses and validates response rules; it [does not enact]"; lib.rs:195 "PARSE but law-inert"; lib.rs:345/863 tests | **HELD** |
| "Enactment **beyond the reversible rungs** is phased … law-inert" | `Correct => Some(Costly)` (lib.rs:219) — **`correct` is NOT reversible AND NOT law-inert**; only the kinetic verbs are `_ => None` (law-inert) | **CORROBORATES** |

The candidate was: does §7.3's phrase "beyond the reversible rungs is phased … law-inert" sweep `correct` (which hub-law classifies **Costly**, not Reversible) into the law-inert set, contradicting the implementer? **REFUTED.** web4-policy — which did not exist at C202 and is the authoritative implementer — resolves the ambiguity in §7.3's favor: `Correct => Costly` is a fully-enactable (non-`None`) rung, while the *kinetic* verbs map to `None` (law-inert). So "beyond the reversible rungs is phased" reads, correctly, as *the undoable/kinetic family is phased* — the same reading C202 §B-1 adopted, now confirmed by landed code. §7.3 introduces no divergence from its implementer; the implementer introduces no gap against §7.3.

**C232-N1 non-intersection.** The live cross-spec seam C232-N1 (`reputation.delta.category` response selector has no producer-side `category` field) lives in `web4-policy` law rules + `reputation-computation.md` §1/§4. §7.3 references the response vocabulary **abstractly** — it names the rungs and the `reputation-computation.md` §4 category binding, but does **not** restate the selector or the delta shape. No intersection; C232-N1 is not re-opened or duplicated here (routed, per the policy-review carry-forward note).

**§B conclusion: 0 net-new spec defects.**

---

## §C — Carry Re-Verification (bidirectional; snapshot-presence + path-provenance guarded)

All re-verified against HEAD, re-reading the **current** sibling byte and re-running each carried anchor. No sibling moved a carry target since C202 (society-roles.md / web4-society-authority-law.md unchanged in the corpus log; #541 touched reputation-computation.md but no carry cites it).

- **C50-B13 (Law Oracle name collision)** — **OPEN, unmoved.** Target `:24` defines "Law" as codified rules; `society-roles.md:71` `### 2.2 Law Oracle` still binds the name to the publisher role. Operator DESIGN-Q bundle.
- **C50-B14 (citizenship revocability vs SAL §5.1)** — **OPEN, unmoved.** `web4-society-authority-law.md:180` `### 5.1 Citizen (Genesis, Immutable)` → `:181` "Permanent birth pairing; **cannot be revoked**." — the C131/C164/C202 "SAL §5.1" citation HOLDS. Operator DESIGN-Q bundle.
- **C50-B15 (law inheritance model)** — **OPEN, unmoved.** Target `:178` "Local laws can extend but not contradict inherited laws" vs SAL's conditioned-override model. Frozen body. Operator DESIGN-Q bundle.
- **C92-N1 (solo-founder SDK guard)** — **OPEN, unmoved.** `society.py:317–318` guard live; `role.py:303–304` docstring still claims resolution while `create_society()` still rejects a solo founder — half-closed. `society.py` frozen since `759eaefa`. SDK-track bundle.
- **C164-N1 (enum-comment stale vocab)** — **OPEN, unmoved.** `society.py:92/:94` still carry pre-C51 verbs (no `mint`/`slash`), byte-unchanged. SDK-track bundle.
- **C92-N3 / C50-B20 (id-scheme example strings)** — **OPEN, present.** Non-canonical example strings unchanged (frozen body). C33 id-scheme bundle.
- **C22-M3 (`type` ↔ `event_type`)** — **OPEN, present** (`society.py:111` `event_type: LedgerEventType` vs spec envelope `type`). SDK-track.

**No carry resolved or hardened downstream since C202. No net-new carry this delta.**

---

## §D — Disposition

- **Spec side: NO ACTION.** `SOCIETY_SPECIFICATION.md` byte-frozen since C202; 0 net-new; fourth consecutive fully-clean delta. Do NOT self-edit.
- **Operator DESIGN-Q bundle (unchanged):** C50-B13 (Law Oracle name collision), C50-B14 (citizenship revocability vs SAL §5.1), C50-B15 (law inheritance model). Route to the standing operator memo; do NOT self-apply.
- **SDK-track bundle (unchanged, travels together):** C92-N1 (solo-founder guard, half-closed), C164-N1 (enum-comment stale vocab), C22-M3 (`type`↔`event_type`), C92-N3/C50-B20 (id-scheme example strings). Owed to an SDK pass; re-derive the owed set from this doc's §C text, not from a downstream §C alone ([[feedback_prose_is_not_ledger]]).
- **Cross-track (unchanged):** C232-N1 (`reputation.delta.category` recognition→response seam) STANDS with its own routing; §7.3 does not intersect it, so it is neither closed nor duplicated here.
- **web4-policy note (new, INFO — not a defect):** `web4-policy` (#525) is now the landed implementer of §7.3's response vocabulary and is faithful (`Correct => Costly`, kinetic → law-inert). Recorded as the genuine-mirror gate result for this lineage so future deltas re-derive it rather than re-discovering it.
- **C241 = declared NO-OP on the spec side.** Rotation advances (+2) to the next target; SOCIETY_SPEC's next delta ≈ C280.

---

*Method references: [[feedback_remediation_introduced_regression]] (mover regression-check), [[feedback_refute_your_best_finding]] (§B-2 refuted the flagship candidate), [[feedback_prose_is_not_ledger]] (SDK-owed set from §C text), [[feedback_snapshot_presence_guard]] + prior-finding path-provenance (§C anchors re-run at live HEAD). Genuine-mirror gate re-derived at live HEAD per the standing method guard — the new web4-policy crate is where a net-new would have lived, and it was clean.*
