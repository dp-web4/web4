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
use web4_policy::PolicyExtension;

// Re-export the generic engine surface so `crate::law::*` consumers are unchanged.
pub use web4_policy::{
    Condition, CustomPredicate, Decision, DecisionOutcome, EscalationTrigger, Norm, Operator,
    Procedure, R6Request,
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
/// `mesh_worker`). Members validate their declared role at connect against this
/// set and **fail closed to [`DEFAULT_CONSTELLATION_ROLE`]** on any unknown value
/// — never minting a novel role subject. See [`normalize_constellation_role`].
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
/// [`DEFAULT_CONSTELLATION_ROLE`] on any unpublished value. This is the hub's
/// half of the HUB Concern 2 contract: a member calls this with the role it
/// declared, stamps the returned canonical string as its `role_lct`, and thereby
/// cannot fragment the fold with a typo'd or novel capacity.
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

/// The hub's `reputation_emit` law section — who, other than the Sovereign, may
/// record reputation deltas, and for which subject-roles. Absent section ⇒ the
/// emit path is fully dark (Sovereign-only, the pre-wiring behavior).
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct ReputationEmitPolicy {
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub rules: Vec<ReputationEmitRule>,
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

    // ----- Interop fixtures (shared-context/interop-fixtures/hub-law/) -----
    //
    // Legion seeded shared fixtures so the hub parser + the web4-law-check
    // validator CLI assert against the same source-of-truth files. Catches
    // divergence early. If these fail after a pull, the schema has shifted
    // and the parser needs updating.

    const FIXTURE_MINIMAL: &str = include_str!(
        "../../../../shared-context/interop-fixtures/hub-law/minimal.yaml"
    );
    const FIXTURE_FULL: &str = include_str!(
        "../../../../shared-context/interop-fixtures/hub-law/full-featured.yaml"
    );
    const FIXTURE_INVALID_BAD_OPERATOR: &str = include_str!(
        "../../../../shared-context/interop-fixtures/hub-law/invalid-bad-operator.yaml"
    );
    const FIXTURE_INVALID_MISSING_NORM_ID: &str = include_str!(
        "../../../../shared-context/interop-fixtures/hub-law/invalid-missing-norm-id.yaml"
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

}
