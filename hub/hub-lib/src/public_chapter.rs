//! B1 — the public chapter profile: what this society *is*, for an outsider.
//!
//! The companion to [`crate::public_ledger`], which answers "what has it decided". Together
//! they are the whole public plane's data: identity and law here, acts there.
//!
//! # Why this is built by hand rather than derived
//!
//! The obvious implementation is to serialize [`crate::state::HubState`] with
//! `#[serde(skip)]` on the private parts. That is the shape this module exists to refuse.
//! A skip-list is a **denylist**: it discloses every field nobody remembered to mark, so the
//! failure mode is silent over-disclosure at exactly the moment someone adds a field — and
//! the person adding a member-roster field to internal state is not thinking about the
//! anonymous HTTP surface. [`ChapterProfile`] is an **allowlist by construction**: it has
//! its own named fields, each assigned from an explicit expression, so a new field on
//! `HubState` reaches the public plane only when a human writes a line here.
//!
//! `chapter_profile_is_an_allowlist_not_a_filter` plants a member carrying a secret profile
//! value in internal state and asserts it cannot appear in the serialized output.
//!
//! # What is deliberately absent, and why
//!
//! Under the tiered-disclosure model (PRD_CHAPTER_DELIVERY §4.5) the public tier answers
//! *that this exists and that acts occurred*; **who participated** is the member tier.
//!
//! - **No member identities, names, skills or profile fields.** Member tier.
//! - **No member count.** This one is a judgment call worth stating: a count carries no
//!   identity and is tempting to include as "chapter size". But it is an aggregate *over
//!   the membership*, it moves when a specific person joins or leaves, and a small chapter's
//!   count plus one public `member_join_resolved` act is close to naming them. It is
//!   therefore member tier, and a later decision to publish it should be a decision, not a
//!   convenience.
//! - **No founding sovereign LCT.** It is an identity, and it is not in
//!   `.well-known/web4-hub.json` either; publishing it here would widen disclosure as a side
//!   effect of adding a page.
//! - **The charter HASH, never the charter text.** A hash lets an outsider verify a copy
//!   they were given; it discloses nothing on its own.

use serde::{Deserialize, Serialize};

use crate::law::Law;
use crate::state::HubState;

/// The public, machine-readable answer to "what is this chapter?".
///
/// Every field is public tier. See the module docs for what is excluded and why.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChapterProfile {
    /// The society's own LCT id — the same value `.well-known/web4-hub.json` publishes.
    pub hub_id: String,
    /// The society's chosen name.
    pub name: String,
    /// Whether the vault is sealed right now. Published because a locked hub answers 503 on
    /// most routes, and a reader who cannot tell "sealed" from "broken" reads a working
    /// safety posture as an outage.
    pub locked: bool,
    /// `sha256:...` of the founding charter. The hash, never the text: it is verifiable
    /// against a copy and discloses nothing by itself.
    ///
    /// `None` means only "not disclosed here" and is NOT evidence of an unfounded chapter —
    /// a sealed hub has an empty projection, so this is `None` while locked no matter what
    /// the store holds. Read it together with [`ChapterProfile::locked`]; the renderer must
    /// not say "not yet founded" when the true answer is "sealed".
    pub charter_hash: Option<String>,
    /// The law in force, as far as a stranger may see it.
    ///
    /// `None` means **sealed**, not lawless. A locked hub holds no law in memory, so a
    /// `ChapterLaw { present: false }` built from that state would tell a stranger this
    /// chapter has no rules — a false statement about the society, produced by reading an
    /// unavailable fact as an absent one. Sealed and lawless are opposite claims.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub law: Option<ChapterLaw>,
    /// How this chapter answers a membership request — derived by EVALUATING law, never read
    /// from a display flag. See [`AdmissionPosture`].
    ///
    /// `None` while sealed, for the same reason as [`ChapterProfile::law`], and it matters
    /// more here: evaluating an absent law yields ALLOW, so a locked hub would have
    /// advertised "anyone can join, no review" while its actual admission norm sat encrypted
    /// on disk. Measured on the live fleet hub, 2026-09-08.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub admission: Option<AdmissionPosture>,
    /// Where the rest of the public plane lives, so the page and its readers agree on one
    /// set of pointers instead of hardcoding paths in three renderers.
    pub links: ChapterLinks,
}

