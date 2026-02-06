"""
ATP Transactions for Consensus Integration

Defines transaction types for ATP transfers that can be embedded in consensus blocks.
Enables atomic cross-platform ATP transfers via distributed consensus.

Author: Legion Autonomous Session #44
Date: 2025-12-01
Status: Research prototype - tested at research scale
Integration: Built on Session #43 consensus + ATP ledger

References:
- CROSS_PLATFORM_ATP_PROTOCOL.md (protocol design)
- engine/consensus.py (consensus protocol)
- engine/atp_ledger.py (ATP state management)
"""

from __future__ import annotations

import time
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum


class ATPTransactionType(Enum):
    """ATP transaction types for consensus"""
    TRANSFER_LOCK = "ATP_TRANSFER_LOCK"  # Phase 1: Lock ATP at source
    TRANSFER_COMMIT = "ATP_TRANSFER_COMMIT"  # Phase 2: Credit at destination
    TRANSFER_ROLLBACK = "ATP_TRANSFER_ROLLBACK"  # Failure: Unlock at source
    BALANCE_SET = "ATP_BALANCE_SET"  # Initialize/set balance (for testing)


@dataclass
class ATPTransferLockTransaction:
    """
    Phase 1: Lock ATP at source platform

    This transaction locks ATP at the source platform for a pending transfer.
    Must reach consensus before destination can credit.
    """

    type: str = "ATP_TRANSFER_LOCK"
    transfer_id: str = ""  # Unique transfer ID
    source_platform: str = ""  # Platform where ATP is locked
    source_agent: str = ""  # Agent sending ATP (LCT)
    dest_platform: str = ""  # Platform where ATP will be credited
    dest_agent: str = ""  # Agent receiving ATP (LCT)
    amount: float = 0.0  # ATP amount to transfer
    timestamp: float = field(default_factory=time.time)
    signature: str = ""  # Ed25519 signature by source platform

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "transfer_id": self.transfer_id,
            "source_platform": self.source_platform,
            "source_agent": self.source_agent,
            "dest_platform": self.dest_platform,
            "dest_agent": self.dest_agent,
            "amount": self.amount,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to sign (excludes signature)"""
        return json.dumps(self.to_dict(), sort_keys=True)

    def hash(self) -> str:
        """Compute transaction hash"""
        return hashlib.sha256(self.signable_content().encode()).hexdigest()


@dataclass
class ATPTransferCommitTransaction:
    """
    Phase 2: Credit ATP at destination platform

    This transaction credits ATP at the destination platform after LOCK has reached consensus.
    References the original LOCK transaction by transfer_id.
    """

    type: str = "ATP_TRANSFER_COMMIT"
    transfer_id: str = ""  # Must match original LOCK transaction
    dest_platform: str = ""  # Platform where ATP is credited
    dest_agent: str = ""  # Agent receiving ATP (LCT)
    amount: float = 0.0  # ATP amount (must match LOCK)
    timestamp: float = field(default_factory=time.time)
    signature: str = ""  # Ed25519 signature by dest platform

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "transfer_id": self.transfer_id,
            "dest_platform": self.dest_platform,
            "dest_agent": self.dest_agent,
            "amount": self.amount,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to sign (excludes signature)"""
        return json.dumps(self.to_dict(), sort_keys=True)

    def hash(self) -> str:
        """Compute transaction hash"""
        return hashlib.sha256(self.signable_content().encode()).hexdigest()


