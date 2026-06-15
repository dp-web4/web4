# C58: web4-society-authority-law.md (SAL) Delta Re-Audit

**Date**: 2026-06-15
**Auditor**: Autonomous session (legion-web4-20260615-000047)
**Document**: `web4-standard/core-spec/web4-society-authority-law.md` (399 lines, HEAD `a3fee0e1`)
**Prior audit**: C23 (`docs/audits/C23-society-authority-law-audit-2026-05-30.md`, 2026-05-30)
**Prior remediation**: PR #254 (`4eb691e8`) — resolved 3 autonomous-actionable C23 findings (M2, L1, I1)

**Framing**: This is the **first delta re-audit of SAL** (C23 was itself a delta re-audit of C16). The SAL file is **byte-identical since its C23 remediation #254** (`git log 4eb691e8..HEAD -- <file>` is empty). Per the C56 lesson (when a file is byte-identical to its remediation, §A shifts from diff-regression to **remediation-completeness** — audit the remediation's own site-enumeration — plus **mirror-drift check** — re-verify every mirror the audited findings touch, since SDK strings and sister-doc paragraphs move even when the target file does not). §A below applies both. NET-NEW C58 IDs are reserved for §B findings absent from the C23 HELD/DEFERRED/DEMOTED ledger.

**Counts**:
- **§A prior-finding ledger**: C23-rem 3/3 HELD; C23-M1 now RESOLVED (mirror); C23-L2 prose-reconciled (mirror); C16-M6 partially closed (mirror); 4 design-Q + 6 C16-carries re-verified OPEN.
- **C58 new IDs**: see §B (post-verify count below).

---

## §A. Prior-Finding Verification (live evidence at HEAD `a3fee0e1`)

### A.1 — C23 remediation #254 HELD (3/3) + site-enumeration complete

| C23 ID | Remediation | Live site | Status |
|--------|-------------|-----------|--------|
| M2 | §3.1 add 4th "Immutable Record" bullet | L75 `- An **Immutable Record** binding (per §3.4).` | **HELD** — single committed site, complete |
| L1 | SAL-side reciprocal cross-refs | §3.1 L77 + §3.6 L138 both `See also: SOCIETY_SPECIFICATION.md` | **HELD** — both committed sites present |
| I1 | date header bump | L3 `Last Updated: 2026-05-31` | **HELD** |

**Site-enumeration completeness (C56 method)**: #254's three edits were each single-site and are each present. #254 explicitly deferred the SAL-internal/sister-doc residuals (M1, the §1.4→§3.6 SPEC-side back-link, all design-Q) — none of those were in #254's committed scope, so #254 is *complete with respect to its own committed site-list*. The residuals are tracked below, not charged against #254.

### A.2 — Mirror movement since C23 (positive; caught by per-file provenance re-check)

- **C23-M1 → RESOLVED.** `entity-types.md` L160-167 no longer uses `initialRights`/`initialResponsibilities`. It now affirms `rights`/`obligations` as the SAL-canonical keys *and* explicitly cross-references the open C23-H1 ("canonical BirthCertificate shape") design question, framing its own `ledgerProof`/`parentEntity` as a SAL-aligned superset. C23-M1 (sister-doc deprecated-name leftover) is **CLOSED** by a later entity-types remediation.
- **C23-L2 → prose-reconciled (SDK gap remains).** `SOCIETY_SPECIFICATION.md` §1.2.2 Note (L39) was substantially expanded since C23: it now explicitly legitimizes SAL §3.4's witness-attestation as "a standalone record class in its own right," resolving the C23-L2 witness-as-event-category *contradiction* at the prose level. The remaining half — SDK `LedgerEventType` has no `AUDIT` type for SAL §3.4's "auditor adjustments" — persists and overlaps C16-M5.
- **C16-M6 → partially closed.** SDK `federation.py:242-266` now implements `appeal_path` (+ `has_negative_adjustment`/validity check). The **cool-down period** half of SAL §5.5 L221 (`Negative adjustments MUST include appeal path and cool-down period`) is still unrepresented in the SDK. C16-M6 narrows to cool-down-only.
- **C23-H1 leg (b) shifted.** `LCT-linked-context-token.md` now marks `birth_context` + `genesis_block_hash` as RECOMMENDED (L280-286), where C23 quoted them as plain inline fields. The 3-way design-Q is unchanged in substance; the divergence map needs a refresh (folded into §B/H1-refresh if surfaced).

