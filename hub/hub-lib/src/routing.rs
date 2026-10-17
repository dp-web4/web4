// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Member-of routing (hub/docs/PRD_MEMBER_OF_ROUTING.md rev 7, slice Hub A).
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
    let key = PublicKey::from_bytes(&bytes).map_err(|_| format!("{what} is not an Ed25519 key"))?;
    // PRD rev 11 (Sprout): a small-order point decompresses fine but makes ECDH to it
    // predictable. Refused at every key intake here — router, member and consent keys.
    if key.is_weak() {
        return Err(format!("{what} is a small-order (weak) point"));
    }
    Ok(key)
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
        let parsed = chrono::DateTime::parse_from_rfc3339(&self.issued_at)
            .map_err(|_| e("issued_at is not RFC 3339".into()))?;
        // PRD H2: RFC 3339 **UTC** (`Z` or `+00:00`). An offset would still sign verbatim and compare
        // as an instant, but a second implementation (hestia S2) must not drift on spelling (CBP nit).
        if parsed.offset().local_minus_utc() != 0 {
            return Err(e("issued_at must be UTC (Z or +00:00)".into()));
        }
        let at = parsed.with_timezone(&chrono::Utc);
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

// ---- H5: the reply path. A member-of child speaks through its router (PRD rev 9-13). ----

/// Domain of the H5 statement. A consent can never be replayed as an act-as, or the reverse.
pub const ACT_AS_DOMAIN: &str = "web4-act-as-v1";

/// A child's authorization of an act its router member carries (PRD H5). Stored on the witnessed
/// `ReferencedAct` (rev 13: on the hub event, not on web4-core's `Act`, so the published crate is
/// unchanged). Together with that act it is everything [`act_as_bytes`] needs, so anyone holding the
/// ledger can re-verify who said it.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct ActAs {
    /// x: the child's canonical LCT.
    pub lct: String,
    /// RFC 3339 UTC, signed exactly as sent and never re-formatted (rev 11).
    pub issued_at: String,
    /// `member_of_at[x]`: the ledger index that witnessed x's current edge.
    pub edge_epoch: u64,
    /// The ledger index of the `RouterRegistered` in force for x's parent.
    pub router_epoch: u64,
    /// x's Ed25519 signature over [`act_as_bytes`], with the key on its current edge.
    pub signature_hex: String,
}

/// Why an act-as was refused. `code()` is the structured code a router keys on: `stale_epoch` and
/// `issued_at_outside_window` mean "re-sign through x"; the others mean "refused" (PRD H5).
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ActAsRefusal {
    NotTheRouter(String),
    StaleEpoch(String),
    IssuedAtOutsideWindow(String),
    BadChildSignature(String),
}

impl ActAsRefusal {
    pub fn code(&self) -> &'static str {
        match self {
            Self::NotTheRouter(_) => "not_the_router",
            Self::StaleEpoch(_) => "stale_epoch",
            Self::IssuedAtOutsideWindow(_) => "issued_at_outside_window",
            Self::BadChildSignature(_) => "bad_child_signature",
        }
    }
    pub fn detail(&self) -> &str {
        match self {
            Self::NotTheRouter(m) | Self::StaleEpoch(m) | Self::IssuedAtOutsideWindow(m)
            | Self::BadChildSignature(m) => m,
        }
    }
}

/// `to` in the tagged-text form H5 signs: `lct:<canonical>`, `peer:<uuid>`, `citizen:<uuid>`,
/// `role:<name>` or `society:<uuid>`. `FutureSelf` has no form: a child does not write to its own
/// future through a router, so such an act-as is refused.
pub fn address_text(a: &web4_core::act::ActAddress) -> Option<String> {
    use web4_core::act::ActAddress as A;
    Some(match a {
        A::Lct { canonical } => format!("lct:{canonical}"),
        A::Peer { lct_id } => format!("peer:{lct_id}"),
        A::Citizen { lct_id } => format!("citizen:{lct_id}"),
        A::Role { role } => format!("role:{role}"),
        A::Society { lct_id } => format!("society:{lct_id}"),
        A::FutureSelf { .. } => return None,
    })
}

fn netstring(out: &mut Vec<u8>, field: &str) {
    out.extend_from_slice(field.len().to_string().as_bytes());
    out.push(b':');
    out.extend_from_slice(field.as_bytes());
    out.push(b',');
}

