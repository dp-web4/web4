//! Python bindings via PyO3
//!
//! Exposes the Rust trust primitives to Python for use in hooks.
//! T3: Talent/Training/Temperament, V3: Valuation/Veracity/Validity

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::PyModule;

// P3b: bindings now wrap the canonical `web4_core` tensors and share the trust
// semantics via `crate::tensor` free functions (no parallel math).
use crate::tensor;
use web4_core::t3::{TrustDimension, T3 as RustT3};
use web4_core::v3::{ValueDimension, V3 as RustV3};
use crate::entity::{EntityTrust as RustEntityTrust, EntityType};
use crate::storage::TrustStore;

#[cfg(feature = "file-store")]
use crate::storage::FileStore;

use std::sync::Arc;
use parking_lot::RwLock;

/// Python-exposed T3 Trust Tensor (Talent/Training/Temperament)
#[pyclass(name = "T3Tensor")]
#[derive(Clone)]
pub struct PyT3Tensor {
    inner: RustT3,
}

#[pymethods]
impl PyT3Tensor {
    #[new]
    #[pyo3(signature = (talent=0.5, training=0.5, temperament=0.5))]
    fn new(talent: f64, training: f64, temperament: f64) -> Self {
        Self {
            inner: RustT3::from_parts([talent, training, temperament], [0, 0, 0]),
        }
    }

    /// Create a neutral tensor (all 0.5)
    #[staticmethod]
    fn neutral() -> Self {
        Self { inner: RustT3::new() }
    }

    #[getter]
    fn talent(&self) -> f64 { self.inner.score(TrustDimension::Talent) }

    #[setter]
    fn set_talent(&mut self, value: f64) { tensor::t3_set_score(&mut self.inner, TrustDimension::Talent, value); }

    #[getter]
    fn training(&self) -> f64 { self.inner.score(TrustDimension::Training) }

    #[setter]
    fn set_training(&mut self, value: f64) { tensor::t3_set_score(&mut self.inner, TrustDimension::Training, value); }

    #[getter]
    fn temperament(&self) -> f64 { self.inner.score(TrustDimension::Temperament) }

    #[setter]
    fn set_temperament(&mut self, value: f64) { tensor::t3_set_score(&mut self.inner, TrustDimension::Temperament, value); }

    /// Calculate average trust score
    fn average(&self) -> f64 {
        tensor::t3_average(&self.inner)
    }

    /// Get trust level as string
    fn level(&self) -> String {
        tensor::t3_level(&self.inner).to_string()
    }

    /// Update from action outcome
    fn update_from_outcome(&mut self, success: bool, magnitude: f64) {
        tensor::t3_update_from_outcome(&mut self.inner, success, magnitude);
    }

    /// Apply temporal decay
    fn apply_decay(&mut self, days_inactive: f64, decay_rate: f64) -> bool {
        tensor::t3_apply_decay(&mut self.inner, days_inactive, decay_rate)
    }

    fn __repr__(&self) -> String {
        format!(
            "T3Tensor(talent={:.3}, training={:.3}, temperament={:.3})",
            self.inner.score(TrustDimension::Talent),
            self.inner.score(TrustDimension::Training),
            self.inner.score(TrustDimension::Temperament)
        )
    }
}

/// Python-exposed V3 Value Tensor (Valuation/Veracity/Validity)
#[pyclass(name = "V3Tensor")]
#[derive(Clone)]
pub struct PyV3Tensor {
    inner: RustV3,
}

#[pymethods]
impl PyV3Tensor {
    #[new]
    #[pyo3(signature = (valuation=0.5, veracity=0.5, validity=0.5))]
    fn new(valuation: f64, veracity: f64, validity: f64) -> Self {
        Self {
            inner: RustV3::from_parts([valuation, veracity, validity], [0, 0, 0]),
        }
    }

    #[staticmethod]
    fn neutral() -> Self {
        Self { inner: RustV3::new() }
    }

    #[getter]
    fn valuation(&self) -> f64 { self.inner.score(ValueDimension::Valuation) }

    #[setter]
    fn set_valuation(&mut self, value: f64) { tensor::v3_set_score(&mut self.inner, ValueDimension::Valuation, value); }

    #[getter]
    fn veracity(&self) -> f64 { self.inner.score(ValueDimension::Veracity) }

    #[setter]
    fn set_veracity(&mut self, value: f64) { tensor::v3_set_score(&mut self.inner, ValueDimension::Veracity, value); }

    #[getter]
    fn validity(&self) -> f64 { self.inner.score(ValueDimension::Validity) }

    #[setter]
    fn set_validity(&mut self, value: f64) { tensor::v3_set_score(&mut self.inner, ValueDimension::Validity, value); }

    fn average(&self) -> f64 {
        tensor::v3_average(&self.inner)
    }

    fn __repr__(&self) -> String {
        format!(
            "V3Tensor(valuation={:.3}, veracity={:.3}, validity={:.3})",
            self.inner.score(ValueDimension::Valuation),
            self.inner.score(ValueDimension::Veracity),
            self.inner.score(ValueDimension::Validity)
        )
    }
}

