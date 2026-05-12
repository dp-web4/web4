-- Delegation Audit Log Schema
-- Session #59: P1 Security Fix for Unauthorized Delegation

-- Audit log for all delegation validation attempts
CREATE TABLE IF NOT EXISTS delegation_audit_log (
    audit_id BIGSERIAL PRIMARY KEY,
    delegation_id VARCHAR(255) NOT NULL,
    delegator_lct VARCHAR(255) NOT NULL,
    delegatee_lct VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- 'validation_success', 'validation_failure', 'creation', 'revocation'
    event_data JSONB DEFAULT '{}',   -- Additional event details
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for querying
CREATE INDEX IF NOT EXISTS idx_audit_delegation_id ON delegation_audit_log(delegation_id);
CREATE INDEX IF NOT EXISTS idx_audit_delegator ON delegation_audit_log(delegator_lct);
CREATE INDEX IF NOT EXISTS idx_audit_delegatee ON delegation_audit_log(delegatee_lct);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON delegation_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON delegation_audit_log(created_at DESC);

-- Comments
COMMENT ON TABLE delegation_audit_log IS 'Audit trail for all delegation validation and lifecycle events';
COMMENT ON COLUMN delegation_audit_log.event_type IS 'Type of event: validation_success, validation_failure, creation, revocation';
COMMENT ON COLUMN delegation_audit_log.event_data IS 'JSON data with event details (error messages, validation results, etc.)';
