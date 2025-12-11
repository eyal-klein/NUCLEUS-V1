"""
NUCLEUS V2.0 - Extended DNA Schema Models
Additional DNA tables for comprehensive entity profiling
"""

from sqlalchemy import Column, String, Text, Float, Boolean, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class PersonalityTrait(Base):
    """Entity personality traits (Big Five, MBTI, etc.)"""
    __tablename__ = "personality_traits"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    trait_name = Column(String(255), nullable=False)  # e.g., "Openness", "Extraversion"
    trait_value = Column(Float, nullable=False)  # 0.0 to 1.0 scale
    trait_description = Column(Text)
    confidence_score = Column(Float, default=0.0)
    first_detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    evidence_count = Column(Integer, default=0)  # Number of supporting observations
    
    # Relationships
    entity = relationship("Entity", back_populates="personality_traits")


class CommunicationStyle(Base):
    """Entity communication patterns and preferences"""
    __tablename__ = "communication_styles"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    style_name = Column(String(255), nullable=False)  # e.g., "Direct", "Analytical", "Empathetic"
    style_description = Column(Text)
    frequency_score = Column(Float, default=0.0)  # How often this style is used
    preferred_channels = Column(ARRAY(String))  # e.g., ["email", "chat", "voice"]
    tone_preferences = Column(JSONB)  # e.g., {"formality": "casual", "humor": "moderate"}
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="communication_styles")


class DecisionPattern(Base):
    """Entity decision-making patterns and biases"""
    __tablename__ = "decision_patterns"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    pattern_name = Column(String(255), nullable=False)  # e.g., "Risk-averse", "Data-driven"
    pattern_description = Column(Text)
    confidence_score = Column(Float, default=0.0)
    decision_context = Column(String(255))  # e.g., "work", "personal", "financial"
    typical_factors = Column(JSONB)  # Factors typically considered
    typical_timeframe = Column(String(100))  # e.g., "immediate", "deliberate", "procrastinating"
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="decision_patterns")


class WorkHabit(Base):
    """Entity work habits and productivity patterns"""
    __tablename__ = "work_habits"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    habit_name = Column(String(255), nullable=False)  # e.g., "Morning person", "Deep work blocks"
    habit_description = Column(Text)
    frequency = Column(String(100))  # e.g., "daily", "weekly", "occasionally"
    peak_productivity_times = Column(ARRAY(String))  # e.g., ["09:00-11:00", "14:00-16:00"]
    preferred_work_environment = Column(JSONB)  # e.g., {"noise_level": "quiet", "location": "home"}
    task_management_style = Column(String(255))  # e.g., "list-based", "time-blocking", "spontaneous"
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="work_habits")


class Relationship(Base):
    """Entity relationships with other entities or external people"""
    __tablename__ = "relationships"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)  # If related to another entity in system
    related_name = Column(String(255), nullable=False)  # Name of person/entity
    relationship_type = Column(String(100), nullable=False)  # e.g., "colleague", "friend", "mentor"
    relationship_strength = Column(Float, default=0.5)  # 0.0 to 1.0
    interaction_frequency = Column(String(100))  # e.g., "daily", "weekly", "monthly"
    relationship_context = Column(Text)  # Description of the relationship
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="relationships")


class Skill(Base):
    """Entity skills and competencies"""
    __tablename__ = "skills"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    skill_name = Column(String(255), nullable=False)
    skill_category = Column(String(100))  # e.g., "technical", "soft", "domain"
    proficiency_level = Column(Float, nullable=False)  # 0.0 (beginner) to 1.0 (expert)
    skill_description = Column(Text)
    years_of_experience = Column(Float)
    last_used_at = Column(TIMESTAMP(timezone=True))
    is_actively_developing = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="skills")


class Preference(Base):
    """Entity preferences across various domains"""
    __tablename__ = "preferences"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    preference_category = Column(String(100), nullable=False)  # e.g., "food", "music", "tools"
    preference_name = Column(String(255), nullable=False)
    preference_value = Column(Text)  # The actual preference
    strength = Column(Float, default=0.5)  # How strong is this preference (0.0 to 1.0)
    context = Column(String(255))  # When/where this preference applies
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="preferences")


