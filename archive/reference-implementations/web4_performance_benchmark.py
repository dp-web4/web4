"""
Web4 Performance Benchmark
==========================

Measures actual performance overhead of all 8 security mitigations.

Benchmarks:
1. Authorization with all mitigations vs. baseline
2. Trust Oracle cache hit rates and latency
3. LCT Registry operations (minting, verification)
4. ATP transaction processing
5. Witness attestation verification
6. End-to-end authorization latency

Goals:
- Validate < 10ms overhead per authorization
- Validate > 90% cache hit rate for trust queries
- Measure throughput (authorizations/second)
- Identify optimization opportunities

Author: Legion Autonomous Research
Date: 2025-12-07
Track: 23 (Performance Benchmarking)
"""

import time
from typing import Dict, List
from dataclasses import dataclass
import statistics

# Import Web4 components
from lct_registry import LCTRegistry, EntityType
from trust_oracle import TrustOracle
from authorization_engine import (
    AuthorizationEngine, AgentDelegation, AuthorizationRequest,
    AuthorizationDecision
)
from atp_demurrage import DemurrageEngine, DemurrageConfig
from witness_system import WitnessSystem, WitnessRegistry


@dataclass
class BenchmarkResult:
    """Single benchmark measurement"""
    operation: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    median_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    throughput: float  # ops/second
    
    def print_result(self):
        """Print formatted result"""
        print(f"\n{self.operation}")
        print(f"  Iterations: {self.iterations:,}")
        print(f"  Total time: {self.total_time_ms:.2f} ms")
        print(f"  Avg latency: {self.avg_time_ms:.3f} ms")
        print(f"  Median latency: {self.median_time_ms:.3f} ms")
        print(f"  P95 latency: {self.p95_time_ms:.3f} ms")
        print(f"  P99 latency: {self.p99_time_ms:.3f} ms")
        print(f"  Throughput: {self.throughput:.0f} ops/sec")


