"""
NUCLEUS V2.0 - Core Intelligence Schema Models
Models for: Proactive Engagement, Interest Discovery, Self-Evolution,
Autonomy Management, Core Principles, Behavior Monitoring, Domain Management
"""

from sqlalchemy import Column, String, Text, Float, Boolean, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


# ============================================================================
# SECTION 1: PROACTIVE ENGAGEMENT ENGINE
# ============================================================================

class ProactiveTrigger(Base):
    """Triggers that can initiate proactive engagement"""
    __tablename__ = "proactive_triggers"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    
    # Trigger identification
    trigger_type = Column(String(100), nullable=False)  # meeting_approaching, health_change, etc.
    trigger_source = Column(String(100), nullable=False)  # calendar, health, social, goals
    
    # Trigger details
    trigger_data = Column(JSONB, nullable=False, default={})
    priority = Column(String(50), nullable=False, default="medium")
    confidence_score = Column(Float, nullable=False, default=0.5)
    
    # Context
    context_summary = Column(Text)
    relevant_dna_elements = Column(JSONB, default=[])
    
    # Status
    status = Column(String(50), nullable=False, default="pending")
    processed_at = Column(TIMESTAMP(timezone=True))
    
    # Timestamps
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True))
    
    # Metadata
    meta_data = Column(JSONB, default={})
    
    # Relationships
    initiatives = relationship("ProactiveInitiative", back_populates="trigger", cascade="all, delete-orphan")


class ProactiveInitiative(Base):
    """Initiatives generated from triggers - implements 4 Options Protocol"""
    __tablename__ = "proactive_initiatives"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    trigger_id = Column(UUID(as_uuid=True), ForeignKey("nucleus_core.proactive_triggers.id", ondelete="SET NULL"))
    
    # Initiative content
    initiative_type = Column(String(100), nullable=False)  # question, suggestion, reminder, alert
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    
    # 4 Options Protocol
    options = Column(JSONB, nullable=False, default=[])  # [{id, text, action_type}]
    selected_option_id = Column(String(50))
    
    # Timing
    optimal_delivery_time = Column(TIMESTAMP(timezone=True))
    delivery_channel = Column(String(100), default="app")
    
    # Status
    status = Column(String(50), nullable=False, default="pending")
    delivered_at = Column(TIMESTAMP(timezone=True))
    responded_at = Column(TIMESTAMP(timezone=True))
    
    # Response tracking
    user_response = Column(JSONB)
    response_quality_score = Column(Float)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True))
    
    # Metadata
    meta_data = Column(JSONB, default={})
    
    # Relationships
    trigger = relationship("ProactiveTrigger", back_populates="initiatives")


# ============================================================================
# SECTION 2: INTEREST DISCOVERY ENGINE
# ============================================================================

class InterestSignal(Base):
    """Raw signals collected for interest discovery"""
    __tablename__ = "interest_signals"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    
    # Signal source
    signal_source = Column(String(100), nullable=False)  # email, calendar, linkedin, health
    signal_type = Column(String(100), nullable=False)  # topic_mention, time_spent, engagement
    
    # Signal content
    signal_content = Column(Text, nullable=False)
    extracted_topics = Column(JSONB, default=[])
    sentiment = Column(Float)  # -1.0 to 1.0
    engagement_level = Column(Float)  # 0.0 to 1.0
    
    # Context
    source_id = Column(String(255))
    source_timestamp = Column(TIMESTAMP(timezone=True))
    
    # Processing
    is_processed = Column(Boolean, default=False)
    processed_at = Column(TIMESTAMP(timezone=True))
    
    # Timestamps
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})


