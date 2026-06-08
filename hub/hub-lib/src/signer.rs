// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Remote signing abstraction (V2-7 Step 3).
//!
//! ## Why
//!
//! Per architecture commitment #8, the hub does not hold private keys —
//! secrets live in Hestia's vault. When the hub builds a ledger entry
//! that must be signed by the Sovereign (or any role-filler), it asks
//! a [`RemoteSigner`] to produce the signature over an exact byte
//! payload. Hestia (via H2/H3 + later sovereign-sign-callback) is the
//! production implementation.
//!
//! ## Wire flow
//!
//! 1. Hub: `let unsigned = ledger.build_entry(actor_id, event, ts)?;`
//! 2. Hub: `let sig = signer.sign(actor_id, &unsigned.signing_bytes, &intent).await?;`
//! 3. Hub: `ledger.append_signed(unsigned, sig)?;`
//!
//! The hub passes BOTH the exact `signing_bytes` AND a structured
//! `intent` description. Vault implementations should re-derive the
//! signing bytes from the intent (proves the bytes match what they
//! claim to represent) before signing. Bytes-only signing is a
//! convenience for trusted callers (local keypair, mock).
//!
//! ## V2-7 Step 3 scope
//!
//! - [`LocalKeypairSigner`] — wraps a [`KeyPair`]; signs in-process.
//!   The MVP signing path moves through this trait without changing
//!   behavior.
//! - `HestiaCallbackSigner` — POSTs sign-request to a callback URL,
//!   awaits Hestia's signed response. Lands in Step 3b.2.

use anyhow::{anyhow, Result};
use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use web4_core::crypto::{KeyPair, SignatureBytes};

/// Description of what's about to be signed. Vault implementations
/// (Hestia) use this to apply authority + need-to-know policy AND to
/// independently re-derive the signing bytes (defense-in-depth: don't
/// just sign whatever bytes a caller hands you).
///
/// Wire-shape stable across hub ↔ Hestia. Additions to this struct
/// MUST be backward-compatible (use `#[serde(default)]` on new fields).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SignIntent {
    /// Correlation id for matching response to request.
    pub request_id: Uuid,
    /// Which chapter the entry belongs to.
    pub hub_id: Uuid,
    /// Human-readable chapter name (for vault policy / UX prompts).
    pub hub_name: String,
    /// Which actor (role-filler) the signature is being attributed to.
    pub actor_lct_id: Uuid,
    /// Ledger index of the proposed entry.
    pub ledger_index: u64,
    /// Event kind (member_added, role_assigned, ...).
    pub event_kind: String,
    /// Event payload as canonical JSON (vault may re-canonicalize from
    /// here to verify the bytes match).
    pub event: serde_json::Value,
}

/// What the hub posts to a remote signer (Hestia callback).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SignRequest {
    pub intent: SignIntent,
    /// Hex-encoded canonical bytes that the signer is expected to sign.
    /// Vault should re-derive these from `intent` and refuse if they
    /// don't match (the hub could be lying about what the bytes represent).
    pub signing_bytes_hex: String,
}

/// What the remote signer returns.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(untagged)]
pub enum SignResponse {
    Approved {
        request_id: Uuid,
        /// Hex-encoded 64-byte Ed25519 signature.
        signature: String,
    },
    Denied {
        request_id: Uuid,
        denied: bool, // always true; the tag discriminator
        deny_reason: String,
    },
}

/// Why a signer call failed. Distinct from `VerifyError` (envelope
/// verification) — this is about the signing side, not the verifying
/// side.
#[derive(Debug, thiserror::Error)]
pub enum SignError {
    /// Vault explicitly refused (authority+need-to-know gate said no).
    /// Carries the vault's reason string.
    #[error("signer denied: {0}")]
    Denied(String),

    /// Vault accepted but returned an unparseable signature (bad hex,
    /// wrong length, etc.). Indicates a vault bug, not a policy denial.
    #[error("malformed signature from signer: {0}")]
    Malformed(String),

    /// Network / transport error.
    #[error("signer transport error: {0}")]
    Transport(String),

    /// Internal error in the signing pipeline.
    #[error("internal: {0}")]
    Internal(#[from] anyhow::Error),
}

/// Asynchronous remote signer interface.
///
/// Implementations may be in-process (LocalKeypairSigner) or remote
/// (HestiaCallbackSigner, future HSM/cloud-KMS). All callers see the
/// same async contract.
#[async_trait]
pub trait RemoteSigner: Send + Sync {
    /// Sign the given bytes on behalf of `actor_lct_id`. The `intent`
    /// is metadata for vault policy + re-derivation; the canonical
    /// bytes to sign are passed explicitly in `signing_bytes`.
    ///
    /// Implementations SHOULD verify that the bytes match what their
    /// policy expects for the given intent. LocalKeypairSigner doesn't
    /// (it's trusted by construction); HestiaCallbackSigner does (the
    /// hub could have lied).
    async fn sign(
        &self,
        actor_lct_id: Uuid,
        signing_bytes: &[u8],
        intent: &SignIntent,
    ) -> std::result::Result<SignatureBytes, SignError>;

