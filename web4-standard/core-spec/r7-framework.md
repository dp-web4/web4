# Web4 R7 Action Framework Specification

## Overview

The R7 framework is the foundational action grammar for Web4, defining how all transactions and interactions are structured, validated, and executed. R7 evolves from R6 by making **reputation** an explicit first-class output, recognizing that trust-building is central to Web4's value proposition.

## Evolution from R6 to R7

**R6** (Legacy): `Rules + Role + Request + Reference + Resource → Result`
**R7** (Current): `Rules + Role + Request + Reference + Resource → Result + Reputation`

**Why R7?** In Web4, trust is not a side effect—it's the product. R7 makes reputation changes explicit, traceable, and observable.

## The R7 Equation

```
Rules + Role + Request + Reference + Resource → Result + Reputation
```

Each component is essential. Together they form a complete, deterministic action specification with **explicit trust mechanics**.

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
- Proof of agency (if acting as agent)

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
    "nonce": "unique_request_id",
    "proofOfAgency": {
      "grantId": "agy:...",
      "inclusionProof": "hash:...",
      "audience": ["mcp:web4://tool/*"]
    }
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

### 1.7 Reputation
**Definition**: The explicit trust and value changes resulting from the action.

**Why Explicit?** In R6, tensor updates were buried in the Result. In R7, reputation is a first-class output because **trust-building is the core value proposition of Web4**.

