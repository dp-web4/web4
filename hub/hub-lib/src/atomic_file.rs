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
    let path = path.as_ref();
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

    let mut f = std::fs::File::create(&tmp)
        .with_context(|| format!("creating temp file {}", tmp.display()))?;
    f.write_all(contents.as_ref())
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
