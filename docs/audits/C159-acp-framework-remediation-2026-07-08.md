# C159 — ACP Framework Remediation

**Date:** 2026-07-08
**Remediator:** Autonomous session `legion-web4-20260708-180036`
**Document remediated:** `web4-standard/core-spec/acp-framework.md`
**Applies:** the 3 AUTONOMOUS items pre-declared by the C158 4th-delta audit (`docs/audits/C158-acp-framework-4th-delta-2026-07-08.md`, PR #485, merged `8151f636`).
**Lineage:** C18 (PR #244) → C37 (PR #283) → C86 → C87 (PR #378) → C125 (PR #434) → C126 (PR #437) → C158 (PR #485) → **C159** (this remediation).
**Mutation surface:** spec prose/pseudocode only. **ZERO SDK/schema/vector/.ttl mutation.** `detect_changes` = 0 symbols / 0 flows.

---

## Applied edits (3 autonomous, each authority-pinned, ≤1 logical line)

### 1. C156-5 — §7.2 L418 trust-gaming mitigation dereferences to an unspecified future mechanism

- **Before:** `| Trust gaming | Audit adjustments, reputation stakes |`
- **After:** `| Trust gaming | Audit adjustments (reputation staking is a future mechanism — see reputation-computation.md §10) |`
- **Why:** "reputation stakes" was acp's only "stake" token and dereferenced solely to `reputation-computation.md` §10 **"Reputation Staking"** (L789-790), which is explicitly under `## 10. Future Evolution` — no schema/SDK/vector/spec defines the mechanism. Every other cell in the mitigation table names a *specified* mechanism (resource caps, agency grants, law compliance, nonces), so listing an unspecified future mechanism as a current mitigation violates the table's own convention. Fix follows the **B-I1 / C156-2 shape** (soften to future, add cross-ref) applied at C157.
- **Authority:** reputation-computation.md §10 L789-790 (owner-confirmed Future Evolution). Inbound from the reputation audit (C156-5), adopted AUTONOMOUS at C158 §A.4 only after re-adjudication at the acp file per `[[feedback_prior_finding_path_provenance]]`.
- **Provenance / regression check:** the softened cell adds no new normative claim (it *removes* an over-strong "current mitigation" implication). No new prose to re-test against the SDK.

### 2. N1 — §10.2 L568 WitnessDeficit runtime-count branch mis-cited `(§4.1)`

- **Before:** `#   - runtime-count deficit (§4.1): too few witnesses gathered at execution time -> ...`
- **After:** `#   - runtime-count deficit (approval-gate phase, §3.2/§5.2): too few witnesses gathered at execution time -> ...`
- **Why:** §4.1 (L257-259) explicitly states the **opposite** — "Witness check deferred to approval-gate phase (§3.2 Approval Gate state). Witnesses live on Decision (§2.3), not Intent (§2.2)" — and `validate_acp_agency` raises only NoValidGrant/ScopeViolation/ResourceCapExceeded, never WitnessDeficit. The runtime witness gathering it describes happens at the approval gate (§3.2) under the §5.2 witness config (quorum/timeout/fallback; §5.2's `timeout: 300` matches `wait_for_witnesses(context, timeout=300)`).
- **Authority:** §4.1 L257-259 (deferral note) + §3.2 (approval-gate state) + §5.2 (witness requirements).
- **Provenance:** cross-remediation regression — C18 (`1bb9bcaa`) removed the §4.1 witness check + installed the deferral note; C37 (`c43822e9`) then wrote "(§4.1)" against the already-removed raise site. Survived C86/C125 §A because those checked the config-vs-runtime discrimination, not the citation's accuracy. The parallel ScopeViolation branch's §4.1 cite (L579) is CORRECT and untouched (grant-scope IS validated at §4.1) — consistent with a copy-parallel error confined to the witness branch.
- **Note:** the comment reflowed to two source lines to stay within the surrounding ~72-col width; semantics unchanged.

### 3. N3 — §4.1 L254 pseudocode dereferenced a non-existent flat `grant.resourceCaps`

- **Before:** `if exceeds_caps(intent, grant.resourceCaps):`
- **After:** `if exceeds_caps(intent, grant.scope.r6Caps.resourceCaps):`
- **Why:** the canonical Agency Grant Structure (entity-types.md §4.7 L365-397) has no top-level `resourceCaps`; caps are nested at `scope.r6Caps.resourceCaps` (L377-379: `"r6Caps": { "resourceCaps": {"max_atp": 25} }`). The pseudocode-shorthand refutation fails — the same function uses the exact canonical `grant.scope` at L250, and §5.1 uses the full `plan.guards.resourceCaps.maxAtp` path — so L254 was a wrong shape claim, not elision.
- **Authority:** entity-types.md §4.7 L377-379.
- **Casing note:** both container keys (`r6Caps`, `resourceCaps`) are camelCase in both files; `exceeds_caps` consumes the whole caps object, so this fix does **not** touch the open corpus `max_atp` snake_case DESIGN-Q.

---

## Routed — NOT self-applied this turn (recorded outbound to carries)

- **N2** (LOW-high, CROSS-TRACK): §2.4 L174 `maxAtp` "budget"/cumulative semantics + §6.2 L390 "approaching ATP cap" alert vs the SDK's **per-intent-only** cap enforcement (`check_atp` compares a single intent's `atp_requested`; `resources_consumed` is never summed; `check_executions` has zero call sites). Requires a **semantics decision** (SDK adds cumulative tracking, or spec rewords "budget" → per-action cap and re-cuts the §6.2 alert). Until decided, §7.2's "runaway automation" mitigation is soft. → SDK/operator track.
- **N4** (INFO): hub MCP write tools carry no ACP proof-of-agency — silent non-adoption behind the operator-plane guard, NOT a §9.1 MUST #5 violation (§4.2 self-scopes the requirement to calls "from ACP"; hub makes zero ACP claims). Converts to a real spec-lag gap only if hub later admits non-operator agentic callers. → INFO awareness, no action.
- **JSONC fences** (INFO-corpus): 3 of 7 `json` fences fail strict parse — established illustrative-annotation style shared by 7 of ~20 core-spec files; any relabel/strip is a corpus-wide operator DESIGN-Q. → carries INFO-corpus.

## Standing DESIGN-Q / cross-track carries (unchanged, re-verified STILL-OPEN at C158 §A.3)

B-LEDGERPROOF/C37-5; B11; B14 · B-AGENCY/L1 (mcp-owned); B8 (atp-adp §7.1 #5); B12/B13 (SAL); M6/B-M6 (ontology); B15 (D0 cluster); M7 (SDK bridge).

---

## Verification

- All three loci + both authority references independently re-verified at live HEAD before editing (session log Step 3).
- Policy review: **APPROVED** first pass (reviewer independently re-confirmed all three loci, the C156-5 in-corpus adoption path, and the N1 anchor).
- `detect_changes` (unstaged) = **0 changed symbols / 0 affected flows / risk none** — confirms spec-only, no SDK surface touched.
- Post-edit grep confirms: no residual flat `grant.resourceCaps`; no `reputation stakes` current-mitigation token; the sole `runtime-count deficit` cite now reads `(approval-gate phase, §3.2/§5.2)`.

---

## Note for the next ACP delta (C-series 5th, future)

The three edited loci are the newest net-new prose in acp-framework.md. Per `[[feedback_remediation_introduced_regression]]`, the next acp audit's §A should token-test:
- C156-5's softened cell against reputation §10 (still Future Evolution? if §10 promotes staking to specified, the "future mechanism" phrasing must update).
- N1's `(§3.2/§5.2)` anchor against those sections' live content (they must still describe approval-gate witness gathering + witness config).
- N3's `grant.scope.r6Caps.resourceCaps` path against entity-types §4.7 (if the grant structure moves caps, this pseudocode must follow).

Audit-side rotation advances acp → **presence-protocol** 4th delta (last: C127 3rd-delta / C128 remediation).

*C159 complete. 3 spec-local edits, 1 new file (this note). ACP lineage C18 → C37 → C86/C87 → C125/C126 → C158/C159.*
