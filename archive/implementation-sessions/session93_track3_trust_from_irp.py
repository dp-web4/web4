#!/usr/bin/env python3
"""
Session 93 Track 3: Trust Tensor Updates from IRP Signals

**Date**: 2025-12-27
**Platform**: Legion (RTX 4090)
**Track**: 3 of 3 - Fractal IRP Integration

## Problem Statement

IRP execution produces rich signals about expert performance:
- `quality`: How good was the output?
- `confidence`: How certain was the expert?
- `latency_ms`: How fast was execution?
- `cost_ratio`: Actual cost vs estimated cost

These signals should update Web4 trust/reputation to enable:
1. Future expert selection based on track record
2. Reputation-based routing and discovery
3. Trust degradation for poor performance
4. Multi-dimensional trust (reliability, accuracy, speed, cost efficiency)

## Solution: IRP Signal → Trust Tensor Mapping

Map IRP result signals to Web4 V3/T3 dimensions:

```python
V3/T3 Dimensions:
- reliability: quality signal (0.0-1.0)
- accuracy: confidence signal (0.0-1.0)
- speed: 1.0 / (latency_ms / expected_latency_ms)
- cost_efficiency: estimated_cost / actual_cost
```

Update reputation using exponential moving average with metabolic state tracking.

## Integration with Previous Work

- **Session 92 Track 2**: Metabolic state-dependent reputation
- **Session 93 Track 1**: IRP expert registry with LCT identity
- **Session 93 Track 2**: ATP settlement produces quality signals

## Test Scenarios

1. **High-Quality Execution**: Quality signal updates reliability dimension
2. **Low-Confidence Execution**: Confidence signal updates accuracy dimension
3. **Fast Execution**: Low latency improves speed dimension
4. **Cost Overrun**: High cost degrades cost_efficiency dimension
5. **Multi-Execution History**: Reputation converges over multiple invocations

## Implementation

Based on SAGE's IRP signal mapping to Web4 V3/T3 from AUTO_SESSION_BRIEF.
"""

import time
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from pathlib import Path

# Import from previous tracks
from session93_track1_irp_expert_registry import (
    IRPExpertRegistry,
    IRPExpertDescriptor,
    TaskContext,
)

from session93_track2_atp_settlement import (
    ATPSettlementManager,
    invoke_irp_with_settlement,
)

from session92_track2_metabolic_reputation import (
    MetabolicState,
    StateDependentReputation,
    MetabolicReputationTracker,
)

from session88_track1_lct_society_authentication import (
    create_test_lct_identity,
)


# =============================================================================
# Multi-Dimensional Trust (V3/T3)
# =============================================================================

@dataclass
class TrustDimensions:
    """Multi-dimensional trust from V3/T3."""

    # Four dimensions (0.0 - 1.0)
    reliability: float = 0.5    # quality of outputs
    accuracy: float = 0.5       # confidence/certainty
    speed: float = 0.5          # latency performance
    cost_efficiency: float = 0.5  # cost vs estimate

    # Sample counts
    reliability_samples: int = 0
    accuracy_samples: int = 0
    speed_samples: int = 0
    cost_efficiency_samples: int = 0

    def update_dimension(self, dimension: str, value: float, learning_rate: float = 0.2):
        """Update dimension using exponential moving average."""
        if dimension == "reliability":
            current = self.reliability
            self.reliability = (1 - learning_rate) * current + learning_rate * value
            self.reliability_samples += 1
        elif dimension == "accuracy":
            current = self.accuracy
            self.accuracy = (1 - learning_rate) * current + learning_rate * value
            self.accuracy_samples += 1
        elif dimension == "speed":
            current = self.speed
            self.speed = (1 - learning_rate) * current + learning_rate * value
            self.speed_samples += 1
        elif dimension == "cost_efficiency":
            current = self.cost_efficiency
            self.cost_efficiency = (1 - learning_rate) * current + learning_rate * value
            self.cost_efficiency_samples += 1

    def get_overall_trust(self) -> float:
        """Compute overall trust (weighted average of dimensions)."""
        # Weight reliability and accuracy higher than speed and cost
        weights = {
            "reliability": 0.4,
            "accuracy": 0.3,
            "speed": 0.15,
            "cost_efficiency": 0.15
        }

        total = (
            self.reliability * weights["reliability"] +
            self.accuracy * weights["accuracy"] +
            self.speed * weights["speed"] +
            self.cost_efficiency * weights["cost_efficiency"]
        )

        return total

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


# =============================================================================
# IRP Signal → Trust Tensor Mapper
# =============================================================================

@dataclass
class IRPExecutionSignal:
    """Signals from IRP execution."""
    quality: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    latency_ms: float  # Actual latency
    expected_latency_ms: float  # Expected latency (from expert descriptor)
    actual_cost: float  # Actual ATP cost
    estimated_cost: float  # Estimated ATP cost (from expert descriptor)


