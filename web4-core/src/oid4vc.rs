// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! OpenID4VCI / OpenID4VP protocol types + reference flows (EUDI Phase 2).
//!
//! The transport layer that carries Web4 SD-JWT-VCs to and from wallets:
//! - **OID4VCI** (issuance): the issuer offers a credential; the wallet pulls it
//!   with a holder-key proof. We model the **pre-authorized-code** grant — the
//!   simplest conformant flow, no full OAuth dance.
//! - **OID4VP** (presentation): the verifier requests a presentation with a
//!   nonce; the wallet returns a VP token (the SD-JWT-VC + holder KB-JWT bound to
//!   that nonce + audience).
//!
//! This module owns the **wire message shapes + the verification logic**; the
//! HTTP endpoints (in the hub / hestia daemon) are thin wrappers that
//! deserialize a request, call into here, and serialize the result. Everything
//! is testable in-memory without a server.
//!
//! Generic / public-eligible: standard OpenID4VC shapes, no novel mechanism.

use crate::crypto::{KeyPair, PublicKey, SignatureBytes};
use crate::sd_jwt_vc::{present, verify_presentation, VerifiedCredential};
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn b64(bytes: &[u8]) -> String {
    URL_SAFE_NO_PAD.encode(bytes)
}
fn unb64(s: &str) -> Result<Vec<u8>, String> {
    URL_SAFE_NO_PAD.decode(s).map_err(|e| e.to_string())
}

// ════════════════════════ OID4VCI (issuance) ════════════════════════

/// Issuer metadata — served at `/.well-known/openid-credential-issuer`.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CredentialIssuerMetadata {
    pub credential_issuer: String,
    pub credential_endpoint: String,
    /// Map of credential-config-id → its `vct` / format descriptor.
    pub credential_configurations_supported: Value,
}

impl CredentialIssuerMetadata {
    /// Minimal metadata advertising one SD-JWT-VC type.
    pub fn for_vct(issuer: &str, vct: &str) -> Self {
        Self {
            credential_issuer: issuer.to_string(),
            credential_endpoint: format!("{issuer}/credential"),
            credential_configurations_supported: json!({
                vct: { "format": "vc+sd-jwt", "vct": vct }
            }),
        }
    }
}

/// A Credential Offer (pre-authorized-code grant) — the issuer hands this to the
/// wallet (QR / link). The `pre_authorized_code` is single-use and binds the
/// subject the issuer will credential.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CredentialOffer {
    pub credential_issuer: String,
    pub credential_configuration_ids: Vec<String>,
    /// `grants["urn:ietf:params:oauth:grant-type:pre-authorized_code"]`
    pub pre_authorized_code: String,
}

/// The wallet's Credential Request: an access token (= the redeemed pre-auth
/// code, in this minimal flow) + a **holder-key proof** (`jwt` proof type) so
/// the issued credential can be `cnf`-bound to the holder.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CredentialRequest {
    pub credential_configuration_id: String,
    /// The holder key-possession proof JWT (`typ: openid4vci-proof+jwt`).
    pub proof_jwt: String,
}

/// Build a holder key-possession proof JWT (wallet side). Binds to the issuer
/// (`aud`) and a `c_nonce` the issuer supplied, signed by the holder key. The
/// holder's public key travels in the JWT header (`jwk`) so the issuer can both
/// verify the proof and `cnf`-bind the credential to it.
pub fn build_holder_proof(
    holder_key: &KeyPair,
    issuer: &str,
    c_nonce: &str,
    now: i64,
) -> String {
    let pk = holder_key.verifying_key().to_bytes();
    let header = json!({
        "alg": "EdDSA",
        "typ": "openid4vci-proof+jwt",
        "jwk": { "kty": "OKP", "crv": "Ed25519", "x": b64(&pk) }
    });
    let payload = json!({ "aud": issuer, "iat": now, "nonce": c_nonce });
    let h = b64(serde_json::to_string(&header).unwrap().as_bytes());
    let p = b64(serde_json::to_string(&payload).unwrap().as_bytes());
    let signing = format!("{h}.{p}");
    let sig = holder_key.sign(signing.as_bytes());
    format!("{signing}.{}", b64(&sig.bytes))
}

