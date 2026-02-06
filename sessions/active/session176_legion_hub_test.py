#!/usr/bin/env python3
"""
Session 176: Legion Hub Node Test

Tests Legion as hub node for real LAN deployment, waiting for Thor and Sprout
to connect.

Network Topology:
- Legion (Hub): 10.0.0.72:8888 (RTX 4090, TPM2, L5)
- Thor: 10.0.0.99:8889 (AGX Thor, TrustZone, L5)
- Sprout: 10.0.0.36:8890 (Orin Nano 8GB, TPM2, L3)

Usage:
    python3 session176_legion_hub_test.py

This starts Legion as hub and waits for connections. Thor and Sprout should
connect to 10.0.0.72:8888.

Platform: Legion (RTX 4090)
Date: 2026-01-09
"""

import asyncio
import json
import signal
import sys
from pathlib import Path
from typing import Optional

# Add paths
HOME = Path.home()
sys.path.insert(0, str(HOME / "ai-workspace" / "web4"))

# Import Session 153 (advanced security federation)
from session153_advanced_security_federation import (
    AdvancedSecurityFederationNode,
    CogitationMode,
)


class LegionHubNode:
    """
    Legion hub node for Session 176 deployment.

    Acts as central hub for Thor and Sprout to connect to.
    """

    def __init__(self):
        """Initialize Legion hub node."""
        self.node = AdvancedSecurityFederationNode(
            node_id="legion",
            lct_id="lct:web4:ai:legion",
            hardware_type="tpm2",
            hardware_level=5,
            listen_host="0.0.0.0",  # Listen on all interfaces
            listen_port=8888,
            network_subnet="10.0.0.0/24",
        )

        self.running = True
        self.server_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start Legion hub node."""
        print("\n" + "="*80)
        print("SESSION 176: LEGION HUB NODE")
        print("="*80)
        print("\nNetwork Configuration:")
        print("  Legion (Hub): 10.0.0.72:8888 (RTX 4090, TPM2, L5)")
        print("  Thor:         10.0.0.99:8889 (AGX Thor, TrustZone, L5)")
        print("  Sprout:       10.0.0.36:8890 (Orin Nano 8GB, TPM2, L3)")
        print("\nStarting hub node...")
        print("="*80 + "\n")

        # Start server
        print("[legion] Starting federation server on 0.0.0.0:8888...")
        self.server_task = asyncio.create_task(self.node.start())

        # Wait for server to bind
        await asyncio.sleep(2)
        print("[legion] ✅ Server started and listening")
        print("[legion] Ready for peer connections from Thor and Sprout")
        print("\n" + "="*80)
        print("WAITING FOR CONNECTIONS")
        print("="*80)
        print("\nPeers should connect to: 10.0.0.72:8888")
        print("\nThor command:")
        print("  (on Thor) python3 session176_deploy.py --node thor --port 8889 \\")
        print("    --connect legion:10.0.0.72:8888")
        print("\nSprout command:")
        print("  (on Sprout) python3 session176_deploy.py --node sprout --port 8890 \\")
        print("    --connect legion:10.0.0.72:8888")
        print("\n" + "="*80 + "\n")

        # Monitor connections
        await self.monitor_connections()

    async def monitor_connections(self):
        """Monitor peer connections and display status."""
        last_peer_count = 0

        while self.running:
            await asyncio.sleep(5)

            peer_count = len(self.node.peers)

            if peer_count != last_peer_count:
                print(f"\n[legion] Connection update: {peer_count} peer(s) connected")

                if peer_count > 0:
                    print(f"[legion] Connected peers:")
                    for peer_id, peer_info in self.node.peers.items():
                        print(f"[legion]   - {peer_id} (verified: {peer_info.verified})")

                # Display metrics when we have peers
                if peer_count >= 1:
                    print("\n" + "="*80)
                    print("NETWORK STATUS")
                    print("="*80)
                    metrics = self.node.get_advanced_security_metrics()
                    print(f"ATP Balance: {metrics['atp_balance']}")
                    print(f"Total Peers: {peer_count}")
                    print(f"Thoughts Accepted: {metrics['thoughts_accepted']}")
                    print("="*80 + "\n")

                last_peer_count = peer_count

    async def stop(self):
        """Stop Legion hub node."""
        print("\n[legion] Stopping hub node...")
        self.running = False
        await self.node.stop()
        if self.server_task:
            self.server_task.cancel()
        print("[legion] Hub node stopped")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Run Legion hub node test."""
    hub = LegionHubNode()

    # Handle shutdown signals
    def signal_handler(sig, frame):
        print("\n\n[Signal] Received shutdown signal")
        asyncio.create_task(hub.stop())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await hub.start()
    except KeyboardInterrupt:
        print("\n\n[Interrupted] Shutting down...")
        await hub.stop()
    except Exception as e:
        print(f"\n[Error] {e}")
        await hub.stop()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("LEGION HUB NODE TEST")
    print("="*80)
    print("Starting Legion as hub node for real LAN deployment...")
    print("Press Ctrl+C to stop")
    print("="*80 + "\n")

    asyncio.run(main())
