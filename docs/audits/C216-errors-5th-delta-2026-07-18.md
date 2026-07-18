# C216 — `errors.md` Fifth Delta Re-Audit (6th pass)

**Audit ID**: C216
**Target**: `web4-standard/core-spec/errors.md` (154 lines) — the Web4 core RFC-9457 error taxonomy
**Date**: 2026-07-18
**Auditor**: autonomous web4 session (legion, slot `060036`), v2 protocol
**Type**: **Fifth delta re-audit** (6th pass overall). Lineage: **C30** (first pass, 2026-06-04, PR #268 → remediation #269 `aaa2bd86`, 5 autonomous) → **C66** (1st delta, 2026-06-17, PR #345) → **C67** (remediation, 2026-06-17, PR #347 `6189432d`, applied 3 autonomous: B-3/B-6/B-7) → **C106** (2nd delta, 2026-06-27, **0 net-new**) → **C138** (3rd delta, 2026-07-05, **0 net-new**) → **C178** (4th delta, 2026-07-11, **0 net-new**; mapped the SDK-mirror-guard boundary) → **C216**.

**Method note**: `errors.md` is **byte-identical since C67** (`git log` last touch = `6189432d`, 2026-06-17 10:03; banner `Last-Updated: 2026-06-17` accurate — 31 days frozen). Per the frozen-wrap proportionality precedent (policy-reviewed and APPROVED this fire), the audit is a single-analyst fresh-internal pass + moved-sibling corpus-delta + the **SDK-mirror expansion** with the **C178 false-mirror boundary** applied. §A done by hand against live files + git; §B is the corpus-delta surface (siblings moved since the **C178 snapshot**, 2026-07-11); §B′ re-derives BOTH the Python SDK `errors.py` AND the Rust `web4-core/src/error.rs` at live HEAD **and checks whether any new error-mirror surface emerged this interval**; §C a focused refute-by-default internal pass.

**Headline**: `errors.md`'s **4th consecutive fully-clean delta** (C106 + C138 + C178 + C216), **0 actionable net-new**. Two genuine siblings moved this interval — **mcp-protocol.md** (`3e765345`, +§7.8 async mailbox) and **web4-society-authority-law.md** (`1354e4c2`, #523 Effector §5.6/§7.1.1) — but **both are disjoint** from the error-taxonomy surfaces errors.md cross-refs (mcp §7.6 / SAL §9): each mover added a *different* normative section and touched **zero** `W4_ERR_*` / `web4_*` lines. The SDK mirrors are frozen pre-snapshot and held by construction; the C178 Rust false-mirror boundary re-confirmed (0 `W4_ERR` anywhere in web4-core), and the two new web4-core files this interval (`attestation.rs`, `ratchet.rs`) carry **no** wire-error taxonomy — no new mirror emerged.

---

## Scope & Methodology

Because `errors.md` is unchanged since its C67 remediation, §A applies the **C56 completeness method** (audit the remediation's *claims* token-by-token, not merely "is the edit present") and the **bidirectional carry re-check** (C62/C64). §B follows the frozen-wrap lesson: the yield lives on the **corpus-delta surface** (siblings moved since the last snapshot) + the **SDK-mirror expansion**. Snapshot-presence guard (C98) applied: a pre-existing condition is not a delta finding; "is it NEW?" precedes "is it TRUE?" ([[feedback_prose_is_not_ledger]]). Enumerations re-derived from ground truth, not carried ([[feedback_enumeration_and_grep_hypotheses]]).

Severity: **HIGH** correctness/normative contradiction; **MEDIUM** consumer-affecting inconsistency; **LOW** hygiene; **INFO** forward-awareness.
Routing: **AUTONOMOUS** (fixable in `errors.md`), **DESIGN-Q** (operator), **CROSS-TRACK** (lands in another file/track).

---

## §A — Prior-Finding Verification (C67 remediation + C106/C138/C178 → current)

### A.1 — The 3 AUTONOMOUS C67 fixes: **all HELD by byte-freeze**

`errors.md` has not changed a byte since C67 (`6189432d`, 31 days). C106/C138/C178 each verified all three token-by-token and found them HELD; the byte-freeze mechanically preserves that verdict. Re-confirmed against the live file:

| C66 ID | C67 fix | Verdict | Evidence (current `errors.md`) |
|---|---|---|---|
| **B-3** (MED) | §1 rescope: `W4_ERR_*` to SAL §9 / ACP §10 / metering §6; name mcp §7.6 separately as lowercase `web4_*` | **HELD + RE-REINFORCED** | §1 L9 unchanged; mcp §7.6 remains all-lowercase (§B′.2 grep, live L520-525). |
| **B-6** (LOW) | §5 retitle → "Status Code Semantics" + transport-agnostic lead | **HELD** | §5 L141/L143 unchanged. |
| **B-7** (LOW) | §5 401/403 prose sharpened to mirror §2's split | **HELD** | §5 L146/L147 mirror §2.4 DENIED@401 / SCOPE@403. |

No `&#`/encoding artifacts; §3 examples still consistent with §2. PR #347 was a single-file diff → cross-file regression surface nil.

### A.2 — Bidirectional carry re-verification (against the further-moved corpus)

Re-checked the C178 ledger against the current corpus, with attention to the two siblings that moved **since C178** (mcp `3e765345`, SAL `1354e4c2` — see §B). All carries **STAND**; none resolved into a defect, none regressed:

| Carry | Status now | Note |
|---|---|---|
| **B-1** `AUTHZ_DENIED`@401 vs RFC 403 (5-mirror coordinated DESIGN-Q) | **STANDS** | handshake §10 mirror unchanged (`web4-handshake.md` last-touch 2026-06-29 `57caa2e1`, pre-C178). Operator-gated. |
| **B-H1 / B-D1** numeric `registries/error-codes.md` orphan + SSOT inversion (DESIGN-Q) | **STANDS** | `error-codes.md` last moved 2026-06-18 — not moved since C138. |
| **B-2 / X2** `initial-registries.md` divergent core-taxonomy mirror (CROSS-TRACK) | **STANDS** | last moved 2026-06-18 — unchanged. |
| **B-4** SDK docstring "canonical per errors.md / 30 codes 7 cats" over-claim (CROSS-TRACK) | **STANDS; re-verified** | `errors.py:4-9` still claims canonical-per-errors.md while defining 30/7 (errors.md §2 = 24/6). See §B′.1. Direction: **spec CORRECT; SDK docstring over-claims.** |
| **B-5** SDK cross-society statuses diverge from mcp §7.6 (CROSS-TRACK) | **STANDS; 6-code accounting re-verified HOLDS** | Re-derived mcp §7.6 at live HEAD (L520-525) — **still 6 codes** (403/409/409/412/400/400); the §7.8 mover did NOT touch the §7.6 table. Divergence remains 3 of 6 statuses + naming transform on all 6. See §B′.1. |
| **B-8 / X3** ACP §10 / SAL §9 parallel-naming + ledger-write collision (CROSS-TRACK) | **STANDS; SAL §9 re-confirmed post-#523** | SAL `1354e4c2` (§B) touched **zero** error-taxonomy lines; `W4_ERR_LEDGER_WRITE` (SAL L331) ↔ `W4_ERR_ACP_LEDGER_WRITE` (acp) collision intact. |
| **B-9** no cross-society test vectors (INFO/CROSS-TRACK) | **STANDS** | Add after B-5 settles. |
| **B-M1** centralized-vs-distributed error ownership (DESIGN-Q) | **STANDS** | load-bearing across metering / ACP / numeric registry / textual registry. |
| **B-M2** `web4://` SSOT in `data-formats.md` (CROSS-TRACK) | **STANDS** | unchanged. |
| **B-M3** W4IDp `w4idp-ABCD` form (DESIGN-Q, inherited C29) | **STANDS** | corpus-wide identifier decision. |
| **C16-H1-remainder / C16-M8/B6** SAL §9 3 codes + `chapter-law.ttl` (CROSS-TRACK) | **STANDS** | SAL §9 error table (L325-333) byte-stable across #523. |
| **I2** `QUICK_REFERENCE.md` custom `type` URI (INFO/CROSS-TRACK); **I3** content-type over transports (INFO) | **STAND** | unchanged. |
| **C178-N1** Rust `error.rs` false mirror (INFO forward-awareness) | **STANDS; re-confirmed** | 0 `W4_ERR` anywhere in web4-core at live HEAD; `Web4Error` still a 13-variant internal `thiserror` enum. See §B′.2. |

---

## §B — Corpus-Delta Pass (siblings moved since the C178 snapshot, 2026-07-11)

Of the siblings cited by `errors.md` (or holding its mirrored data), exactly **two moved since C178**: **mcp-protocol.md** (`3e765345`, 2026-07-13) and **web4-society-authority-law.md** (`1354e4c2`, 2026-07-14, PR #523). All others pre-C178 and unchanged: handshake (2026-06-29), metering (2026-04-29), acp (2026-07-08 C159, pre-snapshot), core-protocol (2026-06-05), error-codes.md / initial-registries.md (2026-06-18).

### B-1 — `mcp-protocol.md` (`3e765345`, +56 lines): **§7.6 error table untouched; 0 net-new**

The mover added a single new section — **§7.8 The Asynchronous Mailbox (accept-and-defer)** with subsections §7.8.1–§7.8.3. Verified at diff granularity:
- `git show 3e765345 -- mcp-protocol.md | grep -E 'W4_ERR|web4_|§7\.6|cross_society'` returns **zero** added error-taxonomy lines; the only diff-context hits are two pre-existing §7.7.7 rate-negotiation rows unrelated to the new section.
- The **§7.6 cross-society table** (the surface errors.md §1 cross-refs and the source of the SDK's 7th category) is **byte-stable at live L520-525** — still the same 6 codes (403/409/409/412/400/400) the C178 B-5 accounting recorded. The §7.8 mailbox is a message-queue conformance surface, **disjoint** from the error taxonomy.

**0 findings routed to errors.md.** Same "adjacent-but-disjoint" mechanism as every recent errors delta: the mover touched a different normative surface of the sibling than the one errors.md cross-refs.

### B-2 — `web4-society-authority-law.md` (`1354e4c2`, PR #523 Effector): **§9 error table untouched; 0 net-new**

The mover added **§5.6 Effector** (the W4IP response-side role, Auditor's sibling) and **§7.1.1 Additional Required Triples**. Verified at diff granularity:
- `git show 1354e4c2 -- web4-society-authority-law.md | grep -E 'W4_ERR|## 9|LEDGER_WRITE'` returns **zero** lines — the change is disjoint from the §9 error taxonomy.
- SAL §9's error table is **byte-stable at live L325-333**, including `W4_ERR_LEDGER_WRITE` (L331) — so the standing **B-8** collision (`W4_ERR_LEDGER_WRITE` ↔ acp `W4_ERR_ACP_LEDGER_WRITE`) and the **C16-H1-remainder** 3-code carry are both intact and unchanged.

**0 findings routed to errors.md.** (The Effector role registration is being tracked on the entity-types/SAL/W4IP surfaces — C208/C214 — none of which is the error-taxonomy surface.)

---

## §B′ — SDK-Mirror Expansion (C172/C174/C176 guard + C178 false-mirror boundary)

Both candidate mirrors are frozen **pre-snapshot**, so they are held by construction; re-derived at live HEAD anyway, plus a check for any *new* error-mirror surface (methodology guard: re-derive implementers at live HEAD, do not assume the mirror set is fixed).

### B′.1 — Python `web4-standard/implementation/sdk/web4/errors.py` (frozen `39fb4119`, 2026-05-17): **faithful mirror; only standing B-4/B-5 divergences**

- **Frozen since 2026-05-17** — 62 days, well before the C178 snapshot. No interval movement.
- **B-4 re-verified**: `errors.py:1-11` docstring still says "Canonical implementation per web4-standard/core-spec/errors.md … Defines 30 error codes across 7 categories: Binding, Pairing, Witness, Authorization, Cryptographic, Protocol, Cross-Society (mcp-protocol.md §7.6)." errors.md §2 is **24/6**; the 6 extra are the mcp §7.6 cross-society codes. The "canonical per errors.md" phrasing over-claims a single SSOT that does not hold (the taxonomy is split across errors.md + mcp §7.6). **Direction: spec CORRECT; SDK docstring over-claims** (C174-N1 shape). CROSS-TRACK, SDK-side docstring fix.
- **B-5 re-verified, 6-code accounting HOLDS**: `ErrorCategory.CROSS_SOCIETY` carries the 6 codes sourced from mcp §7.6. Because the mcp mover this interval did NOT touch the §7.6 table (§B-1), the C178 accounting is unchanged: divergence on **3 of 6** statuses (`UNRECOGNIZED_LCT` 404≠403, `EXCHANGE_INVALID` 400≠409, `WITNESS_REQUIRED` 403≠412) + naming transform on all 6 (mcp lowercase `web4_*` → SDK uppercase `W4_ERR_CROSS_SOCIETY_*`). **mcp owns cross-society canonicity; the divergence is entirely SDK-side.** CROSS-TRACK, SDK-track owns the fix.

**Net Python: 0 net-new; the two divergences are the standing B-4/B-5 carries, re-verified not multiplied.**

### B′.2 — Rust `web4-core/src/error.rs` (frozen `6f7051f7`, 2026-06-13): **false mirror re-confirmed (C178-N1)**

- **Frozen since 2026-06-13** — 35 days, pre-snapshot. `Web4Error` is still a **13-variant** internal `thiserror` enum (`Crypto`, `SignatureInvalid`, `Lct`, `CoherenceBelowThreshold`, `Serialization`, `InvalidInput`, `NotFound`, `Unauthorized`, `LctVoided`, `InvalidState`, `Ledger`, `Vault`, `DecryptionFailed`) — the `Result<T, Web4Error>` return type for the crate's own functions.
- `grep -rn "W4_ERR" web4-core/` → **0 hits.** No `W4_ERR_*` code, no RFC-9457 Problem Details fields, no HTTP-class status codes, no §2 category structure. It shares only the **name** `Web4Error` with the Python SDK's wire-taxonomy carrier. **False mirror — exclude from mirror-divergence analysis** (C178-N1 boundary holds).

### B′.3 — No new error-mirror surface emerged this interval

Methodology-guard check (the mirror set is not fixed): re-derived error implementers at live HEAD.
- No new `error*.py` / `error*.rs` file was added between 2026-07-11 and 2026-07-18 (the only interval addition matching `error` is the C178 audit **doc** itself).
- web4-core grew **two** new source files this interval — `attestation.rs` and `ratchet.rs` — but both carry **zero** wire-error taxonomy (`grep W4_ERR|ProblemDetail|RFC-9457|"status":` → 0 hits) and do not participate in the error surface at all. They are primitive/type-layer additions, not a protocol/wire-serialization layer. **The C178-N1 forward-note's trigger** ("if web4-core grows a wire-serialization layer, that layer SHOULD implement errors.md §2") **has NOT fired** — these additions are not that layer.

**Net Rust: 0 net-new defect; C178-N1 false-mirror boundary re-confirmed and NOT crossed.**

---

## §C — Fresh Internal-Consistency Pass (refute-by-default)

Focused recheck of the 154-line frozen file (each candidate read at its call site). **0 net-new internal contradictions** — byte-freeze mechanically preserves C178's clean §C, re-confirmed:

- **§2 ↔ §3 examples**: all three §3 examples match their §2 rows (§3.1 `AUTHZ_DENIED`/401 = §2.4 L72; §3.2 `WITNESS_QUORUM`/409 = §2.3 L66; §3.3 `AUTHZ_RATE`/429 = §2.4 L75).
- **§2 statuses ⊆ §5 list**: §2 uses exactly {400, 401, 403, 408, 409, 410, 429, 503}; §5 (L145-152) lists exactly those 8 — no orphan, no omission.
- **§1 example ↔ §2.1**: "Binding Already Exists"/409/`W4_ERR_BINDING_EXISTS` = §2.1 L45.
- **§1 Fields ↔ examples**: every example carries the mandated `status`+`title`+`code`; `type` defaults to `about:blank`; `detail`/`instance` optional and present.
- **§1 extender convention ↔ corpus**: `W4_ERR_*` (SAL §9 / ACP §10 / metering §6) vs lowercase `web4_*` (mcp §7.6) split accurate against live siblings (§B/§B′.1 — re-verified at live HEAD this delta).

### Considered-and-dismissed (snapshot-presence guard; anti-padding transparency)

- **mcp §7.8 async mailbox** — considered as a corpus-delta. **Dismissed as net-new for errors**: it defines message-queue conformance, not error codes; the §7.6 table it neighbors is byte-stable. Nothing to route.
- **SAL §5.6 Effector / §7.1.1 triples (#523)** — considered. **Dismissed**: additive role-registration + ontology triples, disjoint from §9 error taxonomy; tracked on the entity-types/SAL/W4IP surfaces (C208/C214), not the error surface.
- **web4-core `attestation.rs` / `ratchet.rs`** — considered as candidate new mirrors. **Dismissed** (§B′.3): 0 wire-error taxonomy; not a serialization layer; C178-N1 trigger un-fired.
- **AGY / ACP `*_INTEGRATION_SUMMARY.md` codes** not in errors.md §1 extender list — **dismissed** (same as C106/C138/C178): errors.md §1 lists *normative framework homes*, and the summaries predate all snapshots. At most latent INFO; no route.

---

## Classification Summary

**0 net-new findings** (no INFO this cycle either — C178-N1's boundary was re-confirmed, not re-discovered).

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| — | — | *(none)* | — |

**Totals**: 0 HIGH, 0 MEDIUM, 0 LOW, 0 INFO net-new = **0 actionable net-new defects.**

**§A**: 3/3 C67 autonomous fixes HELD by byte-freeze, 0 regressed. All standing carries STAND (incl. C178-N1 re-confirmed); no carry resolved into a defect.

**§B**: 2 moved siblings — mcp §7.8 mailbox and SAL #523 Effector — **both disjoint** from the §7.6/§9 error surfaces errors.md cross-refs → **0 findings routed to errors.md**. mcp §7.6 table (6 codes) and SAL §9 table byte-stable at live HEAD.

**§B′**: Python `errors.py` = faithful 30/7 mirror, only standing B-4/B-5 cross-track divergences (re-verified, 6-code accounting holds). Rust `error.rs` = false mirror (C178-N1 re-confirmed, 0 `W4_ERR` in web4-core). No new error-mirror surface emerged (`attestation.rs`/`ratchet.rs` carry no wire taxonomy).

**§C**: 0 net-new internal contradictions.

**This is `errors.md`'s 4th CONSECUTIVE fully-clean delta (C106 + C138 + C178 + C216), 0 actionable net-new.**

---

## Key Adjudication

1. **A frozen target with a moving neighborhood is still a real audit — and this fire is the textbook disjoint-drift catch.** Both interval movers (mcp §7.8, SAL #523 Effector) are exactly the kind of adjacent change the rotation exists to check: each touched a section *next to* the surface errors.md cross-refs. Verifying disjointness at diff granularity (0 `W4_ERR`/`web4_` lines in either diff; §7.6 and §9 tables byte-stable at live HEAD) is what converts "the neighbor moved" from a latent worry into a recorded negative result. Proportionality: the check is cheap, the failure mode (a sibling silently editing a cross-ref'd table) is real.

2. **The SDK-mirror-expansion guard's C178 boundary held — and this fire tested its trigger.** C178 recorded that web4-core's `error.rs` is a false mirror and set a forward-note: *if* web4-core grows a wire-serialization layer, that layer SHOULD carry errors.md §2. This interval web4-core DID grow (`attestation.rs`, `ratchet.rs`) — so the trigger was live-tested and found **un-fired**: the new files carry no wire taxonomy. The discipline (re-derive implementers at live HEAD every delta, don't assume the mirror set is fixed) worked as a *guard*, producing a confirmed negative rather than a missed mirror.

3. **B-5's re-derived count is stable because its source didn't move — but it was still re-derived, not carried.** [[feedback_enumeration_and_grep_hypotheses]] says re-derive the "N of X" from the source table every delta. The mcp §7.6 table was re-read at live L520-525 this cycle (6 codes) rather than trusting the carried "6"; the fact that it matched C178 is *because* the §7.8 mover left §7.6 untouched, which is itself the finding of §B-1.

---

## Next-Turn Carry

- **C217 errors.md remediation slot = NO-OP** (0 actionable net-new — consistent with the frozen-wrap no-op precedents C107/C139/C179). Nothing to apply inside errors.md. Rotation advances.
- **Rotation advances to next-oldest.** After errors (now C216, 5th delta), the next file in the fixed-order round-robin is **`security-framework.md`** → its 4th delta (lineage C31→C68→C69→C108→C140→**C180**). [Order: SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, SAL, LCT, ISP, entity-types, errors, **security**, registries, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap.] **Continue the SDK-mirror expansion at security** — apply the C178/C216 boundary lesson: check whether a genuine Rust mirror exists (`web4-core/src/*.rs` for the security primitive) before running divergence analysis; a name-collision is a false mirror, not a finding. (Note: `attestation.rs` landed this interval and may be a genuine security-primitive mirror — probe it at C180.)
- **Standing operator bundle (route as ONE memo; none gate a normal audit turn)**: B-1 AUTHZ_DENIED 401→403 (5-mirror coordinated) + B-M1 distributed error ownership (4 sites) + B-H1 numeric-registry canonicity / B-D1 SSOT inversion + B-M3 W4IDp form. **Cross-track (other owners)**: B-2 initial-registries mirror, **B-4 SDK docstring over-claim**, **B-5 SDK↔mcp statuses (3 of 6 codes)**, B-8 ACP/SAL ledger-write, B-9 cross-society vectors, B-M2 `web4://` SSOT, C16-H1-remainder, C16-M8/B6 chapter-law.ttl, I2 QUICK_REFERENCE, I3 content-type, **C178-N1 Rust false-mirror (INFO)**. **Do not self-apply any.**
- **D0 (protocols/ cluster) still operator-gated** — unrelated to errors; do not touch.
