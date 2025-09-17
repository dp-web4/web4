# ATP/ADP Implementation Insights from ACT Blockchain

## Date: January 17, 2025
## Source: ACT (Agentic Context Tool) - Web4 Sandbox Implementation

## Key Discovery: Society Token Pool Architecture

### Conceptual Shift
The initial implementation incorrectly assumed individual entity balances. Through discussion and correction, we discovered the fundamental Web4 principle:

**All tokens belong to the society, not individuals.**

This isn't just a technical detail—it's foundational to Web4's economic philosophy.

### Implementation Pattern
```
Society Pool (not individual wallets)
├── Total ADP tokens (discharged state)
├── Total ATP tokens (charged state)
├── Allocation requests from LCT entities
└── Value distribution to all members
```

## Semifungible Token Mechanics

### State Transitions Require Real Resources
- **ADP → ATP**: Requires actual energy input from producers
- **ATP → ADP**: Occurs during work execution
- States are distinct, not interchangeable

### Implementation Details
```protobuf
// Energy producer converts ADP to ATP
message MsgRechargeADP {
  string lct_id = 1;           // Producer entity
  string amount = 2;            // ADP to convert
  string energy_source = 3;     // solar/wind/nuclear/etc
  string validation_proof = 4;  // Proof of real energy
}

// Worker converts ATP to ADP during task
message MsgDischargeATP {
  string lct_id = 1;            // Worker entity
  string amount = 2;            // ATP to use
  string work_description = 3;  // Task being performed
  string target_lct = 4;        // Work beneficiary
}
```

## Energy Producer Validation

### Discovered Requirements
Energy producers must prove actual energy generation:
- Solar panels: Wattage output verification
- Wind turbines: Generation metrics
- Grid connections: Metered input
- Batteries: Discharge verification

This prevents "phantom charging" where ADP→ATP conversion happens without real energy input.

## Value Creation Formula

### Critical Insight
```
ATP_in - ADP_out = Confirmed_Value + Energy_Invested
```

**Energy_Invested is not waste—it's learning cost.**

### Task Tolerance Patterns
Different task types have different tolerance for energy investment:
- **Research/Exploration**: High tolerance (learning valuable)
- **Production**: Low tolerance (efficiency required)
- **Maintenance**: Medium tolerance (prevention worth investment)

## V3 Tensor Integration

### Work Validation Through Witnessing
```go
// Track work relationship for V3 calculation
if ms.trusttensorKeeper != nil {
    _, _, err = ms.trusttensorKeeper.CalculateRelationshipTrust(
        ctx,
        worker_lct,      // Who did the work
        work_id,         // What work was done
    )
}
```

### Validation Windows
- ADP tokens created with `ValidationBlock`
- Window for validators to assess work quality
- V3 score affects future ATP allocation priority

## LCT Entity Types

### Expanded Entity Categories
Through implementation, we identified key entity types:
- **agent**: Software/AI entities
- **human**: Human participants
- **device**: Hardware/IoT devices
- **service**: API endpoints, data sources
- **swarm**: Collective entities
- **producer**: Energy generation entities (special high-trust category)

### Entity Minting Pattern
```go
// Generate unique LCT ID with entity type
lctId := fmt.Sprintf("lct-%s-%s-%d",
    entityType,
    entityName,
    timestamp)

// Derive deterministic address
hash := sha256.Sum256([]byte(lctId))
entityAddress := sdk.AccAddress(hash[:20])
```

## Token Expiration Mechanics

### ATP Tokens Expire
Discovery: ATP tokens must have expiration to prevent hoarding:
```go
ExpirationBlock: blockHeight + 100000  // ~7 days at 6s blocks
```

This forces energy to be used productively, not accumulated.

## Society-Level Events

### Tracking Energy Flows
All token operations emit society-level events for tracking:
```go
sdk.NewEvent("adp_charged_to_atp",
    sdk.NewAttribute("producer_lct", producerId),
    sdk.NewAttribute("energy_source", source),
    sdk.NewAttribute("energy_harvested", amount),
)
```

This enables society-wide energy economy monitoring.

## Implementation Challenges

### Keeper Dependencies
Challenge: Circular dependencies between modules (energycycle ↔ trusttensor)

Solution: Optional keeper interfaces
```go
if ms.trusttensorKeeper != nil {
    // Use trust tensor if available
} else {
    // Fallback to basic validation
}
```

### Storage Architecture
Challenge: Efficient storage of ATP/ADP tokens

Solution: Collections-based storage with deterministic IDs
```go
RelationshipAtpTokens collections.Map[TokenId, AtpToken]
RelationshipAdpTokens collections.Map[TokenId, AdpToken]
```

## Next Implementation Steps

### Priority 1: Society Pool Tracking
Currently using placeholders. Need to implement:
- Society-level token counters
- Pool balance queries
- Allocation tracking

### Priority 2: V3 Validation Logic
- Implement actual V3 tensor calculations
- Define validation criteria per work type
- Create validator selection mechanism

### Priority 3: Energy Efficiency Metrics
- Track planned vs actual energy use
- Calculate efficiency ratings
- Adjust trust scores based on efficiency

## Philosophical Validation

The implementation confirms Web4's core philosophy:
- **Energy constrains action**: Can't act without ATP
- **Work creates value**: ATP discharge must produce outcomes
- **Society benefits collectively**: Individual accumulation impossible
- **Trust emerges from behavior**: Efficient entities gain priority

## Integration Points

### With Physical Systems
The ModuleCPU/CellCPU battery systems can:
- Act as energy producers (battery discharge → ADP charging)
- Report actual watt-hours for validation
- Create unforgeable energy generation proofs

### With AI Swarms
Agent swarms now have:
- Economic constraints (limited ATP)
- Value incentives (V3 validation)
- Collaboration requirements (society pool)
- Learning mechanisms (energy investment tracking)

## Conclusion

The ACT implementation validates Web4's energy economy design while revealing critical implementation patterns. The society pool architecture, semifungible token mechanics, and energy validation requirements are not just technical details—they embody Web4's philosophy of collective value creation through energy-constrained action.