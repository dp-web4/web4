# Python Reference Implementations

Production-quality Python implementations of Web4 ledger systems.

## Files

| File | Lines | Purpose | Storage |
|------|-------|---------|---------|
| `enterprise_ledger.py` | ~730 | Enterprise governance ledger | SQLite |
| `heartbeat_ledger.py` | ~980 | Metabolic state-driven ledger | SQLite |
| `governance_audit.py` | ~450 | Immutable governance audit trail | SQLite |
| `witness_system.py` | ~600 | Multi-type witness attestations | JSON/SQLite |

## Quick Start

### Enterprise Ledger

```python
from enterprise_ledger import Ledger

# Initialize
ledger = Ledger("team_data.db")
ledger.initialize()

# Register identity
ledger.register_identity(
    lct_id="lct:web4:alice",
    name="Alice",
    initial_atp=1000
)

# Record audit entry
entry_id = ledger.record_audit(
    actor_lct="lct:web4:alice",
    action_type="tool_call",
    target="file:///src/main.py",
    result_hash="sha256:abc123...",
    atp_cost=10
)

# Verify chain integrity
valid, errors = ledger.verify_audit_chain()
```

### Heartbeat Ledger

```python
from heartbeat_ledger import HeartbeatLedger, MetabolicState

# Initialize with team configuration
ledger = HeartbeatLedger("team_heartbeat.db", team_id="team:eng")

# Submit transactions
ledger.submit_transaction({
    "type": "code_review",
    "actor": "lct:web4:alice",
    "target": "PR #123"
})

# Trigger heartbeat (seals pending transactions)
block = ledger.heartbeat()

# Transition metabolic state
ledger.transition_state(MetabolicState.REST)

# Verify chain
valid, errors = ledger.verify_chain()
```

### Governance Audit

```python
from governance_audit import GovernanceAuditTrail, AuditEventType

# Initialize
audit = GovernanceAuditTrail("governance.db")

# Record governance event
audit.record(
    event_type=AuditEventType.PROPOSAL_CREATED,
    actor_lct="lct:web4:alice",
    event_data={
        "proposal_id": "prop-001",
        "title": "Update team policy",
        "description": "..."
    }
)

# Query events
events = audit.query(
    event_type=AuditEventType.PROPOSAL_APPROVED,
    since="2026-01-01"
)

# Export for compliance
audit.export_compliance_report("audit_report.json")
```

### Witness System

```python
from witness_system import WitnessSystem, WitnessType

# Initialize
witness = WitnessSystem("witness_data.db")

# Create witness mark
mark = witness.create_mark(
    entry_id="leaf-42-1337",
    entry_hash="sha256:abc123...",
    summary={"type": "code_review", "outcome": "approved"}
)

# Witness (from another entity)
ack = witness.acknowledge(
    mark_id=mark.mark_id,
    witness_lct="lct:web4:bob",
    witness_type=WitnessType.ACTION,
    trust_delta=0.01
)

# Verify witness chain
results = witness.verify_chain(entry_id="leaf-42-1337")
```

## Provenance

These files are canonical copies from:

- `enterprise_ledger.py` ← `web4/simulations/ledger.py`
- `heartbeat_ledger.py` ← `web4/simulations/heartbeat_ledger.py`
- `governance_audit.py` ← `web4/simulations/governance_audit.py`
- `witness_system.py` ← `web4/web4-standard/implementation/reference/witness_system.py`

## Dependencies

```
Python >= 3.10
sqlite3 (stdlib)
hashlib (stdlib)
cryptography >= 40.0  # For Ed25519 signing
```

## See Also

- [../typescript/](../typescript/) - TypeScript implementations
- [../../spec/](../../spec/) - Formal specifications
- [../../act-chain/](../../act-chain/) - Distributed ledger (Cosmos SDK)
