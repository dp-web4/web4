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


# ── info subcommand (in-process) ────────────────────────────────


class TestInfo:
    def test_info_shows_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        import web4

        rc = main(["info"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "web4" in out
        assert web4.__version__ in out

    def test_info_shows_module_count(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["info"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Modules: 20" in out

    def test_info_shows_export_count(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["info"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Exports:" in out

    def test_info_shows_schema_count(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["info"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Schemas:" in out


# ── list-schemas subcommand (in-process) ────────────────────────


class TestListSchemas:
    def test_lists_all_schemas(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["list-schemas"])
        out = capsys.readouterr().out
        assert rc == 0
        lines = out.strip().splitlines()
        assert len(lines) >= 12

    def test_contains_known_schemas(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["list-schemas"])
        out = capsys.readouterr().out
        assert rc == 0
        for name in ["lct", "atp", "acp", "t3v3", "entity", "capability"]:
            assert name in out


# ── validate subcommand (in-process) ────────────────────────────


class TestValidate:
    def test_valid_document(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Validate a T3 document (has @type for auto-detection)."""
        from web4.trust import T3

        doc = T3(talent=0.8, training=0.7, temperament=0.9).to_jsonld()
        path = _make_json_file(doc)
        rc = main(["validate", path])
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out

    def test_valid_with_explicit_schema(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
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
        rc = main(["validate", path, "--schema", "lct"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out

    def test_invalid_document(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Invalid document produces error output and exit code 1."""
        path = _make_json_file({"@type": "web4:LinkedContextToken"})
        rc = main(["validate", path, "--schema", "lct"])
        captured = capsys.readouterr()
        assert rc == 1
        assert "INVALID" in captured.out

    def test_file_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["validate", "/tmp/web4_nonexistent_file.json"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "not found" in err

    def test_invalid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        f.write("not json at all")
        f.close()
        rc = main(["validate", f.name, "--schema", "lct"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "invalid JSON" in err

    def test_unknown_schema(self, capsys: pytest.CaptureFixture[str]) -> None:
        path = _make_json_file({"key": "value"})
        rc = main(["validate", path, "--schema", "nonexistent"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "Error" in err

    def test_no_type_no_schema_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Document without @type and no --schema flag gives clear error."""
        path = _make_json_file({"key": "value"})
        rc = main(["validate", path])
        err = capsys.readouterr().err
        assert rc == 1
        assert "cannot detect" in err

    def test_non_object_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        """JSON array (not object) is rejected."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump([1, 2, 3], f)
        f.close()
        rc = main(["validate", f.name, "--schema", "lct"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "must be a JSON object" in err

    def test_stdin_input(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Validate from stdin using '-' as file path."""
        from web4.trust import T3
        import io

        doc = T3(talent=0.5, training=0.6, temperament=0.7).to_jsonld()
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(doc)))
        rc = main(["validate", "-"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out


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


# ── Parser and help (in-process) ────────────────────────────────


class TestParser:
    def test_no_args_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "web4" in out

    def test_help_flag(self) -> None:
        """--help calls sys.exit(0), so use subprocess for this one."""
        r = run_cli(["--help"])
        assert r.returncode == 0
        assert "validate" in r.stdout
        assert "info" in r.stdout
        assert "list-schemas" in r.stdout

    def test_build_parser_returns_parser(self) -> None:
        import argparse

        p = build_parser()
        assert isinstance(p, argparse.ArgumentParser)


# ── End-to-end subprocess smoke tests ────────────────────────────


class TestSubprocessSmoke:
    """A few subprocess tests to verify the module runs as ``python -m web4``."""

    def test_module_invocation(self) -> None:
        r = run_cli(["info"])
        assert r.returncode == 0
        assert "web4" in r.stdout

    def test_validate_roundtrip(self) -> None:
        from web4.trust import T3

        doc = T3(talent=0.8, training=0.7, temperament=0.9).to_jsonld()
        path = _make_json_file(doc)
        r = run_cli(["validate", path])
        assert r.returncode == 0
        assert "OK" in r.stdout

    def test_list_schemas_subprocess(self) -> None:
        r = run_cli(["list-schemas"])
        assert r.returncode == 0
        assert "lct" in r.stdout
