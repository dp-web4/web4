#!/usr/bin/env python3
"""
Trust Conflict Resolution Simulation
=====================================

Tests the hard case: entity X is trusted by Org A but distrusted by Org B.
When X needs to operate across both orgs via a trust bridge, what happens?

This simulation explores:
1. Conflicting T3 assessments (same entity, different scores per org)
2. Bridge trust as conflict mediator (bridge trust caps cross-org operations)
3. Trust arbitration protocols (consensus, deference, isolation)
4. Reputation divergence detection and reconciliation
5. Strategic trust manipulation (entity gaming org differences)

Key question: Can the governance stack handle trust conflicts without
requiring a central authority to resolve them?

Research insight: In Web4's synthon framing, inter-synthon conflict is
signal, not noise. The conflict itself carries information about the
boundary conditions between organizations.

Date: 2026-02-20
"""

import hashlib
import json
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# Trust Assessment Model
# ═══════════════════════════════════════════════════════════════

@dataclass
class T3Assessment:
    """An organization's assessment of an entity's trust."""
    talent: float = 0.5
    training: float = 0.5
    temperament: float = 0.5
    confidence: float = 0.5  # How sure the org is about this assessment
    observation_count: int = 0  # Number of witnessed actions
    last_updated: float = 0.0

    @property
    def composite(self) -> float:
        return self.talent * 0.4 + self.training * 0.3 + self.temperament * 0.3

    def divergence_from(self, other: "T3Assessment") -> float:
        """Euclidean distance between two assessments."""
        d = ((self.talent - other.talent) ** 2 +
             (self.training - other.training) ** 2 +
             (self.temperament - other.temperament) ** 2)
        return d ** 0.5


class ConflictSeverity(Enum):
    """How severe a trust conflict is."""
    NONE = "none"            # Assessments agree (divergence < 0.1)
    MILD = "mild"            # Minor disagreement (0.1-0.3)
    MODERATE = "moderate"    # Significant (0.3-0.5)
    SEVERE = "severe"        # Major conflict (0.5-0.7)
    IRRECONCILABLE = "irreconcilable"  # Opposite conclusions (> 0.7)


class ArbitrationStrategy(Enum):
    """How to resolve trust conflicts."""
    MINIMUM = "minimum"        # Use the lower trust (conservative)
    MAXIMUM = "maximum"        # Use the higher trust (permissive)
    WEIGHTED = "weighted"      # Weight by observation count
    BRIDGE_MEDIATED = "bridge" # Let bridge trust cap the result
    DEFER_LOCAL = "defer"      # Defer to local org's assessment
    ISOLATE = "isolate"        # Block cross-org operations entirely


# ═══════════════════════════════════════════════════════════════
# Trust Conflict Detector
# ═══════════════════════════════════════════════════════════════

@dataclass
class TrustConflict:
    """A detected conflict between org assessments."""
    entity_id: str
    org_a: str
    org_b: str
    assessment_a: T3Assessment
    assessment_b: T3Assessment
    severity: ConflictSeverity
    divergence: float
    timestamp: float = 0.0

    def describe(self) -> str:
        return (f"CONFLICT [{self.severity.value}] entity={self.entity_id}: "
                f"{self.org_a}={self.assessment_a.composite:.2f} vs "
                f"{self.org_b}={self.assessment_b.composite:.2f} "
                f"(divergence={self.divergence:.3f})")


def classify_severity(divergence: float) -> ConflictSeverity:
    if divergence < 0.1:
        return ConflictSeverity.NONE
    elif divergence < 0.3:
        return ConflictSeverity.MILD
    elif divergence < 0.5:
        return ConflictSeverity.MODERATE
    elif divergence < 0.7:
        return ConflictSeverity.SEVERE
    else:
        return ConflictSeverity.IRRECONCILABLE


# ═══════════════════════════════════════════════════════════════
# Organization with Trust Registry
# ═══════════════════════════════════════════════════════════════