/// The statement x signs (PRD H5, rev 10): every field a netstring (`<byte length>:<bytes>,`), in
/// this order, no separators; an absent optional field is `0:,`. UUIDs lowercase hyphenated.
/// Pinned by `act_as_bytes_vector`.
#[allow(clippy::too_many_arguments)]
pub fn act_as_bytes(hub: Uuid, x: &str, router_member: Uuid, act_id: Uuid, issued_at: &str,
                    edge_epoch: u64, router_epoch: u64, kind: &str, to: &str,
                    pointer_uri: &str, content_hash: &str) -> Vec<u8> {
    let mut out = Vec::new();
    for f in [ACT_AS_DOMAIN, &hub.to_string(), x, &router_member.to_string(), &act_id.to_string(),
              issued_at, &edge_epoch.to_string(), &router_epoch.to_string(), kind, to, pointer_uri,
              content_hash] {
        netstring(&mut out, f);
    }
    out
}

impl ActAs {
    /// The bytes x signed for `act` on `hub`: the carrier is `act.actor_lct`, and every other field
    /// comes from the act itself. `None` for an address with no tagged-text form.
    pub fn statement(&self, hub: Uuid, act: &web4_core::act::Act) -> Option<Vec<u8>> {
        Some(act_as_bytes(hub, &self.lct, act.actor_lct, act.act_id, &self.issued_at,
            self.edge_epoch, self.router_epoch, &act.kind, &address_text(&act.address)?,
            &act.substance.uri, &act.substance.content_hash))
    }

