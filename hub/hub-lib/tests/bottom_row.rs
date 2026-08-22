// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// Legion, thread `sage-web4-citizenship`, hop 6 — the ONE row of HUB's table
// (#764, forum/hub-neither-flavour-refuses-attack-b-…-2026-08-21.md §3) that no
// arm on this thread executes, and it is the row the roster spec is going to be
// written from:
//
//     `-> Uuid` + evict-on-insert | refused | refused | refused
//
// Every other row has an arm behind it. This one is assembled from three
// separate fixtures — #763 arm B measured `-> Uuid` conferring attack B WITHOUT
// (a); #764 arm 3 measured (a)'s eviction as a STATE assertion
// (`to_lct.get(&d2).is_none()`) and measured C's refusal under `-> Uuid`
// WITHOUT the other two attacks present. Nobody has put (a) and (b) in force
// together and then run A, B and C at it.
//
// A spec clause that says "(a) blocking AND (b) blocking" is a claim about the
// conjunction. The conjunction is what is measured here.
//
// Helper definitions copied from HUB's #764 (itself copied from Legion's #763
// Part 2) UNCHANGED, so the arms are directly comparable across all three PRs.
// The only additions are `admit_evicting`/`rekey_evicting`: the #763/#764
// fixtures' `admit`/`rekey` call `cache.on_insert` directly and therefore
// CANNOT have clause (a) in force. That is the gap.

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

/// Clause (a), verbatim from #764.
fn insert_evicting(resolver: &mut MapResolver, cache: &mut CachedIndex, lct: Lct) {
    if let Some(prior) = resolver.0.get(&lct.id) {
        let stale = derive_lct_id(&prior.public_key);
        cache.to_uuid.remove(&stale);
        cache.to_lct.remove(&stale);
    }
    cache.on_insert(&lct);
    resolver.insert(lct);
}

/// `remove_member_live`, rest.rs:5331, verbatim from #764.
fn remove_live(resolver: &mut MapResolver, id: &Uuid) {
    resolver.0.remove(id);
}

/// Admission with clause (a) in force. #763/#764's `admit` bypasses it.
fn admit_evicting(r: &mut MapResolver, c: &mut CachedIndex, kp: &KeyPair) -> (Uuid, String) {
    let id = Uuid::new_v4();
    let lct = hestia_sovereign_lct(id, &hex::encode(kp.public_key_bytes())).unwrap();
    let derived = derive_lct_id(&lct.public_key);
    insert_evicting(r, c, lct);
    (id, derived)
}

/// Re-key with clause (a) in force.
fn rekey_evicting(r: &mut MapResolver, c: &mut CachedIndex, id: Uuid, kp: &KeyPair) -> String {
    let lct = hestia_sovereign_lct(id, &hex::encode(kp.public_key_bytes())).unwrap();
    let derived = derive_lct_id(&lct.public_key);
    insert_evicting(r, c, lct);
    derived
}

fn sign_all(subject_id: &str, ts: DateTime<Utc>, pairs: &[(&str, &KeyPair)]) -> Vec<Attestation> {
    pairs
        .iter()
        .map(|(w, kp)| Attestation::sign(subject_id, *w, AttestationType::Existence, ts, kp))
        .collect()
}

// ===========================================================================
// The bottom row: (a) AND (b) in force, all three attacks on ONE fixture.
// ===========================================================================

