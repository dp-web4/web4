# Canonical T3/V3 Definition Audit

**Date**: 2026-04-27
**Scope**: All Python and Rust source in dp-web4/web4 repo
**Method**: GitNexus code knowledge graph (123,106 nodes / 181,493 edges, freshly re-indexed) + targeted Cypher queries for class properties and import relationships. Earlier grep-based passes were superseded by this graph-based pass after a session lesson: grep finds patterns, not data flow.

---

## Question

After fixing the most-visible T3/V3 staleness in docs (Python README, web4-trust-core README, claude-code-plugin README, GLOSSARY, CANONICAL_TERMS, CONTRIBUTING.md, AGENTS.md, README.md): **does all active code now use the canonical 3-root T3/V3 schema, or are there remaining production-path implementations on legacy variants?**

The canonical schema (per `web4-standard/ontology/t3v3-ontology.ttl` and `web4-core/src/{t3,v3}.rs`):
- **T3** = 3 root dimensions: Talent / Training / Temperament. Each root is itself an open-ended RDF sub-graph of context-specific sub-dimensions via `web4:subDimensionOf`. Fractally extensible, not a fixed-size vector.
- **V3** = 3 root dimensions: Valuation / Veracity / Validity. Same fractal RDF pattern.

---

## Method

1. Re-indexed the repo with GitNexus (`npx gitnexus analyze --embeddings`).
2. Cypher query for all `Class` nodes named `T3Tensor`, `TrustTensor`, `T3`, `CoherenceTrustTensor` and their `HAS_PROPERTY` relationships. Returns class fields per file.
3. Impact analysis (`mcp__gitnexus__impact`) on candidate-legacy classes to identify upstream importers and process participation.
4. Cypher query for `IMPORTS` edges into the legacy file paths to identify which production code (if any) reaches them.
5. Cross-checked against extracted `Process` nodes (execution flows) — `STEP_IN_PROCESS` edges show whether a class participates in any analyzed call chain.

---

## Findings

### Active production code: uniformly canonical

All `T3Tensor` / `T3` / `TrustTensor` classes outside the marked-deprecated files in `core/` declare canonical 3-root fields (`talent`, `training`, `temperament`). Verified across:

- `web4-core/src/t3.rs`, `v3.rs` (Rust core)
- `web4-trust-core/src/tensor/{t3,v3}.rs` (Rust trust core)
- `web4-standard/implementation/sdk/web4/trust.py` (Python SDK — `T3` class)
- `web4-standard/implementation/reference/`:
  - `trust_tensor.py`, `reputation_engine.py`, `lct_capability_levels.py`, `mrh_graph.py`
  - `acp_framework.py`, `avp_core_protocol.py`, `cognitive_sub_entity.py`, `compliance_drift_monitoring.py`
  - `conformance_test_suite.py`, `dictionary_compression_trust.py`, `dictionary_cross_domain.py`, `dictionary_entities_spec.py`, `dictionary_entity.py`
  - `e2e_federation_scenario.py`, `e2e_fullstack_demo.py`, `e2e_integration_prototype.py`
  - `entity_relationships.py`, `entity_relationships_unified.py`
  - `eu_ai_act_compliance_demo.py`, `eu_ai_act_compliance_engine.py`, `eu_ai_act_demo_stack.py`
  - `full_stack_protocol_integration.py`, `governance_simulation_engine.py`
  - `lct_core_spec.py`, `lct_document.py`
  - `mcp_trust_binding.py`, `mcp_web4_protocol.py`
  - `mrh_policy_scoping.py`, `multi_scale_trust_composition.py`
  - `privacy_preserving_trust.py`, `r6_framework_spec.py`, `r6_implementation_tiers.py`, `r6_tensor_guide.py`, `r7_framework.py`
  - `regulatory_audit_evidence_package.py`, `reputation_computation.py`
  - `sal_society_authority_law.py`, `t3_tracker.py`, `t3v3_privacy_governance.py`
  - `web4_entity.py`, `web4_integration_sdk.py`

### Legacy 6D-C files: graph-isolated, 0 process participation

Two files in `core/` use the legacy 6D-C variant (technical_competence / social_reliability / temporal_consistency / witness_count / lineage_depth / context_alignment):

- `core/pattern_source_identity.py` — deprecation header added 2026-04-27, points at canonical impls
- `core/lct_capability_levels.py` — deprecation header was already in place since Feb 2026, points at canonical impls

**Both have 0 `IMPORTS` edges from non-test, non-archive code.** They form a closed loop with `core/pattern_signing.py` (which uses `getattr(t3, 'technical_competence', 0.1)` — dynamic attribute access invisible to static analysis but verifiable from text). `core/pattern_signing.py` is imported only by 4 test files:

