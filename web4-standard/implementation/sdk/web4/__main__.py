"""
``python -m web4`` — command-line interface for the Web4 SDK.

Subcommands::

    python -m web4 info               # Show SDK version, modules, exports
    python -m web4 list-schemas       # List available JSON Schemas
    python -m web4 validate F.json    # Validate a JSON-LD document
    python -m web4 roundtrip F.json   # Deserialize + re-serialize (normalize)
    python -m web4 roundtrip --check  # Verify round-trip fidelity
    python -m web4 generate T3Tensor  # Generate a minimal valid JSON-LD document
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
        "trust", "lct", "atp", "federation", "r6", "mrh", "acp",
        "dictionary", "entity", "capability", "errors", "metabolic",
        "binding", "society", "reputation", "security", "protocol",
        "mcp", "attestation", "validation", "deserialize", "generate",
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
                "Error: cannot detect schema type. "
                "Use --schema to specify (e.g. --schema lct).",
                file=sys.stderr,
            )
            return 1

    # Validate
    from web4.validation import validate, SchemaNotFound, SchemaValidationUnavailable

    try:
        result = validate(doc, schema_name)
    except SchemaValidationUnavailable:
        print(
            "Error: jsonschema package not installed. "
            "Install with: pip install 'web4[validation]'",
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
            f"Error: {type_val} does not support re-serialization "
            f"(no to_jsonld method on {type(obj).__name__})",
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
        "type", nargs="?", default=None,
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
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
