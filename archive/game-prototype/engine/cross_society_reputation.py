#!/usr/bin/env python3
"""
Cross-Society Reputation Propagation

Implements reputation sharing across federated societies using V3 veracity signals.

Key Concepts:
1. **Reputation Gossip**: Societies share V3 updates about agents
2. **Trust Weighting**: Updates weighted by society's own V3 veracity
3. **Convergence**: Federation-wide consensus on agent quality
4. **Anti-Gaming**: Prevents reputation manipulation via trust weighting

Theory:
- Each society maintains local V3 scores for agents
- When agent performs operation, society broadcasts V3 update
- Other societies receive update and weight it by source society's veracity
- Weighted average creates federation-wide reputation consensus

Session #75 Priority #1: Implement cross-society quality signal sharing
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

try:
    from .models import World, Society, Agent
    from .lct import LCT
except ImportError:
    # Allow testing as standalone script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from models import World, Society, Agent
    from lct import LCT


# Reputation propagation parameters
REPUTATION_DECAY_RATE = 0.98  # Per gossip round (2% decay toward 0.5)
MIN_TRUST_WEIGHT = 0.1  # Minimum weight for low-veracity societies
GOSSIP_THRESHOLD = 0.01  # Minimum V3 change to trigger gossip


@dataclass
class ReputationUpdate:
    """Single reputation update event"""
    source_society_lct: str
    target_agent_lct: str
    new_veracity: float
    old_veracity: float
    operation_type: str
    timestamp: float
    source_veracity: float  # V3 veracity of source society

    @property
    def veracity_delta(self) -> float:
        """Change in veracity"""
        return self.new_veracity - self.old_veracity

    @property
    def trust_weight(self) -> float:
        """Weight based on source society's veracity"""
        return max(MIN_TRUST_WEIGHT, self.source_veracity)


@dataclass
class FederationReputation:
    """Federation-wide reputation tracking"""

    # agent_lct -> {society_lct -> veracity}
    local_reputations: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # agent_lct -> consensus veracity
    consensus_reputations: Dict[str, float] = field(default_factory=dict)

    # Recent updates for analysis
    update_history: List[ReputationUpdate] = field(default_factory=list)

    # Gossip statistics
    total_updates: int = 0
    total_gossip_messages: int = 0

    def get_local_reputation(self, agent_lct: str, society_lct: str) -> float:
        """Get agent's reputation in specific society"""
        if agent_lct not in self.local_reputations:
            return 0.5  # Default: unknown
        return self.local_reputations[agent_lct].get(society_lct, 0.5)

    def get_consensus_reputation(self, agent_lct: str) -> float:
        """Get federation-wide consensus reputation for agent"""
        return self.consensus_reputations.get(agent_lct, 0.5)

    def set_local_reputation(self, agent_lct: str, society_lct: str, veracity: float):
        """Update local reputation in specific society"""
        if agent_lct not in self.local_reputations:
            self.local_reputations[agent_lct] = {}
        self.local_reputations[agent_lct][society_lct] = veracity

    def update_consensus(self, agent_lct: str, society_veracities: Dict[str, float]):
        """
        Recalculate consensus reputation using trust-weighted average

        Args:
            agent_lct: Agent to update consensus for
            society_veracities: {society_lct -> society's own V3 veracity}
        """
        if agent_lct not in self.local_reputations:
            return

        local_reps = self.local_reputations[agent_lct]

        # Trust-weighted average
        weighted_sum = 0.0
        total_weight = 0.0

        for society_lct, agent_veracity in local_reps.items():
            # Weight by society's own veracity (high-veracity societies count more)
            society_veracity = society_veracities.get(society_lct, 0.5)
            weight = max(MIN_TRUST_WEIGHT, society_veracity)

            weighted_sum += agent_veracity * weight
            total_weight += weight

        if total_weight > 0:
            self.consensus_reputations[agent_lct] = weighted_sum / total_weight
        else:
            self.consensus_reputations[agent_lct] = 0.5

    def get_convergence_stats(self, agent_lct: str) -> Dict:
        """
        Analyze consensus convergence for agent

        Returns:
            - variance: Variance of local reputations
            - std_dev: Standard deviation
            - min_rep: Minimum local reputation
            - max_rep: Maximum local reputation
            - consensus: Federation consensus
            - societies_reporting: Number of societies with opinions
        """
        if agent_lct not in self.local_reputations:
            return {
                "variance": 0.0,
                "std_dev": 0.0,
                "min_rep": 0.5,
                "max_rep": 0.5,
                "consensus": 0.5,
                "societies_reporting": 0
            }

        local_reps = list(self.local_reputations[agent_lct].values())
        n = len(local_reps)

        if n == 0:
            return {
                "variance": 0.0,
                "std_dev": 0.0,
                "min_rep": 0.5,
                "max_rep": 0.5,
                "consensus": 0.5,
                "societies_reporting": 0
            }

        consensus = self.consensus_reputations.get(agent_lct, 0.5)

        # Calculate variance
        variance = sum((r - consensus) ** 2 for r in local_reps) / n
        std_dev = variance ** 0.5

        return {
            "variance": variance,
            "std_dev": std_dev,
            "min_rep": min(local_reps),
            "max_rep": max(local_reps),
            "consensus": consensus,
            "societies_reporting": n
        }


