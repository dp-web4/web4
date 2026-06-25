# C98: web4-society-authority-law.md (SAL) — Second Delta Re-Audit

**Date**: 2026-06-25
**Auditor**: Autonomous session (legion-web4-20260625-060010)
**Document**: `web4-standard/core-spec/web4-society-authority-law.md` (SAL, 408 lines, HEAD frozen at `0d756773`)
**Prior audit**: C58 (`docs/audits/C58-society-authority-law-audit-2026-06-15.md`, snapshot `a3fee0e1`)
**Prior remediation**: C59 / PR #330 (`0d756773`) — applied all 10 autonomous-actionable C58 findings (B2, B3, B4, B5, B12, B13, B14, B15, birth-witness-cosign, date)

**Lineage**: C16 → C21 → C23 → C58 → **C98**.

**Framing**: This is the **second delta re-audit of SAL** (C58 was the first). The SAL file is **byte-identical since its C59 remediation #330** — `git log 0d756773..HEAD -- web4-standard/core-spec/web4-society-authority-law.md` is empty (frozen 10 days). This is the **4th consecutive frozen target** in the rotation (after C92 SOCIETY_SPEC, C94 dictionary, C96 SOCIETY_METABOLIC), all of which returned 0 autonomous defects — the steady-state pattern: *files churn slower than audit cadence, so wraps hit frozen targets, §A becomes verification, and §B yield is entirely on the moving corpus-delta surface and inbound cross-doc carries* (per [[feedback_cross_doc_carry_inbound]]).

Per the C56 method (file byte-identical to its remediation), §A shifts from diff-regression to **remediation-completeness** + **mirror-drift re-check** (re-verify every mirror the audited findings touch — SDK strings, sister-doc paragraphs, ontology — since those move even when SAL does not) + **bidirectional carry re-verification** (a prior design-Q may RESOLVE or HARDEN downstream, leaving a stale note). NET-NEW C98 IDs are reserved for §B findings absent from the C58 HELD/DEFERRED/DEMOTED ledger.

**Counts**:
- **§A**: C59-rem **10/10 HELD**, 0 regressed, 0 encoding artifacts. Mirror movement: **2 positive convergences** (entity-types C65, errors.md C67 alignment), **1 detail-only sibling shift** (LCT-spec C61). All C58 + C23 + C16 design-Q / cross-track carries **re-verified OPEN**.
- **§B**: **0 net-new autonomous defects.** Corpus-delta surface (3 moved siblings) adversarially verified — 0 new SAL contradictions. Positive frozen-target result.
- **§C**: routing unchanged (all carries STAND); C58-B10 re-confirmed two-sided open per policy-review condition.

---

## §A. Prior-Finding Verification (live evidence at frozen HEAD `0d756773`)

### A.1 — C59 remediation #330 HELD (10/10) + site-enumeration complete

Each C59 edit was single-site; each is present and unregressed at HEAD:

| C58 ID | Remediation | Live site | Status |
|--------|-------------|-----------|--------|
| B2 | §2.1 prose "responsibilities" → "obligations" | L41 `initial rights/obligations` | **HELD** |
| B3 | §7 renumber — §7.1.1 now precedes §7.2 | L264 `### 7.1.1`, L271 `### 7.2 SPARQL Examples` | **HELD** |
| B4 | §7.1 add `web4:publishes`/`web4:hash`/`web4:scope` | L260 `web4:publishes (law oracle → law dataset)` (+ hash, scope) | **HELD** |
| B5 | §7.2 SPARQL PREFIX decls + IRI→CURIE | L275/L288 `PREFIX web4: <https://web4.io/ontology#>`; subjects `lct:societyRoot` (CURIE) | **HELD** |
| B12 | §3.6 reword "R6 evaluation pipeline" → R6 action grammar | L144 `precondition of R6 action evaluation (per the R6 action grammar in r6-framework.md; see §6...)` | **HELD** |
| B13 | §2.2 `exist` → `presence` | L57 `"rights": ["presence", "interact", "accumulate_reputation"]` | **HELD** |
| B14 | §2.2 malformed witness ids segmented | L55 `["lct:web4:witness:1", "lct:web4:witness:2"]` | **HELD** |
| B15 | §9 "Expired delegation" → `W4_ERR_AUTHZ_EXPIRED` | L318 `\| Expired delegation \| W4_ERR_AUTHZ_EXPIRED \|` | **HELD** (target code present errors.md:73) |
| birth-cosign | §2.3 MAY → MUST witness co-signatures | L64 `... **MUST** carry witness co-signatures meeting the society's quorum policy.` | **HELD** |
| date | header bump | L3 `Last Updated: 2026-06-15` | **HELD** |

