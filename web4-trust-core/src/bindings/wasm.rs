//! WASM bindings via wasm-bindgen
//!
//! Exposes the Rust trust primitives to JavaScript/TypeScript for browser use.
//! T3: Talent/Training/Temperament, V3: Valuation/Veracity/Validity

use wasm_bindgen::prelude::*;
use js_sys::{Array, Object, Reflect};

use crate::tensor::{T3Tensor as RustT3, V3Tensor as RustV3};
use crate::entity::EntityTrust as RustEntityTrust;
use crate::storage::{TrustStore, InMemoryStore};

use std::sync::Arc;
use std::cell::RefCell;

/// WASM-exposed T3 Trust Tensor (Talent/Training/Temperament)
#[wasm_bindgen]
pub struct T3Tensor {
    inner: RustT3,
}

#[wasm_bindgen]
impl T3Tensor {
    /// Create a new T3 tensor with specified values
    #[wasm_bindgen(constructor)]
    pub fn new(talent: f64, training: f64, temperament: f64) -> Self {
        Self {
            inner: RustT3::new(talent, training, temperament),
        }
    }

    /// Create a neutral tensor (all 0.5)
    pub fn neutral() -> Self {
        Self { inner: RustT3::neutral() }
    }

    // Getters
    #[wasm_bindgen(getter)]
    pub fn talent(&self) -> f64 { self.inner.talent }

    #[wasm_bindgen(getter)]
    pub fn training(&self) -> f64 { self.inner.training }

    #[wasm_bindgen(getter)]
    pub fn temperament(&self) -> f64 { self.inner.temperament }

    // Setters
    #[wasm_bindgen(setter)]
    pub fn set_talent(&mut self, value: f64) { self.inner.talent = value.clamp(0.0, 1.0); }

    #[wasm_bindgen(setter)]
    pub fn set_training(&mut self, value: f64) { self.inner.training = value.clamp(0.0, 1.0); }

    #[wasm_bindgen(setter)]
    pub fn set_temperament(&mut self, value: f64) { self.inner.temperament = value.clamp(0.0, 1.0); }

    /// Calculate average trust score
    pub fn average(&self) -> f64 {
        self.inner.average()
    }

    /// Get trust level as string
    pub fn level(&self) -> String {
        self.inner.level().to_string()
    }

    /// Update from action outcome
    #[wasm_bindgen(js_name = updateFromOutcome)]
    pub fn update_from_outcome(&mut self, success: bool, magnitude: f64) {
        self.inner.update_from_outcome(success, magnitude);
    }

    /// Apply temporal decay
    #[wasm_bindgen(js_name = applyDecay)]
    pub fn apply_decay(&mut self, days_inactive: f64, decay_rate: f64) -> bool {
        self.inner.apply_decay(days_inactive, decay_rate)
    }

    /// Convert to JSON object
    #[wasm_bindgen(js_name = toJSON)]
    pub fn to_json(&self) -> JsValue {
        let obj = Object::new();
        let _ = Reflect::set(&obj, &"talent".into(), &self.inner.talent.into());
        let _ = Reflect::set(&obj, &"training".into(), &self.inner.training.into());
        let _ = Reflect::set(&obj, &"temperament".into(), &self.inner.temperament.into());
        obj.into()
    }
}

/// WASM-exposed V3 Value Tensor (Valuation/Veracity/Validity)
#[wasm_bindgen]
pub struct V3Tensor {
    inner: RustV3,
}

#[wasm_bindgen]
impl V3Tensor {
    #[wasm_bindgen(constructor)]
    pub fn new(valuation: f64, veracity: f64, validity: f64) -> Self {
        Self {
            inner: RustV3::new(valuation, veracity, validity),
        }
    }

    pub fn neutral() -> Self {
        Self { inner: RustV3::neutral() }
    }

    #[wasm_bindgen(getter)]
    pub fn valuation(&self) -> f64 { self.inner.valuation }

    #[wasm_bindgen(getter)]
    pub fn veracity(&self) -> f64 { self.inner.veracity }

    #[wasm_bindgen(getter)]
    pub fn validity(&self) -> f64 { self.inner.validity }

    pub fn average(&self) -> f64 {
        self.inner.average()
    }

    #[wasm_bindgen(js_name = toJSON)]
    pub fn to_json(&self) -> JsValue {
        let obj = Object::new();
        let _ = Reflect::set(&obj, &"valuation".into(), &self.inner.valuation.into());
        let _ = Reflect::set(&obj, &"veracity".into(), &self.inner.veracity.into());
        let _ = Reflect::set(&obj, &"validity".into(), &self.inner.validity.into());
        obj.into()
    }
}

