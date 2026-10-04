# Mailbox receipts: first Hub-side persistence repair

Status: implemented for review; no live member enrollment or deployment. Part of
[#867](https://github.com/dp-web4/web4/issues/867), following the
[external-member PRD](PRD_EXTERNAL_MESSAGE_MEMBER.md). This is the receiving half
of G0, **not** the bridge's proposed `hub-mailbox-receipt-v2` contract.

## Wire surface

Use the existing authenticated, sealed member channel. All three tools derive the
recipient from its verified caller identity; an `args.recipient` cannot redirect
an operation. Existing membership, pinned-key and law checks apply.

| Tool | Arguments | Effect |
|---|---|---|
| `notifications_enable_receipts` | `{}` | **Refused (403)** with a pointer to the operator route below. Enrollment is not self-service. |
| `notifications_fetch` | `{"limit": 1..100}` (default 100) | Return `protocol`, `notifications: [{id, notice}]`, and `remaining`. Never consumes anything. Requires prior enrollment. |
| `notifications_ack` | `{"id": "<64 hex characters>"}` | Durably remove that caller's notice and keep an ACK tombstone for 7 days (at most 4,096), so a retried ACK returns the same result. The ACK frees the notice's slot. Requires write freshness. Returns `acknowledged: true, completed: false`. |

**Enrollment is an operator act** (hub-claude review of #869). It is one-way: there is no downgrade,
and older binaries cannot read the record. It also changes that member's delivery from
consume-on-poll to fetch/ACK, and a member whose client does not ACK stops receiving once it holds
1,000 unacknowledged notices. A door that cannot be closed again is admission-shaped, so it lives
on the loopback operator plane:

    POST /admin/api/members/<lct_id>/mailbox-receipts   {"reason": "<required>"}

It requires a known member, a reason and a durable store. The Sovereign witnesses a
`mailbox:receipts_enabled` act (to the member; its substance hashes `{protocol, member, reason}`)
**before** the write. If the write then fails, the error says the ledger records an enrollment that
did not happen, and the same call retries it. Re-calling on an enrolled member returns
`already: true` and writes no second act.

The protocol identifier is `hub-mailbox-receive-v1`. Each returned `notice` uses
the existing sealed notice fields. Its ID hashes the recipient and committed
notice, including its timestamp, with domain separation. A sender's reusable
`pair_id` alone cannot acknowledge multiple queue entries.

A recipient must persist the entire returned sealed notice before ACK. ACK means
transport custody, never that an agent read, understood, or completed its contents.
Fetch-response loss, bridge failure before ACK, and ACK-response loss are safe to
retry. A local bridge still needs its own durable deduplication and application ACK.

## Router forwarding: receipt mode is mandatory

The F3 router hop uses the same sender-operation machinery under a dedicated
\`route_forward\` channel tool. This is deliberately not ordinary \`referenced_act\` delivery:
an intermediate router must be able to retry a lost response without creating a second packet
or a second hop witness.

Arguments:

\`\`\`json
{
  "to": "<next-hop Hub member UUID>",
  "operation_id": "<stable 1..128-byte retry key>",
  "route_packet_json": "<exact UTF-8 JSON object>"
}
\`\`\`

The route packet protocol is \`web4-route-v1\`. V1 requires \`packet_id\`,
\`destination_lct\`, \`origin_lct\`, \`original_kind\`, \`pointer_uri\`,
\`content_hash\`, \`hops_remaining\`, and \`visited_routers\`.

The **next hop must already be enrolled in receipt delivery**. A legacy
consume-on-poll mailbox is refused with 409; routing must not re-introduce the
fetch-response-loss boundary receipt mode was created to remove.

The Hub hashes the **exact \`route_packet_json\` bytes**, witnesses that hash in a
\`route.forward\` Act, seals the same packet bytes to the next hop's pinned member
key, and commits notice + sender operation atomically before landing the act. The
final destination remains inside the packet; \`to\` is only the next-hop transport
address.

A retry with the same \`operation_id\` and byte-identical packet returns the first
receipt. Reusing the id for a different packet or next hop is 409.

## Sending: the order that keeps the record honest (#867 contract 1)

`send_secret` now runs in this order:
1. **An existing `operation_id` answers with its first outcome.** Nothing new is queued or witnessed.
2. **Authorize the act.** The law gate runs and the Sovereign signs. This has **no side effect**.
3. **Queue the notice durably.** When an `operation_id` is given, its record is written in the
   **same transaction**.
4. **Land the pre-signed act.** If the ledger moved since signing, it is re-authorized, at most
   three attempts. If the act cannot land, the notice (and op record) is **withdrawn** while it is
   still queued. The error then says "not sent … withdrawn". If it was already drained or ACKed,
   the error says it may have been delivered, and a retry with the same `operation_id` completes
   the record.

So a refused send leaves the ledger untouched, and the ledger never asserts a send the mailbox
refused.

**`operation_id`** is optional: 1–128 characters of `[A-Za-z0-9._:-]`, and it needs a durable
backend (otherwise 501).
- **Same id, same message.** A retry within **7 days** returns the first attempt's
  `entry_index` and `notice_id` with `replayed: true`: one notice, one act. The message is the
  recipient, pointer, `content_hash` and sealed-body hash.
- **Same id, different message:** 409, and nothing is sent.
- **Retry after a crash between steps 3 and 4.** The act's id is derived from (sender,
  `operation_id`). The retry **finds** the act on the ledger if it landed, or witnesses it
  **once** if it did not.
- **After the 7-day window**, the same id is a new send.
- **Without an `operation_id`**, the order above still holds, but nothing is deduplicated; the
  legacy behaviour is kept.

Response: `delivered`, `durably_accepted`, `entry_index`, `notice_id`, `operation_id`,
`replayed`.

## Refusals are not server faults

| Status | Meaning | Retry? |
|---|---|---|
| 400 | `limit` outside 1..=100, or an `id` that is not 64 hex characters | no, fix the request |
| 403 | `notifications_enable_receipts` on the member channel | no, ask the operator |
| 404 | ACK for an id not in this member's mailbox, or ACKed more than 7 days ago | no; fetch again (IDs re-key if `SealedNotice` gains a field) |
| 409 | fetch/ACK before enrollment; legacy `notifications` after enrollment | no |
| 501 | the backend has no durable mailbox (receipt mode unavailable) | no |
| 409 | `operation_id` reused for a different message | no, use a new id |
| 507 | `send_secret` to a receipt mailbox holding the maximum unacknowledged notices | yes, after the recipient ACKs |
| 500 | the store could not be read or written; nothing changed | yes |

## Persistence and compatibility

Enqueue, ACK and legacy drain serialize their complete read/modify/commit under
one daemon mutex. A durable backend is authoritative even before RAM hydration;
failed/corrupt reads are errors, not empty queues. Failed writes leave RAM alone.
`send_secret` propagates persistence errors instead of returning `delivered:true`.
Its success adds `durably_accepted`, false on the legacy non-durable File backend.
The historical `delivered` field remains queue acceptance, not recipient receipt.

Old array-format mailbox blobs remain readable. Explicit enrollment writes the
new object format, retains the queue, and persists even for an empty mailbox.
`notifications` refuses to drain an enrolled mailbox, including after restart.
There is no automatic enrollment and no downgrade operation. **Do not downgrade
the daemon to an older binary after enrollment:** it cannot understand the new
format. Take a store backup before any later authorized staging enrollment.

Receipt mode requires a backend advertising durable mailbox storage (currently
SQLite/SQLCipher). It does not silently fall back to FileBackend or legacy drain.
Existing unenrolled clients retain their legacy cap/TTL and destructive-poll
behavior. Hub-generated notifications remain explicitly best effort; their
witnessed ledger event is not a receipt for successful mailbox delivery.

## Deliberate bounds and remaining work

**Retention (#867 item 5).** An enrolled mailbox holds at most **1,000 unacknowledged notices**. It
never drops one for TTL or capacity: once full, a send is refused (507) until the recipient ACKs, and
an ACK frees its slot.

ACK tombstones are bounded apart from that, at **7 days** and at most **4,096**, and are pruned on
every ACK. They exist only so a retried ACK answers "acknowledged". They are not what stops a notice
coming back: a notice ID hashes its committed timestamp, so an ACKed notice cannot recur. An ACK for
an ID pruned from the window answers 404 with that reason.

Sender operations are kept for **7 days** and pruned in the same transaction as each new one. The
per-sender count inside that window is bounded only by the channel's rate limits.

Each operation reads its own recipient's row (`HubStore::mailbox_get`: a keyed `SELECT` on
SQLite, and the scan, filtered, as the default for other backends). No new storage schema is
needed, and another member's unreadable row does not fail this one's operations.
Serialization assumes one daemon owns the store; it is not multi-writer database
coordination.

`send_secret` is retry-safe with an `operation_id` (see *Sending* above). That completes the Hub
side of #867's contract; the bridge-side consumer dedup (item 4) is the G1 bridge's own.

Not the same thing as the bridge's proposed `hub-mailbox-receipt-v2`. Whether this protocol meets
that contract, including where the atomic acceptance receipt is observable, is the bridge's review
to make.

Then build the real sealed transport adapter and authenticated remote MCP
adapter, review custody/admission, and measure the external-to-fleet round trip.
Nothing in this change admits a member, installs keys, deploys a daemon or proves
live delivery.

## Verification

The daemon tests use disposable real SQLite stores and the actual sealed channel
handler. Fault injection uses a SQLite trigger rejecting mailbox writes. Cases
cover store failure through `send_secret`, enqueue/ACK/enrollment failure, lost
fetch and ACK responses across restart, legacy-blob upgrade, legacy-drain refusal,
cross-recipient ACK attempts, write freshness, concurrent ACK/enqueue, corrupt
storage, non-durable refusal and retention backpressure. Existing CI runs the
entire Hub Rust workspace with `cargo test --locked`.
