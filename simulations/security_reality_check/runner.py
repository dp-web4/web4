"""Security Reality Check v1 runner.

Minimal execution harness for replay scenarios and invariant-based scorecards.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Callable, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class Invariant:
    """Invariant definition for scorecard evaluation."""

    invariant_id: str
    name: str
    description: str


@dataclass(frozen=True)
class ScenarioResult:
    """Single scenario execution output."""

    scenario_id: str
    scenario_name: str
    exploitability: str
    invariants_violated: List[str]
    mttd_seconds: Optional[float]
    mttr_seconds: Optional[float]
    severity: str
    fix_status: str
    residual_risk: str


def _load_invariants(invariant_file: Path) -> Dict[str, Invariant]:
    """Load a very small subset of YAML needed for invariants.

    Prefers PyYAML when available. Falls back to a tiny parser for this file shape
    so no extra dependency is required for basic operation.
    """

    text = invariant_file.read_text(encoding="utf-8")

    try:
        import yaml  # type: ignore

        payload = yaml.safe_load(text)
        rows = payload.get("invariants", [])
        return {
            row["id"]: Invariant(
                invariant_id=row["id"],
                name=row["name"],
                description=row["description"],
            )
            for row in rows
        }
    except Exception:
        pass

    # Fallback parser for this specific structure:
    # - id: ...
    #   name: ...
    #   description: ...
    rows: List[Dict[str, str]] = []
    current: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("- id:"):
            if current:
                rows.append(current)
            current = {"id": line.split(":", 1)[1].strip()}
        elif line.startswith("name:"):
            current["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("description:"):
            current["description"] = line.split(":", 1)[1].strip()
    if current:
        rows.append(current)

    return {
        row["id"]: Invariant(
            invariant_id=row["id"],
            name=row.get("name", ""),
            description=row.get("description", ""),
        )
        for row in rows
    }


def _validate_result(result: ScenarioResult, invariants: Dict[str, Invariant]) -> None:
    valid_exploitability = {"confirmed", "partial", "not_reproduced"}
    valid_severity = {"critical", "high", "medium", "low"}
    valid_fix_status = {"open", "mitigated", "retest_passed"}

    if result.exploitability not in valid_exploitability:
        raise ValueError(f"Invalid exploitability: {result.exploitability}")
    if result.severity not in valid_severity:
        raise ValueError(f"Invalid severity: {result.severity}")
    if result.fix_status not in valid_fix_status:
        raise ValueError(f"Invalid fix_status: {result.fix_status}")

    missing = [inv for inv in result.invariants_violated if inv not in invariants]
    if missing:
        raise ValueError(f"Unknown invariant ids: {missing}")


def _aggregate(results: Iterable[ScenarioResult]) -> Dict[str, object]:
    rows = list(results)
    by_severity: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    confirmed_exploits = 0

    for result in rows:
        by_severity[result.severity] += 1
        if result.exploitability == "confirmed":
            confirmed_exploits += 1

    unresolved_high_critical = [
        r.scenario_id
        for r in rows
        if r.severity in {"critical", "high"} and r.fix_status != "retest_passed"
    ]

    return {
        "total_scenarios_executed": len(rows),
        "confirmed_exploit_count": confirmed_exploits,
        "by_severity": by_severity,
        "unresolved_high_or_critical": unresolved_high_critical,
    }


def run_scenarios(
    scenario_functions: Dict[str, Callable[[Dict[str, Invariant]], ScenarioResult]],
    invariant_file: Path | None = None,
    output_dir: Path | None = None,
) -> Dict[str, object]:
    """Run scenario callables and write JSON + markdown scorecards.

    Args:
        scenario_functions: Mapping of scenario id to callable.
        invariant_file: Optional path override for invariants yaml.
        output_dir: Optional output path for reports.

    Returns:
        Serialized payload used for report generation.
    """

    base_dir = Path(__file__).resolve().parent
    invariant_path = invariant_file or (base_dir / "invariants.yaml")
    report_dir = output_dir or (base_dir / "reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    invariants = _load_invariants(invariant_path)

    scenario_results: List[ScenarioResult] = []
    for scenario_id, scenario_fn in scenario_functions.items():
        result = scenario_fn(invariants)
        if result.scenario_id != scenario_id:
            raise ValueError(
                f"Scenario function id mismatch: expected {scenario_id}, got {result.scenario_id}"
            )
        _validate_result(result, invariants)
        scenario_results.append(result)

    aggregate = _aggregate(scenario_results)
    timestamp = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at": timestamp,
        "invariants": [asdict(i) for i in invariants.values()],
        "results": [asdict(r) for r in scenario_results],
        "aggregate": aggregate,
    }

    json_path = report_dir / "security_reality_check_report.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md_lines = [
        "# Security Reality Check Report",
        "",
        f"Generated at: `{timestamp}`",
        "",
        "## Aggregate",
        f"- Total scenarios executed: {aggregate['total_scenarios_executed']}",
        f"- Confirmed exploit count: {aggregate['confirmed_exploit_count']}",
        f"- Severity distribution: {aggregate['by_severity']}",
        f"- Unresolved high/critical: {aggregate['unresolved_high_or_critical']}",
        "",
        "## Scenario Results",
        "",
        "| Scenario | Exploitability | Severity | Fix Status | Invariants Violated |",
        "|---|---|---|---|---|",
    ]

    for row in scenario_results:
        inv = ", ".join(row.invariants_violated) if row.invariants_violated else "none"
        md_lines.append(
            f"| {row.scenario_id} ({row.scenario_name}) | {row.exploitability} | {row.severity} | {row.fix_status} | {inv} |"
        )

    md_path = report_dir / "security_reality_check_report.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return payload
