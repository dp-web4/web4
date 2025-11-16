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

## ADP Return → Reputation Flow (November 16, 2025)

### Critical Discovery: When Reputation Updates Happen

**Key Insight**: Reputation updates occur during **ADP return to pool**, not during ATP discharge.

This prevents all reputation gaming thermodynamically.

### The Complete Cycle

```
1. Energy Source → ATP (charged with energy)
    ↓
2. ATP allocated to R6 transaction (automatic staking)
    ↓
3. Work performed (R6 processing)
    ↓
4. ATP → ADP (energy discharged, proof of work created)
    ↓
5. ADP RETURNS TO POOL:
    │
    ├─ DURING RETURN: Reputation updates propagate UP fractal chain
    │  ├─ Individual Agent: +reputation for work quality
    │  ├─ Team: +reputation for coordination
    │  ├─ Organization: +reputation for service delivery
    │  └─ Society: +reputation for citizen service
    │
    ├─ Reputation update REQUIRES discharged ADP
    ├─ ADP bound to THIS transaction context ONLY
    └─ ADP completes return, available for recharging with new energy
```

### Context-Bound ADP (Anti-Gaming)

ADP can only update reputation "in context of the current transaction only":

```go
type ADP struct {
    Amount          string    // ADP amount
    TransactionId   string    // Unique R6 transaction
    TransactionHash string    // Cryptographic binding
    EnergySpent     string    // Actual joules consumed
    FractalChain    []string  // All entities in delegation chain
    AlreadyReturned bool      // Single-use flag
}

func (adp *ADP) VerifyContext(tx R6Transaction) bool {
    // Verify this ADP came from the specified transaction
    // Cannot reuse old ADP for new reputation claims
    return adp.TransactionHash == tx.ComputeHash() &&
           adp.TransactionId == tx.Id
}
```

**This prevents:**
- Reusing old ADP to claim new reputation
- Transferring ADP between contexts to inflate scores
- Claiming reputation for work you didn't participate in

### Automatic Staking

ATP allocation to R6 task **IS** the stake:

```
NOT: "Lock 1000 ATP hoping to get it back" (gambling)
BUT: "Allocate 1000 ATP to work, prove completion with ADP" (energy accounting)

Success: Work done → ADP returns → reputation earned
Failure: No work → ADP slashed → no reputation
```

### Active vs Passive Resources

**Active Resources** (can process R6 transactions):
```
ATP → R6 Work → ADP
    ↓
ADP returns to pool
    ↓
Reputation updates propagate
    ↓
ADP available for recharging
```

**Passive Resources** (infrastructure, cannot process R6):
```
ATP → Maintenance → ADP
    ↓
ADP SLASHED (permanently consumed)
    ↓
NO reputation updates
    ↓
Only utilization metrics updated
```

This creates the **efficiency forcing function**:
- Minimize passive overhead → maximize reputation per ATP
- Share infrastructure efficiently → reduce slashed ADP
- Abandon underutilized infrastructure → let it decay naturally

### Fractal Reputation Propagation

When ADP returns to pool, reputation updates propagate up the entire delegation chain:

```go
func PropagateReputationFromADP(
    adp ADP,
    result R6Result,
    contributions map[string]float64, // entity_lct → contribution %
) []ReputationUpdate {
    // Calculate base reputation from ADP and result quality
    baseReputation := adp.Amount * result.QualityScore

    updates := []ReputationUpdate{}

    // Propagate up fractal chain
    for entityLct, contribution := range contributions {
        // Verify entity was in fractal chain
        if !adp.CanUpdateReputationFor(entityLct) {
            return error("entity not in fractal chain")
        }

        // Create reputation update
        update := ReputationUpdate{
            Entity:    entityLct,
            Delta:     baseReputation * contribution,
            Proof:     adp,
            Timestamp: now(),
        }
        updates = append(updates, update)
    }

    // Mark ADP as returned (single-use)
    adp.AlreadyReturned = true

    return updates
}
```

