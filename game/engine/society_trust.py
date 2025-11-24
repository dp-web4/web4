from __future__ import annotations

"""Society-level trust helpers for the Web4 game (v0).

This module derives a simple T3-like composite trust score for
Society instances based on their on-chain behavior.

The goal is not to be "correct" but to provide a tunable signal that
can drive cross-society policies and federation decisions.
"""

from typing import Dict, Any

from .models import World, Society


def update_society_trust(world: World, society: Society) -> None:
    """Update the society's T3-like composite trust based on recent events.

    v0 heuristic:
    - Start from existing composite (default 0.7 if missing).
    - Look at recent blocks (last 20) and count:
      - Good signals ("cooperative"):
        - treasury_deposit
      - Bad signals ("costly"):
        - treasury_spend with "suspicious" in reason
        - role_revocation
        - membership_revocation
        - audit_request
    - Adjust composite by small steps and clamp to [0.0, 1.0].
      Currently: +0.015 per good, -0.02 per bad.
    """

    t_axes = society.trust_axes.get("T3") if society.trust_axes else None
    if t_axes is None:
        t_axes = {
            "talent": 0.5,
            "training": 0.5,
            "temperament": 0.7,
            "composite": 0.7,
        }

    composite = float(t_axes.get("composite", 0.7))

    good = 0
    bad = 0

    for block in society.blocks[-20:]:
        for ev in block.get("events", []):
            etype = ev.get("type")
            if etype == "treasury_deposit":
                good += 1
            elif etype == "treasury_spend" and "suspicious" in str(ev.get("reason", "")):
                bad += 1
            elif etype in {"role_revocation", "membership_revocation", "audit_request"}:
                bad += 1

    # Heuristic adjustments: reward cooperation slightly more than before,
    # but punish bad behavior more strongly.
    composite += 0.015 * good
    composite -= 0.02 * bad

    composite = max(0.0, min(1.0, composite))
    t_axes["composite"] = composite
    society.trust_axes = society.trust_axes or {}
    society.trust_axes["T3"] = t_axes
