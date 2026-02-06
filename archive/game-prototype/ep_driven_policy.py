#!/usr/bin/env python3
"""
EP-Driven Policy for Web4 Closed-Loop Multi-Life

Session 114-115: Legion autonomous research
- Session 114: EP-driven policy with safety layer (100% survival)
- Session 115: Pattern learning integration (maturation demonstration)
Integrates:
- Session 113: Learning EP with pattern matching (maturation IMMATURE→LEARNING→MATURE)
- Session 112: Five-domain EP contexts (Emotional, Quality, Attention, Grounding, Authorization)
- Cascade's closed-loop framework: HRM policy integration with action application

This replaces the simple heuristic policy in `research_agent_driver.py` with
EP-based predictions that learn from experience.

Key Innovation:
- Uses EP predictions to propose actions (instead of simple heuristics)
- Learns from outcomes to improve future predictions
- Maturation progression: IMMATURE (heuristic) → LEARNING (mixed) → MATURE (pattern-based)

Architecture:
```
Tick N:
  1. Build EP contexts from current agent/world state
  2. Generate EP predictions (pattern-based if available, else heuristic)
  3. Coordinate predictions across domains
  4. Propose action based on coordinated decision:
     - "proceed" → risky_spend or small_spend
     - "adjust" → conservative_audit (lower ATP cost)
     - "defer" → idle (zero cost)
  5. Apply action via closed-loop framework
  6. Record outcome as pattern for learning
Tick N+1:
  → Pattern corpus grows, EP matures
```

Comparison to Heuristic Policy:
- Heuristic: if ATP < 20 → conservative, if ATP > 80 → risky
- EP-Driven: Multi-domain assessment with learning from past similar contexts

"""

import sys
from pathlib import Path
from dataclasses import dataclass, asdict
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
from engine.models import Agent, Society, World


# ============================================================================
# Pattern Learning (from Session 113)
# ============================================================================

@dataclass
class InteractionPattern:
    """Pattern collected from interaction for learning."""
    pattern_id: str
    life_id: str
    tick: int
    domain: EPDomain
    context: Dict[str, Any]
    prediction: Dict[str, Any]
    outcome: Dict[str, Any]
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
    """A pattern match with similarity score."""
    pattern: InteractionPattern
    similarity: float
    distance: float


class DomainPatternMatcher:
    """Pattern matcher for single EP domain using cosine similarity."""

    def __init__(self, domain: EPDomain):
        self.domain = domain
        self.patterns: List[InteractionPattern] = []

    def add_pattern(self, pattern: InteractionPattern) -> None:
        """Add a pattern to the corpus."""
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

        current_vector = self._context_to_vector(current_context)

        matches = []
        for pattern in self.patterns:
            pattern_vector = pattern.context_vector()

            # Handle dimension mismatch (different context keys)
            if len(current_vector) != len(pattern_vector):
                continue

            similarity = self._cosine_similarity(current_vector, pattern_vector)
            distance = np.linalg.norm(current_vector - pattern_vector)

            if similarity >= min_similarity:
                matches.append(PatternMatch(
                    pattern=pattern,
                    similarity=similarity,
                    distance=distance
                ))

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
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0

        return float(np.dot(v1, v2) / (norm1 * norm2))


# ============================================================================
# EP Context Builders (from Session 112)
# ============================================================================

