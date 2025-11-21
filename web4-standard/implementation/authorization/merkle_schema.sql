-- Merkle Tree Anchoring Schema
-- Session #57: Database schema for trust update Merkle trees
--
-- Purpose: Store Merkle roots and proofs for cryptographic auditability
-- Phase 1: Off-chain storage only (blockchain anchoring in Phase 2)

-- ============================================================================
-- Table: merkle_roots
-- Stores one row per flush, with the Merkle root for that batch
-- ============================================================================

CREATE TABLE IF NOT EXISTS merkle_roots (
    root_id BIGSERIAL PRIMARY KEY,
    merkle_root VARCHAR(64) NOT NULL UNIQUE,  -- SHA-256 hex (64 chars)
    previous_root VARCHAR(64),                 -- Chain to previous flush
    flush_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    batch_size INTEGER NOT NULL,               -- Number of updates in batch
    leaf_count INTEGER NOT NULL,               -- Number of entities (leaves)

    -- Statistics
    total_actions INTEGER DEFAULT 0,
    total_transactions INTEGER DEFAULT 0,

    -- Blockchain anchoring (Phase 2)
    blockchain_tx_hash VARCHAR(66),            -- Ethereum tx hash
    blockchain_block_number BIGINT,            -- Block number
    anchored_at TIMESTAMP,                     -- When anchored on-chain

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (batch_size > 0),
    CHECK (leaf_count > 0),
    CHECK (LENGTH(merkle_root) = 64)
);

-- Index for querying by timestamp
CREATE INDEX IF NOT EXISTS idx_merkle_roots_timestamp
    ON merkle_roots(flush_timestamp DESC);

-- Index for blockchain lookups
CREATE INDEX IF NOT EXISTS idx_merkle_roots_blockchain
    ON merkle_roots(blockchain_tx_hash)
    WHERE blockchain_tx_hash IS NOT NULL;

-- ============================================================================
-- Table: trust_update_leaves
-- Stores individual trust updates that were included in Merkle trees
-- ============================================================================

CREATE TABLE IF NOT EXISTS trust_update_leaves (
    leaf_id BIGSERIAL PRIMARY KEY,
    root_id BIGINT NOT NULL REFERENCES merkle_roots(root_id) ON DELETE CASCADE,
    leaf_index INTEGER NOT NULL,               -- Index in Merkle tree (0-based)

    -- Entity identification
    lct_id VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id),
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(organization_id),

    -- Trust deltas (what was updated)
    talent_delta NUMERIC(10,6),
    training_delta NUMERIC(10,6),
    temperament_delta NUMERIC(10,6),
    veracity_delta NUMERIC(10,6),
    validity_delta NUMERIC(10,6),
    valuation_delta NUMERIC(10,6),

    -- Statistics
    action_count INTEGER DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,

    -- Hashes
    leaf_hash VARCHAR(64) NOT NULL,            -- SHA-256 of this leaf

    -- Timestamp
    update_timestamp TIMESTAMP NOT NULL,

    -- Constraints
    UNIQUE (root_id, leaf_index),
    UNIQUE (root_id, lct_id, organization_id),  -- One update per entity per flush
    CHECK (leaf_index >= 0),
    CHECK (LENGTH(leaf_hash) = 64)
);

-- Index for entity lookups
CREATE INDEX IF NOT EXISTS idx_leaves_lct
    ON trust_update_leaves(lct_id, organization_id);

-- Index for root lookups
CREATE INDEX IF NOT EXISTS idx_leaves_root
    ON trust_update_leaves(root_id, leaf_index);

-- ============================================================================
-- Table: merkle_proofs
-- Pre-computed Merkle proofs for efficient verification
-- ============================================================================

CREATE TABLE IF NOT EXISTS merkle_proofs (
    proof_id BIGSERIAL PRIMARY KEY,
    leaf_id BIGINT NOT NULL REFERENCES trust_update_leaves(leaf_id) ON DELETE CASCADE,
    root_id BIGINT NOT NULL REFERENCES merkle_roots(root_id) ON DELETE CASCADE,

    -- Proof data (JSON array of [hash_hex, position])
    -- Example: [["abc123...", "right"], ["def456...", "left"], ...]
    proof_path JSONB NOT NULL,

    -- Verification
    proof_length INTEGER NOT NULL,             -- Number of hashes in proof
    verified BOOLEAN DEFAULT FALSE,            -- Whether proof has been verified

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,

    -- Constraints
    UNIQUE (leaf_id),                          -- One proof per leaf
    CHECK (proof_length >= 0)
);

-- Index for verification status
CREATE INDEX IF NOT EXISTS idx_proofs_verified
    ON merkle_proofs(verified, verified_at);

-- ============================================================================
-- View: trust_audit_trail
-- Combined view of entity trust updates with Merkle proofs
-- ============================================================================

CREATE OR REPLACE VIEW trust_audit_trail AS
SELECT
    l.leaf_id,
    l.lct_id,
    l.organization_id,
    l.update_timestamp,
    l.talent_delta,
    l.training_delta,
    l.temperament_delta,
    l.veracity_delta,
    l.validity_delta,
    l.valuation_delta,
    l.action_count,
    l.transaction_count,
    l.leaf_hash,
    r.merkle_root,
    r.flush_timestamp,
    r.batch_size,
    r.blockchain_tx_hash,
    r.anchored_at,
    p.proof_path,
    p.verified,
    p.verified_at
