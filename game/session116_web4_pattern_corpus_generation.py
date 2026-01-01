#!/usr/bin/env python3
"""
Session 116: Web4-Specific ATP Pattern Corpus Generation

Following Thor's Session 147 methodology, generate production-native patterns
for Web4 ATP resource management.

Problem from Session 115:
- Thor's SAGE patterns trained on consciousness scenarios
- When applied to ATP management → 100% agent death
- Pattern matching worked, but context mismatch

Solution:
- Generate patterns FROM Web4 ATP management scenarios
- Use same context structure as ep_driven_policy.py
- Cover diverse ATP scenarios (abundance, scarcity, critical)

Goal: 100 Web4-native patterns for true EP maturation demonstration

Methodology (from Thor Session 147):
1. Define scenario types (ATP-specific)
2. Generate diverse scenarios for each type
3. Run EP predictions with heuristics
4. Record patterns with actual contexts
5. Create clean JSON corpus

Architecture:
- Scenario types: ATP abundance, scarcity, critical, recovery, etc.
- 10 scenario types × 10 patterns each = 100 total
- Record in same format as Session 115's InteractionPattern
"""

import sys
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

# Add Web4 modules
sys.path.insert(0, str(Path(__file__).parent))
from ep_driven_policy import EPDomain, EPPrediction, Web4EPContextBuilder
from engine.models import Agent, World

# Import SAGE EP coordinator
hrm_path = Path(__file__).parent.parent.parent / "HRM"
sys.path.insert(0, str(hrm_path / "sage" / "experiments"))
from multi_ep_coordinator import MultiEPCoordinator


# ============================================================================
# Web4 ATP Scenario Types
# ============================================================================

class Web4ScenarioType:
    """ATP resource management scenario types."""

    # Abundance scenarios (ATP > 80)
    ABUNDANCE_HIGH_T3 = "atp_abundance_high_t3"  # Lots of ATP, high trust
    ABUNDANCE_LOW_T3 = "atp_abundance_low_t3"    # Lots of ATP, low trust
    ABUNDANCE_RISKY_SPEND = "atp_abundance_risky_spend"  # Can afford risky actions

    # Moderate scenarios (ATP 40-80)
    MODERATE_BALANCED = "atp_moderate_balanced"  # Balanced ATP and T3
    MODERATE_DECLINING = "atp_moderate_declining"  # ATP dropping
    MODERATE_RECOVERING = "atp_moderate_recovering"  # ATP rising

    # Scarcity scenarios (ATP 20-40)
    SCARCITY_APPROACHING = "atp_scarcity_approaching"  # Nearing reserve
    SCARCITY_CONSERVATIVE = "atp_scarcity_conservative"  # Need conservation

    # Critical scenarios (ATP < 20)
    CRITICAL_SURVIVAL = "atp_critical_survival"  # Near death threshold
    CRITICAL_RECOVERY = "atp_critical_recovery"  # Trying to recover


# ============================================================================
# Web4 Pattern Generator
# ============================================================================

