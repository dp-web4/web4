//! Entity trust implementation

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::tensor::{T3Tensor, V3Tensor, TrustLevel};
use super::EntityType;

/// Entity trust combining T3 and V3 tensors with witnessing relationships
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct EntityTrust {
    /// Unique entity identifier (format: "type:name")
    pub entity_id: String,

    /// Parsed entity type
    #[serde(default)]
    pub entity_type: String,

    /// Entity name (without type prefix)
    #[serde(default)]
    pub entity_name: String,

    /// T3 Trust Tensor
    #[serde(flatten, with = "t3_fields")]
    pub t3: T3Tensor,

    /// V3 Value Tensor
    #[serde(flatten, with = "v3_fields")]
    pub v3: V3Tensor,

    /// Entities that have witnessed this entity
    #[serde(default)]
    pub witnessed_by: Vec<String>,

    /// Entities this entity has witnessed
    #[serde(default)]
    pub has_witnessed: Vec<String>,

    /// Total number of actions
    #[serde(default)]
    pub action_count: u64,

    /// Number of successful actions
    #[serde(default)]
    pub success_count: u64,

    /// Number of times witnessed by others
    #[serde(default)]
    pub witness_count: u64,

    /// Timestamp of last action
    #[serde(default)]
    pub last_action: Option<DateTime<Utc>>,

    /// Creation timestamp
    #[serde(default = "Utc::now")]
    pub created_at: DateTime<Utc>,
}

// Custom serialization to flatten T3 fields
mod t3_fields {
    use super::*;
    use serde::{Deserializer, Serializer};

    #[derive(Serialize, Deserialize)]
    struct T3Flat {
        competence: f64,
        reliability: f64,
        consistency: f64,
        witnesses: f64,
        lineage: f64,
        alignment: f64,
    }

    pub fn serialize<S>(t3: &T3Tensor, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        T3Flat {
            competence: t3.competence,
            reliability: t3.reliability,
            consistency: t3.consistency,
            witnesses: t3.witnesses,
            lineage: t3.lineage,
            alignment: t3.alignment,
        }
        .serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<T3Tensor, D::Error>
    where
        D: Deserializer<'de>,
    {
        let flat = T3Flat::deserialize(deserializer)?;
        Ok(T3Tensor::new(
            flat.competence,
            flat.reliability,
            flat.consistency,
            flat.witnesses,
            flat.lineage,
            flat.alignment,
        ))
    }
}

// Custom serialization to flatten V3 fields
mod v3_fields {
    use super::*;
    use serde::{Deserializer, Serializer};

    #[derive(Serialize, Deserialize)]
    struct V3Flat {
        energy: f64,
        contribution: f64,
        stewardship: f64,
        network: f64,
        reputation: f64,
        temporal: f64,
    }

    pub fn serialize<S>(v3: &V3Tensor, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        V3Flat {
            energy: v3.energy,
            contribution: v3.contribution,
            stewardship: v3.stewardship,
            network: v3.network,
            reputation: v3.reputation,
            temporal: v3.temporal,
        }
        .serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<V3Tensor, D::Error>
    where
        D: Deserializer<'de>,
    {
        let flat = V3Flat::deserialize(deserializer)?;
        Ok(V3Tensor::new(
            flat.energy,
            flat.contribution,
            flat.stewardship,
            flat.network,
            flat.reputation,
            flat.temporal,
        ))
    }
}

impl EntityTrust {
    /// Create a new entity with default (neutral) trust
    pub fn new(entity_id: impl Into<String>) -> Self {
        let entity_id = entity_id.into();
        let (entity_type, entity_name) = Self::parse_entity_id(&entity_id);

        Self {
            entity_id,
            entity_type,
            entity_name,
            t3: T3Tensor::neutral(),
            v3: V3Tensor::neutral(),
            witnessed_by: Vec::new(),
            has_witnessed: Vec::new(),
            action_count: 0,
            success_count: 0,
            witness_count: 0,
            last_action: None,
            created_at: Utc::now(),
        }
    }

    /// Parse entity_id into type and name
    fn parse_entity_id(entity_id: &str) -> (String, String) {
        if let Some(idx) = entity_id.find(':') {
            let (type_part, name_part) = entity_id.split_at(idx);
            (type_part.to_string(), name_part[1..].to_string())
        } else {
            (String::new(), entity_id.to_string())
        }
    }

    /// Get the parsed entity type
    pub fn entity_type(&self) -> crate::Result<EntityType> {
        EntityType::from_entity_id(&self.entity_id)
    }

    /// Get average T3 trust score
    pub fn t3_average(&self) -> f64 {
        self.t3.average()
    }

    /// Get average V3 value score
    pub fn v3_average(&self) -> f64 {
        self.v3.average()
    }

    /// Get categorical trust level
    pub fn trust_level(&self) -> TrustLevel {
        self.t3.level()
    }

