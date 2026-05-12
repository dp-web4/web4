-- Web4 AI Entity Support - Schema Extension
-- Session #54: Implementation of Session #53 AI Entity Design
--
-- Extends the authorization schema to support AI entities with:
-- 1. Hardware binding (TPM/TEE attestation)
-- 2. Model provenance tracking
-- 3. AI-specific roles and capabilities
-- 4. Plugin capability requirements
--
-- This implements the design from SAGE_INTEGRATION_ANSWERS.md

-- ============================================================================
-- AI-Specific Entity Attributes
-- ============================================================================

-- Extend lct_identities entity_type to support AI subtypes
-- Already has: HUMAN, AI, SOCIETY, ROLE
-- Adding AI subtype tracking

CREATE TABLE IF NOT EXISTS ai_entity_attributes (
    lct_id VARCHAR(255) PRIMARY KEY REFERENCES lct_identities(lct_id) ON DELETE CASCADE,

    -- AI subtype (SAGE, GPT, CLAUDE, etc.)
    ai_subtype VARCHAR(50) NOT NULL, -- SAGE, GPT, CLAUDE, LLAMA, etc.
    ai_architecture VARCHAR(100), -- SAGE_v1, GPT-4, Claude-3, etc.

    -- Hardware Binding (for Sybil resistance)
    hardware_binding_type VARCHAR(50), -- TPM_ATTESTATION, TEE_ATTESTATION, SOFTWARE_ONLY
    hardware_binding_hash VARCHAR(66), -- SHA256 of hardware attestation
    hardware_id VARCHAR(255), -- Unique hardware identifier
    hardware_renewable BOOLEAN DEFAULT FALSE, -- Can binding be renewed?
    hardware_attestation_data JSONB, -- Full TPM/TEE attestation details

    -- Model Provenance
    model_weights_hash VARCHAR(66), -- SHA256 of model weights
    model_architecture_hash VARCHAR(66), -- SHA256 of architecture definition
    training_lineage_lct VARCHAR(255), -- LCT of training organization (e.g., lct:society:anthropic:...)
    training_completion_date TIMESTAMP WITH TIME ZONE,
    model_version VARCHAR(50),

    -- Capability Declaration
    declared_capabilities JSONB DEFAULT '[]'::jsonb, -- Array of capability names
    required_plugins JSONB DEFAULT '[]'::jsonb, -- Array of required plugin names
    supported_modalities JSONB DEFAULT '[]'::jsonb, -- ['vision', 'language', 'audio', etc.]

    -- Birth Witnesses (AI-specific)
    hardware_witness_signatures JSONB DEFAULT '[]'::jsonb, -- Hardware attestation witnesses
    deployment_authority_lct VARCHAR(255), -- Who deployed this AI instance

    -- Status
    hardware_binding_verified BOOLEAN DEFAULT FALSE,
    provenance_verified BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'active', -- active, suspended, decommissioned

    -- Metadata
    deployment_config JSONB DEFAULT '{}'::jsonb,
    resource_constraints JSONB DEFAULT '{}'::jsonb, -- Memory, compute, etc.

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_ai_entity_type CHECK (
        (SELECT entity_type FROM lct_identities WHERE lct_id = ai_entity_attributes.lct_id) = 'AI'
    )
);

CREATE INDEX idx_ai_subtype ON ai_entity_attributes(ai_subtype);
CREATE INDEX idx_ai_architecture ON ai_entity_attributes(ai_architecture);
CREATE INDEX idx_ai_hardware_id ON ai_entity_attributes(hardware_id);
CREATE INDEX idx_ai_training_lineage ON ai_entity_attributes(training_lineage_lct);
CREATE INDEX idx_ai_status ON ai_entity_attributes(status);

COMMENT ON TABLE ai_entity_attributes IS 'AI-specific attributes for entities with entity_type = AI';
COMMENT ON COLUMN ai_entity_attributes.hardware_binding_hash IS 'SHA256 hash of TPM/TEE attestation binding AI LCT to physical hardware';
COMMENT ON COLUMN ai_entity_attributes.model_weights_hash IS 'SHA256 hash of model weights for provenance tracking';
COMMENT ON COLUMN ai_entity_attributes.training_lineage_lct IS 'LCT of the society/organization that trained this model';

