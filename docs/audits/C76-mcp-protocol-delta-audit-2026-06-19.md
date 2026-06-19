# C76 — `mcp-protocol.md` Delta Re-Audit

**Date**: 2026-06-19
**Auditor**: autonomous web4 session (legion, LEAD `120047`, C-series)
**Subject**: `web4-standard/core-spec/mcp-protocol.md` (current: 931 lines, 16 sections)
**Instrument**: multi-agent refute-by-default workflow — 6 finders (2× §A disposition/deferred-cluster, 4× §B internal + cross-spec lenses) → 3 adversarial verifiers (refute-by-default) → synthesis with dedupe. 9 agents total.
**Scope**: Internal-consistency + cross-spec delta re-audit. Two parts:
- **§A** — delta re-verification of the **C35** audit (2026-06-06) and its remediation **PR #279** ("12 autonomous-actionable C35 findings"). Verifies which findings held, whether the remediation regressed anything, and re-checks the three deferred clusters against the **now-moved corpus** (errors.md C66/C67, ISP C62/C63, r7 C46/C47, registries C70/C71, entity-types C64/C65).
- **§B** — NEW findings since 2026-06-06.

This audit **recommends; it does not patch**. No spec text was modified. One new file.

**Predecessor**: `docs/audits/C35-mcp-protocol-audit-2026-06-06.md`.

---

## Headline

PR #279 was a **clean remediation**: all 12 applied C35 findings **HELD** with **0 regressions**. But the delta surfaces three results that matter more than the line-items:

1. **Two C35 carries should be RETIRED — they are no longer defects.**
   - **N4 (error-canonicity) is RESOLVED-DOWNSTREAM.** The errors.md C67 remediation explicitly rescoped `W4_ERR_*` to SAL/ACP/metering and **named mcp §7.6's lowercase `web4_*` codes as a sanctioned exception** (errors.md L9). The SSOT no longer demands mcp conform → stale deferral.
   - **F9 (`Policy-Entity` → `PolicyEntity`) has an INVERTED PREMISE.** The C35 audit (and CLAUDE.md) assert canonical = `PolicyEntity` (one word). But mcp's cited authority, `society-roles.md` §2.3, *is itself titled* `Policy-Entity` (hyphenated) and uses that form throughout. **mcp is consistent with its own SSOT.** Applying F9 to mcp alone would *introduce* cross-doc drift. F9 is not an mcp defect — it is a **corpus-wide** `PolicyEntity` / `Policy-Entity` / `Policy` terminology question (three forms live across CLAUDE.md, society-roles.md, and entity-types.md). Routed cross-track; do NOT self-apply to mcp. (A textbook [[feedback_remediation_introduced_regression]] case: a "mechanical single-file rename" that would have manufactured a mirror divergence.)

2. **NEW HIGH — mcp invents entity types the taxonomy rejects.** §3.1/§3.2 set `entity_type` to `mcp_server` / `mcp_client`, neither of which exists in entity-types.md's **closed** 15-type taxonomy. The reference SDK's `EntityType` enum literally raises on both values (same treatment as a deliberate `"not_real"` negative test). The canonical fit already exists (`service`/`device` for the server; `ai`/`service` for the client). Second site: the standalone `MCP_ENTITY_SPECIFICATION.md:64`.

3. **NEW cluster — mcp's §7.3 `reputation` envelope is a privately-named, T3-only subset of r7-framework §1.7's canonical Reputation**, despite §7.3 L355 citing r7 as "the canonical R7 definition." Field-name (`witness_signatures` vs `witnesses`), sub-key shape (`{delta,context}` vs `{change,from,to}`), V3-delta omission, and dropped `action_id` provenance (a C47 addition) all diverge. The V3 omission is load-bearing: r7 treats V3-in-reputation as definitional, so an mcp reputation envelope structurally cannot represent it.

What **remains correctly deferred**: the §7.7-promotion wire-shape cluster (N5/N9/N13, WIP-fenced), the §10 RFC-9457-vs-JSON-RPC error model (N12, sole survivor of the carry-C30 mcp cluster after N4 retired), and the `lct:web4:` entity-vs-instance identifier scheme (N15, carry-C33).

---

## Severity legend

