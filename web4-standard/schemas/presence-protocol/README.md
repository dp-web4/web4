# Presence Protocol — JSON Schemas

JSON Schema documents for every tool's input and output, every
resource body, and shared types referenced from the spec. These
schemas are the **wire-format authority**: if a SDK or daemon
serializes a shape that doesn't validate against the schema, the
implementation is non-conforming.

The schemas mirror the protocol version. v0 schemas describe v0
shapes. v1 schemas will live alongside v0 (e.g. `v1/tools/`) once
v1 lands, so historical clients can validate against the version
they speak.

## Layout

```
schemas/presence-protocol/
  v0/
    tools/
      hestia_connect.input.schema.json
      hestia_connect.output.schema.json
      hestia_begin_action.input.schema.json
      ...
    resources/
      society_state.schema.json
      trust_state.schema.json
      witness_entry.schema.json
      ...
    common/
      error_envelope.schema.json
      r6_action.schema.json
      ...
```

## Validation

A reference validator script lives at
`web4-standard/testing/conformance/validate-presence.py` (Step 1b).
Implementations can run it against their own daemon's responses to
self-check conformance before publishing.

## Compatibility

Schemas use JSON Schema Draft 2020-12 and follow the same `$id`
convention as the existing Web4 schemas (`https://web4.io/schemas/...`).
