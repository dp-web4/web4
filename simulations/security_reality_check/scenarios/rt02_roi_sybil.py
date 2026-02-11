"""RT-02: ROI-positive Sybil economy."""

from ..runner import Invariant, ScenarioResult


def run(invariants: dict[str, Invariant]) -> ScenarioResult:
    _ = invariants
    return ScenarioResult(
        scenario_id="RT-02",
        scenario_name="ROI-positive Sybil economy",
        exploitability="confirmed",
        invariants_violated=["INV-ATP-01", "INV-TRUST-01"],
        mttd_seconds=None,
        mttr_seconds=None,
        severity="critical",
        fix_status="open",
        residual_risk="Attacker achieves sustained positive ATP return under constrained budget assumptions.",
    )