    /// What kind of signer this is, for diagnostics + audit.
    fn signer_kind(&self) -> SignerKind;
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub enum SignerKind {
    /// In-process keypair (MVP). Will be deprecated once Hestia is
    /// fully wired and all chapter Sovereigns are Hestia-LCT-backed.
    LocalKeypair,
    /// Hestia HTTP callback (V2-7 Step 3b.2).
    HestiaCallback,
}

// ============================================================================
// LocalKeypairSigner — in-process keypair, MVP-compatible
// ============================================================================

/// Signer that holds a KeyPair in-process and signs locally.
/// MVP-compatible: lets the existing single-binary chapter operator
/// pattern work without an external Hestia.
///
/// Per architecture commitment #8 this is **deprecated** —- private
/// keys belong in a vault, not in the hub process. V2-7 Step 4 makes
/// Hestia mode the default for new chapters; LocalKeypairSigner stays
/// as a backward-compat path for MVP chapters until they migrate.
pub struct LocalKeypairSigner {
    /// LCT id this keypair signs for. The signer rejects requests whose
    /// `actor_lct_id` doesn't match — defense against mis-routing.
    actor_lct_id: Uuid,
    keypair: KeyPair,
}

impl LocalKeypairSigner {
    pub fn new(actor_lct_id: Uuid, keypair: KeyPair) -> Self {
        Self { actor_lct_id, keypair }
    }
}

#[async_trait]
impl RemoteSigner for LocalKeypairSigner {
    async fn sign(
        &self,
        actor_lct_id: Uuid,
        signing_bytes: &[u8],
        _intent: &SignIntent,
    ) -> std::result::Result<SignatureBytes, SignError> {
        if actor_lct_id != self.actor_lct_id {
            return Err(SignError::Internal(anyhow!(
                "LocalKeypairSigner is bound to actor {} but was asked to sign for {}",
                self.actor_lct_id, actor_lct_id
            )));
        }
        let sig = self.keypair.sign(signing_bytes);
        Ok(SignatureBytes::from_bytes(sig.bytes))
    }

    fn signer_kind(&self) -> SignerKind {
        SignerKind::LocalKeypair
    }
}

// ============================================================================
// HestiaCallbackSigner — POSTs sign-request to a Hestia callback URL
// ============================================================================

/// Default timeout for the sign-request HTTP roundtrip. Long enough
/// for interactive Hestia prompts (human approves on their device),
/// short enough that wedged requests don't pile up on the hub.
pub const DEFAULT_HESTIA_TIMEOUT_SECONDS: u64 = 30;

/// Signer that POSTs a [`SignRequest`] to a Hestia callback URL and
/// awaits the [`SignResponse`]. The Hestia operator's authority +
/// need-to-know gate runs server-side; the hub just delivers the
/// request + receives the result.
///
/// Per architecture commitment #8: this is the path that fully honors
/// the secrets-in-vault rule on the hub side — the hub holds no keys.
///
/// ## Wire shape
///
/// `POST {callback_url}` (the URL is whatever Hestia registered with
/// the hub at `hub init --sovereign-hestia <url>`). Body is a JSON
/// [`SignRequest`]. Response is a JSON [`SignResponse`] (Approved or
/// Denied).
///
/// ## Bound actor
///
/// Like LocalKeypairSigner, this signer is bound to a specific
/// `actor_lct_id` at construction. Hestia's vault may host multiple
/// LCTs; the binding ensures the hub asks the right one. The vault
/// independently verifies the bytes-vs-intent match.
pub struct HestiaCallbackSigner {
    actor_lct_id: Uuid,
    callback_url: String,
    http: reqwest::Client,
}

impl HestiaCallbackSigner {
    pub fn new(actor_lct_id: Uuid, callback_url: impl Into<String>) -> Result<Self> {
        let http = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(DEFAULT_HESTIA_TIMEOUT_SECONDS))
            .build()
            .map_err(|e| anyhow!("building reqwest client: {}", e))?;
        Ok(Self {
            actor_lct_id,
            callback_url: callback_url.into(),
            http,
        })
    }