class Web4EPContextBuilder:
    """Builds EP contexts from Web4 agent/world state for action proposals."""

    @staticmethod
    def build_emotional_context(
        agent: Agent,
        proposed_action_type: str,
        world: World
    ) -> Dict[str, Any]:
        """Build Emotional EP context."""
        atp = agent.resources.get("ATP", 0.0)
        frustration = max(0.0, min(1.0, (100.0 - atp) / 100.0))

        complexity_map = {
            "idle": 0.1,
            "conservative_audit": 0.3,
            "small_spend": 0.4,
            "risky_spend": 0.7,
        }
        complexity = complexity_map.get(proposed_action_type, 0.5)

        return {
            "current_frustration": frustration,
            "recent_failure_rate": 0.1,
            "atp_stress": frustration,
            "interaction_complexity": complexity
        }

    @staticmethod
    def build_quality_context(
        agent: Agent,
        proposed_action_type: str
    ) -> Dict[str, Any]:
        """Build Quality EP context."""
        t3 = agent.trust_axes.get("T3", {}).get("composite", 0.5)

        risk_map = {
            "idle": 0.0,
            "conservative_audit": 0.1,
            "small_spend": 0.2,
            "risky_spend": 0.6,
        }
        risk = risk_map.get(proposed_action_type, 0.3)

        return {
            "current_relationship_quality": t3,
            "recent_avg_outcome": 0.6,
            "trust_alignment": t3,
            "interaction_risk_to_quality": risk
        }

    @staticmethod
    def build_attention_context(
        agent: Agent,
        proposed_atp_cost: float
    ) -> Dict[str, Any]:
        """Build Attention EP context."""
        atp_available = agent.resources.get("ATP", 0.0)

        return {
            "atp_available": atp_available,
            "atp_cost": proposed_atp_cost,
            "atp_reserve_needed": 20.0,
            "interaction_count": 0,
            "expected_benefit": max(0.0, proposed_atp_cost * 0.5)
        }


# ============================================================================
# EP-Driven Policy
# ============================================================================

