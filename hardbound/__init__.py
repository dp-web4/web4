# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Web4 Contributors
#
# Hardbound - Enterprise AI Governance
# https://github.com/dp-web4/web4

"""
Hardbound: Enterprise AI Governance

Implements Web4 "team/society" structure for enterprise AI deployments:
- Team identity (root LCT)
- Member management
- Policy enforcement
- R6 workflow for auditable actions
- ATP resource tracking
- Reputation accrual

Uses enterprise terminology:
- Team (not society)
- Ledger (not blockchain)
- Admin (not law oracle)
- Member (not citizen)
"""

from .team import Team, TeamConfig
from .member import Member, MemberRole
from .policy import Policy, PolicyRule
from .r6 import R6Request, R6Response, R6Status
from .activity_quality import ActivityWindow, ActivityTier

__all__ = [
    'Team',
    'TeamConfig',
    'Member',
    'MemberRole',
    'Policy',
    'PolicyRule',
    'R6Request',
    'R6Response',
    'R6Status',
    'ActivityWindow',
    'ActivityTier',
]
