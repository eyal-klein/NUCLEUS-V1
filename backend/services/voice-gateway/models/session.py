"""
NUCLEUS Voice Gateway - Session Models

Defines the VoiceSession class that manages a single voice conversation.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import websockets
from fastapi import WebSocket
from pydantic import BaseModel, Field

from .events import (
    ConversationLog,
    ConversationMessage,
    MessageRole,
    SessionState,
    ServerAudioEvent,
    ServerStatusEvent,
    ServerTranscriptEvent,
    ServerToolCallEvent,
    ServerErrorEvent,
)

logger = logging.getLogger(__name__)


class EntityContext(BaseModel):
    """Context loaded from NUCLEUS DNA and Memory."""
    entity_id: UUID
    name: str
    master_prompt: Optional[str] = None
    values: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    communication_style: Optional[str] = None
    recent_context: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)


class VoiceSessionConfig(BaseModel):
    """Configuration for a voice session."""
    voice: str = "Sal"
    language: str = "he"
    audio_format: str = "audio/pcm"
    sample_rate: int = 24000
    custom_instructions: Optional[str] = None
    tools_enabled: bool = True
    web_search_enabled: bool = True
    x_search_enabled: bool = True


class VoiceSession:
    """
    Manages a single voice conversation session.
    
    Handles:
    - WebSocket connections (client and xAI)
    - Audio streaming
    - State management
    - Conversation logging
    - Tool execution
    """
    
    def __init__(
        self,
        entity_id: UUID,
        client_ws: WebSocket,
        config: VoiceSessionConfig,
        entity_context: Optional[EntityContext] = None,
    ):
        # Identity
        self.session_id = uuid4()
        self.entity_id = entity_id
        
        # Connections
        self.client_ws = client_ws
        self.xai_ws: Optional[websockets.WebSocketClientProtocol] = None
        
        # Configuration
        self.config = config
        self.entity_context = entity_context
        
        # State
        self.state = SessionState.INITIALIZING
        self.is_active = False
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        
        # Conversation
        self.messages: List[ConversationMessage] = []
        self.current_user_transcript = ""
        self.current_assistant_transcript = ""
        self.tool_calls_count = 0
        
        # Tasks
        self._xai_listener_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    @property
    def duration_ms(self) -> int:
        """Get session duration in milliseconds."""
        delta = datetime.utcnow() - self.created_at
        return int(delta.total_seconds() * 1000)
    
    async def set_state(self, new_state: SessionState, message: Optional[str] = None):
        """Update session state and notify client."""
        self.state = new_state
        self.last_activity = datetime.utcnow()
        
        logger.info(f"Session {self.session_id}: State changed to {new_state}")
        
        # Notify client
        await self.send_to_client(ServerStatusEvent(
            state=new_state,
            message=message
        ))
    
    async def send_to_client(self, event: BaseModel):
        """Send an event to the client WebSocket."""
        try:
            await self.client_ws.send_json(event.model_dump())
        except Exception as e:
            logger.error(f"Session {self.session_id}: Failed to send to client: {e}")
    
    async def send_to_xai(self, event: Dict[str, Any]):
        """Send an event to the xAI WebSocket."""
        if self.xai_ws is None:
            logger.error(f"Session {self.session_id}: xAI WebSocket not connected")
            return
        
        try:
            await self.xai_ws.send(json.dumps(event))
        except Exception as e:
            logger.error(f"Session {self.session_id}: Failed to send to xAI: {e}")
    
    async def handle_client_audio(self, audio_data: str):
        """Handle audio data from client."""
        self.last_activity = datetime.utcnow()
        
        if self.state not in [SessionState.READY, SessionState.LISTENING]:
            await self.set_state(SessionState.LISTENING)
        
        # Forward to xAI
        await self.send_to_xai({
            "type": "input_audio_buffer.append",
            "audio": audio_data
        })
    
    async def handle_client_text(self, text: str):
        """Handle text input from client (hybrid mode)."""
        self.last_activity = datetime.utcnow()
        
        # Add to conversation
        message = ConversationMessage(
            role=MessageRole.USER,
            content=text
        )
        self.messages.append(message)
        
        # Send to xAI as conversation item
        await self.send_to_xai({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}]
            }
        })
        
        # Request response
        await self.send_to_xai({"type": "response.create"})
    
    async def handle_xai_event(self, event: Dict[str, Any]):
        """Handle an event from xAI."""
        event_type = event.get("type", "")
        
        logger.debug(f"Session {self.session_id}: xAI event: {event_type}")
        
        if event_type == "session.created":
            await self.set_state(SessionState.READY, "Session ready")
        
        elif event_type == "session.updated":
            logger.info(f"Session {self.session_id}: Session configuration updated")
        
        elif event_type == "input_audio_buffer.speech_started":
            await self.set_state(SessionState.LISTENING)
        
        elif event_type == "input_audio_buffer.speech_stopped":
            await self.set_state(SessionState.THINKING)
        
        elif event_type == "response.audio_transcript.delta":
            # Assistant is speaking - accumulate transcript
            delta = event.get("delta", "")
            self.current_assistant_transcript += delta
            await self.send_to_client(ServerTranscriptEvent(
                role=MessageRole.ASSISTANT,
                content=delta,
                is_final=False
            ))
        
        elif event_type == "response.audio.delta":
            # Audio chunk from assistant
            audio_data = event.get("delta", "")
            if audio_data:
                await self.set_state(SessionState.SPEAKING)
                await self.send_to_client(ServerAudioEvent(data=audio_data))
        
        elif event_type == "response.audio.done":
            # Audio response complete
            if self.current_assistant_transcript:
                self.messages.append(ConversationMessage(
                    role=MessageRole.ASSISTANT,
                    content=self.current_assistant_transcript
                ))
                await self.send_to_client(ServerTranscriptEvent(
                    role=MessageRole.ASSISTANT,
                    content=self.current_assistant_transcript,
                    is_final=True
                ))
                self.current_assistant_transcript = ""
            await self.set_state(SessionState.READY)
        
        elif event_type == "conversation.item.input_audio_transcription.completed":
            # User speech transcription complete
            transcript = event.get("transcript", "")
            if transcript:
                self.messages.append(ConversationMessage(
                    role=MessageRole.USER,
                    content=transcript
                ))
                await self.send_to_client(ServerTranscriptEvent(
                    role=MessageRole.USER,
                    content=transcript,
                    is_final=True
                ))
        
        elif event_type == "response.function_call_arguments.done":
            # Tool call complete - need to execute
            call_id = event.get("call_id")
            name = event.get("name")
            arguments = event.get("arguments", "{}")
            
            await self.send_to_client(ServerToolCallEvent(
                name=name,
                status="executing"
            ))
            
            # Tool execution will be handled by the tool handler
            # This is a placeholder - actual execution happens in handlers/tools.py
            self.tool_calls_count += 1
        
        elif event_type == "error":
            error = event.get("error", {})
            await self.send_to_client(ServerErrorEvent(
                code=error.get("code", "unknown"),
                message=error.get("message", "Unknown error")
            ))
    
    def get_conversation_log(self) -> ConversationLog:
        """Get the complete conversation log for memory storage."""
        return ConversationLog(
            session_id=self.session_id,
            entity_id=self.entity_id,
            messages=self.messages,
            started_at=self.created_at,
            ended_at=datetime.utcnow(),
            total_duration_ms=self.duration_ms,
            tool_calls_count=self.tool_calls_count,
            metadata={
                "voice": self.config.voice,
                "language": self.config.language,
                "state_at_end": self.state.value
            }
        )
    
    async def close(self):
        """Close the session and clean up resources."""
        logger.info(f"Session {self.session_id}: Closing session")
        
        self.is_active = False
        await self.set_state(SessionState.ENDED)
        
        # Cancel background tasks
        if self._xai_listener_task:
            self._xai_listener_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        
        # Close xAI connection
        if self.xai_ws:
            try:
                await self.xai_ws.close()
            except Exception as e:
                logger.error(f"Session {self.session_id}: Error closing xAI connection: {e}")
        
        logger.info(f"Session {self.session_id}: Session closed after {self.duration_ms}ms")
