# Web4 R6 Action Framework Specification

## Overview

The R6 framework is the foundational action grammar for Web4, defining how all transactions and interactions are structured, validated, and executed. Every action in Web4 follows the R6 pattern, ensuring consistency, auditability, and verifiable outcomes.

## The R6 Equation

```
Rules + Role + Request + Reference + Resource → Result
```

Each component is essential and together they form a complete, deterministic action specification.

## 1. Core Components

### 1.1 Rules
**Definition**: The governing constraints and policies that apply to the action.

**Sources**:
- Law Oracle norms and procedures (SAL layer)
- Smart contracts and protocol rules
- Role-specific permissions and limitations
- Society-specific governance policies

**Structure**:
```json
{
  "rules": {
    "lawHash": "sha256:...",
    "society": "lct:web4:society:...",
    "constraints": [
      {"type": "rate_limit", "value": "100/hour"},
      {"type": "atp_minimum", "value": 50},
      {"type": "witness_required", "value": 3}
    ],
    "permissions": ["read", "write", "delegate"],
    "prohibitions": ["delete", "impersonate"]
  }
}
```

### 1.2 Role
**Definition**: The contextual identity under which the action is performed.

**Requirements**:
- Must be a valid role pairing in the actor's MRH
- Citizen role is prerequisite for all other roles
- Role must have necessary permissions for the request

**Structure**:
```json
{
  "role": {
    "actor": "lct:web4:entity:alice",
    "roleType": "web4:DataAnalyst",
    "roleLCT": "lct:web4:role:analyst:...",
    "pairedAt": "2025-09-15T12:00:00Z",
    "scopeContext": "financial_analysis",
    "t3InRole": {
      "talent": 0.85,
      "training": 0.90,
      "temperament": 0.88
    }
  }
}
```

### 1.3 Request
**Definition**: The specific action intent and parameters.

**Components**:
- Action type (verb)
- Target entity or resource
- Parameters and modifiers
- Temporal constraints

**Structure**:
```json
{
  "request": {
    "action": "analyze_dataset",
    "target": "resource:web4:dataset:...",
    "parameters": {
      "algorithm": "neural_net_v2",
      "confidence_threshold": 0.95,
      "output_format": "json"
    },
    "constraints": {
      "deadline": "2025-09-15T18:00:00Z",
      "max_compute": "1000_units"
    },
    "atpStake": 100,
    "nonce": "unique_request_id"
  }
}
```

### 1.4 Reference
**Definition**: Historical context and precedents that inform the action.

**Sources**:
- MRH graph relationships
- Previous similar actions
- Law Oracle interpretations
- Witness attestations

**Structure**:
```json
{
  "reference": {
    "precedents": [
      {"actionHash": "sha256:...", "outcome": "success", "relevance": 0.9}
    ],
    "mrhContext": {
      "depth": 2,
      "relevantEntities": ["lct:web4:...", "lct:web4:..."],
      "trustPaths": [...]
    },
    "interpretations": [
      {"lawOracle": "lct:web4:oracle:...", "ruling": "permitted", "hash": "..."}
    ],
    "witnesses": [
      {"lct": "lct:web4:witness:...", "attestation": "verified", "timestamp": "..."}
    ]
  }
}
```

### 1.5 Resource
**Definition**: The computational, economic, and material resources required.

**Types**:
- ATP (Alignment Transfer Protocol) tokens
- Computational units (CPU, memory, storage)
- Network bandwidth
- External service quotas
- Physical resources (for IoT/hardware entities)

**Structure**:
```json
{
  "resource": {
    "required": {
      "atp": 100,
      "compute": {"cpu": "2_cores", "memory": "4GB", "duration": "300s"},
      "bandwidth": "10Mbps",
      "storage": "1GB"
    },
    "available": {
      "atp_balance": 500,
      "compute_quota": "unlimited",
      "bandwidth_quota": "100Mbps"
    },
    "pricing": {
      "atp_per_compute": 0.1,
      "surge_multiplier": 1.0
    },
    "escrow": {
      "amount": 100,
      "release_condition": "result_verified"
    }
  }
}
```

### 1.6 Result
**Definition**: The deterministic outcome of the action execution.

**Components**:
- Success/failure status
- Output data or error details
- Resource consumption actual
- Tensor updates (T3/V3)
- Witness attestations
- Ledger proof

