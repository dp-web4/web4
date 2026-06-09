# C40 Audit: `mrh-tensors.md` Delta Re-Audit

**Date**: 2026-06-09
**Auditor**: Autonomous session (Legion, web4 track) — exit #168, AUDIT turn
**Document**: `web4-standard/core-spec/mrh-tensors.md` (373 lines)
**Prior pass**: C10 — `docs/audits/mrh-tensors-internal-consistency-2026-05-23.md` (9 findings: H1, M1–M4, L1–L4)
**Methodology**: Delta re-audit via multi-agent **refute-by-default WORKFLOW** (1 carry-verifier + 6 dimension finders → adversarial verification, default-to-refute). 37 agents.
**Reference materials**: SDK `implementation/sdk/web4/mrh.py` (564L; `trust.py` zone model), ontology `ontology/web4-core-ontology.ttl` + `ontology/t3v3-ontology.ttl`, sibling spec `t3-v3-tensors.md` (next audit target, C42).

---

## Summary

| | Count |
|---|---|
| **§A** C10 carries verified | 9 (7 HELD-REMEDIATED, 1 PARTIAL, 1 STILL-OPEN, **0 REGRESSED**) |
| **§B** raw candidate findings | 30 |
| §B CONFIRMED | 21 (incl. 3 no-defect clean-bill verifications) |
| §B DEFLATED | 4 |
| §B REFUTED | 5 |

**§B confirmed-defect severity** (excluding the 3 no-defect verifications): 0 HIGH / 5 MEDIUM / 9 LOW / 4 INFO = **18 actionable**.

