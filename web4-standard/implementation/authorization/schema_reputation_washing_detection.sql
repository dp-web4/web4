--
-- Reputation Washing Detection Schema
-- Session #63: P2 Security Enhancement
--
-- Implements anti-laundering analysis to detect suspicious reputation
-- transfer patterns that could indicate reputation washing attacks.
--
-- Attack Pattern (ATTACK_VECTORS.md line 281-321):
-- 1. Build high reputation on compromised/discarded identity
-- 2. Transfer reputation via trust relationships
-- 3. Discard old identity, use new identity with inherited trust
-- 4. Evade reputation-based penalties
--
-- Detection Approaches:
-- 1. Rapid reputation transfers (high trust change in short time)
-- 2. New identities receiving disproportionate trust
-- 3. Trust source diversity (single vs many sources)
-- 4. Temporal patterns (sudden spikes followed by identity discard)
--

-- ============================================================================
-- 1. Reputation Transfer Analysis View
-- ============================================================================

CREATE OR REPLACE VIEW reputation_transfer_analysis AS
WITH
-- Calculate trust change velocity (delta per day)
trust_velocity AS (
    SELECT
        lct_id,
        organization_id,
        t3_delta,
        v3_delta,
        recorded_at,
        LAG(recorded_at) OVER (PARTITION BY lct_id, organization_id ORDER BY recorded_at) as prev_recorded_at,
        -- Time between trust updates
        EXTRACT(EPOCH FROM (recorded_at - LAG(recorded_at) OVER (PARTITION BY lct_id, organization_id ORDER BY recorded_at))) / 86400.0 as days_since_last,
        -- Velocity = delta / time
        CASE
            WHEN EXTRACT(EPOCH FROM (recorded_at - LAG(recorded_at) OVER (PARTITION BY lct_id, organization_id ORDER BY recorded_at))) > 0
            THEN (t3_delta + v3_delta) / (EXTRACT(EPOCH FROM (recorded_at - LAG(recorded_at) OVER (PARTITION BY lct_id, organization_id ORDER BY recorded_at))) / 86400.0)
            ELSE 0
        END as trust_velocity_per_day
    FROM trust_history
    WHERE t3_delta IS NOT NULL OR v3_delta IS NOT NULL
),

-- Identify rapid trust accumulation (suspiciously fast reputation building)
rapid_accumulation AS (
    SELECT
        lct_id,
        organization_id,
        COUNT(*) as rapid_increases,
        SUM(t3_delta + v3_delta) as total_rapid_gain,
        MAX(trust_velocity_per_day) as max_velocity,
        MIN(recorded_at) as first_rapid_event,
        MAX(recorded_at) as last_rapid_event
    FROM trust_velocity
    WHERE trust_velocity_per_day > 0.5  -- Gaining >0.5 trust per day is suspicious
    GROUP BY lct_id, organization_id
),

-- Identify sudden large trust drops (potential abandonment)
sudden_drops AS (
    SELECT
        lct_id,
        organization_id,
        COUNT(*) as drop_count,
        SUM(t3_delta + v3_delta) as total_loss,
        MIN(recorded_at) as first_drop,
        MAX(recorded_at) as last_drop
    FROM trust_history
    WHERE (t3_delta + v3_delta) < -0.1  -- Large negative change
    GROUP BY lct_id, organization_id
)

SELECT
    ra.lct_id,
    ra.organization_id,
    ra.rapid_increases,
    ra.total_rapid_gain,
    ra.max_velocity,
    ra.first_rapid_event,
    ra.last_rapid_event,
    sd.drop_count,
    sd.total_loss,
    sd.first_drop,
    sd.last_drop,
    -- Washing risk score (0-10)
    LEAST(10, (
        CASE WHEN ra.rapid_increases > 10 THEN 3 ELSE 0 END +
        CASE WHEN ra.max_velocity > 1.0 THEN 3 ELSE 0 END +
        CASE WHEN sd.drop_count > 5 THEN 2 ELSE 0 END +
        CASE WHEN sd.total_loss < -0.5 THEN 2 ELSE 0 END
    )) as washing_risk_score
