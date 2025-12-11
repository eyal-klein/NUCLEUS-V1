"""
NUCLEUS V1.2 - Assembly Schema Models
Agent & tool definitions, versions, performance
"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base


class Agent(Base):
    """Agent definitions"""
    __tablename__ = "agents"
    __table_args__ = {"schema": "assembly"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(255), nullable=False, unique=True)
    agent_type = Column(String(100), nullable=False)  # strategic, tactical
    system_prompt = Column(Text, nullable=False)
    description = Column(Text)
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    agent_tools = relationship("AgentTool", back_populates="agent", cascade="all, delete-orphan")
    performance_records = relationship("AgentPerformance", back_populates="agent", cascade="all, delete-orphan")


class Tool(Base):
    """Tool definitions"""
    __tablename__ = "tools"
    __table_args__ = {"schema": "assembly"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_name = Column(String(255), nullable=False, unique=True)
    tool_description = Column(Text)
    tool_schema = Column(JSONB, nullable=False)  # LangChain tool schema
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    agent_tools = relationship("AgentTool", back_populates="tool", cascade="all, delete-orphan")


class AgentTool(Base):
    """Agent-Tool permissions (many-to-many)"""
    __tablename__ = "agent_tools"
    __table_args__ = (
        UniqueConstraint("agent_id", "tool_id", name="uq_agent_tool"),
        {"schema": "assembly"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("assembly.agents.id", ondelete="CASCADE"))
    tool_id = Column(UUID(as_uuid=True), ForeignKey("assembly.tools.id", ondelete="CASCADE"))
    granted_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="agent_tools")
    tool = relationship("Tool", back_populates="agent_tools")


class AgentPerformance(Base):
    """Agent performance metrics"""
    __tablename__ = "agent_performance"
    __table_args__ = {"schema": "assembly"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("assembly.agents.id", ondelete="CASCADE"))
    task_id = Column(UUID(as_uuid=True), nullable=False)
    success = Column(Boolean, nullable=False)
    execution_time_ms = Column(Integer)
    feedback_score = Column(Float)
    meta_data = Column(JSONB)
    recorded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="performance_records")


class AgentNeed(Base):
    """Agent needs detected by the Intelligent Agent Factory"""
    __tablename__ = "agent_needs"
    __table_args__ = {"schema": "assembly"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    need_type = Column(String(100), nullable=False)  # coverage_gap, high_demand, failure_pattern, emerging_topic
    description = Column(Text, nullable=False)
    priority = Column(String(50), nullable=False)  # low, medium, high, critical
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    evidence = Column(JSONB)  # List of evidence supporting this need
    suggested_agent = Column(JSONB)  # Suggested agent specification from LLM
    status = Column(String(50), default='pending')  # pending, fulfilled, rejected
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entities.id", ondelete="SET NULL"), nullable=True)
    created_agent_id = Column(UUID(as_uuid=True), ForeignKey("assembly.agents.id", ondelete="SET NULL"), nullable=True)
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    fulfilled_at = Column(TIMESTAMP(timezone=True), nullable=True)


class AgentLifecycleEvent(Base):
    """Agent lifecycle events (apoptosis, evolution, mitosis)"""
    __tablename__ = "agent_lifecycle_events"
    __table_args__ = {"schema": "assembly"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("assembly.agents.id", ondelete="CASCADE"))
    event_type = Column(String(50), nullable=False)  # apoptosis, evolution, mitosis
    reason = Column(Text, nullable=False)
    health_score_before = Column(Float)
    health_score_after = Column(Float, nullable=True)
    changes_made = Column(JSONB)  # Details of what changed
    new_agent_id = Column(UUID(as_uuid=True), ForeignKey("assembly.agents.id", ondelete="SET NULL"), nullable=True)  # For mitosis
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
