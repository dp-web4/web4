//! Atomic whole-file writes.
//!
//! `std::fs::write` truncates the target and then fills it. Two consequences,
//! and the second is the one that bites:
//!
//! 1. A concurrent reader can observe a half-written file (a *torn read*).
//! 2. A crash or a failed write mid-way leaves the file truncated **on disk**.
//!    A torn read heals on the next successful write; a truncated config does
//!    not. It is durable corruption of a file something needs in order to boot.
//!
//! Writing to a unique temp file in the same directory and `rename(2)`-ing it
//! over the target fixes both: `rename` is atomic with respect to readers, so a
//! reader sees either the entire old file or the entire new one, never a splice.
//!
//! ## What this does NOT do
//!
//! **It does not serialize writers.** Two processes that read-modify-write the
//! same file still lose one of the updates — the second `rename` simply wins,
//! and the loser gets no error. Atomicity and mutual exclusion are different
//! properties and a single call cannot supply both. Measured on this shape:
//! tmp+rename removed 1493/1500 torn reads and 0% of lost updates (two RMW
//! writers lost one hook in 80/80 trials, replicated on three kernels and four
//! filesystems).
//!
//! So: if a file is read-modify-written by **≥2 independent processes**, this
//! helper is necessary and not sufficient — it also needs a lock. Two warnings
//! for whoever writes that lock, both of them measured rather than reasoned:
//!
//! - Lock a **sidecar** path (`foo.json.lock`), never the target file. `rename`
//!   installs a *new inode* and an `flock` lives on the inode, not the path, so
//!   a process that opens the target after a swap locks a different object than
//!   the holder and both enter the critical section believing they hold it.
//!   Exclusion was void in 200/200 trials once the second writer started ≥1ms
//!   after the first, and with three writers that cost 46/100 lost updates.
//! - That defect is **invisible to outcome testing**: the same runs show 0 lost
//!   updates for two writers at every stagger. Only a structural check (did the
//!   two processes lock two distinct inodes?) detects it.
//!
//! Evidence and harnesses: `shared-context/explorations/supervisor-scope-2026-07-31/`.

use anyhow::{Context, Result};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

/// Distinguishes temp files created by concurrent `write_atomic` calls in this
/// process. Combined with the pid it makes the temp name unique across the box,
/// which a fixed `foo.json.tmp` is not — two writers of the same target would
/// otherwise share a temp path and splice each other's bytes.
static SEQ: AtomicU64 = AtomicU64::new(0);

/// Removes the temp file if we leave before the rename succeeds.
struct TmpGuard(Option<PathBuf>);

impl TmpGuard {
    fn disarm(&mut self) {
        self.0 = None;
    }
}

impl Drop for TmpGuard {
    fn drop(&mut self) {
        if let Some(p) = self.0.take() {
            let _ = std::fs::remove_file(p);
        }
    }
}

/// Write `contents` to `path` atomically: unique temp file in the same
/// directory, `fsync`, then `rename` over the target.
///
/// The parent directory is created if missing. The temp file must live in the
/// same directory as the target — `rename` is only atomic within a filesystem.
///
/// This serializes nothing; see the module docs before using it on a file that
/// more than one process read-modify-writes.
pub fn write_atomic(path: impl AsRef<Path>, contents: impl AsRef<[u8]>) -> Result<()> {
    write_inner(path.as_ref(), contents.as_ref(), None)
}

/// [`write_atomic`], but the file is **created** with `mode` (unix only; the
/// mode is ignored elsewhere).
///
/// Use this for anything secret. Writing first and `chmod`-ing after leaves the
/// file world-readable for the interval in between, which is a window an
/// attacker on the box can lose a race to but does not have to win twice — the
/// operator token was written that way, under a doc comment claiming it was
/// not. Here the mode is on the `open(2)`, so the bytes are never visible at
/// 0644, and it is re-asserted after the write so a stale temp file left by a
/// crashed predecessor cannot donate its permissions.
pub fn write_atomic_mode(
    path: impl AsRef<Path>,
    contents: impl AsRef<[u8]>,
    mode: u32,
) -> Result<()> {
    write_inner(path.as_ref(), contents.as_ref(), Some(mode))
}

