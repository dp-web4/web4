# Energy-Backed ATP Integration Design

**Session #36** - 2025-11-16
**Status:** Design Exploration
**Purpose:** Bridge Sessions #30-35 mechanisms with proper ATP energy model

---

## Context

### Existing Work (Sessions #30-35)
Excellent mechanisms implemented:
- Identity bonds (Sybil resistance)
- Vouching systems (accountability)
- Trust-based pricing (reputation affects costs)
- Gaming resistance (statistical detection)
- Web of trust (social graph)

### The Problem
Current implementations treat ATP like traditional currency:
- Can be **hoarded** (savings/profit)
- Can be **staked** (with possibility of loss)
- **Persists** independently of backing
- Underwritten by **belief** rather than **energy**

This replicates problems Web4 aims to solve.

### The Solution Direction
ATP must be reimagined as:
- **Energy flow**, not money
- **Backed by real resources** (compute, solar, human labor)
- **Cannot be hoarded** (expires if not used)
- **State transitions** (ATP ↔ ADP) require real work

---

## ATP Energy Model Fundamentals

### What ATP Actually Is

```
ATP = Allocation Transfer Packet
BUT fundamentally: Energy allocation tracker

ATP is NOT:
✗ A currency you own
✗ A store of value
✗ Something that persists indefinitely
✗ Underwritten by belief

ATP IS:
✓ Energy available for allocation
✓ A flow measure, not a stock
✓ Only meaningful when charged with actual energy
✓ Underwritten by physical/computational resources
```

### The ATP ↔ ADP Cycle

```
Energy Source (solar, compute, human labor)
    ↓
Charge ADP to ATP (backed by real energy)
    ↓
ATP Allocation (energy spent on tasks)
    ↓
Discharge ATP to ADP (work completed)
    ↓
ADP Reputation Credit (recognizes work done)
    ↓
Return to Society Pool
    ↓
Recharge with new energy → ATP (cycle continues)
```

**Key Properties:**
1. ATP is **charged** - only ATP backed by available energy can allocate resources
2. Energy is **spent** - work discharges ATP to ADP
3. ADP **can't do work** - only allocates reputation/recognition
4. **No hoarding** - uncharged ATP is meaningless (like dead battery)
5. **Continuous flow** - energy flows through system, doesn't accumulate

---

## Three Energy Models for Societies

### Model 1: Own Energy Production
```
Society has energy source (solar panels, compute cluster, etc.)
    → Can charge ATP directly from own production
    → Full energy autonomy
    → Example: SAGE on Jetson with local GPU

Energy Flow:
Solar Panel → ATP charged → Work done → ADP → Recharge
```

### Model 2: Citizenship in Parent Society
```
Society has no energy production
    → Fractally adopts parent society's ATP
    → Energy allocation from parent's pool
    → Example: Sub-society within Web4 sharing compute

Energy Flow:
Parent's ATP pool → Allocation to sub-society → Work → ADP → Parent pool
```

### Model 3: Energy Trade
```
Society trades for charged ATP
    → Must have value to trade (goods, services, ADP reputation)
    → Exchanges with energy-producing societies
    → Example: Software society trades code for compute credits

Energy Flow:
Own ADP (reputation) → Trade for ATP → Work → ADP → Trade again
```

---

## Integrating Energy-Backed ATP with Sessions #30-35 Mechanisms

### Challenge: Identity Bonds

**Session #34 Implementation:**
```python
class IdentityBond:
    bond_amount: int = 1000  # ATP staked
    lock_period_days: int = 30
```

**Problem:** Treating ATP as stakeable currency that persists

**Energy-Backed Solution:**
```python
class IdentityBond:
    """
    Bond is commitment of ENERGY CAPACITY, not currency stake.

    Bond represents: "I commit to maintaining X energy capacity
    available for society work for Y period"
    """
    energy_capacity_commitment: float  # Watts or compute units
    lock_period_days: int = 30
    energy_source: str  # "solar:panel_id" or "compute:gpu_model"

    # Validation: Must prove energy capacity exists
    capacity_proof: EnergyCapacityProof

    # Forfeiture: Lose reputation, not money
    # If fail: ADP reputation reduced, not ATP seized
    forfeit_reputation_penalty: float = 0.5  # 50% trust reduction
```

**Key Change:** Bond commits **energy capacity** (provable), not currency (stakeable)

### Challenge: Vouching System

**Session #35 Implementation:**
```python
class Vouch:
    stake_amount: int = 200  # ATP staked
```

**Problem:** Stakes ATP as if it's persistent money

