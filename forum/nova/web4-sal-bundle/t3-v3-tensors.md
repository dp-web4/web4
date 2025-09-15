# Web4 T3/V3 Tensor Specification

This document defines the Trust (T3) and Value (V3) tensor systems that provide nuanced, multi-dimensional assessment of entity capabilities and value creation in Web4.

## 1. Overview

Traditional reputation systems reduce complex behaviors to simple scores. Web4's tensor approach captures the multi-dimensional nature of trust and value, enabling context-aware assessment that evolves through actual performance.

### 1.1 Critical Design Principle: Role-Contextual Trust

**T3/V3 tensors are not absolute properties - they exist only within role contexts.** An entity trusted as a surgeon has no inherent trust as a mechanic. Trust and value are always qualified by the role being performed. RDF triples in the MRH explicitly bind tensors to entity-role pairs, ensuring trust assessments remain contextually appropriate.

## 2. T3 Tensor: Trust Through Capability

The T3 Tensor measures an entity's trustworthiness through three capability dimensions:

### 2.1 Dimensions

#### Talent (Role-Specific Capability)
- **Range**: 0.0 to 1.0
- **Measures**: Natural aptitude for specific role, creativity within domain
- **Updates**: Increases with novel solutions in role, decreases with role-specific failures
- **Context**: Always role-qualified (e.g., talent as analyst, not general talent)

#### Training (Role-Specific Expertise)
- **Range**: 0.0 to 1.0
- **Measures**: Learned skills for role, role-specific knowledge, relevant experience
- **Updates**: Grows with successful role performance, role-relevant training
- **Context**: Qualified by role certifications and demonstrated role competence

#### Temperament (Role-Contextual Reliability)
- **Range**: 0.0 to 1.0
- **Measures**: Consistency in role, role-appropriate behavior, role ethics
- **Updates**: Improves with consistent role performance, degrades with role violations
- **Context**: Role-dependent (surgeon needs steady hands, trader needs risk tolerance)

### 2.2 T3 Tensor Structure with Role Binding

```json
{
  "t3_tensor": {
    "entity": "lct:alice",
    "role_tensors": {
      "web4:DataAnalyst": {
        "talent": 0.85,
        "training": 0.90,
        "temperament": 0.95
      },
      "web4:ProjectManager": {
        "talent": 0.65,
        "training": 0.70,
        "temperament": 0.91
      },
      "web4:Mechanic": {
        "talent": 0.20,
        "training": 0.15,
        "temperament": 0.50
      }
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

## 5. Role-Based Tensor Application

### 5.1 Role-Specific Trust Matching

Roles specify required T3 thresholds, and entities are matched based on role-specific tensors:

```json
{
  "role": "web4:Surgeon",
  "role_requirements": {
    "minimum_t3": {
      "talent": 0.7,      // High precision required
      "training": 0.9,    // Extensive medical training
      "temperament": 0.85 // Steady under pressure
    }
  },
  "candidate_evaluation": {
    "lct:alice": {
      "role_tensor": {
        "talent": 0.95,
        "training": 0.92,
        "temperament": 0.88
      },
      "qualified": true,
      "trust_score": 0.92  // Computed for THIS role
    }
  }
}
```

### 5.2 RDF Role-Tensor Binding

```turtle
# T3 tensors are bound to entity-role pairs
lct:alice web4:hasRole web4:Surgeon .
lct:alice web4:hasRole web4:Researcher .

_:tensor1 a web4:T3Tensor ;
    web4:entity lct:alice ;
    web4:role web4:Surgeon ;
    web4:talent 0.95 ;
    web4:training 0.92 ;
    web4:temperament 0.88 .

_:tensor2 a web4:T3Tensor ;
    web4:entity lct:alice ;
    web4:role web4:Researcher ;
    web4:talent 0.80 ;
    web4:training 0.85 ;
    web4:temperament 0.90 .
```

### 5.3 Role-Aware Value Pricing

ATP costs derived from role-specific V3 expectations:

```python
def calculate_atp_price(entity_id, role, task_type):
    # Get role-specific V3 tensor
    v3 = get_v3_for_role(entity_id, role)
    
    # Price depends on role-task alignment
    if not role_matches_task(role, task_type):
        return INVALID_ROLE_PRICE  # Very high or rejection
    
    # Role-appropriate pricing
    base_cost = get_role_base_cost(role)
    role_multiplier = get_role_value_multiplier(role)
    
    return base_cost * (1 + v3.valuation) * v3.veracity * v3.validity * role_multiplier
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

### 6.3 Role-Based Segregation
- No global trust scores - only role-specific tensors
- Each role maintains separate T3/V3 tensors
- New roles start with minimal trust, not inherited
- Cross-role trust transfer requires explicit bridging

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

### 8.2 Role-Aware Tensor Composition
For composite entities:
- Team T3 for role = weighted average of members' tensors FOR THAT ROLE
- Organization V3 = sum of role-appropriate contributions
- Cannot average trust across different roles
- Multi-role teams compose role-specific sub-teams

Example:
```python
def compute_team_trust(team_members, required_role):
    role_qualified = [m for m in team_members 
                      if has_role(m, required_role)]
    
    if not role_qualified:
        return NO_TRUST  # Team lacks required role
    
    # Average only among those with the role
    role_tensors = [get_t3_for_role(m, required_role) 
                    for m in role_qualified]
    return weighted_average(role_tensors)
```

### 8.3 Cross-Tensor Analytics
- Identify T3/V3 correlation patterns
- Detect anomalous tensor evolution
- Optimize for specific tensor targets

## 9. Integration with R6 and MRH

### 9.1 R6 Role-Based Updates

The R6 framework updates tensors within role contexts:

1. **Before Action**: Role-specific T3 used for confidence
2. **During Action**: Monitor performance in role context
3. **After Action**: Update tensors for performed role only
4. **As Reference**: Role-specific history informs similar roles

### 9.2 MRH Graph Integration

RDF triples in MRH explicitly track role-tensor relationships:

```sparql
# Query for best entity-role match for task
SELECT ?entity ?role ?trust WHERE {
    ?tensor web4:entity ?entity ;
            web4:role ?role ;
            web4:matchesTask ?taskType .
    
    # Calculate composite trust for role
    ?tensor web4:talent ?t ;
            web4:training ?tr ;
            web4:temperament ?tm .
    
    BIND((?t * 0.3 + ?tr * 0.4 + ?tm * 0.3) AS ?trust)
}
ORDER BY DESC(?trust)
LIMIT 1
```

This creates a continuous learning loop where every action refines role-specific capabilities, preventing trust leakage across unrelated domains.
---
**See also:** Web4 Society–Authority–Law (SAL) — normative requirements for genesis **Citizen** role, **Authority**, **Law Oracle**, **Witness/Auditor**, immutable record, MRH edges, and R6 bindings. ([sal.md](web4-society-authority-law.md), [sal.jsonld](sal.jsonld))
