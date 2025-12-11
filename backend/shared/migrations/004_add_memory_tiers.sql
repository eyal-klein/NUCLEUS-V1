-- Migration 004: Add 4-Tier Memory Architecture
-- Phase 1 - V2.0: Memory Engine
-- Date: 2025-12-10

-- Create memory_tier1 table (Ultra-fast, < 10ms)
CREATE TABLE IF NOT EXISTS memory.memory_tier1 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    interaction_type VARCHAR(100) NOT NULL,
    interaction_data JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ttl_hours INTEGER DEFAULT 24
);

CREATE INDEX IF NOT EXISTS idx_memory_tier1_entity_timestamp ON memory.memory_tier1(entity_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memory_tier1_timestamp ON memory.memory_tier1(timestamp);

COMMENT ON TABLE memory.memory_tier1 IS 'Tier 1: Ultra-fast memory (< 10ms latency), last 24 hours';
COMMENT ON COLUMN memory.memory_tier1.ttl_hours IS 'Time to live in hours before moving to Tier 2';

-- Create memory_tier2 table (Fast, < 100ms)
CREATE TABLE IF NOT EXISTS memory.memory_tier2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    interaction_type VARCHAR(100) NOT NULL,
    interaction_data JSONB NOT NULL,
    summary TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    moved_from_tier1_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ttl_days INTEGER DEFAULT 30
);

CREATE INDEX IF NOT EXISTS idx_memory_tier2_entity_timestamp ON memory.memory_tier2(entity_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memory_tier2_timestamp ON memory.memory_tier2(timestamp);

COMMENT ON TABLE memory.memory_tier2 IS 'Tier 2: Fast memory (< 100ms latency), 7-30 days';
COMMENT ON COLUMN memory.memory_tier2.summary IS 'LLM-generated summary for quick retrieval';
COMMENT ON COLUMN memory.memory_tier2.ttl_days IS 'Time to live in days before moving to Tier 3';

-- Create memory_tier3 table (Semantic, < 500ms)
CREATE TABLE IF NOT EXISTS memory.memory_tier3 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    interaction_type VARCHAR(100) NOT NULL,
    summary TEXT NOT NULL,
    embedding vector(1536),
    importance_score FLOAT DEFAULT 0.5,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    moved_from_tier2_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ttl_days INTEGER DEFAULT 365
);

CREATE INDEX IF NOT EXISTS idx_memory_tier3_entity_timestamp ON memory.memory_tier3(entity_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memory_tier3_timestamp ON memory.memory_tier3(timestamp);
CREATE INDEX IF NOT EXISTS idx_memory_tier3_embedding ON memory.memory_tier3 USING ivfflat (embedding vector_cosine_ops);

COMMENT ON TABLE memory.memory_tier3 IS 'Tier 3: Semantic memory (< 500ms latency), 30-365 days, vector search';
COMMENT ON COLUMN memory.memory_tier3.embedding IS 'Vector embedding for semantic search';
COMMENT ON COLUMN memory.memory_tier3.importance_score IS '0-1 score indicating importance';
COMMENT ON COLUMN memory.memory_tier3.ttl_days IS 'Time to live in days before archiving to Tier 4';

-- Create memory_tier4 table (Archive, > 1s acceptable)
CREATE TABLE IF NOT EXISTS memory.memory_tier4 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    gcs_bucket VARCHAR(255) NOT NULL,
    gcs_path VARCHAR(500) NOT NULL,
    time_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    time_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    record_count INTEGER NOT NULL,
    file_size_bytes INTEGER,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_tier4_entity ON memory.memory_tier4(entity_id);
CREATE INDEX IF NOT EXISTS idx_memory_tier4_period ON memory.memory_tier4(time_period_start, time_period_end);

COMMENT ON TABLE memory.memory_tier4 IS 'Tier 4: Long-term archive (> 1s latency), indefinite retention in GCS';
COMMENT ON COLUMN memory.memory_tier4.gcs_bucket IS 'GCS bucket name';
COMMENT ON COLUMN memory.memory_tier4.gcs_path IS 'Full path to the archived file in GCS';
COMMENT ON COLUMN memory.memory_tier4.record_count IS 'Number of interactions in this archive';
