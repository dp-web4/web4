# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - Rate Limiting Infrastructure
# https://github.com/dp-web4/web4

"""
Rate Limiter: Prevent resource exhaustion and abuse.

Rate limiting protects against:
1. Request flooding (too many requests/second)
2. LCT creation abuse (Sybil attacks)
3. ATP drain attacks (rapid budget consumption)
4. Audit trail flooding

Uses token bucket algorithm with per-LCT and per-action limits.
"""

import sqlite3
import time
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Optional, Dict, List, TYPE_CHECKING
from enum import Enum
from pathlib import Path

if TYPE_CHECKING:
    from .ledger import Ledger


class RateLimitScope(Enum):
    """Scope of rate limiting."""
    GLOBAL = "global"      # Team-wide limit
    PER_LCT = "per_lct"    # Per-member limit
    PER_ACTION = "per_action"  # Per-action-type limit


@dataclass
class RateLimitRule:
    """A rate limit rule."""
    name: str
    scope: RateLimitScope
    max_requests: int      # Maximum requests in window
    window_seconds: int    # Time window size
    burst_allowance: int = 0  # Extra requests allowed in burst
    cooldown_seconds: int = 0  # Cooldown after hitting limit

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "scope": self.scope.value,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "burst_allowance": self.burst_allowance,
            "cooldown_seconds": self.cooldown_seconds
        }


# Default rate limit rules
DEFAULT_RULES = {
    # Request rate limits
    "r6_requests": RateLimitRule(
        name="r6_requests",
        scope=RateLimitScope.PER_LCT,
        max_requests=60,     # 60 requests per minute
        window_seconds=60,
        burst_allowance=10   # Allow 10 extra in burst
    ),
    "global_requests": RateLimitRule(
        name="global_requests",
        scope=RateLimitScope.GLOBAL,
        max_requests=1000,   # 1000 team-wide per minute
        window_seconds=60,
        burst_allowance=100
    ),

    # LCT creation limits (anti-Sybil)
    "lct_creation": RateLimitRule(
        name="lct_creation",
        scope=RateLimitScope.GLOBAL,
        max_requests=10,     # 10 new LCTs per hour
        window_seconds=3600,
        burst_allowance=2,
        cooldown_seconds=60  # 1 minute cooldown after limit
    ),

    # Audit entry limits (anti-flooding)
    "audit_entries": RateLimitRule(
        name="audit_entries",
        scope=RateLimitScope.PER_LCT,
        max_requests=100,    # 100 audit entries per minute per member
        window_seconds=60,
        burst_allowance=20
    ),

    # Proposal limits
    "proposals": RateLimitRule(
        name="proposals",
        scope=RateLimitScope.PER_LCT,
        max_requests=5,      # 5 proposals per hour
        window_seconds=3600,
        burst_allowance=1
    ),

    # ATP operations
    "atp_operations": RateLimitRule(
        name="atp_operations",
        scope=RateLimitScope.PER_LCT,
        max_requests=30,     # 30 ATP operations per minute
        window_seconds=60,
        burst_allowance=5
    ),

    # Authentication attempts
    "auth_attempts": RateLimitRule(
        name="auth_attempts",
        scope=RateLimitScope.PER_LCT,
        max_requests=5,      # 5 failed auth attempts
        window_seconds=300,  # 5 minute window
        burst_allowance=0,
        cooldown_seconds=300  # 5 minute lockout
    ),
}


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int         # Remaining requests in window
    reset_seconds: int     # Seconds until window reset
    retry_after: int = 0   # Seconds to wait if blocked
    rule_name: str = ""
    reason: str = ""


class TokenBucket:
    """
    Token bucket for rate limiting.

    Each bucket has:
    - tokens: Current available tokens
    - last_update: Last time tokens were added
    - max_tokens: Maximum tokens (capacity)
    - refill_rate: Tokens added per second
    """

    def __init__(self, max_tokens: int, refill_rate: float):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = float(max_tokens)
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Returns:
            True if tokens consumed, False if insufficient
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.max_tokens,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_update = now

    @property
    def available(self) -> int:
        """Get available tokens."""
        self._refill()
        return int(self.tokens)


