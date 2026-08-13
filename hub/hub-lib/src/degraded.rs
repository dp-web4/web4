//! Degraded-event recording — Sprint F0.1 / PRD_HUB_V2_FEDERATED R7a.
//!
//! When the hub's signing/referee dependencies fail, that fact must be
//! **recorded**, append-only, and **distinguishable from member conduct**
//! (the measured fleet failure this prevents: infrastructure fail-closed
//! denies scored as conduct — hestia PR #357 class). The recorder cannot be
//! the witnessed ledger itself, because the signer is frequently the
//! unreachable thing: a witnessed `DegradedRecorded` event would need the
//! very signature that just failed. So the mechanism is the fleet's ratified
//! pattern (hestia PRD_GATE_CONSOLIDATION criterion 9c): a **local
//! append-only JSONL diagnostic log** — the fallback witness precisely when
//! the normal witness is the unreachable thing — reconciled into one
//! witnessed [`crate::events::HubEvent::DegradedReconciled`] entry when
//! signing capability returns.
//!
//! **Reconciliation is opportunistic, not ignition-only.** It runs at ignition
//! AND after any successful signed append while entries are pending, so a
//! dependency that recovers on a LIVE hub (a callback coming back, a peer
//! reachable again) is folded in immediately. A hub can run for weeks between
//! ignitions; a record that waits that long is not one anyone can act on.
//!
//! Design properties:
//! - **Best-effort, never load-bearing for serving**: an `append` that cannot
//!   write logs an error and returns; it never panics and never blocks the
//!   request path on anything slower than a local file append.
//! - **Append-only**: the file is opened `O_APPEND`; `drain` (reconciliation)
//!   is the only truncation, and it happens under the same lock as appends,
//!   after the drained bytes have been captured and digested.
//! - **No secrets**: `context` is a bounded operator-facing string (operation
//!   + error text), never key material or payload bytes.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use web4_core::crypto::sha256_hex;

/// Why the hub was degraded for one call. Every variant is an infrastructure
/// fact by construction — there is deliberately no conduct-shaped variant.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum DegradedSource {
    /// The vault is sealed (`LockedSigner`) — a signing act was refused
    /// because the hub has no signing capability, not because policy said no.
    LockedRefusal,
    /// The remote signer (hestia callback / HSM) did not answer (transport).
    SignerUnreachable,
    /// A federation peer did not answer. Forward slot for R1; unused until
    /// federation edges exist.
    PeerUnreachable,
    /// A law-gate / referee round-trip timed out.
    GateTimeout,
}

impl DegradedSource {
    /// Stable snake_case token used in reconciliation summaries.
    pub fn token(&self) -> &'static str {
        match self {
            DegradedSource::LockedRefusal => "locked_refusal",
            DegradedSource::SignerUnreachable => "signer_unreachable",
            DegradedSource::PeerUnreachable => "peer_unreachable",
            DegradedSource::GateTimeout => "gate_timeout",
        }
    }
}

/// One degraded event, as persisted to the diagnostic log (one JSON object
/// per line).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DegradedEntry {
    pub source: DegradedSource,
    pub ts: DateTime<Utc>,
    /// Bounded, operator-facing context: what was attempted and what failed.
    pub context: String,
}

/// Maximum stored context length — a transport error carrying a huge body
/// must not bloat the diagnostic log.
const MAX_CONTEXT: usize = 400;

/// The result of draining the log for reconciliation: everything a
/// `DegradedReconciled` ledger event needs.
#[derive(Clone, Debug)]
pub struct DrainSummary {
    pub count: u32,
    pub first_ts: DateTime<Utc>,
    pub last_ts: DateTime<Utc>,
    /// SHA-256 hex over the exact drained JSONL bytes, binding the local log
    /// content to the witnessed reconciliation event.
    pub entries_digest: String,
    /// Per-source counts, keyed by [`DegradedSource::token`].
    pub by_source: BTreeMap<String, u32>,
}