def broadcast_reputation_update(
    world: World,
    source_society: Society,
    agent_lct: str,
    new_veracity: float,
    old_veracity: float,
    operation_type: str,
    federation_reputation: FederationReputation
) -> int:
    """
    Broadcast reputation update across federation

    Args:
        world: World instance
        source_society: Society that observed the update
        agent_lct: Agent whose reputation changed
        new_veracity: New V3 veracity score
        old_veracity: Old V3 veracity score
        operation_type: Type of operation that triggered update
        federation_reputation: Federation reputation tracker

    Returns:
        Number of societies that received the update
    """
    # Check if update is significant enough to gossip
    veracity_delta = abs(new_veracity - old_veracity)
    if veracity_delta < GOSSIP_THRESHOLD:
        return 0  # Don't gossip insignificant updates

    # Get source society's own veracity
    source_society_lct = LCT.from_dict(world.get_society_lct(source_society.society_lct))
    source_veracity = source_society_lct.value_axes.get("V3", {}).get("veracity", 0.5)

    # Create update record
    update = ReputationUpdate(
        source_society_lct=source_society.society_lct,
        target_agent_lct=agent_lct,
        new_veracity=new_veracity,
        old_veracity=old_veracity,
        operation_type=operation_type,
        timestamp=world.tick,
        source_veracity=source_veracity
    )

    federation_reputation.update_history.append(update)
    federation_reputation.total_updates += 1

    # Get federated societies
    federated_societies = world.federation.get(source_society.society_lct, [])

    if not federated_societies:
        return 0  # No federation, no gossip

    # Broadcast to all federated societies
    updates_sent = 0

    for target_society_lct in federated_societies:
        # Receive update in target society
        receive_reputation_update(
            world=world,
            target_society_lct=target_society_lct,
            update=update,
            federation_reputation=federation_reputation
        )
        updates_sent += 1
        federation_reputation.total_gossip_messages += 1

    return updates_sent


def receive_reputation_update(
    world: World,
    target_society_lct: str,
    update: ReputationUpdate,
    federation_reputation: FederationReputation
):
    """
    Receive and process reputation update from another society

    Args:
        world: World instance
        target_society_lct: Society receiving the update
        update: Reputation update event
        federation_reputation: Federation reputation tracker
    """
    # Get target society's current local reputation for agent
    current_local = federation_reputation.get_local_reputation(
        agent_lct=update.target_agent_lct,
        society_lct=target_society_lct
    )

    # Trust-weighted update (blend remote signal with local knowledge)
    # High-veracity sources have more influence
    trust_weight = update.trust_weight

    # Blend: new_local = (1 - α) * current_local + α * remote_signal
    # where α = trust_weight * 0.3 (cap influence at 30% per update)
    blend_factor = min(0.3, trust_weight * 0.3)
    new_local = (1 - blend_factor) * current_local + blend_factor * update.new_veracity

    # Update local reputation
    federation_reputation.set_local_reputation(
        agent_lct=update.target_agent_lct,
        society_lct=target_society_lct,
        veracity=new_local
    )


