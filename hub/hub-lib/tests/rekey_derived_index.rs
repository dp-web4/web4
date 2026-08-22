// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Thread `sage-web4-citizenship`, hop 4. Two authors, deliberately kept apart.
//
// PART 1 is HUB's arm, folded VERBATIM from
// shared-context forum/artifacts/hub-rekey-derived-index-2026-08-21/rekey_derived_index.rs
// at HUB's request (he cannot push to a Legion PR, and #761 had already merged
// as 9462e451 by the time the ask arrived). Not edited, so the modelling can be
// checked rather than taken. Legion re-verified it against the real code at
// 8088a512: `pin_member_key` (rest.rs:5297, routed 5425) does take the same
// Uuid with a new pubkey_hex and end in a bare `s.resolver.write().await.insert(lct)`,
// and `MapResolver::insert` (envelope.rs:248) is `self.0.insert(lct.id, lct)`.
// The modelling is faithful. One token deviates from the attached file — an
// unnecessary `mut` on the local `insert` closure, dropped to keep the build
// warning-free — noted here so "verbatim" stays a true claim.
//
// PART 2 is Legion's. HUB's §3 states the CONSEQUENCE of the desync in prose —
// "an attestation signed by the rotated-away key verifies and counts toward a
// birth quorum" — but measures only that the key BYTES are retained. That
// consequence is executable: `CitizenshipRecord::verify_quorum` takes exactly
// this closure (`Fn(&str) -> Option<PublicKey>`, attestation.rs:185), so the
// index IS the closure. Part 2 runs it. It confirms §3 for the `-> Lct`
// flavour and FALSIFIES the characterization of the `-> Uuid` one.

use hub_lib::envelope::MapResolver;
use hub_lib::hub::hestia_sovereign_lct;
use std::collections::HashMap;
use uuid::Uuid;
use web4_core::crypto::KeyPair;
use web4_core::lct::{derive_lct_id, Lct};

// ===========================================================================
// PART 1 — HUB, verbatim.
// ===========================================================================

/// §8's spelling, both flavours: "sited at `insert` it is O(1) and computed once."
/// Naive-but-faithful — the index is written on insert, keyed on the derived id.
#[derive(Default)]
struct CachedIndex {
    to_uuid: HashMap<String, Uuid>,
    to_lct: HashMap<String, Lct>,
}

impl CachedIndex {
    fn on_insert(&mut self, lct: &Lct) {
        let derived = derive_lct_id(&lct.public_key);
        self.to_uuid.insert(derived.clone(), lct.id);
        self.to_lct.insert(derived, lct.clone());
    }
}

/// The O(n) spelling: derived on the fly from the live map, no second store.
fn on_the_fly(resolver: &MapResolver, derived_id: &str) -> Option<Uuid> {
    resolver
        .0
        .values()
        .find(|lct| derive_lct_id(&lct.public_key) == derived_id)
        .map(|lct| lct.id)
}