class InterestCandidate(Base):
    """Candidate interests before validation"""
    __tablename__ = "interest_candidates"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    
    # Interest identification
    interest_name = Column(String(255), nullable=False)
    interest_category = Column(String(100))
    interest_description = Column(Text)
    
    # Evidence
    supporting_signals = Column(JSONB, default=[])
    signal_count = Column(Integer, default=0)
    first_signal_at = Column(TIMESTAMP(timezone=True))
    last_signal_at = Column(TIMESTAMP(timezone=True))
    
    # Scoring
    confidence_score = Column(Float, nullable=False, default=0.0)
    consistency_score = Column(Float, default=0.0)
    depth_score = Column(Float, default=0.0)
    
    # Validation
    validation_status = Column(String(50), default="pending")
    validated_at = Column(TIMESTAMP(timezone=True))
    validation_method = Column(String(100))
    
    # If promoted to DNA
    promoted_to_interest_id = Column(UUID(as_uuid=True), ForeignKey("dna.interests.id", ondelete="SET NULL"))
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})


# ============================================================================
# SECTION 3: SELF-EVOLUTION ENGINE
# ============================================================================

class EvolutionFeedback(Base):
    """Agent performance feedback for evolution"""
    __tablename__ = "evolution_feedback"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("assembly.agents.id", ondelete="SET NULL"))
    
    # Task context
    task_id = Column(UUID(as_uuid=True))
    task_type = Column(String(100))
    task_description = Column(Text)
    
    # Performance metrics
    success = Column(Boolean)
    execution_time_ms = Column(Integer)
    token_usage = Column(Integer)
    
    # Feedback
    feedback_source = Column(String(50), nullable=False)  # user, system, llm_judge
    feedback_type = Column(String(50), nullable=False)  # rating, correction, preference
    feedback_score = Column(Float)
    feedback_text = Column(Text)
    
    # What went wrong/right
    failure_reason = Column(Text)
    success_factors = Column(JSONB, default=[])
    
    # Timestamps
    recorded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})


class EvolutionCycle(Base):
    """Evolution cycles using RLAIF pattern"""
    __tablename__ = "evolution_cycles"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Target
    target_type = Column(String(50), nullable=False)  # agent, prompt, workflow
    target_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Cycle details
    cycle_number = Column(Integer, nullable=False, default=1)
    
    # Before state
    baseline_prompt = Column(Text)
    baseline_score = Column(Float)
    
    # Feedback batch
    feedback_ids = Column(JSONB, default=[])
    feedback_summary = Column(Text)
    
    # LLM Judge evaluation
    judge_evaluation = Column(JSONB)
    
    # Meta-prompted improvements
    suggested_improvements = Column(JSONB, default=[])
    
    # After state
    updated_prompt = Column(Text)
    updated_score = Column(Float)
    
    # Status
    status = Column(String(50), nullable=False, default="pending")
    
    # Timestamps
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))
    
    # Metadata
    meta_data = Column(JSONB, default={})


# ============================================================================
# SECTION 4: AUTONOMY LEVEL MANAGEMENT
# ============================================================================

class AutonomyLevel(Base):
    """Entity autonomy configuration"""
    __tablename__ = "autonomy_levels"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Current level (5-level framework)
    current_level = Column(Integer, nullable=False, default=2)
    current_level_name = Column(String(100), nullable=False, default="Preparatory Agent")
    autonomy_percentage = Column(Integer, nullable=False, default=30)
    
    # Level thresholds
    level_thresholds = Column(JSONB, default={
        "1": {"name": "Deterministic Task Bot", "percentage": 10, "min_score": 0},
        "2": {"name": "Preparatory Agent", "percentage": 30, "min_score": 0.5},
        "3": {"name": "Narrow Operator", "percentage": 50, "min_score": 0.7},
        "4": {"name": "Semi-Autonomous Specialist", "percentage": 75, "min_score": 0.85},
        "5": {"name": "Autonomous Problem Solver", "percentage": 95, "min_score": 0.95}
    })
    
    # Performance metrics
    precision_at_3 = Column(Float, default=0.0)
    coherence_score = Column(Float, default=0.0)
    trust_score = Column(Float, default=0.0)
    
    # Permissions
    allowed_actions = Column(JSONB, default=[])
    requires_approval = Column(JSONB, default=[])
    forbidden_actions = Column(JSONB, default=[])
    
    # Budget/limits
    daily_action_limit = Column(Integer, default=10)
    spending_limit_usd = Column(Float, default=0.0)
    
    # Timestamps
    level_achieved_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_evaluated_at = Column(TIMESTAMP(timezone=True))
    next_evaluation_at = Column(TIMESTAMP(timezone=True))
    
    # Metadata
    meta_data = Column(JSONB, default={})


