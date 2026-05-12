# Reference Implementation Triage

**Date**: 2026-05-11
**Directory**: `web4-standard/implementation/reference/`
**Authorization**: Issue #166 candidate (a)-2
**Session**: `legion-web4-20260511-180014`

---

## Summary

The `reference/` directory contains **31 Python files** (17,017 lines) plus 4 markdown files. These were produced during autonomous sessions 30-34 as "reference implementations" of web4 subsystems. The primer identifies this body of work as academic sprawl — standalone reimplementations of web4 concepts that don't integrate with the published SDK (`web4-standard/implementation/sdk/web4/`).

This audit classifies each file to enable informed archive/keep decisions.

### Counts

| Classification | Files | Lines | Notes |
|---------------|-------|-------|-------|
| ARCHIVE | 15 | 8,943 | Standalone, no dependents outside reference/ |
| KEEP (cluster) | 13 | 7,412 | Interconnected integration cluster |
| ORPHAN | 1 | 308 | Imports from deleted game prototype |
| REVIEW | 2 | 354 | Small protocol stubs, partially integrated |
| **Total** | **31** | **17,017** | |

---

## Classification Criteria

- **ARCHIVE**: No imports from or to other reference files. No dependents outside `reference/` (excluding `archive/`). Reimplements concepts already in the SDK or in published Rust crates.
- **KEEP**: Part of the interconnected integration cluster. Has dependents in `web4-standard/implementation/services/` or `web4-standard/implementation/authorization/`. Removing would break other active (non-archived) code.
- **ORPHAN**: Imports from deleted/archived code. Non-functional as-is.
- **REVIEW**: Edge cases requiring operator judgment.

---

## ARCHIVE — 15 files (8,943 lines)

These files are standalone: they import only from the Python standard library (or external pip packages like `cryptography`, `nacl`, `psycopg2`). No other reference file imports them. No active code outside `reference/` imports them.

| File | Lines | What it implements | SDK equivalent | External deps |
|------|-------|-------------------|----------------|---------------|
| `attack_mitigations.py` | 557 | Advanced attack mitigations (rate limiting, stake verification, Sybil detection) | `web4.security` module | None |
| `hardware_binding_detection.py` | 484 | TPM/FIDO2/SE capability detection via subprocess | `web4.attestation` (AttestationEnvelope) + `web4-core` (Rust) | None |
| `heartbeat_ledger.py` | 813 | Append-only heartbeat ledger with timing validation | `web4-core` LocalLedger (Rust, published) | None |
| `heartbeat_verification.py` | 664 | Cross-machine heartbeat chain verification | `web4-core` ledger chain verification (Rust) | None |
| `lct_capability_levels.py` | 1,053 | LCT capability level system (5 tiers) | `web4.lct` + `web4.capability` | None |
| `persistence_layer.py` | 935 | PostgreSQL persistence for LCT/delegations/witnesses | No SDK equivalent (SDK is in-memory) | `psycopg2` |
| `production_crypto.py` | 795 | Production-grade Ed25519/X25519/AESGCM operations | `web4-core` crypto module (Rust, published) | None |
| `production_hardening.py` | 821 | Rate limiters, circuit breakers, secure key storage | `web4.security` + production concerns | None |
| `tpm_binding.py` | 739 | TPM 2.0 key binding for LCTs | `web4.attestation` + `web4-core` (Rust) | None |
| `tpm_cli_bridge.py` | 414 | TPM via tpm2-tools CLI subprocess | `web4.attestation` (higher-level) | `tpm2-tools` (CLI) |
| `tpm_lct_identity.py` | 545 | TPM-based LCT identity (Phase 2) | `web4.attestation` + `web4-core` | None |
| `tpm_lct_simple.py` | 272 | Simplified TPM LCT binding | `web4.attestation` (simplified) | None |
| `trust_tensor.py` | 661 | T3/V3 tensor implementation | `web4.trust` (T3Tensor, V3Tensor) + `web4-trust-core` (Rust) | None |
| `web4_client.py` | 290 | Reference client with handshake/session | No direct SDK equivalent | `cryptography`, `nacl` |
| **Subtotal** | **8,943** | | | |

### Notes on ARCHIVE files

1. **TPM cluster** (4 files, 1,970 lines): `tpm_binding.py`, `tpm_cli_bridge.py`, `tpm_lct_identity.py`, `tpm_lct_simple.py` represent iterative attempts at hardware binding. The published Rust `web4-core` crate and the SDK's `attestation.py` module supersede these. The Rust `identity_bootstrap.py` example demonstrates the canonical approach.