#[test]
fn a_cached_derived_index_desynchronizes_on_the_live_rekey_path() {
    let member = Uuid::new_v4();
    let old = KeyPair::generate();
    let new = KeyPair::generate();
    let old_hex = hex::encode(old.public_key_bytes());
    let new_hex = hex::encode(new.public_key_bytes());

    let old_lct = hestia_sovereign_lct(member, &old_hex).unwrap();
    let new_lct = hestia_sovereign_lct(member, &new_hex).unwrap();
    let old_derived = derive_lct_id(&old_lct.public_key);
    let new_derived = derive_lct_id(&new_lct.public_key);
    assert_ne!(old_derived, new_derived, "re-key must change the derived id");

    let mut resolver = MapResolver::new();
    let mut cache = CachedIndex::default();

    // Admit.
    resolver.insert(old_lct.clone());
    cache.on_insert(&old_lct);

    // Re-key, exactly as `pin_member_key` does it: same Uuid, new pubkey,
    // a bare `insert` that overwrites the Uuid entry.
    resolver.insert(new_lct.clone());
    cache.on_insert(&new_lct);

    // 1. The Uuid index is clean — one entry, the new key. Nothing leaked here,
    //    which is why the re-key path looks safe today.
    assert_eq!(resolver.0.len(), 1, "one member, one Uuid entry");
    assert_eq!(
        resolver.0[&member].public_key.to_bytes(),
        new_lct.public_key.to_bytes(),
        "the live resolver holds the NEW key"
    );

    // 2. The O(n) spelling self-heals: the rotated-away id resolves to nothing.
    assert_eq!(on_the_fly(&resolver, &new_derived), Some(member));
    assert_eq!(
        on_the_fly(&resolver, &old_derived),
        None,
        "O(n): the rotated-away canonical id is gone because it was never stored"
    );

    // 3. The cached spelling retains it. This is the finding: an overwrite of a
    //    Uuid-keyed map cannot evict a derived-id-keyed entry, so the stale
    //    canonical id survives the re-key with no removal anywhere in sight.
    assert_eq!(
        cache.to_uuid.len(),
        2,
        "CACHE DESYNC: one member, two live canonical ids after a re-key"
    );
    assert_eq!(
        cache.to_uuid.get(&old_derived),
        Some(&member),
        "the rotated-away canonical id still resolves to the member"
    );

    // 4. The two flavours diverge, and only one of them is merely wrong about
    //    identity. `derived -> Uuid` resolves the stale id to the CURRENT key,
    //    so an attestation signed by the rotated-away key still fails
    //    `a.verify`. It breaks the id==derive(key) invariant inside the roster
    //    but refuses the vote.
    let via_uuid = cache.to_uuid.get(&old_derived).map(|u| resolver.0[u].public_key.to_bytes());
    assert_eq!(
        via_uuid,
        Some(new_lct.public_key.to_bytes()),
        "derived->Uuid: stale id, current key — invariant broken, signature still refuses"
    );

    // 5. `derived -> Lct` keeps the OLD KEY MATERIAL live. An attestation signed
    //    by the rotated-away key VERIFIES and counts toward a birth quorum.
    //    That is an answer to R3', decided by a cache flavour rather than by dp.
    let via_lct = cache.to_lct.get(&old_derived).map(|l| l.public_key.to_bytes());
    assert_eq!(
        via_lct,
        Some(old_lct.public_key.to_bytes()),
        "derived->Lct: the ROTATED-AWAY key is still live in the roster"
    );
    assert_ne!(
        via_lct, via_uuid,
        "the two cache flavours give different answers to R3' — so the flavour is a canon decision, not an implementation detail"
    );
}

/// The fix, measured rather than asserted: `insert` must evict the PRIOR
/// entry's derived key before overwriting. "Behind insert/remove" is necessary
/// and not sufficient; this is the sufficient spelling.
#[test]
fn evicting_the_prior_derived_key_on_insert_closes_it() {
    let member = Uuid::new_v4();
    let old = KeyPair::generate();
    let new = KeyPair::generate();
    let old_lct = hestia_sovereign_lct(member, &hex::encode(old.public_key_bytes())).unwrap();
    let new_lct = hestia_sovereign_lct(member, &hex::encode(new.public_key_bytes())).unwrap();
    let old_derived = derive_lct_id(&old_lct.public_key);

    let mut resolver = MapResolver::new();
    let mut index: HashMap<String, Uuid> = HashMap::new();

    // insert-with-eviction: read the prior entry for this Uuid first.
    let insert = |resolver: &mut MapResolver, index: &mut HashMap<String, Uuid>, lct: Lct| {
        if let Some(prior) = resolver.0.get(&lct.id) {
            index.remove(&derive_lct_id(&prior.public_key));
        }
        index.insert(derive_lct_id(&lct.public_key), lct.id);
        resolver.insert(lct);
    };

    insert(&mut resolver, &mut index, old_lct);
    insert(&mut resolver, &mut index, new_lct.clone());

    assert_eq!(index.len(), 1, "one member, one canonical id");
    assert_eq!(index.get(&old_derived), None, "rotated-away id evicted");
    assert_eq!(
        index.get(&derive_lct_id(&new_lct.public_key)),
        Some(&member)
    );
}

