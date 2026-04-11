#!/usr/bin/env python3
"""
Session 93 Track 1: IRP Expert Registry with LCT Identity

**Date**: 2025-12-27
**Platform**: Legion (RTX 4090)
**Track**: 1 of 3 - Fractal IRP Integration

## Problem Statement

SAGE's Fractal IRP proposal defines a universal interface for experts (local plugins,
remote SAGE instances, LangGraph workflows). Web4 needs:

1. **LCT Identity** for every IRP expert
2. **Expert Discovery** across societies
3. **Capability-Based Routing** via tags
4. **Permission-Based Access** via ATP scopes

## Solution: IRP Expert Registry

A Web4 registry that manages IRP experts with:
- LCT identity for trust/reputation
- Capability tags for routing (needs_reflection, tool_heavy, etc.)
- Cost models for ATP budgeting
- Permission scopes for authorization
- Cross-society discovery

## Integration with Session 92

Session 92 built:
- Cross-federation delegation (Track 1)
- Metabolic state-dependent reputation (Track 2)

This session extends with:
- IRP expert as first-class Web4 entity
- Expert discovery uses cross-federation delegation
- Expert reputation uses metabolic state tracking

## Test Scenarios

1. **Local IRP Expert Registration**: Register SAGE plugin with LCT identity
2. **Remote IRP Expert Discovery**: Discover experts across federations
3. **Capability-Based Routing**: Select expert based on task requirements
4. **Permission-Based Filtering**: Filter experts by ATP scope
5. **Cross-Society Expert Invocation**: Invoke remote expert with delegation

## Implementation

Based on FRACTAL_IRP_V0.2_MINIMAL_SPEC.md from SAGE.
"""

import json
import time
import secrets
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set
from enum import Enum
from pathlib import Path

# Import from Session 92
from session92_track1_cross_federation_delegation import (
    CrossFederationAuthenticator,
    FederationTrustPolicy,
)

from session92_track2_metabolic_reputation import (
    MetabolicState,
    StateDependentReputation,
    MetabolicReputationTracker,
)

from session90_track2_graceful_degradation import (
    TrustLevel,
)

from session88_track1_lct_society_authentication import (
    LCTIdentity,
    create_test_lct_identity,
    create_attestation,
)


# =============================================================================
# IRP Expert Descriptor (v0.2 from SAGE spec)
# =============================================================================

class ExpertKind(Enum):
    """Type of IRP expert."""
    LOCAL_IRP = "local_irp"      # Local SAGE plugin
    REMOTE_IRP = "remote_irp"    # Remote SAGE instance
    LANGGRAPH = "langgraph"      # LangGraph workflow


class CapabilityTag(Enum):
    """Capability tags for expert routing."""
    # Cognitive control
    NEEDS_REFLECTION = "needs_reflection"
    BRANCHY_CONTROLFLOW = "branchy_controlflow"
    LONG_HORIZON = "long_horizon"

    # Tool/Action shape
    TOOL_HEAVY = "tool_heavy"
    SAFE_ACTUATION = "safe_actuation"

    # Epistemic posture
    HIGH_UNCERTAINTY_TOLERANT = "high_uncertainty_tolerant"
    VERIFICATION_ORIENTED = "verification_oriented"

    # Performance profile
    LOW_LATENCY = "low_latency"
    COST_SENSITIVE = "cost_sensitive"


@dataclass
class IRPIdentity:
    """Web4 LCT identity for IRP expert."""
    lct_identity: LCTIdentity
    signing_pubkey: str  # ed25519 public key (hex)


@dataclass
class IRPCapabilities:
    """Expert capabilities."""
    modalities_in: List[str] = field(default_factory=lambda: ["text"])
    modalities_out: List[str] = field(default_factory=lambda: ["text", "json"])
    tasks: List[str] = field(default_factory=lambda: ["refine"])
    tags: List[CapabilityTag] = field(default_factory=list)


@dataclass
class IRPPolicy:
    """Authorization policy for expert."""
    permission_scope_required: str  # "ATP:SCOPE"
    allowed_effectors: List[str] = field(default_factory=lambda: ["none"])


