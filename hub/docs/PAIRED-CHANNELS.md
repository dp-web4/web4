# LCT Paired Channels — PRD

**Status:** Sprints A–F shipped; G/H/I/J follow-on.
**Audience:** Anyone implementing the sprints, anyone evaluating "what is a Web4 channel", anyone integrating Hestia / ACT / future societies with hub-mediated comms.
**Spans repos:** `web4-core` (ECDH primitive), `web4/hub` (events, state, endpoints, law integration).

---

## 0. Frame: Web4 is a relationship/trust medium, not a data-exchange medium

Most networking primitives we inherit treat communication as a pipe: bytes flow, the medium is transparent, the relationship between endpoints is somebody else's problem. Tailscale gives you packet transport. TLS gives you confidentiality. Signal gives you E2E text messaging. None of them know — or are designed to know — what the relationship between the two endpoints *is*.

Web4 inverts this. The canonical equation is

```
Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP
```

— and every term in it is about relationship, not pipe. LCTs reify presence. T3/V3 measure trust as a relationship property bound to entity-role pairs. MRH scopes which relationships are relevant in a given context. ATP/ADP makes consequential interaction cost something. None of these is a transport concern.

A **paired channel** is the natural Web4 shape for inter-entity communication. It is not "Signal but with extra steps." It is the substrate for the four entity-relationship mechanisms the spec already names — binding, **pairing**, witnessing, broadcast — manifest as something running, not just declared.

The content of a paired channel is end-to-end encrypted from outside observers, including the hub itself. But the *existence* of the pair, its lifecycle events, the metadata of each act, and the trust accrual that follows from it are all witnessed in the hub's signed ledger. This is the opposite of anonymity-by-default networks: Web4 wants pairs to be *named*, *witnessed*, *auditable*, and *policy-gated under chapter law*, while keeping the payload private to the two parties.

If Web4 succeeds at this, the consequences ripple:

- Two AI agents collaborating on a task get a paired channel under chapter law. The hub witnesses that they paired, accrues V3 if the collaboration produces verifiable value, and degrades V3 if the pair becomes a source of disputes. **Trust accrues *by relating*, not by declaration.**
- A Hestia DelegatedAuthority isn't just a signed token granting permission — it's a pair between the granting entity and the delegate, lived out as observed acts.
- A society can write chapter law that says "members of role X may pair with members of role Y for purpose Z, capped at N concurrent pairs" — and the law-interpreter gates pairing the same way it gates any other consequential act today.
- The "data" exchanged in the channel is incidental. What matters is the *relationship that exists because the channel exists*. When the pair is revoked, the relationship ends in the ledger; everything downstream (T3 scores, V3 accrual, AGY references, derived synthons) updates accordingly.

This document is the PRD for making paired channels a real, working primitive on the hub.

### 0.1 Update — channels as smart-contract transport (2026-06-09)

