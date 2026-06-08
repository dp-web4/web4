# Backend Options — Design Exploration

**Status:** Design / decision-framework doc, not a sprint plan. Operator
reference for currently-supported backends lives in [`STORAGE.md`](STORAGE.md);
this doc maps the wider space so we can accommodate a variety of hosting
choices as deployment patterns diverge.

**Audience:** Anyone deciding which backend to add next, or which to pick
for a specific hub deployment.

---

## Frame

A hub stores three kinds of state:

1. **State documents** — charter (immutable post-genesis), society
   (mutable current state), law (mutable YAML).
2. **Append-only signed event log** — the ledger. Hash-chained for
   integrity, signed per-entry for authenticity.
3. **Sidecar records** — V2-9 P2 council proposals (mutable
   open → committed/rejected/expired lifecycle).

All three sit behind the `HubStore` trait
([`hub-lib/src/store.rs`](../hub-lib/src/store.rs)). Backends are
swappable; data is portable. `hub migrate` moves an existing chapter
between any two implemented backends byte-for-byte (no re-signing).

### Hard constraints on any backend

These are derived from the existing architecture commitments
([V2-V3-ARCHITECTURE.md](V2-V3-ARCHITECTURE.md) §Load-bearing
commitments) and aren't negotiable:

- **Secrets-free** — `HubStore` never sees private keys. Vault concern.
- **Atomic ledger_append** — `prev_hash` chain integrity requires that
  two concurrent appenders cannot both succeed at the same `index`.
  Implementations need a primitive that gives this (filesystem locks
  for `file`, primary-key constraint for `sqlite`, conditional-write
  for DynamoDB, `SELECT … FOR UPDATE` for Postgres, etc.).
- **Byte-stable serialization** — entries are hashed in canonical
  JSON; the backend MUST round-trip bytes exactly, not "equivalent
  JSON." This is why we store `entry_json TEXT` in sqlite, not
  reconstructed-from-columns.
- **Migratable** — there must be a sensible mapping to/from the
  reference `file` layout. Backends that can't be exported back to
  file are sovereignty traps.

---

## Backend catalog

### `file` — local JSON / JSONL  ✅ shipped (MVP)

```
<chapter-dir>/{charter.json, society.json, ledger.jsonl, hub-law.yaml, proposals/}
```

| Property | Value |
|---|---|
| Operational profile | Solo operator, dev / R&D, edge devices |
| Locality | Wherever you put the directory |
| Multi-tenancy | One chapter per directory |
| Atomicity | Append via `O_APPEND`; state via temp-then-rename |
| Cost | Disk only |
| Lock-in | Zero. Plain files, inspectable with `cat` / `jq` |
| Sovereignty fit | ✅ Maximum — operator literally holds the bytes |
| Hardware-binding fit | ✅ Pairs cleanly with TPM-sealed dir / encrypted volume |

**Best for:** Single-machine hubs, R&D, chapters small enough for the full
ledger to live in RAM. The MVP default.

