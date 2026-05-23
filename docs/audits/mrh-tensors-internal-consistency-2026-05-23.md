# C10 Audit: `mrh-tensors.md` Internal Consistency

**Date**: 2026-05-23
**Auditor**: Autonomous session (Legion, web4 track)
**Document**: `web4-standard/core-spec/mrh-tensors.md` (370 lines)
**Methodology**: C-series internal consistency audit (same as C2, C5, C6, C7, C8, C9)
**SDK alignment**: Checked against `web4-standard/implementation/sdk/web4/mrh.py` — functional compliance with naming divergences noted below
**Ontology alignment**: Checked against `web4-standard/ontology/t3v3-ontology.ttl`, `web4-standard/ontology/web4-core-ontology.ttl` — namespace usage consistent (`https://web4.io/ontology#`)

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| HIGH | 1 | H1 |
| MEDIUM | 4 | M1, M2, M3, M4 |
| LOW | 4 | L1, L2, L3, L4 |
| **Total** | **9** | |

The document has a **section numbering collision** in §3 where subsections are misnumbered as §2.1 and §2.2 (colliding with the real §2.1 in the previous section). The content is generally sound and the SDK implements the spec's concepts faithfully, but several naming divergences between spec pseudocode and SDK implementation should be reconciled. §5 substantially duplicates material from `t3-v3-tensors.md` without cross-referencing it, creating a maintenance risk.

---

## HIGH Findings

### H1: §3 Subsection Numbering Collision — §2.1/§2.2 Duplicated Inside §3

**Lines**: 110, 129, 137
**Issue**: Section 3 "How MRH Creates Context" contains three subsections with broken numbering:
- Line 110: `### 2.1 Relationship Types Define Context` — should be `### 3.1`
- Line 129: `### 2.2 Context Propagation` — should be `### 3.2`
- Line 137: `### 3.3 The Markov Property with Graph Traversal` — correct number but no preceding §3.1/§3.2

The §2.1 and §2.2 labels collide with the actual `### 2.1 Relationship Ontology` in §2. Any cross-reference to "§2.1" is ambiguous — it could mean the Relationship Ontology subsection (line 76) or the Relationship Types subsection (line 110).

**Impact**: Structural ambiguity. Two different sections share the same address. Cross-references to §2.1 or §2.2 cannot be resolved unambiguously.

**Remediation**: Renumber to `### 3.1 Relationship Types Define Context`, `### 3.2 Context Propagation`, `### 3.3 The Markov Property with Graph Traversal` (already correct).

---

## MEDIUM Findings

### M1: Spec `MRHEdge.probability` / `distance` vs SDK `MRHEdge.weight` / (absent)

**Lines**: 68–69 (spec), SDK `mrh.py` lines 148–149
**Issue**: The spec's pseudocode `MRHEdge` class defines:
```python
probability: float       # Edge weight/probability
distance: int            # Hop distance from origin
```

The SDK implementation uses:
```python
weight: float = 1.0      # Edge weight (trust probability)
# No `distance` field
```

Two divergences:
1. **`probability` → `weight`**: Different names for the same concept (edge trust weight).
2. **`distance` field**: The spec includes `distance` as a stored field on each edge. The SDK computes distance dynamically via BFS traversal in `MRHGraph.horizon()`, which is architecturally different — edges don't carry their hop distance.

**Impact**: Developers reading the spec would expect `edge.probability` and `edge.distance` fields that don't exist in the SDK. The architectural difference (stored vs computed distance) is substantive.

**Remediation**: Either update the spec pseudocode to match the SDK field names (`weight` instead of `probability`, remove `distance`), or document the divergence as intentional (spec = conceptual, SDK = optimized).

---

### M2: Spec trust propagation uses instance method (`self.decay_rate`) vs SDK stateless function

**Lines**: 188–208 (spec), SDK `mrh.py` lines 198–211
**Issue**: The spec defines trust propagation as a class `TrustPropagation` with instance methods:
```python
class TrustPropagation:
    def multiplicative(self, path: List[MRHEdge]) -> float:
        trust *= edge.probability * (self.decay_rate ** edge.distance)
```

