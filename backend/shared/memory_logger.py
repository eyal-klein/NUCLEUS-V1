"""
NUCLEUS V2.0 - Memory Logger Client
Utility for logging interactions to Memory Engine
"""

import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class MemoryLogger:
    """Client for logging interactions to Memory Engine"""
    
    def __init__(self, memory_engine_url: Optional[str] = None):
        """
        Initialize Memory Logger
        
        Args:
            memory_engine_url: URL of Memory Engine service
                              Defaults to MEMORY_ENGINE_URL env var
        """
        self.memory_engine_url = memory_engine_url or os.getenv(
            "MEMORY_ENGINE_URL",
            "https://nucleus-memory-engine-xeihvetbja-uc.a.run.app"
        )
        self.client = httpx.AsyncClient(timeout=10.0)
        logger.info(f"Memory Logger initialized: {self.memory_engine_url}")
    
    async def log(
        self,
        entity_id: str,
        interaction_type: str,
        interaction_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Log an interaction to Memory Engine
        
        Args:
            entity_id: UUID of the entity
            interaction_type: Type of interaction (conversation, action, event, etc.)
            interaction_data: Dictionary containing interaction details
            timestamp: Optional timestamp (defaults to now)
        
        Returns:
            Response from Memory Engine
        
        Raises:
            httpx.HTTPError: If the request fails
        """
        try:
            payload = {
                "entity_id": entity_id,
                "interaction_type": interaction_type,
                "interaction_data": interaction_data,
            }
            
            if timestamp:
                payload["timestamp"] = timestamp.isoformat()
            
            response = await self.client.post(
                f"{self.memory_engine_url}/log",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Memory logged: {result.get('memory_id')} (Tier {result.get('tier')})")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to log memory: {e}")
            # Don't raise - memory logging should not break the main flow
            return {"status": "error", "message": str(e)}
    
    async def log_conversation(
        self,
        entity_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method for logging conversations
        
        Args:
            entity_id: UUID of the entity
            role: Role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        
        Returns:
            Response from Memory Engine
        """
        interaction_data = {
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        
        return await self.log(
            entity_id=entity_id,
            interaction_type="conversation",
            interaction_data=interaction_data
        )
    
    async def log_task_execution(
        self,
        entity_id: str,
        task_id: str,
        task_title: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convenience method for logging task executions
        
        Args:
            entity_id: UUID of the entity
            task_id: UUID of the task
            task_title: Title of the task
            status: Status (completed, failed, etc.)
            result: Optional result data
        
        Returns:
            Response from Memory Engine
        """
        interaction_data = {
            "task_id": task_id,
            "task_title": task_title,
            "status": status,
            "result": result or {}
        }
        
        return await self.log(
            entity_id=entity_id,
            interaction_type="task_execution",
            interaction_data=interaction_data
        )
    
    async def log_decision(
        self,
        entity_id: str,
        decision_type: str,
        decision_data: Dict[str, Any],
        outcome: str
    ) -> Dict[str, Any]:
        """
        Convenience method for logging decisions
        
        Args:
            entity_id: UUID of the entity
            decision_type: Type of decision
            decision_data: Decision details
            outcome: Outcome of the decision
        
        Returns:
            Response from Memory Engine
        """
        interaction_data = {
            "decision_type": decision_type,
            "decision_data": decision_data,
            "outcome": outcome
        }
        
        return await self.log(
            entity_id=entity_id,
            interaction_type="decision",
            interaction_data=interaction_data
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        logger.info("Memory Logger client closed")


# Global instance (optional - for convenience)
_memory_logger: Optional[MemoryLogger] = None


def get_memory_logger() -> MemoryLogger:
    """Get or create global Memory Logger instance"""
    global _memory_logger
    if _memory_logger is None:
        _memory_logger = MemoryLogger()
    return _memory_logger
