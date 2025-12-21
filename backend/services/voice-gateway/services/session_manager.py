"""
NUCLEUS Voice Gateway - Session Manager

Manages the lifecycle of voice sessions:
- Session creation and initialization
- Active session tracking
- Session cleanup and logging
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID

from fastapi import WebSocket

from config import get_settings
from models.session import EntityContext, VoiceSession, VoiceSessionConfig
from models.events import SessionState, VoiceSessionEvent
from services.xai_bridge import get_xai_bridge
from services.nucleus_integration import get_nucleus_integration

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages all active voice sessions.
    
    Responsibilities:
    - Create and initialize new sessions
    - Track active sessions
    - Handle session lifecycle events
    - Clean up expired sessions
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.xai_bridge = get_xai_bridge()
        self.nucleus = get_nucleus_integration()
        
        # Active sessions: session_id -> VoiceSession
        self._sessions: Dict[UUID, VoiceSession] = {}
        
        # Entity to session mapping (one session per entity)
        self._entity_sessions: Dict[UUID, UUID] = {}
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
    
    @property
    def active_session_count(self) -> int:
        """Get the number of active sessions."""
        return len(self._sessions)
    
    async def start(self):
        """Start the session manager background tasks."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Session manager started")
    
    async def stop(self):
        """Stop the session manager and clean up all sessions."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        # Close all active sessions
        for session in list(self._sessions.values()):
            await self.close_session(session.session_id)
        
        logger.info("Session manager stopped")
    
    async def create_session(
        self,
        entity_id: UUID,
        client_ws: WebSocket,
        config: Optional[VoiceSessionConfig] = None,
    ) -> VoiceSession:
        """
        Create and initialize a new voice session.
        
        Args:
            entity_id: The entity's UUID
            client_ws: WebSocket connection to the client
            config: Optional session configuration
        
        Returns:
            The created VoiceSession
        
        Raises:
            Exception: If session creation fails
        """
        # Check for existing session
        if entity_id in self._entity_sessions:
            existing_session_id = self._entity_sessions[entity_id]
            logger.info(f"Closing existing session {existing_session_id} for entity {entity_id}")
            await self.close_session(existing_session_id)
        
        # Check max sessions
        if self.active_session_count >= self.settings.max_concurrent_sessions:
            raise Exception("Maximum concurrent sessions reached")
        
        # Use default config if not provided
        if config is None:
            config = VoiceSessionConfig()
        
        # Load entity context from NUCLEUS
        entity_context = await self.nucleus.load_entity_context(entity_id)
        
        # Create session
        session = VoiceSession(
            entity_id=entity_id,
            client_ws=client_ws,
            config=config,
            entity_context=entity_context,
        )
        
        logger.info(f"Creating session {session.session_id} for entity {entity_id}")
        
        try:
            # Connect to xAI
            session.xai_ws = await self.xai_bridge.connect()
            
            # Configure xAI session
            await self.xai_bridge.configure_session(
                session.xai_ws,
                config,
                entity_context,
            )
            
            # Start xAI listener
            session._xai_listener_task = asyncio.create_task(
                self._xai_listener(session)
            )
            
            # Mark session as active
            session.is_active = True
            
            # Register session
            self._sessions[session.session_id] = session
            self._entity_sessions[entity_id] = session.session_id
            
            # Publish session started event
            await self.nucleus.publish_event(VoiceSessionEvent(
                type="voice.session.started",
                entity_id=entity_id,
                session_id=session.session_id,
                data={"config": config.model_dump()}
            ))
            
            logger.info(f"Session {session.session_id} created successfully")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            await session.close()
            raise
    
    async def get_session(self, session_id: UUID) -> Optional[VoiceSession]:
        """Get a session by ID."""
        return self._sessions.get(session_id)
    
    async def get_session_by_entity(self, entity_id: UUID) -> Optional[VoiceSession]:
        """Get a session by entity ID."""
        session_id = self._entity_sessions.get(entity_id)
        if session_id:
            return self._sessions.get(session_id)
        return None
    
    async def close_session(self, session_id: UUID):
        """
        Close a session and clean up resources.
        
        Args:
            session_id: The session to close
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for closing")
            return
        
        logger.info(f"Closing session {session_id}")
        
        try:
            # Log conversation to memory
            conversation_log = session.get_conversation_log()
            if conversation_log.messages:
                await self.nucleus.log_conversation(conversation_log)
            
            # Publish session ended event
            await self.nucleus.publish_event(VoiceSessionEvent(
                type="voice.session.ended",
                entity_id=session.entity_id,
                session_id=session_id,
                data={
                    "duration_ms": session.duration_ms,
                    "message_count": len(session.messages),
                    "tool_calls_count": session.tool_calls_count,
                }
            ))
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
        
        finally:
            # Close session
            await session.close()
            
            # Remove from tracking
            self._sessions.pop(session_id, None)
            if session.entity_id in self._entity_sessions:
                if self._entity_sessions[session.entity_id] == session_id:
                    del self._entity_sessions[session.entity_id]
            
            logger.info(f"Session {session_id} closed")
    
    async def _xai_listener(self, session: VoiceSession):
        """
        Listen for events from xAI and handle them.
        
        Args:
            session: The voice session
        """
        try:
            await self.xai_bridge.listen_for_events(
                session.xai_ws,
                session.handle_xai_event
            )
        except asyncio.CancelledError:
            logger.debug(f"xAI listener cancelled for session {session.session_id}")
        except Exception as e:
            logger.error(f"xAI listener error for session {session.session_id}: {e}")
            await session.set_state(SessionState.ERROR, str(e))
        finally:
            # Close session if listener exits
            if session.is_active:
                await self.close_session(session.session_id)
    
    async def _cleanup_loop(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Close sessions that have been inactive for too long."""
        timeout = timedelta(seconds=self.settings.session_timeout_seconds)
        now = datetime.utcnow()
        
        expired_sessions = [
            session_id
            for session_id, session in self._sessions.items()
            if (now - session.last_activity) > timeout
        ]
        
        for session_id in expired_sessions:
            logger.info(f"Closing expired session {session_id}")
            await self.close_session(session_id)


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