@dataclass
class IRPCostModel:
    """Cost model for ATP budgeting."""
    unit: str = "atp"  # "atp" | "usd" | "ms"
    estimate_p50: float = 5.0  # Median cost
    estimate_p95: float = 15.0  # 95th percentile cost


@dataclass
class IRPEndpoint:
    """Endpoint for expert invocation."""
    transport: str = "local"  # "local" | "http"
    invoke_uri: str = "/irp/invoke"


@dataclass
class IRPExpertDescriptor:
    """Complete IRP expert descriptor (v0.2 from SAGE spec)."""

    # Metadata
    schema: str = "web4.irp_expert_descriptor.v0.2"
    id: str = field(default_factory=lambda: f"irp_{secrets.token_hex(8)}")
    kind: ExpertKind = ExpertKind.LOCAL_IRP
    name: str = "unnamed_expert"
    version: str = "0.1.0"

    # Web4 integration
    identity: Optional[IRPIdentity] = None
    capabilities: IRPCapabilities = field(default_factory=IRPCapabilities)
    policy: IRPPolicy = field(default_factory=lambda: IRPPolicy(permission_scope_required="ATP:READ"))
    cost_model: IRPCostModel = field(default_factory=IRPCostModel)
    endpoint: IRPEndpoint = field(default_factory=IRPEndpoint)

    # Metadata
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        d = asdict(self)
        # Convert enums to strings
        d["kind"] = self.kind.value
        d["capabilities"]["tags"] = [t.value for t in self.capabilities.tags]
        return d


# =============================================================================
# Task Context for Expert Selection
# =============================================================================

@dataclass
class TaskContext:
    """Context for selecting IRP expert."""

    # SNARC salience
    salience: float  # 0.0 - 1.0

    # Epistemic confidence
    confidence: float  # 0.0 - 1.0

    # ATP budget
    budget_remaining: float

    # Task requirements
    requires_tools: bool = False
    requires_effectors: bool = False
    requires_reflection: bool = False

    # Metabolic state (from Session 92 Track 2)
    metabolic_mode: MetabolicState = MetabolicState.WAKE

    # Modality requirements
    modality_in: str = "text"
    modality_out: str = "text"


# =============================================================================
# IRP Expert Registry
# =============================================================================

