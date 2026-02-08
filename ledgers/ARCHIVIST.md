# Archivist Guide to Web4 Ledgers

This document provides guidance for long-term storage, retention policies, and recovery procedures for Web4 ledger data.

## Retention Policy by Chain Level

| Chain Level | Default Retention | Pruning | Archive Trigger |
|-------------|------------------|---------|-----------------|
| **Compost** | 1 hour | Automatic (ring buffer) | Never archived |
| **Leaf** | 24 hours | SNARC-based | High-value entries |
| **Stem** | 90 days | Value-based | Pattern consolidation |
| **Root** | Permanent | Never | Always archived |

### Compost Chains

**Retention**: Minutes to hours
**Storage**: Memory only (ring buffers)
**Archive**: Not archived - ephemeral by design

Compost data is working memory. Let it decompose naturally.

### Leaf Chains

**Retention**: Hours to days
**Storage**: SQLite or JSONL files
**Archive**: Entries with SNARC score ≥ 5 promoted to Stem

```python
# Archival trigger
if entry.snarc_score >= 5:
    create_witness_mark(entry)  # Promotes to Stem
    archive_entry(entry)        # Local archive
```

### Stem Chains

**Retention**: Days to months
**Storage**: PostgreSQL or distributed SQLite
**Archive**: Patterns with value score > threshold → Root chain

```python
# Value-based retention
if pattern.value_score > ARCHIVE_THRESHOLD:
    submit_to_root_chain(pattern)
elif pattern.last_access < now() - 90_days:
    archive_to_cold_storage(pattern)
```

### Root Chains

**Retention**: Permanent
**Storage**: Distributed consensus (ACT chain)
**Archive**: Cross-chain anchors for redundancy

```python
# Redundancy anchoring
anchor_to_solana(entry.merkle_root)
anchor_to_ethereum(entry.merkle_root)  # Optional, high cost
```

## Storage Formats

### JSONL (Leaf Chains)

```
{"entry_id":"leaf-42-1337","timestamp":"2026-02-08T14:00:00Z","content":{...},"prev_hash":"sha256:abc..."}
{"entry_id":"leaf-42-1338","timestamp":"2026-02-08T14:01:00Z","content":{...},"prev_hash":"sha256:def..."}
```

**Advantages**:
- Append-only (crash-safe)
- Line-oriented (easy streaming)
- Human-readable

**File rotation**: Daily files (`audit-2026-02-08.jsonl`)

### SQLite (Stem Chains)

```sql
CREATE TABLE entries (
    entry_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    content BLOB NOT NULL,  -- JSON or CBOR
    chain_level TEXT DEFAULT 'stem'
);

CREATE INDEX idx_timestamp ON entries(timestamp);
CREATE INDEX idx_prev_hash ON entries(prev_hash);
```

**Advantages**:
- Queryable
- ACID transactions
- Efficient for medium datasets

**WAL mode**: Enable for concurrent access

### CBOR (SAL Compliance)

For formal SAL (Society-Authority-Law) compliance:

```python
import cbor2

# CBOR encoding for official records
encoded = cbor2.dumps({
    'entry_id': 'root:lct:reg:alice',
    'content': {...},
    'signatures': [...]
})
```

## Integrity Verification

### Hash Chain Verification

```python
def verify_chain_integrity(entries: List[dict]) -> Tuple[bool, List[str]]:
    """Verify hash chain is unbroken."""
    errors = []

    for i in range(1, len(entries)):
        expected_prev = compute_hash(entries[i-1])
        actual_prev = entries[i]['prev_hash']

        if expected_prev != actual_prev:
            errors.append(f"Chain break at entry {entries[i]['entry_id']}")

    return len(errors) == 0, errors
```

### Witness Verification

```python
def verify_witnesses(entry: dict) -> bool:
    """Verify all witness signatures."""
    for witness in entry.get('witnesses', []):
        pub_key = get_public_key(witness['lct'])
        if not verify_signature(entry['content_hash'], witness['signature'], pub_key):
            return False
    return True
```

### Merkle Proof Verification

```python
def verify_merkle_proof(entry_hash: str, proof: List[str], root: str) -> bool:
    """Verify entry inclusion in Merkle tree."""
    current = entry_hash
    for sibling in proof:
        if current < sibling:
            current = sha256(current + sibling)
        else:
            current = sha256(sibling + current)
    return current == root
```

## Recovery Procedures

### From JSONL Backup

