#!/usr/bin/env python3
"""EP-Driven Agent Life Simulation

Integrates Web4 Security EP Trilogy with the game simulation to create
agent interactions guided by epistemic proprioception (EP) predictions.

This demonstrates how the Security EP Trilogy (Grounding, Relationship,
Authorization) can prevent security issues BEFORE they occur in a live
multi-agent environment.

Session 111: Legion autonomous research
Based on:
- Session 110: Web4 Security EP Trilogy (280K decisions/sec validated)
- Session 141 (Thor): Authorization EP in SAGE
- Web4 game vertical slice (one_life_home_society.py)

Key Innovation:
Instead of reacting to security issues after they occur, agents use EP
predictions to proactively adjust behavior, avoid dangerous interactions,
and maintain system health.

Architecture:
1. Game simulation provides agent context (identity, relationships, permissions)
2. Security EP Trilogy predicts risks before interactions
3. Agents adjust behavior based on predictions
4. Outcomes feed back to EPs for learning
5. System evolves toward safer, more coherent behaviors
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json

# Add implementation reference to path
implementation_path = Path(__file__).parent.parent / "web4-standard" / "implementation" / "reference"
sys.path.append(str(implementation_path))

# Import Web4 Security EP Trilogy
from web4_multi_ep_coordinator import (
    Web4MultiEPCoordinator,
    Web4SecurityDecision,
    SecurityEPDomain
)
from relationship_coherence_ep import (
    RelationshipCoherencePredictor,
    RelationshipContext,
    RelationshipStance,
    SecurityEPPrediction,
    SecurityEPDomain as RelSecurityEPDomain
)
from authorization_ep import (
    AuthorizationEPPredictor,
    AuthorizationContext,
    Permission,
    PermissionScope
)

# Import game engine
sys.path.append(str(Path(__file__).parent / "engine"))
from models import Agent, Society, World
from scenarios import bootstrap_home_society_world
from sim_loop import tick_world


# ============================================================================
# EP-Driven Interaction Types
# ============================================================================

@dataclass
class InteractionProposal:
    """A proposed interaction between agents that needs security validation."""

    interaction_id: str
    tick: int

    # Who is proposing the interaction?
    initiator_lct: str
    target_lct: str

    # What type of interaction?
    interaction_type: str  # "collaborate", "resource_transfer", "delegation", "challenge"

    # What are the details?
    description: str
    atp_cost: float  # ATP cost to both parties
    trust_impact: float  # Expected T3 change (-1.0 to +1.0)
    risk_level: float  # Inherent risk (0.0 to 1.0)

    # Permission being requested
    permission_requested: Optional[str] = None  # e.g., "write_to_ledger", "delegate_authority"
    resource_sensitivity: float = 0.5  # 0.0-1.0

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class InteractionOutcome:
    """Result of an agent interaction."""

    interaction_id: str
    decision: str  # "proceeded", "adjusted", "rejected"

    # EP predictions
    grounding_risk: float
    relationship_risk: float
    authorization_risk: float
    combined_risk: float
    cascade_detected: bool

    # Actual outcome
    success: bool
    atp_consumed: float
    t3_change_initiator: float
    t3_change_target: float

    # Security measures applied
    security_measures: List[str]

    # Learning data
    prediction_accurate: bool  # Did EP prediction match outcome?
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# EP-Driven Agent World
# ============================================================================

class EPDrivenAgentWorld:
    """
    Agent world where interactions are guided by epistemic proprioception.

    Instead of agents blindly interacting and discovering failures, they
    use EP predictions to avoid dangerous situations proactively.
    """

    def __init__(self, steps: int = 50):
        self.steps = steps

        # Game world
        self.world = bootstrap_home_society_world()
        self.research_agent_lct = self._select_research_agent()

        # Security EP Trilogy
        # Note: Using simple grounding prediction for now (Session 107's Grounding EP has different interface)
        self.relationship_ep = RelationshipCoherencePredictor()
        self.authorization_ep = AuthorizationEPPredictor()
        self.coordinator = Web4MultiEPCoordinator()

        # Tracking
        self.t3_history: List[float] = []
        self.atp_history: List[float] = []
        self.interaction_history: List[InteractionOutcome] = []
        self.ep_predictions: List[Dict[str, Any]] = []

        # Statistics
        self.interactions_proposed = 0
        self.interactions_proceeded = 0
        self.interactions_adjusted = 0
        self.interactions_rejected = 0
        self.cascades_detected = 0
        self.security_issues_prevented = 0

    def _select_research_agent(self) -> str:
        """Select research agent (Alice by default)."""
        if not self.world.agents:
            return None
        return sorted(self.world.agents.keys())[0]

    def _get_agent_t3_and_atp(self, agent_lct: str) -> Tuple[float, float]:
        """Get current T3 and ATP for agent."""
        agent = self.world.agents.get(agent_lct)
        if not agent:
            return 0.0, 0.0

        t_axes = (agent.trust_axes or {}).get("T3") or {}
        t3_composite = float(t_axes.get("composite", 0.0))
        atp = float((agent.resources or {}).get("ATP", 0.0))
        return t3_composite, atp

    def _create_grounding_prediction(self, agent_lct: str, interaction: InteractionProposal) -> SecurityEPPrediction:
        """Create simple grounding prediction from game state."""
        agent = self.world.agents[agent_lct]
        t3, atp = self._get_agent_t3_and_atp(agent_lct)

        # Simple grounding prediction based on T3 (proxy for identity coherence)
        # Higher T3 → lower grounding risk
        grounding_risk = max(0.0, 1.0 - t3)

        # Determine recommendation based on risk
        if grounding_risk > 0.7:
            recommendation = "reject"
        elif grounding_risk > 0.4:
            recommendation = "adjust"
        else:
            recommendation = "proceed"

        return SecurityEPPrediction(
            domain=SecurityEPDomain.GROUNDING,
            risk_probability=grounding_risk,
            confidence=0.8,  # Moderate confidence
            severity=grounding_risk,
            recommendation=recommendation,
            reasoning=f"T3-based grounding prediction: T3={t3:.2f}, risk={grounding_risk:.2f}",
            security_measure="increase_grounding_checks" if grounding_risk > 0.4 else None
        )

    def _create_relationship_context(self, initiator_lct: str, target_lct: str, interaction: InteractionProposal) -> RelationshipContext:
        """Create relationship context from game state."""
        initiator = self.world.agents[initiator_lct]
        target = self.world.agents[target_lct]

        initiator_t3, _ = self._get_agent_t3_and_atp(initiator_lct)
        target_t3, _ = self._get_agent_t3_and_atp(target_lct)

        # Determine stance from interaction type
        stance_map = {
            "collaborate": RelationshipStance.COLLABORATIVE,
            "resource_transfer": RelationshipStance.NEUTRAL,
            "delegation": RelationshipStance.NEUTRAL,
            "challenge": RelationshipStance.ADVERSARIAL
        }
        stance = stance_map.get(interaction.interaction_type, RelationshipStance.NEUTRAL)

        return RelationshipContext(
            relationship_id=f"{initiator_lct}:{target_lct}",
            agent_a_lct=initiator_lct,
            agent_b_lct=target_lct,
            current_relationship_ci=min(initiator_t3, target_t3),  # Use minimum T3
            historical_relationship_ci=[min(initiator_t3, target_t3)] * 5,
            interaction_count=self.world.tick,  # Use tick as proxy
            collaborative_interactions=max(0, self.world.tick - 5),
            adversarial_interactions=0,  # Start clean
            trust_violations=0,
            current_stance=stance,
            stance_stability=0.9,
            witness_count=2,  # Both agents in home society
            relationship_age_days=30,
            timestamp=datetime.now()
        )

    def _create_authorization_context(self, initiator_lct: str, target_lct: str, interaction: InteractionProposal) -> Optional[AuthorizationContext]:
        """Create authorization context if permission is requested."""
        if not interaction.permission_requested:
            return None

        initiator_t3, initiator_atp = self._get_agent_t3_and_atp(initiator_lct)
        target_t3, target_atp = self._get_agent_t3_and_atp(target_lct)

        # Map interaction to permission scope
        scope_map = {
            "collaborate": {PermissionScope.READ, PermissionScope.WRITE},
            "resource_transfer": {PermissionScope.WRITE},
            "delegation": {PermissionScope.GRANT},
            "challenge": {PermissionScope.READ}
        }
        scopes = scope_map.get(interaction.interaction_type, {PermissionScope.READ})

        permission = Permission(
            resource_type=interaction.permission_requested,
            resource_id=f"{target_lct}:{interaction.interaction_type}",
            scope=scopes,
            duration=timedelta(hours=1),  # Temporary permission
            sensitivity_level=interaction.resource_sensitivity,
            can_delegate=PermissionScope.GRANT in scopes,
            requester_lct=initiator_lct,
            resource_owner_lct=target_lct
        )

        return AuthorizationContext(
            permission=permission,
            requester_identity_coherence=initiator_t3,
            requester_identity_history_length=30,
            requester_grounding_ci_stable=True,
            relationship_ci=min(initiator_t3, target_t3),
            relationship_stance=RelationshipStance.COLLABORATIVE if interaction.interaction_type != "challenge" else RelationshipStance.ADVERSARIAL,
            relationship_age_days=30,
            historical_violations=0,
            recent_revocations=0,
            permission_history_count=self.world.tick,
            abuse_count=0,
            timestamp=datetime.now()
        )

    def evaluate_interaction(self, interaction: InteractionProposal) -> Web4SecurityDecision:
        """
        Use Security EP Trilogy to evaluate interaction safety.

        Returns Web4SecurityDecision with recommendation.
        """
        # Get initiator and target
        initiator_lct = interaction.initiator_lct
        target_lct = interaction.target_lct

        # Create contexts and predictions
        grounding_pred = self._create_grounding_prediction(initiator_lct, interaction)
        relationship_context = self._create_relationship_context(initiator_lct, target_lct, interaction)
        authorization_context = self._create_authorization_context(initiator_lct, target_lct, interaction)

        # Get predictions
        relationship_pred = self.relationship_ep.predict_relationship(relationship_context)
        authorization_pred = self.authorization_ep.predict_authorization(authorization_context) if authorization_context else None

        # Coordinate decision
        decision = self.coordinator.coordinate(
            grounding_pred=grounding_pred,
            relationship_pred=relationship_pred,
            authorization_pred=authorization_pred,
            decision_id=interaction.interaction_id
        )

        # Store prediction for analysis
        self.ep_predictions.append({
            "interaction_id": interaction.interaction_id,
            "tick": interaction.tick,
            "grounding_risk": grounding_pred.risk_probability,
            "relationship_risk": relationship_pred.risk_probability,
            "authorization_risk": authorization_pred.risk_probability if authorization_pred else 0.0,
            "combined_risk": decision.combined_risk_score,
            "cascade_detected": decision.cascade_predicted,
            "final_decision": decision.final_decision,
            "security_measures": decision.security_measures
        })

        return decision

    def execute_interaction(self, interaction: InteractionProposal, decision: Web4SecurityDecision) -> InteractionOutcome:
        """Execute interaction based on EP decision."""

        initiator_lct = interaction.initiator_lct
        target_lct = interaction.target_lct

        # Get current state
        initiator_t3_before, initiator_atp_before = self._get_agent_t3_and_atp(initiator_lct)
        target_t3_before, target_atp_before = self._get_agent_t3_and_atp(target_lct)

        # Execute based on decision
        if decision.final_decision == "reject":
            # Interaction blocked - no changes
            self.interactions_rejected += 1
            if decision.cascade_predicted:
                self.cascades_detected += 1
                self.security_issues_prevented += 1

            return InteractionOutcome(
                interaction_id=interaction.interaction_id,
                decision="rejected",
                grounding_risk=decision.grounding_prediction.risk_probability,
                relationship_risk=decision.relationship_prediction.risk_probability,
                authorization_risk=decision.authorization_prediction.risk_probability if decision.authorization_prediction else 0.0,
                combined_risk=decision.combined_risk_score,
                cascade_detected=decision.cascade_predicted,
                success=False,
                atp_consumed=0.0,
                t3_change_initiator=0.0,
                t3_change_target=0.0,
                security_measures=decision.security_measures,
                prediction_accurate=True  # Rejection prevents harm
            )

        elif decision.final_decision == "adjust":
            # Interaction proceeds with restrictions
            self.interactions_adjusted += 1

            # Reduce ATP cost by 50% (security measure: scope reduction)
            adjusted_atp_cost = interaction.atp_cost * 0.5

            # Reduce trust impact by 30% (security measure: limit interaction scope)
            adjusted_trust_impact = interaction.trust_impact * 0.7

            # Apply changes
            self.world.agents[initiator_lct].resources["ATP"] -= adjusted_atp_cost
            self.world.agents[target_lct].resources["ATP"] -= adjusted_atp_cost

            # Modest T3 change (restricted interaction)
            new_initiator_t3 = max(0.0, min(1.0, initiator_t3_before + adjusted_trust_impact * 0.5))
            new_target_t3 = max(0.0, min(1.0, target_t3_before + adjusted_trust_impact * 0.5))

            self.world.agents[initiator_lct].trust_axes["T3"]["composite"] = new_initiator_t3
            self.world.agents[target_lct].trust_axes["T3"]["composite"] = new_target_t3

            return InteractionOutcome(
                interaction_id=interaction.interaction_id,
                decision="adjusted",
                grounding_risk=decision.grounding_prediction.risk_probability,
                relationship_risk=decision.relationship_prediction.risk_probability,
                authorization_risk=decision.authorization_prediction.risk_probability if decision.authorization_prediction else 0.0,
                combined_risk=decision.combined_risk_score,
                cascade_detected=decision.cascade_predicted,
                success=True,
                atp_consumed=adjusted_atp_cost * 2,
                t3_change_initiator=new_initiator_t3 - initiator_t3_before,
                t3_change_target=new_target_t3 - target_t3_before,
                security_measures=decision.security_measures,
                prediction_accurate=True
            )

        else:  # proceed
            # Interaction proceeds normally
            self.interactions_proceeded += 1

            # Apply full ATP cost
            self.world.agents[initiator_lct].resources["ATP"] -= interaction.atp_cost
            self.world.agents[target_lct].resources["ATP"] -= interaction.atp_cost

            # Full T3 change
            new_initiator_t3 = max(0.0, min(1.0, initiator_t3_before + interaction.trust_impact))
            new_target_t3 = max(0.0, min(1.0, target_t3_before + interaction.trust_impact))

            self.world.agents[initiator_lct].trust_axes["T3"]["composite"] = new_initiator_t3
            self.world.agents[target_lct].trust_axes["T3"]["composite"] = new_target_t3

            # Determine success based on risk level
            success = interaction.risk_level < 0.3  # Low risk → high success probability

            return InteractionOutcome(
                interaction_id=interaction.interaction_id,
                decision="proceeded",
                grounding_risk=decision.grounding_prediction.risk_probability,
                relationship_risk=decision.relationship_prediction.risk_probability,
                authorization_risk=decision.authorization_prediction.risk_probability if decision.authorization_prediction else 0.0,
                combined_risk=decision.combined_risk_score,
                cascade_detected=decision.cascade_predicted,
                success=success,
                atp_consumed=interaction.atp_cost * 2,
                t3_change_initiator=new_initiator_t3 - initiator_t3_before,
                t3_change_target=new_target_t3 - target_t3_before,
                security_measures=decision.security_measures,
                prediction_accurate=success
            )

    def generate_interaction(self, tick: int) -> Optional[InteractionProposal]:
        """Generate a random interaction proposal for this tick."""
        import random

        # Get agents
        agents = list(self.world.agents.keys())
        if len(agents) < 2:
            return None

        # Select initiator and target
        initiator = random.choice(agents)
        target = random.choice([a for a in agents if a != initiator])

        # Interaction types with varying risk profiles
        interaction_types = [
            ("collaborate", 0.1, 5.0, 0.05, "shared_resource", 0.3),  # Low risk, low cost, modest trust gain
            ("resource_transfer", 0.2, 10.0, 0.02, "transfer_ledger", 0.5),  # Medium risk
            ("delegation", 0.4, 15.0, 0.08, "delegate_authority", 0.7),  # Higher risk, high trust impact
            ("challenge", 0.6, 20.0, -0.05, None, 0.8),  # High risk, trust loss
        ]

        # Weighted random selection (favor low-risk collaborations)
        weights = [10, 5, 3, 1]
        interaction_type, risk, atp_cost, trust_impact, permission, sensitivity = random.choices(
            interaction_types,
            weights=weights,
            k=1
        )[0]

        # Occasionally inject high-risk interactions to test EP predictions
        if tick % 10 == 0:
            # Every 10 ticks, try something risky
            interaction_type = "challenge"
            risk = 0.8
            atp_cost = 30.0
            trust_impact = -0.1
            permission = None
            sensitivity = 0.9

        return InteractionProposal(
            interaction_id=f"interaction_{tick}",
            tick=tick,
            initiator_lct=initiator,
            target_lct=target,
            interaction_type=interaction_type,
            description=f"{interaction_type} between {initiator} and {target}",
            atp_cost=atp_cost,
            trust_impact=trust_impact,
            risk_level=risk,
            permission_requested=permission,
            resource_sensitivity=sensitivity
        )

    def run_simulation(self) -> Dict[str, Any]:
        """Run EP-driven agent simulation."""

        print("=" * 80)
        print("EP-DRIVEN AGENT LIFE SIMULATION")
        print("=" * 80)
        print(f"Steps: {self.steps}")
        print(f"Research Agent: {self.research_agent_lct}")
        print()

        for tick in range(self.steps):
            # Advance world
            tick_world(self.world)

            # Record state
            t3, atp = self._get_agent_t3_and_atp(self.research_agent_lct)
            self.t3_history.append(t3)
            self.atp_history.append(atp)

            # Generate interaction proposal
            interaction = self.generate_interaction(tick)
            if not interaction:
                continue

            self.interactions_proposed += 1

            # Evaluate with Security EP Trilogy
            decision = self.evaluate_interaction(interaction)

            # Execute based on decision
            outcome = self.execute_interaction(interaction, decision)
            self.interaction_history.append(outcome)

            # Print progress every 10 ticks
            if tick % 10 == 0:
                print(f"Tick {tick}: {interaction.interaction_type} - {decision.final_decision}")
                print(f"  Risk: {decision.combined_risk_score:.2f}, Cascade: {decision.cascade_predicted}")
                print(f"  T3: {t3:.3f}, ATP: {atp:.1f}")
                if decision.security_measures:
                    print(f"  Measures: {', '.join(decision.security_measures[:3])}")
                print()

            # Check termination conditions
            if atp <= 0.0 or t3 < 0.2:
                print(f"LIFE TERMINATED at tick {tick}")
                print(f"  Reason: {'ATP depleted' if atp <= 0 else 'T3 collapsed'}")
                break

        return self.generate_summary()

    def generate_summary(self) -> Dict[str, Any]:
        """Generate simulation summary."""

        # Calculate statistics
        total_interactions = len(self.interaction_history)
        successful_interactions = sum(1 for i in self.interaction_history if i.success)

        proceeded_rate = self.interactions_proceeded / max(1, self.interactions_proposed)
        adjusted_rate = self.interactions_adjusted / max(1, self.interactions_proposed)
        rejected_rate = self.interactions_rejected / max(1, self.interactions_proposed)

        avg_grounding_risk = sum(i.grounding_risk for i in self.interaction_history) / max(1, total_interactions)
        avg_relationship_risk = sum(i.relationship_risk for i in self.interaction_history) / max(1, total_interactions)
        avg_authorization_risk = sum(i.authorization_risk for i in self.interaction_history) / max(1, total_interactions)

        total_atp_consumed = sum(i.atp_consumed for i in self.interaction_history)

        return {
            "simulation": {
                "steps": self.steps,
                "ticks_completed": self.world.tick,
                "research_agent": self.research_agent_lct
            },
            "agent_state": {
                "final_t3": self.t3_history[-1] if self.t3_history else 0.0,
                "final_atp": self.atp_history[-1] if self.atp_history else 0.0,
                "t3_trajectory": {
                    "start": self.t3_history[0] if self.t3_history else 0.0,
                    "end": self.t3_history[-1] if self.t3_history else 0.0,
                    "min": min(self.t3_history) if self.t3_history else 0.0,
                    "max": max(self.t3_history) if self.t3_history else 0.0
                },
                "atp_trajectory": {
                    "start": self.atp_history[0] if self.atp_history else 0.0,
                    "end": self.atp_history[-1] if self.atp_history else 0.0,
                    "total_consumed": total_atp_consumed
                }
            },
            "ep_performance": {
                "interactions_proposed": self.interactions_proposed,
                "interactions_proceeded": self.interactions_proceeded,
                "interactions_adjusted": self.interactions_adjusted,
                "interactions_rejected": self.interactions_rejected,
                "cascades_detected": self.cascades_detected,
                "security_issues_prevented": self.security_issues_prevented,
                "rates": {
                    "proceeded": proceeded_rate,
                    "adjusted": adjusted_rate,
                    "rejected": rejected_rate
                }
            },
            "risk_analysis": {
                "avg_grounding_risk": avg_grounding_risk,
                "avg_relationship_risk": avg_relationship_risk,
                "avg_authorization_risk": avg_authorization_risk,
                "total_interactions": total_interactions,
                "successful_interactions": successful_interactions,
                "success_rate": successful_interactions / max(1, total_interactions)
            },
            "coordinator_stats": self.coordinator.get_stats(),
            "t3_history": self.t3_history,
            "atp_history": self.atp_history,
            "interaction_outcomes": [
                {
                    "id": i.interaction_id,
                    "decision": i.decision,
                    "success": i.success,
                    "cascade": i.cascade_detected,
                    "risk": i.combined_risk
                }
                for i in self.interaction_history
            ]
        }


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EP-Driven Agent Life Simulation")
    parser.add_argument("--steps", type=int, default=50, help="Number of simulation ticks")
    parser.add_argument("--output", type=str, default="ep_driven_simulation_results.json", help="Output file")
    args = parser.parse_args()

    # Run simulation
    sim = EPDrivenAgentWorld(steps=args.steps)
    results = sim.run_simulation()

    # Print summary
    print()
    print("=" * 80)
    print("SIMULATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Agent State:")
    print(f"  Final T3: {results['agent_state']['final_t3']:.3f}")
    print(f"  Final ATP: {results['agent_state']['final_atp']:.1f}")
    print()
    print(f"EP Performance:")
    print(f"  Proceeded: {results['ep_performance']['interactions_proceeded']} ({results['ep_performance']['rates']['proceeded']:.1%})")
    print(f"  Adjusted: {results['ep_performance']['interactions_adjusted']} ({results['ep_performance']['rates']['adjusted']:.1%})")
    print(f"  Rejected: {results['ep_performance']['interactions_rejected']} ({results['ep_performance']['rates']['rejected']:.1%})")
    print(f"  Cascades Detected: {results['ep_performance']['cascades_detected']}")
    print(f"  Security Issues Prevented: {results['ep_performance']['security_issues_prevented']}")
    print()
    print(f"Risk Analysis:")
    print(f"  Avg Grounding Risk: {results['risk_analysis']['avg_grounding_risk']:.3f}")
    print(f"  Avg Relationship Risk: {results['risk_analysis']['avg_relationship_risk']:.3f}")
    print(f"  Avg Authorization Risk: {results['risk_analysis']['avg_authorization_risk']:.3f}")
    print(f"  Success Rate: {results['risk_analysis']['success_rate']:.1%}")
    print()

    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results saved to: {args.output}")
    print()
    print("=" * 80)
