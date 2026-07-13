# Web4 Changelog

This file consolidates release notes across the package family. Per-package CHANGELOGs may have more granular history (e.g. `web4-standard/implementation/sdk/CHANGELOG.md`).

The Web4 package family currently consists of:

- **`web4-sdk`** (Python) — high-level SDK at `web4-standard/implementation/sdk/` (previously published on PyPI as `web4`; renamed because that PyPI name is held by an unrelated dormant project). `import web4` unchanged.
- **`web4-core`** (Python + Rust crate) — core primitives, PyO3 bindings. `pip install web4-core` / `cargo add web4-core`.
- **`web4-trust`** (Python wheel) / **`web4-trust-core`** (Rust crate + npm WASM bindings) — trust tensors and the trust ledger. `pip install web4-trust` / `cargo add web4-trust-core` / `npm install web4-trust-core`.

## web4-core Unreleased (0.4.0)

- **FIX (spec conformance, audit C192-N1): Talent no longer decays through inactivity.**
  `T3::decay` (web4-core) and `t3_apply_decay` (web4-trust-core) both violated protocol
  invariant t3v3-012 ("Talent MUST NOT decay") — trust-core used the LITERAL `0.995` value
  spec §10.4 names as violating. Talent score, weight, and Talent-parented sub-dimensions
  now pass through untouched (matching the Python SDK reference). Live via public
  `EntityTrust::apply_decay`; no known production caller in the fleet, so no stored trust
  needs repair.

- **BREAKING (Rust + JS/wasm): `compute_reputation` signature** — now takes the subject's real
  tensor baselines: `compute_reputation(quality, t3_from, v3_from, rule, reason, factors)`
  (wasm: `computeReputation(quality, t3From, v3From, rule, reason)`). Previously `from_value`
  was fabricated as `0.5` and `change` could exceed the clamped movement; now `from`/`to` are
  real and `change = to − from` post-clamp. Migration: pass your subject's current T3/V3
  averages (use `0.5, 0.5` only for genuinely neutral subjects).

## web4-core 0.3.0 — 2026-07-09 (single-package release)

`web4-core` only (Rust crate + Python wheel); the trust family stays at 0.2.0. Closes the 18-commit gap accumulated since 0.2.0 (2026-05-15). 171 tests green at publish; `cargo publish --dry-run` + fresh-venv wheel install verified first. Tags: `web4-core-rust-v0.3.0`, `web4-core-py-v0.3.0`.

### Added

