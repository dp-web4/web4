// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! SD-JWT-VC issuance — Web4 attestations as selectively-disclosable
//! Verifiable Credentials (EUDI / IETF interop, Phase 1).
//!
//! Implements the issuance half of IETF SD-JWT (`draft-ietf-oauth-
//! selective-disclosure-jwt`) + SD-JWT-VC (`draft-ietf-oauth-sd-jwt-vc`):
//! a JWT whose selected claims are replaced by salted digests (`_sd`), with the
//! cleartext carried in detached *disclosures*. The holder presents only the
//! disclosures it chooses; the issuer signature still verifies.
//!
//! The issuer is an LCT (identified by a `did:web4` / `did:web`), signing with
//! its Ed25519 key (`EdDSA` JWS). This is the bridge from a Web4 attestation
//! into a wallet-consumable credential — lossy by design (the rich witness
//! structure collapses to signed claims; see `docs/strategy/
//! eudi-resolvability-plan.md`).
//!
//! Generic and public-eligible: no novel mechanism, just the standard format.
//!
//! Compact serialization: `<JWS>~<disclosure>~<disclosure>~` (trailing `~`;
//! a holder Key-Binding JWT is appended after the last `~` at presentation).

use crate::crypto::{KeyPair, PublicKey, SignatureBytes};
use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine;
use rand::RngCore;
use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

fn b64(bytes: &[u8]) -> String {
    URL_SAFE_NO_PAD.encode(bytes)
}
fn unb64(s: &str) -> Result<Vec<u8>, String> {
    URL_SAFE_NO_PAD.decode(s).map_err(|e| e.to_string())
}

/// A salted disclosure for one object claim: `[salt, name, value]`.
#[derive(Clone, Debug)]
pub struct Disclosure {
    pub salt: String,
    pub name: String,
    pub value: Value,
}

impl Disclosure {
    pub fn new(name: impl Into<String>, value: Value) -> Self {
        let mut salt_bytes = [0u8; 16];
        rand::thread_rng().fill_bytes(&mut salt_bytes);
        Self { salt: b64(&salt_bytes), name: name.into(), value }
    }

    /// Deterministic salt — for tests and reproducible issuance.
    pub fn with_salt(salt: impl Into<String>, name: impl Into<String>, value: Value) -> Self {
        Self { salt: salt.into(), name: name.into(), value }
    }

    /// The base64url(JSON `[salt, name, value]`) disclosure string.
    pub fn encoded(&self) -> String {
        let arr = json!([self.salt, self.name, self.value]);
        b64(serde_json::to_string(&arr).expect("disclosure serializes").as_bytes())
    }

    /// The `_sd` digest: base64url(SHA-256(ASCII(encoded))).
    pub fn digest(&self) -> String {
        let enc = self.encoded();
        b64(&Sha256::digest(enc.as_bytes()))
    }
}

/// Builder for an SD-JWT-VC.
pub struct SdJwtVc {
    vct: String,
    issuer: String,
    typ: String,
    iat: i64,
    /// Optional holder key binding (`cnf`) — the holder's public key, multibase.
    cnf_holder_multikey: Option<String>,
    plain: Map<String, Value>,
    disclosures: Vec<Disclosure>,
}

impl SdJwtVc {
    /// `vct` = credential type (e.g. "Web4Presence"); `issuer` = the issuer DID.
    pub fn new(vct: impl Into<String>, issuer: impl Into<String>) -> Self {
        Self {
            vct: vct.into(),
            issuer: issuer.into(),
            // The IETF SD-JWT-VC draft is renaming `vc+sd-jwt` → `dc+sd-jwt`
            // ("Digital Credential"). `vc+sd-jwt` is the most widely deployed
            // value; override with `.typ()` for newer verifiers.
            typ: "vc+sd-jwt".to_string(),
            iat: chrono::Utc::now().timestamp(),
            cnf_holder_multikey: None,
            plain: Map::new(),
            disclosures: Vec::new(),
        }
    }

