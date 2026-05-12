-- Web4 V3 Trust Tensor - Schema Extension
-- Session #55: Implementation of Session #53 Trust API Extensions (Q10)
--
-- Extends reputation system to support V3 trust tensor:
-- 1. V3 scores (Veracity, Validity, Valuation)
-- 2. Trust history for temporal tracking
-- 3. Trust relationships between entities
-- 4. Phi-based trust updates
--
-- This implements the design from SAGE_INTEGRATION_ANSWERS.md Q10-Q12

-- ============================================================================
-- V3 Trust Scores
-- ============================================================================

CREATE TABLE IF NOT EXISTS v3_scores (
    lct_id VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id) ON DELETE CASCADE,
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(organization_id),

    -- V3 components (Veracity, Validity, Valuation)
    veracity_score NUMERIC(4, 3) DEFAULT 0.5 CHECK (veracity_score >= 0.0 AND veracity_score <= 1.0),
    validity_score NUMERIC(4, 3) DEFAULT 0.5 CHECK (validity_score >= 0.0 AND validity_score <= 1.0),
    valuation_score NUMERIC(4, 3) DEFAULT 0.5 CHECK (valuation_score >= 0.0 AND valuation_score <= 1.0),

    -- Aggregated V3
    v3_score NUMERIC(4, 3) GENERATED ALWAYS AS (
        (veracity_score + validity_score + valuation_score) / 3.0
    ) STORED,

    -- Transaction statistics
    total_transactions INTEGER DEFAULT 0,
    successful_transactions INTEGER DEFAULT 0,
    disputed_transactions INTEGER DEFAULT 0,
    reversed_transactions INTEGER DEFAULT 0,

    -- Value statistics
    total_value_transacted NUMERIC(12, 2) DEFAULT 0.0,
    avg_transaction_value NUMERIC(10, 2),

    -- Timestamps
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_transaction_at TIMESTAMP WITH TIME ZONE,

    PRIMARY KEY (lct_id, organization_id)
);

CREATE INDEX idx_v3_lct ON v3_scores(lct_id);
CREATE INDEX idx_v3_org ON v3_scores(organization_id);
CREATE INDEX idx_v3_score ON v3_scores(v3_score DESC);
CREATE INDEX idx_v3_veracity ON v3_scores(veracity_score DESC);
CREATE INDEX idx_v3_validity ON v3_scores(validity_score DESC);
CREATE INDEX idx_v3_valuation ON v3_scores(valuation_score DESC);

COMMENT ON TABLE v3_scores IS 'V3 trust tensor: Veracity (truthfulness), Validity (correctness), Valuation (value delivered)';
COMMENT ON COLUMN v3_scores.veracity_score IS 'Veracity: Truthfulness and honesty in claims and communications';
COMMENT ON COLUMN v3_scores.validity_score IS 'Validity: Correctness and accuracy of work delivered';
COMMENT ON COLUMN v3_scores.valuation_score IS 'Valuation: Value and utility provided to others';
COMMENT ON COLUMN v3_scores.v3_score IS 'Aggregated V3 score (average of veracity, validity, valuation)';

-- ============================================================================
-- Trust History
-- ============================================================================

CREATE TABLE IF NOT EXISTS trust_history (
    history_id BIGSERIAL PRIMARY KEY,
    lct_id VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id) ON DELETE CASCADE,
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(organization_id),

    -- Timestamp
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- T3 snapshot (Talent, Training, Temperament)
    talent_score NUMERIC(4, 3),
    training_score NUMERIC(4, 3),
    temperament_score NUMERIC(4, 3),
    t3_score NUMERIC(4, 3),

    -- V3 snapshot (Veracity, Validity, Valuation)
    veracity_score NUMERIC(4, 3),
    validity_score NUMERIC(4, 3),
    valuation_score NUMERIC(4, 3),
    v3_score NUMERIC(4, 3),

    -- Event that triggered update
    event_type VARCHAR(100), -- action_success, action_failure, transaction_complete, phi_contribution, etc.
    event_id VARCHAR(255), -- Reference to action/transaction/event
    event_description TEXT,

    -- Delta from previous
    t3_delta NUMERIC(5, 4), -- Change in T3 score
    v3_delta NUMERIC(5, 4), -- Change in V3 score

    -- Phi contribution (if applicable)
    phi_contribution NUMERIC(6, 4), -- Integrated information contribution

    -- Metadata
    context JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_trust_history_lct ON trust_history(lct_id);
