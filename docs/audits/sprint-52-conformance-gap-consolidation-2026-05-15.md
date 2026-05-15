# Sprint 52 Conformance Gap Consolidation

**Date**: 2026-05-15
**Sprint context**: Follow-up to Sprint 52 T1 (PR #189, merged 2026-05-15T05:07Z)
**Scope**: Catalogue the 8 conformance xfails wired by Sprint 52, map each to its
audit origin, classify by actionability tier, and propose Sprint 53+ candidates.
**Source**: `web4-standard/implementation/sdk/tests/test_conformance.py` and
`web4-standard/testing/conformance/{tensor,atp,r6-r7,society}-*.json`.

## Why this memo exists

Sprint 52 wired the operator-shipped conformance vectors into pytest. Of the
39 tests, **8 land as `pytest.mark.xfail` (strict) with documented divergence
reasons**. Each xfail is a real surface gap, but their nature is heterogeneous:
some restate findings from prior code-reading audits (Sprint 47, Sprint 49),
some surface gaps that no prior audit caught, and some are architectural design
splits where it isn't yet clear whether the SDK or the vector should change.

A "fix the conformance xfails" sprint would be a category error: the xfails
are not a uniform fix queue. This memo separates the queue.

## The 8 xfails

| # | Test | Suite | Failure source |
|---|------|-------|----------------|
| 1 | `t3-002` weighted vs unweighted aggregate | tensor-operations | `pytest.xfail()` at `test_conformance.py:115` |
| 2 | `t3-004` update direction (quality vs success flag) | tensor-operations | `pytest.xfail()` at `test_conformance.py:174` |
| 3 | `t3-006` talent decay vs talent invariant | tensor-operations | `pytest.xfail()` at `test_conformance.py:213` |
| 4 | `r6-val-004` witness quorum constraint enforcement | r6-r7-actions | `@pytest.mark.xfail` at `test_conformance.py:526` |
| 5 | `r7-rep-001` V3 valuation in reputation delta | r6-r7-actions | `pytest.xfail()` at `test_conformance.py:575` |
| 6 | `role-004` assigner authorization predicate | society-roles | `@pytest.mark.xfail` at `test_conformance.py:807` |
| 7 | `fed-001` join/secede vs incorporate_child | society-roles | `@pytest.mark.xfail` at `test_conformance.py:826` |
| 8 | `sub-001` T3 sub-dimension rollup | tensor-operations | `@pytest.mark.xfail` at `test_conformance.py:887` |

## Audit-origin mapping

### Known-class (3 of 8): Sprint 47 T3/V3 cross-language audit

Sprint 47 documented 8 divergences between the Rust web4-trust-core
implementation and the spec/Python SDK. Of those 8, three correspond directly
to Sprint 52 xfails. In each case the Python SDK matches the spec; the Rust
SDK and the conformance vectors (authored alongside Rust) diverge.

| Sprint 52 xfail | Sprint 47 audit finding | Severity in Sprint 47 |
|-----------------|-------------------------|-----------------------|
| #1 t3-002 weighted vs unweighted | Finding #2 (T3 composite: unweighted) | HIGH |
| #2 t3-004 update direction | Finding #4 (T3 update: wrong formula) | HIGH |
| #3 t3-006 talent decay | Finding #1 (Talent decay applied — spec violation) | CRITICAL |

These three xfails do not surface new information. They are conformance-runner
restatements of the Sprint 47 findings. The relevant fact is **which side aligns
to the canonical spec**: the Python SDK matches the spec's normative invariants
(weighted composites, quality-based update, no Talent decay per Sprint 44).
The vectors were authored against the Rust implementation's behavior, which
diverges from spec. Closing these xfails by changing the Python SDK would
move the SDK away from canonical alignment.

### New surface gaps (5 of 8): not in any prior audit

The remaining five xfails surface gaps that neither Sprint 47 nor Sprint 49
caught. This is the more informative half of the consolidation.

| Sprint 52 xfail | Why this isn't in Sprint 47/49 audits |
|-----------------|---------------------------------------|
| #4 r6-val-004 constraint enforcement | Sprint 49 #10 covered Constraint **shape** (closed by Sprint 51 PR #187). Constraint **enforcement at validate-time** was not examined — the audit treated Constraint as a data type, not an enforcement point. |
| #5 r7-rep-001 V3 valuation in reputation | Neither audit examined which V3 dimensions are updated by `compute_reputation()`. The SDK splits V3 into a behavioral subset (veracity, validity) and an economic dimension (valuation, updated via ATP settlement). The vector treats all three as behavioral. This is a **conceptual split** the audits missed. |
| #6 role-004 assigner authorization | Sprint 49 mapped Society/Role data types; it did not model an "is_allowed_to_assign_roles(role) → bool" predicate. The vector introduces one. **Not flagged anywhere in the audits.** |
| #7 fed-001 join/secede vs incorporate_child | Sprint 49 #5 noted "composite architecture difference" but did not enumerate the federation API. The conformance vector concretizes the difference: child-initiated `join()`/`secede()` vs parent-initiated `incorporate_child()`. |
| #8 sub-001 sub-dimension rollup | The ontology defines `web4:subDimensionOf` (T3/V3 ontology TTL). Neither audit examined whether the runtime implements rollup. The vector exposes this as an ontology-vs-runtime gap. |

**Headline finding**: 5 of 8 xfails (62.5%) are new surface gaps not surfaced
by either code-reading audit. The conformance-vector instrument finds gaps that
code-reading audits don't, because vectors encode **behavioral expectations**
while audits compare **structural shapes**. The two instruments are complementary;
neither subsumes the other.

## Actionability tier classification

Three tiers, with one note: no Sprint 52 xfail is purely autonomous-actionable.
Each either depends on external toolchain (Rust web4-trust-core) or on operator
architectural decisions. This means a Sprint 53 framed as "fix the xfails"
would block on inputs the current track cannot provide.

### Tier A — CROSS-LANGUAGE-EXTERNAL-TOOLCHAIN (3 xfails)

Sprint 47's audit recommendations live in the Rust web4-trust-core repo, not
this one. Until that toolchain is exercised, these xfails persist by design.

- **#1 t3-002 weighted composite** — Fix Rust to use weighted average (Sprint 47 Recommendation 2).
- **#2 t3-004 update formula** — Fix Rust to adopt `0.02 * (quality - 0.5)` (Sprint 47 Recommendation 3).
- **#3 t3-006 talent decay** — Fix Rust to honor Talent no-decay invariant (Sprint 47 Recommendation 1; also vector author should regenerate the vector to match the invariant).

Resolution cost from this track: zero (cannot resolve). Resolution cost from
Rust track: small (line-level edits per Sprint 47 audit), but requires the
Rust toolchain. The xfails are the right outcome here — they make the cross-language
divergence executable on every Python test run.

### Tier B — DESIGN-QUESTION-NEEDS-OPERATOR (4 xfails)

These are not "implement the missing thing." They are "decide which side is
right, then implement." The decision is architectural and lives above the
autonomous track.

- **#4 r6-val-004 constraint enforcement** — Decision: should `R7Action.validate()` enforce Constraint satisfaction, or is enforcement strictly PolicyGate's responsibility?
  - The current SDK splits responsibility: `validate()` checks structural correctness, PolicyGate checks policy/constraint satisfaction. This is a defensible architecture.
  - If the decision is "validate() enforces constraints," the implementation is **small** (one method on R7Action that iterates `self.constraints` and emits errors).
  - If the decision is "PolicyGate-only," the conformance vector itself should be retargeted (or the xfail rephrased as a documented design split, not a gap).

- **#5 r7-rep-001 V3 valuation in reputation** — Decision: is V3.valuation a behavioral or an economic dimension?
  - The SDK answer: economic (updated via ATP settlement, not via R7Action quality).
  - The vector answer: behavioral (`compute_reputation()` should produce a valuation delta).
  - One answer is wrong. This is a single decision with implementation consequences either way.

- **#6 role-004 assigner authorization** — Decision: is "who can assign which role" data (lives in role.py) or governance (lives in PolicyGate/SocietyState)?
  - The conformance vector implies a data-layer predicate: `is_allowed_to_assign_roles(role) → bool`, returning True for Sovereign/Administrator and False for others.
  - The SDK comment in the xfail block places this in the governance layer, not in `web4/role.py`.
  - Autonomous implementation cost in role.py: **small** (5 lines + tests). But this would lock in the data-layer answer to the architectural question.

- **#7 fed-001 join/secede vs incorporate_child** — Decision: is federation membership child-initiated or parent-initiated?
  - The SDK chose parent-initiated (`incorporate_child(parent_state, child_state, timestamp)`).
  - The vector chose child-initiated (`join(parent) → is_constituent=True`, `secede() → is_constituent=False`).
  - The two patterns express different governance semantics. Web4's sovereignty stance (sub-society sovereignty is intrinsic, not granted) leans **child-initiated** — which makes the SDK's parent-initiated API the candidate to revisit.

Resolution cost from this track once the decision lands: small to medium per item.
Without the decision, autonomous work risks locking in the wrong side.

### Tier C — NEEDS-SPEC-SCOPING (1 xfail)

- **#8 sub-001 T3 sub-dimension rollup** — Decision: is sub-dimensional T3 a runtime construct or an ontology-metadata construct?
  - The ontology TTL defines `web4:subDimensionOf` (e.g., `talent:python web4:subDimensionOf talent`).
  - The runtime T3 dataclass has three scalar fields (talent, training, temperament); it does not accept sub-dimensional attestations and project them via the ontology.
  - If sub-dimensions are purely metadata for human consumption: the vector itself is over-reaching, and the xfail should be reframed as a documented non-gap (closed via vector retraction or test removal).
  - If sub-dimensions are runtime constructs: this is a substantial T3 redesign (~medium-large autonomous-session cost — new data structure, ingestion path, rollup math, persistence implications). It also needs to define how sub-dimension attestations compose with the existing scalar fields.

This is the only xfail where the choice isn't "implement vs not" but "is the
feature scoped at runtime at all" — which is a spec-level question.

## Counter-finding from Sprint 52 (worth preserving)

Of the **27 non-xfail conformance assertions in tensor + ATP + R6 + Society
suites that the Python SDK passes**, the **11 ATP vectors all pass exactly**
(no near-misses, no behavioral-but-not-numeric equivalence). The Sprint 49 audit's
documentary claim "ATP is the best-aligned cross-language pair (identical core
semantics)" is now operationally confirmed: every conformance vector the operator
could author against Rust/spec matches what the Python SDK produces. This is a
stronger statement than the audit made — it's the audit's claim hardened into
a continuously-executed check.

