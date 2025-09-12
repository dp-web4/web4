# Web4 T3/V3 Tensor Specification

This document defines the Trust (T3) and Value (V3) tensor systems that provide nuanced, multi-dimensional assessment of entity capabilities and value creation in Web4.

## 1. Overview

Traditional reputation systems reduce complex behaviors to simple scores. Web4's tensor approach captures the multi-dimensional nature of trust and value, enabling context-aware assessment that evolves through actual performance.

## 2. T3 Tensor: Trust Through Capability

The T3 Tensor measures an entity's trustworthiness through three capability dimensions:

### 2.1 Dimensions

#### Talent (Inherent Capability)
- **Range**: 0.0 to 1.0
- **Measures**: Natural aptitude, creativity, problem-solving ability
- **Updates**: Increases with novel solutions, decreases with repeated failures
- **Context**: Domain-specific (e.g., high talent in analysis, low in design)

#### Training (Acquired Expertise)
- **Range**: 0.0 to 1.0
- **Measures**: Learned skills, domain knowledge, experience
- **Updates**: Grows with successful repetitions, domain exposure
- **Context**: Skill-specific and measurable through certifications

#### Temperament (Behavioral Reliability)
- **Range**: 0.0 to 1.0
- **Measures**: Consistency, reliability, ethical behavior
- **Updates**: Improves with consistent performance, degrades with violations
- **Context**: Universal but weighted by role requirements

### 2.2 T3 Tensor Structure

```json
{
  "t3_tensor": {
    "global": {
      "talent": 0.75,
      "training": 0.82,
      "temperament": 0.91
    },
    "contextual": {
      "data_analysis": {
        "talent": 0.85,
        "training": 0.90,
        "temperament": 0.95
      },
      "project_management": {
        "talent": 0.65,
        "training": 0.70,
        "temperament": 0.91
      }
    },
    "evolution": [
      {
        "timestamp": "2025-01-11T15:00:00Z",
        "context": "data_analysis",
        "action": "r6:web4:...",
        "deltas": {
          "talent": 0.02,
          "training": 0.01,
          "temperament": 0.0
        },
        "reason": "Novel approach to complex analysis"
      }
    ]
  }
}
```

### 2.3 T3 Evolution Mechanics

#### Performance-Based Updates

T3 scores evolve based on R6 action outcomes:

| Outcome | Talent Impact | Training Impact | Temperament Impact |
|---------|--------------|-----------------|-------------------|
| Novel Success | +0.02 to +0.05 | +0.01 to +0.02 | +0.01 |
| Standard Success | 0 | +0.005 to +0.01 | +0.005 |
| Expected Failure | -0.01 | 0 | 0 |
| Unexpected Failure | -0.02 | -0.01 | -0.02 |
| Ethics Violation | -0.05 | 0 | -0.10 |

#### Decay and Refresh

- **Training Decay**: -0.001 per month without practice
- **Temperament Recovery**: +0.01 per month of good behavior
- **Talent Stability**: No decay, represents inherent capability

## 3. V3 Tensor: Value Through Verification

The V3 Tensor quantifies value creation through three verification dimensions:

### 3.1 Dimensions

#### Valuation (Subjective Worth)
- **Range**: Variable (can exceed 1.0)
- **Measures**: Perceived value by recipients
- **Updates**: Each transaction adds to history
- **Context**: Recipient-specific and use-case dependent

#### Veracity (Objective Accuracy)
- **Range**: 0.0 to 1.0
- **Measures**: Truthfulness, accuracy, reproducibility
- **Updates**: External validation and witness attestation
- **Context**: Domain-specific verification standards

#### Validity (Confirmed Transfer)
- **Range**: 0.0 to 1.0
- **Measures**: Actual value delivery and receipt
- **Updates**: Binary per transaction, averaged over time
- **Context**: Completion of value transfer cycle

### 3.2 V3 Tensor Structure

