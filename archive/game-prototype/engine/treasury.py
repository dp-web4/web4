from __future__ import annotations

"""Treasury event and policy helpers for the Web4 game engine (v0).

This module defines structured treasury events (spend, deposit,
transfer) that are recorded on a society's microchain and, in v0,
perform simple ATP balance updates.

Future work will align ATP handling with full Web4/ACT economics.
"""

from typing import Dict, Any

from .models import World, Society
from .r6 import make_r6_envelope
from .mrh_profiles import get_mrh_for_event_type


def treasury_spend(
    *,
    world: World,
    society: Society,
    treasury_lct: str,
    initiator_lct: str,
    amount: float,
    reason: str,
    mrh: Dict[str, str] | None = None,
) -> None:
    """Record a spend from a society treasury.

    v0 behavior:
    - Appends a `treasury_spend` event to `society.pending_events`.
    - Decreases `society.treasury["ATP"]` by `amount` if funds exist.
    - Wraps the event in an R6 envelope.
    """

    mrh_profile = mrh or get_mrh_for_event_type("treasury_spend")

    # Basic membership and role checks (v0 enforcement):
    is_member = initiator_lct in society.members
    treasurer_role_lct = f"lct:web4:role:{society.society_lct.split(':')[-1]}:treasurer"
    has_treasurer_role = any(
        edge.subject == initiator_lct
        and edge.predicate == "web4:hasRole"
        and edge.object == treasurer_role_lct
        for edge in world.context_edges
    )

    if not (is_member and has_treasurer_role):
        reject_reason = (
            "treasury_spend rejected: initiator must be current member "
            "with active treasurer role"
        )
        reject_event: Dict[str, Any] = {
            "type": "treasury_spend_rejected",
            "society_lct": society.society_lct,
            "treasury_lct": treasury_lct,
            "initiator_lct": initiator_lct,
            "amount": float(amount),
            "mrh": mrh_profile,
            "reason": f"{reject_reason} ({reason})",
            "r6": make_r6_envelope(
                interaction_type="treasury_spend_rejected",
                justification=reject_reason,
                constraints={
                    "mrh": mrh_profile,
                    "max_amount": amount,
                },
            ),
            "world_tick": world.tick,
        }
        society.pending_events.append(reject_event)
        return

    atp_before = float(society.treasury.get("ATP", 0.0))
    atp_after = max(0.0, atp_before - float(amount))
    society.treasury["ATP"] = atp_after

    event: Dict[str, Any] = {
        "type": "treasury_spend",
        "society_lct": society.society_lct,
        "treasury_lct": treasury_lct,
        "initiator_lct": initiator_lct,
        "amount": float(amount),
        "atp_before": atp_before,
        "atp_after": atp_after,
        "mrh": mrh_profile,
        "reason": reason,
        "r6": make_r6_envelope(
            interaction_type="treasury_spend",
            justification=reason,
            constraints={
                "mrh": mrh_profile,
                "max_amount": amount,
            },
        ),
        "world_tick": world.tick,
    }
    society.pending_events.append(event)


def treasury_deposit(
    *,
    world: World,
    society: Society,
    treasury_lct: str,
    source_lct: str,
    amount: float,
    reason: str,
    mrh: Dict[str, str] | None = None,
) -> None:
    """Record a deposit into a society treasury (v0)."""

    mrh_profile = mrh or get_mrh_for_event_type("treasury_deposit")
    atp_before = float(society.treasury.get("ATP", 0.0))
    atp_after = atp_before + float(amount)
    society.treasury["ATP"] = atp_after

    event: Dict[str, Any] = {
        "type": "treasury_deposit",
        "society_lct": society.society_lct,
        "treasury_lct": treasury_lct,
        "source_lct": source_lct,
        "amount": float(amount),
        "atp_before": atp_before,
        "atp_after": atp_after,
        "mrh": mrh_profile,
        "reason": reason,
        "r6": make_r6_envelope(
            interaction_type="treasury_deposit",
            justification=reason,
            constraints={"mrh": mrh_profile},
        ),
        "world_tick": world.tick,
    }
    society.pending_events.append(event)


def treasury_transfer(
    *,
    world: World,
    society: Society,
    from_lct: str,
    to_lct: str,
    amount: float,
    reason: str,
    mrh: Dict[str, str] | None = None,
) -> None:
    """Logical transfer event between two LCTs within/related to a society.

    v0: Does not adjust per-agent balances beyond the society treasury
    field; it just records an intent for later, richer economic models.
    """

    mrh_profile = mrh or get_mrh_for_event_type("treasury_transfer")

    event: Dict[str, Any] = {
        "type": "treasury_transfer",
        "society_lct": society.society_lct,
        "from_lct": from_lct,
        "to_lct": to_lct,
        "amount": float(amount),
        "mrh": mrh_profile,
        "reason": reason,
        "r6": make_r6_envelope(
            interaction_type="treasury_transfer",
            justification=reason,
            constraints={
                "mrh": mrh_profile,
                "max_amount": amount,
            },
        ),
        "world_tick": world.tick,
    }
    society.pending_events.append(event)
