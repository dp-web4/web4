"""
LCT Identity Registry - Consensus Integration

Integrates identity registry with consensus blockchain.
Identity operations (REGISTER, REVOKE) are processed via consensus blocks.

Author: Legion Autonomous Session #48
Date: 2025-12-02
Status: Phase 2 implementation - consensus integration
References: identity_registry.py, consensus.py, LCT_IDENTITY_SYSTEM.md

Transaction Flow:
1. Client creates IDENTITY_REGISTER or IDENTITY_REVOKE transaction
2. Transaction embedded in consensus block
3. Block reaches consensus (2f+1 agreements)
4. Transaction applied to local identity registry
5. Registry state synchronized across all platforms

Byzantine Fault Tolerance:
- Registry updates only via consensus blocks
- No single platform can forge identities
- 2f+1 agreement required for all operations
- State synchronized across platforms
"""

from typing import Dict, List, Optional, Any, Tuple
import time
import json

from game.engine.identity_registry import (
    IdentityRegistry,
    IdentityRegisterTransaction,
    IdentityRevokeTransaction,
    RegistryOperationType
)


class IdentityConsensusEngine:
    """
    Consensus-integrated identity registry.

    Processes identity transactions from consensus blocks and maintains
    synchronized registry state across all platforms.
    """

    def __init__(self, platform_name: str):
        """
        Initialize identity consensus engine.

        Args:
            platform_name: This platform's name
        """
        self.platform_name = platform_name
        self.registry = IdentityRegistry(platform_name=platform_name)

        # Transaction processing stats
        self.transactions_processed = 0
        self.transactions_failed = 0
        self.last_block_number = 0

    def process_block_transactions(
        self,
        block_number: int,
        transactions: List[Dict[str, Any]]
    ) -> Tuple[int, int, List[str]]:
        """
        Process all identity transactions from a consensus block.

        Args:
            block_number: Block number being processed
            transactions: List of transaction dictionaries from block

        Returns:
            (processed_count, failed_count, error_messages) tuple

        Example:
            >>> engine = IdentityConsensusEngine("Thor")
            >>> processed, failed, errors = engine.process_block_transactions(
            ...     block_number=42,
            ...     transactions=[
            ...         {
            ...             "type": "IDENTITY_REGISTER",
            ...             "lct_id": "lct:web4:agent:alice@Thor#perception",
            ...             "lineage": "alice",
            ...             "context": "Thor",
            ...             "task": "perception",
            ...             "creator_pubkey": "ed25519:ABC123",
            ...             "platform_pubkey": "ed25519:DEF456",
            ...             "signature": "ed25519:SIG123"
            ...         }
            ...     ]
            ... )
        """
        processed = 0
        failed = 0
        errors = []

        for tx in transactions:
            tx_type = tx.get("type", "")

            # Process identity transactions
            if tx_type == "IDENTITY_REGISTER":
                success, error = self._process_register_transaction(block_number, tx)
                if success:
                    processed += 1
                    self.transactions_processed += 1
                else:
                    failed += 1
                    self.transactions_failed += 1
                    errors.append(f"REGISTER failed: {error}")

            elif tx_type == "IDENTITY_REVOKE":
                success, error = self._process_revoke_transaction(block_number, tx)
                if success:
                    processed += 1
                    self.transactions_processed += 1
                else:
                    failed += 1
                    self.transactions_failed += 1
                    errors.append(f"REVOKE failed: {error}")

        # Update last processed block
        if processed > 0 or failed > 0:
            self.last_block_number = block_number

        return (processed, failed, errors)

    def _process_register_transaction(
        self,
        block_number: int,
        tx: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Process IDENTITY_REGISTER transaction.

        Args:
            block_number: Block number
            tx: Transaction dictionary

        Returns:
            (success, error_message) tuple
        """
        try:
            # Extract transaction fields
            lct_id = tx.get("lct_id", "")
            lineage = tx.get("lineage", "")
            context = tx.get("context", "")
            task = tx.get("task", "")
            creator_pubkey = tx.get("creator_pubkey", "")
            platform_pubkey = tx.get("platform_pubkey", "")

            # Compute transaction hash
            tx_hash = self._compute_transaction_hash(tx)

            # Register in registry
            success, reason = self.registry.register(
                lct_id=lct_id,
                lineage=lineage,
                context=context,
                task=task,
                creator_pubkey=creator_pubkey,
                platform_pubkey=platform_pubkey,
                block_number=block_number,
                transaction_hash=tx_hash
            )

            return (success, "" if success else reason)

        except Exception as e:
            return (False, f"Exception: {str(e)}")

    def _process_revoke_transaction(
        self,
        block_number: int,
        tx: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Process IDENTITY_REVOKE transaction.

        Args:
            block_number: Block number
            tx: Transaction dictionary

        Returns:
            (success, error_message) tuple
        """
        try:
            # Extract transaction fields
            lct_id = tx.get("lct_id", "")
            reason = tx.get("reason", "")

            # Revoke in registry
            success, result = self.registry.revoke(
                lct_id=lct_id,
                reason=reason
            )

            return (success, "" if success else result)

        except Exception as e:
            return (False, f"Exception: {str(e)}")

    def _compute_transaction_hash(self, tx: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of transaction"""
        import hashlib
        # Remove signature for hashing
        tx_copy = tx.copy()
        tx_copy.pop("signature", None)
        tx_json = json.dumps(tx_copy, sort_keys=True)
        return hashlib.sha256(tx_json.encode()).hexdigest()

    def create_register_transaction(
        self,
        lct_id: str,
        lineage: str,
        context: str,
        task: str,
        creator_pubkey: str,
        platform_pubkey: str,
        identity_certificate: Optional[Dict[str, Any]] = None,
        signature: str = ""
    ) -> Dict[str, Any]:
        """
        Create IDENTITY_REGISTER transaction for inclusion in consensus block.

        Args:
            lct_id: Full LCT identity string
            lineage: Lineage component
            context: Context component
            task: Task component
            creator_pubkey: Creator's Ed25519 public key
            platform_pubkey: Platform's Ed25519 public key
            identity_certificate: Full identity certificate (optional)
            signature: Creator's signature

        Returns:
            Transaction dictionary ready for consensus block

        Example:
            >>> engine = IdentityConsensusEngine("Thor")
            >>> tx = engine.create_register_transaction(
            ...     lct_id="lct:web4:agent:alice@Thor#perception",
            ...     lineage="alice",
            ...     context="Thor",
            ...     task="perception",
            ...     creator_pubkey="ed25519:ABC123",
            ...     platform_pubkey="ed25519:DEF456",
            ...     signature="ed25519:SIG123"
            ... )
        """
        tx = IdentityRegisterTransaction(
            lct_id=lct_id,
            lineage=lineage,
            context=context,
            task=task,
            creator_pubkey=creator_pubkey,
            platform_pubkey=platform_pubkey,
            identity_certificate=identity_certificate or {},
            signature=signature,
            timestamp=time.time()
        )

        return tx.to_dict()

    def create_revoke_transaction(
        self,
        lct_id: str,
        reason: str,
        revoker: str,
        signature: str = ""
    ) -> Dict[str, Any]:
        """
        Create IDENTITY_REVOKE transaction for inclusion in consensus block.

        Args:
            lct_id: LCT identity to revoke
            reason: Reason for revocation
            revoker: Who is revoking (creator or platform)
            signature: Revoker's signature

        Returns:
            Transaction dictionary ready for consensus block

        Example:
            >>> engine = IdentityConsensusEngine("Thor")
            >>> tx = engine.create_revoke_transaction(
            ...     lct_id="lct:web4:agent:alice@Thor#perception",
            ...     reason="COMPROMISED",
            ...     revoker="alice",
            ...     signature="ed25519:REVOKE_SIG"
            ... )
        """
        tx = IdentityRevokeTransaction(
            lct_id=lct_id,
            reason=reason,
            revoker=revoker,
            signature=signature,
            timestamp=time.time()
        )

        return tx.to_dict()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get consensus engine statistics.

        Returns:
            Dictionary with engine and registry stats
        """
        registry_stats = self.registry.get_stats()

        return {
            "platform": self.platform_name,
            "consensus": {
                "transactions_processed": self.transactions_processed,
                "transactions_failed": self.transactions_failed,
                "last_block_number": self.last_block_number
            },
            "registry": registry_stats
        }

    def export_state(self) -> Dict[str, Any]:
        """
        Export complete identity registry state.

        Used for:
        - State synchronization between platforms
        - Backup and recovery
        - Debugging and auditing

        Returns:
            Dictionary with complete state
        """
        return {
            "platform": self.platform_name,
            "last_block_number": self.last_block_number,
            "transactions_processed": self.transactions_processed,
            "identities": self.registry.export_records()
        }

    def import_state(self, state: Dict[str, Any]) -> Tuple[int, int]:
        """
        Import identity registry state.

        Used for:
        - State synchronization from other platforms
        - Recovery from backup
        - Genesis block initialization

        Args:
            state: State dictionary from export_state()

        Returns:
            (imported_count, skipped_count) tuple
        """
        # Import identity records
        identities = state.get("identities", [])
        imported, skipped = self.registry.import_records(identities)

        # Update block number if higher
        block_number = state.get("last_block_number", 0)
        if block_number > self.last_block_number:
            self.last_block_number = block_number

        return (imported, skipped)


def create_genesis_identity_block(
    platform_name: str,
    identities: List[Dict[str, Any]],
    block_number: int = 0
) -> Dict[str, Any]:
    """
    Create genesis block with initial identity registrations.

    Used to initialize identity registry with pre-authorized identities.

    Args:
        platform_name: Platform creating genesis block
        identities: List of identity registration transactions
        block_number: Genesis block number (default: 0)

    Returns:
        Genesis block dictionary

    Example:
        >>> genesis_block = create_genesis_identity_block(
        ...     platform_name="Thor",
        ...     identities=[
        ...         {
        ...             "type": "IDENTITY_REGISTER",
        ...             "lct_id": "lct:web4:agent:system:genesis@Thor#admin.full",
        ...             "lineage": "system:genesis",
        ...             "context": "Thor",
        ...             "task": "admin.full",
        ...             "creator_pubkey": "ed25519:GENESIS_KEY",
        ...             "platform_pubkey": "ed25519:THOR_KEY",
        ...             "signature": "ed25519:GENESIS_SIG"
        ...         }
        ...     ]
        ... )
    """
    from game.engine.consensus import Block

    # Create block header
    header = {
        "block_number": block_number,
        "previous_hash": "0" * 64,  # Genesis has no previous block
        "merkle_root": "genesis",
        "type": "GENESIS_IDENTITY"
    }

    # Create block
    block = Block(
        header=header,
        transactions=identities,
        timestamp=time.time(),
        proposer_platform=platform_name
    )

    return block.to_dict()
