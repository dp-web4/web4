// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Hub law — the **society specialization** of the shared policy engine.
//!
//! The domain-agnostic engine (Law/Norm/Decision/Operator/Procedure/Condition/
//! R6Request/evaluate/hydrate mechanism + structural validation) was extracted
//! into the `web4-policy` crate (RFC #419 step-2 joint extraction). This module
//! is now the hub's specialization on top of it:
//!
//! - `Law` = [`web4_policy::Law`]`<`[`HubPolicy`]`>` — the generic engine carrying
//!   the hub's society policy (admission / delegation / ATP issuance), flattened
//!   into the same wire form as before (the extraction is byte-compatible with
//!   signed law already on disk).
//! - [`HubPolicy`] implements [`PolicyExtension`]: the society validation rules
//!   (role vocabulary, admission/delegation/ATP constraints) and the admission
//!   default-hydration (web4 #417), which the generic `Law::hydrate_defaults`
//!   delegates to.
//! - The generic engine types are re-exported so existing `crate::law::{Law, Norm,
//!   Decision, R6Request, …}` imports keep working unchanged.

use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use web4_policy::PolicyExtension;

// Re-export the generic engine surface so `crate::law::*` consumers are unchanged.
pub use web4_policy::{
    Condition, CustomPredicate, Decision, DecisionOutcome, EscalationTrigger, Norm, Operator,
    Procedure, R6Request, Response, ResponseRule,
};

/// The hub's law: the generic policy engine specialized with [`HubPolicy`].
pub type Law = web4_policy::Law<HubPolicy>;

/// Known SocietyRole names per web4-core. Used by the §2 validation rules
/// (delegation/escalation/admission/atp role typing). Kept as a free list (not
/// the `SocietyRole` enum directly) so law files can reference future custom
/// roles, while the canonical Web4 roles are enforced for role-typed fields.
pub const KNOWN_ROLES: &[&str] = &[
    "sovereign",
    "administrator",
    "treasurer",
    "archivist",
    "witness",
    "citizen",
    "applicant",
];

fn is_known_role(role: &str) -> bool {
    KNOWN_ROLES.contains(&role.to_lowercase().as_str())
}

/// The canonical **constellation session-capacity** role vocabulary — the
/// `role_lct` a constellation orchestrator (e.g. hestia, claude-code) acts under
/// for per-`(instance, role)` reputation (RFC #403 role dimension; #430 fold).
///
/// This is a **distinct namespace** from [`KNOWN_ROLES`] (the Web4 *society*
/// roles — sovereign/administrator/…): a society role types delegation/admission/
/// ATP authority, whereas a constellation role scopes an instance's reputation to
/// the capacity it is acting in. Both are role vocabularies; they do not overlap.
///
/// Published per thread `identity-p1-cospec` (HUB Concern 2): self-declared roles
/// fragment the fold exactly like `plugin_id` does one level up (`mesh-worker` vs
/// `mesh_worker`).
///
/// **This vocabulary is published, not enforced.** The hub reads `role_lct`
/// verbatim off the caller's R7 body and folds it unnormalized; it never calls
/// [`normalize_constellation_role`] or [`is_known_constellation_role`] on an
/// inbound value, and as of 2026-07-29 neither helper has a caller outside this
/// module's tests. A member that declares `role:constellation:mesh_worker` — or
/// any novel string — mints a distinct reputation subject and the hub does not
/// notice.
///
/// That is deliberate, per dp's ruling of 2026-07-28 (`git-manager-role` §8b:
/// the hub should resist feature creep beyond the core role of being a hub).
/// Gating a self-declaration is the member's half of the contract, at connect,
/// with the member's own vocabulary check; the hub's half is publishing a
/// canonical set to check against and carrying what it is given. What was wrong
/// was this doc comment previously asserting the member's half as an enforced
/// property — a contract with no construct behind it, which reads as a guarantee
/// to anyone consuming the fold. Use [`normalize_constellation_role`] to hold up
/// your end; nothing here will do it for you.
pub const KNOWN_CONSTELLATION_ROLES: &[&str] = &[
    "role:constellation:interactive-dev", // a human-driven session
    "role:constellation:mesh-worker",     // a hub-mesh-fired autonomous session
    "role:constellation:reviewer",        // a review/verify session
    "role:constellation:autonomous-timer", // a scheduled/cron session
    "role:constellation:member",          // the fail-closed default capacity
];

/// The fail-closed default constellation role: an unknown/unstated capacity folds
/// here rather than fragmenting reputation onto a freely-minted role subject.
/// Matches hestia's v1 `V1_CONSTELLATION_ROLE` placeholder.
pub const DEFAULT_CONSTELLATION_ROLE: &str = "role:constellation:member";

/// Whether `role` is a published constellation session-capacity role.
/// Case-sensitive: the vocabulary is canonical lowercase `role:constellation:*`.
pub fn is_known_constellation_role(role: &str) -> bool {
    KNOWN_CONSTELLATION_ROLES.contains(&role)
}

/// Validate a self-declared constellation role at connect, failing closed to
/// [`DEFAULT_CONSTELLATION_ROLE`] on any unpublished value.
///
/// This is the **member's** half of the HUB Concern 2 contract, offered by the
/// hub as a shared implementation: a member calls this with the role it declared
/// and stamps the returned canonical string as its `role_lct`. A member that
/// calls it cannot fragment the fold with a typo'd or novel capacity; a member
/// that does not is unaffected, because no hub path invokes this on inbound
/// values. See [`KNOWN_CONSTELLATION_ROLES`] for why the hub does not enforce it.
pub fn normalize_constellation_role(declared: &str) -> &'static str {
    KNOWN_CONSTELLATION_ROLES
        .iter()
        .find(|&&r| r == declared)
        .copied()
        .unwrap_or(DEFAULT_CONSTELLATION_ROLE)
}

