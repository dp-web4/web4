# C37 — ACP Framework Delta Re-Audit

**Date:** 2026-06-07
**Auditor:** Autonomous session `legion-web4-20260607-120050`
**Document audited:** `web4-standard/core-spec/acp-framework.md` (656 lines)
**Method:** Multi-agent refute-by-default workflow (independent finders × adversarial verify; every cited line re-read against live source before a verdict was admitted)
**Instrument note:** This is a C-series **DELTA re-audit**. It builds on the prior internal-consistency audit of the same file, `docs/audits/acp-framework-internal-consistency-2026-05-28.md` (C18), whose 11 findings were remediated by **PR #244** (commit `1bb9bcaa`, "resolve 6 autonomous-actionable C18 findings"). §A re-verifies each C18 finding's current state; §B reports newly-confirmed findings not in the C18 set.

---

## Authority Hierarchy

Trust-ordering used to adjudicate every claim (highest authority wins on conflict). Mirrors the C18 audit instrument.

| Claim class | Authority (highest → lowest) | Files |
|-------------|------------------------------|-------|
| Wire shape / field presence | Conformance test vectors → JSON-LD schema → SDK serializers (`to_dict`/`to_jsonld`/`from_dict`) → spec example | `web4-standard/test-vectors/schema-validation/acp-jsonld-validation.json`, `web4-standard/test-vectors/acp/plan-operations.json`, `web4-standard/schemas/acp-jsonld.schema.json`, SDK `acp.py`, `acp-framework.md` |
| Error taxonomy | Canonical `errors.md` → SDK error classes (`error_code`) → spec §10.1 catalog | `web4-standard/core-spec/errors.md`, SDK `acp.py` L77-128, `acp-framework.md` §10.1 |
| State machine | SDK `VALID_TRANSITIONS` + `reset()`/`fail()` + tests → test vector `acp-002` → spec §3.1/§3.2 | SDK `acp.py` L134-182/L1114-1128, `plan-operations.json`, `acp-framework.md` §3 |
| Trust dimension keys | Canonical T3/V3 tensor spec → SDK → spec example | `web4-standard/core-spec/t3-v3-tensors.md`, SDK, `acp-framework.md` |
| RDF predicates | Ontology TTLs → spec §8 | `web4-standard/ontology/*.ttl`, `acp-framework.md` §8 |
| Cross-spec envelope casing | Consuming-spec definition → spec example | `mcp-protocol.md`, `acp-framework.md` |

---

## Summary

### §A — C18 finding delta (status counts)

| State | Count |
|-------|-------|
| HELD (fix applied and still correct) | 6 |
| PARTIALLY-OPEN (actionable half remediated; deferred half still open) | 2 |
| STILL-OPEN (deferred at C18, unchanged) | 4 |
| REGRESSED (fix broken or new defect introduced) | 0 |
| **Total C18 findings tracked** | **12** |

Note: C18 shipped 11 findings; this delta tracks 12 rows because the §4.1 corrective coupling (`H1` algorithmic fix + `M5` reading-(a)) is reported under both its `H1` and `M5` identities — `M5` carries the only PARTIALLY-OPEN nuance (deferred Intent-shape extension).

### §B — New confirmed findings by severity

| Severity | Count |
|----------|-------|
| HIGH | 3 |
| MEDIUM | 12 |
| LOW | 15 |
| INFO | 7 |
| **Total confirmed** | **37** |

### Deflation ratio

**41 raw findings → 41 confirmed/retained → 0 refuted.** No finding was refuted (raw observations all held against live source); 20 of the 41 carried a **DEFLATED** verdict (severity/framing lowered under overcall discipline) while the underlying observation was retained, and 21 were **CONFIRMED** at stated severity. Note that §B's 37 entries deduplicate heavy multi-agent overlap on the same underlying defects (notably the `§2.2 stepId`, `§2.4 recordId`/`ledgerInclusion`, `§2.x type/@type`, `proofOfAgency`/`ledgerProof`, and `§3.2 state-table` clusters, each reported independently by 3–5 agents).

---

## §A — C18 Finding Delta Re-Verification

