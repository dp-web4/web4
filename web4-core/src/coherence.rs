// Copyright (c) 2026 MetaLINXX Inc.
// SPDX-License-Identifier: MIT
//
// This software is covered by US Patents 11,477,027 and 12,278,913,
// and pending application 19/178,619. See PATENTS.md for details.

//! Identity Coherence Implementation
//!
//! Identity coherence measures how well an entity maintains consistent identity
//! over time. The formula is:
//!
//!   Coherence = C × S × Φ × R
//!
//! Where:
//! - C (Continuity): Temporal consistency of identity
//! - S (Stability): Resistance to perturbation
//! - Φ (Phi): Information integration (IIT-inspired)
//! - R (Reachability): Connection to the trust network
//!
//! Coherence is multiplicative because all factors are necessary:
//! a zero in any dimension zeros the total coherence.

use crate::error::{Result, Web4Error};
use crate::lct::{EntityType, Lct};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Identity coherence score
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Coherence {
    /// Continuity factor (0.0 to 1.0)
    /// Measures temporal consistency of identity
    pub continuity: f64,

    /// Stability factor (0.0 to 1.0)
    /// Measures resistance to perturbation
    pub stability: f64,

    /// Phi factor (0.0 to 1.0)
    /// Measures information integration (inspired by IIT)
    pub phi: f64,

    /// Reachability factor (0.0 to 1.0)
    /// Measures connection to the trust network
    pub reachability: f64,
}

impl Default for Coherence {
    fn default() -> Self {
        Self::new()
    }
}

impl Coherence {
    /// Create a new coherence score with neutral values
    pub fn new() -> Self {
        Self {
            continuity: 0.5,
            stability: 0.5,
            phi: 0.5,
            reachability: 0.5,
        }
    }

    /// Create with specific values
    pub fn with_values(continuity: f64, stability: f64, phi: f64, reachability: f64) -> Result<Self> {
        for (name, value) in [
            ("continuity", continuity),
            ("stability", stability),
            ("phi", phi),
            ("reachability", reachability),
        ] {
            if !(0.0..=1.0).contains(&value) {
                return Err(Web4Error::InvalidInput(format!(
                    "{} must be in range [0.0, 1.0]",
                    name
                )));
            }
        }
        Ok(Self {
            continuity,
            stability,
            phi,
            reachability,
        })
    }

    /// Compute total coherence score (C × S × Φ × R)
    pub fn total(&self) -> f64 {
        self.continuity * self.stability * self.phi * self.reachability
    }

    /// Check if coherence meets a threshold
    pub fn meets_threshold(&self, threshold: f64) -> bool {
        self.total() >= threshold
    }

    /// Get the limiting factor (lowest component)
    pub fn limiting_factor(&self) -> (&'static str, f64) {
        let factors = [
            ("continuity", self.continuity),
            ("stability", self.stability),
            ("phi", self.phi),
            ("reachability", self.reachability),
        ];
        *factors.iter().min_by(|a, b| a.1.partial_cmp(&b.1).unwrap()).unwrap()
    }
}

/// Coherence calculator for an LCT
pub struct CoherenceCalculator {
    /// Time window for continuity calculation (in seconds)
    continuity_window: u64,

    /// Minimum interactions for stability calculation
    min_interactions: u64,

    /// Network depth for reachability calculation
    network_depth: u32,
}

impl Default for CoherenceCalculator {
    fn default() -> Self {
        Self {
            continuity_window: 86400 * 30, // 30 days
            min_interactions: 10,
            network_depth: 3,
        }
    }
}

impl CoherenceCalculator {
    /// Create a new calculator with custom parameters
    pub fn new(continuity_window: u64, min_interactions: u64, network_depth: u32) -> Self {
        Self {
            continuity_window,
            min_interactions,
            network_depth,
        }
    }

