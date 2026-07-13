//! Trust/value tensor semantics for `web4-trust-core`.
//!
//! As of the **P3b convergence migration**, this crate no longer defines its own
//! `T3Tensor`/`V3Tensor`. There is now ONE canonical tensor: the fractal
//! `web4_core::t3::T3` / `web4_core::v3::V3` (each root dimension a node in an
//! open-ended RDF sub-graph, with per-dimension observation counts + confidence
//! weights). `EntityTrust` holds those types directly.
//!
//! What remains here:
//!
//! - [`TrustLevel`] — the categorical bucket derived from a T3's arithmetic-mean
//!   score (a `web4-trust-core` presentation concept, not part of the engine).
//! - The **trust-behavior semantics** (`update_from_outcome`, witness/alignment
//!   updates, temporal decay) as free functions over the canonical tensors.
//!   These are the *exact* per-dimension deltas the old `T3Tensor`/`V3Tensor`
//!   applied, re-expressed via `T3::apply_delta`/`V3::apply_delta` so that:
//!     * scores move **identically** to the pre-migration math, and
//!     * confidence is **gained additively** (each update is one observation).
//!   Keeping them in one place means `EntityTrust` and the Python/WASM tensor
//!   wrappers share a single source of truth — no parallel math to drift.
//!
//! See `web4-standard/ontology/t3v3-ontology.ttl` for the formal ontology.

use web4_core::t3::{TrustDimension, T3};
use web4_core::v3::{ValueDimension, V3};

/// Categorical trust level derived from T3 average
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
#[cfg_attr(feature = "python", pyo3::pyclass)]
pub enum TrustLevel {
    /// T3 average >= 0.8
    High,
    /// T3 average >= 0.6
    MediumHigh,
    /// T3 average >= 0.4
    Medium,
    /// T3 average >= 0.2
    Low,
    /// T3 average < 0.2
    Minimal,
}

impl TrustLevel {
    /// Convert from T3 average score
    pub fn from_score(score: f64) -> Self {
        if score >= 0.8 {
            TrustLevel::High
        } else if score >= 0.6 {
            TrustLevel::MediumHigh
        } else if score >= 0.4 {
            TrustLevel::Medium
        } else if score >= 0.2 {
            TrustLevel::Low
        } else {
            TrustLevel::Minimal
        }
    }

    /// Convert to string representation
    pub fn as_str(&self) -> &'static str {
        match self {
            TrustLevel::High => "high",
            TrustLevel::MediumHigh => "medium-high",
            TrustLevel::Medium => "medium",
            TrustLevel::Low => "low",
            TrustLevel::Minimal => "minimal",
        }
    }
}

impl std::fmt::Display for TrustLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.as_str())
    }
}

impl serde::Serialize for TrustLevel {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_str(self.as_str())
    }
}

impl<'de> serde::Deserialize<'de> for TrustLevel {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        Ok(TrustLevel::from_score(match s.as_str() {
            "high" => 0.8,
            "medium-high" => 0.6,
            "medium" => 0.4,
            "low" => 0.2,
            _ => 0.1,
        }))
    }
}

// ─── T3 trust-behavior semantics (canonical-tensor ports) ──────────────────

/// Arithmetic mean of the three T3 root scores.
///
/// This is the pre-migration `T3Tensor::average()` and drives [`TrustLevel`].
/// It is deliberately **not** `T3::aggregate()` (a confidence-weighted geometric
/// mean) — the categorical trust level is defined over the flat average.
pub fn t3_average(t3: &T3) -> f64 {
    (t3.score(TrustDimension::Talent)
        + t3.score(TrustDimension::Training)
        + t3.score(TrustDimension::Temperament))
        / 3.0
}

/// Categorical trust level from a T3 (via [`t3_average`]).
pub fn t3_level(t3: &T3) -> TrustLevel {
    TrustLevel::from_score(t3_average(t3))
}

