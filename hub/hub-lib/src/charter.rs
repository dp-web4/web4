// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Chapter charter — the constitutional document of a chapter society.
//!
//! Sprint 1: minimal charter with chapter name, founding date, Sovereign LCT
//! reference, a free-text preamble, and an empty rules list. The charter
//! gets sha256-hashed and the hash goes into `web4_core::Society::charter_hash`.
//!
//! Sprint 6+ may add structured rules, amendment history, and law-oracle-
//! consumable machine-readable sections. For MVP, the charter is a document;
//! enforcement is human (chapter members read the rules).

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::path::Path;
use uuid::Uuid;
use web4_core::crypto::sha256_hex;

/// Schema version of the on-disk charter file. Bump on breaking changes.
pub const CHARTER_SCHEMA_VERSION: &str = "0.1";

/// A chapter charter — minimal MVP shape.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Charter {
    /// Schema version. Bump when fields change incompatibly.
    pub schema_version: String,

    /// Human-readable chapter name (e.g. "Lisbon Chapter").
    pub hub_name: String,

    /// When the charter was founded.
    pub founded_at: DateTime<Utc>,

    /// The Sovereign LCT that signs the charter at genesis.
    pub founding_sovereign_lct_id: Uuid,

    /// Free-text preamble — the chapter's purpose, scope, and ethos.
    /// MVP: plain text. V2: structured markdown.
    pub preamble: String,

    /// Rules — empty in MVP. Future: structured rule entries the Law Oracle
    /// can publish and the Policy Entity can enforce.
    #[serde(default)]
    pub rules: Vec<String>,

    /// Amendment history. Empty at founding; entries appended by Sovereign-
    /// signed amendment events recorded in the ledger.
    #[serde(default)]
    pub amendments: Vec<String>,
}

impl Charter {
    /// Compose a fresh founding charter for a new chapter.
    pub fn found(hub_name: String, sovereign_lct_id: Uuid) -> Self {
        Self {
            schema_version: CHARTER_SCHEMA_VERSION.to_string(),
            hub_name: hub_name.clone(),
            founded_at: Utc::now(),
            founding_sovereign_lct_id: sovereign_lct_id,
            preamble: default_preamble(&hub_name),
            rules: Vec::new(),
            amendments: Vec::new(),
        }
    }

    /// Canonical sha256 hash of the charter — feeds `Society::charter_hash`.
    /// Uses sorted-key JSON via serde_json::to_string (serde_json is ordered
    /// by struct field order, which is stable across builds because we
    /// don't use HashMap fields in Charter).
    pub fn hash(&self) -> Result<String> {
        let canonical = serde_json::to_string(self)
            .context("serializing charter for hashing")?;
        Ok(format!("sha256:{}", sha256_hex(canonical.as_bytes())))
    }

    /// Write the charter to disk as pretty-printed JSON.
    pub fn save(&self, path: impl AsRef<Path>) -> Result<()> {
        let path = path.as_ref();
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)
                .with_context(|| format!("creating parent dir {}", parent.display()))?;
        }
        let json = serde_json::to_string_pretty(self)
            .context("serializing charter")?;
        std::fs::write(path, json)
            .with_context(|| format!("writing charter to {}", path.display()))?;
        Ok(())
    }

    /// Load a charter from disk.
    pub fn load(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        let json = std::fs::read_to_string(path)
            .with_context(|| format!("reading charter from {}", path.display()))?;
        let charter: Self = serde_json::from_str(&json)
            .with_context(|| format!("parsing charter at {}", path.display()))?;
        Ok(charter)
    }
}

fn default_preamble(hub_name: &str) -> String {
    format!(
        "This is the founding charter of the {name}. \
         The {name} is constituted as a Web4 society — sovereign, \
         federation-capable, and accountable to its members through \
         witnessed action. Members hold portable identity (LCT) and \
         accrue reputation (T3/V3) by attested contribution. The \
         chapter operates by chapter law, signed by the Sovereign and \
         amendable through the witnessed process the law itself defines.",
        name = hub_name
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use uuid::Uuid;

    #[tokio::test]
    async fn founding_charter_has_expected_shape() {
        let sovereign = Uuid::new_v4();
        let charter = Charter::found("Lisbon Chapter".into(), sovereign);

        assert_eq!(charter.schema_version, CHARTER_SCHEMA_VERSION);
        assert_eq!(charter.hub_name, "Lisbon Chapter");
        assert_eq!(charter.founding_sovereign_lct_id, sovereign);
        assert!(charter.rules.is_empty());
        assert!(charter.amendments.is_empty());
        assert!(charter.preamble.contains("Lisbon Chapter"));
        assert!(charter.preamble.contains("Web4 society"));
    }

    #[tokio::test]
    async fn hash_is_stable_and_prefixed() {
        let sovereign = Uuid::new_v4();
        let charter = Charter::found("Test".into(), sovereign);
        let h1 = charter.hash().unwrap();
        let h2 = charter.hash().unwrap();
        assert_eq!(h1, h2, "hash must be deterministic for the same content");
        assert!(h1.starts_with("sha256:"), "hash must carry algorithm prefix");
        assert_eq!(h1.len(), "sha256:".len() + 64, "sha256 hex is 64 chars");
    }

    #[tokio::test]
    async fn hash_changes_when_content_changes() {
        let sovereign = Uuid::new_v4();
        let mut charter = Charter::found("Test".into(), sovereign);
        let h1 = charter.hash().unwrap();
        charter.preamble.push_str(" (amended)");
        let h2 = charter.hash().unwrap();
        assert_ne!(h1, h2);
    }
}