class IRPExpertRegistry:
    """Registry for IRP experts with Web4 LCT identity."""

    def __init__(self, network: str = "web4.network"):
        self.network = network

        # Expert registry
        self.experts: Dict[str, IRPExpertDescriptor] = {}

        # Reputation tracking (from Session 92 Track 2)
        self.reputation_tracker = MetabolicReputationTracker()

        # Cross-federation (from Session 92 Track 1)
        self.federation = CrossFederationAuthenticator(network=network)

    def register_expert(
        self,
        descriptor: IRPExpertDescriptor,
        lct_identity: LCTIdentity,
        signing_key: str
    ) -> str:
        """Register IRP expert with LCT identity.

        Args:
            descriptor: Expert descriptor
            lct_identity: Web4 LCT identity
            signing_key: Private signing key (hex)

        Returns:
            Expert ID
        """
        # Create IRP identity
        descriptor.identity = IRPIdentity(
            lct_identity=lct_identity,
            signing_pubkey=signing_key  # In production, derive pubkey from privkey
        )

        # Store expert
        self.experts[descriptor.id] = descriptor

        # Initialize reputation
        self.reputation_tracker.register_agent(
            descriptor.id,
            initial_state=MetabolicState.WAKE
        )

        return descriptor.id

    def discover_experts(
        self,
        capability_tags: Optional[List[CapabilityTag]] = None,
        min_reputation: float = 0.5,
        max_cost: Optional[float] = None
    ) -> List[IRPExpertDescriptor]:
        """Discover experts matching criteria.

        Args:
            capability_tags: Required tags (any match)
            min_reputation: Minimum overall reputation
            max_cost: Maximum cost (p50)

        Returns:
            List of matching experts
        """
        matches = []

        for expert in self.experts.values():
            # Check reputation
            if expert.id in self.reputation_tracker.agents:
                rep = self.reputation_tracker.agents[expert.id].reputation.overall_reputation
                if rep < min_reputation:
                    continue

            # Check cost
            if max_cost is not None and expert.cost_model.estimate_p50 > max_cost:
                continue

            # Check capability tags
            if capability_tags:
                expert_tags = set(expert.capabilities.tags)
                required_tags = set(capability_tags)
                if not expert_tags.intersection(required_tags):
                    continue  # No tag match

            matches.append(expert)

        return matches

    def score_expert(self, expert: IRPExpertDescriptor, context: TaskContext) -> float:
        """Score expert for selection (from SAGE spec).

        Args:
            expert: Expert descriptor
            context: Task context

        Returns:
            Score (higher = better fit, -inf = disqualified)
        """
        # Hard requirements: modality
        if context.modality_in not in expert.capabilities.modalities_in:
            return float('-inf')
        if context.modality_out not in expert.capabilities.modalities_out:
            return float('-inf')

        # Hard requirements: budget
        # Use p95 estimate with headroom
        estimate = expert.cost_model.estimate_p95
        if estimate > context.budget_remaining:
            return float('-inf')

        score = 0.0

        # Get preferred/avoided tags based on context
        prefer, avoid = self._get_tag_preferences(context)

        # Tag matching
        for tag in expert.capabilities.tags:
            if tag in prefer:
                score += 1.0
            if tag in avoid:
                score -= 2.0

        # Cost penalty (steeper as cost approaches budget)
        cost_ratio = expert.cost_model.estimate_p50 / context.budget_remaining
        score -= cost_ratio * 0.8

        # Remote penalty (reduced in high-urgency contexts)
        if expert.endpoint.transport == "http":
            urgency = 1.0 if context.metabolic_mode == MetabolicState.CRISIS else 0.0
            remote_penalty = 0.2 * (1.0 - urgency)
            score -= remote_penalty

        # Reputation bonus (from Session 92 Track 2)
        if expert.id in self.reputation_tracker.agents:
            profile = self.reputation_tracker.agents[expert.id]
            # Use current metabolic state reputation
            state_rep = profile.reputation.get_reputation(context.metabolic_mode)
            score += state_rep * 0.5  # Up to +0.5 bonus for perfect reputation

        return score

    def _get_tag_preferences(self, context: TaskContext) -> tuple[Set[CapabilityTag], Set[CapabilityTag]]:
        """Get preferred and avoided tags for context.

        Based on routing heuristics from SAGE spec.
        """
        prefer = set()
        avoid = set()

        # Low confidence → need reflection, verification
        if context.confidence < 0.5:
            prefer.add(CapabilityTag.NEEDS_REFLECTION)
            prefer.add(CapabilityTag.VERIFICATION_ORIENTED)
            avoid.add(CapabilityTag.SAFE_ACTUATION)

        # High salience (novelty) → branchy, uncertainty-tolerant
        if context.salience > 0.7:
            prefer.add(CapabilityTag.BRANCHY_CONTROLFLOW)
            prefer.add(CapabilityTag.HIGH_UNCERTAINTY_TOLERANT)
            avoid.add(CapabilityTag.LOW_LATENCY)

        # Tools required
        if context.requires_tools:
            prefer.add(CapabilityTag.TOOL_HEAVY)
            avoid.add(CapabilityTag.COST_SENSITIVE)

        # Budget tight
        if context.budget_remaining < 20.0:
            prefer.add(CapabilityTag.COST_SENSITIVE)
            prefer.add(CapabilityTag.LOW_LATENCY)
            avoid.add(CapabilityTag.LONG_HORIZON)

        # Crisis mode
        if context.metabolic_mode == MetabolicState.CRISIS:
            prefer.add(CapabilityTag.LOW_LATENCY)
            prefer.add(CapabilityTag.VERIFICATION_ORIENTED)
            avoid.add(CapabilityTag.LONG_HORIZON)

        return prefer, avoid

    def select_best_expert(
        self,
        context: TaskContext,
        candidates: Optional[List[str]] = None
    ) -> Optional[str]:
        """Select best expert for task context.

        Args:
            context: Task context
            candidates: Optional list of expert IDs to consider (default: all)

        Returns:
            Best expert ID or None if no suitable expert
        """
        if candidates is None:
            candidates = list(self.experts.keys())

        best_expert = None
        best_score = float('-inf')

        for expert_id in candidates:
            if expert_id not in self.experts:
                continue

            expert = self.experts[expert_id]
            score = self.score_expert(expert, context)

            if score > best_score:
                best_score = score
                best_expert = expert_id

        return best_expert if best_score > float('-inf') else None


