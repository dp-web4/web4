// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: AGPL-3.0-only
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. A royalty-free license is granted
// under AGPL-3.0 terms for non-commercial and research use.
// For commercial licensing: dp@metalinxx.io
// See PATENTS.md for details.

//! Trust Tensor (T3) Implementation
//!
//! T3 is a 6-dimensional trust tensor that captures the multi-faceted nature
//! of trust in Web4. Each dimension measures a distinct aspect of trustworthiness.
//!
//! Dimensions:
//! 1. Competence - ability to perform claimed capabilities
//! 2. Integrity - consistency between stated and actual behavior
//! 3. Benevolence - intent toward benefit vs harm
//! 4. Predictability - consistency of behavior over time
//! 5. Transparency - visibility into decision-making process
//! 6. Accountability - willingness to accept consequences

use crate::error::{Result, Web4Error};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Number of dimensions in the trust tensor
pub const T3_DIMENSIONS: usize = 6;

/// The six dimensions of trust
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[repr(usize)]
pub enum TrustDimension {
    /// Ability to perform claimed capabilities
    Competence = 0,
    /// Consistency between stated and actual behavior
    Integrity = 1,
    /// Intent toward benefit vs harm
    Benevolence = 2,
    /// Consistency of behavior over time
    Predictability = 3,
    /// Visibility into decision-making process
    Transparency = 4,
    /// Willingness to accept consequences
    Accountability = 5,
}

impl TrustDimension {
    /// Get all dimensions in order
    pub fn all() -> [TrustDimension; T3_DIMENSIONS] {
        [
            TrustDimension::Competence,
            TrustDimension::Integrity,
            TrustDimension::Benevolence,
            TrustDimension::Predictability,
            TrustDimension::Transparency,
            TrustDimension::Accountability,
        ]
    }

    /// Get the dimension name
    pub fn name(&self) -> &'static str {
        match self {
            TrustDimension::Competence => "competence",
            TrustDimension::Integrity => "integrity",
            TrustDimension::Benevolence => "benevolence",
            TrustDimension::Predictability => "predictability",
            TrustDimension::Transparency => "transparency",
            TrustDimension::Accountability => "accountability",
        }
    }
}

/// A 6-dimensional trust tensor
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct T3 {
    /// Trust scores for each dimension (0.0 to 1.0)
    dimensions: [f64; T3_DIMENSIONS],

    /// Confidence weights for each dimension (0.0 to 1.0)
    /// Higher weight = more observations/evidence
    weights: [f64; T3_DIMENSIONS],

    /// Number of observations contributing to each dimension
    observation_counts: [u64; T3_DIMENSIONS],
}

impl Default for T3 {
    fn default() -> Self {
        Self::new()
    }
}

impl T3 {
    /// Create a new T3 with neutral trust (0.5) and zero confidence
    pub fn new() -> Self {
        Self {
            dimensions: [0.5; T3_DIMENSIONS],
            weights: [0.0; T3_DIMENSIONS],
            observation_counts: [0; T3_DIMENSIONS],
        }
    }

    /// Create a T3 with specific initial scores
    pub fn with_scores(scores: [f64; T3_DIMENSIONS]) -> Result<Self> {
        for score in scores {
            if !(0.0..=1.0).contains(&score) {
                return Err(Web4Error::InvalidInput(
                    "Trust scores must be in range [0.0, 1.0]".into(),
                ));
            }
        }
        Ok(Self {
            dimensions: scores,
            weights: [0.0; T3_DIMENSIONS],
            observation_counts: [0; T3_DIMENSIONS],
        })
    }

    /// Get the score for a specific dimension
    pub fn score(&self, dimension: TrustDimension) -> f64 {
        self.dimensions[dimension as usize]
    }

    /// Get the weight (confidence) for a specific dimension
    pub fn weight(&self, dimension: TrustDimension) -> f64 {
        self.weights[dimension as usize]
    }

    /// Get all dimension scores
    pub fn scores(&self) -> &[f64; T3_DIMENSIONS] {
        &self.dimensions
    }

    /// Get all weights
    pub fn weights(&self) -> &[f64; T3_DIMENSIONS] {
        &self.weights
    }

