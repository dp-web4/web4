# Web4 SAL — Conformance Suite & Ledger API
**Generated:** 2025-09-15T12:01:26.550698Z

This package includes:
- **SPARQL conformance queries** to validate SAL requirements on the MRH/RDF graph.
- **Ledger API** (OpenAPI 3.1) for the immutable record service.
- **JSON Schemas** for key SAL objects (BirthCertificate, AuditRequest).

## Structure
- `sparql/`
  - `ASK_validate_citizen_pairing.rq`
  - `ASK_has_witness_quorum_for_birth.rq`
  - `SELECT_effective_law_hash.rq`
  - `ASK_auditor_adjustment_recorded.rq`
  - `ASK_law_inheritance_consistency.rq`
  - `SELECT_audit_transcript_integrity.rq`
- `ledger-openapi.yaml`
- `schemas/`
  - `Web4BirthCertificate.schema.json`
  - `Web4AuditRequest.schema.json`

## Notes
- These queries assume the SAL ontology terms as defined in `sal-ontology.ttl` and context in `sal.jsonld`.
- Ledger endpoints return canonicalized objects; inclusion proofs should be bound into SAL action transcripts.