The file is in **good health**. The C10 remediation (#217/#221 era) held cleanly with zero regressions — a notable contrast to the [[feedback_remediation_introduced_regression]] pattern seen in C36/C38. The new findings cluster into two themes: (1) **one genuine algorithm bug** in the §4.2 illustrative pseudocode, and (2) a **systemic ontology-vocabulary divergence** — the spec's illustrative Turtle/SPARQL use ~12 predicates and 2 classes that are undefined in the canonical ontology. The latter is consolidated below as a single operator DESIGN-Q rather than 6 scattered carries, per [[feedback_cross_cutting_consolidation_audit]].

---

## §A — C10 Carry Verification

| C10 ID | Title | Status | Evidence (current file) |
|--------|-------|--------|-------------------------|
| **H1** | §3 subsection numbering collision (§2.1/§2.2 inside §3) | **HELD-REMEDIATED** | §3 correctly renumbered §3.1 (L108)/§3.2 (L127)/§3.3 (L135); only §2.1 is L74. No collision. |
| **M1** | `MRHEdge.probability`/`distance` vs SDK `weight`/(absent) | **HELD-REMEDIATED** | L65 `weight: float` (was `probability`); `distance` removed, replaced by L68–69 BFS-computed note. Matches SDK. |
| **M2** | `TrustPropagation` OOP class vs SDK stateless functions | **PARTIAL (by design)** | L186–189 note documents the divergence ("SDK implements these as stateless module-level functions … identical mathematical semantics"); naming aligned (`edge.weight`, `decay_factor` param). The OOP-vs-functional *structure* persists by choice — C10 offered "align OR note"; note path taken. **Caveat: the "identical semantics" claim is now falsified — see §B-F1.** |
| **M3** | §5 duplicates T3/V3 without cross-ref | **HELD-REMEDIATED** | L219 cross-reference banner added per M3 remediation. (Body not trimmed — residual tracked as §B-X4.) |
| **M4** | Inconsistent ontology cross-ref styles | **HELD-REMEDIATED** | Both refs now relative: L104 markdown link, L242 relative path in comment. |
| **L1** | Three blank lines at file start | **HELD-REMEDIATED** | Title on L1. |
| **L2** | Unnumbered preamble sections before §1 | **STILL-OPEN (INFO)** | L5/L14 `##` + L18 `###` precede §1 (L27). Neither remediation option applied. Per BC#13, INFO-grade absent a normative date/numbering dependency. |
| **L3** | SPARQL hardcodes T3 weights 0.4/0.3/0.3 | **HELD-REMEDIATED** | L321 comment cites `t3-v3-tensors.md §9.2/§10.2 (parameter t3v3-001)` — went beyond "example weights" to cite the canonical normative source. |
| **L4** | §7 refs point to standalone scripts, not SDK | **HELD-REMEDIATED** | L366 now leads with **Canonical SDK module** `web4/mrh.py` before the five legacy scripts. |

**Carry verdict: 7 HELD-REMEDIATED, 1 PARTIAL-by-design (M2), 1 STILL-OPEN-INFO (L2), 0 REGRESSED.**

---

## §B — New Findings

### AUTONOMOUS (remediable in `mrh-tensors.md` at C41)

#### F1 (MEDIUM) — §4.2 probabilistic-propagation pseudocode always returns 1.0 (real bug)
**Lines**: L198–204 (vs SDK `mrh.py` L214–225).
`TrustPropagation.probabilistic()` initializes `combined = 1.0` (L200), then applies the noisy-OR update `combined = 1 - ((1 - combined) * (1 - path_trust))` (L203). With `combined = 1.0`, `(1 - combined) = 0`, so every iteration yields `1 - 0 = 1.0` invariantly — the method returns **1.0 for any non-empty path set regardless of path trusts**. The noisy-OR accumulator's identity element is `0.0`, not `1.0`. The SDK `propagate_probabilistic()` is correct (accumulates product-of-complements, returns `1 - ∏(1-p_i)`). This also **falsifies the L186–189 "identical mathematical semantics" claim** (the M2 caveat above).
**Fix**: change L200 `combined = 1.0` → `combined = 0.0`. Then iter₁=p₁, final=`1-∏(1-pᵢ)`, matching the SDK. Held at MEDIUM (not HIGH) because the block is labeled "conceptual structure" with the SDK named as canonical — only a reader implementing directly from pseudocode reproduces the bug.

#### F2 (MEDIUM) — §5.3 titled "Value Tensor (V3)" but body is entirely T3 trust
**Lines**: L252 (heading), L254 (intro), L256–282 (body).
`### 5.3 Role-Contextual Value Tensor (V3)` / "Value creation is measured within role contexts:" promises V3, but `RoleContextualT3V3` only implements the **trust** half: queries `web4:talent/training/temperament`, returns `T3Tensor`, `calculate_role_trust()` returns `self.t3.compute_trust_score()`. `self.v3 = None` (L261) is never read/written. No valuation/veracity/validity logic anywhere. The section duplicates §5.2's T3 subject under a V3 heading; V3 (a primitive in `T3/V3*MRH`) is left undemonstrated.
**Fix**: either re-title/re-intro §5.3 to honestly describe a T3 example, or populate `self.v3` with valuation/veracity/validity logic.

#### F3 (MEDIUM) — L16 "no trust scores / not from abstract metrics" is falsified document-wide
**Lines**: L16 (vs L58–59, L179, L185–215, L296, L304, L313, L322, L352).
L16: "Rather than calculating trust scores or maintaining global reputation … not from abstract metrics." The body does exactly the opposite: `MRHNode.trust_scores: Dict # Multi-dimensional trust metrics` (L58–59); §4.2 computes numeric trust via multiplicative/probabilistic/maximal (L185–215); §5.4 binds `web4:t3Score 0.92`/`0.15` (L296/304); §5.5/§6 compute `?trustScore` from `(talent*0.4 + training*0.3 + temperament*0.3)`. SDK confirms (`trust_scores`, `propagate_*`, `trust_between`). The *intent* (avoid a single global context-free reputation number) is valid, but the wording is overstated.
**Fix**: requalify L16 to "Rather than reducing trust to a single global, context-free reputation number … contextualized by computed role-specific trust scores."

#### F4 (LOW) — §2.1 Turtle block uses `rdfs:` prefix that is never declared
**Lines**: L78–102. Uses `rdfs:subPropertyOf`/`rdfs:comment` but the file declares only `web4:`/`lct:`/`xsd:` (L34–36) — `rdfs:` is declared nowhere. Pasted into a Turtle parser this raises "Undefined namespace prefix: rdfs". (The `web4:`/`lct:` non-redeclaration in later fences is the doc's deliberate fragment convention — *not* a defect; only `rdfs:` is genuinely orphaned.)
**Fix**: add `@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .` to the §2.1 block (matching the canonical TTL files).

#### F5 (LOW) — §3.3 horizon SPARQL `FILTER(?distance <= 3)` is a logical no-op
**Lines**: L143–159. Three UNION branches each hardcode `BIND(n AS ?distance)`, so `?distance ∈ {1,2,3}` structurally — the trailing `FILTER(?distance <= 3)` (L158) can never exclude a row (dead code). The query is *correct* (depth is bounded by the unrolled UNION) but the FILTER misleads anyone trying to parameterize the depth.
**Fix**: remove the FILTER, or comment that the depth bound is structural, not filtered.

#### F6 (LOW) — §5.5/§6 pack multiple complete SELECT forms into one SPARQL fence
**Lines**: L309–336 (2 SELECTs), L342–362 (3 SELECTs). A SPARQL request is a single query form; concatenated SELECTs are a parse error. Additionally §6 (L342–362) declares **no** `PREFIX web4:` at all.
**Fix**: split each comment-delimited query into its own fence, each with a `PREFIX web4: <https://web4.io/ontology#>` header.

#### F7 (LOW) — §3.3 horizon query matches `hasRelationship` but data stores sub-properties (needs RDFS entailment)
**Lines**: L146–156. Example triples store `web4:boundTo`/`pairedWith`/`witnessedBy` (L39–41); the query matches only the super-property `web4:hasRelationship`. Under plain SPARQL (no RDFS regime) those sub-property triples do **not** match — the example returns empty on a non-inferencing store. The prose silently assumes RDFS reasoning. (SDK is unaffected — it does BFS over typed `RelationType` edges.) *Couples to D1/D2 below.*
**Fix**: add a one-line note that the query requires RDFS sub-property entailment, OR use a property-path `(web4:boundTo|web4:pairedWith|web4:witnessedBy)`.

#### F8 (LOW) — `MRHEdge` pseudocode field types diverge from SDK
**Lines**: L61–67 (vs SDK L141–155). Spec `relation: str` / `timestamp: datetime`; SDK `relation: RelationType` (12-member enum, coerced) / `timestamp: Optional[str]` (ISO-8601). Note the spec's own RDF example (L49) already uses an ISO-8601 string, so `datetime` is the internal outlier. SDK also clamps `weight` to [0,1] in `__post_init__` (undocumented in spec). Sits at the LOW/INFO boundary — illustrative pseudocode.
**Fix**: align to `relation: RelationType`, `timestamp: str (ISO 8601)`; optionally note the weight clamp.

#### F9 (LOW) — L16 "MRH is simply the list of other entities" contradicts the doc's own RDF-graph reframe
**Lines**: L16 (vs L5–12, L20, L27, L31, L64–67). "the list" is the doc's own label for the **deprecated** model — §"Evolution: From Lists to RDF Graphs" (L5–7) says MRH "has evolved from simple relationship lists to full RDF graphs." Leftover list-era prose. (Same sentence as F3; can be fixed in one rewrite.)
**Fix**: "…is grounded in the graph of other entities it relates to…".

#### F10 (INFO) — L186–189 note understates the propagate signature refactor
**Lines**: L186–189 (vs SDK L198/214/228). The note flags the method→function shape change but not that `propagate_probabilistic`/`maximal` now consume **pre-computed path-trust scalars** (`List[float]`) and dropped the `decay_factor` parameter (decay is applied earlier). The "identical mathematical semantics" claim is true for these two (modulo F1); only the API description is incomplete.
**Fix**: extend the note to mention the input-type/parameter change across all three functions.

#### F11 (INFO) — §5.5 second query `GROUP BY ?entity ?role` + `MAX` does not "find best role match"
**Lines**: L328–335. Grouping by both vars makes `MAX(?trust)` trivial per (entity,role) pair and preserves per-role rows; the comment "Find best role match for interaction" would require `GROUP BY ?entity` (or a sub-select). Comment/logic mismatch.
**Fix**: adjust the comment to "Rank entity-role pairings by trust", or change to `GROUP BY ?entity` with a sub-select.

#### F12 (INFO) — §5.3 embedded f-string SPARQL omits `PREFIX web4:`
**Lines**: L266–274. `get_trust_in_role` builds a SPARQL string using `web4:` predicates with no in-string `PREFIX` (contrast L141 which declares it). `rdflib.query()` would raise undeclared-prefix. Illustrative pseudocode (`RDFGraph` undefined), so INFO.
**Fix**: insert `PREFIX web4: …` into the f-string.

#### Carry-INFO — L2 (C10) STILL-OPEN
Unnumbered preamble before §1. INFO-grade per BC#13. A C41 remediator MAY demote L5/L14/L18 headings or fold into an intro paragraph; no normative dependency forces it.

---

### DESIGN-Q (operator / architecture — do NOT self-resolve)

> **Consolidated ontology-vocabulary DESIGN-Q (D1).** Six §B findings (the four below + cross-track X1/X2/X3) share one root cause: the spec's illustrative Turtle/SPARQL reference a vocabulary the **canonical ontology does not define**. Rather than scatter them, this is ONE operator decision per [[feedback_cross_cutting_consolidation_audit]]: *for each undefined term, pick a direction — (a) add it to `web4-core-ontology.ttl`, or (b) rewrite the spec example onto existing vocabulary.* The constituent gaps:

#### D1 (MEDIUM) — `web4:hasRelationship`, the root MRH predicate, is undefined in any ontology
**Lines**: L80/88/96 (subPropertyOf declarations), L149–156/L345 (SPARQL traversal). Grep across `ontology/` returns zero hits. §2.1 is framed "The Web4 ontology defines…" but the parent predicate it builds on, and the sub-property taxonomy the §3.3/§6 SPARQL depends on, are materialized nowhere. (No runtime impact — SDK uses `MRHEdge` relation strings, not RDF inference — so MEDIUM not HIGH.) Couples F7.
**Resolution**: (a) add `web4:hasRelationship` super-property + declare boundTo/pairedWith/witnessedBy as subproperties (edits protected canonical ontology), or (b) rewrite §2.1/§3.3/§6 off the super-property.

#### D2 (MEDIUM) — §2.1 `subPropertyOf` taxonomy contradicts the ontology's class-scoped property model
**Lines**: L82–101. The doc models parentBinding/.../oracleWitness as `rdfs:subPropertyOf` the relationship verbs; the canonical ontology models all nine as standalone `rdf:Property` with `rdfs:domain web4:Binding`/`web4:Pairing`/`web4:WitnessAttestation` (class-scoped reification properties). Two structurally incompatible models; the doc's Turtle would not validate. The doc-side alignment is the actionable core; the residual canonical-model question (verb-refinement vs class-scoped reification) is the DESIGN-Q.

#### D3 (MEDIUM) — §5.4 `web4:RolePairing` vocabulary (class + 6 terms) is entirely undefined
**Lines**: L290–304. `web4:RolePairing`, `subjectRole`, `objectRole`, `trustContext`, `t3Score`, plus `subject`/`object` — none exist in either ontology. The canonical T3 binding (`web4:T3Tensor` + `entity` + `role` + `hasDimensionScore`/`talent`) is used correctly **9 lines later** in §5.5 (L313–319), so the section contradicts itself. Resolution: add RolePairing vocab, OR rewrite §5.4 onto `web4:Pairing`/`pairedWithRole` + `T3Tensor`.

#### D4 (LOW) — horizon depth vs decay-zone threshold + zone taxonomy undocumented
**Lines**: L131–164 (vs `mrh.py` L384–401 `horizon_zones()` + `trust.py` L91/L563–574). The spec sets `horizon_depth = 3` and describes Direct/Inherited/Network qualitatively. The SDK exposes a SELF/DIRECT/INDIRECT/PERIPHERAL/BEYOND zone taxonomy with PERIPHERAL out to `MRH_MAX_HOPS = 4` and BEYOND (zero trust) at 5+ — living only in code + test vector `t3v3-009`, never in the spec. A graph traversed at depth 3 never surfaces the 4-hop PERIPHERAL boundary the zone model defines. **Architecture decision needed**: are `horizon_depth (3)` and `MRH_MAX_HOPS (4)` intentionally distinct, or should they unify? Documenting the zones is the easy half; the number reconciliation is operator-gated.

---

### CROSS-TRACK

#### X1 (MEDIUM) — `web4:pairedWith` used throughout but ontology defines only `web4:pairedWithRole`
**Lines**: L40/88/91–93/176. `boundTo` (core) and `witnessedBy` (t3v3) exist, so pairing alone lacks its base predicate — an asymmetric gap. Natural fix is to add `web4:pairedWith` to `web4-core-ontology.ttl`. **Ontology track.** (Folds into the D1 consolidated decision.)

#### X2 (LOW) — Reification predicates `web4:subject/predicate/object/bindingType/timestamp` undefined
**Lines**: L44–49 (§1.1), reused L291/293/299/301 (§5.4). `web4:Binding` is a valid class; the reification predicates are not (only `web4:timestamp` exists, JSON-LD-context-only). **Ontology track.** (Folds into D1.)

#### X3 (LOW) — SPARQL example predicates `interactionType/witnessRole/memberOf/trustScore` undefined
**Lines**: L329/351–352/358–359. Absent from both ontologies; `witnessRole` also demotes the real `web4:timeWitness` property to an object value; §5.4 uses `trustContext` while §5.5 uses `interactionType` for the same record. Illustrative queries, low impact. **Ontology/doc track.** (Folds into D1.)

#### X4 (LOW) — §5 body still duplicates T3/V3 role-contextual material (C10-M3 residual)
**Lines**: L221–305 (vs `t3-v3-tensors.md` §1.1/§5.1/§5.2). The C10-M3 cross-reference banner was applied (§A) but the recommended §5 trimming was not. The alice-Surgeon-vs-Mechanic example, T3Tensor shorthand, and role-contextual principle appear in both docs. **Tag CROSS-TRACK, resolve at C42** (`t3-v3-tensors.md` is the next audit target): decide the canonical home for the role-contextual examples; whether mrh §5 shrinks to a pure MRH-integration pointer (keeping only RolePairing/SPARQL). A mrh-only remediator cannot trim §5 without prejudging that decision.

---

## §B — Deflated (real but over-severitized; recorded, not carried)

| Finding | Raw → Final | Note |
|---------|-------------|------|
| Unnumbered preamble (L5–25) | LOW → **INFO** | = C10-L2 still-open; cosmetic, BC#13. |
| §2 lone subsection §2.1, no §2.2 | LOW → **INFO** | Non-actionable; §2.1 is a stable cite anchor, consistent with doc style. Leave as-is. |
| §5.2 T3Tensor Turtle | claim → **INFO no-defect** | Verified §5.2 shorthand correctly mirrors `t3v3-ontology.ttl` `hasDimensionScore` pattern. Clean. |
| §5.2/§5.4 Turtle omit `@prefix` | LOW → **INFO** | Deliberate fragment convention (prefixes set in §1.1); C10 "Namespace Consistency" already passed this. |

## §B — Refuted (default-to-refute upheld; not defects)

| Finding | Why refuted |
|---------|-------------|
| Cross-ref to t3-v3 §9.2/§10.2 broken | Resolves correctly; §10.2 is the normative source for `t3v3-001`. Clean verification. |
| MRHEdge/MRHNode omit SDK defaults | Pseudocode-convention; spec never claims required-no-default. Not a contradiction. |
| §5 T3/V3 cross-doc inconsistent | Verified clean — weights, citation, dimension names, trust=0.0 rule all match canonical. |
| §5.4 `t3Score 0.15` vs §5.2 Mechanic T3 | Incommensurable — `_:pairing2` is a `RolePairing` (alice-as-CarOwner→garage), not alice's Mechanic T3 composite; L300 already says `# Different role`. |
| §3.3 "relationships become irrelevant" overstates SDK | SDK module docstring (L11–12) uses *identical* language; "Relevancy" is the defined R in MRH. Softening would desync prose from the SDK. |

---

## Disposition for C41 (paired remediation)

- **Apply autonomous**: F1 (flagship bug-fix, one line), F2, F3+F9 (one L16 rewrite), F4, F5, F6, F7 (note-form), F8, F10, F11, F12, and optionally the L2 demotion. All single-file, no design decision. Suggested clustering: **G1 algorithm/SDK-fidelity** (F1, F8, F10), **G2 prose-honesty** (F2, F3, F9), **G3 SPARQL/Turtle hygiene** (F4, F5, F6, F7, F11, F12).
- **Defer (DESIGN-Q, operator)**: **D1 consolidated ontology-vocabulary decision** (subsumes D2, D3, X1, X2, X3) + **D4** horizon_depth/MRH_MAX_HOPS reconciliation + zone-taxonomy documentation. Fold D1/D4 into the standing operator DESIGN-Q bundle alongside id-scheme (carry-C33), Policy-Entity casing (carry-C35-F9), error canonicity (carry-C30), slashing authority (carry-C34-M2).
- **Defer (cross-track)**: X4 §5 duplication → resolve at **C42** (`t3-v3-tensors.md` audit). The ontology-side half of D1/X1/X2/X3 → ontology track (note: editing `web4-core-ontology.ttl` is protected per BC-C23-3).
- **No date bump**: `mrh-tensors.md` carries no date/version banner (an INFO observation, not a finding); nothing to stamp this turn (audit-only).

**Carry-chain note**: prior pass was titled-by-content (`mrh-tensors-internal-consistency-2026-05-23.md`), not `C10-`-prefixed; cited here by filename for traceability.
