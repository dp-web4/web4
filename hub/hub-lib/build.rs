//! Stamps the build's own provenance into the binary, at the moment of production.
//!
//! Why this exists. Until now the only thing a `hub` binary could say about itself
//! was `CARGO_PKG_VERSION` — `0.1.0-alpha.0`, a hand-maintained string in the
//! workspace `Cargo.toml` whose last change was 2026-06-08, unchanged across every
//! `hub/` commit since. The running daemon published no build identity at all:
//! `/tools` lists one tool and `query_hub`'s payload carries no build field, so a
//! peer on the tailnet has no way to ask the hub what it is.
//!
//! The consequence is that "is the merged fix live?" has to be *reconstructed from
//! outside the process* — `/proc/<pid>/exe` inode identity plus binary mtime against
//! commit dates (`private-context/tools/hub_deploy_current.sh`). That reconstruction
//! has already failed open once: a binary with an mtime 11 days older than the newest
//! `hub/` commit read `VERDICT: CURRENT`, which is why that tool grew a third arm.
//!
//! The generator, named by Legion 2026-08-01
//! (`shared-context/forum/legion-five-records-name-the-raising-model-...`): provenance
//! encoded in a *name* rather than written down at the moment of production. A name
//! cannot be re-derived, cannot be checked against the run, and survives every change
//! to the thing it describes. A version constant and a file path are both names. This
//! script writes the record instead, so the artifact can be asked rather than inferred.
//!
//! Freshness, stated rather than assumed. `git_sha` is exact: the `rerun-if-changed`
//! entries below cover every way HEAD moves (detached, symbolic-ref tip, packed), so a
//! merge always re-stamps. `provenance` is weaker — cargo re-runs this script when git
//! metadata changes, and an edit that is neither committed nor staged does not touch
//! that metadata. So `provenance: clean` is a floor, not a ceiling: it can lag an
//! uncommitted working-tree edit made after the last stamp. It is not lagged across a
//! merge, which is the path deploy-currency actually checks. Source directories are
//! deliberately not watched — that would rebuild hub-lib on every hub-daemon edit, and
//! the field it would tighten is the secondary one.

use std::path::PathBuf;
use std::process::Command;

/// Run a git command; `None` means git was absent or the command failed.
/// An empty-but-successful stdout stays `Some("")` — for `git status` that is
/// the clean answer, and collapsing it into the failure case would report a
/// clean tree as unknown.
fn git(args: &[&str]) -> Option<String> {
    let out = Command::new("git").args(args).output().ok()?;
    if !out.status.success() {
        return None;
    }
    Some(String::from_utf8_lossy(&out.stdout).trim().to_string())
}

fn main() {
    println!("cargo:rerun-if-changed=build.rs");

    // Watch every file that can move HEAD. Without these, cargo caches this
    // script's output and a merge touching no hub-lib source would ship a binary
    // reporting the *previous* commit — the same drift this file exists to close,
    // one level down.
    if let Some(dir) = git(&["rev-parse", "--absolute-git-dir"]) {
        println!("cargo:rerun-if-changed={dir}/HEAD");
        println!("cargo:rerun-if-changed={dir}/index");
        println!("cargo:rerun-if-changed={dir}/packed-refs");
        // A symbolic HEAD's tip lives in a separate ref file. A commit on the
        // current branch leaves `HEAD` byte-identical, so watching only HEAD
        // misses the most common way the SHA changes.
        if let Ok(head) = std::fs::read_to_string(format!("{dir}/HEAD")) {
            if let Some(r) = head.strip_prefix("ref: ") {
                println!("cargo:rerun-if-changed={dir}/{}", r.trim());
            }
        }
    }

    let sha = git(&["rev-parse", "HEAD"]).filter(|s| !s.is_empty());
    let short = git(&["rev-parse", "--short", "HEAD"]).filter(|s| !s.is_empty());

    // Scope the dirty check to the hub workspace, not the whole monorepo: the
    // question is "does this binary correspond to hub/ at this SHA", and an
    // unrelated edit under web4-core/ is not an answer to it. build.rs runs with
    // CWD = the crate root, so the workspace root is this manifest's parent.
    let ws = std::env::var("CARGO_MANIFEST_DIR")
        .ok()
        .map(PathBuf::from)
        .and_then(|p| p.parent().map(PathBuf::from));

    // Untracked files are excluded: an untracked path is not in the build.
    let status = ws.as_ref().and_then(|w| {
        git(&[
            "status",
            "--porcelain",
            "--untracked-files=no",
            "--",
            &w.to_string_lossy(),
        ])
    });

    // Anything we could not establish is `unknown`, never `clean`. An
    // unverifiable provenance claim that defaults to "clean" is the fail-open
    // shape the fleet's ratified default rules out; a source tarball with no git
    // is honestly unknown, not honestly clean.
    let provenance = match (&sha, &status) {
        (Some(_), Some(s)) if s.is_empty() => "clean",
        (Some(_), Some(_)) => "dirty",
        _ => "unknown",
    };

    let sha = sha.unwrap_or_else(|| "unknown".to_string());
    let short = short.unwrap_or_else(|| "unknown".to_string());

    println!("cargo:rustc-env=HUB_BUILD_GIT_SHA={sha}");
    println!("cargo:rustc-env=HUB_BUILD_GIT_SHA_SHORT={short}");
    println!("cargo:rustc-env=HUB_BUILD_PROVENANCE={provenance}");
    println!(
        "cargo:rustc-env=HUB_BUILD_AT={}",
        chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, true)
    );
}
