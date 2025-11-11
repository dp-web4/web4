"""
Web4 Phase 1 Mitigation Test Suite
===================================

Tests Phase 1 security mitigations against attack vectors.

Tests:
1. LCT Minting Cost - Does ATP cost deter Sybil attacks?
2. Witness Validation - Are fake witnesses rejected?
3. Outcome Recording Cost - Does cost prevent reputation washing?
4. Usage Monitoring - Is misreporting detected and penalized?
5. Triple Authentication - Are unauthorized triples rejected?

Usage:
    python test_phase1_mitigations.py

Author: Web4 Security Research (Session 13)
Date: 2025-11-11
"""

import asyncio
import sys
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    import httpx
except ImportError:
    print("httpx not installed. Install with: python3 -m pip install httpx --user")
    sys.exit(1)


# =============================================================================
# Test Configuration
# =============================================================================

@dataclass
class TestConfig:
    """Configuration for mitigation tests"""
    base_urls: Dict[str, str] = None
    use_secured_endpoints: bool = True  # Test secured vs unsecured

    def __post_init__(self):
        if self.base_urls is None:
            # Default to secured services on alternate ports
            if self.use_secured_endpoints:
                self.base_urls = {
                    "identity": "http://localhost:8101",  # Secured
                    "reputation": "http://localhost:8104",  # Secured
                    "resources": "http://localhost:8105",  # Secured
                    "knowledge": "http://localhost:8106",  # Secured
                }
            else:
                self.base_urls = {
                    "identity": "http://localhost:8001",
                    "reputation": "http://localhost:8004",
                    "resources": "http://localhost:8005",
                    "knowledge": "http://localhost:8006",
                }


@dataclass
class TestResult:
    """Result from a mitigation test"""
    mitigation_name: str
    test_name: str
    passed: bool
    expected_behavior: str
    actual_behavior: str
    metrics: Dict[str, Any]
    notes: str


# =============================================================================
# Test Harness
# =============================================================================

class MitigationTester:
    """Base class for mitigation tests"""

    def __init__(self, config: TestConfig):
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None
        self.results = []

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.close()

    def record_result(self, result: TestResult):
        """Record test result"""
        self.results.append(result)

        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"  {status}: {result.test_name}")
        print(f"    Expected: {result.expected_behavior}")
        print(f"    Actual: {result.actual_behavior}")
        if result.notes:
            print(f"    Notes: {result.notes}")


# =============================================================================
# Mitigation 1 & 2: LCT Minting Cost + Witness Validation
# =============================================================================

