"""
``python -m web4`` — command-line interface for the Web4 SDK.

Subcommands::

    python -m web4 info               # Show SDK version, modules, exports
    python -m web4 list-schemas       # List available JSON Schemas
    python -m web4 validate F.json    # Validate a JSON-LD document
    python -m web4 roundtrip F.json   # Deserialize + re-serialize (normalize)
    python -m web4 roundtrip --check  # Verify round-trip fidelity
    python -m web4 generate T3Tensor  # Generate a minimal valid JSON-LD document
    python -m web4 selftest           # Verify SDK installation
    python -m web4 trust Q.json       # Evaluate a trust query from JSON file
    python -m web4 trust --actor A --target B --role R  # Quick trust evaluation
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List, Optional, Sequence


def _cmd_info(args: argparse.Namespace) -> int:
    """Display SDK version, module count, and export count."""
    import web4

    modules = [
        "trust",
        "lct",
        "atp",
        "federation",
        "r6",
        "mrh",
        "acp",
        "dictionary",
        "entity",
        "capability",
        "errors",
        "metabolic",
        "binding",
        "society",
        "reputation",
        "security",
        "protocol",
        "mcp",
        "attestation",
        "validation",
        "deserialize",
        "generate",
    ]

    print(f"web4 {web4.__version__}")
    print(f"Modules: {len(modules)}")
    print(f"Exports: {len(web4.__all__)}")

    # Show available schemas if validation module can locate them
    try:
        from web4.validation import list_schemas

        schemas = list_schemas()
        print(f"Schemas: {len(schemas)}")
    except Exception:
        print("Schemas: unavailable (schema directory not found)")

    return 0


def _cmd_list_schemas(args: argparse.Namespace) -> int:
    """List all available JSON Schemas."""
    from web4.validation import list_schemas

    schemas = list_schemas()
    for name in schemas:
        print(name)

    return 0


def _read_json_doc(
    file_path: str,
) -> "tuple[Dict[str, object], None] | tuple[None, int]":
    """Read and parse a JSON object from *file_path* (or ``-`` for stdin).

    Returns ``(doc, None)`` on success or ``(None, exit_code)`` on failure
    (error already printed to stderr).
    """
    try:
        if file_path == "-":
            raw = sys.stdin.read()
        else:
            with open(file_path) as f:
                raw = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        return None, 1
    except OSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return None, 1

    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON: {exc}", file=sys.stderr)
        return None, 1

    if not isinstance(doc, dict):
        print("Error: document must be a JSON object", file=sys.stderr)
        return None, 1

    return doc, None


def _cmd_validate(args: argparse.Namespace) -> int:
    """Validate a JSON-LD document against a Web4 JSON Schema."""
    file_path: str = args.file
    schema_name: Optional[str] = args.schema

    doc, err = _read_json_doc(file_path)
    if doc is None:
        return err  # type: ignore[return-value]

    # Auto-detect schema from @type if not specified
    if schema_name is None:
        schema_name = _detect_schema(doc)
        if schema_name is None:
            print(
                "Error: cannot detect schema type. Use --schema to specify (e.g. --schema lct).",
                file=sys.stderr,
            )
            return 1

    # Validate
    from web4.validation import validate, SchemaNotFound, SchemaValidationUnavailable

    try:
        result = validate(doc, schema_name)
    except SchemaValidationUnavailable:
        print(
            "Error: jsonschema package not installed. Install with: pip install 'web4[validation]'",
            file=sys.stderr,
        )
        return 1
    except SchemaNotFound as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if result.valid:
        print(f"OK: valid {schema_name} document")
        return 0
    else:
        print(f"INVALID: {len(result.errors)} error(s) against {schema_name} schema")
        for validation_err in result.errors:
            print(f"  - {validation_err}")
        return 1


# ── roundtrip subcommand ───────────────────────────────────────


def _cmd_roundtrip(args: argparse.Namespace) -> int:
    """Deserialize a JSON-LD document and re-serialize it."""
    file_path: str = args.file
    check: bool = args.check

    doc, err = _read_json_doc(file_path)
    if doc is None:
        return err  # type: ignore[return-value]

    from web4.deserialize import from_jsonld, UnknownTypeError

    try:
        obj = from_jsonld(doc)
    except (UnknownTypeError, ValueError, TypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not hasattr(obj, "to_jsonld"):
        type_val = doc.get("@type", "<unknown>")
        print(
            f"Error: {type_val} does not support re-serialization (no to_jsonld method on {type(obj).__name__})",
            file=sys.stderr,
        )
        return 1

    roundtripped: Dict[str, object] = obj.to_jsonld()

    if check:
        if roundtripped == doc:
            print("OK: round-trip preserves document")
            return 0
        # Report differences
        print("MISMATCH: round-trip produced a different document")
        _report_diff(doc, roundtripped)
        return 1

    # Default: print the normalized (re-serialized) document
    print(json.dumps(roundtripped, indent=2))
    return 0


def _report_diff(
    original: Dict[str, object],
    roundtripped: Dict[str, object],
) -> None:
    """Print a human-readable diff between two dicts."""
    all_keys = sorted(set(list(original.keys()) + list(roundtripped.keys())))
    for key in all_keys:
        in_orig = key in original
        in_rt = key in roundtripped
        if in_orig and not in_rt:
            print(f"  - {key}: {original[key]!r}  (removed)")
        elif in_rt and not in_orig:
            print(f"  + {key}: {roundtripped[key]!r}  (added)")
        elif original[key] != roundtripped[key]:
            print(f"  ~ {key}: {original[key]!r} -> {roundtripped[key]!r}")


# ── generate subcommand ───────────────────────────────────────


def _cmd_generate(args: argparse.Namespace) -> int:
    """Generate a minimal valid JSON-LD document for a given type."""
    from web4.generate import UnsupportedTypeError, available_types, generate

    if args.list_types:
        for t in available_types():
            print(t)
        return 0

    if args.type is None:
        print("Error: type argument required (or use --list)", file=sys.stderr)
        return 1

    type_name: str = args.type
    compact: bool = args.compact

    try:
        doc = generate(type_name)
    except UnsupportedTypeError:
        print(f"Error: unknown type {type_name!r}", file=sys.stderr)
        print(f"Available types: {', '.join(available_types())}", file=sys.stderr)
        return 1

    indent = None if compact else 2
    print(json.dumps(doc, indent=indent))
    return 0


# ── selftest subcommand ───────────────────────────────────────


_SELFTEST_MODULES: List[str] = [
    "trust",
    "lct",
    "atp",
    "federation",
    "r6",
    "mrh",
    "acp",
    "dictionary",
    "entity",
    "capability",
    "errors",
    "metabolic",
    "binding",
    "society",
    "reputation",
    "security",
    "protocol",
    "mcp",
    "attestation",
    "validation",
    "deserialize",
    "generate",
]


def _cmd_selftest(args: argparse.Namespace) -> int:
    """Verify SDK installation: imports, schemas, and round-trip fidelity."""
    import importlib

    errors: List[str] = []
    verbose: bool = args.verbose

    # 1. Module imports
    imported = 0
    for mod_name in _SELFTEST_MODULES:
        try:
            importlib.import_module(f"web4.{mod_name}")
            imported += 1
        except Exception as exc:
            errors.append(f"import web4.{mod_name}: {exc}")

    if verbose:
        print(f"Modules: {imported}/{len(_SELFTEST_MODULES)} imported")

    # 2. Schema registry
    schema_count = 0
    try:
        from web4.validation import list_schemas

        schemas = list_schemas()
        schema_count = len(schemas)
        if verbose:
            print(f"Schemas: {schema_count} loaded")
    except Exception as exc:
        errors.append(f"schema registry: {exc}")

    # 3. Generate + round-trip for each dispatcher type
    try:
        from web4.generate import available_types, generate
        from web4.deserialize import from_jsonld

        types = available_types()
        passed = 0
        for type_name in types:
            try:
                doc = generate(type_name)
                obj = from_jsonld(doc)
                if hasattr(obj, "to_jsonld"):
                    rt_doc = obj.to_jsonld()
                    if rt_doc != doc:
                        errors.append(f"roundtrip {type_name}: output differs from input")
                    else:
                        passed += 1
                else:
                    # Function-based types (no to_jsonld method) — import OK
                    passed += 1
            except Exception as exc:
                errors.append(f"roundtrip {type_name}: {exc}")

        if verbose:
            print(f"Roundtrip: {passed}/{len(types)} types passed")
    except Exception as exc:
        errors.append(f"generate/roundtrip setup: {exc}")

    # Summary
    if errors:
        print(f"FAIL: {len(errors)} error(s)")
        for err in errors:
            print(f"  - {err}")
        return 1

    total_types = len(types) if "types" in dir() else 0
    print(f"OK: {imported} modules, {schema_count} schemas, {total_types} types roundtripped")
    return 0


# ── trust subcommand ─────────────────────────────────────────


def _cmd_trust(args: argparse.Namespace) -> int:
    """Evaluate a trust query against a profile with ATP stake locking."""
    from web4.atp import ATPAccount
    from web4.trust import (
        DisclosureLevel,
        T3,
        TrustProfile,
        TrustQuery,
        evaluate_trust_query,
    )

    # If --file provided, read query from JSON file/stdin
    file_path: Optional[str] = args.file
    if file_path is not None:
        doc, err = _read_json_doc(file_path)
        if doc is None:
            return err  # type: ignore[return-value]
        try:
            query = TrustQuery.from_dict(doc)
        except (KeyError, ValueError, TypeError) as exc:
            print(f"Error: invalid TrustQuery: {exc}", file=sys.stderr)
            return 1
    else:
        # Build query from CLI flags
        actor: Optional[str] = args.actor
        target: Optional[str] = args.target
        role: Optional[str] = args.role
        if not all([actor, target, role]):
            print(
                "Error: --actor, --target, and --role are required (or use --file to provide a JSON query)",
                file=sys.stderr,
            )
            return 1
        # These assertions are safe — we checked all() above
        assert actor is not None
        assert target is not None
        assert role is not None
        dl_str: str = args.disclosure_level
        try:
            dl = DisclosureLevel(dl_str)
        except ValueError:
            valid = ", ".join(d.value for d in DisclosureLevel)
            print(f"Error: invalid disclosure level {dl_str!r}. Valid: {valid}", file=sys.stderr)
            return 1
        query = TrustQuery(
            querier=actor,
            target_entity=target,
            requested_role=role,
            intended_interaction=args.interaction,
            atp_stake=args.stake,
            validity_period=args.validity,
            signature="cli-generated",
            disclosure_level=dl,
        )

    # Build target profile from --profile-roles JSON if provided
    profile = TrustProfile(query.target_entity)
    roles_json: Optional[str] = args.profile_roles
    if roles_json is not None:
        try:
            roles_dict = json.loads(roles_json)
        except json.JSONDecodeError as exc:
            print(f"Error: invalid --profile-roles JSON: {exc}", file=sys.stderr)
            return 1
        for role_name, t3_data in roles_dict.items():
            try:
                profile.set_role(role_name, T3.from_dict(t3_data))
            except (KeyError, ValueError, TypeError, AttributeError) as exc:
                print(f"Error: invalid T3 for role {role_name!r}: {exc}", file=sys.stderr)
                return 1

    # Build requester ATP account
    atp_balance: float = args.atp_balance
    account = ATPAccount(available=atp_balance)

    # Evaluate
    response = evaluate_trust_query(query, profile, account)
    indent = None if args.compact else 2
    print(json.dumps(response.to_dict(), indent=indent))
    return 0


# ── Schema auto-detection ──────────────────────────────────────

# @type value -> schema name mapping
_TYPE_TO_SCHEMA = {
    "web4:LinkedContextToken": "lct",
    "LinkedContextToken": "lct",
    "web4:AttestationEnvelope": "attestation-envelope",
    "AttestationEnvelope": "attestation-envelope",
    "web4:T3Tensor": "t3v3",
    "T3Tensor": "t3v3",
    "web4:V3Tensor": "t3v3",
    "V3Tensor": "t3v3",
    "web4:ATPAccount": "atp",
    "ATPAccount": "atp",
    "web4:TransferResult": "atp",
    "TransferResult": "atp",
    "web4:AgentPlan": "acp",
    "AgentPlan": "acp",
    "web4:Intent": "acp",
    "Intent": "acp",
    "web4:Decision": "acp",
    "Decision": "acp",
    "web4:ExecutionRecord": "acp",
    "ExecutionRecord": "acp",
    "web4:EntityTypeInfo": "entity",
    "EntityTypeInfo": "entity",
    "web4:EntityTypeRegistry": "entity",
    "EntityTypeRegistry": "entity",
    "web4:LevelRequirement": "capability",
    "LevelRequirement": "capability",
    "web4:CapabilityAssessment": "capability",
    "CapabilityAssessment": "capability",
    "web4:CapabilityFramework": "capability",
    "CapabilityFramework": "capability",
    "web4:DictionarySpec": "dictionary",
    "DictionarySpec": "dictionary",
    "web4:TranslationResult": "dictionary",
    "TranslationResult": "dictionary",
    "web4:TranslationChain": "dictionary",
    "TranslationChain": "dictionary",
    "web4:DictionaryEntity": "dictionary",
    "DictionaryEntity": "dictionary",
    "web4:R7Action": "r7-action",
    "R7Action": "r7-action",
    "web4:TrustQuery": "trust-query",
    "TrustQuery": "trust-query",
}


def _detect_schema(doc: dict) -> Optional[str]:  # type: ignore[type-arg]
    """Detect the schema name from the document's @type field."""
    type_val = doc.get("@type")
    if isinstance(type_val, str):
        return _TYPE_TO_SCHEMA.get(type_val)
    if isinstance(type_val, list):
        for t in type_val:
            if isinstance(t, str):
                schema = _TYPE_TO_SCHEMA.get(t)
                if schema is not None:
                    return schema
    return None