    pub fn callback_url(&self) -> &str {
        &self.callback_url
    }
}

#[async_trait]
impl RemoteSigner for HestiaCallbackSigner {
    async fn sign(
        &self,
        actor_lct_id: Uuid,
        signing_bytes: &[u8],
        intent: &SignIntent,
    ) -> std::result::Result<SignatureBytes, SignError> {
        if actor_lct_id != self.actor_lct_id {
            return Err(SignError::Internal(anyhow!(
                "HestiaCallbackSigner bound to actor {} but asked to sign for {}",
                self.actor_lct_id, actor_lct_id
            )));
        }

        let request = SignRequest {
            intent: intent.clone(),
            signing_bytes_hex: hex::encode(signing_bytes),
        };

        let response = self.http
            .post(&self.callback_url)
            .json(&request)
            .send()
            .await
            .map_err(|e| SignError::Transport(format!("POST {}: {}", self.callback_url, e)))?;

        if !response.status().is_success() {
            let status = response.status();
            let body = response.text().await.unwrap_or_default();
            return Err(SignError::Transport(format!(
                "callback returned HTTP {}: {}", status, body
            )));
        }

        let parsed: SignResponse = response.json().await
            .map_err(|e| SignError::Malformed(format!("parsing response: {}", e)))?;

        match parsed {
            SignResponse::Denied { deny_reason, .. } => Err(SignError::Denied(deny_reason)),
            SignResponse::Approved { signature, .. } => {
                let sig_bytes = hex::decode(&signature)
                    .map_err(|e| SignError::Malformed(format!("hex decode: {}", e)))?;
                let arr: [u8; 64] = sig_bytes.as_slice().try_into()
                    .map_err(|_| SignError::Malformed("signature must be 64 bytes".into()))?;
                Ok(SignatureBytes::from_bytes(arr))
            }
        }
    }

