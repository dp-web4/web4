-- Web4 Authorization System - PostgreSQL Schema
-- Session #52: Persistent Storage for Permissions and Delegations
--
-- This schema supports:
-- 1. Permission claims with cryptographic signatures
-- 2. Agent delegations with ATP budgets and constraints
-- 3. Delegation chains (sub-delegation tracking)
-- 4. Revocation history with audit trails
-- 5. LCT identity integration
-- 6. Cross-organization permissions

-- ============================================================================
-- Core Tables
-- ============================================================================

-- LCT Identities (read-only view of identity system)
CREATE TABLE IF NOT EXISTS lct_identities (
    lct_id VARCHAR(255) PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, -- HUMAN, AI, SOCIETY, ROLE
    society_id VARCHAR(255),
    birth_certificate_hash VARCHAR(66) NOT NULL, -- SHA256 hex
    public_key TEXT NOT NULL, -- Ed25519 public key (hex or base64)
    hardware_binding_hash VARCHAR(66), -- Optional hardware binding
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lct_society ON lct_identities(society_id);
CREATE INDEX idx_lct_entity_type ON lct_identities(entity_type);

-- Organizations (societies, companies, DAOs)
CREATE TABLE IF NOT EXISTS organizations (
    organization_id VARCHAR(255) PRIMARY KEY,
    organization_name VARCHAR(255) NOT NULL,
    parent_organization_id VARCHAR(255) REFERENCES organizations(organization_id),
    admin_lct_id VARCHAR(255) REFERENCES lct_identities(lct_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_org_parent ON organizations(parent_organization_id);

-- Permission Claims
CREATE TABLE IF NOT EXISTS permission_claims (
    claim_hash VARCHAR(66) PRIMARY KEY, -- SHA256 of claim content
    claim_id VARCHAR(255) UNIQUE NOT NULL, -- Human-readable ID
    subject_lct VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id),
    issuer_lct VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id),
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(organization_id),

    -- Permission specification
    permission_action VARCHAR(100) NOT NULL, -- read, write, execute, delete, admin
    resource_pattern VARCHAR(500) NOT NULL, -- e.g., "code:*", "data:project123:*"
    resource_scope VARCHAR(500), -- Optional additional scope

    -- Signature and proof
    signature TEXT NOT NULL, -- Ed25519 signature (hex)
    witness_signatures JSONB DEFAULT '[]'::jsonb, -- Array of {lct_id, signature}

    -- Status and lifecycle
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, revoked, expired
    issued_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revocation_reason TEXT,

    -- Metadata
    description TEXT,
    conditions JSONB DEFAULT '{}'::jsonb, -- Conditions like min_t3, required_roles
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_claim_subject ON permission_claims(subject_lct);
CREATE INDEX idx_claim_issuer ON permission_claims(issuer_lct);
CREATE INDEX idx_claim_org ON permission_claims(organization_id);
CREATE INDEX idx_claim_status ON permission_claims(status);
CREATE INDEX idx_claim_resource ON permission_claims(resource_pattern);
CREATE INDEX idx_claim_expires ON permission_claims(expires_at) WHERE expires_at IS NOT NULL;

-- Agent Delegations
CREATE TABLE IF NOT EXISTS agent_delegations (
    delegation_id VARCHAR(255) PRIMARY KEY,

    -- Delegation chain (who delegates to whom)
    delegator_lct VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id), -- Client/Principal
    delegatee_lct VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id), -- Agent
    parent_delegation_id VARCHAR(255) REFERENCES agent_delegations(delegation_id), -- For sub-delegation

    -- Role and organization context
    role_lct VARCHAR(255) REFERENCES lct_identities(lct_id), -- Optional role identity
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(organization_id),

    -- Granted permissions (references to permission_claims)
    granted_claim_hashes JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of claim_hash references

    -- ATP Budget Management
    atp_budget_total INTEGER NOT NULL, -- Total ATP allocated
    atp_budget_spent INTEGER NOT NULL DEFAULT 0, -- ATP consumed so far
    atp_cost_per_action INTEGER DEFAULT 1, -- Default cost if not specified

    -- Rate Limiting
    max_actions_per_hour INTEGER DEFAULT 100,
    actions_this_hour INTEGER DEFAULT 0,
    last_hour_reset TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Time Constraints
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, suspended, revoked, expired
    revoked_at TIMESTAMP WITH TIME ZONE,
    revocation_reason TEXT,

    -- Signature proof
    delegation_signature TEXT NOT NULL, -- Delegator's signature
    witness_signatures JSONB DEFAULT '[]'::jsonb, -- Required witnesses

    -- Metadata and constraints
    description TEXT,
    constraints JSONB DEFAULT '{}'::jsonb, -- Additional constraints (e.g., resource limits)
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_atp_budget CHECK (atp_budget_spent <= atp_budget_total),
    CONSTRAINT chk_valid_timerange CHECK (valid_until > valid_from),
    CONSTRAINT chk_no_self_delegation CHECK (delegator_lct != delegatee_lct)
);

