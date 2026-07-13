//! Entity trust implementation
//!
//! **P3b convergence migration**: `EntityTrust` now holds the canonical
//! `web4_core::t3::T3` / `web4_core::v3::V3` tensors internally (fractal, with
//! per-dimension observation counts + confidence weights). There is no longer a
//! parallel `T3Tensor`/`V3Tensor`.
//!
//! Two invariants are preserved by construction (see the module tests):
//!
//! 1. **Sealed-file serde compat.** The at-rest JSON is unchanged: T3 serializes
//!    as `{talent, training, temperament}` and V3 as `{valuation, veracity,
//!    validity}`, so existing sealed `EntityTrust` files on the fleet load byte-
//!    for-byte as before. Confidence (observation counts) is additionally
//!    persisted under the optional `t3_observation_counts` / `v3_observation_counts`
//!    arrays — old files lack them and load as zero (honest "unmeasured").
//!
//! 2. **Identical update semantics.** Every mutator applies the exact same
//!    per-dimension deltas as the pre-migration `T3Tensor`/`V3Tensor` math (via
//!    the shared ports in [`crate::tensor`]), so trust trajectories on every
//!    machine are unchanged — only confidence is now additionally accrued.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::tensor::{self, TrustLevel};
use super::EntityType;
use web4_core::t3::{TrustDimension, T3};
use web4_core::v3::{ValueDimension, V3};

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

    /// T3 Trust Tensor (Talent/Training/Temperament) — canonical `web4_core` tensor.
    #[serde(flatten, with = "t3_fields")]
    pub t3: T3,

    /// V3 Value Tensor (Valuation/Veracity/Validity) — canonical `web4_core` tensor.
    #[serde(flatten, with = "v3_fields")]
    pub v3: V3,

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

// Custom serialization for T3 — reads/writes the canonical 3D field names
// (`talent`/`training`/`temperament`) so existing sealed files round-trip
// unchanged. Also:
//   * persists per-dimension observation counts under the OPTIONAL
//     `t3_observation_counts` array so confidence survives save/load
//     (old files without it load as zero counts), and
//   * still accepts the legacy 6D format for very old persisted JSON.
mod t3_fields {
    use super::*;
    use serde::{Deserializer, Serializer};

    #[derive(Serialize)]
    struct T3Canonical {
        talent: f64,
        training: f64,
        temperament: f64,
        // Optional confidence carrier — flattened into the entity object under a
        // t3-scoped key so it can't collide with the v3 counts. Absent on old
        // files; present on all files written post-migration.
        #[serde(skip_serializing_if = "Option::is_none")]
        t3_observation_counts: Option<[u64; 3]>,
    }

    // Deserialize supports canonical 3D (+ optional counts) and legacy 6D formats.
    #[derive(Deserialize)]
    struct T3Compat {
        // New canonical names
        #[serde(default)]
        talent: Option<f64>,
        #[serde(default)]
        training: Option<f64>,
        #[serde(default)]
        temperament: Option<f64>,
        // Optional per-dimension observation counts [talent, training, temperament]
        #[serde(default)]
        t3_observation_counts: Option<[u64; 3]>,
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

    pub fn serialize<S>(t3: &T3, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let counts = *t3.observation_counts();
        T3Canonical {
            talent: t3.score(TrustDimension::Talent),
            training: t3.score(TrustDimension::Training),
            temperament: t3.score(TrustDimension::Temperament),
            t3_observation_counts: Some(counts),
        }
        .serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<T3, D::Error>
    where
        D: Deserializer<'de>,
    {
        let compat = T3Compat::deserialize(deserializer)?;

        // If canonical names present, use them (+ restore confidence if carried).
        if let (Some(talent), Some(training), Some(temperament)) =
            (compat.talent, compat.training, compat.temperament)
        {
            let counts = compat.t3_observation_counts.unwrap_or([0, 0, 0]);
            return Ok(T3::from_parts([talent, training, temperament], counts));
        }

        // Otherwise try legacy 6D → 3D migration (no observation history).
        if let (Some(comp), Some(rel), Some(con), Some(wit), Some(lin), Some(ali)) = (
            compat.competence,
            compat.reliability,
            compat.consistency,
            compat.witnesses,
            compat.lineage,
            compat.alignment,
        ) {
            // Maps: talent=competence, training=avg(reliability,consistency,lineage),
            // temperament=avg(witnesses,alignment) — the old `from_legacy_6d`.
            let talent = comp;
            let training = (rel + con + lin) / 3.0;
            let temperament = (wit + ali) / 2.0;
            return Ok(T3::from_parts([talent, training, temperament], [0, 0, 0]));
        }

        // Fallback to neutral / unmeasured.
        Ok(T3::new())
    }
}

// Custom serialization for V3 — mirrors `t3_fields`.
mod v3_fields {
    use super::*;
    use serde::{Deserializer, Serializer};

