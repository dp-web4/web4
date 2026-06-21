// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later

//! # Time as a first-class web4 axis (the temporal twin of ATP)
//!
//! `Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP` has **space** (MRH),
//! **energy** (ATP/ADP), **trust** (T3/V3), and **identity** (LCT) — but no
//! **time + events as an accountable axis**. This module adds it (Thor's RTOS
//! proposal, 2026-06-20):
//!
//! 1. **A deadline is a Resource** — the temporal twin of ATP. ATP makes
//!    *spending energy* accountable; this makes *spending time* accountable.
//! 2. **R6/R7 is a wait-on-event-with-timeout** (see [`crate::event`]); a
//!    deadline bounds the wait.
//! 3. **A deadline-miss is a trust event** — it folds into T3 (Temperament) and
//!    V3 (Veracity), propagating up the MRH like any other reputation delta.
//!
//! ## The accountability gate (HUB's review caveats, baked in)
//!
//! A non-response is *not* automatically a temperament fault. Only a genuine
//! "could have responded in time and didn't" debits trust:
//!
//! - **Witness-unavailable ⇒ [`DeadlineOutcome::Suspended`], not missed.** If
//!   the deadline-witness (e.g. the hub) was down/locked at the due time, every
//!   in-flight deadline must *pause*, not expire — otherwise a hub outage would
//!   fire a fleet-wide false-lateness cascade. *Hub downtime is not fleet
//!   lateness.* Checked first; it overrides everything.
//! - **Unreachable ≠ refused.** A responder partitioned/crashed is
//!   [`DeadlineOutcome::Unreachable`] — a clock/network fault, **not** priced as
//!   Temperament (don't poison the trust graph with the network).
//! - Only [`DeadlineOutcome::Late`]/[`DeadlineOutcome::Missed`] with a reachable
//!   responder and an available witness carry a trust debit.
//!
//! Idempotency (a requester that timed out, retried, then got the slow success)
//! is handled at the event layer ([`crate::event::EventLog`]) so a slow success
//! isn't double-counted as both a miss and a result.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::{T3, TrustDimension, V3, ValueDimension};

/// How critical lateness is — scales the trust debit, like RTOS task priority.
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, Default)]
#[serde(rename_all = "snake_case")]
pub enum Criticality {
    /// Best-effort; lateness is noted, barely penalized.
    Soft,
    /// The default — lateness is a real but bounded trust signal.
    #[default]
    Firm,
    /// Hard real-time; a miss is a significant temperament fault.
    Hard,
}

impl Criticality {
    fn scale(self) -> f64 {
        match self {
            Criticality::Soft => 0.25,
            Criticality::Firm => 1.0,
            Criticality::Hard => 2.0,
        }
    }
}

/// A deadline carried on an R6 [`Request`](crate::r6::Request) — **time as a
/// Resource**, the twin of `atp_stake`. The requester commits to a `due_at`;
/// the responder is accountable for meeting it.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Deadline {
    /// When the Result is due.
    pub due_at: DateTime<Utc>,
    /// How hard the deadline is.
    #[serde(default)]
    pub criticality: Criticality,
}

impl Deadline {
    pub fn new(due_at: DateTime<Utc>) -> Self {
        Self { due_at, criticality: Criticality::Firm }
    }

    pub fn with_criticality(mut self, c: Criticality) -> Self {
        self.criticality = c;
        self
    }

    /// Decide the outcome from observed timing + witnessed liveness, applying
    /// the accountability gate. `now` is the evaluation time (for an action
    /// that hasn't completed). See the module docs for the caveats.
    pub fn evaluate(
        &self,
        timing: &Timing,
        witness: WitnessAvailability,
        reachable: bool,
        now: DateTime<Utc>,
    ) -> DeadlineOutcome {
        // A clock fault overrides everything: if the deadline-witness was down,
        // the deadline is paused, never auto-expired.
        if witness == WitnessAvailability::Unavailable {
            return DeadlineOutcome::Suspended;
        }
        match timing.completed_at {
            Some(done) if done <= self.due_at => DeadlineOutcome::Met,
            Some(done) => DeadlineOutcome::Late {
                overdue_secs: (done - self.due_at).num_seconds().max(0),
            },
            // Still in flight:
            None if now <= self.due_at => DeadlineOutcome::Met, // not yet due
            None if !reachable => DeadlineOutcome::Unreachable, // network fault
            None => DeadlineOutcome::Missed {
                overdue_secs: (now - self.due_at).num_seconds().max(0),
            },
        }
    }

