// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-or-later

//! R6/R7 Action Framework
//!
//! R6: Rules + Role + Request + Reference + Resource → Result
//! R7: Rules + Role + Request + Reference + Resource → Result + Reputation
//!
//! R6 is for low-consequence actions (cheap). R7 adds explicit reputation
//! tracking for consequential actions. Both are canonical; R7 extends R6.
//!
//! Key invariants:
//! - Determinism: same inputs → identical results across implementations
//! - Non-repudiation: all actions signed, recorded with witnesses
//! - Resource bounds: consumption cannot exceed pre-declared limits
//! - Role isolation: actions scoped to role's permissions
//! - Atomic settlement: transfers and tensor updates fully complete or roll back
//!
//! Reference: `web4-standard/core-spec/r6-framework.md`,
//!            `web4-standard/core-spec/r7-framework.md`

use crate::crypto::sha256_hex;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

// ── R6 Components ───────────────────────────────────────────────────

/// Rules governing an action — law reference + constraints + permissions.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Rules {
    /// SHA-256 of the governing law document
    pub law_hash: String,
    /// Society LCT that issued these rules
    pub society: String,
    /// Constraints (rate limits, ATP minimums, witness requirements)
    pub constraints: Vec<Constraint>,
    /// Permitted action types
    pub permissions: Vec<String>,
    /// Forbidden action types
    pub prohibitions: Vec<String>,
}

impl Rules {
    pub fn has_permission(&self, action: &str) -> bool {
        if self.prohibitions.iter().any(|p| p == action || p == "*") {
            return false;
        }
        self.permissions.is_empty() || self.permissions.iter().any(|p| p == action || p == "*")
    }
}

/// A constraint on action execution.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Constraint {
    /// Constraint type (e.g., "rate_limit", "min_atp", "witness_quorum")
    pub constraint_type: String,
    /// Threshold value
    pub threshold: f64,
    /// Whether this constraint is hard (blocks) or soft (warns)
    pub hard: bool,
}

/// Role context for an action — who is acting, in what capacity.
/// Reputation is ROLE-CONTEXTUALIZED, never global.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ActionRole {
    /// Entity LCT ID (who is acting)
    pub actor_lct: String,
    /// Role LCT ID (in what capacity — domain-specific)
    pub role_lct: String,
    /// When this role pairing was established
    pub paired_at: DateTime<Utc>,
}

/// Request — the action being requested.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Request {
    /// Action verb (e.g., "file_write", "deploy", "analyze_dataset")
    pub action: String,
    /// Target entity or resource
    pub target: String,
    /// Action-specific parameters
    pub parameters: HashMap<String, serde_json::Value>,
    /// ATP staked on outcome (the *energy* resource committed to the action).
    pub atp_stake: f64,
    /// Deadline staked on outcome (the *time* resource — the temporal twin of
    /// `atp_stake`). `None` = no temporal accountability. A typed promotion of
    /// the legacy free-text `constraints["deadline"]`. See [`crate::time`].
    #[serde(default)]
    pub deadline: Option<crate::time::Deadline>,
    /// Unique request nonce
    pub nonce: String,
    /// Execution constraints (legacy free-text bag; typed time → `deadline`).
    pub constraints: HashMap<String, serde_json::Value>,
    /// Proof of delegated agency (if acting on behalf of another)
    pub proof_of_agency: Option<ProofOfAgency>,
}

/// Proof that an agent is authorized to act on behalf of a principal.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ProofOfAgency {
    /// Grant ID from the delegation ledger
    pub grant_id: String,
    /// Merkle inclusion proof for the grant
    pub inclusion_proof: String,
    /// Scope of delegation (e.g., "finance:payments")
    pub scope: String,
    /// Resource scopes the agent can access
    pub audience: Vec<String>,
}

/// Reference — precedents, witnesses, and context for the action.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Reference {
    /// Previous similar actions (for precedent-based evaluation)
    pub precedents: Vec<Precedent>,
    /// Markov Relevancy Horizon depth
    pub mrh_depth: u32,
    /// Trust path entities
    pub relevant_entities: Vec<String>,
    /// Witness attestations
    pub witnesses: Vec<WitnessAttestation>,
}

