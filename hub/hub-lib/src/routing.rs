// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Member-of routing (hub/docs/PRD_MEMBER_OF_ROUTING.md, slice Hub A).
//!
//! A machine's hestia holds ONE hub membership and is registered here as the **router** for its
//! canonical LCT. Entities on that machine are witnessed as **member-of** it — the bare fact
//! "LCT-x is reported as member-of LCT-y", nothing else recorded with it. Mail for LCT-x is then
//! routed to the nearest ancestor that has a router ([`route_target`]).
//!
//! This module holds the pure parts: the router-interface certificate verifier (byte-for-byte the
//! construction hestia signs, `hestia/core/src/router_certificate.rs`), the member-of consent
//! statement, and the ancestor walk with its cycle and depth guards. The daemon owns the I/O
//! checks (live pin, receipt mode, envelope signer).

use crate::ids::{CanonicalLctId, HubMemberId};
use crate::state::HubState;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use web4_core::crypto::{PublicKey, SignatureBytes};

pub const ROUTER_CERT_PROTOCOL: &str = "hestia-router-interface-cert-v1";
pub const RECEIPT_PROTOCOL: &str = "hub-mailbox-receive-v1";
/// Ancestry deeper than this is refused at intake and never walked further at delivery.
pub const MAX_DEPTH: usize = 8;
/// How old a member-of consent signature may be when it reaches the hub.
pub const CONSENT_MAX_AGE_SECS: i64 = 600;

/// hestia's `RouterInterfaceCertificatePayload`, field for field.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct RouterCertPayload {
    pub protocol: String,
    pub router_lct: String,
    pub router_pubkey_hex: String,
    pub hub_lct_id: Uuid,
    pub hub_member_lct: Uuid,
    pub hub_member_pubkey_hex: String,
    pub interface_binding_id: Uuid,
    pub receipt_protocol: String,
    pub issued_at: u64,
}

/// hestia's `RouterInterfaceCertificate`: the payload, signed by the router's binding key AND by
/// the dedicated hub membership key.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct RouterCert {
    pub payload: RouterCertPayload,
    pub router_signature_hex: String,
    pub hub_member_signature_hex: String,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RoutingError {
    #[error("router certificate: {0}")]
    Cert(String),
    #[error("member-of consent: {0}")]
    Consent(String),
    #[error("member-of edge: {0}")]
    Edge(String),
}

fn pubkey(hex_str: &str, what: &str) -> Result<PublicKey, RoutingError> {
    let raw = hex::decode(hex_str).map_err(|_| RoutingError::Cert(format!("{what} is not hex")))?;
    let bytes: [u8; 32] = raw.try_into().map_err(|_| RoutingError::Cert(format!("{what} is not 32 bytes")))?;
    PublicKey::from_bytes(&bytes).map_err(|_| RoutingError::Cert(format!("{what} is not an Ed25519 key")))
}

fn signature(hex_str: &str) -> Option<SignatureBytes> {
    let raw: [u8; 64] = hex::decode(hex_str).ok()?.try_into().ok()?;
    Some(SignatureBytes::from_bytes(raw))
}

impl RouterCertPayload {
    /// The exact bytes hestia signs. Any change here must change the domain string there too.
    pub fn signing_bytes(&self) -> Vec<u8> {
        format!(
            "HESTIA-ROUTER-INTERFACE-CERT-V1\n\
             protocol={}\n\
             router_lct={}\n\
             router_pubkey_hex={}\n\
             hub_lct_id={}\n\
             hub_member_lct={}\n\
             hub_member_pubkey_hex={}\n\
             interface_binding_id={}\n\
             receipt_protocol={}\n\
             issued_at={}\n",
            self.protocol, self.router_lct, self.router_pubkey_hex, self.hub_lct_id,
            self.hub_member_lct, self.hub_member_pubkey_hex, self.interface_binding_id,
            self.receipt_protocol, self.issued_at,
        )
        .into_bytes()
    }
}

/// What a verified certificate proves, in the hub's own types.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct VerifiedRouter {
    pub router_lct: CanonicalLctId,
    pub member: HubMemberId,
    /// The membership key the certificate names; the daemon checks it equals the hub's pin.
    pub member_key: PublicKey,
}