| C18-ID | C18 disposition (PR #244) | Current State | Evidence |
|--------|---------------------------|---------------|----------|
| **H1** | APPLIED | **HELD** | §4.1 `raise InsufficientWitnesses()` is GONE; replaced by a deferral comment (L249-251) noting witnesses live on Decision (§2.3), not Intent (§2.2). Remaining §4.1 raises — `NoValidGrant()` L239, `ScopeViolation()` L243, `ResourceCapExceeded()` L247 — are all canonical. Corpus grep for `InsufficientWitnesses` returns no matches. Full live-spec `raise \w+` sweep = 6 statements (L239/243/247/300/304/308), all mapping to a §10.1+SDK class. The M5 reading-(a) algorithmic correction was applied alongside H1. |
| **H2** | APPLIED | **HELD** | §5.1 now raises only canonical classes: `ScopeViolation` (L300, was `IllegalTrigger`), `ResourceCapExceeded` (L304, was `ExcessiveResourceCap`), `WitnessDeficit` (L308, was `InsufficientWitnessLevel`). Corpus grep for all three former names returns no matches. Each replacement is defined in §10.1 AND SDK `acp.py`. Coupled M1 catalog fix also present (§10.1 now defines all 8 SDK classes incl. `InvalidTransition` + `ResourceCapExceeded`). |
| **H3** | APPLIED | **HELD** | §2.1 `humanApproval.mode` value (`"conditional"`, L84, authored by `1bb9bcaa`) is schema/SDK/vector-valid: schema `HumanApproval.mode` enum = `["auto","manual","conditional"]`; SDK `ApprovalMode(str, Enum).CONDITIONAL = "conditional"` (lowercase wire value); vector `acp-valid-002` MUST-PASS carries `"mode":"conditional"`, while `acp-invalid-015` proves the enum is live (`"always"` MUST-FAIL). Live value matches MUST-PASS form. |
| **M1** | APPLIED | **HELD** | SDK defines exactly 8 ACP error subclasses (`acp.py` L83-125). §10.1 (L488-524) now enumerates all 8 with identical class names + `error_code` strings, incl. the two formerly-missing `InvalidTransition` (L517) and `ResourceCapExceeded` (L521). (Minor non-M1 note: spec base `ACPError` omits the SDK base `error_code="W4_ERR_ACP"` — outside M1's 8-subclass scope; see §B B1-3.) |
| **M4** | APPLIED | **HELD** | §2.4 `t3v3Delta` now uses canonical V3 key `valuation` (L163), not the prior non-canonical `value`; T3 delta uses canonical `temperament`. Anchored to `t3-v3-tensors.md` (canonical V3 dims = valuation/veracity/validity). No non-canonical `value` V3 key remains anywhere in the file. |
| **M5** | PARTIAL | **PARTIALLY-OPEN** | Reading-(a) algorithmic correction APPLIED + HELD: the `intent.witnesses` reference is gone from §4.1 (replaced by deferral comment L249-251); no `intent.witnesses` survives in the file. Reading-(b) Intent-shape extension STILL-OPEN: §2.2 Intent shape (L100-122) still has no `witnesses` field. SDK confirms deferral is correct-by-design — `class Intent` has no witnesses field; witnesses live only on `Decision` (acp.py:776) and `ExecutionRecord` (acp.py:891), exactly as the §4.1 comment asserts. Not REGRESSED; design-Q half intentionally deferred and unclosed. |
| **M2** | DEFERRED | **PARTIALLY-OPEN** | `errors.md` §2 still lists only §2.1-§2.6; `grep -c W4_ERR_ACP errors.md` = 0, so the 8 ACP codes remain absent as taxonomy rows (no §2.7 ACP table). HOWEVER a post-C18 change occurred: commit `aaa2bd86` (2026-06-04, C30 remediation PR #269) rewrote `errors.md` L9 to establish the subsystem-extends-core architecture (subsystem specs "extend this taxonomy with additional domain-specific `W4_ERR_*` codes"). Design model partially resolved (subsystem-extends-core chosen); codes still not added to `errors.md`. |
| **M3** | DEFERRED | **STILL-OPEN** | §2.1 L78-80 still snake_case: `resourceCaps: {max_atp, max_executions, rate_limit}`. SDK `to_jsonld` still emits camelCase `maxAtp`/`maxExecutions`/`rateLimit`; schema still defines camelCase. A doc built from §2.1 still fails the shipped schema's property names. Unchanged since C18 (file untouched except `1bb9bcaa`). |
| **M6** | DEFERRED | **STILL-OPEN** | §8.1/§8.2 still use `acp:` predicates (`hasAgent`, `hasPrincipal`, `underGrant`, `derivedFrom`, `executedBy`, `witnessedBy`, `status`, `atpConsumed`). `grep acp:` in `web4-core-ontology.ttl` and `t3v3-ontology.ttl` = no match; no `acp-ontology.ttl` exists. Zero `acp:` predicate definitions anywhere canonical. Unchanged. |
| **M7** | DEFERRED | **STILL-OPEN** | Both unbridged witness models persist: §2.1 integer `witnessLevel: 2` (reused §5.1 L307) vs §5.2 structured `witness_requirement` object {level, types, quorum:{model:byzantine, threshold}, timeout, fallback}. SDK implements ONLY the integer model (`witness_level: int`, simple-count `validate_witnesses`). No bridge specified. Unchanged. |
| **L1** | DEFERRED | **STILL-OPEN** | §4.2 still `web4_context.proofOfAgency` (camelCase key + nested fields) inside the snake_case `web4_context` envelope; `mcp-protocol.md` still snake_case `web4_context.proof_of_agency` for the same envelope (L137/164-165/465). The two specs still disagree on casing of the same key. Unchanged. |

---

## §B — New Confirmed Findings

Ordered by severity (HIGH → MEDIUM → LOW → INFO). Each finding's verdict reflects the adversarial-verify pass: **CONFIRMED** = retained at stated severity; **DEFLATED** = observation real but severity/framing lowered.

### B2-1 / B4-2 / B5-2 / C37-1 — §2.2 Intent example omits required `stepId`

- **Location:** acp-framework.md §2.2 Intent, lines 100-122
- **Severity:** HIGH (B2-1, B4-2) / MEDIUM (B5-2, C37-1) — see note
- **Verdict:** CONFIRMED
- **Routing:** AUTONOMOUS
- **Claim:** The §2.2 Intent reference example has no `stepId`, but `stepId` is REQUIRED by the schema (`Intent.required` array), is emitted unconditionally by both SDK `Intent.to_dict()` (acp.py:644) and `to_jsonld()` (acp.py:703), is a positional no-default dataclass field (acp.py:625), and appears in every Intent test vector. `from_dict()` reads `d["stepId"]` with no default → hard KeyError.
- **Evidence:** Quad-anchor convergence (schema + both SDK serializers + vectors) against one dissenting spec example. Corpus grep for `stepId|step_id` in acp-framework.md returns zero matches — entirely absent, not merely abbreviated. C18 reproduced this exact §2.2 block (audit L362-374) and noted "No witnesses field" for M5 but never raised the missing `stepId`; genuinely un-flagged. Severity split across agents: the strict-anchor view holds HIGH (load-bearing reference example, hard schema-invalidation + KeyError); the calibration view deflates to MEDIUM because §2.2 is loose illustrative notation (no `@context`, `type:"ACP.Intent"` not `@type`, `ledgerProof`-shaped proofOfAgency) so `stepId` is one of several divergences. **Adjudicated MEDIUM** for the consolidated carry (consistent with C18 scoring the analogous §2.2 M5 shape issue at MEDIUM), with the HIGH dissent recorded.
- **Remediation direction:** Add `"stepId": "approve"` (referencing the §2.1 plan step id) after `planId` in the §2.2 Intent example to match SDK field order. Single-file AUTONOMOUS; schema/SDK/vectors already correct.

### C37-2 — §2.4 ExecutionRecord example omits required `recordId`

- **Location:** acp-framework.md §2.4 ExecutionRecord, lines 145-171
- **Severity:** HIGH
- **Verdict:** CONFIRMED
- **Routing:** AUTONOMOUS
- **Claim:** The §2.4 reference ExecutionRecord has no `recordId`, but `recordId` is REQUIRED by the schema (L202-205), is the first field after `type` in SDK `to_dict()` (acp.py:924), is part of `canonical_hash()` (acp.py:907) so the record is unhashable without it, and `from_dict()` reads `d["recordId"]` with no fallback (acp.py:945). Vector `acp-invalid-011` explicitly asserts a missing `recordId` is invalid (error_kind `required`).
- **Evidence:** All anchors agree; defect contained in this one file's example. Matches the C18-H3 flagship pattern (reference example fails its own conformance vector). HIGH warranted: the omitted field is simultaneously the schema-required identity field, the canonical-hash anchor, and explicitly tested-invalid. (Note: sibling agents B2-3/B4-3 reported the same omission DEFLATED to MEDIUM on the illustrative-prose-form argument; the C37-2 reading holds HIGH because the field is the record's own identity + hash anchor + tested-invalid, distinguishing it from the softer top-level-`timestamp` half. Adjudicated HIGH.)
- **Remediation direction:** Add `"recordId": "exec:web4:001"` as the second key (after `type`) in the §2.4 example, matching SDK `to_dict()` ordering and the `exec:web4:` vector form. Single-line AUTONOMOUS.

### B4-1 — §2.1 AgentPlan event trigger uses `topic`; schema/vector require `expr`

- **Location:** acp-framework.md §2.1 Agent Plan example, line 50
- **Severity:** HIGH
- **Verdict:** CONFIRMED
- **Routing:** AUTONOMOUS
- **Claim:** The §2.1 event trigger is `{"kind":"event","topic":"invoice.ready"}`. The shipped schema's `Trigger` $def permits only `kind`/`expr`/`authorized` with `additionalProperties:false`; the event topic is carried in `expr`, not `topic`. A document built from this example fails schema validation on the unrecognized `topic`. Vector `acp-valid-002` confirms canonical `{"kind":"event","expr":"data.updated"}`.
- **Evidence:** Three independent authorities (schema Trigger $def, SDK `Trigger.expr` "cron expression or event topic" comment + `to_jsonld`, validation vector) unanimously use `expr`; only spec L50 dissents. Same C18-H3 conformance class (example fails its own shipped schema), genuinely not in the C18 set. The block is explicitly JSON-LD-typed (§2.1 L41 `@context`, L42 type), so not loosely illustrative — HIGH held. (Reported also as B2-6 at MEDIUM; B4-1 holds HIGH because the §2.1 block carries `@context` making it a typed JSON-LD doc. Adjudicated HIGH for the schema-rejecting case; B2-6's single-line-rename remediation is identical.)
- **Remediation direction:** Change L50 `"topic":"invoice.ready"` → `"expr":"invoice.ready"`, matching the adjacent cron trigger (L49), SDK, schema, and vector. Single-key AUTONOMOUS fix.

### B1-1 — §10.2 `ScopeViolation` recovery (`request_grant_expansion`) is wrong for the §5.1 law-trigger `ScopeViolation` the C18 H2 remediation introduced

- **Location:** acp-framework.md §5.1 L300 (raise site) + §10.2 L540-542 (recovery branch)
- **Severity:** MEDIUM
- **Verdict:** CONFIRMED
- **Routing:** AUTONOMOUS
- **Claim:** C18-H2 re-mapped §5.1's law-trigger violation to `raise ScopeViolation("trigger ... not allowed by law")` (L300). §10.2's single `ScopeViolation` recovery branch responds with `request_grant_expansion(context)` (L542). A society-LAW trigger violation cannot be cured by expanding an AGENCY grant — laws bound the grant, not vice-versa. The recovery handler now misroutes every law-trigger violation to a grant-expansion request that cannot resolve it.
- **Evidence:** All three live sites match verbatim. §4.1 L242-243 raises bare `ScopeViolation()` for a GRANT-scope violation; §5.1 L300 raises `ScopeViolation(...)` for a LAW-scope violation; §10.2 has a single undiscriminated `ScopeViolation` branch. SDK `acp.py:89-92` defines `ScopeViolation` as grant-scoped with no law-violation subclass — the dispatcher genuinely cannot distinguish the two raise sites. Remediation-introduced regression verified: pre-H2 the undefined `IllegalTrigger` would fall through to the safe `else: log_error/abort_plan`; post-H2 it matches the `ScopeViolation` branch and routes to an incorrect active remedy. H2 converted safe-abort into wrong-remedy. In-file, not a cross-spec overcall (SDK corroborates, does not refute).
- **Remediation direction:** Split the §10.2 `ScopeViolation` branch so a law-scope violation routes to escalate/abort (distinguished via message/context), reserving `request_grant_expansion` for the §4.1 grant-scope case. AUTONOMOUS. A cleaner reintroduction of a distinct `LawViolation`/`IllegalTrigger` class is DESIGN-Q + SDK-TRACK coupled — surface as a carry, do not self-apply.

### C37-3 / B2-4 / B4-3 — §2.4 ExecutionRecord example uses `ledgerInclusion`, absent from SDK/schema (forbidden by `additionalProperties:false`)

- **Location:** acp-framework.md §2.4 ExecutionRecord, lines 166-170
- **Severity:** MEDIUM (B2-4, B4-3) / LOW (C37-3) — see note
- **Verdict:** CONFIRMED (B2-4, B4-3) / DEFLATED (C37-3)
- **Routing:** AUTONOMOUS
- **Claim:** The §2.4 example carries `ledgerInclusion: {hash, block, proof}`. SDK ExecutionRecord has no such field — `to_jsonld()` instead emits `canonicalHash` (string, acp.py:980). The schema defines `canonicalHash` (string) and sets `additionalProperties:false`, so `ledgerInclusion` is a rejected extra property. The ledger-proof concept has a different name and shape (object vs string) from canonical wire.
- **Evidence:** `ledgerInclusion` appears in the entire corpus only twice — §2.4 and `ACP_INTEGRATION_SUMMARY.md:101` — never in SDK/schema/context/vectors. Canonical valid example `acp-valid-008` uses `"canonicalHash":"sha256:exec_hash_002"` (string). Severity split: B2-4/B4-3 hold MEDIUM (rejected by `additionalProperties:false`, calibrated against the C18-M4 sibling on the same example); C37-3 deflates to LOW arguing §2.4 is conceptual `type:"ACP.*"` prose the JSON-LD schema does not validate, so the genuine defect is an orphan illustrative field contradicting the canonical `canonicalHash`, not a schema-rejection. **Adjudicated MEDIUM** (consistent with the C18-M4 sibling-field calibration on this exact example).
- **Remediation direction:** Replace the `ledgerInclusion` object with `"canonicalHash":"sha256:..."` (string) to match SDK `to_jsonld()`, schema, and `acp-valid-008`. Single-file AUTONOMOUS. Secondary: reconcile `ACP_INTEGRATION_SUMMARY.md:101` in a corpus follow-up (CROSS-TRACK, low urgency).

### B2-3 — §2.4 ExecutionRecord example omits top-level `timestamp` (and `recordId`)

- **Location:** acp-framework.md §2.4 ExecutionRecord, lines 145-171
- **Severity:** MEDIUM
- **Verdict:** DEFLATED
- **Routing:** AUTONOMOUS
- **Claim:** The §2.4 example has neither a `recordId` key nor a top-level `timestamp` (only `mcpCall.timestamp`). SDK `to_dict()`/`to_jsonld()` both emit top-level `recordId` and `timestamp`; the schema marks both required; `from_dict()` reads `d["recordId"]` with no default.
- **Evidence:** SDK+schema+vectors triad agrees; spec example is the outlier. Deflated HIGH→MEDIUM: §2.4 is a conceptual plain-JSON illustration (`"type":"ACP.ExecutionRecord"` not `"@type"`, includes non-schema `ledgerInclusion`), so a reader would not paste it straight into a validator. Held at MEDIUM (not LOW): `recordId` is the record's own identity field for an artifact the spec calls "immutable," and §2.4 is the only entity example missing both its own id and (unlike §2.3 Decision) the top-level `timestamp`; `from_dict` hard-fails. The `recordId` half is consolidated under C37-2 (HIGH); the distinct contribution here is the missing top-level `timestamp`.
- **Remediation direction:** Add a top-level `"timestamp"` (mirroring §2.3 Decision L137) to the §2.4 example. AUTONOMOUS, same edit cluster as C37-2.

### B2-2 — §2.2 Intent `proofOfAgency` carries `ledgerProof` (absent from SDK/schema) and omits required `nonce`

- **Location:** acp-framework.md §2.2 Intent, lines 109-112
- **Severity:** MEDIUM
- **Verdict:** DEFLATED
- **Routing:** DESIGN-Q
- **Claim:** §2.2's `proofOfAgency` is `{grantId, ledgerProof:{hash,block}}`. SDK emits `{grantId, planId, intentId, nonce}` with no `ledgerProof`; the schema's `ProofOfAgency` $def requires `nonce` (+planId+intentId) and sets `additionalProperties:false` (so `ledgerProof` is rejected and missing `nonce` fails required). Vector `acp-invalid-008` asserts a proofOfAgency without `nonce` is invalid.
- **Evidence:** All four anchors hold. Deflated HIGH→MEDIUM and routed DESIGN-Q because the finding bundles two issues at different routing levels: the missing-`nonce`/`planId`/`intentId` half is a clean autonomous example fix, but `ledgerProof` appears in BOTH §2.2 and §4.2 (L269-281, with a different internal shape `{grantBlock, grantHash, inclusionProof}`) yet is absent from SDK and schema — a spec-wide modeling disagreement, not a localized typo. §2.2 cannot be made fully schema-valid without deciding the `ledgerProof` admit-vs-drop question that also governs §4.2 and the schema. Consolidated with C37-4 and B5-4.
- **Remediation direction:** AUTONOMOUS now — bring §2.2 `proofOfAgency` to `{grantId, planId, intentId, nonce}`. DESIGN-Q (operator, couples §4.2 + schema + SDK): decide whether `ledgerProof` is a legitimate field — if yes, add to schema $def + SDK dataclass; if no, strip from both §2.2 and §4.2. Couples with C18-L1.

### C37-4 — §2.2 `proofOfAgency` shape contradicts SDK/schema AND the §4.2 `proofOfAgency` shape

- **Location:** acp-framework.md §2.2 (lines 109-112) vs §4.2 (lines 269-281)
- **Severity:** MEDIUM
- **Verdict:** CONFIRMED
- **Routing:** AUTONOMOUS (the §2.2 alignment) + DESIGN-Q (the §4.2 `ledgerProof` question)
- **Claim:** §2.2's `proofOfAgency` omits the SDK/schema-required `planId`/`intentId`/`nonce` and adds a `ledgerProof` sub-object forbidden by the schema; it is also internally inconsistent with §4.2's `proofOfAgency` `{grantId, planId, intentId, ledgerProof, nonce, audience, expiresAt}` in the SAME file. The two examples disagree on which fields exist.
- **Evidence:** Both examples re-read verbatim; the field sets differ. SDK `ProofOfAgency` dataclass (acp.py:599-604) = grant_id/plan_id/intent_id/nonce/audience/expires_at, no ledgerProof; `Intent.to_dict()` emits `{grantId, planId, intentId, nonce}`. §2.2 fails the schema on three counts (missing nonce/planId/intentId, forbidden ledgerProof). Primary defect wholly internal to acp-framework.md — not a cross-doc overcall. MEDIUM held (example-only, not normative MUST; but a validator rejects it and the two examples genuinely disagree).
- **Remediation direction:** Remediate §2.2 `proofOfAgency` to `{grantId, planId, intentId, nonce}` (matches SDK `Intent.to_dict()`), resolving both the conformance failure and the §2.2↔§4.2 disagreement. Confine the autonomous edit to §2.2. Surface the §4.2 `ledgerProof` admit/define question as a DESIGN-Q (do not silently drop §4.2's `ledgerProof`).

### C37-5 — Three mutually-inconsistent ledger-proof sub-shapes within one spec

- **Location:** acp-framework.md §2.2 L111, §2.4 L166-170, §4.2 L273-277
- **Severity:** MEDIUM
- **Verdict:** CONFIRMED
- **Routing:** CROSS-TRACK
- **Claim:** The spec presents three different field-sets for conceptually the same ledger-inclusion proof, none matching: §2.2 `ledgerProof:{hash, block}`; §4.2 `ledgerProof:{grantBlock, grantHash, inclusionProof}`; §2.4 `ledgerInclusion:{hash, block, proof}`. The field name itself alternates between `ledgerProof` and `ledgerInclusion`.
- **Evidence:** All three blocks re-read verbatim; field-sets pairwise distinct, key name alternates. INTRA-spec contradiction (all in one file) — strongest finding class, not the cross-doc overcall class. SDK models ledger inclusion as a single `canonicalHash` string (no structured object); vectors contain no ledger-proof shape, so no external anchor resolves which spec form is canonical. C18 cited only the §4.2 form (for casing) and never compared the three — NEW. MEDIUM held: the field-NAME alternation breaks key-based consumption (harder than mere field-set looseness), pushing above INFO; but only examples diverge (no normative schema contradicted), so not HIGH.
- **Remediation direction:** Reconcile to ONE canonical ledger-proof shape AND one key name across §2.2/§2.4/§4.2. CROSS-TRACK because the SDK deliberately uses a flat `canonicalHash` string and §1 (L19) marks ledger writes out of scope — the canonical choice needs an owner decision coupled to the SDK model. Couples with C37-3, C37-4, B2-2, B5-4.

### B2-6 — §2.1 event trigger uses `topic` key; SDK and schema use `expr`

- **Location:** acp-framework.md §2.1 Agent Plan, line 50
- **Severity:** MEDIUM
- **Verdict:** CONFIRMED
- **Routing:** AUTONOMOUS
- **Claim:** Duplicate of B4-1 from a second finder (held MEDIUM rather than HIGH). The §2.1 event trigger `{"kind":"event","topic":"invoice.ready"}` emits a document the schema's `Trigger` $def (`additionalProperties:false`, properties `kind`/`expr`/`authorized`) rejects, losing the event topic.
- **Evidence:** SDK `to_jsonld` (L478-482), schema Trigger $def, and vector `acp-jsonld-validation.json:39` all use `expr`; adjacent triggers L49 (cron, `expr`) and L51 (manual, `authorized`) already correct. Consolidated with B4-1 (which holds the higher HIGH severity for the schema-rejecting JSON-LD-typed block).
- **Remediation direction:** Same single-key rename as B4-1: L50 `topic` → `expr`.

### B2-7 — §2.1 AgentPlan places `expiresAt` at top level; SDK/schema locate it only inside `guards`

- **Location:** acp-framework.md §2.1 Agent Plan, line 91
- **Severity:** MEDIUM
- **Verdict:** CONFIRMED
- **Routing:** AUTONOMOUS
- **Claim:** The §2.1 example has top-level `"expiresAt"` (L91) and its `guards` object contains no `expiresAt`. SDK `to_dict()`/`to_jsonld()` emit `expiresAt` only INSIDE guards (acp.py:412/507); the schema has no top-level `expiresAt` (and `additionalProperties:false` rejects it), while `expiresAt` is a `Guards` $def property. The example puts expiry where both SDK and schema reject it and omits it from where they expect it.
- **Evidence:** Three independent artifacts (spec example, SDK serializer, JSON schema) mutually agree the top-level placement is wrong. MEDIUM held (schema-rejecting under `additionalProperties:false`, not cosmetic; bounded to one block, so not HIGH).
- **Remediation direction:** Move the L91 `"expiresAt"` into the guards object (after `humanApproval`, before the guards closing brace), matching SDK acp.py:412/507 and schema `Guards` $def. AUTONOMOUS.

### C37-7 / C37-B3-1 / B4-6 — §3.2 state-transition table omits COMPLETE→Idle and FAILED→Idle (SDK/vector count = 13)

- **Location:** acp-framework.md §3.2 State Transitions, lines 218-226
- **Severity:** MEDIUM (C37-B3-1) / LOW (B4-6) / INFO (C37-7) — see note
- **Verdict:** CONFIRMED (C37-B3-1) / CONFIRMED (B4-6) / DEFLATED (C37-7)
- **Routing:** AUTONOMOUS
- **Claim:** The §3.2 table has 7 rows and no row returning COMPLETE or FAILED back to Idle. SDK `VALID_TRANSITIONS` (acp.py:173-182) defines `COMPLETE→IDLE` ("Can restart") and `FAILED→IDLE` ("Can retry"); `reset()` (acp.py:1121-1128) implements both; `test_acp.py` exercises both; vector `acp-002` asserts `totalValidTransitions=13`. A reader implementing strictly from §3.2 builds a terminal-Complete/terminal-Failed machine with no re-execution path, contradicting the SDK restart/retry contract and the §10.2 retry/escalate recovery strategies.
- **Evidence:** SDK edge count = 1+2+2+2+2+2+1+1 = 13, matching `acp-002`. The two re-entry edges appear nowhere in the spec. Severity split: C37-B3-1 holds MEDIUM (restart/retry contract invisible, vector count irreconcilable); B4-6 holds LOW; C37-7 deflates to INFO arguing the §3.2 table never claims to enumerate 13 (no "13"/"totalValidTransitions" anywhere in the file) and the `Any | Error/Timeout | Failed` wildcard already collapses six SDK FAILED edges, so the table is a descriptive summary, not a 1:1 enumeration. **Adjudicated MEDIUM** (the restart/retry semantics are wholly absent from the spec yet normative in SDK + vector — a genuine completeness gap, not merely a counting artifact).
- **Remediation direction:** Add two rows: `Complete | Reset/Retrigger | Idle | Clear intent/decision/record, ready for re-execution` and `Failed | Retry | Idle | Reset state for retry`. To reconcile the vector count of 13, footnote or enumerate that the `Any | Error/Timeout | Failed` wildcard expands to the six per-active-state FAILED edges. Optionally add a return-to-Idle loop to the §3.1 diagram. AUTONOMOUS (spec catches up to canon).

### C37-B3-4 — §3.2 table folds Approval-Gate→Failed (Deny) and Intent-Created→Failed (law-check fail) into the `Any→Failed` wildcard, mislabeling governance outcomes as errors

- **Location:** acp-framework.md §3.2 lines 222-226 vs SDK acp.py:176-177
- **Severity:** LOW
- **Verdict:** DEFLATED
- **Routing:** AUTONOMOUS
- **Claim:** The only Approval-Gate row is `Approval Gate | Approved | Executing` and the only Intent-Created row is `Intent Created | Law check passes | Approval Gate`; the deny/fail counterparts fold into `Any | Error/Timeout | Failed`. In the SDK these are first-class edges (`APPROVAL_GATE→FAILED`, `INTENT_CREATED→FAILED`) triggered by domain events (Deny, law-check failure) that are NOT errors/timeouts — `approve()` routes a Decision deny to FAILED (acp.py:1096-1098). Labeling them under "Error/Timeout" mischaracterizes a normal governance deny as an error.
- **Evidence:** SDK edges confirmed at acp.py:176-177; `approve()` deny→FAILED confirmed. Deflated from "table omits distinct rows" to "wildcard event label too narrow": the §3.1 ASCII diagram (L189-200) ALREADY depicts these edges (`Law/Scope Check → Fail → Reject`, `Approval Gate → Deny → Abort`), and the SDK itself collapses deny into a single FAILED state via `fail(reason)`. The valid residue is editorial — the L226 `Error/Timeout` label is too narrow. LOW held.
- **Remediation direction:** Broaden the §3.2 L226 wildcard event label to also cover governance denials and law-check failures (e.g. `Error / Timeout / Deny / Law-check fail`). Single-file editorial. Bundle with C37-B3-1.

### B5-4 — §2.2 `proofOfAgency.ledgerProof` not permitted by the canonical ProofOfAgency schema

- **Location:** acp-framework.md §2.2, lines 109-112
- **Severity:** MEDIUM
- **Verdict:** CONFIRMED
- **Routing:** DESIGN-Q
- **Claim:** §2.2's `proofOfAgency` contains a `ledgerProof` object. The shipped ProofOfAgency schema defines only `{grantId, planId, intentId, nonce, audience, expiresAt}` with `additionalProperties:false` and requires `planId`/`intentId`/`nonce` — none of which §2.2 provides. The SDK dataclass has no ledger-proof field. The example both adds a forbidden `ledgerProof` and omits three required keys.
- **Evidence:** Schema $def + SDK `Intent.to_jsonld()` re-read verbatim; §2.2 fails on both counts. §4.2 reintroduces `ledgerProof` with a third, different internal shape, confirming the author treats it as a real intended element the schema/SDK reject. C18 examined §2.2 (M5) and §4.2 casing (L1) but never cross-checked §2.2 proofOfAgency against `additionalProperties:false` — NEW. Consolidated with C37-4 and B2-2. DESIGN-Q because the fix couples to "does `ledgerProof` belong in ProofOfAgency?"
- **Remediation direction:** (a) AUTONOMOUS — rewrite §2.2 to `{grantId, planId, intentId, nonce}` and drop/relabel §4.2's `ledgerProof`; or (b) CROSS-TRACK + SDK-TRACK — if ledger inclusion proof IS intended, add the field to schema $def + SDK dataclass + `Intent.to_jsonld()`, reconciling the two divergent `ledgerProof` shapes. Operator picks. The cleanest answer is likely (a): agency proof is grant-binding, not ledger-inclusion (ExecutionRecord already carries the ledger hash).

### B2-8 — §2.1 AgentPlan top-level `signatures` field absent from SDK/schema (rejected)

- **Location:** acp-framework.md §2.1 Agent Plan, line 92
- **Severity:** LOW
- **Verdict:** CONFIRMED
- **Routing:** AUTONOMOUS
- **Claim:** The §2.1 example carries a top-level `"signatures": [...]`. Neither SDK `to_dict()` nor `to_jsonld()` emit any `signatures` key (a case-insensitive grep for `signature` across `acp.py` returns no matches — the ACP SDK has no signature concept), and the schema's AgentPlan has no `signatures` property under `additionalProperties:false`. Vector `acp-invalid-013` confirms an unknown top-level key is schema-rejected.
- **Evidence:** Distinct from C18's demoted ellipsis-as-value hygiene note: C18 demoted on the `[...]` placeholder convention (implicitly assuming `signatures` is a real elided field); B2-8 surfaces that the field itself has no home in the canonical wire/schema — a reader replacing `[...]` with a real array still produces a schema-rejected document. LOW floor right (example-only, but yields a schema-invalid document verifiable via `acp-invalid-013`).
- **Remediation direction:** Remove the `"signatures": [...]` line from the §2.1 example (matches SDK, which has no signature concept). Record-only adjacency: L91 `expiresAt` is the sibling top-level-key divergence (see B2-7) — remediate both as a §2.1 example-shape cleanup. AUTONOMOUS.

### B4-5 / B5-5 / C37-8 — §2.3 Decision example uses `by`; canonical JSON-LD wire uses `decidedBy`

- **Location:** acp-framework.md §2.3 Decision, line 134
- **Severity:** LOW (B4-5 covers `modifications`; see below) / INFO (B5-5, C37-8 cover `by`)
- **Verdict:** DEFLATED (B5-5) / CONFIRMED (C37-8)
- **Routing:** DESIGN-Q (B5-5) / CROSS-TRACK (C37-8)
- **Claim:** §2.3 keys the decider as `"by"`. The shipped schema requires `decidedBy` (and forbids `by` via `additionalProperties:false`); SDK `to_jsonld()` emits `decidedBy`; tests and every Decision vector use `decidedBy`. `by` is the SDK `to_dict()` casing.
- **Evidence:** All anchors verified: `to_dict()` L799 = `by`; `to_jsonld()` L833 = `decidedBy`; schema Decision requires `decidedBy`. But `by` is INTERNALLY CONSISTENT with its sibling examples — §2.2/§2.3/§2.4 all use the `type:"ACP.*"`/no-`@context` to_dict family. So this is not a wire defect in isolation; it is a representational note that the whole §2 example set documents the to_dict shape, which a reader validating against `acp-jsonld.schema.json` will not realize. INFO held; routed CROSS-TRACK/DESIGN-Q because any remediation is a spec-wide convention decision (see B4-4, B5-1, B5-5, C37-8 cluster).
- **Remediation direction:** Do NOT spot-fix `by`→`decidedBy` alone (would diverge §2.3 from its sibling examples). Fold into the operator-facing to_dict-vs-JSON-LD example-convention decision.

### B4-5 — §2.3 Decision example sets `"modifications": null`

- **Location:** acp-framework.md §2.3 Decision, line 132
- **Severity:** LOW
- **Verdict:** CONFIRMED
- **Routing:** AUTONOMOUS
- **Claim:** §2.3 includes `"modifications": null`. SDK `to_dict()` (acp.py:804-805) and `to_jsonld()` (acp.py:838-839) both OMIT the key when falsy/None, so the canonical wire never carries explicit `null`. The schema types `modifications` as `{"type":"object"}`, under which `null` is invalid. The spec's own TS `ApprovalResponse` interface (L355) types it `modifications?: Partial<Intent>` (optional → absence is the canonical "no modifications").
- **Evidence:** SDK-omission + spec's own optional typing independently establish the inconsistency. LOW (single example field, documentation-only). The "schema would reject" leg is slightly aspirational against the dict-form §2.3 example, so the rationale rests on SDK-omission + TS optional typing.
- **Remediation direction:** Remove the `"modifications": null,` line from the §2.3 example (matches SDK omission and the spec's own optional typing), or show a concrete object only in a `decision:"modify"` example. AUTONOMOUS.

### B4-7 — §6.1 `ApprovalRequest.riskAssessment: RiskProfile` (object) conflicts with §2.2 string enum

- **Location:** acp-framework.md §6.1 line 342 vs §2.2 line 117
- **Severity:** LOW
- **Verdict:** CONFIRMED
- **Routing:** AUTONOMOUS
- **Claim:** §6.1's TS `ApprovalRequest` declares `riskAssessment: RiskProfile` (object). Everywhere else `riskAssessment` is a string from `{low,medium,high,critical}`: §2.2 uses `"riskAssessment":"low"`, the schema types it as a string enum, the SDK as `risk_assessment: str`. The same field name denotes two incompatible types within one spec, with no bridge. Compounding: `RiskProfile` is referenced only at L342 and is never defined anywhere in the file.
- **Evidence:** Schema (`enum:[low,medium,high,critical]`), SDK (`risk_assessment: str = "low"`), and §2.2 unanimously corroborate the string typing — local defect in §6.1, not a misread. LOW held: §6.1 is a non-normative illustrative console-UI sketch; the normative wire surfaces are already consistent. Not below LOW: it is a true type contradiction plus a dangling undefined type.
- **Remediation direction:** Type the field as the string enum (`riskAssessment: "low" | "medium" | "high" | "critical"`) to match §2.2/schema/SDK, or rename to `riskProfile: RiskProfile` AND add a `RiskProfile` interface definition. Single-file AUTONOMOUS.

### B2-9 / B5-1 / B5-7 / B4-4 — §2.x examples mix bare `type:"ACP.<Name>"` with JSON-LD; canonical wire uses `@type:"<Name>"`

- **Location:** acp-framework.md §2.1 L41-42, §2.2 L102, §2.3 L130, §2.4 L147
- **Severity:** LOW
- **Verdict:** DEFLATED (B2-9, B5-1, B4-4) / CONFIRMED (B5-7)
- **Routing:** AUTONOMOUS
- **Claim:** All four §2.x examples type their object with the `to_dict()`-flavor key `"type":"ACP.<Name>"`. The schema validates the JSON-LD form requiring `@type` (const `"<Name>"`, no `ACP.` prefix) plus `@context`. §2.1 additionally carries a JSON-LD `@context` header (L41) yet uses bare `type`/`ACP.`-value — matching NEITHER pure `to_dict()` (no `@context`) nor the JSON-LD schema (needs `@type`).
- **Evidence:** `@context` appears EXACTLY ONCE in the 656-line file (§2.1 L41); §2.2/§2.3/§2.4 use bare `type:"ACP.*"` with no `@context` — exactly the established `to_dict()` dict-flavor convention (acp.py:391). So §2.2-2.4 are internally consistent illustrative dict-form, NOT defects; the only true inconsistency is §2.1's hybrid (a lone `@context` grafted onto dict-flavor type). The spec never asserts these examples are schema-conformant JSON-LD. DEFLATED to LOW (doc/example hygiene). B5-7 separately confirms the `ACP.`-prefix value divergence at LOW (parser-tolerable since processors key on `@type`, but the `@context` presence makes §2.x hybrid docs).
- **Remediation direction:** Minimal: delete the stray §2.1 L41 `@context` so all four §2.x examples are uniform dict-flavor. Larger/optional: convert all four to canonical JSON-LD (`@type` unprefixed + `@context` + schema-required `createdAt`) — a bigger DESIGN choice better left as ONE consolidated decision (illustrative-dict-form vs canonical-JSON-LD throughout §2). Do NOT touch §2.2-2.4 type lines piecemeal. Flag the dict-vs-JSON-LD example-form convention for the operator DESIGN-Q bundle. AUTONOMOUS for the minimal fix.

### B5-3 / C37-6 / B2-5 — §2.2 Intent nested `explain.alternatives` has no SDK/schema counterpart

- **Location:** acp-framework.md §2.2 Intent, lines 113-118
- **Severity:** LOW (B5-3, C37-6) / INFO (B2-5)
- **Verdict:** DEFLATED (B5-3, B2-5) / CONFIRMED (C37-6)
- **Routing:** AUTONOMOUS
- **Claim:** §2.2 nests reasoning under `explain: {why, confidence, alternatives, riskAssessment}`. SDK `to_dict()` nests `explain` but only `{why, confidence, riskAssessment}` — no `alternatives`; `to_jsonld()` and schema flatten to top-level `explanation`/`confidence`/`riskAssessment` (`additionalProperties:false`, no `alternatives`). The `alternatives` key is supported by neither serialization nor the schema.
- **Evidence:** `explain.alternatives` appears at exactly one site (L116); the Intent dataclass has no backing field; `alternatives` IS a first-class concept elsewhere in the same spec (§6.1 Human Console `explanation.alternatives: Alternative[]`, L346), so the author plausibly imported the console structure into the wire example. LOW/INFO (cosmetic example-vs-impl drift; no conformance vector exercises `explain`). The deeper latent issue — the `explain:{}` NESTING itself diverges from the flattened canonical JSON-LD wire — is the bigger fish (record-only; to_dict still nests while to_jsonld/schema flatten, a wider SDK shape inconsistency this only touches the edge of).
- **Remediation direction:** Drop the `alternatives` line from the §2.2 `explain` block to match SDK `to_dict()`, or add a one-line note that `alternatives` is illustrative-only. Optionally flatten the `explain` wrapper to top-level `explanation`/`confidence`/`riskAssessment` to match `to_jsonld()`/schema. AUTONOMOUS.

### B1-2 — §10.2 `WitnessDeficit` recovery (`wait_for_witnesses`) wrong for the §5.1 plan-configuration witness deficit (C18-H2 collision)

- **Location:** acp-framework.md §5.1 L307-308 (raise) + §10.2 L536-538 (recovery)
- **Severity:** LOW
- **Verdict:** DEFLATED
- **Routing:** AUTONOMOUS
- **Claim:** §5.1 raises `WitnessDeficit()` when the plan's DECLARED `witnessLevel` is below the law minimum (`if plan.guards.witnessLevel < law.min_witness_level`) — a static plan-MISCONFIGURATION. §10.2's only `WitnessDeficit` recovery is `wait_for_witnesses(context, timeout=300)`, which gathers RUNTIME witnesses. Waiting cannot raise a plan's declared config value above the law minimum, so the recovery is a no-op/infinite-wait. Like B1-1, a C18-H2 remediation-introduced collision: H2 mapped the undefined `InsufficientWitnessLevel()` config check onto the same `WitnessDeficit` class used for runtime count deficits.
- **Evidence:** L307-308 confirmed as the SOLE `raise WitnessDeficit()` site (a static config-vs-config compare). SDK confirms the two-semantics collapse: `Guards.witness_level` is a declared threshold and `validate_witnesses(witness_count)` is a runtime-count compare — distinct from the §5.1 config compare. The correct remedy is amend-plan/abort, not wait. DEFLATED MEDIUM→LOW: illustrative error-recovery pseudocode in §10.2, no parser/interop/conformance impact. Not REFUTED — the inconsistency is real.
- **Remediation direction:** (a) recovery-side — split the §10.2 `WitnessDeficit` branch so a config-level deficit escalates/aborts (amend-plan) rather than `wait_for_witnesses`, reserving the wait path for runtime-count deficits; or (b) raise-side — give §5.1 its own error semantics (the original H2 `InsufficientWitnessLevel` intent). Couples to B1-1 (same C18-H2 collision) — bundle both into one §10.2 remediation edit. AUTONOMOUS.

### C37-B3-2 — §3.2 `Any | Error/Timeout | Failed` wildcard over-specifies the FAILED fan-in (SDK forbids FAILED from Idle and Complete)

- **Location:** acp-framework.md §3.2 line 226 vs SDK acp.py:173-182, 1114-1119
- **Severity:** LOW
- **Verdict:** DEFLATED
- **Routing:** AUTONOMOUS
- **Claim:** The `Any | Error/Timeout | Failed` row states ANY state may transition to Failed. The SDK only permits FAILED from the 5 active states; `IDLE→FAILED` and `COMPLETE→FAILED` are NOT in `VALID_TRANSITIONS`, and `fail()` (acp.py:1117) guards on `if FAILED in VALID_TRANSITIONS.get(self.state, [])`, so a `fail()` from IDLE/COMPLETE is silently a no-op. Literal "Any" claims 2 transitions the SDK rejects (count would be 15 vs canonical 13).
- **Evidence:** All anchors confirmed. Deflated MEDIUM→LOW: "Any → error/timeout → Failed" is near-universal FSM-table SHORTHAND for "any in-flight state" (the row's own "Log error, rollback" action semantically excludes IDLE/COMPLETE), and the SDK's own `fail()` docstring reads "from any active state" — spec and SDK agree in intent, diverge only in one table cell's prose precision. Parser-irrelevant (human-readable table, no wire artifact).
- **Remediation direction:** Replace the bare "Any" in the L226 From-State cell with "Any active state" (or enumerate the 5 in-flight states) with a footnote noting IDLE and COMPLETE are excluded, mirroring SDK `VALID_TRANSITIONS` and the `fail()` docstring. AUTONOMOUS; bundle with other §3.2 touch-ups.

### C37-B3-3 — §3.1 lifecycle diagram introduces `Reject`/`Abort` as terminal nodes not in the ACPState enum

- **Location:** acp-framework.md §3.1 Lifecycle Flow, lines 192-202
- **Severity:** LOW
- **Verdict:** DEFLATED
- **Routing:** AUTONOMOUS
- **Claim:** The §3.1 ASCII flow shows `Reject` (Law/Scope Check → Fail, L192) and `Abort` (Approval Gate → Deny, L200) as outcome nodes. Neither is a member of the SDK ACPState enum (8 states), and neither appears as a §3.2 To-State. In the SDK both resolve to FAILED (`approve()` on a denial → `fail()` → FAILED). The diagram presents two phantom terminal states an implementer could mistake for distinct enum values.
- **Evidence:** Facts accurate, but "Reject"/"Abort" are NOT boxed state nodes — they are loose label text to the right of the boxes, structurally identical to other edge-outcome labels ("Pass/Fail", "Approve/Deny"). No normative text introduces them as states; the §3.2 table unambiguously lists 8. DEFLATED MEDIUM→LOW: a diagram-vs-table clarity/traceability gap, not a phantom-enum wire divergence.
- **Remediation direction:** Relabel the two branches to terminate explicitly at "Failed" (`Fail → Failed`, `Deny → Failed`), or add an explicit §3.2 row `Approval Gate | Denied | Failed | Log denial rationale` (and optionally `Intent Created | Law check fails | Failed`) so every diagram outcome maps to a table state. AUTONOMOUS; folds with C37-B3-1/B3-4.

### B4-6 — §3.2 table under-counts the 13 transitions asserted by `acp-002` (COMPLETE→Idle, FAILED→Idle)

- **Location:** acp-framework.md §3.2 State Transitions table, lines 218-226
- **Severity:** LOW
- **Verdict:** CONFIRMED
- **Claim/Evidence:** Second-finder report of the same restart/retry omission as C37-B3-1/C37-7. Confirmed at LOW: the table is already a deliberately lossy summary (the `Any | Error/Timeout | Failed` meta-row collapses every per-state →Failed edge), and the conformance vector tests the SDK graph (8 states / 13 edges), not the table — so this is documentation completeness, not a wire-conformance break. Consolidated under the §3.2 cluster; adjudicated severity for the cluster is MEDIUM (per C37-B3-1).
- **Remediation direction:** Add `Complete | Restart | Idle` and `Failed | Retry | Idle` rows or a sentence noting terminal states return to Idle. AUTONOMOUS.

### B1-4 — §10.2 dispatches on `ApprovalRequired` and `LedgerWriteFailure` but no spec pseudocode raises either (orphan recovery branches)

- **Location:** acp-framework.md §10.2 L532-534 + L544-546; raise sites L239/243/247/300/304/308
- **Severity:** INFO
- **Verdict:** DEFLATED
- **Routing:** AUTONOMOUS
- **Claim:** The exhaustive set of `raise` statements in the spec's normative pseudocode is `NoValidGrant`, `ScopeViolation`, `ResourceCapExceeded`, `WitnessDeficit`. `ApprovalRequired` and `LedgerWriteFailure` are never raised, yet §10.2 provides recovery branches for both; conversely `NoValidGrant`/`ResourceCapExceeded` (the most-raised) have no dedicated branch and fall to else/abort.
- **Evidence:** Literal facts check out, but the "orphan/mis-aligned" framing is an intra-doc overread. §10.2 dispatches on the §10.1 error-class TAXONOMY (8 subclasses), not on the raise-site inventory. `ApprovalRequired` (§10.1 L501) and `LedgerWriteFailure` (§10.1 L513) are first-class DEFINED classes mapping to documented state-machine states (Approval Gate; Recording), and the SDK raises both at runtime (acp.py:95/113). The §4.1/§5.1 snippets are two narrow illustrative validators, never claimed exhaustive. The `NoValidGrant`/`ResourceCapExceeded` else-fall is correct terminal handling for unrecoverable agency failures. DEFLATED LOW→INFO (documentation-polish nit).
- **Remediation direction:** Optional single-file polish — add a one-line note that §10.2 is illustrative (dispatches over the §10.1 taxonomy, not exhaustive over raise sites), or expand the Approval Gate (§3/§4) and Recording (§5) pseudocode to show where `ApprovalRequired`/`LedgerWriteFailure` are raised. Not blocking; bundle into any future §10 editorial pass.

### B1-3 — SDK base `ACPError` carries `error_code "W4_ERR_ACP"`; §10.1 base class omits it

- **Location:** acp-framework.md §10.1 L489-491 + acp.py L77-80
- **Severity:** INFO
- **Verdict:** DEFLATED
- **Routing:** CROSS-TRACK
- **Claim:** The SDK base `ACPError` declares `error_code = "W4_ERR_ACP"` (acp.py:80); the spec §10.1 base class declares no code (`pass`). An implementer building the taxonomy from §10.1 alone would not emit the base code, diverging from SDK wire output. Inverse of C18-M1 (subclass count); the BASE code is the omission.
- **Evidence:** Both lines verbatim. But the wire-divergence framing is overstated: `W4_ERR_ACP` appears NOWHERE else in the corpus (grep returns only acp.py:80), is never instantiated/raised (the base is abstract; all 8 subclasses override), is untested, and is NOT registered in `errors.md`. So it is never wire-observable — the claim describes output the SDK never produces. The spec base having no code is arguably MORE correct than the SDK carrying an unregistered default. DEFLATED LOW→INFO; the unregistered token lives in the SDK, not as a spec gap.
- **Remediation direction:** Do NOT add `W4_ERR_ACP` to §10.1 (would propagate an unregistered code). Either (a) register a base `W4_ERR_ACP` problem-type in `errors.md` and reflect in spec+SDK, or (b) drop the SDK base default as a non-canonical idiom (SDK-TRACK). CROSS-TRACK (errors.md SSOT moves first). Bundle with C18-M1 + the standing `carry-C30` error-canonicity cluster.

### B5-8 — §5.1 accesses `plan.guards.resourceCaps.max_atp` (camelCase container + snake_case leaf)

- **Location:** acp-framework.md §5.1, line 303
- **Severity:** INFO
- **Verdict:** DEFLATED
- **Routing:** CROSS-TRACK
- **Claim:** The §5.1 pseudocode reads `plan.guards.resourceCaps.max_atp` — a camelCase container + snake_case leaf hybrid matching neither the SDK attribute path (`resource_caps.max_atp`) nor the JSON-LD wire key (`resourceCaps.maxAtp`).
- **Evidence:** Observation correct, but the "no anchor supports it" framing is false: the spec's OWN §2.1 example (L77-78 `resourceCaps`/`max_atp`/`max_executions`/`rate_limit`) uses exactly this hybrid, and §5.1 faithfully dot-accesses the §2.1 keys (`lawHash`, `resourceCaps.max_atp`, `witnessLevel` all mirror §2.1). This is the same hybrid as C18-M3 surfaced at a second site (the pseudocode mirroring the §2.1 example M3 governs), NOT a new defect. Fixing §5.1 alone would CREATE a new §5.1-vs-§2.1 inconsistency. DEFLATED to INFO; CROSS-TRACK.
- **Remediation direction:** Do not remediate §5.1 in isolation. Add §5.1 L303 (`resourceCaps.max_atp`) + L295 (`lawHash`) + L307 (`witnessLevel`) as coverage-extension sites to the existing C18-M3 cross-corpus casing DESIGN-Q, so the accessors are renamed in lockstep with §2.1 when the operator selects canonical casing.

### B4-8 — §2.x/§5.2 JSON examples contain `//` inline comments (invalid JSON)

- **Location:** acp-framework.md lines 49-51, 132, 320-327
- **Severity:** INFO
- **Verdict:** DEFLATED
- **Routing:** AUTONOMOUS (but see note — corpus-wide convention)
- **Claim:** Several `json` code blocks carry `//` trailing comments inside otherwise-strict JSON (trigger array, the Decision `decision` line, the §5.2 `witness_requirement` object). Standard JSON has no comments; a verbatim copy into a parser/validator errors before any schema check.
- **Evidence:** Literal observation accurate (RFC 8259 admits no comments). But this is an established PERVASIVE corpus convention (46 such occurrences across 7+ core-spec files: atp-adp-cycle.md, dictionary-entities.md, entity-types.md, LCT-token, mcp-protocol.md, t3-v3-tensors.md, plus acp), deliberately annotating illustrative examples — not an acp-local defect. The load-bearing "undermines the copy-paste-then-validate workflow that B4-1..B4-3 depend on" claim is REFUTED by tooling: the shipped validator (`validate_schema_vectors.py`) consumes STANDALONE JSON fixtures, not markdown `json` blocks. B4-1..B4-3 operate on standalone vectors, unaffected. DEFLATED to a pure convention note; INFO.
- **Remediation direction:** Do NOT cite as blocking the B4-1..B4-3 vector/schema work. Any real remediation is a corpus-wide convention decision (JSONC-style fenced blocks, or a stated "illustrative, non-normative" preamble), not a local acp-only edit (which would diverge it from 9+ sibling specs). Record as a corpus convention note; bundle into broader documentation-style cleanup.

---

## Routing Summary

### §B — AUTONOMOUS (applicable in the C37 remediation turn, single-file in `acp-framework.md`)

The following can be remediated autonomously without operator decision or cross-spec/SDK change (the canonical authorities — schema, SDK serializers, vectors — are already correct; only the spec examples/prose lag):

- **C37-2 (HIGH)** — add `recordId` to the §2.4 ExecutionRecord example.
- **B4-1 / B2-6 (HIGH→MEDIUM)** — rename §2.1 L50 event-trigger key `topic` → `expr`.
- **B2-1 / B5-2 / C37-1 (MEDIUM)** — add `stepId` to the §2.2 Intent example.
- **B1-1 (MEDIUM)** — split the §10.2 `ScopeViolation` recovery branch so law-scope violations escalate/abort rather than `request_grant_expansion`.
- **C37-3 / B2-4 / B4-3 (MEDIUM)** — replace §2.4 `ledgerInclusion` object with `canonicalHash` string.
- **B2-3 (MEDIUM)** — add top-level `timestamp` to the §2.4 example.
- **C37-4 (MEDIUM)** — bring §2.2 `proofOfAgency` to `{grantId, planId, intentId, nonce}` (the autonomous half; §4.2 `ledgerProof` is DESIGN-Q).
- **B2-7 (MEDIUM)** — move §2.1 top-level `expiresAt` into `guards`.
- **C37-7 / C37-B3-1 / B4-6 (MEDIUM)** — add COMPLETE→Idle and FAILED→Idle rows to §3.2 (+ wildcard-expansion footnote reconciling the 13-edge count).
- **C37-B3-4 (LOW)** — broaden the §3.2 L226 wildcard event label to include Deny / Law-check fail.
- **B2-8 (LOW)** — remove top-level `signatures` from the §2.1 example.
- **B4-5 (LOW)** — remove `"modifications": null` from the §2.3 example.
- **B4-7 (LOW)** — fix §6.1 `riskAssessment` to the string enum (or rename + define `RiskProfile`).
- **B2-9 / B5-1 / B5-7 / B4-4 (LOW)** — delete the stray §2.1 L41 `@context` (minimal fix) so §2.x examples are uniform dict-flavor.
- **B5-3 / C37-6 / B2-5 (LOW/INFO)** — drop `explain.alternatives` from the §2.2 example (or mark illustrative).
- **B1-2 (LOW)** — split the §10.2 `WitnessDeficit` recovery branch for the §5.1 config-deficit case (bundle with B1-1).
- **C37-B3-2 (LOW)** — qualify the §3.2 "Any" → "Any active state" with an IDLE/COMPLETE-excluded footnote.
- **C37-B3-3 (LOW)** — relabel §3.1 diagram `Reject`/`Abort` branches to terminate at "Failed".
- **B1-4 (INFO)** — optional §10.2 note that recovery dispatches over the §10.1 taxonomy, not the raise inventory.

**Bundling guidance:** the §2 example fixes (C37-2, B2-1, B2-3, B2-7, B2-8, B2-9/B5-1, B4-1/B2-6, C37-3/B2-4/B4-3, C37-4, B4-5, B5-3/C37-6) form one cohesive "§2 example-shape correction" edit. The §3 fixes (C37-7/B3-1/B4-6, B3-2, B3-3, B3-4) form one "§3 state-machine reconciliation" edit. The §10.2 recovery fixes (B1-1, B1-2) form one "recovery-branch discrimination" edit (both are the same C18-H2 remediation-introduced collision — [[feedback_remediation_introduced_regression]]).

### §B — DESIGN-Q (operator decision required; do NOT self-apply)

- **B2-2 / B5-4 / C37-4-tail — `ledgerProof` in ProofOfAgency:** does it belong? It appears in §2.2 `{hash, block}` and §4.2 `{grantBlock, grantHash, inclusionProof}` (two divergent shapes) but is absent from SDK dataclass and schema (`additionalProperties:false`). Either drop from both examples (likely correct — agency proof is grant-binding, not ledger-inclusion) or add to schema + SDK. Couples with C18-L1.
- **B5-5 / C37-8 / B4-4 — §2 example representation convention:** should the §2 component catalog illustrate the SDK `to_dict()` shape (`type:"ACP.X"`, `by`, `proofOfAgency`, no `@context`) or canonical JSON-LD wire (`@type`, `decidedBy`, `@context`)? A single coupled convention decision spanning §2.1-§2.4; couples with the `@context` minimal-fix above. Candidate for the accumulating operator DESIGN-Q bundle.

### §B — CROSS-TRACK / SDK-TRACK (folds into existing operator queues)

- **C37-5 (MEDIUM, CROSS-TRACK) — three divergent ledger-proof shapes + name alternation (`ledgerProof`/`ledgerInclusion`):** canonical choice coupled to the SDK flat-`canonicalHash` model and §1's "ledger writes out of scope" clause. Couples with C37-3, C37-4, B2-2, B5-4.
- **B1-3 (INFO, CROSS-TRACK) — SDK base `W4_ERR_ACP` unregistered default:** fold into the standing `carry-C30` error-canonicity cluster (`errors.md` SSOT moves first); bundle with C18-M1.
- **B5-8 (INFO, CROSS-TRACK) — §5.1 `resourceCaps.max_atp` casing:** coverage-extension of the still-open C18-M3 snake/camel casing DESIGN-Q; rename §5.1 L295/L303/L307 in lockstep with §2.1 when the operator picks canonical casing.
- **B4-8 (INFO) — `//` comments in `json` blocks:** corpus-wide convention decision, not an acp-local edit.

### C18 deferred cluster status (carry into operator queues)

| C18-ID | Status | Disposition |
|--------|--------|-------------|
| **M2** (W4_ERR_ACP_* absent from errors.md) | PARTIALLY-OPEN | Architecture now chosen (subsystem-extends-core, via PR #269 `aaa2bd86`); ACP code rows still not added to `errors.md`. Fold into `carry-C30`. |
| **M3** (resourceCaps snake/camel) | STILL-OPEN | Now extended by B5-8 (§5.1 site). One casing DESIGN-Q. |
| **M6** (acp: predicates absent from TTLs) | STILL-OPEN | Requires an `acp-ontology.ttl` or predicate definitions; no canonical home exists. Operator/ontology-track. |
| **M7** (integer vs structured witness models) | STILL-OPEN | SDK implements only the integer model; no bridge. DESIGN-Q (couples §2.1 + §5.2 + SDK). |
| **L1** (proofOfAgency cross-spec casing) | STILL-OPEN | mcp-protocol `proof_of_agency` vs acp `proofOfAgency`; couples with the B2-2/B5-4 `ledgerProof` DESIGN-Q. |

---

## Calibration Note

**Overcall discipline applied throughout.** This file is example-heavy, which is exactly the surface where the documented 4-streak cross-doc overcall pattern recurs — agents repeatedly framed "the spec example fails the shipped JSON-LD schema" as a HIGH wire defect when the example was in fact the spec's established `to_dict()` illustrative dialect (`type:"ACP.<Name>"`, no `@context`), which the JSON-LD schema does not govern. Of 41 raw findings, **20 carried a DEFLATED verdict** (severity/framing lowered) while the underlying observation was retained, and **0 were refuted**.

Representative deflations:

- **The "fails its own schema" framing** was repeatedly trimmed: the §2.x examples are conceptual `to_dict()`-form blocks, not schema-validated JSON-LD wire docs, so several MEDIUM/HIGH "schema-rejection" claims were re-grounded on the genuinely authoritative anchor (SDK `to_dict()` non-optional emission, vector required-sets, or internal §2↔§4 inconsistency) rather than on the schema's `additionalProperties:false` directly. The defects survived; only the mechanism/severity moved.
- **§3.2 state-table (C37-7 vs C37-B3-1):** the "13-transition graph it claims to specify" framing was deflated — the table never references 13 and uses a deliberate `Any→Failed` wildcard collapse; adjudicated MEDIUM (a real completeness gap: restart/retry semantics wholly absent from the spec yet normative in SDK + vector), not the INFO floor one agent proposed nor an over-counting alarm.
- **B1-3 (W4_ERR_ACP base code):** the cross-doc "diverges from SDK wire output" claim was DEFLATED to INFO after grep showed the token is never instantiated, never registered in `errors.md`, and never wire-observable — the unregistered idiom lives in the SDK, not as a spec gap (the inverse of what the finding asserted).
- **B5-8 (§5.1 casing):** the "no anchor supports this hybrid" claim was DEFLATED — the spec's own §2.1 example uses exactly that hybrid, making §5.1 internally consistent and merely a second site of the still-open C18-M3 casing decision, not a new defect.
- **B4-8 (`//` comments):** the claim that inline comments "undermine the copy-paste-then-validate workflow B4-1..B4-3 depend on" was REFUTED at the framing level — the shipped validator consumes standalone JSON fixtures, not markdown blocks; deflated to a corpus-wide convention note.

**Genuine cross-spec/intra-spec convergences held at stated severity** where multiple independent authorities agreed against a lone dissenting spec example — notably C37-2 (recordId: schema + SDK first-field + canonical_hash + `acp-invalid-011` vector), B2-1/C37-1 (stepId: schema required + both serializers + positional dataclass + all vectors), B4-1 (topic/expr: schema + SDK + `acp-valid-002`), and the INTRA-spec contradictions C37-4/C37-5 (proofOfAgency and three ledger-proof shapes, all in one file) — the strongest finding class, immune to the cross-doc overcall discipline because every anchor lives in or under the audited file and was re-read line-by-line.

**Remediation-introduced regressions surfaced (C18-H2):** B1-1 and B1-2 are both consequences of the C18-H2 remediation collapsing previously-distinct undefined error classes (`IllegalTrigger`, `InsufficientWitnessLevel`) onto the canonical `ScopeViolation`/`WitnessDeficit` classes, which the §10.2 recovery dispatcher cannot then discriminate — converting a prior safe-abort path into a wrong-active-remedy path. This is a live instance of the [[feedback_remediation_introduced_regression]] pattern: a correct wire-level remediation (removing undefined classes) introduced a semantic recovery-routing defect in adjacent §10.2 code. Both are autonomously fixable in-file via branch discrimination; the cleaner class-reintroduction alternative is DESIGN-Q + SDK-TRACK and was NOT self-resolved.
