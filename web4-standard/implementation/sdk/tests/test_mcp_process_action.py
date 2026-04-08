"""Tests for web4_process_action MCP tool — action → consequence pipeline.

Tests the MCP wrapper around process_action_outcome(), validating JSON-in/JSON-out
contract, error handling, and integration with the MCP call mechanism.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

import pytest

from web4.mcp_server import mcp, web4_process_action


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _call_tool(name: str, arguments: Dict[str, Any] | None = None) -> Any:
    """Call an MCP tool synchronously and return the structured result."""
    if arguments is None:
        arguments = {}
    content_blocks, extra = asyncio.run(mcp.call_tool(name, arguments))
    return extra["result"]


def _make_rules_json(
    *,
    action_type: str = "data_analysis",
    result_status: str = "success",
    talent_delta: float = 0.05,
    training_delta: float = 0.03,
    veracity_delta: float = 0.02,
) -> str:
    """Build a reputation rules JSON array string for testing."""
    return json.dumps([{
        "rule_id": "R001",
        "trigger_conditions": {
            "action_type": action_type,
            "result_status": result_status,
        },
        "t3_impacts": {
            "talent": {"base_delta": talent_delta, "modifiers": []},
            "training": {"base_delta": training_delta, "modifiers": []},
        },
        "v3_impacts": {
            "veracity": {"base_delta": veracity_delta, "modifiers": []},
        },
    }])


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


class TestSuccessPath:
    """Tests for successful action outcomes via the MCP tool."""

    def test_basic_success(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="success",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules=_make_rules_json(),
            profile_roles=json.dumps({
                "web4:DataAnalyst": {"talent": 0.7, "training": 0.8, "temperament": 0.9},
            }),
        )
        assert "error" not in result
        assert result["atp_committed"] == 10.0
        assert result["atp_rolled_back"] == 0.0
        assert result["delta"] is not None

    def test_t3_updated(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="success",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules=_make_rules_json(talent_delta=0.05),
            profile_roles=json.dumps({
                "web4:DataAnalyst": {"talent": 0.7, "training": 0.8, "temperament": 0.9},
            }),
        )
        # Engine evaluates delta from the R7Action's role T3 (default 0.5),
        # but process_action_outcome applies delta to TrustProfile (0.7).
        # Delta: talent from_value=0.5 → to_value=0.55, change=+0.05
        # Applied to profile: to_value = 0.55 (the delta's to_value overwrites)
        assert result["updated_t3"]["talent"] == pytest.approx(0.55, abs=1e-6)

    def test_v3_updated(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="success",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules=_make_rules_json(veracity_delta=0.02),
            profile_roles=json.dumps({
                "web4:DataAnalyst": {"talent": 0.7, "training": 0.8, "temperament": 0.9},
            }),
        )
        # Veracity defaults to 0.5 (no V3 set), +0.02 = 0.52
        assert result["updated_v3"]["veracity"] == pytest.approx(0.52, abs=1e-6)

    def test_custom_atp_stake(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="success",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules=_make_rules_json(),
            atp_stake=25.0,
        )
        assert result["atp_committed"] == 25.0
        assert result["atp_rolled_back"] == 0.0


# ---------------------------------------------------------------------------
# Failure path
# ---------------------------------------------------------------------------


class TestFailurePath:
    """Tests for failed action outcomes — ATP rollback."""

    def test_failure_rolls_back_atp(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="failure",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules=_make_rules_json(),
            atp_stake=10.0,
        )
        # Rules trigger on success, so delta is None for failure
        assert result["delta"] is None
        assert result["atp_rolled_back"] == 10.0
        assert result["atp_committed"] == 0.0

    def test_failure_no_t3_change(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="failure",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules=_make_rules_json(),
            profile_roles=json.dumps({
                "web4:DataAnalyst": {"talent": 0.7, "training": 0.8, "temperament": 0.9},
            }),
        )
        # No rule matched → T3 unchanged
        assert result["updated_t3"]["talent"] == pytest.approx(0.7, abs=1e-6)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Tests for input validation and error paths."""

    def test_invalid_status(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="pending",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules="[]",
        )
        assert "error" in result
        assert "success" in result["error"] and "failure" in result["error"]

    def test_invalid_rules_json(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="success",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules="not json",
        )
        assert "error" in result
        assert "Invalid rules JSON" in result["error"]

    def test_rules_not_array(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="success",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules='{"not": "array"}',
        )
        assert "error" in result
        assert "array" in result["error"]

    def test_invalid_rule_data(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="success",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules='[{"missing": "rule_id"}]',
        )
        assert "error" in result
        assert "Invalid rule" in result["error"]

    def test_invalid_profile_roles_json(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="success",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules="[]",
            profile_roles="not json",
        )
        assert "error" in result
        assert "Invalid profile_roles JSON" in result["error"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for boundary conditions."""

    def test_no_matching_rules(self) -> None:
        """No rules match → delta is None, T3 unchanged."""
        result = web4_process_action(
            action_type="code_review",
            status="success",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules=_make_rules_json(action_type="data_analysis"),  # wrong type
        )
        assert result["delta"] is None
        assert result["atp_committed"] == 10.0  # ATP still settles

    def test_empty_rules(self) -> None:
        """Empty rules → no delta, ATP settles normally."""
        result = web4_process_action(
            action_type="data_analysis",
            status="success",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules="[]",
        )
        assert result["delta"] is None
        assert result["atp_committed"] == 10.0

    def test_zero_atp_stake(self) -> None:
        result = web4_process_action(
            action_type="data_analysis",
            status="success",
            actor="lct:alice",
            role="web4:DataAnalyst",
            rules=_make_rules_json(),
            atp_stake=0.0,
        )
        assert result["atp_committed"] == 0.0
        assert result["atp_rolled_back"] == 0.0


# ---------------------------------------------------------------------------
# MCP call integration
# ---------------------------------------------------------------------------


class TestMCPIntegration:
    """Tests that the tool works through the MCP call mechanism."""

    def test_via_mcp_call(self) -> None:
        result = _call_tool("web4_process_action", {
            "action_type": "data_analysis",
            "status": "success",
            "actor": "lct:alice",
            "role": "web4:DataAnalyst",
            "rules": _make_rules_json(),
            "profile_roles": json.dumps({
                "web4:DataAnalyst": {"talent": 0.7, "training": 0.8, "temperament": 0.9},
            }),
        })
        assert "error" not in result
        assert result["atp_committed"] == 10.0
        assert result["delta"] is not None