CREATE INDEX idx_trust_history_org ON trust_history(organization_id);
CREATE INDEX idx_trust_history_time ON trust_history(recorded_at DESC);
CREATE INDEX idx_trust_history_event ON trust_history(event_type);
CREATE INDEX idx_trust_history_phi ON trust_history(phi_contribution DESC) WHERE phi_contribution IS NOT NULL;

COMMENT ON TABLE trust_history IS 'Temporal tracking of trust score evolution';
COMMENT ON COLUMN trust_history.phi_contribution IS 'Integrated information contribution (Φ) from action or transaction';

-- ============================================================================
-- Trust Relationships
-- ============================================================================

CREATE TABLE IF NOT EXISTS trust_relationships (
    relationship_id BIGSERIAL PRIMARY KEY,
    source_lct VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id) ON DELETE CASCADE,
    target_lct VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id) ON DELETE CASCADE,
    organization_id VARCHAR(255) REFERENCES organizations(organization_id),

    -- Relationship type
    relationship_type VARCHAR(50) NOT NULL, -- witnessed, collaborated, delegated_to, transacted_with

    -- Direct trust score (source's trust in target)
    trust_score NUMERIC(4, 3) CHECK (trust_score >= 0.0 AND trust_score <= 1.0),
    confidence NUMERIC(4, 3) DEFAULT 0.5, -- How confident source is in this trust score

    -- Interaction statistics
    interaction_count INTEGER DEFAULT 1,
    last_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    first_interaction_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Success/failure tracking
    successful_interactions INTEGER DEFAULT 0,
    failed_interactions INTEGER DEFAULT 0,
    disputed_interactions INTEGER DEFAULT 0,

    -- Metadata
    relationship_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (source_lct, target_lct, organization_id, relationship_type),
    CONSTRAINT chk_no_self_trust CHECK (source_lct != target_lct)
);

CREATE INDEX idx_trust_rel_source ON trust_relationships(source_lct);
CREATE INDEX idx_trust_rel_target ON trust_relationships(target_lct);
CREATE INDEX idx_trust_rel_org ON trust_relationships(organization_id);
CREATE INDEX idx_trust_rel_type ON trust_relationships(relationship_type);
CREATE INDEX idx_trust_rel_score ON trust_relationships(trust_score DESC);

COMMENT ON TABLE trust_relationships IS 'Direct trust relationships between entities';
COMMENT ON COLUMN trust_relationships.trust_score IS 'Source entity''s trust in target entity (0.0-1.0)';
COMMENT ON COLUMN trust_relationships.confidence IS 'Confidence in trust score based on interaction history';

-- ============================================================================
-- Views
-- ============================================================================

-- Complete Trust Profile (T3 + V3)
CREATE OR REPLACE VIEW complete_trust_profiles AS
SELECT
    lct.lct_id,
    lct.entity_type,
    lct.society_id,
    -- T3 scores
    t3.talent_score,
    t3.training_score,
    t3.temperament_score,
    t3.t3_score,
    t3.reputation_level,
    -- V3 scores
    v3.veracity_score,
    v3.validity_score,
    v3.valuation_score,
    v3.v3_score,
    -- Statistics
    t3.total_actions,
    t3.successful_actions,
    t3.failed_actions,
    v3.total_transactions,
    v3.successful_transactions,
    v3.disputed_transactions,
    -- Organization
    t3.organization_id,
    o.organization_name
FROM lct_identities lct
LEFT JOIN reputation_scores t3 ON lct.lct_id = t3.lct_id
LEFT JOIN v3_scores v3 ON lct.lct_id = v3.lct_id AND t3.organization_id = v3.organization_id
LEFT JOIN organizations o ON t3.organization_id = o.organization_id;

COMMENT ON VIEW complete_trust_profiles IS 'Complete trust profile combining T3 (capability) and V3 (transaction) scores';

-- Trust Evolution Timeline
CREATE OR REPLACE VIEW trust_evolution AS
SELECT
    th.lct_id,
    th.organization_id,
    th.recorded_at,
    th.t3_score,
    th.v3_score,
    th.t3_delta,
    th.v3_delta,
    th.event_type,
    th.phi_contribution,
    -- Running statistics
    AVG(th.t3_score) OVER (
        PARTITION BY th.lct_id, th.organization_id
        ORDER BY th.recorded_at
        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ) AS t3_ma10, -- 10-point moving average
    AVG(th.v3_score) OVER (
        PARTITION BY th.lct_id, th.organization_id
        ORDER BY th.recorded_at
        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ) AS v3_ma10
