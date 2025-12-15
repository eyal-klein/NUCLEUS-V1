"""
NUCLEUS Pub/Sub Consumer Utilities
Shared library for handling Pub/Sub push messages
"""

import base64
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Callable, Awaitable
from pydantic import BaseModel
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


class PubSubMessage(BaseModel):
    """Pub/Sub message structure."""
    messageId: str
    publishTime: str
    data: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None


class PubSubEnvelope(BaseModel):
    """Pub/Sub push envelope structure."""
    message: PubSubMessage
    subscription: str


class NucleusEvent(BaseModel):
    """NUCLEUS event structure."""
    type: str
    entity_id: str
    data: Dict[str, Any]
    timestamp: str
    source: str
    version: str = "1.0"


async def parse_pubsub_message(request: Request) -> NucleusEvent:
    """
    Parse a Pub/Sub push message from a FastAPI request.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        NucleusEvent parsed from the message
        
    Raises:
        HTTPException: If the message is invalid
    """
    try:
        # Parse envelope
        body = await request.json()
        envelope = PubSubEnvelope(**body)
        
        # Decode message data
        if not envelope.message.data:
            raise HTTPException(status_code=400, detail="No message data")
        
        decoded_data = base64.b64decode(envelope.message.data)
        event_dict = json.loads(decoded_data)
        
        # Parse event
        event = NucleusEvent(**event_dict)
        
        logger.info(f"Received event: {event.type} for entity {event.entity_id}")
        return event
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except Exception as e:
        logger.error(f"Failed to parse Pub/Sub message: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid message: {e}")


def create_push_handler(
    handler: Callable[[NucleusEvent], Awaitable[None]]
) -> Callable[[Request], Awaitable[Dict[str, str]]]:
    """
    Create a FastAPI endpoint handler for Pub/Sub push messages.
    
    Args:
        handler: Async function that processes NucleusEvent
        
    Returns:
        FastAPI endpoint handler
        
    Usage:
        @app.post("/pubsub/digital")
        async def handle_digital(request: Request):
            return await digital_handler(request)
        
        digital_handler = create_push_handler(process_digital_event)
    """
    async def endpoint(request: Request) -> Dict[str, str]:
        event = await parse_pubsub_message(request)
        
        try:
            await handler(event)
            return {"status": "ok", "message_id": event.type}
        except Exception as e:
            logger.error(f"Failed to process event {event.type}: {e}")
            # Return 500 to trigger retry
            raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
    
    return endpoint


class EventRouter:
    """
    Route events to handlers based on event type.
    
    Usage:
        router = EventRouter()
        
        @router.on("email.received")
        async def handle_email(event: NucleusEvent):
            # Process email event
            pass
        
        @router.on("calendar.event.created")
        async def handle_calendar(event: NucleusEvent):
            # Process calendar event
            pass
        
        # In endpoint:
        await router.route(event)
    """
    
    def __init__(self):
        self._handlers: Dict[str, Callable[[NucleusEvent], Awaitable[None]]] = {}
        self._default_handler: Optional[Callable[[NucleusEvent], Awaitable[None]]] = None
    
    def on(self, event_type: str):
        """Decorator to register a handler for an event type."""
        def decorator(handler: Callable[[NucleusEvent], Awaitable[None]]):
            self._handlers[event_type] = handler
            return handler
        return decorator
    
    def default(self, handler: Callable[[NucleusEvent], Awaitable[None]]):
        """Decorator to register a default handler."""
        self._default_handler = handler
        return handler
    
    async def route(self, event: NucleusEvent) -> None:
        """Route an event to the appropriate handler."""
        handler = self._handlers.get(event.type)
        
        if handler:
            await handler(event)
        elif self._default_handler:
            await self._default_handler(event)
        else:
            logger.warning(f"No handler for event type: {event.type}")


# Idempotency support
_processed_messages: Dict[str, datetime] = {}
MAX_CACHE_SIZE = 10000
CACHE_TTL_HOURS = 24


def is_duplicate(message_id: str) -> bool:
    """
    Check if a message has already been processed.
    
    Args:
        message_id: Pub/Sub message ID
        
    Returns:
        True if the message has been processed before
    """
    global _processed_messages
    
    # Clean old entries
    now = datetime.utcnow()
    _processed_messages = {
        k: v for k, v in _processed_messages.items()
        if (now - v).total_seconds() < CACHE_TTL_HOURS * 3600
    }
    
    # Limit cache size
    if len(_processed_messages) > MAX_CACHE_SIZE:
        # Remove oldest entries
        sorted_items = sorted(_processed_messages.items(), key=lambda x: x[1])
        _processed_messages = dict(sorted_items[MAX_CACHE_SIZE // 2:])
    
    if message_id in _processed_messages:
        logger.info(f"Duplicate message detected: {message_id}")
        return True
    
    _processed_messages[message_id] = now
    return False
