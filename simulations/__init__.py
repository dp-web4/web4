# SPDX-License-Identifier: PROPRIETARY
# Copyright (c) 2025 Hardbound Contributors
#
# Hardbound - Enterprise AI Governance
# https://github.com/dp-web4/hardbound

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

DERIVATION & MODULARITY
=======================

Hardbound is a self-contained enterprise product. While it shares conceptual
ancestry with the open-source Web4 governance modules, it maintains its own
implementations for commercial deployment independence.

Derived modules:
- ledger.py: Enterprise ledger (derived from claude-code-plugin/governance/ledger.py)
- policy_entity.py: Enterprise PolicyEntity (derived from claude-code-plugin/governance/policy_entity.py)

The derivation relationship is documented for transparency but the codebases
are intentionally decoupled. Changes to the open-source modules do not
automatically flow to Hardbound, allowing:
- Independent versioning and release cycles
- Enterprise-specific features without open-source constraints
- Regulatory compliance requiring isolated code review
- Commercial licensing separate from MIT

For the open-source governance implementation, see:
- https://github.com/dp-web4/web4/tree/main/claude-code-plugin/governance

Each repo serves a different purpose:
- hardbound: Enterprise commercial product
- web4: Research and specification
- plugins/extensions: Public concept demonstrations
- 4-life: Public explainer and simulation
"""

from .team import Team, TeamConfig
from .member import Member, MemberRole
from .policy import Policy, PolicyRule
from .r6 import R6Request, R6Response, R6Status
from .activity_quality import ActivityWindow, ActivityTier
from .ledger import Ledger
from .policy_entity import (
    PolicyEntity,
    PolicyRegistry,
    PolicyEvaluation,
    PolicyConfig,
    PolicyMatch,
    PolicyDecision,
    get_enterprise_preset,
)

__all__ = [
    # Team/Society
    'Team',
    'TeamConfig',
    'Member',
    'MemberRole',
    # Policy (legacy)
    'Policy',
    'PolicyRule',
    # PolicyEntity (derived from open-source)
    'PolicyEntity',
    'PolicyRegistry',
    'PolicyEvaluation',
    'PolicyConfig',
    'PolicyMatch',
    'PolicyDecision',
    'get_enterprise_preset',
    # R6 workflow
    'R6Request',
    'R6Response',
    'R6Status',
    # Activity
    'ActivityWindow',
    'ActivityTier',
    # Ledger (derived from open-source)
    'Ledger',
]
