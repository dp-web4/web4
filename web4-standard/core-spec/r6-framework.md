# Web4 R6 Action Framework Specification

## Overview

R6 is the **base action grammar** for Web4. ATP→ADP transactions follow this pattern for **routine, low-consequence tasks** that don't merit explicit, first-class reputation tracking — the cheap default mode. (R6 Results do include implicit tensor updates via `tensorUpdates` in §1.6; R7 adds the full reputation machinery: role-contextualized, witnessed, attributed, ledger-recorded.)

For consequential actions where the outcome should shape future trust, use [R7](r7-framework.md) — a superset of R6 that adds reputation back-propagation.

R6 and R7 are **both canonical**. The choice is contextual, selected per action or per role based on consequence tier. Neither is deprecated.

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
    "roleLCT": "lct:web4:role:analyst_financial_q4:abc123",
    "pairedAt": "2025-09-15T12:00:00Z",
    "t3InRole": {
      "talent": 0.85,
      "training": 0.90,
      "temperament": 0.88
    },
    "v3InRole": {
      "veracity": 0.92,
      "validity": 0.88,
      "value": 0.85
    }
  }
}
```

**Note**: Both T3 (trust) and V3 (value) tensors are stored on the MRH role pairing link. There is no global reputation — all reputation is role-contextualized. The `roleLCT` encodes the domain-specific context (e.g., `analyst_financial_q4`) within the LCT identifier itself.

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
- ATP (Allocation Transfer Packet) tokens
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

    # 2. Check for agency delegation if acting as agent
    if r6_action.request.get('proofOfAgency'):
        if not verify_agency_grant(r6_action.request.proofOfAgency):
            raise InvalidAgency("Invalid or expired agency grant")
        if not check_agency_scope(r6_action.request, r6_action.request.proofOfAgency):
            raise AgencyScopeViolation("Action outside delegated scope")

    # 3. Check rules compliance
    if not check_law_compliance(r6_action.rules, r6_action.request):
        raise RuleViolation("Request violates active rules")

    # 4. Verify resource availability (including agency caps)
    if not check_resources(r6_action.resource.required):
        raise InsufficientResources("Cannot fulfill resource requirements")

    # 5. Validate references
    if not verify_references(r6_action.reference):
        raise InvalidReference("Referenced precedents/witnesses invalid")

    # 6. Lock resources (escrow)
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
            sender=r6_action.role.actor,
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
        role_lct=r6_action.role.roleLCT,
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
| **Role** | Citizen role prerequisite, Authority scoping, Agency delegation | Role LCTs with permissions |
| **Request** | Must comply with society's laws, proof-of-agency for delegated actions | Quorum checks, rate limits |
| **Reference** | Law interpretations and precedents, agency grants | Oracle rulings cached |
| **Resource** | ATP caps and pricing from law, agency resource caps | Metering enforced |
| **Result** | Auditor reviews evidence; corrections are issued as a *new* corrective R6 action — the original Result stays immutable per §4.2 | Witness attestations required |

## 4. R6 Security Properties

### 4.1 Determinism
Given the same R6 inputs **and execution outcome**, the settlement (resource accounting, tensor updates, ledger entry) must be identical across all valid implementations. The determinism guarantee applies to the R6 framework's processing, not to the underlying action execution which may depend on external factors (hardware, network state, nondeterministic algorithms).

### 4.2 Non-repudiation
All R6 actions are signed and recorded on the immutable ledger with witness attestations.

### 4.3 Resource Bounds
Resource consumption cannot exceed pre-declared limits, preventing denial-of-service.

### 4.4 Role Isolation
Actions are strictly scoped to the permissions of the role under which they execute.

### 4.5 Atomic Settlement
Resource transfers and tensor updates either fully complete or fully roll back. The settlement steps in §2.3 (ATP transfer, escrow release, tensor updates, ledger write, and MRH update) execute within a single atomic boundary; the §2.3 pseudocode shows the logical sequence, not the transaction/rollback scaffolding that enforces this all-or-nothing commitment.

## 5. R6 Transaction Types

### 5.1 Simple Query
```json
{
  "type": "query",
  "rules": {"lawHash": "..."},
  "role": {"roleLCT": "lct:web4:role:reader:..."},
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
  "role": {"roleLCT": "lct:web4:role:investigator:..."},
  "request": {
    "action": "query_trust",
    "target": "lct:web4:entity:...",
    "parameters": {"requestedRole": "web4:Surgeon"},
    "atpStake": 100
  },
  "reference": {"mrhContext": {"depth": 2}},
  "resource": {"escrow": {"amount": 100}},
  "result": {
    "output": {"t3InRole": {...}, "commitment": "must_engage_or_forfeit"}
  }
}
```

### 5.3 Computational Task
```json
{
  "type": "compute",
  "rules": {"permissions": ["execute"]},
  "role": {"roleLCT": "lct:web4:role:data_scientist:..."},
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
  "role": {"roleLCT": "lct:web4:role:authority:..."},
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

### 5.5 Agency-Delegated Action (AGY)
```json
{
  "type": "agency_action",
  "rules": {"lawHash": "...", "agencyGrant": "agy:..."},
  "role": {"roleLCT": "lct:web4:role:agent:...", "actingFor": "lct:web4:client:..."},
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
    "output": {"approval": "confirmed"},
    "attribution": {
      "agent": "lct:web4:agent:...",
      "client": "lct:web4:client:...",
      "grantUsed": "agy:..."
    },
    "tensorUpdates": [
      {"entity": "lct:web4:agent:...", "t3": {"temperament": +0.01}},
      {"entity": "lct:web4:client:...", "v3": {"validity": +0.005}}
    ]
  }
}
```

**Note on multi-party tensor attribution**: Agency-delegated actions affect multiple parties. The `tensorUpdates` array uses explicit per-entity attribution with standard `t3`/`v3` keys (matching §1.6 Result format). For consequential agency actions, prefer R7's `ReputationDelta` per-party model which provides full attribution, witnessing, and ledger recording.

## 6. R6 Implementation Requirements

### MUST Requirements
1. All actions MUST follow the complete R6 structure
2. All components MUST be present (even if empty)
3. Settlement MUST be deterministic given inputs and execution outcome
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

R6 distinguishes two non-success statuses:
- **`error`**: Pre-execution validation failures — the action was never attempted (e.g., insufficient resources, invalid role, malformed request).
- **`failure`**: Execution-time errors — the action was attempted but did not succeed (e.g., runtime error, output constraint violation).

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

**SDK note**: In implementations that support both R6 and R7, the error hierarchy may use a shared base class. The SDK uses `R7Error` as the common base, since R7 is a superset of R6. A pure R6 implementation would define `R6Error` as shown above.

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
- **Deterministic** settlement (same inputs + execution outcome → same settlement)
- **Auditable** transactions (all on ledger)
- **Role-contextual** operations (no global permissions)
- **Resource-bounded** execution (no unbounded consumption)
- **Law-integrated** validation (SAL compliance built-in)

Every Web4 transaction is an R6 action, making the entire system consistent, predictable, and verifiable.

## 10. References

- [r7-framework.md](r7-framework.md) — R7 superset with explicit reputation tracking and back-propagation
- [atp-adp-cycle.md](atp-adp-cycle.md) — ATP/ADP token lifecycle, value mechanics, and conservation invariants
- [t3-v3-tensors.md](t3-v3-tensors.md) — T3 (Trust) and V3 (Value) tensor definitions and update mechanics
- [mrh-tensors.md](mrh-tensors.md) — Markov Relevancy Horizon graph structure and trust propagation
- [society-roles.md](society-roles.md) — Role definitions, tier structure, and role pairing lifecycle
- [SOCIETY_SPECIFICATION.md](SOCIETY_SPECIFICATION.md) — Society-Authority-Law (SAL) governance framework