### A.3 — Still OPEN (re-verified live)

| Item | Live evidence | Class |
|------|---------------|-------|
| C23-H1 birth-cert 3-way | SAL §2.2 L44-60 unchanged (`Web4BirthCertificate`, camelCase); LCT-spec leg shifted (A.2); SDK `lct.py:145-164` unchanged (snake_case dataclass) | DESIGN-Q |
| C23-M3 Rest queue-vs-refuse | `metabolic.py:413` `return state == MetabolicState.ACTIVE` (Rest→False=refuse); docstring L412 still says "Rest: queued"; SMS §2.2 L59 "queued"; SAL §3.6 L141 "Rest MAY queue" | DESIGN-Q |
| C23-L2 ledger taxonomy (SDK half) | `society.py:89-96` `LedgerEventType`=5 (no AUDIT); SAL §3.4 L109 = 6 categories | DESIGN-Q |
| C16-H1-remainder (3 codes) | `W4_ERR_LEDGER_WRITE`/`W4_ERR_AUDIT_EVIDENCE`/`W4_ERR_LAW_CONFLICT` absent from BOTH `errors.py` AND `errors.md` (broader than C23's "SDK only" framing) | cross-track |
| C16-M1 role taxonomy 3-way | `federation.RoleType`=5, `role.SocietyRole`=9, `society-roles.md`=7 base-mandatory | DESIGN-Q |
| C16-M3 r6Bindings | absent from SDK (grep empty) | DESIGN-Q |
| C16-M4 ledger ops / C16-M5 event-topic+AUDIT | SAL §3.4 ops/topics not mirrored in SDK | DESIGN-Q / cross-track |
| C16-M8 sal-ontology.ttl | **MISSING**; `web4-core-ontology.ttl` L195 + L219-220 dangling-reference it + undefined `Web4BirthCertificate` class | cross-track (subordinate-ontology cluster) |
| L1 residual | `SOCIETY_SPEC` §1.4 has no back-link to SAL §3.6 (SAL→SPEC side present L138); note: §1.2↔§3.1 is now fully reciprocal — SPEC L59 added SAL §3.1 back-ref since C23 | LOW (cross-track, SPEC-side) |

**Subordinate-ontology cluster (BC-C23-3 / BC#7)**: C58 does NOT increment the cluster. The missing `sal-ontology.ttl` + dangling `Web4BirthCertificate` remain the C16-M8 carry. Cluster stays operator-engagement-class.

---

## §B. C58 NEW Findings

**Method**: 10-lens finder workflow (`wf_67fe82c4-18f`, 30 agents) — lenses: spec-internal, sdk-align, sister-society-spec, sister-metabolic-lct, wire-json, rdf-ontology, error-taxonomy, role-taxonomy, r6-mapping, primitive-cluster. Refute-by-default per-candidate verifier (every candidate independently re-read at cited lines; finders fed the full HELD/DEFERRED/DEMOTED list). **30 raw → 23 confirmed → 15 distinct after synthesis dedup (0 HIGH / 6 MED / 7 LOW / 2 INFO).** 7 refuted (all duplicated a tracked carry or were materially overstated — see §B.refuted). Every MED was independently re-verified by the auditor via Bash before write (evidence inline).

**Severity calibration** (anchored to C16-C23 precedent): MED = field/enum/shape divergence converging on a normative MUST, OR internal framing contradiction on a primitive, OR spec-vs-spec on a primitive. LOW = doc-hygiene / non-executable example / asymmetric-xref / taxonomy-naming. INFO = cosmetic/lexical with no live consumer.

### Birth-certificate cluster (§2.1 normative prose ↔ §2.2 "Canonical JSON-LD")

**B1 (MED) — §2.1 mandates a "law-oracle digest"; §2.2 canonical JSON carries no hash field.** §2.1 L41 (under the L39 `implementations MUST:` header) lists "law-oracle **digest**" as a required Birth Certificate member. The §2.2 canonical JSON-LD (L45-59) has NO digest/hash field — only `lawOracle` (an LCT pointer, L52) + `lawVersion: "v1.2.0"` (a human version string, L53). A version string is not a content hash and is exactly the downgrade/replay vector §4.2 L174 guards against (`Entities MUST cache and pin the hash ... to detect downgrade/replay`). So the canonical example implementers copy satisfies neither §2.1's digest MUST nor §4.2's hash-pin MUST. The law-pin field is further named **four ways** across the doc: "law-oracle digest" (§2.1 L41), `lawVersion` (§2.2 L53), `hash` (§4.1 L164, §3.4 L117), `lawHash` (§6 L247, §8 L293/296, §11 L331). *(Merges 3 confirmed candidates: birthcert-prose-vs-json-digest, birthcert-law-pin-digest-vs-version, sal-2.1-law-oracle-digest-vs-2.2-reference.)* **Class: autonomous** (intra-doc; but the *direction* — add a `lawHash` to §2.2 vs soften §2.1 — touches the C23-H1 canonical-shape design-Q; recommend resolving alongside H1).

**B2 (LOW) — §2.1 prose says "responsibilities", §2.2 key is `obligations`.** §2.1 L41 "initial rights/**responsibilities**" vs §2.2 L57-58 keys `"rights"`/`"obligations"`. A reader cannot derive the wire-key name from the prose. **Class: autonomous** (align §2.1 prose to `obligations`).

**B14 (LOW) — §2.2 witness LCT ids are malformed.** §2.2 L55 `"witnesses": ["lct:web4:witness1", "lct:web4:witness2"]` collapses the type segment; every other id in the same example uses `lct:web4:<type>:<id>` (L49-52: `entity`, `role:citizen`, `society`, `oracle:law`), and the mirror LCT-spec witnesses are segmented (`lct:web4:witness:1...`). **Class: autonomous** (fix example ids to `lct:web4:witness:1` / `:2`). *(Note: the 2-witness count itself is subsumed by C23-H1 — see refuted.)*

### Witness/conformance contradictions

**B3 (LOW) — §7 heading mis-ordering.** L261 `### 7.2 SPARQL Examples` is immediately followed by L262 `### 7.1.1 Additional Required Triples (Witness/Auditor/Ledger)`; the actual SPARQL blocks only begin at L270. Numbering runs 7.1 → 7.2 → 7.1.1; the five MUST-maintain triples (hasWitness/hasAuditor/recordsOn/adjustedBy/attestedBy) sit orphaned under the "SPARQL Examples" header instead of under §7.1 Required Triples. *(Merges 3 candidates.)* **Class: autonomous** (renumber §7.1.1 → place before §7.2).

**B11 (LOW) — §6 closing MUST binds `citizen` into the transcript, but r6-framework provides no carrier field.** §6 L247 `Execution engines MUST bind the current lawHash, society, and citizen pairing into the signed action transcript.` `lawHash` + `society` are carried by the r6 Rules object (r6-framework §1.1 L34-35) → they land in the transcript. But the genesis `citizen` pairing has no field anywhere in r6-framework (Role object §1.2 carries only `actor`/`roleLCT`; Result object carries none). The §6 MUST mandates binding a value r6 defines no slot for. **Class: cross-track** (r6-framework add a field, or SAL relax to "via the §7.1 `web4:pairedWith` triple").

**B-birth-cosign (MED) — §2.3 makes birth-cert witness signatures MAY; §8 makes them MUST.** §2.3 L64 `Birth certificates MUST be signed by the society's binding authority key and MAY include witness signatures.` vs §8 L291 `SAL-critical events (birth, ...) MUST carry witness co-signatures meeting quorum` (reinforced §3.4 L123). The birth certificate IS stored as the SAL-critical birth event (§2.1 L42, §3.4 L109), so the two sections set incompatible conformance levels for witness co-signing of the same primitive. **Class: autonomous** (reconcile §2.3 to §8's MUST, or scope §8's "birth" to the ledger append vs the cert object). *(id: birth-witness-cosign-may-vs-must.)*

### Role taxonomy — mandatory-vs-optional (sharpens C16-M1)

**B7 (MED) — SAL makes Authority / Witness / Auditor conformance-MUST; society-roles.md tiers all three as Optional.** SAL: §12.1 L340 MUST `Bind to a Society with Authority and Law Oracle`; §7.1 L256 MUST-maintain `web4:hasAuthority`; §5.2/§5.4/§5.5 normative MUSTs; §11 L329 Discovery MUST expose `hasWitness`/`hasAuditor`. society-roles.md: 7 base-mandatory roles (Sovereign, Law-Oracle, Policy-Entity, Treasurer, Administrator, Archivist, Citizen) — **Authority is not among them** and Witness/Auditor are explicitly §4 **Optional** ("MAY define when needs warrant"). A society conformant to society-roles.md's mandatory tier fails SAL's role MUSTs. *(Merges sal-authority-mandatory-vs-optional + witness-auditor-mandatory-vs-optional.)* **Class: design-q** — distinct, sharper facet of C16-M1 (which was framed as 5-vs-7+2 *count* divergence; this is the *conformance-level* contradiction). Requires taxonomy reconciliation.

### Spec-vs-spec on citizenship primitive

**B8 (MED) — SAL: genesis Citizen pairing "cannot be revoked"; SOCIETY_SPEC: citizenship `terminate` → Terminated, with no genesis carve-out.** SAL §5.1 L181 `Permanent birth pairing; cannot be revoked` (+ §2.1 L40 "immutable birth pairing"; corroborated by entity-types.md §3.4 L244). SOCIETY_SPECIFICATION.md §4.2.1 L281 action-to-status: `suspend` → Suspended, `terminate` → Terminated for citizenship generically, explicitly noting "`terminate` replaces the `revoke` action of earlier drafts." No exception is stated for the genesis Citizen role. The two specs disagree on whether genesis citizenship is terminable. **Class: design-q** (normative: is genesis citizenship truly non-terminable, and if so does SOCIETY_SPEC §4.2.1 need a carve-out?).

### Metabolic-state divergences (distinct from C23-M3 queue-vs-refuse)

**B10 (MED) — §3.6 says dormant states SHOULD *defer* citizenship; SMS makes a new-citizen request a *wake trigger* for Hibernation.** SAL §3.6 L141 `dormant states SHOULD defer`. But SOCIETY_METABOLIC_STATES.md §2.4 L91 / §3.1 L184 / §4.1 L229 make `new_citizen` an explicit Hibernation→Active **wake** trigger (`wake_on: ["new_citizen", ...]`). A new-citizen request that SAL says to defer is the same event SMS says wakes the society. **Class: design-q** (which semantic wins — defer or wake?).

**B9 (LOW) — SDK `DORMANT_STATES` includes REST; SAL §3.6 treats Rest as non-dormant.** SAL §3.6 L140-141 enumerates dormant states as exactly four (Sleep, Hibernation, Torpor, Estivation) and treats Rest separately ("Rest MAY queue" vs "dormant states SHOULD defer"). SDK `metabolic.py:374-376` `DORMANT_STATES` frozenset includes `REST` (so `is_dormant(REST)` is True). Classification divergence on "dormant" membership, distinct from C23-M3. **Class: design-q/cross-track** (align SAL §3.6 or the SDK set).

### Error taxonomy

**B15 (MED) — §9 maps "Expired delegation" to `W4_ERR_BINDING_REVOKED`; the correct code `W4_ERR_AUTHZ_EXPIRED` already exists.** SAL §9 L309 `| Expired delegation | W4_ERR_BINDING_REVOKED |`. Taxonomy: `W4_ERR_BINDING_REVOKED` = "Binding Revoked / Referenced binding has been **revoked**" (HTTP 410, errors.md:47) — an explicit revocation, not a time-based expiry. `W4_ERR_AUTHZ_EXPIRED` = "Authorization **Expired** / ...has expired" (401, errors.md:73) is the semantically correct code. **Class: autonomous** (intra-SAL: change the §9 mapping to `W4_ERR_AUTHZ_EXPIRED`).

### Ontology — chapter-law.ttl (reframes C16-M8)

**B6 (MED) — the one existing SAL-domain ontology, `chapter-law.ttl`, diverges from canonical `web4:` namespace and uses `law:hash` where SAL's SPARQL binds `web4:hash`.** A partial SAL ontology **does exist** at `web4-standard/ontology/chapter-law.ttl` (its header cites `web4-society-authority-law.md §4`). Two divergences: **(a)** L1 declares `@prefix web4: <https://web4.io/ontology/>` (trailing **slash**), whereas SAL §3.3 L87 and `web4-core-ontology.ttl` L1/L24 ("Canonical namespace") both use `<https://web4.io/ontology#>` (**hash**) — every `web4:` term in chapter-law.ttl resolves to a different IRI; an RDF merge / SPARQL across the graphs treats them as disjoint. **(b)** chapter-law.ttl L97 defines the law-dataset hash predicate as `law:hash`, but SAL §7.2 L275 binds `web4:hash ?hash` on the law object — the query never matches the ontology's predicate. *(Merges web4hash-vs-lawhash-namespace + chapter-law-web4-prefix-base-divergence.)* **Class: cross-track** — updates the C16-M8 subordinate-ontology carry: the gap is not purely "sal-ontology.ttl missing" — a partial ontology exists under a different name AND a different namespace base. Per BC-C23-3 this does NOT increment the cluster count; it sharpens the existing C16-M8 carry.

### Self-consistency hygiene (SPARQL examples + cross-refs)

**B4 (LOW) — §7.1 "Required Triples" omits `web4:publishes`, `web4:hash`, `web4:scope` that the spec's own queries/data depend on.** The §7.2 canonical query "Find a society's active law hash" uses `web4:publishes` + `web4:hash`, and §3.3 L101 uses `web4:scope`, but neither §7.1 nor §7.1.1 lists them. An implementation maintaining exactly the stated required set cannot answer the spec's own canonical query. **Class: autonomous** (add the three edges to §7.1/§7.1.1).

**B5 (LOW) — §7.2 SPARQL examples are non-executable (2 facets).** (a) Neither SPARQL block declares `PREFIX web4: <...>` (nor `lct:`), unlike the house style in sibling mrh-tensors.md where every block opens with the PREFIX lines → a parser rejects the undeclared prefix. (b) The queries reference subjects as full IRIs `<lct:societyRoot>` / `<lct:entity>` / `<lct:roleCitizen>` (scheme `lct:`), but the §3.3 example data writes them as CURIEs `lct:societyRoot` which under `@prefix lct: <https://web4.io/lct/>` expand to `https://web4.io/lct/societyRoot` — different IRIs, so the example ASK/SELECT would never match the example triples. *(Merges sparql-missing-prefix-decl + sparql-iri-vs-curie-mismatch.)* **Class: autonomous** (add PREFIX decls; make subject notation consistent with §3.3 data).

**B12 (INFO) — §3.6 L144 calls §6 "the R6 evaluation pipeline"; §6 is a static mapping table.** §6 is titled "SAL ↔ R6 Mapping (Normative)" and defines no ordered pipeline/precondition sequence. The cross-ref's "precondition of the R6 evaluation pipeline" has no concrete target in SAL. **Class: autonomous** (reword to reference the R6 action grammar / r6-framework pipeline rather than §6).

**B13 (INFO) — citizen base capability is `"exist"` (§2.2 wire token) vs "presence" (§5.1 prose).** §2.2 L57 `"rights": ["exist", ...]` vs §5.1 L182 "Grants base capabilities: **presence**, ...". "presence" is the project's load-bearing canonical term; §5.1 is descriptive prose (no live token consumer), so INFO. **Class: autonomous** (align vocabulary; the other two pairs — interact/interaction, accumulate_reputation/accumulation — are trivial morphological variants).

### §B.refuted (7 — recorded per BC#9 overcall discipline)

| id | why refuted |
|----|-------------|
| sdk-birthcert-omits-sal-must-fields | duplicate of C23-H1 (its evidence table already records lawOracle/lawVersion/rights/obligations as ABSENT from SDK shape) |
| bc-example-two-witnesses-violates-quorum-3 | the 2-vs-3 witness count is subsumed under the C23-H1 deferred birth-cert-shape DESIGN-Q (H1 prints the divergent witness arrays) |
| sal-policy-entity-absent | duplicate of C16-M1 role-taxonomy carry (Policy-Entity-absent is one symptom of the 5-vs-7 mismatch) |
| sal-section5-header-omits-witness-auditor | duplicate of C16-M1 (the §5 header is the C16-anchored site) |
| sdk-cross-society-law-conflict-vs-sal-law-conflict | `CROSS_SOCIETY_LAW_CONFLICT` (horizontal peer, mcp §7.6) ≠ SAL `LAW_CONFLICT` (vertical inheritance) — distinct error classes; base gap already tracked as C16-H1-remainder |
| sal9-law-hash-mismatch-downgrade-narrowing | SAL's own model (§4.2 L174, §8 L296) frames law-hash-mismatch AS a downgrade-attack signal → the `W4_ERR_PROTO_DOWNGRADE` mapping is consistent, not a narrowing |
| quorum-scaling-miscite-3.1 | §3.6 "(§3.1)" anchors the *term* Quorum Policy (defined at §3.1 L74); the scaling behavior is sourced from SMS (cited at §3.6 L138); §8 "meeting quorum" is abstract, no numeric collision |

---

## §C. Autonomous / Design-Q / Cross-Track Split (routing for C59)

**Autonomous-actionable (9)** — intra-SAL edits, no cross-doc decision required:
- **B2** §2.1 "responsibilities" → "obligations" (match §2.2 key)
- **B3** §7 renumber: move §7.1.1 before §7.2
- **B4** §7.1/§7.1.1 add `web4:publishes`, `web4:hash`, `web4:scope` to required triples
- **B5** §7.2 SPARQL: add PREFIX decls + reconcile IRI/CURIE subject notation with §3.3
- **B12** §3.6 L144 reword "R6 evaluation pipeline (§6)" → R6 action grammar
- **B13** §2.2/§5.1 align `exist`/`presence` citizen base-capability vocabulary
- **B14** §2.2 fix malformed witness ids → `lct:web4:witness:1` / `:2`
- **B15** §9 "Expired delegation" → `W4_ERR_AUTHZ_EXPIRED` (correct code already in taxonomy)
- **birth-witness-cosign** (§2.3 MAY vs §8 MUST) — reconcile to §8's MUST (or scope §8 "birth" to ledger append)
- **B1** §2.1-digest-vs-§2.2-JSON — autonomous in principle (add a `lawHash` field to §2.2 or soften §2.1), but **recommend pairing with C23-H1** so the §2.2 shape is fixed once. *(Listed here AND flagged for H1.)*

**Design-Q / operator-engagement (4)**:
- **B7** role conformance-MUST (Authority/Witness/Auditor) vs society-roles.md Optional tier — sharpens C16-M1
- **B8** genesis-citizen permanent (SAL) vs terminable (SOCIETY_SPEC §4.2.1) — primitive contradiction
- **B9** Rest dormant-membership (SDK `DORMANT_STATES` ⊇ REST) vs SAL §3.6 non-dormant
- **B10** §3.6 dormant-defer vs SMS new_citizen wake-trigger — semantic contradiction

**Cross-track (2)**:
- **B6** chapter-law.ttl namespace/predicate divergence — folds into the **C16-M8 subordinate-ontology cluster** (now reframed: a partial ontology exists but diverges; cluster NOT incremented per BC-C23-3)
- **B11** §6 transcript `citizen`-binding has no r6-framework carrier field

**Carried design-Q / cross-track from §A (unchanged-open):** C23-H1 (birth-cert 3-way), C23-M3 (Rest queue-vs-refuse), C23-L2 SDK-half (no AUDIT LedgerEventType), C16-H1-remainder (3 codes absent from errors.py + errors.md), C16-M1 (role-count taxonomy), C16-M3 (r6Bindings absent from SDK), C16-M4/M5 (ledger ops / event-topic + AUDIT), C16-M6 (cool-down absent; appeal_path now present), C16-M8 (sal ontology — see B6), L1-residual (SOCIETY_SPEC §1.4 → SAL §3.6 back-link absent).

---

## §D. Lessons

1. **Byte-identical-since-remediation → §A shifts to completeness + mirror-drift (C56 method confirmed, again productive).** SAL was untouched since #254, so §A diff-regression would have found nothing. The completeness/mirror pass instead surfaced three *positive* movements invisible to a same-file diff: C23-M1 RESOLVED (entity-types.md fixed by a later remediation), C23-L2 prose-reconciled (SOCIETY_SPEC §1.2.2 Note expanded), C16-M6 partially closed (appeal_path landed). A pure "did the file change?" check reports "no movement" and is wrong on all three.

2. **Mirror-drift cuts both ways — verify the *other* leg even when the audited file is frozen.** C23-H1's LCT-spec leg (b) shifted (`birth_context`/`genesis_block_hash` → RECOMMENDED) with zero SAL edits. A delta-audit that only re-reads the target file would carry a stale divergence map.

3. **Finders surface unknown files — `chapter-law.ttl` (B6).** The rdf-ontology lens found an existing partial SAL ontology that prior SAL audits (C16/C23) never cited — they tracked only the *absent* `sal-ontology.ttl`. The real state (a differently-named ontology with a divergent namespace base) is more useful than the "missing file" carry. Lesson: a finder fed "X is missing" can still discover "X exists under another name, and it's wrong" — feed the absence claim AND let the lens look.

4. **High verifier-survival still needs synthesis dedup (C56 lesson re-confirmed at scale).** 23/30 confirmed, but only 15 distinct: the §7 misorder was found 3× (spec-internal + primitive-cluster ×2), the birthcert-digest 3×. Refute-by-default catches *false* findings; it does NOT collapse *true duplicates* across lenses — that is synthesis-time work.

5. **The "tracked-item" refute filter is essential and load-bearing.** 4 of 7 refutations were "real observation, but duplicates a known carry" (C23-H1 ×2, C16-M1 ×2). Without feeding finders the HELD/DEFERRED list, these would have been mis-counted as net-new, inflating the §B count by ~27%.

6. **Anti-padding held: 0 HIGH is the honest result.** SAL's remaining defects are intra-doc hygiene, taxonomy reconciliation, and spec-vs-spec design questions — none wire-breaking on their own. The most consequential (B1 birth-cert digest, B6 ontology namespace) are MED because they degrade security/interop guarantees but have in-spec detectability or design-Q escape hatches.

---

*End of C58 audit. No remediation patches (BC#7 — findings only). Routing for C59 remediation in §C.*
