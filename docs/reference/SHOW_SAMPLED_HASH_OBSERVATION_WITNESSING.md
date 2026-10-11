# SHOW — Sampled Hash Observation Witnessing

**Status:** Design/reference; proposed interoperable Web4 primitive, not a claim of implemented behavior  
**Date:** 2026-10-11  
**Scope:** Chain-agnostic independent historical integrity observation  
**Related:** [Hub federated PRD R3](../../hub/docs/PRD_HUB_V2_FEDERATED.md), [Hub–Hestia witnessing PRD](../../hub/docs/PRD_HUB_HESTIA_SHOW_WITNESSING.md)

## 1. Summary and intended guarantee

Sampled Hash Observation Witnessing (SHOW) is a simple independent observation service. An origin chain periodically submits a block identifier, cryptographic commitment (typically the block hash/head), and canonical metadata to a witness. The witness durably preserves the *original observation* and its own receipt time. Later a verifier presents the same block identity and proposed commitment. The witness answers MATCH, MISMATCH, or NOT_RECORDED. For NOT_RECORDED it may provide the immediately preceding and following *observed block IDs* (not the retained hashes), within the same chain and unambiguous ordering namespace.

SHOW addresses a narrow question: **is the presented commitment consistent with the commitment independently recorded earlier?** It does **not** assert the truth of source events, uninterrupted availability, chain authenticity absent source identity validation, authorization of actions, or correctness of unexamined intermediate links. A successor checkpoint cryptographically commits to preceding chain content *if and only if* the verifier independently verifies a valid path from that content to the checkpoint.

The witness does not compute or repair origin-chain history. It does not join consensus, grant role authority, execute member actions, or require access to plaintext events. Separation is deliberate: **witness, don't control**.

## 2. Minimal protocol

### 2.1 Canonical observation identity and payload

- Identity key: `(origin_chain_id, epoch_or_generation_id, block_id, commitment_scheme)`. Epoch prevents ID collision across reset/rollover; a fixed global chain ID alone is not sufficient.
- Observation commitment: canonical typed tuple containing the key, algorithm identifier, block hash/head commitment, metadata digest, and origin signing identity as required by the profile. Use domain separation and deterministic encoding; avoid ambiguous string concatenation.
- Metadata explicitly distinguish **origin assertions** (source timestamp, chain height, previous block reference) from **witness-observed** fields (witness receipt time, record sequence, witness identity, signature). Witness receipt time is not proof that the source event happened at that time.
- Validate origin signature/identity and allowed algorithm suite when required by the governed service profile. Unsupported, malformed, or unauthorized submissions must not be silently recorded as trusted.
- Store immutable original observations. Repeated identical submissions may be idempotent; different commitments for the same identity produce a **conflict** record with references to both observations, not last-write-wins.
- Preserve original observation bytes/canonical commitment or enough verifiable material to compare exactly. Loss/corruption of witness storage is a distinct failure, not NOT_RECORDED.

### 2.2 Record

`OBSERVE(key, commitment, metadata, origin_proof)` -> signed, timestamped receipt including witness ID, observation sequence, canonical record digest, and status NEW | IDEMPOTENT | CONFLICT. Receipt includes enough context to prevent cross-chain and cross-epoch replay. An acknowledgement is emitted **only after durable commit**.

The cadence may be time-based, block-count-based, and/or event-triggered; missed samples must remain apparent. SHOW does not imply that every block was observed.

### 2.3 Verify

`VERIFY(key, candidate_commitment, candidate_metadata_digest)` ->

- **MATCH**: exact canonical comparison with the immutable original observation at this key. Include observed_at and evidence receipt reference (policy permitting). A match does not endorse underlying events.
- **MISMATCH**: observation exists but candidate differs. Preserve minimal, policy-governed evidence; never return the stored hash by default.
- **NOT_RECORDED**: no observation for this key; return nearest preceding and succeeding *observed block IDs* in the same chain/epoch, if they exist, never their hashes. Unknown chain, inaccessible namespace, invalid request, unavailable storage, and unsupported algorithm must have *distinct error results* rather than misleading NOT_RECORDED.
- **CONFLICT**: multiple historical observations for same key with differing commitments, if a conflicted key is queried. A conflicted observation must not be reduced to an ordinary MATCH.
- For membership privacy, policy can suppress neighbor IDs altogether where index disclosure is sensitive. The basic SHOW profile returns them.

The conceptual three-state SHOW result remains MATCH / MISMATCH / NOT_RECORDED **for non-conflicted valid records**; conflict and protocol failures are separate status/error channels.

### 2.4 Example

Samples exist for chain C, epoch E, block IDs 100 and 200. Query for 150 returns `NOT_RECORDED(before=100, after=200)`. This alone proves nothing about block 150. The verifier may obtain and verify a complete linked path from 150 to 200 and submit the locally calculated commitment for block 200. MATCH at 200 then anchors the verified path (subject to the hash/security assumptions). Merely matching both endpoint hashes without validating links does **not** validate the intervening segment.

### 2.5 Trust and cryptographic limits

Threats: source rewrites or rollback; multiple histories/equivocation; malicious or colluding witness; backdated source timestamps; replay and chain identity collision; forged/rotated keys; lookup enumeration; hash algorithm downgrade; observation loss; service outage; timing analysis.

A single witness gives *independent recordation*, not mathematical immutability. Witness signed receipts, append-only authenticated internal storage, retention/backups, third-party replication, and/or multiple independent witnesses can improve confidence but introduce independent trust assumptions. Observe and verify time and signature semantics precisely. A hash only binds preceding data when the construction/path is actually checked. Receipt does not mean legal attestation or governance authorization.

## 3. Public-domain historical foundation and patentability/FTO posture

