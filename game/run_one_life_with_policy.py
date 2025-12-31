"""Run a single Web4 home-society life and apply the HRM research policy.

This script glues together:
- `web4/game/one_life_home_society.py::run_single_life` and
- `HRM/implementation/research_agent_driver.py::run_policy_once`.

It assumes the `HRM` repository lives alongside `web4` under the same
`ai-agents` parent directory.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

from one_life_home_society import run_single_life


def _import_hrm_policy() -> Any:
    """Dynamically import `run_policy_once` from the HRM repo.

    We avoid taking a hard dependency on HRM being installed as a Python
    package by temporarily adding its path to `sys.path`.
    """

    # Assume repo layout: c:/projects/ai-agents/{web4, HRM}
    game_dir = Path(__file__).resolve().parent
    ai_agents_root = game_dir.parent.parent  # go up from web4/game -> web4 -> ai-agents
    hrm_root = ai_agents_root / "HRM"

    if hrm_root.is_dir():
        sys.path.insert(0, str(hrm_root))

    try:
        from implementation.research_agent_driver import run_policy_once  # type: ignore
    except Exception as exc:  # pragma: no cover - defensive import
        raise RuntimeError(
            "Could not import HRM research_agent_driver. Ensure the HRM repo "
            "exists alongside web4 under the same parent directory."
        ) from exc

    return run_policy_once


def run_one_life_with_policy(steps: int = 20) -> Dict[str, Any]:
    """Run a single life and apply the HRM research agent policy once.

    Returns a combined JSON-serializable dict containing:
    - `life_summary`: raw output from `run_single_life`.
    - `policy_result`: agent metrics + proposed action from HRM.
    """

    life_summary = run_single_life(steps=steps)
    run_policy_once = _import_hrm_policy()
    policy_result = run_policy_once(life_summary)

    return {
        "life_summary": life_summary,
        "policy_result": policy_result,
    }


if __name__ == "__main__":
    combined = run_one_life_with_policy(steps=20)
    print(json.dumps(combined, indent=2, sort_keys=True))
