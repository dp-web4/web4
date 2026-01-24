//! V3 Value Tensor
//!
//! The V3 tensor captures value contribution across 6 dimensions:
//!
//! 1. **Energy**: Effort/resources invested
//! 2. **Contribution**: Value added to ecosystem
//! 3. **Stewardship**: Care for shared resources
//! 4. **Network**: Connections / reach
//! 5. **Reputation**: External perception
//! 6. **Temporal**: Time-based value accumulation

use serde::{Deserialize, Serialize};

/// V3 Value Tensor - 6 dimensions measuring value contribution
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "python", pyo3::pyclass(get_all, set_all))]
pub struct V3Tensor {
    /// Effort/resources invested
    pub energy: f64,
    /// Value added to ecosystem
    pub contribution: f64,
    /// Care for shared resources
    pub stewardship: f64,
    /// Connections / reach
    pub network: f64,
    /// External perception
    pub reputation: f64,
    /// Time-based value accumulation
    pub temporal: f64,
}

impl Default for V3Tensor {
    fn default() -> Self {
        Self::neutral()
    }
}

impl V3Tensor {
    /// Create a new V3 tensor with specified values
    pub fn new(
        energy: f64,
        contribution: f64,
        stewardship: f64,
        network: f64,
        reputation: f64,
        temporal: f64,
    ) -> Self {
        Self {
            energy: energy.clamp(0.0, 1.0),
            contribution: contribution.clamp(0.0, 1.0),
            stewardship: stewardship.clamp(0.0, 1.0),
            network: network.clamp(0.0, 1.0),
            reputation: reputation.clamp(0.0, 1.0),
            temporal: temporal.clamp(0.0, 1.0),
        }
    }

    /// Create a neutral V3 tensor (all values at 0.5)
    pub fn neutral() -> Self {
        Self {
            energy: 0.5,
            contribution: 0.5,
            stewardship: 0.5,
            network: 0.5,
            reputation: 0.5,
            temporal: 0.5,
        }
    }

    /// Create a zero V3 tensor (minimum value)
    pub fn zero() -> Self {
        Self {
            energy: 0.0,
            contribution: 0.0,
            stewardship: 0.0,
            network: 0.0,
            reputation: 0.0,
            temporal: 0.0,
        }
    }

    /// Create a maximum V3 tensor (maximum value)
    pub fn max() -> Self {
        Self {
            energy: 1.0,
            contribution: 1.0,
            stewardship: 1.0,
            network: 1.0,
            reputation: 1.0,
            temporal: 1.0,
        }
    }

    /// Calculate the average value score (0.0 - 1.0)
    pub fn average(&self) -> f64 {
        (self.energy
            + self.contribution
            + self.stewardship
            + self.network
            + self.reputation
            + self.temporal)
            / 6.0
    }

    /// Update energy (effort invested)
    ///
    /// Energy increases with each action, representing effort spent.
    pub fn add_energy(&mut self, amount: f64) {
        self.energy = (self.energy + amount).min(1.0);
    }

    /// Update contribution from successful work
    pub fn add_contribution(&mut self, amount: f64) {
        self.contribution = (self.contribution + amount).min(1.0);
    }

    /// Update network (connections)
    ///
    /// Network grows as entity connects with others.
    pub fn grow_network(&mut self, amount: f64) {
        self.network = (self.network + amount).min(1.0);
    }

    /// Update reputation from being witnessed
    ///
    /// # Arguments
    /// * `success` - Whether the witnessed action succeeded
    /// * `magnitude` - Update magnitude
    pub fn update_reputation(&mut self, success: bool, magnitude: f64) {
        let delta = if success {
            magnitude * 0.8 * (1.0 - self.reputation)
        } else {
            -magnitude * 0.5 * self.reputation
        };
        self.reputation = (self.reputation + delta).clamp(0.0, 1.0);
    }

    /// Apply temporal decay
    ///
    /// # Arguments
    /// * `days_inactive` - Days since last action
    /// * `decay_rate` - Decay rate per day
    pub fn apply_decay(&mut self, days_inactive: f64, decay_rate: f64) {
        if days_inactive <= 0.0 {
            return;
        }

        let decay_factor = (1.0 - decay_rate).powf(days_inactive);
        let floor = 0.3;

        let decay_value = |current: f64, factor: f64| -> f64 {
            let decayed = floor + (current - floor) * decay_factor * factor;
            decayed.max(floor)
        };

        // Temporal decays directly
        self.temporal = decay_value(self.temporal, 1.0);
        // Energy fades over time
        self.energy = decay_value(self.energy, 0.99);
    }

    /// Get tensor as an array of values
    pub fn as_array(&self) -> [f64; 6] {
        [
            self.energy,
            self.contribution,
            self.stewardship,
            self.network,
            self.reputation,
            self.temporal,
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
        let v3 = V3Tensor::neutral();
        assert_eq!(v3.average(), 0.5);
    }

    #[test]
    fn test_add_energy() {
        let mut v3 = V3Tensor::neutral();
        v3.add_energy(0.1);
        assert_eq!(v3.energy, 0.6);
    }

    #[test]
    fn test_energy_capped() {
        let mut v3 = V3Tensor::neutral();
        v3.add_energy(0.6);
        assert_eq!(v3.energy, 1.0);
    }

    #[test]
    fn test_reputation_update() {
        let mut v3 = V3Tensor::neutral();
        v3.update_reputation(true, 0.1);
        assert!(v3.reputation > 0.5);
    }

    #[test]
    fn test_decay() {
        let mut v3 = V3Tensor::new(0.9, 0.5, 0.5, 0.5, 0.5, 0.9);
        v3.apply_decay(30.0, 0.01);
        assert!(v3.temporal < 0.9);
        assert!(v3.temporal >= 0.3); // Floor
    }

    #[test]
    fn test_clamping() {
        let v3 = V3Tensor::new(1.5, -0.5, 0.5, 0.5, 0.5, 0.5);
        assert_eq!(v3.energy, 1.0);
        assert_eq!(v3.contribution, 0.0);
    }
}
