-- ATP Refund Exploit Mitigation - Session #62
-- ================================================
--
-- Prevents ATP Refund Exploitation (Attack Vector 4.1) by tracking actual
-- resource consumption and implementing non-refundable ATP.
--
-- Attack Pattern (from ATTACK_VECTORS.md):
-- 1. Reserve 100 ATP with FULL refund policy
-- 2. Execute expensive operation consuming real resources
-- 3. Trigger failure before full ATP charged
-- 4. Get refunded despite resource consumption
--
-- Solution:
-- 1. Track resource consumption separately from ATP charging
-- 2. Implement minimum non-refundable ATP per iteration
-- 3. Enforce partial refunds based on actual resource usage
-- 4. Add refund limits to prevent abuse

-- ============================================================================
-- Schema Extensions for Resource Tracking
-- ============================================================================

-- Add resource consumption tracking to action_sequences
ALTER TABLE action_sequences ADD COLUMN IF NOT EXISTS
    atp_committed INTEGER DEFAULT 0;  -- ATP that cannot be refunded (resource costs)

ALTER TABLE action_sequences ADD COLUMN IF NOT EXISTS
    resource_consumption_log JSONB DEFAULT '[]'::jsonb;  -- Log of actual resource usage

ALTER TABLE action_sequences ADD COLUMN IF NOT EXISTS
    min_retention_ratio NUMERIC(3, 2) DEFAULT 0.50;  -- Minimum % of ATP to retain (50%)

COMMENT ON COLUMN action_sequences.atp_committed IS 'ATP committed to resource consumption (non-refundable)';
COMMENT ON COLUMN action_sequences.resource_consumption_log IS 'Array of {iteration, resource_type, amount, cost_atp} entries';
COMMENT ON COLUMN action_sequences.min_retention_ratio IS 'Minimum ratio of ATP to retain even on failure (e.g., 0.50 = 50%)';

-- ============================================================================
-- Refund Limits (Prevent Rapid Cycling Attacks)
-- ============================================================================

CREATE TABLE IF NOT EXISTS atp_refund_limits (
    lct_id VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id),
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(organization_id),

    -- Time window tracking
    window_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    window_duration_hours INTEGER DEFAULT 24,  -- 24-hour rolling window

    -- Refund tracking
    total_refunds_received INTEGER DEFAULT 0,
    refund_count INTEGER DEFAULT 0,
    max_refunds_per_window INTEGER DEFAULT 10,  -- Max 10 refunds per day
    max_total_refund_per_window INTEGER DEFAULT 1000,  -- Max 1000 ATP refunded per day

    -- Flags
    refund_abuse_detected BOOLEAN DEFAULT FALSE,
    last_refund_at TIMESTAMP WITH TIME ZONE,

    PRIMARY KEY (lct_id, organization_id),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refund_limits_lct ON atp_refund_limits(lct_id);
CREATE INDEX idx_refund_limits_window ON atp_refund_limits(window_start);

COMMENT ON TABLE atp_refund_limits IS 'Rate limits for ATP refunds to prevent rapid cycling attacks';

-- ============================================================================
-- Updated Finalize Function with Resource-Aware Refunds
-- ============================================================================

CREATE OR REPLACE FUNCTION finalize_sequence_v2(
    p_sequence_id VARCHAR(255),
    p_success BOOLEAN
) RETURNS JSONB AS $$
DECLARE
    seq RECORD;
    refund_amount INTEGER;
    unused_atp INTEGER;
    completion_ratio NUMERIC;
    min_retention INTEGER;
    resource_committed INTEGER;
    refund_limit_check RECORD;
    effective_refund INTEGER;
