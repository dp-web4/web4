//! T3 Trust Tensor
//!
//! The T3 tensor captures trust across 6 dimensions:
//!
//! 1. **Competence**: Can they do it? (skill/ability)
//! 2. **Reliability**: Will they do it consistently?
//! 3. **Consistency**: Same quality over time?
//! 4. **Witnesses**: Corroborated by others?
//! 5. **Lineage**: Track record / history length?
//! 6. **Alignment**: Values match context?

use serde::{Deserialize, Serialize};
use super::TrustLevel;

/// T3 Trust Tensor - 6 dimensions measuring trustworthiness
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "python", pyo3::pyclass(get_all, set_all))]
pub struct T3Tensor {
    /// Can they do it? (skill/ability)
    pub competence: f64,
    /// Will they do it consistently?
    pub reliability: f64,
    /// Same quality over time?
    pub consistency: f64,
    /// Corroborated by others?
    pub witnesses: f64,
    /// Track record / history length?
    pub lineage: f64,
    /// Values match context?
    pub alignment: f64,
}

impl Default for T3Tensor {
    fn default() -> Self {
        Self::neutral()
    }
}

impl T3Tensor {
    /// Create a new T3 tensor with specified values
    pub fn new(
        competence: f64,
        reliability: f64,
        consistency: f64,
        witnesses: f64,
        lineage: f64,
        alignment: f64,
    ) -> Self {
        Self {
            competence: competence.clamp(0.0, 1.0),
            reliability: reliability.clamp(0.0, 1.0),
            consistency: consistency.clamp(0.0, 1.0),
            witnesses: witnesses.clamp(0.0, 1.0),
            lineage: lineage.clamp(0.0, 1.0),
            alignment: alignment.clamp(0.0, 1.0),
        }
    }

    /// Create a neutral T3 tensor (all values at 0.5)
    pub fn neutral() -> Self {
        Self {
            competence: 0.5,
            reliability: 0.5,
            consistency: 0.5,
            witnesses: 0.5,
            lineage: 0.5,
            alignment: 0.5,
        }
    }

    /// Create a zero T3 tensor (minimum trust)
    pub fn zero() -> Self {
        Self {
            competence: 0.0,
            reliability: 0.0,
            consistency: 0.0,
            witnesses: 0.0,
            lineage: 0.0,
            alignment: 0.0,
        }
    }

    /// Create a maximum T3 tensor (maximum trust)
    pub fn max() -> Self {
        Self {
            competence: 1.0,
            reliability: 1.0,
            consistency: 1.0,
            witnesses: 1.0,
            lineage: 1.0,
            alignment: 1.0,
        }
    }

    /// Calculate the average trust score (0.0 - 1.0)
    pub fn average(&self) -> f64 {
        (self.competence
            + self.reliability
            + self.consistency
            + self.witnesses
            + self.lineage
            + self.alignment)
            / 6.0
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
            // Diminishing returns as reliability approaches 1.0
            magnitude * 0.05 * (1.0 - self.reliability)
        } else {
            // Bigger fall from height
            -magnitude * 0.10 * self.reliability
        };

        // Update dimensions
        self.reliability = (self.reliability + delta).clamp(0.0, 1.0);
        self.consistency = (self.consistency + delta * 0.5).clamp(0.0, 1.0);
        self.competence = (self.competence + delta * 0.3).clamp(0.0, 1.0);
    }

    /// Update lineage based on action history
    ///
    /// Lineage builds slowly with consistent success over many actions.
    ///
    /// # Arguments
    /// * `success_count` - Total number of successful actions
    /// * `action_count` - Total number of actions
    pub fn update_lineage(&mut self, success_count: u64, action_count: u64) {
        if action_count == 0 {
            return;
        }

        let success_rate = success_count as f64 / action_count as f64;
        let history_factor = (action_count as f64 / 100.0).min(1.0);

        // Lineage = base + (success_rate factor) * (history factor)
        self.lineage = 0.2 + 0.8 * success_rate.sqrt() * history_factor;
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

        let old_reliability = self.reliability;

        // Reliability decays most (will they still do it?)
        self.reliability = decay_value(self.reliability, 1.0);
        // Consistency decays slightly less
        self.consistency = decay_value(self.consistency, 0.98);
        // Competence decays slowest (skills don't fade as fast)
        self.competence = decay_value(self.competence, 0.995);

        // Return whether meaningful decay occurred
        (old_reliability - self.reliability).abs() > 0.001
    }

    /// Update witnesses dimension from being observed
    ///
    /// # Arguments
    /// * `success` - Whether the witnessed action succeeded
    /// * `magnitude` - Update magnitude
    pub fn update_witnesses(&mut self, success: bool, magnitude: f64) {
        let delta = if success {
            magnitude * 0.03 * (1.0 - self.witnesses)
        } else {
            -magnitude * 0.05 * self.witnesses
        };
        self.witnesses = (self.witnesses + delta).clamp(0.0, 1.0);
    }

    /// Update alignment dimension
    ///
    /// # Arguments
    /// * `success` - Whether the aligned action succeeded
    /// * `magnitude` - Update magnitude
    pub fn update_alignment(&mut self, success: bool, magnitude: f64) {
        let delta = if success {
            magnitude * 0.02 * (1.0 - self.alignment)
        } else {
            magnitude * 0.01 * (1.0 - self.alignment) // Witnessing failures doesn't hurt much
        };
        self.alignment = (self.alignment + delta).clamp(0.0, 1.0);
    }

    /// Get tensor as an array of values
    pub fn as_array(&self) -> [f64; 6] {
        [
            self.competence,
            self.reliability,
            self.consistency,
            self.witnesses,
            self.lineage,
            self.alignment,
        ]
    }

    /// Create tensor from an array of values
    pub fn from_array(values: [f64; 6]) -> Self {
        Self::new(
            values[0],
            values[1],
            values[2],
            values[3],
            values[4],
            values[5],
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
        let initial = t3.reliability;
        t3.update_from_outcome(true, 0.1);
        assert!(t3.reliability > initial);
    }

    #[test]
    fn test_update_from_failure() {
        let mut t3 = T3Tensor::neutral();
        let initial = t3.reliability;
        t3.update_from_outcome(false, 0.1);
        assert!(t3.reliability < initial);
    }

    #[test]
    fn test_asymmetric_updates() {
        let mut t3_success = T3Tensor::neutral();
        let mut t3_failure = T3Tensor::neutral();

        t3_success.update_from_outcome(true, 0.1);
        t3_failure.update_from_outcome(false, 0.1);

        let success_delta = (t3_success.reliability - 0.5).abs();
        let failure_delta = (t3_failure.reliability - 0.5).abs();

        // Failure should have bigger impact
        assert!(failure_delta > success_delta);
    }

    #[test]
    fn test_decay() {
        let mut t3 = T3Tensor::new(0.9, 0.9, 0.9, 0.5, 0.5, 0.5);
        let decayed = t3.apply_decay(30.0, 0.01);
        assert!(decayed);
        assert!(t3.reliability < 0.9);
        assert!(t3.reliability >= 0.3); // Floor
    }

    #[test]
    fn test_lineage_update() {
        let mut t3 = T3Tensor::neutral();
        t3.update_lineage(90, 100);
        assert!(t3.lineage > 0.5);
    }

    #[test]
    fn test_clamping() {
        let t3 = T3Tensor::new(1.5, -0.5, 0.5, 0.5, 0.5, 0.5);
        assert_eq!(t3.competence, 1.0);
        assert_eq!(t3.reliability, 0.0);
    }
}
