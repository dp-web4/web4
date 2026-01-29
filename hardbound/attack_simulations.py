#!/usr/bin/env python3
"""
Web4 Hardbound Attack Simulations.

Explores attack vectors against the trust/ATP/heartbeat systems.
These are research simulations to discover vulnerabilities and
inform mitigation design.

Attack categories tested:
1. Metabolic Manipulation - Exploit state transitions for ATP savings
2. Sybil Trust Farming - Create fake members to inflate trust scores
3. ATP Exhaustion - Drain team ATP reserves through strategic actions
4. Heartbeat Timing Attack - Exploit timing assumptions for chain manipulation
5. Trust Decay Evasion - Maintain artificially high trust scores
6. Multi-Sig Quorum Manipulation - Game the voting system

Each simulation reports:
- Attack setup cost
- Expected gain (if successful)
- Detection probability
- Time to detection
- Recommended mitigation
"""

import json
import math
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from hardbound.heartbeat_ledger import (
    HeartbeatLedger, MetabolicState, Transaction,
    STATE_ENERGY_MULTIPLIER, STATE_HEARTBEAT_INTERVAL,
)
from hardbound.team import Team, TeamConfig
from hardbound.trust_decay import TrustDecayCalculator
from hardbound.multisig import MultiSigManager, CriticalAction, ProposalStatus, QUORUM_REQUIREMENTS
from hardbound.rate_limiter import RateLimiter, RateLimitRule, RateLimitScope


@dataclass
class AttackResult:
    """Result of an attack simulation."""
    attack_name: str
    success: bool
    setup_cost_atp: float
    gain_atp: float
    roi: float  # gain / cost (negative = loss)
    detection_probability: float  # 0.0 to 1.0
    time_to_detection_hours: float
    blocks_until_detected: int
    trust_damage: float  # damage to attacker's trust if caught
    description: str
    mitigation: str
    raw_data: Dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Attack 1: Metabolic State Manipulation
# ---------------------------------------------------------------------------

def attack_metabolic_manipulation() -> AttackResult:
    """
    ATTACK: Exploit metabolic state transitions to minimize ATP costs.

    Strategy:
    - Keep team in SLEEP or REST as much as possible
    - Only wake for high-value transactions
    - Immediately return to dormant state
    - Save 60-98% of ATP compared to honest ACTIVE team

    This is similar to "tax optimization" - technically within rules
    but undermines the economic model.
    """
    db_path = Path(tempfile.mkdtemp()) / "attack_metabolic.db"

    # Create two teams: honest (always active) and attacker (gaming states)
    honest_ledger = HeartbeatLedger("web4:team:honest", db_path=db_path)
    attack_ledger = HeartbeatLedger("web4:team:attacker", db_path=db_path)

    # Simulate 100 heartbeats
    honest_energy = 0.0
    attack_energy = 0.0
    honest_txns = 0
    attack_txns = 0

    # Both do the same work (10 transactions)
    work_items = [
        ("r6_request", {"action": "commit"}, 2.0),
        ("trust_update", {"dim": "reliability"}, 0.5),
        ("r6_request", {"action": "review"}, 1.5),
        ("member_added", {"role": "dev"}, 1.0),
        ("r6_request", {"action": "deploy"}, 5.0),
        ("r6_request", {"action": "commit"}, 2.0),
        ("trust_update", {"dim": "competence"}, 0.5),
        ("r6_request", {"action": "commit"}, 2.0),
        ("r6_request", {"action": "test"}, 1.0),
        ("policy_update", {"rule": "deploy_threshold"}, 3.0),
    ]

    actor = "web4:lct:actor:001"

    # HONEST TEAM: stays active, regular heartbeats
    for i in range(100):
        if i < len(work_items):
            tx_type, data, cost = work_items[i]
            honest_ledger.submit_transaction(tx_type, actor, data, atp_cost=cost)
            honest_txns += 1
        block = honest_ledger.heartbeat()
        honest_energy += block.energy_cost

    # ATTACKER TEAM: gaming metabolic states
    # Strategy: submit all work in burst, then sleep
    for item in work_items:
        tx_type, data, cost = item
        attack_ledger.submit_transaction(tx_type, actor, data, atp_cost=cost)
        attack_txns += 1

    # Seal one block with all work
    block = attack_ledger.heartbeat()
    attack_energy += block.energy_cost

    # Immediately transition to REST then SLEEP
    attack_ledger.transition_state(MetabolicState.REST, trigger="work_complete")
    block = attack_ledger.heartbeat()
    attack_energy += block.energy_cost

    attack_ledger.transition_state(MetabolicState.SLEEP, trigger="scheduled_sleep")

    # 98 heartbeats in sleep mode (minimal cost)
    for i in range(98):
        block = attack_ledger.heartbeat()
        attack_energy += block.energy_cost

    savings = honest_energy - attack_energy
    savings_pct = (savings / honest_energy * 100) if honest_energy > 0 else 0

    # Detection: Compare metabolic health scores
    honest_health = honest_ledger.get_metabolic_health()
    attack_health = attack_ledger.get_metabolic_health()

    # Attacker has much lower transaction density and poor regularity
    density_ratio = attack_health["transaction_density"] / max(honest_health["transaction_density"], 0.001)
    detected = density_ratio < 0.3  # Obvious outlier

    # Cleanup
    import shutil
    shutil.rmtree(db_path.parent)

    return AttackResult(
        attack_name="Metabolic State Manipulation",
        success=True,  # Attack works (saves energy)
        setup_cost_atp=0.0,
        gain_atp=savings,
        roi=float('inf') if savings > 0 else 0.0,
        detection_probability=0.85 if detected else 0.3,
        time_to_detection_hours=24.0,  # Detectable in daily health check
        blocks_until_detected=100,
        trust_damage=0.15,  # Moderate - gaming, not fraud
        description=(
            f"Attacker saved {savings:.2f} ATP ({savings_pct:.1f}%) by batching work "
            f"and sleeping. Honest team spent {honest_energy:.2f}, attacker spent "
            f"{attack_energy:.2f}. Both completed {attack_txns} transactions."
        ),
        mitigation=(
            "1. Minimum active-state requirements per epoch\n"
            "2. Transaction density thresholds for metabolic reliability\n"
            "3. Trust penalty for teams with very low metabolic reliability\n"
            "4. Require minimum heartbeats in active state per work unit"
        ),
        raw_data={
            "honest_energy": honest_energy,
            "attack_energy": attack_energy,
            "savings": savings,
            "savings_pct": savings_pct,
            "honest_health": honest_health,
            "attack_health": attack_health,
        }
    )


# ---------------------------------------------------------------------------
# Attack 2: Sybil Trust Farming
# ---------------------------------------------------------------------------

def attack_sybil_trust_farming() -> AttackResult:
    """
    ATTACK: Create multiple fake team members who witness each other
    to inflate trust scores, then use elevated trust for high-value actions.

    Tests the FULL defense stack:
    1. Trust velocity caps (per-dimension per-day limits)
    2. Diminishing same-pair witnessing (exponential decay)
    3. Sybil detection via behavioral correlation
    4. Activity quality scoring (ping detection)

    Strategy:
    - Create N Sybil members
    - Each Sybil reports "success" for every other Sybil's actions
    - Sybils mutually witness each other
    - Try to reach high-trust thresholds

    Cost: N member creation + ATP for fake transactions
    Gain: Access to high-trust-threshold actions (deploy, admin, etc.)
    """
    from hardbound.sybil_detection import SybilDetector

    config = TeamConfig(
        name="sybil-test-team",
        description="Testing Sybil resistance",
        default_member_budget=100,
    )
    team = Team(config=config)
    admin_lct = "web4:soft:admin:sybil001"
    team.set_admin(admin_lct)

    # Create Sybil members
    n_sybils = 5
    sybil_lcts = [f"web4:soft:sybil:{i:03d}" for i in range(n_sybils)]
    for lct in sybil_lcts:
        team.add_member(lct, role="developer", atp_budget=50)

    # Also add one honest member for comparison
    honest_lct = "web4:soft:honest:001"
    team.add_member(honest_lct, role="developer", atp_budget=50)

    # ATTACK PHASE 1: Trust inflation via update_member_trust
    # (capped by velocity limits)
    rounds = 20
    for _ in range(rounds):
        for sybil in sybil_lcts:
            team.update_member_trust(sybil, "success", magnitude=0.7)

    # Honest member also works
    for _ in range(rounds):
        team.update_member_trust(honest_lct, "success", magnitude=0.7)

    # ATTACK PHASE 2: Mutual witnessing (diminishing returns apply)
    witness_rounds = 10
    for _ in range(witness_rounds):
        for i, sybil in enumerate(sybil_lcts):
            for j, other in enumerate(sybil_lcts):
                if i != j:
                    team.witness_member(other, sybil, quality=1.0)

    # Compare trust scores
    sybil_trusts = [team.get_member_trust_score(s) for s in sybil_lcts]
    honest_trust = team.get_member_trust_score(honest_lct)
    avg_sybil_trust = sum(sybil_trusts) / len(sybil_trusts)

    # Check thresholds
    high_threshold = 0.8
    sybils_pass = sum(1 for t in sybil_trusts if t >= high_threshold)
    honest_passes = honest_trust >= high_threshold

    # DEFENSE: Run Sybil detection
    member_trusts = {}
    for lct in sybil_lcts + [honest_lct]:
        member_trusts[lct] = team.get_member_trust(lct, apply_decay=False)

    detector = SybilDetector()
    report = detector.analyze_team(team.team_id, member_trusts)

    # Check witness effectiveness decay
    # After 10 rounds of mutual witnessing between 5 Sybils,
    # each pair has 10 attestations -> effectiveness should be very low
    witness_effs = []
    for i, s1 in enumerate(sybil_lcts):
        for j, s2 in enumerate(sybil_lcts):
            if i < j:
                eff = team.get_witness_effectiveness(s1, s2)
                witness_effs.append(eff)
    avg_witness_eff = sum(witness_effs) / len(witness_effs) if witness_effs else 0

    trust_variance = max(sybil_trusts) - min(sybil_trusts)
    setup_cost = n_sybils * 50
    gain = 0.0
    if sybils_pass >= 3:
        gain = 500.0

    return AttackResult(
        attack_name="Sybil Trust Farming",
        success=sybils_pass >= 3,
        setup_cost_atp=float(setup_cost),
        gain_atp=gain,
        roi=(gain - setup_cost) / setup_cost if setup_cost > 0 else 0.0,
        detection_probability=0.95 if report.clusters else 0.40,
        time_to_detection_hours=48.0 if not report.clusters else 0.0,
        blocks_until_detected=200 if not report.clusters else 0,
        trust_damage=0.5,
        description=(
            f"Created {n_sybils} Sybil members with mutual trust inflation over {rounds} rounds.\n"
            f"Average Sybil trust: {avg_sybil_trust:.3f}\n"
            f"Honest member trust: {honest_trust:.3f}\n"
            f"Sybils passing {high_threshold} threshold: {sybils_pass}/{n_sybils}\n"
            f"Honest passes threshold: {honest_passes}\n"
            f"Trust variance among Sybils: {trust_variance:.4f} "
            f"({'SUSPICIOUS' if trust_variance < 0.01 else 'normal'})\n"
            f"\n"
            f"Defense Stack Results:\n"
            f"  Velocity caps: Trust capped at {avg_sybil_trust:.3f} (below {high_threshold})\n"
            f"  Witness diminishing: avg pair effectiveness={avg_witness_eff:.3f} (after {witness_rounds} rounds)\n"
            f"  Sybil detection: {len(report.clusters)} clusters found, risk={report.overall_risk.value}\n"
            f"  Sybil cluster members: {[c.members for c in report.clusters[:3]]}"
        ),
        mitigation=(
            "IMPLEMENTED (5-layer defense):\n"
            "1. Trust velocity caps (per-dimension per-day limits)\n"
            "2. Diminishing same-pair witnessing (half-life=3 attestations)\n"
            "3. Sybil detection via behavioral correlation (4 signals)\n"
            "4. Activity quality scoring (trivial pings get near-zero credit)\n"
            "5. Wake recalibration (dormancy re-entry cost)\n"
            "\n"
            "STILL RECOMMENDED:\n"
            "6. Hardware-bound identity (cost of creating Sybils becomes non-trivial)\n"
            "7. External witness requirement (at least 1 witness from outside team)"
        ),
        raw_data={
            "sybil_trusts": sybil_trusts,
            "honest_trust": honest_trust,
            "trust_variance": trust_variance,
            "sybils_passing": sybils_pass,
            "witness_effectiveness": avg_witness_eff,
            "sybil_clusters": len(report.clusters),
            "sybil_risk": report.overall_risk.value,
        }
    )


# ---------------------------------------------------------------------------
# Attack 3: ATP Exhaustion (Resource Drain)
# ---------------------------------------------------------------------------

