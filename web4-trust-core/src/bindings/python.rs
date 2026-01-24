//! Python bindings via PyO3
//!
//! Exposes the Rust trust primitives to Python for use in hooks.

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::PyModule;

use crate::tensor::{T3Tensor as RustT3, V3Tensor as RustV3};
use crate::entity::{EntityTrust as RustEntityTrust, EntityType};
use crate::storage::TrustStore;

#[cfg(feature = "file-store")]
use crate::storage::FileStore;

use std::sync::Arc;
use parking_lot::RwLock;

/// Python-exposed T3 Trust Tensor
#[pyclass(name = "T3Tensor")]
#[derive(Clone)]
pub struct PyT3Tensor {
    inner: RustT3,
}

#[pymethods]
impl PyT3Tensor {
    #[new]
    #[pyo3(signature = (competence=0.5, reliability=0.5, consistency=0.5, witnesses=0.5, lineage=0.5, alignment=0.5))]
    fn new(
        competence: f64,
        reliability: f64,
        consistency: f64,
        witnesses: f64,
        lineage: f64,
        alignment: f64,
    ) -> Self {
        Self {
            inner: RustT3::new(competence, reliability, consistency, witnesses, lineage, alignment),
        }
    }

    /// Create a neutral tensor (all 0.5)
    #[staticmethod]
    fn neutral() -> Self {
        Self { inner: RustT3::neutral() }
    }

    #[getter]
    fn competence(&self) -> f64 { self.inner.competence }

    #[setter]
    fn set_competence(&mut self, value: f64) { self.inner.competence = value.clamp(0.0, 1.0); }

    #[getter]
    fn reliability(&self) -> f64 { self.inner.reliability }

    #[setter]
    fn set_reliability(&mut self, value: f64) { self.inner.reliability = value.clamp(0.0, 1.0); }

    #[getter]
    fn consistency(&self) -> f64 { self.inner.consistency }

    #[setter]
    fn set_consistency(&mut self, value: f64) { self.inner.consistency = value.clamp(0.0, 1.0); }

    #[getter]
    fn witnesses(&self) -> f64 { self.inner.witnesses }

    #[setter]
    fn set_witnesses(&mut self, value: f64) { self.inner.witnesses = value.clamp(0.0, 1.0); }

    #[getter]
    fn lineage(&self) -> f64 { self.inner.lineage }

    #[setter]
    fn set_lineage(&mut self, value: f64) { self.inner.lineage = value.clamp(0.0, 1.0); }

    #[getter]
    fn alignment(&self) -> f64 { self.inner.alignment }

    #[setter]
    fn set_alignment(&mut self, value: f64) { self.inner.alignment = value.clamp(0.0, 1.0); }

    /// Calculate average trust score
    fn average(&self) -> f64 {
        self.inner.average()
    }

    /// Get trust level as string
    fn level(&self) -> String {
        self.inner.level().to_string()
    }

    /// Update from action outcome
    fn update_from_outcome(&mut self, success: bool, magnitude: f64) {
        self.inner.update_from_outcome(success, magnitude);
    }

    /// Apply temporal decay
    fn apply_decay(&mut self, days_inactive: f64, decay_rate: f64) -> bool {
        self.inner.apply_decay(days_inactive, decay_rate)
    }

    fn __repr__(&self) -> String {
        format!(
            "T3Tensor(competence={:.3}, reliability={:.3}, consistency={:.3}, witnesses={:.3}, lineage={:.3}, alignment={:.3})",
            self.inner.competence, self.inner.reliability, self.inner.consistency,
            self.inner.witnesses, self.inner.lineage, self.inner.alignment
        )
    }
}

/// Python-exposed V3 Value Tensor
#[pyclass(name = "V3Tensor")]
#[derive(Clone)]
pub struct PyV3Tensor {
    inner: RustV3,
}

#[pymethods]
impl PyV3Tensor {
    #[new]
    #[pyo3(signature = (energy=0.5, contribution=0.5, stewardship=0.5, network=0.5, reputation=0.5, temporal=0.5))]
    fn new(
        energy: f64,
        contribution: f64,
        stewardship: f64,
        network: f64,
        reputation: f64,
        temporal: f64,
    ) -> Self {
        Self {
            inner: RustV3::new(energy, contribution, stewardship, network, reputation, temporal),
        }
    }

    #[staticmethod]
    fn neutral() -> Self {
        Self { inner: RustV3::neutral() }
    }

    #[getter]
    fn energy(&self) -> f64 { self.inner.energy }

    #[setter]
    fn set_energy(&mut self, value: f64) { self.inner.energy = value.clamp(0.0, 1.0); }

    #[getter]
    fn contribution(&self) -> f64 { self.inner.contribution }

    #[setter]
    fn set_contribution(&mut self, value: f64) { self.inner.contribution = value.clamp(0.0, 1.0); }

    #[getter]
    fn stewardship(&self) -> f64 { self.inner.stewardship }

