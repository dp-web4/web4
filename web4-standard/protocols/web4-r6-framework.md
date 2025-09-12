# Web4 R6 Action Framework

This document specifies the R6 Action Framework, a suggested mechanism for initiating, tracking, and evaluating interactions between Web4 entities. While Web4 is not restrictive of entity interactions, R6 provides a structured approach for transforming intent into accountable action.

## 1. Overview

The R6 Framework transforms every action—from simple queries to complex governance decisions—into a transparent, trackable process through six essential components:

**Rules + Role + Request + Reference + Resource → Result**

This creates accountability, enables learning, and allows for systematic improvement of both entities and the system itself.

## 2. The Six Components

### 2.1 Rules
The systemic boundaries and protocols that define what's possible:
- Smart contracts and governance protocols
- Permission boundaries from LCTs
- Contextual constraints from MRH
- Not external enforcement but inherent structure

### 2.2 Role
The operational identity for this specific action:
- Which Role LCT is being performed
- Associated permissions and responsibilities
- Contextual capabilities (T3 tensor state)
- Not global identity but contextual function

### 2.3 Request
The heart of intent—what the entity desires to achieve:
- Explicit action specification
- Acceptance criteria and quality thresholds
- Priority indicators and deadlines
- Success metrics for evaluation

### 2.4 Reference
The temporal context from past interactions:
- Historical patterns from similar requests
- Accumulated wisdom from MRH
- Previous Results that inform approach
- Memory as active participant, not passive storage

### 2.5 Resource
The energy and assets required for manifestation:
- ATP tokens for energy accounting
- Computational resources needed
- Access to data or services
- Not just consumed but invested with expected returns

### 2.6 Result
The outcome that emerges from action:
- Actual output produced
- Performance metrics achieved
- Value created (V3 assessment)
- Becomes Reference for future actions

## 3. R6 Transaction Format

### 3.1 R6 Action Structure

```json
{
  "r6_action": {
    "action_id": "r6:web4:mb32...",
    "timestamp": "2025-01-11T15:00:00Z",
    "initiator_lct": "lct:web4:agent:...",
    "status": "pending|executing|completed|failed",
    
    "rules": {
      "governing_contracts": ["contract_id_1", "contract_id_2"],
      "permission_scope": ["read:data", "write:results"],
      "constraints": {
        "max_atp_spend": 100,
        "timeout_seconds": 3600,
        "quality_threshold": 0.8
      }
    },
    
    "role": {
      "role_lct": "lct:web4:role:...",
      "role_context": "data-analyst",
      "delegated_permissions": ["analyze", "report"],
      "t3_snapshot": {
        "talent": 0.7,
        "training": 0.85,
        "temperament": 0.9
      }
    },
    
    "request": {
      "action_type": "analyze|compute|verify|delegate",
      "description": "Natural language intent",
      "acceptance_criteria": [
        "Output format specification",
        "Quality requirements",
        "Completeness conditions"
      ],
      "priority": "low|medium|high|critical",
      "deadline": "ISO-8601"
    },
    
    "reference": {
      "similar_actions": ["r6:web4:previous1", "r6:web4:previous2"],
      "success_patterns": {
        "approach": "methodology from past successes",
        "average_confidence": 0.85
      },
      "relevant_memory": ["memory_lct_1", "memory_lct_2"],
      "mrh_context": {
        "depth": 2,
        "relevant_entities": ["lct:web4:..."]
      }
    },
    
    "resource": {
      "atp_allocated": 50,
      "atp_consumed": 0,
      "compute_units": 1000,
      "data_access": ["resource_lct_1", "resource_lct_2"],
      "estimated_cost": {
        "atp": 45,
        "time": 1800
      }
    },
    
    "result": {
      "output": "Actual result data or reference",
      "performance": {
        "completion_time": 1650,
        "quality_score": 0.92,
        "criteria_met": ["criterion_1", "criterion_2"]
      },
      "value_created": {
        "v3_assessment": {
          "valuation": 0.9,
          "veracity": 0.95,
          "validity": 1.0
        },
        "atp_earned": 55
      },
      "side_effects": ["Updated cache", "Trained model"],
      "witness_attestations": [
        {
          "witness_lct": "lct:web4:oracle:...",
          "attestation_type": "quality",
          "signature": "cose:..."
        }
      ]
    }
  }
}
```

### 3.2 Confidence Calculation

Before execution, confidence is calculated based on:

```json
{
  "confidence_assessment": {
    "role_capability": 0.8,      // From Role's T3 tensor
    "historical_success": 0.75,  // From Reference patterns
    "resource_availability": 1.0, // Can afford the attempt
    "risk_assessment": 0.9,      // Cost of failure analysis
    "overall_confidence": 0.86   // Weighted average
  }
}
```