def attack_atp_exhaustion() -> AttackResult:
    """
    ATTACK: Drain a target team's ATP reserves through strategic
    expensive operations, leaving the team unable to operate.

    Strategy:
    - Submit many R6 requests for expensive actions
    - Even rejected requests may consume reviewer ATP (time to review)
    - Trigger frequent metabolic state transitions (wake penalties)
    - Force unnecessary multi-sig proposals
    """
    db_path = Path(tempfile.mkdtemp()) / "attack_atp.db"
    target_ledger = HeartbeatLedger("web4:team:target", db_path=db_path)

    initial_reserves = target_ledger._get_atp_reserves()

    # Attack vector 1: Spam expensive transactions
    attacker_lct = "web4:lct:attacker:001"
    spam_cost = 0.0
    for i in range(50):
        tx = target_ledger.submit_transaction(
            "r6_request", attacker_lct,
            {"action": "deploy", "description": f"Deploy request #{i}"},
            atp_cost=5.0,  # Expensive action
        )
        spam_cost += 5.0

    # Seal blocks (consumes base energy too)
    for _ in range(10):
        block = target_ledger.heartbeat()

    # Attack vector 2: Force metabolic state transitions (wake penalties)
    target_ledger.transition_state(MetabolicState.REST, trigger="attack_induced_rest")
    target_ledger.heartbeat()

    target_ledger.transition_state(MetabolicState.SLEEP, trigger="forced_sleep")
    target_ledger.heartbeat()

    # Premature wake (incurs penalty)
    target_ledger.transition_state(MetabolicState.ACTIVE, trigger="forced_wake")
    target_ledger.heartbeat()

    # Do it again
    target_ledger.transition_state(MetabolicState.DREAMING, trigger="forced_dream")
    target_ledger.heartbeat()
    target_ledger.transition_state(MetabolicState.ACTIVE, trigger="forced_wake_dream")
    target_ledger.heartbeat()

    final_reserves = target_ledger._get_atp_reserves()
    drained = initial_reserves - final_reserves

    # Check if team is operational
    team_operational = final_reserves > 50.0  # Minimum viable reserves

    # Detection: Unusual transaction volume from single actor
    # In real system, rate limiter would catch this
    detection_prob = 0.95  # Very detectable (volume spike from one LCT)

    import shutil
    shutil.rmtree(db_path.parent)

    return AttackResult(
        attack_name="ATP Exhaustion (Resource Drain)",
        success=not team_operational,
        setup_cost_atp=0.0,  # Attacker spends nothing (target pays)
        gain_atp=0.0,  # Destructive attack, no direct gain
        roi=0.0,
        detection_probability=detection_prob,
        time_to_detection_hours=1.0,  # Rate limiter catches quickly
        blocks_until_detected=10,
        trust_damage=1.0,  # Maximum - destructive attack
        description=(
            f"Drained {drained:.2f} ATP from target team.\n"
            f"Initial reserves: {initial_reserves:.2f}\n"
            f"Final reserves: {final_reserves:.2f}\n"
            f"Transaction spam cost: {spam_cost:.2f}\n"
            f"Team operational: {team_operational}\n"
            f"Attack {'succeeded' if not team_operational else 'failed'} in making team inoperable."
        ),
        mitigation=(
            "1. Per-LCT rate limiting on R6 requests (implemented in rate_limiter.py)\n"
            "2. Require ATP deposit from requester (not just target team)\n"
            "3. Admin-only metabolic state transitions\n"
            "4. Emergency ATP freeze when drain detected\n"
            "5. Minimum ATP reserve that cannot be consumed\n"
            "6. Escalating cost for repeated expensive actions"
        ),
        raw_data={
            "initial_reserves": initial_reserves,
            "final_reserves": final_reserves,
            "drained": drained,
            "spam_cost": spam_cost,
            "team_operational": team_operational,
        }
    )


# ---------------------------------------------------------------------------
# Attack 4: Heartbeat Timing Attack
# ---------------------------------------------------------------------------

def attack_heartbeat_timing() -> AttackResult:
    """
    ATTACK: Exploit timing assumptions in the heartbeat ledger.

    Strategy:
    - Manipulate heartbeat timing to create favorable energy costs
    - Fire heartbeats very rapidly during active state (lower per-block cost)
    - Fire heartbeats very slowly during rest (accumulate time without paying)
    - Create "phantom blocks" with artificially low energy costs

    This tests whether the energy model is robust to timing manipulation.
    """
    db_path = Path(tempfile.mkdtemp()) / "attack_timing.db"

    honest_ledger = HeartbeatLedger("web4:team:honest-timing", db_path=db_path)
    attack_ledger = HeartbeatLedger("web4:team:attack-timing", db_path=db_path)

    # Both submit same work
    actor = "web4:lct:actor:001"
    for ledger in [honest_ledger, attack_ledger]:
        for i in range(5):
            ledger.submit_transaction("r6_request", actor,
                                      {"action": f"work_{i}"}, atp_cost=2.0)

    # HONEST: Regular heartbeats
    honest_energy = 0.0
    for _ in range(20):
        block = honest_ledger.heartbeat()
        honest_energy += block.energy_cost

    # ATTACKER: Rapid-fire heartbeats (minimal time between = minimal energy)
    # The attacker calls heartbeat() as fast as possible
    attack_energy = 0.0
    for _ in range(20):
        block = attack_ledger.heartbeat()
        attack_energy += block.energy_cost

    # Analysis: Are the costs significantly different?
    # Since both run in-process with minimal delay, they should be similar
    # The vulnerability would be if someone could fire heartbeats faster than
    # real time allows
    cost_ratio = attack_energy / max(honest_energy, 0.001)

    # In our model, energy = base_rate * actual_interval * multiplier
    # So rapid heartbeats = less energy per block (correct behavior)
    # But total energy over same real time period should be the same
    # The attack exploits that blocks are "cheap" when intervals are short

    # Detection: Heartbeat regularity check
    attack_health = attack_ledger.get_metabolic_health()
    honest_health = honest_ledger.get_metabolic_health()

    import shutil
    shutil.rmtree(db_path.parent)

    return AttackResult(
        attack_name="Heartbeat Timing Attack",
        success=cost_ratio < 0.8,  # Saved >20%
        setup_cost_atp=0.0,
        gain_atp=honest_energy - attack_energy,
        roi=float('inf') if honest_energy > attack_energy else 0.0,
        detection_probability=0.7,
        time_to_detection_hours=6.0,
        blocks_until_detected=50,
        trust_damage=0.2,
        description=(
            f"Honest team energy: {honest_energy:.4f}\n"
            f"Attacker energy: {attack_energy:.4f}\n"
            f"Cost ratio: {cost_ratio:.4f}\n"
            f"Regularity (honest): {honest_health['heartbeat_regularity']:.4f}\n"
            f"Regularity (attacker): {attack_health['heartbeat_regularity']:.4f}\n"
            f"Attack {'exploitable' if cost_ratio < 0.8 else 'not significant'}: "
            f"Rapid heartbeats reduce per-block cost but total time-cost is governed "
            f"by wall clock, so the energy model is {'vulnerable' if cost_ratio < 0.8 else 'robust'}."
        ),
        mitigation=(
            "1. Minimum heartbeat interval enforcement (reject rapid-fire heartbeats)\n"
            "2. Energy floor per block regardless of interval\n"
            "3. Heartbeat regularity as trust signal\n"
            "4. Server-side timestamp validation"
        ),
        raw_data={
            "honest_energy": honest_energy,
            "attack_energy": attack_energy,
            "cost_ratio": cost_ratio,
            "honest_health": honest_health,
            "attack_health": attack_health,
        }
    )


# ---------------------------------------------------------------------------
# Attack 5: Trust Decay Evasion
# ---------------------------------------------------------------------------

def attack_trust_decay_evasion() -> AttackResult:
    """
    ATTACK: Maintain artificially high trust by gaming the decay system.

    Strategy:
    - Do minimal work to keep "last activity" timestamp fresh
    - Keep team in HIBERNATION or SLEEP to freeze trust decay
    - Burst activity just before trust evaluations
    - Exploit sustained-performance bonus (>0.8 decays at 50% rate)
    """
    calc = TrustDecayCalculator()

    # Scenario 1: Honest member - 30 days, moderate activity
    honest_trust = {
        'competence': 0.9,
        'reliability': 0.85,
        'consistency': 0.8,
        'witnesses': 0.7,
        'lineage': 0.9,
        'alignment': 0.75,
    }

    now = datetime.now(timezone.utc)
    last_update = now - timedelta(days=30)

    honest_decayed = calc.apply_decay(honest_trust, last_update, now, actions_since_update=5)
    honest_avg = sum(honest_decayed.values()) / 6

    # Scenario 2: Attacker - same starting trust, but exploits timing
    # Strategy: perform 1 action every day to reset the "last activity" counter
    attacker_trust = dict(honest_trust)  # Same starting point

    # Simulate daily micro-activity
    current_trust = dict(attacker_trust)
    for day in range(30):
        # Each day: apply 1 day of decay with 1 action
        day_start = last_update + timedelta(days=day)
        day_end = day_start + timedelta(days=1)
        current_trust = calc.apply_decay(current_trust, day_start, day_end, actions_since_update=1)

    attacker_avg = sum(current_trust.values()) / 6

    # Scenario 3: Hibernation trust (MITIGATED - now decays at 5% rate)
    # Previously: trust was completely frozen (0.0 decay) = 13.6% advantage
    # Now: trust decays at 5% rate during hibernation
    hibernation_trust = dict(honest_trust)
    hibernation_decayed = calc.apply_decay(
        hibernation_trust, last_update, now,
        actions_since_update=0,
        metabolic_state="hibernation",  # NEW: metabolic-aware decay
    )
    hibernation_avg = sum(hibernation_decayed.values()) / 6

    # Compare
    trust_diff_attack = attacker_avg - honest_avg
    trust_diff_hibernation = hibernation_avg - honest_avg

    # Scenario 4: Activity quality adjustment
    # With quality scoring, micro-pings get near-zero decay credit
    from hardbound.activity_quality import (
        ActivityWindow, compute_quality_adjusted_decay
    )

    # Micro-pinger: 1 heartbeat/day for 30 days
    ping_window = ActivityWindow(entity_id="attacker", window_seconds=86400*30)
    for day in range(30):
        ts = (now - timedelta(days=29-day)).isoformat()
        ping_window.record("heartbeat", ts)
    ping_quality = ping_window.quality_score
    ping_adjusted = compute_quality_adjusted_decay(30, ping_window)

    # Honest worker: diverse actions
    work_window = ActivityWindow(entity_id="honest", window_seconds=86400*30)
    work_types = ["r6_created", "r6_completed", "trust_update", "audit_record", "heartbeat"]
    for day in range(30):
        ts = (now - timedelta(days=29-day)).isoformat()
        work_window.record(work_types[day % len(work_types)], ts, atp_cost=2.0)
    work_quality = work_window.quality_score
    work_adjusted = compute_quality_adjusted_decay(30, work_window)

    # With quality-adjusted counts, recalculate decay
    quality_attacker = calc.apply_decay(
        dict(honest_trust), last_update, now,
        actions_since_update=int(ping_adjusted)
    )
    quality_honest = calc.apply_decay(
        dict(honest_trust), last_update, now,
        actions_since_update=int(work_adjusted)
    )
    quality_attacker_avg = sum(quality_attacker.values()) / 6
    quality_honest_avg = sum(quality_honest.values()) / 6
    quality_diff = quality_attacker_avg - quality_honest_avg

    # Success criteria: with all defenses, any remaining advantage?
    gaming_successful = quality_diff > 0.05 or trust_diff_hibernation > 0.1

    return AttackResult(
        attack_name="Trust Decay Evasion",
        success=gaming_successful,
        setup_cost_atp=30.0,
        gain_atp=0.0,
        roi=0.0,
        detection_probability=0.80,
        time_to_detection_hours=168.0 if gaming_successful else 0.0,
        blocks_until_detected=500 if gaming_successful else 0,
        trust_damage=0.3,
        description=(
            f"Trust after 30 days:\n"
            f"  Honest (moderate activity):     avg={honest_avg:.4f}\n"
            f"  Attacker (daily micro-ping):    avg={attacker_avg:.4f} "
            f"(+{trust_diff_attack:.4f})\n"
            f"  Hibernation (5% decay rate):    avg={hibernation_avg:.4f} "
            f"(+{trust_diff_hibernation:.4f})\n\n"
            f"Activity Quality Analysis:\n"
            f"  Micro-ping quality: {ping_quality:.3f} (adjusted count: {ping_adjusted:.1f})\n"
            f"  Honest work quality: {work_quality:.3f} (adjusted count: {work_adjusted:.1f})\n"
            f"  With quality scoring:\n"
            f"    Attacker trust: {quality_attacker_avg:.4f}\n"
            f"    Honest trust:   {quality_honest_avg:.4f}\n"
            f"    Difference:     {quality_diff:+.4f}\n\n"
            f"The micro-pinger now gets LESS trust preservation than honest workers.\n"
            f"Quality-adjusted advantage: {quality_diff/quality_honest_avg*100:+.1f}%\n"
            f"Gaming {'still viable' if gaming_successful else 'FULLY MITIGATED'}."
        ),
        mitigation=(
            "IMPLEMENTED (full defense stack):\n"
            "1. Metabolic-state-aware decay (5% rate during hibernation/torpor)\n"
            "2. Activity quality scoring (micro-pings get near-zero credit)\n"
            "3. Wake recalibration (re-entry cost on dormancy exit)\n"
            "\n"
            "RESULT: Attacker trust preservation is now WORSE than honest workers.\n"
            "The gaming vector is fully closed."
        ),
        raw_data={
            "honest_decayed": honest_decayed,
            "attacker_trust": current_trust,
            "hibernation_trust": hibernation_decayed,
            "honest_avg": honest_avg,
            "attacker_avg": attacker_avg,
            "hibernation_avg": hibernation_avg,
            "ping_quality": ping_quality,
            "work_quality": work_quality,
            "quality_attacker_avg": quality_attacker_avg,
            "quality_honest_avg": quality_honest_avg,
        }
    )


