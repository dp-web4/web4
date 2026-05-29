# Internal Consistency Audit: `lct-capability-levels.md`

**Audit ID**: C20
**Date**: 2026-05-29
**Auditor**: legion-web4-20260529-060057 (LEAD, autonomous)
**Spec under audit**: `web4-standard/core-spec/lct-capability-levels.md` (v1.0.0, 2026-01-03, 733 lines)
**Audit type**: Audit-only — remediation deferred per C-series discipline

## Authority hierarchy

When `lct-capability-levels.md` ("**cap-levels**") diverges from another in-tree
artifact, this audit applies the C-series default authority precedence:

```
SDK Python + canonical TTL ontology + shipped test vectors  >  spec prose
```

For T3/V3 dimensionality and naming, the SDK and ontology side is well-established
by the prior `docs/audits/2026-04-27-canonical-t3v3.md` audit, which confirmed all
production code paths use the canonical 3-root T3/V3 schema. C20 covers the
spec-prose side of that schism, which the 2026-04-27 audit's code-graph scan did
not address.

Where neither an SDK module nor a canonical ontology predicate nor a test vector
covers a topic, this audit flags items as **DESIGN-Q** (open question requiring
operator input) rather than wire-defect.

## Authoritative anchors consulted

- `web4-standard/ontology/t3v3-ontology.ttl` — canonical T3/V3 RDF ontology (3 root dims, fractal sub-graph)
- `web4-standard/ontology/web4-core-ontology.ttl` — core entity ontology
- `web4-standard/core-spec/LCT-linked-context-token.md` — canonical LCT structure spec
- `web4-standard/core-spec/t3-v3-tensors.md` — canonical T3/V3 tensor spec (§10 parameter-governance table)
- `web4-standard/core-spec/entity-types.md` — canonical 15-type entity taxonomy (§2.1)
- `web4-standard/core-spec/mrh-tensors.md` — canonical MRH/RDF graph spec
- `web4-standard/implementation/sdk/web4/capability.py` — SDK capability module (600 lines)
- `web4-standard/test-vectors/capability/capability-levels.json` — cross-language assessment test vectors
- `web4-standard/test-vectors/schema-validation/capability-jsonld-validation.json` — JSON-LD schema-validation vectors
- `web4-standard/schemas/capability-jsonld.schema.json` — JSON-LD schema definition
- `docs/audits/2026-04-27-canonical-t3v3.md` — prior code-graph audit confirming SDK-side 3-root migration
- `docs/audits/reference-implementation-triage-2026-05-11.md` — prior triage classifying the 1053-line `lct_capability_levels.py` reference implementation as ARCHIVE

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH     | 3     | H1, H2, H3 |
| MEDIUM   | 7     | M1, M2, M3, M4, M5, M6, M7 |
| LOW      | 3     | L1, L2, L3 |
| INFO     | 2     | INFO1, INFO2 |
| DEMOTED  | 3     | D1, D2, D3 |
| **Total findings (excl. INFO/DEMOTED)** | **13** | |

Cross-corpus clusters re-encountered: `subordinate-ontology` (now 5 audits:
C16-M8 + C17-M1 + C18-M6 + C19-M5 + **C20-M5**),
`lifecycle-state-undocumented` (now 3: C19-H1/H2/H3 + C19-M6 + **C20-M7**),
`stale-reference-impl-link` (NEW cluster opened by C20-M1; carry-resume target
once a second instance is found).

New cluster opened by C20:
- **`spec-prose-vs-multi-anchor-canon`** — when spec prose contradicts an
  already-aligned set of SDK + ontology + test-vector + sibling-spec. C20 is
  the first audit in C-series to encounter this *multi-anchor* pattern at H1
  scale; prior audits had single-anchor SDK or single-anchor test-vector
  divergences.
- **`test-vector-coverage-gap`** — when a normatively-detailed protocol
  section has no shipped test vector or schema. C20-M6 opens this cluster.

---

## HIGH

### H1 — T3/V3 dimensionality and naming contradicts canonical ontology, SDK, sibling specs, and test vectors

**Severity**: HIGH (flagship)
**Cluster**: `spec-prose-vs-multi-anchor-canon` (NEW, opened by C20)
**Anchor**: 5-way canonical alignment