    pub fn typ(mut self, typ: impl Into<String>) -> Self {
        self.typ = typ.into();
        self
    }
    /// Override issued-at (unix seconds) — for reproducible issuance/tests.
    pub fn iat(mut self, iat: i64) -> Self {
        self.iat = iat;
        self
    }
    /// Bind the credential to a holder key (`cnf`) — the holder's Ed25519
    /// public key as a multibase string. Enables holder Key-Binding at present.
    pub fn holder_binding(mut self, holder_multikey: impl Into<String>) -> Self {
        self.cnf_holder_multikey = Some(holder_multikey.into());
        self
    }

    /// An always-disclosed claim (appears in cleartext in the JWT payload).
    pub fn claim(mut self, name: impl Into<String>, value: Value) -> Self {
        self.plain.insert(name.into(), value);
        self
    }

    /// A selectively-disclosable claim (replaced by a digest; cleartext in a
    /// detached disclosure the holder may withhold).
    pub fn sd_claim(mut self, name: impl Into<String>, value: Value) -> Self {
        self.disclosures.push(Disclosure::new(name, value));
        self
    }

    /// SD claim with a fixed salt — reproducible issuance/tests.
    pub fn sd_claim_salted(
        mut self,
        salt: impl Into<String>,
        name: impl Into<String>,
        value: Value,
    ) -> Self {
        self.disclosures.push(Disclosure::with_salt(salt, name, value));
        self
    }

    /// Issue: build + sign the JWS and emit the compact SD-JWT-VC.
    /// `kid` is the issuer verification method id (e.g. `<did>#key-0`).
    pub fn issue(&self, issuer_key: &KeyPair, kid: &str) -> String {
        // Digests, sorted so order doesn't leak insertion sequence.
        let mut digests: Vec<String> = self.disclosures.iter().map(|d| d.digest()).collect();
        digests.sort();

        let mut payload = self.plain.clone();
        payload.insert("iss".into(), json!(self.issuer));
        payload.insert("vct".into(), json!(self.vct));
        payload.insert("iat".into(), json!(self.iat));
        payload.insert("_sd_alg".into(), json!("sha-256"));
        payload.insert("_sd".into(), json!(digests));
        if let Some(h) = &self.cnf_holder_multikey {
            payload.insert("cnf".into(), json!({ "kid": h }));
        }

        let header = json!({ "alg": "EdDSA", "typ": self.typ, "kid": kid });
        let header_b64 = b64(serde_json::to_string(&header).unwrap().as_bytes());
        let payload_b64 = b64(serde_json::to_string(&Value::Object(payload)).unwrap().as_bytes());
        let signing_input = format!("{header_b64}.{payload_b64}");
        let sig = issuer_key.sign(signing_input.as_bytes());
        let jws = format!("{signing_input}.{}", b64(&sig.bytes));

        // JWS ~ disclosures ~ (trailing tilde; KB-JWT slot left empty)
        let mut out = jws;
        for d in &self.disclosures {
            out.push('~');
            out.push_str(&d.encoded());
        }
        out.push('~');
        out
    }
}

/// The result of verifying an SD-JWT-VC: the issuer-signed claims, with the
/// presented disclosures merged back in.
#[derive(Clone, Debug)]
pub struct VerifiedCredential {
    pub vct: String,
    pub issuer: String,
    pub claims: Map<String, Value>,
}