/// Law as the public tier sees it: that there is one, which version, and how to fetch it.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChapterLaw {
    /// `false` when no law is loaded — an honest state, not an error. A hub without law is
    /// open by default, which is exactly what a reader needs to know.
    pub present: bool,
    pub version: Option<String>,
    /// Counts, not content: the text is served whole at `links.law`, and summarising it here
    /// would create a second description of law that can drift from the law itself.
    pub norms: usize,
    pub procedures: usize,
}

/// What a membership request would actually meet.
///
/// **Derived, never declared.** `admission.open` exists in law as a display knob that no gate
/// consumes; rendering it let the landing page claim "closed admission" while the law
/// auto-admitted (review 2026-07-23). This is computed by running the same synthetic R6 the
/// join path runs, so the page cannot disagree with the gate.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AdmissionPosture {
    /// A request is admitted without human review.
    Open,
    /// A request queues for a human decision.
    Reviewed,
    /// A request is refused.
    Closed,
}

impl AdmissionPosture {
    /// One sentence, in the second person, for a reader who is deciding whether to apply.
    pub fn describe(&self) -> &'static str {
        match self {
            Self::Open => "Anyone holding a Web4 LCT can request citizenship and is admitted \
                           without human review.",
            Self::Reviewed => "Membership requests queue for a human decision; the chapter's \
                              operator admits or declines each one.",
            Self::Closed => "This chapter is not accepting membership requests at the moment.",
        }
    }
}

/// Canonical pointers to the rest of the public plane.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChapterLinks {
    /// The signed law, served whole.
    pub law: String,
    /// The B9a public decision record.
    pub decisions: String,
    /// The machine-readable descriptor.
    pub descriptor: String,
}

