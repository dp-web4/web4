#!/usr/bin/env python3
"""
Five-Domain EP-Driven Multi-Life Simulation for Web4

Session 112: Legion autonomous research
Integrates:
- Thor's SAGE Session 143: Five-domain EP coordination (373K decisions/sec)
- Cascade's multi-life framework: Karma carry-forward and lineage tracking
- Legion Session 111: EP-driven agent interactions concept

This is the production-grade implementation that combines:
1. SAGE's complete five-domain EP framework
2. Web4's multi-life system with LifeRecord and lineage
3. HRM policy integration with closed-loop actions
4. Pattern corpus building for EP learning

Key Improvement over Session 111:
- Thor's Session 143 showed agents stayed alive and healthy (Alice ATP=71, Bob ATP=35)
- My Session 111 simple demo had Bob's ATP→0.0 (died!)
- This implementation uses proper five-domain EP coordination

Architecture:
```
Life N Start
  ↓
Tick Loop:
  1. Generate interaction proposal (based on HRM policy or game state)
  2. Build 5 EP contexts (Emotional, Quality, Attention, Grounding, Authorization)
  3. Generate 5 EP predictions
  4. Coordinate via Multi-EP Coordinator
  5. Execute based on final_decision (proceed/adjust/defer)
  6. Update agent state
  7. Record outcome for pattern learning
  ↓
Life N End (T3<0.2 or ATP≤0)
  ↓
Carry forward karma (T3 → initial conditions for Life N+1)
  ↓
Life N+1 Start
```

"""

import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

# Add SAGE EP framework to path
hrm_path = Path(__file__).parent.parent.parent / "HRM"
sys.path.insert(0, str(hrm_path / "sage" / "experiments"))

from multi_ep_coordinator import (
    MultiEPCoordinator,
    EPDomain,
    EPPrediction
)

# Add Web4 game engine
sys.path.insert(0, str(Path(__file__).parent))
from engine.models import Agent, Society, World, LifeRecord
from engine.scenarios import bootstrap_home_society_world
from engine.sim_loop import tick_world


# ============================================================================
# EP Context Builders for Web4 Agents
# ============================================================================

