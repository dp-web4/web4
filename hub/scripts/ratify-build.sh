#!/usr/bin/env bash
# ratify-build.sh — record which build a hub seat is approved to run.
#
# Sprint F0.3 / PRD R7c. This writes the SUPERVISOR side of the deploy
# ratification check; the daemon only ever reads it. That asymmetry is the
# point: a process that could write its own ratification record would be
# certifying itself, which is precisely the shape the check exists to refuse.
#
# WHY THIS EXISTS, given the fleet already has a currency check:
#   The currency instrument answers "is the running image the on-disk binary,
#   and does that binary postdate the merged source?" A binary built from a
#   PARKED FEATURE BRANCH passes both arms — the process matches the file, and
#   the file is newer than anything merged. Measured on this fleet: a build on
#   a parked branch put unmerged code at ExecStart and HEAD-based currency read
#   it clean. Currency is not ratification.
#
# WHAT RATIFICATION MEANS HERE: a human (or a supervisor that verified it)
# asserts "this commit is the one this seat may run." The daemon then compares
# that against what the running binary attests about itself (a compile-time
# stamp, not an observer's reconstruction from mtimes and /proc inodes — that
# reconstruction has already failed open here).
#
# Usage:
#   ratify-build.sh <git-sha> [binary-path] [--manifest <path>] [--by <who>]
#   ratify-build.sh --from-binary <binary-path> ...   # read the sha the binary attests
#
# The manifest path defaults to $HUB_RATIFIED_MANIFEST, else <hub-root>/ratified-build.json
# via --root, else ./ratified-build.json.
#
# DEPLOYMENT NOTE: prefer a manifest the daemon user CANNOT write (root-owned,
# 0644). The daemon needs read only, and a ratification record writable by the
# thing it ratifies is not a control. Point the daemon at it with
# HUB_RATIFIED_MANIFEST.
#
# Exit codes: 0 written · 1 refused (bad input / unverifiable) · 2 usage.

set -euo pipefail

die()  { echo "ratify-build: $*" >&2; exit 1; }
usage(){ sed -n '1,40p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'; exit 2; }

SHA=""; BIN=""; MANIFEST="${HUB_RATIFIED_MANIFEST:-}"; BY="${USER:-unknown}"; ROOT=""
FROM_BINARY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --from-binary) FROM_BINARY=1; BIN="${2:-}"; shift 2 ;;
    --manifest)    MANIFEST="${2:-}"; shift 2 ;;
    --by)          BY="${2:-}"; shift 2 ;;
    --root)        ROOT="${2:-}"; shift 2 ;;
    -h|--help)     usage ;;
    -*)            die "unknown flag $1" ;;
    *)             if [ -z "$SHA" ] && [ "$FROM_BINARY" = 0 ]; then SHA="$1"
                   elif [ -z "$BIN" ]; then BIN="$1"
                   else die "unexpected argument $1"; fi; shift ;;
  esac
done

if [ -z "$MANIFEST" ]; then
  if [ -n "$ROOT" ]; then MANIFEST="$ROOT/ratified-build.json"
  else MANIFEST="./ratified-build.json"; fi
fi

# --from-binary: ask the artifact what it is, rather than trusting the operator's
# memory of what they built. `hub --version` prints the same stamp the daemon
# publishes, so the ratified record and the running record cannot disagree about
# what the string means.
if [ "$FROM_BINARY" = 1 ]; then
  [ -n "$BIN" ] || die "--from-binary needs a binary path"
  [ -x "$BIN" ] || die "not executable: $BIN"
  VERSION_LINE="$("$BIN" --version 2>/dev/null)" || die "could not run $BIN --version"
  # Format: "<ver> (<short-sha> <provenance>, built <ts>)"
  SHA="$(printf '%s' "$VERSION_LINE" | sed -n 's/.*(\([0-9a-f]\{7,\}\) .*/\1/p')"
  [ -n "$SHA" ] || die "could not read a build sha from: $VERSION_LINE"
  PROV="$(printf '%s' "$VERSION_LINE" | sed -n 's/.*([0-9a-f]\{7,\} \([a-z]*\).*/\1/p')"
  # A dirty or unverifiable build is not a ratifiable artifact: it is not any
  # commit, so ratifying "the commit" would name something that does not
  # describe the bytes. Refuse rather than record a claim that cannot hold.
  case "$PROV" in
    clean) ;;
    dirty)   die "refusing to ratify a build from a MODIFIED tree ($SHA dirty) — it is not any commit" ;;
    *)       die "refusing to ratify a build whose provenance is '$PROV' — unverified is not clean" ;;
  esac
fi

[ -n "$SHA" ] || usage
printf '%s' "$SHA" | grep -Eq '^[0-9a-fA-F]{7,40}$' || die "not a git sha: $SHA"

DIGEST=""
if [ -n "$BIN" ]; then
  [ -f "$BIN" ] || die "no such binary: $BIN"
  DIGEST="$(sha256sum "$BIN" | cut -d' ' -f1)"
fi

TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TMP="$(mktemp "${MANIFEST}.XXXXXX")"
{
  printf '{\n'
  printf '  "ratified_git_sha": "%s",\n' "$SHA"
  [ -n "$DIGEST" ] && printf '  "ratified_binary_sha256": "%s",\n' "$DIGEST"
  printf '  "ratified_at": "%s",\n' "$TS"
  printf '  "ratified_by": "%s"\n' "$BY"
  printf '}\n'
} > "$TMP"
# Atomic replace: a half-written ratification record must never be readable.
mv -f "$TMP" "$MANIFEST"

echo "ratified $SHA${DIGEST:+ (binary ${DIGEST:0:12}…)} → $MANIFEST"
echo "the seat's operator page will now compare its running build against this."