FROM trust_update_leaves l
JOIN merkle_roots r ON l.root_id = r.root_id
LEFT JOIN merkle_proofs p ON l.leaf_id = p.leaf_id
ORDER BY l.update_timestamp DESC;

-- ============================================================================
-- View: merkle_chain
-- Shows the chain of Merkle roots (linked via previous_root)
-- ============================================================================

CREATE OR REPLACE VIEW merkle_chain AS
WITH RECURSIVE chain AS (
    -- Start with most recent root
    SELECT
        root_id,
        merkle_root,
        previous_root,
        flush_timestamp,
        batch_size,
        blockchain_tx_hash,
        1 as depth
    FROM merkle_roots
    WHERE root_id = (SELECT MAX(root_id) FROM merkle_roots)

    UNION ALL

    -- Follow the chain backwards
    SELECT
        r.root_id,
        r.merkle_root,
        r.previous_root,
        r.flush_timestamp,
        r.batch_size,
        r.blockchain_tx_hash,
        c.depth + 1
    FROM merkle_roots r
    JOIN chain c ON r.merkle_root = c.previous_root
)
SELECT * FROM chain ORDER BY depth;

-- ============================================================================
-- Function: verify_merkle_proof
-- Verifies a Merkle proof for a given leaf
-- ============================================================================

CREATE OR REPLACE FUNCTION verify_merkle_proof(
    p_leaf_hash VARCHAR(64),
    p_proof_path JSONB,
    p_merkle_root VARCHAR(64)
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_hash VARCHAR(64);
    v_proof_item JSONB;
    v_sibling_hash VARCHAR(64);
    v_position VARCHAR(10);
BEGIN
    -- Start with leaf hash
    v_current_hash := p_leaf_hash;

    -- Apply each proof step
    FOR v_proof_item IN SELECT jsonb_array_elements FROM jsonb_array_elements(p_proof_path)
    LOOP
        v_sibling_hash := v_proof_item->>0;
        v_position := v_proof_item->>1;

        -- Hash with sibling (position determines order)
        IF v_position = 'left' THEN
            v_current_hash := encode(sha256(decode(v_sibling_hash || v_current_hash, 'hex')), 'hex');
        ELSE
            v_current_hash := encode(sha256(decode(v_current_hash || v_sibling_hash, 'hex')), 'hex');
        END IF;
    END LOOP;

    -- Check if we reached the root
    RETURN v_current_hash = p_merkle_root;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- Function: get_entity_trust_history
-- Gets full trust update history for an entity with Merkle proofs
-- ============================================================================

CREATE OR REPLACE FUNCTION get_entity_trust_history(
    p_lct_id VARCHAR(255),
    p_org_id VARCHAR(255),
    p_limit INTEGER DEFAULT 100
) RETURNS TABLE (
    update_timestamp TIMESTAMP,
    talent_delta NUMERIC,
    training_delta NUMERIC,
    temperament_delta NUMERIC,
    veracity_delta NUMERIC,
    validity_delta NUMERIC,
    valuation_delta NUMERIC,
    merkle_root VARCHAR(64),
    leaf_hash VARCHAR(64),
    proof_verified BOOLEAN,
    blockchain_tx VARCHAR(66)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        l.update_timestamp,
        l.talent_delta,
        l.training_delta,
        l.temperament_delta,
        l.veracity_delta,
        l.validity_delta,
        l.valuation_delta,
        r.merkle_root,
        l.leaf_hash,
        COALESCE(p.verified, FALSE) as proof_verified,
        r.blockchain_tx_hash
    FROM trust_update_leaves l
    JOIN merkle_roots r ON l.root_id = r.root_id
    LEFT JOIN merkle_proofs p ON l.leaf_id = p.leaf_id
    WHERE l.lct_id = p_lct_id AND l.organization_id = p_org_id
    ORDER BY l.update_timestamp DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON TABLE merkle_roots IS
    'Merkle roots for trust update batches - one per flush';

COMMENT ON TABLE trust_update_leaves IS
    'Individual trust updates included in Merkle trees';

COMMENT ON TABLE merkle_proofs IS
    'Pre-computed Merkle proofs for efficient verification';

COMMENT ON VIEW trust_audit_trail IS
    'Complete audit trail of trust updates with Merkle proofs';

COMMENT ON VIEW merkle_chain IS
    'Chain of Merkle roots showing trust history lineage';

COMMENT ON FUNCTION verify_merkle_proof IS
    'Verifies a Merkle proof matches the given root';

COMMENT ON FUNCTION get_entity_trust_history IS
    'Gets trust update history for an entity with Merkle proofs';

-- ============================================================================
-- Usage Examples
-- ============================================================================

/*
-- Example 1: Query recent Merkle roots
SELECT
    merkle_root,
    flush_timestamp,
    batch_size,
    leaf_count,
    blockchain_tx_hash
FROM merkle_roots
ORDER BY flush_timestamp DESC
LIMIT 10;

-- Example 2: Get trust history for an entity
SELECT * FROM get_entity_trust_history('lct:ai:nova:001', 'org:web4:001', 50);

-- Example 3: Verify a proof
SELECT verify_merkle_proof(
    'abc123...',
    '[["def456...", "right"], ["ghi789...", "left"]]'::jsonb,
    'root123...'
);

-- Example 4: Audit trail for specific time range
SELECT * FROM trust_audit_trail
WHERE update_timestamp BETWEEN '2025-11-20' AND '2025-11-22'
ORDER BY update_timestamp DESC;

-- Example 5: Check Merkle chain integrity
SELECT * FROM merkle_chain;
*/
