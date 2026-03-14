# Reference Implementations Archive — Manifest

**Archived**: 2026-03-14
**Sprint task**: S4 (archive reference implementation sprawl)
**Reason**: 189 entries in `implementation/reference/` accumulated during sessions 1-34.
None import from the canonical web4 SDK (`web4.trust`, `web4.lct`, `web4.atp`, `web4.federation`).
The directory predates the SDK (built in sessions 35-39).

## Triage Summary

| Category | Count | Action |
|----------|-------|--------|
| Genuine web4 protocol implementations | 39 | **KEPT** in `implementation/reference/` |
| Session-specific scripts | 19 | Archived |
| SAGE integration experiments | 19 | Archived |
| SAGE coordinator cluster | 17 | Archived |
| Generic CS with trust-prefix | 13 | Archived |
| MRH grounding / coherence cluster | 14 | Archived |
| Authorization/reputation demos | 7 | Archived |
| Test files for archived modules | 39 | Archived |
| Data/log/JSON files | 14 | Archived |
| Session documentation | 7 | Archived |
| **Total archived** | **149** | |

## What Was KEPT (39 items in `implementation/reference/`)

### Core Protocol (24 .py)

| File | Implements |
|------|-----------|
| `trust_tensor.py` | Canonical T3/V3 tensor with fractal sub-dimensions, CI modulation |
| `trust_tensors.py` | CI modulation of trust application (companion to trust_tensor.py) |
| `lct_registry.py` | LCT minting, birth certificates, entity lifecycle |
| `law_oracle.py` | Society law dataset, norm/procedure/interpretation system |
| `authorization_engine.py` | Full authorization pipeline: LCT + trust + law + ATP |
| `reputation_engine.py` | T3/V3 delta computation from R6 action outcomes |
| `resource_allocator.py` | ATP budget enforcement, quota management |
| `witness_system.py` | COSE/JOSE attestations, Ed25519 verification |
| `mrh_graph.py` | RDF triple store, trust propagation, SPARQL-like queries |
| `atp_demurrage.py` | Demurrage mechanics, velocity enforcement, decay rates |
| `demurrage_service.py` | Background ATP decay service |
| `trust_oracle.py` | PostgreSQL-backed T3/V3 query service with temporal decay |
| `crypto_verification.py` | Ed25519 verification for LCT credentials |
| `production_crypto.py` | ATP/delegation/birth certificate signing |
| `persistence_layer.py` | PostgreSQL backend for LCT registry and attestations |
| `lct_capability_levels.py` | LCT capability levels (0-5), entity type registry |
| `web4_client.py` | Full client: ECDH key exchange, AEAD encryption |
| `web4_demo.py` | Minimal handshake + ATP/ADP metering flow |
| `web4_reference_client.py` | Handshake + ATP roundtrip reference |
| `web4_crypto_stub.py` | Toy COSE/JWS facade (used by demo files) |
| `web4_full_stack_demo.py` | Integrated authorization + reputation + resource + MRH |
| `heartbeat_ledger.py` | Heartbeat-driven presence verification ledger |
| `heartbeat_verification.py` | Cross-machine heartbeat chain verification |
| `production_hardening.py` | P0 security hardening against attack vectors |

### TPM / Hardware Binding (5 .py)

| File | Implements |
|------|-----------|
| `tpm_binding.py` | TPM 2.0 bound LCT — hardware-rooted identity |
| `tpm_lct_identity.py` | tpm2-pytss based LCT key management with PCR sealing |
| `tpm_lct_simple.py` | Simplified tpm2-pytss API |
| `tpm_cli_bridge.py` | tpm2-tools CLI bridge (the working approach) |
| `hardware_binding_detection.py` | TPM/TrustZone/SecureBoot detection |

### Security / Attack Corpus (2 .py)

| File | Implements |
|------|-----------|
| `attack_mitigations.py` | 8 named mitigations for web4-specific attacks |
| `attack_demonstrations.py` | Concrete exploit demos for web4 attack vectors |

### Documentation (5 .md)

