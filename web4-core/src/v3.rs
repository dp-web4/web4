// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: MIT
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! Value Tensor (V3) Implementation
//!
//! V3 is a 3-dimensional value tensor whose root dimensions are nodes in an
//! open-ended RDF sub-graph. Each root can have any number of sub-dimensions
//! linked via `web4:subDimensionOf`.
//!
//! Root Dimensions:
//! 1. Valuation - subjective worth as perceived by recipients
//! 2. Veracity - truthfulness and accuracy of claims
//! 3. Validity - soundness of reasoning and confirmed value delivery
//!
//! Formal ontology: `web4-standard/ontology/t3v3-ontology.ttl`

use crate::error::{Result, Web4Error};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Number of root dimensions in the value tensor
pub const V3_DIMENSIONS: usize = 3;

/// The three root dimensions of value
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[repr(usize)]
pub enum ValueDimension {
    /// Subjective worth as perceived by recipients
    Valuation = 0,
    /// Truthfulness and accuracy of claims
    Veracity = 1,
    /// Soundness of reasoning and confirmed value delivery
    Validity = 2,
}

impl ValueDimension {
    /// Get all root dimensions in order
    pub fn all() -> [ValueDimension; V3_DIMENSIONS] {
        [
            ValueDimension::Valuation,
            ValueDimension::Veracity,
            ValueDimension::Validity,
        ]
    }

    /// Get the dimension name
    pub fn name(&self) -> &'static str {
        match self {
            ValueDimension::Valuation => "valuation",
            ValueDimension::Veracity => "veracity",
            ValueDimension::Validity => "validity",
        }
    }
}

/// Score data for a sub-dimension
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SubDimensionScore {
    /// Current score (0.0 to 1.0)
    pub score: f64,
    /// Confidence weight
    pub weight: f64,
    /// Number of observations
    pub observation_count: u64,
    /// Which root dimension this is under
    pub parent: ValueDimension,
}

/// A 3-dimensional value tensor with fractal sub-dimension support
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct V3 {
    /// Value scores for each root dimension (0.0 to 1.0)
    dimensions: [f64; V3_DIMENSIONS],

    /// Confidence weights for each root dimension (0.0 to 1.0)
    weights: [f64; V3_DIMENSIONS],

    /// Number of observations contributing to each root dimension
    observation_counts: [u64; V3_DIMENSIONS],

    /// Sub-dimensions keyed by name, linked to root via parent field.
    #[serde(default, skip_serializing_if = "HashMap::is_empty")]
    sub_dimensions: HashMap<String, SubDimensionScore>,
}

impl Default for V3 {
    fn default() -> Self {
        Self::new()
    }
}

impl V3 {
    /// Create a new V3 with neutral value (0.5) and zero confidence
    pub fn new() -> Self {
        Self {
            dimensions: [0.5; V3_DIMENSIONS],
            weights: [0.0; V3_DIMENSIONS],
            observation_counts: [0; V3_DIMENSIONS],
            sub_dimensions: HashMap::new(),
        }
    }

    /// Create a V3 with specific initial root scores
    pub fn with_scores(scores: [f64; V3_DIMENSIONS]) -> Result<Self> {
        for score in scores {
            if !(0.0..=1.0).contains(&score) {
                return Err(Web4Error::InvalidInput(
                    "Value scores must be in range [0.0, 1.0]".into(),
                ));
            }
        }
        Ok(Self {
            dimensions: scores,
            weights: [0.0; V3_DIMENSIONS],
            observation_counts: [0; V3_DIMENSIONS],
            sub_dimensions: HashMap::new(),
        })
    }

    /// Get the score for a root dimension
    pub fn score(&self, dimension: ValueDimension) -> f64 {
        self.dimensions[dimension as usize]
    }

    /// Get the weight (confidence) for a root dimension
    pub fn weight(&self, dimension: ValueDimension) -> f64 {
        self.weights[dimension as usize]
    }

    /// Get all root dimension scores
    pub fn scores(&self) -> &[f64; V3_DIMENSIONS] {
        &self.dimensions
    }

    /// Get all weights
    pub fn weights(&self) -> &[f64; V3_DIMENSIONS] {
        &self.weights
    }

    /// Get sub-dimensions map
    pub fn sub_dimensions(&self) -> &HashMap<String, SubDimensionScore> {
        &self.sub_dimensions
    }

