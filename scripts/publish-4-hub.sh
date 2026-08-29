#!/usr/bin/env bash
# publish-4-hub.sh — publish the standalone 4-hub mirror from this monorepo.
#
# 4-hub (github.com/dp-web4/4-hub) is a READ-ONLY mirror containing hub/ and
# web4-core/ with monorepo layout preserved, so hub's relative path dependency
# (hub/Cargo.toml: web4-core = { path = "../web4-core" }) resolves and a fresh
# clone builds with plain `cargo build`. Development happens HERE, in web4 —
# run this script after hub-relevant changes land to refresh the mirror.
#
# Mechanism: fresh clone -> git filter-repo (history rewritten to the kept
# paths) -> add a mirror-only root README -> force-push. The mirror is fully
# derived; every run rebuilds it deterministically. Requires git-filter-repo
# (pip install git-filter-repo) and push access to dp-web4/4-hub.
set -euo pipefail

MONOREPO="$(cd "$(dirname "$0")/.." && pwd)"
# WHERE to publish. Overridable so a test run can aim at a throwaway bare repo.
MIRROR_REMOTE="${MIRROR_REMOTE:-git@github.com:dp-web4/4-hub.git}"

# WHAT to publish. HARD-PINNED, deliberately not overridable — see the pin below.
#
# This script's failure mode is not a bad merge, it is a SILENT publication: the
# mirror is fully derived and force-pushed, so there is no conflict for anyone to
# notice and a wrong publish is visible only in this script's own output. An env
# knob on the source ref is therefore an env knob on what becomes public, sitting
# on the one path that looks like the safe publication path. A test bed does not
# need it: redirect MIRROR_REMOTE at a throwaway repo (that is how this fix's own
# evidence was produced) and edit this line locally if you must publish something
# else. Announce an ignored override rather than silently publishing main.
if [ -n "${PUBLISH_REF:-}" ] && [ "$PUBLISH_REF" != "refs/remotes/origin/main" ]; then
  echo "[4-hub] IGNORING PUBLISH_REF=$PUBLISH_REF from the environment:" >&2
  echo "[4-hub]   the publish source is hard-pinned to refs/remotes/origin/main." >&2
fi
PUBLISH_REF="refs/remotes/origin/main"
readonly PUBLISH_REF

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Refresh the ref we are about to pin to. Nothing else in this script advances it:
# the `git fetch "$MONOREPO" …` below fetches FROM the monorepo INTO the clone, which
# does not move the monorepo's own origin/main. Unrefreshed, the pin is only as fresh
# as whenever someone last happened to fetch in a shared, human-and-agent-operated
# checkout — trading "publishes unmerged" for "publishes stale", the same trade the
# --branch main note below rejects.
#
# Branch on the REFRESH's rc, never on the shape of the answer: `rev-parse` resolves a
# stale remote-tracking ref just fine after a failed fetch, so a value check cannot
# tell fresh from stale. And refuse rather than continue — a force-push to a public
# mirror is the irreversible direction, so doubt costs less than a wrong publication.
echo "[4-hub] refreshing $PUBLISH_REF in $MONOREPO ..."
if ! git -C "$MONOREPO" fetch -q origin main; then
  echo "[4-hub] REFUSING to publish: could not refresh $PUBLISH_REF (fetch failed)." >&2
  echo "[4-hub] The ref would still resolve, to a stale commit. Fix the network/remote" >&2
  echo "[4-hub] and re-run; nothing has been pushed." >&2
  exit 1
fi

echo "[4-hub] fresh clone of monorepo..."
git clone --no-local -q "$MONOREPO" "$WORK/mirror"
cd "$WORK/mirror"

