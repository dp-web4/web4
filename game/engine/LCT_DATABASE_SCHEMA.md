# LCT Database Schema Proposal
**Session #71 Priority 3**: Database integration for LCT objects

## Overview

This document proposes a database schema for persisting LCT (Linked Context Token) objects with full T3/V3/MRH metadata. This extends the existing `lct_identities` table with complete LCT state tracking.

## Current State

**Existing** (from Session #66):
```sql
lct_identities (
    lct_id TEXT PRIMARY KEY,
    entity_type TEXT,
    birth_certificate_hash TEXT,
    public_key TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)
```

**Gap**: No storage for T3 trust, V3 value, MRH profiles, blockchain provenance, or lifecycle state.

## Proposed Schema

### Core LCT Table

```sql
CREATE TABLE lcts (
    -- Core identity
    lct_id TEXT PRIMARY KEY,
    lct_type TEXT NOT NULL,  -- 'agent' | 'society' | 'role' | 'resource' | 'event'

    -- Blockchain provenance
    owning_society_lct TEXT NOT NULL,
    created_at_block INTEGER NOT NULL,
    created_at_tick INTEGER NOT NULL,

    -- T3 trust tensor (role-contextual)
    t3_talent REAL DEFAULT 0.5,
    t3_training REAL DEFAULT 0.5,
    t3_temperament REAL DEFAULT 0.5,
    t3_composite REAL DEFAULT 0.5,

    -- V3 value tensor
    v3_valuation REAL DEFAULT 0.5,
    v3_veracity REAL DEFAULT 0.5,
    v3_validity REAL DEFAULT 0.5,
    v3_composite REAL DEFAULT 0.5,

    -- MRH profile
    mrh_delta_r TEXT DEFAULT 'local',      -- spatial scope
    mrh_delta_t TEXT DEFAULT 'session',    -- temporal scope
    mrh_delta_c TEXT DEFAULT 'agent-scale', -- complexity

    -- Type-specific metadata (JSONB)
    metadata JSONB DEFAULT '{}',

    -- Lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    deactivated_at_tick INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CHECK (t3_talent BETWEEN 0.0 AND 1.0),
    CHECK (t3_training BETWEEN 0.0 AND 1.0),
    CHECK (t3_temperament BETWEEN 0.0 AND 1.0),
    CHECK (v3_veracity BETWEEN 0.0 AND 1.0),
    CHECK (v3_validity BETWEEN 0.0 AND 1.0),
    CHECK (mrh_delta_r IN ('local', 'regional', 'global')),
    CHECK (mrh_delta_t IN ('ephemeral', 'session', 'day', 'epoch')),
    CHECK (mrh_delta_c IN ('simple', 'agent-scale', 'society-scale'))
);

-- Indexes for common queries
CREATE INDEX idx_lcts_type ON lcts(lct_type);
CREATE INDEX idx_lcts_owning_society ON lcts(owning_society_lct);
CREATE INDEX idx_lcts_active ON lcts(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_lcts_t3_composite ON lcts(t3_composite);
CREATE INDEX idx_lcts_v3_composite ON lcts(v3_composite);
CREATE INDEX idx_lcts_metadata ON lcts USING GIN (metadata);
```

### T3/V3 Evolution History

Track changes to trust and value over time:

```sql
CREATE TABLE lct_tensor_history (
    id SERIAL PRIMARY KEY,
    lct_id TEXT NOT NULL REFERENCES lcts(lct_id),
    world_tick INTEGER NOT NULL,
    tensor_type TEXT NOT NULL,  -- 'T3' | 'V3'

    -- T3 changes
    t3_talent_delta REAL,
    t3_training_delta REAL,
    t3_temperament_delta REAL,

    -- V3 changes
    v3_valuation_delta REAL,
    v3_veracity_delta REAL,
    v3_validity_delta REAL,

    -- Context
    reason TEXT,
    action_ref TEXT,  -- Reference to R6 action
    evidence JSONB,

    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tensor_history_lct ON lct_tensor_history(lct_id);
CREATE INDEX idx_tensor_history_tick ON lct_tensor_history(world_tick);
CREATE INDEX idx_tensor_history_type ON lct_tensor_history(tensor_type);
```

### LCT Context Edges (MRH Graph)

RDF-like triples linking LCTs:

```sql
CREATE TABLE lct_context_edges (
    id SERIAL PRIMARY KEY,
    subject_lct TEXT NOT NULL REFERENCES lcts(lct_id),
    predicate TEXT NOT NULL,  -- e.g., 'web4:hasRole', 'web4:memberOf'
    object_lct TEXT NOT NULL REFERENCES lcts(lct_id),

    -- MRH profile for this edge
    mrh_delta_r TEXT DEFAULT 'local',
    mrh_delta_t TEXT DEFAULT 'session',
    mrh_delta_c TEXT DEFAULT 'agent-scale',

    -- Lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    created_at_tick INTEGER NOT NULL,
    deactivated_at_tick INTEGER,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_context_edges_subject ON lct_context_edges(subject_lct);
CREATE INDEX idx_context_edges_object ON lct_context_edges(object_lct);
CREATE INDEX idx_context_edges_predicate ON lct_context_edges(predicate);
CREATE INDEX idx_context_edges_active ON lct_context_edges(is_active) WHERE is_active = TRUE;
```

## Sync API

### Python Functions

```python
def sync_lct_to_db(self, lct: LCT) -> bool:
    """
    Sync LCT object to database

    Args:
        lct: LCT object from engine/lct.py

    Returns:
        True if sync successful
    """
    cursor = self.conn.cursor()

    try:
        t3 = lct.trust_axes.get("T3", {})
        v3 = lct.value_axes.get("V3", {})

        cursor.execute("""
            INSERT INTO lcts (
                lct_id, lct_type, owning_society_lct,
                created_at_block, created_at_tick,
                t3_talent, t3_training, t3_temperament, t3_composite,
                v3_valuation, v3_veracity, v3_validity, v3_composite,
                mrh_delta_r, mrh_delta_t, mrh_delta_c,
                metadata, is_active, deactivated_at_tick
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
            ON CONFLICT (lct_id) DO UPDATE SET
                t3_talent = EXCLUDED.t3_talent,
                t3_training = EXCLUDED.t3_training,
                t3_temperament = EXCLUDED.t3_temperament,
                t3_composite = EXCLUDED.t3_composite,
                v3_valuation = EXCLUDED.v3_valuation,
                v3_veracity = EXCLUDED.v3_veracity,
                v3_validity = EXCLUDED.v3_validity,
                v3_composite = EXCLUDED.v3_composite,
                metadata = EXCLUDED.metadata,
                is_active = EXCLUDED.is_active,
                deactivated_at_tick = EXCLUDED.deactivated_at_tick,
                updated_at = NOW()
        """, (
            lct.lct_id, lct.lct_type, lct.owning_society_lct,
            lct.created_at_block, lct.created_at_tick,
            t3.get("talent", 0.5), t3.get("training", 0.5),
            t3.get("temperament", 0.5), t3.get("composite", 0.5),
            v3.get("valuation", 0.5), v3.get("veracity", 0.5),
            v3.get("validity", 0.5), v3.get("composite", 0.5),
            lct.mrh_profile.get("deltaR", "local"),
            lct.mrh_profile.get("deltaT", "session"),
            lct.mrh_profile.get("deltaC", "agent-scale"),
            json.dumps(lct.metadata),
            lct.is_active,
            lct.deactivated_at_tick
        ))

        self.conn.commit()
        cursor.close()
        return True

    except Exception as e:
        print(f"Error syncing LCT {lct.lct_id}: {e}")
        self.conn.rollback()
        cursor.close()
        return False


def load_lct_from_db(self, lct_id: str) -> Optional[LCT]:
    """
    Load LCT object from database

    Args:
        lct_id: LCT identifier

    Returns:
        LCT object or None if not found
    """
    cursor = self.conn.cursor()

    cursor.execute("""
        SELECT * FROM lcts WHERE lct_id = %s
    """, (lct_id,))

    row = cursor.fetchone()
    cursor.close()

    if not row:
        return None

    return LCT(
        lct_id=row['lct_id'],
        lct_type=row['lct_type'],
        owning_society_lct=row['owning_society_lct'],
        created_at_block=row['created_at_block'],
        created_at_tick=row['created_at_tick'],
        trust_axes={
            "T3": {
                "talent": row['t3_talent'],
                "training": row['t3_training'],
                "temperament": row['t3_temperament'],
                "composite": row['t3_composite']
            }
        },
        value_axes={
            "V3": {
                "valuation": row['v3_valuation'],
                "veracity": row['v3_veracity'],
                "validity": row['v3_validity'],
                "composite": row['v3_composite']
            }
        },
        mrh_profile={
            "deltaR": row['mrh_delta_r'],
            "deltaT": row['mrh_delta_t'],
            "deltaC": row['mrh_delta_c']
        },
        metadata=row['metadata'],
        is_active=row['is_active'],
        deactivated_at_tick=row['deactivated_at_tick']
    )


def record_tensor_evolution(self, lct_id: str, tick: int,
                            tensor_type: str, deltas: Dict[str, float],
                            reason: str, evidence: Optional[Dict] = None) -> None:
    """
    Record T3/V3 evolution event

    Args:
        lct_id: LCT identifier
        tick: World tick
        tensor_type: 'T3' or 'V3'
        deltas: Changes to axes
        reason: Why the change occurred
        evidence: Supporting data
    """
    cursor = self.conn.cursor()

    cursor.execute("""
        INSERT INTO lct_tensor_history (
            lct_id, world_tick, tensor_type,
            t3_talent_delta, t3_training_delta, t3_temperament_delta,
            v3_valuation_delta, v3_veracity_delta, v3_validity_delta,
            reason, evidence
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s
        )
    """, (
        lct_id, tick, tensor_type,
        deltas.get("talent") if tensor_type == "T3" else None,
        deltas.get("training") if tensor_type == "T3" else None,
        deltas.get("temperament") if tensor_type == "T3" else None,
        deltas.get("valuation") if tensor_type == "V3" else None,
        deltas.get("veracity") if tensor_type == "V3" else None,
        deltas.get("validity") if tensor_type == "V3" else None,
        reason,
        json.dumps(evidence) if evidence else None
    ))

    self.conn.commit()
    cursor.close()
```

## Queries

### Common Queries

```sql
-- Find all agents with high T3 trust
SELECT lct_id, t3_composite
FROM lcts
WHERE lct_type = 'agent' AND t3_composite > 0.8 AND is_active = TRUE
ORDER BY t3_composite DESC;

-- Find all LCTs owned by a society
SELECT * FROM lcts WHERE owning_society_lct = 'lct:web4:society:test';

-- Get T3 evolution for an agent
SELECT world_tick, t3_talent_delta, t3_training_delta, t3_temperament_delta, reason
FROM lct_tensor_history
WHERE lct_id = 'lct:web4:agent:alice' AND tensor_type = 'T3'
ORDER BY world_tick DESC;

-- Find role assignments (context edges)
SELECT subject_lct, object_lct, predicate
FROM lct_context_edges
WHERE predicate = 'web4:hasRole' AND is_active = TRUE;

-- Aggregate V3 value created by agents in a society
SELECT owning_society_lct, AVG(v3_composite) as avg_value, COUNT(*) as agent_count
FROM lcts
WHERE lct_type = 'agent' AND is_active = TRUE
GROUP BY owning_society_lct
ORDER BY avg_value DESC;
```

## Integration with Existing Tables

### lct_identities (Session #66)

Keep existing table for backward compatibility. LCTs table is a superset.

```sql
-- Migration: Populate lcts from lct_identities
INSERT INTO lcts (lct_id, lct_type, owning_society_lct, created_at_block, created_at_tick)
SELECT
    lct_id,
    entity_type,
    'lct:web4:society:legacy',  -- Default owning society
    0,  -- Genesis block
    0   -- Genesis tick
FROM lct_identities
ON CONFLICT (lct_id) DO NOTHING;
```

### reputation_scores (Session #65)

Map T3 composite to reputation_score:

```sql
-- Update reputation scores from LCT T3
UPDATE reputation_scores rs
SET t3_score = l.t3_composite
FROM lcts l
WHERE rs.lct_id = l.lct_id AND l.is_active = TRUE;
```

## Performance Considerations

**Indexes**: Created on lct_type, owning_society_lct, active status, and composites for fast queries.

**JSONB**: Metadata stored as JSONB for flexible schema evolution and fast JSON queries.

**Partitioning**: Consider partitioning `lct_tensor_history` by month if history grows large.

**Caching**: LCT objects can be cached in-memory during simulation, synced to DB periodically.

## Implementation Plan

1. **Phase 1**: Create schema (this document)
2. **Phase 2**: Implement `sync_lct_to_db()` and `load_lct_from_db()`
3. **Phase 3**: Integrate with existing demos (add DB sync to LCT operations)
4. **Phase 4**: Migrate existing `lct_identities` data
5. **Phase 5**: Add tensor evolution tracking with automatic history recording

## Testing

```python
# Test sync
lct = create_agent_lct(agent_id="test", ...)
bridge = create_bridge()
assert bridge.sync_lct_to_db(lct)

# Test load
loaded = bridge.load_lct_from_db(lct.lct_id)
assert loaded.trust_axes == lct.trust_axes
assert loaded.value_axes == lct.value_axes

# Test evolution tracking
lct.update_trust({"talent": 0.9})
bridge.record_tensor_evolution(
    lct.lct_id, tick=10, tensor_type="T3",
    deltas={"talent": 0.1}, reason="Novel solution"
)
```

## Benefits

1. **Complete LCT State**: Full T3/V3/MRH persistence
2. **Temporal Tracking**: Evolution history for trust and value
3. **Graph Queries**: MRH context edges enable RDF-like queries
4. **Backward Compatible**: Extends existing `lct_identities` table
5. **Analytics Ready**: JSONB metadata and indexes enable complex queries
6. **ACID Compliant**: PostgreSQL guarantees for LCT state integrity

## Next Steps

- Implement sync functions in `db_bridge.py`
- Add LCT database sync to `run_lct_objects_demo.py`
- Create migration script for existing data
- Performance testing with 1000+ LCTs
- Document query patterns for common use cases
