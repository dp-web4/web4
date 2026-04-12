#!/usr/bin/env python3
"""
Society Metabolic States — Track I
====================================
First reference implementation of the 8-state society lifecycle from
web4-standard/core-spec/SOCIETY_METABOLIC_STATES.md.

8 bio-inspired states: Active, Rest, Sleep, Hibernation, Torpor,
Estivation, Dreaming, Molting — each with different energy costs,
witness requirements, trust tensor behavior, and transition rules.

Builds on existing entity-level 5-state metabolic model (web4_entity.py)
but operates at society scale with witness rotation, sentinel witnesses,
wake penalties, and metabolic reliability scoring.
"""

import hashlib
import json
import time
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timezone


# ═══════════════════════════════════════════════════════════════
# Society Metabolic State Definitions
# ═══════════════════════════════════════════════════════════════

class SocietyState(str, Enum):
    ACTIVE = "active"            # 100% energy — full operational capacity
    REST = "rest"                # 40% energy — low activity, witness rotation
    SLEEP = "sleep"              # 15% energy — deep rest, minimal quorum
    HIBERNATION = "hibernation"  # 5% energy — extended dormancy, sentinel only
    TORPOR = "torpor"            # 2% energy — emergency conservation
    ESTIVATION = "estivation"    # 10% energy — protective dormancy (hostile env)
    DREAMING = "dreaming"        # 20% energy — memory consolidation
    MOLTING = "molting"           # 60% energy — structural renewal


# Energy multiplier relative to baseline
ENERGY_MULTIPLIERS: Dict[SocietyState, float] = {
    SocietyState.ACTIVE: 1.0,
    SocietyState.REST: 0.4,
    SocietyState.SLEEP: 0.15,
    SocietyState.HIBERNATION: 0.05,
    SocietyState.TORPOR: 0.02,
    SocietyState.ESTIVATION: 0.10,
    SocietyState.DREAMING: 0.20,
    SocietyState.MOLTING: 0.60,
}

# Trust tensor update rate (fraction of normal)
TRUST_UPDATE_RATES: Dict[SocietyState, float] = {
    SocietyState.ACTIVE: 1.0,
    SocietyState.REST: 0.9,
    SocietyState.SLEEP: 0.1,       # 10% decay rate
    SocietyState.HIBERNATION: 0.0,  # Frozen
    SocietyState.TORPOR: 0.0,       # Frozen + alert bonus
    SocietyState.ESTIVATION: 0.5,   # Internal only
    SocietyState.DREAMING: 0.0,     # Recalibration (special handling)
    SocietyState.MOLTING: 0.8,      # -20% temporary
}

# Minimum witness fraction required per state
WITNESS_REQUIREMENTS: Dict[SocietyState, float] = {
    SocietyState.ACTIVE: 1.0,       # All witnesses active
    SocietyState.REST: 0.3,         # 3 of 10
    SocietyState.SLEEP: 0.2,        # 2 of 10 (minimal quorum)
    SocietyState.HIBERNATION: 0.0,  # Sentinel only (1 witness always)
    SocietyState.TORPOR: 0.0,       # Reactive only
    SocietyState.ESTIVATION: 0.2,   # Defensive quorum
    SocietyState.DREAMING: 0.2,     # Monitoring during consolidation
    SocietyState.MOLTING: 0.5,      # Heightened security
}

# ATP recharge rate per heartbeat interval (per state)
RECHARGE_RATES: Dict[SocietyState, float] = {
    SocietyState.ACTIVE: 5.0,
    SocietyState.REST: 15.0,        # Good recharge during rest
    SocietyState.SLEEP: 25.0,       # Best recharge during sleep
    SocietyState.HIBERNATION: 2.0,  # Trickle
    SocietyState.TORPOR: 1.0,       # Minimal
    SocietyState.ESTIVATION: 3.0,   # Low
    SocietyState.DREAMING: 20.0,    # High (consolidation energy)
    SocietyState.MOLTING: 8.0,      # Moderate
}

# Wake penalty multipliers for interrupted cycles
WAKE_PENALTIES: Dict[SocietyState, float] = {
    SocietyState.SLEEP: 10.0,
    SocietyState.HIBERNATION: 100.0,
    SocietyState.DREAMING: 50.0,
}

# Heartbeat intervals (seconds) per state
HEARTBEAT_INTERVALS: Dict[SocietyState, int] = {
    SocietyState.ACTIVE: 60,
    SocietyState.REST: 300,
    SocietyState.SLEEP: 600,
    SocietyState.HIBERNATION: 3600,
    SocietyState.TORPOR: 7200,
    SocietyState.ESTIVATION: 1800,
    SocietyState.DREAMING: 900,
    SocietyState.MOLTING: 120,
}


# ═══════════════════════════════════════════════════════════════
# Transition Matrix
# ═══════════════════════════════════════════════════════════════

# Valid transitions: (from_state, to_state) → trigger_condition
TRANSITIONS: Dict[Tuple[SocietyState, SocietyState], str] = {
    # From Active
    (SocietyState.ACTIVE, SocietyState.REST): "no_transactions_1h",
    (SocietyState.ACTIVE, SocietyState.SLEEP): "scheduled_sleep",
    (SocietyState.ACTIVE, SocietyState.TORPOR): "atp_reserves_critical",
    (SocietyState.ACTIVE, SocietyState.DREAMING): "maintenance_window",
    (SocietyState.ACTIVE, SocietyState.MOLTING): "governance_change_approved",
    (SocietyState.ACTIVE, SocietyState.ESTIVATION): "threat_detected",
    # From Rest
    (SocietyState.REST, SocietyState.ACTIVE): "transaction_received",
    (SocietyState.REST, SocietyState.SLEEP): "no_activity_6h",
    # From Sleep
    (SocietyState.SLEEP, SocietyState.ACTIVE): "wake_trigger",
    (SocietyState.SLEEP, SocietyState.HIBERNATION): "no_activity_30d",
    # From Hibernation
    (SocietyState.HIBERNATION, SocietyState.ACTIVE): "external_wake",
    # From Torpor
    (SocietyState.TORPOR, SocietyState.ACTIVE): "energy_recharged",
    (SocietyState.TORPOR, SocietyState.HIBERNATION): "grace_period_expired",
    # From Estivation
    (SocietyState.ESTIVATION, SocietyState.ACTIVE): "threat_resolved",
    (SocietyState.ESTIVATION, SocietyState.HIBERNATION): "extended_duration",
    # From Dreaming
    (SocietyState.DREAMING, SocietyState.ACTIVE): "consolidation_complete",
    # From Molting
    (SocietyState.MOLTING, SocietyState.ACTIVE): "renewal_complete",
}


