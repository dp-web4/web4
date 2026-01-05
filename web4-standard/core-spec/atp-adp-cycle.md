# Web4 ATP/ADP Value Cycle Specification

## Overview

The ATP/ADP (Allocation Transfer Packet / Allocation Discharge Packet) cycle is Web4's fundamental value mechanism, inspired by the biological ATP/ADP energy cycle that powers all living cells. ATP packets are the reification of allocated resources—semifungible tokens that exist in either charged (ATP) or discharged (ADP) states, managed by societies as their native currency.

**Terminology Note**: "Allocation" covers all resource types: energy, attention, work, compute, trust budgets. "Packet" reflects that these are units of value that can be implemented as blockchain tokens, local ledger entries, or other locally appropriate means. The discharged state (ADP) carries ephemeral metadata about how resources were consumed, which is cleared on recharge.

## 1. Core Concepts

### 1.1 The Biological Metaphor

Just as biological ATP (Adenosine Triphosphate) stores energy and ADP (Adenosine Diphosphate) is the discharged form, Web4's ATP/ADP cycle manages value:

```
Biological:  ADP + Energy → ATP → Work + ADP
Web4:        ADP + Value  → ATP → R6 Action + ADP
```

### 1.2 Token Properties

ATP/ADP tokens are:
- **Semifungible**: Can exist in two states (charged/discharged)
- **Non-accumulative**: Cannot be hoarded by entities
- **Society-managed**: Exist in pools controlled by societies
- **Value-reifying**: Physical representation of abstract value
- **Fractal**: Track value creation across all scales

### 1.3 Fundamental Principle

**Value flows through work, not accumulation.**

Unlike traditional currencies designed for storage, ATP tokens must flow to maintain value. Stagnant ATP naturally decays, encouraging continuous value creation and circulation.

## 2. Token Lifecycle

### 2.1 Minting (ADP Creation)

Societies mint tokens in the discharged (ADP) state:

```json
{
  "type": "TokenMinting",
  "society": "lct:web4:society:...",
  "lawReference": "sha256:...",
  "mintingEvent": {
    "amount": 1000000,
    "state": "ADP",
    "timestamp": "2025-09-15T12:00:00Z",
    "authority": "lct:web4:authority:monetary",
    "justification": "Quarterly expansion per economic policy",
    "witnesses": ["lct:web4:witness:auditor1", "lct:web4:witness:auditor2"]
  },
  "poolAllocation": {
    "total": 1000000,
    "reserved": 100000,
    "available": 900000
  }
}
```

### 2.2 Charging (ADP → ATP)

ADP tokens are charged to ATP through value creation:

```python
def charge_atp(producer, adp_amount, value_proof):
    """
    Charge ADP to ATP through value creation
    """
    # 1. Verify producer authorization
    if not is_authorized_producer(producer):
        raise UnauthorizedProducer()
    
    # 2. Validate value creation proof
    if not validate_value_proof(value_proof):
        raise InvalidValueProof()
    
    # 3. Check society's charging laws
    charge_rate = get_society_charge_rate(value_proof.type)
    atp_amount = adp_amount * charge_rate
    
    # 4. Execute charging
    society_pool.convert(
        from_state="ADP",
        to_state="ATP",
        amount=atp_amount,
        producer=producer,
        proof=value_proof
    )
    
    # 5. Update producer's T3/V3
    update_tensors(
        entity=producer,
        t3_delta={"training": +0.01},
        v3_delta={"value": +0.02}
    )
    
    # 6. Record on ledger
    record_charging_event(producer, atp_amount, value_proof)
    
    return atp_amount
```

#### 2.2.1 Charging Mechanisms

Societies define their own charging laws:

| Society Type | Charging Mechanism | Value Proof |
|--------------|-------------------|-------------|
| **Energy Grid** | Electricity generation | kWh produced |
| **Research Network** | Knowledge creation | Papers published |
| **Computing Cluster** | Computation performed | FLOPS delivered |
| **Creative Commons** | Content creation | Works registered |
| **Service Economy** | Services rendered | Tasks completed |

### 2.3 Discharging (ATP → ADP)

ATP discharges through R6 transactions:

```json
{
  "type": "R6Transaction",
  "request": {
    "action": "analyze_dataset",
    "atpRequired": 50
  },
  "execution": {
    "atpConsumed": 47,
    "work": {
      "compute": "300 CPU-seconds",
      "memory": "4GB peak",
      "bandwidth": "100MB"
    }
  },
  "discharge": {
    "from": "ATP",
    "to": "ADP",
    "amount": 47,
    "returned_to_pool": true
  },
  "valueTracking": {
    "primary_beneficiary": "lct:web4:entity:client",
    "executor": "lct:web4:entity:agent",
    "witnesses": ["lct:web4:witness:..."],
    "t3v3_updates": [
      {"entity": "client", "v3": {"value": +0.03}},
      {"entity": "agent", "t3": {"talent": +0.01}}
    ]
  }
}
```

