// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Web4 shared policy substrate — the domain-agnostic Law/PolicyEntity engine.
//!
//! Step-2 joint extraction (RFC #419 `shared policy/identity substrate`). This
//! crate carries the **generic** R6 policy engine lifted out of the hub's
//! `hub-lib/src/law.rs`, with the society-specific pieces (admission, council,
//! role vocabulary) left to the consuming domain via [`PolicyExtension`]:
//!
//! - `web4-core` → `web4-policy` → `{hub society, hestia constellation, hardbound RBAC/TPM}`
//!
//! ## What's here (generic)
//! - [`Law<E>`] — version + norms + procedures + escalation + a typed,
//!   `#[serde(flatten)]`-ed domain extension `E: PolicyExtension`.
//! - [`Norm`] / [`Decision`] / [`Operator`] / [`Procedure`] / [`EscalationTrigger`]
//! - [`Condition`] + [`R6Request`] — the predicate engine + R6 selector namespace.
//! - [`Law::evaluate`] / [`Law::evaluate_outcome`] — priority-ordered conflict
//!   resolution, default-Allow.
//! - [`Law::hydrate_defaults`] — self-populating-defaults mechanism (delegates the
//!   *what* to the extension; per hub web4 #417).
//! - structural [`Law::validate`] (id-uniqueness, version semver, escalation shape).
//!
//! ## What the domain supplies ([`PolicyExtension`])
//! Per-domain policy shape (e.g. hub's `AdmissionPolicy`/`DelegationPolicy`),
//! per-domain role vocabulary in `validate`, and per-domain code-defaults in
//! `hydrate_defaults`. Open-valued dynamism lives in a field *inside* the typed
//! extension (e.g. a `serde_yaml::Value`/map field), not an untyped top-level bag
//! (RFC #419 Q5 — verified to fit hub society + hestia constellation + hardbound RBAC).

use anyhow::{anyhow, Context, Result};
use serde::{de::DeserializeOwned, Deserialize, Serialize};
use std::collections::HashSet;

/// Per-domain specialization of the generic [`Law`]. Carries the domain's
/// policy shape (flattened into the law's wire form), its validation vocabulary,
/// and its code-defaults.
///
/// The engine ([`Law::evaluate`]) never touches `E` — it operates only on the
/// generic `norms`/`escalation`. `E` is policy *shape* (what an operator can set);
/// identity/role-trust is a *separate* surface (RFC #419 Q2), not part of `E`.
pub trait PolicyExtension:
    Clone + std::fmt::Debug + Default + Serialize + DeserializeOwned
{
    /// Domain-specific validation. Receives the full [`Law`] so the extension can
    /// validate role-typed references that live on the *generic* engine (e.g.
    /// `escalation[].escalate_to`) against its own role vocabulary, in addition
    /// to its own fields. Error loudly on the first failure (one fix per message).
    fn validate(&self, law: &Law<Self>) -> Result<()>;

    /// Fill domain code-defaults into any unset law-driven field. Returns `true`
    /// iff anything changed, so the caller persists + witnesses **only on change**
    /// (idempotent — a second hydrate is a no-op). See [`Law::hydrate_defaults`].
    fn hydrate_defaults(&mut self) -> bool;
}

/// The empty extension — a pure policy engine with no domain specialization.
/// `Law<NoExtension>` is the generic engine usable standalone (and the natural
/// default for consumers that only need norms/escalation).
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct NoExtension {}

impl PolicyExtension for NoExtension {
    fn validate(&self, _law: &Law<Self>) -> Result<()> {
        Ok(())
    }
    fn hydrate_defaults(&mut self) -> bool {
        false
    }
}

/// A policy law document, generic over a domain extension `E`.
///
/// The generic fields (`version`, `norms`, `procedures`, `escalation`,
/// `custom_predicates`) are the engine's; `ext` is `#[serde(flatten)]`-ed so the
/// **wire form stays flat** — a hub law still serializes as
/// `{version, norms, …, delegation, admission, atp_issuance}` with the society
/// fields coming from `HubPolicy`. This preserves byte-compatibility with signed,
/// hash-chained law already on disk (the extraction is wire-neutral).
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(bound(serialize = "E: Serialize", deserialize = "E: DeserializeOwned"))]
pub struct Law<E: PolicyExtension = NoExtension> {
    pub version: String,

    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub norms: Vec<Norm>,

