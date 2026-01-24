//! Storage trait definition

use crate::{EntityTrust, EntityType, Result};

/// Trait for entity trust storage backends
pub trait TrustStore {
    /// Get trust for an entity by ID
    ///
    /// Returns the stored trust or creates a new entity with neutral trust.
    fn get(&self, entity_id: &str) -> Result<EntityTrust>;

    /// Get trust only if entity exists (no auto-creation)
    fn get_existing(&self, entity_id: &str) -> Result<Option<EntityTrust>>;

    /// Save entity trust
    fn save(&self, trust: &EntityTrust) -> Result<()>;

    /// Delete an entity
    fn delete(&self, entity_id: &str) -> Result<bool>;

    /// List all entity IDs, optionally filtered by type
    fn list(&self, entity_type: Option<&EntityType>) -> Result<Vec<String>>;

    /// Check if an entity exists
    fn exists(&self, entity_id: &str) -> Result<bool>;

    /// Get or create an entity with neutral trust
    fn get_or_create(&self, entity_id: &str) -> Result<EntityTrust> {
        self.get(entity_id)
    }

    /// Update entity trust from an action outcome
    fn update(&self, entity_id: &str, success: bool, magnitude: f64) -> Result<EntityTrust> {
        let mut trust = self.get(entity_id)?;
        trust.update_from_outcome(success, magnitude);
        self.save(&trust)?;
        Ok(trust)
    }

    /// Record a witnessing event between two entities
    ///
    /// Returns (witness_trust, target_trust) after updates.
    fn witness(
        &self,
        witness_id: &str,
        target_id: &str,
        success: bool,
        magnitude: f64,
    ) -> Result<(EntityTrust, EntityTrust)> {
        // Update target (being witnessed)
        let mut target = self.get(target_id)?;
        target.receive_witness(witness_id, success, magnitude);
        self.save(&target)?;

        // Update witness (doing the witnessing)
        let mut witness = self.get(witness_id)?;
        witness.give_witness(target_id, success, magnitude);
        self.save(&witness)?;

        Ok((witness, target))
    }

    /// Get count of entities, optionally by type
    fn count(&self, entity_type: Option<&EntityType>) -> Result<usize> {
        Ok(self.list(entity_type)?.len())
    }
}
