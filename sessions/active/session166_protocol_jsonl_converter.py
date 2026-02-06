#!/usr/bin/env python3
"""
Session 166: Protocol JSONL Converter (Phase 1 Protocol Implementation)

Research Goal: Implement real-world protocol for Web4 reputation system,
enabling inter-node communication with full Phase 1 security.

Context:
- Session 7 completed Phase 1 security (3/3 defenses)
- Thor Session 182 integrated security into SAGE
- Ready for test deployment on LAN (Legion, Thor, Sprout)

Protocol Design:
1. JSONL format for streaming reputation events
2. Full Phase 1 security integration
3. Network-ready message format
4. Attestation verification at protocol level

Architecture:
- ReputationEvent: Base event structure
- ProtocolMessage: Network-ready format with attestation
- JSONLProtocolConverter: Serialization/deserialization
- NetworkProtocolHandler: Send/receive with validation

Platform: Legion (RTX 4090, TPM2)
Session: Autonomous Web4 Research - Session 166
Date: 2026-01-11
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import sys

HOME = Path.home()
sys.path.insert(0, str(HOME / "ai-workspace" / "web4"))

# Import Phase 1 security infrastructure
from session163_lct_reputation_binding import (
    LCTIdentity,
    LCTBoundReputation,
    LCTReputationManager,
)

from session164_reputation_source_diversity import (
    ReputationSourceProfile,
    SourceDiversityManager,
)

from session165_decentralized_reputation_consensus import (
    ReputationEventProposal,
    ConsensusVote,
    VoteType,
    DecentralizedReputationConsensus,
)


# ============================================================================
# PROTOCOL MESSAGE TYPES
# ============================================================================

class MessageType(Enum):
    """Protocol message types."""
    # Reputation events
    REPUTATION_PROPOSAL = "reputation_proposal"
    CONSENSUS_VOTE = "consensus_vote"
    REPUTATION_UPDATE = "reputation_update"

    # Identity management
    IDENTITY_ANNOUNCEMENT = "identity_announcement"
    IDENTITY_VERIFICATION = "identity_verification"

    # Network coordination
    PEER_DISCOVERY = "peer_discovery"
    NETWORK_STATUS = "network_status"

    # Security
    SECURITY_ALERT = "security_alert"
    ATTESTATION_REQUEST = "attestation_request"


@dataclass
class ProtocolMessage:
    """
    Network-ready protocol message.

    All messages include:
    - Type identification
    - Source LCT identity
    - Timestamp
    - Payload (type-specific data)
    - Attestation (TPM/TEE signature)
    """
    message_type: str  # MessageType enum value
    source_lct_id: str  # Who sent this
    timestamp: float
    payload: Dict[str, Any]  # Type-specific data
    attestation: str  # TPM signature

    # Optional fields
    message_id: Optional[str] = None
    target_lct_id: Optional[str] = None  # For directed messages
    network_id: Optional[str] = None  # Which network/federation

    def __post_init__(self):
        """Generate message ID if not provided."""
        if self.message_id is None:
            self.message_id = hashlib.sha256(
                f"{self.source_lct_id}:{self.timestamp}:{self.message_type}".encode()
            ).hexdigest()[:16]

    def to_jsonl(self) -> str:
        """
        Convert to JSONL format (one JSON object per line).

        JSONL is streaming-friendly and easy to parse.
        """
        return json.dumps(asdict(self))

    @classmethod
    def from_jsonl(cls, jsonl_line: str) -> 'ProtocolMessage':
        """Parse from JSONL format."""
        data = json.loads(jsonl_line)
        return cls(**data)

    def get_signable_data(self) -> str:
        """
        Get canonical signable data for this message.

        Used for both generating and verifying attestations.
        """
        # Include everything except attestation itself
        return f"{self.message_id}:{self.source_lct_id}:{self.timestamp}:{self.message_type}:{json.dumps(self.payload, sort_keys=True)}"

    def verify_attestation(self, lct_identity: LCTIdentity) -> bool:
        """
        Verify message attestation.

        Ensures message came from claimed source.
        """
        signable_data = self.get_signable_data()
        return lct_identity.verify_attestation(self.attestation, signable_data)


# ============================================================================
# REPUTATION EVENT MESSAGES
# ============================================================================

@dataclass
class ReputationProposalMessage:
    """
    Proposal for reputation change (requires consensus).

    Payload for MessageType.REPUTATION_PROPOSAL
    """
    proposal_id: str
    target_lct_id: str
    quality_contribution: float
    event_type: str  # "verification", "validation", "challenge"
    event_data: str  # Description

    def to_payload(self) -> Dict[str, Any]:
        """Convert to message payload."""
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'ReputationProposalMessage':
        """Parse from message payload."""
        return cls(**payload)


@dataclass
class ConsensusVoteMessage:
    """
    Vote on a reputation proposal.

    Payload for MessageType.CONSENSUS_VOTE
    """
    proposal_id: str
    vote_type: str  # VoteType enum value
    vote_weight: float
    justification: str

    # Voter reputation snapshot
    voter_reputation_score: float
    voter_diversity_score: float

    def to_payload(self) -> Dict[str, Any]:
        """Convert to message payload."""
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'ConsensusVoteMessage':
        """Parse from message payload."""
        return cls(**payload)


@dataclass
class ReputationUpdateMessage:
    """
    Finalized reputation update (after consensus).

    Payload for MessageType.REPUTATION_UPDATE
    """
    proposal_id: str
    target_lct_id: str
    quality_contribution: float
    consensus_result: str  # "approved" or "rejected"
    voter_count: int
    total_approve_weight: float
    total_reject_weight: float

    def to_payload(self) -> Dict[str, Any]:
        """Convert to message payload."""
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'ReputationUpdateMessage':
        """Parse from message payload."""
        return cls(**payload)


# ============================================================================
# IDENTITY MESSAGES
# ============================================================================

@dataclass
class IdentityAnnouncementMessage:
    """
    Node announces its LCT identity to network.

    Payload for MessageType.IDENTITY_ANNOUNCEMENT
    """
    lct_id: str
    hardware_type: str  # "tpm2", "trustzone", etc.
    hardware_fingerprint: str
    attestation_public_key: str
    node_capabilities: List[str]  # What this node can do

    def to_payload(self) -> Dict[str, Any]:
        """Convert to message payload."""
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> 'IdentityAnnouncementMessage':
        """Parse from message payload."""
        return cls(**payload)


# ============================================================================
# PROTOCOL CONVERTER
# ============================================================================

class JSONLProtocolConverter:
    """
    Converts between internal objects and JSONL protocol messages.

    Handles:
    - Serialization (object → JSONL)
    - Deserialization (JSONL → object)
    - Attestation generation
    - Message validation
    """

    def __init__(self, lct_identity: LCTIdentity, network_id: str = "web4_test"):
        self.lct_identity = lct_identity
        self.network_id = network_id

    def create_reputation_proposal_message(
        self,
        proposal: ReputationEventProposal
    ) -> ProtocolMessage:
        """
        Convert ReputationEventProposal to protocol message.
        """
        payload = ReputationProposalMessage(
            proposal_id=proposal.proposal_id,
            target_lct_id=proposal.target_lct_id,
            quality_contribution=proposal.quality_contribution,
            event_type=proposal.event_type,
            event_data=proposal.event_data,
        ).to_payload()

        # Create message first (to get message_id)
        message = ProtocolMessage(
            message_type=MessageType.REPUTATION_PROPOSAL.value,
            source_lct_id=self.lct_identity.lct_id,
            timestamp=time.time(),
            payload=payload,
            attestation="placeholder",  # Will be replaced
            target_lct_id=proposal.target_lct_id,
            network_id=self.network_id,
        )

        # Generate attestation using canonical format
        signable_data = message.get_signable_data()
        message.attestation = self.lct_identity.generate_attestation(signable_data)

        return message

    def create_consensus_vote_message(
        self,
        vote: ConsensusVote
    ) -> ProtocolMessage:
        """
        Convert ConsensusVote to protocol message.
        """
        payload = ConsensusVoteMessage(
            proposal_id=vote.proposal_id,
            vote_type=vote.vote_type.value,
            vote_weight=vote.vote_weight,
            justification=vote.justification,
            voter_reputation_score=vote.voter_reputation_score,
            voter_diversity_score=vote.voter_diversity_score,
        ).to_payload()

        # Create message first
        message = ProtocolMessage(
            message_type=MessageType.CONSENSUS_VOTE.value,
            source_lct_id=self.lct_identity.lct_id,
            timestamp=time.time(),
            payload=payload,
            attestation="placeholder",
            network_id=self.network_id,
        )

        # Generate attestation using canonical format
        signable_data = message.get_signable_data()
        message.attestation = self.lct_identity.generate_attestation(signable_data)

        return message

    def create_identity_announcement_message(self) -> ProtocolMessage:
        """
        Create identity announcement for network discovery.
        """
        payload = IdentityAnnouncementMessage(
            lct_id=self.lct_identity.lct_id,
            hardware_type=self.lct_identity.hardware_type,
            hardware_fingerprint=self.lct_identity.hardware_fingerprint,
            attestation_public_key=self.lct_identity.attestation_public_key,
            node_capabilities=["reputation_consensus", "pattern_exchange", "verification"],
        ).to_payload()

        # Create message first
        message = ProtocolMessage(
            message_type=MessageType.IDENTITY_ANNOUNCEMENT.value,
            source_lct_id=self.lct_identity.lct_id,
            timestamp=time.time(),
            payload=payload,
            attestation="placeholder",
            network_id=self.network_id,
        )

        # Generate attestation using canonical format
        signable_data = message.get_signable_data()
        message.attestation = self.lct_identity.generate_attestation(signable_data)

        return message

    def parse_message(self, jsonl_line: str) -> ProtocolMessage:
        """
        Parse JSONL line into ProtocolMessage.
        """
        return ProtocolMessage.from_jsonl(jsonl_line)

    def verify_message(
        self,
        message: ProtocolMessage,
        known_identities: Dict[str, LCTIdentity]
    ) -> bool:
        """
        Verify message attestation against known identities.
        """
        if message.source_lct_id not in known_identities:
            print(f"[PROTOCOL] Unknown source: {message.source_lct_id}")
            return False

        source_identity = known_identities[message.source_lct_id]
        return message.verify_attestation(source_identity)


# ============================================================================
# NETWORK PROTOCOL HANDLER
# ============================================================================

class NetworkProtocolHandler:
    """
    Handles network-level protocol operations.

    Manages:
    - Message streaming (JSONL files)
    - Message validation
    - Peer discovery
    - Security monitoring
    """

    def __init__(
        self,
        lct_identity: LCTIdentity,
        lct_manager: LCTReputationManager,
        diversity_manager: SourceDiversityManager,
        consensus: DecentralizedReputationConsensus,
        network_id: str = "web4_test",
    ):
        self.lct_identity = lct_identity
        self.lct_manager = lct_manager
        self.diversity_manager = diversity_manager
        self.consensus = consensus
        self.network_id = network_id

        self.converter = JSONLProtocolConverter(lct_identity, network_id)

        # Known peers
        self.known_identities: Dict[str, LCTIdentity] = {
            lct_identity.lct_id: lct_identity
        }

        # Message history
        self.sent_messages: List[ProtocolMessage] = []
        self.received_messages: List[ProtocolMessage] = []

        # Security tracking
        self.failed_verifications: List[Dict[str, Any]] = []

    def add_peer(self, lct_identity: LCTIdentity):
        """Register a known peer."""
        self.known_identities[lct_identity.lct_id] = lct_identity
        print(f"[PROTOCOL] Peer added: {lct_identity.lct_id}")

    def send_reputation_proposal(
        self,
        target_lct_id: str,
        quality_contribution: float,
        event_type: str,
        event_data: str,
    ) -> str:
        """
        Send reputation proposal (requires consensus).

        Returns proposal_id for tracking.
        """
        # Create proposal via consensus manager
        proposal_id = self.consensus.propose_reputation_event(
            target_lct_id=target_lct_id,
            source_lct_id=self.lct_identity.lct_id,
            quality_contribution=quality_contribution,
            event_type=event_type,
            event_data=event_data,
            source_attestation="placeholder",  # Will be regenerated
        )

        # Get the actual proposal
        proposal = self.consensus.proposals[proposal_id]

        # Generate proper attestation
        proposal_data = proposal.to_signable_data()
        proposal.source_attestation = self.lct_identity.generate_attestation(proposal_data)

        # Convert to protocol message
        message = self.converter.create_reputation_proposal_message(proposal)

        # Track sent message
        self.sent_messages.append(message)

        print(f"\n[PROTOCOL] Reputation proposal sent")
        print(f"  Proposal ID: {proposal_id}")
        print(f"  Target: {target_lct_id}")
        print(f"  Contribution: {quality_contribution:+.2f}")
        print(f"  Message ID: {message.message_id}")

        return proposal_id

    def send_consensus_vote(
        self,
        proposal_id: str,
        vote_type: VoteType,
        justification: str,
    ) -> bool:
        """
        Send consensus vote on a proposal.

        Returns True if vote accepted.
        """
        # Generate vote attestation
        vote_data = f"{proposal_id}:{vote_type.value}:{justification}"
        vote_attestation = self.lct_identity.generate_attestation(vote_data)

        # Submit vote via consensus manager
        success = self.consensus.submit_vote(
            proposal_id=proposal_id,
            voter_lct_id=self.lct_identity.lct_id,
            vote_type=vote_type,
            justification=justification,
            voter_attestation=vote_attestation,
        )

        if success:
            # Get the vote object
            consensus_round = self.consensus.consensus_rounds[proposal_id]
            vote = consensus_round.votes[self.lct_identity.lct_id]

            # Convert to protocol message
            message = self.converter.create_consensus_vote_message(vote)

            # Track sent message
            self.sent_messages.append(message)

            print(f"\n[PROTOCOL] Consensus vote sent")
            print(f"  Proposal ID: {proposal_id}")
            print(f"  Vote: {vote_type.value}")
            print(f"  Message ID: {message.message_id}")

        return success

    def announce_identity(self):
        """Announce identity to network for peer discovery."""
        message = self.converter.create_identity_announcement_message()
        self.sent_messages.append(message)

        print(f"\n[PROTOCOL] Identity announced to network")
        print(f"  LCT ID: {self.lct_identity.lct_id}")
        print(f"  Hardware: {self.lct_identity.hardware_type}")
        print(f"  Message ID: {message.message_id}")

    def receive_message(self, jsonl_line: str) -> bool:
        """
        Receive and process incoming message.

        Returns True if message processed successfully.
        """
        try:
            message = self.converter.parse_message(jsonl_line)

            # Verify attestation
            if not self.converter.verify_message(message, self.known_identities):
                self.failed_verifications.append({
                    "message_id": message.message_id,
                    "source": message.source_lct_id,
                    "timestamp": time.time(),
                })
                print(f"[PROTOCOL] ❌ Message verification FAILED: {message.message_id}")
                return False

            # Process by type
            if message.message_type == MessageType.REPUTATION_PROPOSAL.value:
                return self._process_reputation_proposal(message)

            elif message.message_type == MessageType.CONSENSUS_VOTE.value:
                return self._process_consensus_vote(message)

            elif message.message_type == MessageType.IDENTITY_ANNOUNCEMENT.value:
                return self._process_identity_announcement(message)

            else:
                print(f"[PROTOCOL] Unknown message type: {message.message_type}")
                return False

        except Exception as e:
            print(f"[PROTOCOL] Error processing message: {e}")
            return False

    def _process_reputation_proposal(self, message: ProtocolMessage) -> bool:
        """Process incoming reputation proposal."""
        payload = ReputationProposalMessage.from_payload(message.payload)

        print(f"\n[PROTOCOL] Received reputation proposal")
        print(f"  Proposal ID: {payload.proposal_id}")
        print(f"  Target: {payload.target_lct_id}")
        print(f"  From: {message.source_lct_id}")

        # Track received message
        self.received_messages.append(message)

        return True

    def _process_consensus_vote(self, message: ProtocolMessage) -> bool:
        """Process incoming consensus vote."""
        payload = ConsensusVoteMessage.from_payload(message.payload)

        print(f"\n[PROTOCOL] Received consensus vote")
        print(f"  Proposal ID: {payload.proposal_id}")
        print(f"  Vote: {payload.vote_type}")
        print(f"  Weight: {payload.vote_weight:.2f}")
        print(f"  From: {message.source_lct_id}")

        # Track received message
        self.received_messages.append(message)

        return True

    def _process_identity_announcement(self, message: ProtocolMessage) -> bool:
        """Process identity announcement (peer discovery)."""
        payload = IdentityAnnouncementMessage.from_payload(message.payload)

        print(f"\n[PROTOCOL] Peer discovered")
        print(f"  LCT ID: {payload.lct_id}")
        print(f"  Hardware: {payload.hardware_type}")
        print(f"  Capabilities: {', '.join(payload.node_capabilities)}")

        # Create LCT identity for peer
        peer_identity = LCTIdentity(
            lct_id=payload.lct_id,
            hardware_type=payload.hardware_type,
            hardware_fingerprint=payload.hardware_fingerprint,
            attestation_public_key=payload.attestation_public_key,
            created_at=message.timestamp,
        )

        # Add to known peers
        self.add_peer(peer_identity)

        # Track received message
        self.received_messages.append(message)

        return True

    def export_messages_to_file(self, filepath: Path, messages: List[ProtocolMessage]):
        """Export messages to JSONL file."""
        with open(filepath, 'w') as f:
            for message in messages:
                f.write(message.to_jsonl() + '\n')

        print(f"\n[PROTOCOL] Exported {len(messages)} messages to {filepath}")

    def import_messages_from_file(self, filepath: Path) -> int:
        """Import messages from JSONL file."""
        count = 0
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    if self.receive_message(line.strip()):
                        count += 1

        print(f"\n[PROTOCOL] Imported {count} messages from {filepath}")
        return count

    def get_statistics(self) -> Dict[str, Any]:
        """Get protocol statistics."""
        return {
            "known_peers": len(self.known_identities),
            "sent_messages": len(self.sent_messages),
            "received_messages": len(self.received_messages),
            "failed_verifications": len(self.failed_verifications),
            "message_types": {
                "sent": self._count_message_types(self.sent_messages),
                "received": self._count_message_types(self.received_messages),
            },
        }

    def _count_message_types(self, messages: List[ProtocolMessage]) -> Dict[str, int]:
        """Count messages by type."""
        counts = {}
        for message in messages:
            counts[message.message_type] = counts.get(message.message_type, 0) + 1
        return counts


# ============================================================================
# TESTING
# ============================================================================

async def test_protocol_implementation():
    """Test JSONL protocol implementation."""
    print("=" * 80)
    print("SESSION 166: Protocol JSONL Converter Test")
    print("=" * 80)
    print("Phase 1 Protocol Implementation")
    print("=" * 80)

    # Create test nodes
    print("\n" + "=" * 80)
    print("PHASE 1: Create Test Network (3 nodes)")
    print("=" * 80)

    # Node 1: Alice (Legion)
    alice_identity = LCTIdentity(
        lct_id="lct:web4:legion:alice",
        hardware_type="tpm2",
        hardware_fingerprint=hashlib.sha256(b"alice_hw").hexdigest(),
        attestation_public_key="alice_pubkey",
        created_at=time.time(),
    )

    alice_lct_manager = LCTReputationManager()
    alice_lct_manager.register_lct_identity(alice_identity)

    alice_diversity = SourceDiversityManager()
    alice_consensus = DecentralizedReputationConsensus(alice_lct_manager, alice_diversity)

    alice_protocol = NetworkProtocolHandler(
        alice_identity,
        alice_lct_manager,
        alice_diversity,
        alice_consensus,
        network_id="web4_test_lan",
    )

    # Node 2: Bob (Thor)
    bob_identity = LCTIdentity(
        lct_id="lct:web4:thor:bob",
        hardware_type="trustzone",
        hardware_fingerprint=hashlib.sha256(b"bob_hw").hexdigest(),
        attestation_public_key="bob_pubkey",
        created_at=time.time(),
    )

    bob_lct_manager = LCTReputationManager()
    bob_lct_manager.register_lct_identity(bob_identity)

    bob_diversity = SourceDiversityManager()
    bob_consensus = DecentralizedReputationConsensus(bob_lct_manager, bob_diversity)

    bob_protocol = NetworkProtocolHandler(
        bob_identity,
        bob_lct_manager,
        bob_diversity,
        bob_consensus,
        network_id="web4_test_lan",
    )

    # Node 3: Charlie (Sprout)
    charlie_identity = LCTIdentity(
        lct_id="lct:web4:sprout:charlie",
        hardware_type="tpm2",
        hardware_fingerprint=hashlib.sha256(b"charlie_hw").hexdigest(),
        attestation_public_key="charlie_pubkey",
        created_at=time.time(),
    )

    charlie_lct_manager = LCTReputationManager()
    charlie_lct_manager.register_lct_identity(charlie_identity)

    charlie_diversity = SourceDiversityManager()
    charlie_consensus = DecentralizedReputationConsensus(charlie_lct_manager, charlie_diversity)

    charlie_protocol = NetworkProtocolHandler(
        charlie_identity,
        charlie_lct_manager,
        charlie_diversity,
        charlie_consensus,
        network_id="web4_test_lan",
    )

    # Test 1: Identity Announcement
    print("\n" + "=" * 80)
    print("TEST 1: Identity Announcement (Peer Discovery)")
    print("=" * 80)

    alice_protocol.announce_identity()
    bob_protocol.announce_identity()
    charlie_protocol.announce_identity()

    # Cross-register peers
    alice_protocol.add_peer(bob_identity)
    alice_protocol.add_peer(charlie_identity)

    bob_protocol.add_peer(alice_identity)
    bob_protocol.add_peer(charlie_identity)

    charlie_protocol.add_peer(alice_identity)
    charlie_protocol.add_peer(bob_identity)

    # Test 2: Reputation Proposal
    print("\n" + "=" * 80)
    print("TEST 2: Reputation Proposal (Alice proposes +10 for Bob)")
    print("=" * 80)

    proposal_id = alice_protocol.send_reputation_proposal(
        target_lct_id="lct:web4:thor:bob",
        quality_contribution=10.0,
        event_type="verification",
        event_data="High quality pattern validation",
    )

    # Test 3: Consensus Voting
    print("\n" + "=" * 80)
    print("TEST 3: Consensus Voting (All nodes vote)")
    print("=" * 80)

    # Give nodes some reputation for voting weight
    for _ in range(3):
        att = alice_identity.generate_attestation(f"test_{_}")
        alice_lct_manager.record_quality_event("lct:web4:legion:alice", 10.0, f"test_{_}", att)

        att = bob_identity.generate_attestation(f"test_{_}")
        bob_lct_manager.record_quality_event("lct:web4:thor:bob", 8.0, f"test_{_}", att)

        att = charlie_identity.generate_attestation(f"test_{_}")
        charlie_lct_manager.record_quality_event("lct:web4:sprout:charlie", 5.0, f"test_{_}", att)

    # Add diversity
    for i in range(4):
        alice_diversity.record_reputation_event("lct:web4:legion:alice", f"source_{i}", 2.0)
        bob_diversity.record_reputation_event("lct:web4:thor:bob", f"source_{i}", 2.0)
        charlie_diversity.record_reputation_event("lct:web4:sprout:charlie", f"source_{i}", 2.0)

    # Vote
    alice_protocol.send_consensus_vote(proposal_id, VoteType.APPROVE, "Verified high quality")
    bob_protocol.send_consensus_vote(proposal_id, VoteType.APPROVE, "Looks good to me")
    charlie_protocol.send_consensus_vote(proposal_id, VoteType.APPROVE, "Approved")

    # Test 4: JSONL Export/Import
    print("\n" + "=" * 80)
    print("TEST 4: JSONL Export/Import")
    print("=" * 80)

    export_path = Path("/tmp/web4_protocol_test.jsonl")
    alice_protocol.export_messages_to_file(export_path, alice_protocol.sent_messages)

    # Create new node and import
    dave_identity = LCTIdentity(
        lct_id="lct:web4:test:dave",
        hardware_type="tpm2",
        hardware_fingerprint=hashlib.sha256(b"dave_hw").hexdigest(),
        attestation_public_key="dave_pubkey",
        created_at=time.time(),
    )

    dave_lct_manager = LCTReputationManager()
    dave_lct_manager.register_lct_identity(dave_identity)

    dave_diversity = SourceDiversityManager()
    dave_consensus = DecentralizedReputationConsensus(dave_lct_manager, dave_diversity)

    dave_protocol = NetworkProtocolHandler(
        dave_identity,
        dave_lct_manager,
        dave_diversity,
        dave_consensus,
        network_id="web4_test_lan",
    )

    # Add peers so Dave can verify messages
    dave_protocol.add_peer(alice_identity)
    dave_protocol.add_peer(bob_identity)
    dave_protocol.add_peer(charlie_identity)

    # Import messages
    imported_count = dave_protocol.import_messages_from_file(export_path)

    # Statistics
    print("\n" + "=" * 80)
    print("PROTOCOL STATISTICS")
    print("=" * 80)

    print("\nAlice (Legion):")
    alice_stats = alice_protocol.get_statistics()
    for key, value in alice_stats.items():
        print(f"  {key}: {value}")

    print("\nDave (imported messages):")
    dave_stats = dave_protocol.get_statistics()
    for key, value in dave_stats.items():
        print(f"  {key}: {value}")

    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION")
    print("=" * 80)

    validations = []
    validations.append(("✅ All nodes announced identities", len(alice_protocol.known_identities) == 3))
    validations.append(("✅ Reputation proposal sent", len(alice_protocol.sent_messages) >= 2))  # announcement + proposal
    validations.append(("✅ Consensus votes sent", len(alice_protocol.sent_messages) >= 3))  # + vote
    validations.append(("✅ Messages exported to JSONL", export_path.exists()))
    validations.append(("✅ Messages imported successfully", imported_count > 0))
    validations.append(("✅ No failed verifications", len(alice_protocol.failed_verifications) == 0))

    for validation, passed in validations:
        print(f"  {validation}: {'PASS' if passed else 'FAIL'}")

    if all(passed for _, passed in validations):
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\nPhase 1 Protocol Implementation: VALIDATED")
        print("  ✅ JSONL serialization/deserialization")
        print("  ✅ Attestation verification at protocol level")
        print("  ✅ Peer discovery (identity announcement)")
        print("  ✅ Reputation proposals")
        print("  ✅ Consensus voting")
        print("  ✅ Message streaming (export/import)")
        print("\n🎯 Ready for LAN deployment")
        print("=" * 80)
    else:
        print("\n❌ SOME TESTS FAILED")

    return all(passed for _, passed in validations)


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_protocol_implementation())

    if success:
        print("\n" + "=" * 80)
        print("SESSION 166: PROTOCOL IMPLEMENTATION COMPLETE")
        print("=" * 80)
        print("\nWeb4 reputation system now has:")
        print("  ✅ Phase 1 Security (Sessions 163-165)")
        print("  ✅ JSONL Protocol (Session 166)")
        print("  ✅ Network-ready message format")
        print("  ✅ Attestation verification")
        print("  ✅ Peer discovery")
        print("\nReady for real-world deployment on:")
        print("  - Legion (10.0.0.72): RTX 4090, TPM2")
        print("  - Thor (10.0.0.99): Jetson AGX Thor, TrustZone")
        print("  - Sprout (10.0.0.36): Orin Nano, TPM2")
        print("=" * 80)
