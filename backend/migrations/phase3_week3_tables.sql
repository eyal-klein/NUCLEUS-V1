-- ============================================================================
-- NUCLEUS Phase 3 - Week 3: LinkedIn Integration & Social Context
-- Database Migration Script
-- ============================================================================
-- Purpose: Create tables for LinkedIn data, relationship scoring, and network intelligence
-- Date: December 11, 2025
-- ============================================================================

-- ============================================================================
-- 1. LinkedIn Profiles Table
-- ============================================================================
-- Stores LinkedIn profile data for entities

CREATE TABLE IF NOT EXISTS memory.linkedin_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Profile basics
    linkedin_id VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    headline VARCHAR(500),
    summary TEXT,
    profile_url VARCHAR(500),
    profile_picture_url VARCHAR(500),
    
    -- Current position
    current_company VARCHAR(255),
    current_title VARCHAR(255),
    
    -- Location
    location VARCHAR(255),
    country VARCHAR(100),
    
    -- Stats
    connections_count INTEGER DEFAULT 0,
    followers_count INTEGER DEFAULT 0,
    
    -- Experience & Education (JSONB arrays)
    experience JSONB DEFAULT '[]'::jsonb,
    education JSONB DEFAULT '[]'::jsonb,
    skills JSONB DEFAULT '[]'::jsonb,
    certifications JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT linkedin_profiles_entity_unique UNIQUE (entity_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_entity_id ON memory.linkedin_profiles(entity_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_linkedin_id ON memory.linkedin_profiles(linkedin_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_company ON memory.linkedin_profiles(current_company);

-- Comments
COMMENT ON TABLE memory.linkedin_profiles IS 'LinkedIn profile data for entities';
COMMENT ON COLUMN memory.linkedin_profiles.experience IS 'Array of work experience objects';
COMMENT ON COLUMN memory.linkedin_profiles.education IS 'Array of education objects';
COMMENT ON COLUMN memory.linkedin_profiles.skills IS 'Array of skill objects';

-- ============================================================================
-- 2. LinkedIn Connections Table
-- ============================================================================
-- Stores LinkedIn connections for entities

CREATE TABLE IF NOT EXISTS memory.linkedin_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Connection details
    connection_linkedin_id VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    headline VARCHAR(500),
    profile_url VARCHAR(500),
    profile_picture_url VARCHAR(500),
    
    -- Current position
    current_company VARCHAR(255),
    current_title VARCHAR(255),
    
    -- Location
    location VARCHAR(255),
    
    -- Connection metadata
    connected_at TIMESTAMP WITH TIME ZONE,
    connection_strength VARCHAR(50), -- first, second, third degree
    
    -- Metadata
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT linkedin_connections_unique UNIQUE (entity_id, connection_linkedin_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_entity_id ON memory.linkedin_connections(entity_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_linkedin_id ON memory.linkedin_connections(connection_linkedin_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_company ON memory.linkedin_connections(current_company);
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_location ON memory.linkedin_connections(location);

-- Comments
COMMENT ON TABLE memory.linkedin_connections IS 'LinkedIn connections for entities';
COMMENT ON COLUMN memory.linkedin_connections.connection_strength IS 'Degree of connection: first, second, third';

-- ============================================================================
-- 3. LinkedIn Activities Table
-- ============================================================================
-- Stores LinkedIn activity feed (posts, comments, shares, etc.)

CREATE TABLE IF NOT EXISTS memory.linkedin_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Activity details
    activity_id VARCHAR(255) NOT NULL,
    activity_type VARCHAR(50), -- post, comment, share, like, job_change
    author_linkedin_id VARCHAR(255),
    author_name VARCHAR(255),
    
    -- Content
    content TEXT,
    media_urls JSONB DEFAULT '[]'::jsonb,
    
    -- Engagement
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    
    -- Timing
    posted_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT linkedin_activities_unique UNIQUE (entity_id, activity_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_linkedin_activities_entity_id ON memory.linkedin_activities(entity_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_activities_author ON memory.linkedin_activities(author_linkedin_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_activities_type ON memory.linkedin_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_linkedin_activities_posted_at ON memory.linkedin_activities(posted_at DESC);

-- Comments
COMMENT ON TABLE memory.linkedin_activities IS 'LinkedIn activity feed for entities';
COMMENT ON COLUMN memory.linkedin_activities.activity_type IS 'Type of activity: post, comment, share, like, job_change';

-- ============================================================================
-- 4. Relationship Scores Table
-- ============================================================================
-- Stores calculated relationship strength scores

CREATE TABLE IF NOT EXISTS dna.relationship_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    connection_id UUID NOT NULL REFERENCES memory.linkedin_connections(id) ON DELETE CASCADE,
    
    -- Scores (0-1 range)
    overall_score DECIMAL(3,2) CHECK (overall_score >= 0 AND overall_score <= 1),
    interaction_score DECIMAL(3,2),
    recency_score DECIMAL(3,2),
    mutual_connections_score DECIMAL(3,2),
    shared_experience_score DECIMAL(3,2),
    
    -- Factors
    last_interaction_date TIMESTAMP WITH TIME ZONE,
    interaction_count INTEGER DEFAULT 0,
    mutual_connections_count INTEGER DEFAULT 0,
    shared_companies JSONB DEFAULT '[]'::jsonb,
    shared_schools JSONB DEFAULT '[]'::jsonb,
    
    -- Sentiment
    sentiment_score DECIMAL(3,2), -- -1 to 1
    
    -- Metadata
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT relationship_scores_unique UNIQUE (entity_id, connection_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_relationship_scores_entity_id ON dna.relationship_scores(entity_id);
CREATE INDEX IF NOT EXISTS idx_relationship_scores_connection_id ON dna.relationship_scores(connection_id);
CREATE INDEX IF NOT EXISTS idx_relationship_scores_overall ON dna.relationship_scores(overall_score DESC);

-- Comments
COMMENT ON TABLE dna.relationship_scores IS 'Calculated relationship strength scores';
COMMENT ON COLUMN dna.relationship_scores.overall_score IS 'Overall relationship strength (0-1)';
COMMENT ON COLUMN dna.relationship_scores.sentiment_score IS 'Sentiment score (-1 to 1)';

-- ============================================================================
-- 5. Network Insights Table
-- ============================================================================
-- Stores network analysis insights

CREATE TABLE IF NOT EXISTS dna.network_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Network stats
    total_connections INTEGER,
    network_growth_rate DECIMAL(5,2), -- percentage
    
    -- Clusters (JSONB)
    company_clusters JSONB DEFAULT '[]'::jsonb,
    industry_clusters JSONB DEFAULT '[]'::jsonb,
    location_clusters JSONB DEFAULT '[]'::jsonb,
    
    -- Key connections
    top_connectors JSONB DEFAULT '[]'::jsonb,
    
    -- Opportunities
    detected_opportunities JSONB DEFAULT '[]'::jsonb,
    
    -- Analysis date
    analysis_date DATE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT network_insights_entity_date_unique UNIQUE (entity_id, analysis_date)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_network_insights_entity_id ON dna.network_insights(entity_id);
CREATE INDEX IF NOT EXISTS idx_network_insights_date ON dna.network_insights(analysis_date DESC);

-- Comments
COMMENT ON TABLE dna.network_insights IS 'Network analysis insights and statistics';
COMMENT ON COLUMN dna.network_insights.company_clusters IS 'Connections grouped by company';
COMMENT ON COLUMN dna.network_insights.top_connectors IS 'Most valuable connections';

-- ============================================================================
-- Grant Permissions
-- ============================================================================

-- Grant permissions to application role (adjust role name as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA memory TO nucleus_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA dna TO nucleus_app;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify tables were created
SELECT 
    schemaname, 
    tablename, 
    tableowner 
FROM pg_tables 
WHERE schemaname IN ('memory', 'dna') 
    AND tablename IN (
        'linkedin_profiles',
        'linkedin_connections', 
        'linkedin_activities',
        'relationship_scores',
        'network_insights'
    )
ORDER BY schemaname, tablename;

-- ============================================================================
-- Sample Queries (for testing)
-- ============================================================================

-- Count LinkedIn profiles
-- SELECT COUNT(*) FROM memory.linkedin_profiles;

-- Get entity's connections
-- SELECT * FROM memory.linkedin_connections WHERE entity_id = 'YOUR_ENTITY_ID';

-- Get top relationship scores
-- SELECT * FROM dna.relationship_scores WHERE entity_id = 'YOUR_ENTITY_ID' ORDER BY overall_score DESC LIMIT 10;

-- Get latest network insights
-- SELECT * FROM dna.network_insights WHERE entity_id = 'YOUR_ENTITY_ID' ORDER BY analysis_date DESC LIMIT 1;

-- ============================================================================
-- End of Migration Script
-- ============================================================================