- **Role entities** (#489): `RoleEntity` / `RoleExtension` / `RoleRegistry` — orchestration roles as first-class `EntityType::Role` LCTs with typed affordances (Tool/Channel/Repo/WriteClass/CliFlag), responsibilities, MRH scope + ATP budget, and sovereign-issued LCT binding. The Phase-1→2 bridge for role orchestration (and the load-bearing primitive for foreign-agent onboarding).
- **Act primitive + time/events axis** (#369, #384): witnessed action grammar with `Act.kind`, `requires_council` as default-not-law, and `ReputationDelta`.
- **Constellation role enum + provenance-strength fold** (#457): published capacity roles; `SovereignStrength` fail-closed to `Placeholder` for non-hub-verified claims.
- **Recursive vault** (`web4_core::vault`): Argon2id + ChaCha20-Poly1305, per-item independent locking, memory-only unlock, `DerivedKey::from_bytes`, self-framing seal/open.
- **EUDI / W3C-DID stack** (`did` / `sd_jwt_vc` / `oid4vc`): signer-agnostic SD-JWT-VC issuance, OID4VCI holder-proof, `jwt_payload_claim` for external-signer validation, unverified peek helpers.

### Changed

- **Canonical T3/V3** (#445): `EntityTrust` migrated to the canonical `web4_core::t3::T3` / `v3::V3` tensor types — one tensor source across the dependency graph.

### Fixed

- **`RoleExtension` defaults + `affords()` were fail-OPEN** (#492, CBP review F1–F3 on #489): affordance checks now fail closed — absence is denial.

## 0.2.0 — 2026-05-15 (package family release)

First coordinated release closing the publish-vs-main gap flagged by Nova 2026-05-15. Brings `web4-core`, `web4-trust-core` (Rust + Python + npm WASM) up to the body of work accumulated since April 28 v0.1.1 — roughly 17 days and 66 commits of substantive spec, SDK, and conformance work.

### Spec additions

- **Inter-society protocol** (`core-spec/inter-society-protocol.md`): society genesis (self-bootstrapped + federation-based), three-option first-contact protocol, ATP reification sovereignty (form/substance distinction), secession/dissolution, witnesses-as-encompassing-society notaries.
- **Society roles** (`core-spec/society-roles.md`): three-tier role taxonomy (base-mandatory / context-mandatory / optional), corporate analogues (Sovereign / Law Oracle / Policy-Entity / Treasurer / Administrator / Archivist / Citizen), fractal composability semantics, audit implications.
- **MCP protocol** amendments (`core-spec/mcp-protocol.md`):
  - §1.1 MCP as the inter-society interface (per the Web4 equation, MCP IS the cross-society interaction layer)
  - §7.3 MCP actions as R7 transactions
  - §7.4 Cross-society LCT envelope
  - §7.5 Cross-society witnessing and R7 reputation propagation
  - §7.6 Cross-society R7 failure modes
  - §7.7 (WIP) Referent-grounded exchange rate negotiation

### SDK additions (`web4-sdk` 0.27.0, formerly published as `web4`)

- Society Roles module: `SocietyRole`, `RoleAssignment`, `bootstrap_society_roles`
- Cross-society types: `CrossSocietyContext`, `ReputationEnvelope`, `MCPContextResource`
- Constraint alignment with Rust (`threshold` + `hard`) — full cross-language parity
- Conformance test runner: 35 vectors, 39 tests (8 xfailed gaps documented)
- `validate_minimum_viable()` for cross-language parity with Rust
- 23 modules, 369 exports, 2709 tests

### Conformance + cross-language parity

- 35 operator-created conformance test vectors at `testing/conformance/`, wired into pytest (Sprint 52)
- T3/V3 specs-schemas-Python-Rust alignment (web4-core: 38 tests; web4-trust-core: 57 tests)
- WASM bindings published for Society, SocietyRole, RoleAssignment, ATPAccount, R7Action

### Documentation discipline

- README "Findings vs Framings" split (quantitative findings vs theoretical framings/positions)
- Authorship & Methodology disclosure (work is substantially AI-assisted; documented as a relevant methodological fact)
- Whitepaper refactor to match the README discipline (Appendix J: Authorship & Methodology, Findings/Framings table in Conclusion)
- Linux/GNU/distribution framing replaces TCP/IP analogy in README positioning

### Packaging notes

- **PyPI rename**: the Python SDK is now `web4-sdk` (previously `web4`). The PyPI name `web4` is held by an unrelated dormant project (author Sahil Prasad, continual.ai, last release 0.0.1). Renaming avoids ambiguity. The Python import path is unchanged — `from web4 import ...` works as before.
- **First-time publishes**: `web4-core` (Rust crate, crates.io), `web4-trust-core` (Rust crate, crates.io), `web4-trust` (Python wheel, PyPI), `web4-trust-core` (npm WASM). Previously these were tagged in git but never published to their respective registries.

## Earlier history

- **0.1.1 (2026-04-28)** — fix Python import path (`web4_core/__init__.py` missing in 0.1.0 was yanked), canonical T3/V3 docstring framing.
- **0.1.0 (2026-04-27)** — initial release of `web4-core` and `web4-trust-core` to PyPI / crates.io tagged but not all channels populated (yanked on PyPI due to broken import path; see 0.1.1).

For pre-0.1 history, see the per-package CHANGELOGs and the SDK-specific changelog at `web4-standard/implementation/sdk/CHANGELOG.md`.