/// Verify the issuer signature and reconstruct the disclosed claims.
///
/// - Verifies the EdDSA JWS against `issuer_pubkey`.
/// - For each presented disclosure: recomputes its digest, requires it to be in
///   the JWT's `_sd`, and merges `name → value` into the result.
/// - Always-disclosed claims pass through. Withheld disclosures simply don't
///   appear (selective disclosure). A disclosure whose digest isn't in `_sd`
///   is rejected (tamper).
pub fn verify_issuer(compact: &str, issuer_pubkey: &PublicKey) -> Result<VerifiedCredential, String> {
    let mut parts = compact.split('~');
    let jws = parts.next().ok_or("empty credential")?;
    // remaining parts are disclosures; a trailing '~' yields a final empty part
    // and the (unused here) KB-JWT slot.
    let disclosures: Vec<&str> = parts.filter(|p| !p.is_empty()).collect();

    // 1. JWS signature
    let jp: Vec<&str> = jws.split('.').collect();
    if jp.len() != 3 {
        return Err("malformed JWS".into());
    }
    let signing_input = format!("{}.{}", jp[0], jp[1]);
    let sig_raw = unb64(jp[2])?;
    let sig_arr: [u8; 64] = sig_raw.as_slice().try_into().map_err(|_| "bad sig length")?;
    issuer_pubkey
        .verify(signing_input.as_bytes(), &SignatureBytes::from_bytes(sig_arr))
        .map_err(|_| "issuer signature invalid".to_string())?;

    // 2. payload
    let payload: Value = serde_json::from_slice(&unb64(jp[1])?).map_err(|e| e.to_string())?;
    let obj = payload.as_object().ok_or("payload not an object")?;
    let sd: Vec<String> = obj
        .get("_sd")
        .and_then(|v| v.as_array())
        .map(|a| a.iter().filter_map(|x| x.as_str().map(String::from)).collect())
        .unwrap_or_default();

    // 3. reconstruct claims: start from cleartext (minus protocol fields)
    let mut claims = Map::new();
    for (k, v) in obj {
        if !matches!(k.as_str(), "_sd" | "_sd_alg") {
            claims.insert(k.clone(), v.clone());
        }
    }

    // 4. merge presented disclosures whose digest is in `_sd`
    for enc in disclosures {
        let digest = b64(&Sha256::digest(enc.as_bytes()));
        if !sd.contains(&digest) {
            return Err(format!("disclosure digest not in _sd (tamper?): {enc}"));
        }
        let raw = unb64(enc)?;
        let arr: Value = serde_json::from_slice(&raw).map_err(|e| e.to_string())?;
        let a = arr.as_array().ok_or("disclosure not an array")?;
        if a.len() != 3 {
            return Err("object disclosure must be [salt, name, value]".into());
        }
        let name = a[1].as_str().ok_or("disclosure name not a string")?;
        claims.insert(name.to_string(), a[2].clone());
    }

    Ok(VerifiedCredential {
        vct: obj.get("vct").and_then(|v| v.as_str()).unwrap_or_default().to_string(),
        issuer: obj.get("iss").and_then(|v| v.as_str()).unwrap_or_default().to_string(),
        claims,
    })
}

// ─────────────── Web4 credential helpers (the pattern, not the policy) ───────────────

