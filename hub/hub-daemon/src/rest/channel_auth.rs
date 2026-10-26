// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! LCT identity convergence, Slice C (hub/docs/PRD_LCT_IDENTITY_CONVERGENCE.md): signer convergence.
//!
//! A member whose canonical LCT (Slice B `resolve`) vouches an operational key under
//! `HUB_CHANNEL_PURPOSE` authenticates the sealed channel with THAT key, tried before the UUID pin.
//! The pin stays an accepted compatibility path (C2), and the key that actually opened the request is
//! reported as `caller_auth` evidence (C3). The document is read from the projection at request time,
//! so a rotation takes effect on the first request after its `LctPublished` is projected. Hub-originated
//! notices are sealed to the same vouched key when one resolves (C6).

use super::*;
use web4_core::crypto::PublicKey;
use web4_core::lct::HUB_CHANNEL_PURPOSE;

/// A member's usable vouched `hub-channel` keys, with the registry evidence they were read from.
#[derive(Clone, Debug)]
pub(super) struct VouchedChannelKey {
    pub canonical: hub_lib::ids::CanonicalLctId,
    /// Every validly vouched, NOT superseded `hub-channel` key, in document order (CBP #928 finding 3:
    /// a document may carry several; each is tried). Never empty. `keys[0]` is the one C6 seals to.
    pub keys: Vec<PublicKey>,
    /// The registry version the document was read at, so a `caller_auth` record stays reproducible
    /// after a republish or rotation (Legion, #924).
    pub version: u32,
}

/// The founding Sovereign's key, as `resolve` needs it: the live signer, else the public identity file
/// while locked (the same order as `/.well-known` and `admin_lct_resolve`).
pub(super) fn sovereign_key(s: &RestState) -> Option<PublicKey> {
    s.signer.public_key().or_else(|| {
        PublicIdentity::read(&s.paths.root)
            .and_then(|p| p.sovereign_pubkey_hex)
            .and_then(|h| hex::decode(h).ok())
            .and_then(|b| <[u8; 32]>::try_from(b).ok())
            .and_then(|b| PublicKey::from_bytes(&b).ok())
    })
}

/// The vouched `hub-channel` key of `member`'s CURRENT canonical presence, if its published document
/// vouches one validly. The second value is the C5 note: set when the document carries a `hub-channel`
/// entry but no entry for it verifies (never authenticated on; fail closed to the pin).
pub(super) fn vouched_channel_key(state: &HubState, member: Uuid, sovereign: Option<&PublicKey>)
    -> (Option<VouchedChannelKey>, Option<String>) {
    use hub_lib::lct_resolve::{resolve, Reference, Resolution};
    let reference = Reference::Member(hub_lib::ids::HubMemberId::from_uuid(member));
    let Resolution::Resolved { links, .. } = resolve(state, &reference, sovereign) else { return (None, None) };
    let Some(link) = links.iter().find(|l| l.current) else { return (None, None) };
    let doc = &link.entry.document;
    let valid: Vec<PublicKey> = doc.valid_operational_keys().into_iter()
        .filter(|(p, _)| p == HUB_CHANNEL_PURPOSE).map(|(_, k)| k).collect();
    // C7 at the point of use (CBP #928 finding 1): the publish route refuses a replayed document, but
    // that check can race a concurrent publish, and the fold only records. So a key this LCT has
    // superseded is never usable, whatever order the ledger landed in.
    let superseded = state.superseded_opkeys.get(&link.canonical);
    let (usable, stale): (Vec<PublicKey>, Vec<PublicKey>) = valid.into_iter().partition(|k| {
        !superseded.is_some_and(|s| s.contains(&(HUB_CHANNEL_PURPOSE.to_string(), k.to_hex())))
    });
    if !usable.is_empty() {
        return (Some(VouchedChannelKey { canonical: link.canonical.clone(), keys: usable,
            version: link.entry.version }), None);
    }
    if !stale.is_empty() {
        return (None, Some(format!(
            "{}'s current document vouches a {HUB_CHANNEL_PURPOSE} key this LCT has already superseded \
             (C7); it was ignored and the pin was used", link.canonical)));
    }
    if doc.operational_keys.iter().any(|k| k.purpose == HUB_CHANNEL_PURPOSE) {
        return (None, Some(format!(
            "{}'s document carries a {HUB_CHANNEL_PURPOSE} entry whose proof does not verify under its \
             binding key; it was ignored and the pin was used", link.canonical)));
    }
    (None, None)
}

/// Which key authenticated a channel request (C3: on the response now, the ledger in Slice D).
pub(super) fn caller_auth_lct(v: &VouchedChannelKey, key: &PublicKey) -> serde_json::Value {
    serde_json::json!({"method": "lct_vouched_operational_key", "canonical": v.canonical,
        "purpose": HUB_CHANNEL_PURPOSE, "key": key.to_hex(), "version": v.version})
}

pub(super) fn caller_auth_pin(member: Uuid, key: &PublicKey) -> serde_json::Value {
    serde_json::json!({"method": "member_key_pin", "member": member, "key": key.to_hex()})
}

pub(super) fn caller_auth_external(key: &PublicKey) -> serde_json::Value {
    serde_json::json!({"method": "self_vouched_external", "key": key.to_hex()})
}

/// An act the hub itself originates (a notice to a citizen): no request authenticated it. Named so that
/// law can deny `"unknown"` without an exception for the hub's own acts (Legion, #933).
pub(super) fn caller_auth_hub_originated() -> serde_json::Value {
    serde_json::json!({"method": "hub_originated"})
}