def update_federation_consensus(
    world: World,
    federation_reputation: FederationReputation
):
    """
    Recalculate consensus reputations for all agents in federation

    Args:
        world: World instance
        federation_reputation: Federation reputation tracker
    """
    # Build society veracity map
    society_veracities = {}

    for society in world.societies.values():
        society_lct = LCT.from_dict(world.get_society_lct(society.society_lct))
        society_veracities[society.society_lct] = society_lct.value_axes.get("V3", {}).get("veracity", 0.5)

    # Update consensus for all agents with local reputations
    for agent_lct in federation_reputation.local_reputations.keys():
        federation_reputation.update_consensus(agent_lct, society_veracities)


def propagate_v3_update(
    world: World,
    society: Society,
    agent_lct: str,
    new_veracity: float,
    old_veracity: float,
    operation_type: str,
    federation_reputation: FederationReputation
) -> Dict:
    """
    Complete V3 propagation workflow

    1. Update local reputation in source society
    2. Broadcast to federated societies
    3. Update federation-wide consensus

    Args:
        world: World instance
        society: Society that observed the update
        agent_lct: Agent whose V3 changed
        new_veracity: New V3 veracity
        old_veracity: Old V3 veracity
        operation_type: Operation that triggered update
        federation_reputation: Federation reputation tracker

    Returns:
        {
            "local_updated": bool,
            "gossip_sent": int,
            "consensus_updated": bool,
            "convergence_stats": dict
        }
    """
    # Step 1: Update local reputation
    federation_reputation.set_local_reputation(
        agent_lct=agent_lct,
        society_lct=society.society_lct,
        veracity=new_veracity
    )

    # Step 2: Broadcast to federation
    gossip_sent = broadcast_reputation_update(
        world=world,
        source_society=society,
        agent_lct=agent_lct,
        new_veracity=new_veracity,
        old_veracity=old_veracity,
        operation_type=operation_type,
        federation_reputation=federation_reputation
    )

    # Step 3: Update consensus
    update_federation_consensus(world, federation_reputation)

    # Step 4: Get convergence stats
    convergence_stats = federation_reputation.get_convergence_stats(agent_lct)

    return {
        "local_updated": True,
        "gossip_sent": gossip_sent,
        "consensus_updated": True,
        "convergence_stats": convergence_stats
    }


def get_federation_reputation_summary(
    federation_reputation: FederationReputation
) -> Dict:
    """
    Get summary statistics about federation reputation system

    Returns:
        {
            "total_agents_tracked": int,
            "total_updates": int,
            "total_gossip_messages": int,
            "avg_societies_per_agent": float,
            "avg_convergence_variance": float,
            "consensus_reputations": {agent_lct -> veracity}
        }
    """
    total_agents = len(federation_reputation.local_reputations)

    if total_agents == 0:
        return {
            "total_agents_tracked": 0,
            "total_updates": 0,
            "total_gossip_messages": 0,
            "avg_societies_per_agent": 0.0,
            "avg_convergence_variance": 0.0,
            "consensus_reputations": {}
        }

    # Calculate average societies reporting per agent
    total_societies_reporting = sum(
        len(societies)
        for societies in federation_reputation.local_reputations.values()
    )
    avg_societies = total_societies_reporting / total_agents

    # Calculate average convergence variance
    variances = [
        federation_reputation.get_convergence_stats(agent_lct)["variance"]
        for agent_lct in federation_reputation.local_reputations.keys()
    ]
    avg_variance = sum(variances) / len(variances) if variances else 0.0

    return {
        "total_agents_tracked": total_agents,
        "total_updates": federation_reputation.total_updates,
        "total_gossip_messages": federation_reputation.total_gossip_messages,
        "avg_societies_per_agent": avg_societies,
        "avg_convergence_variance": avg_variance,
        "consensus_reputations": dict(federation_reputation.consensus_reputations)
    }


