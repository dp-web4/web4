# C86 — ACP Framework Second-Delta Re-Audit

**Date:** 2026-06-22
**Auditor:** Autonomous session `legion-web4-20260622-120002`
**Document audited:** `web4-standard/core-spec/acp-framework.md` (679 lines)
**Method:** Multi-agent refute-by-default workflow (8 primitive-clustered finders × adversarial refute-by-default verify; every cited line re-read against live source before a verdict was admitted). §A verified by hand against the live spec + mirrors.
**Lineage:** This is a C-series **second-delta** re-audit. First-pass internal-consistency audit was **C18** (`docs/audits/acp-framework-internal-consistency-2026-05-28.md`, 11 findings, remediated PR #244 `1bb9bcaa`). First delta was **C37** (`docs/audits/C37-acp-framework-audit-2026-06-07.md`, §A 12 rows / §B 37 findings, autonomous subset remediated PR #283 `c43822e9`). This C86 delta re-verifies the C37 state and surfaces drift introduced since #283 by the churned canonical neighbors.

---

## Instrument note — why ACP, why now

ACP's canonical neighbors **all churned after its #283 remediation (2026-06-07)**: errors.md (C66/C67), atp-adp-cycle.md (C78/C79), inter-society-protocol.md (C62/C63), web4-society-authority-law.md (C58/C59), mcp-protocol.md (C76/C77), t3-v3-tensors.md (C82/C83). A second-delta is the instrument that catches one-directional mirror-drift: ACP *references* these primitives (SAL §5, ATP caps §2.1/§5.1, errors §10, proofOfAgency §4.2, RDF §8) but none of them reference ACP back, so the question is whether ACP's *use* of each primitive still matches that primitive's *current* definition. The errors operator bundle explicitly named "ACP §10 parallel names + ACP/SAL ledger-write" as a live drift site.

---

## Authority Hierarchy

Trust-ordering used to adjudicate every claim (highest authority wins on conflict). Mirrors the C18/C37 instrument.

| Claim class | Authority (highest → lowest) | Files |
|-------------|------------------------------|-------|
| Wire shape / field presence | Conformance vectors → JSON-LD schema → SDK serializers (`to_dict`/`to_jsonld`/`from_dict`) → spec example | `test-vectors/acp/plan-operations.json`, `test-vectors/schema-validation/acp-jsonld-validation.json`, `schemas/acp-jsonld.schema.json`, SDK `acp.py`, `acp-framework.md` |
| Error taxonomy | Canonical `errors.md` → SDK error classes → spec §10.1 | `core-spec/errors.md`, SDK `acp.py` L77-128, `acp-framework.md` §10 |
| State machine | SDK `VALID_TRANSITIONS` + tests → vector `acp-002` → spec §3 | SDK `acp.py` L173-181, `plan-operations.json`, `acp-framework.md` §3 |
| ATP / energy | Canonical `atp-adp-cycle.md` → SDK → spec | `core-spec/atp-adp-cycle.md`, `acp-framework.md` §2.1/§2.4/§5.1 |
| Agency proof envelope | Consuming-spec `mcp-protocol.md` `web4_context` → spec | `core-spec/mcp-protocol.md` §4.1, `acp-framework.md` §4.2 |
| Trust dims / RDF | T3/V3 spec + ontology TTLs → spec §2.4/§8 | `core-spec/t3-v3-tensors.md`, `ontology/*.ttl`, `acp-framework.md` |

---

## §A — C18 + C37 Finding Delta Re-Verification

### §A.1 — C37 §B AUTONOMOUS fixes applied by #283 (HELD check)

All 19 autonomous fixes #283 claimed to apply were re-read token-by-token against the live spec. **All 19 are HELD** (edit present and still correct):

| Fix (C37 id) | Live evidence | State |
|---|---|---|
| §2.4 `recordId` added | L146 `"recordId": "exec:web4:001"` | HELD |
| §2.1 trigger `topic`→`expr` | L49 `{"kind": "event", "expr": "invoice.ready"}` | HELD |
| §2.2 `stepId` added | L102 `"stepId": "approve"` | HELD |
| §2.4 `ledgerInclusion`→`canonicalHash` string | L166 `"canonicalHash": "sha256:exec_hash_002"` | HELD |
| §2.4 top-level `timestamp` added | L165 | HELD |
| §2.2 `proofOfAgency`→`{grantId,planId,intentId,nonce}` | L107-112 | HELD |
| §2.1 `expiresAt` moved into `guards` | L88 (inside guards) | HELD |
| §2.1 top-level `signatures` removed | absent | HELD |
| §2.1 stray `@context` deleted | absent | HELD |
| §2.2 `explain.alternatives` dropped | L113-117 (only why/confidence/riskAssessment) | HELD |
| §2.3 `modifications:null` removed | absent | HELD |
| §3.2 `Complete→Idle` + `Failed→Idle` rows | L222-223 | HELD |
| §3.2 `Any`→`Any active state` + footnote | L224-226 | HELD **(but footnote carries a NEW counting error — §A.3 / C86-1)** |
| §3.1 `Reject`/`Abort`→`Failed` relabel | L188-198 | HELD |
| §6.1 `riskAssessment`→string enum | L344 | HELD |
| §10.2 `ScopeViolation` law-vs-grant discrimination | L557-565 | HELD |
| §10.2 `WitnessDeficit` config-vs-runtime discrimination | L546-555 | HELD |
| §10.2 taxonomy-dispatch note (B1-4) | L532-538 | HELD |
| §5.1 raise-site annotations | L300, L309 | HELD |

**0 regressions** among the applied fixes. One fix (§3.2 footnote) is substantively HELD but introduced a NEW arithmetic defect — see §A.3.

### §A.2 — C18-deferred carries (current state)

| Carry | C37 state | C86 state | Evidence |
|---|---|---|---|
| **M2** — `W4_ERR_ACP_*` codes absent from `errors.md` | PARTIALLY-OPEN (architecture chosen) | **RESOLVED-DOWNSTREAM** (design tension closed) | `errors.md` L9 (post-C67 `d55c0932`) now *explicitly* names "ACP (`acp-framework.md` §10)" as a subsystem that "extend[s] this taxonomy with additional domain-specific codes … following the `W4_ERR_*` convention defined here." So ACP §10 owning its 8 codes (rather than listing them in `errors.md`) is now **by design**, not a gap. `grep -c W4_ERR_ACP errors.md` = 0 is therefore correct. **BUT** errors.md L9 now makes a *claim* about ACP §10 conformance that §10.1 does not fully satisfy — see §B `error-taxonomy` (C86-2). The M2 *design* question is closed; a NEW *conformance* question is opened by the same C67 edit. |
| **M3** — `resourceCaps` snake_case (`max_atp`/`max_executions`/`rate_limit`) | STILL-OPEN | **STILL-OPEN (unchanged)** | §2.1 L77-79 snake_case; schema L56-58 camelCase (`maxAtp`/`maxExecutions`/`rateLimit`); SDK `to_jsonld` L378-379/L402-404 emits camelCase. A doc built from §2.1 fails the shipped schema's property names. Extended by C37-B5-8 (§5.1 L304 same hybrid). |
| **M6** — `acp:` RDF predicates undefined | STILL-OPEN | **STILL-OPEN (unchanged)** | §8 declares `@prefix acp: <https://web4.io/ontology/acp#>` (L420) and uses 9+ `acp:` predicates; `grep acp:` across all 5 `ontology/*.ttl` = 0 matches; no `acp-ontology.ttl` exists. Zero canonical predicate definitions. |
| **M7** — integer `witnessLevel` vs structured `witness_requirement` | STILL-OPEN | **STILL-OPEN (unchanged)** | §2.1 L81 `witnessLevel: 2` (integer) + §5.1 L308 reuse vs §5.2 L320-331 structured `{level,types,quorum:{byzantine,threshold},timeout,fallback}`. SDK implements ONLY the integer model (`witness_level: int` L256; `validate_witnesses(count) >= witness_level` L267-269). No bridge. |
| **L1** — `proofOfAgency` (ACP) vs `proof_of_agency` (mcp) casing | STILL-OPEN (casing only) | **HARDENED / WIDENED** | Now more than casing: mcp `web4_context.proof_of_agency` evolved its shape to `{grant_id, scope}` (mcp §4.1 L485) and added an `agency_chain` ordered-list form (L452, L484-488) with no ACP counterpart, while ACP §4.2 `proofOfAgency` = `{grantId,planId,intentId,ledgerProof,nonce,audience,expiresAt}`. Same `web4_context` envelope, now divergent on casing **and** field-set **and** the new chain concept. See §B `agency-proof` (C86-N). |

### §A.3 — C37 §B DESIGN-Q / CROSS-TRACK carries (current state)

| Carry | C86 state | Evidence |
|---|---|---|
| **C37-5** — three divergent ledger-proof shapes + `ledgerProof`/`ledgerInclusion` name alternation | **PARTIALLY RESOLVED by #283 → COLLAPSED to one site** | §2.2 `ledgerProof` removed; §2.4 `ledgerInclusion`→`canonicalHash` string. Only **§4.2** `ledgerProof {grantBlock,grantHash,inclusionProof}` (L273-276) survives. The "three shapes + name alternation" finding is now a single residual: §4.2 `ledgerProof` object, absent from SDK `ProofOfAgency` dataclass + schema `ProofOfAgency` $def (L86, no `ledgerProof`). |
| **B2-2 / B5-4 / C37-4-tail** — does `ledgerProof` belong in `ProofOfAgency`? | **STILL-OPEN DESIGN-Q (cleaner)** | Now a one-site decision: admit `ledgerProof` to schema+SDK, or strip it from §4.2. (Likely strip — agency proof is grant-binding; the ExecutionRecord already carries the ledger hash via `canonicalHash`.) Couples with L1. |
| **B5-5 / C37-8 / B4-4** — §2 example representation convention (`to_dict` `type:"ACP.X"`/`by` vs JSON-LD `@type`/`decidedBy`) | **STILL-OPEN DESIGN-Q (unchanged)** | §2.1-§2.4 still use `type:"ACP.<Name>"` and §2.3 `by` (L132). Internally consistent dict-flavor; not schema-conformant JSON-LD. One coupled convention decision. |
| **B5-8** — §5.1 `resourceCaps.max_atp` casing | **STILL-OPEN (folds into M3)** | §5.1 L304 `plan.guards.resourceCaps.max_atp` hybrid persists; coverage-extension of M3. |
| **B1-3** — SDK base `ACPError` `error_code="W4_ERR_ACP"` unregistered | **STILL-OPEN CROSS-TRACK (unchanged)** | SDK `acp.py` L80; not in `errors.md`; never wire-observable. Folds into the errors-canonicity cluster. |

---

## §B — New / Hardened Findings (this delta)

**Method:** 8 primitive-clustered finders → 21 raw findings → adversarial refute-by-default verify (refute unless a named authority genuinely contradicts the spec, re-reading every cited line) → **18 survived, 2 refuted, 1 verify-incomplete (API overload — independently hand-verified, see B-AGENCY).** Synthesis dedup folds 2 `is_new:false` items into §A as hardened carries.

### Summary by severity

| Severity | Count | IDs |
|----------|-------|-----|
| MEDIUM | 3 | B-AGENCY (L1 hardened), B-LEDGERPROOF (C37-5 widened), B-M6 (M6 reconfirmed+sharpened) |
| LOW | 8 | B1 plus-literals, B2 footnote-arithmetic, B3 witness-audit-name, B4 sparql-undeclared-preds, B5 sparql-invalid, B6 usecase-guards, B7 atp-discharge-xref, B8 atp-R6-gap |
| INFO | 7 | B9 §2.4 hybrid, B10 §2.1 createdAt, B11 ACP§10 no problem+json, B12 witness-quorum-bridge, B13 min_witness_level-name, B14 critical-undefined, B15 errors.L9-metering / B16 ledger-MUST-layering |
| **Total** | **18** | + 2 refuted (M2-by-design, t3v3-single-root) |

The 2 refuted findings independently corroborate §A: (a) `errors.md` enumerating 0 ACP codes is **BY DESIGN** (confirms M2 resolved-downstream), and (b) §2.4 `t3v3Delta` single-root sparse delta is **consistent** with t3-v3 §2.5 / the 3-root model (no C83 drift).

### Deflation

21 raw → 18 retained / 2 refuted / 1 verify-incomplete. 3 carried a DEFLATED verdict (severity lowered, observation kept): `atp-resource-1` MEDIUM→LOW (no conservation contradiction; ACP does no charging — it's an unbridged *discharge-linkage* gap), `error-taxonomy-…-problem-details` LOW→INFO (the gap is corpus-wide subsystem under-spec, not ACP-specific — SAL §9 has it too), `sal-law-witness-3` LOW→INFO (field-name face of M7).

---

### MEDIUM

#### B-AGENCY — `web4_context` proof-of-agency: divergent casing + disjoint field-set across ACP §4.2 and mcp §4.1, and mcp's `agency_chain` has no ACP counterpart (prior **L1 HARDENED + WIDENED**)

- **Location:** §4.2 L268-281 vs mcp-protocol.md §4.1 L145-148 + §7.4 L452/L484-488
- **Severity:** MEDIUM · **Routing:** CROSS-TRACK · **is_new:** false (L1 hardened)
- **Verify status:** verifier died on API overload; the finding is **hand-confirmed in §A.2 (L1)** and the finder evidence cites both SDK classes verbatim.
- **Claim:** The SAME `web4_context` envelope nests the agency proof under two incompatible definitions. ACP §4.2 = camelCase `proofOfAgency` 7-key `{grantId, planId, intentId, ledgerProof{grantBlock,grantHash,inclusionProof}, nonce, audience, expiresAt}`; mcp §4.1 = snake_case `proof_of_agency` `{grant_id, scope}`. (1) **Casing** — ACP's camelCase member is even internally inconsistent with its own sibling envelope members (`sender_lct`, `trust_context`, `law_hash`, `mrh_depth` are snake_case in both specs). (2) **Field-set** — only `grantId↔grant_id` overlaps; mcp's `scope` is absent from ACP, and ACP's 6 other fields are absent from mcp. (3) **`agency_chain` absence** — mcp §7.4 added a normative ordered-list `agency_chain` (`MUST be non-empty when present`; each element a §4.1 `{grant_id, scope}` object), but ACP — the framework that actually generates multi-hop delegated proofs — has no chain counterpart. SDK confirms the split is live: `mcp.py:225-239 ProofOfAgency={grant_id,scope}` vs `acp.py:599-604 ProofOfAgency={grant_id,plan_id,intent_id,nonce,audience,expires_at}` (camelCase-serialized); neither carries `ledgerProof`.
- **Routing:** CROSS-TRACK — the `web4_context` envelope is mcp-owned; reconciliation couples mcp §4.1/§7.4 + both SDK `ProofOfAgency` classes. Folds into the standing reputation/mcp HELD bundle (envelope↔record mapping). Couples B-LEDGERPROOF.

#### B-LEDGERPROOF — §4.2 `ledgerProof` is now the sole in-doc ledger object but diverges from the R6/R7 shared shape AND the canonical ACP schema (prior **C37-5 collapsed-then-migrated**)

- **Location:** §4.2 L273-277
- **Severity:** MEDIUM · **Routing:** DESIGN-Q · **is_new:** false (C37-5 widened)
- **Claim:** After #283 the C37-5 "three divergent shapes" collapsed to **one in-doc site** (§2.2 ledgerProof removed; §2.4 → `canonicalHash`; §4.2 sole survivor). But the divergence **migrated** to cross-corpus + schema: (a) ACP §4.2 `ledgerProof = {grantBlock, grantHash, inclusionProof}` whereas **r6-framework.md L214-217 and r7-framework.md L222-226 both use the shared `{txHash, blockHeight, inclusionProof}`** — so corpus-wide there are now exactly **two** ledgerProof shapes (R6/R7-shared vs ACP-unique), with `grantBlock`/`blockHeight` and `grantHash`/`txHash` unreconciled. (b) The §4.2 object is absent from schema `$defs.ProofOfAgency` (L86-101, `additionalProperties:false`, admits only `{grantId,planId,intentId,nonce,audience,expiresAt}`) and SDK `ProofOfAgency` (acp.py L592-604) — so a §4.2 `proofOfAgency` carrying `ledgerProof` is schema-REJECTED.
- **Routing:** DESIGN-Q — admit `ledgerProof` (add to schema+SDK, aligned to the R6/R7 `{txHash,blockHeight,inclusionProof}` shape) or strip it from §4.2 (likely: agency proof is grant-binding; the ExecutionRecord already carries `canonicalHash`). Couples B-AGENCY + the C37 ledgerProof DESIGN-Q carry.

#### B-M6 — all 11 `acp:` predicates in §8 absent from every ontology TTL (prior **M6 reconfirmed + sharpened**)

- **Location:** §8.1 L418-436, §8.2 L442-458
- **Severity:** MEDIUM · **Routing:** CROSS-TRACK · **is_new:** false (M6, see §A.2)
- **Sharpening:** count is now **11** (§8.1 declares 8: hasAgent/hasPrincipal/underGrant/derivedFrom/hasDecision/hasExecutionRecord/executedBy/witnessedBy/recordedIn; §8.2 adds 3: executedIntent/status/atpConsumed). `web4-core-ontology.ttl` L14 lists `acp-ontology.ttl` in a *planned-files comment* but no such file exists. Note `acp:witnessedBy` ≠ `web4:witnessedBy` — different namespace AND domain (`web4:witnessedBy` has `rdfs:domain web4:DimensionScore`; ACP applies `acp:witnessedBy` to `lct:record`), so the corpus overlap is illusory.

---

### LOW

#### B1 — §2.4 and §6.2 JSON examples use leading-plus numeric literals (invalid JSON)

- **Location:** §2.4 L161-162 (`t3v3Delta` `"temperament": +0.01`, `"valuation": +0.02`), §6.2 L376-377 (`trustTrend` `"t3": +0.05`, `"v3": +0.03`)
- **Severity:** LOW · **Routing:** AUTONOMOUS · **is_new:** true
- **Claim:** A leading `+` on a number is not permitted by the JSON grammar — these `\`\`\`json` fenced blocks are unparseable (`json.loads('{"x":+0.01}')` → JSONDecodeError). Every canonical authority uses bare numbers (vector `acp-valid-008` L160 `"training":0.01,"temperament":0.005`; zero signed literals anywhere in `test-vectors/`). Unlike the §2.x to_dict dialect note, these are numeric *wire/record* values, schema-relevant.
- **Fix:** strip the leading `+` (4 literals). Spec-local AUTONOMOUS.

#### B2 — §3.2 footnote miscounts the wildcard expansion (states 6+7; correct decomposition is 5+8) — **remediation-introduced by #283**

- **Location:** §3.2 footnote L226
- **Severity:** LOW · **Routing:** AUTONOMOUS · **is_new:** true
- **Claim:** The footnote #283 added says the wildcard "expands to **six** distinct →Failed edges (one per active state)" and "the **seven** explicit rows above yields the 13 transitions." Both addends are wrong: (a) the same footnote correctly enumerates **five** active states, and SDK `VALID_TRANSITIONS` has exactly **5** `→FAILED` edges (PLANNING/INTENT_CREATED/APPROVAL_GATE/EXECUTING/RECORDING) — the spurious +1 comes from re-counting the law-check-fail/deny edges already in the per-state count; (b) the §3.2 table has **eight** explicit non-wildcard rows, not seven. The correct decomposition is **5 + 8 = 13**. The total (13) is right and matches SDK + vector `acp-002`, so this is a self-contained explanatory miscount, not a transition-count error. A live instance of [[feedback_remediation_introduced_regression]] — a correct row-addition introduced an incorrect explanatory footnote.
- **Fix:** "six"→"five", "seven"→"eight" in the footnote. Spec-local AUTONOMOUS.

#### B3 — §5.2 witness type `"audit"` is not a registered witness role (canonical is `"audit-minimal"`)

- **Location:** §5.2 L323 (`"types": ["time", "audit"]`)
- **Severity:** LOW · **Routing:** AUTONOMOUS · **is_new:** true
- **Claim:** The canonical Witness Role Registry defines exactly `time`, `audit-minimal`, `oracle`, and `role` MUST be one of these. `"audit"` is unregistered; intended value is `audit-minimal`. `"time"` is correct. (Same registry that `web4-witnessing.md` §6 / C74-B17 references.)
- **Fix:** `"audit"` → `"audit-minimal"`. Spec-local AUTONOMOUS (registry is the authority).

#### B4 — §8.2 SPARQL uses 3 `acp:` predicates (`executedIntent`, `status`, `atpConsumed`) never declared in §8.1 (intra-doc, distinct from M6)

- **Location:** §8.2 L446-448 vs §8.1 L418-436
- **Severity:** LOW · **Routing:** AUTONOMOUS · **is_new:** true
- **Claim:** Distinct from M6 (spec-vs-TTL): §8.2 queries the record via `acp:executedIntent` (inverse of §8.1's `hasExecutionRecord`) and reads `acp:status`/`acp:atpConsumed` as record literals — none appear in the §8.1 vocabulary. Even if `acp-ontology.ttl` were authored from §8.1, the §8.2 query would still fail. Also: `acp:status`/`acp:atpConsumed` have no edge mapping `result.status` (§2.4 L156) / `result.resourcesConsumed.atp` (L158) into the RDF graph.
- **Fix:** add the 3 predicates to §8.1 (and an edge mapping record→result literals), or rewrite §8.2 to the §8.1 vocabulary. Spec-local AUTONOMOUS.

#### B5 — §8.2 SPARQL is invalid (aggregates inside `BIND`, `IF`-as-counter, unaggregated projection under `GROUP BY`)

- **Location:** §8.2 L450-456
- **Severity:** LOW · **Routing:** AUTONOMOUS · **is_new:** true
- **Claim:** (a) `BIND(COUNT(...))`/`BIND(AVG(...))` place set-aggregates inside `BIND`, which SPARQL 1.1 disallows (aggregates only in SELECT/HAVING). (b) `COUNT(IF(?status="success",1,0))` counts every solution (IF always returns a bound value) so `?successes == ?total`; the intended conditional count needs `SUM(IF(...))` or a filter. (c) `?successRate`/`?avgATP` derive from these illegal BINDs and the non-grouped projection under `GROUP BY ?agent` is itself invalid. The query communicates intent but is not runnable.
- **Fix:** rewrite as a valid aggregate query (SUM-of-IF in SELECT, group by ?agent). Spec-local AUTONOMOUS.

#### B6 — §11 use-case YAML guards use field names absent from the §2.1 / SDK / schema guard model

- **Location:** §11 L596-600 / L621-625 / L643-647
- **Severity:** LOW · **Routing:** AUTONOMOUS · **is_new:** true
- **Claim:** All three use cases specify guard keys that exist nowhere in the canonical guard model: §11.1 `max_daily_amount`/`require_witness`/`human_approval_threshold`; §11.2 `auto_isolation`/`max_false_positives`/`escalation_timeout`; §11.3 `false_positive_rate`/`review_queue_max`/`human_review_sla`. The canonical guards (§2.1 L74-89, schema L78-80, SDK L209-211/L443-447) are strictly `{lawHash, resourceCaps{maxAtp,maxExecutions,rateLimit}, witnessLevel, humanApproval, expiresAt}`. All 9 §11 names are disjoint — a reader copying a use case produces a plan that fails canonical validation. Illustrative YAML, so LOW.
- **Fix:** add an "illustrative, non-normative" note on §11, or map the use-case guards onto canonical keys. Spec-local AUTONOMOUS.

#### B7 — `atpConsumed` (§2.4/§6.2/§8.2) is the same quantity as atp-adp discharge but is never reified as a discharge event

- **Location:** §2.4 L158, §6.2 L374, §8.2 L448
- **Severity:** LOW · **Routing:** AUTONOMOUS · **is_new:** true
- **Claim:** Not a conservation contradiction (ACP never mints/charges, so atp-adp §7.1 #4 "Charging MUST require value proof" is not violated). Purely terminological/structural: ACP's "consumed" maps exactly onto atp-adp §2.3 "discharged" (ATP→ADP, L124-147), but ACP never names the resulting ADP, `returned_to_pool`, or links to `atp-adp-cycle.md`. Example-level values (atp:2, 523), so documentation-only.
- **Fix:** add a §2.4/§5 cross-reference that `atpConsumed` == atp-adp §2.3 discharge (not a separate metering quantity). Spec-local AUTONOMOUS.

#### B8 — ACP execution/ATP model does not route discharge through R6 transactions (atp-adp §7.1 #5 gap) — DEFLATED MEDIUM→LOW

- **Location:** §2.4 (esp. `result.resourcesConsumed.atp` L158) + §9.1 MUST list L462-468
- **Severity:** LOW · **Routing:** CROSS-TRACK · **is_new:** true
- **Claim:** atp-adp §7.1 #5 is normative: "Discharging MUST occur through R6 transactions" (L620). ATP "consumed" during work IS discharge; atp-adp §2.3 frames it as an R6Transaction with an explicit `{from:ATP,to:ADP,amount,returned_to_pool}` block. ACP §2.4 models execution as a bare `mcpCall`+`result` with `resourcesConsumed.atp:2` — no ADP transition, no R6 framing — and §9.1's 5 MUSTs contain no requirement that ATP discharge route through R6. So an ACP-conformant impl can record consumption with zero R6/ADP linkage. Deflated to LOW (no conservation contradiction; unbridged-linkage gap).
- **Routing:** CROSS-TRACK — whether ACP execution records MUST be (or reference) R6 discharge transactions couples atp-adp §7.1 + R6 framework + the ACP execution model. Surface; do not self-apply.

---

### INFO

#### B9 — §2.4 ExecutionRecord example is a to_dict/to_jsonld hybrid (`type:"ACP.ExecutionRecord"` + to_jsonld-only `canonicalHash`)

- §2.4 L145+L166 · INFO · DESIGN-Q · is_new:true. `type:"ACP.X"` is the SDK `to_dict()` discriminator (acp.py:923, no canonicalHash); `canonicalHash` is emitted only by `to_jsonld()` (acp.py:980, which uses `@type` not `type`). The example matches neither serializer exactly. The `type` half is the established §2.x to_dict-dialect carry; the canonicalHash juxtaposition is a #283 remediation artifact. Folds into the B5-5/C37-8 to_dict-vs-JSON-LD convention DESIGN-Q.

#### B10 — §2.1 AgentPlan example omits `createdAt`, which the to_dict serializer always emits

- §2.1 L40-90 · INFO · AUTONOMOUS · is_new:true. SDK `AgentPlan.to_dict()` unconditionally emits `createdAt` (acp.py:414; `__post_init__` L335-337 guarantees it); schema lists it required (L107-110). The §2.2 Intent sibling *does* show `createdAt` (L119), so the §2.1 omission is internally inconsistent. Fix: add a `createdAt` to the §2.1 example. AUTONOMOUS.

#### B11 — ACP §10.1 codes lack `title`+`status`, so cannot form the RFC 9457 problem+json object errors.md §1 mandates — DEFLATED LOW→INFO (the new face of M2)

- §10.1 L488-526 · INFO · DESIGN-Q · is_new:true. errors.md §1 (L13/L28/L31-33) mandates every error be an `application/problem+json` object requiring `title`+`status`; §2 lists each core code with Title+Status columns. ACP §10.1 supplies only class names + `error_code` strings — no title, no status, no problem-type URI. **errors.md L9's post-C67 claim that ACP "add[s] codes following the W4_ERR_* convention" is satisfied only on the *naming* axis, not the *envelope* axis.** Deflated to INFO/corpus-wide because the peer subsystem cited in the same L9 sentence — **SAL §9 (L312-322)** — has the identical gap (Condition|Code|Guidance table, no status/problem+json). So this is a corpus-wide under-specification of how subsystem extension codes map onto the §1 RFC 9457 envelope, not an ACP-isolated defect. **This is the conformance question §A.2 M2 predicted the C67 edit would open.**
- **Routing:** DESIGN-Q (corpus-wide) — define, once, how subsystem `W4_ERR_*` tables (ACP §10, SAL §9, metering §6) carry title/status onto the §1 envelope.

#### B12 — §5.2 `byzantine`/`threshold:0.67` quorum model has no bridge to SAL's count+policy quorum vocabulary

- §5.2 L322-327 · INFO (finder LOW) · CROSS-TRACK · is_new:true. SAL expresses quorum as integer `requires_witnesses` + named `policy` (e.g. `quorum:{witnesses:3, policy:"majority"}`, §14.2; §4.1 `PROC-WIT-3`), never a byzantine fault-fraction. `byzantine`/0.67 appears nowhere else in core-spec. Also internally unreconciled with §5.1's count compare (`witnessLevel < min_witness_level`). CROSS-TRACK (bridge to SAL quorum form). Couples M7.

#### B13 — §5.1 `law.min_witness_level` / `plan.guards.witnessLevel` name a field SAL does not publish (`requires_witnesses`) — DEFLATED LOW→INFO (field-name face of M7)

- §5.1 L308 · INFO · CROSS-TRACK · is_new:true. SAL publishes the witness minimum as `requires_witnesses` (§4.1/§5.4), not `min_witness_level`; semantics (integer count) align but the field name in ACP's law-oracle access path matches nothing SAL publishes. The cross-spec face of M7. CROSS-TRACK.

#### B14 — §9.1 "Critical actions MUST be witnessed" is broader than SAL's enumerated SAL-critical-event witness scope

- §9.1 #3 L466 · INFO · DESIGN-Q · is_new:true. SAL scopes mandatory witness co-signing to an enumerated set (birth, delegation, law updates, auditor adjustments — §8 L300, §3.4 L123, §5.4). ACP never defines which actions are "critical" nor maps onto SAL's set. Not a contradiction (SAL is a floor), but the trigger boundary is undefined vs the explicit canonical authority. (§9.1 #4 Ledger Recording IS consistent with SAL §3.4 — no defect there.) DESIGN-Q (define ACP-critical or reference SAL's set).

#### B15 — errors.md L9 cites metering at `web4-metering.md §6`, which lives in the frozen, D0-gated `protocols/` cluster

- errors.md §1 L9 · INFO · CROSS-TRACK · is_new:true. Of L9's three named extenders, SAL and ACP are core-spec (exist); metering resolves only to `protocols/web4-metering.md` — a member of the C75 D0-gated frozen cluster. errors.md anchors a normative "follows the convention" claim partly on a doc of unsettled canonical status. Contingent on the D0 decision; recorded CROSS-TRACK/INFO. (Out of ACP scope — surfaced for the errors/D0 owners.)

#### B16 — §9.1 "Ledger Recording MUST" vs SDK module-docstring "ledger writes out of scope" is a layering boundary, not a contradiction

- §9.1 #4 L467 / SDK acp.py:19 · INFO · CROSS-TRACK · is_new:true (clarification/non-defect). acp-framework.md contains **no** out-of-scope clause; §9.1 #4 stands unqualified and consistent. The "out of scope" clause exists only in the reference SDK module docstring (a normal implementation-boundary declaration; the SDK still exposes `LedgerWriteFailure` at L113). Recorded so a future finder does not mis-file it as a spec defect.

---

## Routing Summary (for the C87 remediation turn)

### AUTONOMOUS — spec-local, canonical authority already correct (apply in C87)

One cohesive remediation, grouped by section:

- **§2 examples:** B1 (strip 4 leading-plus literals in §2.4/§6.2), B10 (add `createdAt` to §2.1).
- **§3.2:** B2 (footnote "six"→"five", "seven"→"eight").
- **§5.2:** B3 (`"audit"`→`"audit-minimal"`).
- **§8:** B4 (declare the 3 §8.2 predicates in §8.1 or rewrite the query to §8.1 vocab + add record→result edge), B5 (rewrite §8.2 SPARQL as a valid aggregate query).
- **§11:** B6 ("illustrative, non-normative" note or map use-case guards to canonical keys).
- **§2.4/§5:** B7 (cross-reference `atpConsumed` == atp-adp §2.3 discharge).

### DESIGN-Q — operator decision (do NOT self-apply)

- **B-LEDGERPROOF / B9:** §4.2 `ledgerProof` admit-vs-strip, and if admit, align to the R6/R7 `{txHash,blockHeight,inclusionProof}` shape (couples schema+SDK); plus the §2.x to_dict-vs-JSON-LD example-convention decision (B5-5/C37-8 carry). 
- **B11:** corpus-wide — how subsystem `W4_ERR_*` tables (ACP §10, SAL §9, metering §6) map title/status onto the §1 RFC 9457 envelope.
- **B14:** define "ACP-critical actions" or reference SAL's enumerated set.

### CROSS-TRACK — needs another spec/SDK to move first (route into existing queues)

- **B-AGENCY (L1 hardened):** `web4_context` proofOfAgency casing+field-set+`agency_chain` reconciliation — mcp-owned envelope; folds into the standing reputation/mcp HELD bundle (envelope↔record mapping) + both SDK `ProofOfAgency` classes.
- **B8:** ACP execution ↔ R6 discharge linkage (atp-adp §7.1 #5) — couples atp-adp + R6.
- **B12 / B13:** ACP §5 witness vocabulary (`byzantine`/`threshold`; `min_witness_level`) ↔ SAL count+policy quorum (`requires_witnesses`/`policy`) — couples M7 + SAL.
- **B15:** errors.md L9 metering reference rides the C75 D0 cluster decision.
- **B-M6:** `acp:` predicates need an `acp-ontology.ttl` (or definitions in an existing TTL) — ontology-track. Carries M6.

### Carries reconfirmed / hardened (see §A)

M3 (resourceCaps casing) STILL-OPEN; M6 reconfirmed+sharpened (→B-M6); M7 STILL-OPEN (+B12/B13 new cross-spec faces); L1 HARDENED (→B-AGENCY); C37-5 collapsed-then-migrated (→B-LEDGERPROOF); M2 RESOLVED-DOWNSTREAM (but opened conformance question B11). Refuted: M2-codes-by-design, t3v3-single-root (both corroborate §A).

---

## Calibration Note

Overcall discipline held: 21 raw → 18 retained, 2 refuted, 3 deflated. The refutations are load-bearing — both corroborate §A's resolved-downstream / no-drift verdicts rather than adding findings. The strongest NEW class is **intra-document** (B1 unparseable JSON, B2 footnote miscount, B4/B5 SPARQL, B6 use-case guards) — all spec-local AUTONOMOUS, immune to cross-doc overcall because every authority is in-file or in the already-correct schema/SDK/registry. The CROSS-TRACK cluster (B-AGENCY, B8, B12/B13, B-M6) is the genuine yield of the 2nd-delta-against-churned-neighbors instrument: ACP's *use* of mcp's agency envelope, atp-adp's discharge model, and SAL's witness/quorum vocabulary has drifted as those neighbors were remediated (C77/C79/C59) while ACP sat untouched since #283. **B2 is a fresh [[feedback_remediation_introduced_regression]] instance** — #283's own footnote, added to reconcile the transition count, states the decomposition wrong (6+7 for a 5+8 reality). One verifier (B-AGENCY) died on API overload; the finding is retained on independent §A hand-verification + the finder's verbatim dual-SDK evidence.

---

*C86 complete. Next: **C87 remediation turn** applies the AUTONOMOUS list above to `acp-framework.md` (single file); DESIGN-Q + CROSS-TRACK items route to operator/existing queues. ACP lineage C18 → C37 → C86 → (C87).*