The SDK implements the same logic as stateless module-level functions:
```python
def propagate_multiplicative(path_weights: List[float], decay_factor: float = 0.7) -> float:
```

Naming divergences: `self.decay_rate` (spec) vs `decay_factor` parameter (SDK); `edge.probability` (spec) vs `w` weight value (SDK); `edge.distance` (spec) vs computed `i + 1` index (SDK).

**Impact**: The mathematical semantics are identical, but the structural pattern (OOP class vs stateless functions) and naming differ. A developer implementing from the spec would produce different code than the SDK.

**Remediation**: Align the spec pseudocode with the SDK's stateless function pattern, or add a note that the spec shows conceptual structure while the SDK uses a more Pythonic implementation.

---

### M3: §5 Duplicates T3/V3 Content Without Cross-Reference to `t3-v3-tensors.md`

**Lines**: 216–333
**Issue**: §5 "Role-Contextual T3/V3 Tensors" spans 118 lines and covers:
- Role-specific trust principle (§5.1)
- Role-bound T3 tensor with Turtle examples (§5.2)
- Role-contextual V3 with Python class (§5.3)
- Role pairing in MRH with Turtle examples (§5.4)
- SPARQL for role-based trust queries (§5.5)

This material substantially overlaps with `t3-v3-tensors.md`, which is the canonical T3/V3 specification. However, §5 never cross-references that document. If either document changes, the other could silently become contradictory.

**Impact**: Maintenance risk. Two authoritative-looking descriptions of the same concepts with no linkage.

**Remediation**: Add a cross-reference note at the top of §5, e.g.: "For the full T3/V3 specification, see [`t3-v3-tensors.md`](t3-v3-tensors.md). This section describes how T3/V3 tensors integrate with MRH context." Consider reducing §5 to the MRH-specific aspects (§5.4 Role Pairing, §5.5 SPARQL queries) and referencing the T3/V3 spec for the foundational material.

---

### M4: Inconsistent Cross-Reference Styles for Ontology File

**Lines**: 106, 238–239
**Issue**: Two references to the T3/V3 ontology use different formats:
- Line 106: Relative markdown link — `[T3/V3 Ontology](../ontology/t3v3-ontology.ttl)` ✓
- Lines 238–239: Parenthetical absolute repo path — `(web4-standard/ontology/t3v3-ontology.ttl)` in a code comment

The line 106 style is correct for markdown rendering. The line 239 style uses a repo-root-relative path in a code comment, which doesn't render as a clickable link and is inconsistent with the other reference.

**Impact**: Minor usability issue. The second reference won't render as a clickable link in markdown viewers.

**Remediation**: Use consistent relative markdown link syntax throughout, or at minimum keep the parenthetical reference as a relative path (`../ontology/t3v3-ontology.ttl`).

---

## LOW Findings

### L1: Three Blank Lines at Start of File

**Lines**: 1–3
**Issue**: The file starts with three blank lines before the `#` title on line 4. Other spec files (e.g., `entity-types.md`, `inter-society-protocol.md`) start with the title on line 1.

**Remediation**: Remove leading blank lines.

---

### L2: Unnumbered Introductory Sections Before §1

**Lines**: 8–28
**Issue**: Two `##` sections appear before `## 1. MRH Implementation as RDF Graph`:
- Line 8: `## Evolution: From Lists to RDF Graphs`
- Line 17: `## Core Concept: Context Through Relationships`

These are followed by `### Key Principles` (line 21), also unnumbered. Other spec files like `t3-v3-tensors.md` and `atp-adp-cycle.md` start numbering from `## 1.` with all preamble material above.

**Impact**: Not necessarily wrong (preamble sections are common), but creates an inconsistency in the document's numbering scheme — the numbered body starts at §1 on line 30, after 22 lines of unnumbered `##` content.

**Remediation**: Either number the introductory sections (renumbering all subsequent sections), or keep them unnumbered but demote to a brief introductory paragraph under the title.

---

### L3: SPARQL Query Hardcodes T3 Dimension Weights

**Lines**: 319
**Issue**: The SPARQL query example hardcodes composite trust weights:
```sparql
BIND((?talent * 0.4 + ?training * 0.3 + ?temperament * 0.3) AS ?trustScore)
```