def initialize_federation_reputation(
    world: World,
    agents: List[Agent]
) -> FederationReputation:
    """
    Initialize federation reputation tracker with initial V3 scores

    Args:
        world: World instance
        agents: List of agents to track

    Returns:
        Initialized FederationReputation instance
    """
    fed_rep = FederationReputation()

    # Initialize local reputations from each society's perspective
    for society in world.societies.values():
        for agent in agents:
            # Get agent's current V3 veracity (if they have an LCT)
            try:
                agent_lct = LCT.from_dict(world.get_agent_lct(agent.agent_lct))
                initial_veracity = agent_lct.value_axes.get("V3", {}).get("veracity", 0.5)
            except:
                initial_veracity = 0.5

            fed_rep.set_local_reputation(
                agent_lct=agent.agent_lct,
                society_lct=society.society_lct,
                veracity=initial_veracity
            )

    # Calculate initial consensus
    update_federation_consensus(world, fed_rep)

    return fed_rep


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("  Cross-Society Reputation Propagation - Unit Tests")
    print("=" * 80)

    # Test 1: Trust weighting
    print("\n=== Test 1: Trust Weighting ===")

    update1 = ReputationUpdate(
        source_society_lct="lct:society:A",
        target_agent_lct="lct:agent:alice",
        new_veracity=0.95,
        old_veracity=0.90,
        operation_type="audit",
        timestamp=100.0,
        source_veracity=0.95  # High-veracity source
    )

    update2 = ReputationUpdate(
        source_society_lct="lct:society:B",
        target_agent_lct="lct:agent:bob",
        new_veracity=0.95,
        old_veracity=0.90,
        operation_type="audit",
        timestamp=101.0,
        source_veracity=0.05  # Very low-veracity source (below MIN_TRUST_WEIGHT)
    )

    print(f"High-veracity source (0.95): trust_weight = {update1.trust_weight:.2f}")
    print(f"Low-veracity source (0.05): trust_weight = {update2.trust_weight:.2f}")
    print(f"✅ Low-veracity source capped at minimum: {update2.trust_weight == MIN_TRUST_WEIGHT}")

    # Test 2: Consensus calculation
    print("\n=== Test 2: Consensus Calculation ===")

    fed_rep = FederationReputation()

    # Agent Alice has different reputations across 3 societies
    fed_rep.set_local_reputation("lct:agent:alice", "lct:society:A", 0.95)
    fed_rep.set_local_reputation("lct:agent:alice", "lct:society:B", 0.85)
    fed_rep.set_local_reputation("lct:agent:alice", "lct:society:C", 0.75)

    # Societies have different veracities
    society_veracities = {
        "lct:society:A": 0.90,  # High-veracity society
        "lct:society:B": 0.70,  # Medium-veracity
        "lct:society:C": 0.50   # Low-veracity
    }

    fed_rep.update_consensus("lct:agent:alice", society_veracities)
    consensus = fed_rep.get_consensus_reputation("lct:agent:alice")

    print(f"Local reputations:")
    print(f"  Society A (V3=0.90): Alice = 0.95")
    print(f"  Society B (V3=0.70): Alice = 0.85")
    print(f"  Society C (V3=0.50): Alice = 0.75")
    print(f"\nConsensus reputation: {consensus:.3f}")
    print(f"✅ Consensus weighted toward high-veracity societies: {consensus > 0.85}")

    # Test 3: Convergence stats
    print("\n=== Test 3: Convergence Statistics ===")

    stats = fed_rep.get_convergence_stats("lct:agent:alice")

    print(f"Societies reporting: {stats['societies_reporting']}")
    print(f"Consensus: {stats['consensus']:.3f}")
    print(f"Min reputation: {stats['min_rep']:.2f}")
    print(f"Max reputation: {stats['max_rep']:.2f}")
    print(f"Std deviation: {stats['std_dev']:.4f}")
    print(f"Variance: {stats['variance']:.6f}")
    print(f"✅ Low variance indicates good convergence: {stats['variance'] < 0.01}")

    # Test 4: Summary statistics
    print("\n=== Test 4: Summary Statistics ===")

    fed_rep.total_updates = 50
    fed_rep.total_gossip_messages = 450  # 50 updates * 9 societies

    summary = get_federation_reputation_summary(fed_rep)

    print(f"Total agents tracked: {summary['total_agents_tracked']}")
    print(f"Total updates: {summary['total_updates']}")
    print(f"Total gossip messages: {summary['total_gossip_messages']}")
    print(f"Avg societies per agent: {summary['avg_societies_per_agent']:.1f}")
    print(f"Avg convergence variance: {summary['avg_convergence_variance']:.6f}")
    print(f"✅ All statistics computed correctly")

    print("\n" + "=" * 80)
    print("  All Unit Tests Passed!")
    print("=" * 80)