**Regression sweep**: `grep "&#"` over the file → 0 hits (no HTML-entity encoding artifacts, the failure mode tracked since C51). #330's `+20/-11` introduced no collateral changes.

**Site-enumeration completeness (C56 method)**: #330's edits were each single-site and present. #330 explicitly ROUTED (did not touch) the design-Q (B7/B8/B9/B10), cross-track (B6/B11), and B1 (birthcert digest — paired with C23-H1). None of those were in #330's committed scope, so #330 is **complete with respect to its own committed site-list**. Residuals tracked in §A.3 / §C, not charged against #330.

### A.2 — Mirror movement since C58 snapshot (per-file provenance re-check)

Three SAL mirrors were remediated **after** the C58 snapshot `a3fee0e1` (2026-06-14 22:03) — verified via `git merge-base --is-ancestor`. Each re-checked for drift against current SAL:

- **entity-types.md (C65 #344, 2026-06-16) → CONVERGENCE (positive).** entity-types §3.2 birth-cert example changed `rights: ["exist",...]` → `["presence",...]` (L153) and "Provides base rights: Exist" → "Presence" (L493). This is the **same B13 fix SAL received at C59** — the citizen base-capability vocabulary is now **corpus-consistent** across SAL §2.2 + §5.1 and entity-types §3.2 + prose. entity-types also already carries the segmented `lct:web4:witness:1/:2` ids (L153), matching SAL's C59 **B14** fix. Two independent C58 SAL findings (B13, B14) and the parallel C64/C65 entity-types remediation converged the corpus rather than diverging it. *(Mirrors the C58 pattern where C23-M1 was RESOLVED by a later entity-types remediation.)*
- **errors.md (C67 #347, 2026-06-17) → ALIGNED (no SAL impact).** C67 remediated 3 unrelated C66 findings. Adversarially verified: **every error code SAL §9 cites** (`W4_ERR_BINDING_INVALID`, `W4_ERR_PROTO_DOWNGRADE`, `W4_ERR_WITNESS_QUORUM`, `W4_ERR_AUTHZ_SCOPE`, `W4_ERR_AUTHZ_EXPIRED`) **remains present and unremapped**. C67's §1 rescope explicitly retains SAL under the `W4_ERR_*` convention ("Society/Authority Law (`web4-society-authority-law.md` §9)… follow the `W4_ERR_*` convention"). No SAL §9 mapping is invalidated; B15's target `W4_ERR_AUTHZ_EXPIRED` confirmed at errors.md:73.
- **LCT-linked-context-token.md (C61 #338, 2026-06-15) → DETAIL-ONLY shift (no new contradiction).** C61 added a `witness_attested(lct, witness)` MUST-definition (verify a COSE_Sign1 existence attestation), reworded L508 ("multiple independent witnesses" → "a quorum (≥3) of witnesses"), and downgraded witness-society-membership enforcement to "implementation-defined." Adversarially verified consistent with SAL §2.3 L64 + §5.4 L198 (both already mandate witness co-signing). **Critically: the LCT-spec ≥3 birth-witness floor is NOT new** — it was present at the C58 snapshot (L206 "minimum 3", L283 "Array of ≥3", L300, L311 table, L604 `assert ... >= 3`); C61 only reworded the *prose* leg. The 2-witness SAL §2.2 example vs ≥3 LCT floor was already weighed and **refuted at C58** as subsumed under C23-H1 (birth-cert-shape design-Q). It remains a C23-H1 facet, **not a net-new finding** — re-surfacing it would be a re-audit overcall.

### A.3 — Still OPEN (re-verified live; all targets frozen → carries STAND)

| Item | Live evidence | Class |
|------|---------------|-------|
| C23-H1 birth-cert 3-way | SAL §2.2 L45-58 `Web4BirthCertificate` camelCase, key `witnesses`, 2-witness example; LCT-spec `birth_witnesses` snake_case ≥3 floor (+ C61 `witness_attested`); SDK `lct.py` snake_case dataclass — divergence-map detail grew (LCT side) but substance unchanged | DESIGN-Q |
| C23-M3 Rest queue-vs-refuse | SAL §3.6 L141 "Rest MAY queue"; SDK `metabolic.py` Rest→refuse; SMS "queued" — all frozen since C59 | DESIGN-Q |
| C23-L2 ledger taxonomy (SDK half) | SDK `LedgerEventType` has no AUDIT type for SAL §3.4's auditor-adjustment category | DESIGN-Q (overlaps C16-M5) |
| **C16-H1-remainder (3 codes)** | `W4_ERR_LEDGER_WRITE` / `W4_ERR_AUDIT_EVIDENCE` / `W4_ERR_LAW_CONFLICT` **confirmed ABSENT from errors.md** (C67 #347 did NOT add them) AND `errors.py` | cross-track |
| C16-M1 role taxonomy | `federation.RoleType`=5, `role.SocietyRole`=9, `society-roles.md`=7 base-mandatory — sharpened by B7 conformance-level facet | DESIGN-Q |
| C16-M3 r6Bindings | absent from SDK | DESIGN-Q |
| C16-M4/M5 ledger ops / event-topic+AUDIT | SAL §3.4 ops/topics not mirrored in SDK | DESIGN-Q / cross-track |
| C16-M6 cool-down | SDK `federation.py` has `appeal_path`; SAL §5.5 cool-down half still unrepresented | cross-track |
| C16-M8 / B6 ontology | `chapter-law.ttl` frozen — `web4:` trailing-slash namespace + `law:hash` predicate diverge from SAL §7.2 `web4:hash`; `sal-ontology.ttl` still absent | cross-track (subordinate-ontology cluster, NOT incremented per BC-C23-3) |
| B7 role conformance-MUST vs Optional | SAL §12.1/§7.1/§11 MUST Authority/Witness/Auditor; society-roles.md tiers them Optional | DESIGN-Q |
| B8 genesis-citizen terminability | SAL §5.1 L181 "cannot be revoked" + entity-types §3.4 L244 "permanent and cannot be terminated" (re-confirmed) vs SOCIETY_SPEC §4.2.1 `terminate`→Terminated, no carve-out | DESIGN-Q |
| B9 Rest dormant-membership | SDK `DORMANT_STATES` ⊇ REST vs SAL §3.6 Rest-non-dormant | DESIGN-Q / cross-track |
| **B10 dormant-defer vs new_citizen wake** | SAL §3.6 L141 "dormant states SHOULD defer" vs SMS §3.1 L184 + §4.1 L229 `wake_on: ["new_citizen",...]` — **both files frozen since C59; two-sided contradiction stands** (elevated from metabolic side at C96) | DESIGN-Q |
| B11 §6 `citizen`-binding | r6-framework has no carrier field for the genesis citizen pairing in the signed transcript | cross-track |
| B1 birthcert digest-vs-version | SAL §2.1 "law-oracle digest" MUST vs §2.2 carries only `lawVersion` string — paired with C23-H1 | autonomous-in-principle / paired-with-H1 |
| L1-residual | SOCIETY_SPEC §1.4 has no back-link to SAL §3.6 (SAL→SPEC side present L138) | LOW (cross-track, SPEC-side) |

**Subordinate-ontology cluster (BC-C23-3 / BC#7)**: C98 does NOT increment the cluster. `chapter-law.ttl` namespace/predicate divergence + missing `sal-ontology.ttl` remain the C16-M8/B6 carry, operator-engagement-class.

---

## §B. C98 NEW Findings

**Method**: Frozen-target — SAL byte-identical since C59. Per policy-review condition 1, §B was scoped tightly to the **corpus-delta surface** (the 3 sibling docs remediated after the C58 snapshot: LCT-spec C61, entity-types C65, errors.md C67) plus inbound cross-doc carries. No finder pass was run over unchanged SAL prose (that is the mechanism that manufactures findings on a clean frozen target — the explicit lesson of C92/C94/C96).

A single **adversarial delta-verifier** (refute-by-default) inspected all three sibling diffs against current SAL prose, fed the full HELD/DEFERRED/DEMOTED carry ledger, asking only: *did any ADDED sibling line create a NEW normative contradiction with SAL not already tracked?*

**Result: 0 net-new autonomous defects.** All three siblings REFUTED cleanly:
- **LCT-spec C61** — `witness_attested` MUST + ≥3 reword are consistent with SAL §2.3/§5.4; the 2-vs-3 witness count and `witnesses`/`birth_witnesses` name are pre-existing C23-H1 facets (≥3 floor predates C58). REFUTED.
- **entity-types C65** — `presence` + colon-witness-ids move entity-types *toward* SAL (convergence, B13/B14). REFUTED.
- **errors.md C67** — no code SAL §9 relies on was remapped/removed; rescope retains SAL. REFUTED.

This is the **4th consecutive frozen-target 0-autonomous result** (C92, C94, C96, C98). It is reported as the honest outcome, not padded — consistent with the anti-padding discipline ("a clean frozen result stands, don't manufacture findings"). No findings were demoted-to-INFO to fill the section.

### §B inbound cross-doc carry (re-verified, NOT net-new)

**C58-B10** (new-citizen DEFER-vs-WAKE) was elevated to a two-sided DESIGN-Q from the metabolic side at C96. Per policy-review condition 2, re-verified from SAL's side this turn: SAL §3.6 L141 "dormant states SHOULD defer" citizenship issuance vs SMS §3.1 L184 / §4.1 L229 making `new_citizen` an explicit Hibernation→Active **wake** trigger. **Both files frozen since C59** → the contradiction stands unchanged. **Routes to the operator bundle** (couples to M5 "define dormant precisely" + B9 Rest-membership). Not self-applied.

---

## §C. Autonomous / Design-Q / Cross-Track Split (routing for the hypothetical C99 remediation)

**Autonomous-actionable (this turn): NONE.** Frozen target, 0 net-new. The hypothetical C99 metabolic-style remediation slot for SAL is a **NO-OP** (as C93/C95/C97 were for their frozen targets).

**Standing design-Q / cross-track carries (all STAND, route as ONE operator decision memo — none gate a normal AUDIT turn):**
- **Design-Q**: C23-H1 (birth-cert 3-way + B1 digest), C23-M3 (Rest queue-vs-refuse), C23-L2-SDK (no AUDIT LedgerEventType), C16-M1 (role taxonomy + B7 conformance-level facet), C16-M3 (r6Bindings), B8 (genesis-citizen terminable?), B9 (Rest dormant-membership), **B10 (dormant-defer vs new_citizen wake — now two-sided, couples B9 + M5)**.
- **Cross-track**: C16-H1-remainder (3 codes absent from errors.md + errors.py — re-confirmed C67 did not add them; route to errors-track + SDK-track), C16-M4/M5 (ledger ops/topics → SDK), C16-M6 (cool-down → SDK `federation.py`), C16-M8 / B6 (`chapter-law.ttl` namespace+predicate / `sal-ontology.ttl` absent → ontology-track), B11 (§6 citizen-binding → r6-framework), L1-residual (SOCIETY_SPEC §1.4 back-link → SPEC-side).

**Positive movements logged (no action needed):** entity-types C65 converged on `presence` + colon-witness-ids (B13/B14 corpus-wide consistent); errors.md C67 retained all SAL §9 codes.

---

## §D. Lessons

1. **"Was it present at the prior snapshot?" is the load-bearing guard against re-surfacing a refuted finding.** The LCT-spec ≥3 birth-witness floor looked like fresh corpus-delta (C61 reworded the prose at L508 to read "a quorum (≥3)"). The disciplined check — `git show a3fee0e1:<file> | grep ≥3` — showed the floor (L206/283/300/311/604) was already there at C58, where the 2-vs-3 contradiction was **explicitly refuted** as subsumed under C23-H1. Without that check, C98 would have re-reported a known-and-dismissed finding as net-new, inflating the count and contradicting C58's own ledger. **Reword ≠ new normative content.**

2. **Frozen-target §B yield is asymmetric: it surfaces CONVERGENCE as readily as divergence.** The moving corpus didn't add a SAL defect — it *removed* latent ones. entity-types C65 independently landed the same `presence` + segmented-witness-id fixes SAL got at C59, so two specs that could have drifted instead converged. A delta-audit that only hunts for new contradictions misses that the corpus is self-healing; logging the convergence is as much the audit's job as logging a gap (mirrors the C58 C23-M1-RESOLVED note).

3. **The frozen-target pattern is now confirmed across 4 consecutive wraps (C92/C94/C96/C98).** Files churn slower than the +2-per-file rotation cadence, so every wrap hits a frozen target. The stable shape: §A = remediation-completeness + mirror-drift + bidirectional carries (all of SAL's value this turn); §B = tightly-scoped corpus-delta verification returning 0 autonomous. The honest 0 is the result, not a failure to find work.

4. **Adversarial refute-by-default scales down cleanly.** With only 3 moved siblings and a frozen target, a single delta-verifier (vs C58's 30-agent finder workflow) was proportionate. Proportionality is set by the *moving surface*, not by audit ambition — a 30-agent sweep over unchanged SAL prose would have been pure padding.

---

*End of C98 audit. No remediation patches (BC#7 — findings only). All carries route to the standing operator decision memo; C99 SAL remediation slot is a NO-OP. Next rotation target: next-oldest = `LCT-linked-context-token.md` (last audited C60/C61) for its 2nd-delta (≈C100).*