/// Build a `Web4Presence` SD-JWT-VC: an assurance attestation about a subject,
/// with the assurance level selectively-disclosable. Inputs are primitives
/// (no hestia/witness types) so web4-core stays dependency-clean.
pub fn web4_presence_credential(
    issuer_did: &str,
    subject_did: &str,
    assurance_level: &str,
) -> SdJwtVc {
    SdJwtVc::new("Web4Presence", issuer_did)
        .claim("sub", json!(subject_did))
        .sd_claim("assurance_level", json!(assurance_level))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_issue_and_verify_roundtrip() {
        let issuer = KeyPair::generate();
        let pk = issuer.verifying_key();

        let compact = SdJwtVc::new("Web4Presence", "did:web4:hub.example.com:abc")
            .iat(1_700_000_000)
            .claim("sub", json!("did:web4:hub.example.com:def"))
            .sd_claim_salted("salt1", "assurance_level", json!("multi_device"))
            .sd_claim_salted("salt2", "github", json!("https://github.com/dp-web4"))
            .issue(&issuer, "did:web4:hub.example.com:abc#key-0");

        let v = verify_issuer(&compact, &pk).expect("must verify");
        assert_eq!(v.vct, "Web4Presence");
        assert_eq!(v.issuer, "did:web4:hub.example.com:abc");
        // cleartext claim present
        assert_eq!(v.claims.get("sub").unwrap(), &json!("did:web4:hub.example.com:def"));
        // both SD claims reconstructed
        assert_eq!(v.claims.get("assurance_level").unwrap(), &json!("multi_device"));
        assert_eq!(v.claims.get("github").unwrap(), &json!("https://github.com/dp-web4"));
    }

    #[test]
    fn test_selective_disclosure() {
        let issuer = KeyPair::generate();
        let pk = issuer.verifying_key();
        let compact = SdJwtVc::new("Web4Presence", "did:iss")
            .sd_claim_salted("s1", "assurance_level", json!("hardware_backed"))
            .sd_claim_salted("s2", "email", json!("dp@metalinxx.io"))
            .issue(&issuer, "did:iss#key-0");

        // Holder presents ONLY the assurance disclosure, withholds email.
        let jws_and_first = {
            let mut it = compact.split('~');
            let jws = it.next().unwrap();
            // find the assurance disclosure (the one decoding to "assurance_level")
            let discs: Vec<&str> = it.filter(|p| !p.is_empty()).collect();
            let keep = discs.iter().find(|d| {
                let raw = unb64(d).unwrap();
                let a: Value = serde_json::from_slice(&raw).unwrap();
                a[1] == json!("assurance_level")
            }).unwrap();
            format!("{jws}~{keep}~")
        };

        let v = verify_issuer(&jws_and_first, &pk).expect("partial presentation verifies");
        assert_eq!(v.claims.get("assurance_level").unwrap(), &json!("hardware_backed"));
        assert!(!v.claims.contains_key("email")); // withheld
    }

    #[test]
    fn test_wrong_issuer_key_rejected() {
        let issuer = KeyPair::generate();
        let imposter = KeyPair::generate();
        let compact = SdJwtVc::new("Web4Presence", "did:iss")
            .sd_claim_salted("s1", "x", json!(1))
            .issue(&issuer, "did:iss#key-0");
        assert!(verify_issuer(&compact, &imposter.verifying_key()).is_err());
    }

    #[test]
    fn test_tampered_disclosure_rejected() {
        let issuer = KeyPair::generate();
        let pk = issuer.verifying_key();
        let compact = SdJwtVc::new("Web4Presence", "did:iss")
            .sd_claim_salted("s1", "assurance_level", json!("single_device"))
            .issue(&issuer, "did:iss#key-0");

        // Forge a disclosure claiming hardware_backed and splice it in.
        let forged = Disclosure::with_salt("s1", "assurance_level", json!("hardware_backed")).encoded();
        let jws = compact.split('~').next().unwrap();
        let tampered = format!("{jws}~{forged}~");
        // its digest won't be in _sd → rejected
        assert!(verify_issuer(&tampered, &pk).is_err());
    }

    #[test]
    fn test_holder_binding_in_payload() {
        let issuer = KeyPair::generate();
        let compact = SdJwtVc::new("Web4Presence", "did:iss")
            .holder_binding("z6MkHolderKey")
            .claim("sub", json!("did:holder"))
            .issue(&issuer, "did:iss#key-0");
        // cnf present in the signed payload
        let payload_b64 = compact.split('~').next().unwrap().split('.').nth(1).unwrap();
        let payload: Value = serde_json::from_slice(&unb64(payload_b64).unwrap()).unwrap();
        assert_eq!(payload["cnf"]["kid"], json!("z6MkHolderKey"));
    }

    #[test]
    fn test_web4_presence_helper() {
        let issuer = KeyPair::generate();
        let pk = issuer.verifying_key();
        let compact = web4_presence_credential("did:iss", "did:sub", "multi_device")
            .issue(&issuer, "did:iss#key-0");
        let v = verify_issuer(&compact, &pk).unwrap();
        assert_eq!(v.vct, "Web4Presence");
        assert_eq!(v.claims.get("sub").unwrap(), &json!("did:sub"));
        assert_eq!(v.claims.get("assurance_level").unwrap(), &json!("multi_device"));
    }
}
