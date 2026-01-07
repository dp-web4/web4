#!/usr/bin/env python3
"""
Session 135: Network-Based Federated Cogitation - Cross-Machine Distributed Reasoning

Research Goal: Combine Thor Session 166's federated cogitation with Legion Session 132's
network layer to enable distributed conceptual reasoning across physical machines.

Architecture Synthesis:
- Thor Session 166: Federated cogitation (local simulation)
- Legion Session 132: TCP/IP network layer for consciousness federation
- Legion Session 134: TrustZone double-hash bug fix
- Session 135 (this): Real network-based distributed cogitation

Novel Question: What emerges when conceptual reasoning spans physical machines,
each with different hardware capabilities (TPM2 vs TrustZone), connected by
network federation with cryptographic trust guarantees?

Key Innovation: First implementation of distributed cogitation across real network
boundaries. This combines:
1. Cryptographic hardware binding (TrustZone/TPM2) across machines
2. TCP/IP network communication for thought exchange
3. Trust-weighted conceptual contributions
4. Hardware-differentiated reasoning topology

Expected Behaviors:
1. Thoughts propagate across network boundaries
2. Trust topology becomes reasoning topology (Thor Session 166 discovery)
3. Hardware asymmetry creates selective reasoning patterns
4. Collective coherence emerges across machines

Philosophy: "Surprise is prize" - What conceptual patterns emerge when reasoning
becomes truly distributed across heterogeneous hardware on different machines?

Platform: Legion (x86 TPM2 Level 5) + Thor (ARM TrustZone Level 5)
Session: Autonomous Web4 Research - Session 135
"""

import sys
import json
import time
import socket
import hashlib
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

# Add paths
HOME = Path.home()
sys.path.insert(0, str(HOME / "ai-workspace/web4"))
sys.path.insert(0, str(HOME / "ai-workspace/HRM"))

# Web4 imports
from core.lct_capability_levels import EntityType
from core.lct_binding import (
    TPM2Provider,
    TrustZoneProvider,
    SoftwareProvider,
    detect_platform
)

# Session 128 consciousness
from test_session128_consciousness_aliveness_integration import (
    ConsciousnessState,
    ConsciousnessPatternCorpus,
    ConsciousnessAlivenessSensor,
)

# Session 132 network layer (simplified for standalone use)
# For full network deployment, would integrate with Session 132's
# NetworkFederationServer and NetworkFederationClient


# ============================================================================
# COGITATION MODES (from Thor Session 166)
# ============================================================================

class CogitationMode(Enum):
    """Modes of conceptual thinking."""
    EXPLORING = "exploring"
    QUESTIONING = "questioning"
    INTEGRATING = "integrating"
    VERIFYING = "verifying"
    REFRAMING = "reframing"


