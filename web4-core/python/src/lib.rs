//! Python bindings for web4-core
//!
//! Provides Python access to Web4 primitives via PyO3.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use web4_core::{self as core};

/// Python-compatible error conversion
fn to_py_err(e: core::Web4Error) -> PyErr {
    PyValueError::new_err(e.to_string())
}

/// Entity type that an LCT can represent
#[pyclass]
#[derive(Clone)]
pub enum PyEntityType {
    Human,
    AiSoftware,
    AiEmbodied,
    Organization,
    Role,
    Task,
    Resource,
    Hybrid,
}

impl From<PyEntityType> for core::EntityType {
    fn from(t: PyEntityType) -> Self {
        match t {
            PyEntityType::Human => core::EntityType::Human,
            PyEntityType::AiSoftware => core::EntityType::AiSoftware,
            PyEntityType::AiEmbodied => core::EntityType::AiEmbodied,
            PyEntityType::Organization => core::EntityType::Organization,
            PyEntityType::Role => core::EntityType::Role,
            PyEntityType::Task => core::EntityType::Task,
            PyEntityType::Resource => core::EntityType::Resource,
            PyEntityType::Hybrid => core::EntityType::Hybrid,
        }
    }
}

impl From<core::EntityType> for PyEntityType {
    fn from(t: core::EntityType) -> Self {
        match t {
            core::EntityType::Human => PyEntityType::Human,
            core::EntityType::AiSoftware => PyEntityType::AiSoftware,
            core::EntityType::AiEmbodied => PyEntityType::AiEmbodied,
            core::EntityType::Organization => PyEntityType::Organization,
            core::EntityType::Role => PyEntityType::Role,
            core::EntityType::Task => PyEntityType::Task,
            core::EntityType::Resource => PyEntityType::Resource,
            core::EntityType::Hybrid => PyEntityType::Hybrid,
        }
    }
}

/// Trust dimension for T3 tensor
#[pyclass]
#[derive(Clone)]
pub enum PyTrustDimension {
    Competence,
    Integrity,
    Benevolence,
    Predictability,
    Transparency,
    Accountability,
}

impl From<PyTrustDimension> for core::TrustDimension {
    fn from(d: PyTrustDimension) -> Self {
        match d {
            PyTrustDimension::Competence => core::TrustDimension::Competence,
            PyTrustDimension::Integrity => core::TrustDimension::Integrity,
            PyTrustDimension::Benevolence => core::TrustDimension::Benevolence,
            PyTrustDimension::Predictability => core::TrustDimension::Predictability,
            PyTrustDimension::Transparency => core::TrustDimension::Transparency,
            PyTrustDimension::Accountability => core::TrustDimension::Accountability,
        }
    }
}

/// Value dimension for V3 tensor
#[pyclass]
#[derive(Clone)]
pub enum PyValueDimension {
    Utility,
    Novelty,
    Quality,
    Timeliness,
    Relevance,
    Leverage,
}

impl From<PyValueDimension> for core::ValueDimension {
    fn from(d: PyValueDimension) -> Self {
        match d {
            PyValueDimension::Utility => core::ValueDimension::Utility,
            PyValueDimension::Novelty => core::ValueDimension::Novelty,
            PyValueDimension::Quality => core::ValueDimension::Quality,
            PyValueDimension::Timeliness => core::ValueDimension::Timeliness,
            PyValueDimension::Relevance => core::ValueDimension::Relevance,
            PyValueDimension::Leverage => core::ValueDimension::Leverage,
        }
    }
}

/// A keypair for signing and verification
#[pyclass]
pub struct PyKeyPair {
    inner: core::KeyPair,
}

#[pymethods]
impl PyKeyPair {
    /// Generate a new random keypair
    #[staticmethod]
    pub fn generate() -> Self {
        Self {
            inner: core::KeyPair::generate(),
        }
    }

    /// Create from secret key bytes (32 bytes)
    #[staticmethod]
    pub fn from_secret_bytes(bytes: [u8; 32]) -> Self {
        Self {
            inner: core::KeyPair::from_secret_bytes(&bytes),
        }
    }

    /// Get the public key bytes
    pub fn public_key_bytes(&self) -> [u8; 32] {
        self.inner.public_key_bytes()
    }

    /// Get the secret key bytes (handle with care!)
    pub fn secret_key_bytes(&self) -> [u8; 32] {
        self.inner.secret_key_bytes()
    }

