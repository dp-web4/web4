# Web4 Agency Delegation (AGY) Bundle
**Generated:** 2025-09-15T15:07:46.705282Z

## Contents
- `web4-agency-delegation.md` — normative spec for Agency delegation (grant, revocation, scope, caps, security, R6/MCP bindings).
- `agy.jsonld` — JSON-LD context.
- `agy-ontology.ttl` — ontology patch for Agency classes/properties.
- `agy-schemas/` — JSON Schemas for `Web4AgencyGrant` and `Web4AgencyRevocation`.
- `agy-sparql/` — SPARQL conformance queries (expiry, scope, revocation, delegation chain).

## Notes
- Proof-of-agency is REQUIRED on all Agent-originated actions.
- Grants and revocations MUST be recorded on the Immutable Record with inclusion proofs.
- For cross-society actions, pin both Client and Agent law hashes.
