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
from .mrh_profiles import quality_level_to_veracity
from .trust_client import (
    get_society_trust_composite,
    note_cross_society_trust_read,
)


def apply_cross_society_policies(world: World) -> None:
    """Apply simple cross-society suppression/quarantine policies.

    v0 heuristic:
    - For each pair of federated societies A, B, look at B's composite
      T3 trust.
    - Map low-trust neighbors to MRH-like quality bands and convert
      those to numeric thresholds via quality_level_to_veracity().
    - If B's composite falls below the "high" quality band,
      A emits a `federation_throttle` event.
    - If B's composite falls below the "critical" quality band,
      A additionally emits a `quarantine_request`.

    Federation is inferred from context edges with predicate
    `web4:federatesWith`.
    """

    # Build a quick lookup of society trust and federation links.
    society_trust: Dict[str, float] = {}
    federation: Dict[str, set[str]] = {}

    for s in world.societies.values():
        composite = get_society_trust_composite(world, s.society_lct, default=0.7)
        society_trust[s.society_lct] = composite

    for edge in world.context_edges:
        if edge.predicate == "web4:federatesWith":
            federation.setdefault(edge.subject, set()).add(edge.object)

    # MRH-informed trust thresholds for cross-society decisions.
    throttle_quality = "high"
    quarantine_quality = "critical"
    throttle_threshold = quality_level_to_veracity(throttle_quality)
    quarantine_threshold = quality_level_to_veracity(quarantine_quality)

    for src_lct, neighbors in federation.items():
        src_soc = world.get_society(src_lct)
        if not src_soc:
            continue
        for dst_lct in neighbors:
            dst_trust = society_trust.get(dst_lct, 0.7)
            note_cross_society_trust_read(
                world=world,
                src_society_lct=src_lct,
                dst_society_lct=dst_lct,
                trust_value=dst_trust,
            )
            events: list[Dict[str, Any]] = []

            if dst_trust < throttle_threshold:
                ev = {
                    "type": "federation_throttle",
                    "from_society_lct": src_lct,
                    "to_society_lct": dst_lct,
                    "dst_trust": dst_trust,
                    "r6": make_r6_envelope(
                        interaction_type="federation_throttle",
                        justification="low-trust neighbor (below MRH-aware federation threshold)",
                        constraints={
                            "threshold": throttle_threshold,
                            "quality": throttle_quality,
                            "trust": dst_trust,
                        },
                    ),
                }
                events.append(ev)

            if dst_trust < quarantine_threshold:
                ev = {
                    "type": "quarantine_request",
                    "from_society_lct": src_lct,
                    "to_society_lct": dst_lct,
                    "dst_trust": dst_trust,
                    "r6": make_r6_envelope(
                        interaction_type="quarantine_request",
                        justification="very low-trust neighbor (below MRH-aware quarantine threshold)",
                        constraints={
                            "threshold": quarantine_threshold,
                            "quality": quarantine_quality,
                            "trust": dst_trust,
                        },
                    ),
                }
                events.append(ev)

            if not events:
                continue

            for ev in events:
                src_soc.pending_events.append(ev)