/// Append-only JSONL diagnostic log for degraded events.
pub struct DegradedLog {
    path: PathBuf,
    lock: std::sync::Mutex<()>,
    /// Cheap "something is pending" flag so the reconciliation hook on the
    /// witness path costs an atomic load, not a file read, in the common case
    /// (nothing degraded). Set on append; cleared only when a commit leaves
    /// the file empty.
    dirty: AtomicBool,
    /// Re-entrancy + concurrency guard. Reconciliation witnesses a ledger
    /// event, and the witness path itself triggers reconciliation — without
    /// this, that recurses. It also collapses concurrent attempts, so two
    /// signing acts finishing together cannot both witness the same window.
    reconciling: AtomicBool,
}

impl DegradedLog {
    /// A log at `path`. The file is created lazily on first append; a missing
    /// file reads as empty.
    pub fn new(path: impl Into<PathBuf>) -> Self {
        let path = path.into();
        // A log left behind by a previous process still needs reconciling.
        let dirty = std::fs::metadata(&path).map(|m| m.len() > 0).unwrap_or(false);
        Self {
            path,
            lock: std::sync::Mutex::new(()),
            dirty: AtomicBool::new(dirty),
            reconciling: AtomicBool::new(false),
        }
    }

    /// Is there anything to reconcile? An atomic load — safe to call on the
    /// witness path for every event.
    pub fn has_pending(&self) -> bool {
        self.dirty.load(Ordering::Acquire)
    }

    /// Claim the reconciliation slot. `false` = another reconciliation is in
    /// flight (or this call is re-entering from inside one); the caller must
    /// do nothing. Pair every `true` with [`Self::end_reconcile`].
    pub fn try_begin_reconcile(&self) -> bool {
        self.reconciling
            .compare_exchange(false, true, Ordering::AcqRel, Ordering::Acquire)
            .is_ok()
    }

    /// Release the reconciliation slot.
    pub fn end_reconcile(&self) {
        self.reconciling.store(false, Ordering::Release);
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    /// Record one degraded event. Best-effort: failures to write are logged
    /// via `tracing::error!` and swallowed — the serving path never fails
    /// because its diagnostic log did.
    pub fn append(&self, source: DegradedSource, context: &str) {
        let mut ctx = context.to_string();
        if ctx.len() > MAX_CONTEXT {
            // Walk DOWN to a char boundary before truncating. `String::truncate`
            // panics when the split lands mid-codepoint, and this input is
            // attacker-shaped: the context is `format!("{op}: {msg}")` over a
            // `SignError::Transport` payload — a peer error body or a non-ASCII
            // hostname. A single leading ASCII byte shifts every following
            // multibyte character across byte 400. A panic here would fire
            // inside the signer's error path, i.e. exactly during the degraded
            // window this module exists to record: the record would be lost and
            // the caller would unwind 500 instead of receiving its `SignError`,
            // inverting this module's stated best-effort invariant.
            let mut cut = MAX_CONTEXT;
            while cut > 0 && !ctx.is_char_boundary(cut) {
                cut -= 1;
            }
            ctx.truncate(cut);
            ctx.push('…');
        }
        let entry = DegradedEntry { source, ts: Utc::now(), context: ctx };
        let line = match serde_json::to_string(&entry) {
            Ok(l) => l,
            Err(e) => {
                tracing::error!("degraded-log serialize failed: {e}");
                return;
            }
        };
        let _guard = self.lock.lock().expect("degraded log lock poisoned");
        let res = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)
            .and_then(|mut f| writeln!(f, "{line}"));
        match res {
            Ok(()) => self.dirty.store(true, Ordering::Release),
            Err(e) => tracing::error!(
                "degraded-log append failed at {}: {e}", self.path.display()),
        }
    }

    /// Read all entries without consuming them. Malformed lines are skipped
    /// (counted via `tracing::warn!`), never fatal: a torn final line from a
    /// crash must not brick reconciliation.
    pub fn read_all(&self) -> Vec<DegradedEntry> {
        let _guard = self.lock.lock().expect("degraded log lock poisoned");
        self.read_unlocked().0
    }

