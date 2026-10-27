// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! LCT identity convergence Slice D-c (hub/docs/PRD_LCT_IDENTITY_CONVERGENCE.md, FR6 + D7): the MRH projection.
//!
//! A READ-ONLY view of one canonical's relationships, computed from the projection at request time. Nothing
//! is written and there is no second store: the ledger stays authoritative. Every edge says where it came
//! from (`source`):
//!
//! - `ledger`: a witnessed hub fact; `index` cites the ledger entry that witnessed it, so a reader can check.
//! - `self_declared`: an edge in the canonical's OWN published document (`mrh.bound` / `paired` /
//!   `witnessing`), cited by `registry_version`. Signed only by that document's binding key, never by the
//!   other end, and backed by no ledger event. Measured for D-c: a document's `witnessing` entries are plain
//!   `MrhEdge`s of this kind, so they are `self_declared`, not witnessed (CBP's §4 on #930).
//!
//! Slice E-c: attested (lost-key) lineage is `attested_successor` / `attested_predecessor` /
//! `attested_successor_conflict`, never `successor` / `predecessor`: a Sovereign claim is not a key fact.
//!
//! Role occupancy is `occupant` / `previous_occupant`, never `rotated_from`: a seat changing hands is not a
//! key rotation (`successor` / `predecessor`, D-b1).
//!
//! Exposure (D7): an anonymous reader gets `self_declared` only, which the registry already serves. An
//! authenticated member also gets the ledger edges, except pairings and introductions, which only their
//! parties and the Sovereign see (pairing topology is the social graph, and sealed material rides it).

use serde::Serialize;
use uuid::Uuid;

use crate::ids::CanonicalLctId;
use crate::state::HubState;

/// Who is reading. The route decides this from how the request was authenticated.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Reader {
    Anonymous,
    Member(Uuid),
    Sovereign,
}

/// One edge. `category` is the MRH bucket (`bound` | `paired` | `witnessing`), `edge_type` the relation, and
/// `target` the other end (a canonical `lct:web4:…`, a hub member UUID, a role UUID, or the hub id).
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct MrhEdge {
    pub category: &'static str,
    pub edge_type: String,
    pub target: String,
    /// `ledger` | `self_declared`.
    pub source: &'static str,
    /// For `ledger` edges: the entry that witnessed the fact.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub index: Option<u64>,
    /// For `self_declared` edges: the registry version of the document that carries it.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub registry_version: Option<u32>,
    /// A status the fact carries (a pairing's or introduction's state), when it has one.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub status: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct MrhProjection {
    pub canonical: CanonicalLctId,
    /// The hub member whose pinned key derives this canonical, when exactly one does. Ledger facts keyed by
    /// member (citizenship, roles, pairings, introductions) are reported through it.
    pub member: Option<Uuid>,
    pub edges: Vec<MrhEdge>,
    /// Why something is absent (e.g. an ambiguous owner, or an anonymous reader), never silently.
    pub notes: Vec<String>,
}

fn ledger(category: &'static str, edge_type: &str, target: String, index: u64) -> MrhEdge {
    MrhEdge { category, edge_type: edge_type.into(), target, source: "ledger", index: Some(index),
        registry_version: None, status: None }
}