    /// Response rules (W4IP N3) — the second-person, post-recognition side.
    /// Parsed and validated; NOT evaluated or enacted by this engine (see
    /// [`ResponseRule`]). `skip_serializing_if` keeps existing signed laws
    /// byte-identical on round-trip (wire-neutral addition).
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub responses: Vec<ResponseRule>,

    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub procedures: Vec<Procedure>,

    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub escalation: Vec<EscalationTrigger>,

    /// Community-defined custom predicates (generic extension list; not yet
    /// evaluated — a future evaluator hook).
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub custom_predicates: Vec<CustomPredicate>,

    /// Domain policy, flattened into the law's top-level wire form.
    #[serde(flatten)]
    pub ext: E,
}

/// A single norm — the atomic unit of law. When `selector` resolves and
/// `operator`+`value` match, the norm "fires" with `decision`. Higher `priority`
/// wins on conflicts (default 0).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Norm {
    pub id: String,
    pub selector: String,
    pub operator: Operator,
    /// Norm-specific value — strings, numbers, bools via untyped serde::Value;
    /// the evaluator coerces based on selector + operator.
    pub value: serde_yaml::Value,
    pub decision: Decision,
    #[serde(default)]
    pub priority: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

/// A single response rule — the response side's parallel to [`Norm`]
/// (W4IP N3, hub-law-schema.md "Response vocabulary"). Same rule anatomy,
/// different verb field: where a norm's `decision` answers the first-person,
/// pre-act question (*may this act I am requesting proceed?*), a response
/// rule's `response` names the second-person, post-recognition act (*what does
/// the society do about a target's witnessed act?*). Selectors range over
/// recognition evidence (e.g. `reputation.delta.category`), NOT the pre-act
/// `r6.*` namespace — deliberately disjoint vocabularies so gate rules cannot
/// silently emit responses.
///
/// **Parse-don't-enact:** this engine parses and validates response rules; it
/// does NOT evaluate or enact them. [`Law::evaluate_outcome`] never reads
/// `responses` — every rung's enactment is individually ratified and lands as
/// its own reviewed surface. The vocabulary exists so law can be drafted and
/// reviewed against it before any machinery can act on it.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ResponseRule {
    pub id: String,
    pub selector: String,
    pub operator: Operator,
    pub value: serde_yaml::Value,
    pub response: Response,
    #[serde(default)]
    pub priority: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

/// The response vocabulary (W4IP N3): the graded ladder plus the kinetic
/// class. Every enacted response is an R7 act whose required evidence and veto
/// scale with the rung's `ConsequenceClass` — the ladder IS S and V applied to
/// responses. The kinetic verbs name existing scattered primitives (slash_atp,
/// citizenship suspend/terminate, LCT revocation, CRISIS halt) so law can cite
/// them uniformly; naming them creates no new enactment authority.
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Response {
    /// Formal, witnessed notification to the target that a recognition delta
    /// has accrued against it. Does not interfere with the target's ability
    /// to act. (Ratified first-rung name — `notice` is second-person by
    /// construction; gate `warn` is first-person pre-act and stays disjoint.)
    Notice,
    /// Reversible containment of the target's interaction surface pending
    /// adjudication. MUST be liftable by the same authority that imposed it —
    /// an unliftable containment is not quarantine and belongs to the kinetic
    /// class instead.
    Quarantine,
    /// Restorative: undo or compensate the violation's effects.
    Correct,
    /// The return path: earned restoration of standing against a rehab-bound.
    Rehabilitate,
    /// Kinetic: ATP stake slashing (`atp-adp-cycle.md` slash_atp).
    Slash,
    /// Kinetic: citizenship suspension (SOCIETY_SPECIFICATION §4.2).
    Suspend,
    /// Kinetic: LCT/credential revocation (LCT spec revocation record).
    Revoke,
    /// Kinetic: citizenship termination (SOCIETY_SPECIFICATION §4.2).
    Terminate,
    /// Kinetic: CRISIS motor-halt (entity-types.md "halt effectors").
    Halt,
}

