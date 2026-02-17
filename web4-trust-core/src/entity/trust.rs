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

    /// T3 Trust Tensor (Talent/Training/Temperament)
    #[serde(flatten, with = "t3_fields")]
    pub t3: T3Tensor,

    /// V3 Value Tensor (Valuation/Veracity/Validity)
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

// Custom serialization for T3 — writes canonical 3D names,
// reads both canonical and legacy 6D formats
mod t3_fields {
    use super::*;
    use serde::{Deserializer, Serializer};

    #[derive(Serialize)]
    struct T3Canonical {
        talent: f64,
        training: f64,
        temperament: f64,
    }

    // Deserialize supports both new 3D and legacy 6D formats
    #[derive(Deserialize)]
    struct T3Compat {
        // New canonical names
        #[serde(default)]
        talent: Option<f64>,
        #[serde(default)]
        training: Option<f64>,
        #[serde(default)]
        temperament: Option<f64>,
        // Legacy 6D names (for backward compat with persisted JSON)
        #[serde(default)]
        competence: Option<f64>,
        #[serde(default)]
        reliability: Option<f64>,
        #[serde(default)]
        consistency: Option<f64>,
        #[serde(default)]
        witnesses: Option<f64>,
        #[serde(default)]
        lineage: Option<f64>,
        #[serde(default)]
        alignment: Option<f64>,
    }

    pub fn serialize<S>(t3: &T3Tensor, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        T3Canonical {
            talent: t3.talent,
            training: t3.training,
            temperament: t3.temperament,
        }
        .serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<T3Tensor, D::Error>
    where
        D: Deserializer<'de>,
    {
        let compat = T3Compat::deserialize(deserializer)?;

        // If canonical names present, use them
        if let (Some(talent), Some(training), Some(temperament)) =
            (compat.talent, compat.training, compat.temperament)
        {
            return Ok(T3Tensor::new(talent, training, temperament));
        }

        // Otherwise try legacy 6D → 3D migration
        if let (Some(comp), Some(rel), Some(con), Some(wit), Some(lin), Some(ali)) = (
            compat.competence,
            compat.reliability,
            compat.consistency,
            compat.witnesses,
            compat.lineage,
            compat.alignment,
        ) {
            return Ok(T3Tensor::from_legacy_6d(comp, rel, con, wit, lin, ali));
        }

        // Fallback to neutral
        Ok(T3Tensor::neutral())
    }
}

// Custom serialization for V3 — writes canonical 3D names,
// reads both canonical and legacy 6D formats
mod v3_fields {
    use super::*;
    use serde::{Deserializer, Serializer};

    #[derive(Serialize)]
    struct V3Canonical {
        valuation: f64,
        veracity: f64,
        validity: f64,
    }

    #[derive(Deserialize)]
    struct V3Compat {
        // New canonical names
        #[serde(default)]
        valuation: Option<f64>,
        #[serde(default)]
        veracity: Option<f64>,
        #[serde(default)]
        validity: Option<f64>,
        // Legacy 6D names
        #[serde(default)]
        energy: Option<f64>,
        #[serde(default)]
        contribution: Option<f64>,
        #[serde(default)]
        stewardship: Option<f64>,
        #[serde(default)]
        network: Option<f64>,
        #[serde(default)]
        reputation: Option<f64>,
        #[serde(default)]
        temporal: Option<f64>,
    }

