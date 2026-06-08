// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Chapter law — typed representation + YAML parsing + validation.
//!
//! Implements the schema in `web4-standard/core-spec/chapter-law-schema.md`
//! (Legion's Track U sub-item U3, web4@08213d1). The hub holds law as a
//! typed Rust struct in memory + as a signed YAML file in chapter storage.
//! Operators edit YAML; the hub validates, signs, and (eventually)
//! compiles to canonical RDF for cross-chapter exchange.
//!
//! ## V2-8 scope split
//!
//! - **Step 1 (this module)**: types + YAML parser + structural validator.
//!   Pure library, no PolicyEntity integration yet.
//! - Step 2: signed law storage + LawAmended ChapterEvent for audit trail.
//! - Step 3: evaluator — given (Law, R6Request) → Decision.
//! - Step 4: PolicyEntity integration in REST + MCP act handlers.
//!
//! ## Architecture commitment #1: law always signed + auditable
//!
//! Law in storage is signed; amendments go through the ledger as
//! LawAmended acts. The hub binary contains NO policy — it's a law
//! interpreter that reads the chapter's signed law and applies it.

use anyhow::{anyhow, Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashSet;

/// A chapter's law document. Parsed from YAML, validated structurally,
/// (later) compiled to canonical RDF for exchange.
///
/// Wire shape matches `chapter-law-schema.md` §1 exactly. Backward-
/// compatible field additions use `#[serde(default)]`.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Law {
    pub version: String,

    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub norms: Vec<Norm>,

    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub procedures: Vec<Procedure>,

    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delegation: Option<DelegationPolicy>,

    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub escalation: Vec<EscalationTrigger>,

    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub admission: Option<AdmissionPolicy>,

    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub atp_issuance: Option<AtpIssuancePolicy>,

    /// Community-defined custom predicates (per §4 extension mechanism).
    /// Not yet evaluated — V2-8 Step 3 may add a hook.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub custom_predicates: Vec<CustomPredicate>,
}

/// A single norm — the atomic unit of law. Triggered when `selector`
/// matched against a value, applies `operator` + `value`, returns
/// `decision`. Higher `priority` wins on conflicts (default 0).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Norm {
    pub id: String,
    pub selector: String,
    pub operator: Operator,
    /// Norm-specific value — strings, numbers, bools all accepted via
    /// untyped serde::Value. The evaluator (V2-8 Step 3) coerces based
    /// on the selector + operator.
    pub value: serde_yaml::Value,
    pub decision: Decision,
    #[serde(default)]
    pub priority: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Decision {
    Allow,
    Deny,
    Escalate,
}