    /// Record an observation for a root dimension
    pub fn observe(&mut self, dimension: ValueDimension, observed_score: f64) -> Result<()> {
        if !(0.0..=1.0).contains(&observed_score) {
            return Err(Web4Error::InvalidInput(
                "Observed score must be in range [0.0, 1.0]".into(),
            ));
        }

        let idx = dimension as usize;
        let count = self.observation_counts[idx];

        // Exponential moving average
        let alpha = 0.5 / (1.0 + (count as f64 / 10.0));
        self.dimensions[idx] = alpha * observed_score + (1.0 - alpha) * self.dimensions[idx];

        // Weight increases logarithmically with observations
        self.observation_counts[idx] += 1;
        self.weights[idx] = (1.0 + self.observation_counts[idx] as f64).ln() / 10.0_f64.ln();
        self.weights[idx] = self.weights[idx].min(1.0);

        Ok(())
    }

    /// Record an observation for a sub-dimension
    pub fn observe_sub_dimension(
        &mut self,
        name: &str,
        parent: ValueDimension,
        observed_score: f64,
    ) -> Result<()> {
        if !(0.0..=1.0).contains(&observed_score) {
            return Err(Web4Error::InvalidInput(
                "Observed score must be in range [0.0, 1.0]".into(),
            ));
        }

        let entry = self.sub_dimensions.entry(name.to_string()).or_insert(
            SubDimensionScore {
                score: 0.5,
                weight: 0.0,
                observation_count: 0,
                parent,
            },
        );

        let alpha = 0.5 / (1.0 + (entry.observation_count as f64 / 10.0));
        entry.score = alpha * observed_score + (1.0 - alpha) * entry.score;
        entry.observation_count += 1;
        entry.weight = (1.0 + entry.observation_count as f64).ln() / 10.0_f64.ln();
        entry.weight = entry.weight.min(1.0);

        Ok(())
    }

    /// Compute the aggregate value score (weighted arithmetic mean)
    ///
    /// Unlike trust (geometric mean), value uses arithmetic mean because
    /// high value in one dimension can partially compensate for lower value
    /// in another (specialization is valid).
    pub fn aggregate(&self) -> f64 {
        let total_weight: f64 = self.weights.iter().sum();
        if total_weight == 0.0 {
            return 0.5;
        }

        let weighted_sum: f64 = self
            .dimensions
            .iter()
            .zip(self.weights.iter())
            .map(|(score, weight)| score * weight)
            .sum();

        weighted_sum / total_weight
    }

    /// Compute specialized value score for specific dimensions
    ///
    /// Allows calculating value in a particular area of expertise
    pub fn specialized_aggregate(&self, dims: &[ValueDimension]) -> f64 {
        let mut total_weight = 0.0;
        let mut weighted_sum = 0.0;

        for dim in dims {
            let idx = *dim as usize;
            total_weight += self.weights[idx];
            weighted_sum += self.dimensions[idx] * self.weights[idx];
        }

        if total_weight == 0.0 {
            return 0.5;
        }

        weighted_sum / total_weight
    }

    /// Merge with another V3
    pub fn merge(&self, other: &V3) -> Self {
        let mut result = Self::new();

        for i in 0..V3_DIMENSIONS {
            let total_count = self.observation_counts[i] + other.observation_counts[i];
            if total_count == 0 {
                continue;
            }

            let self_weight = self.observation_counts[i] as f64 / total_count as f64;
            let other_weight = other.observation_counts[i] as f64 / total_count as f64;

            result.dimensions[i] =
                self_weight * self.dimensions[i] + other_weight * other.dimensions[i];
            result.observation_counts[i] = total_count;
            result.weights[i] = (1.0 + total_count as f64).ln() / 10.0_f64.ln();
            result.weights[i] = result.weights[i].min(1.0);
        }

        // Merge sub-dimensions
        for (name, sub) in &self.sub_dimensions {
            result.sub_dimensions.insert(name.clone(), sub.clone());
        }
        for (name, other_sub) in &other.sub_dimensions {
            if let Some(existing) = result.sub_dimensions.get_mut(name) {
                let total = existing.observation_count + other_sub.observation_count;
                if total > 0 {
                    let w1 = existing.observation_count as f64 / total as f64;
                    let w2 = other_sub.observation_count as f64 / total as f64;
                    existing.score = w1 * existing.score + w2 * other_sub.score;
                    existing.observation_count = total;
                    existing.weight = (1.0 + total as f64).ln() / 10.0_f64.ln();
                    existing.weight = existing.weight.min(1.0);
                }
            } else {
                result.sub_dimensions.insert(name.clone(), other_sub.clone());
            }
        }

        result
    }

    /// Apply time decay
    pub fn decay(&mut self, decay_factor: f64) {
        for i in 0..V3_DIMENSIONS {
            let distance_from_neutral = self.dimensions[i] - 0.5;
            self.dimensions[i] = 0.5 + distance_from_neutral * decay_factor;
            self.weights[i] *= decay_factor;
        }

        for sub in self.sub_dimensions.values_mut() {
            let distance = sub.score - 0.5;
            sub.score = 0.5 + distance * decay_factor;
            sub.weight *= decay_factor;
        }
    }
}

