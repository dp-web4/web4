# C134: web4-society-authority-law.md (SAL) — Third Delta Re-Audit

**Date**: 2026-07-04
**Auditor**: Autonomous session (legion-web4-20260704-000036)
**Document**: `web4-standard/core-spec/web4-society-authority-law.md` (SAL, 408 lines, HEAD frozen at `0d756773`)
**Prior audit**: C98 (`docs/audits/C98-society-authority-law-audit-2026-06-25.md`, snapshot `9f4a2e09`)
**Prior remediation**: C59 / PR #330 (`0d756773`) — applied all 10 autonomous-actionable C58 findings.

**Lineage**: C16 → C21 → C23 → C58 → C98 → **C134**.

**Rotation note (metabolic remediation slot = no-op)**: Per the fixed-order round-robin, this fire was the **C134 SOCIETY_METABOLIC REMEDIATION slot**. C133 (#447, `70e3ddcc`) found SOCIETY_METABOLIC_STATES fully clean (0 autonomous). With **0 commits merged to origin/main since C133** (`git log 70e3ddcc..origin/main` empty), the remediation slot is a **trivial genuine no-op**: 0 DESIGN-Q answered, 0 metabolic SDK authorizations — nothing merged could have introduced a metabolic autonomous item. Mirroring C93→C94, C131→C132, and C132→C133, the round-robin **advances** to the next-oldest file: SAL. (SAL's own hypothetical C135 remediation slot is likewise pre-determined a no-op by this audit's 0-autonomous result.)

**Framing**: This is the **third delta re-audit of SAL** (C58 = first, C98 = second). SAL is **byte-identical since its C59 remediation #330** — `git diff 0d756773 HEAD -- web4-standard/core-spec/web4-society-authority-law.md` is empty (frozen **19 days**). Every sibling SAL cites is likewise frozen since the C98 snapshot. Per the established frozen-target pattern (C92/C94/C96/C98/C131/C132/C133), §A becomes verification and §B yield is entirely on the **moving corpus-delta surface** and inbound cross-doc carries (per [[feedback_cross_doc_carry_inbound]], [[feedback_snapshot_presence_guard]]).

Per the C56 method (file byte-identical to its remediation), §A shifts from diff-regression to **remediation-completeness** + **mirror-drift re-check** + **bidirectional carry re-verification**. NET-NEW C134 IDs are reserved for §B findings absent from the C58/C98 HELD/DEFERRED/DEMOTED ledger.

**Counts**:
- **§A**: C59-rem **10/10 HELD** (trivially — SAL byte-frozen at the exact HEAD C98 verified, nothing touched it since), 0 regressed, 0 encoding artifacts. **All SAL-cited siblings frozen since C98** → 0 mirror drift. All C58 + C23 + C16 design-Q / cross-track carries **re-verified OPEN** with live evidence.
- **§B**: **0 net-new autonomous defects.** Corpus-delta surface (8 sibling files moved since the C98 snapshot) adversarially verified disjoint from SAL's citation/normative surface — 0 new SAL contradictions. **This is SAL's 2nd consecutive fully-clean delta (C98 + C134).**
- **§C**: routing unchanged (all carries STAND); one carry-**referent** bookkeeping update (chapter-law.ttl → hub-law.ttl rename); C58-B10 re-confirmed two-sided open (both files frozen).

---

## §A. Prior-Finding Verification (live evidence at frozen HEAD `0d756773`)

### A.1 — C59 remediation #330 HELD (10/10)

SAL is **byte-identical** to the HEAD at which C98 verified all 10 C59 edits present-and-unregressed (`git diff 0d756773 HEAD -- <SAL>` empty). No edit could have regressed because no byte changed. The C98 site-table (B2 L41, B3 L264, B4 L260, B5 L275/L288, B12 L144, B13 L57, B14 L55, B15 L318, birth-cosign L64, date L3) stands verbatim. **Regression sweep**: `grep "&#"` over the file → 0 hits (no HTML-entity artifacts). **Site-enumeration completeness (C56)**: #330 complete w.r.t. its committed site-list; design-Q/cross-track residuals tracked in §A.3 / §C, not charged against #330.

### A.2 — Mirror movement since the C98 snapshot (`9f4a2e09`, 2026-06-25)

**Every sibling SAL cites by name is frozen since C98** (`git log 9f4a2e09..HEAD -- <path>` = 0 commits, verified for all):

| SAL-cited sibling | Commits since C98 | Status |
|-------------------|-------------------|--------|
| `SOCIETY_METABOLIC_STATES.md` (§3.6 L138/L140) | 0 | frozen — B10/M3 carries stable |
| `SOCIETY_SPECIFICATION.md` (§1.4 back-ref, L138) | 0 | frozen — L1-residual stable |
| `r6-framework.md` (§3.6 L144, §6 mapping) | 0 | frozen — B11/B12 stable |
| `errors.md` (§9 codes) | 0 | frozen — B15 target + C16-H1-remainder stable |
| `entity-types.md` (§2.2/§5.1 mirror) | 0 | frozen — B13/B14 convergence held |
| `LCT-linked-context-token.md` (birth-cert) | 0 | frozen — C23-H1 stable |

**Zero mirror drift**: since no cited sibling moved, none of the C98 mirror-convergence results (entity-types C65 `presence`/witness-id convergence; errors.md C67 code-retention; LCT-spec C61 `witness_attested`) could have regressed. They stand as verified at C98.

### A.3 — Still OPEN (re-verified live; all targets frozen → carries STAND)

All carries from the C98 §A.3 ledger re-verified OPEN at frozen HEAD. No change in substance. Summary (full detail in C98 §A.3):

| Item | Live status | Class |
|------|-------------|-------|
| C23-H1 birth-cert 3-way (+ B1 digest) | SAL §2.2 camelCase/2-witness vs LCT-spec snake_case ≥3 vs SDK — frozen both sides | DESIGN-Q |
| C23-M3 Rest queue-vs-refuse | SAL §3.6 L141 "MAY queue" vs SDK `metabolic.py` refuse — frozen | DESIGN-Q |
| C23-L2 ledger taxonomy (SDK half) | no AUDIT `LedgerEventType` | DESIGN-Q (overlaps C16-M5) |
| C16-H1-remainder (3 codes) | `W4_ERR_LEDGER_WRITE`/`_AUDIT_EVIDENCE`/`_LAW_CONFLICT` absent from errors.md (frozen) + errors.py | cross-track |
| C16-M1 role taxonomy (+ B7 facet) | federation=5 / SocietyRole=9 / society-roles=7 | DESIGN-Q |
| C16-M3 r6Bindings | absent from SDK | DESIGN-Q |
| C16-M4/M5 ledger ops / event-topic+AUDIT | SAL §3.4 not mirrored in SDK | DESIGN-Q / cross-track |
| C16-M6 cool-down | SAL §5.5 cool-down half unrepresented in SDK `federation.py` | cross-track |
| **C16-M8 / B6 ontology** | **referent RENAMED** `chapter-law.ttl`→`hub-law.ttl` (#412); divergence substance UNCHANGED (see §B) | cross-track (subordinate-ontology cluster, BC-C23-3 — NOT incremented) |
| B7 role conformance-MUST vs Optional | SAL §12.1/§7.1/§11 MUST vs society-roles.md Optional | DESIGN-Q |
| B8 genesis-citizen terminability | SAL §5.1 L181 + entity-types §3.4 vs SOCIETY_SPEC §4.2.1 terminate | DESIGN-Q |
| B9 Rest dormant-membership | SDK `DORMANT_STATES` ⊇ REST vs SAL §3.6 | DESIGN-Q / cross-track |
| **B10 dormant-defer vs new_citizen wake** | SAL §3.6 L141 vs SMS §4.1 L229 — **both frozen** → two-sided contradiction stands | DESIGN-Q |
| B11 §6 `citizen`-binding | r6-framework no carrier field | cross-track |
| B1 birthcert digest-vs-version | SAL §2.1 digest MUST vs §2.2 `lawVersion` — paired w/ C23-H1 | paired-with-H1 |
| L1-residual | SOCIETY_SPEC §1.4 no back-link to SAL §3.6 (frozen) | LOW (SPEC-side) |

**Subordinate-ontology cluster (BC-C23-3 / BC#7)**: NOT incremented. See §B for the rename's effect on the carry referent.

---

## §B. C134 NEW Findings

**Method**: Frozen-target — SAL byte-identical since C59, every cited sibling frozen since C98. Per the frozen-target discipline (the explicit lesson of C92/C94/C96/C98/C131/C132/C133), §B was scoped tightly to the **moving corpus-delta surface** — the spec/ontology files that changed since the C98 snapshot `9f4a2e09` — plus inbound cross-doc carries. No finder pass was run over unchanged SAL prose (the mechanism that manufactures findings on a clean frozen target).

**Moving surface since C98** (`git diff --stat 9f4a2e09..HEAD -- web4-standard/core-spec/** web4-standard/ontology/**`), with disjointness verdict against SAL's citation/normative surface:

| Moved file (Δ) | Change | SAL cites it? | Verdict |
|----------------|--------|---------------|---------|
| `atp-adp-cycle.md` (+16, C119 #420 `e99b419e`) | §7.1 MUST#6 scope note: entity-role value → T3/V3; society-aggregate → non-tensor rollup | No (SAL cites no atp-adp anchor) | **REFUTED — consistent** (see B.1) |
| `hub-law.ttl` + `hub-law-schema.md` (RENAME, #412 `7c1f86dc`) | `chapter-law`→`hub-law` title/desc prose only | No (SAL cites neither ttl nor schema) | **REFUTED — carry referent update only** (see B.2) |
| `reputation-computation.md` (+13, C123) | internal reputation remediation (NEW-1 ⊥ SDK) | No | **REFUTED — disjoint** |
| `acp-framework.md` (Δ8) | internal acp edits | No | **REFUTED — disjoint** |
| `security-framework.md` (2 lines) | handshake §6.0.5/§9 cross-ref anchor precision | No (SAL cites "Security" spec generically, not this line) | **REFUTED — disjoint** |
| `t3-v3-tensors.md` (2 lines) | atp-adp conservation cross-ref anchor precision | No (SAL cites "T3/V3" spec generically) | **REFUTED — disjoint** |
| `mcp-protocol.md` (2 lines) | R7-witnessing MUST scoping to high-consequence | No | **REFUTED — disjoint** |

**Result: 0 net-new autonomous defects.** All moved siblings are disjoint from SAL's citation surface (SAL cites only the six frozen siblings in §A.2). The two moved files with any conceptual adjacency to SAL (atp-adp, hub-law.ttl) were adversarially verified below and both REFUTED.

**This is SAL's 2nd consecutive fully-clean delta (C98 + C134)** and the corpus-level frozen-target 0-autonomous streak's continuation. Reported as the honest outcome, not padded; no finding demoted-to-INFO to fill the section.

### B.1 — atp-adp C119 §7.1 MUST#6 scope note ⊥ SAL value surface (REFUTED, consistent by construction)

C119 (`e99b419e`, #420) added a scope note to atp-adp §7.1 MUST#6: *entity-level value MUST be tracked through T3/V3 tensors; society-level aggregates MAY use non-tensor rollup accounting* (the same carve-out pattern as the §3.3 demurrage note).

SAL **does** carry a value surface — but it is **entirely the entity-role, within-role-context leg** that MUST#6 governs, so the clarification is consistent, not contradictory:
- **§10 "T3/V3 Implications"** (L326-333): Witness Temperament, Auditor Training/Temperament, Citizen **V3 Validity** — all "computed **within role context**". These are exactly the *entity-role* tensor legs MUST#6 mandates.
- **§7/§4 `aggregate_v3(v3, deltas.v3, law.recency_weights)`** (L229): the auditor aggregating a **citizen's** V3 deltas — an *entity-role, in-context* aggregation, NOT a society-level rollup.
- **`LAW-ATP-LIMIT` norm** (L165, `selector:"r6.resource.atp","op":"<=","value":100`): an *example* law norm imposing an ATP resource **cap** — a resource-metering example, not value-tracking, and orthogonal to MUST#6.

Disjointness proven by **absence of the carved-out surface**: SAL has **no society-level aggregate value channel** (grep for `aggregate` yields only the auditor's in-role `aggregate_v3`; no `aggregate_value`, no Level-4/5 society-rollup). The MUST#6 carve-out addresses exactly the society-aggregate rollup that SAL does not contain. SAL's value surface is on the governed side of MUST#6, so C119's clarification **reinforces** SAL §10's within-role-context framing rather than contradicting it. **REFUTED.**

*(This mirrors the C133 metabolic-side verdict on the same C119 hunk — there, disjoint from metabolic's zero-value-surface; here, consistent with SAL's entity-role-only value surface. Two independent audits, same moved hunk, both clean by disjointness-of-surface.)*

### B.2 — chapter-law.ttl → hub-law.ttl RENAME (#412) — C16-M8/B6 substance UNCHANGED, referent updated

The lockstep sweep #412 (`7c1f86dc`, "rename: chapter law → hub law", decided 2026-06-11) renamed `web4-standard/ontology/chapter-law.ttl` → `hub-law.ttl` and `chapter-law-schema.md` → `hub-law-schema.md`. Content diff (verified): **title/description prose only** ("Chapter Law Ontology" → "Hub Law Ontology"). The **C16-M8/B6 divergence substance is unchanged**:
- `hub-law.ttl` still declares `@prefix web4: <https://web4.io/ontology/>` — **trailing-slash** namespace (L1) — vs SAL §7.2 `PREFIX web4: <https://web4.io/ontology#>` (**hash** fragment, L275/L288).
- `hub-law.ttl` still uses the `law:hash` predicate (L97, namespace `…/ontology/law/`) vs SAL §7.2 `web4:hash` (L261/L281).
- `sal-ontology.ttl` **still ABSENT** from canonical `web4-standard/ontology/` (dir holds `hub-law.ttl`, no `sal-ontology.ttl`; a copy exists only in `forum/nova/web4-sal-bundle/`, not canonical).

SAL cites **neither** the ttl nor the schema doc by name (`grep chapter-law|hub-law|law-schema` over SAL → 0 hits), so the rename creates **no stale citation** in SAL. The only effect on the audit ledger is **bookkeeping**: the C16-M8/B6 carry's *referent filename* updates `chapter-law.ttl` → `hub-law.ttl`. This is a carry-referent update, **not** a net-new finding and **not** a resolution. The operator-engagement-class carry STANDS (subordinate-ontology cluster BC-C23-3, NOT incremented). **REFUTED as net-new.**

### §B inbound cross-doc carry (re-verified, NOT net-new)

**C58-B10** (new-citizen DEFER-vs-WAKE): SAL §3.6 L141 "dormant states SHOULD defer" citizenship issuance vs SMS §4.1 L229 `wake_on: ["new_citizen",...]`. **Both SAL and SOCIETY_METABOLIC_STATES.md frozen since C98** (0 commits each) → the two-sided contradiction stands unchanged. Routes to the operator bundle (couples B9 + M5). Not self-applied.

---

## §C. Autonomous / Design-Q / Cross-Track Split (routing for the hypothetical C135 remediation)

**Autonomous-actionable (this turn): NONE.** Frozen target, 0 net-new. The hypothetical C135 SAL remediation slot is a **NO-OP** (as C99 was).

**Standing design-Q / cross-track carries (all STAND, route as ONE operator decision memo — none gate a normal AUDIT turn):**
- **Design-Q**: C23-H1 (birth-cert 3-way + B1 digest), C23-M3 (Rest queue-vs-refuse), C23-L2-SDK (no AUDIT LedgerEventType), C16-M1 (role taxonomy + B7 facet), C16-M3 (r6Bindings), B8 (genesis-citizen terminable?), B9 (Rest dormant-membership), **B10 (dormant-defer vs new_citizen wake — two-sided, couples B9 + M5)**.
- **Cross-track**: C16-H1-remainder (3 codes absent from errors.md + errors.py), C16-M4/M5 (ledger ops/topics → SDK), C16-M6 (cool-down → SDK `federation.py`), **C16-M8 / B6 (`hub-law.ttl` [renamed from chapter-law.ttl] trailing-slash namespace + `law:hash` vs SAL §7.2 `web4:hash`/`ontology#`; `sal-ontology.ttl` still absent → ontology-track)**, B11 (§6 citizen-binding → r6-framework), L1-residual (SOCIETY_SPEC §1.4 back-link → SPEC-side).

**Positive/neutral movements logged (no action needed):** atp-adp C119 MUST#6 scope note is consistent with SAL §10's within-role-context value framing; hub-law rename is title-prose only (substance unchanged).

---

## §D. Lessons

1. **Disjointness by ABSENCE of surface generalizes across audits of the same moved hunk.** C133 refuted atp-adp C119's MUST#6 carve-out against metabolic by grepping metabolic for value/V3 and finding ZERO hits (disjoint by construction). C134 hits the *inverse* case: SAL **does** have a value surface, but grepping shows it is *entirely* the entity-role within-context leg MUST#6 governs, with **no** society-aggregate rollup channel — the exact surface the carve-out carves out. Same hunk, two targets, both clean — one by having zero value-surface, one by having only the *governed* value-surface. The refute-by-absence discipline (grep the target for the moved concept, reason from what's present/absent) is stronger than a prose argument and reusable across sibling audits.

2. **A rename touches the carry REFERENT, not the carry SUBSTANCE — check both, conflate neither.** #412 renamed chapter-law.ttl→hub-law.ttl. The reflex is either "resolved!" (wrong — the divergence bytes didn't move) or "net-new!" (wrong — nothing normative changed). The correct read: the C16-M8/B6 carry's *filename referent* updates, its *substance* (trailing-slash ns + law:hash) is byte-identical, and SAL doesn't cite the file anyway so there's zero SAL-side impact. Diff the rename content (title-only) before assigning any verdict. [[feedback_snapshot_presence_guard]]

3. **The frozen-target pattern now holds across 7 consecutive wraps (C92/C94/C96/C98/C131/C132/C133) + C134 = 8.** Files churn slower than the +2-per-file cadence, so every wrap hits a frozen target with all cited siblings also frozen. The stable shape: §A = trivial remediation-hold (byte-identical at the verified HEAD) + mirror-frozen confirmation + carry re-verification; §B = tightly-scoped moving-corpus verification returning 0 autonomous. SAL's 2nd consecutive fully-clean delta (C98 + C134) matches metabolic's (C96 + C133) and dictionary's (C94 + C132) and SOCIETY_SPEC's (C92 + C131).

4. **A no-op remediation slot with 0 intervening commits is the strongest possible no-op.** C134-as-metabolic-remediation had not merely "0 autonomous items found upstream" but "0 commits merged at all since the audit" — nothing *could* have introduced work. Step-(a) is satisfied by construction. Rotation advances (4th instance: C93→C94, C131→C132, C132→C133, C134→SAL).

---

*End of C134 audit. No remediation patches (BC#7 — findings only). All carries route to the standing operator decision memo (one referent update: chapter-law.ttl→hub-law.ttl); C135 SAL remediation slot is a NO-OP. Next rotation target: next-oldest = `LCT-linked-context-token.md` (last audited C60/C61) for its 2nd-delta (≈C136).*