    #[derive(Serialize)]
    struct V3Canonical {
        valuation: f64,
        veracity: f64,
        validity: f64,
        #[serde(skip_serializing_if = "Option::is_none")]
        v3_observation_counts: Option<[u64; 3]>,
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
        // Optional per-dimension observation counts [valuation, veracity, validity]
        #[serde(default)]
        v3_observation_counts: Option<[u64; 3]>,
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

    pub fn serialize<S>(v3: &V3, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let counts = *v3.observation_counts();
        V3Canonical {
            valuation: v3.score(ValueDimension::Valuation),
            veracity: v3.score(ValueDimension::Veracity),
            validity: v3.score(ValueDimension::Validity),
            v3_observation_counts: Some(counts),
        }
        .serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<V3, D::Error>
    where
        D: Deserializer<'de>,
    {
        let compat = V3Compat::deserialize(deserializer)?;

        if let (Some(valuation), Some(veracity), Some(validity)) =
            (compat.valuation, compat.veracity, compat.validity)
        {
            let counts = compat.v3_observation_counts.unwrap_or([0, 0, 0]);
            return Ok(V3::from_parts([valuation, veracity, validity], counts));
        }

        // Legacy 6D → 3D migration (the old `from_legacy_6d`).
        if let (Some(eng), Some(con), Some(stew), Some(net), Some(rep), Some(temp)) = (
            compat.energy,
            compat.contribution,
            compat.stewardship,
            compat.network,
            compat.reputation,
            compat.temporal,
        ) {
            let valuation = (eng + con) / 2.0;
            let veracity = rep;
            let validity = (stew + net + temp) / 3.0;
            return Ok(V3::from_parts([valuation, veracity, validity], [0, 0, 0]));
        }

        Ok(V3::new())
    }
}

impl EntityTrust {
    /// Create a new entity with default (neutral, **unmeasured**) trust.
    ///
    /// Scores start at 0.5 with **zero** observation counts — i.e. honest
    /// "unmeasured", not a fabricated 0.5-with-confidence. Only real updates
    /// raise observation counts / confidence.
    pub fn new(entity_id: impl Into<String>) -> Self {
        let entity_id = entity_id.into();
        let (entity_type, entity_name) = Self::parse_entity_id(&entity_id);

        Self {
            entity_id,
            entity_type,
            entity_name,
            t3: T3::new(),
            v3: V3::new(),
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

    // ── T3/V3 root-score accessors (canonical 3D) ────────────────────────
    // Convenience getters so consumers can read a dimension without importing
    // `TrustDimension`/`ValueDimension`. Equivalent to `self.t3.score(..)`.

    /// Talent root score (0.0–1.0).
    pub fn talent(&self) -> f64 {
        self.t3.score(TrustDimension::Talent)
    }
    /// Training root score (0.0–1.0).
    pub fn training(&self) -> f64 {
        self.t3.score(TrustDimension::Training)
    }
    /// Temperament root score (0.0–1.0).
    pub fn temperament(&self) -> f64 {
        self.t3.score(TrustDimension::Temperament)
    }
    /// Valuation root score (0.0–1.0).
    pub fn valuation(&self) -> f64 {
        self.v3.score(ValueDimension::Valuation)
    }
    /// Veracity root score (0.0–1.0).
    pub fn veracity(&self) -> f64 {
        self.v3.score(ValueDimension::Veracity)
    }
    /// Validity root score (0.0–1.0).
    pub fn validity(&self) -> f64 {
        self.v3.score(ValueDimension::Validity)
    }

    /// Get average T3 trust score (arithmetic mean of the three root scores).
    pub fn t3_average(&self) -> f64 {
        tensor::t3_average(&self.t3)
    }

    /// Get average V3 value score (arithmetic mean of the three root scores).
    pub fn v3_average(&self) -> f64 {
        tensor::v3_average(&self.v3)
    }

    /// Get categorical trust level
    pub fn trust_level(&self) -> TrustLevel {
        tensor::t3_level(&self.t3)
    }

    /// Update trust from direct action outcome
    pub fn update_from_outcome(&mut self, success: bool, magnitude: f64) {
        self.action_count += 1;
        if success {
            self.success_count += 1;
        }

        // Update T3 tensor (identical per-dimension deltas to the old math).
        tensor::t3_update_from_outcome(&mut self.t3, success, magnitude);

        // Update V3 valuation (effort spent)
        tensor::v3_add_valuation(&mut self.v3, 0.01);

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
        tensor::t3_update_temperament_from_witness(&mut self.t3, success, magnitude);

        // Update V3 veracity and validity
        tensor::v3_update_veracity(&mut self.v3, success, magnitude);
        tensor::v3_grow_validity(&mut self.v3, 0.01);
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
        tensor::t3_update_temperament_from_alignment(&mut self.t3, success, magnitude);

        // Update V3 valuation (contribution through validation)
        tensor::v3_add_valuation(&mut self.v3, 0.005);
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
        let t3_decayed = tensor::t3_apply_decay(&mut self.t3, days_inactive, decay_rate);
        tensor::v3_apply_decay(&mut self.v3, days_inactive, decay_rate);
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
        // Transparent-stub discipline: a fresh entity is unmeasured (zero
        // confidence), NOT a fabricated 0.5-with-confidence.
        for dim in TrustDimension::all() {
            assert_eq!(trust.t3.weight(dim), 0.0);
            assert_eq!(trust.t3.observation_counts()[dim as usize], 0);
        }
    }

    #[test]
    fn test_update_from_outcome() {
        let mut trust = EntityTrust::new("mcp:test");
        trust.update_from_outcome(true, 0.1);

        assert_eq!(trust.action_count, 1);
        assert_eq!(trust.success_count, 1);
        assert!(trust.training() > 0.5);
        assert!(trust.last_action.is_some());
        // A real update raises confidence.
        assert!(trust.t3.weight(TrustDimension::Training) > 0.0);
    }

    #[test]
    fn test_receive_witness() {
        let mut trust = EntityTrust::new("mcp:test");
        trust.receive_witness("session:abc", true, 0.1);

        assert_eq!(trust.witness_count, 1);
        assert!(trust.witnessed_by.contains(&"session:abc".to_string()));
        assert!(trust.temperament() > 0.5);
    }

    #[test]
    fn test_give_witness() {
        let mut trust = EntityTrust::new("session:abc");
        trust.give_witness("mcp:test", true, 0.1);

        assert!(trust.has_witnessed.contains(&"mcp:test".to_string()));
        assert!(trust.temperament() > 0.5);
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

    /// LANDMINE 1 — a hand-written OLD-format sealed file (canonical 3D names,
    /// no observation-count arrays) must still deserialize unchanged. This is
    /// the exact on-disk shape written by the pre-migration crate (crates.io
    /// 0.2.0), so existing fleet trust files load byte-for-byte.
    #[test]
    #[cfg(feature = "file-store")]
    fn test_old_format_json_still_deserializes() {
        let old = r#"{
            "entity_id": "mcp:legacy3d",
            "talent": 0.8,
            "training": 0.75,
            "temperament": 0.9,
            "valuation": 0.6,
            "veracity": 0.7,
            "validity": 0.55,
            "action_count": 12,
            "success_count": 10,
            "witness_count": 3,
            "witnessed_by": [],
            "has_witnessed": []
        }"#;
        let parsed: EntityTrust = serde_json::from_str(old).unwrap();
        assert_eq!(parsed.entity_id, "mcp:legacy3d");
        assert!((parsed.talent() - 0.8).abs() < 1e-12);
        assert!((parsed.training() - 0.75).abs() < 1e-12);
        assert!((parsed.temperament() - 0.9).abs() < 1e-12);
        assert!((parsed.valuation() - 0.6).abs() < 1e-12);
        assert!((parsed.veracity() - 0.7).abs() < 1e-12);
        assert!((parsed.validity() - 0.55).abs() < 1e-12);
        assert_eq!(parsed.action_count, 12);
        // Old files carry no confidence → unmeasured (weight 0), honest.
        for dim in TrustDimension::all() {
            assert_eq!(parsed.t3.weight(dim), 0.0);
        }
    }

    /// Confidence (observation counts) must survive a save → load round-trip via
    /// the optional `*_observation_counts` arrays.
    #[test]
    #[cfg(feature = "file-store")]
    fn test_confidence_survives_roundtrip() {
        let mut trust = EntityTrust::new("plugin:conf");
        for _ in 0..7 {
            trust.update_from_outcome(true, 0.2);
        }
        let json = serde_json::to_string(&trust).unwrap();
        assert!(json.contains("t3_observation_counts"));
        let parsed: EntityTrust = serde_json::from_str(&json).unwrap();
        for dim in TrustDimension::all() {
            assert_eq!(
                parsed.t3.observation_counts()[dim as usize],
                trust.t3.observation_counts()[dim as usize]
            );
            assert!((parsed.t3.weight(dim) - trust.t3.weight(dim)).abs() < 1e-12);
            assert!((parsed.t3.score(dim) - trust.t3.score(dim)).abs() < 1e-12);
        }
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
        assert!((parsed.talent() - 0.8).abs() < 0.01);
        // training = avg(0.7, 0.6, 0.9) ≈ 0.733
        assert!((parsed.training() - 0.733).abs() < 0.01);
        // veracity = reputation = 0.9
        assert!((parsed.veracity() - 0.9).abs() < 0.01);
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

    // ─── LANDMINE 2: semantic-preservation oracle ──────────────────────────
    //
    // A byte-for-byte copy of the PRE-MIGRATION `T3Tensor`/`V3Tensor` math acts
    // as the oracle. We drive an identical sequence of mutations through both an
    // `EntityTrust` (canonical tensor) and the oracle, and assert the resulting
    // scores are identical. If any port drifts, this fails.

    #[derive(Clone)]
    struct OracleT3 {
        talent: f64,
        training: f64,
        temperament: f64,
    }
    impl OracleT3 {
        fn neutral() -> Self {
            Self { talent: 0.5, training: 0.5, temperament: 0.5 }
        }
        fn update_from_outcome(&mut self, success: bool, magnitude: f64) {
            let magnitude = magnitude.clamp(0.0, 1.0);
            let delta = if success {
                magnitude * 0.05 * (1.0 - self.training)
            } else {
                -magnitude * 0.10 * self.training
            };
            self.training = (self.training + delta).clamp(0.0, 1.0);
            self.temperament = (self.temperament + delta * 0.5).clamp(0.0, 1.0);
            self.talent = (self.talent + delta * 0.3).clamp(0.0, 1.0);
        }
        fn update_temperament_from_witness(&mut self, success: bool, magnitude: f64) {
            let delta = if success {
                magnitude * 0.03 * (1.0 - self.temperament)
            } else {
                -magnitude * 0.05 * self.temperament
            };
            self.temperament = (self.temperament + delta).clamp(0.0, 1.0);
        }
        fn update_temperament_from_alignment(&mut self, success: bool, magnitude: f64) {
            let delta = if success {
                magnitude * 0.02 * (1.0 - self.temperament)
            } else {
                magnitude * 0.01 * (1.0 - self.temperament)
            };
            self.temperament = (self.temperament + delta).clamp(0.0, 1.0);
        }
        fn apply_decay(&mut self, days_inactive: f64, decay_rate: f64) {
            if days_inactive <= 0.0 {
                return;
            }
            let decay_factor = (1.0 - decay_rate).powf(days_inactive);
            let floor = 0.3;
            let dv = |current: f64, factor: f64| -> f64 {
                (floor + (current - floor) * decay_factor * factor).max(floor)
            };
            self.training = dv(self.training, 1.0);
            self.temperament = dv(self.temperament, 0.98);
            // Talent passes through: spec §2.3 / t3v3-012 (C192-N1). The Oracle
            // models the intended semantics, which are now the spec's.
        }
    }

    #[derive(Clone)]
    struct OracleV3 {
        valuation: f64,
        veracity: f64,
        validity: f64,
    }
    impl OracleV3 {
        fn neutral() -> Self {
            Self { valuation: 0.5, veracity: 0.5, validity: 0.5 }
        }
        fn add_valuation(&mut self, amount: f64) {
            self.valuation = (self.valuation + amount).min(1.0);
        }
        fn grow_validity(&mut self, amount: f64) {
            self.validity = (self.validity + amount).min(1.0);
        }
        fn update_veracity(&mut self, success: bool, magnitude: f64) {
            let delta = if success {
                magnitude * 0.8 * (1.0 - self.veracity)
            } else {
                -magnitude * 0.5 * self.veracity
            };
            self.veracity = (self.veracity + delta).clamp(0.0, 1.0);
        }
        fn apply_decay(&mut self, days_inactive: f64, decay_rate: f64) {
            if days_inactive <= 0.0 {
                return;
            }
            let decay_factor = (1.0 - decay_rate).powf(days_inactive);
            let floor = 0.3;
            let dv = |current: f64, factor: f64| -> f64 {
                (floor + (current - floor) * decay_factor * factor).max(floor)
            };
            self.validity = dv(self.validity, 1.0);
            self.valuation = dv(self.valuation, 0.99);
        }
    }

    #[test]
    fn test_semantic_preservation_identical_scores() {
        let mut trust = EntityTrust::new("plugin:oracle");
        let mut ot3 = OracleT3::neutral();
        let mut ov3 = OracleV3::neutral();

        // A representative sequence exercising every mutator path.
        let steps = [true, false, true, true, false, false, true, false];
        for (i, &success) in steps.iter().enumerate() {
            let magnitude = 0.05 + (i as f64) * 0.1; // varied, some > 1.0 → clamps

            // update_from_outcome
            trust.update_from_outcome(success, magnitude);
            ot3.update_from_outcome(success, magnitude);
            ov3.add_valuation(0.01);

            // receive_witness → temperament(witness) + veracity + validity(+0.01)
            trust.receive_witness("session:w", success, magnitude);
            ot3.update_temperament_from_witness(success, magnitude);
            ov3.update_veracity(success, magnitude);
            ov3.grow_validity(0.01);

            // give_witness → temperament(alignment) + valuation(+0.005)
            trust.give_witness("mcp:t", success, magnitude);
            ot3.update_temperament_from_alignment(success, magnitude);
            ov3.add_valuation(0.005);

            // apply_decay
            trust.apply_decay(3.0, 0.02);
            ot3.apply_decay(3.0, 0.02);
            ov3.apply_decay(3.0, 0.02);

            // Assert identical scores at every step.
            assert!((trust.talent() - ot3.talent).abs() < 1e-12, "talent step {i}");
            assert!((trust.training() - ot3.training).abs() < 1e-12, "training step {i}");
            assert!((trust.temperament() - ot3.temperament).abs() < 1e-12, "temperament step {i}");
            assert!((trust.valuation() - ov3.valuation).abs() < 1e-12, "valuation step {i}");
            assert!((trust.veracity() - ov3.veracity).abs() < 1e-12, "veracity step {i}");
            assert!((trust.validity() - ov3.validity).abs() < 1e-12, "validity step {i}");
        }
    }
}