FROM trust_history th
ORDER BY th.lct_id, th.organization_id, th.recorded_at DESC;

COMMENT ON VIEW trust_evolution IS 'Temporal evolution of trust scores with moving averages';

-- Trust Network
CREATE OR REPLACE VIEW trust_network AS
SELECT
    tr.source_lct,
    tr.target_lct,
    tr.relationship_type,
    tr.trust_score,
    tr.confidence,
    tr.interaction_count,
    tr.successful_interactions,
    tr.failed_interactions,
    (tr.successful_interactions::FLOAT / NULLIF(tr.interaction_count, 0)) AS success_rate,
    tr.last_interaction_at,
    -- Source trust
    t3_source.t3_score AS source_t3,
    v3_source.v3_score AS source_v3,
    -- Target trust
    t3_target.t3_score AS target_t3,
    v3_target.v3_score AS target_v3,
    tr.organization_id
FROM trust_relationships tr
LEFT JOIN reputation_scores t3_source ON tr.source_lct = t3_source.lct_id AND tr.organization_id = t3_source.organization_id
LEFT JOIN v3_scores v3_source ON tr.source_lct = v3_source.lct_id AND tr.organization_id = v3_source.organization_id
LEFT JOIN reputation_scores t3_target ON tr.target_lct = t3_target.lct_id AND tr.organization_id = t3_target.organization_id
LEFT JOIN v3_scores v3_target ON tr.target_lct = v3_target.lct_id AND tr.organization_id = v3_target.organization_id;

COMMENT ON VIEW trust_network IS 'Trust network graph with source/target trust scores';

-- ============================================================================
-- Functions
-- ============================================================================

-- Update V3 scores from transaction
CREATE OR REPLACE FUNCTION update_v3_from_transaction(
    p_lct_id VARCHAR(255),
    p_org_id VARCHAR(255),
    p_success BOOLEAN,
    p_transaction_value NUMERIC,
    p_disputed BOOLEAN DEFAULT FALSE
) RETURNS void AS $$
BEGIN
    -- Ensure V3 record exists
    INSERT INTO v3_scores (lct_id, organization_id)
    VALUES (p_lct_id, p_org_id)
    ON CONFLICT (lct_id, organization_id) DO NOTHING;

    -- Update statistics and scores
    IF p_success THEN
        UPDATE v3_scores
        SET total_transactions = total_transactions + 1,
            successful_transactions = successful_transactions + 1,
            disputed_transactions = disputed_transactions + CASE WHEN p_disputed THEN 1 ELSE 0 END,
            total_value_transacted = total_value_transacted + p_transaction_value,
            avg_transaction_value = (total_value_transacted + p_transaction_value) / (total_transactions + 1),
            -- Increase validity (successful transaction)
            validity_score = LEAST(1.0, validity_score + 0.01),
            -- Increase valuation (value delivered)
            valuation_score = LEAST(1.0, valuation_score + (p_transaction_value / 100.0) * 0.01),
            -- Decrease veracity if disputed
            veracity_score = CASE WHEN p_disputed
                THEN GREATEST(0.0, veracity_score - 0.02)
                ELSE LEAST(1.0, veracity_score + 0.005)
            END,
            last_updated = CURRENT_TIMESTAMP,
            last_transaction_at = CURRENT_TIMESTAMP
        WHERE lct_id = p_lct_id AND organization_id = p_org_id;
    ELSE
        UPDATE v3_scores
        SET total_transactions = total_transactions + 1,
            -- Decrease validity (failed transaction)
            validity_score = GREATEST(0.0, validity_score - 0.01),
            -- Decrease valuation (no value delivered)
            valuation_score = GREATEST(0.0, valuation_score - 0.005),
            last_updated = CURRENT_TIMESTAMP,
            last_transaction_at = CURRENT_TIMESTAMP
        WHERE lct_id = p_lct_id AND organization_id = p_org_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_v3_from_transaction IS 'Update V3 trust scores based on transaction outcomes';

-- Record trust history snapshot
CREATE OR REPLACE FUNCTION record_trust_snapshot(
    p_lct_id VARCHAR(255),
    p_org_id VARCHAR(255),
    p_event_type VARCHAR(100),
    p_event_id VARCHAR(255),
    p_phi_contribution NUMERIC DEFAULT NULL
) RETURNS BIGINT AS $$
DECLARE
    history_id BIGINT;
    prev_t3 NUMERIC;
    prev_v3 NUMERIC;
    curr_t3 NUMERIC;
    curr_v3 NUMERIC;
