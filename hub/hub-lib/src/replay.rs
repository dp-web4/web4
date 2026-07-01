// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Anti-replay guard for the sealed channel.
//!
//! The sealed channel authenticates via AEAD — only the holder of the pinned
//! key could have sealed a request. But AEAD proves *possession*, not
//! *freshness*: a captured `{pair_id, sealed}` POST decrypts identically on
//! re-submission. Without a seen-set, an observer positioned to capture the
//! ciphertext (a compromised relay, host-log access, or — in the open-community
//! future — any peer) can replay a captured **write** act (`referenced_act`,
//! `record_reputation`, `request_citizenship`, …) to double-witness it,
//! inflating the ledger and any reputation folded from it.
//!
//! This guard records a per-request key with a TTL and rejects a repeat within
//! the window. The key is an explicit client nonce when supplied, else the hash
//! of the sealed blob (so it works for every existing client with no wire
//! change). Paired with the caller-supplied `issued_at` freshness check in the
//! channel handler, the bounded TTL is *complete*: a replay must arrive inside
//! the freshness window to reach the set at all. Clients that don't yet send
//! `issued_at` still get burst-replay protection for the TTL duration.
//!
//! In-memory, per-process. Multi-replica hubs will want shared state — the same
//! caveat that already applies to [`crate::envelope::NonceStore`].

use chrono::{DateTime, Duration, Utc};
use std::collections::HashMap;
use std::sync::Mutex;

/// Default seen-key retention. Must be >= the channel freshness window so an
/// in-window replay is always still recorded when the duplicate arrives.
pub const DEFAULT_REPLAY_TTL_SECONDS: i64 = 300;

/// Flood backstop: hard cap on retained keys. A burst of *unique* requests
/// (each fresh, so none are replays) can't grow the map without bound between
/// prunes. On overflow we prune expired entries first, then evict the oldest.
const MAX_KEYS: usize = 100_000;

/// Records recently-seen channel-request keys to reject exact replays.
pub struct ReplayGuard {
    seen: Mutex<HashMap<String, DateTime<Utc>>>,
    ttl: Duration,
}

impl ReplayGuard {
    pub fn new() -> Self {
        Self::with_ttl(DEFAULT_REPLAY_TTL_SECONDS)
    }

    pub fn with_ttl(ttl_seconds: i64) -> Self {
        Self {
            seen: Mutex::new(HashMap::new()),
            ttl: Duration::seconds(ttl_seconds),
        }
    }

    /// Record `key` as seen at `now`. Returns `true` if it was fresh (accept),
    /// `false` if the same key was already seen within the TTL (replay → reject).
    ///
    /// The freshness comparison is explicit (`now - first < ttl`), so a stale
    /// leftover entry never false-rejects even if it hasn't been pruned yet;
    /// pruning is purely a memory concern and runs only when the map is full,
    /// keeping the hot path O(1) amortized.
    pub fn check_and_record(&self, key: &str, now: DateTime<Utc>) -> bool {
        let mut seen = self.seen.lock().expect("replay guard poisoned");
        if let Some(&first) = seen.get(key) {
            if now - first < self.ttl {
                return false; // replay within the window
            }
            // Stale entry for the same key — fall through and overwrite it.
        }
        if seen.len() >= MAX_KEYS {
            let ttl = self.ttl;
            seen.retain(|_, &mut t| now - t < ttl);
            if seen.len() >= MAX_KEYS {
                // Still full: a genuine flood of in-window unique keys. Evict
                // the oldest to bound memory (worst case: an attacker can age
                // out a real entry, re-opening a narrow replay window — an
                // acceptable trade against unbounded growth).
                if let Some(oldest) = seen.iter().min_by_key(|(_, &t)| t).map(|(k, _)| k.clone()) {
                    seen.remove(&oldest);
                }
            }
        }
        seen.insert(key.to_string(), now);
        true
    }

    pub fn len(&self) -> usize {
        self.seen.lock().expect("replay guard poisoned").len()
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
}

impl Default for ReplayGuard {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fresh_key_accepted_replay_rejected() {
        let g = ReplayGuard::new();
        let now = Utc::now();
        assert!(
            g.check_and_record("caller:h:abc", now),
            "first sighting = accept"
        );
        assert!(
            !g.check_and_record("caller:h:abc", now),
            "exact replay = reject"
        );
        assert!(
            g.check_and_record("caller:h:def", now),
            "distinct key = accept"
        );
    }

    #[test]
    fn key_reusable_after_ttl_expires() {
        let g = ReplayGuard::with_ttl(60);
        let t0 = Utc::now();
        assert!(g.check_and_record("k", t0));
        // Same key just past the TTL is no longer a replay (freshness gate in the
        // handler is what actually prevents deferred replay; this just frees memory).
        let later = t0 + Duration::seconds(61);
        assert!(
            g.check_and_record("k", later),
            "past TTL the key is free again"
        );
    }

    #[test]
    fn caller_namespacing_keeps_nonces_independent() {
        let g = ReplayGuard::new();
        let now = Utc::now();
        assert!(g.check_and_record("alice:n:1", now));
        // Same nonce value under a different caller prefix must not collide.
        assert!(g.check_and_record("bob:n:1", now));
    }
}
