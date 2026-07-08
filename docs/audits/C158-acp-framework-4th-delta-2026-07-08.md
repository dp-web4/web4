# C158 — ACP Framework Fourth-Delta Re-Audit

**Date:** 2026-07-08
**Auditor:** Autonomous session `legion-web4-20260708-120003`
**Document audited:** `web4-standard/core-spec/acp-framework.md` (709 lines)
**Method:** §A hand-verification against the live spec + SDK + schema + vectors. §B multi-agent refute-by-default workflow (4 primitive-clustered lens finders — internal cross-section, atp-adp/t3-v3/reputation neighbor drift, mcp/agency-envelope drift, **Rust-implementation sweep** — every finding piped to an adversarial verifier instructed to refute by default; routed candidates pinned to one lens each per the C52 addendum).
**Lineage:** C18 (first-pass, PR #244) → C37 (PR #283) → C86 (2nd-delta) → C87 (remediation PR #378 `31cea0b0`) → C125 (3rd-delta, PR #434) → C126 (remediation PR #437 `aabe4457`) → **C158** (this 4th delta).

---

## Instrument note — why ACP, why now

Rotation wraps reputation → acp (C156/C157 pair closed with #484 merged + operator APPROVED). The target is **byte-frozen since C126** (`aabe4457`, 2026-07-02, is its last touch; SDK `acp.py`, schema `acp-jsonld.schema.json`, and `test-vectors/acp/` have **0 commits** since — the full authority stack is frozen). The yield surface is therefore (1) remediation-completeness + remediation-introduced-regression on C126's own 4-token edit, (2) the corpus-delta since `aabe4457` — remarkably narrow on the spec side (4 files: atp-adp §2.4 reword C151, reputation §9 C157, FRACTAL_ROLE_IDENTITY line-number fix, presence-protocol schema README) but **large on the impl side** (hub Rust ~2.2k lines #462–#481, `web4-core/src/r6.rs`, web4-trust-core tensor consolidation), and (3) two pre-declared inbound adjudications: **C156-5** (acp:418 dereference failure, routed here by the reputation audit) and **C126's own routed JSONC-fence observation**. Per the C156 lesson, non-spec impl deltas that newly consume the target's semantics are swept as first-class movers (lens d).

## Authority Hierarchy

Unchanged from C125 (see that doc's table): vectors → schema → SDK → spec prose; canonical neighbor owns its primitive.

---

## §A — C125/C126 Finding Delta Re-Verification

### §A.1 — C126's M3 fix (HELD + remediation-introduced-regression check)

C126 applied exactly one item (M3): 4 tokens, §2.1 L77-79 `maxAtp`/`maxExecutions`/`rateLimit` + §5.1 L312 `.maxAtp`. Re-verified token-by-token at live HEAD:

- All four edits present; keys match schema `$defs.ResourceCaps` (L56-58) exactly.
- `law.max_atp_per_plan` (L312 RHS) correctly left snake_case — it is a law attribute, not a guard key (re-confirmed as a distinct symbol).
- Full-document grep: no residual snake_case guard keys; §2.4 L174 and §11 L604 already-camelCase loci unchanged.
- **[[feedback_remediation_introduced_regression]] check: CLEAN.** C126's edit introduced no new prose claims (pure token substitution), and its verification note's parse-count claim ("3 bad / 7 total, pre-existing") is re-derived below (§A.4) and confirmed exact. Second consecutive clean ACP remediation (C87, C126).

### §A.2 — C87's 8 fixes (spot re-verification of the computed ones)

- **B2 footnote (L234):** re-derived from the live SDK, not pattern-matched: `VALID_TRANSITIONS` (acp.py L173-182) totals **13** edges; exactly **5** states carry `→FAILED` (PLANNING, INTENT_CREATED, APPROVAL_GATE, EXECUTING, RECORDING); table has **8** explicit rows; 5+8=13 = vector `acp-002 totalValidTransitions`. Still correct.
- **B5 SPARQL (§8.2):** file frozen; C125's structural validation stands.
- Remaining six (B1/B3/B4/B6/B7/B10): byte-frozen since verified HELD at C125.

### §A.3 — Standing carries (re-verified at live HEAD, snapshot-presence guard applied)

| Carry | C125 state | C158 state | Live evidence |
|---|---|---|---|
| **M6 / B-M6** — 11 `acp:` predicates in no TTL | STILL-OPEN | **STILL-OPEN (unchanged)** | `grep acp: ontology/*.ttl` = 0 across all three TTLs (incl. post-rename `hub-law.ttl`). CROSS-TRACK (ontology). |
| **M7** — integer `witnessLevel` vs structured `witness_requirement` | STILL-OPEN | **STILL-OPEN (unchanged)** | Integer at L81/L316; structured at L329; SDK integer-only. |
| **B-AGENCY / L1** — `web4_context` proofOfAgency casing + field-set + `agency_chain` | STILL-OPEN | **STILL-OPEN (unchanged after mcp C148-clean)** | Live mcp: §4.1 `proof_of_agency {grant_id, scope}` snake_case (L145); §7.4 `agency_chain` (L452, L484-488). acp §4.2 7-key camelCase unchanged. mcp frozen since C117; C148 audited it clean without touching §4.1/§7.4. MEDIUM CROSS-TRACK (mcp-owned envelope). |
| **B-LEDGERPROOF / C37-5** — §4.2 `ledgerProof {grantBlock,grantHash,inclusionProof}` | STILL-OPEN | **STILL-OPEN (unchanged)** | Sole in-doc ledger object §4.2 L281-285; SDK `ProofOfAgency` = 6 fields (acp.py L592-604), no ledger proof; schema `additionalProperties:false` unchanged (0 commits). DESIGN-Q. |
| **B8** — ACP discharge not routed through R6 | STILL-OPEN | **STILL-OPEN (unchanged after atp-adp C150/C151)** | atp-adp §7.1 #5 persists (L621); the demurrage carve-out note (atp-adp L326-331) citing MUST #5 **predates C126** (present at `aabe4457` — snapshot-presence guard) and scopes *maintenance* discharge, not ACP execution discharge. acp §9.1 MUST list still has no R6-discharge item. CROSS-TRACK. |
| **B11 / B12 / B13 / B14 / B15** — DESIGN-Q & cross-track batch | STILL-OPEN | **STILL-OPEN (unchanged)** | No mover touched errors.md envelope (§10.1), SAL witness vocab, or the C75 D0 cluster this interval. |

**Snapshot-presence guard summary.** Both spec-side movers edited **outside** acp's cross-ref surface: C151 reworded the atp-adp *conservation-invariant scope* ("ATP→ADP transfers" → "ATP transfers between entities (§6.3)") — acp cites only §2.3 *discharge* (its §2.4 note L171-176) and nowhere invokes the conservation invariant (`grep conservation|initial == final` = 1 hit, the §2.3 citation itself); C157 edited reputation §9 Sybil item 4 — acp does not cite reputation §9. FRACTAL_ROLE_IDENTITY (mrh line-number fix) and presence-protocol README (schema known-gap ledger) carry no acp surface. **Clean inbound on all four spec movers.** Note C151's edit is *load-bearing for acp in the favorable direction*: under the old wording ("conservation scopes ATP→ADP transfers"), acp's §2.4 equation of `resourcesConsumed.atp` with the §2.3 ATP→ADP transition sat awkwardly close to a mis-scoped invariant; the C151 clarification removes that latent ambiguity without acp moving.

### §A.4 — Inbound adjudication 1: C156-5 (acp:418 "reputation stakes") — **ADOPTED, AUTONOMOUS → C159**

Adjudicated **at the acp file against acp's own constraints** per [[feedback_prior_finding_path_provenance]]:

- §7.2 L418 lists `reputation stakes` as a *current* trust-gaming mitigation. It is acp's **only** "stake" token (whole-file grep).
- Sole corpus dereference: reputation-computation §10 L789-790 "**Reputation Staking** — Allow entities to stake their reputation as collateral for high-trust actions" — explicitly **Future Evolution**, unspecified. No schema, SDK, vector, or other spec defines the mechanism.
- Refutation attempted: no ATP-stake in acp could rescue the phrase (acp has no `min_atp_stake`; resource caps are budgets, not stakes). The C156 refutation-test (reputation's own §4 `min_atp_stake` is an ATP stake, not reputation-as-collateral) holds from this side too.
- **Fitness of prescription re-checked at the target:** the C156-2/B-I1 fix shape transfers cleanly — soften to future/SHOULD with a cross-ref, e.g. `Trust gaming | Audit adjustments (reputation staking is a future mechanism — see reputation-computation.md §10)` or split current-vs-future. The mitigation table's other cells all name *specified* mechanisms (resource caps, agency grants, law compliance, nonces), so the defect is real by the table's own convention.
- Verdict: **LOW, AUTONOMOUS** — the single autonomous item this audit routes to C159. Third consecutive audit where a citation fails the dereference test (C154-N1 → C156-1 → C156-5), confirming dereference-testing as a standing lens.

### §A.5 — Inbound adjudication 2: C126's routed JSONC-fence observation — **INFO, corpus-style, no acp-local action**

Re-derived: exactly 3 of 7 `json` fences fail strict `json.loads` (L39 triggers, L128 decision, L327 witness-requirement) — matching C126's count, pre-existing since before C87. **Corpus-wide sweep (the deflating evidence):** 7 of ~20 core-spec files carry `//`-annotated json fences (dictionary-entities 4, mcp-protocol 3, acp 3, atp-adp 2, t3-v3 2, LCT 2, entity-types 2). This is an established illustrative-annotation style, not an acp defect — the same deflation shape as C31's missing-header DESIGN-Q → INFO (a property shared by half the corpus is corpus style). **Adjudication: option (c) accept-as-illustrative at the acp level; INFO.** Any relabel-to-`jsonc`/strip decision is a corpus-wide style DESIGN-Q for the operator, not an acp-local fix. Routed to carries as INFO-corpus; NOT queued for C159.

---

## §B — New / Hardened Findings (this delta)

**Method:** 4 lens finders → adversarial refute-by-default verify (every cited line re-read live; verdicts REAL/OVERSTATED/FALSE with corrected severity/disposition). 8 agents, ~381k tokens. All 4 candidate findings survived verification as REAL at their corrected levels; finder negatives (below) are load-bearing coverage.

### Summary by severity

| Severity | Count | IDs |
|----------|-------|-----|
| MEDIUM | 0 | — |
| LOW | 3 | N1, N2, N3 |
| INFO | 1 | N4 |
| **Net-new confirmed** | **4** | first non-zero ACP §B since C86 |
| Carries re-confirmed | 6 groups | §A.3 |
| Inbound adjudications | 2 | C156-5 (adopted), JSONC (deflated to INFO-corpus) |

### N1 (LOW, AUTONOMOUS → C159) — §10.2 WitnessDeficit branch mis-cites "(§4.1)" as the runtime-count raise site; §4.1 explicitly disclaims any witness check

`acp-framework.md:568`: the §10.2 recovery comment says the runtime-count deficit is raised at "(§4.1)". §4.1 L257-259 states the **opposite** — "Witness check deferred to approval-gate phase (§3.2 Approval Gate state). Witnesses live on Decision (§2.3), not Intent (§2.2)" — and `validate_acp_agency` raises only NoValidGrant/ScopeViolation/ResourceCapExceeded. The sole in-file `raise WitnessDeficit()` is §5.1 L318 (config-level branch); the SDK defines the class (acp.py L101) but **never raises it**. **Provenance: remediation-introduced regression** — C18's remediation (`1bb9bcaa`) removed the §4.1 witness check and installed the deferral note; C37's remediation (`c43822e9`) then wrote "(§4.1)" against the already-removed raise site. It survived C86/C125 §A because those passes presence-checked the config-vs-runtime *discrimination*, not the *citation's accuracy*. Distinct from refuted F2/F3 (the wait branch is legitimate taxonomy-dispatch; the defect is only the factually wrong internal cite — the parallel ScopeViolation branch's §4.1 cite at L579 is CORRECT, consistent with a copy-parallel error). **Fix: one-token re-cite** `(§4.1)` → `(approval-gate phase, §3.2/§5.2)`. Verifier: REAL/LOW/AUTONOMOUS (quoted both sides; confirmed §10.2 preamble does not rescue a wrong cross-reference; confirmed §5.2 `timeout: 300` matches `wait_for_witnesses(context, timeout=300)`).

### N2 (LOW high-end, CROSS-TRACK routed) — §2.4 `maxAtp` "budget" (cumulative) semantics vs SDK per-intent-only cap enforcement

`acp-framework.md:174` (C87-B7's note): "ACP records consumption against the plan's `resourceCaps.maxAtp` **budget**" + §6.2 L390 dashboard alert "Plan **approaching** ATP cap" — both presuppose cumulative accrual toward the cap. The SDK enforces **per-intent only**: `check_atp` (acp.py L213-217) compares a single intent's `atp_requested` against `max_atp` at its sole call site (L1078-1081); `resources_consumed` is never summed against `max_atp`; `check_executions` has **zero call sites**. **Provenance: the "budget" clause is C87 net-new prose exceeding C86-B7's prescription** (which asked only for the `atpConsumed` == atp-adp §2.3 discharge cross-ref) — the remediation-introduced-regression class, missed by C125 §A.2 which token-tested only B2's arithmetic and B5's SPARQL. Real stakes: §7.2 L414 claims resource caps mitigate "runaway automation," which a per-intent-only cap cannot; yet §4.1 L254 `exceeds_caps(intent, …)` is per-intent-shaped — the spec is internally mixed, so a **semantics decision** is required (SDK adds cumulative tracking, or spec rewords "budget" → per-action cap and re-cuts the §6.2 alert). Verifier: REAL/LOW-high/CROSS-TRACK (no vector covers cap enforcement — acp-001 hashes guards only; the contradiction rides on a non-MUST accounting note + illustrative dashboard). NOT autonomous — routed.

### N3 (LOW, AUTONOMOUS → C159) — §4.1 pseudocode dereferences `grant.resourceCaps`, a top-level member that does not exist on the canonical AGY grant

`acp-framework.md:254`: `exceeds_caps(intent, grant.resourceCaps)` — the only flat `grant.resourceCaps` in the corpus. The canonical Agency Grant Structure (entity-types.md §4.7 L365-397) has top-level members {type, grantId, client, agent, society, lawHash, scope, duration, witnesses, signatures} with caps nested at `scope.r6Caps.resourceCaps`. The pseudocode-shorthand refutation fails: the same function uses the exact canonical path `grant.scope` at L250, and §5.1 uses the full `plan.guards.resourceCaps.maxAtp` path — L254 is a shape claim, not elision. No SDK mirror exists (no `AgencyGrant` class in any SDK module). Same dereference-to-nothing class as C154-N1/C156-1/C156-5. **Fix: one-line path correction** to `grant.scope.r6Caps.resourceCaps` (container key is camelCase in both files, so the fix does not touch the open corpus `max_atp` casing DESIGN-Q — `exceeds_caps` consumes the whole caps object). Verifier: REAL/LOW/AUTONOMOUS.

### N4 (INFO, awareness) — hub MCP write tools carry zero ACP proof-of-agency: silent non-adoption, NOT a violation

`hub/hub-daemon/src/mcp.rs:401`: hub's write tools sign as the Sovereign behind an operator-plane guard (loopback/token, #462/#468/#473) with no `web4_context.proofOfAgency`. NOT a contradiction of acp §9.1 MUST #5: §4.2 L266 self-scopes the requirement to calls "**from ACP**", and hub makes **zero** ACP conformance claims (corpus grep for acp/agency-grant/W4_ERR_ACP across hub = 0; `SignIntent` at signer.rs:51 is a name-collision-only vault primitive). **Trigger to watch:** if hub later admits non-operator agentic tool calls (autonomous members invoking write tools), the ACP-adoption question becomes live and this converts to a real spec-lag gap. Verifier: REAL/INFO/INFO-ONLY.

### Load-bearing finder negatives (coverage record)

- **atp-adp/t3-v3 lens:** §2.4 ATP-accounting note token-verified against LIVE atp-adp §2.3 post-C151 — heading/semantics unchanged, `atpConsumed` key name identical; C151's invariant rescope does not touch any acp claim (acp never mentions conservation). **C90 shared-example-DATA diff CLEAN**: `temperament`/`valuation` ∈ canonical roots, values producible under t3-v3 §2.3 outcome table; sparse-delta refutation STANDS (t3-v3 zero commits since baseline). atp amounts consistent incl. §2.1 maxAtp 25 == vector acp-001 `25.0`.
- **internal lens:** §3.2 footnote 8+5=13 re-verified vs vector acp-002; §8.1/§8.2 predicate declarations HELD; full internal cross-ref sweep — all resolve except the single N1 mis-cite; §3.1 "Post-Audit" diagram node adjudicated NOT a defect (lifecycle flow, not state machine; §7.1 layer 5 gives it a home; 13-count complete without it).
- **mcp-agency lens:** §4.2 "Every MCP call from ACP includes proof" vs mcp's conditional "validated when present" = compatible layered strictness; **W4_ERR_ACP registry CLEAN** — errors.md §1 explicitly delegates subsystem code extension, and all 8 spec codes match SDK `error_code` strings byte-exactly; §7 security semantics (nonces/expiry/caps) compatible with mcp §5.2/§7.2/§13; a candidate envelope-members finding was self-refuted as inside excluded B-AGENCY.
- **rust-impl lens:** `web4-core/src/r6.rs` delta since freeze = exactly the +34-line SovereignStrength/ReputationDelta surface **already routed as C156-3** — zero ACP content; web4-core `ProofOfAgency` struct divergence is pre-existing (present at `aabe4457`) and inside excluded B-AGENCY; full hub sweep = no ACP.Plan/Intent/Decision/ExecutionRecord shapes; hub "approval" vocabulary = SAL governance, not ACP approval gates; a candidate MED (hub vs §9.1 MUST #5 unconditional reading) was refuted by §4.2's self-scoping — the doc resolves its own apparent contradiction.

---

## Routing Summary (for the C159 remediation turn)

### AUTONOMOUS — spec-local, authority pinned, apply in C159 (3 items; C159 is NOT a no-op)

1. **C156-5** (§A.4): §7.2 L418 — soften `reputation stakes` to future/SHOULD with a reputation-computation §10 cross-ref (B-I1/C156-2 fix shape).
2. **N1**: §10.2 L568 — re-cite `(§4.1)` → `(approval-gate phase, §3.2/§5.2)`.
3. **N3**: §4.1 L254 — `grant.resourceCaps` → `grant.scope.r6Caps.resourceCaps` (authority: entity-types.md §4.7).

### ROUTED — not autonomous

- **N2** → CROSS-TRACK (acp+SDK semantics decision): `maxAtp` cumulative-budget vs per-intent cap — operator/SDK-track picks: (a) SDK implements cumulative `resources_consumed` tracking against `max_atp` (+ wire up `check_executions`, currently zero call sites), or (b) spec rewords "budget" → per-action cap and re-cuts the §6.2 "approaching" alert. Until decided, §7.2's "runaway automation" mitigation claim is soft.
- **N4** → INFO awareness, hub-adjacent: no action; converts to spec-lag only if hub admits non-operator agentic callers.
- **JSONC fences** (§A.5) → INFO-corpus style DESIGN-Q (7 of ~20 core-spec files); any relabel/strip is corpus-wide, operator-gated.

### DESIGN-Q / CROSS-TRACK carries (unchanged, NOT self-applied)

B-LEDGERPROOF/C37-5; B11; B14 (operator DESIGN-Q) · B-AGENCY/L1 (mcp-owned); B8 (atp-adp §7.1 #5); B12/B13 (SAL); M6/B-M6 (ontology); B15 (D0 cluster); M7 (SDK bridge). All re-verified STILL-OPEN at §A.3.

---

## Calibration Note

C158 breaks the clean-delta streak (C125 was 0 net-new) with **4 confirmed findings on a byte-frozen target** — and the two most instructive are both **remediation-introduced regressions from remediations previously declared clean**: N1 was born when C37's remediation wrote a §4.1 citation against a raise site C18's remediation had already removed (a *cross-remediation* interaction — neither remediation was wrong in isolation); N2 is C87 net-new prose ("budget") exceeding its C86-B7 prescription, surviving C125's §A.2 regression check because that check token-tested only the *computed* edits (B2 arithmetic, B5 SPARQL), not the *semantic claims* of prose edits. **Lesson for the standing method: the remediation-regression sweep must (a) check citation accuracy of every cross-reference a remediation writes, against the state its *sibling remediations* left behind, and (b) token-test prose edits' semantic claims against the SDK, not just their presence.** The dereference-test lens also scored its 4th consecutive hit (C154-N1 → C156-1 → C156-5 → N3): every audit since C154 has found at least one citation/path that dereferences to nothing — it should remain a standing first-class lens.

The §A inbound surface behaved exactly as the snapshot-presence guard predicts: all four spec-side movers were disjoint by cited hunk, and C151's atp-adp rescope is *favorable* to acp (removes a latent ambiguity acp never depended on). The Rust sweep (lens d) earned its first-class-mover status negatively but valuably: hub's authorization model is confirmed non-ACP by design with a named future trigger, and the r6.rs delta is confirmed fully covered by the already-routed C156-3.

---

*C158 complete. NO spec/SDK/vector/.ttl mutation (AUDIT turn). Next: **C159 remediation turn** — apply the 3 autonomous items (C156-5 §7.2 L418; N1 §10.2 L568; N3 §4.1 L254), each a ≤1-line spec-local edit with in-corpus authority; route N2 to the SDK/operator track. Audit-side rotation advances acp → **presence-protocol** 4th delta (last: C127 3rd-delta 2026-07-02 / C128 remediation — verify at that turn). ACP lineage C18 → C37 → C86/C87 → C125/C126 → C158 → (C159).*
