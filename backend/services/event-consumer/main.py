"""
NUCLEUS Phase 3 - Event Consumer Service
Subscribes to NATS streams and processes events into Memory Engine
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import os
import asyncio
import json
import httpx
import nats
from nats.js import JetStreamContext
from nats.js.api import ConsumerConfig, AckPolicy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NUCLEUS Event Consumer",
    description="Subscribes to NATS and processes events",
    version="3.0.0"
)

# Configuration
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
MEMORY_ENGINE_URL = os.getenv("MEMORY_ENGINE_URL", "http://memory-engine:8080")

# Global state
nc: Optional[nats.NATS] = None
js: Optional[JetStreamContext] = None
http_client: Optional[httpx.AsyncClient] = None
consumer_task: Optional[asyncio.Task] = None


# Pydantic models
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    nats_connected: bool
    consuming: bool


# Event processing
async def process_event(event: Dict[str, Any]):
    """
    Process an event from NATS and send to Memory Engine.
    
    Event schema:
    {
        "source": "gmail" | "oura" | "calendar" | etc.,
        "type": "received" | "sleep_completed" | etc.,
        "entity_id": "uuid",
        "payload": {...},
        "timestamp": "ISO8601",
        "metadata": {...}
    }
    """
    try:
        source = event.get("source")
        event_type = event.get("type")
        entity_id = event.get("entity_id")
        payload = event.get("payload", {})
        timestamp = event.get("timestamp")
        
        logger.info(f"Processing event: {source}.{event_type} for entity {entity_id}")
        
        # Determine interaction type for Memory Engine
        interaction_type = map_to_interaction_type(source, event_type)
        
        # Prepare memory log request
        memory_request = {
            "entity_id": entity_id,
            "interaction_type": interaction_type,
            "interaction_data": {
                "source": source,
                "type": event_type,
                "payload": payload,
                "metadata": event.get("metadata", {})
            },
            "timestamp": timestamp
        }
        
        # Send to Memory Engine
        response = await http_client.post(
            f"{MEMORY_ENGINE_URL}/log",
            json=memory_request
        )
        
        if response.status_code == 200:
            logger.info(f"Event logged to Memory Engine: {source}.{event_type}")
            return True
        else:
            logger.error(f"Failed to log event: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return False


def map_to_interaction_type(source: str, event_type: str) -> str:
    """
    Map external event to Memory Engine interaction type.
    
    Memory Engine interaction types:
    - conversation: User-agent dialogue
    - action: Task execution or decision
    - event: System event or trigger
    - task_execution: Completed task details
    - decision: Decision made by Decisions Engine
    - email: Email events (new!)
    - health: Health/wellness events (new!)
    """
    # Gmail events
    if source == "gmail":
        return "email"
    
    # Health/IOT events
    if source in ["oura", "apple_health", "garmin", "whoop", "fitbit"]:
        return "health"
    
    # Calendar events
    if source == "calendar":
        return "event"
    
    # Social media events
    if source in ["linkedin", "twitter", "slack"]:
        return "conversation"
    
    # Default
    return "event"


async def subscribe_to_stream(stream_name: str, subjects: list[str]):
    """Subscribe to a NATS stream and process messages"""
    global js
    
    if not js:
        logger.error("JetStream not initialized")
        return
    
    try:
        # Create durable consumer
        consumer_name = f"{stream_name}_consumer"
        
        try:
            # Try to create consumer
            await js.add_consumer(
                stream_name,
                config=ConsumerConfig(
                    durable_name=consumer_name,
                    ack_policy=AckPolicy.EXPLICIT,
                    max_deliver=3
                )
            )
            logger.info(f"Created consumer: {consumer_name}")
        except:
            # Consumer already exists
            logger.info(f"Consumer {consumer_name} already exists")
        
        # Subscribe to consumer
        psub = await js.pull_subscribe("", consumer_name, stream=stream_name)
        
        logger.info(f"Subscribed to {stream_name} (subjects: {subjects})")
        
        # Process messages
        while True:
            try:
                # Fetch messages (batch of 10, wait up to 5 seconds)
                messages = await psub.fetch(batch=10, timeout=5)
                
                for msg in messages:
                    try:
                        # Parse event
                        event = json.loads(msg.data.decode())
                        
                        # Process event
                        success = await process_event(event)
                        
                        # Acknowledge message
                        if success:
                            await msg.ack()
                        else:
                            # Negative acknowledge (will be redelivered)
                            await msg.nak()
                            
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        await msg.nak()
                        
            except asyncio.TimeoutError:
                # No messages, continue
                continue
            except Exception as e:
                logger.error(f"Error fetching messages: {str(e)}")
                await asyncio.sleep(5)
                
    except Exception as e:
        logger.error(f"Error subscribing to {stream_name}: {str(e)}")


async def start_consumers():
    """Start all stream consumers"""
    # Subscribe to all streams
    await asyncio.gather(
        subscribe_to_stream("DIGITAL_EVENTS", ["digital.email.*", "digital.calendar.*", "digital.social.*"]),
        subscribe_to_stream("PHYSICAL_EVENTS", ["physical.sleep.*", "physical.activity.*", "physical.health.*"]),
        subscribe_to_stream("SYSTEM_EVENTS", ["system.agent.*", "system.decision.*", "system.action.*"])
    )


# Lifecycle
@app.on_event("startup")
async def startup_event():
    """Initialize NATS connection and start consumers"""
    global nc, js, http_client, consumer_task
    
    try:
        # Connect to NATS
        logger.info(f"Connecting to NATS at {NATS_URL}")
        nc = await nats.connect(NATS_URL)
        js = nc.jetstream()
        
        # Initialize HTTP client
        http_client = httpx.AsyncClient(timeout=30.0)
        
        # Start consumers in background
        consumer_task = asyncio.create_task(start_consumers())
        
        logger.info("Event Consumer started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start Event Consumer: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global nc, http_client, consumer_task
    
    # Cancel consumer task
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    
    # Close HTTP client
    if http_client:
        await http_client.aclose()
    
    # Close NATS connection
    if nc:
        await nc.close()
    
    logger.info("Event Consumer shut down")


# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "event-consumer",
        "version": "3.0.0",
        "nats_connected": nc is not None and nc.is_connected,
        "consuming": consumer_task is not None and not consumer_task.done()
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
