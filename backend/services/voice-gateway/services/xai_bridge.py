"""
NUCLEUS Voice Gateway - xAI Bridge Service

Handles all communication with the xAI Grok Voice Agent API.
Manages WebSocket connections, session configuration, and event handling.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

import websockets
from websockets.client import WebSocketClientProtocol

from config import get_settings, HEBREW_INSTRUCTION, FOUR_OPTIONS_PROTOCOL
from models.session import EntityContext, VoiceSessionConfig
from models.tools import get_all_tools

logger = logging.getLogger(__name__)


class XAIBridge:
    """
    Bridge for communicating with xAI Grok Voice Agent API.
    
    Handles:
    - WebSocket connection establishment
    - Session configuration
    - Audio streaming
    - Event parsing
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.ws_url = self.settings.xai_ws_url
        self.api_key = self.settings.xai_api_key
    
    async def connect(self) -> WebSocketClientProtocol:
        """
        Establish WebSocket connection to xAI.
        
        Returns:
            WebSocket connection to xAI Realtime API
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"  # xAI uses OpenAI-compatible header
        }
        
        logger.info(f"Connecting to xAI at {self.ws_url}")
        
        try:
            ws = await websockets.connect(
                self.ws_url,
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )
            logger.info("Successfully connected to xAI")
            return ws
        except Exception as e:
            logger.error(f"Failed to connect to xAI: {e}")
            raise
    
    def build_instructions(
        self,
        entity_context: Optional[EntityContext] = None,
        custom_instructions: Optional[str] = None,
    ) -> str:
        """
        Build the system instructions for the xAI session.
        
        Combines:
        - Entity DNA (master prompt, values, goals)
        - Hebrew language instruction
        - 4 Options Protocol
        - Custom instructions
        
        Args:
            entity_context: User's DNA context from NUCLEUS
            custom_instructions: Additional custom instructions
        
        Returns:
            Complete instruction string for xAI
        """
        parts = []
        
        # Entity identity
        if entity_context:
            parts.append(f"""
# זהות
אתה NUCLEUS, השותף האסטרטגי של {entity_context.name}.
אתה ה-HOW, {entity_context.name} הוא ה-WHAT וה-WHY.
המטרה שלכם: לשגשג ביחד.

## תפקידך
{entity_context.master_prompt or 'לעזור ולתמוך בכל דרך אפשרית.'}
""")
            
            # Values
            if entity_context.values:
                values_str = ", ".join(entity_context.values[:5])
                parts.append(f"\n## ערכים מנחים\n{values_str}")
            
            # Goals
            if entity_context.goals:
                goals_str = "\n".join([f"- {g}" for g in entity_context.goals[:3]])
                parts.append(f"\n## מטרות נוכחיות\n{goals_str}")
            
            # Communication style
            if entity_context.communication_style:
                parts.append(f"\n## סגנון תקשורת\n{entity_context.communication_style}")
            
            # Recent context
            if entity_context.recent_context:
                parts.append(f"\n## הקשר אחרון\n{entity_context.recent_context}")
        else:
            parts.append("""
