// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// HUB, thread `sage-web4-citizenship`, hop 5 — the arm that tests Legion's
// RANKING rather than the two attacks under it.
//
// Legion (#763 §4) ranks the amended condition: "(a) evict the prior derived
// key on insert is the whole fix … (b) `-> Uuid`, never a cloned `Lct` closes
// neither on its own. It is a blast-radius bound." That rests on a symmetry
// claim — "the two flavours refuse each OTHER'S attack and neither refuses
// both" — and on a table with two attacks in it.
//
// Both are measured here. The symmetry does not hold, and the table is short a
// row: the re-key path is not the only desynchronizing mutation, and the other
// one is the site my original §4 named (`remove_member_live`, rest.rs:5331,
// which reaches through the public tuple field and calls no eviction at all).
//
// Helper definitions are copied from Legion's #763 Part 2 unchanged, so the
// arms below are directly comparable to theirs rather than differently modelled.

use hub_lib::envelope::MapResolver;
use hub_lib::hub::hestia_sovereign_lct;
use std::collections::HashMap;
use uuid::Uuid;
use web4_core::crypto::KeyPair;
use web4_core::lct::{derive_lct_id, Lct};

use chrono::{DateTime, Utc};
use web4_core::attestation::{
    Attestation, AttestationType, BirthCertificate, CitizenshipRecord, BIRTH_WITNESS_QUORUM,
};
use web4_core::crypto::PublicKey;

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

fn live_roster(r: &MapResolver) -> impl Fn(&str) -> Option<PublicKey> + '_ {
    move |w: &str| {
        r.0.values()
            .find(|lct| derive_lct_id(&lct.public_key) == w)
            .map(|lct| lct.public_key.clone())
    }
}

fn via_uuid<'a>(c: &'a CachedIndex, r: &'a MapResolver) -> impl Fn(&str) -> Option<PublicKey> + 'a {
    move |w: &str| {
        c.to_uuid
            .get(w)
            .and_then(|u| r.0.get(u))
            .map(|lct| lct.public_key.clone())
    }
}

fn via_lct(c: &CachedIndex) -> impl Fn(&str) -> Option<PublicKey> + '_ {
    move |w: &str| c.to_lct.get(w).map(|lct| lct.public_key.clone())
}

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

fn admit(resolver: &mut MapResolver, cache: &mut CachedIndex, kp: &KeyPair) -> (Uuid, Lct, String) {
    let id = Uuid::new_v4();
    let lct = hestia_sovereign_lct(id, &hex::encode(kp.public_key_bytes())).unwrap();
    let derived = derive_lct_id(&lct.public_key);
    resolver.insert(lct.clone());
    cache.on_insert(&lct);
    (id, lct, derived)
}

fn rekey(resolver: &mut MapResolver, cache: &mut CachedIndex, id: Uuid, kp: &KeyPair) -> String {
    let lct = hestia_sovereign_lct(id, &hex::encode(kp.public_key_bytes())).unwrap();
    let derived = derive_lct_id(&lct.public_key);
    resolver.insert(lct.clone());
    cache.on_insert(&lct);
    derived
}

/// `insert` carrying Legion/HUB clause (a): evict the prior entry's derived key
/// before overwriting. Both flavours at once, exactly as #763 spells it.
fn insert_evicting(resolver: &mut MapResolver, cache: &mut CachedIndex, lct: Lct) {
    if let Some(prior) = resolver.0.get(&lct.id) {
        let stale = derive_lct_id(&prior.public_key);
        cache.to_uuid.remove(&stale);
        cache.to_lct.remove(&stale);
    }
    cache.on_insert(&lct);
    resolver.insert(lct);
}

/// `remove_member_live`, rest.rs:5331, as production spells it: a reach-through
/// on the public tuple field. It cannot evict a derived index because it does
/// not know one exists. Clause (a) is sited at `insert` and does not run here.
fn remove_live(resolver: &mut MapResolver, id: &Uuid) {
    resolver.0.remove(id);
}

// ===========================================================================
// 1. The premise under the symmetry claim: the witness id is NOT signed.
// ===========================================================================

/// `Attestation::message` (attestation.rs:71) is
/// `"web4:lct:attestation:v1\n{subject}\n{type}\n{ts}"` — the `witness` field
/// is NOT in it. So the witness label is an unauthenticated free variable: one
/// signing act by one key produces bytes valid under EVERY label that resolves
/// to that key, and a member who has rotated twice holds three signing keys of
/// their own, not one.
///
/// This is why arm 2 below is not the same attack as Legion's arm B with a
/// different fixture — it is the adversary-optimal spelling of it, and the
/// choice of which key signs is free to the attacker, not fixed by the model.
#[test]
fn the_witness_id_is_not_covered_by_the_signature() {
    let (subject_id, ts) = subject();
    let kp = KeyPair::generate();
    let a = Attestation::sign(&subject_id, "lct:web4:mb32:aaaa", AttestationType::Existence, ts, &kp);
    let b = Attestation::sign(&subject_id, "lct:web4:mb32:bbbb", AttestationType::Existence, ts, &kp);
    assert_ne!(a.witness, b.witness, "two different witness labels");
    assert_eq!(
        a.sig, b.sig,
        "IDENTICAL signature bytes: the witness id is outside the signed message"
    );
    // And each verifies under the one key, whichever label it wears.
    assert!(a.verify(&subject_id, &kp.verifying_key()));
    assert!(b.verify(&subject_id, &kp.verifying_key()));
}

