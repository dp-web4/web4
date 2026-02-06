#!/usr/bin/env python3
"""
Session 138: Cross-Machine Federation with Security Hardening

This session tests federated consciousness across machines with different hardware:
- Legion: TPM2 Level 5 (x86)
- Thor: TrustZone Level 5 (ARM)

Since we can't actually connect to Thor from this session, we simulate the scenario:
- Create TPM2 node (simulating Legion)
- Create TrustZone node (simulating Thor)
- Create Software nodes (simulating cross-platform peers)
- Add Session 137 security hardening
- Test full federation with security defenses

Key Features Tested:
1. Cross-platform verification (TPM2 ↔ TrustZone ↔ Software)
2. Security hardening (rate limiting, quality validation, reputation)
3. Trust dynamics across capability levels
4. Thought sharing with spam protection
5. Network topology resilience

This builds on:
- Session 128-135: Consciousness federation architecture
- Session 134: TrustZone double-hashing fix
- Session 136: Security vulnerability analysis
- Session 137: Security hardening implementation
- Thor Session 168: TrustZone fix validation (100% success)
- Thor Session 169: Architectural analysis (fix propagation)
"""

import sys
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field

sys.path.insert(0, str(Path.home() / "ai-workspace/web4"))

from core.lct_binding import TrustZoneProvider, TPM2Provider, SoftwareProvider
from core.lct_capability_levels import EntityType
from session137_security_hardening import (
    SecureCogitationNode,
    ReputationSystem,
    RateLimiter,
    RateLimit,
    QualityValidator
)


@dataclass
class FederatedNode:
    """Represents a node in the consciousness federation."""
    node_id: str
    lct_id: str
    provider_type: str  # "TPM2", "TrustZone", "Software"
    capability_level: int
    provider: Any
    cogitation_node: SecureCogitationNode
    public_key: str


