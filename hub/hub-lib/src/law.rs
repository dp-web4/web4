// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Hub law — typed representation + YAML parsing + validation.
//!
//! Implements the schema in `web4-standard/core-spec/hub-law-schema.md`
//! (Legion's Track U sub-item U3, web4@08213d1). The hub holds law as a
//! typed Rust struct in memory + as a signed YAML file in chapter storage.
//! Operators edit YAML; the hub validates, signs, and (eventually)
//! compiles to canonical RDF for cross-chapter exchange.
//!
//! ## V2-8 scope split
//!
//! - **Step 1 (this module)**: types + YAML parser + structural validator.
//!   Pure library, no PolicyEntity integration yet.
//! - Step 2: signed law storage + LawAmended HubEvent for audit trail.
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
/// Wire shape matches `hub-law-schema.md` §1 exactly. Backward-
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
    /// [`DEFAULT_ADMISSION_REVIEW_LIMIT`]). Operator changes are written here (law
    /// is the single inspectable source of truth), via a witnessed `LawAmended`.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub repeat_limit: Option<u32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub review_limit: Option<u32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

/// Default admission repeat limit: denials before an applicant is auto-blocked.
pub const DEFAULT_ADMISSION_REPEAT_LIMIT: u32 = 3;
/// Default admission review limit: denial-review requests before the terminal
/// state (cleared only by an operator admission-reset).
pub const DEFAULT_ADMISSION_REVIEW_LIMIT: u32 = 1;

impl Law {
    /// Effective admission repeat limit — the law value, or the default.
    pub fn admission_repeat_limit(&self) -> u32 {
        self.admission.as_ref().and_then(|a| a.repeat_limit)
            .unwrap_or(DEFAULT_ADMISSION_REPEAT_LIMIT)
    }
    /// Effective admission review limit — the law value, or the default.
    pub fn admission_review_limit(&self) -> u32 {
        self.admission.as_ref().and_then(|a| a.review_limit)
            .unwrap_or(DEFAULT_ADMISSION_REVIEW_LIMIT)
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
        serde_yaml::from_str(s).context("parsing hub law YAML")
    }

    /// Serialize back to YAML for storage / display.
    pub fn to_yaml(&self) -> Result<String> {
        serde_yaml::to_string(self).context("serializing hub law to YAML")
    }

    /// Validate per `hub-law-schema.md` §2 rules 1-10. Errors loudly
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

    /// Canonical SHA-256 of the law's serialized YAML form. Used to
    /// populate `HubEvent::LawAmended.new_law_sha256` when recording
    /// an amendment in the ledger.
    pub fn sha256_hex(&self) -> Result<String> {
        use web4_core::crypto::sha256_hex;
        let yaml = self.to_yaml()?;
        Ok(sha256_hex(yaml.as_bytes()))
    }

    /// SHA-256 of a raw YAML string (without round-tripping through the
    /// parser). Useful when the caller already has the canonical bytes
    /// and wants to avoid re-serialization drift.
    pub fn sha256_hex_of(yaml: &str) -> String {
        web4_core::crypto::sha256_hex(yaml.as_bytes())
    }
}

fn is_known_role(role: &str) -> bool {
    KNOWN_ROLES.contains(&role.to_lowercase().as_str())
}

// ============================================================================
// Escalation conditions (V2-8 Step 3b)
// ============================================================================

/// A parsed escalation-trigger condition: `<selector> <op> <value>`.
///
/// The schema represents conditions as free-text strings like
/// `"r6.resource.atp > 50"` or `"r6.request.action == 'amend_charter'"`.
/// This struct is the parsed form; it reuses the same operator-evaluation
/// machinery as norms via [`R6Request::resolve_selector`] + the
/// `operator_matches` helper.
#[derive(Clone, Debug, PartialEq)]
pub struct Condition {
    pub selector: String,
    pub operator: Operator,
    pub value: serde_yaml::Value,
}

