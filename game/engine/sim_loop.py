"""Minimal simulation loop for the Web4 game (v0).

This module defines a very simple tick-based simulation loop that
advances a `World` instance. Behavior is intentionally minimal and
will be extended over time.
"""

from __future__ import annotations

import hashlib
import json
from typing import Callable, Optional

from .models import World, Agent, Society
from .policy import apply_simple_policies
from .signing import BlockSigner
from .signing import get_block_signer
from .cross_society_policy import apply_cross_society_policies


def tick_world(world: World) -> None:
    """Advance the world by one tick.

    For v0 this simply increments the tick counter and calls
    placeholder hooks for agent and society behavior.
    """

    world.tick += 1

    # Placeholder: iterate over agents and societies and allow them to
    # take actions. Future versions will plug in real decision
    # policies, trust updates, and economic flows.
    for agent in list(world.agents.values()):
        _agent_step(world, agent)

    for society in list(world.societies.values()):
        _society_step(world, society)

    # Apply cross-society policies once per tick after individual
    # societies have taken their local actions.
    apply_cross_society_policies(world)


def _agent_step(world: World, agent: Agent) -> None:
    """Placeholder for per-agent behavior in a single tick."""

    # Future work: choose actions based on trust, resources,
    # memberships, and available societies/tasks.

    # For now, just record MRH/LCT context edges for memberships so we can
    # inspect the evolving society graph. We use a coarse MRH profile.
    mrh_profile = {
        "deltaR": "local",
        "deltaT": "session",
        "deltaC": "agent-scale",
    }
    for society_lct in agent.memberships:
        world.add_context_edge(
            subject=agent.agent_lct,
            predicate="web4:participantIn",
            object=society_lct,
            mrh=mrh_profile,
        )


def _society_step(world: World, society: Society) -> None:
    """Placeholder for per-society behavior in a single tick.

    Implements minimal microblock sealing logic:
    - Checks pending events and elapsed time
    - Seals blocks with cryptographic chaining (previous_hash, header_hash)
    - Adds stub signature for future TPM-backed signing
    """

    # Future work: evaluate membership requests, tasks, treasury, and
    # update trust and MRH context.

    current_time = float(world.tick)

    # Allow policies to react to recent chain events (e.g., suspicious
    # treasury behavior) before sealing any new blocks.
    apply_simple_policies(world, society)

    if not society.pending_events:
        return

    # If enough time has passed since the last block, create a new one.
    if (current_time - society.last_block_time) >= float(society.block_interval_seconds):
        block_index = len(society.blocks)

        # Determine previous header hash, if any.
        previous_hash = None
        if society.blocks:
            previous_hash = society.blocks[-1].get("header_hash")

        # Build the block header (without events/signature).
        header = {
            "index": block_index,
            "society_lct": society.society_lct,
            "previous_hash": previous_hash,
            "timestamp": current_time,
        }

        # Deterministic JSON encoding for hashing.
        header_json = json.dumps(header, sort_keys=True, separators=(",", ":"))
        header_hash = hashlib.sha256(header_json.encode("utf-8")).hexdigest()

        signer = get_block_signer()
        signature = signer.sign_block_header(header)

        # Construct full block including events and stub/hardware signature.
        block = {
            **header,
            "events": list(society.pending_events),
            "header_hash": header_hash,
            "signature": signature,
        }

        society.blocks.append(block)
        society.pending_events.clear()
        society.last_block_time = current_time


def run_world(world: World, steps: int) -> World:
    """Run the world for a fixed number of ticks (v0 helper)."""

    for _ in range(steps):
        tick_world(world)
    return world
