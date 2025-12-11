-- Migration 005: Add Extended DNA Tables (V2.0)
-- Description: Create 14 additional DNA tables for comprehensive entity profiling
-- Date: 2025-12-11

-- Personality Traits
CREATE TABLE IF NOT EXISTS dna.personality_traits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    trait_name VARCHAR(255) NOT NULL,
    trait_value FLOAT NOT NULL CHECK (trait_value >= 0.0 AND trait_value <= 1.0),
    trait_description TEXT,
    confidence_score FLOAT DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    first_detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evidence_count INTEGER DEFAULT 0
);

CREATE INDEX idx_personality_traits_entity ON dna.personality_traits(entity_id);
CREATE INDEX idx_personality_traits_name ON dna.personality_traits(trait_name);

-- Communication Styles
CREATE TABLE IF NOT EXISTS dna.communication_styles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    style_name VARCHAR(255) NOT NULL,
    style_description TEXT,
    frequency_score FLOAT DEFAULT 0.0 CHECK (frequency_score >= 0.0 AND frequency_score <= 1.0),
    preferred_channels TEXT[],
    tone_preferences JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_communication_styles_entity ON dna.communication_styles(entity_id);

-- Decision Patterns
CREATE TABLE IF NOT EXISTS dna.decision_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    pattern_name VARCHAR(255) NOT NULL,
    pattern_description TEXT,
    confidence_score FLOAT DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    decision_context VARCHAR(255),
    typical_factors JSONB,
    typical_timeframe VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_decision_patterns_entity ON dna.decision_patterns(entity_id);
CREATE INDEX idx_decision_patterns_context ON dna.decision_patterns(decision_context);

-- Work Habits
CREATE TABLE IF NOT EXISTS dna.work_habits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    habit_name VARCHAR(255) NOT NULL,
    habit_description TEXT,
    frequency VARCHAR(100),
    peak_productivity_times TEXT[],
    preferred_work_environment JSONB,
    task_management_style VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_work_habits_entity ON dna.work_habits(entity_id);

-- Relationships
CREATE TABLE IF NOT EXISTS dna.relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    related_entity_id UUID,
    related_name VARCHAR(255) NOT NULL,
    relationship_type VARCHAR(100) NOT NULL,
    relationship_strength FLOAT DEFAULT 0.5 CHECK (relationship_strength >= 0.0 AND relationship_strength <= 1.0),
    interaction_frequency VARCHAR(100),
    relationship_context TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_relationships_entity ON dna.relationships(entity_id);
CREATE INDEX idx_relationships_type ON dna.relationships(relationship_type);

-- Skills
CREATE TABLE IF NOT EXISTS dna.skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    skill_name VARCHAR(255) NOT NULL,
    skill_category VARCHAR(100),
    proficiency_level FLOAT NOT NULL CHECK (proficiency_level >= 0.0 AND proficiency_level <= 1.0),
    skill_description TEXT,
    years_of_experience FLOAT,
    last_used_at TIMESTAMP WITH TIME ZONE,
    is_actively_developing BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_skills_entity ON dna.skills(entity_id);
CREATE INDEX idx_skills_category ON dna.skills(skill_category);
CREATE INDEX idx_skills_proficiency ON dna.skills(proficiency_level);

-- Preferences
CREATE TABLE IF NOT EXISTS dna.preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    preference_category VARCHAR(100) NOT NULL,
    preference_name VARCHAR(255) NOT NULL,
    preference_value TEXT,
    strength FLOAT DEFAULT 0.5 CHECK (strength >= 0.0 AND strength <= 1.0),
    context VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_preferences_entity ON dna.preferences(entity_id);
CREATE INDEX idx_preferences_category ON dna.preferences(preference_category);

-- Constraints
CREATE TABLE IF NOT EXISTS dna.constraints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    constraint_type VARCHAR(100) NOT NULL,
    constraint_name VARCHAR(255) NOT NULL,
    constraint_description TEXT,
    severity VARCHAR(50),
    impact_areas TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_constraints_entity ON dna.constraints(entity_id);
CREATE INDEX idx_constraints_type ON dna.constraints(constraint_type);
CREATE INDEX idx_constraints_active ON dna.constraints(is_active);

-- Beliefs
CREATE TABLE IF NOT EXISTS dna.beliefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    belief_category VARCHAR(100),
    belief_statement TEXT NOT NULL,
    conviction_strength FLOAT DEFAULT 0.5 CHECK (conviction_strength >= 0.0 AND conviction_strength <= 1.0),
    origin_context TEXT,
    influences_decisions BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_beliefs_entity ON dna.beliefs(entity_id);
CREATE INDEX idx_beliefs_category ON dna.beliefs(belief_category);

-- Experiences
CREATE TABLE IF NOT EXISTS dna.experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    experience_title VARCHAR(500) NOT NULL,
    experience_description TEXT,
    experience_category VARCHAR(100),
    impact_level FLOAT DEFAULT 0.5 CHECK (impact_level >= 0.0 AND impact_level <= 1.0),
    lessons_learned TEXT[],
    skills_gained TEXT[],
    occurred_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_experiences_entity ON dna.experiences(entity_id);
CREATE INDEX idx_experiences_category ON dna.experiences(experience_category);
CREATE INDEX idx_experiences_impact ON dna.experiences(impact_level);

-- Emotions
CREATE TABLE IF NOT EXISTS dna.emotions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    emotion_name VARCHAR(100) NOT NULL,
    emotion_intensity FLOAT DEFAULT 0.5 CHECK (emotion_intensity >= 0.0 AND emotion_intensity <= 1.0),
    trigger_context TEXT,
    typical_response TEXT,
    frequency VARCHAR(100),
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_emotions_entity ON dna.emotions(entity_id);
CREATE INDEX idx_emotions_name ON dna.emotions(emotion_name);

-- Routines
CREATE TABLE IF NOT EXISTS dna.routines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    routine_name VARCHAR(255) NOT NULL,
    routine_description TEXT,
    routine_type VARCHAR(100),
    time_of_day VARCHAR(100),
    typical_duration INTEGER,
    consistency_score FLOAT DEFAULT 0.5 CHECK (consistency_score >= 0.0 AND consistency_score <= 1.0),
    purpose TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_routines_entity ON dna.routines(entity_id);
CREATE INDEX idx_routines_type ON dna.routines(routine_type);
CREATE INDEX idx_routines_active ON dna.routines(is_active);

-- Contexts
CREATE TABLE IF NOT EXISTS dna.contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    context_name VARCHAR(255) NOT NULL,
    context_description TEXT,
    typical_behaviors JSONB,
    typical_goals TEXT[],
    typical_constraints TEXT[],
    frequency VARCHAR(100),
    last_active_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_contexts_entity ON dna.contexts(entity_id);
CREATE INDEX idx_contexts_name ON dna.contexts(context_name);

-- Evolution History
CREATE TABLE IF NOT EXISTS dna.evolution_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    evolution_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    change_type VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    confidence_delta FLOAT,
    source_memory_ids UUID[],
    distillation_run_id UUID
);

CREATE INDEX idx_evolution_history_entity ON dna.evolution_history(entity_id);
CREATE INDEX idx_evolution_history_date ON dna.evolution_history(evolution_date);
CREATE INDEX idx_evolution_history_table ON dna.evolution_history(table_name);
CREATE INDEX idx_evolution_history_run ON dna.evolution_history(distillation_run_id);

-- Record migration
INSERT INTO public.migrations (migration_name, applied_at)
VALUES ('005_add_extended_dna_tables', NOW())
ON CONFLICT (migration_name) DO NOTHING;

-- Migration complete
