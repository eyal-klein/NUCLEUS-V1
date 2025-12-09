-- Migration: Add Entity Integrations Table
-- Version: 002
-- Date: 2025-12-09
-- Description: Add support for storing third-party service integrations

-- Create entity_integrations table
CREATE TABLE IF NOT EXISTS dna.entity_integrations (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Entity reference
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Integration details
    service_name VARCHAR(100) NOT NULL,      -- 'gmail', 'github', 'notion', 'slack'
    service_type VARCHAR(50) NOT NULL,       -- 'email', 'code', 'docs', 'chat', 'calendar'
    display_name VARCHAR(255),               -- User-friendly name
    description TEXT,                        -- Optional description
    
    -- Credentials reference (NOT the actual credentials!)
    secret_path VARCHAR(255) NOT NULL,       -- Path in GCP Secret Manager
    credential_type VARCHAR(50) NOT NULL,    -- 'oauth2', 'api_key', 'basic_auth', 'bearer_token'
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'active',     -- 'active', 'inactive', 'expired', 'error', 'revoked'
    last_sync_at TIMESTAMP WITH TIME ZONE,   -- Last successful data sync
    last_sync_status VARCHAR(50),            -- 'success', 'failed', 'partial'
    sync_error_message TEXT,                 -- Error details if sync failed
    next_sync_at TIMESTAMP WITH TIME ZONE,   -- Scheduled next sync
    
    -- OAuth-specific (if applicable)
    token_expires_at TIMESTAMP WITH TIME ZONE, -- When access token expires
    scopes JSONB,                            -- OAuth scopes granted
    
    -- Configuration
    config JSONB DEFAULT '{}',               -- Service-specific configuration
    sync_settings JSONB DEFAULT '{}',        -- Sync frequency, filters, etc.
    
    -- Metadata
    meta_data JSONB DEFAULT '{}',            -- Additional metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),                 -- Who created this integration
    
    -- Constraints
    UNIQUE(entity_id, service_name),         -- One integration per service per entity
    CHECK (status IN ('active', 'inactive', 'expired', 'error', 'revoked')),
    CHECK (credential_type IN ('oauth2', 'api_key', 'basic_auth', 'bearer_token'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_entity_integrations_entity_id 
    ON dna.entity_integrations(entity_id);

CREATE INDEX IF NOT EXISTS idx_entity_integrations_service_name 
    ON dna.entity_integrations(service_name);

CREATE INDEX IF NOT EXISTS idx_entity_integrations_status 
    ON dna.entity_integrations(status);

CREATE INDEX IF NOT EXISTS idx_entity_integrations_next_sync 
    ON dna.entity_integrations(next_sync_at) 
    WHERE status = 'active';

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_entity_integrations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER entity_integrations_updated_at
    BEFORE UPDATE ON dna.entity_integrations
    FOR EACH ROW
    EXECUTE FUNCTION update_entity_integrations_updated_at();

-- Record migration
INSERT INTO public.migrations (version, description, executed_at)
VALUES ('002', 'Add entity_integrations table', CURRENT_TIMESTAMP)
ON CONFLICT (version) DO NOTHING;