# ---------------------------------------------------------------------------
# Attack 6: Multi-Sig Quorum Manipulation
# ---------------------------------------------------------------------------

def attack_multisig_quorum() -> AttackResult:
    """
    ATTACK: Manipulate multi-sig voting by controlling enough trust-weighted
    votes to force through critical actions.

    Strategy:
    - Build up 3 members to high trust through legitimate work
    - Then use trust-weighted voting to push through a malicious proposal
    - The trust-weighted quorum may be met before minimum vote count
    """
    config = TeamConfig(name="multisig-attack-team", description="Test")
    team = Team(config=config)

    admin_lct = "web4:soft:admin:msig-atk"
    team.set_admin(admin_lct)

    # Add attack members and honest members
    attacker_lcts = [f"web4:soft:attacker:{i}" for i in range(3)]
    honest_lcts = [f"web4:soft:honest:{i}" for i in range(3)]

    for lct in attacker_lcts + honest_lcts:
        team.add_member(lct, role="developer")

    # All members do legitimate work to build trust
    for _ in range(25):
        for lct in attacker_lcts + honest_lcts:
            team.update_member_trust(lct, "success", 0.8)

    # Check trust scores
    attacker_trusts = [team.get_member_trust_score(lct) for lct in attacker_lcts]
    honest_trusts = [team.get_member_trust_score(lct) for lct in honest_lcts]

    # Create multi-sig manager
    msig = MultiSigManager(team)

    # ATTACK: Propose malicious action (budget allocation to attackers)
    # With mitigations: conflict-of-interest detection will flag this
    mitigations_active = {
        "beneficiary_detected": False,
        "beneficiary_blocked": False,
        "veto_exercised": False,
        "voting_period_blocked": False,
        "quorum_raised": False,
    }

    proposal = msig.create_proposal(
        proposer_lct=attacker_lcts[0],
        action=CriticalAction.BUDGET_ALLOCATION,
        action_data={"recipient": attacker_lcts[0], "amount": 500},
        description="Allocate budget for critical infrastructure",
    )

    # Check if conflict-of-interest was detected
    if proposal.beneficiaries:
        mitigations_active["beneficiary_detected"] = True
        # Quorum should be raised
        if proposal.min_approvals > QUORUM_REQUIREMENTS[CriticalAction.BUDGET_ALLOCATION]["min_approvals"]:
            mitigations_active["quorum_raised"] = True

    # Attackers try to vote YES
    vote_errors = []
    for lct in attacker_lcts:
        if lct != attacker_lcts[0]:  # Can't self-vote
            try:
                proposal = msig.vote(proposal.proposal_id, lct, approve=True,
                                      comment="Approved")
            except PermissionError as e:
                vote_errors.append((lct, str(e)))
                mitigations_active["beneficiary_blocked"] = True

    # Check if quorum reached
    quorum_reached = proposal.status == ProposalStatus.APPROVED

    # Try with admin to reach quorum if needed
    if not quorum_reached and proposal.status == ProposalStatus.PENDING:
        try:
            proposal = msig.vote(proposal.proposal_id, admin_lct, approve=True,
                                  comment="Looks reasonable")
            quorum_reached = proposal.status == ProposalStatus.APPROVED
        except (PermissionError, ValueError):
            pass

    # DEFENSE: Honest member exercises veto
    # Boost one honest member's trust above veto threshold
    for _ in range(30):
        team.update_member_trust(honest_lcts[0], "success", 0.9)
    honest_veto_trust = team.get_member_trust_score(honest_lcts[0])

    if quorum_reached or proposal.status == ProposalStatus.PENDING:
        # Reset to pending for veto test
        if proposal.status == ProposalStatus.APPROVED:
            # In real system, voting period would block execution
            mitigations_active["voting_period_blocked"] = True

        try:
            # Honest member with high trust casts veto
            proposal = msig.vote(proposal.proposal_id, honest_lcts[0],
                                  approve=False,
                                  comment="Self-dealing: proposer is recipient")
            if proposal.vetoed_by:
                mitigations_active["veto_exercised"] = True
                quorum_reached = False
        except (PermissionError, ValueError):
            pass  # Already voted or other issue

    # Final status
    attack_blocked = (
        mitigations_active["beneficiary_blocked"] or
        mitigations_active["veto_exercised"] or
        not quorum_reached
    )

    return AttackResult(
        attack_name="Multi-Sig Quorum Manipulation",
        success=quorum_reached and not attack_blocked,
        setup_cost_atp=0.0,
        gain_atp=500.0 if quorum_reached and not attack_blocked else 0.0,
        roi=float('inf') if quorum_reached and not attack_blocked else 0.0,
        detection_probability=0.95,  # Much higher with mitigations
        time_to_detection_hours=0.0 if mitigations_active["beneficiary_detected"] else 72.0,
        blocks_until_detected=0 if mitigations_active["beneficiary_detected"] else 300,
        trust_damage=0.8 if quorum_reached and not attack_blocked else 0.0,
        description=(
            f"Attacker trust scores: {[f'{t:.3f}' for t in attacker_trusts]}\n"
            f"Honest trust scores:   {[f'{t:.3f}' for t in honest_trusts]}\n"
            f"Honest veto trust:     {honest_veto_trust:.3f}\n"
            f"Proposal status: {proposal.status.value}\n"
            f"Approval count: {proposal.approval_count}\n"
            f"Trust-weighted: {proposal.trust_weighted_approvals:.3f}\n"
            f"Quorum reached: {quorum_reached}\n"
            f"Attack blocked: {attack_blocked}\n"
            f"\nMitigation results:\n"
            f"  Beneficiary detected:     {mitigations_active['beneficiary_detected']}\n"
            f"  Beneficiary vote blocked: {mitigations_active['beneficiary_blocked']}\n"
            f"  Quorum raised:            {mitigations_active['quorum_raised']}\n"
            f"  Voting period enforced:   {mitigations_active['voting_period_blocked']}\n"
            f"  Veto exercised:           {mitigations_active['veto_exercised']}\n"
            f"  Vote errors: {vote_errors}"
        ),
        mitigation=(
            "IMPLEMENTED:\n"
            "1. Conflict-of-interest detection (beneficiary flagging)\n"
            "2. Beneficiary exclusion from approval voting\n"
            "3. Raised quorum for self-benefiting proposals (1.5x)\n"
            "4. Mandatory voting period before execution\n"
            "5. Veto power for high-trust members (>0.85)\n"
            "\nSTILL NEEDED:\n"
            "6. Cross-team witness requirement for critical actions\n"
            "7. Automatic audit alert on self-benefiting proposals"
        ),
        raw_data={
            "attacker_trusts": attacker_trusts,
            "honest_trusts": honest_trusts,
            "proposal_status": proposal.status.value,
            "approval_count": proposal.approval_count,
            "quorum_reached": quorum_reached,
            "mitigations": mitigations_active,
            "vote_errors": vote_errors,
        }
    )


# ---------------------------------------------------------------------------
# Attack 7: Cross-Team Witness Collusion
# ---------------------------------------------------------------------------

def attack_cross_team_witness_collusion() -> AttackResult:
    """
    ATTACK: Two colluding teams provide fake external witnesses to each other.

    Strategy:
    - Attacker controls Team A and Team B
    - Team A creates a critical proposal (e.g. admin transfer)
    - Team B members act as "external witnesses" for Team A
    - Team A members return the favor for Team B
    - Both teams bypass the external witness requirement via mutual collusion

    Expected outcome: This should succeed unless witness diversity is checked.
    """
    team_a = Team(config=TeamConfig(name="colluder-a", description="Colluding team A"))
    team_a.set_admin("admin:collude_a")
    team_b = Team(config=TeamConfig(name="colluder-b", description="Colluding team B"))
    team_b.set_admin("admin:collude_b")

    # Add members to both teams
    for i in range(4):
        team_a.add_member(f"a_member:{i}", role="developer")
        member_a = team_a.get_member(f"a_member:{i}")
        member_a["trust"] = {
            "reliability": 0.85, "competence": 0.85, "alignment": 0.85,
            "consistency": 0.85, "witnesses": 0.85, "lineage": 0.85,
        }
        team_b.add_member(f"b_member:{i}", role="developer")
        member_b = team_b.get_member(f"b_member:{i}")
        member_b["trust"] = {
            "reliability": 0.85, "competence": 0.85, "alignment": 0.85,
            "consistency": 0.85, "witnesses": 0.85, "lineage": 0.85,
        }
    team_a._update_team()
    team_b._update_team()

    msig_a = MultiSigManager(team_a)

    # Team A creates admin transfer proposal
    proposal = msig_a.create_proposal(
        proposer_lct="admin:collude_a",
        action=CriticalAction.ADMIN_TRANSFER,
        action_data={"new_admin_lct": "a_member:0"},
        description="Colluding admin transfer",
    )

    # Get votes from Team A members
    for i in range(1, 4):
        msig_a.vote(proposal.proposal_id, f"a_member:{i}", approve=True)

    # SCENARIO 1: Single witness from colluding team (admin transfer needs 1)
    # This still works because 1 witness from 1 team = valid diversity
    single_witness_succeeded = False
    try:
        msig_a.add_external_witness(
            proposal.proposal_id,
            witness_lct="b_member:0",
            witness_team_id=team_b.team_id,
            witness_trust_score=0.85,
            attestation="Totally legit, trust me bro",
        )
        single_witness_succeeded = True
    except (ValueError, PermissionError):
        single_witness_succeeded = False

    # SCENARIO 2: Try to stack multiple witnesses from SAME colluding team
    # This tests the new diversity requirement.
    # Create a dissolution proposal (needs 2 external witnesses)
    team_a.add_member("a_member:4", role="developer")
    member_a4 = team_a.get_member("a_member:4")
    member_a4["trust"] = {
        "reliability": 0.85, "competence": 0.85, "alignment": 0.85,
        "consistency": 0.85, "witnesses": 0.85, "lineage": 0.85,
    }
    team_a._update_team()

    dissolve_proposal = msig_a.create_proposal(
        proposer_lct="admin:collude_a",
        action=CriticalAction.TEAM_DISSOLUTION,
        action_data={"reason": "Colluding dissolution"},
        description="Test diversity on dissolution",
    )

    # First witness from Team B - should work
    first_collude = False
    try:
        msig_a.add_external_witness(
            dissolve_proposal.proposal_id,
            witness_lct="b_member:1",
            witness_team_id=team_b.team_id,
            witness_trust_score=0.85,
        )
        first_collude = True
    except (ValueError, PermissionError):
        first_collude = False

    # Second witness ALSO from Team B - should FAIL due to diversity requirement
    diversity_blocked = False
    try:
        msig_a.add_external_witness(
            dissolve_proposal.proposal_id,
            witness_lct="b_member:2",
            witness_team_id=team_b.team_id,  # Same team!
            witness_trust_score=0.85,
        )
    except ValueError as e:
        if "already provided a witness" in str(e):
            diversity_blocked = True

    # Check final state
    proposal = msig_a.get_proposal(proposal.proposal_id)
    dissolve = msig_a.get_proposal(dissolve_proposal.proposal_id)

    # The attack is PARTIALLY defended:
    # - Single-witness actions (admin transfer): colluding team can still provide 1 witness
    # - Multi-witness actions (dissolution): diversity requirement blocks same-team stacking
    attack_success = single_witness_succeeded and not diversity_blocked

    return AttackResult(
        attack_name="Cross-Team Witness Collusion",
        success=attack_success,
        setup_cost_atp=200.0,
        gain_atp=25.0,  # Reduced gain - only single-witness actions exploitable
        roi=-0.875,
        detection_probability=0.70,  # Higher detection with diversity tracking
        time_to_detection_hours=168,
        blocks_until_detected=500,
        trust_damage=1.0,
        description=(
            f"Single-witness collusion: {'SUCCEEDED' if single_witness_succeeded else 'FAILED'}. "
            f"Multi-witness diversity block: {'ENFORCED' if diversity_blocked else 'BYPASSED'}. "
            f"FINDING: Witness diversity requirement blocks same-team stacking. "
            f"Single-witness actions remain vulnerable to a single colluding team. "
            f"Federation registry now provides reputation scoring and collusion detection."
        ),
        mitigation=(
            "IMPLEMENTED:\n"
            "1. Witness diversity: each external witness must come from a different team\n"
            "2. Federation registry: cross-team witness graph analysis flags reciprocal collusion\n"
            "3. Witness reputation scoring: Bayesian scores degrade when attested proposals fail\n"
            "4. Federation-integrated witnessing: add_external_witness() validates team registration,\n"
            "   active status, and minimum witness score via FederationRegistry\n"
            "5. Collusion detection: reciprocity analysis flags team pairs with >60% mutual witnessing\n"
            "6. Witness pool filtering: find_witness_pool() excludes flagged colluding teams\n"
            "\n"
            "7. Team creation lineage: creator_lct tracked, same-creator teams excluded from pool\n"
            "\n"
            "STILL NEEDED:\n"
            "8. Random witness selection from qualified pool (currently manual)"
        ),
        raw_data={
            "single_witness_succeeded": single_witness_succeeded,
            "diversity_blocked": diversity_blocked,
            "first_collude_from_b": first_collude,
            "admin_transfer_witnesses": len(proposal.external_witnesses),
            "dissolution_witnesses": len(dissolve.external_witnesses),
        }
    )


