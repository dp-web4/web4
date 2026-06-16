//! Rate limiter for vault-unlock attempts (the stub-console / passphrase path).
//!
//! The unlock slot does not remove the need for the passphrase — a privileged
//! unlock plugin is more secure because *we* control how the passphrase is
//! obtained (prompted in our UI) and what we do with it (use-then-discard,
//! never stored). But anyone who can reach that UI could still *feed it
//! guesses*. So, independent of how the secret is obtained, the unlock path is
//! gated: a **minimum interval** between attempts, a **maximum number of
//! consecutive failures**, and a **lockout** once that cap is hit. This is the
//! "usual number of tries + minimum time between attempts" backstop against
//! online brute force.
//!
//! Time is passed in explicitly (`now`, unix seconds) so the policy is
//! deterministically testable; production callers pass `Utc::now().timestamp()`.

use std::sync::Mutex;

/// What the gate decided about an attempt right now.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GateDecision {
    /// Proceed with the unlock attempt; the caller MUST then report the outcome
    /// via [`UnlockGate::record_failure`] or [`UnlockGate::record_success`].
    Allow,
    /// Too soon after the previous attempt — wait `retry_after_secs`.
    TooSoon { retry_after_secs: i64 },
    /// Locked out after too many consecutive failures — wait `retry_after_secs`.
    LockedOut { retry_after_secs: i64 },
}

#[derive(Debug, Default)]
struct GateState {
    consecutive_fails: u32,
    last_attempt: Option<i64>,
    locked_out_until: Option<i64>,
}

/// A small, thread-safe attempt limiter. One per hub (shared via `Arc`).
#[derive(Debug)]
pub struct UnlockGate {
    inner: Mutex<GateState>,
    max_fails: u32,
    min_interval_secs: i64,
    lockout_secs: i64,
}

impl UnlockGate {
    pub fn new(max_fails: u32, min_interval_secs: i64, lockout_secs: i64) -> Self {
        Self {
            inner: Mutex::new(GateState::default()),
            max_fails,
            min_interval_secs,
            lockout_secs,
        }
    }

    /// The default policy: **5** consecutive failures, **2 s** minimum between
    /// attempts, **5-minute** lockout once the cap is hit.
    pub fn default_policy() -> Self {
        Self::new(5, 2, 300)
    }

    /// Check whether an attempt is allowed *now*, and (if allowed) stamp it as
    /// the latest attempt so the min-interval applies to the next one. Returns
    /// the reason + retry hint when refused.
    pub fn check(&self, now: i64) -> GateDecision {
        let mut g = self.inner.lock().expect("unlock gate poisoned");
        if let Some(until) = g.locked_out_until {
            if now < until {
                return GateDecision::LockedOut { retry_after_secs: until - now };
            }
            // Lockout elapsed — clear it and the failure streak.
            g.locked_out_until = None;
            g.consecutive_fails = 0;
        }
        if let Some(last) = g.last_attempt {
            let elapsed = now - last;
            if elapsed < self.min_interval_secs {
                return GateDecision::TooSoon { retry_after_secs: self.min_interval_secs - elapsed };
            }
        }
        g.last_attempt = Some(now);
        GateDecision::Allow
    }

    /// Record a failed attempt; trips the lockout once the cap is reached.
    pub fn record_failure(&self, now: i64) {
        let mut g = self.inner.lock().expect("unlock gate poisoned");
        g.consecutive_fails += 1;
        g.last_attempt = Some(now);
        if g.consecutive_fails >= self.max_fails {
            g.locked_out_until = Some(now + self.lockout_secs);
        }
    }

    /// Record a successful unlock; clears all rate-limit state.
    pub fn record_success(&self) {
        let mut g = self.inner.lock().expect("unlock gate poisoned");
        *g = GateState::default();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn min_interval_between_attempts_is_enforced() {
        let g = UnlockGate::new(5, 2, 300);
        assert_eq!(g.check(1000), GateDecision::Allow);
        // 1s later — too soon (need 2s).
        assert_eq!(g.check(1001), GateDecision::TooSoon { retry_after_secs: 1 });
        // 2s after the first allowed attempt — fine again.
        assert_eq!(g.check(1002), GateDecision::Allow);
    }

    #[test]
    fn lockout_after_max_consecutive_failures() {
        let g = UnlockGate::new(3, 0, 300); // 0 min-interval to isolate the fail cap
        for i in 0..3 {
            let now = 2000 + i;
            assert_eq!(g.check(now), GateDecision::Allow);
            g.record_failure(now);
        }
        // 3 fails reached (last at t=2002 → locked until 2302) → locked out.
        match g.check(2002) {
            GateDecision::LockedOut { retry_after_secs } => assert_eq!(retry_after_secs, 300),
            other => panic!("expected lockout, got {other:?}"),
        }
    }

    #[test]
    fn lockout_expires_then_allows_again() {
        let g = UnlockGate::new(2, 0, 300);
        for i in 0..2 {
            assert_eq!(g.check(3000 + i), GateDecision::Allow);
            g.record_failure(3000 + i);
        }
        assert!(matches!(g.check(3001), GateDecision::LockedOut { .. }));
        // After the lockout window (last fail t=3001 → until 3301), attempts resume.
        assert_eq!(g.check(3301), GateDecision::Allow);
    }

    #[test]
    fn success_resets_the_failure_streak() {
        let g = UnlockGate::new(3, 0, 300);
        g.check(4000);
        g.record_failure(4000);
        g.check(4001);
        g.record_failure(4001);
        g.record_success();
        // Streak cleared; a fresh failure doesn't immediately lock out.
        assert_eq!(g.check(4002), GateDecision::Allow);
        g.record_failure(4002);
        assert_eq!(g.check(4003), GateDecision::Allow); // only 1 fail since reset
    }
}