impl RouterCert {
    /// Verify the certificate on its own terms: shape, the router LCT re-derives from the router
    /// key, both signatures, and that it names THIS hub. The live checks (the hub's pin equals
    /// `member_key`, receipt mode, the caller is the member) are the daemon's.
    pub fn verify(&self, this_hub: Uuid) -> Result<VerifiedRouter, RoutingError> {
        let p = &self.payload;
        if p.protocol != ROUTER_CERT_PROTOCOL {
            return Err(RoutingError::Cert(format!("protocol must be {ROUTER_CERT_PROTOCOL}")));
        }
        if p.receipt_protocol != RECEIPT_PROTOCOL {
            return Err(RoutingError::Cert(format!("receipt protocol must be {RECEIPT_PROTOCOL}")));
        }
        if p.hub_lct_id != this_hub {
            return Err(RoutingError::Cert(format!("issued for hub {}, not this hub {this_hub}", p.hub_lct_id)));
        }
        let router_key = pubkey(&p.router_pubkey_hex, "router key")?;
        let member_key = pubkey(&p.hub_member_pubkey_hex, "member key")?;
        let router_lct = CanonicalLctId::parse(&p.router_lct)
            .map_err(|e| RoutingError::Cert(e.to_string()))?;
        if CanonicalLctId::derive(&router_key) != router_lct {
            return Err(RoutingError::Cert("router_lct does not derive from the router key".into()));
        }
        let bytes = p.signing_bytes();
        let ok = |key: &PublicKey, sig: &str| signature(sig).is_some_and(|s| key.verify(&bytes, &s).is_ok());
        if !ok(&router_key, &self.router_signature_hex) {
            return Err(RoutingError::Cert("router signature does not verify".into()));
        }
        if !ok(&member_key, &self.hub_member_signature_hex) {
            return Err(RoutingError::Cert("hub-member signature does not verify".into()));
        }
        Ok(VerifiedRouter { router_lct, member: HubMemberId::from_uuid(p.hub_member_lct), member_key })
    }
}

/// x's consent to being member-of y, signed with x's binding key.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Consent {
    pub pubkey_hex: String,
    pub signature_hex: String,
    /// RFC 3339.
    pub issued_at: String,
}

/// The statement x signs. Domain-separated and newline-delimited like the certificate, so it is
/// reproducible in any language without JSON canonicalisation.
pub fn consent_bytes(hub: Uuid, member: &CanonicalLctId, of: &CanonicalLctId, issued_at: &str) -> Vec<u8> {
    format!("web4-member-of-v1\n{hub}\n{member}\n{of}\n{issued_at}\n").into_bytes()
}

impl Consent {
    /// Verify that `member`'s own binding key consented to `of`, recently. Checked at intake and
    /// never stored: the witnessed edge is the bare fact (PRD §3 H2).
    pub fn verify(&self, hub: Uuid, member: &CanonicalLctId, of: &CanonicalLctId,
                  now: chrono::DateTime<chrono::Utc>) -> Result<(), RoutingError> {
        let key = pubkey(&self.pubkey_hex, "consent key").map_err(|e| RoutingError::Consent(e.to_string()))?;
        if &CanonicalLctId::derive(&key) != member {
            return Err(RoutingError::Consent("the consenting key is not the member's binding key".into()));
        }
        let at = chrono::DateTime::parse_from_rfc3339(&self.issued_at)
            .map_err(|_| RoutingError::Consent("issued_at is not RFC 3339".into()))?
            .with_timezone(&chrono::Utc);
        let age = (now - at).num_seconds();
        if !(-60..=CONSENT_MAX_AGE_SECS).contains(&age) {
            return Err(RoutingError::Consent(format!("issued {age}s ago; must be within {CONSENT_MAX_AGE_SECS}s")));
        }
        let sig = signature(&self.signature_hex)
            .ok_or_else(|| RoutingError::Consent("signature is not 64-byte hex".into()))?;
        key.verify(&consent_bytes(hub, member, of, &self.issued_at), &sig)
            .map_err(|_| RoutingError::Consent("signature does not verify".into()))
    }
}

/// Would recording `member` member-of `of` be refused on structure alone (self-edge, cycle, depth)?
pub fn check_edge(state: &HubState, member: &CanonicalLctId, of: &CanonicalLctId) -> Result<(), RoutingError> {
    if member == of {
        return Err(RoutingError::Edge("an entity cannot be member-of itself".into()));
    }
    // Walk up from `of`; meeting `member` means the new edge closes a cycle.
    let mut cur = of.clone();
    for depth in 1..=MAX_DEPTH {
        if &cur == member {
            return Err(RoutingError::Edge("the edge would create a cycle".into()));
        }
        match state.member_of.get(&cur) {
            Some(parent) => cur = parent.clone(),
            None => return Ok(()),
        }
        if depth == MAX_DEPTH {
            break;
        }
    }
    Err(RoutingError::Edge(format!("ancestry would exceed depth {MAX_DEPTH}")))
}

