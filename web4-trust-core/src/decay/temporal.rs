//! Temporal decay calculations

use serde::{Deserialize, Serialize};

/// Configuration for trust decay
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DecayConfig {
    /// Decay rate per day (e.g., 0.01 = 1% per day)
    pub rate_per_day: f64,

    /// Minimum value trust can decay to (floor)
    pub floor: f64,

    /// Days of inactivity before decay starts
    pub grace_period_days: f64,
}

impl Default for DecayConfig {
    fn default() -> Self {
        Self {
            rate_per_day: 0.01,  // 1% per day
            floor: 0.3,          // Never below 0.3
            grace_period_days: 1.0, // 1 day grace period
        }
    }
}

impl DecayConfig {
    /// Create a new decay configuration
    pub fn new(rate_per_day: f64, floor: f64, grace_period_days: f64) -> Self {
        Self {
            rate_per_day: rate_per_day.clamp(0.0, 1.0),
            floor: floor.clamp(0.0, 1.0),
            grace_period_days: grace_period_days.max(0.0),
        }
    }

    /// Create a "no decay" configuration
    pub fn no_decay() -> Self {
        Self {
            rate_per_day: 0.0,
            floor: 0.0,
            grace_period_days: f64::MAX,
        }
    }

    /// Create an aggressive decay configuration
    pub fn aggressive() -> Self {
        Self {
            rate_per_day: 0.05,  // 5% per day
            floor: 0.2,
            grace_period_days: 0.0,
        }
    }
}

/// Calculate the decay factor for a given number of days
///
/// # Arguments
/// * `days_inactive` - Days since last action
/// * `decay_rate` - Decay rate per day (0.0 - 1.0)
///
/// # Returns
/// Decay factor (0.0 - 1.0) to multiply against (value - floor)
///
/// # Example
/// ```
/// use web4_trust_core::decay::calculate_decay_factor;
///
/// // After 30 days at 1% decay rate
/// let factor = calculate_decay_factor(30.0, 0.01);
/// assert!(factor < 1.0); // Some decay
/// assert!(factor > 0.5); // Not too much
/// ```
pub fn calculate_decay_factor(days_inactive: f64, decay_rate: f64) -> f64 {
    if days_inactive <= 0.0 {
        return 1.0; // No decay
    }

    // Exponential decay: factor = (1 - rate)^days
    // After 30 days at 1%: (0.99)^30 ≈ 0.74
    // After 60 days at 1%: (0.99)^60 ≈ 0.55
    // After 90 days at 1%: (0.99)^90 ≈ 0.41
    (1.0 - decay_rate).powf(days_inactive)
}

/// Apply decay to a single value
///
/// # Arguments
/// * `current` - Current value (0.0 - 1.0)
/// * `days_inactive` - Days since last action
/// * `config` - Decay configuration
///
/// # Returns
/// Decayed value (never below floor)
pub fn apply_decay_to_value(current: f64, days_inactive: f64, config: &DecayConfig) -> f64 {
    if days_inactive <= config.grace_period_days {
        return current;
    }

    let effective_days = days_inactive - config.grace_period_days;
    let decay_factor = calculate_decay_factor(effective_days, config.rate_per_day);

    // Decay towards floor: new = floor + (current - floor) * factor
    let decayed = config.floor + (current - config.floor) * decay_factor;
    decayed.max(config.floor)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_decay_factor_no_time() {
        assert_eq!(calculate_decay_factor(0.0, 0.01), 1.0);
        assert_eq!(calculate_decay_factor(-1.0, 0.01), 1.0);
    }

    #[test]
    fn test_decay_factor_30_days() {
        let factor = calculate_decay_factor(30.0, 0.01);
        assert!((factor - 0.74).abs() < 0.01);
    }

    #[test]
    fn test_decay_factor_60_days() {
        let factor = calculate_decay_factor(60.0, 0.01);
        assert!((factor - 0.55).abs() < 0.01);
    }

    #[test]
    fn test_apply_decay() {
        let config = DecayConfig::default();

        // Start at 0.9, decay for 30 days
        let decayed = apply_decay_to_value(0.9, 30.0, &config);

        // Should decay but stay above floor
        assert!(decayed < 0.9);
        assert!(decayed >= 0.3);
    }

    #[test]
    fn test_grace_period() {
        let config = DecayConfig {
            grace_period_days: 7.0,
            ..Default::default()
        };

        // Within grace period - no decay
        let decayed = apply_decay_to_value(0.9, 5.0, &config);
        assert_eq!(decayed, 0.9);

        // After grace period - some decay
        let decayed = apply_decay_to_value(0.9, 10.0, &config);
        assert!(decayed < 0.9);
    }

    #[test]
    fn test_floor_respected() {
        let config = DecayConfig::default();

        // Even with massive decay, floor is respected
        let decayed = apply_decay_to_value(0.9, 1000.0, &config);
        assert!(decayed >= config.floor);
    }

    #[test]
    fn test_no_decay_config() {
        let config = DecayConfig::no_decay();
        let decayed = apply_decay_to_value(0.9, 100.0, &config);
        assert_eq!(decayed, 0.9);
    }
}