    /// Calculate continuity from activity history
    ///
    /// High continuity = consistent presence over time
    /// Low continuity = sporadic or inconsistent activity
    pub fn calculate_continuity(&self, activity_timestamps: &[i64]) -> f64 {
        if activity_timestamps.is_empty() {
            return 0.0;
        }
        if activity_timestamps.len() == 1 {
            return 0.1;
        }

        let mut timestamps: Vec<i64> = activity_timestamps.to_vec();
        timestamps.sort_unstable();

        // Calculate gap distribution
        let gaps: Vec<i64> = timestamps.windows(2).map(|w| w[1] - w[0]).collect();
        let avg_gap = gaps.iter().sum::<i64>() as f64 / gaps.len() as f64;
        let expected_gap = self.continuity_window as f64 / activity_timestamps.len() as f64;

        // Continuity is higher when gaps are consistent and not too long
        let gap_consistency = 1.0 / (1.0 + (avg_gap / expected_gap - 1.0).abs());

        // Also consider total coverage of the window
        let total_span = (timestamps.last().unwrap() - timestamps.first().unwrap()) as f64;
        let coverage = (total_span / self.continuity_window as f64).min(1.0);

        (gap_consistency * 0.7 + coverage * 0.3).min(1.0)
    }

    /// Calculate stability from interaction variance
    ///
    /// High stability = consistent behavior patterns
    /// Low stability = erratic or unpredictable behavior
    pub fn calculate_stability(&self, interaction_scores: &[f64]) -> f64 {
        if interaction_scores.len() < self.min_interactions as usize {
            // Not enough data for stability assessment
            return 0.3;
        }

        let mean: f64 = interaction_scores.iter().sum::<f64>() / interaction_scores.len() as f64;
        let variance: f64 = interaction_scores
            .iter()
            .map(|x| (x - mean).powi(2))
            .sum::<f64>()
            / interaction_scores.len() as f64;
        let std_dev = variance.sqrt();

        // Low variance = high stability
        // Using logistic function to map std_dev to stability
        1.0 / (1.0 + (std_dev * 5.0).exp())
    }

    /// Calculate phi (information integration)
    ///
    /// Inspired by Integrated Information Theory.
    /// Measures how much the entity's outputs depend on integrated processing
    /// rather than simple input-output mapping.
    ///
    /// For practical purposes, we approximate this using:
    /// - Context sensitivity (same input, different context = different output)
    /// - Cross-reference density (outputs reference multiple inputs)
    pub fn calculate_phi(&self, context_sensitivity: f64, cross_reference_density: f64) -> f64 {
        // Both factors contribute to phi
        // High phi = high integration of information
        ((context_sensitivity + cross_reference_density) / 2.0).min(1.0).max(0.0)
    }

    /// Calculate reachability in the trust network
    ///
    /// High reachability = well-connected to trusted entities
    /// Low reachability = isolated or poorly connected
    pub fn calculate_reachability(
        &self,
        direct_connections: u32,
        indirect_connections: u32,
        max_connections: u32,
    ) -> f64 {
        if max_connections == 0 {
            return 0.0;
        }

        // Direct connections are weighted more heavily
        let direct_weight = 0.7;
        let indirect_weight = 0.3;

        let direct_ratio = (direct_connections as f64 / max_connections as f64).min(1.0);
        let indirect_ratio = (indirect_connections as f64 / (max_connections * self.network_depth) as f64).min(1.0);

        direct_weight * direct_ratio + indirect_weight * indirect_ratio
    }

    /// Calculate full coherence score for an entity
    pub fn calculate(&self, params: &CoherenceParams) -> Coherence {
        let continuity = self.calculate_continuity(&params.activity_timestamps);
        let stability = self.calculate_stability(&params.interaction_scores);
        let phi = self.calculate_phi(params.context_sensitivity, params.cross_reference_density);
        let reachability = self.calculate_reachability(
            params.direct_connections,
            params.indirect_connections,
            params.max_connections,
        );

        Coherence {
            continuity,
            stability,
            phi,
            reachability,
        }
    }
}

/// Parameters for coherence calculation
#[derive(Clone, Debug, Default)]
pub struct CoherenceParams {
    /// Unix timestamps of activity events
    pub activity_timestamps: Vec<i64>,

    /// Scores from past interactions (0.0 to 1.0)
    pub interaction_scores: Vec<f64>,

    /// Context sensitivity measure (0.0 to 1.0)
    pub context_sensitivity: f64,

    /// Cross-reference density (0.0 to 1.0)
    pub cross_reference_density: f64,

    /// Number of direct trust connections
    pub direct_connections: u32,

    /// Number of indirect (transitive) trust connections
    pub indirect_connections: u32,

    /// Maximum expected connections for normalization
    pub max_connections: u32,
}

