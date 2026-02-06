"""
ATP Ledger - Cross-Platform ATP Accounting

Implements ATP (Attention/Token/Payment) accounting for distributed Web4 societies.
Supports atomic cross-platform transfers via consensus-based settlement.

Author: Legion Autonomous Session #43
Date: 2025-11-30
Status: Research prototype - tested at research scale
Integration: Built on Session #43 consensus protocol

References:
- CROSS_PLATFORM_ATP_PROTOCOL.md (design specification)
- Session #43: Distributed consensus (FB-PBFT)
- Session #41: ATP economic analysis
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class TransferPhase(Enum):
    """ATP transfer phases (two-phase commit)"""
    LOCK = "LOCK"
    COMMIT = "COMMIT"
    ROLLBACK = "ROLLBACK"
    COMPLETE = "COMPLETE"


@dataclass
class ATPAccount:
    """
    ATP account for an agent.

    Tracks total balance, available balance, and locked balance (in cross-platform transfers).
    """

    agent_lct: str
    total: float = 0.0  # Total ATP balance
    locked: float = 0.0  # ATP locked in pending transfers

    @property
    def available(self) -> float:
        """Available ATP (total - locked)"""
        return self.total - self.locked

    def lock(self, amount: float) -> bool:
        """
        Lock ATP for cross-platform transfer.

        Returns True if successful, False if insufficient available balance.
        """
        if amount <= 0:
            return False
        if self.available < amount:
            return False

        self.locked += amount
        return True

    def unlock(self, amount: float) -> bool:
        """
        Unlock ATP (rollback transfer).

        Returns True if successful, False if insufficient locked balance.
        """
        if amount <= 0:
            return False
        if self.locked < amount:
            return False

        self.locked -= amount
        return True

    def deduct(self, amount: float) -> bool:
        """
        Deduct ATP permanently (complete transfer).

        Assumes amount was previously locked.
        Returns True if successful, False if insufficient locked balance.
        """
        if amount <= 0:
            return False
        if self.locked < amount:
            return False

        self.locked -= amount
        self.total -= amount
        return True

    def credit(self, amount: float) -> bool:
        """
        Credit ATP (receive transfer).

        Returns True if successful, False if invalid amount.
        """
        if amount <= 0:
            return False

        self.total += amount
        return True


@dataclass
class ATPTransfer:
    """
    Cross-platform ATP transfer record.

    Tracks state of two-phase commit protocol.
    """

    transfer_id: str
    source_platform: str
    source_agent: str
    dest_platform: str
    dest_agent: str
    amount: float
    phase: TransferPhase = TransferPhase.LOCK
    initiated_at: float = field(default_factory=time.time)
    locked_at: Optional[float] = None
    committed_at: Optional[float] = None
    completed_at: Optional[float] = None
    rollback_reason: Optional[str] = None

    def is_pending(self) -> bool:
        """Check if transfer is pending (not completed or rolled back)"""
        return self.phase in [TransferPhase.LOCK, TransferPhase.COMMIT]

    def is_complete(self) -> bool:
        """Check if transfer is complete"""
        return self.phase == TransferPhase.COMPLETE

    def is_rolled_back(self) -> bool:
        """Check if transfer was rolled back"""
        return self.phase == TransferPhase.ROLLBACK


class ATPLedger:
    """
    Platform-level ATP ledger.

    Manages ATP accounts for all agents and tracks cross-platform transfers.
    """

    def __init__(self, platform_name: str):
        self.platform_name = platform_name

        # Local accounts (agents native to this platform)
        self.accounts: Dict[str, ATPAccount] = {}

        # Pending transfers (by transfer_id)
        self.pending_transfers: Dict[str, ATPTransfer] = {}

        # Completed/rolled-back transfer history
        self.transfer_history: List[ATPTransfer] = []

        # Statistics
        self.total_transfers_initiated = 0
        self.total_transfers_completed = 0
        self.total_transfers_rolled_back = 0

    # -------------------------------------------------------------------------
    # Account Management
    # -------------------------------------------------------------------------

    def create_account(self, agent_lct: str, initial_balance: float = 0.0) -> ATPAccount:
        """Create new ATP account for agent"""
        if agent_lct in self.accounts:
            raise ValueError(f"Account {agent_lct} already exists")

        account = ATPAccount(agent_lct=agent_lct, total=initial_balance)
        self.accounts[agent_lct] = account
        return account

    def get_account(self, agent_lct: str) -> Optional[ATPAccount]:
        """Get ATP account for agent"""
        return self.accounts.get(agent_lct)

    def get_or_create_account(self, agent_lct: str) -> ATPAccount:
        """Get account, creating if it doesn't exist"""
        if agent_lct not in self.accounts:
            return self.create_account(agent_lct)
        return self.accounts[agent_lct]

    def get_balance(self, agent_lct: str) -> Tuple[float, float, float]:
        """
        Get balance for agent.

        Returns (total, available, locked) or (0, 0, 0) if account doesn't exist.
        """
        account = self.get_account(agent_lct)
        if account is None:
            return (0.0, 0.0, 0.0)
        return (account.total, account.available, account.locked)

    def set_balance(self, agent_lct: str, amount: float) -> bool:
        """Set balance for agent (for initialization/testing)"""
        account = self.get_or_create_account(agent_lct)
        account.total = amount
        account.locked = 0.0
        return True

    # -------------------------------------------------------------------------
    # Intra-Platform Transfers (Existing)
    # -------------------------------------------------------------------------

    def transfer_local(self, from_agent: str, to_agent: str, amount: float) -> bool:
        """
        Transfer ATP between agents on same platform (instant, no consensus).

        Returns True if successful, False if insufficient balance.
        """
        if amount <= 0:
            return False

        from_account = self.get_or_create_account(from_agent)
        to_account = self.get_or_create_account(to_agent)

        # Check sufficient available balance
        if from_account.available < amount:
            return False

        # Atomic transfer
        from_account.total -= amount
        to_account.total += amount

        return True

    # -------------------------------------------------------------------------
    # Cross-Platform Transfers (NEW)
    # -------------------------------------------------------------------------

    def initiate_transfer(
        self,
        source_agent: str,
        dest_platform: str,
        dest_agent: str,
        amount: float,
        transfer_id: Optional[str] = None
    ) -> Optional[ATPTransfer]:
        """
        Initiate cross-platform ATP transfer (Phase 1: LOCK).

        Locks ATP in source account and creates transfer record.
        Returns transfer record if successful, None if insufficient balance.

        Args:
            source_agent: Agent initiating transfer (LCT)
            dest_platform: Destination platform name
            dest_agent: Destination agent (LCT)
            amount: ATP amount to transfer
            transfer_id: Optional transfer ID (generated if not provided)
        """
        if amount <= 0:
            return None

        # Check sufficient balance
        source_account = self.get_or_create_account(source_agent)
        if source_account.available < amount:
            return None

        # Lock ATP
        if not source_account.lock(amount):
            return None

        # Create transfer record
        transfer = ATPTransfer(
            transfer_id=transfer_id or str(uuid.uuid4()),
            source_platform=self.platform_name,
            source_agent=source_agent,
            dest_platform=dest_platform,
            dest_agent=dest_agent,
            amount=amount,
            phase=TransferPhase.LOCK,
            locked_at=time.time()
        )

        self.pending_transfers[transfer.transfer_id] = transfer
        self.total_transfers_initiated += 1

        return transfer

    def commit_transfer(self, transfer_id: str, dest_agent: str, amount: float) -> bool:
        """
        Commit transfer (Phase 2: COMMIT).

        Credits ATP to destination account.
        Called by destination platform after receiving COMMIT consensus.
        Returns True if successful.
        """
        # For destination platform, this is a credit operation
        dest_account = self.get_or_create_account(dest_agent)
        if not dest_account.credit(amount):
            return False

        # Record transfer completion
        transfer = ATPTransfer(
            transfer_id=transfer_id,
            source_platform="<remote>",  # We're the destination
            source_agent="<remote>",
            dest_platform=self.platform_name,
            dest_agent=dest_agent,
            amount=amount,
            phase=TransferPhase.COMMIT,
            committed_at=time.time()
        )
        self.pending_transfers[transfer_id] = transfer

        return True

    def finalize_transfer(self, transfer_id: str) -> bool:
        """
        Finalize transfer (Phase 3: RELEASE).

        Permanently deducts locked ATP from source account.
        Called by source platform after receiving COMMIT consensus.
        Returns True if successful.
        """
        transfer = self.pending_transfers.get(transfer_id)
        if transfer is None:
            return False

        if transfer.phase != TransferPhase.LOCK:
            return False

        # Deduct locked ATP
        source_account = self.get_account(transfer.source_agent)
        if source_account is None:
            return False

        if not source_account.deduct(transfer.amount):
            return False

        # Update transfer state
        transfer.phase = TransferPhase.COMPLETE
        transfer.completed_at = time.time()

        # Move to history
        del self.pending_transfers[transfer_id]
        self.transfer_history.append(transfer)
        self.total_transfers_completed += 1

        return True

    def rollback_transfer(self, transfer_id: str, reason: str = "TIMEOUT") -> bool:
        """
        Rollback transfer (unlock ATP).

        Unlocks ATP in source account.
        Called when transfer fails (timeout, destination unreachable, etc.).
        Returns True if successful.
        """
        transfer = self.pending_transfers.get(transfer_id)
        if transfer is None:
            return False

        if transfer.phase != TransferPhase.LOCK:
            return False

        # Unlock ATP
        source_account = self.get_account(transfer.source_agent)
        if source_account is None:
            return False

        if not source_account.unlock(transfer.amount):
            return False

        # Update transfer state
        transfer.phase = TransferPhase.ROLLBACK
        transfer.rollback_reason = reason

        # Move to history
        del self.pending_transfers[transfer_id]
        self.transfer_history.append(transfer)
        self.total_transfers_rolled_back += 1

        return True

    # -------------------------------------------------------------------------
    # Transfer Queries
    # -------------------------------------------------------------------------

    def get_transfer(self, transfer_id: str) -> Optional[ATPTransfer]:
        """Get transfer by ID (pending or history)"""
        if transfer_id in self.pending_transfers:
            return self.pending_transfers[transfer_id]

        for transfer in self.transfer_history:
            if transfer.transfer_id == transfer_id:
                return transfer

        return None

    def get_pending_transfers(self) -> List[ATPTransfer]:
        """Get all pending transfers"""
        return list(self.pending_transfers.values())

    def get_transfers_for_agent(self, agent_lct: str) -> List[ATPTransfer]:
        """Get all transfers (pending + history) for agent"""
        transfers = []

        # Pending transfers
        for transfer in self.pending_transfers.values():
            if transfer.source_agent == agent_lct or transfer.dest_agent == agent_lct:
                transfers.append(transfer)

        # Historical transfers
        for transfer in self.transfer_history:
            if transfer.source_agent == agent_lct or transfer.dest_agent == agent_lct:
                transfers.append(transfer)

        return transfers

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, any]:
        """Get ledger statistics"""
        return {
            "platform": self.platform_name,
            "total_accounts": len(self.accounts),
            "total_balance": sum(acc.total for acc in self.accounts.values()),
            "total_locked": sum(acc.locked for acc in self.accounts.values()),
            "pending_transfers": len(self.pending_transfers),
            "transfers_initiated": self.total_transfers_initiated,
            "transfers_completed": self.total_transfers_completed,
            "transfers_rolled_back": self.total_transfers_rolled_back
        }

    def get_summary(self) -> str:
        """Get human-readable summary"""
        stats = self.get_stats()
        return f"""ATP Ledger Summary ({stats['platform']})
  Accounts: {stats['total_accounts']}
  Total Balance: {stats['total_balance']:.2f} ATP
  Locked Balance: {stats['total_locked']:.2f} ATP
  Pending Transfers: {stats['pending_transfers']}
  Transfers: {stats['transfers_completed']} completed, {stats['transfers_rolled_back']} rolled back
"""