| Sev | Meaning |
|-----|---------|
| **HIGH** | A conformant implementation cannot satisfy the document as written, OR a normative value/structure is rejected by the canonical taxonomy/SSOT. |
| **MEDIUM** | Normative guidance is self-contradicting/ambiguous enough that two good-faith implementations would diverge. |
| **LOW** | Maintainability / terminology / illustrative-example hazard; not a blocking contradiction. |
| **INFO** | Observation; recorded for completeness or to confirm a seam was inspected and found bounded. |

---

## §A — Delta re-verification of C35 (+ PR #279)

### A.1 — Disposition of the 14 autonomous candidates (12 applied)

| C35 ID | Verdict | Current line(s) | Evidence |
|--------|---------|-----------------|----------|
| N1 | **HELD** | §7.5 L479 | "R7 MUST NOT proceed without witnessing (consistent with §7.3 …)". |
| N2 | **HELD** | §7.4 L413/415 | `web4:role:` infix gone (0 hits); canonical `web4:<Name>` form. |
| N3 | **HELD** | §3.2 L107 | `"valuation": 0.90` — carry-C34 single-token fix present. |
| N6 | **HELD** | §7.7.5 L654/668 | Tagged informative; RFC2119 keywords removed (now "by convention"/"commonly"). |
| N7 | **HELD** | §6.3 L274, §11 L826/848 | Unified on `mcp:session:`; no `sess:` scheme remains. |
| N8 | **HELD** | §7.4 L430/447 | Orphan `exchange_agreement_hash` gone; only nested `exchange_agreement_ref`. |
| N10 | **HELD** | §4.2 L160 | `verify_atp_stake(web4_context.trust_context.atp_stake)` nested correctly. |
| N11 | **HELD** | §9.1 L740 | `min(total_cost, context.atp_remaining)` — defined §11 field (L834). |
| F6 | **HELD** | §7.5 L486 | "`propagation_scope` is a single enum, not a set". |
| F7 | **HELD** | §7.3 L397 | Default now `interaction_type`-aware with `both` fallback. |
| F10 | **HELD** | §7.6 L502 | Law-conflict recovery split by encompassing-society existence. |
| F13 | **HELD** | §7.7.5/7.7.6 L654/672 | Now cross-reference §7.7.1 instead of restating. |
| **N14** | **NOT APPLIED** (optional) | §7.4 L446-451 | The optional inline cross-ref L451←L447 was not added. Explicitly optional in C35; LOW. |
| **F9** | **NOT APPLIED — PREMISE INVERTED** | §7.3 L394/400; §7.6 L504; §7.7.2 L554 | `Policy-Entity` still appears **4×** (C35 undercounted: cited 3). But society-roles.md §2.3 is itself titled `Policy-Entity` → mcp is consistent with SSOT. RETIRE as single-file fix; see §C cross-track. |

**A.1 tally**: 12 HELD · 0 REGRESSED · 2 not applied (N14 optional; F9 premise-inverted). Matches "12 of 14 applied."

**Regression sweep** (edited sites L107 / §4.2 L160 / §6.3 + §11 session-id / §7.3 L397+L400 / §7.4 L413-431 + L452-468 / §7.5 L479/486/487 / §7.6 L502 / §7.7.5 / §9.1 L740): **no defect introduced.** All cross-refs resolve — §9.1 "per §11" → L834 `atp_remaining` ✓; §7.3 society-roles §2.3/§4.1/§2.6 and §7.7.2 §2.4 citations all match current society-roles.md headings ✓; N10/N7 fixes left no stale mirror ✓.

### A.2 — Deferred-cluster re-verification against the moved corpus

