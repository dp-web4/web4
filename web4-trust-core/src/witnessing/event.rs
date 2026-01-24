//! Witness event types

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// A witnessing event between two entities
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WitnessEvent {
    /// Entity doing the witnessing
    pub witness_id: String,

    /// Entity being witnessed
    pub target_id: String,

    /// Whether the witnessed action succeeded
    pub success: bool,

    /// Magnitude of the witnessing (0.0 - 1.0)
    pub magnitude: f64,

    /// When the witnessing occurred
    pub timestamp: DateTime<Utc>,

    /// Optional context about what was witnessed
    #[serde(default)]
    pub context: Option<String>,
}

impl WitnessEvent {
    /// Create a new witness event
    pub fn new(
        witness_id: impl Into<String>,
        target_id: impl Into<String>,
        success: bool,
        magnitude: f64,
    ) -> Self {
        Self {
            witness_id: witness_id.into(),
            target_id: target_id.into(),
            success,
            magnitude: magnitude.clamp(0.0, 1.0),
            timestamp: Utc::now(),
            context: None,
        }
    }

    /// Create a witness event with context
    pub fn with_context(mut self, context: impl Into<String>) -> Self {
        self.context = Some(context.into());
        self
    }
}

/// Node in a witnessing chain
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WitnessNode {
    /// Entity ID
    pub entity_id: String,

    /// T3 average trust score
    pub t3_average: f64,

    /// Trust level
    pub trust_level: String,

    /// Depth in the chain (0 = root)
    pub depth: u32,
}

impl WitnessNode {
    /// Create a new witness node
    pub fn new(entity_id: impl Into<String>, t3_average: f64, trust_level: impl Into<String>, depth: u32) -> Self {
        Self {
            entity_id: entity_id.into(),
            t3_average,
            trust_level: trust_level.into(),
            depth,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_witness_event() {
        let event = WitnessEvent::new("session:abc", "mcp:filesystem", true, 0.1);

        assert_eq!(event.witness_id, "session:abc");
        assert_eq!(event.target_id, "mcp:filesystem");
        assert!(event.success);
        assert_eq!(event.magnitude, 0.1);
    }

    #[test]
    fn test_magnitude_clamping() {
        let event = WitnessEvent::new("a", "b", true, 1.5);
        assert_eq!(event.magnitude, 1.0);

        let event = WitnessEvent::new("a", "b", true, -0.5);
        assert_eq!(event.magnitude, 0.0);
    }

    #[test]
    fn test_with_context() {
        let event = WitnessEvent::new("a", "b", true, 0.1)
            .with_context("Tool call succeeded");

        assert_eq!(event.context, Some("Tool call succeeded".to_string()));
    }
}
