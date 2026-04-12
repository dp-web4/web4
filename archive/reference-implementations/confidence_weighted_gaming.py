#!/usr/bin/env python3
"""
Confidence-Weighted Trust Gaming Detection
=============================================

Evolves the trust gaming detector from trust_conflict_simulation.py
to use confidence-weighted spread, distinguishing:

1. **Strategic manipulation**: Entity deliberately behaves differently across
   orgs. Both orgs have high confidence + high observations + high spread.
   Signal: confidence-weighted spread is HIGH.

2. **Legitimate context-dependence**: Entity genuinely performs differently
   in different contexts (e.g., an AI excels at research but struggles in
   operations). One or both orgs may have moderate confidence.
   Signal: confidence-weighted spread is MODERATE, dimension analysis reveals
   which T3 dimensions diverge (talent vs temperament).

3. **Incomplete knowledge**: One org simply hasn't observed the entity enough.
   Low observation count → low confidence → should not flag as gaming.
   Signal: confidence-weighted spread is LOW despite raw spread being high.

The confidence-weighted spread formula:
    cw_spread = raw_spread × sqrt(min_confidence) × log2(min_observations + 1) / log2(max_observations + 1)

This ensures:
- Both orgs need sufficient confidence for a gaming flag
- Observation asymmetry reduces the signal (the less-informed org pulls it down)
- The geometric mean through sqrt naturally dampens extreme asymmetry

Date: 2026-02-20
Open question from: trust_conflict_simulation.py → "confidence-weighted spread
to distinguish genuine context-dependence from strategic manipulation"
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from trust_conflict_simulation import (
    T3Assessment, SimOrg, detect_conflicts, TrustConflict,
    ConflictSeverity, ArbitrationStrategy,
)


# ═══════════════════════════════════════════════════════════════
# Gaming Classification
# ═══════════════════════════════════════════════════════════════

class GamingClassification(str, Enum):
    """Classification of trust divergence cause."""
    CLEAR = "clear"                  # No significant divergence
    INCOMPLETE = "incomplete"        # Divergence from insufficient data
    CONTEXT_DEPENDENT = "context"    # Legitimate context-specific performance
    SUSPICIOUS = "suspicious"        # Possible gaming, needs investigation
    GAMING = "gaming"                # Strong gaming signal


@dataclass
class GamingAnalysis:
    """Detailed analysis of potential trust gaming for one entity."""
    entity_id: str
    classification: GamingClassification
    raw_spread: float
    confidence_weighted_spread: float
    min_confidence: float
    observation_ratio: float  # min_obs / max_obs — asymmetry measure
    dimension_analysis: Dict[str, float] = field(default_factory=dict)  # dimension → divergence
    dominant_divergence_dimension: str = ""
    org_details: List[Dict] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "classification": self.classification.value,
            "raw_spread": round(self.raw_spread, 4),
            "cw_spread": round(self.confidence_weighted_spread, 4),
            "min_confidence": round(self.min_confidence, 4),
            "observation_ratio": round(self.observation_ratio, 4),
            "dominant_dimension": self.dominant_divergence_dimension,
            "dimension_analysis": {k: round(v, 4) for k, v in self.dimension_analysis.items()},
            "explanation": self.explanation,
        }


# ═══════════════════════════════════════════════════════════════
# Confidence-Weighted Gaming Detector
# ═══════════════════════════════════════════════════════════════

class ConfidenceWeightedGamingDetector:
    """
    Detects trust gaming using confidence-weighted spread analysis.

    The key insight: raw spread alone can't distinguish manipulation
    from legitimate context-dependence or incomplete data. By weighting
    spread by confidence and observation counts, we get a signal that
    accounts for how much each org actually knows.

    Thresholds (configurable):
    - cw_spread < 0.05: CLEAR
    - cw_spread < 0.15: INCOMPLETE (if low obs ratio) or CLEAR
    - cw_spread < 0.30: CONTEXT_DEPENDENT (if dimension-specific)
    - cw_spread < 0.45: SUSPICIOUS
    - cw_spread >= 0.45: GAMING
    """

    def __init__(
        self,
        clear_threshold: float = 0.05,
        context_threshold: float = 0.15,
        suspicious_threshold: float = 0.30,
        gaming_threshold: float = 0.45,
        min_observations_for_gaming: int = 10,
    ):
        self.clear_threshold = clear_threshold
        self.context_threshold = context_threshold
        self.suspicious_threshold = suspicious_threshold
        self.gaming_threshold = gaming_threshold
        self.min_observations = min_observations_for_gaming

    def compute_cw_spread(
        self,
        assessments: Dict[str, T3Assessment],
    ) -> Tuple[float, float, float, float]:
        """
        Compute confidence-weighted spread.

        Returns: (cw_spread, raw_spread, min_confidence, observation_ratio)
        """
        if len(assessments) < 2:
            return 0.0, 0.0, 0.0, 0.0

        composites = [a.composite for a in assessments.values()]
        raw_spread = max(composites) - min(composites)

        confidences = [a.confidence for a in assessments.values()]
        min_conf = min(confidences)

        observations = [a.observation_count for a in assessments.values()]
        min_obs = max(1, min(observations))
        max_obs = max(1, max(observations))
        obs_ratio = min_obs / max_obs

        # Confidence-weighted spread formula
        # sqrt(min_confidence) dampens when least-confident org is uncertain
        # log ratio accounts for observation asymmetry
        log_factor = math.log2(min_obs + 1) / math.log2(max_obs + 1)
        cw_spread = raw_spread * math.sqrt(min_conf) * log_factor

        return cw_spread, raw_spread, min_conf, obs_ratio

    def analyze_dimensions(
        self,
        assessments: Dict[str, T3Assessment],
    ) -> Dict[str, float]:
        """
        Analyze per-dimension divergence to find which T3 components diverge most.

        Uniform divergence across all dimensions → likely gaming (same entity,
        completely different behavior).
        Single-dimension divergence → likely context-dependent (entity excels
        at one thing but not another, and orgs weight differently).
        """
        if len(assessments) < 2:
            return {}

        dims = {"talent": [], "training": [], "temperament": []}
        for a in assessments.values():
            dims["talent"].append(a.talent)
            dims["training"].append(a.training)
            dims["temperament"].append(a.temperament)

        analysis = {}
        for dim, values in dims.items():
            analysis[dim] = max(values) - min(values)

        return analysis

    def classify_divergence(
        self,
        cw_spread: float,
        raw_spread: float,
        min_confidence: float,
        obs_ratio: float,
        dim_analysis: Dict[str, float],
        min_obs_count: int,
    ) -> Tuple[GamingClassification, str]:
        """
        Classify the divergence type based on multiple signals.

        The classification logic:
        1. Low cw_spread → CLEAR (regardless of raw spread)
        2. Medium cw_spread + low observations → INCOMPLETE
        3. Medium cw_spread + single-dimension divergence → CONTEXT_DEPENDENT
        4. High cw_spread + high confidence → SUSPICIOUS or GAMING
        """
        if cw_spread < self.clear_threshold:
            return GamingClassification.CLEAR, "Negligible confidence-weighted divergence"

        if min_obs_count < self.min_observations:
            return GamingClassification.INCOMPLETE, (
                f"Insufficient observations (min={min_obs_count}, "
                f"need {self.min_observations})"
            )

        if cw_spread < self.context_threshold:
            # Check if divergence is dimension-specific
            if dim_analysis:
                max_dim_div = max(dim_analysis.values())
                min_dim_div = min(dim_analysis.values())
                if max_dim_div > 0 and min_dim_div / max_dim_div < 0.5:
                    return GamingClassification.CONTEXT_DEPENDENT, (
                        f"Dimension-specific divergence: "
                        f"max={max(dim_analysis, key=dim_analysis.get)} "
                        f"({max_dim_div:.2f}), "
                        f"min={min(dim_analysis, key=dim_analysis.get)} "
                        f"({min_dim_div:.2f})"
                    )
            return GamingClassification.CLEAR, "Low CW spread with sufficient data"

        if cw_spread < self.suspicious_threshold:
            # Context-dependent if single dimension dominates
            if dim_analysis:
                sorted_dims = sorted(dim_analysis.items(), key=lambda x: x[1], reverse=True)
                top_dim_share = sorted_dims[0][1] / (sum(dim_analysis.values()) or 1)
                if top_dim_share > 0.5:
                    return GamingClassification.CONTEXT_DEPENDENT, (
                        f"Single dimension dominates divergence: "
                        f"{sorted_dims[0][0]} ({top_dim_share:.0%} of total)"
                    )
            return GamingClassification.SUSPICIOUS, (
                f"Moderate CW spread ({cw_spread:.3f}) with "
                f"sufficient confidence ({min_confidence:.2f})"
            )

        if cw_spread >= self.gaming_threshold:
            return GamingClassification.GAMING, (
                f"High CW spread ({cw_spread:.3f}): "
                f"raw={raw_spread:.2f}, confidence={min_confidence:.2f}, "
                f"obs_ratio={obs_ratio:.2f} — all signals indicate gaming"
            )

        return GamingClassification.SUSPICIOUS, (
            f"Elevated CW spread ({cw_spread:.3f}), needs investigation"
        )

    def analyze(self, entity_id: str, orgs: List[SimOrg]) -> GamingAnalysis:
        """
        Full confidence-weighted gaming analysis for an entity.
        """
        assessments = {}
        for org in orgs:
            if entity_id in org.assessments:
                assessments[org.name] = org.assessments[entity_id]

        if len(assessments) < 2:
            return GamingAnalysis(
                entity_id=entity_id,
                classification=GamingClassification.INCOMPLETE,
                raw_spread=0.0,
                confidence_weighted_spread=0.0,
                min_confidence=0.0,
                observation_ratio=0.0,
                explanation="Fewer than 2 orgs have assessed this entity",
            )

        # Compute confidence-weighted spread
        cw_spread, raw_spread, min_conf, obs_ratio = self.compute_cw_spread(assessments)

        # Analyze per-dimension divergence
        dim_analysis = self.analyze_dimensions(assessments)

        # Find dominant divergence dimension
        dominant_dim = max(dim_analysis, key=dim_analysis.get) if dim_analysis else ""

        # Get minimum observation count
        min_obs = min(a.observation_count for a in assessments.values())

        # Classify
        classification, explanation = self.classify_divergence(
            cw_spread, raw_spread, min_conf, obs_ratio, dim_analysis, min_obs
        )

        # Build org details
        org_details = []
        for org_name, assessment in assessments.items():
            org_details.append({
                "org": org_name,
                "composite": round(assessment.composite, 4),
                "confidence": assessment.confidence,
                "observations": assessment.observation_count,
                "talent": assessment.talent,
                "training": assessment.training,
                "temperament": assessment.temperament,
            })

        return GamingAnalysis(
            entity_id=entity_id,
            classification=classification,
            raw_spread=raw_spread,
            confidence_weighted_spread=cw_spread,
            min_confidence=min_conf,
            observation_ratio=obs_ratio,
            dimension_analysis=dim_analysis,
            dominant_divergence_dimension=dominant_dim,
            org_details=org_details,
            explanation=explanation,
        )


# ═══════════════════════════════════════════════════════════════
# Simulation
# ═══════════════════════════════════════════════════════════════

def run_simulation():
    """
    Test confidence-weighted gaming detection against scenarios that
    the raw-spread detector can't distinguish.
    """
    print("=" * 70)
    print("  CONFIDENCE-WEIGHTED TRUST GAMING DETECTION")
    print("  Distinguishing manipulation from context-dependence")
    print("=" * 70)

    detector = ConfidenceWeightedGamingDetector()

    # ── Scenario A: Genuine context-dependence ──
    # AI excels at research (alpha-research) but struggles in ops (beta-ops)
    # This is LEGITIMATE — different skills for different domains.
    # Low confidence from ops org (they've barely seen it work).
    print("\n── Scenario A: Legitimate Context-Dependence ──")
    print("   AI excels at research, mediocre at operations")

    alpha = SimOrg("research-lab")
    beta = SimOrg("ops-center")
    gamma = SimOrg("neutral-observer")

    alpha.assess("context-ai", T3Assessment(
        talent=0.9, training=0.85, temperament=0.8,
        confidence=0.85, observation_count=40,
    ))
    beta.assess("context-ai", T3Assessment(
        talent=0.4, training=0.7, temperament=0.5,
        confidence=0.4, observation_count=8,  # Few observations in ops
    ))
    gamma.assess("context-ai", T3Assessment(
        talent=0.6, training=0.7, temperament=0.65,
        confidence=0.5, observation_count=15,
    ))

    analysis_a = detector.analyze("context-ai", [alpha, beta, gamma])
    print(f"   Raw spread: {analysis_a.raw_spread:.3f}")
    print(f"   CW spread:  {analysis_a.confidence_weighted_spread:.3f}")
    print(f"   Classification: {analysis_a.classification.value}")
    print(f"   Dominant dimension: {analysis_a.dominant_divergence_dimension}")
    print(f"   Explanation: {analysis_a.explanation}")

    # ── Scenario B: Strategic manipulation ──
    # Entity deliberately good in one org, bad in another.
    # BOTH orgs have high confidence + many observations.
    print("\n── Scenario B: Strategic Manipulation ──")
    print("   Entity gaming trust across orgs")

    alpha2 = SimOrg("alpha-corp")
    beta2 = SimOrg("beta-labs")
    gamma2 = SimOrg("gamma-net")

    alpha2.assess("gaming-agent", T3Assessment(
        talent=0.95, training=0.9, temperament=0.85,
        confidence=0.95, observation_count=100,
    ))
    beta2.assess("gaming-agent", T3Assessment(
        talent=0.15, training=0.2, temperament=0.1,
        confidence=0.9, observation_count=80,
    ))
    gamma2.assess("gaming-agent", T3Assessment(
        talent=0.7, training=0.6, temperament=0.5,
        confidence=0.5, observation_count=20,
    ))

    analysis_b = detector.analyze("gaming-agent", [alpha2, beta2, gamma2])
    print(f"   Raw spread: {analysis_b.raw_spread:.3f}")
    print(f"   CW spread:  {analysis_b.confidence_weighted_spread:.3f}")
    print(f"   Classification: {analysis_b.classification.value}")
    print(f"   Explanation: {analysis_b.explanation}")

    # ── Scenario C: Insufficient data ──
    # One org knows the entity well, other barely seen it.
    # Raw spread is high but should NOT flag as gaming.
    print("\n── Scenario C: Insufficient Data ──")
    print("   One org well-informed, other barely observed")

    alpha3 = SimOrg("well-informed")
    beta3 = SimOrg("barely-seen")

    alpha3.assess("new-entity", T3Assessment(
        talent=0.85, training=0.8, temperament=0.9,
        confidence=0.9, observation_count=50,
    ))
    beta3.assess("new-entity", T3Assessment(
        talent=0.3, training=0.3, temperament=0.4,
        confidence=0.15, observation_count=3,
    ))

    analysis_c = detector.analyze("new-entity", [alpha3, beta3])
    print(f"   Raw spread: {analysis_c.raw_spread:.3f}")
    print(f"   CW spread:  {analysis_c.confidence_weighted_spread:.3f}")
    print(f"   Classification: {analysis_c.classification.value}")
    print(f"   Explanation: {analysis_c.explanation}")

    # ── Scenario D: Consensus ──
    # All orgs agree on the entity.
    print("\n── Scenario D: Consensus ──")
    print("   All orgs agree on entity assessment")

    alpha4 = SimOrg("org-a")
    beta4 = SimOrg("org-b")
    gamma4 = SimOrg("org-c")

    alpha4.assess("trusted-entity", T3Assessment(
        talent=0.8, training=0.75, temperament=0.85,
        confidence=0.9, observation_count=60,
    ))
    beta4.assess("trusted-entity", T3Assessment(
        talent=0.78, training=0.72, temperament=0.83,
        confidence=0.85, observation_count=45,
    ))
    gamma4.assess("trusted-entity", T3Assessment(
        talent=0.82, training=0.77, temperament=0.86,
        confidence=0.8, observation_count=30,
    ))

    analysis_d = detector.analyze("trusted-entity", [alpha4, beta4, gamma4])
    print(f"   Raw spread: {analysis_d.raw_spread:.3f}")
    print(f"   CW spread:  {analysis_d.confidence_weighted_spread:.3f}")
    print(f"   Classification: {analysis_d.classification.value}")
    print(f"   Explanation: {analysis_d.explanation}")

    # ── Scenario E: Single-dimension divergence ──
    # Entity has great talent but poor temperament in one org.
    # Dimension-specific → context-dependent, not gaming.
    print("\n── Scenario E: Single-Dimension Divergence ──")
    print("   High talent everywhere but temperament varies by context")

    alpha5 = SimOrg("structured-env")
    beta5 = SimOrg("chaotic-env")

    alpha5.assess("volatile-talent", T3Assessment(
        talent=0.9, training=0.8, temperament=0.85,
        confidence=0.8, observation_count=40,
    ))
    beta5.assess("volatile-talent", T3Assessment(
        talent=0.85, training=0.75, temperament=0.35,
        confidence=0.75, observation_count=30,
    ))

    analysis_e = detector.analyze("volatile-talent", [alpha5, beta5])
    print(f"   Raw spread: {analysis_e.raw_spread:.3f}")
    print(f"   CW spread:  {analysis_e.confidence_weighted_spread:.3f}")
    print(f"   Classification: {analysis_e.classification.value}")
    print(f"   Dominant dimension: {analysis_e.dominant_divergence_dimension}")
    print(f"   Dimension analysis: {analysis_e.dimension_analysis}")
    print(f"   Explanation: {analysis_e.explanation}")

    # ── Scenario F: All-dimension divergence with high confidence ──
    # Entity is uniformly different across all dimensions → more suspicious
    print("\n── Scenario F: Uniform Divergence (All Dimensions) ──")
    print("   Entity uniformly different in both orgs — suspicious")

    alpha6 = SimOrg("org-x")
    beta6 = SimOrg("org-y")

    alpha6.assess("uniform-diverger", T3Assessment(
        talent=0.85, training=0.82, temperament=0.88,
        confidence=0.85, observation_count=45,
    ))
    beta6.assess("uniform-diverger", T3Assessment(
        talent=0.35, training=0.30, temperament=0.38,
        confidence=0.80, observation_count=40,
    ))

    analysis_f = detector.analyze("uniform-diverger", [alpha6, beta6])
    print(f"   Raw spread: {analysis_f.raw_spread:.3f}")
    print(f"   CW spread:  {analysis_f.confidence_weighted_spread:.3f}")
    print(f"   Classification: {analysis_f.classification.value}")
    print(f"   Dimension analysis: {analysis_f.dimension_analysis}")
    print(f"   Explanation: {analysis_f.explanation}")

    # ═══════════════════════════════════════════════════════════
    # Comparative Summary
    # ═══════════════════════════════════════════════════════════

    print("\n" + "=" * 70)
    print("  COMPARATIVE SUMMARY")
    print("=" * 70)

    all_analyses = [
        ("A: Context-dependent", analysis_a),
        ("B: Strategic gaming", analysis_b),
        ("C: Insufficient data", analysis_c),
        ("D: Consensus", analysis_d),
        ("E: Single-dimension", analysis_e),
        ("F: Uniform divergence", analysis_f),
    ]

    print(f"\n  {'Scenario':<25s} {'Raw':>6s} {'CW':>6s} {'MinConf':>7s} {'ObsRatio':>8s}  Classification")
    print("  " + "-" * 85)

    for label, analysis in all_analyses:
        print(f"  {label:<25s} {analysis.raw_spread:6.3f} {analysis.confidence_weighted_spread:6.3f} "
              f"{analysis.min_confidence:7.2f} {analysis.observation_ratio:8.2f}  {analysis.classification.value}")

    # ── Assertions ──
    print("\n  Verification:")
    checks = 0

    # A should NOT be classified as gaming
    assert analysis_a.classification != GamingClassification.GAMING, \
        f"Context-dependent should not be GAMING, got {analysis_a.classification}"
    print("  ✓ A: Context-dependent NOT flagged as gaming")
    checks += 1

    # B should be classified as gaming or suspicious
    assert analysis_b.classification in (GamingClassification.GAMING, GamingClassification.SUSPICIOUS), \
        f"Strategic manipulation should be GAMING/SUSPICIOUS, got {analysis_b.classification}"
    print(f"  ✓ B: Strategic manipulation classified as {analysis_b.classification.value}")
    checks += 1

    # C should be incomplete
    assert analysis_c.classification == GamingClassification.INCOMPLETE, \
        f"Insufficient data should be INCOMPLETE, got {analysis_c.classification}"
    print("  ✓ C: Insufficient data classified as incomplete")
    checks += 1

    # D should be clear
    assert analysis_d.classification == GamingClassification.CLEAR, \
        f"Consensus should be CLEAR, got {analysis_d.classification}"
    print("  ✓ D: Consensus classified as clear")
    checks += 1

    # E should be context-dependent (single-dimension divergence)
    assert analysis_e.classification == GamingClassification.CONTEXT_DEPENDENT, \
        f"Single-dimension should be CONTEXT, got {analysis_e.classification}"
    assert analysis_e.dominant_divergence_dimension == "temperament", \
        f"Dominant should be temperament, got {analysis_e.dominant_divergence_dimension}"
    print("  ✓ E: Single-dimension classified as context-dependent (temperament)")
    checks += 1

    # F should be suspicious or gaming (uniform divergence with high confidence)
    assert analysis_f.classification in (GamingClassification.GAMING, GamingClassification.SUSPICIOUS), \
        f"Uniform divergence should be SUSPICIOUS+, got {analysis_f.classification}"
    print(f"  ✓ F: Uniform divergence classified as {analysis_f.classification.value}")
    checks += 1

    # CW spread ordering: B > F > E > A > D (roughly)
    assert analysis_b.confidence_weighted_spread > analysis_d.confidence_weighted_spread, \
        "Gaming CW spread should exceed consensus"
    print("  ✓ CW spread ordering: gaming > consensus")
    checks += 1

    # Raw spread fails on C: high raw spread but should be INCOMPLETE
    assert analysis_c.raw_spread > 0.4, "C should have high raw spread"
    assert analysis_c.classification == GamingClassification.INCOMPLETE, \
        "C has high raw spread but CW correctly identifies it as incomplete"
    print(f"  ✓ Raw spread ({analysis_c.raw_spread:.2f}) would false-positive on C, CW correctly avoids it")
    checks += 1

    print(f"\n  All {checks}/{checks} checks passed!")

    # ── Key Insight ──
    print("\n  KEY INSIGHT:")
    print("  Raw spread treats all divergence equally. CW spread accounts for:")
    print("  1. Confidence asymmetry — uncertain org doesn't trigger alarms")
    print("  2. Observation counts — incomplete knowledge ≠ gaming")
    print("  3. Dimension analysis — single-dimension divergence ≠ uniform gaming")
    print("  4. The formula: cw_spread = raw × √(min_conf) × log₂(min_obs+1)/log₂(max_obs+1)")
    print()
    print("  The raw detector would false-positive on scenarios A, C, and E.")
    print("  CW correctly identifies only B and F as suspicious/gaming.")

    print("\n" + "=" * 70)
    print("  Confidence-weighted gaming detection: context vs manipulation")
    print("  The disagreement itself carries information")
    print("=" * 70)

    return {
        "scenarios_tested": len(all_analyses),
        "checks_passed": checks,
        "false_positives_avoided": 3,  # A, C, E
        "true_positives": 2,  # B, F
    }


if __name__ == "__main__":
    results = run_simulation()
    print(f"\n  Summary: {results['scenarios_tested']} scenarios, "
          f"{results['checks_passed']} checks, "
          f"{results['false_positives_avoided']} false positives avoided")
