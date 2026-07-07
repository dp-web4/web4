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

> **Note on examples.** The JSON event objects in this document (e.g.
> `TokenMinting`, `R6Transaction` below) are **illustrative plain JSON**, using a
> bare `"type"` discriminator for readability. Canonical wire serializations are
> JSON-LD: the SDK serializers emit `"@type"` with an `@context` (see
> `data-formats.md`). Treat these examples as shape illustrations, not literal
> wire payloads.

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
    "circulating": 900000
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
        v3_delta={"valuation": +0.02}
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
      {"entity": "client", "v3": {"valuation": +0.03}},
      {"entity": "agent", "t3": {"talent": +0.01}}
    ]
  }
}
```

> **R6 / R7 note.** ATP→ADP discharge is an **R6** action. `r6-framework.md`
> names ATP→ADP transactions as the canonical R6 pattern for routine work, and
> §1.6 (Result) lists T3/V3 tensor updates as a standard R6 Result component.
> The `t3v3_updates` above are therefore R6 Result deltas on the direct
> participants — not evidence that discharge is R7. Discharges whose outcome
> should feed fractal trust evolution use **R7**, which adds **Reputation** as an
> explicit seventh output (see `r7-framework.md`, "R6 → R7 Relationship");
> ATP→ADP spending happens in both modes.

### 2.4 Slashing (ATP Destruction)

ATP can be slashed for violations:

```python
def slash_atp(caller, violator, amount, evidence, witnesses):
    """
    Slash ATP for law violations or failed commitments

    caller:    entity initiating the slash (must hold slashing authority)
    violator:  entity whose ATP is slashed
    witnesses: entities attesting the slashing event (recorded on the ledger)
    """
    # 1. Validate slashing authority of the initiator (not the violator)
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

> **Supply accounting.** Slashing **destroys** ATP: the slashed amount is removed
> from the society's `total_supply` (§3.1) rather than discharged to ADP. Slashing
> therefore sits **outside** the transfer-conservation invariant
> (`initial == final + fees`), which scopes only ATP transfers between entities (§6.3) — a destruction
> event is an intended supply reduction, not a conservation violation.

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
      "charged_fraction": 0.15,  // ATP/(ATP+ADP): fraction of supply currently charged (state ratio; distinct from the §2.2/§6 conversion-multiplier `charge_rate`)
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
        
        # Pool keys follow the §3.1 nested architecture: minted ADP enters the
        # discharged state distribution and the circulating allocation, keeping
        # `total_supply` == sum(allocations) and == sum(state_distribution).
        self.pools['state_distribution']['ADP'] += amount
        self.pools['allocations']['circulating'] += amount
        self.pools['total_supply'] += amount
        
        return MintingReceipt(amount, justification)
    
    def regulate_flow(self):
        """Regulate charge/discharge rates"""
        metrics = self.calculate_metrics()
        
        # Adjust charge rate based on velocity
        # (target_velocity is a society-defined threshold from the economic law)
        if metrics.velocity < self.law.target_velocity:
            self.increase_charge_incentives()
        elif metrics.velocity > self.law.target_velocity:
            self.apply_decay_pressure()
        
        # Prevent hoarding: the pool-level entry point delegates to the
        # per-stake decay routine in §3.3 (apply_demurrage_decay)
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
def apply_demurrage_decay(entity_stakes):
    """Apply time-based decay to prevent hoarding.

    Per-stake decay routine invoked by SocietyTokenPool.apply_demurrage
    (§3.2); named distinctly to avoid colliding with that pool method.
    """
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

> **R6 scoping.** Demurrage performs the ATP→ADP discharge of §2.3, but it is
> **time-triggered and not an R6 transaction** — it fires automatically once a
> stake passes the demurrage threshold, with no R6 Request/Result. It is
> therefore a carve-out from §7.1 MUST #5 ("Discharging MUST occur through R6
> transactions"), in the same way slashing (§2.4) is a carve-out from the
> transfer-conservation invariant: MUST #5 scopes *value-spending* discharge,
> while demurrage is a *maintenance* discharge enforcing anti-hoarding. The
> hoarding-penalty tensor delta above is the only T3/V3 effect; demurrage
> creates no V3 value and so does not engage MUST #6.

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
    # (nested {"t3"/"v3": {dim: delta}} notation, consistent with §2.3)
    primary_updates = [
        (r6_transaction.client, {"v3": {"valuation": +0.05}}),
        (r6_transaction.agent, {"t3": {"talent": +0.02}})
    ]
    
    # Secondary beneficiaries (witnessed)
    secondary_updates = [
        (witness, {"t3": {"temperament": +0.001}})
        for witness in r6_transaction.witnesses
    ]
    
    # Tertiary (society-level aggregate, not a T3/V3 dimension —
    # rollup accounting, outside §7.1 MUST #6 per its scope note)
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

The percentages shown are **illustrative defaults**, not protocol constants.
Societies SHOULD define attribution rates in their economic laws (see §6.2 on
economic laws). Implementations MUST NOT hard-code these values.

> **Role vocabulary (aligns with §2.3).** The cascade levels use these roles:
> *Direct executor* (Level 1) is the entity that performs the work — the §2.3
> `executor` (the acting agent). *Agent/delegator* (Level 2) is an intermediary
> that appears **only in a delegation chain**; in the simple §2.3 example the
> executor acts directly for the client, so Level 2 is empty. The **primary
> beneficiary** (§2.3 `primary_beneficiary`, the client) is the value
> *recipient*, not a contributor, and therefore sits **outside** this
> contribution-attribution cascade: its tensor delta — the largest in the
> example (§4.2, `valuation +0.05`) — is a *value-receipt* update on the
> consumer of the work, distinct from the contribution shares the cascade
> distributes. Keeping the beneficiary out of the cascade is why the attribution
> percentages sum over contributors only and are unaffected by it.

