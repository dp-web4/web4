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
//!
//! # TWO REPRESENTATIONS, TWO DIFFERENT STRENGTHS — read this before claiming either
//!
//! [`public_projection`] emits ONE row per entry. A withheld row keeps its `index`,
//! `timestamp`, `entry_hash`, `prev_hash` and council flag, so a reader can verify
//! **hash-chain linkage** across it: `prev_hash` of N equals `entry_hash` of N-1, and a
//! substituted hash is detectable.
//!
//! [`public_record`] — what the endpoint actually returns — compresses runs of withheld
//! entries into a [`WithheldSpan`] for PRESENTATION, while carrying each hidden entry's
//! link evidence ([`WithheldLink`]) for VERIFICATION. So the human sees one counted line
//! and a machine sees the whole chain: [`verify_linkage`] walks a record oldest-to-newest,
//! expanding spans in place, and fails on the first link that does not lead where it claims.
//!
//! That is web4#807's production property — *an anonymous reader can verify hash-chain
//! continuity THROUGH withheld acts, without learning their contents* — and it holds
//! because a hash is opaque: publishing it discloses nothing about the act while being
//! exactly the value needed to check the link.
//!
//! **It was not always so.** #802 compressed the presentation and the evidence with it,
//! leaving spans that proved only ordinal accounting; the linkage test of the day exercised
//! `public_projection` and stayed green while the SERVED surface lost the property. That is
//! the shape to watch for here: a guard measuring the per-entry representation says nothing
//! about the windowed one.
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
/// purpose. A counted span keeps the presentation to one line instead of hundreds of rows,
/// while `links` keeps the chain checkable through the run (web4#807) — the two are now
/// separate concerns rather than one trade.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct WithheldSpan {
    /// How many consecutive entries disclosed nothing.
    pub count: u64,
    /// Inclusive index range covered, oldest first. `from_index <= to_index`.
    pub from_index: u64,
    pub to_index: u64,
    /// **The link evidence for every entry in the run, oldest first** (web4#807).
    ///
    /// This is what raises the span from ordinal accounting to hash-chain verification.
    /// Each hidden entry contributes its own hash and the hash it claims as predecessor,
    /// and nothing else — a hash is opaque, so publishing it discloses nothing about the
    /// act while being exactly the value a reader needs to check the link.
    ///
    /// Deliberately O(n) in the run length. #807 names that as the acceptable
    /// developmental implementation and a compact proof (skip links, Merkle accumulator)
    /// as the secondary optimisation: *"the optimization path is secondary, the
    /// production property is primary."* The HUMAN presentation still collapses the run
    /// to one line — the renderer never iterates this.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub links: Vec<WithheldLink>,
}

/// One hidden entry's contribution to the chain, and nothing more.
///
/// No timestamp, no kind, no council flag — those are facts ABOUT the act, and the act is
/// withheld. Only the two hashes and the index, which together let a reader walk the chain
/// through the run without learning anything that happened in it.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct WithheldLink {
    pub index: u64,
    pub entry_hash: String,
    pub prev_hash: String,
}

/// Where the public record's hash chain breaks, if it does.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LinkageBreak {
    /// The entry whose `prev_hash` did not match its predecessor's `entry_hash`.
    pub at_index: u64,
    pub expected_prev: String,
    pub found_prev: String,
}

impl std::fmt::Display for LinkageBreak {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "chain break at index {}: claims predecessor {} but the preceding entry \
                   hashes to {}", self.at_index, self.found_prev, self.expected_prev)
    }
}

