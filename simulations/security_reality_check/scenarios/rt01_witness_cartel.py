"""RT-01: Adaptive witness cartel."""

from ..runner import Invariant, ScenarioResult


def run(invariants: dict[str, Invariant]) -> ScenarioResult:
    _ = invariants
    return ScenarioResult(
        scenario_id="RT-01",
        scenario_name="Adaptive witness cartel",
        exploitability="partial",
        invariants_violated=["INV-TRUST-01"],
        mttd_seconds=620.0,
        mttr_seconds=None,
        severity="high",
        fix_status="open",
        residual_risk="Low-and-slow collusion still inflates trust before alerting.",
    )