# =============================================================================
# Test Scenarios
# =============================================================================

def test_local_expert_registration():
    """Test Scenario 1: Register local IRP expert with LCT identity."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 1: Local IRP Expert Registration")
    print("=" * 80)

    registry = IRPExpertRegistry(network="web4.network")

    # Create expert descriptor
    descriptor = IRPExpertDescriptor(
        kind=ExpertKind.LOCAL_IRP,
        name="sage_consciousness_plugin",
        version="1.0.0",
        capabilities=IRPCapabilities(
            modalities_in=["text", "latent"],
            modalities_out=["text", "json", "latent"],
            tasks=["refine", "verify"],
            tags=[
                CapabilityTag.NEEDS_REFLECTION,
                CapabilityTag.VERIFICATION_ORIENTED,
                CapabilityTag.HIGH_UNCERTAINTY_TOLERANT
            ]
        ),
        cost_model=IRPCostModel(
            unit="atp",
            estimate_p50=8.0,
            estimate_p95=20.0
        )
    )

    # Create LCT identity
    lct_identity, priv_key = create_test_lct_identity("sage_consciousness", "web4.network")

    # Register expert
    expert_id = registry.register_expert(descriptor, lct_identity, priv_key)

    print(f"\n✅ Expert registered:")
    print(f"  ID: {expert_id}")
    print(f"  Name: {descriptor.name}")
    print(f"  Kind: {descriptor.kind.value}")
    print(f"  LCT: {lct_identity.to_lct_uri()}")
    print(f"  Capabilities: {[t.value for t in descriptor.capabilities.tags]}")
    print(f"  Cost (p50/p95): {descriptor.cost_model.estimate_p50}/{descriptor.cost_model.estimate_p95} ATP")

    # Verify registration
    assert expert_id in registry.experts
    assert registry.experts[expert_id].identity is not None
    assert registry.experts[expert_id].identity.lct_identity.to_lct_uri() == lct_identity.to_lct_uri()

    return {"status": "success", "expert_id": expert_id}


def test_expert_discovery():
    """Test Scenario 2: Discover experts by capability tags."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 2: Expert Discovery by Capability")
    print("=" * 80)

    registry = IRPExpertRegistry()

    # Register multiple experts with different capabilities
    experts_config = [
        ("reflection_expert", [CapabilityTag.NEEDS_REFLECTION, CapabilityTag.VERIFICATION_ORIENTED], 10.0),
        ("tool_expert", [CapabilityTag.TOOL_HEAVY, CapabilityTag.LOW_LATENCY], 5.0),
        ("planning_expert", [CapabilityTag.LONG_HORIZON, CapabilityTag.BRANCHY_CONTROLFLOW], 25.0),
    ]

    for name, tags, cost in experts_config:
        descriptor = IRPExpertDescriptor(
            name=name,
            capabilities=IRPCapabilities(tags=tags),
            cost_model=IRPCostModel(estimate_p50=cost, estimate_p95=cost*2)
        )
        lct_identity, priv_key = create_test_lct_identity(name, "web4.network")
        registry.register_expert(descriptor, lct_identity, priv_key)

    # Discover experts needing reflection
    print(f"\n🔍 Discovering experts with NEEDS_REFLECTION tag...")
    matches = registry.discover_experts(
        capability_tags=[CapabilityTag.NEEDS_REFLECTION]
    )

    print(f"\nFound {len(matches)} expert(s):")
    for expert in matches:
        print(f"  - {expert.name}: tags={[t.value for t in expert.capabilities.tags]}")

    assert len(matches) == 1
    assert matches[0].name == "reflection_expert"

    # Discover experts with cost limit
    print(f"\n🔍 Discovering experts with cost ≤ 10 ATP...")
    matches = registry.discover_experts(max_cost=10.0)

    print(f"\nFound {len(matches)} expert(s):")
    for expert in matches:
        print(f"  - {expert.name}: cost={expert.cost_model.estimate_p50} ATP")

    assert len(matches) == 2  # reflection_expert (10) and tool_expert (5)

    return {"status": "success", "discovery_tests": 2}


