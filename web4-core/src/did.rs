// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! `did:web4` — the W3C DID interop face of an LCT.
//!
//! Projects an LCT into a conformant DID Document (identifier + keys +
//! endpoints) so the existing DID / VC / EUDI ecosystem can resolve a Web4
//! entity. The DID Document is a *lossy view* — the identifier-and-keys slice;
//! Web4's trust/relationship layer (T3/V3, MRH, witnessing, ATP) has no DID
//! representation by design and is reached only via the `Web4Hub` service.
//!
//! Design note: `docs/designs/did-web4-mapping.md`. This module is generic and
//! public-eligible — it exposes only what DID standardizes; no novel mechanism.
//!
//! Identifier syntax: `did:web4:<authority>:<lct-uuid>`, where `<authority>` is
//! the resolving hub host. Resolution returns a hub-signed pubkey binding,
//! making `did:web4` resolution *attested* (vs `did:web`'s TLS-only trust).

use crate::lct::{Lct, LctStatus};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Build a `did:web4` identifier string.
pub fn did_web4(authority: &str, lct_id: Uuid) -> String {
    format!("did:web4:{authority}:{lct_id}")
}

/// Parse a `did:web4:<authority>:<uuid>` identifier into its parts.
pub fn parse_did_web4(did: &str) -> Option<(String, Uuid)> {
    let rest = did.strip_prefix("did:web4:")?;
    // Authority may itself contain no ':' in v0 (a bare host); the UUID is the
    // final ':'-delimited segment.
    let idx = rest.rfind(':')?;
    let authority = &rest[..idx];
    let uuid = Uuid::parse_str(&rest[idx + 1..]).ok()?;
    if authority.is_empty() {
        return None;
    }
    Some((authority.to_string(), uuid))
}

/// Encode a 32-byte Ed25519 public key as a `Multikey` `publicKeyMultibase`
/// string: multicodec `ed25519-pub` (0xed 0x01) + key, base58btc, 'z' prefix.
/// Yields the standard `z6Mk...` form.
pub fn ed25519_multikey(pubkey: &[u8; 32]) -> String {
    let mut bytes = Vec::with_capacity(34);
    bytes.push(0xed);
    bytes.push(0x01);
    bytes.extend_from_slice(pubkey);
    format!("z{}", base58btc_encode(&bytes))
}

const B58: &[u8] = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

fn base58btc_encode(input: &[u8]) -> String {
    // Leading zero bytes → leading '1's.
    let zeros = input.iter().take_while(|b| **b == 0).count();
    let mut digits: Vec<u8> = Vec::new();
    for &byte in input {
        let mut carry = byte as u32;
        for d in digits.iter_mut() {
            carry += (*d as u32) << 8;
            *d = (carry % 58) as u8;
            carry /= 58;
        }
        while carry > 0 {
            digits.push((carry % 58) as u8);
            carry /= 58;
        }
    }
    let mut out = String::with_capacity(zeros + digits.len());
    for _ in 0..zeros {
        out.push('1');
    }
    for &d in digits.iter().rev() {
        out.push(B58[d as usize] as char);
    }
    out
}

// ─────────────────────────── DID Document ───────────────────────────

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VerificationMethod {
    pub id: String,
    #[serde(rename = "type")]
    pub type_: String,
    pub controller: String,
    #[serde(rename = "publicKeyMultibase")]
    pub public_key_multibase: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Service {
    pub id: String,
    #[serde(rename = "type")]
    pub type_: String,
    #[serde(rename = "serviceEndpoint")]
    pub service_endpoint: String,
}

/// A W3C DID Core 1.0 conformant DID Document — the public projection of an LCT.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DidDocument {
    #[serde(rename = "@context")]
    pub context: Vec<String>,
    pub id: String,
    #[serde(rename = "verificationMethod")]
    pub verification_method: Vec<VerificationMethod>,
    pub authentication: Vec<String>,
    #[serde(rename = "assertionMethod")]
    pub assertion_method: Vec<String>,
    #[serde(rename = "capabilityInvocation")]
    pub capability_invocation: Vec<String>,
    #[serde(rename = "capabilityDelegation")]
    pub capability_delegation: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub service: Vec<Service>,
}

/// Optional service endpoints to advertise in the DID Document.
#[derive(Clone, Debug, Default)]
pub struct ServiceEndpoints {
    /// The hub REST base (the door into the Web4-native trust layer).
    pub hub_rest: Option<String>,
    /// The sealed-channel endpoint for E2E messaging.
    pub channel: Option<String>,
}

