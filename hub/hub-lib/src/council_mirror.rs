//! Sprint 3 of `PRD_ROLE_ENTITIES_AND_SUBROLES`: the Sovereign Council mirrored onto roles,
//! **dual-read, nothing switched**.
//!
//! Three things live here, all pure functions of a projected [`HubState`]:
//!
//! 1. [`legacy_council`] — the council exactly as the governance gate reads it today. The
//!    daemon's `project_council` delegates to this, so the differential compares against
//!    the real authority rather than against a reimplementation of it.
//! 2. [`role_council`] — the same body read from the role tree: occupants of the council's
//!    unretired Office seats, and the `M` the council's law declared.
//! 3. [`council_differential`] — where the two disagree, with each disagreement NAMED.
//!
//! Plus the two write-side helpers the operator surfaces use: [`build_mirror`] derives the
//! one-shot `CouncilMirrored` act from the legacy projection, and [`counterparts`] computes
//! the role-side acts a later legacy council change needs so the two stay in step.
//!
//! **Why the differential names its divergences instead of returning a bool.** Sprint 4
//! switches signer resolution onto the role tree, and the switch changes one behaviour on
//! purpose: the legacy projection lowers `M` whenever a removal takes `N` below it and never
//! raises it back, while the role tree keeps `M` as law and reports the body unable to reach
//! a verdict instead. A differential that only said "disagree" would block the cutover on
//! the very defect the cutover exists to remove. One that only said "agree" after
//! normalising the clamp away would hide it. So the clamp is its own divergence class, and
//! the cutover rule can be stated precisely: holder sets must match exactly, and the only
//! permitted threshold divergence is [`CouncilDivergence::LegacyClampedThreshold`].

use std::collections::BTreeSet;

use serde::Serialize;
use uuid::Uuid;

use crate::events::{HubEvent, MirroredSeat, RoleKind};
use crate::state::{HubState, SeatQuorum, COUNCIL_SEAT_NAME};

/// The council as the legacy projection — and therefore the live governance gate — reads it.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct LegacyCouncilView {
    /// `council_holders` plus the founding Sovereign, who is always a holder.
    pub holders: BTreeSet<Uuid>,
    /// The effective M the gate enforces. After a removal this may be LOWER than what the
    /// council's law asked for — see `requested_m`.
    pub m: u32,
    /// Legacy N: recomputed from the live holder count.
    pub n: u32,
    /// What the last threshold change asked for, before clamping. `None` = never set.
    pub requested_m: Option<u32>,
}

/// The same body read from the role tree.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct RoleCouncilView {
    pub council_role_lct_id: Uuid,
    /// Occupants of unretired Office seats — the only entities Sprint 4 lets sign.
    pub holders: BTreeSet<Uuid>,
    /// N established, O occupied, M required — kept apart.
    pub quorum: SeatQuorum,
}

/// One named way the two readings of the council disagree.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "divergence", rename_all = "snake_case")]
pub enum CouncilDivergence {
    /// No role tree exists yet, so there is nothing to compare. Not an error: every hub
    /// starts here.
    NotMirrored,
    /// Different entities may sign. **Always blocks cutover** — this is the property the
    /// switch must preserve.
    HolderSets {
        only_in_legacy: BTreeSet<Uuid>,
        only_in_roles: BTreeSet<Uuid>,
    },
    /// The legacy projection clamped M below what the law asked for, and the role tree kept
    /// the law's value. **The one divergence that is expected**: it is the defect Sprint 4
    /// removes, and it is reported so the cutover changes that behaviour knowingly.
    LegacyClampedThreshold {
        requested: u32,
        legacy_effective: u32,
        role_required: u32,
    },
    /// M differs for a reason that is NOT the clamp. Blocks cutover.
    RequiredSignatures {
        legacy_effective: u32,
        role_required: u32,
    },
}

/// The differential between the legacy council and the role-derived one.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct CouncilDifferential {
    pub legacy: LegacyCouncilView,
    pub roles: Option<RoleCouncilView>,
    pub divergences: Vec<CouncilDivergence>,
}

impl CouncilDifferential {
    /// Both readings are identical in every compared respect.
    pub fn agrees(&self) -> bool {
        self.divergences.is_empty()
    }

