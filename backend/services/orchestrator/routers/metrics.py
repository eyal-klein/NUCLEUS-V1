"""
NUCLEUS V1.2 - Metrics Router
Success metrics endpoints for entities
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging
import uuid

import sys
sys.path.append("/app/backend")

from shared.models import get_db, Entity
from shared.memory_logger import get_memory_logger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


class MetricsResponse(BaseModel):
    entity_id: str
    entity_name: str
    ttv_weeks: Optional[float]
    precision_at_3: Optional[float]
    coherence_percent: Optional[float]
    

@router.get("/{entity_id}", response_model=MetricsResponse)
async def get_entity_metrics(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """
    Get success metrics for a specific entity.
    Returns TTV (Time To Value), Precision@3, and Coherence metrics.
    """
    logger.info(f"Fetching metrics for entity: {entity_id}")
    
    # Query entity
    try:
        entity = db.query(Entity).filter(Entity.id == uuid.UUID(entity_id)).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity ID format")
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Log metrics retrieval to Memory Engine
    memory_logger = get_memory_logger()
    await memory_logger.log(
        entity_id=entity_id,
        interaction_type="metrics_retrieval",
        interaction_data={
            "ttv_weeks": entity.ttv_weeks,
            "precision_at_3": entity.precision_at_3,
            "coherence_percent": entity.coherence_percent
        }
    )
    
    return {
        "entity_id": str(entity.id),
        "entity_name": entity.name,
        "ttv_weeks": entity.ttv_weeks,
        "precision_at_3": entity.precision_at_3,
        "coherence_percent": entity.coherence_percent
    }
