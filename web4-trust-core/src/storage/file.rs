//! File-based storage (JSON)
//!
//! Compatible with the Python implementation's JSON format.
//! Each entity is stored in a separate file named by SHA256 hash of entity_id.

use std::fs;
use std::path::{Path, PathBuf};
use sha2::{Sha256, Digest};

use crate::{EntityTrust, EntityType, Error, Result};
use super::TrustStore;

/// File-based trust store using JSON files
///
/// Compatible with the Python implementation.
/// Each entity is stored in `{base_dir}/{hash}.json`.
pub struct FileStore {
    base_dir: PathBuf,
}

impl FileStore {
    /// Create a new file store at the given directory
    pub fn new(base_dir: impl AsRef<Path>) -> Result<Self> {
        let base_dir = base_dir.as_ref().to_path_buf();

        // Create directory if it doesn't exist
        fs::create_dir_all(&base_dir)?;

        Ok(Self { base_dir })
    }

    /// Open the default store location (~/.web4/governance/entities)
    pub fn open_default() -> Result<Self> {
        let home = dirs::home_dir().ok_or_else(|| Error::Storage("Cannot find home directory".to_string()))?;
        let base_dir = home.join(".web4").join("governance").join("entities");
        Self::new(base_dir)
    }

    /// Get the file path for an entity ID
    fn entity_file(&self, entity_id: &str) -> PathBuf {
        let mut hasher = Sha256::new();
        hasher.update(entity_id.as_bytes());
        let hash = format!("{:x}", hasher.finalize());
        let short_hash = &hash[..16];
        self.base_dir.join(format!("{}.json", short_hash))
    }

    /// Get the base directory
    pub fn base_dir(&self) -> &Path {
        &self.base_dir
    }
}

impl TrustStore for FileStore {
    fn get(&self, entity_id: &str) -> Result<EntityTrust> {
        let file_path = self.entity_file(entity_id);

        if file_path.exists() {
            let content = fs::read_to_string(&file_path)?;
            let trust: EntityTrust = serde_json::from_str(&content)
                .map_err(|e| Error::Serialization(e.to_string()))?;
            Ok(trust)
        } else {
            // Create new entity with neutral trust
            let trust = EntityTrust::new(entity_id);
            self.save(&trust)?;
            Ok(trust)
        }
    }

    fn get_existing(&self, entity_id: &str) -> Result<Option<EntityTrust>> {
        let file_path = self.entity_file(entity_id);

        if file_path.exists() {
            let content = fs::read_to_string(&file_path)?;
            let trust: EntityTrust = serde_json::from_str(&content)
                .map_err(|e| Error::Serialization(e.to_string()))?;
            Ok(Some(trust))
        } else {
            Ok(None)
        }
    }

    fn save(&self, trust: &EntityTrust) -> Result<()> {
        let file_path = self.entity_file(&trust.entity_id);
        let content = serde_json::to_string_pretty(trust)
            .map_err(|e| Error::Serialization(e.to_string()))?;
        fs::write(&file_path, content)?;
        Ok(())
    }

    fn delete(&self, entity_id: &str) -> Result<bool> {
        let file_path = self.entity_file(entity_id);

        if file_path.exists() {
            fs::remove_file(&file_path)?;
            Ok(true)
        } else {
            Ok(false)
        }
    }

    fn list(&self, entity_type: Option<&EntityType>) -> Result<Vec<String>> {
        let mut entities = Vec::new();

        for entry in fs::read_dir(&self.base_dir)? {
            let entry = entry?;
            let path = entry.path();

            if path.extension().map_or(false, |ext| ext == "json") {
                // Read and parse to get entity_id
                if let Ok(content) = fs::read_to_string(&path) {
                    if let Ok(trust) = serde_json::from_str::<EntityTrust>(&content) {
                        // Filter by type if specified
                        let include = match entity_type {
                            Some(etype) => trust.entity_type == etype.type_prefix(),
                            None => true,
                        };

                        if include {
                            entities.push(trust.entity_id);
                        }
                    }
                }
            }
        }

        Ok(entities)
    }

    fn exists(&self, entity_id: &str) -> Result<bool> {
        let file_path = self.entity_file(entity_id);
        Ok(file_path.exists())
    }
}

// Add dirs dependency for home directory detection
// Note: In real implementation, add `dirs = "5.0"` to Cargo.toml
mod dirs {
    use std::path::PathBuf;

    pub fn home_dir() -> Option<PathBuf> {
        std::env::var_os("HOME")
            .or_else(|| std::env::var_os("USERPROFILE"))
            .map(PathBuf::from)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn temp_store() -> (FileStore, TempDir) {
        let temp_dir = TempDir::new().unwrap();
        let store = FileStore::new(temp_dir.path()).unwrap();
        (store, temp_dir)
    }

    #[test]
    fn test_new_store() {
        let (store, _temp) = temp_store();
        assert!(store.base_dir().exists());
    }

    #[test]
    fn test_get_creates_file() {
        let (store, _temp) = temp_store();

        let trust = store.get("mcp:filesystem").unwrap();
        assert_eq!(trust.entity_id, "mcp:filesystem");

        // File should exist
        let file_path = store.entity_file("mcp:filesystem");
        assert!(file_path.exists());
    }

    #[test]
    fn test_save_and_load() {
        let (store, _temp) = temp_store();

        let mut trust = EntityTrust::new("mcp:test");
        trust.update_from_outcome(true, 0.1);
        store.save(&trust).unwrap();

        let loaded = store.get("mcp:test").unwrap();
        assert_eq!(loaded.action_count, 1);
        assert_eq!(loaded.success_count, 1);
    }

    #[test]
    fn test_list() {
        let (store, _temp) = temp_store();

        store.get("mcp:a").unwrap();
        store.get("mcp:b").unwrap();
        store.get("role:x").unwrap();

        let all = store.list(None).unwrap();
        assert_eq!(all.len(), 3);

        let mcps = store.list(Some(&EntityType::Mcp("".to_string()))).unwrap();
        assert_eq!(mcps.len(), 2);
    }

    #[test]
    fn test_delete() {
        let (store, _temp) = temp_store();

        store.get("mcp:test").unwrap();
        assert!(store.exists("mcp:test").unwrap());

        store.delete("mcp:test").unwrap();
        assert!(!store.exists("mcp:test").unwrap());
    }

    #[test]
    fn test_json_format_compatibility() {
        let (store, _temp) = temp_store();

        let mut trust = EntityTrust::new("mcp:filesystem");
        trust.update_from_outcome(true, 0.1);
        trust.receive_witness("session:abc", true, 0.05);
        store.save(&trust).unwrap();

        // Read the raw JSON to verify format
        let file_path = store.entity_file("mcp:filesystem");
        let content = fs::read_to_string(&file_path).unwrap();

        // Should have flattened canonical 3D fields
        assert!(content.contains("\"entity_id\""));
        assert!(content.contains("\"talent\""));
        assert!(content.contains("\"training\""));
        assert!(content.contains("\"valuation\""));
        assert!(content.contains("\"witnessed_by\""));
    }
}
