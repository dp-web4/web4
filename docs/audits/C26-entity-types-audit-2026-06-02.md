# C26 Audit: `entity-types.md` Internal-Consistency RE-Audit

**Date**: 2026-06-02
**Auditor**: Autonomous session (Legion, web4 track) — firing `000050`, LEAD voice
**Document**: `web4-standard/core-spec/entity-types.md` (709 lines, last edited 2026-05-23)
**Methodology**: C-series internal-consistency **delta RE-audit** — same pattern as C23 (SAL), C24 (LCT), C25 (ISP). Two passes: (§A) verify the prior first-pass **C8** audit's remediations still hold + track its deferred carry; (§B) find NEW findings, with emphasis on **drift from sibling specs that moved since the C8 audit (2026-05-22)**. A third **primitive-clustered pass** (per the `auditor-blindspot-pattern`) checks for cross-section contradictions that severity-ordered reading misses.
**Cross-spec authorities re-read this session** (per the cross-doc-overcall hygiene rule — passages re-read, not recalled): `web4-society-authority-law.md` §2.1–§2.3, §3.1 (SAL); `society-roles.md` §1–§2 (role taxonomy); `LCT-linked-context-token.md` ID format (`subject`).

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 1 | H1 |
| MEDIUM | 2 | M1, M2 |
| LOW | 2 | L1, L2 |
| INFO | 1 | INFO1 |
| **NEW Total** | **5 actionable + 1 INFO** | |

