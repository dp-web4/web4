# JSON-LD Namespace Reconciliation

**Date**: 2026-03-24
**Sprint**: 6 (B3)
**Status**: Decided

## Problem

After Sprint 3-5 delivered JSON-LD serialization for all 9 core types, an audit
revealed three inconsistent namespace patterns:

| Pattern | Used by | Namespace URI |
|---------|---------|---------------|
| Application contexts | ATP, ACP, Entity, Capability, Dictionary, LCT, AttestationEnvelope | `https://web4.io/ns/` |
| Ontology contexts | T3/V3, R7 Action | `https://web4.io/ontology#` |
| SDK constants | All types | `https://web4.io/contexts/{type}.jsonld` (URL, not namespace) |

Additionally:
- T3 and V3 share a single context file (`ontology/t3v3.jsonld`) but the SDK
  references separate files (`t3-tensor.jsonld`, `v3-tensor.jsonld`) that don't exist
- R7 Action context lives in `ontology/` while all others are in `schemas/contexts/`
- T3/V3 `to_jsonld()` emits a bare namespace URI (`https://web4.io/ontology#`) as
  a second `@context` entry — this is not a valid context document and would cause
  JSON-LD processors to fail when attempting to dereference it

## Decision

**Standardize on `https://web4.io/ns/` for all application-facing JSON-LD contexts.**

### Rationale

1. **`ontology#` is for OWL/RDF class definitions** — formal type hierarchy, property
   domains/ranges, class inheritance. These serve the semantic web tooling layer.

2. **`ns/` is for application serialization** — JSON-LD contexts that map Python/Go/Rust
   field names to semantic URIs. These serve cross-language interoperability.

3. **7 of 9 types already use `ns/`** — changing 2 to match is less disruptive than
   changing 7. The `ns/` pattern was established in Sprint 5 and is well-tested.

4. **Separate concerns**: Ontology files (`ontology/*.ttl`, `ontology/*.jsonld`) remain
   unchanged at `ontology#`. Application context files (`schemas/contexts/*.jsonld`)
   all use `ns/`. The two layers serve different consumers.

### Changes

| Before | After |
|--------|-------|
| T3/V3 context: `ontology/t3v3.jsonld` (ontology#) | New: `schemas/contexts/t3.jsonld` + `schemas/contexts/v3.jsonld` (ns/) |
| R7 context: `ontology/r7-action.jsonld` (ontology#) | New: `schemas/contexts/r7-action.jsonld` (ns/) |
| SDK: `T3_JSONLD_CONTEXT = ".../t3-tensor.jsonld"` | `T3_JSONLD_CONTEXT = ".../t3.jsonld"` |
| SDK: `V3_JSONLD_CONTEXT = ".../v3-tensor.jsonld"` | `V3_JSONLD_CONTEXT = ".../v3.jsonld"` |
| SDK: `WEB4_ONTOLOGY_NS` in T3/V3 @context arrays | Removed from @context (ns/ context files are self-contained) |

### R7 Context File — Field Name Alignment

The R7 Action `to_jsonld()` uses snake_case for top-level fields (`action_id`, `prev_action_hash`)
while nested component `to_dict()` methods use camelCase (`lawHash`, `roleLCT`, `atpStake`).
The application context file maps BOTH conventions to the same semantic IRIs, ensuring
JSON-LD processors can expand terms regardless of which naming convention the producing
implementation uses.

### Backward Compatibility

- `from_jsonld()` ignores `@context` values — reads property names directly
- Old serialized documents with `ontology#` context still deserialize correctly
- Ontology files in `ontology/` remain unchanged (no impact on RDF/SPARQL consumers)
- `WEB4_ONTOLOGY_NS` constant kept in SDK for any code referencing the ontology directly

### Not Changed

- `ontology/t3v3.jsonld` and `ontology/r7-action.jsonld` — left in place for OWL tooling
- `ontology/t3v3-ontology.ttl` — formal ontology unchanged
- JSON Schema files — not namespace-dependent
- Test vectors — use property names, not namespace URIs
