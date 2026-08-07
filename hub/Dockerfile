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
# Toolchain floor is REAL, not stylistic: `uuid` declares rust-version 1.85 and
# `aws-config` (the DynamoDB backend) declares 1.91.1, both in hub's lockfile. The
# previous pin was 1.83, which cannot build this image at all. Pinned to the
# version this workspace is actually built and tested with on the fleet (1.96).
#
# To re-derive the floor after a dependency bump:
#   grep -rhm1 '^rust-version' ~/.cargo/registry/src/*/*/Cargo.toml \
#     | cut -d'"' -f2 | sort -V | tail -1
FROM rust:1.96-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Copy only what hub needs: hub itself + path-dependency siblings.
#
# The sibling list must match hub's ACTUAL path dependencies, which are three:
# `web4-core`, `web4-trust-core` and `web4-policy` (hub/Cargo.toml). `web4-policy`
# was missing here, so this image could not build at all -- cargo resolves the
# path dep against a directory that was never copied. `hub-lib` needs no line of
# its own because it lives INSIDE hub/ and arrives with `COPY hub`.
COPY web4-core ./web4-core
COPY web4-trust-core ./web4-trust-core
COPY web4-policy ./web4-policy
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