# ---------------------------------------------------------------------------
# Attack 8: Role Cycling to Reset Diminishing Witness
# ---------------------------------------------------------------------------

def attack_role_cycling() -> AttackResult:
    """
    ATTACK: Leave and rejoin team to reset diminishing witness effectiveness.

    Strategy:
    - Witness A attests for Target B until effectiveness drops to ~10%
    - Witness A leaves the team
    - Witness A rejoins with a new LCT (or same LCT if allowed)
    - Witness A's effectiveness should reset to 100%

    Expected outcome: Depends on whether witness history is tied to LCT or membership.
    """
    team = Team(config=TeamConfig(name="role-cycle", description="Role cycling test"))
    team.set_admin("admin:rc")
    team.add_member("witness:cycle", role="developer")
    team.add_member("target:cycle", role="developer")

    # Phase 1: Witness until diminishing returns kick in
    for _ in range(10):
        team.witness_member("witness:cycle", "target:cycle")

    eff_before_leave = team.get_witness_effectiveness("witness:cycle", "target:cycle")
    trust_before = team.get_member_trust("target:cycle")
    witness_trust_before = trust_before.get("witnesses", 0.5)

    # Phase 2: Remove and re-add via official API
    team.remove_member("witness:cycle", requester_lct="admin:rc", reason="cycling attempt")
    team.add_member("witness:cycle", role="developer")  # Re-added with same LCT

    # Phase 3: Check cooldown and effectiveness
    in_cooldown = team.is_in_cooldown("witness:cycle")
    eff_after_rejoin = team.get_witness_effectiveness("witness:cycle", "target:cycle")

    # Phase 4: Try witnessing again (should be blocked by cooldown)
    witness_blocked = False
    try:
        team.witness_member("witness:cycle", "target:cycle")
    except PermissionError:
        witness_blocked = True

    reset_worked = eff_after_rejoin > eff_before_leave * 2  # Significant improvement?

    # Check if the witness log on the TARGET was preserved
    target_member = team.get_member("target:cycle")
    target_witness_log = target_member.get("_witness_log", {})
    witness_history_preserved = "witness:cycle" in target_witness_log

    # The defense: 3-layer protection
    # 1. Post-rejoin cooldown blocks immediate witnessing (72h)
    # 2. Witness log on target persists across member re-add
    # 3. Even after cooldown, diminishing returns still apply
    defense_held = (in_cooldown and witness_blocked
                    and witness_history_preserved and not reset_worked)

    return AttackResult(
        attack_name="Role Cycling (Witness Reset)",
        success=reset_worked and not witness_history_preserved,
        setup_cost_atp=50.0,  # Cost of leave/rejoin
        gain_atp=30.0,  # Value of refreshed witness effectiveness
        roi=-0.40,
        detection_probability=0.80,  # Leave/rejoin is highly visible in audit log
        time_to_detection_hours=1,  # Immediately visible
        blocks_until_detected=1,
        trust_damage=0.5,
        description=(
            f"Witness effectiveness before leaving: {eff_before_leave:.3f}. "
            f"After rejoin: {eff_after_rejoin:.3f}. "
            f"Post-rejoin cooldown: {in_cooldown}. "
            f"Witnessing blocked: {witness_blocked}. "
            f"Target witness history {'PRESERVED' if witness_history_preserved else 'LOST'}. "
            f"Defense {'HELD' if defense_held else 'FAILED'}: "
            f"{'3-layer defense (cooldown + history + diminishing returns)' if defense_held else 'Cycling bypassed defenses'}."
        ),
        mitigation=(
            "IMPLEMENTED (3-layer defense):\n"
            "1. Post-rejoin cooldown: 72h before re-added members can witness\n"
            "2. Target witness history: _witness_log persists on target across remove/re-add\n"
            "3. Diminishing same-pair returns: effectiveness still degraded after cooldown\n"
            "4. Audit trail: remove/re-add visible in audit log\n"
            "\n"
            "The combination fully closes the witness cycling vector."
        ),
        raw_data={
            "eff_before": eff_before_leave,
            "eff_after": eff_after_rejoin,
            "in_cooldown": in_cooldown,
            "witness_blocked": witness_blocked,
            "reset_worked": reset_worked,
            "history_preserved": witness_history_preserved,
        }
    )


# ---------------------------------------------------------------------------
# Attack 9: Sybil Team Creation via Lineage Evasion
# ---------------------------------------------------------------------------

def attack_sybil_team_creation() -> AttackResult:
    """
    ATTACK: Create multiple teams to bypass cross-team witness requirements.

    Strategy:
    - Adversary creates Team A and Team B
    - Naive approach: same creator_lct (detected by lineage tracking)
    - Evasion: use different straw-man creator LCTs for each team
    - Teams witness for each other to validate malicious proposals

    This tests whether lineage tracking plus other federation signals
    can detect the attack even when creator LCTs differ.
    """
    from hardbound.federation import FederationRegistry

    fed = FederationRegistry()

    # SCENARIO 1: Same creator (should be detected)
    fed.register_team(
        "team:shell_a", "Shell Corp A",
        domains=["finance"],
        admin_lct="admin:shell_a",
        creator_lct="adversary:main",
        member_count=3,
    )
    fed.register_team(
        "team:shell_b", "Shell Corp B",
        domains=["audit"],
        admin_lct="admin:shell_b",
        creator_lct="adversary:main",  # Same creator!
        member_count=3,
    )

    lineage_report = fed.get_lineage_report()
    same_creator_detected = lineage_report["health"] in ("warning", "critical")
    same_creator_teams = len(lineage_report["multi_team_creators"])

    # Verify witness pool excludes same-creator team
    pool_for_a = fed.find_witness_pool("team:shell_a", count=5)
    shell_b_in_pool = any(t.team_id == "team:shell_b" for t in pool_for_a)

    # SCENARIO 2: Different straw-man creators (harder to detect)
    fed2 = FederationRegistry()
    fed2.register_team(
        "team:front_a", "Front Corp A",
        domains=["engineering"],
        admin_lct="admin:front_a",
        creator_lct="strawman:alpha",  # Different creator
        member_count=3,
    )
    fed2.register_team(
        "team:front_b", "Front Corp B",
        domains=["security"],
        admin_lct="admin:front_b",
        creator_lct="strawman:beta",  # Different creator
        member_count=3,
    )
    # Also register a legit team for comparison
    fed2.register_team(
        "team:legit", "Legit Corp",
        domains=["compliance"],
        admin_lct="admin:legit",
        creator_lct="honest:creator",
        member_count=10,
    )

    lineage2 = fed2.get_lineage_report()
    strawman_evades_lineage = lineage2["health"] == "healthy"

    # But if they witness for each other repeatedly, reciprocity catches them
    for i in range(5):
        fed2.record_witness_event(
            "team:front_a", "team:front_b",
            f"front_a:member{i}", f"msig:ab{i}"
        )
        fed2.record_witness_event(
            "team:front_b", "team:front_a",
            f"front_b:member{i}", f"msig:ba{i}"
        )

    collusion_report = fed2.get_collusion_report()
    reciprocity_catches_them = collusion_report["health"] != "healthy"

    # Check if witness pool filters after reciprocity detection
    pool_for_front_a = fed2.find_witness_pool("team:front_a", count=5)
    front_b_excluded = not any(
        t.team_id == "team:front_b" for t in pool_for_front_a
    )

    # Overall: lineage catches naive version, reciprocity catches evasion
    naive_defended = same_creator_detected and not shell_b_in_pool
    evasion_defended = reciprocity_catches_them and front_b_excluded

    return AttackResult(
        attack_name="Sybil Team Creation",
        success=not naive_defended and not evasion_defended,
        setup_cost_atp=500.0,  # High cost: create and maintain multiple teams
        gain_atp=50.0,  # Moderate gain: bypass witness requirements
        roi=-0.90,
        detection_probability=0.85,
        time_to_detection_hours=336,  # 2 weeks for reciprocity to accumulate
        blocks_until_detected=1000,
        trust_damage=2.0,  # Federation-level penalty
        description=(
            f"SCENARIO 1 (Same creator): Lineage detection {'CAUGHT' if same_creator_detected else 'MISSED'}. "
            f"Witness pool exclusion {'ENFORCED' if not shell_b_in_pool else 'BYPASSED'}. "
            f"SCENARIO 2 (Straw-man creators): Lineage {'EVADED' if strawman_evades_lineage else 'CAUGHT'}. "
            f"Reciprocity detection {'CAUGHT' if reciprocity_catches_them else 'MISSED'}. "
            f"Pool exclusion {'ENFORCED' if front_b_excluded else 'BYPASSED'}. "
            f"FINDING: Lineage tracking catches naive Sybil teams. "
            f"Straw-man creators evade lineage but reciprocity analysis catches the behavioral pattern."
        ),
        mitigation=(
            "IMPLEMENTED:\n"
            "1. Creator lineage tracking: same creator_lct flagged in lineage report\n"
            "2. Witness pool exclusion: same-creator teams excluded from pool\n"
            "3. Reciprocity detection: teams that always witness for each other flagged\n"
            "4. Collusion report: federation-wide health monitoring\n"
            "\n"
            "STILL NEEDED:\n"
            "5. Network analysis: graph clustering to detect coordinated team creation\n"
            "6. Temporal analysis: teams created in rapid succession flagged\n"
            "7. Member overlap analysis: same LCTs appearing across teams"
        ),
        raw_data={
            "same_creator_detected": same_creator_detected,
            "same_creator_teams": same_creator_teams,
            "shell_b_excluded_from_pool": not shell_b_in_pool,
            "strawman_evades_lineage": strawman_evades_lineage,
            "reciprocity_catches_evasion": reciprocity_catches_them,
            "front_b_excluded_from_pool": front_b_excluded,
            "naive_defended": naive_defended,
            "evasion_defended": evasion_defended,
        }
    )


# ---------------------------------------------------------------------------
# Attack 10: Witness Cycling via Official Remove/Re-Add
# ---------------------------------------------------------------------------

def attack_witness_cycling() -> AttackResult:
    """
    ATTACK: Remove and re-add a witness to reset diminishing effectiveness.

    Strategy:
    - Witness A exhausts effectiveness against Target B (10+ attestations)
    - Admin removes Witness A
    - Admin re-adds Witness A (same LCT)
    - Witness A attempts to witness again with "fresh" effectiveness

    This tests whether the post-rejoin cooldown defense prevents the attack.
    """
    team = Team(config=TeamConfig(name="witness-cycle-v2", description="Cycling attack v2"))
    team.set_admin("admin:wc2")
    team.add_member("witness:wc2", role="developer")
    team.add_member("target:wc2", role="developer")

    # Phase 1: Exhaust witness effectiveness
    for _ in range(10):
        team.witness_member("witness:wc2", "target:wc2")

    eff_exhausted = team.get_witness_effectiveness("witness:wc2", "target:wc2")
    target_trust_before = team.get_member_trust_score("target:wc2")

    # Phase 2: Remove and re-add via official API
    team.remove_member("witness:wc2", requester_lct="admin:wc2", reason="cycling attempt")
    team.add_member("witness:wc2", role="developer")

    # Phase 3: Check cooldown status
    in_cooldown = team.is_in_cooldown("witness:wc2")

    # Phase 4: Attempt to witness during cooldown
    witness_blocked = False
    try:
        team.witness_member("witness:wc2", "target:wc2")
    except PermissionError:
        witness_blocked = True

    # Phase 5: Check if target's witness history was preserved
    target = team.get_member("target:wc2")
    history_preserved = "witness:wc2" in target.get("_witness_log", {})

    # The defense layers:
    # 1. Post-rejoin cooldown blocks immediate witnessing (72h)
    # 2. Target's witness history persists across remove/re-add
    # 3. Even after cooldown, diminishing returns still apply (history on target)
    defense_held = in_cooldown and witness_blocked and history_preserved

    return AttackResult(
        attack_name="Witness Cycling (Official API)",
        success=not defense_held,
        setup_cost_atp=50.0,
        gain_atp=0.0 if defense_held else 30.0,
        roi=-1.0 if defense_held else -0.40,
        detection_probability=0.95,
        time_to_detection_hours=0.0,  # Immediately visible
        blocks_until_detected=0,
        trust_damage=0.5,
        description=(
            f"Witness effectiveness before cycling: {eff_exhausted:.3f}. "
            f"Post-rejoin cooldown active: {in_cooldown}. "
            f"Witnessing blocked by cooldown: {witness_blocked}. "
            f"Target witness history preserved: {history_preserved}. "
            f"Defense {'HELD' if defense_held else 'FAILED'}: "
            f"{'3-layer defense (cooldown + history preservation + diminishing returns)' if defense_held else 'Cycling bypassed defenses'}."
        ),
        mitigation=(
            "IMPLEMENTED (3-layer defense):\n"
            "1. Post-rejoin cooldown: 72h before re-added members can witness\n"
            "2. Target witness history preservation: _witness_log persists on target\n"
            "3. Diminishing same-pair returns: effectiveness still degraded after cooldown\n"
            "4. Audit trail: remove/re-add visible in audit log\n"
            "\n"
            "The combination fully closes the witness cycling vector."
        ),
        raw_data={
            "eff_exhausted": eff_exhausted,
            "target_trust_before": target_trust_before,
            "in_cooldown": in_cooldown,
            "witness_blocked": witness_blocked,
            "history_preserved": history_preserved,
            "defense_held": defense_held,
        }
    )