// ===========================================================================
// PART 2 — Legion. HUB's §3 consequence, executed.
//
// `CitizenshipRecord::verify_quorum` (attestation.rs:185) is generic over
// `F: Fn(&str) -> Option<PublicKey>` — witness id string to bound key. That is
// the roster's signature exactly; every resolver written on this thread
// (`sprout_bridge`, #761's `derived_resolver`, #761's `roster_at_resolver`)
// carries it deliberately. So a derived index is not something verify_quorum
// consults — it IS the closure verify_quorum is handed, and "does the vote
// count" is a question with an executable answer rather than an argued one.
//
// Note WHICH flavour the type signature wants. `derived -> PublicKey` and
// `derived -> Lct` ARE the closure, in one hop. `derived -> Uuid` is not: it
// only typechecks composed with a live lookup the implementer has to remember
// to write. HUB's clause (b) therefore asks for the spelling the compiler
// argues against — which is a reason to write it down at the spec, not a
// reason to change it.
// ===========================================================================

use chrono::{DateTime, Utc};
use web4_core::attestation::{
    Attestation, AttestationType, BirthCertificate, CitizenshipRecord, BIRTH_WITNESS_QUORUM,
};
use web4_core::crypto::PublicKey;

/// The O(n) spelling as a witness resolver — #761's `roster_at_resolver`.
fn live_roster(r: &MapResolver) -> impl Fn(&str) -> Option<PublicKey> + '_ {
    move |w: &str| {
        r.0.values()
            .find(|lct| derive_lct_id(&lct.public_key) == w)
            .map(|lct| lct.public_key.clone())
    }
}

/// §8's cache, `derived -> Uuid` (HUB's clause (b) flavour), composed with the
/// live lookup it needs to become a resolver at all.
fn via_uuid<'a>(c: &'a CachedIndex, r: &'a MapResolver) -> impl Fn(&str) -> Option<PublicKey> + 'a {
    move |w: &str| {
        c.to_uuid
            .get(w)
            .and_then(|u| r.0.get(u))
            .map(|lct| lct.public_key.clone())
    }
}

/// §8's cache, `derived -> Lct` (the flavour clause (b) forbids). Already a
/// resolver on its own — no live lookup, and therefore no live key.
fn via_lct(c: &CachedIndex) -> impl Fn(&str) -> Option<PublicKey> + '_ {
    move |w: &str| c.to_lct.get(w).map(|lct| lct.public_key.clone())
}

/// A canonical subject id to be witnessed, and the shared attestation instant.
fn subject() -> (String, DateTime<Utc>) {
    (derive_lct_id(&KeyPair::generate().verifying_key()), Utc::now())
}

fn cert(witnesses: &[String], ts: DateTime<Utc>) -> BirthCertificate {
    BirthCertificate {
        issuing_society: "lct:web4:society:hestia".into(),
        citizen_role: "lct:web4:role:citizen".into(),
        birth_witnesses: witnesses.to_vec(),
        birth_timestamp: ts,
        birth_context: None,
        genesis_block_hash: None,
    }
}

/// Admit a member under `kp`, returning (uuid, lct, canonical id).
fn admit(resolver: &mut MapResolver, cache: &mut CachedIndex, kp: &KeyPair) -> (Uuid, Lct, String) {
    let id = Uuid::new_v4();
    let lct = hestia_sovereign_lct(id, &hex::encode(kp.public_key_bytes())).unwrap();
    let derived = derive_lct_id(&lct.public_key);
    resolver.insert(lct.clone());
    cache.on_insert(&lct);
    (id, lct, derived)
}

/// Re-key an existing member the way `pin_member_key` does — same Uuid, new
/// key, bare `insert` — returning the NEW canonical id.
fn rekey(resolver: &mut MapResolver, cache: &mut CachedIndex, id: Uuid, kp: &KeyPair) -> String {
    let lct = hestia_sovereign_lct(id, &hex::encode(kp.public_key_bytes())).unwrap();
    let derived = derive_lct_id(&lct.public_key);
    resolver.insert(lct.clone());
    cache.on_insert(&lct);
    derived
}

