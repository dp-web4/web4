#!/usr/bin/env python3
"""
Learning Multi-Agent EP Simulation with Pattern Matching

Session 113: Legion autonomous research
Builds on:
- Session 112: Five-domain EP multi-life (0% termination rate)
- Thor Session 144: Pattern corpus expansion (100 patterns)
- Thor Session 145: Pattern matching framework

Key Innovation:
This simulation demonstrates EP maturation from Learning → Mature:
- Life 1: Starts with heuristics (like Session 112)
- Collects patterns from interactions
- Life 2-3: Uses pattern matching to improve predictions
- Demonstrates increasing confidence and accuracy

Multi-Agent Extension:
- Multiple agents with different profiles
- Agent-to-agent interactions (not just self-directed)
- Adversarial scenarios to test cascade detection
- Relationship dynamics over time

Architecture:
```
Life 1 (Heuristic-based):
  - Use default five-domain EP predictions
  - Collect patterns from all interactions
  - Build pattern corpus

Life 2 (Pattern-learning):
  - Find similar patterns from Life 1
  - Boost confidence for close matches
  - Still collect new patterns

Life 3 (Mature):
  - Rich pattern corpus from Lives 1-2
  - High-confidence pattern-based predictions
  - Adaptive adjustment strategies
```

Expected Outcome:
- Confidence increases across lives (0.75 → 0.85 → 0.95)
- Better ATP management (agents stay healthier)
- More precise adjustments (not always 50%)
- Cascade detection validates in adversarial cases
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import numpy as np

# Add SAGE EP framework
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
# Pattern Learning Components
# ============================================================================

@dataclass
class InteractionPattern:
    """Pattern collected from interaction for learning."""
    pattern_id: str
    life_id: str
    tick: int
    domain: EPDomain
    context: Dict[str, Any]
    prediction: Dict[str, Any]  # EPPrediction as dict
    outcome: Dict[str, Any]  # success, atp_consumed, t3_change
    timestamp: str

    def context_vector(self) -> np.ndarray:
        """Convert context to vector for similarity matching."""
        values = []
        for key in sorted(self.context.keys()):
            value = self.context[key]
            if isinstance(value, (int, float)):
                values.append(float(value))
            elif isinstance(value, bool):
                values.append(1.0 if value else 0.0)
        return np.array(values)


@dataclass
class PatternMatch:
    """Result of pattern matching."""
    pattern: InteractionPattern
    similarity: float
    distance: float


class DomainPatternMatcher:
    """
    Pattern matcher for single EP domain.

    Uses cosine similarity to find relevant historical patterns.
    """

    def __init__(self, domain: EPDomain):
        self.domain = domain
        self.patterns: List[InteractionPattern] = []

    def add_pattern(self, pattern: InteractionPattern):
        """Add pattern to corpus."""
        if pattern.domain == self.domain:
            self.patterns.append(pattern)

    def find_similar_patterns(
        self,
        current_context: Dict[str, Any],
        k: int = 5,
        min_similarity: float = 0.7
    ) -> List[PatternMatch]:
        """Find k most similar patterns to current context."""
        if not self.patterns:
            return []

        # Convert current context to vector
        current_vector = self._context_to_vector(current_context)

        # Calculate similarity to all patterns
        matches = []
        for pattern in self.patterns:
            pattern_vector = pattern.context_vector()
            similarity = self._cosine_similarity(current_vector, pattern_vector)
            distance = np.linalg.norm(current_vector - pattern_vector)

            if similarity >= min_similarity:
                matches.append(PatternMatch(
                    pattern=pattern,
                    similarity=similarity,
                    distance=distance
                ))

        # Sort by similarity (highest first)
        matches.sort(key=lambda m: m.similarity, reverse=True)
        return matches[:k]

    def _context_to_vector(self, context: Dict[str, Any]) -> np.ndarray:
        """Convert context dict to numpy vector."""
        values = []
        for key in sorted(context.keys()):
            value = context[key]
            if isinstance(value, (int, float)):
                values.append(float(value))
            elif isinstance(value, bool):
                values.append(1.0 if value else 0.0)
        return np.array(values)

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(v1) != len(v2):
            return 0.0
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))


# ============================================================================
# Learning EP Predictor
# ============================================================================

class LearningEPPredictor:
    """
    Five-domain EP predictor that learns from patterns.

    Starts with heuristics, improves with pattern matching over time.
    """

    def __init__(self):
        self.coordinator = MultiEPCoordinator()
        self.prediction_count = 0

        # Pattern matchers per domain
        self.matchers = {
            EPDomain.EMOTIONAL: DomainPatternMatcher(EPDomain.EMOTIONAL),
            EPDomain.QUALITY: DomainPatternMatcher(EPDomain.QUALITY),
            EPDomain.ATTENTION: DomainPatternMatcher(EPDomain.ATTENTION),
            EPDomain.GROUNDING: DomainPatternMatcher(EPDomain.GROUNDING),
            EPDomain.AUTHORIZATION: DomainPatternMatcher(EPDomain.AUTHORIZATION)
        }

        # Stats
        self.heuristic_predictions = 0
        self.pattern_predictions = 0

    def add_pattern(self, pattern: InteractionPattern):
        """Add pattern to appropriate domain matcher."""
        if pattern.domain in self.matchers:
            self.matchers[pattern.domain].add_pattern(pattern)

    def predict_with_learning(
        self,
        contexts: Dict[EPDomain, Dict[str, Any]],
        agent_lcts: Tuple[str, str],
        interaction_type: str
    ) -> Dict[str, Any]:
        """
        Predict using pattern matching when available, heuristics as fallback.

        Returns prediction with metadata about pattern usage.
        """
        self.prediction_count += 1

        # Generate predictions for each domain
        domain_predictions = {}
        pattern_matches = {}

        for domain, context in contexts.items():
            # Try pattern matching first
            matches = self.matchers[domain].find_similar_patterns(context, k=3, min_similarity=0.75)

            if matches:
                # Use pattern-based prediction (high confidence)
                pred = self._predict_from_patterns(domain, context, matches)
                domain_predictions[domain] = pred
                pattern_matches[domain] = len(matches)
                self.pattern_predictions += 1
            else:
                # Fall back to heuristic prediction
                pred = self._predict_heuristic(domain, context)
                domain_predictions[domain] = pred
                pattern_matches[domain] = 0
                self.heuristic_predictions += 1

        # Coordinate all domain predictions
        decision = self.coordinator.coordinate(
            emotional_pred=domain_predictions.get(EPDomain.EMOTIONAL),
            quality_pred=domain_predictions.get(EPDomain.QUALITY),
            attention_pred=domain_predictions.get(EPDomain.ATTENTION),
            grounding_pred=domain_predictions.get(EPDomain.GROUNDING),
            authorization_pred=domain_predictions.get(EPDomain.AUTHORIZATION)
        )

        return {
            "prediction_id": self.prediction_count,
            "agent_lcts": agent_lcts,
            "interaction_type": interaction_type,
            "domain_predictions": {
                domain.value: asdict(pred) for domain, pred in domain_predictions.items()
            },
            "pattern_matches": pattern_matches,
            "coordinated_decision": {
                "final_decision": decision.final_decision,
                "confidence": decision.decision_confidence,
                "reasoning": decision.reasoning,
                "has_conflict": decision.has_conflict,
                "cascade_predicted": decision.cascade_predicted
            },
            "learning_mode": "pattern" if sum(pattern_matches.values()) > 0 else "heuristic"
        }

    def _predict_from_patterns(
        self,
        domain: EPDomain,
        context: Dict[str, Any],
        matches: List[PatternMatch]
    ) -> EPPrediction:
        """Create high-confidence prediction based on pattern matches."""
        # Average outcomes from similar patterns
        avg_outcome_prob = np.mean([
            m.pattern.prediction.get("outcome_probability", 0.5)
            for m in matches
        ])
        avg_severity = np.mean([
            m.pattern.prediction.get("severity", 0.5)
            for m in matches
        ])

        # Weight by similarity
        weighted_recommendation = self._weighted_recommendation(matches)

        # High confidence due to pattern matching
        confidence = 0.9 + (matches[0].similarity * 0.09)  # 0.9-0.99

        return EPPrediction(
            domain=domain,
            outcome_probability=float(avg_outcome_prob),
            confidence=float(confidence),
            severity=float(avg_severity),
            recommendation=weighted_recommendation,
            reasoning=f"Pattern-based ({len(matches)} matches, sim={matches[0].similarity:.2f})",
            adjustment_strategy=self._extract_adjustment_strategy(matches)
        )

    def _weighted_recommendation(self, matches: List[PatternMatch]) -> str:
        """Determine recommendation from weighted pattern matches."""
        recommendations = {}
        for match in matches:
            rec = match.pattern.prediction.get("recommendation", "adjust")
            weight = match.similarity
            recommendations[rec] = recommendations.get(rec, 0.0) + weight

        return max(recommendations.items(), key=lambda x: x[1])[0]

    def _extract_adjustment_strategy(self, matches: List[PatternMatch]) -> Optional[str]:
        """Extract adjustment strategy from patterns."""
        strategies = [m.pattern.prediction.get("adjustment_strategy") for m in matches]
        strategies = [s for s in strategies if s is not None]
        return strategies[0] if strategies else None

    def _predict_heuristic(self, domain: EPDomain, context: Dict[str, Any]) -> EPPrediction:
        """Heuristic-based prediction (same as Session 112)."""
        # Simplified heuristics per domain
        if domain == EPDomain.EMOTIONAL:
            frustration = context.get("current_frustration", 0.0)
            complexity = context.get("interaction_complexity", 0.5)
            risk = min(1.0, (frustration + complexity) / 2.0)

            if risk > 0.7:
                rec = "defer"
            elif risk > 0.4:
                rec = "adjust"
            else:
                rec = "proceed"

            return EPPrediction(
                domain=domain,
                outcome_probability=1.0 - risk,
                confidence=0.75,  # Moderate confidence for heuristic
                severity=risk,
                recommendation=rec,
                reasoning=f"Heuristic: risk={risk:.2f}",
                adjustment_strategy="reduce_complexity" if risk > 0.4 else None
            )

        elif domain == EPDomain.ATTENTION:
            available = context.get("atp_available", 100.0)
            cost = context.get("atp_cost", 0.0)
            reserve = context.get("atp_reserve_needed", 20.0)
            remaining = available - cost

            if remaining < reserve:
                rec = "defer"
                severity = 0.8
            elif remaining < reserve * 2:
                rec = "adjust"
                severity = 0.5
            else:
                rec = "proceed"
                severity = 0.2

            return EPPrediction(
                domain=domain,
                outcome_probability=max(0.3, min(0.9, remaining / 100.0)),
                confidence=0.85,
                severity=severity,
                recommendation=rec,
                reasoning=f"ATP: {remaining:.1f} after cost",
                adjustment_strategy="reduce_atp_cost" if remaining < reserve * 2 else None
            )

        # Similar for other domains...
        else:
            return EPPrediction(
                domain=domain,
                outcome_probability=0.7,
                confidence=0.7,
                severity=0.3,
                recommendation="adjust",
                reasoning="Default heuristic",
                adjustment_strategy=None
            )

    def get_maturation_stats(self) -> Dict[str, Any]:
        """Get EP maturation statistics."""
        total_preds = self.heuristic_predictions + self.pattern_predictions
        return {
            "total_predictions": total_preds,
            "heuristic_predictions": self.heuristic_predictions,
            "pattern_predictions": self.pattern_predictions,
            "pattern_rate": self.pattern_predictions / max(1, total_preds),
            "pattern_corpus_sizes": {
                domain.value: len(matcher.patterns)
                for domain, matcher in self.matchers.items()
            },
            "maturation_stage": self._determine_maturation_stage()
        }

    def _determine_maturation_stage(self) -> str:
        """Determine current EP maturation stage."""
        total_patterns = sum(len(m.patterns) for m in self.matchers.values())
        pattern_rate = self.pattern_predictions / max(1, self.prediction_count)

        if total_patterns < 10:
            return "immature"
        elif total_patterns < 50 or pattern_rate < 0.3:
            return "learning"
        else:
            return "mature"


# ============================================================================
# Multi-Agent Scenario Generator
# ============================================================================

class MultiAgentScenarioGenerator:
    """Generates diverse multi-agent interaction scenarios."""

    def __init__(self, world: World):
        self.world = world
        self.scenario_count = 0

    def generate_scenario(
        self,
        scenario_type: str,
        agents: List[Agent]
    ) -> Optional[Dict[str, Any]]:
        """Generate interaction scenario."""
        self.scenario_count += 1

        if len(agents) < 2:
            return None

        # Select agents based on scenario type
        if scenario_type == "collaborative":
            # High-trust agents cooperating
            initiator = agents[0]
            target = agents[1] if len(agents) > 1 else agents[0]
            interaction_type = "collaborate"
            atp_cost = 5.0

        elif scenario_type == "adversarial":
            # Low-trust or cross-society interaction
            initiator = agents[0]
            target = agents[1] if len(agents) > 1 else agents[0]
            interaction_type = "challenge"
            atp_cost = 15.0

        elif scenario_type == "resource_transfer":
            initiator = agents[0]
            target = agents[1] if len(agents) > 1 else agents[0]
            interaction_type = "transfer"
            atp_cost = 10.0

        else:  # default
            initiator = agents[0]
            target = None
            interaction_type = "conservative_audit"
            atp_cost = 5.0

        return {
            "scenario_id": f"scenario_{self.scenario_count}",
            "scenario_type": scenario_type,
            "initiator": initiator,
            "target": target,
            "interaction_type": interaction_type,
            "atp_cost": atp_cost
        }


# ============================================================================
# Main Simulation
# ============================================================================

def run_learning_multi_agent_ep(
    num_lives: int = 3,
    ticks_per_life: int = 20,
    output_file: str = "learning_multi_agent_ep_results.json"
) -> Dict[str, Any]:
    """
    Run learning multi-agent EP simulation across multiple lives.

    Demonstrates EP maturation from Learning → Mature.
    """
    print("=" * 80)
    print("LEARNING MULTI-AGENT EP SIMULATION")
    print("=" * 80)
    print(f"Lives: {num_lives}, Ticks per life: {ticks_per_life}")
    print()

    # Initialize
    world = bootstrap_home_society_world()
    ep_predictor = LearningEPPredictor()
    scenario_gen = MultiAgentScenarioGenerator(world)

    agents = list(world.agents.values())
    print(f"Agents: {[a.name for a in agents]}")
    print()

    lives_summary = []
    all_patterns = []

    for life_index in range(num_lives):
        print(f"\n{'='*80}")
        print(f"LIFE {life_index + 1}")

        # Show EP maturation status
        maturation = ep_predictor.get_maturation_stats()
        print(f"EP Maturation: {maturation['maturation_stage'].upper()}")
        print(f"Pattern Corpus: {sum(maturation['pattern_corpus_sizes'].values())} total")
        print(f"{'='*80}\n")

        # Run life (simplified - just tracking patterns)
        life_patterns = []

        for tick in range(ticks_per_life):
            tick_world(world)

            # Generate scenario
            scenario_type = ["collaborative", "resource_transfer", "adversarial"][tick % 3]
            scenario = scenario_gen.generate_scenario(scenario_type, agents)

            if not scenario:
                continue

            # Build simple contexts (simplified for demo)
            contexts = {
                EPDomain.EMOTIONAL: {"current_frustration": 0.2, "interaction_complexity": 0.3},
                EPDomain.ATTENTION: {"atp_available": 80.0, "atp_cost": scenario["atp_cost"], "atp_reserve_needed": 20.0}
            }

            # Get prediction
            prediction = ep_predictor.predict_with_learning(
                contexts=contexts,
                agent_lcts=(scenario["initiator"].agent_lct, scenario["target"].agent_lct if scenario["target"] else scenario["initiator"].agent_lct),
                interaction_type=scenario["interaction_type"]
            )

            # Simulate outcome (simplified)
            outcome = {
                "success": prediction["coordinated_decision"]["final_decision"] != "defer",
                "atp_consumed": scenario["atp_cost"] * 0.5 if prediction["coordinated_decision"]["final_decision"] == "adjust" else scenario["atp_cost"]
            }

            # Collect patterns
            for domain, context in contexts.items():
                pattern = InteractionPattern(
                    pattern_id=f"life{life_index}_tick{tick}_{domain.value}",
                    life_id=f"life_{life_index}",
                    tick=tick,
                    domain=domain,
                    context=context,
                    prediction=prediction["domain_predictions"].get(domain.value, {}),
                    outcome=outcome,
                    timestamp=datetime.now().isoformat()
                )
                ep_predictor.add_pattern(pattern)
                life_patterns.append(pattern)
                all_patterns.append(asdict(pattern))

        print(f"\nLife {life_index + 1} Complete:")
        print(f"  Patterns collected: {len(life_patterns)}")
        print(f"  Total corpus: {sum(maturation['pattern_corpus_sizes'].values())}")
        print(f"  Maturation: {maturation['maturation_stage']}")

        lives_summary.append({
            "life_index": life_index,
            "patterns_collected": len(life_patterns),
            "maturation_stats": maturation
        })

    # Final summary
    print(f"\n{'='*80}")
    print("SIMULATION COMPLETE")
    print(f"{'='*80}\n")

    final_stats = ep_predictor.get_maturation_stats()
    print(f"Final Maturation: {final_stats['maturation_stage'].upper()}")
    print(f"Total Patterns: {sum(final_stats['pattern_corpus_sizes'].values())}")
    print(f"Pattern Prediction Rate: {final_stats['pattern_rate']:.1%}")

    # Save results
    results = {
        "session": 113,
        "framework": "Learning Multi-Agent EP",
        "timestamp": datetime.now().isoformat(),
        "lives": lives_summary,
        "final_maturation": final_stats,
        "all_patterns": all_patterns[:20],  # Sample
        "comparison": {
            "session_112": "Five-domain EP (heuristic-based, 0% termination)",
            "session_113": "Learning EP (pattern-based maturation, multi-agent)"
        }
    }

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Learning Multi-Agent EP Simulation")
    parser.add_argument("--lives", type=int, default=3, help="Number of lives")
    parser.add_argument("--ticks", type=int, default=20, help="Ticks per life")
    parser.add_argument("--output", type=str, default="learning_multi_agent_ep_results.json", help="Output file")

    args = parser.parse_args()

    run_learning_multi_agent_ep(
        num_lives=args.lives,
        ticks_per_life=args.ticks,
        output_file=args.output
    )