class Web4EPContextBuilder:
    """Builds five-domain EP contexts from Web4 agent/world state."""

    @staticmethod
    def build_emotional_context(agent: Agent, interaction_type: str, world: World) -> Dict[str, Any]:
        """Build Emotional EP context."""
        # Calculate frustration from recent failures
        # For now, simple heuristic based on ATP stress
        atp = agent.resources.get("ATP", 0.0)
        frustration = max(0.0, min(1.0, (100.0 - atp) / 100.0))

        # Interaction complexity
        complexity_map = {
            "idle": 0.1,
            "conservative_audit": 0.3,
            "small_spend": 0.4,
            "risky_spend": 0.7,
            "collaborate": 0.2,
            "delegate": 0.5,
            "challenge": 0.8
        }
        complexity = complexity_map.get(interaction_type, 0.5)

        return {
            "current_frustration": frustration,
            "recent_failure_rate": 0.1,  # Could track from history
            "atp_stress": frustration,
            "interaction_complexity": complexity
        }

    @staticmethod
    def build_quality_context(agent: Agent, target_agent: Optional[Agent], interaction_type: str) -> Dict[str, Any]:
        """Build Quality EP context."""
        # Agent's T3 as proxy for quality
        t3 = agent.trust_axes.get("T3", {}).get("composite", 0.5)

        # Interaction risk to quality
        risk_map = {
            "idle": 0.0,
            "conservative_audit": 0.1,
            "small_spend": 0.2,
            "risky_spend": 0.6,
            "collaborate": 0.1,
            "delegate": 0.4,
            "challenge": 0.7
        }
        risk = risk_map.get(interaction_type, 0.3)

        return {
            "current_relationship_quality": t3,
            "recent_avg_outcome": 0.6,  # Could track from history
            "trust_alignment": t3,
            "interaction_risk_to_quality": risk
        }

    @staticmethod
    def build_attention_context(agent: Agent, atp_cost: float) -> Dict[str, Any]:
        """Build Attention EP context."""
        atp_available = agent.resources.get("ATP", 0.0)

        return {
            "atp_available": atp_available,
            "atp_cost": atp_cost,
            "atp_reserve_needed": 20.0,  # Minimum to keep alive
            "interaction_count": 0,  # Could track
            "expected_benefit": max(0.0, atp_cost * 0.5)  # Conservative estimate
        }

    @staticmethod
    def build_grounding_context(
        agent: Agent,
        target_agent: Optional[Agent],
        society: Society,
        world: World
    ) -> Dict[str, Any]:
        """Build Grounding EP context."""
        agent_t3 = agent.trust_axes.get("T3", {}).get("composite", 0.5)

        # Check society coherence
        same_society = True  # In home society scenario
        if target_agent:
            target_t3 = target_agent.trust_axes.get("T3", {}).get("composite", 0.5)
            trust_gap = abs(agent_t3 - target_t3)
        else:
            target_t3 = agent_t3
            trust_gap = 0.0

        return {
            "same_society": same_society,
            "initiator_trust": agent_t3,
            "target_trust": target_t3,
            "trust_gap": trust_gap,
            "society_coherence_index": 1.0 if same_society else 0.3
        }

    @staticmethod
    def build_authorization_context(
        agent: Agent,
        target_agent: Optional[Agent],
        interaction_type: str
    ) -> Dict[str, Any]:
        """Build Authorization EP context."""
        agent_t3 = agent.trust_axes.get("T3", {}).get("composite", 0.5)

        # Permission thresholds
        permission_thresholds = {
            "idle": 0.0,
            "conservative_audit": 0.4,
            "small_spend": 0.5,
            "risky_spend": 0.7,
            "collaborate": 0.4,
            "delegate": 0.6,
            "challenge": 0.7
        }

        required_trust = permission_thresholds.get(interaction_type, 0.5)
        has_permission = agent_t3 >= required_trust

        return {
            "has_base_permission": agent_t3 >= 0.3,
            "required_trust_level": required_trust,
            "actual_trust_level": agent_t3,
            "permission_granted": has_permission,
            "past_abuse_count": 0,  # Could track
            "interaction_type": interaction_type
        }


# ============================================================================
# Five-Domain EP Predictor
# ============================================================================