class AutonomyTransition(Base):
    """Autonomy level transitions history"""
    __tablename__ = "autonomy_transitions"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    
    # Transition details
    from_level = Column(Integer, nullable=False)
    to_level = Column(Integer, nullable=False)
    from_percentage = Column(Integer, nullable=False)
    to_percentage = Column(Integer, nullable=False)
    
    # Reason
    transition_reason = Column(Text, nullable=False)
    evaluation_summary = Column(JSONB)
    
    # Approval
    auto_approved = Column(Boolean, default=False)
    approved_by = Column(String(100))
    
    # Timestamps
    transitioned_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})


# ============================================================================
# SECTION 5: CORE PRINCIPLES ENFORCEMENT
# ============================================================================

class CorePrinciple(Base):
    """Core principles definition"""
    __tablename__ = "core_principles"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Principle identification
    principle_code = Column(String(50), nullable=False, unique=True)
    principle_name = Column(String(255), nullable=False)
    principle_description = Column(Text, nullable=False)
    
    # Priority and enforcement
    priority = Column(Integer, nullable=False, default=1)
    enforcement_level = Column(String(50), nullable=False, default="strict")
    
    # Validation rules
    validation_prompt = Column(Text)
    validation_examples = Column(JSONB, default=[])
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})
    
    # Relationships
    violations = relationship("PrincipleViolation", back_populates="principle", cascade="all, delete-orphan")


class PrincipleViolation(Base):
    """Principle violations log"""
    __tablename__ = "principle_violations"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    principle_id = Column(UUID(as_uuid=True), ForeignKey("nucleus_core.core_principles.id", ondelete="CASCADE"), nullable=False)
    
    # Violation details
    action_type = Column(String(100), nullable=False)
    action_description = Column(Text, nullable=False)
    violation_severity = Column(String(50), nullable=False)
    
    # Context
    agent_id = Column(UUID(as_uuid=True), ForeignKey("assembly.agents.id", ondelete="SET NULL"))
    task_id = Column(UUID(as_uuid=True))
    
    # Resolution
    was_blocked = Column(Boolean, default=False)
    resolution_action = Column(Text)
    
    # Timestamps
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    resolved_at = Column(TIMESTAMP(timezone=True))
    
    # Metadata
    meta_data = Column(JSONB, default={})
    
    # Relationships
    principle = relationship("CorePrinciple", back_populates="violations")


# ============================================================================
# SECTION 6: BEHAVIOR MONITORING
# ============================================================================

class BehaviorLog(Base):
    """Agent behavior tracking"""
    __tablename__ = "behavior_logs"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("assembly.agents.id", ondelete="SET NULL"))
    
    # Action details
    action_type = Column(String(100), nullable=False)
    action_description = Column(Text)
    action_input = Column(JSONB)
    action_output = Column(JSONB)
    
    # Performance
    execution_time_ms = Column(Integer)
    success = Column(Boolean)
    error_message = Column(Text)
    
    # Alignment checks
    dna_alignment_score = Column(Float)
    principle_compliance = Column(Boolean, default=True)
    
    # Anomaly detection
    is_anomaly = Column(Boolean, default=False)
    anomaly_type = Column(String(100))
    anomaly_score = Column(Float)
    
    # Timestamps
    executed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})


class BehaviorDrift(Base):
    """Behavior drift detection"""
    __tablename__ = "behavior_drift"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("assembly.agents.id", ondelete="SET NULL"))
    
    # Drift details
    drift_type = Column(String(100), nullable=False)
    drift_description = Column(Text, nullable=False)
    
    # Metrics
    baseline_metric = Column(Float)
    current_metric = Column(Float)
    drift_magnitude = Column(Float)
    
    # Time window
    detection_window_start = Column(TIMESTAMP(timezone=True))
    detection_window_end = Column(TIMESTAMP(timezone=True))
    sample_count = Column(Integer)
    
    # Status
    status = Column(String(50), nullable=False, default="detected")
    resolution_action = Column(Text)
    
    # Timestamps
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    resolved_at = Column(TIMESTAMP(timezone=True))
    
    # Metadata
    meta_data = Column(JSONB, default={})