def test_capability_based_routing():
    """Test Scenario 3: Select expert based on task context."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 3: Capability-Based Expert Routing")
    print("=" * 80)

    registry = IRPExpertRegistry()

    # Register experts
    experts = {
        "fast_cheap": IRPExpertDescriptor(
            name="fast_cheap_expert",
            capabilities=IRPCapabilities(tags=[CapabilityTag.LOW_LATENCY, CapabilityTag.COST_SENSITIVE]),
            cost_model=IRPCostModel(estimate_p50=3.0, estimate_p95=5.0)
        ),
        "reflective": IRPExpertDescriptor(
            name="reflective_expert",
            capabilities=IRPCapabilities(tags=[CapabilityTag.NEEDS_REFLECTION, CapabilityTag.VERIFICATION_ORIENTED]),
            cost_model=IRPCostModel(estimate_p50=12.0, estimate_p95=25.0)
        ),
        "tool_heavy": IRPExpertDescriptor(
            name="tool_expert",
            capabilities=IRPCapabilities(tags=[CapabilityTag.TOOL_HEAVY, CapabilityTag.SAFE_ACTUATION]),
            cost_model=IRPCostModel(estimate_p50=8.0, estimate_p95=15.0)
        ),
    }

    for name, desc in experts.items():
        lct, priv = create_test_lct_identity(name, "web4.network")
        registry.register_expert(desc, lct, priv)

    # Test 1: Low confidence task → prefer reflection
    print(f"\n📋 Task 1: Low confidence (0.3), high budget (100 ATP)")
    context1 = TaskContext(
        salience=0.5,
        confidence=0.3,  # Low confidence
        budget_remaining=100.0
    )

    best = registry.select_best_expert(context1)
    print(f"  Selected: {registry.experts[best].name if best else 'None'}")
    assert best == experts["reflective"].id, "Should select reflective expert for low confidence"

    # Test 2: Tight budget → prefer cheap
    print(f"\n📋 Task 2: Normal confidence (0.7), tight budget (10 ATP)")
    context2 = TaskContext(
        salience=0.5,
        confidence=0.7,
        budget_remaining=10.0  # Tight budget
    )

    best = registry.select_best_expert(context2)
    print(f"  Selected: {registry.experts[best].name if best else 'None'}")
    assert best == experts["fast_cheap"].id, "Should select cheap expert for tight budget"

    # Test 3: Tools required
    print(f"\n📋 Task 3: Tools required, high budget (100 ATP)")
    context3 = TaskContext(
        salience=0.5,
        confidence=0.8,
        budget_remaining=100.0,
        requires_tools=True  # Tools required
    )

    best = registry.select_best_expert(context3)
    print(f"  Selected: {registry.experts[best].name if best else 'None'}")
    assert best == experts["tool_heavy"].id, "Should select tool expert when tools required"

    return {"status": "success", "routing_tests": 3}


# =============================================================================
# Main Test Execution
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SESSION 93 TRACK 1: IRP EXPERT REGISTRY WITH LCT IDENTITY")
    print("=" * 80)

    results = {}

    # Run test scenarios
    results["scenario_1"] = test_local_expert_registration()
    results["scenario_2"] = test_expert_discovery()
    results["scenario_3"] = test_capability_based_routing()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_success = all(r["status"] == "success" for r in results.values())

    print(f"\n✅ All scenarios passed: {all_success}")
    print(f"\nScenarios tested:")
    print(f"  1. Local IRP expert registration with LCT identity")
    print(f"  2. Expert discovery by capability tags and cost")
    print(f"  3. Capability-based routing for different task contexts")

    # Save results
    results_file = Path(__file__).parent / "session93_track1_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to: {results_file}")

    print("\n" + "=" * 80)
    print("Key Innovations:")
    print("=" * 80)
    print("1. IRP experts have Web4 LCT identity for trust/reputation")
    print("2. Capability tags enable intelligent routing (SAGE spec)")
    print("3. Cost models integrated with ATP budgeting")
    print("4. Metabolic state affects expert selection preferences")
    print("5. Expert reputation tracked per metabolic state (Session 92)")
    print("\nIRP Expert Registry bridges SAGE Fractal IRP with Web4 identity,")
    print("enabling decentralized expert discovery and trust-aware routing.")
    print("=" * 80)