    /// The T3/V3 reputation impact of an outcome — "lateness is a trust event",
    /// gated so only genuine faults debit trust. Met → a small positive
    /// (responsiveness builds Temperament); Late/Missed → negative scaled by
    /// criticality × overdue magnitude; Suspended/Unreachable → **zero** (clock
    /// and network faults are not temperament faults).
    pub fn reputation_impact(&self, outcome: &DeadlineOutcome) -> TemporalImpact {
        let scale = self.criticality.scale();
        match outcome {
            DeadlineOutcome::Met => TemporalImpact {
                temperament: 0.01 * scale,
                veracity: 0.005 * scale,
            },
            DeadlineOutcome::Late { overdue_secs } => {
                let m = magnitude(*overdue_secs);
                TemporalImpact { temperament: -0.02 * scale * m, veracity: -0.01 * scale * m }
            }
            DeadlineOutcome::Missed { overdue_secs } => {
                let m = magnitude(*overdue_secs);
                TemporalImpact { temperament: -0.05 * scale * m, veracity: -0.03 * scale * m }
            }
            DeadlineOutcome::Suspended | DeadlineOutcome::Unreachable => {
                TemporalImpact { temperament: 0.0, veracity: 0.0 }
            }
        }
    }
}

/// Observed timing of an action's execution.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Timing {
    pub started_at: DateTime<Utc>,
    /// `None` ⇒ still in-flight / never completed.
    #[serde(default)]
    pub completed_at: Option<DateTime<Utc>>,
}

impl Timing {
    pub fn started(at: DateTime<Utc>) -> Self {
        Self { started_at: at, completed_at: None }
    }
    pub fn complete(mut self, at: DateTime<Utc>) -> Self {
        self.completed_at = Some(at);
        self
    }
}

/// Whether the deadline-witness (the observer timing the deadline) was reachable
/// at the due time. The first thing the gate checks.
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq, Default)]
#[serde(rename_all = "snake_case")]
pub enum WitnessAvailability {
    #[default]
    Available,
    /// The deadline-witness (e.g. the hub) was down/locked at the due time.
    Unavailable,
}

/// The temporal-accountability verdict. Note `Late ≠ Missed ≠ Suspended ≠
/// Unreachable` — only the first two are faults (HUB's "late ≠ never ≠ refused
/// ≠ unreachable").
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case", tag = "outcome")]
pub enum DeadlineOutcome {
    /// Completed at or before the deadline (or not yet due).
    Met,
    /// Completed, but after the deadline.
    Late { overdue_secs: i64 },
    /// Past due, responder reachable, witness available — a genuine fault.
    Missed { overdue_secs: i64 },
    /// Deadline-witness was unavailable at the due time → paused, not missed.
    /// Carries **no** trust debit.
    Suspended,
    /// Responder unreachable (partition/crash) — a network fault, not a
    /// temperament fault. **No** trust debit.
    Unreachable,
}

impl DeadlineOutcome {
    /// Whether this outcome is a genuine accountability fault (debits trust).
    pub fn is_fault(&self) -> bool {
        matches!(self, DeadlineOutcome::Late { .. } | DeadlineOutcome::Missed { .. })
    }
}

/// The T3/V3 trust signal a deadline outcome produces.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct TemporalImpact {
    /// Delta to T3 Temperament (consistency / responsiveness).
    pub temperament: f64,
    /// Delta to V3 Veracity (did it do what it said, when it said).
    pub veracity: f64,
}

impl TemporalImpact {
    /// Fold this temporal trust signal into a T3 + V3 (Temperament / Veracity).
    /// This is the "deadline-miss propagates to T3/V3" step.
    pub fn apply(&self, t3: &mut T3, v3: &mut V3) {
        t3.apply_delta(TrustDimension::Temperament, self.temperament);
        v3.apply_delta(ValueDimension::Veracity, self.veracity);
    }
}