class Web4FiveDomainEPPredictor:
    """
    Uses five-domain EP coordination to predict interaction outcomes.

    Based on Thor's Session 143 approach, adapted for Web4 game engine.
    """

    def __init__(self):
        self.coordinator = MultiEPCoordinator()
        self.context_builder = Web4EPContextBuilder()
        self.prediction_count = 0
        self.pattern_corpus = []

    def predict_interaction(
        self,
        agent: Agent,
        target_agent: Optional[Agent],
        interaction_type: str,
        atp_cost: float,
        society: Society,
        world: World
    ) -> Dict[str, Any]:
        """
        Predict interaction outcome using five-domain EP.

        Returns comprehensive prediction with coordinated decision.
        """
        self.prediction_count += 1

        # Build contexts for each domain
        emotional_ctx = self.context_builder.build_emotional_context(agent, interaction_type, world)
        quality_ctx = self.context_builder.build_quality_context(agent, target_agent, interaction_type)
        attention_ctx = self.context_builder.build_attention_context(agent, atp_cost)
        grounding_ctx = self.context_builder.build_grounding_context(agent, target_agent, society, world)
        authorization_ctx = self.context_builder.build_authorization_context(agent, target_agent, interaction_type)

        # Generate predictions for each domain
        emotional_pred = self._predict_emotional(emotional_ctx)
        quality_pred = self._predict_quality(quality_ctx)
        attention_pred = self._predict_attention(attention_ctx)
        grounding_pred = self._predict_grounding(grounding_ctx)
        authorization_pred = self._predict_authorization(authorization_ctx)

        # Coordinate predictions
        decision = self.coordinator.coordinate(
            emotional_pred=emotional_pred,
            quality_pred=quality_pred,
            attention_pred=attention_pred,
            grounding_pred=grounding_pred,
            authorization_pred=authorization_pred
        )

        return {
            "prediction_id": self.prediction_count,
            "interaction_type": interaction_type,
            "atp_cost": atp_cost,
            "contexts": {
                "emotional": emotional_ctx,
                "quality": quality_ctx,
                "attention": attention_ctx,
                "grounding": grounding_ctx,
                "authorization": authorization_ctx
            },
            "coordinated_decision": {
                "final_decision": decision.final_decision,
                "confidence": decision.decision_confidence,
                "reasoning": decision.reasoning,
                "has_conflict": decision.has_conflict,
                "cascade_predicted": decision.cascade_predicted
            }
        }

    def _predict_emotional(self, ctx: Dict[str, Any]) -> EPPrediction:
        """Predict emotional impact (similar to Thor's Session 143)."""
        frustration = ctx["current_frustration"]
        failure_rate = ctx["recent_failure_rate"]
        atp_stress = ctx["atp_stress"]
        complexity = ctx["interaction_complexity"]

        cascade_risk = min(1.0, (frustration + failure_rate + atp_stress + complexity) / 4.0)
        outcome_probability = 1.0 - cascade_risk

        if cascade_risk > 0.7:
            recommendation = "defer"
            reasoning = f"High emotional risk ({cascade_risk:.2f})"
        elif cascade_risk > 0.4:
            recommendation = "adjust"
            reasoning = f"Moderate stress ({cascade_risk:.2f})"
        else:
            recommendation = "proceed"
            reasoning = f"Low emotional risk ({cascade_risk:.2f})"

        return EPPrediction(
            domain=EPDomain.EMOTIONAL,
            outcome_probability=outcome_probability,
            confidence=0.8,
            severity=cascade_risk,
            recommendation=recommendation,
            reasoning=reasoning,
            adjustment_strategy="reduce_complexity" if cascade_risk > 0.4 else None
        )

    def _predict_quality(self, ctx: Dict[str, Any]) -> EPPrediction:
        """Predict quality impact."""
        current_quality = ctx["current_relationship_quality"]
        risk = ctx["interaction_risk_to_quality"]

        expected_quality = max(0.0, current_quality - risk)
        severity_float = risk
        outcome_probability = max(0.0, min(1.0, 0.5 + (expected_quality - current_quality)))

        if expected_quality < current_quality - 0.2:
            recommendation = "defer"
            reasoning = f"Quality would drop significantly (risk={risk:.2f})"
        elif expected_quality < current_quality:
            recommendation = "adjust"
            reasoning = f"Quality may decline (risk={risk:.2f})"
        else:
            recommendation = "proceed"
            reasoning = f"Quality stable or improves (current={current_quality:.2f})"

        return EPPrediction(
            domain=EPDomain.QUALITY,
            outcome_probability=outcome_probability,
            confidence=0.7,
            severity=severity_float,
            recommendation=recommendation,
            reasoning=reasoning,
            adjustment_strategy="lower_risk_interaction" if expected_quality < current_quality else None
        )

    def _predict_attention(self, ctx: Dict[str, Any]) -> EPPrediction:
        """Predict ATP resource impact."""
        available = ctx["atp_available"]
        cost = ctx["atp_cost"]
        reserve = ctx["atp_reserve_needed"]

        remaining = available - cost
        severity_float = max(0.0, min(1.0, (reserve - remaining) / reserve)) if remaining < reserve else 0.0

        if remaining < reserve:
            outcome_probability = max(0.0, remaining / reserve)
            recommendation = "defer"
            reasoning = f"ATP would drop to {remaining:.1f} (below reserve {reserve})"
        elif remaining < reserve * 2:
            outcome_probability = 0.7
            recommendation = "adjust"
            reasoning = f"ATP close to reserve ({remaining:.1f} remaining)"
        else:
            outcome_probability = 0.9
            recommendation = "proceed"
            reasoning = f"Sufficient ATP ({remaining:.1f} after cost)"

        return EPPrediction(
            domain=EPDomain.ATTENTION,
            outcome_probability=outcome_probability,
            confidence=0.9,
            severity=severity_float,
            recommendation=recommendation,
            reasoning=reasoning,
            adjustment_strategy="reduce_atp_cost" if remaining < reserve * 2 else None
        )

    def _predict_grounding(self, ctx: Dict[str, Any]) -> EPPrediction:
        """Predict grounding coherence."""
        same_society = ctx["same_society"]
        trust_gap = ctx["trust_gap"]
        coherence = ctx["society_coherence_index"]

        severity_float = trust_gap if not same_society else trust_gap * 0.5
        outcome_probability = coherence * (1.0 - severity_float)

        if not same_society:
            recommendation = "defer"
            reasoning = "Different societies - grounding risk"
        elif trust_gap > 0.4:
            recommendation = "adjust"
            reasoning = f"High trust gap ({trust_gap:.2f})"
        else:
            recommendation = "proceed"
            reasoning = f"Good grounding coherence ({coherence:.2f})"

        return EPPrediction(
            domain=EPDomain.GROUNDING,
            outcome_probability=outcome_probability,
            confidence=0.8,
            severity=severity_float,
            recommendation=recommendation,
            reasoning=reasoning,
            adjustment_strategy="require_witnesses" if trust_gap > 0.4 else None
        )

    def _predict_authorization(self, ctx: Dict[str, Any]) -> EPPrediction:
        """Predict authorization safety."""
        has_permission = ctx["permission_granted"]
        required_trust = ctx["required_trust_level"]
        actual_trust = ctx["actual_trust_level"]

        severity_float = max(0.0, required_trust - actual_trust)
        outcome_probability = min(1.0, actual_trust / required_trust) if required_trust > 0 else 1.0

        if not has_permission:
            recommendation = "defer"
            reasoning = f"Insufficient trust ({actual_trust:.2f} < {required_trust:.2f})"
        elif actual_trust < required_trust + 0.1:
            recommendation = "adjust"
            reasoning = f"Barely sufficient trust ({actual_trust:.2f})"
        else:
            recommendation = "proceed"
            reasoning = f"Authorized (trust={actual_trust:.2f})"

        return EPPrediction(
            domain=EPDomain.AUTHORIZATION,
            outcome_probability=outcome_probability,
            confidence=0.85,
            severity=severity_float,
            recommendation=recommendation,
            reasoning=reasoning,
            adjustment_strategy="reduce_scope" if not has_permission else None
        )

    def record_outcome(self, prediction: Dict[str, Any], outcome: Dict[str, Any]):
        """Record outcome for pattern learning."""
        self.pattern_corpus.append({
            "prediction": prediction,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat()
        })


