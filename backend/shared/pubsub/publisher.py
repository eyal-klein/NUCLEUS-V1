"""
NUCLEUS Pub/Sub Publisher Client
Shared library for publishing events to Cloud Pub/Sub
"""

import json
import os
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from google.cloud import pubsub_v1
from google.api_core import retry

logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "thrive-system1")

# Topic names
TOPICS = {
    "digital": f"projects/{PROJECT_ID}/topics/nucleus-digital-events",
    "health": f"projects/{PROJECT_ID}/topics/nucleus-health-events",
    "social": f"projects/{PROJECT_ID}/topics/nucleus-social-events",
}


class NucleusPublisher:
    """
    Pub/Sub publisher for NUCLEUS events.
    
    Usage:
        publisher = NucleusPublisher()
        await publisher.publish_digital_event("email.received", entity_id, data)
    """
    
    def __init__(self):
        self._publisher = None
        self._initialized = False
    
    def _get_publisher(self) -> pubsub_v1.PublisherClient:
        """Lazy initialization of publisher client."""
        if self._publisher is None:
            self._publisher = pubsub_v1.PublisherClient()
            self._initialized = True
            logger.info("Pub/Sub publisher initialized")
        return self._publisher
    
    def publish(
        self,
        topic_key: str,
        event_type: str,
        entity_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Publish an event to a Pub/Sub topic.
        
        Args:
            topic_key: One of 'digital', 'health', 'social'
            event_type: Event type (e.g., 'email.received', 'health.oura.sync')
            entity_id: The entity ID this event belongs to
            data: Event payload data
            metadata: Optional metadata attributes
            
        Returns:
            Message ID of the published message
        """
        if topic_key not in TOPICS:
            raise ValueError(f"Invalid topic key: {topic_key}. Must be one of {list(TOPICS.keys())}")
        
        topic_path = TOPICS[topic_key]
        publisher = self._get_publisher()
        
        # Build event envelope
        event = {
            "type": event_type,
            "entity_id": entity_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": os.getenv("K_SERVICE", "unknown"),
            "version": "1.0"
        }
        
        # Encode message
        message_data = json.dumps(event).encode("utf-8")
        
        # Build attributes
        attributes = {
            "event_type": event_type,
            "entity_id": entity_id,
            "source": os.getenv("K_SERVICE", "unknown"),
        }
        if metadata:
            attributes.update(metadata)
        
        # Publish with retry
        try:
            future = publisher.publish(
                topic_path,
                data=message_data,
                **attributes
            )
            message_id = future.result(timeout=30)
            logger.info(f"Published {event_type} to {topic_key}: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to publish {event_type} to {topic_key}: {e}")
            raise
    
    def publish_digital_event(
        self,
        event_type: str,
        entity_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Publish an event to the digital events topic (Gmail, Calendar)."""
        return self.publish("digital", event_type, entity_id, data, metadata)
    
    def publish_health_event(
        self,
        event_type: str,
        entity_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Publish an event to the health events topic (Oura, Apple Watch)."""
        return self.publish("health", event_type, entity_id, data, metadata)
    
    def publish_social_event(
        self,
        event_type: str,
        entity_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Publish an event to the social events topic (LinkedIn)."""
        return self.publish("social", event_type, entity_id, data, metadata)
    
    def close(self):
        """Close the publisher client."""
        if self._publisher:
            self._publisher.close()
            self._publisher = None
            self._initialized = False
            logger.info("Pub/Sub publisher closed")


# Singleton instance for convenience
_default_publisher: Optional[NucleusPublisher] = None


def get_publisher() -> NucleusPublisher:
    """Get the default publisher instance."""
    global _default_publisher
    if _default_publisher is None:
        _default_publisher = NucleusPublisher()
    return _default_publisher


def publish_event(
    topic_key: str,
    event_type: str,
    entity_id: str,
    data: Dict[str, Any],
    metadata: Optional[Dict[str, str]] = None
) -> str:
    """Convenience function to publish an event using the default publisher."""
    return get_publisher().publish(topic_key, event_type, entity_id, data, metadata)
