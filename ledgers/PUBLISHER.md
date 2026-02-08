# Publisher Guide to Web4 Ledgers

This document provides API specifications, integration patterns, and webhook configuration for publishing and subscribing to Web4 ledger events.

## API Overview

Web4 ledgers expose a consistent REST API across all chain levels:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/append` | POST | Append entry to ledger |
| `/get/{hash}` | GET | Retrieve entry by content hash |
| `/query` | POST | Query entries with filters |
| `/prove` | POST | Get inclusion proof |
| `/events` | GET | Stream events (NDJSON) |
| `/health` | GET | Health check |

## REST API Specification

### Append Entry

```http
POST /append
Content-Type: application/json

{
  "content": {
    "type": "action_record",
    "actor_lct": "lct:web4:alice",
    "action": "tool_call",
    "target": "file:///src/main.py",
    "result_hash": "sha256:abc123..."
  },
  "signatures": [
    {
      "lct": "lct:web4:alice",
      "signature": "ed25519:xyz789..."
    }
  ]
}
```

**Response**:

```json
{
  "entry_id": "leaf-42-1337",
  "content_hash": "sha256:def456...",
  "prev_hash": "sha256:ghi789...",
  "timestamp": "2026-02-08T14:00:00.123Z",
  "status": "accepted"
}
```

### Get Entry

```http
GET /get/sha256:def456...
```

**Response**:

```json
{
  "entry_id": "leaf-42-1337",
  "timestamp": "2026-02-08T14:00:00.123Z",
  "prev_hash": "sha256:ghi789...",
  "content_hash": "sha256:def456...",
  "content": {
    "type": "action_record",
    "actor_lct": "lct:web4:alice",
    "action": "tool_call",
    "target": "file:///src/main.py"
  },
  "witnesses": [
    {"lct": "lct:web4:bob", "timestamp": "...", "signature": "..."}
  ]
}
```

### Query Entries

```http
POST /query
Content-Type: application/json

{
  "filters": {
    "actor_lct": "lct:web4:alice",
    "type": "action_record",
    "from_timestamp": "2026-02-01T00:00:00Z",
    "to_timestamp": "2026-02-08T23:59:59Z"
  },
  "limit": 100,
  "offset": 0,
  "order": "desc"
}
```

**Response**:

```json
{
  "total": 247,
  "returned": 100,
  "entries": [
    {"entry_id": "...", "content": {...}},
    ...
  ],
  "next_offset": 100
}
```

### Get Inclusion Proof

```http
POST /prove
Content-Type: application/json

{
  "entry_id": "leaf-42-1337"
}
```

**Response**:

```json
{
  "entry_id": "leaf-42-1337",
  "content_hash": "sha256:def456...",
  "merkle_proof": {
    "root": "sha256:root123...",
    "path": [
      "sha256:sibling1...",
      "sha256:sibling2...",
      "sha256:sibling3..."
    ],
    "position": 42
  },
  "witnesses": [
    {"lct": "lct:web4:bob", "ack_signature": "..."}
  ]
}
```

## Event Streaming

### NDJSON Stream

```http
GET /events?topics=sal.*&since=2026-02-08T00:00:00Z
Accept: application/x-ndjson
```

**Response** (streaming):

```json
{"event":"sal.birth","timestamp":"2026-02-08T14:00:00Z","data":{"lct":"lct:web4:alice"}}
{"event":"sal.role.bind","timestamp":"2026-02-08T14:01:00Z","data":{"lct":"lct:web4:alice","role":"developer"}}
{"event":"sal.audit.record","timestamp":"2026-02-08T14:02:00Z","data":{"entry_id":"leaf-42-1337"}}
```

### Event Topics

| Topic | Description |
|-------|-------------|
| `sal.birth` | Entity creation (LCT registration) |
| `sal.role.bind` | Role assignment |
| `sal.role.unbind` | Role removal |
| `sal.law.update` | Policy change |
| `sal.audit.record` | Audit entry created |
| `sal.audit.witness` | Witness acknowledgment |
| `sal.trust.update` | Trust tensor change |
| `sal.atp.discharge` | ATP spent |
| `sal.atp.recharge` | ATP earned |
| `sal.alert.*` | System alerts |

### Topic Filtering

Use glob patterns:
- `sal.*` - All SAL events
- `sal.audit.*` - All audit events
- `sal.trust.update` - Specific event

## Webhook Configuration

### Register Webhook

```http
POST /webhooks
Content-Type: application/json

