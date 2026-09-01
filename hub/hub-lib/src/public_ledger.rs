//! The public decision record (chapter-delivery B9a).
//!
//! "Governance opacity" is a confirmed pain point for the proving use case, and
//! "transparent" is the headline promise. The ledger already holds every governed
//! act; until now it was visible only on the operator plane. This module is the
//! **public projection** of it — plane D at public exposure, a separate surface
//! with a separate authorization from the member view (B9b).
//!
//! # The safety property: construct, never filter
//!
//! A projection that *removes* fields from an event leaks every field somebody
//! adds later. So nothing here serializes a [`HubEvent`]. Each disclosed kind is
//! rebuilt by hand into [`PublicDecision`], naming the fields it discloses. A new
//! variant — or a new field on an existing variant — cannot reach a public caller
//! without someone editing `classify` and the test that pins the disclosed set.
//!
//! # Fail-closed by default
//!
//! `classify` matches an **allowlist**. Everything unmatched is [`Disclosure::Withheld`],
//! including any variant added after this was written. Getting a new act onto the
//! public record is a deliberate edit; forgetting to classify one discloses nothing.
//!
//! # Why withheld entries still appear
//!
//! Omitting them entirely would leave gaps in a hash-chained record, and a reader
//! cannot distinguish "nothing happened at index 41" from "index 41 was removed".
//! So every entry keeps its `index`, `timestamp`, `entry_hash`, `prev_hash` and
//! whether the council authorized it — enough to verify the chain is continuous and
//! unbroken — while `kind` reads `withheld` and no detail is emitted.
//!
//! `prev_hash` is what makes that sentence true rather than aspirational. With only
//! `entry_hash` a reader can detect a missing INDEX and nothing else; the linkage
//! claim needs the link. Both hashes are opaque, so carrying them on a withheld
//! entry discloses nothing about the act it withholds. Continuity is itself an
//! accountability property: a chapter cannot quietly drop an inconvenient decision.
//!
//! This does disclose *activity timing and volume*, which is a deliberate trade: a
//! public record of a volunteer chapter that hides how often it decides things is
//! not answering the question it exists to answer.
//!
//! # One free-text field is public on purpose
//!
//! `diff_summary` on a law or charter amendment is emitted verbatim. It is the one
//! place an author's prose reaches an anonymous reader, and it is included because
//! an amendment record that shows only a hash tells a member nothing about what
//! changed. **Write it for that audience** — the field is documented as public in
//! `hub/docs/MAINTAINER.md`.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::events::HubEvent;
use crate::ledger::LedgerEntry;

/// Whether a caller sees the act, or only that an act occurred.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Disclosure {
    /// Classified public: `kind` names the act and `detail` may describe it.
    Disclosed,
    /// Not classified for public disclosure. The entry's existence and chain
    /// position are shown; nothing about what it was.
    Withheld,
}

/// One entry as an anonymous caller may see it.
///
/// Every field here is chosen deliberately. There is no `#[serde(flatten)]` of an
/// event, and no path by which an unclassified field reaches this struct.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PublicDecision {
    /// Chain position. Always present so continuity is verifiable.
    pub index: u64,
    /// When the act was committed. Always present.
    pub timestamp: DateTime<Utc>,
    /// The entry's own hash. Always present.
    pub entry_hash: String,
    /// The PRECEDING entry's hash. Always present, including on withheld entries.
    ///
    /// Without this the record advertised a property it could not deliver (GPT/Nova
    /// blocking review of dd4918b). `entry_hash` alone lets a reader see an ORDINAL gap —
    /// index 41 missing between 40 and 42 — but nothing more: a public server could
    /// substitute an arbitrary hash at any index and the response gave the reader nothing
    /// to compare it against. Ordinal continuity is not hash-chain verification, and the
    /// module doc claimed the latter.
    ///
    /// Emitting it for WITHHELD entries is the half that matters: a hash is opaque, so it
    /// discloses nothing about the act, and it is precisely the link that lets a reader
    /// carry verification ACROSS a withheld entry instead of stopping at one.
    pub prev_hash: String,
    /// Whether the Sovereign Council's M-of-N flow authorized this act. A fact
    /// *about the authorization*, carrying no identity.
    pub council_authorized: bool,
    pub disclosure: Disclosure,
    /// The act's kind when disclosed; `"withheld"` otherwise.
    pub kind: String,
    /// A short human description, only for disclosed kinds.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub detail: Option<String>,
    /// The run of entries that disclosed nothing between this act and the next MORE
    /// RECENT disclosed act (or the ledger head, for the newest entry in the window).
    /// Absent when the two are adjacent. This is how continuity survives windowing.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub withheld_before: Option<WithheldSpan>,
}

