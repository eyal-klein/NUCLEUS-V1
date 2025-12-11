"""
NUCLEUS Phase 3 - Base IOT Connector Framework
Standardized framework for all IOT device connectors
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import httpx
import os

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """
    Base class for all IOT connectors.
    Provides common functionality for authentication, data fetching, and event publishing.
    """
    
    def __init__(self, entity_id: str, credentials: Dict[str, str]):
        """
        Initialize connector.
        
        Args:
            entity_id: UUID of the entity this connector belongs to
            credentials: Dictionary of credentials (API keys, tokens, etc.)
        """
        self.entity_id = entity_id
        self.credentials = credentials
        self.event_stream_url = os.getenv("EVENT_STREAM_URL", "http://event-stream:8080")
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this data source (e.g., 'oura', 'apple_health')"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the external API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def fetch_latest_data(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Fetch latest data from the external API.
        
        Args:
            since: Only fetch data after this timestamp (optional)
            
        Returns:
            List of raw data records from the API
        """
        pass
    
    @abstractmethod
    def parse_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse raw API data into standardized events.
        
        Args:
            raw_data: Raw data from the API
            
        Returns:
            List of standardized events ready to publish
        """
        pass
    
    async def publish_event(self, event_type: str, payload: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publish an event to the Event Stream.
        
        Args:
            event_type: Type of event (e.g., 'sleep_completed', 'hrv_measured')
            payload: Event payload
            metadata: Optional metadata
            
        Returns:
            True if published successfully, False otherwise
        """
        try:
            event = {
                "source": self.source_name,
                "type": event_type,
                "entity_id": self.entity_id,
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            response = await self.http_client.post(
                f"{self.event_stream_url}/publish",
                json=event
            )
            
            if response.status_code == 200:
                logger.info(f"Published {self.source_name}.{event_type} event")
                return True
            else:
                logger.error(f"Failed to publish event: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing event: {str(e)}")
            return False
    
    async def sync(self, since: Optional[datetime] = None) -> int:
        """
        Main sync method: fetch, parse, and publish data.
        
        Args:
            since: Only sync data after this timestamp (optional)
            
        Returns:
            Number of events published
        """
        try:
            # Authenticate
            if not await self.authenticate():
                logger.error(f"{self.source_name}: Authentication failed")
                return 0
            
            # Fetch data
            raw_data_list = await self.fetch_latest_data(since=since)
            logger.info(f"{self.source_name}: Fetched {len(raw_data_list)} records")
            
            # Parse and publish
            events_published = 0
            for raw_data in raw_data_list:
                events = self.parse_data(raw_data)
                for event in events:
                    if await self.publish_event(
                        event_type=event["type"],
                        payload=event["payload"],
                        metadata=event.get("metadata")
                    ):
                        events_published += 1
            
            logger.info(f"{self.source_name}: Published {events_published} events")
            return events_published
            
        except Exception as e:
            logger.error(f"{self.source_name}: Sync error - {str(e)}")
            return 0
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


class HealthConnector(BaseConnector):
    """
    Base class specifically for health/wellness IOT devices.
    Provides common health metric parsing.
    """
    
    @staticmethod
    def normalize_sleep_score(raw_score: float, max_score: float = 100.0) -> float:
        """Normalize sleep score to 0-1 scale"""
        return min(1.0, max(0.0, raw_score / max_score))
    
    @staticmethod
    def normalize_hrv(hrv_ms: int, baseline_ms: int = 50) -> float:
        """
        Normalize HRV to 0-1 scale.
        Higher HRV = better recovery.
        """
        return min(1.0, max(0.0, hrv_ms / (baseline_ms * 2)))
    
    @staticmethod
    def normalize_resting_heart_rate(rhr: int, optimal_rhr: int = 60) -> float:
        """
        Normalize resting heart rate to 0-1 scale.
        Lower RHR = better fitness (inverted scale).
        """
        # Inverted: lower is better
        # Assume range of 40-100 bpm
        normalized = (100 - rhr) / (100 - 40)
        return min(1.0, max(0.0, normalized))
    
    def create_health_metric_event(
        self,
        metric_type: str,
        value: float,
        unit: str,
        recorded_at: datetime,
        source_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized health metric event.
        
        Args:
            metric_type: Type of metric (sleep_score, hrv, heart_rate, etc.)
            value: Metric value
            unit: Unit of measurement
            recorded_at: When the metric was recorded
            source_id: External ID from the source system
            
        Returns:
            Standardized event dict
        """
        return {
            "type": f"{metric_type}_measured",
            "payload": {
                "metric_type": metric_type,
                "value": value,
                "unit": unit,
                "recorded_at": recorded_at.isoformat()
            },
            "metadata": {
                "source_id": source_id
            } if source_id else {}
        }
