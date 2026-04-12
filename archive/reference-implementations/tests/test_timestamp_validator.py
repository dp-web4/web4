"""
Unit tests for Timestamp Validator

Tests the critical security fix: Timestamp validation
that was previously missing from the LCT identity system.

Author: Claude (Anthropic AI), autonomous security hardening
Date: November 9, 2025
"""

import pytest
from datetime import datetime, timedelta, timezone

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from timestamp_validator import TimestampValidator


class TestTimestampValidator:
    """Test TimestampValidator class."""

    def test_create_validator(self):
        """Test creating validator."""
        validator = TimestampValidator(
            max_clock_skew_seconds=300,
            max_age_days=365
        )

        assert validator.max_clock_skew_seconds == 300
        assert validator.max_age_days == 365

    def test_validate_current_timestamp(self):
        """Test validating current timestamp."""
        validator = TimestampValidator()

        current = validator.get_current_timestamp()
        valid, msg = validator.validate_timestamp(current)

        assert valid is True
        assert "valid" in msg.lower()

    def test_future_timestamp_rejected(self):
        """
        Critical security test: Prevent future-dating attacks.

        An attacker tries to create delegation with future timestamp
        to bypass temporal restrictions.
        """
        validator = TimestampValidator(max_clock_skew_seconds=300)

        # Create timestamp 1 hour in future
        future = (
            datetime.now(timezone.utc) + timedelta(hours=1)
        ).isoformat().replace('+00:00', 'Z')

        valid, msg = validator.validate_timestamp(future)

        # Should be REJECTED
        assert valid is False, "Future timestamp must be rejected"
        assert "future" in msg.lower()

    def test_clock_skew_tolerance(self):
        """Test that small clock skew is tolerated."""
        validator = TimestampValidator(max_clock_skew_seconds=300)

        # Create timestamp 2 minutes in future (within tolerance)
        near_future = (
            datetime.now(timezone.utc) + timedelta(minutes=2)
        ).isoformat().replace('+00:00', 'Z')

        valid, msg = validator.validate_timestamp(near_future)

        # Should be ACCEPTED (within clock skew)
        assert valid is True

    def test_ancient_timestamp_rejected(self):
        """
        Critical security test: Prevent backdating attacks.

        An attacker tries to use very old delegation to
        claim authorization existed historically.
        """
        validator = TimestampValidator(max_age_days=365)

        # Create timestamp 2 years old
        ancient = (
            datetime.now(timezone.utc) - timedelta(days=730)
        ).isoformat().replace('+00:00', 'Z')

        valid, msg = validator.validate_timestamp(ancient)

        # Should be REJECTED
        assert valid is False, "Ancient timestamp must be rejected"
        assert "old" in msg.lower() or "days" in msg.lower()

    def test_old_but_valid_timestamp(self):
        """Test that old but within-limit timestamps are valid."""
        validator = TimestampValidator(max_age_days=365)

        # Create timestamp 6 months old (within limit)
        old = (
            datetime.now(timezone.utc) - timedelta(days=180)
        ).isoformat().replace('+00:00', 'Z')

        valid, msg = validator.validate_timestamp(old)

        # Should be ACCEPTED
        assert valid is True

    def test_invalid_format_rejected(self):
        """Test that invalid timestamp formats are rejected."""
        validator = TimestampValidator()

        invalid_timestamps = [
            "not-a-timestamp",
            "2025-13-45",  # Invalid date
            "2025-11-09",  # Missing time
            "",             # Empty
            "12345",        # Not ISO format
        ]

        for invalid in invalid_timestamps:
            valid, msg = validator.validate_timestamp(invalid)
            assert valid is False, f"Invalid format should be rejected: {invalid}"

    def test_is_recent(self):
        """Test recency checking."""
        validator = TimestampValidator()

        # Create timestamp 30 minutes ago
        recent = (
            datetime.now(timezone.utc) - timedelta(minutes=30)
        ).isoformat().replace('+00:00', 'Z')

        # Should be recent within 1 hour
        assert validator.is_recent(recent, max_age_seconds=3600) is True

        # Should not be recent within 15 minutes
        assert validator.is_recent(recent, max_age_seconds=900) is False

    def test_is_expired(self):
        """Test expiry checking."""
        validator = TimestampValidator()

        # Create timestamp 10 days ago
        created = (
            datetime.now(timezone.utc) - timedelta(days=10)
        ).isoformat().replace('+00:00', 'Z')

        # Should be expired with 7-day duration
        assert validator.is_expired(created, duration_seconds=7*24*3600) is True

        # Should not be expired with 14-day duration
        assert validator.is_expired(created, duration_seconds=14*24*3600) is False

    def test_compare_timestamps(self):
        """Test timestamp comparison."""
        validator = TimestampValidator()

        ts1 = (
            datetime.now(timezone.utc) - timedelta(hours=2)
        ).isoformat().replace('+00:00', 'Z')

        ts2 = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).isoformat().replace('+00:00', 'Z')

        ts3 = ts1  # Same as ts1

        # ts1 < ts2
        assert validator.compare_timestamps(ts1, ts2) == -1

        # ts2 > ts1
        assert validator.compare_timestamps(ts2, ts1) == 1

        # ts1 == ts3
        assert validator.compare_timestamps(ts1, ts3) == 0

    def test_normalize_timestamp(self):
        """Test timestamp normalization."""
        validator = TimestampValidator()

        # Various formats that should normalize
        timestamps = [
            "2025-11-09T10:30:00Z",
            "2025-11-09T10:30:00+00:00",
            "2025-11-09T10:30:00.123456Z",
        ]

        for ts in timestamps:
            normalized = validator.normalize_timestamp(ts)
            assert normalized is not None
            assert normalized.endswith('Z')
            assert 'T' in normalized

    def test_timezone_handling(self):
        """Test that different timezones are handled correctly."""
        validator = TimestampValidator()

        # Create timestamp in different timezone (PST = UTC-8)
        pst_timestamp = "2025-11-09T10:30:00-08:00"

        # Should successfully validate (converted to UTC internally)
        valid, msg = validator.validate_timestamp(pst_timestamp)
        assert valid is True

    def test_microseconds_preserved(self):
        """Test that microseconds in timestamps are handled."""
        validator = TimestampValidator()

        # Timestamp with microseconds
        with_micro = "2025-11-09T10:30:00.123456Z"

        valid, msg = validator.validate_timestamp(with_micro)
        assert valid is True

    def test_get_current_timestamp_format(self):
        """Test current timestamp format."""
        validator = TimestampValidator()

        current = validator.get_current_timestamp()

        # Should be valid ISO 8601
        assert 'T' in current
        assert current.endswith('Z')

        # Should validate
        valid, _ = validator.validate_timestamp(current)
        assert valid is True

    def test_context_logging(self):
        """Test that context is used in validation."""
        validator = TimestampValidator()

        current = validator.get_current_timestamp()

        # Should work with different contexts
        valid1, _ = validator.validate_timestamp(current, context="delegation")
        valid2, _ = validator.validate_timestamp(current, context="authorization")

        assert valid1 is True
        assert valid2 is True

    def test_edge_case_exactly_at_limit(self):
        """Test timestamps exactly at the limit."""
        validator = TimestampValidator(
            max_clock_skew_seconds=300,
            max_age_days=365
        )

        # Exactly at clock skew limit
        at_skew_limit = (
            datetime.now(timezone.utc) + timedelta(seconds=300)
        ).isoformat().replace('+00:00', 'Z')

        valid, _ = validator.validate_timestamp(at_skew_limit)
        # Should be accepted (at or below limit)
        assert valid is True

        # Exactly at age limit
        at_age_limit = (
            datetime.now(timezone.utc) - timedelta(days=365)
        ).isoformat().replace('+00:00', 'Z')

        valid, _ = validator.validate_timestamp(at_age_limit)
        # Should be accepted (at or below limit)
        assert valid is True


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
