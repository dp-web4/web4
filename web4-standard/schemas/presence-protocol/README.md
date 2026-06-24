# Presence Protocol — JSON Schemas

JSON Schema documents for every tool's input and output, every
resource body, and shared types referenced from the spec. These
schemas are the **wire-format authority**: if a SDK or daemon
serializes a shape that doesn't validate against the schema, the
implementation is non-conforming.

The schemas mirror the protocol version. v0 schemas describe v0
shapes. v1 schemas live alongside v0 (`v1/tools/`) so historical
clients can validate against the version they speak. v1 has landed
(2026-05-16); so far only `hestia_query_policy` grew its output
shape in v1, so it is the only tool with a `v1/` schema — every
other tool's v0 schema is still current at v1.

## Layout

Each tool's input and output schemas live in a single combined file
(`$defs/input` + `$defs/output`), not split per direction. Shared
structs and the error envelope live under `common/`.

```
schemas/presence-protocol/
  README.md
  v0/
    tools/
      hestia_begin_action.schema.json
      hestia_connect.schema.json
      hestia_query_history.schema.json
      hestia_query_policy.schema.json
      hestia_record_outcome.schema.json
      hestia_request_witness.schema.json
      hestia_vault_get.schema.json
      hestia_vault_set.schema.json
    common/
      error_envelope.schema.json
      trust_state.schema.json
      witness_entry.schema.json
  v1/
    tools/
      hestia_query_policy.schema.json
```

Note: the `hestia://society/state` resource body and the §5.2
`R6Action` struct have no JSON Schema yet (the former is an ad-hoc
stats object bound directly by conformance vector P0-009; the latter
is a documentary type catalog with no wire carrier — see
presence-protocol.md §8).

## Validation

The conformance vectors in
`web4-standard/testing/conformance/presence-protocol-conformance.json`
bind each tool's output to the `$id` URLs above via `shapeMatchesSchema`.
A standalone reference validator script (to let implementations
self-check a live daemon's responses) is planned but not yet present
in this repo.

## Compatibility

Schemas use JSON Schema Draft 2020-12 and follow the same `$id`
convention as the existing Web4 schemas (`https://web4.io/schemas/...`).
