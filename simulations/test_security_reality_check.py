from pathlib import Path

from simulations.security_reality_check.runner import run_scenarios
from simulations.security_reality_check.scenarios import SCENARIOS


def test_security_reality_check_runs(tmp_path: Path) -> None:
    payload = run_scenarios(SCENARIOS, output_dir=tmp_path)

    assert payload["aggregate"]["total_scenarios_executed"] == 4
    assert payload["aggregate"]["confirmed_exploit_count"] >= 1

    json_report = tmp_path / "security_reality_check_report.json"
    md_report = tmp_path / "security_reality_check_report.md"

    assert json_report.exists()
    assert md_report.exists()
    assert "RT-02" in md_report.read_text(encoding="utf-8")