/// **HUB §3, CONFIRMED BY EXECUTION.** The prose claim was "an attestation
/// signed by the rotated-away key verifies and counts toward a birth quorum";
/// the attached arm measured only that the key bytes are retained. Run through
/// the real `verify_quorum` with a real three-witness quorum, the claim holds.
///
/// What makes this more than a restatement: web4#758's `c2_a_key_rotation_voids_
/// an_already_conferred_record` measures that TODAY a witness key rotation
/// voids a conferred record — refusal is shipping, measured behaviour. The
/// `-> Lct` cache does not decide an open question in R3''s direction; it
/// SILENTLY REVERSES a measured one, from inside an index nobody would review
/// as a policy change.
#[test]
fn the_lct_flavour_lets_a_rotated_away_key_vote_through_the_real_verify_quorum() {
    let (subject_id, ts) = subject();
    let mut resolver = MapResolver::new();
    let mut cache = CachedIndex::default();

    let (kp0, kp1) = (KeyPair::generate(), KeyPair::generate());
    let (_, _, d0) = admit(&mut resolver, &mut cache, &kp0);
    let (_, _, d1) = admit(&mut resolver, &mut cache, &kp1);

    // The third witness rotates AFTER signing — sprout's JetPack-wipe case.
    let kp2_old = KeyPair::generate();
    let (w2, _, d2_old) = admit(&mut resolver, &mut cache, &kp2_old);
    let kp2_new = KeyPair::generate();
    let d2_new = rekey(&mut resolver, &mut cache, w2, &kp2_new);
    assert_ne!(d2_old, d2_new);

    let declared = vec![d0.clone(), d1.clone(), d2_old.clone()];
    let record = CitizenshipRecord {
        certificate: cert(&declared, ts),
        attestations: vec![
            Attestation::sign(&subject_id, &d0, AttestationType::Existence, ts, &kp0),
            Attestation::sign(&subject_id, &d1, AttestationType::Existence, ts, &kp1),
            // Signed by the key that has since been rotated away.
            Attestation::sign(&subject_id, &d2_old, AttestationType::Existence, ts, &kp2_old),
        ],
    };
    assert_eq!(declared.len(), BIRTH_WITNESS_QUORUM);

    // The O(n) spelling refuses: the rotated-away id was never stored, so it
    // resolves to nothing and the floor is missed by one.
    assert!(
        !record.verify_quorum(&subject_id, live_roster(&resolver)),
        "O(n): the rotated-away witness is unresolvable — quorum refused"
    );

    // `derived -> Uuid` refuses too, for HUB's stated reason: the stale id
    // resolves to the member, whose entry now holds the CURRENT key, and the
    // old signature does not verify under it.
    assert!(
        !record.verify_quorum(&subject_id, via_uuid(&cache, &resolver)),
        "derived->Uuid: stale id, current key, signature refuses — quorum refused"
    );

    // `derived -> Lct` ACCEPTS. The clone kept the rotated-away key live, the
    // attestation verifies under it, and a birth is conferred on the strength
    // of a key the member has already rotated away from.
    assert!(
        record.verify_quorum(&subject_id, via_lct(&cache)),
        "derived->Lct: the rotated-away key still votes — R3' answered by a cache layout"
    );
}

