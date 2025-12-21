"""
NUCLEUS Voice Gateway - Event Models

Defines all event types for communication between:
- Client <-> Voice Gateway
- Voice Gateway <-> xAI
- Voice Gateway <-> NUCLEUS services
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class SessionState(str, Enum):
    """Voice session states."""
    INITIALIZING = "initializing"
    READY = "ready"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    TOOL_EXECUTING = "tool_executing"
    ENDED = "ended"
    ERROR = "error"


class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


# =============================================================================
# Client <-> Voice Gateway Events
# =============================================================================

class ClientAudioEvent(BaseModel):
    """Audio data from client."""
    type: Literal["audio"] = "audio"
    data: str  # Base64 encoded audio


class ClientTextEvent(BaseModel):
    """Text message from client (for hybrid mode)."""
    type: Literal["text"] = "text"
    content: str


class ClientControlEvent(BaseModel):
    """Control commands from client."""
    type: Literal["control"] = "control"
    action: Literal["interrupt", "end_session", "mute", "unmute"]


class ServerAudioEvent(BaseModel):
    """Audio data to client."""
    type: Literal["audio"] = "audio"
    data: str  # Base64 encoded audio


class ServerTranscriptEvent(BaseModel):
    """Transcript update to client."""
    type: Literal["transcript"] = "transcript"
    role: MessageRole
    content: str
    is_final: bool = False


class ServerStatusEvent(BaseModel):
    """Status update to client."""
    type: Literal["status"] = "status"
    state: SessionState
    message: Optional[str] = None


class ServerToolCallEvent(BaseModel):
    """Tool call notification to client."""
    type: Literal["tool_call"] = "tool_call"
    name: str
    status: Literal["executing", "completed", "failed"]
    result: Optional[str] = None


class ServerErrorEvent(BaseModel):
    """Error notification to client."""
    type: Literal["error"] = "error"
    code: str
    message: str


# =============================================================================
# xAI Event Types
# =============================================================================

class XAIClientEvent(BaseModel):
    """Base class for events sent to xAI."""
    type: str


class XAISessionUpdate(XAIClientEvent):
    """Session configuration update for xAI."""
    type: Literal["session.update"] = "session.update"
    session: Dict[str, Any]


class XAIInputAudioAppend(XAIClientEvent):
    """Append audio to xAI input buffer."""
    type: Literal["input_audio_buffer.append"] = "input_audio_buffer.append"
    audio: str  # Base64 encoded


class XAIInputAudioCommit(XAIClientEvent):
    """Commit audio buffer to xAI."""
    type: Literal["input_audio_buffer.commit"] = "input_audio_buffer.commit"


class XAIResponseCreate(XAIClientEvent):
    """Request response from xAI."""
    type: Literal["response.create"] = "response.create"
    response: Optional[Dict[str, Any]] = None


class XAIConversationItemCreate(XAIClientEvent):
    """Add item to conversation."""
    type: Literal["conversation.item.create"] = "conversation.item.create"
    item: Dict[str, Any]


# =============================================================================
# NUCLEUS Internal Events
# =============================================================================

class VoiceSessionEvent(BaseModel):
    """Event for NUCLEUS Pub/Sub."""
    type: str
    entity_id: UUID
    session_id: UUID
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "voice-gateway"
    version: str = "2.0.0"


class ConversationMessage(BaseModel):
    """A single message in the conversation."""
    id: UUID = Field(default_factory=uuid4)
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    audio_duration_ms: Optional[int] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ConversationLog(BaseModel):
    """Complete conversation log for memory storage."""
    session_id: UUID
    entity_id: UUID
    messages: List[ConversationMessage]
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_duration_ms: Optional[int] = None
    tool_calls_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
