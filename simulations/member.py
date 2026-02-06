# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - Member (Citizen) Implementation
# https://github.com/dp-web4/web4

"""
Member: An entity participating in a team.

Members are entities (humans, AI agents, sub-teams) with:
- LCT identity in team context
- Role assignment
- ATP budget
- Trust/reputation tracking
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict


class MemberRole(Enum):
    """Standard roles for team members."""
    ADMIN = "admin"         # Full governance authority
    REVIEWER = "reviewer"   # Can approve code/content
    DEPLOYER = "deployer"   # Can deploy to environments
    DEVELOPER = "developer" # Can submit code changes
    MEMBER = "member"       # Basic member access
    OBSERVER = "observer"   # Read-only access


@dataclass
class MemberTrust:
    """Trust tensor for a member in team context."""
    competence: float = 0.5   # Skill level demonstrated
    reliability: float = 0.5  # Consistency of performance
    alignment: float = 0.5    # Alignment with team goals

    def score(self) -> float:
        """Compute aggregate trust score."""
        return (self.competence * 0.4 +
                self.reliability * 0.4 +
                self.alignment * 0.2)

    def to_dict(self) -> dict:
        return {
            "competence": self.competence,
            "reliability": self.reliability,
            "alignment": self.alignment,
            "score": self.score()
        }


@dataclass
class Member:
    """
    A team member with identity and state.

    Note: This is a data class for member info.
    Actual member management is via Team methods.
    """
    lct_id: str
    team_id: str
    role: MemberRole = MemberRole.MEMBER
    atp_budget: int = 100
    atp_consumed: int = 0
    trust: MemberTrust = field(default_factory=MemberTrust)
    joined_at: str = ""
    action_count: int = 0
    metadata: Dict = field(default_factory=dict)

    @property
    def atp_remaining(self) -> int:
        """Remaining ATP budget."""
        return self.atp_budget - self.atp_consumed

    @property
    def trust_score(self) -> float:
        """Aggregate trust score."""
        return self.trust.score()

    def can_perform_action(self, required_trust: float = 0.5,
                          atp_cost: int = 1) -> tuple:
        """
        Check if member can perform an action.

        Returns:
            (can_perform: bool, reason: str)
        """
        if self.atp_remaining < atp_cost:
            return (False, f"Insufficient ATP: need {atp_cost}, have {self.atp_remaining}")

        if self.trust_score < required_trust:
            return (False, f"Insufficient trust: need {required_trust}, have {self.trust_score:.2f}")

        return (True, "OK")

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "lct_id": self.lct_id,
            "team_id": self.team_id,
            "role": self.role.value,
            "atp_budget": self.atp_budget,
            "atp_consumed": self.atp_consumed,
            "atp_remaining": self.atp_remaining,
            "trust": self.trust.to_dict(),
            "joined_at": self.joined_at,
            "action_count": self.action_count
        }

    @classmethod
    def from_dict(cls, data: dict, team_id: str) -> 'Member':
        """Create from dictionary."""
        trust_data = data.get("trust", {})
        trust = MemberTrust(
            competence=trust_data.get("competence", 0.5),
            reliability=trust_data.get("reliability", 0.5),
            alignment=trust_data.get("alignment", 0.5)
        )

        role = MemberRole(data.get("role", "member"))

        return cls(
            lct_id=data["lct_id"],
            team_id=team_id,
            role=role,
            atp_budget=data.get("atp_budget", 100),
            atp_consumed=data.get("atp_consumed", 0),
            trust=trust,
            joined_at=data.get("joined_at", ""),
            action_count=data.get("action_count", 0),
            metadata=data.get("metadata", {})
        )
