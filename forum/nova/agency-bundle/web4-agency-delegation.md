# Web4 Agency Delegation (AGY)

**Status:** Draft • **Last Updated:** 2025-09-15T15:07:46.705282Z • **Layer:** SAL extension

This document defines **Agency Delegation (AGY)** — a special **pairing/binding** whereby a **Client** entity
delegates **authority to act** to an **Agent** entity within a scoped, attestable context. AGY bindings are first-class,
signed objects with well-defined **scope, trust caps, duration, delegatability, witnessing,** and **revocation** semantics.

AGY integrates with **R6** (action grammar), **MRH** (RDF), **T3/V3** (trust/value tensors), **SAL** (citizenship/authority/law),
and **Security** (canonicalization, signatures, inclusion proofs).

---

## 0. Notation & Roles

- **Client** — the delegating entity (principal).
- **Agent** — the delegated entity (authorized actor).
- **Grant** — the signed object conferring agency.
- **Revocation** — the signed object that terminates an active grant.
- **Witness** — co-signer(s) for grant events per society law/quorum.
- **Auditor** — role that can validate/correct post-hoc consequences (T3/V3).

---

## 1. Design Goals

1. **Deterministic authority**: clear, machine-verifiable scope and caps.
2. **Least privilege**: default-deny; scope expands by explicit grants.
3. **Fractal composition**: grants may be nested, inherited, or bridged across societies.
4. **Safety**: revocation, expiry, nonces, replay resistance, witness quorum.
5. **Traceability**: all grants/revocations appear in the **Immutable Record** with inclusion proofs.

---

## 2. Grant Object (Canonical JSON-LD)

```json
{
  "@context": ["https://web4.io/contexts/sal.jsonld", "https://web4.io/contexts/agy.jsonld"],
  "type": "Web4AgencyGrant",
  "grantId": "agy:...",
  "client": "lct:web4:entity:CLIENT",
  "agent": "lct:web4:entity:AGENT",
  "society": "lct:web4:society:ROOT",
  "lawHash": "sha256-...",
  "scope": {
    "contexts": ["finance:payments", "docs:sign"],
    "mrhSelectors": ["web4://org/finance/*", "web4://docs/contracts/*"],
    "r6Caps": {
      "rules": ["LAW-ATP-LIMIT","LAW-KYC"],
      "resourceCaps": {"max_atp": 25, "bandwidth_mbps": 10},
      "roleImpersonation": false
    },
    "methods": ["create","update","approve"],
    "delegatable": false,
    "witnessLevel": 2,
    "trustCaps": {"t3.min": {"temperament": 0.7}, "v3.floor": {"veracity": 0.9}}
  },
  "duration": {
    "notBefore": "2025-09-15T00:00:00Z",
    "expiresAt": "2025-12-31T23:59:59Z"
  },
  "session": {
    "nonce": "b64url-...",
    "audience": ["mcp:web4://tool/*"],
    "bindings": ["mcp:context.proofOfAgency"]
  },
  "witnesses": ["lct:web4:witness:A", "lct:web4:witness:B"],
  "signatures": [{"alg":"Ed25519","kid":"client#1","sig":"..."}, {"alg":"Ed25519","kid":"witness#A","sig":"..."}]
}
```

**Normative:** Fields MUST be canonicalized (JCS/COSE) prior to hashing/signing.

---

## 3. Revocation Object

```json
{
  "@context": ["https://web4.io/contexts/sal.jsonld", "https://web4.io/contexts/agy.jsonld"],
  "type": "Web4AgencyRevocation",
  "grantId": "agy:...",
  "revokedBy": "lct:web4:entity:CLIENT",
  "reason": "key compromise",
  "timestamp": "2025-10-01T12:00:00Z",
  "witnesses": ["lct:web4:witness:A"],
  "signatures": [{"alg":"Ed25519","kid":"client#1","sig":"..."}]
}
```

**Revocation semantics:** immediate; society law may define grace/wind-down for in-flight actions.

---

## 4. R6 Mapping (Normative)

