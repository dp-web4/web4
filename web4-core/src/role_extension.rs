//! Role-extension entities — the Rust representation of the canonical
//! `web4-standard/ontology/role-extension.ttl` schema (Phase-0 concord, #486),
//! plus role-LCT issuance and a registry. This is the web4-core/schema half of
//! the Hestia role-orchestration PRD: it turns an orchestration role from a bare
//! string into a first-class `EntityType::Role` LCT entity carrying its law
//! extension (affordances / responsibilities / scope), so a role born from a
//! migrated launcher and a role defined via the hub UI are the *same* entity.
//!
//! Serialization mirrors the ontology property names, so the Rust `RoleExtension`
//! round-trips against the ttl (the check HUB asked for in Phase 1).
//!
//! **Monotone restriction** is NOT enforced here (it is an eval-time property of
//! the *fold*, `hestia::policy::fold_strictest` — strictest-wins, deployed): an
//! extension can only tighten inherited law, never grant. What this module owns
//! is the §2.3 correction — an eval-time base-deny on a role-permissive action is
//! attributable to a *cause* only via the authoring-validity witness persisted
//! here (`authored_under` + `lint_verdict`); the fold alone cannot tell the causes
//! apart. See [`RoleExtension::drift_mark`].

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::crypto::KeyPair;
use crate::lct::{EntityType, Lct, LctBuilder};

/// A concrete affordance grant — what the role's occupant MAY do. One variant per
/// `role:Affordance` subclass in the ontology; the payload is `role:permits` (the
/// grant token). Absence is fail-closed: the launcher MUST refuse what the role
/// does not afford (`--dangerously-skip-permissions` is exactly a `CliFlag`).
///
/// NOTE: `role:EnvAffordance` (env-at-invocation, e.g. `PATH=…`) is deliberately
/// absent — flagged to HUB in the Phase-1 round-trip as a pending concord item;
/// added here only once the ontology adds it, to keep the round-trip exact.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", content = "permits", rename_all = "snake_case")]
pub enum Affordance {
    /// `role:ToolAffordance` — a tool or tool-category (hestia `PolicyMatch.tools`/`.categories`).
    Tool(String),
    /// `role:ChannelAffordance` — a mesh/hub channel id.
    Channel(String),
    /// `role:RepoAffordance` — a repository the role may act in.
    Repo(String),
    /// `role:WriteClassAffordance` — a class of write the role may perform.
    WriteClass(String),
    /// `role:CliFlagAffordance` — a specific launcher flag.
    CliFlag(String),
}

/// `role:Responsibility` — what the occupant MUST do, and on what cadence.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Responsibility {
    pub description: String,
    /// `role:cadence` — cron-like or event trigger for how often the duty is due.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub cadence: Option<String>,
    /// `role:reportsTo` — where the duty's discharge is reported.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reports_to: Option<String>,
}

/// `role:Scope` — the MRH horizon the role reads and acts within.
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub struct Scope {
    /// `role:rangesOver` — resources (repos, machines, channels, data classes) in the MRH.
    #[serde(default)]
    pub ranges_over: Vec<String>,
    /// `role:atpBudget` — ATP ceiling per period, enforced by the Treasurer at act time.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub atp_budget: Option<f64>,
}

/// The extension's no-match verdict (`role:defaultVerdict`). Monotone restriction
/// requires this to be `Allow`: the extension only *adds* denies/warns on top of
/// inherited law, so a no-match means "the role adds no restriction here" and the
/// parent law decides via the fold. `Warn`/`Deny` defaults are expressible but
/// tighten the whole surface and should be rare.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ExtensionVerdict {
    #[default]
    Allow,
    Warn,
    Deny,
}

/// `role:lintVerdict` — the write-time linter's recorded verdict against
/// `authored_under`. Persisted, not throwaway: it is the attribution anchor.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum LintVerdict {
    /// Extension passed the linter against its authoring-time parent law.
    Pass,
    /// Extension exceeded parent even at authoring time (author error).
    Fail,
}

