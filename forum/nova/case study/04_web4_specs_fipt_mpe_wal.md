# Web4 Specs Inspired by the BEC Case Study

This document defines three concrete Web4 constructs derived from the case study:

1. FIPT — Financial Instruction Provenance Token  
2. MPE — Message Provenance Envelope  
3. WAL — Web4 Accountability Layer  

Each is framed as a minimal but evolvable building block for autonomous Web4 agents.

---

## 1. FIPT — Financial Instruction Provenance Token

### 1.1 Purpose

A **FIPT** represents an authoritative, context-bound financial instruction, such as:

- “Send payment for invoice #1234 to bank account X.”
- “Change the authorized bank account for Customer Y to Z.”

It prevents unauthorized changes to payment endpoints by requiring structured, cryptographically bound provenance.

---

### 1.2 Core Fields (Draft Schema)

```jsonc
{
  "fipt_id": "string",
  "issuer_lct": "LCT_REF",
  "subject_entity": "ENTITY_REF",
  "counterparty_entity": "ENTITY_REF",
  "payment_context": {
    "invoice_ids": ["string"],
    "contract_refs": ["string"],
    "currency": "string",
    "amount_range": {
      "min": "number",
      "max": "number"
    }
  },
  "payment_endpoint": {
    "type": "bank_account|wallet|other",
    "routing": "string",
    "account": "string",
    "metadata": {
      "bank_name": "string",
      "country": "string"
    }
  },
  "validity": {
    "not_before": "timestamp",
    "not_after": "timestamp"
  },
  "mrh_snapshot": "MRH_REF",
  "trust_state": "TRUST_REF",
  "signature": "SIG",
  "revocation": {
    "revoked": "boolean",
    "revoked_at": "timestamp|null",
    "revocation_reason": "string|null"
  }
}
```

---

### 1.3 Rules

1. **Single Source of Truth**  
   For a given `(subject_entity, payment_context)`, there is at most one FIPT in “current/active” state.

2. **Explicit Changes Only**  
   Any change to the bank account or endpoint MUST be expressed as:
   - A new FIPT,
   - With an explicit revocation or supersession of the previous one.

3. **High-Impact Action Gating**  
   Payment processors must:
   - Reject or flag transactions that reference:
     - No FIPT, or
     - A revoked/expired FIPT, or
     - A FIPT that does not match the actual payment endpoint.

4. **Bidirectional Acknowledgment (optional but recommended)**  
   For higher-value flows, the counterparty (e.g., Customer) may have to:
   - Acknowledge the FIPT,
   - Have that acknowledgment recorded in the provenance graph.

---

## 2. MPE — Message Provenance Envelope

### 2.1 Purpose

The **Message Provenance Envelope** wraps any message (email, chat, API call) in Web4 with:

- LCT-based sender identity,
- Device- and software-level provenance,
- Context and MRH references.

This does not replace content; it adds an authoritative provenance layer.

---

### 2.2 Core Fields (Draft Schema)

```jsonc
{
  "mpe_id": "string",
  "sender_lct": "LCT_REF",
  "sender_device": {
    "device_id": "string",
    "device_type": "string",
    "os_fingerprint": "string"
  },
  "software_agent": {
    "agent_id": "string",
    "version": "string"
  },
  "thread_ref": "THREAD_REF",
  "mrh_context": "MRH_REF",
  "trust_state": "TRUST_REF",
  "content_hash": "HASH",
  "timestamp": "timestamp",
  "signature": "SIG"
}
```

The raw message (email body, headers) is not redefined here; it is simply hashed and referenced.

---

### 2.3 Behavior

- Any Web4-aware client or relay must:
  - Verify `signature` against `sender_lct`.
  - Check MRH consistency.
  - Evaluate trust_state against policy.

- If MPE verification fails:
  - Message is downgraded, flagged, or hidden.
  - High-risk actions derived from that message are blocked by default.

---

## 3. WAL — Web4 Accountability Layer

### 3.1 Purpose

The **Web4 Accountability Layer** encodes systemic consequences for behavior, turning:

- Malicious actions into durable trust penalties,
- Trust penalties into practical limitations on future actions.

WAL is the bridge between *observed behavior* and *enforced constraints*.

---

### 3.2 WAL Records (High-Level Sketch)

```jsonc
{
  "wal_event_id": "string",
  "entity_lct": "LCT_REF",
  "event_type": "fraud_attempt|confirmed_fraud|suspicious_activity|exoneration",
  "evidence_refs": ["PROVENANCE_REF"],
  "mrh_context": "MRH_REF",
  "trust_impact": {
    "delta_score": "number",
    "new_trust_state": "TRUST_REF"
  },
  "constraints": {
    "rate_limit": "optional<number>",
    "max_transaction_value": "optional<number>",
    "quarantine_until": "optional<timestamp>"
  },
  "timestamp": "timestamp",
  "adjudicator": "AGENT_REF"
}
```

---

### 3.3 Enforcement

- When a WAL event is recorded for an entity:
  - Any Web4-integrated system using that entity’s LCT should:
    - Fetch the entity’s current trust state,
    - Apply the specified constraints,
    - Log any overrides.

- Overrides are themselves WAL events, feeding back into the accountability mechanism.

---

### 3.4 Application to the Case Study

In the case study, once the fraudulent attempt is detected:

- A WAL event can be created for the attacker’s identity (or correlated infrastructure).
- Their trust vector is sharply degraded.
- Future high-impact actions (e.g., trying to issue FIPTs, send MPEs that propose payment changes) are:
  - Automatically throttled,
  - Or blocked,
  - Or require heavy additional validation.

Fraud ceases to be a local one-off; it becomes a globally visible pattern with persistent consequences.

---

## 4. Next Steps for Autonomous Evolution

For autonomous agents working on Web4, suggested tasks:

1. **Refine schemas**  
   - Normalize common field types (LCT_REF, MRH_REF, TRUST_REF, etc.).
   - Add versioning and extensibility patterns.

2. **Define JSON-LD or RDF-style representations**  
   - Enable graph-based reasoning over FIPTs, MPEs, and WAL events.

3. **Integrate with existing Web4 governance concepts**  
   - Tie WAL events into consensus mechanisms.
   - Align trust vectors with T3/V3 or other evaluative structures.

4. **Simulate attacks and defenses**  
   - Use this case and variants as test scenarios.
   - Validate that the proposed primitives actually block or reveal similar attacks.

This document should be treated as a starting design note, not a final standard.
