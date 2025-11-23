from __future__ import annotations

"""Role-related helpers for the Web4 game engine (v0).

This module provides utilities for:
- Constructing role LCT identifiers from a society LCT.
- Emitting role binding and pairing events into a Society's pending_events.
- Recording corresponding MRH/LCT context edges in the World.
"""

from typing import Dict, Any

from .models import World, Society, Agent


def make_role_lct(society_lct: str, role_name: str) -> str:
    """Construct a role LCT under a society's namespace.

    Example:
        society_lct: lct:web4:society:home-root
        role_name:  auditor
        -> lct:web4:role:home-root:auditor
    """

    # Extract the society fragment after the last ':'
    fragment = society_lct.split(":")[-1]
    return f"lct:web4:role:{fragment}:{role_name}"


def bind_role(
    *,
    world: World,
    society: Society,
    role_name: str,
    subject_lct: str,
    reason: str,
    mrh: Dict[str, str] | None = None,
) -> str:
    """Bind a role to a subject LCT under the authority of a society.

    - Creates a role LCT if needed.
    - Appends a role_binding event to society.pending_events.
    - Adds MRH/LCT context edges to world.context_edges.

    Returns the role LCT.
    """

    role_lct = make_role_lct(society.society_lct, role_name)
    mrh_profile = mrh or {
        "deltaR": "local",
        "deltaT": "session",
        "deltaC": "agent-scale",
    }

    # Record event on the society microchain (pending until sealed).
    event: Dict[str, Any] = {
        "type": "role_binding",
        "society_lct": society.society_lct,
        "role_lct": role_lct,
        "subject_lct": subject_lct,
        "mrh": mrh_profile,
        "reason": reason,
        "world_tick": world.tick,
    }
    society.pending_events.append(event)

    # Reflect in MRH/LCT context edges.
    world.add_context_edge(
        subject=subject_lct,
        predicate="web4:hasRole",
        object=role_lct,
        mrh=mrh_profile,
    )
    world.add_context_edge(
        subject=society.society_lct,
        predicate="web4:bindsRole",
        object=role_lct,
        mrh=mrh_profile,
    )

    return role_lct


def pair_role_with_lct(
    *,
    world: World,
    society: Society,
    role_lct: str,
    other_lct: str,
    reason: str,
    mrh: Dict[str, str] | None = None,
) -> None:
    """Create a contextual pairing between a role LCT and another LCT.

    The root society acts as pairing authority; this is recorded as a
    chain event and mirrored into MRH/LCT context edges.
    """

    mrh_profile = mrh or {
        "deltaR": "local",
        "deltaT": "session",
        "deltaC": "agent-scale",
    }

    event: Dict[str, Any] = {
        "type": "role_pairing",
        "society_lct": society.society_lct,
        "role_lct": role_lct,
        "other_lct": other_lct,
        "mrh": mrh_profile,
        "reason": reason,
        "world_tick": world.tick,
    }
    society.pending_events.append(event)

    world.add_context_edge(
        subject=role_lct,
        predicate="web4:pairedWith",
        object=other_lct,
        mrh=mrh_profile,
    )
    world.add_context_edge(
        subject=society.society_lct,
        predicate="web4:authorizesPairing",
        object=role_lct,
        mrh=mrh_profile,
    )