**Energy-Backed Solution:**
```python
class Vouch:
    """
    Vouch is commitment to SPONSOR newcomer's energy needs
    during bootstrap period.

    Voucher commits: "I will allocate some of my energy budget
    to this newcomer until they establish their own sources"
    """
    energy_allocation_commitment: float  # Portion of voucher's ATP
    bootstrap_period_days: int = 30

    # Success: Newcomer establishes own energy, commitment ends
    # Failure: Voucher's reputation damaged (not ATP seized)
    reputation_at_risk: float  # Trust score penalty if fail
```

**Key Change:** Vouch commits **energy allocation** (temporary flow), not stake (permanent lock)

### Challenge: Trust-Based Pricing

**Session #33 Implementation:**
```python
# Low trust → High ATP cost
rate = base_rate * trust_multiplier  # 1.0x to 2.0x
```

**Problem:** Treats ATP as currency with pricing

**Energy-Backed Solution:**
```python
"""
Trust affects ENERGY PRIORITY, not cost.

High trust: Your work requests get priority in energy queue
Low trust: Your work waits until high-trust tasks completed

No 'cost' - just queue priority based on reputation
"""

class EnergyAllocationPriority:
    def calculate_priority(self, requester_trust: float) -> int:
        """
        Priority = trust_score × urgency × efficiency

        High trust (0.8-1.0): Priority 1-2 (immediate)
        Medium trust (0.5-0.8): Priority 3-5 (soon)
        Low trust (0-0.5): Priority 6-10 (when available)
        """
        if requester_trust >= 0.8:
            return 1  # High priority
        elif requester_trust >= 0.5:
            return 3  # Medium priority
        else:
            return 6  # Low priority (but still gets work done)
```

**Key Change:** Trust determines **priority** (queue position), not **price** (cost)

---

## ATP State Transitions with Energy Validation

### ADP → ATP (Charging)

**Requires:** Proof of real energy input

```python
@dataclass
class EnergyCapacityProof:
    """
    Proof that society has real energy capacity.

    Without this, ADP cannot be charged to ATP.
    """
    energy_source_type: str  # "solar", "compute", "grid", "human"
    capacity_watts: float    # Rated capacity in watts
    timestamp: datetime
    validation_method: str   # How capacity was proven

    # Examples:
    # Solar: "solar_panel_serial:XYZ, rated 300W, verified by hardware query"
    # Compute: "gpu:RTX4090, 450W TDP, verified by CUDA query"
    # Grid: "meter:ABC, 1kW allocated, verified by utility API"
    # Human: "labor:agent:123, 100W metabolic, verified by work history"

class EnergyBackedATPPool:
    """Society's ATP is backed by real energy capacity"""

    def charge_adp_to_atp(
        self,
        adp_amount: float,
        energy_proof: EnergyCapacityProof
    ) -> float:
        """
        Charge ADP to ATP only if backed by real energy.

        Cannot create ATP from nothing - must prove energy source.
        """
        # Validate energy proof
        if not self._validate_energy_source(energy_proof):
            raise ValueError("Cannot charge ATP without valid energy source")

        # Calculate how much ATP can be charged based on capacity
        available_capacity = energy_proof.capacity_watts
        current_allocation = self.get_current_allocation()

        if current_allocation + adp_amount > available_capacity:
            raise ValueError(
                f"Insufficient capacity: "
                f"{current_allocation + adp_amount}W > {available_capacity}W"
            )

        # Charge: ADP → ATP
        self.adp_pool -= adp_amount
        self.atp_pool += adp_amount

        # Record energy backing
        self.energy_backing_ledger.append({
            "atp_charged": adp_amount,
            "energy_source": energy_proof,
            "timestamp": datetime.now(timezone.utc)
        })

        return adp_amount
```

### ATP → ADP (Discharging)

**Requires:** Work being performed

```python
class WorkAllocation:
    """ATP discharge happens when work is actually done"""

    def allocate_atp_to_work(
        self,
        work_description: str,
        atp_amount: float,
        worker_lct: str
    ) -> WorkTicket:
        """
        Allocate ATP to work task.
        ATP is 'spent' (discharged to ADP) as work progresses.
        """
        # Create work ticket
        ticket = WorkTicket(
            work_id=generate_work_id(),
            description=work_description,
            atp_allocated=atp_amount,
            worker=worker_lct,
            status="in_progress"
        )

        # Reserve ATP (not yet discharged)
        self.atp_pool -= atp_amount
        self.atp_reserved_for_work += atp_amount

        return ticket

    def complete_work(
        self,
        ticket: WorkTicket,
        work_proof: WorkCompletionProof
    ):
        """
        When work completes, ATP discharges to ADP.

        This is the only way ATP becomes ADP - through work.
        """
        # Validate work was done
        if not self._validate_work_completion(work_proof):
            # Work failed - ATP returns to pool, no ADP created
            self.atp_reserved_for_work -= ticket.atp_allocated
            self.atp_pool += ticket.atp_allocated
            return

        # Work succeeded - discharge ATP to ADP
        self.atp_reserved_for_work -= ticket.atp_allocated
        self.adp_pool += ticket.atp_allocated

        # Credit worker's reputation (ADP represents work done)
        self.credit_worker_reputation(
            ticket.worker,
            ticket.atp_allocated,
            work_proof.quality_score
        )
```

