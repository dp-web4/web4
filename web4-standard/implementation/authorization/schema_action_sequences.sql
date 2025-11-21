-- Web4 Action Sequence Protocol - Schema Extension
-- Session #54: Implementation of Session #53 Multi-Step Action Design
--
-- Extends the authorization schema to support multi-step actions for IRP:
-- 1. Action sequences with iteration budgets
-- 2. Checkpoints for resumability and witness verification
-- 3. ATP charging per iteration
-- 4. Convergence tracking and early stopping
-- 5. Failure refund policies
--
-- This implements the design from SAGE_INTEGRATION_ANSWERS.md (Q4-Q6)

-- ============================================================================
-- Action Sequences
-- ============================================================================

CREATE TABLE IF NOT EXISTS action_sequences (
    sequence_id VARCHAR(255) PRIMARY KEY,
    parent_action_id BIGINT, -- Reference to initial delegation_action if applicable

    -- Entity and delegation context
    actor_lct VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id),
    delegation_id VARCHAR(255) REFERENCES agent_delegations(delegation_id),
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(organization_id),

    -- Sequence specification
    sequence_type VARCHAR(100) NOT NULL, -- IRP_REFINEMENT, MULTI_STEP_TASK, COLLABORATIVE_WORKFLOW
    target_resource VARCHAR(500) NOT NULL,
    operation VARCHAR(100) NOT NULL, -- vision_encoding, causal_reasoning, etc.

    -- Iteration budget
    max_iterations INTEGER NOT NULL, -- Maximum iterations allowed
    current_iteration INTEGER DEFAULT 0, -- Current iteration number
    iteration_atp_cost INTEGER DEFAULT 1, -- ATP cost per iteration

    -- ATP management
    atp_budget_reserved INTEGER NOT NULL, -- Total ATP reserved upfront
    atp_consumed INTEGER DEFAULT 0, -- ATP consumed so far
    atp_refund_policy VARCHAR(50) DEFAULT 'TIERED', -- TIERED, NONE, FULL

    -- Convergence criteria
    convergence_target NUMERIC(6, 4), -- Energy target (e.g., 0.0500 for IRP)
    convergence_metric VARCHAR(50), -- energy, loss, error, delta
    early_stopping_enabled BOOLEAN DEFAULT TRUE,
    early_stopping_threshold NUMERIC(6, 4),

    -- Status tracking
    status VARCHAR(50) DEFAULT 'active', -- active, converged, failed, timeout, cancelled
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    failure_reason TEXT,

    -- Results
    final_energy NUMERIC(6, 4), -- Final convergence value
    convergence_achieved BOOLEAN DEFAULT FALSE,
    iterations_used INTEGER DEFAULT 0,

    -- Metadata
    sequence_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_iterations CHECK (current_iteration <= max_iterations),
    CONSTRAINT chk_atp_consumed CHECK (atp_consumed <= atp_budget_reserved)
);

CREATE INDEX idx_seq_actor ON action_sequences(actor_lct);
CREATE INDEX idx_seq_delegation ON action_sequences(delegation_id);
CREATE INDEX idx_seq_org ON action_sequences(organization_id);
CREATE INDEX idx_seq_status ON action_sequences(status);
CREATE INDEX idx_seq_type ON action_sequences(sequence_type);
CREATE INDEX idx_seq_started ON action_sequences(started_at);

COMMENT ON TABLE action_sequences IS 'Multi-step action sequences for iterative refinement (IRP) and complex workflows';
COMMENT ON COLUMN action_sequences.atp_budget_reserved IS 'ATP reserved upfront, charged incrementally, refunded on completion';
COMMENT ON COLUMN action_sequences.convergence_target IS 'Target value for convergence metric (e.g., energy < 0.05)';
COMMENT ON COLUMN action_sequences.atp_refund_policy IS 'TIERED (partial based on completion), NONE (no refund), FULL (refund unused)';

-- ============================================================================
-- Action Checkpoints
-- ============================================================================

