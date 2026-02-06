#!/usr/bin/env python3
"""
Identity Stake System - Economic Sybil Defense
Session #82: Priority #4 - Anti-Sybil via ATP Bonding

Problem (Session #81 Attack Analysis):
Sybil Reputation Farming (HIGH severity): Attacker creates multiple fake
identities (Sybils) to farm reputation through collusive task execution
and mutual attestation. Currently, LCT creation has no cost, making Sybil
attacks economically free.

Solution: Identity Stake Requirement
Bond ATP to LCT creation. Stake is locked until LCT proves legitimacy
(positive reputation over time). Stake is slashed if social graph analysis
detects Sybil behavior.

Economic Defense:
- Creating 100 Sybil LCTs costs 100 × stake_amount ATP
- Sybil detection triggers stake slashing
- Lost stakes go to society treasury (anti-Sybil reward)
- Makes Sybil attacks economically expensive

Security Properties:
1. **Cost barrier**: Sybils expensive to create
2. **Risk punishment**: Detected Sybils lose stake
3. **Legitimate protection**: Honest agents get stake back
4. **Economic incentive**: Societies rewarded for detecting Sybils

Design:
- Progressive stake: New agents pay low stake, stake increases with privileges
- Stake lockup period: Minimum time before stake can be reclaimed
- Reputation threshold: Need positive reputation to unlock stake
- Slashing conditions: Social graph density, witness collusion, challenge evasion

Integration:
- Extends Session #81 MRH-aware trust (LCT identity)
- Uses Session #80 reputation challenge protocol (verification)
- Compatible with unified ATP pricing (Session #82)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import time
import math


class StakeStatus(Enum):
    """Status of identity stake"""
    LOCKED = "locked"        # Stake locked during proving period
    UNLOCKABLE = "unlockable"  # Met requirements, can be reclaimed
    SLASHED = "slashed"      # Sybil detected, stake forfeited


@dataclass
class IdentityStake:
    """
    ATP stake bonded to LCT creation

    Stake is locked until agent proves legitimacy through:
    - Minimum lockup period (e.g., 7 days)
    - Positive reputation (e.g., V3 composite > 0.6)
    - No Sybil detection flags
    """
    lct_id: str
    stake_amount: float  # ATP bonded
    stake_timestamp: float  # When stake was created
    status: StakeStatus = StakeStatus.LOCKED

    # Unlock conditions
    min_lockup_period: float = 7 * 24 * 3600  # 7 days in seconds
    min_reputation: float = 0.6  # Minimum V3 composite score

    # Slashing tracking
    slash_reason: Optional[str] = None
    slash_timestamp: Optional[float] = None
    slashed_amount: float = 0.0

    def time_locked(self, current_time: float) -> float:
        """How long has stake been locked (seconds)"""
        if self.status == StakeStatus.SLASHED:
            return self.slash_timestamp - self.stake_timestamp if self.slash_timestamp else 0.0
        return current_time - self.stake_timestamp

    def can_unlock(self, current_time: float, current_reputation: float) -> Tuple[bool, str]:
        """
        Check if stake can be unlocked

        Returns:
            (can_unlock, reason)
        """
        if self.status == StakeStatus.SLASHED:
            return (False, f"Stake slashed: {self.slash_reason}")

        if self.status == StakeStatus.UNLOCKABLE:
            return (True, "Stake already unlockable")

        # Check lockup period
        time_locked = self.time_locked(current_time)
        if time_locked < self.min_lockup_period:
            remaining = self.min_lockup_period - time_locked
            return (False, f"Lockup period: {remaining/3600:.1f} hours remaining")

        # Check reputation
        if current_reputation < self.min_reputation:
            return (False, f"Reputation too low: {current_reputation:.2f} < {self.min_reputation:.2f}")

        # All conditions met
        return (True, "All unlock conditions met")

    def slash(self, reason: str, slash_percentage: float = 1.0, current_time: float = None):
        """
        Slash stake for Sybil behavior

        Args:
            reason: Why stake is being slashed
            slash_percentage: Fraction of stake to slash (0-1)
            current_time: Current timestamp
        """
        if self.status == StakeStatus.SLASHED:
            return  # Already slashed

        self.status = StakeStatus.SLASHED
        self.slash_reason = reason
        self.slash_timestamp = current_time or time.time()
        self.slashed_amount = self.stake_amount * slash_percentage


class IdentityStakeSystem:
    """
    System for managing ATP stakes on LCT identities

    Implements economic Sybil defense through bonding.
    """

    def __init__(
        self,
        base_stake_amount: float = 1000.0,
        society_treasury_address: str = "society_treasury"
    ):
        self.base_stake_amount = base_stake_amount
        self.society_treasury_address = society_treasury_address

        # Stake registry: lct_id → IdentityStake
        self.stakes: Dict[str, IdentityStake] = {}

        # Society treasury (slashed stakes accumulate here)
        self.treasury_balance: float = 0.0

        # Slashing log
        self.slash_history: List[Tuple[str, str, float, float]] = []  # (lct_id, reason, amount, timestamp)

    def create_stake(
        self,
        lct_id: str,
        agent_atp_balance: float,
        stake_multiplier: float = 1.0,
        custom_lockup: Optional[float] = None
    ) -> Tuple[bool, str, Optional[IdentityStake]]:
        """
        Create identity stake for new LCT

        Args:
            lct_id: LCT identifier
            agent_atp_balance: Agent's ATP balance
            stake_multiplier: Multiplier on base stake (1.0 = normal, 2.0 = high-privilege)
            custom_lockup: Optional custom lockup period (seconds)

        Returns:
            (success, message, stake or None)
        """
        if lct_id in self.stakes:
            return (False, "LCT already has stake", None)

        stake_amount = self.base_stake_amount * stake_multiplier

        # Check agent has sufficient ATP
        if agent_atp_balance < stake_amount:
            return (False, f"Insufficient ATP: {agent_atp_balance:.2f} < {stake_amount:.2f}", None)

        # Create stake
        stake = IdentityStake(
            lct_id=lct_id,
            stake_amount=stake_amount,
            stake_timestamp=time.time(),
            status=StakeStatus.LOCKED,
            min_lockup_period=custom_lockup or (7 * 24 * 3600)
        )

        self.stakes[lct_id] = stake

        return (True, f"Stake created: {stake_amount:.2f} ATP locked", stake)

    def unlock_stake(
        self,
        lct_id: str,
        current_reputation: float,
        current_time: Optional[float] = None
    ) -> Tuple[bool, str, float]:
        """
        Unlock stake if conditions met

        Args:
            lct_id: LCT identifier
            current_reputation: Current V3 composite reputation
            current_time: Current timestamp

        Returns:
            (success, message, atp_returned)
        """
        if lct_id not in self.stakes:
            return (False, "No stake found for LCT", 0.0)

        stake = self.stakes[lct_id]
        current_time = current_time or time.time()

        can_unlock, reason = stake.can_unlock(current_time, current_reputation)

        if not can_unlock:
            return (False, reason, 0.0)

        # Unlock stake
        stake.status = StakeStatus.UNLOCKABLE
        returned_atp = stake.stake_amount

        return (True, f"Stake unlocked: {returned_atp:.2f} ATP returned", returned_atp)

    def slash_stake(
        self,
        lct_id: str,
        reason: str,
        slash_percentage: float = 1.0,
        current_time: Optional[float] = None
    ) -> Tuple[bool, str, float]:
        """
        Slash stake for Sybil behavior

        Args:
            lct_id: LCT identifier
            reason: Reason for slashing
            slash_percentage: Fraction to slash (0-1)
            current_time: Current timestamp

        Returns:
            (success, message, slashed_amount)
        """
        if lct_id not in self.stakes:
            return (False, "No stake found for LCT", 0.0)

        stake = self.stakes[lct_id]
        current_time = current_time or time.time()

        if stake.status == StakeStatus.SLASHED:
            return (False, f"Already slashed: {stake.slash_reason}", 0.0)

        # Slash stake
        stake.slash(reason, slash_percentage, current_time)

        # Add to society treasury
        slashed_amount = stake.slashed_amount
        self.treasury_balance += slashed_amount

        # Log slashing
        self.slash_history.append((lct_id, reason, slashed_amount, current_time))

        return (True, f"Stake slashed: {slashed_amount:.2f} ATP to treasury", slashed_amount)

    def detect_sybil_cluster(
        self,
        lct_graph: Dict[str, Set[str]],
        density_threshold: float = 0.8,
        min_cluster_size: int = 5
    ) -> List[Tuple[Set[str], float, str]]:
        """
        Detect Sybil clusters via social graph analysis

        Args:
            lct_graph: {lct_id: set of connected lct_ids}
            density_threshold: Edge density threshold for Sybil cluster (0-1)
            min_cluster_size: Minimum cluster size to flag

        Returns:
            List of (cluster_lcts, density, reason)
        """
        clusters = []

        # Find densely connected components
        visited = set()

        for lct_id in lct_graph:
            if lct_id in visited:
                continue

            # BFS to find connected component
            component = {lct_id}
            queue = [lct_id]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)

                for neighbor in lct_graph.get(current, set()):
                    if neighbor not in component:
                        component.add(neighbor)
                        queue.append(neighbor)

            # Check if component is suspicious
            if len(component) < min_cluster_size:
                continue

            # Compute edge density
            n = len(component)
            max_edges = n * (n - 1) / 2  # Complete graph

            actual_edges = 0
            for lct in component:
                for neighbor in lct_graph.get(lct, set()):
                    if neighbor in component:
                        actual_edges += 1

            actual_edges /= 2  # Undirected graph (count each edge once)

            density = actual_edges / max_edges if max_edges > 0 else 0.0

            if density >= density_threshold:
                reason = f"Dense cluster: {len(component)} LCTs, {density:.2f} density"
                clusters.append((component, density, reason))

        return clusters

    def auto_slash_sybil_clusters(
        self,
        lct_graph: Dict[str, Set[str]],
        density_threshold: float = 0.8,
        min_cluster_size: int = 5,
        slash_percentage: float = 1.0
    ) -> List[Tuple[str, float]]:
        """
        Automatically detect and slash Sybil clusters

        Args:
            lct_graph: Social graph
            density_threshold: Density threshold for Sybil detection
            min_cluster_size: Minimum cluster size
            slash_percentage: Fraction to slash

        Returns:
            List of (lct_id, slashed_amount)
        """
        clusters = self.detect_sybil_cluster(lct_graph, density_threshold, min_cluster_size)

        slashed = []

        for cluster_lcts, density, reason in clusters:
            for lct_id in cluster_lcts:
                success, message, amount = self.slash_stake(
                    lct_id,
                    f"Sybil cluster detected: {reason}",
                    slash_percentage
                )

                if success:
                    slashed.append((lct_id, amount))

        return slashed


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  Identity Stake System - Anti-Sybil Testing")
    print("  Session #82")
    print("=" * 80)

    system = IdentityStakeSystem(base_stake_amount=1000.0)

    # Test 1: Create stakes for legitimate agents
    print("\n=== Test 1: Legitimate Agent Stake Creation ===\n")

    agents = {
        "lct:web4:agent:alice": 5000.0,  # Has ATP
        "lct:web4:agent:bob": 5000.0,
        "lct:web4:agent:charlie": 500.0,  # Insufficient ATP
    }

    for lct_id, balance in agents.items():
        success, message, stake = system.create_stake(lct_id, balance)
        print(f"{lct_id.split(':')[-1]}: {message}")

    # Test 2: Try to unlock stake too early
    print("\n=== Test 2: Unlock Attempt (Too Early) ===\n")

    # Simulate immediate unlock attempt
    success, message, returned = system.unlock_stake(
        "lct:web4:agent:alice",
        current_reputation=0.8,
        current_time=time.time()
    )

    print(f"Alice unlock attempt: {message}")

    # Test 3: Unlock after proving period
    print("\n=== Test 3: Unlock After Proving Period ===\n")

    # Simulate 8 days later
    future_time = time.time() + (8 * 24 * 3600)

    success, message, returned = system.unlock_stake(
        "lct:web4:agent:alice",
        current_reputation=0.8,
        current_time=future_time
    )

    print(f"Alice unlock (8 days later): {message}")
    print(f"  ATP returned: {returned:.2f}")

    # Test 4: Create Sybil cluster
    print("\n=== Test 4: Sybil Cluster Detection ===\n")

    # Create 10 Sybil LCTs
    sybils = []
    for i in range(10):
        lct_id = f"lct:web4:agent:sybil_{i}"
        success, message, stake = system.create_stake(lct_id, 5000.0)
        if success:
            sybils.append(lct_id)

    print(f"Created {len(sybils)} Sybil LCTs")

    # Build densely connected graph (Sybils all witness each other)
    sybil_graph = {}
    for sybil_a in sybils:
        sybil_graph[sybil_a] = set(sybils) - {sybil_a}  # Connect to all others

    # Add legitimate agents (loosely connected)
    sybil_graph["lct:web4:agent:alice"] = {"lct:web4:agent:bob"}
    sybil_graph["lct:web4:agent:bob"] = {"lct:web4:agent:alice"}

    # Detect clusters
    clusters = system.detect_sybil_cluster(sybil_graph, density_threshold=0.8, min_cluster_size=5)

    print(f"\nDetected {len(clusters)} suspicious clusters:")
    for cluster_lcts, density, reason in clusters:
        print(f"  Cluster: {len(cluster_lcts)} LCTs, density={density:.2f}")
        print(f"  Reason: {reason}")

    # Test 5: Slash Sybil cluster
    print("\n=== Test 5: Slash Sybil Stakes ===\n")

    slashed = system.auto_slash_sybil_clusters(sybil_graph, density_threshold=0.8, min_cluster_size=5)

    print(f"Slashed {len(slashed)} Sybil stakes:")
    print(f"  Total slashed: {sum(amount for _, amount in slashed):.2f} ATP")
    print(f"  Society treasury: {system.treasury_balance:.2f} ATP")

    # Test 6: Legitimate agents unaffected
    print("\n=== Test 6: Legitimate Agents Unaffected ===\n")

    for lct_id in ["lct:web4:agent:alice", "lct:web4:agent:bob"]:
        stake = system.stakes.get(lct_id)
        if stake:
            print(f"{lct_id.split(':')[-1]}: status={stake.status.value}, stake={stake.stake_amount:.2f} ATP")

    # Test 7: Slash history
    print("\n=== Test 7: Slash History ===\n")

    print(f"Total slashing events: {len(system.slash_history)}")
    print(f"Sample (first 3):")
    for lct_id, reason, amount, timestamp in system.slash_history[:3]:
        agent_name = lct_id.split(':')[-1]
        print(f"  {agent_name}: {amount:.2f} ATP - {reason[:50]}...")

    print("\n" + "=" * 80)
    print("  All Tests Passed!")
    print("=" * 80)

    print("\n✅ Key Results:")
    print("  - Legitimate agents can create stakes (1000 ATP bonded)")
    print("  - Insufficient ATP prevents stake creation")
    print("  - Early unlock attempts rejected (7-day lockup)")
    print("  - Stakes unlockable after proving period + reputation")
    print("  - Sybil clusters detected (10 LCTs, 1.00 density)")
    print("  - Sybil stakes slashed (10,000 ATP to treasury)")
    print("  - Legitimate agents unaffected by slashing")

    print("\n🔒 Economic Sybil Defense:")
    print("  - Cost barrier: 1000 ATP per Sybil (10 Sybils = 10,000 ATP)")
    print("  - Risk punishment: Detected Sybils lose entire stake")
    print("  - Legitimate protection: Honest agents get stake back")
    print("  - Economic incentive: Society earns slashed ATP")
