"""
View Change Protocol for FB-PBFT Consensus

Implements view change mechanism for Byzantine fault tolerance when primary
proposer fails or becomes unresponsive.

Author: Legion Autonomous Session #46
Date: 2025-12-01
Status: Research prototype - view change protocol
Integration: Built on Session #43 consensus protocol

References:
- PBFT: "Practical Byzantine Fault Tolerance" (Castro & Liskov, 1999)
- Session #43: FB-PBFT consensus protocol
- Session #45: Fault injection testing (identified view change gap)

View Change Flow:
1. Replica detects primary timeout (no PRE-PREPARE received)
2. Replica broadcasts VIEW-CHANGE message to all platforms
3. When new primary collects 2f+1 VIEW-CHANGE messages:
   - New primary broadcasts NEW-VIEW message
   - Includes proof of 2f+1 VIEW-CHANGE messages
   - Resumes consensus in new view with new proposer
4. Replicas validate NEW-VIEW and resume consensus

Timeout Detection:
- Primary timeout: No PRE-PREPARE received within timeout period
- PREPARE timeout: No PREPARE quorum within timeout period
- COMMIT timeout: No COMMIT quorum within timeout period

Proposer Selection:
- Round-robin by sorted platform names
- New proposer = platforms[(view + 1) % N]
"""

import time
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum


class ViewChangePhase(Enum):
    """View change protocol phases"""
    NORMAL = "NORMAL"  # Normal consensus operation
    VIEW_CHANGE = "VIEW_CHANGE"  # View change in progress
    NEW_VIEW = "NEW_VIEW"  # New view established


@dataclass
class ViewChangeMessage:
    """
    VIEW-CHANGE message broadcast by replica when primary timeout detected.

    Contains:
    - view: Current view number
    - new_view: Proposed new view number (view + 1)
    - sequence: Last committed sequence number
    - prepared: Prepared messages (PRE-PREPARE + 2f PREPAREs) for uncommitted sequences
    - platform: Platform sending VIEW-CHANGE
    - signature: Ed25519 signature
    - timestamp: Message creation time
    """

    view: int = 0  # Current view
    new_view: int = 0  # Proposed new view (view + 1)
    sequence: int = 0  # Last committed sequence
    prepared: List[Dict[str, Any]] = field(default_factory=list)  # Prepared certificates
    platform: str = ""  # Platform sending VIEW-CHANGE
    signature: str = ""  # Ed25519 signature
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": "VIEW-CHANGE",
            "view": self.view,
            "new_view": self.new_view,
            "sequence": self.sequence,
            "prepared": self.prepared,
            "platform": self.platform,
            "signature": self.signature,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to sign (excludes signature)"""
        data = {
            "type": "VIEW-CHANGE",
            "view": self.view,
            "new_view": self.new_view,
            "sequence": self.sequence,
            "prepared": self.prepared,
            "platform": self.platform,
            "timestamp": self.timestamp
        }
        return json.dumps(data, sort_keys=True)

    def hash(self) -> str:
        """Compute message hash"""
        return hashlib.sha256(self.signable_content().encode()).hexdigest()


@dataclass
class NewViewMessage:
    """
    NEW-VIEW message broadcast by new primary when 2f+1 VIEW-CHANGE messages received.

    Contains:
    - new_view: New view number
    - view_change_messages: 2f+1 VIEW-CHANGE messages as proof
    - pre_prepare: New PRE-PREPARE message for first sequence in new view
    - platform: New primary platform
    - signature: Ed25519 signature
    - timestamp: Message creation time
    """

    new_view: int = 0  # New view number
    view_change_messages: List[Dict[str, Any]] = field(default_factory=list)  # 2f+1 proofs
    pre_prepare: Optional[Dict[str, Any]] = None  # First PRE-PREPARE in new view
    platform: str = ""  # New primary
    signature: str = ""  # Ed25519 signature
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": "NEW-VIEW",
            "new_view": self.new_view,
            "view_change_messages": self.view_change_messages,
            "pre_prepare": self.pre_prepare,
            "platform": self.platform,
            "signature": self.signature,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to sign (excludes signature)"""
        data = {
            "type": "NEW-VIEW",
            "new_view": self.new_view,
            "view_change_messages": self.view_change_messages,
            "pre_prepare": self.pre_prepare,
            "platform": self.platform,
            "timestamp": self.timestamp
        }
        return json.dumps(data, sort_keys=True)

    def hash(self) -> str:
        """Compute message hash"""
        return hashlib.sha256(self.signable_content().encode()).hexdigest()