# ═══════════════════════════════════════════════════════════════
# Core Data Types
# ═══════════════════════════════════════════════════════════════

@dataclass
class SocietyWitness:
    """A witness entity in the society."""
    lct_id: str
    name: str
    is_sentinel: bool = False
    duty_cycles_served: int = 0
    last_attestation: float = 0.0
    trust_score: float = 0.5

    def attest(self):
        self.last_attestation = time.time()
        self.duty_cycles_served += 1


@dataclass
class StateTransition:
    """Record of a state transition on the ledger."""
    from_state: SocietyState
    to_state: SocietyState
    trigger: str
    timestamp: float
    witnesses_notified: List[str]
    checkpoint_hash: str
    wake_penalty: float = 0.0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "trigger": self.trigger,
            "timestamp": self.timestamp,
            "witnesses_notified": self.witnesses_notified,
            "checkpoint_hash": self.checkpoint_hash,
            "wake_penalty": self.wake_penalty,
            "metadata": self.metadata,
        }


@dataclass
class SocietyTrustTensor:
    """Society-level trust tensor with metabolic adjustments."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5

    def composite(self) -> float:
        return round((self.talent + self.training + self.temperament) / 3.0, 4)

    def apply_update(self, dimension: str, delta: float, rate: float):
        """Apply update with metabolic rate scaling."""
        scaled_delta = delta * rate
        current = getattr(self, dimension)
        new_val = max(0.0, min(1.0, current + scaled_delta))
        setattr(self, dimension, round(new_val, 4))

    def apply_molting_penalty(self):
        """Temporary -20% during molting."""
        self.talent = round(self.talent * 0.8, 4)
        self.training = round(self.training * 0.8, 4)
        self.temperament = round(self.temperament * 0.8, 4)

    def recalibrate(self, observations: List[float]):
        """Dreaming state recalibration from historical patterns."""
        if not observations:
            return
        avg = sum(observations) / len(observations)
        # EMA towards historical average
        alpha = 0.3
        self.talent = round(self.talent * (1 - alpha) + avg * alpha, 4)
        self.training = round(self.training * (1 - alpha) + avg * alpha, 4)
        self.temperament = round(self.temperament * (1 - alpha) + avg * alpha, 4)

    def to_dict(self) -> dict:
        return {
            "talent": self.talent,
            "training": self.training,
            "temperament": self.temperament,
            "composite": self.composite()
        }


# ═══════════════════════════════════════════════════════════════
# Witness Rotation
# ═══════════════════════════════════════════════════════════════

def deterministic_shuffle(items: list, seed: int) -> list:
    """Deterministic shuffle based on seed — no randomness."""
    result = list(items)
    n = len(result)
    for i in range(n - 1, 0, -1):
        j = seed % (i + 1)
        result[i], result[j] = result[j], result[i]
        seed = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
    return result


def select_active_witnesses(
    witnesses: List[SocietyWitness],
    state: SocietyState,
    block_height: int,
    society_lct: str,
    cycle_length: int = 100
) -> List[SocietyWitness]:
    """Select witnesses for current duty cycle based on metabolic state."""
    if not witnesses:
        return []

    # Sentinel always included for dormant states
    sentinels = [w for w in witnesses if w.is_sentinel]

    required_fraction = WITNESS_REQUIREMENTS[state]
    required_count = max(1, int(len(witnesses) * required_fraction))

    if state in (SocietyState.HIBERNATION, SocietyState.TORPOR):
        # Only sentinel(s) for deep dormancy
        return sentinels if sentinels else [witnesses[0]]

    # Deterministic rotation
    cycle = block_height // cycle_length
    seed_str = f"{cycle}:{society_lct}"
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest()[:16], 16)

    shuffled = deterministic_shuffle(witnesses, seed)
    selected = shuffled[:required_count]

    # Ensure sentinel is always in the rotation
    for s in sentinels:
        if s not in selected:
            selected.append(s)

    return selected


# ═══════════════════════════════════════════════════════════════
# Sentinel Witness
# ═══════════════════════════════════════════════════════════════

@dataclass
class SentinelWitness:
    """Minimal monitoring during dormant states."""
    society_lct: str
    heartbeat_interval: int = 60
    wake_triggers: List[str] = field(default_factory=list)
    heartbeats_sent: int = 0
    alerts_raised: int = 0

    def send_heartbeat(self) -> dict:
        self.heartbeats_sent += 1
        return {
            "type": "sentinel_heartbeat",
            "society": self.society_lct,
            "sequence": self.heartbeats_sent,
            "timestamp": time.time()
        }

    def check_wake_triggers(self, events: List[str]) -> Optional[str]:
        """Check if any events match wake triggers."""
        for event in events:
            for trigger in self.wake_triggers:
                if trigger in event:
                    self.alerts_raised += 1
                    return trigger
        return None


# ═══════════════════════════════════════════════════════════════
# Society Metabolic Manager
# ═══════════════════════════════════════════════════════════════

class SocietyMetabolicManager:
    """
    Full 8-state society lifecycle manager.

    Manages state transitions, witness rotation, ATP costs,
    trust tensor adjustments, and metabolic reliability scoring.
    """

    def __init__(
        self,
        society_lct: str,
        baseline_atp_per_hour: float = 100.0,
        initial_atp: float = 1000.0,
        atp_cap: float = 5000.0,
    ):
        self.society_lct = society_lct
        self.state = SocietyState.ACTIVE
        self.baseline_atp_per_hour = baseline_atp_per_hour
        self.atp_balance = initial_atp
        self.atp_cap = atp_cap

        # Witnesses
        self.witnesses: List[SocietyWitness] = []
        self.sentinel: Optional[SentinelWitness] = None

        # Trust
        self.trust = SocietyTrustTensor()
        self._pre_molt_trust: Optional[Dict] = None

        # State tracking
        self.transition_log: List[StateTransition] = []
        self.state_entered_at: float = time.time()
        self.state_planned_duration: Optional[float] = None
        self.transaction_count: int = 0
        self.last_transaction_at: float = time.time()
        self.block_height: int = 0
        self.threat_score: float = 0.0

        # Metabolic reliability
        self._scheduled_transitions: int = 0
        self._on_time_transitions: int = 0
        self._hibernation_wakes: int = 0
        self._successful_hibernation_wakes: int = 0
        self._molts: int = 0
        self._successful_molts: int = 0
        self._total_atp_spent: float = 0.0
        self._total_atp_recharged: float = 0.0

        # Dreaming
        self._historical_observations: List[float] = []

        # Ledger
        self._ledger_sealed: bool = False
        self._treasury_locked: bool = False
        self._new_citizens_queued: List[str] = []
        self._transactions_accepted: bool = True

    # ─── State Transitions ────────────────────────────────

    def can_transition(self, to_state: SocietyState) -> Tuple[bool, str]:
        """Check if a transition is valid."""
        key = (self.state, to_state)
        if key not in TRANSITIONS:
            return False, f"No valid transition from {self.state.value} to {to_state.value}"
        return True, TRANSITIONS[key]

    def transition(self, to_state: SocietyState, trigger: str,
                   planned_duration: Optional[float] = None) -> StateTransition:
        """Execute a state transition with full safety protocol."""
        valid, reason = self.can_transition(to_state)
        if not valid:
            raise ValueError(reason)

        # 1. Checkpoint current state
        checkpoint = self._create_checkpoint()

        # 2. Calculate wake penalty (if leaving dormant state early)
        wake_penalty = self._calculate_wake_penalty()

        # 3. Notify witnesses
        active_witnesses = select_active_witnesses(
            self.witnesses, self.state, self.block_height, self.society_lct
        )
        notified = [w.lct_id for w in active_witnesses]

        # 4. Apply state-specific entry logic
        self._on_exit_state(self.state)
        from_state = self.state
        self.state = to_state
        self.state_entered_at = time.time()
        self.state_planned_duration = planned_duration
        self._on_enter_state(to_state)

        # 5. Apply wake penalty
        if wake_penalty > 0:
            self.atp_balance = max(0, self.atp_balance - wake_penalty)

        # 6. Record transition
        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            timestamp=time.time(),
            witnesses_notified=notified,
            checkpoint_hash=checkpoint,
            wake_penalty=wake_penalty,
            metadata={
                "atp_balance": round(self.atp_balance, 2),
                "trust_composite": self.trust.composite(),
                "block_height": self.block_height,
            }
        )
        self.transition_log.append(transition)
        return transition

    def _on_enter_state(self, state: SocietyState):
        """Apply entry effects for a state."""
        if state == SocietyState.HIBERNATION:
            self._ledger_sealed = True
            self._treasury_locked = True
            self._transactions_accepted = False
        elif state == SocietyState.TORPOR:
            self._transactions_accepted = False
        elif state == SocietyState.ESTIVATION:
            self._transactions_accepted = False
        elif state == SocietyState.DREAMING:
            self._transactions_accepted = False
        elif state == SocietyState.MOLTING:
            self._pre_molt_trust = self.trust.to_dict()
            self.trust.apply_molting_penalty()
            self._molts += 1
        elif state == SocietyState.SLEEP:
            self._transactions_accepted = False
        elif state == SocietyState.REST:
            # Still accepts transactions (that's what wakes it up)
            self._transactions_accepted = True
        elif state == SocietyState.ACTIVE:
            self._ledger_sealed = False
            self._treasury_locked = False
            self._transactions_accepted = True

    def _on_exit_state(self, state: SocietyState):
        """Apply exit effects for a state."""
        if state == SocietyState.MOLTING:
            self._successful_molts += 1
        elif state == SocietyState.HIBERNATION:
            self._hibernation_wakes += 1
            self._successful_hibernation_wakes += 1
        elif state == SocietyState.DREAMING:
            # Apply recalibration
            self.trust.recalibrate(self._historical_observations)

    def _calculate_wake_penalty(self) -> float:
        """Calculate ATP penalty for premature wake from dormant state."""
        if self.state not in WAKE_PENALTIES:
            return 0.0
        if self.state_planned_duration is None:
            return 0.0

        actual_duration = time.time() - self.state_entered_at
        if actual_duration >= self.state_planned_duration:
            return 0.0

        incompleteness = 1.0 - (actual_duration / self.state_planned_duration)
        return WAKE_PENALTIES[self.state] * incompleteness

    def _create_checkpoint(self) -> str:
        """Create a state checkpoint hash."""
        data = json.dumps({
            "state": self.state.value,
            "atp": round(self.atp_balance, 2),
            "trust": self.trust.to_dict(),
            "block_height": self.block_height,
            "transaction_count": self.transaction_count,
            "timestamp": time.time(),
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    # ─── ATP Economics ────────────────────────────────────

    def compute_hourly_cost(self, society_size: int = 1) -> float:
        """Compute ATP cost per hour for current state."""
        multiplier = ENERGY_MULTIPLIERS[self.state]
        return self.baseline_atp_per_hour * multiplier * society_size

    def tick_heartbeat(self, society_size: int = 1):
        """Process one heartbeat interval: deduct cost, apply recharge."""
        interval_hours = HEARTBEAT_INTERVALS[self.state] / 3600.0

        # Deduct energy cost
        cost = self.compute_hourly_cost(society_size) * interval_hours
        self.atp_balance -= cost
        self._total_atp_spent += cost

        # Apply recharge
        recharge = RECHARGE_RATES[self.state] * interval_hours
        old_balance = self.atp_balance
        self.atp_balance = min(self.atp_cap, self.atp_balance + recharge)
        self._total_atp_recharged += (self.atp_balance - old_balance)

        self.block_height += 1

        # Auto-torpor if ATP critical
        if self.atp_balance < self.atp_cap * 0.10 and self.state == SocietyState.ACTIVE:
            # Don't auto-transition here, just flag it
            pass

        return {
            "state": self.state.value,
            "cost": round(cost, 4),
            "recharge": round(recharge, 4),
            "balance": round(self.atp_balance, 2),
            "block_height": self.block_height,
        }

    # ─── Trust Tensor Management ──────────────────────────

    def update_trust(self, dimension: str, delta: float):
        """Update trust tensor with metabolic rate scaling."""
        rate = TRUST_UPDATE_RATES[self.state]
        if rate == 0.0 and self.state != SocietyState.DREAMING:
            return  # Frozen
        self.trust.apply_update(dimension, delta, rate)

    def add_observation(self, score: float):
        """Add historical observation for dreaming recalibration."""
        self._historical_observations.append(score)
        # Keep last 100
        if len(self._historical_observations) > 100:
            self._historical_observations = self._historical_observations[-100:]

    # ─── Witness Management ───────────────────────────────

    def add_witness(self, lct_id: str, name: str, is_sentinel: bool = False):
        """Register a witness."""
        witness = SocietyWitness(lct_id=lct_id, name=name, is_sentinel=is_sentinel)
        self.witnesses.append(witness)
        if is_sentinel:
            self.sentinel = SentinelWitness(
                society_lct=self.society_lct,
                wake_triggers=["new_citizen", "external_witness", "emergency"]
            )
        return witness

    def get_active_witnesses(self) -> List[SocietyWitness]:
        """Get currently active witnesses for this state."""
        return select_active_witnesses(
            self.witnesses, self.state, self.block_height, self.society_lct
        )

    # ─── Transaction Handling ─────────────────────────────

    def submit_transaction(self, tx_type: str, data: dict) -> Tuple[bool, str]:
        """Submit a transaction, respecting metabolic state constraints."""
        if not self._transactions_accepted:
            if self.state == SocietyState.REST:
                # Rest accepts transactions (wakes society)
                pass
            else:
                return False, f"Transactions not accepted in {self.state.value} state"

        if self._ledger_sealed:
            return False, "Ledger is sealed (hibernation)"

        if self._treasury_locked and tx_type in ("transfer", "allocation"):
            return False, "Treasury is locked"

        self.transaction_count += 1
        self.last_transaction_at = time.time()
        return True, "accepted"

    def queue_citizen(self, citizen_lct: str):
        """Queue a citizenship request (for non-active states)."""
        if self.state == SocietyState.ACTIVE:
            return True, "Accepted immediately"
        self._new_citizens_queued.append(citizen_lct)
        return False, f"Queued for {self.state.value} → active transition"

    # ─── Metabolic Reliability ────────────────────────────

    def metabolic_reliability_score(self) -> float:
        """Calculate reliability score based on predictable metabolic cycles."""
        score = 0.0

        # Predictable transitions (scheduled = on time)
        if self._scheduled_transitions > 0:
            schedule_adherence = self._on_time_transitions / self._scheduled_transitions
            score += 0.3 * schedule_adherence
        elif self._scheduled_transitions == 0:
            score += 0.3  # No schedule violations = perfect

        # Successful hibernation recovery
        if self._hibernation_wakes > 0:
            recovery_rate = self._successful_hibernation_wakes / self._hibernation_wakes
            score += 0.2 * recovery_rate
        elif self._hibernation_wakes == 0:
            score += 0.2  # No failures = perfect score

        # Energy efficiency
        if self._total_atp_spent > 0:
            efficiency = min(1.0, self._total_atp_recharged / self._total_atp_spent)
            score += 0.3 * efficiency
        else:
            score += 0.3  # No spending = efficient

        # Successful molts
        if self._molts > 0:
            molt_rate = self._successful_molts / self._molts
            score += 0.2 * molt_rate
        elif self._molts == 0:
            score += 0.2  # No failures = perfect score

        return round(min(1.0, score), 4)

    # ─── Security Checks ─────────────────────────────────

    def check_sleep_deprivation(self, wake_requests_per_hour: int) -> bool:
        """Detect sleep deprivation attack (rate-limit wake triggers)."""
        return wake_requests_per_hour > 10  # Threshold

    def check_hibernation_timeout(self, max_days: int = 90) -> bool:
        """Ensure hibernation doesn't exceed timeout (dead-man switch)."""
        if self.state != SocietyState.HIBERNATION:
            return False
        elapsed_days = (time.time() - self.state_entered_at) / 86400
        return elapsed_days > max_days

    def check_torpor_reserves(self, minimum_atp: float = 10.0) -> bool:
        """Check if torpor has exhausted protected minimum reserves."""
        return self.state == SocietyState.TORPOR and self.atp_balance < minimum_atp

    # ─── Status & Reporting ───────────────────────────────

    def status(self) -> dict:
        """Complete metabolic status snapshot."""
        return {
            "society_lct": self.society_lct,
            "state": self.state.value,
            "energy_multiplier": ENERGY_MULTIPLIERS[self.state],
            "atp_balance": round(self.atp_balance, 2),
            "trust": self.trust.to_dict(),
            "heartbeat_interval": HEARTBEAT_INTERVALS[self.state],
            "witness_requirement": WITNESS_REQUIREMENTS[self.state],
            "active_witnesses": len(self.get_active_witnesses()),
            "total_witnesses": len(self.witnesses),
            "block_height": self.block_height,
            "transactions_accepted": self._transactions_accepted,
            "ledger_sealed": self._ledger_sealed,
            "treasury_locked": self._treasury_locked,
            "queued_citizens": len(self._new_citizens_queued),
            "transition_count": len(self.transition_log),
            "metabolic_reliability": self.metabolic_reliability_score(),
        }