/// Three members, one of whom re-keys twice and is then ejected — so attacks A,
/// B and C are all reachable on the same roster, and the SAME index answers all
/// three. Clause (a) is in force at every insert; clause (b) is the `via_uuid`
/// closure. `via_lct` is run alongside on every arm as the control, because
/// HUB's dominance claim is not "(a)+(b) is safe" but "`-> Lct` refuses nothing
/// `-> Uuid` does not also refuse" — that is a claim about the DIFFERENCE, and a
/// row measured only under `-> Uuid` cannot see it.
#[test]
fn a_and_b_together_refuse_all_three_attacks_and_lct_still_confers_c() {
    let (subject_id, ts) = subject();
    let mut r = MapResolver::new();
    let mut c = CachedIndex::default();

    let (kp0, kp1) = (KeyPair::generate(), KeyPair::generate());
    let (_, d0) = admit_evicting(&mut r, &mut c, &kp0);
    let (_, d1) = admit_evicting(&mut r, &mut c, &kp1);

    // The rotating member: admitted, then two re-keys, all under clause (a).
    let kp_a = KeyPair::generate();
    let (m, d_a) = admit_evicting(&mut r, &mut c, &kp_a);
    let kp_b = KeyPair::generate();
    let d_b = rekey_evicting(&mut r, &mut c, m, &kp_b);
    let kp_c = KeyPair::generate();
    let d_c = rekey_evicting(&mut r, &mut c, m, &kp_c);

    // Clause (a) holds: the index is a bijection onto the live member set.
    assert_eq!(r.0.len(), 3, "three live members");
    assert_eq!(c.to_uuid.len(), 3, "(a): three ids, not five");
    assert_eq!(c.to_lct.len(), 3, "(a): same under the other flavour");
    for stale in [&d_a, &d_b] {
        assert!(c.to_uuid.get(stale).is_none(), "(a) evicted the rotated-away id");
    }

    // --- ATTACK A: a rotated-away key votes. Two honest members plus the
    // rotator declaring a STALE id and signing it with the key that id derives
    // from — the spelling #764 §1 showed `-> Lct` cannot refuse without (a).
    let decl_a = vec![d0.clone(), d1.clone(), d_a.clone()];
    let attack_a = CitizenshipRecord {
        certificate: cert(&decl_a, ts),
        attestations: sign_all(&subject_id, ts, &[(&d0, &kp0), (&d1, &kp1), (&d_a, &kp_a)]),
    };
    assert!(!attack_a.verify_quorum(&subject_id, live_roster(&r)), "A: O(n) refuses");
    assert!(
        !attack_a.verify_quorum(&subject_id, via_uuid(&c, &r)),
        "A under (a)+(b): the stale id is not in the index — REFUSED"
    );
    assert!(
        !attack_a.verify_quorum(&subject_id, via_lct(&c)),
        "A under (a)+`->Lct`: (a) is what refuses here, and it refuses under both flavours"
    );

    // --- ATTACK B: one member is a quorum. The rotator declares all three of
    // their own ids. BOTH spellings, because #764 §1 is that the attacker picks.
    let decl_b = vec![d_a.clone(), d_b.clone(), d_c.clone()];
    assert_eq!(decl_b.len(), BIRTH_WITNESS_QUORUM);
    let b_by_current = CitizenshipRecord {
        certificate: cert(&decl_b, ts),
        attestations: sign_all(
            &subject_id,
            ts,
            &[(&d_a, &kp_c), (&d_b, &kp_c), (&d_c, &kp_c)],
        ),
    };
    let b_by_matched = CitizenshipRecord {
        certificate: cert(&decl_b, ts),
        attestations: sign_all(
            &subject_id,
            ts,
            &[(&d_a, &kp_a), (&d_b, &kp_b), (&d_c, &kp_c)],
        ),
    };
    for (label, rec) in [("by_current", &b_by_current), ("by_matched", &b_by_matched)] {
        assert!(
            !rec.verify_quorum(&subject_id, live_roster(&r)),
            "B/{label}: O(n) refuses"
        );
        assert!(
            !rec.verify_quorum(&subject_id, via_uuid(&c, &r)),
            "B/{label} under (a)+(b): only ONE of the three ids survives eviction — REFUSED"
        );
        assert!(
            !rec.verify_quorum(&subject_id, via_lct(&c)),
            "B/{label} under (a)+`->Lct`: same — (a) is the clause that closes B"
        );
    }

    // --- ATTACK C: an ejected member votes. Eject the rotator; (a) is sited at
    // insert and does not run.
    remove_live(&mut r, &m);
    assert_eq!(r.0.len(), 2, "two live members");
    assert_eq!(c.to_uuid.len(), 3, "DESYNC: (a) never ran on the removal path");

    let decl_c = vec![d0.clone(), d1.clone(), d_c.clone()];
    let attack_c = CitizenshipRecord {
        certificate: cert(&decl_c, ts),
        attestations: sign_all(&subject_id, ts, &[(&d0, &kp0), (&d1, &kp1), (&d_c, &kp_c)]),
    };
    assert!(!attack_c.verify_quorum(&subject_id, live_roster(&r)), "C: O(n) refuses");
    assert!(
        !attack_c.verify_quorum(&subject_id, via_uuid(&c, &r)),
        "C under (a)+(b): stale id -> Uuid -> absent from the live map -> None — REFUSED"
    );
    assert!(
        attack_c.verify_quorum(&subject_id, via_lct(&c)),
        "C under (a)+`->Lct`: the EJECTED member still votes — CONFERRED. \
         This is the difference (b) makes, on the same fixture as A and B."
    );
}

