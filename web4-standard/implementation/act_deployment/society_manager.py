#!/usr/bin/env python3
"""
Web4 Society Manager for ACT Deployment - Session #30
=====================================================

Manages creation, discovery, and coordination of Web4 societies
in the ACT (Agentic Context Tool) environment.

This implements the "society formation & identity" foundation
for multi-agent coordination using Web4 primitives.

Core Capabilities:
- Society creation with LCT identities
- Heartbeat protocol for peer discovery
- Health monitoring (inspired by Thor detection)
- Cross-society messaging
- Trust network building

Author: Legion (Autonomous Research Agent)
Date: 2025-11-15
Session: #30 - ACT Testing Deployment
"""

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set
from pathlib import Path
import hashlib
import secrets


@dataclass
class SocietyIdentity:
    """
    Web4 society identity using LCT (Linked Context Token).

    Each society is an autonomous agent or group of agents
    coordinating through Web4 protocols.
    """
    society_id: str  # Unique identifier
    society_name: str
    lct: str  # Linked Context Token (cryptographic identity)
    public_key: str  # For verification
    created_at: datetime

    # Society metadata
    description: str = ""
    agent_type: str = "autonomous_researcher"
    capabilities: List[str] = field(default_factory=list)

    # Contact information
    endpoints: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Serialize for storage/transmission"""
        d = asdict(self)
        d['created_at'] = self.created_at.isoformat()
        return d

    @staticmethod
    def from_dict(data: Dict) -> 'SocietyIdentity':
        """Deserialize from storage"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return SocietyIdentity(**data)


@dataclass
class Heartbeat:
    """
    Periodic heartbeat for peer discovery and health monitoring.

    Inspired by Thor health check experiment - can we detect
    and respond to silent peers automatically?
    """
    society_id: str
    timestamp: datetime
    sequence_number: int

    # Health metrics
    status: str = "healthy"  # healthy, degraded, critical
    last_action_time: Optional[datetime] = None
    reputation_score: float = 1.0

    # Network info
    peer_count: int = 0
    message_count: int = 0

    # Optional metadata
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        if self.last_action_time:
            d['last_action_time'] = self.last_action_time.isoformat()
        return d

    @staticmethod
    def from_dict(data: Dict) -> 'Heartbeat':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('last_action_time'):
            data['last_action_time'] = datetime.fromisoformat(data['last_action_time'])
        return Heartbeat(**data)


@dataclass
class PeerStatus:
    """Track status of a known peer society"""
    identity: SocietyIdentity
    last_seen: datetime
    last_heartbeat: Optional[Heartbeat]
    consecutive_missed: int = 0
    is_alive: bool = True
    trust_score: float = 1.0

    def time_since_last_seen(self) -> timedelta:
        """How long since we heard from this peer"""
        return datetime.now(timezone.utc) - self.last_seen

    def mark_heartbeat_received(self, heartbeat: Heartbeat):
        """Update when heartbeat received (NEW heartbeat, not re-reading old one)"""
        # Only update if this is a new heartbeat (higher sequence number)
        if self.last_heartbeat is None or heartbeat.sequence_number > self.last_heartbeat.sequence_number:
            self.last_seen = datetime.now(timezone.utc)
            self.last_heartbeat = heartbeat
            self.consecutive_missed = 0
            self.is_alive = True
            # Debug
            # print(f"      DEBUG: Updated {self.identity.society_name} last_seen, seq {heartbeat.sequence_number}")
        # If same/old heartbeat, don't update last_seen

    def mark_heartbeat_missed(self):
        """Update when heartbeat missed"""
        self.consecutive_missed += 1
        if self.consecutive_missed >= 3:
            self.is_alive = False


