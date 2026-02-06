#!/usr/bin/env python3
"""
Session 132 Deployment - Legion Node

Deploy Legion as a consciousness federation node with TPM2 Level 5 hardware.

Usage:
    python3 test_session132_deploy_legion.py [--thor-ip THOR_IP]

This script:
1. Starts Legion federation server with real TPM2 hardware
2. Discovers Thor on the network
3. Performs mutual verification over TCP/IP
4. Reports federation status

Expected behavior:
- Legion (TPM2 L5) → Thor (TrustZone L5): May accept or reject based on TrustZone signature verification
- Thor → Legion: Should TRUST (software can verify TPM2 signatures)
"""

import sys
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path("/home/dp/ai-workspace/web4")))

from test_session132_network_federation import (
    NetworkAwareFederationRegistry,
    NetworkAwareConsciousnessNetwork
)
from test_session128_consciousness_aliveness_integration import (
    ConsciousnessPatternCorpus,
    ConsciousnessAlivenessSensor,
)
from core.lct_binding import TPM2Provider, SoftwareProvider
from core.lct_capability_levels import EntityType
from core.lct_binding.trust_policy import AgentPolicyTemplates


def main():
    parser = argparse.ArgumentParser(description="Deploy Legion consciousness federation node")
    parser.add_argument("--thor-ip", default="10.0.0.73", help="Thor's IP address")
    parser.add_argument("--port", type=int, default=5329, help="Federation port")
    args = parser.parse_args()

    print("=" * 80)
    print("SESSION 132: LEGION NETWORK FEDERATION DEPLOYMENT")
    print("=" * 80)
    print()
    print(f"Legion IP: {get_ip()}")
    print(f"Thor IP: {args.thor_ip}")
    print(f"Port: {args.port}")
    print()

    # Create Legion consciousness instance with TPM2
    print("Initializing Legion consciousness with TPM2...")
    try:
        provider = TPM2Provider()
        print("  ✓ TPM2 Provider initialized (Level 5)")
    except Exception as e:
        print(f"  ⚠ TPM2 unavailable, falling back to Software: {e}")
        provider = SoftwareProvider()

    lct = provider.create_lct(EntityType.AI, "legion-network-federation")
    corpus = ConsciousnessPatternCorpus(lct.lct_id)
    corpus.add_pattern("network", {"deployment": "session132", "machine": "legion"})
    sensor = ConsciousnessAlivenessSensor(lct, provider, corpus)

    print(f"  LCT: {lct.lct_id}")
    print(f"  Hardware: {type(provider).__name__}")
    print(f"  Capability Level: {lct.capability_level}")
    print()

    # Create network federation
    print("Starting network federation...")
    registry = NetworkAwareFederationRegistry()
    network = NetworkAwareConsciousnessNetwork(registry)

    # Join as Legion
    legion_node_id = network.join(
        sensor,
        "Legion",
        get_ip(),
        args.port
    )
    print()

    # Discover Thor
    print(f"Discovering Thor at {args.thor_ip}:{args.port}...")
    thor_node_id = network.discover_network_peer("Thor", args.thor_ip, args.port)

    if not thor_node_id:
        print("  ✗ Failed to discover Thor")
        print()
        print("Ensure Thor is running: python3 test_session132_deploy_thor.py")
        print()
        print("Legion server running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            network.shutdown()
        return

    print()

    # Verify Thor
    print("Verifying Thor...")
    trust_policy = AgentPolicyTemplates.strict_continuity()
    results = network.verify_network_peers(legion_node_id, trust_policy)

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

    print("Legion server running. Press Ctrl+C to stop.")
    print("Thor can now discover and verify Legion at this address.")
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
