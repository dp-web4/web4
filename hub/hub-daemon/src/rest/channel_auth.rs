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
