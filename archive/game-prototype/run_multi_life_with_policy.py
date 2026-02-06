"""Run multiple Web4 lives and apply the HRM research policy to each.

This script glues together:
- `web4/game/multi_life_home_society.py::run_multi_life` and
- `HRM/implementation/research_agent_driver.py::run_policy_once`.

It assumes the `HRM` repository lives alongside `web4` under the same
`ai-agents` parent directory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from closed_loop_multi_life import run_closed_loop_multi_life


def _import_hrm_policy() -> Any:
    """Dynamically import `run_policy_once` from the HRM repo."""

    game_dir = Path(__file__).resolve().parent
    ai_agents_root = game_dir.parent.parent
    hrm_root = ai_agents_root / "HRM"

    if hrm_root.is_dir():
        sys.path.insert(0, str(hrm_root))

    try:
        from implementation.research_agent_driver import run_policy_once  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Could not import HRM research_agent_driver. Ensure the HRM repo "
            "exists alongside web4 under the same parent directory."
        ) from exc

    return run_policy_once


def run_multi_life_with_policy(
    *,
    num_lives: int = 3,
    steps_per_life: int = 20,
    termination_t3_threshold: float = 0.2,
) -> Dict[str, Any]:
    """Run multiple lives and attach a per-life HRM action proposal."""

    multi = run_closed_loop_multi_life(
        num_lives=num_lives,
        steps_per_life=steps_per_life,
        termination_t3_threshold=termination_t3_threshold,
    )

    if "error" in multi:
        return {"multi_life": multi, "policy_results": []}

    run_policy_once = _import_hrm_policy()

    policy_results: List[Dict[str, Any]] = []
    for life in multi.get("lives", []) or []:
        # HRM policy expects the one-life keys.
        life_summary = {
            "life_state": life.get("life_state"),
            "t3_history": life.get("t3_history"),
            "atp_history": life.get("atp_history"),
            "life_id": life.get("life_id"),
            "termination_reason": life.get("termination_reason"),
        }
        policy_result = run_policy_once(life_summary)
        policy_results.append(
            {
                "life_id": life.get("life_id"),
                "policy_result": policy_result,
            }
        )

    return {
        "multi_life": multi,
        "policy_results": policy_results,
    }


if __name__ == "__main__":
    combined = run_multi_life_with_policy(num_lives=3, steps_per_life=20)
    print(json.dumps(combined, indent=2, sort_keys=True))
