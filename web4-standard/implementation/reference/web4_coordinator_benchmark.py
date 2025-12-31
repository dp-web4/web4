"""
Web4 Multi-EP Security Coordinator Performance Benchmark

Focused performance validation of the coordinator - the critical integration point.

Based on Sprout's methodology which achieved:
- Multi-EP Coordinator: 97,204/sec throughput, 10.29 microsecond latency
- Integrated stress test: 9,516 cycles/sec

This benchmark validates Web4 Multi-EP Security Coordinator on Legion (RTX 4090).

Created: 2025-12-31
Session: 110 (Legion autonomous research)
"""

import time
import json
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, asdict

from web4_multi_ep_coordinator import (
    Web4MultiEPCoordinator,
    SecurityEPPrediction,
    SecurityEPDomain
)


@dataclass
class BenchmarkResult:
    """Benchmark result metrics."""
    test_name: str
    iterations: int
    total_time_seconds: float
    throughput_per_second: float
    avg_latency_ms: float
    avg_latency_us: float  # microseconds for comparison with Sprout
    min_latency_ms: float
    max_latency_ms: float
    notes: str = ""


class CoordinatorBenchmark:
    """Performance benchmark for Web4 Multi-EP Security Coordinator."""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.coordinator = Web4MultiEPCoordinator()

    def run_all_tests(self) -> Dict:
        """Run all benchmark tests."""
        print("=" * 80)
        print("WEB4 MULTI-EP SECURITY COORDINATOR BENCHMARK")
        print(f"Hardware: Legion RTX 4090")
        print(f"Started: {datetime.now().isoformat()}")
        print("=" * 80)
        print()

        self.test_consensus_throughput()
        self.test_conflict_resolution_throughput()
        self.test_cascade_detection_throughput()
        self.test_mixed_scenario_stress()

        summary = self.generate_summary()
        return summary

    def test_consensus_throughput(self):
        """Test throughput when all EPs agree."""
        print("Test 1: Consensus Decision Throughput")
        print("-" * 80)

        # Create predictions that all agree
        pred_low_risk = SecurityEPPrediction(
            domain=SecurityEPDomain.GROUNDING,
            risk_probability=0.15,
            confidence=0.85,
            severity=0.25,
            recommendation="proceed",
            reasoning="Low risk scenario"
        )

        # Warm-up
        for _ in range(1000):
            self.coordinator.coordinate(
                grounding_pred=pred_low_risk,
                relationship_pred=pred_low_risk,
                authorization_pred=pred_low_risk
            )

        # Reset stats
        self.coordinator = Web4MultiEPCoordinator()

        # Benchmark
        iterations = 100000
        latencies_ms = []

        start = time.time()
        for i in range(iterations):
            iter_start = time.perf_counter()

            decision = self.coordinator.coordinate(
                grounding_pred=pred_low_risk,
                relationship_pred=pred_low_risk,
                authorization_pred=pred_low_risk,
                decision_id=f"consensus_{i}"
            )

            iter_end = time.perf_counter()
            latencies_ms.append((iter_end - iter_start) * 1000)

        end = time.time()

        total_time = end - start
        throughput = iterations / total_time
        avg_lat_ms = sum(latencies_ms) / len(latencies_ms)

        result = BenchmarkResult(
            test_name="Consensus (all proceed)",
            iterations=iterations,
            total_time_seconds=total_time,
            throughput_per_second=throughput,
            avg_latency_ms=avg_lat_ms,
            avg_latency_us=avg_lat_ms * 1000,
            min_latency_ms=min(latencies_ms),
            max_latency_ms=max(latencies_ms),
            notes="All 3 EPs agree to proceed"
        )

        self.results.append(result)
        self._print_result(result)
        print()

    def test_conflict_resolution_throughput(self):
        """Test throughput when EPs conflict."""
        print("Test 2: Conflict Resolution Throughput")
        print("-" * 80)

        grounding_reject = SecurityEPPrediction(
            domain=SecurityEPDomain.GROUNDING,
            risk_probability=0.75,
            confidence=0.85,
            severity=0.80,
            recommendation="reject",
            reasoning="Identity concern"
        )

        relationship_proceed = SecurityEPPrediction(
            domain=SecurityEPDomain.RELATIONSHIP,
            risk_probability=0.20,
            confidence=0.75,
            severity=0.30,
            recommendation="proceed",
            reasoning="Trusted relationship"
        )

        # Warm-up
        for _ in range(1000):
            self.coordinator.coordinate(
                grounding_pred=grounding_reject,
                relationship_pred=relationship_proceed
            )

        # Reset
        self.coordinator = Web4MultiEPCoordinator()

        # Benchmark
        iterations = 100000
        latencies_ms = []

        start = time.time()
        for i in range(iterations):
            iter_start = time.perf_counter()

            decision = self.coordinator.coordinate(
                grounding_pred=grounding_reject,
                relationship_pred=relationship_proceed,
                decision_id=f"conflict_{i}"
            )

            iter_end = time.perf_counter()
            latencies_ms.append((iter_end - iter_start) * 1000)

        end = time.time()

        total_time = end - start
        throughput = iterations / total_time
        avg_lat_ms = sum(latencies_ms) / len(latencies_ms)

        result = BenchmarkResult(
            test_name="Conflict Resolution",
            iterations=iterations,
            total_time_seconds=total_time,
            throughput_per_second=throughput,
            avg_latency_ms=avg_lat_ms,
            avg_latency_us=avg_lat_ms * 1000,
            min_latency_ms=min(latencies_ms),
            max_latency_ms=max(latencies_ms),
            notes="Grounding rejects, Relationship proceeds - priority resolution"
        )

        self.results.append(result)
        self._print_result(result)
        print()

    def test_cascade_detection_throughput(self):
        """Test throughput when detecting security cascades."""
        print("Test 3: Cascade Detection Throughput")
        print("-" * 80)

        severe_pred_1 = SecurityEPPrediction(
            domain=SecurityEPDomain.GROUNDING,
            risk_probability=0.85,
            confidence=0.90,
            severity=0.90,  # Severe
            recommendation="reject",
            reasoning="Critical grounding failure"
        )

        severe_pred_2 = SecurityEPPrediction(
            domain=SecurityEPDomain.RELATIONSHIP,
            risk_probability=0.80,
            confidence=0.88,
            severity=0.85,  # Severe
            recommendation="reject",
            reasoning="Relationship degraded"
        )

        # Warm-up
        for _ in range(1000):
            self.coordinator.coordinate(
                grounding_pred=severe_pred_1,
                relationship_pred=severe_pred_2
            )

        # Reset
        self.coordinator = Web4MultiEPCoordinator()

        # Benchmark
        iterations = 100000
        latencies_ms = []

        start = time.time()
        for i in range(iterations):
            iter_start = time.perf_counter()

            decision = self.coordinator.coordinate(
                grounding_pred=severe_pred_1,
                relationship_pred=severe_pred_2,
                decision_id=f"cascade_{i}"
            )

            iter_end = time.perf_counter()
            latencies_ms.append((iter_end - iter_start) * 1000)

        end = time.time()

        total_time = end - start
        throughput = iterations / total_time
        avg_lat_ms = sum(latencies_ms) / len(latencies_ms)

        result = BenchmarkResult(
            test_name="Cascade Detection",
            iterations=iterations,
            total_time_seconds=total_time,
            throughput_per_second=throughput,
            avg_latency_ms=avg_lat_ms,
            avg_latency_us=avg_lat_ms * 1000,
            min_latency_ms=min(latencies_ms),
            max_latency_ms=max(latencies_ms),
            notes="2 severe predictions triggering cascade"
        )

        self.results.append(result)
        self._print_result(result)
        print()

    def test_mixed_scenario_stress(self):
        """Stress test with mixed scenarios."""
        print("Test 4: Mixed Scenario Stress Test (50,000 cycles)")
        print("-" * 80)

        # Create varied scenarios
        scenarios = [
            # Consensus proceed
            (
                SecurityEPPrediction(SecurityEPDomain.GROUNDING, 0.10, 0.85, 0.20, "proceed", "OK"),
                SecurityEPPrediction(SecurityEPDomain.RELATIONSHIP, 0.15, 0.80, 0.25, "proceed", "OK"),
                SecurityEPPrediction(SecurityEPDomain.AUTHORIZATION, 0.12, 0.78, 0.22, "proceed", "OK")
            ),
            # Conflict
            (
                SecurityEPPrediction(SecurityEPDomain.GROUNDING, 0.60, 0.75, 0.65, "reject", "Issue"),
                SecurityEPPrediction(SecurityEPDomain.RELATIONSHIP, 0.25, 0.70, 0.35, "proceed", "OK"),
                None
            ),
            # Cascade
            (
                SecurityEPPrediction(SecurityEPDomain.GROUNDING, 0.85, 0.90, 0.90, "reject", "Critical"),
                SecurityEPPrediction(SecurityEPDomain.RELATIONSHIP, 0.80, 0.88, 0.85, "reject", "Critical"),
                SecurityEPPrediction(SecurityEPDomain.AUTHORIZATION, 0.90, 0.92, 0.95, "reject", "Critical")
            ),
            # Adjust
            (
                SecurityEPPrediction(SecurityEPDomain.GROUNDING, 0.45, 0.70, 0.50, "adjust", "Moderate"),
                SecurityEPPrediction(SecurityEPDomain.RELATIONSHIP, 0.50, 0.68, 0.55, "adjust", "Moderate"),
                None
            ),
        ]

        # Reset
        self.coordinator = Web4MultiEPCoordinator()

        # Benchmark
        iterations = 50000
        latencies_ms = []
        decision_counts = {}

        start = time.time()
        for i in range(iterations):
            scenario = scenarios[i % len(scenarios)]

            iter_start = time.perf_counter()

            decision = self.coordinator.coordinate(
                grounding_pred=scenario[0],
                relationship_pred=scenario[1],
                authorization_pred=scenario[2],
                decision_id=f"mixed_{i}"
            )

            iter_end = time.perf_counter()
            latencies_ms.append((iter_end - iter_start) * 1000)

            decision_counts[decision.final_decision] = decision_counts.get(decision.final_decision, 0) + 1

        end = time.time()

        total_time = end - start
        throughput = iterations / total_time
        avg_lat_ms = sum(latencies_ms) / len(latencies_ms)

        stats = self.coordinator.get_stats()
        result = BenchmarkResult(
            test_name="Mixed Scenarios",
            iterations=iterations,
            total_time_seconds=total_time,
            throughput_per_second=throughput,
            avg_latency_ms=avg_lat_ms,
            avg_latency_us=avg_lat_ms * 1000,
            min_latency_ms=min(latencies_ms),
            max_latency_ms=max(latencies_ms),
            notes=(
                f"4 scenario types rotated. "
                f"Decisions: proceed={decision_counts.get('proceed', 0)}, "
                f"adjust={decision_counts.get('adjust', 0)}, "
                f"reject={decision_counts.get('reject', 0)}. "
                f"Cascades: {stats['cascades_detected']}, "
                f"Conflicts: {stats['conflicts_resolved']}"
            )
        )

        self.results.append(result)
        self._print_result(result)
        print()

    def _print_result(self, result: BenchmarkResult):
        """Print benchmark result."""
        print(f"Test: {result.test_name}")
        print(f"Iterations: {result.iterations:,}")
        print(f"Total Time: {result.total_time_seconds:.3f}s")
        print(f"Throughput: {result.throughput_per_second:,.0f} decisions/sec")
        print(f"Avg Latency: {result.avg_latency_ms:.4f}ms ({result.avg_latency_us:.2f} microseconds)")
        print(f"Min Latency: {result.min_latency_ms:.4f}ms")
        print(f"Max Latency: {result.max_latency_ms:.4f}ms")
        if result.notes:
            print(f"Notes: {result.notes}")

    def generate_summary(self) -> Dict:
        """Generate summary report."""
        print("=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)
        print()

        summary = {
            "timestamp": datetime.now().isoformat(),
            "hardware": "Legion RTX 4090",
            "component": "Web4 Multi-EP Security Coordinator",
            "results": [asdict(r) for r in self.results],
            "comparison_to_edge": {
                "edge_hardware": "Jetson Orin Nano 8GB (Sprout)",
                "edge_throughput": 97204,
                "edge_latency_us": 10.29
            }
        }

        print(f"Total Tests: {len(self.results)}")
        print(f"Total Iterations: {sum(r.iterations for r in self.results):,}")
        print(f"Total Time: {sum(r.total_time_seconds for r in self.results):.2f}s")
        print()

        print("Performance Results:")
        print()
        for result in self.results:
            print(f"{result.test_name:30s}: {result.throughput_per_second:>15,.0f} decisions/sec")
            print(f"{'':30s}  {result.avg_latency_us:>15,.2f} microseconds avg")
            print()

        # Calculate average
        avg_throughput = sum(r.throughput_per_second for r in self.results) / len(self.results)
        avg_latency_us = sum(r.avg_latency_us for r in self.results) / len(self.results)

        print(f"{'Average Performance':30s}: {avg_throughput:>15,.0f} decisions/sec")
        print(f"{'':30s}  {avg_latency_us:>15,.2f} microseconds avg")
        print()

        print("Comparison to Edge (Sprout on Jetson Orin Nano):")
        print(f"  Edge Throughput:    97,204 decisions/sec")
        print(f"  Legion Throughput: {avg_throughput:>7,.0f} decisions/sec")
        print(f"  Speedup Factor:    {avg_throughput / 97204:>7.2f}x")
        print()

        print("=" * 80)
        print("✅ BENCHMARK COMPLETE")
        print("=" * 80)

        return summary


if __name__ == "__main__":
    benchmark = CoordinatorBenchmark()
    summary = benchmark.run_all_tests()

    # Save results
    with open("web4_coordinator_benchmark_results.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults saved to: web4_coordinator_benchmark_results.json")
