from __future__ import annotations

"""Trust client interface for the Web4 game engine (v0).

This module provides a narrow API that the in-memory game engine can use to:

- Query an agent's or society's composite trust score.
- Record trust-relevant events (e.g. suspicious treasury behavior).

v0 behavior primarily operates on the in-memory `World` model, but this
module also makes a best-effort attempt to talk to the Web4 authorization
database by loading the TrustUpdateBatcher from
`web4-standard/implementation/authorization/trust_update_batcher.py` when
available.

All trust I/O from `/web4/game` should go through this module so that
DB-backed integration can evolve without changing policy code.
"""

from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import Dict, Any, Optional

from .models import World, Society


_batcher = None
_batcher_load_error: Optional[Exception] = None


def _ensure_batcher() -> Optional[object]:
    """Lazily load the TrustUpdateBatcher from the authorization module.

    Best-effort only:
    - If loading fails, we remember the error and return None.
    - Callers should treat a None return as "DB integration unavailable".
    """

    global _batcher, _batcher_load_error
    if _batcher is not None or _batcher_load_error is not None:
        return _batcher

    try:
        here = Path(__file__).resolve()
        # This file lives under web4/game/engine; the Web4 repo root is two
        # levels up from here (../..). From that root we can reach the
        # authorization implementation under web4-standard/implementation/authorization.
        web4_root = here.parents[2]
        auth_root = web4_root / "web4-standard" / "implementation" / "authorization"
        batcher_path = auth_root / "trust_update_batcher.py"
        if not batcher_path.is_file():
            raise FileNotFoundError(str(batcher_path))

        loader = SourceFileLoader("web4_auth_trust_update_batcher", str(batcher_path))
        module = loader.load_module()
        TrustUpdateBatcher = getattr(module, "TrustUpdateBatcher", None)
        if TrustUpdateBatcher is None:
            raise AttributeError("TrustUpdateBatcher not found in trust_update_batcher module")

        # Minimal DB config; adjust as needed. If this fails at runtime, the
        # exception will be recorded and future calls will see integration as
        # unavailable.
        db_config = {
            "dbname": "web4",
            "user": "postgres",
            "host": "localhost",
        }
        _batcher = TrustUpdateBatcher(db_config=db_config, auto_start=True)
        return _batcher
    except Exception as exc:  # noqa: BLE001 - best-effort loader
        _batcher_load_error = exc
        print(f"[web4/game] TrustUpdateBatcher unavailable ({exc!r}); continuing with in-memory trust only")
        return None


def get_agent_trust_composite(world: World, agent_lct: str, *, default: float = 0.0) -> float:
    """Return the agent's composite T3 trust score as seen by the game.

    v0 implementation reads from the in-memory `World` only. It exists as a
    seam so future work can optionally prefer DB-backed values when available.
    """

    agent = world.get_agent(agent_lct)
    if not agent:
        return default

    t3 = agent.trust_axes.get("T3") or {}
    try:
        return float(t3.get("composite", default))
    except (TypeError, ValueError):
        return default


def set_agent_trust_composite(world: World, agent_lct: str, value: float) -> None:
    """Set the agent's composite T3 trust score in the in-memory world.

    This mirrors the existing behavior in `policy._lower_trust` and is kept
    here so a future DB-backed client can update both in-memory and external
    state in one place.
    """

    agent = world.get_agent(agent_lct)
    if not agent:
        return

    t3 = agent.trust_axes.get("T3") or {}
    t3["composite"] = float(value)
    agent.trust_axes["T3"] = t3


def get_society_trust_composite(world: World, society_lct: str, *, default: float = 0.7) -> float:
    """Return the society's composite T3 trust score.

    v0 implementation reads from the in-memory `World` only, but centralizes
    the logic behind a clear seam.
    """

    society = world.get_society(society_lct)
    if not society:
        return default

    t_axes = (society.trust_axes or {}).get("T3") or {}
    try:
        return float(t_axes.get("composite", default))
    except (TypeError, ValueError):
        return default


def record_suspicious_treasury_event(
    *,
    world: World,
    society: Society,
    initiator_lct: str,
    count: int,
    trust_delta_per_spend: float,
) -> None:
    """Record a suspicious treasury event for an initiator.

    v0 behavior:
    - Lowers the agent's in-memory composite trust by `trust_delta_per_spend * count`.
    - Logs an intent to integrate with the DB-backed authorization layer.

    Future work:
    - Emit a structured trust event into the Web4 authorization DB (e.g.,
      insert into trust_history and/or use TrustUpdateBatcher).
    """

    current = get_agent_trust_composite(world, initiator_lct, default=0.0)
    new_comp = max(0.0, current + (trust_delta_per_spend * count))
    set_agent_trust_composite(world, initiator_lct, new_comp)

    # Best-effort DB integration: try to enqueue a T3 update via the
    # authorization TrustUpdateBatcher. Failures are logged but do not
    # interrupt the game loop.
    batcher = _ensure_batcher()
    if batcher is not None:
        try:
            # Use temperament as the primary axis for "suspicious behavior".
            from decimal import Decimal

            delta = Decimal(str(trust_delta_per_spend * count))
            batcher.record_t3_update(
                lct_id=initiator_lct,
                org_id=society.society_lct,
                talent_delta=Decimal("0.0"),
                training_delta=Decimal("0.0"),
                temperament_delta=delta,
            )
        except Exception as exc:  # noqa: BLE001
            print(
                "[web4/game] failed to enqueue DB trust update for suspicious treasury event:",
                {
                    "society_lct": society.society_lct,
                    "initiator_lct": initiator_lct,
                    "error": repr(exc),
                },
            )

    # Always log the in-memory update so autonomous sessions can see that
    # the hook is firing regardless of DB availability.
    print(
        "[web4/game] record_suspicious_treasury_event:",
        {
            "society_lct": society.society_lct,
            "initiator_lct": initiator_lct,
            "count": count,
            "old_composite": current,
            "new_composite": new_comp,
        },
    )


def note_cross_society_trust_read(
    *, world: World, src_society_lct: str, dst_society_lct: str, trust_value: float
) -> None:
    """Optional hook to log cross-society trust reads.

    For now this only prints a debug line; future work can mirror these reads
    into a DB-backed monitoring or metrics system.
    """

    print(
        "[web4/game] cross-society trust read:",
        {
            "from": src_society_lct,
            "to": dst_society_lct,
            "trust": trust_value,
        },
    )
