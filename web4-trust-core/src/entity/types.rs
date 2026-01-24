//! Entity type definitions

use serde::{Deserialize, Serialize};
use crate::{Error, Result};

/// Types of entities in the Web4 ecosystem
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(tag = "type", content = "name")]
pub enum EntityType {
    /// MCP server (e.g., "mcp:filesystem")
    Mcp(String),
    /// Agent role (e.g., "role:code-reviewer")
    Role(String),
    /// Session identity (e.g., "session:abc123")
    Session(String),
    /// Reference/context (e.g., "ref:pattern-123")
    Reference(String),
    /// Linked Context Token (e.g., "lct:...")
    Lct(String),
    /// Unknown/other entity type
    Other(String),
}

impl EntityType {
    /// Parse entity type from an entity ID string
    ///
    /// Entity IDs follow the format "type:name"
    ///
    /// # Examples
    /// ```
    /// use web4_trust_core::EntityType;
    ///
    /// let etype = EntityType::from_entity_id("mcp:filesystem").unwrap();
    /// assert!(matches!(etype, EntityType::Mcp(_)));
    /// ```
    pub fn from_entity_id(entity_id: &str) -> Result<Self> {
        let parts: Vec<&str> = entity_id.splitn(2, ':').collect();

        if parts.len() != 2 {
            return Err(Error::InvalidEntityId(format!(
                "Expected format 'type:name', got '{}'",
                entity_id
            )));
        }

        let (type_str, name) = (parts[0], parts[1]);
        let name = name.to_string();

        Ok(match type_str {
            "mcp" => EntityType::Mcp(name),
            "role" => EntityType::Role(name),
            "session" => EntityType::Session(name),
            "ref" => EntityType::Reference(name),
            "lct" => EntityType::Lct(name),
            _ => EntityType::Other(format!("{}:{}", type_str, name)),
        })
    }

    /// Get the type prefix string
    pub fn type_prefix(&self) -> &'static str {
        match self {
            EntityType::Mcp(_) => "mcp",
            EntityType::Role(_) => "role",
            EntityType::Session(_) => "session",
            EntityType::Reference(_) => "ref",
            EntityType::Lct(_) => "lct",
            EntityType::Other(_) => "other",
        }
    }

    /// Get the entity name (without type prefix)
    pub fn name(&self) -> &str {
        match self {
            EntityType::Mcp(name) => name,
            EntityType::Role(name) => name,
            EntityType::Session(name) => name,
            EntityType::Reference(name) => name,
            EntityType::Lct(name) => name,
            EntityType::Other(name) => name,
        }
    }

    /// Convert to full entity ID string
    pub fn to_entity_id(&self) -> String {
        match self {
            EntityType::Other(name) => name.clone(),
            _ => format!("{}:{}", self.type_prefix(), self.name()),
        }
    }

    /// Check if this is an MCP server
    pub fn is_mcp(&self) -> bool {
        matches!(self, EntityType::Mcp(_))
    }

    /// Check if this is a role
    pub fn is_role(&self) -> bool {
        matches!(self, EntityType::Role(_))
    }

    /// Check if this is a session
    pub fn is_session(&self) -> bool {
        matches!(self, EntityType::Session(_))
    }
}

impl std::fmt::Display for EntityType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.to_entity_id())
    }
}

impl std::str::FromStr for EntityType {
    type Err = Error;

    fn from_str(s: &str) -> Result<Self> {
        Self::from_entity_id(s)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_mcp() {
        let etype = EntityType::from_entity_id("mcp:filesystem").unwrap();
        assert!(matches!(etype, EntityType::Mcp(ref name) if name == "filesystem"));
        assert_eq!(etype.type_prefix(), "mcp");
        assert_eq!(etype.name(), "filesystem");
    }

    #[test]
    fn test_parse_role() {
        let etype = EntityType::from_entity_id("role:code-reviewer").unwrap();
        assert!(matches!(etype, EntityType::Role(ref name) if name == "code-reviewer"));
    }

    #[test]
    fn test_parse_session() {
        let etype = EntityType::from_entity_id("session:abc123").unwrap();
        assert!(matches!(etype, EntityType::Session(ref name) if name == "abc123"));
    }

    #[test]
    fn test_to_entity_id() {
        let etype = EntityType::Mcp("filesystem".to_string());
        assert_eq!(etype.to_entity_id(), "mcp:filesystem");
    }

    #[test]
    fn test_invalid_format() {
        let result = EntityType::from_entity_id("invalid");
        assert!(result.is_err());
    }

    #[test]
    fn test_unknown_type() {
        let etype = EntityType::from_entity_id("custom:thing").unwrap();
        assert!(matches!(etype, EntityType::Other(_)));
    }
}