-- ============================================================================
-- AI-Specific Roles
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_role_requirements (
    role_lct VARCHAR(255) PRIMARY KEY REFERENCES lct_identities(lct_id) ON DELETE CASCADE,

    -- Role specification
    role_name VARCHAR(255) NOT NULL,
    role_description TEXT,

    -- Capability requirements
    required_capabilities JSONB NOT NULL DEFAULT '[]'::jsonb, -- e.g., ['vision_encoding', 'image_analysis']
    required_plugins JSONB NOT NULL DEFAULT '[]'::jsonb, -- e.g., ['vision_irp', 'multimodal_fusion']
    required_modalities JSONB DEFAULT '[]'::jsonb, -- e.g., ['vision', 'language']

    -- Trust requirements
    min_t3_score NUMERIC(4, 3), -- Minimum T3 trust score to hold this role
    min_talent NUMERIC(4, 3),
    min_training NUMERIC(4, 3),
    min_temperament NUMERIC(4, 3),

    -- ATP economics
    atp_earning_multiplier NUMERIC(4, 2) DEFAULT 1.0, -- Role-based ATP earning bonus
    base_atp_cost_modifier NUMERIC(4, 2) DEFAULT 1.0, -- Role-based cost modifier

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_role_entity_type CHECK (
        (SELECT entity_type FROM lct_identities WHERE lct_id = ai_role_requirements.role_lct) = 'ROLE'
    ),
    CONSTRAINT chk_atp_multipliers CHECK (
        atp_earning_multiplier > 0 AND atp_cost_modifier > 0
    )
);

CREATE INDEX idx_role_name ON ai_role_requirements(role_name);

COMMENT ON TABLE ai_role_requirements IS 'Capability and trust requirements for AI-specific roles';
COMMENT ON COLUMN ai_role_requirements.atp_earning_multiplier IS 'Multiplier for ATP earned when performing role actions (e.g., 1.5 = 50% bonus)';

