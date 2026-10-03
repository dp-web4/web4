// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Member ↔ canonical-presence resolution (PRD_LCT_IDENTITY_CONVERGENCE, Slice B; web4#875).
//!
//! Slice A made a [`HubMemberId`] and a [`CanonicalLctId`] different types. This module is the
//! ONE place that crosses between them, and it does so only on evidence the ledger already
//! witnesses — no new event, no stored mapping:
//!
//! - a key was pinned to the member (`MemberAdded` / `MemberKeyPinned` / `CouncilMemberAdded`,
//!   or the Sovereign's identity key, which `Genesis` never pins and the caller supplies), and
//! - that key derives a canonical id under which a document carrying the SAME key is published
//!   (`LctPublished`).
//!
//! Both facts are witnessed, so the link is too. It is compared on decoded key BYTES, never on
//! hex spellings, and never through `document.id` — the characterization tests in `state.rs`
//! (C8–C11) are the four ways the earlier string-and-uuid walk missed, and each has a test
//! below that this resolver does not.
//!
//! A legacy alias (`lct:web4:member:…`, the hestia member label a document's `legacy_alias`
//! claims to continue) is matched only on documents whose claim RE-VERIFIES here. Verification
//! proves the claim is consistent, not that its publisher owns it — the derivation inputs are
//! public — so an alias claimed by documents that do not all belong to one member refuses.
//!
//! What it deliberately does NOT do: guess. A member with no pinned key, or whose keys derive
//! nothing published, is [`Resolution::Unmapped`] with the reason. A roster name matching two
//! members, a key pinned by two members, or a contested alias is [`Resolution::Ambiguous`] — a
//! forged or reused reference refuses rather than picking one. A published document no member's
//! key derives is [`Resolution::PresenceOnly`]: the presence exists, membership is not shown.
//! Links that no key derivation can show (an operational key vouching for a different binding
//! key) wait on web4#819 and are out of scope here.

use crate::ids::{CanonicalLctId, HubMemberId};
use crate::state::{HubState, RegistryEntry};
use serde::Serialize;
use uuid::Uuid;
use web4_core::crypto::PublicKey;

/// Which witnessed act put a key on a member.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PinSource {
    MemberAdded,
    MemberKeyPinned,
    CouncilMemberAdded,
    /// The founding Sovereign's key, supplied by the caller from the hub's identity store:
    /// `Genesis` seeds the Sovereign's member row and never a key (C8).
    SovereignIdentity,
}

/// One key pinned to a member, as the ledger witnessed it.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct KeyPin {
    pub pubkey_hex: String,
    pub source: PinSource,
    /// The ledger entry that pinned it; `0` for [`PinSource::SovereignIdentity`], which no
    /// entry carries.
    pub ledger_index: u64,
}

/// The prefix of a hestia member label, the legacy id a `legacy_alias` continues.
const LEGACY_MEMBER_PREFIX: &str = "lct:web4:member:";

/// A reference as an operator or a peer would hand it in. [`Reference::parse`] tries the
/// strict forms first, so a string is only treated as a NAME when it is none of the others.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Reference {
    Member(HubMemberId),
    Canonical(CanonicalLctId),
    LegacyAlias(String),
    Name(String),
}

impl Reference {
    pub fn parse(s: &str) -> Self {
        if let Ok(c) = CanonicalLctId::parse(s) {
            return Reference::Canonical(c);
        }
        if s.starts_with(LEGACY_MEMBER_PREFIX) {
            return Reference::LegacyAlias(s.to_string());
        }
        if let Ok(u) = Uuid::parse_str(s) {
            return Reference::Member(HubMemberId::from_uuid(u));
        }
        Reference::Name(s.to_string())
    }
}

/// A published presence: its canonical id and the registry entry the hub serves for it.
#[derive(Clone, Debug, Serialize)]
pub struct Presence {
    pub canonical: CanonicalLctId,
    pub entry: RegistryEntry,
}