**Structure**:
```json
{
  "result": {
    "status": "success",
    "output": {
      "data": "...",
      "hash": "sha256:...",
      "format": "json"
    },
    "resourceConsumed": {
      "atp": 95,
      "compute": {"cpu_seconds": 285, "memory_peak": "3.8GB"}
    },
    "tensorUpdates": {
      "t3": {"training": +0.01},
      "v3": {"veracity": +0.02, "validity": 1.0}
    },
    "attestations": [
      {"witness": "lct:web4:...", "signature": "...", "timestamp": "..."}
    ],
    "ledgerProof": {
      "txHash": "0x...",
      "blockHeight": 12345,
      "inclusionProof": "..."
    }
  }
}
```

## 2. R6 Transaction Flow

### 2.1 Pre-execution Validation
```python
def validate_r6_action(r6_action):
    # 1. Verify actor has required role
    if not verify_role_pairing(r6_action.role):
        raise InvalidRole("Actor not paired with specified role")
    
    # 2. Check rules compliance
    if not check_law_compliance(r6_action.rules, r6_action.request):
        raise RuleViolation("Request violates active rules")
    
    # 3. Verify resource availability
    if not check_resources(r6_action.resource.required):
        raise InsufficientResources("Cannot fulfill resource requirements")
    
    # 4. Validate references
    if not verify_references(r6_action.reference):
        raise InvalidReference("Referenced precedents/witnesses invalid")
    
    # 5. Lock resources (escrow)
    escrow_lock = lock_resources(r6_action.resource.escrow)
    
    return ValidationResult(valid=True, escrow=escrow_lock)
```

### 2.2 Execution
```python
def execute_r6_action(r6_action, validation_result):
    # 1. Begin metered execution
    meter = ResourceMeter()
    meter.start()
    
    # 2. Execute with role context
    with role_context(r6_action.role):
        try:
            # 3. Perform the actual action
            raw_result = perform_action(
                r6_action.request,
                r6_action.reference,
                r6_action.rules
            )
            
            # 4. Validate output against rules
            if not validate_output(raw_result, r6_action.rules):
                raise OutputViolation("Result violates output constraints")
            
            # 5. Stop metering
            resources_used = meter.stop()
            
            # 6. Create result object
            result = create_r6_result(
                status="success",
                output=raw_result,
                resources=resources_used
            )
            
        except Exception as e:
            meter.stop()
            result = create_r6_result(
                status="failure",
                error=str(e),
                resources=meter.get_partial()
            )
    
    return result
```

### 2.3 Post-execution Settlement
```python
def settle_r6_action(r6_action, result):
    # 1. Calculate final resource costs
    final_cost = calculate_costs(
        result.resourceConsumed,
        r6_action.resource.pricing
    )
    
    # 2. Settle ATP transfers
    if result.status == "success":
        transfer_atp(
            from=r6_action.role.actor,
            to=resource_providers,
            amount=final_cost
        )
        release_escrow(r6_action.resource.escrow, "completed")
    else:
        # Partial refund on failure
        refund = calculate_refund(r6_action.resource.escrow, result)
        release_escrow(refund, "failed")
    
    # 3. Update tensors
    update_t3_v3_tensors(
        entity=r6_action.role.actor,
        role=r6_action.role.roleType,
        updates=result.tensorUpdates
    )
    
    # 4. Record to ledger
    ledger_entry = create_ledger_entry(r6_action, result)
    proof = write_to_ledger(ledger_entry, witnesses=get_witnesses())
    
    # 5. Update MRH
    update_mrh_with_action(
        r6_action.role.actor,
        r6_action,
        result,
        proof
    )
    
    return SettlementResult(proof=proof, final_cost=final_cost)
```

## 3. R6-SAL Integration

The R6 framework integrates tightly with the Society-Authority-Law layer:

| R6 Component | SAL Integration | Enforcement |
|--------------|-----------------|-------------|
| **Rules** | Law Oracle provides norms and procedures | Laws versioned and signed |
| **Role** | Citizen role prerequisite, Authority scoping | Role LCTs with permissions |
| **Request** | Must comply with society's laws | Quorum checks, rate limits |
| **Reference** | Law interpretations and precedents | Oracle rulings cached |
| **Resource** | ATP caps and pricing from law | Metering enforced |
| **Result** | Auditor can adjust based on evidence | Witness attestations required |

## 4. R6 Security Properties

### 4.1 Determinism
Given the same R6 inputs, the result must be identical across all valid implementations.

### 4.2 Non-repudiation
All R6 actions are signed and recorded on the immutable ledger with witness attestations.

### 4.3 Resource Bounds
Resource consumption cannot exceed pre-declared limits, preventing denial-of-service.

### 4.4 Role Isolation
Actions are strictly scoped to the permissions of the role under which they execute.

### 4.5 Atomic Settlement
Resource transfers and tensor updates either fully complete or fully roll back.

## 5. R6 Transaction Types

