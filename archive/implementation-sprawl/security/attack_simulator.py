"""
Web4 Attack Simulation Framework
=================================

Test security vulnerabilities and validate mitigations for Web4 services.

This framework simulates attacks discovered in the attack vector analysis
and provides metrics on:
- Attack success rate
- Resource impact
- Detection capabilities
- Mitigation effectiveness

Usage:
    python attack_simulator.py --attack sybil --services http://localhost:8001

Author: Web4 Security Research (Session 11)
Date: 2025-11-10
"""

import asyncio
import sys
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random
import string

try:
    import httpx
except ImportError:
    print("httpx not installed. Install with: python3 -m pip install httpx --user")
    sys.exit(1)


# =============================================================================
# Attack Types
# =============================================================================

class AttackType(Enum):
    """Enumeration of attack types from attack vector analysis"""
    SYBIL_IDENTITY = "sybil_identity"
    REPUTATION_WASHING = "reputation_washing"
    REPUTATION_SYBIL = "reputation_sybil"
    ATP_DRAINING = "atp_draining"
    RESOURCE_HOARDING = "resource_hoarding"
    GRAPH_POISONING = "graph_poisoning"
    TRUST_ECLIPSE = "trust_eclipse"
    MULTI_STAGE_ESCALATION = "multi_stage_escalation"


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class AttackConfig:
    """Configuration for attack simulation"""
    attack_type: AttackType
    sybil_count: int = 10  # Number of fake identities to create
    attack_duration: int = 60  # Seconds
    request_rate: float = 1.0  # Requests per second
    base_urls: Dict[str, str] = field(default_factory=lambda: {
        "identity": "http://localhost:8001",
        "governance": "http://localhost:8002",
        "authorization": "http://localhost:8003",
        "reputation": "http://localhost:8004",
        "resources": "http://localhost:8005",
        "knowledge": "http://localhost:8006"
    })


@dataclass
class AttackResult:
    """Results from attack simulation"""
    attack_type: AttackType
    success: bool
    metrics: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    detection_triggered: bool
    mitigation_effective: bool
    notes: str


# =============================================================================
# Base Attack Simulator
# =============================================================================

class AttackSimulator:
    """Base class for attack simulations"""

    def __init__(self, config: AttackConfig):
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None
        self.metrics = {
            "requests_sent": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "resources_allocated": 0,
            "atp_consumed": 0,
            "identities_created": 0,
            "reputation_gained": 0.0,
            "errors": []
        }
        self.timeline = []
        self.start_time = None
        self.entities = []

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
        self.start_time = time.time()
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.close()

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log attack event to timeline"""
        self.timeline.append({
            "timestamp": time.time() - self.start_time,
            "event_type": event_type,
            "data": data
        })

    async def run(self) -> AttackResult:
        """Run the attack simulation (override in subclasses)"""
        raise NotImplementedError("Subclasses must implement run()")


# =============================================================================
# Sybil Identity Attack
# =============================================================================

class SybilIdentityAttack(AttackSimulator):
    """
    Attack A1: Create multiple fake identities to gain disproportionate influence

    Simulates an attacker creating many LCTs with fake witnesses to:
    - Amplify voting power
    - Inflate reputation through self-attestation
    - Manipulate resource allocation
    """

    async def run(self) -> AttackResult:
        """Execute Sybil identity attack"""
        print(f"\n[ATTACK] Sybil Identity Attack - Creating {self.config.sybil_count} fake LCTs...")

        # Create attacker-controlled society
        society = f"attacker_society_{self._random_id()}"

        # Mint multiple fake LCTs
        for i in range(self.config.sybil_count):
            try:
                lct_data = await self._mint_fake_lct(
                    entity_identifier=f"fake_agent_{i}_{self._random_id()}",
                    society=society
                )

                if lct_data:
                    self.entities.append(lct_data)
                    self.metrics["identities_created"] += 1
                    self.log_event("lct_minted", {"lct_id": lct_data["lct_id"]})
                    print(f"  ✓ Created LCT {i+1}/{self.config.sybil_count}: {lct_data['lct_id'][:40]}...")

                # Rate limiting
                await asyncio.sleep(1.0 / self.config.request_rate)

            except Exception as e:
                self.metrics["requests_failed"] += 1
                self.metrics["errors"].append(str(e))
                print(f"  ✗ Failed to create LCT {i+1}: {e}")

        # Analyze success
        success_rate = self.metrics["identities_created"] / self.config.sybil_count
        attack_successful = success_rate > 0.5  # More than 50% succeeded

        result = AttackResult(
            attack_type=AttackType.SYBIL_IDENTITY,
            success=attack_successful,
            metrics=self.metrics.copy(),
            timeline=self.timeline.copy(),
            detection_triggered=False,  # Would need monitoring system to detect
            mitigation_effective=not attack_successful,
            notes=f"Created {self.metrics['identities_created']} fake identities. "
                  f"Success rate: {success_rate:.1%}. "
                  f"{'VULNERABLE' if attack_successful else 'MITIGATED'}"
        )

        return result

    async def _mint_fake_lct(self, entity_identifier: str, society: str) -> Optional[Dict[str, Any]]:
        """Mint a fake LCT with fabricated witness"""
        request = {
            "entity_type": "ai",
            "entity_identifier": entity_identifier,
            "society": society,
            "witnesses": [f"witness:fake_supervisor_{self._random_id()}"]  # Fake witness
        }

        self.metrics["requests_sent"] += 1

        try:
            response = await self.client.post(
                f"{self.config.base_urls['identity']}/v1/lct/mint",
                json=request
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    self.metrics["requests_successful"] += 1
                    return data["data"]

            self.metrics["requests_failed"] += 1
            return None

        except Exception as e:
            self.metrics["requests_failed"] += 1
            self.metrics["errors"].append(f"LCT mint failed: {e}")
            return None

    def _random_id(self, length: int = 8) -> str:
        """Generate random ID"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