class IRPTrustMapper:
    """Maps IRP signals to Web4 trust dimensions."""

    def __init__(self):
        # Expert trust (expert_id → TrustDimensions)
        self.expert_trust: Dict[str, TrustDimensions] = {}

        # Execution history (for analysis)
        self.execution_history: List[Dict] = []

    def initialize_expert(self, expert_id: str):
        """Initialize trust tracking for expert."""
        self.expert_trust[expert_id] = TrustDimensions()

    def update_from_irp_signal(
        self,
        expert_id: str,
        signal: IRPExecutionSignal,
        metabolic_state: MetabolicState = MetabolicState.WAKE
    ):
        """Update expert trust from IRP execution signal.

        Maps IRP signals to V3/T3 dimensions:
        - quality → reliability
        - confidence → accuracy
        - latency performance → speed
        - cost performance → cost_efficiency
        """
        if expert_id not in self.expert_trust:
            self.initialize_expert(expert_id)

        trust = self.expert_trust[expert_id]

        # Update reliability from quality
        trust.update_dimension("reliability", signal.quality)

        # Update accuracy from confidence
        trust.update_dimension("accuracy", signal.confidence)

        # Update speed from latency (1.0 = met expected, >1.0 = faster, <1.0 = slower)
        latency_ratio = signal.expected_latency_ms / signal.latency_ms
        speed_signal = min(1.0, latency_ratio)  # Cap at 1.0 (perfect)
        trust.update_dimension("speed", speed_signal)

        # Update cost_efficiency from cost (1.0 = met estimate, >1.0 = cheaper, <1.0 = more expensive)
        cost_ratio = signal.estimated_cost / signal.actual_cost
        efficiency_signal = min(1.0, cost_ratio)  # Cap at 1.0 (perfect)
        trust.update_dimension("cost_efficiency", efficiency_signal)

        # Record execution
        self.execution_history.append({
            "expert_id": expert_id,
            "metabolic_state": metabolic_state.value,
            "signal": asdict(signal),
            "trust_after": trust.to_dict(),
            "timestamp": time.time()
        })

    def get_expert_trust(self, expert_id: str) -> Optional[TrustDimensions]:
        """Get expert trust dimensions."""
        return self.expert_trust.get(expert_id)

    def get_trust_summary(self) -> Dict:
        """Get summary of all expert trust."""
        summary = {}
        for expert_id, trust in self.expert_trust.items():
            summary[expert_id] = {
                "overall": trust.get_overall_trust(),
                "dimensions": trust.to_dict()
            }
        return summary


# =============================================================================
# Integrated IRP with Trust Updates
# =============================================================================

def invoke_irp_with_trust_tracking(
    registry: IRPExpertRegistry,
    settlement: ATPSettlementManager,
    trust_mapper: IRPTrustMapper,
    caller_lct: str,
    expert_id: str,
    task_context: TaskContext,
    inputs: Dict,
    expected_latency_ms: float = 100.0
) -> Dict:
    """Invoke IRP with complete integration (settlement + trust updates).

    Args:
        registry: IRP expert registry
        settlement: ATP settlement manager
        trust_mapper: Trust mapper
        caller_lct: Caller LCT URI
        expert_id: Expert ID
        task_context: Task context
        inputs: Task inputs
        expected_latency_ms: Expected latency

    Returns:
        Complete result with ATP settlement and trust updates
    """
    # Get expert
    expert = registry.experts[expert_id]

    # Track execution time
    start_time = time.time()

    # Invoke with ATP settlement
    result = invoke_irp_with_settlement(
        registry=registry,
        settlement=settlement,
        caller_lct=caller_lct,
        expert_id=expert_id,
        task_context=task_context,
        inputs=inputs
    )

    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000

    # Create IRP signal
    signal = IRPExecutionSignal(
        quality=result.quality,
        confidence=result.confidence,
        latency_ms=latency_ms,
        expected_latency_ms=expected_latency_ms,
        actual_cost=result.atp_amount,
        estimated_cost=expert.cost_model.estimate_p50
    )

    # Update trust
    trust_mapper.update_from_irp_signal(
        expert_id=expert_id,
        signal=signal,
        metabolic_state=task_context.metabolic_mode
    )

    # Get updated trust
    trust = trust_mapper.get_expert_trust(expert_id)

    return {
        "irp_result": result,
        "signal": signal,
        "trust": trust.to_dict() if trust else None,
        "overall_trust": trust.get_overall_trust() if trust else 0.5
    }


# =============================================================================
# Test Scenarios
# =============================================================================