/// A value contribution observation
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ValueObservation {
    /// The observer's LCT ID
    pub observer_id: Uuid,

    /// The contributor's LCT ID
    pub contributor_id: Uuid,

    /// The dimension being observed
    pub dimension: ValueDimension,

    /// The observed score (0.0 to 1.0)
    pub score: f64,

    /// Context/reason for the observation
    pub context: String,

    /// Timestamp of the observation
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

impl ValueObservation {
    /// Create a new value observation
    pub fn new(
        observer_id: Uuid,
        contributor_id: Uuid,
        dimension: ValueDimension,
        score: f64,
        context: impl Into<String>,
    ) -> Result<Self> {
        if !(0.0..=1.0).contains(&score) {
            return Err(Web4Error::InvalidInput(
                "Score must be in range [0.0, 1.0]".into(),
            ));
        }
        Ok(Self {
            observer_id,
            contributor_id,
            dimension,
            score,
            context: context.into(),
            timestamp: chrono::Utc::now(),
        })
    }
}

/// Combined trust-value score
///
/// Represents the overall quality of an entity's participation in Web4.
/// High trust + high value = highly sought collaborator.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TrustValueScore {
    /// The entity's LCT ID
    pub entity_id: Uuid,

    /// Trust tensor
    pub trust: crate::t3::T3,

    /// Value tensor
    pub value: V3,
}

impl TrustValueScore {
    /// Create a new trust-value score
    pub fn new(entity_id: Uuid) -> Self {
        Self {
            entity_id,
            trust: crate::t3::T3::new(),
            value: V3::new(),
        }
    }

    /// Compute combined score
    ///
    /// Uses geometric mean of trust and value aggregates,
    /// because both are required for meaningful collaboration.
    pub fn combined(&self) -> f64 {
        let trust_agg = self.trust.aggregate();
        let value_agg = self.value.aggregate();
        (trust_agg * value_agg).sqrt()
    }

    /// Check if entity meets minimum requirements for a role
    pub fn meets_requirements(
        &self,
        min_trust: f64,
        min_value: f64,
        min_combined: f64,
    ) -> bool {
        self.trust.aggregate() >= min_trust
            && self.value.aggregate() >= min_value
            && self.combined() >= min_combined
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_v3_is_neutral() {
        let v3 = V3::new();
        assert_eq!(v3.aggregate(), 0.5);
        for dim in ValueDimension::all() {
            assert_eq!(v3.score(dim), 0.5);
            assert_eq!(v3.weight(dim), 0.0);
        }
    }

    #[test]
    fn test_observation_updates_score() {
        let mut v3 = V3::new();
        v3.observe(ValueDimension::Valuation, 1.0).unwrap();

        assert!(v3.score(ValueDimension::Valuation) > 0.5);
        assert!(v3.weight(ValueDimension::Valuation) > 0.0);
    }

    #[test]
    fn test_specialized_aggregate() {
        let mut v3 = V3::new();

        // High scores in valuation and validity
        for _ in 0..10 {
            v3.observe(ValueDimension::Valuation, 0.9).unwrap();
            v3.observe(ValueDimension::Validity, 0.9).unwrap();
        }

        // Low scores in veracity
        for _ in 0..10 {
            v3.observe(ValueDimension::Veracity, 0.2).unwrap();
        }

        // Specialized in valuation+validity should be high
        let specialized =
            v3.specialized_aggregate(&[ValueDimension::Valuation, ValueDimension::Validity]);
        assert!(specialized > 0.8);

        // Overall aggregate includes veracity, so lower
        assert!(v3.aggregate() < specialized);
    }

    #[test]
    fn test_trust_value_combined() {
        let mut tv = TrustValueScore::new(Uuid::new_v4());

        // Build up good trust and value
        for _ in 0..10 {
            tv.trust
                .observe(crate::t3::TrustDimension::Talent, 0.9)
                .unwrap();
            tv.value.observe(ValueDimension::Valuation, 0.9).unwrap();
        }

        assert!(tv.combined() > 0.5);
    }

    #[test]
    fn test_requirements_check() {
        let tv = TrustValueScore::new(Uuid::new_v4());

        // No observations = neutral = 0.5
        assert!(tv.meets_requirements(0.5, 0.5, 0.5));
        assert!(!tv.meets_requirements(0.6, 0.5, 0.5));
    }

    #[test]
    fn test_sub_dimension_observation() {
        let mut v3 = V3::new();

        v3.observe_sub_dimension("market_demand", ValueDimension::Valuation, 0.85)
            .unwrap();

        let subs = v3.sub_dimensions();
        assert_eq!(subs.len(), 1);
        assert!(subs["market_demand"].score > 0.5);
        assert_eq!(subs["market_demand"].parent, ValueDimension::Valuation);
    }
}
