# Agency Delegation (AGY) Integration Summary

## Overview

The Agency Delegation (AGY) layer has been integrated into the Web4 standard, providing a formal mechanism for Client entities to delegate authority to Agent entities within scoped, attestable contexts. This enables sophisticated delegation patterns while maintaining security, traceability, and accountability.

## Key Concepts Added

### 1. Agency as First-Class Relationship
- **Definition**: Special pairing/binding where Client delegates authority to Agent
- **Capabilities**: Scoped actions, resource caps, temporal bounds, witness requirements
- **Non-impersonation**: Agents act under Agency role, not Client role (unless explicitly allowed)
- **Revocable**: Immediate revocation with ledger recording

### 2. Agency Grant Structure
Every agency delegation requires:
- Client and Agent entity LCTs
- Society context and Law Oracle reference
- Scope definition (contexts, methods, MRH selectors)
- Resource caps (ATP limits, bandwidth, etc.)
- Trust caps (minimum T3/V3 requirements)
- Temporal bounds (notBefore, expiresAt)
- Witness requirements and signatures
- Delegation permissions (can agent sub-delegate?)

### 3. Proof-of-Agency Requirements
All agent-originated actions MUST include:
- Grant ID reference
- Ledger inclusion proof
- Audience binding (prevents replay)
- Nonce for session uniqueness
- Scope verification

### 4. Agent and Client Roles
New entity roles added:
- **Agent Role**: Acts on behalf of Client within constraints
- **Client Role**: Principal who delegates and maintains ultimate responsibility
- Both accumulate separate T3/V3 tensors
- Attribution tracks both Agent execution and Client principal

### 5. Agency Revocation
Formal revocation mechanism:
- Immediate effect (society law may define grace period)
- Recorded on immutable ledger
- Reason tracking for audit trail
- Witness requirements per society law

## AGY-R6 Integration

| R6 Component | AGY Enhancement |
|--------------|-----------------|
| **Rules** | Agency grants add scope-specific rules and caps |
| **Role** | Agent acts under Agency role with proof requirement |
| **Request** | Must include proof-of-agency for delegated actions |
| **Reference** | Includes grant lookups and revocation checks |
| **Resource** | Enforces both society and grant-specific caps |
| **Result** | Dual attribution to Agent and Client |

## Security Properties

### 1. Least Privilege
- Default-deny model
- Explicit scope expansion required
- Resource caps prevent runaway delegation

### 2. Non-Repudiation
- All grants signed and ledger-recorded
- Proof-of-agency creates audit trail
- Witness requirements for critical grants

### 3. Temporal Safety
- Grants have explicit expiration
- notBefore prevents premature activation
- Revocation provides immediate termination

### 4. Scope Enforcement
- MRH selectors limit action targets
- Method restrictions (create, update, approve, etc.)
- Context boundaries (finance, docs, operations)

## Implementation Requirements

### Mandatory (MUST)
1. Require proof-of-agency on all agent actions
2. Verify grant validity before execution
3. Enforce scope, caps, and temporal bounds
4. Record grants/revocations on immutable ledger
5. Check revocation status for high-risk actions

### Recommended (SHOULD)
1. Cache grant status with TTL
2. Require witness quorum ≥2 for critical grants
3. Implement grace periods for in-flight actions
4. Support delegation chains with scope inheritance

## Trust and Value Impact

### Agent T3/V3
- Builds execution quality reputation
- Scoped to specific delegation contexts
- Independent from Client reputation

### Client T3/V3
- Reduced/indirect value attribution
- Shared liability per law policy
- Maintains principal responsibility

### Auditor Oversight
- Can validate agency execution post-hoc
- Evidence must cite grant and scope
- Adjustments apply to both Agent and Client

## Use Cases

### 1. Automated Operations
Client delegates routine approvals to AI Agent with strict ATP limits and scope.

### 2. Cross-Organization Actions
Organization A's Agent acts on behalf of Organization B within agreed boundaries.

### 3. Temporary Authority
Time-bound delegation for specific project or emergency response.

### 4. Hierarchical Delegation
Delegatable grants allow sub-delegation with inherited constraints.

## MRH Graph Extensions

New RDF triples for AGY:
```turtle
@prefix web4: <https://web4.io/ontology#> .

# Agency relationships
lct:client web4:hasAgent lct:agent .
lct:agent web4:agentOf lct:client .

# Grant properties
lct:grant web4:delegationScope lct:scopeNode .
lct:grant web4:expiresAt "2025-12-31T23:59:59Z"^^xsd:dateTime .
lct:grant web4:witnessLevel 2 .

# Action attribution
lct:action web4:underGrant lct:grant .
lct:revocation web4:revokedBy lct:client .
```

## Error Codes

New AGY-specific errors:
- `W4_ERR_AGY_EXPIRED`: Grant expired
- `W4_ERR_AGY_REVOKED`: Grant revoked
- `W4_ERR_AGY_SCOPE`: Action outside scope
- `W4_ERR_AGY_WITNESS`: Witness quorum not met
- `W4_ERR_AGY_REPLAY`: Nonce/audience mismatch
- `W4_ERR_AGY_DELEGATION`: Invalid sub-delegation

## Migration Path

For existing implementations:
1. Define agency policy in Law Oracle
2. Implement proof-of-agency validation
3. Add grant/revocation ledger recording
4. Update R6 validation for agency checks
5. Enable Agent/Client role types

## Benefits of AGY Integration

1. **Formal Delegation**: Machine-verifiable authority chains
2. **Granular Control**: Fine-grained scope and resource limits
3. **Accountability**: Clear attribution and audit trails
4. **Flexibility**: Temporal, contextual, and hierarchical delegation
5. **Security**: Witness requirements, revocation, non-repudiation

## Next Steps

1. Deploy reference AGY implementation
2. Create grant management tools
3. Define standard delegation templates
4. Implement cross-society bridging
5. Build delegation analytics

## References

- [Web4 Agency Delegation Specification](../forum/nova/agency-bundle/web4-agency-delegation.md)
- [AGY JSON-LD Context](../forum/nova/agency-bundle/agy.jsonld)
- [AGY Ontology](../forum/nova/agency-bundle/agy-ontology.ttl)
- [R6 Framework Specification](core-spec/r6-framework.md)