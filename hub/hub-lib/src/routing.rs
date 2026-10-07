// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Member-of routing (hub/docs/PRD_MEMBER_OF_ROUTING.md rev 5, slice Hub A).
//!
//! A machine's hestia holds ONE hub membership and is registered here as the **router** for its
//! canonical LCT. Entities on that machine are witnessed as **member-of** it: "LCT-x is reported as
//! member-of LCT-y". Hub edges are ONE level (D6): the parent is always a registered router, and a
//! router is never a child. Deeper structure is hestia-local.
//!
//! This module holds the pure parts: the router-interface certificate verifier (byte-for-byte the
//! construction hestia signs, `hestia/core/src/router_certificate.rs`), the consent statements for
//! report and withdrawal (separate domain strings), their time window, and the routing lookup. The
//! daemon owns the I/O checks (live pin, receipt mode, envelope signer) and the ordering rules that
//! need the projection (strictly increasing `issued_at`).

use crate::ids::{CanonicalLctId, HubMemberId};
use crate::state::HubState;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use web4_core::crypto::{PublicKey, SignatureBytes};

pub const ROUTER_CERT_PROTOCOL: &str = "hestia-router-interface-cert-v1";
pub const RECEIPT_PROTOCOL: &str = "hub-mailbox-receive-v1";
/// How old a consent (or a certificate) may be, and how far in the future it may claim to be.
pub const CONSENT_MAX_AGE_SECS: i64 = 600;
pub const CLOCK_SKEW_SECS: i64 = 60;
pub const REPORT_DOMAIN: &str = "web4-member-of-v1";
pub const WITHDRAW_DOMAIN: &str = "web4-member-of-withdraw-v1";

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
}

fn pubkey(hex_str: &str, what: &str) -> Result<PublicKey, String> {
    let raw = hex::decode(hex_str).map_err(|_| format!("{what} is not hex"))?;
    let bytes: [u8; 32] = raw.try_into().map_err(|_| format!("{what} is not 32 bytes"))?;
    PublicKey::from_bytes(&bytes).map_err(|_| format!("{what} is not an Ed25519 key"))
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
    /// Unix seconds; H1.7 orders re-registrations by it.
    pub issued_at: u64,
}

impl RouterCert {
    /// Verify the certificate on its own terms (H1.1–3): shape, the router LCT re-derives from the
    /// router key, both signatures, this hub, and not future-dated beyond clock skew (H1.7). The
    /// live checks (pin, receipt mode, caller, monotonic `issued_at`) are the daemon's.
    pub fn verify(&self, this_hub: Uuid, now: chrono::DateTime<chrono::Utc>) -> Result<VerifiedRouter, RoutingError> {
        let e = |m: String| RoutingError::Cert(m);
        let p = &self.payload;
        if p.protocol != ROUTER_CERT_PROTOCOL {
            return Err(e(format!("protocol must be {ROUTER_CERT_PROTOCOL}")));
        }
        if p.receipt_protocol != RECEIPT_PROTOCOL {
            return Err(e(format!("receipt protocol must be {RECEIPT_PROTOCOL}")));
        }
        if p.hub_lct_id != this_hub {
            return Err(e(format!("issued for hub {}, not this hub {this_hub}", p.hub_lct_id)));
        }
        if p.issued_at as i64 > now.timestamp() + CLOCK_SKEW_SECS {
            return Err(e("issued_at is in the future beyond clock skew".into()));
        }
        let router_key = pubkey(&p.router_pubkey_hex, "router key").map_err(e)?;
        let member_key = pubkey(&p.hub_member_pubkey_hex, "member key").map_err(e)?;
        let router_lct = CanonicalLctId::parse(&p.router_lct).map_err(|x| e(x.to_string()))?;
        if CanonicalLctId::derive(&router_key) != router_lct {
            return Err(e("router_lct does not derive from the router key".into()));
        }
        let bytes = p.signing_bytes();
        let ok = |key: &PublicKey, sig: &str| signature(sig).is_some_and(|s| key.verify(&bytes, &s).is_ok());
        if !ok(&router_key, &self.router_signature_hex) {
            return Err(e("router signature does not verify".into()));
        }
        if !ok(&member_key, &self.hub_member_signature_hex) {
            return Err(e("hub-member signature does not verify".into()));
        }
        Ok(VerifiedRouter {
            router_lct, member: HubMemberId::from_uuid(p.hub_member_lct), member_key, issued_at: p.issued_at,
        })
    }
}