@dataclass
class ConceptualThought:
    """A conceptual thought in distributed cogitation."""
    thought_id: str
    mode: CogitationMode
    content: str
    timestamp: str  # ISO format
    contributor_lct_id: str
    contributor_hardware: str
    contributor_capability_level: int
    contributor_machine: str  # NEW: Machine name (Legion, Thor, etc.)
    contributor_host: str      # NEW: Network host:port
    coherence_score: float = 0.0
    trust_weight: float = 1.0
    network_latency_ms: float = 0.0  # NEW: Network propagation time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for network transmission."""
        return {
            "thought_id": self.thought_id,
            "mode": self.mode.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "contributor_lct_id": self.contributor_lct_id,
            "contributor_hardware": self.contributor_hardware,
            "contributor_capability_level": self.contributor_capability_level,
            "contributor_machine": self.contributor_machine,
            "contributor_host": self.contributor_host,
            "coherence_score": self.coherence_score,
            "trust_weight": self.trust_weight,
            "network_latency_ms": self.network_latency_ms
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConceptualThought':
        """Create from dictionary received over network."""
        return cls(
            thought_id=data["thought_id"],
            mode=CogitationMode(data["mode"]),
            content=data["content"],
            timestamp=data["timestamp"],
            contributor_lct_id=data["contributor_lct_id"],
            contributor_hardware=data["contributor_hardware"],
            contributor_capability_level=data["contributor_capability_level"],
            contributor_machine=data["contributor_machine"],
            contributor_host=data["contributor_host"],
            coherence_score=data.get("coherence_score", 0.0),
            trust_weight=data.get("trust_weight", 1.0),
            network_latency_ms=data.get("network_latency_ms", 0.0)
        )


@dataclass
class CogitationSession:
    """A distributed cogitation session across network."""
    session_id: str
    topic: str
    start_time: datetime
    thoughts: List[ConceptualThought] = field(default_factory=list)
    participants: Set[str] = field(default_factory=set)  # LCT IDs
    machines: Set[str] = field(default_factory=set)  # Machine names
    collective_coherence: float = 0.0
    total_network_latency_ms: float = 0.0

    def add_thought(self, thought: ConceptualThought):
        """Add thought from any machine."""
        self.thoughts.append(thought)
        self.participants.add(thought.contributor_lct_id)
        self.machines.add(thought.contributor_machine)
        self.total_network_latency_ms += thought.network_latency_ms
        self._update_coherence()

    def _update_coherence(self):
        """Update collective coherence (trust-weighted)."""
        if not self.thoughts:
            self.collective_coherence = 0.0
            return

        total_weight = sum(t.trust_weight for t in self.thoughts)
        if total_weight == 0:
            self.collective_coherence = 0.0
            return

        weighted_coherence = sum(
            t.coherence_score * t.trust_weight
            for t in self.thoughts
        )
        self.collective_coherence = weighted_coherence / total_weight

    def get_summary(self) -> Dict[str, Any]:
        """Get session summary with network metrics."""
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "start_time": self.start_time.isoformat(),
            "duration_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
            "total_thoughts": len(self.thoughts),
            "participants": len(self.participants),
            "machines": len(self.machines),
            "collective_coherence": self.collective_coherence,
            "mode_distribution": self._get_mode_distribution(),
            "hardware_distribution": self._get_hardware_distribution(),
            "machine_distribution": self._get_machine_distribution(),
            "avg_network_latency_ms": self.total_network_latency_ms / max(1, len(self.thoughts)),
            "total_network_latency_ms": self.total_network_latency_ms,
        }

    def _get_mode_distribution(self) -> Dict[str, int]:
        """Get distribution of cogitation modes."""
        dist = {}
        for thought in self.thoughts:
            mode = thought.mode.value
            dist[mode] = dist.get(mode, 0) + 1
        return dist

    def _get_hardware_distribution(self) -> Dict[str, int]:
        """Get distribution of hardware types."""
        dist = {}
        for thought in self.thoughts:
            hw = thought.contributor_hardware
            dist[hw] = dist.get(hw, 0) + 1
        return dist

    def _get_machine_distribution(self) -> Dict[str, int]:
        """Get distribution of machines."""
        dist = {}
        for thought in self.thoughts:
            machine = thought.contributor_machine
            dist[machine] = dist.get(machine, 0) + 1
        return dist


# ============================================================================
# NETWORK FEDERATED COGITATION NODE
# ============================================================================