BEGIN
    -- Get sequence with lock
    SELECT * INTO seq FROM action_sequences WHERE sequence_id = p_sequence_id FOR UPDATE;

    IF seq IS NULL THEN
        RETURN jsonb_build_object('error', 'Sequence not found');
    END IF;

    -- Calculate unused ATP
    unused_atp := seq.atp_budget_reserved - seq.atp_consumed;
    resource_committed := COALESCE(seq.atp_committed, 0);

    -- Minimum retention: Even on full refund, retain minimum % of consumed ATP
    -- This prevents free resource consumption
    min_retention := CEIL((seq.atp_consumed * COALESCE(seq.min_retention_ratio, 0.50))::NUMERIC);

    -- Calculate base refund based on policy
    IF seq.atp_refund_policy = 'FULL' THEN
        -- FULL policy now respects minimum retention
        -- Refund = unused - committed resources - minimum retention
        refund_amount := GREATEST(0, unused_atp - resource_committed);

        -- Additional constraint: Never refund more than allows minimum retention
        IF (seq.atp_consumed - min_retention) < 0 THEN
            refund_amount := GREATEST(0, refund_amount - ABS(seq.atp_consumed - min_retention));
        END IF;

    ELSIF seq.atp_refund_policy = 'TIERED' THEN
        IF p_success THEN
            -- Success: Refund unused minus committed resources
            refund_amount := GREATEST(0, unused_atp - resource_committed);
        ELSE
            -- Failure: Partial refund based on completion ratio
            completion_ratio := seq.iterations_used::NUMERIC / NULLIF(seq.max_iterations, 1);
            refund_amount := FLOOR(unused_atp * (1.0 - completion_ratio));

            -- Subtract committed resources
            refund_amount := GREATEST(0, refund_amount - resource_committed);
        END IF;
    ELSE
        -- NONE policy: No refund
        refund_amount := 0;
    END IF;

    -- Check refund limits to prevent abuse
    SELECT * INTO refund_limit_check
    FROM atp_refund_limits
    WHERE lct_id = seq.actor_lct
      AND organization_id = seq.organization_id;

    IF refund_limit_check IS NOT NULL THEN
        -- Reset window if expired
        IF (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - refund_limit_check.window_start)) / 3600) > refund_limit_check.window_duration_hours THEN
            UPDATE atp_refund_limits
            SET window_start = CURRENT_TIMESTAMP,
                total_refunds_received = 0,
                refund_count = 0
            WHERE lct_id = seq.actor_lct AND organization_id = seq.organization_id;

            refund_limit_check.total_refunds_received := 0;
            refund_limit_check.refund_count := 0;
        END IF;

        -- Check if refund would exceed limits
        IF refund_limit_check.refund_count >= refund_limit_check.max_refunds_per_window THEN
            -- Refund limit exceeded - no refund
            effective_refund := 0;

            UPDATE atp_refund_limits
            SET refund_abuse_detected = TRUE
            WHERE lct_id = seq.actor_lct AND organization_id = seq.organization_id;

        ELSIF (refund_limit_check.total_refunds_received + refund_amount) > refund_limit_check.max_total_refund_per_window THEN
            -- Would exceed total refund limit - cap refund
            effective_refund := GREATEST(0, refund_limit_check.max_total_refund_per_window - refund_limit_check.total_refunds_received);
        ELSE
            effective_refund := refund_amount;
        END IF;

        -- Update refund limits
        UPDATE atp_refund_limits
        SET total_refunds_received = total_refunds_received + effective_refund,
            refund_count = refund_count + 1,
            last_refund_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE lct_id = seq.actor_lct AND organization_id = seq.organization_id;
    ELSE
        -- No existing limit record - create one
        INSERT INTO atp_refund_limits (lct_id, organization_id, total_refunds_received, refund_count, last_refund_at)
        VALUES (seq.actor_lct, seq.organization_id, refund_amount, 1, CURRENT_TIMESTAMP);

        effective_refund := refund_amount;
    END IF;

    -- Update sequence status
    UPDATE action_sequences
    SET status = CASE WHEN p_success THEN 'converged' ELSE 'failed' END,
        completed_at = CURRENT_TIMESTAMP,
        convergence_achieved = p_success
    WHERE sequence_id = p_sequence_id;

    -- Return detailed refund breakdown
    RETURN jsonb_build_object(
        'sequence_id', p_sequence_id,
        'success', p_success,
        'atp_reserved', seq.atp_budget_reserved,
        'atp_consumed', seq.atp_consumed,
        'atp_committed', resource_committed,
        'unused_atp', unused_atp,
        'min_retention', min_retention,
        'calculated_refund', refund_amount,
        'refund_amount', effective_refund,
        'refund_limited', (effective_refund < refund_amount),
        'policy', seq.atp_refund_policy
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION finalize_sequence_v2 IS 'Session #62: ATP refund with resource consumption tracking and abuse prevention';

-- ============================================================================
-- Helper Function: Record Resource Consumption
-- ============================================================================

CREATE OR REPLACE FUNCTION record_resource_consumption(
    p_sequence_id VARCHAR(255),
    p_iteration INTEGER,
    p_resource_type VARCHAR(100),  -- cpu, memory, gpu, storage, network
    p_amount NUMERIC,              -- Amount of resource (e.g., 1.5 GB RAM, 100 CPU-seconds)
    p_cost_atp INTEGER             -- ATP cost of this resource consumption
) RETURNS BOOLEAN AS $$
DECLARE
    current_committed INTEGER;
BEGIN
    -- Add to resource consumption log
    UPDATE action_sequences
    SET resource_consumption_log = resource_consumption_log ||
        jsonb_build_array(jsonb_build_object(
            'iteration', p_iteration,
            'resource_type', p_resource_type,
            'amount', p_amount,
            'cost_atp', p_cost_atp,
            'timestamp', CURRENT_TIMESTAMP
        )),
        atp_committed = COALESCE(atp_committed, 0) + p_cost_atp
    WHERE sequence_id = p_sequence_id;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION record_resource_consumption IS 'Track actual resource consumption for non-refundable ATP calculation';

-- ============================================================================
-- View: Refund Abuse Detection
-- ============================================================================

CREATE OR REPLACE VIEW refund_abuse_candidates AS
SELECT
    lct_id,
    organization_id,
    refund_count,
    total_refunds_received,
    max_refunds_per_window,
    max_total_refund_per_window,
    (refund_count::FLOAT / NULLIF(max_refunds_per_window, 0)) AS refund_count_ratio,
    (total_refunds_received::FLOAT / NULLIF(max_total_refund_per_window, 0)) AS refund_total_ratio,
    window_start,
    last_refund_at,
    refund_abuse_detected
FROM atp_refund_limits
WHERE refund_count > (max_refunds_per_window * 0.8)  -- Over 80% of limit
   OR total_refunds_received > (max_total_refund_per_window * 0.8)
   OR refund_abuse_detected = TRUE
ORDER BY refund_count DESC, total_refunds_received DESC;

COMMENT ON VIEW refund_abuse_candidates IS 'Identify LCTs approaching or exceeding refund limits';

-- ============================================================================
-- Example Usage
-- ============================================================================

/*
-- Track resource consumption during execution:
SELECT record_resource_consumption(
    'seq:irp:vision:001',
    iteration := 1,
    resource_type := 'gpu',
    amount := 2.5,  -- 2.5 GPU-seconds
    cost_atp := 15  -- 15 ATP non-refundable
);

-- Finalize sequence with resource-aware refunds:
SELECT finalize_sequence_v2('seq:irp:vision:001', success := FALSE);

-- Result might be:
{
    "sequence_id": "seq:irp:vision:001",
    "success": false,
    "atp_reserved": 100,
    "atp_consumed": 25,
    "atp_committed": 15,  -- GPU usage
    "unused_atp": 75,
    "min_retention": 13,  -- 50% of 25 consumed
    "calculated_refund": 60,  -- 75 unused - 15 committed
    "refund_amount": 60,
    "refund_limited": false,
    "policy": "FULL"
}

-- With FULL policy, attacker only gets 60 ATP back, not 75
-- 15 ATP retained for GPU resources consumed
*/