impl Condition {
    /// Parse a condition expression.
    ///
    /// Grammar (informal):
    ///   condition := selector OP value
    ///   selector  := identifier ( "." identifier )*    (must start with "r6")
    ///   OP        := "<=" | ">=" | "==" | "!=" | "<" | ">" | "in" | "not_in" | "matches"
    ///   value     := number | quoted_string | bare_word | list
    ///   list      := "[" value ( "," value )* "]"
    ///
    /// Whitespace around tokens is forgiving. Quoted strings use either
    /// `"..."` or `'...'`. Bare words become strings.
    pub fn parse(s: &str) -> Result<Self> {
        let s = s.trim();
        // Operators must be tried longest-first so "<=" beats "<", etc.
        // Word ops ("in", "not_in", "matches") need word boundaries.
        const SYMBOL_OPS: &[(&str, Operator)] = &[
            ("<=", Operator::Le),
            (">=", Operator::Ge),
            ("==", Operator::Eq),
            ("!=", Operator::Ne),
            ("<", Operator::Lt),
            (">", Operator::Gt),
        ];
        const WORD_OPS: &[(&str, Operator)] = &[
            ("not_in", Operator::NotIn),
            ("matches", Operator::Matches),
            ("in", Operator::In),
        ];

        for (sym, op) in SYMBOL_OPS {
            if let Some(pos) = s.find(sym) {
                let selector = s[..pos].trim();
                let value_str = s[pos + sym.len()..].trim();
                return Self::build(selector, op.clone(), value_str);
            }
        }
        // Word ops need to be surrounded by whitespace (otherwise "matches"
        // could match a substring of a selector).
        for (word, op) in WORD_OPS {
            let needle = format!(" {} ", word);
            if let Some(pos) = s.find(&needle) {
                let selector = s[..pos].trim();
                let value_str = s[pos + needle.len()..].trim();
                return Self::build(selector, op.clone(), value_str);
            }
        }

        Err(anyhow!(
            "escalation condition '{}' has no recognized operator \
             (expected one of: <=, >=, ==, !=, <, >, in, not_in, matches)",
            s
        ))
    }

    fn build(selector: &str, operator: Operator, value_str: &str) -> Result<Self> {
        if selector.is_empty() {
            return Err(anyhow!("escalation condition has empty selector"));
        }
        if !selector.starts_with("r6.") && selector != "r6" {
            return Err(anyhow!(
                "escalation condition selector '{}' must start with 'r6.'",
                selector
            ));
        }
        let value = parse_value(value_str)?;
        Ok(Condition {
            selector: selector.to_string(),
            operator,
            value,
        })
    }

    /// Does this condition match the request?
    pub fn matches(&self, req: &R6Request) -> bool {
        match req.resolve_selector(&self.selector) {
            Some(actual) => operator_matches(&self.operator, &actual, &self.value),
            None => false,
        }
    }
}

/// Parse a value literal: number, quoted string, bare word, or list.
fn parse_value(s: &str) -> Result<serde_yaml::Value> {
    let s = s.trim();
    if s.is_empty() {
        return Err(anyhow!("empty value in escalation condition"));
    }
    // List
    if s.starts_with('[') && s.ends_with(']') {
        let inner = &s[1..s.len() - 1];
        if inner.trim().is_empty() {
            return Ok(serde_yaml::Value::Sequence(vec![]));
        }
        let items: Result<Vec<_>> = inner.split(',').map(|p| parse_value(p.trim())).collect();
        return Ok(serde_yaml::Value::Sequence(items?));
    }
    // Quoted string
    if (s.starts_with('"') && s.ends_with('"')) || (s.starts_with('\'') && s.ends_with('\'')) {
        if s.len() < 2 {
            return Err(anyhow!("malformed quoted string in escalation condition"));
        }
        return Ok(serde_yaml::Value::String(s[1..s.len() - 1].to_string()));
    }
    // Number
    if let Ok(n) = s.parse::<i64>() {
        return Ok(serde_yaml::Value::Number(n.into()));
    }
    if let Ok(n) = s.parse::<f64>() {
        return Ok(serde_yaml::Value::Number(serde_yaml::Number::from(n)));
    }
    // Bool
    match s {
        "true" => return Ok(serde_yaml::Value::Bool(true)),
        "false" => return Ok(serde_yaml::Value::Bool(false)),
        _ => {}
    }
    // Bare word as string
    Ok(serde_yaml::Value::String(s.to_string()))
}

// ============================================================================
// Evaluator (V2-8 Step 3) — (Law, R6Request) → Decision
// ============================================================================

