// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! AIC Hub — society logic library.
//!
//! Sprint 1 modules:
//! - [`identity`] — on-disk LCT + KeyPair persistence
//! - [`charter`] — chapter founding charter (compose, hash, persist)
//! - [`chapter`] — chapter directory layout + config.toml
//! - [`init`] — `hub init` flow: bootstrap a chapter society
//!
//! Later sprints (per `docs/SPRINTS.md`):
//! - Sprint 2: `ledger` — witnessed event log via web4-core's LocalLedger
//! - Sprint 3: `mcp` — MCP server tool implementations
//! - Sprint 4: CLI subcommand handlers (most live in hub-daemon)
//!
//! Discipline reminder: this crate IS NOT the place to reimplement LCT,
//! T3/V3, MRH, ATP, R6, or Society/Role primitives. Those live in
//! `web4-core` / `web4-trust-core` and are used as dependencies. See
//! `docs/PRD.md` §10 "Risks + mitigations" for the rationale and
//! `web4/CLAUDE.md` "MRH-Specific Policy" for the development-phase
//! drift prevention.

pub mod chapter;
pub mod charter;
pub mod identity;
pub mod init;

/// Crate version, exposed for `hub --version`.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn version_is_set() {
        assert!(!VERSION.is_empty());
        assert!(VERSION.starts_with("0."));
    }
}