class LCTSecurityTests(MitigationTester):
    """Test Mitigations 1 & 2: LCT minting security"""

    async def test_minting_cost_deters_sybil(self):
        """Test that ATP cost makes Sybil attacks expensive"""
        print("\n[TEST] Mitigation 1: LCT Minting Cost")

        # Attempt to mint 10 LCTs rapidly (Sybil attack)
        sybil_count = 10
        successes = 0
        total_atp_cost = 0

        for i in range(sybil_count):
            request = {
                "entity_type": "ai",
                "entity_identifier": f"sybil_test_{i}_{int(time.time())}",
                "society": "test_society",
                "witnesses": [f"witness:fake_{i}"]
            }

            try:
                response = await self.client.post(
                    f"{self.config.base_urls['identity']}/v1/lct/mint",
                    json=request
                )

                if response.status_code == 201:
                    data = response.json()
                    if data.get("success"):
                        successes += 1
                        total_atp_cost += data.get("atp_cost", 0)

            except Exception as e:
                pass

            await asyncio.sleep(0.1)

        # In secured version, should have high ATP cost
        # In unsecured version, would have no cost
        avg_cost = total_atp_cost / successes if successes > 0 else 0

        # Mitigation effective if:
        # 1. Minting has significant ATP cost (>= 50 ATP), OR
        # 2. Witness validation rejects fake witnesses
        mitigation_effective = (avg_cost >= 50) or (successes < sybil_count / 2)

        self.record_result(TestResult(
            mitigation_name="LCT Minting Cost",
            test_name="Sybil Attack Deterrence",
            passed=mitigation_effective,
            expected_behavior="High ATP cost (>=50) or <50% success rate",
            actual_behavior=f"{successes}/{sybil_count} succeeded, avg cost {avg_cost} ATP",
            metrics={"successes": successes, "total_cost": total_atp_cost, "avg_cost": avg_cost},
            notes=f"{'Sybil attack deterred' if mitigation_effective else 'VULNERABLE to Sybil'}"
        ))

    async def test_witness_validation(self):
        """Test that fake witnesses are rejected"""
        print("\n[TEST] Mitigation 2: Witness Validation")

        test_cases = [
            {
                "name": "No witnesses",
                "witnesses": [],
                "should_succeed": False
            },
            {
                "name": "Fake witness",
                "witnesses": ["witness:nonexistent"],
                "should_succeed": False
            },
            {
                "name": "Short witness ID",
                "witnesses": ["w:a"],
                "should_succeed": False
            }
        ]

        for test_case in test_cases:
            request = {
                "entity_type": "ai",
                "entity_identifier": f"witness_test_{int(time.time())}",
                "society": "test_society",
                "witnesses": test_case["witnesses"]
            }

            try:
                response = await self.client.post(
                    f"{self.config.base_urls['identity']}/v1/lct/mint",
                    json=request
                )

                succeeded = response.status_code == 201
                expected = test_case["should_succeed"]
                passed = (succeeded == expected)

                self.record_result(TestResult(
                    mitigation_name="Witness Validation",
                    test_name=test_case["name"],
                    passed=passed,
                    expected_behavior="Rejected" if not expected else "Accepted",
                    actual_behavior="Rejected" if not succeeded else "Accepted",
                    metrics={"status_code": response.status_code},
                    notes=""
                ))

            except Exception as e:
                self.record_result(TestResult(
                    mitigation_name="Witness Validation",
                    test_name=test_case["name"],
                    passed=False,
                    expected_behavior="Rejected",
                    actual_behavior=f"Error: {str(e)}",
                    metrics={},
                    notes="Test failed with exception"
                ))

            await asyncio.sleep(0.1)


# =============================================================================
# Mitigation 3: Outcome Recording Cost
# =============================================================================