/// x's signature over a member-of statement, with x's binding key. Stored in the witnessed event
/// (D7); the projection and the H4 read stay the bare fact.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Consent {
    pub pubkey_hex: String,
    pub signature_hex: String,
    /// RFC 3339.
    pub issued_at: String,
}

/// The statement x signs, exactly as PRD H2 (rev 7) writes it: five lines, each ending in `\n`
/// (trailing newline included, matching the router-certificate construction). `domain` is [`REPORT_DOMAIN`] or [`WITHDRAW_DOMAIN`], so a report consent can
/// never be replayed as a withdrawal, or the reverse. Pinned by `consent_bytes_vector`.
pub fn consent_bytes(domain: &str, hub: Uuid, member: &CanonicalLctId, of: &CanonicalLctId, issued_at: &str) -> Vec<u8> {
    format!("{domain}\n{hub}\n{member}\n{of}\n{issued_at}\n").into_bytes()
}

impl Consent {
    /// Verify that `member`'s own key signed `domain` for (`member`, `of`) inside the two-sided window
    /// `now − 10 min ≤ issued_at ≤ now + 60 s`. Returns the consent's `issued_at`, which the daemon
    /// must find strictly greater than the member's last accepted one (H2).
    pub fn verify(&self, domain: &str, hub: Uuid, member: &CanonicalLctId, of: &CanonicalLctId,
                  now: chrono::DateTime<chrono::Utc>) -> Result<chrono::DateTime<chrono::Utc>, RoutingError> {
        let e = |m: String| RoutingError::Consent(m);
        let key = pubkey(&self.pubkey_hex, "consent key").map_err(e)?;
        if &CanonicalLctId::derive(&key) != member {
            return Err(e("the consenting key is not the member's key".into()));
        }
        let at = chrono::DateTime::parse_from_rfc3339(&self.issued_at)
            .map_err(|_| e("issued_at is not RFC 3339".into()))?
            .with_timezone(&chrono::Utc);
        let age = (now - at).num_seconds();
        if !(-CLOCK_SKEW_SECS..=CONSENT_MAX_AGE_SECS).contains(&age) {
            return Err(e(format!(
                "issued {age}s from now; must be within -{CLOCK_SKEW_SECS}..{CONSENT_MAX_AGE_SECS}s")));
        }
        let sig = signature(&self.signature_hex).ok_or_else(|| e("signature is not 64-byte hex".into()))?;
        key.verify(&consent_bytes(domain, hub, member, of, &self.issued_at), &sig)
            .map_err(|_| e("signature does not verify".into()))?;
        Ok(at)
    }
}

/// Where mail for `lct` goes (H3 rules 0 and 1): a registered router receives its own mail; a member
/// with a current edge to a registered router goes to that router. One level, no walk (D6).
pub fn route_target(state: &HubState, lct: &CanonicalLctId) -> Option<(CanonicalLctId, HubMemberId)> {
    if let Some(r) = state.routers.get(lct) {
        return Some((lct.clone(), r.member));
    }
    let parent = state.member_of.get(lct)?;
    state.routers.get(parent).map(|r| (parent.clone(), r.member))
}

#[cfg(test)]
pub(crate) mod tests {
    use super::*;
    use crate::events::{HubEvent, MemberOfWithdrawnBy};
    use chrono::Utc;
    use web4_core::crypto::KeyPair;

    pub(crate) fn cert(hub: Uuid, member: Uuid, router: &KeyPair, member_key: &KeyPair, issued_at: u64) -> RouterCert {
        let payload = RouterCertPayload {
            protocol: ROUTER_CERT_PROTOCOL.into(),
            router_lct: CanonicalLctId::derive(&router.verifying_key()).to_string(),
            router_pubkey_hex: router.verifying_key().to_hex(),
            hub_lct_id: hub,
            hub_member_lct: member,
            hub_member_pubkey_hex: member_key.verifying_key().to_hex(),
            interface_binding_id: Uuid::nil(),
            receipt_protocol: RECEIPT_PROTOCOL.into(),
            issued_at,
        };
        let bytes = payload.signing_bytes();
        RouterCert {
            router_signature_hex: router.sign(&bytes).to_hex(),
            hub_member_signature_hex: member_key.sign(&bytes).to_hex(),
            payload,
        }
    }

