"""Web4 MCP server — expose SDK trust operations as MCP tools.

Starts an MCP server (stdio transport by default) that wraps the web4 SDK's
public API as tools accessible from any MCP client.

Usage::

    python -m web4.mcp_server              # stdio transport (default)
    web4-mcp                               # via console script entry point

Tools provided:

- ``web4_info``       — SDK version, module count, export count, schema count
- ``web4_validate``   — validate a JSON-LD document against web4 schemas
- ``web4_generate``   — generate a minimal valid JSON-LD document for any type
- ``web4_roundtrip``  — deserialize + re-serialize for conformance testing
- ``web4_list_types`` — list all supported types for generation and deserialization

Requires the ``mcp`` package: ``pip install 'web4[mcp]'``
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

__all__ = ["mcp", "run"]

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="web4",
    instructions=(
        "Web4 SDK trust operations server. "
        "Provides tools for generating, validating, and round-tripping "
        "web4 JSON-LD documents (trust tensors, LCTs, attestation envelopes, "
        "ATP accounts, agent plans, and more)."
    ),
)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="web4_info",
    description="Show Web4 SDK version, module count, export count, and available schema count.",
)
def web4_info() -> Dict[str, Any]:
    """Return SDK metadata as a structured dict."""
    import web4

    modules = [
        "trust", "lct", "atp", "federation", "r6", "mrh", "acp",
        "dictionary", "entity", "capability", "errors", "metabolic",
        "binding", "society", "reputation", "security", "protocol",
        "mcp", "attestation", "validation", "deserialize", "generate",
    ]

    result: Dict[str, Any] = {
        "version": web4.__version__,
        "modules": len(modules),
        "module_names": modules,
        "exports": len(web4.__all__),
    }

    try:
        from web4.validation import list_schemas
        schemas = list_schemas()
        result["schemas"] = len(schemas)
        result["schema_names"] = schemas
    except Exception:
        result["schemas"] = "unavailable"

    return result


@mcp.tool(
    name="web4_validate",
    description=(
        "Validate a JSON-LD document against a web4 JSON Schema. "
        "Pass the document as a JSON string. Optionally specify a schema name "
        "(e.g. 'lct', 'atp', 't3v3'); if omitted, the schema is auto-detected "
        "from the document's @type field."
    ),
)
def web4_validate(document: str, schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Validate a JSON-LD document string against a web4 schema."""
    try:
        doc = json.loads(document)
    except json.JSONDecodeError as exc:
        return {"valid": False, "error": f"Invalid JSON: {exc}"}

    if not isinstance(doc, dict):
        return {"valid": False, "error": "Document must be a JSON object"}

    # Auto-detect schema from @type if not specified
    if schema_name is None:
        schema_name = _detect_schema(doc)
        if schema_name is None:
            return {
                "valid": False,
                "error": (
                    "Cannot detect schema type from @type field. "
                    "Specify schema_name explicitly (e.g. 'lct', 'atp', 't3v3')."
                ),
            }

    from web4.validation import (
        SchemaNotFound,
        SchemaValidationUnavailable,
        validate,
    )

    try:
        result = validate(doc, schema_name)
    except SchemaValidationUnavailable:
        return {
            "valid": False,
            "error": "jsonschema not installed. Install with: pip install 'web4[validation]'",
        }
    except SchemaNotFound as exc:
        return {"valid": False, "error": str(exc)}

    if result.valid:
        return {"valid": True, "schema": schema_name}
    else:
        return {
            "valid": False,
            "schema": schema_name,
            "errors": [str(e) for e in result.errors],
        }


@mcp.tool(
    name="web4_generate",
    description=(
        "Generate a minimal valid JSON-LD document for a given web4 type. "
        "Pass the type name (e.g. 'T3Tensor', 'R7Action', 'LinkedContextToken'). "
        "Use web4_list_types to see all available types."
    ),
)
def web4_generate(type_name: str, compact: bool = False) -> Dict[str, Any]:
    """Generate a minimal valid JSON-LD document for *type_name*."""
    from web4.generate import UnsupportedTypeError, generate

    try:
        doc = generate(type_name)
    except UnsupportedTypeError:
        from web4.generate import available_types
        return {
            "error": f"Unknown type: {type_name!r}",
            "available_types": available_types(),
        }

    if compact:
        return {"type": type_name, "document": json.dumps(doc, separators=(",", ":"))}
    else:
        return {"type": type_name, "document": doc}


@mcp.tool(
    name="web4_roundtrip",
    description=(
        "Deserialize a JSON-LD document via from_jsonld() and re-serialize via "
        "to_jsonld() for conformance testing. Pass the document as a JSON string. "
        "Returns the normalized document and whether the round-trip preserved it."
    ),
)
def web4_roundtrip(document: str) -> Dict[str, Any]:
    """Deserialize + re-serialize a JSON-LD document."""
    try:
        doc = json.loads(document)
    except json.JSONDecodeError as exc:
        return {"success": False, "error": f"Invalid JSON: {exc}"}

    if not isinstance(doc, dict):
        return {"success": False, "error": "Document must be a JSON object"}

    from web4.deserialize import UnknownTypeError, from_jsonld

    try:
        obj = from_jsonld(doc)
    except (UnknownTypeError, ValueError, TypeError) as exc:
        return {"success": False, "error": str(exc)}

    if not hasattr(obj, "to_jsonld"):
        type_val = doc.get("@type", "<unknown>")
        return {
            "success": False,
            "error": (
                f"{type_val} does not support re-serialization "
                f"(no to_jsonld method on {type(obj).__name__})"
            ),
        }

    roundtripped: Dict[str, object] = obj.to_jsonld()
    preserved = roundtripped == doc

    result: Dict[str, Any] = {
        "success": True,
        "preserved": preserved,
        "document": roundtripped,
    }

    if not preserved:
        # Report top-level key differences
        diffs: List[str] = []
        all_keys = sorted(set(list(doc.keys()) + list(roundtripped.keys())))
        for key in all_keys:
            in_orig = key in doc
            in_rt = key in roundtripped
            if in_orig and not in_rt:
                diffs.append(f"removed: {key}")
            elif in_rt and not in_orig:
                diffs.append(f"added: {key}")
            elif doc[key] != roundtripped[key]:
                diffs.append(f"changed: {key}")
        result["differences"] = diffs

    return result


@mcp.tool(
    name="web4_list_types",
    description=(
        "List all web4 types available for generation (via web4_generate) "
        "and deserialization (via web4_roundtrip)."
    ),
)
def web4_list_types() -> Dict[str, Any]:
    """List available types for generation and deserialization."""
    from web4.deserialize import supported_types
    from web4.generate import available_types

    gen_types = available_types()
    deser_types = supported_types()

    return {
        "generate_types": gen_types,
        "generate_count": len(gen_types),
        "deserialize_types": deser_types,
        "deserialize_count": len(deser_types),
    }


# ---------------------------------------------------------------------------
# Schema auto-detection (reuse from __main__.py)
# ---------------------------------------------------------------------------

_TYPE_TO_SCHEMA: Dict[str, str] = {
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


def _detect_schema(doc: Dict[str, Any]) -> Optional[str]:
    """Detect schema name from a document's ``@type`` field."""
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run() -> None:
    """Start the web4 MCP server with stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