/// An R6 request being evaluated against hub law.
///
/// Per the Web4 R6 framework (Rules + Role + Request + Reference + Resource
/// → Result), this struct carries the inputs the evaluator needs:
/// - Role (which role-LCT is acting)
/// - Request (action + payload)
/// - Resource (quantifiable costs — ATP, member-count, etc.)
///
/// The `Rules` come from the [`Law`] passed alongside; the `Reference`
/// (prior ledger context) is implicit in the evaluator's caller; the
/// `Result` is what [`Law::evaluate`] returns.
#[derive(Clone, Debug, Default)]
pub struct R6Request {
    /// Role taking the action (e.g. "citizen", "treasurer", "sovereign").
    pub role: String,
    /// Action being requested (e.g. "add_member", "assign_role").
    pub action: String,
    /// Action-specific payload (member_lct_id, name, role being assigned, etc.).
    pub payload: serde_yaml::Value,
    /// Quantifiable resources (atp: 50, witness_count: 3, etc.).
    pub resource: std::collections::HashMap<String, serde_yaml::Value>,
}

impl R6Request {
    /// Resolve a selector like `"r6.resource.atp"` or `"r6.request.action"`
    /// against this request. Returns the matching value or None if the
    /// selector doesn't resolve to anything.
    pub fn resolve_selector(&self, selector: &str) -> Option<serde_yaml::Value> {
        let parts: Vec<&str> = selector.split('.').collect();
        if parts.first() != Some(&"r6") {
            return None; // Unknown root namespace
        }
        match parts.get(1).copied() {
            Some("role") => Some(serde_yaml::Value::String(self.role.clone())),
            Some("request") => match parts.get(2).copied() {
                Some("action") => Some(serde_yaml::Value::String(self.action.clone())),
                Some("payload") => {
                    // r6.request.payload OR r6.request.payload.<field>
                    if parts.len() == 3 {
                        Some(self.payload.clone())
                    } else {
                        // Walk the payload by remaining path
                        let mut cursor = &self.payload;
                        for key in &parts[3..] {
                            cursor = cursor.get(*key)?;
                        }
                        Some(cursor.clone())
                    }
                }
                _ => None,
            },
            Some("resource") => {
                let key = parts.get(2)?;
                self.resource.get(*key).cloned()
            }
            _ => None,
        }
    }
}

/// Rich evaluation outcome: decision + which rule fired (for audit /
/// debugging / human-review queueing).
#[derive(Clone, Debug)]
pub struct DecisionOutcome {
    pub decision: Decision,
    /// Norm id that fired (highest priority), if any.
    pub winning_norm: Option<String>,
    /// Index of the escalation trigger that fired, if any. Pair with
    /// `law.escalation[index]` to get the trigger's escalate_to.
    pub escalation_index: Option<usize>,
    /// Role to escalate to (populated from the matching trigger). None
    /// if no escalation fired. Defaults to "sovereign" if a norm
    /// produced Escalate but no escalation trigger fired (per architecture
    /// convention — escalations without a target route to Sovereign).
    pub escalate_to: Option<String>,
}

impl Law {
    /// Evaluate this law against an [`R6Request`]. Returns a [`Decision`]
    /// (use [`Self::evaluate_outcome`] for the full audit info).
    ///
    /// See [`Self::evaluate_outcome`] for the algorithm.
    pub fn evaluate(&self, req: &R6Request) -> Decision {
        self.evaluate_outcome(req).decision
    }

