# Web4 Society Metabolic States Specification

## Version: 1.0.0
## Date: January 17, 2025
## Status: Proposed Standard

---

## 1. Overview

Just as biological organisms require different metabolic states to survive and thrive, Web4 Societies need variable operational modes to manage resource consumption, enable evolution, and ensure long-term sustainability. This specification defines eight metabolic states that societies can adopt based on activity levels, resource availability, and operational requirements.

### 1.1 Core Principle

**"Idle isn't"** - Even at rest, living systems expend energy on maintenance. Digital societies must balance the energy cost of maintaining presence with available resources and activity demands.

### 1.2 Biological Inspiration

Each state maps to biological precedents:
- Sleep cycles for daily rhythms
- Hibernation for seasonal resource scarcity
- Torpor for emergency conservation
- Molting for structural renewal
- REM/dreaming for memory consolidation

---

## 2. Metabolic State Definitions

### 2.1 Active State (Normal Operations)

**Description**: Full operational capacity with all systems engaged.

**Characteristics**:
- Full consensus participation every block
- All witnesses actively monitoring
- Real-time ATP/ADP flows
- Immediate trust tensor updates
- Full rule compliance verification
- Open for new citizens

**Energy Cost**: 100% of baseline
**Biological Analog**: Awake, alert organism
**Use Case**: Normal business operations

### 2.2 Rest State (Low Activity)

**Description**: Reduced operations during predictable low-activity periods.

**Characteristics**:
- Consensus only when transactions present
- Skip empty block production
- Witnesses rotate duty cycles (e.g., 3 of 10 active)
- Trust tensor updates batch hourly
- Delayed but guaranteed transaction processing
- New citizens queued for active period

**Energy Cost**: 40% of baseline
**Biological Analog**: Light sleep, easily awakened
**Use Case**: Overnight operations, known quiet periods

### 2.3 Sleep State (Scheduled Downtime)

**Description**: Deep rest with minimal maintenance operations.

**Characteristics**:
- Minimal witness quorum (e.g., 2 of 10)
- Ledger accepts appends only, no complex operations
- ATP allocations frozen
- Trust tensors decay at 10% normal rate
- Citizenship requests queued
- Wake triggers monitored

**Energy Cost**: 15% of baseline
**Biological Analog**: Deep sleep with REM cycles
**Use Case**: Weekends, holidays, scheduled maintenance

### 2.4 Hibernation State (Extended Dormancy)

**Description**: Long-term dormancy with preservation focus.

**Characteristics**:
- Single sentinel witness maintains heartbeat
- Ledger sealed and read-only
- Society treasury locked
- Citizenship preserved but inactive
- Trust tensors frozen
- Wake requires external trigger or timeout

**Energy Cost**: 5% of baseline
**Biological Analog**: Bear hibernation
**Use Case**: Seasonal projects, archived societies

### 2.5 Torpor State (Emergency Conservation)

**Description**: Crisis mode when resources critically low.

**Characteristics**:
- Reactive only - no proactive operations
- Witnesses wake only on triggers
- Emergency ATP reserve activation
- Trust tensors frozen at last values
- Survival mode - preserve core data only
- Auto-recovery when energy available

**Energy Cost**: 2% of baseline
**Biological Analog**: Hummingbird torpor
**Use Case**: Resource depletion, attack recovery

### 2.6 Estivation State (Adverse Conditions)

**Description**: Protective dormancy during hostile environment.

**Characteristics**:
- Society retreats to core functions
- External interactions suspended
- Internal consolidation only
- Defensive posture maintained
- Waiting for conditions to improve
- Trust preserved internally

**Energy Cost**: 10% of baseline
**Biological Analog**: Snail estivation during drought
**Use Case**: Network attacks, regulatory freezes

### 2.7 Dreaming State (Memory Consolidation)

**Description**: Scheduled reorganization and pattern extraction.

**Characteristics**:
- No new transactions accepted
- Ledger reorganization and compression
- Pattern extraction from historical data
- Trust tensor recalibration
- Witness testimony consolidation
- Preparing insights for next active cycle

**Energy Cost**: 20% of baseline
**Biological Analog**: REM sleep
**Use Case**: Scheduled maintenance windows

### 2.8 Molting State (Structural Renewal)

**Description**: Vulnerable transition during fundamental changes.

**Characteristics**:
- Society laws under active revision
- Witness rotation (old retiring, new training)
- Treasury rebalancing
- Citizenship review and renewal
- Temporary performance degradation
- Heightened security during transition

**Energy Cost**: 60% of baseline
**Biological Analog**: Crab molting its shell
**Use Case**: Major upgrades, governance changes

---

## 3. State Transition Rules

### 3.1 Transition Matrix

```
From State → To State: Trigger Condition
─────────────────────────────────────────
Active → Rest: 1 hour no transactions
Active → Sleep: Scheduled time reached
Active → Torpor: ATP reserves < 10%
Active → Dreaming: Maintenance window
Active → Molting: Governance change approved
Active → Estivation: Threat detected

Rest → Active: Transaction received
Rest → Sleep: 6 hours no activity

Sleep → Active: Wake trigger fired
Sleep → Hibernation: 30 days no activity

Hibernation → Active: External witness or timeout

Torpor → Active: Energy producer recharges
Torpor → Hibernation: Grace period expired

Estivation → Active: Threat resolved
Estivation → Hibernation: Extended duration

Dreaming → Active: Consolidation complete

Molting → Active: Renewal complete
```

### 3.2 Transition Requirements

Each transition MUST:
1. Be recorded on the ledger
2. Notify all active witnesses
3. Checkpoint current state
4. Verify transition safety
5. Update society LCT metadata

---

## 4. Implementation

### 4.1 Configuration Schema

