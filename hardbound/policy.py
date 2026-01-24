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
"""

import json
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any
from enum import Enum


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

    def __init__(self, rules: Optional[List[PolicyRule]] = None):
        """
        Initialize policy with rules.

        Args:
            rules: List of policy rules. Uses defaults if None.
        """
        self.rules: Dict[str, PolicyRule] = {}
        self.created_at = datetime.now(timezone.utc).isoformat() + "Z"
        self.version = 1

        # Load rules
        rule_list = rules if rules is not None else self.DEFAULT_RULES
        for rule in rule_list:
            self.rules[rule.action_type] = rule

    def get_rule(self, action_type: str) -> Optional[PolicyRule]:
        """Get rule for an action type."""
        return self.rules.get(action_type)

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
        policy = cls(rules=rules)
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