@dataclass
class ATPTransferRollbackTransaction:
    """
    Rollback: Unlock ATP at source platform

    This transaction rolls back a LOCK when the transfer cannot complete
    (e.g., destination unreachable, timeout, validation failure).
    """

    type: str = "ATP_TRANSFER_ROLLBACK"
    transfer_id: str = ""  # Must match original LOCK transaction
    source_platform: str = ""  # Platform where ATP will be unlocked
    reason: str = ""  # Reason for rollback (e.g., "COMMIT_TIMEOUT")
    timestamp: float = field(default_factory=time.time)
    signature: str = ""  # Ed25519 signature by source platform

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "transfer_id": self.transfer_id,
            "source_platform": self.source_platform,
            "reason": self.reason,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to sign (excludes signature)"""
        return json.dumps(self.to_dict(), sort_keys=True)

    def hash(self) -> str:
        """Compute transaction hash"""
        return hashlib.sha256(self.signable_content().encode()).hexdigest()


@dataclass
class ATPBalanceSetTransaction:
    """
    Set ATP balance for agent (initialization/testing)

    This transaction sets an agent's ATP balance directly.
    Used for initialization and testing. In production, would be restricted.
    """

    type: str = "ATP_BALANCE_SET"
    platform: str = ""  # Platform where balance is set
    agent_lct: str = ""  # Agent whose balance to set
    amount: float = 0.0  # New balance amount
    reason: str = ""  # Reason (e.g., "GENESIS", "TESTING")
    timestamp: float = field(default_factory=time.time)
    signature: str = ""  # Ed25519 signature by platform

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "type": self.type,
            "platform": self.platform,
            "agent_lct": self.agent_lct,
            "amount": self.amount,
            "reason": self.reason,
            "timestamp": self.timestamp
        }

    def signable_content(self) -> str:
        """Content to sign (excludes signature)"""
        return json.dumps(self.to_dict(), sort_keys=True)

    def hash(self) -> str:
        """Compute transaction hash"""
        return hashlib.sha256(self.signable_content().encode()).hexdigest()


class ATPTransactionProcessor:
    """
    Processes ATP transactions from consensus blocks

    Integrates with ATPLedger to apply transactions when consensus is reached.
    """

    def __init__(self, ledger_map: Dict[str, Any]):
        """
        Initialize processor

        Args:
            ledger_map: Map of platform_name -> ATPLedger instance
        """
        self.ledger_map = ledger_map

        # Track pending transfers (transfer_id -> LOCK transaction)
        self.pending_locks: Dict[str, ATPTransferLockTransaction] = {}

    def get_ledger(self, platform_name: str) -> Optional[Any]:
        """Get ledger for platform"""
        return self.ledger_map.get(platform_name)

    def process_transaction(self, tx_dict: Dict[str, Any], block_sequence: int) -> bool:
        """
        Process ATP transaction from consensus block

        Args:
            tx_dict: Transaction dictionary
            block_sequence: Block sequence number (for logging)

        Returns:
            True if transaction processed successfully, False otherwise
        """
        tx_type = tx_dict.get("type")

        if tx_type == "ATP_TRANSFER_LOCK":
            return self._process_lock(tx_dict, block_sequence)
        elif tx_type == "ATP_TRANSFER_COMMIT":
            return self._process_commit(tx_dict, block_sequence)
        elif tx_type == "ATP_TRANSFER_ROLLBACK":
            return self._process_rollback(tx_dict, block_sequence)
        elif tx_type == "ATP_BALANCE_SET":
            return self._process_balance_set(tx_dict, block_sequence)
        else:
            # Unknown transaction type (might be non-ATP transaction)
            return False

    def _process_lock(self, tx_dict: Dict[str, Any], block_sequence: int) -> bool:
        """Process LOCK transaction"""
        # Reconstruct transaction
        tx = ATPTransferLockTransaction(
            transfer_id=tx_dict["transfer_id"],
            source_platform=tx_dict["source_platform"],
            source_agent=tx_dict["source_agent"],
            dest_platform=tx_dict["dest_platform"],
            dest_agent=tx_dict["dest_agent"],
            amount=tx_dict["amount"],
            timestamp=tx_dict["timestamp"],
            signature=tx_dict.get("signature", "")
        )

        # Get source ledger
        source_ledger = self.get_ledger(tx.source_platform)
        if source_ledger is None:
            print(f"[ATP Processor] Warning: No ledger for {tx.source_platform}")
            return False

        # Initiate transfer (locks ATP) with specified transfer_id
        transfer = source_ledger.initiate_transfer(
            source_agent=tx.source_agent,
            dest_platform=tx.dest_platform,
            dest_agent=tx.dest_agent,
            amount=tx.amount,
            transfer_id=tx.transfer_id
        )

        if transfer is None:
            print(f"[ATP Processor] LOCK failed (insufficient balance or error)")
            return False

        # Store pending lock
        self.pending_locks[tx.transfer_id] = tx

        print(f"[ATP Processor] Block {block_sequence}: LOCK processed")
        print(f"  Transfer ID: {tx.transfer_id}")
        print(f"  {tx.source_agent}@{tx.source_platform} → {tx.dest_agent}@{tx.dest_platform}")
        print(f"  Amount: {tx.amount:.2f} ATP locked")

        return True

    def _process_commit(self, tx_dict: Dict[str, Any], block_sequence: int) -> bool:
        """Process COMMIT transaction"""
        # Reconstruct transaction
        tx = ATPTransferCommitTransaction(
            transfer_id=tx_dict["transfer_id"],
            dest_platform=tx_dict["dest_platform"],
            dest_agent=tx_dict["dest_agent"],
            amount=tx_dict["amount"],
            timestamp=tx_dict["timestamp"],
            signature=tx_dict.get("signature", "")
        )

        # Check if LOCK exists
        lock_tx = self.pending_locks.get(tx.transfer_id)
        if lock_tx is None:
            print(f"[ATP Processor] Warning: COMMIT for unknown LOCK {tx.transfer_id}")
            return False

        # Get destination ledger
        dest_ledger = self.get_ledger(tx.dest_platform)
        if dest_ledger is None:
            print(f"[ATP Processor] Warning: No ledger for {tx.dest_platform}")
            return False

        # Credit destination
        success = dest_ledger.commit_transfer(
            transfer_id=tx.transfer_id,
            dest_agent=tx.dest_agent,
            amount=tx.amount
        )

        if not success:
            print(f"[ATP Processor] COMMIT failed (credit error)")
            return False

        # Get source ledger and finalize (deduct locked ATP)
        source_ledger = self.get_ledger(lock_tx.source_platform)
        if source_ledger:
            source_ledger.finalize_transfer(tx.transfer_id)

        # Remove from pending
        del self.pending_locks[tx.transfer_id]

        print(f"[ATP Processor] Block {block_sequence}: COMMIT processed")
        print(f"  Transfer ID: {tx.transfer_id}")
        print(f"  {lock_tx.source_agent}@{lock_tx.source_platform} → {tx.dest_agent}@{tx.dest_platform}")
        print(f"  Amount: {tx.amount:.2f} ATP credited + deducted")

        return True

    def _process_rollback(self, tx_dict: Dict[str, Any], block_sequence: int) -> bool:
        """Process ROLLBACK transaction"""
        # Reconstruct transaction
        tx = ATPTransferRollbackTransaction(
            transfer_id=tx_dict["transfer_id"],
            source_platform=tx_dict["source_platform"],
            reason=tx_dict["reason"],
            timestamp=tx_dict["timestamp"],
            signature=tx_dict.get("signature", "")
        )

        # Check if LOCK exists
        lock_tx = self.pending_locks.get(tx.transfer_id)
        if lock_tx is None:
            print(f"[ATP Processor] Warning: ROLLBACK for unknown LOCK {tx.transfer_id}")
            return False

        # Get source ledger
        source_ledger = self.get_ledger(tx.source_platform)
        if source_ledger is None:
            print(f"[ATP Processor] Warning: No ledger for {tx.source_platform}")
            return False

        # Rollback (unlock ATP)
        success = source_ledger.rollback_transfer(
            transfer_id=tx.transfer_id,
            reason=tx.reason
        )

        if not success:
            print(f"[ATP Processor] ROLLBACK failed (unlock error)")
            return False

        # Remove from pending
        del self.pending_locks[tx.transfer_id]

        print(f"[ATP Processor] Block {block_sequence}: ROLLBACK processed")
        print(f"  Transfer ID: {tx.transfer_id}")
        print(f"  Reason: {tx.reason}")
        print(f"  {lock_tx.source_agent}@{tx.source_platform} ATP unlocked")

        return True

    def _process_balance_set(self, tx_dict: Dict[str, Any], block_sequence: int) -> bool:
        """Process BALANCE_SET transaction"""
        # Reconstruct transaction
        tx = ATPBalanceSetTransaction(
            platform=tx_dict["platform"],
            agent_lct=tx_dict["agent_lct"],
            amount=tx_dict["amount"],
            reason=tx_dict["reason"],
            timestamp=tx_dict["timestamp"],
            signature=tx_dict.get("signature", "")
        )

        # Get ledger
        ledger = self.get_ledger(tx.platform)
        if ledger is None:
            print(f"[ATP Processor] Warning: No ledger for {tx.platform}")
            return False

        # Set balance
        success = ledger.set_balance(tx.agent_lct, tx.amount)

        if not success:
            print(f"[ATP Processor] BALANCE_SET failed")
            return False

        print(f"[ATP Processor] Block {block_sequence}: BALANCE_SET processed")
        print(f"  Agent: {tx.agent_lct}@{tx.platform}")
        print(f"  Amount: {tx.amount:.2f} ATP")
        print(f"  Reason: {tx.reason}")

        return True

    def get_pending_transfer_count(self) -> int:
        """Get count of pending transfers"""
        return len(self.pending_locks)

    def get_pending_transfers(self) -> List[ATPTransferLockTransaction]:
        """Get all pending LOCK transactions"""
        return list(self.pending_locks.values())