/// Map overdue seconds to a saturating penalty magnitude in `[0.1, 1.0]`:
/// a small overshoot is minor; very late saturates (no unbounded punishment).
fn magnitude(overdue_secs: i64) -> f64 {
    let mins = overdue_secs.max(0) as f64 / 60.0;
    ((1.0 + mins).ln() / 6.0).clamp(0.1, 1.0)
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Duration;

    fn base() -> (DateTime<Utc>, Deadline) {
        let due = DateTime::parse_from_rfc3339("2026-06-20T12:00:00Z").unwrap().with_timezone(&Utc);
        (due, Deadline::new(due))
    }

    #[test]
    fn met_when_completed_before_due() {
        let (due, d) = base();
        let t = Timing::started(due - Duration::minutes(10)).complete(due - Duration::minutes(1));
        let o = d.evaluate(&t, WitnessAvailability::Available, true, due);
        assert_eq!(o, DeadlineOutcome::Met);
        let imp = d.reputation_impact(&o);
        assert!(imp.temperament > 0.0, "meeting a deadline builds Temperament");
    }

    #[test]
    fn late_when_completed_after_due_debits_trust() {
        let (due, d) = base();
        let t = Timing::started(due - Duration::minutes(10)).complete(due + Duration::minutes(30));
        let o = d.evaluate(&t, WitnessAvailability::Available, true, due + Duration::hours(1));
        assert!(matches!(o, DeadlineOutcome::Late { .. }));
        assert!(o.is_fault());
        let imp = d.reputation_impact(&o);
        assert!(imp.temperament < 0.0 && imp.veracity < 0.0);
    }

    #[test]
    fn missed_when_past_due_reachable_and_witnessed() {
        let (due, d) = base();
        let t = Timing::started(due - Duration::minutes(10)); // never completed
        let o = d.evaluate(&t, WitnessAvailability::Available, true, due + Duration::minutes(45));
        assert!(matches!(o, DeadlineOutcome::Missed { .. }));
        assert!(d.reputation_impact(&o).temperament < 0.0);
    }

    #[test]
    fn witness_unavailable_suspends_not_misses() {
        // HUB's caveat: hub down/locked at due time ⇒ paused, no debit.
        let (due, d) = base();
        let t = Timing::started(due - Duration::minutes(10));
        let o = d.evaluate(&t, WitnessAvailability::Unavailable, true, due + Duration::hours(5));
        assert_eq!(o, DeadlineOutcome::Suspended);
        assert!(!o.is_fault());
        let imp = d.reputation_impact(&o);
        assert_eq!((imp.temperament, imp.veracity), (0.0, 0.0));
    }

    #[test]
    fn unreachable_is_not_a_temperament_fault() {
        // HUB's caveat: a partition/crash ≠ declining. No trust debit.
        let (due, d) = base();
        let t = Timing::started(due - Duration::minutes(10));
        let o = d.evaluate(&t, WitnessAvailability::Available, false, due + Duration::minutes(45));
        assert_eq!(o, DeadlineOutcome::Unreachable);
        assert!(!o.is_fault());
        assert_eq!(d.reputation_impact(&o).temperament, 0.0);
    }

    #[test]
    fn criticality_scales_the_debit() {
        let (due, _) = base();
        let t = Timing::started(due).complete(due + Duration::minutes(30));
        let soft = Deadline::new(due).with_criticality(Criticality::Soft);
        let hard = Deadline::new(due).with_criticality(Criticality::Hard);
        let now = due + Duration::hours(1);
        let soft_imp = soft.reputation_impact(&soft.evaluate(&t, WitnessAvailability::Available, true, now));
        let hard_imp = hard.reputation_impact(&hard.evaluate(&t, WitnessAvailability::Available, true, now));
        assert!(hard_imp.temperament < soft_imp.temperament, "hard miss costs more");
    }

    #[test]
    fn impact_folds_into_tensors() {
        let (due, d) = base();
        let t = Timing::started(due).complete(due + Duration::hours(2));
        let o = d.evaluate(&t, WitnessAvailability::Available, true, due + Duration::hours(3));
        let mut t3 = T3::new();
        let mut v3 = V3::new();
        let before = t3.score(TrustDimension::Temperament);
        d.reputation_impact(&o).apply(&mut t3, &mut v3);
        assert!(t3.score(TrustDimension::Temperament) < before, "late miss lowers Temperament");
    }
}