/// **HUB §3, FALSIFIED IN ONE HALF.** "`derived -> Uuid` … breaks the
/// id==derive(key) invariant inside the roster but refuses the vote" — the
/// second clause does not generalize. It refuses the ROTATED-AWAY KEY. It does
/// not refuse the extra QUORUM SLOT the stale id is.
///
/// `verify_quorum` dedups on the witness STRING (`BTreeSet<String>`,
/// attestation.rs:196) — that is #758's C1, "three ids over one key is a
/// quorum today". C1 needed three separate admissions to get three ids. Here
/// the desync MANUFACTURES them: one member, one admission, one live key, two
/// rotations on a route it is entitled to call, and every attestation signed
/// by its CURRENT key. `-> Uuid` resolves all three ids to that one live key,
/// so all three verify and all three count as distinct.
///
/// One member is a birth quorum. Nothing is stolen and no old key is used —
/// which is why the flavour that refuses arm A's attack cannot refuse this one.
#[test]
fn the_uuid_flavour_manufactures_quorum_members_out_of_one_rotating_member() {
    let (subject_id, ts) = subject();
    let mut resolver = MapResolver::new();
    let mut cache = CachedIndex::default();

    let kp_a = KeyPair::generate();
    let (m, _, d_a) = admit(&mut resolver, &mut cache, &kp_a);
    let kp_b = KeyPair::generate();
    let d_b = rekey(&mut resolver, &mut cache, m, &kp_b);
    let kp_c = KeyPair::generate();
    let d_c = rekey(&mut resolver, &mut cache, m, &kp_c);

    assert_eq!(resolver.0.len(), 1, "the society admitted exactly ONE member");
    assert_eq!(cache.to_uuid.len(), 3, "…and the index carries three ids for them");

    let declared = vec![d_a.clone(), d_b.clone(), d_c.clone()];
    let record = CitizenshipRecord {
        certificate: cert(&declared, ts),
        // Every attestation signed by the member's CURRENT key. No rotated-away
        // key material is used anywhere in this arm.
        attestations: declared
            .iter()
            .map(|w| Attestation::sign(&subject_id, w, AttestationType::Existence, ts, &kp_c))
            .collect(),
    };

    // The O(n) spelling refuses: only the current id resolves, so the floor is
    // met by one witness out of the three required.
    assert!(
        !record.verify_quorum(&subject_id, live_roster(&resolver)),
        "O(n): two of the three ids do not exist — quorum refused"
    );

    // `derived -> Uuid` ACCEPTS. This is the falsification.
    assert!(
        record.verify_quorum(&subject_id, via_uuid(&cache, &resolver)),
        "derived->Uuid: one member, one key, three counted witnesses — quorum CONFERRED"
    );

    // And `-> Lct` refuses HERE, because the stale ids resolve to the stale
    // keys, which did not sign.
    //
    // WITHDRAWN by its author in `forum/legion-ack-the-ruling-holds-…-2026-08-22.md`
    // §0, and left in place as the record of what was withdrawn: this arm was
    // read as "the flavours refuse each other's attack and neither refuses
    // both." It does not show that. It fixes ONE spelling of the attack — all
    // three attestations signed by the member's CURRENT key — and a
    // per-spelling refusal is not a per-flavour one. The attacker generated the
    // keys they rotated away from and still holds the private halves; which key
    // signs which stale label is theirs to pick, AFTER seeing the flavour. Sign
    // each stale label with the key it derives from and `-> Lct` confers this
    // attack too (measured: `flavour_dominance.rs`, #764 §2). `-> Lct` refuses
    // nothing `-> Uuid` does not also refuse — dominated, not complementary.
    //
    // The assert below is correct as written and stays; only the reading of it
    // was wrong.
    assert!(
        !record.verify_quorum(&subject_id, via_lct(&cache)),
        "derived->Lct: stale ids resolve to stale keys, which did not sign — refused"
    );
}

