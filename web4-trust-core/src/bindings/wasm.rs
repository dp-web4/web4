//! WASM bindings via wasm-bindgen
//!
//! Exposes the Rust trust primitives to JavaScript/TypeScript for browser use.
//! T3: Talent/Training/Temperament, V3: Valuation/Veracity/Validity

use wasm_bindgen::prelude::*;
use js_sys::{Array, Object, Reflect};

use crate::tensor::{T3Tensor as RustT3, V3Tensor as RustV3};
use crate::entity::EntityTrust as RustEntityTrust;
use crate::storage::{TrustStore, InMemoryStore};

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

// ── Web4-Core WASM Bindings ────────────────────────────────────────────

use web4_core::role::SocietyRole as RustSocietyRole;
use web4_core::role::RoleAssignment as RustRoleAssignment;
use web4_core::society::Society as RustSociety;
use web4_core::atp::ATPAccount as RustATPAccount;
use web4_core::r6::{
    R7Action as RustR7Action,
    Rules as RustRules,
    ActionRole as RustActionRole,
    Request as RustRequest,
    Reference as RustReference,
    ResourceRequirements as RustResourceRequirements,
};

/// WASM-exposed SocietyRole enum.
///
/// Represents one of the 7 base-mandatory roles, 2 context-mandatory roles,
/// or a custom role. Use the static methods to enumerate roles.
#[wasm_bindgen]
pub struct WasmSocietyRole {
    inner: RustSocietyRole,
}

#[wasm_bindgen]
impl WasmSocietyRole {
    /// Create a role by name. Valid names: sovereign, law_oracle, policy_entity,
    /// treasurer, administrator, archivist, citizen, witness, auditor,
    /// or "custom:<name>" for custom roles.
    #[wasm_bindgen(constructor)]
    pub fn new(name: &str) -> Result<WasmSocietyRole, JsValue> {
        let role = match name {
            "sovereign" => RustSocietyRole::Sovereign,
            "law_oracle" => RustSocietyRole::LawOracle,
            "policy_entity" => RustSocietyRole::PolicyEntity,
            "treasurer" => RustSocietyRole::Treasurer,
            "administrator" => RustSocietyRole::Administrator,
            "archivist" => RustSocietyRole::Archivist,
            "citizen" => RustSocietyRole::Citizen,
            "witness" => RustSocietyRole::Witness,
            "auditor" => RustSocietyRole::Auditor,
            other if other.starts_with("custom:") => {
                RustSocietyRole::Custom(other[7..].to_string())
            }
            _ => return Err(JsValue::from_str(&format!("Unknown role: {}", name))),
        };
        Ok(Self { inner: role })
    }

    /// Returns the 7 base-mandatory roles as a JS array of WasmSocietyRole.
    #[wasm_bindgen(js_name = baseMandatory)]
    pub fn base_mandatory() -> Array {
        RustSocietyRole::base_mandatory()
            .into_iter()
            .map(|r| JsValue::from(WasmSocietyRole { inner: r }))
            .collect()
    }

    /// Whether this is a base-mandatory role.
    #[wasm_bindgen(js_name = isBaseMandatory)]
    pub fn is_base_mandatory(&self) -> bool {
        self.inner.is_base_mandatory()
    }

    /// Human-readable description of this role's responsibility.
    pub fn description(&self) -> String {
        self.inner.description().to_string()
    }

    /// Role name as string.
    pub fn name(&self) -> String {
        match &self.inner {
            RustSocietyRole::Sovereign => "sovereign".into(),
            RustSocietyRole::LawOracle => "law_oracle".into(),
            RustSocietyRole::PolicyEntity => "policy_entity".into(),
            RustSocietyRole::Treasurer => "treasurer".into(),
            RustSocietyRole::Administrator => "administrator".into(),
            RustSocietyRole::Archivist => "archivist".into(),
            RustSocietyRole::Citizen => "citizen".into(),
            RustSocietyRole::Witness => "witness".into(),
            RustSocietyRole::Auditor => "auditor".into(),
            RustSocietyRole::Custom(name) => format!("custom:{}", name),
        }
    }
}

/// WASM-exposed RoleAssignment — binds a role to its LCT and tracks filling entity.
#[wasm_bindgen]
pub struct WasmRoleAssignment {
    inner: RustRoleAssignment,
}

#[wasm_bindgen]
impl WasmRoleAssignment {
    /// Create a new role assignment.
    ///
    /// Arguments are UUID strings (will be parsed).
    #[wasm_bindgen(constructor)]
    pub fn new(
        role_name: &str,
        role_lct_id: &str,
        filling_entity_lct_id: &str,
        assigned_by: &str,
    ) -> Result<WasmRoleAssignment, JsValue> {
        let role_wrapper = WasmSocietyRole::new(role_name)?;
        let role_lct = parse_uuid(role_lct_id)?;
        let filling = parse_uuid(filling_entity_lct_id)?;
        let by = parse_uuid(assigned_by)?;
        Ok(Self {
            inner: RustRoleAssignment::new(role_wrapper.inner, role_lct, filling, by),
        })
    }