2. **Heartbeat pair** (2 files, 1,477 lines): `heartbeat_ledger.py` and `heartbeat_verification.py` implement ledger timing concepts now handled by `web4-core`'s `LocalLedger` (Rust, with chain integrity verification).

3. **Trust tensor** (1 file, 661 lines): `trust_tensor.py` is a pure-Python reimplementation. The SDK has `web4.trust` (T3Tensor, V3Tensor). The published Rust `web4-trust-core` crate provides high-performance tensor operations with PyO3 bindings.

4. **PostgreSQL persistence** (1 file, 935 lines): `persistence_layer.py` is the only file implementing database-backed storage. The SDK is deliberately in-memory. This file could inform a future persistence layer but is not importable as-is (hardcoded schemas, no interface alignment with SDK types). Flagged as ARCHIVE rather than MERGE because the SDK uses its own dataclass serialization (to_dict/from_dict) and the Rust crates use their own storage traits.

5. **Production crypto/hardening** (2 files, 1,616 lines): These implement operational concerns (rate limiting, circuit breakers, key management). The published Rust crate handles crypto; operational concerns belong in deployment tooling, not the SDK.

---

## KEEP — 13 files (7,412 lines)

These files form an **interconnected integration cluster** — they import from each other and are imported by active code in `web4-standard/implementation/services/` and `web4-standard/implementation/authorization/`.

### Dependency graph

```
web4_full_stack_demo.py ──┬── lct_registry.py
                          ├── law_oracle.py ◄── authorization_engine.py
                          ├── authorization_engine.py ──┬── trust_oracle.py
                          │                             ├── crypto_verification.py
                          │                             └── law_oracle.py
                          ├── reputation_engine.py
                          ├── resource_allocator.py
                          └── mrh_graph.py

attack_demonstrations.py ─┬── authorization_engine.py
                          ├── reputation_engine.py
                          └── resource_allocator.py

witness_system.py ───────── crypto_verification.py

demurrage_service.py ────── atp_demurrage.py
```

### External dependents (non-archived code that imports these modules)

| Reference file | Imported by (outside reference/) |
|---------------|--------------------------------|
| `authorization_engine.py` | `services/authorization_service.py`, `authorization/test_authorization.py`, `authorization/test_delegation_system.py` |
| `crypto_verification.py` | `authorization/delegation_validator.py` |
| `law_oracle.py` | `services/governance_service.py`, `authorization/test_delegation_validator.py` |
| `lct_registry.py` | `services/identity_service.py`, `services/identity_service_phase2.py`, `services/identity_service_secured.py` |
| `reputation_engine.py` | `services/reputation_service.py`, `services/reputation_service_secured.py`, `authorization/reputation_service.py`, `integration_tests/test_reputation_authorization_integration.py` |
| `resource_allocator.py` | `services/resources_service.py`, `services/resources_service_secured.py` |
| `trust_oracle.py` | `services/knowledge_service.py`, `services/knowledge_service_secured.py` |
| `mrh_graph.py` | `services/governance_service.py` |

### Per-file details

| File | Lines | Role | Dependents |
|------|-------|------|------------|
| `authorization_engine.py` | 586 | Runtime authorization verification | 3 external |
| `crypto_verification.py` | 396 | Ed25519 signature verification | 1 external |
| `law_oracle.py` | 786 | Rules/norms/procedures authority | 2 external |
| `lct_registry.py` | 709 | LCT identity management | 3 external |
| `reputation_engine.py` | 542 | T3/V3 reputation delta computation | 4 external |
| `resource_allocator.py` | 503 | ATP-to-resource mapping | 2 external |
| `trust_oracle.py` | 489 | PostgreSQL-backed trust queries | 2 external |
| `mrh_graph.py` | 745 | RDF-based entity relationship graph | 1 external |
| `atp_demurrage.py` | 600 | ATP decay mechanics | 0 external (only demurrage_service.py) |
| `demurrage_service.py` | 412 | Background ATP demurrage service | 0 external |
| `attack_demonstrations.py` | 412 | Attack vector demonstrations | 0 external |
| `web4_full_stack_demo.py` | 492 | Full-stack integration demo | 0 external |
| `witness_system.py` | 713 | Witness attestation system | 0 external |

### Important caveat