**Spec sites (cap-levels)**:
- L22: "T3 always has 6 dimensions"
- L37: T3 row "Trust Tensor (6 dimensions)" + "NEVER Use: Old 3-dimension Talent/Training/Temperament"
- L38: V3 row "Value Tensor (6 dimensions)" + "NEVER Use: Old 3-dimension Valuation/Veracity/Validity"
- L99: "`t3_tensor`: All 6 dimensions with initial values"
- L100: "`v3_tensor`: All 6 dimensions with zero values"
- L131-138: T3 example listing 6 dims: `technical_competence, social_reliability, temporal_consistency, witness_count, lineage_depth, context_alignment`
- L145-152: V3 example listing 6 dims: `energy_balance, contribution_history, resource_stewardship, network_effects, reputation_capital, temporal_value`
- L204-213: T3 Level 2 example, same 6 dims
- L251-260: T3 Level 3 example, same 6 dims
- L264-272: V3 Level 3 example, same 6 dims
- L502, L507: §4.3 QueryResponse `t3_tensor.dimensions: 6` and `v3_tensor.dimensions: 6` (within the L489-538 supported_components block)
- L573-588: §5.3 T3 stub example with 6 dims
- L676: "Verify all 6 T3 dimensions present (value or null)"
- L677: "Verify all 6 V3 dimensions present (value or null)"

**Authoritative anchors (all assert 3-root canonical)**:

1. `web4-standard/ontology/t3v3-ontology.ttl` L11-14: "T3 and V3 tensors are NOT fixed-dimensionality arrays. Each has 3 BASE dimensions that serve as root nodes in an open-ended RDF sub-graph"; L36-43 T3 roots = Talent/Training/Temperament; L47-54 V3 roots = Valuation/Veracity/Validity

2. `LCT-linked-context-token.md` §2.1 L46: "Trust Tensor (T3) (3 root dimensions, fractally extensible via RDF sub-dimensions)" + §2.3 L129-142 canonical example uses `talent/training/temperament` + `sub_dimensions`

3. `t3-v3-tensors.md` §2.1 L22-38 declares 3 T3 root dimensions (Talent/Training/Temperament); §3.1 L185-208 declares 3 V3 root dimensions; §2.4 L124 "T3 dimensions are root nodes in an open-ended RDF sub-graph, not fixed scalars"; §10.2 L531 `T3 composite weights | talent=0.4, training=0.3, temperament=0.3` (protocol-invariant)

4. SDK `web4-standard/implementation/sdk/web4/capability.py` L253: `lct.t3.talent != 0.0 and lct.t3.training != 0.0 and lct.t3.temperament != 0.0`; L268: `lct.v3.valuation != 0.0 or lct.v3.veracity != 0.0 or lct.v3.validity != 0.0` — SDK already uses canonical 3-root

5. Canonical test vector `web4-standard/test-vectors/capability/capability-levels.json` L13-14, 30-31, 56-57, 83-84 — every input record uses `{"talent": ..., "training": ..., "temperament": ...}` and `{"valuation": ..., "veracity": ..., "validity": ...}`