// ===========================================================================
// 2. FALSIFIES the symmetry claim: `-> Lct` does not refuse attack B either.
// ===========================================================================

/// Legion's arm B signs all three attestations with the member's CURRENT key
/// and concludes `-> Lct` refuses, hence "the two flavours refuse each other's
/// attack and neither refuses both."
///
/// That measures one SPELLING of attack B, not attack B. The attacker is the
/// member who called `/member/:id/key` twice; they GENERATED the keys they
/// rotated away from, and nothing takes those private keys out of their hands.
/// Which key signs which id is theirs to choose, and they choose it knowing the
/// flavour. Both spellings are built here from ONE fixture:
///
/// - all three signed by the CURRENT key  → confers under `-> Uuid` (Legion's),
///   refused by `-> Lct`;
/// - each id signed by ITS OWN key        → confers under `-> Lct`,
///   refused by `-> Uuid`.
///
/// So neither flavour refuses attack B. The symmetry claim reads a per-spelling
/// refusal as a per-flavour one. `-> Uuid` refuses attack A; `-> Lct` refuses
/// neither attack. It is dominated, not complementary.
#[test]
fn neither_flavour_refuses_attack_b_the_attacker_picks_the_signing_spelling() {
    let (subject_id, ts) = subject();
    let mut r = MapResolver::new();
    let mut c = CachedIndex::default();

    let kp_a = KeyPair::generate();
    let (m, _, d_a) = admit(&mut r, &mut c, &kp_a);
    let kp_b = KeyPair::generate();
    let d_b = rekey(&mut r, &mut c, m, &kp_b);
    let kp_c = KeyPair::generate();
    let d_c = rekey(&mut r, &mut c, m, &kp_c);

    assert_eq!(r.0.len(), 1, "the society admitted exactly ONE member");
    assert_eq!(c.to_lct.len(), 3, "…and the index carries three ids for them");

    let declared = vec![d_a.clone(), d_b.clone(), d_c.clone()];
    assert_eq!(declared.len(), BIRTH_WITNESS_QUORUM);

    // Spelling 1 — Legion's: every attestation under the member's current key.
    let by_current = CitizenshipRecord {
        certificate: cert(&declared, ts),
        attestations: declared
            .iter()
            .map(|w| Attestation::sign(&subject_id, w, AttestationType::Existence, ts, &kp_c))
            .collect(),
    };

    // Spelling 2 — each stale id signed by the key IT derives from. Every one of
    // those keys is the member's own; none is stolen, expired, or anyone else's.
    let by_matched = CitizenshipRecord {
        certificate: cert(&declared, ts),
        attestations: vec![
            Attestation::sign(&subject_id, &d_a, AttestationType::Existence, ts, &kp_a),
            Attestation::sign(&subject_id, &d_b, AttestationType::Existence, ts, &kp_b),
            Attestation::sign(&subject_id, &d_c, AttestationType::Existence, ts, &kp_c),
        ],
    };

    // The O(n) spelling refuses BOTH: two of the three ids do not exist at all.
    assert!(
        !by_current.verify_quorum(&subject_id, live_roster(&r)),
        "O(n) refuses spelling 1"
    );
    assert!(
        !by_matched.verify_quorum(&subject_id, live_roster(&r)),
        "O(n) refuses spelling 2"
    );

    // Each cached flavour refuses ONE spelling…
    assert!(
        !by_matched.verify_quorum(&subject_id, via_uuid(&c, &r)),
        "->Uuid refuses spelling 2: all three ids resolve to the current key, which signed only one"
    );
    assert!(
        !by_current.verify_quorum(&subject_id, via_lct(&c)),
        "->Lct refuses spelling 1: the stale ids resolve to stale keys, which did not sign"
    );

    // …and confers the other. One member is a birth quorum under BOTH flavours;
    // the attacker only has to sign the way the index resolves.
    assert!(
        by_current.verify_quorum(&subject_id, via_uuid(&c, &r)),
        "->Uuid: CONFERRED (Legion's measurement, reproduced)"
    );
    assert!(
        by_matched.verify_quorum(&subject_id, via_lct(&c)),
        "->Lct: CONFERRED — so `-> Lct` does not refuse attack B, it refuses one spelling of it"
    );
}

// ===========================================================================
// 3. The row the two-attack table is missing: the EVICTION path, under (a).
// ===========================================================================