/// Default admission repeat limit: denials before an applicant is auto-blocked.
pub const DEFAULT_ADMISSION_REPEAT_LIMIT: u32 = 3;
/// Default admission review limit: denial-review requests before the terminal
/// state (cleared only by an operator admission-reset).
pub const DEFAULT_ADMISSION_REVIEW_LIMIT: u32 = 1;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DelegationPolicy {
    pub max_depth: i64,
    #[serde(default)]
    pub requires_approval: bool,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub allowed_roles: Vec<String>,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct AdmissionPolicy {
    #[serde(default)]
    pub open: bool,
    #[serde(default)]
    pub requires_sponsor: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sponsor_role: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub min_trust_score: Option<f64>,
    /// Abuse-resistant repair path. After `repeat_limit` denials an applicant is
    /// auto-blocked (must request a review); the review path itself allows up to
    /// `review_limit` requests before a terminal state (operator reset only).
    /// Unset → defaults ([`DEFAULT_ADMISSION_REPEAT_LIMIT`] /
    /// [`DEFAULT_ADMISSION_REVIEW_LIMIT`]); operator changes are written here (law
    /// is the single inspectable source of truth), via a witnessed `LawAmended`.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub repeat_limit: Option<u32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub review_limit: Option<u32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

// ============================================================================
// F0.2 (R7b): sponsor evidence — the asserted-asker rule, in LAW
// ============================================================================

/// What the hub could establish about an applicant's claimed sponsor.
///
/// **Sprint F0.2 / PRD_HUB_V2_FEDERATED R7b.** The governing rule: *a witness
/// vouch counts only toward an identity resolved from the authoritative
/// record; a self-asserted binding collects no peer factors.* Generalizes the
/// Legion incident (a hostname-minted second identity out-polling the
/// canonical seat) from a roster filter into law.
///
/// The verdict deliberately **splits its failure exits**. A guard with one
/// failure exit either certifies a lie (treating "cannot check" as "checked
/// and passed") or becomes unsatisfiable (treating it as "checked and
/// failed"). So:
///
/// - [`SponsorVerdict::Refuted`] — the claim was checked and definitely fails.
/// - [`SponsorVerdict::Undecidable`] — the hub cannot establish it either way
///   from what it projects. Not a refutation, and never silently an approval.
///
/// Both block **auto-admission**; neither is a terminal exclusion. Which one
/// fired is carried to the operator, because "you vouched for yourself" and
/// "we cannot verify treasurer role" call for different human responses.
#[derive(Clone, Debug, PartialEq)]
pub enum SponsorVerdict {
    /// Law imposes no sponsor requirement — nothing to establish.
    NotRequired,
    /// Requirement met by an authoritatively-resolved sponsor.
    Satisfied { sponsor_lct_id: Uuid },
    /// Checked and definitely unmet.
    Refuted(SponsorRefusal),
    /// Not establishable from what the hub projects.
    Undecidable(SponsorUnknown),
}

/// Definite failures — the claim was evaluated and does not hold.
#[derive(Clone, Debug, PartialEq)]
pub enum SponsorRefusal {
    /// Law requires a sponsor; the applicant named none.
    Missing,
    /// **The asserted-asker case.** The applicant named itself. An identity
    /// cannot be its own peer factor at any strength.
    SelfSponsored,
    /// The named sponsor is not resolvable from the authoritative record —
    /// not a member, or a member with no key-bound identity pinned. A name in
    /// a payload is an assertion, not evidence.
    NotResolved { named: Uuid },
    /// The sponsor resolved, but its trust in the sponsoring role is below the
    /// bar law sets.
    TrustBelowBar { score: f64, required: f64 },
}

/// Conditions the hub cannot decide from its projection.
#[derive(Clone, Debug, PartialEq)]
pub enum SponsorUnknown {
    /// **The sponsoring ACT is not witnessed.** The named party resolves to a
    /// key-bound member — but that proves the member *exists*, not that they
    /// *sponsored anyone*. The sponsorship relation as submitted is a field
    /// the applicant typed, and member ids are not secret by any route (the
    /// public identity file publishes the founding sovereign's; the presence
    /// roster returns every member's; every member already knows the others').
    /// So an applicant could name any member and collect a peer factor they
    /// never granted — the asserted-asker hole this rule is named after,
    /// one level out.
    ///
    /// Until the hub projects a witnessed vouch event, this is **undecidable**
    /// and routes to operator review. It is not a refutation: the sponsorship
    /// may well be real, and a human can confirm it. When a vouch event lands,
    /// [`SponsorVerdict::Satisfied`] becomes reachable cleanly.
    VouchNotAttested { named: Uuid },
    /// Law names a sponsor role other than membership itself. The hub does not
    /// project role assignments today (`RoleAssigned` is witnessed, not
    /// folded), so holding that role can be neither confirmed nor refuted.
    RoleNotProjected { required_role: String },
    /// Law sets a trust bar, but the sponsor has no observations to read —
    /// e.g. while the reputation seam is in `classify_only` (F0.1), tensors
    /// are deliberately empty. Absence of a record is not a low score.
    NoTrustRecord { required: f64 },
}

/// Facts the caller resolved from the authoritative record, handed to the pure
/// evaluation below. Keeping the projection lookups on the caller's side keeps
/// LAW transport-free and directly testable.
#[derive(Clone, Copy, Debug)]
pub struct SponsorFacts {
    /// Who is applying.
    pub applicant_lct_id: Uuid,
    /// Who the applicant claims sponsors them, if anyone.
    pub claimed_sponsor: Option<Uuid>,
    /// Is that claimed sponsor a member **with a key-bound identity pinned**
    /// in the authoritative record? (Membership alone is not enough — R7b
    /// wants a witnessed, key-bound identity, per the RWOA `W` clause.)
    ///
    /// Note this establishes only that the *identity exists*. Whether that
    /// member performed a sponsoring **act** is a separate fact —
    /// `vouch_is_attested` below.
    pub sponsor_is_resolved_member: bool,
    /// Did the hub witness the claimed sponsor actually **vouch for this
    /// applicant**? Identity existence is not evidence of an act, so this is
    /// what `Satisfied` genuinely rests on. Today the hub projects no vouch
    /// event, so callers pass `false` and every named sponsor is undecidable
    /// (operator review) — deliberately, rather than crediting a peer factor
    /// nobody granted.
    pub vouch_is_attested: bool,
    /// The sponsor's aggregate trust in the sponsoring role, if any
    /// observations exist. `None` = no record, which is [`SponsorUnknown`],
    /// never a zero.
    pub sponsor_trust: Option<f64>,
}

/// The role name that membership itself confers. A `sponsor_role` naming this
/// is checkable from the member projection; any other role is not (yet).
pub const MEMBERSHIP_ROLE: &str = "citizen";

/// Evaluate an applicant's sponsor claim against law. Pure: no I/O, no
/// projection access — see [`SponsorFacts`].
pub fn evaluate_sponsor(
    policy: Option<&AdmissionPolicy>,
    facts: SponsorFacts,
) -> SponsorVerdict {
    let Some(p) = policy else {
        return SponsorVerdict::NotRequired;
    };
    // A trust bar is meaningful only against a sponsor, so it rides the same
    // requirement. Law that sets a bar without requiring a sponsor states a
    // requirement it cannot apply; treat it as requiring one.
    if !p.requires_sponsor && p.min_trust_score.is_none() {
        return SponsorVerdict::NotRequired;
    }
    let Some(sponsor) = facts.claimed_sponsor else {
        return SponsorVerdict::Refuted(SponsorRefusal::Missing);
    };
    // R7b, the core rule: an asserted asker collects no peer factor. Checked
    // FIRST, so self-sponsorship can never be laundered through any later
    // clause.
    if sponsor == facts.applicant_lct_id {
        return SponsorVerdict::Refuted(SponsorRefusal::SelfSponsored);
    }
    if !facts.sponsor_is_resolved_member {
        return SponsorVerdict::Refuted(SponsorRefusal::NotResolved { named: sponsor });
    }
    // Existence is not consent. The applicant typed this relation; only a
    // witnessed sponsoring act can establish it, and member ids are public
    // enough that anyone could name anyone. Undecidable, not refuted — the
    // claim may be true, and an operator can confirm what the hub cannot.
    if !facts.vouch_is_attested {
        return SponsorVerdict::Undecidable(SponsorUnknown::VouchNotAttested { named: sponsor });
    }
    // A sponsor role beyond membership is unverifiable from the projection.
    if let Some(role) = &p.sponsor_role {
        if !role.eq_ignore_ascii_case(MEMBERSHIP_ROLE) {
            return SponsorVerdict::Undecidable(SponsorUnknown::RoleNotProjected {
                required_role: role.clone(),
            });
        }
    }
    if let Some(required) = p.min_trust_score {
        return match facts.sponsor_trust {
            None => SponsorVerdict::Undecidable(SponsorUnknown::NoTrustRecord { required }),
            Some(score) if score < required => {
                SponsorVerdict::Refuted(SponsorRefusal::TrustBelowBar { score, required })
            }
            Some(_) => SponsorVerdict::Satisfied { sponsor_lct_id: sponsor },
        };
    }
    SponsorVerdict::Satisfied { sponsor_lct_id: sponsor }
}

impl SponsorVerdict {
    /// May this verdict auto-admit? Only an established one may.
    pub fn may_auto_admit(&self) -> bool {
        matches!(self, SponsorVerdict::NotRequired | SponsorVerdict::Satisfied { .. })
    }

    /// Operator-facing reason, recorded on the queued request so a human sees
    /// **which exit fired**.
    pub fn reason(&self) -> Option<String> {
        match self {
            SponsorVerdict::NotRequired | SponsorVerdict::Satisfied { .. } => None,
            SponsorVerdict::Refuted(r) => Some(match r {
                SponsorRefusal::Missing =>
                    "hub law requires a sponsor; none was named".to_string(),
                SponsorRefusal::SelfSponsored =>
                    "applicant named itself as sponsor — a self-asserted identity \
                     collects no peer factors".to_string(),
                SponsorRefusal::NotResolved { named } => format!(
                    "named sponsor {named} is not a key-bound member of this society"),
                SponsorRefusal::TrustBelowBar { score, required } => format!(
                    "sponsor trust {score:.3} is below the required {required:.3}"),
            }),
            SponsorVerdict::Undecidable(u) => Some(match u {
                SponsorUnknown::VouchNotAttested { named } => format!(
                    "sponsor {named} is a member, but no witnessed vouch for this \
                     applicant exists — identity existence is not evidence of a \
                     sponsoring act; operator review"),
                SponsorUnknown::RoleNotProjected { required_role } => format!(
                    "cannot verify the sponsor holds role '{required_role}' — role \
                     assignments are witnessed but not projected; operator review"),
                SponsorUnknown::NoTrustRecord { required } => format!(
                    "sponsor has no trust observations to compare against the \
                     required {required:.3}; operator review"),
            }),
        }
    }

    /// Short token for logs/telemetry — which exit fired.
    pub fn token(&self) -> &'static str {
        match self {
            SponsorVerdict::NotRequired => "not_required",
            SponsorVerdict::Satisfied { .. } => "satisfied",
            SponsorVerdict::Refuted(SponsorRefusal::Missing) => "refuted_missing",
            SponsorVerdict::Refuted(SponsorRefusal::SelfSponsored) => "refuted_self_sponsored",
            SponsorVerdict::Refuted(SponsorRefusal::NotResolved { .. }) => "refuted_not_resolved",
            SponsorVerdict::Refuted(SponsorRefusal::TrustBelowBar { .. }) => "refuted_trust_below_bar",
            SponsorVerdict::Undecidable(SponsorUnknown::VouchNotAttested { .. }) => "undecidable_vouch_not_attested",
            SponsorVerdict::Undecidable(SponsorUnknown::RoleNotProjected { .. }) => "undecidable_role",
            SponsorVerdict::Undecidable(SponsorUnknown::NoTrustRecord { .. }) => "undecidable_trust",
        }
    }
}

/// Compose the sponsor verdict with the norms-gate decision on the ratified
/// **strictest-wins** lattice (Family 8): the sponsor check may only *tighten*
/// the outcome, never loosen it. An unmet sponsor requirement turns an
/// auto-admit into operator review; it cannot rescue a law-denied applicant,
/// and it cannot downgrade an escalation.
pub fn tighten_with_sponsor(norms: Decision, verdict: &SponsorVerdict) -> Decision {
    if verdict.may_auto_admit() {
        return norms;
    }
    match norms {
        Decision::Allow | Decision::Warn => Decision::Escalate,
        other => other,
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AtpIssuancePolicy {
    pub mint_authority: String,
    pub max_mint_per_cycle: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub distribution: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

/// One `reputation_emit` rule — "this emitter may record reputation deltas for
/// this subject-pattern." Co-spec'd with Legion on thread `repemit-1`
/// (`shared-context/forum/legion-to-hub-reputation-emit-grammar-cospec-2026-07-04.md`
/// + `…grammar-confirmed…`). v1 authority hinge, two pins:
///
/// - **`emitter`** is matched against the **authenticated channel identity** of the
///   caller that sealed the emit (its pinned-key LCT id), NEVER a self-declared
///   payload field — Pin #1 (the eval, [`HubLawExt::reputation_emit_decision`], is
///   handed the authenticated caller, not a delta field).
/// - **`subject`** is matched against the delta's `role_lct`:
///   - `subject: <role>` matches iff `delta.role_lct == <role>` (the only role
///     signal the hub holds in v1).
///   - `subject: constellation:<emitter>` is the **v2** attestation pattern
///     ("subject is a member of emitter's constellation"). It is **inert in v1** —
///     it can't be evaluated until hestia's constellation-publish lands, so it
///     never matches and fails closed. Warned at law-load (Pin #2) so a v2 rule
///     staged early isn't a silent no-op.
///
/// Ordered by `priority` (highest wins, ties → first); no matching rule ⇒
/// fail-closed deny.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ReputationEmitRule {
    /// The authenticated channel identity permitted to emit (Pin #1). Matched
    /// against the caller's pinned-key LCT id, not a payload field.
    pub emitter: String,
    /// Subject pattern — `<role>` (matches `delta.role_lct`) or the v2-inert
    /// `constellation:<emitter>` token.
    pub subject: String,
    /// Reuses the shared [`Decision`] vocabulary (`allow` / `warn` / `deny` /
    /// `escalate`) — same as norms.
    pub decision: Decision,
    /// Highest priority among matching rules wins (ties → first).
    pub priority: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

/// How authorized reputation deltas are APPLIED — the staged seam-opening
/// (Sprint F0.1 / PRD R7a, decision recorded in `SPRINTS.md` 2026-08-13).
///
/// - `classify_only` (fail-closed default): authorized deltas are witnessed to
///   the ledger with their conduct-vs-infra class, visible on the operator
///   surface, and applied to **no** tensor. The observation-window mode.
/// - `apply`: authorized `Conduct`-class deltas fold into `(subject, role)`
///   tensors. `Infra` and `Unclassified` deltas are recorded, never applied,
///   in **every** mode.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "snake_case")]
pub enum EmitMode {
    #[default]
    ClassifyOnly,
    Apply,
}

/// The hub's `reputation_emit` law section — who, other than the Sovereign, may
/// record reputation deltas, and for which subject-roles. Absent section ⇒ the
/// emit path is fully dark (Sovereign-only, the pre-wiring behavior).
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct ReputationEmitPolicy {
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub rules: Vec<ReputationEmitRule>,
    /// Staged application mode (F0.1). Absent ⇒ `classify_only` — a law that
    /// opens the seam without stating a mode observes before it actuates.
    #[serde(default)]
    pub mode: EmitMode,
}

/// A `subject` token that references `constellation:<emitter>` — the v2 attestation
/// pattern, inert in v1 (see [`ReputationEmitRule`]). Discriminated by the
/// `constellation:` prefix; note `role:constellation:member` (a v1 `role_lct`
/// value that merely *contains* the word) starts with `role:` and is NOT inert.
pub fn subject_is_v2_inert(subject: &str) -> bool {
    subject.starts_with("constellation:")
}

/// Resolved outcome of a `reputation_emit` evaluation: the winning rule's
/// [`Decision`] plus its description (for operator-visible logging), or a
/// fail-closed [`Decision::Deny`] with `matched_rule = None` when nothing matched.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ReputationEmitOutcome {
    pub decision: Decision,
    pub matched_rule: Option<String>,
}

/// The hub's society policy — the [`PolicyExtension`] flattened into [`Law`].
///
/// `#[serde(flatten)]` in `web4_policy::Law` merges these at the top level, so the
/// law's wire form is unchanged: `{version, norms, …, delegation, admission,
/// atp_issuance}`.
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct HubPolicy {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delegation: Option<DelegationPolicy>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub admission: Option<AdmissionPolicy>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub atp_issuance: Option<AtpIssuancePolicy>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reputation_emit: Option<ReputationEmitPolicy>,
}

impl PolicyExtension for HubPolicy {
    /// Society validation rules 6-10 (hub-law-schema §2): delegation depth +
    /// roles, escalation target role, admission sponsor role + trust range, ATP
    /// mint authority role + cap. `law` is passed so the escalation targets
    /// (which live on the generic engine) validate against the hub role vocabulary.
    fn validate(&self, law: &Law) -> Result<()> {
        // Rule 6 + 7: delegation depth >= 0; allowed_roles are known roles.
        if let Some(d) = &self.delegation {
            if d.max_depth < 0 {
                return Err(anyhow!(
                    "delegation.max_depth must be >= 0 (got {})",
                    d.max_depth
                ));
            }
            for role in &d.allowed_roles {
                if !is_known_role(role) {
                    return Err(anyhow!(
                        "delegation.allowed_roles contains unknown role '{}' (known: {})",
                        role,
                        KNOWN_ROLES.join(", ")
                    ));
                }
            }
        }

        // Rule 8 (society half): escalation[].escalate_to is a valid role.
        for esc in &law.escalation {
            if !is_known_role(&esc.escalate_to) {
                return Err(anyhow!(
                    "escalation[].escalate_to '{}' is not a known role (known: {})",
                    esc.escalate_to,
                    KNOWN_ROLES.join(", ")
                ));
            }
        }

        // Rule 9: admission.sponsor_role valid (if set); min_trust_score in [0,1].
        if let Some(a) = &self.admission {
            if let Some(role) = &a.sponsor_role {
                if !is_known_role(role) {
                    return Err(anyhow!(
                        "admission.sponsor_role '{}' is not a known role (known: {})",
                        role,
                        KNOWN_ROLES.join(", ")
                    ));
                }
            }
            if let Some(score) = a.min_trust_score {
                if !(0.0..=1.0).contains(&score) {
                    return Err(anyhow!(
                        "admission.min_trust_score {} out of range [0, 1]",
                        score
                    ));
                }
            }
        }

        // Rule 10: atp_issuance.mint_authority valid role; max_mint_per_cycle >= 0.
        if let Some(a) = &self.atp_issuance {
            if !is_known_role(&a.mint_authority) {
                return Err(anyhow!(
                    "atp_issuance.mint_authority '{}' is not a known role (known: {})",
                    a.mint_authority,
                    KNOWN_ROLES.join(", ")
                ));
            }
            if a.max_mint_per_cycle < 0 {
                return Err(anyhow!(
                    "atp_issuance.max_mint_per_cycle must be >= 0 (got {})",
                    a.max_mint_per_cycle
                ));
            }
        }

        // Rule 11 (thread repemit-1): reputation_emit rules must carry a non-empty
        // emitter + subject. Pin #2 — a rule whose subject is a v2-inert
        // `constellation:<emitter>` token is ACCEPTED (stays fail-closed at eval),
        // but warned here at law-load so a v2 rule staged before the
        // constellation-publish lands isn't a silent no-op. validate() is the parse
        // choke point (`parse_and_validate`), so this warns exactly at load.
        if let Some(re) = &self.reputation_emit {
            for (i, rule) in re.rules.iter().enumerate() {
                if rule.emitter.trim().is_empty() {
                    return Err(anyhow!("reputation_emit.rules[{}].emitter must not be empty", i));
                }
                if rule.subject.trim().is_empty() {
                    return Err(anyhow!("reputation_emit.rules[{}].subject must not be empty", i));
                }
                if subject_is_v2_inert(&rule.subject) {
                    tracing::warn!(
                        "reputation_emit.rules[{}] uses the v2 token `subject: {}` — inert in v1 \
                         (never matches, fails closed) until hestia constellation-publish lands",
                        i,
                        rule.subject
                    );
                }
            }
        }

        Ok(())
    }

    /// Hydrate the hub's law-driven code defaults (web4 #417): the admission
    /// repeat/review limits. SINGLE MAINTENANCE POINT — add new hub defaults here.
    /// Returns true iff anything was filled (so the caller witnesses only on change).
    fn hydrate_defaults(&mut self) -> bool {
        let mut changed = false;
        let adm = self.admission.get_or_insert_with(|| {
            changed = true;
            Default::default()
        });
        if adm.repeat_limit.is_none() {
            adm.repeat_limit = Some(DEFAULT_ADMISSION_REPEAT_LIMIT);
            changed = true;
        }
        if adm.review_limit.is_none() {
            adm.review_limit = Some(DEFAULT_ADMISSION_REVIEW_LIMIT);
            changed = true;
        }
        // ── future hub law-driven defaults: add `get_or_insert`/default lines here ──
        changed
    }
}

/// Hub-specific accessors on [`Law`]. `Law` is a foreign type alias
/// (`web4_policy::Law<HubPolicy>`), so these live on an extension trait rather
/// than an inherent impl. Bring into scope with `use crate::law::HubLawExt;`.
/// Action strings the gate evaluates that are **not** `HubEvent::kind()` values.
///
/// The join gate prices a request *before* any event exists, so it synthesises an
/// action name (`rest.rs` `submit_join`, `admin.rs`). `member_join_request` is
/// therefore a real, load-bearing action that no event kind will ever match — and
/// it appears in the shipped starter law. Any guard over norm actions has to know
/// that, or it rejects the template the hub ships with.
pub const KNOWN_SYNTHETIC_ACTIONS: &[&str] = &["member_join_request"];

/// Prefix for the read-gate action family (`read:<tool>`, `rest.rs read_decision`).
/// Open-ended by design — the tool name is not enumerable — so membership is a
/// prefix rule rather than a list.
pub const READ_ACTION_PREFIX: &str = "read:";

/// Is `action` a value the gate can ever actually see?
pub fn is_known_law_action(action: &str) -> bool {
    action.starts_with(READ_ACTION_PREFIX)
        || KNOWN_SYNTHETIC_ACTIONS.contains(&action)
        || crate::events::HubEvent::ALL_EVENT_KINDS.contains(&action)
}

/// A norm that tests `r6.request.action` for equality against a value the gate
/// can never produce.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct UnknownActionNorm {
    pub norm_id: String,
    pub value: String,
}

pub trait HubLawExt {
    /// Effective admission repeat limit — the law value, or the code default.
    fn admission_repeat_limit(&self) -> u32;
    /// Effective admission review limit — the law value, or the code default.
    fn admission_review_limit(&self) -> u32;
    /// Evaluate the `reputation_emit` section for an emit sealed by `emitter` (the
    /// **authenticated** caller LCT id — Pin #1) carrying a delta whose role is
    /// `delta_role_lct`. Highest-priority matching rule wins (ties → first); no
    /// match — or no section at all — ⇒ fail-closed [`Decision::Deny`]. The
    /// Sovereign path is not routed through here (Sovereign may always record); this
    /// governs only non-Sovereign emitters.
    fn reputation_emit_decision(&self, emitter: &str, delta_role_lct: &str) -> ReputationEmitOutcome;

    /// F0.1 (R7a): the staged application mode of the `reputation_emit`
    /// section. Fail-closed: no section ⇒ `ClassifyOnly` — with the seam dark
    /// or unstated, nothing applies to tensors.
    fn reputation_emit_mode(&self) -> EmitMode;

    /// Norms that test `r6.request.action` for equality against a value the gate
    /// can never produce.
    ///
    /// Such a norm is **worse than absent**: it reads as a restriction, never
    /// fires, and leaves the act on whatever the default is. Nothing else in the
    /// stack can tell the two apart, because an unmatched norm is not an error —
    /// it is an allow. `HUB-LAW.md` shipped an example naming `assign_role` when
    /// the gate emits `role_assigned`, which is exactly this failure with a
    /// documentation source.
    ///
    /// Only equality-shaped tests are checked (`==`, `in`). `!=` is deliberately
    /// exempt: the starter law's `DEFAULT-ALLOW` matches everything by asserting
    /// `action != __never_match__`, where the value is *meant* to be unmatchable.
    fn unknown_action_norms(&self) -> Vec<UnknownActionNorm>;
}

impl HubLawExt for Law {
    fn admission_repeat_limit(&self) -> u32 {
        self.ext
            .admission
            .as_ref()
            .and_then(|a| a.repeat_limit)
            .unwrap_or(DEFAULT_ADMISSION_REPEAT_LIMIT)
    }
    fn admission_review_limit(&self) -> u32 {
        self.ext
            .admission
            .as_ref()
            .and_then(|a| a.review_limit)
            .unwrap_or(DEFAULT_ADMISSION_REVIEW_LIMIT)
    }

    fn unknown_action_norms(&self) -> Vec<UnknownActionNorm> {
        use web4_policy::Operator;
        let mut out = Vec::new();
        for norm in &self.norms {
            if norm.selector != "r6.request.action" {
                continue;
            }
            // Equality-shaped only. `!=` is how DEFAULT-ALLOW matches everything
            // (`action != __never_match__`), where an unmatchable value is the
            // point; ordering operators over an action string are meaningless but
            // are not this guard's business to adjudicate.
            let values: Vec<String> = match norm.operator {
                Operator::Eq => norm.value.as_str().map(|s| vec![s.to_string()]).unwrap_or_default(),
                Operator::In => norm
                    .value
                    .as_sequence()
                    .map(|seq| seq.iter().filter_map(|v| v.as_str().map(str::to_string)).collect())
                    .unwrap_or_default(),
                _ => continue,
            };
            for v in values {
                if !is_known_law_action(&v) {
                    out.push(UnknownActionNorm { norm_id: norm.id.clone(), value: v });
                }
            }
        }
        out
    }

    fn reputation_emit_mode(&self) -> EmitMode {
        self.ext.reputation_emit.as_ref().map(|re| re.mode).unwrap_or_default()
    }

    fn reputation_emit_decision(&self, emitter: &str, delta_role_lct: &str) -> ReputationEmitOutcome {
        let deny = || ReputationEmitOutcome { decision: Decision::Deny, matched_rule: None };
        let Some(re) = self.ext.reputation_emit.as_ref() else {
            // No section ⇒ the emit path is dark: nothing but the Sovereign records.
            return deny();
        };
        // Highest priority among matching rules wins; ties → first in file order
        // (mirrors the norm engine's `priority > current` strict comparison).
        let mut winner: Option<&ReputationEmitRule> = None;
        for rule in &re.rules {
            // Pin #1: emitter is the authenticated caller, matched verbatim.
            if rule.emitter != emitter {
                continue;
            }
            // v2-inert `constellation:<emitter>` tokens never match in v1 (fail closed).
            if subject_is_v2_inert(&rule.subject) {
                continue;
            }
            // v1 `subject: <role>` matches iff it equals the delta's role_lct.
            if rule.subject != delta_role_lct {
                continue;
            }
            match winner {
                Some(w) if rule.priority > w.priority => winner = Some(rule),
                None => winner = Some(rule),
                _ => {}
            }
        }
        match winner {
            Some(rule) => ReputationEmitOutcome {
                decision: rule.decision.clone(),
                matched_rule: rule.description.clone().or_else(|| Some(rule.emitter.clone())),
            },
            None => deny(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn constellation_roles_are_a_separate_namespace_from_society_roles() {
        // The two vocabularies must not overlap: a society role is never a valid
        // constellation role and vice-versa (they type different things).
        for r in KNOWN_CONSTELLATION_ROLES {
            assert!(!is_known_role(r), "'{r}' leaked into the society role set");
        }
        for r in KNOWN_ROLES {
            assert!(
                !is_known_constellation_role(r),
                "society role '{r}' is not a constellation role"
            );
        }
    }

    #[test]
    fn unknown_constellation_role_fails_closed_to_default() {
        // The HUB Concern 2 contract: typos/novel capacities do NOT fragment the
        // fold — they collapse to the published default.
        assert_eq!(
            normalize_constellation_role("role:constellation:mesh_worker"), // underscore typo
            DEFAULT_CONSTELLATION_ROLE
        );
        assert_eq!(
            normalize_constellation_role("role:constellation:whatever-i-want"),
            DEFAULT_CONSTELLATION_ROLE
        );
        // A published capacity passes through unchanged.
        assert_eq!(
            normalize_constellation_role("role:constellation:mesh-worker"),
            "role:constellation:mesh-worker"
        );
        assert!(is_known_constellation_role(DEFAULT_CONSTELLATION_ROLE));
    }

    #[test]
    fn hub_law_parses_response_rules_and_stays_inert() {
        // W4IP N3 Phase 2: the hub's Law<HubPolicy> parses the `responses:` key
        // (canonical example from hub-law-schema.md "Response vocabulary"),
        // validates it, and the R6 gate remains blind to it (parse-don't-enact).
        let yaml = r#"
version: "1.0.0"
responses:
  - id: QUARANTINE-ON-AGENCY-OVERRIDE
    selector: reputation.delta.category
    operator: "=="
    value: coercive_extractive
    response: quarantine
    priority: 10
    description: "Witnessed agency-override delta -> reversible containment pending adjudication"
"#;
        let law = Law::parse_and_validate(yaml).expect("hub law with responses parses");
        assert_eq!(law.responses.len(), 1);
        assert_eq!(law.responses[0].response, Response::Quarantine);
        assert!(!law.responses[0].response.is_kinetic());
        // The society gate is unaffected: no norms -> default allow, and the
        // response rule is invisible to R6 evaluation.
        let out = law.evaluate_outcome(&R6Request {
            role: "citizen".into(),
            action: "member_added".into(),
            ..Default::default()
        });
        assert_eq!(out.decision, Decision::Allow);
        assert_eq!(out.winning_norm, None);
    }

    /// The canonical example from hub-law-schema.md §1.
    const EXAMPLE_LAW: &str = r#"
version: "1.0.0"

norms:
  - id: ATP-LIMIT
    selector: r6.resource.atp
    operator: "<="
    value: 100
    decision: deny
    priority: 10
    description: "No single action may consume more than 100 ATP"

  - id: ADMIN-ONLY-ROLES
    selector: r6.request.action
    operator: "=="
    value: assign_role
    decision: escalate
    priority: 20
    description: "Role assignment requires Sovereign or Administrator"

procedures:
  - id: WITNESS-3
    requires_witnesses: 3
    applies_to: "consequential_actions"
    description: "Consequential actions require 3 independent witnesses"

  - id: ADMISSION-VOTE
    requires_quorum: 3
    applies_to: "member_join"
    description: "New member admission requires 3 existing members to approve"

delegation:
  max_depth: 2
  requires_approval: true
  allowed_roles:
    - administrator
    - archivist
    - witness

escalation:
  - condition: "r6.resource.atp > 50"
    escalate_to: sovereign
    description: "High-ATP actions escalate to Sovereign"

  - condition: "r6.request.action == 'amend_charter'"
    escalate_to: sovereign
    description: "Charter amendments always go to Sovereign"

admission:
  open: false
  requires_sponsor: true
  sponsor_role: citizen
  min_trust_score: 0.3
  description: "Closed admission — existing citizen must sponsor"

atp_issuance:
  mint_authority: treasurer
  max_mint_per_cycle: 1000
  distribution: proportional_to_contribution
  description: "Treasurer mints up to 1000 ATP per cycle"
"#;

    #[tokio::test]
    async fn canonical_example_parses_and_validates() {
        let law = Law::parse_and_validate(EXAMPLE_LAW)
            .expect("canonical example from schema doc must parse + validate");
        assert_eq!(law.version, "1.0.0");
        assert_eq!(law.norms.len(), 2);
        assert_eq!(law.procedures.len(), 2);
        assert_eq!(law.escalation.len(), 2);
        assert!(law.ext.delegation.is_some());
        assert!(law.ext.admission.is_some());
        assert!(law.ext.atp_issuance.is_some());
    }

    #[tokio::test]
    async fn round_trip_yaml() {
        let original = Law::from_yaml(EXAMPLE_LAW).unwrap();
        let yaml = original.to_yaml().unwrap();
        let reparsed = Law::from_yaml(&yaml).unwrap();
        assert_eq!(reparsed.version, original.version);
        assert_eq!(reparsed.norms.len(), original.norms.len());
        assert_eq!(reparsed.procedures.len(), original.procedures.len());
    }

    #[tokio::test]
    async fn empty_version_rejected() {
        let yaml = r#"
version: ""
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("version"));
    }

    #[tokio::test]
    async fn bad_semver_rejected() {
        let yaml = r#"
version: "not-a-semver"
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("semver"));
    }

    #[tokio::test]
    async fn duplicate_norm_id_rejected() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: SAME
    selector: r6.resource.atp
    operator: "<="
    value: 100
    decision: deny
  - id: SAME
    selector: r6.request.action
    operator: "=="
    value: foo
    decision: allow
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("duplicate norm id"));
    }

    #[tokio::test]
    async fn unknown_role_in_delegation_rejected() {
        let yaml = r#"
version: "1.0.0"
delegation:
  max_depth: 1
  allowed_roles:
    - bogus_role
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("unknown role 'bogus_role'"));
    }

    #[tokio::test]
    async fn negative_max_depth_rejected() {
        let yaml = r#"
version: "1.0.0"
delegation:
  max_depth: -1
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn unknown_role_in_escalation_rejected() {
        let yaml = r#"
version: "1.0.0"
escalation:
  - condition: "x > 1"
    escalate_to: not_a_role
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn unknown_role_in_atp_issuance_rejected() {
        let yaml = r#"
version: "1.0.0"
atp_issuance:
  mint_authority: bogus
  max_mint_per_cycle: 100
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn min_trust_out_of_range_rejected() {
        let yaml = r#"
version: "1.0.0"
admission:
  min_trust_score: 1.5
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("min_trust_score"));
    }

    #[tokio::test]
    async fn bad_operator_rejected_during_parse() {
        // Operator is an enum; serde rejects unknown variants at parse time.
        let yaml = r#"
version: "1.0.0"
norms:
  - id: X
    selector: a.b
    operator: "===="
    value: 1
    decision: deny
"#;
        let result = Law::from_yaml(yaml);
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn bad_decision_rejected_during_parse() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: X
    selector: a.b
    operator: "=="
    value: 1
    decision: maybe
"#;
        let result = Law::from_yaml(yaml);
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn minimal_law_validates() {
        let yaml = r#"
version: "0.1.0"
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        assert_eq!(law.norms.len(), 0);
        assert!(law.ext.delegation.is_none());
    }

    #[tokio::test]
    async fn duplicate_procedure_id_rejected() {
        let yaml = r#"
version: "1.0.0"
procedures:
  - id: P1
    requires_witnesses: 3
  - id: P1
    requires_quorum: 5
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("duplicate procedure id"));
    }

    #[tokio::test]
    async fn role_names_are_case_insensitive() {
        let yaml = r#"
version: "1.0.0"
delegation:
  max_depth: 1
  allowed_roles:
    - Sovereign
    - ADMINISTRATOR
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        assert_eq!(law.ext.delegation.as_ref().unwrap().allowed_roles.len(), 2);
    }

    // ----- Evaluator tests (V2-8 Step 3) -----

    fn request_with(role: &str, action: &str) -> R6Request {
        R6Request {
            role: role.into(),
            action: action.into(),
            payload: serde_yaml::Value::Mapping(Default::default()),
            resource: Default::default(),
        }
    }

    #[tokio::test]
    async fn no_norms_defaults_to_allow() {
        let law = Law::parse_and_validate(r#"version: "1.0.0""#).unwrap();
        let decision = law.evaluate(&request_with("citizen", "add_member"));
        assert_eq!(decision, Decision::Allow);
    }

    #[tokio::test]
    async fn atp_limit_denies_when_exceeded() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: ATP-LIMIT
    selector: r6.resource.atp
    operator: ">"
    value: 100
    decision: deny
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        let mut req = request_with("citizen", "expensive_action");
        req.resource.insert("atp".into(), serde_yaml::Value::Number(150.into()));
        assert_eq!(law.evaluate(&req), Decision::Deny);
    }

    #[tokio::test]
    async fn atp_limit_allows_when_under() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: ATP-LIMIT
    selector: r6.resource.atp
    operator: ">"
    value: 100
    decision: deny
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        let mut req = request_with("citizen", "cheap_action");
        req.resource.insert("atp".into(), serde_yaml::Value::Number(50.into()));
        assert_eq!(law.evaluate(&req), Decision::Allow);
    }

    #[tokio::test]
    async fn action_match_triggers_escalate() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: ADMIN-ONLY-ROLES
    selector: r6.request.action
    operator: "=="
    value: assign_role
    decision: escalate
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        assert_eq!(law.evaluate(&request_with("citizen", "assign_role")), Decision::Escalate);
        assert_eq!(law.evaluate(&request_with("citizen", "add_member")), Decision::Allow);
    }

    #[tokio::test]
    async fn higher_priority_norm_wins() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: BROAD-ALLOW
    selector: r6.request.action
    operator: "!="
    value: never_match
    decision: allow
    priority: 1
  - id: SPECIFIC-DENY
    selector: r6.request.action
    operator: "=="
    value: sensitive_op
    decision: deny
    priority: 10
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        let req = request_with("citizen", "sensitive_op");
        // Both fire; higher priority deny wins
        assert_eq!(law.evaluate(&req), Decision::Deny);
    }

    #[tokio::test]
    async fn role_selector_works() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: TREASURER-ONLY
    selector: r6.role
    operator: "!="
    value: treasurer
    decision: deny
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        assert_eq!(law.evaluate(&request_with("citizen", "mint_atp")), Decision::Deny);
        assert_eq!(law.evaluate(&request_with("treasurer", "mint_atp")), Decision::Allow);
    }

    #[tokio::test]
    async fn in_operator_works() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: ALLOWED-ACTIONS
    selector: r6.request.action
    operator: "in"
    value: [read, query, list]
    decision: allow
  - id: DENY-DEFAULT
    selector: r6.request.action
    operator: "not_in"
    value: [read, query, list]
    decision: deny
    priority: 1
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        assert_eq!(law.evaluate(&request_with("citizen", "read")), Decision::Allow);
        assert_eq!(law.evaluate(&request_with("citizen", "write")), Decision::Deny);
    }

    #[tokio::test]
    async fn payload_dotpath_selector_resolves() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: BLOCK-PROTECTED
    selector: r6.request.payload.target_role
    operator: "=="
    value: sovereign
    decision: deny
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        let mut payload = serde_yaml::Mapping::new();
        payload.insert(
            serde_yaml::Value::String("target_role".into()),
            serde_yaml::Value::String("sovereign".into()),
        );
        let req = R6Request {
            role: "administrator".into(),
            action: "assign_role".into(),
            payload: serde_yaml::Value::Mapping(payload),
            resource: Default::default(),
        };
        assert_eq!(law.evaluate(&req), Decision::Deny);
    }

    #[tokio::test]
    async fn unresolved_selector_means_norm_does_not_fire() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: NONEXISTENT-FIELD
    selector: r6.resource.atp
    operator: ">"
    value: 100
    decision: deny
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        // No atp in resource → norm doesn't fire → default allow
        let req = request_with("citizen", "anything");
        assert_eq!(law.evaluate(&req), Decision::Allow);
    }

    #[tokio::test]
    async fn canonical_example_evaluates_atp_limit() {
        // Sanity: the example law from schema doc actually does what
        // the descriptions claim.
        let law = Law::parse_and_validate(EXAMPLE_LAW).unwrap();
        let mut over_budget = request_with("citizen", "spend_a_lot");
        over_budget.resource.insert("atp".into(), serde_yaml::Value::Number(150.into()));

        // ATP-LIMIT in the example uses `<=`, value 100, deny. The
        // semantics in the example description is "no single action may
        // consume more than 100" but encoded as `<= 100 → deny`. That
        // looks wrong — should fire when atp > 100. But we're testing
        // the SCHEMA as written, not fixing it. With <=, atp=150 doesn't
        // fire (150 is NOT <= 100), so allow. atp=50 DOES fire → deny.
        // This is a documentation bug in the schema doc, but our
        // evaluator correctly implements the encoded operator.
        let mut under = request_with("citizen", "spend_a_little");
        under.resource.insert("atp".into(), serde_yaml::Value::Number(50.into()));

        // Confirms our evaluator matches the literal schema: <= 100 fires for 50.
        assert_eq!(law.evaluate(&under), Decision::Deny);
        // atp=150 doesn't trigger ATP-LIMIT (150 NOT <= 100). But the
        // canonical example also has an escalation trigger
        // "r6.resource.atp > 50 → escalate_to sovereign" — which DOES
        // fire for 150. So Escalate, not Allow.
        assert_eq!(law.evaluate(&over_budget), Decision::Escalate);
    }

    // ----- Condition parser tests (V2-8 Step 3b) -----

    #[tokio::test]
    async fn condition_parses_numeric_gt() {
        let c = Condition::parse("r6.resource.atp > 50").unwrap();
        assert_eq!(c.selector, "r6.resource.atp");
        assert_eq!(c.operator, Operator::Gt);
        assert_eq!(c.value, serde_yaml::Value::Number(50.into()));
    }

    #[tokio::test]
    async fn condition_parses_quoted_string_eq() {
        let c = Condition::parse("r6.request.action == 'amend_charter'").unwrap();
        assert_eq!(c.selector, "r6.request.action");
        assert_eq!(c.operator, Operator::Eq);
        assert_eq!(c.value, serde_yaml::Value::String("amend_charter".into()));
    }

    #[tokio::test]
    async fn condition_parses_double_quoted_string() {
        let c = Condition::parse("r6.role == \"sovereign\"").unwrap();
        assert_eq!(c.value, serde_yaml::Value::String("sovereign".into()));
    }

    #[tokio::test]
    async fn condition_parses_bare_word() {
        let c = Condition::parse("r6.request.action == add_member").unwrap();
        assert_eq!(c.value, serde_yaml::Value::String("add_member".into()));
    }

    #[tokio::test]
    async fn condition_parses_list_for_in() {
        let c = Condition::parse("r6.role in [administrator, archivist]").unwrap();
        assert_eq!(c.operator, Operator::In);
        match c.value {
            serde_yaml::Value::Sequence(items) => assert_eq!(items.len(), 2),
            _ => panic!("expected sequence"),
        }
    }

    #[tokio::test]
    async fn condition_parses_le_and_ge() {
        assert_eq!(Condition::parse("r6.x <= 5").unwrap().operator, Operator::Le);
        assert_eq!(Condition::parse("r6.x >= 5").unwrap().operator, Operator::Ge);
    }

    #[tokio::test]
    async fn condition_rejects_non_r6_selector() {
        let result = Condition::parse("user.role == sovereign");
        assert!(result.is_err());
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("must start with 'r6.'"));
    }

    #[tokio::test]
    async fn condition_rejects_missing_operator() {
        let result = Condition::parse("r6.role sovereign");
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn condition_matches_request() {
        let c = Condition::parse("r6.resource.atp > 50").unwrap();
        let mut req = request_with("citizen", "anything");
        req.resource.insert("atp".into(), serde_yaml::Value::Number(75.into()));
        assert!(c.matches(&req));
        req.resource.insert("atp".into(), serde_yaml::Value::Number(25.into()));
        assert!(!c.matches(&req));
    }

    // ----- Full evaluator with escalation -----

    #[tokio::test]
    async fn escalation_fires_when_norms_silent() {
        let yaml = r#"
version: "1.0.0"
escalation:
  - condition: "r6.resource.atp > 50"
    escalate_to: sovereign
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        let mut req = request_with("citizen", "spend");
        req.resource.insert("atp".into(), serde_yaml::Value::Number(75.into()));
        let outcome = law.evaluate_outcome(&req);
        assert_eq!(outcome.decision, Decision::Escalate);
        assert_eq!(outcome.escalate_to, Some("sovereign".to_string()));
        assert_eq!(outcome.escalation_index, Some(0));
    }

    #[tokio::test]
    async fn deny_norm_overrides_escalation_trigger() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: HARD-DENY
    selector: r6.request.action
    operator: "=="
    value: forbidden
    decision: deny
escalation:
  - condition: "r6.request.action == forbidden"
    escalate_to: sovereign
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        let outcome = law.evaluate_outcome(&request_with("citizen", "forbidden"));
        // Deny is terminal; escalation can't override.
        assert_eq!(outcome.decision, Decision::Deny);
        assert_eq!(outcome.winning_norm, Some("HARD-DENY".to_string()));
    }

    #[tokio::test]
    async fn norm_escalate_defaults_to_sovereign() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: ESC
    selector: r6.request.action
    operator: "=="
    value: review_me
    decision: escalate
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        let outcome = law.evaluate_outcome(&request_with("citizen", "review_me"));
        assert_eq!(outcome.decision, Decision::Escalate);
        assert_eq!(outcome.escalate_to, Some("sovereign".to_string()));
    }

    #[tokio::test]
    async fn escalation_with_quoted_string_value() {
        let yaml = r#"
version: "1.0.0"
escalation:
  - condition: "r6.request.action == 'amend_charter'"
    escalate_to: sovereign
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        let outcome = law.evaluate_outcome(&request_with("admin", "amend_charter"));
        assert_eq!(outcome.decision, Decision::Escalate);
    }

    // ----- Interop fixtures (hub-lib/tests/fixtures/hub-law/) -----
    //
    // Legion seeded shared fixtures so the hub parser + the web4-law-check
    // validator CLI assert against the same source-of-truth files. Catches
    // divergence early. If these fail after a pull, the schema has shifted
    // and the parser needs updating.
    //
    // These used to `include_str!` straight out of `../../../../shared-context/`
    // — a sibling checkout, one directory ABOVE the repo root. That made a
    // PUBLIC repo's test suite depend, at COMPILE time, on a PRIVATE one
    // (dp-web4/shared-context). `include_str!` is not a soft dependency: a
    // missing file is a hard compile error, so `cargo test -p hub-lib` could
    // not build at all without the sibling. Consequences, both measured:
    //   - `cargo test (hub)` in .github/workflows/ci.yml has been red since the
    //     workflow was armed — the runner checks out dp-web4/web4 and nothing
    //     else. Four `couldn't read ... No such file or directory` errors.
    //   - Any clone of the public repo — an outside contributor, or one of our
    //     own worktrees — hits the identical error. Reproduced 2026-07-30 in a
    //     worktree with no sibling: byte-identical to the CI log.
    // Fixing it CI-side (checking the private repo out into the runner) needs a
    // secret in a public repo, and can't be the answer anyway: it would leave
    // every external clone broken.
    //
    // So the compile-time source of truth is now IN-REPO and public. The shared
    // copy under `shared-context/interop-fixtures/hub-law/` stays canonical for
    // the fleet; `interop_fixtures_match_shared_context_canonical` below asserts
    // the two are byte-identical on any machine that has both, which is every
    // fleet machine. The drift check the shared fixture existed to provide is
    // preserved — it just moved from "hard compile dependency" to "runtime
    // equivalence assertion where observable."

    const FIXTURE_MINIMAL: &str = include_str!(
        "../tests/fixtures/hub-law/minimal.yaml"
    );
    const FIXTURE_FULL: &str = include_str!(
        "../tests/fixtures/hub-law/full-featured.yaml"
    );
    const FIXTURE_INVALID_BAD_OPERATOR: &str = include_str!(
        "../tests/fixtures/hub-law/invalid-bad-operator.yaml"
    );
    const FIXTURE_INVALID_MISSING_NORM_ID: &str = include_str!(
        "../tests/fixtures/hub-law/invalid-missing-norm-id.yaml"
    );

    #[tokio::test]
    async fn interop_minimal_parses_and_validates() {
        Law::parse_and_validate(FIXTURE_MINIMAL)
            .expect("interop minimal fixture must parse + validate");
    }

    #[tokio::test]
    async fn interop_full_featured_parses_and_validates() {
        let law = Law::parse_and_validate(FIXTURE_FULL)
            .expect("interop full-featured fixture must parse + validate");
        assert!(!law.norms.is_empty(), "full-featured should have norms");
    }

    #[tokio::test]
    async fn interop_invalid_bad_operator_rejected() {
        let result = Law::parse_and_validate(FIXTURE_INVALID_BAD_OPERATOR);
        assert!(result.is_err(),
            "fixture with operator 'LIKE' must be rejected by validator");
    }

    #[tokio::test]
    async fn interop_invalid_missing_norm_id_rejected() {
        let result = Law::parse_and_validate(FIXTURE_INVALID_MISSING_NORM_ID);
        assert!(result.is_err(),
            "fixture with norm missing id must be rejected by validator");
    }

    /// The in-repo fixtures above are a copy. This asserts the copy has not
    /// drifted from the fleet-canonical originals in the `shared-context`
    /// sibling checkout — the guarantee the old `include_str!` bought by
    /// reading them directly, minus the hard compile dependency.
    ///
    /// Deliberately a RUNTIME read, not `include_str!`: the sibling is a
    /// private repo that CI and outside clones do not have, and re-introducing
    /// a compile-time reach out of the repo root is the exact defect this
    /// replaced. Where the sibling is absent the check cannot run and the test
    /// no-ops; where it is present — every fleet machine, including the one
    /// that publishes the canonical copy — drift fails loudly.
    #[test]
    fn interop_fixtures_match_shared_context_canonical() {
        use std::path::PathBuf;

        // CARGO_MANIFEST_DIR = <repo>/hub/hub-lib → ../../.. = the directory
        // holding the repo, where the shared-context checkout sits beside it.
        let shared: PathBuf = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../../shared-context/interop-fixtures/hub-law");
        if !shared.is_dir() {
            eprintln!(
                "SKIP interop drift check: no shared-context sibling at {} \
                 (expected on CI and on clones without the private repo)",
                shared.display()
            );
            return;
        }

        let cases: [(&str, &str); 4] = [
            ("minimal.yaml", FIXTURE_MINIMAL),
            ("full-featured.yaml", FIXTURE_FULL),
            ("invalid-bad-operator.yaml", FIXTURE_INVALID_BAD_OPERATOR),
            ("invalid-missing-norm-id.yaml", FIXTURE_INVALID_MISSING_NORM_ID),
        ];

        let mut checked = 0;
        for (name, in_repo) in cases {
            let path = shared.join(name);
            let canonical = std::fs::read_to_string(&path)
                .unwrap_or_else(|e| panic!("shared-context sibling exists but {} is unreadable: {e}", path.display()));
            assert_eq!(
                canonical, in_repo,
                "interop fixture `{name}` has DRIFTED from the fleet-canonical copy at {}.\n\
                 The canonical file is the source of truth: re-copy it into \
                 hub/hub-lib/tests/fixtures/hub-law/ and re-run.",
                path.display()
            );
            checked += 1;
        }
        assert_eq!(checked, 4, "all four interop fixtures must be compared");
    }

    #[tokio::test]
    async fn canonical_example_evaluates_admin_only_roles() {
        let law = Law::parse_and_validate(EXAMPLE_LAW).unwrap();
        let assign = request_with("citizen", "assign_role");
        // ADMIN-ONLY-ROLES (priority 20) fires; ATP-LIMIT may also fire
        // but only if atp <= 100 (default 0 satisfies). Both fire.
        // Priority: ADMIN-ONLY-ROLES (20) > ATP-LIMIT (10). Escalate wins.
        assert_eq!(law.evaluate(&assign), Decision::Escalate);
    }

    #[test]
    fn hydrate_fills_unset_defaults_preserves_explicit_idempotent() {
        // A law with one admission limit set explicitly, the other absent.
        let mut law = Law::parse_and_validate("version: \"1.0.0\"\nadmission:\n  review_limit: 5\n").unwrap();
        assert!(law.hydrate_defaults(), "fills the missing repeat_limit");
        let adm = law.ext.admission.as_ref().unwrap();
        assert_eq!(adm.repeat_limit, Some(DEFAULT_ADMISSION_REPEAT_LIMIT), "default filled");
        assert_eq!(adm.review_limit, Some(5), "explicit value preserved, not overwritten");
        assert!(!law.hydrate_defaults(), "idempotent — second call is a no-op");

        // A law with NO admission section gets one created to hold the defaults.
        let mut bare = Law::parse_and_validate("version: \"1.0.0\"\n").unwrap();
        assert!(bare.ext.admission.is_none());
        assert!(bare.hydrate_defaults());
        assert_eq!(bare.admission_repeat_limit(), DEFAULT_ADMISSION_REPEAT_LIMIT);
        assert_eq!(bare.admission_review_limit(), DEFAULT_ADMISSION_REVIEW_LIMIT);
        assert!(!bare.hydrate_defaults(), "idempotent");
    }

    #[test]
    fn live_admission_law_roundtrips_and_evaluates() {
        // The exact law the running HUB serves (GET /law, v1.0.2) — the signed,
        // hash-chained artifact. Integration canary for the #419 extraction: the
        // new Law<HubPolicy> must parse it, evaluate it, expose the admission
        // accessors, and re-serialize as a FIXED POINT (serde(flatten) of
        // HubPolicy must not drift — drift would change a law's hash).
        let live = r#"
version: "1.0.2"
norms:
  - id: ADMISSION-REQUIRES-SOVEREIGN
    selector: r6.request.action
    operator: "=="
    value: member_join_request
    decision: escalate
    priority: 100
    description: "Citizenship is not open-admission."
admission:
  open: false
  requires_sponsor: false
  repeat_limit: 3
  review_limit: 1
"#;
        let law = Law::parse_and_validate(live).expect("live law parses + validates");
        assert_eq!(law.admission_repeat_limit(), 3);
        assert_eq!(law.admission_review_limit(), 1);
        assert!(!law.ext.admission.as_ref().unwrap().open);
        let mut req = R6Request {
            role: "external".into(),
            action: "member_join_request".into(),
            ..Default::default()
        };
        assert_eq!(law.evaluate(&req), Decision::Escalate);
        req.action = "something_else".into();
        assert_eq!(law.evaluate(&req), Decision::Allow);
        // Serialization is a fixed point — the flatten extraction cannot silently
        // change a law's serialized bytes (and thus its hash).
        let y1 = law.to_yaml().unwrap();
        let y2 = Law::from_yaml(&y1).unwrap().to_yaml().unwrap();
        assert_eq!(y1, y2, "law serialization must be a fixed point (hash-stable)");
    }

    // ── reputation_emit (thread repemit-1) ──────────────────────────────────

    /// Legion's concrete v1 rule, verbatim from the locked grammar co-spec.
    const LEGION_EMIT_LAW: &str = r#"
