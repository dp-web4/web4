// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later
//
// HUB's measurements taken while ruling on Legion's M-CIT-3a spec delta
// (forum/legion-m-cit-3-witness-producer-spec-delta-2026-08-21.md).
// Characterization only: every assertion states TODAY's behaviour, including
// the parts that are wrong, and names which way it should move.

use std::collections::BTreeMap;
use web4_core::attestation::{
    Attestation, AttestationType, BirthCertificate, CitizenshipRecord, BIRTH_WITNESS_QUORUM,
};
use web4_core::crypto::{KeyPair, PublicKey};
use web4_core::lct::{EntityType, Lct};

/// A resolver over an explicit id -> key map. Unknown ids resolve to None,
/// which is exactly the hub-side "witness not on the roster" case.
fn resolver(map: BTreeMap<String, PublicKey>) -> impl Fn(&str) -> Option<PublicKey> {
    move |id: &str| map.get(id).cloned()
}

fn subject() -> (String, chrono::DateTime<chrono::Utc>) {
    let (lct, _sk) = Lct::new(EntityType::AiSoftware, None);
    (lct.lct_id(), lct.created_at)
}

fn cert(witnesses: Vec<&str>, ts: chrono::DateTime<chrono::Utc>) -> BirthCertificate {
    BirthCertificate {
        issuing_society: "lct:web4:society:hestia".into(),
        citizen_role: "lct:web4:role:citizen".into(),
        birth_witnesses: witnesses.into_iter().map(String::from).collect(),
        birth_timestamp: ts,
        birth_context: None,
        genesis_block_hash: None,
    }
}

/// C1 (Legion, confirmed): clause 4 dedups on the witness STRING, so three ids
/// backed by one signing key are a quorum. Should move to: distinct KEYS.
#[test]
fn c1_three_ids_over_one_key_is_a_quorum_today() {
    let (sid, ts) = subject();
    let one_key = KeyPair::generate();
    let ids = ["lct:web4:member:a", "lct:web4:member:b", "lct:web4:member:c"];

    let record = CitizenshipRecord {
        certificate: cert(ids.to_vec(), ts),
        attestations: ids
            .iter()
            .map(|w| Attestation::sign(&sid, *w, AttestationType::Existence, ts, &one_key))
            .collect(),
    };
    let map: BTreeMap<_, _> =
        ids.iter().map(|w| (w.to_string(), one_key.verifying_key())).collect();

    let distinct_keys: std::collections::BTreeSet<String> =
        map.values().map(|k| k.to_hex()).collect();
    assert_eq!(distinct_keys.len(), 1, "one signer behind three ids");
    assert!(
        record.verify_quorum(&sid, resolver(map)),
        "TODAY: passes. SHOULD: fail once clause 4 counts distinct keys (R2)"
    );
}

/// C2 (Legion, confirmed): clause 5 is evaluated against a LIVE resolver, so a
/// conferred record is voided when a declared witness rotates its key — even
/// with the quorum floor still met by the others. Redundancy inverts into
/// fragility: the 4-witness record fails where a 3-witness one would pass.
#[test]
fn c2_a_key_rotation_voids_an_already_conferred_record() {
    let (sid, ts) = subject();
    let kps: Vec<KeyPair> = (0..4).map(|_| KeyPair::generate()).collect();
    let ids: Vec<String> = (0..4).map(|i| format!("lct:web4:member:w{i}")).collect();

    let record = CitizenshipRecord {
        certificate: cert(ids.iter().map(String::as_str).collect(), ts),
        attestations: ids
            .iter()
            .zip(&kps)
            .map(|(w, kp)| Attestation::sign(&sid, w, AttestationType::Existence, ts, kp))
            .collect(),
    };

    let all: BTreeMap<String, PublicKey> =
        ids.iter().cloned().zip(kps.iter().map(|k| k.verifying_key())).collect();
    assert!(record.verify_quorum(&sid, resolver(all.clone())), "conferred and verifiable");

    // w3 rotates its witnessing key: authorize_operational_key keeps one key per
    // purpose, so the key that signed is gone. Model that as a new key.
    let mut rotated = all.clone();
    rotated.insert(ids[3].clone(), KeyPair::generate().verifying_key());

    let still_valid = record
        .attestations
        .iter()
        .filter(|a| rotated.get(&a.witness).is_some_and(|pk| a.verify(&sid, pk)))
        .count();
    assert_eq!(still_valid, 3, "the floor is still met");
    assert!(still_valid >= BIRTH_WITNESS_QUORUM);
    assert!(
        !record.verify_quorum(&sid, resolver(rotated)),
        "TODAY: false anyway, because ALL declared must remain live (R3)"
    );
}

