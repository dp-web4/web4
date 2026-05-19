# Web4 Sprint Plan

**Created**: 2026-03-14
**Updated**: 2026-05-19 (Sprint 55)
**Phase**: Development
**Track**: web4 (Legion)

---

## Sprint 55: SDK v0.28.0 Release Housekeeping (2026-05-19)

Version bump and documentation update consolidating post-Sprint-53 work:
cross-society MCP types (PR #195/#199), conformance xfail resolution (PR #210),
and the informal C-series audit/remediation thread (PRs #197, #200-#211).

### T1: v0.28.0 release housekeeping
**Status**: DONE
**Completed**: 2026-05-19
**Authorized by**: Established release housekeeping pattern (Sprints 21, 23,
26, 31, 33, 34, 39, 53). Policy-reviewed and approved.
**Scope**:
1. Version bump 0.27.0 -> 0.28.0 in `pyproject.toml`.
2. CHANGELOG entry for v0.28.0 covering PRs #195, #199, #210.
3. `__init__.py` docstring: corrected stale counters (exports 369->376,
   tests 2709->2749), updated version note.
4. README: version, export count (369->376), test count (2709->2749),
   error categories (6->7 with Cross-Society), project structure counts.
5. `examples/quickstart.py`: docstring version.
6. Test assertions: version strings in `test_cli.py` and `test_package_api.py`.
7. `docs/SPRINT.md` and `SESSION_FOCUS.md` updated.

**Result**: 0 new files. All version references consistent. 376 exports,
2749 tests (2744 passed, 5 xfailed conformance gaps).

---

## Sprint 54: Spec Audit & Remediation Series (2026-05-15 – 2026-05-18)

Informal C-series: internal-consistency audits of `mcp-protocol.md` (C1/C2)
and `presence-protocol.md` (C5), §7.7 promotion tracking (C3), vector-freshness
process (C4), and remediation PRs resolving audit findings. Also includes
cross-society SDK types and conformance xfail resolution.

**Note**: This sprint was not formally defined in advance. Work was proposed
and policy-reviewed per session under v2 protocol. Recorded here retroactively
as the formal Sprint 54 entry for continuity.

### Work completed (PRs #195–#211)
**Status**: DONE
**Key deliverables**:
- **C1**: MCP Protocol ↔ SDK alignment audit (`docs/audits/mcp-protocol-sdk-alignment-2026-05-15.md`)
- **C2**: mcp-protocol.md internal-consistency audit (13 findings: 4 HIGH, 5 MEDIUM, 4 LOW) → PRs #200, #201, #203
- **C3**: §7.7 promotion tracking stub (`docs/audits/s7.7-promotion-tracking-2026-05-16.md`) → PR #202
- **C4**: Vector-freshness check process → PR #197
- **C5**: presence-protocol.md internal-consistency audit (2 HIGH, 6 MEDIUM, 5 LOW) → PRs #206, #207, #208, #209
- **SDK**: Cross-society types (PR #195), test coverage (PR #199), 3 conformance xfails resolved (PR #210)
- **Docs**: CHANGELOG staleness resolved (PR #211), whitepaper no-change checks

---

## Sprint 53: SDK v0.27.0 Release Housekeeping (2026-05-15)

Version bump and documentation update consolidating Sprints 41-42 and 50-52
into a coherent release marker. Covers the Society Roles module (Sprint 50),
Constraint alignment (Sprint 51), conformance test runner (Sprint 52),
dead code removal (Sprint 41), and CI quickstart smoke (Sprint 42).

### T1: v0.27.0 release housekeeping
**Status**: DONE
**Completed**: 2026-05-15
**Authorized by**: Established release housekeeping pattern (Sprints 21, 23,
26, 31, 33, 34, 39). Policy-reviewed and approved.
**Scope**:
1. Version bump 0.26.0 -> 0.27.0 in `pyproject.toml`.
2. CHANGELOG entry for v0.27.0 covering Sprints 41-42, 50-52.
3. `__init__.py` docstring: corrected stale counters (tests 2668->2709),
   added v0.27.0 version note, added missing `validate_minimum_viable` export.
4. `__main__.py`: added `role` to both `_cmd_info` and `_SELFTEST_MODULES`
   module lists (was 22, now 23 — Sprint 50 added `web4/role.py` but the
   CLI lists were not updated).
5. README: version, module count (22->23), export count (364->369), test
   count (2613->2709), added `role` row to module table, project structure
   section updated.
6. `examples/quickstart.py`: docstring version.
7. Test assertions: version strings in `test_cli.py` and `test_package_api.py`,
   module count assertions (22->23).
8. `docs/SPRINT.md` and `SESSION_FOCUS.md` updated.

**Result**: 0 new files, 0 new exports beyond the missing `validate_minimum_viable`
(369 total). All version references consistent. CLI now reports 23 modules.

---

## Sprint 52: Conformance Test Vector Runner (2026-05-14)

Wires the operator-created conformance test vectors (`web4-standard/testing/
conformance/`, commit `0c39a9b6`) into the Python SDK's pytest suite. The
35 vectors across 4 suites define cross-language behavioral properties that
all Web4 implementations must satisfy. Addresses Kimi's K2 gap (conformance
test suite).

### T1: Wire conformance vectors into pytest
**Status**: DONE
**Completed**: 2026-05-14
**Authorized by**: Operator signal (conformance vectors in direct-to-main
commits). Policy-reviewed and approved.
**Scope**:
New `tests/test_conformance.py` exercising 35 vectors across 4 suites:
- **Tensor operations** (8 vectors): T3/V3 construction, update, level
  thresholds, decay
- **ATP operations** (11 vectors): account lifecycle, transfers, conservation,
  sliding scale
- **R6/R7 actions** (8 vectors): validation, reputation deltas, hash
  determinism, role contextualization
- **Society/roles** (8 vectors): bootstrap, lifecycle, rotation, multi-holder,
  minimum viable validation

**Result**: 39 tests (31 passed, 8 xfailed conformance gaps), 1 new file.
2709 total tests (2701 passed, 8 xfailed). mypy --strict clean, ruff
lint/format clean.

**Conformance gaps documented** (8 xfail):
1. T3 aggregate: weighted vs unweighted mean (Sprint 47 audit class)
2. T3 update: success flag ignored (quality-only direction in SDK)
3. T3 decay: talent invariant vs vector expecting decay
4. V3 reputation: valuation not in behavioral update (economic dimension)
5. Constraint checking: validate() defers to PolicyGate
6. Role assignment authorization: governance-layer check not in data types
7. Federation join/secede: different API shape than incorporate_child()
8. Sub-dimension rollup: ontology-defined but not runtime-implemented

---

## Sprint 51: Minimum Viable Society Validation + Constraint Alignment (2026-05-14)

Resolves two remaining autonomous-actionable items from the Sprint 49
cross-language audit fix queue: P5 (validate_minimum_viable) and P6
(Constraint threshold + hard flag alignment).

### T1: validate_minimum_viable() + Constraint alignment
**Status**: DONE
**Completed**: 2026-05-14
**Authorized by**: Sprint 49 audit fix queue P5+P6. Policy-reviewed and approved.
**Scope**:
1. **P5 — `validate_minimum_viable()`**: New function in `web4/role.py` per
   `inter-society-protocol.md` §6.2 and Rust `Society::validate_minimum_viable()`.
   Checks base-mandatory completeness, internal differentiation (≥2 fillers when
   operational), witnessing capacity (Witness or Auditor when operational).
2. **P6 — Constraint alignment**: Updated `Constraint` dataclass in `web4/r6.py`
   from `value: Any` to `threshold: float` + `hard: bool = True`. Updated
   serialization, JSON schemas, and test vectors.

**Result**: 1 new export (369 total), 12 new tests (2668 total), 0 new files.
mypy --strict clean, ruff lint/format clean.

**Remaining from audit**: P4 (MetabolicState — needs operator decision),
P7 (role integration — needs operator decision).

---

## Sprint 50: Add SocietyRole + RoleAssignment to Python SDK (2026-05-14)

Implements the top 3 items from the Sprint 49 cross-language audit fix queue:
P1 (CRITICAL: add SocietyRole enum), P2 (HIGH: RoleAssignment with role-LCT
binding), P3 (HIGH: solo-founder bootstrap). Achieves cross-language parity
with `web4-core/src/role.rs` for the core role types.

### T1: SocietyRole enum + RoleAssignment dataclass + bootstrap_society_roles()
**Status**: DONE
**Completed**: 2026-05-14
**Authorized by**: Sprint 49 audit fix queue P1+P2+P3. Policy-reviewed and approved.
**Scope**:
New `web4/role.py` module implementing:
- `SocietyRole` enum: 7 base-mandatory roles (Sovereign, LawOracle, PolicyEntity,
  Treasurer, Administrator, Archivist, Citizen) + 2 context-mandatory (Witness,
  Auditor). `str` mixin for JSON-friendly serialization. `is_base_mandatory`
  property, `description` property.
- `RoleAssignment` dataclass: role-LCT binding (authority binds to role, not
  filling entity), T3/V3 per role, `rotate()` (entity rotation preserving
  role-LCT), `add_holder()`/`remove_holder()` (committee/federation pattern),
  `is_authorized()`, `to_dict()`/`from_dict()` round-trip serialization.
- `bootstrap_society_roles()`: solo-founder genesis per `inter-society-protocol.md`
  §2.1 — creates 7 base-mandatory role assignments with the founder filling every
  role. Custom `role_lct_factory` support. Resolves the `len(founders) >= 2`
  contradiction in `create_society()`.
- `BASE_MANDATORY_ROLES` constant: ordered list of the 7 base-mandatory roles.

**Result**: 4 new exports (368 total), 43 new tests (2656 total), 1 new module
(23 total + MCP server). mypy --strict clean, ruff lint/format clean. Cross-language
parity with `web4-core/src/role.rs::SocietyRole` and `RoleAssignment`.

**Remaining from audit**: P4 (MetabolicState reconciliation — needs operator
decision), P5 (validate_minimum_viable — depends on P1, now unblocked), P6
(Constraint hard flag), P7 (SocietyState integration — needs operator decision).

---

## Sprint 49: Cross-Language Society/Role/ATP/R6 Alignment Audit (2026-05-14)

Operator commits `82438958` and `8857ab09` added 4 new Rust modules to `web4-core`
(society.rs, role.rs, atp.rs, r6.rs) implementing concepts from the new specs
(`society-roles.md`, `inter-society-protocol.md`). The Python SDK has corresponding
modules built against older specs. Sprint 49 applies the Sprint 47 audit methodology
to these new modules, documenting cross-language divergences before they become
entrenched.

### T1: Cross-language alignment audit for Society/Role/ATP/R6
**Status**: DONE
**Completed**: 2026-05-14
**Authorized by**: Operator signal via 8 direct-to-main commits adding new specs + Rust SDK modules. Same audit pattern as Sprint 47 T1.
**Scope**:
Systematic comparison of 4 new Rust SDK modules against Python SDK counterparts
and canonical specs. Documented 14 items: 1 CRITICAL (Python SDK missing
SocietyRole/RoleAssignment entirely), 3 HIGH (genesis protocol mismatch,
MetabolicState divergence, no role-LCT binding), 3 MEDIUM (Constraint structure,
ActionStatus mismatch, composite architecture), 4 LOW (naming, utilities, JSON-LD).
ATP module is the best-aligned pair (identical core semantics). Produced prioritized
fix queue (P1-P7) with 2 operator decisions required (MetabolicState model, role
integration architecture).
**Result**: Audit at `docs/audits/cross-language-society-role-atp-r6-alignment-2026-05-14.md`.
Key finding: the Python SDK was built before `society-roles.md` existed and lacks
the entire 7-role taxonomy. Unlike Sprint 47 findings (which required Rust toolchain),
P1-P3/P5-P7 are autonomous-actionable from this repo (Python SDK changes). P4
(MetabolicState reconciliation) requires operator design input. 1 new file, 2
bookkeeping files modified.

---

## Sprint 48: Parameter Governance Index (2026-05-13)

The spec-vs-explainer alignment audit (Sprint 43 T1) includes Unanswered
Question #3: "Who decides the parameters? (MRH decay rate, CI multiplier,
trust thresholds)." The question was partially blocked by item #10 (CI
canonicity), which Sprint 46 T1 resolved. With that dependency cleared,
the parameter governance decisions scattered across Sprints 44, 46, and
existing spec text can be synthesized into a single normative index.

### T1: Parameter governance index in t3-v3-tensors.md
**Status**: DONE
**Completed**: 2026-05-13
**Authorized by**: Downstream from Sprint 43 audit (Unanswered Question #3), unblocked by Sprint 46 T1 (item #10 resolved). Recommended by peer session 120024's queue-state analysis (Sub-option A).
**Scope**:
Add §10 "Parameter Governance" to `t3-v3-tensors.md` — classifies all
trust, value, and energy parameters into three governance tiers:
protocol-invariant (MUST — enforced by test vectors), society-configurable
(MAY — published in governance laws), and simulation-only (not protocol
parameters). Synthesizes decisions from §2.3 (Talent no-decay invariant,
Training/Temperament decay configurability), `atp-adp-cycle.md` §6.3/§7
(transfer fees, ATP decay rates, demurrage), and
`multi-device-lct-binding.md` §4.4 (constellation_coherence as simulation
parameter). Cross-references rather than duplicates existing normative text.
**Result**: A developer or autonomous session can now answer "who decides
this parameter?" for any trust/value/energy tunable by reading one section.
Resolves Unanswered Question #3 from the spec-vs-explainer audit. Remaining
audit items (#13 synthons, #14 karma) still require operator design
decisions. 0 new files, 1 spec file modified, 2 bookkeeping files modified.

---

## Sprint 47: Cross-Language T3/V3 Alignment Audit (2026-05-13)

Operator commit `55b1a3d8` rebuilt the web4-trust-core WASM package with canonical
3D tensor names ("Driven by Hardbound alignment audit"). Exploration revealed that
the naming surface is now correct but the behavioral semantics — composite calculation,
update formulas, decay model — remain significantly divergent from the canonical test
vectors and Python SDK. Sprint 47 documents these divergences as an actionable audit.

### T1: Cross-language T3/V3 semantic alignment audit
**Status**: DONE
**Completed**: 2026-05-13
**Authorized by**: Operator signal in commit `55b1a3d8` (hardbound alignment audit)
**Scope**:
Systematic comparison of `web4-trust-core/src/tensor/` (Rust) against canonical test
vectors (`web4-standard/test-vectors/t3v3/tensor-operations.json`) and Python SDK
(`web4-standard/implementation/sdk/web4/trust.py`). Documented 8 divergences: 1
CRITICAL (Talent decay applied, violates Sprint 44 T1 normative invariant), 4 HIGH
(T3/V3 composites unweighted, T3 update formula wrong, T3 decay model wrong), 2
MEDIUM (no ActionOutcome evolution, legacy bridge formula wrong), 1 LOW (missing test
vector operations).
**Result**: Audit document at `docs/audits/cross-language-t3v3-alignment-2026-05-13.md`.
Hardbound has an actionable gap list before relying on Rust T3/V3 semantics. The four
HIGH-severity items (#2-#5) mean that every composite, update, and decay operation in
the Rust path will produce different numbers than the Python SDK — hardbound cannot
use them interchangeably until fixed. 1 new file, 2 bookkeeping files modified.

---

## Sprint 46: Clarify CI Canonicity (2026-05-13)

The spec-to-explainer alignment audit (Sprint 43 T1) identified 14 friction items.
Sprint 44 resolved the two MEDIUM-priority items. Three LOW-priority items remain:
#10 (CI canonicity), #13 (synthons), #14 (karma). Sprint 46 resolves #10 — the
cleanest scope, following the downstream-from-audit pattern.

### T1: Normative clarification of constellation_coherence vs "CI"
**Status**: DONE
**Completed**: 2026-05-13
**Authorized by**: Downstream from Sprint 43 audit (spec-vs-explainer-alignment-2026-04-19.md item #10)
**Scope**:
(1) Add §4.4 "Canonical Terminology and Simulation Parameters" to
`multi-device-lct-binding.md`. Documents that `constellation_coherence` is the
canonical metric (T3 tensor extension, 0.0–1.0, witness density). "CI" / "Coherence
Index" is a derived label used in explainers/simulations, not a standalone protocol
primitive. The canonical equation does not include CI. Specific multiplier values
(e.g., "1.4×") are simulation parameters, not protocol-prescribed.
(2) Update `docs/SPRINT.md` (this section) and `SESSION_FOCUS.md`.
**Result**: Audit item #10 resolved on the spec side. 4-life team has unambiguous
normative language: cite `constellation_coherence` by name, label any derived
multiplier as a simulation parameter. Remaining audit items (#13 synthons, #14
karma) are LOW-priority and deferred to future sprints — both require operator
design decisions about whether to add new spec primitives. 0 new files, 1 spec
file modified, 2 bookkeeping files modified.

---

## Sprint 45: Archive Stale Implementation Artifacts (2026-05-13)

PRs #174-178 archived 319+ sprawl files and triaged the implementation/ tree,
but three non-code files in `guides/` and `examples/` were missed (the triage
focused on .py files). These files reference non-canonical terminology (W4ID,
ClientHello, CreditGrant, joule-equivalent) that does not appear in the current
SDK or core-spec. Archiving them completes the cleanup chain.

### T1: Archive 3 stale non-code files from implementation/
**Status**: DONE
**Completed**: 2026-05-13
**Authorized by**: Continuation of implementation/ cleanup chain (PRs #174-178)
**Scope**:
(1) Archive `guides/implementation_guide.md` — generic crypto implementation
guide from drift era. References "W4ID", handshake protocols, ECDH, AES-GCM,
"Verifiable Credentials specification". Does not reference the SDK (`pip install
web4`, `import web4`) or any current module. Misleading to developers.
(2) Archive `examples/handshake_exchange.json` — references "ClientHello",
"ServerHello", "W4-BASE-1", "W4-FIPS-1" cipher suites. None canonical.
(3) Archive `examples/metering_flow.json` — references "CreditGrant",
"UsageReport", "Settle", "joule-equivalent". None canonical.
All three moved to `archive/implementation-sprawl/` via `git mv`.
(4) Update `docs/SPRINT.md` (this section) and `SESSION_FOCUS.md`.
**Result**: `implementation/` now contains only `sdk/` (the shipped SDK) and
`reference/` (3 REVIEW .py files pending operator decision). The `guides/` and
`examples/` directories no longer exist in the tracked tree. 0 new files,
3 files moved, 2 bookkeeping files modified.

---

## Sprint 44: Resolve MEDIUM-Priority Spec Gaps (2026-05-12)

The spec-to-explainer alignment audit (Sprint 43 T1) identified 4 SPEC GAPs
and 2 BOTH items. Sprint 44 resolves the two MEDIUM-priority spec gaps —
the natural downstream step in the audit → fix pipeline.

### T1: ATP transfer-fee semantics + T3 Talent-decay clarification
**Status**: DONE
**Completed**: 2026-05-12
**Authorized by**: Downstream from Sprint 43 audit (spec-vs-explainer-alignment-2026-04-19.md items #2 and #5)
**Scope**:
(1) Add §6.3 "Transfer Fees" to `atp-adp-cycle.md`: transfer fees are not
prescribed by the protocol; societies MAY levy them as economic law. Fee rate,
bearer, and destination must be declared in published laws. Fees recycled to
society pool. Specific rates in simulations/explainers are simulation parameters.
Added MAY requirement #6 to §7.3.
(2) Strengthen "Talent Stability" in `t3-v3-tensors.md` §2.3: Talent's no-decay
property is normative and invariant, not tunable. Societies MAY configure custom
decay for Training and Temperament but not Talent. Half-life values for Talent in
simulations/explainers are simulation parameters, not canonical.
(3) Update `docs/SPRINT.md` (this section) and `SESSION_FOCUS.md`.
**Result**: Two MEDIUM-priority SPEC GAPs from the Sprint 43 audit are resolved.
4-life team has unambiguous canonical language to reference. Remaining spec gaps
(#10 CI, #13 synthons, #14 karma) are LOW-priority and deferred to future sprints.
0 new files, 2 spec files modified, 2 bookkeeping files modified.

---

## Sprint 43: Spec-to-Explainer Alignment Memo (2026-04-19)

Five consecutive empty-queue autonomous sessions (Apr 17 18:00 → Apr 18 18:00)
exhausted the sprint plan through Sprint 42. Operator filed issue #166
("Sprint 43 planning needed") with four pre-approved candidates. Sprint 43 T1
executes candidate (a)-1: close the feedback loop CLAUDE.md names as the
"4-Life Feedback Loop" but for which no artifact currently exists.

### T1: Spec-to-explainer alignment memo
**Status**: DONE
**Completed**: 2026-04-19
**Authorized by**: issue #166 candidate (a)-1
**Scope**:
(1) Read the 14 friction items in `../4-life/visitor/logs/2026-04-18.md` (table only,
not the separate "Unanswered Questions" section).
(2) For each item, classify as SPEC GAP (spec silent/ambiguous), EXPLAINER GAP
(spec clear, 4-life doesn't surface it), or BOTH.
(3) Every SPEC GAP citation must be verified by reading the cited file.
(4) Produce `docs/audits/spec-vs-explainer-alignment-2026-04-19.md` as the single
bounded deliverable. Precedent: `whitepaper-sdk-coherence-2026-03-15.md`.
(5) Out of bounds: NO spec edits, NO 4-life edits, NO SDK code changes, NO
inventing a 15th friction item, NO writing the fix in-place (memo classifies; it
does not fix). The 4 "Unanswered Questions" below the friction table are handled
as an appendix, not as additional classifications.
**Result**: Categorized triage artifact consumable by downstream sprints on either
side of the feedback loop. Does NOT consume issue #166 — candidates (a)-2, (a)-3,
(a)-4 remain open.

---

## Sprint 42: CI Quickstart Smoke (2026-04-18)

Sprint 36 T1 introduced `examples/quickstart.py` as a minimal, offline composition
of the three SDK behavioral functions (`generate`/`from_jsonld` roundtrip,
`evaluate_trust_query`, `process_action_outcome`). Sprint 36 left one follow-up
open: wire the quickstart into CI so a breaking API change surfaces in the
wheel-install smoke job, not just in the editable-install test matrix. This sprint
was originally proposed as Sprint 40 (PR #164 opened 2026-04-17) but is renumbered
to Sprint 42 to reflect merge order — Sprint 41 (PR #165) landed on main first.

### T1: Wire `examples/quickstart.py` into CI wheel smoke job
**Status**: DONE
**Completed**: 2026-04-18
**Scope**:
(1) Add one step to the `wheel` job in `.github/workflows/sdk-test.yml`, immediately
after `Verify CLI entry point`, running
`/tmp/web4-wheel-test/bin/python examples/quickstart.py`. The working directory
is already `web4-standard/implementation/sdk`, so the relative path resolves.
(2) The step uses the interpreter from the isolated venv already created by the
`Install from wheel in fresh environment` step, so it exercises the packaged
wheel — not the editable-install source tree used by the matrix `test` job.
(3) No changes to `examples/quickstart.py`, `web4/`, `pyproject.toml`, or tests.
(4) Update `docs/SPRINT.md` (this section) and `SESSION_FOCUS.md`.
**Result**: A breaking change to the quickstart's public API surface now fails
CI on every PR. Verified locally by reproducing the full CI chain: build wheel,
install in fresh venv, `web4 selftest`, `web4 info`, then
`python examples/quickstart.py` — all succeed against v0.26.0. 0 new files.

---

## Sprint 41: Remove Dead web4_sdk.py + Fix v0.26.0 Documentation Gaps (2026-04-17)

Sprint 36 deleted the example scripts that imported from `web4_sdk.py` because they
caused `ImportError` (referencing nonexistent microservices). However, `web4_sdk.py`
itself (~1500 lines) and its test file were left behind. The README still documented
it as a usable Client SDK. Additionally, the README and quickstart docstring still
referenced v0.25.0 despite the v0.26.0 bump in Sprint 39.

### T1: Remove dead `web4_sdk.py` + fix v0.26.0 documentation gaps
**Status**: DONE
**Completed**: 2026-04-17
**Scope**:
(1) Delete `web4_sdk.py` — async HTTP client for nonexistent services, not distributed
in wheel (`packages.find.include = ["web4*"]`), examples deleted in Sprint 36.
(2) Delete `tests/test_sdk_integration.py` — 14 tests for the removed module.
(3) Update `README.md`: version 0.25.0 → 0.26.0, remove "Client SDK" section,
remove `web4_sdk.py` from Project Structure, update test count 2627 → 2613.
(4) Update `examples/quickstart.py` docstring: v0.25.0 → v0.26.0.
(5) Update `docs/SPRINT.md` and `SESSION_FOCUS.md`.
**Result**: No dead code referencing nonexistent services. README accurately reflects
what's distributed in the wheel. All version references consistent at v0.26.0.
2613 tests pass (14 removed with deleted module). mypy --strict clean. ruff clean.
0 new files, 2 files deleted, 4 files modified.

---

## Sprint 39: SDK v0.26.0 Release Housekeeping (2026-04-17)

Three quality-improvement PRs merged since v0.25.0: CI workflow hardening (#158),
ruff lint cleanup + CI enforcement (#161), ruff format codebase-wide + CI enforcement
(#162). Sprint 39 brings all SDK metadata into alignment with the current state.

### T1: SDK v0.26.0 release housekeeping
**Status**: DONE
**Completed**: 2026-04-17
**Scope**:
(1) Version bump 0.25.0 → 0.26.0 in `pyproject.toml`.
(2) CHANGELOG v0.26.0 entry documenting Sprints 35, 37, 38.
(3) Update `web4/__init__.py` docstring with v0.26.0 note.
(4) Update test version assertions in `test_cli.py` and `test_package_api.py`.
(5) Update `docs/SPRINT.md` and `SESSION_FOCUS.md`.
**Result**: SDK version metadata reflects the 3 CI/quality merges since v0.25.0.
All 2627 tests pass. mypy --strict clean. ruff check + format clean. 0 new files.

---

## Sprint 38: Ruff Format Codebase-Wide + CI Enforcement (2026-04-17)

Sprints 35 and 37 both listed `ruff format` codebase-wide + `ruff format --check` in CI
as an explicit pending follow-up. A prior PR #159 attempted it but was closed
without merging (bundled accidental session-report artifacts and shipped with
10 failing `ruff check` lint errors; the lint portion was later fixed independently
in Sprint 37 T1 / PR #161). Sprint 38 closes the follow-up cleanly on a fresh branch.

### T1: `ruff format` codebase-wide + CI enforcement
**Status**: DONE
**Completed**: 2026-04-17
**Scope**:
(1) Apply `ruff format` to `web4/` and `tests/test_*.py` (70 files reformatted).
(2) Extend `.github/workflows/sdk-test.yml` lint job with a new
`ruff format --check web4/ tests/test_*.py` step immediately after the existing
`ruff check` step, using the same path scope so the two gates stay aligned.
(3) No semantic code changes — `ruff format` is purely mechanical (whitespace,
quote style, line wrapping per line-length=120 in pyproject.toml).
(4) No pyproject.toml changes.
(5) Update SESSION_FOCUS.md to correct stale open-PR metadata (PR #159 is CLOSED,
not pending; add PR #160 which is the only open PR).
**Result**: `ruff format --check web4/ tests/test_*.py` passes with 0 needed
changes. CI now enforces both lint (`ruff check`) and formatting (`ruff format --check`)
on every PR. All 2627 tests pass. `mypy --strict` clean (25 files). 0 new files,
0 manual source edits.

---

## Sprint 37: Ruff Lint Cleanup + CI Enforcement (2026-04-16)

`ruff check` (lint) was configured in pyproject.toml but only partially enforced —
CI ran `ruff check web4/` (source only), and neither source nor tests were lint-clean.
239 issues across source (10) and tests (229): unused imports, unsorted imports,
unused variables, imports not at top of file, line-too-long.

### T1: `ruff check` lint cleanup + CI enforcement
**Status**: DONE
**Completed**: 2026-04-16
**Scope**: Fix all `ruff check` issues in web4/ and tests/:
(1) Source code: 10 issues (7 unsorted imports, 3 unused imports — including genuinely
unused V3 import in mcp_server.py and dead _ATPAccount import in trust.py). All auto-fixed.
(2) Tests: 229 issues — 114 unused imports (auto-removed), 77 unsorted imports (auto-fixed),
23 E402 import-not-at-top (per-file-ignore for tests/), 12 unused variables (prefixed with _),
2 line-too-long (reformatted), 1 redefinition (noqa for intentional re-import test).
(3) pyproject.toml: Added `"tests/*" = ["E402"]` per-file-ignore.
(4) CI: Expanded lint step from `ruff check web4/` to `ruff check web4/ tests/`.
(5) 1 jsonschema availability probe import preserved with `# noqa: F401`.
**Result**: `ruff check web4/ tests/` passes with 0 errors. CI now enforces lint on
both source and tests. All 2627 tests pass. mypy --strict clean (25 files). 0 new files.

### Follow-up (not this sprint)
- `ruff format` codebase-wide — ADDRESSED in Sprint 38 (2026-04-17)

---

## Sprint 36: Quickstart Example Refresh (2026-04-16)

The SDK shipped two `examples/*.py` files in Dec 2025 that referenced a
`web4_sdk` HTTP-client module (`Web4Client`, microservice URLs, async I/O)
that does not exist in the current v0.25.0 package. Any user who ran them
got an immediate `ImportError`. Sprint 36 replaces them with a single
offline quickstart that composes the three behavioral functions the SDK
actually exports.

### T1: Replace stale examples with v0.25.0 quickstart
**Status**: DONE
**Completed**: 2026-04-16
**Scope**: Delete `examples/ai_agent_workflow.py` and
`examples/multi_agent_coordination.py` (both import the nonexistent
`web4_sdk` module). Add `examples/quickstart.py` — a ~170-line offline
script demonstrating (1) `generate(type) → from_jsonld(doc)` roundtrip
for `LinkedContextToken`, (2) `evaluate_trust_query()` with ATP stake
locking and RANGE-disclosure T3 return, (3) `process_action_outcome()`
with R7Action → ReputationEngine → TrustProfile → ATPAccount composition.
Add `examples/README.md` documenting run instructions and contribution
guidelines. Passes `ruff check`, `ruff format --check`, `mypy --strict`.
**Result**: 2 files deleted, 2 files added. No changes under `web4/`,
no new tests, no new SDK features. `python examples/quickstart.py` runs
offline to completion.

### Follow-up (not this sprint)
- Wire `examples/quickstart.py` into a CI smoke job (run after wheel install)

---

## Sprint 35: CI Workflow Hardening (2026-04-13)

CI quality gates were weaker than local development standards. Sprint 35 aligns
them: strict mypy in CI (matching pyproject.toml), and a new wheel verification
job that builds a wheel, installs in an isolated venv, and runs `web4 selftest`.
Sprint 30 found 4 real packaging bugs via manual wheel testing — this automates
that verification for every PR.

### T1: CI workflow hardening
**Status**: DONE
**Completed**: 2026-04-13
**Scope**: Update `.github/workflows/sdk-test.yml`:
(1) mypy job now uses `mypy web4/` (picks up `strict = true` from pyproject.toml)
instead of `mypy web4/ --ignore-missing-imports` (which was weaker than local).
(2) New `wheel` job: builds wheel via `python -m build`, installs in isolated
venv (`python -m venv`), runs `web4 selftest` and `web4 info` from installed wheel.
(3) Dropped planned `ruff format --check` — 70 files need reformatting, deferred
to avoid scope expansion.
**Result**: CI now matches local quality gates for type checking. Packaging
regressions (like Sprint 30's 4 bugs) will be caught automatically. 0 new files.

### Follow-up (not this sprint)
- `ruff format` codebase-wide (70 files) + `ruff format --check` in CI — ADDRESSED in Sprint 38 (2026-04-17)

---

## Sprint 34: SDK v0.25.0 Release Housekeeping (2026-04-12)

Three PRs merged since v0.24.0: trust CLI subcommand (#147), archive reference
implementation sprawl (#151), archive remaining implementation/ session sprawl (#153).
Sprint 34 brings all SDK metadata into alignment with the current state.

### T1: SDK v0.25.0 release housekeeping
**Status**: DONE
**Completed**: 2026-04-12
**Scope**: Version bump 0.24.0 → 0.25.0. CHANGELOG v0.25.0 entry documenting
PR #147 (trust CLI as 7th subcommand, 13 tests) and PRs #151/#153 (archive cleanup).
README.md updates (7 CLI subcommands, 2627 tests, trust CLI docs in CLI section and
project structure). `__init__.py` docstring update (test count 2614 → 2627, CLI
subcommand count 6 → 7). Fix test version assertions (0.24.0 → 0.25.0). Update
SESSION_FOCUS.md and SPRINT.md.
**Result**: All SDK metadata now accurately reflects 22 modules + MCP server,
364 exports, 2627 tests, 97.8% coverage, 8 MCP tools, 3 behavioral functions,
7 CLI subcommands. Version 0.25.0. 0 new files.

---

## Sprint 33: SDK v0.24.0 Release Housekeeping (2026-04-11)

Sprint 32 added `web4 selftest` (deployment verification CLI) and merged to main
after the v0.23.0 version bump. Sprint 33 brings all SDK metadata into alignment
with the current state.

### T1: SDK v0.24.0 release housekeeping
**Status**: DONE
**Completed**: 2026-04-11
**Scope**: Version bump 0.23.0 → 0.24.0. CHANGELOG v0.24.0 entry documenting
Sprint 32 (selftest CLI command). README.md updates (test count 2610 → 2614,
selftest in CLI docs and project structure). `__init__.py` docstring update
(test count, CLI subcommand count). Fix test version assertions (0.23.0 → 0.24.0).
Update SESSION_FOCUS.md (version, open PRs, recent commits, completeness).
**Result**: All SDK metadata now accurately reflects 22 modules + MCP server,
364 exports, 2614 tests, 97.8% coverage, 8 MCP tools, 3 behavioral functions,
6 CLI subcommands. Version 0.24.0. 0 new files.

---

## Sprint 32: Deployment Verification CLI (2026-04-11)

The SDK has been feature-complete since Sprint 31 (v0.23.0). Sprint 30 performed
manual deployment verification (build wheel → install → test imports/CLI/schemas/roundtrip)
and found 4 bugs. Sprint 32 automates that verification as a CLI subcommand so any
user can verify their `pip install web4` works correctly.

### T1: `web4 selftest` deployment verification command
**Status**: DONE
**Completed**: 2026-04-11
**Scope**: Add `selftest` subcommand to `web4/__main__.py` that verifies: (1) all
22 modules import successfully, (2) schema registry loads, (3) all 23 dispatcher
types generate and round-trip with fidelity. Supports `--verbose`/`-v` for per-phase
progress. Exits 0 with summary on success, exits 1 with error details on failure.
**Result**: ~60 lines in `__main__.py` (function + module list + parser entry).
4 new tests in `test_cli.py` (success path, verbose mode, simulated import failure,
short flag). 2614 tests passing (up from 2610). mypy strict clean (25 files). 0 new files.

---

## Sprint 31: SDK v0.23.0 Release Housekeeping (2026-04-11)

Sprints 29 and 30 landed significant changes on main (CLI test refactoring for
coverage accuracy, 4 roundtrip fidelity bug fixes) without a version bump.
Sprint 31 brings all SDK metadata into alignment with the current state.

### T1: SDK v0.23.0 release housekeeping
**Status**: DONE
**Completed**: 2026-04-11
**Scope**: Version bump 0.22.0 → 0.23.0. CHANGELOG v0.23.0 entry documenting
Sprint 29 (CLI test refactoring, `__main__.py` coverage 15.8% → 90.6%) and
Sprint 30 T1b (4 bug fixes: LCT `@type` roundtrip, LCT schema `@type` rejection,
DictionaryEntity `lct_id` loss, `pyproject.toml` license deprecation). Update
README.md (2610 tests, 97.8% coverage). Update `__init__.py` docstring. Update
SESSION_FOCUS.md (correct Open PRs, test count, coverage). Fix test version
assertions (0.22.0 → 0.23.0).
**Result**: All SDK metadata now accurately reflects 22 modules + MCP server,
364 exports, 2610 tests, 97.8% coverage, 8 MCP tools, 3 behavioral functions.
Version 0.23.0. 0 new files.

---

## Sprint 30: Distribution Verification + Roundtrip Fidelity (2026-04-10)

Wheel distribution verification uncovered real bugs: LCT JSON-LD roundtrip
losing `@type`, DictionaryEntity roundtrip losing `lct_id`, and LCT schema
rejecting valid `@type` fields. Also fixed setuptools license deprecation.

### T1: Wheel distribution verification + roundtrip bug fixes
**Status**: DONE
**Completed**: 2026-04-10
**Scope**: Build a wheel, install in isolated venv, verify all SDK features.
Fix all roundtrip fidelity issues and packaging warnings discovered.
**Result**: 4 bugs fixed:
1. `LCT.to_jsonld()` now includes `@type: "web4:LinkedContextToken"` (roundtrip fidelity)
2. LCT JSON Schema now allows optional `@type` property (was rejecting valid documents)
3. `DictionaryEntity.from_jsonld()` now preserves `lct_id` from original document
4. `pyproject.toml` license updated to SPDX format (fixes setuptools deprecation)
Removed `@type` workaround from `generate.py`. Rebuilt `schema_registry.json`.
Updated LCT test vectors (10 vectors, all with `@type`). Added LCT to dispatcher
lifecycle test. 2610 tests passing (up from 2608). mypy strict clean (25 files).
Wheel verified: 14 import tests + CLI + schema validation + roundtrip all pass.

---

## Sprint 29: CLI Test Coverage Hardening (2026-04-10)

The CLI module (`__main__.py`) was at 15.8% measured coverage despite having
comprehensive tests — because all tests used `subprocess.run()`, running in
child processes invisible to coverage. Sprint 29 refactors these tests to
call `main(argv)` in-process so coverage tracks accurately.

### T1: Refactor CLI tests from subprocess to in-process
**Status**: DONE
**Completed**: 2026-04-10
**Scope**: Convert all `test_cli.py` test classes from `subprocess.run()` calls
to in-process `main(argv)` + `capsys` calls. Keep a small `TestSmoke` class (3
subprocess tests) for end-to-end entry point validation. Add `TestGenerate`
class (5 tests) for the previously untested generate subcommand CLI paths.
**Result**: `__main__.py` coverage: 15.8% → 90.6%. 40 total tests in test_cli.py
(was 32 — net +8: 5 generate tests + 3 smoke tests). 2608 total tests passing
(up from 2600). mypy strict clean (25 files). 0 new files.

---

## Sprint 28: MCP process_action Tool + v0.22.0 Release (2026-04-08)

Sprints 24 and 27 added `process_action_outcome()` (3rd behavioral function) and exposed
`evaluate_trust_query()` / `resolve_trust()` as MCP tools. Sprint 28 completes the set:
`web4_process_action` wraps `process_action_outcome()` for MCP clients, achieving 3-for-3
behavioral function coverage. Release housekeeping brings version to 0.22.0.

### T1: `web4_process_action` MCP tool
**Status**: DONE
**Completed**: 2026-04-08
**Scope**: Add 8th MCP tool to `web4/mcp_server.py` wrapping `process_action_outcome()`.
Accepts simple parameters (action_type, status, actor, role, rules JSON, profile_roles JSON,
atp_stake, atp_locked, quality), constructs R7Action + ReputationEngine + TrustProfile +
ATPAccount internally, calls `process_action_outcome()`, returns updated T3/V3 tensors,
ATP settlement, and reputation delta. Input validation for status (success/failure),
rules JSON parsing with error messages, profile_roles JSON parsing.
**Result**: 1 new tool function (~120 lines), 1 new test file (test_mcp_process_action.py).
15 new tests across 5 classes (success path, failure path, error handling, edge cases,
MCP integration). MCP server now has 8 tools (5 data + 3 behavioral). Updated docstring,
`__all__`, server instructions.

### T2: SDK v0.22.0 release housekeeping
**Status**: DONE
**Completed**: 2026-04-08
**Scope**: Version bump 0.21.0 → 0.22.0. CHANGELOG v0.22.0 entry documenting Sprint 28
(MCP process_action tool). README.md updates (8 tools, 2600 tests, 364 exports). Update
`__init__.py` docstring. Update SESSION_FOCUS.md and SPRINT.md. Fix stale PR #137
reference in CHANGELOG v0.21.0 entry (now #143).
**Result**: All SDK metadata now accurately reflects 22 modules + MCP server, 364 exports,
2600 tests, 8 MCP tools, 3 behavioral functions. Version 0.22.0.

---

## Sprint 27: MCP Behavioral Tools (2026-04-07)

The MCP server had 5 data-oriented tools (info, validate, generate, roundtrip,
list_types) but did not expose the behavioral functions. Sprint 27 adds MCP tools
for `evaluate_trust_query()` and `resolve_trust()`, making the full trust resolution
pipeline accessible to MCP clients.

### T1: Expose behavioral functions as MCP tools
**Status**: DONE
**Completed**: 2026-04-07
**Scope**: Add `web4_evaluate_trust` and `web4_resolve_trust` tools to
`web4/mcp_server.py`. Each wraps the corresponding behavioral function,
accepting JSON inputs and returning structured dicts. Update docstring,
server instructions, and `__all__`. 20 new tests covering approval/rejection,
disclosure levels, direct/indirect/no-path resolution, custom strategies,
error handling, and MCP call integration.
**Result**: MCP server now has 7 tools (5 data + 2 behavioral). 2567 tests
passing (up from 2547). mypy strict clean (25 files). 0 new files.

---

## Sprint 26: Release Housekeeping v0.21.0 (2026-04-07)

Sprint 25 added the third behavioral function (`resolve_trust()` + `TrustResolution`)
without a version bump. Sprint 26 brings all metadata into alignment.

### T1: SDK v0.21.0 release housekeeping
**Status**: DONE
**Completed**: 2026-04-07
**Scope**: Bump version 0.20.0 → 0.21.0. Add CHANGELOG v0.21.0 entry documenting
Sprint 25 features (resolve_trust, TrustResolution). Update README.md with 3rd
behavioral function, updated test count (2525→2547), export count (360→362). Update
`__init__.py` docstring. Update SESSION_FOCUS.md to reflect Sprint 25 merge.
**Result**: All SDK metadata now accurately reflects 22 modules + MCP server, 362
exports, 2547 tests, 3 behavioral functions, and `resolve_trust()`. Version 0.21.0.

---

## Sprint 25: Indirect Trust Resolution (2026-04-07)

Sprints 22 and 24 added the first two behavioral functions: `evaluate_trust_query()`
(direct trust lookup) and `process_action_outcome()` (action → reputation pipeline).
Sprint 25 adds the third: `resolve_trust()`, which composes MRH graph topology with
TrustProfile T3 tensors to resolve **indirect** trust through intermediary chains —
the "transitive DNS lookup" for trust when observer and target are not directly connected.

### T1: `resolve_trust()` function + `TrustResolution` dataclass
**Status**: DONE
**Completed**: 2026-04-07
**Scope**: Add `resolve_trust()` to `web4/trust.py` that composes
`MRHGraph.trust_between()` (scalar path trust with decay) with
`TrustProfile.get_t3()` (per-role T3 tensors) to produce tensor-aware
indirect trust resolution. New `TrustResolution` dataclass captures the
resolution method (direct/indirect/none), effective T3, path trust scalar,
hop count, and propagation strategy used. Handles self-trust (direct),
graph-mediated indirect trust, and no-path cases. `to_dict()`/`from_dict()`
round-trip on TrustResolution. Uses `TYPE_CHECKING` import for MRHGraph
(same pattern as evaluate_trust_query's ATPAccount). 2 new exports in
`__init__.py` `__all__` (364 total, up from 362).
**Result**: 1 new function (~50 lines), 1 new dataclass (~40 lines) in trust.py.
22 new tests in test_trust_resolution.py covering direct trust (3), 1-hop
indirect (3), multi-hop decay (3), multi-path aggregation (3), no-path (2),
decay factor (2), round-trip serialization (3), and integration (3).
2565 total tests passing (up from 2543). mypy strict clean (25 files).

---

## Sprint 24: Action Consequence Pipeline (2026-04-08)

Sprint 22 added `evaluate_trust_query()` (direct trust resolution). Sprint 24 adds the
second behavioral function: `process_action_outcome()`, which connects completed R7Actions
to reputation/trust updates through the full composition pipeline.

### T1: `process_action_outcome()` function + `ActionOutcomeResult` dataclass
**Status**: DONE
**Completed**: 2026-04-08
**Scope**: Add `process_action_outcome()` to `web4/reputation.py` composing
R7Action → ReputationEngine.evaluate() → TrustProfile T3/V3 delta application →
ATPAccount settlement (commit on success, rollback on failure) → optional
ReputationStore recording. New `ActionOutcomeResult` dataclass captures the
reputation delta, updated T3/V3, ATP committed/rolled-back amounts. 2 new exports
in `__init__.py` `__all__` (364 total, up from 362). 18 new tests covering success
paths (5), failure paths (3), edge cases (5), store integration (3), root imports (2).
**Result**: 2585 total tests passing (up from 2567). mypy strict clean (25 files).
**Note**: Original PR #137 was closed due to Sprint 25 overlap. Resubmitted as clean
PR on current main.

---

## Sprint 23: Release Housekeeping v0.20.0 (2026-04-07)

Sprint 22 added two significant features — `evaluate_trust_query()` (first behavioral
function) and the MCP server module (5 tools via FastMCP) — without a version bump.
Sprint 23 brings all metadata into alignment.

### T1: SDK v0.20.0 release housekeeping
**Status**: DONE
**Completed**: 2026-04-07
**Scope**: Bump version 0.19.0 → 0.20.0. Add CHANGELOG v0.20.0 entry documenting
Sprint 22 features (evaluate_trust_query + MCP server). Update README.md with MCP
server section, updated test count (2459→2525), export count (359→360), MCP optional
extra docs. Update `__init__.py` docstring. Update SESSION_FOCUS.md to reflect PR #133
merge and MCP server on main.
**Result**: All SDK metadata now accurately reflects 22 modules + MCP server, 360
exports, 2525 tests, `web4-mcp` entry point, and `evaluate_trust_query()`. Version 0.20.0.

---

## Sprint 22: Trust Query Evaluation Pipeline + MCP Server (2026-04-06)

Sprints 1-21 built all data types, serialization, validation, and CLI tools.
Sprint 22 adds the first *behavioral* function and an MCP server: composing
TrustQuery + TrustProfile + ATPAccount into TrustQueryResponse (the core trust
resolution operation), and exposing SDK operations as MCP tools for any client.

### T1: `evaluate_trust_query()` function
**Status**: DONE
**Completed**: 2026-04-06
**Scope**: Add `evaluate_trust_query()` to `web4/trust.py` that composes
existing SDK types into the trust resolution pipeline: validate query, lock
ATP stake, look up T3 for requested role, apply disclosure level filtering
(binary/range/precise), compute validity window, return TrustQueryResponse.
Handles rejection (insufficient ATP) with rollback. 1 new export in
`__init__.py` `__all__` (360 total, up from 359).
**Result**: 1 new function in trust.py (~60 lines), TYPE_CHECKING import
for ATPAccount (no circular import). 23 new tests in test_trust_query_eval.py
covering approval flow, rejection paths, disclosure levels, role lookup,
timestamp handling, response round-trip, and ATP accounting. mypy strict clean
(25 files).

### T1b: Web4 MCP Server module
**Status**: DONE
**Completed**: 2026-04-06
**Scope**: New `web4/mcp_server.py` module exposing SDK operations as MCP
tools via FastMCP (mcp v1.27.0, stdio transport). 5 tools: `web4_info`,
`web4_validate`, `web4_generate`, `web4_roundtrip`, `web4_list_types`.
Entry point: `web4-mcp` console script or `python -m web4.mcp_server`.
Optional extra: `pip install 'web4[mcp]'`.
**Result**: 1 new module (web4/mcp_server.py), 1 new test file
(test_mcp_server.py). 43 new tests. 2525 total tests passing (up from 2459).
mypy strict clean (25 files).

---

## Sprint 21: Release Housekeeping v0.19.0 (2026-04-05)

SDK v0.18.0 was set in Sprint 17 but only covered Sprint 16 features. Sprints 18-20
added significant functionality (roundtrip CLI, lifecycle tests, TrustQuery types,
generate module) without a version bump. Sprint 21 brings all metadata into alignment.

### T1: SDK v0.19.0 release housekeeping
**Status**: DONE
**Completed**: 2026-04-05
**Scope**: Bump version 0.18.0 → 0.19.0. Add CHANGELOG v0.19.0 entry documenting
Sprints 18-20 features. Update README.md module count (21→22), export count (348→359),
test count (2245→2459), add generate module to module table, add roundtrip/generate CLI
docs, update project structure section. Update `__init__.py` docstring with current counts.
**Result**: All SDK metadata now accurately reflects 22 modules, 359 exports, 2459 tests,
5 CLI subcommands, and the generate module. Version 0.19.0.

---

## Sprint 20: Document Generation (2026-04-05)

The SDK can deserialize any JSON-LD document via `from_jsonld()` (23 types) and
serialize via `to_jsonld()`, but there was no way for developers to bootstrap a
valid document from scratch without knowing each type's constructor. Sprint 20
adds a `generate` module and CLI command that produces minimal valid JSON-LD
documents for any supported type — useful for bootstrapping, cross-language
conformance testing, and documentation examples.

### T1: `web4 generate <type>` CLI command + generate module
**Status**: DONE
**Completed**: 2026-04-05
**Scope**: New `web4/generate.py` module with factory functions for all 23
dispatcher types. Each factory produces a minimal but schema-valid instance
serialized via `to_jsonld()`. Public API: `generate(type_name)`,
`generate_string(type_name)`, `available_types()`, `UnsupportedTypeError`.
CLI subcommand `web4 generate <type>` with `--compact` and `--list` flags.
Accepts both bare and `web4:`-prefixed type names. 4 new exports in
`__init__.py` `__all__` (359 total, up from 355).
**Result**: 1 new module (web4/generate.py), 1 new test file (test_generate.py).
102 new tests (23 types x 3 parametrized suites + 6 unit + 19 schema validation
+ 6 CLI integration). 2459 total tests passing (up from 2355). mypy strict clean
(24 files, up from 23). 22 modules in SDK (up from 21).

---

## Sprint 19: Trust Query Data Types (2026-04-05)

The trust-query JSON schema exists in the schema registry with 2 test vectors,
but had no corresponding Python data class — the only schema type without one.
Sprint 19 closes this gap.

### T1: TrustQuery and TrustQueryResponse data classes
**Status**: DONE
**Completed**: 2026-04-05
**Scope**: Add `TrustQuery`, `TrustQueryResponse`, and `DisclosureLevel` to
`web4/trust.py`. TrustQuery models the ATP-staked trust information request per
trust-query.schema.json, with validation (minimum stake, validity period bounds).
TrustQueryResponse models approved/rejected responses with embedded T3 tensors.
Both have `to_dict()`/`from_dict()` round-trips. TrustQuery additionally has
`to_jsonld()`/`from_jsonld()` for JSON-LD dispatch, registered in the
`web4.deserialize` dispatcher (23 types, up from 22). Schema validation uses
`to_dict()` against the raw trust-query.schema.json (which has no @context/@type).
7 new exports in `__init__.py` `__all__` (355 total, up from 348).
**Result**: 3 new types, 3 new constants, 1 new context URI. 2355 total tests
passing (up from 2322). 23 dispatcher types. mypy strict clean (23 files).

---

## Sprint 18: CLI Conformance Tooling (2026-04-05)

The SDK has complete serialization round-trips (22 types via `from_jsonld()`, 19 class-based
types with `to_jsonld()`). Sprint 18 exposes this capability through the CLI for
cross-language conformance testing.

### T1: CLI `web4 roundtrip` conformance command
**Status**: DONE
**Completed**: 2026-04-05
**Scope**: Add `web4 roundtrip <file>` CLI command that reads a JSON-LD document,
deserializes via `from_jsonld()`, re-serializes via `to_jsonld()`, and outputs the
normalized result. With `--check` flag, compares input vs output semantically and
returns exit 0 (match) or 1 (mismatch with diff). Supports stdin via `-`.
**Result**: New CLI command with normalize and check modes. Refactored shared
`_read_json_doc()` helper (DRY improvement for validate + roundtrip). 10 new tests
(32 total CLI tests), 2255 total tests passing, mypy strict clean (23 files).

### T2: JSON-LD document lifecycle integration tests
**Status**: DONE
**Completed**: 2026-04-05
**Scope**: Integration tests exercising the full SDK pipeline for JSON-LD documents:
create object → `to_jsonld()` → `web4.validation.validate()` → `web4.from_jsonld()`
(generic dispatcher) → verify round-trip fidelity. Covers all 21 dispatcher types and
all 19 schema-validated types through the SDK's public API (not direct schema loading).
**Result**: 67 tests in `test_jsonld_lifecycle.py`. Deep per-type lifecycle tests for 8
representative types (LCT, T3, V3, AttestationEnvelope, ATP, R7Action, ACP, Dictionary),
parametrized dispatcher coverage for all 21 types, parametrized schema validation for 19
types, cross-module composition tests, and dispatcher completeness checks. 2322 total
tests passing, mypy strict clean (23 files).

---

## Sprint 17: Release Housekeeping (2026-04-04)

Sprint 16 added two significant features (mypy strict compliance and the deserialize
module) without a version bump. Sprint 17 T1 brings all SDK metadata into alignment
with the current state: version 0.18.0, CHANGELOG, README, docstrings.

### T1: SDK v0.18.0 release housekeeping
**Status**: DONE
**Completed**: 2026-04-04
**Scope**: Bump version 0.17.0 → 0.18.0. Add CHANGELOG v0.18.0 entry documenting
Sprint 16 T1 (mypy strict) and T2 (deserialize). Update README.md module count
(20→21), export count (344→348), test count (→2245), add deserialize to module table,
update coverage and project structure sections. Update `__init__.py` docstring.
**Result**: All SDK metadata now accurately reflects 21 modules, 348 exports, 2245 tests,
mypy strict zero-error, and the deserialize module. Version 0.18.0.

---

## Sprint 16: Quality Gates + Generic Deserialization (2026-04-04)

With Sprints 1-15 delivering a complete 20-module SDK (v0.17.0, 2183 tests, 344 exports,
56 from_dict() methods, 278 schema vectors), Sprint 16 closes the last quality gate
(mypy strict zero-error) and establishes a test coverage baseline to inform future work.

### T1: mypy strict zero-error + test coverage baseline
**Status**: DONE
**Completed**: 2026-04-04
**Scope**: Fix the one remaining `mypy --strict` error (jsonschema `import-untyped` in
`validation.py`) by adding a mypy override in `pyproject.toml`. Run pytest-cov to
establish a per-module coverage baseline.
**Result**: Added `[tool.mypy]` config with `strict = true` and `[[tool.mypy.overrides]]`
for `jsonschema.*` (ignore_missing_imports). `mypy --strict web4/` now reports 0 errors
across 22 source files. Coverage baseline: **96.2% overall** (4491 statements, 169 missed).

**Coverage baseline (2026-04-04)**:

| Module | Stmts | Miss | Cover | Notes |
|--------|-------|------|-------|-------|
| atp.py | 119 | 0 | 100.0% | |
| errors.py | 93 | 0 | 100.0% | |
| lct.py | 247 | 0 | 100.0% | |
| metabolic.py | 102 | 0 | 100.0% | |
| dictionary.py | 280 | 1 | 99.6% | |
| protocol.py | 212 | 1 | 99.5% | |
| r6.py | 464 | 3 | 99.4% | |
| acp.py | 460 | 5 | 98.9% | |
| mcp.py | 282 | 3 | 98.9% | |
| security.py | 145 | 2 | 98.6% | |
| entity.py | 75 | 1 | 98.7% | |
| attestation.py | 203 | 4 | 98.0% | Verification stubs (TPM2/FIDO2/SE) |
| capability.py | 152 | 3 | 98.0% | |
| reputation.py | 198 | 4 | 98.0% | |
| trust.py | 194 | 4 | 97.9% | |
| society.py | 249 | 7 | 97.2% | |
| binding.py | 225 | 9 | 96.0% | |
| federation.py | 345 | 14 | 95.9% | |
| mrh.py | 244 | 12 | 95.1% | |
| validation.py | 100 | 17 | 83.0% | Fallback paths + jsonschema-absent |
| __main__.py | 102 | 79 | 22.5% | CLI tested via subprocess (not counted) |
| **TOTAL** | **4491** | **169** | **96.2%** | |

**Key findings**:
- 4 modules at 100% coverage (atp, errors, lct, metabolic)
- 16 modules at 95%+ (excellent)
- `validation.py` at 83%: schema loading fallback paths and jsonschema-absent branches
- `__main__.py` at 22.5%: expected — CLI tests use subprocess, not counted by pytest-cov
- `attestation.py` misses are verification stubs (TPM2/FIDO2/SE) — by design

### T2: Generic JSON-LD deserialization dispatcher
**Status**: DONE
**Completed**: 2026-04-04
**Scope**: Add a top-level `from_jsonld(doc)` function that reads the `@type` field from any
web4 JSON-LD document and dispatches to the correct class's `from_jsonld()` method. Covers
all 22 types across 10 modules. Also add `from_jsonld_string(s)` convenience wrapper,
`supported_types()` introspection, and `UnknownTypeError` exception.
**Result**: New module `web4/deserialize.py` with lazy registry pattern (avoids circular imports).
22 types mapped (19 class-based + 3 function-based), bare + `web4:` prefixed = 44 registry entries.
62 parametrized tests, 2245 total tests passing, mypy strict clean (23 files).
**Edge case**: LCT.to_jsonld() omits `@type` at top level (spec §2.3 canonical format). The
dispatcher supports `LinkedContextToken` when a producer adds `@type` to the document.

---

## Sprint 15: from_dict() Round-Trip Completeness + Schema Vector Integration (2026-04-04)

Post-Sprint 14 work completed the from_dict() round-trip series across all SDK modules
and integrated the 278 cross-language schema validation vectors into the pytest suite.
This sprint retroactively documents that work and bumps the SDK to v0.17.0.

### N1: Security module from_dict() round-trip completeness
**Status**: DONE
**Completed**: 2026-04-03
**Scope**: Add `from_dict()` classmethods to W4ID, KeyPolicy, SignatureEnvelope, and
VerifiableCredential in `web4/security.py`. 16 round-trip tests.
**Result**: 4 from_dict() methods, 16 tests. PR #119, merged.

### O1: R6 module from_dict() round-trip completeness
**Status**: DONE
**Completed**: 2026-04-03
**Scope**: Add `from_dict()` classmethods to all 12 R6 component types in `web4/r6.py`.
32 round-trip tests.
**Result**: 12 from_dict() methods (Constraint, Rules, Role, ProofOfAgency, Request,
Precedent, WitnessAttestation, Reference, ResourceRequirements, Result, TensorDelta,
ContributingFactor). 32 tests. PR #120, merged.

### P1: Reputation + protocol from_dict() round-trip completeness
**Status**: DONE
**Completed**: 2026-04-03
**Scope**: Add `from_dict()` classmethods to ReputationRule and HandshakeMessage.
8 round-trip tests.
**Result**: 2 from_dict() methods, 8 tests. PR #121, merged.

### Q1: ACP module from_dict() round-trip completeness
**Status**: DONE
**Completed**: 2026-04-03
**Scope**: Add `from_dict()` classmethods to PlanStep, AgentPlan, Intent, Decision,
and ExecutionRecord in `web4/acp.py`. 18 round-trip tests.
**Result**: 5 from_dict() methods, 18 tests. PR #123, merged.

### R1: LCT module from_dict() round-trip completeness
**Status**: DONE
**Completed**: 2026-04-03
**Scope**: Add `from_dict()` classmethods to Binding, MRHPairing, MRH, BirthCertificate,
Attestation, LineageEntry, Policy, and LCT in `web4/lct.py`. 27 round-trip tests.
**Result**: 8 from_dict() methods, 27 tests. Completes the N1-R1 series — all SDK classes
with to_dict() now have matching from_dict(). PR #124, merged.

### M1: Integrate schema validation vectors into pytest suite
**Status**: DONE
**Completed**: 2026-04-03
**Scope**: Migrate the 278 cross-language schema validation vectors from the standalone
`validate_schema_vectors.py` runner into pytest as parametrized tests. Covers all 9
JSON-LD schemas (92 valid + 186 invalid vectors).
**Result**: 278 vector tests + 4 coverage assertions = 282 new tests in
`test_schema_validation_vectors.py`. PR #117, merged.

### S1: Trust/MRH from_dict() + SDK v0.17.0 release housekeeping
**Status**: DONE
**Completed**: 2026-04-04
**Depends on**: N1-R1, M1
**Scope**: Add `from_dict()` classmethods to T3 and V3 in `web4/trust.py` and MRHNode
and MRHEdge in `web4/mrh.py` — the last 4 classes with serialization methods but no
`from_dict()`. Version bump 0.16.0 to 0.17.0, CHANGELOG.md entry, SESSION_FOCUS.md and
SPRINT.md updates.
**Result**: 4 from_dict() methods, 27 round-trip tests (16 trust + 11 mrh). CHANGELOG
v0.17.0 documents 35 total from_dict() methods and 278 schema vectors. 2183 tests passing.

---

## Sprint 14: Optional Extras and Release Polish (2026-03-29)

The validation module and CLI require `jsonschema`, but it's only available in the
`dev` extras group. Users who `pip install web4` and try `web4 validate` get a
confusing error. This sprint adds a `validation` optional extra and updates
documentation to reflect the current SDK state.

### K1: Validation optional extra + README coherence + v0.16.0 release
**Status**: DONE
**Completed**: 2026-03-29
**Depends on**: J1 (CLI module), H1 (validation module)
**Scope**: Add `validation = ["jsonschema>=4.0"]` to pyproject.toml optional deps.
Update error messages in `validation.py` and `__main__.py` to suggest
`pip install web4[validation]`. Update README.md for v0.16.0 (20 modules, 344
exports, CLI docs, validation extra). Bump version 0.15.0 → 0.16.0, CHANGELOG entry.
**Result**: `pip install web4[validation]` works. README accurate. Error messages
guide users to the correct install command. Version 0.16.0. 1770 tests, zero regressions.

---

## Sprint 13: SDK CLI & Distribution Readiness (2026-03-29)

The SDK has 20 modules, 344 exports, and a validation module — but no CLI and schemas
only work from repo checkouts. This sprint adds a CLI entry point and bundles schemas
as package data so `pip install web4` works end-to-end.

### J1: CLI module (`web4/__main__.py`)
**Status**: DONE
**Completed**: 2026-03-29
**Depends on**: H1 (validation module)
**Scope**: Create `web4/__main__.py` with three subcommands: `validate` (validate
JSON-LD documents against web4 schemas, with `--schema` flag and `@type`
auto-detection), `info` (show SDK version, module count, export count, schema count),
`list-schemas` (list all available schemas). Uses argparse (stdlib only). Wire
`web4` console script into `pyproject.toml` `[project.scripts]`. Tests via
subprocess invocation.
**Result**: `web4/__main__.py` with 3 subcommands. Schema auto-detection from `@type`
field (30+ type mappings covering all JSON-LD types with and without `web4:` prefix).
Stdin support (`-` as file path). Clear error messages for missing files, invalid JSON,
unknown schemas, and missing jsonschema dependency. Console script entry point wired.
22 tests covering all subcommands, error cases, auto-detection, and help output.
Mypy strict clean. 1774 tests passing, zero regressions.

### I1: Bundle JSON Schemas as package data
**Status**: DONE
**Completed**: 2026-03-30
**Depends on**: H1 (validation module)
**Scope**: Bundle all 12 JSON Schemas into the SDK wheel so `pip install web4`
works without a repo checkout. Single `schema_registry.json` file (all schemas
in one keyed JSON object) instead of copying 12 individual files. Refactor
`validation.py` to use `importlib.resources` for bundled registry as primary
source with repo-walk fallback. Add tests. Verify with wheel build and clean
venv install.
**Result**: Single `schema_registry.json` (96KB, all 12 schemas). `validation.py`
refactored: `_load_bundled_registry()` via `importlib.resources`, `_load_schema()`
checks registry → directory fallback. `pyproject.toml` updated with package-data.
4 new tests covering registry loading and schema resolution. Wheel build verified:
registry present. Clean venv install verified: `validate()` works from
`site-packages`. 1774 tests passing (4 new), mypy strict clean, zero regressions.
1 new file (within 5-file constraint).

---

## Sprint 12: Schema Validation Integration (2026-03-29)

The SDK produces JSON-LD via `to_jsonld()` for all 10 types and has JSON Schemas in
`web4-standard/schemas/`. But there was no way to validate documents against those schemas
from within the SDK. This sprint closes that gap with a validation module.

### H1: Schema validation module (`web4/validation.py`)
**Status**: DONE
**Completed**: 2026-03-29
**Depends on**: None
**Scope**: Create `web4/validation.py` module that loads JSON schemas from
`web4-standard/schemas/` and validates JSON-LD documents against them. `jsonschema` as
optional dependency with graceful degradation. Public API: `validate()`, `list_schemas()`,
`get_schema()`, `get_schema_dir()`. Tests covering all 9 JSON-LD schema types with both
valid SDK output and invalid documents.
**Result**: 20th SDK module with 8 public symbols. Schema directory auto-detected via
repo-relative walk (with `WEB4_SCHEMA_DIR` env override). 12 named schemas (9 JSON-LD +
3 standalone). 33 tests covering all schema types, error handling, caching, and
directory resolution. Mypy strict clean. 1748 tests passing, zero regressions.

### H2: SDK v0.15.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-29
**Depends on**: H1
**Scope**: Version bump 0.14.0 → 0.15.0, CHANGELOG.md entry documenting Sprint 12.
**Result**: Version bumped in pyproject.toml. CHANGELOG.md v0.15.0 entry documents
Sprint 11 (G3: mypy strict, G4: README coherence) and Sprint 12 (H1: validation module).
SESSION_FOCUS.md updated with current SDK status (20 modules, 344 exports, 1748 tests).
Sprint 12 complete (2/2 tasks).

---

## Sprint 11: Code Quality Gates (2026-03-28)

Sprint 10 established CI with pytest (4 Python versions) and mypy. Follow-up sessions
add ruff linting, coverage reporting (PR #98), and mypy strict compliance to complete the
quality gate trifecta: lint + typecheck + test with coverage.

### G4: SDK README coherence update
**Status**: DONE
**Completed**: 2026-03-29
**Depends on**: None
**Scope**: The SDK README.md documented `web4_sdk.py` (async HTTP client, v1.0.0)
rather than the actual `web4` package (19 modules, 336 exports, v0.14.0). Rewrite
to accurately reflect installation, module structure, usage patterns, JSON-LD
serialization, error handling, and testing. All code examples verified against
the actual API.
**Result**: README reduced from 688 lines of outdated content to a focused,
accurate document. Covers all 19 modules, correct import patterns, verified
code examples, JSON-LD round-trip, error handling, testing commands, and project
structure. `web4_sdk.py` HTTP client retained as secondary section.

### G3: Mypy strict compliance + .gitignore housekeeping
**Status**: DONE
**Completed**: 2026-03-28
**Depends on**: None (complements G1+G2 in PR #98)
**Scope**: Fix all 72 `mypy --strict` errors across 13 SDK source files (46 type-arg,
17 no-untyped-def, 9 no-any-return). Add missing `.gitignore` entries for build/test
artifacts (.coverage, htmlcov/, .mypy_cache/, .ruff_cache/).
**Result**: All 72 errors fixed across 13 files: parameterized bare `Dict`/`dict`/`set`/`tuple`
annotations, added return type annotations to `__init__`/`__post_init__` methods, added
`bool()` casts for `Any`-typed comparisons, added explicit `type[Web4Error]` annotations.
`.gitignore` updated with 4 new entries. `mypy --strict web4/` passes with 0 errors.
1715 tests passing, zero regressions.

---

## Sprint 10: CI/CD & Packaging Quality (2026-03-27)

Sprints 4-9 built a comprehensive SDK: 19 modules, 336 exports, 1715 tests, 278 cross-language
validation vectors, full docstrings and type annotations. However, none of this is verified in
CI — there are no GitHub Actions workflows. This sprint adds automated test verification and
improves packaging metadata so the SDK is ready for external distribution.

### F1: GitHub Actions CI workflow
**Status**: DONE
**Completed**: 2026-03-27
**Depends on**: None
**Scope**: Create `.github/workflows/sdk-test.yml` that runs the full pytest suite across
Python 3.10-3.13 on push/PR to SDK paths. Zero external dependencies — only pytest needed.

### F2: Packaging metadata improvements
**Status**: DONE
**Completed**: 2026-03-27
**Depends on**: None
**Scope**: Add project URLs (homepage, repository, issues, changelog) to `pyproject.toml`.
Add keywords for PyPI discoverability. Ensure `MANIFEST.in` includes README, CHANGELOG, and
`py.typed` in sdist. Add LICENSE file to SDK directory.
**Result**: Added `[project.urls]` (Homepage, Repository, Issues, Changelog), 10 keywords,
`MANIFEST.in` (LICENSE, README.md, CHANGELOG.md, py.typed), MIT LICENSE file. 1715 tests
passing, zero regressions.

### F3: Single-source version management
**Status**: DONE
**Completed**: 2026-03-27
**Depends on**: None
**Scope**: Version is currently hardcoded in 3 places (`pyproject.toml`, `setup.py`,
`__init__.py`). Use `importlib.metadata` or a shared `_version.py` to eliminate sync risk.
Remove redundant `setup.py` if `pyproject.toml` is sufficient.
**Result**: `pyproject.toml` is now the single source of truth. `__init__.py` reads version
via `importlib.metadata.version("web4")` with fallback. Redundant `setup.py` removed —
`pyproject.toml` with setuptools ≥64 is sufficient. 1715 tests passing, zero regressions.

### F4: SDK v0.14.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-28
**Depends on**: F1 (at minimum)
**Scope**: Version bump 0.13.0 → 0.14.0, CHANGELOG.md entry documenting Sprint 10
deliverables.
**Result**: Version bumped in `pyproject.toml`. CHANGELOG.md entry documents all Sprint 10
deliverables (F1-F3: CI workflow, packaging metadata, single-source version management).
Sprint 10 complete (4/4 tasks). 1715 tests passing.

---

## Sprint 9: SDK Documentation Completeness (2026-03-26)

Sprint 8 completed docstring coverage for mcp.py (the worst module at 13.5% → 100%). An
SDK-wide audit reveals 6 more modules below 90% docstring coverage, totaling ~51 undocumented
public methods. Additionally, 21 public methods across 5 modules lack return type annotations.
This sprint closes remaining documentation gaps so the SDK is fully self-documenting for
external consumers.

### E1: Docstring coverage for r6.py, mrh.py, security.py
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: None
**Scope**: Add docstrings to all undocumented public methods in the three worst-documented
modules: r6.py (19 methods at 69% coverage), mrh.py (7 methods at 72%), security.py
(4 methods at 77%). Total: ~30 methods. Focus on `to_dict()` methods explaining serialization
format, and property accessors explaining what they return.
**Result**: 32 docstrings added across 3 modules. r6.py: 95.4% (62/65), mrh.py: 93.5%
(29/31), security.py: 81.5% (22/27). Remaining undocumented are dunder/private methods
(__init__, __post_init__, __eq__, __hash__, __str__, _generate_id). 1715 tests passing,
zero regressions.

### E2: Docstring coverage for reputation.py, protocol.py, acp.py
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: None
**Scope**: Add docstrings to remaining undocumented public methods in reputation.py
(3 methods at 81%), protocol.py (5 methods at 84%), acp.py (11 methods at 84%).
Total: ~19 methods.
**Result**: 17 docstrings added across 3 modules (reputation.py: 3, protocol.py: 5,
acp.py: 9). 2 of the original 11 acp.py symbols were inner functions (visit, dfs) —
not public API. 1715 tests passing, zero regressions.

### E3: Return type annotations for public methods
**Status**: DONE
**Completed**: 2026-03-27
**Depends on**: None
**Scope**: Add return type annotations to all public methods across 5 modules (acp.py,
federation.py, lct.py, dictionary.py, trust.py) that currently lack them.
Improves static analysis, IDE support, and mypy compatibility.
**Result**: 33 `-> None` annotations added across 5 modules: acp.py (15), federation.py (8),
dictionary.py (4), trust.py (4), lct.py (2). Covers public methods, `__init__`, and
`__post_init__`. 1715 tests passing, zero regressions.

### E4: SDK v0.13.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-27
**Depends on**: E1 (at minimum)
**Scope**: Version bump 0.12.0 → 0.13.0, CHANGELOG.md entry documenting Sprint 9
deliverables.
**Result**: Version bumped in __init__.py, pyproject.toml, setup.py. CHANGELOG.md
documents E1-E4 deliverables. Sprint 9 complete (4/4 tasks).

---

## Sprint 8: SDK Developer Experience (2026-03-26)

Sprints 1-7 built the full SDK (19 modules, 284 exports, 1659 tests, 278 cross-language
validation vectors, 10 JSON-LD schemas with bidirectional roundtrip). An internal audit
reveals developer experience gaps: 48 public symbols not exported from the package root,
all 19 submodules missing `__all__` declarations, and several modules with incomplete
docstring coverage. This sprint closes DX gaps to prepare the SDK for external consumers.

### D1: Export completeness — missing public symbols
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: None
**Scope**: Add 52 public symbols across 10 modules to `web4/__init__.py` that were
previously accessible only via direct submodule import:
- ATP core operations: `transfer`, `sliding_scale`, `check_conservation`, `sybil_cost`,
  `fee_sensitivity` (5 functions)
- R7 exceptions + component classes: `R7Error` + 7 subclasses, `Constraint`, `Reference`,
  `Precedent`, `TensorDelta`, `ContributingFactor` (13 symbols)
- ACP exceptions + guard: `NoValidGrant`, `ScopeViolation`, `ApprovalRequired`,
  `WitnessDeficit`, `PlanExpired`, `LedgerWriteFailure`, `InvalidTransition`,
  `ResourceCapExceeded`, `HumanApproval` (9 symbols)
- Federation serialization: 6 `_to_dict` + 6 `_from_dict` functions for Norm, Procedure,
  Interpretation, LawDataset, Delegation, QuorumPolicy (12 functions)
- Dictionary types: `AmbiguityHandling`, `ChainStep`, `EvolutionConfig`, `FeedbackRecord`
  (4 classes)
- Trust utilities: `RoleTensors`, `trust_bridge`, `diminishing_returns` (3 symbols)
- LCT sub-types (aliased): `LCTBinding`, `LCTMRH`, `LCTMRHPairing`, `LCTPolicy` (4 aliases)
- Entity lookup: `get_info` (1 function)
- MRH helper: `relation_category` (1 function)
**Result**: 52 new exports (284 → 336 total). 35 new tests in `test_package_api.py`
with roundtrip validation for federation helpers and functional tests for ATP operations.
1694 tests passing, zero regressions.

### D2: Submodule `__all__` declarations
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: D1
**Scope**: Add `__all__` list to each of the 19 submodules (`trust.py`, `lct.py`, etc.)
so that `from web4.trust import *` works correctly and IDEs can autocomplete submodule
imports. Extract the symbol list from the corresponding `web4/__init__.py` import group
plus any module-internal public symbols.
**Result**: All 19 submodules now have `__all__` declarations (375 total symbols across
submodules). 21 new tests in `test_package_api.py` verify consistency (all entries resolve,
no duplicates, submodule count). 1715 tests passing, zero regressions.

### D3: Docstring coverage for mcp.py
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: None
**Scope**: Add docstrings to the 32 undocumented public functions/methods in `web4/mcp.py`.
This module has the worst documentation coverage (13.5%) in the SDK. Focus on class-level
docstrings, constructor parameters, and return types.
**Result**: All 32 previously undocumented `to_dict()` and `from_dict()` methods now have
docstrings. Coverage went from 13.5% to 100% (56/56 public symbols documented).
1715 tests passing, zero regressions.

### D4: SDK v0.12.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: D1 (at minimum)
**Scope**: Version bump 0.11.0 → 0.12.0, CHANGELOG.md entry documenting Sprint 8
deliverables.
**Result**: Version bumped in `__init__.py`, `pyproject.toml`, `setup.py`. CHANGELOG.md
v0.12.0 section documents D1 (export completeness), D2 (submodule `__all__`), D3
(mcp.py docstrings). Sprint 8 complete (4/4 tasks). 1715 tests passing.

---

## Sprint 7: SDK API Completeness (2026-03-24)

Sprints 3-6 delivered JSON-LD serialization for all 10 core types with schemas, context
files, and 278 cross-language validation vectors. However, an API audit reveals asymmetries:
3 module-level `to_jsonld()` functions lack `from_jsonld()` inverses (write-only export),
the ATP module has no direct unit tests, and `BirthCertificate.context` diverges from the
spec's `birth_context` field name. This sprint closes these API gaps before v0.11.0.

### C1: Missing from_jsonld() inverse functions
**Status**: DONE
**Completed**: 2026-03-24
**Depends on**: None
**Scope**: Add `from_jsonld()` counterparts for the 3 module-level serialization functions
that currently only have `to_jsonld()`:
1. `entity_registry_from_jsonld(doc)` → `Dict[EntityType, EntityTypeInfo]` in `web4/entity.py`
2. `capability_assessment_from_jsonld(doc)` → assessment dict in `web4/capability.py`
3. `capability_framework_from_jsonld(doc)` → framework dict in `web4/capability.py`

Schemas already specify the format (`entity-jsonld.schema.json`, `capability-jsonld.schema.json`).
Export new functions from `web4/__init__.py`. Add roundtrip tests.
**Result**: 3 `from_jsonld()` inverses plus 3 `from_jsonld_string()` convenience wrappers.
New `CapabilityAssessment` dataclass. 7 new exports (284 total). 14 new tests with roundtrip
validation. PR #81, merged.

### C2: ATP core unit tests
**Status**: DONE
**Completed**: 2026-03-25
**Depends on**: None
**Scope**: Create `tests/test_atp.py` with direct unit tests for core ATP operations
(transfer, sliding_scale, recharge, conservation invariants). Currently only JSON-LD
serialization tests exist (`test_atp_jsonld.py`). Follow `test_acp.py` pattern.
**Result**: 74 tests covering all 8 ATP public functions/classes. Validates all 15
cross-language ATP test vectors. PR #82, merged.

### C3: BirthCertificate field naming harmonization
**Status**: DONE
**Completed**: 2026-03-25
**Depends on**: None
**Scope**: Rename `BirthCertificate.context` → `BirthCertificate.birth_context` to align
with LCT spec §2.3 and JSON-LD output. The field currently uses `context` internally but
serializes as `birth_context` — creating asymmetric round-trips. Breaking change requiring
`from_jsonld()` backward compatibility (accept both field names).
**Result**: 9 files modified, 34-line symmetric diff. `from_jsonld()` retains backward
compat (accepts both field names). 1571 tests passing, zero regressions. PR #83, merged.

### C4: SDK v0.11.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-26
**Depends on**: C1 (at minimum)
**Scope**: Version bump 0.10.1 → 0.11.0, CHANGELOG.md entry documenting Sprint 7
deliverables.
**Result**: Version bumped in `__init__.py`, `pyproject.toml`, `setup.py`. CHANGELOG.md
v0.11.0 section documents C1 (from_jsonld inverses), C2 (ATP unit tests), C3
(BirthCertificate rename), Dictionary validation vectors. Sprint 7 complete (4/4 tasks).
1659 tests passing.

---

## Sprint 6: JSON-LD Context Consolidation & SDK Quality (2026-03-23)

Sprints 3-5 delivered JSON-LD serialization for all 8 core types with JSON Schemas
and 228 cross-language test vectors. However, an audit reveals inconsistencies in the
JSON-LD context layer: 2 missing context files, a namespace split (`ontology#` vs `ns/`),
and no programmatic schema validation in the SDK. This sprint consolidates the JSON-LD
foundation before building on it.

### B1: SDK v0.10.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-23
**Depends on**: None
**Scope**: Update CHANGELOG.md to document A3 (Entity+Capability JSON-LD, 5 new exports),
A4 complete (127 total vectors, up from 59 partial documented in v0.9.0), and B6
(Dictionary JSON-LD). Bump SDK version 0.9.0 → 0.10.0.
**Result**: CHANGELOG v0.10.0 entry documents A3, A4 complete, and B6. Version bumped
in `__init__.py`, `pyproject.toml`, `setup.py`. 277 symbols in `__all__` (up from 269).
1465 tests passing.

### B2: Missing JSON-LD context files for LCT and AttestationEnvelope
**Status**: DONE
**Completed**: 2026-03-23
**Depends on**: None
**Scope**: Create `lct.jsonld` and `attestation-envelope.jsonld` context files in
`web4-standard/schemas/contexts/`. LCT and AttestationEnvelope Python constants
(`LCT_JSONLD_CONTEXT`, `ATTESTATION_JSONLD_CONTEXT`) reference context URIs that don't
exist as files. All other 6 types have external context files. These 2 are the gap.
Extract term mappings from the Python `to_jsonld()` output and create context files
matching the pattern used by ATP/ACP/Entity/Capability contexts (namespace: `https://web4.io/ns/`).
**Result**: 2 `.jsonld` context files (lct.jsonld: 30+ term mappings, attestation-envelope.jsonld:
25+ term mappings). 26 consistency tests verifying all to_jsonld() keys have context mappings.
Fixed 3 type errors in attestation context (timestamp/TTL as xsd:double, PCR selection as @list).
1477 total tests passing.

### B3: JSON-LD namespace and context URI reconciliation
**Status**: DONE
**Completed**: 2026-03-24
**Depends on**: B2
**Scope**: Audit and reconcile the namespace split across all 8 types. Currently:
- T3/V3 and R7 use `https://web4.io/ontology#` (from TTL ontology files)
- ATP/ACP/Entity/Capability use `https://web4.io/ns/` (from schemas/contexts/)
- LCT and AttestationEnvelope reference `https://web4.io/contexts/` URIs

Determine canonical namespace strategy (likely `https://web4.io/ns/` for all, with
`ontology#` reserved for OWL/RDF class definitions). Document the decision. Update
context files and Python constants for consistency. Preserve backward compatibility
in `from_jsonld()` (accept both old and new namespace URIs).
**Result**: Decision: `https://web4.io/ns/` canonical for all application contexts;
`ontology#` reserved for OWL/RDF. Created 3 new context files (`t3.jsonld`, `v3.jsonld`,
`r7-action.jsonld`) in `schemas/contexts/` using `ns/` namespace. Updated T3/V3 constants
and removed bare `WEB4_ONTOLOGY_NS` from @context arrays. R7 context maps both snake_case
(from to_jsonld) and camelCase (from nested to_dict) field names. 32 consistency tests.
Decision doc: `docs/history/design_decisions/JSONLD-NAMESPACE-RECONCILIATION.md`.
1523 total tests passing.

### B4: Schema-validated JSON-LD round-trip tests
**Status**: DONE
**Completed**: 2026-03-24
**Depends on**: B2, B3
**Scope**: Add integration tests that validate all 9 `to_jsonld()` schemas (19 @type
values) programmatically using `jsonschema`. Pattern: create object → `to_jsonld()` →
validate against schema → `from_jsonld()` → assert equality.
**Result**: `tests/test_jsonld_schema_roundtrip.py` — 48 tests covering all 9 JSON-LD
schemas and 19 distinct @type values: LCT, AttestationEnvelope, T3Tensor, V3Tensor,
R7Action, ATPAccount, TransferResult, AgentPlan, Intent, Decision, ExecutionRecord,
EntityTypeInfo, EntityTypeRegistry, LevelRequirement, CapabilityAssessment,
CapabilityFramework, DictionarySpec, TranslationResult, TranslationChain, DictionaryEntity.
Includes per-type schema validation, round-trip fidelity, and a parametrized summary test
that validates all types in one pass. 1571 total tests passing.

### B5: SDK v0.10.1 release housekeeping
**Status**: DONE
**Completed**: 2026-03-24
**Depends on**: B2, B3, B4, B6
**Scope**: Version bump and CHANGELOG entry documenting B2-B6 deliverables.
**Result**: CHANGELOG.md v0.10.1 entry documents B2 (missing context files), B3
(namespace reconciliation), B4 (schema-validated round-trip tests). Version bumped
0.10.0 → 0.10.1 in `__init__.py`, `pyproject.toml`, `setup.py`. Sprint 6 complete
(6/6 tasks). 1571 tests passing.

### B6: Dictionary JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-23
**Depends on**: None
**Scope**: Add `to_jsonld()` / `from_jsonld()` to DictionarySpec, TranslationResult,
TranslationChain, and DictionaryEntity in `web4.dictionary`. JSON Schema
(`dictionary-jsonld.schema.json`) and JSON-LD context (`contexts/dictionary.jsonld`).
**Result**: 4 types with JSON-LD serialization (DictionarySpec, TranslationResult,
TranslationChain, DictionaryEntity). JSON Schema with 4 type definitions and 4
reusable sub-schemas (DomainCoverage, CompressionProfile, ChainStep, DictionaryType).
JSON-LD context (`contexts/dictionary.jsonld`). 1 new export (`DICTIONARY_JSONLD_CONTEXT`).
14 new tests, 1463 total SDK tests passing.

---

## Sprint 5: Core Type JSON-LD Phase 2 (2026-03-21)

Sprint 4 delivered JSON-LD for the highest-priority types (LCT, AttestationEnvelope,
R7Action, T3/V3). Sprint 5 extends JSON-LD serialization to the next tier of core
types needed for cross-language interoperability.

### A1: ATP/ADP JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-21
**Scope**: Add `to_jsonld()` / `from_jsonld()` to `ATPAccount` and `TransferResult`
in `web4.atp`, producing RDF-aligned JSON-LD documents. JSON Schema
(`atp-jsonld.schema.json`) and JSON-LD context (`contexts/atp.jsonld`).
**Result**: `ATPAccount.to_jsonld()` / `from_jsonld()`, `TransferResult.to_jsonld()` /
`from_jsonld()`. JSON Schema with ATPAccount and TransferResult definitions.
JSON-LD context mapping snake_case fields to web4 namespace.
2 new exports (`TransferResult`, `ATP_JSONLD_CONTEXT`). 28 new tests, 1302 total
SDK tests passing.

### A2: ACP JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-21
**Depends on**: None
**Scope**: Add `to_jsonld()` / `from_jsonld()` to ACP types (AgentPlan, Intent,
Decision, ExecutionRecord) in `web4.acp`. JSON Schema and JSON-LD context.
**Result**: `AgentPlan.to_jsonld()` / `from_jsonld()`, `Intent.to_jsonld()` /
`from_jsonld()`, `Decision.to_jsonld()` / `from_jsonld()`,
`ExecutionRecord.to_jsonld()` / `from_jsonld()`. JSON Schema
(`acp-jsonld.schema.json`) with 4 type definitions and 6 reusable sub-schemas.
JSON-LD context (`contexts/acp.jsonld`). 1 new export (`ACP_JSONLD_CONTEXT`).
54 new tests, 1356 total SDK tests passing.

### A3: Entity + Capability JSON-LD
**Status**: DONE
**Completed**: 2026-03-23
**Depends on**: None
**Scope**: Add `to_jsonld()` / `from_jsonld()` to EntityTypeInfo and LevelRequirement
types, plus registry/framework/assessment serializers. JSON Schema and JSON-LD context.
**Result**: `EntityTypeInfo.to_jsonld()` / `from_jsonld()`, `entity_registry_to_jsonld()`,
`LevelRequirement.to_jsonld()` / `from_jsonld()`, `capability_assessment_to_jsonld()`,
`capability_framework_to_jsonld()`. JSON Schemas (`entity-jsonld.schema.json`,
`capability-jsonld.schema.json`). JSON-LD contexts (`entity.jsonld`, `capability.jsonld`).
5 new exports (`ENTITY_JSONLD_CONTEXT`, `entity_registry_to_jsonld`,
`CAPABILITY_JSONLD_CONTEXT`, `capability_assessment_to_jsonld`,
`capability_framework_to_jsonld`). 37 new tests, 1393 total SDK tests passing.

### A4: Cross-language validation vectors for Phase 2
**Status**: DONE
**Completed**: 2026-03-23
**Depends on**: A1, A2, A3
**Scope**: JSON test vectors for ATP, ACP, Entity, Capability schemas.
**Result**: 127 vectors for all 4 Phase 2 schemas.
ATP: 8 valid + 15 invalid = 23 vectors (ATPAccount and TransferResult types).
ACP: 12 valid + 24 invalid = 36 vectors (AgentPlan, Intent, Decision, ExecutionRecord types).
Entity: 12 valid + 20 invalid = 32 vectors (EntityTypeInfo and EntityTypeRegistry types).
Capability: 12 valid + 24 invalid = 36 vectors (LevelRequirement, CapabilityAssessment, CapabilityFramework types).
Validation runner updated to include all 8 schemas. 228 total vectors across all schemas.

### A5: SDK v0.9.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-22
**Depends on**: A1 (at minimum)
**Scope**: Version bump, CHANGELOG.md entry for Sprint 5 deliverables.
**Result**: Version bumped 0.8.0 → 0.9.0 in `__init__.py`, `pyproject.toml`, `setup.py`.
CHANGELOG.md v0.9.0 section documents A1 (ATP JSON-LD), A2 (ACP JSON-LD),
A4 partial (59 validation vectors), and 3 new exports. 269 symbols, 1356 tests passing.

---

## Sprint 4: Cross-Language Schema Standardization (2026-03-20)

Sprint 3 produced spec-compliant JSON-LD serialization for LCT and AttestationEnvelope.
This sprint provides formal JSON Schema files so that Go/TypeScript/Rust implementations
can validate their serialization output against a machine-readable specification. It
also extends JSON-LD coverage to remaining core types.

### V1: JSON Schema for LCT and AttestationEnvelope JSON-LD
**Status**: DONE
**Completed**: 2026-03-20
**Scope**: Create JSON Schema (draft 2020-12) files for the LCT JSON-LD format (spec §2.3)
and AttestationEnvelope JSON-LD format. Include a validation script that confirms current
SDK `to_jsonld()` output passes the schemas. Schemas derived from spec documents,
cross-checked against SDK output.
**Result**: `lct-jsonld.schema.json`, `attestation-envelope-jsonld.schema.json`,
`validate_schemas.py`. 19 validation checks (10 LCT + 9 AttestationEnvelope). PR #53, merged.

### V2: T3/V3 Trust Tensor JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-22
**Depends on**: V1
**Scope**: Add `to_jsonld()` / `from_jsonld()` to `T3` and `V3` classes in `web4.trust`,
producing output matching `t3v3-ontology.ttl`. JSON Schema for the format.
**Result**: `T3.to_jsonld()` / `from_jsonld()`, `V3.to_jsonld()` / `from_jsonld()` with
ontology-aligned dual representation. JSON Schema (`t3v3-jsonld.schema.json`).
58 new tests. PR #54, awaiting review.

### V3: R7 Action JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-21
**Depends on**: V1
**Scope**: Add `to_jsonld()` / `from_jsonld()` to R7 action types in `web4.r6`,
enabling cross-language representation of actions, action chains, and reputation deltas.
JSON Schema for the format.
**Result**: `R7Action.to_jsonld()` / `from_jsonld()`, `ReputationDelta.to_jsonld()` /
`from_jsonld()`, `ActionChain.to_jsonld()` / `from_jsonld()`. JSON-LD context
(`r7-action.jsonld`) and JSON Schema (`r7-action-jsonld.schema.json`). All 7 R7
components serialized (Rules/Role/Request/Reference/Resource/Result/Reputation).
26 new tests, 75 total R6 tests, 1274 total SDK tests passing. PR #55, merged.

### V4: Cross-language validation test vectors
**Status**: DONE
**Completed**: 2026-03-22
**Depends on**: V1, V2, V3
**Scope**: JSON test vectors that exercise schema validation edge cases — malformed
documents, missing required fields, extra fields, boundary values. Vectors usable
by any language's JSON Schema validator.
**Result**: 101 vectors for 4 merged schemas (LCT, AttestationEnvelope, R7 Action, T3/V3).
31 valid documents + 70 invalid documents covering: missing required fields, enum violations,
out-of-range values, pattern mismatches, type errors, additionalProperties, boundary values,
type mismatches (T3 fields with V3 @type and vice versa), DimensionScore sub-schema validation.
T3/V3 vectors: 10 valid + 28 invalid = 38 vectors.
Validation runner script (`validate_schema_vectors.py`) covers all 4 schemas.

### V5: SDK v0.8.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-21
**Depends on**: V1 (at minimum)
**Scope**: Version bump, CHANGELOG.md entry for Sprint 4 deliverables.
**Result**: Version bumped 0.7.0 → 0.8.0 in `__init__.py`, `pyproject.toml`, `setup.py`.
CHANGELOG.md v0.8.0 section documents V1 (JSON Schemas), V3 (R7 Action JSON-LD),
V4 partial (63 validation vectors), and new exports. 266 symbols, 1274 tests passing.

---

## Sprint 3: SDK Interoperability (2026-03-19)

The SDK has 19 modules with 1000+ tests, but a known gap exists: no Python
implementation produces schema-compliant LCT documents. This sprint closes
interoperability gaps between the SDK output and the spec's canonical formats.

### I1: LCT spec-compliant JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-19
**Scope**: Add `to_jsonld()` / `from_jsonld()` methods to `LCT` class producing
documents matching spec §2.3 canonical structure. Includes: `@context` header,
spec-compliant field naming (`birth_context` not `context`), structured MRH entries
(bound/witnessing as objects), optional sections (attestations, lineage) included
only when populated, full revocation structure (status + ts + reason).
New types: `Attestation`, `LineageEntry`, `LCT_JSONLD_CONTEXT`.
`BirthCertificate` gains optional `genesis_block_hash`.
`LCT.revoke()` gains optional `reason` parameter.
Backward compatible: `to_dict()` unchanged, `from_jsonld()` accepts both formats.
**Result**: 51 new tests, 1093 total passing. Closes known gap "NO Python impl
produces schema-compliant LCT document."

### I2: Cross-language LCT test vectors
**Status**: DONE
**Completed**: 2026-03-20
**Scope**: JSON test vectors for LCT JSON-LD roundtrip that TypeScript/Go/Rust
implementations can validate against. Same pattern as existing 79+ SDK vectors.
**Result**: 10 vectors covering: minimal LCT, full LCT (all optional fields), revoked,
attestations, lineage, complex MRH, boundary T3/V3, suspended status, genesis_block_hash,
no birth certificate. 110 validation tests (roundtrip, structure, values, spec compliance,
backward compat). 1203 total passing.

### I3: AttestationEnvelope JSON-LD serialization
**Status**: DONE
**Completed**: 2026-03-19
**Scope**: Add `to_jsonld()` / `from_jsonld()` to `AttestationEnvelope` in
`web4.attestation`, matching the attestation-envelope spec format.
**Result**: `AttestationEnvelope.to_jsonld()` and `from_jsonld()` with full
spec compliance. 41 tests. PR #48.

### I4: SDK v0.7.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-20
**Depends on**: I1 (at minimum)
**Scope**: Version bump 0.5.0 → 0.7.0 (0.6.0 covered by H6 PR #46),
CHANGELOG.md entry for Sprint 3 JSON-LD serialization (I1, I2, I3),
updated exports count (263 symbols).
**Result**: Version bumped in `__init__.py`, `pyproject.toml`, `setup.py`.
CHANGELOG.md v0.7.0 section documents LCT JSON-LD, cross-language vectors,
and AttestationEnvelope JSON-LD. 1093 tests passing, zero regressions.

---

## Sprint 2: Hardware Trust Validation (2026-03-19)

The AttestationEnvelope landed on main (3 commits by operator, 2026-03-18) as the P0
hardware binding primitive. It has a spec, implementation, and verification dispatch —
but zero test coverage. This sprint validates the new code and prepares it for
integration with the SDK.

### H1: AttestationEnvelope test coverage
**Status**: DONE
**Completed**: 2026-03-19
**Scope**: Comprehensive tests for `web4-core/python/web4/trust/attestation/envelope.py` —
construction, defaults, auto-computed fields (fingerprint, trust ceiling), serialization
round-trips (to_dict/from_dict, to_json/from_json), freshness model (is_fresh,
freshness_factor, effective_trust), and edge cases.
**Result**: 49 tests in `test_envelope.py` — all passing.

### H2: Verification dispatch test coverage
**Status**: DONE
**Completed**: 2026-03-19
**Scope**: Tests for `verify_envelope()` dispatch and all 4 anchor verifiers —
software (end-to-end), TPM2/FIDO2/SE (stub behavior), challenge mismatch,
unknown anchor type, PCR validation.
**Result**: 42 tests in `test_verify.py` — all passing. Parametrized cross-anchor consistency tests.

### H3: Cross-language test vectors for attestation
**Status**: DONE
**Completed**: 2026-03-19
**Scope**: JSON test vectors for AttestationEnvelope construction, trust ceilings,
freshness model, serialization, and verification dispatch. Python validator script.
**Result**: 35 vectors in `web4-standard/test-vectors/attestation/attestation-vectors.json`,
validator in `validate_attestation_vectors.py` — all passing.

### H4: SDK integration for AttestationEnvelope
**Status**: DONE
**Completed**: 2026-03-19
**Depends on**: H1, H2
**Scope**: Evaluate whether `web4-core/` attestation types should be re-exported from
the `web4` SDK package or remain separate. If integrating, add to `web4/__init__.py`.
**Decision**: Mirror into SDK (not re-export from web4-core). Rationale: namespace collision
between web4-core and web4-standard SDK (both define `web4` package), SDK has zero imports
from web4-core, attestation types are pure Python (stdlib only). Created `web4/attestation.py`
consolidating all types + verify_envelope dispatcher + 4 anchor verifiers.
**Result**: `web4.attestation` module — 8 new symbols in `web4/__init__.py`
(AttestationEnvelope, AnchorInfo, Proof, PlatformState, VerificationResult, TRUST_CEILINGS,
FRESHNESS_MAX_AGE, verify_envelope). 41 tests, 1015 total passing.

### H5: AttestationEnvelope + binding module integration
**Status**: DONE
**Completed**: 2026-03-19
**Depends on**: H4
**Scope**: Wire AttestationEnvelope into the existing `web4.binding` module
(DeviceConstellation, HardwareAnchor). The binding module already has AnchorType
and trust ceiling concepts — these should use AttestationEnvelope as the proof carrier.
**Result**: Bidirectional AnchorType↔attestation mapping (`ANCHOR_TYPE_TO_ATTESTATION`,
`attestation_anchor_type()`, `binding_anchor_type()`), `DeviceRecord.latest_attestation`
optional field, `enroll_device()` validates attestation purpose + anchor type compatibility,
`compute_device_trust()` combines anchor weight × witness freshness × attestation freshness.
`compute_constellation_trust()` now uses attestation-aware per-device trust (backward
compatible). 27 integration tests, 1042 total passing.

### H6: SDK v0.6.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-20
**Scope**: Version bump (0.5.0 -> 0.6.0) and changelog for the attestation module
that landed in H4. Sprint 2 status update.
**Result**: CHANGELOG.md v0.6.0 entry. PR #46, merged.

---

## Sprint 1 (Complete)

## Active Tasks

### U5: Entity type taxonomy module
**Status**: DONE
**Completed**: 2026-03-16
**Result**: `web4.entity` module — 284 lines, 48 tests, 5 vectors. PR #20, merged.

### U9: Society metabolic states module
**Status**: DONE
**Completed**: 2026-03-17
**Result**: `web4.metabolic` module — 300 lines, 71 tests, 12 vectors. PR #23, merged.

### U10: T3/V3 tensor enhancements
**Status**: DONE
**Completed**: 2026-03-17
**Result**: ActionOutcome enum, outcome-based T3 evolution, decay/refresh, RoleRequirement, V3.calculate(), compute_team_t3(). 51 new tests, 5 vectors. Extended trust.py.

### U6: Capability levels module
**Status**: DONE
**Completed**: 2026-03-17
**Result**: `web4.capability` module — 6-level LCT capability framework (Stub → Hardware) per lct-capability-levels.md spec. 42 tests, cross-language vectors. PR #26, merged.

### U7: Error taxonomy module
**Status**: DONE
**Completed**: 2026-03-17
**Result**: `web4.errors` module — 353 lines, 42 tests, 5 vectors. 24 error codes across 6 categories with RFC 9457 Problem Details serialization. PR #27, merged.

### U11: Society core module
**Status**: DONE
**Completed**: 2026-03-17
**Spec**: `web4-standard/core-spec/SOCIETY_SPECIFICATION.md`
**Result**: `web4.society` module — 766 lines, 86 tests, 6 vectors. Composes federation, metabolic, atp, trust, lct, entity modules into society orchestration layer. PR #31, merged.

### U12: SDK v0.4.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-18
**Result**: Fixed missing metabolic module re-exports in web4_sdk.py (22 symbols), bumped version to 0.4.0, CHANGELOG.md documents 6 new + 2 enhanced modules since v0.3.0. SPRINT.md updated (U7/U11 → DONE).

### U14: Core protocol types module
**Status**: DONE
**Spec**: `web4-standard/core-spec/core-protocol.md`
**Description**: Implement `web4.protocol` module with handshake message types (ClientHello, ServerHello, ClientFinished, ServerFinished), PairingMethod enum, Transport enum with profiles, DiscoveryMethod enum with privacy levels, Web4URI parser/validator, and transport negotiation. Types only — no networking.

### U15: MCP protocol types module
**Status**: DONE
**Spec**: `web4-standard/core-spec/mcp-protocol.md`
**Description**: Implement `web4.mcp` module with Web4Context headers, CommunicationPattern enum, MCP resource types (tool/prompt/context), TrustRequirements, MCPSession with ATP tracking, SessionHandoff, ATP metering (calculate_mcp_cost), WitnessAttestation, MCPCapabilities/CapabilityBroadcast, MCPAuthority, MCPErrorContext. Types only — no networking or JSON-RPC.

### U16: Full-stack integration tests (all 18 modules)
**Status**: DONE
**Completed**: 2026-03-18
**Result**: Extended `test_integration.py` with 3 new cross-module test classes exercising
all 10 newer modules (security, protocol, mcp, entity, capability, errors, metabolic,
binding, society, reputation) alongside the original 8. 28 total integration tests,
928 total SDK tests passing. Validates SDK works as a coherent 18-module library.

### U17: SDK v0.5.0 release housekeeping
**Status**: DONE
**Completed**: 2026-03-18
**Result**: CHANGELOG.md updated with v0.5.0 entries for U13 (security), U14 (protocol),
U15 (mcp). Version bumped 0.4.0 → 0.5.0. SPRINT.md U13 status corrected, U16/U17 added.

### U18: SDK public API and packaging cleanup
**Status**: DONE
**Completed**: 2026-03-20
**Description**: Consolidate web4 package public API surface. Populate `web4/__init__.py`
with re-exports from all 18 modules (247 symbols, `__all__` defined). Fix `pyproject.toml`
metadata (version 0.5.0, classifiers, description). Add PEP 561 `py.typed` marker.
Fix `setup.py` consistency. `from web4 import T3, LCT, Society, R7Action` now works.
49 new tests, 974 total passing. PR #40, merged.

---

## Unscoped Tasks

These are known needs without implementation details. Each requires its own
scoping session before work begins.

### U2: Multi-device binding
**Status**: DONE
**Completed**: 2026-03-17
**Design**: `docs/designs/u2-multi-device-binding.md`
**Spec**: `web4-standard/core-spec/multi-device-lct-binding.md`
**Result**: `web4.binding` module — AnchorType (4 types), DeviceStatus, HardwareAnchor,
DeviceRecord, DeviceConstellation, constellation management (enroll/remove), trust
computation (witness freshness, coherence bonus, cross-witness density, ceiling),
cross-device witnessing, recovery quorum. 68 tests, 6 vectors. Patent-covered (305 family).

### U3: Whitepaper-SDK coherence fixes

**Status**: SCOPED (audit complete 2026-03-15)
**Depends on**: None (can proceed independently of S1)
**Audit**: `docs/audits/whitepaper-sdk-coherence-2026-03-15.md`
**Description**: Audit found 4 divergences and 3 gaps between whitepaper and SDK.
Two sub-tasks:

**U3a: SDK coherence naming fix** — DONE (2026-03-15). Renamed `coherence()`→`operational_health()`,
`is_coherent()`→`is_healthy()`, constants `COHERENCE_WEIGHTS`→`HEALTH_WEIGHTS`,
`COHERENCE_THRESHOLD`→`HEALTH_THRESHOLD`, `ReputationScore.coherence_score`→`health_score`.
All 70 tests passing. Docstring explains distinction from whitepaper identity coherence.

**U3b: Whitepaper section updates** — DONE (2026-03-15). Updated §2.4.4 to name Reputation
as the 7th component (R7 evolution). Added §2.5.4 reconciling 5-dimension conceptual model
vs graph implementation model. §2.2 entity type expansion skipped (audit rated LOW).

**Acceptance**: (a) No naming collision between SDK coherence function and whitepaper
identity coherence concept. (b) Whitepaper §2.4 references R7. (c) Whitepaper §2.5
acknowledges graph-based MRH implementation.

---

## Completed Tasks

### U8: SAL governance extensions (federation module)
**Completed**: 2026-03-16 (PR #22, merged as commit f00c35f)
**Result**: Extended `web4.federation` with SAL governance primitives — CitizenshipStatus
(5 lifecycle states), CitizenshipRecord, QuorumPolicy (3 modes), LedgerType, AuditRequest,
AuditAdjustment, Norm, Procedure, Interpretation, merge_law(). 29 new tests, 6 vectors.

### S6: Post-merge integration tests (all 8 modules)
**Completed**: 2026-03-15 (PR #14, merged as commit 8453df6)
**Result**: Extended integration tests covering cross-module workflows using all 8 SDK modules.
Workflows span trust→lct→atp→federation→r6→mrh→acp→dictionary. 298 total tests passing.

### U4: Reputation computation module
**Completed**: 2026-03-16
**Result**: `web4.reputation` module — 451 lines, 41 tests, 5 test vectors.
ReputationRule (trigger matching with modifiers), ReputationEngine (multi-rule evaluation),
ReputationStore (time-weighted aggregation + inactivity decay). SDK bumped to v0.3.0.

### S1: Merge SDK module PRs
**Completed**: 2026-03-15 (all 3 PRs merged)
**Result**: PRs #5 (R6), #6 (MRH), #7 (ACP) merged to main. All tests passing.

### S2: Cross-module integration tests
**Completed**: 2026-03-14 (PR #8, merged as commit 099e524)
**Result**: 19 integration tests covering trust+lct+atp+federation cross-module workflows.

### S3: Update web4_sdk.py re-exports
**Completed**: 2026-03-15
**Result**: web4_sdk.py imports and re-exports canonical types from all 8 modules
(trust, lct, atp, federation, r6, mrh, acp, dictionary). 51 re-exported symbols.

### S4: Archive reference implementation sprawl
**Completed**: 2026-03-14 (PR #9, merged as commit 0a514e6)
**Result**: 149 files archived to `archive/reference-implementations/`, 39 kept.
MANIFEST.md documents triage rationale.

### S5: Close stale PR #4
**Completed**: 2026-03-14
**Result**: PR #4 closed (duplicate of #5, superseded).

### S7: SDK version bump and changelog
**Completed**: 2026-03-15
**Result**: Version 0.2.0 (set during module PR merges). CHANGELOG.md covers
v0.1.0 (4 core modules) and v0.2.0 (3 new modules + full re-exports).

### U1: Dictionary entities module
**Completed**: 2026-03-15 (PR #10, merged as commit df1fca7)
**Result**: `web4.dictionary` module — 320 lines, 33 tests, 5 test vectors.

### U3a: SDK coherence naming fix
**Completed**: 2026-03-15
**Result**: Renamed `coherence()`→`operational_health()`, `is_coherent()`→`is_healthy()`,
plus constants and `ReputationScore.coherence_score`→`health_score`. Resolves naming
collision with whitepaper identity coherence (C×S×Phi×R). 70 tests passing.

### U3b: Whitepaper section updates
**Completed**: 2026-03-15
**Result**: Updated §2.4.4 to name Reputation as the 7th component (R7 evolution).
Added §2.5.4 reconciling 5-dimension conceptual model vs graph implementation model.
Addresses audit findings D2 (MEDIUM) and D3 (MEDIUM).

### U13: Security primitives module
**Status**: DONE
**Completed**: 2026-03-18
**Spec**: `web4-standard/core-spec/security-framework.md`, `web4-standard/core-spec/data-formats.md`
**Result**: `web4.security` module — 339 lines, 51 tests, 12 vectors. CryptoSuite definitions
(W4-BASE-1, W4-FIPS-1), W4ID (DID:web4) parsing/validation/pairwise derivation, KeyPolicy types,
SignatureEnvelope, VerifiableCredential. Types-only — no crypto implementations. PR #34, merged.

---

## Task ID Reference

| ID | Summary | Status |
|----|---------|--------|
| S1 | Merge SDK module PRs (#5, #6, #7) | DONE |
| S2 | Cross-module integration tests (main) | DONE |
| S3 | Update web4_sdk.py re-exports | DONE |
| S4 | Archive reference sprawl | DONE |
| S5 | Close stale PR #4 | DONE |
| S6 | Post-merge integration tests (all 8) | DONE |
| S7 | SDK version bump + changelog | DONE |
| U1 | Dictionary entities module | DONE |
| U2 | Multi-device binding | DONE |
| U3 | Whitepaper-SDK coherence fixes | DONE (U3a + U3b) |
| U4 | Reputation computation module | DONE |
| U5 | Entity type taxonomy module | DONE |
| U6 | Capability levels module | DONE |
| U7 | Error taxonomy module | DONE |
| U8 | SAL governance extensions | DONE |
| U9 | Society metabolic states module | DONE |
| U10 | T3/V3 tensor enhancements | DONE |
| U11 | Society core module | DONE |
| U12 | SDK v0.4.0 release housekeeping | DONE |
| U13 | Security primitives module | DONE |
| U14 | Core protocol types module | DONE |
| U15 | MCP protocol types module | DONE |
| U16 | Full-stack integration tests (18 modules) | DONE |
| U17 | SDK v0.5.0 release housekeeping | DONE |
| U18 | SDK public API and packaging cleanup | DONE |
| H1 | AttestationEnvelope test coverage | DONE |
| H2 | Verification dispatch test coverage | DONE |
| H3 | Cross-language attestation test vectors | DONE |
| H4 | SDK integration for AttestationEnvelope | DONE |
| H5 | AttestationEnvelope + binding integration | DONE |
| H6 | SDK v0.6.0 release housekeeping | DONE |
| I1 | LCT spec-compliant JSON-LD serialization | DONE |
| I2 | Cross-language LCT test vectors | DONE |
| I3 | AttestationEnvelope JSON-LD serialization | DONE |
| I4 | SDK v0.7.0 release housekeeping | DONE |
| V1 | JSON Schema for LCT + AttestationEnvelope JSON-LD | DONE |
| V2 | T3/V3 Trust Tensor JSON-LD serialization | DONE |
| V3 | R7 Action JSON-LD serialization | DONE |
| V4 | Cross-language validation test vectors | DONE |
| V5 | SDK v0.8.0 release housekeeping | DONE |
| A1 | ATP/ADP JSON-LD serialization | DONE |
| A2 | ACP JSON-LD serialization | DONE |
| A3 | Entity + Capability JSON-LD | DONE |
| A4 | Cross-language validation vectors (Phase 2) | DONE |
| A5 | SDK v0.9.0 release housekeeping | DONE |
| I1 | Bundle JSON Schemas as package data | DONE |
| J1 | CLI module (`web4/__main__.py`) | DONE |