# Pin the publish source to a MERGED ref.
#
# A local clone checks out whatever the SOURCE checkout's HEAD happens to be, and
# the last line of this script is `push --force ... HEAD:main`. The web4 checkout on
# HUB is shared with an interactive session and is routinely parked on a feature
# branch, so unpinned this publishes UNMERGED work to a PUBLIC repo. Measured
# 2026-08-08: HEAD was `hub/quickstart-and-track-h-docs`, 3 commits ahead of
# origin/main, and a run would have force-pushed all three.
#
# `git clone --branch main` is NOT the fix. In a local clone the source's LOCAL
# branches become the clone's branches, and that local `main` can trail the real
# one (measured the same day: local 68c2ba9 vs origin/main f7707a9, two behind).
# That trades publishing unmerged code for publishing stale code. Fetch the
# source's remote-tracking ref instead — that is the one the merge queue advances.
git fetch -q "$MONOREPO" "$PUBLISH_REF:refs/heads/__publish"
git checkout -q __publish
echo "[4-hub] publishing $PUBLISH_REF = $(git rev-parse --short HEAD)"

# The kept set is hub/ plus the transitive closure of its monorepo path
# dependencies. Recompute when deps change:
#   cd hub && cargo metadata --format-version 1 | <extract manifest dirs under the monorepo root>
echo "[4-hub] filtering history to hub/ + its web4 path dependencies..."
# --force because the pin fetch above leaves the clone looking non-pristine to
# filter-repo's freshness check. Safe here and only here: $WORK is a mktemp clone
# this script created and its EXIT trap deletes.
git filter-repo --force --quiet \
  --path hub \
  --path web4-core \
  --path web4-policy \
  --path web4-trust-core \
  --path LICENSE \
  --path PATENTS.md

echo "[4-hub] adding mirror root README..."
cat > README.md << 'EOF'
# 4-hub — Web4 Community Hub (standalone mirror)

A single-binary Rust daemon (~6 MB) that turns a community into a sovereign
Web4 society: 7 roles, a signed machine-readable founding law, an append-only
witnessed ledger, sealed member<->hub channels, and a multi-surface API
(MCP `/tools/*`, REST `/v1`, admin web GUI).

**Start here: [`hub/README.md`](hub/README.md).**

## Layout

| Path | What it is |
|---|---|
| [`hub/`](hub/) | The hub itself: `hub-daemon`, `hub-lib`, `hub-plugin`, docs, examples |
| [`web4-core/`](web4-core/) | The Web4 core library the hub builds on (AGPL-3.0-or-later) |
| [`web4-policy/`](web4-policy/) | Policy evaluation (the law gate) |
| [`web4-trust-core/`](web4-trust-core/) | T3/V3 trust tensor primitives |

## Build

```bash
cd hub && cargo build --release
```

The monorepo layout is preserved so `hub/`'s relative path dependency on
`../web4-core` resolves in this standalone clone.

## Where development happens

This repository is a **read-only mirror**, published from the
[`hub/`](https://github.com/dp-web4/web4/tree/main/hub) directory of the
[dp-web4/web4](https://github.com/dp-web4/web4) monorepo by
`scripts/publish-4-hub.sh`. History here is the filtered history of those
paths. **File issues and PRs against
[dp-web4/web4](https://github.com/dp-web4/web4).**

## License

Root [`LICENSE`](LICENSE) (AGPL-3.0-or-later) covers `hub/`;
[`web4-core/LICENSE`](web4-core/LICENSE) is the same AGPL-3.0-or-later text
(the crate declares `license = "AGPL-3.0-or-later"`). The patent grant in
[`PATENTS.md`](PATENTS.md) is royalty-free for non-commercial use, research and
academic use, and open-source projects that comply with AGPL-3.0; commercial
licensing is separate.
EOF
git add README.md
git -c user.name="4-hub mirror" -c user.email="noreply@metalinxx.io" \
  commit -q -m "mirror: root README (generated by scripts/publish-4-hub.sh)"

echo "[4-hub] force-pushing mirror..."
git push --force -q "$MIRROR_REMOTE" HEAD:main

echo "[4-hub] done: https://github.com/dp-web4/4-hub"
