# Hub Law Interop Fixtures (in-repo copy)

Canonical test files for the hub-side law parser (V2-8) and the
`web4-law-check` validator CLI (U3). Both sides assert against the same
fixture content so divergence is caught early.

## Provenance — read this before editing

**These are a copy.** The fleet-canonical originals live in the private
`dp-web4/shared-context` repo at `interop-fixtures/hub-law/`, where Legion
seeded them. That copy remains the source of truth for the fleet.

They are duplicated here because `hub-lib/src/law.rs` loads them with
`include_str!`, which is a **compile-time** read. Pointing it at the sibling
checkout (`../../../../shared-context/...`, one directory above the repo root)
made this **public** repo unable to compile its own tests without a **private**
one:

- `cargo test (hub)` in `.github/workflows/ci.yml` was red from the day the
  workflow was armed — the runner checks out `dp-web4/web4` and nothing else.
- Any clone of the public repo hit the same four
  `couldn't read ... No such file or directory` errors.

Checking the private repo out inside CI would need a secret in a public repo,
and would still leave every external clone broken. So the compile-time source
of truth moved in-repo, and stayed public.

## Drift protection

`interop_fixtures_match_shared_context_canonical` in `hub-lib/src/law.rs`
asserts these files are byte-identical to the `shared-context` originals. It is
a **runtime** read, so it no-ops where the sibling is absent (CI, outside
clones) and fails loudly where it is present (every fleet machine). The drift
guarantee the shared fixture existed to provide is preserved.

## Editing

Edit the canonical copy in `shared-context/interop-fixtures/hub-law/` first,
then copy the file here in the same change. The drift test fails if you do only
one of the two.

## Files

| File | Valid? | Tests |
|------|--------|-------|
| `minimal.yaml` | Yes | Smallest valid law file (1 norm) |
| `full-featured.yaml` | Yes | Exercises all predicate types |
| `invalid-missing-norm-id.yaml` | No | Norm missing required `id` field |
| `invalid-bad-operator.yaml` | No | Unsupported operator `LIKE` |

## Schema reference

`web4-standard/core-spec/hub-law-schema.md` — YAML surface spec, validation
rules (§2), and YAML→RDF compilation mapping (§3).

`web4-standard/ontology/hub-law.ttl` — RDF canonical ontology.
