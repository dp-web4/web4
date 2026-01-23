// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-only
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. A royalty-free license is granted
// under AGPL-3.0 terms for non-commercial and research use.
// For commercial licensing: dp@metalinxx.io
// See PATENTS.md for details.

//! Value Tensor (V3) Implementation
//!
//! V3 is a 6-dimensional value tensor that captures the multi-faceted nature
//! of value exchange in Web4. It complements T3 by measuring what an entity
//! contributes rather than how trustworthy they are.
//!
//! Dimensions:
//! 1. Utility - practical usefulness of contributions
//! 2. Novelty - originality and uniqueness of contributions
//! 3. Quality - craftsmanship and attention to detail
//! 4. Timeliness - delivery within appropriate timeframes
//! 5. Relevance - alignment with current needs and context
//! 6. Leverage - multiplicative effect on others' capabilities

use crate::error::{Result, Web4Error};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Number of dimensions in the value tensor
pub const V3_DIMENSIONS: usize = 6;

/// The six dimensions of value
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[repr(usize)]
pub enum ValueDimension {
    /// Practical usefulness of contributions
    Utility = 0,
    /// Originality and uniqueness of contributions
    Novelty = 1,
    /// Craftsmanship and attention to detail
    Quality = 2,
    /// Delivery within appropriate timeframes
    Timeliness = 3,
    /// Alignment with current needs and context
    Relevance = 4,
    /// Multiplicative effect on others' capabilities
    Leverage = 5,
}

impl ValueDimension {
    /// Get all dimensions in order
    pub fn all() -> [ValueDimension; V3_DIMENSIONS] {
        [
            ValueDimension::Utility,
            ValueDimension::Novelty,
            ValueDimension::Quality,
            ValueDimension::Timeliness,
            ValueDimension::Relevance,
            ValueDimension::Leverage,
        ]
    }

    /// Get the dimension name
    pub fn name(&self) -> &'static str {
        match self {
            ValueDimension::Utility => "utility",
            ValueDimension::Novelty => "novelty",
            ValueDimension::Quality => "quality",
            ValueDimension::Timeliness => "timeliness",
            ValueDimension::Relevance => "relevance",
            ValueDimension::Leverage => "leverage",
        }
    }
}

/// A 6-dimensional value tensor
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct V3 {
    /// Value scores for each dimension (0.0 to 1.0)
    dimensions: [f64; V3_DIMENSIONS],

    /// Confidence weights for each dimension (0.0 to 1.0)
    weights: [f64; V3_DIMENSIONS],

    /// Number of observations contributing to each dimension
    observation_counts: [u64; V3_DIMENSIONS],
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
        }
    }

    /// Create a V3 with specific initial scores
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
        })
    }

    /// Get the score for a specific dimension
    pub fn score(&self, dimension: ValueDimension) -> f64 {
        self.dimensions[dimension as usize]
    }

    /// Get the weight (confidence) for a specific dimension
    pub fn weight(&self, dimension: ValueDimension) -> f64 {
        self.weights[dimension as usize]
    }

    /// Get all dimension scores
    pub fn scores(&self) -> &[f64; V3_DIMENSIONS] {
        &self.dimensions
    }

    /// Get all weights
    pub fn weights(&self) -> &[f64; V3_DIMENSIONS] {
        &self.weights
    }

    /// Record an observation for a dimension
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

        result
    }

    /// Apply time decay
    pub fn decay(&mut self, decay_factor: f64) {
        for i in 0..V3_DIMENSIONS {
            let distance_from_neutral = self.dimensions[i] - 0.5;
            self.dimensions[i] = 0.5 + distance_from_neutral * decay_factor;
            self.weights[i] *= decay_factor;
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
        v3.observe(ValueDimension::Utility, 1.0).unwrap();

        assert!(v3.score(ValueDimension::Utility) > 0.5);
        assert!(v3.weight(ValueDimension::Utility) > 0.0);
    }

    #[test]
    fn test_specialized_aggregate() {
        let mut v3 = V3::new();

        // High scores in utility and quality
        for _ in 0..10 {
            v3.observe(ValueDimension::Utility, 0.9).unwrap();
            v3.observe(ValueDimension::Quality, 0.9).unwrap();
        }

        // Low scores in novelty
        for _ in 0..10 {
            v3.observe(ValueDimension::Novelty, 0.2).unwrap();
        }

        // Specialized in utility+quality should be high
        let specialized = v3.specialized_aggregate(&[ValueDimension::Utility, ValueDimension::Quality]);
        assert!(specialized > 0.8);

        // Overall aggregate includes novelty, so lower
        assert!(v3.aggregate() < specialized);
    }

    #[test]
    fn test_trust_value_combined() {
        let mut tv = TrustValueScore::new(Uuid::new_v4());

        // Build up good trust and value
        for _ in 0..10 {
            tv.trust.observe(crate::t3::TrustDimension::Competence, 0.9).unwrap();
            tv.value.observe(ValueDimension::Utility, 0.9).unwrap();
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
}