CREATE TABLE IF NOT EXISTS action_checkpoints (
    checkpoint_id BIGSERIAL PRIMARY KEY,
    sequence_id VARCHAR(255) NOT NULL REFERENCES action_sequences(sequence_id) ON DELETE CASCADE,

    -- Checkpoint location
    iteration_number INTEGER NOT NULL,
    step_name VARCHAR(255), -- Optional step name

    -- State snapshot
    state_hash VARCHAR(66), -- SHA256 of state at this checkpoint
    energy_value NUMERIC(6, 4), -- Current convergence metric value
    delta_from_previous NUMERIC(6, 4), -- Improvement since last checkpoint

    -- Witness verification
    witnessed_by JSONB DEFAULT '[]'::jsonb, -- Array of {lct_id, signature, verified_at}
    witness_count INTEGER DEFAULT 0,
    verification_status VARCHAR(50) DEFAULT 'unverified', -- unverified, pending, verified, disputed

    -- ATP accounting at checkpoint
    atp_consumed_cumulative INTEGER,
    atp_consumed_this_step INTEGER,

    -- Performance metrics
    computation_time_ms INTEGER,
    memory_usage_mb INTEGER,

    -- Checkpoint data (optional, can be large)
    state_data JSONB, -- Optional state snapshot for resumability
    output_preview TEXT, -- Human-readable preview of output

    -- Metadata
    checkpoint_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (sequence_id, iteration_number)
);

CREATE INDEX idx_checkpoint_sequence ON action_checkpoints(sequence_id);
CREATE INDEX idx_checkpoint_iteration ON action_checkpoints(sequence_id, iteration_number);
CREATE INDEX idx_checkpoint_verified ON action_checkpoints(verification_status);
CREATE INDEX idx_checkpoint_energy ON action_checkpoints(energy_value);

COMMENT ON TABLE action_checkpoints IS 'Checkpoints within action sequences for witness verification and resumability';
COMMENT ON COLUMN action_checkpoints.state_hash IS 'SHA256 hash of state for witness verification without full state';
COMMENT ON COLUMN action_checkpoints.witnessed_by IS 'JSONB array of witnesses who verified this checkpoint';

-- ============================================================================
-- Sequence Steps (optional, for predefined multi-step workflows)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sequence_step_definitions (
    step_definition_id BIGSERIAL PRIMARY KEY,
    sequence_type VARCHAR(100) NOT NULL, -- Must match action_sequences.sequence_type

    -- Step specification
    step_order INTEGER NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    step_description TEXT,

    -- Step requirements
    required_capability VARCHAR(255), -- From ai_capabilities table
    estimated_atp_cost INTEGER DEFAULT 1,
    estimated_duration_seconds INTEGER,

    -- Checkpoint configuration
    checkpoint_required BOOLEAN DEFAULT FALSE,
    witness_required BOOLEAN DEFAULT FALSE,
    min_witnesses INTEGER DEFAULT 0,

    -- Metadata
    step_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (sequence_type, step_order),
    UNIQUE (sequence_type, step_name)
);

CREATE INDEX idx_step_def_type ON sequence_step_definitions(sequence_type);
CREATE INDEX idx_step_def_order ON sequence_step_definitions(sequence_type, step_order);

COMMENT ON TABLE sequence_step_definitions IS 'Predefined step templates for multi-step workflows';

-- ============================================================================
-- Views
-- ============================================================================

-- Active sequences with progress
CREATE OR REPLACE VIEW active_sequences AS
SELECT
    seq.sequence_id,
    seq.actor_lct,
    seq.sequence_type,
    seq.operation,
    seq.current_iteration,
    seq.max_iterations,
    (seq.current_iteration::FLOAT / NULLIF(seq.max_iterations, 0)) AS progress_ratio,
    seq.atp_budget_reserved,
    seq.atp_consumed,
    (seq.atp_budget_reserved - seq.atp_consumed) AS atp_remaining,
    seq.convergence_target,
    seq.final_energy,
    seq.status,
    seq.started_at,
    (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - seq.started_at)))::INTEGER AS runtime_seconds,
    (
        SELECT COUNT(*)
        FROM action_checkpoints cp
        WHERE cp.sequence_id = seq.sequence_id
    ) AS checkpoint_count,
    (
        SELECT COUNT(*)
        FROM action_checkpoints cp
        WHERE cp.sequence_id = seq.sequence_id AND cp.verification_status = 'verified'
    ) AS verified_checkpoint_count