**Limits:** No concurrent multi-process writers (file lock would help but
isn't implemented). Linear ledger scan for queries. Backup = `tar`.

### `sqlite` — single-file embedded SQL  ✅ shipped (V2-2)

```
<chapter-dir>/chapter.db   # single SQLite file (+ WAL/SHM transient)
```

| Property | Value |
|---|---|
| Operational profile | Single machine, slightly larger / more queries |
| Locality | One file, anywhere |
| Multi-tenancy | One chapter per file |
| Atomicity | `INTEGER PRIMARY KEY` on `idx` enforces append-only at the index level; WAL mode for concurrent readers |
| Cost | Disk + bundled sqlite library |
| Lock-in | Low. Open with `sqlite3 chapter.db`, dump back to file backend |
| Sovereignty fit | ✅ Same as file — single artifact you own |
| Hardware-binding fit | ✅ Same as file |

**Best for:** Single-machine hubs that want one artifact to back up, faster
ledger queries (indexed by `idx`), or transactional state-doc writes.

**Limits:** One writer at a time (sqlite's design). Migrate to Postgres
if a single operator hosts many chapters and wants shared infrastructure.
Proposal storage not yet implemented for sqlite (file mode is sufficient
for current use; ~50 lines when needed).

### `postgres` — multi-chapter SQL  📋 planned (V2-15 B6)

Schema-per-chapter (default). One Postgres deployment hosting many
chapters. Same `HubStore` trait.

| Property | Value |
|---|---|
| Operational profile | One operator running multiple chapters at scale |
| Locality | Wherever your Postgres lives (typically operator's VPC) |
| Multi-tenancy | Schema-per-chapter; tens of thousands of chapters per cluster |
| Atomicity | Native transactions; `SERIALIZABLE` for chain integrity |
| Cost | Postgres license-free; pay for managed (RDS, Aurora, Crunchy, etc.) or self-host |
| Lock-in | Low. SQL is portable; pg_dump → restore anywhere |
| Sovereignty fit | ✅ if you run it; ⚠️ if managed (operator's cloud provider sees bytes) |
| Hardware-binding fit | ⚠️ Whole DB is one trust domain; per-chapter HSM gating is non-trivial |

**Best for:** AIC chapters (the namesake use case) where one operator runs
many hubs and wants shared ops + backup + monitoring. Federated
deployments where chapters share an operator but not sovereignty.

**Limits:** Async client (`tokio-postgres` / `sqlx`) — see [§Async trait](#open-design-question-async-trait)
below. Network round-trips on every op (acceptable for hubs serving
human-scale request rates).

### `dynamodb` — AWS managed NoSQL  💭 candidate

| Property | Value |
|---|---|
| Operational profile | AWS-native deployment, serverless / Lambda-fronted |
| Locality | AWS region of your choice; Global Tables for multi-region |
| Multi-tenancy | Single-table-design (PK=hub_id, SK=item_type#id) is idiomatic |
| Atomicity | `ConditionExpression: attribute_not_exists(idx)` for ledger append; `TransactWriteItems` for multi-doc commits (25-item limit) |
| Cost | Per-request: ~$1.25 per million writes, ~$0.25 per million reads on-demand. Storage ~$0.25/GB-mo. Free tier: 25GB + 200M req/mo. |
| Lock-in | High. AWS-specific. Export possible via DynamoDB Streams → S3 → batch convert to file format. |
| Sovereignty fit | ⚠️ AWS-hosted. Operator can encrypt at rest with KMS-CMK they own. Still: bytes live in AWS infrastructure. |
| Hardware-binding fit | ❌ Doesn't compose with TPM-on-operator's-machine; KMS HSM is the substitute (different trust model). |

**Best for:** Serverless / Lambda-fronted hubs. Operators who already
run AWS-native and don't want to manage stateful infra. Bursty workloads
where per-request pricing beats provisioned capacity.

**Limits:** No native JSON column type — items use Map attributes
(careful with the canonical-bytes constraint; we'd store `entry_json` as
a `B` (binary) attribute to preserve exact bytes, not as a Map). Item
size limit 400KB — fine for ledger entries (kilobytes each) but caps
proposal payloads if proposed_events ever embed large blobs.

**Open question on DynamoDB**: do we go single-table-design (one table,
PK=`hub_id`, SK=`charter` / `society` / `ledger#0000000042` /
`proposal#<uuid>`) or table-per-concern? Single-table is the AWS-best-
practice answer; we should match that idiom.

### `s3` (or any S3-compatible: R2, B2, GCS via interop) — object store  💭 candidate

| Property | Value |
|---|---|
| Operational profile | Archive tier; cold ledger pages; write-once audit blobs |
| Locality | Region of your choice; cross-region replication available |
| Multi-tenancy | Bucket-per-chapter OR prefix-per-chapter in a shared bucket |
| Atomicity | `If-None-Match: *` (S3 conditional PUT, GA 2024) gives the same primitive as DynamoDB's `attribute_not_exists`. R2/GCS have equivalents. |
| Cost | Storage cheap ($0.023/GB-mo S3 Standard, $0.015 R2). Per-request adds up at scale. |
| Lock-in | Low. S3 API is a de-facto standard (R2, B2, MinIO, GCS-via-interop). |
| Sovereignty fit | ⚠️ Same as DynamoDB — provider holds the bytes. Bring-your-own-key encryption helps. |
| Hardware-binding fit | ❌ Same constraint as DynamoDB. |

**Best for:** Append-only ledger as the source of truth, with state docs
projected to a faster store (Redis, DynamoDB, sqlite-replica). Archive
tier for old ledger pages where the live store is something else.
Distribution: anyone can fetch the public bucket and verify the chain.

**Limits:** No transactions across objects. Listing has eventual
consistency on some providers. State docs (charter, society, law)
work fine as overwritten objects; concurrent updates need an external
lock (DynamoDB lock table, fly.io lock service, etc.) — which makes
S3-alone insufficient for a live hub. Pair with another backend for
state.

### `cloudflare-d1` / `vercel-postgres` / `turso` / `neon` — managed serverless SQL  💭 candidate

Same shape as Postgres, deployed at edge or as a managed service.
Subset:

- **Cloudflare D1** — SQLite-at-the-edge, free tier generous, beta-grade
- **Turso** — libSQL (SQLite fork) with replication
- **Neon / Supabase / Vercel Postgres** — managed Postgres variants

| Property | Value |
|---|---|
| Operational profile | Hubs fronted by edge functions (Workers, Vercel) |
| Lock-in | Medium. SQL is portable but the managed surface varies |
| Sovereignty fit | ⚠️ Provider-hosted, same posture as DynamoDB |

**Best for:** Edge-deployed hubs where the daemon itself runs as Workers
/ serverless functions. Currently the hub is a long-running axum
process — using edge SQL would require a daemon refactor toward
request-scoped lifetime.

### Distributed consensus (`etcd`, `foundationdb`, `cockroachdb`)  💭 future

| Property | Value |
|---|---|
| Operational profile | Federation backbone (V2-11+); multiple hubs sharing a consensus layer |
| Atomicity | Raft / Paxos / similar — strong consistency by design |
| Cost | Higher op complexity; self-hosted typically |
| Sovereignty fit | ✅ if the federation self-hosts; the consensus group IS the sovereign |

**Best for:** Federated hub clusters where the consensus layer
represents the federation itself (not just a hosting choice). Not
needed for single-hub deployments. **Out of scope for V2**; mentioning
to flag the shape for when federation lands.

---

## Decision guidance by operator profile

| Profile | Recommended | Why |
|---|---|---|
| **Solo dev / R&D / a few members** | `file` | Inspectable, zero ops |
| **Single chapter, modest scale, single machine** | `sqlite` | One artifact, fast queries |
| **One operator, many chapters, on a VPS** | `postgres` (when shipped) | Shared backup + monitoring; chapter isolation via schemas |
| **AWS-native operator, serverless front-end** | `dynamodb` (when shipped) | No stateful infra to run; scales with traffic |
| **Archive / cold storage of old pages** | `s3` (pair with another for live state) | Cheapest storage; immutable by convention |
| **Edge-deployed hub (Workers, Vercel)** | D1 / Turso / managed Postgres | Matches the daemon's lifetime model |
| **Federation backbone** | etcd / FDB / Cockroach | Consensus IS the federation |

The "right" answer is almost always the simplest backend that fits the
operator's actual operational comfort + sovereignty posture.

---

## Migration paths

`hub migrate` already handles `file ↔ sqlite` end-to-end. Same shape
extends to any pair:

```
hub migrate <chapter-dir> --to <kind> [--from-uri ...] [--to-uri ...]
```

Open question: backends with off-machine state (Postgres, DynamoDB,
S3) need a URI for source / target rather than `<chapter-dir>`. The
CLI needs to grow `--from-uri` / `--to-uri` flags, and the migration
tool needs a `BackendUri` shape distinct from `BackendKind`.

The migration contract is invariant across backends: charter copied,
society copied, ledger entries copied byte-for-byte, `head_hash`
matches end-to-end, source artifacts preserved for rollback. Any new
backend that can't meet this contract isn't a `HubStore` — it's a
read-only projection (which is fine, just a different abstraction).

---

## Open design question: async trait

The `HubStore` trait is currently synchronous. Network-backed
backends (Postgres, DynamoDB, S3) MUST do I/O on the tokio runtime
to participate in the axum daemon's async model.

Three options to resolve:

### A. Wrap calls in `spawn_blocking` (status quo)

What I did for V2-9 P2 proposal storage — handler spawns a blocking
task that opens the store + runs the sync operation. Works today,
zero trait changes, but:

- Sequentializes I/O behind the rayon-blocking-pool worker count
- Hidden cost (the blocking pool defaults are tuned for occasional
  blocking, not "every request")
- Forces store re-open on every request (no connection pooling)

### B. `#[async_trait]` on `HubStore`

Convert to async-first. Sync backends (`file`, `sqlite`) implement
the async signature with `async fn` that just runs synchronously —
no `spawn_blocking` needed because the work is in-process and fast.
Network backends do real awaits.

Cost: every call site needs `.await`. Boxing overhead per call
(`async_trait` allocates a `Box<dyn Future>`).

### C. Split into `HubStore` (sync) + `HubStoreAsync` (async) traits

Two traits, two impl families. Higher-layer code uses one or the
other. Migration boundary is the daemon: pick async if any backend
is network-backed.

Cost: trait duplication; converters between the two; tests doubled.

### Recommendation

**B (`#[async_trait]`).** Pay the boxing cost once, get a uniform
abstraction, and the daemon-internal call sites already await
elsewhere (envelope verify, signer roundtrip, etc.) so adding
`.await` to store calls is consistent.

This is a one-sprint refactor that should land **before** the first
network-backed backend, not as part of it. Otherwise we pay the
`spawn_blocking` tax permanently on `file`/`sqlite` and end up with
async only on the new backend (inconsistent).

---

## Web4 sovereignty considerations

Backends differ on a property the spec cares about: **who can read
the bytes without the operator's involvement?**

| Backend | Bytes-readable-by |
|---|---|
| `file` (on operator's disk) | Just the operator |
| `sqlite` (same disk) | Just the operator |
| `postgres` (self-hosted) | Operator + anyone with DB access |
| `postgres` (RDS / Aurora) | + AWS, by way of platform access |
| `dynamodb` | + AWS, same |
| `s3` (any cloud) | + provider |
| `cloudflare-d1` / `vercel-postgres` | + provider |

For the chapter state itself, this matters less than it sounds —
it's all signed and not encrypted by design (the data is public to
chapter members + auditors; the integrity guarantee comes from
signatures, not from confidentiality).

For an emerging Hestia-mode hub where Hestia holds the keys and the
hub holds the data: a cloud-hosted hub is *fine*, because the cloud
provider sees signed-but-public state, not secrets. The vault stays
on the operator's hardware.

The argument for `file` / `sqlite` over cloud-hosted backends is
operational, not constitutional:

- Latency: local I/O beats network round-trip for state-doc reads
- Cost: at small scale, free disk beats per-request pricing
- Failure modes: a local backend can't be "API rate-limited" or
  "region-evacuated"
- Vendor leverage: no platform-policy risk

For hubs that want or need the cloud-native operational model
(serverless, multi-region, auto-scaling), the cloud backends are
appropriate. The trust model doesn't degrade — the operator just
moves the bytes to a different physical location.

---

## What this doc deliberately doesn't decide

- Which backend to implement next. That's a sprint decision driven
  by who wants to deploy what.
- The naming / URI scheme for off-machine backends.
  (`postgres://...` vs `dynamo://region/table` vs config-file blocks
  — needs its own RFC-style note.)
- Per-backend tuning (Postgres pool size, DynamoDB capacity mode,
  etc.) — those are operator config concerns.

---

## See also

- [`STORAGE.md`](STORAGE.md) — operator reference for currently-shipping
  backends + migration tool
- [`V2-V3-ARCHITECTURE.md`](V2-V3-ARCHITECTURE.md) — §Load-bearing
  commitments #8 (secrets posture) and #5 (multi-Sovereign Council)
- [`hub-lib/src/store.rs`](../hub-lib/src/store.rs) — the `HubStore` trait
- [`hub-lib/src/ledger.rs`](../hub-lib/src/ledger.rs) — how the trait
  is used for chain integrity
