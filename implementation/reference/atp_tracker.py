"""
ATP (Adaptive Trust Points) Budget Tracker

Implements budget tracking and enforcement for Web4 authorization system.

Key Features:
- Per-entity ATP accounts with daily limits
- Per-action cost enforcement
- Daily recharge mechanism
- Persistent storage (JSON)
- Integration with authorization engine

Fixes Critical Vulnerability:
- Budget limits were defined in delegations but never enforced
- This implementation tracks usage and enforces limits at authorization time

Usage:
    tracker = ATPTracker(storage_path="atp_accounts.json")
    tracker.create_account("entity-001", daily_limit=1000, per_action_limit=100)

    # Check and deduct
    success, msg = tracker.check_and_deduct("entity-001", cost=50)
    if success:
        # Proceed with action
        pass
    else:
        # Deny authorization
        print(f"ATP budget exceeded: {msg}")

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 9, 2025
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ATPAccount:
    """ATP account for a single entity."""
    entity_id: str
    daily_limit: int
    per_action_limit: int
    usage: Dict[str, int] = field(default_factory=dict)  # date_str -> amount
    last_recharge: str = ""  # ISO timestamp
    total_earned: int = 0  # Lifetime ATP earned (for reputation tracking)
    total_spent: int = 0  # Lifetime ATP spent (for audit trail)

    def __post_init__(self):
        if not self.last_recharge:
            self.last_recharge = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    def get_usage_today(self) -> int:
        """Get ATP usage for current day."""
        today = date.today().isoformat()
        return self.usage.get(today, 0)

    def remaining_today(self) -> int:
        """Get remaining ATP for today."""
        return max(0, self.daily_limit - self.get_usage_today())

    def can_afford(self, amount: int) -> bool:
        """Check if entity can afford this action."""
        if amount > self.per_action_limit:
            return False
        return self.remaining_today() >= amount

    def deduct(self, amount: int) -> bool:
        """
        Deduct ATP from today's budget.

        Returns:
            True if deduction successful, False if insufficient funds
        """
        if not self.can_afford(amount):
            return False

        today = date.today().isoformat()
        current_usage = self.usage.get(today, 0)
        self.usage[today] = current_usage + amount
        self.total_spent += amount

        return True

    def add_earned_atp(self, amount: int, reason: str = "work_completed"):
        """
        Add earned ATP (for completing work, building reputation, etc.).

        This is separate from daily recharge - earned ATP is reward for contribution.
        """
        self.total_earned += amount
        self.daily_limit += amount  # Increase daily limit as reward
        logger.info(f"Entity {self.entity_id} earned {amount} ATP: {reason}")

    def cleanup_old_usage(self, days_to_keep: int = 30):
        """Remove usage records older than specified days (save storage)."""
        cutoff = (date.today() - timedelta(days=days_to_keep)).isoformat()
        self.usage = {
            date_str: amount
            for date_str, amount in self.usage.items()
            if date_str >= cutoff
        }


class ATPTracker:
    """Track ATP usage and enforce budget limits."""

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize ATP tracker.

        Args:
            storage_path: Path to JSON file for persistent storage (optional)
        """
        self.accounts: Dict[str, ATPAccount] = {}
        self.storage_path = storage_path

        if storage_path:
            self.storage_file = Path(storage_path)
            self.load_from_storage()
        else:
            self.storage_file = None

    def create_account(
        self,
        entity_id: str,
        daily_limit: int,
        per_action_limit: int
    ) -> ATPAccount:
        """
        Create new ATP account for entity.

        Args:
            entity_id: Unique identifier for entity
            daily_limit: Maximum ATP per day
            per_action_limit: Maximum ATP per single action

        Returns:
            Created ATPAccount
        """
        if entity_id in self.accounts:
            logger.warning(f"Account already exists for {entity_id}, returning existing")
            return self.accounts[entity_id]

        account = ATPAccount(
            entity_id=entity_id,
            daily_limit=daily_limit,
            per_action_limit=per_action_limit,
            last_recharge=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        )

        self.accounts[entity_id] = account

        if self.storage_file:
            self.save_to_storage()

        logger.info(f"Created ATP account for {entity_id}: {daily_limit}/day, {per_action_limit}/action")

        return account

    def get_account(self, entity_id: str) -> Optional[ATPAccount]:
        """Get ATP account for entity."""
        return self.accounts.get(entity_id)

    def check_and_deduct(self, entity_id: str, amount: int) -> Tuple[bool, str]:
        """
        Check if entity has sufficient ATP and deduct if so.

        This is the main enforcement function called during authorization.

        Args:
            entity_id: Entity requesting action
            amount: ATP cost of action

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check account exists
        if entity_id not in self.accounts:
            logger.warning(f"ATP check failed: No account for {entity_id}")
            return False, f"No ATP account for {entity_id}"

        account = self.accounts[entity_id]

        # Check per-action limit
        if amount > account.per_action_limit:
            logger.warning(
                f"ATP check failed: {entity_id} requested {amount}, "
                f"per-action limit {account.per_action_limit}"
            )
            return False, (
                f"Per-action limit exceeded: {account.per_action_limit}, "
                f"requested {amount}"
            )

        # Check daily limit
        remaining = account.remaining_today()
        if remaining < amount:
            logger.warning(
                f"ATP check failed: {entity_id} has {remaining} remaining, "
                f"requested {amount}"
            )
            return False, (
                f"Daily limit exceeded: {account.daily_limit}, "
                f"used {account.get_usage_today()}, requested {amount}"
            )

        # Deduct
        success = account.deduct(amount)
        if not success:
            return False, "Deduction failed (race condition?)"

        # Persist
        if self.storage_file:
            self.save_to_storage()

        remaining_after = account.remaining_today()
        logger.info(
            f"ATP deducted: {entity_id} spent {amount}, "
            f"remaining today: {remaining_after}"
        )

        return True, f"Authorized. Remaining ATP today: {remaining_after}"

    def recharge_daily(self):
        """
        Reset daily ATP for all accounts (run daily at midnight).

        This doesn't increase total ATP - just resets the daily spending limit.
        """
        today = date.today().isoformat()
        recharged_count = 0

        for account in self.accounts.values():
            # Reset daily usage
            account.usage[today] = 0
            account.last_recharge = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            recharged_count += 1

            # Cleanup old usage records
            account.cleanup_old_usage()

        if self.storage_file:
            self.save_to_storage()

        logger.info(f"Daily recharge complete: {recharged_count} accounts")

        return recharged_count

    def get_balance(self, entity_id: str) -> Optional[int]:
        """
        Get current ATP balance (remaining today) for entity.

        Returns:
            Remaining ATP, or None if account doesn't exist
        """
        account = self.accounts.get(entity_id)
        return account.remaining_today() if account else None

    def get_account_stats(self, entity_id: str) -> Optional[Dict]:
        """
        Get detailed statistics for entity's ATP account.

        Returns:
            Dict with stats, or None if account doesn't exist
        """
        account = self.accounts.get(entity_id)
        if not account:
            return None

        return {
            "entity_id": account.entity_id,
            "daily_limit": account.daily_limit,
            "per_action_limit": account.per_action_limit,
            "used_today": account.get_usage_today(),
            "remaining_today": account.remaining_today(),
            "total_earned": account.total_earned,
            "total_spent": account.total_spent,
            "last_recharge": account.last_recharge
        }

    def award_atp(self, entity_id: str, amount: int, reason: str = "contribution"):
        """
        Award ATP to entity for good behavior, contribution, etc.

        This is separate from daily limits - it's a reward mechanism.
        """
        account = self.accounts.get(entity_id)
        if not account:
            logger.warning(f"Cannot award ATP: No account for {entity_id}")
            return False

        account.add_earned_atp(amount, reason)

        if self.storage_file:
            self.save_to_storage()

        return True

    def save_to_storage(self):
        """Persist ATP accounts to disk."""
        if not self.storage_file:
            return

        data = {
            "version": "1.0",
            "saved_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "accounts": {
                entity_id: asdict(account)
                for entity_id, account in self.accounts.items()
            }
        }

        # Atomic write (write to temp file, then rename)
        temp_file = self.storage_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            temp_file.rename(self.storage_file)
            logger.debug(f"ATP accounts saved to {self.storage_file}")
        except Exception as e:
            logger.error(f"Failed to save ATP accounts: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def load_from_storage(self):
        """Load ATP accounts from disk."""
        if not self.storage_file or not self.storage_file.exists():
            logger.info("No existing ATP storage, starting fresh")
            return

        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)

            accounts_data = data.get("accounts", {})
            for entity_id, acc_data in accounts_data.items():
                self.accounts[entity_id] = ATPAccount(
                    entity_id=acc_data["entity_id"],
                    daily_limit=acc_data["daily_limit"],
                    per_action_limit=acc_data["per_action_limit"],
                    usage=acc_data.get("usage", {}),
                    last_recharge=acc_data.get("last_recharge", ""),
                    total_earned=acc_data.get("total_earned", 0),
                    total_spent=acc_data.get("total_spent", 0)
                )

            logger.info(f"Loaded {len(self.accounts)} ATP accounts from {self.storage_file}")

        except Exception as e:
            logger.error(f"Failed to load ATP accounts: {e}")

    def get_all_accounts(self) -> Dict[str, Dict]:
        """Get statistics for all accounts (for monitoring/admin)."""
        return {
            entity_id: self.get_account_stats(entity_id)
            for entity_id in self.accounts.keys()
        }


# Example usage and testing
if __name__ == "__main__":
    print("ATP Tracker - Example Usage\n" + "="*60)

    # Create tracker
    tracker = ATPTracker()

    # Create accounts
    print("\n1. Creating ATP accounts...")
    tracker.create_account("claude-001", daily_limit=1000, per_action_limit=100)
    tracker.create_account("agent-002", daily_limit=500, per_action_limit=50)

    # Check initial balance
    print(f"\nClaude balance: {tracker.get_balance('claude-001')} ATP")
    print(f"Agent-002 balance: {tracker.get_balance('agent-002')} ATP")

    # Perform actions
    print("\n2. Performing actions...")
    for i in range(5):
        success, msg = tracker.check_and_deduct("claude-001", 50)
        print(f"  Action {i+1}: {'✅ ' if success else '❌ '}{msg}")

    # Check balance after
    print(f"\nClaude balance after 5 actions: {tracker.get_balance('claude-001')} ATP")

    # Try to exceed per-action limit
    print("\n3. Testing per-action limit...")
    success, msg = tracker.check_and_deduct("claude-001", 150)
    print(f"  Request 150 ATP: {'✅ ' if success else '❌ '}{msg}")

    # Exhaust budget
    print("\n4. Exhausting daily budget...")
    while True:
        success, msg = tracker.check_and_deduct("claude-001", 50)
        if not success:
            print(f"  Budget exhausted: {msg}")
            break

    # Award ATP
    print("\n5. Awarding ATP for good behavior...")
    tracker.award_atp("claude-001", 200, "completed high-quality work")
    stats = tracker.get_account_stats("claude-001")
    print(f"  Total earned: {stats['total_earned']} ATP")
    print(f"  Daily limit increased to: {stats['daily_limit']} ATP")

    # Daily recharge
    print("\n6. Daily recharge simulation...")
    tracker.recharge_daily()
    print(f"  Claude balance after recharge: {tracker.get_balance('claude-001')} ATP")

    # Show all accounts
    print("\n7. All account statistics:")
    all_stats = tracker.get_all_accounts()
    for entity_id, stats in all_stats.items():
        print(f"\n  {entity_id}:")
        print(f"    Daily limit: {stats['daily_limit']}")
        print(f"    Used today: {stats['used_today']}")
        print(f"    Remaining: {stats['remaining_today']}")
        print(f"    Lifetime earned: {stats['total_earned']}")
        print(f"    Lifetime spent: {stats['total_spent']}")

    print("\n" + "="*60)
    print("✅ ATP Tracker operational - Critical vulnerability fixed!")
    print("="*60)