    /// Rotate the filling entity. The role-LCT stays the same.
    pub fn rotate(&mut self, new_entity_lct_id: &str, rotated_by: &str) -> Result<(), JsValue> {
        let new_entity = parse_uuid(new_entity_lct_id)?;
        let by = parse_uuid(rotated_by)?;
        self.inner.rotate(new_entity, by);
        Ok(())
    }

    /// Check if an entity is authorized to act in this role.
    #[wasm_bindgen(js_name = isAuthorized)]
    pub fn is_authorized(&self, entity_lct_id: &str) -> Result<bool, JsValue> {
        let entity = parse_uuid(entity_lct_id)?;
        Ok(self.inner.is_authorized(entity))
    }

    /// Add an additional holder (committee/federation pattern).
    #[wasm_bindgen(js_name = addHolder)]
    pub fn add_holder(&mut self, entity_lct_id: &str) -> Result<(), JsValue> {
        let entity = parse_uuid(entity_lct_id)?;
        self.inner.add_holder(entity);
        Ok(())
    }

    /// The role's LCT ID.
    #[wasm_bindgen(getter, js_name = roleLctId)]
    pub fn role_lct_id(&self) -> String {
        self.inner.role_lct_id.to_string()
    }

    /// The filling entity's LCT ID.
    #[wasm_bindgen(getter, js_name = fillingEntityLctId)]
    pub fn filling_entity_lct_id(&self) -> String {
        self.inner.filling_entity_lct_id.to_string()
    }

    /// Whether this role supports multiple holders.
    #[wasm_bindgen(getter, js_name = multiHolder)]
    pub fn multi_holder(&self) -> bool {
        self.inner.multi_holder
    }
}

/// WASM-exposed Society — self-sovereign organizational unit.
#[wasm_bindgen]
pub struct WasmSociety {
    inner: RustSociety,
}

#[wasm_bindgen]
impl WasmSociety {
    /// Bootstrap a new society. Returns the society with all 7 base-mandatory
    /// roles assigned to the founder.
    pub fn bootstrap(
        name: &str,
        charter_hash: &str,
        founder_lct_id: &str,
    ) -> Result<WasmSociety, JsValue> {
        let founder = parse_uuid(founder_lct_id)?;
        let (society, _role_lcts) =
            RustSociety::bootstrap(name.to_string(), charter_hash.to_string(), founder);
        Ok(Self { inner: society })
    }

    /// Add a citizen to the society.
    #[wasm_bindgen(js_name = addCitizen)]
    pub fn add_citizen(&mut self, entity_lct_id: &str) -> Result<(), JsValue> {
        let entity = parse_uuid(entity_lct_id)?;
        self.inner.add_citizen(entity);
        Ok(())
    }

    /// Assign a role to an entity. Only Sovereign or Administrator can assign.
    /// Returns the role's LCT ID.
    #[wasm_bindgen(js_name = assignRole)]
    pub fn assign_role(
        &mut self,
        role_name: &str,
        entity_lct_id: &str,
        assigned_by: &str,
    ) -> Result<String, JsValue> {
        let role_wrapper = WasmSocietyRole::new(role_name)?;
        let entity = parse_uuid(entity_lct_id)?;
        let by = parse_uuid(assigned_by)?;
        self.inner
            .assign_role(role_wrapper.inner, entity, by)
            .map(|id| id.to_string())
            .map_err(|e| JsValue::from_str(&e.to_string()))
    }

    /// Check if an entity holds a specific role.
    #[wasm_bindgen(js_name = hasRole)]
    pub fn has_role(&self, entity_lct_id: &str, role_name: &str) -> Result<bool, JsValue> {
        let role_wrapper = WasmSocietyRole::new(role_name)?;
        let entity = parse_uuid(entity_lct_id)?;
        Ok(self.inner.has_role_authority(entity, &role_wrapper.inner))
    }

    /// Validate minimum viable society requirements.
    /// Returns null on success, or a JSON array of error strings on failure.
    #[wasm_bindgen(js_name = validateMinimumViable)]
    pub fn validate_minimum_viable(&self) -> JsValue {
        match self.inner.validate_minimum_viable() {
            Ok(()) => JsValue::NULL,
            Err(errors) => {
                let arr: Array = errors.into_iter().map(|e| JsValue::from_str(&e)).collect();
                arr.into()
            }
        }
    }