The T3/V3 specification (`t3-v3-tensors.md`) does not prescribe fixed weights — dimension aggregation is domain-specific. The hardcoded 0.4/0.3/0.3 could be misread as normative.

**Impact**: Low — the SPARQL is clearly an example. But developers might copy it verbatim.

**Remediation**: Add a comment to the SPARQL: `# Example weights — actual weights are domain/role-specific`.

---

### L4: §7 Implementation References Point to Standalone Scripts

**Lines**: 363–367
**Issue**: §7 links to five files in the `web4-standard/` root:
- `../MRH_RDF_SPECIFICATION.md`
- `../mrh_rdf_implementation.py`
- `../mrh_sparql_queries.py`
- `../mrh_trust_propagation.py`
- `../mrh_visualizer.py`

All five files exist and links resolve correctly. However, the four `.py` files are standalone scripts in the repository root, not importable modules within the SDK (`web4-standard/implementation/sdk/web4/`). The canonical SDK implementation is `web4/mrh.py`, which is not referenced in §7.

**Impact**: §7 references pre-SDK artifacts without mentioning the actual SDK module. Readers seeking the canonical implementation would find standalone scripts rather than the tested, integrated module.

**Remediation**: Add a reference to the SDK implementation: "Canonical SDK implementation: `implementation/sdk/web4/mrh.py`". Consider whether the standalone scripts should be noted as historical/supplementary.

---

## SDK Alignment Summary

| Spec Concept | SDK Implementation | Status |
|-------------|-------------------|--------|
| `MRHNode` class | `MRHNode` dataclass | ✅ Aligned (fields match) |
| `MRHEdge` class | `MRHEdge` dataclass | ⚠️ M1: `probability`→`weight`, `distance` absent |
| `MRHEdge.relation: str` | `MRHEdge.relation: RelationType` | ✅ SDK more specific (enum) |
| Relationship ontology (12 types) | `RelationType` enum (12 values) | ✅ Fully aligned |
| 3 relationship categories | `relation_category()` function | ✅ Fully aligned |
| `TrustPropagation` class (3 methods) | 3 module-level functions | ⚠️ M2: OOP→functional pattern |
| `horizon_depth = 3` default | `MRHGraph(horizon_depth=3)` | ✅ Aligned |
| BFS horizon traversal (SPARQL) | `MRHGraph.horizon()` (Python BFS) | ✅ Semantically aligned |
| Trust propagation math | `propagate_*` functions | ✅ Formulas match |

---

## Cross-Reference Validation

| Reference | Target | Valid? |
|-----------|--------|--------|
| Line 106: `[T3/V3 Ontology](../ontology/t3v3-ontology.ttl)` | `web4-standard/ontology/t3v3-ontology.ttl` | ✅ |
| Line 363: `[MRH RDF Specification](../MRH_RDF_SPECIFICATION.md)` | `web4-standard/MRH_RDF_SPECIFICATION.md` | ✅ |
| Line 364: `[MRH RDF Implementation](../mrh_rdf_implementation.py)` | `web4-standard/mrh_rdf_implementation.py` | ✅ |
| Line 365: `[SPARQL Query Examples](../mrh_sparql_queries.py)` | `web4-standard/mrh_sparql_queries.py` | ✅ |
| Line 366: `[Trust Propagation](../mrh_trust_propagation.py)` | `web4-standard/mrh_trust_propagation.py` | ✅ |
| Line 367: `[MRH Visualizer](../mrh_visualizer.py)` | `web4-standard/mrh_visualizer.py` | ✅ |
| Line 239: `(web4-standard/ontology/t3v3-ontology.ttl)` (comment) | Same file | ⚠️ M4: Not a markdown link |

---

## Namespace Consistency

The spec uses `@prefix web4: <https://web4.io/ontology#>` throughout. This is consistent with:
- `web4-standard/ontology/web4-core-ontology.ttl` (uses `https://web4.io/ontology#`)
- `web4-standard/ontology/t3v3-ontology.ttl` (uses `https://web4.io/ontology#`)

The separate `https://web4.io/ns/` namespace is used for JSON-LD contexts (`schemas/contexts/`), which is a different layer. No conflict.
