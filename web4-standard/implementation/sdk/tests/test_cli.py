"""Tests for web4.__main__ CLI module.

Tests are split into two categories:
- In-process tests: call ``main(argv)`` directly so coverage tracks __main__.py
- Subprocess smoke tests (TestSmoke): run ``python -m web4`` in a child process
  to verify the entry point works end-to-end
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from typing import List

import pytest

from web4.__main__ import main, build_parser, _detect_schema


# ── Helpers ──────────────────────────────────────────────────────


def _make_json_file(data: object, suffix: str = ".json") -> str:
    """Write *data* to a temp file and return the path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    json.dump(data, f)
    f.close()
    return f.name


def _make_text_file(text: str, suffix: str = ".txt") -> str:
    """Write raw text to a temp file and return the path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    f.write(text)
    f.close()
    return f.name


# ── info subcommand (in-process) ─────────────────────────────────


class TestInfo:
    def test_info_shows_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["info"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "web4" in out
        assert "0.25.0" in out

    def test_info_shows_module_count(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["info"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Modules: 22" in out

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


# ── list-schemas subcommand (in-process) ─────────────────────────


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


# ── validate subcommand (in-process) ─────────────────────────────


class TestValidate:
    def test_valid_document(self, capsys: pytest.CaptureFixture[str]) -> None:
        from web4.trust import T3

        doc = T3(talent=0.8, training=0.7, temperament=0.9).to_jsonld()
        path = _make_json_file(doc)
        rc = main(["validate", path])
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out

    def test_valid_with_explicit_schema(self, capsys: pytest.CaptureFixture[str]) -> None:
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
        path = _make_json_file({"@type": "web4:LinkedContextToken"})
        rc = main(["validate", path, "--schema", "lct"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "INVALID" in out

    def test_file_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["validate", "/tmp/web4_nonexistent_file.json"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "not found" in err

    def test_invalid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        path = _make_text_file("not json at all")
        rc = main(["validate", path, "--schema", "lct"])
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
        path = _make_json_file({"key": "value"})
        rc = main(["validate", path])
        err = capsys.readouterr().err
        assert rc == 1
        assert "cannot detect" in err

    def test_non_object_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump([1, 2, 3], f)
        f.close()
        rc = main(["validate", f.name, "--schema", "lct"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "must be a JSON object" in err


# ── Schema auto-detection (in-process, no I/O) ──────────────────


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


# ── roundtrip subcommand (in-process) ────────────────────────────


class TestRoundtrip:
    def test_normalize_t3(self, capsys: pytest.CaptureFixture[str]) -> None:
        from web4.trust import T3

        doc = T3(talent=0.8, training=0.7, temperament=0.9).to_jsonld()
        path = _make_json_file(doc)
        rc = main(["roundtrip", path])
        out = capsys.readouterr().out
        assert rc == 0
        output = json.loads(out)
        assert output["@type"] == "T3Tensor"
        assert output["talent"] == 0.8

    def test_check_pass(self, capsys: pytest.CaptureFixture[str]) -> None:
        from web4.trust import V3

        doc = V3(valuation=0.5, veracity=0.6, validity=0.7).to_jsonld()
        path = _make_json_file(doc)
        rc = main(["roundtrip", "--check", path])
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out

    def test_check_mismatch(self, capsys: pytest.CaptureFixture[str]) -> None:
        from web4.trust import T3

        doc = T3(talent=0.8, training=0.7, temperament=0.9).to_jsonld()
        doc["extra_key"] = "should_be_lost"
        path = _make_json_file(doc)
        rc = main(["roundtrip", "--check", path])
        out = capsys.readouterr().out
        assert rc == 1
        assert "MISMATCH" in out

    def test_unknown_type(self, capsys: pytest.CaptureFixture[str]) -> None:
        doc = {"@type": "NotARealType", "data": 123}
        path = _make_json_file(doc)
        rc = main(["roundtrip", path])
        err = capsys.readouterr().err
        assert rc == 1
        assert "Unknown @type" in err

    def test_no_type(self, capsys: pytest.CaptureFixture[str]) -> None:
        path = _make_json_file({"key": "value"})
        rc = main(["roundtrip", path])
        err = capsys.readouterr().err
        assert rc == 1
        assert "no @type" in err

    def test_file_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["roundtrip", "/tmp/web4_nonexistent_roundtrip.json"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "not found" in err

    def test_invalid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        path = _make_text_file("{broken json")
        rc = main(["roundtrip", path])
        err = capsys.readouterr().err
        assert rc == 1
        assert "invalid JSON" in err

    def test_non_object_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump([1, 2, 3], f)
        f.close()
        rc = main(["roundtrip", f.name])
        err = capsys.readouterr().err
        assert rc == 1
        assert "must be a JSON object" in err

    def test_atp_account_roundtrip(self, capsys: pytest.CaptureFixture[str]) -> None:
        from web4.atp import ATPAccount

        acct = ATPAccount(available=80.0, locked=20.0)
        doc = acct.to_jsonld()
        path = _make_json_file(doc)
        rc = main(["roundtrip", "--check", path])
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out


# ── generate subcommand (in-process) ─────────────────────────────


class TestGenerate:
    def test_list_types(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["generate", "--list"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "T3Tensor" in out
        assert "R7Action" in out

    def test_generate_t3(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["generate", "T3Tensor"])
        out = capsys.readouterr().out
        assert rc == 0
        doc = json.loads(out)
        assert doc["@type"] == "T3Tensor"

    def test_generate_compact(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["generate", "T3Tensor", "--compact"])
        out = capsys.readouterr().out
        assert rc == 0
        # Compact output should be a single line
        assert "\n" not in out.strip()

    def test_generate_unknown_type(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["generate", "NotARealType"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "unknown type" in err.lower()

    def test_generate_no_type_arg(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["generate"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "type argument required" in err


# ── trust subcommand (in-process) ──────────────────────────────────


class TestTrust:
    def test_trust_with_flags(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["trust", "--actor", "lct:alice", "--target", "lct:bob", "--role", "analyst"])
        out = capsys.readouterr().out
        assert rc == 0
        doc = json.loads(out)
        assert doc["status"] == "APPROVED"
        assert doc["response"]["entity"] == "lct:bob"
        assert doc["response"]["role"] == "analyst"

    def test_trust_with_profile_roles(self, capsys: pytest.CaptureFixture[str]) -> None:
        roles = '{"analyst": {"talent": 0.8, "training": 0.9, "temperament": 0.7}}'
        rc = main(
            [
                "trust",
                "--actor",
                "lct:alice",
                "--target",
                "lct:bob",
                "--role",
                "analyst",
                "--profile-roles",
                roles,
            ]
        )
        out = capsys.readouterr().out
        assert rc == 0
        doc = json.loads(out)
        assert doc["status"] == "APPROVED"
        t3 = doc["response"]["t3_in_role"]
        # With range disclosure (default), T3 composite is returned
        assert "talent" in t3 or "composite" in t3

    def test_trust_precise_disclosure(self, capsys: pytest.CaptureFixture[str]) -> None:
        roles = '{"analyst": {"talent": 0.8, "training": 0.9, "temperament": 0.7}}'
        rc = main(
            [
                "trust",
                "--actor",
                "lct:alice",
                "--target",
                "lct:bob",
                "--role",
                "analyst",
                "--disclosure-level",
                "precise",
                "--profile-roles",
                roles,
            ]
        )
        out = capsys.readouterr().out
        assert rc == 0
        doc = json.loads(out)
        assert doc["status"] == "APPROVED"
        t3 = doc["response"]["t3_in_role"]
        assert t3["talent"] == 0.8

    def test_trust_binary_disclosure(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(
            [
                "trust",
                "--actor",
                "lct:alice",
                "--target",
                "lct:bob",
                "--role",
                "analyst",
                "--disclosure-level",
                "binary",
            ]
        )
        out = capsys.readouterr().out
        assert rc == 0
        doc = json.loads(out)
        assert doc["status"] == "APPROVED"
        # Binary disclosure does not reveal T3 dimensions
        assert doc["response"].get("t3_in_role") is None

    def test_trust_insufficient_atp(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(
            [
                "trust",
                "--actor",
                "lct:alice",
                "--target",
                "lct:bob",
                "--role",
                "analyst",
                "--atp-balance",
                "5",
            ]
        )
        out = capsys.readouterr().out
        assert rc == 0  # command succeeds, but query is rejected
        doc = json.loads(out)
        assert doc["status"] == "REJECTED"
        assert doc["error"]["code"] == "INSUFFICIENT_STAKE"

    def test_trust_compact_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(
            [
                "trust",
                "--actor",
                "lct:alice",
                "--target",
                "lct:bob",
                "--role",
                "analyst",
                "--compact",
            ]
        )
        out = capsys.readouterr().out
        assert rc == 0
        assert "\n" not in out.strip()

    def test_trust_missing_required_flags(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["trust"])
        err = capsys.readouterr().err
        assert rc == 1
        assert "--actor" in err

    def test_trust_from_json_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        query_doc = {
            "query": {
                "querier": "lct:alice",
                "target_entity": "lct:bob",
                "requested_role": "admin",
                "intended_interaction": "test",
                "atp_stake": 10,
                "validity_period": 3600,
            },
            "signature": "test-sig",
        }
        path = _make_json_file(query_doc)
        rc = main(["trust", "--file", path])
        out = capsys.readouterr().out
        assert rc == 0
        doc = json.loads(out)
        assert doc["status"] == "APPROVED"
        assert doc["response"]["role"] == "admin"

    def test_trust_invalid_json_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        path = _make_text_file("{broken json")
        rc = main(["trust", "--file", path])
        err = capsys.readouterr().err
        assert rc == 1
        assert "invalid JSON" in err

    def test_trust_invalid_query_in_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        path = _make_json_file({"not": "a trust query"})
        rc = main(["trust", "--file", path])
        err = capsys.readouterr().err
        assert rc == 1
        assert "invalid TrustQuery" in err

    def test_trust_invalid_disclosure_level(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(
            [
                "trust",
                "--actor",
                "lct:alice",
                "--target",
                "lct:bob",
                "--role",
                "analyst",
                "--disclosure-level",
                "invalid",
            ]
        )
        err = capsys.readouterr().err
        assert rc == 1
        assert "invalid disclosure level" in err.lower()

    def test_trust_invalid_profile_roles_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(
            [
                "trust",
                "--actor",
                "lct:alice",
                "--target",
                "lct:bob",
                "--role",
                "analyst",
                "--profile-roles",
                "{broken",
            ]
        )
        err = capsys.readouterr().err
        assert rc == 1
        assert "profile-roles" in err.lower() or "json" in err.lower()

    def test_trust_invalid_t3_in_profile_roles(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(
            [
                "trust",
                "--actor",
                "lct:alice",
                "--target",
                "lct:bob",
                "--role",
                "analyst",
                "--profile-roles",
                '{"analyst": "not-a-dict"}',
            ]
        )
        err = capsys.readouterr().err
        assert rc == 1
        assert "invalid T3" in err or "Error" in err


# ── Parser and help (in-process) ─────────────────────────────────


class TestParser:
    def test_no_args_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "web4" in out

    def test_build_parser_has_subcommands(self) -> None:
        parser = build_parser()
        # Parser should have all expected subcommands
        assert parser.prog == "web4"

    def test_help_mentions_roundtrip(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "roundtrip" in out


# ── selftest subcommand (in-process) ──────────────────────────────


class TestSelftest:
    def test_selftest_passes(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["selftest"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "OK" in out
        assert "22 modules" in out
        assert "23 types roundtripped" in out

    def test_selftest_verbose(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["selftest", "--verbose"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Modules: 22/22" in out
        assert "Schemas:" in out
        assert "Roundtrip: 23/23" in out
        assert "OK" in out

    def test_selftest_reports_import_failure(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Simulate a broken module to verify error reporting."""
        import importlib

        original_import = importlib.import_module

        def _broken_import(name: str, *args: object, **kwargs: object) -> object:
            if name == "web4.metabolic":
                raise ImportError("simulated failure")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(importlib, "import_module", _broken_import)
        rc = main(["selftest"])
        out = capsys.readouterr().out
        assert rc == 1
        assert "FAIL" in out
        assert "web4.metabolic" in out

    def test_selftest_short_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["selftest", "-v"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Modules:" in out


# ── Subprocess smoke tests (end-to-end entry point) ──────────────


def _run_cli(args: List[str]) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    """Run ``python -m web4`` in a subprocess and capture output."""
    return subprocess.run(
        [sys.executable, "-m", "web4"] + args,
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestSmoke:
    """Subprocess smoke tests verify the entry point works end-to-end."""

    def test_no_args(self) -> None:
        r = _run_cli([])
        assert r.returncode == 0
        assert "web4" in r.stdout

    def test_info(self) -> None:
        r = _run_cli(["info"])
        assert r.returncode == 0
        assert "0.25.0" in r.stdout

    def test_validate_valid_doc(self) -> None:
        from web4.trust import T3

        doc = T3(talent=0.8, training=0.7, temperament=0.9).to_jsonld()
        path = _make_json_file(doc)
        r = _run_cli(["validate", path])
        assert r.returncode == 0
        assert "OK" in r.stdout