**Corpus sweep for "NEVER Use" terminology violations** (BC#5):
- `technical_competence` field names appear in SDK code only at `web4-standard/implementation/sdk/web4/__init__.py`, `generate.py`, `test_package_api.py`, `test_integration.py`, `test_jsonld_lifecycle.py`, `test_capability.py` — these are legacy/test paths NOT the canonical `T3.talent` field. Per the 2026-04-27 audit's GitNexus impact analysis, "All `T3Tensor` / `T3` / `TrustTensor` classes outside the marked-deprecated files in `core/` declare canonical 3-root fields."
- `archive/reference-implementations/lct_capability_levels{,_v2}.py` use the 6-dim names; both are formally archived per the 2026-05-11 reference-implementation triage.
- `core/lct_capability_levels.py` uses 6-dim names; per 2026-04-27 audit it has been deprecation-headed since Feb 2026 and has 0 IMPORTS from non-test/non-archive code.

**CLAUDE.md (project root) is explicit about ground truth**:
> `T3 | Trust Tensor (3 root dims, each an RDF sub-graph via web4:subDimensionOf) | web4-standard/ontology/t3v3-ontology.ttl`

**Authority precedence**: TTL (canonical RDF) + SDK (canonical implementation)
+ canonical test vector + 2 sibling specs (LCT + t3-v3-tensors) + CLAUDE.md
all assert 3 root dims. Cap-levels prose is the **only** in-tree artifact
asserting 6 dims AND the only one forbidding the canonical terminology. The
weight of evidence is overwhelming.

**Authority precedence reasoning**: Where five orthogonal canonical anchors
(ontology, SDK, test vector, 2 sibling specs) agree, and the spec prose is
the lone dissenter, the spec prose is the defect. This is the textbook
"shipped artifacts are authoritative" pattern previously applied at C18-H3
(test vectors > spec prose) — here extended to a 5-way anchor agreement.

**Scope precision (BC#8)** — the rename surface is **field references in JSON
examples + dimension-count assertions in prose**; the field is a tensor
schema. Local-variable identifiers in adjacent files (e.g. SDK return values
named `lct.t3` or `v3` carrying full tensor objects) are NOT in scope and
must NOT be renamed. The audit-time rename map is approximately:
- 6 T3-name fields → drop to 3 canonical fields (`talent/training/temperament`)
- 6 V3-name fields → drop to 3 canonical fields (`valuation/veracity/validity`)
- 11 prose assertions of "6 dimensions" → "3 root dimensions, fractally extensible via sub-dimensions per t3v3-ontology.ttl"
- L37-38 NEVER-Use cells → DELETE the row contents entirely (or invert to assert 3-root as canonical)

**Recommended remediation**: separate-PR rewrite of every L131-260 + L264-272
+ L489-509 + L573-588 + L675-676 example JSON to canonical 3-root form, with
optional `sub_dimensions` fields when illustrating fractal extension. L22
prose updated. L37-38 NEVER-Use rows DELETED. **Cross-doc check at
remediation time**: also verify `LCT-linked-context-token.md:553`
("`energy_balance` sub-dimension" reference) is consistent with the rewrite.

**Why HIGH**: this is wire-shape-affecting. Any cross-language implementation
reading the spec literally would produce LCTs with `technical_competence`
fields and would fail to validate against the canonical
`test-vectors/capability/capability-levels.json` or interop with the SDK's
`T3` dataclass. Largest spec-vs-multi-anchor divergence found in C-series.

---

### H2 — Spec L37-38 actively forbids canonical T3/V3 terminology

**Severity**: HIGH (terminology-protection violation)
**Cluster**: `spec-prose-vs-multi-anchor-canon` (H1 sub-finding worth its own ID due to severity of explicit prohibition)

**Spec sites (cap-levels)**:
- L34-39: terminology table, "NEVER Use" column
- L37: `T3 | Trust Tensor (6 dimensions) | "Old 3-dimension Talent/Training/Temperament"`
- L38: `V3 | Value Tensor (6 dimensions) | "Old 3-dimension Valuation/Veracity/Validity"`

**Authoritative anchors**:
- `CLAUDE.md` (project root) "Terminology Protection" section lists T3 and V3
  among "DO NOT redefine" terms; canonical spec is `t3v3-ontology.ttl`
- `t3v3-ontology.ttl` L36-54 declares Talent/Training/Temperament + Valuation/Veracity/Validity as the canonical root dimensions
- `t3-v3-tensors.md` §2.1, §3.1 use canonical names throughout

**Why HIGH (separate from H1)**: H1 is "spec asserts wrong count and names";
H2 is the stronger inverse — "spec actively prohibits canonical names". L37-38
turn the canonical ontology into a terminology violation per cap-levels' own
'Terminology is sacred' design principle (L43). This isn't just stale prose;
it's an active anti-canon assertion. Even readers who notice the spec is
out-of-date with the ontology would be discouraged from using canonical
terms by the explicit prohibition.

**Recommended remediation**: delete L37-38 NEVER-Use cells outright, OR
invert them to: "NEVER Use: Old 6-dimension {technical_competence et al}
schema. Canonical: 3 root dimensions Talent/Training/Temperament (T3) and
Valuation/Veracity/Validity (V3), fractally extensible via subDimensionOf."

---

### H3 — V3 dimension list uses operational/economic sub-dimensions as root dimensions

**Severity**: HIGH (semantic/scoping confusion)
**Cluster**: `spec-prose-vs-multi-anchor-canon` (H1/H2 sibling; distinct from H1 because the defect is *category confusion* not just rename)

**Spec sites (cap-levels)**:
- L100, L145-152, L264-272 list V3 with: `energy_balance, contribution_history, resource_stewardship, network_effects, reputation_capital, temporal_value`

**Authoritative anchors**:
- `t3v3-ontology.ttl` L47-54: V3 roots are Valuation, Veracity, Validity
- `t3-v3-tensors.md` §3.1 L185-208: same 3 V3 roots
- `LCT-linked-context-token.md` §10.3 L553 **explicitly classifies `energy_balance` as a sub-dimension, not a root**: "V3 tensor: ATP/ADP balance MAY be tracked via a context-specific `energy_balance` sub-dimension (see `lct-capability-levels.md`)"

**Authority precedence reasoning**: LCT canonical spec §10.3 L553 references
cap-levels as the authority for the `energy_balance` *sub-dimension* — but
cap-levels itself treats `energy_balance` as a ROOT dimension. This is a
circular reference where cap-levels is cited as authority for a sub-dim that
cap-levels itself mis-categorizes.

**Why HIGH (separate from H1)**: H1 is rename-count. H3 is category-shape:
the 6 names cap-levels lists for V3 are conceptually *operational sub-
dimensions of Valuation/Veracity/Validity*, not replacements for those
roots. Even if cap-levels were renaming the roots to 6 different names, the
listed names aren't peer to Valuation/Veracity/Validity — they're items
that would live UNDER `web4:subDimensionOf web4:Valuation` or similar.
This is a deeper conceptual error than H1's rename problem.

**Recommended remediation**: bundled with H1's V3 rewrite — restore V3 to
canonical Valuation/Veracity/Validity root, and demote the 6 named items
to OPTIONAL `sub_dimensions` examples where appropriate (e.g.
`energy_balance` under `valuation` for V3 examples involving ATP economics).

---

## MEDIUM

### M1 — Stale reference-implementation pointer at L725

**Severity**: MEDIUM
**Cluster**: `stale-reference-impl-link` (NEW, opened by C20)

**Spec site**: `lct-capability-levels.md` L725
> `Reference Implementation: implementation/reference/lct_capability_levels.py`

**Anchor**:
- The path `web4-standard/implementation/reference/lct_capability_levels.py` does NOT exist. The actual files are at:
  - `archive/reference-implementations/lct_capability_levels.py` (1053 lines, classified ARCHIVE in `docs/audits/reference-implementation-triage-2026-05-11.md` row 5)
  - `archive/reference-implementations/lct_capability_levels_v2.py`
  - `core/lct_capability_levels.py` (deprecation-headed since Feb 2026, per 2026-04-27 audit)
- Canonical impl: `web4-standard/implementation/sdk/web4/capability.py` (per 2026-05-11 triage's "SDK equivalent" column = "`web4.lct + web4.capability`")

**Why MEDIUM**: spec ships a broken link to its own reference impl. The
correct canonical pointer should be the SDK module, not an archived file.

**Recommended remediation**: change L725 to point at
`web4-standard/implementation/sdk/web4/capability.py`. (Single-line edit.)

### M2 — §3.1 core entity-type table is missing canonical types (`policy`, `infrastructure`) and duplicates `society`

**Severity**: MEDIUM
**Cluster**: fresh

**Spec sites**:
- L406-419 (cap-levels §3.1 "Core Entity Types"): lists 12 types — `human, ai, organization, role, task, resource, device, service, oracle, accumulator, dictionary, hybrid`
- L425-433 (cap-levels §3.2 "Extended Entity Types"): lists `plugin, session, relationship, pattern, society, witness, pending`

**Anchor**:
- `entity-types.md` §2.1 L17-35: canonical 15-type taxonomy — adds `Policy` (L34) and `Infrastructure` (L35) to the 12-listed-in-cap-levels-§3.1, AND lists `Society` (L23) as a primary type (not extended)
- SDK `capability.py:103-119` `ENTITY_LEVEL_RANGES` has 15 entries matching `entity-types.md` (not cap-levels §3.1's 12). Imports `EntityType` from `web4.lct`, which per `LCT-linked-context-token.md:28` declares the canonical 15-type taxonomy.

**Corpus-sweep (BC#5)**:
- `entity-types.md:13-35` declares 15 types
- `LCT-linked-context-token.md:28` cites the canonical 15-type taxonomy
- SDK `capability.py` matches the 15-type canonical
- Cap-levels §3.1 is the only spec asserting only 12

**Authority precedence**: 3-way anchor (canonical entity-types spec + LCT spec
+ SDK enum). Cap-levels §3.1 is wrong.

**Specific sub-findings**:
- M2a: cap-levels §3.1 missing `Policy` (canonical, typical level 3-4 per SDK `ENTITY_LEVEL_RANGES[POLICY] = (3, 4)`)
- M2b: cap-levels §3.1 missing `Infrastructure` (canonical, typical level 3-5 per SDK `ENTITY_LEVEL_RANGES[INFRASTRUCTURE] = (3, 5)`)
- M2c: `society` listed twice (L429 as extended) — should be removed from §3.2 since canonical §3.1 placement is correct elsewhere; or removed entirely if §3.2 is dissolved (see M3)

**Recommended remediation**: regenerate §3.1 from canonical `entity-types.md`
§2.1 taxonomy (15 rows); deduplicate `society` (currently duplicated at
cap-levels L429 in §3.2) from §3.2.

### M3 — §3.2 "Extended Entity Types" invents non-canonical entities

**Severity**: MEDIUM
**Cluster**: fresh

**Spec sites**: L425-433 lists `plugin, session, relationship, pattern, society, witness, pending` as "Extended" entity types

**Anchor**:
- `entity-types.md` §2.1 (canonical 15-type taxonomy) does NOT include `plugin, session, relationship, pattern, witness, pending`
- `web4-core-ontology.ttl` searched: no matches for these as entity types
- SDK `EntityType` enum (imported in `capability.py:28`): inspection per
  `ENTITY_LEVEL_RANGES` keys (L103-119) shows 15-type canonical, no
  `PLUGIN/SESSION/RELATIONSHIP/PATTERN/WITNESS/PENDING` members

**Why MEDIUM**: cap-levels invents 7 entity types unsupported by canonical
ontology or SDK. Cross-doc readers cannot rely on these names. Some (e.g.
`witness` as entity type) collide with the canonical `role: Witness`
pattern in `entity-types.md` §2.1 L25 (Witness is an example *role*, not
an entity type).

**Recommended remediation**: dissolve §3.2; merge the underlying intent
("these are ROLE-PATTERN names used at low levels") into a single paragraph
clarifying that LCT capability levels are orthogonal to role-pattern names,
and that any prose reference to "plugin LCT" means "an LCT pairing with a
plugin role at the role layer". Defer to operator: this is partly
DESIGN-Q since dissolving §3.2 changes the spec's framing.

### M4 — §8.3 L688 makes Level 4 birth-certificate issuance circular

**Severity**: MEDIUM
**Cluster**: fresh (potentially `lifecycle-state-undocumented` extension; flagged separately because the contradiction is direct)

**Spec site**:
- L686-688: `### 8.3 Societies MUST  - Issue birth certificates only to Level 4+ entities`

**Anchor**:
- `LCT-linked-context-token.md` §3.1 L190-213 "Genesis: Birth Certificate from Society" describes the canonical genesis process where the society MINTS the LCT with the birth certificate, i.e. the birth certificate IS the LCT's first existence. There is no "Level 4 entity" prior to issuance.

**Why MEDIUM**: cap-levels §8.3 requires the entity already be Level 4
*before* receiving a birth certificate, but per canonical LCT §3.1 a
birth certificate is what CREATES Level 4 in the first place. Unreachable
state if the spec is taken literally.

**Recommended remediation**: rephrase as "Societies MUST issue birth
certificates to entities that meet Level 4 *post-issuance requirements*"
or "MUST attach birth certificates to LCTs that will be Level 4 after
this issuance". Single-paragraph rephrase.

### M5 — Capability-level concepts absent from canonical ontology

**Severity**: MEDIUM
**Cluster**: `subordinate-ontology` (CONTINUING — now 5 audits: C16-M8 + C17-M1 + C18-M6 + C19-M5 + **C20-M5**)

**Spec sites**: cap-levels prose treats `CapabilityLevel`, `TrustTier`,
`LevelRequirement`, `CapabilityAssessment`, `CapabilityFramework` as
first-class concepts (with JSON-LD schemas declared in
`schemas/capability-jsonld.schema.json` L7-11).

**Anchor**:
- Grep `web4-standard/ontology/*.ttl` for `CapabilityLevel|TrustTier|capability_level|capability:` returns **zero matches**.
- No `web4:CapabilityLevel`, `web4:TrustTier`, `web4:LevelRequirement` classes.
- No `web4:capabilityLevel`, `web4:trustTier`, `web4:hasCapability` predicates.

**Why MEDIUM**: same pattern as C16-M8 (SAL subordinate predicates missing),
C17-M1 (dictionary subordinate predicates), C18-M6 (ACP), C19-M5 (multi-
device). The capability-level layer has shipped JSON-LD schemas and a SDK
module, but no canonical TTL ontology definitions. RDF tools cannot
SPARQL-query capability levels via canonical predicates.

**Recommended remediation**: define a small `capability-levels.ttl` ontology
file declaring `web4:CapabilityLevel`, `web4:TrustTier`, and predicates
`web4:capabilityLevel`, `web4:trustTier`. **This is the same recommended
remediation as C16-M8/C17-M1/C18-M6/C19-M5** — at 5 audits the cluster is
ready for operator-engagement on a unified subordinate-ontology extension
PR covering all 5 specs at once. Defer per BC#9.

### M6 — Capability Query Protocol (§4.2/§4.3) has no test-vector or JSON-LD schema coverage

**Severity**: MEDIUM
**Cluster**: `test-vector-coverage-gap` (NEW, opened by C20)

**Spec sites**:
- L462-478: §4.2 QueryRequest format (8 fields)
- L482-538: §4.3 QueryResponse format (~17 fields with nested structure)

**Anchor**:
- `web4-standard/schemas/capability-jsonld.schema.json` `oneOf` (L7-11) ships
  schemas for `LevelRequirement`, `CapabilityAssessment`, `CapabilityFramework` —
  **no `CapabilityQueryRequest` or `CapabilityQueryResponse`**
- `web4-standard/test-vectors/capability/capability-levels.json` covers
  level-assessment, not query/response
- `web4-standard/test-vectors/schema-validation/capability-jsonld-validation.json`
  covers only the 3 schemas above; nothing for §4.2/§4.3

**Why MEDIUM**: §4 is normatively-detailed (uses MUST in §4.4) but has no
wire-validated artifact. Two independent implementations could produce
incompatible QueryRequest/QueryResponse formats and both would conform to
the spec.

**Recommended remediation**: ship `CapabilityQueryRequest` and
`CapabilityQueryResponse` schemas under
`web4-standard/schemas/capability-jsonld.schema.json` `oneOf`, plus
corresponding test vectors. Both edits are SDK/schema track, not spec-prose
track, and should be paired with H1+H3 remediation so the test vectors use
canonical 3-root T3/V3. Cross-track item; flag for SDK-side carry-resume.

### M7 — §6.2 L632 "Level 5 requires hardware binding from creation" conflicts with multi-device LCT binding (C19 territory)

**Severity**: MEDIUM
**Cluster**: `lifecycle-state-undocumented` (CONTINUING — now 5 instances: C19-H1/H2/H3 + C19-M6 + **C20-M7**)

**Spec sites**:
- L628: §6.1 upgrade table row `4 → 5 | Bind to hardware (cannot be done post-hoc)`
- L632: §6.2 "Level 5 (HARDWARE) requires hardware binding from creation"
- L715: §9.3 "Hardware binding cannot be added post-hoc for Level 5"

**Anchor**:
- `web4-standard/core-spec/multi-device-lct-binding.md` (C19 audit target) defines
  multi-device binding as a process where devices can JOIN an existing entity's
  LCT, including hardware-bound device entities being added to a composite
  identity. The whole point of the multi-device spec is post-creation device
  binding.

**Tension**: a Level 4 (FULL) human-identity LCT presumably can pair with a
Level 5 device via the multi-device binding protocol — does that elevate the
composite identity to Level 5? Cap-levels says no (Level 5 must be at
creation). Multi-device implies yes (composite identity inherits hardware
trust from device member). Spec is silent on which wins.

**Why MEDIUM, not HIGH**: this is genuinely design-uncertain. Both spec
positions are individually coherent. The conflict only emerges when both
specs are read together. Operator must decide whether cap-levels' Level 5
constraint applies to *atomic* LCTs only or also to composite multi-device
LCTs.

**Recommended remediation**: DEFER as DESIGN-Q for operator. Carry-resume
target: bundle with C19 carry-NEW-A/B and other lifecycle-state-undocumented
cluster items for a single operator-engagement session.

---

## LOW

### L1 — §6.2 "Downgrades are not permitted" silent on revocation/witness-loss semantics

**Severity**: LOW
**Cluster**: `lifecycle-state-undocumented` (CONTINUING)

**Spec site**: L635 "Downgrades are not permitted (would break trust chains)"

**Anchor**:
- `LCT-linked-context-token.md` §7.4 L466-479 defines revocation states
  (compromise, superseded, expired, violation) including witness deficit
  scenarios
- `LCT-linked-context-token.md` §6.2 V3 tensor computation depends on
  `computation_witnesses`; if all witnesses revoke, what happens to the level?

**Why LOW**: theoretical edge case; no immediate wire impact. But the
spec's "no downgrade ever" is too absolute given the LCT spec's revocation
machinery.

**Recommended remediation**: add a single-sentence clarification: "When
required components are lost (witness deficit, revoked attestations), the
LCT enters a 'degraded' state retaining its claimed level but failing
`validate_level` checks. Society policy determines whether the LCT is
revoked or held degraded pending recovery."

### L2 — §9.3 L717 introduces unstated requirement "MRH relationships must be mutual" for Level 2

**Severity**: LOW
**Cluster**: fresh

**Spec sites**:
- L717: "MRH relationships must be mutual for Level 2"
- §2.4 (Level 2 BASIC) L174-177: "Additional Requirements over Level 1: `mrh.bound` OR `mrh.paired`: At least one relationship"

**Anchor (intra-document)**: cap-levels itself; §2.4 declares Level 2
requirements without "mutual" qualifier. §9.3 (Security) introduces
"mutual" requirement not present in level definition.

**Why LOW**: presentational inconsistency between Section 2 (level definition)
and Section 9 (security). Spec contradicts itself within itself.

**Recommended remediation**: either (a) add "(mutual)" to §2.4 if mutuality
is in fact required, OR (b) rephrase §9.3 to "MRH relationships must be
mutual *for the relationship to count toward level upgrade*" (clarifying
scope), OR (c) drop the L718 line if it's a stale assertion.

### L3 — §4.3 QueryResponse stub format diverges from §5.2 canonical stub format

**Severity**: LOW
**Cluster**: fresh (intra-document)

**Spec sites**:
- §5.2 L561-568: canonical stub format requires `stub: true` AND `reason: "..."`
- §4.3 L510-513 and L518-521: QueryResponse stub examples show
  `{"implemented": false, "stub": true}` **without `reason`**

**Anchor**: §5.2 is the canonical stub format definition.

**Why LOW**: presentation/example inconsistency. The §4.3 examples drop
`reason` from the stub representation, contradicting §5.2's own normative
shape.

**Recommended remediation**: add `"reason": "Component not implemented"`
(or similar) to the §4.3 L510-513 + L518-521 stub examples. Single-paragraph
edit.

---

## INFO

### INFO1 — SDK `capability.py:281` uses fragile substring match for citizen-pairing detection

**Cross-track (SDK, not C20-spec scope)**:

```python
def _has_permanent_citizen_pairing(lct: LCT) -> bool:
    return any(p.permanent and "citizen" in p.lct_id for p in lct.mrh.paired)
```

Per cap-levels §2.6 L325 and LCT spec §2.3 L98, the canonical marker for
citizen pairing is `pairing_type == "birth_certificate"` AND `permanent ==
true` — not a substring match on `lct_id`. The SDK's substring check on
`"citizen"` would miss citizen role LCTs whose ID doesn't contain the
substring (e.g. society-issued role LCT IDs that hash the role rather than
spelling it). Out-of-scope for C20 audit per BC1; flagged for SDK carry-NEW.

### INFO2 — Trust tier labels not declared in spec but used in SDK and test vectors

**Cross-track presentational**:

Cap-levels L55-60 table column "Trust Tier" gives numeric ranges
(0.0-0.2, 0.2-0.4, ...) but does NOT name the tier labels.

SDK `capability.py` declares: UNTRUSTED, LOW, MODERATE, MEDIUM, HIGH,
MAXIMUM (L79-84). Canonical test vector
`test-vectors/capability/capability-levels.json` uses these labels
consistently.

The labels are SDK conventions absent from the spec but consistently
applied; the missing-from-spec status is a presentational gap, not a
wire-invariant defect. Recommended (out-of-C20-scope): add a one-row column
to the L53 table mapping range → tier label.

---

## DEMOTED

### D1 — JSON-LD schema-validation test vector trust_ranges differ from spec/SDK tier ranges (DEMOTED)

**Initial impression**: `test-vectors/schema-validation/capability-jsonld-validation.json` shows trust_ranges like [0.0, 0.1], [0.9, 1.0], [0.5, 0.7] — these don't match the spec/SDK tier ranges (0.0-0.2, 0.8-1.0, 0.4-0.6).

**Why DEMOTED**: the schema-validation file's `trust_range` values are
testing the JSON Schema's `[0, 1]` numeric constraint (`minimum: 0,
maximum: 1` per `capability-jsonld.schema.json` L60). They are *schema
test inputs*, not canonical tier-range assertions. The CANONICAL
assessment test vector (`test-vectors/capability/capability-levels.json`)
matches the SDK tier ranges (e.g. Level 2 → trust_tier "moderate", Level
3 → "medium"). Demoted under BC#6 corpus-sweep discipline.

### D2 — Schema-validation test vector `requirements` strings look like Web2 KYC (DEMOTED)

**Initial impression**: `cap-valid-002` describes Level 5 requirements as
"Email or phone verification, Government ID verification, Biometric binding,
Hardware attestation (TPM2/FIDO2/SE)" — Web2-style KYC requirements that
don't match cap-levels §2.7 Level 5 requirements (hardware_anchor,
hardware_type, hardware_attestation).

**Why DEMOTED**: the schema declares `requirements: type: array, items:
type: string` with no enum constraint. The validation test vectors use
arbitrary strings to exercise the schema; they're not asserting
canonical requirement names. Per BC#6 corpus-sweep — verified that the
schema imposes no value constraint, so any string list passes. Demoted.

### D3 — §5.3 T3 stub example uses old 6-dim names (DEMOTED — same as H1)

**Initial impression**: §5.3 L573-588 T3 stub example uses
`technical_competence` et al.

**Why DEMOTED**: this is one of the ~15 spec line-positions in H1's scope.
Captured under H1's "Recommended remediation" rather than as a separate
finding to avoid double-counting. Demoted into H1's edit map.

---

## Cross-corpus cluster carry forward

These clusters are now ready (5+ instances) or near-ready (3-4 instances)
for operator-engagement bundled remediation:

| Cluster | Instances | Status |
|---------|-----------|--------|
| `subordinate-ontology` | C16-M8 + C17-M1 + C18-M6 + C19-M5 + **C20-M5** = 5 | **5-audit threshold reached** — recommend unified TTL extension PR |
| `canonical-errors-taxonomy` (W4_ERR) | C16-H1 + C17-M4 + C18-M2 + C19-M3 = 4 | 4-audit; one more brings it to 5-threshold |
| `lifecycle-state-undocumented` | C19-H1 + C19-H2 + C19-H3 + C19-M6 + **C20-M7** + **C20-L1** = 6 (1 audit's worth + 2) | C19-internal cluster extended by C20 |
| `test-vectors-as-authority` | C18-H3 + C19-M1 + C19-M2 + **C20-H1** = 4 | hardened to 4 |
| `snake/camel wire split` | C18-M3 + C18-L1 + C17-M3 = 3 | unchanged this audit |
| `spec-prose-vs-multi-anchor-canon` | **C20-H1 + C20-H2 + C20-H3** = 3 (within one audit) | NEW |
| `stale-reference-impl-link` | **C20-M1** = 1 | NEW |
| `test-vector-coverage-gap` | **C20-M6** = 1 | NEW |

The `subordinate-ontology` cluster is now formally at the 5-audit threshold
established by the C-series cadence. Operator-engagement bundled TTL
extension PR covering all 5 audits' subordinate-ontology gaps is the
recommended next-step.

---

## Remediation discipline (per C-series default)

This audit is audit-only. Remediation will be a future-session task. The
graceful-partial-remediation pattern (C16/C17/C18/C19) applies: a future
remediation PR will likely ship 5-7 of the 13 findings as autonomous
wire-fixes (H1 + H2 + H3 + M1 + L3 + likely M2 + M4 are clean spec-only
edits) with the rest deferred as DESIGN-Q (M3, M5, M6, M7, L1, L2) for
operator engagement. INFO1 is SDK-track; INFO2 is presentational.

H1 alone touches ~15 line positions across cap-levels.md; a remediation
PR should plan for ~+50/-40 lines just for H1 + H2 + H3 bundled. M2+M4+L3
adds modest additional surface. Total remediation: ~+80/-60 expected.

---

## Audit metadata

- **Line count of this audit**: ~570 (within BC2 ≤ 650)
- **Findings count (excl. INFO/DEMOTED)**: 13 (consistent with C19's 13)
- **Cluster contributions**: +2 NEW clusters opened (`spec-prose-vs-multi-anchor-canon`, `stale-reference-impl-link`, `test-vector-coverage-gap`), 1 cluster reached 5-audit threshold (`subordinate-ontology`)
- **Corpus-sweep events (BC5)**: 4 (H1 sweep across SDK + test vectors; M2 sweep across entity-types specs; M3 sweep across ontology + SDK; M5 sweep across ontology TTLs)
- **Demotion events (BC6)**: 3 (D1, D2, D3 with corpus evidence)
- **Authority-precedence reasoning (BC4)**: explicit for H1, H2, H3, M1, M2

*"Where five canonical anchors agree, prose is the dissenter."*