/// A run of consecutive entries that disclosed nothing, reported as a counted span.
///
/// Withheld entries used to be emitted one row each, to prove the chain is continuous.
/// On a real ledger that buried every governed act: measured 2026-09-01 on a live chapter,
/// the newest 200 entries were 100% withheld (398 of the last 400 are mesh `referenced_act`)
/// while every governance act sat 1,700+ entries back. A public record that renders as an
/// unbroken wall of "withheld" reads as concealment, which is the opposite of the surface's
/// purpose. A counted span keeps the continuity property — a reader can still verify no index
/// is missing — in one line instead of hundreds of rows.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct WithheldSpan {
    /// How many consecutive entries disclosed nothing.
    pub count: u64,
    /// Inclusive index range covered, oldest first. `from_index <= to_index`.
    pub from_index: u64,
    pub to_index: u64,
}

/// The kinds classified for public disclosure.
///
/// Pinned as data so the test can assert the disclosed set exactly: a new variant
/// classified without a deliberate decision fails that test rather than shipping.
pub const PUBLIC_KINDS: &[&str] = &[
    "genesis",
    "charter_amended",
    "law_amended",
    "role_assigned",
    "council_threshold_changed",
    "member_join_resolved",
    "event_recorded",
];

/// Project one entry for an anonymous caller.
///
/// The allowlist is the whole security argument: the `_ =>` arm withholds, so a
/// variant added to [`HubEvent`] after this was written discloses nothing.
pub fn public_projection(entry: &LedgerEntry) -> PublicDecision {
    let (kind, detail) = classify(&entry.event);
    let disclosure = if kind.is_some() { Disclosure::Disclosed } else { Disclosure::Withheld };
    PublicDecision {
        index: entry.index,
        timestamp: entry.timestamp,
        entry_hash: entry.entry_hash.clone(),
        prev_hash: entry.prev_hash.clone(),
        council_authorized: entry.proposal_ref.is_some(),
        disclosure,
        kind: kind.unwrap_or("withheld").to_string(),
        detail,
        withheld_before: None,
    }
}

/// Project the newest `limit` **disclosable** acts, newest first, annotating each with the
/// run of withheld entries between it and the next more recent disclosed act.
///
/// Windowing over disclosable acts rather than over raw entries is the whole point: a fixed
/// window of raw entries on a busy ledger contains no governance at all (see [`WithheldSpan`]).
/// The scan walks newest-first and stops once `limit` acts are found, so the cost is bounded
/// by how far back the governance is, not by the ledger's size.
///
/// Returns the projected acts and the oldest index examined, so a caller can report how much
/// of the chain the window actually covers.
pub fn public_record(entries: &[LedgerEntry], limit: usize) -> (Vec<PublicDecision>, Option<u64>) {
    let mut out: Vec<PublicDecision> = Vec::new();
    let mut pending: Option<WithheldSpan> = None;
    let mut scanned_to: Option<u64> = None;

    for e in entries.iter().rev() {
        scanned_to = Some(e.index);
        let mut d = public_projection(e);
        if d.disclosure == Disclosure::Withheld {
            // Accumulate the run. Entries arrive newest-first, so the span grows downward.
            pending = Some(match pending {
                None => WithheldSpan { count: 1, from_index: e.index, to_index: e.index },
                Some(s) => WithheldSpan { count: s.count + 1, from_index: e.index, to_index: s.to_index },
            });
            continue;
        }
        d.withheld_before = pending.take();
        out.push(d);
        if out.len() >= limit {
            break;
        }
    }
    (out, scanned_to)
}

