# KV cache as derived and scoped state: Web4 research note
Date: 2026-10-21 | Status: proposed, not normative
Background: LMCache https://lmcache.ai/en/ and SAGE's earlier KV save/resume research.
Cross-project record: dp-web4/private-context/research/lmcache-kv-persistence-evaluation-2026-10-21.md

Persistent transformer KV is derived from an exact token/context history and implementation-specific model state. It may encode sensitive context even when unreadable as ordinary text. An infrastructure cache hit does not establish provenance, delegated authority or admissibility.

Candidate Web4 object: a cache-state claim bound to owner LCT, source context refs, model/runtime fingerprint, allowed recipient and purpose, scope, TTL, revocation epoch, integrity evidence and witness/decision references. These are suggested envelope semantics, not mandatory wire format or LMCache functionality. Avoid assigning independent personhood or transferable identity to cache blobs; distinguish cache state from SAGE resident/visitor roles.

Design rules:
1. Cache source/disclosure governed by applicable law and contextual delegation; recipient must be able to evaluate evidence of provenance and current validity.
2. Reuse across tenants, beings or resident/visitor trust boundaries is disallowed by default. Unknown validity denies cache reuse, not necessarily the original request.
3. Cached computation does not authorize future actions. A fresh action receives a fresh Hestia decision and recipient-side acceptance check.
4. Revoked/expired/incompatible cache is discarded and reconstructed; there must be no dependency on cache retention for identity, durable memory, debt or witnessed history.
5. Distinguish access audit (cache retrieval) from outcome/battle-damage feedback; neither turns the governance gate into an execution controller.

Research questions: protocol-level envelope vs local policy only; signatures/integrity vs encryption and capability grants; revocation of derived content; compatibility attestations for cross-worker reuse. Defer normative RFC until a real deployment and threat model justify interoperability.