impl DidDocument {
    /// Project an LCT into a DID Document resolved via `authority`.
    ///
    /// Note: `keyAgreement` is intentionally absent in v0 — the Web4 channel
    /// key (`pair_channel`) is an *independent* X25519 key, not derived from the
    /// Ed25519 identity key, so it cannot be expressed as a derived DID
    /// verification method. A channel endpoint is advertised as a service
    /// instead.
    pub fn from_lct(lct: &Lct, authority: &str, services: &ServiceEndpoints) -> Self {
        let did = did_web4(authority, lct.id);
        let key_id = format!("{did}#key-0");
        let multibase = ed25519_multikey(&lct.public_key.to_bytes());

        let vm = VerificationMethod {
            id: key_id.clone(),
            type_: "Multikey".to_string(),
            controller: did.clone(),
            public_key_multibase: multibase,
        };

        let mut service = Vec::new();
        if let Some(rest) = &services.hub_rest {
            service.push(Service {
                id: format!("{did}#hub"),
                type_: "Web4Hub".to_string(),
                service_endpoint: rest.clone(),
            });
        }
        if let Some(ch) = &services.channel {
            service.push(Service {
                id: format!("{did}#channel"),
                type_: "Web4Channel".to_string(),
                service_endpoint: ch.clone(),
            });
        }

        DidDocument {
            context: vec![
                "https://www.w3.org/ns/did/v1".to_string(),
                "https://web4.io/ns/did/v1".to_string(),
            ],
            id: did,
            verification_method: vec![vm],
            authentication: vec![key_id.clone()],
            assertion_method: vec![key_id.clone()],
            capability_invocation: vec![key_id.clone()],
            capability_delegation: vec![key_id],
            service,
        }
    }
}

/// DID document metadata — carries deactivation, per the DID Resolution spec.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DidDocumentMetadata {
    pub deactivated: bool,
}

impl DidDocumentMetadata {
    /// A voided or slashed LCT resolves as deactivated.
    pub fn for_lct(lct: &Lct) -> Self {
        Self {
            deactivated: matches!(lct.status, LctStatus::Void | LctStatus::Slashed),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::lct::{EntityType, Lct};

    #[test]
    fn test_did_roundtrip() {
        let id = Uuid::new_v4();
        let did = did_web4("hub.example.com", id);
        assert_eq!(did, format!("did:web4:hub.example.com:{id}"));
        let (auth, parsed) = parse_did_web4(&did).unwrap();
        assert_eq!(auth, "hub.example.com");
        assert_eq!(parsed, id);
    }

    #[test]
    fn test_parse_rejects_garbage() {
        assert!(parse_did_web4("did:web:example.com").is_none());
        assert!(parse_did_web4("did:web4:onlyauthority").is_none());
        assert!(parse_did_web4("did:web4:auth:not-a-uuid").is_none());
    }

    #[test]
    fn test_multikey_form() {
        // All-zero key → still a valid 'z'-prefixed base58btc multikey.
        let mk = ed25519_multikey(&[0u8; 32]);
        assert!(mk.starts_with('z'));
        // A known key produces the standard z6Mk prefix (ed25519-pub multicodec).
        let mk2 = ed25519_multikey(&[1u8; 32]);
        assert!(mk2.starts_with("z6Mk"));
    }

    #[test]
    fn test_base58_leading_zeros() {
        // Two leading zero bytes → two '1's.
        assert!(base58btc_encode(&[0, 0, 1]).starts_with("11"));
    }

    #[test]
    fn test_did_document_from_lct() {
        let (lct, _kp) = Lct::new(EntityType::Human, None);
        let services = ServiceEndpoints {
            hub_rest: Some("https://hub.example.com/v1".to_string()),
            channel: None,
        };
        let doc = DidDocument::from_lct(&lct, "hub.example.com", &services);

        assert_eq!(doc.id, format!("did:web4:hub.example.com:{}", lct.id));
        assert_eq!(doc.context[0], "https://www.w3.org/ns/did/v1");
        assert_eq!(doc.verification_method.len(), 1);
        assert_eq!(doc.verification_method[0].type_, "Multikey");
        assert!(doc.verification_method[0].public_key_multibase.starts_with('z'));
        // authentication etc. reference the single key
        assert_eq!(doc.authentication[0], format!("{}#key-0", doc.id));
        assert_eq!(doc.capability_delegation[0], format!("{}#key-0", doc.id));
        // one service (hub), channel omitted
        assert_eq!(doc.service.len(), 1);
        assert_eq!(doc.service[0].type_, "Web4Hub");
    }

    #[test]
    fn test_did_document_serializes_conformant() {
        let (lct, _kp) = Lct::new(EntityType::AiSoftware, None);
        let doc = DidDocument::from_lct(&lct, "h.io", &ServiceEndpoints::default());
        let json = serde_json::to_string(&doc).unwrap();
        // Conformant field names present
        assert!(json.contains("\"@context\""));
        assert!(json.contains("\"verificationMethod\""));
        assert!(json.contains("\"publicKeyMultibase\""));
        assert!(json.contains("\"capabilityDelegation\""));
        // empty service list is omitted
        assert!(!json.contains("\"service\""));
        // round-trips
        let back: DidDocument = serde_json::from_str(&json).unwrap();
        assert_eq!(back.id, doc.id);
    }

    #[test]
    fn test_deactivation_reflects_status() {
        let (mut lct, _kp) = Lct::new(EntityType::Human, None);
        assert!(!DidDocumentMetadata::for_lct(&lct).deactivated);
        lct.void();
        assert!(DidDocumentMetadata::for_lct(&lct).deactivated);
    }
}
