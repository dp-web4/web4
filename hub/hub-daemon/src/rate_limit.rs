// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Per-IP rate limiting middleware for the public fleet plane.
//!
//! P0 (public-release): a hub bound to 0.0.0.0 can be enumerated and queried by
//! arbitrary internet clients. This layer provides basic fail-closed rate
//! limiting as a last-line defense against scraping and cheap DoS.
//!
//! Configuration (all optional, sensible defaults):
//!   HUB_RATE_LIMIT_RPS      — sustained requests per second per IP (default 10)
//!   HUB_RATE_LIMIT_BURST    — burst capacity per IP (default 30)
//!   HUB_RATE_LIMIT_ENABLED  — set to 0 to disable (default 1)
//!
//! NOTE: this is an in-memory limiter. It protects a single process; a
//! production public hub should still sit behind a reverse proxy / edge layer
//! (Caddy, nginx, cloud) for global and geo-distributed rate limiting.

use axum::{
    extract::{ConnectInfo, Request},
    http::StatusCode,
    middleware::Next,
    response::{IntoResponse, Response},
};
use std::collections::HashMap;
use std::net::IpAddr;
use std::sync::Arc;
use std::time::Instant;
use tokio::sync::Mutex;

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

#[derive(Clone)]
pub struct RateLimiter {
    inner: Arc<RateLimiterInner>,
}

struct RateLimiterInner {
    buckets: Mutex<HashMap<IpAddr, Bucket>>,
    rate_per_second: f64,
    capacity: f64,
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
        Some(Self {
            inner: Arc::new(RateLimiterInner {
                buckets: Mutex::new(HashMap::new()),
                rate_per_second: rps,
                capacity: burst,
            }),
        })
    }

    /// Check whether `ip` may make a request right now. Returns true if allowed.
    async fn allow(&self, ip: IpAddr) -> bool {
        let now = Instant::now();
        let mut buckets = self.inner.buckets.lock().await;
        let bucket = buckets.entry(ip).or_insert_with(|| Bucket::new(self.inner.capacity));
        let elapsed = now.duration_since(bucket.last_update).as_secs_f64();
        bucket.tokens = (bucket.tokens + elapsed * self.inner.rate_per_second).min(self.inner.capacity);
        bucket.last_update = now;
        if bucket.tokens >= 1.0 {
            bucket.tokens -= 1.0;
            true
        } else {
            false
        }
    }
}

/// Axum middleware entry point.
pub async fn layer(
    ConnectInfo(addr): ConnectInfo<std::net::SocketAddr>,
    req: Request,
    next: Next,
) -> Response {
    // The limiter is constructed once in main.rs and passed as an extension.
    let Some(limiter): Option<&RateLimiter> = req.extensions().get::<RateLimiter>() else {
        return next.run(req).await;
    };
    // Hard request-body size cap (Content-Length only; chunked bodies without a
    // length header pass through to the handlers, which is why production should
    // use a reverse proxy or tower-http's RequestBodyLimitLayer).
    let max_body = max_body_size();
    if let Some(content_length) = req.headers().get("content-length") {
        if let Ok(s) = content_length.to_str() {
            if let Ok(n) = s.parse::<usize>() {
                if n > max_body {
                    return (
                        StatusCode::PAYLOAD_TOO_LARGE,
                        format!("request body exceeds {} bytes", max_body),
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

/// Convenience: build a request-body length limit fallback. Axum's default body
/// is streaming; without tower-http we cannot enforce a hard payload cap in the
/// middleware layer cleanly. Production deployments should use a reverse proxy
/// or tower-http's RequestBodyLimitLayer. This helper documents/envoys the
/// intended max body size (bytes) from HUB_MAX_BODY_SIZE (default 1 MiB).
pub fn max_body_size() -> usize {
    std::env::var("HUB_MAX_BODY_SIZE")
        .ok()
        .and_then(|s| s.parse::<usize>().ok())
        .filter(|&n| n >= 1024)
        .unwrap_or(1024 * 1024)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::{IpAddr, Ipv4Addr};

    #[tokio::test]
    async fn token_bucket_allows_burst_then_throttles() {
        let limiter = RateLimiter {
            inner: Arc::new(RateLimiterInner {
                buckets: Mutex::new(HashMap::new()),
                rate_per_second: 1.0,
                capacity: 3.0,
            }),
        };
        let ip = IpAddr::V4(Ipv4Addr::new(192, 0, 2, 1));
        assert!(limiter.allow(ip).await, "first request uses token 1");
        assert!(limiter.allow(ip).await, "second request uses token 2");
        assert!(limiter.allow(ip).await, "third request uses token 3");
        assert!(!limiter.allow(ip).await, "bucket empty");
    }

    #[tokio::test]
    async fn token_bucket_is_per_ip() {
        let limiter = RateLimiter {
            inner: Arc::new(RateLimiterInner {
                buckets: Mutex::new(HashMap::new()),
                rate_per_second: 1.0,
                capacity: 1.0,
            }),
        };
        let a = IpAddr::V4(Ipv4Addr::new(192, 0, 2, 1));
        let b = IpAddr::V4(Ipv4Addr::new(192, 0, 2, 2));
        assert!(limiter.allow(a).await);
        assert!(!limiter.allow(a).await);
        assert!(limiter.allow(b).await, "distinct IP has its own bucket");
    }
}