# ============================================================================
# SECTION 7: DOMAIN MANAGEMENT
# ============================================================================

class Domain(Base):
    """Domains (Kingdoms) for entity"""
    __tablename__ = "domains"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    
    # Domain identification
    domain_name = Column(String(255), nullable=False)
    domain_type = Column(String(100), nullable=False)
    domain_description = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=5)
    
    # Associated elements
    associated_goals = Column(JSONB, default=[])
    associated_interests = Column(JSONB, default=[])
    associated_relationships = Column(JSONB, default=[])
    
    # Domain-specific agent
    domain_agent_id = Column(UUID(as_uuid=True), ForeignKey("assembly.agents.id", ondelete="SET NULL"))
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})
    
    # Relationships
    knowledge = relationship("DomainKnowledge", back_populates="domain", cascade="all, delete-orphan")


class DomainKnowledge(Base):
    """Domain knowledge library"""
    __tablename__ = "domain_knowledge"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("nucleus_core.domains.id", ondelete="CASCADE"), nullable=False)
    
    # Knowledge item
    knowledge_type = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    
    # Source
    source_type = Column(String(100))
    source_reference = Column(Text)
    
    # Relevance
    relevance_score = Column(Float, default=0.5)
    usage_count = Column(Integer, default=0)
    last_used_at = Column(TIMESTAMP(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})
    
    # Relationships
    domain = relationship("Domain", back_populates="knowledge")


# ============================================================================
# SECTION 8: RELATIONSHIP BUILDING (Private Language)
# ============================================================================

class PrivateLanguage(Base):
    """Private language elements"""
    __tablename__ = "private_language"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    
    # Language element
    element_type = Column(String(100), nullable=False)
    element_key = Column(String(255), nullable=False)
    element_meaning = Column(Text, nullable=False)
    
    # Context
    origin_context = Column(Text)
    usage_examples = Column(JSONB, default=[])
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(TIMESTAMP(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})


# ============================================================================
# SECTION 9: AGENT TESTBED
# ============================================================================

class TestScenario(Base):
    """Test scenarios for agents"""
    __tablename__ = "test_scenarios"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Scenario identification
    scenario_name = Column(String(255), nullable=False)
    scenario_type = Column(String(100), nullable=False)
    scenario_description = Column(Text)
    
    # Test configuration
    input_data = Column(JSONB, nullable=False)
    expected_output = Column(JSONB)
    validation_rules = Column(JSONB, default=[])
    
    # Target
    target_agent_type = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})
    
    # Relationships
    results = relationship("TestResult", back_populates="scenario", cascade="all, delete-orphan")


class TestResult(Base):
    """Test results"""
    __tablename__ = "test_results"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("nucleus_core.test_scenarios.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("assembly.agents.id", ondelete="SET NULL"))
    
    # Result
    passed = Column(Boolean, nullable=False)
    actual_output = Column(JSONB)
    error_message = Column(Text)
    
    # Performance
    execution_time_ms = Column(Integer)
    
    # Validation details
    validation_results = Column(JSONB, default=[])
    
    # Timestamps
    executed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})
    
    # Relationships
    scenario = relationship("TestScenario", back_populates="results")


# ============================================================================
# SECTION 10: WELLBEING GUARDIAN
# ============================================================================

class WellbeingCheck(Base):
    """Wellbeing checks"""
    __tablename__ = "wellbeing_checks"
    __table_args__ = {"schema": "nucleus_core"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    
    # Check type
    check_type = Column(String(100), nullable=False)
    
    # Metrics
    score = Column(Float, nullable=False)
    indicators = Column(JSONB, default=[])
    
    # Recommendations
    recommendations = Column(JSONB, default=[])
    
    # Status
    requires_attention = Column(Boolean, default=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(TIMESTAMP(timezone=True))
    
    # Timestamps
    checked_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Metadata
    meta_data = Column(JSONB, default={})
