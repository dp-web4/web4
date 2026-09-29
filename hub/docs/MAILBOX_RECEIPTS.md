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
| `notifications_enable_receipts` | `{}` | Persistently opt the caller into receipt delivery. Requires write freshness (`nonce`, `issued_at`). Idempotent. |
| `notifications_fetch` | `{"limit": 1..100}` (default 100) | Return `protocol`, `notifications: [{id, notice}]`, and `remaining`. Never consumes anything. Requires prior enrollment. |
| `notifications_ack` | `{"id": "<64 hex characters>"}` | Durably remove that caller's notice and retain its ACK tombstone. Requires write freshness. Returns `acknowledged: true, completed: false`. Repeated ACK returns the same result. |

The protocol identifier is `hub-mailbox-receive-v1`. Each returned `notice` uses
the existing sealed notice fields. Its ID hashes the recipient and committed
notice, including its timestamp, with domain separation. A sender's reusable
`pair_id` alone cannot acknowledge multiple queue entries.

A recipient must persist the entire returned sealed notice before ACK. ACK means
transport custody, never that an agent read, understood, or completed its contents.
Fetch-response loss, bridge failure before ACK, and ACK-response loss are safe to
retry. A local bridge still needs its own durable deduplication and application ACK.

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

This review slice retains at most 1,000 total pending notices plus ACK tombstones
per enrolled member. It never silently drops an unacknowledged notice for TTL or
capacity. Once full, enqueue refuses rather than erasing evidence. ACK transfers
a slot to a tombstone; it does not free one. **This is a bounded prototype, not a
long-running deployment contract.** Define and implement a bounded replay/retention
epoch and safe tombstone compaction before admitting a continuously active member.

The existing store interface scans mailbox rows; no new storage schema is needed.
A recipient-keyed read should replace that scan before scaling beyond staging.
Serialization assumes one daemon owns the store; it is not multi-writer database
coordination.

`send_secret` still witnesses before enqueue, with no persisted sender operation
key. Failure can leave a ledger act without a queued message; retry can duplicate
that act or an accepted message if its response was lost. It must not be used as
the G1 bridge's retry-safe send adapter. Remaining G0 work is a durable,
sender-bound idempotency key/content binding and receipt committed with mailbox
acceptance, plus composed lost-send-response tests. The bridge's strict transport
contract remains unchanged and refuses this partial protocol.

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
