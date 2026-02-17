//! T3 Trust Tensor
//!
//! The T3 tensor captures trust across 3 root dimensions, each a root node
//! in an open-ended RDF sub-graph extensible via `web4:subDimensionOf`:
//!
//! 1. **Talent**: Natural/demonstrated ability (can they do it?)
//! 2. **Training**: Learned skills, track record, reliability
//! 3. **Temperament**: Character, consistency, alignment with context

use serde::{Deserialize, Serialize};
use super::TrustLevel;

/// T3 Trust Tensor - 3 root dimensions measuring trustworthiness
///
/// Each root dimension is a node in an open-ended RDF sub-graph.
/// See `web4-standard/ontology/t3v3-ontology.ttl` for the formal ontology.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "python", pyo3::pyclass(get_all, set_all))]
pub struct T3Tensor {
    /// Natural/demonstrated ability (can they do it?)
    pub talent: f64,
    /// Learned skills, track record, reliability
    pub training: f64,
    /// Character, consistency, alignment with context
    pub temperament: f64,
}

impl Default for T3Tensor {
    fn default() -> Self {
        Self::neutral()
    }
}

impl T3Tensor {
    /// Create a new T3 tensor with specified values
    pub fn new(talent: f64, training: f64, temperament: f64) -> Self {
        Self {
            talent: talent.clamp(0.0, 1.0),
            training: training.clamp(0.0, 1.0),
            temperament: temperament.clamp(0.0, 1.0),
        }
    }

    /// Create a neutral T3 tensor (all values at 0.5)
    pub fn neutral() -> Self {
        Self {
            talent: 0.5,
            training: 0.5,
            temperament: 0.5,
        }
    }

    /// Create a zero T3 tensor (minimum trust)
    pub fn zero() -> Self {
        Self {
            talent: 0.0,
            training: 0.0,
            temperament: 0.0,
        }
    }

    /// Create a maximum T3 tensor (maximum trust)
    pub fn max() -> Self {
        Self {
            talent: 1.0,
            training: 1.0,
            temperament: 1.0,
        }
    }

    /// Calculate the average trust score (0.0 - 1.0)
    pub fn average(&self) -> f64 {
        (self.talent + self.training + self.temperament) / 3.0
    }

    /// Get the categorical trust level
    pub fn level(&self) -> TrustLevel {
        TrustLevel::from_score(self.average())
    }

    /// Update tensor from an action outcome
    ///
    /// Success increases trust slowly (asymptotic to 1.0).
    /// Failure decreases trust faster (trust is hard to earn, easy to lose).
    ///
    /// # Arguments
    /// * `success` - Whether the action succeeded
    /// * `magnitude` - Update magnitude (0.0 - 1.0), typically 0.1
    pub fn update_from_outcome(&mut self, success: bool, magnitude: f64) {
        let magnitude = magnitude.clamp(0.0, 1.0);

        // Calculate delta (asymmetric: failures hit harder)
        let delta = if success {
            // Diminishing returns as training approaches 1.0
            magnitude * 0.05 * (1.0 - self.training)
        } else {
            // Bigger fall from height
            -magnitude * 0.10 * self.training
        };

        // Update dimensions: training most affected, then temperament, then talent
        self.training = (self.training + delta).clamp(0.0, 1.0);
        self.temperament = (self.temperament + delta * 0.5).clamp(0.0, 1.0);
        self.talent = (self.talent + delta * 0.3).clamp(0.0, 1.0);
    }

    /// Update training based on action history (track record)
    ///
    /// Training builds slowly with consistent success over many actions.
    ///
    /// # Arguments
    /// * `success_count` - Total number of successful actions
    /// * `action_count` - Total number of actions
    pub fn update_training(&mut self, success_count: u64, action_count: u64) {
        if action_count == 0 {
            return;
        }

        let success_rate = success_count as f64 / action_count as f64;
        let history_factor = (action_count as f64 / 100.0).min(1.0);

        // Training = base + (success_rate factor) * (history factor)
        self.training = 0.2 + 0.8 * success_rate.sqrt() * history_factor;
    }

    /// Apply temporal decay based on inactivity
    ///
    /// Trust decays slowly over time if not used.
    /// Decay is asymptotic to a floor (never fully decays to 0).
    ///
    /// # Arguments
    /// * `days_inactive` - Days since last action
    /// * `decay_rate` - Decay rate per day (default 0.01 = 1% per day)
    ///
    /// # Returns
    /// `true` if meaningful decay occurred (> 0.001 change)
    pub fn apply_decay(&mut self, days_inactive: f64, decay_rate: f64) -> bool {
        if days_inactive <= 0.0 {
            return false;
        }

        let decay_factor = (1.0 - decay_rate).powf(days_inactive);
        let floor = 0.3;

        let decay_value = |current: f64, factor: f64| -> f64 {
            let decayed = floor + (current - floor) * decay_factor * factor;
            decayed.max(floor)
        };

        let old_training = self.training;

        // Training decays most (will they still do it?)
        self.training = decay_value(self.training, 1.0);
        // Temperament decays slightly less (character is more stable)
        self.temperament = decay_value(self.temperament, 0.98);
        // Talent decays slowest (innate ability doesn't fade as fast)
        self.talent = decay_value(self.talent, 0.995);

        // Return whether meaningful decay occurred
        (old_training - self.training).abs() > 0.001
    }

