# PRD — Hub Witnessing of Member Hestia Chains via SHOW

**Status:** Proposed / not implemented by this PRD  
**Date:** 2026-10-11  
**Owner:** Web4 Hub; Hestia maintains member-side adapter  
**Reference (required):** [SHOW — Sampled Hash Observation Witnessing](../../docs/reference/SHOW_SAMPLED_HASH_OBSERVATION_WITNESSING.md)  
**Also:** [Federated Hub PRD — R3](PRD_HUB_V2_FEDERATED.md), [Hub Implementation Authority](../../docs/reference/HUB_IMPLEMENTATION_AUTHORITY.md), [Hub law](HUB-LAW.md)

## 1. Product proposition

A Web4 Hub optionally serves as an **independent, passive historical witness** to hash-linked chains maintained by its member Hestia instances. Member Hestia periodically sends limited signed checkpoint commitments; the Hub records immutable observations and receipt times. A later authorized third party can present a purported historical block identity/hash/metadata commitment and obtain MATCH, MISMATCH, or NOT_RECORDED. For unobserved IDs the Hub supplies nearest observed before/after IDs only, never stored hashes.

**Prior-art posture:** This PRD explicitly relies on the companion [SHOW reference](../../docs/reference/SHOW_SAMPLED_HASH_OBSERVATION_WITNESSING.md), which concludes that the *fundamental technique* of intermittent external hash commitments and retrospective authentication is **believed to be public-domain technology** grounded particularly in expired [US 5,781,629 A](https://patents.google.com/patent/US5781629A/en) (including its linear-chain Figure 7), earlier secure timestamping work, and public standards. This is an engineering belief **not a comprehensive freedom-to-operate legal opinion**, particularly for later patented improvements. The product is intended as open, interoperable implementation of established primitives, not a novelty claim.

## 2. Relationship to existing Hub direction

Federated Hub PRD R3 already calls for peers to witness periodic `(ledger head hash, height, timestamp, signature)`. SHOW supplies a **common witness record/verify semantic** reusable for that peer-Hub capability and this member-Hestia capability. They differ only in admission, consent, policy, and origin profile. Do not ship a second protocol stack, policy bypass, competing ledger format, or a Hub-specific hash-chain algorithm.

The Hub **witnesses, does not control** members. It never writes member chains, holds their private signing keys, requires plaintext Hestia events, or gates Hestia's ability to continue its local operations. A missing witness observation is absence of external evidence, not evidence of misconduct.

## 3. Actors / trust boundaries

- **Member Hestia**: sovereign owner of the chain; signs checkpoint submissions using authorized identity; maintains local chain and links; may consent to or discontinue witness relationship per applicable law/delegation.
- **Hub witness service**: independently timestamp-observes, immutably stores, and later responds to queries under Hub law.
- **Verifier**: member, federation peer, auditor, or explicitly delegated third party; authorized for the requested namespace and operation. May independently verify the path from an unsampled block to an observed successor.
- **Hub policy gate**: existing canonical PolicyEntity/production law gate, used for member enrollment, submission, query, retention/export, and administrative acts. No second authority route.
- **Other independent witnesses** (future): federation peers or other Hubs may co-witness without consensus or central custody.

Trust assumption: the Hub's evidence is only as reliable as its identity, append-only storage, operational integrity, and receipt signing. Hub membership does not confer infallibility or determine Hestia truthfulness.

## 4. MVP functional requirements

### HSHOW-01: Explicit enrollment and namespace binding (MUST)
Establish law-gated, witnessed enrollment mapping `member_lct_id`, `hestia_chain_id`, `epoch_id`, supported commitment algorithm, authorized submission key(s), and consent/disclosure policy. Never infer that joining a Hub consents to public hash-check queries. Key rotation is versioned and leaves historic proofs verifiable. Remove/revoke affects *future* submissions/queries, not recorded history; retention and availability comply with prior lawful agreement.

### HSHOW-02: Source-generated samples (MUST)
Hestia creates cryptographic commitments over its existing chain according to that chain's canonical algorithm. Triggers: configurable fixed block interval, time interval, and optional significant-event trigger. Defaults are configuration decisions, **not** invented constants in this PRD. Capture chain ID, epoch, monotonic block ID/height, hash algorithm, block commitment, optional metadata digest, source timestamp (marked source-asserted), and origin signature. No plaintext content, agent chat, user data, role policy, or source private keys transmitted in MVP.

### HSHOW-03: Independent durable observation (MUST)
Hub validates identity, key status, schema, policy, bounded payload, and signature; stores typed commitment, *independent Hub receipt timestamp*, receipt sequence, and Hub signature. Ack only after durable commit; retries idempotent. Conflicting submitted hash at an already observed key must never overwrite original: preserve conflict evidence and produce CONFLICT. Origin chain IDs and epochs cannot collide.

### HSHOW-04: Constrained verification API (MUST)
Authorized request with canonical key and proposed commitment returns:
- `MATCH` where stored original equals submitted commitment;
- `MISMATCH` where stored original differs (without returning stored hash);
- `NOT_RECORDED` with `previous_observed_block_id` and `next_observed_block_id` from **same origin chain + epoch only**, nullable, and never adjacent retained hashes;
- `CONFLICT` if original observed key has conflicting history (not mapped to a dishonest MATCH);
- explicit typed error for UNKNOWN/UNAUTHORIZED/UNAVAILABLE/UNSUPPORTED/INVALID, with safe policy handling to avoid membership enumeration.

Responses bind to query digest, witnessed chain/epoch, Hub identity, policy epoch where applicable, and time of query. Signed verification receipts are preferred for portable audit evidence; define whether signature is required in MVP before code freeze.

### HSHOW-05: Sparse segment validation separation (MUST)
The Hub never claims an unobserved block is valid simply because it reports adjacent observation IDs or because both boundary hashes match. Third-party link/path verification lives with source/verifier. A successor commitment only validates an intermediate segment after the verifier checks the full cryptographic linkage from the claimed segment to that successor. This preserves the simple witness service boundary.

### HSHOW-06: Governed disclosure (MUST)
No open-by-default member-history oracle. Different law scopes for submit, own-chain verify, third-party verify, receipts, export, and inspection. Rate-limit and audit queries to prevent guessing and tracking. Neighbor IDs may reveal activity cadence, so the member must consent to that disclosure class; higher-privacy policy may suppress neighbors or deny query. Hub must not leak observed hashes through error diagnostics, logs, telemetry, UI, or API.

### HSHOW-07: Auditable append-only evidence (MUST)
Store observation and conflict events via existing Hub canonical evidence/ledger path with signed witness receipts. Preserve chronology; backups/recovery test that old observations cannot be silently replaced. Retention, pruning, service shutdown, and membership withdrawal explicitly specify what remains verifiable and what can be deleted under law. Do not claim tamper-proofness from database append-only flags alone.

### HSHOW-08: Operational status (MUST)
Per enrolled chain: last successful observed height and Hub receipt time, configured sampling policy, missing-sample/lag health, latest conflict, signed witness identity and algorithm, key/epoch status. Status is authorization-scoped and must distinguish chain inactivity from transport failure or paused consent. Metrics aggregated without leaking member contents.

### HSHOW-09: Federation compatibility (SHOULD)
Same common SHOW record/verify schema should support R3 peer-Hub ledger heads via an alternate source profile. Do not assume every federation peer is automatically authorized to query member chains. Later multi-Hub witnessing uses independent receipts, not implicit consensus; conflicting witnesses are surfaced as evidence.

## 5. Illustrative API (names to reconcile with current Hub routes and MCP)

```text
enroll_witness_chain(member_lct, chain_id, epoch, algorithm, submission_keys, consent_policy)
observe_chain_block(chain_id, epoch, block_id, algorithm, hash, metadata_digest, origin_signature)
verify_chain_block(chain_id, epoch, block_id, algorithm, candidate_hash, metadata_digest)
list_witness_status(chain_id, epoch)
get_witness_receipt(receipt_id)   // policy scoped
```

Implementation should use existing Hub MCP/signed REST membrane and canonical policy gate. Final API names and schemas must be reconciled with actual current routes and core specs, not presumed here.

Illustrative signed response:

```json
{
  "status": "NOT_RECORDED",
  "chain_id": "opaque-chain-id",
  "epoch_id": "opaque-generation",
  "block_id": 150,
  "previous_observed_block_id": 100,
  "next_observed_block_id": 200,
  "witness_id": "hub-lct-id",
  "query_digest": "canonical-query-digest",
  "evaluated_at": "witness-clock-time"
}
```

No hashes of neighboring observations are returned.

## 6. Journeys

**Enrollment:** member consents -> Hub policy gate -> signed enrollment receipt -> Hestia enables scheduled submission.

**Normal operation:** Hestia commits local actions to its chain -> sample at chosen interval/event -> sign -> send to Hub -> Hub law/identity gate -> durable append-only observation -> signed receipt -> Hestia stores receipt locally.

**Third-party check of recorded block:** verifier has external copy of original block identity/hash -> authorized query -> MATCH or MISMATCH -> result evidences whether observed state matches (not whether actions were truthful).

**Third-party check of unsampled block:** query ID 150 -> NOT_RECORDED(100,200) -> verifier obtains local path from 150 through observed 200 -> cryptographically verifies linked path -> compares computed 200 commitment using Hub verify endpoint. If path unavailable, conclude **not established**, not valid.

**Conflicting rewrite:** later source sends different commitment for previously sampled ID -> immutable conflict record -> policy-defined alert; original evidence remains available according to permitted disclosure.

**Member departs:** revoke future access/submission according to scope; preserve or delete existing receipts only according to explicitly accepted retention law, and never silently reinterpret deleted material as if it never existed.

## 7. Data and governance requirements

Use canonical existing Web4/LCT signature and hashing primitives and current hub law gate. No plaintext block bodies in the Hub. Explicitly bind each receipt to chain LCT, epoch, hash suite, relevant key version, canonical metadata digest, and witness identity. Signed query results should specify whether original observation was conflict-free and whether a receipt is independently checkable. Treat locally asserted timestamps separately from independent observed times. Support signed revocation/amendment evidence for enrollment scopes without retroactively falsifying existing attestations.

Respect signed law version and revocation on **each new submission/query**. Do not turn this into a speculative second gate between approval and action execution. The Hub's law determines whether that individual witness act is permitted at the point it is gated.

## 8. Acceptance tests

- Enroll only with law-accepted, authentic member signature + consent; no implicit participation for all members.
- Witness 100 and 200; 100 correct -> MATCH; altered 100 -> MISMATCH; 150 -> NOT_RECORDED with IDs 100/200 and **no recorded hashes**.
- Chain 150 tampered with while 100/200 remain original: verify endpoint queries still match, but no claim about 150 without path verification; recomputed invalid path fails.
- Wrong chain ID/epoch, algorithm mismatch, swapped metadata, malformed signature, expired key, unauthorized request all fail closed with policy-safe errors.
- Retry identical submission after lost ack yields one original record and stable receipt.
- Different submitted commitment for same block creates durable conflict, never replaces original.
- Crash before durable write never issues success; restart restores original evidence and signature verification.
- No plaintext source log/event payload in Hub storage, audit, tracing, or diagnostics.
- Historical evidence remains verifiable across source key rotation and Hub witness key rotation using identity state valid at historical receipt time.
- Neighbor IDs from another chain or epoch never cross lookup boundaries; prefix / gap / empty index queries correct.
- Query scopes, consent withdrawal, retention, rate limits, source outage/lag, and compromised observer failure cases all covered.
- Integration fixture exercises real Hub signed-MCP/REST membrane and law gate, not a fabricated permissive test-only path.

## 9. Phased delivery / ownership

**Phase 0 — profile contract and fixture first:** inspect actual Hestia chain and Hub ledger types; ratify canonical tuple/receipts/privacy/retention; settle whether verification results must be signed. Implement shared generic conformance fixtures in Web4.

**Phase 1 — Web4 Hub observer MVP:** persistent record + query via canonical membrane and law; per-chain index, receipts, explicit conflict handling, status; tests above. No federation expansion or new consensus.

**Phase 2 — Hestia adapter:** opt-in configuration, submission queue/retry, receipts, status and verifier tooling; Hestia code belongs in its own authoritative repo. Integration tests using synthetic Hestia chains.

**Phase 3 — federation reuse:** adapt R3 Hub-to-Hub witness profile, cross-Hub third-party witnessing, archival/export and multi-witness comparison. Separate governance review for federation disclosure.

**Done when:** demonstrated independent Hub receiving sparse signed Hestia commitments; deterministic durable receipts; authorized three-state lookups and nearest-ID privacy semantics; conflict behavior; evidence survives restart; tests for path verification limitation, consent, policy gate and key rotation; documentation links to SHOW public-domain reference.

## 10. Exclusions and outstanding decisions

Out of scope: full chain replication, remote chain repair, blockchain consensus, transaction re-execution, guarantee of original truth, universal timestamp guarantees, mandatory federation sharing, proprietary patent claims.

Decisions: wire format canonicalization, observation cadence profiles, signature required on verification replies, disclosure classes, signed membership/offboarding retention, origin/Hub identity rotation, replication/witness disaster recovery, witness service fee/resource policy.

**Normative reference:** [SHOW — Sampled Hash Observation Witnessing](../../docs/reference/SHOW_SAMPLED_HASH_OBSERVATION_WITNESSING.md). This PRD adopts its historical/public-domain assessment *with its explicit FTO caveat*.