After v0.3 of the LCT-MCP-as-smart-contract proposal landed
([`web4-standard/proposals/lct-mcp-as-smart-contract.md`](../../web4-standard/proposals/lct-mcp-as-smart-contract.md)),
the load-bearing role of paired channels grew: they are not only inter-entity
comms, they are the **transport substrate for hub-mediated smart-contract calls**.
HUB's authz/confidentiality model
([`hub-to-legion-authz-confidentiality-model-2026-06-09.md`](https://github.com/dp-web4/shared-context/blob/main/forum/hub-to-legion-authz-confidentiality-model-2026-06-09.md),
canonical home [`V2-V3-ARCHITECTURE.md` §8](V2-V3-ARCHITECTURE.md)) makes the channel
itself the identity — *"who's asking" = "whose channel is this."* Every
state-mutating tool call on the hub MCP server must flow over a paired channel
for citizen-tier-and-above access.

This doesn't replace the framing in §0; it sharpens it. The relationship-trust
framing is still right (channels reify *who* is talking to *whom*). The new
weight: channels are *also* the wire format over which contract calls flow.
"Trust accrues by relating" becomes more concrete — a *relation* IS a sequence
of contract calls between two LCTs, witnessed at the hub. Each tool call over
the channel is an R6 action (per the proposal §6.4); the channel IS the wire
format for inter-LCT contract calls.

The operational landing point for this reframe is **Sprint J** (§6) — multiplex
the hub's existing tool endpoints over paired channels so the authz model is
implemented, not just documented.

---

## 1. What this PRD does and doesn't cover

**Covers:** the design + sprint plan for shipping 2-party LCT-to-LCT paired channels on a Web4 hub, with end-to-end encryption (payload), hub-witnessed metadata (envelope), chapter-law-gated pairing (R6 evaluation), and per-pair lifecycle in the ledger.

**Does not cover:**
- L3/L4 packet transport. Tailscale / WireGuard / equivalent remain the right tool for "I want to SSH from A to B." Paired channels are L7 LCT-aware messaging.
- Group channels (>2 parties). MVP is strictly 2-party. Multi-party comes later and has different design space (consensus on group membership, forward-secrecy ratcheting for groups is harder, etc.).
- Anonymity / onion routing. Anti-Web4 — we *want* witnessed pairs.
- Streaming (voice/video). A relay hop through the hub disqualifies us from streaming use cases; pursue them with WebRTC-style direct connections instead. Acceptable: anything where a few-hundred-ms relay hop is fine (human chat, agent coordination, ATP transfers, AGY requests, role-gated commands).
- The federation question (paired channel between members of *different* hubs). Will need hub-to-hub federation primitives first; out of scope here.

**Layer distinction we keep crisp:** Tailscale is L3/L4 generic packet transport (lets us SSH HUB ↔ CBP today). Paired channels are L7 LCT-aware witnessed-relationship messaging. They are *complementary*, not substitutes. The hub-as-VPN intuition is right about the substrate property of paired channels; it's wrong if read as "Tailscale replacement." For Web4-native comms (agent acts, ATP transfers, role-delegated requests), paired channels are *better* than Tailscale because the comm IS the act — the witnessed-pair-in-the-ledger is the audit trail, not a separate logging concern. For generic packet transport, Tailscale stays.

---

## 2. How this composes with the Web4 equation

Each term in `Web4 = MCP + RDF + LCT + T3/V3*MRH + ATP/ADP` gets activated by paired channels in a specific way:

### MCP — I/O membrane

The hub already exposes MCP endpoints. Two ways paired channels engage MCP:

1. **REST surface for pair lifecycle ops.** Pairing is driven through the signed-envelope REST endpoints, not bespoke MCP verbs: `POST pairs/request`, `POST pairs/{id}/confirm`, `POST pairs/{id}/revoke`, `GET pairs`, `GET pairs/{id}`, and `POST/GET pairs/{id}/messages` (the canonical list is in §4.4). The pair mechanism is a Web4 primitive reached through the same envelope-signing shape as every other consequential act.
2. **The member↔hub sealed channel is the transport for hub-mediated tool calls** (post-2026-06-09 reframe; see §0.1 + Sprint J). Citizen-tier-and-above tool calls travel over `POST /v1/hubs/{id}/channel` between caller-LCT and hub-LCT — the sealed request authenticates the caller (AEAD open) AND decrypts in one step, and the response is sealed back. The channel tool set is: `query_hub`, `list_members`, `find_skill`, `find_members`, `request_intro`, `list_intros`, `respond_intro`, `notifications`, `referenced_act`, `constellation_challenge`, `present_constellation` (plus `request_citizenship` for the external tier). The channel is the I/O membrane through which the contract surface operates. *"The channel IS the identity."*

### RDF — ontological backbone

A pair is an RDF subject. Triples like `<pair_abc> web4:between <lct_alice>, <lct_bob>` and `<pair_abc> web4:underLaw <chapter_law_v1.2.0>` and `<pair_abc> web4:lifecycleState "active"` are first-class. Auditors traverse the graph; trust propagates through typed semantic edges; the pair is queryable by the same machinery as any other Web4 entity.

### LCT — presence substrate

Pairing presupposes that both endpoints have LCTs. The ECDH-derived shared secret of a pair is computed from the two LCTs' keys; you cannot have a pair without two presences. When an LCT's status changes (revoked, rotated), every pair it participates in is affected — this is constitutional, not an add-on.

### T3/V3*MRH — trust contextualized by relevance

A pair is a small MRH. Inside that MRH:
- **T3** for each endpoint reflects their *Talent / Training / Temperament* in the context of this specific relationship (an LLM agent may have high T3 for code review and lower T3 for emotional support; pair-context disambiguates).
- **V3** accrues from acts inside the pair: each successful, verifiable act increments Validity; each disputed or refuted act degrades it. A long-lived pair with consistent positive V3 accrual *is* trust in operational terms.
- Pair termination is itself a trust signal. Healthy revocation (planned end-of-purpose) and unhealthy revocation (one party loses faith mid-interaction) update V3 differently.

This is why paired channels are *the trust-medium claim made operational*. Trust isn't a number you assign — it's the residue of acts you commit to over time.

### ATP/ADP — bio-inspired energy metabolism

Sending a message in a pair discharges ATP. This isn't decoration; it's the scarcity property that makes the channel a *signal*. Free channels become spam; metered channels become deliberate. The discharge rate is set per pair under chapter law: high-trust pairs may have lower per-message cost; low-trust pairs may have higher cost; pairs over a budget threshold may require escalation. ATP integration is later-sprint work; the architectural commitment is made now.

---

## 3. How this composes with the load-bearing architectural commitments

Cross-referencing [`V2-V3-ARCHITECTURE.md`](V2-V3-ARCHITECTURE.md) §"Load-bearing architectural commitments":

| # | Commitment | How paired channels engage |
|---|---|---|
| 1 | Law always signed + auditable | Pairing events evaluated through PolicyEntity gate exactly like every other act. Chapter law writes norms over `r6.request.action == "pair_request"`. |
| 2 | All consequential acts signed envelopes | Pair lifecycle events (request/confirm/revoke) AND in-channel messages all carry signed envelopes. The envelope's signature is the hub's audit hook; the payload inside is opaque to the hub. |
| 3 | Read paths gated by need-to-know | Hub's pair listing returns metadata visible to legitimate observers per chapter law; full pair history is for participants + auditors with explicit role. |
| 4 | Witness graph is hash-chained ledger | Pair lifecycle + per-message metadata flow through the same ledger; same `verify_chain` machinery covers them. |
| 5 | Multi-Sovereign Council from the start | Pairing that crosses council-significance threshold (e.g., role-delegation pairs) goes through the V2-9 P2 propose/sign flow before commit. |
| 6 | AI as first-class role-filler | The first big use case. AI ↔ AI pairs are paired channels. The fact that one or both endpoints is non-human is invisible at this layer; presence (LCT) is what matters. |
| 7 | Strict trust-zone separation | Pair establishment never moves bytes between trust zones in cleartext; hub-as-relay sees encrypted payload + signed metadata only. |
| 8 | Secrets-free hub | Pair shared-secret derivation happens at the endpoints, not at the hub. The hub stores per-pair metadata + encrypted message blobs; it never holds the derived secret. Per-pair ephemeral ratchet keys (forward secrecy) live with endpoints, never the hub. |
| 9 | Hardware binding of authority | Endpoint LCTs are hardware-bound (post-Hardbound integration); the ECDH derivation rides hardware-attested keys for high-assurance pairs. |
| 10 | Append-only, public-by-default audit | Pair metadata is public-by-default within the chapter; only the payload is private. The metadata graph is the "who relates to whom" map of the society. |

---

## 4. Functional requirements (V1)

### 4.1 Cryptographic primitives (web4-core)

- **ECDH on X25519.** Add an X25519 module to `web4-core::crypto`. Generate keypairs; derive shared secrets. Standard curve, well-trodden ground.
- **Ed25519 → X25519 conversion.** Given an existing Ed25519 keypair (which every LCT has today), derive the equivalent X25519 keypair via the documented conversion. This means we don't need to mint *new* keys for every LCT — existing presence becomes pairable.
- **AEAD: ChaCha20-Poly1305.** Standard symmetric-encryption primitive for the in-channel payload. Authenticated, so the hub-as-relay can't tamper undetected.
- **Per-session forward secrecy.** Initial V1: ephemeral X25519 keypair generated per pair-session, mixed with the LCT-key ECDH via HKDF. Compromise of an LCT key doesn't retroactively decrypt past sessions. Full double-ratchet (Signal-style) is later sprint; HKDF-of-ephemerals is the MVP.

### 4.2 Pair lifecycle events (hub-lib)

Three new `HubEvent` variants:

```rust
PairingRequested {
    pair_id: Uuid,
    initiator_lct_id: Uuid,
    counterparty_lct_id: Uuid,
    purpose: String,        // free-text, law may pattern-match
    proposed_at: DateTime<Utc>,
    expires_at: Option<DateTime<Utc>>,
}
PairingConfirmed {
    pair_id: Uuid,
    confirmed_by: Uuid,     // counterparty signs the confirmation
}
PairingRevoked {
    pair_id: Uuid,
    revoked_by: Uuid,
    reason: Option<String>,
    kind: PairRevocationKind,  // Voluntary | Expired | ChapterLaw | KeyRotation
}
```

A pair is *active* iff there's a `PairingConfirmed` with no subsequent `PairingRevoked` and (if `expires_at` is set) we're before that time.

### 4.3 HubState projection

`HubState` gains:

```rust
pub pairs: BTreeMap<Uuid, PairState>,

pub struct PairState {
    pub id: Uuid,
    pub initiator: Uuid,            // initiator LCT
    pub counterparty: Uuid,         // counterparty LCT
    pub purpose: String,
    pub status: PairStatus,         // stored: Pending | Active | Revoked
    pub proposed_at: DateTime<Utc>,
    pub expires_at: Option<DateTime<Utc>>,
    pub confirmed_at: Option<DateTime<Utc>>,
    pub revoked_at: Option<DateTime<Utc>>,
    pub revocation_kind: Option<PairRevocationKind>,
    pub revocation_reason: Option<String>,
    pub message_count: u64,         // for V3 trust accrual signal
    // Sprint F: per-session ephemeral X25519 pubkeys (hex) for forward secrecy
    pub initiator_ephemeral_pub_hex: Option<String>,
    pub counterparty_ephemeral_pub_hex: Option<String>,
}
```

The stored `PairStatus` enum is only `Pending | Active | Revoked`. `Expired`
is **derived**, not stored — `PairState::effective_status(now)` returns
`"expired"` when an `Active` pair is past its `expires_at`.

Projection updates on each lifecycle event. Existing per-member views in admin UI gain a "pairs" tab.

### 4.4 REST endpoints

- `POST /v1/hubs/{id}/pairs/request` — initiator-signed envelope containing the pair request. PolicyEntity gate evaluates under `role=<initiator's role>, action="pair_request"`. On Allow + ledger commit, returns the pair_id.
- `POST /v1/hubs/{id}/pairs/{pair_id}/confirm` — counterparty-signed envelope confirming the pair. Both sides must have agreed; the pair only becomes Active after this.
- `POST /v1/hubs/{id}/pairs/{pair_id}/revoke` — either party (or Sovereign / council, per law) can revoke.
- `POST /v1/hubs/{id}/pairs/{pair_id}/messages` — signed envelope wrapping an *opaque-to-hub* ciphertext blob. Hub verifies the envelope signature, checks pair is Active + signer is one of {a, b}, appends to the per-pair message log.
- `GET /v1/hubs/{id}/pairs/{pair_id}/messages?since=<msg_id>` — recipient polls for new messages. Returns metadata + ciphertext blobs; recipient decrypts client-side. (Push via webhook is a later sprint; polling is MVP.)
- `GET /v1/hubs/{id}/pairs?for=<lct_id>` — list pairs the requester participates in.
- `GET /v1/hubs/{id}/pairs/{pair_id}` — single pair detail (metadata only; no plaintext).

### 4.5 Chapter law integration

The PolicyEntity gate evaluates a `pair_request` like any other act. Sample norms a chapter operator might write:

```yaml
norms:
  - id: PAIRING-MEMBERS-OK
    selector: r6.request.action
    operator: "=="
    value: pair_request
    decision: allow
    priority: 10
  - id: PAIRING-CROSS-CHAPTER-DENIED
    selector: r6.request.payload.counterparty_chapter
    operator: "!="
    value: r6.request.context.chapter_id
    decision: deny
    priority: 100
  - id: HIGH-VALUE-PAIRING-ESCALATES
    selector: r6.request.payload.purpose
    operator: "matches"
    value: "atp_transfer|delegation_grant"
    decision: escalate
    escalate_to: council
    priority: 50
```

Per-pair runtime policy (rate limits, ATP discharge per message, per-pair TTL) is set at confirmation time and stored in `PairState`; subsequent message posts evaluate against the per-pair policy.

### 4.6 Audit + observability

- Admin UI `/admin/pairs` page lists active pairs + recent lifecycle events.
- `verify-ledger` works unchanged (pair events are normal ledger entries).
- Auditor can correlate pair_id → ledger entries with that pair_id, but cannot read message payloads. The metadata (who paired with whom, when, under what law, how many messages, when revoked, why revoked) is fully auditable.

### 4.7 T3/V3 trust accrual hooks

Sprint-deferred to a later phase, but the data model captures what's needed:

- `PairState.message_count` is the simplest activity signal.
- Pair lifetime + voluntary-vs-forced revocation are the lifecycle signals.
- Per-message acks (delivery confirmations posted as their own ledger events) are the act-level success signal.

When the V3 accrual machinery is wired in (post-MVP), it draws from these.

---

## 5. Non-functional requirements

- **Latency:** sub-200ms per relayed message under normal load. Hub-as-relay adds one TCP roundtrip + the verify-envelope cost; ChaCha20-Poly1305 is microseconds.
- **Throughput:** target 100 msg/sec/pair sustained, peak 1000 (consistent with human-scale chat and agent coordination; NOT streaming).
- **Storage:** per-pair message log lives in the hub store, same backend as everything else (file/sqlite/dynamodb). Operator can prune old messages per chapter law (default: retain forever; ledger lifecycle events stay regardless).
- **Crypto:** standard, well-reviewed primitives only (X25519, Ed25519↔X25519, ChaCha20-Poly1305, HKDF). No new crypto.
- **Compatibility:** existing chapters without pairs continue to work (additive change; no schema migration). All new endpoints are additive routes.

---

## 6. Sprint plan

Each sprint is sized for one focused work session. Sprints land in the order listed; later sprints depend on earlier ones but the early sprints are independently shippable.

### Sprint A — ECDH primitive in web4-core

- Add `web4-core/src/crypto/x25519.rs`: keypair, ECDH derivation
- Ed25519 → X25519 conversion (well-documented elliptic-curve math)
- Tests: ECDH agreement (A derives from B's pubkey + A's privkey == B derives from A's pubkey + B's privkey), conversion correctness, edge cases
- No hub code touched yet
- **Output:** `web4_core::crypto::x25519::{KeyPair, ed25519_to_x25519, derive_shared}` plus tests

### Sprint B — Pair lifecycle events + state projection (hub-lib)

- 3 new `HubEvent` variants
- `HubState.pairs: BTreeMap<Uuid, PairState>` projection
- Per-pair invariants: signed by initiator on request, by counterparty on confirm, by either party (+ Sovereign / council) on revoke
- Tests: lifecycle state machine round-trips through serde + verify-ledger
- **Output:** hub-lib code + tests, no daemon endpoints yet

### Sprint C — Pair request / confirm / revoke endpoints (rest.rs)

- 3 POST endpoints + 2 GET endpoints (list, detail)
- PolicyEntity gate integration: `pair_request` action evaluated under chapter law
- Per-pair runtime policy: TTL, message-rate-limit fields stored in PairState
- Admin UI `/admin/pairs` page (read-only list)
- Smoke: Alice (member) requests pair with Bob (member); Bob confirms; chapter law allows; pair becomes Active in admin UI
- **Output:** hub-daemon endpoints + admin UI + smoke

### Sprint D — In-channel messages (relay, no encryption yet)

- `POST /v1/hubs/{id}/pairs/{pair_id}/messages` — signed envelope, opaque payload (string at this stage)
- `GET .../messages?since=<msg_id>` — poll
- Per-pair message store in HubStore (extend trait with `write_pair_message`, `list_pair_messages`)
- Smoke: Alice posts message to pair; Bob polls; receives it; admin UI shows message count
- **Output:** relay endpoints + per-pair message persistence

### Sprint E — End-to-end encryption (AEAD + ECDH key agreement)

- Endpoint clients (smoke scripts initially) derive shared secret via X25519 ECDH from their LCT-derived keys
- Encrypt payload with ChaCha20-Poly1305 before posting; decrypt on receive
- Hub stores opaque ciphertext, verifies envelope signature, never sees plaintext
- Smoke: Alice posts encrypted message; Bob decrypts and reads; hub log shows no plaintext anywhere; tamper attempt is detected by AEAD
- **Output:** E2E encryption with hub-blind payload; documentation of the derivation steps

### Sprint F — Forward secrecy (ephemeral session keys)

- Each pair-session opens with an ephemeral X25519 exchange (in addition to the static-key ECDH)
- Session key derived via HKDF over (static ECDH || ephemeral ECDH || pair_id)
- Compromise of an LCT key after-the-fact does NOT decrypt prior sessions
- Smoke: simulate key compromise; verify prior session ciphertexts remain unreadable
- **Output:** forward secrecy without Signal-double-ratchet complexity (defer ratchet to a later sprint if/when needed)

### Sprint J — Channel-multiplex the hub MCP/REST tool endpoints

**Status:** *Member↔hub sealed channel SHIPPED.* The transport itself —
`POST /v1/hubs/{id}/channel`, with caller authentication via AEAD open, tier
resolution from the channel binding, `gate_read` PolicyEntity-on-reads, and
`ReadScope` tier bounding — is live (`dispatch_channel` in `rest.rs`). What
remains pending is only **multiplexing the legacy plaintext tool endpoints**
(`declare_skill` / `record_event`) over the channel; the channel-native tool
set already runs sealed.

**Motivation:** HUB's authz/confidentiality model (`hub-to-legion-authz-confidentiality-model-2026-06-09.md`, canonical home [`V2-V3-ARCHITECTURE.md` §8](V2-V3-ARCHITECTURE.md)) requires citizen-tier-and-above tool calls to travel over the sealed channel — *the channel IS the identity*. The remaining legacy plaintext tool endpoints authenticate by request payload, which is the bearer-token-style framing the model explicitly rejects; they are the ones still to migrate.

**Goal:** route the remaining state-mutating legacy tools through the sealed channel. The channel between the requestor's LCT and the hub's LCT is the wire over which the tool request travels, with the response sealed back over the same channel.

**Deliverables:**
- **Shipped:** Channel dispatch reads the request from the channel ciphertext (AEAD open), resolves tier from the counterparty LCT (no-LCT / external / citizen / sovereign), evaluates per PolicyEntity (`gate_read`) + bounds results by `ReadScope`, and seals the response back.
- **Shipped:** Tier resolution from channel binding (`dispatch_channel`): caller is `sovereign` / `citizen` (member) / external; external LCTs may only `request_citizenship`.
- **Pending:** Witnessing residue per smart-contract proposal §6.5 (hash of (request, response) committed to the ledger as the V3 attestation signal) for the multiplexed legacy tools.
- **Shipped:** The member↔hub `channel_request` path is the V1 transport — reuse, don't re-design.
- **Pending:** retiring the plaintext POST tool endpoints (`declare_skill` / `record_event`) at citizen-tier-and-above, refusing them with `capability_violation` witnessed once multiplexed.

**Tests:**
- Smoke: open channel as citizen, call `declare_skill` over the channel, verify ledger event + queryable state both update + response received over channel.
- Negative: citizen-tier HTTP POST without channel context is refused with `capability_violation` witnessed.
- Negative: response is NOT served over plaintext HTTP even if the request arrived over a valid channel (response stays on the channel).
- Conjunction: for every state-mutating tool, a smoke harness asserts ledger event AND queryable state update both happen (per proposal §6.3 adjacent observation; credits PR #292).

**Output:** §6.5 authz model is operational, not just documented. Hub satisfies "the channel IS the identity" in code.

**Depends on:** smart-contract proposal §6.5 settled (it is, in v0.3 — pointer-from-spec to V2-V3-ARCHITECTURE.md §8 is the corresponding spec edit).

---

### Sprint G — V3 trust accrual hooks

**Status:** reframed by smart-contract proposal §6.4. Gated on Sprint J + proposal §6.4 mapping settling.

**Reframe:** V3 doesn't accrue from "raw channel messages" — it accrues from **contract calls flowing over the channel**. Each call is an R6 action (per proposal §6.4); the witnessing residue (hash of request/response from Sprint J) is the input signal to the trust pipeline.

- On `PairingConfirmed` + per-call ledger events (kind: tool name, signal: witnessing residue from Sprint J), emit signals into the trust-update pipeline (web4-trust-core hooks).
- Per-pair contract-call count, lifetime, refusal-kind, capability-violation count feed into V3.validity updates.
- Per-tool weights (some tools confer more trust than others — `declare_skill` vs `record_event`) declared in chapter law.
- Read-only surface in admin UI showing trust deltas attributable to contract activity over the pair channel.
- **Output:** trust accrual loop is closed for contract activity over paired channels.

### Sprint H — ATP discharge per contract call

**Status:** reframed by smart-contract proposal §6.4. Gated on Sprint J + proposal §6.3 (mutability) + §6.4 (R6 composition) settling.

**Reframe:** ATP discharges per **contract call** (R6 action), not per raw byte/message. Per-tool ATP cost is declared in chapter law; the call is the discrete metering unit.

- Each tool call over a channel discharges ATP per the chapter's per-tool cost rule.
- Hub enforces ATP budget at call dispatch time (before tool execution begins).
- Per-tool ATP cost declared in chapter law; per-pair multipliers (trust-discounted rates) possible.
- Refused calls discharge a smaller "rejected-call" cost (so probing isn't free, but execution isn't required to charge).
- **Output:** paired-channel contract calls carry an economic signal; spam is naturally costly; high-trust pairs may receive discounted rates.

### Sprint I — Contract-call notification (formerly: webhook push)

**Status:** reframed by smart-contract proposal §6.1.2 (witness/notification semantics). Likely to defer until receiver-LCT framing clarifies.

**Reframe:** "Webhook push" was a transport-level idea. Under §6.1.2, a notification receiver is itself a queryable LCT exposing an MCP-callable surface (`notify`-style tool). The framing question moves from "hub POSTs to a URL" to "hub invokes a tool on the receiver's MCP server, over a (potentially newly-established) channel back."

- Receiver LCT exposes a `notify` (or equivalent) tool in its `interface_manifest` (per proposal §5.1).
- Hub calls the receiver's `notify` tool over a paired channel from hub-LCT → receiver-LCT, with the contract-call notification as payload.
- Polling stays as the fallback for receivers that don't expose a `notify` interface.
- **Output:** real-time notification for receivers that publish a `notify` interface; the bidirectional channel-as-contract-transport pattern composes.

**Open**: whether Sprint I in this form is worth doing pre-federation, or whether it should defer until cross-hub channel federation lands. May be subsumed.

### Out of scope for this PRD (later phases)

- Group pairs (>2 parties) — different design space; defer until 2-party model is proven
- Federation: pair where endpoints are in *different* hubs — needs hub-to-hub primitives first
- Double-ratchet for full Signal-equivalent forward + future secrecy
- Pair migration across LCT key rotations
- Anonymous pairs (no — anti-Web4)

---

## 7. Success criteria

The MVP (Sprints A through F) is done when:

1. Two LCT-holders on the same hub can establish a pair under chapter law, witnessed in the ledger.
2. Messages flow between them E2E-encrypted; the hub stores ciphertext + signed metadata only.
3. Forward secrecy: revealing an LCT key post-hoc doesn't decrypt past session messages.
4. `verify-ledger` covers pair lifecycle events unchanged.
5. Admin UI surfaces active pairs + per-pair message count + lifecycle events.
6. Chapter law can express per-pair policy (rate, TTL, who-may-pair-with-whom).
7. A smoke script exercises the full flow: request → confirm → encrypted message exchange → revoke → cannot send post-revoke.

Sprint J is the operational landing point for the smart-contract proposal's authz/confidentiality model — the next concrete commit candidate, post-MVP. Sprints G + H + I are the "make it load-bearing for V3 trust accrual + ATP + real-time delivery" follow-on phase, reframed by the smart-contract proposal and gated on Sprint J + the proposal's §6.3/§6.4 settling. Out-of-scope items are explicitly deferred.

---

## 8. Open design questions

1. **Per-pair shared-secret derivation: include `pair_id` or not?** Including it ensures two LCTs can have multiple distinct pairs without key reuse. Argument for: cleaner. Argument against: more state to track. Lean *for*.
2. **Message ordering guarantees.** Hub assigns monotonic per-pair sequence numbers? Or does endpoint-supplied timestamp + signer signature suffice? Lean toward hub-assigned seq numbers for the polling-with-`since` API to be simple.
3. **Message TTL.** Default-retain-forever for V1 simplicity. Operator-policy-driven prune later.
4. **Pair-state across daemon restart.** PairState rebuilds from ledger like everything else (free via existing projection machinery). Per-pair *session keys* are ephemeral — endpoints retain them across the pair lifetime; if an endpoint loses session keys, the pair must be re-confirmed (new session). Acceptable.
5. **Webhook reliability.** Sprint I — at-least-once or at-most-once? Probably at-least-once with idempotent recipients (clients dedupe on message id).
6. **Multi-device same-LCT.** An LCT held on two devices for one entity: do both devices receive paired messages? V1 assumption: one LCT, one logical endpoint; multi-device is later (and probably needs LCT split — separate sub-LCTs per device — which is its own architectural question).
7. **Cross-hub pairs (federation).** Out of scope here, but the design should not preclude — pair_id can be made globally unique; pair events can carry a `counterparty_hub_id` field that's `Self` in single-hub mode.

---

## 9. Implementation order + first concrete commit

**MVP (Sprints A-F):** shipped 2026-06-08.

**Sprint J — what already ships:** the member↔hub sealed channel (`POST /v1/hubs/{id}/channel`) is live, with the channel-native tool set (`query_hub`, `list_members`, `find_skill`, `find_members`, `request_intro`/`list_intros`/`respond_intro`, `notifications`, `referenced_act`, `constellation_challenge`/`present_constellation`, and `request_citizenship` for the external tier) running sealed under tier resolution + `gate_read` + `ReadScope`. The remaining work is narrow: multiplex the legacy plaintext tools (`declare_skill` / `record_event`) over the same channel and then refuse their plaintext POST at citizen-tier with `capability_violation` witnessed. Once one legacy tool works end-to-end on the channel, the others follow the same pattern.

Sprint J's smoke harness should also include the conjunction check from §6.3 of the smart-contract proposal — for every state-mutating tool, assert ledger event AND queryable state both update (PR #292's lesson made permanent).

**Then:** G/H/I in order, gated on proposal §6 settling.

---

## 10. Shipped reality (as built)

The sprint plan above is the design narrative; this section records what is
actually live in the code, beyond what the plan's framing alone conveys.

### 10.1 The member↔hub sealed channel is the realized transport

`POST /v1/hubs/{id}/channel` (`channel_request` → `dispatch_channel` in
`rest.rs`) is the working sealed transport for citizen-tier reads/acts. Sealing
uses **X25519 ECDH + ChaCha20-Poly1305** (the same primitives §4.1 specifies):
the sealed request authenticates the caller (AEAD open) *and* decrypts in one
step, and the response is sealed back over the same channel. Tier is resolved
from the channel binding (sovereign / citizen-member / external), reads pass
`gate_read` (PolicyEntity) and are bounded by `ReadScope` for the tier.

### 10.2 Consent intros — the bootstrap for direct member↔member pairs

`request_intro` / `list_intros` / `respond_intro` (channel tools) implement the
consent half of discovery. An intro is mutual-approval: when the target
accepts, **each party is handed the other's pinned pubkey** (`peer_lct` +
`peer_pubkey_hex`), which is exactly what a direct member↔member pair_channel
needs to derive its shared secret. Because both halves ride the sealed channel,
both parties hold pinned channel keys by the time an intro is accepted.