    /// Update temperament from being witnessed by others
    ///
    /// # Arguments
    /// * `success` - Whether the witnessed action succeeded
    /// * `magnitude` - Update magnitude
    pub fn update_temperament_from_witness(&mut self, success: bool, magnitude: f64) {
        let delta = if success {
            magnitude * 0.03 * (1.0 - self.temperament)
        } else {
            -magnitude * 0.05 * self.temperament
        };
        self.temperament = (self.temperament + delta).clamp(0.0, 1.0);
    }

    /// Update temperament from alignment observation
    ///
    /// # Arguments
    /// * `success` - Whether the aligned action succeeded
    /// * `magnitude` - Update magnitude
    pub fn update_temperament_from_alignment(&mut self, success: bool, magnitude: f64) {
        let delta = if success {
            magnitude * 0.02 * (1.0 - self.temperament)
        } else {
            magnitude * 0.01 * (1.0 - self.temperament)
        };
        self.temperament = (self.temperament + delta).clamp(0.0, 1.0);
    }

    /// Get tensor as an array of values [talent, training, temperament]
    pub fn as_array(&self) -> [f64; 3] {
        [self.talent, self.training, self.temperament]
    }

    /// Create tensor from an array of values [talent, training, temperament]
    pub fn from_array(values: [f64; 3]) -> Self {
        Self::new(values[0], values[1], values[2])
    }

    /// Migrate from old 6D format to canonical 3D
    ///
    /// Maps: talent=competence, training=avg(reliability,consistency,lineage),
    /// temperament=avg(witnesses,alignment)
    pub fn from_legacy_6d(
        competence: f64,
        reliability: f64,
        consistency: f64,
        witnesses: f64,
        lineage: f64,
        alignment: f64,
    ) -> Self {
        Self::new(
            competence,
            (reliability + consistency + lineage) / 3.0,
            (witnesses + alignment) / 2.0,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_neutral_tensor() {
        let t3 = T3Tensor::neutral();
        assert_eq!(t3.average(), 0.5);
        assert_eq!(t3.level(), TrustLevel::Medium);
    }

    #[test]
    fn test_update_from_success() {
        let mut t3 = T3Tensor::neutral();
        let initial = t3.training;
        t3.update_from_outcome(true, 0.1);
        assert!(t3.training > initial);
    }

    #[test]
    fn test_update_from_failure() {
        let mut t3 = T3Tensor::neutral();
        let initial = t3.training;
        t3.update_from_outcome(false, 0.1);
        assert!(t3.training < initial);
    }

    #[test]
    fn test_asymmetric_updates() {
        let mut t3_success = T3Tensor::neutral();
        let mut t3_failure = T3Tensor::neutral();

        t3_success.update_from_outcome(true, 0.1);
        t3_failure.update_from_outcome(false, 0.1);

        let success_delta = (t3_success.training - 0.5).abs();
        let failure_delta = (t3_failure.training - 0.5).abs();

        // Failure should have bigger impact
        assert!(failure_delta > success_delta);
    }

    #[test]
    fn test_decay() {
        let mut t3 = T3Tensor::new(0.9, 0.9, 0.9);
        let decayed = t3.apply_decay(30.0, 0.01);
        assert!(decayed);
        assert!(t3.training < 0.9);
        assert!(t3.training >= 0.3); // Floor
    }

    #[test]
    fn test_training_update() {
        let mut t3 = T3Tensor::neutral();
        t3.update_training(90, 100);
        assert!(t3.training > 0.5);
    }

    #[test]
    fn test_clamping() {
        let t3 = T3Tensor::new(1.5, -0.5, 0.5);
        assert_eq!(t3.talent, 1.0);
        assert_eq!(t3.training, 0.0);
    }

    #[test]
    fn test_legacy_migration() {
        let t3 = T3Tensor::from_legacy_6d(0.8, 0.7, 0.6, 0.5, 0.9, 0.4);
        assert!((t3.talent - 0.8).abs() < 0.001);
        // training = avg(0.7, 0.6, 0.9) = 0.7333
        assert!((t3.training - 0.7333).abs() < 0.01);
        // temperament = avg(0.5, 0.4) = 0.45
        assert!((t3.temperament - 0.45).abs() < 0.001);
    }
}