class ViewChangeManager:
    """
    Manages view change protocol for consensus engine.

    Handles:
    - Timeout detection (primary, PREPARE, COMMIT)
    - VIEW-CHANGE message broadcasting
    - NEW-VIEW message validation
    - View transition
    """

    def __init__(
        self,
        platform_name: str,
        platforms: List[str],
        signing_func,
        verification_func,
        on_send_message=None
    ):
        """
        Initialize view change manager.

        Args:
            platform_name: This platform's name
            platforms: All platforms in consensus group (sorted)
            signing_func: Function to sign messages
            verification_func: Function to verify signatures
            on_send_message: Callback to send messages
        """
        self.platform_name = platform_name
        self.platforms = sorted(platforms)
        self.sign = signing_func
        self.verify = verification_func
        self.on_send_message = on_send_message

        # Fault tolerance parameters
        self.N = len(self.platforms)
        self.f = (self.N - 1) // 3  # Max Byzantine faults
        self.quorum_size = 2 * self.f + 1  # 2f+1 for quorum

        # View change state
        self.phase = ViewChangePhase.NORMAL
        self.current_view = 0

        # Timeout configuration (seconds)
        self.primary_timeout = 30.0  # Timeout for PRE-PREPARE
        self.prepare_timeout = 10.0  # Timeout for PREPARE quorum
        self.commit_timeout = 10.0  # Timeout for COMMIT quorum

        # Timeout tracking
        self.last_pre_prepare_time: Optional[float] = None
        self.last_prepare_time: Optional[float] = None
        self.last_commit_time: Optional[float] = None

        # VIEW-CHANGE messages received (view -> platform -> message)
        self.view_change_messages: Dict[int, Dict[str, ViewChangeMessage]] = {}

        # NEW-VIEW messages received (view -> message)
        self.new_view_messages: Dict[int, NewViewMessage] = {}

        # Statistics
        self.view_changes_triggered = 0
        self.view_changes_completed = 0
        self.total_timeout_detections = 0

    def get_proposer_for_view(self, view: int) -> str:
        """Get proposer platform for given view"""
        return self.platforms[view % self.N]

    def is_proposer(self, view: int) -> bool:
        """Check if this platform is proposer for given view"""
        return self.get_proposer_for_view(view) == self.platform_name

    def check_timeout(self, sequence: int) -> bool:
        """
        Check if timeout occurred for current sequence.

        Returns True if timeout detected and view change triggered.
        """
        now = time.time()

        # Check primary timeout (no PRE-PREPARE received)
        if self.last_pre_prepare_time is None:
            # No PRE-PREPARE received yet, check if timeout elapsed
            if self.phase == ViewChangePhase.NORMAL:
                # Start timer on first check
                if not hasattr(self, 'first_timeout_check'):
                    self.first_timeout_check = now
                    return False

                elapsed = now - self.first_timeout_check
                if elapsed > self.primary_timeout:
                    self.total_timeout_detections += 1
                    return self._trigger_view_change(
                        sequence,
                        reason="PRIMARY_TIMEOUT"
                    )

        # Check PREPARE timeout (no PREPARE quorum)
        if self.last_prepare_time is not None:
            elapsed = now - self.last_prepare_time
            if elapsed > self.prepare_timeout:
                self.total_timeout_detections += 1
                return self._trigger_view_change(
                    sequence,
                    reason="PREPARE_TIMEOUT"
                )

        # Check COMMIT timeout (no COMMIT quorum)
        if self.last_commit_time is not None:
            elapsed = now - self.last_commit_time
            if elapsed > self.commit_timeout:
                self.total_timeout_detections += 1
                return self._trigger_view_change(
                    sequence,
                    reason="COMMIT_TIMEOUT"
                )

        return False

    def _trigger_view_change(self, sequence: int, reason: str) -> bool:
        """
        Trigger view change protocol.

        Broadcasts VIEW-CHANGE message to all platforms.
        """
        if self.phase != ViewChangePhase.NORMAL:
            return False  # Already in view change

        self.phase = ViewChangePhase.VIEW_CHANGE
        self.view_changes_triggered += 1

        # Create VIEW-CHANGE message
        msg = ViewChangeMessage(
            view=self.current_view,
            new_view=self.current_view + 1,
            sequence=sequence,
            prepared=[],  # TODO: Include prepared certificates
            platform=self.platform_name,
            timestamp=time.time()
        )

        # Sign message
        msg.signature = self.sign(msg.signable_content())

        print(f"[{self.platform_name}] VIEW-CHANGE triggered")
        print(f"  Reason: {reason}")
        print(f"  Current view: {self.current_view}")
        print(f"  New view: {msg.new_view}")
        print(f"  Sequence: {sequence}")

        # Broadcast to all platforms
        if self.on_send_message:
            for platform in self.platforms:
                self.on_send_message(platform, msg.to_dict())

        # Record own VIEW-CHANGE message
        self.handle_view_change(msg)

        return True

    def handle_view_change(self, msg: ViewChangeMessage) -> None:
        """
        Handle incoming VIEW-CHANGE message.

        Collects 2f+1 VIEW-CHANGE messages. When quorum reached:
        - If this platform is new primary → broadcast NEW-VIEW
        - If not new primary → wait for NEW-VIEW
        """
        new_view = msg.new_view

        # Initialize storage for this view
        if new_view not in self.view_change_messages:
            self.view_change_messages[new_view] = {}

        # Verify signature
        if not self.verify(msg.signable_content(), msg.signature, msg.platform):
            print(f"[{self.platform_name}] VIEW-CHANGE signature invalid from {msg.platform}")
            return

        # Store VIEW-CHANGE message
        self.view_change_messages[new_view][msg.platform] = msg

        # Check if quorum reached
        count = len(self.view_change_messages[new_view])
        if count >= self.quorum_size:
            print(f"[{self.platform_name}] VIEW-CHANGE quorum reached ({count}/{self.quorum_size})")

            # Check if this platform is new primary
            new_proposer = self.get_proposer_for_view(new_view)
            if new_proposer == self.platform_name:
                self._broadcast_new_view(new_view)

    def _broadcast_new_view(self, new_view: int) -> None:
        """
        Broadcast NEW-VIEW message as new primary.

        Includes 2f+1 VIEW-CHANGE messages as proof.
        """
        # Collect 2f+1 VIEW-CHANGE messages
        view_change_msgs = list(self.view_change_messages[new_view].values())
        proof_messages = [msg.to_dict() for msg in view_change_msgs[:self.quorum_size]]

        # Create NEW-VIEW message
        msg = NewViewMessage(
            new_view=new_view,
            view_change_messages=proof_messages,
            pre_prepare=None,  # TODO: Include first PRE-PREPARE for new view
            platform=self.platform_name,
            timestamp=time.time()
        )

        # Sign message
        msg.signature = self.sign(msg.signable_content())

        print(f"[{self.platform_name}] Broadcasting NEW-VIEW")
        print(f"  New view: {new_view}")
        print(f"  Proof count: {len(proof_messages)}")

        # Broadcast to all platforms
        if self.on_send_message:
            for platform in self.platforms:
                self.on_send_message(platform, msg.to_dict())

        # Handle own NEW-VIEW message
        self.handle_new_view(msg)

    def handle_new_view(self, msg: NewViewMessage) -> None:
        """
        Handle incoming NEW-VIEW message.

        Validates:
        - Message is from new primary
        - Contains 2f+1 valid VIEW-CHANGE messages
        - VIEW-CHANGE messages are for correct new view

        If valid: Transition to new view and resume consensus.
        """
        new_view = msg.new_view

        # Verify new primary
        expected_proposer = self.get_proposer_for_view(new_view)
        if msg.platform != expected_proposer:
            print(f"[{self.platform_name}] NEW-VIEW from wrong platform: {msg.platform} (expected {expected_proposer})")
            return

        # Verify signature
        if not self.verify(msg.signable_content(), msg.signature, msg.platform):
            print(f"[{self.platform_name}] NEW-VIEW signature invalid")
            return

        # Verify VIEW-CHANGE messages
        view_change_count = len(msg.view_change_messages)
        if view_change_count < self.quorum_size:
            print(f"[{self.platform_name}] NEW-VIEW insufficient VIEW-CHANGE messages: {view_change_count} < {self.quorum_size}")
            return

        # TODO: Validate each VIEW-CHANGE message

        print(f"[{self.platform_name}] NEW-VIEW accepted")
        print(f"  New view: {new_view}")
        print(f"  New primary: {expected_proposer}")

        # Transition to new view
        self.current_view = new_view
        self.phase = ViewChangePhase.NORMAL
        self.view_changes_completed += 1

        # Reset timeouts
        self.last_pre_prepare_time = None
        self.last_prepare_time = None
        self.last_commit_time = None

        # Resume consensus
        print(f"[{self.platform_name}] Resumed consensus in view {new_view}")

    def update_pre_prepare_time(self) -> None:
        """Update timestamp when PRE-PREPARE received"""
        self.last_pre_prepare_time = time.time()

    def update_prepare_time(self) -> None:
        """Update timestamp when PREPARE quorum reached"""
        self.last_prepare_time = time.time()

    def update_commit_time(self) -> None:
        """Update timestamp when COMMIT quorum reached"""
        self.last_commit_time = time.time()

    def get_stats(self) -> Dict[str, Any]:
        """Get view change statistics"""
        return {
            "platform": self.platform_name,
            "current_view": self.current_view,
            "phase": self.phase.value,
            "view_changes_triggered": self.view_changes_triggered,
            "view_changes_completed": self.view_changes_completed,
            "total_timeout_detections": self.total_timeout_detections,
            "pending_view_changes": len(self.view_change_messages)
        }
