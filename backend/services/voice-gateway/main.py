"""
NUCLEUS Voice Gateway Service

Real-time voice interface for NUCLEUS using xAI Grok Voice Agent API.

This service provides:
- WebSocket endpoint for voice conversations
- REST API for session management
- Integration with NUCLEUS Memory, DNA, and other services
- Hebrew language support with natural conversation flow

Version: 2.0.0
"""

import asyncio
import json
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local imports
from config import get_settings
from models.session import VoiceSessionConfig, EntityContext
from models.events import SessionState, ConversationLog, VoiceSessionEvent
from services.session_manager import get_session_manager
from services.nucleus_integration import get_nucleus_integration
from services.xai_bridge import get_xai_bridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# REST API Models
# =============================================================================

class SessionRequest(BaseModel):
    """Request to create a new voice session."""
    entity_id: UUID
    voice: str = Field(default="Sal", description="Voice to use")
    language: str = Field(default="he", description="Language code")
    custom_instructions: Optional[str] = Field(default=None, description="Custom instructions")
    tools_enabled: bool = Field(default=True, description="Enable tool calling")


class SessionResponse(BaseModel):
    """Response with session information."""
    session_id: UUID
    ws_url: str
    expires_at: datetime


class SessionStatusResponse(BaseModel):
    """Response with session status."""
    session_id: UUID
    entity_id: UUID
    state: str
    created_at: datetime
    last_activity: datetime
    duration_ms: int
    message_count: int
    tool_calls_count: int


class GatewayStatsResponse(BaseModel):
    """Response with gateway statistics."""
    active_sessions: int
    max_sessions: int


# =============================================================================
# REST API Router
# =============================================================================

router = APIRouter()


@router.post("/session", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """Create a new voice session token."""
    settings = get_settings()
    session_id = uuid4()
    ws_url = f"wss://voice-gateway.nucleus.ai/ws/{request.entity_id}"
    expires_at = datetime.utcnow() + timedelta(seconds=settings.session_timeout_seconds)
    
    logger.info(f"Created session token for entity {request.entity_id}")
    
    return SessionResponse(
        session_id=session_id,
        ws_url=ws_url,
        expires_at=expires_at,
    )


@router.get("/session/{entity_id}", response_model=SessionStatusResponse)
async def get_session_status(entity_id: UUID):
    """Get the status of an active session for an entity."""
    session_manager = get_session_manager()
    session = await session_manager.get_session_by_entity(entity_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")
    
    return SessionStatusResponse(
        session_id=session.session_id,
        entity_id=session.entity_id,
        state=session.state.value,
        created_at=session.created_at,
        last_activity=session.last_activity,
        duration_ms=session.duration_ms,
        message_count=len(session.messages),
        tool_calls_count=session.tool_calls_count,
    )


@router.delete("/session/{entity_id}")
async def end_session(entity_id: UUID):
    """End an active session for an entity."""
    session_manager = get_session_manager()
    session = await session_manager.get_session_by_entity(entity_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")
    
    await session_manager.close_session(session.session_id)
    
    return {"status": "ended", "session_id": str(session.session_id)}


@router.get("/stats", response_model=GatewayStatsResponse)
async def get_gateway_stats():
    """Get voice gateway statistics."""
    settings = get_settings()
    session_manager = get_session_manager()
    
    return GatewayStatsResponse(
        active_sessions=session_manager.active_session_count,
        max_sessions=settings.max_concurrent_sessions,
    )


@router.get("/voices")
async def list_available_voices():
    """List available voices for voice conversations."""
    return {
        "voices": [
            {"id": "Sal", "name": "Sal", "description": "Neutral, Smooth, balanced", "recommended": True},
            {"id": "Ara", "name": "Ara", "description": "Warm, Expressive", "recommended": False},
            {"id": "Eve", "name": "Eve", "description": "Clear, Professional", "recommended": False},
            {"id": "Rex", "name": "Rex", "description": "Deep, Authoritative", "recommended": False},
            {"id": "Leo", "name": "Leo", "description": "Energetic, Dynamic", "recommended": False},
        ]
    }


# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    settings = get_settings()
    
    # Startup
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    # Initialize session manager
    session_manager = get_session_manager()
    await session_manager.start()
    
    logger.info(f"Voice Gateway ready on port {settings.service_port}")
    logger.info(f"Using xAI voice: {settings.xai_voice}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Voice Gateway...")
    
    # Stop session manager
    await session_manager.stop()
    
    # Close NUCLEUS integration
    nucleus = get_nucleus_integration()
    await nucleus.close()
    
    logger.info("Voice Gateway shutdown complete")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="NUCLEUS Voice Gateway",
    description="""
    Real-time voice interface for NUCLEUS.
    
    Enables natural voice conversations with NUCLEUS using xAI Grok Voice Agent API.
    
    ## Features
    
    - **Real-time Voice**: Low-latency voice conversations
    - **Hebrew Support**: Native Hebrew language support
    - **Tool Calling**: Access to NUCLEUS capabilities (calendar, email, memory)
    - **Unified Experience**: Same brain, same memory as text chat
    
    ## WebSocket Protocol
    
    Connect to `/ws/{entity_id}` for voice conversations.
    """,
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST router
app.include_router(router, tags=["Voice Gateway"])


# =============================================================================
# Health Check
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    session_manager = get_session_manager()
    
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version,
        "active_sessions": session_manager.active_session_count,
    }


# =============================================================================
# WebSocket Handler
# =============================================================================

async def handle_voice_connection(
    websocket: WebSocket,
    entity_id: UUID,
    config: VoiceSessionConfig,
):
    """Handle a WebSocket connection for voice conversation."""
    session_manager = get_session_manager()
    xai_bridge = get_xai_bridge()
    nucleus = get_nucleus_integration()
    session = None
    
    try:
        # Accept WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for entity {entity_id}")
        
        # Create voice session
        session = await session_manager.create_session(
            entity_id=entity_id,
            client_ws=websocket,
            config=config,
        )
        
        # Main message loop
        while session.is_active:
            try:
                message = await websocket.receive_json()
                message_type = message.get("type")
                
                if message_type == "audio":
                    audio_data = message.get("data")
                    if audio_data:
                        await session.handle_client_audio(audio_data)
                
                elif message_type == "text":
                    content = message.get("content")
                    if content:
                        await session.handle_client_text(content)
                
                elif message_type == "control":
                    action = message.get("action")
                    if action == "interrupt" and session.xai_ws:
                        await xai_bridge.cancel_response(session.xai_ws)
                    elif action == "end_session":
                        session.is_active = False
                
            except WebSocketDisconnect:
                logger.info(f"Client disconnected from session {session.session_id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from client: {e}")
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
    
    except Exception as e:
        logger.error(f"Error in voice connection: {e}")
    
    finally:
        if session:
            await session_manager.close_session(session.session_id)
        try:
            await websocket.close()
        except:
            pass


# =============================================================================
# WebSocket Endpoint
# =============================================================================

@app.websocket("/ws/{entity_id}")
async def voice_websocket(
    websocket: WebSocket,
    entity_id: UUID,
    voice: str = Query(default="Sal", description="Voice to use"),
    language: str = Query(default="he", description="Language code"),
):
    """WebSocket endpoint for voice conversations."""
    config = VoiceSessionConfig(
        voice=voice,
        language=language,
    )
    
    await handle_voice_connection(
        websocket=websocket,
        entity_id=entity_id,
        config=config,
    )


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=False,
        log_level="info",
    )