/// Coherence threshold requirements by entity type
pub fn coherence_threshold_for_entity(entity_type: &EntityType) -> f64 {
    match entity_type {
        EntityType::Human => 0.5,        // Body-bound identity helps
        EntityType::AiEmbodied => 0.6,   // Hardware binding helps
        EntityType::AiSoftware => 0.7,   // Higher bar due to copyability
        EntityType::Organization => 0.5,
        EntityType::Role => 0.5,
        EntityType::Task => 0.3,
        EntityType::Resource => 0.3,
        EntityType::Hybrid => 0.6,
    }
}

/// Check if an LCT meets coherence requirements
pub fn check_coherence(lct: &Lct, coherence: &Coherence) -> Result<()> {
    let threshold = coherence_threshold_for_entity(&lct.entity_type);

    // Also apply hardware binding ceiling
    let effective_threshold = threshold.max(1.0 - lct.trust_ceiling());

    if coherence.total() < effective_threshold {
        return Err(Web4Error::CoherenceBelowThreshold {
            score: coherence.total(),
            threshold: effective_threshold,
        });
    }

    Ok(())
}

/// Coherence event for tracking history
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CoherenceEvent {
    /// The entity's LCT ID
    pub entity_id: Uuid,

    /// Coherence score at this point
    pub coherence: Coherence,

    /// Timestamp of measurement
    pub timestamp: chrono::DateTime<chrono::Utc>,

    /// Optional context/reason
    pub context: Option<String>,
}

impl CoherenceEvent {
    /// Create a new coherence event
    pub fn new(entity_id: Uuid, coherence: Coherence) -> Self {
        Self {
            entity_id,
            coherence,
            timestamp: chrono::Utc::now(),
            context: None,
        }
    }

    /// Create with context
    pub fn with_context(entity_id: Uuid, coherence: Coherence, context: impl Into<String>) -> Self {
        Self {
            entity_id,
            coherence,
            timestamp: chrono::Utc::now(),
            context: Some(context.into()),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_coherence_total() {
        let c = Coherence::with_values(0.8, 0.8, 0.8, 0.8).unwrap();
        let total = c.total();
        assert!((total - 0.4096).abs() < 0.001); // 0.8^4 = 0.4096
    }

    #[test]
    fn test_zero_factor_zeros_total() {
        let c = Coherence::with_values(0.9, 0.9, 0.0, 0.9).unwrap();
        assert_eq!(c.total(), 0.0);
    }

    #[test]
    fn test_limiting_factor() {
        let c = Coherence::with_values(0.9, 0.5, 0.8, 0.7).unwrap();
        let (name, value) = c.limiting_factor();
        assert_eq!(name, "stability");
        assert_eq!(value, 0.5);
    }

    #[test]
    fn test_continuity_calculation() {
        let calc = CoherenceCalculator::default();

        // Regular activity = high continuity
        let regular: Vec<i64> = (0..30).map(|i| i * 86400).collect();
        let continuity = calc.calculate_continuity(&regular);
        assert!(continuity > 0.5);

        // Empty = zero continuity
        assert_eq!(calc.calculate_continuity(&[]), 0.0);
    }

    #[test]
    fn test_stability_calculation() {
        let calc = CoherenceCalculator::default();

        // Consistent scores = higher stability
        let consistent: Vec<f64> = vec![0.8, 0.82, 0.79, 0.81, 0.8, 0.78, 0.81, 0.79, 0.8, 0.82];
        let stability = calc.calculate_stability(&consistent);
        assert!(stability > 0.4); // Consistent data should have reasonable stability

        // Erratic scores = lower stability
        let erratic: Vec<f64> = vec![0.1, 0.9, 0.2, 0.8, 0.3, 0.7, 0.15, 0.85, 0.25, 0.75];
        let stability_erratic = calc.calculate_stability(&erratic);
        assert!(stability_erratic < stability); // Erratic should be less stable
    }

    #[test]
    fn test_entity_thresholds() {
        assert_eq!(coherence_threshold_for_entity(&EntityType::Human), 0.5);
        assert_eq!(coherence_threshold_for_entity(&EntityType::AiSoftware), 0.7);
        assert_eq!(coherence_threshold_for_entity(&EntityType::Task), 0.3);
    }

    #[test]
    fn test_coherence_check() {
        let (lct, _) = Lct::new(EntityType::Human, None);

        // High coherence passes
        let high = Coherence::with_values(0.9, 0.9, 0.9, 0.9).unwrap();
        assert!(check_coherence(&lct, &high).is_ok());

        // Low coherence fails
        let low = Coherence::with_values(0.5, 0.5, 0.5, 0.5).unwrap();
        assert!(check_coherence(&lct, &low).is_err());
    }
}
