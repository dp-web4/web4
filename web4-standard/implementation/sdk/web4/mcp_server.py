"""Web4 MCP server — expose SDK trust operations as MCP tools.

Starts an MCP server (stdio transport by default) that wraps the web4 SDK's
public API as tools accessible from any MCP client.

Usage::

    python -m web4.mcp_server              # stdio transport (default)
    web4-mcp                               # via console script entry point

Tools provided:

- ``web4_info``             — SDK version, module count, export count, schema count
- ``web4_validate``         — validate a JSON-LD document against web4 schemas
- ``web4_generate``         — generate a minimal valid JSON-LD document for any type
- ``web4_roundtrip``        — deserialize + re-serialize for conformance testing
- ``web4_list_types``       — list all supported types for generation and deserialization
- ``web4_evaluate_trust``   — evaluate a trust query (ATP stake + T3 lookup + disclosure)
- ``web4_resolve_trust``           — resolve trust through MRH graph (direct/indirect/none)
- ``web4_process_action_outcome``  — process action through reputation pipeline (T3/V3 + ATP)

Requires the ``mcp`` package: ``pip install 'web4[mcp]'``
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

__all__ = [
    "mcp", "run",
    "web4_evaluate_trust", "web4_resolve_trust", "web4_process_action_outcome",
]

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="web4",
    instructions=(
        "Web4 SDK trust operations server. "
        "Provides tools for generating, validating, and round-tripping "
        "web4 JSON-LD documents, plus behavioral trust resolution operations "
        "(evaluate trust queries, resolve trust through MRH graphs)."
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
    name="web4_evaluate_trust",
    description=(
        "Evaluate a trust query: lock ATP stake, look up the target's T3 "
        "for the requested role, apply disclosure filtering, and return an "
        "APPROVED or REJECTED response. Pass the trust query, target's trust "
        "profile, and requester's ATP balance as JSON."
    ),
)
def web4_evaluate_trust(
    query: str,
    profile_entity_id: str,
    profile_roles: str = "{}",
    atp_balance: float = 1000.0,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate a trust query against a profile with ATP stake locking.

    Args:
        query: JSON string of TrustQuery fields (querier, target_entity,
            requested_role, intended_interaction, atp_stake, validity_period,
            signature; optional: disclosure_level, query_justification, timestamp).
        profile_entity_id: Entity ID for the target's trust profile.
        profile_roles: JSON string mapping role names to T3 dicts, e.g.
            ``{"analyst": {"talent": 0.8, "training": 0.9, "temperament": 0.7}}``.
        atp_balance: Initial ATP balance for the requester (default 1000).
        timestamp: Optional ISO timestamp for the response audit log.
    """
    from web4.atp import ATPAccount
    from web4.trust import (
        T3,
        TrustProfile,
        TrustQuery,
        evaluate_trust_query,
    )

    # Parse query
    try:
        query_dict = json.loads(query)
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid query JSON: {exc}"}
    try:
        tq = TrustQuery.from_dict(query_dict)
    except (KeyError, ValueError, TypeError) as exc:
        return {"error": f"Invalid TrustQuery: {exc}"}

    # Build target profile
    profile = TrustProfile(profile_entity_id)
    try:
        roles_dict = json.loads(profile_roles)
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid profile_roles JSON: {exc}"}
    for role_name, t3_data in roles_dict.items():
        profile.set_role(role_name, T3.from_dict(t3_data))

    # Build requester ATP account
    account = ATPAccount(available=atp_balance)

    # Evaluate
    response = evaluate_trust_query(tq, profile, account, timestamp=timestamp)
    return response.to_dict()


@mcp.tool(
    name="web4_resolve_trust",
    description=(
        "Resolve trust between two entities through an MRH graph. Finds "
        "direct or indirect trust paths, attenuates the target's T3 tensor "
        "by path decay, and returns the effective trust resolution."
    ),
)
def web4_resolve_trust(
    observer: str,
    target: str,
    role: str,
    edges: str,
    profiles: str = "{}",
    strategy: str = "probabilistic",
    decay_factor: float = 0.7,
) -> Dict[str, Any]:
    """Resolve trust between observer and target through an MRH graph.

    Args:
        observer: Entity ID of the observer requesting trust information.
        target: Entity ID of the entity being evaluated.
        role: Role context for trust lookup.
        edges: JSON string — list of edge objects, each with ``source``,
            ``target``, ``relation`` (e.g. "PAIRED_WITH"), and ``weight``.
        profiles: JSON string mapping entity IDs to role→T3 dicts, e.g.
            ``{"lct:bob": {"analyst": {"talent": 0.8, "training": 0.9, "temperament": 0.7}}}``.
        strategy: Propagation strategy ("probabilistic", "multiplicative",
            "maximal"). Default "probabilistic".
        decay_factor: Per-hop decay factor (0.0–1.0). Default 0.7.
    """
    from web4.mrh import MRHEdge, MRHGraph, MRHNode
    from web4.trust import T3, TrustProfile, resolve_trust

    # Parse edges
    try:
        edges_list = json.loads(edges)
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid edges JSON: {exc}"}
    if not isinstance(edges_list, list):
        return {"error": "edges must be a JSON array of edge objects"}

    # Build graph
    graph = MRHGraph()
    node_ids: set[str] = set()
    for edge_data in edges_list:
        try:
            edge = MRHEdge.from_dict(edge_data)
        except (KeyError, ValueError, TypeError) as exc:
            return {"error": f"Invalid edge: {exc} — data: {edge_data}"}
        for nid in (edge.source, edge.target):
            if nid not in node_ids:
                graph.add_node(MRHNode(lct_id=nid))
                node_ids.add(nid)
        graph.add_edge(edge)

    # Ensure observer and target are in graph
    for nid in (observer, target):
        if nid not in node_ids:
            graph.add_node(MRHNode(lct_id=nid))
            node_ids.add(nid)

    # Parse profiles
    try:
        profiles_dict = json.loads(profiles)
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid profiles JSON: {exc}"}
    trust_profiles: Dict[str, TrustProfile] = {}
    for entity_id, roles_data in profiles_dict.items():
        tp = TrustProfile(entity_id)
        for role_name, t3_data in roles_data.items():
            tp.set_role(role_name, T3.from_dict(t3_data))
        trust_profiles[entity_id] = tp

    # Resolve
    resolution = resolve_trust(
        graph, trust_profiles, observer, target, role,
        strategy=strategy, decay_factor=decay_factor,
    )
    return resolution.to_dict()