# =============================================================================
# Reputation Washing Attack
# =============================================================================

class ReputationWashingAttack(AttackSimulator):
    """
    Attack B1: Manipulate T3/V3 scores through coordinated fake activity

    Simulates collusive mutual attestation where multiple attacker-controlled
    entities attest to each other's fake high-quality outcomes.
    """

    async def run(self) -> AttackResult:
        """Execute reputation washing attack"""
        print(f"\n[ATTACK] Reputation Washing - Inflating reputation through collusion...")

        # Phase 1: Create Sybil network for reputation washing
        print("  Phase 1: Creating Sybil network...")
        society = f"collusion_network_{self._random_id()}"

        for i in range(min(self.config.sybil_count, 5)):  # Limit to 5 for demo
            try:
                lct_data = await self._mint_lct(f"colluder_{i}", society)
                if lct_data:
                    self.entities.append(lct_data)
                    self.metrics["identities_created"] += 1
                    print(f"    ✓ Created colluder {i+1}")

                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"    ✗ Failed to create colluder {i+1}: {e}")

        if len(self.entities) < 2:
            return AttackResult(
                attack_type=AttackType.REPUTATION_WASHING,
                success=False,
                metrics=self.metrics,
                timeline=self.timeline,
                detection_triggered=False,
                mitigation_effective=True,
                notes="Failed to create enough identities for collusion"
            )

        # Phase 2: Cross-attest fake exceptional outcomes
        print(f"  Phase 2: Cross-attesting fake outcomes...")
        rounds = 5  # Number of attestation rounds

        for round_num in range(rounds):
            for entity_a in self.entities:
                # Pick random colluders as witnesses
                witnesses = random.sample(
                    [e["lct_id"] for e in self.entities if e != entity_a],
                    min(2, len(self.entities) - 1)
                )

                try:
                    outcome_data = await self._record_fake_outcome(
                        entity=entity_a["lct_id"],
                        witnesses=witnesses
                    )

                    if outcome_data:
                        delta_t3 = outcome_data.get("t3_delta", 0)
                        delta_v3 = outcome_data.get("v3_delta", 0)
                        self.metrics["reputation_gained"] += (delta_t3 + delta_v3) / 2
                        self.log_event("reputation_gained", {
                            "entity": entity_a["lct_id"],
                            "t3_delta": delta_t3,
                            "v3_delta": delta_v3
                        })
                        print(f"    ✓ Round {round_num+1}: +{delta_t3:.3f} T3, +{delta_v3:.3f} V3")

                    await asyncio.sleep(0.5)

                except Exception as e:
                    print(f"    ✗ Failed to record outcome: {e}")

        # Phase 3: Verify inflated reputation
        print(f"  Phase 3: Verifying reputation inflation...")
        final_scores = []

        for entity in self.entities:
            try:
                rep_data = await self._get_reputation(entity["lct_id"])
                if rep_data:
                    t3 = rep_data.get("t3_score", 0)
                    v3 = rep_data.get("v3_score", 0)
                    final_scores.append((t3, v3))
                    print(f"    Entity {entity['lct_id'][:40]}... T3={t3:.3f}, V3={v3:.3f}")
            except Exception as e:
                print(f"    ✗ Failed to get reputation: {e}")

        # Attack successful if average score increased significantly
        avg_score = sum(sum(scores) / 2 for scores in final_scores) / len(final_scores) if final_scores else 0
        attack_successful = avg_score > 0.3  # Threshold for "significant" gain

        result = AttackResult(
            attack_type=AttackType.REPUTATION_WASHING,
            success=attack_successful,
            metrics=self.metrics,
            timeline=self.timeline,
            detection_triggered=False,
            mitigation_effective=not attack_successful,
            notes=f"Average reputation score: {avg_score:.3f}. "
                  f"{'VULNERABLE - Collusion successful' if attack_successful else 'MITIGATED'}"
        )

        return result

    async def _mint_lct(self, entity_id: str, society: str) -> Optional[Dict[str, Any]]:
        """Mint LCT for collusion network"""
        request = {
            "entity_type": "ai",
            "entity_identifier": entity_id,
            "society": society,
            "witnesses": [f"witness:fake_{self._random_id()}"]
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
            return None
        except:
            return None

    async def _record_fake_outcome(self, entity: str, witnesses: List[str]) -> Optional[Dict[str, Any]]:
        """Record fake exceptional outcome with collusive witnesses"""
        request = {
            "entity": entity,
            "role": "researcher",
            "action": "compute",
            "outcome": "exceptional_quality",  # Always claim best outcome
            "witnesses": witnesses,
            "context": {"fake_task": True, "attack": "reputation_washing"}
        }

        try:
            response = await self.client.post(
                f"{self.config.base_urls['reputation']}/v1/reputation/record",
                json=request
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    return data["data"]
            return None
        except:
            return None

    async def _get_reputation(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get reputation scores for entity"""
        try:
            response = await self.client.get(
                f"{self.config.base_urls['reputation']}/v1/reputation/{entity_id}",
                params={"role": "researcher"}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data["data"]
            return None
        except:
            return None

    def _random_id(self, length: int = 8) -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


# =============================================================================
# ATP Draining Attack
# =============================================================================

class ATPDrainingAttack(AttackSimulator):
    """
    Attack C1: Exhaust ATP resources through legitimate-looking requests

    Simulates repeatedly requesting maximum resources and under-reporting
    actual usage to get refunds, fragmenting resource pools.
    """

    async def run(self) -> AttackResult:
        """Execute ATP draining attack"""
        print(f"\n[ATTACK] ATP Draining - Exhausting resources through over-allocation...")

        # Create attacker identity
        attacker_lct = await self._mint_attacker_lct()
        if not attacker_lct:
            return AttackResult(
                attack_type=AttackType.ATP_DRAINING,
                success=False,
                metrics=self.metrics,
                timeline=self.timeline,
                detection_triggered=False,
                mitigation_effective=True,
                notes="Failed to create attacker identity"
            )

        print(f"  Attacker LCT: {attacker_lct['lct_id'][:50]}...")

        # Repeatedly allocate maximum resources
        allocation_rounds = 10
        allocations = []

        for round_num in range(allocation_rounds):
            try:
                # Request maximum CPU
                alloc_data = await self._allocate_resources(
                    entity_id=attacker_lct["lct_id"],
                    resource_type="cpu",
                    amount=16.0,  # Request maximum
                    duration_seconds=3600
                )

                if alloc_data:
                    allocations.append(alloc_data)
                    atp_cost = alloc_data.get("atp_cost", 0)
                    self.metrics["resources_allocated"] += alloc_data.get("amount_allocated", 0)
                    self.metrics["atp_consumed"] += atp_cost
                    self.log_event("resource_allocated", alloc_data)
                    print(f"    ✓ Round {round_num+1}: Allocated {alloc_data.get('amount_allocated', 0)} CPU cores, "
                          f"ATP cost: {atp_cost}")

                    # Immediately report minimal usage to get refund
                    if alloc_data.get("allocation_id"):
                        refund = await self._report_minimal_usage(
                            allocation_id=alloc_data["allocation_id"],
                            actual_usage=0.1  # Claim only 0.1 CPU used
                        )
                        if refund:
                            print(f"    ✓ Claimed refund for under-utilization")

                await asyncio.sleep(1.0)

            except Exception as e:
                print(f"    ✗ Allocation failed: {e}")
                self.metrics["errors"].append(str(e))

        # Attack successful if we allocated significant resources
        attack_successful = self.metrics["resources_allocated"] > 50.0  # More than 50 CPU-hours

        result = AttackResult(
            attack_type=AttackType.ATP_DRAINING,
            success=attack_successful,
            metrics=self.metrics,
            timeline=self.timeline,
            detection_triggered=False,
            mitigation_effective=not attack_successful,
            notes=f"Allocated {self.metrics['resources_allocated']:.1f} total CPU cores. "
                  f"ATP consumed: {self.metrics['atp_consumed']}. "
                  f"{'VULNERABLE - Resource drain successful' if attack_successful else 'MITIGATED'}"
        )

        return result

    async def _mint_attacker_lct(self) -> Optional[Dict[str, Any]]:
        """Create attacker LCT"""
        request = {
            "entity_type": "ai",
            "entity_identifier": f"drainer_{self._random_id()}",
            "society": "attacker_society",
            "witnesses": ["witness:fake"]
        }

        try:
            response = await self.client.post(
                f"{self.config.base_urls['identity']}/v1/lct/mint",
                json=request
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    self.metrics["identities_created"] += 1
                    return data["data"]
            return None
        except:
            return None

    async def _allocate_resources(self, entity_id: str, resource_type: str,
                                   amount: float, duration_seconds: int) -> Optional[Dict[str, Any]]:
        """Allocate resources"""
        request = {
            "entity_id": entity_id,
            "resource_type": resource_type,
            "amount": amount,
            "duration_seconds": duration_seconds
        }

        try:
            response = await self.client.post(
                f"{self.config.base_urls['resources']}/v1/resources/allocate",
                json=request
            )

            if response.status_code == 201:
                data = response.json()
                if data.get("success"):
                    return data["data"]
            return None
        except:
            return None

    async def _report_minimal_usage(self, allocation_id: str, actual_usage: float) -> bool:
        """Report minimal usage to claim refund"""
        request = {
            "allocation_id": allocation_id,
            "actual_usage": actual_usage
        }

        try:
            response = await self.client.post(
                f"{self.config.base_urls['resources']}/v1/resources/usage",
                json=request
            )

            return response.status_code == 200
        except:
            return False

    def _random_id(self, length: int = 8) -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


# =============================================================================
# Attack Simulation Runner
# =============================================================================

async def run_attack_simulation(attack_type: AttackType, config: Optional[AttackConfig] = None):
    """Run attack simulation and print results"""

    if config is None:
        config = AttackConfig(attack_type=attack_type)

    # Select appropriate attack simulator
    simulators = {
        AttackType.SYBIL_IDENTITY: SybilIdentityAttack,
        AttackType.REPUTATION_WASHING: ReputationWashingAttack,
        AttackType.ATP_DRAINING: ATPDrainingAttack
    }

    simulator_class = simulators.get(attack_type)
    if not simulator_class:
        print(f"❌ Attack type {attack_type} not yet implemented")
        return None

    print("=" * 70)
    print(f"Web4 Attack Simulation: {attack_type.value}")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Configuration:")
    print(f"  - Sybil count: {config.sybil_count}")
    print(f"  - Duration: {config.attack_duration}s")
    print(f"  - Request rate: {config.request_rate}/s")

    # Run simulation
    async with simulator_class(config) as simulator:
        result = await simulator.run()

    # Print results
    print("\n" + "=" * 70)
    print("Attack Simulation Results")
    print("=" * 70)
    print(f"Attack Type: {result.attack_type.value}")
    print(f"Success: {'✅ ATTACK SUCCESSFUL (VULNERABLE)' if result.success else '❌ ATTACK FAILED (MITIGATED)'}")
    print(f"Detection: {'✅ Detected' if result.detection_triggered else '❌ Not detected'}")
    print(f"Mitigation: {'✅ Effective' if result.mitigation_effective else '❌ Ineffective'}")

    print("\nMetrics:")
    for key, value in result.metrics.items():
        if key != "errors":
            print(f"  {key}: {value}")

    if result.metrics.get("errors"):
        print(f"\nErrors: {len(result.metrics['errors'])}")
        for error in result.metrics["errors"][:5]:  # Show first 5
            print(f"  - {error}")

    print(f"\nNotes: {result.notes}")
    print("=" * 70)

    return result


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Main entry point for attack simulator"""

    print("\n╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  Web4 Attack Simulation Framework".center(68) + "║")
    print("║" + "  Security Research - Session 11".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝\n")

    # Run multiple attack simulations
    attacks_to_test = [
        AttackType.SYBIL_IDENTITY,
        AttackType.REPUTATION_WASHING,
        AttackType.ATP_DRAINING
    ]

    results = []

    for attack_type in attacks_to_test:
        try:
            result = await run_attack_simulation(attack_type)
            if result:
                results.append(result)

            # Pause between attacks
            await asyncio.sleep(2)

        except Exception as e:
            print(f"\n❌ Attack simulation failed: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 70)
    print("Attack Simulation Summary")
    print("=" * 70)

    vulnerabilities_found = sum(1 for r in results if r.success)
    total_attacks = len(results)

    print(f"\nTotal attacks simulated: {total_attacks}")
    print(f"Successful attacks: {vulnerabilities_found}")
    print(f"Vulnerability rate: {vulnerabilities_found/total_attacks:.1%}" if total_attacks > 0 else "N/A")

    if vulnerabilities_found > 0:
        print("\n⚠️  VULNERABILITIES DETECTED - Implement mitigations!")
        print("\nVulnerable to:")
        for result in results:
            if result.success:
                print(f"  - {result.attack_type.value}")
    else:
        print("\n✅ All tested attacks mitigated successfully!")

    print("\n" + "=" * 70)

    return results


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