FROM rapid_accumulation ra
LEFT JOIN sudden_drops sd USING (lct_id, organization_id)
WHERE ra.rapid_increases > 5 OR sd.drop_count > 3
ORDER BY washing_risk_score DESC, ra.max_velocity DESC;

COMMENT ON VIEW reputation_transfer_analysis IS
'Detects suspicious reputation transfer patterns for anti-laundering analysis (Session #63)';

-- ============================================================================
-- 2. New Identity Trust Source Analysis
-- ============================================================================

CREATE OR REPLACE VIEW new_identity_trust_sources AS
WITH
-- Identify new identities (created within last 30 days)
new_identities AS (
    SELECT
        lct_id,
        created_at
    FROM lct_identities
    WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
),

-- Analyze their trust sources
trust_source_diversity AS (
    SELECT
        th.lct_id,
        th.organization_id,
        COUNT(DISTINCT th.event_id) as event_count,
        COUNT(DISTINCT DATE_TRUNC('day', th.recorded_at)) as active_days,
        MIN(th.recorded_at) as first_trust_event,
        MAX(th.recorded_at) as last_trust_event,
        SUM(th.t3_delta) as total_t3_gain,
        SUM(th.v3_delta) as total_v3_gain,
        AVG(th.t3_delta) as avg_t3_delta,
        AVG(th.v3_delta) as avg_v3_delta,
        -- Trust accumulation rate
        CASE
            WHEN MAX(th.recorded_at) != MIN(th.recorded_at)
            THEN (SUM(th.t3_delta) + SUM(th.v3_delta)) /
                 (EXTRACT(EPOCH FROM (MAX(th.recorded_at) - MIN(th.recorded_at))) / 86400.0)
            ELSE 0
        END as trust_gain_per_day
    FROM new_identities ni
    JOIN trust_history th ON th.lct_id = ni.lct_id
    WHERE th.t3_delta > 0 OR th.v3_delta > 0
    GROUP BY th.lct_id, th.organization_id
)

SELECT
    ni.lct_id,
    ni.created_at as identity_created_at,
    tsd.organization_id,
    tsd.event_count,
    tsd.active_days,
    tsd.first_trust_event,
    tsd.last_trust_event,
    tsd.total_t3_gain,
    tsd.total_v3_gain,
    tsd.avg_t3_delta,
    tsd.avg_v3_delta,
    tsd.trust_gain_per_day,
    -- Suspicious score (0-10)
    LEAST(10, (
        -- Very high trust gain rate
        CASE WHEN tsd.trust_gain_per_day > 0.5 THEN 4 ELSE 0 END +
        -- Large total gain for new identity
        CASE WHEN (tsd.total_t3_gain + tsd.total_v3_gain) > 1.0 THEN 3 ELSE 0 END +
        -- Few active days but high gain (burst activity)
        CASE WHEN tsd.active_days < 3 AND tsd.trust_gain_per_day > 0.3 THEN 3 ELSE 0 END
    )) as suspicious_score
FROM new_identities ni
JOIN trust_source_diversity tsd ON tsd.lct_id = ni.lct_id
WHERE tsd.trust_gain_per_day > 0.1 OR (tsd.total_t3_gain + tsd.total_v3_gain) > 0.5
ORDER BY suspicious_score DESC, tsd.trust_gain_per_day DESC;

COMMENT ON VIEW new_identity_trust_sources IS
'Identifies new identities with suspiciously rapid trust accumulation (Session #63)';

-- ============================================================================
-- 3. Identity Abandonment Detection
-- ============================================================================

CREATE OR REPLACE VIEW identity_abandonment_patterns AS
WITH
-- Recent trust activity per identity
recent_activity AS (
    SELECT
        lct_id,
        organization_id,
        MAX(recorded_at) as last_activity,
        COUNT(*) as total_events,
        SUM(CASE WHEN recorded_at > CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 ELSE 0 END) as events_last_7d,
        SUM(CASE WHEN recorded_at > CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 1 ELSE 0 END) as events_last_30d
    FROM trust_history
    GROUP BY lct_id, organization_id
),

-- Peak trust scores
peak_trust AS (
    SELECT
        lct_id,
        organization_id,
        MAX(t3_score) as peak_t3,
        MAX(v3_score) as peak_v3,
        MAX(t3_score + v3_score) as peak_total_trust
    FROM trust_history
    GROUP BY lct_id, organization_id
),

