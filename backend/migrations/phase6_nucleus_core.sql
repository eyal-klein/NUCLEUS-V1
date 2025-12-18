-- ============================================================================
-- NUCLEUS V2.0 - Phase 6: Core Intelligence Schema
-- Creates tables for: Proactive Engagement, Interest Discovery, Self-Evolution,
-- Autonomy Management, Core Principles, and Behavior Monitoring
-- ============================================================================

-- Create the nucleus_core schema
CREATE SCHEMA IF NOT EXISTS nucleus_core;

-- ============================================================================
-- SECTION 1: PROACTIVE ENGAGEMENT ENGINE
-- ============================================================================

-- Triggers that can initiate proactive engagement
CREATE TABLE IF NOT EXISTS nucleus_core.proactive_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Trigger identification
    trigger_type VARCHAR(100) NOT NULL,  -- meeting_approaching, health_change, relationship_decay, goal_stall, opportunity_detected
    trigger_source VARCHAR(100) NOT NULL,  -- calendar, health, social, goals, external
    
    -- Trigger details
    trigger_data JSONB NOT NULL DEFAULT '{}',
    priority VARCHAR(50) NOT NULL DEFAULT 'medium',  -- low, medium, high, critical
    confidence_score FLOAT NOT NULL DEFAULT 0.5,  -- 0.0 to 1.0
    
    -- Context
    context_summary TEXT,
    relevant_dna_elements JSONB DEFAULT '[]',  -- IDs of relevant DNA elements
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, processed, dismissed, expired
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_proactive_triggers_entity ON nucleus_core.proactive_triggers(entity_id);
CREATE INDEX idx_proactive_triggers_status ON nucleus_core.proactive_triggers(status);
CREATE INDEX idx_proactive_triggers_type ON nucleus_core.proactive_triggers(trigger_type);

-- Initiatives generated from triggers
CREATE TABLE IF NOT EXISTS nucleus_core.proactive_initiatives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    trigger_id UUID REFERENCES nucleus_core.proactive_triggers(id) ON DELETE SET NULL,
    
    -- Initiative content
    initiative_type VARCHAR(100) NOT NULL,  -- question, suggestion, reminder, alert
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    
    -- 4 Options Protocol (GI X requirement)
    options JSONB NOT NULL DEFAULT '[]',  -- Array of 4 options: [{id, text, action_type}]
    selected_option_id VARCHAR(50),
    
    -- Timing
    optimal_delivery_time TIMESTAMP WITH TIME ZONE,
    delivery_channel VARCHAR(100) DEFAULT 'app',  -- app, email, sms, push
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, delivered, responded, expired
    delivered_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    
    -- Response tracking
    user_response JSONB,
    response_quality_score FLOAT,  -- 0.0 to 1.0, how useful was this initiative
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_proactive_initiatives_entity ON nucleus_core.proactive_initiatives(entity_id);
CREATE INDEX idx_proactive_initiatives_status ON nucleus_core.proactive_initiatives(status);

-- ============================================================================
-- SECTION 2: INTEREST DISCOVERY ENGINE
-- ============================================================================

-- Raw signals collected for interest discovery
CREATE TABLE IF NOT EXISTS nucleus_core.interest_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Signal source
    signal_source VARCHAR(100) NOT NULL,  -- email, calendar, linkedin, health, conversation
    signal_type VARCHAR(100) NOT NULL,  -- topic_mention, time_spent, engagement, search, action
    
    -- Signal content
    signal_content TEXT NOT NULL,
    extracted_topics JSONB DEFAULT '[]',  -- Array of topics extracted
    sentiment FLOAT,  -- -1.0 to 1.0
    engagement_level FLOAT,  -- 0.0 to 1.0
    
    -- Context
    source_id VARCHAR(255),  -- ID of source record (email_id, event_id, etc.)
    source_timestamp TIMESTAMP WITH TIME ZONE,
    
    -- Processing
    is_processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_interest_signals_entity ON nucleus_core.interest_signals(entity_id);