/// Where mail for `lct` goes: the nearest ancestor (starting with `lct` itself) that has a
/// registered router, and that router's hub member. `None` when nothing on the chain is routed.
pub fn route_target(state: &HubState, lct: &CanonicalLctId) -> Option<(CanonicalLctId, HubMemberId)> {
    let mut cur = lct.clone();
    for _ in 0..=MAX_DEPTH {
        if let Some(member) = state.routers.get(&cur) {
            return Some((cur, *member));
        }
        cur = state.member_of.get(&cur)?.clone();
    }
    None
}

#[cfg(test)]
pub(crate) mod tests {
    use super::*;
    use crate::events::HubEvent;
    use chrono::Utc;
    use web4_core::crypto::KeyPair;

    pub(crate) fn cert(hub: Uuid, member: Uuid, router: &KeyPair, member_key: &KeyPair) -> RouterCert {
        let payload = RouterCertPayload {
            protocol: ROUTER_CERT_PROTOCOL.into(),
            router_lct: CanonicalLctId::derive(&router.verifying_key()).to_string(),
            router_pubkey_hex: router.verifying_key().to_hex(),
            hub_lct_id: hub,
            hub_member_lct: member,
            hub_member_pubkey_hex: member_key.verifying_key().to_hex(),
            interface_binding_id: Uuid::nil(),
            receipt_protocol: RECEIPT_PROTOCOL.into(),
            issued_at: 1_790_000_000,
        };
        let bytes = payload.signing_bytes();
        RouterCert {
            router_signature_hex: router.sign(&bytes).to_hex(),
            hub_member_signature_hex: member_key.sign(&bytes).to_hex(),
            payload,
        }
    }

    pub(crate) fn consent(hub: Uuid, x: &KeyPair, of: &CanonicalLctId, at: chrono::DateTime<Utc>) -> Consent {
        let member = CanonicalLctId::derive(&x.verifying_key());
        let issued_at = at.to_rfc3339();
        Consent {
            pubkey_hex: x.verifying_key().to_hex(),
            signature_hex: x.sign(&consent_bytes(hub, &member, of, &issued_at)).to_hex(),
            issued_at,
        }
    }

    /// CROSS-REPO VECTOR. hestia's `signing_bytes` for this payload must produce these exact bytes;
    /// hestia should pin the same string so drift on EITHER side fails a test (the constellation
    /// vector was one-sided for a month — see constellation.rs).
    #[test]
    fn signing_bytes_match_the_hestia_construction() {
        let p = RouterCertPayload {
            protocol: ROUTER_CERT_PROTOCOL.into(),
            router_lct: "lct:web4:mb32:bvector".into(),
            router_pubkey_hex: "aa".repeat(32),
            hub_lct_id: Uuid::nil(),
            hub_member_lct: Uuid::from_u128(1),
            hub_member_pubkey_hex: "bb".repeat(32),
            interface_binding_id: Uuid::from_u128(2),
            receipt_protocol: RECEIPT_PROTOCOL.into(),
            issued_at: 42,
        };
        let want = format!(
            "HESTIA-ROUTER-INTERFACE-CERT-V1\nprotocol=hestia-router-interface-cert-v1\nrouter_lct=lct:web4:mb32:bvector\n\
             router_pubkey_hex={}\nhub_lct_id=00000000-0000-0000-0000-000000000000\n\
             hub_member_lct=00000000-0000-0000-0000-000000000001\nhub_member_pubkey_hex={}\n\
             interface_binding_id=00000000-0000-0000-0000-000000000002\nreceipt_protocol=hub-mailbox-receive-v1\nissued_at=42\n",
            "aa".repeat(32), "bb".repeat(32));
        assert_eq!(String::from_utf8(p.signing_bytes()).unwrap(), want);
    }

