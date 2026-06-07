# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Metalinxx Inc.
#
# AIC Hub — multi-stage Docker build.
#
# Build context must be the web4 repo root (not web4/hub), because the
# workspace has path-dependencies on sibling crates web4-core and
# web4-trust-core. From web4/:
#
#   docker build -t hub:0.1.0-alpha.0 -f hub/Dockerfile .
#
# Or use docker-compose from inside web4/hub/.
#
# Image size target: <50 MB. Achieved by:
# - multi-stage build (build deps not in runtime image)
# - debian:bookworm-slim runtime
# - statically link nothing — just the hub binary + needed dynamic libs

# ─── Builder ─────────────────────────────────────────────────────────────
FROM rust:1.83-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Copy only what hub needs: hub itself + path-dependency siblings.
COPY web4-core ./web4-core
COPY web4-trust-core ./web4-trust-core
COPY hub ./hub

WORKDIR /src/hub
RUN cargo build --release --bin hub

# ─── Runtime ─────────────────────────────────────────────────────────────
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 hub

USER hub
WORKDIR /home/hub

COPY --from=builder /src/hub/target/release/hub /usr/local/bin/hub

# Default port; override at compose level if needed.
EXPOSE 8770

# Default to printing help — concrete commands come from `docker run hub <cmd>`
# or via docker-compose's `command:` directive.
ENTRYPOINT ["hub"]
CMD ["--help"]