| R6 | AGY Binding |
|----|-------------|
| **Rules** | Derived from society **Law Oracle** + `scope.r6Caps` |
| **Role** | Agent acts under **Agency** role, not Client role (no impersonation unless explicitly allowed) |
| **Request** | Each Agent action MUST include a **proof-of-agency** reference to `grantId` and inclusion proof |
| **Reference** | MRH lookups of grant, prior usage, revocations |
| **Resource** | Enforced via `resourceCaps`; metered and priced |
| **Result** | Outcomes attributed to **Agent**, with **Client** as principal; T3/V3 updated per policy |

---

## 5. MRH (RDF) Model (Normative)

Required classes and properties (see ontology patch):

- Classes: `AgencyGrant`, `AgencyRevocation`, `AgentRole`, `ClientRole`.
- Properties:
  - `web4:hasAgent` (client → agent)
  - `web4:agentOf` (agent → client)
  - `web4:underGrant` (action → grant)
  - `web4:delegationScope` (grant → scope node)
  - `web4:delegatable` (grant → xsd:boolean)
  - `web4:expiresAt` (grant → xsd:dateTime)
  - `web4:revokedBy` (revocation → client)
  - `web4:witnessLevel` (grant → xsd:integer)

**SPARQL example (proof-of-agency):**
```sparql
ASK {{
  ?action web4:underGrant ?grant .
  ?grant  a web4:AgencyGrant ;
          web4:agentOf <lct:web4:entity:AGENT> ;
          web4:hasAgent <lct:web4:entity:AGENT> ;
          web4:expiresAt ?t .
  FILTER(NOW() < ?t)
}}
```

---

## 6. Security

- **Proof-of-Agency** header/field is REQUIRED in MCP/Web4 action transcripts, binding `grantId`, ledger inclusion proof, and audience.
- **Replay protection:** nonce + audience + expiry; bind to session transport keys where available.
- **Witness quorum:** per `witnessLevel`; SAL-critical grants SHOULD require ≥2 witnesses.
- **Revocation checking:** caches MUST re-validate grant status against ledger before high-risk actions.
- **Cross-society:** pin both Client and Agent `lawHash` when acting across inherited-law boundaries.

---

## 7. Delegation & Composition

- **Delegatable grants:** only if `delegatable: true`; child grants MUST be **scope⊆parent** and **expiresAt≤parent.expiresAt**.
- **Bridging:** society-to-society agency requires both societies to publish compatible law bindings; conflicts resolved by higher authority or explicit bridge policy.
- **Temporality:** `notBefore` and `expiresAt` enforce temporal MRH; actions outside window MUST fail.

---

## 8. T3/V3 Implications

- **Agent** accrues T3/V3 for execution quality within AGY scope.
- **Client** accrues reduced/indirect V3 (e.g., validity of delivered value) and shares liability per law policy.
- **Auditor** MAY adjust both sides post-hoc; evidence MUST cite the grant and its scope.

---

## 9. Errors

- `W4_ERR_AGY_EXPIRED` — grant expired
- `W4_ERR_AGY_REVOKED` — grant revoked
- `W4_ERR_AGY_SCOPE` — attempted action outside scope
- `W4_ERR_AGY_WITNESS` — witness quorum not met
- `W4_ERR_AGY_REPLAY` — nonce/audience mismatch
- `W4_ERR_AGY_DELEGATION` — invalid sub-delegation

---

## 10. MCP Binding (Informative)

- **Initialize**: model advertises `proofOfAgency` support.
- **ResourceInvoke**: include `proofOfAgency` with `grantId`, inclusion proof, nonce, audience.
- **Server**: verifies grant status/scope and maps to enforcement (caps/quorum).

---

## 11. Worked Example

- Client `OrgA` grants `BotX` authority to **approve** invoices ≤25 ATP under `finance:payments` for Q4.
- `BotX` invokes `approve(invoice#123)`, attaches proof-of-agency; ledger proves grant; server enforces caps; witnesses co-sign the result.
- Auditor later samples approvals; detects one attempted over-cap approval; issues cautionary T3 delta, no V3 rollback.

---

## 12. Conformance

Implementations MUST:
1. Require **proof-of-agency** on agent-originated actions.
2. Enforce **scope**, **caps**, **temporal bounds**, **witness levels**, and **revocations**.
3. Record **grants** and **revocations** on the immutable record with inclusion proofs.
4. Expose MRH edges for query-based validation.