    #[test]
    fn a_dual_signed_certificate_verifies_and_every_forgery_does_not() {
        let hub = Uuid::new_v4();
        let (r, m) = (KeyPair::generate(), KeyPair::generate());
        let member = Uuid::new_v4();
        let good = cert(hub, member, &r, &m);
        let v = good.verify(hub).expect("verifies");
        assert_eq!(v.member.as_uuid(), member);
        assert_eq!(v.router_lct, CanonicalLctId::derive(&r.verifying_key()));

        assert!(good.verify(Uuid::new_v4()).is_err(), "another hub's certificate");
        let mut t = good.clone(); t.payload.hub_member_lct = Uuid::new_v4();
        assert!(t.verify(hub).is_err(), "tampered member");
        let mut t = good.clone(); t.router_signature_hex = m.sign(&good.payload.signing_bytes()).to_hex();
        assert!(t.verify(hub).is_err(), "router signature by the wrong key");
        let mut t = good.clone(); t.hub_member_signature_hex = "00".repeat(64);
        assert!(t.verify(hub).is_err(), "missing member signature");
        let other = KeyPair::generate();
        let mut t = good.clone(); t.payload.router_lct = CanonicalLctId::derive(&other.verifying_key()).to_string();
        assert!(t.verify(hub).is_err(), "a router LCT the key does not derive");
    }

    #[test]
    fn consent_must_come_from_the_members_own_key_recently() {
        let hub = Uuid::new_v4();
        let (x, y) = (KeyPair::generate(), KeyPair::generate());
        let (xl, yl) = (CanonicalLctId::derive(&x.verifying_key()), CanonicalLctId::derive(&y.verifying_key()));
        let now = Utc::now();
        consent(hub, &x, &yl, now).verify(hub, &xl, &yl, now).expect("x consents to y");

        let by_router = consent(hub, &y, &yl, now);
        assert!(by_router.verify(hub, &xl, &yl, now).is_err(), "the router cannot consent for x");
        assert!(consent(hub, &x, &yl, now).verify(hub, &xl, &xl, now).is_err(), "consent to y is not consent to another parent");
        assert!(consent(hub, &x, &yl, now).verify(Uuid::new_v4(), &xl, &yl, now).is_err(), "another hub");
        let stale = consent(hub, &x, &yl, now - chrono::Duration::seconds(CONSENT_MAX_AGE_SECS + 5));
        assert!(stale.verify(hub, &xl, &yl, now).is_err(), "stale consent");
    }

    fn lct() -> CanonicalLctId {
        CanonicalLctId::derive(&KeyPair::generate().verifying_key())
    }

    fn edge(state: &mut HubState, member: &CanonicalLctId, of: &CanonicalLctId, at: u64) {
        state.apply(&HubEvent::MemberOfReported { member: member.to_string(), of: of.to_string() }, Utc::now(), at);
    }

    #[test]
    fn routing_walks_to_the_nearest_router_and_refuses_cycles_and_depth() {
        let mut state = HubState::default();
        let (being, machine, society) = (lct(), lct(), lct());
        let router_member = Uuid::new_v4();
        edge(&mut state, &being, &machine, 1);
        edge(&mut state, &machine, &society, 2);
        assert_eq!(route_target(&state, &being), None, "no router anywhere on the chain");

        state.apply(&HubEvent::RouterRegistered { router_lct: machine.to_string(), member: router_member }, Utc::now(), 3);
        assert_eq!(route_target(&state, &being), Some((machine.clone(), HubMemberId::from_uuid(router_member))));
        assert_eq!(route_target(&state, &machine).map(|t| t.0), Some(machine.clone()), "a router routes to itself");
        assert_eq!(route_target(&state, &society), None, "routing goes up, never down");

        assert!(check_edge(&state, &society, &being).is_err(), "society -> being would close a cycle");
        assert!(check_edge(&state, &being, &being).is_err(), "self-edge");

        // A chain at the depth limit refuses one more level.
        let mut chain = vec![lct()];
        for i in 0..MAX_DEPTH { let n = lct(); edge(&mut state, &chain[i], &n, 10 + i as u64); chain.push(n); }
        assert!(check_edge(&state, &lct(), &chain[0]).is_err(), "would exceed depth");
    }

    #[test]
    fn edges_supersede_and_withdraw_and_routers_retire() {
        let mut state = HubState::default();
        let (x, y1, y2) = (lct(), lct(), lct());
        edge(&mut state, &x, &y1, 1);
        edge(&mut state, &x, &y2, 2);
        assert_eq!(state.member_of.get(&x), Some(&y2), "a new report supersedes: one current parent");
        state.apply(&HubEvent::MemberOfWithdrawn { member: x.to_string() }, Utc::now(), 3);
        assert_eq!(state.member_of.get(&x), None);

        let m = Uuid::new_v4();
        state.apply(&HubEvent::RouterRegistered { router_lct: y1.to_string(), member: m }, Utc::now(), 4);
        state.apply(&HubEvent::RouterRetired { router_lct: y1.to_string() }, Utc::now(), 5);
        assert!(state.routers.get(&y1).is_none());
    }
}