    /// Sign a message
    pub fn sign(&self, message: &[u8]) -> Vec<u8> {
        self.inner.sign(message).bytes.to_vec()
    }
}

/// Linked Context Token - the fundamental identity primitive
#[pyclass]
pub struct PyLct {
    inner: core::Lct,
}

#[pymethods]
impl PyLct {
    /// Create a new LCT, returns (PyLct, PyKeyPair)
    #[staticmethod]
    pub fn new(entity_type: PyEntityType, created_by: Option<String>) -> PyResult<(Self, PyKeyPair)> {
        let created_by_uuid = created_by
            .map(|s| uuid::Uuid::parse_str(&s))
            .transpose()
            .map_err(|e| PyValueError::new_err(format!("Invalid UUID: {}", e)))?;

        let (lct, keypair) = core::Lct::new(entity_type.into(), created_by_uuid);
        Ok((Self { inner: lct }, PyKeyPair { inner: keypair }))
    }

    /// Get the LCT ID as a string
    #[getter]
    pub fn id(&self) -> String {
        self.inner.id.to_string()
    }

    /// Get the entity type
    #[getter]
    pub fn entity_type(&self) -> PyEntityType {
        self.inner.entity_type.clone().into()
    }

    /// Check if LCT is active
    pub fn is_active(&self) -> bool {
        self.inner.is_active()
    }

    /// Get trust ceiling based on hardware binding
    pub fn trust_ceiling(&self) -> f64 {
        self.inner.trust_ceiling()
    }

    /// Get coherence threshold for this entity type
    pub fn coherence_threshold(&self) -> f64 {
        self.inner.coherence_threshold()
    }

    /// Get the LCT fingerprint (short identifier)
    pub fn fingerprint(&self) -> String {
        self.inner.fingerprint()
    }

    /// Verify a signature
    pub fn verify_signature(&self, message: &[u8], signature: Vec<u8>) -> PyResult<bool> {
        let sig_bytes: [u8; 64] = signature
            .try_into()
            .map_err(|_| PyValueError::new_err("Signature must be 64 bytes"))?;
        let sig = core::SignatureBytes::from_bytes(sig_bytes);
        match self.inner.verify_signature(message, &sig) {
            Ok(()) => Ok(true),
            Err(_) => Ok(false),
        }
    }

    /// Create a child LCT under this parent
    pub fn create_child(&self, entity_type: PyEntityType) -> (Self, PyKeyPair) {
        let (lct, keypair) = self.inner.create_child(entity_type.into());
        (Self { inner: lct }, PyKeyPair { inner: keypair })
    }

    /// Void this LCT
    pub fn void(&mut self) {
        self.inner.void();
    }

    /// Slash this LCT
    pub fn slash(&mut self) {
        self.inner.slash();
    }

    /// Get parent ID (if any)
    #[getter]
    pub fn parent_id(&self) -> Option<String> {
        self.inner.parent_id.map(|id| id.to_string())
    }

    /// Get lineage depth
    #[getter]
    pub fn lineage_depth(&self) -> u32 {
        self.inner.lineage_depth
    }
}

/// Trust Tensor (T3) - 6-dimensional trust measurement
#[pyclass]
pub struct PyT3 {
    inner: core::T3,
}

#[pymethods]
impl PyT3 {
    /// Create a new T3 with neutral trust
    #[new]
    pub fn new() -> Self {
        Self {
            inner: core::T3::new(),
        }
    }

    /// Create T3 with specific scores
    #[staticmethod]
    pub fn with_scores(scores: [f64; 6]) -> PyResult<Self> {
        Ok(Self {
            inner: core::T3::with_scores(scores).map_err(to_py_err)?,
        })
    }

    /// Get score for a dimension
    pub fn score(&self, dimension: PyTrustDimension) -> f64 {
        self.inner.score(dimension.into())
    }

    /// Get weight for a dimension
    pub fn weight(&self, dimension: PyTrustDimension) -> f64 {
        self.inner.weight(dimension.into())
    }

    /// Get all dimension scores
    pub fn scores(&self) -> Vec<f64> {
        self.inner.scores().to_vec()
    }

    /// Record an observation
    pub fn observe(&mut self, dimension: PyTrustDimension, score: f64) -> PyResult<()> {
        self.inner.observe(dimension.into(), score).map_err(to_py_err)
    }