### 2.4 Slashing (ATP Destruction)

ATP can be slashed for violations:

```python
def slash_atp(violator, amount, evidence):
    """
    Slash ATP for law violations or failed commitments
    """
    # 1. Validate slashing authority
    if not has_slashing_authority(caller):
        raise UnauthorizedSlashing()
    
    # 2. Verify evidence
    if not verify_evidence(evidence):
        raise InsufficientEvidence()
    
    # 3. Execute slashing
    slashed = society_pool.slash(
        entity=violator,
        amount=min(amount, get_entity_stake(violator)),
        reason=evidence.violation_type
    )
    
    # 4. Update tensors (negative)
    update_tensors(
        entity=violator,
        t3_delta={"temperament": -0.05},
        v3_delta={"veracity": -0.10}
    )
    
    # 5. Record with witnesses
    record_slashing_event(violator, slashed, evidence, witnesses)
    
    return slashed
```

## 3. Society Token Pools

### 3.1 Pool Architecture

Each society maintains token pools:

```json
{
  "society": "lct:web4:society:energy-grid",
  "pools": {
    "total_supply": 100000000,
    "state_distribution": {
      "ATP": 15000000,  // Charged, ready for use
      "ADP": 85000000   // Discharged, awaiting charging
    },
    "allocations": {
      "circulating": 90000000,
      "reserved": 5000000,
      "emergency": 3000000,
      "governance": 2000000
    },
    "metrics": {
      "velocity": 4.2,  // Cycles per period
      "charge_rate": 0.73,  // ATP/ADP ratio
      "decay_rate": 0.001,  // Per period
      "efficiency": 0.91  // Value preserved
    }
  }
}
```

### 3.2 Pool Management

Societies govern their pools through authorities:

```python
class SocietyTokenPool:
    def __init__(self, society, law_oracle):
        self.society = society
        self.law = law_oracle
        self.pools = self.initialize_pools()
    
    def mint_adp(self, amount, authority, justification):
        """Mint new ADP tokens per monetary policy"""
        if not self.law.permits_minting(authority, amount):
            raise UnauthorizedMinting()
        
        self.pools['ADP'] += amount
        self.pools['total_supply'] += amount
        
        return MintingReceipt(amount, justification)
    
    def regulate_flow(self):
        """Regulate charge/discharge rates"""
        metrics = self.calculate_metrics()
        
        # Adjust charge rate based on velocity
        if metrics.velocity < target_velocity:
            self.increase_charge_incentives()
        elif metrics.velocity > target_velocity:
            self.apply_decay_pressure()
        
        # Prevent hoarding
        self.apply_demurrage(rate=self.law.demurrage_rate)
        
        return metrics
```

### 3.3 Anti-Hoarding Mechanisms

ATP cannot be accumulated:

1. **Demurrage**: Held ATP gradually decays to ADP
2. **Velocity Requirements**: Minimum circulation rates
3. **Stake Limits**: Maximum stakeable amounts
4. **Use-or-Lose**: Unutilized allocations return to pool

```python
def apply_demurrage(entity_stakes):
    """Apply time-based decay to prevent hoarding"""
    for entity, stake in entity_stakes.items():
        age = get_stake_age(stake)
        if age > DEMURRAGE_THRESHOLD:
            decay_rate = calculate_decay_rate(age)
            decayed = stake.amount * decay_rate
            
            # Convert ATP to ADP
            convert_to_adp(stake, decayed)
            
            # Penalize hoarding behavior
            update_tensors(
                entity=entity,
                t3_delta={"temperament": -0.01}
            )
```

## 4. Value Creation and Tracking

### 4.1 Producer Entities

Authorized producers charge ADP to ATP:

```json
{
  "producer": {
    "lct": "lct:web4:producer:solar-farm-01",
    "type": "energy_producer",
    "authorization": {
      "society": "lct:web4:society:energy-grid",
      "scope": "solar_generation",
      "rate": "1 ATP per kWh",
      "caps": {
        "daily_max": 10000,
        "surge_multiplier": 1.5
      }
    },
    "production_proof": {
      "method": "meter_reading",
      "validators": ["utility_company", "smart_meter"],
      "frequency": "15_minutes"
    }
  }
}
```

### 4.2 Value Flow Tracking

Value flows fractally through T3/V3 tensors:

