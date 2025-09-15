# Agentic Context Protocol (ACP) Bundle
**Generated:** 2025-09-15T15:27:37.121413Z

## Files
- `acp-spec.md` — ACP specification (plans, intents, decisions, execution records, security, errors, conformance).
- `acp.jsonld` — JSON-LD context for ACP classes and properties.
- `acp-ontology.ttl` — Ontology patch for ACP MRH edges.
- `schemas/` — JSON Schemas for AgentPlan, Intent, Decision, ExecutionRecord.
- `acp-openapi.yaml` — OpenAPI 3.1 for ACP control plane (plans, intents, decisions, records).
- `sparql/` — SPARQL conformance checks.

## Notes
- ACP is agentic: it **initiates** under valid AGY grants.
- MCP servers remain reactive; ACP is the agentic client orchestrator.
- All SAL-critical actions must be **witness co-signed** and persisted on the immutable record.