class RateLimiter:
    """
    Rate limiting with token bucket algorithm.

    Provides multiple limiting strategies:
    - Fixed window: Simple count per time window
    - Sliding window: More accurate rate over time
    - Token bucket: Allows bursts with steady refill
    """

    def __init__(self, ledger: 'Ledger', rules: Optional[Dict[str, RateLimitRule]] = None):
        """
        Initialize rate limiter.

        Args:
            ledger: Ledger for persistence
            rules: Custom rules (uses defaults if None)
        """
        self.ledger = ledger
        self.rules = rules or DEFAULT_RULES.copy()
        self._buckets: Dict[str, TokenBucket] = {}
        self._cooldowns: Dict[str, float] = {}  # key -> cooldown_end_time
        self._ensure_table()

    def _ensure_table(self):
        """Create rate limit tracking table."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    key TEXT PRIMARY KEY,
                    rule_name TEXT NOT NULL,
                    request_count INTEGER NOT NULL,
                    window_start TEXT NOT NULL,
                    cooldown_until TEXT
                )
            """)

    def _get_bucket_key(self, rule_name: str, lct_id: Optional[str] = None,
                        action: Optional[str] = None) -> str:
        """Generate bucket key based on scope."""
        rule = self.rules.get(rule_name)
        if not rule:
            return f"unknown:{rule_name}"

        if rule.scope == RateLimitScope.GLOBAL:
            return f"global:{rule_name}"
        elif rule.scope == RateLimitScope.PER_LCT:
            return f"lct:{lct_id or 'unknown'}:{rule_name}"
        elif rule.scope == RateLimitScope.PER_ACTION:
            return f"action:{action or 'unknown'}:{rule_name}"
        return f"unknown:{rule_name}"

    def _get_bucket(self, key: str, rule: RateLimitRule) -> TokenBucket:
        """Get or create token bucket for key."""
        if key not in self._buckets:
            max_tokens = rule.max_requests + rule.burst_allowance
            refill_rate = rule.max_requests / rule.window_seconds
            self._buckets[key] = TokenBucket(max_tokens, refill_rate)
        return self._buckets[key]

    def check(
        self,
        rule_name: str,
        lct_id: Optional[str] = None,
        action: Optional[str] = None,
        consume: bool = True
    ) -> RateLimitResult:
        """
        Check rate limit and optionally consume a token.

        Args:
            rule_name: Name of the rule to check
            lct_id: LCT ID for per-LCT rules
            action: Action type for per-action rules
            consume: If True, consume a token on success

        Returns:
            RateLimitResult with allowed status and details
        """
        rule = self.rules.get(rule_name)
        if not rule:
            return RateLimitResult(
                allowed=True,
                remaining=999,
                reset_seconds=0,
                rule_name=rule_name,
                reason="Unknown rule - allowing"
            )

        key = self._get_bucket_key(rule_name, lct_id, action)

        # Check cooldown
        if key in self._cooldowns:
            cooldown_end = self._cooldowns[key]
            if time.time() < cooldown_end:
                retry_after = int(cooldown_end - time.time())
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_seconds=retry_after,
                    retry_after=retry_after,
                    rule_name=rule_name,
                    reason=f"In cooldown for {retry_after} seconds"
                )
            else:
                del self._cooldowns[key]

        bucket = self._get_bucket(key, rule)

        if consume:
            if bucket.consume(1):
                return RateLimitResult(
                    allowed=True,
                    remaining=bucket.available,
                    reset_seconds=int(rule.window_seconds * (1 - bucket.tokens / bucket.max_tokens)),
                    rule_name=rule_name,
                    reason="OK"
                )
            else:
                # Apply cooldown if configured
                if rule.cooldown_seconds > 0:
                    self._cooldowns[key] = time.time() + rule.cooldown_seconds

                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_seconds=int(1 / bucket.refill_rate),  # Time for 1 token
                    retry_after=int(1 / bucket.refill_rate) + rule.cooldown_seconds,
                    rule_name=rule_name,
                    reason="Rate limit exceeded"
                )
        else:
            # Just checking, don't consume
            return RateLimitResult(
                allowed=bucket.available > 0,
                remaining=bucket.available,
                reset_seconds=int(rule.window_seconds * (1 - bucket.tokens / bucket.max_tokens)),
                rule_name=rule_name,
                reason="OK" if bucket.available > 0 else "Would exceed limit"
            )

    def get_status(self, rule_name: str, lct_id: Optional[str] = None,
                   action: Optional[str] = None) -> dict:
        """
        Get current rate limit status without consuming.

        Returns:
            Status dict with current limits and usage
        """
        result = self.check(rule_name, lct_id, action, consume=False)
        rule = self.rules.get(rule_name)

        return {
            "rule": rule.to_dict() if rule else None,
            "remaining": result.remaining,
            "max": rule.max_requests + rule.burst_allowance if rule else 0,
            "reset_seconds": result.reset_seconds,
            "in_cooldown": result.retry_after > 0,
            "allowed": result.allowed
        }

    def add_rule(self, rule: RateLimitRule):
        """Add or update a rate limit rule."""
        self.rules[rule.name] = rule

    def reset(self, rule_name: str, lct_id: Optional[str] = None,
              action: Optional[str] = None):
        """Reset rate limit for a specific key (admin action)."""
        key = self._get_bucket_key(rule_name, lct_id, action)
        if key in self._buckets:
            del self._buckets[key]
        if key in self._cooldowns:
            del self._cooldowns[key]