/// Update a T3 from an action outcome — faithful port of the pre-migration
/// `T3Tensor::update_from_outcome`.
///
/// Success increases trust slowly (asymptotic to 1.0); failure decreases it
/// faster (trust is hard to earn, easy to lose). Training is most affected,
/// then temperament, then talent. Deltas are applied via `T3::apply_delta`,
/// which clamps to `[0, 1]` identically to the old code and additionally counts
/// each as one observation (confidence gained).
pub fn t3_update_from_outcome(t3: &mut T3, success: bool, magnitude: f64) {
    let magnitude = magnitude.clamp(0.0, 1.0);
    // All three deltas are derived from the *pre-update* training score.
    let training = t3.score(TrustDimension::Training);
    let delta = if success {
        magnitude * 0.05 * (1.0 - training)
    } else {
        -magnitude * 0.10 * training
    };
    t3.apply_delta(TrustDimension::Training, delta);
    t3.apply_delta(TrustDimension::Temperament, delta * 0.5);
    t3.apply_delta(TrustDimension::Talent, delta * 0.3);
}

/// Update temperament from being witnessed — port of
/// `T3Tensor::update_temperament_from_witness`.
pub fn t3_update_temperament_from_witness(t3: &mut T3, success: bool, magnitude: f64) {
    let temperament = t3.score(TrustDimension::Temperament);
    let delta = if success {
        magnitude * 0.03 * (1.0 - temperament)
    } else {
        -magnitude * 0.05 * temperament
    };
    t3.apply_delta(TrustDimension::Temperament, delta);
}

/// Update temperament from an alignment observation — port of
/// `T3Tensor::update_temperament_from_alignment`. Note both branches *add*
/// (a correct witness judgment builds character either way).
pub fn t3_update_temperament_from_alignment(t3: &mut T3, success: bool, magnitude: f64) {
    let temperament = t3.score(TrustDimension::Temperament);
    let delta = if success {
        magnitude * 0.02 * (1.0 - temperament)
    } else {
        magnitude * 0.01 * (1.0 - temperament)
    };
    t3.apply_delta(TrustDimension::Temperament, delta);
}

/// Apply temporal decay toward a floor of 0.3 — port of `T3Tensor::apply_decay`.
///
/// Training decays most, temperament slightly less, talent slowest. Returns
/// `true` if meaningful decay occurred (> 0.001 change in training). The
/// multiplicative-toward-floor transform is expressed as a signed delta into
/// `T3::apply_delta`, so the resulting scores are identical to the old code.
pub fn t3_apply_decay(t3: &mut T3, days_inactive: f64, decay_rate: f64) -> bool {
    if days_inactive <= 0.0 {
        return false;
    }
    let decay_factor = (1.0 - decay_rate).powf(days_inactive);
    let floor = 0.3;
    let decay_value = |current: f64, factor: f64| -> f64 {
        (floor + (current - floor) * decay_factor * factor).max(floor)
    };

    let old_training = t3.score(TrustDimension::Training);
    let new_training = decay_value(old_training, 1.0);
    t3.apply_delta(TrustDimension::Training, new_training - old_training);

    let old_temperament = t3.score(TrustDimension::Temperament);
    let new_temperament = decay_value(old_temperament, 0.98);
    t3.apply_delta(TrustDimension::Temperament, new_temperament - old_temperament);

    // PROTOCOL INVARIANT (spec §2.3, t3v3-012): Talent MUST NOT decay through
    // inactivity. The previous `decay_value(old_talent, 0.995)` was the LITERAL
    // value spec §10.4 pre-emptively names as violating ("any decay value
    // violates the spec"). Talent passes through untouched (audit C192-N1).

    (old_training - new_training).abs() > 0.001
}

/// Absolute-set a single T3 root score (clamped to `[0, 1]`), preserving
/// observation counts and sub-dimensions. Used by the Python/WASM tensor
/// setters, which expose direct assignment. Implemented as a signed
/// `apply_delta`, so it counts as one observation.
pub fn t3_set_score(t3: &mut T3, dimension: TrustDimension, value: f64) {
    let delta = value.clamp(0.0, 1.0) - t3.score(dimension);
    t3.apply_delta(dimension, delta);
}

// ─── V3 value semantics (canonical-tensor ports) ───────────────────────────

/// Arithmetic mean of the three V3 root scores — port of `V3Tensor::average()`.
pub fn v3_average(v3: &V3) -> f64 {
    (v3.score(ValueDimension::Valuation)
        + v3.score(ValueDimension::Veracity)
        + v3.score(ValueDimension::Validity))
        / 3.0
}

