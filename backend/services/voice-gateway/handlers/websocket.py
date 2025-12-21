"""
NUCLEUS Voice Gateway - WebSocket Handler

Handles WebSocket connections from clients for voice conversations.
"""

import asyncio
import json
import logging
from typing import Any, Dict
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect

from ..models.session import VoiceSession, VoiceSessionConfig
from ..models.events import (
    ClientAudioEvent,
    ClientTextEvent,
    ClientControlEvent,
    ServerErrorEvent,
    SessionState,
)
from ..services.session_manager import get_session_manager
from ..services.xai_bridge import get_xai_bridge
from ..services.nucleus_integration import get_nucleus_integration
from .tools import handle_tool_call

logger = logging.getLogger(__name__)


async def handle_voice_connection(
    websocket: WebSocket,
    entity_id: UUID,
    config: VoiceSessionConfig,
):
    """
    Handle a WebSocket connection for voice conversation.
    
    Args:
        websocket: The WebSocket connection
        entity_id: The entity's UUID
        config: Session configuration
    """
    session_manager = get_session_manager()
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
                # Receive message from client
                message = await websocket.receive_json()
                await handle_client_message(session, message)
                
            except WebSocketDisconnect:
                logger.info(f"Client disconnected from session {session.session_id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from client: {e}")
                await session.send_to_client(ServerErrorEvent(
                    code="invalid_json",
                    message="Invalid JSON message"
                ))
            except Exception as e:
                logger.error(f"Error handling client message: {e}")
                await session.send_to_client(ServerErrorEvent(
                    code="internal_error",
                    message=str(e)
                ))
    
    except Exception as e:
        logger.error(f"Error in voice connection: {e}")
        try:
            await websocket.send_json(ServerErrorEvent(
                code="connection_error",
                message=str(e)
            ).model_dump())
        except:
            pass
    
    finally:
        # Clean up session
        if session:
            await session_manager.close_session(session.session_id)
        
        # Close WebSocket if still open
        try:
            await websocket.close()
        except:
            pass


async def handle_client_message(session: VoiceSession, message: Dict[str, Any]):
    """
    Handle a message from the client.
    
    Args:
        session: The voice session
        message: The message from the client
    """
    message_type = message.get("type")
    
    if message_type == "audio":
        # Audio data from client
        audio_data = message.get("data")
        if audio_data:
            await session.handle_client_audio(audio_data)
    
    elif message_type == "text":
        # Text message (hybrid mode)
        content = message.get("content")
        if content:
            await session.handle_client_text(content)
    
    elif message_type == "control":
        # Control command
        action = message.get("action")
        await handle_control_action(session, action)
    
    elif message_type == "config":
        # Configuration update
        await handle_config_update(session, message)
    
    else:
        logger.warning(f"Unknown message type: {message_type}")


async def handle_control_action(session: VoiceSession, action: str):
    """
    Handle a control action from the client.
    
    Args:
        session: The voice session
        action: The control action
    """
    xai_bridge = get_xai_bridge()
    
    if action == "interrupt":
        # Cancel current response
        logger.info(f"Session {session.session_id}: Interrupt requested")
        if session.xai_ws:
            await xai_bridge.cancel_response(session.xai_ws)
        await session.set_state(SessionState.READY)
    
    elif action == "end_session":
        # End the session
        logger.info(f"Session {session.session_id}: End session requested")
        session.is_active = False
    
    elif action == "mute":
        # Mute (stop sending audio)
        logger.info(f"Session {session.session_id}: Mute requested")
        # Client-side action, no server action needed
    
    elif action == "unmute":
        # Unmute (resume sending audio)
        logger.info(f"Session {session.session_id}: Unmute requested")
        # Client-side action, no server action needed
    
    else:
        logger.warning(f"Unknown control action: {action}")


async def handle_config_update(session: VoiceSession, message: Dict[str, Any]):
    """
    Handle a configuration update from the client.
    
    Args:
        session: The voice session
        message: The configuration message
    """
    xai_bridge = get_xai_bridge()
    
    # Update session config
    if "voice" in message:
        session.config.voice = message["voice"]
    if "custom_instructions" in message:
        session.config.custom_instructions = message["custom_instructions"]
    
    # Send updated config to xAI
    if session.xai_ws:
        await xai_bridge.configure_session(
            session.xai_ws,
            session.config,
            session.entity_context,
        )
    
    logger.info(f"Session {session.session_id}: Configuration updated")


async def handle_xai_tool_call(
    session: VoiceSession,
    call_id: str,
    tool_name: str,
    arguments: str,
):
    """
    Handle a tool call from xAI.
    
    Args:
        session: The voice session
        call_id: The tool call ID
        tool_name: Name of the tool
        arguments: JSON string of arguments
    """
    xai_bridge = get_xai_bridge()
    nucleus = get_nucleus_integration()
    
    try:
        # Parse arguments
        args = json.loads(arguments) if arguments else {}
        
        # Execute tool
        result = await nucleus.execute_tool(
            entity_id=session.entity_id,
            tool_name=tool_name,
            arguments=args,
        )
        
        # Send result back to xAI
        if session.xai_ws:
            await xai_bridge.send_tool_result(
                session.xai_ws,
                call_id,
                json.dumps(result, ensure_ascii=False)
            )
        
        logger.info(f"Tool {tool_name} executed successfully")
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        
        # Send error result to xAI
        if session.xai_ws:
            await xai_bridge.send_tool_result(
                session.xai_ws,
                call_id,
                json.dumps({"error": str(e)})
            )
