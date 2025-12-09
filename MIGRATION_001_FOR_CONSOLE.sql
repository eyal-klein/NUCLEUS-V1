-- ============================================================================
-- NUCLEUS V1.2 - Migration 001: Initialize Core Schemas
-- Simplified version for Cloud Console (without vector extension)
-- ============================================================================

-- ============================================================================
-- SCHEMA: dna
-- Purpose: Entity identity, values, goals, interests
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS dna;

CREATE TABLE IF NOT EXISTS dna.entity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dna.interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES dna.entity(id) ON DELETE CASCADE,
    interest_name VARCHAR(255) NOT NULL,
    interest_description TEXT,
    confidence_score FLOAT DEFAULT 0.0,
    first_detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_reinforced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS dna.goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES dna.entity(id) ON DELETE CASCADE,
    goal_title VARCHAR(500) NOT NULL,
    goal_description TEXT,
    priority INTEGER DEFAULT 5,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dna.values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES dna.entity(id) ON DELETE CASCADE,
    value_name VARCHAR(255) NOT NULL,
    value_description TEXT,
    importance_score FLOAT DEFAULT 0.5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dna.raw_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES dna.entity(id) ON DELETE CASCADE,
    data_type VARCHAR(100) NOT NULL,
    data_content TEXT NOT NULL,
    meta_data JSONB,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SCHEMA: memory
-- Purpose: Conversation history, summaries
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS memory;

CREATE TABLE IF NOT EXISTS memory.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    session_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memory.summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    summary_type VARCHAR(100) NOT NULL,
    summary_content TEXT NOT NULL,
    time_period_start TIMESTAMP WITH TIME ZONE,
    time_period_end TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SCHEMA: assembly
-- Purpose: Agent & tool definitions
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS assembly;

CREATE TABLE IF NOT EXISTS assembly.agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(255) NOT NULL UNIQUE,
    agent_type VARCHAR(100) NOT NULL,
    system_prompt TEXT NOT NULL,
    description TEXT,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assembly.tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name VARCHAR(255) NOT NULL UNIQUE,
    tool_description TEXT,
    tool_schema JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assembly.agent_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES assembly.agents(id) ON DELETE CASCADE,
    tool_id UUID REFERENCES assembly.tools(id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_id, tool_id)
);

CREATE TABLE IF NOT EXISTS assembly.agent_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES assembly.agents(id) ON DELETE CASCADE,
    task_id UUID NOT NULL,
    success BOOLEAN NOT NULL,
    execution_time_ms INTEGER,
    feedback_score FLOAT,
    metadata JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SCHEMA: execution
-- Purpose: Tasks, jobs, logs
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS execution;

CREATE TABLE IF NOT EXISTS execution.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    task_title VARCHAR(500) NOT NULL,
    task_description TEXT,
    assigned_agent_id UUID,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS execution.jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name VARCHAR(255) NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS execution.logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    log_level VARCHAR(20) NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tasks_entity_id ON execution.tasks(entity_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON execution.tasks(status);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON execution.jobs(status);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON execution.logs(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_entity_id ON memory.conversations(entity_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON memory.conversations(session_id);

-- ============================================================================
-- SEED DATA: Create default entity
-- ============================================================================

INSERT INTO dna.entity (name) VALUES ('Eyal Klein') 
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Success message
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 001 completed successfully!';
    RAISE NOTICE '   - Schema: dna created with 5 tables';
    RAISE NOTICE '   - Schema: memory created with 2 tables';
    RAISE NOTICE '   - Schema: assembly created with 4 tables';
    RAISE NOTICE '   - Schema: execution created with 3 tables';
    RAISE NOTICE '   - Default entity "Eyal Klein" created';
    RAISE NOTICE '';
    RAISE NOTICE '👉 Next: Run migration 002 to add entity_integrations table';
END $$;
