// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Is the hub executing a **ratified** build? — Sprint F0.3 / PRD R7c.
//!
//! ## Currency is not ratification
//!
//! The fleet already has a currency instrument: it answers *does the running
//! process image equal the on-disk binary, and does that binary postdate the
//! merged source?* Both are necessary and neither is sufficient, because a
//! binary built from a **parked feature branch** passes both — the process
//! matches the file, and the file is newer than anything merged. That is not a
//! hypothetical: a build on a parked branch put unmerged code at `ExecStart`
//! and HEAD-based currency called it clean.
//!
//! This module asks the question currency cannot: *is what runs here the build
//! the society ratified?* It compares two records that are produced
//! independently —
//!
//! - **what is running** — [`crate::build_info::BUILD`], stamped into the
//!   artifact at compile time, so the running binary attests its own identity
//!   rather than an observer reconstructing it from file mtimes and `/proc`
//!   inodes (a reconstruction that has already failed open here);
//! - **what was ratified** — a supervisor-owned manifest, written by the deploy
//!   path, never by the daemon.
//!
//! The daemon is deliberately a **reader** of the manifest. A process that
//! could write its own ratification record would be certifying itself, which is
//! the shape this exists to refuse.
//!
//! ## Fail-closed
//!
//! Every unestablished condition resolves to [`DeployVerdict::Unknown`], never
//! to `Current`. An absent manifest, an unparseable one, a build whose
//! provenance could not be established — each is *"we do not know"*, which is
//! an operator-visible state and not a pass. `Unknown` and `Stale` are kept
//! distinct for the same reason `Refuted` and `Undecidable` are in the sponsor
//! predicate: a guard with one failure exit either certifies a lie or becomes
//! unsatisfiable, and "nobody has ratified anything yet" calls for a different
//! human response than "this seat is running something that was not ratified."

use crate::build_info::{BuildInfo, Provenance};
use serde::{Deserialize, Serialize};
use std::path::Path;

/// The supervisor-owned record of what this seat is approved to run.
///
/// Written by the deploy path (a human or a supervisor process that has
/// verified the build), read by everyone. Deliberately small: a ratification
/// record with many fields invites partial writes and per-field drift.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct RatifiedManifest {
    /// The commit the ratified build was compiled from. Compared against
    /// [`BuildInfo::git_sha`], which the running binary attests about itself.
    pub ratified_git_sha: String,
    /// SHA-256 of the ratified binary, hex. Lets the staged-artifact check
    /// (`ExecStart` path) answer *before* a restart makes it the running one.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ratified_binary_sha256: Option<String>,
    /// RFC 3339 instant of ratification — operator context, not a check input.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ratified_at: Option<String>,
    /// Who ratified it — operator context.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ratified_by: Option<String>,
}

impl RatifiedManifest {
    /// Read the manifest from `path`. A missing file is `Ok(None)` — "no
    /// ratification recorded" is a legitimate state that must render as
    /// `Unknown`, not as an error that a caller might swallow into a pass.
    /// A present-but-unparseable file is `Err`: something IS there and it is
    /// wrong, which is not the same as nothing being there.
    pub fn read(path: &Path) -> anyhow::Result<Option<Self>> {
        match std::fs::read_to_string(path) {
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
            Err(e) => Err(anyhow::anyhow!("reading ratified manifest: {e}")),
            Ok(s) => {
                let m: Self = serde_json::from_str(&s)
                    .map_err(|e| anyhow::anyhow!("parsing ratified manifest: {e}"))?;
                if m.ratified_git_sha.trim().is_empty() {
                    anyhow::bail!("ratified manifest has an empty ratified_git_sha");
                }
                Ok(Some(m))
            }
        }
    }
}

/// What the seat is running, relative to what was ratified.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "verdict", rename_all = "lowercase")]
pub enum DeployVerdict {
    /// Running exactly the ratified build, from a clean tree.
    Current,
    /// Established as NOT the ratified build. Carries what differs.
    Stale { reason: String },
    /// Could not be established either way. Never a pass.
    Unknown { reason: String },
}

impl DeployVerdict {
    pub fn token(&self) -> &'static str {
        match self {
            DeployVerdict::Current => "current",
            DeployVerdict::Stale { .. } => "stale",
            DeployVerdict::Unknown { .. } => "unknown",
        }
    }
    /// Only `Current` is a pass. Used by callers that need a boolean without
    /// re-deriving the fail-closed rule (and thereby getting it wrong).
    pub fn is_current(&self) -> bool {
        matches!(self, DeployVerdict::Current)
    }
    pub fn detail(&self) -> Option<&str> {
        match self {
            DeployVerdict::Current => None,
            DeployVerdict::Stale { reason } | DeployVerdict::Unknown { reason } => Some(reason),
        }
    }
}