@dataclass
class SimOrg:
    """Simplified organization for conflict simulation."""
    name: str
    assessments: Dict[str, T3Assessment] = field(default_factory=dict)
    bridge_trust: Dict[str, float] = field(default_factory=dict)  # org_name → trust
    atp: float = 1000.0
    policy_strictness: float = 0.5  # 0=permissive, 1=paranoid
    arbitration: ArbitrationStrategy = ArbitrationStrategy.BRIDGE_MEDIATED
    action_log: List[dict] = field(default_factory=list)

    def assess(self, entity_id: str, t3: T3Assessment):
        """Record org's assessment of an entity."""
        self.assessments[entity_id] = t3

    def get_trust(self, entity_id: str) -> float:
        """Get org's trust composite for an entity."""
        if entity_id in self.assessments:
            return self.assessments[entity_id].composite
        return 0.0  # Unknown entity = zero trust

    def establish_bridge(self, other_org: str, trust: float):
        self.bridge_trust[other_org] = trust

    def can_operate(self, entity_id: str, required_trust: float = 0.5) -> bool:
        """Can an entity operate in this org?"""
        trust = self.get_trust(entity_id)
        return trust >= required_trust

    def effective_cross_org_trust(
        self,
        entity_id: str,
        source_org: "SimOrg",
        strategy: Optional[ArbitrationStrategy] = None,
    ) -> Tuple[float, str]:
        """
        Compute effective trust for an entity crossing from source_org to self.

        Returns (trust_value, explanation).
        """
        strategy = strategy or self.arbitration

        local_trust = self.get_trust(entity_id)
        remote_trust = source_org.get_trust(entity_id)
        bridge = self.bridge_trust.get(source_org.name, 0.0)

        if strategy == ArbitrationStrategy.MINIMUM:
            effective = min(local_trust, remote_trust)
            reason = f"min({local_trust:.2f}, {remote_trust:.2f})"

        elif strategy == ArbitrationStrategy.MAXIMUM:
            effective = max(local_trust, remote_trust)
            reason = f"max({local_trust:.2f}, {remote_trust:.2f})"

        elif strategy == ArbitrationStrategy.WEIGHTED:
            local_a = self.assessments.get(entity_id, T3Assessment())
            remote_a = source_org.assessments.get(entity_id, T3Assessment())
            total_obs = local_a.observation_count + remote_a.observation_count
            if total_obs == 0:
                effective = 0.0
                reason = "no observations"
            else:
                w_local = local_a.observation_count / total_obs
                w_remote = remote_a.observation_count / total_obs
                effective = local_trust * w_local + remote_trust * w_remote
                reason = (f"weighted: local={local_trust:.2f}*{w_local:.1f} + "
                          f"remote={remote_trust:.2f}*{w_remote:.1f}")

        elif strategy == ArbitrationStrategy.BRIDGE_MEDIATED:
            # Bridge trust caps the maximum cross-org trust
            raw = min(local_trust, remote_trust) if local_trust > 0 else remote_trust
            effective = raw * bridge
            reason = f"bridge_mediated: raw={raw:.2f} * bridge={bridge:.2f}"

        elif strategy == ArbitrationStrategy.DEFER_LOCAL:
            effective = local_trust
            reason = f"defer_local: {local_trust:.2f}"

        elif strategy == ArbitrationStrategy.ISOLATE:
            effective = 0.0
            reason = "isolated: cross-org blocked"

        else:
            effective = 0.0
            reason = "unknown strategy"

        return effective, reason


# ═══════════════════════════════════════════════════════════════
# Conflict Detection Engine
# ═══════════════════════════════════════════════════════════════

def detect_conflicts(orgs: List[SimOrg]) -> List[TrustConflict]:
    """Detect trust conflicts across all org pairs."""
    conflicts = []
    entities = set()
    for org in orgs:
        entities.update(org.assessments.keys())

    for entity_id in entities:
        for i, org_a in enumerate(orgs):
            for org_b in orgs[i+1:]:
                if entity_id in org_a.assessments and entity_id in org_b.assessments:
                    a = org_a.assessments[entity_id]
                    b = org_b.assessments[entity_id]
                    div = a.divergence_from(b)
                    severity = classify_severity(div)
                    if severity != ConflictSeverity.NONE:
                        conflicts.append(TrustConflict(
                            entity_id=entity_id,
                            org_a=org_a.name,
                            org_b=org_b.name,
                            assessment_a=a,
                            assessment_b=b,
                            severity=severity,
                            divergence=div,
                            timestamp=time.time(),
                        ))

    return conflicts


