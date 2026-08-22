#!/usr/bin/env python3
"""Convergence gate for PRD_ROLE_SCOPE_BRIDGE §2 (`concepts_generation`).

§2 of `hub/docs/PRD_ROLE_SCOPE_BRIDGE.md` is a NON-NORMATIVE summary whose
normative home is §2 of the twin, `dp-web4/hestia:docs/PRD_ROLE_SCOPE_BRIDGE.md`.
The two sections legitimately say different amounts, so a diff cannot tell an
intended asymmetry from a real divergence — the PRD replaced the diff rule with
an integer comparison of an anchored `concepts_generation:` marker on each side.

That rule was documented and nothing executed it (HUB/Legion, 2026-08-21). This
is the executable half. It implements the PRD's table verbatim:

    equal                     => CURRENT       exit 0
    home greater than here    => STALE         exit 1
    either missing/unreadable => UNDETERMINED  exit 2   (never a pass)

Two properties of the shape are deliberate and are asserted by --self-test:

  * The extraction is ANCHORED on `: *[0-9]+`. An unanchored `grep -m1
    concepts_generation` matches the earliest PROSE mention of the token — a
    line carrying no number — and so cannot extract the value it claims to
    compare. That was a real defect in the first published version of the check
    (GPT review, 2026-08-21), and arm 5 below fails if it comes back.

  * STALE and UNDETERMINED get DISTINCT exit codes even though CI collapses both
    to "failed". A check whose arms return the same value cannot discriminate,
    which is exactly how the rule this one replaced failed. The self-test asserts
    the arms are pairwise distinct rather than merely non-green.

FOURTH CASE, NOT IN THE PRD'S TABLE: `home < here` — the hub citing a generation
the home never issued (a citation bumped without the amendment, or a home that
regressed). The PRD enumerates three rows and this is not one of them. It is
treated as UNDETERMINED (fail-closed, per the fleet's deny-and-warn default) and
printed as such. It is a gap in the document, not a decision this tool is making
quietly; routing it back to §2 is tracked in the PR that added this file.

Stdlib only — no pip step, nothing to version-drift. The home is fetched over
raw HTTPS because `dp-web4/hestia` is public: no clone, no submodule, no token.
"""

import argparse
import re
import sys
import time
import urllib.error
import urllib.request

# Anchored: names the VALUE, not the topic. See module docstring.
MARKER = re.compile(r"concepts_generation:\s*(\d+)")

DEFAULT_HERE = "hub/docs/PRD_ROLE_SCOPE_BRIDGE.md"
DEFAULT_HOME_URL = (
    "https://raw.githubusercontent.com/dp-web4/hestia/main/docs/PRD_ROLE_SCOPE_BRIDGE.md"
)

CURRENT, STALE, UNDETERMINED = 0, 1, 2
NAME = {CURRENT: "CURRENT", STALE: "STALE", UNDETERMINED: "UNDETERMINED"}


def extract(text):
    """First anchored marker value, or None. Mirrors the PRD's documented grep."""
    if text is None:
        return None
    m = MARKER.search(text)
    return int(m.group(1)) if m else None


def verdict(here, home):
    if here is None or home is None:
        return UNDETERMINED
    if home == here:
        return CURRENT
    if home > here:
        return STALE
    return UNDETERMINED  # home < here — see FOURTH CASE in the module docstring


def read_local(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        print(f"  could not read {path}: {exc}", file=sys.stderr)
        return None


def fetch(url, attempts=3):
    """Fetch the home. Transient failure retries; exhausted failure is UNDETERMINED,
    never a silent pass — the PRD declares the missing-home arm fail-closed."""
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "web4-concepts-generation-gate"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            last = exc
            if i + 1 < attempts:
                time.sleep(2 * (i + 1))
    print(f"  could not fetch {url}: {last}", file=sys.stderr)
    return None


def self_test():
    """Induce every arm against fixtures. A guard that has never been run against
    the condition it guards is a claim, not a check."""
    equal = "## 2. Concepts (`concepts_generation: 1`)"
    bumped = "## 2. Concepts (`concepts_generation: 2`)"
    stripped = "## 2. Concepts — the marker was renamed away"
    # Arm 5: the first mention is bare prose with no value; the real marker follows.
    prose_first = "cited by `concepts_generation` in §2\n\n## 2. (`concepts_generation: 3`)"

    arms = [
        ("1 equal            ", extract(equal), extract(equal), CURRENT),
        ("2 home bumped      ", extract(equal), extract(bumped), STALE),
        ("3 home marker gone ", extract(equal), extract(stripped), UNDETERMINED),
        ("4 home < here      ", extract(bumped), extract(equal), UNDETERMINED),
    ]

    ok = True
    for label, here, home, want in arms:
        got = verdict(here, home)
        flag = "ok " if got == want else "FAIL"
        if got != want:
            ok = False
        print(f"  {flag} arm {label} here={here} home={home} -> {NAME[got]} (want {NAME[want]})")

    got5 = extract(prose_first)
    ok5 = got5 == 3
    ok = ok and ok5
    print(f"  {'ok ' if ok5 else 'FAIL'} arm 5 anchoring       prose-first fixture -> {got5} (want 3)")

    # The property the replaced rule lacked: the arms must not all agree.
    distinct = {verdict(*a[1:3]) for a in arms[:3]}
    ok_d = len(distinct) == 3
    ok = ok and ok_d
    print(f"  {'ok ' if ok_d else 'FAIL'} arms 1-3 pairwise distinct: {sorted(NAME[v] for v in distinct)}")

    print("  SELF-TEST " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--here", default=DEFAULT_HERE, help="hub-side summary (default: %(default)s)")
    ap.add_argument("--home", default=None, help="local path to the normative home; overrides --home-url")
    ap.add_argument("--home-url", default=DEFAULT_HOME_URL, help="raw URL of the normative home")
    ap.add_argument("--self-test", action="store_true", help="run every arm against fixtures and exit")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    here_text = read_local(args.here)
    if args.home:
        home_text = read_local(args.home)
        home_src = args.home
    else:
        home_text = fetch(args.home_url)
        home_src = args.home_url

    here = extract(here_text)
    home = extract(home_text)
    v = verdict(here, home)

    print(f"  here ({args.here}) -> {here}")
    print(f"  home ({home_src}) -> {home}")
    print(f"  VERDICT: {NAME[v]}")

    if v == STALE:
        print(
            "  The hub's §2 summary predates an amendment to its normative home.\n"
            "  Re-point it: read the home's §2, update hub/docs/PRD_ROLE_SCOPE_BRIDGE.md §2,\n"
            f"  and set its citation to concepts_generation: {home}."
        )
    elif v == UNDETERMINED:
        if here is not None and home is not None:
            print(
                "  home < here: the hub cites a generation the home never issued. Not a row in\n"
                "  the PRD's table; fail-closed. Resolve on the home side before relying on §2."
            )
        else:
            print(
                "  A marker is missing or unreadable. UNDETERMINED is NOT less-than, and NOT a\n"
                "  pass — a renamed/moved home must not read as 'not stale'. Resolve, then re-run."
            )
    return v


if __name__ == "__main__":
    sys.exit(main())