/// Evaluate the **running** binary against the ratified manifest.
///
/// Pure: the running side comes from the compile-time stamp the artifact
/// carries, the ratified side from the supervisor's record.
pub fn evaluate_running(build: &BuildInfo, manifest: Option<&RatifiedManifest>) -> DeployVerdict {
    let Some(m) = manifest else {
        return DeployVerdict::Unknown {
            reason: "no ratified-build manifest on this seat — nothing has been recorded as \
                     approved to run here".to_string(),
        };
    };
    // A build that cannot say what it came from cannot be matched to anything.
    if build.git_sha == "unknown" || build.git_sha.is_empty() {
        return DeployVerdict::Unknown {
            reason: "this binary carries no build commit, so it cannot be compared to the \
                     ratified one".to_string(),
        };
    }
    // Provenance first: a dirty tree means the artifact is not any commit, so
    // a matching sha would be a coincidence of naming, not of content. Unknown
    // provenance is explicitly NOT folded into clean.
    match build.provenance {
        Provenance::Dirty => {
            return DeployVerdict::Stale {
                reason: format!(
                    "built from a MODIFIED tree at {} — a dirty build is not the ratified \
                     artifact even when the commit matches",
                    build.git_sha_short
                ),
            };
        }
        Provenance::Unknown => {
            return DeployVerdict::Unknown {
                reason: format!(
                    "build provenance at {} could not be established; an unverified tree \
                     state is not an assertion that it was clean",
                    build.git_sha_short
                ),
            };
        }
        Provenance::Clean => {}
    }
    if !sha_matches(&m.ratified_git_sha, build.git_sha) {
        return DeployVerdict::Stale {
            reason: format!(
                "running {} but {} is ratified for this seat",
                build.git_sha_short,
                short(&m.ratified_git_sha)
            ),
        };
    }
    DeployVerdict::Current
}

/// Evaluate the artifact **staged at the exec path** against the manifest.
///
/// This is the arm that answers before a restart: an unratified binary dropped
/// where the unit will next execute it is a fact the operator should see
/// *now*, not discover after the ignition that makes it the running one. (The
/// deploy path is part of the governance closure precisely because a write
/// that redirects *which* binary executes is equivalent to a write to the
/// binary.)
///
/// `staged_sha256` is the digest of the file at the exec path, or `None` when
/// it could not be read.
pub fn evaluate_staged(
    staged_sha256: Option<&str>,
    manifest: Option<&RatifiedManifest>,
) -> DeployVerdict {
    let Some(m) = manifest else {
        return DeployVerdict::Unknown {
            reason: "no ratified-build manifest to compare the staged artifact against"
                .to_string(),
        };
    };
    let Some(ratified) = m.ratified_binary_sha256.as_deref() else {
        return DeployVerdict::Unknown {
            reason: "the ratified manifest records no binary digest, so a staged artifact \
                     cannot be checked before it runs".to_string(),
        };
    };
    let Some(staged) = staged_sha256 else {
        return DeployVerdict::Unknown {
            reason: "could not read the artifact at the exec path".to_string(),
        };
    };
    if staged.eq_ignore_ascii_case(ratified) {
        DeployVerdict::Current
    } else {
        DeployVerdict::Stale {
            reason: format!(
                "the artifact staged at the exec path ({}…) is not the ratified binary ({}…) — \
                 the next restart would run something unratified",
                short(staged),
                short(ratified)
            ),
        }
    }
}

/// SHA-256 of a file, hex. `None` when it cannot be read — the caller renders
/// that as `Unknown`, never as a match.
pub fn file_sha256(path: &Path) -> Option<String> {
    std::fs::read(path).ok().map(|b| web4_core::crypto::sha256_hex(&b))
}

/// Compare two commit shas allowing either side to be abbreviated — the
/// manifest may record a short sha, the build a full one. Comparison is on the
/// shorter length, case-insensitively, and an empty or absurdly short value
/// never matches (a 1-character "sha" must not prefix-match everything).
fn sha_matches(a: &str, b: &str) -> bool {
    let (a, b) = (a.trim(), b.trim());
    let n = a.len().min(b.len());
    if n < 7 {
        return false;
    }
    a[..n].eq_ignore_ascii_case(&b[..n])
}