/// C6 (HUB, new): verify_quorum never checks how many witnesses the certificate
/// DECLARES, and lets the >=3 floor be met by attestations from signers that are
/// not declared at all. A certificate declaring ONE witness verifies.
#[test]
fn c6_the_floor_is_met_by_undeclared_signers_and_declared_count_is_unchecked() {
    let (sid, ts) = subject();
    let declared = "lct:web4:member:only-one";
    let extras = ["lct:web4:member:tagalong-1", "lct:web4:member:tagalong-2"];

    let kp_declared = KeyPair::generate();
    let kp_extras: Vec<KeyPair> = (0..2).map(|_| KeyPair::generate()).collect();

    let certificate = cert(vec![declared], ts);
    assert!(
        !certificate.quorum_structurally_ok(),
        "the STRUCTURAL check refuses a one-witness certificate"
    );

    let mut attestations =
        vec![Attestation::sign(&sid, declared, AttestationType::Existence, ts, &kp_declared)];
    attestations.extend(
        extras
            .iter()
            .zip(&kp_extras)
            .map(|(w, kp)| Attestation::sign(&sid, *w, AttestationType::Existence, ts, kp)),
    );
    let record = CitizenshipRecord { certificate, attestations };

    let mut map = BTreeMap::new();
    map.insert(declared.to_string(), kp_declared.verifying_key());
    for (w, kp) in extras.iter().zip(&kp_extras) {
        map.insert(w.to_string(), kp.verifying_key());
    }

    assert!(
        record.verify_quorum(&sid, resolver(map)),
        "TODAY: the COSE-verified check passes what the structural check refuses. \
         SHOULD: the >=3 must come from the DECLARED witnesses (R7)"
    );
}