/// `role:driftMark` — the *cause* of an eval-time base-deny on a role-permissive
/// action, DERIVED from the authoring witness (never re-derived from the fold
/// alone; the fold cannot tell these apart — all three present identically as
/// overlay-permissive/base-denies). The load-bearing §2.3 correction.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum DriftMark {
    /// `lint_verdict = Fail` — extension always exceeded parent. Author error.
    #[serde(rename = "author:violation")]
    AuthorViolation,
    /// `lint_verdict = Pass` — once-valid extension, parent later tightened. Silent
    /// role-rot, NOT the author's fault.
    #[serde(rename = "drift:parent-tightened")]
    DriftParentTightened,
    /// No witness (offline / linter skipped / pre-migration string-role). Denied,
    /// cause unknown — fail-closed on the deny, honest on the cause.
    #[serde(rename = "drift:unattributed")]
    DriftUnattributed,
}

/// The `role:Extension` — a role's own law layer, composed under inherited society
/// ∧ constellation law via strictest-wins fold (eval-time, in hestia). Affordances,
/// responsibilities, scope, plus the authoring-validity witness (§2.3).
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct RoleExtension {
    /// `role:boundToRoleLct` — the Role LCT this extension is the law of.
    pub bound_to_role_lct: Uuid,
    /// `role:hasAffordance`.
    #[serde(default)]
    pub affordances: Vec<Affordance>,
    /// `role:hasResponsibility`.
    #[serde(default)]
    pub responsibilities: Vec<Responsibility>,
    /// `role:hasScope`.
    #[serde(default)]
    pub scope: Scope,
    /// `role:defaultVerdict` — Allow under monotone restriction.
    #[serde(default)]
    pub default_verdict: ExtensionVerdict,
    /// `role:foldsUnder` — the parent law level(s) (society / constellation) this
    /// composes under. Extension can only tighten.
    #[serde(default)]
    pub folds_under: Vec<String>,
    /// `role:authoredUnder` — the parent-law snapshot the write-time linter checked
    /// this extension against. `None` = no witness → `drift:unattributed` on deny.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub authored_under: Option<String>,
    /// `role:lintVerdict` — the linter's persisted verdict. Paired with
    /// `authored_under` it records whether the extension was EVER valid.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub lint_verdict: Option<LintVerdict>,
}

impl RoleExtension {
    /// The §2.3 attribution: given an eval-time base-deny on a role-permissive
    /// action, the cause is read from the authoring witness — never guessed from
    /// the fold. `Fail` ⇒ author violated parent at authoring; `Pass` ⇒ parent
    /// tightened under a once-valid extension; no witness ⇒ unattributed.
    pub fn drift_mark(&self) -> DriftMark {
        match self.lint_verdict {
            Some(LintVerdict::Fail) => DriftMark::AuthorViolation,
            Some(LintVerdict::Pass) => DriftMark::DriftParentTightened,
            None => DriftMark::DriftUnattributed,
        }
    }

    /// Does this extension grant `token` under any affordance? Fail-closed helper
    /// for the launcher: a flag/tool/repo not afforded is refused.
    pub fn affords(&self, token: &str) -> bool {
        self.affordances.iter().any(|a| {
            matches!(a,
                Affordance::Tool(t) | Affordance::Channel(t) | Affordance::Repo(t)
                    | Affordance::WriteClass(t) | Affordance::CliFlag(t) if t == token)
        })
    }
}

/// A first-class orchestration role: a `EntityType::Role` LCT + its canonical
/// label (`role:constellation:*`) + its law extension.
#[derive(Clone, Debug)]
pub struct RoleEntity {
    pub lct: Lct,
    /// The canonical constellation-role label (the string the fleet already uses).
    pub label: String,
    pub extension: RoleExtension,
}

impl RoleEntity {
    /// Issue a new role entity: mint a `Role` LCT under the sovereign and bind the
    /// extension to it. The role gets its own keypair (roles have presence). The
    /// extension's `bound_to_role_lct` is overwritten with the freshly-minted id so
    /// the binding is authoritative, not caller-asserted.
    pub fn issue(label: impl Into<String>, sovereign_lct: Uuid, mut extension: RoleExtension) -> (Self, KeyPair) {
        let (lct, keypair) = LctBuilder::new(EntityType::Role)
            .created_by(sovereign_lct)
            .build();
        extension.bound_to_role_lct = lct.id;
        (
            Self { lct, label: label.into(), extension },
            keypair,
        )
    }
}

/// A registry of orchestration role entities, keyed by canonical label. The
/// audit-first mirror populates this from the existing launchers (Phase 1); the
/// hub UI adds to it (Phase 2+). Read/act split lives at the caller — this is the
/// in-memory index.
#[derive(Clone, Debug, Default)]
pub struct RoleRegistry {
    roles: std::collections::HashMap<String, RoleEntity>,
}

