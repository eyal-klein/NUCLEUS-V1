"""
NUCLEUS Phase 3 - Event Stream Service
NATS JetStream for real-time event processing
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import os
import json
import asyncio
import nats
from nats.js import JetStreamContext
from nats.js.api import StreamConfig, RetentionPolicy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NUCLEUS Event Stream",
    description="NATS JetStream for real-time event processing",
    version="3.0.0"
)

# NATS configuration
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")

# Global NATS connection
nc: Optional[nats.NATS] = None
js: Optional[JetStreamContext] = None


# Pydantic models
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    nats_connected: bool


class Event(BaseModel):
    source: str  # gmail, oura, calendar, linkedin, etc.
    type: str  # email.received, sleep.completed, event.created, etc.
    entity_id: str
    payload: Dict[str, Any]
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = {}


class PublishResponse(BaseModel):
    status: str
    sequence: int
    stream: str


class StreamInfo(BaseModel):
    name: str
    subjects: List[str]
    messages: int
    bytes: int
    consumers: int


# NATS connection management
@app.on_event("startup")
async def startup_event():
    """Initialize NATS connection on startup"""
    global nc, js
    
    try:
        logger.info(f"Connecting to NATS at {NATS_URL}")
        nc = await nats.connect(NATS_URL)
        js = nc.jetstream()
        
        # Create streams for different event categories
        await create_streams()
        
        logger.info("NATS JetStream connected successfully")
    except Exception as e:
        logger.error(f"Failed to connect to NATS: {str(e)}")
        # Don't fail startup, but log the error


@app.on_event("shutdown")
async def shutdown_event():
    """Close NATS connection on shutdown"""
    global nc
    
    if nc:
        await nc.close()
        logger.info("NATS connection closed")


async def create_streams():
    """Create JetStream streams for different event categories"""
    global js
    
    if not js:
        logger.error("JetStream not initialized")
        return
    
    streams = [
        {
            "name": "DIGITAL_EVENTS",
            "subjects": ["digital.email.*", "digital.calendar.*", "digital.social.*"],
            "description": "Digital self events (email, calendar, social media)"
        },
        {
            "name": "PHYSICAL_EVENTS",
            "subjects": ["physical.sleep.*", "physical.activity.*", "physical.health.*"],
            "description": "Physical self events (IOT devices)"
        },
        {
            "name": "SYSTEM_EVENTS",
            "subjects": ["system.agent.*", "system.decision.*", "system.action.*"],
            "description": "Internal system events"
        }
    ]
    
    for stream_config in streams:
        try:
            # Try to get existing stream
            try:
                await js.stream_info(stream_config["name"])
                logger.info(f"Stream {stream_config['name']} already exists")
            except:
                # Create new stream
                config = StreamConfig(
                    name=stream_config["name"],
                    subjects=stream_config["subjects"],
                    retention=RetentionPolicy.LIMITS,
                    max_age=7 * 24 * 60 * 60 * 1000000000,  # 7 days in nanoseconds
                    max_bytes=10 * 1024 * 1024 * 1024,  # 10 GB
                    description=stream_config["description"]
                )
                await js.add_stream(config)
                logger.info(f"Created stream: {stream_config['name']}")
        except Exception as e:
            logger.error(f"Error creating stream {stream_config['name']}: {str(e)}")


# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "event-stream",
        "version": "3.0.0",
        "nats_connected": nc is not None and nc.is_connected
    }


@app.post("/publish", response_model=PublishResponse)
async def publish_event(event: Event):
    """
    Publish an event to the appropriate NATS stream.
    
    Event routing:
    - digital.* → DIGITAL_EVENTS stream
    - physical.* → PHYSICAL_EVENTS stream
    - system.* → SYSTEM_EVENTS stream
    """
    global js
    
    if not js:
        raise HTTPException(status_code=503, detail="NATS JetStream not available")
    
    # Determine subject based on source and type
    category = get_event_category(event.source)
    subject = f"{category}.{event.source}.{event.type}"
    
    # Add timestamp if not provided
    if not event.timestamp:
        event.timestamp = datetime.utcnow()
    
    # Prepare message
    message = {
        "source": event.source,
        "type": event.type,
        "entity_id": event.entity_id,
        "payload": event.payload,
        "timestamp": event.timestamp.isoformat(),
        "metadata": event.metadata
    }
    
    try:
        # Publish to NATS
        ack = await js.publish(subject, json.dumps(message).encode())
        
        logger.info(f"Published event: {subject} (seq: {ack.seq})")
        
        return {
            "status": "published",
            "sequence": ack.seq,
            "stream": ack.stream
        }
    except Exception as e:
        logger.error(f"Failed to publish event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to publish event: {str(e)}")


@app.get("/streams", response_model=List[StreamInfo])
async def list_streams():
    """List all JetStream streams"""
    global js
    
    if not js:
        raise HTTPException(status_code=503, detail="NATS JetStream not available")
    
    try:
        streams_info = []
        
        for stream_name in ["DIGITAL_EVENTS", "PHYSICAL_EVENTS", "SYSTEM_EVENTS"]:
            try:
                info = await js.stream_info(stream_name)
                streams_info.append({
                    "name": info.config.name,
                    "subjects": info.config.subjects,
                    "messages": info.state.messages,
                    "bytes": info.state.bytes,
                    "consumers": info.state.consumer_count
                })
            except Exception as e:
                logger.error(f"Error getting info for stream {stream_name}: {str(e)}")
        
        return streams_info
    except Exception as e:
        logger.error(f"Failed to list streams: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list streams: {str(e)}")


def get_event_category(source: str) -> str:
    """Determine event category based on source"""
    digital_sources = ["gmail", "calendar", "linkedin", "twitter", "slack"]
    physical_sources = ["oura", "apple_health", "garmin", "whoop", "fitbit"]
    
    if source in digital_sources:
        return "digital"
    elif source in physical_sources:
        return "physical"
    else:
        return "system"


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
