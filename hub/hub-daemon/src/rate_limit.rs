// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Per-IP rate limiting middleware for the public fleet plane.
//!
//! P0 (public-release): a hub bound to 0.0.0.0 can be enumerated and queried by
//! arbitrary internet clients. This layer provides basic fail-closed rate
//! limiting as a last-line defense against scraping and cheap DoS.
//!
//! Wiring contract (review 2026-07-23): the limiter is passed via
//! `from_fn_with_state(limiter, rate_limit::layer)` — NOT a request extension.
//! The original extension-based wiring layered the middleware outside the
//! `Extension` layer, so the lookup always missed and the guard silently
//! fail-opened on every request. State-based wiring makes "limiter present"
//! a compile-time fact, so that failure mode cannot be reintroduced.
//!
//! Configuration (all optional, sensible defaults):
//!   HUB_RATE_LIMIT_RPS           — sustained requests/s per IP (default 10)
//!   HUB_RATE_LIMIT_BURST         — burst capacity per IP (default 30)
//!   HUB_RATE_LIMIT_LOOPBACK_MULT — ×rate for loopback callers (default 10;
//!                                  operator automation lives on loopback, but
//!                                  a same-host reverse proxy also launders
//!                                  public traffic to loopback, so loopback is
//!                                  rate-ADVANTAGED, never rate-EXEMPT)
//!   HUB_RATE_LIMIT_ENABLED       — set to 0 to disable (default 1)
//!   HUB_MAX_BODY_SIZE            — Content-Length cap in bytes (default 1 MiB)
//!
//! NOTE: this is an in-memory limiter. It protects a single process; a
//! production public hub should still sit behind a reverse proxy / edge layer
//! (Caddy, nginx, cloud) for global and geo-distributed rate limiting.

use axum::{
    extract::{ConnectInfo, Request, State},
    http::StatusCode,
    middleware::Next,
    response::{IntoResponse, Response},
};
use std::collections::HashMap;
use std::net::IpAddr;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::Mutex;

/// Sweep cadence for evicting refilled-idle buckets (see `Buckets::sweep`).
const SWEEP_EVERY: Duration = Duration::from_secs(60);
/// Hard cap on tracked IPs. An attacker cycling source addresses (trivial
/// with IPv6) would otherwise grow the map without bound — the limiter
/// itself becoming the memory-DoS vector. Hitting the cap clears the map:
/// momentarily generous (fresh buckets start full anyway), never unbounded.
const MAX_TRACKED_IPS: usize = 100_000;

/// Token-bucket state for one IP.
struct Bucket {
    tokens: f64,
    last_update: Instant,
}

impl Bucket {
    fn new(capacity: f64) -> Self {
        Self {
            tokens: capacity,
            last_update: Instant::now(),
        }
    }
}

/// Bucket map + sweep bookkeeping, behind one lock.
struct Buckets {
    map: HashMap<IpAddr, Bucket>,
    last_sweep: Instant,
}

impl Buckets {
    /// Evict buckets that have refilled to capacity — a full idle bucket is
    /// behaviorally identical to a fresh one, so dropping it loses nothing
    /// and bounds the map by *active* clients rather than *ever-seen* IPs.
    fn sweep(&mut self, now: Instant, rate: f64, capacity: f64) {
        if now.duration_since(self.last_sweep) < SWEEP_EVERY {
            return;
        }
        self.last_sweep = now;
        self.map.retain(|_, b| {
            b.tokens + now.duration_since(b.last_update).as_secs_f64() * rate < capacity
        });
        if self.map.len() > MAX_TRACKED_IPS {
            self.map.clear();
        }
    }
}

#[derive(Clone)]
pub struct RateLimiter {
    inner: Arc<RateLimiterInner>,
}

struct RateLimiterInner {
    buckets: Mutex<Buckets>,
    rate_per_second: f64,
    capacity: f64,
    loopback_mult: f64,
    max_body: usize,
}

