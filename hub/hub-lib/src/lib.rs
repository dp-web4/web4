// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! AIC Hub — society logic library.
//!
//! Sprint 0 stub. Subsequent sprints fill in:
//! - `society` — 7-role state, founding charter, role assignments (Sprint 1)
//! - `ledger` — append-only witnessed event log (Sprint 2)
//! - `charter` — LCT-signed founding document + amendments (Sprint 1)
//! - `mcp` — MCP tool implementations (Sprint 3)
//!
//! Discipline: this crate IS NOT the place to reimplement LCT, T3/V3, MRH,
//! ATP, R6, or any other Web4 primitive. Those live in `web4-core` and
//! `web4-trust-core` and are used as dependencies. See `docs/PRD.md` §10
//! "Risks + mitigations" for the drift-prevention rationale.

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