/// Python-exposed EntityTrust
#[pyclass(name = "EntityTrust")]
#[derive(Clone)]
pub struct PyEntityTrust {
    inner: RustEntityTrust,
}

#[pymethods]
impl PyEntityTrust {
    #[new]
    fn new(entity_id: &str) -> Self {
        Self {
            inner: RustEntityTrust::new(entity_id),
        }
    }

    #[getter]
    fn entity_id(&self) -> &str {
        &self.inner.entity_id
    }

    #[getter]
    fn entity_type(&self) -> &str {
        &self.inner.entity_type
    }

    #[getter]
    fn entity_name(&self) -> &str {
        &self.inner.entity_name
    }

    #[getter]
    fn action_count(&self) -> u64 {
        self.inner.action_count
    }

    #[getter]
    fn success_count(&self) -> u64 {
        self.inner.success_count
    }

    #[getter]
    fn witness_count(&self) -> u64 {
        self.inner.witness_count
    }

    #[getter]
    fn witnessed_by(&self) -> Vec<String> {
        self.inner.witnessed_by.clone()
    }

    #[getter]
    fn has_witnessed(&self) -> Vec<String> {
        self.inner.has_witnessed.clone()
    }

    // T3 accessors (canonical 3D)
    #[getter]
    fn talent(&self) -> f64 { self.inner.talent() }

    #[setter]
    fn set_talent(&mut self, value: f64) { tensor::t3_set_score(&mut self.inner.t3, TrustDimension::Talent, value); }

    #[getter]
    fn training(&self) -> f64 { self.inner.training() }

    #[setter]
    fn set_training(&mut self, value: f64) { tensor::t3_set_score(&mut self.inner.t3, TrustDimension::Training, value); }

    #[getter]
    fn temperament(&self) -> f64 { self.inner.temperament() }

    #[setter]
    fn set_temperament(&mut self, value: f64) { tensor::t3_set_score(&mut self.inner.t3, TrustDimension::Temperament, value); }

    // V3 accessors (canonical 3D)
    #[getter]
    fn valuation(&self) -> f64 { self.inner.valuation() }

    #[setter]
    fn set_valuation(&mut self, value: f64) { tensor::v3_set_score(&mut self.inner.v3, ValueDimension::Valuation, value); }

    #[getter]
    fn veracity(&self) -> f64 { self.inner.veracity() }

    #[setter]
    fn set_veracity(&mut self, value: f64) { tensor::v3_set_score(&mut self.inner.v3, ValueDimension::Veracity, value); }

    #[getter]
    fn validity(&self) -> f64 { self.inner.validity() }

    #[setter]
    fn set_validity(&mut self, value: f64) { tensor::v3_set_score(&mut self.inner.v3, ValueDimension::Validity, value); }

    /// Get T3 average
    fn t3_average(&self) -> f64 {
        self.inner.t3_average()
    }

    /// Get V3 average
    fn v3_average(&self) -> f64 {
        self.inner.v3_average()
    }

    /// Get trust level
    fn trust_level(&self) -> String {
        self.inner.trust_level().to_string()
    }

    /// Update from action outcome
    fn update_from_outcome(&mut self, success: bool, magnitude: f64) {
        self.inner.update_from_outcome(success, magnitude);
    }

    /// Receive witness event
    fn receive_witness(&mut self, witness_id: &str, success: bool, magnitude: f64) {
        self.inner.receive_witness(witness_id, success, magnitude);
    }

    /// Give witness event
    fn give_witness(&mut self, target_id: &str, success: bool, magnitude: f64) {
        self.inner.give_witness(target_id, success, magnitude);
    }

    /// Days since last action
    fn days_since_last_action(&self) -> f64 {
        self.inner.days_since_last_action()
    }

    /// Apply decay
    fn apply_decay(&mut self, days_inactive: f64, decay_rate: f64) -> bool {
        self.inner.apply_decay(days_inactive, decay_rate)
    }

    /// Success rate
    fn success_rate(&self) -> f64 {
        self.inner.success_rate()
    }

    /// Convert to dict (for JSON serialization)
    fn to_dict(&self, py: Python<'_>) -> PyResult<PyObject> {
        let dict = pyo3::types::PyDict::new(py);

        dict.set_item("entity_id", &self.inner.entity_id)?;
        dict.set_item("entity_type", &self.inner.entity_type)?;
        dict.set_item("entity_name", &self.inner.entity_name)?;

        // T3 fields (canonical 3D)
        dict.set_item("talent", self.inner.talent())?;
        dict.set_item("training", self.inner.training())?;
        dict.set_item("temperament", self.inner.temperament())?;

        // V3 fields (canonical 3D)
        dict.set_item("valuation", self.inner.valuation())?;
        dict.set_item("veracity", self.inner.veracity())?;
        dict.set_item("validity", self.inner.validity())?;

        // Witnessing
        dict.set_item("witnessed_by", self.inner.witnessed_by.clone())?;
        dict.set_item("has_witnessed", self.inner.has_witnessed.clone())?;

        // Metadata
        dict.set_item("action_count", self.inner.action_count)?;
        dict.set_item("success_count", self.inner.success_count)?;
        dict.set_item("witness_count", self.inner.witness_count)?;

        Ok(dict.into())
    }

