-- ============================================================================
-- NUCLEUS Phase 3 - Week 4: Apple Watch & Real-Time Health
-- Database Migration Script
-- ============================================================================

-- 1. Apple Watch Metrics Table
CREATE TABLE IF NOT EXISTS memory.apple_watch_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10,2) NOT NULL,
    metric_unit VARCHAR(20),
    activity_state VARCHAR(50),
    device_name VARCHAR(100),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_app VARCHAR(100),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_apple_watch_metrics_entity_id ON memory.apple_watch_metrics(entity_id);
CREATE INDEX IF NOT EXISTS idx_apple_watch_metrics_type ON memory.apple_watch_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_apple_watch_metrics_recorded_at ON memory.apple_watch_metrics(recorded_at DESC);

COMMENT ON TABLE memory.apple_watch_metrics IS 'Real-time Apple Watch health metrics';

-- 2. Workout Sessions Table
CREATE TABLE IF NOT EXISTS memory.workout_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    workout_type VARCHAR(50),
    duration_minutes INTEGER,
    distance_km DECIMAL(10,2),
    calories_burned INTEGER,
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    heart_rate_zones JSONB DEFAULT '{}'::jsonb,
    avg_pace DECIMAL(10,2),
    elevation_gain INTEGER,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    route_data JSONB DEFAULT '{}'::jsonb,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workout_sessions_entity_id ON memory.workout_sessions(entity_id);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_type ON memory.workout_sessions(workout_type);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_started_at ON memory.workout_sessions(started_at DESC);

COMMENT ON TABLE memory.workout_sessions IS 'Workout and exercise sessions from Apple Watch';

-- 3. Stress Events Table
CREATE TABLE IF NOT EXISTS dna.stress_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    stress_level INTEGER CHECK (stress_level >= 0 AND stress_level <= 100),
    stress_category VARCHAR(20),
    heart_rate INTEGER,
    hrv_value DECIMAL(10,2),
    activity_level VARCHAR(50),
    detected_triggers JSONB DEFAULT '[]'::jsonb,
    context_notes TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    recovery_actions JSONB DEFAULT '[]'::jsonb,
    recovery_time_minutes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stress_events_entity_id ON dna.stress_events(entity_id);
CREATE INDEX IF NOT EXISTS idx_stress_events_level ON dna.stress_events(stress_level DESC);
CREATE INDEX IF NOT EXISTS idx_stress_events_started_at ON dna.stress_events(started_at DESC);

COMMENT ON TABLE dna.stress_events IS 'Detected stress events and patterns';

-- 4. Health Baselines Table
CREATE TABLE IF NOT EXISTS dna.health_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    resting_heart_rate_avg DECIMAL(5,2),
    resting_heart_rate_std DECIMAL(5,2),
    max_heart_rate_avg DECIMAL(5,2),
    hrv_avg DECIMAL(10,2),
    hrv_std DECIMAL(10,2),
    daily_steps_avg INTEGER,
    daily_calories_avg INTEGER,
    active_minutes_avg INTEGER,
    sleep_duration_avg DECIMAL(4,2),
    sleep_quality_avg DECIMAL(3,2),
    baseline_start_date DATE,
    baseline_end_date DATE,
    data_points_count INTEGER,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT health_baselines_entity_unique UNIQUE (entity_id)
);

CREATE INDEX IF NOT EXISTS idx_health_baselines_entity_id ON dna.health_baselines(entity_id);

COMMENT ON TABLE dna.health_baselines IS 'Personal health baselines for comparison';

-- 5. Wellness Scores Table
CREATE TABLE IF NOT EXISTS dna.wellness_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    wellness_score INTEGER CHECK (wellness_score >= 0 AND wellness_score <= 100),
    activity_score INTEGER,
    sleep_score INTEGER,
    recovery_score INTEGER,
    stress_score INTEGER,
    consistency_score INTEGER,
    heart_rate_variability DECIMAL(10,2),
    resting_heart_rate INTEGER,
    sleep_hours DECIMAL(4,2),
    active_minutes INTEGER,
    steps_count INTEGER,
    recommendations JSONB DEFAULT '[]'::jsonb,
    insights TEXT,
    score_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT wellness_scores_entity_date_unique UNIQUE (entity_id, score_date)
);

CREATE INDEX IF NOT EXISTS idx_wellness_scores_entity_id ON dna.wellness_scores(entity_id);
CREATE INDEX IF NOT EXISTS idx_wellness_scores_date ON dna.wellness_scores(score_date DESC);
CREATE INDEX IF NOT EXISTS idx_wellness_scores_score ON dna.wellness_scores(wellness_score DESC);

COMMENT ON TABLE dna.wellness_scores IS 'Daily wellness scores and insights';

-- Verification
SELECT schemaname, tablename FROM pg_tables 
WHERE schemaname IN ('memory', 'dna') 
AND tablename IN ('apple_watch_metrics', 'workout_sessions', 'stress_events', 'health_baselines', 'wellness_scores')
ORDER BY schemaname, tablename;