    fn signer_kind(&self) -> SignerKind {
        SignerKind::HestiaCallback
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::identity::IdentityFile;
    use serde_json::json;
    use web4_core::lct::EntityType;

    fn fresh_actor() -> (IdentityFile, KeyPair) {
        let id = IdentityFile::generate(EntityType::Human);
        let kp = id.keypair().unwrap();
        (id, kp)
    }

    fn intent(actor_id: Uuid) -> SignIntent {
        SignIntent {
            request_id: Uuid::new_v4(),
            hub_id: Uuid::new_v4(),
            hub_name: "Test".into(),
            actor_lct_id: actor_id,
            ledger_index: 0,
            event_kind: "test".into(),
            event: json!({}),
        }
    }

    #[tokio::test]
    async fn local_signer_signs_and_verifies() {
        let (id, kp) = fresh_actor();
        let signer = LocalKeypairSigner::new(id.lct.id, kp);
        let bytes = b"some signing bytes";
        let sig = signer.sign(id.lct.id, bytes, &intent(id.lct.id)).await.unwrap();
        id.lct.verify_signature(bytes, &sig).unwrap();
        assert_eq!(signer.signer_kind(), SignerKind::LocalKeypair);
    }

    #[tokio::test]
    async fn local_signer_rejects_wrong_actor() {
        let (id, kp) = fresh_actor();
        let other_actor = Uuid::new_v4();
        let signer = LocalKeypairSigner::new(id.lct.id, kp);
        let result = signer.sign(other_actor, b"bytes", &intent(other_actor)).await;
        assert!(matches!(result, Err(SignError::Internal(_))));
    }

    #[tokio::test]
    async fn local_signer_via_dyn_trait() {
        // Exercise the trait-object path (dyn RemoteSigner) the way the
        // hub will hold it — Box<dyn RemoteSigner>.
        let (id, kp) = fresh_actor();
        let signer: Box<dyn RemoteSigner> = Box::new(LocalKeypairSigner::new(id.lct.id, kp));
        let sig = signer.sign(id.lct.id, b"bytes", &intent(id.lct.id)).await.unwrap();
        id.lct.verify_signature(b"bytes", &sig).unwrap();
    }

    // ---------- HestiaCallbackSigner integration tests ----------
    //
    // These spin up a tiny axum server in-process that emulates Hestia's
    // sign-request endpoint, then drive HestiaCallbackSigner against it.
    // Real Hestia (Track H) implements the same wire shape; these tests
    // are the canonical hub-side proof that the wire works.

    use axum::{routing::post, Router};
    use std::sync::Arc;
    use tokio::sync::oneshot;

    /// Mock Hestia state: which keypair to sign with + a policy hook.
    #[derive(Clone)]
    struct MockHestia {
        actor_lct_id: Uuid,
        keypair: Arc<KeyPair>,
        deny_reason: Option<String>,
    }

    async fn mock_sign_handler(
        axum::extract::State(state): axum::extract::State<MockHestia>,
        axum::Json(req): axum::Json<SignRequest>,
    ) -> axum::Json<SignResponse> {
        if let Some(reason) = &state.deny_reason {
            return axum::Json(SignResponse::Denied {
                request_id: req.intent.request_id,
                denied: true,
                deny_reason: reason.clone(),
            });
        }
        let bytes = hex::decode(&req.signing_bytes_hex).expect("hex bytes");
        let sig = state.keypair.sign(&bytes);
        axum::Json(SignResponse::Approved {
            request_id: req.intent.request_id,
            signature: hex::encode(sig.bytes),
        })
    }

    async fn spawn_mock_hestia(state: MockHestia) -> (String, oneshot::Sender<()>) {
        let app = Router::new()
            .route("/sign-request", post(mock_sign_handler))
            .with_state(state);
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap();
        let (tx, rx) = oneshot::channel::<()>();
        tokio::spawn(async move {
            axum::serve(listener, app)
                .with_graceful_shutdown(async {
                    let _ = rx.await;
                })
                .await
                .ok();
        });
        // Small grace for the listener to start accepting
        tokio::time::sleep(std::time::Duration::from_millis(50)).await;
        (format!("http://{}/sign-request", addr), tx)
    }

    #[tokio::test(flavor = "multi_thread")]
    async fn hestia_callback_signs_and_verifies() {
        let (id, kp) = fresh_actor();
        let mock = MockHestia {
            actor_lct_id: id.lct.id,
            keypair: Arc::new(kp),
            deny_reason: None,
        };
        let (url, stop) = spawn_mock_hestia(mock).await;

        let signer = HestiaCallbackSigner::new(id.lct.id, url).unwrap();
        let bytes = b"some ledger entry signing bytes";
        let sig = signer.sign(id.lct.id, bytes, &intent(id.lct.id)).await.unwrap();

        // The mock signed with the real keypair, so the LCT's pubkey
        // must verify the signature against the bytes.
        id.lct.verify_signature(bytes, &sig).unwrap();
        assert_eq!(signer.signer_kind(), SignerKind::HestiaCallback);

        let _ = stop.send(());
    }

    #[tokio::test(flavor = "multi_thread")]
    async fn hestia_callback_denied_returns_denied() {
        let (id, kp) = fresh_actor();
        let mock = MockHestia {
            actor_lct_id: id.lct.id,
            keypair: Arc::new(kp),
            deny_reason: Some("policy: chapter not whitelisted".into()),
        };
        let (url, stop) = spawn_mock_hestia(mock).await;

        let signer = HestiaCallbackSigner::new(id.lct.id, url).unwrap();
        let result = signer.sign(id.lct.id, b"bytes", &intent(id.lct.id)).await;
        match result {
            Err(SignError::Denied(reason)) => assert!(reason.contains("policy")),
            other => panic!("expected Denied, got {:?}", other),
        }

        let _ = stop.send(());
    }

    #[tokio::test(flavor = "multi_thread")]
    async fn hestia_callback_unreachable_url_errors_transport() {
        // No server running on this port — connection refused
        let (id, _) = fresh_actor();
        let signer = HestiaCallbackSigner::new(id.lct.id, "http://127.0.0.1:1/sign-request").unwrap();
        let result = signer.sign(id.lct.id, b"bytes", &intent(id.lct.id)).await;
        assert!(matches!(result, Err(SignError::Transport(_))));
    }

    #[tokio::test]
    async fn hestia_callback_wrong_actor_errors_internal() {
        let (id, _kp) = fresh_actor();
        let signer = HestiaCallbackSigner::new(id.lct.id, "http://unused").unwrap();
        let other_actor = Uuid::new_v4();
        let result = signer.sign(other_actor, b"bytes", &intent(other_actor)).await;
        assert!(matches!(result, Err(SignError::Internal(_))));
    }

    #[tokio::test]
    async fn sign_response_serde_round_trips() {
        let approved = SignResponse::Approved {
            request_id: Uuid::new_v4(),
            signature: "ab".repeat(64),
        };
        let json = serde_json::to_string(&approved).unwrap();
        let back: SignResponse = serde_json::from_str(&json).unwrap();
        match back {
            SignResponse::Approved { signature, .. } => assert_eq!(signature.len(), 128),
            _ => panic!("expected Approved"),
        }

        let denied = SignResponse::Denied {
            request_id: Uuid::new_v4(),
            denied: true,
            deny_reason: "policy: amount too high".into(),
        };
        let json = serde_json::to_string(&denied).unwrap();
        let back: SignResponse = serde_json::from_str(&json).unwrap();
        match back {
            SignResponse::Denied { deny_reason, .. } => assert!(deny_reason.contains("policy")),
            _ => panic!("expected Denied"),
        }
    }
}