-- Current trust scores
current_trust AS (
    SELECT DISTINCT ON (lct_id, organization_id)
        lct_id,
        organization_id,
        t3_score as current_t3,
        v3_score as current_v3,
        recorded_at as score_date
    FROM trust_history
    ORDER BY lct_id, organization_id, recorded_at DESC
)

SELECT
    ra.lct_id,
    ra.organization_id,
    ra.last_activity,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ra.last_activity)) / 86400.0 as days_inactive,
    ra.total_events,
    ra.events_last_7d,
    ra.events_last_30d,
    pt.peak_total_trust,
    ct.current_t3 + ct.current_v3 as current_total_trust,
    pt.peak_total_trust - (ct.current_t3 + ct.current_v3) as trust_decline,
    -- Abandonment risk score (0-10)
    LEAST(10, (
        -- Inactive for >30 days
        CASE WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ra.last_activity)) / 86400.0 > 30 THEN 3 ELSE 0 END +
        -- Had high trust but declined
        CASE WHEN pt.peak_total_trust > 1.5 AND (pt.peak_total_trust - (ct.current_t3 + ct.current_v3)) > 0.5 THEN 4 ELSE 0 END +
        -- No recent activity
        CASE WHEN ra.events_last_30d = 0 THEN 3 ELSE 0 END
    )) as abandonment_risk_score
FROM recent_activity ra
JOIN peak_trust pt USING (lct_id, organization_id)
JOIN current_trust ct USING (lct_id, organization_id)
WHERE
    pt.peak_total_trust > 1.0  -- Only track identities that achieved significant trust
    AND EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ra.last_activity)) / 86400.0 > 7  -- Inactive >7 days
ORDER BY abandonment_risk_score DESC, trust_decline DESC;

COMMENT ON VIEW identity_abandonment_patterns IS
'Detects identities with high trust that have been abandoned (potential laundering source) (Session #63)';

-- ============================================================================
-- 4. Comprehensive Washing Detection View
-- ============================================================================

CREATE OR REPLACE VIEW reputation_washing_alerts AS
WITH
-- Combine all suspicious patterns
rapid_transfers AS (
    SELECT
        lct_id,
        organization_id,
        'RAPID_TRANSFER' as alert_type,
        washing_risk_score as score,
        'Rapid reputation accumulation and/or large drops detected' as description,
        first_rapid_event as first_event,
        last_rapid_event as last_event
    FROM reputation_transfer_analysis
    WHERE washing_risk_score >= 5
),

new_identity_alerts AS (
    SELECT
        lct_id,
        organization_id,
        'NEW_IDENTITY_SUSPICIOUS' as alert_type,
        suspicious_score as score,
        'New identity with suspiciously rapid trust gain' as description,
        first_trust_event as first_event,
        last_trust_event as last_event
    FROM new_identity_trust_sources
    WHERE suspicious_score >= 5
),

abandonment_alerts AS (
    SELECT
        lct_id,
        organization_id,
        'IDENTITY_ABANDONED' as alert_type,
        abandonment_risk_score as score,
        'High-trust identity abandoned after peak' as description,
        last_activity as first_event,
        CURRENT_TIMESTAMP as last_event
    FROM identity_abandonment_patterns
    WHERE abandonment_risk_score >= 5
)

SELECT * FROM rapid_transfers
UNION ALL
SELECT * FROM new_identity_alerts
UNION ALL
SELECT * FROM abandonment_alerts
ORDER BY score DESC, last_event DESC;

COMMENT ON VIEW reputation_washing_alerts IS
'Aggregates all reputation washing detection alerts for monitoring (Session #63)';

-- ============================================================================
-- 5. Statistics Function for Monitoring
-- ============================================================================