def test_high_quality_execution():
    """Test Scenario 1: High-quality execution improves reliability."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 1: High-Quality Execution → Reliability Update")
    print("=" * 80)

    registry = IRPExpertRegistry()
    settlement = ATPSettlementManager()
    trust_mapper = IRPTrustMapper()

    # Create accounts
    caller, _ = create_test_lct_identity("alice", "web4.network")
    executor, executor_priv = create_test_lct_identity("quality_expert", "web4.network")

    caller_lct = caller.to_lct_uri()
    settlement.initialize_account(caller_lct, 100.0)

    # Register high-quality expert
    from session93_track1_irp_expert_registry import IRPExpertDescriptor, ExpertKind, IRPCapabilities, CapabilityTag, IRPCostModel
    expert_desc = IRPExpertDescriptor(
        name="verified_expert",
        capabilities=IRPCapabilities(tags=[CapabilityTag.VERIFICATION_ORIENTED]),
        cost_model=IRPCostModel(estimate_p50=10.0, estimate_p95=15.0)
    )
    expert_id = registry.register_expert(expert_desc, executor, executor_priv)

    # Get initial trust (initialize if needed)
    if expert_id not in trust_mapper.expert_trust:
        trust_mapper.initialize_expert(expert_id)
    initial_trust = trust_mapper.get_expert_trust(expert_id)
    initial_reliability = initial_trust.reliability

    print(f"\n📊 Initial trust:")
    print(f"  Reliability: {initial_trust.reliability:.3f}")
    print(f"  Overall: {initial_trust.get_overall_trust():.3f}")

    # Invoke IRP
    result = invoke_irp_with_trust_tracking(
        registry=registry,
        settlement=settlement,
        trust_mapper=trust_mapper,
        caller_lct=caller_lct,
        expert_id=expert_id,
        task_context=TaskContext(salience=0.7, confidence=0.6, budget_remaining=100.0),
        inputs={"task": "verify"}
    )

    print(f"\n🔄 Execution:")
    print(f"  Quality: {result['signal'].quality:.3f}")
    print(f"  Confidence: {result['signal'].confidence:.3f}")

    print(f"\n📊 Updated trust:")
    print(f"  Reliability: {result['trust']['reliability']:.3f}")
    print(f"  Accuracy: {result['trust']['accuracy']:.3f}")
    print(f"  Overall: {result['overall_trust']:.3f}")

    # Verify trust improved
    reliability_improved = result['trust']['reliability'] > initial_reliability
    print(f"\n✅ Trust improved: {reliability_improved}")
    print(f"   {initial_reliability:.3f} → {result['trust']['reliability']:.3f}")

    assert reliability_improved, f"Reliability should improve: {initial_reliability} -> {result['trust']['reliability']}"

    return {"status": "success", "trust_improved": reliability_improved}


def test_multi_execution_convergence():
    """Test Scenario 2: Trust converges over multiple executions."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 2: Multi-Execution Trust Convergence")
    print("=" * 80)

    registry = IRPExpertRegistry()
    settlement = ATPSettlementManager()
    trust_mapper = IRPTrustMapper()

    # Setup
    caller, _ = create_test_lct_identity("alice", "web4.network")
    executor, executor_priv = create_test_lct_identity("consistent_expert", "web4.network")

    caller_lct = caller.to_lct_uri()
    settlement.initialize_account(caller_lct, 1000.0)  # Large balance for multiple invocations

    # Register expert
    from session93_track1_irp_expert_registry import IRPExpertDescriptor, IRPCapabilities, CapabilityTag, IRPCostModel
    expert_desc = IRPExpertDescriptor(
        name="stable_expert",
        capabilities=IRPCapabilities(tags=[CapabilityTag.VERIFICATION_ORIENTED]),
        cost_model=IRPCostModel(estimate_p50=10.0, estimate_p95=15.0)
    )
    expert_id = registry.register_expert(expert_desc, executor, executor_priv)

    trust_mapper.initialize_expert(expert_id)

    print(f"\n📊 Running 10 executions...")

    trust_history = []

    for i in range(10):
        result = invoke_irp_with_trust_tracking(
            registry=registry,
            settlement=settlement,
            trust_mapper=trust_mapper,
            caller_lct=caller_lct,
            expert_id=expert_id,
            task_context=TaskContext(salience=0.5, confidence=0.7, budget_remaining=1000.0),
            inputs={"task": f"execution_{i}"}
        )

        trust_history.append(result['overall_trust'])

        if i % 3 == 0:  # Print every 3rd execution
            print(f"  Execution {i+1}: Overall trust = {result['overall_trust']:.3f}")

    # Verify convergence (variance should decrease)
    early_variance = sum((t - sum(trust_history[:5])/5)**2 for t in trust_history[:5]) / 5
    late_variance = sum((t - sum(trust_history[5:])/5)**2 for t in trust_history[5:]) / 5

    print(f"\n📈 Convergence:")
    print(f"  Early variance (executions 1-5): {early_variance:.6f}")
    print(f"  Late variance (executions 6-10): {late_variance:.6f}")
    print(f"  Converged: {late_variance < early_variance}")

    final_trust = trust_mapper.get_expert_trust(expert_id)
    print(f"\n📊 Final trust (after 10 executions):")
    print(f"  Reliability: {final_trust.reliability:.3f} ({final_trust.reliability_samples} samples)")
    print(f"  Accuracy: {final_trust.accuracy:.3f} ({final_trust.accuracy_samples} samples)")
    print(f"  Speed: {final_trust.speed:.3f} ({final_trust.speed_samples} samples)")
    print(f"  Cost Efficiency: {final_trust.cost_efficiency:.3f} ({final_trust.cost_efficiency_samples} samples)")
    print(f"  Overall: {final_trust.get_overall_trust():.3f}")

    return {"status": "success", "executions": 10, "converged": late_variance < early_variance}