CREATE INDEX idx_interest_signals_processed ON nucleus_core.interest_signals(is_processed);
CREATE INDEX idx_interest_signals_source ON nucleus_core.interest_signals(signal_source);

-- Candidate interests (before validation)
CREATE TABLE IF NOT EXISTS nucleus_core.interest_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Interest identification
    interest_name VARCHAR(255) NOT NULL,
    interest_category VARCHAR(100),  -- professional, personal, health, social, creative
    interest_description TEXT,
    
    -- Evidence
    supporting_signals JSONB DEFAULT '[]',  -- Array of signal IDs
    signal_count INTEGER DEFAULT 0,
    first_signal_at TIMESTAMP WITH TIME ZONE,
    last_signal_at TIMESTAMP WITH TIME ZONE,
    
    -- Scoring
    confidence_score FLOAT NOT NULL DEFAULT 0.0,  -- 0.0 to 1.0
    consistency_score FLOAT DEFAULT 0.0,  -- How consistent across time
    depth_score FLOAT DEFAULT 0.0,  -- How deep is the engagement
    
    -- Validation
    validation_status VARCHAR(50) DEFAULT 'pending',  -- pending, validated, rejected, merged
    validated_at TIMESTAMP WITH TIME ZONE,
    validation_method VARCHAR(100),  -- auto, user_confirmed, user_rejected
    
    -- If promoted to DNA
    promoted_to_interest_id UUID REFERENCES dna.interests(id) ON DELETE SET NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_interest_candidates_entity ON nucleus_core.interest_candidates(entity_id);
CREATE INDEX idx_interest_candidates_status ON nucleus_core.interest_candidates(validation_status);

-- ============================================================================
-- SECTION 3: SELF-EVOLUTION ENGINE
-- ============================================================================

-- Agent performance feedback for evolution
CREATE TABLE IF NOT EXISTS nucleus_core.evolution_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES assembly.agents(id) ON DELETE SET NULL,
    
    -- Task context
    task_id UUID,
    task_type VARCHAR(100),
    task_description TEXT,
    
    -- Performance metrics
    success BOOLEAN,
    execution_time_ms INTEGER,
    token_usage INTEGER,
    
    -- Feedback
    feedback_source VARCHAR(50) NOT NULL,  -- user, system, llm_judge
    feedback_type VARCHAR(50) NOT NULL,  -- rating, correction, preference
    feedback_score FLOAT,  -- 0.0 to 1.0
    feedback_text TEXT,
    
    -- What went wrong/right
    failure_reason TEXT,
    success_factors JSONB DEFAULT '[]',
    
    -- Timestamps
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_evolution_feedback_entity ON nucleus_core.evolution_feedback(entity_id);
CREATE INDEX idx_evolution_feedback_agent ON nucleus_core.evolution_feedback(agent_id);

-- Evolution cycles (RLAIF pattern)
CREATE TABLE IF NOT EXISTS nucleus_core.evolution_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Target
    target_type VARCHAR(50) NOT NULL,  -- agent, prompt, workflow
    target_id UUID NOT NULL,
    
    -- Cycle details
    cycle_number INTEGER NOT NULL DEFAULT 1,
    
    -- Before state
    baseline_prompt TEXT,
    baseline_score FLOAT,
    
    -- Feedback batch
    feedback_ids JSONB DEFAULT '[]',  -- Array of evolution_feedback IDs used
    feedback_summary TEXT,
    
    -- LLM Judge evaluation
    judge_evaluation JSONB,  -- {score, reasoning, suggestions}
    
    -- Meta-prompted improvements
    suggested_improvements JSONB DEFAULT '[]',
    
    -- After state
    updated_prompt TEXT,
    updated_score FLOAT,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, evaluating, improving, completed, failed
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_evolution_cycles_target ON nucleus_core.evolution_cycles(target_type, target_id);
CREATE INDEX idx_evolution_cycles_status ON nucleus_core.evolution_cycles(status);

-- ============================================================================
-- SECTION 4: AUTONOMY LEVEL MANAGEMENT
-- ============================================================================

