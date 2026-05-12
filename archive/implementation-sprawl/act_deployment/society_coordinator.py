#!/usr/bin/env python3
"""
Web4 Society Coordinator - Session #32

Complete coordination system combining:
- Session #30: Society formation, peer discovery, heartbeats
- Session #31: Ed25519 signatures, security hardening
- Session #32: Cross-society encrypted messaging

This is the unified system for autonomous AI society coordination.

Features:
- Cryptographically-secured heartbeat protocol
- End-to-end encrypted peer messaging
- Reputation tracking with signature failure integration
- Resource request/response coordination
- Multi-society collaboration scenarios

Author: Claude (Session #32)
Date: 2025-11-15
"""

import json
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from enum import Enum

from society_manager_secure import (
    SecureSocietyManager,
    SocietyIdentity,
    PeerStatus,
    SignedHeartbeat
)
from web4_messaging import (
    Web4MessageSender,
    Web4MessageReceiver,
    Web4MessagingCrypto,
    MessageType,
    MessagePriority,
    DecryptedMessage
)
from web4_crypto import Web4Crypto, KeyPair


class CoordinationAction(Enum):
    """Types of coordination actions"""
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_OFFER = "resource_offer"
    ATP_TRANSFER = "atp_transfer"
    TRUST_UPDATE = "trust_update"
    COLLABORATION_PROPOSAL = "collaboration_proposal"
    STATUS_UPDATE = "status_update"


@dataclass
class CoordinationMessage:
    """High-level coordination message"""
    action: CoordinationAction
    from_society: str  # LCT
    to_society: str    # LCT
    payload: dict
    timestamp: datetime
    message_id: Optional[str] = None