# זהות
אתה NUCLEUS, עוזר אישי חכם.
המטרה שלך: לעזור למשתמש לשגשג.
""")
        
        # Hebrew instruction
        parts.append(f"\n# שפה\n{HEBREW_INSTRUCTION}")
        
        # 4 Options Protocol
        parts.append(f"\n{FOUR_OPTIONS_PROTOCOL}")
        
        # Custom instructions
        if custom_instructions:
            parts.append(f"\n# הנחיות נוספות\n{custom_instructions}")
        
        return "\n".join(parts)
    
    def build_session_config(
        self,
        config: VoiceSessionConfig,
        entity_context: Optional[EntityContext] = None,
    ) -> Dict[str, Any]:
        """
        Build the session.update configuration for xAI.
        
        Args:
            config: Voice session configuration
            entity_context: User's DNA context
        
        Returns:
            Session configuration dictionary
        """
        instructions = self.build_instructions(
            entity_context=entity_context,
            custom_instructions=config.custom_instructions,
        )
        
        # Build tools list
        tools = get_all_tools(
            include_web_search=config.web_search_enabled,
            include_x_search=config.x_search_enabled,
        ) if config.tools_enabled else []
        
        return {
            "type": "session.update",
            "session": {
                "voice": config.voice,
                "instructions": instructions,
                "input_audio_format": config.audio_format,
                "output_audio_format": config.audio_format,
                "input_audio_transcription": {
                    "model": "grok-2-vision-latest"  # For transcription
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": self.settings.vad_threshold,
                    "prefix_padding_ms": self.settings.vad_prefix_padding_ms,
                    "silence_duration_ms": self.settings.vad_silence_duration_ms,
                    "create_response": True,
                    "interrupt_response": True,
                },
                "tools": tools,
            }
        }
    
    async def configure_session(
        self,
        ws: WebSocketClientProtocol,
        config: VoiceSessionConfig,
        entity_context: Optional[EntityContext] = None,
    ):
        """
        Send session configuration to xAI.
        
        Args:
            ws: WebSocket connection
            config: Voice session configuration
            entity_context: User's DNA context
        """
        session_config = self.build_session_config(config, entity_context)
        
        logger.info(f"Configuring xAI session with voice={config.voice}")
        await ws.send(json.dumps(session_config))
    
    async def send_audio(self, ws: WebSocketClientProtocol, audio_data: str):
        """
        Send audio data to xAI.
        
        Args:
            ws: WebSocket connection
            audio_data: Base64 encoded audio
        """
        await ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": audio_data
        }))
    
    async def commit_audio(self, ws: WebSocketClientProtocol):
        """
        Commit the audio buffer to trigger processing.
        
        Args:
            ws: WebSocket connection
        """
        await ws.send(json.dumps({
            "type": "input_audio_buffer.commit"
        }))
    
    async def request_response(
        self,
        ws: WebSocketClientProtocol,
        modalities: Optional[List[str]] = None,
    ):
        """
        Request a response from xAI.
        
        Args:
            ws: WebSocket connection
            modalities: Response modalities (default: ["text", "audio"])
        """
        response_config = {
            "type": "response.create",
        }
        
        if modalities:
            response_config["response"] = {"modalities": modalities}
        
        await ws.send(json.dumps(response_config))
    
    async def send_tool_result(
        self,
        ws: WebSocketClientProtocol,
        call_id: str,
        result: str,
    ):
        """
        Send tool execution result back to xAI.
        
        Args:
            ws: WebSocket connection
            call_id: The tool call ID from xAI
            result: JSON string of the tool result
        """
        await ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": result
            }
        }))
        
        # Request response after tool result
        await self.request_response(ws)
    
    async def cancel_response(self, ws: WebSocketClientProtocol):
        """
        Cancel the current response (for interruption).
        
        Args:
            ws: WebSocket connection
        """
        await ws.send(json.dumps({
            "type": "response.cancel"
        }))
    
    async def listen_for_events(
        self,
        ws: WebSocketClientProtocol,
        callback: Callable[[Dict[str, Any]], None],
    ):
        """
        Listen for events from xAI and call the callback for each.
        
        Args:
            ws: WebSocket connection
            callback: Async function to call for each event
        """
        try:
            async for message in ws:
                try:
                    event = json.loads(message)
                    await callback(event)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse xAI message: {e}")
        except websockets.ConnectionClosed as e:
            logger.info(f"xAI connection closed: {e}")
        except Exception as e:
            logger.error(f"Error in xAI listener: {e}")


# Singleton instance
_xai_bridge: Optional[XAIBridge] = None


def get_xai_bridge() -> XAIBridge:
    """Get or create the global xAI bridge instance."""
    global _xai_bridge
    if _xai_bridge is None:
        _xai_bridge = XAIBridge()
    return _xai_bridge