| C35 ID | Cluster | Verdict | Evidence |
|--------|---------|---------|----------|
| **N4** | carry-C30 error-canonicity | **RESOLVED-DOWNSTREAM → RETIRE** | errors.md L9 (C67, 2026-06-17) now names mcp §7.6 and sanctions lowercase `web4_*`; `W4_ERR_*` scoped to SAL/ACP/metering. The "errors.md names §7.6 by number / demands `W4_ERR_*`" basis is gone. |
| **N12** | carry-C30 error-canonicity | **STILL OPEN** (sole survivor) | §10 (L774-814) is JSON-RPC numeric `-32001` + Python exception classes, disjoint from errors.md's RFC-9457 `problem+json` model (errors.md §1). errors.md L9 addressed only §7.6 strings, not §10. Decouple from N4. |
| **N5** | §7.7-promotion wire-shape | **STILL OPEN** (WIP-fenced) | §7.4 `atp_settlement` flat `caller_amount`/`responder_amount` (L420-423) vs §7.7.3 `agreed_rate_caller_atp.{amount,per_unit}` (L629-630). Byte-identical to C35. |
| **N9** | §7.7-promotion wire-shape | **STILL OPEN** (WIP-fenced) | §7.4 `referent` bundles `quantity` (L424-429); §7.7.3 carries `reference_standard`, amount externalized (L587-594). |
| **N13** | §7.7-promotion wire-shape | **STILL OPEN** (WIP-fenced) | §7.4 inline `atp_settlement` has no signer binding (L419-431); §7.7.3 acceptance is `accepting_treasurer`-signed (L632-633). |
| **N15** | carry-C33 identifier-scheme | **STILL OPEN** | data-formats.md §1.3 (L35) confirms split: entity → `did:web4:`; `lct:web4:` is the LCT *instance* id. mcp names entities `lct:web4:…` pervasively (L411/827/828/811). data-formats itself defers reconciliation → carry live. |

---

## §B — New findings since 2026-06-06

All adversarially verified (refute-by-default). Severities reflect post-verify deflation.