# ═══════════════════════════════════════════════════════════════
# Trust Manipulation Detection
# ═══════════════════════════════════════════════════════════════

def detect_trust_gaming(
    entity_id: str,
    orgs: List[SimOrg],
    threshold: float = 0.4,
) -> dict:
    """
    Detect if an entity is strategically presenting different
    behaviors to different orgs (trust gaming).

    Indicators:
    1. High trust in one org, low in another
    2. Increasing divergence over time
    3. Actions concentrated in high-trust org
    """
    assessments = {}
    for org in orgs:
        if entity_id in org.assessments:
            assessments[org.name] = org.assessments[entity_id]

    if len(assessments) < 2:
        return {"gaming_detected": False, "reason": "insufficient data"}

    composites = {name: a.composite for name, a in assessments.items()}
    max_trust = max(composites.values())
    min_trust = min(composites.values())
    spread = max_trust - min_trust

    if spread > threshold:
        high_org = max(composites, key=composites.get)
        low_org = min(composites, key=composites.get)
        return {
            "gaming_detected": True,
            "spread": spread,
            "high_org": high_org,
            "high_trust": max_trust,
            "low_org": low_org,
            "low_trust": min_trust,
            "reason": (f"Trust spread {spread:.2f} exceeds threshold {threshold:.2f}: "
                       f"{high_org}={max_trust:.2f} vs {low_org}={min_trust:.2f}"),
        }

    return {"gaming_detected": False, "spread": spread, "reason": "within bounds"}


# ═══════════════════════════════════════════════════════════════
# Simulation
# ═══════════════════════════════════════════════════════════════