    /// The cutover rule: a role tree exists, holder sets match exactly, and any threshold
    /// divergence is the named legacy clamp and nothing else.
    pub fn cutover_permitted(&self) -> bool {
        self.roles.is_some()
            && self.divergences.iter().all(|d| {
                matches!(d, CouncilDivergence::LegacyClampedThreshold { .. })
            })
    }
}

/// The council exactly as the governance gate reads it. `sovereign` is the hub's founding
/// Sovereign, who is a holder whether or not any event says so.
pub fn legacy_council(state: &HubState, sovereign: Uuid) -> LegacyCouncilView {
    let mut holders = state.council_holders.clone();
    holders.insert(sovereign);
    // Default when no threshold was ever set: 1-of-N, single-signer behaviour. This line is
    // the daemon's historical default, moved here so there is one copy of it.
    let (m, n) = state.council_threshold.unwrap_or((1, holders.len() as u32));
    LegacyCouncilView { holders, m, n, requested_m: state.council_threshold_requested }
}

/// The council read from the role tree, or `None` if it has not been mirrored.
pub fn role_council(state: &HubState) -> Option<RoleCouncilView> {
    let council = state.mirrored_council?;
    let required = state.roles.get(&council).and_then(|r| r.quorum_m).unwrap_or(1);
    Some(RoleCouncilView {
        council_role_lct_id: council,
        holders: state.seat_occupants(council),
        quorum: state.seat_quorum(council, required),
    })
}

/// The quorum the governance gate enforces RIGHT NOW, as N established / O occupied / M
/// required — the one reading every public page renders, so no two of them can disagree
/// about whether this council can reach a verdict.
///
/// Sprint 3: the legacy council is the authority, and it has no notion of an empty seat, so
/// O always equals N and the body is always reachable — the clamp guarantees it. That is an
/// honest reading of the legacy gate, not a claim that vacancies cannot happen. Sprint 4
/// switches this one function to [`role_council`], and "quorum currently unreachable" starts
/// being able to appear exactly when it becomes true.
pub fn authoritative_quorum(state: &HubState, sovereign: Uuid) -> SeatQuorum {
    let legacy = legacy_council(state, sovereign);
    let seats = legacy.holders.len();
    SeatQuorum { established: seats, occupied: seats, required: legacy.m }
}

/// Compare the two readings and name every disagreement.
pub fn council_differential(state: &HubState, sovereign: Uuid) -> CouncilDifferential {
    let legacy = legacy_council(state, sovereign);
    let Some(roles) = role_council(state) else {
        return CouncilDifferential {
            legacy,
            roles: None,
            divergences: vec![CouncilDivergence::NotMirrored],
        };
    };
    let mut divergences = Vec::new();

    if legacy.holders != roles.holders {
        divergences.push(CouncilDivergence::HolderSets {
            only_in_legacy: legacy.holders.difference(&roles.holders).copied().collect(),
            only_in_roles: roles.holders.difference(&legacy.holders).copied().collect(),
        });
    }

    let role_required = roles.quorum.required;
    if legacy.m != role_required {
        let clamp = legacy.requested_m == Some(role_required) && legacy.m < role_required;
        divergences.push(if clamp {
            CouncilDivergence::LegacyClampedThreshold {
                requested: role_required,
                legacy_effective: legacy.m,
                role_required,
            }
        } else {
            CouncilDivergence::RequiredSignatures { legacy_effective: legacy.m, role_required }
        });
    }

    CouncilDifferential { legacy, roles: Some(roles), divergences }
}

/// Why a mirror act was not built.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum MirrorRefusal {
    /// The council is already a role tree. Mirroring twice would fork it.
    AlreadyMirrored { council_role_lct_id: Uuid },
}

impl std::fmt::Display for MirrorRefusal {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::AlreadyMirrored { council_role_lct_id } => write!(
                f,
                "the council is already mirrored onto roles as {council_role_lct_id}; \
                 mirroring twice would fork it"
            ),
        }
    }
}