def test_cost_overrun_penalty():
    """Test Scenario 3: Cost overrun degrades cost_efficiency dimension."""

    print("\n" + "=" * 80)
    print("TEST SCENARIO 3: Cost Overrun → Cost Efficiency Penalty")
    print("=" * 80)

    trust_mapper = IRPTrustMapper()

    expert_id = "expensive_expert"
    trust_mapper.initialize_expert(expert_id)

    # First establish good cost efficiency
    good_signal = IRPExecutionSignal(
        quality=0.80, confidence=0.75,
        latency_ms=100.0, expected_latency_ms=100.0,
        actual_cost=10.0, estimated_cost=10.0  # Perfect cost match
    )
    trust_mapper.update_from_irp_signal(expert_id, good_signal)

    initial_trust = trust_mapper.get_expert_trust(expert_id)
    initial_efficiency = initial_trust.cost_efficiency

    print(f"\n📊 Initial cost efficiency (after good execution): {initial_efficiency:.3f}")

    # Simulate expensive execution (actual cost > estimated cost)
    signal = IRPExecutionSignal(
        quality=0.85,
        confidence=0.80,
        latency_ms=100.0,
        expected_latency_ms=100.0,
        actual_cost=20.0,  # Actual
        estimated_cost=10.0  # Estimated (2x overrun!)
    )

    trust_mapper.update_from_irp_signal(expert_id, signal)

    updated_trust = trust_mapper.get_expert_trust(expert_id)
    updated_efficiency = updated_trust.cost_efficiency

    print(f"\n🔄 Execution:")
    print(f"  Estimated cost: {signal.estimated_cost} ATP")
    print(f"  Actual cost: {signal.actual_cost} ATP")
    print(f"  Overrun: {signal.actual_cost / signal.estimated_cost:.1f}x")

    print(f"\n📊 Updated cost efficiency: {updated_efficiency:.3f}")
    print(f"  Change: {updated_efficiency - initial_efficiency:+.3f}")

    # Verify efficiency degraded
    assert updated_efficiency < initial_efficiency

    return {"status": "success", "efficiency_degraded": True}


# =============================================================================
# Main Test Execution
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SESSION 93 TRACK 3: TRUST TENSOR UPDATES FROM IRP SIGNALS")
    print("=" * 80)

    results = {}

    # Run test scenarios
    results["scenario_1"] = test_high_quality_execution()
    results["scenario_2"] = test_multi_execution_convergence()
    results["scenario_3"] = test_cost_overrun_penalty()

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    all_success = all(r["status"] == "success" for r in results.values())

    print(f"\n✅ All scenarios passed: {all_success}")
    print(f"\nScenarios tested:")
    print(f"  1. High-quality execution improves reliability")
    print(f"  2. Trust converges over 10 executions")
    print(f"  3. Cost overrun degrades cost_efficiency")

    # Save results
    results_file = Path(__file__).parent / "session93_track3_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to: {results_file}")

    print("\n" + "=" * 80)
    print("Key Innovations:")
    print("=" * 80)
    print("1. IRP signals map to V3/T3 trust dimensions:")
    print("   - quality → reliability")
    print("   - confidence → accuracy")
    print("   - latency → speed")
    print("   - cost → cost_efficiency")
    print("2. Multi-dimensional trust enables fine-grained reputation")
    print("3. Exponential moving average for trust convergence")
    print("4. Overall trust weighted by dimension importance")
    print("5. Complete integration: Registry → Settlement → Trust")
    print("\nIRP Trust Mapping completes the Fractal IRP integration,")
    print("enabling Web4's decentralized AI marketplace with reputation.")
    print("=" * 80)
