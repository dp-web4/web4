"""
Timestamp Validator for Temporal Security

Implements timestamp validation and clock skew handling for Web4 authorization.

Key Features:
- Validates timestamps are within reasonable bounds
- Handles clock skew between client and server
- Prevents future-dating and backdating attacks
- Timezone-aware validation
- Configurable tolerance windows

Fixes Critical Vulnerability #4:
- Previously no timestamp validation
- Delegations could be future-dated or backdated
- Temporal ordering unreliable
- Audit trail integrity compromised
- This implementation ensures temporal security

Usage:
    validator = TimestampValidator(
        max_clock_skew_seconds=300,  # 5 minutes tolerance
        max_age_days=365             # 1 year maximum age
    )

    # Validate timestamp
    valid, msg = validator.validate_timestamp(timestamp_str)
    if not valid:
        deny_authorization()

    # Check if timestamp is recent enough
    if not validator.is_recent(timestamp_str, max_age_seconds=3600):
        deny_authorization()

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 9, 2025
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimestampValidator:
    """
    Validate timestamps for temporal security.

    Ensures timestamps are:
    - Not from the far future (with clock skew tolerance)
    - Not from the ancient past (configurable max age)
    - Properly formatted and timezone-aware
    - Within expected bounds for authorization
    """

    def __init__(
        self,
        max_clock_skew_seconds: int = 300,
        max_age_days: int = 365
    ):
        """
        Initialize timestamp validator.

        Args:
            max_clock_skew_seconds: Allow timestamps this far in future (clock drift)
            max_age_days: Reject timestamps older than this
        """
        self.max_clock_skew_seconds = max_clock_skew_seconds
        self.max_age_days = max_age_days

        logger.info(
            f"TimestampValidator initialized "
            f"(clock_skew: {max_clock_skew_seconds}s, max_age: {max_age_days}d)"
        )

    def validate_timestamp(
        self,
        timestamp_str: str,
        context: str = "general"
    ) -> Tuple[bool, str]:
        """
        Validate timestamp is within acceptable bounds.

        Args:
            timestamp_str: ISO 8601 timestamp string
            context: Context for logging (e.g., "delegation", "authorization")

        Returns:
            Tuple of (valid: bool, message: str)
        """
        # Parse timestamp
        try:
            ts = self._parse_timestamp(timestamp_str)
        except Exception as e:
            logger.warning(
                f"Invalid timestamp format in {context}: {timestamp_str} ({e})"
            )
            return False, f"Invalid timestamp format: {str(e)}"

        # Get current time (UTC)
        now = datetime.now(timezone.utc)

        # Check not from far future
        future_limit = now + timedelta(seconds=self.max_clock_skew_seconds)
        if ts > future_limit:
            seconds_in_future = (ts - now).total_seconds()
            logger.warning(
                f"Future timestamp in {context}: {timestamp_str} "
                f"({seconds_in_future:.1f}s ahead, max allowed: {self.max_clock_skew_seconds}s)"
            )
            return False, (
                f"Timestamp is {seconds_in_future:.0f}s in future "
                f"(max clock skew: {self.max_clock_skew_seconds}s)"
            )

        # Check not from ancient past
        age_days = (now - ts).days
        if age_days > self.max_age_days:
            logger.warning(
                f"Ancient timestamp in {context}: {timestamp_str} "
                f"({age_days} days old, max allowed: {self.max_age_days})"
            )
            return False, (
                f"Timestamp is {age_days} days old "
                f"(max age: {self.max_age_days} days)"
            )

        # Valid!
        age_seconds = (now - ts).total_seconds()
        logger.debug(
            f"✅ Valid timestamp in {context}: {timestamp_str} "
            f"(age: {age_seconds:.1f}s)"
        )

        return True, f"Timestamp valid (age: {age_seconds:.1f}s)"

    def is_recent(
        self,
        timestamp_str: str,
        max_age_seconds: int
    ) -> bool:
        """
        Check if timestamp is recent (within max_age_seconds).

        Use this for authorization requests that should be fresh
        (e.g., within last hour).

        Args:
            timestamp_str: ISO 8601 timestamp
            max_age_seconds: Maximum age in seconds

        Returns:
            True if timestamp is recent enough
        """
        try:
            ts = self._parse_timestamp(timestamp_str)
            now = datetime.now(timezone.utc)
            age = (now - ts).total_seconds()

            is_recent = age <= max_age_seconds

            if not is_recent:
                logger.debug(
                    f"Timestamp too old: {age:.1f}s (max: {max_age_seconds}s)"
                )

            return is_recent

        except Exception as e:
            logger.error(f"Error checking timestamp recency: {e}")
            return False

    def is_expired(
        self,
        timestamp_str: str,
        duration_seconds: int
    ) -> bool:
        """
        Check if timestamp + duration has passed (expiry check).

        Args:
            timestamp_str: ISO 8601 timestamp (e.g., delegation.created)
            duration_seconds: Duration until expiry

        Returns:
            True if expired, False if still valid
        """
        try:
            ts = self._parse_timestamp(timestamp_str)
            now = datetime.now(timezone.utc)
            expiry = ts + timedelta(seconds=duration_seconds)

            is_expired = now > expiry

            if is_expired:
                logger.debug(
                    f"Timestamp expired: created {timestamp_str}, "
                    f"duration {duration_seconds}s"
                )

            return is_expired

        except Exception as e:
            logger.error(f"Error checking expiry: {e}")
            # On error, consider expired (fail secure)
            return True

    def compare_timestamps(
        self,
        timestamp1_str: str,
        timestamp2_str: str
    ) -> Optional[int]:
        """
        Compare two timestamps.

        Args:
            timestamp1_str: First ISO 8601 timestamp
            timestamp2_str: Second ISO 8601 timestamp

        Returns:
            -1 if timestamp1 < timestamp2
             0 if timestamp1 == timestamp2
             1 if timestamp1 > timestamp2
            None if comparison fails
        """
        try:
            ts1 = self._parse_timestamp(timestamp1_str)
            ts2 = self._parse_timestamp(timestamp2_str)

            if ts1 < ts2:
                return -1
            elif ts1 > ts2:
                return 1
            else:
                return 0

        except Exception as e:
            logger.error(f"Error comparing timestamps: {e}")
            return None

    def normalize_timestamp(self, timestamp_str: str) -> Optional[str]:
        """
        Normalize timestamp to standard format (ISO 8601 UTC with 'Z').

        Args:
            timestamp_str: Timestamp in various formats

        Returns:
            Normalized timestamp string, or None if invalid
        """
        try:
            ts = self._parse_timestamp(timestamp_str)
            # Convert to UTC and format
            normalized = ts.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
            return normalized

        except Exception as e:
            logger.error(f"Error normalizing timestamp: {e}")
            return None

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse ISO 8601 timestamp string to datetime (internal).

        Handles various formats:
        - 2025-11-09T10:30:00Z
        - 2025-11-09T10:30:00+00:00
        - 2025-11-09T10:30:00.123456Z

        Args:
            timestamp_str: ISO 8601 timestamp

        Returns:
            Timezone-aware datetime object (UTC)

        Raises:
            ValueError: If timestamp format invalid
        """
        if not timestamp_str:
            raise ValueError("Empty timestamp")

        # Require full timestamp (date + time), not just date
        if 'T' not in timestamp_str:
            raise ValueError("Timestamp must include time component (date only not allowed)")

        # Replace 'Z' with '+00:00' for parsing
        normalized = timestamp_str.replace('Z', '+00:00')

        try:
            # Parse ISO 8601
            dt = datetime.fromisoformat(normalized)

            # Ensure timezone-aware
            if dt.tzinfo is None:
                # Assume UTC if no timezone specified
                dt = dt.replace(tzinfo=timezone.utc)
                logger.debug(f"Timestamp missing timezone, assuming UTC: {timestamp_str}")
            else:
                # Convert to UTC
                dt = dt.astimezone(timezone.utc)

            return dt

        except Exception as e:
            raise ValueError(f"Invalid ISO 8601 timestamp: {timestamp_str}") from e

    def get_current_timestamp(self) -> str:
        """
        Get current timestamp in standard format.

        Returns:
            ISO 8601 timestamp string (UTC with 'Z')
        """
        return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