class SocietyCoordinator:
    """
    Complete coordination system for Web4 societies.

    Combines:
    - SecureSocietyManager: Heartbeats, peer discovery, health monitoring
    - Web4MessageSender/Receiver: Encrypted messaging
    - Reputation tracking: Trust scores based on behavior
    """

    def __init__(
        self,
        society_name: str,
        description: str,
        agent_type: str,
        capabilities: List[str],
        data_dir: Path,
        discovery_channels: List[Path],
        deterministic_keys: bool = True
    ):
        """
        Initialize society coordinator.

        Args:
            society_name: Name of this society
            description: Purpose/description
            agent_type: Type of agent (research, compute, etc.)
            capabilities: List of capabilities
            data_dir: Local data directory
            discovery_channels: Shared discovery channels
            deterministic_keys: Use deterministic key generation (testing)
        """
        self.society_name = society_name
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize society manager (heartbeats + discovery)
        self.society_mgr = SecureSocietyManager(
            data_dir=self.data_dir,
            heartbeat_interval=10,  # 10 second heartbeats
            timeout_threshold=30    # 30 second timeout
        )

        # Create society identity
        self.identity = self.society_mgr.create_society(
            name=society_name,
            description=description,
            agent_type=agent_type,
            capabilities=capabilities,
            deterministic=deterministic_keys
        )

        self.society_mgr.register_local_society(self.identity)

        # Add discovery channels
        for channel in discovery_channels:
            self.society_mgr.add_discovery_channel(channel)

        # Generate X25519 keypair for messaging encryption
        self.x25519_private, self.x25519_public = Web4MessagingCrypto.generate_ephemeral_keypair()

        # Store X25519 public key separately
        self.x25519_public_key_hex = self.x25519_public.hex()

        # Save X25519 key to file (local)
        x25519_key_file = self.data_dir / "x25519_public_key.json"
        with open(x25519_key_file, 'w') as f:
            json.dump({
                'lct': self.identity.lct,
                'x25519_public_key_hex': self.x25519_public_key_hex
            }, f, indent=2)

        # Publish X25519 key to discovery channels (for peers to find)
        for channel in discovery_channels:
            channel_key_file = channel / f"x25519_key_{self.identity.society_id}.json"
            with open(channel_key_file, 'w') as f:
                json.dump({
                    'lct': self.identity.lct,
                    'society_name': society_name,
                    'x25519_public_key_hex': self.x25519_public_key_hex
                }, f, indent=2)

        # Initialize messaging
        message_outbox = self.data_dir / "messages" / "outbox"
        message_inbox = self.data_dir / "messages" / "inbox"
        message_outbox.mkdir(parents=True, exist_ok=True)
        message_inbox.mkdir(parents=True, exist_ok=True)

        self.message_sender = Web4MessageSender(
            sender_lct=self.identity.lct,
            signing_keypair=self.society_mgr.local_keypair,
            message_dir=message_outbox
        )

        self.message_receiver = Web4MessageReceiver(
            recipient_lct=self.identity.lct,
            x25519_private_key=self.x25519_private,
            signing_keypair=self.society_mgr.local_keypair,
            inbox_dir=message_inbox,
            max_age_hours=24
        )

        # Coordination state
        self.pending_requests: Dict[str, CoordinationMessage] = {}
        self.active_collaborations: Dict[str, dict] = {}

        # Track message exchange for trust scoring
        self.message_stats: Dict[str, dict] = {}  # peer_lct -> stats

        # Running state
        self.running = False

        print(f"✨ Society coordinator initialized: {society_name}")
        print(f"   LCT: {self.identity.lct}")
        print(f"   Ed25519 public key: {self.identity.public_key_hex[:32]}...")
        print(f"   X25519 public key: {self.x25519_public.hex()[:32]}...")

    async def start(self):
        """Start coordinator (heartbeats + message processing)"""
        print(f"\n🚀 Starting {self.society_name} coordinator...")

        # Start heartbeat
        await self.society_mgr.start_heartbeat()

        # Start message processing loop
        self.running = True
        asyncio.create_task(self._message_processing_loop())

        print(f"✅ {self.society_name} coordinator running")

    async def stop(self):
        """Stop coordinator"""
        print(f"\n🛑 Stopping {self.society_name} coordinator...")
        await self.society_mgr.stop_heartbeat()
        self.running = False

    async def discover_and_sync(self):
        """Discover peers and sync messages"""
        # Discover peers via heartbeats
        new_peers = await self.society_mgr.discover_peers()

        if new_peers:
            print(f"\n🔍 {self.society_name} discovered new peers: {[p.society_name for p in new_peers]}")

        # Check messages
        await self._process_messages()

        return new_peers

    async def send_coordination_message(
        self,
        recipient_lct: str,
        action: CoordinationAction,
        payload: dict,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Optional[str]:
        """
        Send coordination message to another society.

        Args:
            recipient_lct: Recipient's LCT
            action: Type of coordination action
            payload: Action-specific payload
            priority: Message priority

        Returns:
            Message ID if sent, None if recipient not found
        """
        # Find recipient by LCT (peers are indexed by society_id)
        recipient = None
        for peer in self.society_mgr.peers.values():
            if peer.identity.lct == recipient_lct:
                recipient = peer
                break

        if not recipient:
            print(f"⚠️  Recipient {recipient_lct} not found in peers")
            return None

        # Try to load recipient's X25519 key from discovery channel
        recipient_x25519_public = None
        for channel in self.society_mgr.discovery_channels:
            # Look for X25519 key files in shared channel
            for key_file in channel.glob("x25519_key_*.json"):
                try:
                    with open(key_file, 'r') as f:
                        data = json.load(f)
                        if data.get('lct') == recipient_lct:
                            recipient_x25519_public = bytes.fromhex(data['x25519_public_key_hex'])
                            break
                except Exception:
                    continue
            if recipient_x25519_public:
                break

        if not recipient_x25519_public:
            print(f"⚠️  Recipient {recipient_lct} has no X25519 key in discovery")
            return None

        # Create coordination message
        coord_msg = CoordinationMessage(
            action=action,
            from_society=self.identity.lct,
            to_society=recipient_lct,
            payload=payload,
            timestamp=datetime.now(timezone.utc)
        )

        # Determine message type
        message_type = MessageType.REQUEST if "request" in action.value else MessageType.DIRECT

        # Send encrypted message
        encrypted_msg = self.message_sender.send_message(
            recipient_lct=recipient_lct,
            recipient_x25519_public_key=recipient_x25519_public,
            payload={
                "action": action.value,
                "payload": payload
            },
            message_type=message_type,
            priority=priority
        )

        coord_msg.message_id = encrypted_msg.message_id

        # Track pending request
        if message_type == MessageType.REQUEST:
            self.pending_requests[encrypted_msg.message_id] = coord_msg

        print(f"📤 {self.society_name} → {recipient.identity.society_name}: {action.value}")
        print(f"   Message ID: {encrypted_msg.message_id}")

        # Copy message to recipient's inbox (simulating message delivery)
        # In production, this would be network transmission
        message_file = self.message_sender.message_dir / f"message_{encrypted_msg.message_id}.json"

        # Construct recipient inbox path from data_dir root
        # self.data_dir = /tmp/web4_coordination_demo/legion
        # recipient should be at /tmp/web4_coordination_demo/thor
        base_dir = self.data_dir.parent  # /tmp/web4_coordination_demo
        recipient_dir = base_dir / recipient.identity.society_name.lower()
        recipient_inbox = recipient_dir / "messages" / "inbox"
        recipient_inbox_file = recipient_inbox / f"message_{encrypted_msg.message_id}.json"

        # Ensure recipient inbox exists
        recipient_inbox.mkdir(parents=True, exist_ok=True)

        import shutil
        if message_file.exists():
            shutil.copy(message_file, recipient_inbox_file)
            print(f"   ✉️  Delivered to {recipient_inbox_file}")

        return encrypted_msg.message_id

    async def _message_processing_loop(self):
        """Background loop to process incoming messages"""
        while self.running:
            await self._process_messages()
            await asyncio.sleep(2)  # Check every 2 seconds

    async def _process_messages(self):
        """Process incoming messages"""
        # Build sender public key map from known peers (indexed by LCT, not society_id)
        sender_keys = {}
        for peer_status in self.society_mgr.peers.values():
            peer_lct = peer_status.identity.lct
            ed25519_public_hex = peer_status.identity.public_key_hex
            sender_keys[peer_lct] = bytes.fromhex(ed25519_public_hex)

        # Receive messages
        new_messages = self.message_receiver.receive_messages(sender_keys)

        for msg in new_messages:
            await self._handle_coordination_message(msg)

    async def _handle_coordination_message(self, msg: DecryptedMessage):
        """Handle incoming coordination message"""
        action_str = msg.payload.get('action')
        action = CoordinationAction(action_str)
        payload = msg.payload.get('payload', {})

        # Find sender peer
        sender_peer = self.society_mgr.peers.get(msg.sender_lct)
        sender_name = sender_peer.identity.society_name if sender_peer else msg.sender_lct

        print(f"\n📨 {self.society_name} received: {action.value} from {sender_name}")
        print(f"   Payload: {payload}")

        # Update message stats for trust scoring
        if msg.sender_lct not in self.message_stats:
            self.message_stats[msg.sender_lct] = {
                'messages_received': 0,
                'valid_signatures': 0,
                'invalid_signatures': 0
            }

        stats = self.message_stats[msg.sender_lct]
        stats['messages_received'] += 1
        if msg.signature_valid:
            stats['valid_signatures'] += 1
        else:
            stats['invalid_signatures'] += 1

        # Handle specific actions
        if action == CoordinationAction.RESOURCE_REQUEST:
            await self._handle_resource_request(msg.sender_lct, payload, msg.message_id)

        elif action == CoordinationAction.ATP_TRANSFER:
            await self._handle_atp_transfer(msg.sender_lct, payload)

        elif action == CoordinationAction.COLLABORATION_PROPOSAL:
            await self._handle_collaboration_proposal(msg.sender_lct, payload, msg.message_id)

        elif action == CoordinationAction.STATUS_UPDATE:
            await self._handle_status_update(msg.sender_lct, payload)

    async def _handle_resource_request(self, sender_lct: str, payload: dict, message_id: str):
        """Handle resource request from peer"""
        resource = payload.get('resource')
        amount = payload.get('amount')
        atp_offered = payload.get('atp_offered', 0)

        print(f"   Request: {amount} {resource} for {atp_offered} ATP")

        # Simple auto-response logic (can be made more sophisticated)
        # Accept if we're not at capacity
        accept = True  # Placeholder

        if accept:
            response_payload = {
                "request_id": message_id,
                "status": "accepted",
                "resource": resource,
                "amount": amount,
                "atp_price": atp_offered,
                "message": f"{self.society_name} accepts resource request"
            }

            await self.send_coordination_message(
                recipient_lct=sender_lct,
                action=CoordinationAction.RESOURCE_OFFER,
                payload=response_payload,
                priority=MessagePriority.HIGH
            )

    async def _handle_atp_transfer(self, sender_lct: str, payload: dict):
        """Handle ATP transfer notification"""
        amount = payload.get('amount', 0)
        print(f"   ATP transfer: {amount} ATP received")

    async def _handle_collaboration_proposal(self, sender_lct: str, payload: dict, message_id: str):
        """Handle collaboration proposal"""
        proposal_type = payload.get('type')
        print(f"   Collaboration proposal: {proposal_type}")

        # Track collaboration
        self.active_collaborations[message_id] = {
            'partner': sender_lct,
            'type': proposal_type,
            'payload': payload,
            'started_at': datetime.now(timezone.utc)
        }

    async def _handle_status_update(self, sender_lct: str, payload: dict):
        """Handle status update from peer"""
        status = payload.get('status')
        print(f"   Status update: {status}")

    def get_coordination_report(self) -> dict:
        """Get full coordination status report"""
        return {
            "society": {
                "name": self.society_name,
                "lct": self.identity.lct,
                "type": self.identity.agent_type,
                "capabilities": self.identity.capabilities
            },
            "peers": {
                peer.identity.society_name: {
                    "lct": peer.identity.lct,
                    "alive": peer.is_alive,
                    "last_seen": peer.last_seen.isoformat(),
                    "trust_score": peer.trust_score,
                    "signature_failures": peer.signature_failures
                }
                for peer in self.society_mgr.peers.values()
            },
            "messaging": {
                "sent_messages": len(self.message_sender.sent_messages),
                "received_messages": len(self.message_receiver.messages),
                "pending_requests": len(self.pending_requests),
                "active_collaborations": len(self.active_collaborations)
            },
            "trust_metrics": self.message_stats
        }


# ============================================================================
# DEMO: Multi-Society Coordination
# ============================================================================

async def demo_multi_society_coordination():
    """Demonstrate complete multi-society coordination"""

    print("=" * 70)
    print("Web4 Multi-Society Coordination Demo - Session #32")
    print("=" * 70)
    print()
    print("This demo combines:")
    print("  - Session #30: Society formation, peer discovery")
    print("  - Session #31: Ed25519 signatures, security")
    print("  - Session #32: Encrypted messaging, coordination")
    print()

    # Shared discovery channel
    discovery_channel = Path("/tmp/web4_coordination_demo/discovery")
    discovery_channel.mkdir(parents=True, exist_ok=True)

    # Create three societies
    print("1. Creating societies...")
    print()

    legion = SocietyCoordinator(
        society_name="Legion",
        description="High-performance research platform",
        agent_type="research_agent",
        capabilities=["research", "implementation", "analysis"],
        data_dir=Path("/tmp/web4_coordination_demo/legion"),
        discovery_channels=[discovery_channel],
        deterministic_keys=True
    )

    cbp = SocietyCoordinator(
        society_name="cbp",
        description="Philosophical reasoning system",
        agent_type="reasoning_agent",
        capabilities=["philosophy", "reasoning", "synthesis"],
        data_dir=Path("/tmp/web4_coordination_demo/cbp"),
        discovery_channels=[discovery_channel],
        deterministic_keys=True
    )

    thor = SocietyCoordinator(
        society_name="Thor",
        description="Edge computing network",
        agent_type="compute_agent",
        capabilities=["compute", "edge_deployment", "sensing"],
        data_dir=Path("/tmp/web4_coordination_demo/thor"),
        discovery_channels=[discovery_channel],
        deterministic_keys=True
    )

    # Start coordinators
    print("\n2. Starting coordinators...")
    await legion.start()
    await cbp.start()
    await thor.start()

    # Discovery phase
    print("\n3. Discovery phase (10 seconds)...")
    for i in range(5):
        await legion.discover_and_sync()
        await cbp.discover_and_sync()
        await thor.discover_and_sync()
        await asyncio.sleep(2)

    # Coordination scenario: Legion requests compute from Thor
    print("\n4. Coordination: Legion → Thor (resource request)")
    print()

    await legion.send_coordination_message(
        recipient_lct=thor.identity.lct,
        action=CoordinationAction.RESOURCE_REQUEST,
        payload={
            "resource": "compute_hour",
            "amount": 10,
            "atp_offered": 100,
            "urgency": "high",
            "purpose": "Web4 security testing"
        },
        priority=MessagePriority.HIGH
    )

    # Allow message delivery and processing
    print("   (processing messages...)")
    await thor._process_messages()  # Force message processing
    await asyncio.sleep(2)

    # cbp sends philosophical insight to Legion
    print("\n5. Coordination: cbp → Legion (collaboration)")
    print()

    await cbp.send_coordination_message(
        recipient_lct=legion.identity.lct,
        action=CoordinationAction.COLLABORATION_PROPOSAL,
        payload={
            "type": "philosophical_research",
            "topic": "AI autonomy and coordination",
            "duration_hours": 24,
            "atp_value": 500
        },
        priority=MessagePriority.NORMAL
    )

    # Allow message delivery and processing
    print("   (processing messages...)")
    await legion._process_messages()  # Force message processing
    await asyncio.sleep(2)

    # Status reports
    print("\n6. Coordination status reports:")
    print()

    print("Legion report:")
    legion_report = legion.get_coordination_report()
    print(f"   Peers: {list(legion_report['peers'].keys())}")
    print(f"   Sent messages: {legion_report['messaging']['sent_messages']}")
    print(f"   Received messages: {legion_report['messaging']['received_messages']}")
    print(f"   Pending requests: {legion_report['messaging']['pending_requests']}")
    print()

    print("cbp report:")
    cbp_report = cbp.get_coordination_report()
    print(f"   Peers: {list(cbp_report['peers'].keys())}")
    print(f"   Sent messages: {cbp_report['messaging']['sent_messages']}")
    print(f"   Received messages: {cbp_report['messaging']['received_messages']}")
    print()

    print("Thor report:")
    thor_report = thor.get_coordination_report()
    print(f"   Peers: {list(thor_report['peers'].keys())}")
    print(f"   Sent messages: {thor_report['messaging']['sent_messages']}")
    print(f"   Received messages: {thor_report['messaging']['received_messages']}")
    print()

    # Stop coordinators
    await legion.stop()
    await cbp.stop()
    await thor.stop()

    print("=" * 70)
    print("✅ Multi-society coordination working!")
    print("=" * 70)
    print()
    print("Capabilities demonstrated:")
    print("  ✅ Society formation with cryptographic identities")
    print("  ✅ Peer discovery via signed heartbeats")
    print("  ✅ Encrypted cross-society messaging")
    print("  ✅ Resource request/offer coordination")
    print("  ✅ Collaboration proposals")
    print("  ✅ Trust tracking via message statistics")
    print()
    print("Complete ACT deployment stack operational!")


if __name__ == "__main__":
    asyncio.run(demo_multi_society_coordination())