    pub(crate) fn consent(domain: &str, hub: Uuid, x: &KeyPair, of: &CanonicalLctId, at: chrono::DateTime<Utc>) -> Consent {
        let member = CanonicalLctId::derive(&x.verifying_key());
        let issued_at = at.to_rfc3339();
        Consent {
            pubkey_hex: x.verifying_key().to_hex(),
            signature_hex: x.sign(&consent_bytes(domain, hub, &member, of, &issued_at)).to_hex(),
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

    /// CROSS-REPO VECTOR for the consent statement (PRD H2): what hestia's S2 must sign.
    #[test]
    fn consent_bytes_vector() {
        let x = CanonicalLctId::parse(&format!("lct:web4:mb32:b{}", "a".repeat(52))).unwrap();
        let y = CanonicalLctId::parse(&format!("lct:web4:mb32:b{}", "b".repeat(52))).unwrap();
        let got = consent_bytes(REPORT_DOMAIN, Uuid::nil(), &x, &y, "2026-10-07T00:00:00+00:00");
        let want = format!("web4-member-of-v1\n00000000-0000-0000-0000-000000000000\nlct:web4:mb32:b{}\nlct:web4:mb32:b{}\n2026-10-07T00:00:00+00:00\n",
            "a".repeat(52), "b".repeat(52));
        assert_eq!(String::from_utf8(got).unwrap(), want);
        assert!(String::from_utf8(consent_bytes(WITHDRAW_DOMAIN, Uuid::nil(), &x, &y, "t")).unwrap()
            .starts_with("web4-member-of-withdraw-v1\n"));
    }

    #[test]
    fn a_dual_signed_certificate_verifies_and_every_forgery_does_not() {
        let hub = Uuid::new_v4();
        let now = Utc::now();
        let (r, m) = (KeyPair::generate(), KeyPair::generate());
        let member = Uuid::new_v4();
        let good = cert(hub, member, &r, &m, now.timestamp() as u64);
        let v = good.verify(hub, now).expect("verifies");
        assert_eq!(v.member.as_uuid(), member);
        assert_eq!(v.router_lct, CanonicalLctId::derive(&r.verifying_key()));

        assert!(good.verify(Uuid::new_v4(), now).is_err(), "another hub's certificate");
        let mut t = good.clone(); t.payload.hub_member_lct = Uuid::new_v4();
        assert!(t.verify(hub, now).is_err(), "tampered member");
        let mut t = good.clone(); t.router_signature_hex = m.sign(&good.payload.signing_bytes()).to_hex();
        assert!(t.verify(hub, now).is_err(), "router signature by the wrong key");
        let mut t = good.clone(); t.hub_member_signature_hex = "00".repeat(64);
        assert!(t.verify(hub, now).is_err(), "missing member signature");
        let other = KeyPair::generate();
        let mut t = good.clone(); t.payload.router_lct = CanonicalLctId::derive(&other.verifying_key()).to_string();
        assert!(t.verify(hub, now).is_err(), "a router LCT the key does not derive");
        let future = cert(hub, member, &r, &m, (now.timestamp() + CLOCK_SKEW_SECS + 30) as u64);
        assert!(future.verify(hub, now).is_err(), "future-dated beyond skew (H1.7, rev 5)");
    }

    #[test]
    fn consent_is_the_members_own_recent_signature_in_its_own_domain() {
        let hub = Uuid::new_v4();
        let (x, y) = (KeyPair::generate(), KeyPair::generate());
        let (xl, yl) = (CanonicalLctId::derive(&x.verifying_key()), CanonicalLctId::derive(&y.verifying_key()));
        let now = Utc::now();
        consent(REPORT_DOMAIN, hub, &x, &yl, now).verify(REPORT_DOMAIN, hub, &xl, &yl, now).expect("x consents to y");

        assert!(consent(REPORT_DOMAIN, hub, &y, &yl, now).verify(REPORT_DOMAIN, hub, &xl, &yl, now).is_err(),
            "the router cannot consent for x");
        assert!(consent(REPORT_DOMAIN, hub, &x, &yl, now).verify(REPORT_DOMAIN, hub, &xl, &xl, now).is_err(),
            "consent to y is not consent to another parent");
        assert!(consent(REPORT_DOMAIN, hub, &x, &yl, now).verify(REPORT_DOMAIN, Uuid::new_v4(), &xl, &yl, now).is_err(),
            "another hub");
        assert!(consent(REPORT_DOMAIN, hub, &x, &yl, now).verify(WITHDRAW_DOMAIN, hub, &xl, &yl, now).is_err(),
            "a report consent is not a withdrawal");
        assert!(consent(WITHDRAW_DOMAIN, hub, &x, &yl, now).verify(REPORT_DOMAIN, hub, &xl, &yl, now).is_err(),
            "a withdrawal is not a report consent");
        let stale = consent(REPORT_DOMAIN, hub, &x, &yl, now - chrono::Duration::seconds(CONSENT_MAX_AGE_SECS + 5));
        assert!(stale.verify(REPORT_DOMAIN, hub, &xl, &yl, now).is_err(), "stale");
        let future = consent(REPORT_DOMAIN, hub, &x, &yl, now + chrono::Duration::seconds(CLOCK_SKEW_SECS + 30));
        assert!(future.verify(REPORT_DOMAIN, hub, &xl, &yl, now).is_err(), "future-dated (two-sided window, rev 5)");
    }

    fn lct_of(k: &KeyPair) -> CanonicalLctId { CanonicalLctId::derive(&k.verifying_key()) }

    #[test]
    fn routing_is_one_level_and_a_router_receives_its_own_mail() {
        let hub = Uuid::new_v4();
        let mut state = HubState::default();
        let (xk, yk) = (KeyPair::generate(), KeyPair::generate());
        let (x, y) = (lct_of(&xk), lct_of(&yk));
        let m = Uuid::new_v4();
        state.apply(&HubEvent::MemberOfReported {
            member: x.to_string(), of: y.to_string(),
            consent: consent(REPORT_DOMAIN, hub, &xk, &y, Utc::now()),
        }, Utc::now(), 1);
        assert_eq!(route_target(&state, &x), None, "y has no router yet");
        state.apply(&HubEvent::RouterRegistered { router_lct: y.to_string(), member: m, issued_at: 10 }, Utc::now(), 2);
        assert_eq!(route_target(&state, &x), Some((y.clone(), HubMemberId::from_uuid(m))));
        assert_eq!(route_target(&state, &y), Some((y.clone(), HubMemberId::from_uuid(m))), "rule 0: a router's own mail");
        assert_eq!(state.member_of_consent_key.get(&x).map(String::as_str), Some(xk.verifying_key().to_hex().as_str()),
            "the current consent key is projected for sealing (rev 3)");
    }

    #[test]
    fn the_high_water_mark_moves_on_report_and_self_withdraw_but_not_router_withdraw() {
        let hub = Uuid::new_v4();
        let mut state = HubState::default();
        let (xk, yk) = (KeyPair::generate(), KeyPair::generate());
        let (x, y) = (lct_of(&xk), lct_of(&yk));
        let t0 = Utc::now() - chrono::Duration::seconds(30);
        let c = consent(REPORT_DOMAIN, hub, &xk, &y, t0);
        state.apply(&HubEvent::MemberOfReported { member: x.to_string(), of: y.to_string(), consent: c }, Utc::now(), 1);
        assert_eq!(state.member_of_mark.get(&x).copied(), Some(chrono::DateTime::parse_from_rfc3339(&t0.to_rfc3339()).unwrap().with_timezone(&Utc)));

        state.apply(&HubEvent::MemberOfWithdrawn { member: x.to_string(), by: MemberOfWithdrawnBy::Router { member: Uuid::new_v4() } }, Utc::now(), 2);
        assert!(state.member_of.get(&x).is_none());
        assert!(state.member_of_mark.get(&x).is_some(), "router withdrawal leaves the mark (rev 5)");

        let t1 = Utc::now();
        state.apply(&HubEvent::MemberOfWithdrawn {
            member: x.to_string(),
            by: MemberOfWithdrawnBy::Member { of: y.to_string(), consent: consent(WITHDRAW_DOMAIN, hub, &xk, &y, t1) },
        }, Utc::now(), 3);
        assert_eq!(state.member_of_mark.get(&x).map(|d| d.timestamp()), Some(t1.timestamp()), "self-withdrawal advances it");
    }
}