-- Entity autonomy configuration
CREATE TABLE IF NOT EXISTS nucleus_core.autonomy_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Current level (based on Datasaur 5-level framework)
    current_level INTEGER NOT NULL DEFAULT 2,  -- 1-5
    current_level_name VARCHAR(100) NOT NULL DEFAULT 'Preparatory Agent',
    autonomy_percentage INTEGER NOT NULL DEFAULT 30,  -- 30, 50, 75, 95
    
    -- Level thresholds
    level_thresholds JSONB DEFAULT '{
        "1": {"name": "Deterministic Task Bot", "percentage": 10, "min_score": 0},
        "2": {"name": "Preparatory Agent", "percentage": 30, "min_score": 0.5},
        "3": {"name": "Narrow Operator", "percentage": 50, "min_score": 0.7},
        "4": {"name": "Semi-Autonomous Specialist", "percentage": 75, "min_score": 0.85},
        "5": {"name": "Autonomous Problem Solver", "percentage": 95, "min_score": 0.95}
    }',
    
    -- Performance metrics for level transitions
    precision_at_3 FLOAT DEFAULT 0.0,  -- Top-3 suggestions relevance
    coherence_score FLOAT DEFAULT 0.0,  -- Actions aligned with DNA
    trust_score FLOAT DEFAULT 0.0,  -- User trust level
    
    -- Permissions at current level
    allowed_actions JSONB DEFAULT '[]',
    requires_approval JSONB DEFAULT '[]',
    forbidden_actions JSONB DEFAULT '[]',
    
    -- Budget/limits
    daily_action_limit INTEGER DEFAULT 10,
    spending_limit_usd FLOAT DEFAULT 0.0,
    
    -- Timestamps
    level_achieved_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_evaluated_at TIMESTAMP WITH TIME ZONE,
    next_evaluation_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE UNIQUE INDEX idx_autonomy_levels_entity ON nucleus_core.autonomy_levels(entity_id);

-- Autonomy level transitions history
CREATE TABLE IF NOT EXISTS nucleus_core.autonomy_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Transition details
    from_level INTEGER NOT NULL,
    to_level INTEGER NOT NULL,
    from_percentage INTEGER NOT NULL,
    to_percentage INTEGER NOT NULL,
    
    -- Reason
    transition_reason TEXT NOT NULL,
    evaluation_summary JSONB,  -- Metrics that triggered the transition
    
    -- Approval
    auto_approved BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(100),  -- 'system' or user identifier
    
    -- Timestamps
    transitioned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_autonomy_transitions_entity ON nucleus_core.autonomy_transitions(entity_id);

-- ============================================================================
-- SECTION 5: CORE PRINCIPLES ENFORCEMENT
-- ============================================================================

-- Core principles definition
CREATE TABLE IF NOT EXISTS nucleus_core.core_principles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Principle identification
    principle_code VARCHAR(50) NOT NULL UNIQUE,  -- P1, P2, etc.
    principle_name VARCHAR(255) NOT NULL,
    principle_description TEXT NOT NULL,
    
    -- Priority and enforcement
    priority INTEGER NOT NULL DEFAULT 1,  -- 1 = highest
    enforcement_level VARCHAR(50) NOT NULL DEFAULT 'strict',  -- strict, moderate, advisory
    
    -- Validation rules
    validation_prompt TEXT,  -- Prompt for LLM to check compliance
    validation_examples JSONB DEFAULT '[]',  -- Examples of compliant/non-compliant actions
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

-- Principle violations log
CREATE TABLE IF NOT EXISTS nucleus_core.principle_violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    principle_id UUID NOT NULL REFERENCES nucleus_core.core_principles(id) ON DELETE CASCADE,
    
    -- Violation details
    action_type VARCHAR(100) NOT NULL,
    action_description TEXT NOT NULL,
    violation_severity VARCHAR(50) NOT NULL,  -- minor, moderate, severe
    
    -- Context
    agent_id UUID REFERENCES assembly.agents(id) ON DELETE SET NULL,
    task_id UUID,
    
    -- Resolution
    was_blocked BOOLEAN DEFAULT FALSE,
    resolution_action TEXT,
    
    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_principle_violations_entity ON nucleus_core.principle_violations(entity_id);
