-- Migration 006: Add Agent Health & Lifecycle Tables
-- Date: 2025-12-11
-- Description: Create tables for agent health monitoring and lifecycle management

-- ============================================================================
-- Agent Health Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS assembly.agent_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES assembly.agents(id) ON DELETE CASCADE,
    
    -- Overall Health Score (0.0 to 1.0)
    health_score FLOAT NOT NULL CHECK (health_score >= 0.0 AND health_score <= 1.0),
    
    -- Component Scores (0.0 to 1.0)
    usage_frequency FLOAT CHECK (usage_frequency >= 0.0 AND usage_frequency <= 1.0),
    success_rate FLOAT CHECK (success_rate >= 0.0 AND success_rate <= 1.0),
    user_satisfaction FLOAT CHECK (user_satisfaction >= 0.0 AND user_satisfaction <= 1.0),
    cost_efficiency FLOAT CHECK (cost_efficiency >= 0.0 AND cost_efficiency <= 1.0),
    response_time_score FLOAT CHECK (response_time_score >= 0.0 AND response_time_score <= 1.0),
    
    -- Raw Metrics
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    avg_response_time_ms FLOAT,
    total_cost FLOAT DEFAULT 0.0,
    
    -- Analysis
    trend VARCHAR(20) CHECK (trend IN ('improving', 'declining', 'stable', 'unknown')),
    risk_level VARCHAR(20) CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    recommendations JSONB,
    
    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT uq_agent_health_latest UNIQUE (agent_id, calculated_at)
);

CREATE INDEX idx_agent_health_agent ON assembly.agent_health(agent_id);
CREATE INDEX idx_agent_health_score ON assembly.agent_health(health_score);
CREATE INDEX idx_agent_health_risk ON assembly.agent_health(risk_level);
CREATE INDEX idx_agent_health_calculated ON assembly.agent_health(calculated_at DESC);

-- ============================================================================
-- Agent Lifecycle Events Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS assembly.agent_lifecycle_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES assembly.agents(id) ON DELETE CASCADE,
    
    -- Event Details
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'created', 'improved', 'split', 'merged', 'shutdown', 
        'reactivated', 'health_alert', 'manual_override'
    )),
    reason TEXT NOT NULL,
    
    -- State Tracking
    before_state JSONB,
    after_state JSONB,
    
    -- Trigger Information
    triggered_by VARCHAR(100) NOT NULL CHECK (triggered_by IN (
        'system', 'user', 'health_monitor', 'lifecycle_manager', 
        'agent_factory', 'manual'
    )),
    triggered_by_id UUID,  -- User ID or system component ID
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamp
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_lifecycle_agent ON assembly.agent_lifecycle_events(agent_id);
CREATE INDEX idx_lifecycle_type ON assembly.agent_lifecycle_events(event_type);
CREATE INDEX idx_lifecycle_occurred ON assembly.agent_lifecycle_events(occurred_at DESC);
CREATE INDEX idx_lifecycle_triggered_by ON assembly.agent_lifecycle_events(triggered_by);

-- ============================================================================
-- Agent Needs Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS assembly.agent_needs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    
    -- Need Description
    need_description TEXT NOT NULL,
    need_category VARCHAR(100),  -- capability, integration, automation, analysis
    
    -- Confidence & Evidence
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    supporting_evidence JSONB NOT NULL,
    
    -- Proposed Solution
    proposed_agent_spec JSONB,
    
    -- Status Tracking
    status VARCHAR(50) NOT NULL DEFAULT 'detected' CHECK (status IN (
        'detected', 'analyzing', 'approved', 'generating', 
        'testing', 'deployed', 'rejected', 'obsolete'
    )),
    
    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    fulfilled_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    
    -- Rejection/Obsolescence Reason
    resolution_reason TEXT
);

CREATE INDEX idx_agent_needs_entity ON assembly.agent_needs(entity_id);
CREATE INDEX idx_agent_needs_status ON assembly.agent_needs(status);
CREATE INDEX idx_agent_needs_confidence ON assembly.agent_needs(confidence_score DESC);
CREATE INDEX idx_agent_needs_detected ON assembly.agent_needs(detected_at DESC);

-- ============================================================================
-- Views for Easy Querying
-- ============================================================================

-- Latest health score per agent
CREATE OR REPLACE VIEW assembly.agent_health_latest AS
SELECT DISTINCT ON (agent_id)
    agent_id,
    health_score,
    usage_frequency,
    success_rate,
    user_satisfaction,
    cost_efficiency,
    response_time_score,
    trend,
    risk_level,
    recommendations,
    calculated_at
FROM assembly.agent_health
ORDER BY agent_id, calculated_at DESC;

-- Agent health summary with agent details
CREATE OR REPLACE VIEW assembly.agent_health_summary AS
SELECT 
    a.id as agent_id,
    a.agent_name,
    a.agent_type,
    a.is_active,
    h.health_score,
    h.trend,
    h.risk_level,
    h.total_requests,
    h.successful_requests,
    h.failed_requests,
    h.success_rate,
    h.calculated_at as last_health_check
FROM assembly.agents a
LEFT JOIN assembly.agent_health_latest h ON a.id = h.agent_id
ORDER BY h.health_score ASC NULLS LAST;

-- ============================================================================
-- Record Migration
-- ============================================================================

INSERT INTO public.migrations (migration_name, applied_at)
VALUES ('006_add_agent_health_tables', NOW())
ON CONFLICT (migration_name) DO NOTHING;
