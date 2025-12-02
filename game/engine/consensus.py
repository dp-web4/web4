"""
Distributed Consensus Protocol for Web4 Societies

Federation-Based PBFT-Lite (FB-PBFT) implementation for Byzantine fault-tolerant
distributed consensus across multiple platforms.

Author: Legion Autonomous Session #43
Date: 2025-11-30
Status: Research prototype - tested at research scale
Integration: Built on Session #42 cross-platform verification infrastructure

References:
- DISTRIBUTED_CONSENSUS_PROTOCOL.md (design specification)
- Session #42: Cross-platform block verification (Ed25519)
- Phase 3 Federation Network: HTTP/REST infrastructure
"""

from __future__ import annotations

import time
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

# Import view change protocol (Session #46)
try:
    from game.engine.view_change import ViewChangeManager
    VIEW_CHANGE_AVAILABLE = True
except ImportError:
    VIEW_CHANGE_AVAILABLE = False


class MessageType(Enum):
    """Consensus message types"""
    PRE_PREPARE = "PRE-PREPARE"
    PREPARE = "PREPARE"
    COMMIT = "COMMIT"
    VIEW_CHANGE = "VIEW-CHANGE"


class ConsensusPhase(Enum):
    """Consensus state machine phases"""
    IDLE = "IDLE"
    PRE_PREPARED = "PRE-PREPARED"
    PREPARED = "PREPARED"
    COMMITTED = "COMMITTED"