class Constraint(Base):
    """Entity constraints and limitations"""
    __tablename__ = "constraints"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    constraint_type = Column(String(100), nullable=False)  # e.g., "time", "budget", "resource", "physical"
    constraint_name = Column(String(255), nullable=False)
    constraint_description = Column(Text)
    severity = Column(String(50))  # e.g., "hard", "soft", "flexible"
    impact_areas = Column(ARRAY(String))  # Areas affected by this constraint
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="constraints")


class Belief(Base):
    """Entity beliefs and worldviews"""
    __tablename__ = "beliefs"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    belief_category = Column(String(100))  # e.g., "professional", "personal", "philosophical"
    belief_statement = Column(Text, nullable=False)
    conviction_strength = Column(Float, default=0.5)  # How strongly held (0.0 to 1.0)
    origin_context = Column(Text)  # Where/how this belief was formed
    influences_decisions = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="beliefs")


class Experience(Base):
    """Entity significant experiences and life events"""
    __tablename__ = "experiences"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    experience_title = Column(String(500), nullable=False)
    experience_description = Column(Text)
    experience_category = Column(String(100))  # e.g., "professional", "personal", "educational"
    impact_level = Column(Float, default=0.5)  # How impactful (0.0 to 1.0)
    lessons_learned = Column(ARRAY(Text))
    skills_gained = Column(ARRAY(String))
    occurred_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="experiences")


class Emotion(Base):
    """Entity emotional patterns and triggers"""
    __tablename__ = "emotions"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    emotion_name = Column(String(100), nullable=False)  # e.g., "joy", "frustration", "anxiety"
    emotion_intensity = Column(Float, default=0.5)  # 0.0 to 1.0
    trigger_context = Column(Text)  # What typically triggers this emotion
    typical_response = Column(Text)  # How entity typically responds
    frequency = Column(String(100))  # How often this emotion is observed
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="emotions")


class Routine(Base):
    """Entity routines and recurring patterns"""
    __tablename__ = "routines"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    routine_name = Column(String(255), nullable=False)
    routine_description = Column(Text)
    routine_type = Column(String(100))  # e.g., "daily", "weekly", "monthly", "seasonal"
    time_of_day = Column(String(100))  # e.g., "morning", "afternoon", "evening"
    typical_duration = Column(Integer)  # Minutes
    consistency_score = Column(Float, default=0.5)  # How consistently followed (0.0 to 1.0)
    purpose = Column(Text)  # Why this routine exists
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="routines")


class Context(Base):
    """Entity contexts and situational awareness"""
    __tablename__ = "contexts"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    context_name = Column(String(255), nullable=False)  # e.g., "work", "home", "travel"
    context_description = Column(Text)
    typical_behaviors = Column(JSONB)  # Behaviors typical in this context
    typical_goals = Column(ARRAY(String))  # Goals active in this context
    typical_constraints = Column(ARRAY(String))  # Constraints active in this context
    frequency = Column(String(100))  # How often entity is in this context
    last_active_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    entity = relationship("Entity", back_populates="contexts")


class EvolutionHistory(Base):
    """Track DNA evolution over time"""
    __tablename__ = "evolution_history"
    __table_args__ = {"schema": "dna"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"))
    evolution_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    table_name = Column(String(100), nullable=False)  # Which DNA table was updated
    record_id = Column(UUID(as_uuid=True))  # ID of the record that changed
    change_type = Column(String(50), nullable=False)  # "created", "updated", "deleted"
    old_values = Column(JSONB)  # Previous values (for updates/deletes)
    new_values = Column(JSONB)  # New values (for creates/updates)
    confidence_delta = Column(Float)  # Change in confidence score
    source_memory_ids = Column(ARRAY(UUID(as_uuid=True)))  # Memory records that triggered this change
    distillation_run_id = Column(UUID(as_uuid=True))  # ID of the DNA Engine run that made this change
    
    # Relationships
    entity = relationship("Entity", back_populates="evolution_history")