    fn read_unlocked(&self) -> (Vec<DegradedEntry>, Vec<u8>) {
        let bytes = std::fs::read(&self.path).unwrap_or_default();
        let mut out = Vec::new();
        for line in bytes.split(|b| *b == b'\n') {
            if line.is_empty() {
                continue;
            }
            match serde_json::from_slice::<DegradedEntry>(line) {
                Ok(e) => out.push(e),
                Err(e) => tracing::warn!("degraded-log skipping malformed line: {e}"),
            }
        }
        (out, bytes)
    }

    /// Number of readable entries (operator surface).
    pub fn len(&self) -> usize {
        self.read_all().len()
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Phase 1 of reconciliation: capture + digest the current contents
    /// WITHOUT consuming them. Returns `None` when there is nothing to
    /// reconcile. The caller witnesses the summary to the ledger and, only on
    /// success, calls [`Self::commit_reconciled`] — so a failed witness loses
    /// nothing (the entries re-report on the next snapshot, with the same
    /// digest, which is auditable duplication rather than silent loss).
    pub fn snapshot(&self) -> Option<Snapshot> {
        let _guard = self.lock.lock().expect("degraded log lock poisoned");
        let (entries, bytes) = self.read_unlocked();
        if entries.is_empty() {
            return None;
        }
        let digest = sha256_hex(&bytes);
        let mut by_source: BTreeMap<String, u32> = BTreeMap::new();
        for e in &entries {
            *by_source.entry(e.source.token().to_string()).or_insert(0) += 1;
        }
        Some(Snapshot {
            summary: DrainSummary {
                count: entries.len() as u32,
                first_ts: entries.first().expect("non-empty").ts,
                last_ts: entries.last().expect("non-empty").ts,
                entries_digest: digest,
                by_source,
            },
            byte_len: bytes.len(),
        })
    }

    /// Phase 2: remove exactly the bytes the snapshot summarized (now
    /// witnessed), preserving any entries appended since the snapshot was
    /// taken. Runs under the append lock, so nothing lands between the read
    /// and the rewrite.
    pub fn commit_reconciled(&self, snap: &Snapshot) {
        let _guard = self.lock.lock().expect("degraded log lock poisoned");
        let bytes = std::fs::read(&self.path).unwrap_or_default();
        let tail: &[u8] = if bytes.len() >= snap.byte_len {
            &bytes[snap.byte_len..]
        } else {
            // The file shrank underneath us (external interference). The
            // witnessed summary stands; start clean rather than guess.
            tracing::warn!(
                "degraded-log at {} shorter than reconciled snapshot — clearing",
                self.path.display()
            );
            b""
        };
        let remaining = tail.len();
        if let Err(e) = std::fs::write(&self.path, tail) {
            tracing::error!("degraded-log commit failed at {}: {e}", self.path.display());
            // Write failed: entries stand, so the log stays dirty.
            return;
        }
        // Entries appended after the snapshot survive the commit and still need
        // reconciling — clear the flag only when nothing is left.
        self.dirty.store(remaining > 0, Ordering::Release);
    }
}

/// A captured, digested view of the log pending witness — see
/// [`DegradedLog::snapshot`] / [`DegradedLog::commit_reconciled`].
#[derive(Clone, Debug)]
pub struct Snapshot {
    pub summary: DrainSummary,
    byte_len: usize,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn tmp_log(name: &str) -> DegradedLog {
        let dir = std::env::temp_dir().join("hub-degraded-tests");
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join(format!("{name}-{}.jsonl", uuid::Uuid::new_v4()));
        DegradedLog::new(path)
    }

    #[test]
    fn append_read_roundtrip() {
        let log = tmp_log("roundtrip");
        log.append(DegradedSource::SignerUnreachable, "sign member_admit: connect refused");
        log.append(DegradedSource::LockedRefusal, "sign law_amend: vault locked");
        let entries = log.read_all();
        assert_eq!(entries.len(), 2);
        assert_eq!(entries[0].source, DegradedSource::SignerUnreachable);
        assert_eq!(entries[1].source, DegradedSource::LockedRefusal);
    }

