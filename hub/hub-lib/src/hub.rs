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
//! The Sovereign LCT lives OUTSIDE the hub dir — the operator points
//! at it via `[sovereign].lct_path` in config.toml. This separation
//! protects the private key material from being checked into version
//! control alongside the hub dir.

use anyhow::{anyhow, Context, Result};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use uuid::Uuid;
use web4_core::lct::{EntityType, Lct};

/// Default MCP listen port. 8760 is sage-daemon's; 8770 leaves room.
pub const DEFAULT_MCP_PORT: u16 = 8770;

/// On-disk hub config.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct HubConfig {
    /// Serialized as `[hub]` in TOML. Accepts `[chapter]` for back-compat
    /// with hub dirs created before the chapter→hub rename.
    #[serde(alias = "chapter")]
    pub hub: HubSection,
    pub daemon: DaemonSection,
    pub sovereign: SovereignSection,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct HubSection {
    /// Human-readable hub name.
    pub name: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct DaemonSection {
    /// MCP server port.
    pub mcp_port: u16,
}

/// Sovereign config: either local-file mode (MVP, deprecated) OR
/// Hestia-mode (V2-7+, per architecture commitment #8). Exactly one
/// mode must be populated; [`Self::mode`] validates + classifies.
#[derive(Clone, Debug, Serialize, Deserialize, Default)]
pub struct SovereignSection {
    /// **Local mode** (MVP, deprecated post-V2-7):
    /// Path to the Sovereign IdentityFile (LCT + keypair). Absolute or
    /// relative-to-chapter-dir.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub lct_path: Option<PathBuf>,

    /// **Hestia mode** (V2-7+, recommended):
    /// URL of the Sovereign's Hestia sign-request callback. The hub
    /// POSTs SignRequest here whenever a Sovereign-signed ledger entry
    /// is needed; Hestia decides per its authority+need-to-know gate.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub hestia_callback_url: Option<String>,

    /// **Hestia mode**: the Sovereign's LCT id (the entity Hestia signs
    /// for). The hub needs this to label the signer + verify envelopes
    /// claiming this signer.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub lct_id: Option<Uuid>,

    /// **Hestia mode**: the Sovereign's public key (hex-encoded raw 32
    /// bytes). The hub uses this to verify envelopes signed by the
    /// Sovereign (it doesn't have the IdentityFile to load Lct from
    /// in Hestia mode).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pubkey_hex: Option<String>,
}

/// Which mode a [`SovereignSection`] is in. Used by `hub serve` to
/// choose the right signer + by `hub init` to write the right config.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum SovereignMode {
    /// Local IdentityFile holds the Sovereign keypair. MVP-compat.
    Local { lct_path: PathBuf },
    /// Hestia vault holds the keypair; hub knows only the LCT id +
    /// public key + callback URL.
    Hestia {
        callback_url: String,
        lct_id: Uuid,
        pubkey_hex: String,
    },
}

/// Synthesize a minimal Lct from a Hestia-mode config's stored
/// pubkey + lct_id. In Hestia mode, the hub holds NO IdentityFile —
/// only the public key — so envelope verification / ledger
/// verification needs this construction path.
///
/// The synthesized Lct carries Human entity_type (matches `hub gen-lct
/// --entity-type human` default for Sovereigns) and uses current time
/// for created_at. Neither field is consulted by signature
/// verification; only `id` and `public_key` are used by
/// `verify_signature`.
pub fn hestia_sovereign_lct(lct_id: Uuid, pubkey_hex: &str) -> Result<Lct> {
    use web4_core::crypto::PublicKey;
    use web4_core::lct::{HardwareBinding, LctStatus};
    use chrono::Utc;

    let pubkey_bytes = hex::decode(pubkey_hex)
        .with_context(|| format!("decoding sovereign pubkey_hex '{}'", pubkey_hex))?;
    let arr: [u8; 32] = pubkey_bytes.as_slice().try_into()
        .map_err(|_| anyhow!("sovereign pubkey must be 32 bytes (got {})", pubkey_bytes.len()))?;
    let public_key = PublicKey::from_bytes(&arr)
        .context("constructing PublicKey from sovereign pubkey_hex")?;

    Ok(Lct {
        id: lct_id,
        entity_type: EntityType::Human,
        status: LctStatus::Active,
        public_key,
        created_at: Utc::now(),
        created_by: None,
        hardware_binding: HardwareBinding::default(),
        parent_id: None,
        lineage_depth: 0,
    })
}