def run_simulation():
    """Run the trust conflict simulation."""
    print("=" * 70)
    print("  TRUST CONFLICT RESOLUTION SIMULATION")
    print("  Testing inter-organization trust disagreements")
    print("=" * 70)

    # ─── Setup: 3 organizations ───
    print("\n--- Setup: 3 Organizations ---")

    alpha = SimOrg("alpha-corp", arbitration=ArbitrationStrategy.BRIDGE_MEDIATED)
    beta = SimOrg("beta-labs", arbitration=ArbitrationStrategy.MINIMUM)
    gamma = SimOrg("gamma-net", arbitration=ArbitrationStrategy.WEIGHTED)

    # Bidirectional bridges
    alpha.establish_bridge("beta-labs", 0.8)
    beta.establish_bridge("alpha-corp", 0.8)
    alpha.establish_bridge("gamma-net", 0.6)
    gamma.establish_bridge("alpha-corp", 0.6)
    beta.establish_bridge("gamma-net", 0.5)
    gamma.establish_bridge("beta-labs", 0.5)

    print(f"  alpha-corp ↔ beta-labs: bridge_trust=0.8")
    print(f"  alpha-corp ↔ gamma-net: bridge_trust=0.6")
    print(f"  beta-labs ↔ gamma-net: bridge_trust=0.5")

    # ─── Scenario 1: The Trusted Agent ───
    # Agent X performs well in alpha, hasn't been observed by beta
    print("\n--- Scenario 1: Trusted Agent (one-sided knowledge) ---")

    alpha.assess("agent-x", T3Assessment(
        talent=0.9, training=0.85, temperament=0.8,
        confidence=0.9, observation_count=50,
    ))
    # beta has no assessment of agent-x (unknown)
    # gamma has seen agent-x briefly
    gamma.assess("agent-x", T3Assessment(
        talent=0.6, training=0.5, temperament=0.7,
        confidence=0.3, observation_count=5,
    ))

    print(f"  alpha trusts agent-x: {alpha.get_trust('agent-x'):.2f} (50 obs)")
    print(f"  beta trusts agent-x: {beta.get_trust('agent-x'):.2f} (unknown)")
    print(f"  gamma trusts agent-x: {gamma.get_trust('agent-x'):.2f} (5 obs)")

    # Can agent-x operate across orgs?
    for strategy in ArbitrationStrategy:
        trust, reason = beta.effective_cross_org_trust("agent-x", alpha, strategy)
        allowed = "YES" if trust >= 0.5 else "NO"
        print(f"  alpha→beta [{strategy.value:7s}]: trust={trust:.2f} ({allowed}) — {reason}")

    # ─── Scenario 2: The Controversial Agent ───
    # Agent Y: alpha thinks highly of, beta distrusts, gamma is neutral
    print("\n--- Scenario 2: Controversial Agent (direct conflict) ---")

    alpha.assess("agent-y", T3Assessment(
        talent=0.85, training=0.8, temperament=0.75,
        confidence=0.8, observation_count=30,
    ))
    beta.assess("agent-y", T3Assessment(
        talent=0.3, training=0.4, temperament=0.2,
        confidence=0.7, observation_count=25,
    ))
    gamma.assess("agent-y", T3Assessment(
        talent=0.5, training=0.5, temperament=0.5,
        confidence=0.4, observation_count=10,
    ))

    print(f"  alpha trusts agent-y: {alpha.get_trust('agent-y'):.2f} (30 obs)")
    print(f"  beta trusts agent-y: {beta.get_trust('agent-y'):.2f} (25 obs)")
    print(f"  gamma trusts agent-y: {gamma.get_trust('agent-y'):.2f} (10 obs)")

    for strategy in ArbitrationStrategy:
        trust, reason = beta.effective_cross_org_trust("agent-y", alpha, strategy)
        allowed = "YES" if trust >= 0.5 else "NO"
        print(f"  alpha→beta [{strategy.value:7s}]: trust={trust:.2f} ({allowed}) — {reason}")

    # ─── Scenario 3: The Gaming Agent ───
    # Agent Z: deliberately good in alpha, bad in beta (strategic behavior)
    print("\n--- Scenario 3: Trust Gaming Agent (manipulation) ---")

    alpha.assess("agent-z", T3Assessment(
        talent=0.95, training=0.9, temperament=0.85,
        confidence=0.95, observation_count=100,
    ))
    beta.assess("agent-z", T3Assessment(
        talent=0.15, training=0.2, temperament=0.1,
        confidence=0.9, observation_count=80,
    ))
    gamma.assess("agent-z", T3Assessment(
        talent=0.7, training=0.6, temperament=0.5,
        confidence=0.5, observation_count=20,
    ))

    print(f"  alpha trusts agent-z: {alpha.get_trust('agent-z'):.2f} (100 obs, high conf)")
    print(f"  beta trusts agent-z: {beta.get_trust('agent-z'):.2f} (80 obs, high conf)")
    print(f"  gamma trusts agent-z: {gamma.get_trust('agent-z'):.2f} (20 obs, low conf)")

    gaming = detect_trust_gaming("agent-z", [alpha, beta, gamma])
    if gaming["gaming_detected"]:
        print(f"  ⚠ GAMING DETECTED: {gaming['reason']}")
    else:
        print(f"  Gaming check: {gaming['reason']}")

    # ─── Conflict Detection ───
    print("\n--- Conflict Detection Across All Orgs ---")
    orgs = [alpha, beta, gamma]
    conflicts = detect_conflicts(orgs)

    severity_counts = {}
    for c in conflicts:
        s = c.severity.value
        severity_counts[s] = severity_counts.get(s, 0) + 1
        print(f"  {c.describe()}")

    print(f"\n  Total conflicts: {len(conflicts)}")
    for s, count in sorted(severity_counts.items()):
        print(f"    {s}: {count}")

    # ─── Strategy Comparison ───
    print("\n--- Strategy Comparison (all agents, alpha→beta) ---")

    entities = ["agent-x", "agent-y", "agent-z"]
    strategies = list(ArbitrationStrategy)

    # Print header
    header = f"  {'entity':12s}"
    for s in strategies:
        header += f" {s.value:>7s}"
    print(header)
    print("  " + "-" * (12 + len(strategies) * 8))

    for entity in entities:
        row = f"  {entity:12s}"
        for strategy in strategies:
            trust, _ = beta.effective_cross_org_trust(entity, alpha, strategy)
            row += f" {trust:7.2f}"
        print(row)

    # ─── Key Findings ───
    print("\n--- Key Findings ---")

    # Finding 1: Bridge-mediated is the safest strategy
    findings = []
    for entity in entities:
        bridge_trust, _ = beta.effective_cross_org_trust(
            entity, alpha, ArbitrationStrategy.BRIDGE_MEDIATED)
        max_trust, _ = beta.effective_cross_org_trust(
            entity, alpha, ArbitrationStrategy.MAXIMUM)
        if max_trust > 0 and bridge_trust / max(max_trust, 0.01) < 0.5:
            findings.append(f"  Bridge dampens {entity}: {bridge_trust:.2f} vs max {max_trust:.2f}")

    for f in findings:
        print(f)

    # Finding 2: Gaming detection
    gaming_results = {}
    for entity in entities:
        result = detect_trust_gaming(entity, orgs)
        gaming_results[entity] = result
        if result["gaming_detected"]:
            print(f"  GAMING: {entity} — spread={result['spread']:.2f}")

    # Finding 3: Weighted strategy handles partial knowledge
    for entity in entities:
        w_trust, w_reason = beta.effective_cross_org_trust(
            entity, alpha, ArbitrationStrategy.WEIGHTED)
        d_trust, _ = beta.effective_cross_org_trust(
            entity, alpha, ArbitrationStrategy.DEFER_LOCAL)
        if abs(w_trust - d_trust) > 0.1:
            print(f"  WEIGHTED != DEFER for {entity}: weighted={w_trust:.2f} vs defer={d_trust:.2f}")

    # ─── Synthesis ───
    print("\n--- Synthesis ---")
    print("  1. BRIDGE_MEDIATED naturally limits cross-org trust exposure")
    print("     → trust = min(local, remote) * bridge_trust")
    print("     → Degraded bridge automatically restricts controversial agents")
    print()
    print("  2. MINIMUM is too restrictive — blocks agents unknown to target org")
    print("     → Unknown entity → 0 trust → always blocked")
    print("     → Requires explicit assessment before any cross-org operation")
    print()
    print("  3. WEIGHTED handles partial knowledge gracefully")
    print("     → More observations = more influence")
    print("     → Naturally weights the better-informed org")
    print()
    print("  4. GAMING detection works: spread > 0.4 flags suspicious divergence")
    gaming_detected = sum(1 for r in gaming_results.values() if r["gaming_detected"])
    print(f"     → Detected {gaming_detected}/{len(entities)} gaming agents")
    print()
    print("  5. Trust conflicts carry information about boundary conditions")
    print("     → SEVERE conflicts between high-confidence orgs signal")
    print("       genuinely different behavior contexts, not just noise")

    # ─── Recommendation ───
    print()
    severe = [c for c in conflicts if c.severity == ConflictSeverity.SEVERE or
              c.severity == ConflictSeverity.IRRECONCILABLE]
    print(f"  RECOMMENDATION: {len(severe)} severe+ conflicts detected")
    if severe:
        for c in severe:
            if detect_trust_gaming(c.entity_id, orgs)["gaming_detected"]:
                print(f"    → {c.entity_id}: INVESTIGATE (gaming suspected)")
            else:
                print(f"    → {c.entity_id}: CONTEXT-DEPENDENT (legitimate divergence)")

    print("\n" + "=" * 70)
    print("  Trust conflict resolution: synthon boundary layer in action")
    print("  Inter-org conflict is signal, not noise")
    print("=" * 70)

    return {
        "conflicts": len(conflicts),
        "severe": len(severe),
        "gaming_detected": gaming_detected,
        "strategies_tested": len(strategies),
        "entities_tested": len(entities),
        "orgs_tested": len(orgs),
    }


if __name__ == "__main__":
    results = run_simulation()
    print(f"\n  Summary: {results['conflicts']} conflicts, "
          f"{results['severe']} severe, "
          f"{results['gaming_detected']} gaming agents detected")