impl RateLimiter {
    pub fn from_env() -> Option<Self> {
        if std::env::var("HUB_RATE_LIMIT_ENABLED").ok().as_deref() == Some("0") {
            return None;
        }
        let rps = std::env::var("HUB_RATE_LIMIT_RPS")
            .ok()
            .and_then(|s| s.parse::<f64>().ok())
            .filter(|&n| n > 0.0)
            .unwrap_or(10.0);
        let burst = std::env::var("HUB_RATE_LIMIT_BURST")
            .ok()
            .and_then(|s| s.parse::<f64>().ok())
            .filter(|&n| n >= 1.0)
            .unwrap_or((rps * 3.0).max(30.0));
        let loopback_mult = std::env::var("HUB_RATE_LIMIT_LOOPBACK_MULT")
            .ok()
            .and_then(|s| s.parse::<f64>().ok())
            .filter(|&n| n >= 1.0)
            .unwrap_or(10.0);
        let max_body = std::env::var("HUB_MAX_BODY_SIZE")
            .ok()
            .and_then(|s| s.parse::<usize>().ok())
            .filter(|&n| n >= 1024)
            .unwrap_or(1024 * 1024);
        Some(Self::new(rps, burst, loopback_mult, max_body))
    }

    fn new(rps: f64, burst: f64, loopback_mult: f64, max_body: usize) -> Self {
        Self {
            inner: Arc::new(RateLimiterInner {
                buckets: Mutex::new(Buckets {
                    map: HashMap::new(),
                    last_sweep: Instant::now(),
                }),
                rate_per_second: rps,
                capacity: burst,
                loopback_mult,
                max_body,
            }),
        }
    }

    /// Check whether `ip` may make a request right now. Returns true if allowed.
    async fn allow(&self, ip: IpAddr) -> bool {
        let now = Instant::now();
        // Loopback = operator plane + local tooling: advantaged, not exempt
        // (a same-host reverse proxy makes public traffic read as loopback).
        let mult = if ip.is_loopback() { self.inner.loopback_mult } else { 1.0 };
        let rate = self.inner.rate_per_second * mult;
        let capacity = self.inner.capacity * mult;
        let mut buckets = self.inner.buckets.lock().await;
        buckets.sweep(now, self.inner.rate_per_second, self.inner.capacity);
        let bucket = buckets.map.entry(ip).or_insert_with(|| Bucket::new(capacity));
        let elapsed = now.duration_since(bucket.last_update).as_secs_f64();
        bucket.tokens = (bucket.tokens + elapsed * rate).min(capacity);
        bucket.last_update = now;
        if bucket.tokens >= 1.0 {
            bucket.tokens -= 1.0;
            true
        } else {
            false
        }
    }

    pub fn max_body_size(&self) -> usize {
        self.inner.max_body
    }
}