impl Response {
    /// Whether this verb belongs to the kinetic class — responses that
    /// interfere with the target's ability to act. Kinetic verbs are valid to
    /// PARSE but law-inert: nothing in this crate (or its consumers, until a
    /// rung's enactment is individually ratified) may enact them.
    pub fn is_kinetic(self) -> bool {
        matches!(
            self,
            Response::Slash
                | Response::Suspend
                | Response::Revoke
                | Response::Terminate
                | Response::Halt
        )
    }

    /// The ladder rung's `ConsequenceClass` (referenced-acts §4), which scales
    /// the required evidence and veto for enactment. `None` for the kinetic
    /// class: those verbs cite primitives whose consequence semantics live
    /// with their source specs, and per the governing invariant an
    /// unclassified consequential surface defaults to high-consequence —
    /// callers MUST NOT read `None` as "unclassified therefore mild".
    pub fn consequence_class(self) -> Option<web4_core::ConsequenceClass> {
        use web4_core::ConsequenceClass::*;
        match self {
            Response::Notice => Some(Reversible),
            Response::Quarantine => Some(Reversible),
            Response::Correct => Some(Costly),
            Response::Rehabilitate => Some(Reversible),
            _ => None,
        }
    }
}

/// The outcome of policy evaluation. `Allow` and `Warn` are non-blocking (the
/// action proceeds); `Deny` and `Escalate` block. `Warn` is a non-blocking
/// flagged-allow — "allowed, but noteworthy" — a genuine fourth outcome, not a
/// flag on `Allow`: it keeps the advisory inside the resolved decision where the
/// engine already arbitrates by priority. The advisory text rides the winning
/// norm's existing `description`, surfaced via `winning_norm` in `DecisionOutcome`
/// (no hot-path field). Three consumers need it — society, hardbound audit, and
/// the hestia constellation, where it is already deployed feeding `EntityTrust`
/// as a live risk signal.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Decision {
    /// Proceed silently.
    Allow,
    /// Proceed, but flag the action as noteworthy (non-blocking advisory).
    Warn,
    /// Block the action (terminal).
    Deny,
    /// Block pending a higher authority's decision.
    Escalate,
}

/// One of `<=`, `>=`, `==`, `!=`, `<`, `>`, `in`, `not_in`, `matches`.
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
pub struct EscalationTrigger {
    pub condition: String,
    pub escalate_to: String,
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

impl<E: PolicyExtension> Law<E> {
    /// Parse a YAML law document. Run [`Self::validate`] separately for checks.
    pub fn from_yaml(s: &str) -> Result<Self> {
        serde_yaml::from_str(s).context("parsing policy law YAML")
    }

    /// Serialize back to YAML for storage / display.
    pub fn to_yaml(&self) -> Result<String> {
        serde_yaml::to_string(self).context("serializing policy law to YAML")
    }

    /// Structural validation (engine-generic) + the domain's
    /// [`PolicyExtension::validate`]. Errors loudly on the first failure.
    ///
    /// Generic rules here: version semver; norm shape + id-uniqueness; escalation
    /// condition non-empty; procedure id-uniqueness. Role-vocabulary checks
    /// (e.g. `escalate_to` is a known role) live in the extension, which receives
    /// `self` so it can see the generic `escalation`.
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

        // Rules 2-5: norm shape + id-uniqueness.
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

        // Response rules (W4IP N3): same shape rules as norms, own id
        // namespace. Kinetic verbs are valid to parse (parse-don't-enact);
        // there is deliberately NO verb-level rejection here.
        let mut response_ids = HashSet::new();
        for rule in &self.responses {
            if rule.id.is_empty() {
                return Err(anyhow!("response rule has empty id"));
            }
            if rule.selector.is_empty() {
                return Err(anyhow!("response rule '{}' has empty selector", rule.id));
            }
            if rule.selector.starts_with("r6.") || rule.selector == "r6" {
                return Err(anyhow!(
                    "response rule '{}' selects over the pre-act r6 namespace — \
                     response selectors range over recognition evidence \
                     (e.g. reputation.delta.category); the vocabularies are \
                     deliberately disjoint",
                    rule.id
                ));
            }
            if !response_ids.insert(rule.id.clone()) {
                return Err(anyhow!("duplicate response rule id '{}'", rule.id));
            }
        }

