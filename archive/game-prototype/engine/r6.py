from __future__ import annotations

"""R6 interaction envelope helpers for the Web4 game engine (v0).

These utilities construct a minimal, structured envelope describing
interactions that will be recorded on a society's chain.

The intent is to give auditors and policies a uniform way to interpret
"what kind of interaction is this?", "why was it done?", and "under
what constraints?".
"""

from typing import Dict, Any


def make_r6_envelope(
    *,
    interaction_type: str,
    justification: str,
    constraints: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Create a minimal R6 envelope for an interaction.

    Args:
        interaction_type: Short string naming the interaction
            (e.g. "audit", "role_binding", "role_pairing").
        justification: Human-readable reason for the interaction.
        constraints: Optional structured constraints such as MRH,
            scope fields, budgets, etc.
    """

    return {
        "interaction_type": interaction_type,
        "justification": justification,
        "constraints": constraints or {},
    }