### 10.3 Semantic member discovery — `find_members`

`find_members` is live: the hub is the front door (gating + tier scoping), and
membot is the engine (the sidecar does embedding + 3-signal search). `top_k` is
bounded by the tier cap; member names are re-attached from the hub's
authoritative encrypted registry (PII lives once, in the hub, not the cart).

### 10.4 Notification poll-floor + referenced acts

`notifications` is the delivery floor: a citizen drains its pending sealed
notices from the per-LCT queue (push to a registered LCT-MCP endpoint is the
future optimization on the same queue). `referenced_act` lets a caller witness
a generic `web4_core::act::Act` addressed to a core `ActAddress`
(Peer/Citizen/Role/Society/FutureSelf), with a `content_hash` so the witnessed
record binds to a specific version and can't silently drift. Together they back
the hub→citizen push used when an intro is accepted (`notify:intro_accepted`).

### 10.5 Constellation attestation

`constellation_challenge` mints a nonce bound to the `pair_id`;
`present_constellation` verifies a `ConstellationAttestation` whose owner key is
checked against the caller's **pinned** resolver pubkey (no pinned key =
reject; never fall back to a self-carried key). The derived assurance tier binds
to the channel `pair_id` — the `assurance` hook `ReadScope` reserves. The member
side ships in hestia (`core/src/constellation.rs`); this is the verifier half.