/// WASM-exposed EntityTrust
#[wasm_bindgen]
pub struct EntityTrust {
    inner: RustEntityTrust,
}

#[wasm_bindgen]
impl EntityTrust {
    #[wasm_bindgen(constructor)]
    pub fn new(entity_id: &str) -> Self {
        Self {
            inner: RustEntityTrust::new(entity_id),
        }
    }

    #[wasm_bindgen(getter, js_name = entityId)]
    pub fn entity_id(&self) -> String {
        self.inner.entity_id.clone()
    }

    #[wasm_bindgen(getter, js_name = entityType)]
    pub fn entity_type(&self) -> String {
        self.inner.entity_type.clone()
    }

    #[wasm_bindgen(getter, js_name = entityName)]
    pub fn entity_name(&self) -> String {
        self.inner.entity_name.clone()
    }

    #[wasm_bindgen(getter, js_name = actionCount)]
    pub fn action_count(&self) -> u64 {
        self.inner.action_count
    }

    #[wasm_bindgen(getter, js_name = successCount)]
    pub fn success_count(&self) -> u64 {
        self.inner.success_count
    }

    #[wasm_bindgen(getter, js_name = witnessCount)]
    pub fn witness_count(&self) -> u64 {
        self.inner.witness_count
    }

    #[wasm_bindgen(getter, js_name = witnessedBy)]
    pub fn witnessed_by(&self) -> Array {
        self.inner.witnessed_by.iter().map(|s| JsValue::from_str(s)).collect()
    }

    #[wasm_bindgen(getter, js_name = hasWitnessed)]
    pub fn has_witnessed(&self) -> Array {
        self.inner.has_witnessed.iter().map(|s| JsValue::from_str(s)).collect()
    }

    // T3 accessors (canonical 3D)
    #[wasm_bindgen(getter)]
    pub fn talent(&self) -> f64 { self.inner.t3.talent }

    #[wasm_bindgen(getter)]
    pub fn training(&self) -> f64 { self.inner.t3.training }

    #[wasm_bindgen(getter)]
    pub fn temperament(&self) -> f64 { self.inner.t3.temperament }

    // V3 accessors (canonical 3D)
    #[wasm_bindgen(getter)]
    pub fn valuation(&self) -> f64 { self.inner.v3.valuation }

    #[wasm_bindgen(getter)]
    pub fn veracity(&self) -> f64 { self.inner.v3.veracity }

    #[wasm_bindgen(getter)]
    pub fn validity(&self) -> f64 { self.inner.v3.validity }

    /// Get T3 average
    #[wasm_bindgen(js_name = t3Average)]
    pub fn t3_average(&self) -> f64 {
        self.inner.t3_average()
    }

    /// Get V3 average
    #[wasm_bindgen(js_name = v3Average)]
    pub fn v3_average(&self) -> f64 {
        self.inner.v3_average()
    }

    /// Get trust level
    #[wasm_bindgen(js_name = trustLevel)]
    pub fn trust_level(&self) -> String {
        self.inner.trust_level().to_string()
    }

    /// Update from action outcome
    #[wasm_bindgen(js_name = updateFromOutcome)]
    pub fn update_from_outcome(&mut self, success: bool, magnitude: f64) {
        self.inner.update_from_outcome(success, magnitude);
    }

    /// Receive witness event
    #[wasm_bindgen(js_name = receiveWitness)]
    pub fn receive_witness(&mut self, witness_id: &str, success: bool, magnitude: f64) {
        self.inner.receive_witness(witness_id, success, magnitude);
    }

    /// Give witness event
    #[wasm_bindgen(js_name = giveWitness)]
    pub fn give_witness(&mut self, target_id: &str, success: bool, magnitude: f64) {
        self.inner.give_witness(target_id, success, magnitude);
    }

    /// Days since last action
    #[wasm_bindgen(js_name = daysSinceLastAction)]
    pub fn days_since_last_action(&self) -> f64 {
        self.inner.days_since_last_action()
    }

    /// Apply decay
    #[wasm_bindgen(js_name = applyDecay)]
    pub fn apply_decay(&mut self, days_inactive: f64, decay_rate: f64) -> bool {
        self.inner.apply_decay(days_inactive, decay_rate)
    }

    /// Success rate
    #[wasm_bindgen(js_name = successRate)]
    pub fn success_rate(&self) -> f64 {
        self.inner.success_rate()
    }

