"""
NUCLEUS Phase 3 - Event Consumer Service (Pub/Sub Edition)
Receives events from Pub/Sub push subscriptions and processes them
"""

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
import base64
import json
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NUCLEUS Event Consumer",
    description="Processes events from Pub/Sub push subscriptions",
    version="3.1.0"
)

# Configuration
MEMORY_ENGINE_URL = os.getenv("MEMORY_ENGINE_URL", "http://analysis-memory:8080")
DNA_ENGINE_URL = os.getenv("DNA_ENGINE_URL", "http://analysis-dna:8080")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "thrive-system1")

# HTTP client for downstream services
http_client = httpx.AsyncClient(timeout=30.0)

# Idempotency cache
_processed_messages: Dict[str, float] = {}
MAX_CACHE_SIZE = 10000


# ============================================
# Pydantic Models
# ============================================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class PubSubMessage(BaseModel):
    messageId: str
    publishTime: str
    data: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None


class PubSubEnvelope(BaseModel):
    message: PubSubMessage
    subscription: str


class NucleusEvent(BaseModel):
    event_type: str
    entity_id: str
    payload: Dict[str, Any]
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


# ============================================
# Helper Functions
# ============================================

def check_idempotency(message_id: str) -> bool:
    """Check if message was already processed. Returns True if duplicate."""
    import time
    global _processed_messages
    
    now = time.time()
    
    # Clean old entries (older than 1 hour)
    _processed_messages = {
        k: v for k, v in _processed_messages.items()
        if now - v < 3600
    }
    
    # Limit cache size
    if len(_processed_messages) > MAX_CACHE_SIZE:
        sorted_items = sorted(_processed_messages.items(), key=lambda x: x[1])
        _processed_messages = dict(sorted_items[MAX_CACHE_SIZE // 2:])
    
    if message_id in _processed_messages:
        logger.info(f"Duplicate message detected: {message_id}")
        return True
    
    _processed_messages[message_id] = now
    return False


async def parse_pubsub_message(request: Request) -> tuple[NucleusEvent, str]:
    """Parse Pub/Sub push message from request."""
    try:
        body = await request.json()
        envelope = PubSubEnvelope(**body)
        
        if not envelope.message.data:
            raise HTTPException(status_code=400, detail="No message data")
        
        decoded_data = base64.b64decode(envelope.message.data)
        event_dict = json.loads(decoded_data)
        
        event = NucleusEvent(**event_dict)
        
        logger.info(f"Received event: {event.event_type} for entity {event.entity_id}")
        return event, envelope.message.messageId
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except Exception as e:
        logger.error(f"Failed to parse Pub/Sub message: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid message: {e}")


def map_to_interaction_type(event_type: str) -> str:
    """Map event type to Memory Engine interaction type."""
    if event_type.startswith("email"):
        return "email"
    elif event_type.startswith("calendar"):
        return "event"
    elif event_type.startswith("health") or event_type.startswith("oura") or event_type.startswith("apple"):
        return "health"
    elif event_type.startswith("linkedin") or event_type.startswith("social"):
        return "conversation"
    else:
        return "event"


async def store_in_memory(event: NucleusEvent) -> bool:
    """Store event in Memory Engine."""
    try:
        interaction_type = map_to_interaction_type(event.event_type)
        
        response = await http_client.post(
            f"{MEMORY_ENGINE_URL}/log",
            json={
                "entity_id": event.entity_id,
                "interaction_type": interaction_type,
                "interaction_data": {
                    "event_type": event.event_type,
                    "payload": event.payload,
                    "metadata": event.metadata or {}
                },
                "timestamp": event.timestamp
            }
        )
        
        if response.status_code == 200:
            logger.info(f"Stored event in Memory Engine: {event.event_type}")
            return True
        else:
            logger.warning(f"Memory Engine returned: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to store in Memory Engine: {e}")
        return False


async def update_dna(event: NucleusEvent) -> bool:
    """Update DNA Engine with event data."""
    try:
        response = await http_client.post(
            f"{DNA_ENGINE_URL}/process-event",
            json={
                "entity_id": event.entity_id,
                "event_type": event.event_type,
                "data": event.payload,
                "timestamp": event.timestamp
            }
        )
        
        if response.status_code == 200:
            logger.info(f"Updated DNA Engine: {event.event_type}")
            return True
        else:
            logger.warning(f"DNA Engine returned: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to update DNA Engine: {e}")
        return False


# ============================================
# Health Endpoints
# ============================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="event-consumer",
        version="3.1.0"
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"service": "NUCLEUS Event Consumer", "status": "running", "mode": "pubsub-push"}


# ============================================
# Pub/Sub Push Endpoints
# ============================================

@app.post("/pubsub/digital")
async def handle_digital_event(request: Request):
    """
    Handle digital events (Gmail, Calendar).
    Called by Pub/Sub push subscription.
    """
    event, message_id = await parse_pubsub_message(request)
    
    # Idempotency check
    if check_idempotency(message_id):
        return {"status": "duplicate", "message_id": message_id}
    
    # Process event
    try:
        await store_in_memory(event)
        await update_dna(event)
        
        logger.info(f"Processed digital event: {event.event_type}")
        return {"status": "ok", "message_id": message_id}
        
    except Exception as e:
        logger.error(f"Failed to process digital event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pubsub/health")
async def handle_health_event(request: Request):
    """
    Handle health events (Oura, Apple Watch).
    Called by Pub/Sub push subscription.
    """
    event, message_id = await parse_pubsub_message(request)
    
    # Idempotency check
    if check_idempotency(message_id):
        return {"status": "duplicate", "message_id": message_id}
    
    # Process event
    try:
        await store_in_memory(event)
        await update_dna(event)
        
        logger.info(f"Processed health event: {event.event_type}")
        return {"status": "ok", "message_id": message_id}
        
    except Exception as e:
        logger.error(f"Failed to process health event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pubsub/social")
async def handle_social_event(request: Request):
    """
    Handle social events (LinkedIn).
    Called by Pub/Sub push subscription.
    """
    event, message_id = await parse_pubsub_message(request)
    
    # Idempotency check
    if check_idempotency(message_id):
        return {"status": "duplicate", "message_id": message_id}
    
    # Process event
    try:
        await store_in_memory(event)
        await update_dna(event)
        
        logger.info(f"Processed social event: {event.event_type}")
        return {"status": "ok", "message_id": message_id}
        
    except Exception as e:
        logger.error(f"Failed to process social event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Debug Endpoints
# ============================================

@app.get("/stats")
async def get_stats():
    """Get consumer statistics."""
    return {
        "processed_messages_cached": len(_processed_messages),
        "max_cache_size": MAX_CACHE_SIZE,
        "memory_engine_url": MEMORY_ENGINE_URL,
        "dna_engine_url": DNA_ENGINE_URL,
        "mode": "pubsub-push"
    }


# ============================================
# Startup/Shutdown
# ============================================

@app.on_event("startup")
async def startup():
    """Startup event handler."""
    logger.info("Event Consumer starting up (Pub/Sub Push mode)...")
    logger.info(f"Memory Engine URL: {MEMORY_ENGINE_URL}")
    logger.info(f"DNA Engine URL: {DNA_ENGINE_URL}")
    logger.info("Ready to receive Pub/Sub push messages!")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event handler."""
    logger.info("Event Consumer shutting down...")
    await http_client.aclose()


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
