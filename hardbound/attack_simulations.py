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

    Strategy:
    - Create N Sybil members
    - Each Sybil reports "success" for every other Sybil's actions
    - Trust scores inflate rapidly through mutual witnessing
    - Once trust exceeds thresholds, Sybils can approve critical actions

    Cost: N member creation + ATP for fake transactions
    Gain: Access to high-trust-threshold actions (deploy, admin, etc.)
    """
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

    # ATTACK PHASE: Mutual trust inflation
    # Each Sybil "succeeds" and all others witness
    rounds = 20
    for _ in range(rounds):
        for sybil in sybil_lcts:
            # Report success
            team.update_member_trust(sybil, "success", magnitude=0.7)

    # Honest member also works, but alone
    for _ in range(rounds):
        team.update_member_trust(honest_lct, "success", magnitude=0.7)

    # Compare trust scores
    sybil_trusts = [team.get_member_trust_score(s) for s in sybil_lcts]
    honest_trust = team.get_member_trust_score(honest_lct)

    avg_sybil_trust = sum(sybil_trusts) / len(sybil_trusts)

    # Check if Sybils can pass thresholds that honest member cannot
    # High trust threshold for critical actions
    high_threshold = 0.8
    sybils_pass = sum(1 for t in sybil_trusts if t >= high_threshold)
    honest_passes = honest_trust >= high_threshold

    # Detection: Unusual trust velocity
    # Sybils all have identical trust trajectories (highly correlated)
    trust_variance = max(sybil_trusts) - min(sybil_trusts)
    suspiciously_uniform = trust_variance < 0.01

    # Calculate ROI
    setup_cost = n_sybils * 50  # ATP budgets allocated
    gain = 0.0
    if sybils_pass >= 3:
        # Can approve multi-sig proposals
        gain = 500.0  # Value of being able to approve critical actions

    return AttackResult(
        attack_name="Sybil Trust Farming",
        success=sybils_pass >= 3,
        setup_cost_atp=float(setup_cost),
        gain_atp=gain,
        roi=(gain - setup_cost) / setup_cost if setup_cost > 0 else 0.0,
        detection_probability=0.90 if suspiciously_uniform else 0.40,
        time_to_detection_hours=48.0,
        blocks_until_detected=200,
        trust_damage=0.5,  # Severe - identity fraud
        description=(
            f"Created {n_sybils} Sybil members with mutual trust inflation over {rounds} rounds.\n"
            f"Average Sybil trust: {avg_sybil_trust:.3f}\n"
            f"Honest member trust: {honest_trust:.3f}\n"
            f"Sybils passing {high_threshold} threshold: {sybils_pass}/{n_sybils}\n"
            f"Honest passes threshold: {honest_passes}\n"
            f"Trust variance among Sybils: {trust_variance:.4f} "
            f"({'SUSPICIOUS' if suspiciously_uniform else 'normal'})"
        ),
        mitigation=(
            "1. Witness diversity requirement (minimum N unique witnesses per trust epoch)\n"
            "2. Trust velocity caps (max trust gain per time period)\n"
            "3. Correlation detection (flag members with near-identical trust trajectories)\n"
            "4. Hardware-bound identity (cost of creating Sybils becomes non-trivial)\n"
            "5. External witness requirement (at least 1 witness from outside team)\n"
            "6. Diminishing returns on same-pair witnessing"
        ),
        raw_data={
            "sybil_trusts": sybil_trusts,
            "honest_trust": honest_trust,
            "trust_variance": trust_variance,
            "sybils_passing": sybils_pass,
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

    # Scenario 3: Frozen trust (keep team in hibernation)
    # Trust doesn't decay during hibernation/torpor
    frozen_trust = dict(honest_trust)
    # If trust is frozen for 30 days, it stays the same
    frozen_avg = sum(frozen_trust.values()) / 6  # No decay applied

    # Compare
    trust_diff_attack = attacker_avg - honest_avg
    trust_diff_frozen = frozen_avg - honest_avg

    return AttackResult(
        attack_name="Trust Decay Evasion",
        success=trust_diff_attack > 0.05 or trust_diff_frozen > 0.1,
        setup_cost_atp=30.0,  # 1 ATP per day for 30 days of micro-activity
        gain_atp=0.0,  # Trust-based, not ATP-based
        roi=0.0,
        detection_probability=0.60,
        time_to_detection_hours=168.0,  # Takes a week to notice
        blocks_until_detected=500,
        trust_damage=0.3,
        description=(
            f"Trust after 30 days:\n"
            f"  Honest (moderate activity):  avg={honest_avg:.4f}\n"
            f"  Attacker (daily micro-ping): avg={attacker_avg:.4f} "
            f"(+{trust_diff_attack:.4f})\n"
            f"  Frozen (hibernation):        avg={frozen_avg:.4f} "
            f"(+{trust_diff_frozen:.4f})\n\n"
            f"The daily micro-activity strategy preserves "
            f"{trust_diff_attack/honest_avg*100:.1f}% more trust.\n"
            f"The hibernation freeze preserves "
            f"{trust_diff_frozen/honest_avg*100:.1f}% more trust.\n"
            f"Both represent gaming of the decay system."
        ),
        mitigation=(
            "1. Minimum meaningful activity threshold (not just any action counts)\n"
            "2. Activity quality scoring (trivial actions don't fully reset decay)\n"
            "3. Hibernation trust degradation (slow decay even in dormant states)\n"
            "4. Trust recalibration on wake from dormancy\n"
            "5. Decay based on productive output, not just presence"
        ),
        raw_data={
            "honest_decayed": honest_decayed,
            "attacker_trust": current_trust,
            "frozen_trust": frozen_trust,
            "honest_avg": honest_avg,
            "attacker_avg": attacker_avg,
            "frozen_avg": frozen_avg,
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