The "external dependents" listed above are themselves part of the broader implementation sprawl — `services/`, `authorization/`, and `integration_tests/` directories contain code generated during the same drift period. None of these services are imported by the SDK (`web4/`), published as packages, or used in CI. They form a self-referential cluster of reference implementations.

**Recommendation**: Classify the KEEP files as "KEEP PENDING SERVICES TRIAGE." If a future session triages `services/` and `authorization/` and determines they are also sprawl, these KEEP files downgrade to ARCHIVE. The dependency chain is: `reference/ → services/ → nothing`. The SDK (`web4/`) is completely independent.

---

## ORPHAN — 1 file (308 lines)

| File | Lines | Issue |
|------|-------|-------|
| `trust_tensors.py` | 308 | Imports from `game.engine.mrh_aware_trust.T3Tensor` — the game prototype is archived at `archive/game-prototype/`. This file cannot execute. |

**Recommendation**: ARCHIVE. The SDK's `web4.trust.T3Tensor` supersedes this entirely.

---

## REVIEW — 2 files (354 lines)

| File | Lines | Issue |
|------|-------|-------|
| `web4_crypto_stub.py` | 66 | Toy crypto facade (non-production). Imported by `web4_demo.py` and `web4_reference_client.py`. Together these 3 files form a minimal protocol handshake demo. |
| `web4_demo.py` | 177 | Handshake + session key derivation demo using `web4_crypto_stub`. Also exists as a copy in `forum/nova/`. |

The stub+demo pair is a self-contained protocol walkthrough. It doesn't overlap with the SDK (which doesn't implement protocol handshakes). It's small enough (243 lines combined) to keep as documentation of the handshake concept, or archive as superseded by the published Rust crate's examples.

`web4_reference_client.py` (38 lines) imports `web4_crypto_stub` but via `implementation.reference.web4_crypto_stub` — suggesting it was designed to run from outside the directory. It's a minimal ATP/ADP roundtrip demo.

**Recommendation**: Operator choice. These are small, self-contained, and illustrative. KEEP as protocol documentation or ARCHIVE as superseded by `web4-core/examples/`.

---

## Markdown files (not classified — documentation)

| File | Lines | Content |
|------|-------|---------|
| `ATTACK_VECTOR_ANALYSIS.md` | — | Attack vector analysis document |
| `AUTHORIZATION_SYSTEM_DESIGN.md` | — | Authorization system design document |
| `hardware_binding_roadmap.md` | — | Hardware binding roadmap |
| `RESEARCH_PROVENANCE.md` | — | Research provenance for sparse network reputation parameters |
| `WEB4_SECURITY_EP_TRILOGY.md` | — | Security EP trilogy document |

These documents are reference material. They don't have import dependencies. Recommend keeping with the KEEP cluster or moving alongside archived files as provenance documentation.

---

## Summary of findings

1. **15 files (8,943 lines) are immediately archivable** — standalone reimplementations with no dependents outside the directory.

2. **13 files (7,412 lines) form an integration cluster** with dependents in `services/` and `authorization/` — but those dependents are themselves unused by the SDK or any published artifact. The entire chain (`reference/ → services/ → nothing`) is self-referential sprawl.

3. **1 file (308 lines) is orphaned** — imports from deleted code.

4. **2 files (354 lines) are edge cases** — small protocol demos that could go either way.

5. **The SDK (`web4/`) imports nothing from `reference/`**. The published Rust crates (`web4-core`, `web4-trust-core`) have no relationship to these files. The `reference/` directory is an island.

6. **Total archivable (ARCHIVE + ORPHAN)**: 16 files, 9,251 lines (54% of directory).
   **Total pending services triage (KEEP)**: 13 files, 7,412 lines (44% of directory).
   **Total operator-review (REVIEW)**: 2 files, 354 lines (2% of directory).

---

## Recommended next steps

1. **Archive 16 files** (ARCHIVE + ORPHAN) to `archive/reference-implementations/` — many already have companion test files there.
2. **Triage `services/` and `authorization/`** — if these are also sprawl (likely), the 13 KEEP files downgrade to ARCHIVE.
3. **Operator decision on REVIEW files** — keep as protocol documentation or archive.
4. **After archiving**: the `reference/` directory either becomes empty (if services are also triaged) or contains only the integration cluster (13 files serving as a dependency backbone for `services/`).

---

*Produced by autonomous session `legion-web4-20260511-180014` under v2 protocol. Classification only — no files were moved, deleted, or modified.*
