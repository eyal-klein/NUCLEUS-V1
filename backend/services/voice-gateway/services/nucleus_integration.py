"""
NUCLEUS Voice Gateway - NUCLEUS Integration Service

Integrates the Voice Gateway with other NUCLEUS services:
- Memory Engine: Log conversations
- DNA Engine: Load user context
- Pub/Sub: Publish voice events
- Orchestrator: Execute tools
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

from config import get_settings
from models.session import EntityContext
from models.events import ConversationLog, VoiceSessionEvent

logger = logging.getLogger(__name__)


class NucleusIntegration:
    """
    Integrates Voice Gateway with NUCLEUS ecosystem.
    
    Provides:
    - Entity context loading from DNA Engine
    - Conversation logging to Memory Engine
    - Event publishing to Pub/Sub
    - Tool execution via Orchestrator
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
    
    # =========================================================================
    # DNA Engine Integration
    # =========================================================================
    
    async def load_entity_context(self, entity_id: UUID) -> Optional[EntityContext]:
        """
        Load entity DNA context from DNA Engine.
        
        Args:
            entity_id: The entity's UUID
        
        Returns:
            EntityContext with DNA information, or None if not found
        """
        try:
            # Get entity profile
            response = await self.http_client.get(
                f"{self.settings.dna_engine_url}/entity/{entity_id}"
            )
            
            if response.status_code == 404:
                logger.warning(f"Entity {entity_id} not found in DNA Engine")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant fields
            context = EntityContext(
                entity_id=entity_id,
                name=data.get("name", "User"),
                master_prompt=data.get("master_prompt"),
                values=[v.get("name") for v in data.get("values", [])],
                goals=[g.get("description") for g in data.get("goals", [])],
                communication_style=self._extract_communication_style(data),
                preferences=data.get("preferences", {}),
            )
            
            # Load recent context from memory
            context.recent_context = await self._load_recent_context(entity_id)
            
            logger.info(f"Loaded context for entity {entity_id}: {context.name}")
            return context
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to load entity context: {e}")
            return None
    
    def _extract_communication_style(self, entity_data: Dict[str, Any]) -> Optional[str]:
        """Extract communication style from entity data."""
        styles = entity_data.get("communication_styles", [])
        if styles:
            # Combine styles into a description
            style_names = [s.get("style_type", "") for s in styles[:3]]
            return ", ".join(style_names)
        return None
    
    async def _load_recent_context(self, entity_id: UUID) -> Optional[str]:
        """Load recent context from Memory Engine."""
        try:
            response = await self.http_client.get(
                f"{self.settings.memory_engine_url}/recent/{entity_id}",
                params={"limit": 5}
            )
            
            if response.status_code != 200:
                return None
            
            memories = response.json()
            if not memories:
                return None
            
            # Format recent memories as context
            context_parts = []
            for memory in memories[:3]:
                summary = memory.get("summary", "")
                if summary:
                    context_parts.append(f"- {summary}")
            
            if context_parts:
                return "פעילות אחרונה:\n" + "\n".join(context_parts)
            
            return None
            
        except httpx.HTTPError as e:
            logger.warning(f"Failed to load recent context: {e}")
            return None
    
    # =========================================================================
    # Memory Engine Integration
    # =========================================================================
    
    async def log_conversation(self, conversation: ConversationLog):
        """
        Log a voice conversation to Memory Engine.
        
        Args:
            conversation: The conversation log to store
        """
        try:
            # Format for Memory Engine
            memory_data = {
                "entity_id": str(conversation.entity_id),
                "interaction_type": "conversation",
                "channel": "voice",
                "content": self._format_conversation_content(conversation),
                "metadata": {
                    "session_id": str(conversation.session_id),
                    "duration_ms": conversation.total_duration_ms,
                    "tool_calls_count": conversation.tool_calls_count,
                    "message_count": len(conversation.messages),
                    **conversation.metadata
                },
                "timestamp": conversation.started_at.isoformat(),
            }
            
            response = await self.http_client.post(
                f"{self.settings.memory_engine_url}/log",
                json=memory_data
            )
            response.raise_for_status()
            
            logger.info(
                f"Logged conversation {conversation.session_id} "
                f"({len(conversation.messages)} messages, "
                f"{conversation.total_duration_ms}ms)"
            )
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to log conversation: {e}")
    
    def _format_conversation_content(self, conversation: ConversationLog) -> str:
        """Format conversation messages as text content."""
        parts = []
        for msg in conversation.messages:
            role = "משתמש" if msg.role.value == "user" else "NUCLEUS"
            parts.append(f"{role}: {msg.content}")
        return "\n".join(parts)
    
    # =========================================================================
    # Pub/Sub Integration
    # =========================================================================
    
    async def publish_event(self, event: VoiceSessionEvent):
        """
        Publish a voice event to Pub/Sub.
        
        Args:
            event: The event to publish
        """
        if not self.settings.pubsub_project_id:
            logger.debug("Pub/Sub not configured, skipping event publish")
            return
        
        try:
            # For now, we'll use HTTP to publish (can be replaced with direct Pub/Sub client)
            # This assumes there's a Pub/Sub proxy or the orchestrator handles it
            
            event_data = {
                "type": event.type,
                "entity_id": str(event.entity_id),
                "session_id": str(event.session_id),
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
                "source": event.source,
                "version": event.version,
            }
            
            response = await self.http_client.post(
                f"{self.settings.orchestrator_url}/events/publish",
                json={
                    "topic": self.settings.pubsub_topic_voice_events,
                    "event": event_data
                }
            )
            response.raise_for_status()
            
            logger.debug(f"Published event: {event.type}")
            
        except httpx.HTTPError as e:
            logger.warning(f"Failed to publish event: {e}")
    
    # =========================================================================
    # Tool Execution
    # =========================================================================
    
    async def execute_tool(
        self,
        entity_id: UUID,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a NUCLEUS tool and return the result.
        
        Args:
            entity_id: The entity making the request
            tool_name: Name of the tool to execute
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        """
        logger.info(f"Executing tool: {tool_name} for entity {entity_id}")
        
        try:
            # Route to appropriate service based on tool name
            if tool_name == "get_calendar_events":
                return await self._get_calendar_events(entity_id, arguments)
            
            elif tool_name == "create_calendar_event":
                return await self._create_calendar_event(entity_id, arguments)
            
            elif tool_name == "get_recent_emails":
                return await self._get_recent_emails(entity_id, arguments)
            
            elif tool_name == "send_email":
                return await self._send_email(entity_id, arguments)
            
            elif tool_name == "get_memory_context":
                return await self._get_memory_context(entity_id, arguments)
            
            elif tool_name == "create_task":
                return await self._create_task(entity_id, arguments)
            
            elif tool_name == "get_contacts":
                return await self._get_contacts(entity_id, arguments)
            
            elif tool_name == "get_user_preferences":
                return await self._get_user_preferences(entity_id, arguments)
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": str(e)}
    
    async def _get_calendar_events(
        self,
        entity_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get calendar events from Calendar Connector."""
        response = await self.http_client.get(
            f"{self.settings.orchestrator_url}/calendar/{entity_id}/events",
            params={
                "days_ahead": args.get("days_ahead", 7),
                "include_details": args.get("include_details", True)
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def _create_calendar_event(
        self,
        entity_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create calendar event via Calendar Connector."""
        response = await self.http_client.post(
            f"{self.settings.orchestrator_url}/calendar/{entity_id}/events",
            json=args
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_recent_emails(
        self,
        entity_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get recent emails from Gmail Connector."""
        response = await self.http_client.get(
            f"{self.settings.orchestrator_url}/email/{entity_id}/messages",
            params={
                "count": args.get("count", 10),
                "unread_only": args.get("unread_only", False)
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def _send_email(
        self,
        entity_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send email via Gmail Connector."""
        response = await self.http_client.post(
            f"{self.settings.orchestrator_url}/email/{entity_id}/send",
            json=args
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_memory_context(
        self,
        entity_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search memory via Memory Engine."""
        response = await self.http_client.post(
            f"{self.settings.memory_engine_url}/search",
            json={
                "entity_id": str(entity_id),
                "query": args.get("query"),
                "time_range_days": args.get("time_range_days", 30),
                "memory_types": args.get("memory_types")
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def _create_task(
        self,
        entity_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create task via Task Manager."""
        response = await self.http_client.post(
            f"{self.settings.orchestrator_url}/tasks/{entity_id}",
            json=args
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_contacts(
        self,
        entity_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search contacts via Relationship Builder."""
        response = await self.http_client.get(
            f"{self.settings.orchestrator_url}/contacts/{entity_id}/search",
            params={
                "query": args.get("query"),
                "limit": args.get("limit", 5)
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def _get_user_preferences(
        self,
        entity_id: UUID,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get user preferences from DNA Engine."""
        response = await self.http_client.get(
            f"{self.settings.dna_engine_url}/entity/{entity_id}/preferences",
            params={"category": args.get("category")}
        )
        response.raise_for_status()
        return response.json()


# Singleton instance
_nucleus_integration: Optional[NucleusIntegration] = None


def get_nucleus_integration() -> NucleusIntegration:
    """Get or create the global NUCLEUS integration instance."""
    global _nucleus_integration
    if _nucleus_integration is None:
        _nucleus_integration = NucleusIntegration()
    return _nucleus_integration