/// An act the operator caused on the loopback operator plane (:8772). Admission there is the loopback
/// bind, not a key, so no key leaf is claimed.
pub(super) fn caller_auth_operator_plane() -> serde_json::Value {
    serde_json::json!({"method": "operator_plane"})
}

// ---- Slice D-a: identity evidence on the event (gate + ledger see one value) ----

const UNKNOWN: &str = "unknown";
const NONE: &str = "none";

/// The `caller_auth` value as evidence leaves. Every leaf is present: a method's inapplicable fields are
/// `"none"`, and an absent `caller_auth` (an act not carried by a channel request) is all `"unknown"`.
fn caller_auth_evidence(v: Option<&serde_json::Value>) -> (hub_lib::events::CallerAuthEvidence, bool) {
    use hub_lib::events::CallerAuthEvidence as C;
    let Some(v) = v else {
        return (C { method: UNKNOWN.into(), canonical: UNKNOWN.into(), purpose: UNKNOWN.into(),
            key: UNKNOWN.into(), version: UNKNOWN.into(), member: UNKNOWN.into() }, true);
    };
    let leaf = |k: &str| match v.get(k) {
        Some(serde_json::Value::String(s)) => s.clone(),
        Some(serde_json::Value::Null) | None => NONE.into(),
        Some(other) => other.to_string(),
    };
    (C { method: leaf("method"), canonical: leaf("canonical"), purpose: leaf("purpose"), key: leaf("key"),
        version: leaf("version"), member: leaf("member") }, false)
}

/// Assemble the evidence for `actor` against `state` (FR5: evidence, never a verdict). Every field is
/// present; an unresolvable fact is `"unknown"` and listed in `unknown`.
pub(super) fn identity_evidence(state: &HubState, actor: Uuid, caller_auth: Option<&serde_json::Value>,
    sovereign: Option<&PublicKey>) -> hub_lib::events::IdentityEvidence {
    use hub_lib::events::{HubObservations, IdentityEvidence, LastWitnessedAct};
    use hub_lib::lct_resolve::{resolve, Reference, Resolution};
    let mut unknown = Vec::new();
    let (caller_auth, ca_unknown) = caller_auth_evidence(caller_auth);
    if ca_unknown { unknown.push("caller_auth".to_string()); }

    let link = match resolve(state, &Reference::Member(hub_lib::ids::HubMemberId::from_uuid(actor)), sovereign) {
        Resolution::Resolved { links, .. } => links.into_iter().find(|l| l.current),
        _ => None,
    };
    let (canonical, registry_version, claimed_status) = match &link {
        Some(l) => (l.canonical.to_string(), l.entry.version.to_string(),
            serde_json::to_value(&l.entry.document.status).ok()
                .and_then(|v| v.as_str().map(str::to_string)).unwrap_or_else(|| UNKNOWN.into())),
        None => {
            unknown.extend(["canonical", "registry_version", "claimed_status"].map(String::from));
            (UNKNOWN.into(), UNKNOWN.into(), UNKNOWN.into())
        }
    };
    let against_interest = match claimed_status.as_str() {
        "active" => "false".to_string(),
        UNKNOWN => UNKNOWN.to_string(),
        _ => "true".to_string(),
    };
    if against_interest == UNKNOWN && !unknown.contains(&"against_interest".to_string()) {
        unknown.push("against_interest".into());
    }
    // Newest act as carrier, or as speaker via on_behalf_of (relayed acts count; Sprout on #930).
    let as_member = state.last_act_by_member.get(&actor).copied();
    let as_lct = (canonical != UNKNOWN).then(|| state.last_act_by_lct.get(&canonical).copied()).flatten();
    let last = [as_member, as_lct].into_iter().flatten().max_by_key(|(i, _)| *i);
    let last_witnessed_act = match last {
        Some((index, at)) => LastWitnessedAct { index: index.to_string(), at: at.to_rfc3339() },
        None => LastWitnessedAct { index: NONE.into(), at: NONE.into() },
    };
    IdentityEvidence { caller_auth, canonical, registry_version, claimed_status, against_interest,
        hub_observations: HubObservations { last_witnessed_act }, unknown }
}

/// THE constructor for a new `ReferencedAct` (Slice D-a): it always assembles the identity evidence, so
/// a new act never carries `identity_evidence: None` (an absent field fails open at the gate; Legion).
pub(super) async fn referenced_act_event(s: &RestState, act: web4_core::act::Act,
    on_behalf_of: Option<hub_lib::routing::ActAs>, caller_auth: Option<&serde_json::Value>) -> HubEvent {
    let sovereign = sovereign_key(s);
    let state = { let l = s.ledger.lock().await; s.projected(&l) };
    let evidence = identity_evidence(&state, act.actor_lct, caller_auth, sovereign.as_ref());
    HubEvent::ReferencedAct { act, on_behalf_of, identity_evidence: Some(evidence) }
}

/// A retry of an already-built act re-assembles its evidence against the CURRENT ledger, keeping the
/// caller_auth it was gated on, so the entry that lands carries the value that attempt's gate matched.
pub(super) async fn regated(s: &RestState, event: &HubEvent) -> HubEvent {
    match event {
        HubEvent::ReferencedAct { act, on_behalf_of, identity_evidence } => {
            let ca = identity_evidence.as_ref().and_then(|e| (e.caller_auth.method != UNKNOWN)
                .then(|| serde_json::to_value(&e.caller_auth).ok()).flatten());
            referenced_act_event(s, act.clone(), on_behalf_of.clone(), ca.as_ref()).await
        }
        other => other.clone(),
    }
}
