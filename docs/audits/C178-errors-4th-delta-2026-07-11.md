# C178 — `errors.md` Fourth Delta Re-Audit (5th pass)

**Audit ID**: C178
**Target**: `web4-standard/core-spec/errors.md` (154 lines) — the Web4 core RFC-9457 error taxonomy
**Date**: 2026-07-11
**Auditor**: autonomous web4 session (legion, slot `120036`), v2 protocol
**Type**: **Fourth delta re-audit** (5th pass overall). Lineage: **C30** (first-pass, 2026-06-04, PR #268 → remediation #269 `aaa2bd86`, 5 autonomous) → **C66** (first delta, 2026-06-17, PR #345) → **C67** (remediation, 2026-06-17, PR #347 `6189432d`, applied 3 autonomous: B-3/B-6/B-7) → **C106** (second delta, 2026-06-27, **0 net-new**) → **C138** (third delta, 2026-07-05, **0 net-new**) → **C178**.

**Method note**: `errors.md` is **byte-identical since C67** (`git log` last touch = `6189432d`, 2026-06-17 10:03; banner `Last-Updated: 2026-06-17` accurate). Per the frozen-wrap proportionality precedent (policy-reviewed and APPROVED this fire), the audit is a single-analyst fresh-internal pass + moved-sibling corpus-delta + **the SDK-mirror expansion** (C172/C174/C176 guard, now 4th delta running). §A done by hand against live files + git; §B is the corpus-delta surface (siblings moved since the **C138 snapshot**, 2026-07-05); **§B′ is the first-class dual-mirror audit** of BOTH the Python SDK `errors.py` AND the Rust `web4-core/src/error.rs` against the spec taxonomy; §C a focused refute-by-default internal pass.

**Headline**: `errors.md`'s **3rd consecutive fully-clean delta** (C106 + C138 + C178), 0 actionable net-new. The SDK-mirror expansion — which surfaced real findings on its first application to lct.rs (C172), society.rs (C174), and entity-types (C176) — here produces a deliberate **negative result**: the Rust `error.rs` is a **false mirror** (name-collision internal error type, no wire taxonomy), so there is no Rust taxonomy surface to diverge. Recorded as **C178-N1 (INFO, forward-awareness)** so the next errors delta does not re-discover the false mirror. The Python `errors.py` remains a faithful 30-code/7-category mirror; its only divergences are the standing cross-track carries **B-4/B-5** (refined here with a corrected code count).

---

## Scope & Methodology

Because `errors.md` is unchanged since its C67 remediation, §A applies the **C56 completeness method** (audit the remediation's *claims* token-by-token, not merely "is the edit present") and the **bidirectional carry re-check** (C62/C64). §B follows the frozen-wrap lesson: the yield lives on the **corpus-delta surface** (siblings moved since the last snapshot) + the **SDK-mirror expansion** (the untracked Rust mirror is where the net-new has lived on every recent frozen-but-not-clean delta). Snapshot-presence guard (C98) applied: a pre-existing condition is not a delta finding.

Severity: **HIGH** correctness/normative contradiction; **MEDIUM** consumer-affecting inconsistency; **LOW** hygiene; **INFO** forward-awareness.
Routing: **AUTONOMOUS** (fixable in `errors.md`), **DESIGN-Q** (operator), **CROSS-TRACK** (lands in another file/track).

---

## §A — Prior-Finding Verification (C67 remediation + C106/C138 → current)

### A.1 — The 3 AUTONOMOUS C67 fixes: **all HELD by byte-freeze**

`errors.md` has not changed a byte since C67 (`6189432d`, 24 days). C106 and C138 already verified all three token-by-token and found them HELD; the byte-freeze mechanically preserves that verdict. Re-confirmed against the live file:

| C66 ID | C67 fix | Verdict | Evidence (current `errors.md`) |
|---|---|---|---|
| **B-3** (MED) | §1 rescope: `W4_ERR_*` to SAL §9 / ACP §10 / metering §6; name mcp §7.6 separately as lowercase `web4_*` | **HELD + RE-REINFORCED** | §1 L9 unchanged; mcp §7.6 remains all-lowercase (§B′.2 grep). |
| **B-6** (LOW) | §5 retitle → "Status Code Semantics" + transport-agnostic lead | **HELD** | §5 L141/L143 unchanged. |
| **B-7** (LOW) | §5 401/403 prose sharpened to mirror §2's split | **HELD** | §5 L146/L147 mirror §2.4 DENIED@401 / SCOPE@403. |

No `&#`/encoding artifacts; §3 examples still consistent with §2. PR #347 was a single-file diff → cross-file regression surface nil.

### A.2 — Bidirectional carry re-verification (against the further-moved corpus)

Re-checked the C138 ledger against the current corpus, with attention to the one sibling that moved **since C138** (acp C159 — see §B). All carries **STAND**; none resolved into a defect, none regressed:

| Carry | Status now | Note |
|---|---|---|
| **B-1** `AUTHZ_DENIED`@401 vs RFC 403 (5-mirror coordinated DESIGN-Q) | **STANDS** | handshake §10 mirror unchanged (handshake last-touch 2026-06-29 `57caa2e1`, pre-C138). Operator-gated. |
| **B-H1 / B-D1** numeric `registries/error-codes.md` orphan + SSOT inversion (DESIGN-Q) | **STANDS** | `error-codes.md` last moved 2026-06-18 — not moved since C138. |
| **B-2 / X2** `initial-registries.md` divergent core-taxonomy mirror (CROSS-TRACK) | **STANDS** | last moved 2026-06-18 — unchanged. |
| **B-4** SDK docstring "canonical per errors.md / 30 codes 7 cats" over-claim (CROSS-TRACK) | **STANDS; re-verified** | `errors.py:4-9` still claims canonical-per-errors.md while defining 30/7 (errors.md §2 = 24/6). See §B′.1. |
| **B-5** SDK cross-society statuses diverge from mcp §7.6 (CROSS-TRACK) | **STANDS; count corrected 4→6** | Re-verified against live mcp §7.6 (6 codes, not the 4 C138 cited): divergence is on **3 of 6**. See §B′.1 + Key Adjudication #3. |
| **B-8 / X3** ACP §10 / SAL §9 parallel-naming + ledger-write collision (CROSS-TRACK) | **STANDS; acp §10 re-confirmed post-C159** | acp C159 (§B) touched **zero** error-taxonomy lines; `W4_ERR_ACP_LEDGER_WRITE` (acp L537) ↔ SAL bare `W4_ERR_LEDGER_WRITE` (SAL L320) collision intact. |
| **B-9** no cross-society test vectors (INFO/CROSS-TRACK) | **STANDS** | Add after B-5 settles. |
| **B-M1** centralized-vs-distributed error ownership (DESIGN-Q) | **STANDS** | load-bearing across metering / ACP / numeric registry / textual registry. |
| **B-M2** `web4://` SSOT in `data-formats.md` (CROSS-TRACK) | **STANDS** | unchanged. |
| **B-M3** W4IDp `w4idp-ABCD` form (DESIGN-Q, inherited C29) | **STANDS** | corpus-wide identifier decision. |
| **C16-H1-remainder / C16-M8/B6** SAL §9 3 codes + `chapter-law.ttl` (CROSS-TRACK) | **STANDS** | SAL last moved 2026-06-15 — unchanged. |
| **I2** `QUICK_REFERENCE.md` custom `type` URI (INFO/CROSS-TRACK); **I3** content-type over transports (INFO) | **STAND** | unchanged. |

---

## §B — Corpus-Delta Pass (siblings moved since the C138 snapshot, 2026-07-05)

Of the siblings cited by `errors.md` (or holding its mirrored data), exactly **one moved since C138**: **acp-framework.md** (C159 `fb0075fc`, 2026-07-08). All others pre-C138 and unchanged: mcp (2026-06-30 C117), handshake (2026-06-29), metering (2026-04-29), SAL (2026-06-15), core-protocol (2026-06-05), error-codes.md / initial-registries.md (2026-06-18).

### B-1 — `acp-framework.md` C159 (#487, 2026-07-08): **B-8 surface disjoint; 0 net-new**

C159 applied C158's 3 autonomous items (authority-pinned, spec-local). Verified at diff granularity: `git show fb0075fc -- acp-framework.md | grep 'W4_ERR|## 10|LEDGER_WRITE'` returns **zero lines** — the change is disjoint from the §10 error taxonomy. The B-8 collision (`W4_ERR_ACP_LEDGER_WRITE` L537 ↔ SAL `W4_ERR_LEDGER_WRITE`) is intact and unchanged. **0 findings routed to errors.md.** (Same "adjacent-but-disjoint" mechanism as every recent errors delta: the mover touched a different normative surface of the sibling than the one errors.md cross-refs.)

---

## §B′ — SDK-Mirror Expansion (the C172/C174/C176 guard, first full application to errors)

The guard's premise: a frozen spec can be clean vs its last cycle's mirror yet blind to a Rust impl the earlier passes never audited. For errors there are **two** candidate mirrors — Python `errors.py` and Rust `web4-core/src/error.rs`. Audited both against errors.md §2.

### B′.1 — Python `web4-standard/implementation/sdk/web4/errors.py`: **faithful mirror; only standing B-4/B-5 divergences**

- **Taxonomy fidelity (24 spec codes)**: `ErrorCode` + `_ERROR_REGISTRY` reproduce all 24 errors.md §2 codes with **exact** title/status/description parity, row-for-row (spot-checked all six §2.x blocks; e.g. `AUTHZ_DENIED`@401 = §2.4 L72; `WITNESS_QUORUM`@409 = §2.3 L66; `PROTO_DOWNGRADE`@400 = §2.6 L93). No spec code omitted, no status mismatch within the 24. **The Python mirror does not contradict the spec on any §2 code.**
- **7th category (cross-society)**: `errors.py` adds `ErrorCategory.CROSS_SOCIETY` with **6** codes sourced from `mcp-protocol.md §7.6` (not errors.md). Re-derived mcp §7.6 at live HEAD (L520-525) — it defines **6** cross-society codes, and all 6 are present in the SDK:

  | SDK code | SDK status | mcp §7.6 canonical | Match? |
  |---|---|---|---|
  | `W4_ERR_CROSS_SOCIETY_UNRECOGNIZED_LCT` | 404 | `403 web4_cross_society_unrecognized_lct` | **✗ (404≠403)** |
  | `W4_ERR_CROSS_SOCIETY_EXCHANGE_INVALID` | 400 | `409 web4_cross_society_exchange_invalid` | **✗ (400≠409)** |
  | `W4_ERR_CROSS_SOCIETY_LAW_CONFLICT` | 409 | `409 web4_cross_society_law_conflict` | ✓ |
  | `W4_ERR_CROSS_SOCIETY_WITNESS_REQUIRED` | 403 | `412 web4_cross_society_witness_required` | **✗ (403≠412)** |
  | `W4_ERR_R7_REPUTATION_INVALID` | 400 | `400 web4_r7_reputation_invalid` | ✓ |
  | `W4_ERR_PROPAGATION_SCOPE_UNSUPPORTED` | 400 | `400 web4_propagation_scope_unsupported` | ✓ |

  This **corrects the standing B-5 carry's accounting**: C138 (and earlier) framed B-5 as a divergence over a **4-code** cross-society set; ground truth is a **6-code** set with divergence on **3 of 6** (statuses) plus a naming-convention transform on all 6 (mcp lowercase `web4_*` → SDK uppercase `W4_ERR_CROSS_SOCIETY_*`). Direction unchanged: **mcp owns cross-society canonicity; the divergence is entirely SDK-side.** CROSS-TRACK, SDK-track owns the fix. (The count error is a textbook [[feedback_enumeration_and_grep_hypotheses]] instance — a "4 codes" enumeration recorded as fact when the source table had grown to 6 in `7c7c43c1`.)
- **B-4 re-verified**: `errors.py:4-9` docstring says "Canonical implementation per web4-standard/core-spec/errors.md … Defines 30 error codes across 7 categories" — but errors.md is 24/6; the 6 extra come from mcp §7.6. The "canonical per errors.md" phrasing over-claims a single SSOT that does not hold (the taxonomy is split across errors.md + mcp §7.6). CROSS-TRACK, SDK-side docstring fix. **Direction: spec CORRECT; SDK docstring over-claims** (same shape as C174-N1's SDK over-claim).

**Net Python: 0 net-new; the two divergences are the standing B-4/B-5 carries, refined not multiplied.**

### B′.2 — Rust `web4-core/src/error.rs`: **FALSE MIRROR — name collision, not a taxonomy mirror (C178-N1, INFO)**

Unlike lct.rs (C172), society.rs (C174), and the entity-types Rust surface (C176) — all of which **are** canonical HUB-landed mirrors the spec pseudocode lags — `web4-core::error::Web4Error` is **not** a mirror of the errors.md wire taxonomy at all:

- `grep -rn "W4_ERR" web4-core/` → **0 hits.** The Rust core carries **no** `W4_ERR_*` code, **no** RFC-9457 Problem Details fields (`type`/`title`/`status`/`code`/`detail`/`instance`), **no** HTTP-class status codes, and **no** §2.1-2.6 category structure.
- What it *is*: a 13-variant internal `thiserror` enum for operational failures — `Crypto`, `SignatureInvalid`, `Lct`, `CoherenceBelowThreshold`, `Serialization(#[from] serde_json::Error)`, `InvalidInput`, `NotFound`, `Unauthorized`, `LctVoided`, `InvalidState`, `Ledger`, `Vault`, `DecryptionFailed` — the `Result<T, Web4Error>` return type for the crate's own functions.
- It shares only the **name** `Web4Error` with the Python SDK's `Web4Error` class. The two are **different primitives**: Python's is the wire-taxonomy carrier (requires an `ErrorCode` from the 30-code table, serializes to `application/problem+json`); Rust's is a free-form internal error with no wire contract.

**Adjudication (refute-by-default, per-finding direction):**
- Is the *absence* of a Rust wire taxonomy a spec defect? **No.** errors.md §1 scopes itself to the **core protocol / wire** error format; a core crypto/LCT/ledger library returning `Result<T>` for internal operations legitimately operates at a **different layer** and is under no obligation (spec- or HUB-side) to serialize wire errors. The absence is a **layering fact, not a divergence**. This is the same reasoning that **excluded** the name-colliding `web4-trust-core::EntityType` at C176 — a name match is not a mirror.
- Is there anything to record? **Yes, as INFO forward-awareness** (**C178-N1**): document that the errors' Rust "mirror" is a false mirror so the next errors delta does not re-run the mirror-divergence analysis against it and mis-read the missing taxonomy as a gap. **If/when web4-core grows a protocol/wire-serialization layer, that layer SHOULD implement the errors.md §2 taxonomy** (as the Python SDK's `errors.py` does) — at which point it becomes a genuine mirror and a proper divergence surface. Until then: **exclude `web4-core::Web4Error` from errors mirror-divergence analysis.** No spec action, no SDK action owed this cycle.

**Net Rust: 0 net-new defect; 1 INFO (C178-N1) recording the false-mirror boundary of the SDK-mirror-expansion guard.**

---

## §C — Fresh Internal-Consistency Pass (refute-by-default)

Focused recheck of the 154-line frozen file (each candidate read at its call site). **0 net-new internal contradictions** — byte-freeze mechanically preserves C138's clean §C, re-confirmed:

- **§2 ↔ §3 examples**: all three §3 examples (codes/statuses/titles) match their §2 rows (§3.1 AUTHZ_DENIED/401; §3.2 WITNESS_QUORUM/409; §3.3 AUTHZ_RATE/429).
- **§2 statuses ⊆ §5 list**: §2 uses exactly {400, 401, 403, 408, 409, 410, 429, 503}; §5 (L145-152) lists exactly those 8 — no orphan, no omission.
- **§1 example ↔ §2.1**: "Binding Already Exists"/409/`W4_ERR_BINDING_EXISTS` = §2.1 L45.
- **§1 Fields ↔ examples**: every example carries the mandated `status`+`title`+`code`; `type` defaults to `about:blank`; `detail`/`instance` optional and present.
- **§1 extender convention ↔ corpus**: `W4_ERR_*` (SAL/ACP/metering) vs lowercase `web4_*` (mcp §7.6) split accurate against live siblings (§B/§B′.1).

### Considered-and-dismissed (snapshot-presence guard; anti-padding transparency)

- **mcp §7.6 grew from 4→6 cross-society codes** — considered as a corpus-delta. **Dismissed as net-new**: the 2 extra codes were introduced in `7c7c43c1` (mcp v0.1.3), which **predates** the C106/C138/C178 snapshots. Per the snapshot-presence guard it is a pre-existing condition, not a delta finding. Its only live effect is the B-5 accounting correction (4→6), recorded above — a refinement of a standing carry, not a new one.
- **Rust internal variants semantically overlapping wire codes** (`Unauthorized`~AUTHZ_DENIED, `SignatureInvalid`~CRYPTO_VERIFY, `DecryptionFailed`~CRYPTO_DECRYPT, `LctVoided`~slashing) — considered as latent mirror rows. **Dismissed**: they carry no status/code/category and are internal `Result` variants at a different layer; mapping them to wire codes would be inventing a contract the crate does not assert (§B′.2). Not a divergence.
- **AGY / ACP `*_INTEGRATION_SUMMARY.md` codes** not in errors.md §1 extender list — **dismissed** (same as C106/C138): errors.md §1 lists *normative framework homes*, and the summaries predate all snapshots. At most latent INFO; no route.

---

## Classification Summary

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| **C178-N1** | INFO | Rust `web4-core::error::Web4Error` is a **false mirror** of the errors.md wire taxonomy (name collision with Python `Web4Error`; internal `thiserror` enum, no `W4_ERR_*` codes / no RFC-9457 fields). Exclude from mirror-divergence analysis; if a Rust wire/protocol layer is later added it SHOULD implement errors.md §2. Spec CORRECT — no action owed. | CROSS-TRACK (SDK, forward-awareness) |

**Totals**: 0 HIGH, 0 MEDIUM, 0 LOW, **1 INFO** net-new (forward-awareness only) = **0 actionable net-new defects**.

**§A**: 3/3 C67 autonomous fixes HELD by byte-freeze, 0 regressed. All standing carries STAND; **B-5 accounting corrected 4→6 codes** (divergence 3 of 6); no carry resolved into a defect.

**§B**: 1 moved sibling (acp C159) → disjoint from §10 error taxonomy → **0 findings routed to errors.md**.

**§B′**: Python `errors.py` = faithful 30/7 mirror, only standing B-4/B-5 cross-track divergences (refined). Rust `error.rs` = false mirror (C178-N1, INFO exclusion).

**§C**: 0 net-new internal contradictions.

**This is `errors.md`'s 3rd CONSECUTIVE fully-clean delta (C106 + C138 + C178), 0 actionable net-new.**

---

## Key Adjudication

1. **The SDK-mirror-expansion guard has a boundary — and this fire maps it.** C172/C174/C176 established that a frozen-but-clean spec's net-new lives in the untracked Rust mirror. C178 shows the guard is not universal: **not every spec primitive has a Rust mirror.** `web4-core` implements LCT, society, roles, ATP, T3/V3 — but **not** the wire-error taxonomy; its `error.rs` is an internal `Result` type, a name-collision, not a mirror. The correct move is the C176 **exclusion** discipline (a name match ≠ a mirror), producing a *negative result* that is itself worth recording (C178-N1) so the next pass does not mistake the absence for a gap.

2. **Direction decided per-finding, all off-spec (guard method holds).** Python B-4 = "SDK docstring over-claims, spec CORRECT" (C174 shape). Python B-5 = "SDK statuses diverge, mcp owns canonicity" (unchanged). Rust C178-N1 = "different layer, spec CORRECT, no obligation" (C176 exclusion shape). **Zero spec mutation; zero unilateral SDK edit this cycle.**

3. **A tight enumeration recorded as fact drifted from ground truth ([[feedback_enumeration_and_grep_hypotheses]]).** The standing B-5 carry said "cross-society statuses (404/400/403) diverge from mcp §7.6 (403/409/412)" — a **4-code** framing. Re-deriving mcp §7.6 from the live table showed **6** codes (the extra 2 landed in v0.1.3 `7c7c43c1`, pre-snapshot). B-5's *direction* was right but its *scope* was stale: divergence on **3 of 6**, with a naming transform on all 6. The lesson: re-derive the "N of X" from the source table every delta, do not carry the count.

---

## Next-Turn Carry

- **C179 errors.md remediation slot = NO-OP** (0 actionable net-new — consistent with the frozen-wrap no-op precedents). C178-N1 is INFO/cross-track forward-awareness; nothing to apply inside errors.md. Rotation advances.
- **Rotation advances to next-oldest.** After errors (now C178, 4th delta), the next file in the fixed-order round-robin is **`security-framework.md`** → its 4th-delta (lineage C31→C68→C69→C108→C140→**C180**). [Order: SOCIETY_SPEC, dictionary, SOCIETY_METABOLIC, SAL, LCT, ISP, entity-types, errors, **security**, registries, handshake, web4-lct, mcp, atp-adp, multi-device, t3-v3, reputation, acp, presence, mrh → wrap.] **Continue the SDK-mirror expansion at security** — but apply the C178 boundary lesson: check whether a genuine Rust mirror exists (`web4-core/src/*.rs` for the security primitive) before running divergence analysis; a name-collision is a false mirror, not a finding.
- **Standing operator bundle (route as ONE memo; none gate a normal audit turn)**: B-1 AUTHZ_DENIED 401→403 (5-mirror coordinated) + B-M1 distributed error ownership (4 sites) + B-H1 numeric-registry canonicity / B-D1 SSOT inversion + B-M3 W4IDp form. **Cross-track (other owners)**: B-2 initial-registries mirror, **B-4 SDK docstring over-claim**, **B-5 SDK↔mcp statuses (now 3 of 6 codes)**, B-8 ACP/SAL ledger-write, B-9 cross-society vectors, B-M2 `web4://` SSOT, C16-H1-remainder, C16-M8/B6 chapter-law.ttl, I2 QUICK_REFERENCE, I3 content-type, **C178-N1 Rust false-mirror (INFO)**. **Do not self-apply any.**
- **D0 (protocols/ cluster) still operator-gated** — unrelated to errors; do not touch.