---

## ATP Expiration to Prevent Hoarding

```python
@dataclass
class ChargedATP:
    """
    ATP has expiration - must be used or energy is wasted.

    This prevents hoarding and forces productive allocation.
    """
    amount: float
    charged_at: datetime
    expiration: datetime  # e.g., charged_at + 7 days
    energy_source: EnergyCapacityProof

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expiration

    def remaining_lifetime(self) -> timedelta:
        return self.expiration - datetime.now(timezone.utc)

class ATPPoolWithExpiration:
    """ATP pool manages expiring energy allocations"""

    def __init__(self):
        self.charged_atp_batches: List[ChargedATP] = []
        self.expiration_handler = ExpirationHandler()

    def charge_atp(
        self,
        amount: float,
        energy_proof: EnergyCapacityProof,
        lifetime_days: int = 7
    ):
        """Charge ATP with expiration"""
        batch = ChargedATP(
            amount=amount,
            charged_at=datetime.now(timezone.utc),
            expiration=datetime.now(timezone.utc) + timedelta(days=lifetime_days),
            energy_source=energy_proof
        )
        self.charged_atp_batches.append(batch)

    def get_available_atp(self) -> float:
        """Only non-expired ATP is available"""
        return sum(
            batch.amount
            for batch in self.charged_atp_batches
            if not batch.is_expired()
        )

    def expire_old_atp(self):
        """
        Expire old ATP - energy wasted if not used.

        This is NOT a punishment - it's natural decay.
        Like food spoiling or battery discharge.
        """
        expired = [b for b in self.charged_atp_batches if b.is_expired()]

        for batch in expired:
            self.charged_atp_batches.remove(batch)

            # Log expiration for analysis
            self.expiration_handler.log_waste({
                "amount": batch.amount,
                "source": batch.energy_source,
                "age": datetime.now(timezone.utc) - batch.charged_at
            })

            # Could trigger efficiency alerts if too much expiring
            if batch.amount > 100:
                self.alert_high_waste(batch)
```

---

## Integration Strategy: Adapting Sessions #30-35

### Step 1: ATP Pool Architecture

```python
class EnergyBackedSocietyPool:
    """
    Society pool with energy backing (not currency).

    Replaces: Traditional ATP balance from Sessions #30-33
    """

    def __init__(self, society_lct: str):
        self.society_lct = society_lct

        # Energy sources backing this pool
        self.energy_sources: List[EnergyCapacityProof] = []

        # ATP/ADP pools (flow, not stock)
        self.atp_pool: List[ChargedATP] = []  # Charged, available energy
        self.adp_pool: float = 0.0             # Discharged, reputation credits

        # Work allocations
        self.active_work: List[WorkTicket] = []

    def get_energy_capacity(self) -> float:
        """Total energy capacity society can draw on"""
        return sum(source.capacity_watts for source in self.energy_sources)

    def get_available_atp(self) -> float:
        """Currently available charged ATP (non-expired)"""
        return sum(
            batch.amount
            for batch in self.atp_pool
            if not batch.is_expired()
        )
```

### Step 2: Trust Affects Priority, Not Price

```python
class TrustBasedEnergyPriority:
    """
    Integrates Session #33-35 trust system with energy allocation.

    Trust doesn't change cost - it changes queue priority.
    """

    def __init__(self, trust_graph: TrustGraph):
        self.trust_graph = trust_graph  # From Session #35
        self.work_queue = PriorityQueue()

    def request_work_allocation(
        self,
        requester_lct: str,
        work_description: str,
        atp_needed: float
    ) -> WorkRequest:
        """
        Queue work request based on requester's trust.

        High trust: Priority 1 (processed immediately)
        Low trust: Priority 10 (processed when capacity available)
        """
        # Get requester's trust from Session #33-35 systems
        trust_score = self.get_combined_trust(requester_lct)

        # Calculate priority based on trust
        priority = self.calculate_priority(trust_score)

        # Create work request
        request = WorkRequest(
            requester=requester_lct,
            description=work_description,
            atp_needed=atp_needed,
            priority=priority,
            submitted_at=datetime.now(timezone.utc)
        )

        # Add to priority queue
        self.work_queue.put((priority, request))

        return request

    def calculate_priority(self, trust_score: float) -> int:
        """
        Trust determines priority in energy queue.

        This is where Sessions #33-35 trust mechanisms matter:
        - Identity bonds → Higher trust
        - Good behavior history → Higher trust
        - Vouching → Bootstrap trust
        - Web of trust → Transitive trust

        Higher trust → Better priority → Work done faster
        Lower trust → Worse priority → Work waits

        But everyone's work eventually gets done (no one excluded).
        """
        if trust_score >= 0.9:
            return 1  # Highest priority
        elif trust_score >= 0.7:
            return 3
        elif trust_score >= 0.5:
            return 5
        elif trust_score >= 0.3:
            return 7
        else:
            return 10  # Lowest priority (but still served)
```