## 5. Inter-Society Currency Exchange

> **Inter-society homes.** Cross-society settlement is also governed by
> `inter-society-protocol.md` (which declares `Extends: atp-adp-cycle.md` for the
> ATP form) and `mcp-protocol.md` (the inter-society protocol; §7.7 covers
> cross-society exchange-rate negotiation). The exchange mechanisms in §5.2/§5.3
> describe society-level currency-pair bookkeeping; how rates are *grounded* and
> negotiated across societies is owned by those specs and is being reconciled
> with them (see References).

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
        "initial_rate": 1000,  // 1000 CITY = 1 NATION (CITY per NATION; get_exchange_rate (§5.3) returns the inverse, NATION per CITY = 0.001)
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
        # Convention: get_exchange_rate(source, target) returns
        # target-per-source units, so it multiplies the source amount directly.
        rate = get_exchange_rate(
            source_society.currency,
            target_society.currency
        )
        
        # Convert currency
        # e.g. CITY -> NATION: rate = 0.001 (NATION per CITY); see §5.1
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

  transfer_policy:
    intra_society_fee: "none"        # Or society-defined rate
    cross_society_fee: "none"        # Or society-defined rate
    fee_bearer: "sender"             # "sender" | "receiver" | "split"
    fee_destination: "society_pool"  # Recycled, not destroyed
```

### 6.3 Transfer Fees

The core protocol does **not** prescribe transfer fees. Peer-to-peer ATP
transfers within a society and cross-society exchanges (§5) are fee-free
at the protocol level.

Societies **MAY** implement transfer fees as economic law. When a society
chooses to levy fees:

- The fee rate, bearer (sender, receiver, or split), and destination MUST
  be declared in the society's published economic laws.
- Fees SHOULD be recycled into the society's pool (not destroyed), preserving
  total supply.
- Fee rates MUST NOT exceed society-defined caps.

Any specific fee rates appearing in simulations, explainers, or demos
(e.g., "5% transfer fee") are **simulation parameters**, not protocol
constants. Implementations MUST NOT hard-code fee rates; they MUST read
them from the governing society's published laws.

## 7. Implementation Requirements

### 7.1 MUST Requirements

1. Tokens MUST exist in only ATP or ADP state
2. Entities MUST NOT accumulate tokens beyond stake limits
3. Societies MUST maintain token pools
4. Charging MUST require value proof
5. Discharging MUST occur through R6 transactions
6. Entity-level value MUST be tracked through T3/V3 tensors; society-level aggregates MAY use non-tensor rollup accounting (§4.2)

> **Note on society-level value (MUST #6 scope).** MUST #6 scopes the
> *entity-role* legs that the §4.2 reference implementation tracks through
> T3/V3 deltas — the primary beneficiary's `v3`, the contributors'/agents'
> `t3`, and the witnesses' `t3`. The *society-level* aggregate (§4.3 Levels 4–5:
> Society and Parent-society) is a coarse rollup tracked via the
> `aggregate_value` channel in §4.2 — explicitly "**not a T3/V3 dimension**" —
> so it does **not** engage MUST #6. This is the same carve-out pattern as the
> §3.3 demurrage note (a maintenance discharge that "creates no V3 value and so
> does not engage MUST #6"): MUST #6 governs entity-role tensor accounting, not
> the society-aggregate rollup.

> **Note on intermediate (escrow) state.** The two-state requirement above is
> not violated by an *escrow/lock* lifecycle: ATP reserved for an in-flight
> operation ("locked") remains ATP, not a third token state — analogous to the
> `reserved` sub-partition of a pool (§3.1). Implementations MAY use a
> two-phase commit (lock → commit / rollback) to prevent double-spend on
> concurrent operations; that lifecycle is specified in `r6-framework.md`
> (escrow in §1.5, `lock_resources` in §2.1, `release_escrow` in §2.3).

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
6. Societies MAY levy transfer fees on ATP transfers (§6.3)

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

## References

This specification cross-references the following Web4 core specs:

- **R6 / R7 action grammar** — `r6-framework.md` (ATP→ADP discharge is the
  canonical R6 action; §1.6 Result includes T3/V3 updates; escrow/lock lifecycle
  in §1.5 / §2.1 / §2.3) and `r7-framework.md` ("R6 → R7 Relationship": R7 adds
  Reputation as the seventh output).
- **T3 / V3 trust and value tensors** — `t3-v3-tensors.md` and
  `../ontology/t3v3-ontology.ttl` for the dimensions updated during charging,
  discharging, and slashing.
- **LCT identity** — `LCT-linked-context-token.md` for the `lct:web4:...`
  identifiers used throughout (societies, entities, witnesses).
- **Societies and roles** — `society-roles.md` and `SOCIETY_SPECIFICATION.md`
  for pool governance, monetary authority, and role-scoped economic law.
- **Inter-society settlement** — `inter-society-protocol.md` (declares
  `Extends: atp-adp-cycle.md` for the ATP form; §4 covers unit-of-account
  semantics and ADP minting) and `mcp-protocol.md` (the inter-society protocol;
  §7.7 covers referent-grounded cross-society exchange-rate negotiation) for the
  cross-society exchange described in §5.

*"In Web4, value flows like energy through living systems—constantly cycling, never hoarded, always creating."*