- `tests/sessions/test_session123_integrated_federation.py`
- `tests/sessions/test_session124_tpm2_validation.py`
- `tests/sessions/test_session124_cross_machine_federation.py`
- `tests/sessions/test_session125_canonical_lct_integration.py`

No production code path reaches the legacy 6D-C objects.

### Physics-of-trust research subsystem: not a competing schema

`web4-standard/implementation/trust/coherence_trust_tensor.py` references "psychological 4D model (competence/reliability/benevolence/integrity)" in its module-level docstring as bridge framing. The actual classes inside (`TrustBehaviorProfile`, `CoherenceTrustMetrics`) have **physics-flavored fields** (`trust_value`, `trust_variance`, `network_density`, `coherence`, `gamma`, `entropy_ratio`, `n_corr`, `d_eff`, etc.) — not competing T3/V3 fields.

Impact analysis: 6 upstream importers (4 in `archive/`, 2 in same `trust/` subdir). **0 process participation.** Isolated research subsystem.

### Archive findings (acceptable, documented)

The archive directory contains a few legacy variants that are appropriately archived:
- `archive/reference-implementations/relationship_coherence_ep.py` — 4D variant
- `archive/implementation-sessions/session94_track3_reputation_persistence.py` — 5D variant

All other `archive/` T3 implementations use canonical 3-root.

### Migration helpers (intentional, not stale)

These files reference legacy 6D dim names by design:
- `web4-trust-core/src/tensor/t3.rs::from_legacy_6d` — explicit migration helper
- `ledgers/reference/go/lct/document.go::MigrateT3FromLegacy6D` — explicit migration helper

Both correctly named, both fold legacy 6D input into canonical 3-root output. Live `T3Tensor` types in both files use canonical 3-root.

---

## Conclusion

The canonical-definition state of active production code is clean. Every T3/V3 class that participates in active execution flows uses the canonical 3-root (Talent/Training/Temperament; Valuation/Veracity/Validity) schema with fractal RDF sub-graph extensibility.

Remaining 6D references in the repo are confined to:

| Category | Status |
|---|---|
| Marked-deprecated legacy files in `core/` | Headers point at canonical; 0 graph-level importers; only reachable via test scaffolding |
| Physics research subsystem (`coherence_trust_tensor.py`) | Not a competing schema; physics analytics with bridge framing in docstring |
| `archive/` directory | Acceptable; archive is the deprecation signal |
| Migration helpers (`from_legacy_6d`, `MigrateT3FromLegacy6D`) | Correct by design |
| Test files exercising legacy code paths | Tests of deprecated functionality; can be left or migrated incrementally |

**Publish-readiness implication**: web4-core (Rust + Python) and web4-trust-core (Rust + Python) can be published to crates.io / PyPI without exposing downstream users to legacy 6D dim names. The legacy code remains available for backward-compatibility purposes, properly annotated.

---

## Method note

This audit was preceded by grep-based passes that surfaced several stale-dim instances but couldn't answer the data-flow question ("does any production process actually reach this code?"). GitNexus's graph-level queries answered that directly via `IMPORTS` edges and `STEP_IN_PROCESS` participation. Lesson for future audits: when the question is "is anything still using X?", graph-based call/import tracing is the appropriate tool — grep is for pattern coverage, not reachability.

---

## Appendix: query log

Key Cypher queries executed (for reproducibility):

```cypher
-- All T3-named classes with their property names
MATCH (c:Class)-[:CodeRelation {type: 'HAS_PROPERTY'}]->(p)
WHERE c.name = 'T3Tensor' OR c.name = 'TrustTensor' OR c.name = 'T3'
RETURN c.name AS class, c.filePath AS file, collect(p.name) AS props
ORDER BY file
```

```cypher
-- Importers of legacy core/ files
MATCH (caller)-[r:CodeRelation {type: 'IMPORTS'}]->(target)
WHERE target.filePath CONTAINS 'core/pattern_source_identity'
   OR target.filePath CONTAINS 'core/lct_capability_levels'
RETURN target.filePath AS legacy_file, count(caller) AS importers,
       collect(DISTINCT caller.filePath)[..10] AS sample_importers
```

```cypher
-- pattern_signing.py importers (the dynamic-access bridge)
MATCH (caller)-[r:CodeRelation {type: 'IMPORTS'}]->(target:File)
WHERE target.filePath = 'core/pattern_signing.py'
RETURN count(caller) AS importers, collect(DISTINCT caller.filePath) AS files
```
