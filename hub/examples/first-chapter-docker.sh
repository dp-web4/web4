#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
#
# AIC Hub — first-day chapter demo via Docker compose.
#
# Companion to first-chapter.sh (which uses the native binary). This
# version uses the Docker image so a chapter organizer with no Rust
# toolchain can deploy the same chapter in containers.
#
# Prerequisites:
#   - docker + docker compose
#   - cd web4/hub/ before running
#   - python3 + curl for the demo queries
#
# Run from the hub/ directory:
#   bash examples/first-chapter-docker.sh
#
# NOTE (2026-06-07): runtime not yet verified on a machine with Docker —
# the author's dev machine doesn't have Docker installed. The artifacts
# (Dockerfile, docker-compose.yml) follow standard patterns and should
# build cleanly, but the first chapter operator to run this end-to-end
# should report back if anything stumbles.

set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
    echo "error: docker not installed. See https://docs.docker.com/engine/install/"
    exit 1
fi

# Compose v2 is `docker compose`; v1 was `docker-compose`. Prefer v2.
COMPOSE="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    COMPOSE="docker-compose"
    if ! command -v docker-compose >/dev/null 2>&1; then
        echo "error: neither 'docker compose' nor 'docker-compose' available"
        exit 1
    fi
fi

# Where the chapter state lives on the host. docker-compose.yml mounts
# this to /chapter in the container.
mkdir -p ./chapter-data
mkdir -p ./chapter-data/data  # subdir the chapter society itself lives in

echo "============================================================"
echo "AIC Hub — first chapter via Docker"
echo "============================================================"

echo ""
echo "── 1. Build image ───────────────────────────────────────────"
$COMPOSE build hub

echo ""
echo "── 2. Generate Sovereign LCT inside container ──────────────"
$COMPOSE run --rm hub gen-lct /chapter/sovereign.json

echo ""
echo "── 3. Initialize chapter inside container ──────────────────"
$COMPOSE run --rm hub init "Docker Demo Chapter" \
    --sovereign-lct /chapter/sovereign.json \
    --chapter-dir /chapter/data

echo ""
echo "── 4. Bring up the daemon ──────────────────────────────────"
$COMPOSE up -d hub
sleep 2

echo ""
echo "── 5. Hit MCP from outside the container ───────────────────"
echo "  GET /tools:"
curl -s http://localhost:8770/tools | python3 -m json.tool | head -20
echo ""
echo "  GET /tools/query_chapter:"
curl -s http://localhost:8770/tools/query_chapter | python3 -m json.tool

echo ""
echo "── 6. Tear down ────────────────────────────────────────────"
$COMPOSE down

echo ""
echo "============================================================"
echo "Demo complete. Chapter state persisted in:"
echo "  ./chapter-data/"
echo ""
echo "To bring the chapter back up later:"
echo "  $COMPOSE up -d hub"
echo "============================================================"
