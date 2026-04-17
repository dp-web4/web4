# web4 SDK Examples

Runnable, offline examples of the current `web4` Python package (v0.25.0).

## quickstart.py

Single-file tour of the three behavioral composition points in the SDK:

| Step | API | Demonstrates |
|------|-----|--------------|
| 1 | `web4.generate(type)` + `web4.from_jsonld(doc)` | JSON-LD dispatcher roundtrip for `LinkedContextToken` (one of 23 registered types) |
| 2 | `web4.evaluate_trust_query(query, profile, atp)` | Direct trust resolution — ATP stake lock, role lookup, disclosure-level filtering |
| 3 | `web4.process_action_outcome(action, engine, profile, account)` | Action consequence pipeline — R7Action → reputation → ATP settlement |

Run:

```bash
pip install -e web4-standard/implementation/sdk/
python web4-standard/implementation/sdk/examples/quickstart.py
```

No network or external services required.

## Passing / style

Quickstart is held to the same quality gates as the rest of the SDK:

```bash
python -m ruff check examples/
python -m ruff format --check examples/
python -m mypy --strict examples/quickstart.py
```

## Adding new examples

Guidelines:

- Compose existing public API from the `web4` package; do not reimplement concepts.
- Offline by default. Any example that needs network must say so in its docstring.
- No emoji, no ANSI codes in output.
- Pass `ruff check`, `ruff format --check`, and `mypy --strict`.
- No tests for examples — examples are themselves the smoke test.