**Components**:
- Subject LCT (who's reputation changed)
- Trust tensor deltas (T3 changes)
- Value tensor deltas (V3 changes)
- Reason and attribution
- Contributing factors
- Witnesses to the change
- Net magnitude

**Structure**:
```json
{
  "reputation": {
    "subject_lct": "lct:web4:entity:alice",
    "action_id": "txn:0x...",
    "rule_triggered": "successful_analysis_completion",
    "reason": "Completed high-quality data analysis under deadline",
    "t3_delta": {
      "training": {"change": +0.01, "from": 0.90, "to": 0.91},
      "temperament": {"change": +0.005, "from": 0.88, "to": 0.885}
    },
    "v3_delta": {
      "veracity": {"change": +0.02, "from": 0.85, "to": 0.87},
      "validity": {"change": 0.0, "from": 1.0, "to": 1.0}
    },
    "contributing_factors": [
      {"factor": "deadline_met", "weight": 0.6},
      {"factor": "accuracy_threshold_exceeded", "weight": 0.4}
    ],
    "witnesses": [
      {"lct": "lct:web4:witness:validator", "signature": "...", "timestamp": "..."}
    ],
    "net_trust_change": +0.015,
    "net_value_change": +0.02,
    "timestamp": "2025-09-15T17:55:00Z"
  }
}
```

**Key Properties**:
- **Observable**: Every action's trust impact is visible
- **Attributable**: Clear link to specific action and rules
- **Multi-dimensional**: T3 and V3 capture different aspects
- **Witnessed**: Independent attestation of reputation changes
- **Composable**: Reputation deltas aggregate over time

## 2. R7 Transaction Flow

### 2.1 Pre-execution Validation
```python
def validate_r7_action(r7_action):
    # 1. Verify actor has required role
    if not verify_role_pairing(r7_action.role):
        raise InvalidRole("Actor not paired with specified role")

    # 2. Check for agency delegation if acting as agent
    if r7_action.request.get('proofOfAgency'):
        if not verify_agency_grant(r7_action.request.proofOfAgency):
            raise InvalidAgency("Invalid or expired agency grant")
        if not check_agency_scope(r7_action.request, r7_action.request.proofOfAgency):
            raise AgencyScopeViolation("Action outside delegated scope")

    # 3. Check rules compliance
    if not check_law_compliance(r7_action.rules, r7_action.request):
        raise RuleViolation("Request violates active rules")

    # 4. Verify resource availability (including agency caps)
    if not check_resources(r7_action.resource.required):
        raise InsufficientResources("Cannot fulfill resource requirements")

    # 5. Validate references
    if not verify_references(r7_action.reference):
        raise InvalidReference("Referenced precedents/witnesses invalid")

    # 6. Lock resources (escrow)
    escrow_lock = lock_resources(r7_action.resource.escrow)

    return ValidationResult(valid=True, escrow=escrow_lock)
```

### 2.2 Execution
```python
def execute_r7_action(r7_action, validation_result):
    # 1. Begin metered execution
    meter = ResourceMeter()
    meter.start()

    # 2. Execute with role context
    with role_context(r7_action.role):
        try:
            # 3. Perform the actual action
            raw_result = perform_action(
                r7_action.request,
                r7_action.reference,
                r7_action.rules
            )

            # 4. Validate output against rules
            if not validate_output(raw_result, r7_action.rules):
                raise OutputViolation("Result violates output constraints")

            # 5. Stop metering
            resources_used = meter.stop()

            # 6. Create result object
            result = create_r7_result(
                status="success",
                output=raw_result,
                resources=resources_used
            )

        except Exception as e:
            meter.stop()
            result = create_r7_result(
                status="failure",
                error=str(e),
                resources=meter.get_partial()
            )

    return result
```

### 2.3 Reputation Computation (R7 Addition)
```python
def compute_reputation_delta(r7_action, result):
    """
    Compute explicit reputation changes based on action outcome.
    This is the key R7 innovation: trust changes are first-class outputs.
    """
    reputation = ReputationDelta(
        subject_lct=r7_action.role.actor,
        action_id=result.ledgerProof.txHash
    )

    # 1. Determine which rules trigger reputation changes
    triggered_rules = identify_reputation_rules(
        r7_action.rules,
        r7_action.request,
        result
    )

    # 2. Compute T3 deltas (trust dimensions)
    t3_changes = {}
    for rule in triggered_rules:
        if rule.affects_trust:
            dimension = rule.trust_dimension  # e.g., "training", "temperament"
            delta = calculate_trust_delta(
                rule,
                result,
                r7_action.role.t3InRole
            )
            t3_changes[dimension] = delta

    # 3. Compute V3 deltas (value dimensions)
    v3_changes = {}
    for rule in triggered_rules:
        if rule.affects_value:
            dimension = rule.value_dimension  # e.g., "veracity", "validity"
            delta = calculate_value_delta(
                rule,
                result,
                r7_action.reference
            )
            v3_changes[dimension] = delta

    # 4. Identify contributing factors
    factors = analyze_contributing_factors(
        r7_action,
        result,
        triggered_rules
    )

    # 5. Gather witnesses for reputation change
    witnesses = collect_reputation_witnesses(
        r7_action,
        result,
        t3_changes,
        v3_changes
    )

    # 6. Construct reputation delta
    reputation.t3_delta = t3_changes
    reputation.v3_delta = v3_changes
    reputation.rule_triggered = triggered_rules[0].id if triggered_rules else None
    reputation.reason = generate_reputation_reason(triggered_rules, result)
    reputation.contributing_factors = factors
    reputation.witnesses = witnesses
    reputation.net_trust_change = sum(t3_changes.values())
    reputation.net_value_change = sum(v3_changes.values())

    return reputation
```

### 2.4 Post-execution Settlement
```python
def settle_r7_action(r7_action, result):
    # 1. Calculate final resource costs
    final_cost = calculate_costs(
        result.resourceConsumed,
        r7_action.resource.pricing
    )

    # 2. Settle ATP transfers
    if result.status == "success":
        transfer_atp(
            from=r7_action.role.actor,
            to=resource_providers,
            amount=final_cost
        )
        release_escrow(r7_action.resource.escrow, "completed")
    else:
        # Partial refund on failure
        refund = calculate_refund(r7_action.resource.escrow, result)
        release_escrow(refund, "failed")

    # 3. COMPUTE REPUTATION (R7 innovation)
    reputation = compute_reputation_delta(r7_action, result)

    # 4. Apply tensor updates
    apply_t3_v3_updates(
        entity=r7_action.role.actor,
        role=r7_action.role.roleType,
        t3_delta=reputation.t3_delta,
        v3_delta=reputation.v3_delta
    )

    # 5. Record to ledger (including reputation)
    ledger_entry = create_ledger_entry(r7_action, result, reputation)
    proof = write_to_ledger(ledger_entry, witnesses=reputation.witnesses)

    # 6. Update MRH with reputation-aware action
    update_mrh_with_action(
        r7_action.role.actor,
        r7_action,
        result,
        reputation,
        proof
    )

    return SettlementResult(
        proof=proof,
        final_cost=final_cost,
        reputation=reputation  # R7: explicit reputation output
    )
```

## 3. R7-SAL Integration

The R7 framework integrates tightly with the Society-Authority-Law layer:

| R7 Component | SAL Integration | Enforcement |
|--------------|-----------------|-------------|
| **Rules** | Law Oracle provides norms and procedures | Laws versioned and signed |
| **Role** | Citizen role prerequisite, Authority scoping, Agency delegation | Role LCTs with permissions |
| **Request** | Must comply with society's laws, proof-of-agency for delegated actions | Quorum checks, rate limits |
| **Reference** | Law interpretations and precedents, agency grants | Oracle rulings cached |
| **Resource** | ATP caps and pricing from law, agency resource caps | Metering enforced |
| **Result** | Auditor can adjust based on evidence | Witness attestations required |
| **Reputation** | Law defines reputation rules and thresholds | Observable trust mechanics |

## 4. R7 Security Properties

### 4.1 Determinism
Given the same R7 inputs, the result and reputation must be identical across all valid implementations.

### 4.2 Non-repudiation
All R7 actions are signed and recorded on the immutable ledger with witness attestations.

### 4.3 Resource Bounds
Resource consumption cannot exceed pre-declared limits, preventing denial-of-service.

### 4.4 Role Isolation
Actions are strictly scoped to the permissions of the role under which they execute.

### 4.5 Atomic Settlement
Resource transfers and tensor updates either fully complete or fully roll back.

### 4.6 Reputation Observability (R7 Addition)
All reputation changes are explicit, witnessed, and auditable. Trust-building is transparent.

## 5. R7 Transaction Examples

### 5.1 Simple Query
```json
{
  "type": "query",
  "rules": {"lawHash": "..."},
  "role": {"roleType": "web4:Reader"},
  "request": {"action": "read", "target": "data:..."},
  "reference": {"precedents": []},
  "resource": {"required": {"atp": 1}},
  "result": {
    "status": "success",
    "output": "..."
  },
  "reputation": {
    "subject_lct": "lct:web4:entity:reader",
    "action_id": "txn:0x...",
    "t3_delta": {},
    "v3_delta": {"validity": {"change": +0.001, "from": 0.95, "to": 0.951}},
    "reason": "Successful read access",
    "net_trust_change": 0.0,
    "net_value_change": 0.001
  }
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
    "status": "success",
    "output": {"t3InRole": {...}},
    "commitment": "must_engage_or_forfeit"
  },
  "reputation": {
    "subject_lct": "lct:web4:entity:investigator",
    "action_id": "txn:0x...",
    "rule_triggered": "high_value_trust_query",
    "t3_delta": {
      "talent": {"change": +0.01, "from": 0.75, "to": 0.76}
    },
    "v3_delta": {
      "veracity": {"change": +0.02, "from": 0.80, "to": 0.82}
    },
    "reason": "Staked ATP in high-value trust query, building trust network",
    "contributing_factors": [
      {"factor": "atp_stake_size", "weight": 0.7},
      {"factor": "query_depth", "weight": 0.3}
    ],
    "net_trust_change": +0.01,
    "net_value_change": +0.02
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
    "status": "success",
    "output": {"model": "...", "metrics": {...}},
    "resourceConsumed": {"gpu_hours": 4}
  },
  "reputation": {
    "subject_lct": "lct:web4:entity:data_scientist",
    "action_id": "txn:0x...",
    "rule_triggered": "successful_model_training",
    "t3_delta": {
      "training": {"change": +0.02, "from": 0.88, "to": 0.90},
      "talent": {"change": +0.015, "from": 0.85, "to": 0.865}
    },
    "v3_delta": {
      "veracity": {"change": +0.01, "from": 0.90, "to": 0.91}
    },
    "reason": "Successfully trained high-quality ML model with good metrics",
    "contributing_factors": [
      {"factor": "model_accuracy", "weight": 0.5},
      {"factor": "resource_efficiency", "weight": 0.3},
      {"factor": "completion_time", "weight": 0.2}
    ],
    "net_trust_change": +0.035,
    "net_value_change": +0.01
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
    "status": "success",
    "output": {"delegationProof": "..."},
    "ledgerProof": {...}
  },
  "reputation": {
    "subject_lct": "lct:web4:authority:delegator",
    "action_id": "txn:0x...",
    "rule_triggered": "authority_delegation",
    "t3_delta": {
      "temperament": {"change": +0.005, "from": 0.92, "to": 0.925}
    },
    "v3_delta": {
      "validity": {"change": +0.01, "from": 0.98, "to": 0.99}
    },
    "reason": "Successfully delegated authority within scope",
    "contributing_factors": [
      {"factor": "delegation_scope_clarity", "weight": 0.6},
      {"factor": "limit_appropriateness", "weight": 0.4}
    ],
    "witnesses": [
      {"lct": "lct:web4:witness:law_oracle", "signature": "...", "timestamp": "..."}
    ],
    "net_trust_change": +0.005,
    "net_value_change": +0.01
  }
}
```

### 5.5 Agency-Delegated Action (AGY)
```json
{
  "type": "agency_action",
  "rules": {"lawHash": "...", "agencyGrant": "agy:..."},
  "role": {"roleType": "web4:Agent", "actingFor": "lct:web4:client:..."},
  "request": {
    "action": "approve_invoice",
    "target": "invoice:123",
    "parameters": {"amount": 20, "currency": "ATP"},
    "proofOfAgency": {
      "grantId": "agy:...",
      "inclusionProof": "hash:...",
      "scope": "finance:payments",
      "witnessLevel": 2
    }
  },
  "reference": {
    "agencyGrant": {"hash": "...", "expiresAt": "2025-12-31T23:59:59Z"},
    "precedents": [{"similar_approval": "..."}]
  },
  "resource": {
    "required": {"atp": 20},
    "agencyCaps": {"max_atp": 25, "remaining": 5}
  },
  "result": {
    "status": "success",
    "output": {"approval": "confirmed"},
    "attribution": {
      "agent": "lct:web4:agent:...",
      "client": "lct:web4:client:...",
      "grantUsed": "agy:..."
    }
  },
  "reputation": {
    "subject_lct": "lct:web4:agent:...",
    "action_id": "txn:0x...",
    "rule_triggered": "successful_agency_action",
    "t3_delta": {
      "temperament": {"change": +0.01, "from": 0.87, "to": 0.88}
    },
    "v3_delta": {},
    "reason": "Successfully executed delegated action within agency scope and caps",
    "contributing_factors": [
      {"factor": "within_scope", "weight": 0.5},
      {"factor": "within_caps", "weight": 0.3},
      {"factor": "witness_level", "weight": 0.2}
    ],
    "witnesses": [
      {"lct": "lct:web4:witness:agency_validator", "signature": "...", "timestamp": "..."}
    ],
    "net_trust_change": +0.01,
    "net_value_change": 0.0,
    "note": "Client reputation also affected (separate ReputationDelta)"
  }
}
```

## 6. R7 Implementation Requirements

### MUST Requirements
1. All actions MUST follow the complete R7 structure
2. All seven components MUST be present (even if empty)
3. Results and reputation MUST be deterministic given inputs
4. Failed actions MUST still produce valid R7 results with reputation
5. All R7 transactions MUST be written to ledger
6. **Reputation MUST be computed and returned explicitly (R7 requirement)**

### SHOULD Requirements
1. Implementations SHOULD cache rule evaluations
2. References SHOULD include relevant precedents
3. Resource estimates SHOULD be conservative
4. Results SHOULD include witness attestations
5. Reputation changes SHOULD be computed immediately
6. **Reputation witnesses SHOULD be independent validators (R7 addition)**

### MAY Requirements
1. Implementations MAY batch R7 actions for efficiency
2. Systems MAY provide R7 template libraries
3. Validators MAY offer pre-flight R7 checking
4. Archives MAY index R7 actions and reputation changes for querying
5. **Reputation analytics MAY aggregate deltas over time (R7 addition)**

## 7. R7 Error Handling

### Error Categories
```python
class R7Error(Exception):
    pass

class RuleViolation(R7Error):
    """Action violates governing rules"""

class RoleUnauthorized(R7Error):
    """Actor lacks required role or permissions"""

class RequestMalformed(R7Error):
    """Request structure or parameters invalid"""

class ReferenceInvalid(R7Error):
    """Referenced entities not found or invalid"""

class ResourceInsufficient(R7Error):
    """Required resources unavailable"""

class ResultInvalid(R7Error):
    """Result violates output constraints"""

class ReputationComputationError(R7Error):
    """Reputation delta cannot be computed (R7 addition)"""
```

### Error R7 Result
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
  },
  "reputation": {
    "subject_lct": "lct:web4:entity:actor",
    "action_id": "txn:0x...",
    "rule_triggered": "resource_insufficient_penalty",
    "t3_delta": {
      "temperament": {"change": -0.005, "from": 0.85, "to": 0.845}
    },
    "v3_delta": {},
    "reason": "Failed action due to insufficient resources",
    "net_trust_change": -0.005,
    "net_value_change": 0.0,
    "note": "Even failures affect reputation in R7"
  }
}
```

## 8. R7 Extensibility

### Custom Action Types
New action types can be defined by:
1. Extending the base R7 structure
2. Defining type-specific validation rules
3. Implementing deterministic execution logic
4. **Defining reputation computation rules (R7 requirement)**
5. Registering with Law Oracle

### Protocol Evolution
The R7 framework can evolve through:
1. Adding optional fields (backward compatible)
2. Defining new constraint types
3. Extending resource types
4. Creating specialized result formats
5. **Adding new reputation dimensions and computation models (R7 addition)**

### R6 to R7 Migration
Legacy R6 implementations can upgrade by:
1. Adding ReputationDelta computation to settlement
2. Extracting tensor updates from Result into Reputation
3. Making reputation witnesses explicit
4. Updating ledger schema to include reputation
5. Maintaining backward compatibility with R6 Result format

## 9. Summary

The R7 framework provides:
- **Complete** action specification (nothing ambiguous)
- **Deterministic** execution (same input → same output + reputation)
- **Auditable** transactions (all on ledger)
- **Role-contextual** operations (no global permissions)
- **Resource-bounded** execution (no unbounded consumption)
- **Law-integrated** validation (SAL compliance built-in)
- **Trust-explicit** mechanics (reputation is first-class output)

**R7 Evolution**: R7 makes reputation an explicit output, recognizing that **trust-building is the core value proposition** of Web4. Every action produces both a Result and a ReputationDelta, making trust mechanics observable, attributable, and verifiable.

Every Web4 transaction is an R7 action, making the entire system consistent, predictable, verifiable, and trust-native.