/// A precedent action used for context.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Precedent {
    /// Hash of the precedent action
    pub action_hash: String,
    /// Outcome of the precedent ("success", "failure", etc.)
    pub outcome: String,
    /// Relevance score (0.0 to 1.0)
    pub relevance: f64,
}

/// A witness attestation — signed statement from an independent observer.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct WitnessAttestation {
    /// Witness entity LCT
    pub lct: String,
    /// Attestation status ("verified", "disputed", etc.)
    pub attestation: String,
    /// Ed25519 signature
    pub signature: String,
    /// When the attestation was made
    pub timestamp: DateTime<Utc>,
}

/// Resource requirements for an action.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ResourceRequirements {
    /// ATP needed for this action
    pub required_atp: f64,
    /// Actor's current available ATP
    pub available_atp: f64,
    /// Compute requirements (cpu_seconds, memory_mb, max_duration_s, etc.)
    pub compute: HashMap<String, f64>,
    /// ATP locked during execution
    pub escrow_amount: f64,
    /// Condition for escrow release ("result_verified", "timeout", etc.)
    pub escrow_condition: String,
}

impl ResourceRequirements {
    pub fn has_sufficient_atp(&self) -> bool {
        self.available_atp >= self.required_atp
    }
}

/// Status of an action through its lifecycle.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ActionStatus {
    Pending,
    Validated,
    InProgress,
    Success,
    Failure,
    Error,
}

/// Result of an action execution.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ActionResult {
    /// Current status
    pub status: ActionStatus,
    /// Result data
    pub output: HashMap<String, serde_json::Value>,
    /// SHA-256 of output (for chain integrity)
    pub output_hash: String,
    /// Error message on failure
    pub error: Option<String>,
    /// Actual ATP consumed
    pub atp_consumed: f64,
    /// Actual resources consumed
    pub resource_consumed: HashMap<String, f64>,
    /// Witness attestations on the result
    pub attestations: Vec<WitnessAttestation>,
}

// ── R7 Extension ────────────────────────────────────────────────────

/// Delta to a single trust/value tensor dimension.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TensorDelta {
    /// Change magnitude
    pub change: f64,
    /// Previous value
    pub from_value: f64,
    /// New value
    pub to_value: f64,
}

/// Contributing factor to a reputation change.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ContributingFactor {
    pub factor_type: String,
    pub weight: f64,
    pub description: String,
}

/// R7's first-class reputation output — explicit trust/value delta per action.
///
/// Key: reputation is ROLE-CONTEXTUALIZED. The `role_lct` field determines
/// which MRH role-pairing link this delta applies to. There is no global reputation.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ReputationDelta {
    /// Whose reputation changed
    pub subject_lct: String,
    /// WHICH ROLE CONTEXT (the MRH link, not global)
    pub role_lct: String,
    /// What action caused the change
    pub action_type: String,
    /// Target of the action
    pub action_target: String,
    /// Ledger reference (action ID / tx hash)
    pub action_id: String,
    /// Which rule fired to cause this change
    pub rule_triggered: String,
    /// Human-readable explanation
    pub reason: String,
    /// Per-dimension T3 changes
    pub t3_delta: HashMap<String, TensorDelta>,
    /// Per-dimension V3 changes
    pub v3_delta: HashMap<String, TensorDelta>,
    /// Factors that contributed to this reputation change
    pub contributing_factors: Vec<ContributingFactor>,
    /// Witness attestations on this reputation event
    pub witnesses: Vec<WitnessAttestation>,
    /// When this reputation change occurred
    pub timestamp: DateTime<Utc>,
}

impl ReputationDelta {
    /// Net trust change (sum of all T3 dimension deltas).
    pub fn net_trust_change(&self) -> f64 {
        self.t3_delta.values().map(|d| d.change).sum()
    }

    /// Net value change (sum of all V3 dimension deltas).
    pub fn net_value_change(&self) -> f64 {
        self.v3_delta.values().map(|d| d.change).sum()
    }
}

// ── R7 Action (composite) ───────────────────────────────────────────

