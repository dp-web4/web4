"""
ATP (Autonomy Trust Points) Management System
==============================================

Central ATP tracking and enforcement for Web4 security mitigations.

ATP is the economic resource that powers Web4 operations. This module
provides:
- Balance tracking per entity
- Deduction/credit operations
- Transaction history
- Balance queries
- Economic security enforcement

Used by all services to implement Phase 1 security mitigations from
Session 11 security research.

Author: Web4 Security Implementation (Session 12)
Date: 2025-11-10
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


# =============================================================================
# Data Models
# =============================================================================

class TransactionType(Enum):
    """ATP transaction types"""
    MINT_LCT = "mint_lct"
    RECORD_OUTCOME = "record_outcome"
    ALLOCATE_RESOURCE = "allocate_resource"
    ADD_TRIPLE = "add_triple"
    VOTE = "vote"
    GRANT = "grant"  # System grants ATP
    REFUND = "refund"  # Refund for verified non-usage
    PENALTY = "penalty"  # Slashed for violations
    TRANSFER = "transfer"  # Entity-to-entity transfer


@dataclass
class ATPTransaction:
    """Record of an ATP transaction"""
    transaction_id: str
    entity_id: str
    transaction_type: TransactionType
    amount: int  # Positive for credits, negative for debits
    balance_after: int
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "transaction_id": self.transaction_id,
            "entity_id": self.entity_id,
            "transaction_type": self.transaction_type.value,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "description": self.description
        }


# =============================================================================
# ATP Manager
# =============================================================================

class ATPManager:
    """
    Central ATP management system for Web4.

    Maintains ATP balances for all entities and enforces economic
    security controls.
    """

    def __init__(self, initial_system_atp: int = 1_000_000):
        """
        Initialize ATP manager.

        Args:
            initial_system_atp: Starting ATP for system grants
        """
        self.balances: Dict[str, int] = {}  # entity_id -> balance
        self.transactions: Dict[str, List[ATPTransaction]] = {}  # entity_id -> transactions
        self.system_balance = initial_system_atp
        self._transaction_counter = 0

    def get_balance(self, entity_id: str) -> int:
        """
        Get ATP balance for an entity.

        Args:
            entity_id: Entity LCT ID

        Returns:
            Current ATP balance (0 if entity not found)
        """
        return self.balances.get(entity_id, 0)

    def has_sufficient_balance(self, entity_id: str, amount: int) -> bool:
        """
        Check if entity has sufficient ATP balance.

        Args:
            entity_id: Entity LCT ID
            amount: Required ATP amount

        Returns:
            True if balance >= amount, False otherwise
        """
        return self.get_balance(entity_id) >= amount

    def deduct(
        self,
        entity_id: str,
        amount: int,
        transaction_type: TransactionType,
        description: str = "",
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Optional[ATPTransaction]]:
        """
        Deduct ATP from an entity's balance.

        Args:
            entity_id: Entity LCT ID
            amount: ATP amount to deduct (must be positive)
            transaction_type: Type of transaction
            description: Human-readable description
            metadata: Additional transaction metadata

        Returns:
            Tuple of (success: bool, transaction: Optional[ATPTransaction])
        """
        if amount < 0:
            return False, None

        current_balance = self.get_balance(entity_id)

        if current_balance < amount:
            return False, None

        # Perform deduction
        new_balance = current_balance - amount
        self.balances[entity_id] = new_balance

        # Record transaction
        transaction = self._create_transaction(
            entity_id=entity_id,
            amount=-amount,  # Negative for deduction
            balance_after=new_balance,
            transaction_type=transaction_type,
            description=description,
            metadata=metadata or {}
        )

        # Store transaction
        if entity_id not in self.transactions:
            self.transactions[entity_id] = []
        self.transactions[entity_id].append(transaction)

        return True, transaction

    def credit(
        self,
        entity_id: str,
        amount: int,
        transaction_type: TransactionType,
        description: str = "",
        metadata: Optional[Dict] = None
    ) -> ATPTransaction:
        """
        Credit ATP to an entity's balance.

        Args:
            entity_id: Entity LCT ID
            amount: ATP amount to credit (must be positive)
            transaction_type: Type of transaction
            description: Human-readable description
            metadata: Additional transaction metadata

        Returns:
            ATPTransaction record
        """
        if amount < 0:
            amount = 0

        current_balance = self.get_balance(entity_id)
        new_balance = current_balance + amount
        self.balances[entity_id] = new_balance

        # Record transaction
        transaction = self._create_transaction(
            entity_id=entity_id,
            amount=amount,  # Positive for credit
            balance_after=new_balance,
            transaction_type=transaction_type,
            description=description,
            metadata=metadata or {}
        )

        # Store transaction
        if entity_id not in self.transactions:
            self.transactions[entity_id] = []
        self.transactions[entity_id].append(transaction)

        return transaction

    def grant_initial_atp(
        self,
        entity_id: str,
        amount: int = 10000,
        reason: str = "Initial ATP grant"
    ) -> ATPTransaction:
        """
        Grant initial ATP to a new entity from system pool.

        Args:
            entity_id: Entity LCT ID
            amount: ATP amount to grant
            reason: Reason for grant

        Returns:
            ATPTransaction record
        """
        # Deduct from system balance
        if self.system_balance >= amount:
            self.system_balance -= amount
        else:
            amount = self.system_balance
            self.system_balance = 0

        # Credit to entity
        return self.credit(
            entity_id=entity_id,
            amount=amount,
            transaction_type=TransactionType.GRANT,
            description=reason,
            metadata={"source": "system", "initial_grant": True}
        )

    def transfer(
        self,
        from_entity: str,
        to_entity: str,
        amount: int,
        description: str = ""
    ) -> Tuple[bool, Optional[ATPTransaction], Optional[ATPTransaction]]:
        """
        Transfer ATP between entities.

        Args:
            from_entity: Source entity LCT ID
            to_entity: Destination entity LCT ID
            amount: ATP amount to transfer
            description: Transfer description

        Returns:
            Tuple of (success, from_transaction, to_transaction)
        """
        # Deduct from source
        success, from_tx = self.deduct(
            entity_id=from_entity,
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            description=f"Transfer to {to_entity}: {description}",
            metadata={"recipient": to_entity}
        )

        if not success:
            return False, None, None

        # Credit to destination
        to_tx = self.credit(
            entity_id=to_entity,
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            description=f"Transfer from {from_entity}: {description}",
            metadata={"sender": from_entity}
        )

        return True, from_tx, to_tx

    def get_transaction_history(
        self,
        entity_id: str,
        limit: Optional[int] = None
    ) -> List[ATPTransaction]:
        """
        Get transaction history for an entity.

        Args:
            entity_id: Entity LCT ID
            limit: Maximum number of transactions to return (most recent first)

        Returns:
            List of ATP transactions
        """
        transactions = self.transactions.get(entity_id, [])

        # Sort by timestamp descending (most recent first)
        sorted_txs = sorted(
            transactions,
            key=lambda tx: tx.timestamp,
            reverse=True
        )

        if limit:
            return sorted_txs[:limit]
        return sorted_txs

    def get_statistics(self) -> Dict:
        """
        Get ATP system statistics.

        Returns:
            Dictionary with system-wide ATP statistics
        """
        total_entity_balance = sum(self.balances.values())
        total_entities = len(self.balances)
        total_transactions = sum(len(txs) for txs in self.transactions.values())

        # Calculate transaction type distribution
        tx_type_counts = {}
        for tx_list in self.transactions.values():
            for tx in tx_list:
                tx_type = tx.transaction_type.value
                tx_type_counts[tx_type] = tx_type_counts.get(tx_type, 0) + 1

        return {
            "total_entity_balance": total_entity_balance,
            "system_balance": self.system_balance,
            "total_atp": total_entity_balance + self.system_balance,
            "total_entities": total_entities,
            "total_transactions": total_transactions,
            "average_balance": total_entity_balance / total_entities if total_entities > 0 else 0,
            "transaction_type_distribution": tx_type_counts
        }

    def _create_transaction(
        self,
        entity_id: str,
        amount: int,
        balance_after: int,
        transaction_type: TransactionType,
        description: str,
        metadata: Dict
    ) -> ATPTransaction:
        """
        Create a transaction record.

        Args:
            entity_id: Entity LCT ID
            amount: Transaction amount (positive for credit, negative for debit)
            balance_after: Balance after transaction
            transaction_type: Type of transaction
            description: Human-readable description
            metadata: Additional metadata

        Returns:
            ATPTransaction object
        """
        self._transaction_counter += 1
        transaction_id = f"tx:{self._transaction_counter:08d}"

        return ATPTransaction(
            transaction_id=transaction_id,
            entity_id=entity_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=balance_after,
            timestamp=datetime.now(),
            metadata=metadata,
            description=description
        )

    def save_state(self, filepath: str):
        """
        Save ATP manager state to file.

        Args:
            filepath: Path to save state file
        """
        state = {
            "balances": self.balances,
            "system_balance": self.system_balance,
            "transactions": {
                entity_id: [tx.to_dict() for tx in txs]
                for entity_id, txs in self.transactions.items()
            },
            "transaction_counter": self._transaction_counter
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, filepath: str):
        """
        Load ATP manager state from file.

        Args:
            filepath: Path to state file
        """
        with open(filepath, 'r') as f:
            state = json.load(f)

        self.balances = state["balances"]
        self.system_balance = state["system_balance"]
        self._transaction_counter = state["transaction_counter"]

        # Reconstruct transactions
        self.transactions = {}
        for entity_id, tx_dicts in state["transactions"].items():
            self.transactions[entity_id] = [
                ATPTransaction(
                    transaction_id=tx["transaction_id"],
                    entity_id=tx["entity_id"],
                    transaction_type=TransactionType(tx["transaction_type"]),
                    amount=tx["amount"],
                    balance_after=tx["balance_after"],
                    timestamp=datetime.fromisoformat(tx["timestamp"]),
                    metadata=tx["metadata"],
                    description=tx["description"]
                )
                for tx in tx_dicts
            ]


# =============================================================================
# Global ATP Manager Instance
# =============================================================================

# Single global instance shared across all services
# In production, this would be backed by a database
_atp_manager = ATPManager(initial_system_atp=10_000_000)  # 10M ATP system pool


def get_atp_manager() -> ATPManager:
    """Get the global ATP manager instance"""
    return _atp_manager


# =============================================================================
# Convenience Functions
# =============================================================================

def get_balance(entity_id: str) -> int:
    """Get ATP balance for entity"""
    return _atp_manager.get_balance(entity_id)


def deduct_atp(
    entity_id: str,
    amount: int,
    transaction_type: TransactionType,
    description: str = "",
    metadata: Optional[Dict] = None
) -> Tuple[bool, Optional[ATPTransaction]]:
    """Deduct ATP from entity"""
    return _atp_manager.deduct(
        entity_id=entity_id,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        metadata=metadata
    )


def credit_atp(
    entity_id: str,
    amount: int,
    transaction_type: TransactionType,
    description: str = "",
    metadata: Optional[Dict] = None
) -> ATPTransaction:
    """Credit ATP to entity"""
    return _atp_manager.credit(
        entity_id=entity_id,
        amount=amount,
        transaction_type=transaction_type,
        description=description,
        metadata=metadata
    )


def grant_initial_atp(entity_id: str, amount: int = 10000) -> ATPTransaction:
    """Grant initial ATP to new entity"""
    return _atp_manager.grant_initial_atp(entity_id, amount)


# =============================================================================
# Usage Example
# =============================================================================

if __name__ == "__main__":
    # Example usage
    manager = ATPManager()

    # Grant initial ATP to a new entity
    entity = "lct:web4:ai:test_society:alice"
    manager.grant_initial_atp(entity, amount=5000)

    print(f"Balance after grant: {manager.get_balance(entity)} ATP")

    # Deduct ATP for LCT minting
    success, tx = manager.deduct(
        entity_id=entity,
        amount=100,
        transaction_type=TransactionType.MINT_LCT,
        description="Minting new LCT for agent_bob"
    )

    if success:
        print(f"Deducted 100 ATP. New balance: {manager.get_balance(entity)} ATP")
        print(f"Transaction ID: {tx.transaction_id}")

    # Get transaction history
    history = manager.get_transaction_history(entity)
    print(f"\nTransaction history ({len(history)} transactions):")
    for tx in history:
        print(f"  {tx.timestamp.isoformat()}: {tx.transaction_type.value} "
              f"{tx.amount:+d} ATP (balance: {tx.balance_after})")

    # Get system statistics
    stats = manager.get_statistics()
    print(f"\nSystem Statistics:")
    print(f"  Total entities: {stats['total_entities']}")
    print(f"  Total entity balance: {stats['total_entity_balance']} ATP")
    print(f"  System balance: {stats['system_balance']} ATP")
    print(f"  Total transactions: {stats['total_transactions']}")