    /// Transition to Operational state (all mandatory roles must be filled).
    #[wasm_bindgen(js_name = goOperational)]
    pub fn go_operational(&mut self) -> Result<(), JsValue> {
        self.inner.begin_bootstrap().map_err(|e| JsValue::from_str(&e.to_string()))?;
        self.inner.go_operational().map_err(|e| JsValue::from_str(&e.to_string()))
    }

    /// Get a JSON summary of the society state.
    pub fn summary(&self) -> JsValue {
        let obj = Object::new();
        let _ = Reflect::set(&obj, &"lctId".into(), &self.inner.lct_id.to_string().into());
        let _ = Reflect::set(&obj, &"name".into(), &self.inner.name.clone().into());
        let _ = Reflect::set(&obj, &"charterHash".into(), &self.inner.charter_hash.clone().into());
        let _ = Reflect::set(
            &obj,
            &"state".into(),
            &format!("{:?}", self.inner.state).into(),
        );
        let _ = Reflect::set(
            &obj,
            &"founderLctId".into(),
            &self.inner.founder_lct_id.to_string().into(),
        );
        let _ = Reflect::set(
            &obj,
            &"citizenCount".into(),
            &(self.inner.citizens.len() as f64).into(),
        );
        let _ = Reflect::set(
            &obj,
            &"roleCount".into(),
            &(self.inner.roles.len() as f64).into(),
        );
        let _ = Reflect::set(
            &obj,
            &"isFederation".into(),
            &self.inner.is_federation().into(),
        );
        let _ = Reflect::set(
            &obj,
            &"isConstituent".into(),
            &self.inner.is_constituent().into(),
        );
        obj.into()
    }

    /// Society's LCT ID.
    #[wasm_bindgen(getter, js_name = lctId)]
    pub fn lct_id(&self) -> String {
        self.inner.lct_id.to_string()
    }

    /// Society name.
    #[wasm_bindgen(getter)]
    pub fn name(&self) -> String {
        self.inner.name.clone()
    }

    /// Current metabolic state as string.
    #[wasm_bindgen(getter)]
    pub fn state(&self) -> String {
        format!("{:?}", self.inner.state)
    }
}

/// WASM-exposed ATPAccount — bio-inspired energy metabolism.
#[wasm_bindgen]
pub struct WasmATPAccount {
    inner: RustATPAccount,
}

#[wasm_bindgen]
impl WasmATPAccount {
    /// Create a new ATP account with the given initial balance.
    #[wasm_bindgen(constructor)]
    pub fn new(initial: f64) -> Self {
        Self {
            inner: RustATPAccount::new(initial),
        }
    }

    /// Lock tokens from available to escrow.
    pub fn lock(&mut self, amount: f64) -> Result<(), JsValue> {
        self.inner
            .lock(amount)
            .map_err(|e| JsValue::from_str(&e.to_string()))
    }

    /// Commit locked tokens to ADP (discharge on success).
    pub fn commit(&mut self, amount: f64) -> Result<f64, JsValue> {
        self.inner
            .commit(amount)
            .map_err(|e| JsValue::from_str(&e.to_string()))
    }

    /// Rollback locked tokens back to available (on failure/cancel).
    pub fn rollback(&mut self, amount: f64) -> Result<f64, JsValue> {
        self.inner
            .rollback(amount)
            .map_err(|e| JsValue::from_str(&e.to_string()))
    }

    /// Recharge ATP up to max_multiplier * initial_balance.
    /// Returns actual amount recharged.
    pub fn recharge(&mut self, rate: f64, max_multiplier: f64) -> f64 {
        self.inner.recharge(rate, max_multiplier)
    }

    /// Total active ATP (available + locked).
    pub fn total(&self) -> f64 {
        self.inner.total()
    }

    /// Energy ratio: ATP / (ATP + ADP). High = earning, low = spending.
    #[wasm_bindgen(js_name = energyRatio)]
    pub fn energy_ratio(&self) -> f64 {
        self.inner.energy_ratio()
    }

    /// Available ATP.
    #[wasm_bindgen(getter)]
    pub fn available(&self) -> f64 {
        self.inner.available
    }

    /// Locked (escrowed) ATP.
    #[wasm_bindgen(getter)]
    pub fn locked(&self) -> f64 {
        self.inner.locked
    }

    /// Discharged tokens (ADP).
    #[wasm_bindgen(getter)]
    pub fn adp(&self) -> f64 {
        self.inner.adp
    }

    /// Initial balance.
    #[wasm_bindgen(getter, js_name = initialBalance)]
    pub fn initial_balance(&self) -> f64 {
        self.inner.initial_balance
    }

