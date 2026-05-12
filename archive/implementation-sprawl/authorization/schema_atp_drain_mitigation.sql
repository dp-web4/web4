--
-- ATP Drain Attack Mitigation Schema
-- Session #65: P2 Security Enhancement
--
-- Implements 4-layer defense against ATP drain attacks:
-- 1. Failure Attribution (identify sabotage)
-- 2. ATP Insurance (protect victims)
-- 3. Retry Mechanisms (automatic recovery)
-- 4. Reputation Gating (prevent abuse)
--

-- ============================================================================
-- 1. Failure Attribution
-- ============================================================================

CREATE TABLE IF NOT EXISTS failure_attributions (
    attribution_id BIGSERIAL PRIMARY KEY,
    sequence_id VARCHAR(255) REFERENCES action_sequences(sequence_id),
    iteration_number INTEGER,
    failure_type VARCHAR(100),  -- internal, resource_contention, dependency, sabotage, timeout
    attributed_to_lct VARCHAR(255),  -- Who is responsible (may be NULL if unattributable)
    evidence_hash VARCHAR(66),  -- SHA256 of evidence JSON
    confidence_score NUMERIC(3, 2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    investigation_status VARCHAR(50) DEFAULT 'pending',  -- pending, confirmed, dismissed
    penalty_applied BOOLEAN DEFAULT FALSE,
    notes TEXT
);

CREATE INDEX idx_failure_attrib_sequence ON failure_attributions(sequence_id);
CREATE INDEX idx_failure_attrib_lct ON failure_attributions(attributed_to_lct);
CREATE INDEX idx_failure_attrib_confidence ON failure_attributions(confidence_score DESC);
CREATE INDEX idx_failure_attrib_type ON failure_attributions(failure_type);

COMMENT ON TABLE failure_attributions IS
'Tracks failure causes and assigns responsibility for ATP drain attack detection (Session #65)';

COMMENT ON COLUMN failure_attributions.confidence_score IS
'Attribution confidence (0.00-1.00). Scores >0.80 trigger automatic penalties.';

-- ============================================================================
-- 2. ATP Insurance
-- ============================================================================

CREATE TABLE IF NOT EXISTS atp_insurance_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    sequence_id VARCHAR(255) REFERENCES action_sequences(sequence_id),
    policyholder_lct VARCHAR(255) REFERENCES lct_identities(lct_id),
    premium_paid INTEGER CHECK (premium_paid >= 0),
    max_payout INTEGER CHECK (max_payout >= 0),
    coverage_ratio NUMERIC(3, 2) CHECK (coverage_ratio >= 0 AND coverage_ratio <= 1),
    coverage_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    coverage_end TIMESTAMP WITH TIME ZONE,
    policy_status VARCHAR(50) DEFAULT 'active',  -- active, claimed, expired, cancelled
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_insurance_sequence ON atp_insurance_policies(sequence_id);
CREATE INDEX idx_insurance_lct ON atp_insurance_policies(policyholder_lct);
CREATE INDEX idx_insurance_status ON atp_insurance_policies(policy_status);

COMMENT ON TABLE atp_insurance_policies IS
'ATP insurance policies to protect against unattributable failures (Session #65)';

CREATE TABLE IF NOT EXISTS insurance_claims (
    claim_id BIGSERIAL PRIMARY KEY,
    policy_id BIGINT REFERENCES atp_insurance_policies(policy_id),
    sequence_id VARCHAR(255) REFERENCES action_sequences(sequence_id),
    atp_lost INTEGER CHECK (atp_lost >= 0),
    payout_amount INTEGER CHECK (payout_amount >= 0),
    claim_filed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    claim_processed_at TIMESTAMP WITH TIME ZONE,
    claim_status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, denied, paid
    denial_reason TEXT,
    processed_by VARCHAR(255)  -- Who/what processed the claim
);

CREATE INDEX idx_claims_policy ON insurance_claims(policy_id);
CREATE INDEX idx_claims_sequence ON insurance_claims(sequence_id);
CREATE INDEX idx_claims_status ON insurance_claims(claim_status);

COMMENT ON TABLE insurance_claims IS
'Insurance claims for ATP losses due to failures (Session #65)';

-- ============================================================================
-- 3. Retry Policies
-- ============================================================================

CREATE TABLE IF NOT EXISTS retry_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    sequence_id VARCHAR(255) REFERENCES action_sequences(sequence_id),
    max_retries INTEGER DEFAULT 3 CHECK (max_retries >= 0),
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    backoff_strategy VARCHAR(50) DEFAULT 'exponential',  -- exponential, linear, constant
    base_backoff_seconds NUMERIC(10, 2) DEFAULT 1.0,
    atp_reserved_for_retry INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_retry_sequence ON retry_policies(sequence_id);

COMMENT ON TABLE retry_policies IS
'Retry policies for automatic recovery from transient failures (Session #65)';

COMMENT ON COLUMN retry_policies.backoff_strategy IS
'Backoff strategy: exponential (2^n), linear (n), constant (1)';

-- ============================================================================
-- 4. Reputation Requirements
-- ============================================================================

CREATE TABLE IF NOT EXISTS reputation_requirements (
    requirement_id SERIAL PRIMARY KEY,
    operation_type VARCHAR(100),  -- action_sequence, delegation, resource_access
    atp_budget_min INTEGER CHECK (atp_budget_min >= 0),
    atp_budget_max INTEGER CHECK (atp_budget_max >= atp_budget_min),
    min_t3_score NUMERIC(3, 2) CHECK (min_t3_score >= 0 AND min_t3_score <= 1),
    min_v3_score NUMERIC(3, 2) CHECK (min_v3_score >= 0 AND min_v3_score <= 1),
    min_total_actions INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

CREATE INDEX idx_rep_req_operation ON reputation_requirements(operation_type);
CREATE INDEX idx_rep_req_atp_range ON reputation_requirements(atp_budget_min, atp_budget_max);

COMMENT ON TABLE reputation_requirements IS
'Reputation requirements for expensive operations to prevent ATP drain (Session #65)';

-- Default reputation requirements for action sequences
INSERT INTO reputation_requirements (operation_type, atp_budget_min, atp_budget_max, min_t3_score, description) VALUES
    ('action_sequence', 0, 100, 0.30, 'Low-cost operations: New identities allowed'),
    ('action_sequence', 101, 500, 0.50, 'Medium-cost operations: Established identities required'),
    ('action_sequence', 501, 2000, 0.70, 'High-cost operations: Trusted identities required'),
    ('action_sequence', 2001, 999999, 0.90, 'Critical operations: Highly trusted identities only')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 5. Functions
-- ============================================================================

-- Function: Check reputation requirement
CREATE OR REPLACE FUNCTION check_reputation_requirement(
    p_lct_id VARCHAR,
    p_org_id VARCHAR,
    p_atp_budget INTEGER,
    p_operation_type VARCHAR DEFAULT 'action_sequence'
) RETURNS JSONB AS $$
DECLARE
    v_t3_score NUMERIC;
    v_total_actions INTEGER;
    v_requirement RECORD;
    v_result JSONB;
BEGIN
    -- Get actor's reputation
    SELECT
        (talent_score + training_score + temperament_score) / 3.0,
        total_actions
    INTO v_t3_score, v_total_actions
    FROM reputation_scores
    WHERE lct_id = p_lct_id AND organization_id = p_org_id;

    IF v_t3_score IS NULL THEN
        -- No reputation found
        v_t3_score := 0.0;
        v_total_actions := 0;
    END IF;

    -- Find applicable requirement
    SELECT * INTO v_requirement
    FROM reputation_requirements
    WHERE operation_type = p_operation_type
      AND p_atp_budget >= atp_budget_min
      AND p_atp_budget <= atp_budget_max
    ORDER BY atp_budget_min DESC
    LIMIT 1;

    IF v_requirement IS NULL THEN
        -- No requirement found (shouldn't happen with defaults)
        RETURN jsonb_build_object(
            'allowed', true,
            'reason', 'no_requirement_found'
        );
    END IF;

    -- Check if meets requirements
    IF v_t3_score >= v_requirement.min_t3_score AND
       v_total_actions >= v_requirement.min_total_actions THEN
        RETURN jsonb_build_object(
            'allowed', true,
            't3_score', v_t3_score,
            'required_t3', v_requirement.min_t3_score,
            'total_actions', v_total_actions,
            'required_actions', v_requirement.min_total_actions
        );
    ELSE
        RETURN jsonb_build_object(
            'allowed', false,
            't3_score', v_t3_score,
            'required_t3', v_requirement.min_t3_score,
            'total_actions', v_total_actions,
            'required_actions', v_requirement.min_total_actions,
            'reason', CASE
                WHEN v_t3_score < v_requirement.min_t3_score THEN 'insufficient_reputation'
                WHEN v_total_actions < v_requirement.min_total_actions THEN 'insufficient_history'
                ELSE 'unknown'
            END
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_reputation_requirement IS
'Check if actor meets reputation requirements for ATP budget (Session #65)';

-- Function: Purchase ATP insurance
CREATE OR REPLACE FUNCTION purchase_atp_insurance(
    p_sequence_id VARCHAR,
    p_lct_id VARCHAR,
    p_coverage_ratio NUMERIC DEFAULT 0.5,
    p_premium_rate NUMERIC DEFAULT 0.05
) RETURNS JSONB AS $$
DECLARE
    v_sequence RECORD;
    v_premium INTEGER;
    v_max_payout INTEGER;
    v_policy_id BIGINT;
BEGIN
    -- Get sequence details
    SELECT * INTO v_sequence
    FROM action_sequences
    WHERE sequence_id = p_sequence_id;

    IF v_sequence IS NULL THEN
        RETURN jsonb_build_object('error', 'sequence_not_found');
    END IF;

    IF v_sequence.status != 'active' THEN
        RETURN jsonb_build_object('error', 'sequence_not_active');
    END IF;

    -- Calculate premium and max payout
    v_premium := CEIL(v_sequence.atp_budget_reserved * p_premium_rate);
    v_max_payout := CEIL(v_sequence.atp_budget_reserved * p_coverage_ratio);

    -- Check if enough ATP available
    IF v_sequence.atp_consumed + v_premium > v_sequence.atp_budget_reserved THEN
        RETURN jsonb_build_object('error', 'insufficient_atp_for_premium');
    END IF;

    -- Create insurance policy
    INSERT INTO atp_insurance_policies (
        sequence_id,
        policyholder_lct,
        premium_paid,
        max_payout,
        coverage_ratio,
        coverage_end
    ) VALUES (
        p_sequence_id,
        p_lct_id,
        v_premium,
        v_max_payout,
        p_coverage_ratio,
        CURRENT_TIMESTAMP + INTERVAL '7 days'
    ) RETURNING policy_id INTO v_policy_id;

    -- Deduct premium from ATP budget
    UPDATE action_sequences
    SET atp_consumed = atp_consumed + v_premium
    WHERE sequence_id = p_sequence_id;

    RETURN jsonb_build_object(
        'policy_id', v_policy_id,
        'premium_paid', v_premium,
        'max_payout', v_max_payout,
        'coverage_ratio', p_coverage_ratio
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION purchase_atp_insurance IS
'Purchase ATP insurance policy for action sequence (Session #65)';

-- Function: File insurance claim
CREATE OR REPLACE FUNCTION file_insurance_claim(
    p_sequence_id VARCHAR,
    p_atp_lost INTEGER
) RETURNS JSONB AS $$
DECLARE
    v_policy RECORD;
    v_payout INTEGER;
    v_claim_id BIGINT;
BEGIN
    -- Get active policy for sequence
    SELECT * INTO v_policy
    FROM atp_insurance_policies
    WHERE sequence_id = p_sequence_id
      AND policy_status = 'active'
      AND coverage_end > CURRENT_TIMESTAMP
    ORDER BY created_at DESC
    LIMIT 1;

    IF v_policy IS NULL THEN
        RETURN jsonb_build_object(
            'error', 'no_active_policy',
            'claim_status', 'denied'
        );
    END IF;

    -- Calculate payout (capped at max_payout)
    v_payout := LEAST(
        CEIL(p_atp_lost * v_policy.coverage_ratio),
        v_policy.max_payout
    );

    -- File claim
    INSERT INTO insurance_claims (
        policy_id,
        sequence_id,
        atp_lost,
        payout_amount,
        claim_status,
        claim_processed_at,
        processed_by
    ) VALUES (
        v_policy.policy_id,
        p_sequence_id,
        p_atp_lost,
        v_payout,
        'approved',  -- Auto-approve for now
        CURRENT_TIMESTAMP,
        'auto_processor'
    ) RETURNING claim_id INTO v_claim_id;

    -- Update policy status
    UPDATE atp_insurance_policies
    SET policy_status = 'claimed'
    WHERE policy_id = v_policy.policy_id;

    RETURN jsonb_build_object(
        'claim_id', v_claim_id,
        'claim_status', 'approved',
        'atp_lost', p_atp_lost,
        'payout_amount', v_payout,
        'coverage_ratio', v_policy.coverage_ratio
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION file_insurance_claim IS
'File insurance claim for ATP losses due to failure (Session #65)';

-- Function: Record failure attribution
CREATE OR REPLACE FUNCTION record_failure_attribution(
    p_sequence_id VARCHAR,
    p_iteration_number INTEGER,
    p_failure_type VARCHAR,
    p_attributed_to_lct VARCHAR,
    p_evidence_hash VARCHAR,
    p_confidence_score NUMERIC
) RETURNS JSONB AS $$
DECLARE
    v_attribution_id BIGINT;
    v_penalty_applied BOOLEAN := FALSE;
BEGIN
    -- Record attribution
    INSERT INTO failure_attributions (
        sequence_id,
        iteration_number,
        failure_type,
        attributed_to_lct,
        evidence_hash,
        confidence_score,
        investigation_status
    ) VALUES (
        p_sequence_id,
        p_iteration_number,
        p_failure_type,
        p_attributed_to_lct,
        p_evidence_hash,
        p_confidence_score,
        CASE WHEN p_confidence_score >= 0.80 THEN 'confirmed' ELSE 'pending' END
    ) RETURNING attribution_id INTO v_attribution_id;

    -- If high confidence sabotage, apply penalty
    IF p_failure_type = 'sabotage' AND p_confidence_score >= 0.80 AND p_attributed_to_lct IS NOT NULL THEN
        -- Penalize attacker's reputation
        -- Find all organizations where attacker has reputation
        UPDATE reputation_scores
        SET
            temperament_score = GREATEST(0, temperament_score - 0.10),  -- -0.10 penalty
            last_updated = CURRENT_TIMESTAMP
        WHERE lct_id = p_attributed_to_lct;

        -- Record in trust history
        INSERT INTO trust_history (
            lct_id,
            organization_id,
            t3_delta,
            event_type,
            event_description
        )
        SELECT
            p_attributed_to_lct,
            organization_id,
            -0.10,
            'sabotage_penalty',
            format('ATP drain attack detected on sequence %s (confidence: %s)', p_sequence_id, p_confidence_score)
        FROM reputation_scores
        WHERE lct_id = p_attributed_to_lct;

        v_penalty_applied := TRUE;

        -- Mark penalty applied
        UPDATE failure_attributions
        SET penalty_applied = TRUE
        WHERE attribution_id = v_attribution_id;
    END IF;

    RETURN jsonb_build_object(
        'attribution_id', v_attribution_id,
        'confidence', p_confidence_score,
        'status', CASE WHEN p_confidence_score >= 0.80 THEN 'confirmed' ELSE 'pending' END,
        'penalty_applied', v_penalty_applied
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION record_failure_attribution IS
'Record failure attribution and apply penalties for high-confidence sabotage (Session #65)';

-- ============================================================================
-- 6. Views
-- ============================================================================

-- View: ATP drain attack summary
CREATE OR REPLACE VIEW atp_drain_attack_summary AS
SELECT
    fa.attribution_id,
    fa.sequence_id,
    fa.attributed_to_lct as attacker_lct,
    fa.failure_type,
    fa.confidence_score,
    fa.detected_at,
    fa.penalty_applied,
    aseq.actor_lct as victim_lct,
    aseq.atp_consumed as atp_lost,
    ic.payout_amount as insurance_payout,
    fa.investigation_status
FROM failure_attributions fa
JOIN action_sequences aseq ON aseq.sequence_id = fa.sequence_id
LEFT JOIN insurance_claims ic ON ic.sequence_id = fa.sequence_id
WHERE fa.failure_type IN ('sabotage', 'resource_contention')
ORDER BY fa.detected_at DESC;

COMMENT ON VIEW atp_drain_attack_summary IS
'Summary of potential ATP drain attacks for monitoring (Session #65)';

-- View: Insurance statistics
CREATE OR REPLACE VIEW insurance_statistics AS
SELECT
    COUNT(*) as total_policies,
    SUM(premium_paid) as total_premiums,
    SUM(CASE WHEN policy_status = 'claimed' THEN 1 ELSE 0 END) as policies_claimed,
    (SELECT SUM(payout_amount) FROM insurance_claims WHERE claim_status = 'paid') as total_payouts,
    SUM(premium_paid) - COALESCE((SELECT SUM(payout_amount) FROM insurance_claims WHERE claim_status = 'paid'), 0) as net_revenue
FROM atp_insurance_policies;

COMMENT ON VIEW insurance_statistics IS
'ATP insurance fund statistics for risk management (Session #65)';
