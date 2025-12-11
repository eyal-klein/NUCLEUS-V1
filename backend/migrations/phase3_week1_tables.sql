-- Migration: Phase 3 Week 1 - Data Ingestion Tables
-- Date: 2025-12-11
-- Purpose: Add tables for health metrics and daily readiness

-- ============================================================================
-- memory.health_metrics - Raw IOT data storage
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory.health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Metric details
    metric_type VARCHAR(50) NOT NULL,  -- sleep_score, hrv, heart_rate, steps, etc.
    value DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(20),  -- bpm, steps, hours, etc.
    
    -- Source tracking
    source VARCHAR(50) NOT NULL,  -- oura, apple_health, garmin, whoop, etc.
    source_id VARCHAR(255),  -- External ID from the source system
    
    -- Temporal
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    CONSTRAINT health_metrics_entity_recorded_idx UNIQUE (entity_id, metric_type, source, recorded_at)
);

CREATE INDEX IF NOT EXISTS idx_health_metrics_entity_id ON memory.health_metrics(entity_id);
CREATE INDEX IF NOT EXISTS idx_health_metrics_recorded_at ON memory.health_metrics(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_health_metrics_type ON memory.health_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_health_metrics_source ON memory.health_metrics(source);

COMMENT ON TABLE memory.health_metrics IS 'Raw health and wellness data from IOT devices';
COMMENT ON COLUMN memory.health_metrics.metric_type IS 'Type of metric: sleep_score, hrv, heart_rate, steps, calories, temperature, etc.';
COMMENT ON COLUMN memory.health_metrics.source IS 'Source device/app: oura, apple_health, garmin, whoop, etc.';

-- ============================================================================
-- dna.daily_readiness - Aggregated daily health scores
-- ============================================================================

CREATE TABLE IF NOT EXISTS dna.daily_readiness (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Date
    date DATE NOT NULL,
    
    -- Composite scores (0-1 scale)
    readiness_score DECIMAL(3, 2),  -- Overall readiness
    sleep_score DECIMAL(3, 2),      -- Sleep quality
    hrv_score DECIMAL(3, 2),        -- HRV balance
    activity_score DECIMAL(3, 2),   -- Activity balance
    recovery_score DECIMAL(3, 2),   -- Recovery status
    
    -- Raw metrics (for reference)
    sleep_hours DECIMAL(4, 2),
    hrv_avg INTEGER,
    resting_heart_rate INTEGER,
    steps INTEGER,
    calories_burned INTEGER,
    
    -- Recommendations
    recommendations JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_data JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT daily_readiness_entity_date_unique UNIQUE (entity_id, date),
    CONSTRAINT daily_readiness_scores_range CHECK (
        readiness_score BETWEEN 0 AND 1 AND
        sleep_score BETWEEN 0 AND 1 AND
        hrv_score BETWEEN 0 AND 1 AND
        activity_score BETWEEN 0 AND 1 AND
        recovery_score BETWEEN 0 AND 1
    )
);

CREATE INDEX IF NOT EXISTS idx_daily_readiness_entity_id ON dna.daily_readiness(entity_id);
CREATE INDEX IF NOT EXISTS idx_daily_readiness_date ON dna.daily_readiness(date DESC);

COMMENT ON TABLE dna.daily_readiness IS 'Daily aggregated health and readiness scores';
COMMENT ON COLUMN dna.daily_readiness.readiness_score IS 'Overall readiness score (0-1): how prepared the entity is for the day';
COMMENT ON COLUMN dna.daily_readiness.recommendations IS 'Array of recommendations based on scores (e.g., "Take it easy today", "Great day for intense work")';

-- ============================================================================
-- dna.energy_patterns - Time-of-day energy analysis
-- ============================================================================

CREATE TABLE IF NOT EXISTS dna.energy_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Time pattern
    hour_of_day INTEGER NOT NULL CHECK (hour_of_day BETWEEN 0 AND 23),
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),  -- NULL means all days
    
    -- Energy metrics
    avg_energy_level DECIMAL(3, 2) NOT NULL CHECK (avg_energy_level BETWEEN 0 AND 1),
    sample_count INTEGER NOT NULL DEFAULT 1,
    
    -- Optimal activities
    optimal_for VARCHAR(50),  -- deep_work, meetings, creative, exercise, rest, etc.
    
    -- Metadata
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    meta_data JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT energy_patterns_entity_time_unique UNIQUE (entity_id, hour_of_day, day_of_week)
);

CREATE INDEX IF NOT EXISTS idx_energy_patterns_entity_id ON dna.energy_patterns(entity_id);
CREATE INDEX IF NOT EXISTS idx_energy_patterns_hour ON dna.energy_patterns(hour_of_day);

COMMENT ON TABLE dna.energy_patterns IS 'Analysis of entity energy levels by time of day and day of week';
COMMENT ON COLUMN dna.energy_patterns.avg_energy_level IS 'Average energy level (0-1) for this time slot';
COMMENT ON COLUMN dna.energy_patterns.optimal_for IS 'What type of activity this time is best suited for';

-- ============================================================================
-- Grant permissions (if needed)
-- ============================================================================

-- Assuming there's a nucleus_app role
-- GRANT SELECT, INSERT, UPDATE, DELETE ON memory.health_metrics TO nucleus_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON dna.daily_readiness TO nucleus_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON dna.energy_patterns TO nucleus_app;