/// Axum middleware entry point. Wire with
/// `axum::middleware::from_fn_with_state(limiter, rate_limit::layer)` —
/// the limiter arrives as STATE, so a mis-ordered layer stack cannot make
/// this guard silently disappear.
pub async fn layer(
    State(limiter): State<RateLimiter>,
    ConnectInfo(addr): ConnectInfo<std::net::SocketAddr>,
    req: Request,
    next: Next,
) -> Response {
    // Hard request-body size cap (Content-Length only; chunked bodies without
    // a length header pass through to the handlers — production should also
    // bound bodies at the reverse proxy or with tower-http's
    // RequestBodyLimitLayer).
    if let Some(content_length) = req.headers().get("content-length") {
        if let Ok(s) = content_length.to_str() {
            if let Ok(n) = s.parse::<usize>() {
                if n > limiter.max_body_size() {
                    return (
                        StatusCode::PAYLOAD_TOO_LARGE,
                        format!("request body exceeds {} bytes", limiter.max_body_size()),
                    )
                        .into_response();
                }
            }
        }
    }
    if !limiter.allow(addr.ip()).await {
        return (
            StatusCode::TOO_MANY_REQUESTS,
            "rate limit exceeded — slow down",
        )
            .into_response();
    }
    next.run(req).await
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::{IpAddr, Ipv4Addr};

    fn limiter(rps: f64, burst: f64) -> RateLimiter {
        RateLimiter::new(rps, burst, 10.0, 1024 * 1024)
    }

    #[tokio::test]
    async fn token_bucket_allows_burst_then_throttles() {
        let l = limiter(1.0, 3.0);
        let ip = IpAddr::V4(Ipv4Addr::new(192, 0, 2, 1));
        assert!(l.allow(ip).await, "first request uses token 1");
        assert!(l.allow(ip).await, "second request uses token 2");
        assert!(l.allow(ip).await, "third request uses token 3");
        assert!(!l.allow(ip).await, "bucket empty");
    }

    #[tokio::test]
    async fn token_bucket_is_per_ip() {
        let l = limiter(1.0, 1.0);
        let a = IpAddr::V4(Ipv4Addr::new(192, 0, 2, 1));
        let b = IpAddr::V4(Ipv4Addr::new(192, 0, 2, 2));
        assert!(l.allow(a).await);
        assert!(!l.allow(a).await);
        assert!(l.allow(b).await, "distinct IP has its own bucket");
    }

    #[tokio::test]
    async fn loopback_is_advantaged_not_exempt() {
        let l = limiter(1.0, 1.0); // mult 10 → loopback capacity 10
        let lo = IpAddr::V4(Ipv4Addr::LOCALHOST);
        for i in 0..10 {
            assert!(l.allow(lo).await, "loopback request {i} within 10x burst");
        }
        assert!(!l.allow(lo).await, "loopback still bounded — never exempt");
    }

    #[tokio::test]
    async fn composed_router_actually_limits_the_wiring_test() {
        // THE test the original wiring lacked (review 2026-07-23): the
        // extension-based stack layered the middleware outside the Extension
        // layer, so the limiter silently never ran on any request. This
        // drives a router composed exactly like main.rs (from_fn_with_state)
        // and proves a real 429 comes back — if the guard ever silently
        // detaches again, this fails.
        use axum::{routing::get, Router};
        use tower::ServiceExt;
        let l = limiter(1.0, 2.0); // burst of 2
        let app: Router = Router::new()
            .route("/", get(|| async { "ok" }))
            .layer(axum::middleware::from_fn_with_state(l, super::layer));
        let addr: std::net::SocketAddr = "203.0.113.9:4444".parse().unwrap();
        let request = |body: axum::body::Body| {
            let mut req = axum::http::Request::builder().uri("/").body(body).unwrap();
            req.extensions_mut().insert(ConnectInfo(addr));
            req
        };
        for i in 0..2 {
            let res = app.clone().oneshot(request(axum::body::Body::empty())).await.unwrap();
            assert_eq!(res.status(), StatusCode::OK, "request {i} within burst");
        }
        let res = app.clone().oneshot(request(axum::body::Body::empty())).await.unwrap();
        assert_eq!(
            res.status(),
            StatusCode::TOO_MANY_REQUESTS,
            "third request over burst MUST 429 — the limiter runs in the composed router"
        );
        // The body-size cap lives in the same middleware — prove it runs too.
        let mut req = axum::http::Request::builder()
            .uri("/")
            .header("content-length", (10 * 1024 * 1024).to_string())
            .body(axum::body::Body::empty())
            .unwrap();
        req.extensions_mut().insert(ConnectInfo(addr));
        let res = app.clone().oneshot(req).await.unwrap();
        assert_eq!(res.status(), StatusCode::PAYLOAD_TOO_LARGE);
    }

    #[tokio::test]
    async fn sweep_evicts_refilled_buckets_and_caps_map() {
        let l = limiter(1000.0, 1.0); // fast refill so buckets refill instantly
        for i in 0..50u8 {
            let ip = IpAddr::V4(Ipv4Addr::new(192, 0, 2, i));
            let _ = l.allow(ip).await;
        }
        {
            let mut buckets = l.inner.buckets.lock().await;
            assert!(buckets.map.len() >= 50);
            // Force the sweep window open and run it: all buckets have long
            // since refilled at 1000 tokens/s, so all are evictable.
            buckets.last_sweep = Instant::now() - SWEEP_EVERY - Duration::from_secs(1);
            let now = Instant::now() + Duration::from_secs(1);
            buckets.sweep(now, 1000.0, 1.0);
            assert!(
                buckets.map.is_empty(),
                "refilled-idle buckets are evicted — the map is bounded by \
                 active clients, not ever-seen IPs"
            );
        }
        // Evicted IP behaves like a fresh client (full bucket) — no lockout.
        let ip = IpAddr::V4(Ipv4Addr::new(192, 0, 2, 7));
        assert!(l.allow(ip).await);
    }
}
