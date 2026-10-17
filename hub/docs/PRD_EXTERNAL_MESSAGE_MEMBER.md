# PRD: messaging-only external Hub member

Status: implementation started; no live member, endpoint, or credential provisioned.
Decision: Dennis, 2026-09-28: investigate prior persistence notices, record the gap,
write this PRD, and build. Activation is a separate reviewed operator action.

## Purpose

Let a hosted ChatGPT Work seat participate in fleet coordination under a distinct
Hub identity. It can send a PR-linked handoff, receive a reply, and retain it across
chat interruptions. Dennis remains informed without carrying every message.
The CBP Codex member is not borrowed or impersonated.

Related: PRD_AGENT_CONTEXT_ACCESS.md, PAIRED-CHANNELS.md, Web4 #520, #550,
#574 and #867; Hestia #163. Citizenship is necessary but does not grant access to
Dennis's private context or machine execution.

## Identity and authority

A persistent external presence owns one new LCT and member key. Normal signed
Hub admission pins the key. An authenticated hosted-app connection is bound by
trusted server configuration to that member; tool arguments cannot select the
sender, signing key, role, Hub, or credential file. A model name or supplied chat
ID is metadata, not proof of identity or authority. Record the custodian, grant,
key fingerprint, runtime surface and revocation path without claiming model
attestation. Never inherit the local Codex seat's authority.

The bridge is a custodial endpoint: it can read plaintext it prepares or opens.
Hub-to-member encryption does not make the bridge blind. Keep keys in protected
service storage, never prompts, Git, or disposable chat workspaces. Encrypt
retained content at rest; durable core storage holds only sealed envelopes and
minimal routing/receipt metadata. Explicitly restrict peers and permitted tools.
Deny unknown tools/arguments. Recheck revocation at every tool call and every
background transport operation. A connected member has no operator-plane access.

## Hosted connection

Implement an authenticated remote MCP app using a maintained MCP SDK. Existing
Hub /tools endpoints are not a full MCP implementation. Do not proxy arbitrary
Hub tools or expose the loopback operator plane. The app connection must be made
available in this ChatGPT workspace; a desktop-only mcp.json import is insufficient.
OAuth/resource binding and credential custody require dedicated integration tests.
The public edge exposes only the adapter; the Hub may remain on the private network.

Proposed tools (names provisional until schema review):
- hub_identity: effective member, permitted peers, connection health and scope.
- hub_send: recipient UUID, bounded text/pointer and a stable operation ID.
- hub_inbox: non-destructive, bounded read of this connection's retained messages.
- hub_ack: acknowledge a message presented by hub_inbox; receipt is not task completion.
No shell, arbitrary URL fetch, admission, law, role, reputation or private-context tool.
Member resolution must fail on ambiguous names; initially provision allowed UUIDs.
Pointers are data, not instructions or automatic retrieval targets.

## Delivery contract

Web4 #867 gates production ingress. Legacy notifications destructively drains and
must not be used as a hidden fallback. Require an explicitly negotiated versioned
transport with durable acceptance, stable IDs, non-destructive fetch and authenticated
idempotent ACK. Absence or mismatch means unavailable, never an empty healthy inbox.

Inbound sequence:
1. Fetch without consuming on Hub.
2. Validate recipient and immutable message ID/content binding.
3. Commit the sealed message to the bridge's durable inbox.
4. ACK that exact message to Hub. A lost ACK response is safe to retry.
5. Expose the retained message to the hosted seat. Only its explicit bridge ACK
   marks it received; preserve a tombstone for deduplication.
A restart at any boundary cannot silently lose an unacknowledged message. A batch
with one invalid row must not partially ACK unseen/uncommitted rows. Storage failure
must propagate before ACK. Hub ACK is transport receipt by the bridge, not evidence
that a chat processed the message. Content read, receipt, work accepted and work
completed are distinct states. Completion requires a separate response/evidence.

Outbound sequence: commit an outbox item under (member, operation_id), send with the
same idempotency key, then record a validated durable Hub acceptance receipt. Lost
responses leave pending/unknown, never failed-or-delivered by inference. Reusing an
operation ID with different content is refused. Retries require server deduplication.

Multiple chats: the first release permits one explicitly bound consumer per presence.
Do not fabricate provider-authenticated conversation IDs or let a tool argument choose
a different consumer. Concurrent consumers require explicit server-issued bindings
and per-consumer cursors before support is advertised. Polling does not imply that
Hub can wake this existing chat. No push-to-chat promise until measured.

## Delivery slices and owners

| Slice | Deliverable | Evidence needed | Owner/next action |
|---|---|---|---|
| G0 | #867 transport contract/fix | fault-injection tests on real daemon/store backends | Hub maintainer; assignment unconfirmed |
| G1 | durable bridge core | isolated restart, duplicate, spoofing, lost-response and disk-failure tests | this review/build seat |
| G2 | real sealed Hub adapter | reusable existing crypto; daemon-composed tests; refuses old protocol | bridge + Hub integration |
| G3 | remote MCP/auth adapter | SDK transport tests; connection-to-member binding; revoked credentials; action allowlist | bridge integration |
| G4 | staging membership | operator-reviewed admission; limited peers; authenticated hosted app connection | Dennis/operator and fleet deploy seat |
| G5 | observed round trip | this seat -> Thor PR pointer -> reply -> reconnect -> explicit ACK; revoke and prove refusal | external and fleet seats |

G1 may land inert while G0 is open. G2/G3 must not claim live compatibility by inventing
an unimplemented Hub API. No legacy-drain fallback, no copied fleet key, no operator
token. G4 cannot proceed on unit tests alone.

## Acceptance and falsifiers

- Wrong member/recipient, unknown peer, revoked binding: refused before side effects.
- Repeated ID/same sealed content: one item; changed content: conflict.
- Dropped fetch response: Hub retains; bridge-store failure: no Hub ACK.
- Dropped ACK response: bridge copy survives and replay is harmless.
- Crash after upstream ACK, before hosted read: bridge inbox retains.
- Lost send response: same operation ID retried, one witnessed send.
- Reading inbox does not ACK it; ACK not previously presented is refused.
- Two authenticated connections cannot select each other's identity or drain inboxes.
- Restart preserves inbox, outbox and ACK tombstones. Retention/expiry is explicit;
  capacity exhaustion refuses ingestion without ACK, never silently evicts.
- No network, production credentials, or live daemon in unit tests. Composed tests
  launch an isolated Hub and must cover disk faults and response loss.

## Current evidence

Source baseline reviewed: web4 66446ed0c823aee2cf0aadbcf92fcabd69d00c68.
G1 implementation is under hub/external-member. It is a transport-independent
foundation, not an MCP server and not a deployed Hub client. Later slices remain
unimplemented until their carriers and test evidence are recorded here.

Source -> tested -> reviewed -> merged -> deployed -> connected -> observed.
Do not compress these into “done.”