/// C7 (HUB, new): what R3-as-written would cost. If clause 5 relaxes to
/// "every declared witness has a PRESENT attestation" plus a separate ">=3
/// currently verifiable" floor drawn from all attestations, a record can name
/// three witnesses whose signatures DO NOT verify and still pass on three
/// attacker-controlled signers. Measured here by evaluating both halves.
#[test]
fn c7_static_presence_plus_a_free_floor_launders_named_witnesses() {
    let (sid, ts) = subject();
    let named = ["lct:web4:member:thor", "lct:web4:member:cbp", "lct:web4:member:legion"];
    let attacker = ["lct:web4:member:x1", "lct:web4:member:x2", "lct:web4:member:x3"];
    let attacker_kps: Vec<KeyPair> = (0..3).map(|_| KeyPair::generate()).collect();
    let real_kps: Vec<KeyPair> = (0..3).map(|_| KeyPair::generate()).collect();

    // The named witnesses' attestations are present and structurally well formed,
    // but signed by keys that are NOT the ones the resolver returns for them.
    let mut attestations: Vec<Attestation> = named
        .iter()
        .map(|w| {
            Attestation::sign(&sid, *w, AttestationType::Existence, ts, &KeyPair::generate())
        })
        .collect();
    attestations.extend(
        attacker
            .iter()
            .zip(&attacker_kps)
            .map(|(w, kp)| Attestation::sign(&sid, *w, AttestationType::Existence, ts, kp)),
    );
    let record = CitizenshipRecord { certificate: cert(named.to_vec(), ts), attestations };

    let mut map = BTreeMap::new();
    for (w, kp) in named.iter().zip(&real_kps) {
        map.insert(w.to_string(), kp.verifying_key());
    }
    for (w, kp) in attacker.iter().zip(&attacker_kps) {
        map.insert(w.to_string(), kp.verifying_key());
    }
    let resolve = resolver(map);

    // half 1 — static presence: every declared witness has an attestation present
    let static_ok = record
        .certificate
        .birth_witnesses
        .iter()
        .all(|w| record.attestations.iter().any(|a| &a.witness == w
            && a.attestation_type == AttestationType::Existence));
    assert!(static_ok, "R3's static half is satisfied by PRESENCE alone");

    // half 2 — a live floor drawn from ALL attestations
    let live: std::collections::BTreeSet<String> = record
        .attestations
        .iter()
        .filter(|a| a.attestation_type == AttestationType::Existence)
        .filter(|a| resolve(&a.witness).is_some_and(|pk| a.verify(&sid, &pk)))
        .map(|a| a.witness.clone())
        .collect();
    assert_eq!(live.len(), 3, "the floor is met — entirely by the attacker's own signers");
    assert!(live.iter().all(|w| attacker.contains(&w.as_str())));

    // so R3-as-written would ACCEPT this record...
    assert!(static_ok && live.len() >= BIRTH_WITNESS_QUORUM, "R3-as-written: accepts");
    // ...where today's clause 5 refuses it.
    assert!(!record.verify_quorum(&sid, &resolve), "TODAY: refuses. Do not lose this.");

    // the fix: draw the live floor from the DECLARED witnesses only.
    let live_declared = record
        .certificate
        .birth_witnesses
        .iter()
        .filter(|w| live.contains(*w))
        .count();
    assert_eq!(live_declared, 0, "R3+R7: refuses, and for the right reason");
}

/// C3 (Legion, confirmed): the signed bytes carry whatever precision the
/// producer hands in, so a millisecond-normalising hop voids the signature —
/// unless the producer truncated to whole seconds first, where truncation is a
/// no-op. R4 is a producer-side change; the v1 rendering is untouched.
#[test]
fn c3_second_precision_is_the_only_hop_stable_rendering() {
    use chrono::{DurationRound, TimeDelta};
    let (sid, _) = subject();
    let kp = KeyPair::generate();
    let nanos = chrono::DateTime::parse_from_rfc3339("2026-08-22T02:59:05.954554682Z")
        .unwrap()
        .with_timezone(&chrono::Utc);

    let signed_at_nanos = Attestation::sign(&sid, "w", AttestationType::Existence, nanos, &kp);
    let normalised_ms = nanos.duration_trunc(TimeDelta::milliseconds(1)).unwrap();
    let mut hopped = signed_at_nanos.clone();
    hopped.ts = normalised_ms;
    assert!(!hopped.verify(&sid, &kp.verifying_key()), "a ms-normalising hop voids it");

    let secs = nanos.duration_trunc(TimeDelta::seconds(1)).unwrap();
    let signed_at_secs = Attestation::sign(&sid, "w", AttestationType::Existence, secs, &kp);
    let mut hopped_secs = signed_at_secs.clone();
    hopped_secs.ts = secs.duration_trunc(TimeDelta::milliseconds(1)).unwrap();
    assert!(
        hopped_secs.verify(&sid, &kp.verifying_key()),
        "truncating an already-whole-second ts is a no-op — R4 survives the hop"
    );
}

/// C4 (Legion, confirmed): the two spellings. web4-core's own doc comment and
/// tests say "witness"; hestia vouches and resolves "witnessing".
#[test]
fn c4_the_purpose_string_has_two_spellings() {
    let (mut member, binding) = Lct::new(EntityType::AiSoftware, None);

    let op = KeyPair::generate();
    member.authorize_operational_key("witnessing", op.verifying_key(), &binding);

    assert_eq!(member.operational_key_for("witnessing"), Some(op.verifying_key()));
    assert_eq!(
        member.operational_key_for("witness"),
        None,
        "a resolver written from web4-core's own example resolves None (R5)"
    );
}