### Step 3: Identity Bonds as Energy Capacity Commitment

```python
class EnergyBackedIdentityBond(IdentityBond):
    """
    Extends Session #34 identity bonds with energy backing.

    Bond is commitment to maintain energy capacity, not currency stake.
    """

    def __init__(
        self,
        society_lct: str,
        energy_sources: List[EnergyCapacityProof],
        lock_period_days: int = 30
    ):
        # Calculate total committed capacity
        total_capacity = sum(s.capacity_watts for s in energy_sources)

        # Bond amount is now energy capacity (watts), not currency (ATP)
        self.energy_capacity_commitment = total_capacity
        self.energy_sources = energy_sources
        self.lock_period_days = lock_period_days
        self.created_at = datetime.now(timezone.utc)

        # Forfeiture is reputation loss, not currency seizure
        self.reputation_at_risk = 0.5  # 50% trust score reduction

    def validate_capacity_maintained(self) -> bool:
        """
        Verify that committed energy capacity still exists.

        If capacity drops below commitment, bond is violated.
        """
        current_capacity = sum(
            s.capacity_watts
            for s in self.energy_sources
            if s.is_still_valid()
        )

        return current_capacity >= self.energy_capacity_commitment

    def handle_violation(self):
        """
        If capacity commitment not maintained, forfeit reputation.

        This is where Session #34's gaming resistance applies:
        - Reputation drops significantly
        - Future priority in work queue degraded
        - Vouchers who vouched also affected
        - Identity marked as unreliable
        """
        # Reduce trust score (Session #33-35 mechanisms)
        self.apply_reputation_penalty(self.reputation_at_risk)

        # Notify vouchers (Session #35 vouching system)
        self.notify_vouchers_of_violation()

        # Bond marked as forfeited (affects future bonding)
        self.forfeited = True
```

---

## Key Insights

### What Changes

1. **ATP is energy flow, not money**
   - Can't hoard (expires)
   - Can't stake (commits capacity instead)
   - Backed by real resources

2. **Trust affects priority, not price**
   - High trust → fast service
   - Low trust → slow service
   - Everyone still served

3. **Bonds commit capacity, not currency**
   - Prove energy sources
   - Maintain capacity
   - Forfeit reputation, not money

### What Stays the Same

1. **Gaming resistance mechanisms** (Session #34)
   - Identity bonds still prevent Sybil (via capacity commitment)
   - Asymmetric trust still prevents gaming
   - Statistical detection still catches patterns

2. **Web of trust** (Session #35)
   - Transitive trust still works
   - Vouching still provides bootstrap
   - Social graph still resists Sybils

3. **Reputation integration** (Session #33)
   - Trust scores still matter
   - Work history still tracked
   - Relationships still build trust

**The mechanisms are excellent - they just interface with ATP differently.**

---

## Implementation Roadmap

### Phase 1: Energy Capacity Proofs
- Define `EnergyCapacityProof` interface
- Implement validators for different sources (solar, compute, grid)
- Test proof verification

### Phase 2: ATP/ADP Pool with Expiration
- Implement `ChargedATP` with expiration
- Create `EnergyBackedSocietyPool`
- Test charging, allocation, discharge, expiration

### Phase 3: Priority-Based Allocation
- Implement `TrustBasedEnergyPriority`
- Integrate with Session #33-35 trust systems
- Test queue priority mechanics

### Phase 4: Adapt Identity Bonds
- Extend `IdentityBond` to `EnergyBackedIdentityBond`
- Update forfeiture to reputation loss
- Test capacity validation

### Phase 5: Integration Testing
- End-to-end scenarios with all systems
- Verify Sessions #30-35 mechanisms still work
- Document differences from currency model

---

## Conclusion

**The work from Sessions #30-35 is not wasted** - the mechanisms are excellent:
- Identity bonds
- Vouching systems
- Trust-based differentiation
- Gaming resistance
- Web of trust

**These mechanisms adapt cleanly to energy-backed ATP:**
- Bonds commit capacity (not currency)
- Trust affects priority (not price)
- Work creates ADP (not profits)
- Energy flows (doesn't accumulate)

**This design bridges conceptual gap while preserving implementation value.**

---

**Session #36** - Energy-backed ATP design complete