version: "1.0.0"
reputation_emit:
  rules:
    - emitter: "61525719-def6-475c-a030-917f24a9dbf2"
      subject: "role:constellation:member"
      decision: allow
      priority: 10
      description: "Legion/hestia may report reputation on its constellation members (v1 role-scoped)"
"#;

    const LEGION_EMITTER: &str = "61525719-def6-475c-a030-917f24a9dbf2";
    const P3A_ROLE: &str = "role:constellation:member";

    #[test]
    fn reputation_emit_no_section_is_dark() {
        // No reputation_emit section ⇒ every non-Sovereign emit fails closed.
        let law = Law::parse_and_validate("version: \"1.0.0\"\n").unwrap();
        let out = law.reputation_emit_decision(LEGION_EMITTER, P3A_ROLE);
        assert_eq!(out, ReputationEmitOutcome { decision: Decision::Deny, matched_rule: None });
    }

    #[test]
    fn reputation_emit_legion_rule_allows_matching_emitter_and_role() {
        let law = Law::parse_and_validate(LEGION_EMIT_LAW).unwrap();
        let out = law.reputation_emit_decision(LEGION_EMITTER, P3A_ROLE);
        assert_eq!(out.decision, Decision::Allow);
        assert!(out.matched_rule.is_some());
    }

    #[test]
    fn reputation_emit_wrong_emitter_denied() {
        // Pin #1: a different authenticated identity, even with the right role,
        // does not match Legion's rule — fail closed.
        let law = Law::parse_and_validate(LEGION_EMIT_LAW).unwrap();
        let out = law.reputation_emit_decision("00000000-0000-0000-0000-000000000000", P3A_ROLE);
        assert_eq!(out.decision, Decision::Deny);
    }

    #[test]
    fn reputation_emit_wrong_role_denied() {
        // Right emitter, but a delta tagged with a role the rule doesn't cover.
        let law = Law::parse_and_validate(LEGION_EMIT_LAW).unwrap();
        let out = law.reputation_emit_decision(LEGION_EMITTER, "role:constellation:sovereign");
        assert_eq!(out.decision, Decision::Deny);
    }

    #[test]
    fn reputation_emit_v2_constellation_token_is_inert() {
        // A v2 `subject: constellation:<emitter>` rule never matches in v1 (fail
        // closed) even for the right emitter/subject — until the publish lands.
        let law = Law::parse_and_validate(
            "version: \"1.0.0\"\nreputation_emit:\n  rules:\n    - emitter: \"e1\"\n      subject: \"constellation:e1\"\n      decision: allow\n      priority: 10\n",
        )
        .unwrap();
        // The subject the emitter would carry equals the token string, yet it must
        // still not fire — the token is inert, not a literal role match.
        let out = law.reputation_emit_decision("e1", "constellation:e1");
        assert_eq!(out.decision, Decision::Deny, "v2 token must fail closed in v1");
    }

    #[test]
    fn reputation_emit_role_containing_constellation_word_is_not_inert() {
        // Guard the discriminator: `role:constellation:member` starts with `role:`,
        // so it's a live v1 role match — NOT the inert `constellation:` token.
        assert!(!subject_is_v2_inert(P3A_ROLE));
        assert!(subject_is_v2_inert("constellation:e1"));
    }

    #[test]
    fn reputation_emit_priority_and_decisions() {
        // Two matching rules for the same emitter+role: highest priority wins.
        let law = Law::parse_and_validate(
            "version: \"1.0.0\"\nreputation_emit:\n  rules:\n    - emitter: \"e1\"\n      subject: \"r\"\n      decision: allow\n      priority: 5\n    - emitter: \"e1\"\n      subject: \"r\"\n      decision: deny\n      priority: 20\n",
        )
        .unwrap();
        assert_eq!(law.reputation_emit_decision("e1", "r").decision, Decision::Deny,
            "priority-20 deny outranks priority-5 allow");
    }

    #[test]
    fn reputation_emit_legion_law_roundtrips_fixed_point() {
        // The wire form of the reputation_emit section must be hash-stable.
        let law = Law::parse_and_validate(LEGION_EMIT_LAW).unwrap();
        let y1 = law.to_yaml().unwrap();
        let y2 = Law::from_yaml(&y1).unwrap().to_yaml().unwrap();
        assert_eq!(y1, y2, "reputation_emit serialization must be a fixed point");
    }

    #[test]
    fn reputation_emit_empty_emitter_rejected() {
        let res = Law::parse_and_validate(
            "version: \"1.0.0\"\nreputation_emit:\n  rules:\n    - emitter: \"\"\n      subject: \"r\"\n      decision: allow\n      priority: 1\n",
        );
        assert!(res.is_err(), "empty emitter must be rejected at validate");
    }

    // ---- unknown-action guard (doc-audit D1) ----

    #[test]
    fn a_norm_naming_a_nonexistent_action_is_reported() {
        // `assign_role` is what HUB-LAW.md told operators to write. The gate emits
        // `role_assigned`. This norm reads as a restriction and restricts nothing.
        let law: Law = serde_yaml::from_str(r#"
version: "1.0.0"
norms:
  - id: ESCALATE-ROLE-ASSIGN
    selector: r6.request.action
    operator: "=="
    value: assign_role
    decision: escalate
    priority: 50
"#).expect("parses");
        let found = law.unknown_action_norms();
        assert_eq!(found.len(), 1, "the bogus norm was not reported: {found:?}");
        assert_eq!(found[0].norm_id, "ESCALATE-ROLE-ASSIGN");
        assert_eq!(found[0].value, "assign_role");

        // And the same norm written correctly is clean — so the guard is
        // discriminating between the two spellings, not just flagging the norm.
        let good: Law = serde_yaml::from_str(r#"
version: "1.0.0"
norms:
  - id: ESCALATE-ROLE-ASSIGN
    selector: r6.request.action
    operator: "=="
    value: role_assigned
    decision: escalate
    priority: 50
"#).expect("parses");
        assert!(good.unknown_action_norms().is_empty(), "the CORRECT spelling was flagged");
    }

    /// The arm that matters most: the guard must not reject what the hub ships.
    ///
    /// The starter law contains three shapes that a naive implementation gets
    /// wrong — `DEFAULT-ALLOW`'s deliberately-unmatchable `!=` value, an `in` list
    /// of seven kinds, and `member_join_request`, which is a synthesised gate
    /// action that no event kind will ever equal.
    #[test]
    fn the_shipped_starter_law_is_clean() {
        let law: Law = Law::parse_and_validate(include_str!("../../examples/starter-law.yaml"))
            .expect("the embedded starter law validates");
        let found = law.unknown_action_norms();
        assert!(
            found.is_empty(),
            "the guard rejects the law the hub itself ships: {found:?}",
        );
        // Positive control on the two shapes most likely to be mishandled, so a
        // guard that silently skipped every norm could not pass this test.
        assert!(law.norms.iter().any(|n| n.id == "DEFAULT-ALLOW"),
                "fixture lost DEFAULT-ALLOW — the != arm is no longer exercised");
        assert!(law.norms.iter().any(|n| matches!(n.operator, web4_policy::Operator::In)),
                "fixture lost the `in` list — that arm is no longer exercised");
    }

    #[test]
    fn read_actions_and_in_lists_are_understood() {
        let law: Law = serde_yaml::from_str(r#"
version: "1.0.0"
norms:
  - id: READ-GATE
    selector: r6.request.action
    operator: "=="
    value: "read:list_members"
    decision: deny
    priority: 10
  - id: MIXED-LIST
    selector: r6.request.action
    operator: in
    value: [member_added, not_a_real_kind, topic_created]
    decision: escalate
    priority: 10
  - id: NOT-AN-ACTION-SELECTOR
    selector: r6.role
    operator: "=="
    value: citizen
    decision: allow
    priority: 1
"#).expect("parses");
        let found = law.unknown_action_norms();
        // The read: family passes, the two real kinds pass, only the bogus one is
        // named — and a norm on a DIFFERENT selector is not examined at all.
        assert_eq!(found.len(), 1, "expected exactly the bogus list entry: {found:?}");
        assert_eq!(found[0].norm_id, "MIXED-LIST");
        assert_eq!(found[0].value, "not_a_real_kind");
    }

    /// The action table in `HUB-LAW.md` must be EXACTLY the gate's vocabulary.
    ///
    /// Set equality, not containment. A missing kind means an operator cannot
    /// write a norm for an act that exists; a *spurious* one is worse — it is the
    /// canonical table teaching a value the gate never emits, which is D1 with a
    /// documentation source. The first version of this test only checked one
    /// direction; GPT's review on #671 caught that.
    #[test]
    fn hub_law_doc_action_table_equals_the_gate_vocabulary() {
        let doc = include_str!("../../docs/HUB-LAW.md");
        let start = doc.find("| group | actions |")
            .expect("action table heading missing from HUB-LAW.md");
        let end = doc[start..].find("**Two action families")
            .map(|i| start + i)
            .expect("action-table terminator missing from HUB-LAW.md");
        let table = &doc[start..end];

        // Every backticked token inside the table region.
        let mut listed: Vec<&str> = Vec::new();
        let mut rest = table;
        while let Some(a) = rest.find('`') {
            rest = &rest[a + 1..];
            let Some(b) = rest.find('`') else { break };
            let tok = &rest[..b];
            rest = &rest[b + 1..];
            if !tok.is_empty() && tok.chars().all(|c| c.is_ascii_lowercase() || c == '_' || c.is_ascii_digit()) {
                listed.push(tok);
            }
        }
        listed.sort_unstable();
        listed.dedup();
        assert!(listed.len() > 20, "extracted only {} tokens — the extractor broke", listed.len());

        let mut expected: Vec<&str> = crate::events::HubEvent::ALL_EVENT_KINDS.to_vec();
        expected.sort_unstable();

        let missing: Vec<_> = expected.iter().filter(|k| !listed.contains(k)).collect();
        let spurious: Vec<_> = listed.iter().filter(|k| !expected.contains(k)).collect();
        assert!(
            missing.is_empty() && spurious.is_empty(),
            "HUB-LAW.md's action table has drifted from the gate vocabulary.\n  \
             missing (operator cannot write a norm for these): {missing:?}\n  \
             spurious (the table teaches a value the gate never emits): {spurious:?}",
        );
    }

    /// Every YAML block in `HUB-LAW.md` must survive the guard `set-law` applies.
    ///
    /// Extracted from the DOC, not retyped here. The first version of this test
    /// reconstructed the examples in Rust, so the real document could drift back
    /// to an invalid action while the test stayed green — and it did: the full
    /// worked law example carried `value: assign_role` about ninety lines below
    /// its own correction, in the block an operator is most likely to copy
    /// wholesale. Post-#670 that is a hard refusal, not a silent no-op, so a
    /// duplicated fixture was actively hiding the worse failure.
    #[test]
    fn every_yaml_example_in_the_doc_passes_the_action_guard() {
        let doc = include_str!("../../docs/HUB-LAW.md");

        let mut blocks: Vec<&str> = Vec::new();
        let mut rest = doc;
        while let Some(a) = rest.find("```yaml\n") {
            rest = &rest[a + 8..];
            let Some(b) = rest.find("```") else { break };
            blocks.push(&rest[..b]);
            rest = &rest[b + 3..];
        }
        assert!(
            blocks.len() >= 3,
            "found only {} yaml block(s) — the extractor broke, the doc did not",
            blocks.len(),
        );

        let mut checked = 0usize;
        for (i, raw) in blocks.iter().enumerate() {
            // The doc shows three shapes: a whole law, a bare `norms:` map, and a
            // bare norm sequence. Normalise each into something parseable rather
            // than skipping the fragments — the fragments are what people copy.
            let trimmed = raw.trim_start();
            let candidate = if trimmed.starts_with("version:") {
                raw.to_string()
            } else if trimmed.starts_with("norms:") {
                format!("version: \"1.0.0\"\n{raw}")
            } else if trimmed.starts_with("- id:") {
                let indented: String =
                    raw.lines().map(|l| format!("  {l}\n")).collect();
                format!("version: \"1.0.0\"\nnorms:\n{indented}")
            } else {
                continue;
            };

            let law: Law = match serde_yaml::from_str(&candidate) {
                Ok(l) => l,
                Err(e) => panic!("HUB-LAW.md yaml block {i} does not parse: {e}\n{candidate}"),
            };
            let bad = law.unknown_action_norms();
            assert!(
                bad.is_empty(),
                "HUB-LAW.md yaml block {i} tells operators to write a law that \
                 `hub set-law` REFUSES: {bad:?}",
            );
            checked += 1;
        }
        assert!(checked >= 3, "only {checked} block(s) were actually normalised and checked");
    }
}

#[cfg(test)]
mod emit_mode_tests {
    use super::*;

    #[test]
    fn mode_defaults_to_classify_only() {
        // F0.1: a `reputation_emit` section that says nothing about mode
        // observes before it actuates — and no section at all is the same.
        let yaml = r#"
rules:
  - emitter: "hestia-gate"
    subject: "citizen"
    decision: allow
    priority: 10
"#;
        let policy: ReputationEmitPolicy = serde_yaml::from_str(yaml).expect("parses");
        assert_eq!(policy.mode, EmitMode::ClassifyOnly);
    }

    #[test]
    fn mode_apply_parses_and_round_trips() {
        let yaml = r#"
mode: apply
rules:
  - emitter: "hestia-gate"
    subject: "citizen"
    decision: allow
    priority: 10
"#;
        let policy: ReputationEmitPolicy = serde_yaml::from_str(yaml).expect("parses");
        assert_eq!(policy.mode, EmitMode::Apply);
        let back = serde_yaml::to_string(&policy).expect("serializes");
        let again: ReputationEmitPolicy = serde_yaml::from_str(&back).expect("round-trips");
        assert_eq!(again.mode, EmitMode::Apply);
    }
}

#[cfg(test)]
pub(super) mod sponsor_tests {
    use super::*;

    pub(super) fn policy(requires: bool, role: Option<&str>, trust: Option<f64>) -> AdmissionPolicy {
        AdmissionPolicy {
            open: false,
            requires_sponsor: requires,
            sponsor_role: role.map(String::from),
            min_trust_score: trust,
            repeat_limit: None,
            review_limit: None,
            description: None,
        }
    }

    /// Facts for a sponsor whose vouch IS witnessed (the future state, once a
    /// vouch event is projected). Existing assertions about role/trust logic
    /// use this so they exercise the clauses beyond consent.
    pub(super) fn facts(applicant: Uuid, sponsor: Option<Uuid>, resolved: bool, trust: Option<f64>)
        -> SponsorFacts {
        SponsorFacts {
            applicant_lct_id: applicant,
            claimed_sponsor: sponsor,
            sponsor_is_resolved_member: resolved,
            vouch_is_attested: true,
            sponsor_trust: trust,
        }
    }

    /// Facts as the daemon builds them TODAY: no vouch event is projected, so
    /// the sponsoring act is unwitnessed however resolvable the identity is.
    pub(super) fn policy_requiring_sponsor() -> AdmissionPolicy { policy(true, None, None) }

    pub(super) fn facts_unvouched(applicant: Uuid, sponsor: Option<Uuid>, resolved: bool)
        -> SponsorFacts {
        SponsorFacts {
            applicant_lct_id: applicant,
            claimed_sponsor: sponsor,
            sponsor_is_resolved_member: resolved,
            vouch_is_attested: false,
            sponsor_trust: None,
        }
    }

    /// **The R7b acceptance criterion (issue 701).** Differential: two
    /// applicants identical in every respect except *who* they name as
    /// sponsor. The one naming a registry-resolved member is satisfied; its
    /// self-asserting twin collects no peer factor and cannot auto-admit.
    #[test]
    fn self_asserted_twin_collects_no_peer_factor() {
        let p = policy(true, None, None);
        let applicant = Uuid::new_v4();
        let real_sponsor = Uuid::new_v4();

        let resolved = evaluate_sponsor(Some(&p), facts(applicant, Some(real_sponsor), true, None));
        assert_eq!(resolved, SponsorVerdict::Satisfied { sponsor_lct_id: real_sponsor });
        assert!(resolved.may_auto_admit(), "a resolved peer sponsor may auto-admit");

        let twin = evaluate_sponsor(Some(&p), facts(applicant, Some(applicant), true, None));
        assert_eq!(twin, SponsorVerdict::Refuted(SponsorRefusal::SelfSponsored));
        assert!(!twin.may_auto_admit(), "an asserted asker collects no peer factor");
    }

    /// Self-sponsorship is refused even when the applicant is *already*
    /// resolvable — being key-bound does not let an identity vouch for itself.
    #[test]
    fn self_sponsorship_is_checked_before_resolution() {
        let p = policy(true, Some("citizen"), Some(0.9));
        let a = Uuid::new_v4();
        // Resolved member, high trust, right role — and still refused.
        let v = evaluate_sponsor(Some(&p), facts(a, Some(a), true, Some(1.0)));
        assert_eq!(v, SponsorVerdict::Refuted(SponsorRefusal::SelfSponsored),
            "no later clause may launder a self-sponsorship");
    }

    /// A name in a payload is an assertion, not evidence.
    #[test]
    fn unresolved_sponsor_is_refuted() {
        let p = policy(true, None, None);
        let (a, s) = (Uuid::new_v4(), Uuid::new_v4());
        let v = evaluate_sponsor(Some(&p), facts(a, Some(s), false, None));
        assert_eq!(v, SponsorVerdict::Refuted(SponsorRefusal::NotResolved { named: s }));
        assert!(!v.may_auto_admit());
    }

    #[test]
    fn missing_sponsor_when_required_is_refuted() {
        let p = policy(true, None, None);
        let v = evaluate_sponsor(Some(&p), facts(Uuid::new_v4(), None, false, None));
        assert_eq!(v, SponsorVerdict::Refuted(SponsorRefusal::Missing));
    }

    /// The split-exit discipline: "cannot verify" is NOT "verified false".
    /// A role beyond membership is undecidable (roles aren't projected), and
    /// an absent trust record is undecidable (not a zero score) — both block
    /// auto-admission, but each names its own exit.
    #[test]
    fn undecidable_exits_are_distinct_from_refutations() {
        let (a, s) = (Uuid::new_v4(), Uuid::new_v4());

        let role = evaluate_sponsor(
            Some(&policy(true, Some("treasurer"), None)),
            facts(a, Some(s), true, None));
        assert_eq!(role, SponsorVerdict::Undecidable(
            SponsorUnknown::RoleNotProjected { required_role: "treasurer".into() }));
        assert!(!role.may_auto_admit());
        assert_eq!(role.token(), "undecidable_role");

        let trust = evaluate_sponsor(
            Some(&policy(true, None, Some(0.5))),
            facts(a, Some(s), true, None));
        assert_eq!(trust, SponsorVerdict::Undecidable(
            SponsorUnknown::NoTrustRecord { required: 0.5 }));
        assert_eq!(trust.token(), "undecidable_trust",
            "an absent record must not read as a failing score");

        let below = evaluate_sponsor(
            Some(&policy(true, None, Some(0.5))),
            facts(a, Some(s), true, Some(0.2)));
        assert_eq!(below, SponsorVerdict::Refuted(
            SponsorRefusal::TrustBelowBar { score: 0.2, required: 0.5 }),
            "a real score below the bar IS a refutation");
    }

    /// `sponsor_role: citizen` names membership itself, which the projection
    /// can check — so it stays decidable.
    #[test]
    fn membership_role_is_decidable() {
        let (a, s) = (Uuid::new_v4(), Uuid::new_v4());
        let v = evaluate_sponsor(Some(&policy(true, Some("Citizen"), None)),
            facts(a, Some(s), true, None));
        assert_eq!(v, SponsorVerdict::Satisfied { sponsor_lct_id: s },
            "the membership role is case-insensitively checkable");
    }

    #[test]
    fn no_policy_or_no_requirement_imposes_nothing() {
        let a = Uuid::new_v4();
        assert_eq!(evaluate_sponsor(None, facts(a, None, false, None)),
            SponsorVerdict::NotRequired);
        assert_eq!(evaluate_sponsor(Some(&policy(false, None, None)), facts(a, None, false, None)),
            SponsorVerdict::NotRequired);
    }

    /// A trust bar without `requires_sponsor` still requires one — otherwise
    /// law states a bar it can never apply (the unenforced-knob defect this
    /// sprint exists to end).
    #[test]
    fn trust_bar_alone_still_requires_a_sponsor() {
        let v = evaluate_sponsor(Some(&policy(false, None, Some(0.4))),
            facts(Uuid::new_v4(), None, false, None));
        assert_eq!(v, SponsorVerdict::Refuted(SponsorRefusal::Missing));
    }

    /// Strictest-wins: the sponsor check may only tighten (Family 8 lattice).
    #[test]
    fn composition_only_tightens() {
        let refuted = SponsorVerdict::Refuted(SponsorRefusal::SelfSponsored);
        let ok = SponsorVerdict::Satisfied { sponsor_lct_id: Uuid::new_v4() };
        // Unmet turns auto-admit into review...
        assert_eq!(tighten_with_sponsor(Decision::Allow, &refuted), Decision::Escalate);
        assert_eq!(tighten_with_sponsor(Decision::Warn, &refuted), Decision::Escalate);
        // ...but never rescues a denial, and never downgrades an escalation.
        assert_eq!(tighten_with_sponsor(Decision::Deny, &ok), Decision::Deny);
        assert_eq!(tighten_with_sponsor(Decision::Deny, &refuted), Decision::Deny);
        assert_eq!(tighten_with_sponsor(Decision::Escalate, &ok), Decision::Escalate);
        // A met requirement leaves the norms decision untouched.
        assert_eq!(tighten_with_sponsor(Decision::Allow, &ok), Decision::Allow);
    }

    /// Every non-passing verdict tells the operator which exit fired.
    #[test]
    fn every_blocking_verdict_carries_a_reason() {
        let (a, s) = (Uuid::new_v4(), Uuid::new_v4());
        for v in [
            evaluate_sponsor(Some(&policy(true, None, None)), facts(a, None, false, None)),
            evaluate_sponsor(Some(&policy(true, None, None)), facts(a, Some(a), true, None)),
            evaluate_sponsor(Some(&policy(true, None, None)), facts(a, Some(s), false, None)),
            evaluate_sponsor(Some(&policy(true, Some("archivist"), None)), facts(a, Some(s), true, None)),
            evaluate_sponsor(Some(&policy(true, None, Some(0.5))), facts(a, Some(s), true, None)),
            evaluate_sponsor(Some(&policy(true, None, Some(0.5))), facts(a, Some(s), true, Some(0.1))),
        ] {
            assert!(!v.may_auto_admit());
            assert!(v.reason().is_some(), "{v:?} must explain itself to the operator");
        }
        assert!(evaluate_sponsor(None, facts(a, None, false, None)).reason().is_none());
    }
}

#[cfg(test)]
mod sponsor_consent_tests {
    use super::*;
    use super::sponsor_tests::*;

    /// **The review finding (PR 706).** A resolvable member identity proves the
    /// member EXISTS; it does not prove they sponsored anyone. The relation is a
    /// field the applicant typed, and member ids are not secret by any route —
    /// the public identity file publishes the founding sovereign's, the presence
    /// roster returns every member's, and every member already knows the others'.
    /// So resolvability alone must NOT auto-admit.
    #[test]
    fn a_resolvable_but_unconsenting_sponsor_cannot_auto_admit() {
        let p = policy_requiring_sponsor();
        let (applicant, sponsor) = (Uuid::new_v4(), Uuid::new_v4());

        // Exactly the daemon's present facts: real member, pinned key, no
        // witnessed vouch.
        let v = evaluate_sponsor(Some(&p), facts_unvouched(applicant, Some(sponsor), true));
        assert_eq!(v, SponsorVerdict::Undecidable(
            SponsorUnknown::VouchNotAttested { named: sponsor }));
        assert!(!v.may_auto_admit(),
            "naming a member you never spoke to must not admit you");
        assert_eq!(v.token(), "undecidable_vouch_not_attested");
        assert!(v.reason().unwrap().contains("not evidence of a"),
            "the operator is told existence != consent");
    }

    /// It is UNDECIDABLE, not refuted: the sponsorship may be perfectly real,
    /// and a human can confirm what the hub cannot yet witness. Conflating the
    /// two would make an honest applicant look like a liar in the record.
    #[test]
    fn unattested_vouch_is_undecidable_not_a_refutation() {
        let p = policy_requiring_sponsor();
        let (a, s) = (Uuid::new_v4(), Uuid::new_v4());
        let v = evaluate_sponsor(Some(&p), facts_unvouched(a, Some(s), true));
        assert!(matches!(v, SponsorVerdict::Undecidable(_)));
        assert!(!matches!(v, SponsorVerdict::Refuted(_)));
    }

    /// Consent does not rescue the refutations: a self-named sponsor and an
    /// unresolvable name stay Refuted, checked before consent is consulted.
    #[test]
    fn consent_is_checked_after_the_refutations_not_instead_of_them() {
        let p = policy_requiring_sponsor();
        let a = Uuid::new_v4();
        assert_eq!(evaluate_sponsor(Some(&p), facts_unvouched(a, Some(a), true)),
            SponsorVerdict::Refuted(SponsorRefusal::SelfSponsored));
        let ghost = Uuid::new_v4();
        assert_eq!(evaluate_sponsor(Some(&p), facts_unvouched(a, Some(ghost), false)),
            SponsorVerdict::Refuted(SponsorRefusal::NotResolved { named: ghost }));
    }

    /// The forward path: once a vouch event IS witnessed, `Satisfied` becomes
    /// reachable cleanly — the predicate is already correct for that world, so
    /// landing the vouch event is wiring, not a redesign.
    #[test]
    fn an_attested_vouch_satisfies() {
        let p = policy_requiring_sponsor();
        let (a, s) = (Uuid::new_v4(), Uuid::new_v4());
        let v = evaluate_sponsor(Some(&p), facts(a, Some(s), true, None));
        assert_eq!(v, SponsorVerdict::Satisfied { sponsor_lct_id: s });
        assert!(v.may_auto_admit());
    }
}