fn write_inner(path: &Path, contents: &[u8], mode: Option<u32>) -> Result<()> {
    #[cfg(not(unix))]
    let _ = mode;
    let dir = path.parent().unwrap_or_else(|| Path::new("."));
    std::fs::create_dir_all(dir)
        .with_context(|| format!("creating parent dir {}", dir.display()))?;

    let stem = path
        .file_name()
        .map(|s| s.to_string_lossy().into_owned())
        .unwrap_or_else(|| "file".to_string());
    let tmp = dir.join(format!(
        ".{}.{}.{}.tmp",
        stem,
        std::process::id(),
        SEQ.fetch_add(1, Ordering::Relaxed)
    ));

    let mut guard = TmpGuard(Some(tmp.clone()));

    let mut opts = std::fs::OpenOptions::new();
    opts.write(true).create(true).truncate(true);
    #[cfg(unix)]
    if let Some(m) = mode {
        use std::os::unix::fs::OpenOptionsExt;
        opts.mode(m);
    }
    let mut f = opts
        .open(&tmp)
        .with_context(|| format!("creating temp file {}", tmp.display()))?;
    #[cfg(unix)]
    if let Some(m) = mode {
        // `opts.mode()` only takes effect when the open actually creates the
        // file. Re-assert it so a leftover temp from a crashed run with a
        // recycled pid cannot hand us its looser permissions.
        use std::os::unix::fs::PermissionsExt;
        f.set_permissions(std::fs::Permissions::from_mode(m))
            .with_context(|| format!("setting mode on temp file {}", tmp.display()))?;
    }
    f.write_all(contents)
        .with_context(|| format!("writing temp file {}", tmp.display()))?;
    // Without this the rename can become visible while the bytes are not, which
    // reintroduces exactly the durable-truncation failure we are here to remove.
    f.sync_all()
        .with_context(|| format!("syncing temp file {}", tmp.display()))?;
    drop(f);

    std::fs::rename(&tmp, path)
        .with_context(|| format!("installing {} -> {}", tmp.display(), path.display()))?;
    guard.disarm();

    // The directory entry itself is not fsynced. That is deliberate: a crash
    // between the rename and the directory flush leaves the OLD file intact,
    // which is the safe direction to fail in, and config writes are frequent
    // enough that a per-write directory sync is a poor trade.
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn writes_contents_and_leaves_no_temp_behind() {
        let d = tempfile::tempdir().unwrap();
        let p = d.path().join("cfg.json");
        write_atomic(&p, b"{\"a\":1}").unwrap();
        assert_eq!(std::fs::read_to_string(&p).unwrap(), "{\"a\":1}");

        let strays: Vec<_> = std::fs::read_dir(d.path())
            .unwrap()
            .map(|e| e.unwrap().file_name().to_string_lossy().into_owned())
            .filter(|n| n.ends_with(".tmp"))
            .collect();
        assert!(strays.is_empty(), "temp files left behind: {strays:?}");
    }

    #[test]
    fn creates_missing_parent_directories() {
        let d = tempfile::tempdir().unwrap();
        let p = d.path().join("a").join("b").join("cfg.json");
        write_atomic(&p, b"hi").unwrap();
        assert_eq!(std::fs::read_to_string(&p).unwrap(), "hi");
    }

    #[test]
    fn overwrites_existing_file_wholesale() {
        let d = tempfile::tempdir().unwrap();
        let p = d.path().join("cfg.json");
        write_atomic(&p, b"aaaaaaaaaaaaaaaaaaaa").unwrap();
        write_atomic(&p, b"bb").unwrap();
        // Not "bbaaaaaaaaaaaaaaaaaa" — the rename replaces, it does not overlay.
        assert_eq!(std::fs::read_to_string(&p).unwrap(), "bb");
    }

    /// The regression this helper exists to prevent: a *fixed* temp name (the
    /// `path.with_extension("json.tmp")` pattern) lets two concurrent writers of
    /// the same target share one temp file and interleave their bytes. With
    /// unique temp names each writer's content lands whole; one of them wins and
    /// the reader never sees a mixture.
    #[test]
    fn concurrent_writers_never_splice_content() {
        let d = tempfile::tempdir().unwrap();
        let p = d.path().join("cfg.json");
        let a = "A".repeat(64 * 1024);
        let b = "B".repeat(64 * 1024);

        for _ in 0..20 {
            let (pa, pb) = (p.clone(), p.clone());
            let (ca, cb) = (a.clone(), b.clone());
            let h1 = std::thread::spawn(move || write_atomic(&pa, ca.as_bytes()).unwrap());
            let h2 = std::thread::spawn(move || write_atomic(&pb, cb.as_bytes()).unwrap());
            h1.join().unwrap();
            h2.join().unwrap();

            let got = std::fs::read_to_string(&p).unwrap();
            assert!(
                got == a || got == b,
                "spliced write: {} A's, {} B's",
                got.matches('A').count(),
                got.matches('B').count()
            );
        }
    }

    /// A secret written with `write_atomic_mode` is 0600 when it lands, and the
    /// temp file it came from was created 0600 too — the mode is an argument to
    /// the `open(2)`, so unlike a write-then-`chmod` there is no interval in
    /// which the bytes sit at 0644. This asserts the observable half (the final
    /// mode); the absence of the window is structural, from where the mode is
    /// applied, and is why the old `set_permissions`-after-write shape was
    /// replaced rather than kept.
    #[cfg(unix)]
    #[test]
    fn write_atomic_mode_lands_at_0600_and_leaves_no_stray() {
        use std::os::unix::fs::PermissionsExt;
        let d = tempfile::tempdir().unwrap();
        let p = d.path().join("operator.token");
        write_atomic_mode(&p, b"s3cret", 0o600).unwrap();

        assert_eq!(std::fs::read_to_string(&p).unwrap(), "s3cret");
        let mode = std::fs::metadata(&p).unwrap().permissions().mode() & 0o777;
        assert_eq!(mode, 0o600, "token landed at {mode:o}, want 600");

        let strays: Vec<_> = std::fs::read_dir(d.path())
            .unwrap()
            .map(|e| e.unwrap().file_name().to_string_lossy().into_owned())
            .filter(|n| n != "operator.token")
            .collect();
        assert!(strays.is_empty(), "left behind: {strays:?}");
    }

    /// Overwriting an existing 0644 file with a 0600 write must not inherit the
    /// old mode. It cannot here — the rename installs a *new* inode carrying
    /// the temp file's permissions — but that is precisely the kind of thing
    /// that silently regresses if someone "simplifies" this back to a write in
    /// place.
    #[cfg(unix)]
    #[test]
    fn write_atomic_mode_replaces_a_loose_existing_mode() {
        use std::os::unix::fs::PermissionsExt;
        let d = tempfile::tempdir().unwrap();
        let p = d.path().join("t");
        std::fs::write(&p, b"old").unwrap();
        std::fs::set_permissions(&p, std::fs::Permissions::from_mode(0o644)).unwrap();

        write_atomic_mode(&p, b"new", 0o600).unwrap();
        assert_eq!(
            std::fs::metadata(&p).unwrap().permissions().mode() & 0o777,
            0o600
        );
    }

    /// Atomicity is not exclusion. This documents the limit in an executable
    /// form so nobody reads `write_atomic` as a mutex: both writers read the
    /// same base, both write atomically, and one update is silently gone.
    #[test]
    fn does_not_serialize_read_modify_write() {
        let d = tempfile::tempdir().unwrap();
        let p = d.path().join("cfg.json");
        write_atomic(&p, b"base").unwrap();

        let base_a = std::fs::read_to_string(&p).unwrap();
        let base_b = std::fs::read_to_string(&p).unwrap();
        write_atomic(&p, format!("{base_a}+a").as_bytes()).unwrap();
        write_atomic(&p, format!("{base_b}+b").as_bytes()).unwrap();

        let got = std::fs::read_to_string(&p).unwrap();
        assert_eq!(got, "base+b");
        assert!(!got.contains("+a"), "if this ever passes, the docs above are wrong");
    }
}