/// Returns `Some(kind)` plus an optional description for classified-public acts.
///
/// **Identity is never disclosed here.** Who assigned a role, who resolved a join,
/// who attended an event are member facts and belong to member-exposure surfaces
/// with their own authorization — not to an anonymous reader. What is disclosed is
/// that the act happened, under what law, and when.
fn classify(event: &HubEvent) -> (Option<&'static str>, Option<String>) {
    match event {
        HubEvent::Genesis { hub_name, charter_hash, .. } => (
            Some("genesis"),
            Some(format!("chapter \"{hub_name}\" founded under charter {}", short(charter_hash))),
        ),

        HubEvent::CharterAmended { new_charter_hash, diff_summary, .. } => (
            Some("charter_amended"),
            Some(match diff_summary {
                Some(s) => format!("charter amended to {}: {s}", short(new_charter_hash)),
                None => format!("charter amended to {}", short(new_charter_hash)),
            }),
        ),

        HubEvent::LawAmended { new_law_sha256, version, diff_summary, .. } => (
            Some("law_amended"),
            Some(match diff_summary {
                Some(s) => format!("law {version} ({}): {s}", short(new_law_sha256)),
                None => format!("law {version} ({})", short(new_law_sha256)),
            }),
        ),

        // The ROLE is disclosed; the occupant is not. Who holds an office is a
        // membership fact for the roles directory (B3) to disclose under its own
        // decision, not a side effect of publishing the decision record.
        HubEvent::RoleAssigned { role, .. } => (
            Some("role_assigned"),
            Some(format!("{} filled", role_label(role))),
        ),

        HubEvent::CouncilThresholdChanged { new_m, .. } => (
            Some("council_threshold_changed"),
            Some(format!("council signing threshold set to {new_m}")),
        ),

        // The OUTCOME is the governance fact — that admissions are decided, and how.
        // The applicant, the resolver, and any stated reason are not disclosed: a
        // public "denied, because ..." about an identifiable person is precisely the
        // disclosure a volunteer organisation must not make by default.
        HubEvent::MemberJoinResolved { approved, .. } => (
            Some("member_join_resolved"),
            Some(if *approved { "membership request admitted".into() }
                 else { "membership request declined".into() }),
        ),

        // A chapter event is outward-facing by nature. The attendee list is not.
        HubEvent::EventRecorded { event_kind, title, .. } => (
            Some("event_recorded"),
            Some(format!("{event_kind}: {title}")),
        ),

        // Everything else — including any variant added after this was written.
        _ => (None, None),
    }
}

fn short(hash: &str) -> String {
    let h = hash.strip_prefix("sha256:").unwrap_or(hash);
    h.chars().take(12).collect()
}