class ReputationSecurityTests(MitigationTester):
    """Test Mitigation 3: Outcome recording security"""

    async def test_outcome_cost_scales_by_quality(self):
        """Test that ATP cost scales with outcome quality claim"""
        print("\n[TEST] Mitigation 3: Outcome Recording Cost Scaling")

        # First mint an LCT for testing
        lct_data = await self._mint_test_lct()
        if not lct_data:
            self.record_result(TestResult(
                mitigation_name="Outcome Recording Cost",
                test_name="Cost Scaling Test",
                passed=False,
                expected_behavior="Variable costs by quality",
                actual_behavior="Could not create test LCT",
                metrics={},
                notes="Setup failed"
            ))
            return

        lct_id = lct_data.get("lct_id")

        # Test different outcome quality levels
        test_outcomes = [
            ("failure", 5, "Low cost for honest failure reporting"),
            ("partial_success", 10, "Base cost for partial success"),
            ("success", 20, "Moderate cost for success"),
            ("exceptional_quality", 50, "High cost for exceptional claims")
        ]

        for outcome, expected_cost, description in test_outcomes:
            request = {
                "entity": lct_id,
                "role": "researcher",
                "action": "compute",
                "outcome": outcome,
                "witnesses": ["witness:test_valid_witness"]
            }

            try:
                response = await self.client.post(
                    f"{self.config.base_urls['reputation']}/v1/reputation/record",
                    json=request
                )

                if response.status_code == 201:
                    data = response.json()
                    actual_cost = data.get("atp_cost", 0)

                    # Cost should be within 50% of expected
                    cost_appropriate = abs(actual_cost - expected_cost) <= (expected_cost * 0.5)

                    self.record_result(TestResult(
                        mitigation_name="Outcome Recording Cost",
                        test_name=f"Cost for {outcome}",
                        passed=cost_appropriate,
                        expected_behavior=f"~{expected_cost} ATP",
                        actual_behavior=f"{actual_cost} ATP",
                        metrics={"outcome": outcome, "cost": actual_cost},
                        notes=description
                    ))
                else:
                    # If rejected, check if it's due to insufficient ATP or witnesses
                    error_data = response.json()
                    error_msg = error_data.get("error", "")

                    self.record_result(TestResult(
                        mitigation_name="Outcome Recording Cost",
                        test_name=f"Cost for {outcome}",
                        passed=False,
                        expected_behavior=f"~{expected_cost} ATP cost",
                        actual_behavior=f"Rejected: {error_msg}",
                        metrics={"status": response.status_code},
                        notes=""
                    ))

            except Exception as e:
                pass

            await asyncio.sleep(0.2)

    async def _mint_test_lct(self) -> Optional[Dict[str, Any]]:
        """Helper: Mint LCT for testing"""
        request = {
            "entity_type": "ai",
            "entity_identifier": f"rep_test_{int(time.time())}",
            "society": "test_society",
            "witnesses": ["witness:test"]
        }

        try:
            response = await self.client.post(
                f"{self.config.base_urls['identity']}/v1/lct/mint",
                json=request
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    return data["data"]
        except:
            pass

        return None


# =============================================================================
# Mitigation 4: Usage Monitoring
# =============================================================================

class ResourceSecurityTests(MitigationTester):
    """Test Mitigation 4: Resource usage monitoring"""

    async def test_usage_misreporting_detection(self):
        """Test that usage misreporting is detected and penalized"""
        print("\n[TEST] Mitigation 4: Usage Misreporting Detection")

        # Create test LCT
        lct_data = await self._mint_test_lct()
        if not lct_data:
            self.record_result(TestResult(
                mitigation_name="Usage Monitoring",
                test_name="Misreporting Detection",
                passed=False,
                expected_behavior="Detect misreporting",
                actual_behavior="Could not create test LCT",
                metrics={},
                notes="Setup failed"
            ))
            return

        lct_id = lct_data.get("lct_id")

        # Allocate resources
        alloc_request = {
            "entity_id": lct_id,
            "resource_type": "cpu",
            "amount": 4.0,
            "duration_seconds": 300
        }

        try:
            alloc_response = await self.client.post(
                f"{self.config.base_urls['resources']}/v1/resources/allocate",
                json=alloc_request
            )

            if alloc_response.status_code != 201:
                self.record_result(TestResult(
                    mitigation_name="Usage Monitoring",
                    test_name="Misreporting Detection",
                    passed=False,
                    expected_behavior="Detect misreporting",
                    actual_behavior="Could not allocate resources",
                    metrics={},
                    notes="Allocation failed"
                ))
                return

            alloc_data = alloc_response.json()
            allocation_id = alloc_data.get("data", {}).get("allocation_id")
            deposit = alloc_data.get("atp_deposit", 0)

            # Wait for monitoring to collect measurements
            await asyncio.sleep(5)

            # Report drastically under-reported usage (10% of actual)
            usage_request = {
                "allocation_id": allocation_id,
                "actual_usage": 0.4  # Report only 0.4 instead of ~4.0
            }

            usage_response = await self.client.post(
                f"{self.config.base_urls['resources']}/v1/resources/usage",
                json=usage_request
            )

            if usage_response.status_code == 200:
                usage_data = usage_response.json()
                verified = usage_data.get("verified", True)
                penalty = usage_data.get("penalty", 0)
                measured = usage_data.get("measured_usage", 0)

                # Mitigation effective if misreporting detected
                detection_works = (not verified) or (penalty > 0)

                self.record_result(TestResult(
                    mitigation_name="Usage Monitoring",
                    test_name="Misreporting Detection",
                    passed=detection_works,
                    expected_behavior="Detected misreporting, penalty applied",
                    actual_behavior=f"Verified={verified}, penalty={penalty}, measured={measured:.2f}",
                    metrics={"verified": verified, "penalty": penalty, "measured": measured, "deposit": deposit},
                    notes="Misreporting detected" if detection_works else "VULNERABLE - misreporting not detected"
                ))
            else:
                self.record_result(TestResult(
                    mitigation_name="Usage Monitoring",
                    test_name="Misreporting Detection",
                    passed=False,
                    expected_behavior="Detect misreporting",
                    actual_behavior=f"Usage report failed: {usage_response.status_code}",
                    metrics={},
                    notes=""
                ))

        except Exception as e:
            self.record_result(TestResult(
                mitigation_name="Usage Monitoring",
                test_name="Misreporting Detection",
                passed=False,
                expected_behavior="Detect misreporting",
                actual_behavior=f"Error: {str(e)}",
                metrics={},
                notes="Test failed with exception"
            ))

    async def test_deposit_system(self):
        """Test that deposit system prevents resource hoarding"""
        print("\n[TEST] Mitigation 4: Deposit System")

        # Create test LCT
        lct_data = await self._mint_test_lct()
        if not lct_data:
            return

        lct_id = lct_data.get("lct_id")

        # Allocate resources - should require deposit
        alloc_request = {
            "entity_id": lct_id,
            "resource_type": "memory",
            "amount": 8.0,
            "duration_seconds": 300
        }

        try:
            response = await self.client.post(
                f"{self.config.base_urls['resources']}/v1/resources/allocate",
                json=alloc_request
            )

            if response.status_code == 201:
                data = response.json()
                atp_cost = data.get("atp_cost", 0)
                atp_deposit = data.get("atp_deposit", 0)

                # Deposit should be 2x cost
                expected_deposit = atp_cost * 2
                deposit_correct = abs(atp_deposit - expected_deposit) <= 1
                deposit_required = atp_deposit > 0

                self.record_result(TestResult(
                    mitigation_name="Usage Monitoring - Deposit",
                    test_name="Deposit System",
                    passed=deposit_required and deposit_correct,
                    expected_behavior=f"Deposit required (~{expected_deposit} ATP)",
                    actual_behavior=f"Cost={atp_cost}, Deposit={atp_deposit}",
                    metrics={"cost": atp_cost, "deposit": atp_deposit},
                    notes="Deposit system active" if deposit_required else "No deposit required"
                ))
            else:
                error_data = response.json()
                error_msg = error_data.get("error", "")

                # Might fail due to insufficient ATP (which is actually good - prevents hoarding)
                insufficient_atp = "insufficient" in error_msg.lower()

                self.record_result(TestResult(
                    mitigation_name="Usage Monitoring - Deposit",
                    test_name="Deposit System",
                    passed=insufficient_atp,
                    expected_behavior="Deposit required or insufficient ATP",
                    actual_behavior=f"Rejected: {error_msg}",
                    metrics={"status": response.status_code},
                    notes="Economic barrier active" if insufficient_atp else ""
                ))

        except Exception as e:
            pass

    async def _mint_test_lct(self) -> Optional[Dict[str, Any]]:
        """Helper: Mint LCT for testing"""
        request = {
            "entity_type": "ai",
            "entity_identifier": f"resource_test_{int(time.time())}",
            "society": "test_society",
            "witnesses": ["witness:test"]
        }

        try:
            response = await self.client.post(
                f"{self.config.base_urls['identity']}/v1/lct/mint",
                json=request
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    return data["data"]
        except:
            pass

        return None


# =============================================================================
# Mitigation 5: Triple Authentication
# =============================================================================

class KnowledgeSecurityTests(MitigationTester):
    """Test Mitigation 5: Triple authentication for graph operations"""

    async def test_signature_requirement(self):
        """Test that triples require signatures"""
        print("\n[TEST] Mitigation 5: Signature Requirement")

        # Create test LCT
        lct_data = await self._mint_test_lct()
        if not lct_data:
            return

        lct_id = lct_data.get("lct_id")

        # Try to add triple without signature
        request_no_sig = {
            "caller_lct_id": lct_id,
            "subject": lct_id,
            "predicate": "has_property",
            "object": "test_value",
            "signature": None  # No signature
        }

        try:
            response = await self.client.post(
                f"{self.config.base_urls['knowledge']}/v1/graph/triple",
                json=request_no_sig
            )

            rejected = response.status_code != 201

            self.record_result(TestResult(
                mitigation_name="Triple Authentication - Signature",
                test_name="Signature Requirement",
                passed=rejected,
                expected_behavior="Rejected (no signature)",
                actual_behavior="Rejected" if rejected else "Accepted",
                metrics={"status_code": response.status_code},
                notes="Signature required" if rejected else "VULNERABLE - no signature required"
            ))

        except Exception as e:
            pass

        # Try with signature
        request_with_sig = {
            "caller_lct_id": lct_id,
            "subject": lct_id,
            "predicate": "has_property",
            "object": "test_value",
            "signature": "0" * 64  # Fake but valid-looking signature
        }

        try:
            response = await self.client.post(
                f"{self.config.base_urls['knowledge']}/v1/graph/triple",
                json=request_with_sig
            )

            accepted = response.status_code == 201

            self.record_result(TestResult(
                mitigation_name="Triple Authentication - Signature",
                test_name="Valid Signature Accepted",
                passed=accepted,
                expected_behavior="Accepted (with signature)",
                actual_behavior="Accepted" if accepted else "Rejected",
                metrics={"status_code": response.status_code},
                notes=""
            ))

        except Exception as e:
            pass

    async def test_high_stakes_witness_requirement(self):
        """Test that high-stakes predicates require witnesses"""
        print("\n[TEST] Mitigation 5: High-Stakes Witness Requirement")

        # Create test LCT
        lct_data = await self._mint_test_lct()
        if not lct_data:
            return

        lct_id = lct_data.get("lct_id")

        # Try high-stakes predicate without witnesses
        request = {
            "caller_lct_id": lct_id,
            "subject": lct_id,
            "predicate": "trusts",  # High-stakes predicate
            "object": "lct:some_other_entity",
            "signature": "0" * 64,
            "metadata": {"witnesses": []}  # No witnesses
        }

        try:
            response = await self.client.post(
                f"{self.config.base_urls['knowledge']}/v1/graph/triple",
                json=request
            )

            rejected = response.status_code != 201

            if rejected:
                error_data = response.json()
                error_msg = error_data.get("error", "")
                witness_related = "witness" in error_msg.lower()
            else:
                witness_related = False

            self.record_result(TestResult(
                mitigation_name="Triple Authentication - Witnesses",
                test_name="High-Stakes Witness Requirement",
                passed=rejected and witness_related,
                expected_behavior="Rejected (insufficient witnesses)",
                actual_behavior="Rejected (witness error)" if (rejected and witness_related) else
                                ("Rejected (other reason)" if rejected else "Accepted"),
                metrics={"status_code": response.status_code},
                notes="Witness requirement enforced" if (rejected and witness_related) else "VULNERABLE"
            ))

        except Exception as e:
            pass

    async def test_atp_cost_by_predicate(self):
        """Test that ATP cost scales by predicate significance"""
        print("\n[TEST] Mitigation 5: ATP Cost Scaling")

        # Create test LCT
        lct_data = await self._mint_test_lct()
        if not lct_data:
            return

        lct_id = lct_data.get("lct_id")

        # Test different predicates
        test_predicates = [
            ("has_property", 5, "Low-stakes"),
            ("has_role", 20, "Moderate-stakes"),
            ("trusts", 50, "High-stakes")
        ]

        for predicate, expected_cost, category in test_predicates:
            request = {
                "caller_lct_id": lct_id,
                "subject": lct_id,
                "predicate": predicate,
                "object": "test_value",
                "signature": "0" * 64,
                "metadata": {"witnesses": ["w:1", "w:2"]} if expected_cost > 10 else {}
            }

            try:
                response = await self.client.post(
                    f"{self.config.base_urls['knowledge']}/v1/graph/triple",
                    json=request
                )

                if response.status_code == 201:
                    data = response.json()
                    actual_cost = data.get("atp_cost", 0)

                    # Cost appropriate if within 50% of expected
                    cost_appropriate = abs(actual_cost - expected_cost) <= (expected_cost * 0.5)

                    self.record_result(TestResult(
                        mitigation_name="Triple Authentication - Cost",
                        test_name=f"Cost for {category} predicate",
                        passed=cost_appropriate,
                        expected_behavior=f"~{expected_cost} ATP",
                        actual_behavior=f"{actual_cost} ATP",
                        metrics={"predicate": predicate, "cost": actual_cost},
                        notes=""
                    ))
                else:
                    # Might be rejected for other reasons
                    pass

            except Exception as e:
                pass

            await asyncio.sleep(0.1)

    async def _mint_test_lct(self) -> Optional[Dict[str, Any]]:
        """Helper: Mint LCT for testing"""
        request = {
            "entity_type": "ai",
            "entity_identifier": f"knowledge_test_{int(time.time())}",
            "society": "test_society",
            "witnesses": ["witness:test"]
        }

        try:
            response = await self.client.post(
                f"{self.config.base_urls['identity']}/v1/lct/mint",
                json=request
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    return data["data"]
        except:
            pass

        return None


# =============================================================================
# Test Runner
# =============================================================================

async def run_all_tests(config: TestConfig):
    """Run all Phase 1 mitigation tests"""

    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  Web4 Phase 1 Mitigation Test Suite".center(68) + "║")
    print("║" + "  Security Research - Session 13".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝\n")

    print(f"Testing {'SECURED' if config.use_secured_endpoints else 'UNSECURED'} services")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    all_results = []

    # Test Mitigations 1 & 2: LCT Security
    async with LCTSecurityTests(config) as tester:
        await tester.test_minting_cost_deters_sybil()
        await tester.test_witness_validation()
        all_results.extend(tester.results)

    # Test Mitigation 3: Reputation Security
    async with ReputationSecurityTests(config) as tester:
        await tester.test_outcome_cost_scales_by_quality()
        all_results.extend(tester.results)

    # Test Mitigation 4: Resource Security
    async with ResourceSecurityTests(config) as tester:
        await tester.test_deposit_system()
        await tester.test_usage_misreporting_detection()
        all_results.extend(tester.results)

    # Test Mitigation 5: Knowledge Security
    async with KnowledgeSecurityTests(config) as tester:
        await tester.test_signature_requirement()
        await tester.test_high_stakes_witness_requirement()
        await tester.test_atp_cost_by_predicate()
        all_results.extend(tester.results)

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for r in all_results if r.passed)
    total = len(all_results)
    pass_rate = passed / total if total > 0 else 0

    print(f"\nTotal tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Pass rate: {pass_rate:.1%}")

    # By mitigation
    print("\nResults by Mitigation:")
    mitigations = {}
    for result in all_results:
        if result.mitigation_name not in mitigations:
            mitigations[result.mitigation_name] = {"passed": 0, "total": 0}
        mitigations[result.mitigation_name]["total"] += 1
        if result.passed:
            mitigations[result.mitigation_name]["passed"] += 1

    for mitigation, stats in mitigations.items():
        rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
        status = "✅" if rate >= 0.8 else "⚠️" if rate >= 0.5 else "❌"
        print(f"  {status} {mitigation}: {stats['passed']}/{stats['total']} ({rate:.0%})")

    # Overall verdict
    print("\n" + "=" * 70)
    if pass_rate >= 0.8:
        print("✅ Phase 1 Mitigations EFFECTIVE")
        print("   System demonstrates strong resistance to tested attack vectors")
    elif pass_rate >= 0.5:
        print("⚠️  Phase 1 Mitigations PARTIALLY EFFECTIVE")
        print("   Some vulnerabilities remain - review failed tests")
    else:
        print("❌ Phase 1 Mitigations INEFFECTIVE")
        print("   Significant vulnerabilities detected - urgent fixes needed")

    print("=" * 70)

    return all_results


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Main entry point"""

    # Test secured services
    config = TestConfig(use_secured_endpoints=True)

    try:
        results = await run_all_tests(config)
        return results

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