    /// Convert to JSON object
    #[wasm_bindgen(js_name = toJSON)]
    pub fn to_json(&self) -> JsValue {
        let obj = Object::new();

        let _ = Reflect::set(&obj, &"entity_id".into(), &self.inner.entity_id.clone().into());
        let _ = Reflect::set(&obj, &"entity_type".into(), &self.inner.entity_type.clone().into());
        let _ = Reflect::set(&obj, &"entity_name".into(), &self.inner.entity_name.clone().into());

        // T3 (canonical 3D)
        let _ = Reflect::set(&obj, &"talent".into(), &self.inner.t3.talent.into());
        let _ = Reflect::set(&obj, &"training".into(), &self.inner.t3.training.into());
        let _ = Reflect::set(&obj, &"temperament".into(), &self.inner.t3.temperament.into());

        // V3 (canonical 3D)
        let _ = Reflect::set(&obj, &"valuation".into(), &self.inner.v3.valuation.into());
        let _ = Reflect::set(&obj, &"veracity".into(), &self.inner.v3.veracity.into());
        let _ = Reflect::set(&obj, &"validity".into(), &self.inner.v3.validity.into());

        // Metadata
        let _ = Reflect::set(&obj, &"action_count".into(), &(self.inner.action_count as f64).into());
        let _ = Reflect::set(&obj, &"success_count".into(), &(self.inner.success_count as f64).into());
        let _ = Reflect::set(&obj, &"witness_count".into(), &(self.inner.witness_count as f64).into());

        // Witness arrays
        let _ = Reflect::set(&obj, &"witnessed_by".into(), &self.witnessed_by().into());
        let _ = Reflect::set(&obj, &"has_witnessed".into(), &self.has_witnessed().into());

        obj.into()
    }
}

/// WASM-exposed TrustStore (in-memory only for WASM)
#[wasm_bindgen]
pub struct WasmTrustStore {
    inner: RefCell<InMemoryStore>,
}

#[wasm_bindgen]
impl WasmTrustStore {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        Self {
            inner: RefCell::new(InMemoryStore::new()),
        }
    }

    /// Get entity trust
    pub fn get(&self, entity_id: &str) -> Result<EntityTrust, JsValue> {
        let store = self.inner.borrow();
        store.get(entity_id)
            .map(|t| EntityTrust { inner: t })
            .map_err(|e| JsValue::from_str(&e.to_string()))
    }

    /// Save entity trust
    pub fn save(&self, trust: &EntityTrust) -> Result<(), JsValue> {
        let store = self.inner.borrow();
        store.save(&trust.inner)
            .map_err(|e| JsValue::from_str(&e.to_string()))
    }

    /// Update entity from outcome
    pub fn update(&self, entity_id: &str, success: bool, magnitude: f64) -> Result<EntityTrust, JsValue> {
        let store = self.inner.borrow();
        store.update(entity_id, success, magnitude)
            .map(|t| EntityTrust { inner: t })
            .map_err(|e| JsValue::from_str(&e.to_string()))
    }

    /// Witness event
    pub fn witness(
        &self,
        witness_id: &str,
        target_id: &str,
        success: bool,
        magnitude: f64,
    ) -> Result<Array, JsValue> {
        let store = self.inner.borrow();
        let (witness, target) = store.witness(witness_id, target_id, success, magnitude)
            .map_err(|e| JsValue::from_str(&e.to_string()))?;

        let result = Array::new();
        result.push(&JsValue::from(EntityTrust { inner: witness }));
        result.push(&JsValue::from(EntityTrust { inner: target }));
        Ok(result)
    }

    /// List entities
    #[wasm_bindgen(js_name = listEntities)]
    pub fn list_entities(&self) -> Result<Array, JsValue> {
        let store = self.inner.borrow();
        let ids = store.list(None)
            .map_err(|e| JsValue::from_str(&e.to_string()))?;

        Ok(ids.into_iter().map(|s| JsValue::from_str(&s)).collect())
    }

    /// Check if entity exists
    pub fn exists(&self, entity_id: &str) -> Result<bool, JsValue> {
        let store = self.inner.borrow();
        store.exists(entity_id)
            .map_err(|e| JsValue::from_str(&e.to_string()))
    }

    /// Delete entity
    pub fn delete(&self, entity_id: &str) -> Result<bool, JsValue> {
        let store = self.inner.borrow();
        store.delete(entity_id)
            .map_err(|e| JsValue::from_str(&e.to_string()))
    }

    /// Get entity count
    pub fn count(&self) -> usize {
        self.inner.borrow().len()
    }
}

impl Default for WasmTrustStore {
    fn default() -> Self {
        Self::new()
    }
}

/// Initialize the WASM module (called automatically)
#[wasm_bindgen(start)]
pub fn init() {
    // Set panic hook for better error messages
    #[cfg(feature = "console_error_panic_hook")]
    console_error_panic_hook::set_once();
}

/// Get version string
#[wasm_bindgen]
pub fn version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}