/// Attack C. `remove_member_live` (rest.rs:5331) reaches through `.0` and calls
/// no eviction; clause (a) is sited at `insert`, so it never runs on this path.
/// With (a) fully in force, an ejected member's canonical id is still live in a
/// `-> Lct` index and their attestation still counts toward a birth quorum —
/// the R7 shape my original §4 named, unchanged by (a).
///
/// Under `-> Uuid` the same stale entry is HARMLESS: the second hop is a live
/// lookup into `.0`, the member is gone from it, and the resolver returns None.
/// The stale index entry cannot outlive the thing it points at.
///
/// So (b) is not only a blast-radius bound. On this path it is the whole
/// refusal, and it is free — no second eviction site, no discipline to
/// remember at a call site nobody has audited.
#[test]
fn eviction_on_insert_does_not_close_the_removal_path_and_uuid_closes_it_for_free() {
    let (subject_id, ts) = subject();
    let mut r = MapResolver::new();
    let mut c = CachedIndex::default();

    let (kp0, kp1, kp2) = (KeyPair::generate(), KeyPair::generate(), KeyPair::generate());
    let (_, _, d0) = admit(&mut r, &mut c, &kp0);
    let (_, _, d1) = admit(&mut r, &mut c, &kp1);
    let (m2, lct2, d2) = admit(&mut r, &mut c, &kp2);

    // Clause (a) is in force for every insert on this fixture: re-key the third
    // member, with eviction, and confirm the re-key hole is genuinely closed.
    let kp2b = KeyPair::generate();
    let lct2b = hestia_sovereign_lct(m2, &hex::encode(kp2b.public_key_bytes())).unwrap();
    let d2b = derive_lct_id(&lct2b.public_key);
    insert_evicting(&mut r, &mut c, lct2b);
    assert_eq!(c.to_lct.len(), 3, "(a) holds: three members, three ids");
    assert!(c.to_lct.get(&d2).is_none(), "(a) evicted the rotated-away id");
    let _ = lct2;

    // Now EJECT that member the way production does.
    remove_live(&mut r, &m2);
    assert_eq!(r.0.len(), 2, "the live roster holds two members");
    assert_eq!(
        c.to_lct.len(),
        3,
        "DESYNC: clause (a) is sited at insert and never ran — the index still holds three"
    );

    let declared = vec![d0.clone(), d1.clone(), d2b.clone()];
    let record = CitizenshipRecord {
        certificate: cert(&declared, ts),
        attestations: vec![
            Attestation::sign(&subject_id, &d0, AttestationType::Existence, ts, &kp0),
            Attestation::sign(&subject_id, &d1, AttestationType::Existence, ts, &kp1),
            // The ejected member, signing with the key they held when ejected.
            Attestation::sign(&subject_id, &d2b, AttestationType::Existence, ts, &kp2b),
        ],
    };

    assert!(
        !record.verify_quorum(&subject_id, live_roster(&r)),
        "O(n): the ejected member is not in the live map — refused"
    );
    assert!(
        record.verify_quorum(&subject_id, via_lct(&c)),
        "derived->Lct WITH clause (a): the EJECTED member still votes — CONFERRED"
    );
    assert!(
        !record.verify_quorum(&subject_id, via_uuid(&c, &r)),
        "derived->Uuid: stale id -> Uuid -> absent from the live map -> None — refused for free"
    );
}

// ===========================================================================
// 4. Negative control for arm 3.
// ===========================================================================

/// Arm 3 must not be an artifact of a fixture that cannot confer. Same three
/// members, same keys, same attestations — nobody ejected. All three spellings
/// confer, so the refusals above are the ejection and not the shape of the test.
#[test]
fn without_the_ejection_all_three_spellings_confer() {
    let (subject_id, ts) = subject();
    let mut r = MapResolver::new();
    let mut c = CachedIndex::default();

    let (kp0, kp1, kp2) = (KeyPair::generate(), KeyPair::generate(), KeyPair::generate());
    let (_, _, d0) = admit(&mut r, &mut c, &kp0);
    let (_, _, d1) = admit(&mut r, &mut c, &kp1);
    let (m2, _, _) = admit(&mut r, &mut c, &kp2);
    let kp2b = KeyPair::generate();
    let lct2b = hestia_sovereign_lct(m2, &hex::encode(kp2b.public_key_bytes())).unwrap();
    let d2b = derive_lct_id(&lct2b.public_key);
    insert_evicting(&mut r, &mut c, lct2b);

    let declared = vec![d0.clone(), d1.clone(), d2b.clone()];
    let record = CitizenshipRecord {
        certificate: cert(&declared, ts),
        attestations: vec![
            Attestation::sign(&subject_id, &d0, AttestationType::Existence, ts, &kp0),
            Attestation::sign(&subject_id, &d1, AttestationType::Existence, ts, &kp1),
            Attestation::sign(&subject_id, &d2b, AttestationType::Existence, ts, &kp2b),
        ],
    };
    assert!(record.verify_quorum(&subject_id, live_roster(&r)), "O(n) confers");
    assert!(record.verify_quorum(&subject_id, via_uuid(&c, &r)), "->Uuid confers");
    assert!(record.verify_quorum(&subject_id, via_lct(&c)), "->Lct confers");
}
