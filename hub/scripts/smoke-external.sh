#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
#
# Web4 Hub — external (peer-side) reachability smoke.
#
# Confirms the live hub daemon is reachable FROM ANOTHER MACHINE over the
# network, not just from the host it runs on. This catches a common class of
# regression: the daemon bound to 127.0.0.1 (e.g. behind a reverse proxy), so a
# localhost smoke passes 200 while every other machine gets connection-refused.
#
# A host-side smoke (even one that curls the host's own network address) cannot
# catch a host firewall block or a network ACL that only affects *inbound from
# peers*. The only honest reachability check is one run FROM a different
# machine — run this on a peer node, not on the hub host.
#
# Usage:
#   HUB_HOST=<addr> HUB_PORT=8770 ./smoke-external.sh
#   HUB_URL=http://<addr>:8770 ./smoke-external.sh
#
# Exit codes:
#   0  all checks passed (hub is peer-reachable and healthy)
#   1  a check failed (treat as a FAILED deploy)
#   2  prerequisite missing (curl not found, bad args)
#
# Intended use: run as the last step of the hub supervisor's deploy phase,
# OR by any peer that wants to confirm the live hub is reachable. Read-only —
# only hits GET tool endpoints, mutates nothing, needs no credentials.

set -euo pipefail

# The hub's network address — override via env for your deployment.
HUB_HOST="${HUB_HOST:-100.65.206.122}"
HUB_PORT="${HUB_PORT:-8770}"
HUB_URL="${HUB_URL:-http://${HUB_HOST}:${HUB_PORT}}"
TIMEOUT="${TIMEOUT:-5}"

if ! command -v curl >/dev/null 2>&1; then
    echo "error: curl not found on PATH" >&2
    exit 2
fi

echo "============================================================"
echo "Web4 Hub — external peer-side reachability smoke"
echo "============================================================"
echo "  Target:    $HUB_URL"
echo "  From host: $(hostname)"
echo "  Timeout:   ${TIMEOUT}s"
echo ""

fail=0

# A peer reaching the hub at all is the load-bearing assertion. If TCP connect
# itself is refused (bind drift / firewall), curl exits non-zero and %{http_code}
# is 000 — we surface both the curl exit and the code.
check() {
    local label="$1" path="$2"
    local url="${HUB_URL}${path}"
    local code rc
    # Don't let `set -e` abort on a curl failure — we want to report it.
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time "$TIMEOUT" "$url" 2>/dev/null)" && rc=0 || rc=$?
    if [ "$rc" -ne 0 ]; then
        printf "  FAIL  %-14s %s  (curl exit %s — likely connection refused / unreachable)\n" "$label" "$url" "$rc"
        fail=1
        return
    fi
    if [ "$code" = "200" ]; then
        printf "  ok    %-14s %s  -> %s\n" "$label" "$url" "$code"
    else
        printf "  FAIL  %-14s %s  -> %s  (expected 200)\n" "$label" "$url" "$code"
        fail=1
    fi
}

# Read-only tool surface. query_hub is canonical (query_chapter is the legacy
# alias post chapter->hub rename); we hit query_hub so a removed alias doesn't
# mask a real outage.
check "tools"      "/tools"
check "query_hub"  "/tools/query_hub"

echo ""
if [ "$fail" -eq 0 ]; then
    # On success, surface a snippet of society state so the operator sees the
    # hub is not just answering but answering with real data.
    echo "  society snapshot:"
    curl -s --max-time "$TIMEOUT" "${HUB_URL}/tools/query_hub" \
        | head -c 400 | sed 's/^/    /'
    echo ""
    echo ""
    echo "RESULT: PASS — hub is peer-reachable and healthy from $(hostname)."
    exit 0
else
    echo "RESULT: FAIL — hub is NOT properly reachable from this peer." >&2
    echo "" >&2
    echo "  This is the bind-drift / firewall / ACL class of failure. A host-side" >&2
    echo "  (localhost) smoke can pass while this fails. Check, in order:" >&2
    echo "    1. daemon bind address — must be 0.0.0.0:${HUB_PORT}, not 127.0.0.1" >&2
    echo "         (systemd unit: --bind 0.0.0.0; confirm with 'ss -ltnp | grep ${HUB_PORT}')" >&2
    echo "    2. host firewall — Windows host must allow inbound TCP ${HUB_PORT} to the WSL2 VM" >&2
    echo "    3. network ACL / firewall — peers must be permitted to reach the hub node on ${HUB_PORT}" >&2
    exit 1
fi