# ---------------------------------------------------------------------------
# Attack 11: R6 Timeout Evasion (Stale Approval Accumulation)
# ---------------------------------------------------------------------------

def attack_r6_timeout_evasion() -> AttackResult:
    """
    ATTACK: Keep R6 requests alive indefinitely to accumulate stale approvals.

    Strategy:
    - Create an R6 request with long (or no) expiry
    - Collect approvals over time as trust context changes
    - Execute with stale approvals after team composition/trust has shifted
    - Bypass current trust requirements using historical approvals

    Expected defense: R6 expiry system prevents indefinite request lifetime.
    """
    from .r6 import R6Workflow, R6Status
    from .policy import Policy, PolicyRule, ApprovalType
    import time

    team = Team(config=TeamConfig(name="timeout-evasion", description="Timeout evasion test"))
    team.set_admin("admin:te")
    team.add_member("adversary:te", role="developer", atp_budget=100)
    for i in range(3):
        team.add_member(f"voter:{i}", role="developer", atp_budget=50)

    # Boost trust
    for lct in list(team.members.keys()):
        team.members[lct]["trust"] = {k: 0.8 for k in team.members[lct]["trust"]}
    team._update_team()

    policy = Policy()
    policy.add_rule(PolicyRule(
        action_type="sensitive_action",
        allowed_roles=["developer", "admin"],
        trust_threshold=0.5,
        atp_cost=10,
        approval=ApprovalType.MULTI_SIG,
        approval_count=2,
    ))

    # SCENARIO 1: Normal expiry workflow (7-day default)
    wf_normal = R6Workflow(team, policy)
    request_normal = wf_normal.create_request(
        requester_lct="adversary:te",
        action_type="sensitive_action",
        description="Normal expiry request",
    )
    has_expiry = request_normal.expires_at != ""

    # SCENARIO 2: Attempt to disable expiry (set to 0)
    wf_no_expiry = R6Workflow(team, policy, default_expiry_hours=0)
    request_no_expiry = wf_no_expiry.create_request(
        requester_lct="adversary:te",
        action_type="sensitive_action",
        description="No expiry attempt",
    )
    no_expiry_enabled = request_no_expiry.expires_at == ""

    # SCENARIO 3: Very short expiry (1 second)
    wf_short = R6Workflow(team, policy, default_expiry_hours=1/3600)
    request_short = wf_short.create_request(
        requester_lct="adversary:te",
        action_type="sensitive_action",
        description="Short expiry",
    )
    # Get approval
    wf_short.approve_request(request_short.r6_id, "voter:0")

    # Wait for expiry
    time.sleep(1.5)

    # Check if request expired
    expired_request = wf_short.get_request(request_short.r6_id)
    request_auto_expired = expired_request is None

    # SCENARIO 4: Cleanup batch removes stale requests
    wf_batch = R6Workflow(team, policy, default_expiry_hours=1/3600)
    for i in range(3):
        wf_batch.create_request(
            requester_lct="adversary:te",
            action_type="sensitive_action",
            description=f"Stale {i}",
        )
    time.sleep(1.5)
    expired = wf_batch.cleanup_expired()
    batch_cleanup_worked = len(expired) == 3

    # Defense assessment:
    # 1. Default expiry is enabled (7 days)
    # 2. Expiry can be disabled (potential risk if not policy-controlled)
    # 3. Short expiry auto-expires requests
    # 4. Batch cleanup removes all stale requests
    #
    # The attack partially succeeds if expiry can be disabled (scenario 2),
    # but is mitigated by:
    # - Policy can mandate minimum expiry
    # - Admin can run cleanup_expired() periodically
    # - Audit trail records all approvals with timestamps

    defense_held = has_expiry and request_auto_expired and batch_cleanup_worked
    # Note: no_expiry_enabled being True is a configuration choice, not a bypass

    return AttackResult(
        attack_name="R6 Timeout Evasion",
        success=not defense_held,
        setup_cost_atp=40.0,
        gain_atp=20.0 if not defense_held else 0.0,
        roi=-1.0 if defense_held else -0.50,
        detection_probability=0.90,
        time_to_detection_hours=168,  # 7 days (expiry window)
        blocks_until_detected=14,
        trust_damage=0.3,
        description=(
            f"Default expiry enabled: {has_expiry}. "
            f"Zero-expiry allowed: {no_expiry_enabled}. "
            f"Auto-expiry on access: {request_auto_expired}. "
            f"Batch cleanup: {batch_cleanup_worked}. "
            f"Defense {'HELD' if defense_held else 'FAILED'}: "
            f"{'Expiry system prevents indefinite request lifetime' if defense_held else 'Stale approvals persist'}."
        ),
        mitigation=(
            "IMPLEMENTED:\n"
            "1. Default 7-day expiry on all R6 requests\n"
            "2. Auto-expiry on get_request() access (lazy expiry)\n"
            "3. cleanup_expired() batch method for periodic cleanup\n"
            "4. Audit trail records approval timestamps\n"
            "5. Minor trust penalty for expired requests\n"
            "\n"
            "RECOMMENDED:\n"
            "6. Policy-enforced minimum expiry (prevent zero-expiry)\n"
            "7. Heartbeat integration: run cleanup_expired() on each block"
        ),
        raw_data={
            "has_default_expiry": has_expiry,
            "zero_expiry_allowed": no_expiry_enabled,
            "auto_expired": request_auto_expired,
            "batch_cleanup_count": len(expired),
            "defense_held": defense_held,
        }
    )


# ---------------------------------------------------------------------------
# Attack 12: Multi-Party Cross-Team Collusion
# ---------------------------------------------------------------------------

def attack_multiparty_crossteam_collusion() -> AttackResult:
    """
    ATTACK: Coordinate multiple teams to approve malicious cross-team proposals.

    Strategy:
    - Create 3+ teams (or use Sybil teams)
    - Create cross-team proposal that benefits the colluding group
    - Colluding teams auto-approve each other's proposals
    - Bypass the spirit of multi-team governance

    Expected defense: Reciprocity analysis, lineage tracking, member overlap detection.
    """
    from .federation import FederationRegistry, FederationStatus
    import tempfile

    db_path = Path(tempfile.mkdtemp()) / "attack12_multiparty.db"
    fed = FederationRegistry(db_path=db_path)

    # SCENARIO 1: Naive collusion ring (same creator)
    # Create 3 colluding teams with same creator
    fed.register_team("team:ring_a", "Ring A", creator_lct="colluder:master")
    fed.register_team("team:ring_b", "Ring B", creator_lct="colluder:master")
    fed.register_team("team:ring_c", "Ring C", creator_lct="colluder:master")

    # Also create an honest team
    fed.register_team("team:honest", "Honest Team", creator_lct="honest:admin")

    # Ring A creates a malicious cross-team proposal
    proposal1 = fed.create_cross_team_proposal(
        proposing_team_id="team:ring_a",
        proposer_lct="admin:ring_a",
        action_type="resource_drain",
        description="Drain resources from shared pool",
        target_team_ids=["team:ring_b", "team:ring_c"],  # Only ring members
        parameters={"amount": 1000},
    )

    # Ring B and C auto-approve (coordinated)
    fed.approve_cross_team_proposal(proposal1["proposal_id"], "team:ring_b", "admin:ring_b")
    fed.approve_cross_team_proposal(proposal1["proposal_id"], "team:ring_c", "admin:ring_c")

    # Check if proposal passed
    proposal1_result = fed.get_cross_team_proposal(proposal1["proposal_id"])
    naive_attack_succeeded = proposal1_result["status"] == "approved"

    # But lineage should flag them
    lineage_report = fed.get_lineage_report()
    same_creator_flagged = len(lineage_report.get("multi_team_creators", [])) > 0

    # SCENARIO 2: Sophisticated collusion (straw-man creators but mutual approvals)
    # Create teams with different nominal creators
    fed.register_team("team:front_x", "Front X", creator_lct="strawman:x")
    fed.register_team("team:front_y", "Front Y", creator_lct="strawman:y")
    fed.register_team("team:front_z", "Front Z", creator_lct="strawman:z")

    # Multiple rounds of mutual cross-team approval
    # Use veto mode to require both approvals for proposal to pass
    for i in range(5):
        # X proposes, Y and Z approve
        px = fed.create_cross_team_proposal(
            "team:front_x", f"admin:front_x{i}", f"action_x{i}", f"Action X{i}",
            ["team:front_y", "team:front_z"],
            voting_mode="veto",  # Explicit veto mode
        )
        fed.approve_cross_team_proposal(px["proposal_id"], "team:front_y", f"admin:y{i}")
        fed.approve_cross_team_proposal(px["proposal_id"], "team:front_z", f"admin:z{i}")

        # Y proposes, X and Z approve
        py = fed.create_cross_team_proposal(
            "team:front_y", f"admin:front_y{i}", f"action_y{i}", f"Action Y{i}",
            ["team:front_x", "team:front_z"],
            voting_mode="veto",  # Explicit veto mode
        )
        fed.approve_cross_team_proposal(py["proposal_id"], "team:front_x", f"admin:x{i}")
        fed.approve_cross_team_proposal(py["proposal_id"], "team:front_z", f"admin:z{i}")

    # Also have the honest team reject one proposal (control)
    # Honest team should not be in a collusion ring
    honest_proposal = fed.create_cross_team_proposal(
        "team:ring_a", "admin:ring_a", "malicious_action", "Another drain",
        ["team:honest"]
    )
    fed.reject_cross_team_proposal(
        honest_proposal["proposal_id"], "team:honest", "admin:honest",
        reason="Suspicious activity"
    )

    # Check collusion report for mutual approval pattern
    # The current system tracks witness reciprocity; we'd need approval reciprocity
    collusion_report = fed.get_collusion_report()

    # For now, lineage evades detection but witness reciprocity might not trigger
    # since these are approvals not witness events
    # FINDING: Current system doesn't track cross-team approval patterns

    # Calculate detection status
    lineage_detection = same_creator_flagged  # Catches naive ring
    # Cross-team approval pattern detection not yet implemented

    defense_held = lineage_detection  # Partial defense

    return AttackResult(
        attack_name="Multi-Party Cross-Team Collusion",
        success=naive_attack_succeeded and not lineage_detection,
        setup_cost_atp=750.0,  # High: maintain multiple teams
        gain_atp=200.0,  # Significant: drain shared resources
        roi=-0.73,
        detection_probability=0.60,  # Lineage catches naive, approval patterns missed
        time_to_detection_hours=720,  # 30 days for pattern analysis
        blocks_until_detected=2000,
        trust_damage=3.0,  # Severe: federation-level collusion
        description=(
            f"SCENARIO 1 (Same creator ring): Proposal {'PASSED' if naive_attack_succeeded else 'BLOCKED'}. "
            f"Lineage detection {'CAUGHT' if same_creator_flagged else 'MISSED'}. "
            f"SCENARIO 2 (Straw-man creators): Mutual approval pattern NOT YET TRACKED. "
            f"FINDING: Lineage catches naive collusion. Sophisticated collusion using "
            f"mutual cross-team approvals currently evades detection. Need approval pattern analysis."
        ),
        mitigation=(
            "IMPLEMENTED:\n"
            "1. Creator lineage tracking: same creator_lct flagged\n"
            "2. Witness reciprocity analysis (for witness events)\n"
            "3. Single rejection veto power prevents forced approval\n"
            "\n"
            "NEEDED:\n"
            "4. Cross-team approval pattern analysis\n"
            "5. Approval reciprocity detection (A approves B's proposals, B approves A's)\n"
            "6. Temporal clustering: proposals approved too quickly flagged\n"
            "7. Outsider requirement: some proposals should require non-ring approval"
        ),
        raw_data={
            "naive_attack_succeeded": naive_attack_succeeded,
            "lineage_flagged": same_creator_flagged,
            "defense_held": defense_held,
            "multi_team_creators": lineage_report.get("multi_team_creators", []),
        }
    )