## 4. T3/V3 Tensor Evolution

### 4.1 T3 Updates from R6 Actions

The T3 tensor evolves based on R6 performance:

#### Talent Evolution
- Successful novel approaches increase Talent score
- Creative problem-solving in edge cases
- Innovation beyond Reference patterns

```json
"talent_update": {
  "previous": 0.7,
  "delta": 0.02,  // Novel solution bonus
  "new": 0.72,
  "reason": "Innovative approach to complex problem"
}
```

#### Training Evolution
- Successful completion within domain increases Training
- Learning from new References
- Accumulating domain expertise

```json
"training_update": {
  "previous": 0.85,
  "delta": 0.01,  // Domain expertise gain
  "new": 0.86,
  "reason": "Successfully completed 10th similar action"
}
```

#### Temperament Evolution
- Consistent reliability improves Temperament
- Meeting deadlines and quality thresholds
- Appropriate confidence calibration

```json
"temperament_update": {
  "previous": 0.9,
  "delta": -0.05,  // Penalty for overconfidence
  "new": 0.85,
  "reason": "Confidence exceeded actual performance"
}
```

### 4.2 V3 Updates from R6 Results

The V3 tensor captures value creation:

#### Valuation Assessment
- Subjective worth to the recipient
- Measured by ATP willing to pay
- Feedback from beneficiaries

#### Veracity Verification
- Objective accuracy of results
- External validation by witnesses
- Reproducibility of outcomes

#### Validity Confirmation
- Actual transfer of value
- ATP/ADP cycle completion
- Witness attestations

```json
"v3_update": {
  "action_id": "r6:web4:...",
  "valuation": 0.9,   // Recipient highly valued
  "veracity": 0.95,   // Independently verified
  "validity": 1.0,    // Value transfer confirmed
  "atp_impact": {
    "spent": 45,
    "earned": 55,
    "net_gain": 10
  }
}
```

## 5. Action Lifecycle

### 5.1 Initiation Phase
1. Entity forms intent (Request)
2. Checks Role permissions (Role + Rules)
3. Gathers historical context (Reference)
4. Assesses available Resources
5. Calculates confidence
6. Commits to action if confidence exceeds threshold

### 5.2 Execution Phase
1. ATP tokens locked (Resource commitment)
2. Action performed according to Request
3. Real-time monitoring against constraints
4. Witness observations recorded
5. Progress updates to interested parties

### 5.3 Completion Phase
1. Result produced and validated
2. V3 assessment by recipients
3. ATP/ADP settlement
4. T3 tensor updates calculated
5. Action archived as future Reference
6. Witness attestations finalized

## 6. Composability

R6 actions are composable building blocks:

### 6.1 Action Chains
Results become Resources for subsequent actions:
```
R6_Action_1.Result → R6_Action_2.Resource
```

### 6.2 Parallel Execution
Multiple R6 actions share Resources within Role permissions:
```
Role.permissions → [R6_Action_1, R6_Action_2, R6_Action_3]
```

### 6.3 Hierarchical Decomposition
Complex actions decompose into simpler R6 primitives:
```
Complex_Goal → [R6_Subtask_1, R6_Subtask_2, ...]
```

## 7. Integration with Core Web4

### 7.1 LCT Integration
- Every R6 action is recorded in participating LCTs
- Action history affects reputation
- Performance impacts future opportunities

### 7.2 MRH Integration
- References drawn from MRH context
- Results propagate through relevancy horizon
- Witness attestations from MRH entities

### 7.3 ATP/ADP Integration
- Resources tracked through ATP consumption
- Value creation generates new ATP
- Energy-value cycle made transparent

## 8. Implementation Requirements

### 8.1 Mandatory Features
Implementations MUST:
- Record complete R6 tuples for all actions
- Calculate confidence before execution
- Update T3/V3 tensors based on performance
- Enable witness attestation
- Archive Results as References

### 8.2 Optional Features
Implementations MAY:
- Provide action recommendation based on References
- Optimize Resource allocation
- Predict success probability
- Suggest action decomposition

## 9. Security Considerations

### 9.1 Action Integrity
- All R6 components must be cryptographically signed
- Tampering with any component invalidates action
- Witness attestations provide external validation

### 9.2 Resource Protection
- ATP must be locked before execution
- Failure conditions must be clearly defined
- Rollback mechanisms for failed actions

## 10. Privacy Considerations

- Request details may be encrypted
- Reference patterns can be anonymized
- Results can be selectively disclosed
- Witness attestations respect privacy boundaries