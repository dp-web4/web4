"""Tests for web4.__main__ CLI module."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from typing import List

import pytest

from web4.__main__ import main, build_parser, _detect_schema


# ── Helpers ──────────────────────────────────────────────────────


def run_cli(args: List[str]) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    """Run ``python -m web4`` in a subprocess and capture output."""
    return subprocess.run(
        [sys.executable, "-m", "web4"] + args,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _make_json_file(data: object, suffix: str = ".json") -> str:
    """Write *data* to a temp file and return the path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    json.dump(data, f)
    f.close()
    return f.name


# ── info subcommand ──────────────────────────────────────────────


class TestInfo:
    def test_info_shows_version(self) -> None:
        r = run_cli(["info"])
        assert r.returncode == 0
        assert "web4" in r.stdout
        assert "0.16.0" in r.stdout

    def test_info_shows_module_count(self) -> None:
        r = run_cli(["info"])
        assert "Modules: 20" in r.stdout

    def test_info_shows_export_count(self) -> None:
        r = run_cli(["info"])
        # At least 344 exports
        assert "Exports:" in r.stdout

    def test_info_shows_schema_count(self) -> None:
        r = run_cli(["info"])
        assert "Schemas:" in r.stdout


# ── list-schemas subcommand ──────────────────────────────────────


class TestListSchemas:
    def test_lists_all_schemas(self) -> None:
        r = run_cli(["list-schemas"])
        assert r.returncode == 0
        lines = r.stdout.strip().splitlines()
        assert len(lines) >= 12

    def test_contains_known_schemas(self) -> None:
        r = run_cli(["list-schemas"])
        for name in ["lct", "atp", "acp", "t3v3", "entity", "capability"]:
            assert name in r.stdout


# ── validate subcommand ──────────────────────────────────────────


class TestValidate:
    def test_valid_document(self) -> None:
        """Validate a T3 document (has @type for auto-detection)."""
        from web4.trust import T3

        doc = T3(talent=0.8, training=0.7, temperament=0.9).to_jsonld()
        path = _make_json_file(doc)
        r = run_cli(["validate", path])
        assert r.returncode == 0
        assert "OK" in r.stdout

    def test_valid_with_explicit_schema(self) -> None:
        """Validate LCT with --schema flag (LCT has no @type)."""
        from web4.lct import LCT, Binding
        from web4.entity import EntityType

        lct = LCT(
            lct_id="lct:test-cli-001",
            subject="agent:test",
            binding=Binding(
                entity_type=EntityType.AI,
                public_key="pk-test",
                created_at="2026-01-01T00:00:00Z",
            ),
        )
        path = _make_json_file(lct.to_jsonld())
        r = run_cli(["validate", path, "--schema", "lct"])
        assert r.returncode == 0
        assert "OK" in r.stdout

    def test_invalid_document(self) -> None:
        """Invalid document produces error output and exit code 1."""
        path = _make_json_file({"@type": "web4:LinkedContextToken"})
        r = run_cli(["validate", path, "--schema", "lct"])
        assert r.returncode == 1
        assert "INVALID" in r.stdout

    def test_file_not_found(self) -> None:
        r = run_cli(["validate", "/tmp/web4_nonexistent_file.json"])
        assert r.returncode == 1
        assert "not found" in r.stderr

    def test_invalid_json(self) -> None:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        f.write("not json at all")
        f.close()
        r = run_cli(["validate", f.name, "--schema", "lct"])
        assert r.returncode == 1
        assert "invalid JSON" in r.stderr

    def test_unknown_schema(self) -> None:
        path = _make_json_file({"key": "value"})
        r = run_cli(["validate", path, "--schema", "nonexistent"])
        assert r.returncode == 1
        assert "Error" in r.stderr

    def test_no_type_no_schema_flag(self) -> None:
        """Document without @type and no --schema flag gives clear error."""
        path = _make_json_file({"key": "value"})
        r = run_cli(["validate", path])
        assert r.returncode == 1
        assert "cannot detect" in r.stderr

    def test_non_object_json(self) -> None:
        """JSON array (not object) is rejected."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump([1, 2, 3], f)
        f.close()
        r = run_cli(["validate", f.name, "--schema", "lct"])
        assert r.returncode == 1
        assert "must be a JSON object" in r.stderr


# ── Schema auto-detection ────────────────────────────────────────


class TestDetectSchema:
    def test_detect_t3(self) -> None:
        assert _detect_schema({"@type": "T3Tensor"}) == "t3v3"

    def test_detect_v3(self) -> None:
        assert _detect_schema({"@type": "V3Tensor"}) == "t3v3"

    def test_detect_prefixed(self) -> None:
        assert _detect_schema({"@type": "web4:R7Action"}) == "r7-action"

    def test_detect_list_type(self) -> None:
        assert _detect_schema({"@type": ["Thing", "ATPAccount"]}) == "atp"

    def test_detect_unknown(self) -> None:
        assert _detect_schema({"@type": "UnknownType"}) is None

    def test_detect_no_type(self) -> None:
        assert _detect_schema({"key": "value"}) is None


# ── Parser and help ──────────────────────────────────────────────


class TestParser:
    def test_no_args_shows_help(self) -> None:
        r = run_cli([])
        assert r.returncode == 0
        assert "web4" in r.stdout

    def test_help_flag(self) -> None:
        r = run_cli(["--help"])
        assert r.returncode == 0
        assert "validate" in r.stdout
        assert "info" in r.stdout
        assert "list-schemas" in r.stdout