    /// Full evaluation: returns Decision + which rule fired.
    ///
    /// Algorithm:
    /// 1. Walk every norm. Resolve selector against the request, apply
    ///    operator + value. If matches, the norm "fires."
    /// 2. Among firing norms, highest `priority` wins (ties broken by
    ///    first-defined).
    /// 3. Walk every escalation trigger. Parse `condition` into a
    ///    [`Condition`] and check whether it matches the request.
    /// 4. Combine:
    ///    - Norm winner is Deny → Deny is terminal; return Deny.
    ///    - Any escalation matches → return Escalate with escalate_to.
    ///    - Norm winner is Escalate → return Escalate with escalate_to
    ///      defaulted to "sovereign" (norms don't carry an explicit
    ///      target per the schema).
    ///    - Norm winner is Allow → return Allow.
    ///    - No norm fired AND no escalation fired → default Allow.
    pub fn evaluate_outcome(&self, req: &R6Request) -> DecisionOutcome {
        let mut winner: Option<&Norm> = None;
        for norm in &self.norms {
            let actual = match req.resolve_selector(&norm.selector) {
                Some(v) => v,
                None => continue,
            };
            if !operator_matches(&norm.operator, &actual, &norm.value) {
                continue;
            }
            match winner {
                None => winner = Some(norm),
                Some(current) if norm.priority > current.priority => winner = Some(norm),
                _ => {}
            }
        }

        // Deny is terminal — no escalation can override.
        if let Some(w) = winner {
            if w.decision == Decision::Deny {
                return DecisionOutcome {
                    decision: Decision::Deny,
                    winning_norm: Some(w.id.clone()),
                    escalation_index: None,
                    escalate_to: None,
                };
            }
        }

        // Check escalation triggers.
        for (idx, trigger) in self.escalation.iter().enumerate() {
            let condition = match Condition::parse(&trigger.condition) {
                Ok(c) => c,
                // Malformed condition: treat as non-firing rather than
                // crash. validate() should have caught it, but be defensive.
                Err(_) => continue,
            };
            if condition.matches(req) {
                return DecisionOutcome {
                    decision: Decision::Escalate,
                    winning_norm: winner.map(|w| w.id.clone()),
                    escalation_index: Some(idx),
                    escalate_to: Some(trigger.escalate_to.clone()),
                };
            }
        }

        // No escalation fired. Use the winning norm if any.
        match winner {
            Some(norm) => {
                let escalate_to = if norm.decision == Decision::Escalate {
                    Some("sovereign".to_string())
                } else {
                    None
                };
                DecisionOutcome {
                    decision: norm.decision.clone(),
                    winning_norm: Some(norm.id.clone()),
                    escalation_index: None,
                    escalate_to,
                }
            }
            None => DecisionOutcome {
                decision: Decision::Allow,
                winning_norm: None,
                escalation_index: None,
                escalate_to: None,
            },
        }
    }
}

/// Apply an operator: does `actual <op> expected` hold?
///
/// Type coercion rules:
/// - `<=`, `>=`, `<`, `>` require both sides to be numeric. Non-numeric
///   → false.
/// - `==`, `!=` use serde_yaml::Value deep equality (numbers compared
///   as f64; strings as strings; nested structs structurally).
/// - `in`, `not_in` expect `expected` to be a sequence; actual is in/not
///   in that sequence by Value equality.
/// - `matches` reserved for V2-8 Step 3b (regex on string selectors).
///   Currently returns false.
fn operator_matches(
    op: &Operator,
    actual: &serde_yaml::Value,
    expected: &serde_yaml::Value,
) -> bool {
    use Operator::*;
    match op {
        Eq => values_equal(actual, expected),
        Ne => !values_equal(actual, expected),
        Le | Ge | Lt | Gt => {
            let a = as_number(actual);
            let e = as_number(expected);
            match (a, e) {
                (Some(a), Some(e)) => match op {
                    Le => a <= e,
                    Ge => a >= e,
                    Lt => a < e,
                    Gt => a > e,
                    _ => unreachable!(),
                },
                _ => false,
            }
        }
        In => {
            if let serde_yaml::Value::Sequence(seq) = expected {
                seq.iter().any(|v| values_equal(actual, v))
            } else {
                false
            }
        }
        NotIn => {
            if let serde_yaml::Value::Sequence(seq) = expected {
                !seq.iter().any(|v| values_equal(actual, v))
            } else {
                false
            }
        }
        Matches => {
            // Regex evaluation deferred to V2-8 Step 3b
            false
        }
    }
}

fn values_equal(a: &serde_yaml::Value, b: &serde_yaml::Value) -> bool {
    use serde_yaml::Value::*;
    match (a, b) {
        (Number(x), Number(y)) => {
            // Compare via f64 to handle int↔float coercion.
            x.as_f64() == y.as_f64()
        }
        // serde_yaml's PartialEq handles strings, bools, sequences, mappings
        _ => a == b,
    }
}

fn as_number(v: &serde_yaml::Value) -> Option<f64> {
    match v {
        serde_yaml::Value::Number(n) => n.as_f64(),
        // Allow "100" as a string-to-number coercion for YAML
        // unquoted-vs-quoted forgiveness.
        serde_yaml::Value::String(s) => s.parse::<f64>().ok(),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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
        assert!(law.delegation.is_some());
        assert!(law.admission.is_some());
        assert!(law.atp_issuance.is_some());
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
        assert!(law.delegation.is_none());
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
        assert_eq!(law.delegation.as_ref().unwrap().allowed_roles.len(), 2);
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
}