/// Derive the one-shot `CouncilMirrored` act from the legacy projection.
///
/// One seat per current legacy holder, the founding Sovereign included, each filled by that
/// holder. `required_m` is the threshold the law ASKED for when one was ever set, and the
/// legacy default of 1 otherwise — deliberately not the clamped effective value.
pub fn build_mirror(
    state: &HubState,
    sovereign: Uuid,
    mirrored_by: Uuid,
) -> Result<HubEvent, MirrorRefusal> {
    if let Some(council_role_lct_id) = state.mirrored_council {
        return Err(MirrorRefusal::AlreadyMirrored { council_role_lct_id });
    }
    let legacy = legacy_council(state, sovereign);
    let seats = legacy
        .holders
        .iter()
        .map(|holder| MirroredSeat { seat_role_lct_id: Uuid::new_v4(), occupant: *holder })
        .collect();
    Ok(HubEvent::CouncilMirrored {
        council_role_lct_id: Uuid::new_v4(),
        seats,
        required_m: crate::state::normalize_required_m(legacy.requested_m.unwrap_or(legacy.m)),
        legacy_basis_index: state.last_index,
        mirrored_by,
    })
}

/// The role-side acts a legacy council change needs once the council is mirrored, so the
/// two readings stay in step through Sprint 3's dual-read window. Empty before mirroring and
/// for any event that is not a legacy council change.
///
/// Every emitter of a legacy council event must append these after it, and must put them
/// through the same governance gate first — they are acts, not bookkeeping. An emitter that
/// forgets is exactly what the differential exists to catch.
///
/// - **Holder added** — refill the lowest-id vacant seat if one exists; otherwise constitute
///   a new seat and fill it. A seat that was emptied by a resignation is an Office awaiting
///   its next occupant, so it is filled before N grows.
/// - **Holder removed** — vacate their seat. Not retire: the seat still exists, N is
///   unchanged, O drops. This is where the two readings intentionally part ways on N.
/// - **Threshold changed** — set the council's M to the value ASKED for, unclamped.
pub fn counterparts(state: &HubState, legacy_event: &HubEvent) -> Vec<HubEvent> {
    let Some(council) = state.mirrored_council else { return Vec::new() };
    let seat_role = || web4_core::role::SocietyRole::Custom(COUNCIL_SEAT_NAME.into());
    let seats = || {
        state.roles.values().filter(move |r| {
            r.parent_role_lct_id == Some(council) && !r.retired && r.role_kind == RoleKind::Office
        })
    };

    match legacy_event {
        HubEvent::CouncilMemberAdded { member_lct_id, added_by, .. } => {
            if seats().any(|r| r.occupant == Some(*member_lct_id)) {
                return Vec::new();
            }
            if let Some(vacant) = seats().find(|r| r.occupant.is_none()) {
                return vec![HubEvent::RoleAssigned {
                    role: seat_role(),
                    role_lct_id: vacant.role_lct_id,
                    assigned_to: *member_lct_id,
                    assigned_by: *added_by,
                }];
            }
            let seat = Uuid::new_v4();
            vec![
                HubEvent::RoleCreated {
                    role_lct_id: seat,
                    role: seat_role(),
                    role_kind: RoleKind::Office,
                    charter: None,
                    parent_role_lct_id: Some(council),
                    initial_occupant: None,
                    created_by: *added_by,
                },
                HubEvent::RoleAssigned {
                    role: seat_role(),
                    role_lct_id: seat,
                    assigned_to: *member_lct_id,
                    assigned_by: *added_by,
                },
            ]
        }
        HubEvent::CouncilMemberRemoved { member_lct_id, removed_by, removal_kind, reason } => seats()
            .filter(|r| r.occupant == Some(*member_lct_id))
            .map(|r| HubEvent::RoleVacated {
                role_lct_id: r.role_lct_id,
                previous_occupant: *member_lct_id,
                vacation_kind: removal_kind.clone(),
                reason: reason.clone(),
                vacated_by: *removed_by,
            })
            .collect(),
        HubEvent::CouncilThresholdChanged { new_m, initiated_by } => vec![HubEvent::RoleQuorumSet {
            role_lct_id: council,
            required_m: crate::state::normalize_required_m(*new_m),
            set_by: *initiated_by,
        }],
        _ => Vec::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hub::HubPaths;
    use crate::identity::IdentityFile;
    use crate::ledger::HubLedger;
    use crate::store::FileBackend;
    use chrono::Utc;
    use web4_core::crypto::KeyPair;
    use web4_core::lct::EntityType;
    use web4_core::role::RoleEventKind;

    /// A real, file-backed chain rather than hand-applied state, so every assertion below is
    /// also an assertion that the new verbs survive serialisation and replay from zero.
    struct Chain {
        _tmp: tempfile::TempDir,
        ledger: HubLedger,
        kp: KeyPair,
        sov: Uuid,
    }

    impl Chain {
        async fn new() -> Self {
            let tmp = tempfile::tempdir().unwrap();
            let chap = tmp.path().join("chap");
            std::fs::create_dir_all(&chap).unwrap();
            let store: Box<dyn crate::store::HubStore> =
                Box::new(FileBackend::new(HubPaths::new(chap)));
            let mut ledger = HubLedger::open(store).await.unwrap();
            let id = IdentityFile::generate(EntityType::Human);
            let kp = id.keypair().unwrap();
            ledger.write_genesis(id.lct.id, &kp, "Fleet".into(), "sha256:0".into()).await.unwrap();
            Chain { _tmp: tmp, ledger, kp, sov: id.lct.id }
        }
        async fn append(&mut self, e: HubEvent) {
            self.ledger.append(self.sov, &self.kp, e).await.unwrap();
        }
        fn state(&self) -> HubState {
            HubState::project(&self.ledger)
        }
        fn diff(&self) -> CouncilDifferential {
            council_differential(&self.state(), self.sov)
        }
        /// A legacy council change the way Sprint 3's write paths must perform it: the legacy
        /// act, then its role-side counterparts computed from the state at that moment.
        async fn change(&mut self, legacy: HubEvent) {
            let parts = counterparts(&self.state(), &legacy);
            self.append(legacy).await;
            for p in parts {
                self.append(p).await;
            }
        }
        async fn mirror(&mut self) {
            let act = build_mirror(&self.state(), self.sov, self.sov).expect("not yet mirrored");
            self.append(act).await;
        }
    }

    fn add(sov: Uuid, who: Uuid) -> HubEvent {
        HubEvent::CouncilMemberAdded {
            member_lct_id: who,
            member_pubkey_hex: "00".repeat(32),
            added_by: sov,
            member_name: None,
        }
    }
    fn remove(sov: Uuid, who: Uuid) -> HubEvent {
        HubEvent::CouncilMemberRemoved {
            member_lct_id: who,
            removed_by: sov,
            removal_kind: RoleEventKind::FillerResigned,
            reason: None,
        }
    }
    fn threshold(sov: Uuid, m: u32) -> HubEvent {
        HubEvent::CouncilThresholdChanged { new_m: m, initiated_by: sov }
    }

    /// The acceptance test PRD Sprint 3 names: on a fixture shaped like the live fleet hub —
    /// the founding Sovereign plus two co-holders at 2-of-3, the enrollment still owed on
    /// the real hub — the role-derived council and the one the gate enforces are the same
    /// body.
    #[tokio::test]
    async fn a_mirrored_council_is_the_same_body_the_gate_enforces_on_a_fleet_shaped_chain() {
        let mut c = Chain::new().await;
        let (hub, nomad) = (Uuid::new_v4(), Uuid::new_v4());
        c.change(add(c.sov, hub)).await;
        c.change(add(c.sov, nomad)).await;
        c.change(threshold(c.sov, 2)).await;

        let before = c.diff();
        assert_eq!(before.divergences, vec![CouncilDivergence::NotMirrored]);
        assert!(!before.cutover_permitted(), "nothing to cut over TO before the tree exists");

        c.mirror().await;
        let d = c.diff();
        assert!(d.agrees(), "a fresh mirror must agree with the gate exactly: {:?}", d.divergences);
        let roles = d.roles.as_ref().unwrap();
        assert_eq!(roles.holders, [c.sov, hub, nomad].into_iter().collect(),
            "the founding Sovereign holds an ordinary seat like everyone else");
        assert_eq!((roles.quorum.established, roles.quorum.occupied, roles.quorum.required), (3, 3, 2));
        assert!(roles.quorum.reachable());

        // Every seat is a real sub-role of the council, reachable from a root — not a list.
        let st = c.state();
        for seat in st.roles.values().filter(|r| r.parent_role_lct_id == Some(roles.council_role_lct_id)) {
            assert_eq!(st.lineage_of(seat.role_lct_id), crate::state::Lineage::Rooted);
            assert_eq!(seat.occupancy_log.len(), 1, "the mirror's fill is on each seat's own record");
        }
    }

    /// Sprint 3 is dual-read, and the council has to keep working through it. Every later
    /// legacy change carries its counterparts, and after each one the two readings agree.
    /// Along the way the one intended difference shows up where it should: a resignation
    /// empties a seat (O drops) and does not abolish it (N stays), and a returning holder
    /// refills that seat rather than growing the council.
    #[tokio::test]
    async fn every_later_council_change_stays_in_step_through_its_counterparts() {
        let mut c = Chain::new().await;
        let (a, b, x) = (Uuid::new_v4(), Uuid::new_v4(), Uuid::new_v4());
        c.change(add(c.sov, a)).await;
        c.change(add(c.sov, b)).await;
        c.change(threshold(c.sov, 2)).await;
        c.mirror().await;

        c.change(add(c.sov, x)).await;
        let d = c.diff();
        assert!(d.agrees(), "{:?}", d.divergences);
        assert_eq!(d.roles.as_ref().unwrap().quorum.established, 4, "no vacancy to refill, so a seat was constituted");

        c.change(remove(c.sov, x)).await;
        let d = c.diff();
        assert!(d.agrees(), "{:?}", d.divergences);
        let q = d.roles.as_ref().unwrap().quorum;
        assert_eq!((q.established, q.occupied), (4, 3), "resigning moves O, never N");
        assert_eq!(d.legacy.n, 3, "…while the legacy reading recomputes N from who is present");

        c.change(add(c.sov, x)).await;
        let d = c.diff();
        assert!(d.agrees(), "{:?}", d.divergences);
        assert_eq!(d.roles.as_ref().unwrap().quorum.established, 4,
            "a returning holder REFILLS the vacant seat — the council does not grow");

        c.change(threshold(c.sov, 3)).await;
        let d = c.diff();
        assert!(d.agrees(), "{:?}", d.divergences);
        assert_eq!(d.roles.as_ref().unwrap().quorum.required, 3);
    }

    /// The defect this whole migration exists to remove, driven rather than described.
    ///
    /// Legacy: a 3-of-3 council loses a holder and M is clamped to 2 — and when the holder
    /// returns, M STAYS 2. One resignation lowered the bar permanently, with no governed act
    /// ever setting it there. Roles: M stays 3, the body reports it cannot reach a verdict
    /// while a seat is empty, and is whole again when the seat is refilled.
    ///
    /// The differential must NAME that as the clamp — not absorb it as agreement, and not
    /// block cutover on it as if it were an unexplained divergence.
    #[tokio::test]
    async fn a_resignation_that_permanently_lowers_the_legacy_bar_is_named_not_absorbed() {
        let mut c = Chain::new().await;
        let (a, b) = (Uuid::new_v4(), Uuid::new_v4());
        c.change(add(c.sov, a)).await;
        c.change(add(c.sov, b)).await;
        c.change(threshold(c.sov, 3)).await;
        c.mirror().await;
        assert!(c.diff().agrees());

        c.change(remove(c.sov, b)).await;
        let d = c.diff();
        assert_eq!(d.legacy.m, 2, "legacy clamped the bar to the holders who happen to remain");
        let q = d.roles.as_ref().unwrap().quorum;
        assert_eq!((q.established, q.occupied, q.required), (3, 2, 3));
        assert!(!q.reachable(), "the honest state: this body cannot reach a verdict right now");
        assert_eq!(d.divergences, vec![CouncilDivergence::LegacyClampedThreshold {
            requested: 3, legacy_effective: 2, role_required: 3,
        }]);
        assert!(!d.agrees(), "a clamp is a real difference, not agreement");
        assert!(d.cutover_permitted(), "…and it is the one difference cutover is FOR");

        // The holder comes back. The seat is whole again; the legacy bar is not.
        c.change(add(c.sov, b)).await;
        let d = c.diff();
        assert_eq!(d.legacy.n, 3, "legacy N recovered");
        assert_eq!(d.legacy.m, 2,
            "and legacy M did NOT — one resignation lowered this council's bar for good");
        assert!(d.roles.as_ref().unwrap().quorum.reachable(), "the role council is whole again at 3-of-3");
        assert_eq!(d.divergences, vec![CouncilDivergence::LegacyClampedThreshold {
            requested: 3, legacy_effective: 2, role_required: 3,
        }], "the clamp outlives the vacancy, so the named divergence does too");
    }

    /// Mirroring AFTER a clamp takes the law's M, not the lowered one. Taking the effective
    /// value would write the clamp into the new constitution, where no later check could see
    /// it had ever been lowered.
    #[tokio::test]
    async fn the_mirror_takes_m_from_what_the_law_asked_for_not_from_the_clamp() {
        let mut c = Chain::new().await;
        let (a, b) = (Uuid::new_v4(), Uuid::new_v4());
        c.change(add(c.sov, a)).await;
        c.change(add(c.sov, b)).await;
        c.change(threshold(c.sov, 3)).await;
        c.change(remove(c.sov, b)).await; // before mirroring: no counterparts exist yet
        assert_eq!(c.diff().legacy.m, 2);

        c.mirror().await;
        let d = c.diff();
        let q = d.roles.as_ref().unwrap().quorum;
        assert_eq!(q.required, 3, "M comes from the request the law made");
        assert_eq!((q.established, q.occupied), (2, 2), "seats exist only for current holders");
        assert!(!q.reachable());
        assert!(matches!(d.divergences.as_slice(), [CouncilDivergence::LegacyClampedThreshold { .. }]));
    }

    /// The instrument is not constant. A legacy change written WITHOUT its counterparts —
    /// the failure a forgetful emitter produces — is caught, and it blocks cutover. Without
    /// this test, every agreement above could be the differential comparing a thing with
    /// itself.
    #[tokio::test]
    async fn a_legacy_change_without_its_counterparts_is_caught_and_blocks_cutover() {
        let mut c = Chain::new().await;
        let a = Uuid::new_v4();
        c.change(add(c.sov, a)).await;
        c.mirror().await;
        assert!(c.diff().agrees());

        let stray = Uuid::new_v4();
        c.append(add(c.sov, stray)).await; // legacy only
        let d = c.diff();
        assert_eq!(d.divergences, vec![CouncilDivergence::HolderSets {
            only_in_legacy: [stray].into_iter().collect(),
            only_in_roles: BTreeSet::new(),
        }]);
        assert!(!d.cutover_permitted(), "who may sign differs — that can never be waved through");

        // And a threshold change without its counterpart is NOT mistaken for the clamp.
        let mut c = Chain::new().await;
        c.change(add(c.sov, a)).await;
        c.mirror().await;
        c.append(threshold(c.sov, 2)).await; // legacy only: 2-of-2 vs roles still 1
        let d = c.diff();
        assert_eq!(d.divergences, vec![CouncilDivergence::RequiredSignatures {
            legacy_effective: 2, role_required: 1,
        }]);
        assert!(!d.cutover_permitted());
    }

    /// At most one council tree. `build_mirror` refuses a second, and a second mirror event
    /// that reached the chain anyway — a write path that skipped its refusal — is ignored by
    /// replay rather than forking the council into two bodies.
    #[tokio::test]
    async fn a_council_is_mirrored_once_and_replay_ignores_a_second_mirror() {
        let mut c = Chain::new().await;
        c.change(add(c.sov, Uuid::new_v4())).await;
        c.mirror().await;
        let first = c.state().mirrored_council.unwrap();
        let seats_before = c.state().roles.len();

        match build_mirror(&c.state(), c.sov, c.sov) {
            Err(MirrorRefusal::AlreadyMirrored { council_role_lct_id }) => assert_eq!(council_role_lct_id, first),
            Ok(_) => panic!("a second mirror must be refused"),
        }

        c.append(HubEvent::CouncilMirrored {
            council_role_lct_id: Uuid::new_v4(),
            seats: vec![MirroredSeat { seat_role_lct_id: Uuid::new_v4(), occupant: Uuid::new_v4() }],
            required_m: 1, legacy_basis_index: 0, mirrored_by: c.sov,
        }).await;
        let st = c.state();
        assert_eq!(st.mirrored_council, Some(first), "the first tree stands");
        assert_eq!(st.roles.len(), seats_before, "and the second one constituted nothing");
        assert!(c.diff().agrees());
    }

    /// GPT's #848 HOLD: M = 0 must never enter the role substrate. The legacy arm clamps a
    /// zero to 1, but the requested value used to be stored raw, so a CLI-authored or
    /// historical `new_m: 0` would have mirrored as a council requiring NO signatures. Every
    /// door is driven: the requested value, the mirror, the threshold counterpart, and a raw
    /// quorum-set and raw mirror a foreign chain could carry.
    #[tokio::test]
    async fn a_zero_threshold_never_becomes_a_zero_signature_body() {
        let mut c = Chain::new().await;
        c.change(add(c.sov, Uuid::new_v4())).await;
        c.append(threshold(c.sov, 0)).await; // historical / foreign: the CLI now refuses this

        let d = c.diff();
        assert_eq!(d.legacy.m, 1, "legacy clamps a zero up");
        assert_eq!(d.legacy.requested_m, Some(1), "and the request is stored with its lower bound, not raw");

        c.mirror().await;
        let d = c.diff();
        assert_eq!(d.roles.as_ref().unwrap().quorum.required, 1, "the mirror constitutes a 1-signature body");
        assert!(d.agrees(), "{:?}", d.divergences);

        let council = c.state().mirrored_council.unwrap();
        let parts = counterparts(&c.state(), &threshold(c.sov, 0));
        assert!(matches!(parts.as_slice(), [HubEvent::RoleQuorumSet { required_m: 1, .. }]),
            "the counterpart of a zero asks for one");

        c.append(HubEvent::RoleQuorumSet { role_lct_id: council, required_m: 0, set_by: c.sov }).await;
        assert_eq!(c.state().roles[&council].quorum_m, Some(1), "a raw zero quorum-set is normalised on replay");

        let mut fresh = Chain::new().await;
        let raw_council = Uuid::new_v4();
        fresh.append(HubEvent::CouncilMirrored {
            council_role_lct_id: raw_council,
            seats: vec![MirroredSeat { seat_role_lct_id: Uuid::new_v4(), occupant: fresh.sov }],
            required_m: 0, legacy_basis_index: 0, mirrored_by: fresh.sov,
        }).await;
        assert_eq!(fresh.state().roles[&raw_council].quorum_m, Some(1), "so is a raw zero mirror");
    }

    /// The other half of the same HOLD: the lower-bound normalisation must not become a clamp.
    /// An M above the seats that exist is the law asking for more than is present, and it is
    /// kept EXACTLY — which is what lets a vacancy report the body unable to act instead of
    /// quietly lowering what the law requires.
    #[tokio::test]
    async fn a_threshold_above_the_seats_is_kept_exactly() {
        let mut c = Chain::new().await;
        c.change(add(c.sov, Uuid::new_v4())).await;
        c.change(add(c.sov, Uuid::new_v4())).await;
        c.change(threshold(c.sov, 5)).await; // three seats, the law asks for five
        let d = c.diff();
        assert_eq!((d.legacy.m, d.legacy.requested_m), (3, Some(5)), "legacy clamps to N; the request is kept");

        c.mirror().await;
        let d = c.diff();
        let q = d.roles.as_ref().unwrap().quorum;
        assert_eq!((q.established, q.occupied, q.required), (3, 3, 5), "M above N survives the mirror untouched");
        assert!(!q.reachable());
        assert_eq!(d.divergences, vec![CouncilDivergence::LegacyClampedThreshold {
            requested: 5, legacy_effective: 3, role_required: 5,
        }]);
        assert!(d.cutover_permitted());
    }

    #[tokio::test]
    async fn counterparts_are_empty_before_mirroring_and_for_anything_but_council_changes() {
        let mut c = Chain::new().await;
        let a = Uuid::new_v4();
        assert!(counterparts(&c.state(), &add(c.sov, a)).is_empty(),
            "before the tree exists there is nothing to keep in step");
        c.change(add(c.sov, a)).await;
        c.mirror().await;
        let unrelated = HubEvent::EventRecorded {
            event_kind: "demo".into(), title: "t".into(), attended_by: vec![],
            recorded_by: c.sov, held_at: Utc::now(),
        };
        assert!(counterparts(&c.state(), &unrelated).is_empty());
        assert!(counterparts(&c.state(), &add(c.sov, a)).is_empty(),
            "re-adding a holder who already occupies a seat changes nothing");
        assert!(counterparts(&c.state(), &remove(c.sov, Uuid::new_v4())).is_empty(),
            "removing someone who holds no seat vacates nothing");
    }
}
