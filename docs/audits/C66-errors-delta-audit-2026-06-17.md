# C66 — `errors.md` First Delta Re-Audit (prior C30)

**Audit ID**: C66
**Target**: `web4-standard/core-spec/errors.md` (152 lines) — the Web4 core RFC-9457 error taxonomy
**Date**: 2026-06-17
**Auditor**: autonomous web4 session (legion, slot `000047`), v2 protocol
**Type**: **First delta re-audit** of `errors.md`. Prior coverage: **C30** (first-pass, 2026-06-04, PR #268) → remediation **PR #269** (`aaa2bd86`, "resolve 5 autonomous-actionable C30 findings"). This audit verifies that remediation held, checks for remediation-introduced defects, re-verifies the C30 design-Q / cross-track carries against the **current** corpus, and runs a fresh refute-by-default finder pass.
**Method note**: §A (prior-finding verification) done by hand against the live files + git. §B executed as a multi-agent workflow (`wf_bb554451-a68`, 23 agents, 5 primitive-clustered finder lenses each followed by an adversarial refute-by-default verifier): **18 raw candidates → 11 survived → 9 distinct after dedup, 7 refuted**. Every surviving cross-doc claim was then hand-verified with a loose grep before assertion (per the C64-B8 false-positive lesson).

---

## Scope & Methodology

`errors.md` was byte-stable since its C30 remediation (`git log` confirms last touch = `aaa2bd86`, 2026-06-04 10:29; banner `Last-Updated: 2026-06-04` is accurate, not stale). Because the file is unchanged since remediation, §A applies the **C56 completeness method**: audit the remediation's own claims token-by-token against the canonical sources, not merely "is the edit present."

Three passes:
1. **§A — prior-finding verification + regression + bidirectional-carry re-check.** Did the 5 AUTONOMOUS C30 fixes + the I1 banner hold? Did the remediation introduce new defects? Have the 3 DESIGN-Q / 3 CROSS-TRACK carries resolved downstream or hardened?
2. **§B — fresh multi-agent finder pass** (internal-consistency / RFC-9457+HTTP-semantics / SDK+registry mirror / cross-spec error-systems / primitive-clustered blindspot), refute-by-default.
3. **Mirror sweep** of the first-pass "SDK aligned" assumption against the **current** `errors.py` (C64-B2/B9 lesson — first-pass alignment claims go stale).

Severity: **HIGH** = correctness/normative contradiction; **MEDIUM** = consumer-affecting inconsistency or wrong normative citation; **LOW** = hygiene/reference discipline; **INFO** = forward-awareness.
Routing: **AUTONOMOUS** (fixable inside `errors.md`, no design decision), **DESIGN-Q** (operator decision), **CROSS-TRACK** (fix lands in another file).

---

## §A — Prior-Finding Verification (C30 → current)

### A.1 — The 5 AUTONOMOUS C30 findings + I1 banner: **all HELD**

| C30 ID | Fix | Verdict | Evidence (current `errors.md`) |
|---|---|---|---|
| **A-M1** | align example titles to §2 table; make §3.1 a coherent *denied* case | **HELD** | §1 example L18 `"Binding Already Exists"` = §2.1 L45; §3.1 L102 `"Authorization Denied"` = §2.4 L72; §3.1 detail L105 reworded to a generic capability denial (no longer a scope case). §3.3 L128 `"Rate Limit Exceeded"` = §2.4 L75. Consistent with the pinned vector `test-vectors/errors/error-taxonomy.json` (AUTHZ_DENIED/401/"Authorization Denied"). |
| **A-M2** | `type` OPTIONAL; `code` extension member; `status`/`title` mandated | **HELD** | §1 Fields L28–L33: `type` OPTIONAL (default `about:blank`, RFC 9457 §3.1); `code` labelled "Web4 **extension member** (RFC 9457 §3.2)"; `status`/`title` "REQUIRED in Web4". Matches SDK `errors.py` `.get("type", "about:blank")` (L418). |
| **A-M3** | `status` transport-agnostic note | **HELD (in §1)** — but see **C66-IC2**: the note points at §5 as the semantic-class registry, yet §5 was left titled "HTTP Status Code Mapping". Remediation-incompleteness facet. |
| **A-L1** | `instance` paths illustrative | **HELD** | §1 L35: "path segments … are **illustrative**; Web4 defines no normative `instance` path registry". |
| **B-M1 §1 rescope** | "core protocol" taxonomy; subsystems extend | **HELD (but inaccurate)** — see **C66-X1**: the rescope sentence claims mcp §7.6 extends "with `W4_ERR_*` codes", which is false (mcp §7.6 uses lowercase `web4_*`). Remediation-introduced inaccuracy. |
| **I1** | Version/Status/Last-Updated banner | **HELD** | §1 L3–L5, date matches git provenance. |

**No C30 finding regressed in the target.** Two fixes (A-M3, B-M1) are *present but incomplete/over-claimed* — caught only by the C56 token-by-token completeness method, and reported as new findings C66-IC2 and C66-X1 (the C64 pattern: a remediation that edits the right place can still leave a stale mirror or assert more than is true).

### A.2 — Regression sweep (remediation-introduced defects)

PR #269 touched **only `errors.md`** (single-file diff, confirmed via `git show aaa2bd86`). No sister-file or SDK edits rode along, so the cross-file regression surface is nil. The two intra-file imperfections above (IC2, X1) are the remediation-introduced residue.

### A.3 — Bidirectional carry re-verification (C30 design-Q / cross-track → current corpus)

| C30 carry | Status now | Note |
|---|---|---|
| **B-H1** numeric `registries/error-codes.md` orphan (DESIGN-Q) | **HELD / hardened** | `error-codes.md` byte-identical since 2025-12-05; "Section X.Y" placeholder (L10) still unfilled; still 11 codes / 0 adopters. Operator decision still pending. |
| **B-M1** centralized-vs-distributed ownership (DESIGN-Q) | **HELD + widened** | Still unresolved; C66-X2/X3 add two *more* distributed-extension drift sites (initial-registries mirror; ACP parallel names) beyond the catalogued metering drift. |
| **B-M3** W4IDp `w4idp-ABCD` form (DESIGN-Q, inherited C29) | **HELD** | All 3 `instance` URIs still use the hyphen form; bundles into the corpus-wide identifier decision. |
| **B-M2** `web4://` SSOT placement (CROSS-TRACK) | **HELD** | Scheme still defined in `core-protocol.md` §6 + grammar §4.1, still absent from the `data-formats.md` SSOT. No change. |
| **B-M1 metering** parallel-naming (CROSS-TRACK) | **HELD** | `protocols/web4-metering.md` still the home; reconcile pending. |
| **I2** `QUICK_REFERENCE.md` custom `type` URI (CROSS-TRACK/INFO) | **HELD** | L193 still uses `"type": "https://web4.io/errors/invalid-lct"` vs the `about:blank` convention. |
| **I3** content-type over negotiated transports (INFO) | **HELD** | §4 unchanged; no resolution attempted (correct — INFO). |

**No C30 carry resolved downstream this cycle** (unlike C64-A.2 where C25-H1 had resolved). All remain open; two (B-M1) widened.

---

## §B — Fresh Finder Pass (9 distinct, 0 HIGH)

### B-1 / `L1` (MEDIUM, DESIGN-Q) — **FLAGSHIP**: `AUTHZ_DENIED`@401 contradicts RFC HTTP semantics *and* its sibling `AUTHZ_SCOPE`@403

§2.4 maps **`W4_ERR_AUTHZ_DENIED` → 401** ("Credential lacks required capability", L72) but **`W4_ERR_AUTHZ_SCOPE` → 403** ("Operation requires additional scopes", L74). Both describe the *same* semantic class — an **authenticated** entity that lacks a permission. Per RFC 9110 §15.5.1 / RFC 7235, **401 Unauthorized is for authentication failure** (missing/invalid credentials; mandates a `WWW-Authenticate` challenge); an authenticated-but-unpermitted request is **403 Forbidden** (RFC 9110 §15.5.4). So `AUTHZ_DENIED`@401 is RFC-semantically wrong **and** inconsistent with `AUTHZ_SCOPE`@403 inside the same table.

- **Routing**: **DESIGN-Q + coordinated CROSS-TRACK** — *not* in-file autonomous. The `401` value is mirrored in the pinned vector `test-vectors/errors/error-taxonomy.json` (`authz_denied_with_detail`), SDK `errors.py` `_ERROR_REGISTRY` (AUTHZ_DENIED status=401, L218) + `test_errors.py`, `registries/initial-registries.md`, and `web4-handshake.md` §10 (L219). Changing §2.4 alone diverges from the pinned vector. Operator must decide 401→403; if approved, it lands as one coordinated set across all five mirrors.
- *Honest scope*: `AUTHZ_EXPIRED`@401 (L73) is defensible (expiry → re-auth), so the defect is confined to `AUTHZ_DENIED`, not the whole §2.4 table.

### B-2 / `C66-X2` (MEDIUM, CROSS-TRACK) — `errors.md` "single source of truth" claim is silently contradicted by a second, divergent core-taxonomy mirror

§1 L9 now declares `errors.md` "the **single source of truth** for core protocol error codes" and lists exactly four subsystem extenders. But `registries/initial-registries.md` (dated 2025-09-11, never re-synced) contains a **second full enumeration of the entire core taxonomy** — all six categories mirrored — and it **diverges**: it adds `W4_ERR_WITNESS_REQUIRED` (L32) and `W4_ERR_PROTO_FORMAT` (L51) that §2 does **not** define, plus a "Metering Errors" block (L53). `errors.md` never references `initial-registries.md` (grep: 0 refs). The SSOT claim is undermined by an unacknowledged, out-of-sync parallel mirror that also introduces §2-absent codes. **Distinct from B-H1** (that is the *numeric* `error-codes.md`; this is a *textual* mirror in `initial-registries.md`).
- **Routing**: CROSS-TRACK. Either make `initial-registries.md`'s Error-Codes section a pointer to `errors.md` §2 (delete the duplicated body), or regenerate it from §2 and resolve the two §2-absent codes (promote into §2 if intended, drop otherwise). Optionally `errors.md` §1 adds a forward note acknowledging the registry mirror (that half would be AUTONOMOUS).

### B-3 / `C66-X1` (MEDIUM, AUTONOMOUS) — §1 rescope falsely asserts mcp §7.6 uses the `W4_ERR_*` convention

The PR #269 rescope sentence (§1 L9) claims **all four** extenders — SAL §9, ACP §10, metering §6, **mcp §7.6** — "extend this taxonomy with additional domain-specific **`W4_ERR_*`** codes." This is **false for mcp §7.6**: `grep -c W4_ERR core-spec/mcp-protocol.md` = 0. The §7.6 failure table (L500–505) uses **lowercase HTTP-prefixed** identifiers (`403 web4_cross_society_unrecognized_lct`, `412 web4_cross_society_witness_required`, …). The `W4_ERR_CROSS_SOCIETY_*` uppercase form exists **only in the SDK** (`errors.py` L102–107), which minted names mcp never defined. The one extender the rescope added to justify the SDK's CROSS_SOCIETY category does not use the convention §1 claims.
- **Routing**: AUTONOMOUS (in-file §1 correction). Soften the claim, e.g. "…SAL §9, ACP §10 and metering §6 using the `W4_ERR_*` convention; mcp §7.6 currently uses lowercase `web4_*` identifiers — see cross-track note." Pair with the C66-SDK-1 cross-track note that the SDK's `W4_ERR_CROSS_SOCIETY_*` names are not yet grounded in any spec text.

### B-4 / `C66-SDK-1` (MEDIUM, CROSS-TRACK) — SDK docstring provenance over-claim (30/7 "canonical per errors.md" vs 24/6)

`errors.py` L4/L7 asserts "**Canonical implementation per** web4-standard/core-spec/errors.md" and "Defines **30 error codes across 7 categories**." `errors.md` §2 deliberately enumerates **24 codes / 6 categories**; §1 frames cross-society as an *extension* owned by `mcp-protocol.md` §7.6. So the file the SDK calls "canonical per" does **not** contain 6 of the 30 codes the SDK attributes to it. Token-by-token, the **24 core codes match `errors.md` §2 exactly** (titles/statuses/descriptions) — drift is confined to the cross-society block's provenance. (Folds in duplicate finding C66-I1.)
- **Routing**: CROSS-TRACK (SDK docstring). Split the provenance: "24 core codes per `core-spec/errors.md` §2; 6 cross-society codes per `core-spec/mcp-protocol.md` §7.6." Canonicity for the 6 cross-society codes lives in mcp §7.6, consistent with §1's extension framing.

### B-5 / `C66-SDK-2` (MEDIUM, CROSS-TRACK) — SDK cross-society block status & surface-form drift vs its cited source mcp §7.6

Three of six cross-society codes carry a **different status** in the SDK than in the mcp §7.6 source table (hand-verified):

| Code | mcp §7.6 | SDK `errors.py` |
|---|---|---|
| `unrecognized_lct` | **403** (L500) | **404** (L305) |
| `exchange_invalid` | **409** (L501) | **400** (L313) |
| `witness_required` | **412** (L503) | **403** (L326) |

(law_conflict 409=409, r7_reputation 400=400, propagation 400=400 — match.) Additionally mcp §7.6 uses lowercase `web4_*` identifiers while the SDK mints `W4_ERR_CROSS_SOCIETY_*` UPPER_SNAKE; and SDK `R7_REPUTATION_INVALID` / `PROPAGATION_SCOPE_UNSUPPORTED` drop the `CROSS_SOCIETY_` infix the other four carry. (Folds in duplicate finding C66-X4.)
- **Routing**: CROSS-TRACK (SDK ↔ mcp §7.6). Align statuses per code (single-owner decision); mcp §7.6 owns cross-society canonicity. `errors.md` itself does not enumerate these, so no errors.md edit.

### B-6 / `C66-IC2` (LOW, AUTONOMOUS) — §5 still titled "HTTP Status Code Mapping" after the A-M3 transport-agnostic rescope

A-M3 made §1 L32 say `status` is "transport-agnostic … carries the analogous semantic class **per §2/§5**", explicitly pointing at §5 as the transport-agnostic semantic registry. But §5 (L141) is titled "**HTTP** Status Code Mapping" and every bullet is an HTTP reason phrase ("400 Bad Request", "503 Service Unavailable"). The section §1 cites as transport-agnostic is itself framed as HTTP-specific — the remediation rescoped §1 but did not propagate into §5. Pure remediation-incompleteness.
- **Routing**: AUTONOMOUS. Retitle e.g. "## 5. Status Code Semantics" with a lead sentence presenting the HTTP reason phrases as the canonical *illustrative label* and noting the semantic class applies over non-HTTP transports per §1.

### B-7 / `C66-IC3` (LOW, AUTONOMOUS) — §5 401/403 prose could be sharpened to mirror §2's split

§5 L144 "401 Unauthorized: Authentication **or authorization** failures" and L145 "403 Forbidden: Operation not allowed for authenticated entity" both match an authenticated-but-unpermitted case, so the prose alone gives no deterministic 401-vs-403 rule (while §2 routes such codes both ways — DENIED@401, SCOPE@403). The §5 wording is *defensible as a description* of §2's deliberate split (the stronger "internal contradiction" framing was **refuted** — see L2 below), but it could be sharpened.
- **Routing**: AUTONOMOUS, **lowest priority** (clarity nicety, borderline with the refuted L2). If touched: reword to mirror §2 (401 = authentication + credential/capability denial; 403 = authenticated entity lacking the additional scope/authorization), **without** reassigning any status (status reassignment is B-1's DESIGN-Q, not this). Remediator's discretion — may legitimately skip as "no defect, §5 accurately describes §2."

### B-8 / `C66-X3` (LOW, CROSS-TRACK) — ACP §10 parallel-naming drift (+ ACP/SAL ledger-write collision)

ACP §10 defines 8 `W4_ERR_ACP_*` codes; three duplicate core/SAL semantics under new names rather than reusing (violating §1's soft-normative "SHOULD reuse … rather than introducing parallel names"): `W4_ERR_ACP_SCOPE_VIOLATION` (L501) ↔ core `W4_ERR_AUTHZ_SCOPE`; `W4_ERR_ACP_WITNESS_DEFICIT` (L509, "Insufficient witnesses for action") ↔ core `W4_ERR_WITNESS_QUORUM` (L66); `W4_ERR_ACP_LEDGER_WRITE` (L517) ↔ SAL §9 bare `W4_ERR_LEDGER_WRITE` (L320). Same class as the catalogued metering drift but in a **different** consumer (ACP) plus an ACP-vs-SAL ledger mismatch. (The other 5 ACP codes add genuinely-new semantics and are *not* drift.)
- **Routing**: CROSS-TRACK (ACP / SAL §9). Either document `W4_ERR_ACP_*` per-domain namespacing as intentional convention, or alias the 2-3 overlaps to core and reconcile the ledger-write surface form. No errors.md change.

### B-9 / `C66-2` (INFO, CROSS-TRACK) — no cross-society test vectors

`errors.py` L14 claims validation against `test-vectors/errors/`, and now ships 30 codes / 7 categories, but `error-taxonomy.json` contains **zero** cross-society vectors (grep `CROSS_SOCIETY|R7_REPUTATION|PROPAGATION` = 0). The `CrossSocietyError` subclass + its 6 codes (incl. the 404/412 status issues in B-5) are entirely unexercised by the pinned harness.
- **Routing**: CROSS-TRACK/INFO. Add cross-society round-trip vectors *after* B-5's status/naming reconciliation settles (don't pin to values that may change).

---

## Classification Summary

| ID | Sev | Finding | Routing |
|----|-----|---------|---------|
| B-1 (L1) | MED | `AUTHZ_DENIED`@401 vs RFC 403 + sibling `AUTHZ_SCOPE`@403 inconsistency | DESIGN-Q (+coordinated cross-track) |
| B-2 (X2) | MED | `initial-registries.md` second core-taxonomy mirror diverges; undermines §1 SSOT claim | CROSS-TRACK |
| B-3 (X1) | MED | §1 rescope falsely says mcp §7.6 uses `W4_ERR_*` (it uses `web4_*`) | **AUTONOMOUS** |
| B-4 (SDK-1) | MED | SDK docstring "canonical per errors.md / 30 codes 7 cats" over-claims (errors.md = 24/6) | CROSS-TRACK |
| B-5 (SDK-2) | MED | SDK cross-society statuses (404/400/403) diverge from mcp §7.6 (403/409/412) + name-form drift | CROSS-TRACK |
| B-6 (IC2) | LOW | §5 still titled "HTTP Status Code Mapping" after A-M3 transport-agnostic rescope | **AUTONOMOUS** |
| B-7 (IC3) | LOW | §5 401/403 prose could mirror §2 split (defensible; lowest priority) | **AUTONOMOUS** |
| B-8 (X3) | LOW | ACP §10 parallel-naming drift + ACP/SAL ledger-write collision | CROSS-TRACK |
| B-9 (C66-2) | INFO | no cross-society test vectors despite SDK 30/7 claim | CROSS-TRACK |

**Totals**: 0 HIGH, 5 MEDIUM, 3 LOW, 1 INFO = **9 distinct** (8 actionable + 1 INFO).

**Split**:
- **AUTONOMOUS (3)** — next remediation (C67) inside `errors.md`: **B-3** (§1 mcp `W4_ERR_*`→`web4_*` correction — highest value), **B-6** (§5 retitle / transport-agnostic harmonization), **B-7** (§5 401/403 wording sharpen — optional, remediator discretion).
- **DESIGN-Q (1)** — operator: **B-1** (`AUTHZ_DENIED` 401→403; recommend 403 on RFC grounds, but pinned-vector/SDK/handshake coordination required).
- **CROSS-TRACK (5)** — fix lands elsewhere: **B-2** (`initial-registries.md`), **B-4** (SDK docstring), **B-5** (SDK↔mcp §7.6 statuses), **B-8** (ACP/SAL), **B-9** (test vectors).

---

## Key Adjudication

1. **The C30 remediation held, but the C56 completeness method paid out twice.** A naive "did the edit land" check would have passed all 6 fixes. Token-by-token, two are imperfect: A-M3 rescoped §1 but left §5 HTTP-titled (B-6), and the B-M1 §1 rescope **over-claimed** that mcp §7.6 uses `W4_ERR_*` when it uses `web4_*` (B-3). This is the C64 pattern again — *a remediation can edit the right place and still assert more than the corpus supports* — and is exactly why delta re-audits re-read remediation **claims** against canonical sources, not just diffs.

2. **The first-pass "SDK aligned" assumption was stale (C64-B2/B9 lesson, confirmed).** The mirror sweep found the SDK has grown a 7th category (6 cross-society codes) that errors.md does not enumerate, with a provenance over-claim (B-4) and three status mis-transcriptions vs its own cited source mcp §7.6 (B-5), none exercised by the test vectors (B-9). The 24 *core* codes still match exactly — the divergence is entirely in the extension block the SDK absorbed.

3. **The "single source of truth" claim has two unacknowledged challengers, not one.** B-H1 catalogued the orphaned *numeric* registry; C66 adds the *textual* `initial-registries.md` mirror (B-2), which is worse than the numeric one — it copies the core taxonomy verbatim **and adds codes §2 doesn't define**. The distributed-error-ownership design question (B-M1) is now load-bearing across four sites: metering, ACP (B-8), the numeric registry, and the textual registry.

---

## Refuted Candidates (anti-padding transparency)

7 candidates were dropped by the adversarial pass:
- **IC1** — "§1 mandate sentence self-contradicts" — no contradiction; §1 L28 reads consistently.
- **L2** (`SECTION5-401-CONFLATES-AUTHN-AUTHZ`) — "§5 401 line is an internal contradiction" — **refuted**: §5 L144 *accurately describes* §2's deliberate split; it is a wording-clarity matter (downgraded and kept as the milder B-7), not a contradiction.
- **L3** (`401-FOR-SIGNATURE-VERIFY`) — `CRYPTO_VERIFY`@401 / `BINDING_PROOF_FAIL`@401 — facts accurate but defensible design (signature failure ≈ failed authentication); not a defect.
- **C66-1** — "§5 omits a status used in §2" — **refuted**: §2 uses exactly {400,401,403,408,409,410,429,503} and §5 lists exactly those 8 (grep-confirmed).
- **C66-A1** — "A-M3 re-introduces transport coupling / completeness gap" — the *§1* clause is fine; the genuine residue is the §5 title (kept as B-6), not the §1 note.
- **C66-A2** — "§2 defines no authentication error codes" — false premise (`CRYPTO_VERIFY`, `BINDING_PROOF_FAIL` cover auth-class failures).
- **C66-B1** — "§5 self-contradiction" — rests on a misquote of §5 L144.

---

## Next-Turn Carry

- **Remediation turn (C67, next by alternation)**: apply the 3 AUTONOMOUS findings inside `errors.md` — **B-3** (§1: correct the mcp §7.6 `W4_ERR_*`→`web4_*` claim — *priority*), **B-6** (§5 retitle to transport-agnostic "Status Code Semantics"), **B-7** (optional §5 401/403 wording sharpen, or skip with rationale). Run a BC#5 corpus sweep for any inserted term. Diff will be small (<+58) → focused self-check, not a full mini-audit.
- **`carry-C66-design-Q`**: **B-1** `AUTHZ_DENIED` 401→403 (recommend 403 on RFC 9110 §15.5.4 grounds; requires coordinated change across `errors.md` §2.4 + test-vector `error-taxonomy.json` + SDK `errors.py`/`test_errors.py` + `registries/initial-registries.md` + `web4-handshake.md` §10). **Folds with** carried B-H1 (numeric registry canonicity) + B-M1 (centralized-vs-distributed error ownership) + B-M3 (W4IDp form) — the error layer's open operator bundle.
- **`carry-C66-cross-track`**: **B-2** reconcile `initial-registries.md` core-taxonomy mirror (delete-and-point or regenerate; resolve §2-absent `WITNESS_REQUIRED`/`PROTO_FORMAT`); **B-4** SDK docstring provenance split; **B-5** SDK↔mcp §7.6 cross-society status reconciliation (3 codes) + name-form; **B-8** ACP §10 / SAL §9 parallel-naming + ledger-write; **B-9** add cross-society test vectors after B-5 settles. Plus carried C30 cross-track: **B-M2** (`web4://` SSOT in data-formats), **B-M1 metering** name reconcile, **I2** (`QUICK_REFERENCE` `about:blank`), **I3** (content-type over negotiated transports).
- **Coverage note**: with C66, `errors.md` lineage is C30→C66 (audit) — C67 remediation pending. The last never-delta'd core-spec file is **`security-framework.md`** (prior C31, 2026-06-04) → next AUDIT target after the C67 errors remediation.
