from __future__ import annotations

"""Simple policy helpers for Web4 game societies (v0).

This module inspects recent chain events for a society and applies
rudimentary policy responses, such as lowering trust or revoking roles.

It is intentionally simple and meant as a starting point for richer
policy/intent systems.
"""

from typing import Dict, Any

from .models import World, Society
from .roles import revoke_role
from .membership import membership_revocation
from .society_trust import update_society_trust
from .mrh_profiles import quality_level_to_veracity
from .trust_client import (
    get_agent_trust_composite,
    record_suspicious_treasury_event,
)


def _suspicious_spend_trust_threshold(count: int) -> float:
    """Map suspicious spend count to an MRH-like quality band and trust threshold.

    This is a v0 heuristic that treats more repeated abuses as requiring
    a higher trust bar to avoid revocation. It reuses the quality
    levels from MRH (low/medium/high/critical) and converts them to a
    numeric threshold via quality_level_to_veracity().
    """

    if count >= 3:
        quality = "critical"
    elif count == 2:
        quality = "high"
    else:
        quality = "medium"

    return quality_level_to_veracity(quality)


def apply_simple_policies(world: World, society: Society) -> None:
    """Inspect recent events and apply simple policy responses.

    Current behaviors (very rough):
    - If an agent initiates multiple suspicious treasury_spend events,
      lower their composite trust and, after a threshold, revoke their
      treasurer role if present.
    """

    # Aggregate suspicious spends by initiator.
    suspicious_counts: Dict[str, int] = {}
    for block in society.blocks[-10:]:  # look at recent history only
        for ev in block.get("events", []):
            if ev.get("type") == "treasury_spend" and "suspicious" in str(ev.get("reason", "")):
                initiator = ev.get("initiator_lct")
                if not initiator:
                    continue
                suspicious_counts[initiator] = suspicious_counts.get(initiator, 0) + 1

    if not suspicious_counts:
        return

    # Simple thresholds.
    trust_delta_per_spend = -0.05
    revoke_threshold = 3

    for initiator_lct, count in suspicious_counts.items():
        # Lower trust proportional to suspicious behavior via the trust client.
        record_suspicious_treasury_event(
            world=world,
            society=society,
            initiator_lct=initiator_lct,
            count=count,
            trust_delta_per_spend=trust_delta_per_spend,
        )

        # If behavior is bad enough and trust has fallen below the
        # context-appropriate threshold, attempt to revoke treasurer
        # role and membership.
        composite = get_agent_trust_composite(world, initiator_lct, default=0.0)
        threshold = _suspicious_spend_trust_threshold(count)

        if count >= revoke_threshold and composite < threshold:
            treasurer_role_lct = f"lct:web4:role:{society.society_lct.split(':')[-1]}:treasurer"
            revoke_role(
                world=world,
                society=society,
                role_lct=treasurer_role_lct,
                subject_lct=initiator_lct,
                reason="policy: repeated suspicious treasury spending (below MRH-aware trust threshold)",
            )
            membership_revocation(
                world=world,
                society=society,
                agent_lct=initiator_lct,
                reason="policy: membership revoked for suspicious treasury behavior (below MRH-aware trust threshold)",
            )

    # Update society-level trust tensor based on recent behavior.
    update_society_trust(world, society)
