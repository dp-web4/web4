# Agentic Context Protocol (ACP) Integration Summary

## Overview

The Agentic Context Protocol (ACP) has been integrated into the Web4 standard, transforming Web4 from a reactive system to an agentic one. ACP enables entities to initiate actions autonomously while maintaining safety through agency delegation (AGY), law compliance (SAL), and human oversight.

## Key Concepts Added

### 1. Agentic Capability
- **From Reactive to Agentic**: Entities can now initiate actions, not just respond
- **Autonomous Planning**: Multi-step workflows with triggers and dependencies
- **Decision Making**: Choose between alternatives based on context
- **Learning**: Adjust behavior based on outcomes

### 2. Agent Plans
Declarative specifications that define:
- **Triggers**: Cron schedules, events, or manual initiation
- **Steps**: Ordered sequence of MCP resource calls
- **Guards**: Resource caps, witness requirements, approval gates
- **Expiration**: Temporal bounds on plan validity

### 3. Intent-Decision-Execution Flow
1. **Intent**: Proposed action generated from plan evaluation
2. **Decision**: Human or automated approval/denial/modification
3. **Execution**: MCP resource invocation with proof of agency
4. **Record**: Immutable ledger entry with witness attestation

### 4. Human Console
Interface for human oversight:
- Approval requests with risk assessment
- Real-time monitoring dashboards
- Audit trails and explanation
- Manual intervention capabilities

## ACP-AGY-SAL Integration

### Agency Requirements
- Every ACP action MUST have valid AGY grant
- Proof of agency included in all MCP calls
- Scope enforcement prevents unauthorized actions
- Resource caps limit potential damage

### Law Compliance
- Plans checked against Law Oracle rules
- Witness requirements per society policy
- Quorum models for critical decisions
- Audit adjustments for violations

### Trust Impact
- Agent accrues T3 for execution quality
- Client maintains V3 for value delivered
- Failed plans reduce trust scores
- Successful automation increases reputation

## Core Objects

### AgentPlan
```json
{
  "type": "ACP.AgentPlan",
  "planId": "acp:plan:...",
  "principal": "lct:web4:client",
  "agent": "lct:web4:agent",
  "grantId": "agy:grant:...",
  "triggers": [...],
  "steps": [...],
  "guards": {...}
}
```

### Intent
```json
{
  "type": "ACP.Intent",
  "intentId": "acp:intent:...",
  "planId": "acp:plan:...",
  "proposedAction": {...},
  "proofOfAgency": {...},
  "needsApproval": boolean
}
```

### Decision
```json
{
  "type": "ACP.Decision",
  "intentId": "acp:intent:...",
  "decision": "approve|deny|modify",
  "by": "lct:web4:approver",
  "witnesses": [...]
}
```

### ExecutionRecord
```json
{
  "type": "ACP.ExecutionRecord",
  "intentId": "acp:intent:...",
  "mcpCall": {...},
  "result": {...},
  "ledgerInclusion": {...}
}
```

## State Machine

```
Trigger → Plan → Intent → Law Check → Approval → Execute → Record → Audit
```

Each transition is witnessed and recorded, creating complete auditability.

## Security Model

### Multi-Layer Defense
1. **Agency Layer**: Valid grants required
2. **Law Layer**: Compliance verification
3. **Approval Layer**: Human oversight gates
4. **Witness Layer**: Multi-party attestation
5. **Audit Layer**: Post-execution review

### Threat Mitigation
- **Runaway automation**: Resource caps and rate limits
- **Unauthorized actions**: Scope enforcement
- **Malicious plans**: Law compliance checks
- **Replay attacks**: Nonces and temporal bounds
- **Trust gaming**: Audit adjustments

## MRH Graph Extensions

New RDF relationships:
```turtle
# Plan relationships
lct:plan acp:hasAgent lct:agent .
lct:plan acp:hasPrincipal lct:client .
lct:plan acp:underGrant lct:grant .

# Intent relationships  
lct:intent acp:derivedFrom lct:plan .
lct:intent acp:hasDecision lct:decision .

# Execution relationships
lct:record acp:executedBy lct:agent .
lct:record acp:witnessedBy lct:witness .
```

## Implementation Requirements

### Mandatory (MUST)
1. Valid agency grants for all actions
2. Law compliance verification
3. Witness attestation for critical actions
4. Ledger recording of execution records
5. Proof of agency in MCP calls

### Recommended (SHOULD)
1. Human approval gates for high-risk actions
2. Explanations for proposed actions
3. Risk assessment for decisions
4. Real-time monitoring dashboards
5. Complete audit trails

## Use Cases

### 1. Invoice Processing
- Automated approval for small amounts
- Human oversight for large transactions
- Budget checking and compliance
- Accounting system integration

### 2. Security Monitoring
- Continuous threat assessment
- Automated incident response
- Escalation to security team
- System isolation capabilities

### 3. Content Moderation
- AI-assisted review
- Confidence-based routing
- Policy compliance checking
- Human review queuing

### 4. Resource Management
- Dynamic allocation based on demand
- Cost optimization strategies
- Capacity planning and scaling
- Performance monitoring

## Benefits of ACP Integration

1. **Autonomous Operation**: Agents can work independently within boundaries
2. **Human Oversight**: Critical decisions remain under human control
3. **Full Auditability**: Every action is recorded and witnessed
4. **Trust Building**: Successful automation increases reputation
5. **Flexibility**: Plans can adapt to changing conditions
6. **Safety**: Multiple layers of protection against misuse

## Error Handling

Comprehensive error model:
- `W4_ERR_ACP_NO_GRANT`: No valid agency grant
- `W4_ERR_ACP_SCOPE_VIOLATION`: Outside grant scope
- `W4_ERR_ACP_APPROVAL_REQUIRED`: Needs human approval
- `W4_ERR_ACP_WITNESS_DEFICIT`: Insufficient witnesses
- `W4_ERR_ACP_PLAN_EXPIRED`: Plan has expired
- `W4_ERR_ACP_LEDGER_WRITE`: Ledger write failed

## Future Directions

- **Multi-Agent Coordination**: Complex workflows across agents
- **Adaptive Planning**: Self-improving plans
- **Predictive Triggers**: Anticipate events
- **Negotiation Protocols**: Resource negotiation
- **Federated Learning**: Cross-society knowledge sharing

## Migration Path

For existing implementations:
1. Deploy ACP control plane
2. Define initial agent plans
3. Establish approval workflows
4. Configure witness requirements
5. Enable gradual automation

## Summary

ACP completes Web4's evolution into a fully agentic system where:
- Entities can act autonomously within defined boundaries
- Every action is authorized, witnessed, and recorded
- Humans maintain oversight of critical decisions
- Trust is built through successful execution
- The system becomes more capable over time

This creates an antifragile architecture that grows stronger through use while maintaining safety and accountability.

## References

- [ACP Framework Specification](core-spec/acp-framework.md)
- [ACP Bundle](../forum/nova/ACP-bundle/)
- [AGY Integration](AGY_INTEGRATION_SUMMARY.md)
- [SAL Integration](SAL_INTEGRATION_SUMMARY.md)
- [MCP Protocol](core-spec/mcp-protocol.md)