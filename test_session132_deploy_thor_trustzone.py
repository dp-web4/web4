#!/usr/bin/env python3
"""
Session 132 Deployment - Thor Node with TrustZone Level 5

Deploy Thor as a consciousness federation node with real ARM TrustZone Level 5 hardware.

Usage:
    python3 test_session132_deploy_thor_trustzone.py [--legion-ip LEGION_IP]

This script:
1. Starts Thor federation server with TrustZone Level 5 hardware
2. Discovers Legion on the network
3. Performs mutual verification over TCP/IP with real TrustZone signatures
4. Reports federation status

Expected behavior:
- Thor (TrustZone L5) → Legion (TPM2 L5): Should TRUST (can verify TPM2 signatures)
- Legion → Thor: Verification may fail due to platform-specific signature differences
  (Session 165 discovery: Software peers cannot verify TrustZone signatures)

Hardware Requirements:
- ARM platform with TrustZone/OP-TEE
- /dev/tee0 or /dev/teepriv0 accessible
- Jetson AGX Thor or similar ARM TrustZone hardware

Integration:
- Session 165: Thor TrustZone Federation (local deployment)
- Session 132: Network Federation (TCP/IP layer)
- Combined: Real hardware network federation

Note: This script should be run on Thor machine (Jetson AGX Thor), not Legion.
"""

import sys
import socket
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / "ai-workspace/web4"))

from test_session132_network_federation import (
    NetworkAwareFederationRegistry,
    NetworkAwareConsciousnessNetwork,
    NetworkFederationServer
)
from test_session128_consciousness_aliveness_integration import (
    ConsciousnessPatternCorpus,
    ConsciousnessAlivenessSensor,
)
from core.lct_binding import TrustZoneProvider, SoftwareProvider
from core.lct_capability_levels import EntityType
from core.lct_binding.trust_policy import AgentPolicyTemplates