```python
def track_value_flow(r6_transaction):
    """Track value creation through fractal tensor updates"""
    
    # Direct participants
    primary_updates = [
        (r6_transaction.client, {"v3.value": +0.05}),
        (r6_transaction.agent, {"t3.talent": +0.02})
    ]
    
    # Secondary beneficiaries (witnessed)
    secondary_updates = [
        (witness, {"t3.temperament": +0.001})
        for witness in r6_transaction.witnesses
    ]
    
    # Tertiary (society-level)
    society_updates = [
        (r6_transaction.society, {"aggregate_value": +0.0001})
    ]
    
    # Apply updates fractally
    for entity, update in (primary_updates + 
                           secondary_updates + 
                           society_updates):
        apply_tensor_update(entity, update)
    
    return ValueFlowRecord(
        primary=primary_updates,
        secondary=secondary_updates,
        tertiary=society_updates,
        total_value=sum_value_created()
    )
```

### 4.3 Fractal Value Attribution

Value cascades through relationships:

```
Level 1: Direct executor (100% attribution)
Level 2: Agent/delegator (10% attribution)  
Level 3: Witnesses (1% attribution)
Level 4: Society (0.1% attribution)
Level 5: Parent society (0.01% attribution)
```

## 5. Inter-Society Currency Exchange

### 5.1 Society Membership and Currency

When a society joins another as citizen:

```json
{
  "membership_event": {
    "child_society": "lct:web4:society:city-grid",
    "parent_society": "lct:web4:society:national-grid",
    "currency_negotiation": {
      "child_currency": {
        "token": "CITY-ATP",
        "supply": 1000000,
        "velocity": 3.5
      },
      "parent_currency": {
        "token": "NATION-ATP",
        "supply": 1000000000,
        "velocity": 4.2
      },
      "exchange_agreement": {
        "initial_rate": 1000,  // 1000 CITY = 1 NATION
        "mechanism": "floating",
        "adjustment": "daily",
        "reserves": {
          "child_holds": 10000,  // NATION-ATP
          "parent_holds": 10000000  // CITY-ATP
        }
      }
    }
  }
}
```

### 5.2 Exchange Mechanisms

Societies can choose exchange models:

| Model | Description | Use Case |
|-------|-------------|----------|
| **Fixed Peg** | Constant exchange rate | Stable subsocieties |
| **Floating** | Market-determined rate | Independent economies |
| **Basket** | Weighted average | Multi-society members |
| **Algorithmic** | Formula-based | Automated adjustment |

### 5.3 Cross-Society Transactions

```python
def cross_society_transaction(source_entity, target_entity, amount):
    """Execute transaction across society boundaries"""
    
    source_society = get_society(source_entity)
    target_society = get_society(target_entity)
    
    if source_society != target_society:
        # Get exchange rate
        rate = get_exchange_rate(
            source_society.currency,
            target_society.currency
        )
        
        # Convert currency
        source_atp = amount
        target_atp = amount * rate
        
        # Execute exchange
        source_society.pool.discharge(source_atp)
        target_society.pool.charge(target_atp)
        
        # Update exchange reserves
        update_reserves(source_society, target_society, amount)
        
        # Record with both society witnesses
        record_cross_society_tx(
            source_entity, target_entity,
            source_atp, target_atp, rate,
            witnesses=[source_society.witness, target_society.witness]
        )
```

## 6. Governance and Regulation

### 6.1 Monetary Authority

Each society's monetary authority manages:

```json
{
  "monetary_authority": {
    "lct": "lct:web4:authority:monetary",
    "society": "lct:web4:society:...",
    "powers": [
      "mint_adp",
      "set_charge_rates",
      "adjust_decay",
      "authorize_producers",
      "slash_violations",
      "manage_reserves"
    ],
    "constraints": {
      "max_mint_per_period": 1000000,
      "min_reserve_ratio": 0.1,
      "max_slash_per_event": 10000,
      "governance_quorum": 0.66
    },
    "oversight": {
      "auditors": ["lct:web4:auditor:1", "lct:web4:auditor:2"],
      "review_period": "monthly",
      "transparency": "public_ledger"
    }
  }
}
```

### 6.2 Economic Laws

Societies encode economic policy as law:

```yaml
economic_laws:
  minting_policy:
    frequency: quarterly
    formula: "gdp_growth * 1.1"
    caps: "10% of current_supply"
    
  charging_rules:
    energy: "1 ATP per kWh"
    compute: "10 ATP per TFLOP"
    storage: "1 ATP per TB-day"
    bandwidth: "0.1 ATP per GB"
    
  decay_policy:
    idle_threshold: "7 days"
    decay_rate: "1% per day after threshold"
    minimum_velocity: 2.0
    
  slashing_rules:
    false_claim: "100 ATP"
    service_failure: "50 ATP"
    law_violation: "500 ATP"
```