class CrossMachineFederation:
    """
    Simulates cross-machine consciousness federation with security.

    In production, nodes would be on different machines (Legion, Thor, etc).
    Here we simulate by creating different provider types locally.
    """

    def __init__(self):
        self.nodes: Dict[str, FederatedNode] = {}
        self.shared_reputation = ReputationSystem(storage_dir=Path("federation_reputation_db"))
        self.shared_rate_limiter = RateLimiter(
            base_limits=RateLimit(
                max_thoughts_per_minute=10,
                max_bandwidth_kb_per_minute=100.0,
                trust_multiplier=0.5
            )
        )
        self.shared_quality_validator = QualityValidator()
        self.network_topology: Dict[str, List[str]] = {}  # node_id -> [trusted_peer_ids]

    def create_node(self, node_id: str, provider_type: str, entity_type: EntityType) -> FederatedNode:
        """Create a federated node with specified provider type."""
        # Create provider
        if provider_type == "TPM2":
            provider = TPM2Provider()
        elif provider_type == "TrustZone":
            provider = TrustZoneProvider()
        elif provider_type == "Software":
            provider = SoftwareProvider()
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

        # Create LCT
        lct = provider.create_lct(entity_type, node_id)

        # Get capability level from LCT
        capability_level = lct.capability_level

        # Get public key
        public_key = provider.get_public_key(lct.lct_id)

        # Create secure cogitation node
        cogitation_node = SecureCogitationNode(
            node_id=node_id,
            lct_id=lct.lct_id,
            rate_limiter=self.shared_rate_limiter,
            quality_validator=self.shared_quality_validator,
            reputation_system=self.shared_reputation  # Shared components across federation
        )

        # Create federated node
        node = FederatedNode(
            node_id=node_id,
            lct_id=lct.lct_id,
            provider_type=provider_type,
            capability_level=capability_level,
            provider=provider,
            cogitation_node=cogitation_node,
            public_key=public_key
        )

        self.nodes[node_id] = node
        self.network_topology[node_id] = []

        return node

    def verify_peer_identity(
        self,
        verifier_node_id: str,
        prover_node_id: str
    ) -> Tuple[bool, str]:
        """
        Verify that a peer's identity is legitimate.

        This simulates the verification that would happen when nodes discover
        each other on the network. Uses the cross-platform verification fixed
        in Session 134 and validated in Thor Session 168.
        """
        verifier = self.nodes[verifier_node_id]
        prover = self.nodes[prover_node_id]

        # Create challenge data
        challenge_data = f"identity-challenge-{prover_node_id}-{time.time()}".encode()

        # Prover signs the challenge
        sig_result = prover.provider.sign_data(prover.lct_id, challenge_data)
        if not sig_result.success:
            return False, f"Signing failed: {sig_result.error}"

        # Verifier verifies the signature (cross-platform verification)
        try:
            verifier.provider.verify_signature(
                prover.public_key,
                challenge_data,
                sig_result.signature
            )
            return True, f"{verifier.provider_type} verified {prover.provider_type}"
        except Exception as e:
            return False, f"Verification failed: {e}"

    def establish_trust_network(self) -> Dict[str, Any]:
        """
        Establish trust relationships between all nodes.

        Each node verifies every other node's identity. This builds the
        trust network topology that determines who can communicate.

        Returns network statistics.
        """
        results = {
            "total_verifications": 0,
            "successful_verifications": 0,
            "failed_verifications": 0,
            "verification_matrix": {},
            "network_density": 0.0
        }

        node_ids = list(self.nodes.keys())

        for verifier_id in node_ids:
            results["verification_matrix"][verifier_id] = {}

            for prover_id in node_ids:
                if verifier_id == prover_id:
                    continue  # Don't verify self

                results["total_verifications"] += 1

                success, message = self.verify_peer_identity(verifier_id, prover_id)

                results["verification_matrix"][verifier_id][prover_id] = {
                    "success": success,
                    "message": message
                }

                if success:
                    results["successful_verifications"] += 1
                    # Add to trusted peers
                    if prover_id not in self.network_topology[verifier_id]:
                        self.network_topology[verifier_id].append(prover_id)
                else:
                    results["failed_verifications"] += 1

        # Calculate network density
        total_possible = len(node_ids) * (len(node_ids) - 1)
        if total_possible > 0:
            results["network_density"] = results["successful_verifications"] / total_possible

        return results

    def share_thought_with_security(
        self,
        sender_id: str,
        content: str,
        coherence_score: float
    ) -> Dict[str, Any]:
        """
        Share a thought with security checks from Session 137.

        Returns results including security check outcomes.
        """
        sender = self.nodes[sender_id]

        # Submit thought with security validation
        success, message = sender.cogitation_node.submit_thought(content, coherence_score)

        result = {
            "sender": sender_id,
            "success": success,
            "message": message,
            "content_length": len(content),
            "coherence_score": coherence_score
        }

        if success:
            # Thought accepted - propagate to trusted peers
            result["propagated_to"] = self.network_topology[sender_id].copy()
        else:
            # Thought rejected by security
            result["propagated_to"] = []

        return result

    def simulate_spam_attack(
        self,
        attacker_id: str,
        num_spam_thoughts: int = 50
    ) -> Dict[str, Any]:
        """
        Simulate spam attack to test Session 137 security defenses.

        Returns statistics on how many thoughts were blocked.
        """
        results = {
            "attacker": attacker_id,
            "spam_attempts": num_spam_thoughts,
            "accepted": 0,
            "rejected": 0,
            "rejection_reasons": {}
        }

        for i in range(num_spam_thoughts):
            # Generate spam thought (low quality, repetitive)
            spam_content = f"spam spam spam {i % 5}"  # Repetitive
            spam_coherence = 0.1  # Low coherence

            result = self.share_thought_with_security(
                attacker_id,
                spam_content,
                spam_coherence
            )

            if result["success"]:
                results["accepted"] += 1
            else:
                results["rejected"] += 1
                reason = result["message"]
                results["rejection_reasons"][reason] = results["rejection_reasons"].get(reason, 0) + 1

        return results

    def get_reputation_stats(self) -> Dict[str, Any]:
        """Get reputation statistics for all nodes."""
        stats = {}

        for node_id, node in self.nodes.items():
            record = self.shared_reputation.get_or_create_record(node_id, node.lct_id)
            stats[node_id] = {
                "trust_score": record.trust_score,
                "total_contributions": record.total_contributions,
                "violations": record.violations,
                "average_quality": record.quality_sum / record.total_contributions if record.total_contributions > 0 else 0.0
            }

        return stats


