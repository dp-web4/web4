// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! AIC Hub daemon — single-binary entrypoint.
//!
//! Sprint 0 surface: `hub --version` and `hub --help`. Subcommands land
//! sprint-by-sprint (see `docs/SPRINTS.md`):
//!
//! - Sprint 1: `hub init <chapter-name> --sovereign-lct <path>`
//! - Sprint 2: `hub record-event <event>` (writes to chapter ledger)
//! - Sprint 3: `hub serve` (MCP server on configured port)
//! - Sprint 4: `hub status`, `hub add-member`, `hub assign-role`, `hub query`
//! - Sprint 5: Docker compose entrypoint (no source change; ships as ENTRYPOINT)
//! - Sprint 6: error-message audit + docs polish

use clap::Parser;

/// AIC Hub — minimum-viable Web4 society for a community chapter.
#[derive(Parser, Debug)]
#[command(name = "hub", version = hub_lib::VERSION, about, long_about = None)]
struct Cli {
    // Subcommands land in subsequent sprints.
}

fn main() -> anyhow::Result<()> {
    let _filter = tracing_subscriber::EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info"));
    tracing_subscriber::fmt().with_env_filter(_filter).init();

    let _cli = Cli::parse();

    // Sprint 0: parser handles `--version` and `--help` automatically.
    // Running with no args is a valid no-op until sprint 1 lands subcommands.
    tracing::info!(version = hub_lib::VERSION, "hub daemon starting (sprint 0 scaffold)");
    Ok(())
}