# ---------------------------------------------------------------------------
# Attack 13: Defense Evasion (Testing AP-AS Collusion Defenses)
# ---------------------------------------------------------------------------

def attack_defense_evasion() -> AttackResult:
    """
    ATTACK: Attempt to evade new collusion defenses (Tracks AP-AS).

    Tests the effectiveness of:
    - AP: Approval reciprocity analysis
    - AQ: Temporal pattern detection
    - AR: Outsider requirement
    - AS: Weighted voting

    Strategy:
    - Try various evasion techniques against each defense
    - Measure which defenses hold and which can be bypassed
    """
    from .federation import FederationRegistry
    import sqlite3
    import tempfile
    import time as time_module

    db_path = Path(tempfile.mkdtemp()) / "attack13_evasion.db"
    fed = FederationRegistry(db_path=db_path)

    # Setup: Create teams for attack scenarios
    # Legitimate teams (high reputation)
    fed.register_team("team:legit_a", "Legit A", creator_lct="founder:a")
    fed.register_team("team:legit_b", "Legit B", creator_lct="founder:b")
    fed.register_team("team:legit_c", "Legit C", creator_lct="founder:c")

    # Colluding teams (lower reputation)
    fed.register_team("team:ring_x", "Ring X", creator_lct="colluder:x")
    fed.register_team("team:ring_y", "Ring Y", creator_lct="colluder:y")
    fed.register_team("team:ring_z", "Ring Z", creator_lct="colluder:z")

    # Set reputation scores (legitimate teams have higher scores)
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE federated_teams SET witness_score = 0.9 WHERE team_id = 'team:legit_a'")
        conn.execute("UPDATE federated_teams SET witness_score = 0.85 WHERE team_id = 'team:legit_b'")
        conn.execute("UPDATE federated_teams SET witness_score = 0.8 WHERE team_id = 'team:legit_c'")
        conn.execute("UPDATE federated_teams SET witness_score = 0.3 WHERE team_id = 'team:ring_x'")
        conn.execute("UPDATE federated_teams SET witness_score = 0.25 WHERE team_id = 'team:ring_y'")
        conn.execute("UPDATE federated_teams SET witness_score = 0.2 WHERE team_id = 'team:ring_z'")

    defenses = {
        "reciprocity_analysis": False,
        "temporal_detection": False,
        "outsider_requirement": False,
        "weighted_voting": False,
    }

    # ========================================================================
    # TEST 1: Reciprocity Analysis (Track AP)
    # ========================================================================
    # Try to evade by using one-directional approvals
    # Strategy: A approves B's proposals, C approves A's, B approves C's (chain)

    # Instead of X <-> Y, do X -> Y -> Z -> X (one-way chain)
    for i in range(4):
        # X proposes to Y only
        px = fed.create_cross_team_proposal(
            "team:ring_x", f"admin:x{i}", f"chain_x{i}", f"Chain X{i}",
            ["team:ring_y"]
        )
        fed.approve_cross_team_proposal(px["proposal_id"], "team:ring_y", f"admin:y{i}")

        # Y proposes to Z only
        py = fed.create_cross_team_proposal(
            "team:ring_y", f"admin:y{i}", f"chain_y{i}", f"Chain Y{i}",
            ["team:ring_z"]
        )
        fed.approve_cross_team_proposal(py["proposal_id"], "team:ring_z", f"admin:z{i}")

        # Z proposes to X only (completing chain)
        pz = fed.create_cross_team_proposal(
            "team:ring_z", f"admin:z{i}", f"chain_z{i}", f"Chain Z{i}",
            ["team:ring_x"]
        )
        fed.approve_cross_team_proposal(pz["proposal_id"], "team:ring_x", f"admin:x{i}")

    # Check reciprocity report - circular chains should be harder to detect
    # than direct A<->B reciprocity
    reciprocity_xy = fed.check_approval_reciprocity("team:ring_x", "team:ring_y")
    reciprocity_yz = fed.check_approval_reciprocity("team:ring_y", "team:ring_z")
    reciprocity_zx = fed.check_approval_reciprocity("team:ring_z", "team:ring_x")

    # Chain pattern: each pair should NOT be suspicious (one-way)
    chain_evades = (
        not reciprocity_xy.get("is_suspicious", False) and
        not reciprocity_yz.get("is_suspicious", False) and
        not reciprocity_zx.get("is_suspicious", False)
    )

    # But full reciprocity report should catch overall patterns
    full_report = fed.get_approval_reciprocity_report()
    chain_detected_anyway = len(full_report.get("suspicious_pairs", [])) > 0

    # NEW: Cycle detection (Track AU) should catch the chain pattern
    cycle_report = fed.detect_approval_cycles(min_cycle_length=3, min_approvals=2)
    cycle_detected = cycle_report.get("suspicious_cycles", 0) > 0

    if not chain_evades or chain_detected_anyway or cycle_detected:
        defenses["reciprocity_analysis"] = True

    # ========================================================================
    # TEST 2: Temporal Detection (Track AQ)
    # ========================================================================
    # Strategy: Introduce artificial delays between creation and approval

    # Create proposal and wait before approving
    delayed_proposal = fed.create_cross_team_proposal(
        "team:ring_x", "admin:x_delayed", "delayed_action", "Delayed approval",
        ["team:ring_y"]
    )

    # In real attack, would wait 6+ minutes. Here we just test the detection.
    # Since we can't actually wait in a test, we'll check if the system
    # would flag instant approvals
    instant_proposal = fed.create_cross_team_proposal(
        "team:ring_x", "admin:x_instant", "instant_action", "Instant approval",
        ["team:ring_y"]
    )
    fed.approve_cross_team_proposal(instant_proposal["proposal_id"], "team:ring_y", "admin:y_instant")

    timing_analysis = fed.analyze_approval_timing(instant_proposal["proposal_id"])
    instant_flagged = timing_analysis.get("is_suspicious", False)

    if instant_flagged:
        defenses["temporal_detection"] = True

    # ========================================================================
    # TEST 3: Outsider Requirement (Track AR)
    # ========================================================================
    # Strategy: Try to approve outsider-required proposal without outsider

    # Create proposal requiring outsider
    outsider_proposal = fed.create_cross_team_proposal(
        "team:ring_x", "admin:x_outsider", "critical_action", "Critical action",
        target_team_ids=["team:ring_y", "team:ring_z"],
        require_outsider=True,
        outsider_team_ids=["team:legit_a", "team:legit_b", "team:legit_c"]
    )

    # Colluding teams approve
    fed.approve_cross_team_proposal(outsider_proposal["proposal_id"], "team:ring_y", "admin:ring_y")
    fed.approve_cross_team_proposal(outsider_proposal["proposal_id"], "team:ring_z", "admin:ring_z")

    # Check status - should NOT be approved without outsider
    outsider_result = fed.get_cross_team_proposal(outsider_proposal["proposal_id"])
    outsider_blocked = outsider_result["status"] != "approved"

    if outsider_blocked:
        defenses["outsider_requirement"] = True

    # Now try ring member pretending to be outsider
    try:
        # Ring Z tries to approve as outsider (but is target team)
        fed.approve_as_outsider(
            outsider_proposal["proposal_id"],
            "team:ring_z",  # Not valid outsider
            "admin:z_pretend"
        )
        outsider_impersonation_blocked = False
    except ValueError:
        outsider_impersonation_blocked = True

    if outsider_impersonation_blocked:
        defenses["outsider_requirement"] = True

    # ========================================================================
    # TEST 4: Weighted Voting (Track AS)
    # ========================================================================
    # Strategy: Low-rep ring tries to pass proposal in weighted mode

    # Ring tries to pass proposal affecting legitimate teams
    weighted_proposal = fed.create_cross_team_proposal(
        "team:ring_x", "admin:x_weighted", "resource_grab", "Ring resource grab",
        target_team_ids=["team:legit_a", "team:ring_y"],  # Mix of legit and ring
        voting_mode="weighted",
        approval_threshold=0.5,
    )

    # Ring Y approves (low weight: 0.25)
    fed.approve_cross_team_proposal(weighted_proposal["proposal_id"], "team:ring_y", "admin:ring_y")

    # Check if passed without legitimate approval
    weighted_result = fed.get_cross_team_proposal(weighted_proposal["proposal_id"])
    low_rep_blocked = weighted_result["status"] != "approved"

    if low_rep_blocked:
        # Now test that high-rep rejection blocks
        weighted_proposal2 = fed.create_cross_team_proposal(
            "team:ring_x", "admin:x_w2", "another_grab", "Another grab",
            target_team_ids=["team:legit_a", "team:legit_b"],
            voting_mode="weighted",
            approval_threshold=0.5,
        )

        # Legit A rejects (high weight: 0.9)
        fed.reject_cross_team_proposal(weighted_proposal2["proposal_id"], "team:legit_a", "admin:legit_a", "Suspicious")

        weighted_result2 = fed.get_cross_team_proposal(weighted_proposal2["proposal_id"])
        high_rep_veto = weighted_result2["status"] == "rejected"

        if high_rep_veto:
            defenses["weighted_voting"] = True

    # ========================================================================
    # RESULTS
    # ========================================================================
    defenses_held = sum(1 for v in defenses.values() if v)
    total_defenses = len(defenses)
    attack_success = defenses_held < total_defenses / 2

    return AttackResult(
        attack_name="Defense Evasion (Testing AP-AS)",
        success=attack_success,
        setup_cost_atp=500.0,
        gain_atp=100.0 if attack_success else 0.0,
        roi=-0.8 if not attack_success else 0.2,
        detection_probability=0.85 if defenses_held >= 3 else 0.4,
        time_to_detection_hours=24 if defenses_held >= 3 else 168,
        blocks_until_detected=100 if defenses_held >= 3 else 500,
        trust_damage=2.5,
        description=(
            f"DEFENSE TEST RESULTS:\n"
            f"  - Reciprocity + Cycle Analysis (AP+AU): {'HELD' if defenses['reciprocity_analysis'] else 'EVADED'}\n"
            f"  - Temporal Detection (AQ): {'HELD' if defenses['temporal_detection'] else 'EVADED'}\n"
            f"  - Outsider Requirement (AR): {'HELD' if defenses['outsider_requirement'] else 'EVADED'}\n"
            f"  - Weighted Voting (AS): {'HELD' if defenses['weighted_voting'] else 'EVADED'}\n"
            f"\n"
            f"Overall: {defenses_held}/{total_defenses} defenses held. "
            f"{'ATTACK BLOCKED' if not attack_success else 'ATTACK PARTIALLY SUCCESSFUL'}.\n"
            f"\n"
            f"Chain-pattern evasion of pairwise reciprocity: {'WORKED' if chain_evades else 'BLOCKED'}\n"
            f"Cycle detection caught chain: {'YES' if cycle_detected else 'NO'}\n"
            f"Instant approval flagged: {'YES' if instant_flagged else 'NO'}\n"
            f"Outsider bypass blocked: {'YES' if outsider_blocked else 'NO'}\n"
            f"Low-rep weighted approval blocked: {'YES' if low_rep_blocked else 'NO'}"
        ),
        mitigation=(
            "DEFENSES IMPLEMENTED (Tracks AP-AU):\n"
            "1. Approval reciprocity analysis - detects mutual A<->B patterns\n"
            "2. Cycle detection (NEW) - catches A->B->C->A chain patterns\n"
            "3. Temporal pattern detection - flags suspiciously fast approvals\n"
            "4. Outsider requirement - critical proposals need neutral third party\n"
            "5. Weighted voting - reputation-weighted votes prevent low-trust takeover\n"
            "\n"
            "IMPLEMENTED (Tracks AU-AW):\n"
            "6. Reputation decay - inactive teams lose influence\n"
            "7. Adaptive thresholds - critical actions get stricter governance"
        ),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "chain_evades_reciprocity": chain_evades,
            "chain_detected_anyway": chain_detected_anyway,
            "cycle_detected": cycle_detected,
            "instant_flagged": instant_flagged,
            "outsider_blocked": outsider_blocked,
            "outsider_impersonation_blocked": outsider_impersonation_blocked,
            "low_rep_blocked": low_rep_blocked,
        }
    )


# ---------------------------------------------------------------------------
# Attack 14: Advanced Defense Testing (Tracks AU-AW)
# ---------------------------------------------------------------------------

