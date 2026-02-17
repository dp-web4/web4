//! V3 Value Tensor
//!
//! The V3 tensor captures value contribution across 3 root dimensions, each a
//! root node in an open-ended RDF sub-graph extensible via `web4:subDimensionOf`:
//!
//! 1. **Valuation**: Economic worth (effort invested + value added)
//! 2. **Veracity**: Truthfulness, authenticity, reputation
//! 3. **Validity**: Legitimacy, relevance, network standing

use serde::{Deserialize, Serialize};

/// V3 Value Tensor - 3 root dimensions measuring value contribution
///
/// Each root dimension is a node in an open-ended RDF sub-graph.
/// See `web4-standard/ontology/t3v3-ontology.ttl` for the formal ontology.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "python", pyo3::pyclass(get_all, set_all))]
pub struct V3Tensor {
    /// Economic worth (effort invested + value added)
    pub valuation: f64,
    /// Truthfulness, authenticity, reputation
    pub veracity: f64,
    /// Legitimacy, relevance, network standing
    pub validity: f64,
}

impl Default for V3Tensor {
    fn default() -> Self {
        Self::neutral()
    }
}

impl V3Tensor {
    /// Create a new V3 tensor with specified values
    pub fn new(valuation: f64, veracity: f64, validity: f64) -> Self {
        Self {
            valuation: valuation.clamp(0.0, 1.0),
            veracity: veracity.clamp(0.0, 1.0),
            validity: validity.clamp(0.0, 1.0),
        }
    }

    /// Create a neutral V3 tensor (all values at 0.5)
    pub fn neutral() -> Self {
        Self {
            valuation: 0.5,
            veracity: 0.5,
            validity: 0.5,
        }
    }

    /// Create a zero V3 tensor (minimum value)
    pub fn zero() -> Self {
        Self {
            valuation: 0.0,
            veracity: 0.0,
            validity: 0.0,
        }
    }

    /// Create a maximum V3 tensor (maximum value)
    pub fn max() -> Self {
        Self {
            valuation: 1.0,
            veracity: 1.0,
            validity: 1.0,
        }
    }

    /// Calculate the average value score (0.0 - 1.0)
    pub fn average(&self) -> f64 {
        (self.valuation + self.veracity + self.validity) / 3.0
    }

    /// Update valuation (effort/energy invested)
    ///
    /// Valuation increases with each action, representing effort spent.
    pub fn add_valuation(&mut self, amount: f64) {
        self.valuation = (self.valuation + amount).min(1.0);
    }

    /// Update valuation from successful contribution
    pub fn add_contribution(&mut self, amount: f64) {
        self.valuation = (self.valuation + amount).min(1.0);
    }

    /// Update validity (network/connections growth)
    ///
    /// Validity grows as entity connects with others and establishes standing.
    pub fn grow_validity(&mut self, amount: f64) {
        self.validity = (self.validity + amount).min(1.0);
    }

    /// Update veracity from being witnessed (reputation)
    ///
    /// # Arguments
    /// * `success` - Whether the witnessed action succeeded
    /// * `magnitude` - Update magnitude
    pub fn update_veracity(&mut self, success: bool, magnitude: f64) {
        let delta = if success {
            magnitude * 0.8 * (1.0 - self.veracity)
        } else {
            -magnitude * 0.5 * self.veracity
        };
        self.veracity = (self.veracity + delta).clamp(0.0, 1.0);
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

        // Validity decays directly (relevance fades)
        self.validity = decay_value(self.validity, 1.0);
        // Valuation fades over time (energy dissipates)
        self.valuation = decay_value(self.valuation, 0.99);
    }

    /// Get tensor as an array of values [valuation, veracity, validity]
    pub fn as_array(&self) -> [f64; 3] {
        [self.valuation, self.veracity, self.validity]
    }

    /// Create tensor from an array of values [valuation, veracity, validity]
    pub fn from_array(values: [f64; 3]) -> Self {
        Self::new(values[0], values[1], values[2])
    }

    /// Migrate from old 6D format to canonical 3D
    ///
    /// Maps: valuation=avg(energy,contribution), veracity=reputation,
    /// validity=avg(stewardship,network,temporal)
    pub fn from_legacy_6d(
        energy: f64,
        contribution: f64,
        stewardship: f64,
        network: f64,
        reputation: f64,
        temporal: f64,
    ) -> Self {
        Self::new(
            (energy + contribution) / 2.0,
            reputation,
            (stewardship + network + temporal) / 3.0,
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
    fn test_add_valuation() {
        let mut v3 = V3Tensor::neutral();
        v3.add_valuation(0.1);
        assert_eq!(v3.valuation, 0.6);
    }

    #[test]
    fn test_valuation_capped() {
        let mut v3 = V3Tensor::neutral();
        v3.add_valuation(0.6);
        assert_eq!(v3.valuation, 1.0);
    }

    #[test]
    fn test_veracity_update() {
        let mut v3 = V3Tensor::neutral();
        v3.update_veracity(true, 0.1);
        assert!(v3.veracity > 0.5);
    }

    #[test]
    fn test_decay() {
        let mut v3 = V3Tensor::new(0.9, 0.5, 0.9);
        v3.apply_decay(30.0, 0.01);
        assert!(v3.validity < 0.9);
        assert!(v3.validity >= 0.3); // Floor
    }

    #[test]
    fn test_clamping() {
        let v3 = V3Tensor::new(1.5, -0.5, 0.5);
        assert_eq!(v3.valuation, 1.0);
        assert_eq!(v3.veracity, 0.0);
    }

    #[test]
    fn test_legacy_migration() {
        let v3 = V3Tensor::from_legacy_6d(0.8, 0.6, 0.5, 0.7, 0.9, 0.3);
        // valuation = avg(0.8, 0.6) = 0.7
        assert!((v3.valuation - 0.7).abs() < 0.001);
        // veracity = 0.9
        assert!((v3.veracity - 0.9).abs() < 0.001);
        // validity = avg(0.5, 0.7, 0.3) = 0.5
        assert!((v3.validity - 0.5).abs() < 0.001);
    }
}
