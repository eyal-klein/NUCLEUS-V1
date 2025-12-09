"""
NUCLEUS V1.2 - Entity Integrations Model
Represents third-party service integrations for entities
"""

from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class EntityIntegration(Base):
    """
    Represents a third-party service integration for an entity.
    Stores metadata and reference to credentials in Secret Manager.
    
    The actual credentials are stored securely in GCP Secret Manager,
    not in the database. This table only stores the reference path.
    """
    __tablename__ = "entity_integrations"
    __table_args__ = {'schema': 'dna'}
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Entity reference
    entity_id = Column(UUID(as_uuid=True), ForeignKey('dna.entity.id', ondelete='CASCADE'), nullable=False)
    
    # Integration details
    service_name = Column(String(100), nullable=False)  # gmail, github, notion
    service_type = Column(String(50), nullable=False)   # email, code, docs
    display_name = Column(String(255))
    description = Column(Text)
    
    # Credentials reference (NOT the actual credentials!)
    secret_path = Column(String(255), nullable=False)
    credential_type = Column(String(50), nullable=False)
    
    # Status tracking
    status = Column(String(50), default='active')
    last_sync_at = Column(TIMESTAMP(timezone=True))
    last_sync_status = Column(String(50))
    sync_error_message = Column(Text)
    next_sync_at = Column(TIMESTAMP(timezone=True))
    
    # OAuth-specific
    token_expires_at = Column(TIMESTAMP(timezone=True))
    scopes = Column(JSONB)
    
    # Configuration
    config = Column(JSONB, default={})
    sync_settings = Column(JSONB, default={})
    
    # Metadata
    meta_data = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    
    # Relationships
    entity = relationship("Entity", back_populates="integrations")
    
    def __repr__(self):
        return f"<EntityIntegration(id={self.id}, entity_id={self.entity_id}, service={self.service_name}, status={self.status})>"
    
    def to_dict(self):
        """Convert to dictionary (without sensitive data)"""
        return {
            "id": str(self.id),
            "entity_id": str(self.entity_id),
            "service_name": self.service_name,
            "service_type": self.service_type,
            "display_name": self.display_name,
            "description": self.description,
            "credential_type": self.credential_type,
            "status": self.status,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_sync_status": self.last_sync_status,
            "sync_error_message": self.sync_error_message,
            "next_sync_at": self.next_sync_at.isoformat() if self.next_sync_at else None,
            "token_expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
            "scopes": self.scopes,
            "config": self.config,
            "sync_settings": self.sync_settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }
