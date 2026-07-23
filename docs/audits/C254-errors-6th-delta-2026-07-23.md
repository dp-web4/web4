# C254 — `errors.md` Sixth Delta Re-Audit (7th pass)

**Audit ID**: C254
**Target**: `web4-standard/core-spec/errors.md` (154 lines, blob `acda930e`) — the Web4 core RFC-9457 error taxonomy
**Date**: 2026-07-23
**Auditor**: autonomous web4 session (legion, slot `000036`), v2 protocol
**Type**: **Sixth delta re-audit** (7th pass overall). Lineage: **C30** (first pass, 2026-06-04, PR #268 → remediation #269 `aaa2bd86`, 5 autonomous) → **C66** (1st delta, 2026-06-17, PR #345) → **C67** (remediation, 2026-06-17, PR #347 `6189432d`, applied 3 autonomous: B-3/B-6/B-7) → **C106** (2nd delta, 2026-06-27, **0 net-new**) → **C138** (3rd delta, 2026-07-05, **0 net-new**) → **C178** (4th delta, 2026-07-11, **0 net-new**; mapped the SDK-mirror-guard boundary) → **C216** (5th delta, 2026-07-18, **0 net-new**; live-tested the C178-N1 trigger, un-fired) → **C254**.

**Method note**: `errors.md` is **byte-identical since C67** (`git log` last touch = `6189432d`, 2026-06-17 10:03; banner `Last-Updated: 2026-06-17` accurate — **36 days frozen**, blob `acda930e`). Per the frozen-wrap proportionality precedent (policy-reviewed and APPROVED this fire), the audit is a single-analyst fresh-internal pass + moved-sibling corpus-delta + the **SDK-mirror expansion** with the **C178 false-mirror boundary** applied. §A done by hand against live files + git; §B is the corpus-delta surface (siblings moved since the **C216 snapshot**, 2026-07-18); §B′ re-derives BOTH the Python SDK `errors.py` AND the Rust `web4-core/src/error.rs` at live HEAD **and executes the C254-specific mover-guard** (did the #538 / #544 / #540 web4-core movers introduce new error variants the spec must enumerate?); §C a focused refute-by-default internal pass.

**Headline**: `errors.md`'s **5th consecutive fully-clean delta** (C106 + C138 + C178 + C216 + C254), **0 actionable net-new** — and the *first* errors delta with a **fully empty corpus-delta surface**: **zero** errors.md-cross-referenced siblings moved this interval (the last sibling movements — mcp `3e765345` 2026-07-13, SAL `1354e4c2` 2026-07-14 — both predate the C216 snapshot and were adjudicated there). The primary yield this fire is the **executed #544/#540 mover-guard**: web4-core *did* move this interval (`2ec6ae09` #544 `authority_ratchet`, `357173c4` #540 operational-key vouching, `4f76f110` oracle-scope on `role.rs`), so the guard question ("did an LCT-structure mover grow a wire-error layer errors.md must enumerate?") was **live** — and answered **clean**: `ratchet.rs`/`attestation.rs` carry **0** error-taxonomy tokens, `error.rs` is unchanged (still a 13-variant internal `thiserror` enum), and `grep -rn W4_ERR web4-core/` = **0**. The C178-N1 false-mirror boundary holds; its wire-serialization trigger remains **un-fired**.

---

## Scope & Methodology

Because `errors.md` is unchanged since its C67 remediation, §A applies the **C56 completeness method** (audit the remediation's *claims* token-by-token, not merely "is the edit present") and the **bidirectional carry re-check** (C62/C64). §B follows the frozen-wrap lesson: the yield lives on the **corpus-delta surface** (siblings moved since the last snapshot) + the **SDK-mirror expansion**. Snapshot-presence guard (C98) applied: a pre-existing condition is not a delta finding; "is it NEW?" precedes "is it TRUE?" ([[feedback_prose_is_not_ledger]]). Enumerations re-derived from ground truth, not carried ([[feedback_enumeration_and_grep_hypotheses]]). The **genuine-mirror gate** (C178/C216) is applied before §B′ divergence analysis: a name-collision is a false mirror, not a finding.

Severity: **HIGH** correctness/normative contradiction; **MEDIUM** consumer-affecting inconsistency; **LOW** hygiene; **INFO** forward-awareness.
Routing: **AUTONOMOUS** (fixable in `errors.md`), **DESIGN-Q** (operator), **CROSS-TRACK** (lands in another file/track).

---

## §A — Prior-Finding Verification (C67 remediation + C106/C138/C178/C216 → current)

### A.1 — The 3 AUTONOMOUS C67 fixes: **all HELD by byte-freeze**

`errors.md` has not changed a byte since C67 (`6189432d`, 36 days). C106/C138/C178/C216 each verified all three token-by-token and found them HELD; the byte-freeze mechanically preserves that verdict. Re-confirmed against the live file (read in full this fire):

| C66 ID | C67 fix | Verdict | Evidence (current `errors.md`) |
|---|---|---|---|
| **B-3** (MED) | §1 rescope: `W4_ERR_*` to SAL §9 / ACP §10 / metering §6; name mcp §7.6 separately as lowercase `web4_*` | **HELD** | §1 L9 unchanged (names all four homes + the mcp lowercase split verbatim). |
| **B-6** (LOW) | §5 retitle → "Status Code Semantics" + transport-agnostic lead | **HELD** | §5 L141/L143 unchanged. |
| **B-7** (LOW) | §5 401/403 prose sharpened to mirror §2's split | **HELD** | §5 L146/L147 mirror §2.4 DENIED@401 / SCOPE@403. |

No `&#`/encoding artifacts; §3 examples still consistent with §2 (§C re-verified). PR #347 was a single-file diff → cross-file regression surface nil.

### A.2 — Bidirectional carry re-verification

Re-checked the C216 ledger against the current corpus. **No** errors.md-cross-referenced sibling moved since the C216 snapshot (§B), so every carry is preserved by construction; re-confirmed against live HEAD anyway. All carries **STAND**; none resolved into a defect, none regressed:

| Carry | Status now | Note |
|---|---|---|
| **B-1** `AUTHZ_DENIED`@401 vs RFC 403 (5-mirror coordinated DESIGN-Q) | **STANDS** | handshake §10 mirror unchanged (`web4-handshake.md` last-touch `57caa2e1` 2026-06-29, pre-snapshot). Operator-gated. |
| **B-H1 / B-D1** numeric `registries/error-codes.md` orphan + SSOT inversion (DESIGN-Q) | **STANDS** | `error-codes.md` last moved `3f1d6fad` 2026-06-18 — not moved since. |
| **B-2 / X2** `initial-registries.md` divergent core-taxonomy mirror (CROSS-TRACK) | **STANDS** | `3f1d6fad` 2026-06-18 — unchanged. |
| **B-4** SDK docstring "canonical per errors.md / 30 codes 7 cats" over-claim (CROSS-TRACK) | **STANDS; re-verified** | `errors.py:1-11` still claims canonical-per-errors.md while defining 30/7 (errors.md §2 = 24/6). See §B′.1. Direction: **spec CORRECT; SDK docstring over-claims.** |
| **B-5** SDK cross-society statuses diverge from mcp §7.6 (CROSS-TRACK) | **STANDS; accounting HOLDS by construction** | mcp §7.6 table did NOT move this interval (mcp frozen since `3e765345` 07-13, pre-snapshot) → C216's 6-code accounting (3 of 6 statuses diverge + naming transform on all 6) is unchanged. See §B′.1. |
| **B-8 / X3** ACP §10 / SAL §9 parallel-naming + ledger-write collision (CROSS-TRACK) | **STANDS** | SAL §9 error table byte-stable (SAL frozen `1354e4c2` 07-14, pre-snapshot); `W4_ERR_LEDGER_WRITE` (SAL) ↔ `W4_ERR_ACP_LEDGER_WRITE` (acp) collision intact. |
| **B-9** no cross-society test vectors (INFO/CROSS-TRACK) | **STANDS** | Add after B-5 settles. |
| **B-M1** centralized-vs-distributed error ownership (DESIGN-Q) | **STANDS** | load-bearing across metering / ACP / numeric registry / textual registry. |
| **B-M2** `web4://` SSOT in `data-formats.md` (CROSS-TRACK) | **STANDS** | unchanged. |
| **B-M3** W4IDp `w4idp-ABCD` form (DESIGN-Q, inherited C29) | **STANDS** | corpus-wide identifier decision. |
| **C16-H1-remainder / C16-M8/B6** SAL §9 3 codes + `chapter-law.ttl` (CROSS-TRACK) | **STANDS** | SAL §9 error table byte-stable across the interval. |
| **I2** `QUICK_REFERENCE.md` custom `type` URI (INFO/CROSS-TRACK); **I3** content-type over transports (INFO) | **STAND** | unchanged. |
| **C178-N1** Rust `error.rs` false mirror (INFO forward-awareness) | **STANDS; re-confirmed + trigger re-tested un-fired** | 0 `W4_ERR` anywhere in web4-core at live HEAD; `Web4Error` still a 13-variant internal `thiserror` enum. See §B′.2/§B′.3. |

---

## §B — Corpus-Delta Pass (siblings moved since the C216 snapshot, 2026-07-18)

**Result: the corpus-delta surface is EMPTY this interval.** Of the siblings cited by `errors.md` (or holding its mirrored data), **none** moved since the C216 snapshot. Verified `git log -1` per file:

| Sibling (errors.md cross-ref / mirror) | Last touch | Moved since C216 (2026-07-18)? |
|---|---|---|
| `mcp-protocol.md` (§7.6 cross-society) | `3e765345` 2026-07-13 | No (pre-snapshot; adjudicated C216 §B-1) |
| `web4-society-authority-law.md` (§9) | `1354e4c2` 2026-07-14 | No (pre-snapshot; adjudicated C216 §B-2) |
| `acp-framework.md` (§10) | `fb0075fc` 2026-07-08 | No |
| `web4-handshake.md` (§10 mirror) | `57caa2e1` 2026-06-29 | No |
| `web4-metering.md` (§6) | (frozen, pre-06-29) | No |
| `core-protocol.md` (§5.1 transports) | `3084e4d2` 2026-06-05 | No |
| `registries/error-codes.md` (numeric) | `3f1d6fad` 2026-06-18 | No |
| `registries/initial-registries.md` (mirror) | `3f1d6fad` 2026-06-18 | No |

This is the first errors delta in the C-series with **zero** interval sibling movement. Both movers that *were* live at C216 (mcp §7.8 mailbox, SAL #523 Effector) were already found disjoint from the §7.6/§9 error surfaces and are behind us. **0 findings routed to errors.md from §B.** The §7.6 and §9 error tables remain byte-stable at live HEAD (their host files have not moved).

---

## §B′ — SDK-Mirror Expansion (C172/C174/C176 guard + C178 false-mirror boundary + C254 mover-guard)

Both candidate mirrors are frozen well before the snapshot, so they are held by construction; re-derived at live HEAD anyway, plus the **C254-specific mover-guard** (methodology guard: re-derive implementers at live HEAD; the mirror set is not fixed — this interval web4-core moved, so probe it).

### B′.1 — Python `web4-standard/implementation/sdk/web4/errors.py` (frozen `39fb4119`, 2026-05-17): **faithful mirror; only standing B-4/B-5 divergences**

- **Frozen since 2026-05-17** — 67 days, far before the C216 snapshot. No interval movement.
- **B-4 re-verified**: docstring still says "Canonical implementation per web4-standard/core-spec/errors.md … Defines 30 error codes across 7 categories: Binding, Pairing, Witness, Authorization, Cryptographic, Protocol, Cross-Society (mcp-protocol.md §7.6)." errors.md §2 is **24/6**; the 6 extra are the mcp §7.6 cross-society codes. "canonical per errors.md" over-claims a single SSOT that does not hold (the taxonomy is split across errors.md + mcp §7.6). **Direction: spec CORRECT; SDK docstring over-claims** (C174-N1 shape). CROSS-TRACK, SDK-side docstring fix.
- **B-5 re-verified, accounting HOLDS by construction**: `ErrorCategory.CROSS_SOCIETY` carries 6 codes sourced from mcp §7.6. Because mcp did NOT move this interval (§B), the C216/C178 accounting is unchanged: divergence on **3 of 6** statuses (`UNRECOGNIZED_LCT` 404≠403, `EXCHANGE_INVALID` 400≠409, `WITNESS_REQUIRED` 403≠412) + naming transform on all 6 (mcp lowercase `web4_*` → SDK uppercase `W4_ERR_CROSS_SOCIETY_*`). **mcp owns cross-society canonicity; the divergence is entirely SDK-side.** CROSS-TRACK, SDK-track owns the fix.

**Net Python: 0 net-new; the two divergences are the standing B-4/B-5 carries, re-verified not multiplied.**

### B′.2 — Rust `web4-core/src/error.rs` (frozen `6f7051f7`, 2026-06-13): **false mirror re-confirmed (C178-N1)**

- **Frozen since 2026-06-13** — 40 days, pre-snapshot; unchanged this interval. `Web4Error` is still a **13-variant** internal `thiserror` enum (`Crypto`, `SignatureInvalid`, `Lct`, `CoherenceBelowThreshold`, `Serialization`, `InvalidInput`, `NotFound`, `Unauthorized`, `LctVoided`, `InvalidState`, `Ledger`, `Vault`, `DecryptionFailed`) — the `Result<T, Web4Error>` return type for the crate's own functions.
- `grep -rn "W4_ERR" web4-core/` → **0 hits.** No `W4_ERR_*` code, no RFC-9457 Problem Details fields, no HTTP-class status codes, no §2 category structure. It shares only the **name** `Web4Error` with the Python SDK's wire-taxonomy carrier. **False mirror — exclude from mirror-divergence analysis** (C178-N1 boundary holds).

### B′.3 — C254 mover-guard: the #544 / #540 / oracle-scope web4-core movers introduced **no** new error taxonomy

Methodology-guard check (the mirror set is not fixed): web4-core **did** move this interval — three `web4-core/src/` commits since the C216 snapshot:

| Commit | Change | Error-taxonomy contribution |
|---|---|---|
| `2ec6ae09` (#544) | `authority_ratchet` — society ratchet level provable on the LCT (`ratchet.rs` + LCT struct) | **0** — `grep -cE 'W4_ERR\|ProblemDetail\|RFC.?9457\|"status"' ratchet.rs` = 0 |
| `357173c4` (#540) | operational-key vouching — publish a witness's signing key on its LCT | **0** — no wire-error surface; LCT-structure field |
| `4f76f110` | oracle consult/write sets on `Scope` (role-gating, Piece B) | **0** — role-scope type, not an error layer |

- `error.rs` itself is **unchanged** (still 13 variants — the enum did not gain a variant from any mover).
- `grep -rn "W4_ERR" web4-core/` across live HEAD = **0** (whole-crate re-derivation, not just the moved files).
- `attestation.rs` / `ratchet.rs` = **0** error-taxonomy tokens each.
- No new `error*.py` / `error*.rs` file was added this interval (the only `error`-matching addition since 2026-07-18 is the C216 audit **doc** itself).

**The #538 (`citizenships`, ISP/LCT-structure) mover is likewise not an error surface** — it realizes multi-citizenship on the LCT/birth-certificate structure (adjudicated C248-N1/C250 C212-I1), touches zero `W4_ERR` lines. These movers are **primitive/type-layer** additions (LCT fields, role scope), **not** a protocol/wire-serialization layer. **The C178-N1 forward-note's trigger** ("if web4-core grows a wire-serialization layer, that layer SHOULD implement errors.md §2") is **live-tested and un-fired** — for the second consecutive delta (C216 tested it on `attestation.rs`/`ratchet.rs`; C254 re-tests it on the #544/#540/oracle-scope movers).

**Net Rust: 0 net-new defect; C178-N1 false-mirror boundary re-confirmed and NOT crossed; mover-guard = confirmed clean.**

---

## §C — Fresh Internal-Consistency Pass (refute-by-default)

Focused recheck of the 154-line frozen file (each candidate read at its call site this fire). **0 net-new internal contradictions** — byte-freeze mechanically preserves C216's clean §C, re-confirmed against the full file:

- **§2 ↔ §3 examples**: all three §3 examples match their §2 rows (§3.1 `AUTHZ_DENIED`/401 = §2.4 L72; §3.2 `WITNESS_QUORUM`/409 = §2.3 L66; §3.3 `AUTHZ_RATE`/429 = §2.4 L75).
- **§2 statuses ⊆ §5 list**: §2 uses exactly {400, 401, 403, 408, 409, 410, 429, 503}; §5 (L145-152) lists exactly those 8 — no orphan, no omission.
- **§1 example ↔ §2.1**: "Binding Already Exists"/409/`W4_ERR_BINDING_EXISTS` = §2.1 L45.
- **§1 Fields ↔ examples**: every example carries the mandated `status`+`title`+`code`; `type` defaults to `about:blank`; `detail`/`instance` optional and present.
- **§1 extender convention ↔ corpus**: `W4_ERR_*` (SAL §9 / ACP §10 / metering §6) vs lowercase `web4_*` (mcp §7.6) split accurate against live siblings (§B/§B′.1 — none moved, so unchanged).

### Considered-and-dismissed (snapshot-presence guard; anti-padding transparency)

- **web4-core #544 `authority_ratchet` / #540 operational-key / oracle-scope** — considered as candidate new error mirrors (the interval's live movers). **Dismissed** (§B′.3): 0 wire-error taxonomy in any moved file; `error.rs` variant-count unchanged; not a serialization layer; C178-N1 trigger un-fired. This is the recorded confirmed-negative that is the fire's primary yield.
- **#538 `citizenships` (ISP/LCT multi-citizenship)** — considered. **Dismissed**: LCT-structure realization (C248-N1/C250), touches zero `W4_ERR`; not an error surface.
- **AGY / ACP `*_INTEGRATION_SUMMARY.md` codes** not in errors.md §1 extender list — **dismissed** (same as C106–C216): errors.md §1 lists *normative framework homes*, and the summaries predate all snapshots. At most latent INFO; no route.

---

## Classification Summary

**0 net-new findings** (no INFO this cycle — C178-N1's boundary was re-confirmed and its trigger re-tested un-fired, not re-discovered).

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| — | — | *(none)* | — |

**Totals**: 0 HIGH, 0 MEDIUM, 0 LOW, 0 INFO net-new = **0 actionable net-new defects.**

**§A**: 3/3 C67 autonomous fixes HELD by byte-freeze, 0 regressed. All standing carries STAND (incl. C178-N1 re-confirmed); no carry resolved into a defect.

**§B**: **Empty corpus-delta surface** — 0 errors.md-cross-referenced siblings moved since the C216 snapshot. §7.6 / §9 error tables byte-stable at live HEAD (host files unmoved). 0 findings routed.

**§B′**: Python `errors.py` = faithful 30/7 mirror, only standing B-4/B-5 cross-track divergences (re-verified; B-5 accounting holds by construction since mcp §7.6 did not move). Rust `error.rs` = false mirror (C178-N1 re-confirmed, 0 `W4_ERR` in web4-core, 13 variants unchanged). **C254 mover-guard = clean**: the three web4-core movers this interval (#544/#540/oracle-scope) + #538 added **no** wire-error taxonomy; C178-N1 trigger live-tested un-fired.

**§C**: 0 net-new internal contradictions.

**This is `errors.md`'s 5th CONSECUTIVE fully-clean delta (C106 + C138 + C178 + C216 + C254), 0 actionable net-new.**

---

## Key Adjudication

1. **An empty corpus-delta surface is a recorded result, not a skipped audit.** This is the first errors delta where no cross-ref'd sibling moved. The value this fire is not on the (empty) §B surface — it is the executed **§B′.3 mover-guard**. web4-core genuinely moved this interval (#544 `authority_ratchet`, #540 operational-key, oracle-scope `role.rs`), so the guard question — "did an LCT-structure mover grow the wire-error layer errors.md §2 must enumerate?" — was **live**, and answering it *clean* (0 `W4_ERR`, `error.rs` variant-count unchanged) is a governance result. A skipped audit here would have left that guard un-executed.

2. **The C178-N1 trigger is now twice live-tested and twice un-fired.** C216 tested it against `attestation.rs`/`ratchet.rs`; C254 re-tests it against the #544/#540/oracle-scope movers. Both cycles confirm: web4-core keeps growing *primitive/type-layer* structure (LCT fields, ratchet level, role scope), never a *wire-serialization* layer. The forward-note remains correctly parked — the day web4-core serializes RFC-9457 Problem Details on the wire, that layer inherits errors.md §2; until then `error.rs` stays a false mirror.

3. **B-5's count is stable *because its source is frozen* — and that was verified, not assumed.** [[feedback_enumeration_and_grep_hypotheses]] says re-derive "N of X" from the source every delta. The mcp §7.6 table's host file was checked at live HEAD and found un-moved since C216 (`3e765345` 07-13, pre-snapshot); the 6-code accounting therefore holds *by construction*, and that construction (source unmoved) is itself the recorded reason — not a trusted carry.

---

## Next-Turn Carry

- **C255 errors.md remediation slot = NO-OP** (0 actionable net-new — consistent with the frozen-wrap no-op precedents C107/C139/C179/C217). Nothing to apply inside errors.md. Rotation advances. Next errors delta ~C292.
- **Rotation advances to next-oldest → `security-framework.md` 6th delta = C256** (the rotation has wrapped; security's last audit was **C218**, 5th delta, 2026-07-18 — lineage C31→C68→C69→C108→C140→C180→C218→**C256**). Fixed order [SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, SAL, LCT, ISP, entity-types, errors, **security**, registries, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap]; entity-types was C252, errors C254, security C256. **Continue the SDK-mirror expansion at security** with the C178/C216/C254 boundary lesson: probe whether a *genuine* Rust mirror exists (`web4-core/src/*.rs` — `attestation.rs` is the likely security-primitive mirror; it carries 0 wire-error taxonomy but may carry genuine attestation/security structure worth divergence analysis at the security turn) before running divergence analysis; a name-collision is a false mirror, not a finding. Read the C218 audit entry (per_file_guards + sprint_history) before C256.
- **Standing operator bundle (route as ONE memo; none gate a normal audit turn)**: B-1 AUTHZ_DENIED 401→403 (5-mirror coordinated) + B-M1 distributed error ownership (4 sites) + B-H1 numeric-registry canonicity / B-D1 SSOT inversion + B-M3 W4IDp form. **Cross-track (other owners)**: B-2 initial-registries mirror, **B-4 SDK docstring over-claim**, **B-5 SDK↔mcp statuses (3 of 6 codes)**, B-8 ACP/SAL ledger-write, B-9 cross-society vectors, B-M2 `web4://` SSOT, C16-H1-remainder, C16-M8/B6 chapter-law.ttl, I2 QUICK_REFERENCE, I3 content-type, **C178-N1 Rust false-mirror (INFO)**. **Do not self-apply any.**
- **D0 (protocols/ cluster) still operator-gated** — unrelated to errors; do not touch.