impl SovereignSection {
    /// Validate + classify which mode this config is in. Exactly one
    /// mode must be populated.
    pub fn mode(&self) -> Result<SovereignMode> {
        let local_set = self.lct_path.is_some();
        let hestia_set = self.hestia_callback_url.is_some()
            || self.lct_id.is_some()
            || self.pubkey_hex.is_some();
        match (local_set, hestia_set) {
            (true, true) => Err(anyhow!(
                "[sovereign] has both local (lct_path) and Hestia fields set; pick one"
            )),
            (false, false) => Err(anyhow!(
                "[sovereign] has no mode configured; set either lct_path (local) \
                 or {{hestia_callback_url, lct_id, pubkey_hex}} (Hestia)"
            )),
            (true, false) => Ok(SovereignMode::Local {
                lct_path: self.lct_path.clone().unwrap(),
            }),
            (false, true) => {
                let callback_url = self.hestia_callback_url.clone().ok_or_else(|| anyhow!(
                    "[sovereign] Hestia mode requires hestia_callback_url"
                ))?;
                let lct_id = self.lct_id.ok_or_else(|| anyhow!(
                    "[sovereign] Hestia mode requires lct_id"
                ))?;
                let pubkey_hex = self.pubkey_hex.clone().ok_or_else(|| anyhow!(
                    "[sovereign] Hestia mode requires pubkey_hex"
                ))?;
                Ok(SovereignMode::Hestia { callback_url, lct_id, pubkey_hex })
            }
        }
    }
}

impl HubConfig {
    /// Local-mode constructor (MVP-compat).
    pub fn new(name: String, sovereign_lct_path: PathBuf) -> Self {
        Self {
            hub: HubSection { name },
            daemon: DaemonSection { mcp_port: DEFAULT_MCP_PORT },
            sovereign: SovereignSection {
                lct_path: Some(sovereign_lct_path),
                ..Default::default()
            },
        }
    }

    /// Hestia-mode constructor (V2-7+).
    pub fn new_hestia(
        name: String,
        callback_url: String,
        lct_id: Uuid,
        pubkey_hex: String,
    ) -> Self {
        Self {
            hub: HubSection { name },
            daemon: DaemonSection { mcp_port: DEFAULT_MCP_PORT },
            sovereign: SovereignSection {
                lct_path: None,
                hestia_callback_url: Some(callback_url),
                lct_id: Some(lct_id),
                pubkey_hex: Some(pubkey_hex),
            },
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

/// File-path helper bound to a hub directory.
#[derive(Clone, Debug)]
pub struct HubPaths {
    pub root: PathBuf,
}

impl HubPaths {
    pub fn new(root: impl Into<PathBuf>) -> Self {
        Self { root: root.into() }
    }

    pub fn config(&self) -> PathBuf { self.root.join("config.toml") }
    pub fn charter(&self) -> PathBuf { self.root.join("charter.json") }
    pub fn society(&self) -> PathBuf { self.root.join("society.json") }
    pub fn ledger(&self) -> PathBuf { self.root.join("ledger.jsonl") }

    /// True if the hub dir contains a society — i.e. has been initialized.
    pub fn is_initialized(&self) -> bool {
        self.society().exists()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[tokio::test]
    async fn config_round_trips() {
        let dir = tempdir().unwrap();
        let cfg_path = dir.path().join("config.toml");
        let cfg = HubConfig::new(
            "Test Chapter".into(),
            PathBuf::from("../sovereign.json"),
        );
        cfg.save(&cfg_path).unwrap();
        let loaded = HubConfig::load(&cfg_path).unwrap();
        assert_eq!(loaded.hub.name, "Test Chapter");
        assert_eq!(loaded.daemon.mcp_port, DEFAULT_MCP_PORT);
        assert_eq!(loaded.sovereign.lct_path, Some(PathBuf::from("../sovereign.json")));
    }

    #[tokio::test]
    async fn paths_resolve_off_root() {
        let p = HubPaths::new("/tmp/chapter");
        assert_eq!(p.config(), PathBuf::from("/tmp/chapter/config.toml"));
        assert_eq!(p.charter(), PathBuf::from("/tmp/chapter/charter.json"));
        assert_eq!(p.society(), PathBuf::from("/tmp/chapter/society.json"));
        assert_eq!(p.ledger(), PathBuf::from("/tmp/chapter/ledger.jsonl"));
    }

    #[tokio::test]
    async fn is_initialized_reflects_society_file() {
        let dir = tempdir().unwrap();
        let paths = HubPaths::new(dir.path());
        assert!(!paths.is_initialized());
        std::fs::write(paths.society(), "{}").unwrap();
        assert!(paths.is_initialized());
    }
}