CREATE INDEX idx_delegation_delegator ON agent_delegations(delegator_lct);
CREATE INDEX idx_delegation_delegatee ON agent_delegations(delegatee_lct);
CREATE INDEX idx_delegation_parent ON agent_delegations(parent_delegation_id);
CREATE INDEX idx_delegation_org ON agent_delegations(organization_id);
CREATE INDEX idx_delegation_status ON agent_delegations(status);
CREATE INDEX idx_delegation_expires ON agent_delegations(valid_until);

-- Delegation Actions (audit trail)
CREATE TABLE IF NOT EXISTS delegation_actions (
    action_id BIGSERIAL PRIMARY KEY,
    delegation_id VARCHAR(255) NOT NULL REFERENCES agent_delegations(delegation_id),
    delegatee_lct VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id),

    -- Action details
    action_type VARCHAR(100) NOT NULL, -- R6 action type or custom
    target_resource VARCHAR(500) NOT NULL,
    atp_cost INTEGER NOT NULL DEFAULT 1,

    -- Authorization result
    authorized BOOLEAN NOT NULL,
    denial_reason VARCHAR(255),

    -- Context
    request_context JSONB DEFAULT '{}'::jsonb,
    result_metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamp
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_action_delegation ON delegation_actions(delegation_id);
CREATE INDEX idx_action_delegatee ON delegation_actions(delegatee_lct);
CREATE INDEX idx_action_timestamp ON delegation_actions(executed_at);
CREATE INDEX idx_action_authorized ON delegation_actions(authorized);

-- Reputation Scores (T3 trust tensor)
CREATE TABLE IF NOT EXISTS reputation_scores (
    lct_id VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id),
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(organization_id),

    -- T3 components (Talent, Training, Temperament)
    talent_score NUMERIC(4, 3) DEFAULT 0.0 CHECK (talent_score >= 0.0 AND talent_score <= 1.0),
    training_score NUMERIC(4, 3) DEFAULT 0.0 CHECK (training_score >= 0.0 AND training_score <= 1.0),
    temperament_score NUMERIC(4, 3) DEFAULT 0.0 CHECK (temperament_score >= 0.0 AND temperament_score <= 1.0),

    -- Aggregated T3
    t3_score NUMERIC(4, 3) GENERATED ALWAYS AS (
        (talent_score * 0.3 + training_score * 0.4 + temperament_score * 0.3)
    ) STORED,

    -- Reputation level derived from T3
    reputation_level VARCHAR(50) GENERATED ALWAYS AS (
        CASE
            WHEN (talent_score * 0.3 + training_score * 0.4 + temperament_score * 0.3) < 0.3 THEN 'novice'
            WHEN (talent_score * 0.3 + training_score * 0.4 + temperament_score * 0.3) < 0.5 THEN 'developing'
            WHEN (talent_score * 0.3 + training_score * 0.4 + temperament_score * 0.3) < 0.7 THEN 'trusted'
            WHEN (talent_score * 0.3 + training_score * 0.4 + temperament_score * 0.3) < 0.9 THEN 'expert'
            ELSE 'master'
        END
    ) STORED,

    -- Statistics
    total_actions INTEGER DEFAULT 0,
    successful_actions INTEGER DEFAULT 0,
    failed_actions INTEGER DEFAULT 0,

    -- Timestamps
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (lct_id, organization_id)
);

CREATE INDEX idx_reputation_lct ON reputation_scores(lct_id);
CREATE INDEX idx_reputation_org ON reputation_scores(organization_id);
CREATE INDEX idx_reputation_t3 ON reputation_scores(t3_score DESC);
CREATE INDEX idx_reputation_level ON reputation_scores(reputation_level);

