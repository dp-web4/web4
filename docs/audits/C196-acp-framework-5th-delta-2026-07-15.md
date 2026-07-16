# C196 — ACP Framework Fifth-Delta Re-Audit

**Date:** 2026-07-15
**Auditor:** Autonomous session `legion-web4-20260715-180036`
**Document audited:** `web4-standard/core-spec/acp-framework.md` (710 lines)
**Method:** §A hand-verification against the live spec + SDK + neighbor cross-refs (C159's three edits + its pre-declared regression checklist + all standing carries). §B refute-by-default multi-agent finder pass — two primitive-clustered lenses (W4IP-vocabulary inbound; internal-consistency + neighbor-drift), each candidate refuted before recording; plus a hand-run SDK/Rust-mirror gate baselined on current HEAD.
**Lineage:** C18 (PR #244) → C37 (PR #283) → C86 (2nd) → C87 (PR #378) → C125 (3rd) → C126 (PR #437) → C158 (4th, PR #485) → C159 (remediation, PR #487 `fb0075fc`) → **C196** (this 5th delta).

---

## Instrument note — why ACP, why now

Rotation wraps reputation (C194 audit / C195 remediation, #524/#526 merged) → **acp**. The full acp authority stack is **byte-frozen since C159's merge `fb0075fc`** (2026-07-02): the spec, SDK `acp.py`, schema `acp-jsonld.schema.json`, and `test-vectors/acp/` all show **0 commits** since. The yield surface is therefore (1) remediation-completeness + remediation-introduced-regression on C159's three edits, and (2) the corpus-delta since `fb0075fc` — which this interval is **substantial and governance-flavored**: the four merged **W4IP** PRs (#521/#522/#523/#525) ratified new controlled vocabularies (decision `allow|warn|deny|escalate`, response `notice|quarantine|correct|rehabilitate`, Effector Role, Coercive/Extractive rule category), plus reputation C194/C195 edits, mcp §7.8 async mailbox (#520), entity-types §4.8 Effector insert, and t3-v3 Talent-no-decay (#517). The pre-declared question this delta had to answer: **do the W4IP ratifications create any drift in the frozen acp vocabulary?** (Answer below: no — clean-by-layer.)

## Authority Hierarchy

Unchanged from C125/C158: vectors → schema → SDK → spec prose; canonical neighbor owns its primitive.

---

## §A — C158/C159 Delta Re-Verification

### §A.1 — C159's three applied edits (present + regression-clean)

All three edits present at live HEAD, verified token-by-token:

| Edit | Locus | Live state | Anchor-target re-verified |
|---|---|---|---|
| **C156-5** softened trust-gaming cell | `:418` | `Audit adjustments (reputation staking is a future mechanism — see reputation-computation.md §10)`; no bare `reputation stakes` token in the file | reputation-computation.md **§10 still `## 10. Future Evolution` (L831) + `### Reputation Staking` (L841)**. The cell cross-refs the *section*, so the C194/C195 line-shift (§10 ~L789→L831) does **not** break it. HELD. |
| **N1** WitnessDeficit re-cite | `:568` | `runtime-count deficit (approval-gate phase, §3.2/§5.2): too few…`; no `(§4.1)` mis-cite remains | acp §3.2 Approval-Gate state (L226-227) + §5.2 witness config (`timeout: 300` L336, `wait_for_witnesses(context, timeout=300)` L576) both live and unchanged. HELD. |
| **N3** grant-path correction | `:254` | `exceeds_caps(intent, grant.scope.r6Caps.resourceCaps)`; no flat `grant.resourceCaps` remains | entity-types.md §4.7 Agency Grant Structure (L365) with `"r6Caps": { "resourceCaps": {"max_atp": 25} }` (L377-379). **Critically: #523's Effector insert landed at §4.8 (L399), *after* §4.7 — the grant structure did not move.** HELD. |

**[[feedback_remediation_introduced_regression]] check: CLEAN.** C159's edits were pure re-cites/softening; none introduced a new normative claim. The one place a neighbor edit could have silently invalidated a C159 anchor — entity-types §4.8 Effector shifting §4.7 — was explicitly checked and did NOT occur (Effector appended after the grant structure). Third consecutive clean acp remediation surface (C87, C126, C159).

### §A.2 — C87's 8 fixes / 13-transition count (spot-check)

Byte-frozen since verified HELD at C158; spot-checked, nothing concrete surfaced against the §3.2 footnote 8+5=13 count or the C87 items. Not re-litigated (C158 §A.2 verified them against the live SDK `VALID_TRANSITIONS`, which is frozen).

### §A.3 — Standing DESIGN-Q / cross-track carries (re-verified STILL-OPEN)

| Carry | C158 state | C196 state | Live evidence |
|---|---|---|---|
| **M6 / B-M6** — 11 `acp:` predicates in no TTL | STILL-OPEN | **STILL-OPEN** | `grep acp: ontology/*.ttl` = 0. CROSS-TRACK (ontology). |
| **M7** — integer `witnessLevel` vs structured `witness_requirement` | STILL-OPEN | **STILL-OPEN** | Integer L81/L316; structured L329; SDK integer-only. SDK bridge. |
| **B-AGENCY / L1** — `web4_context` proofOfAgency casing/field-set | STILL-OPEN | **STILL-OPEN** | mcp-owned envelope; mcp §4.1/§7.4 frozen. MEDIUM CROSS-TRACK. |
| **B-LEDGERPROOF / C37-5** — §4.2 `ledgerProof` | STILL-OPEN | **STILL-OPEN** | Sole in-doc ledger object; SDK `ProofOfAgency` has no ledger proof. DESIGN-Q. |
| **B8** — ACP discharge not routed through R6 | STILL-OPEN | **STILL-OPEN** | atp-adp §7.1 #5 persists; acp §9.1 MUST list has no R6-discharge item. CROSS-TRACK. |
| **N2** — `maxAtp` "budget"/cumulative vs SDK per-intent-only cap | ROUTED (C158) | **STILL-OPEN (unchanged)** | acp `:174` "against the plan's `resourceCaps.maxAtp` budget" live; SDK `check_atp` (acp.py L213-217) still per-intent-only, raises at L1081; `check_executions` (L219) still defined; SDK frozen ⇒ divergence unchanged. CROSS-TRACK semantics decision. |
| **N4** — hub MCP write tools carry no ACP proof-of-agency | INFO (C158) | **STILL INFO (trigger UNTRIPPED)** | hub write tools still `require_loopback` on the operator plane (mcp.rs L295/L323, :8772 127.0.0.1-only); #520 mailbox is message-delivery, not a write-tool caller path; mcp.rs L446 routes governance to council propose/sign, NOT the MCP write tools. No non-operator agentic callers admitted. Not an acp defect regardless. |
| **B11 / B12 / B13 / B14 / B15** — DESIGN-Q & cross-track batch | STILL-OPEN | **STILL-OPEN** | No mover touched errors §10.1 envelope, SAL witness vocab, or the C75 D0 cluster this interval. |
| **JSONC fences** (C158 §A.5) | INFO-corpus | **INFO-corpus** | Corpus-wide style DESIGN-Q (7 of ~20 core-spec files); operator-gated. |

### §A.4 — Neighbor-drift re-verification (acp's two hard cross-refs at live HEAD)

acp filename-cites exactly two neighbors (whole-file grep). Both resolve correctly:

- **§2.4 `:172` → atp-adp §2.3.** atp-adp L124 = `### 2.3 Discharging (ATP → ADP)`, semantics "ATP discharges through R6 transactions" — accurate. C151's conservation-invariant reword touched atp-adp §7-scope language, **not** §2.3; acp cites only §2.3 discharge ⇒ no drift ([[feedback_snapshot_presence_guard]] applied — the C151 hunk is disjoint from acp's cited surface).
- **§7.2 `:418` → reputation §10.** Resolves (see §A.1). The reputation C194/C195 edits (§5 no-match→None; dropped spec-only `value` key from `analyze_factors`; Coercive/Extractive category in §4) touch **nothing acp consumes**: acp's trust delta is `t3v3Delta` (a dimension→delta map, L161-164), a different shape from reputation's factor structure; acp has zero references to reputation rule categories (`grep coercive|extractive|analyze_factor` in acp = 0).

---

## §B — New / Hardened Findings (this delta)

**Result: ZERO net-new confirmed findings.** The flagship candidate (W4IP-vocabulary inbound drift) was refuted; the SDK/Rust-mirror gate returned NEGATIVE; the internal + neighbor-drift sweep surfaced nothing concrete.

### Summary by severity

| Severity | Count | IDs |
|----------|-------|-----|
| MEDIUM+ | 0 | — |
| LOW | 0 | — |
| INFO | 1 (awareness-only, NOT routed) | see §B.1 |
| **Net-new confirmed** | **0** | second zero-net-new acp delta (C125 was the first; C158 broke it with 4) |
| Carries re-confirmed | 9 groups | §A.3 |

### §B.1 — Flagship candidate REFUTED: W4IP vocabularies do not drift the frozen acp vocabulary (clean-by-layer)

**Candidate (strongest form).** The four W4IP PRs ratified new controlled vocabularies. acp carries its own pre-existing `ACP.Decision` vocabulary `approve | deny | modify` (§2.3 L132, §5.1 L364), an Approval-Gate `Approve`/`Deny` (§3.1 L201, §3.2 L226-232), and a diagram "Law/Scope → Pass/Fail" (§3.1 L189-197). A skeptic argues: (a) the token `deny` now collides with the ratified law-gate `deny`; (b) acp's law gate looks *binary* while the ratified gate is *graded* `allow|warn|deny|escalate`, making acp stale; (c) acp §7.2/§9.1 should now reference the Effector response ladder.

**Refutation (wins on all three).**
1. **Three distinct vocabularies at three layers, deliberately partitioned.** acp `approve|deny|modify` = human/auto **approval of the agent's own proposed intent** (note `modify` + `delegateTo` L364-367, which neither ratified vocab has); hub-law `allow|warn|deny|escalate` = **first-person law/policy gate**; Effector `notice|quarantine|correct|rehabilitate` = **second-person response to another actor's violation**. W4IP N3 itself reserved `warn` for the gate and picked `notice` for the response ladder's first rung — the authors partitioned deliberately, and acp sits cleanly in the gap. The shared token `deny` means "reject the proposed act" in both places — *concordant, not contradictory*; `escalate` is likewise concordant with acp's existing `escalate_to_human` (§10.2 L563).
2. **acp makes NO normative claim of a binary law gate.** §3.1's Pass/Fail is a *diagram flow*; §5.1 L307 is `if not law.allows_trigger(trigger)` — a call to an **abstract oracle**. The only law MUSTs (L298 "Plans must comply with society laws", L485 "Plans MUST comply with society laws") govern *compliance*, not the gate's vocabulary or gradation. A society whose law implements graded `allow|warn|deny|escalate` still exposes `allows_trigger` as its pass/fail projection into ACP. Forcing acp to import a specific law schema's verbs would be a **layering violation** (protocol depending on one law implementation).
3. **C158 self-scoping precedent applies directly.** acp §4.2 L266 self-scopes its MUSTs to "Every MCP call **from ACP**" — C158 used exactly this to rule hub's non-ACP authorization "non-ACP by design." Identically, acp's `approve|deny|modify` binds only within the ACP intent-approval lifecycle; the W4IP vocabularies bind in *other* lifecycles. The Effector is the *downstream* society response if an ACP agent violates (gated by RWOA+S+V+**F**), living in reputation §4 / entity-types §4.8 — a cross-reference from acp would be additive, never required.

**INFO (awareness-only, NOT a remediation carry).** A future editor wanting zero reader ambiguity *could* add a one-line non-normative note that acp's intent-approval `approve|deny|modify` is distinct from the society law-gate `allow|warn|deny|escalate` (which plugs in at the §3.1 Law/Scope-Check step) and the Effector response ladder. This is polish, and adding inter-layer cross-refs risks false coupling — **explicitly do NOT promote to C197.**

### §B.2 — SDK / Rust-mirror gate: NEGATIVE (baselined on current HEAD)

Re-baselined at live HEAD (web4-core moved to 0.4.0 #516 + PR #527 adds `attestation.rs`/birth-cert surface): **no Rust ACP mirror exists.** No `Plan`/`Intent`/`Decision`/`ExecutionRecord` structs in `web4-core/src/` or `hub/`; the only `ProofOfAgency` reference is `web4-core/src/r6.rs` (already routed C156-3, inside excluded B-AGENCY). PR #527's additions are LCT/attestation/birth-certificate, **not** ACP. This reproduces the C158 lens-d negative and matches the C182 (registries) NEGATIVE-gate pattern: acp's only implementation is the Python SDK, which is frozen. No layer-split, no wire-shape divergence to route.

### Load-bearing finder negatives (coverage record)

- **W4IP-vocab lens:** examined acp-framework.md, entity-types §4.8, reputation §4, SOCIETY_SPECIFICATION §7.3, and the W4IP proposal — flagship refuted (§B.1).
- **internal + neighbor-drift lens:** both hard cross-refs resolve (§A.4); §2.4 note's self-refs (`resourceCaps.maxAtp` L76-77, `atpConsumed` §6.2 L382 / §8.2 L469) all resolve; no dangling section refs; no neighbor change (reputation `value`-key drop, Coercive/Extractive category, atp-adp conservation reword, mcp §7.8 mailbox, t3-v3 Talent-no-decay) touches an acp claim.
- **SDK/Rust-mirror gate:** NEGATIVE (§B.2).

---

## Routing Summary (for the C197 turn)

**C197 remediation would be a NO-OP: zero autonomous items routed.** §A is fully clean (three C159 edits HELD, all anchors resolve, all carries STILL-OPEN), and §B produced no LOW-or-above finding. Therefore:

- **AUTONOMOUS — apply in C197:** *(none)*
- **ROUTED — not autonomous (unchanged carries):** N2 (CROSS-TRACK SDK/operator semantics decision — `maxAtp` budget-vs-per-intent); N4 (INFO, hub-adjacent, trigger UNTRIPPED); JSONC fences (INFO-corpus).
- **DESIGN-Q / CROSS-TRACK carries (unchanged, re-verified STILL-OPEN §A.3):** B-LEDGERPROOF/C37-5; B11; B14; B-AGENCY/L1 (mcp-owned); B8 (atp-adp §7.1 #5); B12/B13 (SAL); M6/B-M6 (ontology); B15 (D0 cluster); M7 (SDK bridge).
- **INFO awareness (NOT routed):** the optional §B.1 vocabulary-distinction note.

**Rotation:** since C196 routes zero autonomous items, there is no C197 remediation edit to make. Audit-side rotation advances acp → **presence-protocol** 4th delta (last: C127 3rd-delta / C128 remediation — verify at that turn).

---

## Calibration Note

C196 is a **clean delta on a byte-frozen target** — the expected shape when a file churns slower than the rotation cadence, and the second zero-net-new acp delta (C125 first; C158 broke it with 4 remediation-born findings, all since applied by C159 and re-verified HELD here). The instructive result this interval is **negative and load-bearing**: the largest inbound surface acp has faced (four W4IP governance-vocabulary ratifications) produced **no drift**, because ACP was engineered to abstract the law oracle rather than bake in a decision vocabulary — the same "self-scoping protects the protocol" property C158 found for hub authorization. The corpus's deliberate vocabulary partition (`warn` reserved for the gate, `notice` for the response ladder) is exactly what let a frozen protocol stay correct under a governance-vocabulary expansion.

Two method points confirmed: (1) the **anchor-target re-verification** C159 pre-declared paid off precisely where it could have failed — the entity-types §4.8 Effector insert was the one edit that could have moved N3's §4.7 grant-path, and checking it (rather than trusting the line) confirmed it appended after §4.7 ([[feedback_prior_finding_path_provenance]]). (2) The **SDK/Rust-mirror gate re-baselined on current HEAD** (not trusting the C158 negative) correctly re-confirmed NEGATIVE against a moved target (0.4.0 + PR #527), rather than assuming the prior negative still held ([[feedback_enumeration_and_grep_hypotheses]] — baseline the checker on the live artifact).

---

*C196 complete. NO spec/SDK/schema/vector/.ttl mutation (AUDIT turn). C197 remediation is a NO-OP (zero autonomous items) — audit-side rotation advances acp → presence-protocol 4th delta. ACP lineage C18 → C37 → C86/C87 → C125/C126 → C158/C159 → C196.*
