"""
NUCLEUS Voice Gateway - REST API Handler

Provides REST endpoints for voice gateway management.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..config import get_settings
from ..models.session import VoiceSessionConfig
from ..services.session_manager import get_session_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Request/Response Models
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


class VoiceSettingsRequest(BaseModel):
    """Request to update voice settings."""
    voice: Optional[str] = None
    language: Optional[str] = None
    custom_instructions: Optional[str] = None
    tools_enabled: Optional[bool] = None
    web_search_enabled: Optional[bool] = None
    x_search_enabled: Optional[bool] = None


class VoiceSettingsResponse(BaseModel):
    """Response with voice settings."""
    voice: str
    language: str
    custom_instructions: Optional[str]
    tools_enabled: bool
    web_search_enabled: bool
    x_search_enabled: bool


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
    uptime_seconds: int


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/session", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """
    Create a new voice session token.
    
    Returns a WebSocket URL that the client can connect to.
    """
    settings = get_settings()
    
    # Generate session token
    session_id = uuid4()
    
    # Build WebSocket URL
    # In production, this would be the actual service URL
    ws_url = f"wss://voice-gateway.nucleus.ai/ws/{request.entity_id}"
    
    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(seconds=settings.session_timeout_seconds)
    
    logger.info(f"Created session token for entity {request.entity_id}")
    
    return SessionResponse(
        session_id=session_id,
        ws_url=ws_url,
        expires_at=expires_at,
    )


@router.get("/session/{entity_id}", response_model=SessionStatusResponse)
async def get_session_status(entity_id: UUID):
    """
    Get the status of an active session for an entity.
    """
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
    """
    End an active session for an entity.
    """
    session_manager = get_session_manager()
    session = await session_manager.get_session_by_entity(entity_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="No active session found")
    
    await session_manager.close_session(session.session_id)
    
    return {"status": "ended", "session_id": str(session.session_id)}


@router.get("/settings/{entity_id}", response_model=VoiceSettingsResponse)
async def get_voice_settings(entity_id: UUID):
    """
    Get voice settings for an entity.
    
    Returns default settings if no custom settings are stored.
    """
    # In a full implementation, this would load from database
    # For now, return defaults
    settings = get_settings()
    
    return VoiceSettingsResponse(
        voice=settings.xai_voice,
        language="he",
        custom_instructions=None,
        tools_enabled=True,
        web_search_enabled=True,
        x_search_enabled=True,
    )


@router.put("/settings/{entity_id}", response_model=VoiceSettingsResponse)
async def update_voice_settings(entity_id: UUID, request: VoiceSettingsRequest):
    """
    Update voice settings for an entity.
    """
    # In a full implementation, this would save to database
    # For now, just return the updated settings
    settings = get_settings()
    
    return VoiceSettingsResponse(
        voice=request.voice or settings.xai_voice,
        language=request.language or "he",
        custom_instructions=request.custom_instructions,
        tools_enabled=request.tools_enabled if request.tools_enabled is not None else True,
        web_search_enabled=request.web_search_enabled if request.web_search_enabled is not None else True,
        x_search_enabled=request.x_search_enabled if request.x_search_enabled is not None else True,
    )


@router.get("/stats", response_model=GatewayStatsResponse)
async def get_gateway_stats():
    """
    Get voice gateway statistics.
    """
    settings = get_settings()
    session_manager = get_session_manager()
    
    # Calculate uptime (simplified - in production would track actual start time)
    uptime_seconds = 0  # Would be calculated from service start time
    
    return GatewayStatsResponse(
        active_sessions=session_manager.active_session_count,
        max_sessions=settings.max_concurrent_sessions,
        uptime_seconds=uptime_seconds,
    )


@router.get("/voices")
async def list_available_voices():
    """
    List available voices for voice conversations.
    """
    return {
        "voices": [
            {
                "id": "Sal",
                "name": "Sal",
                "description": "Neutral, Smooth, balanced - versatile voice",
                "language_support": ["en", "he", "multi"],
                "recommended": True,
            },
            {
                "id": "Ara",
                "name": "Ara",
                "description": "Warm, Expressive - friendly voice",
                "language_support": ["en", "he", "multi"],
                "recommended": False,
            },
            {
                "id": "Eve",
                "name": "Eve",
                "description": "Clear, Professional - business voice",
                "language_support": ["en", "he", "multi"],
                "recommended": False,
            },
            {
                "id": "Rex",
                "name": "Rex",
                "description": "Deep, Authoritative - confident voice",
                "language_support": ["en", "he", "multi"],
                "recommended": False,
            },
            {
                "id": "Leo",
                "name": "Leo",
                "description": "Energetic, Dynamic - engaging voice",
                "language_support": ["en", "he", "multi"],
                "recommended": False,
            },
        ]
    }
