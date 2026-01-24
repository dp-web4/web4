//! Witnessing chain traversal

use serde::{Deserialize, Serialize};
use super::WitnessNode;

/// Result of traversing a witnessing chain
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WitnessingChain {
    /// Root entity ID
    pub entity_id: String,

    /// T3 average of the root entity
    pub t3_average: f64,

    /// Trust level of the root entity
    pub trust_level: String,

    /// Entities that have witnessed this entity
    pub witnessed_by: Vec<WitnessNode>,

    /// Entities this entity has witnessed
    pub has_witnessed: Vec<WitnessNode>,
}

impl WitnessingChain {
    /// Create a new witnessing chain for an entity
    pub fn new(entity_id: impl Into<String>, t3_average: f64, trust_level: impl Into<String>) -> Self {
        Self {
            entity_id: entity_id.into(),
            t3_average,
            trust_level: trust_level.into(),
            witnessed_by: Vec::new(),
            has_witnessed: Vec::new(),
        }
    }

    /// Add an entity that witnessed this one
    pub fn add_witness(&mut self, node: WitnessNode) {
        self.witnessed_by.push(node);
    }

    /// Add an entity this one has witnessed
    pub fn add_witnessed(&mut self, node: WitnessNode) {
        self.has_witnessed.push(node);
    }

    /// Total number of witness relationships
    pub fn total_connections(&self) -> usize {
        self.witnessed_by.len() + self.has_witnessed.len()
    }

    /// Calculate aggregate trust from witnesses
    ///
    /// Entities witnessed by high-trust witnesses get a boost.
    pub fn aggregate_witness_trust(&self) -> f64 {
        if self.witnessed_by.is_empty() {
            return 0.0;
        }

        let total: f64 = self.witnessed_by.iter().map(|w| w.t3_average).sum();
        total / self.witnessed_by.len() as f64
    }

    /// Calculate transitive trust score
    ///
    /// Combines direct trust with witness attestations.
    /// Formula: direct_trust * 0.7 + witness_trust * 0.3
    pub fn transitive_trust(&self) -> f64 {
        let witness_trust = self.aggregate_witness_trust();
        self.t3_average * 0.7 + witness_trust * 0.3
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_chain() {
        let chain = WitnessingChain::new("mcp:test", 0.5, "medium");
        assert_eq!(chain.entity_id, "mcp:test");
        assert_eq!(chain.t3_average, 0.5);
        assert_eq!(chain.total_connections(), 0);
    }

    #[test]
    fn test_add_witnesses() {
        let mut chain = WitnessingChain::new("mcp:test", 0.5, "medium");

        chain.add_witness(WitnessNode::new("session:a", 0.8, "high", 1));
        chain.add_witness(WitnessNode::new("session:b", 0.6, "medium-high", 1));

        assert_eq!(chain.witnessed_by.len(), 2);
        assert_eq!(chain.total_connections(), 2);
    }

    #[test]
    fn test_aggregate_witness_trust() {
        let mut chain = WitnessingChain::new("mcp:test", 0.5, "medium");

        chain.add_witness(WitnessNode::new("session:a", 0.8, "high", 1));
        chain.add_witness(WitnessNode::new("session:b", 0.6, "medium-high", 1));

        assert_eq!(chain.aggregate_witness_trust(), 0.7);
    }

    #[test]
    fn test_transitive_trust() {
        let mut chain = WitnessingChain::new("mcp:test", 0.5, "medium");

        // With high-trust witnesses, transitive trust should be boosted
        chain.add_witness(WitnessNode::new("session:a", 0.9, "high", 1));
        chain.add_witness(WitnessNode::new("session:b", 0.9, "high", 1));

        let transitive = chain.transitive_trust();
        // 0.5 * 0.7 + 0.9 * 0.3 = 0.35 + 0.27 = 0.62
        assert!((transitive - 0.62).abs() < 0.01);
    }
}