## 7. Implementation Requirements

### 7.1 MUST Requirements

1. Tokens MUST exist in only ATP or ADP state
2. Entities MUST NOT accumulate tokens beyond stake limits
3. Societies MUST maintain token pools
4. Charging MUST require value proof
5. Discharging MUST occur through R6 transactions
6. Value MUST be tracked through T3/V3 tensors

### 7.2 SHOULD Requirements

1. Societies SHOULD implement demurrage
2. Producers SHOULD be authorized by law
3. Exchange rates SHOULD be transparent
4. Monetary policy SHOULD be public
5. Slashing SHOULD require evidence

### 7.3 MAY Requirements

1. Societies MAY choose charging mechanisms
2. Societies MAY implement custom decay rates
3. Societies MAY create exchange agreements
4. Societies MAY delegate monetary authority
5. Societies MAY implement emergency measures

## 8. Security Considerations

### 8.1 Attack Vectors and Mitigations

| Attack | Description | Mitigation |
|--------|-------------|------------|
| **Double Charging** | Charging same value twice | Cryptographic proofs, witness requirements |
| **Phantom Value** | Claiming nonexistent value | Producer authorization, proof validation |
| **Pool Draining** | Exhausting society pools | Rate limits, reserve requirements |
| **Exchange Manipulation** | Gaming exchange rates | Multi-society witnesses, algorithmic rates |
| **Hoarding** | Accumulating ATP | Demurrage, velocity requirements |

### 8.2 Cryptographic Requirements

- Value proofs must be cryptographically signed
- Pool states must be merkle-rooted
- Exchange rates must be witnessed
- Slashing must have evidence trails

## 9. Economic Properties

### 9.1 Desired Behaviors

The ATP/ADP cycle encourages:
- **Continuous value creation** (not rent-seeking)
- **Rapid circulation** (not hoarding)
- **Productive work** (not speculation)
- **Cooperative behavior** (shared value tracking)
- **Sustainable growth** (decay prevents inflation)

### 9.2 Anti-Patterns Prevented

The system prevents:
- **Wealth accumulation** (tokens must flow)
- **Artificial scarcity** (societies mint as needed)
- **Speculation** (no secondary markets)
- **Rent extraction** (value requires work)
- **Monetary manipulation** (transparent governance)

## 10. Use Cases

### 10.1 Energy Grid Society

```yaml
society: National Energy Grid
currency: ENERGY-ATP
charging: 1 ATP per kWh generated
producers:
  - Solar farms
  - Wind turbines
  - Hydroelectric
consumers:
  - Data centers (compute work)
  - Factories (production work)
  - Homes (living work)
flow: Generation → ATP → Work → ADP → Generation
```

### 10.2 Research Network Society

```yaml
society: Academic Research Network
currency: KNOWLEDGE-ATP
charging: 100 ATP per peer-reviewed paper
producers:
  - Researchers
  - Laboratories
  - Think tanks
consumers:
  - Students (learning work)
  - Industry (application work)
  - Government (policy work)
flow: Research → ATP → Application → ADP → Research
```

### 10.3 Creative Commons Society

```yaml
society: Global Creative Commons
currency: CREATIVE-ATP
charging: Variable by work type
producers:
  - Artists (visual works)
  - Musicians (audio works)
  - Writers (textual works)
consumers:
  - Audiences (experiential work)
  - Remixers (derivative work)
  - Educators (teaching work)
flow: Creation → ATP → Experience → ADP → Creation
```

## 11. Migration and Adoption

### 11.1 Bootstrapping a Society's Economy

1. **Define value sources** (what can be charged)
2. **Authorize producers** (who can charge)
3. **Set initial supply** (mint initial ADP)
4. **Establish rates** (charging/discharging ratios)
5. **Implement governance** (monetary authority)

### 11.2 Joining Existing Economies

1. **Negotiate membership** (citizen role in parent)
2. **Establish exchange** (currency conversion)
3. **Align policies** (compatible laws)
4. **Share reserves** (stability mechanism)
5. **Cross-witness** (transaction validation)

## 12. Summary

The ATP/ADP cycle creates a value system where:

- **Value is work**: ATP represents capacity for productive action
- **Flow over stock**: Tokens must circulate, not accumulate
- **Society sovereignty**: Each society manages its own currency
- **Fractal tracking**: Value creation benefits all participants
- **Natural decay**: Prevents hoarding and encourages use

This creates an economy aligned with Web4's principles: trust through action, value through contribution, and prosperity through cooperation rather than competition.

---

*"In Web4, value flows like energy through living systems—constantly cycling, never hoarded, always creating."*