//! The generic seam: gate → handle → scope, with a sample plugin.

use super::*;
use serde_json::json;

struct MockCtx {
    caller: Caller,
    state: Value,
}

#[async_trait]
impl PluginCtx for MockCtx {
    fn caller(&self) -> &Caller {
        &self.caller
    }
    fn hub_lct(&self) -> LctId {
        Uuid::nil()
    }
    fn sign(&self, _bytes: &[u8]) -> Result<Vec<u8>, PluginError> {
        Ok(vec![0u8; 64])
    }
    fn hub_pubkey_hex(&self) -> String {
        "00".repeat(32)
    }
    fn state(&self) -> &Value {
        &self.state
    }
    async fn send_to_peer(&self, _peer: LctId, _payload: &[u8]) -> Result<Vec<u8>, PluginError> {
        Err(PluginError::Unavailable("no peer in test".into()))
    }
}

/// A trivial bounded plugin that returns a list out of `ctx.state`.
struct ListPlugin;
#[async_trait]
impl ToolPlugin for ListPlugin {
    fn name(&self) -> &str {
        "list_things"
    }
    async fn handle(&self, ctx: &dyn PluginCtx, _args: &Value) -> Result<Value, PluginError> {
        Ok(json!({ "items": ctx.state()["items"].clone() }))
    }
}

struct AllowAll;
impl PolicyGate for AllowAll {
    fn allow(&self, _r: &str, _a: &str) -> bool {
        true
    }
}
struct DenyCitizen;
impl PolicyGate for DenyCitizen {
    fn allow(&self, role: &str, _a: &str) -> bool {
        role != "citizen"
    }
}
/// Bounds non-sovereign callers to 2 items.
struct CapTwo;
impl Scoper for CapTwo {
    fn bound(&self, role: &str, mut result: Value) -> Value {
        if role == "sovereign" {
            return result;
        }
        if let Some(items) = result.get_mut("items").and_then(|v| v.as_array_mut()) {
            items.truncate(2);
        }
        result
    }
}

fn registry() -> PluginRegistry {
    let mut r = PluginRegistry::new();
    r.register(Arc::new(ListPlugin));
    r
}
fn ctx(role: &str) -> MockCtx {
    MockCtx {
        caller: Caller { lct: Uuid::new_v4(), role: role.into() },
        state: json!({ "items": [1, 2, 3, 4] }),
    }
}

#[tokio::test]
async fn dispatch_gates_then_scopes_by_tier() {
    let r = registry();
    // citizen → bounded to 2
    let out = r.dispatch(&ctx("citizen"), "list_things", &json!({}), &AllowAll, &CapTwo).await.unwrap();
    assert_eq!(out["items"].as_array().unwrap().len(), 2);
    // sovereign → unbounded
    let out = r.dispatch(&ctx("sovereign"), "list_things", &json!({}), &AllowAll, &CapTwo).await.unwrap();
    assert_eq!(out["items"].as_array().unwrap().len(), 4);
}

#[tokio::test]
async fn gate_denies_before_the_handler_runs() {
    let r = registry();
    let err = r
        .dispatch(&ctx("citizen"), "list_things", &json!({}), &DenyCitizen, &CapTwo)
        .await
        .unwrap_err();
    assert!(matches!(err, PluginError::Denied(_)));
}

#[tokio::test]
async fn unknown_tool_is_a_bad_request() {
    let r = registry();
    let err = r.dispatch(&ctx("citizen"), "nope", &json!({}), &AllowAll, &CapTwo).await.unwrap_err();
    assert!(matches!(err, PluginError::BadRequest(_)));
}