fn role_label(role: &web4_core::role::SocietyRole) -> String {
    serde_json::to_value(role)
        .ok()
        .and_then(|v| v.as_str().map(str::to_string))
        .unwrap_or_else(|| format!("{role:?}").to_lowercase())
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::TimeZone;
    use uuid::Uuid;

    fn entry(index: u64, event: HubEvent) -> LedgerEntry {
        LedgerEntry {
            index,
            timestamp: Utc.with_ymd_and_hms(2026, 8, 27, 12, 0, 0).unwrap(),
            // CHAINED, not a constant. The fixture used a literal "prev" for every entry,
            // which cannot express linkage at all: a linkage test written against it would
            // pass on a record whose hashes do not connect. entry N's prev is entry N-1's
            // hash, exactly as the real ledger builds it.
            prev_hash: if index == 0 { "genesis".into() } else { format!("hash{}", index - 1) },
            actor_lct_id: Uuid::nil(),
            event,
            signature: "sig".into(),
            entry_hash: format!("hash{index}"),
            proposal_ref: None,
        }
    }

    /// ADJACENT LINKAGE IS VERIFIABLE, INCLUDING ACROSS A WITHHELD ENTRY.
    ///
    /// GPT/Nova's blocking finding on dd4918b: the record advertised hash-chain
    /// verification while exposing only `entry_hash`. A reader could see that index 41 was
    /// missing and could NOT tell whether the hash at index 42 actually followed the one at
    /// 41 — a public server could substitute any value and nothing in the response
    /// contradicted it. Ordinal continuity is a weaker property than linkage, and the
    /// module doc claimed the stronger one.
    ///
    /// The middle entry here is WITHHELD on purpose. That is the case the property exists
    /// for: verification has to carry ACROSS an entry whose content a reader may not see,
    /// or a chapter could hide a decision by making its neighbours unverifiable.
    #[test]
    fn a_reader_can_verify_linkage_across_a_withheld_entry() {
        let chain = vec![
            entry(0, HubEvent::Genesis {
                hub_name: "chapter".into(),
                charter_hash: "c".into(),
                founding_sovereign_lct_id: Uuid::nil(),
                created_at: Utc.with_ymd_and_hms(2026, 8, 27, 12, 0, 0).unwrap(),
            }),
            // Not in PUBLIC_KINDS -> withheld, and its hashes must still link.
            entry(1, HubEvent::PostAdded {
                topic_id: Uuid::new_v4(),
                post_id: Uuid::new_v4(),
                body: "a private post".into(),
                posted_by: Uuid::new_v4(),
            }),
            entry(2, HubEvent::Genesis {
                hub_name: "chapter".into(),
                charter_hash: "c".into(),
                founding_sovereign_lct_id: Uuid::nil(),
                created_at: Utc.with_ymd_and_hms(2026, 8, 27, 12, 0, 0).unwrap(),
            }),
        ];
        let rec: Vec<_> = chain.iter().map(public_projection).collect();

        assert_eq!(rec[1].disclosure, Disclosure::Withheld, "fixture: middle entry withheld");
        for w in rec.windows(2) {
            assert_eq!(
                w[1].prev_hash, w[0].entry_hash,
                "entry {} must name entry {}'s hash as its predecessor — without prev_hash \
                 a reader can only detect a missing INDEX, which is ordinal continuity and \
                 not the hash-chain verification this record advertises",
                w[1].index, w[0].index
            );
        }
        assert!(!rec[1].prev_hash.is_empty(),
            "a WITHHELD entry must still carry its link: a hash is opaque, so omitting it \
             protects nothing and breaks verification exactly where it is needed");
    }

    /// The load-bearing test. A member's post body must not reach a public caller
    /// through ANY field, so this searches the serialized projection rather than
    /// asserting on one field — a leak through `detail`, `kind`, or a field added
    /// later would still be caught.
    #[test]
    fn member_content_never_reaches_the_public_projection() {
        const SECRET: &str = "the-body-of-a-private-post";
        let e = entry(7, HubEvent::PostAdded {
            topic_id: Uuid::new_v4(),
            post_id: Uuid::new_v4(),
            body: SECRET.into(),
            posted_by: Uuid::new_v4(),
        });
        let p = public_projection(&e);
        assert_eq!(p.disclosure, Disclosure::Withheld);
        assert_eq!(p.kind, "withheld");
        assert!(p.detail.is_none());

        let json = serde_json::to_string(&p).unwrap();
        assert!(!json.contains(SECRET), "post body leaked into the public projection: {json}");
    }

    /// Member identity is not disclosed even for an act whose KIND is public.
    #[test]
    fn a_disclosed_kind_still_withholds_the_member() {
        let member = Uuid::new_v4();
        let e = entry(9, HubEvent::MemberJoinResolved {
            request_id: Uuid::new_v4(),
            approved: false,
            resolved_by: member,
            reason: Some("did not meet the vouching bar".into()),
            resolved_at: Utc::now(),
        });
        let p = public_projection(&e);
        assert_eq!(p.disclosure, Disclosure::Disclosed);
        let json = serde_json::to_string(&p).unwrap();
        assert!(!json.contains(&member.to_string()), "resolver identity leaked: {json}");
        assert!(!json.contains("vouching bar"), "stated reason leaked: {json}");
        assert!(json.contains("declined"), "the governance outcome must be visible: {json}");
    }

    /// THE REGRESSION TEST for the live defect: a realistic ledger is mostly
    /// non-disclosable traffic with governance acts far back. Windowing over raw
    /// entries returned zero governance; windowing over disclosable acts must
    /// return them, and must account for every skipped entry.
    #[test]
    fn a_busy_ledger_still_surfaces_its_governance() {
        // 1 governance act, then 300 entries of mesh traffic, then another act.
        let mut entries = vec![entry(1, HubEvent::CouncilThresholdChanged {
            new_m: 2, initiated_by: Uuid::nil() })];
        for i in 2..=301 {
            entries.push(entry(i, HubEvent::PostAdded {
                topic_id: Uuid::new_v4(), post_id: Uuid::new_v4(),
                body: "mesh chatter".into(), posted_by: Uuid::new_v4() }));
        }
        entries.push(entry(302, HubEvent::LawAmended {
            new_law_sha256: "sha256:deadbeefcafe0000".into(), amended_by: Uuid::new_v4(),
            version: "1.1.0".into(), diff_summary: Some("raised quorum".into()) }));

        let (rec, scanned_to) = public_record(&entries, 20);

        // The old behaviour: a 200-entry raw window over this ledger yields NOTHING.
        let raw_window_disclosed = entries.iter().rev().take(200)
            .filter(|e| public_projection(e).disclosure == Disclosure::Disclosed).count();
        assert_eq!(raw_window_disclosed, 1,
            "fixture must reproduce the shape: a raw window sees almost no governance");

        assert_eq!(rec.len(), 2, "both governance acts must surface: {rec:?}");
        assert_eq!(rec[0].index, 302);
        assert_eq!(rec[1].index, 1);

        // Every skipped entry is accounted for, so continuity survives windowing.
        let span = rec[1].withheld_before.as_ref().expect("the 300-entry run must be reported");
        assert_eq!(span.count, 300);
        assert_eq!(span.from_index, 2);
        assert_eq!(span.to_index, 301);
        assert!(rec[0].withheld_before.is_none(), "the newest act is adjacent to the head");
        assert_eq!(scanned_to, Some(1));
    }

    /// Withheld entries keep their chain position, so a reader can verify the
    /// record is continuous and nothing was quietly dropped.
    #[test]
    fn withheld_entries_preserve_chain_continuity() {
        let entries = vec![
            entry(1, HubEvent::CouncilThresholdChanged { new_m: 2, initiated_by: Uuid::nil() }),
            entry(2, HubEvent::PostAdded {
                topic_id: Uuid::new_v4(), post_id: Uuid::new_v4(),
                body: "private".into(), posted_by: Uuid::new_v4(),
            }),
            entry(3, HubEvent::CouncilThresholdChanged { new_m: 3, initiated_by: Uuid::nil() }),
        ];
        let (rec, _) = public_record(&entries, 10);
        // Only the two disclosable acts are rows now; the withheld one is accounted
        // for as a span on the older act, which is what keeps continuity checkable.
        let indices: Vec<u64> = rec.iter().map(|d| d.index).collect();
        assert_eq!(indices, vec![3, 1], "newest first, disclosable only");
        assert!(rec.iter().all(|d| !d.entry_hash.is_empty()), "chain hash always present");
        let span = rec[1].withheld_before.as_ref().expect("the skipped entry must be reported");
        assert_eq!((span.count, span.from_index, span.to_index), (1, 2, 2));
    }

    /// Pins the disclosed set. A variant classified public without a deliberate
    /// decision fails here rather than shipping — and the `_ =>` arm means
    /// forgetting to classify a NEW variant discloses nothing.
    #[test]
    fn the_disclosed_set_is_exactly_what_was_decided() {
        let mut disclosed: Vec<&str> = PUBLIC_KINDS.to_vec();
        disclosed.sort_unstable();
        let mut expected = vec![
            "genesis", "charter_amended", "law_amended", "role_assigned",
            "council_threshold_changed", "member_join_resolved", "event_recorded",
        ];
        expected.sort_unstable();
        assert_eq!(disclosed, expected,
            "the public disclosure set changed — that is a governance decision, not a refactor");
    }

    /// An unclassified kind is withheld by default. This is the property that
    /// survives someone adding a variant and forgetting this module exists.
    #[test]
    fn an_unclassified_kind_defaults_to_withheld() {
        for e in [
            HubEvent::MemberSkillDeclared {
                member_lct_id: Uuid::nil(), skill: "rust".into(),
                declared_by: Uuid::nil(),
            },
        ] {
            let p = public_projection(&entry(1, e));
            assert_eq!(p.disclosure, Disclosure::Withheld,
                "an unclassified kind must withhold: {p:?}");
            assert!(!PUBLIC_KINDS.contains(&p.kind.as_str()));
        }
    }

    #[test]
    fn an_amendment_discloses_what_changed() {
        let e = entry(4, HubEvent::LawAmended {
            new_law_sha256: "sha256:abcdef1234567890".into(),
            amended_by: Uuid::new_v4(),
            version: "1.0.3".into(),
            diff_summary: Some("quorum for role conferral raised to 3".into()),
        });
        let p = public_projection(&e);
        let d = p.detail.unwrap();
        assert!(d.contains("1.0.3"), "{d}");
        assert!(d.contains("abcdef123456"), "{d}");
        assert!(d.contains("quorum"), "the summary is public on purpose: {d}");
    }
}