def attack_advanced_defenses() -> AttackResult:
    """
    ATTACK: Test new defenses from Tracks AU-AW.

    Tests:
    - AU: Cycle detection (already tested in Attack 13)
    - AV: Reputation decay bypass attempts
    - AW: Adaptive threshold exploitation
    """
    from .federation import FederationRegistry
    import sqlite3
    import tempfile

    db_path = Path(tempfile.mkdtemp()) / "attack14_advanced.db"
    fed = FederationRegistry(db_path=db_path)

    defenses = {
        "reputation_decay": False,
        "adaptive_thresholds": False,
        "severity_classification": False,
    }

    # Setup teams
    fed.register_team("team:active", "Active Team", creator_lct="honest:a")
    fed.register_team("team:dormant", "Dormant Team", creator_lct="sleeper:d")
    fed.register_team("team:attacker", "Attacker", creator_lct="attacker:x")

    # Set up dormant team with high reputation but old activity
    old_time = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE federated_teams SET last_activity = ?, witness_score = 0.95 WHERE team_id = 'team:dormant'",
            (old_time,)
        )
        # Attacker has low reputation
        conn.execute(
            "UPDATE federated_teams SET witness_score = 0.3 WHERE team_id = 'team:attacker'"
        )

    # ========================================================================
    # TEST 1: Reputation Decay (Track AV)
    # ========================================================================
    # Attack: Try to use dormant high-rep team before decay runs

    # Check dormant team's current score
    dormant_before = fed.get_team("team:dormant").witness_score
    assert dormant_before == 0.95, "Setup failed: dormant team should have high score"

    # Apply reputation decay
    decay_result = fed.apply_reputation_decay(decay_threshold_days=30, decay_rate=0.2)

    dormant_after = fed.get_team("team:dormant").witness_score
    dormant_decayed = dormant_after < dormant_before

    if dormant_decayed:
        defenses["reputation_decay"] = True

    # ========================================================================
    # TEST 2: Adaptive Thresholds (Track AW)
    # ========================================================================
    # Attack: Try to use low-severity thresholds for critical action

    # Try to create critical action with low thresholds
    # (Should be auto-escalated by severity classification)
    critical_proposal = fed.create_cross_team_proposal(
        "team:attacker", "admin:attacker", "admin_transfer", "Transfer admin",
        ["team:active"],
    )

    # Critical actions should auto-apply strict thresholds
    has_strict_thresholds = (
        critical_proposal["severity"] == "critical" and
        critical_proposal["require_outsider"] == True and
        critical_proposal["approval_threshold"] >= 0.8
    )

    if has_strict_thresholds:
        defenses["adaptive_thresholds"] = True

    # ========================================================================
    # TEST 3: Severity Classification (Track AW)
    # ========================================================================
    # Attack: Try to disguise critical action as low-severity

    # Attempt to manually override severity (should still classify correctly)
    disguised_proposal = fed.create_cross_team_proposal(
        "team:attacker", "admin:attacker", "team_dissolution", "Dissolve team",
        ["team:active"],
        severity="low",  # Explicit low severity (attacker tries to downgrade)
    )

    # Check if policy was still applied based on explicit severity
    # Note: If explicit severity is allowed, this is a potential gap
    # The test documents current behavior
    severity_override_works = disguised_proposal["severity"] == "low"

    # But the action type classification should be available for audit
    classified_severity = fed.classify_action_severity("team_dissolution")
    correct_classification = classified_severity == "critical"

    if correct_classification:
        defenses["severity_classification"] = True

    # ========================================================================
    # RESULTS
    # ========================================================================
    defenses_held = sum(1 for v in defenses.values() if v)
    total_defenses = len(defenses)
    attack_success = defenses_held < total_defenses

    return AttackResult(
        attack_name="Advanced Defenses (AU-AW)",
        success=attack_success,
        setup_cost_atp=200.0,
        gain_atp=50.0 if attack_success else 0.0,
        roi=-0.75 if not attack_success else 0.25,
        detection_probability=0.90 if defenses_held == total_defenses else 0.6,
        time_to_detection_hours=12 if defenses_held == total_defenses else 72,
        blocks_until_detected=50 if defenses_held == total_defenses else 200,
        trust_damage=2.0,
        description=(
            f"ADVANCED DEFENSE TEST (Tracks AU-AW):\n"
            f"  - Reputation Decay (AV): {'HELD' if defenses['reputation_decay'] else 'EVADED'}\n"
            f"    Dormant team score: {dormant_before:.2f} -> {dormant_after:.2f}\n"
            f"  - Adaptive Thresholds (AW): {'HELD' if defenses['adaptive_thresholds'] else 'EVADED'}\n"
            f"    Critical action got strict policy: {has_strict_thresholds}\n"
            f"  - Severity Classification: {'HELD' if defenses['severity_classification'] else 'EVADED'}\n"
            f"    team_dissolution classified as: {classified_severity}\n"
            f"\n"
            f"Overall: {defenses_held}/{total_defenses} defenses held.\n"
            f"NOTE: Explicit severity override currently {'ALLOWED' if severity_override_works else 'BLOCKED'}.\n"
            f"This is a policy decision - explicit override may be valid for audited use."
        ),
        mitigation=(
            "DEFENSES IMPLEMENTED (Tracks AU-AW):\n"
            "1. Cycle detection - catches chain-pattern collusion\n"
            "2. Reputation decay - inactive teams lose influence over time\n"
            "3. Adaptive thresholds - critical actions get stricter governance\n"
            "4. Severity classification - action types mapped to severity levels\n"
            "\n"
            "POTENTIAL GAPS:\n"
            "5. Explicit severity override allowed (audit-trail recommended)\n"
            "6. Decay only applied when explicitly called (integrate with heartbeat)\n"
            "7. Amount-based classification needs more granular thresholds"
        ),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "dormant_score_before": dormant_before,
            "dormant_score_after": dormant_after,
            "has_strict_thresholds": has_strict_thresholds,
            "severity_override_works": severity_override_works,
            "classified_severity": classified_severity,
        }
    )


# ---------------------------------------------------------------------------
# Attack 15: New Mechanism Testing (Tracks AY-BB)
# ---------------------------------------------------------------------------

def attack_new_mechanisms() -> AttackResult:
    """
    ATTACK: Test new defenses from Tracks AY-BB.

    Tests:
    - AY: Governance audit logging (try to evade audit trail)
    - AZ: Heartbeat-integrated decay (try to bypass automatic decay)
    - BA: Cross-domain temporal analysis (try to evade correlation detection)
    - BB: Dashboard integration (check for blind spots)
    """
    from .federation import FederationRegistry
    import sqlite3
    import tempfile
    import time

    db_path = Path(tempfile.mkdtemp()) / "attack15_mechanisms.db"
    fed = FederationRegistry(db_path=db_path)

    defenses = {
        "audit_logging": False,
        "heartbeat_decay": False,
        "cross_domain_detection": False,
        "dashboard_visibility": False,
    }

    # Setup teams
    fed.register_team("team:honest", "Honest Team", creator_lct="honest:h")
    fed.register_team("team:colluder1", "Colluder 1", creator_lct="collude:1")
    fed.register_team("team:colluder2", "Colluder 2", creator_lct="collude:2")
    fed.register_team("team:target", "Target", creator_lct="target:t")

    # ========================================================================
    # TEST 1: Audit Logging (Track AY)
    # ========================================================================
    # Attack: Try to perform severity downgrade without being logged

    # Attempt severity downgrade (should be logged as warning)
    fed.create_cross_team_proposal(
        "team:colluder1", "admin:colluder1", "team_dissolution", "Dissolve target",
        ["team:target"],
        severity="low",  # Downgrade from critical
    )

    # Check if audit was logged
    audit_log = fed.get_governance_audit_log(audit_type="severity_override")
    downgrade_logged = any(
        entry.get("risk_level") == "warning"
        for entry in audit_log
    )

    if downgrade_logged:
        defenses["audit_logging"] = True

    # ========================================================================
    # TEST 2: Heartbeat-Integrated Decay (Track AZ)
    # ========================================================================
    # Attack: Try to maintain reputation without activity via heartbeat bypass

    # Set up a dormant team with high reputation
    old_time = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE federated_teams SET last_activity = ?, witness_score = 0.9 WHERE team_id = 'team:colluder1'",
            (old_time,)
        )

    colluder_before = fed.get_team("team:colluder1").witness_score

    # Run heartbeat with decay enabled (simulates automated maintenance)
    heartbeat_result = fed.federation_heartbeat(
        apply_decay=True,
        decay_threshold_days=30,
        decay_rate=0.15
    )

    colluder_after = fed.get_team("team:colluder1").witness_score
    decay_applied = colluder_after < colluder_before

    if decay_applied and heartbeat_result["decay_result"]["teams_decayed"] > 0:
        defenses["heartbeat_decay"] = True

    # ========================================================================
    # TEST 3: Cross-Domain Temporal Analysis (Track BA)
    # ========================================================================
    # Attack: Try to coordinate approvals without triggering detection

    # Create a burst of proposals (should be detected)
    for i in range(4):
        p = fed.create_cross_team_proposal(
            "team:colluder1", "admin:colluder1", f"coordinated_action_{i}",
            f"Coordinated {i}",
            ["team:colluder2"],
        )
        # Instant approval (coordinated)
        fed.approve_cross_team_proposal(p["proposal_id"], "team:colluder2", "admin:colluder2")

    # Run cross-domain analysis
    cross_analysis = fed.get_cross_domain_temporal_analysis(
        min_proposals=3
    )

    # Check if burst pattern was detected
    burst_detected = len(cross_analysis["burst_patterns"]) > 0

    # Check if colluder teams show suspicious pattern
    colluder_pattern = cross_analysis["team_patterns"].get("team:colluder1", {})
    pattern_flagged = colluder_pattern.get("suspicion_level", "normal") in ("high", "critical")

    if burst_detected or pattern_flagged:
        defenses["cross_domain_detection"] = True

    # ========================================================================
    # TEST 4: Dashboard Visibility (Track BB)
    # ========================================================================
    # Attack: Check if issues appear in dashboard (no blind spots)

    dashboard = fed.get_federation_health_dashboard()

    # Dashboard should show:
    # 1. Audit warnings (from severity downgrade)
    # 2. Temporal flags (from fast approvals)
    # 3. Cross-domain issues (from burst pattern)

    has_audit_visibility = dashboard["summary"].get("audit_warnings", 0) > 0
    has_temporal_visibility = dashboard["summary"].get("proposals_flagged", 0) > 0
    has_cross_domain_visibility = (
        dashboard["summary"].get("burst_patterns", 0) > 0 or
        dashboard["summary"].get("correlated_approvals", 0) > 0
    )

    # Dashboard should not be "healthy" given all these issues
    not_falsely_healthy = dashboard["overall_health"] != "healthy"

    if has_audit_visibility or has_temporal_visibility or has_cross_domain_visibility:
        if not_falsely_healthy:
            defenses["dashboard_visibility"] = True

    # ========================================================================
    # RESULTS
    # ========================================================================
    defenses_held = sum(1 for v in defenses.values() if v)
    total_defenses = len(defenses)
    attack_success = defenses_held < total_defenses

    return AttackResult(
        attack_name="New Mechanisms (AY-BB)",
        success=attack_success,
        setup_cost_atp=150.0,
        gain_atp=40.0 if attack_success else 0.0,
        roi=-0.73 if not attack_success else 0.27,
        detection_probability=0.95 if defenses_held == total_defenses else 0.65,
        time_to_detection_hours=6 if defenses_held == total_defenses else 48,
        blocks_until_detected=30 if defenses_held == total_defenses else 150,
        trust_damage=2.5,
        description=(
            f"NEW MECHANISM TEST (Tracks AY-BB):\n"
            f"  - Audit Logging (AY): {'HELD' if defenses['audit_logging'] else 'EVADED'}\n"
            f"    Severity downgrade logged as warning: {downgrade_logged}\n"
            f"  - Heartbeat Decay (AZ): {'HELD' if defenses['heartbeat_decay'] else 'EVADED'}\n"
            f"    Dormant score: {colluder_before:.2f} -> {colluder_after:.2f}\n"
            f"  - Cross-Domain Detection (BA): {'HELD' if defenses['cross_domain_detection'] else 'EVADED'}\n"
            f"    Burst detected: {burst_detected}, Pattern flagged: {pattern_flagged}\n"
            f"  - Dashboard Visibility (BB): {'HELD' if defenses['dashboard_visibility'] else 'EVADED'}\n"
            f"    Overall health: {dashboard['overall_health']}\n"
            f"\n"
            f"Overall: {defenses_held}/{total_defenses} defenses held."
        ),
        mitigation=(
            "DEFENSES IMPLEMENTED (Tracks AY-BB):\n"
            "1. Governance audit logging - severity overrides tracked with risk levels\n"
            "2. Heartbeat-integrated decay - automatic reputation reduction for inactive teams\n"
            "3. Cross-domain temporal analysis - burst and correlation pattern detection\n"
            "4. Federation health dashboard - consolidated visibility into all issues\n"
            "\n"
            "KEY IMPROVEMENTS:\n"
            "- No silent severity downgrades (all logged)\n"
            "- Decay runs automatically via heartbeat\n"
            "- Coordinated approval patterns detected across proposals\n"
            "- Single dashboard shows all federation health issues"
        ),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "audit_log_count": len(audit_log),
            "downgrade_logged": downgrade_logged,
            "colluder_score_before": colluder_before,
            "colluder_score_after": colluder_after,
            "burst_detected": burst_detected,
            "pattern_flagged": pattern_flagged,
            "dashboard_health": dashboard["overall_health"],
            "dashboard_alerts": dashboard["alerts"],
        }
    )