| File | Content |
|------|---------|
| `ATTACK_VECTOR_ANALYSIS.md` | 424+ attack vector catalog |
| `AUTHORIZATION_SYSTEM_DESIGN.md` | Authorization architecture |
| `WEB4_SECURITY_EP_TRILOGY.md` | Security EP system design |
| `hardware_binding_roadmap.md` | Hardware binding implementation plan |
| `RESEARCH_PROVENANCE.md` | Research provenance index |

### Key Artifacts (3 directories)

| Directory | Content |
|-----------|---------|
| `simple_tpm_keys/` | TPM key artifacts from working implementation |
| `tpm_cli_keys/` | TPM CLI key artifacts |
| `tpm_lct_keys/` | TPM LCT key artifacts |

## What Was ARCHIVED (149 items)

### Session-Specific Scripts (19)

Scripts named after specific research sessions — validation artifacts with no reuse value.

```
web4_session18_real_validation.py
web4_session19_diverse_scenarios.py
web4_session19_final_analysis.py
web4_session19_improved_state_logic.py
web4_session19_prediction_calibration_analysis.py
web4_session19_state_estimation_analysis.py
web4_session20_dual_context_validation.py
web4_session20_revalidation.py
web4_session22_cross_validation.py
web4_session22_learning_demo.py
web4_phase2b_demo.py
web4_phase2b_integrated_coordinator.py
web4_phase2c_circadian_coordinator.py
web4_phase2_demo.py
web4_phase2d_emotional_coordinator.py
test_phase2c_circadian.py
test_phase2c_sage_comparison_tuned.py
test_phase2c_sage_tuned.py
test_phase2c_with_sage_patterns.py
```

### SAGE Integration Experiments (19)

Cross-project integration with SAGE (separate project). Not web4 ontology implementations.

```
sage_authorization_integration.py
sage_federation_demo.py
sage_grounding_extension.py
sage_identity_bridge.py
sage_web4_bridge.py
cross_platform_pattern_exchange.py
demo_thor_pattern_import.py
temporal_pattern_exchange.py
pattern_exchange_protocol.py
universal_pattern_schema.py
web4_coordination_learning.py
web4_emotional_tracking.py
web4_phase_tagged_learning.py
web4_epistemic_coordinator_phase2.py
web4_epistemic_measurement_demo.py
web4_epistemic_observational_extension.py
web4_observational_framework.py
web4_observational_predictions.py
web4_unified_prediction_framework.py
```

### SAGE Coordinator Cluster (17)

Self-contained SAGE coordinator experiment suite. Import each other, not the web4 SDK.

```
web4_production_coordinator.py
web4_multi_ep_coordinator.py
web4_multi_objective_production.py
web4_multi_objective_workload_test.py
web4_coordinator_with_atp.py
web4_coordinator_benchmark.py
web4_coordination_epistemic_states.py
web4_quality_metrics.py
web4_telemetry.py
web4_temporal_adaptation.py
web4_performance_benchmark.py
web4_ep_performance_benchmark.py
long_duration_web4_validation.py
execute_long_duration_multi_objective_validation.py
validate_web4_temporal_adaptation.py
web4_longduration_validation.py
web4_security_integration_test.py
```

### Generic CS Algorithms with Trust-Themed Variables (13)

Standard CS/math/physics concepts using trust metaphors. Not web4-specific.

```
quantum_trust_evolution.py        # Schrödinger equation as trust dynamics
tidal_trust_decay.py              # Tidal stripping model as trust decay
cosmological_reputation_decay.py  # Friedmann equation as reputation decay
cosmic_coherence_reputation.py    # Cosmological coherence metrics
pattern_interaction_trust.py      # Synchronism C(ρ) applied to trust
sparse_network_reputation.py      # Network topology math
adversarial_testing.py            # Generic adversarial agent framework
salience_resource_allocation.py   # Generic signal processing
quality_coverage_resource_allocation.py  # Generic Pareto optimization
adaptive_atp_learning.py          # Evolutionary strategy optimization
multi_objective_web4_coordination.py     # Generic multi-objective optimization
empirical_authorization_model.py  # Curve fitting
production_atp_allocation.py      # Parameter tuning
```

