from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

from .models import Agent, Society, World
from .mrh_profiles import get_mrh_for_event_type
from .r6 import make_r6_envelope
from .trust_client import get_agent_trust_composite, set_agent_trust_composite
from .audit import request_audit


@dataclass
class AppliedAction:
    life_id: str
    world_tick: int
    agent_lct: str
    action_type: str
    atp_cost: float
    atp_before: float
    atp_after: float
    trust_before: float
    trust_after: float
    event_type: str
    reason: str


def apply_policy_action(
    *,
    world: World,
    society: Society,
    agent: Agent,
    life_id: str,
    proposed_action: Dict[str, Any],
    default_target_lct: Optional[str] = None,
) -> AppliedAction:
    action_type = str(proposed_action.get("action_type", "idle"))
    atp_cost = float(proposed_action.get("atp_cost", 0.0))
    description = str(proposed_action.get("description", ""))

    atp_before = float((agent.resources or {}).get("ATP", 0.0))
    atp_after = max(0.0, atp_before - max(0.0, atp_cost))
    agent.resources["ATP"] = atp_after

    trust_before = get_agent_trust_composite(world, agent.agent_lct, default=0.0)
    trust_after = trust_before

    event_type = "agent_action"
    reason = description or f"policy action: {action_type}"

    if action_type == "idle":
        event_type = "agent_idle"
    elif action_type == "conservative_audit":
        event_type = "audit_request"
        target_lct = default_target_lct
        if target_lct is None:
            # Choose any other member as a default audit target.
            for lct in society.members:
                if lct != agent.agent_lct:
                    target_lct = lct
                    break
        if target_lct is None:
            target_lct = agent.agent_lct

        scope = {
            "mrh": get_mrh_for_event_type("audit_request"),
            "fields": ["treasury", "roles", "membership"],
        }
        request_audit(
            world=world,
            society=society,
            auditor_lct=agent.agent_lct,
            target_lct=target_lct,
            scope=scope,
            reason=reason,
            atp_allocation=float(atp_cost),
        )
        trust_after = min(1.0, trust_before + 0.01)
        set_agent_trust_composite(world, agent.agent_lct, trust_after)
    elif action_type in {"small_spend", "risky_spend"}:
        event_type = "agent_atp_spend"
        # Treat risky spend as slightly harmful to trust; small spend neutral.
        if action_type == "risky_spend":
            trust_after = max(0.0, trust_before - 0.01)
            set_agent_trust_composite(world, agent.agent_lct, trust_after)

    mrh_profile = get_mrh_for_event_type("trust_update")
    action_lct = f"{life_id}:action:{world.tick}:{action_type}"

    world.add_context_edge(
        subject=agent.agent_lct,
        predicate="web4:performedAction",
        object=action_lct,
        mrh={"deltaR": "local", "deltaT": "session", "deltaC": "agent-scale"},
    )

    society.pending_events.append(
        {
            "type": event_type,
            "life_id": life_id,
            "agent_lct": agent.agent_lct,
            "action_type": action_type,
            "atp_cost": float(atp_cost),
            "atp_before": atp_before,
            "atp_after": atp_after,
            "trust_before": float(trust_before),
            "trust_after": float(trust_after),
            "mrh": mrh_profile,
            "reason": reason,
            "r6": make_r6_envelope(
                interaction_type=event_type,
                justification=reason,
                constraints={
                    "mrh": mrh_profile,
                    "life_id": life_id,
                    "action_lct": action_lct,
                },
            ),
            "world_tick": world.tick,
        }
    )

    return AppliedAction(
        life_id=life_id,
        world_tick=world.tick,
        agent_lct=agent.agent_lct,
        action_type=action_type,
        atp_cost=float(atp_cost),
        atp_before=atp_before,
        atp_after=atp_after,
        trust_before=float(trust_before),
        trust_after=float(trust_after),
        event_type=event_type,
        reason=reason,
    )


def applied_action_to_dict(action: AppliedAction) -> Dict[str, Any]:
    return asdict(action)
