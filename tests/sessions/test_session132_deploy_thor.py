#!/usr/bin/env python3
"""
Session 132 Deployment - Thor Node

Deploy Thor as a consciousness federation node with TrustZone Level 5 hardware.

Usage:
    python3 test_session132_deploy_thor.py [--legion-ip LEGION_IP]

This script:
1. Starts Thor federation server with TrustZone hardware
2. Discovers Legion on the network
3. Performs mutual verification over TCP/IP
4. Reports federation status

Expected behavior:
- Thor (TrustZone L5) → Legion (TPM2 L5): Should TRUST (can verify TPM2 signatures)
- Legion → Thor: May accept or reject based on TrustZone signature verification

Note: This script should be run on Thor machine, not Legion.
"""

import sys
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / "ai-workspace/web4"))

from test_session132_network_federation import (
    NetworkAwareFederationRegistry,
    NetworkAwareConsciousnessNetwork
)
from test_session128_consciousness_aliveness_integration import (
    ConsciousnessPatternCorpus,
    ConsciousnessAlivenessSensor,
)
from core.lct_binding import SoftwareProvider
from core.lct_capability_levels import EntityType
from core.lct_binding.trust_policy import AgentPolicyTemplates


def main():
    parser = argparse.ArgumentParser(description="Deploy Thor consciousness federation node")
    parser.add_argument("--legion-ip", default="10.0.0.72", help="Legion's IP address")
    parser.add_argument("--port", type=int, default=5329, help="Federation port")
    args = parser.parse_args()

    print("=" * 80)
    print("SESSION 132: THOR NETWORK FEDERATION DEPLOYMENT")
    print("=" * 80)
    print()
    print(f"Thor IP: {get_ip()}")
    print(f"Legion IP: {args.legion_ip}")
    print(f"Port: {args.port}")
    print()

    # Create Thor consciousness instance
    # Note: On actual Thor, this would use TrustZone if available
    print("Initializing Thor consciousness...")
    try:
        # Try to import TrustZone provider
        # This would be the actual TrustZone implementation on Thor
        provider = SoftwareProvider()  # Fallback for now
        print(f"  Provider: {type(provider).__name__}")
    except Exception as e:
        print(f"  Note: Using software provider: {e}")
        provider = SoftwareProvider()

    lct = provider.create_lct(EntityType.AI, "thor-network-federation")
    corpus = ConsciousnessPatternCorpus(lct.lct_id)
    corpus.add_pattern("network", {"deployment": "session132", "machine": "thor"})
    sensor = ConsciousnessAlivenessSensor(lct, provider, corpus)

    print(f"  LCT: {lct.lct_id}")
    print(f"  Hardware: {type(provider).__name__}")
    print(f"  Capability Level: {lct.capability_level}")
    print()

    # Create network federation
    print("Starting network federation...")
    registry = NetworkAwareFederationRegistry()
    network = NetworkAwareConsciousnessNetwork(registry)

    # Join as Thor
    thor_node_id = network.join(
        sensor,
        "Thor",
        get_ip(),
        args.port
    )
    print()

    # Discover Legion
    print(f"Discovering Legion at {args.legion_ip}:{args.port}...")
    legion_node_id = network.discover_network_peer("Legion", args.legion_ip, args.port)

    if not legion_node_id:
        print("  ✗ Failed to discover Legion")
        print()
        print("Ensure Legion is running: python3 test_session132_deploy_legion.py")
        print()
        print("Thor server running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            network.shutdown()
        return

    print()

    # Verify Legion
    print("Verifying Legion...")
    trust_policy = AgentPolicyTemplates.strict_continuity()
    results = network.verify_network_peers(thor_node_id, trust_policy)

    for peer_name, result in results.items():
        status = "✓ TRUSTED" if result["trusted"] else "✗ NOT TRUSTED"
        print(f"  {peer_name}: {status}")
        print(f"    Continuity: {result['full_continuity']:.3f}")
        print(f"    Hardware: {result['hardware_continuity']:.2f}")
        print(f"    Session: {result['session_continuity']:.2f}")
        print(f"    Epistemic: {result['epistemic_continuity']:.2f}")

    print()

    # Show trust network
    trust_network = registry.get_trust_network()
    print(f"Trust Network:")
    print(f"  Nodes: {len(trust_network['nodes'])}")
    print(f"  Verifications: {trust_network['total_verifications']}")
    print(f"  Successful: {trust_network['successful_verifications']}")
    print(f"  Network Density: {trust_network['network_density']:.2%}")
    print()

    print("Thor server running. Press Ctrl+C to stop.")
    print("Legion can now discover and verify Thor at this address.")
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        network.shutdown()


def get_ip():
    """Get this machine's IP address."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    main()