FROM action_sequences seq
WHERE seq.status = 'active';

COMMENT ON VIEW active_sequences IS 'Active action sequences with progress and ATP tracking';

-- Checkpoint summary per sequence
CREATE OR REPLACE VIEW sequence_checkpoint_summary AS
SELECT
    seq.sequence_id,
    seq.actor_lct,
    seq.sequence_type,
    seq.status,
    COUNT(cp.checkpoint_id) AS total_checkpoints,
    COUNT(cp.checkpoint_id) FILTER (WHERE cp.verification_status = 'verified') AS verified_checkpoints,
    COUNT(cp.checkpoint_id) FILTER (WHERE cp.verification_status = 'disputed') AS disputed_checkpoints,
    MIN(cp.energy_value) AS best_energy,
    MAX(cp.energy_value) AS worst_energy,
    AVG(cp.energy_value) AS avg_energy,
    SUM(cp.atp_consumed_this_step) AS total_atp_consumed,
    AVG(cp.computation_time_ms) AS avg_computation_time_ms
FROM action_sequences seq
LEFT JOIN action_checkpoints cp ON seq.sequence_id = cp.sequence_id
GROUP BY seq.sequence_id, seq.actor_lct, seq.sequence_type, seq.status;

COMMENT ON VIEW sequence_checkpoint_summary IS 'Aggregated checkpoint statistics per sequence';

-- ============================================================================
-- Functions
-- ============================================================================

-- Record iteration and charge ATP
CREATE OR REPLACE FUNCTION record_sequence_iteration(
    p_sequence_id VARCHAR(255),
    p_energy_value NUMERIC(6, 4),
    p_state_hash VARCHAR(66),
    p_atp_cost INTEGER
) RETURNS JSONB AS $$
DECLARE
    seq RECORD;
    checkpoint_id BIGINT;
    should_checkpoint BOOLEAN;
    result JSONB;