/// The evidence for one member → canonical link: which pin's key derived it.
#[derive(Clone, Debug, Serialize)]
pub struct Link {
    pub canonical: CanonicalLctId,
    pub entry: RegistryEntry,
    pub pin: KeyPin,
    /// True when this pin is the member's key in force (the last one witnessed).
    pub current: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum UnmappedReason {
    /// No key was ever pinned to this member, and none was supplied for it.
    NoKeyPinned,
    /// Keys were pinned, but none derives a published document carrying that key.
    NoPublishedPresence { derived_unpublished: Vec<CanonicalLctId> },
}

#[derive(Clone, Debug, Serialize)]
#[serde(tag = "outcome", rename_all = "snake_case")]
pub enum Resolution {
    /// The member, and every published presence one of its pinned keys derives. `links` is
    /// non-empty and in pin order. The link with `current: true` is the presence of the key in
    /// force; if none has it, that key derives nothing published (only earlier ones do).
    Resolved { member: HubMemberId, name: Option<String>, links: Vec<Link> },
    /// The member exists; no presence can be shown for it, and why.
    Unmapped { member: HubMemberId, name: Option<String>, reason: UnmappedReason },
    /// The reference names a published presence that no current member's pinned key derives.
    PresenceOnly { presence: Presence },
    /// More than one member — or presence — answers this reference. Nothing is picked.
    Ambiguous { members: Vec<HubMemberId>, presences: Vec<CanonicalLctId> },
    /// Nothing answers it.
    Unresolved { reason: String },
}

/// Every key pinned to `member`, oldest first, with the caller-supplied Sovereign key added for
/// the founding Sovereign.
fn pins_of(state: &HubState, member: Uuid, sovereign_key: Option<&PublicKey>) -> Vec<KeyPin> {
    let mut pins = state.member_key_pins.get(&member).cloned().unwrap_or_default();
    if state.founding_sovereign_lct_id == Some(member) {
        if let Some(k) = sovereign_key {
            pins.push(KeyPin { pubkey_hex: k.to_hex(), source: PinSource::SovereignIdentity, ledger_index: 0 });
        }
    }
    pins
}

/// Decode a pinned hex key. Case-insensitive, as the daemon's own envelope path is (C10).
fn decode(hex_key: &str) -> Option<PublicKey> {
    let bytes: [u8; 32] = hex::decode(hex_key).ok()?.try_into().ok()?;
    PublicKey::from_bytes(&bytes).ok()
}

/// The canonical id `pin` derives, and the registry entry published under it if that entry's
/// document carries the same key.
fn derive_pin<'s>(state: &'s HubState, pin: &KeyPin) -> Option<(CanonicalLctId, Option<&'s RegistryEntry>)> {
    let key = decode(&pin.pubkey_hex)?;
    let id = CanonicalLctId::derive(&key);
    let entry = state.registry.get(&id).filter(|e| e.document.public_key.to_bytes() == key.to_bytes());
    Some((id, entry))
}

/// The current members with a pinned key that derives the published `canonical`.
fn owners_of(state: &HubState, canonical: &CanonicalLctId, sovereign_key: Option<&PublicKey>) -> Vec<Uuid> {
    state.members.keys().copied()
        .filter(|m| pins_of(state, *m, sovereign_key).iter()
            .any(|p| derive_pin(state, p).is_some_and(|(id, entry)| entry.is_some() && &id == canonical)))
        .collect()
}

fn resolve_member(state: &HubState, member: Uuid, sovereign_key: Option<&PublicKey>) -> Resolution {
    let Some(row) = state.members.get(&member) else {
        return Resolution::Unresolved { reason: format!("{member} is not a member of this hub") };
    };
    let id = HubMemberId::from_uuid(member);
    let name = row.name.clone();
    let pins = pins_of(state, member, sovereign_key);
    if pins.is_empty() {
        return Resolution::Unmapped { member: id, name, reason: UnmappedReason::NoKeyPinned };
    }
    let current_bytes = pins.last().and_then(|p| decode(&p.pubkey_hex)).map(|k| k.to_bytes());
    let mut links: Vec<Link> = Vec::new();
    let mut unpublished: Vec<CanonicalLctId> = Vec::new();
    for pin in pins {
        let Some((canonical, entry)) = derive_pin(state, &pin) else { continue };
        let Some(entry) = entry.cloned() else {
            if !unpublished.contains(&canonical) { unpublished.push(canonical); }
            continue;
        };
        let current = decode(&pin.pubkey_hex).map(|k| k.to_bytes()) == current_bytes;
        // A key re-pinned unchanged is one presence, not two: keep the latest pin as its evidence.
        links.retain(|l| l.canonical != canonical);
        links.push(Link { canonical, entry, pin, current });
    }
    if links.is_empty() {
        Resolution::Unmapped { member: id, name, reason: UnmappedReason::NoPublishedPresence { derived_unpublished: unpublished } }
    } else {
        Resolution::Resolved { member: id, name, links }
    }
}