/// Complete R7 action — the full R6 cycle plus reputation tracking.
///
/// R6 actions are R7 actions with `reputation: None`.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct R7Action {
    /// Governing rules (law reference + constraints)
    pub rules: Rules,
    /// Role context (who + in what capacity)
    pub role: ActionRole,
    /// The request (what action, on what target)
    pub request: Request,
    /// Context (precedents, witnesses, MRH depth)
    pub reference: Reference,
    /// Resource requirements and escrow
    pub resource: ResourceRequirements,
    /// Execution result
    pub result: ActionResult,
    /// R7: first-class reputation output (None for R6-only actions)
    pub reputation: Option<ReputationDelta>,

    // ── Chain linking ───────────────────────────────────────────
    /// Unique action ID
    pub action_id: String,
    /// Hash of the previous action in this chain
    pub prev_action_hash: String,
    /// When this action was created
    pub timestamp: DateTime<Utc>,
}

impl R7Action {
    /// Create a new R7 action with a fresh ID.
    pub fn new(
        rules: Rules,
        role: ActionRole,
        request: Request,
        reference: Reference,
        resource: ResourceRequirements,
    ) -> Self {
        Self {
            rules,
            role,
            request,
            reference,
            resource,
            result: ActionResult {
                status: ActionStatus::Pending,
                output: HashMap::new(),
                output_hash: String::new(),
                error: None,
                atp_consumed: 0.0,
                resource_consumed: HashMap::new(),
                attestations: Vec::new(),
            },
            reputation: None,
            action_id: Uuid::new_v4().to_string(),
            prev_action_hash: "0".repeat(64),
            timestamp: Utc::now(),
        }
    }

    /// Whether this is an R7 action (has reputation tracking).
    pub fn is_r7(&self) -> bool {
        self.reputation.is_some()
    }

    /// Validate the action before execution. Returns list of validation errors.
    pub fn validate(&self) -> Vec<String> {
        let mut errors = Vec::new();

        // Check permissions
        if !self.rules.has_permission(&self.request.action) {
            errors.push(format!(
                "Action '{}' not permitted under current rules",
                self.request.action
            ));
        }

        // Check resource availability
        if !self.resource.has_sufficient_atp() {
            errors.push(format!(
                "Insufficient ATP: {} < {}",
                self.resource.available_atp, self.resource.required_atp
            ));
        }

        // Check constraints
        for constraint in &self.rules.constraints {
            if constraint.hard && constraint.constraint_type == "min_atp" {
                if self.request.atp_stake < constraint.threshold {
                    errors.push(format!(
                        "ATP stake {} below minimum {}",
                        self.request.atp_stake, constraint.threshold
                    ));
                }
            }
            if constraint.constraint_type == "witness_quorum" {
                if (self.reference.witnesses.len() as f64) < constraint.threshold {
                    errors.push(format!(
                        "Witness quorum not met: {} < {}",
                        self.reference.witnesses.len(),
                        constraint.threshold
                    ));
                }
            }
        }

        errors
    }

    /// Compute the canonical hash for chain integrity.
    pub fn canonical_hash(&self) -> String {
        let canonical = serde_json::json!({
            "action_id": self.action_id,
            "prev_action_hash": self.prev_action_hash,
            "action": self.request.action,
            "target": self.request.target,
            "actor_lct": self.role.actor_lct,
            "role_lct": self.role.role_lct,
            "status": self.result.status,
            "output_hash": self.result.output_hash,
            "timestamp": self.timestamp.to_rfc3339(),
        });
        sha256_hex(canonical.to_string().as_bytes())
    }