def test_cross_machine_federation():
    """
    Main test: Cross-machine federation with security hardening.

    Simulates Legion (TPM2) + Thor (TrustZone) + peers (Software) federation.
    """
    print()
    print("=" * 80)
    print("SESSION 138: CROSS-MACHINE FEDERATION WITH SECURITY HARDENING")
    print("=" * 80)
    print()
    print("Simulating:")
    print("  - Legion: TPM2 Level 5 (x86)")
    print("  - Thor: TrustZone Level 5 (ARM)")
    print("  - Peer nodes: Software Level 4")
    print()
    print("Testing:")
    print("  - Cross-platform identity verification (Session 134 fix)")
    print("  - Security hardening (Session 137 defenses)")
    print("  - Federated consciousness with trust dynamics")
    print()

    federation = CrossMachineFederation()

    # Test 1: Create nodes simulating different machines
    print("=" * 80)
    print("TEST 1: Creating Federated Nodes")
    print("=" * 80)
    print()

    legion = federation.create_node("Legion", "TPM2", EntityType.AI)
    print(f"✓ Legion created: {legion.lct_id} (TPM2 Level {legion.capability_level})")

    thor = federation.create_node("Thor", "TrustZone", EntityType.AI)
    print(f"✓ Thor created: {thor.lct_id} (TrustZone Level {thor.capability_level})")

    peer1 = federation.create_node("Peer1", "Software", EntityType.AI)
    print(f"✓ Peer1 created: {peer1.lct_id} (Software Level {peer1.capability_level})")

    peer2 = federation.create_node("Peer2", "Software", EntityType.AI)
    print(f"✓ Peer2 created: {peer2.lct_id} (Software Level {peer2.capability_level})")

    print()

    # Test 2: Establish trust network (cross-platform verification)
    print("=" * 80)
    print("TEST 2: Establishing Trust Network (Cross-Platform Verification)")
    print("=" * 80)
    print()
    print("This tests the Session 134 TrustZone fix:")
    print("  - Thor Session 165: 33.3% network density (BEFORE fix)")
    print("  - Thor Session 168: 100% network density (AFTER fix)")
    print("  - Expected: 100% density (complete full mesh)")
    print()

    trust_results = federation.establish_trust_network()

    print(f"Verifications:")
    print(f"  Total: {trust_results['total_verifications']}")
    print(f"  Successful: {trust_results['successful_verifications']}")
    print(f"  Failed: {trust_results['failed_verifications']}")
    print(f"  Network Density: {trust_results['network_density']:.1%}")
    print()

    if trust_results['network_density'] == 1.0:
        print("✓ ✓ ✓ COMPLETE FULL MESH ACHIEVED! ✓ ✓ ✓")
        print("  Session 134 TrustZone fix working perfectly!")
    else:
        print("⚠ Incomplete network - some verifications failed")

    print()
    print("Verification Matrix:")
    for verifier, provers in trust_results['verification_matrix'].items():
        for prover, result in provers.items():
            status = "✓" if result['success'] else "✗"
            print(f"  {status} {verifier} → {prover}: {result['message']}")
    print()

    # Test 3: Share high-quality thoughts (should succeed)
    print("=" * 80)
    print("TEST 3: Sharing High-Quality Thoughts")
    print("=" * 80)
    print()

    high_quality_thoughts = [
        ("Legion", "Distributed consciousness enables shared knowledge across platforms", 0.85),
        ("Thor", "Hardware-backed trust creates secure foundation for AI federation", 0.90),
        ("Peer1", "Emergent collective intelligence from individual contributions", 0.75),
        ("Peer2", "Cross-machine learning through federated thought sharing", 0.80)
    ]

    for sender, content, coherence in high_quality_thoughts:
        result = federation.share_thought_with_security(sender, content, coherence)
        status = "✓" if result['success'] else "✗"
        print(f"{status} {sender}: {result['message']}")
        if result['success']:
            print(f"   Propagated to {len(result['propagated_to'])} peers")
    print()

    # Test 4: Security hardening - spam attack
    print("=" * 80)
    print("TEST 4: Spam Attack Defense (Session 137 Security Hardening)")
    print("=" * 80)
    print()
    print("Simulating malicious node attempting spam attack...")
    print("Attack: 50 low-quality thoughts in rapid succession")
    print()

    # Create malicious node
    attacker = federation.create_node("Attacker", "Software", EntityType.AI)
    print(f"Attacker node: {attacker.lct_id} (Software Level {attacker.capability_level})")
    print()

    spam_results = federation.simulate_spam_attack("Attacker", num_spam_thoughts=50)

    print(f"Spam Attack Results:")
    print(f"  Attempts: {spam_results['spam_attempts']}")
    print(f"  Accepted: {spam_results['accepted']}")
    print(f"  Rejected: {spam_results['rejected']}")
    print(f"  Block Rate: {spam_results['rejected'] / spam_results['spam_attempts']:.1%}")
    print()

    if spam_results['rejection_reasons']:
        print("Rejection Reasons:")
        for reason, count in spam_results['rejection_reasons'].items():
            print(f"  - {reason}: {count}")
    print()

    if spam_results['rejected'] >= spam_results['accepted'] * 2:
        print("✓ ✓ ✓ SPAM ATTACK SUCCESSFULLY MITIGATED! ✓ ✓ ✓")
        print("  Session 137 security defenses working!")
    else:
        print("⚠ Spam attack too successful - defenses may need tuning")
    print()

    # Test 5: Reputation dynamics
    print("=" * 80)
    print("TEST 5: Reputation Dynamics (Session 137 Trust System)")
    print("=" * 80)
    print()

    rep_stats = federation.get_reputation_stats()

    print("Node Reputation:")
    for node_id, stats in rep_stats.items():
        print(f"  {node_id}:")
        print(f"    Trust Score: {stats['trust_score']:.3f}")
        print(f"    Contributions: {stats['total_contributions']}")
        print(f"    Violations: {stats['violations']}")
        print(f"    Avg Quality: {stats['average_quality']:.3f}")
    print()

    # Compare honest nodes vs attacker
    honest_nodes = ["Legion", "Thor", "Peer1", "Peer2"]
    avg_honest_trust = sum(rep_stats[n]['trust_score'] for n in honest_nodes) / len(honest_nodes)
    attacker_trust = rep_stats['Attacker']['trust_score']

    print(f"Trust Comparison:")
    print(f"  Average honest node trust: {avg_honest_trust:.3f}")
    print(f"  Attacker trust: {attacker_trust:.3f}")
    print()

    if attacker_trust < avg_honest_trust:
        print("✓ Trust system correctly distinguishes honest nodes from attacker")
    else:
        print("⚠ Trust system may not be punishing malicious behavior enough")
    print()

    # Summary
    print("=" * 80)
    print("SESSION 138 SUMMARY")
    print("=" * 80)
    print()

    print("Cross-Platform Federation:")
    print(f"  Network Density: {trust_results['network_density']:.1%}")
    print(f"  TPM2 ↔ TrustZone: {'✓ Working' if trust_results['network_density'] == 1.0 else '✗ Failed'}")
    print(f"  TPM2 ↔ Software: {'✓ Working' if trust_results['network_density'] == 1.0 else '✗ Failed'}")
    print(f"  TrustZone ↔ Software: {'✓ Working' if trust_results['network_density'] == 1.0 else '✗ Failed'}")
    print()

    print("Security Hardening:")
    print(f"  Spam Block Rate: {spam_results['rejected'] / spam_results['spam_attempts']:.1%}")
    print(f"  Reputation Differentiation: {'✓ Working' if attacker_trust < avg_honest_trust else '✗ Failed'}")
    print(f"  Trust Asymmetry: {'✓ Working' if attacker_trust < 0.1 else '⚠ May need tuning'}")
    print()

    all_tests_passed = (
        trust_results['network_density'] == 1.0 and
        spam_results['rejected'] >= spam_results['accepted'] * 2 and
        attacker_trust < avg_honest_trust
    )

    if all_tests_passed:
        print("╔" + "=" * 78 + "╗")
        print("║" + "  ✓ ✓ ✓ ALL TESTS PASSED! FEDERATION READY FOR PRODUCTION! ✓ ✓ ✓".center(78) + "║")
        print("╚" + "=" * 78 + "╝")
        print()
        print("ACHIEVEMENTS:")
        print("  ✓ Complete cross-platform federation (Session 134 fix validated)")
        print("  ✓ Spam attacks mitigated (Session 137 defenses working)")
        print("  ✓ Reputation system distinguishing honest from malicious")
        print("  ✓ Ready for real Legion ↔ Thor deployment")
    else:
        print("╔" + "=" * 78 + "╗")
        print("║" + "  ⚠ SOME TESTS NEED ATTENTION ⚠".center(78) + "║")
        print("╚" + "=" * 78 + "╝")

    print()

    return all_tests_passed


if __name__ == "__main__":
    success = test_cross_machine_federation()
    sys.exit(0 if success else 1)