/// Add to valuation (effort/energy invested) — port of `V3Tensor::add_valuation`
/// and `add_contribution` (both target valuation). `apply_delta` clamps `[0,1]`;
/// for the small positive amounts used here this is identical to the old
/// `min(1.0)`.
pub fn v3_add_valuation(v3: &mut V3, amount: f64) {
    v3.apply_delta(ValueDimension::Valuation, amount);
}

/// Grow validity (network/standing) — port of `V3Tensor::grow_validity`.
pub fn v3_grow_validity(v3: &mut V3, amount: f64) {
    v3.apply_delta(ValueDimension::Validity, amount);
}

/// Update veracity from being witnessed (reputation) — port of
/// `V3Tensor::update_veracity`.
pub fn v3_update_veracity(v3: &mut V3, success: bool, magnitude: f64) {
    let veracity = v3.score(ValueDimension::Veracity);
    let delta = if success {
        magnitude * 0.8 * (1.0 - veracity)
    } else {
        -magnitude * 0.5 * veracity
    };
    v3.apply_delta(ValueDimension::Veracity, delta);
}

/// Apply temporal decay toward a floor of 0.3 — port of `V3Tensor::apply_decay`.
/// Validity decays directly; valuation fades slightly slower; veracity is not
/// decayed (reputation is externally anchored).
pub fn v3_apply_decay(v3: &mut V3, days_inactive: f64, decay_rate: f64) {
    if days_inactive <= 0.0 {
        return;
    }
    let decay_factor = (1.0 - decay_rate).powf(days_inactive);
    let floor = 0.3;
    let decay_value = |current: f64, factor: f64| -> f64 {
        (floor + (current - floor) * decay_factor * factor).max(floor)
    };

    let old_validity = v3.score(ValueDimension::Validity);
    let new_validity = decay_value(old_validity, 1.0);
    v3.apply_delta(ValueDimension::Validity, new_validity - old_validity);

    let old_valuation = v3.score(ValueDimension::Valuation);
    let new_valuation = decay_value(old_valuation, 0.99);
    v3.apply_delta(ValueDimension::Valuation, new_valuation - old_valuation);
}

/// Absolute-set a single V3 root score (clamped to `[0, 1]`), preserving
/// observation counts and sub-dimensions. Mirrors [`t3_set_score`].
pub fn v3_set_score(v3: &mut V3, dimension: ValueDimension, value: f64) {
    let delta = value.clamp(0.0, 1.0) - v3.score(dimension);
    v3.apply_delta(dimension, delta);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_trust_level_from_score() {
        assert_eq!(TrustLevel::from_score(0.9), TrustLevel::High);
        assert_eq!(TrustLevel::from_score(0.7), TrustLevel::MediumHigh);
        assert_eq!(TrustLevel::from_score(0.5), TrustLevel::Medium);
        assert_eq!(TrustLevel::from_score(0.3), TrustLevel::Low);
        assert_eq!(TrustLevel::from_score(0.1), TrustLevel::Minimal);
    }

    #[test]
    fn test_new_t3_is_neutral() {
        let t3 = T3::new();
        assert_eq!(t3_average(&t3), 0.5);
        assert_eq!(t3_level(&t3), TrustLevel::Medium);
    }

    #[test]
    fn test_update_from_outcome_moves_training() {
        let mut t3 = T3::new();
        t3_update_from_outcome(&mut t3, true, 0.1);
        assert!(t3.score(TrustDimension::Training) > 0.5);
        let mut t3f = T3::new();
        t3_update_from_outcome(&mut t3f, false, 0.1);
        assert!(t3f.score(TrustDimension::Training) < 0.5);
    }

    #[test]
    fn test_asymmetric_updates() {
        let mut s = T3::new();
        let mut f = T3::new();
        t3_update_from_outcome(&mut s, true, 0.1);
        t3_update_from_outcome(&mut f, false, 0.1);
        let up = (s.score(TrustDimension::Training) - 0.5).abs();
        let down = (f.score(TrustDimension::Training) - 0.5).abs();
        assert!(down > up, "failure should hit harder than success");
    }

    #[test]
    fn test_decay_floor() {
        let mut t3 = T3::from_parts([0.9, 0.9, 0.9], [1, 1, 1]);
        let decayed = t3_apply_decay(&mut t3, 30.0, 0.01);
        assert!(decayed);
        assert!(t3.score(TrustDimension::Training) < 0.9);
        assert!(t3.score(TrustDimension::Training) >= 0.3);
    }
}
