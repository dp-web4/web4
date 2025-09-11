# Web4 ATP/ADP Metering Subprotocol
Status: Draft • Last-Updated: 2025-09-11T22:47:56.408268Z
Authors: Web4 Editors

## 1. Purpose
This subprotocol provides a privacy-preserving, auditable way to meter resource exchange
(energy, compute, bandwidth, storage) between Web4 entities. ATP (Alignment Transfer Protocol)
represents *credit* issuance; ADP (Alignment Delivery Proof) represents *evidence* of value
delivered. Settlement MAY be off-ledger with optional anchoring to a lightchain.

## 2. Roles
- **Grantor**: issues ATP credits with constraints (scope, rate, ceilings).
- **Consumer**: spends credits by performing actions that generate ADP usage reports.
- **Witness**: time-stamps, audits, or arbitrates disputes.
- **Anchor** (optional): records hashes or receipts to a chain.

## 3. Messages
All messages are protected in the established session from the Core Handshake and
encoded with the same media profile (CBOR or JSON). Examples shown in JSON.

### 3.1 CreditGrant (Grantor → Consumer)
```json
{
  "type": "CreditGrant",
  "ver": "w4/1",
  "grant_id": "atp-<mb32>",
  "scopes": ["compute:infer", "net:egress"],
  "ceil": {"total": 100000, "unit": "joule-equivalent"},
  "rate": {"max_per_min": 5000},
  "window": {"size_s": 3600, "burst": 2},
  "policy": {"region": ["us-west"], "priority": 3},
  "not_before": "<iso8601>",
  "not_after": "<iso8601>",
  "proof": {"jws": "<issuer-sig-over-body>"},
  "witness_req": ["time", "audit-minimal"],
  "nonce": "<96-bit>",
  "ts": "<iso8601>"
}
```

### 3.2 UsageReport (Consumer → Grantor, optionally Witness)
```json
{
  "type": "UsageReport",
  "ver": "w4/1",
  "grant_id": "atp-<mb32>",
  "seq": 42,
  "window": "2025-09-11T15:00:00Z/2025-09-11T15:01:00Z",
  "usage": [
    {"scope":"compute:infer","amount":420,"unit":"joule-equivalent"},
    {"scope":"net:egress","amount":12,"unit":"MB"}
  ],
  "evidence": {"digest":"b3...","method":"sha256-agg","samples":7},
  "witness": [{"type":"time","ref":"w4idp-...","sig":"<sig>"}],
  "nonce":"<96-bit>",
  "ts":"<iso8601>"
}
```

### 3.3 Dispute (either → other, cc Witness)
```json
{
  "type":"Dispute",
  "ver":"w4/1",
  "grant_id":"atp-<mb32>",
  "seq":42,
  "reason":"exceeds-rate-limit",
  "details":{"limit":5000,"observed":7200},
  "proposed":"partial-accept",
  "nonce":"<96-bit>","ts":"<iso8601>"
}
```

### 3.4 Settle (Grantor → Consumer, cc Witness)
```json
{
  "type":"Settle",
  "ver":"w4/1",
  "grant_id":"atp-<mb32>",
  "up_to_seq":42,
  "balance":{"remaining":95000,"unit":"joule-equivalent"},
  "receipt":"rcpt-<mb32>",
  "anchor":{"txid":"lc:abc123","digest":"..."},
  "nonce":"<96-bit>","ts":"<iso8601>"
}
```

## 4. Semantics
- **Grant validity**: Usage outside `[not_before, not_after]` MUST be rejected.
- **Rate enforcement**: Receivers MUST apply token-bucket semantics using `rate` and `window`.
- **Replay**: (`grant_id`, `seq`) MUST be unique; maintain per-grant replay windows.
- **Partial acceptance**: `Dispute` → `Settle` with reduced acceptance is RECOMMENDED over hard fail.
- **Privacy**: Pairwise W4IDp hides long-lived correlation; witnesses SHOULD see minimal data (digests).

## 5. Witnessing
Witness classes:
- `time`: RFC 3161-like timestamp or verifiable clock proof.
- `audit-minimal`: validates token-bucket math and digests without raw samples.
- `oracle`: domain-specific validation (e.g., power meter attestation).

Witness attestations are COSE/JWS signatures over a canonical form of the message
(or its digest) with role and policy embedded in protected headers.

## 6. Errors (subset)
- `W4_ERR_GRANT_EXPIRED`
- `W4_ERR_RATE_LIMIT`
- `W4_ERR_SCOPE_DENIED`
- `W4_ERR_BAD_SEQUENCE`
- `W4_ERR_WITNESS_REQUIRED`
- `W4_ERR_FORMAT`

## 7. Security Considerations
- Enforce ceilings and windows before cryptographic heavy work during high load.
- Include suite negotiation, `grant_id`, and full policy in the session transcript to
  prevent context confusion.
- Supply-chain: prefer hardware-backed keys (EAT/TPM) for Grantor/Witness in high-stakes contexts.

## 8. Conformance
Profile A (Edge): JSON/JOSE, Ed25519, UsageReport every ≥60s.  
Profile B (Enterprise): CBOR/COSE, ECDSA-P256, batched UsageReport with digest trees, optional lightchain anchor.
