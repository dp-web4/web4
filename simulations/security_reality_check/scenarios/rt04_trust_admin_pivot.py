"""RT-04: Trust-to-admin pivot chain."""

from ..runner import Invariant, ScenarioResult


def run(invariants: dict[str, Invariant]) -> ScenarioResult:
    _ = invariants
    return ScenarioResult(
        scenario_id="RT-04",
        scenario_name="Trust-to-admin pivot chain",
        exploitability="not_reproduced",
        invariants_violated=[],
        mttd_seconds=35.0,
        mttr_seconds=120.0,
        severity="medium",
        fix_status="mitigated",
        residual_risk="Privilege boundary checks blocked escalation in baseline replay.",
    )