    #[setter]
    fn set_stewardship(&mut self, value: f64) { self.inner.stewardship = value.clamp(0.0, 1.0); }

    #[getter]
    fn network(&self) -> f64 { self.inner.network }

    #[setter]
    fn set_network(&mut self, value: f64) { self.inner.network = value.clamp(0.0, 1.0); }

    #[getter]
    fn reputation(&self) -> f64 { self.inner.reputation }

    #[setter]
    fn set_reputation(&mut self, value: f64) { self.inner.reputation = value.clamp(0.0, 1.0); }

    #[getter]
    fn temporal(&self) -> f64 { self.inner.temporal }

    #[setter]
    fn set_temporal(&mut self, value: f64) { self.inner.temporal = value.clamp(0.0, 1.0); }

    fn average(&self) -> f64 {
        self.inner.average()
    }

    fn __repr__(&self) -> String {
        format!(
            "V3Tensor(energy={:.3}, contribution={:.3}, stewardship={:.3}, network={:.3}, reputation={:.3}, temporal={:.3})",
            self.inner.energy, self.inner.contribution, self.inner.stewardship,
            self.inner.network, self.inner.reputation, self.inner.temporal
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

    // T3 accessors
    #[getter]
    fn competence(&self) -> f64 { self.inner.t3.competence }

    #[setter]
    fn set_competence(&mut self, value: f64) { self.inner.t3.competence = value.clamp(0.0, 1.0); }

    #[getter]
    fn reliability(&self) -> f64 { self.inner.t3.reliability }

    #[setter]
    fn set_reliability(&mut self, value: f64) { self.inner.t3.reliability = value.clamp(0.0, 1.0); }

    #[getter]
    fn consistency(&self) -> f64 { self.inner.t3.consistency }

    #[setter]
    fn set_consistency(&mut self, value: f64) { self.inner.t3.consistency = value.clamp(0.0, 1.0); }

    #[getter]
    fn witnesses(&self) -> f64 { self.inner.t3.witnesses }

    #[setter]
    fn set_witnesses(&mut self, value: f64) { self.inner.t3.witnesses = value.clamp(0.0, 1.0); }

    #[getter]
    fn lineage(&self) -> f64 { self.inner.t3.lineage }

    #[setter]
    fn set_lineage(&mut self, value: f64) { self.inner.t3.lineage = value.clamp(0.0, 1.0); }

    #[getter]
    fn alignment(&self) -> f64 { self.inner.t3.alignment }

    #[setter]
    fn set_alignment(&mut self, value: f64) { self.inner.t3.alignment = value.clamp(0.0, 1.0); }

    // V3 accessors
    #[getter]
    fn energy(&self) -> f64 { self.inner.v3.energy }

    #[setter]
    fn set_energy(&mut self, value: f64) { self.inner.v3.energy = value.clamp(0.0, 1.0); }

    #[getter]
    fn contribution(&self) -> f64 { self.inner.v3.contribution }

    #[setter]
    fn set_contribution(&mut self, value: f64) { self.inner.v3.contribution = value.clamp(0.0, 1.0); }

    #[getter]
    fn stewardship(&self) -> f64 { self.inner.v3.stewardship }

    #[setter]
    fn set_stewardship(&mut self, value: f64) { self.inner.v3.stewardship = value.clamp(0.0, 1.0); }

    #[getter]
    fn network(&self) -> f64 { self.inner.v3.network }

    #[setter]
    fn set_network(&mut self, value: f64) { self.inner.v3.network = value.clamp(0.0, 1.0); }

    #[getter]
    fn reputation(&self) -> f64 { self.inner.v3.reputation }

    #[setter]
    fn set_reputation(&mut self, value: f64) { self.inner.v3.reputation = value.clamp(0.0, 1.0); }

    #[getter]
    fn temporal(&self) -> f64 { self.inner.v3.temporal }

    #[setter]
    fn set_temporal(&mut self, value: f64) { self.inner.v3.temporal = value.clamp(0.0, 1.0); }

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

        // T3 fields
        dict.set_item("competence", self.inner.t3.competence)?;
        dict.set_item("reliability", self.inner.t3.reliability)?;
        dict.set_item("consistency", self.inner.t3.consistency)?;
        dict.set_item("witnesses", self.inner.t3.witnesses)?;
        dict.set_item("lineage", self.inner.t3.lineage)?;
        dict.set_item("alignment", self.inner.t3.alignment)?;

        // V3 fields
        dict.set_item("energy", self.inner.v3.energy)?;
        dict.set_item("contribution", self.inner.v3.contribution)?;
        dict.set_item("stewardship", self.inner.v3.stewardship)?;
        dict.set_item("network", self.inner.v3.network)?;
        dict.set_item("reputation", self.inner.v3.reputation)?;
        dict.set_item("temporal", self.inner.v3.temporal)?;

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
    // This is a workaround - ideally we'd have separate types
    // For now, just return a new store
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
