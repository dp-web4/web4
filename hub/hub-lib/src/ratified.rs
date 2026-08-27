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
                m.validate()?;
                Ok(Some(m))
            }
        }
    }

    /// Admit only a well-formed record. **The validation belongs here, at
    /// admission, not at the writer.**
    ///
    /// The writer already checks shape (`ratify-build.sh` enforces hex), but
    /// this module's entire premise is that the daemon must assume nothing
    /// about the writer — the manifest is deliberately owned by a different
    /// principal, root-owned and daemon-unwritable, because "a process that
    /// could write its own ratification record would be certifying itself". A
    /// writer untrusted enough to need that asymmetry is untrusted enough to
    /// need input validation. Leaving the check on the writer's side put the
    /// whole guarantee in the hands of the party it is designed to distrust.
    ///
    /// A malformed record therefore reaches the same fail-closed rendering as
    /// any other unparseable one (`manifest unreadable` ⇒ `Unknown`, never a
    /// pass) instead of reaching a comparison at all.
    fn validate(&self) -> anyhow::Result<()> {
        let sha = self.ratified_git_sha.trim();
        if sha.is_empty() {
            anyhow::bail!("ratified manifest has an empty ratified_git_sha");
        }
        // FULL commit id, not an abbreviation. A short sha is a
        // repository-local locator whose uniqueness changes as history grows —
        // it is not a durable identity token, and in the commit-only fallback
        // (no artifact digest pinned) it is the ONLY identity claim carrying
        // the control. Accepting 7 hex characters would ratify any future
        // commit sharing 28 bits of prefix.
        if sha.len() != 40 || !sha.chars().all(|c| c.is_ascii_hexdigit()) {
            anyhow::bail!(
                "ratified_git_sha must be a full 40-character hex commit id \
                 (got {} character(s)); an abbreviation is a repo-local locator, \
                 not an identity — resolve it before writing the manifest",
                sha.chars().count()
            );
        }
        if let Some(d) = self.ratified_binary_sha256.as_deref() {
            let d = d.trim();
            if d.len() != 64 || !d.chars().all(|c| c.is_ascii_hexdigit()) {
                anyhow::bail!(
                    "ratified_binary_sha256 must be 64 hex characters (got {})",
                    d.chars().count()
                );
            }
        }
        Ok(())
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
/// carries plus the digest of the executing image, the ratified side from the
/// supervisor's record.
///
/// **Commit identity is provenance; artifact identity is the ratification
/// claim.** Two builds of the same commit are not the same executable — a
/// different toolchain, different feature flags, or a tampered artifact all
/// keep the commit while changing the bytes. So when the manifest records a
/// binary digest, that digest is authoritative and must match; the commit
/// check remains as the earlier, cheaper discriminator. A manifest with no
/// digest can only support the weaker commit-level claim, and callers are
/// expected to say so on the operator surface rather than let it read as a
/// full artifact match.
///
/// `running_sha256` is the digest of the executing image (on Linux, read via
/// `/proc/self/exe`, which stays readable even after a replace-in-place has
/// unlinked the original path — that is the point: it is the bytes actually
/// running, not the bytes currently at the path).
pub fn evaluate_running(
    build: &BuildInfo,
    running_sha256: Option<&str>,
    manifest: Option<&RatifiedManifest>,
) -> DeployVerdict {
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
    // Full-to-full. `read()` admitted only a 40-hex `ratified_git_sha`, and the
    // build stamp is 40-hex by construction, so there is no shorter-operand case
    // left to have an opinion about — the prefix-identity question is closed at
    // admission rather than re-decided here on every render.
    if !m.ratified_git_sha.trim().eq_ignore_ascii_case(build.git_sha.trim()) {
        return DeployVerdict::Stale {
            reason: format!(
                "running {} but {} is ratified for this seat",
                build.git_sha_short,
                short(&m.ratified_git_sha)
            ),
        };
    }
    // The commit matches. That is provenance, not identity — decide on the
    // artifact when the manifest names one.
    match (m.ratified_binary_sha256.as_deref(), running_sha256) {
        (Some(ratified), Some(running)) => {
            if running.eq_ignore_ascii_case(ratified) {
                DeployVerdict::Current
            } else {
                DeployVerdict::Stale {
                    reason: format!(
                        "the EXECUTING artifact ({}…) is not the ratified binary ({}…) — same \
                         commit, different bytes (toolchain, build flags, or substitution)",
                        short(running),
                        short(ratified)
                    ),
                }
            }
        }
        // A digest was ratified but the running image could not be read: the
        // authoritative check could not be performed, so this is not a pass.
        (Some(_), None) => DeployVerdict::Unknown {
            reason: "the ratified manifest pins a binary digest, but the executing image \
                     could not be read to compare against it".to_string(),
        },
        // No digest ratified: the commit-level claim is the strongest available.
        // Callers surface this as the weaker claim it is.
        (None, _) => DeployVerdict::Current,
    }
}

/// Does the manifest support a full **artifact**-level claim, or only the
/// weaker commit-level one? The operator surface renders the difference so a
/// commit-only `current` is never read as "these are the ratified bytes".
pub fn is_artifact_pinned(manifest: Option<&RatifiedManifest>) -> bool {
    manifest.map(|m| m.ratified_binary_sha256.is_some()).unwrap_or(false)
}

/// SHA-256 of the **executing image**. On Linux `/proc/self/exe` resolves to
/// the running inode even after the file at that path has been replaced or
/// unlinked, which is exactly what this needs: the bytes in memory, not the
/// bytes someone has since staged. Falls back to `current_exe` elsewhere.
pub fn running_image_sha256() -> Option<String> {
    let proc_self = Path::new("/proc/self/exe");
    if proc_self.exists() {
        if let Some(d) = file_sha256(proc_self) {
            return Some(d);
        }
    }
    std::env::current_exe().ok().as_deref().and_then(file_sha256)
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

fn short(s: &str) -> String {
    s.chars().take(12).collect()
}

#[cfg(test)]
pub(super) mod tests {
    use super::*;

    // Full 40-hex commit ids. SHA_A and SHA_PREFIX_TWIN deliberately share the
    // first 7 characters — the abbreviation a human would type — and are
    // otherwise distinct, which is the pair the prefix-identity test needs.
    // Their LENGTH is asserted in that test: SHA_PREFIX_TWIN was 39 characters
    // for as long as nothing checked, which is precisely how a fixture stops
    // being able to reach the state it names.
    pub(super) const SHA_A: &str = "abcdef1234567890abcdef1234567890abcdef12";
    pub(super) const SHA_B: &str = "feedface00000000feedface00000000feedface";
    pub(super) const SHA_PREFIX_TWIN: &str = "abcdef1999999999999999999999999999999999";

    pub(super) fn build_clean_at(sha: &'static str) -> BuildInfo { build(sha, Provenance::Clean) }
    pub(super) fn build_dirty_at(sha: &'static str) -> BuildInfo { build(sha, Provenance::Dirty) }
    pub(super) fn build(sha: &'static str, prov: Provenance) -> BuildInfo {
        BuildInfo {
            version: "test",
            git_sha: sha,
            git_sha_short: "abcdef1",
            provenance: prov,
            built_at: "2026-08-13T00:00:00Z",
        }
    }

    pub(super) fn manifest(sha: &str) -> RatifiedManifest {
        RatifiedManifest {
            ratified_git_sha: sha.to_string(),
            ratified_binary_sha256: None,
            ratified_at: None,
            ratified_by: None,
        }
    }

    #[test]
    fn matching_clean_build_is_current() {
        let b = build(SHA_A, Provenance::Clean);
        assert_eq!(evaluate_running(&b, None, Some(&manifest(SHA_A))), DeployVerdict::Current);
    }

    /// **The parked-checkout case this module exists for.** The binary is
    /// clean, newer than merged source, and the process image matches the file
    /// — every currency arm passes — but it was built from a commit nobody
    /// ratified.
    #[test]
    fn a_clean_build_of_an_unratified_commit_is_stale() {
        let b = build(SHA_B, Provenance::Clean);
        let v = evaluate_running(&b, None, Some(&manifest(SHA_A)));
        assert!(matches!(v, DeployVerdict::Stale { .. }), "got {v:?}");
        assert!(v.detail().unwrap().contains("ratified"));
        assert!(!v.is_current());
    }

    /// A dirty tree is not the ratified artifact even when the commit matches:
    /// the binary is not any commit.
    #[test]
    fn a_dirty_build_is_stale_even_at_the_ratified_commit() {
        let b = build(SHA_A, Provenance::Dirty);
        let v = evaluate_running(&b, None, Some(&manifest(SHA_A)));
        assert!(matches!(v, DeployVerdict::Stale { .. }), "got {v:?}");
        assert!(v.detail().unwrap().contains("MODIFIED"));
    }

    /// Unknown provenance is NOT folded into clean — an unverified tree state
    /// is not an assertion that it was clean.
    #[test]
    fn unknown_provenance_is_unknown_not_current() {
        let b = build(SHA_A, Provenance::Unknown);
        let v = evaluate_running(&b, None, Some(&manifest(SHA_A)));
        assert!(matches!(v, DeployVerdict::Unknown { .. }), "got {v:?}");
        assert!(!v.is_current());
    }

    /// The two failure exits stay distinct: "nothing was ratified" needs a
    /// different human response from "this is not the ratified build".
    #[test]
    fn absent_manifest_is_unknown_not_stale_and_never_current() {
        let b = build(SHA_A, Provenance::Clean);
        let v = evaluate_running(&b, None, None);
        assert!(matches!(v, DeployVerdict::Unknown { .. }), "got {v:?}");
        assert!(!v.is_current(), "an unratified seat never reads as a pass");
    }

    #[test]
    fn a_build_with_no_commit_cannot_be_matched() {
        let b = build("unknown", Provenance::Clean);
        assert!(matches!(
            evaluate_running(&b, None, Some(&manifest(SHA_A))),
            DeployVerdict::Unknown { .. }
        ));
    }

    /// **Review finding (PR 708): a short sha is a locator, not an identity.**
    /// Its uniqueness changes as history grows, so accepting one would ratify
    /// any future commit sharing 28 bits of prefix. Abbreviations are refused
    /// at ADMISSION, which closes the question by construction — there is no
    /// shorter-operand case left for the comparison to have an opinion about.
    #[test]
    fn an_abbreviated_sha_is_refused_at_admission() {
        for short in ["abcdef1", "abcdef1234567890", &SHA_A[..39]] {
            let m = RatifiedManifest {
                ratified_git_sha: short.to_string(),
                ratified_binary_sha256: None, ratified_at: None, ratified_by: None,
            };
            let e = m.validate().expect_err(&format!("{short} must be refused"));
            assert!(e.to_string().contains("full 40"), "{e}");
        }
        // ...and the full one is admitted.
        assert!(manifest(SHA_A).validate().is_ok());
    }

    /// The prefix-twin risk is closed at ADMISSION, not at comparison — and this
    /// test drives the abbreviation on the side the defect actually lived on.
    ///
    /// `SHA_A` and `SHA_PREFIX_TWIN` are distinct full commits sharing 7 hex
    /// characters. The vulnerable shape compared `min(len_a, len_b)` characters,
    /// so a manifest holding the 7-char *abbreviation* matched BOTH commits and
    /// made them interchangeable. Refusing the abbreviation at admission removes
    /// the shorter operand, so the comparison never gets an opinion.
    ///
    /// The earlier form of this test pinned the manifest at a full 40 and varied
    /// only the build, which left `n == 40` and made both implementations agree —
    /// it passed on the vulnerable code and discriminated nothing. The fixture is
    /// now asserted to reach the state it names before anything is tested.
    #[test]
    fn a_prefix_shared_by_two_commits_is_refused_on_the_manifest_side() {
        for (name, sha) in [("SHA_A", SHA_A), ("SHA_B", SHA_B), ("SHA_PREFIX_TWIN", SHA_PREFIX_TWIN)] {
            assert_eq!(sha.len(), 40, "{name} must be a full 40-hex commit id, got {}", sha.len());
            assert!(sha.chars().all(|c| c.is_ascii_hexdigit()), "{name} must be hex");
        }
        assert_eq!(&SHA_A[..7], &SHA_PREFIX_TWIN[..7], "the fixture must actually collide");
        assert_ne!(SHA_A, SHA_PREFIX_TWIN);

        // Discriminating: the colliding prefix cannot be admitted as a manifest.
        // On the vulnerable shape this validates, and the twin then reads Current.
        let abbreviated = manifest(&SHA_A[..7]);
        assert!(abbreviated.validate().is_err(),
            "a manifest holding a prefix shared by two commits must be refused at admission");

        // And with a properly-admitted full manifest the twin is plainly stale.
        let v = evaluate_running(&build(SHA_PREFIX_TWIN, Provenance::Clean), None, Some(&manifest(SHA_A)));
        assert!(matches!(v, DeployVerdict::Stale { .. }),
            "a prefix twin must not read as the ratified commit: {v:?}");
        assert!(!v.is_current());
    }

    #[test]
    fn staged_artifact_is_checked_before_it_runs() {
        let mut m = manifest(SHA_A);
        m.ratified_binary_sha256 = Some("aa".repeat(32));
        assert_eq!(evaluate_staged(Some(&"aa".repeat(32)), Some(&m)), DeployVerdict::Current);
        let v = evaluate_staged(Some(&"bb".repeat(32)), Some(&m));
        assert!(matches!(v, DeployVerdict::Stale { .. }), "got {v:?}");
        assert!(v.detail().unwrap().contains("next restart"),
            "the operator is told what the consequence is");
        // Unreadable artifact, and a manifest with no digest, are both unknown.
        assert!(matches!(evaluate_staged(None, Some(&m)), DeployVerdict::Unknown { .. }));
        let no_digest = manifest(SHA_A);
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
        std::fs::write(&good, format!(r#"{{"ratified_git_sha":"{SHA_A}","ratified_by":"dp"}}"#).as_bytes()).unwrap();
        let m = RatifiedManifest::read(&good).unwrap().expect("parsed");
        assert_eq!(m.ratified_git_sha, SHA_A);
        assert_eq!(m.ratified_by.as_deref(), Some("dp"));
    }
}

#[cfg(test)]
mod artifact_identity_tests {
    use super::*;
    use super::tests::*;

    /// **The review finding (PR 708).** Same commit does NOT mean same
    /// executable: a different toolchain, different feature flags, or an
    /// outright substitution all preserve the commit while changing the bytes.
    /// When the manifest pins a digest, the digest decides.
    #[test]
    fn same_commit_different_bytes_is_stale() {
        let b = build_clean_at(SHA_A);
        let mut m = manifest(SHA_A);
        m.ratified_binary_sha256 = Some("aa".repeat(32));

        // The ratified artifact: current.
        assert_eq!(evaluate_running(&b, Some(&"aa".repeat(32)), Some(&m)), DeployVerdict::Current);

        // A different build of the SAME commit: stale, and the operator is told
        // why a matching commit is not a match.
        let v = evaluate_running(&b, Some(&"bb".repeat(32)), Some(&m));
        assert!(matches!(v, DeployVerdict::Stale { .. }), "got {v:?}");
        // Single arm, deliberately: the previous two-arm `||` had an unreachable
        // first arm (it matched raw source whitespace that `\`-continuation
        // removes at runtime), so it checked one property while looking like it
        // checked two.
        let why = v.detail().unwrap();
        assert!(why.contains("different bytes"), "reason names the distinction: {why:?}");
        assert!(why.contains("same commit"), "and names what is NOT the difference: {why:?}");
        assert!(!v.is_current());
    }

    /// A pinned digest that cannot be checked is UNKNOWN, never a pass — the
    /// authoritative comparison did not happen.
    #[test]
    fn pinned_digest_with_unreadable_image_is_unknown() {
        let b = build_clean_at(SHA_A);
        let mut m = manifest(SHA_A);
        m.ratified_binary_sha256 = Some("aa".repeat(32));
        let v = evaluate_running(&b, None, Some(&m));
        assert!(matches!(v, DeployVerdict::Unknown { .. }), "got {v:?}");
        assert!(!v.is_current());
    }

    /// Without a pinned digest the commit-level claim is all there is. It may
    /// read `current`, but callers must be able to tell it apart from a full
    /// artifact match — hence `is_artifact_pinned`.
    #[test]
    fn commit_only_ratification_is_marked_as_the_weaker_claim() {
        let b = build_clean_at(SHA_A);
        let m = manifest(SHA_A);
        assert_eq!(evaluate_running(&b, Some(&"cc".repeat(32)), Some(&m)), DeployVerdict::Current);
        assert!(!is_artifact_pinned(Some(&m)), "commit-only ratification is distinguishable");
        let mut pinned = m.clone();
        pinned.ratified_binary_sha256 = Some("cc".repeat(32));
        assert!(is_artifact_pinned(Some(&pinned)));
        assert!(!is_artifact_pinned(None));
    }

    /// The artifact check does not rescue a wrong commit or a dirty tree —
    /// those are decided before it and stay decided.
    #[test]
    fn artifact_match_cannot_launder_a_wrong_commit_or_dirty_tree() {
        let mut m = manifest(SHA_A);
        m.ratified_binary_sha256 = Some("aa".repeat(32));
        let wrong_commit = build_clean_at(SHA_B);
        assert!(matches!(
            evaluate_running(&wrong_commit, Some(&"aa".repeat(32)), Some(&m)),
            DeployVerdict::Stale { .. }));
        let dirty = build_dirty_at(SHA_A);
        assert!(matches!(
            evaluate_running(&dirty, Some(&"aa".repeat(32)), Some(&m)),
            DeployVerdict::Stale { .. }));
    }
}

#[cfg(test)]
mod malformed_manifest_tests {
    use super::*;
    use super::tests::*;

    /// **The blocking review finding (PR 708), as a regression.** The manifest
    /// is operator-supplied JSON from a principal this module deliberately does
    /// NOT trust, and the old comparison byte-sliced it:
    /// `a[..n]` where `n = a.len().min(b.len())`. A multi-byte character
    /// straddling byte 40 is not a char boundary, so a manifest of
    /// `"aééé…"` panicked — inside `/admin`, the very surface that reports the
    /// ratification verdict, taking the page down.
    ///
    /// Second time this exact shape shipped in this sprint (the degraded-log
    /// truncation was the first), which is why the fix is structural: validate
    /// at admission so no non-hex string ever reaches a comparison, rather than
    /// making one comparison site multibyte-safe.
    #[test]
    fn a_non_ascii_sha_yields_a_verdict_not_a_panic() {
        let dir = std::env::temp_dir().join(format!("hub-ratified-mb-{}", uuid::Uuid::new_v4()));
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join("m.json");
        // 41 bytes / 21 chars — byte 40 lands inside the final 'é'.
        let payload = format!("a{}", "é".repeat(20));
        assert_eq!(payload.len(), 41);
        assert!(!payload.is_char_boundary(40), "fixture must straddle byte 40");
        std::fs::write(&path, format!(r#"{{"ratified_git_sha":"{payload}"}}"#)).unwrap();

        // Admission refuses it — the same fail-closed exit as any other
        // malformed record, reached without a comparison.
        let err = RatifiedManifest::read(&path).expect_err("a non-hex sha is malformed");
        assert!(err.to_string().contains("full 40"), "{err}");

        // And the evaluation path is unreachable-by-construction for such a
        // record; called directly with one anyway, it still returns a verdict.
        let m = RatifiedManifest {
            ratified_git_sha: payload,
            ratified_binary_sha256: None, ratified_at: None, ratified_by: None,
        };
        let v = evaluate_running(&build(SHA_A, Provenance::Clean), None, Some(&m));
        assert!(matches!(v, DeployVerdict::Stale { .. }), "verdict, not panic: {v:?}");
        assert!(!v.is_current());
    }

    /// The same class on the other operator-supplied field.
    #[test]
    fn a_malformed_binary_digest_is_refused_at_admission() {
        for bad in ["nothex", &"a".repeat(63), &"é".repeat(32)] {
            let m = RatifiedManifest {
                ratified_git_sha: SHA_A.to_string(),
                ratified_binary_sha256: Some(bad.to_string()),
                ratified_at: None, ratified_by: None,
            };
            assert!(m.validate().is_err(), "{bad:?} must be refused");
        }
        let ok = RatifiedManifest {
            ratified_git_sha: SHA_A.to_string(),
            ratified_binary_sha256: Some("ab".repeat(32)),
            ratified_at: None, ratified_by: None,
        };
        assert!(ok.validate().is_ok());
    }
}