    fn __repr__(&self) -> String {
        format!(
            "EntityTrust('{}', t3={:.3}, level={})",
            self.inner.entity_id,
            self.inner.t3_average(),
            self.inner.trust_level()
        )
    }
}

/// Python-exposed TrustStore (wraps FileStore or InMemoryStore)
#[pyclass(name = "TrustStore")]
pub struct PyTrustStore {
    #[cfg(feature = "file-store")]
    inner: Arc<RwLock<FileStore>>,
    #[cfg(not(feature = "file-store"))]
    inner: Arc<RwLock<InMemoryStore>>,
}

#[pymethods]
impl PyTrustStore {
    /// Create a new trust store at the given path
    #[new]
    #[pyo3(signature = (path=None))]
    fn new(path: Option<&str>) -> PyResult<Self> {
        #[cfg(feature = "file-store")]
        {
            let store = match path {
                Some(p) => FileStore::new(p),
                None => FileStore::open_default(),
            }.map_err(|e| PyValueError::new_err(e.to_string()))?;

            Ok(Self {
                inner: Arc::new(RwLock::new(store)),
            })
        }

        #[cfg(not(feature = "file-store"))]
        {
            Ok(Self {
                inner: Arc::new(RwLock::new(InMemoryStore::new())),
            })
        }
    }

    /// Get entity trust (creates if doesn't exist)
    fn get(&self, entity_id: &str) -> PyResult<PyEntityTrust> {
        let store = self.inner.read();
        let trust = store.get(entity_id)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(PyEntityTrust { inner: trust })
    }

    /// Save entity trust
    fn save(&self, trust: &PyEntityTrust) -> PyResult<()> {
        let store = self.inner.read();
        store.save(&trust.inner)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Update entity from outcome
    fn update(&self, entity_id: &str, success: bool, magnitude: f64) -> PyResult<PyEntityTrust> {
        let store = self.inner.read();
        let trust = store.update(entity_id, success, magnitude)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(PyEntityTrust { inner: trust })
    }

    /// Witness event between two entities
    fn witness(
        &self,
        witness_id: &str,
        target_id: &str,
        success: bool,
        magnitude: f64,
    ) -> PyResult<(PyEntityTrust, PyEntityTrust)> {
        let store = self.inner.read();
        let (witness, target) = store.witness(witness_id, target_id, success, magnitude)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok((PyEntityTrust { inner: witness }, PyEntityTrust { inner: target }))
    }

    /// List all entity IDs
    #[pyo3(signature = (entity_type=None))]
    fn list_entities(&self, entity_type: Option<&str>) -> PyResult<Vec<String>> {
        let store = self.inner.read();
        let etype = entity_type.map(|t| {
            EntityType::from_entity_id(&format!("{}:_", t)).ok()
        }).flatten();

        store.list(etype.as_ref())
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Check if entity exists
    fn exists(&self, entity_id: &str) -> PyResult<bool> {
        let store = self.inner.read();
        store.exists(entity_id)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Delete entity
    fn delete(&self, entity_id: &str) -> PyResult<bool> {
        let store = self.inner.read();
        store.delete(entity_id)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Get entities by type
    fn get_by_type(&self, entity_type: &str) -> PyResult<Vec<PyEntityTrust>> {
        let store = self.inner.read();
        let etype = EntityType::from_entity_id(&format!("{}:_", entity_type))
            .map_err(|e| PyValueError::new_err(e.to_string()))?;

        let ids = store.list(Some(&etype))
            .map_err(|e| PyValueError::new_err(e.to_string()))?;

        let mut trusts = Vec::new();
        for id in ids {
            if let Ok(trust) = store.get(&id) {
                trusts.push(PyEntityTrust { inner: trust });
            }
        }

        Ok(trusts)
    }

    fn __repr__(&self) -> String {
        #[cfg(feature = "file-store")]
        {
            let store = self.inner.read();
            format!("TrustStore(path='{}')", store.base_dir().display())
        }
        #[cfg(not(feature = "file-store"))]
        {
            "TrustStore(in-memory)".to_string()
        }
    }
}

/// Create in-memory store (for testing)
#[pyfunction]
fn create_memory_store() -> PyResult<PyTrustStore> {
    PyTrustStore::new(None)
}

/// Python module definition
#[pymodule]
fn web4_trust(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyT3Tensor>()?;
    m.add_class::<PyV3Tensor>()?;
    m.add_class::<PyEntityTrust>()?;
    m.add_class::<PyTrustStore>()?;
    m.add_function(wrap_pyfunction!(create_memory_store, m)?)?;

    // Version info
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;

    Ok(())
}
