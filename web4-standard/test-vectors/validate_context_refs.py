#!/usr/bin/env python3
"""
Context-reference integrity check for cross-language test vectors.

Every `@context` URI of the form `https://web4.io/contexts/<name>.jsonld`
carried by any JSON document under `test-vectors/` must have a backing
file at `schemas/contexts/<name>.jsonld` — the convention the standard's
own SDK test asserts (`test_t3v3_jsonld.py` calls `os.path.exists()` on
exactly those paths). The schema-validation runner
(`schema-validation/validate_schema_vectors.py`) cannot see this class of
error: the schemas type `@context` as an array of URI strings and never
dereference it, so a vector can pass schema validation forever while
citing a context that does not exist (audit C310-N3, 2026-08-02: 36 of 38
published t3v3 vectors cited `contexts/t3v3.jsonld`, retired by the
2026-03-24 namespace reconciliation and never re-created).

Stdlib only — no jsonschema, no network. URIs are checked against the
tree, never fetched.

Usage:
    python validate_context_refs.py              # Check all of test-vectors/
    python validate_context_refs.py --verbose    # List every reference by file

Exit code 0 = every referenced context exists OR is listed in
KNOWN_MISSING below; 1 = a reference points at a context with no backing
file that nobody has accounted for.

KNOWN_MISSING is the carrying mechanism, not a pass: a name lands there
only with a citation to the audit that found it and the track the fix is
routed to. Removing a name requires the backing file to exist — the
check goes red if it doesn't, so the list can only shrink honestly.
"""

import json
import re
import sys
from pathlib import Path

VECTORS_DIR = Path(__file__).parent
CONTEXTS_DIR = VECTORS_DIR.parent / "schemas" / "contexts"
VERBOSE = "--verbose" in sys.argv

CONTEXT_URI = re.compile(r"^https://web4\.io/contexts/([A-Za-z0-9_-]+\.jsonld)$")

# Referenced contexts with no backing file, each routed to a fix track.
# Entry format: name -> (audit citation, disposition). A name here that
# GAINS a backing file is reported as resolved; a referenced name NOT
# here and NOT on disk fails the run.
KNOWN_MISSING = {
    "t3v3.jsonld": (
        "C310-N3 (docs/audits/C310-t3-v3-tensors-8th-delta-2026-08-02.md)",
        "routed to the SDK / build track: add the context file, or repoint "
        "the vectors at t3.jsonld / v3.jsonld — the 2026-03-24 "
        "reconciliation replaced the shared t3v3 context",
    ),
}


def iter_context_uris(node):
    """Yield every string carried by a `@context` key, at any depth."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "@context":
                if isinstance(value, str):
                    yield value
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            yield item
            else:
                yield from iter_context_uris(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_context_uris(item)


def main():
    # name -> {file: ref_count}
    references = {}
    ref_total = 0
    unparseable = []

    for path in sorted(VECTORS_DIR.rglob("*.json")):
        try:
            doc = json.loads(path.read_text())
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            unparseable.append((path, exc))
            continue
        for uri in iter_context_uris(doc):
            match = CONTEXT_URI.match(uri)
            if not match:
                continue
            name = match.group(1)
            rel = path.relative_to(VECTORS_DIR)
            references.setdefault(name, {}).setdefault(rel, 0)
            references[name][rel] += 1
            ref_total += 1

    print(f"Scanned {VECTORS_DIR.name}/**: {ref_total} web4.io context references, "
          f"{len(references)} distinct context names\n")

    failures = []
    resolved = []
    for name in sorted(references):
        files = references[name]
        count = sum(files.values())
        backing = CONTEXTS_DIR / name
        if backing.exists():
            status = f"OK       ({count} refs, {len(files)} files)"
            if name in KNOWN_MISSING:
                resolved.append(name)
                status += " — was KNOWN_MISSING, now backed: remove the entry"
        elif name in KNOWN_MISSING:
            citation, disposition = KNOWN_MISSING[name]
            status = (f"KNOWN    ({count} refs, {len(files)} files) — missing, carried: "
                      f"{citation}; {disposition}")
        else:
            status = f"MISSING  ({count} refs, {len(files)} files) — NO backing file, NOT carried"
            failures.append(name)
        print(f"  {name:35s} {status}")
        if VERBOSE:
            for rel, n in sorted(files.items()):
                print(f"      {rel} ({n})")

    if unparseable:
        print(f"\nWARNING: {len(unparseable)} file(s) did not parse as JSON (skipped):")
        for path, exc in unparseable:
            print(f"  {path.relative_to(VECTORS_DIR)}: {exc}")

    for name in resolved:
        print(f"\nNOTE: '{name}' now has a backing file — delete it from KNOWN_MISSING.")

    # Context names on disk that nothing references are not a defect —
    # this check guards references, not coverage.

    print(f"\n{'=' * 50}")
    if failures:
        print(f"{len(failures)} CONTEXT(S) MISSING AND UNCARRIED: {', '.join(failures)}")
    else:
        known = [n for n in references if n in KNOWN_MISSING
                 and not (CONTEXTS_DIR / n).exists()]
        msg = f"ALL REFERENCED CONTEXTS BACKED"
        if known:
            msg += f" (except {len(known)} carried: {', '.join(sorted(known))})"
        print(msg)
    print(f"{'=' * 50}\n")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
