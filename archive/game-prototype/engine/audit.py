from __future__ import annotations

"""Audit-related helpers for the Web4 game engine (v0).

These utilities construct structured, R6-wrapped audit events and
append them to a society's pending_events so they are later sealed into
blocks.
"""

from typing import Dict, Any

from .models import World, Society
from .r6 import make_r6_envelope


def request_audit(
    *,
    world: World,
    society: Society,
    auditor_lct: str,
    target_lct: str,
    scope: Dict[str, Any],
    reason: str,
    atp_allocation: float,
) -> None:
    """Append an audit_request event to a society's pending_events.

    Constraints (v0):
    - Explicit auditor and target LCTs.
    - Explicit scope (fields + MRH).
    - Explicit ATP allocation and human-readable reason.
    - R6 envelope included for downstream analysis.

    ATP deduction is NOT yet enforced here; this is a structural stub
    to keep the chain auditable.
    """

    event = {
        "type": "audit_request",
        "auditor_lct": auditor_lct,
        "target_lct": target_lct,
        "scope": scope,
        "reason": reason,
        "atp_allocation": atp_allocation,
        "r6": make_r6_envelope(
            interaction_type="audit",
            justification=reason,
            constraints={
                "mrh": scope.get("mrh"),
                "fields": scope.get("fields"),
            },
        ),
        "world_tick": world.tick,
    }
    society.pending_events.append(event)
