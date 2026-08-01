// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! What this binary was built from — recorded at production, not inferred later.
//!
//! [`VERSION`](crate::VERSION) is a *name*: a hand-maintained string in the
//! workspace `Cargo.toml`. It last changed 2026-06-08 and has not moved across
//! any `hub/` commit since, so it cannot distinguish two binaries and never
//! could. [`BUILD`] is the re-derivable record that can: the commit the source
//! was at, whether the tree was modified relative to it, and when the compile
//! happened. See `hub-lib/build.rs` for how it is stamped and for the exact
//! freshness guarantee (`git_sha` is exact across a merge; `provenance` is a
//! floor).
//!
//! The point of putting it here rather than only behind `--version` is that the
//! daemon publishes it (`GET /tools/query_hub`). A hub that can be *asked* what
//! it is does not need an observer to reconstruct the answer from `/proc` inode
//! identity and file mtimes — a reconstruction that has already failed open.

use serde::Serialize;

/// Whether the source tree matched the recorded commit at build time.
///
/// `Unknown` is a real answer and the default for anything unestablished — a
/// tarball with no git, a `git` that failed. It is deliberately not folded into
/// `Clean`: a provenance claim that cannot be verified is not a claim that the
/// tree was clean.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Provenance {
    /// `hub/` had no tracked modifications against `git_sha`.
    Clean,
    /// `hub/` had tracked modifications — this binary is not any commit.
    Dirty,
    /// Could not be established. Not an assertion of cleanliness.
    Unknown,
}

/// The build's self-description, as published by `query_hub` and printed by
/// `hub --version`.
#[derive(Debug, Clone, Copy, Serialize)]
pub struct BuildInfo {
    /// `CARGO_PKG_VERSION`. Retained for continuity; it is a name, and it does
    /// not identify a build.
    pub version: &'static str,
    /// Full commit SHA the source was at, or `"unknown"`.
    pub git_sha: &'static str,
    /// Abbreviated commit SHA, or `"unknown"`.
    pub git_sha_short: &'static str,
    /// Tree state against `git_sha` at build time.
    pub provenance: Provenance,
    /// RFC 3339 UTC instant the stamp was produced.
    pub built_at: &'static str,
}

/// Parsed at compile time from the `build.rs` stamp.
///
/// The wildcard arm maps every unrecognised value to [`Provenance::Unknown`]
/// rather than to `Clean` — the fleet's ratified fail-closed default. There is
/// no input that makes an unverified build report as verified.
const fn provenance(s: &str) -> Provenance {
    match s.as_bytes() {
        [b'c', b'l', b'e', b'a', b'n'] => Provenance::Clean,
        [b'd', b'i', b'r', b't', b'y'] => Provenance::Dirty,
        _ => Provenance::Unknown,
    }
}

/// This binary's provenance. Constant — stamped into the artifact at compile
/// time, so it cannot drift from the artifact the way an external record can.
pub const BUILD: BuildInfo = BuildInfo {
    version: crate::VERSION,
    git_sha: env!("HUB_BUILD_GIT_SHA"),
    git_sha_short: env!("HUB_BUILD_GIT_SHA_SHORT"),
    provenance: provenance(env!("HUB_BUILD_PROVENANCE")),
    built_at: env!("HUB_BUILD_AT"),
};

/// One-line human form, e.g.
/// `0.1.0-alpha.0 (0fb9d95 clean, built 2026-08-01T21:15:03Z)`.
///
/// Assembled by `concat!` from the same `env!` stamps [`BUILD`] parses, so the
/// printed line and the published JSON cannot disagree — there is one record,
/// rendered twice, not two records to be kept in step. (A second hand-formatted
/// copy would be the drift this module exists to remove, reintroduced inside
/// it.) It is a `const` because clap's `version` needs a `&'static str`.
pub const SUMMARY: &str = concat!(
    env!("CARGO_PKG_VERSION"),
    " (",
    env!("HUB_BUILD_GIT_SHA_SHORT"),
    " ",
    env!("HUB_BUILD_PROVENANCE"),
    ", built ",
    env!("HUB_BUILD_AT"),
    ")"
);

#[cfg(test)]
mod tests {
    use super::*;

    /// The stamp exists and is not the empty string in any field. A build.rs
    /// that silently emitted nothing would leave `env!` failing to compile, so
    /// this is really guarding the *contents* against a stamp of `""`.
    #[test]
    fn the_stamp_is_populated() {
        assert!(!BUILD.git_sha.is_empty());
        assert!(!BUILD.git_sha_short.is_empty());
        assert!(!BUILD.built_at.is_empty());
        assert_eq!(BUILD.version, crate::VERSION);
    }

    /// In this repo the build runs inside a git checkout, so the SHA must be a
    /// real 40-hex object and not the `unknown` fallback. This is what makes
    /// the field usable as a deploy-currency answer rather than decoration —
    /// if the stamp ever silently degrades to `unknown` in CI, that is a
    /// regression in the mechanism and not a cosmetic one.
    #[test]
    fn a_git_checkout_stamps_a_real_sha() {
        assert_ne!(BUILD.git_sha, "unknown", "built inside a git checkout");
        assert_eq!(BUILD.git_sha.len(), 40, "full object id");
        assert!(BUILD.git_sha.chars().all(|c| c.is_ascii_hexdigit()));
        assert!(BUILD.git_sha.starts_with(BUILD.git_sha_short));
    }

    /// The fail-closed arm, exercised rather than asserted about: every input
    /// other than the two recognised words must land on `Unknown`. An earlier
    /// shape of this returned `Clean` for the empty string, which would have
    /// made a git-less build claim a clean tree.
    #[test]
    fn unrecognised_provenance_is_unknown_not_clean() {
        for s in ["", "CLEAN", "clean ", "cl", "cleanx", "unknown", "true"] {
            assert_eq!(
                provenance(s),
                Provenance::Unknown,
                "{s:?} must not resolve to a verified state"
            );
        }
        assert_eq!(provenance("clean"), Provenance::Clean);
        assert_eq!(provenance("dirty"), Provenance::Dirty);
    }

    /// The human line and the published struct are the same record. A reader of
    /// `hub --version` and a reader of `query_hub` must not be able to reach
    /// different conclusions about the same binary.
    #[test]
    fn the_summary_line_agrees_with_the_published_struct() {
        assert!(SUMMARY.starts_with(BUILD.version));
        assert!(SUMMARY.contains(BUILD.git_sha_short));
        assert!(SUMMARY.contains(BUILD.built_at));
        let word = match BUILD.provenance {
            Provenance::Clean => "clean",
            Provenance::Dirty => "dirty",
            Provenance::Unknown => "unknown",
        };
        assert!(SUMMARY.contains(word), "the tree state is stated, not omitted");
        // Never silently readable as verified when it is not.
        if BUILD.provenance != Provenance::Clean {
            assert!(!SUMMARY.contains("clean"));
        }
    }

    /// Serialises with lowercase tags, since the JSON is a wire contract for
    /// any peer comparing the hub's answer against `git rev-parse HEAD`.
    #[test]
    fn it_serialises_as_a_stable_wire_shape() {
        let j = serde_json::to_value(BUILD).unwrap();
        assert!(j.get("git_sha").is_some());
        assert!(j.get("provenance").is_some());
        let p = serde_json::to_value(Provenance::Clean).unwrap();
        assert_eq!(p, serde_json::json!("clean"));
        let p = serde_json::to_value(Provenance::Unknown).unwrap();
        assert_eq!(p, serde_json::json!("unknown"));
    }
}
