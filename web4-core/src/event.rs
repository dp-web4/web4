// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later

//! # Events: R6/R7 as a wait-on-event-with-timeout
//!
//! The second half of the time axis (Thor's RTOS proposal): an R6/R7 submission
//! is **not** fire-and-forget or poll — the requester *blocks on the Result
//! event* up to its [`Deadline`](crate::time::Deadline). **Events are the
//! primary trigger; timers are the backup** for when no event arrives.
//!
//! This module provides the *types* and the *idempotency* logic; the actual
//! async blocking / dispatch surface is the hub's (the implementing track). An
//! [`Event`] carries a `request_id` so a Result can be matched to its Request
//! and **deduped** — HUB's caveat: a requester can time out, retry, then the
//! slow-but-successful Result arrives; without request-id dedup you'd
//! double-count it (once as a miss, once as a result). [`EventLog`] gives each
//! request exactly one terminal accounting.

use std::collections::HashSet;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::time::Deadline;

/// An event on the web4 event axis — the primary trigger for R6/R7 acts.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Event {
    pub event_id: Uuid,
    /// The request this event resolves/triggers (the matching + dedup key).
    pub request_id: Uuid,
    /// What kind of event (the subscription filter).
    pub topic: String,
    /// Who emitted it.
    pub emitter_lct: Uuid,
    /// Opaque payload (e.g. the Result).
    #[serde(default)]
    pub payload: serde_json::Value,
    pub at: DateTime<Utc>,
}

impl Event {
    pub fn new(request_id: Uuid, topic: impl Into<String>, emitter_lct: Uuid, at: DateTime<Utc>) -> Self {
        Self {
            event_id: Uuid::new_v4(),
            request_id,
            topic: topic.into(),
            emitter_lct,
            payload: serde_json::Value::Null,
            at,
        }
    }
    pub fn with_payload(mut self, payload: serde_json::Value) -> Self {
        self.payload = payload;
        self
    }
}

/// A wait-on-event-with-timeout: the submission blocks on an event matching
/// `topic` + `request_id`, up to `deadline`. Timers are the backup trigger.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct WaitCondition {
    pub request_id: Uuid,
    pub topic: String,
    pub deadline: Deadline,
}

impl WaitCondition {
    pub fn new(request_id: Uuid, topic: impl Into<String>, deadline: Deadline) -> Self {
        Self { request_id, topic: topic.into(), deadline }
    }

    /// Does `event` satisfy this wait?
    pub fn matches(&self, event: &Event) -> bool {
        event.request_id == self.request_id && event.topic == self.topic
    }

    /// Evaluate the wait given the (optional) event seen so far and the current
    /// time. The event-first/timer-backup rule: a matching event always wins;
    /// otherwise it's `Pending` until the deadline, then `TimedOut`.
    pub fn evaluate(&self, fired: Option<&Event>, now: DateTime<Utc>) -> WaitOutcome {
        if let Some(e) = fired {
            if self.matches(e) {
                return WaitOutcome::Fired(e.clone());
            }
        }
        if now > self.deadline.due_at {
            WaitOutcome::TimedOut
        } else {
            WaitOutcome::Pending
        }
    }
}

/// The result of a wait-on-event-with-timeout.
#[derive(Clone, Debug, PartialEq)]
pub enum WaitOutcome {
    /// The awaited event arrived (in or out of time — timing is judged
    /// separately via [`Deadline::evaluate`](crate::time::Deadline::evaluate)).
    Fired(Event),
    /// Still waiting; the deadline hasn't elapsed.
    Pending,
    /// The deadline elapsed with no matching event (the timer backup fired).
    TimedOut,
}

/// Whether a resolution is the first for its request, or a duplicate.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Admit {
    /// First terminal resolution of this request — account for it.
    Fresh,
    /// Already resolved (a retry, or a slow success after a timeout) — ignore;
    /// counting it again would double-count the request.
    Duplicate,
}

/// Idempotency ledger over request resolutions. Each `request_id` gets **one**
/// terminal accounting: the first resolution (a fired event *or* a timeout)
/// wins; any later one is a [`Admit::Duplicate`]. This is what stops a
/// slow-but-successful Result arriving after a timeout from being counted both
/// as a miss (trust debit) and a result.
#[derive(Debug, Default, Clone)]
pub struct EventLog {
    resolved: HashSet<Uuid>,
}

impl EventLog {
    pub fn new() -> Self {
        Self::default()
    }

    /// Record the terminal resolution of a request. First call → `Fresh`; any
    /// subsequent call for the same `request_id` → `Duplicate`.
    pub fn resolve(&mut self, request_id: Uuid) -> Admit {
        if self.resolved.insert(request_id) {
            Admit::Fresh
        } else {
            Admit::Duplicate
        }
    }

    pub fn is_resolved(&self, request_id: &Uuid) -> bool {
        self.resolved.contains(request_id)
    }

    pub fn len(&self) -> usize {
        self.resolved.len()
    }

    pub fn is_empty(&self) -> bool {
        self.resolved.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::time::Deadline;
    use chrono::Duration;

    fn due() -> DateTime<Utc> {
        DateTime::parse_from_rfc3339("2026-06-20T12:00:00Z").unwrap().with_timezone(&Utc)
    }

    #[test]
    fn fires_on_matching_event() {
        let rid = Uuid::new_v4();
        let w = WaitCondition::new(rid, "result", Deadline::new(due()));
        let ev = Event::new(rid, "result", Uuid::new_v4(), due() - Duration::minutes(1));
        assert!(matches!(w.evaluate(Some(&ev), due()), WaitOutcome::Fired(_)));
    }

    #[test]
    fn pending_then_timed_out() {
        let rid = Uuid::new_v4();
        let w = WaitCondition::new(rid, "result", Deadline::new(due()));
        assert_eq!(w.evaluate(None, due() - Duration::minutes(1)), WaitOutcome::Pending);
        assert_eq!(w.evaluate(None, due() + Duration::minutes(1)), WaitOutcome::TimedOut);
    }

    #[test]
    fn non_matching_event_does_not_fire() {
        let w = WaitCondition::new(Uuid::new_v4(), "result", Deadline::new(due()));
        let other = Event::new(Uuid::new_v4(), "result", Uuid::new_v4(), due());
        assert_eq!(w.evaluate(Some(&other), due() - Duration::minutes(1)), WaitOutcome::Pending);
    }

    #[test]
    fn idempotency_slow_success_after_timeout_is_deduped() {
        // HUB's caveat: time out, retry, then the slow success arrives — count
        // the request exactly once.
        let mut log = EventLog::new();
        let rid = Uuid::new_v4();
        // The timeout resolves it first (a miss is recorded).
        assert_eq!(log.resolve(rid), Admit::Fresh);
        // The slow-but-successful Result arrives later → duplicate, ignored, so
        // it's not also counted as a result (no double-count).
        assert_eq!(log.resolve(rid), Admit::Duplicate);
        // A retry of the same request is likewise deduped.
        assert_eq!(log.resolve(rid), Admit::Duplicate);
        assert_eq!(log.len(), 1);
        assert!(log.is_resolved(&rid));
    }

    #[test]
    fn distinct_requests_each_resolve_once() {
        let mut log = EventLog::new();
        let (a, b) = (Uuid::new_v4(), Uuid::new_v4());
        assert_eq!(log.resolve(a), Admit::Fresh);
        assert_eq!(log.resolve(b), Admit::Fresh);
        assert_eq!(log.resolve(a), Admit::Duplicate);
        assert_eq!(log.len(), 2);
    }
}