/// Resolve `reference` against the projection. `sovereign_key` is the founding Sovereign's
/// key from the hub's identity store (the one key the projection cannot hold, C8); pass `None`
/// where it is not available and the Sovereign will read as unmapped rather than vanish.
pub fn resolve(state: &HubState, reference: &Reference, sovereign_key: Option<&PublicKey>) -> Resolution {
    match reference {
        Reference::Member(m) => resolve_member(state, m.as_uuid(), sovereign_key),
        Reference::Name(n) => {
            let matches: Vec<Uuid> = state.members.values()
                .filter(|m| m.name.as_deref() == Some(n.as_str()))
                .map(|m| m.lct_id)
                .collect();
            match matches.as_slice() {
                [] => Resolution::Unresolved { reason: format!("no member is named {n:?}") },
                [one] => resolve_member(state, *one, sovereign_key),
                _ => Resolution::Ambiguous { members: ids(matches), presences: vec![] },
            }
        }
        Reference::Canonical(c) => {
            let Some(entry) = state.registry.get(c) else {
                return Resolution::Unresolved { reason: format!("{c} is not published on this hub") };
            };
            let owners = owners_of(state, c, sovereign_key);
            match owners.as_slice() {
                [] => Resolution::PresenceOnly { presence: Presence { canonical: c.clone(), entry: entry.clone() } },
                [one] => resolve_member(state, *one, sovereign_key),
                _ => Resolution::Ambiguous { members: ids(owners), presences: vec![c.clone()] },
            }
        }
        Reference::LegacyAlias(alias) => {
            // Re-verify every claim here rather than trust that ingest did.
            let claimed: Vec<(&CanonicalLctId, &RegistryEntry)> = state.registry.iter()
                .filter(|(_, e)| e.document.legacy_alias.as_ref()
                    .is_some_and(|a| &a.legacy_id == alias && a.verify()))
                .collect();
            if claimed.is_empty() {
                return Resolution::Unresolved { reason: format!("no published presence verifiably continues {alias}") };
            }
            let mut owners: Vec<Uuid> = Vec::new();
            let mut unowned = false;
            for (c, _) in &claimed {
                let o = owners_of(state, c, sovereign_key);
                unowned |= o.is_empty();
                for m in o { if !owners.contains(&m) { owners.push(m); } }
            }
            match (owners.as_slice(), unowned, claimed.as_slice()) {
                // Every claiming document belongs to the one member (e.g. before and after a re-key).
                ([one], false, _) => resolve_member(state, *one, sovereign_key),
                // One document, no member: the presence exists; membership is not shown.
                ([], true, [(c, e)]) => Resolution::PresenceOnly { presence: Presence { canonical: (*c).clone(), entry: (*e).clone() } },
                _ => Resolution::Ambiguous { members: ids(owners), presences: claimed.iter().map(|(c, _)| (*c).clone()).collect() },
            }
        }
    }
}