| # | Sev | Actionability | Where | Finding |
|---|-----|---------------|-------|---------|
| **B1** | **HIGH** | autonomous (value-correctness) | §3.1 L76 / §3.2 L100 | `entity_type` = `mcp_server` / `mcp_client` are **not in entity-types.md's closed 15-type taxonomy** (§2.1 L17-35 enumerates the recognized set; §8.1 makes type immutable; §7.1 requires validation at creation). Reference SDK `EntityType` enum rejects both (raises, identical to a `"not_real"` negative test). §3 carries no "illustrative" disclaimer. Canonical fit exists: `service`/`device` (server), `ai`/`service` (client). **Second site**: `MCP_ENTITY_SPECIFICATION.md:64` (also adds a non-canonical `entity_subtype`). |
| **B2** | **MED** | cross-track (r7 + SDK) | §7.3 L381-385 vs `r7-framework.md` §1.7 L284-291 | mcp's reputation `trust_dimension_updates` carries **only T3** with `{delta, context}` sub-keys; r7's canonical Reputation carries **`t3_delta` AND `v3_delta`** with `{change, from, to}`. r7 §1.7 L259/L312 treat V3-in-reputation as definitional → mcp's envelope **structurally cannot represent a V3 change** despite §7.3 L355 citing r7 as canonical. (V3-omission sub-point is HIGH in isolation; bundled MED.) |
| **B3** | **MED** | autonomous (rename to canonical) | §7.3 L387 vs `r7-framework.md` §1.7 L296 | mcp names the attestation array `witness_signatures`; r7's canonical Reputation names it `witnesses` (`{lct, signature, timestamp}`). Same slot, two cross-referencing canonical docs, two names. |
| **B4** | **MED** | autonomous | §12 L863-868/871 vs body §7.3 L398 / §7.5 L479 | The §12 "Implementation Requirements" conformance summary (no "non-exhaustive" qualifier) **omits the high-consequence witnessing MUST** from its MUST list and reduces witnessing to "Servers SHOULD witness significant interactions" (L871). A reader working from §12 alone misses the body MUST. |
| **B5** | **MED** | cross-track (registries) | §7.6 L500-505 vs `registries/` | The six §7.6 cross-society `web4_*` error codes have **no registry home** in either the named (`W4_ERR_*`, `initial-registries.md` L14-59) or numeric (`error-codes.md` L15-27) registry. Registry-completeness gap for a Normative error sub-domain. (Now that N4 sanctions the `web4_*` *form*, the open question is purely *where they register*.) |
| **B6** | **LOW** | cross-track (r7 + SDK) | §7.3 L377-388 vs `r7-framework.md` §1.7 L281/L433 | mcp's reputation envelope omits r7's `action_id` (the C47 provenance field, present in every r7 §5 example) plus `subject_lct`/`role_lct`/`rule_triggered`/etc. mcp claims canonical binding (L355) but drops the action-provenance link. Subset-gap. |
| **B7** | **LOW** | autonomous | §7.3 L378 | `outcome_class` enum lists `partial`, but `partial` is **never given semantics** anywhere in mcp (`violation` is defined inline at L400; `success`/`failure` are implied). Define or drop. (NB: the cross-spec "outcome_class diverges from r7" reading was **refuted** — `outcome_class` is a reputation classifier, a different layer from r7's Result `status`; r7 has no such field, so this is mcp-internal hygiene only.) |
| **B8** | **LOW** | autonomous | §9.1 L731-741 | §9.1 metering pseudocode uses an undefined runtime `context` whose members don't map 1:1 to a single schema: `context.t3.average()` (L735) has no field named `t3` (§4.1 nests `trust_context.t3_in_role`, only 2 of 3 dims — so `.average()` is ambiguous); `context.atp_remaining` is a §11 session field (L834). It is informal Python (function param), not a wire claim — add a one-line "implementation-assembled aggregate" note + align `t3`→`t3_in_role`. (Merges the two finder candidates M2+M3.) |
| **B9** | **LOW** | autonomous | §7.4 L415 | Orphan field `responding_role_expected`: appears once, referenced by no normative bullet in §7.4 (L439-468). Implementer cannot tell if it is required/advisory or how a role mismatch is handled. (Same *class* as the now-fixed C35 N8, different field.) |
| **B10** | **LOW** | autonomous / note | §4.1 L129 / §6.1 L243 / §7.1 L306 | Three field names for the role identifier across sections: `sender_role` (§4.1), `role_required` (§6.1 tool requirements), `roleType` (§7.1 R6 mapping). May be intentional (different contexts) — harmonize or add a note. (Distinct from C35 N2, which was the value *form*.) |
| **B11** | **LOW** | folds into B1 | §3.1 L76 / §8.2 L719 | The MCP-server type appears in three forms: `mcp_server` (JSON), `web4:MCPServer` (§8.2 SPARQL RDF class), vs the taxonomy's bare lowercase tokens. Remediate with B1. (`web4:MCPServer` as an RDF *class* IRI is mildly defensible vs the `entity_type` *value*.) |
| **B12** | **LOW** | cross-track (registries, WIP) | §7.7.7 L680-686 vs `registries/` | The seven §7.7.7 `web4_rate_*` codes are likewise unregistered. §7.7 is WIP so registration is deferrable to v0.1.0-final, but the identifiers are declared "stable", so the registry-home question rides B5. |

**Inspected and bounded (refuted / consistent — recorded for completeness):**
- **r7 `outcome_class` "divergence"** — REFUTED. r7 §1.7 is a conceptual component model with an *illustrative* JSON example (only the Result `status` enum carries a "(normative)… MUST be one of" declaration, r7 L233); r7 §8 explicitly permits added fields. `outcome_class` is an mcp-layer classifier r7 doesn't define. (The residual real defect is B7, mcp-internal.)
- **ATP minting** — CONSISTENT. mcp §7.3/§7.7.2 "updates both societies' ATP accounts" is *settlement* against pre-existing balances at declared referent valuations (L638), never minting ATP nor charging ADP→ATP, so atp-adp-cycle §7.1 ("Charging MUST require value proof") and §2.1 (societies mint ADP) are not engaged. C63's ISP §4.5 "mint ADP not ATP" edit *strengthens* this posture.
- **ISP §9 reciprocal claim** — CONSISTENT. mcp §7.5 L494 claims to resolve ISP §9's "society-society trust tensors" future-work; ISP §9 (current) struck that item through and marked it "RESOLVED — mcp-protocol.md §7.5". Bidirectionally honored.
- **ISP section citations** (§3.1, §3.2 Option 3, §4) and **society-roles citations** (§2.3, §2.4, §2.6, §4.1) — all resolve to current text.
- **Transport/cipher** (§5.1/§5.2 TLS 1.3, HPKE) and **`cose:` signature prefix** — CONSISTENT with corpus (TLS/HPKE are transport-layer, out of the cipher-suite registry's scope; `cose:` matches `initial-registries` W4-BASE-1 and entity-types usage).

---

## §C — Routing for the remediation turn

### Autonomous-actionable (single-file, no design decision)
- **B1 + B11** — replace `mcp_server`→`service` (or `device`) and `mcp_client`→`ai` (or `service`) at §3.1 L76 / §3.2 L100; align §8.2 SPARQL form; also fix `MCP_ENTITY_SPECIFICATION.md:64`. *Recommend `service` for server (responsive+delegative; entity-types lists "microservices" under Service) and `ai` for client (§3.2 says clients are AI models); a remediator should confirm the two type choices against entity-types §2.1 before applying.* HIGH — sequence first.
- **B3** — rename §7.3 `witness_signatures` → `witnesses` to match r7 canonical (and adopt the `{lct, signature, timestamp}` element shape).
- **B4** — add the high-consequence witnessing MUST to §12's MUST list (or label §12 explicitly non-exhaustive).
- **B7** — define `partial` in §7.3, or drop it from the `outcome_class` enum.
- **B8** — add a one-line note that §9.1 `context` is an implementation-assembled aggregate; align `context.t3` → `t3_in_role`.
- **B9** — define `responding_role_expected` in §7.4's normative bullets, or remove it.
- **B10** — harmonize the role-id field names across §4.1/§6.1/§7.1, or add a clarifying note.
- **N14** (optional) — inline cross-ref §7.4 L451 ← L447.

### Design-Q / operator-coupled (do NOT self-resolve)
- **§7.7 v0.1.0-final promotion cluster**: N5 + N9 + N13 — the `atp_settlement` ↔ `rate_accept` wire-shape reconciliation. Resolve as ONE unit at promotion (the spec fences them WIP); do not patch piecemeal.
- **N12** (carry-C30, now sole mcp survivor): §10's JSON-RPC numeric + Python-exception error model vs the RFC-9457 `problem+json` taxonomy. Operator-scoped error-model decision.
- **N15** (carry-C33): `lct:web4:` naming entities vs data-formats `did:web4:` for entities. mcp is a high-volume consumer awaiting the operator's canonical entity-id form.

### Cross-track (touches other specs / SDK / registries)
- **B2 + B6** — reconcile mcp §7.3 `reputation` envelope with r7-framework §1.7 canonical Reputation: V3-delta coverage, `{change,from,to}` sub-key shape, `action_id` provenance. Coordinate r7 + mcp + SDK so all three agree on ONE reputation shape; do not unilaterally reshape mcp's normative envelope. (B2's V3-omission is the load-bearing piece.)
- **B5 + B12** — register mcp's §7.6 `web4_cross_society_*` and §7.7.7 `web4_rate_*` codes (→ registries track; couples C70/C71. Now unblocked on the *form* by N4's resolution; only the *home* remains).
- **F5 / C62-B1** — `interaction_type` values `established`/`federated` (mcp §7.4 L417) have no definition site in inter-society-protocol.md (only `first_contact` is grounded, ISP §3.1). Where these relationship states live is the standing **C62-B1** carry.
- **F9-inverted — corpus-wide `PolicyEntity` / `Policy-Entity` / `Policy` harmonization.** Three forms live: CLAUDE.md / SOIA-SAGE use `PolicyEntity`; society-roles.md §2.3 + mcp use `Policy-Entity`; entity-types.md taxonomy uses `Policy`. **Do NOT apply F9 to mcp alone** — mcp matches society-roles, and a single-file rename would manufacture drift. Pick one canonical form corpus-wide.

### Retired (no longer defects)
- **N4** — resolved-downstream by errors.md C67 (mcp's lowercase `web4_*` codes are now SSOT-sanctioned).
- **F9 as an mcp single-file fix** — premise inverted (see cross-track above for the real, corpus-wide question).

---

## Out of scope (handed off, not closed here)

- SDK-vs-spec conformance of §7 behavior beyond the EntityType-enum observation that confirmed B1 (separate SDK-alignment track).
- §7.7 promotion to v0.1.0-final (operator/fleet-review gated); N5/N9/N13 are inputs.
- The corpus-wide PolicyEntity-form decision (F9-inverted) and the C62-B1 relationship-state-home decision — recorded as cross-track, not resolved here.
- inter-society-protocol.md, r7-framework.md, errors.md, entity-types.md cited only as mirror references; not re-audited (policy-review advisory honored — mcp-protocol.md is the sole audited file).

---

*Delta re-audit only. No spec text modified. No SDK or test code touched. One new file. Instrument: multi-agent refute-by-default workflow (9 agents); see [[feedback_audit_workflow_adversarial_verify]] and [[feedback_remediation_introduced_regression]] (F9 inverted-premise mirror case).*