**Example**: Tax Processing
```
AI Agent (Claude-Tax-Processor-7):
    Contribution: 90% (did the actual work)
    Reputation: +450 (500 ADP * 0.9)

Team (Form 1040 Processing Team):
    Contribution: 7% (coordinated resources)
    Reputation: +35 (500 ADP * 0.07)

Organization (Tax Processing Department):
    Contribution: 2% (allocated budget, set standards)
    Reputation: +10 (500 ADP * 0.02)

Society (Government):
    Contribution: 1% (defined the need)
    Reputation: +5 (500 ADP * 0.01)

TOTAL: 500 ADP fully allocated across all contributors
```

The 500 ADP is unforgeable proof that work happened at each level.

### Anti-Gaming Through Thermodynamics

**Gaming Attempt #1: Fake Work Claims**
```
Attack: Create fake R6 transaction, claim work completed
Defense: Reputation requires ADP, ADP requires actual energy expenditure
Result: Cannot fake energy. Physics prevents fraud.
```

**Gaming Attempt #2: Reusing Old ADP**
```
Attack: Save ADP proof from good transaction, reuse for multiple claims
Defense: ADP cryptographically bound to transaction context, single-use
Result: Cannot replay ADP proof. Each transaction unique.
```

**Gaming Attempt #3: Reputation Inflation**
```
Attack: Create circular delegation to multiply reputation
Defense: Energy conservation - total reputation cannot exceed ADP amount
Result: Cannot create value from nothing. Physics enforces limits.
```

### Implementation Requirements

**ACT Module Updates Needed:**

1. **ADP Context Binding**
```protobuf
message AdpToken {
  string id = 1;
  string amount = 2;
  string transaction_id = 3;      // NEW: Unique R6 transaction
  string transaction_hash = 4;    // NEW: Cryptographic binding
  repeated string fractal_chain = 5;  // NEW: Delegation chain LCTs
  bool already_returned = 6;      // NEW: Single-use flag
  google.protobuf.Timestamp created = 7;
}
```

2. **Reputation Update on Return**
```go
// MsgReturnADP replaces simple pool return
message MsgReturnADP {
  string lct_id = 1;           // Who is returning ADP
  string adp_token_id = 2;     // Which ADP token
  string r6_result_hash = 3;   // Proof of work completion
  map<string, string> contributions = 4;  // entity_lct → contribution %
}

// Handler propagates reputation during return
func handleMsgReturnADP(ctx, msg) {
    // Verify ADP belongs to this LCT
    // Verify ADP not already returned
    // Verify contributions sum to ≤ 100%
    // Calculate reputation updates
    // Propagate up fractal chain
    // Mark ADP as returned
    // Return ADP to society pool
}
```

3. **Slashing for Maintenance**
```go
message MsgSlashADP {
  string lct_id = 1;               // Infrastructure being maintained
  string adp_token_id = 2;         // ADP being slashed
  string maintenance_description = 3;
}

// Handler permanently consumes ADP, no reputation update
func handleMsgSlashADP(ctx, msg) {
    // Verify ADP exists
    // Permanently remove from pool (do NOT return)
    // Update utilization metrics only
    // NO reputation updates
}
```

### Philosophical Validation

This completes the energy economy design:

- **Energy constrains action**: Can't act without ATP
- **Work creates value**: ATP discharge produces outcomes
- **Reputation requires proof**: ADP is unforgeable proof of work
- **Gaming is thermodynamically impossible**: Cannot fake energy expenditure
- **Efficiency emerges naturally**: Slashed ADP creates optimization pressure
- **Society benefits collectively**: Reputation flows up fractal chain

## Conclusion

The ACT implementation validates Web4's energy economy design while revealing critical implementation patterns. The society pool architecture, semifungible token mechanics, energy validation requirements, and **ADP-backed reputation flow** are not just technical details—they embody Web4's philosophy of collective value creation through energy-constrained action where **reputation emerges from thermodynamic proof, not belief**.