    /// Convert to JSON object.
    #[wasm_bindgen(js_name = toJSON)]
    pub fn to_json(&self) -> JsValue {
        let obj = Object::new();
        let _ = Reflect::set(&obj, &"available".into(), &self.inner.available.into());
        let _ = Reflect::set(&obj, &"locked".into(), &self.inner.locked.into());
        let _ = Reflect::set(&obj, &"adp".into(), &self.inner.adp.into());
        let _ = Reflect::set(&obj, &"initialBalance".into(), &self.inner.initial_balance.into());
        let _ = Reflect::set(&obj, &"total".into(), &self.inner.total().into());
        let _ = Reflect::set(&obj, &"energyRatio".into(), &self.inner.energy_ratio().into());
        obj.into()
    }
}

/// WASM-exposed R7Action — the complete R6/R7 action framework.
///
/// R7 actions are constructed from a JSON string containing rules, role,
/// request, reference, and resource fields. This keeps the TypeScript API
/// clean while preserving the full Rust type structure.
#[wasm_bindgen]
pub struct WasmR7Action {
    inner: RustR7Action,
}

#[wasm_bindgen]
impl WasmR7Action {
    /// Create a new R7 action from a JSON configuration string.
    ///
    /// Expected JSON shape:
    /// ```json
    /// {
    ///   "rules": { "law_hash": "sha256:...", "society": "lct:...",
    ///              "constraints": [], "permissions": ["*"], "prohibitions": [] },
    ///   "role": { "actor_lct": "lct:...", "role_lct": "lct:...", "paired_at": "..." },
    ///   "request": { "action": "file_write", "target": "...", "parameters": {},
    ///                "atp_stake": 10.0, "nonce": "...", "constraints": {} },
    ///   "reference": { "precedents": [], "mrh_depth": 3, "relevant_entities": [],
    ///                  "witnesses": [] },
    ///   "resource": { "required_atp": 5.0, "available_atp": 100.0, "compute": {},
    ///                 "escrow_amount": 5.0, "escrow_condition": "result_verified" }
    /// }
    /// ```
    #[wasm_bindgen(constructor)]
    pub fn new(config_json: &str) -> Result<WasmR7Action, JsValue> {
        #[derive(serde::Deserialize)]
        struct ActionConfig {
            rules: RustRules,
            role: RustActionRole,
            request: RustRequest,
            reference: RustReference,
            resource: RustResourceRequirements,
        }

        let config: ActionConfig = serde_json::from_str(config_json)
            .map_err(|e| JsValue::from_str(&format!("Invalid action JSON: {}", e)))?;

        Ok(Self {
            inner: RustR7Action::new(
                config.rules,
                config.role,
                config.request,
                config.reference,
                config.resource,
            ),
        })
    }

    /// Validate the action before execution.
    /// Returns a JS array of error strings (empty = valid).
    pub fn validate(&self) -> Array {
        self.inner
            .validate()
            .into_iter()
            .map(|e| JsValue::from_str(&e))
            .collect()
    }

    /// Compute reputation delta from a quality score (makes this an R7 action).
    ///
    /// quality: 0.0 to 1.0. Below 0.5 = negative, above 0.5 = positive.
    #[wasm_bindgen(js_name = computeReputation)]
    pub fn compute_reputation(
        &mut self,
        quality: f64,
        rule_triggered: &str,
        reason: &str,
    ) {
        self.inner.compute_reputation(quality, rule_triggered, reason, vec![]);
    }

    /// Compute the canonical hash for chain integrity.
    #[wasm_bindgen(js_name = canonicalHash)]
    pub fn canonical_hash(&self) -> String {
        self.inner.canonical_hash()
    }

    /// Whether this is an R7 action (has reputation tracking).
    #[wasm_bindgen(js_name = isR7)]
    pub fn is_r7(&self) -> bool {
        self.inner.is_r7()
    }

    /// The unique action ID.
    #[wasm_bindgen(getter, js_name = actionId)]
    pub fn action_id(&self) -> String {
        self.inner.action_id.clone()
    }

    /// Current action status as string.
    #[wasm_bindgen(getter)]
    pub fn status(&self) -> String {
        format!("{:?}", self.inner.result.status)
    }

    /// Convert the full action to a JSON string.
    #[wasm_bindgen(js_name = toJSON)]
    pub fn to_json(&self) -> Result<String, JsValue> {
        serde_json::to_string(&self.inner)
            .map_err(|e| JsValue::from_str(&format!("Serialization error: {}", e)))
    }
}

/// Helper: parse a UUID string, returning a JsValue error on failure.
fn parse_uuid(s: &str) -> std::result::Result<uuid::Uuid, JsValue> {
    uuid::Uuid::parse_str(s).map_err(|e| JsValue::from_str(&format!("Invalid UUID '{}': {}", s, e)))
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