@dataclass
class Block:
    """Blockchain block structure"""
    header: Dict[str, Any]
    transactions: List[Dict[str, Any]]
    timestamp: float
    proposer_platform: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for hashing/signing"""
        return {
            "header": self.header,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "proposer_platform": self.proposer_platform
        }

    def hash(self) -> str:
        """Compute SHA-256 hash of block"""
        block_json = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(block_json.encode()).hexdigest()


@dataclass
class PrePrepareMessage:
    """Phase 1: Block proposal from proposer"""
    type: str = "PRE-PREPARE"
    view: int = 0
    sequence: int = 0
    block: Optional[Block] = None
    proposer_platform: str = ""
    signature: str = ""  # Ed25519 signature
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for signing/transmission"""
        return {
            "type": self.type,
            "view": self.view,
            "sequence": self.sequence,
            "block": self.block.to_dict() if self.block else None,
            "proposer_platform": self.proposer_platform,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to be signed (excludes signature)"""
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass
class PrepareMessage:
    """Phase 2: Validation vote"""
    type: str = "PREPARE"
    view: int = 0
    sequence: int = 0
    block_hash: str = ""
    platform: str = ""
    signature: str = ""  # Ed25519 signature
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for signing/transmission"""
        return {
            "type": self.type,
            "view": self.view,
            "sequence": self.sequence,
            "block_hash": self.block_hash,
            "platform": self.platform,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to be signed (excludes signature)"""
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass
class CommitMessage:
    """Phase 3: Final commitment vote"""
    type: str = "COMMIT"
    view: int = 0
    sequence: int = 0
    block_hash: str = ""
    platform: str = ""
    signature: str = ""  # Ed25519 signature
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for signing/transmission"""
        return {
            "type": self.type,
            "view": self.view,
            "sequence": self.sequence,
            "block_hash": self.block_hash,
            "platform": self.platform,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to be signed (excludes signature)"""
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass
class ViewChangeMessage:
    """View change request (fault recovery)"""
    type: str = "VIEW-CHANGE"
    new_view: int = 0
    last_sequence: int = 0
    platform: str = ""
    signature: str = ""  # Ed25519 signature
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for signing/transmission"""
        return {
            "type": self.type,
            "new_view": self.new_view,
            "last_sequence": self.last_sequence,
            "platform": self.platform,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to be signed (excludes signature)"""
        return json.dumps(self.to_dict(), sort_keys=True)


@dataclass
class ConsensusState:
    """Consensus state for a single platform"""

    # Configuration
    platform_name: str = ""
    platforms: List[str] = field(default_factory=list)  # Consensus group members
    view: int = 0  # Current view number
    sequence: int = 0  # Next block sequence to commit

    # Byzantine fault tolerance configuration
    @property
    def f(self) -> int:
        """Maximum Byzantine faults tolerated"""
        # f < N/3, so f = floor((N-1)/3)
        return max(0, (len(self.platforms) - 1) // 3)

    @property
    def quorum_size(self) -> int:
        """Quorum size (2f+1)"""
        return 2 * self.f + 1

    # Current consensus phase
    phase: ConsensusPhase = ConsensusPhase.IDLE

    # Per-sequence state (cleared after commit)
    pre_prepare_received: Optional[PrePrepareMessage] = None
    prepare_votes: List[PrepareMessage] = field(default_factory=list)
    commit_votes: List[CommitMessage] = field(default_factory=list)

    # Committed blocks history
    committed_blocks: List[Block] = field(default_factory=list)

    # View change state
    view_change_votes: List[ViewChangeMessage] = field(default_factory=list)

    # Timeout configuration (seconds)
    timeout_seconds: float = 30.0
    last_progress_time: float = field(default_factory=time.time)

    def reset_sequence_state(self) -> None:
        """Reset state for new sequence (after commit or view change)"""
        self.pre_prepare_received = None
        self.prepare_votes = []
        self.commit_votes = []
        self.phase = ConsensusPhase.IDLE

    def has_prepare_quorum(self) -> bool:
        """Check if we have 2f+1 PREPARE votes"""
        return len(self.prepare_votes) >= self.quorum_size

    def has_commit_quorum(self) -> bool:
        """Check if we have 2f+1 COMMIT votes"""
        return len(self.commit_votes) >= self.quorum_size

    def has_view_change_quorum(self) -> bool:
        """Check if we have 2f+1 VIEW-CHANGE votes"""
        return len(self.view_change_votes) >= self.quorum_size

    def is_timeout(self) -> bool:
        """Check if consensus has timed out"""
        return (time.time() - self.last_progress_time) > self.timeout_seconds

    def update_progress_time(self) -> None:
        """Update last progress timestamp"""
        self.last_progress_time = time.time()


class ConsensusEngine:
    """
    Consensus engine implementing FB-PBFT protocol.

    Handles message validation, state transitions, and block commitment.
    """

    def __init__(
        self,
        platform_name: str,
        platforms: List[str],
        signing_func: Callable[[str], str],
        verification_func: Callable[[str, str, str], bool],
        enable_view_change: bool = True
    ):
        """
        Initialize consensus engine.

        Args:
            platform_name: This platform's name
            platforms: List of all platforms in consensus group
            signing_func: Function to sign content: (content: str) -> signature: str
            verification_func: Function to verify signature:
                               (content: str, signature: str, platform: str) -> bool
            enable_view_change: Enable view change protocol for fault recovery (default: True)
        """
        self.state = ConsensusState(
            platform_name=platform_name,
            platforms=sorted(platforms)  # Deterministic ordering
        )
        self.sign = signing_func
        self.verify = verification_func

        # Callbacks for external integration
        self.on_block_committed: Optional[Callable[[Block], None]] = None
        self.on_send_message: Optional[Callable[[str, Dict], None]] = None

        # View change protocol (Session #46 integration)
        self.view_change_manager: Optional[ViewChangeManager] = None
        if enable_view_change and VIEW_CHANGE_AVAILABLE:
            self.view_change_manager = ViewChangeManager(
                platform_name=platform_name,
                platforms=sorted(platforms),
                signing_func=signing_func,
                verification_func=verification_func,
                on_send_message=self._send_view_change_message
            )
            print(f"[{platform_name}] View change protocol enabled")
        elif enable_view_change and not VIEW_CHANGE_AVAILABLE:
            print(f"[{platform_name}] Warning: View change requested but not available")

    def _send_view_change_message(self, target: str, msg: Dict[str, Any]) -> None:
        """Send view change message (VIEW-CHANGE or NEW-VIEW)"""
        if self.on_send_message:
            self.on_send_message(target, msg)

    def get_proposer(self, sequence: int) -> str:
        """Get proposer for given sequence (deterministic round-robin)"""
        return self.state.platforms[sequence % len(self.state.platforms)]

    def is_proposer(self, sequence: int) -> bool:
        """Check if this platform is proposer for given sequence"""
        return self.get_proposer(sequence) == self.state.platform_name

    # -------------------------------------------------------------------------
    # Message Creation
    # -------------------------------------------------------------------------

    def create_pre_prepare(self, block: Block) -> PrePrepareMessage:
        """Create PRE-PREPARE message (proposer only)"""
        msg = PrePrepareMessage(
            view=self.state.view,
            sequence=self.state.sequence,
            block=block,
            proposer_platform=self.state.platform_name,
            timestamp=time.time()
        )
        msg.signature = self.sign(msg.signable_content())
        return msg

    def create_prepare(self, block_hash: str) -> PrepareMessage:
        """Create PREPARE message (all platforms)"""
        msg = PrepareMessage(
            view=self.state.view,
            sequence=self.state.sequence,
            block_hash=block_hash,
            platform=self.state.platform_name,
            timestamp=time.time()
        )
        msg.signature = self.sign(msg.signable_content())
        return msg

    def create_commit(self, block_hash: str) -> CommitMessage:
        """Create COMMIT message (all platforms)"""
        msg = CommitMessage(
            view=self.state.view,
            sequence=self.state.sequence,
            block_hash=block_hash,
            platform=self.state.platform_name,
            timestamp=time.time()
        )
        msg.signature = self.sign(msg.signable_content())
        return msg

    def create_view_change(self) -> ViewChangeMessage:
        """Create VIEW-CHANGE message (triggered by timeout)"""
        msg = ViewChangeMessage(
            new_view=self.state.view + 1,
            last_sequence=self.state.sequence,
            platform=self.state.platform_name,
            timestamp=time.time()
        )
        msg.signature = self.sign(msg.signable_content())
        return msg

    # -------------------------------------------------------------------------
    # Message Validation
    # -------------------------------------------------------------------------

    def validate_pre_prepare(self, msg: PrePrepareMessage) -> bool:
        """Validate PRE-PREPARE message"""
        # Check view and sequence
        if msg.view != self.state.view:
            return False
        if msg.sequence != self.state.sequence:
            return False

        # Check proposer is correct for this sequence
        expected_proposer = self.get_proposer(msg.sequence)
        if msg.proposer_platform != expected_proposer:
            return False

        # Verify signature
        if not self.verify(msg.signable_content(), msg.signature, msg.proposer_platform):
            return False

        # Block must exist
        if msg.block is None:
            return False

        return True

    def validate_prepare(self, msg: PrepareMessage) -> bool:
        """Validate PREPARE message"""
        # Check view and sequence
        if msg.view != self.state.view:
            return False
        if msg.sequence != self.state.sequence:
            return False

        # Check platform is in consensus group
        if msg.platform not in self.state.platforms:
            return False

        # Verify signature
        if not self.verify(msg.signable_content(), msg.signature, msg.platform):
            return False

        # Check block hash matches PRE-PREPARE
        if self.state.pre_prepare_received:
            expected_hash = self.state.pre_prepare_received.block.hash()
            if msg.block_hash != expected_hash:
                return False

        return True

    def validate_commit(self, msg: CommitMessage) -> bool:
        """Validate COMMIT message"""
        # Check view and sequence
        if msg.view != self.state.view:
            return False
        if msg.sequence != self.state.sequence:
            return False

        # Check platform is in consensus group
        if msg.platform not in self.state.platforms:
            return False

        # Verify signature
        if not self.verify(msg.signable_content(), msg.signature, msg.platform):
            return False

        # Check block hash matches PRE-PREPARE
        if self.state.pre_prepare_received:
            expected_hash = self.state.pre_prepare_received.block.hash()
            if msg.block_hash != expected_hash:
                return False

        return True

    def validate_view_change(self, msg: ViewChangeMessage) -> bool:
        """Validate VIEW-CHANGE message"""
        # Check new view is greater than current
        if msg.new_view <= self.state.view:
            return False

        # Check platform is in consensus group
        if msg.platform not in self.state.platforms:
            return False

        # Verify signature
        if not self.verify(msg.signable_content(), msg.signature, msg.platform):
            return False

        return True

    # -------------------------------------------------------------------------
    # Message Handling (State Machine)
    # -------------------------------------------------------------------------

    def handle_pre_prepare(self, msg: PrePrepareMessage) -> None:
        """
        Handle PRE-PREPARE message.

        Phase transition: IDLE → PRE-PREPARED
        Action: Validate, store, send PREPARE
        """
        if not self.validate_pre_prepare(msg):
            return

        # Update view change manager (PRE-PREPARE received)
        if self.view_change_manager:
            self.view_change_manager.update_pre_prepare_time()

        # Store PRE-PREPARE
        self.state.pre_prepare_received = msg
        self.state.phase = ConsensusPhase.PRE_PREPARED
        self.state.update_progress_time()

        # Create and broadcast PREPARE message
        prepare_msg = self.create_prepare(msg.block.hash())
        self._broadcast_message(prepare_msg)

        # Add our own PREPARE vote
        self.handle_prepare(prepare_msg)

    def handle_prepare(self, msg: PrepareMessage) -> None:
        """
        Handle PREPARE message.

        Phase transition: PRE-PREPARED → PREPARED (when quorum reached)
        Action: Collect votes, send COMMIT when quorum reached
        """
        if not self.validate_prepare(msg):
            return

        # Check for duplicate vote from same platform
        for vote in self.state.prepare_votes:
            if vote.platform == msg.platform:
                return  # Ignore duplicate

        # Add vote
        self.state.prepare_votes.append(msg)
        self.state.update_progress_time()

        # Check for quorum
        if self.state.has_prepare_quorum() and self.state.phase == ConsensusPhase.PRE_PREPARED:
            self.state.phase = ConsensusPhase.PREPARED

            # Create and broadcast COMMIT message
            block_hash = self.state.pre_prepare_received.block.hash()
            commit_msg = self.create_commit(block_hash)
            self._broadcast_message(commit_msg)

            # Add our own COMMIT vote
            self.handle_commit(commit_msg)

    def handle_commit(self, msg: CommitMessage) -> None:
        """
        Handle COMMIT message.

        Phase transition: PREPARED → COMMITTED (when quorum reached)
        Action: Collect votes, execute block when quorum reached
        """
        if not self.validate_commit(msg):
            return

        # Check for duplicate vote from same platform
        for vote in self.state.commit_votes:
            if vote.platform == msg.platform:
                return  # Ignore duplicate

        # Add vote
        self.state.commit_votes.append(msg)
        self.state.update_progress_time()

        # Check for quorum
        if self.state.has_commit_quorum() and self.state.phase == ConsensusPhase.PREPARED:
            self.state.phase = ConsensusPhase.COMMITTED

            # Execute block (add to committed blocks)
            block = self.state.pre_prepare_received.block
            self.state.committed_blocks.append(block)

            # Callback for external integration
            if self.on_block_committed:
                self.on_block_committed(block)

            # Advance to next sequence
            self.state.sequence += 1
            self.state.reset_sequence_state()

    def handle_view_change(self, msg: ViewChangeMessage) -> None:
        """
        Handle VIEW-CHANGE message.

        Action: Collect votes, trigger view change when quorum reached
        """
        if not self.validate_view_change(msg):
            return

        # Check for duplicate vote from same platform
        for vote in self.state.view_change_votes:
            if vote.platform == msg.platform:
                return  # Ignore duplicate

        # Add vote
        self.state.view_change_votes.append(msg)

        # Check for quorum
        if self.state.has_view_change_quorum():
            self._execute_view_change(msg.new_view)

    def _execute_view_change(self, new_view: int) -> None:
        """Execute view change (internal)"""
        self.state.view = new_view
        self.state.view_change_votes = []
        self.state.reset_sequence_state()
        self.state.update_progress_time()

    def _broadcast_message(self, msg: Any) -> None:
        """Broadcast message to all platforms (uses callback)"""
        if self.on_send_message:
            for platform in self.state.platforms:
                if platform != self.state.platform_name:
                    self.on_send_message(platform, msg.to_dict())

    # -------------------------------------------------------------------------
    # Proposer Actions
    # -------------------------------------------------------------------------

    def propose_block(self, block: Block) -> None:
        """
        Propose a new block (proposer only).

        Creates PRE-PREPARE message and broadcasts to all platforms.
        """
        if not self.is_proposer(self.state.sequence):
            raise ValueError(f"{self.state.platform_name} is not proposer for sequence {self.state.sequence}")

        if self.state.phase != ConsensusPhase.IDLE:
            raise ValueError(f"Cannot propose in phase {self.state.phase}")

        # Create and broadcast PRE-PREPARE
        msg = self.create_pre_prepare(block)
        self._broadcast_message(msg)

        # Handle our own PRE-PREPARE (start consensus)
        self.handle_pre_prepare(msg)

    # -------------------------------------------------------------------------
    # Timeout Handling & View Change Integration (Session #47)
    # -------------------------------------------------------------------------

    def check_timeout(self) -> bool:
        """
        Check for timeout and trigger view change if needed.

        Returns True if view change triggered, False otherwise.

        Integration with ViewChangeManager (Session #46):
        - Delegates timeout detection to ViewChangeManager
        - ViewChangeManager handles VIEW-CHANGE broadcast
        - Returns True when view change initiated
        """
        if self.view_change_manager:
            # Use view change manager's timeout detection
            return self.view_change_manager.check_timeout(self.state.sequence)
        else:
            # Fallback: basic timeout check (no view change)
            if self.state.is_timeout() and self.state.phase != ConsensusPhase.IDLE:
                print(f"[{self.state.platform_name}] Timeout detected but view change disabled")
                return True
            return False

    def handle_view_change_message(self, msg: Dict[str, Any]) -> None:
        """
        Handle VIEW-CHANGE or NEW-VIEW message.

        Delegates to ViewChangeManager if available.
        """
        if not self.view_change_manager:
            return

        msg_type = msg.get("type")

        if msg_type == "VIEW-CHANGE":
            from game.engine.view_change import ViewChangeMessage
            view_change_msg = ViewChangeMessage(
                view=msg["view"],
                new_view=msg["new_view"],
                sequence=msg["sequence"],
                prepared=msg.get("prepared", []),
                platform=msg["platform"],
                signature=msg.get("signature", ""),
                timestamp=msg["timestamp"]
            )
            self.view_change_manager.handle_view_change(view_change_msg)

        elif msg_type == "NEW-VIEW":
            from game.engine.view_change import NewViewMessage
            new_view_msg = NewViewMessage(
                new_view=msg["new_view"],
                view_change_messages=msg.get("view_change_messages", []),
                pre_prepare=msg.get("pre_prepare"),
                platform=msg["platform"],
                signature=msg.get("signature", ""),
                timestamp=msg["timestamp"]
            )
            self.view_change_manager.handle_new_view(new_view_msg)

    # -------------------------------------------------------------------------
    # Status Queries
    # -------------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """Get current consensus status (for debugging/monitoring)"""
        return {
            "platform": self.state.platform_name,
            "view": self.state.view,
            "sequence": self.state.sequence,
            "phase": self.state.phase.value,
            "f": self.state.f,
            "quorum_size": self.state.quorum_size,
            "committed_blocks": len(self.state.committed_blocks),
            "prepare_votes": len(self.state.prepare_votes),
            "commit_votes": len(self.state.commit_votes),
            "proposer": self.get_proposer(self.state.sequence)
        }