# ═══════════════════════════════════════════════════════════════
# Test Suite
# ═══════════════════════════════════════════════════════════════

def main():
    passed = 0
    failed = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal passed, failed
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
        if condition:
            passed += 1
        else:
            failed += 1
        return condition

    # ─── T1: State enumeration ─────────────────────────────
    print("\n═══ T1: State Enumeration ═══")
    check("T1: 8 metabolic states defined", len(SocietyState) == 8,
          f"count={len(SocietyState)}")
    check("T1: All states have energy multipliers",
          all(s in ENERGY_MULTIPLIERS for s in SocietyState))
    check("T1: All states have trust update rates",
          all(s in TRUST_UPDATE_RATES for s in SocietyState))
    check("T1: All states have heartbeat intervals",
          all(s in HEARTBEAT_INTERVALS for s in SocietyState))
    check("T1: Energy ordering correct",
          ENERGY_MULTIPLIERS[SocietyState.TORPOR] < ENERGY_MULTIPLIERS[SocietyState.HIBERNATION]
          < ENERGY_MULTIPLIERS[SocietyState.ESTIVATION] < ENERGY_MULTIPLIERS[SocietyState.SLEEP]
          < ENERGY_MULTIPLIERS[SocietyState.DREAMING] < ENERGY_MULTIPLIERS[SocietyState.REST]
          < ENERGY_MULTIPLIERS[SocietyState.MOLTING] < ENERGY_MULTIPLIERS[SocietyState.ACTIVE])

    # ─── T2: Transition matrix ─────────────────────────────
    print("\n═══ T2: Transition Matrix ═══")
    check("T2: 17 valid transitions defined", len(TRANSITIONS) == 17,
          f"count={len(TRANSITIONS)}")

    # Active can reach 6 states
    active_targets = [t for (f, t) in TRANSITIONS if f == SocietyState.ACTIVE]
    check("T2: Active can reach 6 states", len(active_targets) == 6,
          f"targets={[s.value for s in active_targets]}")

    # Every non-Active state can reach Active
    for state in SocietyState:
        if state == SocietyState.ACTIVE:
            continue
        can_reach_active = any(f == state and t == SocietyState.ACTIVE
                               for f, t in TRANSITIONS)
        check(f"T2: {state.value} → active path exists", can_reach_active)

    # ─── T3: Basic lifecycle ───────────────────────────────
    print("\n═══ T3: Basic Society Lifecycle ═══")
    mgr = SocietyMetabolicManager("lct:web4:test-society", initial_atp=1000.0)

    # Add witnesses
    for i in range(5):
        mgr.add_witness(f"lct:web4:witness-{i}", f"witness-{i}", is_sentinel=(i == 0))

    check("T3: Initial state is Active", mgr.state == SocietyState.ACTIVE)
    check("T3: 5 witnesses registered", len(mgr.witnesses) == 5)
    check("T3: Sentinel assigned", mgr.sentinel is not None)
    check("T3: Transactions accepted", mgr._transactions_accepted)

    # Transition to Rest
    t = mgr.transition(SocietyState.REST, "no_transactions_1h")
    check("T3: Transitioned to Rest", mgr.state == SocietyState.REST)
    check("T3: Transition recorded", len(mgr.transition_log) == 1)
    check("T3: Witnesses notified", len(t.witnesses_notified) > 0,
          f"notified={t.witnesses_notified}")

    # ─── T4: Witness rotation ─────────────────────────────
    print("\n═══ T4: Witness Rotation ═══")
    # In Rest state, only 30% of witnesses should be active (≈2 of 5)
    active = mgr.get_active_witnesses()
    check("T4: Reduced witness count in Rest", len(active) <= 3,
          f"active={len(active)}, total={len(mgr.witnesses)}")

    # Rotation changes with block height — use a larger pool to make rotation visible
    mgr_rot = SocietyMetabolicManager("lct:web4:rot-test", initial_atp=1000.0)
    for i in range(20):
        mgr_rot.add_witness(f"lct:web4:rw-{i}", f"rw-{i}", is_sentinel=(i == 0))
    mgr_rot.transition(SocietyState.REST, "no_transactions_1h")

    mgr_rot.block_height = 100
    active_100 = set(w.lct_id for w in mgr_rot.get_active_witnesses())
    mgr_rot.block_height = 200
    active_200 = set(w.lct_id for w in mgr_rot.get_active_witnesses())
    check("T4: Rotation changes across cycles", active_100 != active_200,
          f"cycle 1 ({len(active_100)}): {sorted(active_100)[:3]}..., cycle 2 ({len(active_200)}): {sorted(active_200)[:3]}...")

    # Sentinel always included
    sentinel_in_rotation = any(w.is_sentinel for w in mgr.get_active_witnesses())
    check("T4: Sentinel always in rotation", sentinel_in_rotation)

    # ─── T5: ATP economics ─────────────────────────────────
    print("\n═══ T5: ATP Economics ═══")
    mgr2 = SocietyMetabolicManager("lct:web4:econ-test", initial_atp=500.0)

    # Active cost
    active_cost = mgr2.compute_hourly_cost(society_size=1)
    check("T5: Active hourly cost = 100 ATP", active_cost == 100.0,
          f"cost={active_cost}")

    # Rest cost
    mgr2.transition(SocietyState.REST, "no_transactions_1h")
    rest_cost = mgr2.compute_hourly_cost()
    check("T5: Rest hourly cost = 40 ATP", rest_cost == 40.0,
          f"cost={rest_cost}")

    # Heartbeat tick
    result = mgr2.tick_heartbeat()
    check("T5: Heartbeat deducts cost", result["cost"] > 0,
          f"cost={result['cost']}")
    check("T5: Heartbeat applies recharge", result["recharge"] > 0,
          f"recharge={result['recharge']}")
    check("T5: Balance updated", result["balance"] < 500.0)
    check("T5: Block height incremented", result["block_height"] == 1)

    # Torpor has lowest cost
    mgr3 = SocietyMetabolicManager("lct:web4:torpor-test", initial_atp=50.0)
    mgr3.transition(SocietyState.TORPOR, "atp_reserves_critical")
    torpor_cost = mgr3.compute_hourly_cost()
    check("T5: Torpor hourly cost = 2 ATP", torpor_cost == 2.0,
          f"cost={torpor_cost}")

    # ─── T6: Trust tensor adjustments ──────────────────────
    print("\n═══ T6: Trust Tensor Adjustments ═══")
    mgr4 = SocietyMetabolicManager("lct:web4:trust-test", initial_atp=1000.0)

    # Active: full update rate
    mgr4.update_trust("talent", 0.1)
    check("T6: Active trust update at full rate", mgr4.trust.talent == 0.6,
          f"talent={mgr4.trust.talent}")

    # Rest: 90% rate
    mgr4.transition(SocietyState.REST, "no_transactions_1h")
    mgr4.trust.talent = 0.5
    mgr4.update_trust("talent", 0.1)
    check("T6: Rest trust update at 90%", abs(mgr4.trust.talent - 0.59) < 0.001,
          f"talent={mgr4.trust.talent}")

    # Hibernation: frozen
    mgr4.transition(SocietyState.ACTIVE, "transaction_received")
    mgr4.transition(SocietyState.SLEEP, "scheduled_sleep")
    mgr4.transition(SocietyState.HIBERNATION, "no_activity_30d")
    frozen_talent = mgr4.trust.talent
    mgr4.update_trust("talent", 0.5)
    check("T6: Hibernation trust frozen", mgr4.trust.talent == frozen_talent,
          f"talent unchanged at {mgr4.trust.talent}")

    # ─── T7: Molting ───────────────────────────────────────
    print("\n═══ T7: Molting State ═══")
    mgr5 = SocietyMetabolicManager("lct:web4:molt-test", initial_atp=1000.0)
    mgr5.trust = SocietyTrustTensor(0.8, 0.8, 0.8)
    pre_molt = mgr5.trust.composite()

    mgr5.transition(SocietyState.MOLTING, "governance_change_approved")
    post_molt = mgr5.trust.composite()
    check("T7: Molting reduces trust by ~20%", post_molt < pre_molt,
          f"pre={pre_molt:.4f}, post={post_molt:.4f}")
    check("T7: Trust ≈ 0.64 (80% of 0.8)", abs(mgr5.trust.talent - 0.64) < 0.01,
          f"talent={mgr5.trust.talent}")

    # Complete molt → back to active
    mgr5.transition(SocietyState.ACTIVE, "renewal_complete")
    check("T7: Molt recorded", mgr5._molts == 1)
    check("T7: Successful molt recorded", mgr5._successful_molts == 1)

    # ─── T8: Dreaming state ───────────────────────────────
    print("\n═══ T8: Dreaming State ═══")
    mgr6 = SocietyMetabolicManager("lct:web4:dream-test", initial_atp=1000.0)
    mgr6.trust = SocietyTrustTensor(0.3, 0.3, 0.3)

    # Add historical observations of higher quality
    for score in [0.7, 0.8, 0.75, 0.65, 0.9]:
        mgr6.add_observation(score)

    mgr6.transition(SocietyState.DREAMING, "maintenance_window")
    check("T8: Dreaming state entered", mgr6.state == SocietyState.DREAMING)
    check("T8: Transactions blocked", not mgr6._transactions_accepted)

    # Exit dreaming triggers recalibration
    pre_dream = mgr6.trust.composite()
    mgr6.transition(SocietyState.ACTIVE, "consolidation_complete")
    post_dream = mgr6.trust.composite()
    check("T8: Recalibration moved trust toward observations",
          post_dream > pre_dream,
          f"pre={pre_dream:.4f}, post={post_dream:.4f}")

    # ─── T9: Transaction constraints ──────────────────────
    print("\n═══ T9: State-Specific Transaction Constraints ═══")
    mgr7 = SocietyMetabolicManager("lct:web4:tx-test", initial_atp=1000.0)

    # Active: accept everything
    ok, msg = mgr7.submit_transaction("transfer", {"amount": 10})
    check("T9: Active accepts transactions", ok, msg)

    # Hibernation: reject everything
    mgr7.transition(SocietyState.SLEEP, "scheduled_sleep")
    mgr7.transition(SocietyState.HIBERNATION, "no_activity_30d")
    ok, msg = mgr7.submit_transaction("transfer", {"amount": 10})
    check("T9: Hibernation rejects transactions", not ok, msg)
    check("T9: Ledger sealed in hibernation", mgr7._ledger_sealed)
    check("T9: Treasury locked in hibernation", mgr7._treasury_locked)

    # Torpor: reject
    mgr8 = SocietyMetabolicManager("lct:web4:torpor-tx", initial_atp=1000.0)
    mgr8.transition(SocietyState.TORPOR, "atp_reserves_critical")
    ok, msg = mgr8.submit_transaction("action", {})
    check("T9: Torpor rejects transactions", not ok, msg)

    # Estivation: reject external
    mgr9 = SocietyMetabolicManager("lct:web4:estiv-tx", initial_atp=1000.0)
    mgr9.transition(SocietyState.ESTIVATION, "threat_detected")
    ok, msg = mgr9.submit_transaction("external", {})
    check("T9: Estivation rejects transactions", not ok, msg)

    # ─── T10: Wake penalties ──────────────────────────────
    print("\n═══ T10: Wake Penalties ═══")
    mgr10 = SocietyMetabolicManager("lct:web4:wake-test", initial_atp=1000.0)

    # Sleep with planned 8h duration
    mgr10.transition(SocietyState.SLEEP, "scheduled_sleep", planned_duration=28800)
    # Immediately wake (0% completion)
    mgr10.state_entered_at = time.time() - 1  # 1 second ago
    pre_wake_atp = mgr10.atp_balance
    t = mgr10.transition(SocietyState.ACTIVE, "wake_trigger")
    check("T10: Wake penalty applied", t.wake_penalty > 0,
          f"penalty={t.wake_penalty:.2f}")
    check("T10: ATP deducted for early wake", mgr10.atp_balance < pre_wake_atp,
          f"before={pre_wake_atp:.2f}, after={mgr10.atp_balance:.2f}")

    # No penalty for completed duration
    mgr11 = SocietyMetabolicManager("lct:web4:full-sleep", initial_atp=1000.0)
    mgr11.transition(SocietyState.SLEEP, "scheduled_sleep", planned_duration=100)
    mgr11.state_entered_at = time.time() - 200  # Completed
    t = mgr11.transition(SocietyState.ACTIVE, "wake_trigger")
    check("T10: No penalty for completed sleep", t.wake_penalty == 0.0)

    # ─── T11: Invalid transitions ─────────────────────────
    print("\n═══ T11: Invalid Transition Prevention ═══")
    mgr12 = SocietyMetabolicManager("lct:web4:invalid-test", initial_atp=1000.0)

    # Can't go Active → Hibernation directly
    valid, reason = mgr12.can_transition(SocietyState.HIBERNATION)
    check("T11: Active → Hibernation blocked", not valid,
          f"reason={reason}")

    # Can't go Rest → Molting
    mgr12.transition(SocietyState.REST, "no_transactions_1h")
    valid, reason = mgr12.can_transition(SocietyState.MOLTING)
    check("T11: Rest → Molting blocked", not valid)

    # Can't go Hibernation → Rest
    mgr13 = SocietyMetabolicManager("lct:web4:inv2", initial_atp=1000.0)
    mgr13.transition(SocietyState.SLEEP, "scheduled_sleep")
    mgr13.transition(SocietyState.HIBERNATION, "no_activity_30d")
    valid, reason = mgr13.can_transition(SocietyState.REST)
    check("T11: Hibernation → Rest blocked", not valid)

    # ValueError on forced invalid transition
    try:
        mgr13.transition(SocietyState.DREAMING, "random")
        check("T11: Invalid transition raises error", False)
    except ValueError:
        check("T11: Invalid transition raises ValueError", True)

    # ─── T12: Sentinel witness ─────────────────────────────
    print("\n═══ T12: Sentinel Witness ═══")
    sentinel = SentinelWitness(
        society_lct="lct:web4:sentinel-test",
        wake_triggers=["new_citizen", "emergency", "external_witness"]
    )

    hb = sentinel.send_heartbeat()
    check("T12: Sentinel sends heartbeats", hb["type"] == "sentinel_heartbeat")
    check("T12: Heartbeat has sequence", hb["sequence"] == 1)

    # No trigger match
    result = sentinel.check_wake_triggers(["normal_event", "routine_check"])
    check("T12: No false wake triggers", result is None)

    # Trigger match
    result = sentinel.check_wake_triggers(["new_citizen_application"])
    check("T12: Wake trigger detected", result == "new_citizen")
    check("T12: Alert counted", sentinel.alerts_raised == 1)

    # ─── T13: Metabolic reliability ────────────────────────
    print("\n═══ T13: Metabolic Reliability Score ═══")
    mgr14 = SocietyMetabolicManager("lct:web4:reliability-test", initial_atp=1000.0)

    # Perfect reliability with no history
    score = mgr14.metabolic_reliability_score()
    check("T13: Baseline reliability = 1.0 (no failures)", score == 1.0,
          f"score={score}")

    # Simulate some history
    mgr14._scheduled_transitions = 10
    mgr14._on_time_transitions = 8
    mgr14._hibernation_wakes = 5
    mgr14._successful_hibernation_wakes = 5
    mgr14._total_atp_spent = 100
    mgr14._total_atp_recharged = 80
    mgr14._molts = 3
    mgr14._successful_molts = 3

    score = mgr14.metabolic_reliability_score()
    check("T13: Reliability with history", 0.5 < score < 1.0,
          f"score={score}")

    # Bad reliability
    mgr14._on_time_transitions = 2
    mgr14._successful_hibernation_wakes = 1
    mgr14._successful_molts = 1
    mgr14._total_atp_recharged = 10
    bad_score = mgr14.metabolic_reliability_score()
    check("T13: Bad reliability < good reliability", bad_score < score,
          f"bad={bad_score}, good={score}")

    # ─── T14: Security checks ─────────────────────────────
    print("\n═══ T14: Security Checks ═══")
    mgr15 = SocietyMetabolicManager("lct:web4:security-test", initial_atp=1000.0)

    # Sleep deprivation detection
    check("T14: Normal wake rate OK", not mgr15.check_sleep_deprivation(5))
    check("T14: Sleep deprivation detected", mgr15.check_sleep_deprivation(15),
          "wake_requests=15/hour")

    # Torpor reserve check
    mgr15.transition(SocietyState.TORPOR, "atp_reserves_critical")
    mgr15.atp_balance = 5.0
    check("T14: Torpor reserve exhaustion detected", mgr15.check_torpor_reserves(10.0),
          f"balance={mgr15.atp_balance}")

    # ─── T15: Full lifecycle simulation ────────────────────
    print("\n═══ T15: Full Lifecycle Simulation ═══")
    society = SocietyMetabolicManager(
        "lct:web4:lifecycle-society",
        baseline_atp_per_hour=100.0,
        initial_atp=2000.0,
        atp_cap=5000.0,
    )

    # Register 10 witnesses with 1 sentinel
    for i in range(10):
        society.add_witness(f"lct:web4:w-{i}", f"witness-{i}", is_sentinel=(i == 0))

    check("T15: Society initialized", society.state == SocietyState.ACTIVE)

    # Day 1: Active operations
    for _ in range(5):
        society.tick_heartbeat(society_size=1)
    society.submit_transaction("code_review", {"reviewer": "alice"})
    check("T15: Active operations", society.transaction_count == 1)

    # Evening: Rest
    society.transition(SocietyState.REST, "no_transactions_1h")
    for _ in range(3):
        society.tick_heartbeat()
    check("T15: Rest period", society.state == SocietyState.REST)

    # Night: Sleep
    society.transition(SocietyState.SLEEP, "no_activity_6h", planned_duration=28800)
    for _ in range(3):
        society.tick_heartbeat()
    sleep_balance = society.atp_balance
    check("T15: Sleep recharges ATP", sleep_balance > 0)

    # Morning: Wake
    society.state_entered_at = time.time() - 30000  # Simulated full sleep
    society.transition(SocietyState.ACTIVE, "wake_trigger")
    check("T15: Wake from sleep", society.state == SocietyState.ACTIVE)

    # Threat → Estivation
    society.transition(SocietyState.ESTIVATION, "threat_detected")
    ok, msg = society.submit_transaction("external", {})
    check("T15: Estivation blocks transactions", not ok)

    # Threat resolved
    society.transition(SocietyState.ACTIVE, "threat_resolved")
    ok, msg = society.submit_transaction("internal", {})
    check("T15: Active after estivation", ok)

    # Maintenance window → Dreaming
    society.add_observation(0.8)
    society.add_observation(0.75)
    society.transition(SocietyState.DREAMING, "maintenance_window")
    society.transition(SocietyState.ACTIVE, "consolidation_complete")
    check("T15: Dream cycle complete", society.state == SocietyState.ACTIVE)

    # Governance change → Molting
    pre_molt_trust = society.trust.composite()
    society.transition(SocietyState.MOLTING, "governance_change_approved")
    check("T15: Molting reduces trust", society.trust.composite() < pre_molt_trust)
    society.transition(SocietyState.ACTIVE, "renewal_complete")
    check("T15: Molt complete", society._successful_molts == 1)

    # Full status
    status = society.status()
    check("T15: Status includes all fields", all(k in status for k in
          ["state", "atp_balance", "trust", "metabolic_reliability"]))
    check("T15: Transition log complete", len(society.transition_log) >= 8,
          f"transitions={len(society.transition_log)}")

    # ─── T16: Citizen queuing ──────────────────────────────
    print("\n═══ T16: Citizen Queuing ═══")
    mgr16 = SocietyMetabolicManager("lct:web4:queue-test", initial_atp=1000.0)

    # Active: immediate acceptance
    ok, msg = mgr16.queue_citizen("lct:web4:new-citizen-1")
    check("T16: Active accepts citizens immediately", ok)

    # Sleep: queue
    mgr16.transition(SocietyState.SLEEP, "scheduled_sleep")
    ok, msg = mgr16.queue_citizen("lct:web4:new-citizen-2")
    check("T16: Sleep queues citizens", not ok)
    check("T16: Citizen in queue", len(mgr16._new_citizens_queued) == 1)

    # ─── T17: Dormant state witness behavior ──────────────
    print("\n═══ T17: Dormant State Witness Behavior ═══")
    mgr17 = SocietyMetabolicManager("lct:web4:dormant-test", initial_atp=1000.0)
    for i in range(8):
        mgr17.add_witness(f"lct:web4:dw-{i}", f"dw-{i}", is_sentinel=(i == 0))

    # Hibernation: sentinel only
    mgr17.transition(SocietyState.SLEEP, "scheduled_sleep")
    mgr17.transition(SocietyState.HIBERNATION, "no_activity_30d")
    hib_witnesses = mgr17.get_active_witnesses()
    check("T17: Hibernation uses sentinel only", len(hib_witnesses) == 1,
          f"active={len(hib_witnesses)}")
    check("T17: Active witness is sentinel", hib_witnesses[0].is_sentinel)

    # ─── T18: State snapshot/checkpoint ────────────────────
    print("\n═══ T18: State Checkpoints ═══")
    mgr18 = SocietyMetabolicManager("lct:web4:checkpoint-test", initial_atp=1000.0)
    cp1 = mgr18._create_checkpoint()
    check("T18: Checkpoint is SHA-256 hash", len(cp1) == 64)

    # Different state → different checkpoint
    mgr18.atp_balance = 500.0
    cp2 = mgr18._create_checkpoint()
    check("T18: Different state → different checkpoint", cp1 != cp2)

    # Checkpoint recorded in transition
    mgr18.transition(SocietyState.REST, "no_transactions_1h")
    check("T18: Transition has checkpoint",
          len(mgr18.transition_log[0].checkpoint_hash) == 64)

    # ─── T19: Transition serialization ─────────────────────
    print("\n═══ T19: Transition Serialization ═══")
    t = mgr18.transition_log[0]
    d = t.to_dict()
    check("T19: Transition serializes to dict", isinstance(d, dict))
    check("T19: Has from_state", d["from_state"] == "active")
    check("T19: Has to_state", d["to_state"] == "rest")
    check("T19: Has metadata with ATP", "atp_balance" in d["metadata"])

    # JSON roundtrip
    json_str = json.dumps(d, default=str)
    check("T19: JSON-serializable", len(json_str) > 0)

    # ─── Summary ──────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Society Metabolic States — Track I Results")
    print(f"  {passed} passed, {failed} failed out of {passed+failed} checks")
    print(f"{'='*60}")

    return passed, failed


if __name__ == "__main__":
    passed, failed = main()
    sys.exit(0 if failed == 0 else 1)
