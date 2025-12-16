"""
NUCLEUS V1.2 - DNA Schema Models
Entity identity, values, goals, interests
"""

from sqlalchemy import Column, String, Text, Float, Boolean, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class Entity(Base):
    """Main entity (user) table"""
    __tablename__ = "entity"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Success Metrics (Phase 1 - V2.0)
    ttv_weeks = Column(Float, nullable=True, comment="Time To Value in weeks (30% to 50% autonomy)")
    precision_at_3 = Column(Float, nullable=True, comment="Percentage of top-3 suggestions rated as highly relevant")
    coherence_percent = Column(Float, nullable=True, comment="Percentage of actions aligned with DNA and principles")
    
    # Master Prompt (Phase 2 - V2.0)
    master_prompt = Column(Text, nullable=True, comment="Core identity prompt generated from complete DNA profile")
    master_prompt_version = Column(Integer, default=1, comment="Version number of master prompt")
    master_prompt_updated_at = Column(TIMESTAMP(timezone=True), nullable=True, comment="When master prompt was last updated")
    
    # Relationships - Core DNA
    interests = relationship("Interest", back_populates="entity", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="entity", cascade="all, delete-orphan")
    values = relationship("Value", back_populates="entity", cascade="all, delete-orphan")
    raw_data = relationship("RawData", back_populates="entity", cascade="all, delete-orphan")
    integrations = relationship("EntityIntegration", back_populates="entity", cascade="all, delete-orphan")
    
    # Relationships - Extended DNA (V2.0)
    personality_traits = relationship("PersonalityTrait", back_populates="entity", cascade="all, delete-orphan")
    communication_styles = relationship("CommunicationStyle", back_populates="entity", cascade="all, delete-orphan")
    decision_patterns = relationship("DecisionPattern", back_populates="entity", cascade="all, delete-orphan")
    work_habits = relationship("WorkHabit", back_populates="entity", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="entity", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="entity", cascade="all, delete-orphan")
    preferences = relationship("Preference", back_populates="entity", cascade="all, delete-orphan")
    constraints = relationship("Constraint", back_populates="entity", cascade="all, delete-orphan")
    beliefs = relationship("Belief", back_populates="entity", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="entity", cascade="all, delete-orphan")
    emotions = relationship("Emotion", back_populates="entity", cascade="all, delete-orphan")
    routines = relationship("Routine", back_populates="entity", cascade="all, delete-orphan")
    contexts = relationship("Context", back_populates="entity", cascade="all, delete-orphan")
    evolution_history = relationship("EvolutionHistory", back_populates="entity", cascade="all, delete-orphan")


class Interest(Base):
    """Entity interests discovered from interactions"""
    __tablename__ = "interests"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    interest_name = Column(String(255), nullable=False)
    interest_description = Column(Text)
    confidence_score = Column(Float, default=0.0)
    first_detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_reinforced_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    entity = relationship("Entity", back_populates="interests")


class Goal(Base):
    """Entity goals and objectives"""
    __tablename__ = "goals"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    goal_title = Column(String(500), nullable=False)
    goal_description = Column(Text)
    priority = Column(Integer, default=5)
    status = Column(String(50), default="active")  # active, completed, archived
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="goals")


class Value(Base):
    """Entity core values"""
    __tablename__ = "values"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    value_name = Column(String(255), nullable=False)
    value_description = Column(Text)
    importance_score = Column(Float, default=0.5)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="values")


class RawData(Base):
    """Raw data ingested for DNA analysis"""
    __tablename__ = "raw_data"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    data_type = Column(String(100), nullable=False)  # conversation, document, interaction
    data_content = Column(Text, nullable=False)
    meta_data = Column(JSONB)
    ingested_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="raw_data")


# ============================================================================
# Phase 3: Health & Wellness DNA
# ============================================================================

from sqlalchemy import Date

class DailyReadiness(Base):
    """
    Daily aggregated health and readiness scores.
    Calculated from raw health metrics to provide a holistic view of entity's readiness.
    """
    __tablename__ = "daily_readiness"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    
    # Date
    date = Column(Date, nullable=False, index=True)
    
    # Composite scores (0-1 scale)
    readiness_score = Column(Float)
    sleep_score = Column(Float)
    hrv_score = Column(Float)
    activity_score = Column(Float)
    recovery_score = Column(Float)
    
    # Raw metrics
    sleep_hours = Column(Float)
    hrv_avg = Column(Integer)
    resting_heart_rate = Column(Integer)
    steps = Column(Integer)
    calories_burned = Column(Integer)
    
    # Recommendations
    recommendations = Column(JSONB, default=[])
    
    # Metadata
    calculated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    meta_data = Column(JSONB, default={})


class EnergyPattern(Base):
    """
    Analysis of entity energy levels by time of day and day of week.
    Used for optimal scheduling and activity planning.
    """
    __tablename__ = "energy_patterns"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    
    # Time pattern
    hour_of_day = Column(Integer, nullable=False)  # 0-23
    day_of_week = Column(Integer)  # 0-6, NULL for all days
    
    # Energy metrics
    avg_energy_level = Column(Float, nullable=False)  # 0-1
    sample_count = Column(Integer, default=1)
    
    # Optimal activities
    optimal_for = Column(String(50))  # deep_work, meetings, creative, etc.
    
    # Metadata
    last_updated = Column(TIMESTAMP(timezone=True), server_default=func.now())
    meta_data = Column(JSONB, default={})


class SchedulingPreferences(Base):
    """
    Entity scheduling preferences for optimal calendar management.
    Used by Context-Aware Scheduler to plan activities.
    """
    __tablename__ = "scheduling_preferences"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    
    # Work hours preferences
    preferred_work_start = Column(Integer, default=9)  # Hour of day (0-23)
    preferred_work_end = Column(Integer, default=17)  # Hour of day (0-23)
    
    # Meeting preferences
    max_meetings_per_day = Column(Integer, default=5)
    preferred_meeting_duration = Column(Integer, default=30)  # minutes
    buffer_between_meetings = Column(Integer, default=15)  # minutes
    
    # Focus time preferences
    preferred_focus_block_duration = Column(Integer, default=90)  # minutes
    min_focus_blocks_per_day = Column(Integer, default=2)
    
    # Break preferences
    lunch_start_hour = Column(Integer, default=12)
    lunch_duration = Column(Integer, default=60)  # minutes
    
    # Days preferences
    working_days = Column(JSONB, default=[1, 2, 3, 4, 5])  # 0=Sunday, 6=Saturday
    
    # Metadata
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    meta_data = Column(JSONB, default={})