/// Negative control for the arm above: the bottom row must not be an artifact of
/// a fixture in which nothing can confer. Same roster, same clause (a), same
/// `via_uuid` — three live members each signing their own CURRENT id.
#[test]
fn the_bottom_row_fixture_still_confers_an_honest_quorum() {
    let (subject_id, ts) = subject();
    let mut r = MapResolver::new();
    let mut c = CachedIndex::default();

    let (kp0, kp1) = (KeyPair::generate(), KeyPair::generate());
    let (_, d0) = admit_evicting(&mut r, &mut c, &kp0);
    let (_, d1) = admit_evicting(&mut r, &mut c, &kp1);
    let kp_a = KeyPair::generate();
    let (m, _) = admit_evicting(&mut r, &mut c, &kp_a);
    let kp_c = KeyPair::generate();
    let d_c = rekey_evicting(&mut r, &mut c, m, &kp_c);

    let declared = vec![d0.clone(), d1.clone(), d_c.clone()];
    let honest = CitizenshipRecord {
        certificate: cert(&declared, ts),
        attestations: sign_all(&subject_id, ts, &[(&d0, &kp0), (&d1, &kp1), (&d_c, &kp_c)]),
    };
    assert!(honest.verify_quorum(&subject_id, live_roster(&r)), "O(n) confers");
    assert!(
        honest.verify_quorum(&subject_id, via_uuid(&c, &r)),
        "(a)+(b) confers an honest quorum — the refusals above are the attacks, not the fixture"
    );
    assert!(honest.verify_quorum(&subject_id, via_lct(&c)), "`->Lct` confers");
}

// ===========================================================================
// The bijection sentence, taken literally: (a) preserves surjectivity across
// overwrite, but it does not enforce INJECTIVITY, and nothing else does either.
// ===========================================================================

/// HUB's spec sentence is "the derived index must be a bijection onto the live
/// member set", with (a) preserving it across overwrite and (b) making a
/// surjectivity violation fail-closed. Injectivity is the direction neither
/// clause addresses: `derive_lct_id` is a function of the PUBLIC KEY alone, so
/// two members admitted under the same key share one derived label, and the
/// index is a HashMap keyed on that label — last writer wins.
///
/// Measured consequence, so the spec can say which direction it is:
/// the collision is NOT vote-bearing. The loser of the collision is denied their
/// own vote; the winner gets exactly one. An availability failure, not a
/// citizenship one — which is the opposite polarity from A/B/C and worth one
/// sentence at the spec so "bijection" is not read as one undifferentiated
/// requirement.
#[test]
fn injectivity_is_unenforced_but_the_collision_denies_rather_than_confers() {
    let (subject_id, ts) = subject();
    let mut r = MapResolver::new();
    let mut c = CachedIndex::default();

    let shared = KeyPair::generate();
    let (m_first, d_first) = admit_evicting(&mut r, &mut c, &shared);
    let (m_second, d_second) = admit_evicting(&mut r, &mut c, &shared);
    assert_ne!(m_first, m_second, "two distinct members");
    assert_eq!(d_first, d_second, "…sharing ONE derived label: injectivity fails");

    assert_eq!(r.0.len(), 2, "the live roster holds two members");
    assert_eq!(
        c.to_uuid.len(),
        1,
        "…and the index holds ONE entry for them: not surjective either, in the \
         direction (a) does not watch — clause (a) saw no prior entry for the \
         SECOND uuid, so it evicted nothing"
    );

    // Two members, one label, one vote. Add a third real member and the pair
    // still cannot reach quorum: the collision costs a vote instead of adding one.
    let kp3 = KeyPair::generate();
    let (_, d3) = admit_evicting(&mut r, &mut c, &kp3);
    let declared = vec![d_first.clone(), d_second.clone(), d3.clone()];
    assert_eq!(declared.len(), BIRTH_WITNESS_QUORUM, "three DECLARED witnesses");
    let record = CitizenshipRecord {
        certificate: cert(&declared, ts),
        attestations: sign_all(
            &subject_id,
            ts,
            &[(&d_first, &shared), (&d_second, &shared), (&d3, &kp3)],
        ),
    };
    assert!(
        !record.verify_quorum(&subject_id, via_uuid(&c, &r)),
        "REFUSED: `verify_quorum` dedups on the LABEL (BTreeSet<String>), and the \
         colliding members share one — three declared witnesses count as two"
    );
    assert!(
        !record.verify_quorum(&subject_id, live_roster(&r)),
        "the O(n) roster refuses it too, and for the same reason — so this is a \
         property of `derive_lct_id` + the label dedup, NOT of the cache"
    );
}