    /// H5 acceptance steps 1-4, in order, against the projection at `now`. Step 0 (`act_id`) needs
    /// the ledger and is the daemon's, before this.
    pub fn verify(&self, state: &HubState, hub: Uuid, act: &web4_core::act::Act,
                  now: chrono::DateTime<chrono::Utc>) -> Result<(), ActAsRefusal> {
        use ActAsRefusal::*;
        // 1. x's CURRENT edge names a parent whose registered router member carried the envelope.
        let x = CanonicalLctId::parse(&self.lct)
            .map_err(|_| NotTheRouter("on_behalf_of is not a canonical LCT".into()))?;
        // The spelling signed, stored and replied to (`lct:<from_lct>`) is the canonical one. `parse` admits
        // one spelling today; this keeps it so if `parse` ever loosens (Legion, #920).
        if x.to_string() != self.lct {
            return Err(NotTheRouter("on_behalf_of lct is not in canonical spelling".into()));
        }
        let parent = state.member_of.get(&x)
            .ok_or_else(|| NotTheRouter(format!("{x} has no current member-of edge")))?;
        let router = state.routers.get(parent)
            .ok_or_else(|| NotTheRouter(format!("{x}'s parent {parent} is not a registered router")))?;
        if router.member != HubMemberId::from_uuid(act.actor_lct) {
            return Err(NotTheRouter(format!("the carrier is not the router member of {x}'s parent {parent}")));
        }
        // 2. Both epochs current: a signature from before x moved, or before its router re-registered
        //    (a same-member re-key included), no longer verifies.
        // `member_of` and `member_of_at` move together; if they ever diverge, refuse rather than compare
        // against a sentinel a signer could name (CBP, #920).
        let edge_at = state.member_of_at.get(&x).copied()
            .ok_or_else(|| StaleEpoch(format!("{x}'s edge has no recorded epoch")))?;
        if self.edge_epoch != edge_at || self.router_epoch != router.registered_at {
            return Err(StaleEpoch(format!(
                "signed for edge_epoch {} / router_epoch {}; current are {edge_at} / {}",
                self.edge_epoch, self.router_epoch, router.registered_at)));
        }
        // 3. issued_at: UTC, inside now - 10 min ..= now + 60 s (the H2 window).
        let parsed = chrono::DateTime::parse_from_rfc3339(&self.issued_at)
            .map_err(|_| IssuedAtOutsideWindow("issued_at is not RFC 3339".into()))?;
        if parsed.offset().local_minus_utc() != 0 {
            return Err(IssuedAtOutsideWindow("issued_at must be UTC (Z or +00:00)".into()));
        }
        let age = (now - parsed.with_timezone(&chrono::Utc)).num_seconds();
        if !(-CLOCK_SKEW_SECS..=CONSENT_MAX_AGE_SECS).contains(&age) {
            return Err(IssuedAtOutsideWindow(format!(
                "issued {age}s from now; must be within -{CLOCK_SKEW_SECS}..{CONSENT_MAX_AGE_SECS}s")));
        }
        // 4. x's signature, with the key on its current edge (weak keys refused, as at every intake).
        let key_hex = state.member_of_consent_key.get(&x)
            .ok_or_else(|| BadChildSignature(format!("no consent key on {x}'s edge")))?;
        let key = pubkey(key_hex, "edge consent key").map_err(BadChildSignature)?;
        let bytes = self.statement(hub, act)
            .ok_or_else(|| BadChildSignature("the act's address has no tagged-text form".into()))?;
        let sig = signature(&self.signature_hex)
            .ok_or_else(|| BadChildSignature("child_signature is not 64-byte hex".into()))?;
        key.verify(&bytes, &sig).map_err(|_| BadChildSignature("child_signature does not verify".into()))
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

    /// CROSS-REPO VECTOR (H5). Any second implementation (hestia S3's router) must produce these
    /// exact bytes; pin the same string there. Covers an empty optional field and a newline-bearing one.
    #[test]
    fn act_as_bytes_vector() {
        let hub = Uuid::parse_str("11111111-1111-4111-8111-111111111111").unwrap();
        let rm = Uuid::parse_str("22222222-2222-4222-8222-222222222222").unwrap();
        let act = Uuid::parse_str("33333333-3333-4333-8333-333333333333").unwrap();
        let b = act_as_bytes(hub, "lct:web4:mb32:child", rm, act, "2026-10-16T12:00:00Z", 7, 3,
            "coordination", "lct:web4:mb32:peer", "forum/a\nb.md", "");
        assert_eq!(String::from_utf8(b).unwrap(), concat!(
            "14:web4-act-as-v1,",
            "36:11111111-1111-4111-8111-111111111111,",
            "19:lct:web4:mb32:child,",
            "36:22222222-2222-4222-8222-222222222222,",
            "36:33333333-3333-4333-8333-333333333333,",
            "20:2026-10-16T12:00:00Z,",
            "1:7,", "1:3,",
            "12:coordination,",
            "18:lct:web4:mb32:peer,",
            "12:forum/a\nb.md,",
            "0:,"));
    }

    /// A one-field change anywhere moves the bytes (netstrings leave no ambiguity to exploit:
    /// moving a byte across a field boundary changes a length prefix).
    #[test]
    fn act_as_bytes_every_field_binds() {
        let (h, r, a) = (Uuid::new_v4(), Uuid::new_v4(), Uuid::new_v4());
        let base = || act_as_bytes(h, "x", r, a, "t", 1, 2, "k", "lct:p", "u", "c");
        let variants = [
            act_as_bytes(Uuid::new_v4(), "x", r, a, "t", 1, 2, "k", "lct:p", "u", "c"),
            act_as_bytes(h, "y", r, a, "t", 1, 2, "k", "lct:p", "u", "c"),
            act_as_bytes(h, "x", Uuid::new_v4(), a, "t", 1, 2, "k", "lct:p", "u", "c"),
            act_as_bytes(h, "x", r, Uuid::new_v4(), "t", 1, 2, "k", "lct:p", "u", "c"),
            act_as_bytes(h, "x", r, a, "T", 1, 2, "k", "lct:p", "u", "c"),
            act_as_bytes(h, "x", r, a, "t", 9, 2, "k", "lct:p", "u", "c"),
            act_as_bytes(h, "x", r, a, "t", 1, 9, "k", "lct:p", "u", "c"),
            act_as_bytes(h, "x", r, a, "t", 1, 2, "K", "lct:p", "u", "c"),
            act_as_bytes(h, "x", r, a, "t", 1, 2, "k", "lct:q", "u", "c"),
            act_as_bytes(h, "x", r, a, "t", 1, 2, "k", "lct:p", "U", "c"),
            act_as_bytes(h, "x", r, a, "t", 1, 2, "k", "lct:p", "u", "C"),
            // a byte moved across a boundary: "k" + "lct:p" vs "kl" + "ct:p"
            act_as_bytes(h, "x", r, a, "t", 1, 2, "kl", "ct:p", "u", "c"),
        ];
        for (i, v) in variants.iter().enumerate() {
            assert_ne!(v, &base(), "variant {i} did not change the statement");
        }
    }

    /// H5 steps 1-4 against a projection: the happy path, then one refusal per step, each with its code.
    #[test]
    fn act_as_verify_steps_in_order() {
        use web4_core::act::{Act, ActAddress, SubstanceMedium, SubstanceRef};
        let hub = Uuid::new_v4();
        let (router, child) = (KeyPair::generate(), KeyPair::generate());
        let (y, x) = (CanonicalLctId::derive(&router.verifying_key()), CanonicalLctId::derive(&child.verifying_key()));
        let m = Uuid::new_v4();
        let mut state = HubState::default();
        state.apply(&HubEvent::RouterRegistered { router_lct: y.to_string(), member: m, issued_at: 10 }, Utc::now(), 4);
        let c = consent(REPORT_DOMAIN, hub, &child, &y, Utc::now());
        state.apply(&HubEvent::MemberOfReported { member: x.to_string(), of: y.to_string(), consent: c }, Utc::now(), 9);

        let act = Act::addressed(m, ActAddress::Lct { canonical: "lct:web4:mb32:peer".into() }, "coordination",
            SubstanceRef::new("forum/p.md", "sha256-content:00", SubstanceMedium::Other), Utc::now());
        let sign = |a: &ActAs, act: &Act| ActAs { signature_hex: child.sign(&a.statement(hub, act).unwrap()).to_hex(), ..a.clone() };
        let unsigned = ActAs { lct: x.to_string(), issued_at: Utc::now().to_rfc3339(), edge_epoch: 9, router_epoch: 4,
            signature_hex: String::new() };
        let ok = sign(&unsigned, &act);
        ok.verify(&state, hub, &act, Utc::now()).expect("the child signed, through its router");

        let code = |r: Result<(), ActAsRefusal>| r.unwrap_err().code();
        // 1. carried by someone other than x's router member
        let other = Act { actor_lct: Uuid::new_v4(), ..act.clone() };
        assert_eq!(code(sign(&unsigned, &other).verify(&state, hub, &other, Utc::now())), "not_the_router");
        // 2. stale edge, stale router registration (a same-member re-key moves router_epoch)
        assert_eq!(code(sign(&ActAs { edge_epoch: 8, ..unsigned.clone() }, &act).verify(&state, hub, &act, Utc::now())), "stale_epoch");
        let mut rekeyed = state.clone();
        rekeyed.apply(&HubEvent::RouterRegistered { router_lct: y.to_string(), member: m, issued_at: 11 }, Utc::now(), 12);
        assert_eq!(code(ok.verify(&rekeyed, hub, &act, Utc::now())), "stale_epoch");
        // 3. outside the window, and a non-UTC spelling of a valid instant
        let old = (Utc::now() - chrono::Duration::minutes(11)).to_rfc3339();
        assert_eq!(code(sign(&ActAs { issued_at: old, ..unsigned.clone() }, &act).verify(&state, hub, &act, Utc::now())),
            "issued_at_outside_window");
        let offset = Utc::now().with_timezone(&chrono::FixedOffset::east_opt(3600).unwrap()).to_rfc3339();
        assert_eq!(code(sign(&ActAs { issued_at: offset, ..unsigned.clone() }, &act).verify(&state, hub, &act, Utc::now())),
            "issued_at_outside_window");
        // 4. signed by the router, not x; and a signed act whose content changed after signing
        let by_router = ActAs { signature_hex: router.sign(&unsigned.statement(hub, &act).unwrap()).to_hex(), ..unsigned.clone() };
        assert_eq!(code(by_router.verify(&state, hub, &act, Utc::now())), "bad_child_signature");
        let altered = Act { kind: "handoff".into(), ..act.clone() };
        assert_eq!(code(ok.verify(&state, hub, &altered, Utc::now())), "bad_child_signature");
        // no tagged-text form for FutureSelf
        let selfward = Act { address: ActAddress::FutureSelf { entity: m }, ..act.clone() };
        assert!(ok.statement(hub, &selfward).is_none());
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
        let local = now.with_timezone(&chrono::FixedOffset::east_opt(2 * 3600).unwrap()).to_rfc3339();
        let mut offset = consent(REPORT_DOMAIN, hub, &x, &yl, now);
        offset.issued_at = local.clone();
        offset.signature_hex = x.sign(&consent_bytes(REPORT_DOMAIN, hub, &xl, &yl, &local)).to_hex();
        assert!(offset.verify(REPORT_DOMAIN, hub, &xl, &yl, now).is_err(), "a +02:00 issued_at is refused: UTC only");
        // Small-order key (PRD rev 11): the identity point decompresses but is weak. A consent
        // naming it is refused even though the "member" LCT derives from it.
        let mut weak_bytes = [0u8; 32]; weak_bytes[0] = 1;
        let weak = PublicKey::from_bytes(&weak_bytes).expect("the identity point decompresses");
        assert!(weak.is_weak());
        let weak_lct = CanonicalLctId::derive(&weak);
        let weak_consent = Consent { pubkey_hex: hex::encode(weak_bytes), signature_hex: "00".repeat(64),
            issued_at: now.to_rfc3339() };
        let err = weak_consent.verify(REPORT_DOMAIN, hub, &weak_lct, &yl, now).unwrap_err();
        assert!(err.to_string().contains("small-order"), "{err}");
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