    /// Record an observation for a dimension
    ///
    /// Uses exponential moving average with decay factor based on observation count
    pub fn observe(&mut self, dimension: TrustDimension, observed_score: f64) -> Result<()> {
        if !(0.0..=1.0).contains(&observed_score) {
            return Err(Web4Error::InvalidInput(
                "Observed score must be in range [0.0, 1.0]".into(),
            ));
        }

        let idx = dimension as usize;
        let count = self.observation_counts[idx];

        // Exponential moving average: new = α * observed + (1-α) * old
        // α starts high (0.5) and decreases as more observations accumulate
        let alpha = 0.5 / (1.0 + (count as f64 / 10.0));
        self.dimensions[idx] = alpha * observed_score + (1.0 - alpha) * self.dimensions[idx];

        // Weight increases logarithmically with observations, capped at 1.0
        self.observation_counts[idx] += 1;
        self.weights[idx] = (1.0 + self.observation_counts[idx] as f64).ln() / 10.0_f64.ln();
        self.weights[idx] = self.weights[idx].min(1.0);

        Ok(())
    }

    /// Compute the aggregate trust score (weighted geometric mean)
    ///
    /// Geometric mean ensures that a zero in any dimension zeros the total,
    /// reflecting that trust requires all dimensions to be positive.
    pub fn aggregate(&self) -> f64 {
        let total_weight: f64 = self.weights.iter().sum();
        if total_weight == 0.0 {
            return 0.5; // No observations, return neutral
        }

        // Weighted geometric mean
        let log_sum: f64 = self
            .dimensions
            .iter()
            .zip(self.weights.iter())
            .map(|(score, weight)| {
                // Add small epsilon to avoid log(0)
                weight * (score + 1e-10).ln()
            })
            .sum();

        (log_sum / total_weight).exp()
    }

    /// Compute Euclidean distance to another T3
    pub fn distance(&self, other: &T3) -> f64 {
        let sum_sq: f64 = self
            .dimensions
            .iter()
            .zip(other.dimensions.iter())
            .map(|(a, b)| (a - b).powi(2))
            .sum();
        sum_sq.sqrt()
    }

    /// Merge with another T3 using weighted average
    ///
    /// The merge is weighted by the observation counts in each tensor
    pub fn merge(&self, other: &T3) -> Self {
        let mut result = Self::new();

        for i in 0..T3_DIMENSIONS {
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

    /// Apply time decay to the tensor
    ///
    /// Trust that isn't reinforced decays toward neutral (0.5) over time.
    /// The decay_factor should be in (0, 1), where smaller = faster decay.
    pub fn decay(&mut self, decay_factor: f64) {
        for i in 0..T3_DIMENSIONS {
            // Move score toward neutral (0.5)
            let distance_from_neutral = self.dimensions[i] - 0.5;
            self.dimensions[i] = 0.5 + distance_from_neutral * decay_factor;

            // Also decay weights
            self.weights[i] *= decay_factor;
        }
    }

    /// Check if trust meets minimum thresholds
    pub fn meets_thresholds(&self, min_scores: &[f64; T3_DIMENSIONS]) -> bool {
        self.dimensions
            .iter()
            .zip(min_scores.iter())
            .all(|(score, min)| score >= min)
    }
}

/// A trust observation to be recorded
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TrustObservation {
    /// The observer's LCT ID
    pub observer_id: Uuid,

    /// The observed entity's LCT ID
    pub subject_id: Uuid,

    /// The dimension being observed
    pub dimension: TrustDimension,

    /// The observed score (0.0 to 1.0)
    pub score: f64,

    /// Context/reason for the observation
    pub context: String,

    /// Timestamp of the observation
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

impl TrustObservation {
    /// Create a new trust observation
    pub fn new(
        observer_id: Uuid,
        subject_id: Uuid,
        dimension: TrustDimension,
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
            subject_id,
            dimension,
            score,
            context: context.into(),
            timestamp: chrono::Utc::now(),
        })
    }
}

/// Trust relationship between two entities
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TrustRelation {
    /// The trusting entity's LCT ID
    pub from_id: Uuid,

    /// The trusted entity's LCT ID
    pub to_id: Uuid,

    /// The trust tensor
    pub tensor: T3,

    /// When this relation was established
    pub established_at: chrono::DateTime<chrono::Utc>,

    /// Last update timestamp
    pub updated_at: chrono::DateTime<chrono::Utc>,
}

impl TrustRelation {
    /// Create a new trust relation with neutral trust
    pub fn new(from_id: Uuid, to_id: Uuid) -> Self {
        let now = chrono::Utc::now();
        Self {
            from_id,
            to_id,
            tensor: T3::new(),
            established_at: now,
            updated_at: now,
        }
    }