fn short(s: &str) -> String {
    s.chars().take(12).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn build(sha: &'static str, prov: Provenance) -> BuildInfo {
        BuildInfo {
            version: "test",
            git_sha: sha,
            git_sha_short: "abcdef1",
            provenance: prov,
            built_at: "2026-08-13T00:00:00Z",
        }
    }

    fn manifest(sha: &str) -> RatifiedManifest {
        RatifiedManifest {
            ratified_git_sha: sha.to_string(),
            ratified_binary_sha256: None,
            ratified_at: None,
            ratified_by: None,
        }
    }

    #[test]
    fn matching_clean_build_is_current() {
        let b = build("abcdef1234567890", Provenance::Clean);
        assert_eq!(evaluate_running(&b, Some(&manifest("abcdef1234567890"))), DeployVerdict::Current);
    }

    /// **The parked-checkout case this module exists for.** The binary is
    /// clean, newer than merged source, and the process image matches the file
    /// — every currency arm passes — but it was built from a commit nobody
    /// ratified.
    #[test]
    fn a_clean_build_of_an_unratified_commit_is_stale() {
        let b = build("feedface00000000", Provenance::Clean);
        let v = evaluate_running(&b, Some(&manifest("abcdef1234567890")));
        assert!(matches!(v, DeployVerdict::Stale { .. }), "got {v:?}");
        assert!(v.detail().unwrap().contains("ratified"));
        assert!(!v.is_current());
    }

    /// A dirty tree is not the ratified artifact even when the commit matches:
    /// the binary is not any commit.
    #[test]
    fn a_dirty_build_is_stale_even_at_the_ratified_commit() {
        let b = build("abcdef1234567890", Provenance::Dirty);
        let v = evaluate_running(&b, Some(&manifest("abcdef1234567890")));
        assert!(matches!(v, DeployVerdict::Stale { .. }), "got {v:?}");
        assert!(v.detail().unwrap().contains("MODIFIED"));
    }

    /// Unknown provenance is NOT folded into clean — an unverified tree state
    /// is not an assertion that it was clean.
    #[test]
    fn unknown_provenance_is_unknown_not_current() {
        let b = build("abcdef1234567890", Provenance::Unknown);
        let v = evaluate_running(&b, Some(&manifest("abcdef1234567890")));
        assert!(matches!(v, DeployVerdict::Unknown { .. }), "got {v:?}");
        assert!(!v.is_current());
    }

    /// The two failure exits stay distinct: "nothing was ratified" needs a
    /// different human response from "this is not the ratified build".
    #[test]
    fn absent_manifest_is_unknown_not_stale_and_never_current() {
        let b = build("abcdef1234567890", Provenance::Clean);
        let v = evaluate_running(&b, None);
        assert!(matches!(v, DeployVerdict::Unknown { .. }), "got {v:?}");
        assert!(!v.is_current(), "an unratified seat never reads as a pass");
    }

    #[test]
    fn a_build_with_no_commit_cannot_be_matched() {
        let b = build("unknown", Provenance::Clean);
        assert!(matches!(
            evaluate_running(&b, Some(&manifest("abcdef1234567890"))),
            DeployVerdict::Unknown { .. }
        ));
    }

    #[test]
    fn abbreviated_shas_compare_on_the_shorter_length() {
        let b = build("abcdef1234567890", Provenance::Clean);
        assert_eq!(evaluate_running(&b, Some(&manifest("abcdef1"))), DeployVerdict::Current);
        // ...but a stub must not prefix-match the world.
        let v = evaluate_running(&b, Some(&manifest("ab")));
        assert!(matches!(v, DeployVerdict::Stale { .. }), "got {v:?}");
    }

    #[test]
    fn staged_artifact_is_checked_before_it_runs() {
        let mut m = manifest("abcdef1234567890");
        m.ratified_binary_sha256 = Some("aa".repeat(32));
        assert_eq!(evaluate_staged(Some(&"aa".repeat(32)), Some(&m)), DeployVerdict::Current);
        let v = evaluate_staged(Some(&"bb".repeat(32)), Some(&m));
        assert!(matches!(v, DeployVerdict::Stale { .. }), "got {v:?}");
        assert!(v.detail().unwrap().contains("next restart"),
            "the operator is told what the consequence is");
        // Unreadable artifact, and a manifest with no digest, are both unknown.
        assert!(matches!(evaluate_staged(None, Some(&m)), DeployVerdict::Unknown { .. }));
        let no_digest = manifest("abcdef1234567890");
        assert!(matches!(
            evaluate_staged(Some(&"aa".repeat(32)), Some(&no_digest)),
            DeployVerdict::Unknown { .. }
        ));
    }

    #[test]
    fn manifest_read_distinguishes_absent_from_malformed() {
        let dir = std::env::temp_dir().join(format!("hub-ratified-{}", uuid::Uuid::new_v4()));
        std::fs::create_dir_all(&dir).unwrap();
        let missing = dir.join("nope.json");
        assert!(RatifiedManifest::read(&missing).unwrap().is_none(),
            "absent is a state, not an error");

        let bad = dir.join("bad.json");
        std::fs::write(&bad, b"{not json").unwrap();
        assert!(RatifiedManifest::read(&bad).is_err(),
            "something IS there and it is wrong — not the same as nothing");

        let empty_sha = dir.join("empty.json");
        std::fs::write(&empty_sha, br#"{"ratified_git_sha":"  "}"#).unwrap();
        assert!(RatifiedManifest::read(&empty_sha).is_err(),
            "a manifest that ratifies nothing is malformed, not permissive");

        let good = dir.join("good.json");
        std::fs::write(&good, br#"{"ratified_git_sha":"abcdef1234567890","ratified_by":"dp"}"#).unwrap();
        let m = RatifiedManifest::read(&good).unwrap().expect("parsed");
        assert_eq!(m.ratified_git_sha, "abcdef1234567890");
        assert_eq!(m.ratified_by.as_deref(), Some("dp"));
    }
}
