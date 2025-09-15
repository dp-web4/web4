# Agentic Context Protocol (ACP)

**Status:** Draft • **Last Updated:** 2025-09-15T15:27:37.121413Z • **Layer:** SAL/AGY extension over MCP

ACP adds **agentic capability** (initiate, schedule, watch, decide) and **Web4-native delegation (AGY)** to the reactive MCP stack.
It defines plans, intents, human approvals, and execution records that bind to **SAL** (society/authority/law), **AGY** (agency grants),
**MRH** (RDF), **T3/V3**, and the **Immutable Record** (ledger).

---

## 0. Goals (Non-normative)
- Let entities **initiate** actions (not just respond) while remaining safe and auditable.
- Make delegation explicit: every initiated action carries a **proof-of-agency** (AGY grant + ledger proof).
- Provide a **human interface** (Console) for approvals, revocations, explanations, and audits.
- Keep MCP servers unchanged: ACP acts as an **agentic client** orchestrating MCP calls.

---

## 1. Roles
- **ACP Agent** — Initiates actions under valid AGY grants.
- **ACP Scheduler/Watcher** — Time- or event-based triggers.
- **ACP Console** — Human approvals, revocations, explanations, exports.
- **MCP Servers** — Reactive tool/data providers.
- **Ledger** — Immutable record (append/prove).
- **Law Oracle** — Policy, quorum, caps (SAL).
- **Witness / Auditor** — Co-sign critical events; post-hoc validation.

---

## 2. Core Objects (Canonical JSON / JSON-LD)

### 2.1 AgentPlan (Normative)
A declarative plan with triggers, steps, and guard rails.
```json
{
  "@context": ["https://web4.io/contexts/sal.jsonld","https://web4.io/contexts/agy.jsonld","https://web4.io/contexts/acp.jsonld"],
  "type": "ACP.AgentPlan",
  "planId": "acp:plan:...",
  "principal": "lct:web4:entity:CLIENT",
  "agent": "lct:web4:entity:AGENT",
  "grantId": "agy:...",
  "triggers": [
    {"kind":"cron","expr":"0 */6 * * *"},
    {"kind":"event","topic":"invoice.ready"}
  ],
  "steps": [
    {"id":"fetch","mcp":"invoice.search","args":{"status":"ready"}},
    {"id":"approve","mcp":"invoice.approve","args":{"limit":25}}
  ],
  "guards": {
    "lawHash":"sha256-...",
    "resourceCaps":{"max_atp":25},
    "witnessLevel":2,
    "humanApproval":{"mode":"auto-if<=10 else prompt"}
  },
  "expiresAt":"2026-01-01T00:00:00Z",
  "signatures":[{"alg":"Ed25519","kid":"client#1","sig":"..."}]
}
```

### 2.2 Intent (Normative)
An actionable proposal emitted by plan evaluation.
```json
{
  "@context": ["https://web4.io/contexts/acp.jsonld"],
  "type":"ACP.Intent",
  "intentId":"acp:intent:...",
  "planId":"acp:plan:...",
  "proposedAction":{"mcp":"invoice.approve","args":{"id":"INV-123","amount":9.5}},
  "proofOfAgency":{"grantId":"agy:...","ledgerProof":{"hash":"...","block":"..."}},
  "explain":{"why":"match to policy","alts":["route_to_manual"]},
  "needsApproval": true,
  "createdAt":"2025-09-15T15:27:37.121413Z"
}
```

### 2.3 Decision (Normative)
```json
{
  "@context": ["https://web4.io/contexts/acp.jsonld"],
  "type":"ACP.Decision",
  "intentId":"acp:intent:...",
  "decision":"approve|deny|modify",
  "modifications":{"args":{"amount":8.0}},
  "by":"lct:web4:entity:HUMAN-APPROVER",
  "witnesses":["lct:web4:witness:A","lct:web4:witness:B"],
  "timestamp":"2025-09-15T15:27:37.121413Z"
}
```

### 2.4 ExecutionRecord (Normative)
```json
{
  "@context": ["https://web4.io/contexts/acp.jsonld"],
  "type":"ACP.ExecutionRecord",
  "intentId":"acp:intent:...",
  "grantId":"agy:...",
  "lawHash":"sha256-...",
  "mcpCall":{"resource":"invoice.approve","args":{"id":"INV-123","amount":8.0}},
  "result":{"status":"ok","tx":"bank#789"},
  "t3v3Delta":{"agent":{"t3":0.01},"client":{"v3":0.02}},
  "witnesses":["lct:web4:witness:A"],
  "ledgerInclusion":{"hash":"...","block":"..."}
}
```

**Canonicalization:** All objects MUST use JCS (RFC 8785) or COSE/CBOR per Security Framework before hashing/signing.

---

## 3. State Machine (Normative)
1. **Trigger** (cron/event/human) → plan evaluation.
2. Produce **Intent(s)** within AGY scope and SAL law.
3. **Law/Scope Check**: consult Law Oracle; enforce caps/quorum.
4. **Human Gate** (if required) → **Decision**.
5. **Execution**: invoke MCP; write **ExecutionRecord**; witness co-sign; ledger append.
6. **Post-Audit**: optional Auditor sampling; T3/V3 adjustments recorded.

---

## 4. MCP Interop
ACP adds a **proofOfAgency** envelope to MCP invocations; MCP servers remain reactive.
```json
{
  "proofOfAgency": {"grantId":"agy:...","nonce":"b64url-...","audience":["mcp:invoice/*"],"ledgerProof":{"hash":"...","block":"..."}, "expiresAt":"2025-12-31T23:59:59Z"}
}
```

---

## 5. MRH (RDF) Edges (Normative)
- `web4:underPlan` (action → AgentPlan)
- `web4:proofOfAgency` (action → AgencyGrant)
- `web4:executedBy` (action → agent)
- `web4:hasDecision` (intent → decision)
- `web4:hasExecutionRecord` (intent → record)

---

## 6. Security & SAL Alignment (Normative)
- Witness co-sign required for SAL-critical events; pin `lawHash` + ledger proofs.
- Re-check AGY **revocation/expiry** prior to high-risk execution.
- Nonce + audience binding; session-key pinning where transport supports it.
- Cross-society actions: pin both parent/child law hashes when inheritance applies.

---

## 7. Error Profiles
- `W4_ERR_ACP_NO_GRANT`
- `W4_ERR_ACP_SCOPE_VIOLATION`
- `W4_ERR_ACP_APPROVAL_REQUIRED`
- `W4_ERR_ACP_LEDGER_WRITE`
- `W4_ERR_ACP_WITNESS_DEFICIT`
- `W4_ERR_ACP_PLAN_EXPIRED`

---

## 8. Conformance Checklist (Excerpt)
- Require valid **AGY** grant + ledger proof for any initiated action.
- Enforce **scope/caps/temporal** bounds pre-invocation.
- Support **witness co-sign** and ledger append of **ExecutionRecord**.
- Surface **human approval** per plan guards.
- Re-check **revocation** before high-risk steps.
- Emit MRH edges for SPARQL validation; export audit feeds.