CREATE OR REPLACE FUNCTION get_reputation_washing_stats()
RETURNS TABLE (
    metric VARCHAR(100),
    value NUMERIC,
    threshold NUMERIC,
    status VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'Total Washing Alerts'::VARCHAR(100),
        COUNT(*)::NUMERIC,
        10::NUMERIC,
        CASE WHEN COUNT(*) > 10 THEN 'WARNING' ELSE 'OK' END::VARCHAR(20)
    FROM reputation_washing_alerts

    UNION ALL

    SELECT
        'High Risk Alerts (score >= 8)'::VARCHAR(100),
        COUNT(*)::NUMERIC,
        5::NUMERIC,
        CASE WHEN COUNT(*) > 5 THEN 'CRITICAL' ELSE 'OK' END::VARCHAR(20)
    FROM reputation_washing_alerts
    WHERE score >= 8

    UNION ALL

    SELECT
        'Rapid Transfer Patterns'::VARCHAR(100),
        COUNT(*)::NUMERIC,
        5::NUMERIC,
        CASE WHEN COUNT(*) > 5 THEN 'WARNING' ELSE 'OK' END::VARCHAR(20)
    FROM reputation_washing_alerts
    WHERE alert_type = 'RAPID_TRANSFER'

    UNION ALL

    SELECT
        'Suspicious New Identities'::VARCHAR(100),
        COUNT(*)::NUMERIC,
        5::NUMERIC,
        CASE WHEN COUNT(*) > 5 THEN 'WARNING' ELSE 'OK' END::VARCHAR(20)
    FROM reputation_washing_alerts
    WHERE alert_type = 'NEW_IDENTITY_SUSPICIOUS'

    UNION ALL

    SELECT
        'Abandoned High-Trust Identities'::VARCHAR(100),
        COUNT(*)::NUMERIC,
        3::NUMERIC,
        CASE WHEN COUNT(*) > 3 THEN 'WARNING' ELSE 'OK' END::VARCHAR(20)
    FROM reputation_washing_alerts
    WHERE alert_type = 'IDENTITY_ABANDONED';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_reputation_washing_stats IS
'Returns current reputation washing detection statistics for monitoring dashboards (Session #63)';

-- ============================================================================
-- 6. Audit Trigger for High-Risk Events
-- ============================================================================

-- Table to log reputation washing investigations
CREATE TABLE IF NOT EXISTS reputation_washing_investigations (
    investigation_id BIGSERIAL PRIMARY KEY,
    lct_id VARCHAR(255) NOT NULL,
    organization_id VARCHAR(255) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    alert_score NUMERIC(4, 2),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    investigated_at TIMESTAMP WITH TIME ZONE,
    investigator VARCHAR(255),
    findings TEXT,
    action_taken VARCHAR(50), -- no_action, warning_issued, identity_flagged, identity_suspended
    notes TEXT
);

CREATE INDEX idx_washing_investigations_lct ON reputation_washing_investigations(lct_id);
CREATE INDEX idx_washing_investigations_detected ON reputation_washing_investigations(detected_at DESC);
CREATE INDEX idx_washing_investigations_status ON reputation_washing_investigations(action_taken);

COMMENT ON TABLE reputation_washing_investigations IS
'Logs reputation washing alerts for investigation and action tracking (Session #63)';

-- ============================================================================
-- 7. Automated Alert Population (for new high-risk events)
-- ============================================================================

CREATE OR REPLACE FUNCTION auto_log_washing_alerts()
RETURNS TRIGGER AS $$
DECLARE
    alert_score NUMERIC;
    alert_type VARCHAR(100);
BEGIN
    -- Check if this trust update creates a high-risk pattern
    -- (Simplified - full implementation would analyze patterns)

    -- Rapid gain detection
    IF NEW.t3_delta > 0.3 OR NEW.v3_delta > 0.3 THEN
        alert_type := 'RAPID_GAIN_EVENT';
        alert_score := (NEW.t3_delta + NEW.v3_delta) * 10;

        INSERT INTO reputation_washing_investigations (
            lct_id,
            organization_id,
            alert_type,
            alert_score,
            notes
        ) VALUES (
            NEW.lct_id,
            NEW.organization_id,
            alert_type,
            alert_score,
            format('Large single trust gain detected: T3=%s, V3=%s', NEW.t3_delta, NEW.v3_delta)
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Optional: Enable automatic alert logging
-- CREATE TRIGGER trigger_washing_alert
-- AFTER INSERT ON trust_history
-- FOR EACH ROW
-- EXECUTE FUNCTION auto_log_washing_alerts();

COMMENT ON FUNCTION auto_log_washing_alerts IS
'Trigger function to automatically log high-risk trust events for investigation (Session #63)';
