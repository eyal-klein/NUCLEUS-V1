-- ============================================================================
-- NUCLEUS V1.2 - Phase 5: LinkedIn Social Network Models
-- Migration for social-context-engine and network-intelligence services
-- ============================================================================

-- LinkedIn Profiles (entity's own profile)
CREATE TABLE IF NOT EXISTS memory.linkedin_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- LinkedIn identifiers
    linkedin_id VARCHAR(255) UNIQUE NOT NULL,
    profile_url VARCHAR(500),
    
    -- Basic info
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    headline VARCHAR(500),
    summary TEXT,
    
    -- Professional info
    current_company VARCHAR(255),
    current_position VARCHAR(255),
    industry VARCHAR(255),
    location VARCHAR(255),
    
    -- Experience and education (JSONB for flexibility)
    experience JSONB DEFAULT '[]'::jsonb,
    education JSONB DEFAULT '[]'::jsonb,
    skills JSONB DEFAULT '[]'::jsonb,
    
    -- Network stats
    connections_count INTEGER,
    
    -- Timestamps
    last_synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'::jsonb
);

-- Indexes for linkedin_profiles
CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_entity_id ON memory.linkedin_profiles(entity_id);


-- LinkedIn Connections (entity's connections)
CREATE TABLE IF NOT EXISTS memory.linkedin_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Connection identifiers
    connection_linkedin_id VARCHAR(255) NOT NULL,
    profile_url VARCHAR(500),
    
    -- Basic info
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    headline VARCHAR(500),
    
    -- Professional info
    current_company VARCHAR(255),
    current_position VARCHAR(255),
    industry VARCHAR(255),
    location VARCHAR(255),
    
    -- Connection metadata
    connected_at TIMESTAMP WITH TIME ZONE,
    connection_degree INTEGER DEFAULT 1,
    
    -- Timestamps
    last_synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'::jsonb
);

-- Indexes for linkedin_connections
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_entity_id ON memory.linkedin_connections(entity_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_linkedin_id ON memory.linkedin_connections(connection_linkedin_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_company ON memory.linkedin_connections(current_company);
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_location ON memory.linkedin_connections(location);
CREATE INDEX IF NOT EXISTS idx_linkedin_connections_connected_at ON memory.linkedin_connections(connected_at);


-- LinkedIn Activities (posts, comments, likes)
CREATE TABLE IF NOT EXISTS memory.linkedin_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Activity identifiers
    activity_id VARCHAR(255) UNIQUE,
    author_linkedin_id VARCHAR(255) NOT NULL,
    
    -- Activity type
    activity_type VARCHAR(50) NOT NULL,  -- post, comment, like, share, article
    
    -- Content
    content TEXT,
    url VARCHAR(500),
    
    -- Engagement metrics
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    
    -- Temporal
    posted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'::jsonb
);

-- Indexes for linkedin_activities
CREATE INDEX IF NOT EXISTS idx_linkedin_activities_entity_id ON memory.linkedin_activities(entity_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_activities_author ON memory.linkedin_activities(author_linkedin_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_activities_posted_at ON memory.linkedin_activities(posted_at);


-- Relationship Scores (calculated by social-context-engine)
CREATE TABLE IF NOT EXISTS dna.relationship_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    connection_id UUID NOT NULL REFERENCES memory.linkedin_connections(id) ON DELETE CASCADE,
    
    -- Score components (0-1 scale)
    overall_score FLOAT NOT NULL,
    interaction_score FLOAT DEFAULT 0.0,
    recency_score FLOAT DEFAULT 0.0,
    mutual_connections_score FLOAT DEFAULT 0.0,
    shared_experience_score FLOAT DEFAULT 0.0,
    sentiment_score FLOAT DEFAULT 0.0,
    
    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'::jsonb,
    
    -- Unique constraint to prevent duplicates
    UNIQUE(entity_id, connection_id)
);

-- Indexes for relationship_scores
CREATE INDEX IF NOT EXISTS idx_relationship_scores_entity_id ON dna.relationship_scores(entity_id);
CREATE INDEX IF NOT EXISTS idx_relationship_scores_connection_id ON dna.relationship_scores(connection_id);


-- Network Insights (aggregated analysis)
CREATE TABLE IF NOT EXISTS dna.network_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Network metrics
    total_connections INTEGER DEFAULT 0,
    network_growth_rate FLOAT DEFAULT 0.0,
    
    -- Cluster analysis (JSONB for flexibility)
    company_clusters JSONB DEFAULT '{}'::jsonb,
    industry_clusters JSONB DEFAULT '{}'::jsonb,
    location_clusters JSONB DEFAULT '{}'::jsonb,
    
    -- Top connectors
    top_connectors JSONB DEFAULT '[]'::jsonb,
    
    -- Analysis date
    analysis_date DATE NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'::jsonb,
    
    -- Unique constraint for one insight per entity per day
    UNIQUE(entity_id, analysis_date)
);

-- Indexes for network_insights
CREATE INDEX IF NOT EXISTS idx_network_insights_entity_id ON dna.network_insights(entity_id);
CREATE INDEX IF NOT EXISTS idx_network_insights_date ON dna.network_insights(analysis_date);


-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA memory TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA dna TO postgres;
