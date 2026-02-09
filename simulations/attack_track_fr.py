#!/usr/bin/env python3
"""
Track FR: Heartbeat and Metabolic State Attacks (359-364)

Attacks on the adaptive timing mechanism (heartbeat) and metabolic state
that governs entity activity levels and ledger block timing.

Author: Autonomous Research Session
Date: 2026-02-09
Track: FR (Attack vectors 359-364)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import random


class MetabolicState(Enum):
    ACTIVE = "active"
    DORMANT = "dormant"
    STRESSED = "stressed"
    RECOVERING = "recovering"
    HIBERNATING = "hibernating"


@dataclass
class HeartbeatEvent:
    event_id: str
    timestamp: datetime
    entity_id: str
    interval_ms: int
    metabolic_state: MetabolicState
    block_created: bool = False
    atp_consumed: float = 0.0


@dataclass
class EntityMetabolicProfile:
    entity_id: str
    current_state: MetabolicState
    state_since: datetime
    last_heartbeat: datetime
    heartbeat_count: int = 0
    current_interval: timedelta = timedelta(seconds=5)
    atp_balance: float = 100.0
    stress_level: float = 0.0
    recovery_progress: float = 0.0
    activity_score: float = 0.5
    reserve_ratio: float = 0.2
    state_transitions: List[Tuple[MetabolicState, datetime]] = field(default_factory=list)
    heartbeat_history: List[HeartbeatEvent] = field(default_factory=list)


@dataclass
class HeartbeatSimulator:
    entities: Dict[str, EntityMetabolicProfile] = field(default_factory=dict)
    blocks: List[Dict[str, Any]] = field(default_factory=list)
    global_block_count: int = 0

    def create_entity(self, entity_id: str,
                     initial_state: MetabolicState = MetabolicState.ACTIVE,
                     initial_atp: float = 100.0) -> EntityMetabolicProfile:
        now = datetime.now()
        profile = EntityMetabolicProfile(
            entity_id=entity_id, current_state=initial_state,
            state_since=now, last_heartbeat=now, atp_balance=initial_atp
        )
        self.entities[entity_id] = profile
        return profile

    def trigger_heartbeat(self, entity_id: str) -> Optional[HeartbeatEvent]:
        if entity_id not in self.entities:
            return None
        profile = self.entities[entity_id]
        now = datetime.now()
        event = HeartbeatEvent(
            event_id=f"hb_{entity_id}_{profile.heartbeat_count}",
            timestamp=now, entity_id=entity_id, interval_ms=5000,
            metabolic_state=profile.current_state,
            block_created=random.random() > 0.3,
            atp_consumed=self._calc_cost(profile.current_state)
        )
        profile.heartbeat_count += 1
        profile.last_heartbeat = now
        profile.atp_balance -= event.atp_consumed
        profile.heartbeat_history.append(event)
        if event.block_created:
            self.global_block_count += 1
            self.blocks.append({"block_id": self.global_block_count,
                               "entity_id": entity_id, "timestamp": now})
        return event

    def _calc_cost(self, state: MetabolicState) -> float:
        costs = {MetabolicState.ACTIVE: 1.0, MetabolicState.DORMANT: 0.1,
                MetabolicState.STRESSED: 2.0, MetabolicState.RECOVERING: 0.5,
                MetabolicState.HIBERNATING: 0.05}
        return costs.get(state, 1.0)

    def transition_state(self, entity_id: str, new_state: MetabolicState) -> bool:
        if entity_id not in self.entities:
            return False
        profile = self.entities[entity_id]
        valid = {
            MetabolicState.ACTIVE: [MetabolicState.DORMANT, MetabolicState.STRESSED],
            MetabolicState.DORMANT: [MetabolicState.ACTIVE, MetabolicState.HIBERNATING],
            MetabolicState.STRESSED: [MetabolicState.RECOVERING, MetabolicState.ACTIVE],
            MetabolicState.RECOVERING: [MetabolicState.ACTIVE, MetabolicState.DORMANT],
            MetabolicState.HIBERNATING: [MetabolicState.DORMANT]
        }
        if new_state in valid.get(profile.current_state, []):
            profile.current_state = new_state
            profile.state_since = datetime.now()
            profile.state_transitions.append((new_state, datetime.now()))
            return True
        return False


# Attack 359: Heartbeat Timing Manipulation
@dataclass
class HeartbeatTimingAttack:
    simulator: HeartbeatSimulator
    attacker_id: str
    timing_manipulations: int = 0
    atp_saved: float = 0.0
    detected: bool = False

    def execute(self, num_cycles: int = 20) -> Dict[str, Any]:
        results = {"attack_id": 359, "attack_name": "Heartbeat Timing Manipulation",
                  "success": False, "detected": False}
        if self.attacker_id not in self.simulator.entities:
            self.simulator.create_entity(self.attacker_id)
        profile = self.simulator.entities[self.attacker_id]
        initial_atp = profile.atp_balance
        for cycle in range(num_cycles):
            if cycle % 3 == 0:
                orig = profile.current_state
                profile.current_state = MetabolicState.DORMANT
                self.simulator.trigger_heartbeat(self.attacker_id)
                profile.current_state = orig
                self.timing_manipulations += 1
            else:
                self.simulator.trigger_heartbeat(self.attacker_id)
        self.atp_saved = num_cycles * 1.0 - (initial_atp - profile.atp_balance)
        events = []
        if self.timing_manipulations > 5:
            events.append({"type": "timing_manipulation", "severity": "high"})
            self.detected = random.random() < 0.7
        if self.atp_saved > 10:
            events.append({"type": "atp_saving_anomaly", "severity": "critical"})
            self.detected = True
        results["timing_manipulations"] = self.timing_manipulations
        results["atp_saved"] = self.atp_saved
        results["detected"] = self.detected
        results["success"] = self.atp_saved > 5 and not self.detected
        results["detection_events"] = events
        return results


# Attack 360: Metabolic State Spoofing
@dataclass
class MetabolicStateSpoofingAttack:
    simulator: HeartbeatSimulator
    attacker_id: str
    states_spoofed: int = 0
    reserves_accessed: float = 0.0
    detected: bool = False

    def execute(self) -> Dict[str, Any]:
        results = {"attack_id": 360, "attack_name": "Metabolic State Spoofing",
                  "success": False, "detected": False}
        if self.attacker_id not in self.simulator.entities:
            self.simulator.create_entity(self.attacker_id)
        profile = self.simulator.entities[self.attacker_id]
        # Spoof stressed for reserves
        profile.current_state = MetabolicState.STRESSED
        if random.random() < 0.5:
            reserve = profile.atp_balance * profile.reserve_ratio
            profile.atp_balance += reserve
            self.reserves_accessed = reserve
            self.states_spoofed += 1
        events = []
        if self.reserves_accessed > 0:
            events.append({"type": "reserve_access", "severity": "high"})
            self.detected = random.random() < 0.8
        if profile.stress_level < 0.3 and profile.current_state == MetabolicState.STRESSED:
            events.append({"type": "unverified_stress", "severity": "high"})
            self.detected = self.detected or random.random() < 0.7
        results["states_spoofed"] = self.states_spoofed
        results["reserves_accessed"] = self.reserves_accessed
        results["detected"] = self.detected
        results["success"] = self.reserves_accessed > 0 and not self.detected
        results["detection_events"] = events
        return results


# Attack 361: Block Rate Flooding
@dataclass
class BlockRateFloodingAttack:
    simulator: HeartbeatSimulator
    attacker_id: str
    blocks_created: int = 0
    detected: bool = False

    def execute(self, flood_size: int = 50) -> Dict[str, Any]:
        results = {"attack_id": 361, "attack_name": "Block Rate Flooding",
                  "success": False, "detected": False}
        if self.attacker_id not in self.simulator.entities:
            self.simulator.create_entity(self.attacker_id, initial_atp=1000.0)
        for _ in range(flood_size):
            event = self.simulator.trigger_heartbeat(self.attacker_id)
            if event and event.block_created:
                self.blocks_created += 1
        events = []
        if self.blocks_created > 20:
            events.append({"type": "block_rate_exceeded", "severity": "high"})
            self.detected = random.random() < 0.8
        total = len(self.simulator.blocks)
        attacker = len([b for b in self.simulator.blocks if b["entity_id"] == self.attacker_id])
        if total > 0 and attacker / total > 0.3:
            events.append({"type": "chain_concentration", "severity": "critical"})
            self.detected = True
        results["blocks_created"] = self.blocks_created
        results["detected"] = self.detected
        results["success"] = self.blocks_created > 10 and not self.detected
        results["detection_events"] = events
        return results


# Attack 362: Hibernation Abuse
@dataclass
class HibernationAbuseAttack:
    simulator: HeartbeatSimulator
    attacker_id: str
    penalties_evaded: int = 0
    detected: bool = False

    def execute(self) -> Dict[str, Any]:
        results = {"attack_id": 362, "attack_name": "Hibernation Abuse",
                  "success": False, "detected": False}
        if self.attacker_id not in self.simulator.entities:
            self.simulator.create_entity(self.attacker_id)
        profile = self.simulator.entities[self.attacker_id]
        # Try to hibernate to evade penalty
        profile.current_state = MetabolicState.DORMANT
        if self.simulator.transition_state(self.attacker_id, MetabolicState.HIBERNATING):
            if random.random() < 0.4:
                self.penalties_evaded = 1
        events = []
        if self.penalties_evaded > 0:
            events.append({"type": "penalty_evasion", "severity": "critical"})
            self.detected = random.random() < 0.9
        results["penalties_evaded"] = self.penalties_evaded
        results["detected"] = self.detected
        results["success"] = self.penalties_evaded > 0 and not self.detected
        results["detection_events"] = events
        return results


# Attack 363: Stress Cascade Induction
@dataclass
class StressCascadeInductionAttack:
    simulator: HeartbeatSimulator
    attacker_id: str
    entities_stressed: int = 0
    cascade_depth: int = 0
    detected: bool = False

    def execute(self, target_count: int = 10) -> Dict[str, Any]:
        results = {"attack_id": 363, "attack_name": "Stress Cascade Induction",
                  "success": False, "detected": False}
        targets = []
        for i in range(target_count):
            tid = f"target_{i}"
            self.simulator.create_entity(tid, initial_atp=50.0)
            targets.append(tid)
        for tid in targets[:3]:
            if tid in self.simulator.entities:
                p = self.simulator.entities[tid]
                p.current_state = MetabolicState.STRESSED
                self.entities_stressed += 1
        # Cascade
        depth = 0
        stressed = [t for t in targets if self.simulator.entities.get(t) and 
                   self.simulator.entities[t].current_state == MetabolicState.STRESSED]
        while stressed and depth < 5:
            new_stressed = []
            for s in stressed:
                idx = targets.index(s) if s in targets else -1
                if 0 <= idx < len(targets) - 1:
                    next_t = targets[idx + 1]
                    if next_t in self.simulator.entities:
                        p = self.simulator.entities[next_t]
                        if p.current_state != MetabolicState.STRESSED and random.random() < 0.6:
                            p.current_state = MetabolicState.STRESSED
                            new_stressed.append(next_t)
                            self.entities_stressed += 1
            stressed = new_stressed
            depth += 1
        self.cascade_depth = depth
        events = []
        if self.entities_stressed > 3:
            events.append({"type": "stress_propagation", "severity": "high"})
            self.detected = random.random() < 0.7
        if self.cascade_depth > 2:
            events.append({"type": "cascade_detected", "severity": "critical"})
            self.detected = True
        results["entities_stressed"] = self.entities_stressed
        results["cascade_depth"] = self.cascade_depth
        results["detected"] = self.detected
        results["success"] = self.entities_stressed > 5 and not self.detected
        results["detection_events"] = events
        return results


# Attack 364: Recovery Process Exploitation
@dataclass
class RecoveryExploitationAttack:
    simulator: HeartbeatSimulator
    attacker_id: str
    recovery_manipulations: int = 0
    resources_claimed: float = 0.0
    detected: bool = False

    def execute(self) -> Dict[str, Any]:
        results = {"attack_id": 364, "attack_name": "Recovery Process Exploitation",
                  "success": False, "detected": False}
        if self.attacker_id not in self.simulator.entities:
            self.simulator.create_entity(self.attacker_id)
        # Create victims in recovery
        victims = []
        for i in range(3):
            vid = f"recovery_victim_{i}"
            self.simulator.create_entity(vid, initial_atp=30.0)
            p = self.simulator.entities[vid]
            p.current_state = MetabolicState.RECOVERING
            p.recovery_progress = 0.3
            victims.append(vid)
        # Claim resources from recovering victims
        for vid in victims:
            if vid in self.simulator.entities:
                v = self.simulator.entities[vid]
                if random.random() < 0.3:
                    amt = v.atp_balance * 0.2
                    v.atp_balance -= amt
                    self.resources_claimed += amt
        events = []
        if self.resources_claimed > 0:
            events.append({"type": "recovery_resource_claim", "severity": "critical"})
            self.detected = random.random() < 0.9
        results["recovery_manipulations"] = self.recovery_manipulations
        results["resources_claimed"] = self.resources_claimed
        results["detected"] = self.detected
        results["success"] = self.resources_claimed > 5 and not self.detected
        results["detection_events"] = events
        return results


def run_track_fr_tests():
    print("=" * 60)
    print("Track FR: Heartbeat and Metabolic State Attacks (359-364)")
    print("=" * 60)
    results = []

    print("\n[359] Heartbeat Timing Manipulation...")
    s1 = HeartbeatSimulator()
    a359 = HeartbeatTimingAttack(simulator=s1, attacker_id="attacker_359")
    r359 = a359.execute(num_cycles=20)
    results.append(r359)
    print(f"  Success: {r359['success']}, Detected: {r359['detected']}")

    print("\n[360] Metabolic State Spoofing...")
    s2 = HeartbeatSimulator()
    a360 = MetabolicStateSpoofingAttack(simulator=s2, attacker_id="attacker_360")
    r360 = a360.execute()
    results.append(r360)
    print(f"  Success: {r360['success']}, Detected: {r360['detected']}")

    print("\n[361] Block Rate Flooding...")
    s3 = HeartbeatSimulator()
    a361 = BlockRateFloodingAttack(simulator=s3, attacker_id="attacker_361")
    r361 = a361.execute(flood_size=50)
    results.append(r361)
    print(f"  Success: {r361['success']}, Detected: {r361['detected']}")

    print("\n[362] Hibernation Abuse...")
    s4 = HeartbeatSimulator()
    a362 = HibernationAbuseAttack(simulator=s4, attacker_id="attacker_362")
    r362 = a362.execute()
    results.append(r362)
    print(f"  Success: {r362['success']}, Detected: {r362['detected']}")

    print("\n[363] Stress Cascade Induction...")
    s5 = HeartbeatSimulator()
    a363 = StressCascadeInductionAttack(simulator=s5, attacker_id="attacker_363")
    r363 = a363.execute(target_count=10)
    results.append(r363)
    print(f"  Success: {r363['success']}, Detected: {r363['detected']}")

    print("\n[364] Recovery Process Exploitation...")
    s6 = HeartbeatSimulator()
    a364 = RecoveryExploitationAttack(simulator=s6, attacker_id="attacker_364")
    r364 = a364.execute()
    results.append(r364)
    print(f"  Success: {r364['success']}, Detected: {r364['detected']}")

    print("\n" + "=" * 60)
    print("Track FR Summary")
    print("=" * 60)
    detected = sum(1 for r in results if r.get("detected", False))
    print(f"Total Attacks: {len(results)}")
    print(f"Detected: {detected}")
    print(f"Detection Rate: {detected / len(results) * 100:.1f}%")
    return results


if __name__ == "__main__":
    run_track_fr_tests()