    /// Compute reputation delta from a quality score (R7 extension).
    ///
    /// quality: 0.0 to 1.0. Below 0.5 = negative, above 0.5 = positive.
    /// This makes the action an R7 action.
    pub fn compute_reputation(
        &mut self,
        quality: f64,
        rule_triggered: &str,
        reason: &str,
        factors: Vec<ContributingFactor>,
    ) {
        let mut t3_delta = HashMap::new();
        let mut v3_delta = HashMap::new();

        // T3 delta: each dimension shifts proportionally to quality
        let trust_shift = 0.05 * (quality - 0.5); // ±0.025 max per action
        for dim in &["talent", "training", "temperament"] {
            t3_delta.insert(
                dim.to_string(),
                TensorDelta {
                    change: trust_shift,
                    from_value: 0.5, // placeholder — caller should set from actual
                    to_value: (0.5 + trust_shift).clamp(0.0, 1.0),
                },
            );
        }

        // V3 delta: proportional to quality offset
        let value_shift = 0.02 * (quality - 0.5);
        for dim in &["valuation", "veracity", "validity"] {
            v3_delta.insert(
                dim.to_string(),
                TensorDelta {
                    change: value_shift,
                    from_value: 0.5,
                    to_value: (0.5 + value_shift).clamp(0.0, 1.0),
                },
            );
        }

        self.reputation = Some(ReputationDelta {
            subject_lct: self.role.actor_lct.clone(),
            role_lct: self.role.role_lct.clone(),
            action_type: self.request.action.clone(),
            action_target: self.request.target.clone(),
            action_id: self.action_id.clone(),
            rule_triggered: rule_triggered.to_string(),
            reason: reason.to_string(),
            t3_delta,
            v3_delta,
            contributing_factors: factors,
            witnesses: Vec::new(),
            timestamp: Utc::now(),
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_action() -> R7Action {
        R7Action::new(
            Rules {
                law_hash: "sha256:test_law".into(),
                society: "lct:web4:society:test".into(),
                constraints: vec![],
                permissions: vec!["file_read".into(), "file_write".into()],
                prohibitions: vec!["delete_production".into()],
            },
            ActionRole {
                actor_lct: "lct:web4:agent:alice".into(),
                role_lct: "lct:web4:role:developer".into(),
                paired_at: Utc::now(),
            },
            Request {
                action: "file_write".into(),
                target: "src/main.rs".into(),
                parameters: HashMap::new(),
                atp_stake: 10.0,
                deadline: None,
                nonce: Uuid::new_v4().to_string(),
                constraints: HashMap::new(),
                proof_of_agency: None,
            },
            Reference {
                precedents: vec![],
                mrh_depth: 3,
                relevant_entities: vec![],
                witnesses: vec![],
            },
            ResourceRequirements {
                required_atp: 5.0,
                available_atp: 100.0,
                compute: HashMap::new(),
                escrow_amount: 5.0,
                escrow_condition: "result_verified".into(),
            },
        )
    }

    #[test]
    fn test_r6_action_validation() {
        let action = sample_action();
        let errors = action.validate();
        assert!(errors.is_empty(), "Expected no errors, got: {:?}", errors);
        assert!(!action.is_r7());
    }

    #[test]
    fn test_r6_forbidden_action() {
        let mut action = sample_action();
        action.request.action = "delete_production".into();
        let errors = action.validate();
        assert_eq!(errors.len(), 1);
        assert!(errors[0].contains("not permitted"));
    }

    #[test]
    fn test_r7_reputation() {
        let mut action = sample_action();
        action.compute_reputation(0.8, "completion_rule", "Task completed well", vec![]);

        assert!(action.is_r7());
        let rep = action.reputation.as_ref().unwrap();
        assert!(rep.net_trust_change() > 0.0);
        assert!(rep.net_value_change() > 0.0);
        assert_eq!(rep.role_lct, "lct:web4:role:developer");
    }

    #[test]
    fn test_r7_negative_reputation() {
        let mut action = sample_action();
        action.compute_reputation(0.2, "failure_rule", "Task failed", vec![]);

        let rep = action.reputation.as_ref().unwrap();
        assert!(rep.net_trust_change() < 0.0);
        assert!(rep.net_value_change() < 0.0);
    }

    #[test]
    fn test_canonical_hash_determinism() {
        let action = sample_action();
        let hash1 = action.canonical_hash();
        let hash2 = action.canonical_hash();
        assert_eq!(hash1, hash2);
        assert_eq!(hash1.len(), 64); // SHA-256 hex
    }

    #[test]
    fn test_witness_quorum_constraint() {
        let mut action = sample_action();
        action.rules.constraints.push(Constraint {
            constraint_type: "witness_quorum".into(),
            threshold: 2.0,
            hard: true,
        });

        let errors = action.validate();
        assert_eq!(errors.len(), 1);
        assert!(errors[0].contains("Witness quorum"));
    }

    #[test]
    fn test_insufficient_atp() {
        let mut action = sample_action();
        action.resource.available_atp = 1.0;
        action.resource.required_atp = 5.0;

        let errors = action.validate();
        assert!(errors.iter().any(|e| e.contains("Insufficient ATP")));
    }
}