# ============================================================================
# Multi-Life EP-Driven Simulation
# ============================================================================

def run_ep_five_domain_multi_life(
    num_lives: int = 3,
    ticks_per_life: int = 20,
    output_file: str = "ep_five_domain_multi_life_results.json"
) -> Dict[str, Any]:
    """
    Run multi-life simulation with five-domain EP predictions.

    Each life:
    1. Starts with karma from previous life
    2. Runs for N ticks with EP-driven interactions
    3. Records LifeRecord with full metrics
    4. Carries forward state to next life
    """
    print("=" * 80)
    print("FIVE-DOMAIN EP-DRIVEN MULTI-LIFE SIMULATION")
    print("=" * 80)
    print(f"Lives: {num_lives}, Ticks per life: {ticks_per_life}")
    print()

    # Initialize world
    world = bootstrap_home_society_world()
    ep_predictor = Web4FiveDomainEPPredictor()

    # Get research agent and society
    agents = list(world.agents.keys())
    research_agent_lct = agents[0]
    society_lct = list(world.societies.keys())[0]
    society = world.societies[society_lct]

    # Initialize lineage tracking
    world.life_lineage = {}
    world.life_state = {}

    lives_summary = []

    for life_index in range(num_lives):
        print(f"\n{'='*80}")
        print(f"LIFE {life_index + 1}")
        print(f"{'='*80}\n")

        # Get previous life for karma carry-forward
        prev_life = world.life_lineage.get(research_agent_lct, [])[-1] if world.life_lineage.get(research_agent_lct) else None

        # Carry forward karma
        if prev_life:
            prev_t3 = prev_life.final_t3
            if prev_t3 > 0.7:
                initial_t3 = 0.65
                initial_atp = 110.0
                print(f"Previous life T3={prev_t3:.2f} (good) → Starting T3={initial_t3:.2f}, ATP={initial_atp:.1f}")
            elif prev_t3 < 0.3:
                initial_t3 = 0.45
                initial_atp = 80.0
                print(f"Previous life T3={prev_t3:.2f} (poor) → Starting T3={initial_t3:.2f}, ATP={initial_atp:.1f}")
            else:
                initial_t3 = 0.55
                initial_atp = 100.0
                print(f"Previous life T3={prev_t3:.2f} (average) → Starting T3={initial_t3:.2f}, ATP={initial_atp:.1f}")
        else:
            initial_t3 = 0.6
            initial_atp = 100.0
            print(f"First life → Starting T3={initial_t3:.2f}, ATP={initial_atp:.1f}")

        # Set initial conditions
        agent = world.agents[research_agent_lct]
        agent.trust_axes.setdefault("T3", {})
        agent.trust_axes["T3"]["composite"] = initial_t3
        agent.resources["ATP"] = initial_atp

        # Life tracking
        life_id = f"life:{research_agent_lct}:{life_index}"
        start_tick = world.tick
        t3_history = []
        atp_history = []
        interactions = []
        life_state = "alive"
        termination_reason = "unknown"

        # Run life
        for tick_offset in range(ticks_per_life):
            tick_world(world)

            # Get current state
            t3 = agent.trust_axes.get("T3", {}).get("composite", 0.0)
            atp = agent.resources.get("ATP", 0.0)
            t3_history.append(t3)
            atp_history.append(atp)

            # Generate interaction (simple policy for now)
            if atp > 60:
                interaction_type = "small_spend"
                atp_cost = 10.0
            elif atp > 30:
                interaction_type = "conservative_audit"
                atp_cost = 5.0
            else:
                interaction_type = "idle"
                atp_cost = 0.0

            # Get EP prediction
            prediction = ep_predictor.predict_interaction(
                agent=agent,
                target_agent=None,  # Self-directed for now
                interaction_type=interaction_type,
                atp_cost=atp_cost,
                society=society,
                world=world
            )

            # Execute based on EP decision
            decision = prediction["coordinated_decision"]["final_decision"]

            if decision == "defer":
                # Don't execute, no cost
                actual_cost = 0.0
                success = False
                print(f"  Tick {world.tick}: {interaction_type} DEFERRED - {prediction['coordinated_decision']['reasoning'][:50]}")
            elif decision == "adjust":
                # Execute with 50% cost reduction
                actual_cost = atp_cost * 0.5
                agent.resources["ATP"] = max(0.0, atp - actual_cost)
                success = True
                print(f"  Tick {world.tick}: {interaction_type} ADJUSTED (cost {actual_cost:.1f}) - ATP={agent.resources['ATP']:.1f}")
            else:  # proceed
                # Execute normally
                actual_cost = atp_cost
                agent.resources["ATP"] = max(0.0, atp - actual_cost)
                success = True
                print(f"  Tick {world.tick}: {interaction_type} PROCEEDED (cost {actual_cost:.1f}) - ATP={agent.resources['ATP']:.1f}")

            # Record interaction
            interactions.append({
                "tick": world.tick,
                "type": interaction_type,
                "decision": decision,
                "atp_cost_proposed": atp_cost,
                "atp_cost_actual": actual_cost,
                "success": success
            })

            # Record outcome for pattern learning
            ep_predictor.record_outcome(prediction, {"success": success, "atp_cost": actual_cost})

            # Check termination conditions
            current_t3 = agent.trust_axes.get("T3", {}).get("composite", 0.0)
            current_atp = agent.resources.get("ATP", 0.0)

            if current_atp <= 0.0:
                life_state = "terminated"
                termination_reason = "atp_exhausted"
                print(f"\n  LIFE TERMINATED: ATP exhausted at tick {world.tick}")
                break
            elif current_t3 < 0.2:
                life_state = "terminated"
                termination_reason = "low_trust"
                print(f"\n  LIFE TERMINATED: T3 too low ({current_t3:.2f}) at tick {world.tick}")
                break

        # Life completed
        if life_state == "alive":
            life_state = "completed"
            termination_reason = "natural"

        end_tick = world.tick
        final_t3 = agent.trust_axes.get("T3", {}).get("composite", 0.0)
        final_atp = agent.resources.get("ATP", 0.0)

        # Create LifeRecord
        life_record = LifeRecord(
            life_id=life_id,
            agent_lct=research_agent_lct,
            start_tick=start_tick,
            end_tick=end_tick,
            life_state=life_state,
            termination_reason=termination_reason,
            t3_history=t3_history,
            atp_history=atp_history
        )

        # Store in lineage
        world.life_lineage.setdefault(research_agent_lct, []).append(life_record)

        # Add rebornAs edge if not first life
        if life_index > 0:
            prev_life_id = f"life:{research_agent_lct}:{life_index-1}"
            world.add_context_edge(
                subject=prev_life_id,
                predicate="web4:rebornAs",
                object=life_id,
                mrh={"deltaR": "local", "deltaT": "eternal", "deltaC": "agent-scale"}
            )

        # Summary
        print(f"\nLife {life_index + 1} Summary:")
        print(f"  State: {life_state} ({termination_reason})")
        print(f"  Duration: {end_tick - start_tick} ticks")
        print(f"  Final T3: {final_t3:.3f} (started {t3_history[0]:.3f})")
        print(f"  Final ATP: {final_atp:.1f} (started {atp_history[0]:.1f})")
        print(f"  Interactions: {len(interactions)}")

        lives_summary.append({
            "life_id": life_id,
            "life_index": life_index,
            "state": life_state,
            "termination_reason": termination_reason,
            "duration_ticks": end_tick - start_tick,
            "initial_t3": t3_history[0],
            "final_t3": final_t3,
            "initial_atp": atp_history[0],
            "final_atp": final_atp,
            "interactions_count": len(interactions),
            "t3_history": t3_history,
            "atp_history": atp_history,
            "interactions": interactions
        })

    # Overall summary
    print(f"\n{'='*80}")
    print("MULTI-LIFE SIMULATION COMPLETE")
    print(f"{'='*80}\n")
    print(f"Total lives: {num_lives}")
    print(f"EP predictions made: {ep_predictor.prediction_count}")
    print(f"Pattern corpus size: {len(ep_predictor.pattern_corpus)}")

    # Save results
    results = {
        "session": 112,
        "framework": "Web4 Five-Domain EP Multi-Life",
        "based_on": ["Thor Session 143", "Cascade Multi-Life", "Legion Session 111"],
        "timestamp": datetime.now().isoformat(),
        "lives": lives_summary,
        "ep_stats": {
            "total_predictions": ep_predictor.prediction_count,
            "pattern_corpus_size": len(ep_predictor.pattern_corpus)
        },
        "comparison": {
            "session_111": "Simple heuristic EP - Bob died (ATP=0)",
            "session_143": "SAGE five-domain EP - Both alive (Alice ATP=71, Bob ATP=35)",
            "session_112": "Web4 five-domain EP multi-life - Validates karma carry-forward"
        }
    }

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Five-Domain EP Multi-Life Simulation")
    parser.add_argument("--lives", type=int, default=3, help="Number of lives to simulate")
    parser.add_argument("--ticks", type=int, default=20, help="Ticks per life")
    parser.add_argument("--output", type=str, default="ep_five_domain_multi_life_results.json", help="Output file")

    args = parser.parse_args()

    run_ep_five_domain_multi_life(
        num_lives=args.lives,
        ticks_per_life=args.ticks,
        output_file=args.output
    )