    pub fn serialize<S>(v3: &V3Tensor, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        V3Canonical {
            valuation: v3.valuation,
            veracity: v3.veracity,
            validity: v3.validity,
        }
        .serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<V3Tensor, D::Error>
    where
        D: Deserializer<'de>,
    {
        let compat = V3Compat::deserialize(deserializer)?;

        // If canonical names present, use them
        if let (Some(valuation), Some(veracity), Some(validity)) =
            (compat.valuation, compat.veracity, compat.validity)
        {
            return Ok(V3Tensor::new(valuation, veracity, validity));
        }

        // Otherwise try legacy 6D → 3D migration
        if let (Some(eng), Some(con), Some(stew), Some(net), Some(rep), Some(temp)) = (
            compat.energy,
            compat.contribution,
            compat.stewardship,
            compat.network,
            compat.reputation,
            compat.temporal,
        ) {
            return Ok(V3Tensor::from_legacy_6d(eng, con, stew, net, rep, temp));
        }

        // Fallback to neutral
        Ok(V3Tensor::neutral())
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

        // Update V3 valuation (effort spent)
        self.v3.add_valuation(0.01);

        self.last_action = Some(Utc::now());
    }

    /// Receive a witness event (another entity observed this one)
    ///
    /// Being witnessed builds:
    /// - temperament (T3) - more observers = more validated character
    /// - veracity (V3) - external perception of truthfulness
    /// - validity (V3) - connection to other entities
    pub fn receive_witness(&mut self, witness_id: &str, success: bool, magnitude: f64) {
        self.witness_count += 1;

        // Track who witnessed us
        if !self.witnessed_by.contains(&witness_id.to_string()) {
            self.witnessed_by.push(witness_id.to_string());
        }

        // Update T3 temperament (witness validation)
        self.t3.update_temperament_from_witness(success, magnitude);

        // Update V3 veracity and validity
        self.v3.update_veracity(success, magnitude);
        self.v3.grow_validity(0.01);
    }

    /// Give a witness event (this entity observed another)
    ///
    /// Being a witness builds:
    /// - temperament (T3) - if judgment was correct, entity shows good character
    /// - valuation (V3) - value added through validation
    pub fn give_witness(&mut self, target_id: &str, success: bool, magnitude: f64) {
        // Track who we witnessed
        if !self.has_witnessed.contains(&target_id.to_string()) {
            self.has_witnessed.push(target_id.to_string());
        }

        // Update T3 temperament (alignment)
        self.t3.update_temperament_from_alignment(success, magnitude);

        // Update V3 valuation (contribution through validation)
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
        assert!(trust.t3.training > 0.5);
        assert!(trust.last_action.is_some());
    }

    #[test]
    fn test_receive_witness() {
        let mut trust = EntityTrust::new("mcp:test");
        trust.receive_witness("session:abc", true, 0.1);

        assert_eq!(trust.witness_count, 1);
        assert!(trust.witnessed_by.contains(&"session:abc".to_string()));
        assert!(trust.t3.temperament > 0.5);
    }

    #[test]
    fn test_give_witness() {
        let mut trust = EntityTrust::new("session:abc");
        trust.give_witness("mcp:test", true, 0.1);

        assert!(trust.has_witnessed.contains(&"mcp:test".to_string()));
        assert!(trust.t3.temperament > 0.5);
    }

    #[test]
    #[cfg(feature = "file-store")]
    fn test_serialization() {
        let trust = EntityTrust::new("mcp:filesystem");
        let json = serde_json::to_string_pretty(&trust).unwrap();

        // Verify it contains canonical field names
        assert!(json.contains("\"talent\""));
        assert!(json.contains("\"training\""));
        assert!(json.contains("\"temperament\""));
        assert!(json.contains("\"valuation\""));
        assert!(json.contains("\"veracity\""));
        assert!(json.contains("\"validity\""));

        // Verify we can deserialize
        let parsed: EntityTrust = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.entity_id, trust.entity_id);
        assert_eq!(parsed.t3_average(), trust.t3_average());
    }

    #[test]
    #[cfg(feature = "file-store")]
    fn test_legacy_deserialization() {
        // Simulate old 6D JSON format
        let legacy_json = r#"{
            "entity_id": "mcp:legacy",
            "competence": 0.8,
            "reliability": 0.7,
            "consistency": 0.6,
            "witnesses": 0.5,
            "lineage": 0.9,
            "alignment": 0.4,
            "energy": 0.8,
            "contribution": 0.6,
            "stewardship": 0.5,
            "network": 0.7,
            "reputation": 0.9,
            "temporal": 0.3,
            "action_count": 50,
            "success_count": 45,
            "witness_count": 10,
            "witnessed_by": [],
            "has_witnessed": []
        }"#;

        let parsed: EntityTrust = serde_json::from_str(legacy_json).unwrap();
        assert_eq!(parsed.entity_id, "mcp:legacy");
        // talent = competence = 0.8
        assert!((parsed.t3.talent - 0.8).abs() < 0.01);
        // training = avg(0.7, 0.6, 0.9) ≈ 0.733
        assert!((parsed.t3.training - 0.733).abs() < 0.01);
        // veracity = reputation = 0.9
        assert!((parsed.v3.veracity - 0.9).abs() < 0.01);
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