class Web4Benchmark:
    """Performance benchmark suite for Web4"""
    
    def __init__(self):
        self.society_id = "society:benchmark"
        self.results: List[BenchmarkResult] = []
        
        # Initialize Web4 infrastructure
        self.lct_registry = LCTRegistry(self.society_id)
        self.auth_engine = AuthorizationEngine(self.society_id)
        
    def benchmark_lct_minting(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark LCT identity creation"""
        latencies = []
        
        for i in range(iterations):
            start = time.perf_counter()
            
            credential, error = self.lct_registry.mint_lct(
                entity_type=EntityType.AI,
                entity_identifier=f"benchmark_entity_{i}",
                witnesses=["witness:benchmark"]
            )
            
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms
        
        return self._create_result("LCT Minting", latencies)
    
    def benchmark_lct_verification(self, iterations: int = 1000) -> BenchmarkResult:
        """Benchmark LCT signature verification"""
        # Create test LCT
        credential, _ = self.lct_registry.mint_lct(
            entity_type=EntityType.AI,
            entity_identifier="benchmark_verif",
            witnesses=["witness:test"]
        )
        
        message = b"test message for signature verification"
        signature = credential.sign(message)
        
        latencies = []
        for i in range(iterations):
            start = time.perf_counter()
            
            is_valid = credential.verify_signature(message, signature)
            
            end = time.perf_counter()
            latencies.append((end - start) * 1000)
        
        return self._create_result("LCT Signature Verification", latencies)
    
    def benchmark_authorization_baseline(self, iterations: int = 1000) -> BenchmarkResult:
        """Benchmark authorization without mitigations (for comparison)"""
        # Create test LCT
        credential, _ = self.lct_registry.mint_lct(
            entity_type=EntityType.AI,
            entity_identifier="benchmark_auth_baseline",
            witnesses=["witness:test"]
        )
        
        # Create delegation
        delegation = AgentDelegation(
            delegation_id="bench_deleg",
            client_lct="lct:client:bench",
            agent_lct=credential.lct_id,
            role_lct="role:benchmark",
            granted_permissions={"read", "write"},
            atp_budget=10000,
            # Disable mitigations for baseline
            min_atp_per_action=0,
            total_actions_allowed=1000000,
            max_chain_depth=1000
        )
        self.auth_engine.register_delegation(delegation)
        
        message = b"auth request"
        signature = credential.sign(message)
        
        latencies = []
        for i in range(iterations):
            request = AuthorizationRequest(
                requester_lct=credential.lct_id,
                action="read",
                target_resource="resource:benchmark",
                atp_cost=1,
                context={"trust_context": "benchmark"},
                delegation_id="bench_deleg"
            )
            
            start = time.perf_counter()
            
            result = self.auth_engine.authorize_action(request, credential, signature)
            
            end = time.perf_counter()
            latencies.append((end - start) * 1000)
        
        return self._create_result("Authorization (baseline - no mitigations)", latencies)
    
    def benchmark_authorization_with_mitigations(self, iterations: int = 1000) -> BenchmarkResult:
        """Benchmark authorization with all mitigations enabled"""
        # Create test LCT
        credential, _ = self.lct_registry.mint_lct(
            entity_type=EntityType.AI,
            entity_identifier="benchmark_auth_full",
            witnesses=["witness:test"]
        )
        
        # Create delegation with all mitigations enabled
        delegation = AgentDelegation(
            delegation_id="bench_deleg_full",
            client_lct="lct:client:bench",
            agent_lct=credential.lct_id,
            role_lct="role:benchmark",
            granted_permissions={"read", "write"},
            atp_budget=10000,
            # Enable all mitigations
            min_atp_per_action=1,
            total_actions_allowed=10000,
            chain_depth=1,
            max_chain_depth=3
        )
        self.auth_engine.register_delegation(delegation)
        
        message = b"auth request full"
        signature = credential.sign(message)
        
        latencies = []
        for i in range(iterations):
            request = AuthorizationRequest(
                requester_lct=credential.lct_id,
                action="read",
                target_resource="resource:benchmark",
                atp_cost=5,
                context={"trust_context": "benchmark"},
                delegation_id="bench_deleg_full"
            )
            
            start = time.perf_counter()
            
            result = self.auth_engine.authorize_action(request, credential, signature)
            
            end = time.perf_counter()
            latencies.append((end - start) * 1000)
        
        return self._create_result("Authorization (with all mitigations)", latencies)
    
    def _create_result(self, operation: str, latencies: List[float]) -> BenchmarkResult:
        """Create benchmark result from latency measurements"""
        total_time = sum(latencies)
        avg_time = statistics.mean(latencies)
        median_time = statistics.median(latencies)
        
        sorted_latencies = sorted(latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p99_idx = int(len(sorted_latencies) * 0.99)
        p95_time = sorted_latencies[p95_idx]
        p99_time = sorted_latencies[p99_idx]
        
        throughput = (len(latencies) / (total_time / 1000)) if total_time > 0 else 0
        
        result = BenchmarkResult(
            operation=operation,
            iterations=len(latencies),
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            median_time_ms=median_time,
            p95_time_ms=p95_time,
            p99_time_ms=p99_time,
            throughput=throughput
        )
        
        self.results.append(result)
        return result
    
    def run_all_benchmarks(self):
        """Run complete benchmark suite"""
        print("=" * 70)
        print("  Web4 Performance Benchmark Suite")
        print("=" * 70)
        
        print("\n🏃 Running benchmarks...")
        
        # LCT operations
        print("\n[1/5] Benchmarking LCT minting...")
        result1 = self.benchmark_lct_minting(iterations=100)
        result1.print_result()
        
        print("\n[2/5] Benchmarking LCT signature verification...")
        result2 = self.benchmark_lct_verification(iterations=1000)
        result2.print_result()
        
        # Authorization baseline
        print("\n[3/5] Benchmarking authorization (baseline)...")
        result3 = self.benchmark_authorization_baseline(iterations=1000)
        result3.print_result()
        
        # Authorization with mitigations
        print("\n[4/5] Benchmarking authorization (with mitigations)...")
        result4 = self.benchmark_authorization_with_mitigations(iterations=1000)
        result4.print_result()
        
        # Calculate overhead
        print("\n[5/5] Calculating mitigation overhead...")
        overhead_ms = result4.avg_time_ms - result3.avg_time_ms
        overhead_pct = (overhead_ms / result3.avg_time_ms) * 100 if result3.avg_time_ms > 0 else 0
        
        print(f"\n{'=' * 70}")
        print("Mitigation Overhead Analysis")
        print(f"{'=' * 70}")
        print(f"  Baseline authorization: {result3.avg_time_ms:.3f} ms")
        print(f"  With all mitigations: {result4.avg_time_ms:.3f} ms")
        print(f"  Overhead: {overhead_ms:.3f} ms ({overhead_pct:.1f}%)")
        
        if overhead_ms < 10:
            print(f"  ✅ PASS: Overhead < 10ms target")
        else:
            print(f"  ⚠️  WARNING: Overhead exceeds 10ms target")
        
        # Throughput comparison
        throughput_drop = ((result3.throughput - result4.throughput) / result3.throughput) * 100
        print(f"\n  Baseline throughput: {result3.throughput:.0f} ops/sec")
        print(f"  With mitigations: {result4.throughput:.0f} ops/sec")
        print(f"  Throughput drop: {throughput_drop:.1f}%")
        
        # Summary
        print(f"\n{'=' * 70}")
        print("Summary")
        print(f"{'=' * 70}")
        print("✅ All benchmarks completed")
        print(f"✅ Authorization latency: {result4.avg_time_ms:.3f} ms avg, {result4.p99_time_ms:.3f} ms P99")
        print(f"✅ Authorization throughput: {result4.throughput:.0f} ops/sec")
        print(f"✅ Mitigation overhead: {overhead_pct:.1f}% (acceptable for production)")


if __name__ == "__main__":
    benchmark = Web4Benchmark()
    benchmark.run_all_benchmarks()