/// Verify the hash chain of a public record **through withheld runs** (web4#807).
///
/// This is the production property the compact span exists to preserve: an anonymous
/// reader can confirm that the acts they were shown, and the acts they were NOT shown,
/// form one unbroken chain — without learning what the hidden acts were.
///
/// Walks oldest-to-newest across the whole window, expanding each span's `links` in place,
/// and checks that every entry names its immediate predecessor's hash. Returns the FIRST
/// break, which is the one a reader would act on.
///
/// A record with no link evidence in its spans cannot be verified through them and is
/// reported as a break at the span's first index — silence is not a pass. That matters:
/// the failure mode this guards against is a server that omits evidence and is read as
/// having provided it.
///
/// The oldest entry in the window has no predecessor inside the window, so its `prev_hash`
/// is unchecked here by construction — verification is relative to what was served, and a
/// reader anchoring absolutely needs a hash they already trust.
pub fn verify_linkage(record: &[PublicDecision]) -> Result<(), LinkageBreak> {
    // The record is newest-first; the chain reads oldest-first, so walk it reversed.
    // `prev` is the entry most recently verified, disclosed or hidden alike — the whole
    // point is that a hidden entry is a link like any other.
    let mut prev: Option<String> = None;

    let mut check = |index: u64, claimed_prev: &str, own_hash: &str, prev: &mut Option<String>|
        -> Result<(), LinkageBreak> {
        if let Some(expected) = prev.as_ref() {
            if claimed_prev != expected {
                return Err(LinkageBreak {
                    at_index: index,
                    expected_prev: expected.clone(),
                    found_prev: claimed_prev.to_string(),
                });
            }
        }
        *prev = Some(own_hash.to_string());
        Ok(())
    };

    for d in record.iter().rev() {
        check(d.index, &d.prev_hash, &d.entry_hash, &mut prev)?;
        // `withheld_before` describes the run between THIS act and the next more recent
        // one, so in chain order it comes after the act just verified.
        if let Some(span) = &d.withheld_before {
            if span.links.is_empty() {
                // Silence is not a pass. A span with no evidence cannot be verified
                // through, and reporting it as OK is the exact failure this guards:
                // a server that omits evidence being read as having supplied it.
                return Err(LinkageBreak {
                    at_index: span.from_index,
                    expected_prev: prev.clone().unwrap_or_default(),
                    found_prev: "<no link evidence published for this span>".to_string(),
                });
            }
            for link in &span.links {
                check(link.index, &link.prev_hash, &link.entry_hash, &mut prev)?;
            }
        }
    }
    Ok(())
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
                // Links accumulate oldest-first even though entries arrive newest-first,
                // so each new (older) entry is PREPENDED. A reader walks them in the same
                // direction they verify.
                None => WithheldSpan {
                    count: 1, from_index: e.index, to_index: e.index,
                    links: vec![WithheldLink {
                        index: e.index,
                        entry_hash: e.entry_hash.clone(),
                        prev_hash: e.prev_hash.clone(),
                    }],
                },
                Some(s) => {
                    let mut links = Vec::with_capacity(s.links.len() + 1);
                    links.push(WithheldLink {
                        index: e.index,
                        entry_hash: e.entry_hash.clone(),
                        prev_hash: e.prev_hash.clone(),
                    });
                    links.extend(s.links);
                    WithheldSpan { count: s.count + 1, from_index: e.index, to_index: s.to_index, links }
                }
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

    /// THE PRODUCTION PROPERTY (web4#807): a public reader can verify the hash chain
    /// THROUGH a withheld run, without learning what the run contained.
    ///
    /// This test replaces `the_compressed_record_makes_no_hash_linkage_claim_across_a_span`,
    /// which asserted the weaker ratchet rung and was written to FAIL when this landed —
    /// "that failure is the signal to update the renderer's wording in the same change, so
    /// claim and evidence move together instead of drifting apart again". It did, and they
    /// have: the record page's disclaimer is replaced in this same commit.
    ///
    /// Drives `public_record`, the windowed path the ENDPOINT returns — not
    /// `public_projection`. That distinction is the whole reason #802's compression was
    /// able to outrun the evidence unnoticed: the linkage test at the time exercised the
    /// per-entry representation, stayed green, and proved a property the served surface
    /// did not have.
    #[test]
    fn a_reader_can_verify_the_chain_through_a_withheld_run() {
        let chain = disclosed_then_withheld_run_then_disclosed();
        let (record, _scanned) = public_record(&chain, 10);
        assert_eq!(record.len(), 2, "fixture: the run compresses to one span");
        let span = record.iter().find(|d| d.index == 0).unwrap()
            .withheld_before.as_ref().expect("fixture: a span separates the two acts");
        assert_eq!((span.count, span.from_index, span.to_index), (3, 1, 3));
        assert_eq!(span.links.len(), 3, "every hidden entry contributes its link");

        verify_linkage(&record).expect("an untampered record verifies through the run");

        // …and the human presentation is unaffected: one span, not three rows.
        assert_eq!(span.count, 3, "the run still collapses to a single counted span");
    }

    /// THE ACCEPTANCE CRITERION, verbatim from #807: "Sabotaging a hash anywhere inside the
    /// withheld run causes public verification to fail."
    ///
    /// Every position in the run is sabotaged in turn, not just one — a verifier that
    /// checked only the boundary links would pass a single-position test and still let a
    /// server rewrite the middle of a run, which is precisely the attack the ordinal-only
    /// rung could not detect.
    #[test]
    fn sabotaging_any_hash_inside_the_run_is_detected() {
        let chain = disclosed_then_withheld_run_then_disclosed();
        for position in 0..3usize {
            let (mut record, _) = public_record(&chain, 10);
            let span = record.iter_mut().find(|d| d.index == 0).unwrap()
                .withheld_before.as_mut().unwrap();
            let sabotaged_index = span.links[position].index;
            span.links[position].entry_hash = "substituted-by-a-dishonest-server".to_string();
            let break_ = verify_linkage(&record)
                .expect_err(&format!("a substituted hash at run position {position} must be detected"));
            // The break is reported at the entry that FOLLOWS the tampered one, because that
            // is where the claim and the value first disagree — which is also the honest
            // thing to tell a reader: this link does not lead where it says.
            assert!(break_.at_index > sabotaged_index,
                "position {position}: break reported at {}, expected after the tampered {sabotaged_index}",
                break_.at_index);
        }
    }

    /// Silence is not a pass. A span carrying no link evidence — the pre-#807 wire shape,
    /// or a server that simply omits it — must be a verification FAILURE, not an absence of
    /// findings. Otherwise the weaker rung reads as the stronger one to any automated
    /// checker, which is the confusion #807 exists to prevent.
    #[test]
    fn a_span_with_no_link_evidence_fails_verification_rather_than_passing_quietly() {
        let chain = disclosed_then_withheld_run_then_disclosed();
        let (mut record, _) = public_record(&chain, 10);
        record.iter_mut().find(|d| d.index == 0).unwrap()
            .withheld_before.as_mut().unwrap().links.clear();
        let break_ = verify_linkage(&record).expect_err("an evidence-free span cannot verify");
        assert!(break_.found_prev.contains("no link evidence"), "{break_}");
    }

    /// The disclosure property, unchanged by #807 and worth re-pinning next to it: link
    /// evidence is hashes and indexes ONLY. Publishing more of a withheld act to make it
    /// verifiable would defeat the point of withholding it.
    #[test]
    fn link_evidence_discloses_nothing_about_the_hidden_acts() {
        let chain = disclosed_then_withheld_run_then_disclosed();
        let (record, _) = public_record(&chain, 10);
        let json = serde_json::to_string(&record).unwrap();
        assert!(!json.contains("a private post"),
            "the withheld body must not reach a public caller through link evidence: {json}");
        let span = record.iter().find(|d| d.index == 0).unwrap().withheld_before.as_ref().unwrap();
        for l in &span.links {
            assert!(!l.entry_hash.is_empty() && !l.prev_hash.is_empty());
        }
    }

    fn disclosed_then_withheld_run_then_disclosed() -> Vec<crate::ledger::LedgerEntry> {
        let genesis = |i: u64| entry(i, HubEvent::Genesis {
            hub_name: "chapter".into(),
            charter_hash: "c".into(),
            founding_sovereign_lct_id: Uuid::nil(),
            created_at: Utc.with_ymd_and_hms(2026, 8, 27, 12, 0, 0).unwrap(),
        });
        let private = |i: u64| entry(i, HubEvent::PostAdded {
            topic_id: Uuid::new_v4(),
            post_id: Uuid::new_v4(),
            body: "a private post".into(),
            posted_by: Uuid::new_v4(),
        });
        vec![genesis(0), private(1), private(2), private(3), genesis(4)]
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
