# C234 — ACP Framework Sixth-Delta Re-Audit

**Date:** 2026-07-20
**Auditor:** Autonomous session `legion-web4-20260720-120036`
**Document audited:** `web4-standard/core-spec/acp-framework.md` (710 lines, blob `fb0075fc`)
**Method:** §A hand-verification against live HEAD (C159's three edits + C196's regression checklist + all standing carries). §B refute-by-default finder pass over the corpus-delta since C196 (5 commits) — primitive-clustered lenses (net-new-consumer / role-scope inbound; internal-consistency + neighbor-drift), each candidate refuted before recording; plus a hand-run SDK/Rust-mirror gate re-baselined on current HEAD.
**Lineage:** C18 (#244) → C37 (#283) → C86 (2nd) → C87 (#378) → C125 (3rd) → C126 (#437) → C158 (4th, #485) → C159 (remediation, #487 `fb0075fc`) → C196 (5th, zero net-new) → **C234** (this 6th delta).

---

## Instrument note — why ACP, why now

Rotation wraps reputation (C232 audit, #555 merged) → **acp**. The full acp authority stack is **byte-frozen since C159's merge `fb0075fc`** (2026-07-08): spec, SDK `acp.py`, schema `acp-jsonld.schema.json`, and `test-vectors/acp/` all show **0 commits** since — unchanged since C196 verified the same freeze. The yield surface is therefore the **corpus-delta since C196** (2026-07-15), which this interval carries 5 web4-standard commits:

| Commit | What | Prima-facie acp relevance |
|---|---|---|
| `4f76f110` | feat(role): oracle consult/write sets on `RoleExtension::Scope` (Piece B, oracle-scope gating) | **Highest** — shares the word "scope" with acp's N3 grant path `grant.scope.r6Caps.resourceCaps` |
| `2bc3bafb` | C214 entity-types 5th delta (#541) — Effector §4.8 regression-clean, C214-N1 stale forward-ref applied to reputation §4 | acp N3 cross-refs entity-types §4.7 grant structure |
| `d89595e8` | #531 canonize "Inspectable Evidence, Not Prescribed Trust" | touched LCT §1.2 + t3-v3 |
| `062fd24b` | C195 reputation remediation (#526) | acp §7.2 cross-refs reputation §10 |
| `cb788768` | #525 W4IP N3 Phase 2 code half — response vocabulary, parse-don't-enact | W4IP vocab (C196 flagship, refuted) |

Pre-declared question this delta had to answer: **does the new `RoleExtension::Scope` oracle-scope surface (`4f76f110`) touch acp's referenced grant structure, or is it a same-word/different-type collision?** (Answer below: disjoint by construction — two distinct "Scope" types at two layers.)

## Authority Hierarchy

Unchanged from C125/C158/C196: vectors → schema → SDK → spec prose; canonical neighbor owns its primitive.

---

## §A — C159/C196 Delta Re-Verification

### §A.1 — C159's three applied edits (present + regression-clean at live HEAD)

All three loci verified present and byte-identical to C196 (spec blob unchanged since):

| Edit | Locus | Live state | Anchor-target re-verified |
|---|---|---|---|
| **C156-5** softened trust-gaming cell | `:418` | `Audit adjustments (reputation staking is a future mechanism — see reputation-computation.md §10)` | reputation §10 **still `## 10. Future Evolution` (L835) + `### Reputation Staking` (L845)** — section-cite, line-shift-immune to C195's §5/§4 edits. HELD. |
| **N1** WitnessDeficit re-cite | `:568` | `runtime-count deficit (approval-gate phase, §3.2/§5.2): too few…` | acp §3.2 + §5.2 live/unchanged (frozen spec). HELD. |
| **N3** grant-path correction | `:254` | `exceeds_caps(intent, grant.scope.r6Caps.resourceCaps)` | entity-types §4.7 **still carries `"r6Caps": { "resourceCaps": {"max_atp": 25} }` (L377-379)**; Effector still appended at §4.8 (L399), *after* §4.7 — the grant structure did **not** move under C214/#541 (which edited reputation §4, not the entity-types grant JSON). HELD. |

**[[feedback_remediation_introduced_regression]] check: CLEAN.** Spec byte-frozen; nothing to introduce. The one neighbor edit that could have moved N3's anchor (C214's entity-types 5th delta) was verified to touch reputation §4 (the C214-N1 note), not the §4.7 grant JSON — the same anchor C196 pre-declared and checked, re-checked here against the live artifact rather than trusting the C196 result ([[feedback_prior_finding_path_provenance]]).

### §A.2 — C87's 8 fixes / 13-transition count

Byte-frozen since verified HELD at C158; spot-checked, nothing surfaced. Not re-litigated (SDK `VALID_TRANSITIONS` frozen).

### §A.3 — Standing DESIGN-Q / cross-track carries (re-verified STILL-OPEN)

| Carry | C196 state | C234 state | Live evidence |
|---|---|---|---|
| **M6 / B-M6** — 11 `acp:` predicates in no TTL | STILL-OPEN | **STILL-OPEN** | `grep acp: ontology/*.ttl` = 0. CROSS-TRACK (ontology). |
| **M7** — integer `witnessLevel` vs structured `witness_requirement` | STILL-OPEN | **STILL-OPEN** | Integer/structured split live; SDK integer-only. SDK bridge. |
| **B-AGENCY / L1** — `web4_context` proofOfAgency casing/field-set | STILL-OPEN | **STILL-OPEN** | mcp-owned envelope; mcp frozen this interval. MEDIUM CROSS-TRACK. |
| **B-LEDGERPROOF / C37-5** — §4.2 `ledgerProof` | STILL-OPEN | **STILL-OPEN** | Sole in-doc ledger object; SDK `ProofOfAgency` has no ledger proof. DESIGN-Q. |
| **B8** — ACP discharge not routed through R6 | STILL-OPEN | **STILL-OPEN** | atp-adp §7.1 #5 persists; acp §9.1 MUST list has no R6-discharge item. CROSS-TRACK. |
| **N2** — `maxAtp` "budget"/cumulative vs SDK per-intent-only cap | STILL-OPEN | **STILL-OPEN (unchanged)** | acp `:174` "against the plan's `resourceCaps.maxAtp` budget" live; SDK `check_atp` (acp.py L213-217) still `return atp_amount <= self.max_atp` (per-intent), `check_executions` (L219) still defined; SDK frozen ⇒ divergence unchanged. CROSS-TRACK semantics decision. |
| **N4** — hub MCP write tools carry no ACP proof-of-agency | INFO (trigger UNTRIPPED) | **STILL INFO (UNTRIPPED)** | No mover this interval admitted a non-operator agentic caller to hub write tools; `4f76f110`/`cb788768` are role-scope + policy code, not MCP write-tool caller paths. Not an acp defect regardless. |
| **B11 / B12 / B13 / B14 / B15** — DESIGN-Q & cross-track batch | STILL-OPEN | **STILL-OPEN** | No mover touched errors §10.1 envelope, SAL witness vocab, or the D0 cluster this interval. |
| **JSONC fences** | INFO-corpus | **INFO-corpus** | Corpus-wide style DESIGN-Q; operator-gated. |

### §A.4 — Neighbor-drift re-verification (acp's two hard cross-refs at live HEAD)

acp filename-cites exactly two neighbors (whole-file grep). Both resolve:

- **§2.4 `:172` → atp-adp §2.3.** acp `:172` = `…in the sense of [atp-adp-cycle.md] §2.3`; atp-adp L124 = `### 2.3 Discharging (ATP → ADP)`. atp-adp byte-frozen since C151 (C228 confirmed 5th delta), no drift on §2.3.
- **§7.2 `:418` → reputation §10.** Resolves (§A.1). C195's reputation edits (§5 no-match→None; dropped spec-only `value` key; §4 Coercive/Extractive category note) touch **nothing acp consumes** — acp's trust delta is `t3v3Delta` (a dimension→delta map L161-164), a different shape from reputation's factor structure; `grep coercive|extractive|analyze_factor|category` in acp = 0. C232-N1 (the reputation `delta.category` recognition→response seam) is a reputation/response-side concern with **zero acp referent**.

---

## §B — New / Hardened Findings (this delta)

**Result: ZERO net-new confirmed findings.** The flagship candidate (`4f76f110` role-scope inbound) was refuted; the internal + neighbor-drift sweep surfaced nothing concrete; the SDK/Rust-mirror gate returned NEGATIVE. **Third zero-net-new acp delta** (C125 first; C158 broke it with 4, all applied by C159; C196 second; C234 third).

### Summary by severity

| Severity | Count | IDs |
|----------|-------|-----|
| MEDIUM+ | 0 | — |
| LOW | 0 | — |
| INFO | 1 (awareness-only, NOT routed) | §B.1 |
| **Net-new confirmed** | **0** | — |
| Carries re-confirmed | 9 groups | §A.3 |

### §B.1 — Flagship candidate REFUTED: `RoleExtension::Scope` oracle sets do not touch acp's `grant.scope` (two "Scope" types, one word)

**Candidate (strongest form).** `4f76f110` adds `oracle_consult_set` / `oracle_write_set` to `RoleExtension::Scope` (`web4-core/src/role_extension.rs`, siblings of `ranges_over` / `atp_budget`), plus `role:oracleConsultSet` / `role:oracleWriteSet` in `role-extension.ttl`. A skeptic argues: (a) acp's N3 grant path is `grant.scope.r6Caps.resourceCaps` — a `.scope` with resource limits — so a new oracle-access dimension on "Scope" makes acp's grant-scope model stale; (b) acp's `within_scope(intent.proposedAction, grant.scope)` gate (§4.1 `:250`) and `law_oracle` (§5.1 `:301-303`) should now account for oracle-consult/write membership; (c) the new field is a reputation-blind R6 gate — acp §5.2 witness/reputation logic might need to mirror it.

**Refutation (wins on all three).**
1. **Two structurally distinct types sharing the word "scope."** acp's `grant.scope` is the **entity-types §4.7 Agency Grant** shape — a nested object `{ r6Caps: { resourceCaps: {max_atp,…}, … } }` describing *what an agent may do on a principal's behalf* (proposed-action bounds + resource caps). `RoleExtension::Scope` is a **flat role-descriptor** `{ ranges_over: [MRH paths], atp_budget, oracle_consult_set, oracle_write_set }` describing *the launch-time path/oracle horizon of a role*. Different owners (entity-types AGY vs role-extension), different shapes (nested `r6Caps` vs flat lists), different lifecycles (per-intent agency grant vs frozen-at-grant role descriptor). The collision is lexical, not semantic.
2. **acp references neither the role descriptor nor the oracle plane.** Whole-file grep: acp's only "oracle" tokens are `law_oracle` (§5.1 `:301-303`, an **abstract compliance oracle** — `law_oracle.get_law(plan.guards.lawHash)`) and "Blockchain Oracles" (§Appendix future integrations `:692`). Neither is the memory-as-oracle role-scope plane. acp has **zero** references to `ranges_over`, `RoleExtension`, `atp_budget` (the role field), or `oracle_consult/write_set`. The `4f76f110` surface is downstream of acp entirely (the consuming gate is Legion's `check_oracle`, a role-launcher predicate), so no acp claim can be stale against it.
3. **Same "abstract the oracle" layering property C196 found for W4IP vocab.** acp deliberately abstracts its gates (`law_oracle`, `within_scope`, `allows_trigger`) rather than baking in a specific schema. Forcing acp to import `RoleExtension::Scope`'s oracle sets would be the **same layering violation** C196 refuted for the hub-law decision vocabulary — a protocol depending on one role-launcher implementation. The role-scope gate and acp's agency-grant gate are parallel R6-gated mechanisms at different layers; a cross-reference from acp would be additive, never required.

**INFO (awareness-only, NOT a remediation carry).** The lexical collision "Scope" (agency-grant `grant.scope` vs role-descriptor `RoleExtension::Scope`) is a *reader* hazard, not a spec defect — the two live in different specs and never co-occur in acp. A future glossary pass *could* disambiguate, but adding an acp cross-ref risks the false coupling C196 warned against. **Explicitly do NOT promote to C235.** (Directly analogous to C196 §B.1's optional vocabulary-distinction note, which was also held un-routed.)

### §B.2 — SDK / Rust-mirror gate: NEGATIVE (re-baselined on current HEAD)

Re-baselined at live HEAD (web4-core carries the new `role_extension.rs` oracle fields + prior `attestation.rs`): **no Rust ACP mirror exists.** No `Plan` / `Intent` / `Decision` / `ExecutionRecord` / `ACPState` structs in `web4-core/src/` or `hub/`; the sole `ProofOfAgency` is `web4-core/src/r6.rs:103` (already routed C156-3, inside excluded B-AGENCY). `4f76f110`'s additions are **role-descriptor scope**, not ACP. This reproduces the C158/C196 lens-d negative and matches the C182 (registries) / C220 NEGATIVE-gate pattern: acp's only implementation is the frozen Python SDK. No layer-split, no wire-shape divergence to route. Per the standing method guard, the checker was baselined on the *moved* artifact (post-`4f76f110`) rather than trusting C196's negative ([[feedback_enumeration_and_grep_hypotheses]]).

### Load-bearing finder negatives (coverage record)

- **role-scope / net-new-consumer lens:** examined `4f76f110` (role_extension.rs + role-extension.ttl), acp `grant.scope` / `within_scope` / `law_oracle` sites — flagship refuted (§B.1); disjoint by type.
- **internal + neighbor-drift lens:** both hard cross-refs resolve (§A.4); `#531` touched LCT §1.2 / t3-v3 / README / CLAUDE.md — acp cites **none** (grep `inspectable|prescribed trust|1.2` in acp = 0); C214/#541 edited reputation §4, not the entity-types §4.7 grant JSON N3 anchors to; `#525` W4IP code half is web4-policy, no acp referent.
- **SDK/Rust-mirror gate:** NEGATIVE (§B.2).

---

## Routing Summary (for the C235 turn)

**C235 remediation would be a NO-OP: zero autonomous items routed.** §A fully clean (three C159 edits HELD, all anchors resolve, all carries STILL-OPEN); §B produced no LOW-or-above finding.

- **AUTONOMOUS — apply in C235:** *(none)*
- **ROUTED — not autonomous (unchanged carries):** N2 (CROSS-TRACK SDK/operator semantics — `maxAtp` budget-vs-per-intent); N4 (INFO, UNTRIPPED); JSONC fences (INFO-corpus).
- **DESIGN-Q / CROSS-TRACK carries (re-verified STILL-OPEN §A.3):** B-LEDGERPROOF/C37-5; B11; B14; B-AGENCY/L1 (mcp-owned); B8 (atp-adp §7.1 #5); B12/B13 (SAL); M6/B-M6 (ontology); B15 (D0 cluster); M7 (SDK bridge).
- **INFO awareness (NOT routed):** the optional §B.1 "Scope" disambiguation note.

**Rotation:** since C234 routes zero autonomous items, there is no C235 remediation edit. Audit-side rotation advances acp → **presence-protocol** 4th delta (last: C127 3rd / C128 remediation — verify at that turn). Next acp delta ~C272.

---

## Calibration Note

C234 is a **clean delta on a byte-frozen target** — the expected shape when a file churns slower than the rotation cadence, and the third zero-net-new acp delta. The instructive result is again **negative and load-bearing**: the interval's most acp-adjacent inbound (`4f76f110` adds an oracle-access dimension to a type literally named `Scope`) produced **no drift**, because ACP's `grant.scope` and the role-launcher `RoleExtension::Scope` are distinct types owned by distinct specs — a *lexical* collision the delta had to actively disprove rather than assume. This is the same property that protected acp under the W4IP vocabulary expansion (C196): ACP abstracts its oracles/gates instead of baking in a neighbor's schema, so neighbor schema growth is additive, never invalidating.

Two method points confirmed: (1) the **same-word/different-type** trap is exactly where a shallow grep would false-positive — the flagship was refuted by comparing *structure* (nested `r6Caps` vs flat role fields) and *owner* (entity-types AGY vs role-extension), not token overlap ([[feedback_refute_your_best_finding]]). (2) The **N3 anchor re-check against the live entity-types §4.7** (rather than trusting C196's HELD) confirmed C214/#541 edited reputation §4, not the grant JSON — the neighbor edit that *could* have moved the anchor did not ([[feedback_prior_finding_path_provenance]]).

---

*C234 complete. NO spec/SDK/schema/vector/.ttl mutation (AUDIT turn). C235 remediation is a NO-OP (zero autonomous items) — audit-side rotation advances acp → presence-protocol 4th delta. ACP lineage C18 → C37 → C86/C87 → C125/C126 → C158/C159 → C196 → C234.*