```python
def recover_from_jsonl(backup_path: str, target_db: str):
    """Rebuild database from JSONL backup."""
    db = sqlite3.connect(target_db)

    with open(backup_path) as f:
        for line in f:
            entry = json.loads(line)

            # Verify entry integrity
            if not verify_content_hash(entry):
                log_error(f"Corrupt entry: {entry['entry_id']}")
                continue

            db.execute(
                "INSERT OR REPLACE INTO entries VALUES (?, ?, ?, ?, ?)",
                (entry['entry_id'], entry['timestamp'], entry['prev_hash'],
                 entry['content_hash'], json.dumps(entry['content']))
            )

    db.commit()
    verify_chain_integrity(db)
```

### From Witness Marks

If local data is lost but witness marks exist on parent chain:

```python
def recover_from_witnesses(parent_chain: Chain, my_lct: str):
    """Recover from parent's witness marks."""
    marks = parent_chain.query_witness_marks(child_lct=my_lct)

    for mark in marks:
        # We have hash and summary, but not full content
        recovered_entry = {
            'entry_id': mark['entry_id'],
            'content_hash': mark['hash'],
            'summary': mark['summary'],
            'timestamp': mark['timestamp'],
            'recovered': True,
            'recovery_source': 'witness_mark'
        }
        save_partial_entry(recovered_entry)

    log_warning(f"Recovered {len(marks)} entries (summaries only)")
```

### From Cross-Chain Anchor

For root chain entries with external anchors:

```python
def verify_from_anchor(entry_id: str, external_chain: str):
    """Verify entry exists via cross-chain anchor."""
    anchor = get_anchor(entry_id, external_chain)

    if anchor:
        external_tx = query_external_chain(external_chain, anchor['external_tx'])
        if external_tx and external_tx['merkle_root'] == anchor['merkle_root']:
            return True, "Verified via external anchor"

    return False, "Anchor verification failed"
```

## Backup Schedule

| Chain Level | Backup Frequency | Retention | Offsite |
|-------------|------------------|-----------|---------|
| Leaf | Hourly | 7 days | No |
| Stem | Daily | 90 days | Yes |
| Root | Real-time (distributed) | Forever | Always |

### Automated Backup Script

```bash
#!/bin/bash
# /etc/cron.daily/web4-backup

# Leaf chains (local only)
for db in /var/lib/web4/leaf/*.db; do
    sqlite3 "$db" ".backup /backup/leaf/$(basename $db).$(date +%Y%m%d)"
done

# Stem chains (offsite)
pg_dump web4_stem | gzip > /backup/stem/stem-$(date +%Y%m%d).sql.gz
rsync -avz /backup/stem/ offsite:/backup/web4/stem/

# Root chain - handled by distributed consensus
```

## Compliance Export

For regulatory requirements:

```python
def export_compliance_report(
    chain: Chain,
    start_date: str,
    end_date: str,
    actor_filter: Optional[str] = None
) -> str:
    """Generate compliance report."""

    entries = chain.query(
        from_timestamp=start_date,
        to_timestamp=end_date,
        actor_lct=actor_filter
    )

    report = {
        'generated_at': datetime.now().isoformat(),
        'period': {'start': start_date, 'end': end_date},
        'total_entries': len(entries),
        'entries': entries,
        'chain_integrity': verify_chain_integrity(entries),
        'witness_coverage': calculate_witness_coverage(entries),
        'merkle_root': compute_merkle_root(entries)
    }

    return json.dumps(report, indent=2)
```

## Emergency Procedures

### Chain Fork Detection

```python
def detect_fork(local_chain: Chain, peer_chain: Chain) -> Optional[int]:
    """Detect if chains have forked."""
    local_hashes = local_chain.get_hash_sequence()
    peer_hashes = peer_chain.get_hash_sequence()

    for i, (local, peer) in enumerate(zip(local_hashes, peer_hashes)):
        if local != peer:
            return i  # Fork point

    return None
```

### Fork Resolution

1. **Identify fork point**
2. **Compare witness counts** - Higher witness coverage wins
3. **If tie, compare timestamps** - Earlier wins
4. **If still tie, compare ATP cost** - Higher investment wins
5. **Archive losing fork** - Never delete, mark as orphaned

## See Also

- [README.md](README.md) - Ledger overview
- [TERMINOLOGY.md](TERMINOLOGY.md) - Naming conventions
- [PUBLISHER.md](PUBLISHER.md) - API integration guide
- [spec/fractal-chains/](spec/fractal-chains/) - Chain specifications