-- Revocation Events (immutable audit log)
CREATE TABLE IF NOT EXISTS revocation_events (
    event_id BIGSERIAL PRIMARY KEY,
    target_type VARCHAR(50) NOT NULL, -- 'permission_claim' or 'delegation'
    target_id VARCHAR(255) NOT NULL, -- claim_hash or delegation_id

    -- Revocation details
    revoker_lct VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id),
    revocation_reason TEXT NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Context
    triggered_by VARCHAR(100), -- 'manual', 'trust_drop', 'expiration', 'violation'
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_revocation_target ON revocation_events(target_type, target_id);
CREATE INDEX idx_revocation_revoker ON revocation_events(revoker_lct);
CREATE INDEX idx_revocation_timestamp ON revocation_events(revoked_at);

-- ============================================================================
-- Views
-- ============================================================================

-- Active Permissions View (only active, non-expired claims)
CREATE OR REPLACE VIEW active_permissions AS
SELECT
    pc.*,
    rs.t3_score,
    rs.reputation_level,
    o.organization_name
FROM permission_claims pc
JOIN reputation_scores rs ON pc.subject_lct = rs.lct_id AND pc.organization_id = rs.organization_id
JOIN organizations o ON pc.organization_id = o.organization_id
WHERE pc.status = 'active'
  AND (pc.expires_at IS NULL OR pc.expires_at > CURRENT_TIMESTAMP);

-- Active Delegations View
CREATE OR REPLACE VIEW active_delegations AS
SELECT
    ad.*,
    rs.t3_score AS delegatee_t3,
    rs.reputation_level AS delegatee_reputation,
    (ad.atp_budget_total - ad.atp_budget_spent) AS atp_remaining,
    (ad.atp_budget_spent::FLOAT / NULLIF(ad.atp_budget_total, 0)) AS atp_utilization,
    o.organization_name
FROM agent_delegations ad
JOIN reputation_scores rs ON ad.delegatee_lct = rs.lct_id AND ad.organization_id = rs.organization_id
JOIN organizations o ON ad.organization_id = o.organization_id
WHERE ad.status = 'active'
  AND ad.valid_from <= CURRENT_TIMESTAMP
  AND ad.valid_until > CURRENT_TIMESTAMP;

-- Delegation Chains View (recursive, shows full chain)
CREATE OR REPLACE VIEW delegation_chains AS
WITH RECURSIVE chain AS (
    -- Base case: top-level delegations
    SELECT
        delegation_id,
        delegator_lct,
        delegatee_lct,
        parent_delegation_id,
        1 AS depth,
        ARRAY[delegation_id] AS chain_path,
        delegator_lct AS root_delegator
    FROM agent_delegations
    WHERE parent_delegation_id IS NULL

    UNION ALL

    -- Recursive case: sub-delegations
    SELECT
        ad.delegation_id,
        ad.delegator_lct,
        ad.delegatee_lct,
        ad.parent_delegation_id,
        c.depth + 1,
        c.chain_path || ad.delegation_id,
        c.root_delegator
    FROM agent_delegations ad
    JOIN chain c ON ad.parent_delegation_id = c.delegation_id
    WHERE c.depth < 10 -- Prevent infinite loops, max 10 levels
)
SELECT * FROM chain;

-- ============================================================================
-- Functions
-- ============================================================================

-- Update reputation score based on action
CREATE OR REPLACE FUNCTION update_reputation_from_action(
    p_lct_id VARCHAR(255),
    p_org_id VARCHAR(255),
    p_success BOOLEAN,
    p_action_type VARCHAR(100)
) RETURNS void AS $$
BEGIN
    -- Ensure reputation record exists
    INSERT INTO reputation_scores (lct_id, organization_id)
    VALUES (p_lct_id, p_org_id)
    ON CONFLICT (lct_id, organization_id) DO NOTHING;

    -- Update statistics
    IF p_success THEN
        UPDATE reputation_scores
        SET total_actions = total_actions + 1,
            successful_actions = successful_actions + 1,
            -- Slightly increase training and temperament on success
            training_score = LEAST(1.0, training_score + 0.001),
            temperament_score = LEAST(1.0, temperament_score + 0.0005),
            last_updated = CURRENT_TIMESTAMP
        WHERE lct_id = p_lct_id AND organization_id = p_org_id;
    ELSE
        UPDATE reputation_scores
        SET total_actions = total_actions + 1,
            failed_actions = failed_actions + 1,
            -- Slightly decrease temperament on failure
            temperament_score = GREATEST(0.0, temperament_score - 0.001),
            last_updated = CURRENT_TIMESTAMP
        WHERE lct_id = p_lct_id AND organization_id = p_org_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Check and auto-revoke delegations with insufficient trust