{
  "url": "https://your-service.com/web4-events",
  "topics": ["sal.audit.*", "sal.trust.update"],
  "secret": "your-hmac-secret",
  "filters": {
    "actor_lct": "lct:web4:alice"
  }
}
```

**Response**:

```json
{
  "webhook_id": "wh-123456",
  "status": "active",
  "created_at": "2026-02-08T14:00:00Z"
}
```

### Webhook Payload

```http
POST https://your-service.com/web4-events
Content-Type: application/json
X-Web4-Signature: sha256=abc123...
X-Web4-Timestamp: 1707400800

{
  "webhook_id": "wh-123456",
  "event": "sal.audit.record",
  "timestamp": "2026-02-08T14:00:00Z",
  "data": {
    "entry_id": "leaf-42-1337",
    "actor_lct": "lct:web4:alice",
    "type": "action_record"
  }
}
```

### Signature Verification

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature."""
    expected = 'sha256=' + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## Integration Patterns

### Pattern 1: Real-Time Monitoring

```python
import requests

def monitor_events():
    """Stream events in real-time."""
    with requests.get(
        'https://ledger.web4.io/events',
        params={'topics': 'sal.*'},
        stream=True
    ) as response:
        for line in response.iter_lines():
            if line:
                event = json.loads(line)
                handle_event(event)
```

### Pattern 2: Batch Sync

```python
def batch_sync(last_sync: str):
    """Sync all events since last checkpoint."""
    response = requests.post(
        'https://ledger.web4.io/query',
        json={
            'filters': {'from_timestamp': last_sync},
            'limit': 1000
        }
    )

    for entry in response.json()['entries']:
        process_entry(entry)

    return response.json()['entries'][-1]['timestamp']
```

### Pattern 3: Audit Trail Export

```python
def export_audit_trail(actor_lct: str, period: tuple):
    """Export complete audit trail for actor."""
    start, end = period

    entries = []
    offset = 0

    while True:
        response = requests.post(
            'https://ledger.web4.io/query',
            json={
                'filters': {
                    'actor_lct': actor_lct,
                    'from_timestamp': start,
                    'to_timestamp': end
                },
                'limit': 1000,
                'offset': offset
            }
        )

        batch = response.json()['entries']
        entries.extend(batch)

        if len(batch) < 1000:
            break
        offset += 1000

    return entries
```

### Pattern 4: Witness Integration

```python
def witness_and_acknowledge(entry_id: str, witness_lct: str, private_key):
    """Witness an entry and submit acknowledgment."""
    # Get entry
    entry = requests.get(f'https://ledger.web4.io/get/{entry_id}').json()

    # Create witness mark
    mark = {
        'entry_id': entry_id,
        'content_hash': entry['content_hash'],
        'witness_lct': witness_lct,
        'timestamp': datetime.now().isoformat()
    }

    # Sign
    signature = sign_ed25519(json.dumps(mark, sort_keys=True), private_key)
    mark['signature'] = signature

    # Submit acknowledgment
    response = requests.post(
        'https://ledger.web4.io/witness',
        json=mark
    )

    return response.json()
```

## SDK Libraries

### Python

```python
from web4_ledger import LedgerClient

client = LedgerClient(
    url='https://ledger.web4.io',
    lct='lct:web4:alice',
    private_key=load_key('~/.web4/keys/alice.pem')
)

# Append entry
entry = client.append({
    'type': 'code_review',
    'target': 'PR #123',
    'outcome': 'approved'
})

# Query entries
entries = client.query(
    actor_lct='lct:web4:alice',
    since='2026-02-01'
)
```

### TypeScript

```typescript
import { LedgerClient } from '@web4/ledger';

const client = new LedgerClient({
  url: 'https://ledger.web4.io',
  lct: 'lct:web4:alice',
  privateKey: loadKey('~/.web4/keys/alice.pem')
});

// Append entry
const entry = await client.append({
  type: 'code_review',
  target: 'PR #123',
  outcome: 'approved'
});

// Subscribe to events
client.subscribe(['sal.audit.*'], (event) => {
  console.log('Event:', event);
});
```

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/append` | 100/min | Per LCT |
| `/query` | 1000/min | Per IP |
| `/events` | 10 concurrent | Per LCT |
| `/webhooks` | 10 registrations | Per LCT |

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 400 | Invalid request | Check payload format |
| 401 | Unauthorized | Verify signature |
| 403 | Forbidden | Check permissions |
| 409 | Conflict | Entry already exists |
| 429 | Rate limited | Back off and retry |
| 500 | Server error | Retry with backoff |

## See Also

- [README.md](README.md) - Ledger overview
- [ARCHIVIST.md](ARCHIVIST.md) - Storage and recovery
- [spec/api/ledger-openapi.yaml](spec/api/ledger-openapi.yaml) - OpenAPI specification
- [spec/witness-protocol/](spec/witness-protocol/) - Witnessing details
