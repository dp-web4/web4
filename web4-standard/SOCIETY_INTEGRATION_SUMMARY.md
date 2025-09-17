# Society Integration Summary

## Overview

**Societies** are now a foundational Web4 concept, representing self-governing collectives of LCT-bearing entities that maintain shared laws, ledgers, and economies. This integration establishes societies as the organizing principle for digital entities in Web4.

## Date Added: January 17, 2025

## Key Concepts

### 1. Society Definition
A society is a collective with:
- **Law Oracle**: Codified governance rules
- **Ledger**: Immutable event record
- **Treasury**: Shared ATP/ADP token pool
- **Society LCT**: The society's own identity token

### 2. Citizenship
- Witnessed relationship between entity and society
- Multi-society citizenship allowed (fractal citizenship)
- Rights and obligations defined by society laws
- Recorded immutably on society ledger

### 3. Fractal Nature
Societies can be citizens of other societies:
```
Global Society
  └── Regional Society (citizen)
        └── Local Society (citizen)
              └── Team Society (citizen)
```

This creates:
- Law inheritance chains
- Trust propagation paths
- Economic flow hierarchies
- Recursive citizenship relationships

### 4. Ledger Types

#### Confined Ledger
- Access: Citizens only
- Use: Private societies, teams
- Trust: Internal consensus

#### Witnessed Ledger
- Access: Citizens + external witnesses
- Use: Semi-public societies
- Trust: External verification

#### Participatory Ledger
- Access: Via parent society ledger
- Use: Subsidiary societies
- Trust: Inherited from parent

### 5. Amendment Mechanism
All ledgers must support law-driven amendments that:
- Preserve original entries
- Record amendments with context
- Maintain complete provenance chains
- Never delete, only supersede

## Integration Points

### With LCTs
- Every society has a society LCT
- Citizens identified by their LCTs
- Trust relationships via LCT witnessing

### With ATP/ADP Economy
- Societies manage token pools
- Citizens request ATP allocations
- Energy flows follow citizenship paths
- Economic rights defined in laws

### With SAL Framework
- Societies implement the "S" in SAL
- Law oracles codify society rules
- Authority delegation within societies
- Birth certificates for new citizens

### With MRH
- Society boundaries are MRH horizons
- Relevance propagates through citizenship
- Trust decays across society boundaries

## Implementation Examples

### Minimal Society
```json
{
  "society_lct": "lct-society-dev-team-123",
  "citizens": ["lct-alice", "lct-bob"],
  "laws": ["all_decisions_unanimous"],
  "ledger_type": "confined",
  "treasury": {"ADP": 0, "ATP": 0}
}
```

### Complex Society
```json
{
  "society_lct": "lct-society-global-web4",
  "citizens": ["lct-society-regional-1", "lct-society-regional-2"],
  "laws": ["governance_protocol_v3", "economic_policy_v2"],
  "ledger_type": "participatory",
  "treasury": {"ADP": 1000000, "ATP": 500000},
  "parent_society": null,
  "child_societies": ["lct-society-regional-1", "lct-society-regional-2"]
}
```

## Benefits

1. **Natural Organization**: Entities self-organize into purposeful collectives
2. **Scalable Governance**: From 2-entity teams to global federations
3. **Economic Alignment**: Shared pools prevent individual accumulation
4. **Trust Building**: Society-level trust tensors from collective behavior
5. **Flexible Structure**: Fractal hierarchies adapt to any scale

## Use Cases

### Development Teams
- Shared code standards (laws)
- PR/merge history (ledger)
- Feature bounties (ATP allocation)

### Trade Networks
- Trade agreements (laws)
- Transaction records (ledger)
- Settlement tokens (ATP/ADP)

### AI Swarms
- Coordination protocols (laws)
- Task completion logs (ledger)
- Energy distribution (ATP pools)

### Physical Communities
- Local regulations (laws)
- Citizenship records (ledger)
- Resource sharing (ATP economy)

## Migration Path

For existing Web4 implementations:
1. Identify natural entity groupings
2. Define minimal laws for each group
3. Initialize confined ledgers
4. Record existing relationships as citizenship
5. Migrate resource pools to society treasuries
6. Enable fractal relationships as needed

## Future Considerations

- **Treaties**: Inter-society agreements
- **Mergers**: Society combination protocols
- **Splits**: Forking mechanisms
- **Disputes**: Cross-society arbitration
- **Migration**: Citizenship portability

## Conclusion

Societies provide the missing organizational layer in Web4, transforming loose entity relationships into structured, self-governing collectives. Combined with LCTs for identity, ATP for economy, and fractals for scale, societies complete the Web4 vision of trust-native distributed intelligence.

*"From individual sovereignty to collective intelligence - societies are how Web4 entities become more than the sum of their parts."*