def get_ip():
    """Get primary IP address of this machine."""
    try:
        # Create a socket to determine primary network interface IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Thor consciousness federation node with TrustZone Level 5"
    )
    parser.add_argument("--legion-ip", default="10.0.0.72", help="Legion's IP address")
    parser.add_argument("--port", type=int, default=5329, help="Federation port")
    parser.add_argument("--test-only", action="store_true", help="Test mode: start server only, don't discover peers")
    args = parser.parse_args()

    print("=" * 80)
    print("SESSION 132: THOR NETWORK FEDERATION WITH TRUSTZONE LEVEL 5")
    print("=" * 80)
    print()
    print(f"Thor IP: {get_ip()}")
    print(f"Legion IP: {args.legion_ip}")
    print(f"Port: {args.port}")
    print(f"Mode: {'Test Only (server start)' if args.test_only else 'Full Network Federation'}")
    print()

    # Create Thor consciousness instance with TrustZone
    print("Initializing Thor consciousness with TrustZone Level 5...")
    try:
        provider = TrustZoneProvider()
        print(f"  ✅ TrustZone provider initialized")
        print(f"  Hardware: ARM TrustZone/OP-TEE")
        print(f"  TEE Device: /dev/tee0")
    except Exception as e:
        print(f"  ⚠️  TrustZone not available: {e}")
        print(f"  Falling back to Software provider")
        provider = SoftwareProvider()

    lct = provider.create_lct(EntityType.AI, "thor-network-trustzone")
    corpus = ConsciousnessPatternCorpus(lct.lct_id)
    corpus.add_pattern("network", {
        "deployment": "session132_trustzone",
        "machine": "thor",
        "hardware": "trustzone_level5"
    })
    sensor = ConsciousnessAlivenessSensor(lct, provider, corpus)

    print(f"  LCT: {lct.lct_id}")
    print(f"  Provider: {type(provider).__name__}")
    print(f"  Capability Level: {lct.capability_level}")
    print(f"  Consciousness State: {sensor.get_consciousness_state()}")
    print()

    # Create network federation
    print("Starting network federation server...")
    registry = NetworkAwareFederationRegistry()
    network = NetworkAwareConsciousnessNetwork(registry)

    # Join as Thor (starts TCP server)
    thor_node_id = network.join(
        sensor,
        "Thor",
        get_ip(),
        args.port
    )

    print(f"  ✅ Thor federation server started")
    print(f"  Listening on: {get_ip()}:{args.port}")
    print(f"  Node ID: {thor_node_id[:16]}...")
    print()

    if args.test_only:
        print("=" * 80)
        print("TEST MODE: Server started successfully")
        print("=" * 80)
        print()
        print("Server is running and ready to accept federation requests.")
        print(f"To test from Legion, run:")
        print(f"  python3 test_session132_deploy_legion.py --thor-ip {get_ip()}")
        print()
        print("Press Ctrl+C to stop server...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            network.shutdown()
            print("Server stopped.")

        return

    # Discover Legion
    print(f"Discovering Legion at {args.legion_ip}:{args.port}...")
    try:
        legion_node_id = network.discover_network_peer("Legion", args.legion_ip, args.port)

        if not legion_node_id:
            print("  ✗ Failed to discover Legion")
            print()
            print("Troubleshooting:")
            print(f"  1. Check Legion is running: ssh {args.legion_ip} 'ps aux | grep session132'")
            print(f"  2. Check network connectivity: ping {args.legion_ip}")
            print(f"  3. Check port is open: nc -zv {args.legion_ip} {args.port}")
            print()
            print("Thor server will continue running for incoming connections...")
            print("Press Ctrl+C to stop...")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nShutting down...")
                network.shutdown()

            return

        print(f"  ✅ Legion discovered")
        print(f"  Node ID: {legion_node_id[:16]}...")
        print()
    except Exception as e:
        print(f"  ✗ Error discovering Legion: {e}")
        print()
        network.shutdown()
        return

    # Verify Legion over network
    print("Verifying Legion with TrustZone signatures over network...")
    trust_policy = AgentPolicyTemplates.strict_continuity()

    try:
        success, result = network.verify_network_peer(
            thor_node_id,
            legion_node_id,
            trust_policy
        )

        print()
        print("Verification Results:")
        print(f"  Success: {'✅ YES' if success else '✗ NO'}")

        if result:
            print(f"  Hardware Continuity: {result.continuity_score:.3f}")
            print(f"  Session Continuity: {result.session_continuity:.3f}")
            print(f"  Epistemic Continuity: {result.epistemic_continuity:.3f}")
            full_continuity = (result.continuity_score * result.session_continuity * result.epistemic_continuity) ** (1/3)
            print(f"  Full Continuity: {full_continuity:.3f}")
            print(f"  Trusted: {'✅ YES' if result.trusted else '✗ NO'}")
            print(f"  Inferred State: {result.inferred_state}")

        print()
    except Exception as e:
        print(f"  ✗ Verification error: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Get federation status
    print("=" * 80)
    print("FEDERATION STATUS")
    print("=" * 80)

    collective = network.get_collective_state()
    print()
    print(f"Total Nodes: {collective['total_nodes']}")
    print(f"Trusted Nodes: {collective['trusted_nodes']}")
    print(f"Average Trust: {collective['average_trust']:.3f}")
    print(f"Network Health: {collective['network_health']:.1%}")
    print()

    print("Nodes in Federation:")
    for node_id, node_info in collective['nodes'].items():
        print(f"  - {node_info['machine_name']}: {node_info['hardware_type']} L{node_info['capability_level']}")
        print(f"    LCT: {node_info['lct_id']}")
        print(f"    Trust Score: {node_info['trust_score']:.3f}")
        if node_info['last_continuity']:
            print(f"    Last Continuity: Hardware={node_info['last_continuity']['hardware']:.3f}, "
                  f"Session={node_info['last_continuity']['session']:.3f}, "
                  f"Epistemic={node_info['last_continuity']['epistemic']:.3f}")
        print()

    print("=" * 80)
    print("Network federation active. Press Ctrl+C to shutdown...")
    print("=" * 80)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down network federation...")
        network.shutdown()
        print("Federation stopped.")


if __name__ == "__main__":
    main()