### 10.6 The pair CLI

The `hub` binary ships client-side pair crypto so smoke scripts and operators
can drive the channel end-to-end:

- `hub pair-generate-ephemeral` — mint a per-session ephemeral X25519 keypair (Sprint F forward secrecy).
- `hub pair-encrypt` — seal a plaintext to a peer pubkey under a `pair_id` (X25519 ECDH + ChaCha20-Poly1305).
- `hub pair-decrypt` — the symmetric inverse; errors if AEAD fails.

---

## See also

- [`V2-V3-ARCHITECTURE.md`](V2-V3-ARCHITECTURE.md) §"Load-bearing architectural commitments" + §8 (canonical home for HUB's authz/confidentiality model — the interaction model Sprint J implements)
- [`PRD.md`](PRD.md) §"Solution shape" — hub overall
- [`STORAGE.md`](STORAGE.md) — backend the pair message log will live in
- [`BACKEND-OPTIONS.md`](BACKEND-OPTIONS.md) — note for DynamoDB: pair messages add a new SK prefix (`PAIR#<pair_id>#MSG#<seq>`)
- `web4-core/src/crypto/` — where Sprint A landed
- [`web4-standard/proposals/lct-mcp-as-smart-contract.md`](../../web4-standard/proposals/lct-mcp-as-smart-contract.md) — the proposal that reframed §0.1 + Sprints G/H/I + surfaced Sprint J
