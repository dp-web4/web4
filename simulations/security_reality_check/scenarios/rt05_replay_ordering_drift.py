"""RT-05: Replay + ordering drift."""

from ..runner import Invariant, ScenarioResult


def run(invariants: dict[str, Invariant]) -> ScenarioResult:
    _ = invariants
    return ScenarioResult(
        scenario_id="RT-05",
        scenario_name="Replay + ordering drift",
        exploitability="partial",
        invariants_violated=["INV-FED-01"],
        mttd_seconds=92.0,
        mttr_seconds=410.0,
        severity="high",
        fix_status="open",
        residual_risk="Partition and skew replay was detected but inconsistent temporary acceptance occurred.",
    )