    #[test]
    fn snapshot_then_commit_reconciles() {
        let log = tmp_log("snapshot");
        log.append(DegradedSource::SignerUnreachable, "a");
        log.append(DegradedSource::SignerUnreachable, "b");
        log.append(DegradedSource::GateTimeout, "c");
        let snap = log.snapshot().expect("snapshot");
        assert_eq!(snap.summary.count, 3);
        assert_eq!(snap.summary.by_source.get("signer_unreachable"), Some(&2));
        assert_eq!(snap.summary.by_source.get("gate_timeout"), Some(&1));
        assert_eq!(snap.summary.entries_digest.len(), 64);
        // Snapshot does NOT consume — a failed witness loses nothing.
        assert_eq!(log.read_all().len(), 3);
        log.commit_reconciled(&snap);
        assert!(log.is_empty(), "commit must remove the reconciled bytes");
        assert!(log.snapshot().is_none(), "empty log has nothing to reconcile");
    }

    #[test]
    fn commit_preserves_entries_appended_after_snapshot() {
        let log = tmp_log("tail");
        log.append(DegradedSource::LockedRefusal, "before");
        let snap = log.snapshot().expect("snapshot");
        log.append(DegradedSource::GateTimeout, "after");
        log.commit_reconciled(&snap);
        let remaining = log.read_all();
        assert_eq!(remaining.len(), 1, "post-snapshot entry must survive commit");
        assert_eq!(remaining[0].source, DegradedSource::GateTimeout);
    }

    #[test]
    fn malformed_line_is_skipped_not_fatal() {
        let log = tmp_log("malformed");
        log.append(DegradedSource::LockedRefusal, "good");
        {
            let mut f = std::fs::OpenOptions::new().append(true).open(log.path()).unwrap();
            writeln!(f, "{{torn line").unwrap();
        }
        log.append(DegradedSource::GateTimeout, "also good");
        let entries = log.read_all();
        assert_eq!(entries.len(), 2, "torn line skipped, valid lines kept");
    }

    #[test]
    fn context_is_bounded() {
        let log = tmp_log("bounded");
        log.append(DegradedSource::SignerUnreachable, &"x".repeat(10_000));
        let entries = log.read_all();
        assert!(entries[0].context.len() <= MAX_CONTEXT + 4);
    }

    /// Regression: a multibyte character STRADDLING the truncation boundary.
    /// The all-ASCII bound test above cannot see this — every ASCII byte is a
    /// char boundary, so it never exercises the walk. One leading ASCII byte is
    /// all it takes to shift every following 2-byte character across byte 400,
    /// and `String::truncate` panics on a non-boundary split.
    #[test]
    fn context_truncation_survives_a_straddling_multibyte_char() {
        let log = tmp_log("multibyte");
        // 1 + 600 bytes; byte 400 lands mid-'é' (the exact shape reproduced in
        // review: `assertion failed: self.is_char_boundary(new_len)`, exit 101).
        let payload = format!("a{}", "é".repeat(300));
        assert!(!payload.is_char_boundary(MAX_CONTEXT), "the test input must straddle");
        log.append(DegradedSource::SignerUnreachable, &payload);
        let entries = log.read_all();
        assert_eq!(entries.len(), 1, "the degraded record survives, not panics");
        assert!(entries[0].context.ends_with('…'), "truncation marker retained");

        // Non-Latin scripts (3-byte chars) and emoji (4-byte, plus ZWJ
        // sequences) exercise different walk depths.
        for payload in [
            format!("ab{}", "日".repeat(200)),
            format!("abc{}", "🔒".repeat(150)),
        ] {
            log.append(DegradedSource::GateTimeout, &payload);
        }
        let all = log.read_all();
        assert_eq!(all.len(), 3, "every multibyte shape recorded");
        for e in &all {
            assert!(e.context.len() <= MAX_CONTEXT + 4, "still bounded");
        }
    }
}
