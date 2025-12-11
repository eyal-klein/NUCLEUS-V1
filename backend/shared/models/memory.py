"""
NUCLEUS V1.2 - Memory Schema Models
Conversation history, summaries, vector embeddings
"""

from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

from .base import Base


class Conversation(Base):
    """Conversation messages"""
    __tablename__ = "conversations"
    __table_args__ = {"schema": "memory"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    meta_data = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Summary(Base):
    """Conversation and period summaries"""
    __tablename__ = "summaries"
    __table_args__ = {"schema": "memory"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    summary_type = Column(String(100), nullable=False)  # daily, weekly, topic
    summary_content = Column(Text, nullable=False)
    time_period_start = Column(TIMESTAMP(timezone=True))
    time_period_end = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Embedding(Base):
    """Vector embeddings for semantic search"""
    __tablename__ = "embeddings"
    __table_args__ = {"schema": "memory"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    source_type = Column(String(100), nullable=False)  # conversation, document, summary
    source_id = Column(UUID(as_uuid=True), nullable=False)
    content_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536))  # OpenAI ada-002 dimension
    meta_data = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


# ============================================================================
# Phase 1 - V2.0: 4-Tier Memory Architecture
# ============================================================================

class MemoryTier1(Base):
    """
    Tier 1: Ultra-fast memory (< 10ms latency)
    Storage: Redis/In-Memory Cache
    Retention: Last 24 hours of interactions
    """
    __tablename__ = "memory_tier1"
    __table_args__ = {"schema": "memory"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    interaction_type = Column(String(100), nullable=False)  # conversation, action, event
    interaction_data = Column(JSONB, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    ttl_hours = Column(Integer, default=24, comment="Time to live in hours before moving to Tier 2")


class MemoryTier2(Base):
    """
    Tier 2: Fast memory (< 100ms latency)
    Storage: PostgreSQL (hot data)
    Retention: Last 7-30 days
    """
    __tablename__ = "memory_tier2"
    __table_args__ = {"schema": "memory"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    interaction_type = Column(String(100), nullable=False)
    interaction_data = Column(JSONB, nullable=False)
    summary = Column(Text, nullable=True, comment="LLM-generated summary for quick retrieval")
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    moved_from_tier1_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    ttl_days = Column(Integer, default=30, comment="Time to live in days before moving to Tier 3")


class MemoryTier3(Base):
    """
    Tier 3: Semantic memory (< 500ms latency)
    Storage: PostgreSQL + pgvector (vector search)
    Retention: 30-365 days
    """
    __tablename__ = "memory_tier3"
    __table_args__ = {"schema": "memory"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    interaction_type = Column(String(100), nullable=False)
    summary = Column(Text, nullable=False, comment="Condensed summary of the interaction")
    embedding = Column(Vector(1536), comment="Vector embedding for semantic search")
    importance_score = Column(Float, default=0.5, comment="0-1 score indicating importance")
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    moved_from_tier2_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    ttl_days = Column(Integer, default=365, comment="Time to live in days before archiving to Tier 4")


class MemoryTier4(Base):
    """
    Tier 4: Long-term archive (> 1s latency acceptable)
    Storage: Google Cloud Storage (JSON files)
    Retention: Indefinite (compressed, cold storage)
    Note: This table stores metadata only; actual data is in GCS
    """
    __tablename__ = "memory_tier4"
    __table_args__ = {"schema": "memory"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("dna.entity.id", ondelete="CASCADE"), nullable=False)
    gcs_bucket = Column(String(255), nullable=False, comment="GCS bucket name")
    gcs_path = Column(String(500), nullable=False, comment="Full path to the archived file in GCS")
    time_period_start = Column(TIMESTAMP(timezone=True), nullable=False)
    time_period_end = Column(TIMESTAMP(timezone=True), nullable=False)
    record_count = Column(Integer, nullable=False, comment="Number of interactions in this archive")
    file_size_bytes = Column(Integer, nullable=True)
    archived_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
