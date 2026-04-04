"""
``python -m web4`` — command-line interface for the Web4 SDK.

Subcommands::

    python -m web4 info             # Show SDK version, modules, exports
    python -m web4 list-schemas     # List available JSON Schemas
    python -m web4 validate F.json  # Validate a JSON-LD document
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional, Sequence


def _cmd_info(args: argparse.Namespace) -> int:
    """Display SDK version, module count, and export count."""
    import web4

    modules = [
        "trust", "lct", "atp", "federation", "r6", "mrh", "acp",
        "dictionary", "entity", "capability", "errors", "metabolic",
        "binding", "society", "reputation", "security", "protocol",
        "mcp", "attestation", "validation",
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


def _cmd_validate(args: argparse.Namespace) -> int:
    """Validate a JSON-LD document against a Web4 JSON Schema."""
    file_path: str = args.file
    schema_name: Optional[str] = args.schema

    # Read and parse the JSON file
    try:
        if file_path == "-":
            raw = sys.stdin.read()
        else:
            with open(file_path) as f:
                raw = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON: {exc}", file=sys.stderr)
        return 1

    if not isinstance(doc, dict):
        print("Error: document must be a JSON object", file=sys.stderr)
        return 1

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
        for err in result.errors:
            print(f"  - {err}")
        return 1


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
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