@mcp.tool(
    name="web4_process_action_outcome",
    description=(
        "Process a completed R7 action through the reputation pipeline. "
        "Evaluates reputation rules, applies T3/V3 deltas to the actor's "
        "trust profile, and settles ATP (commit on success, rollback on failure)."
    ),
)
def web4_process_action_outcome(
    action: str,
    rules: str,
    profile_entity_id: str,
    profile_roles: str = "{}",
    atp_available: float = 0.0,
    atp_locked: float = 0.0,
) -> Dict[str, Any]:
    """Process a completed action through the reputation and trust pipeline.

    Args:
        action: JSON string of R7Action fields (must include role with
            role_lct, request with atp_stake, result with status).
        rules: JSON string -- list of reputation rule objects, each with
            rule_id, trigger_conditions, and t3_impacts/v3_impacts.
        profile_entity_id: Entity ID for the actor's trust profile.
        profile_roles: JSON string mapping role names to T3/V3 dicts, e.g.
            ``{"analyst": {"talent": 0.8, "training": 0.9, "temperament": 0.7}}``.
        atp_available: Available (unlocked) ATP balance. Default 0.
        atp_locked: Locked ATP balance (the stake). Default 0.
    """
    from web4.atp import ATPAccount
    from web4.r6 import (
        R7Action as R7ActionCls,
        Reference,
        Request,
        ResourceRequirements,
        Result,
        Role,
        Rules,
    )
    from web4.reputation import (
        DimensionImpact,
        Modifier,
        ReputationEngine,
        ReputationRule,
        process_action_outcome,
    )
    from web4.trust import T3, V3, TrustProfile

    # Parse action from component dicts
    try:
        action_dict = json.loads(action)
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid action JSON: {exc}"}
    try:
        r7 = R7ActionCls(
            rules=Rules.from_dict(action_dict.get("rules", {})),
            role=Role.from_dict(action_dict.get("role", {"actor": "", "role_lct": ""})),
            request=Request.from_dict(action_dict.get("request", {"action": ""})),
            reference=Reference.from_dict(action_dict.get("reference", {})),
            resource=ResourceRequirements.from_dict(action_dict.get("resource", {})),
            result=Result.from_dict(action_dict.get("result", {})),
        )
    except (KeyError, ValueError, TypeError) as exc:
        return {"error": f"Invalid R7Action: {exc}"}

    # Build reputation engine from rules
    try:
        rules_list = json.loads(rules)
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid rules JSON: {exc}"}
    if not isinstance(rules_list, list):
        return {"error": "rules must be a JSON array of rule objects"}

    engine = ReputationEngine()
    for rule_data in rules_list:
        try:
            t3_impacts = {}
            for dim, impact_data in rule_data.get("t3_impacts", {}).items():
                modifiers = [
                    Modifier(**m) for m in impact_data.get("modifiers", [])
                ]
                t3_impacts[dim] = DimensionImpact(
                    base_delta=impact_data["base_delta"],
                    modifiers=modifiers,
                )
            v3_impacts = {}
            for dim, impact_data in rule_data.get("v3_impacts", {}).items():
                modifiers = [
                    Modifier(**m) for m in impact_data.get("modifiers", [])
                ]
                v3_impacts[dim] = DimensionImpact(
                    base_delta=impact_data["base_delta"],
                    modifiers=modifiers,
                )
            engine.add_rule(ReputationRule(
                rule_id=rule_data["rule_id"],
                trigger_conditions=rule_data.get("trigger_conditions", {}),
                t3_impacts=t3_impacts,
                v3_impacts=v3_impacts,
            ))
        except (KeyError, ValueError, TypeError) as exc:
            return {"error": f"Invalid rule: {exc} -- data: {rule_data}"}

    # Build actor profile
    profile = TrustProfile(profile_entity_id)
    try:
        roles_dict = json.loads(profile_roles)
    except json.JSONDecodeError as exc:
        return {"error": f"Invalid profile_roles JSON: {exc}"}
    for role_name, tensor_data in roles_dict.items():
        t3 = T3.from_dict(tensor_data) if "talent" in tensor_data else None
        v3 = V3.from_dict(tensor_data) if "valuation" in tensor_data else None
        profile.set_role(role_name, t3=t3, v3=v3)

    # Build ATP account
    account = ATPAccount(available=atp_available, locked=atp_locked)

    # Process
    try:
        result = process_action_outcome(r7, engine, profile, account)
    except ValueError as exc:
        return {"error": str(exc)}

    return {
        "delta": result.delta.to_dict() if result.delta is not None else None,
        "updated_t3": result.updated_t3.as_dict(),
        "updated_v3": result.updated_v3.as_dict(),
        "atp_committed": result.atp_committed,
        "atp_rolled_back": result.atp_rolled_back,
    }


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
