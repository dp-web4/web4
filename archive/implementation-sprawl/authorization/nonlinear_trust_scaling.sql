-- Nonlinear Trust Score Scaling Functions
-- Session #60: P2 Security Fix for Score Clamping Exploitation

-- Function to scale trust delta based on current score
-- Implements "the higher you are, the harder you fall" principle
CREATE OR REPLACE FUNCTION scale_trust_delta(
    current_score NUMERIC,
    raw_delta NUMERIC
) RETURNS NUMERIC AS $$
DECLARE
    scaled_delta NUMERIC;
    scaling_factor NUMERIC;
BEGIN
    -- For positive deltas (rewards), no scaling
    IF raw_delta >= 0 THEN
        RETURN raw_delta;
    END IF;

    -- For negative deltas (penalties), scale by current trust level
    -- scaling_factor ranges from 1.0 (at score=0.0) to 10.0 (at score=1.0)
    -- Formula: 1.0 + (current_score^2) * 9.0
    scaling_factor := 1.0 + (current_score * current_score) * 9.0;

    -- Apply scaling to penalty
    scaled_delta := raw_delta * scaling_factor;

    RETURN scaled_delta;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to apply scaled delta with clamping
CREATE OR REPLACE FUNCTION apply_scaled_trust_delta(
    current_score NUMERIC,
    raw_delta NUMERIC
) RETURNS NUMERIC AS $$
DECLARE
    scaled_delta NUMERIC;
    new_score NUMERIC;
BEGIN
    -- Get scaled delta
    scaled_delta := scale_trust_delta(current_score, raw_delta);

    -- Apply delta and clamp to [0, 1]
    new_score := current_score + scaled_delta;
    new_score := LEAST(1.0, GREATEST(0.0, new_score));

    RETURN new_score;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Example usage:
-- Instead of: SET score = LEAST(1.0, GREATEST(0.0, score + delta))
-- Use:        SET score = apply_scaled_trust_delta(score, delta)

-- Test cases:
-- Score at 1.0, penalty -0.001:
--   scaling_factor = 1.0 + (1.0^2) * 9.0 = 10.0
--   scaled_delta = -0.001 * 10.0 = -0.01
--   new_score = 1.0 + (-0.01) = 0.99 (10x penalty at max trust)

-- Score at 0.5, penalty -0.001:
--   scaling_factor = 1.0 + (0.5^2) * 9.0 = 1.0 + 0.25 * 9.0 = 3.25
--   scaled_delta = -0.001 * 3.25 = -0.00325
--   new_score = 0.5 + (-0.00325) = 0.49675 (3.25x penalty at mid trust)

-- Score at 0.1, penalty -0.001:
--   scaling_factor = 1.0 + (0.1^2) * 9.0 = 1.0 + 0.01 * 9.0 = 1.09
--   scaled_delta = -0.001 * 1.09 = -0.00109
--   new_score = 0.1 + (-0.00109) = 0.09891 (minimal scaling at low trust)

-- Score at 0.0, penalty -0.001:
--   scaling_factor = 1.0 + (0.0^2) * 9.0 = 1.0
--   scaled_delta = -0.001 * 1.0 = -0.001
--   new_score = 0.0 + (-0.001) = 0.0 (clamped, can't go below 0)

-- Comments:
COMMENT ON FUNCTION scale_trust_delta IS 'Scales trust delta based on current score. Penalties scale quadratically with trust level (1x at 0.0, 10x at 1.0). Rewards are linear (no scaling).';
COMMENT ON FUNCTION apply_scaled_trust_delta IS 'Applies scaled trust delta with [0,1] clamping. Use this to update trust scores with nonlinear penalty scaling.';