**Engineering assessment: the foundational cryptographic technique used by SHOW is believed to be public-domain technology, as taught by expired early cryptographic authentication patents.** This is a documented belief, **not** a formal clearance opinion for every implementation detail or every jurisdiction. Expiration of one patent permits practicing *its claims*; it does not immunize later, independently patented improvements. Do not assert that all SHOW embodiments are free of active claims.

Primary foundation: **US 5,781,629 A, “Digital Document Authentication System,” Haber and Stornetta**, filed 1997, issued July 14, 1998, reported expired (lifetime). [Full patent and claims](https://patents.google.com/patent/US5781629A/en).

Significant teachings, relevant irrespective of exact claim mapping:
- Independently secured/publicly published cryptographic commitments to collections of prior records;
- Retrospective authentication of documents against previously secured commitments;
- Local registration/requester and separate service bureau architectures;
- Aggregation structures including *linear hash-linked lists* (particularly **Figure 7**), not only tree structures;
- Intermittent publication of cumulative hashes/checkpoints rather than compulsory publication of every underlying record;
- Identification and verification through earlier published links and authentication paths.

Mapping to SHOW: locally maintained linked history -> existing Hestia/Web4 chain; periodic published linking value -> periodic SHOW observation; third-party publication/service bureau -> independent Hub witness; later document authentication -> submitted hash comparison. **These teachings establish prior-art support for intermittent external commitment and later integrity checking.** The patent does **not** expressly describe SHOW's particular three-state query API or its nearest-observed-ID-only response; those are proposed protocol design choices, not claimed as inventions here.

Other historical foundations and relevant comparisons:
- [US 5,136,647 A](https://patents.google.com/patent/US5136647A/en), earlier secure timestamping;
- [RFC 3161](https://www.rfc-editor.org/rfc/rfc3161), Time-Stamp Protocol (2001);
- [US 8,719,576 B2](https://patents.google.com/patent/US8719576B2/en), distributed calendar commitments, reported expired;
- [RFC 9162](https://www.rfc-editor.org/rfc/rfc9162.html), Certificate Transparency v2, authenticated log auditing (not automatically equivalent to SHOW);
- [US 11,658,831 B2](https://patents.google.com/patent/US11658831B2/en), later active “Validation of the Integrity of Data.” Its **issued independent claims** require a specialized source-chain construction (multiple earlier hash references, salted hashes, internal block confirmation). These requirements are not part of the passive SHOW observer; disclosure in its specification remains prior art even if issued claims are narrower. Do not infer immunity for a deployment whose source chain itself practices those claims.
- Relevant later improvements include [US 10,460,289 B2](https://patents.google.com/patent/US10460289B2/en) on auditing certified blockchain checkpoints and other active checkpointing claims. Implementation-specific clearance may be required.

**Public-domain posture for Web4:** use established primitive(s), publish an interoperable open specification, avoid claiming novelty over historical hash witnessing, keep the implementation narrowly scoped. Before production/commercial deployment, conduct an implementation-specific active-claims assessment if legal certainty is required. Country, claim construction, current legal status, and equivalents matter. The citations above are technical/historical references, not a legal opinion.

## 4. Web4 architectural location

SHOW is a **separate evidence service**. An ordinary Hub may act as the witness for member Hestia chains or for federated peer Hub chains. Witness evidence can feed governance as evidence, never as authority by itself. Recording and exposing evidence are themselves governed actions and must pass the single canonical Hub law gate. No second ad-hoc authorization path. The witness must not demand custody of Hestia keys or direct ledger write access.

Canon / non-duplication: functional implementation and generic conformance tests belong in `dp-web4/web4` per [Hub implementation authority](HUB_IMPLEMENTATION_AUTHORITY.md); `4-hub` is a mirror. Hestia-specific adapter or UX belongs in Hestia, not a duplicate SHOW service. Reuse existing Web4 signing, LCT, storage, and policy utilities rather than creating a parallel trust vocabulary.

## 5. Interoperability and conformance tests

Baseline fixtures:
1. valid record, matching verification;
2. recorded ID, wrong hash or metadata digest -> mismatch;
3. unsampled ID between two observations -> NOT_RECORDED with correct same-epoch neighbor IDs only;
4. before-first and after-last -> one nullable neighbor; empty epoch -> neither;
5. same ID different chain/epoch -> never cross-match;
6. canonical encoding and algorithm/version disagreement -> explicit failure;
7. replayed identical submit -> idempotence, no counterfeit second observation;
8. conflicting submit -> append-only conflict evidence and separate query result;
9. unknown chain vs hidden chain/unauthorized query -> policy-safe error handling;
10. witness crash before durable commit -> no successful receipt;
11. witness crash after commit before ack -> retry retrieves stable receipt;
12. source rewrites unobserved segment but presents original witnessed endpoint -> endpoints alone do not certify segment; path validation detects inconsistent linkage;
13. witness signs receipt for a historical digest, then observed commitment is modified -> integrity alarm;
14. origin key rotation/revocation -> historically signed receipts remain verifiable under archived valid-at-observation identity state; new submissions follow current law;
15. lookup abuse, timing, enumeration and data retention controls.

## 6. Open decisions

- Choose canonical wire encoding and domain-separated commitment tuple under existing Web4 protocol conventions.
- Define allowed cadence, trigger policy, signed receipt schema, retention and pruning commitments.
- Define member consent/delegated authorization and verifier privacy semantics under Hub law.
- Whether to include witnessed LCT identity, law version, and origin chain head metadata by profile.
- How to expose historical witness receipts if a member leaves or a Hub dissolves.
- Distinguish witness observation from actual independent clock/time assurance.

**Companion implementation plan:** [PRD — Hub Witnessing of Member Hestia Chains](../../hub/docs/PRD_HUB_HESTIA_SHOW_WITNESSING.md).