/// Issuer side: verify a holder proof JWT against the expected `c_nonce` +
/// `aud`, returning the holder's public key (to `cnf`-bind the credential).
pub fn verify_holder_proof(
    proof_jwt: &str,
    expected_issuer_aud: &str,
    expected_c_nonce: &str,
    max_age_secs: i64,
    now: i64,
) -> Result<PublicKey, String> {
    let parts: Vec<&str> = proof_jwt.split('.').collect();
    if parts.len() != 3 {
        return Err("malformed proof JWT".into());
    }
    let header: Value = serde_json::from_slice(&unb64(parts[0])?).map_err(|e| e.to_string())?;
    let x = header.get("jwk").and_then(|j| j.get("x")).and_then(|x| x.as_str())
        .ok_or("proof header missing holder jwk")?;
    let raw = unb64(x)?;
    let arr: [u8; 32] = raw.as_slice().try_into().map_err(|_| "bad holder key length")?;
    let holder_pk = PublicKey::from_bytes(&arr).map_err(|e| e.to_string())?;

    let signing = format!("{}.{}", parts[0], parts[1]);
    let sig_raw = unb64(parts[2])?;
    let sig_arr: [u8; 64] = sig_raw.as_slice().try_into().map_err(|_| "bad proof sig length")?;
    holder_pk.verify(signing.as_bytes(), &SignatureBytes::from_bytes(sig_arr))
        .map_err(|_| "holder proof signature invalid".to_string())?;

    let payload: Value = serde_json::from_slice(&unb64(parts[1])?).map_err(|e| e.to_string())?;
    if payload.get("aud").and_then(|v| v.as_str()) != Some(expected_issuer_aud) {
        return Err("proof aud mismatch".into());
    }
    if payload.get("nonce").and_then(|v| v.as_str()) != Some(expected_c_nonce) {
        return Err("proof c_nonce mismatch (replay?)".into());
    }
    let iat = payload.get("iat").and_then(|v| v.as_i64()).ok_or("proof missing iat")?;
    if now.saturating_sub(iat) > max_age_secs {
        return Err("proof expired".into());
    }
    Ok(holder_pk)
}

// ════════════════════════ OID4VP (presentation) ════════════════════════

/// The verifier's Authorization Request — sent to the wallet. Carries the
/// `nonce` the holder KB-JWT must bind to and the `response_uri` to POST to.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PresentationRequest {
    pub client_id: String,
    pub nonce: String,
    pub response_uri: String,
    /// What the verifier wants — a `vct` + required claim names (simplified DCQL).
    pub vct: String,
    #[serde(default)]
    pub required_claims: Vec<String>,
}

impl PresentationRequest {
    pub fn new(client_id: &str, nonce: &str, response_uri: &str, vct: &str) -> Self {
        Self {
            client_id: client_id.to_string(),
            nonce: nonce.to_string(),
            response_uri: response_uri.to_string(),
            vct: vct.to_string(),
            required_claims: Vec::new(),
        }
    }
    pub fn requiring(mut self, claims: &[&str]) -> Self {
        self.required_claims = claims.iter().map(|s| s.to_string()).collect();
        self
    }
}

/// The wallet's Authorization Response: the VP token (the presented SD-JWT-VC
/// with holder KB-JWT).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PresentationResponse {
    pub vp_token: String,
}

/// Wallet side: build a presentation response for `req`, revealing the
/// requested claims, binding the KB-JWT to the verifier's nonce + client_id.
pub fn build_presentation(
    issued_compact: &str,
    holder_key: &KeyPair,
    req: &PresentationRequest,
    now: i64,
) -> Result<PresentationResponse, String> {
    let disclose: Vec<&str> = req.required_claims.iter().map(|s| s.as_str()).collect();
    let vp = present(
        issued_compact,
        holder_key,
        &req.nonce,
        &req.client_id,
        now,
        if disclose.is_empty() { None } else { Some(&disclose) },
    )?;
    Ok(PresentationResponse { vp_token: vp })
}

/// Verifier side: validate the wallet's response. Checks issuer signature,
/// holder KB-JWT (bound to our nonce + client_id), and that the credential's
/// `vct` + required claims are present. Returns the verified claims.
pub fn verify_presentation_response(
    resp: &PresentationResponse,
    req: &PresentationRequest,
    issuer_pubkey: &PublicKey,
    max_age_secs: i64,
    now: i64,
) -> Result<VerifiedCredential, String> {
    let cred = verify_presentation(
        &resp.vp_token,
        issuer_pubkey,
        &req.nonce,
        &req.client_id,
        max_age_secs,
        now,
    )?;
    if cred.vct != req.vct {
        return Err(format!("vct mismatch: wanted {}, got {}", req.vct, cred.vct));
    }
    for claim in &req.required_claims {
        if !cred.claims.contains_key(claim) {
            return Err(format!("required claim '{claim}' not disclosed"));
        }
    }
    Ok(cred)
}