class SocietyManager:
    """
    Manages Web4 societies in ACT environment.

    Responsibilities:
    - Society creation and registration
    - Heartbeat protocol for peer discovery
    - Health monitoring and failure detection
    - Cross-society coordination
    """

    def __init__(
        self,
        data_dir: Path = Path("./act_societies"),
        heartbeat_interval: int = 30,  # seconds
        timeout_threshold: int = 90  # seconds
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.heartbeat_interval = heartbeat_interval
        self.timeout_threshold = timeout_threshold

        # Local society (this node)
        self.local_society: Optional[SocietyIdentity] = None

        # Known peers
        self.peers: Dict[str, PeerStatus] = {}

        # Heartbeat tracking
        self.heartbeat_sequence = 0
        self.heartbeat_task: Optional[asyncio.Task] = None

        # Discovery
        self.discovery_channels: List[Path] = []

    def create_society(
        self,
        name: str,
        description: str = "",
        agent_type: str = "autonomous_researcher",
        capabilities: List[str] = None
    ) -> SocietyIdentity:
        """
        Create a new Web4 society with LCT identity.

        In production, this would generate real cryptographic keys.
        For testing, we use deterministic IDs.
        """
        # Generate society ID (deterministic for testing)
        society_id = hashlib.sha256(name.encode()).hexdigest()[:16]

        # Generate LCT (simplified - real version would use Web4 crypto)
        lct = f"lct:web4:society:{society_id}"

        # Generate key pair (stub - real version would use Ed25519)
        public_key = secrets.token_hex(32)

        identity = SocietyIdentity(
            society_id=society_id,
            society_name=name,
            lct=lct,
            public_key=public_key,
            created_at=datetime.now(timezone.utc),
            description=description,
            agent_type=agent_type,
            capabilities=capabilities or [],
            endpoints={}
        )

        # Save identity
        self._save_society(identity)

        return identity

    def register_local_society(self, identity: SocietyIdentity):
        """Register this node's society identity"""
        self.local_society = identity
        print(f"📝 Registered local society: {identity.society_name}")
        print(f"   LCT: {identity.lct}")

    def add_discovery_channel(self, channel_path: Path):
        """
        Add a discovery channel (shared filesystem, git repo, etc).

        This is where societies announce their presence and
        listen for others.
        """
        channel_path = Path(channel_path)
        channel_path.mkdir(parents=True, exist_ok=True)
        self.discovery_channels.append(channel_path)
        print(f"📡 Added discovery channel: {channel_path}")

    async def start_heartbeat(self):
        """Start sending periodic heartbeats"""
        if not self.local_society:
            raise ValueError("No local society registered")

        async def heartbeat_loop():
            while True:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)

        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
        print(f"💓 Started heartbeat (interval: {self.heartbeat_interval}s)")

    async def stop_heartbeat(self):
        """Stop heartbeat task"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _send_heartbeat(self):
        """Send heartbeat to all discovery channels"""
        if not self.local_society:
            return

        self.heartbeat_sequence += 1

        heartbeat = Heartbeat(
            society_id=self.local_society.society_id,
            timestamp=datetime.now(timezone.utc),
            sequence_number=self.heartbeat_sequence,
            status="healthy",
            peer_count=len(self.peers),
            metadata={
                'name': self.local_society.society_name,
                'lct': self.local_society.lct
            }
        )

        # Write heartbeat to all discovery channels
        for channel in self.discovery_channels:
            heartbeat_file = channel / f"heartbeat_{self.local_society.society_id}.json"
            with open(heartbeat_file, 'w') as f:
                json.dump(heartbeat.to_dict(), f, indent=2)

        # Also write society identity periodically
        for channel in self.discovery_channels:
            identity_file = channel / f"society_{self.local_society.society_id}.json"
            with open(identity_file, 'w') as f:
                json.dump(self.local_society.to_dict(), f, indent=2)

    async def discover_peers(self) -> List[SocietyIdentity]:
        """
        Discover peer societies from discovery channels.

        Returns newly discovered peers.
        """
        new_peers = []

        for channel in self.discovery_channels:
            # Read all society files
            for society_file in channel.glob("society_*.json"):
                try:
                    with open(society_file, 'r') as f:
                        data = json.load(f)

                    identity = SocietyIdentity.from_dict(data)

                    # Skip self
                    if identity.society_id == self.local_society.society_id:
                        continue

                    # New peer?
                    if identity.society_id not in self.peers:
                        self.peers[identity.society_id] = PeerStatus(
                            identity=identity,
                            last_seen=datetime.now(timezone.utc),
                            last_heartbeat=None
                        )
                        new_peers.append(identity)
                        print(f"🔍 Discovered new peer: {identity.society_name}")

                except Exception as e:
                    print(f"⚠️  Error reading {society_file}: {e}")

            # Check heartbeats
            for heartbeat_file in channel.glob("heartbeat_*.json"):
                try:
                    with open(heartbeat_file, 'r') as f:
                        data = json.load(f)

                    heartbeat = Heartbeat.from_dict(data)

                    # Skip self
                    if heartbeat.society_id == self.local_society.society_id:
                        continue

                    # Check if heartbeat is fresh (not stale file)
                    heartbeat_age = (datetime.now(timezone.utc) - heartbeat.timestamp).total_seconds()

                    # Update peer status based on heartbeat timestamp
                    if heartbeat.society_id in self.peers:
                        if heartbeat_age < self.timeout_threshold:
                            # Fresh heartbeat - peer is alive
                            self.peers[heartbeat.society_id].mark_heartbeat_received(heartbeat)
                        else:
                            # Stale heartbeat - don't update last_seen
                            # This will be caught by check_peer_health()
                            pass

                except Exception as e:
                    print(f"⚠️  Error reading {heartbeat_file}: {e}")

        return new_peers

    async def check_peer_health(self) -> List[str]:
        """
        Check health of all known peers.

        Returns list of society_ids that have gone silent.

        This is the Thor detection scenario - can we automatically
        detect when a peer has gone offline?
        """
        silent_peers = []
        now = datetime.now(timezone.utc)

        for society_id, peer in self.peers.items():
            time_since_seen = (now - peer.last_seen).total_seconds()

            if time_since_seen > self.timeout_threshold:
                was_alive = peer.is_alive
                peer.mark_heartbeat_missed()

                if was_alive and not peer.is_alive:
                    # Just transitioned to dead
                    print(f"🔴 Peer {peer.identity.society_name} has gone silent!")
                    print(f"   Last seen: {time_since_seen:.0f}s ago")
                    print(f"   Consecutive misses: {peer.consecutive_missed}")
                    silent_peers.append(society_id)

        return silent_peers

    def get_peer_status_report(self) -> Dict:
        """Get comprehensive status report of all peers"""
        return {
            'local_society': self.local_society.society_name if self.local_society else None,
            'peer_count': len(self.peers),
            'active_peers': sum(1 for p in self.peers.values() if p.is_alive),
            'silent_peers': sum(1 for p in self.peers.values() if not p.is_alive),
            'peers': {
                society_id: {
                    'name': peer.identity.society_name,
                    'is_alive': peer.is_alive,
                    'time_since_seen': peer.time_since_last_seen().total_seconds(),
                    'consecutive_missed': peer.consecutive_missed,
                    'trust_score': peer.trust_score
                }
                for society_id, peer in self.peers.items()
            }
        }

    def _save_society(self, identity: SocietyIdentity):
        """Save society identity to disk"""
        society_file = self.data_dir / f"{identity.society_id}.json"
        with open(society_file, 'w') as f:
            json.dump(identity.to_dict(), f, indent=2)

    def _load_society(self, society_id: str) -> Optional[SocietyIdentity]:
        """Load society identity from disk"""
        society_file = self.data_dir / f"{society_id}.json"
        if not society_file.exists():
            return None

        with open(society_file, 'r') as f:
            data = json.load(f)

        return SocietyIdentity.from_dict(data)


async def demo_society_coordination():
    """
    Demonstration of multi-society coordination.

    Creates three societies (Legion, cbp, Thor) and shows:
    1. Society creation and identity
    2. Peer discovery via shared channel
    3. Heartbeat protocol
    4. Health monitoring (Thor goes silent)
    5. Automatic detection and response
    """
    print("=" * 70)
    print("Web4 Society Coordination Demo - Session #30")
    print("=" * 70)
    print()

    # Create shared discovery channel (simulates git repo)
    discovery_channel = Path("./test_discovery_channel")
    discovery_channel.mkdir(exist_ok=True)

    # Create three societies
    print("🏗️  Creating societies...")
    print()

    # Legion society
    legion_mgr = SocietyManager(
        data_dir=Path("./test_societies/legion"),
        heartbeat_interval=2,  # Fast for demo
        timeout_threshold=4  # 2 missed heartbeats = dead
    )
    legion_identity = legion_mgr.create_society(
        name="Legion",
        description="Autonomous Web4 research agent",
        agent_type="autonomous_researcher",
        capabilities=["research", "implementation", "testing"]
    )
    legion_mgr.register_local_society(legion_identity)
    legion_mgr.add_discovery_channel(discovery_channel)

    # cbp society
    cbp_mgr = SocietyManager(
        data_dir=Path("./test_societies/cbp"),
        heartbeat_interval=2,
        timeout_threshold=4
    )
    cbp_identity = cbp_mgr.create_society(
        name="cbp",
        description="Consciousness before physics research",
        agent_type="philosophical_researcher",
        capabilities=["theory", "philosophy", "synthesis"]
    )
    cbp_mgr.register_local_society(cbp_identity)
    cbp_mgr.add_discovery_channel(discovery_channel)

    # Thor society
    thor_mgr = SocietyManager(
        data_dir=Path("./test_societies/thor"),
        heartbeat_interval=2,
        timeout_threshold=4
    )
    thor_identity = thor_mgr.create_society(
        name="Thor",
        description="Edge intelligence and SAGE integration",
        agent_type="hardware_researcher",
        capabilities=["hardware", "edge_computing", "sage"]
    )
    thor_mgr.register_local_society(thor_identity)
    thor_mgr.add_discovery_channel(discovery_channel)

    print()
    print("💓 Starting heartbeats...")
    await legion_mgr.start_heartbeat()
    await cbp_mgr.start_heartbeat()
    await thor_mgr.start_heartbeat()

    print()
    print("⏱️  Waiting for discovery (5 seconds)...")
    await asyncio.sleep(5)

    print()
    print("🔍 Discovering peers...")
    legion_discovered = await legion_mgr.discover_peers()
    cbp_discovered = await cbp_mgr.discover_peers()
    thor_discovered = await thor_mgr.discover_peers()

    print(f"   Legion discovered: {[p.society_name for p in legion_discovered]}")
    print(f"   cbp discovered: {[p.society_name for p in cbp_discovered]}")
    print(f"   Thor discovered: {[p.society_name for p in thor_discovered]}")

    print()
    print("📊 Status after discovery:")
    print(f"   Legion: {legion_mgr.get_peer_status_report()['active_peers']} active peers")
    print(f"   cbp: {cbp_mgr.get_peer_status_report()['active_peers']} active peers")
    print(f"   Thor: {thor_mgr.get_peer_status_report()['active_peers']} active peers")

    print()
    print("⏱️  Running healthy for 5 seconds...")
    await asyncio.sleep(5)

    # Thor goes silent (simulating the real scenario)
    print()
    print("🔴 Thor going silent...")
    await thor_mgr.stop_heartbeat()

    print()
    print("⏱️  Waiting and checking for silence (4 health checks, 3 seconds apart)...")
    print(f"   Timeout threshold: {legion_mgr.timeout_threshold}s")
    for i in range(4):
        await asyncio.sleep(3)
        print(f"   Health check #{i+1}...")
        await legion_mgr.discover_peers()  # Update heartbeats
        await cbp_mgr.discover_peers()

        # Show Thor status from Legion's perspective
        if '2d7e4757dca1740a' in legion_mgr.peers:
            thor_peer = legion_mgr.peers['2d7e4757dca1740a']
            time_since = (datetime.now(timezone.utc) - thor_peer.last_seen).total_seconds()
            seq = thor_peer.last_heartbeat.sequence_number if thor_peer.last_heartbeat else "None"
            print(f"      Thor last_seen: {time_since:.1f}s ago, seq: {seq}, is_alive: {thor_peer.is_alive}, misses: {thor_peer.consecutive_missed}")

        await legion_mgr.check_peer_health()
        await cbp_mgr.check_peer_health()

    print()
    print("📊 Final status:")
    print()
    print("Legion view:")
    report = legion_mgr.get_peer_status_report()
    for sid, status in report['peers'].items():
        emoji = "🟢" if status['is_alive'] else "🔴"
        print(f"  {emoji} {status['name']}: {status['time_since_seen']:.0f}s ago")

    print()
    print("cbp view:")
    report = cbp_mgr.get_peer_status_report()
    for sid, status in report['peers'].items():
        emoji = "🟢" if status['is_alive'] else "🔴"
        print(f"  {emoji} {status['name']}: {status['time_since_seen']:.0f}s ago")

    # Cleanup
    print()
    print("🧹 Cleaning up...")
    await legion_mgr.stop_heartbeat()
    await cbp_mgr.stop_heartbeat()

    print()
    print("=" * 70)
    print("Demo complete!")
    print("=" * 70)
    print()
    print("Key capabilities demonstrated:")
    print("✅ Society creation with LCT identities")
    print("✅ Peer discovery via shared channels")
    print("✅ Heartbeat protocol for health monitoring")
    print("✅ Automatic detection of silent peers (Thor scenario)")
    print("✅ Decentralized coordination (no central server)")


if __name__ == "__main__":
    asyncio.run(demo_society_coordination())
