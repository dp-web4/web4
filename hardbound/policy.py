# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - Policy (Law) Implementation
# https://github.com/dp-web4/web4

"""
Policy: Rules governing team behavior.

Policy is recorded in the ledger and enforced by the admin.
It defines:
- Action permissions by role
- Trust thresholds for actions
- ATP costs for actions
- Approval requirements

Persistence model:
- Policy stored as JSON in ledger database
- Hash-chain versioning for tamper detection
- All changes recorded in audit trail
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, List, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from governance import Ledger


class ApprovalType(Enum):
    """Types of approval for actions."""
    NONE = "none"              # No approval needed
    ADMIN = "admin"            # Admin must approve
    PEER = "peer"              # Peer review needed
    MULTI_SIG = "multi_sig"    # Multiple approvals needed


@dataclass
class PolicyRule:
    """A single policy rule."""
    action_type: str           # Type of action this rule applies to
    allowed_roles: List[str]   # Roles that can perform this action
    trust_threshold: float = 0.5    # Minimum trust required
    atp_cost: int = 1          # ATP cost for this action
    approval: ApprovalType = ApprovalType.NONE
    approval_count: int = 1    # Number of approvals for MULTI_SIG
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "allowed_roles": self.allowed_roles,
            "trust_threshold": self.trust_threshold,
            "atp_cost": self.atp_cost,
            "approval": self.approval.value,
            "approval_count": self.approval_count,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PolicyRule':
        return cls(
            action_type=data["action_type"],
            allowed_roles=data["allowed_roles"],
            trust_threshold=data.get("trust_threshold", 0.5),
            atp_cost=data.get("atp_cost", 1),
            approval=ApprovalType(data.get("approval", "none")),
            approval_count=data.get("approval_count", 1),
            description=data.get("description", "")
        )


class Policy:
    """
    Team policy - rules governing behavior.

    Policy is the "law" of the team, stored in ledger and
    enforced by admin during R6 workflow.
    """

    # Global policy constraints
    DEFAULT_MIN_EXPIRY_HOURS = 24  # Minimum 1 day expiry for any R6 request
    DEFAULT_MAX_EXPIRY_HOURS = 24 * 30  # Maximum 30 days

    # Default rules if none specified
    DEFAULT_RULES = [
        PolicyRule(
            action_type="read",
            allowed_roles=["admin", "developer", "reviewer", "member", "observer"],
            trust_threshold=0.0,
            atp_cost=0,
            description="Read access - available to all"
        ),
        PolicyRule(
            action_type="write",
            allowed_roles=["admin", "developer"],
            trust_threshold=0.5,
            atp_cost=1,
            description="Write access - developers and above"
        ),
        PolicyRule(
            action_type="commit",
            allowed_roles=["admin", "developer"],
            trust_threshold=0.5,
            atp_cost=2,
            approval=ApprovalType.PEER,
            description="Commit code - requires peer review"
        ),
        PolicyRule(
            action_type="deploy",
            allowed_roles=["admin", "deployer"],
            trust_threshold=0.7,
            atp_cost=5,
            approval=ApprovalType.ADMIN,
            description="Deploy to environment - admin approval required"
        ),
        PolicyRule(
            action_type="admin_action",
            allowed_roles=["admin"],
            trust_threshold=0.8,
            atp_cost=10,
            description="Administrative actions - admin only"
        ),
    ]

    def __init__(self, rules: Optional[List[PolicyRule]] = None,
                 min_expiry_hours: int = None,
                 max_expiry_hours: int = None):
        """
        Initialize policy with rules.

        Args:
            rules: List of policy rules. Uses defaults if None.
            min_expiry_hours: Minimum R6 request expiry time (enforced)
            max_expiry_hours: Maximum R6 request expiry time (enforced)
        """
        self.rules: Dict[str, PolicyRule] = {}
        self.created_at = datetime.now(timezone.utc).isoformat() + "Z"
        self.version = 1

        # Expiry constraints
        self.min_expiry_hours = (min_expiry_hours if min_expiry_hours is not None
                                  else self.DEFAULT_MIN_EXPIRY_HOURS)
        self.max_expiry_hours = (max_expiry_hours if max_expiry_hours is not None
                                  else self.DEFAULT_MAX_EXPIRY_HOURS)

        # Load rules
        rule_list = rules if rules is not None else self.DEFAULT_RULES
        for rule in rule_list:
            self.rules[rule.action_type] = rule

    def get_rule(self, action_type: str) -> Optional[PolicyRule]:
        """Get rule for an action type."""
        return self.rules.get(action_type)

    def validate_expiry_hours(self, expiry_hours: int) -> tuple:
        """
        Validate that requested expiry hours meets policy constraints.

        Args:
            expiry_hours: Requested expiry duration in hours

        Returns:
            (valid: bool, error: Optional[str], enforced_hours: int)
            If valid=False, error explains why
            enforced_hours is the value to use (clamped to bounds)
        """
        # Zero expiry (no expiry) is only allowed if min_expiry_hours is 0
        if expiry_hours <= 0:
            if self.min_expiry_hours == 0:
                # Policy explicitly allows zero/infinite expiry
                return (True, None, 0)
            return (False,
                    f"Expiry must be positive. Policy minimum: {self.min_expiry_hours}h",
                    self.min_expiry_hours)

        if expiry_hours < self.min_expiry_hours:
            return (False,
                    f"Expiry {expiry_hours}h below policy minimum {self.min_expiry_hours}h",
                    self.min_expiry_hours)

        if expiry_hours > self.max_expiry_hours:
            return (False,
                    f"Expiry {expiry_hours}h exceeds policy maximum {self.max_expiry_hours}h",
                    self.max_expiry_hours)

        return (True, None, expiry_hours)

    def check_permission(self, action_type: str, role: str,
                        trust_score: float, atp_available: int) -> tuple:
        """
        Check if an action is permitted.

        Args:
            action_type: Type of action
            role: Member's role
            trust_score: Member's trust score
            atp_available: Member's available ATP

        Returns:
            (permitted: bool, reason: str, rule: Optional[PolicyRule])
        """
        rule = self.get_rule(action_type)

        if rule is None:
            # No rule = denied by default
            return (False, f"No policy rule for action: {action_type}", None)

        # Check role
        if role not in rule.allowed_roles:
            return (False, f"Role '{role}' not permitted for '{action_type}'", rule)

        # Check trust
        if trust_score < rule.trust_threshold:
            return (False,
                   f"Insufficient trust: {trust_score:.2f} < {rule.trust_threshold}",
                   rule)

        # Check ATP
        if atp_available < rule.atp_cost:
            return (False,
                   f"Insufficient ATP: {atp_available} < {rule.atp_cost}",
                   rule)

        return (True, "OK", rule)

    def add_rule(self, rule: PolicyRule):
        """Add or update a rule."""
        self.rules[rule.action_type] = rule
        self.version += 1

    def remove_rule(self, action_type: str) -> bool:
        """Remove a rule."""
        if action_type in self.rules:
            del self.rules[action_type]
            self.version += 1
            return True
        return False

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "version": self.version,
            "created_at": self.created_at,
            "min_expiry_hours": self.min_expiry_hours,
            "max_expiry_hours": self.max_expiry_hours,
            "rules": {
                k: v.to_dict() for k, v in self.rules.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Policy':
        """Create from dictionary."""
        rules = [
            PolicyRule.from_dict(r) for r in data.get("rules", {}).values()
        ]
        policy = cls(
            rules=rules,
            min_expiry_hours=data.get("min_expiry_hours"),
            max_expiry_hours=data.get("max_expiry_hours"),
        )
        policy.version = data.get("version", 1)
        policy.created_at = data.get("created_at", policy.created_at)
        return policy

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'Policy':
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def summary(self) -> dict:
        """Get policy summary."""
        return {
            "version": self.version,
            "rule_count": len(self.rules),
            "action_types": list(self.rules.keys())
        }

    def compute_hash(self) -> str:
        """Compute hash of policy for integrity verification."""
        # Deterministic serialization
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class PolicyStore:
    """
    Persists policy to ledger database with hash-chain versioning.

    Each policy version is stored with:
    - Content hash for integrity
    - Previous version hash for chain
    - Change description
    - Timestamp
    """

    def __init__(self, ledger: 'Ledger'):
        """
        Initialize policy store.

        Args:
            ledger: Ledger instance for persistence
        """
        self.ledger = ledger
        self._ensure_table()

    def _ensure_table(self):
        """Create policy table if not exists."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS policies (
                    policy_id TEXT PRIMARY KEY,
                    team_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    prev_hash TEXT,
                    change_description TEXT,
                    changed_by TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(team_id, version)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_policies_team
                ON policies(team_id, version DESC)
            """)

    def save(self, team_id: str, policy: Policy, changed_by: str,
             description: str = "") -> dict:
        """
        Save policy version to database.

        Args:
            team_id: Team this policy belongs to
            policy: Policy to save
            changed_by: LCT of who made the change
            description: Description of change

        Returns:
            Policy version record
        """
        now = datetime.now(timezone.utc)
        content = policy.to_json()
        content_hash = policy.compute_hash()

        # Get previous version hash
        prev_hash = None
        prev = self.get_latest(team_id)
        if prev:
            prev_hash = prev["content_hash"]
            policy.version = prev["version"] + 1

        # Generate policy ID
        seed = f"policy:{team_id}:{policy.version}:{now.isoformat()}"
        policy_id = f"policy:{hashlib.sha256(seed.encode()).hexdigest()[:12]}"

        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.execute("""
                INSERT INTO policies
                (policy_id, team_id, version, content, content_hash,
                 prev_hash, change_description, changed_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                policy_id, team_id, policy.version, content, content_hash,
                prev_hash, description, changed_by, now.isoformat()
            ))

        # Record in audit trail
        self.ledger.record_audit(
            session_id=team_id,
            action_type="policy_changed",
            tool_name="hardbound",
            target=policy_id,
            r6_data={
                "version": policy.version,
                "content_hash": content_hash,
                "prev_hash": prev_hash,
                "description": description,
                "rule_count": len(policy.rules)
            }
        )

        return {
            "policy_id": policy_id,
            "team_id": team_id,
            "version": policy.version,
            "content_hash": content_hash,
            "prev_hash": prev_hash,
            "created_at": now.isoformat()
        }

    def get_latest(self, team_id: str) -> Optional[dict]:
        """Get the latest policy version for a team."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM policies
                WHERE team_id = ?
                ORDER BY version DESC
                LIMIT 1
            """, (team_id,)).fetchone()

            return dict(row) if row else None

    def get_version(self, team_id: str, version: int) -> Optional[dict]:
        """Get a specific policy version."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM policies
                WHERE team_id = ? AND version = ?
            """, (team_id, version)).fetchone()

            return dict(row) if row else None

    def load(self, team_id: str, version: Optional[int] = None) -> Optional[Policy]:
        """
        Load policy from database.

        Args:
            team_id: Team ID
            version: Specific version, or None for latest

        Returns:
            Policy instance, or None if not found
        """
        if version is not None:
            record = self.get_version(team_id, version)
        else:
            record = self.get_latest(team_id)

        if not record:
            return None

        policy = Policy.from_json(record["content"])
        policy.version = record["version"]
        return policy

    def get_history(self, team_id: str) -> List[dict]:
        """Get policy version history for a team."""
        with sqlite3.connect(self.ledger.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT policy_id, version, content_hash, prev_hash,
                       change_description, changed_by, created_at
                FROM policies
                WHERE team_id = ?
                ORDER BY version DESC
            """, (team_id,)).fetchall()

            return [dict(row) for row in rows]

    def verify_chain(self, team_id: str) -> tuple:
        """
        Verify policy chain integrity.

        Returns:
            (valid: bool, error: Optional[str])
        """
        history = self.get_history(team_id)
        if not history:
            return (True, None)  # No policy = valid

        # Verify from newest to oldest
        expected_prev = None
        for i, record in enumerate(history):
            # Verify content hash
            record_full = self.get_version(team_id, record["version"])
            if record_full:
                policy = Policy.from_json(record_full["content"])
                computed_hash = policy.compute_hash()
                if computed_hash != record["content_hash"]:
                    return (False, f"Content hash mismatch at version {record['version']}")

            # Verify chain linkage
            if expected_prev is not None and record["content_hash"] != expected_prev:
                return (False, f"Chain break at version {record['version']}")

            expected_prev = record["prev_hash"]

        return (True, None)