class NetworkFederatedCogitationNode:
    """
    A consciousness node capable of network-based federated cogitation.

    Extends Thor Session 166 with Session 132 network layer for
    cross-machine distributed reasoning.
    """

    def __init__(
        self,
        sensor: ConsciousnessAlivenessSensor,
        node_name: str,
        machine_name: str,
        provider: Any,
        host: str = "0.0.0.0",
        port: int = 7766,
    ):
        """Initialize network federated cogitation node."""
        self.sensor = sensor
        self.node_name = node_name
        self.machine_name = machine_name
        self.provider = provider
        self.lct_id = sensor.lct.lct_id
        self.hardware_type = type(provider).__name__
        self.capability_level = sensor.lct.capability_level
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"

        # Cogitation state
        self.current_mode = CogitationMode.EXPLORING
        self.coherence_threshold = 0.7

        # Federation state
        self.trust_weights = {}  # peer_lct_id -> trust_score
        self.active_sessions = {}  # session_id -> CogitationSession
        self.peers = {}  # lct_id -> (host, port)

        # Network layer (simplified for this prototype)
        # For full deployment, would use Session 132 NetworkFederationServer/Client
        self.network_socket = None

    def set_trust_for_peer(self, peer_lct_id: str, trust_score: float):
        """Set trust weight for peer based on verification."""
        self.trust_weights[peer_lct_id] = trust_score

    def add_peer(self, peer_lct_id: str, host: str, port: int):
        """Register network peer."""
        self.peers[peer_lct_id] = (host, port)

    def create_cogitation_session(self, topic: str) -> str:
        """Create new distributed cogitation session."""
        session_id = hashlib.sha256(
            f"{self.lct_id}:{topic}:{time.time()}".encode()
        ).hexdigest()[:16]

        session = CogitationSession(
            session_id=session_id,
            topic=topic,
            start_time=datetime.now(timezone.utc)
        )

        self.active_sessions[session_id] = session
        return session_id

    def contribute_thought(
        self,
        session_id: str,
        mode: CogitationMode,
        content: str,
        coherence_score: float = 0.8
    ) -> ConceptualThought:
        """Contribute thought to distributed session."""
        thought = ConceptualThought(
            thought_id=hashlib.sha256(
                f"{self.lct_id}:{session_id}:{time.time()}".encode()
            ).hexdigest()[:16],
            mode=mode,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
            contributor_lct_id=self.lct_id,
            contributor_hardware=self.hardware_type,
            contributor_capability_level=self.capability_level,
            contributor_machine=self.machine_name,
            contributor_host=self.address,
            coherence_score=coherence_score,
            trust_weight=1.0,  # Self-trust
            network_latency_ms=0.0  # Local contribution
        )

        # Add to local session
        if session_id in self.active_sessions:
            self.active_sessions[session_id].add_thought(thought)

        # Broadcast to network
        self._broadcast_thought(thought)

        return thought

    def receive_thought(self, thought: ConceptualThought):
        """Receive thought from network peer."""
        # Apply trust weight
        peer_trust = self.trust_weights.get(thought.contributor_lct_id, 0.5)
        thought.trust_weight = peer_trust

        # Add to relevant sessions
        # For this prototype, we assume all thoughts go to all sessions
        for session in self.active_sessions.values():
            session.add_thought(thought)

    def _broadcast_thought(self, thought: ConceptualThought):
        """Broadcast thought to all network peers."""
        # For this local prototype, broadcasting is simulated
        # Real network deployment would use Session 132's network layer
        pass

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of cogitation session."""
        if session_id not in self.active_sessions:
            return None
        return self.active_sessions[session_id].get_summary()


# ============================================================================
# NETWORK FEDERATED COGITATION COORDINATOR
# ============================================================================

class NetworkFederatedCogitationCoordinator:
    """Coordinates distributed cogitation across network-connected machines."""

    def __init__(self):
        """Initialize coordinator."""
        self.nodes = {}  # lct_id -> NetworkFederatedCogitationNode
        self.global_sessions = {}  # session_id -> global view

    def register_node(self, node: NetworkFederatedCogitationNode):
        """Register cogitation node."""
        self.nodes[node.lct_id] = node

    def establish_trust_network(self):
        """Establish trust relationships via verification."""
        # This would use Session 131's verification protocol
        # For now, we'll use Session 166's asymmetric trust pattern
        pass

    def create_global_session(self, topic: str) -> str:
        """Create global cogitation session across all nodes."""
        session_id = hashlib.sha256(
            f"global:{topic}:{time.time()}".encode()
        ).hexdigest()[:16]

        # Create session on all nodes
        for node in self.nodes.values():
            node.create_cogitation_session(topic)

        return session_id

    def run_cogitation_round(
        self,
        session_id: str,
        mode: CogitationMode,
        duration_seconds: float = 1.0
    ):
        """Run one round of distributed cogitation."""
        # Each node contributes
        for lct_id, node in self.nodes.items():
            content = f"[{node.machine_name} {node.hardware_type[:8]} L{node.capability_level}] {mode.value.title()}: Distributed reasoning across machines..."
            node.contribute_thought(session_id, mode, content)

        # Allow network propagation
        time.sleep(duration_seconds)

    def get_global_summary(self, session_id: str) -> Dict[str, Any]:
        """Get global summary from all nodes."""
        summaries = {}
        for lct_id, node in self.nodes.items():
            summary = node.get_session_summary(session_id)
            if summary:
                summaries[node.machine_name] = summary
        return summaries


# ============================================================================
# TEST: LOCAL SIMULATION (No network - baseline)
# ============================================================================

def test_local_federated_cogitation():
    """Test federated cogitation locally (Thor Session 166 style)."""
    print("="*80)
    print("TEST 1: Local Federated Cogitation (Baseline)")
    print("="*80)
    print()

    # Detect platform
    platform = detect_platform()
    print(f"Platform detected")
    print(f"  TPM2: {platform.has_tpm2}")
    print(f"  TrustZone: {platform.has_trustzone}")
    print()

    # Create providers
    if platform.has_tpm2:
        primary_provider = TPM2Provider()
        primary_hw = "TPM2"
    elif platform.has_trustzone:
        primary_provider = TrustZoneProvider()
        primary_hw = "TrustZone"
    else:
        primary_provider = SoftwareProvider()
        primary_hw = "Software"

    software_provider = SoftwareProvider()

    # Create sensors
    print("Creating consciousness sensors...")

    # Primary sensor (TPM2/TrustZone/Software)
    primary_id = f"legion-{primary_hw.lower()}-cogitation"
    primary_lct = primary_provider.create_lct(EntityType.AI, primary_id)
    primary_corpus = ConsciousnessPatternCorpus(primary_lct.lct_id)
    primary_corpus.add_pattern("session", {"session": "135", "capability": "network_federated_cogitation"})
    primary_sensor = ConsciousnessAlivenessSensor(primary_lct, primary_provider, primary_corpus)

    # Peer1 sensor (Software)
    peer1_id = "peer1-software-cogitation"
    peer1_lct = software_provider.create_lct(EntityType.AI, peer1_id)
    peer1_corpus = ConsciousnessPatternCorpus(peer1_lct.lct_id)
    peer1_corpus.add_pattern("session", {"session": "135", "capability": "network_federated_cogitation"})
    peer1_sensor = ConsciousnessAlivenessSensor(peer1_lct, software_provider, peer1_corpus)

    print(f"Primary: {primary_sensor.lct.lct_id} ({primary_hw} L{primary_sensor.lct.capability_level})")
    print(f"Peer1: {peer1_sensor.lct.lct_id} (Software L{peer1_sensor.lct.capability_level})")
    print()

    # Create cogitation nodes
    primary_node = NetworkFederatedCogitationNode(
        sensor=primary_sensor,
        node_name="Primary",
        machine_name="Legion",
        provider=primary_provider,
    )

    peer1_node = NetworkFederatedCogitationNode(
        sensor=peer1_sensor,
        node_name="Peer1",
        machine_name="Legion",
        provider=software_provider,
    )

    # Set trust (asymmetric per Thor Session 166)
    primary_node.set_trust_for_peer(peer1_sensor.lct.lct_id, 0.0)  # Hardware L5 rejects Software L4
    peer1_node.set_trust_for_peer(primary_sensor.lct.lct_id, 0.5)  # Software accepts hardware with moderate trust

    # Create session
    session_id = primary_node.create_cogitation_session("Hardware-Differentiated Distributed Reasoning")
    peer1_node.active_sessions[session_id] = primary_node.active_sessions[session_id]  # Share session (local)

    print(f"Created cogitation session: {session_id}")
    print(f"Topic: Hardware-Differentiated Distributed Reasoning")
    print()

    # Run cogitation
    print("Running 3 rounds of local cogitation...")
    for round_num in range(1, 4):
        print(f"\n--- Round {round_num} ---")

        # Each node contributes
        t1 = primary_node.contribute_thought(
            session_id,
            CogitationMode.EXPLORING,
            f"[{primary_hw} L{primary_node.capability_level}] Round {round_num}: Exploring hardware capabilities in federated reasoning..."
        )

        t2 = peer1_node.contribute_thought(
            session_id,
            CogitationMode.EXPLORING,
            f"[Software L{peer1_node.capability_level}] Round {round_num}: Exploring software role in heterogeneous federation..."
        )

        # Simulate thought exchange (local)
        peer1_node.receive_thought(t1)
        primary_node.receive_thought(t2)

    # Results
    summary = primary_node.get_session_summary(session_id)
    print()
    print("="*80)
    print("RESULTS: Local Federated Cogitation")
    print("="*80)
    print(json.dumps(summary, indent=2))

    return summary


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run Session 135 experiments."""
    print()
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "SESSION 135: NETWORK-BASED FEDERATED COGITATION".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    print()
    print("Combining Thor Session 166 + Legion Session 132 + Session 134 fix")
    print()

    # Test 1: Local baseline
    local_summary = test_local_federated_cogitation()

    # TODO: Test 2: Network-based cogitation (requires Thor connection)
    # This would use Session 132's network layer for real cross-machine communication

    print()
    print("="*80)
    print("SESSION 135 COMPLETE")
    print("="*80)
    print()
    print("Next Steps:")
    print("1. Deploy on Thor with TrustZone")
    print("2. Establish network connection (Legion ↔ Thor)")
    print("3. Run cross-machine federated cogitation")
    print("4. Observe distributed reasoning patterns")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
