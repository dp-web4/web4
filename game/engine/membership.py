from __future__ import annotations

"""Membership event and context helpers for the Web4 game engine (v0).

This module defines events for membership changes (join, leave,
revocation) and mirrors them into the MRH/LCT context graph.
"""

from typing import Dict, Any

from .models import World, Society
from .r6 import make_r6_envelope


def _default_mrh() -> Dict[str, str]:
    return {
        "deltaR": "local",
        "deltaT": "session",
        "deltaC": "agent-scale",
    }


def membership_join(
    *,
    world: World,
    society: Society,
    agent_lct: str,
    reason: str,
    mrh: Dict[str, str] | None = None,
) -> None:
    """Record that an agent joined a society."""

    mrh_profile = mrh or _default_mrh()
    if agent_lct not in society.members:
        society.members.append(agent_lct)

    event: Dict[str, Any] = {
        "type": "membership_join",
        "society_lct": society.society_lct,
        "agent_lct": agent_lct,
        "mrh": mrh_profile,
        "reason": reason,
        "r6": make_r6_envelope(
            interaction_type="membership_join",
            justification=reason,
            constraints={"mrh": mrh_profile},
        ),
        "world_tick": world.tick,
    }
    society.pending_events.append(event)

    world.add_context_edge(
        subject=agent_lct,
        predicate="web4:memberOf",
        object=society.society_lct,
        mrh=mrh_profile,
    )


def membership_leave(
    *,
    world: World,
    society: Society,
    agent_lct: str,
    reason: str,
    mrh: Dict[str, str] | None = None,
) -> None:
    """Record that an agent voluntarily left a society."""

    mrh_profile = mrh or _default_mrh()
    if agent_lct in society.members:
        society.members.remove(agent_lct)

    event: Dict[str, Any] = {
        "type": "membership_leave",
        "society_lct": society.society_lct,
        "agent_lct": agent_lct,
        "mrh": mrh_profile,
        "reason": reason,
        "r6": make_r6_envelope(
            interaction_type="membership_leave",
            justification=reason,
            constraints={"mrh": mrh_profile},
        ),
        "world_tick": world.tick,
    }
    society.pending_events.append(event)

    world.add_context_edge(
        subject=agent_lct,
        predicate="web4:wasMemberOf",
        object=society.society_lct,
        mrh=mrh_profile,
    )


def membership_revocation(
    *,
    world: World,
    society: Society,
    agent_lct: str,
    reason: str,
    mrh: Dict[str, str] | None = None,
) -> None:
    """Record that an agent's membership was revoked by the society."""

    mrh_profile = mrh or _default_mrh()
    if agent_lct in society.members:
        society.members.remove(agent_lct)

    event: Dict[str, Any] = {
        "type": "membership_revocation",
        "society_lct": society.society_lct,
        "agent_lct": agent_lct,
        "mrh": mrh_profile,
        "reason": reason,
        "r6": make_r6_envelope(
            interaction_type="membership_revocation",
            justification=reason,
            constraints={"mrh": mrh_profile},
        ),
        "world_tick": world.tick,
    }
    society.pending_events.append(event)

    world.add_context_edge(
        subject=agent_lct,
        predicate="web4:membershipRevokedBy",
        object=society.society_lct,
        mrh=mrh_profile,
    )