fn ids(members: Vec<Uuid>) -> Vec<HubMemberId> {
    members.into_iter().map(HubMemberId::from_uuid).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::events::{HubEvent, LctProvenance};
    use chrono::Utc;
    use web4_core::crypto::KeyPair;
    use web4_core::lct::{LegacyAlias, LegacyDerivation};

    fn keyed(id: Uuid) -> (web4_core::lct::Lct, String, PublicKey) {
        let kp = KeyPair::generate();
        let hex = kp.verifying_key().to_hex();
        (crate::hub::hestia_sovereign_lct(id, &hex).unwrap(), hex, kp.verifying_key())
    }

    fn publish(state: &mut HubState, lct: &web4_core::lct::Lct, at: u64) -> CanonicalLctId {
        let id = CanonicalLctId::derive(&lct.public_key);
        state.apply(&HubEvent::LctPublished {
            lct_id: id.to_string(), document: lct.clone(), published_by: lct.id,
            provenance: LctProvenance::SelfIssued, published_at: Utc::now(),
        }, Utc::now(), at);
        id
    }

    fn add(state: &mut HubState, member: Uuid, name: &str, hex: Option<String>, at: u64) {
        state.apply(&HubEvent::MemberAdded {
            member_lct_id: member, added_by: Uuid::nil(), member_name: Some(name.into()),
            member_pubkey_hex: hex, anchor_level: None, trust_ceiling: None,
        }, Utc::now(), at);
    }

    fn links(r: &Resolution) -> &[Link] {
        match r { Resolution::Resolved { links, .. } => links, other => panic!("expected Resolved, got {other:?}") }
    }

    #[test]
    fn a_pinned_published_member_resolves_from_all_three_references() {
        let mut state = HubState::default();
        let m = Uuid::new_v4();
        let (lct, hex, _) = keyed(m);
        add(&mut state, m, "alice", Some(hex), 1);
        let c = publish(&mut state, &lct, 2);
        for r in [Reference::Member(HubMemberId::from_uuid(m)), Reference::Canonical(c.clone()), Reference::Name("alice".into())] {
            let res = resolve(&state, &r, None);
            let l = links(&res);
            assert_eq!(l.len(), 1);
            assert_eq!(l[0].canonical, c);
            assert_eq!(l[0].pin.source, PinSource::MemberAdded);
            assert_eq!(l[0].pin.ledger_index, 1, "the evidence names the pinning entry");
            assert!(l[0].current);
        }
    }

    /// C8: the Sovereign's key is not in the projection. Without it the Sovereign is reported
    /// unmapped (not silently absent); with the identity-store key it resolves.
    #[test]
    fn the_founding_sovereign_resolves_with_the_identity_key_and_says_so_without_it() {
        let mut state = HubState::default();
        let sov = Uuid::new_v4();
        let (lct, _, key) = keyed(sov);
        state.apply(&HubEvent::Genesis {
            hub_name: "Fleet".into(), charter_hash: "sha256:0".into(),
            founding_sovereign_lct_id: sov, created_at: Utc::now(),
        }, Utc::now(), 0);
        let c = publish(&mut state, &lct, 1);
        let r = Reference::Member(HubMemberId::from_uuid(sov));
        assert!(matches!(resolve(&state, &r, None), Resolution::Unmapped { reason: UnmappedReason::NoKeyPinned, .. }));
        let res = resolve(&state, &r, Some(&key));
        assert_eq!(links(&res)[0].canonical, c);
        assert_eq!(links(&res)[0].pin.source, PinSource::SovereignIdentity);
    }

    /// C9: council holders are pinned into `council_pubkeys`, not `member_pubkeys`.
    #[test]
    fn a_council_holder_resolves() {
        let mut state = HubState::default();
        let h = Uuid::new_v4();
        let (lct, hex, _) = keyed(h);
        state.apply(&HubEvent::CouncilMemberAdded {
            member_lct_id: h, member_pubkey_hex: hex, added_by: Uuid::nil(), member_name: Some("Holder".into()),
        }, Utc::now(), 1);
        let c = publish(&mut state, &lct, 2);
        let res = resolve(&state, &Reference::Canonical(c), None);
        assert_eq!(links(&res)[0].pin.source, PinSource::CouncilMemberAdded);
    }

    /// C10: a mixed-case pin is the same key.
    #[test]
    fn a_mixed_case_pin_resolves() {
        let mut state = HubState::default();
        let m = Uuid::new_v4();
        let (lct, hex, _) = keyed(m);
        add(&mut state, m, "bob", Some(hex.to_uppercase()), 1);
        let c = publish(&mut state, &lct, 2);
        assert_eq!(links(&resolve(&state, &Reference::Member(HubMemberId::from_uuid(m)), None))[0].canonical, c);
    }

    /// C11: the membership uuid need not be the document's id — the key is the link.
    #[test]
    fn a_member_whose_uuid_differs_from_the_document_id_resolves() {
        let mut state = HubState::default();
        let membership = Uuid::new_v4();
        let (lct, hex, _) = keyed(Uuid::new_v4());
        add(&mut state, membership, "carol", Some(hex), 1);
        let c = publish(&mut state, &lct, 2);
        let res = resolve(&state, &Reference::Canonical(c), None);
        assert!(matches!(res, Resolution::Resolved { member, .. } if member.as_uuid() == membership));
    }

    /// A re-key keeps the earlier presence resolvable, and marks which one is in force.
    #[test]
    fn a_rekeyed_member_keeps_its_history_and_marks_the_current_key() {
        let mut state = HubState::default();
        let m = Uuid::new_v4();
        let (old_lct, old_hex, _) = keyed(m);
        let (new_lct, new_hex, _) = keyed(m);
        add(&mut state, m, "dana", Some(old_hex), 1);
        let old_c = publish(&mut state, &old_lct, 2);
        state.apply(&HubEvent::MemberKeyPinned {
            member_lct_id: m, member_pubkey_hex: new_hex, pinned_by: Uuid::nil(),
        }, Utc::now(), 3);
        let new_c = publish(&mut state, &new_lct, 4);

        let res = resolve(&state, &Reference::Member(HubMemberId::from_uuid(m)), None);
        let l = links(&res);
        assert_eq!(l.iter().map(|l| (&l.canonical, l.current)).collect::<Vec<_>>(), vec![(&old_c, false), (&new_c, true)]);
        assert_eq!(l[1].pin.source, PinSource::MemberKeyPinned);
        let back = resolve(&state, &Reference::Canonical(old_c), None);
        assert!(matches!(back, Resolution::Resolved { member, .. } if member.as_uuid() == m),
            "the earlier presence still names the member");
    }

    #[test]
    fn a_key_that_derives_nothing_published_is_unmapped_with_the_derived_id() {
        let mut state = HubState::default();
        let m = Uuid::new_v4();
        let (_, hex, key) = keyed(m);
        add(&mut state, m, "erin", Some(hex), 1);
        let res = resolve(&state, &Reference::Member(HubMemberId::from_uuid(m)), None);
        match res {
            Resolution::Unmapped { member, name, reason } => {
                assert_eq!(member, HubMemberId::from_uuid(m));
                assert_eq!(name.as_deref(), Some("erin"));
                assert_eq!(reason, UnmappedReason::NoPublishedPresence { derived_unpublished: vec![CanonicalLctId::derive(&key)] });
            }
            other => panic!("expected Unmapped, got {other:?}"),
        }
    }

    /// A second member taking an existing roster name makes the name ambiguous: it refuses
    /// rather than resolving to either.
    #[test]
    fn a_duplicated_name_is_ambiguous_not_first_match() {
        let mut state = HubState::default();
        let (real, forger) = (Uuid::new_v4(), Uuid::new_v4());
        let (lct, hex, _) = keyed(real);
        add(&mut state, real, "hub-being", Some(hex), 1);
        publish(&mut state, &lct, 2);
        add(&mut state, forger, "hub-being", Some(keyed(forger).1), 3);
        match resolve(&state, &Reference::Name("hub-being".into()), None) {
            Resolution::Ambiguous { members, .. } => {
                assert_eq!(members.len(), 2);
                assert!(members.contains(&HubMemberId::from_uuid(real)));
                assert!(members.contains(&HubMemberId::from_uuid(forger)));
            }
            other => panic!("a duplicated name must not resolve: {other:?}"),
        }
    }

    /// Two members pinning the same key both derive its presence: ambiguous, not first-wins.
    #[test]
    fn a_key_pinned_by_two_members_is_ambiguous() {
        let mut state = HubState::default();
        let (a, b) = (Uuid::new_v4(), Uuid::new_v4());
        let (lct, hex, _) = keyed(a);
        add(&mut state, a, "a", Some(hex.clone()), 1);
        add(&mut state, b, "b", Some(hex), 2);
        let c = publish(&mut state, &lct, 3);
        assert!(matches!(resolve(&state, &Reference::Canonical(c), None), Resolution::Ambiguous { members, .. } if members.len() == 2));
    }

    /// A published document whose key no member pinned is a presence without a member — the
    /// registry entry is returned, membership is not claimed.
    #[test]
    fn a_published_id_no_member_pinned_is_presence_only() {
        let mut state = HubState::default();
        let (lct, _, _) = keyed(Uuid::new_v4());
        let c = publish(&mut state, &lct, 1);
        match resolve(&state, &Reference::Canonical(c.clone()), None) {
            Resolution::PresenceOnly { presence } => {
                assert_eq!(presence.canonical, c);
                assert_eq!(presence.entry.document.public_key.to_bytes(), lct.public_key.to_bytes());
            }
            other => panic!("expected PresenceOnly, got {other:?}"),
        }
        let unpublished = CanonicalLctId::derive(&KeyPair::generate().verifying_key());
        assert!(matches!(resolve(&state, &Reference::Canonical(unpublished), None), Resolution::Unresolved { .. }));
        assert!(matches!(resolve(&state, &Reference::Member(HubMemberId::from_uuid(Uuid::new_v4())), None), Resolution::Unresolved { .. }));
        assert!(matches!(resolve(&state, &Reference::Name("nobody".into()), None), Resolution::Unresolved { .. }));
    }

    const SOV: &str = "lct:web4:hestia:sovereign:test";

    fn alias_for(plugin: &str) -> LegacyAlias {
        let derivation = LegacyDerivation::HestiaMember { plugin_id: plugin.into(), sovereign: SOV.into() };
        LegacyAlias { legacy_id: derivation.derive(), derivation }
    }

    /// A member with a published, alias-carrying document: the alias resolves to that member.
    fn aliased_member(state: &mut HubState, plugin: &str, at: u64) -> (Uuid, CanonicalLctId, String) {
        let m = Uuid::new_v4();
        let (mut lct, hex, _) = keyed(m);
        let alias = alias_for(plugin);
        lct.legacy_alias = Some(alias.clone());
        add(state, m, plugin, Some(hex), at);
        (m, publish(state, &lct, at + 1), alias.legacy_id)
    }

    #[test]
    fn a_verified_legacy_alias_resolves_to_its_member() {
        let mut state = HubState::default();
        let (m, c, alias) = aliased_member(&mut state, "claude-code", 1);
        assert_eq!(Reference::parse(&alias), Reference::LegacyAlias(alias.clone()));
        let res = resolve(&state, &Reference::parse(&alias), None);
        assert!(matches!(&res, Resolution::Resolved { member, .. } if member.as_uuid() == m));
        assert_eq!(links(&res)[0].canonical, c);
    }

    /// Both documents across a re-key continue the same alias; one member owns both: resolved.
    #[test]
    fn an_alias_carried_across_a_rekey_still_resolves() {
        let mut state = HubState::default();
        let (m, _, alias) = aliased_member(&mut state, "claude-code", 1);
        let (mut next, next_hex, _) = keyed(m);
        next.legacy_alias = Some(alias_for("claude-code"));
        state.apply(&HubEvent::MemberKeyPinned { member_lct_id: m, member_pubkey_hex: next_hex, pinned_by: Uuid::nil() }, Utc::now(), 3);
        publish(&mut state, &next, 4);
        let res = resolve(&state, &Reference::LegacyAlias(alias), None);
        assert_eq!(links(&res).len(), 2);
    }

    /// The derivation inputs are public, so anyone can publish a document whose alias claim
    /// verifies. A second claimant — member or not — makes the alias refuse.
    #[test]
    fn a_contested_alias_is_ambiguous_whoever_the_second_claimant_is() {
        for forger_is_member in [false, true] {
            let mut state = HubState::default();
            let (m, c, alias) = aliased_member(&mut state, "claude-code", 1);
            let forger = Uuid::new_v4();
            let (mut forged, forged_hex, _) = keyed(forger);
            forged.legacy_alias = Some(alias_for("claude-code"));
            assert!(forged.legacy_alias.as_ref().unwrap().verify(), "the forged claim DOES verify: inputs are public");
            if forger_is_member { add(&mut state, forger, "mallory", Some(forged_hex), 3); }
            let fc = publish(&mut state, &forged, 4);
            match resolve(&state, &Reference::LegacyAlias(alias), None) {
                Resolution::Ambiguous { members, presences } => {
                    assert!(members.contains(&HubMemberId::from_uuid(m)));
                    assert_eq!(members.len(), if forger_is_member { 2 } else { 1 });
                    assert!(presences.contains(&c) && presences.contains(&fc));
                }
                other => panic!("a contested alias must refuse (forger member: {forger_is_member}): {other:?}"),
            }
        }
    }

    /// A claim that does not re-derive is ignored even if it reached the registry: the resolver
    /// verifies, it does not trust ingest.
    #[test]
    fn an_alias_claim_that_does_not_verify_is_not_matched() {
        let mut state = HubState::default();
        let m = Uuid::new_v4();
        let (mut lct, hex, _) = keyed(m);
        let mut bad = alias_for("claude-code");
        bad.legacy_id = "lct:web4:member:deadbeefdeadbeefdeadbeef".into();
        lct.legacy_alias = Some(bad);
        add(&mut state, m, "x", Some(hex), 1);
        publish(&mut state, &lct, 2);
        assert!(matches!(resolve(&state, &Reference::parse("lct:web4:member:deadbeefdeadbeefdeadbeef"), None),
            Resolution::Unresolved { .. }));
    }

    #[test]
    fn parse_prefers_the_strict_forms() {
        let c = CanonicalLctId::derive(&KeyPair::generate().verifying_key());
        assert_eq!(Reference::parse(c.as_str()), Reference::Canonical(c));
        let u = Uuid::new_v4();
        assert_eq!(Reference::parse(&u.to_string()), Reference::Member(HubMemberId::from_uuid(u)));
        assert_eq!(Reference::parse("hub-being"), Reference::Name("hub-being".into()));
    }
}