/// Per schema §2 rule 4: one of `<=`, `>=`, `==`, `!=`, `<`, `>`, `in`,
/// `not_in`, `matches`. Renamed to Rust-idiomatic enum names with
/// serde aliases for the symbol forms.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub enum Operator {
    #[serde(rename = "<=")]
    Le,
    #[serde(rename = ">=")]
    Ge,
    #[serde(rename = "==")]
    Eq,
    #[serde(rename = "!=")]
    Ne,
    #[serde(rename = "<")]
    Lt,
    #[serde(rename = ">")]
    Gt,
    #[serde(rename = "in")]
    In,
    #[serde(rename = "not_in")]
    NotIn,
    #[serde(rename = "matches")]
    Matches,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Procedure {
    pub id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub requires_witnesses: Option<u32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub requires_quorum: Option<u32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub applies_to: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DelegationPolicy {
    pub max_depth: i64,
    #[serde(default)]
    pub requires_approval: bool,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub allowed_roles: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EscalationTrigger {
    pub condition: String,
    pub escalate_to: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AdmissionPolicy {
    #[serde(default)]
    pub open: bool,
    #[serde(default)]
    pub requires_sponsor: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sponsor_role: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub min_trust_score: Option<f64>,
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

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CustomPredicate {
    pub id: String,
    pub sub_predicate_of: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

/// Known SocietyRole names per web4-core. Used by §2 validation
/// rules 7, 8, 9, 10. Kept as a free list (not the SocietyRole enum
/// directly) so law files can reference future custom roles without
/// the validator rejecting them — but the canonical Web4 roles are
/// enforced for the role-typed fields.
const KNOWN_ROLES: &[&str] = &[
    "sovereign",
    "law_oracle",
    "policy_entity",
    "treasurer",
    "administrator",
    "archivist",
    "citizen",
    "witness",
    "auditor",
];

impl Law {
    /// Parse a YAML law document. Returns the typed Law on success.
    /// Run `Law::validate()` separately for structural checks.
    pub fn from_yaml(s: &str) -> Result<Self> {
        serde_yaml::from_str(s).context("parsing chapter law YAML")
    }

    /// Serialize back to YAML for storage / display.
    pub fn to_yaml(&self) -> Result<String> {
        serde_yaml::to_string(self).context("serializing chapter law to YAML")
    }

    /// Validate per `chapter-law-schema.md` §2 rules 1-10. Errors loudly
    /// on the first failure — operators want one clear message per fix,
    /// not a tower of warnings.
    pub fn validate(&self) -> Result<()> {
        // Rule 1: version is a semver string.
        if self.version.is_empty() {
            return Err(anyhow!("law.version is required (semver string)"));
        }
        if semver::Version::parse(&self.version).is_err() {
            return Err(anyhow!(
                "law.version '{}' is not a valid semver string (e.g. \"1.0.0\")",
                self.version
            ));
        }

        // Rules 2 + 3 + 4: norms shape (id, selector, operator, value,
        // decision required; decision + operator are typed enums so
        // serde already rejected bad values during parse).
        // Rule 5: norm ids unique within the file.
        let mut seen_ids = HashSet::new();
        for norm in &self.norms {
            if norm.id.is_empty() {
                return Err(anyhow!("norm has empty id"));
            }
            if norm.selector.is_empty() {
                return Err(anyhow!("norm '{}' has empty selector", norm.id));
            }
            if !seen_ids.insert(norm.id.clone()) {
                return Err(anyhow!("duplicate norm id '{}'", norm.id));
            }
        }

        // Rule 6: delegation.max_depth >= 0.
        if let Some(d) = &self.delegation {
            if d.max_depth < 0 {
                return Err(anyhow!(
                    "delegation.max_depth must be >= 0 (got {})", d.max_depth
                ));
            }
            // Rule 7: delegation.allowed_roles entries are valid SocietyRole names.
            for role in &d.allowed_roles {
                if !is_known_role(role) {
                    return Err(anyhow!(
                        "delegation.allowed_roles contains unknown role '{}' \
                         (known: {})",
                        role, KNOWN_ROLES.join(", ")
                    ));
                }
            }
        }

        // Rule 8: escalation[].escalate_to is a valid role.
        for esc in &self.escalation {
            if !is_known_role(&esc.escalate_to) {
                return Err(anyhow!(
                    "escalation[].escalate_to '{}' is not a known role \
                     (known: {})",
                    esc.escalate_to, KNOWN_ROLES.join(", ")
                ));
            }
            if esc.condition.is_empty() {
                return Err(anyhow!("escalation trigger has empty condition"));
            }
        }

        // Rule 9: admission.sponsor_role is a valid role (if set).
        if let Some(a) = &self.admission {
            if let Some(role) = &a.sponsor_role {
                if !is_known_role(role) {
                    return Err(anyhow!(
                        "admission.sponsor_role '{}' is not a known role \
                         (known: {})",
                        role, KNOWN_ROLES.join(", ")
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

        // Rule 10: atp_issuance.mint_authority is a valid role (if set).
        if let Some(a) = &self.atp_issuance {
            if !is_known_role(&a.mint_authority) {
                return Err(anyhow!(
                    "atp_issuance.mint_authority '{}' is not a known role \
                     (known: {})",
                    a.mint_authority, KNOWN_ROLES.join(", ")
                ));
            }
            if a.max_mint_per_cycle < 0 {
                return Err(anyhow!(
                    "atp_issuance.max_mint_per_cycle must be >= 0 (got {})",
                    a.max_mint_per_cycle
                ));
            }
        }

        // Procedure ids unique too (parallel to rule 5).
        let mut proc_ids = HashSet::new();
        for proc in &self.procedures {
            if proc.id.is_empty() {
                return Err(anyhow!("procedure has empty id"));
            }
            if !proc_ids.insert(proc.id.clone()) {
                return Err(anyhow!("duplicate procedure id '{}'", proc.id));
            }
        }

        Ok(())
    }

    /// Parse + validate in one call. Most operators want this.
    pub fn parse_and_validate(yaml: &str) -> Result<Self> {
        let law = Self::from_yaml(yaml)?;
        law.validate()?;
        Ok(law)
    }
}

fn is_known_role(role: &str) -> bool {
    KNOWN_ROLES.contains(&role.to_lowercase().as_str())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The canonical example from chapter-law-schema.md §1.
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

    #[test]
    fn canonical_example_parses_and_validates() {
        let law = Law::parse_and_validate(EXAMPLE_LAW)
            .expect("canonical example from schema doc must parse + validate");
        assert_eq!(law.version, "1.0.0");
        assert_eq!(law.norms.len(), 2);
        assert_eq!(law.procedures.len(), 2);
        assert_eq!(law.escalation.len(), 2);
        assert!(law.delegation.is_some());
        assert!(law.admission.is_some());
        assert!(law.atp_issuance.is_some());
    }

    #[test]
    fn round_trip_yaml() {
        let original = Law::from_yaml(EXAMPLE_LAW).unwrap();
        let yaml = original.to_yaml().unwrap();
        let reparsed = Law::from_yaml(&yaml).unwrap();
        assert_eq!(reparsed.version, original.version);
        assert_eq!(reparsed.norms.len(), original.norms.len());
        assert_eq!(reparsed.procedures.len(), original.procedures.len());
    }

    #[test]
    fn empty_version_rejected() {
        let yaml = r#"
version: ""
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("version"));
    }

    #[test]
    fn bad_semver_rejected() {
        let yaml = r#"
version: "not-a-semver"
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
        let err = format!("{:?}", result.unwrap_err());
        assert!(err.contains("semver"));
    }

    #[test]
    fn duplicate_norm_id_rejected() {
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

    #[test]
    fn unknown_role_in_delegation_rejected() {
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

    #[test]
    fn negative_max_depth_rejected() {
        let yaml = r#"
version: "1.0.0"
delegation:
  max_depth: -1
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
    }

    #[test]
    fn unknown_role_in_escalation_rejected() {
        let yaml = r#"
version: "1.0.0"
escalation:
  - condition: "x > 1"
    escalate_to: not_a_role
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
    }

    #[test]
    fn unknown_role_in_atp_issuance_rejected() {
        let yaml = r#"
version: "1.0.0"
atp_issuance:
  mint_authority: bogus
  max_mint_per_cycle: 100
"#;
        let result = Law::parse_and_validate(yaml);
        assert!(result.is_err());
    }

    #[test]
    fn min_trust_out_of_range_rejected() {
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

    #[test]
    fn bad_operator_rejected_during_parse() {
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

    #[test]
    fn bad_decision_rejected_during_parse() {
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

    #[test]
    fn minimal_law_validates() {
        let yaml = r#"
version: "0.1.0"
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        assert_eq!(law.norms.len(), 0);
        assert!(law.delegation.is_none());
    }

    #[test]
    fn duplicate_procedure_id_rejected() {
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

    #[test]
    fn role_names_are_case_insensitive() {
        let yaml = r#"
version: "1.0.0"
delegation:
  max_depth: 1
  allowed_roles:
    - Sovereign
    - ADMINISTRATOR
"#;
        let law = Law::parse_and_validate(yaml).unwrap();
        assert_eq!(law.delegation.as_ref().unwrap().allowed_roles.len(), 2);
    }
}