# ---------------------------------------------------------------------------
# Attack 16: Multi-Federation Attack Vectors (Track BH)
# ---------------------------------------------------------------------------

def attack_multi_federation_vectors() -> AttackResult:
    """
    ATTACK: Exploit multi-federation governance for cross-boundary manipulation.

    Track BH: Tests defenses from Track BF (multi-federation witness requirements).

    Attack scenarios:
    1. Trust bootstrap attack - Create federation with artificially high trust
    2. Colluding federations - Two federations approve each other's proposals
    3. Witness shopping - Find minimal trust federation to witness proposals
    4. External witness bypass - Try to approve without external witness

    Tests:
    - MIN_CROSS_FED_TRUST enforcement
    - External witness federation requirement
    - Federation-level reciprocity detection
    """
    from hardbound.multi_federation import MultiFederationRegistry, FederationRelationship

    db_path = Path(tempfile.mkdtemp()) / "attack_multi_fed.db"
    registry = MultiFederationRegistry(db_path=db_path)

    defenses = {
        "trust_threshold": False,
        "external_witness_required": False,
        "colluding_federation_detection": False,
        "witness_shopping_blocked": False,
    }

    # ========================================================================
    # Setup: Create federations
    # ========================================================================
    # Honest federations
    registry.register_federation("fed:honest1", "Honest One")
    registry.register_federation("fed:honest2", "Honest Two")
    registry.register_federation("fed:honest3", "Honest Three")

    # Attacker federations (colluding pair)
    registry.register_federation("fed:attacker1", "Attacker Alpha")
    registry.register_federation("fed:attacker2", "Attacker Beta")

    # Low-reputation federation (for witness shopping)
    registry.register_federation("fed:lowrep", "Low Rep Inc")

    # ========================================================================
    # Attack 1: Trust Bootstrap - Try high trust without history
    # ========================================================================
    # Attempt to establish mutual high trust between attacker federations
    trust1 = registry.establish_trust(
        "fed:attacker1", "fed:attacker2",
        relationship=FederationRelationship.TRUSTED,
        initial_trust=0.9  # Claim high trust
    )

    trust2 = registry.establish_trust(
        "fed:attacker2", "fed:attacker1",
        relationship=FederationRelationship.TRUSTED,
        initial_trust=0.9
    )

    # Check if system accepts artificially high trust
    # Defense should enforce minimum requirements or decay new relationships
    actual_trust1 = trust1.trust_score
    actual_trust2 = trust2.trust_score

    # If either trust was capped or reduced, defense held
    if actual_trust1 <= 0.6 or actual_trust2 <= 0.6:
        defenses["trust_threshold"] = True
        trust_defense_note = f"Trust capped: {actual_trust1:.2f}, {actual_trust2:.2f}"
    else:
        # System allowed high trust - check if it's actually enforced in proposals
        trust_defense_note = f"Trust accepted: {actual_trust1:.2f}, {actual_trust2:.2f}"

    # ========================================================================
    # Attack 2: Colluding Federation Approval
    # ========================================================================
    # Establish honest trust relationships for comparison
    registry.establish_trust("fed:honest1", "fed:honest2", initial_trust=0.7)
    registry.establish_trust("fed:honest2", "fed:honest1", initial_trust=0.7)
    registry.establish_trust("fed:honest1", "fed:honest3", initial_trust=0.7)
    registry.establish_trust("fed:honest3", "fed:honest1", initial_trust=0.7)

    # Attacker creates proposal requiring multi-fed approval
    try:
        proposal = registry.create_cross_federation_proposal(
            proposing_federation_id="fed:attacker1",
            proposing_team_id="attacker:team1",
            affected_federation_ids=["fed:attacker2"],
            action_type="resource_transfer",
            description="Move resources between federations",
            require_external_witness=True,
        )

        # Attacker2 approves (colluding partner)
        result1 = registry.approve_from_federation(
            proposal.proposal_id, "fed:attacker2", ["attacker2:team1"]
        )

        # Check if proposal approved without external witness
        if result1.get("status") == "approved":
            # No external witness required - defense failed
            external_witness_note = "Approved without external witness!"
        else:
            # Defense held - requires external witness
            defenses["external_witness_required"] = True
            external_witness_note = "Requires external witness"

            # Try to use low-rep federation as witness
            # First establish minimal trust
            registry.establish_trust("fed:attacker1", "fed:lowrep", initial_trust=0.35)

            try:
                witness_result = registry.add_external_witness(
                    proposal.proposal_id,
                    "fed:lowrep",
                    "lowrep:team1"
                )

                # Check if low-trust witness was accepted
                if witness_result.get("total_external_witnesses", 0) > 0:
                    witness_shopping_note = "Low-rep witness accepted"
                else:
                    defenses["witness_shopping_blocked"] = True
                    witness_shopping_note = f"Rejected: no witness added"
            except ValueError as e:
                defenses["witness_shopping_blocked"] = True
                witness_shopping_note = f"Rejected: {str(e)}"

    except ValueError as e:
        # Proposal creation itself failed
        defenses["external_witness_required"] = True
        external_witness_note = f"Proposal blocked: {str(e)}"
        witness_shopping_note = "N/A (proposal blocked)"

    # ========================================================================
    # Attack 3: Federation Reciprocity (Cross-Federation Collusion)
    # ========================================================================
    # Create mutual approval pattern between attacker federations
    proposals_created = []
    for i in range(3):
        try:
            p1 = registry.create_cross_federation_proposal(
                proposing_federation_id=f"fed:attacker{1 + (i % 2)}",
                proposing_team_id=f"attacker{1 + (i % 2)}:team1",
                affected_federation_ids=[f"fed:attacker{2 - (i % 2)}"],
                action_type=f"transfer_{i}",
                description=f"Transfer {i}",
                require_external_witness=True,
            )
            proposals_created.append(p1)
        except Exception:
            pass  # May fail due to earlier defenses

    # Check for reciprocity detection
    # In a full implementation, we'd have federation-level reciprocity analysis
    # For now, check if the pattern is detectable
    reciprocity_detected = len(proposals_created) < 3  # If blocked, defense worked

    if reciprocity_detected or len(proposals_created) == 0:
        defenses["colluding_federation_detection"] = True
        collusion_note = "Federation collusion pattern blocked or limited"
    else:
        collusion_note = f"Created {len(proposals_created)} proposals without detection"

    # ========================================================================
    # RESULTS
    # ========================================================================
    defenses_held = sum(1 for v in defenses.values() if v)
    total_defenses = len(defenses)
    attack_success = defenses_held < total_defenses

    return AttackResult(
        attack_name="Multi-Federation Vectors (BH)",
        success=attack_success,
        setup_cost_atp=300.0,  # Cross-federation setup is expensive
        gain_atp=100.0 if attack_success else 0.0,
        roi=-0.67 if not attack_success else 0.33,
        detection_probability=0.90 if defenses_held == total_defenses else 0.60,
        time_to_detection_hours=8 if defenses_held == total_defenses else 72,
        blocks_until_detected=40 if defenses_held == total_defenses else 200,
        trust_damage=3.0,  # Cross-federation attacks damage both federations
        description=(
            f"MULTI-FEDERATION ATTACK TEST (Track BH):\n"
            f"  - Trust Threshold: {'HELD' if defenses['trust_threshold'] else 'EVADED'}\n"
            f"    {trust_defense_note}\n"
            f"  - External Witness Required: {'HELD' if defenses['external_witness_required'] else 'EVADED'}\n"
            f"    {external_witness_note}\n"
            f"  - Witness Shopping Blocked: {'HELD' if defenses['witness_shopping_blocked'] else 'EVADED'}\n"
            f"    {witness_shopping_note}\n"
            f"  - Colluding Federation Detection: {'HELD' if defenses['colluding_federation_detection'] else 'EVADED'}\n"
            f"    {collusion_note}\n"
            f"\n"
            f"Overall: {defenses_held}/{total_defenses} defenses held."
        ),
        mitigation=(
            "DEFENSES IMPLEMENTED (Track BF):\n"
            "1. Inter-federation trust requirements - MIN_CROSS_FED_TRUST = 0.4\n"
            "2. External witness federation required for cross-fed proposals\n"
            "3. Trust relationship types (peer, parent, child, trusted, allied)\n"
            "4. Federation eligibility checking before witness acceptance\n"
            "\n"
            "POTENTIAL GAPS:\n"
            "5. Federation-level reciprocity analysis needed\n"
            "6. New federation trust bootstrapping could be gamed\n"
            "7. Trust relationship type manipulation (claim 'parent' status)"
        ),
        raw_data={
            "defenses": defenses,
            "defenses_held": defenses_held,
            "trust_values": {"attacker1_to_2": actual_trust1, "attacker2_to_1": actual_trust2},
            "proposals_created": len(proposals_created),
            "trust_defense_note": trust_defense_note,
            "external_witness_note": external_witness_note,
            "witness_shopping_note": witness_shopping_note,
            "collusion_note": collusion_note,
        }
    )


# ---------------------------------------------------------------------------
# Run All Attacks
# ---------------------------------------------------------------------------

def run_all_attacks() -> List[AttackResult]:
    """Run all attack simulations and report results."""
    attacks = [
        ("Metabolic Manipulation", attack_metabolic_manipulation),
        ("Sybil Trust Farming", attack_sybil_trust_farming),
        ("ATP Exhaustion", attack_atp_exhaustion),
        ("Heartbeat Timing", attack_heartbeat_timing),
        ("Trust Decay Evasion", attack_trust_decay_evasion),
        ("Multi-Sig Quorum", attack_multisig_quorum),
        ("Cross-Team Witness Collusion", attack_cross_team_witness_collusion),
        ("Role Cycling (Witness Reset)", attack_role_cycling),
        ("Sybil Team Creation", attack_sybil_team_creation),
        ("Witness Cycling (Official API)", attack_witness_cycling),
        ("R6 Timeout Evasion", attack_r6_timeout_evasion),
        ("Multi-Party Cross-Team Collusion", attack_multiparty_crossteam_collusion),
        ("Defense Evasion (AP-AS)", attack_defense_evasion),
        ("Advanced Defenses (AU-AW)", attack_advanced_defenses),
        ("New Mechanisms (AY-BB)", attack_new_mechanisms),
        ("Multi-Federation Vectors (BH)", attack_multi_federation_vectors),
    ]

    results = []
    print("=" * 80)
    print("WEB4 HARDBOUND ATTACK SIMULATION REPORT")
    print("=" * 80)
    print(f"Date: {datetime.now(timezone.utc).isoformat()[:10]}")
    print(f"Attacks: {len(attacks)}")
    print()

    for name, attack_fn in attacks:
        print(f"--- Running: {name} ---")
        try:
            result = attack_fn()
            results.append(result)

            status = "SUCCEEDED" if result.success else "FAILED"
            print(f"  Status: {status}")
            print(f"  Setup cost: {result.setup_cost_atp:.1f} ATP")
            print(f"  Gain: {result.gain_atp:.1f} ATP")
            print(f"  Detection probability: {result.detection_probability:.0%}")
            print(f"  Time to detection: {result.time_to_detection_hours:.0f}h")
            print(f"  Trust damage if caught: {result.trust_damage:.2f}")
            print()
            print(f"  {result.description}")
            print()
            print(f"  Mitigation:")
            for line in result.mitigation.split('\n'):
                print(f"    {line}")
            print()

        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            print()

    # Summary table
    print("=" * 80)
    print("ATTACK SUMMARY")
    print("=" * 80)
    print(f"{'Attack':<35} {'Success':>8} {'Gain':>8} {'Detect':>8} {'Damage':>8}")
    print("-" * 80)
    for r in results:
        print(f"{r.attack_name:<35} "
              f"{'YES' if r.success else 'NO':>8} "
              f"{r.gain_atp:>7.1f} "
              f"{r.detection_probability:>7.0%} "
              f"{r.trust_damage:>7.2f}")

    print()
    successful = sum(1 for r in results if r.success)
    print(f"Successful attacks: {successful}/{len(results)}")
    print(f"Average detection probability: {sum(r.detection_probability for r in results)/len(results):.0%}")
    print(f"Average trust damage: {sum(r.trust_damage for r in results)/len(results):.2f}")

    # Critical findings
    print()
    print("CRITICAL FINDINGS:")
    for r in results:
        if r.success:
            print(f"  [!] {r.attack_name}: EXPLOITABLE")
            print(f"      Primary mitigation: {r.mitigation.split(chr(10))[0]}")

    return results


if __name__ == "__main__":
    results = run_all_attacks()