/// Build the public profile.
///
/// `admission` is passed in rather than computed here because evaluating law needs the R6
/// request type and the caller already holds the law guard; keeping the evaluation at the
/// call site avoids this module taking a dependency on the request vocabulary purely to
/// duplicate a decision the join path already makes.
pub fn chapter_profile(
    hub_id: uuid::Uuid,
    // The society's configured name, from the daemon's own state rather than the ledger
    // projection. A SEALED hub has an empty projection, and taking the name from there made a
    // locked chapter render nameless — "absent" wearing the clothes of "not yet founded".
    hub_name: &str,
    state: &HubState,
    law: Option<&Law>,
    locked: bool,
    admission: AdmissionPosture,
) -> ChapterProfile {
    // Every line below is a deliberate disclosure. Adding a field to HubState does not add
    // one here; that is the point of the module.
    ChapterProfile {
        hub_id: hub_id.to_string(),
        name: hub_name.to_string(),
        locked,
        charter_hash: state.charter_hash.clone(),
        // SEALED IS NOT LAWLESS, and sealed is not open-admission. While locked there is no
        // law in memory to describe or to evaluate, so both facts are withheld rather than
        // computed from an absence. Everything above this line survives a sealed vault;
        // nothing below it does.
        law: (!locked).then(|| ChapterLaw {
            present: law.is_some(),
            version: law.map(|l| l.version.clone()),
            norms: law.map(|l| l.norms.len()).unwrap_or(0),
            procedures: law.map(|l| l.procedures.len()).unwrap_or(0),
        }),
        admission: (!locked).then_some(admission),
        links: ChapterLinks {
            law: format!("/v1/hubs/{hub_id}/law"),
            decisions: format!("/v1/hubs/{hub_id}/decisions"),
            descriptor: "/.well-known/web4-hub.json".to_string(),
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::{Member, ProfileField};

    fn state_with_a_secret_member() -> HubState {
        let mut s = HubState::default();
        s.hub_name = "Web4 Fleet".to_string();
        s.charter_hash = Some("sha256:deadbeef".to_string());
        let id = uuid::Uuid::new_v4();
        let mut m = Member {
            lct_id: id,
            name: Some("SECRET-MEMBER-NAME".into()),
            skills: Default::default(),
            profile: Default::default(),
        };
        m.skills.insert("SECRET-SKILL".to_string());
        m.profile.insert(
            "phone".to_string(),
            ProfileField::new("SECRET-PHONE-555", crate::events::ProfileVisibility::default()),
        );
        s.members.insert(id, m);
        s.member_pubkeys.insert(id, "SECRET-PUBKEY-HEX".to_string());
        s
    }

    /// The property the whole module exists for: internal state can carry anything and the
    /// public projection still discloses only its own named fields.
    ///
    /// Asserted against the SERIALIZED bytes rather than the struct, because that is what
    /// reaches a stranger — a field could be added, forgotten, and still be invisible in a
    /// field-by-field comparison written at the same time.
    #[test]
    fn chapter_profile_is_an_allowlist_not_a_filter() {
        let state = state_with_a_secret_member();
        let profile = chapter_profile(uuid::Uuid::nil(), "Web4 Fleet", &state, None, false, AdmissionPosture::Open);
        let json = serde_json::to_string(&profile).unwrap();
        for planted in [
            "SECRET-MEMBER-NAME",
            "SECRET-SKILL",
            "SECRET-PHONE-555",
            "SECRET-PUBKEY-HEX",
        ] {
            assert!(
                !json.contains(planted),
                "public chapter output leaked {planted:?} from internal state: {json}"
            );
        }
        // And the fixture must really have planted them, or this guard passes vacuously.
        let internal = serde_json::to_string(&state).unwrap();
        assert!(internal.contains("SECRET-MEMBER-NAME"), "fixture did not plant the member");
        assert!(internal.contains("SECRET-PHONE-555"), "fixture did not plant the profile field");
    }

    /// Membership is a count over people, and the public tier does not answer "who".
    /// Pinned so a later "chapter size" convenience is a decision rather than a drive-by.
    #[test]
    fn the_public_profile_does_not_publish_how_many_members_there_are() {
        let state = state_with_a_secret_member();
        assert_eq!(state.members.len(), 1, "fixture has exactly one member to count");
        let json =
            serde_json::to_string(&chapter_profile(uuid::Uuid::nil(), "Web4 Fleet", &state, None, false, AdmissionPosture::Open))
                .unwrap();
        assert!(!json.contains("member"), "the profile names no member-derived field: {json}");
    }

    /// A sealed hub still knows its own name. The projection is empty while locked, so a
    /// name taken from it renders blank — which reads as a broken page, not a locked one.
    #[test]
    fn a_sealed_chapter_still_reports_its_name() {
        let p = chapter_profile(
            uuid::Uuid::nil(), "Web4 Fleet", &HubState::default(), None, true, AdmissionPosture::Closed,
        );
        assert_eq!(p.name, "Web4 Fleet", "the name survives an empty projection");
        assert!(p.locked);
        assert_eq!(
            p.charter_hash, None,
            "and the charter is absent while sealed — which the renderer must not report as unfounded"
        );
        // The one that was actually wrong in production: evaluating an absent law yields
        // ALLOW, so a sealed hub advertised open admission while its admission norm sat
        // encrypted on disk. Withheld, not computed.
        assert_eq!(p.admission, None, "a sealed hub must not claim an admission posture");
        assert_eq!(p.law, None, "a sealed hub must not claim to be lawless");
        let json = serde_json::to_string(&p).unwrap();
        assert!(!json.contains("admission"), "sealed: the key is absent, not null-with-a-guess: {json}");
        // `"law"` alone would match links.law, which is a pointer and always present.
        assert!(!json.contains("\"law\":{"), "sealed: no law OBJECT at all: {json}");
        assert!(json.contains("Web4 Fleet") && json.contains("\"locked\":true"),
            "but identity and the sealed flag still reach the reader: {json}");
    }

    /// A hub with no law is open by default. Saying "no law" and saying "closed" are
    /// opposite facts and the projection must not confuse them.
    #[test]
    fn no_law_is_reported_as_absent_rather_than_as_an_empty_law() {
        let p = chapter_profile(uuid::Uuid::nil(), "Web4 Fleet", &HubState::default(), None, false, AdmissionPosture::Open);
        let l = p.law.expect("an UNLOCKED hub discloses its law state, even when there is none");
        assert!(!l.present, "no law loaded is reported as absent");
        assert_eq!(l.version, None);
        assert_eq!((l.norms, l.procedures), (0, 0));
        assert_eq!(
            p.admission, Some(AdmissionPosture::Open),
            "and an unlocked, lawless hub really is open — that ALLOW is derived from a law \
             that is genuinely absent, not from one that is merely unreadable"
        );
    }

    /// The locked flag is published on purpose: a sealed hub answers 503 nearly everywhere,
    /// and a reader who cannot tell sealed from broken misreads a working safety posture.
    #[test]
    fn locked_is_disclosed_because_a_sealed_hub_looks_like_a_broken_one() {
        let p = chapter_profile(uuid::Uuid::nil(), "Web4 Fleet", &HubState::default(), None, true, AdmissionPosture::Closed);
        assert!(p.locked);
    }
}