    /// Update trust from direct action outcome
    pub fn update_from_outcome(&mut self, success: bool, magnitude: f64) {
        self.action_count += 1;
        if success {
            self.success_count += 1;
        }

        // Update T3 tensor
        self.t3.update_from_outcome(success, magnitude);
        self.t3.update_lineage(self.success_count, self.action_count);

        // Update V3 energy (effort spent)
        self.v3.add_energy(0.01);

        self.last_action = Some(Utc::now());
    }

    /// Receive a witness event (another entity observed this one)
    ///
    /// Being witnessed builds:
    /// - witnesses score (T3) - more observers = more validated
    /// - reputation (V3) - external perception
    /// - network (V3) - connection to other entities
    pub fn receive_witness(&mut self, witness_id: &str, success: bool, magnitude: f64) {
        self.witness_count += 1;

        // Track who witnessed us
        if !self.witnessed_by.contains(&witness_id.to_string()) {
            self.witnessed_by.push(witness_id.to_string());
        }

        // Update T3 witnesses dimension
        self.t3.update_witnesses(success, magnitude);

        // Update V3 reputation and network
        self.v3.update_reputation(success, magnitude);
        self.v3.grow_network(0.01);
    }

    /// Give a witness event (this entity observed another)
    ///
    /// Being a witness builds:
    /// - alignment (T3) - if judgment was correct, entity is aligned with reality
    /// - contribution (V3) - value added through validation
    pub fn give_witness(&mut self, target_id: &str, success: bool, magnitude: f64) {
        // Track who we witnessed
        if !self.has_witnessed.contains(&target_id.to_string()) {
            self.has_witnessed.push(target_id.to_string());
        }

        // Update T3 alignment
        self.t3.update_alignment(success, magnitude);

        // Update V3 contribution
        self.v3.add_contribution(0.005);
    }

    /// Calculate days since last action
    pub fn days_since_last_action(&self) -> f64 {
        let reference_time = self.last_action.unwrap_or(self.created_at);
        let duration = Utc::now() - reference_time;
        duration.num_seconds() as f64 / 86400.0
    }

    /// Apply temporal decay based on inactivity
    ///
    /// Returns true if meaningful decay occurred
    pub fn apply_decay(&mut self, days_inactive: f64, decay_rate: f64) -> bool {
        let t3_decayed = self.t3.apply_decay(days_inactive, decay_rate);
        self.v3.apply_decay(days_inactive, decay_rate);
        t3_decayed
    }

    /// Get success rate (0.0 - 1.0)
    pub fn success_rate(&self) -> f64 {
        if self.action_count == 0 {
            0.5 // Neutral for entities with no actions
        } else {
            self.success_count as f64 / self.action_count as f64
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_entity() {
        let trust = EntityTrust::new("mcp:filesystem");
        assert_eq!(trust.entity_id, "mcp:filesystem");
        assert_eq!(trust.entity_type, "mcp");
        assert_eq!(trust.entity_name, "filesystem");
        assert_eq!(trust.t3_average(), 0.5);
        assert_eq!(trust.trust_level(), TrustLevel::Medium);
    }

    #[test]
    fn test_update_from_outcome() {
        let mut trust = EntityTrust::new("mcp:test");
        trust.update_from_outcome(true, 0.1);

        assert_eq!(trust.action_count, 1);
        assert_eq!(trust.success_count, 1);
        assert!(trust.t3.reliability > 0.5);
        assert!(trust.last_action.is_some());
    }

    #[test]
    fn test_receive_witness() {
        let mut trust = EntityTrust::new("mcp:test");
        trust.receive_witness("session:abc", true, 0.1);

        assert_eq!(trust.witness_count, 1);
        assert!(trust.witnessed_by.contains(&"session:abc".to_string()));
        assert!(trust.t3.witnesses > 0.5);
    }

    #[test]
    fn test_give_witness() {
        let mut trust = EntityTrust::new("session:abc");
        trust.give_witness("mcp:test", true, 0.1);

        assert!(trust.has_witnessed.contains(&"mcp:test".to_string()));
        assert!(trust.t3.alignment > 0.5);
    }

    #[test]
    fn test_serialization() {
        let trust = EntityTrust::new("mcp:filesystem");
        let json = serde_json::to_string_pretty(&trust).unwrap();

        // Verify it contains flattened fields
        assert!(json.contains("\"competence\""));
        assert!(json.contains("\"reliability\""));
        assert!(json.contains("\"energy\""));

        // Verify we can deserialize
        let parsed: EntityTrust = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.entity_id, trust.entity_id);
        assert_eq!(parsed.t3_average(), trust.t3_average());
    }

    #[test]
    fn test_success_rate() {
        let mut trust = EntityTrust::new("role:test");
        assert_eq!(trust.success_rate(), 0.5); // Neutral when no actions

        trust.update_from_outcome(true, 0.1);
        trust.update_from_outcome(true, 0.1);
        trust.update_from_outcome(false, 0.1);

        assert!((trust.success_rate() - 0.666).abs() < 0.01);
    }
}
