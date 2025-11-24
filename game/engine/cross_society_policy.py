from __future__ import annotations

"""Cross-society suppression/quarantine mechanics (v0).

This module uses society-level trust tensors to emit R6-wrapped events
that represent throttling or quarantining relationships between
societies. It is intentionally simple and meant as a basis for richer
planet-scale policies.
"""

from typing import Dict, Any

from .models import World, Society
from .r6 import make_r6_envelope


def apply_cross_society_policies(world: World) -> None:
    """Apply simple cross-society suppression/quarantine policies.

    v0 heuristic:
    - For each pair of federated societies A, B, look at B's composite
      T3 trust.
    - If B's composite < 0.4, A emits a `federation_throttle` event.
    - If B's composite < 0.25, A additionally emits a `quarantine_request`.

    Federation is inferred from context edges with predicate
    `web4:federatesWith`.
    """

    # Build a quick lookup of society trust and federation links.
    society_trust: Dict[str, float] = {}
    federation: Dict[str, set[str]] = {}

    for s in world.societies.values():
        t_axes = (s.trust_axes or {}).get("T3") or {}
        composite = float(t_axes.get("composite", 0.7))
        society_trust[s.society_lct] = composite

    for edge in world.context_edges:
        if edge.predicate == "web4:federatesWith":
            federation.setdefault(edge.subject, set()).add(edge.object)

    for src_lct, neighbors in federation.items():
        src_soc = world.get_society(src_lct)
        if not src_soc:
            continue
        for dst_lct in neighbors:
            dst_trust = society_trust.get(dst_lct, 0.7)
            events: list[Dict[str, Any]] = []

            if dst_trust < 0.4:
                ev = {
                    "type": "federation_throttle",
                    "from_society_lct": src_lct,
                    "to_society_lct": dst_lct,
                    "dst_trust": dst_trust,
                    "r6": make_r6_envelope(
                        interaction_type="federation_throttle",
                        justification="low-trust neighbor",
                        constraints={"threshold": 0.4, "trust": dst_trust},
                    ),
                }
                events.append(ev)

            if dst_trust < 0.25:
                ev = {
                    "type": "quarantine_request",
                    "from_society_lct": src_lct,
                    "to_society_lct": dst_lct,
                    "dst_trust": dst_trust,
                    "r6": make_r6_envelope(
                        interaction_type="quarantine_request",
                        justification="very low-trust neighbor",
                        constraints={"threshold": 0.25, "trust": dst_trust},
                    ),
                }
                events.append(ev)

            if not events:
                continue

            for ev in events:
                src_soc.pending_events.append(ev)
