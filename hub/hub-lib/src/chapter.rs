// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2026 Metalinxx Inc.

//! Chapter directory layout + on-disk configuration.
//!
//! A chapter lives in a single directory. The layout is:
//!
//! ```text
//! <chapter-dir>/
//! ├── config.toml          # daemon + chapter metadata
//! ├── charter.json         # founding charter (see charter.rs)
//! ├── society.json         # web4_core::Society serialized state
//! └── ledger.jsonl         # witnessed event log (sprint 2 populates)
//! ```
//!
//! The Sovereign LCT lives OUTSIDE the chapter dir — the operator points
//! at it via `[sovereign].lct_path` in config.toml. This separation
//! protects the private key material from being checked into version
//! control alongside the chapter dir.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

/// Default MCP listen port. 8760 is sage-daemon's; 8770 leaves room.
pub const DEFAULT_MCP_PORT: u16 = 8770;

/// On-disk chapter config.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ChapterConfig {
    pub chapter: ChapterSection,
    pub daemon: DaemonSection,
    pub sovereign: SovereignSection,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ChapterSection {
    /// Human-readable chapter name.
    pub name: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DaemonSection {
    /// MCP server port.
    pub mcp_port: u16,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SovereignSection {
    /// Path to the Sovereign LCT file (see identity::IdentityFile).
    /// Absolute or relative-to-chapter-dir.
    pub lct_path: PathBuf,
}

impl ChapterConfig {
    pub fn new(name: String, sovereign_lct_path: PathBuf) -> Self {
        Self {
            chapter: ChapterSection { name },
            daemon: DaemonSection { mcp_port: DEFAULT_MCP_PORT },
            sovereign: SovereignSection { lct_path: sovereign_lct_path },
        }
    }

    pub fn save(&self, path: impl AsRef<Path>) -> Result<()> {
        let path = path.as_ref();
        let toml = toml::to_string_pretty(self).context("serializing config.toml")?;
        std::fs::write(path, toml)
            .with_context(|| format!("writing {}", path.display()))?;
        Ok(())
    }

    pub fn load(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        let toml_str = std::fs::read_to_string(path)
            .with_context(|| format!("reading {}", path.display()))?;
        let config: Self = toml::from_str(&toml_str)
            .with_context(|| format!("parsing {}", path.display()))?;
        Ok(config)
    }
}

/// File-path helper bound to a chapter directory.
#[derive(Clone, Debug)]
pub struct ChapterPaths {
    pub root: PathBuf,
}

impl ChapterPaths {
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Self { root: root.into() }
    }

    pub fn config(&self) -> PathBuf { self.root.join("config.toml") }
    pub fn charter(&self) -> PathBuf { self.root.join("charter.json") }
    pub fn society(&self) -> PathBuf { self.root.join("society.json") }
    pub fn ledger(&self) -> PathBuf { self.root.join("ledger.jsonl") }

    /// True if the chapter dir contains a society — i.e. has been initialized.
    pub fn is_initialized(&self) -> bool {
        self.society().exists()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn config_round_trips() {
        let dir = tempdir().unwrap();
        let cfg_path = dir.path().join("config.toml");
        let cfg = ChapterConfig::new(
            "Test Chapter".into(),
            PathBuf::from("../sovereign.json"),
        );
        cfg.save(&cfg_path).unwrap();
        let loaded = ChapterConfig::load(&cfg_path).unwrap();
        assert_eq!(loaded.chapter.name, "Test Chapter");
        assert_eq!(loaded.daemon.mcp_port, DEFAULT_MCP_PORT);
        assert_eq!(loaded.sovereign.lct_path, PathBuf::from("../sovereign.json"));
    }

    #[test]
    fn paths_resolve_off_root() {
        let p = ChapterPaths::new("/tmp/chapter");
        assert_eq!(p.config(), PathBuf::from("/tmp/chapter/config.toml"));
        assert_eq!(p.charter(), PathBuf::from("/tmp/chapter/charter.json"));
        assert_eq!(p.society(), PathBuf::from("/tmp/chapter/society.json"));
        assert_eq!(p.ledger(), PathBuf::from("/tmp/chapter/ledger.jsonl"));
    }

    #[test]
    fn is_initialized_reflects_society_file() {
        let dir = tempdir().unwrap();
        let paths = ChapterPaths::new(dir.path());
        assert!(!paths.is_initialized());
        std::fs::write(paths.society(), "{}").unwrap();
        assert!(paths.is_initialized());
    }
}
