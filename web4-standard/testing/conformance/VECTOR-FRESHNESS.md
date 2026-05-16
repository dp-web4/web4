# Conformance Vector Freshness

**Status**: process doc + CI-hook design memo (no CI implementation here)
**Applies to**: `web4-standard/testing/conformance/*.json`
**Origin**: open question from autonomous session 180024, formalized as
Sprint 53+ candidate **C4** in
`docs/audits/sprint-52-conformance-gap-consolidation-2026-05-15.md`.

---

## 1. The Staleness Hazard

Conformance vectors are authored against a *snapshot* of an SDK data
structure's shape. When that structure changes shape later — a new field, a
renamed field, a changed default — a vector written before the change keeps
passing while silently testing **outdated semantics**. The failure is not a
red test; it is a green test that no longer means what it claims.

### Why the adapter masks it

Each language binding maps vector JSON onto its own dataclasses through an
adapter. The Python conformance runner does this in
`web4-standard/implementation/sdk/tests/test_conformance.py`,
`TestR6R7Conformance._build_action`:

```python
constraints.append(
    Constraint(
        constraint_type=c["constraint_type"],
        threshold=c["threshold"],
        hard=c.get("hard", True),   # <-- absorbs the shape change
    )
)
```

`hard` was added to `Constraint` in PR #187. The conformance vectors in
`r6-r7-actions.json` were authored *before* `hard` existed and landed the
same day PR #187 changed the shape. Because the adapter does
`c.get("hard", True)`, every pre-`hard` vector is silently coerced to
`hard=True`. A vector that was meant to exercise a soft constraint (or that
*should* be updated to cover the new field) instead tests the default and
stays green. The adapter's defensive `.get(..., default)` — good practice for
forward-compatibility — is exactly what hides the drift.

This is the general pattern, not a one-off:

> **Any adapter line of the form `field=data.get("field", default)` converts a
> vector/shape mismatch from a loud failure into a silent default.**

The hazard is structural and will recur every time an SDK dataclass consumed
by a conformance adapter gains, renames, or re-defaults a field.

---

## 2. Manual Pre-Merge Checklist

Run this when a PR **either** changes a conformance vector file **or** changes
an SDK dataclass that a conformance adapter constructs (today: `R7Action`,
`Rules`, `Role`, `Constraint`, and the T3/V3/ATP/Society types exercised by
the four suites).

- [ ] **Identify touched shapes.** List every SDK dataclass whose field set,
      field names, or field defaults changed in this PR.
- [ ] **Trace each to its adapter.** For each touched dataclass, find where
      `test_conformance.py` constructs it. Note every `.get(key, default)`
      that maps a vector key onto a changed field.
- [ ] **Decide intent per vector suite.** For each affected suite, the change
      is one of:
      - *cosmetic* (no semantic effect on existing vectors) — record why;
      - *additive* (new field; existing vectors legitimately fall back to the
        default) — add at least one new vector exercising the non-default
        value, so the new field is actually covered;
      - *semantic* (existing vectors now test the wrong thing) — update the
        affected vectors and bump the suite `version`.
- [ ] **Update provenance** (see §4) in every suite file whose shape source
      moved.
- [ ] **Confirm coverage didn't silently shrink.** A passing suite after a
      shape change with *no vector edits and no new vectors* is a yellow flag,
      not a green light — state explicitly in the PR why no vector needed to
      change.

The check is a reviewer responsibility, not an author-only one: the masking
makes author self-review unreliable by construction.

---

## 3. CI-Hook Design (design only — not implemented here)

Goal: turn the silent default into a loud signal **without** making adapters
brittle (we want to keep the forward-compatible `.get(..., default)`).

**Detection heuristic — field-set diff.** For each conformance adapter
construction site, the SDK exposes a *declared* field set (the dataclass's
fields). For each vector, the *provided* field set is its JSON keys at the
matching path. The hook compares the two:

| Condition | Signal |
|-----------|--------|
| Vector provides a key the dataclass no longer declares | **FAIL** — stale vector references a removed/renamed field |
| Dataclass declares a non-defaulted field absent from all vectors in the suite | **FAIL** — vectors cannot exercise a required field |
| Dataclass declares a *defaulted* field absent from every vector in the suite | **WARN** — new field is uncovered (likely "additive" case from §2) |
| Field sets reconcile | pass |

**Where the declared field set comes from.** `dataclasses.fields(Constraint)`
(and peers) is authoritative and zero-maintenance — the heuristic reads the
live SDK, so it cannot itself go stale. The adapter→dataclass mapping is the
only hand-maintained input; keep it as a small explicit table in the hook so
adding a suite is a one-line change.

**Trigger.** Run on PRs whose diff touches either
`web4-standard/testing/conformance/**` or any SDK module that a mapped adapter
imports. Non-blocking WARN, blocking FAIL.

**Explicitly out of scope for this memo**: the CI YAML, the script itself, and
any language binding other than the Python runner. This section specifies the
heuristic and its signals; implementation is a separate, scoped task.

---

## 4. Vector Provenance Convention

Today a suite file carries `$schema` and a suite `version`, but nothing
records *which SDK shape the vectors were authored against*. Without that, a
reviewer cannot tell whether a green suite predates a shape change.

Add a top-level `provenance` object to each suite file:

```json
{
  "$schema": "https://web4.io/schemas/test-vectors/v1.json",
  "suite": "R6/R7 Action Framework",
  "version": "0.1.0",
  "provenance": {
    "authored_against_sdk_version": "0.27.0",
    "shape_source_commit": "abab1e79",
    "shapes": ["R7Action", "Rules", "Role", "Constraint"],
    "last_freshness_review": "2026-05-15"
  }
}
```

- `authored_against_sdk_version` — SDK version whose dataclass shapes the
  expected outputs assume.
- `shape_source_commit` — short hash of the commit that last defined those
  shapes (the anchor a reviewer diffs against).
- `shapes` — the SDK dataclasses this suite's adapter constructs; the
  field-set hook (§3) reads exactly these.
- `last_freshness_review` — date the §2 checklist was last run green.

`provenance` is **advisory metadata**, not part of the conformance contract:
language bindings MUST ignore unknown top-level keys (the existing
forward-compat rule), so adding it does not break any current consumer and
requires no schema-version bump. Populating it across the four existing suites
is a follow-up vector-edit task, intentionally out of scope here (this session
does not modify existing JSON vectors).

---

## 5. Relationship to the Existing Suite

This process complements `README.md` §"Contributing Vectors": that section
says *how to write a well-formed vector*; this doc says *how to keep an
already-written vector honest when the SDK moves underneath it*. The two
together close the author→reviewer→drift loop that session 180024 surfaced.