/// The projection for `canonical`, as `reader` may see it. `None` when the canonical is not published here
/// (there is nothing to anchor a view on).
pub fn project(state: &HubState, hub_id: Uuid, canonical: &CanonicalLctId,
    sovereign_key: Option<&web4_core::crypto::PublicKey>, reader: Reader) -> Option<MrhProjection> {
    use crate::lct_resolve::{resolve, Reference, Resolution};
    let entry = state.registry.get(canonical)?;
    let mut edges = Vec::new();
    let mut notes = Vec::new();

    // self_declared: the document's own MRH, verbatim, for every reader.
    let mrh = &entry.document.mrh;
    for (category, list) in [("bound", &mrh.bound), ("paired", &mrh.paired), ("witnessing", &mrh.witnessing)] {
        for e in list {
            edges.push(MrhEdge { category, edge_type: e.edge_type.clone(), target: e.lct_id.clone(),
                source: "self_declared", index: None, registry_version: Some(entry.version), status: None });
        }
    }
    if reader == Reader::Anonymous {
        notes.push("unauthenticated read: self_declared edges only; witnessed edges need an authenticated \
            member (D7)".into());
        return Some(MrhProjection { canonical: canonical.clone(), member: None, edges, notes });
    }

    // Rotation lineage (D-b1): verified both ways, keyed by canonical.
    let lineage = crate::lct_rotation::lineage(state, canonical);
    if let Some(s) = &lineage.successor {
        edges.push(ledger("bound", "successor", s.canonical.to_string(), s.index));
    }
    for s in &lineage.successor_conflict {
        edges.push(ledger("bound", "successor_conflict", s.canonical.to_string(), s.index));
    }
    for p in &lineage.predecessors {
        edges.push(ledger("bound", "predecessor", p.canonical.to_string(), p.index));
    }
    // Slice E-c: attested (lost-key) lineage, LABELLED: `attested_*` edge types, never `successor` /
    // `predecessor`, so a Sovereign claim never reads as a verified rotation. `status` carries the channel the
    // attestation arrived through.
    let attested = |edge_type: &str, r: &crate::lct_attest::AttestedRef| {
        let mut e = ledger("bound", edge_type, r.canonical.to_string(), r.index);
        e.status = Some(format!("attested_via:{}", r.attested_by));
        e
    };
    if let Some(r) = &lineage.attested_successor {
        edges.push(attested("attested_successor", r));
    }
    for r in &lineage.attested_successor_conflict {
        edges.push(attested("attested_successor_conflict", r));
    }
    for r in &lineage.attested_predecessors {
        edges.push(attested("attested_predecessor", r));
    }
    if lineage.successor_kind_conflict {
        notes.push("successor_kind_conflict: this canonical has a live verified successor AND a live attested \
            one; neither is THE successor (law weighs both, FR5)".into());
    }

    // Member-of (H2): this canonical's parent, and the members that report this canonical as theirs.
    if let (Some(parent), Some(at)) = (state.member_of.get(canonical), state.member_of_at.get(canonical)) {
        edges.push(ledger("bound", "member_of", parent.to_string(), *at));
    }
    for (child, parent) in &state.member_of {
        if parent == canonical {
            if let Some(at) = state.member_of_at.get(child) {
                edges.push(ledger("bound", "has_member", child.to_string(), *at));
            }
        }
    }

    // The member behind this canonical, for the facts the ledger keys by member.
    let member = match resolve(state, &Reference::Canonical(canonical.clone()), sovereign_key) {
        Resolution::Resolved { member, .. } => Some(member.as_uuid()),
        Resolution::Ambiguous { members, .. } => {
            notes.push(format!("{} members' pinned keys derive this canonical; member-keyed facts \
                (citizenship, roles, pairings, introductions) are not attributed to any of them", members.len()));
            None
        }
        _ => None,
    };
    if let Some(m) = member {
        if let Some(at) = state.member_since.get(&m) {
            edges.push(ledger("bound", "citizen_of", hub_id.to_string(), *at));
        }
        // Role occupancy from each role's own log: the latest fill by this member is `occupant` if it still
        // holds the seat, every earlier one (and a vacated one) is `previous_occupant`.
        for (role_id, role) in &state.roles {
            let fills: Vec<u64> = role.occupancy_log.iter()
                .filter(|c| c.occupant == Some(m)).map(|c| c.entry_index).collect();
            let holds = role.occupant == Some(m);
            for (i, at) in fills.iter().enumerate() {
                let current = holds && i + 1 == fills.len();
                edges.push(ledger("paired", if current { "occupant" } else { "previous_occupant" },
                    role_id.to_string(), *at));
            }
        }
        // Pairings and introductions: only their parties and the Sovereign.
        let party = |a: Uuid, b: Uuid| reader == Reader::Sovereign || reader == Reader::Member(a)
            || reader == Reader::Member(b);
        let mut hidden = 0usize;
        for (id, p) in &state.pairs {
            if p.initiator != m && p.counterparty != m { continue; }
            if !party(p.initiator, p.counterparty) { hidden += 1; continue; }
            let other = if p.initiator == m { p.counterparty } else { p.initiator };
            if let Some(at) = state.pair_since.get(id) {
                let mut e = ledger("paired", "paired_with", other.to_string(), *at);
                e.status = Some(format!("{:?}", p.status).to_lowercase());
                edges.push(e);
            }
        }
        for (id, it) in &state.intros {
            if it.from_lct != m && it.to_lct != m { continue; }
            if !party(it.from_lct, it.to_lct) { hidden += 1; continue; }
            let (edge_type, other) = if it.from_lct == m { ("introduction_to", it.to_lct) }
                else { ("introduction_from", it.from_lct) };
            if let Some(at) = state.intro_since.get(id) {
                let mut e = ledger("paired", edge_type, other.to_string(), *at);
                e.status = Some(format!("{:?}", it.status).to_lowercase());
                edges.push(e);
            }
        }
        if hidden > 0 {
            notes.push("pairings and introductions are visible to their parties and the Sovereign only".into());
        }
    }

    // Witnessing: the hub witnessed this presence's acts. The latest one is cited (as carrier or speaker).
    let as_lct = state.last_act_by_lct.get(canonical.as_str()).copied();
    let as_member = member.and_then(|m| state.last_act_by_member.get(&m).copied());
    if let Some((index, _)) = [as_lct, as_member].into_iter().flatten().max_by_key(|(i, _)| *i) {
        edges.push(ledger("witnessing", "latest_witnessed_act", hub_id.to_string(), index));
    }
    Some(MrhProjection { canonical: canonical.clone(), member, edges, notes })
}