BEGIN
    -- Get current scores
    SELECT t3_score INTO curr_t3 FROM reputation_scores WHERE lct_id = p_lct_id AND organization_id = p_org_id;
    SELECT v3_score INTO curr_v3 FROM v3_scores WHERE lct_id = p_lct_id AND organization_id = p_org_id;

    -- Get previous scores
    SELECT t3_score, v3_score INTO prev_t3, prev_v3
    FROM trust_history
    WHERE lct_id = p_lct_id AND organization_id = p_org_id
    ORDER BY recorded_at DESC
    LIMIT 1;

    -- Insert history record
    INSERT INTO trust_history (
        lct_id, organization_id, event_type, event_id, phi_contribution,
        talent_score, training_score, temperament_score, t3_score,
        veracity_score, validity_score, valuation_score, v3_score,
        t3_delta, v3_delta
    )
    SELECT
        p_lct_id, p_org_id, p_event_type, p_event_id, p_phi_contribution,
        t3.talent_score, t3.training_score, t3.temperament_score, t3.t3_score,
        v3.veracity_score, v3.validity_score, v3.valuation_score, v3.v3_score,
        COALESCE(curr_t3 - prev_t3, 0.0), COALESCE(curr_v3 - prev_v3, 0.0)
    FROM reputation_scores t3
    LEFT JOIN v3_scores v3 ON t3.lct_id = v3.lct_id AND t3.organization_id = v3.organization_id
    WHERE t3.lct_id = p_lct_id AND t3.organization_id = p_org_id
    RETURNING trust_history.history_id INTO history_id;

    RETURN history_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION record_trust_snapshot IS 'Record snapshot of trust scores in history for temporal tracking';

-- Update or create trust relationship
CREATE OR REPLACE FUNCTION update_trust_relationship(
    p_source_lct VARCHAR(255),
    p_target_lct VARCHAR(255),
    p_org_id VARCHAR(255),
    p_relationship_type VARCHAR(50),
    p_success BOOLEAN
) RETURNS void AS $$
DECLARE
    current_score NUMERIC;
    new_score NUMERIC;
BEGIN
    -- Get current trust score if exists
    SELECT trust_score INTO current_score
    FROM trust_relationships
    WHERE source_lct = p_source_lct AND target_lct = p_target_lct
      AND organization_id = p_org_id AND relationship_type = p_relationship_type;

    -- Calculate new score (exponential moving average)
    IF current_score IS NULL THEN
        new_score := CASE WHEN p_success THEN 0.7 ELSE 0.3 END;
    ELSE
        -- EMA: new = α × outcome + (1 - α) × old, where α = 0.1
        new_score := 0.1 * (CASE WHEN p_success THEN 1.0 ELSE 0.0 END) + 0.9 * current_score;
    END IF;

    -- Upsert relationship
    INSERT INTO trust_relationships (
        source_lct, target_lct, organization_id, relationship_type,
        trust_score, interaction_count,
        successful_interactions, failed_interactions
    ) VALUES (
        p_source_lct, p_target_lct, p_org_id, p_relationship_type,
        new_score, 1,
        CASE WHEN p_success THEN 1 ELSE 0 END,
        CASE WHEN p_success THEN 0 ELSE 1 END
    )
    ON CONFLICT (source_lct, target_lct, organization_id, relationship_type)
    DO UPDATE SET
        trust_score = new_score,
        interaction_count = trust_relationships.interaction_count + 1,
        successful_interactions = trust_relationships.successful_interactions + CASE WHEN p_success THEN 1 ELSE 0 END,
        failed_interactions = trust_relationships.failed_interactions + CASE WHEN p_success THEN 0 ELSE 1 END,
        confidence = LEAST(1.0, trust_relationships.confidence + 0.05),
        last_interaction_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_trust_relationship IS 'Update trust relationship between entities based on interaction outcome';

-- ============================================================================
-- Triggers
-- ============================================================================

CREATE TRIGGER update_trust_relationships_updated_at BEFORE UPDATE ON trust_relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample Data
-- ============================================================================

-- Initialize V3 scores for existing entities with reputation
INSERT INTO v3_scores (lct_id, organization_id, veracity_score, validity_score, valuation_score)
SELECT lct_id, organization_id, 0.5, 0.5, 0.5
FROM reputation_scores
ON CONFLICT (lct_id, organization_id) DO NOTHING;

COMMENT ON TABLE v3_scores IS 'V3 trust tensor from Session #53 Q10 - enables transaction-based trust tracking';