        // Escalation structural shape (the generic half — the role-vocabulary
        // check on escalate_to is the extension's, per RFC #419 Q3).
        for esc in &self.escalation {
            if esc.condition.is_empty() {
                return Err(anyhow!("escalation trigger has empty condition"));
            }
        }

        // Procedure ids unique (parallel to rule 5).
        let mut proc_ids = HashSet::new();
        for proc in &self.procedures {
            if proc.id.is_empty() {
                return Err(anyhow!("procedure has empty id"));
            }
            if !proc_ids.insert(proc.id.clone()) {
                return Err(anyhow!("duplicate procedure id '{}'", proc.id));
            }
        }

        // Domain-specific validation (admission/delegation/atp roles, etc.).
        self.ext.validate(self)
    }

    /// Parse + validate in one call.
    pub fn parse_and_validate(yaml: &str) -> Result<Self> {
        let law = Self::from_yaml(yaml)?;
        law.validate()?;
        Ok(law)
    }

    /// Canonical SHA-256 of the law's serialized YAML form (for
    /// `LawAmended.new_law_sha256`).
    pub fn sha256_hex(&self) -> Result<String> {
        let yaml = self.to_yaml()?;
        Ok(web4_core::crypto::sha256_hex(yaml.as_bytes()))
    }

    /// SHA-256 of a raw YAML string (no round-trip through the parser).
    pub fn sha256_hex_of(yaml: &str) -> String {
        web4_core::crypto::sha256_hex(yaml.as_bytes())
    }

    /// **Hydrate code-defaults into the law** by delegating to the domain
    /// extension. For every law-driven parameter with a code default but no
    /// explicit value, the extension writes the default in so the law inspectably
    /// carries every effective setting (new parameters auto-populate on first boot
    /// — no per-parameter maintenance). Returns `true` iff anything was filled, so
    /// the caller persists + witnesses **only on change** (idempotent).
    pub fn hydrate_defaults(&mut self) -> bool {
        self.ext.hydrate_defaults()
    }
}

// ============================================================================
// Escalation conditions
// ============================================================================

/// A parsed escalation-trigger condition: `<selector> <op> <value>`.
#[derive(Clone, Debug, PartialEq)]
pub struct Condition {
    pub selector: String,
    pub operator: Operator,
    pub value: serde_yaml::Value,
}

