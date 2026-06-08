#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
#
# AIC Hub — first-day chapter demo (native binary, no Docker).
#
# Walks a chapter organizer through their first day in ~5 minutes:
#   1. Generate a Sovereign LCT
#   2. Initialize the chapter society
#   3. Add two members
#   4. Each member declares a skill
#   5. Record a chapter event
#   6. Query members + search by skill
#   7. Start the MCP server briefly + hit it from outside
#   8. Verify the ledger end-to-end
#
# Prerequisites:
#   - `hub` binary built and on $PATH, OR set HUB=/path/to/hub
#   - python3 (only for parsing LCT id from JSON for the curl examples)
#   - curl
#
# This demo creates everything in a fresh /tmp/aic-hub-demo-<ts>/ directory
# and is safe to run repeatedly.

set -euo pipefail

HUB="${HUB:-hub}"

if ! command -v "$HUB" >/dev/null 2>&1; then
    echo "error: '$HUB' not on PATH"
    echo "       set HUB=/absolute/path/to/hub or `cargo build --release` first"
    exit 1
fi

DEMO_ROOT="/tmp/aic-hub-demo-$(date +%s)"
mkdir -p "$DEMO_ROOT"
cd "$DEMO_ROOT"

echo "============================================================"
echo "AIC Hub — first chapter demo"
echo "============================================================"
echo "  Demo dir: $DEMO_ROOT"
echo "  Binary:   $HUB ($($HUB --version))"
echo ""

# ── Step 1: Sovereign LCT ──
echo "── 1. Generate Sovereign LCT ─────────────────────────────────"
"$HUB" gen-lct "$DEMO_ROOT/sovereign.json"
echo ""

# ── Step 2: Member LCTs (for the demo) ──
echo "── 2. Generate two member LCTs (Alice + Bob) ────────────────"
"$HUB" gen-lct "$DEMO_ROOT/alice.json"
"$HUB" gen-lct "$DEMO_ROOT/bob.json"
ALICE_ID=$(python3 -c "import json; print(json.load(open('$DEMO_ROOT/alice.json'))['lct']['id'])")
BOB_ID=$(python3 -c "import json; print(json.load(open('$DEMO_ROOT/bob.json'))['lct']['id'])")
echo "  Alice LCT: $ALICE_ID"
echo "  Bob   LCT: $BOB_ID"
echo ""

# ── Step 3: Init chapter ──
echo "── 3. Initialize chapter society ────────────────────────────"
"$HUB" init "Demo Chapter" --sovereign-lct "$DEMO_ROOT/sovereign.json" --hub-dir "$DEMO_ROOT/demo-chapter"
echo ""

# ── Step 4: Add members + skills ──
echo "── 4. Add members and declare their skills ─────────────────"
CHAPTER="$DEMO_ROOT/demo-chapter"
"$HUB" add-member "$CHAPTER" "$ALICE_ID" --name "Alice"
"$HUB" add-member "$CHAPTER" "$BOB_ID" --name "Bob"
"$HUB" declare-skill "$CHAPTER" "$ALICE_ID" "Medical Imaging RAG"
"$HUB" declare-skill "$CHAPTER" "$BOB_ID" "Distributed Systems"
echo ""

# ── Step 5: Record event ──
echo "── 5. Record a chapter event ────────────────────────────────"
"$HUB" record-event "$CHAPTER" demo_night "First Demo Night" --attended-by "$ALICE_ID,$BOB_ID"
echo ""

# ── Step 6: Query ──
echo "── 6. Query the chapter ─────────────────────────────────────"
"$HUB" query members "$CHAPTER"
echo ""
"$HUB" query skill "$CHAPTER" imaging
echo ""

# ── Step 7: Start daemon briefly + hit MCP from outside ──
echo "── 7. Run MCP server briefly + hit it from outside ──────────"
# Pick a random high port to avoid collisions with leftover daemons
PORT=$(( ( RANDOM % 1000 ) + 18000 ))
"$HUB" serve "$CHAPTER" --port "$PORT" > "$DEMO_ROOT/serve.log" 2>&1 &
DAEMON_PID=$!
sleep 1

echo "  Daemon PID $DAEMON_PID on port $PORT"
echo "  GET /tools — tool catalog:"
curl -s "http://127.0.0.1:$PORT/tools" | python3 -m json.tool | head -30
echo ""
echo "  GET /tools/query_chapter:"
curl -s "http://127.0.0.1:$PORT/tools/query_chapter" | python3 -m json.tool
echo ""

kill "$DAEMON_PID" 2>/dev/null
wait "$DAEMON_PID" 2>/dev/null || true
echo "  Daemon stopped."
echo ""

# ── Step 8: Verify the ledger ──
echo "── 8. Verify ledger end-to-end ──────────────────────────────"
"$HUB" verify-ledger "$CHAPTER"
echo ""

echo "============================================================"
echo "Demo complete. Inspect the chapter at:"
echo "  $CHAPTER/"
echo ""
echo "  - charter.json      the founding charter"
echo "  - society.json      web4_core::Society state"
echo "  - ledger.jsonl      append-only signed event log"
echo "  - config.toml       daemon + Sovereign config"
echo "============================================================"
