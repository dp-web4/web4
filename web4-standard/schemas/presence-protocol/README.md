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

Note: four spec-referenced artifacts have no JSON Schema in this tree
yet — a known-gap ledger, not a permanent exemption:

- The `hestia://society/state` resource body — an ad-hoc stats object
  bound directly by conformance vector P0-009, not a §5 struct.
- The §5.2 `R6Action` struct — a documentary type catalog with no wire
  carrier (see presence-protocol.md §8).
- The `Session` struct (§5.1), returned by the `hestia://session/own`
  resource. The `hestia_connect` output schema binds only the four-field
  connect reply (`sessionId`, `softLct`, `assignedRole`,
  `protocolVersion`), not the full eight-field Session record the
  resource read returns.
- The `VaultEntry` struct (§5.7), returned by the `hestia://vault/{name}`
  resource. `hestia_vault_get` returns `{value, approvalToken}`, not a
  `VaultEntry`, so no tool-output schema covers it.

The last two are the only `camelCase` §5-typed resource bodies reached
*solely* through `resources/read` — unlike `witness/recent`→`WitnessEntry`
and `society/trust`→`TrustState`, which ride the `query_history` /
`record_outcome` tool-output schemas — so they also have no conformance
vector. Authoring their schemas (under `v0/common/`) and their
`resources/read` vectors is pending.

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