### 5.1 Simple Query
```json
{
  "type": "query",
  "rules": {"lawHash": "..."},
  "role": {"roleType": "web4:Reader"},
  "request": {"action": "read", "target": "data:..."},
  "reference": {"precedents": []},
  "resource": {"required": {"atp": 1}},
  "result": {"output": "..."}
}
```

### 5.2 Trust Query (ATP-staked)
```json
{
  "type": "trust_query",
  "rules": {"constraints": [{"type": "atp_minimum", "value": 100}]},
  "role": {"roleType": "web4:Investigator"},
  "request": {
    "action": "query_trust",
    "target": "lct:web4:entity:...",
    "parameters": {"requestedRole": "web4:Surgeon"},
    "atpStake": 100
  },
  "reference": {"mrhContext": {"depth": 2}},
  "resource": {"escrow": {"amount": 100}},
  "result": {
    "output": {"t3InRole": {...}},
    "commitment": "must_engage_or_forfeit"
  }
}
```

### 5.3 Computational Task
```json
{
  "type": "compute",
  "rules": {"permissions": ["execute"]},
  "role": {"roleType": "web4:DataScientist"},
  "request": {
    "action": "train_model",
    "parameters": {"dataset": "...", "algorithm": "..."}
  },
  "reference": {"precedents": [...]},
  "resource": {
    "required": {"compute": {"gpu": "4xA100", "duration": "3600s"}}
  },
  "result": {
    "output": {"model": "...", "metrics": {...}},
    "resourceConsumed": {"gpu_hours": 4}
  }
}
```

### 5.4 Authority Delegation
```json
{
  "type": "delegation",
  "rules": {"lawHash": "...", "society": "..."},
  "role": {"roleType": "web4:Authority"},
  "request": {
    "action": "delegate",
    "target": "lct:web4:subauthority:...",
    "parameters": {"scope": "finance", "limits": {...}}
  },
  "reference": {"lawOracle": "..."},
  "resource": {"required": {"atp": 0}},
  "result": {
    "output": {"delegationProof": "..."},
    "ledgerProof": {...}
  }
}
```

## 6. R6 Implementation Requirements

### MUST Requirements
1. All actions MUST follow the complete R6 structure
2. All components MUST be present (even if empty)
3. Results MUST be deterministic given inputs
4. Failed actions MUST still produce valid R6 results
5. All R6 transactions MUST be written to ledger

### SHOULD Requirements
1. Implementations SHOULD cache rule evaluations
2. References SHOULD include relevant precedents
3. Resource estimates SHOULD be conservative
4. Results SHOULD include witness attestations
5. Tensor updates SHOULD be calculated immediately

### MAY Requirements
1. Implementations MAY batch R6 actions for efficiency
2. Systems MAY provide R6 template libraries
3. Validators MAY offer pre-flight R6 checking
4. Archives MAY index R6 actions for querying

## 7. R6 Error Handling

### Error Categories
```python
class R6Error(Exception):
    pass

class RuleViolation(R6Error):
    """Action violates governing rules"""
    
class RoleUnauthorized(R6Error):
    """Actor lacks required role or permissions"""
    
class RequestMalformed(R6Error):
    """Request structure or parameters invalid"""
    
class ReferenceInvalid(R6Error):
    """Referenced entities not found or invalid"""
    
class ResourceInsufficient(R6Error):
    """Required resources unavailable"""
    
class ResultInvalid(R6Error):
    """Result violates output constraints"""
```

### Error R6 Result
```json
{
  "result": {
    "status": "error",
    "error": {
      "type": "ResourceInsufficient",
      "message": "Insufficient ATP balance",
      "details": {
        "required": 100,
        "available": 50
      }
    },
    "resourceConsumed": {
      "atp": 0
    },
    "refund": {
      "amount": 100,
      "status": "completed"
    }
  }
}
```

## 8. R6 Extensibility

### Custom Action Types
New action types can be defined by:
1. Extending the base R6 structure
2. Defining type-specific validation rules
3. Implementing deterministic execution logic
4. Registering with Law Oracle

### Protocol Evolution
The R6 framework can evolve through:
1. Adding optional fields (backward compatible)
2. Defining new constraint types
3. Extending resource types
4. Creating specialized result formats

## 9. Summary

The R6 framework provides:
- **Complete** action specification (nothing ambiguous)
- **Deterministic** execution (same input → same output)
- **Auditable** transactions (all on ledger)
- **Role-contextual** operations (no global permissions)
- **Resource-bounded** execution (no unbounded consumption)
- **Law-integrated** validation (SAL compliance built-in)

Every Web4 transaction is an R6 action, making the entire system consistent, predictable, and verifiable.