class RateLimitedTeam:
    """
    Mixin for adding rate limiting to Team operations.

    Usage:
        class Team(RateLimitedTeam):
            def __init__(self, ...):
                self._rate_limiter = RateLimiter(self.ledger)

            def add_member(self, lct_id, ...):
                self._check_rate_limit("lct_creation", lct_id)
                # ... actual implementation
    """

    _rate_limiter: RateLimiter

    def _check_rate_limit(
        self,
        rule_name: str,
        lct_id: Optional[str] = None,
        action: Optional[str] = None,
        auto_raise: bool = True
    ) -> RateLimitResult:
        """
        Check rate limit before operation.

        Args:
            rule_name: Rule to check
            lct_id: LCT for per-LCT rules
            action: Action for per-action rules
            auto_raise: If True, raise exception on limit

        Returns:
            RateLimitResult

        Raises:
            RateLimitExceeded: If limit exceeded and auto_raise=True
        """
        result = self._rate_limiter.check(rule_name, lct_id, action)

        if not result.allowed and auto_raise:
            raise RateLimitExceeded(
                f"Rate limit exceeded for {rule_name}: {result.reason}. "
                f"Retry after {result.retry_after} seconds."
            )

        return result


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


if __name__ == "__main__":
    print("=" * 60)
    print("Rate Limiter - Default Rules")
    print("=" * 60)

    for name, rule in DEFAULT_RULES.items():
        print(f"\n{name}:")
        print(f"  Scope: {rule.scope.value}")
        print(f"  Limit: {rule.max_requests}/{rule.window_seconds}s")
        print(f"  Burst: +{rule.burst_allowance}")
        if rule.cooldown_seconds:
            print(f"  Cooldown: {rule.cooldown_seconds}s")

    print("\n" + "=" * 60)
    print("Token Bucket Demo")
    print("=" * 60)

    # Demo token bucket
    bucket = TokenBucket(max_tokens=5, refill_rate=1.0)  # 1 token/second
    print(f"\nBucket: 5 tokens max, 1 token/second refill")
    print(f"Initial tokens: {bucket.available}")

    # Consume some
    for i in range(7):
        result = bucket.consume(1)
        print(f"Consume #{i+1}: {'OK' if result else 'FAILED'}, remaining={bucket.available}")

    # Wait a bit
    print("\nWaiting 3 seconds...")
    time.sleep(3)
    print(f"After 3s: {bucket.available} tokens")