/// SHA-256 hex helper (for opaque single-use codes/nonces in a daemon store).
pub fn opaque_token(seed: &[u8]) -> String {
    hex_lower(&Sha256::digest(seed))
}
fn hex_lower(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sd_jwt_vc::SdJwtVc;

    // The full Phase-2 round trip: issue (with holder proof) → present → verify.
    #[test]
    fn full_vci_then_vp_roundtrip() {
        let issuer_key = KeyPair::generate();
        let holder_key = KeyPair::generate();
        let issuer = "https://hub.example.com/v1";

        // ---- OID4VCI ----
        // Issuer offers; wallet redeems pre-auth code and proves holder key.
        let c_nonce = "issuer-c-nonce";
        let proof = build_holder_proof(&holder_key, issuer, c_nonce, 1000);
        // Issuer verifies the proof → gets the holder pubkey to cnf-bind.
        let holder_pk = verify_holder_proof(&proof, issuer, c_nonce, 300, 1000).unwrap();
        assert_eq!(holder_pk.to_bytes(), holder_key.verifying_key().to_bytes());

        // Issuer mints the credential bound to that holder key.
        let issued = SdJwtVc::new("Web4Presence", issuer)
            .holder_binding(&holder_pk)
            .claim("sub", json!("did:web4:hub.example.com:holder"))
            .sd_claim_salted("s1", "assurance_level", json!("hardware_backed"))
            .sd_claim_salted("s2", "email", json!("dp@metalinxx.io"))
            .issue(&issuer_key, &format!("{issuer}#key-0"));

        // ---- OID4VP ----
        // Verifier requests Web4Presence with assurance_level, fresh nonce.
        let req = PresentationRequest::new("did:verifier", "vp-nonce-1",
            "https://verifier.example/response", "Web4Presence")
            .requiring(&["assurance_level"]);

        // Wallet builds the response (reveals only assurance_level + always-disclosed).
        let resp = build_presentation(&issued, &holder_key, &req, 2000).unwrap();

        // Verifier validates everything.
        let cred = verify_presentation_response(&resp, &req, &issuer_key.verifying_key(), 300, 2050).unwrap();
        assert_eq!(cred.vct, "Web4Presence");
        assert_eq!(cred.claims.get("assurance_level").unwrap(), &json!("hardware_backed"));
        assert!(!cred.claims.contains_key("email")); // withheld
        assert!(cred.claims.contains_key("sub"));
    }

    #[test]
    fn holder_proof_replay_rejected() {
        let holder = KeyPair::generate();
        let proof = build_holder_proof(&holder, "iss", "nonce-A", 1000);
        // wrong c_nonce → reject
        assert!(verify_holder_proof(&proof, "iss", "nonce-B", 300, 1000).is_err());
        // wrong aud → reject
        assert!(verify_holder_proof(&proof, "other", "nonce-A", 300, 1000).is_err());
        // expired → reject
        assert!(verify_holder_proof(&proof, "iss", "nonce-A", 300, 9_999_999).is_err());
    }

    #[test]
    fn vp_missing_required_claim_rejected() {
        let issuer_key = KeyPair::generate();
        let holder = KeyPair::generate();
        let issued = SdJwtVc::new("Web4Presence", "iss")
            .holder_binding(&holder.verifying_key())
            .sd_claim_salted("s1", "assurance_level", json!("single_device"))
            .issue(&issuer_key, "iss#key-0");

        // Verifier requires `email`, which the holder doesn't reveal.
        let req = PresentationRequest::new("v", "n", "uri", "Web4Presence").requiring(&["email"]);
        let resp = build_presentation(&issued, &holder, &req, 1000).unwrap();
        let r = verify_presentation_response(&resp, &req, &issuer_key.verifying_key(), 300, 1000);
        assert!(r.is_err()); // email not disclosed
    }

    #[test]
    fn issuer_metadata_and_offer_serialize() {
        let md = CredentialIssuerMetadata::for_vct("https://hub/v1", "Web4Presence");
        let j = serde_json::to_string(&md).unwrap();
        assert!(j.contains("credential_endpoint"));
        assert!(j.contains("Web4Presence"));

        let offer = CredentialOffer {
            credential_issuer: "https://hub/v1".into(),
            credential_configuration_ids: vec!["Web4Presence".into()],
            pre_authorized_code: opaque_token(b"seed"),
        };
        let back: CredentialOffer = serde_json::from_str(&serde_json::to_string(&offer).unwrap()).unwrap();
        assert_eq!(back.credential_configuration_ids, vec!["Web4Presence".to_string()]);
    }
}