impl Condition {
    /// Parse a condition expression: `selector OP value` (selector must start
    /// with `r6`). Whitespace forgiving; quoted strings `"..."`/`'...'`; lists
    /// `[a, b]`; bare words become strings.
    pub fn parse(s: &str) -> Result<Self> {
        let s = s.trim();
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

/// Parse a value literal: number, quoted string, bare word, bool, or list.
fn parse_value(s: &str) -> Result<serde_yaml::Value> {
    let s = s.trim();
    if s.is_empty() {
        return Err(anyhow!("empty value in escalation condition"));
    }
    if s.starts_with('[') && s.ends_with(']') {
        let inner = &s[1..s.len() - 1];
        if inner.trim().is_empty() {
            return Ok(serde_yaml::Value::Sequence(vec![]));
        }
        let items: Result<Vec<_>> = inner.split(',').map(|p| parse_value(p.trim())).collect();
        return Ok(serde_yaml::Value::Sequence(items?));
    }
    if (s.starts_with('"') && s.ends_with('"')) || (s.starts_with('\'') && s.ends_with('\'')) {
        if s.len() < 2 {
            return Err(anyhow!("malformed quoted string in escalation condition"));
        }
        return Ok(serde_yaml::Value::String(s[1..s.len() - 1].to_string()));
    }
    if let Ok(n) = s.parse::<i64>() {
        return Ok(serde_yaml::Value::Number(n.into()));
    }
    if let Ok(n) = s.parse::<f64>() {
        return Ok(serde_yaml::Value::Number(serde_yaml::Number::from(n)));
    }
    match s {
        "true" => return Ok(serde_yaml::Value::Bool(true)),
        "false" => return Ok(serde_yaml::Value::Bool(false)),
        _ => {}
    }
    Ok(serde_yaml::Value::String(s.to_string()))
}

// ============================================================================
// Evaluator — (Law, R6Request) → Decision
// ============================================================================

/// An R6 request being evaluated against policy law.
///
/// Carries Role (which role-LCT is acting), Request (action + payload), and
/// Resource (quantifiable costs). `role` is a plain `String` — the engine holds
/// **no** domain/role vocabulary; that lives in the extension.
#[derive(Clone, Debug, Default)]
pub struct R6Request {
    /// Role taking the action (e.g. "citizen", "treasurer", "sovereign").
    pub role: String,
    /// Action being requested (e.g. "add_member", "assign_role").
    pub action: String,
    /// Action-specific payload.
    pub payload: serde_yaml::Value,
    /// Quantifiable resources (atp: 50, witness_count: 3, …).
    pub resource: std::collections::HashMap<String, serde_yaml::Value>,
}

impl R6Request {
    /// Resolve a selector like `"r6.resource.atp"` or `"r6.request.action"`.
    pub fn resolve_selector(&self, selector: &str) -> Option<serde_yaml::Value> {
        let parts: Vec<&str> = selector.split('.').collect();
        if parts.first() != Some(&"r6") {
            return None;
        }
        match parts.get(1).copied() {
            Some("role") => Some(serde_yaml::Value::String(self.role.clone())),
            Some("request") => match parts.get(2).copied() {
                Some("action") => Some(serde_yaml::Value::String(self.action.clone())),
                Some("payload") => {
                    if parts.len() == 3 {
                        Some(self.payload.clone())
                    } else {
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

/// Rich evaluation outcome: decision + which rule fired (for audit / review).
#[derive(Clone, Debug)]
pub struct DecisionOutcome {
    pub decision: Decision,
    /// Norm id that fired (highest priority), if any.
    pub winning_norm: Option<String>,
    /// Index of the escalation trigger that fired, if any.
    pub escalation_index: Option<usize>,
    /// Role to escalate to. None if no escalation. Defaults to "sovereign" if a
    /// norm produced Escalate but no escalation trigger fired.
    pub escalate_to: Option<String>,
}

impl<E: PolicyExtension> Law<E> {
    /// Evaluate this law against an [`R6Request`]. See [`Self::evaluate_outcome`].
    pub fn evaluate(&self, req: &R6Request) -> Decision {
        self.evaluate_outcome(req).decision
    }

    /// Full evaluation: Decision + which rule fired.
    ///
    /// 1. Walk norms; among those that fire, highest `priority` wins (ties → first).
    /// 2. Deny is terminal (Warn is NOT — a winning Warn proceeds, like Allow).
    /// 3. Else walk escalation triggers; first match → Escalate.
    /// 4. Else the winning norm's decision — Warn/Allow proceed; Escalate defaults escalate_to=sovereign.
    /// 5. No norm + no escalation → default Allow.
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

        for (idx, trigger) in self.escalation.iter().enumerate() {
            let condition = match Condition::parse(&trigger.condition) {
                Ok(c) => c,
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

/// Apply an operator: does `actual <op> expected` hold? (Comparisons require
/// numerics; `==`/`!=` deep-equality; `in`/`not_in` over sequences; `matches`
/// reserved — currently false.)
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
        Matches => false,
    }
}

fn values_equal(a: &serde_yaml::Value, b: &serde_yaml::Value) -> bool {
    use serde_yaml::Value::*;
    match (a, b) {
        (Number(x), Number(y)) => x.as_f64() == y.as_f64(),
        _ => a == b,
    }
}

fn as_number(v: &serde_yaml::Value) -> Option<f64> {
    match v {
        serde_yaml::Value::Number(n) => n.as_f64(),
        serde_yaml::Value::String(s) => s.parse::<f64>().ok(),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn req(role: &str, action: &str) -> R6Request {
        R6Request {
            role: role.to_string(),
            action: action.to_string(),
            ..Default::default()
        }
    }

    #[test]
    fn no_norms_default_allow() {
        let law: Law = Law::from_yaml("version: \"1.0.0\"").unwrap();
        assert_eq!(law.evaluate(&req("citizen", "anything")), Decision::Allow);
    }

    #[test]
    fn deny_is_terminal_over_escalate() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: deny_high_atp
    selector: r6.resource.atp
    operator: ">"
    value: 100
    decision: deny
    priority: 10
"#;
        let law: Law = Law::parse_and_validate(yaml).unwrap();
        let mut r = req("citizen", "spend");
        r.resource
            .insert("atp".into(), serde_yaml::Value::Number(150.into()));
        assert_eq!(law.evaluate(&r), Decision::Deny);
    }

    #[test]
    fn priority_breaks_conflicts() {
        let yaml = r#"
version: "1.0.0"
norms:
  - id: allow_join
    selector: r6.request.action
    operator: "=="
    value: join
    decision: allow
    priority: 1
  - id: escalate_join
    selector: r6.request.action
    operator: "=="
    value: join
    decision: escalate
    priority: 5
"#;
        let law: Law = Law::parse_and_validate(yaml).unwrap();
        assert_eq!(law.evaluate(&req("external", "join")), Decision::Escalate);
    }

    #[test]
    fn warn_is_non_terminal_and_proceeds() {
        // A winning Warn norm returns Warn and does NOT block — same non-blocking
        // shape as Allow (escalate_to = None), unlike Deny/Escalate.
        let yaml = r#"
version: "1.0.0"
norms:
  - id: warn_risky
    selector: r6.request.action
    operator: "=="
    value: risky
    decision: warn
    priority: 5
    description: "allowed, but noteworthy"
"#;
        let law: Law = Law::parse_and_validate(yaml).unwrap();
        let out = law.evaluate_outcome(&req("citizen", "risky"));
        assert_eq!(out.decision, Decision::Warn);
        assert_eq!(out.escalate_to, None);
        assert_eq!(out.winning_norm.as_deref(), Some("warn_risky"));
    }

    #[test]
    fn higher_priority_warn_beats_lower_priority_deny() {
        // Priority semantics unchanged: the Deny-terminal check fires only when Deny
        // WINS. A higher-priority Warn wins outright, so the lower Deny never triggers
        // the terminal block — the action proceeds with Warn.
        let yaml = r#"
version: "1.0.0"
norms:
  - id: deny_low
    selector: r6.request.action
    operator: "=="
    value: act
    decision: deny
    priority: 1
  - id: warn_high
    selector: r6.request.action
    operator: "=="
    value: act
    decision: warn
    priority: 5
"#;
        let law: Law = Law::parse_and_validate(yaml).unwrap();
        assert_eq!(law.evaluate(&req("citizen", "act")), Decision::Warn);
    }

    #[test]
    fn flatten_keeps_wire_shape() {
        // A NoExtension law round-trips; flatten adds no spurious fields.
        let law: Law = Law::from_yaml("version: \"1.0.0\"\nnorms: []").unwrap();
        let y = law.to_yaml().unwrap();
        assert!(y.contains("version"));
        let back: Law = Law::from_yaml(&y).unwrap();
        assert_eq!(back.version, "1.0.0");
    }

    #[test]
    fn responses_parse_all_nine_verbs_including_kinetic() {
        // Parse-don't-enact: the validator MUST accept a law whose response
        // rules use kinetic verbs (they are law-inert, not law-invalid).
        let yaml = r#"
version: "1.0.0"
responses:
  - id: NOTICE-ON-DELTA
    selector: reputation.delta.category
    operator: "=="
    value: coercive_extractive
    response: notice
    priority: 1
  - {id: R-QUARANTINE, selector: reputation.delta.category, operator: "==", value: x, response: quarantine}
  - {id: R-CORRECT,    selector: reputation.delta.category, operator: "==", value: x, response: correct}
  - {id: R-REHAB,      selector: reputation.delta.category, operator: "==", value: x, response: rehabilitate}
  - {id: R-SLASH,      selector: reputation.delta.category, operator: "==", value: x, response: slash}
  - {id: R-SUSPEND,    selector: reputation.delta.category, operator: "==", value: x, response: suspend}
  - {id: R-REVOKE,     selector: reputation.delta.category, operator: "==", value: x, response: revoke}
  - {id: R-TERMINATE,  selector: reputation.delta.category, operator: "==", value: x, response: terminate}
  - {id: R-HALT,       selector: reputation.delta.category, operator: "==", value: x, response: halt}
"#;
        let law: Law = Law::parse_and_validate(yaml).unwrap();
        assert_eq!(law.responses.len(), 9);
        assert_eq!(law.responses[0].response, Response::Notice);
        assert_eq!(law.responses[0].priority, 1);
        // Ladder vs kinetic split + consequence classes (referenced-acts §4).
        use web4_core::ConsequenceClass::*;
        assert!(!Response::Notice.is_kinetic());
        assert!(!Response::Quarantine.is_kinetic());
        assert!(!Response::Correct.is_kinetic());
        assert!(!Response::Rehabilitate.is_kinetic());
        for k in [Response::Slash, Response::Suspend, Response::Revoke, Response::Terminate, Response::Halt] {
            assert!(k.is_kinetic());
            assert_eq!(k.consequence_class(), None, "kinetic class defers to source primitives");
        }
        assert_eq!(Response::Notice.consequence_class(), Some(Reversible));
        assert_eq!(Response::Quarantine.consequence_class(), Some(Reversible));
        assert_eq!(Response::Correct.consequence_class(), Some(Costly));
        assert_eq!(Response::Rehabilitate.consequence_class(), Some(Reversible));
    }

    #[test]
    fn responses_validation_rejects_bad_shapes() {
        // Unknown verb fails at parse (typed enum), not at validate.
        let bad_verb = r#"
version: "1.0.0"
responses:
  - {id: R1, selector: reputation.delta.category, operator: "==", value: x, response: obliterate}
"#;
        assert!(Law::<NoExtension>::from_yaml(bad_verb).is_err());

        // Duplicate response ids rejected.
        let dup = r#"
version: "1.0.0"
responses:
  - {id: R1, selector: reputation.delta.category, operator: "==", value: x, response: notice}
  - {id: R1, selector: reputation.delta.category, operator: "==", value: y, response: notice}
"#;
        let law: Law = Law::from_yaml(dup).unwrap();
        assert!(law.validate().is_err());

        // The vocabularies are disjoint: a response selecting over the
        // pre-act r6 namespace is exactly the first-person/second-person
        // conflation the response side exists to prevent.
        let conflated = r#"
version: "1.0.0"
responses:
  - {id: R1, selector: r6.request.action, operator: "==", value: x, response: notice}
"#;
        let law: Law = Law::from_yaml(conflated).unwrap();
        let err = law.validate().unwrap_err().to_string();
        assert!(err.contains("r6"), "error names the namespace violation: {err}");
    }

    #[test]
    fn responses_are_wire_neutral_and_law_inert() {
        // Wire-neutral: a law without responses round-trips byte-identically
        // (signed, hash-chained laws on disk are unaffected by the new field).
        let old = "version: \"1.0.0\"\nnorms:\n- id: a\n  selector: r6.role\n  operator: ==\n  value: x\n  decision: allow\n";
        let law: Law = Law::from_yaml(old).unwrap();
        assert!(law.responses.is_empty());
        assert!(!law.to_yaml().unwrap().contains("responses"), "absent responses stay absent");

        // Law-inert (parse-don't-enact): the R6 evaluator is blind to response
        // rules — identical laws ± responses produce identical outcomes, even
        // when a response rule's selector text coincides with request fields.
        let with_responses = r#"
version: "1.0.0"
norms:
  - {id: deny_it, selector: r6.request.action, operator: "==", value: risky, decision: deny, priority: 1}
responses:
  - {id: R-HALT, selector: reputation.delta.category, operator: "==", value: anything, response: halt, priority: 999}
"#;
        let law2: Law = Law::parse_and_validate(with_responses).unwrap();
        let r = R6Request { role: "citizen".into(), action: "risky".into(), ..Default::default() };
        let out = law2.evaluate_outcome(&r);
        assert_eq!(out.decision, Decision::Deny);
        assert_eq!(out.winning_norm.as_deref(), Some("deny_it"));
        let allowed = law2.evaluate_outcome(&R6Request { role: "citizen".into(), action: "benign".into(), ..Default::default() });
        assert_eq!(allowed.decision, Decision::Allow, "responses never leak into R6 evaluation");
    }

    #[test]
    fn validate_rejects_bad_version_and_dup_norms() {
        let bad: Law = Law::from_yaml("version: \"not-semver\"").unwrap();
        assert!(bad.validate().is_err());
        let dup = "version: \"1.0.0\"\nnorms:\n  - {id: a, selector: r6.role, operator: \"==\", value: x, decision: allow}\n  - {id: a, selector: r6.role, operator: \"==\", value: y, decision: deny}";
        let law: Law = Law::from_yaml(dup).unwrap();
        assert!(law.validate().is_err());
    }
}