This counter-finding belongs alongside the xfail catalogue because it answers
the natural follow-up: "OK, but does anything actually work cross-language?"
Yes. ATP works fully. T3/V3 works behaviorally (level classifications agree;
numeric composites diverge). R7 works for happy-path reputation. Society/Role
bootstrap and rotation work. The xfails are the edge surface, not the whole surface.

## Sprint 53+ candidate buckets

### Autonomous-pickable bucket (no operator unblocking needed)

Most natural candidates are not "fix xfails" but adjacent work that benefits
from Sprint 52's now-executable conformance baseline:

- **C1 — MCP-as-inter-society-protocol audit** (memory candidate D1): compare
  the Python SDK's MCP/protocol module against `mcp-protocol.md` §7.3–7.6
  (added in v0.1.3 amendment) to identify missing implementation surface for
  inter-society R7 transactions, LCT envelopes, witnessing, reputation
  propagation, and failure modes. Pure audit; produces one memo. Independent
  of any operator decision.

- **C2 — mcp-protocol.md internal-consistency audit** (memory candidate D4):
  read mcp-protocol.md end-to-end and surface internal inconsistencies between
  §1.1 framing, §7.3–7.6 normative content, and §7.7 WIP. Pure documentation
  audit. Produces one memo.

- **C3 — §7.7 promotion tracking stub** (memory candidate D2): write a small
  memo capturing what would need to be true to promote §7.7 (referent-grounded
  exchange rate negotiation) from v0.1.0-draft to v0.1.0-normative. Two-page
  artifact. Independent of any other work.

