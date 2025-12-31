"""
Web4 EP Performance Benchmark

Validates performance of the Web4 Security EP Trilogy on production hardware:
1. Grounding EP prediction throughput
2. Relationship EP prediction throughput
3. Authorization EP prediction throughput
4. Multi-EP Coordinator throughput
5. Full integration stress test

Based on Sprout's edge validation methodology (EP_EDGE_VALIDATION_SUMMARY.md)
which achieved 63K+ decisions/second on Jetson Orin Nano.

Created: 2025-12-31
Session: 110 (Legion autonomous research)
Hardware: Legion RTX 4090 (expecting significantly higher throughput than edge)
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass, asdict

# Import all EP systems
from grounding_quality_ep import (
    GroundingQualityPredictor,
    IdentityGroundingHistory
)
from relationship_coherence_ep import (
    RelationshipCoherencePredictor,
    RelationshipHistory,
    InteractionCharacteristics,
    TrustTensor,
    StanceVector
)
from authorization_ep import (
    AuthorizationEPPredictor,
    AuthorizationContext,
    Permission,
    PermissionScope
)
from web4_multi_ep_coordinator import (
    Web4MultiEPCoordinator,
    SecurityEPPrediction,
    SecurityEPDomain
)


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    component: str
    test_name: str
    iterations: int
    total_time_seconds: float
    throughput_per_second: float
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    memory_used_mb: float = 0.0
    notes: str = ""


class Web4EPBenchmark:
    """Performance benchmark suite for Web4 EP trilogy."""

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    def run_all_benchmarks(self) -> Dict:
        """Run all performance benchmarks."""
        print("=" * 80)
        print("WEB4 EP PERFORMANCE BENCHMARK")
        print(f"Hardware: Legion RTX 4090")
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 80)
        print()

        # Benchmark each component
        self.benchmark_grounding_ep()
        self.benchmark_relationship_ep()
        self.benchmark_authorization_ep()
        self.benchmark_coordinator()
        self.benchmark_integration_stress_test()

        # Generate summary
        summary = self.generate_summary()
        return summary

    def benchmark_grounding_ep(self):
        """Benchmark Grounding EP prediction throughput."""
        print("1. Grounding EP Prediction Throughput")
        print("-" * 80)

        predictor = GroundingQualityPredictor()

        # Create test data
        history = IdentityGroundingHistory(
            identity_lct="lct://test@mainnet",
            grounding_count=50,
            successful_groundings=45,
            failed_groundings=5,
            avg_coherence_index=0.85,
            last_grounding_ci=0.87,
            last_grounding_time=datetime.now() - timedelta(hours=2),
            location_changes=3,
            capability_changes=1,
            recent_anomalies=0
        )

        context = {
            "impossible_travel": False,
            "capability_mismatch": False,
            "time_since_last_grounding": timedelta(hours=2),
            "has_witnesses": True
        }

        # Warm-up
        for _ in range(100):
            predictor.predict_quality(history, context)

        # Benchmark
        iterations = 10000
        latencies = []

        start = time.time()
        for _ in range(iterations):
            iter_start = time.perf_counter()
            prediction = predictor.predict_quality(history, context)
            iter_end = time.perf_counter()
            latencies.append((iter_end - iter_start) * 1000)  # ms
        end = time.time()

        total_time = end - start
        throughput = iterations / total_time

        result = BenchmarkResult(
            component="Grounding EP",
            test_name="Prediction Throughput",
            iterations=iterations,
            total_time_seconds=total_time,
            throughput_per_second=throughput,
            avg_latency_ms=sum(latencies) / len(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            notes=f"Pattern library: {predictor.get_pattern_count()} patterns"
        )

        self.results.append(result)
        self._print_result(result)
        print()

    def benchmark_relationship_ep(self):
        """Benchmark Relationship EP prediction throughput."""
        print("2. Relationship EP Prediction Throughput")
        print("-" * 80)

        predictor = RelationshipCoherencePredictor()

        # Create test data
        relationship = RelationshipHistory(
            relationship_lct="lct://alice:relationship:bob@mainnet",
            participant_lcts=("lct://alice@mainnet", "lct://bob@mainnet"),
            formed_date="2025-11-01",
            source="crystallized",
            current_trust=TrustTensor(0.85, 0.90, 0.80, 0.88),
            current_stance=StanceVector(0.85, 0.10, 0.03, 0.02),
            current_ci=0.92,
            total_interactions=150,
            recent_interactions=25,
            positive_interactions=140,
            negative_interactions=3,
            repair_events=1,
            avg_response_time=timedelta(minutes=5),
            response_time_variance=0.15,
            avg_interaction_gap=timedelta(hours=6),
            last_interaction=datetime.now() - timedelta(hours=4),
            trust_trajectory="improving",
            stance_stability=0.95,
            ci_history=[0.88, 0.89, 0.91, 0.92]
        )

        interaction = InteractionCharacteristics(
            interaction_type="request",
            complexity="MEDIUM",
            expected_response_time=timedelta(minutes=5),
            actual_response_time=timedelta(minutes=6),
            claims_made=2,
            commitments_made=1,
            resources_requested=10.0,
            time_since_last=timedelta(hours=4),
            grounding_ci=0.91,
            witness_count=3
        )

        # Warm-up
        for _ in range(100):
            predictor.predict_coherence(relationship, interaction)

        # Benchmark
        iterations = 10000
        latencies = []

        start = time.time()
        for _ in range(iterations):
            iter_start = time.perf_counter()
            prediction = predictor.predict_coherence(relationship, interaction)
            iter_end = time.perf_counter()
            latencies.append((iter_end - iter_start) * 1000)
        end = time.time()

        total_time = end - start
        throughput = iterations / total_time

        result = BenchmarkResult(
            component="Relationship EP",
            test_name="Prediction Throughput",
            iterations=iterations,
            total_time_seconds=total_time,
            throughput_per_second=throughput,
            avg_latency_ms=sum(latencies) / len(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            notes=f"Pattern library: {predictor.get_pattern_count()} patterns"
        )

        self.results.append(result)
        self._print_result(result)
        print()

    def benchmark_authorization_ep(self):
        """Benchmark Authorization EP prediction throughput."""
        print("3. Authorization EP Prediction Throughput")
        print("-" * 80)

        predictor = AuthorizationEPPredictor()

        # Create test data
        context = AuthorizationContext(
            requester_lct="lct://alice@mainnet",
            grounding_ci=0.92,
            identity_age=timedelta(days=180),
            relationship_lct="lct://alice:relationship:bob@mainnet",
            relationship_trust_avg=0.85,
            relationship_ci=0.90,
            relationship_stance_collaborative=0.85,
            current_permissions=["storage:read"],
            permission_count=2,
            revocations=0,
            violations=0,
            permission_requested=Permission(
                resource_type="storage",
                resource_id="project-data",
                scope={PermissionScope.READ, PermissionScope.WRITE},
                duration=timedelta(days=30),
                sensitivity_level=0.3,
                can_delegate=False,
                description="Access project storage"
            ),
            justification_provided=True,
            urgency_claimed="low"
        )

        # Warm-up
        for _ in range(100):
            predictor.predict_authorization(context)

        # Benchmark
        iterations = 10000
        latencies = []

        start = time.time()
        for _ in range(iterations):
            iter_start = time.perf_counter()
            prediction = predictor.predict_authorization(context)
            iter_end = time.perf_counter()
            latencies.append((iter_end - iter_start) * 1000)
        end = time.time()

        total_time = end - start
        throughput = iterations / total_time

        result = BenchmarkResult(
            component="Authorization EP",
            test_name="Prediction Throughput",
            iterations=iterations,
            total_time_seconds=total_time,
            throughput_per_second=throughput,
            avg_latency_ms=sum(latencies) / len(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            notes=f"Pattern library: {len(predictor.patterns)} patterns"
        )

        self.results.append(result)
        self._print_result(result)
        print()

    def benchmark_coordinator(self):
        """Benchmark Multi-EP Coordinator throughput."""
        print("4. Multi-EP Coordinator Throughput")
        print("-" * 80)

        coordinator = Web4MultiEPCoordinator()

        # Create test predictions
        grounding_pred = SecurityEPPrediction(
            domain=SecurityEPDomain.GROUNDING,
            risk_probability=0.15,
            confidence=0.85,
            severity=0.25,
            recommendation="proceed",
            reasoning="Identity verified"
        )

        relationship_pred = SecurityEPPrediction(
            domain=SecurityEPDomain.RELATIONSHIP,
            risk_probability=0.20,
            confidence=0.80,
            severity=0.30,
            recommendation="proceed",
            reasoning="Trusted relationship"
        )

        authorization_pred = SecurityEPPrediction(
            domain=SecurityEPDomain.AUTHORIZATION,
            risk_probability=0.12,
            confidence=0.78,
            severity=0.22,
            recommendation="proceed",
            reasoning="Low-risk permission"
        )

        # Warm-up
        for _ in range(100):
            coordinator.coordinate(
                grounding_pred=grounding_pred,
                relationship_pred=relationship_pred,
                authorization_pred=authorization_pred
            )

        # Benchmark
        iterations = 50000  # Higher for coordinator
        latencies = []

        start = time.time()
        for i in range(iterations):
            iter_start = time.perf_counter()
            decision = coordinator.coordinate(
                grounding_pred=grounding_pred,
                relationship_pred=relationship_pred,
                authorization_pred=authorization_pred,
                decision_id=f"bench_{i}"
            )
            iter_end = time.perf_counter()
            latencies.append((iter_end - iter_start) * 1000)
        end = time.time()

        total_time = end - start
        throughput = iterations / total_time

        result = BenchmarkResult(
            component="Multi-EP Coordinator",
            test_name="Coordination Throughput",
            iterations=iterations,
            total_time_seconds=total_time,
            throughput_per_second=throughput,
            avg_latency_ms=sum(latencies) / len(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            notes=f"3-EP coordination, {coordinator.get_stats()['decisions_made']} decisions"
        )

        self.results.append(result)
        self._print_result(result)
        print()

    def benchmark_integration_stress_test(self):
        """Benchmark full integration with all systems."""
        print("5. Full Integration Stress Test (10,000 cycles)")
        print("-" * 80)

        # Initialize all systems
        grounding_predictor = GroundingQualityPredictor()
        relationship_predictor = RelationshipCoherencePredictor()
        authorization_predictor = AuthorizationEPPredictor()
        coordinator = Web4MultiEPCoordinator()

        # Create test data for all systems
        grounding_history = IdentityGroundingHistory(
            identity_lct="lct://stress@mainnet",
            grounding_count=100,
            successful_groundings=95,
            failed_groundings=5,
            avg_coherence_index=0.88,
            last_grounding_ci=0.90,
            last_grounding_time=datetime.now() - timedelta(hours=1),
            location_changes=2,
            capability_changes=0,
            recent_anomalies=0
        )

        relationship_history = RelationshipHistory(
            relationship_lct="lct://stress:relationship:test@mainnet",
            participant_lcts=("lct://stress@mainnet", "lct://test@mainnet"),
            formed_date="2025-11-01",
            source="crystallized",
            current_trust=TrustTensor(0.80, 0.85, 0.75, 0.82),
            current_stance=StanceVector(0.80, 0.15, 0.03, 0.02),
            current_ci=0.85,
            total_interactions=200,
            recent_interactions=30,
            positive_interactions=180,
            negative_interactions=5,
            repair_events=2,
            avg_response_time=timedelta(minutes=8),
            response_time_variance=0.20,
            avg_interaction_gap=timedelta(hours=8),
            last_interaction=datetime.now() - timedelta(hours=6),
            trust_trajectory="stable",
            stance_stability=0.90,
            ci_history=[0.83, 0.84, 0.85, 0.85]
        )

        auth_context = AuthorizationContext(
            requester_lct="lct://stress@mainnet",
            grounding_ci=0.90,
            identity_age=timedelta(days=90),
            relationship_lct="lct://stress:relationship:test@mainnet",
            relationship_trust_avg=0.80,
            relationship_ci=0.85,
            relationship_stance_collaborative=0.80,
            current_permissions=["storage:read", "compute:execute"],
            permission_count=5,
            revocations=0,
            violations=0,
            permission_requested=Permission(
                resource_type="storage",
                resource_id="data",
                scope={PermissionScope.READ, PermissionScope.WRITE},
                duration=timedelta(days=14),
                sensitivity_level=0.4,
                can_delegate=False
            ),
            justification_provided=True,
            urgency_claimed="medium"
        )

        # Warm-up
        for _ in range(100):
            g_pred = grounding_predictor.predict_quality(
                grounding_history,
                {"impossible_travel": False, "capability_mismatch": False,
                 "time_since_last_grounding": timedelta(hours=1), "has_witnesses": True}
            )

        # Full integration benchmark
        iterations = 10000
        latencies = []
        decision_counts = {"proceed": 0, "adjust": 0, "defer": 0, "reject": 0}

        start = time.time()
        for i in range(iterations):
            iter_start = time.perf_counter()

            # Get all predictions
            grounding_pred_result = grounding_predictor.predict_quality(
                grounding_history,
                {"impossible_travel": False, "capability_mismatch": False,
                 "time_since_last_grounding": timedelta(hours=1), "has_witnesses": True}
            )

            relationship_pred_result = relationship_predictor.predict_coherence(
                relationship_history,
                InteractionCharacteristics(
                    interaction_type="request",
                    complexity="MEDIUM",
                    expected_response_time=timedelta(minutes=8),
                    actual_response_time=timedelta(minutes=9),
                    claims_made=2,
                    commitments_made=1,
                    resources_requested=15.0,
                    time_since_last=timedelta(hours=6),
                    grounding_ci=0.90,
                    witness_count=2
                )
            )

            auth_pred_result = authorization_predictor.predict_authorization(auth_context)

            # Convert to SecurityEPPredictions
            grounding_ep_pred = SecurityEPPrediction(
                domain=SecurityEPDomain.GROUNDING,
                risk_probability=1.0 - grounding_pred_result.predicted_ci,
                confidence=grounding_pred_result.confidence,
                severity=grounding_pred_result.risk_score,
                recommendation="proceed" if grounding_pred_result.predicted_ci > 0.6 else "adjust",
                reasoning=grounding_pred_result.reasoning
            )

            relationship_ep_pred = SecurityEPPrediction(
                domain=SecurityEPDomain.RELATIONSHIP,
                risk_probability=abs(relationship_pred_result.predicted_ci_change) if relationship_pred_result.predicted_ci_change < 0 else 0.1,
                confidence=relationship_pred_result.confidence,
                severity=relationship_pred_result.risk_score,
                recommendation="proceed" if relationship_pred_result.predicted_ci_after > 0.6 else "adjust",
                reasoning=relationship_pred_result.reasoning
            )

            auth_ep_pred = SecurityEPPrediction(
                domain=SecurityEPDomain.AUTHORIZATION,
                risk_probability=auth_pred_result.predicted_abuse_probability,
                confidence=auth_pred_result.confidence,
                severity=auth_pred_result.risk_score,
                recommendation="proceed" if auth_pred_result.predicted_abuse_probability < 0.4 else "reject",
                reasoning=auth_pred_result.reasoning
            )

            # Coordinate
            decision = coordinator.coordinate(
                grounding_pred=grounding_ep_pred,
                relationship_pred=relationship_ep_pred,
                authorization_pred=auth_ep_pred,
                decision_id=f"stress_{i}"
            )

            decision_counts[decision.final_decision] = decision_counts.get(decision.final_decision, 0) + 1

            iter_end = time.perf_counter()
            latencies.append((iter_end - iter_start) * 1000)

        end = time.time()

        total_time = end - start
        throughput = iterations / total_time

        result = BenchmarkResult(
            component="Full Integration",
            test_name="Stress Test",
            iterations=iterations,
            total_time_seconds=total_time,
            throughput_per_second=throughput,
            avg_latency_ms=sum(latencies) / len(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            notes=(
                f"All 3 EPs + Coordinator. "
                f"Decisions: proceed={decision_counts.get('proceed', 0)}, "
                f"adjust={decision_counts.get('adjust', 0)}, "
                f"defer={decision_counts.get('defer', 0)}, "
                f"reject={decision_counts.get('reject', 0)}"
            )
        )

        self.results.append(result)
        self._print_result(result)
        print()

    def _print_result(self, result: BenchmarkResult):
        """Print a benchmark result."""
        print(f"Component: {result.component}")
        print(f"Test: {result.test_name}")
        print(f"Iterations: {result.iterations:,}")
        print(f"Total Time: {result.total_time_seconds:.3f}s")
        print(f"Throughput: {result.throughput_per_second:,.0f} operations/sec")
        print(f"Avg Latency: {result.avg_latency_ms:.4f}ms")
        print(f"Min Latency: {result.min_latency_ms:.4f}ms")
        print(f"Max Latency: {result.max_latency_ms:.4f}ms")
        if result.notes:
            print(f"Notes: {result.notes}")

    def generate_summary(self) -> Dict:
        """Generate benchmark summary."""
        print("=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        print()

        summary = {
            "timestamp": datetime.now().isoformat(),
            "hardware": "Legion RTX 4090",
            "results": [asdict(r) for r in self.results],
            "totals": {
                "total_iterations": sum(r.iterations for r in self.results),
                "total_time": sum(r.total_time_seconds for r in self.results),
                "avg_throughput": sum(r.throughput_per_second for r in self.results) / len(self.results)
            }
        }

        print(f"Total Tests: {len(self.results)}")
        print(f"Total Iterations: {summary['totals']['total_iterations']:,}")
        print(f"Total Time: {summary['totals']['total_time']:.2f}s")
        print(f"Average Throughput: {summary['totals']['avg_throughput']:,.0f} ops/sec")
        print()

        print("Individual Component Throughput:")
        for result in self.results:
            print(f"  {result.component:25s}: {result.throughput_per_second:>12,.0f} ops/sec")

        print()
        print("=" * 80)
        print("BENCHMARK COMPLETE")
        print("=" * 80)

        return summary


if __name__ == "__main__":
    benchmark = Web4EPBenchmark()
    summary = benchmark.run_all_benchmarks()

    # Save results
    with open("web4_ep_benchmark_results.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to: web4_ep_benchmark_results.json")