class Web4PatternGenerator:
    """Generates Web4-specific ATP management patterns."""

    def __init__(self):
        self.coordinator = MultiEPCoordinator()
        self.patterns_generated = 0

    def generate_corpus(
        self,
        patterns_per_type: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate complete Web4 ATP pattern corpus.

        Returns list of patterns compatible with Session 115's InteractionPattern.
        """
        all_patterns = []

        scenario_types = [
            Web4ScenarioType.ABUNDANCE_HIGH_T3,
            Web4ScenarioType.ABUNDANCE_LOW_T3,
            Web4ScenarioType.ABUNDANCE_RISKY_SPEND,
            Web4ScenarioType.MODERATE_BALANCED,
            Web4ScenarioType.MODERATE_DECLINING,
            Web4ScenarioType.MODERATE_RECOVERING,
            Web4ScenarioType.SCARCITY_APPROACHING,
            Web4ScenarioType.SCARCITY_CONSERVATIVE,
            Web4ScenarioType.CRITICAL_SURVIVAL,
            Web4ScenarioType.CRITICAL_RECOVERY,
        ]

        for scenario_type in scenario_types:
            for i in range(patterns_per_type):
                pattern = self._generate_pattern(scenario_type, i)
                all_patterns.append(pattern)
                self.patterns_generated += 1

        return all_patterns

    def _generate_pattern(
        self,
        scenario_type: str,
        index: int
    ) -> Dict[str, Any]:
        """Generate single pattern for scenario type."""

        # Create scenario
        scenario = self._create_scenario(scenario_type, index)

        # Build EP contexts (using Web4EPContextBuilder)
        contexts_raw = {
            EPDomain.EMOTIONAL: Web4EPContextBuilder.build_emotional_context(
                scenario["agent"], scenario["action_type"], scenario["world"]
            ),
            EPDomain.QUALITY: Web4EPContextBuilder.build_quality_context(
                scenario["agent"], scenario["action_type"]
            ),
            EPDomain.ATTENTION: Web4EPContextBuilder.build_attention_context(
                scenario["agent"], scenario["atp_cost"]
            ),
        }

        # Convert to string keys for JSON serialization
        contexts = {
            str(domain).split(".")[-1].lower(): ctx
            for domain, ctx in contexts_raw.items()
        }

        # Generate heuristic EP predictions
        predictions = self._generate_ep_predictions(contexts_raw)

        # Coordinate predictions
        coordinated = self.coordinator.coordinate(
            emotional_pred=predictions[EPDomain.EMOTIONAL],
            quality_pred=predictions[EPDomain.QUALITY],
            attention_pred=predictions[EPDomain.ATTENTION],
        )

        # Determine outcome
        outcome = self._determine_outcome(scenario, coordinated)

        # Create pattern
        pattern = {
            "pattern_id": f"web4_{scenario_type}_{index}",
            "scenario_type": scenario_type,
            "scenario_description": scenario["description"],
            "timestamp": datetime.now().isoformat(),
            "context": contexts,
            "ep_predictions": {
                str(domain).split(".")[-1].lower(): {
                    "domain": str(domain),
                    "outcome_probability": pred.outcome_probability,
                    "confidence": pred.confidence,
                    "severity": pred.severity,
                    "recommendation": pred.recommendation,
                    "reasoning": pred.reasoning,
                }
                for domain, pred in predictions.items()
            },
            "coordinated_decision": {
                "final_decision": coordinated.final_decision,
                "confidence": coordinated.decision_confidence,
                "reasoning": coordinated.reasoning,
                "has_conflict": coordinated.has_conflict,
            },
            "outcome": outcome,
        }

        return pattern

    def _create_scenario(
        self,
        scenario_type: str,
        index: int
    ) -> Dict[str, Any]:
        """Create scenario with specific ATP/T3 conditions."""

        # Create Agent and World objects
        agent = Agent(agent_lct=f"lct:web4:agent:test_{index}", name=f"TestAgent{index}")
        world = World()
        world.tick = index

        # Base scenario structure
        scenario = {
            "agent": agent,
            "world": world,
            "action_type": "",
            "atp_cost": 0.0,
            "description": "",
        }

        # ATP abundance scenarios
        if scenario_type == Web4ScenarioType.ABUNDANCE_HIGH_T3:
            atp = random.uniform(85, 100)
            t3 = random.uniform(0.6, 0.9)
            agent.resources["ATP"] = atp
            agent.trust_axes["T3"] = {"composite": t3}
            scenario["action_type"] = "risky_spend"
            scenario["atp_cost"] = 25.0
            scenario["description"] = f"Abundance scenario: ATP={atp:.1f}, T3={t3:.2f}, can afford risky actions"

        elif scenario_type == Web4ScenarioType.ABUNDANCE_LOW_T3:
            atp = random.uniform(85, 100)
            t3 = random.uniform(0.2, 0.4)
            agent.resources["ATP"] = atp
            agent.trust_axes["T3"] = {"composite": t3}
            scenario["action_type"] = "small_spend"
            scenario["atp_cost"] = 10.0
            scenario["description"] = f"Abundance with low trust: ATP={atp:.1f}, T3={t3:.2f}, cautious despite resources"

        elif scenario_type == Web4ScenarioType.ABUNDANCE_RISKY_SPEND:
            atp = random.uniform(90, 100)
            t3 = random.uniform(0.5, 0.8)
            agent.resources["ATP"] = atp
            agent.trust_axes["T3"] = {"composite": t3}
            scenario["action_type"] = "risky_spend"
            scenario["atp_cost"] = 25.0
            scenario["description"] = f"Optimal conditions for risk: ATP={atp:.1f}, T3={t3:.2f}"

        # Moderate scenarios
        elif scenario_type == Web4ScenarioType.MODERATE_BALANCED:
            atp = random.uniform(50, 70)
            t3 = random.uniform(0.45, 0.55)
            agent.resources["ATP"] = atp
            agent.trust_axes["T3"] = {"composite": t3}
            scenario["action_type"] = "small_spend"
            scenario["atp_cost"] = 10.0
            scenario["description"] = f"Balanced moderate state: ATP={atp:.1f}, T3={t3:.2f}"

        elif scenario_type == Web4ScenarioType.MODERATE_DECLINING:
            atp = random.uniform(40, 60)
            t3 = random.uniform(0.4, 0.5)
            agent.resources["ATP"] = atp
            agent.trust_axes["T3"] = {"composite": t3}
            scenario["action_type"] = "small_spend"
            scenario["atp_cost"] = 10.0
            scenario["description"] = f"Declining resources: ATP={atp:.1f}, T3={t3:.2f}, need conservation"

        elif scenario_type == Web4ScenarioType.MODERATE_RECOVERING:
            atp = random.uniform(50, 70)
            t3 = random.uniform(0.5, 0.6)
            agent.resources["ATP"] = atp
            agent.trust_axes["T3"] = {"composite": t3}
            scenario["action_type"] = "conservative_audit"
            scenario["atp_cost"] = 5.0
            scenario["description"] = f"Recovering state: ATP={atp:.1f}, T3={t3:.2f}, cautious growth"

        # Scarcity scenarios
        elif scenario_type == Web4ScenarioType.SCARCITY_APPROACHING:
            atp = random.uniform(25, 35)
            t3 = random.uniform(0.4, 0.6)
            agent.resources["ATP"] = atp
            agent.trust_axes["T3"] = {"composite": t3}
            scenario["action_type"] = "conservative_audit"
            scenario["atp_cost"] = 5.0
            scenario["description"] = f"Approaching scarcity: ATP={atp:.1f}, T3={t3:.2f}, must conserve"

        elif scenario_type == Web4ScenarioType.SCARCITY_CONSERVATIVE:
            atp = random.uniform(20, 30)
            t3 = random.uniform(0.3, 0.5)
            agent.resources["ATP"] = atp
            agent.trust_axes["T3"] = {"composite": t3}
            scenario["action_type"] = "conservative_audit"
            scenario["atp_cost"] = 5.0
            scenario["description"] = f"Scarcity mode: ATP={atp:.1f}, T3={t3:.2f}, strict conservation"

        # Critical scenarios
        elif scenario_type == Web4ScenarioType.CRITICAL_SURVIVAL:
            atp = random.uniform(5, 15)
            t3 = random.uniform(0.3, 0.6)
            agent.resources["ATP"] = atp
            agent.trust_axes["T3"] = {"composite": t3}
            scenario["action_type"] = "idle"
            scenario["atp_cost"] = 0.0
            scenario["description"] = f"CRITICAL survival: ATP={atp:.1f}, T3={t3:.2f}, defer all actions"

        elif scenario_type == Web4ScenarioType.CRITICAL_RECOVERY:
            atp = random.uniform(10, 20)
            t3 = random.uniform(0.4, 0.7)
            agent.resources["ATP"] = atp
            agent.trust_axes["T3"] = {"composite": t3}
            scenario["action_type"] = "idle"
            scenario["atp_cost"] = 0.0
            scenario["description"] = f"Critical recovery: ATP={atp:.1f}, T3={t3:.2f}, minimal actions only"

        return scenario

    def _generate_ep_predictions(
        self,
        contexts: Dict[EPDomain, Dict[str, Any]]
    ) -> Dict[EPDomain, EPPrediction]:
        """Generate heuristic EP predictions (same as ep_driven_policy.py)."""

        predictions = {}

        # Emotional EP
        emotional_ctx = contexts[EPDomain.EMOTIONAL]
        frustration = emotional_ctx.get("current_frustration", 0.0)
        complexity = emotional_ctx.get("interaction_complexity", 0.5)
        severity = (frustration + complexity) / 2.0

        if severity > 0.7:
            rec = "defer"
        elif severity > 0.4:
            rec = "adjust"
        else:
            rec = "proceed"

        predictions[EPDomain.EMOTIONAL] = EPPrediction(
            domain=EPDomain.EMOTIONAL,
            outcome_probability=1.0 - severity,
            confidence=0.75,
            severity=severity,
            recommendation=rec,
            reasoning=f"Heuristic: frustration={frustration:.2f}, complexity={complexity:.2f}",
            adjustment_strategy={}
        )

        # Quality EP
        quality_ctx = contexts[EPDomain.QUALITY]
        quality = quality_ctx.get("current_relationship_quality", 0.5)
        risk = quality_ctx.get("interaction_risk_to_quality", 0.3)
        severity = risk * (1.0 - quality)

        if severity > 0.6:
            rec = "defer"
        elif severity > 0.3:
            rec = "adjust"
        else:
            rec = "proceed"

        predictions[EPDomain.QUALITY] = EPPrediction(
            domain=EPDomain.QUALITY,
            outcome_probability=quality * (1.0 - risk),
            confidence=0.75,
            severity=severity,
            recommendation=rec,
            reasoning=f"Heuristic: quality={quality:.2f}, risk={risk:.2f}",
            adjustment_strategy={}
        )

        # Attention EP (CRITICAL for ATP management)
        attention_ctx = contexts[EPDomain.ATTENTION]
        atp_available = attention_ctx.get("atp_available", 0.0)
        atp_cost = attention_ctx.get("atp_cost", 0.0)
        atp_reserve = attention_ctx.get("atp_reserve_needed", 20.0)

        atp_after = atp_available - atp_cost
        severity = 0.0

        if atp_after < atp_reserve:
            severity = 0.9
            rec = "defer"
        elif atp_after < atp_reserve * 2:
            severity = 0.5
            rec = "adjust"
        else:
            severity = 0.2
            rec = "proceed"

        predictions[EPDomain.ATTENTION] = EPPrediction(
            domain=EPDomain.ATTENTION,
            outcome_probability=1.0 - severity,
            confidence=0.75,
            severity=severity,
            recommendation=rec,
            reasoning=f"Heuristic: ATP {atp_available:.1f} → {atp_after:.1f} (reserve={atp_reserve})",
            adjustment_strategy={}
        )

        return predictions

    def _determine_outcome(
        self,
        scenario: Dict[str, Any],
        coordinated: Any
    ) -> Dict[str, Any]:
        """Determine outcome based on coordinated decision."""

        agent = scenario["agent"]
        atp_before = agent.resources["ATP"]
        atp_cost = scenario["atp_cost"]
        t3_before = agent.trust_axes["T3"]["composite"]

        # Apply decision
        if coordinated.final_decision == "proceed":
            atp_after = atp_before - atp_cost
            # Small T3 impact from action
            if scenario["action_type"] == "risky_spend":
                t3_after = t3_before - 0.01  # Risk can hurt trust
            elif scenario["action_type"] == "conservative_audit":
                t3_after = t3_before + 0.01  # Audits build trust
            else:
                t3_after = t3_before
        elif coordinated.final_decision == "adjust":
            # Downgrade action (lower cost)
            atp_after = atp_before - (atp_cost * 0.5)  # Half cost
            t3_after = t3_before + 0.005  # Conservative is good
        else:  # defer
            atp_after = atp_before  # No cost
            t3_after = t3_before

        # Determine success
        success = atp_after > 0 and t3_after >= 0.2

        return {
            "final_decision": coordinated.final_decision,
            "atp_before": atp_before,
            "atp_after": atp_after,
            "t3_before": t3_before,
            "t3_after": t3_after,
            "success": success,
            "survived": atp_after > 0,
        }


# ============================================================================
# Main Generation
# ============================================================================

def generate_web4_corpus(output_file: Path, patterns_per_type: int = 10):
    """Generate and save Web4 ATP pattern corpus."""

    print("=" * 80)
    print("WEB4 ATP PATTERN CORPUS GENERATION")
    print("=" * 80)
    print(f"Generating {patterns_per_type * 10} patterns (10 scenario types)")
    print()

    generator = Web4PatternGenerator()
    patterns = generator.generate_corpus(patterns_per_type=patterns_per_type)

    # Create corpus document
    corpus = {
        "session": 116,
        "generated_by": "Legion - Autonomous Research",
        "timestamp": datetime.now().isoformat(),
        "description": "Web4-native ATP management patterns for EP maturation",
        "source": "Production-native Web4 scenarios (following Thor Session 147 methodology)",
        "total_patterns": len(patterns),
        "scenario_types": 10,
        "patterns_per_type": patterns_per_type,
        "context_structure": "Web4EPContextBuilder (compatible with ep_driven_policy.py)",
        "patterns": patterns,
    }

    # Save corpus
    with open(output_file, 'w') as f:
        json.dump(corpus, f, indent=2)

    print(f"✅ Generated {len(patterns)} patterns")
    print(f"✅ Saved to: {output_file}")
    print()

    # Statistics
    by_decision = {}
    by_scenario = {}
    for p in patterns:
        dec = p["coordinated_decision"]["final_decision"]
        by_decision[dec] = by_decision.get(dec, 0) + 1

        scenario = p["scenario_type"]
        by_scenario[scenario] = by_scenario.get(scenario, 0) + 1

    print("Decision Distribution:")
    for decision, count in sorted(by_decision.items()):
        print(f"  {decision}: {count}")

    print()
    print("Scenario Distribution:")
    for scenario, count in sorted(by_scenario.items()):
        print(f"  {scenario}: {count}")

    print()
    print("=" * 80)
    print("CORPUS GENERATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    output_file = Path(__file__).parent / "ep_pattern_corpus_web4_native.json"
    generate_web4_corpus(output_file, patterns_per_type=10)