BEGIN
    -- Get sequence
    SELECT * INTO seq FROM action_sequences WHERE sequence_id = p_sequence_id FOR UPDATE;

    IF seq IS NULL THEN
        RETURN jsonb_build_object('error', 'Sequence not found');
    END IF;

    -- Check if can continue
    IF seq.current_iteration >= seq.max_iterations THEN
        UPDATE action_sequences
        SET status = 'timeout',
            completed_at = CURRENT_TIMESTAMP,
            failure_reason = 'Maximum iterations reached'
        WHERE sequence_id = p_sequence_id;

        RETURN jsonb_build_object('status', 'timeout', 'reason', 'max_iterations');
    END IF;

    -- Check ATP budget
    IF seq.atp_consumed + p_atp_cost > seq.atp_budget_reserved THEN
        UPDATE action_sequences
        SET status = 'failed',
            completed_at = CURRENT_TIMESTAMP,
            failure_reason = 'ATP budget exhausted'
        WHERE sequence_id = p_sequence_id;

        RETURN jsonb_build_object('status', 'failed', 'reason', 'atp_budget_exhausted');
    END IF;

    -- Increment iteration
    UPDATE action_sequences
    SET current_iteration = current_iteration + 1,
        atp_consumed = atp_consumed + p_atp_cost,
        final_energy = p_energy_value,
        iterations_used = iterations_used + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE sequence_id = p_sequence_id;

    -- Determine if should checkpoint (every 3 iterations or if converged)
    should_checkpoint := (seq.current_iteration + 1) % 3 = 0 OR
                        (seq.early_stopping_enabled AND p_energy_value < seq.convergence_target);

    IF should_checkpoint THEN
        INSERT INTO action_checkpoints (
            sequence_id, iteration_number, state_hash, energy_value,
            atp_consumed_cumulative, atp_consumed_this_step
        ) VALUES (
            p_sequence_id, seq.current_iteration + 1, p_state_hash, p_energy_value,
            seq.atp_consumed + p_atp_cost, p_atp_cost
        ) RETURNING action_checkpoints.checkpoint_id INTO checkpoint_id;
    END IF;

    -- Check for convergence
    IF seq.early_stopping_enabled AND p_energy_value < seq.convergence_target THEN
        UPDATE action_sequences
        SET status = 'converged',
            convergence_achieved = TRUE,
            completed_at = CURRENT_TIMESTAMP
        WHERE sequence_id = p_sequence_id;

        RETURN jsonb_build_object(
            'status', 'converged',
            'iteration', seq.current_iteration + 1,
            'energy', p_energy_value,
            'checkpoint_id', checkpoint_id
        );
    END IF;

    -- Return continue status
    RETURN jsonb_build_object(
        'status', 'continue',
        'iteration', seq.current_iteration + 1,
        'energy', p_energy_value,
        'checkpointed', should_checkpoint,
        'checkpoint_id', checkpoint_id
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION record_sequence_iteration IS 'Record iteration progress and charge ATP incrementally';

-- Finalize sequence and calculate refund
CREATE OR REPLACE FUNCTION finalize_sequence(
    p_sequence_id VARCHAR(255),
    p_success BOOLEAN
) RETURNS JSONB AS $$
DECLARE
    seq RECORD;
    refund_amount INTEGER;
    unused_atp INTEGER;
    completion_ratio NUMERIC;
BEGIN
    -- Get sequence
    SELECT * INTO seq FROM action_sequences WHERE sequence_id = p_sequence_id FOR UPDATE;

    IF seq IS NULL THEN
        RETURN jsonb_build_object('error', 'Sequence not found');
    END IF;

    unused_atp := seq.atp_budget_reserved - seq.atp_consumed;

    -- Calculate refund based on policy
    IF seq.atp_refund_policy = 'FULL' THEN
        refund_amount := unused_atp;
    ELSIF seq.atp_refund_policy = 'TIERED' THEN
        IF p_success THEN
            refund_amount := unused_atp; -- Full refund on success
        ELSE
            completion_ratio := seq.iterations_used::NUMERIC / NULLIF(seq.max_iterations, 1);
            refund_amount := FLOOR(unused_atp * (1.0 - completion_ratio)); -- Partial refund
        END IF;
    ELSE
        refund_amount := 0; -- NONE policy
    END IF;

    -- Update sequence status
    UPDATE action_sequences
    SET status = CASE WHEN p_success THEN 'converged' ELSE 'failed' END,
        completed_at = CURRENT_TIMESTAMP,
        convergence_achieved = p_success
    WHERE sequence_id = p_sequence_id;

    -- Return refund details
    RETURN jsonb_build_object(
        'sequence_id', p_sequence_id,
        'success', p_success,
        'atp_consumed', seq.atp_consumed,
        'atp_reserved', seq.atp_budget_reserved,
        'unused_atp', unused_atp,
        'refund_amount', refund_amount,
        'refund_policy', seq.atp_refund_policy,
        'iterations_used', seq.iterations_used,
        'max_iterations', seq.max_iterations
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION finalize_sequence IS 'Finalize action sequence and calculate ATP refund based on policy';

-- ============================================================================
-- Triggers
-- ============================================================================

CREATE TRIGGER update_action_sequences_updated_at BEFORE UPDATE ON action_sequences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample Sequence Types
-- ============================================================================

-- IRP (Iterative Refinement Process) step definitions
INSERT INTO sequence_step_definitions (sequence_type, step_order, step_name, step_description, checkpoint_required)
VALUES
    ('IRP_REFINEMENT', 1, 'initial_encoding', 'Encode input into latent representation', FALSE),
    ('IRP_REFINEMENT', 2, 'iterative_refinement', 'Refine representation to minimize energy', TRUE),
    ('IRP_REFINEMENT', 3, 'convergence_check', 'Check if energy target achieved', TRUE),
    ('IRP_REFINEMENT', 4, 'output_decoding', 'Decode final representation to output', FALSE)
ON CONFLICT (sequence_type, step_order) DO NOTHING;

COMMENT ON TABLE action_sequences IS 'Implements multi-step action protocol from Session #53 for SAGE IRP integration';