### MRH Grounding / Coherence Cluster (14)

MRH grounding implementations tightly coupled to SAGE concepts (consciousness states,
circadian rhythms, CI regulation). Protocol concept is genuine but implementation
depends on SAGE internals, not web4 SDK.

```
grounding_lifecycle.py
grounding_quality_ep.py
coherence.py
coherence_aggregation_strategies.py
coherence_regulation.py
proportional_coherence_regulation.py
proportional_regulated_grounding.py
regulated_grounding_manager.py
lct_grounding_registry.py
authorization_ep.py
relationship_coherence_ep.py
extended_grounding_temporal_test.py
authorization_satisfaction_threshold.py
```

### Authorization/Reputation Demos (7)

Thin wrappers around KEEP files or integration demos.

```
authorization_demo.py
authorization_lct_integration.py
authorization_reputation_integration.py
authorization_resource_integration.py
law_oracle_demo.py
production_authorization_integration.py
test_advanced_attacks.py
```

### Test Files for Archived Modules (39)

Tests for the above archived modules. No value independent of their source files.

```
test_all_attack_mitigations.py
test_atp_demurrage.py
test_attack_mitigation_demurrage.py
test_authorization.py
test_bidirectional_learning.py
test_circadian_web4_integration.py
test_coherence_aggregation_comparison.py
test_coherence.py
test_coherence_regulation.py
test_emotional_long_duration.py
test_emotional_modulation.py
test_emotional_tracking.py
test_grounding_lifecycle.py
test_grounding_quality_ep.py
test_heartbeat_verification.py
test_integration_e2e.py
test_multisession_sage_accumulation.py
test_persistence_layer.py
test_phase_specific_learning.py
test_phase_tagged_extraction.py
test_postgresql_integration.py
test_production_crypto.py
test_proportional_coherence_regulation.py
test_proportional_regulated_grounding.py
test_protocol_sage_converters.py
test_real_sage_import.py
test_real_sage_import_v2.py
test_regulated_grounding_manager.py
test_relationship_coherence_ep.py
test_sage_grounding_extension.py
test_sage_longduration.py
test_security_attacks.py
test_session104_aggregation_fix_validation.py
test_spatial_coherence_tightening.py
test_temporal_pattern_transfer.py
test_trust_oracle.py
test_trust_tensors.py
test_web4_multi_ep_coordinator.py
test_web4_to_sage_transfer.py
test_witness_system.py
```

### Data / Log / JSON Files (14)

```
extended_temporal_test_results.json
longduration_output.txt
sage_patterns_export.json
sage_s42_for_longduration.json
sage_s42_real_patterns.json
sage_s42_real_patterns_v2.json
web4_coordinator_benchmark_results.json
web4_patterns_export.json
web4_predictions_catalog.json
web4_to_sage_export.json
test_phase2c_run1.log
test_sage_export_protocol.json
sage/                              # Subdirectory with data files
```

### Session Documentation (7)

```
emotional_to_coordination_mapping.md
FINDINGS_implicit_phase_learning.md
FINDINGS_phase2c_sage_integration.md
FINDINGS_quality_selectivity_tradeoff.md
SESSION105_TRACK2_AGGREGATION_VALIDATION.md
SESSION_19_RECOMMENDATION.md
SESSION_20_SUCCESS.md
tpm_phase2_validation.md
```

## Future Work

The 39 KEPT files are genuine web4 protocol references but do NOT import from the
canonical SDK (`web4.*`). They predate the SDK and implement concepts independently.
Candidates for future SDK migration (new sprint task needed):

- `trust_tensor.py` → concepts already in `web4.trust` (subset)
- `lct_registry.py` → concepts already in `web4.lct` (subset)
- `atp_demurrage.py` → not yet in SDK (demurrage is an ATP lifecycle concept)
- `authorization_engine.py` → full authorization pipeline (new module candidate)
- `law_oracle.py` → concepts in `web4.federation` (subset)
- `witness_system.py` → not yet in SDK (new module candidate)
- `mrh_graph.py` → concepts already in `web4.mrh` (subset, PR #6)
- TPM files → hardware binding integration (U2 in sprint plan)
