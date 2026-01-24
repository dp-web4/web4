//! Trust and Value tensors
//!
//! Web4 uses two 6-dimensional tensors to capture trust and value:
//!
//! - **T3 (Trust Tensor)**: Measures trustworthiness across 6 dimensions
//! - **V3 (Value Tensor)**: Measures value contribution across 6 dimensions

mod t3;
mod v3;

pub use t3::T3Tensor;
pub use v3::V3Tensor;

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
}
