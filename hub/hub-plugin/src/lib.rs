//! `hub-plugin` — the generic hub tool-plugin seam.
//!
//! Core (the hub daemon) owns authn + policy gating + tier scoping + sealing;
//! **plugins own the handler.** This crate is the keystone of the hub's
//! open-core split: it defines the generic [`ToolPlugin`] contract and the
//! `gate → handle → scope` dispatch path, and names no specific tool. Concrete
//! handlers — generic or specialized — live in their own crates that implement
//! [`ToolPlugin`] and register with the [`PluginRegistry`]; the core never has
//! to know what a given tool does, only how to gate, run, and bound it.

use async_trait::async_trait;
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use uuid::Uuid;

pub type LctId = Uuid;

/// Who is invoking a tool (resolved by core before dispatch).
#[derive(Clone, Debug)]
pub struct Caller {
    pub lct: LctId,
    pub role: String, // "sovereign" | "citizen" | "external" | a specific role
}

/// How core bounds a plugin's result for the caller's tier.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ToolScope {
    /// Bounded by the tier cap (record lists).
    Bounded,
    /// Not bounded (summaries, a single attestation/tree).
    Unbounded,
}

#[derive(Debug)]
pub enum PluginError {
    Denied(String),
    BadRequest(String),
    Unavailable(String),
    Internal(String),
}

impl std::fmt::Display for PluginError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            PluginError::Denied(m) => write!(f, "denied: {m}"),
            PluginError::BadRequest(m) => write!(f, "bad request: {m}"),
            PluginError::Unavailable(m) => write!(f, "unavailable: {m}"),
            PluginError::Internal(m) => write!(f, "internal: {m}"),
        }
    }
}
impl std::error::Error for PluginError {}

/// Capabilities core **lends** a plugin. Deliberately generic — a plugin builds
/// whatever it needs from these; the seam never names a specific mechanism.
#[async_trait]
pub trait PluginCtx: Send + Sync {
    fn caller(&self) -> &Caller;
    /// The local signing identity's LCT id. Scale-agnostic: the **society** LCT
    /// when this seam runs in a hub, the **owner** LCT when it runs in a
    /// person-scale node (e.g. a Hestia mini-hub). The same seam, fractally.
    fn signer_lct(&self) -> LctId;
    /// Sign `bytes` as the signer LCT (Ed25519, 64-byte sig). Works whether the
    /// node holds the key (Local) or signs via a remote callback (Hestia).
    fn sign(&self, bytes: &[u8]) -> Result<Vec<u8>, PluginError>;
    /// Verify side of `sign` — the signer's public key, hex.
    fn signer_pubkey_hex(&self) -> String;
    /// Read-only projected node state (members/roles/devices/…) as opaque JSON.
    fn state(&self) -> &Value;
    /// Send an opaque **sealed** payload to a peer LCT over the paired channel
    /// and get the sealed response. Generic — enables fan-out/recursion and
    /// cross-hub calls without the seam knowing the payload.
    async fn send_to_peer(&self, peer: LctId, payload: &[u8]) -> Result<Vec<u8>, PluginError>;
}

/// A registered tool. Core has already authenticated the caller and gated the
/// call by the time `handle` runs.
#[async_trait]
pub trait ToolPlugin: Send + Sync {
    fn name(&self) -> &str;
    /// Policy-action key for the chapter-law gate. Default `read:<name>`.
    fn policy_action(&self) -> String {
        format!("read:{}", self.name())
    }
    fn scope(&self) -> ToolScope {
        ToolScope::Bounded
    }
    async fn handle(&self, ctx: &dyn PluginCtx, args: &Value) -> Result<Value, PluginError>;
}

/// Chapter-law gate (core supplies this — e.g. wrapping the PolicyEntity).
pub trait PolicyGate: Send + Sync {
    fn allow(&self, role: &str, action: &str) -> bool;
}

/// Tier result-bounding (core supplies this — e.g. wrapping `ReadScope`).
pub trait Scoper: Send + Sync {
    fn bound(&self, role: &str, result: Value) -> Value;
}

/// The registry + the canonical dispatch path. Plugins never see an un-gated
/// call: **gate → handle → scope**, the same contract as the hub's
/// `dispatch_channel`.
#[derive(Default)]
pub struct PluginRegistry {
    tools: HashMap<String, Arc<dyn ToolPlugin>>,
}

impl PluginRegistry {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn register(&mut self, plugin: Arc<dyn ToolPlugin>) {
        self.tools.insert(plugin.name().to_string(), plugin);
    }

    pub fn names(&self) -> Vec<String> {
        let mut v: Vec<String> = self.tools.keys().cloned().collect();
        v.sort();
        v
    }

    pub async fn dispatch(
        &self,
        ctx: &dyn PluginCtx,
        tool: &str,
        args: &Value,
        gate: &dyn PolicyGate,
        scoper: &dyn Scoper,
    ) -> Result<Value, PluginError> {
        let plugin = self
            .tools
            .get(tool)
            .ok_or_else(|| PluginError::BadRequest(format!("unknown tool: {tool}")))?;
        let role = ctx.caller().role.clone();
        let action = plugin.policy_action();
        if !gate.allow(&role, &action) {
            return Err(PluginError::Denied(format!("{action} denied for role {role}")));
        }
        let result = plugin.handle(ctx, args).await?;
        Ok(match plugin.scope() {
            ToolScope::Bounded => scoper.bound(&role, result),
            ToolScope::Unbounded => result,
        })
    }
}

#[cfg(test)]
mod tests;
