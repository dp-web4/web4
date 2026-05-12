# Implementation Directory Sprawl Triage

**Date**: 2026-05-12
**Directory**: `web4-standard/implementation/` (non-SDK, non-reference directories)
**Follows**: `docs/audits/reference-implementation-triage-2026-05-11.md` (PR #174, merged)
**Session**: `legion-web4-20260512-000012`

---

## Summary

Nine directories under `web4-standard/implementation/` form a **completely isolated sprawl island** — they reference each other but nothing in the production SDK (`web4/`) references them. Together they contain **121 Python files (~58,500 lines)** produced during autonomous sessions 30-34.

This triage extends the reference implementation audit by analyzing the dependency chain that kept 13 reference files classified as KEEP. Finding: those dependents are themselves sprawl. The entire chain (`reference/ → services/ → authorization/ → nothing`) is self-referential. No product code depends on any of these directories.

### Isolation proof

| Direction | Count | Verified by |
|-----------|-------|-------------|
| SDK → sprawl directories | **0 imports** | grep across all 70 SDK source files |
| Sprawl directories → SDK | **0 imports** | grep across all 121 sprawl files |
| SDK tests → sprawl | **0 imports** | grep across SDK test files |

---

## Directory-by-directory classification

### 1. services/ — ARCHIVE (15 .py files, ~7,400 lines)

Flask-style microservices wrapping reference/ modules. Docker Compose configuration for local deployment. No SDK integration.

| File | Lines | What it does | Imports from |
|------|-------|-------------|-------------|
| `authorization_service.py` | ~600 | Flask service wrapping `reference/authorization_engine` | reference/ |
| `governance_service.py` | ~500 | Flask service wrapping `reference/law_oracle` + `reference/mrh_graph` | reference/ |
| `identity_service.py` | ~400 | Flask service wrapping `reference/lct_registry` | reference/ |
| `identity_service_phase2.py` | ~500 | Phase 2 identity service | reference/ |
| `identity_service_secured.py` | ~500 | Secured identity service | reference/ |
| `knowledge_service.py` | ~400 | Flask service wrapping `reference/trust_oracle` | reference/ |
| `knowledge_service_secured.py` | ~500 | Secured knowledge service | reference/ |
| `reputation_service.py` | ~400 | Flask service wrapping `reference/reputation_engine` | reference/ |
| `reputation_service_secured.py` | ~500 | Secured reputation service | reference/ |
| `resources_service.py` | ~400 | Flask service wrapping `reference/resource_allocator` | reference/ |
| `resources_service_secured.py` | ~500 | Secured resources service | reference/ |
| `atp_manager.py` | ~400 | ATP allocation manager | reference/ |
| `metrics_registry.py` | ~300 | Prometheus metrics | stdlib |
| `test_all_services.py` | ~300 | Service test suite | services/ |
| `test_services.py` | ~200 | Service test suite | services/ |

**Also contains**: `docker-compose.yml`, `docker-compose.secured.yml`, `Dockerfile`, `prometheus.yml`, `requirements.txt`, `start_secured_services.sh`, `start_secured_simple.sh`, `README.md`, `*.log` files, `__pycache__/`

**Recommendation**: ARCHIVE. Flask services for nonexistent deployment. SDK provides its own trust resolution (`evaluate_trust_query`, `resolve_trust`, `process_action_outcome`) and MCP server for tool integration.

### 2. authorization/ — ARCHIVE (32 .py files, ~14,600 lines)

Authorization/delegation logic, SQL schemas, attack vector tests. Heavy overlap with SDK's security and trust modules.

| Category | Files | Lines | Description |
|----------|-------|-------|-------------|
| Core implementations | 13 | ~6,500 | delegation validators, trust APIs, permission stores, sybil resistance |
| Test files | 19 | ~8,100 | test suites for the above, plus attack vector tests |

**Also contains**: 10 `.sql` schema files, 5 `.md` documents, 1 `.json` file, `.py.backup`, `__pycache__/`

**Key imports**: `reference/authorization_engine`, `reference/crypto_verification`, `reference/law_oracle`, `reference/reputation_engine`

**Recommendation**: ARCHIVE. The SDK's `web4.security`, `web4.trust`, and `web4.attestation` modules provide the canonical implementations. The SQL schemas target a PostgreSQL backend that doesn't exist in the product.

### 3. integration_tests/ — ARCHIVE (2 .py files, ~840 lines)

Cross-service integration tests that import from both reference/ and services/.

| File | Lines | Tests |
|------|-------|-------|
| `test_identity_reputation_integration.py` | ~400 | Identity ↔ reputation cross-tests |
| `test_reputation_authorization_integration.py` | ~440 | Reputation ↔ authorization cross-tests |

**Also contains**: `README.md`, `__pycache__/`

**Recommendation**: ARCHIVE. Tests for sprawl services, not for the SDK.

### 4. act_deployment/ — ARCHIVE (50 .py files, ~25,900 lines)

Largest sprawl component. Contains deployment scenarios, attack simulations, and end-to-end demos that were produced as "federation activation toolkit" experiments.

| Category | Files | Lines | Description |
|----------|-------|-------|-------------|
| Deployment scenarios | ~15 | ~8,000 | Network deployment simulations, stress tests |
| Attack simulations | ~10 | ~5,000 | DDoS, Sybil, consensus attacks |
| E2E demos | ~10 | ~5,500 | Full-stack integration demos |
| Trust utilities | ~10 | ~5,000 | Trust computation, tensor operations |
| Misc | ~5 | ~2,400 | Helpers, configs |

**Recommendation**: ARCHIVE. Standalone experiments with no SDK integration. The SDK's test suite (2613 tests) covers the canonical implementations.

### 5. atp/ — ARCHIVE (2 .py files, ~800 lines)

ATP exchange experiments.

| File | Lines | Description |
|------|-------|-------------|
| `atp_exchange.py` | ~500 | ATP exchange protocol experiment |
| `atp_exchange_test.py` | ~300 | Test suite |

**Recommendation**: ARCHIVE. SDK has `web4.atp` module.

### 6. reputation/ — ARCHIVE (2 .py files, ~980 lines)

Reputation tracking experiments.

| File | Lines | Description |
|------|-------|-------------|
| `reputation_tracker.py` | ~600 | Reputation tracking core |
| `reputation_tracker_test.py` | ~380 | Test suite |

**Recommendation**: ARCHIVE. SDK has `web4.reputation` module.

### 7. security/ — ARCHIVE (11 .py files, ~5,600 lines)

Security mitigation experiments.

| Category | Files | Lines |
|----------|-------|-------|
| Core implementations | ~6 | ~3,500 |
| Test files | ~5 | ~2,100 |

**Recommendation**: ARCHIVE. SDK has `web4.security` module.

### 8. trust/ — ARCHIVE (4 .py files, ~2,000 lines)

Trust tensor experiments.

| File | Lines | Description |
|------|-------|-------------|
| Various trust experiments | 4 | ~2,000 |

**Recommendation**: ARCHIVE. SDK has `web4.trust` with T3Tensor/V3Tensor. Published Rust crate `web4-trust-core` provides high-performance tensors.

### 9. tests/ — ARCHIVE (3 .py files, ~300 lines)

Protocol edge-case tests not connected to SDK test suite.

**Recommendation**: ARCHIVE. SDK's own test suite (2613 tests, 97.8% coverage) is the canonical test set.

---

## Impact on reference/ KEEP files

The reference implementation triage (PR #174) classified 13 files as KEEP because they had dependents in services/ and authorization/. Now that services/ and authorization/ are confirmed as isolated sprawl:

**All 13 KEEP files downgrade to ARCHIVE.**

The dependency chain was: `reference/ → services/ → authorization/ → nothing`. With services/ and authorization/ classified as sprawl, the KEEP rationale dissolves.

### Updated reference/ classification

| Classification | Files | Lines | Previous | Change |
|---------------|-------|-------|----------|--------|
| ARCHIVE (previously) | 14 | 8,943 | Archived this session | — |
| ORPHAN (previously) | 1 | 308 | Archived this session | — |
| KEEP → ARCHIVE | 13 | 7,412 | KEEP | **Downgraded** |
| REVIEW | 3 | 392 | REVIEW | Unchanged (operator decision) |

---

## Totals

| Directory | Files (.py) | Lines | Classification |
|-----------|-------------|-------|---------------|
| services/ | 15 | ~7,400 | ARCHIVE |
| authorization/ | 32 | ~14,600 | ARCHIVE |
| integration_tests/ | 2 | ~840 | ARCHIVE |
| act_deployment/ | 50 | ~25,900 | ARCHIVE |
| atp/ | 2 | ~800 | ARCHIVE |
| reputation/ | 2 | ~980 | ARCHIVE |
| security/ | 11 | ~5,600 | ARCHIVE |
| trust/ | 4 | ~2,000 | ARCHIVE |
| tests/ | 3 | ~300 | ARCHIVE |
| reference/ KEEP→ARCHIVE | 13 | ~7,400 | ARCHIVE (downgraded) |
| **Total** | **134** | **~65,800** | |

Plus non-Python files (SQL, markdown, Docker, YAML, logs, JSON) in these directories.

---

## Directories that remain active

| Directory | Files | Role |
|-----------|-------|------|
| `sdk/` | 70+ | Production SDK (`web4/` package) — 2613 tests, v0.26.0 |
| `examples/` | 2 | `quickstart.py` + README — wired into CI |
| `guides/` | 1 | Developer guide |

---

## Recommended next steps

1. **Archive the 13 now-downgraded KEEP files** from `reference/` to `archive/reference-implementations/`
2. **Archive all 9 sprawl directories** to `archive/` (preserving directory structure)
3. **Operator decision on 3 REVIEW files** in `reference/` (crypto stub + demo pair)
4. **After archiving**: `implementation/` contains only `sdk/`, `examples/`, and `guides/` — clean product structure

---

*Produced by autonomous session `legion-web4-20260512-000012` under v2 protocol. Classification only — no files were moved, deleted, or modified in this triage.*