CREATE INDEX idx_principle_violations_principle ON nucleus_core.principle_violations(principle_id);

-- ============================================================================
-- SECTION 6: BEHAVIOR MONITORING
-- ============================================================================

-- Agent behavior tracking
CREATE TABLE IF NOT EXISTS nucleus_core.behavior_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES assembly.agents(id) ON DELETE SET NULL,
    
    -- Action details
    action_type VARCHAR(100) NOT NULL,
    action_description TEXT,
    action_input JSONB,
    action_output JSONB,
    
    -- Performance
    execution_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    
    -- Alignment checks
    dna_alignment_score FLOAT,  -- 0.0 to 1.0
    principle_compliance BOOLEAN DEFAULT TRUE,
    
    -- Anomaly detection
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_type VARCHAR(100),
    anomaly_score FLOAT,
    
    -- Timestamps
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_behavior_logs_entity ON nucleus_core.behavior_logs(entity_id);
CREATE INDEX idx_behavior_logs_agent ON nucleus_core.behavior_logs(agent_id);
CREATE INDEX idx_behavior_logs_anomaly ON nucleus_core.behavior_logs(is_anomaly);

-- Behavior drift detection
CREATE TABLE IF NOT EXISTS nucleus_core.behavior_drift (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES assembly.agents(id) ON DELETE SET NULL,
    
    -- Drift details
    drift_type VARCHAR(100) NOT NULL,  -- performance, alignment, pattern
    drift_description TEXT NOT NULL,
    
    -- Metrics
    baseline_metric FLOAT,
    current_metric FLOAT,
    drift_magnitude FLOAT,  -- Percentage change
    
    -- Time window
    detection_window_start TIMESTAMP WITH TIME ZONE,
    detection_window_end TIMESTAMP WITH TIME ZONE,
    sample_count INTEGER,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'detected',  -- detected, investigating, resolved, false_positive
    resolution_action TEXT,
    
    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_behavior_drift_entity ON nucleus_core.behavior_drift(entity_id);
CREATE INDEX idx_behavior_drift_status ON nucleus_core.behavior_drift(status);

-- ============================================================================
-- SECTION 7: DOMAIN MANAGEMENT
-- ============================================================================

-- Domains (Kingdoms) for entity
CREATE TABLE IF NOT EXISTS nucleus_core.domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Domain identification
    domain_name VARCHAR(255) NOT NULL,
    domain_type VARCHAR(100) NOT NULL,  -- work, health, relationships, finance, personal_growth, etc.
    domain_description TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 5,  -- 1-10
    
    -- Associated elements
    associated_goals JSONB DEFAULT '[]',  -- Goal IDs
    associated_interests JSONB DEFAULT '[]',  -- Interest IDs
    associated_relationships JSONB DEFAULT '[]',  -- Relationship IDs
    
    -- Domain-specific agent
    domain_agent_id UUID REFERENCES assembly.agents(id) ON DELETE SET NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_domains_entity ON nucleus_core.domains(entity_id);

-- Domain knowledge library
CREATE TABLE IF NOT EXISTS nucleus_core.domain_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES nucleus_core.domains(id) ON DELETE CASCADE,
    
    -- Knowledge item
    knowledge_type VARCHAR(100) NOT NULL,  -- principle, best_practice, lesson_learned, resource
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    
    -- Source
    source_type VARCHAR(100),  -- user_input, discovered, imported
    source_reference TEXT,
    
    -- Relevance
    relevance_score FLOAT DEFAULT 0.5,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_domain_knowledge_domain ON nucleus_core.domain_knowledge(domain_id);

-- ============================================================================
-- SECTION 8: RELATIONSHIP BUILDING (Private Language)
-- ============================================================================

-- Private language elements
CREATE TABLE IF NOT EXISTS nucleus_core.private_language (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Language element
    element_type VARCHAR(100) NOT NULL,  -- nickname, shortcut, reference, inside_joke
    element_key VARCHAR(255) NOT NULL,  -- The shorthand/nickname
    element_meaning TEXT NOT NULL,  -- What it means
    
    -- Context
    origin_context TEXT,  -- How this element was established
    usage_examples JSONB DEFAULT '[]',
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_private_language_entity ON nucleus_core.private_language(entity_id);
CREATE UNIQUE INDEX idx_private_language_key ON nucleus_core.private_language(entity_id, element_key);

-- ============================================================================
-- SECTION 9: AGENT TESTBED
-- ============================================================================

-- Test scenarios for agents
CREATE TABLE IF NOT EXISTS nucleus_core.test_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Scenario identification
    scenario_name VARCHAR(255) NOT NULL,
    scenario_type VARCHAR(100) NOT NULL,  -- unit, integration, edge_case, stress
    scenario_description TEXT,
    
    -- Test configuration
    input_data JSONB NOT NULL,
    expected_output JSONB,
    validation_rules JSONB DEFAULT '[]',
    
    -- Target
    target_agent_type VARCHAR(100),  -- Which type of agent this tests
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

-- Test results
CREATE TABLE IF NOT EXISTS nucleus_core.test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES nucleus_core.test_scenarios(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES assembly.agents(id) ON DELETE SET NULL,
    
    -- Result
    passed BOOLEAN NOT NULL,
    actual_output JSONB,
    error_message TEXT,
    
    -- Performance
    execution_time_ms INTEGER,
    
    -- Validation details
    validation_results JSONB DEFAULT '[]',  -- Per-rule results
    
    -- Timestamps
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_test_results_scenario ON nucleus_core.test_results(scenario_id);
CREATE INDEX idx_test_results_agent ON nucleus_core.test_results(agent_id);

-- ============================================================================
-- SECTION 10: WELLBEING GUARDIAN
-- ============================================================================

-- Wellbeing checks
CREATE TABLE IF NOT EXISTS nucleus_core.wellbeing_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES dna.entity(id) ON DELETE CASCADE,
    
    -- Check type
    check_type VARCHAR(100) NOT NULL,  -- cognitive_load, emotional_state, burnout_risk
    
    -- Metrics
    score FLOAT NOT NULL,  -- 0.0 to 1.0
    indicators JSONB DEFAULT '[]',  -- What contributed to this score
    
    -- Recommendations
    recommendations JSONB DEFAULT '[]',
    
    -- Status
    requires_attention BOOLEAN DEFAULT FALSE,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    checked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Metadata
    meta_data JSONB DEFAULT '{}'
);

CREATE INDEX idx_wellbeing_checks_entity ON nucleus_core.wellbeing_checks(entity_id);
CREATE INDEX idx_wellbeing_checks_attention ON nucleus_core.wellbeing_checks(requires_attention);

-- ============================================================================
-- Insert default core principles (6 principles from GI X document)
-- ============================================================================

INSERT INTO nucleus_core.core_principles (principle_code, principle_name, principle_description, priority, enforcement_level) VALUES
('P1', 'Authentic Interest Alignment', 'All actions must align with the entity''s authentic interests, not assumed or projected interests. Never act on interests that haven''t been validated.', 1, 'strict'),
('P2', 'Proactive Value Creation', 'Actively seek opportunities to create value for the entity. Don''t wait to be asked - anticipate needs and offer solutions.', 2, 'strict'),
('P3', 'Transparent Decision Making', 'All decisions must be explainable. The entity should always understand why an action was taken or recommended.', 3, 'strict'),
('P4', 'Respect for Autonomy', 'Respect the entity''s autonomy and right to make their own decisions. Provide options, not mandates.', 4, 'strict'),
('P5', 'Continuous Learning', 'Continuously learn from interactions and feedback. Improve over time based on what works for this specific entity.', 5, 'moderate'),
('P6', 'Wellbeing Protection', 'Protect the entity''s cognitive and emotional wellbeing. Avoid overwhelming, manipulating, or creating dependency.', 6, 'strict')
ON CONFLICT (principle_code) DO NOTHING;

-- ============================================================================
-- Grant permissions
-- ============================================================================

GRANT ALL ON SCHEMA nucleus_core TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA nucleus_core TO postgres;