**§A result**: All **9 of 9** remediated C8 findings (H1, H2, H3, M1–M4, L1, L2) **HOLD** — zero regression. The C8-L3 deferred-carry (§11↔§3.1 citizen-example redundancy, now §12↔§3.1 after C8's renumbering) **persists** and remains correctly deferred (content-merge, not a structural-consistency fix).

**§B headline**: The new findings are almost entirely **birth-certificate and role-taxonomy drift** — entity-types.md describes the SAME primitives (BirthCertificate, the root-authority role, the LCT-ID format) that SAL / society-roles / LCT-spec also describe, and those sibling specs have been re-audited and edited (C23/C22/C24) since C8. The drift is in entity-types.md's *representations* of shared primitives, not in its unique content (the 15-type taxonomy and energy-metabolism model remain sound and SDK-aligned per C8). **Split: 2 autonomous-actionable, 2 design-Q-coupled, 1 cross-track.** H1 and M1 both intersect already-open design-Q carries (C23-H1 canonical-BirthCertificate-shape; C25-H1 canonical-role-list-home), so they are partially deferrable.

---

## §A. Verification of C8 Remediations (2026-05-22)

C8 found 10 issues (3H/4M/3L), remediated 9, deferred L3. Re-verified against current line numbers:

| C8 ID | Issue | C8 fix | C26 status |
|-------|-------|--------|------------|
| **H1** | Duplicate `### 3.2` | Split → §3.2 Role Revolution / §3.3 Role LCT Structure / §3.4 Role Hierarchy / §3.5 Example Roles | **HOLDS** — current §3.2 (L160), §3.3 (L169), §3.4 (L213), §3.5 (L242) all distinct |
| **H2** | Duplicate `## 5.` / `### 5.1` | Renumber "Entity Interactions" → §6; cascade §6→§14 | **HOLDS** — §5 Lifecycle (L375), §6 Interactions (L443), §7–§14 cascade clean through §14 Future Extensions (L703) |
| **H3** | `### 4.2`/`### 4.3` collision under lifecycle | Renumber → §5.2 Evolution, §5.3 Termination | **HOLDS** — §5.2 (L425), §5.3 (L434); no stray §4.2/§4.3 under §5 |
| **M1** | `## 3.4` wrong heading level | → `###` | **HOLDS** — §3.5 (L242) is `###` |
| **M2** | Missing RFC 2119 notation | Add Notation section | **HOLDS** — Notation present (L5–L7), *enhanced* with RFC 8174 |
| **M3** | Auditor Adjustment Policy misfiled under §4.7 Client | Move to §4.5 Auditor | **HOLDS** — Auditor Adjustment Policy now under §4.5 (L308–L323); Agency Grant under §4.7 (L341–L373) |
| **M4** | Cross-ref to LCT spec for pairing mechanics (not there) | Self-ref to §3.4 Role-Agent Pairing | **HOLDS** — §3.5 L266 now self-refs §3.4; LCT-spec ref scoped to "the LCT structures these pairings reference" |
| **L1** | "blockchain" pseudocode comment | → "immutable ledger" | **HOLDS** — L419 `# Record in immutable ledger` |
| **L2** | "see §3 below" self-reference | → "§3.2 ... above" | **HOLDS** — L252 now "see §3.2, 'The Role Revolution,' above" |
| **L3** | §11↔§3.1 citizen-example redundancy | *Deferred (content-merge)* | **CARRY PERSISTS** — now §12 "Citizen Role Examples" (L627–L648) vs §3.1 (L128–L158). Still non-contradictory redundancy; still correctly deferred. |

**Conclusion**: zero C8 regression. The renumbering cascade (the bulk of C8's work) is fully intact one re-audit cycle later.

---

## §B. NEW Findings

### H1 — Three-way Birth-Certificate divergence; §3.1/§5.1 "SAL-compliant" claims over-state alignment

**Lines**: §3.1 JSON-LD (L140–L158), §5.1 pseudocode (L393–L423), heading L377; cross-spec: SAL §2.2 (L44–L60).

**Issue**: entity-types.md carries **two** birth-certificate representations, both flagged "(SAL-compliant)", and they diverge from **each other** and from SAL's **canonical** §2.2 `Web4BirthCertificate`:

| Field concept | SAL §2.2 (canonical) | entity-types §3.1 JSON-LD | entity-types §5.1 pseudocode |
|---|---|---|---|
| initial rights | `rights` | `initialRights` | *(absent)* |
| initial obligations | `obligations` | `initialResponsibilities` | *(absent)* |
| law oracle | `lawOracle` | `lawOracle` | *(absent)* |
| law version | `lawVersion` | `lawVersion` | *(absent)* |
| genesis block | `genesisBlock` | `genesisBlock` | *(absent)* |
| ledger proof | *(not in canonical)* | `ledgerProof` | *(absent)* |
| parent | *(not in canonical)* | `parentEntity` | `parent_entity` |
| witnesses | `witnesses` (array) | `witnesses` (array) | `birth_witness` (singular key) |
| naming convention | camelCase JSON-LD | camelCase JSON-LD | **snake_case** |

Three concrete problems:
1. **§3.1 field-name drift from SAL canonical**: `initialRights`/`initialResponsibilities` vs SAL's `rights`/`obligations`. Both are typed `"Web4BirthCertificate"`, so an implementation populating the §3.1 shape produces an object that **fails SAL §2.2 schema validation** — yet §3.1 is labeled "(SAL-compliant)". This is the concrete, field-level realization of the **C23-M1 anchor** ("technically-false SAL-compliant claim").
2. **§5.1 pseudocode is not SAL-compliant** despite its heading "(SAL-compliant)": SAL §2.1 (normative MUST) requires the birth-certificate object to include issuer society LCT, **law-oracle digest**, witnesses, timestamp, **genesis block reference**, and **initial rights/responsibilities**. The §5.1 `birth_cert` dict has only `entity_lct, citizen_role, context, birth_timestamp, parent_entity, birth_witness` — it **omits law-oracle digest, genesis block, and rights/responsibilities**, and adds a non-canonical `context` field.
3. **Internal §3.1↔§5.1 inconsistency**: camelCase vs snake_case, `witnesses` vs `birth_witness`, and disjoint field sets for the same object within one document.

**Impact**: An implementer cannot tell which of the three shapes is authoritative; following entity-types.md (either form) yields a certificate that does not satisfy SAL's normative §2.1/§2.2. This is the document's single most consequential consistency gap.

**Remediation split**:
- **Autonomous-actionable** (does not require resolving the open design-Q): align §3.1's `initialRights`/`initialResponsibilities` to SAL canonical `rights`/`obligations` (or add an explicit note that §3.1 is a SUPERSET adding `ledgerProof`/`parentEntity`/`initial*` and is therefore *SAL-extending*, not "SAL-compliant"); and qualify the §5.1 heading so the pseudocode is described as "illustrative, abbreviated — see §3.1 / SAL §2.2 for the normative shape" rather than "(SAL-compliant)".
- **DESIGN-Q-coupled**: the authoritative field set (does `ledgerProof`/`parentEntity` belong in canonical SAL §2.2, or are they entity-types extensions?) is the **open C23-H1 "canonical BirthCertificate shape" design-Q**. The naming-convention question (camelCase JSON-LD vs snake_case SDK) is the open **snake/camel cluster**. The full reconciliation should defer to those; the autonomous half above is safe to apply now.

---

### M1 — "Authority Role" semantics drift (scoped vs root) + unreconciled §3.5 "Sovereign" / §4 "Authority" naming

**Lines**: §4.2 (L279–L284); §3.4 hierarchy (L222); §3.5 table (L248–L262); cross-spec: SAL §3.1 (L72), society-roles §2.1 Sovereign (L53).

**Issue**: Two coupled role-taxonomy inconsistencies:
1. **Semantics drift on "Authority Role"**: entity-types §4.2 describes the Authority role as **scoped delegation** ("Scoped delegation powers (finance, safety, membership)", "Can create sub-authorities with limited scope"). SAL §3.1 (L72) describes the Authority Role LCT as the **"root of delegation tree."** Root-of-tree and a finance/safety/membership-scoped delegate are different positions in the authority graph; the same term names both across the two specs.
2. **Unreconciled naming within entity-types.md**: §3.5's example-roles table and §3.4's hierarchy use **"Sovereign"** (a `society-roles.md` §2.1 term) and never "Authority"; §4 enumerates **"Authority"** (the SAL term) and never "Sovereign". The document never states whether its §4.2 "Authority Role" is the same entity as the "Sovereign" listed in §3.5, a scoped sub-authority beneath it, or a synonym. society-roles.md §2.1 makes "Sovereign" the final/root authority and treats scoped powers separately — so the cleanest reading is that entity-types §4.2's *scoped* "Authority" is **not** the root, which makes its omission of "Sovereign" from §4 a gap.

**Impact**: A reader mapping entity-types.md roles to society-roles.md / SAL cannot determine the authority hierarchy's apex from this document; "Authority" is ambiguous between root and scoped-delegate.

**Remediation split**:
- **Autonomous-actionable**: add a one-line reconciling note in §4.2 clarifying that "Authority Role" here denotes *scoped* delegation (finance/safety/membership) beneath the society's root authority (`society-roles.md` "Sovereign" / SAL §3.1 root), with a cross-ref — OR, if the doc intends §4.2 to be the root, align its description to SAL §3.1.
- **DESIGN-Q note**: which spec is the canonical home of the role *names* (society-roles "Sovereign" vs SAL "Authority Role") is part of the open **C25-H1 canonical-role-list-home design-Q**. Defer the naming canonicalization there; the §4.2 scope clarification is safe now.

---

### M2 — Policy LCT format `policy:<name>:<version>:<hash>` diverges from the doc's own `lct:web4:*` convention and the LCT-spec `did:web4:*` subject form

**Lines**: §13.2 (L667); cross-spec: LCT-linked-context-token.md `subject` = `did:web4:key:z6Mk...` (L65, L595).

**Issue**: §13.2 gives the Policy entity's "LCT Format" as `policy:<name>:<version>:<hash>`. Everywhere else in entity-types.md, identifiers use the `lct:web4:*` namespace (`lct:web4:entity:...` L49/L146, `lct:web4:role:...` L174, `lct:web4:society:...` etc.). The LCT spec itself uses a third form for the LCT `subject` field: `did:web4:key:z6Mk...`. So the Policy LCT identifier is written in a form that matches **neither** the rest of this document **nor** the LCT spec.

**Impact**: Three coexisting LCT-identifier styles (`policy:*`, `lct:web4:*`, `did:web4:*`) with no stated mapping. A consumer parsing Policy LCT IDs would need a special-case grammar.

**Remediation**: **Cross-track** — this is a facet of the open **C24-H1 LCT-ID-format divergence design-Q** (the 4-way LCT-ID divergence already tracked across LCT spec, SDK, vectors). The Policy `policy:<name>:<version>:<hash>` form likely originates from `docs/history/design_decisions/POLICY-ENTITY-REPOSITIONING.md`; resolving it belongs with the broader LCT-ID canonicalization, not a unilateral entity-types.md edit. Flag and carry; do **not** self-resolve.

---

### L1 — §4.1 "Society Role" conflates the Society *entity type* with a *role*

**Lines**: §4.1 (L272–L277); cross-ref: §2.1 taxonomy (L23), society-roles.md (root role = Sovereign/Authority, no "Society role").

**Issue**: §4 is titled "SAL-Specific Roles", and §4.1 "Society Role" then describes the **Society entity type's** capabilities (issues citizenship, maintains a Law Oracle, operates a ledger, fractal membership) — these are properties of the Society *entity type* (§2.1), not a *role that an entity fills*. society-roles.md has no "Society role"; the society's apex *role* is Sovereign/Authority. The other §4.x entries (Authority, Law Oracle, Witness, Auditor, Agent, Client) are genuine fillable roles; §4.1 is the odd one out.

**Impact**: Minor; mild category error that could mislead a reader into treating "Society" as a fillable role parallel to "Auditor".

**Remediation**: **Autonomous-actionable** — reframe §4.1 as "Society (entity-type capabilities relevant to SAL roles)" or move its content to a §4 preamble, distinguishing the Society *entity type* from the *roles* it hosts.

---

### L2 — §4's seven subsections coincide in count with society-roles' seven base-mandatory roles but are a different set (reader-confusion / design-Q intersection)

**Lines**: §4.1–§4.7 (L272–L373); cross-spec: society-roles.md §2 "these seven roles" (L51).

**Issue**: entity-types §4 has exactly seven subsections (Society, Authority, Law Oracle, Witness, Auditor, Agent, Client). society-roles.md §2 normatively defines exactly **seven base-mandatory roles** (Sovereign, Law Oracle, Policy-Entity, Treasurer, Administrator, Archivist, Citizen). The two sevens **overlap only on "Law Oracle"** and are otherwise disjoint sets selected on different axes (SAL-specific subset vs base-mandatory governance set). The numeric coincidence invites a reader to equate "the 7 roles in entity-types §4" with "the 7 base-mandatory roles" — they are not the same seven.

**Impact**: Low but real confusion risk; directly intersects the open **C25-H1 "canonical home of the 7-role list" design-Q** (SOCIETY_SPEC §1.2.5 vs ISP §6.2 vs SDK `BASE_MANDATORY_ROLES`). entity-types §4 is a *third* "seven roles" surface that the canonicalization must account for.

**Remediation**: **Design-Q-coupled / cross-track** — add to the C25-H1 carry the fact that entity-types §4's seven SAL-specific roles are an independent "seven" that must be explicitly distinguished from the seven base-mandatory roles when the canonical role-list home is decided. A one-line clarifying note in §4's preamble ("these are the SAL-specific roles, a different set from the seven base-mandatory roles in society-roles.md §2") is the safe autonomous interim.

---

### INFO1 — entity-types.md uses `lct:web4:*` throughout while the LCT spec canonical `subject` is `did:web4:key:*`

**Lines**: pervasive (`lct:web4:entity:...`, `lct:web4:role:...`, etc.); cross-spec LCT-spec L65/L595.

**Note**: Informational, not a standalone finding — this is the document-wide manifestation of the same LCT-ID-format question as M2 (the open C24-H1 design-Q). Recorded so a future LCT-ID canonicalization sweep knows entity-types.md is one of the specs using the `lct:web4:*` style. No action proposed in isolation.

---

## §C. Auditor-Blindspot Pass (primitive-clustered)

Per the `auditor-blindspot-pattern`, after the severity-ordered pass above, the document was re-read clustered by **primitive** rather than by section, to surface contradictions that span sections:

- **BirthCertificate primitive** (§3.1, §5.1 pseudocode, §3.1 characteristics, §6.2.1 citizen rights, §12.2, vs SAL §2.2): the 3-way divergence is **H1**. The "permanent / cannot be revoked" property is stated consistently in §3.1 (L137), §3.4 (L235), §6.2.1 (L462) — **no contradiction there** (clean).
- **Root-authority primitive** (§3.4 hierarchy "Authority", §3.5 table "Sovereign", §4.2 "Authority Role", SAL §3.1 root, society-roles §2.1 Sovereign): the scoped-vs-root + naming tangle is **M1**.
- **LCT-identifier primitive** (`lct:web4:*` pervasive, `policy:*` §13.2, `did:web4:*` in LCT spec): **M2 + INFO1**.
- **Rights/obligations primitive** (§3.1 `initialRights`/`initialResponsibilities`, §6.2.1 "Exist, interact, accumulate reputation", SAL `rights`/`obligations`): the field-name half is folded into **H1**; the §6.2.1 prose list is consistent with §3.1's values (clean).

The clustered pass surfaced no contradiction beyond H1/M1/M2 — i.e., the new findings are concentrated in three shared primitives, all three of which are primitives that sibling specs co-define and that have open design-Q carries. This is consistent with the C25 observation that post-triangle-closure drift is concentrated at shared-primitive boundaries.

---

## §D. Disposition Summary

| ID | Severity | Disposition | Coupled carry |
|----|----------|-------------|---------------|
| H1 | HIGH | **Autonomous (partial)** — align §3.1 field names + qualify §5.1 heading; **defer** canonical-shape | C23-H1 (BirthCertificate shape); snake/camel cluster |
| M1 | MEDIUM | **Autonomous (partial)** — §4.2 scope-clarification note; **defer** name canonicalization | C25-H1 (canonical role-list home) |
| M2 | MEDIUM | **Cross-track** — do not self-resolve | C24-H1 (LCT-ID format) |
| L1 | LOW | **Autonomous** — reframe §4.1 Society-as-entity-type vs role | — |
| L2 | LOW | **Autonomous (interim note)** — distinguish §4's seven from base-mandatory seven | C25-H1 |
| INFO1 | INFO | Record only | C24-H1 |

**Autonomous-actionable for the C26 remediation session**: H1 (field-name alignment + §5.1 heading qualification), M1 (§4.2 scope note), L1 (§4.1 reframe), L2 (interim distinguishing note). **Deferred**: H1 canonical-shape, M1 naming, M2/INFO1 (LCT-ID), all riding existing C23-H1 / C24-H1 / C25-H1 design-Q carries — no new design-Q is opened by this audit.

---

## Cross-Reference to Prior Audits

| Audit | Spec | Findings | Status |
|-------|------|----------|--------|
| C8 | entity-types.md (first pass) | 10 (3H/4M/3L) | 9/10 remediated; L3 deferred |
| C21 | society-metabolic-states.md | — | merged |
| C22 | SOCIETY_SPECIFICATION.md | 11 | merged |
| C23 | web4-society-authority-law.md (SAL) | 7 new + 8 carried | merged (H1 = canonical BirthCertificate design-Q, open) |
| C24 | LCT-linked-context-token.md | 12 new | merged (H1 = LCT-ID 4-way divergence, open) |
| C25 | inter-society-protocol.md | 6 new + 1 carried | merged (H1 = canonical 7-role-list home, open) |
| **C26** | **entity-types.md (RE-audit)** | **5 new + 1 INFO; 9/9 C8 remediations hold; C8-L3 carry persists** | **this audit** |

**Note on overlap discipline**: H1, M1, M2, L2 each intersect an already-open design-Q from C23/C24/C25 rather than opening new ones. This is expected at this stage — entity-types.md is the taxonomy hub that *references* the BirthCertificate, role, and LCT-ID primitives those specs define, so its drift is downstream of theirs. The audit is honest that only the field-name/heading/framing halves are net-new autonomous work; the substantive divergences await the upstream design-Q resolutions.
