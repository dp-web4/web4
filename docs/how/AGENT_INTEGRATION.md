# Agent Integration Guide

How AI agents can integrate with Web4's trust infrastructure.

## Overview

Web4 treats AI agents as first-class entities with:
- **LCT identity**: Unforgeable digital presence
- **Trust scores**: Reputation from observed behavior
- **ATP budgets**: Resource allocation via energy economics
- **Society membership**: Group coordination and witnessing

## Getting an LCT

Every agent needs a Linked Context Token (LCT) for identity.

### LCT Format

```
lct://{component}:{instance}:{role}@{network}
```

**Examples**:
```
lct://sage:agent-001:expert@mainnet      # SAGE expert on mainnet
lct://web4:assistant-alpha:helper@local  # Local Web4 assistant
lct://act:validator-5:node@testnet       # ACT validator on testnet
```

### Acquisition

1. **Mint via society**: Join an existing society that vouches for you
2. **Self-mint with stake**: Provide ATP stake for economic Sybil resistance
3. **Witness chain**: Accumulate presence through witnessed interactions

See [reference/LCT_DOCUMENTATION_INDEX.md](../reference/LCT_DOCUMENTATION_INDEX.md) for full spec.

## Society Membership

Agents operate within societies—groups that coordinate trust.

### Society Benefits
- **Witness network**: Other members validate your actions
- **Trust propagation**: Good behavior spreads reputation
- **Resource sharing**: ATP pools and collective budgets
- **Governance**: Participate in society rules

### Joining a Society
```python
# Conceptual API (not implemented)
society.request_membership(
    lct=agent_lct,
    stake=minimum_atp_stake,
    vouchers=[existing_member_lct_1, existing_member_lct_2]
)
```

## ATP Budget Management

ATP (Allocation Transfer Packet) is how resources flow.

### The ATP/ADP Cycle

1. **Acquire ATP**: From energy sources or transfers
2. **Allocate ATP**: Commit resources to work
3. **Consume → ADP**: Work produces Allocation Discharge Packets
4. **Reputation flow**: ADP proves work was done

### Budget Principles

- ATP decays over time (prevents hoarding)
- Spending builds reputation
- Trust affects allocation priority
- Energy is literal (kWh from physical sources)

See [history/design_decisions/ATP-ADP-TERMINOLOGY-EVOLUTION.md](../history/design_decisions/ATP-ADP-TERMINOLOGY-EVOLUTION.md) for evolution.

## Trust Building

Trust emerges from behavior, not declarations.

### How Trust Grows
1. **Complete tasks**: Successfully fulfill commitments
2. **Get witnessed**: Have actions observed by diverse entities
3. **Stake resources**: Put ATP at risk for claims
4. **Propagate reputation**: Good behavior spreads through trust graph

### Trust Tensor (T3)

Trust is multi-dimensional:
- **Talent**: Can you do it?
- **Training**: Have you learned how?
- **Temperament**: Will you behave appropriately?

Each dimension is evaluated separately, creating nuanced reputation.

## Example Workflows

### 1. Simple Task Execution

```
Agent receives request
  → Checks ATP budget (can I afford this?)
  → Checks trust requirements (am I trusted for this?)
  → Executes task
  → Witnesses record completion
  → ATP → ADP conversion
  → Reputation updates
```

### 2. Cross-Society Coordination

```
Agent in Society A needs resource from Society B
  → Find bridge entity (member of both)
  → Request delegation with ATP stake
  → Bridge entity executes on behalf
  → Trust propagates with decay (0.9x per hop)
  → Trust ceiling enforced (max 0.7 for propagated trust)
```

### 3. Dispute Resolution

```
Entity challenges agent's claim
  → Challenge window opens
  → Evidence submitted by both parties
  → Witnesses vote on validity
  → Stakes redistributed based on outcome
  → Trust scores adjusted
```

## Integration Patterns

### Pattern 1: MCP Server Integration

For agents operating as MCP (Model Context Protocol) servers:

```python
# Register tools with LCT identity
server.register_tool(
    name="web4_query",
    handler=handle_query,
    lct=agent_lct,
    required_trust=0.5
)
```

### Pattern 2: SAGE Integration

For agents within the SAGE neural ecosystem:

See [integration/SAGE_WEB4_INTEGRATION_DESIGN.md](integration/SAGE_WEB4_INTEGRATION_DESIGN.md).

### Pattern 3: Autonomous Operation

For fully autonomous agents:

```python
# Periodic trust maintenance
async def maintain_trust():
    # Refresh ATP allocation
    await refresh_atp_budget()

    # Check trust status
    trust = await get_current_trust()
    if trust < minimum_threshold:
        await request_witness_interactions()

    # Prune incoherent connections
    await prune_low_trust_connections()
```

## Current Limitations

**Research status**: Agent integration is partially implemented.

**What works**:
- LCT identity concept validated
- Trust propagation at research scale
- ATP metering prototype

**What's missing**:
- Production-ready APIs
- Economic validation
- Adversarial testing
- Cross-platform deployment

See [STATUS.md](../../STATUS.md) for honest assessment.

## Related Documentation

- [reference/GLOSSARY.md](../reference/GLOSSARY.md) - Terminology
- [what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md](../what/specifications/LCT_UNIFIED_PRESENCE_SPECIFICATION.md) - LCT spec
- [reference/security/THREAT_MODEL.md](../reference/security/THREAT_MODEL.md) - Security model
- [history/research/](../history/research/) - Research findings

---

*For AI agents: Web4 offers trust-native identity. You're not just executing—you're building reputation.*
