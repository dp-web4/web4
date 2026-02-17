// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: MIT
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! Trust Tensor (T3) Implementation
//!
//! T3 is a 3-dimensional trust tensor whose root dimensions are nodes in an
//! open-ended RDF sub-graph. Each root can have any number of sub-dimensions
//! linked via `web4:subDimensionOf`. The scalar value at each root is the
//! aggregate of its sub-graph.
//!
//! Root Dimensions:
//! 1. Talent - natural aptitude and capability for a specific role
//! 2. Training - acquired expertise, certifications, and experience
//! 3. Temperament - behavioral consistency, reliability, ethical disposition
//!
//! Formal ontology: `web4-standard/ontology/t3v3-ontology.ttl`

use crate::error::{Result, Web4Error};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// Number of root dimensions in the trust tensor
pub const T3_DIMENSIONS: usize = 3;

/// The three root dimensions of trust
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[repr(usize)]
pub enum TrustDimension {
    /// Natural aptitude and capability for a specific role
    Talent = 0,
    /// Acquired expertise, certifications, and experience
    Training = 1,
    /// Behavioral consistency, reliability, ethical disposition
    Temperament = 2,
}

impl TrustDimension {
    /// Get all root dimensions in order
    pub fn all() -> [TrustDimension; T3_DIMENSIONS] {
        [
            TrustDimension::Talent,
            TrustDimension::Training,
            TrustDimension::Temperament,
        ]
    }

    /// Get the dimension name
    pub fn name(&self) -> &'static str {
        match self {
            TrustDimension::Talent => "talent",
            TrustDimension::Training => "training",
            TrustDimension::Temperament => "temperament",
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
    pub parent: TrustDimension,
}

/// A 3-dimensional trust tensor with fractal sub-dimension support
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct T3 {
    /// Trust scores for each root dimension (0.0 to 1.0)
    dimensions: [f64; T3_DIMENSIONS],

    /// Confidence weights for each root dimension (0.0 to 1.0)
    /// Higher weight = more observations/evidence
    weights: [f64; T3_DIMENSIONS],

    /// Number of observations contributing to each root dimension
    observation_counts: [u64; T3_DIMENSIONS],

    /// Sub-dimensions keyed by name, linked to root via parent field.
    /// Anyone can extend the dimension tree without modifying the core.
    #[serde(default, skip_serializing_if = "HashMap::is_empty")]
    sub_dimensions: HashMap<String, SubDimensionScore>,
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
            sub_dimensions: HashMap::new(),
        }
    }

    /// Create a T3 with specific initial root scores
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
            sub_dimensions: HashMap::new(),
        })
    }

    /// Get the score for a root dimension
    pub fn score(&self, dimension: TrustDimension) -> f64 {
        self.dimensions[dimension as usize]
    }

    /// Get the weight (confidence) for a root dimension
    pub fn weight(&self, dimension: TrustDimension) -> f64 {
        self.weights[dimension as usize]
    }

    /// Get all root dimension scores
    pub fn scores(&self) -> &[f64; T3_DIMENSIONS] {
        &self.dimensions
    }

    /// Get all weights
    pub fn weights(&self) -> &[f64; T3_DIMENSIONS] {
        &self.weights
    }

    /// Get sub-dimensions map
    pub fn sub_dimensions(&self) -> &HashMap<String, SubDimensionScore> {
        &self.sub_dimensions
    }

    /// Record an observation for a root dimension
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

    /// Record an observation for a sub-dimension
    ///
    /// Sub-dimensions are keyed by name and linked to a root dimension.
    /// Uses the same EMA math as root dimensions.
    pub fn observe_sub_dimension(
        &mut self,
        name: &str,
        parent: TrustDimension,
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

        // Merge sub-dimensions from both tensors
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

        // Decay sub-dimensions too
        for sub in self.sub_dimensions.values_mut() {
            let distance = sub.score - 0.5;
            sub.score = 0.5 + distance * decay_factor;
            sub.weight *= decay_factor;
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
        t3.observe(TrustDimension::Talent, 1.0).unwrap();

        // Score should move toward 1.0
        assert!(t3.score(TrustDimension::Talent) > 0.5);
        // Weight should be non-zero
        assert!(t3.weight(TrustDimension::Talent) > 0.0);
    }

    #[test]
    fn test_multiple_observations_stabilize() {
        let mut t3 = T3::new();

        // Observe high talent many times
        for _ in 0..20 {
            t3.observe(TrustDimension::Talent, 0.9).unwrap();
        }

        // Score should approach 0.9
        assert!(t3.score(TrustDimension::Talent) > 0.8);
        // Weight should be high
        assert!(t3.weight(TrustDimension::Talent) > 0.5);
    }

    #[test]
    fn test_invalid_scores_rejected() {
        let mut t3 = T3::new();
        assert!(t3.observe(TrustDimension::Talent, 1.5).is_err());
        assert!(t3.observe(TrustDimension::Talent, -0.1).is_err());
    }

    #[test]
    fn test_decay_moves_toward_neutral() {
        let mut t3 = T3::with_scores([0.9, 0.9, 0.9]).unwrap();
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

        // t1 has many observations of high talent
        for _ in 0..10 {
            t1.observe(TrustDimension::Talent, 0.9).unwrap();
        }

        // t2 has fewer observations of low talent
        for _ in 0..2 {
            t2.observe(TrustDimension::Talent, 0.3).unwrap();
        }

        let merged = t1.merge(&t2);

        // Merged should be closer to t1's score (more observations)
        assert!(merged.score(TrustDimension::Talent) > 0.7);
    }

    #[test]
    fn test_distance_calculation() {
        let t1 = T3::with_scores([0.0, 0.0, 0.0]).unwrap();
        let t2 = T3::with_scores([1.0, 1.0, 1.0]).unwrap();

        let dist = t1.distance(&t2);
        // Maximum distance in 3D unit cube
        let expected = (3.0_f64).sqrt();
        assert!((dist - expected).abs() < 0.001);
    }

    #[test]
    fn test_threshold_checking() {
        let t3 = T3::with_scores([0.8, 0.7, 0.6]).unwrap();

        assert!(t3.meets_thresholds(&[0.8, 0.7, 0.6]));
        assert!(t3.meets_thresholds(&[0.7, 0.6, 0.5]));
        assert!(!t3.meets_thresholds(&[0.9, 0.7, 0.6]));
    }

    #[test]
    fn test_sub_dimension_observation() {
        let mut t3 = T3::new();

        // Observe a sub-dimension of Talent
        t3.observe_sub_dimension("surgical_precision", TrustDimension::Talent, 0.9)
            .unwrap();
        t3.observe_sub_dimension("diagnostic_intuition", TrustDimension::Talent, 0.7)
            .unwrap();

        let subs = t3.sub_dimensions();
        assert_eq!(subs.len(), 2);
        assert!(subs["surgical_precision"].score > 0.5);
        assert_eq!(subs["surgical_precision"].parent, TrustDimension::Talent);
    }
}