```json
{
  "v3_tensor": {
    "aggregate": {
      "total_value_created": 15420,  // In ATP units
      "average_valuation": 0.87,
      "veracity_score": 0.93,
      "validity_rate": 0.98
    },
    "recent": [
      {
        "timestamp": "2025-01-11T14:00:00Z",
        "action": "r6:web4:...",
        "valuation": 0.95,
        "veracity": 0.98,
        "validity": 1.0,
        "atp_generated": 55,
        "recipient": "lct:web4:...",
        "witness_count": 3
      }
    ],
    "by_context": {
      "data_processing": {
        "transactions": 45,
        "average_valuation": 0.91,
        "veracity": 0.95,
        "validity": 0.99
      },
      "content_creation": {
        "transactions": 23,
        "average_valuation": 0.78,
        "veracity": 0.88,
        "validity": 0.96
      }
    }
  }
}
```

### 3.3 V3 Calculation

For each completed R6 action:

1. **Valuation** = (ATP_earned / ATP_expected) * recipient_satisfaction
2. **Veracity** = (verified_claims / total_claims) * witness_confidence
3. **Validity** = 1.0 if value_transferred else 0.0

Aggregate scores use weighted averages based on recency and significance.

## 4. Tensor Interactions

### 4.1 T3 → V3 Influence

Higher T3 scores correlate with better V3 outcomes:
- High **Talent** → Higher **Valuation** (innovative solutions valued more)
- High **Training** → Higher **Veracity** (expertise produces accurate results)
- High **Temperament** → Higher **Validity** (reliability ensures delivery)

### 4.2 V3 → T3 Feedback

V3 outcomes influence T3 evolution:
- Consistent high **Valuation** → Talent recognition
- Verified **Veracity** → Training validation
- Perfect **Validity** → Temperament reinforcement

## 5. Contextual Application

### 5.1 Role Matching

Roles specify required T3 thresholds:

```json
{
  "role_requirements": {
    "minimum_t3": {
      "talent": 0.6,
      "training": 0.7,
      "temperament": 0.8
    },
    "preferred_t3": {
      "talent": 0.8,
      "training": 0.85,
      "temperament": 0.9
    }
  }
}
```

### 5.2 Value Pricing

ATP costs derived from expected V3:

```
ATP_price = base_cost * (1 + expected_valuation) * veracity_weight * validity_probability
```

## 6. Implementation Requirements

### 6.1 Calculation Precision
- All tensor values MUST use at least 3 decimal places
- Updates MUST be atomic and consistent
- Historical data MUST be preserved

### 6.2 Update Frequency
- T3 updates SHOULD occur after each R6 action
- V3 updates MUST occur upon value confirmation
- Decay calculations SHOULD run daily

### 6.3 Context Segregation
- Global scores MUST be weighted averages
- Context-specific scores MUST be tracked separately
- New contexts MUST inherit from global initially

## 7. Privacy and Gaming Prevention

### 7.1 Anti-Gaming Measures
- Exponential decay on repeated similar actions
- Witness diversity requirements
- Temporal distribution analysis
- Cross-validation with peer entities

### 7.2 Privacy Protection
- Tensor details MAY be selectively disclosed
- Aggregate scores MAY be public
- Evolution history MAY be truncated
- Context labels MAY be anonymized

## 8. Advanced Features

### 8.1 Tensor Prediction
Based on historical patterns:
- Predict T3 evolution trajectories
- Estimate V3 outcomes for actions
- Recommend improvement strategies

### 8.2 Tensor Composition
For composite entities:
- Team T3 = weighted average of members
- Organization V3 = sum of department contributions
- Role T3 = average of historical performers

### 8.3 Cross-Tensor Analytics
- Identify T3/V3 correlation patterns
- Detect anomalous tensor evolution
- Optimize for specific tensor targets

## 9. Integration with R6

The R6 framework provides the primary mechanism for tensor updates:

1. **Before Action**: T3 used for confidence calculation
2. **During Action**: Real-time performance monitoring
3. **After Action**: V3 assessment and T3 evolution
4. **As Reference**: Historical tensors inform future actions

This creates a continuous learning loop where every action refines the system's understanding of entity capabilities and value creation patterns.