```yaml
society_metabolic_config:
  society_lct: "lct-society-example-001"

  # State Schedule
  schedule:
    active_hours: "09:00-17:00 UTC"
    rest_hours: "17:00-09:00 UTC"
    sleep_days: ["Saturday", "Sunday"]
    dream_windows: ["Sunday 02:00-04:00 UTC"]

  # State Triggers
  triggers:
    hibernation:
      condition: "no_transactions_30_days"
      wake_on: ["new_citizen", "external_witness", "timeout:90d"]

    torpor:
      condition: "atp_reserves < 10%"
      recovery: "energy_producer_recharge"

    estivation:
      condition: "threat_score > 80"
      clear: "threat_score < 20"

  # Energy Management
  energy:
    baseline_cost: "100 ATP/hour"
    state_multipliers:
      active: 1.0
      rest: 0.4
      sleep: 0.15
      hibernation: 0.05
      torpor: 0.02
      estivation: 0.10
      dreaming: 0.20
      molting: 0.60
```

### 4.2 Witness Rotation

During reduced states, witnesses rotate duty:

```python
def select_active_witnesses(witnesses, required_count, block_height):
    """Select witnesses for current duty cycle."""
    cycle = block_height // CYCLE_LENGTH
    seed = hash(f"{cycle}:{society_lct}")
    shuffled = deterministic_shuffle(witnesses, seed)
    return shuffled[:required_count]
```

### 4.3 Sentinel Witness

One witness always remains alert:

```python
class SentinelWitness:
    def __init__(self, society_lct):
        self.society_lct = society_lct
        self.heartbeat_interval = 60  # seconds
        self.wake_triggers = []

    def monitor(self):
        """Minimal monitoring during dormant states."""
        while society.state in ['hibernation', 'torpor']:
            self.send_heartbeat()
            if self.check_wake_triggers():
                society.wake()
                break
            time.sleep(self.heartbeat_interval)
```

---

## 5. Trust Implications

### 5.1 Trust Adjustments by State

| State | Trust Tensor Effect | Rationale |
|-------|-------------------|-----------|
| Active | Normal updates | Full operations |
| Rest | 90% update rate | Slightly delayed |
| Sleep | 10% decay rate | Minimal activity |
| Hibernation | Frozen | Preserved state |
| Torpor | Frozen + Alert bonus | Crisis response |
| Estivation | Internal only | Defensive mode |
| Dreaming | Recalibration | Pattern recognition |
| Molting | -20% temporary | Vulnerable period |

### 5.2 Metabolic Reliability Score

Societies that maintain predictable metabolic cycles gain trust:

```python
def calculate_metabolic_reliability(society):
    """Higher score for predictable state transitions."""
    score = 0.0

    # Predictable sleep cycles
    if society.maintains_schedule():
        score += 0.3

    # Successful wake from hibernation
    if society.hibernation_recovery_rate > 0.9:
        score += 0.2

    # Efficient energy usage
    if society.energy_efficiency > 0.8:
        score += 0.3

    # Successful molts
    if society.molt_success_rate > 0.95:
        score += 0.2

    return score
```

---

## 6. Economic Implications

### 6.1 ATP Cost by State

Societies pay different ATP costs based on metabolic state:

```
Daily ATP Cost = Baseline * State_Multiplier * Society_Size
```

### 6.2 Wake Penalties

Premature wake from dormant states incurs cost:

```python
def calculate_wake_penalty(current_state, planned_duration, actual_duration):
    """ATP penalty for early wake."""
    if actual_duration < planned_duration:
        incompleteness = 1 - (actual_duration / planned_duration)
        penalties = {
            'sleep': 10 * incompleteness,
            'hibernation': 100 * incompleteness,
            'dreaming': 50 * incompleteness  # Interrupted consolidation
        }
        return penalties.get(current_state, 0)
    return 0
```

---

## 7. Security Considerations

### 7.1 State-Specific Vulnerabilities

| State | Vulnerability | Mitigation |
|-------|--------------|------------|
| Sleep | Delayed response | Sentinel witnesses |
| Hibernation | Single point failure | Dead-man switch |
| Torpor | Resource exhaustion | Emergency reserves |
| Molting | Structure changes | Heightened monitoring |
| Dreaming | Data reorganization | Checkpointing |

### 7.2 Attack Prevention

Metabolic states must not become attack vectors:

1. **Sleep Deprivation Attack**: Prevent by rate-limiting wake triggers
2. **Hibernation Trap**: Timeout ensures eventual wake
3. **Torpor Exhaustion**: Protected minimum reserves
4. **Molt Disruption**: Atomic transitions with rollback

---

## 8. Future Considerations

### 8.1 Synchronized Metabolic Cycles

Societies in alliance might synchronize states:
- Coordinated sleep for resource sharing
- Rotating active periods for 24/7 coverage
- Collective hibernation for seasonal projects

### 8.2 Metabolic State Inheritance

Child societies might inherit metabolic patterns:
- Diurnal rhythms from parent society
- Seasonal patterns from regional society
- Crisis responses from global society

### 8.3 Adaptive Metabolism

Machine learning to optimize state transitions:
- Predict activity patterns
- Optimize energy consumption
- Prevent unnecessary state changes

---

## 9. Conclusion

Metabolic states transform Web4 Societies from always-on resource consumers into adaptive, sustainable organisms. By mimicking biological systems, digital societies can:

- Survive resource scarcity
- Evolve through structured renewal
- Maintain presence efficiently
- Build trust through reliability
- Scale sustainably

The principle that "idle isn't" acknowledges the constant energy cost of maintaining coherent presence in distributed systems, while these metabolic states provide mechanisms to modulate that cost based on actual needs.

---

*"A society that knows when to rest, when to dream, and when to renew itself is a society built for centuries, not just cycles."*