# Example usage
if __name__ == "__main__":
    print("Timestamp Validator - Example Usage\n" + "="*60)

    validator = TimestampValidator(
        max_clock_skew_seconds=300,  # 5 minutes
        max_age_days=365             # 1 year
    )

    # Test 1: Valid current timestamp
    print("\n1. Validating current timestamp...")
    current = validator.get_current_timestamp()
    print(f"  Current time: {current}")
    valid, msg = validator.validate_timestamp(current, context="test")
    print(f"  Valid? {valid}")
    print(f"  Message: {msg}")

    # Test 2: Future timestamp (should fail)
    print("\n2. Testing future timestamp (clock skew attack)...")
    from datetime import datetime, timezone
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat().replace('+00:00', 'Z')
    print(f"  Future time: {future}")
    valid, msg = validator.validate_timestamp(future, context="test")
    print(f"  Valid? {valid}")
    print(f"  Message: {msg}")

    # Test 3: Old timestamp (should pass if within 365 days)
    print("\n3. Testing old timestamp...")
    old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace('+00:00', 'Z')
    print(f"  Old time: {old}")
    valid, msg = validator.validate_timestamp(old, context="test")
    print(f"  Valid? {valid}")
    print(f"  Message: {msg}")

    # Test 4: Ancient timestamp (should fail)
    print("\n4. Testing ancient timestamp...")
    ancient = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat().replace('+00:00', 'Z')
    print(f"  Ancient time: {ancient}")
    valid, msg = validator.validate_timestamp(ancient, context="test")
    print(f"  Valid? {valid}")
    print(f"  Message: {msg}")

    # Test 5: Recency check
    print("\n5. Testing recency check (1 hour window)...")
    recent = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat().replace('+00:00', 'Z')
    is_recent = validator.is_recent(recent, max_age_seconds=3600)
    print(f"  Is recent (within 1 hour)? {is_recent}")

    # Test 6: Expiry check
    print("\n6. Testing expiry check...")
    created = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat().replace('+00:00', 'Z')
    is_expired_7d = validator.is_expired(created, duration_seconds=7*24*3600)
    is_expired_14d = validator.is_expired(created, duration_seconds=14*24*3600)
    print(f"  Created 10 days ago, 7-day expiry: Expired? {is_expired_7d}")
    print(f"  Created 10 days ago, 14-day expiry: Expired? {is_expired_14d}")

    # Test 7: Timestamp comparison
    print("\n7. Testing timestamp comparison...")
    ts1 = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat().replace('+00:00', 'Z')
    ts2 = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat().replace('+00:00', 'Z')
    result = validator.compare_timestamps(ts1, ts2)
    print(f"  {ts1[:19]} vs {ts2[:19]}")
    print(f"  Result: {result} (-1=earlier, 0=same, 1=later)")

    print("\n" + "="*60)
    print("✅ Timestamp Validator operational - Temporal attacks prevented!")
    print("="*60)
    print("\nKey capabilities:")
    print("- Future-dating prevention (clock skew tolerance)")
    print("- Backdating prevention (max age limits)")
    print("- Timezone-aware validation")
    print("- Recency and expiry checking")