-- ============================================================================
-- AI Capability Registry
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_capabilities (
    capability_id VARCHAR(255) PRIMARY KEY,
    capability_name VARCHAR(255) NOT NULL UNIQUE,
    capability_category VARCHAR(100), -- 'perception', 'reasoning', 'generation', 'coordination'
    description TEXT,

    -- Technical specification
    input_types JSONB DEFAULT '[]'::jsonb, -- e.g., ['image', 'text', 'audio']
    output_types JSONB DEFAULT '[]'::jsonb,
    plugin_requirements JSONB DEFAULT '[]'::jsonb,

    -- ATP cost model
    base_atp_cost INTEGER DEFAULT 1,
    cost_scaling_factor NUMERIC(4, 2) DEFAULT 1.0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_capability_category ON ai_capabilities(capability_category);

COMMENT ON TABLE ai_capabilities IS 'Registry of AI capabilities for role requirements and entity declarations';

-- ============================================================================
-- AI Entity Role Assignments
-- ============================================================================

CREATE TABLE IF NOT EXISTS ai_entity_roles (
    assignment_id BIGSERIAL PRIMARY KEY,
    lct_id VARCHAR(255) NOT NULL REFERENCES lct_identities(lct_id) ON DELETE CASCADE,
    role_lct VARCHAR(255) NOT NULL REFERENCES ai_role_requirements(role_lct) ON DELETE CASCADE,
    organization_id VARCHAR(255) NOT NULL REFERENCES organizations(organization_id),

    -- Assignment details
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by_lct VARCHAR(255), -- Who granted this role
    valid_until TIMESTAMP WITH TIME ZONE,

    -- Verification
    capabilities_verified BOOLEAN DEFAULT FALSE,
    trust_requirements_met BOOLEAN DEFAULT FALSE,

    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, suspended, revoked

    -- Metadata
    assignment_metadata JSONB DEFAULT '{}'::jsonb,

    UNIQUE (lct_id, role_lct, organization_id),
    CONSTRAINT chk_ai_role_entity_type CHECK (
        (SELECT entity_type FROM lct_identities WHERE lct_id = ai_entity_roles.lct_id) = 'AI'
    )
);

CREATE INDEX idx_entity_role_lct ON ai_entity_roles(lct_id);
CREATE INDEX idx_entity_role_role ON ai_entity_roles(role_lct);
CREATE INDEX idx_entity_role_org ON ai_entity_roles(organization_id);
CREATE INDEX idx_entity_role_status ON ai_entity_roles(status);

COMMENT ON TABLE ai_entity_roles IS 'Assignment of AI entities to roles they are qualified for';

-- ============================================================================
-- Views
-- ============================================================================

-- Full AI Entity Profile (combines identity + AI attributes + roles)
CREATE OR REPLACE VIEW ai_entity_profiles AS
SELECT
    lct.lct_id,
    lct.entity_type,
    lct.society_id,
    lct.public_key,
    ai.ai_subtype,
    ai.ai_architecture,
    ai.hardware_binding_type,
    ai.hardware_binding_verified,
    ai.model_version,
    ai.declared_capabilities,
    ai.supported_modalities,
    ai.provenance_verified,
    ai.status AS ai_status,
    rs.t3_score,
    rs.reputation_level,
    COALESCE(
        (
            SELECT jsonb_agg(jsonb_build_object(
                'role_lct', role_lct,
                'role_name', (SELECT role_name FROM ai_role_requirements WHERE role_lct = aer.role_lct),
                'assigned_at', assigned_at,
                'status', status
            ))
            FROM ai_entity_roles aer
            WHERE aer.lct_id = lct.lct_id AND aer.status = 'active'
        ),
        '[]'::jsonb
    ) AS active_roles
FROM lct_identities lct
LEFT JOIN ai_entity_attributes ai ON lct.lct_id = ai.lct_id
LEFT JOIN reputation_scores rs ON lct.lct_id = rs.lct_id
WHERE lct.entity_type = 'AI';

COMMENT ON VIEW ai_entity_profiles IS 'Complete profile of AI entities including attributes, roles, and reputation';

-- AI entities qualified for specific roles (meets requirements)
CREATE OR REPLACE VIEW ai_role_qualified_entities AS
SELECT
    lct.lct_id,
    ai.ai_subtype,
    ai.ai_architecture,
    arr.role_lct,
    arr.role_name,
    rs.t3_score,
    rs.talent_score,
    rs.training_score,
    rs.temperament_score,
    rs.reputation_level,
    -- Check if capabilities are sufficient
    ai.declared_capabilities @> arr.required_capabilities AS capabilities_met,
    -- Check if plugins are available
    ai.required_plugins @> arr.required_plugins AS plugins_met,
    -- Check if trust requirements are met
    (rs.t3_score >= COALESCE(arr.min_t3_score, 0)) AS trust_met,
    -- Overall qualification
    (
        ai.declared_capabilities @> arr.required_capabilities AND
        ai.required_plugins @> arr.required_plugins AND
        rs.t3_score >= COALESCE(arr.min_t3_score, 0) AND
        (arr.min_talent IS NULL OR rs.talent_score >= arr.min_talent) AND
        (arr.min_training IS NULL OR rs.training_score >= arr.min_training) AND
        (arr.min_temperament IS NULL OR rs.temperament_score >= arr.min_temperament)
    ) AS fully_qualified
FROM lct_identities lct
JOIN ai_entity_attributes ai ON lct.lct_id = ai.lct_id
JOIN reputation_scores rs ON lct.lct_id = rs.lct_id
CROSS JOIN ai_role_requirements arr
WHERE lct.entity_type = 'AI' AND ai.status = 'active';

COMMENT ON VIEW ai_role_qualified_entities IS 'Shows which AI entities are qualified for which roles based on capabilities and trust';

-- ============================================================================
-- Functions
-- ============================================================================

-- Verify AI entity capabilities match declared capabilities
CREATE OR REPLACE FUNCTION verify_ai_capabilities(
    p_lct_id VARCHAR(255),
    p_test_results JSONB -- Results from capability tests
) RETURNS BOOLEAN AS $$
DECLARE
    declared_caps JSONB;
    tested_cap TEXT;
    cap_result BOOLEAN;
    all_verified BOOLEAN := TRUE;
BEGIN
    -- Get declared capabilities
    SELECT declared_capabilities INTO declared_caps
    FROM ai_entity_attributes
    WHERE lct_id = p_lct_id;

    IF declared_caps IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check each declared capability was tested and passed
    FOR tested_cap IN SELECT jsonb_array_elements_text(declared_caps)
    LOOP
        cap_result := (p_test_results->tested_cap)::BOOLEAN;
        IF cap_result IS NULL OR cap_result = FALSE THEN
            all_verified := FALSE;
            EXIT;
        END IF;
    END LOOP;

    RETURN all_verified;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION verify_ai_capabilities IS 'Verify AI entity capabilities match declarations';

-- Check if AI entity meets role requirements
CREATE OR REPLACE FUNCTION check_ai_role_eligibility(
    p_lct_id VARCHAR(255),
    p_role_lct VARCHAR(255),
    p_org_id VARCHAR(255)
) RETURNS JSONB AS $$
DECLARE
    entity_caps JSONB;
    entity_plugins JSONB;
    role_req RECORD;
    entity_trust RECORD;
    result JSONB;
BEGIN
    -- Get entity attributes
    SELECT declared_capabilities, required_plugins
    INTO entity_caps, entity_plugins
    FROM ai_entity_attributes
    WHERE lct_id = p_lct_id;

    -- Get role requirements
    SELECT * INTO role_req
    FROM ai_role_requirements
    WHERE role_lct = p_role_lct;

    -- Get entity trust scores
    SELECT * INTO entity_trust
    FROM reputation_scores
    WHERE lct_id = p_lct_id AND organization_id = p_org_id;

    -- Build eligibility result
    result := jsonb_build_object(
        'eligible', FALSE,
        'capabilities_met', entity_caps @> role_req.required_capabilities,
        'plugins_met', entity_plugins @> role_req.required_plugins,
        'trust_met', entity_trust.t3_score >= COALESCE(role_req.min_t3_score, 0),
        't3_score', entity_trust.t3_score,
        'required_t3', role_req.min_t3_score,
        'missing_capabilities', role_req.required_capabilities - entity_caps,
        'missing_plugins', role_req.required_plugins - entity_plugins
    );

    -- Set eligible flag if all requirements met
    IF (result->'capabilities_met')::BOOLEAN AND
       (result->'plugins_met')::BOOLEAN AND
       (result->'trust_met')::BOOLEAN THEN
        result := jsonb_set(result, '{eligible}', 'true'::jsonb);
    END IF;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_ai_role_eligibility IS 'Check if AI entity meets all requirements for a specific role';

-- ============================================================================
-- Sample Data (AI Capabilities)
-- ============================================================================

INSERT INTO ai_capabilities (capability_id, capability_name, capability_category, description)
VALUES
    ('cap:vision:encoding', 'vision_encoding', 'perception', 'Encode visual input into latent representations'),
    ('cap:vision:analysis', 'image_analysis', 'perception', 'Analyze and interpret image content'),
    ('cap:lang:understanding', 'language_understanding', 'reasoning', 'Understand natural language input'),
    ('cap:lang:generation', 'language_generation', 'generation', 'Generate natural language output'),
    ('cap:reasoning:planning', 'strategic_planning', 'reasoning', 'Plan multi-step action sequences'),
    ('cap:reasoning:causal', 'causal_reasoning', 'reasoning', 'Infer causal relationships'),
    ('cap:coord:delegation', 'task_delegation', 'coordination', 'Delegate tasks to other entities'),
    ('cap:coord:collaboration', 'collaborative_work', 'coordination', 'Collaborate with other AI entities')
ON CONFLICT (capability_id) DO NOTHING;

-- ============================================================================
-- Triggers
-- ============================================================================

-- Auto-update updated_at timestamp for AI entities
CREATE TRIGGER update_ai_entity_attributes_updated_at BEFORE UPDATE ON ai_entity_attributes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ai_role_requirements_updated_at BEFORE UPDATE ON ai_role_requirements
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Migration Support
-- ============================================================================

-- Helper function to convert existing AI entities to new schema
CREATE OR REPLACE FUNCTION migrate_ai_entity(
    p_lct_id VARCHAR(255),
    p_ai_subtype VARCHAR(50),
    p_architecture VARCHAR(100)
) RETURNS void AS $$
BEGIN
    -- Ensure entity is marked as AI type
    UPDATE lct_identities
    SET entity_type = 'AI'
    WHERE lct_id = p_lct_id;

    -- Create AI attributes record
    INSERT INTO ai_entity_attributes (lct_id, ai_subtype, ai_architecture)
    VALUES (p_lct_id, p_ai_subtype, p_architecture)
    ON CONFLICT (lct_id) DO UPDATE
    SET ai_subtype = p_ai_subtype,
        ai_architecture = p_architecture;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION migrate_ai_entity IS 'Helper to migrate existing AI entities to new schema';