# ── Argument parser ────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="web4",
        description="Web4 SDK command-line tools",
    )
    sub = parser.add_subparsers(dest="command")

    # info
    sub.add_parser("info", help="Show SDK version, modules, and exports")

    # list-schemas
    sub.add_parser("list-schemas", help="List available JSON Schemas")

    # validate
    p_val = sub.add_parser("validate", help="Validate a JSON-LD document")
    p_val.add_argument("file", help="Path to JSON file (or '-' for stdin)")
    p_val.add_argument(
        "--schema",
        default=None,
        help="Schema name (e.g. lct, atp). Auto-detected from @type if omitted.",
    )

    # generate
    p_gen = sub.add_parser(
        "generate",
        help="Generate a minimal valid JSON-LD document for a type",
    )
    p_gen.add_argument(
        "type",
        nargs="?",
        default=None,
        help="Type name (e.g. T3Tensor, R7Action, LinkedContextToken)",
    )
    p_gen.add_argument(
        "--compact",
        action="store_true",
        help="Output compact JSON (no indentation).",
    )
    p_gen.add_argument(
        "--list",
        action="store_true",
        dest="list_types",
        help="List available types instead of generating.",
    )

    # roundtrip
    p_rt = sub.add_parser(
        "roundtrip",
        help="Deserialize and re-serialize a JSON-LD document",
    )
    p_rt.add_argument("file", help="Path to JSON file (or '-' for stdin)")
    p_rt.add_argument(
        "--check",
        action="store_true",
        help="Compare input vs output; exit 0 if equal, 1 if different.",
    )

    # selftest
    p_st = sub.add_parser(
        "selftest",
        help="Verify SDK installation (imports, schemas, round-trips)",
    )
    p_st.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show per-phase progress details.",
    )

    # trust
    p_trust = sub.add_parser(
        "trust",
        help="Evaluate a trust query (from JSON or CLI flags)",
    )
    p_trust.add_argument(
        "--file",
        default=None,
        help="Path to TrustQuery JSON file (or '-' for stdin). Overrides --actor/--target/--role flags.",
    )
    p_trust.add_argument("--actor", default=None, help="Querier entity ID")
    p_trust.add_argument("--target", default=None, help="Target entity ID")
    p_trust.add_argument("--role", default=None, help="Requested role")
    p_trust.add_argument(
        "--interaction",
        default="cli-query",
        help="Intended interaction description (default: cli-query)",
    )
    p_trust.add_argument(
        "--disclosure-level",
        default="range",
        dest="disclosure_level",
        help="Disclosure level: binary, range, or precise (default: range)",
    )
    p_trust.add_argument(
        "--stake",
        type=int,
        default=10,
        help="ATP stake amount (default: 10, minimum allowed)",
    )
    p_trust.add_argument(
        "--validity",
        type=int,
        default=3600,
        help="Validity period in seconds (default: 3600)",
    )
    p_trust.add_argument(
        "--profile-roles",
        default=None,
        help="JSON mapping role->T3 for target, e.g. "
        '\'{"analyst": {"talent": 0.8, "training": 0.9, "temperament": 0.7}}\'',
    )
    p_trust.add_argument(
        "--atp-balance",
        type=float,
        default=1000.0,
        dest="atp_balance",
        help="Requester ATP balance (default: 1000.0)",
    )
    p_trust.add_argument(
        "--compact",
        action="store_true",
        help="Output compact JSON (no indentation)",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "info": _cmd_info,
        "list-schemas": _cmd_list_schemas,
        "validate": _cmd_validate,
        "roundtrip": _cmd_roundtrip,
        "generate": _cmd_generate,
        "selftest": _cmd_selftest,
        "trust": _cmd_trust,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