impl RoleRegistry {
    pub fn new() -> Self {
        Self::default()
    }

    /// Register (or replace by label) a role entity. Idempotent by label.
    pub fn register(&mut self, role: RoleEntity) {
        self.roles.insert(role.label.clone(), role);
    }

    pub fn get(&self, label: &str) -> Option<&RoleEntity> {
        self.roles.get(label)
    }

    /// Canonical labels currently registered, sorted for stable enumeration.
    pub fn labels(&self) -> Vec<&str> {
        let mut v: Vec<&str> = self.roles.keys().map(String::as_str).collect();
        v.sort_unstable();
        v
    }

    pub fn len(&self) -> usize {
        self.roles.len()
    }

    pub fn is_empty(&self) -> bool {
        self.roles.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ext(lint: Option<LintVerdict>) -> RoleExtension {
        RoleExtension {
            bound_to_role_lct: Uuid::nil(),
            affordances: vec![
                Affordance::CliFlag("--dangerously-skip-permissions".into()),
                Affordance::Tool("Bash".into()),
            ],
            responsibilities: vec![Responsibility {
                description: "drain mailbox".into(),
                cadence: Some("event".into()),
                reports_to: None,
            }],
            scope: Scope { ranges_over: vec!["repo:web4".into()], atp_budget: Some(100.0) },
            default_verdict: ExtensionVerdict::Allow,
            folds_under: vec!["law:constellation".into()],
            authored_under: lint.map(|_| "lawsnap:2026-07-08".into()),
            lint_verdict: lint,
        }
    }

    #[test]
    fn issue_mints_a_role_lct_and_binds_the_extension() {
        let sovereign = Uuid::new_v4();
        let (role, _kp) = RoleEntity::issue("role:constellation:mesh-worker", sovereign, ext(Some(LintVerdict::Pass)));
        assert_eq!(role.lct.entity_type, EntityType::Role);
        assert_eq!(role.lct.created_by, Some(sovereign));
        // the binding is authoritative — extension points at the freshly-minted LCT
        assert_eq!(role.extension.bound_to_role_lct, role.lct.id);
        assert_ne!(role.lct.id, Uuid::nil());
        assert_eq!(role.label, "role:constellation:mesh-worker");
    }

    #[test]
    fn drift_mark_derives_cause_from_the_witness_not_the_fold() {
        // The §2.3 correction: the three causes are distinguished ONLY by the
        // persisted authoring witness — the fold cannot tell them apart.
        assert_eq!(ext(Some(LintVerdict::Fail)).drift_mark(), DriftMark::AuthorViolation);
        assert_eq!(ext(Some(LintVerdict::Pass)).drift_mark(), DriftMark::DriftParentTightened);
        assert_eq!(ext(None).drift_mark(), DriftMark::DriftUnattributed);
    }

    #[test]
    fn affords_is_fail_closed() {
        let e = ext(Some(LintVerdict::Pass));
        assert!(e.affords("--dangerously-skip-permissions"));
        assert!(e.affords("Bash"));
        assert!(!e.affords("--some-flag-not-granted"));
        assert!(!e.affords("Write"));
    }

    #[test]
    fn registry_registers_and_looks_up_by_label() {
        let mut reg = RoleRegistry::new();
        let s = Uuid::new_v4();
        for label in ["role:constellation:mesh-worker", "role:constellation:reviewer"] {
            let (r, _) = RoleEntity::issue(label, s, ext(Some(LintVerdict::Pass)));
            reg.register(r);
        }
        assert_eq!(reg.len(), 2);
        assert_eq!(reg.labels(), vec!["role:constellation:mesh-worker", "role:constellation:reviewer"]);
        assert!(reg.get("role:constellation:mesh-worker").is_some());
        assert!(reg.get("role:constellation:nope").is_none());
    }

    #[test]
    fn extension_serde_round_trips_the_ontology_shape() {
        let e = ext(Some(LintVerdict::Pass));
        let json = serde_json::to_string(&e).unwrap();
        let back: RoleExtension = serde_json::from_str(&json).unwrap();
        assert_eq!(e, back);
        // driftMark strings match the ontology's provisional enum exactly.
        assert_eq!(serde_json::to_string(&DriftMark::DriftUnattributed).unwrap(), "\"drift:unattributed\"");
        assert_eq!(serde_json::to_string(&DriftMark::AuthorViolation).unwrap(), "\"author:violation\"");
    }
}