    /// Compute aggregate trust score
    pub fn aggregate(&self) -> f64 {
        self.inner.aggregate()
    }

    /// Apply time decay
    pub fn decay(&mut self, decay_factor: f64) {
        self.inner.decay(decay_factor);
    }

    /// Check if trust meets thresholds
    pub fn meets_thresholds(&self, min_scores: [f64; 6]) -> bool {
        self.inner.meets_thresholds(&min_scores)
    }
}

/// Value Tensor (V3) - 6-dimensional value measurement
#[pyclass]
pub struct PyV3 {
    inner: core::V3,
}

#[pymethods]
impl PyV3 {
    /// Create a new V3 with neutral value
    #[new]
    pub fn new() -> Self {
        Self {
            inner: core::V3::new(),
        }
    }

    /// Get score for a dimension
    pub fn score(&self, dimension: PyValueDimension) -> f64 {
        self.inner.score(dimension.into())
    }

    /// Get all dimension scores
    pub fn scores(&self) -> Vec<f64> {
        self.inner.scores().to_vec()
    }

    /// Record an observation
    pub fn observe(&mut self, dimension: PyValueDimension, score: f64) -> PyResult<()> {
        self.inner.observe(dimension.into(), score).map_err(to_py_err)
    }

    /// Compute aggregate value score
    pub fn aggregate(&self) -> f64 {
        self.inner.aggregate()
    }

    /// Apply time decay
    pub fn decay(&mut self, decay_factor: f64) {
        self.inner.decay(decay_factor);
    }
}

/// Identity Coherence score (C × S × Φ × R)
#[pyclass]
pub struct PyCoherence {
    inner: core::Coherence,
}

#[pymethods]
impl PyCoherence {
    /// Create a new coherence score with neutral values
    #[new]
    pub fn new() -> Self {
        Self {
            inner: core::Coherence::new(),
        }
    }

    /// Create with specific values
    #[staticmethod]
    pub fn with_values(
        continuity: f64,
        stability: f64,
        phi: f64,
        reachability: f64,
    ) -> PyResult<Self> {
        Ok(Self {
            inner: core::Coherence::with_values(continuity, stability, phi, reachability)
                .map_err(to_py_err)?,
        })
    }

    /// Get continuity factor
    #[getter]
    pub fn continuity(&self) -> f64 {
        self.inner.continuity
    }

    /// Get stability factor
    #[getter]
    pub fn stability(&self) -> f64 {
        self.inner.stability
    }

    /// Get phi factor
    #[getter]
    pub fn phi(&self) -> f64 {
        self.inner.phi
    }

    /// Get reachability factor
    #[getter]
    pub fn reachability(&self) -> f64 {
        self.inner.reachability
    }

    /// Compute total coherence (C × S × Φ × R)
    pub fn total(&self) -> f64 {
        self.inner.total()
    }

    /// Check if coherence meets threshold
    pub fn meets_threshold(&self, threshold: f64) -> bool {
        self.inner.meets_threshold(threshold)
    }

    /// Get the limiting factor
    pub fn limiting_factor(&self) -> (String, f64) {
        let (name, value) = self.inner.limiting_factor();
        (name.to_string(), value)
    }
}

/// Compute SHA-256 hash of data
#[pyfunction]
pub fn sha256(data: &[u8]) -> Vec<u8> {
    core::sha256(data).to_vec()
}

/// Compute SHA-256 hash and return as hex string
#[pyfunction]
pub fn sha256_hex(data: &[u8]) -> String {
    core::sha256_hex(data)
}

/// Get library version
#[pyfunction]
pub fn version() -> &'static str {
    core::VERSION
}

/// Python module definition
#[pymodule]
fn web4(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Enums
    m.add_class::<PyEntityType>()?;
    m.add_class::<PyTrustDimension>()?;
    m.add_class::<PyValueDimension>()?;

    // Core types
    m.add_class::<PyKeyPair>()?;
    m.add_class::<PyLct>()?;
    m.add_class::<PyT3>()?;
    m.add_class::<PyV3>()?;
    m.add_class::<PyCoherence>()?;

    // Functions
    m.add_function(wrap_pyfunction!(sha256, m)?)?;
    m.add_function(wrap_pyfunction!(sha256_hex, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;

    Ok(())
}
