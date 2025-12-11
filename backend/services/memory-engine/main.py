"""
NUCLEUS V2.0 - Memory Engine
Logs and manages 4-tier memory architecture
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import os
import uuid

# Import shared modules
import sys
sys.path.append("/app/backend")

from shared.models import get_db, MemoryTier1, Entity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NUCLEUS Memory Engine",
    description="Logs and manages 4-tier memory architecture",
    version="2.0.0"
)


# Pydantic models
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class MemoryLogRequest(BaseModel):
    entity_id: str
    interaction_type: str  # conversation, action, event, task_execution, decision
    interaction_data: Dict[str, Any]
    timestamp: Optional[datetime] = None


class MemoryLogResponse(BaseModel):
    status: str
    memory_id: str
    tier: int
    entity_id: str


# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "memory-engine",
        "version": "2.0.0"
    }


@app.post("/log", response_model=MemoryLogResponse)
async def log_interaction(
    request: MemoryLogRequest,
    db: Session = Depends(get_db)
):
    """
    Log an interaction to Tier 1 memory (ultra-fast).
    
    Interaction types:
    - conversation: User-agent dialogue
    - action: Task execution or decision
    - event: System event or trigger
    - task_execution: Completed task details
    - decision: Decision made by Decisions Engine
    """
    logger.info(f"Logging {request.interaction_type} for entity {request.entity_id}")
    
    # Validate entity exists
    try:
        entity = db.query(Entity).filter(Entity.id == uuid.UUID(request.entity_id)).first()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity ID format")
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Create Tier 1 memory entry
    memory = MemoryTier1(
        entity_id=uuid.UUID(request.entity_id),
        interaction_type=request.interaction_type,
        interaction_data=request.interaction_data,
        timestamp=request.timestamp or datetime.utcnow()
    )
    
    db.add(memory)
    db.commit()
    db.refresh(memory)
    
    logger.info(f"Memory logged: {memory.id} (Tier 1)")
    
    return {
        "status": "logged",
        "memory_id": str(memory.id),
        "tier": 1,
        "entity_id": request.entity_id
    }


@app.get("/recent/{entity_id}")
async def get_recent_memories(
    entity_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent memories for an entity from Tier 1"""
    logger.info(f"Fetching recent memories for entity {entity_id}")
    
    try:
        memories = db.query(MemoryTier1).filter(
            MemoryTier1.entity_id == uuid.UUID(entity_id)
        ).order_by(
            MemoryTier1.timestamp.desc()
        ).limit(limit).all()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid entity ID format")
    
    return {
        "entity_id": entity_id,
        "count": len(memories),
        "memories": [
            {
                "id": str(m.id),
                "type": m.interaction_type,
                "data": m.interaction_data,
                "timestamp": m.timestamp.isoformat()
            }
            for m in memories
        ]
    }


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Memory Engine service starting up...")
    logger.info("4-Tier Memory Architecture initialized")
    logger.info("Memory Engine service ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Memory Engine service shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