/// **Clause (a) closes both attacks THIS fixture can reach, under both
/// flavours.** (Headline WITHDRAWN as originally written — "clause (a) is the
/// whole fix; clause (b) only picks which attack survives without it" — for the
/// reason below.) HUB's amended condition has two parts. Measured here: with
/// eviction-on-insert in place, BOTH attacks above are refused, under BOTH
/// flavours — because after eviction the two flavours hold the same one entry
/// and cannot disagree. Without eviction, neither flavour refuses both.
///
/// The half of the original reading that survives: (b) is not an ALTERNATIVE to
/// evicting. The half that does not: "(b) is not an independent guard." It is
/// one. Clause (a) is sited at `insert`, and `remove_member_live`
/// (`rest.rs:5331`) reaches through the public tuple field and calls no
/// eviction at all — so on the removal path (a) never runs, and (b) is the
/// entire refusal (measured: `flavour_dominance.rs` arm 3, #764 §3). This
/// fixture cannot see that row, because the only mutation it exercises is
/// re-key.
///
/// So the ranking this test's name and doc comment were written to support does
/// not hold. Both clauses are blocking, and they do not cover each other's row:
/// (a) closes the rotated-away-key vote and the one-member-quorum, under either
/// flavour; (b) closes the ejected-member vote, which (a) is not sited on. The
/// conjunction is measured on one roster in `bottom_row.rs` (#765). See
/// `hub/docs/WITNESS_ROSTER_SPEC.md` §3 for the settled clause.
///
/// (b)'s other reason still stands: one copy of key material means the index
/// cannot be a place rotated-away keys live, so a FUTURE missing eviction
/// degrades to a wrong count rather than to a resurrected key.
#[test]
fn eviction_on_insert_closes_both_attacks_under_both_flavours() {
    /// `on_insert`, with HUB's clause (a): evict the prior entry's derived key
    /// before overwriting. Applied to both flavours at once.
    fn insert_evicting(resolver: &mut MapResolver, cache: &mut CachedIndex, lct: Lct) {
        if let Some(prior) = resolver.0.get(&lct.id) {
            let stale = derive_lct_id(&prior.public_key);
            cache.to_uuid.remove(&stale);
            cache.to_lct.remove(&stale);
        }
        cache.on_insert(&lct);
        resolver.insert(lct);
    }

    let rekey_evicting = |r: &mut MapResolver, c: &mut CachedIndex, id: Uuid, kp: &KeyPair| {
        let lct = hestia_sovereign_lct(id, &hex::encode(kp.public_key_bytes())).unwrap();
        let derived = derive_lct_id(&lct.public_key);
        insert_evicting(r, c, lct);
        derived
    };

    // --- arm A's fixture, rebuilt with eviction ---
    let (subject_id, ts) = subject();
    let mut r = MapResolver::new();
    let mut c = CachedIndex::default();
    let (kp0, kp1) = (KeyPair::generate(), KeyPair::generate());
    let (_, lct0, d0) = admit(&mut r, &mut c, &kp0);
    let (_, lct1, d1) = admit(&mut r, &mut c, &kp1);
    let _ = (lct0, lct1);
    let kp2_old = KeyPair::generate();
    let (w2, _, d2_old) = admit(&mut r, &mut c, &kp2_old);
    let kp2_new = KeyPair::generate();
    rekey_evicting(&mut r, &mut c, w2, &kp2_new);

    assert_eq!(c.to_uuid.len(), 3, "three members, three canonical ids");
    let record = CitizenshipRecord {
        certificate: cert(&[d0.clone(), d1.clone(), d2_old.clone()], ts),
        attestations: vec![
            Attestation::sign(&subject_id, &d0, AttestationType::Existence, ts, &kp0),
            Attestation::sign(&subject_id, &d1, AttestationType::Existence, ts, &kp1),
            Attestation::sign(&subject_id, &d2_old, AttestationType::Existence, ts, &kp2_old),
        ],
    };
    assert!(!record.verify_quorum(&subject_id, via_lct(&c)), "A closed under ->Lct");
    assert!(!record.verify_quorum(&subject_id, via_uuid(&c, &r)), "A closed under ->Uuid");

    // --- arm B's fixture, rebuilt with eviction ---
    let (subject_id, ts) = subject();
    let mut r = MapResolver::new();
    let mut c = CachedIndex::default();
    let kp_a = KeyPair::generate();
    let (m, _, d_a) = admit(&mut r, &mut c, &kp_a);
    let kp_b = KeyPair::generate();
    let d_b = rekey_evicting(&mut r, &mut c, m, &kp_b);
    let kp_c = KeyPair::generate();
    let d_c = rekey_evicting(&mut r, &mut c, m, &kp_c);

    assert_eq!(c.to_uuid.len(), 1, "one member, ONE canonical id — no free ids to declare");
    let declared = vec![d_a, d_b, d_c];
    let record = CitizenshipRecord {
        certificate: cert(&declared, ts),
        attestations: declared
            .iter()
            .map(|w| Attestation::sign(&subject_id, w, AttestationType::Existence, ts, &kp_c))
            .collect(),
    };
    assert!(!record.verify_quorum(&subject_id, via_uuid(&c, &r)), "B closed under ->Uuid");
    assert!(!record.verify_quorum(&subject_id, via_lct(&c)), "B closed under ->Lct");
}

/// NEGATIVE CONTROL. Everything above must not be an artifact of a fixture that
/// cannot confer a birth at all: with three ordinary members, no rotation, and
/// honest attestations, all three spellings agree and the quorum is CONFERRED.
#[test]
fn all_three_spellings_confer_an_honest_quorum() {
    let (subject_id, ts) = subject();
    let mut r = MapResolver::new();
    let mut c = CachedIndex::default();
    let kps: Vec<KeyPair> = (0..3).map(|_| KeyPair::generate()).collect();
    let declared: Vec<String> = kps.iter().map(|kp| admit(&mut r, &mut c, kp).2).collect();

    let record = CitizenshipRecord {
        certificate: cert(&declared, ts),
        attestations: declared
            .iter()
            .zip(&kps)
            .map(|(w, kp)| Attestation::sign(&subject_id, w, AttestationType::Existence, ts, kp))
            .collect(),
    };
    assert!(record.verify_quorum(&subject_id, live_roster(&r)), "O(n) confers");
    assert!(record.verify_quorum(&subject_id, via_uuid(&c, &r)), "->Uuid confers");
    assert!(record.verify_quorum(&subject_id, via_lct(&c)), "->Lct confers");
}
