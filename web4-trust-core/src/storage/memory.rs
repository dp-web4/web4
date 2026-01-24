//! In-memory storage implementation

use std::collections::HashMap;
use std::sync::RwLock;

use crate::{EntityTrust, EntityType, Error, Result};
use super::TrustStore;

/// In-memory trust store
///
/// Useful for testing and WASM environments.
/// Data is lost when the store is dropped.
pub struct InMemoryStore {
    entities: RwLock<HashMap<String, EntityTrust>>,
}

impl InMemoryStore {
    /// Create a new empty in-memory store
    pub fn new() -> Self {
        Self {
            entities: RwLock::new(HashMap::new()),
        }
    }

    /// Create a store with initial entities
    pub fn with_entities(entities: Vec<EntityTrust>) -> Self {
        let map: HashMap<String, EntityTrust> = entities
            .into_iter()
            .map(|e| (e.entity_id.clone(), e))
            .collect();

        Self {
            entities: RwLock::new(map),
        }
    }

    /// Get number of stored entities
    pub fn len(&self) -> usize {
        self.entities.read().unwrap().len()
    }

    /// Check if store is empty
    pub fn is_empty(&self) -> bool {
        self.entities.read().unwrap().is_empty()
    }

    /// Clear all entities
    pub fn clear(&self) {
        self.entities.write().unwrap().clear();
    }
}

impl Default for InMemoryStore {
    fn default() -> Self {
        Self::new()
    }
}

impl TrustStore for InMemoryStore {
    fn get(&self, entity_id: &str) -> Result<EntityTrust> {
        let entities = self.entities.read().map_err(|e| Error::Storage(e.to_string()))?;

        if let Some(trust) = entities.get(entity_id) {
            Ok(trust.clone())
        } else {
            drop(entities); // Release read lock

            // Create new entity
            let trust = EntityTrust::new(entity_id);
            self.save(&trust)?;
            Ok(trust)
        }
    }

    fn get_existing(&self, entity_id: &str) -> Result<Option<EntityTrust>> {
        let entities = self.entities.read().map_err(|e| Error::Storage(e.to_string()))?;
        Ok(entities.get(entity_id).cloned())
    }

    fn save(&self, trust: &EntityTrust) -> Result<()> {
        let mut entities = self.entities.write().map_err(|e| Error::Storage(e.to_string()))?;
        entities.insert(trust.entity_id.clone(), trust.clone());
        Ok(())
    }

    fn delete(&self, entity_id: &str) -> Result<bool> {
        let mut entities = self.entities.write().map_err(|e| Error::Storage(e.to_string()))?;
        Ok(entities.remove(entity_id).is_some())
    }

    fn list(&self, entity_type: Option<&EntityType>) -> Result<Vec<String>> {
        let entities = self.entities.read().map_err(|e| Error::Storage(e.to_string()))?;

        let ids: Vec<String> = match entity_type {
            Some(etype) => {
                let type_prefix = etype.type_prefix();
                entities
                    .keys()
                    .filter(|id| id.starts_with(&format!("{}:", type_prefix)))
                    .cloned()
                    .collect()
            }
            None => entities.keys().cloned().collect(),
        };

        Ok(ids)
    }

    fn exists(&self, entity_id: &str) -> Result<bool> {
        let entities = self.entities.read().map_err(|e| Error::Storage(e.to_string()))?;
        Ok(entities.contains_key(entity_id))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_store() {
        let store = InMemoryStore::new();
        assert!(store.is_empty());
    }

    #[test]
    fn test_get_creates_entity() {
        let store = InMemoryStore::new();

        let trust = store.get("mcp:filesystem").unwrap();
        assert_eq!(trust.entity_id, "mcp:filesystem");
        assert_eq!(store.len(), 1);
    }

    #[test]
    fn test_save_and_get() {
        let store = InMemoryStore::new();

        let mut trust = EntityTrust::new("mcp:test");
        trust.update_from_outcome(true, 0.1);
        store.save(&trust).unwrap();

        let loaded = store.get("mcp:test").unwrap();
        assert_eq!(loaded.action_count, 1);
    }

    #[test]
    fn test_get_existing() {
        let store = InMemoryStore::new();

        // Doesn't exist yet
        assert!(store.get_existing("mcp:test").unwrap().is_none());

        // Create it
        store.get("mcp:test").unwrap();

        // Now exists
        assert!(store.get_existing("mcp:test").unwrap().is_some());
    }

    #[test]
    fn test_delete() {
        let store = InMemoryStore::new();

        store.get("mcp:test").unwrap();
        assert!(store.exists("mcp:test").unwrap());

        let deleted = store.delete("mcp:test").unwrap();
        assert!(deleted);
        assert!(!store.exists("mcp:test").unwrap());
    }

    #[test]
    fn test_list() {
        let store = InMemoryStore::new();

        store.get("mcp:a").unwrap();
        store.get("mcp:b").unwrap();
        store.get("role:x").unwrap();

        let all = store.list(None).unwrap();
        assert_eq!(all.len(), 3);

        let mcps = store.list(Some(&EntityType::Mcp("".to_string()))).unwrap();
        assert_eq!(mcps.len(), 2);

        let roles = store.list(Some(&EntityType::Role("".to_string()))).unwrap();
        assert_eq!(roles.len(), 1);
    }

    #[test]
    fn test_witness() {
        let store = InMemoryStore::new();

        let (witness, target) = store.witness("session:a", "mcp:b", true, 0.1).unwrap();

        assert!(target.witnessed_by.contains(&"session:a".to_string()));
        assert!(witness.has_witnessed.contains(&"mcp:b".to_string()));
    }

    #[test]
    fn test_update() {
        let store = InMemoryStore::new();

        let trust = store.update("mcp:test", true, 0.1).unwrap();
        assert_eq!(trust.action_count, 1);
        assert_eq!(trust.success_count, 1);

        let trust = store.update("mcp:test", false, 0.1).unwrap();
        assert_eq!(trust.action_count, 2);
        assert_eq!(trust.success_count, 1);
    }
}
