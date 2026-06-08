// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.
//
//! Mock Hestia — minimal sign-request callback server for hub smoke
//! testing. Loads a Sovereign IdentityFile, listens on the given port,
//! signs every SignRequest that comes in (no policy gating). This is
//! NOT a real Hestia — production goes through Legion's hestia repo.
//!
//! Usage:
//!     hub-mock-hestia --identity sov.json --port 9001
//!
//! Then point a Hestia-mode hub at http://127.0.0.1:9001/sign-request.

use anyhow::{Context, Result};
use axum::{routing::post, Router};
use clap::Parser;
use std::path::PathBuf;
use std::sync::Arc;
use uuid::Uuid;

use hub_lib::identity::IdentityFile;
use hub_lib::signer::{SignRequest, SignResponse};
use web4_core::crypto::KeyPair;

#[derive(Parser, Debug)]
#[command(name = "mock-hestia")]
struct Args {
    /// Sovereign IdentityFile (LCT + keypair). Generate with `hub gen-lct`.
    #[arg(long)]
    identity: PathBuf,

    /// Bind port.
    #[arg(long, default_value_t = 9001)]
    port: u16,

    /// Optionally deny every request (smoke test for denial path).
    #[arg(long)]
    deny_all: Option<String>,
}

#[derive(Clone)]
struct MockState {
    lct_id: Uuid,
    keypair: Arc<KeyPair>,
    deny_reason: Option<String>,
}

async fn sign_handler(
    axum::extract::State(state): axum::extract::State<MockState>,
    axum::Json(req): axum::Json<SignRequest>,
) -> axum::Json<SignResponse> {
    eprintln!(
        "[mock-hestia] sign-request: chapter='{}' actor={} event_kind={} ledger_index={}",
        req.intent.hub_name, req.intent.actor_lct_id,
        req.intent.event_kind, req.intent.ledger_index,
    );

    if let Some(reason) = &state.deny_reason {
        eprintln!("[mock-hestia] DENIED: {}", reason);
        return axum::Json(SignResponse::Denied {
            request_id: req.intent.request_id,
            denied: true,
            deny_reason: reason.clone(),
        });
    }

    if req.intent.actor_lct_id != state.lct_id {
        eprintln!(
            "[mock-hestia] DENIED: actor mismatch — request for {} but loaded {}",
            req.intent.actor_lct_id, state.lct_id
        );
        return axum::Json(SignResponse::Denied {
            request_id: req.intent.request_id,
            denied: true,
            deny_reason: format!(
                "loaded identity is {}, not {}",
                state.lct_id, req.intent.actor_lct_id
            ),
        });
    }

    let bytes = hex::decode(&req.signing_bytes_hex).expect("hex signing_bytes");
    let sig = state.keypair.sign(&bytes);
    eprintln!("[mock-hestia] APPROVED: signed {} bytes", bytes.len());

    axum::Json(SignResponse::Approved {
        request_id: req.intent.request_id,
        signature: hex::encode(sig.bytes),
    })
}

#[tokio::main]
async fn main() -> Result<()> {
    let args = Args::parse();

    let identity = IdentityFile::load(&args.identity)
        .with_context(|| format!("loading {}", args.identity.display()))?;
    let keypair = identity.keypair().context("reconstructing keypair")?;

    let state = MockState {
        lct_id: identity.lct.id,
        keypair: Arc::new(keypair),
        deny_reason: args.deny_all,
    };

    let app = Router::new()
        .route("/sign-request", post(sign_handler))
        .with_state(state);

    let addr = format!("127.0.0.1:{}", args.port);
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    eprintln!("[mock-hestia] LCT id:   {}", identity.lct.id);
    eprintln!("[mock-hestia] Pubkey:   {}", hex::encode(identity.lct.public_key.to_bytes()));
    eprintln!("[mock-hestia] Listening on http://{}/sign-request", addr);

    axum::serve(listener, app).await?;
    Ok(())
}