CREATE OR REPLACE FUNCTION check_delegation_trust_thresholds() RETURNS void AS $$
DECLARE
    delegation RECORD;
    min_t3 NUMERIC;
BEGIN
    FOR delegation IN
        SELECT ad.delegation_id, ad.delegatee_lct, ad.organization_id, ad.constraints,
               rs.t3_score
        FROM agent_delegations ad
        JOIN reputation_scores rs ON ad.delegatee_lct = rs.lct_id
                                   AND ad.organization_id = rs.organization_id
        WHERE ad.status = 'active'
    LOOP
        -- Check if constraints specify minimum T3
        IF delegation.constraints ? 'min_t3' THEN
            min_t3 := (delegation.constraints->>'min_t3')::NUMERIC;

            IF delegation.t3_score < min_t3 THEN
                -- Revoke delegation
                UPDATE agent_delegations
                SET status = 'revoked',
                    revoked_at = CURRENT_TIMESTAMP,
                    revocation_reason = 'Trust score dropped below threshold'
                WHERE delegation_id = delegation.delegation_id;

                -- Log revocation event
                INSERT INTO revocation_events (target_type, target_id, revoker_lct, revocation_reason, triggered_by)
                VALUES ('delegation', delegation.delegation_id, 'system',
                        'Automatic revocation: T3 score ' || delegation.t3_score || ' < ' || min_t3,
                        'trust_drop');
            END IF;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_lct_identities_updated_at BEFORE UPDATE ON lct_identities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_permission_claims_updated_at BEFORE UPDATE ON permission_claims
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_delegations_updated_at BEFORE UPDATE ON agent_delegations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-record revocation events
CREATE OR REPLACE FUNCTION log_revocation_event()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'revoked' AND OLD.status != 'revoked' THEN
        INSERT INTO revocation_events (
            target_type,
            target_id,
            revoker_lct,
            revocation_reason,
            triggered_by
        ) VALUES (
            CASE
                WHEN TG_TABLE_NAME = 'permission_claims' THEN 'permission_claim'
                WHEN TG_TABLE_NAME = 'agent_delegations' THEN 'delegation'
            END,
            CASE
                WHEN TG_TABLE_NAME = 'permission_claims' THEN NEW.claim_hash
                WHEN TG_TABLE_NAME = 'agent_delegations' THEN NEW.delegation_id
            END,
            'system', -- Default to system, update with actual revoker if known
            COALESCE(NEW.revocation_reason, 'No reason provided'),
            'manual'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER log_claim_revocation AFTER UPDATE ON permission_claims
    FOR EACH ROW EXECUTE FUNCTION log_revocation_event();

CREATE TRIGGER log_delegation_revocation AFTER UPDATE ON agent_delegations
    FOR EACH ROW EXECUTE FUNCTION log_revocation_event();

-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================

-- Insert sample organization
INSERT INTO organizations (organization_id, organization_name, metadata)
VALUES ('org:web4:default', 'Web4 Default Organization', '{"type": "protocol"}')
ON CONFLICT (organization_id) DO NOTHING;

-- Comments explaining the schema
COMMENT ON TABLE lct_identities IS 'LCT-based cryptographic identities for all entities';
COMMENT ON TABLE permission_claims IS 'Cryptographically signed permission grants';
COMMENT ON TABLE agent_delegations IS 'Authority delegations from principals to agents with ATP budgets';
COMMENT ON TABLE delegation_actions IS 'Immutable audit log of all actions under delegations';
COMMENT ON TABLE reputation_scores IS 'T3 trust tensor scores per entity per organization';
COMMENT ON TABLE revocation_events IS 'Immutable audit log of all revocations';

COMMENT ON COLUMN permission_claims.claim_hash IS 'SHA256 hash of claim content for immutability';
COMMENT ON COLUMN permission_claims.resource_pattern IS 'Glob pattern like "code:project123:*"';
COMMENT ON COLUMN permission_claims.witness_signatures IS 'JSONB array of {lct_id, signature} for witnessed permissions';
COMMENT ON COLUMN agent_delegations.granted_claim_hashes IS 'JSONB array of claim_hash references (foreign keys to permission_claims)';
COMMENT ON COLUMN agent_delegations.parent_delegation_id IS 'For sub-delegation chains, references parent delegation';
COMMENT ON COLUMN reputation_scores.t3_score IS 'Computed as 0.3*talent + 0.4*training + 0.3*temperament';