- **C4 — Pre-merge conformance-vector freshness check process**: define a
  lightweight process (probably a markdown doc + a CI hook design memo) that
  flags conformance vectors that depend on data structures the SDK has recently
  changed shape on. This was the open question from session 180024: vectors
  were authored against R6 Constraint shape and Constraint shape changed in
  PR #187 the same day vectors landed. The process avoids that re-emerging.

### Operator-blocked bucket (cannot pick autonomously)

- **B1 — Decide #4 r6-val-004**: validate() enforces constraints, or
  PolicyGate-only? (Decides whether to add `R7Action.check_constraints()`.)

- **B2 — Decide #5 r7-rep-001**: V3.valuation behavioral or economic?
  (Decides reputation delta API shape.)

- **B3 — Decide #6 role-004**: assigner authorization data or governance layer?
  (Decides whether `role.py` gets the predicate or `PolicyGate` does.)

- **B4 — Decide #7 fed-001**: federation child-initiated or parent-initiated?
  (Affects API design across society + federation modules.)

- **B5 — Decide #8 sub-001**: sub-dimensional T3 runtime or metadata-only?
  (Spec-level scoping question; precedes any implementation.)

- **B6 — P4 carryover**: MetabolicState 5-state vs 7-state reconciliation
  (Sprint 49 audit; operator-blocked since Sprint 49 surfaced it).

- **B7 — P7 carryover**: SocietyState role-integration architecture (Sprint
  49 audit; operator-blocked since Sprint 49 surfaced it).

### External-track-blocked bucket (needs Rust toolchain or vector regeneration)

- **R1, R2, R3** — Sprint 47 recommendations #1, #2, #4 (Talent no-decay,
  weighted composites, update formula) — fix Rust web4-trust-core to match
  spec. Cannot be done from web4 repo. Vector regeneration follows.

## Closing observation

The Sprint 47 audit identified 8 cross-language T3/V3 divergences; we now see
that 3 of them surface as Sprint 52 conformance xfails. The Sprint 49 audit
identified 14 cross-language Society/Role/ATP/R6 items; only 1 of them (Constraint
shape, P6 / Sprint 51) directly mapped to a Sprint 52 vector, and **none** of
the new Sprint 52 surface gaps were in Sprint 49's queue. This asymmetry says
something about the audit methodology: **code-reading audits and behavioral
conformance audits are not redundant**. Doing one well does not predict what
the other will find.

A reasonable governance posture going forward: run both periodically, and treat
disagreements between them (vectors find a gap an audit missed, or an audit
finds a gap no vector exercises) as signal about which surfaces are
under-instrumented.