class EPDrivenPolicy:
    """EP-based policy that learns from experience and proposes actions."""

    def __init__(self):
        self.coordinator = MultiEPCoordinator()
        self.matchers: Dict[EPDomain, DomainPatternMatcher] = {
            EPDomain.EMOTIONAL: DomainPatternMatcher(EPDomain.EMOTIONAL),
            EPDomain.QUALITY: DomainPatternMatcher(EPDomain.QUALITY),
            EPDomain.ATTENTION: DomainPatternMatcher(EPDomain.ATTENTION),
        }

        # Learning statistics
        self.prediction_count = 0
        self.pattern_predictions = 0
        self.heuristic_predictions = 0

    def propose_action(
        self,
        agent: Agent,
        world: World,
        life_id: str
    ) -> Dict[str, Any]:
        """
        Propose an action based on EP predictions.

        Architecture:
        1. Generate initial action proposal (like heuristic policy does)
        2. Ask EP to assess the proposal
        3. EP decides: proceed / adjust (reduce cost) / defer (idle instead)

        Returns:
            {
                "proposed_action": {
                    "action_type": "idle" | "conservative_audit" | "small_spend" | "risky_spend",
                    "atp_cost": float,
                    "description": str
                },
                "ep_assessment": {
                    "coordinated_decision": {...},
                    "pattern_matches": {...},
                    "learning_mode": "pattern" | "heuristic",
                    "maturation_stage": "immature" | "learning" | "mature"
                }
            }
        """

        # Generate initial proposal (heuristic-based)
        initial_action = self._generate_initial_proposal(agent)

        # Ask EP to assess this proposal
        assessment = self._assess_action_with_ep(
            agent, world, life_id, initial_action
        )

        # EP decision modifies the action
        final_decision = assessment["coordinated_decision"]["final_decision"]

        if final_decision == "proceed":
            # EP says go ahead with initial proposal
            final_action = initial_action
        elif final_decision == "adjust":
            # EP says reduce risk - downgrade to lower-cost action
            final_action = self._adjust_action(initial_action, agent)
        else:  # defer
            # EP says don't do it - idle instead
            final_action = {
                "action_type": "idle",
                "atp_cost": 0.0,
                "description": "EP deferred initial proposal - resting instead"
            }

        return {
            "proposed_action": final_action,
            "ep_assessment": assessment
        }

    def _generate_initial_proposal(self, agent: Agent) -> Dict[str, Any]:
        """
        Generate initial action proposal (same logic as heuristic policy).

        This mimics ResearchAgentDriver logic:
        - ATP < 20 or T3 < 0.3 → conservative_audit
        - ATP > 80 and T3 >= 0.5 → risky_spend
        - Otherwise → small_spend
        """
        t3 = agent.trust_axes.get("T3", {}).get("composite", 0.5)
        atp = agent.resources.get("ATP", 0.0)

        if atp < 20.0 or t3 < 0.3:
            return {
                "action_type": "conservative_audit",
                "atp_cost": 5.0,
                "description": "Low ATP or fragile T3; propose audit/verification"
            }

        if atp > 80.0 and t3 >= 0.5:
            return {
                "action_type": "risky_spend",
                "atp_cost": 25.0,
                "description": "High ATP and solid T3; propose experimental spend"
            }

        return {
            "action_type": "small_spend",
            "atp_cost": 10.0,
            "description": "Moderate ATP/T3; propose small exploratory spend"
        }

    def _adjust_action(self, action: Dict[str, Any], agent: Agent) -> Dict[str, Any]:
        """Adjust action to reduce risk (EP recommended 'adjust')."""
        action_type = action["action_type"]

        # Downgrade to less risky action
        if action_type == "risky_spend":
            return {
                "action_type": "small_spend",
                "atp_cost": 10.0,
                "description": "EP adjusted: downgraded from risky_spend to small_spend"
            }
        elif action_type == "small_spend":
            return {
                "action_type": "conservative_audit",
                "atp_cost": 5.0,
                "description": "EP adjusted: downgraded from small_spend to conservative_audit"
            }
        elif action_type == "conservative_audit":
            return {
                "action_type": "idle",
                "atp_cost": 0.0,
                "description": "EP adjusted: downgraded from conservative_audit to idle"
            }
        else:  # already idle
            return action

    def _assess_action_with_ep(
        self,
        agent: Agent,
        world: World,
        life_id: str,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess a proposed action using EP predictions."""

        # Build contexts for this action
        contexts = {
            EPDomain.EMOTIONAL: Web4EPContextBuilder.build_emotional_context(
                agent, action["action_type"], world
            ),
            EPDomain.QUALITY: Web4EPContextBuilder.build_quality_context(
                agent, action["action_type"]
            ),
            EPDomain.ATTENTION: Web4EPContextBuilder.build_attention_context(
                agent, action["atp_cost"]
            ),
        }

        # Generate predictions (pattern-based if available, else heuristic)
        domain_predictions = {}
        pattern_matches = {}

        for domain, context in contexts.items():
            matches = self.matchers[domain].find_similar_patterns(
                context, k=3, min_similarity=0.75
            )

            if matches:
                # Pattern-based prediction
                pattern_pred = self._predict_from_patterns(domain, context, matches)

                # SAFETY OVERRIDE: For Attention domain, check heuristic for critical ATP situations
                if domain == EPDomain.ATTENTION:
                    heuristic_pred = self._predict_heuristic(domain, context)
                    # If heuristic says defer/adjust but patterns say proceed, use more conservative
                    if heuristic_pred.recommendation in ["defer", "adjust"] and pattern_pred.recommendation == "proceed":
                        # Override with heuristic (safety first)
                        pred = heuristic_pred
                        self.heuristic_predictions += 1
                    else:
                        pred = pattern_pred
                        self.pattern_predictions += 1
                else:
                    pred = pattern_pred
                    self.pattern_predictions += 1
            else:
                pred = self._predict_heuristic(domain, context)
                self.heuristic_predictions += 1

            domain_predictions[domain] = pred
            pattern_matches[domain] = len(matches)

        self.prediction_count += 1

        # Coordinate predictions
        decision = self.coordinator.coordinate(
            emotional_pred=domain_predictions.get(EPDomain.EMOTIONAL),
            quality_pred=domain_predictions.get(EPDomain.QUALITY),
            attention_pred=domain_predictions.get(EPDomain.ATTENTION),
            grounding_pred=None,  # Not using in this simplified version
            authorization_pred=None  # Not using in this simplified version
        )

        return {
            "coordinated_decision": {
                "final_decision": decision.final_decision,
                "confidence": decision.decision_confidence,
                "reasoning": decision.reasoning,
                "has_conflict": decision.has_conflict
            },
            "pattern_matches": pattern_matches,
            "learning_mode": "pattern" if sum(pattern_matches.values()) > 0 else "heuristic",
            "maturation_stage": self._determine_maturation_stage(),
            # Store for pattern collection
            "contexts": contexts,
            "predictions": domain_predictions
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

        # High confidence due to pattern matching
        confidence = 0.9 + (matches[0].similarity * 0.09)  # 0.90-0.99

        # Weighted recommendation from patterns
        recommendations = [m.pattern.prediction.get("recommendation", "proceed") for m in matches]
        weighted_recommendation = max(set(recommendations), key=recommendations.count)

        return EPPrediction(
            domain=domain,
            outcome_probability=float(avg_outcome_prob),
            confidence=float(confidence),
            severity=float(avg_severity),
            recommendation=weighted_recommendation,
            reasoning=f"Pattern-based ({len(matches)} matches, sim={matches[0].similarity:.2f})",
            adjustment_strategy={}
        )

    def _predict_heuristic(
        self,
        domain: EPDomain,
        context: Dict[str, Any]
    ) -> EPPrediction:
        """Fallback heuristic prediction when no patterns available."""

        if domain == EPDomain.EMOTIONAL:
            frustration = context.get("current_frustration", 0.0)
            complexity = context.get("interaction_complexity", 0.5)
            severity = (frustration + complexity) / 2.0

            if severity > 0.7:
                rec = "defer"
            elif severity > 0.4:
                rec = "adjust"
            else:
                rec = "proceed"

            return EPPrediction(
                domain=domain,
                outcome_probability=1.0 - severity,
                confidence=0.75,
                severity=severity,
                recommendation=rec,
                reasoning=f"Heuristic: frustration={frustration:.2f}, complexity={complexity:.2f}",
                adjustment_strategy={}
            )

        elif domain == EPDomain.QUALITY:
            quality = context.get("current_relationship_quality", 0.5)
            risk = context.get("interaction_risk_to_quality", 0.3)
            severity = risk * (1.0 - quality)

            if severity > 0.6:
                rec = "defer"
            elif severity > 0.3:
                rec = "adjust"
            else:
                rec = "proceed"

            return EPPrediction(
                domain=domain,
                outcome_probability=quality * (1.0 - risk),
                confidence=0.75,
                severity=severity,
                recommendation=rec,
                reasoning=f"Heuristic: quality={quality:.2f}, risk={risk:.2f}",
                adjustment_strategy={}
            )

        elif domain == EPDomain.ATTENTION:
            atp_available = context.get("atp_available", 0.0)
            atp_cost = context.get("atp_cost", 0.0)
            atp_reserve = context.get("atp_reserve_needed", 20.0)

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

            return EPPrediction(
                domain=domain,
                outcome_probability=1.0 - severity,
                confidence=0.75,
                severity=severity,
                recommendation=rec,
                reasoning=f"Heuristic: ATP {atp_available:.1f} → {atp_after:.1f} (reserve={atp_reserve})",
                adjustment_strategy={}
            )

        # Fallback
        return EPPrediction(
            domain=domain,
            outcome_probability=0.5,
            confidence=0.5,
            severity=0.5,
            recommendation="proceed",
            reasoning="Heuristic: unknown domain",
            adjustment_strategy={}
        )

    def _score_assessment(self, assessment: Dict[str, Any]) -> float:
        """Score an EP assessment (higher is better)."""
        decision = assessment["coordinated_decision"]

        # Prefer "proceed" (confident), then "adjust" (cautious), then "defer" (conservative)
        final_decision = decision.get("final_decision", "defer")
        confidence = decision.get("confidence", 0.0)

        if final_decision == "proceed":
            base_score = 1.0
        elif final_decision == "adjust":
            base_score = 0.7
        else:  # defer
            base_score = 0.3

        return base_score * confidence

    def record_outcome(
        self,
        life_id: str,
        tick: int,
        contexts: Dict[EPDomain, Dict[str, Any]],
        predictions: Dict[EPDomain, EPPrediction],
        action_taken: Dict[str, Any],
        outcome: Dict[str, Any]
    ) -> None:
        """
        Record interaction outcome as pattern for learning.

        This is how the EP system learns from experience and matures over time.
        """
        timestamp = datetime.now().isoformat()

        for domain in [EPDomain.EMOTIONAL, EPDomain.QUALITY, EPDomain.ATTENTION]:
            if domain not in contexts or domain not in predictions:
                continue

            # Create pattern from this interaction
            pattern = InteractionPattern(
                pattern_id=f"{life_id}_tick{tick}_{str(domain).split('.')[-1].lower()}",
                life_id=life_id,
                tick=tick,
                domain=domain,
                context=contexts[domain],
                prediction={
                    "outcome_probability": predictions[domain].outcome_probability,
                    "confidence": predictions[domain].confidence,
                    "severity": predictions[domain].severity,
                    "recommendation": predictions[domain].recommendation,
                },
                outcome=outcome,
                timestamp=timestamp
            )

            # Add to domain's pattern matcher
            self.matchers[domain].add_pattern(pattern)

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

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get current learning statistics."""
        total_patterns = sum(len(m.patterns) for m in self.matchers.values())
        pattern_rate = self.pattern_predictions / max(1, self.prediction_count)

        return {
            "total_patterns": total_patterns,
            "patterns_by_domain": {
                str(domain): len(matcher.patterns)
                for domain, matcher in self.matchers.items()
            },
            "prediction_count": self.prediction_count,
            "pattern_predictions": self.pattern_predictions,
            "heuristic_predictions": self.heuristic_predictions,
            "pattern_rate": pattern_rate,
            "maturation_stage": self._determine_maturation_stage()
        }


# ============================================================================
# Integration Function (compatible with closed_loop_multi_life.py)
# ============================================================================

def run_ep_policy_once(
    life_summary: Dict[str, Any],
    agent: Agent,
    world: World,
    policy: Optional[EPDrivenPolicy] = None
) -> Dict[str, Any]:
    """
    Run EP-driven policy once (compatible with closed_loop_multi_life.py).

    This is a drop-in replacement for `research_agent_driver::run_policy_once`.
    """

    if policy is None:
        policy = EPDrivenPolicy()

    life_id = life_summary.get("life_id", "unknown")

    result = policy.propose_action(agent, world, life_id)

    return {
        "proposed_action": result["proposed_action"],
        "ep_assessment": result["ep_assessment"],
        "learning_stats": policy.get_learning_stats()
    }


# ============================================================================
# Pattern Corpus Loader (Thor's Sessions 144-145)
# ============================================================================

class ThorPatternCorpusLoader:
    """Loads Thor's 100-pattern corpus organized by domain."""

    @staticmethod
    def load_domain_patterns(hrm_path: Path, domain: EPDomain) -> List[InteractionPattern]:
        """Load patterns for a specific domain from Thor's corpus."""
        domain_name = str(domain).split(".")[-1].lower()  # EPDomain.EMOTIONAL -> "emotional"
        pattern_file = hrm_path / "sage" / "experiments" / "ep_patterns_by_domain" / f"{domain_name}_ep_patterns.json"

        if not pattern_file.exists():
            return []

        with open(pattern_file, 'r') as f:
            data = json.load(f)

        patterns = []
        for p in data.get("patterns", []):
            # Convert Thor's pattern format to InteractionPattern
            pattern = InteractionPattern(
                pattern_id=f"thor_{p['scenario_id']}",
                life_id="thor_corpus",  # From Thor's corpus, not a specific life
                tick=0,
                domain=domain,
                context=p["context"].get(domain_name, {}),
                prediction=p["ep_predictions"].get(domain_name, {}),
                outcome={
                    "final_decision": p["coordinated_decision"]["final_decision"],
                    "success": p.get("outcome", {}).get("success", True)
                },
                timestamp=p.get("timestamp", "")
            )
            patterns.append(pattern)

        return patterns

    @staticmethod
    def load_all_patterns(hrm_path: Path) -> Dict[EPDomain, List[InteractionPattern]]:
        """Load all patterns from Thor's corpus."""
        patterns_by_domain = {}

        for domain in [EPDomain.EMOTIONAL, EPDomain.QUALITY, EPDomain.ATTENTION]:
            patterns = ThorPatternCorpusLoader.load_domain_patterns(hrm_path, domain)
            patterns_by_domain[domain] = patterns

        return patterns_by_domain


def create_policy_with_thor_patterns(hrm_path: Optional[Path] = None) -> EPDrivenPolicy:
    """
    Create EP-driven policy pre-loaded with Thor's pattern corpus.

    This creates a LEARNING-stage policy (vs IMMATURE with 0 patterns).
    """
    if hrm_path is None:
        # Default: HRM repo location relative to web4
        hrm_path = Path(__file__).parent.parent.parent / "HRM"

    policy = EPDrivenPolicy()

    # Load Thor's patterns
    patterns_by_domain = ThorPatternCorpusLoader.load_all_patterns(hrm_path)

    # Add to policy's matchers
    for domain, patterns in patterns_by_domain.items():
        for pattern in patterns:
            policy.matchers[domain].add_pattern(pattern)

    return policy


def create_policy_with_web4_patterns(web4_pattern_path: Optional[Path] = None) -> EPDrivenPolicy:
    """
    Create EP-driven policy pre-loaded with Web4-native ATP pattern corpus.

    Session 116: Web4-native patterns generated to address Session 115's
    finding that Thor's SAGE patterns don't transfer to ATP management.

    This creates a LEARNING-stage policy with domain-specific patterns.

    Args:
        web4_pattern_path: Path to ep_pattern_corpus_web4_native.json
                          Defaults to web4/game/ep_pattern_corpus_web4_native.json
    """
    if web4_pattern_path is None:
        # Default: web4/game/ep_pattern_corpus_web4_native.json
        web4_pattern_path = Path(__file__).parent / "ep_pattern_corpus_web4_native.json"

    if not web4_pattern_path.exists():
        raise FileNotFoundError(f"Web4 pattern corpus not found: {web4_pattern_path}")

    policy = EPDrivenPolicy()

    # Load Web4 patterns
    with open(web4_pattern_path, 'r') as f:
        corpus_data = json.load(f)

    patterns_list = corpus_data.get("patterns", [])

    # Convert Web4 patterns to EPPattern format and add to policy
    for web4_pattern in patterns_list:
        # Web4 patterns already have the right structure (context + ep_predictions + outcome)
        # Convert to EPPattern for each domain prediction

        context = web4_pattern.get("context", {})
        ep_predictions = web4_pattern.get("ep_predictions", {})
        outcome = web4_pattern.get("outcome", {})

        # Create EPPattern for each domain that has a prediction
        for domain_str in ["emotional", "quality", "attention"]:
            if domain_str not in ep_predictions:
                continue

            prediction = ep_predictions[domain_str]

            # Map domain string to EPDomain enum
            if domain_str == "emotional":
                domain = EPDomain.EMOTIONAL
            elif domain_str == "quality":
                domain = EPDomain.QUALITY
            elif domain_str == "attention":
                domain = EPDomain.ATTENTION
            else:
                continue

            # Create InteractionPattern
            ep_pattern = InteractionPattern(
                pattern_id=web4_pattern.get("pattern_id", f"web4_{domain_str}_unknown"),
                life_id="web4_corpus",  # Mark as coming from Web4 corpus
                tick=0,  # Pre-generated patterns don't have tick
                domain=domain,
                context=context.get(domain_str, {}),  # Get domain-specific context
                prediction={
                    "outcome_probability": prediction.get("outcome_probability", 0.5),
                    "confidence": prediction.get("confidence", 0.5),
                    "severity": prediction.get("severity", 0.5),
                    "recommendation": prediction.get("recommendation", "adjust"),
                    "reasoning": prediction.get("reasoning", "Web4-native pattern")
                },
                outcome={
                    "success": outcome.get("success", False),
                    "atp_before": outcome.get("atp_before", 0.0),
                    "atp_after": outcome.get("atp_after", 0.0),
                    "t3_before": outcome.get("t3_before", 0.0),
                    "t3_after": outcome.get("t3_after", 0.0),
                    "survived": outcome.get("survived", True)
                },
                timestamp=web4_pattern.get("timestamp", "2026-01-01T00:00:00")
            )

            # Add to appropriate matcher
            policy.matchers[domain].add_pattern(ep_pattern)

    # Log loaded patterns
    total_loaded = sum(len(matcher.patterns) for matcher in policy.matchers.values())
    print(f"[Web4 Patterns] Loaded {total_loaded} Web4-native patterns")
    for domain, matcher in policy.matchers.items():
        print(f"  {domain.name}: {len(matcher.patterns)} patterns")

    return policy


if __name__ == "__main__":
    print("EP-Driven Policy for Web4 Closed-Loop Multi-Life")
    print("=" * 80)
    print("\nThis module provides EP-based action proposals with pattern learning.")
    print("\nIntegration:")
    print("  from ep_driven_policy import run_ep_policy_once, EPDrivenPolicy")
    print("  from ep_driven_policy import create_policy_with_thor_patterns")
    print("\nSession 114-115: Learning EP + Closed-Loop Policy + Thor's Patterns")