    /// Record an observation in this relation
    pub fn observe(&mut self, dimension: TrustDimension, score: f64) -> Result<()> {
        self.tensor.observe(dimension, score)?;
        self.updated_at = chrono::Utc::now();
        Ok(())
    }

    /// Get the aggregate trust score
    pub fn trust_score(&self) -> f64 {
        self.tensor.aggregate()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_t3_is_neutral() {
        let t3 = T3::new();
        assert_eq!(t3.aggregate(), 0.5);
        for dim in TrustDimension::all() {
            assert_eq!(t3.score(dim), 0.5);
            assert_eq!(t3.weight(dim), 0.0);
        }
    }

    #[test]
    fn test_observation_updates_score() {
        let mut t3 = T3::new();
        t3.observe(TrustDimension::Competence, 1.0).unwrap();

        // Score should move toward 1.0
        assert!(t3.score(TrustDimension::Competence) > 0.5);
        // Weight should be non-zero
        assert!(t3.weight(TrustDimension::Competence) > 0.0);
    }

    #[test]
    fn test_multiple_observations_stabilize() {
        let mut t3 = T3::new();

        // Observe high competence many times
        for _ in 0..20 {
            t3.observe(TrustDimension::Competence, 0.9).unwrap();
        }

        // Score should approach 0.9
        assert!(t3.score(TrustDimension::Competence) > 0.8);
        // Weight should be high
        assert!(t3.weight(TrustDimension::Competence) > 0.5);
    }

    #[test]
    fn test_invalid_scores_rejected() {
        let mut t3 = T3::new();
        assert!(t3.observe(TrustDimension::Competence, 1.5).is_err());
        assert!(t3.observe(TrustDimension::Competence, -0.1).is_err());
    }

    #[test]
    fn test_decay_moves_toward_neutral() {
        let mut t3 = T3::with_scores([0.9, 0.9, 0.9, 0.9, 0.9, 0.9]).unwrap();
        t3.decay(0.5);

        for dim in TrustDimension::all() {
            // Score should be closer to 0.5
            assert!(t3.score(dim) < 0.9);
            assert!(t3.score(dim) > 0.5);
        }
    }

    #[test]
    fn test_merge_combines_tensors() {
        let mut t1 = T3::new();
        let mut t2 = T3::new();

        // t1 has many observations of high competence
        for _ in 0..10 {
            t1.observe(TrustDimension::Competence, 0.9).unwrap();
        }

        // t2 has fewer observations of low competence
        for _ in 0..2 {
            t2.observe(TrustDimension::Competence, 0.3).unwrap();
        }

        let merged = t1.merge(&t2);

        // Merged should be closer to t1's score (more observations)
        assert!(merged.score(TrustDimension::Competence) > 0.7);
    }

    #[test]
    fn test_distance_calculation() {
        let t1 = T3::with_scores([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]).unwrap();
        let t2 = T3::with_scores([1.0, 1.0, 1.0, 1.0, 1.0, 1.0]).unwrap();

        let dist = t1.distance(&t2);
        // Maximum distance in 6D unit cube
        let expected = (6.0_f64).sqrt();
        assert!((dist - expected).abs() < 0.001);
    }

    #[test]
    fn test_threshold_checking() {
        let t3 = T3::with_scores([0.8, 0.7, 0.6, 0.5, 0.4, 0.3]).unwrap();

        assert!(t3.meets_thresholds(&[0.8, 0.7, 0.6, 0.5, 0.4, 0.3]));
        assert!(t3.meets_thresholds(&[0.7, 0.6, 0.5, 0.4, 0.3, 0.2]));
        assert!(!t3.meets_thresholds(&[0.9, 0.7, 0.6, 0.5, 0.4, 0.3]));
    }
}
